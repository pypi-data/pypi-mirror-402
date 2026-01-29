"""
Integración de vLLM para batching dinámico y alto throughput.
Optimizado para inferencia de alto rendimiento con EmpoorioLM.
"""

import asyncio
import torch
import logging
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import time
from pathlib import Path

try:
    from vllm import LLM, SamplingParams
    from vllm.engine.arg_utils import EngineArgs
    VLLM_AVAILABLE = True
except ImportError:
    VLLM_AVAILABLE = False
    SamplingParams = Any  # Placeholder
    logger = logging.getLogger(__name__)
    logger.warning("vLLM no disponible. Instalar con: pip install vllm")

from ..models.empoorio_lm import EmpoorioLM

logger = logging.getLogger(__name__)


@dataclass
class BatchingConfig:
    """Configuración para batching dinámico."""

    # Configuración de vLLM
    model_path: str
    tensor_parallel_size: int = 1
    gpu_memory_utilization: float = 0.9
    max_model_len: int = 4096
    max_num_seqs: int = 256
    max_num_batched_tokens: int = 4096

    # Configuración de batching dinámico
    dynamic_batching: bool = True
    max_batch_size: int = 32
    batch_timeout_ms: int = 50
    max_waiting_requests: int = 100

    # Configuración de sampling
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    max_tokens: int = 512
    repetition_penalty: float = 1.1

    # Configuración de cuantización
    quantization: Optional[str] = None  # "awq", "gptq", "squeezellm"

    def to_engine_args(self) -> Dict[str, Any]:
        """Convertir a argumentos de vLLM."""
        return {
            "model": self.model_path,
            "tensor_parallel_size": self.tensor_parallel_size,
            "gpu_memory_utilization": self.gpu_memory_utilization,
            "max_model_len": self.max_model_len,
            "max_num_seqs": self.max_num_seqs,
            "max_num_batched_tokens": self.max_num_batched_tokens,
            "enforce_eager": False,  # Usar CUDA graphs para mejor rendimiento
        }


@dataclass
class BatchRequest:
    """Solicitud para procesamiento en batch."""

    id: str
    prompt: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    stream: bool = False
    priority: int = 0  # 0=normal, 1=high, 2=urgent

    def to_sampling_params(self, config: BatchingConfig) -> SamplingParams:
        """Convertir a parámetros de sampling de vLLM."""
        return SamplingParams(
            max_tokens=self.max_tokens or config.max_tokens,
            temperature=self.temperature or config.temperature,
            top_p=self.top_p or config.top_p,
            top_k=self.top_k or config.top_k,
            repetition_penalty=config.repetition_penalty,
            stop=["</s>", "<|endoftext|>"],
        )


@dataclass
class BatchResponse:
    """Respuesta de procesamiento en batch."""

    request_id: str
    text: str
    usage: Dict[str, Any]
    finish_reason: str
    processing_time: float


class DynamicBatcher:
    """
    Batcher dinámico para optimizar throughput con vLLM.

    Características:
    - Batching continuo con timeouts adaptativos
    - Priorización de requests
    - Monitoreo de rendimiento en tiempo real
    - Auto-scaling basado en carga
    """

    def __init__(self, config: BatchingConfig):
        self.config = config
        self.llm: Optional[LLM] = None

        # Colas de requests
        self.request_queue = asyncio.PriorityQueue(maxsize=config.max_waiting_requests)
        self.processing_batch: List[BatchRequest] = []

        # Estado del sistema
        self.is_running = False
        self.current_batch_size = 0
        self.batch_start_time: Optional[float] = None

        # Métricas
        self.metrics = {
            "total_requests": 0,
            "total_tokens": 0,
            "avg_batch_size": 0.0,
            "avg_latency": 0.0,
            "throughput_tokens_per_sec": 0.0,
            "queue_length": 0
        }

        # Executor para operaciones CPU
        self.executor = ThreadPoolExecutor(max_workers=2)

        logger.info("🔄 DynamicBatcher inicializado")
        logger.info(f"   Max batch size: {config.max_batch_size}")
        logger.info(f"   Batch timeout: {config.batch_timeout_ms}ms")

    async def initialize(self) -> bool:
        """Inicializar vLLM engine."""
        if not VLLM_AVAILABLE:
            logger.error("❌ vLLM no disponible")
            return False

        try:
            logger.info("🚀 Inicializando vLLM engine...")

            engine_args = EngineArgs(**self.config.to_engine_args())
            self.llm = LLM(engine_args)

            logger.info("✅ vLLM engine inicializado exitosamente")
            return True

        except Exception as e:
            logger.error(f"❌ Error inicializando vLLM: {e}")
            return False

    async def start_processing(self):
        """Iniciar procesamiento continuo de batches."""
        if not self.llm:
            logger.error("❌ vLLM no inicializado")
            return

        self.is_running = True
        logger.info("▶️ Iniciando procesamiento de batches dinámicos")

        while self.is_running:
            try:
                await self._process_batch()
            except Exception as e:
                logger.error(f"❌ Error en procesamiento de batch: {e}")
                await asyncio.sleep(1)

    async def stop_processing(self):
        """Detener procesamiento."""
        self.is_running = False
        logger.info("⏹️ Procesamiento de batches detenido")

    async def submit_request(self, request: BatchRequest) -> str:
        """Enviar request para procesamiento."""
        try:
            # Prioridad negativa para que mayor prioridad = menor número
            priority = -request.priority
            await self.request_queue.put((priority, request))
            self.metrics["queue_length"] = self.request_queue.qsize()

            logger.debug(f"📨 Request {request.id} en cola (prioridad: {request.priority})")
            return request.id

        except asyncio.QueueFull:
            logger.warning(f"⚠️ Cola llena, rechazando request {request.id}")
            raise RuntimeError("Queue full")

    async def _process_batch(self):
        """Procesar un batch de requests."""
        # Esperar primer request o timeout
        try:
            priority, first_request = await asyncio.wait_for(
                self.request_queue.get(),
                timeout=self.config.batch_timeout_ms / 1000
            )
        except asyncio.TimeoutError:
            # No hay requests, esperar un poco
            await asyncio.sleep(0.01)
            return

        self.processing_batch = [first_request]
        self.batch_start_time = time.time()
        batch_tokens = self._estimate_tokens(first_request.prompt)

        # Acumular más requests hasta límite
        while len(self.processing_batch) < self.config.max_batch_size:
            try:
                # Timeout muy corto para acumular requests
                priority, request = await asyncio.wait_for(
                    self.request_queue.get(),
                    timeout=0.001
                )

                new_tokens = self._estimate_tokens(request.prompt)
                if batch_tokens + new_tokens <= self.config.max_num_batched_tokens:
                    self.processing_batch.append(request)
                    batch_tokens += new_tokens
                else:
                    # Poner de vuelta en cola si no cabe
                    await self.request_queue.put((priority, request))
                    break

            except asyncio.TimeoutError:
                break

        # Procesar batch
        if self.processing_batch:
            await self._execute_batch()

    async def _execute_batch(self):
        """Ejecutar batch con vLLM."""
        if not self.llm:
            return

        batch_size = len(self.processing_batch)
        start_time = time.time()

        try:
            # Preparar prompts y parámetros
            prompts = [req.prompt for req in self.processing_batch]
            sampling_params = [
                req.to_sampling_params(self.config)
                for req in self.processing_batch
            ]

            # Ejecutar inferencia
            outputs = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.llm.generate,
                prompts,
                sampling_params
            )

            processing_time = time.time() - start_time

            # Procesar resultados
            total_tokens = 0
            for i, output in enumerate(outputs):
                request = self.processing_batch[i]

                # Extraer texto generado
                generated_text = output.outputs[0].text
                total_tokens += len(output.outputs[0].token_ids)

                # Crear respuesta
                response = BatchResponse(
                    request_id=request.id,
                    text=generated_text,
                    usage={
                        "prompt_tokens": len(output.prompt_token_ids),
                        "completion_tokens": len(output.outputs[0].token_ids),
                        "total_tokens": len(output.prompt_token_ids) + len(output.outputs[0].token_ids)
                    },
                    finish_reason=output.outputs[0].finish_reason,
                    processing_time=processing_time / batch_size  # Tiempo promedio por request
                )

                # Aquí se enviaría la respuesta al cliente
                # En implementación real, usar callbacks o queues
                logger.debug(f"✅ Request {request.id} completado")

            # Actualizar métricas
            self._update_metrics(batch_size, total_tokens, processing_time)

        except Exception as e:
            logger.error(f"❌ Error ejecutando batch: {e}")

        finally:
            self.processing_batch.clear()
            self.batch_start_time = None

    def _estimate_tokens(self, text: str) -> int:
        """Estimar número de tokens en texto."""
        # Estimación simple: ~4 caracteres por token
        return len(text) // 4

    def _update_metrics(self, batch_size: int, total_tokens: int, processing_time: float):
        """Actualizar métricas de rendimiento."""
        self.metrics["total_requests"] += batch_size
        self.metrics["total_tokens"] += total_tokens

        # Actualizar promedio de batch size
        prev_avg = self.metrics["avg_batch_size"]
        self.metrics["avg_batch_size"] = (prev_avg * (self.metrics["total_requests"] - batch_size) + batch_size) / self.metrics["total_requests"]

        # Throughput
        if processing_time > 0:
            throughput = total_tokens / processing_time
            self.metrics["throughput_tokens_per_sec"] = throughput

        # Latencia promedio
        avg_latency = processing_time / batch_size
        prev_latency_avg = self.metrics["avg_latency"]
        self.metrics["avg_latency"] = (prev_latency_avg * (self.metrics["total_requests"] - batch_size) + avg_latency) / self.metrics["total_requests"]

    def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas actuales."""
        return {
            **self.metrics,
            "queue_length": self.request_queue.qsize(),
            "current_batch_size": len(self.processing_batch),
            "is_processing": self.batch_start_time is not None
        }


class VLLMInferenceEngine:
    """
    Engine de inferencia completo con vLLM y batching dinámico.
    """

    def __init__(self, config: BatchingConfig):
        self.config = config
        self.batcher = DynamicBatcher(config)
        self.response_queues: Dict[str, asyncio.Queue] = {}

        # Tarea de procesamiento
        self.processing_task: Optional[asyncio.Task] = None

    async def initialize(self) -> bool:
        """Inicializar engine completo."""
        success = await self.batcher.initialize()
        if success:
            self.processing_task = asyncio.create_task(self.batcher.start_processing())
        return success

    async def shutdown(self):
        """Apagar engine."""
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass

        await self.batcher.stop_processing()

    async def generate(
        self,
        prompt: str,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Generar texto con batching dinámico.

        Args:
            prompt: Texto de entrada
            **kwargs: Parámetros adicionales

        Yields:
            Chunks de texto generado
        """
        # Crear request
        request_id = f"req_{int(time.time() * 1000)}_{hash(prompt) % 1000}"
        request = BatchRequest(
            id=request_id,
            prompt=prompt,
            max_tokens=kwargs.get('max_tokens'),
            temperature=kwargs.get('temperature'),
            top_p=kwargs.get('top_p'),
            top_k=kwargs.get('top_k'),
            stream=kwargs.get('stream', False),
            priority=kwargs.get('priority', 0)
        )

        # Crear cola de respuesta
        response_queue = asyncio.Queue()
        self.response_queues[request_id] = response_queue

        try:
            # Enviar request
            await self.batcher.submit_request(request)

            # Esperar respuesta
            response: BatchResponse = await response_queue.get()

            # Para streaming, yield chunks (simplificado)
            if request.stream:
                # En implementación real, manejar streaming token por token
                yield response.text
            else:
                yield response.text

        finally:
            # Limpiar
            self.response_queues.pop(request_id, None)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Obtener métricas de rendimiento."""
        return {
            "batcher_metrics": self.batcher.get_metrics(),
            "config": {
                "max_batch_size": self.config.max_batch_size,
                "dynamic_batching": self.config.dynamic_batching,
                "gpu_memory_utilization": self.config.gpu_memory_utilization
            }
        }


# Funciones de conveniencia
def create_vllm_engine(
    model_path: str,
    tensor_parallel_size: int = 1,
    max_batch_size: int = 32
) -> VLLMInferenceEngine:
    """
    Crear engine de inferencia vLLM con configuración optimizada.

    Args:
        model_path: Ruta del modelo
        tensor_parallel_size: Paralelismo de tensores
        max_batch_size: Tamaño máximo de batch

    Returns:
        Engine configurado
    """
    config = BatchingConfig(
        model_path=model_path,
        tensor_parallel_size=tensor_parallel_size,
        max_batch_size=max_batch_size,
        dynamic_batching=True
    )

    return VLLMInferenceEngine(config)


if __name__ == "__main__":
    # Demo del batcher dinámico
    print("🚀 VLLM Dynamic Batching Demo")
    print("Para uso completo, inicializar con modelo EmpoorioLM")