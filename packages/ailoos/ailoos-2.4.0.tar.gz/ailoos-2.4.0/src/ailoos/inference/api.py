"""
EmpoorioLM Inference API
API de alto rendimiento para inferencia con modelos EmpoorioLM.
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
from dataclasses import dataclass
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import aiohttp
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
import uvicorn

# Import torch opcionalmente
try:
    import torch
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    F = None
    TORCH_AVAILABLE = False

from transformers import AutoTokenizer, AutoModelForCausalLM
from ..models.empoorio_lm import EmpoorioLM, EmpoorioLMConfig

# Nuevos imports para Maturity 2
from .quantization import AdvancedQuantizer, quantize_empoorio_model
from .model_drift_monitor import ModelDriftMonitor, create_drift_monitor, DriftThresholds
from .vllm_batching import VLLMInferenceEngine, create_vllm_engine, BatchingConfig
from .sentencepiece_tokenizer import create_ailoos_tokenizer

# Import para integración con servicios de gestión de modelos (lazy import para evitar circular dependencies)
_inference_coordinator_imported = False
InferenceCoordinator = None
CoordinatorInferenceRequest = None

def _import_inference_coordinator():
    global _inference_coordinator_imported, InferenceCoordinator, CoordinatorInferenceRequest
    if not _inference_coordinator_imported:
        try:
            from ..coordinator.services.inference_coordinator import InferenceCoordinator as IC, InferenceRequest as CIR
            InferenceCoordinator = IC
            CoordinatorInferenceRequest = CIR
            _inference_coordinator_imported = True
        except ImportError:
            # Si hay circular import, usar None
            InferenceCoordinator = None
            CoordinatorInferenceRequest = None

# Import para Guidance y esquemas estructurados
from ..schemas import (
    is_guidance_available,
    create_structured_inference_response,
    StructuredOutputGenerator
)

# Import para métricas de performance
from ..monitoring.performance_metrics import get_performance_collector

logger = logging.getLogger(__name__)


@dataclass
class InferenceConfig:
    """Configuración de la API de inferencia."""

    # Configuración del modelo
    model_path: str = "./src/models/empoorio_lm/versions/empoorio_lm_v1.0.0-trained_267306"
    tokenizer_name: str = "gpt2"  # Tokenizer a usar (HuggingFace model name)
    tokenizer_model_path: Optional[str] = "./test_tokenizer_output/ailoos_tokenizer.model"  # Ruta al modelo SentencePiece fine-tuned
    device: str = "auto"  # auto, cpu, cuda, mps
    torch_dtype: str = "auto"  # auto, float32, float16, bfloat16

    # Configuración de cuantización (Maturity 2)
    enable_quantization: bool = False
    quantization_type: str = "int8"  # int8, int4
    quantized_model_path: Optional[str] = None

    # Configuración de generación
    max_new_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    repetition_penalty: float = 1.1
    do_sample: bool = True

    # Configuración de rendimiento
    max_batch_size: int = 8
    max_concurrent_requests: int = 10
    request_timeout_seconds: int = 300

    # Configuración del servidor
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    # Configuración de cache
    enable_cache: bool = True
    cache_max_size: int = 1000

    # Configuración de logging
    log_level: str = "INFO"
    enable_metrics: bool = True

    # Configuración de monitoreo de deriva (Maturity 2)
    enable_drift_monitoring: bool = False
    drift_history_file: str = "./drift_history.json"
    drift_check_interval_hours: int = 24

    # Configuración de vLLM batching (Maturity 2)
    enable_vllm_batching: bool = False
    vllm_tensor_parallel_size: int = 1
    vllm_gpu_memory_utilization: float = 0.9
    vllm_max_batch_size: int = 32

    # Configuración de Guidance para salidas estructuradas
    enable_guidance: bool = False
    guidance_output_format: str = "inference"  # "inference", "toon", "vsc"
    guidance_validation_enabled: bool = True


@dataclass
class InferenceRequest:
    """Solicitud de inferencia."""

    prompt: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    stream: bool = False
    stop_sequences: Optional[List[str]] = None
    output_format: Optional[str] = None  # "inference", "toon", "vsc"
    structured_output: bool = False  # Forzar salida estructurada con Guidance
    schema: Optional[Dict[str, Any]] = None  # Esquema JSON Schema personalizado para structured output
    validation_enabled: bool = True  # Habilitar validación de esquema

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt": self.prompt,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "stream": self.stream,
            "stop_sequences": self.stop_sequences,
            "output_format": self.output_format,
            "structured_output": self.structured_output,
            "schema": self.schema,
            "validation_enabled": self.validation_enabled
        }


@dataclass
class InferenceResponse:
    """Respuesta de inferencia."""

    text: str
    usage: Dict[str, Any]
    model_version: str
    generated_at: float
    structured_output: bool = False
    schema_used: Optional[Dict[str, Any]] = None
    validation_passed: Optional[bool] = None
    guidance_used: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "usage": self.usage,
            "model_version": self.model_version,
            "generated_at": self.generated_at,
            "structured_output": self.structured_output,
            "schema_used": self.schema_used,
            "validation_passed": self.validation_passed,
            "guidance_used": self.guidance_used
        }


class EmpoorioLMInferenceAPI:
    """
    API de inferencia de alto rendimiento para EmpoorioLM.

    Características:
    - Inferencia síncrona y streaming
    - Batch processing para múltiples requests
    - Cache inteligente de KV-cache
    - Optimizaciones de memoria (quantization, pruning)
    - Métricas de rendimiento detalladas
    - Auto-scaling basado en carga

    Maturity 2 Features:
    - Cuantización INT8/INT4 con Bitsandbytes
    - Monitoreo de deriva del modelo
    - Batching dinámico con vLLM
    """

    def __init__(self, config: InferenceConfig, inference_coordinator=None):
        """
        Inicializar la API de inferencia.

        Args:
            config: Configuración de la API
            inference_coordinator: Coordinador de inferencia opcional para integración federada
        """
        self.config = config

        # Coordinador de inferencia para integración con servicios federados
        self.inference_coordinator = inference_coordinator

        # Modelo y tokenizer
        self.model: Optional[EmpoorioLM] = None
        self.tokenizer = None

        # Estado del sistema
        self.is_loaded = False
        self.device = self._get_device()

        # Cache y optimizaciones
        self.kv_cache = {} if config.enable_cache else None
        self.request_queue = asyncio.Queue(maxsize=config.max_concurrent_requests)

        # Componentes Maturity 2
        self.quantizer: Optional[AdvancedQuantizer] = None
        self.drift_monitor: Optional[ModelDriftMonitor] = None
        self.vllm_engine: Optional[VLLMInferenceEngine] = None

        # Componente Guidance para salidas estructuradas
        self.structured_generator: Optional[StructuredOutputGenerator] = None

        # Dataset de referencia para monitoreo de deriva
        self.reference_dataset: List[str] = []

        # Métricas
        self.metrics = {
            "total_requests": 0,
            "total_tokens_generated": 0,
            "avg_response_time": 0.0,
            "cache_hit_rate": 0.0,
            "error_rate": 0.0,
            # Maturity 2 metrics
            "quantization_memory_savings": 0.0,
            "drift_alerts": 0,
            "vllm_throughput": 0.0,
            # Guidance metrics
            "guidance_requests": 0,
            "guidance_success_rate": 0.0,
            "structured_output_rate": 0.0,
            "schema_validation_errors": 0,
            "custom_schema_requests": 0,
            "streaming_structured_requests": 0
        }

        # Executor para operaciones CPU-bound
        self.executor = ThreadPoolExecutor(max_workers=4)

        logger.info(f"🚀 EmpoorioLM Inference API inicializada - Device: {self.device}")
        logger.info(f"   Cuantización: {'Habilitada' if config.enable_quantization else 'Deshabilitada'}")
        logger.info(f"   Monitoreo de deriva: {'Habilitado' if config.enable_drift_monitoring else 'Deshabilitado'}")
        logger.info(f"   vLLM batching: {'Habilitado' if config.enable_vllm_batching else 'Deshabilitado'}")
        logger.info(f"   Guidance estructurado: {'Habilitado' if config.enable_guidance else 'Deshabilitado'}")

    def _get_device(self) -> "torch.device":
        """Determinar el dispositivo óptimo."""
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch no está disponible. Instale torch para usar la API de inferencia.")

        if self.config.device == "auto":
            if torch.cuda.is_available():
                return torch.device("cuda")
            elif torch.backends.mps.is_available():
                return torch.device("mps")
            else:
                return torch.device("cpu")
        else:
            return torch.device(self.config.device)

    async def load_model(self) -> bool:
        """
        Cargar el modelo EmpoorioLM y tokenizer con optimizaciones Maturity 2.

        Returns:
            True si se cargó correctamente
        """
        try:
            # Determinar ruta del modelo (cuantizado si está habilitado)
            model_path = self.config.quantized_model_path if (
                self.config.enable_quantization and self.config.quantized_model_path
            ) else self.config.model_path

            logger.info(f"📥 Cargando modelo desde: {model_path}")

            model_path_obj = Path(model_path)
            if not model_path_obj.exists():
                logger.error(f"❌ Modelo no encontrado: {model_path_obj}")
                return False

            # Cargar modelo con cuantización si está habilitada
            if self.config.enable_quantization and not self.config.quantized_model_path:
                logger.info(f"🔧 Aplicando cuantización {self.config.quantization_type}...")

                self.quantizer = AdvancedQuantizer()
                self.model = self.quantizer.quantize_model(
                    model_path=str(model_path_obj),
                    quantization_type=self.config.quantization_type,
                    save_path=self.config.quantized_model_path
                )

                # Calcular ahorro de memoria
                original_model = AutoModelForCausalLM.from_pretrained(str(self.config.model_path))
                memory_stats = self.quantizer.compare_model_sizes(original_model, self.model)
                self.metrics["quantization_memory_savings"] = memory_stats["memory_savings_percent"]

                logger.info(f"💾 Ahorro de memoria: {memory_stats['memory_savings_percent']:.1f}%")

            else:
                # Carga normal del modelo
                self.model = AutoModelForCausalLM.from_pretrained(str(model_path_obj))

            # Cargar tokenizer - usar el tokenizer del modelo entrenado
            logger.info(f"🔤 Cargando tokenizer desde el modelo: {model_path_obj}")
            self.tokenizer = AutoTokenizer.from_pretrained(str(model_path_obj), local_files_only=True, use_fast=False)

            # Configurar pad token si no existe
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # Mover modelo a dispositivo
            self.model.to(self.device)

            # Forzar configuración de contexto largo (4096 tokens) para Inference-Time Thinking
            # Esto corrige el error de "3'th index 1024 of condition tensor does not match"
            if hasattr(self.model.config, 'max_position_embeddings'):
                original_max_pos = self.model.config.max_position_embeddings
                self.model.config.max_position_embeddings = 4096
                logger.info(f"🔧 Forzando contexto largo: {original_max_pos} → 4096 tokens")

                # Forzar recreación de embeddings de posición si existen
                if hasattr(self.model, 'embed_positions') and self.model.embed_positions is not None:
                    try:
                        # Recrear embeddings de posición con el nuevo tamaño máximo
                        import torch.nn as nn
                        old_embed = self.model.embed_positions
                        new_embed = nn.Embedding(4096, old_embed.embedding_dim)
                        # Copiar pesos existentes (hasta el límite original)
                        with torch.no_grad():
                            new_embed.weight[:original_max_pos] = old_embed.weight[:original_max_pos]
                        self.model.embed_positions = new_embed
                        logger.info("✅ Embeddings de posición recreados para contexto largo")
                    except Exception as e:
                        logger.warning(f"⚠️ No se pudieron recrear embeddings de posición: {e}")

                # Limpiar cualquier caché que pueda estar limitada
                if hasattr(self.model, 'clear_cache'):
                    try:
                        self.model.clear_cache()
                        logger.info("🗑️ Caché del modelo limpiada")
                    except Exception as e:
                        logger.warning(f"⚠️ No se pudo limpiar caché: {e}")

            # Configurar dtype
            if self.config.torch_dtype != "auto":
                dtype_map = {
                    "float32": torch.float32,
                    "float16": torch.float16,
                    "bfloat16": torch.bfloat16
                }
                if self.config.torch_dtype in dtype_map:
                    self.model = self.model.to(dtype_map[self.config.torch_dtype])

            # Modo evaluación
            self.model.eval()

            # Desactivar gradientes
            for param in self.model.parameters():
                param.requires_grad = False

            # Inicializar componentes Maturity 2
            await self._initialize_maturity2_components()

            self.is_loaded = True
            logger.info(f"✅ Modelo y tokenizer cargados exitosamente")
            # Calcular parámetros del modelo
            total_params = sum(p.numel() for p in self.model.parameters())
            logger.info(f"   📊 Parámetros del modelo: {total_params:,}")
            logger.info(f"   🔤 Vocab size del tokenizer: {self.tokenizer.vocab_size}")
            return True

        except Exception as e:
            logger.error(f"❌ Error cargando modelo/tokenizer: {e}")
            return False

    async def _initialize_maturity2_components(self):
        """Inicializar componentes de Maturity 2."""
        try:
            # Monitoreo de deriva
            if self.config.enable_drift_monitoring:
                logger.info("📊 Inicializando monitoreo de deriva...")

                # Cargar dataset de referencia desde archivo
                self.reference_dataset = await self._load_reference_dataset()

                self.drift_monitor = await create_drift_monitor(
                    model=self.model,
                    tokenizer=self.tokenizer,
                    reference_dataset=self.reference_dataset,
                    history_file=self.config.drift_history_file
                )

                logger.info("✅ Monitoreo de deriva inicializado")

            # vLLM batching
            if self.config.enable_vllm_batching:
                logger.info("🚀 Inicializando vLLM batching...")

                vllm_config = BatchingConfig(
                    model_path=self.config.model_path,
                    tensor_parallel_size=self.config.vllm_tensor_parallel_size,
                    gpu_memory_utilization=self.config.vllm_gpu_memory_utilization,
                    max_batch_size=self.config.vllm_max_batch_size
                )

                self.vllm_engine = VLLMInferenceEngine(vllm_config)
                success = await self.vllm_engine.initialize()

                if success:
                    logger.info("✅ vLLM batching inicializado")
                else:
                    logger.warning("⚠️ Falló inicialización de vLLM, usando modo estándar")

            # Inicializar Guidance para salidas estructuradas
            if self.config.enable_guidance:
                logger.info("🎯 Inicializando Guidance para salidas estructuradas...")

                if is_guidance_available():
                    self.structured_generator = StructuredOutputGenerator()
                    logger.info("✅ Guidance inicializado correctamente")
                else:
                    logger.warning("⚠️ Guidance no disponible, salidas estructuradas deshabilitadas")

        except Exception as e:
            logger.error(f"❌ Error inicializando componentes Maturity 2: {e}")

    async def _load_reference_dataset(self) -> List[str]:
        """
        Cargar dataset de referencia desde archivo JSON para monitoreo de deriva.

        Returns:
            Lista de prompts de referencia
        """
        try:
            reference_file = Path("./data/reference_dataset.json")

            if reference_file.exists():
                with open(reference_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                samples = data.get("samples", [])
                logger.info(f"✅ Cargado dataset de referencia: {len(samples)} muestras desde {reference_file}")
                return samples
            else:
                # Fallback a dataset hardcodeado si no existe el archivo
                logger.warning(f"⚠️ Archivo de dataset de referencia no encontrado: {reference_file}, usando fallback")
                return [
                    "¿Cuál es la capital de Francia?",
                    "Explica la teoría de la relatividad",
                    "Escribe un poema sobre la naturaleza",
                    "¿Cómo funciona la fotosíntesis?",
                    "Traduce 'Hello world' al español",
                    "¿Qué es la inteligencia artificial?",
                    "Describe el proceso de la respiración celular",
                    "Escribe una función Python para calcular el factorial",
                    "¿Cuáles son los planetas del sistema solar?",
                    "Explica el concepto de blockchain"
                ]

        except Exception as e:
            logger.error(f"❌ Error cargando dataset de referencia: {e}, usando fallback")
            # Fallback mínimo
            return [
                "¿Cuál es la capital de Francia?",
                "Explica la teoría de la relatividad",
                "Escribe un poema sobre la naturaleza",
                "¿Cómo funciona la fotosíntesis?",
                "Traduce 'Hello world' al español"
            ]

    async def _check_gcp_connectivity(self) -> str:
        """
        Verificar conectividad real con servicios de GCP.

        Returns:
            Estado de conectividad: "connected", "disconnected", "unknown"
        """
        try:
            # Verificar conectividad con GCP Compute Engine API
            timeout = aiohttp.ClientTimeout(total=5)  # 5 segundos timeout

            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Intentar acceder a un endpoint público de GCP
                url = "https://compute.googleapis.com/compute/v1/projects"

                # En un entorno real con credenciales, usaríamos autenticación
                # Por ahora, verificamos conectividad básica
                try:
                    async with session.get(url, allow_redirects=True) as response:
                        if response.status in [200, 401, 403]:  # 401/403 significa API accesible pero no autorizado
                            logger.info("✅ Conectividad GCP verificada")
                            return "connected"
                        else:
                            logger.warning(f"⚠️ Respuesta GCP inesperada: {response.status}")
                            return "unknown"
                except aiohttp.ClientError as e:
                    logger.warning(f"⚠️ Error de conectividad GCP: {e}")
                    return "disconnected"

        except Exception as e:
            logger.error(f"❌ Error verificando conectividad GCP: {e}")
            return "unknown"

    async def _get_reference_measurements(self, validator) -> Dict[str, Any]:
        """
        Obtener todas las mediciones de referencia del validador TEE.

        Args:
            validator: Instancia del validador TEE

        Returns:
            Diccionario con todas las mediciones de referencia
        """
        try:
            measurements = {}

            # Obtener todas las claves de mediciones disponibles
            for key in validator.reference_measurements.keys():
                measurement = validator.get_reference_measurements(key)
                if measurement:
                    measurements[key] = {
                        "platform_firmware_hash": measurement.platform_firmware_hash,
                        "kernel_hash": measurement.kernel_hash,
                        "initrd_hash": measurement.initrd_hash,
                        "guest_policy": measurement.guest_policy,
                        "family_id": measurement.family_id,
                        "image_id": measurement.image_id,
                        "launch_measurement": measurement.launch_measurement,
                        "created_at": measurement.created_at.isoformat(),
                        "updated_at": measurement.updated_at.isoformat()
                    }

            logger.info(f"✅ Obtenidas {len(measurements)} mediciones de referencia")
            return measurements

        except Exception as e:
            logger.error(f"❌ Error obteniendo mediciones de referencia: {e}")
            return {}

    async def generate(
        self,
        request: InferenceRequest,
        structured_output: Optional[bool] = None,
        use_coordinator: bool = False,
        model_name: str = "empoorio_lm"
    ) -> InferenceResponse:
        """
        Generar texto con EmpoorioLM usando optimizaciones Maturity 2.

        Args:
            request: Solicitud de inferencia
            structured_output: Forzar salida estructurada con Guidance (opcional, sobreescribe request.structured_output)

        Returns:
            Respuesta con texto generado
        """
        if not self.is_loaded:
            raise RuntimeError("Modelo no cargado")

        start_time = time.time()

        try:
            # Usar InferenceCoordinator si está disponible y solicitado
            if use_coordinator and self.inference_coordinator and self.inference_coordinator.is_active:
                return await self._generate_with_coordinator(request, model_name, start_time)

            # Determinar si usar Guidance para salida estructurada
            # Usar parámetro directo si se proporciona, sino usar el del request
            effective_structured_output = structured_output if structured_output is not None else request.structured_output

            use_guidance = (
                self.config.enable_guidance and
                self.structured_generator and
                (effective_structured_output or self.config.guidance_output_format != "inference")
            )

            if use_guidance:
                logger.info(f"🎯 Usando Guidance para generación estructurada - Schema personalizado: {request.schema is not None}")

            if use_guidance:
                return await self._generate_with_guidance(request, start_time)

            # Usar vLLM si está habilitado y disponible
            if self.config.enable_vllm_batching and self.vllm_engine:
                return await self._generate_with_vllm(request, start_time)

            # Preparar parámetros de generación
            gen_kwargs = {
                "max_new_tokens": request.max_tokens or self.config.max_new_tokens,
                "temperature": request.temperature or self.config.temperature,
                "top_p": request.top_p or self.config.top_p,
                "top_k": request.top_k or self.config.top_k,
                "repetition_penalty": self.config.repetition_penalty,
                "do_sample": self.config.do_sample,
                "pad_token_id": self.tokenizer.pad_token_id,
                "eos_token_id": self.tokenizer.eos_token_id,
            }

            # Para streaming, usar método especial
            if request.stream:
                # Streaming implementado en generate_stream
                raise HTTPException(status_code=400, detail="Use /generate endpoint with stream=true for streaming")

            # Generar en thread pool para no bloquear
            loop = asyncio.get_event_loop()
            generated_tokens = await loop.run_in_executor(
                self.executor,
                self._generate_sync,
                request.prompt,
                gen_kwargs
            )

            # Decodificar (simulado por ahora)
            generated_text = self._decode_tokens(generated_tokens)

            # Calcular métricas de uso con tokenizer real
            response_time = time.time() - start_time

            # Tokenizar para contar tokens reales
            prompt_tokens = self.tokenizer.encode(request.prompt, add_special_tokens=True)
            completion_tokens = self.tokenizer.encode(generated_text, add_special_tokens=False)

            usage = {
                "prompt_tokens": len(prompt_tokens),
                "completion_tokens": len(completion_tokens),
                "total_tokens": len(prompt_tokens) + len(completion_tokens),
                "response_time_seconds": response_time
            }

            # Actualizar métricas globales
            self._update_metrics(usage, response_time)

            # Verificar deriva del modelo si está habilitado
            if self.config.enable_drift_monitoring and self.drift_monitor:
                await self._check_model_drift()

            response = InferenceResponse(
                text=generated_text,
                usage=usage,
                model_version="empoorio_lm_v1.0.0-trained",
                generated_at=time.time(),
                structured_output=False,
                guidance_used=False
            )

            return response

        except Exception as e:
            logger.error(f"❌ Error en generación: {e}")
            self.metrics["error_rate"] = (self.metrics["error_rate"] * self.metrics["total_requests"] + 1) / (self.metrics["total_requests"] + 1)
            raise HTTPException(status_code=500, detail=f"Error de inferencia: {str(e)}")

    async def _generate_with_vllm(self, request: InferenceRequest, start_time: float) -> InferenceResponse:
        """Generar usando vLLM para alto throughput."""
        try:
            # Generar con vLLM
            generated_text = ""
            async for chunk in self.vllm_engine.generate(
                prompt=request.prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                top_k=request.top_k,
                stream=False  # Para compatibilidad con API actual
            ):
                generated_text = chunk  # vLLM retorna el texto completo

            response_time = time.time() - start_time

            # Calcular métricas de uso
            prompt_tokens = self.tokenizer.encode(request.prompt, add_special_tokens=True)
            completion_tokens = self.tokenizer.encode(generated_text, add_special_tokens=False)

            usage = {
                "prompt_tokens": len(prompt_tokens),
                "completion_tokens": len(completion_tokens),
                "total_tokens": len(prompt_tokens) + len(completion_tokens),
                "response_time_seconds": response_time
            }

            # Actualizar métricas
            self._update_metrics(usage, response_time)

            # Actualizar métricas de vLLM
            vllm_metrics = self.vllm_engine.get_performance_metrics()
            self.metrics["vllm_throughput"] = vllm_metrics["batcher_metrics"]["throughput_tokens_per_sec"]

            return InferenceResponse(
                text=generated_text,
                usage=usage,
                model_version=self.model.config.version,
                generated_at=time.time(),
                structured_output=False,
                guidance_used=False
            )

        except Exception as e:
            logger.error(f"❌ Error en generación vLLM: {e}")
            # Fallback a método estándar
            logger.info("🔄 Fallback a generación estándar")
            raise

    async def _generate_with_guidance(self, request: InferenceRequest, start_time: float) -> InferenceResponse:
        """Generar usando Guidance para salidas estructuradas."""
        try:
            # Determinar formato de salida y esquema
            output_format = request.output_format or self.config.guidance_output_format

            # Usar esquema personalizado si se proporciona, sino usar formato estándar
            if request.schema:
                # Generar con esquema personalizado
                structured_result = self.structured_generator.generate_with_schema(
                    prompt=request.prompt,
                    schema=request.schema,
                    model=self.model,  # Pasar modelo para Guidance
                    max_tokens=request.max_tokens or self.config.max_new_tokens,
                    temperature=request.temperature or self.config.temperature,
                    top_p=request.top_p or self.config.top_p,
                    top_k=request.top_k or self.config.top_k
                )
            else:
                # Generar con formato estándar
                structured_result = self.structured_generator.generate_inference_response(
                    prompt=request.prompt,
                    output_format=output_format,
                    model=self.model,  # Pasar modelo para Guidance
                    max_tokens=request.max_tokens or self.config.max_new_tokens,
                    temperature=request.temperature or self.config.temperature,
                    top_p=request.top_p or self.config.top_p,
                    top_k=request.top_k or self.config.top_k
                )

            response_time = time.time() - start_time

            if structured_result:
                # Éxito con Guidance
                self.metrics["guidance_requests"] += 1

                # Calcular métricas de uso
                prompt_tokens = self.tokenizer.encode(request.prompt, add_special_tokens=True)
                # Para respuestas estructuradas, estimar tokens de completion
                completion_text = json.dumps(structured_result) if isinstance(structured_result, dict) else str(structured_result)
                completion_tokens = self.tokenizer.encode(completion_text, add_special_tokens=False)

                usage = {
                    "prompt_tokens": len(prompt_tokens),
                    "completion_tokens": len(completion_tokens),
                    "total_tokens": len(prompt_tokens) + len(completion_tokens),
                    "response_time_seconds": response_time,
                    "structured_output": True,
                    "output_format": output_format
                }

                # Actualizar métricas
                self._update_metrics(usage, response_time)
                self._update_guidance_metrics(success=True)

                # Convertir respuesta estructurada a texto
                if isinstance(structured_result, dict):
                    generated_text = json.dumps(structured_result, indent=2, ensure_ascii=False)
                else:
                    generated_text = str(structured_result)

                return InferenceResponse(
                    text=generated_text,
                    usage=usage,
                    model_version=self.model.config.version,
                    generated_at=time.time(),
                    structured_output=True,
                    schema_used=request.schema if request.schema else None,
                    validation_passed=True,  # Guidance ya valida internamente
                    guidance_used=True
                )
            else:
                # Fallback a generación estándar
                logger.warning("⚠️ Guidance falló, usando generación estándar")
                self._update_guidance_metrics(success=False)

                # Llamar recursivamente sin Guidance
                request.structured_output = False
                return await self.generate(request)

        except Exception as e:
            logger.error(f"❌ Error en generación Guidance: {e}")
            self._update_guidance_metrics(success=False)
            # Fallback a método estándar
            logger.info("🔄 Fallback a generación estándar por error")
            request.structured_output = False
            return await self.generate(request)

    async def _generate_with_coordinator(self, request: InferenceRequest, model_name: str, start_time: float) -> InferenceResponse:
        """Generar usando InferenceCoordinator para gestión federada de modelos."""
        try:
            # Importar InferenceCoordinator si no está disponible
            _import_inference_coordinator()
            if not InferenceCoordinator or not CoordinatorInferenceRequest:
                raise RuntimeError("InferenceCoordinator not available")

            # Crear solicitud coordinada
            coord_request = CoordinatorInferenceRequest(
                model_name=model_name,
                input_data=request.prompt,
                parameters={
                    'max_tokens': request.max_tokens,
                    'temperature': request.temperature,
                    'top_p': request.top_p,
                    'top_k': request.top_k
                },
                require_federated_version=True,
                quality_check=True
            )

            # Procesar con coordinador
            coord_result = await self.inference_coordinator.process_inference_request(coord_request)

            if coord_result.success:
                # Convertir resultado coordinado a InferenceResponse
                usage = {
                    "prompt_tokens": len(self.tokenizer.encode(request.prompt, add_special_tokens=True)),
                    "completion_tokens": len(self.tokenizer.encode(coord_result.output, add_special_tokens=False)) if isinstance(coord_result.output, str) else 0,
                    "total_tokens": 0,  # Se calculará abajo
                    "response_time_seconds": coord_result.processing_time
                }
                usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]

                return InferenceResponse(
                    text=coord_result.output if isinstance(coord_result.output, str) else str(coord_result.output),
                    usage=usage,
                    model_version=coord_result.model_version,
                    generated_at=time.time(),
                    structured_output=False,
                    guidance_used=False
                )
            else:
                # Fallback a generación directa si el coordinador falla
                logger.warning(f"⚠️ Coordinator failed: {coord_result.error_message}, using direct generation")
                return await self.generate(request, use_coordinator=False)

        except Exception as e:
            logger.error(f"❌ Coordinator generation failed: {e}")
            # Fallback a generación directa
            return await self.generate(request, use_coordinator=False)

    def _update_guidance_metrics(self, success: bool):
        """Actualizar métricas específicas de Guidance."""
        if success:
            self.metrics["guidance_success_rate"] = (
                self.metrics["guidance_success_rate"] * (self.metrics["guidance_requests"] - 1) + 1
            ) / self.metrics["guidance_requests"]
        else:
            self.metrics["guidance_success_rate"] = (
                self.metrics["guidance_success_rate"] * self.metrics["guidance_requests"]
            ) / (self.metrics["guidance_requests"] + 1)
            self.metrics["schema_validation_errors"] += 1

    async def _check_model_drift(self):
        """Verificar deriva del modelo."""
        try:
            drift_result = await self.drift_monitor.check_drift()

            if drift_result.get("alert_triggered", False):
                self.metrics["drift_alerts"] += 1
                logger.warning(f"🚨 Alerta de deriva: {drift_result['reason']}")

        except Exception as e:
            logger.error(f"❌ Error verificando deriva: {e}")

    def _generate_sync(self, prompt: str, gen_kwargs: Dict[str, Any]) -> torch.Tensor:
        """Generación síncrona (ejecutada en thread pool)."""
        # Tokenizar prompt con tokenizer real
        inputs = self.tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
        input_ids = inputs["input_ids"].to(self.device)

        with torch.no_grad():
            # Generar
            output = self.model.generate(
                input_ids,
                **gen_kwargs
            )

        return output

    def _decode_tokens(self, tokens: torch.Tensor) -> str:
        """Decodificar tokens a texto usando tokenizer real."""
        # Usar tokenizer real para decodificar
        decoded_text = self.tokenizer.decode(tokens[0], skip_special_tokens=True)
        return decoded_text

    def _update_metrics(self, usage: Dict[str, Any], response_time: float):
        """Actualizar métricas globales."""
        self.metrics["total_requests"] += 1
        self.metrics["total_tokens_generated"] += usage["completion_tokens"]

        # Actualizar tiempo promedio de respuesta
        prev_avg = self.metrics["avg_response_time"]
        self.metrics["avg_response_time"] = (prev_avg * (self.metrics["total_requests"] - 1) + response_time) / self.metrics["total_requests"]

        # Actualizar métricas de salidas estructuradas
        if usage.get("structured_output", False):
            self.metrics["structured_output_rate"] = (
                self.metrics["structured_output_rate"] * (self.metrics["total_requests"] - 1) + 1
            ) / self.metrics["total_requests"]

        # Actualizar métricas de esquemas personalizados
        if "schema_used" in usage and usage["schema_used"]:
            self.metrics["custom_schema_requests"] += 1

        # Actualizar métricas de streaming estructurado
        if usage.get("streaming", False) and usage.get("structured_output", False):
            self.metrics["streaming_structured_requests"] += 1

    async def generate_stream(
        self,
        request: InferenceRequest,
        structured_output: Optional[bool] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generar texto en streaming con Server-Sent Events.

        Args:
            request: Solicitud de inferencia
            structured_output: Forzar salida estructurada con Guidance (opcional)

        Yields:
            Chunks de texto generado en formato SSE
        """
        if not self.is_loaded:
            yield f"data: {json.dumps({'error': 'Modelo no cargado'})}\n\n"
            return

        try:
            # Determinar si usar Guidance para salida estructurada
            effective_structured_output = structured_output if structured_output is not None else request.structured_output

            use_guidance = (
                self.config.enable_guidance and
                self.structured_generator and
                effective_structured_output
            )

            if use_guidance:
                # Para Guidance, generar respuesta completa y simular streaming
                async for chunk in self._generate_guidance_stream(request):
                    yield chunk
                return
            # Tokenizar prompt
            inputs = self.tokenizer(request.prompt, return_tensors="pt", padding=True, truncation=True)
            input_ids = inputs["input_ids"].to(self.device)

            # Preparar parámetros de generación
            gen_kwargs = {
                "max_new_tokens": request.max_tokens or self.config.max_new_tokens,
                "temperature": request.temperature or self.config.temperature,
                "top_p": request.top_p or self.config.top_p,
                "top_k": request.top_k or self.config.top_k,
                "repetition_penalty": self.config.repetition_penalty,
                "do_sample": self.config.do_sample,
                "pad_token_id": self.tokenizer.pad_token_id,
                "eos_token_id": self.tokenizer.eos_token_id,
            }

            generated_tokens = input_ids.clone()
            generated_text = ""

            with torch.no_grad():
                for _ in range(gen_kwargs["max_new_tokens"]):
                    # Obtener logits para el último token
                    outputs = self.model(generated_tokens)
                    next_token_logits = outputs["logits"][:, -1, :]

                    # Aplicar temperatura
                    if gen_kwargs["temperature"] != 1.0:
                        next_token_logits = next_token_logits / gen_kwargs["temperature"]

                    # Aplicar top-k
                    if gen_kwargs["top_k"] > 0:
                        top_k_logits, top_k_indices = torch.topk(next_token_logits, gen_kwargs["top_k"], dim=-1)
                        next_token_logits = torch.where(
                            next_token_logits < top_k_logits[:, -1:].expand_as(next_token_logits),
                            torch.full_like(next_token_logits, float('-inf')),
                            next_token_logits
                        )

                    # Aplicar top-p
                    if gen_kwargs["top_p"] < 1.0:
                        sorted_logits, sorted_indices = torch.sort(next_token_logits, descending=True)
                        cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)

                        sorted_logits = torch.where(
                            cumulative_probs > gen_kwargs["top_p"],
                            torch.full_like(sorted_logits, float('-inf')),
                            sorted_logits
                        )

                        next_token_logits = torch.gather(
                            sorted_logits,
                            dim=-1,
                            index=torch.argsort(sorted_indices, dim=-1)
                        )

                    # Sample next token
                    if gen_kwargs["do_sample"]:
                        next_token = torch.multinomial(F.softmax(next_token_logits, dim=-1), num_samples=1)
                    else:
                        next_token = torch.argmax(next_token_logits, dim=-1, keepdim=True)

                    # Append to sequence
                    generated_tokens = torch.cat([generated_tokens, next_token], dim=-1)

                    # Decode new token
                    new_token_text = self.tokenizer.decode(next_token[0], skip_special_tokens=True)
                    generated_text += new_token_text

                    # Yield chunk
                    chunk_data = {
                        "token": new_token_text,
                        "text_so_far": generated_text,
                        "finished": False
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"

                    # Check for EOS
                    if next_token.item() == gen_kwargs["eos_token_id"]:
                        break

            # Final chunk
            final_data = {
                "token": "",
                "text_so_far": generated_text,
                "finished": True
            }
            yield f"data: {json.dumps(final_data)}\n\n"

        except Exception as e:
            error_data = {
                "error": f"Error en streaming: {str(e)}",
                "finished": True
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    async def _generate_guidance_stream(
        self,
        request: InferenceRequest
    ) -> AsyncGenerator[str, None]:
        """
        Generar respuesta estructurada con Guidance y simular streaming.
        """
        try:
            # Generar respuesta completa con Guidance
            response = await self._generate_with_guidance(request, time.time())

            if response:
                # Convertir respuesta a JSON string si es dict
                if isinstance(response.text, dict):
                    full_text = json.dumps(response.text, indent=2, ensure_ascii=False)
                else:
                    full_text = str(response.text)

                # Simular streaming dividiendo en chunks
                chunk_size = 50  # caracteres por chunk
                words = full_text.split()
                current_text = ""

                for i, word in enumerate(words):
                    current_text += word + " "

                    # Enviar chunk cada cierto número de palabras o al final
                    if (i + 1) % 3 == 0 or i == len(words) - 1:
                        chunk_data = {
                            "token": word + " ",
                            "text_so_far": current_text.strip(),
                            "finished": i == len(words) - 1,
                            "structured_output": True,
                            "guidance_used": True
                        }
                        yield f"data: {json.dumps(chunk_data)}\n\n"

                        # Pequeña pausa para simular generación
                        await asyncio.sleep(0.01)
            else:
                # Error en generación Guidance
                error_data = {
                    "error": "Error generando respuesta estructurada",
                    "finished": True
                }
                yield f"data: {json.dumps(error_data)}\n\n"

        except Exception as e:
            error_data = {
                "error": f"Error en streaming Guidance: {str(e)}",
                "finished": True
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    async def get_health_status(self) -> Dict[str, Any]:
        """Obtener estado de salud del servicio con métricas dinámicas."""
        # Obtener métricas de performance en tiempo real
        performance_collector = get_performance_collector()
        current_metrics = performance_collector.get_current_metrics()

        # Combinar métricas locales con métricas de sistema
        combined_metrics = self.metrics.copy()
        if current_metrics:
            combined_metrics.update({
                "system_cpu_percent": current_metrics.get("system", {}).get("cpu_percent", 0.0),
                "system_memory_percent": current_metrics.get("system", {}).get("memory_percent", 0.0),
                "system_memory_used_gb": current_metrics.get("system", {}).get("memory_used_gb", 0.0),
                "active_threads": current_metrics.get("system", {}).get("active_threads", 0),
                "open_files": current_metrics.get("system", {}).get("open_files", 0),
                "avg_response_time_system": current_metrics.get("performance", {}).get("avg_api_latency_ms", 0.0),
                "cache_hit_ratio_system": current_metrics.get("ailoos", {}).get("cache_hit_ratio", 0.0),
                "db_connection_pool_usage_system": current_metrics.get("ailoos", {}).get("db_connection_pool_usage", 0.0)
            })

        base_status = {
            "status": "healthy" if self.is_loaded else "unhealthy",
            "model_loaded": self.is_loaded,
            "device": str(self.device),
            "model_info": {
                "parameters": {
                    "total": sum(p.numel() for p in self.model.parameters()) if self.is_loaded else 0
                }
            } if self.is_loaded else None,
            "metrics": combined_metrics,
            "config": {
                "max_batch_size": self.config.max_batch_size,
                "max_concurrent_requests": self.config.max_concurrent_requests,
                "timeout": self.config.request_timeout_seconds
            }
        }

        # Añadir información de Maturity 2
        maturity2_status = {
            "quantization": {
                "enabled": self.config.enable_quantization,
                "type": self.config.quantization_type if self.config.enable_quantization else None,
                "memory_savings": self.metrics.get("quantization_memory_savings", 0.0)
            },
            "drift_monitoring": {
                "enabled": self.config.enable_drift_monitoring,
                "alerts": self.metrics.get("drift_alerts", 0),
                "last_check": None  # Placeholder
            },
            "vllm_batching": {
                "enabled": self.config.enable_vllm_batching,
                "throughput": self.metrics.get("vllm_throughput", 0.0),
                "available": self.vllm_engine is not None
            },
            "guidance_structured_output": {
                "enabled": self.config.enable_guidance,
                "available": self.structured_generator is not None and self.structured_generator.is_available(),
                "output_format": self.config.guidance_output_format,
                "validation_enabled": self.config.guidance_validation_enabled,
                "success_rate": self.metrics.get("guidance_success_rate", 0.0),
                "structured_output_rate": self.metrics.get("structured_output_rate", 0.0),
                "validation_errors": self.metrics.get("schema_validation_errors", 0)
            }
        }

        base_status["maturity2"] = maturity2_status
        return base_status

    def create_fastapi_app(self) -> FastAPI:
        """Crear aplicación FastAPI para la API."""
        app = FastAPI(
            title="EmpoorioLM Inference API",
            description="API de inferencia para modelos EmpoorioLM v1.0",
            version="1.0.0"
        )

        @app.on_event("startup")
        async def startup_event():
            """Cargar modelo al iniciar."""
            success = await self.load_model()
            if not success:
                logger.error("❌ Falló carga del modelo al iniciar")
                raise RuntimeError("No se pudo cargar el modelo")

        @app.get("/health")
        async def health():
            """Endpoint de health check."""
            return await self.get_health_status()

        @app.post("/generate")
        async def generate_text(request: Dict[str, Any]):
            """Endpoint principal de generación."""
            try:
                inference_request = InferenceRequest(**request)

                if inference_request.stream:
                    # Streaming response
                    return StreamingResponse(
                        self.generate_stream(inference_request),
                        media_type="text/plain"
                    )
                else:
                    # Regular response
                    response = await self.generate(inference_request)
                    return response.to_dict()

            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @app.get("/models")
        async def list_models():
            """Listar modelos disponibles."""
            return {
                "models": [{
                    "id": "empoorio_lm_v1.0",
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "ailoos"
                }]
            }

        # Endpoints Maturity 2
        @app.post("/quantize")
        async def quantize_model_endpoint(request: Dict[str, Any]):
            """Endpoint para cuantizar modelo."""
            if not self.config.enable_quantization:
                raise HTTPException(status_code=400, detail="Cuantización no habilitada")

            try:
                quantization_type = request.get("quantization_type", "int8")
                output_path = request.get("output_path")

                if not output_path:
                    raise HTTPException(status_code=400, detail="output_path requerido")

                # Cuantizar modelo
                result = quantize_empoorio_model(
                    model_path=self.config.model_path,
                    output_path=output_path,
                    quantization_type=quantization_type
                )

                return {"status": "success", "result": result}

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error en cuantización: {str(e)}")

        @app.get("/drift/status")
        async def get_drift_status():
            """Obtener estado del monitoreo de deriva."""
            if not self.config.enable_drift_monitoring or not self.drift_monitor:
                return {"enabled": False, "message": "Monitoreo de deriva no habilitado"}

            try:
                report = await self.drift_monitor.get_drift_report(days=7)
                return {
                    "enabled": True,
                    "report": report,
                    "alerts": self.metrics.get("drift_alerts", 0)
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error obteniendo estado de deriva: {str(e)}")

        @app.post("/drift/check")
        async def check_drift_now():
            """Forzar verificación de deriva."""
            if not self.config.enable_drift_monitoring or not self.drift_monitor:
                raise HTTPException(status_code=400, detail="Monitoreo de deriva no habilitado")

            try:
                result = await self.drift_monitor.check_drift()
                return {"status": "checked", "result": result}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error verificando deriva: {str(e)}")

        @app.get("/performance")
        async def get_performance_metrics():
            """Obtener métricas de rendimiento detalladas."""
            base_metrics = self.metrics.copy()

            # Añadir métricas de vLLM si está disponible
            if self.vllm_engine:
                vllm_metrics = self.vllm_engine.get_performance_metrics()
                base_metrics["vllm"] = vllm_metrics

            return base_metrics

        # Endpoints de attestación TEE
        @app.post("/attestation/validate")
        async def validate_tee_attestation(request: Dict[str, Any]):
            """Validar attestación remota de enclave TEE."""
            try:
                from ..validation import get_security_validator

                instance_name = request.get("instance_name")
                project_id = request.get("project_id")
                zone = request.get("zone")
                expected_measurements = request.get("expected_measurements")

                if not all([instance_name, project_id, zone]):
                    raise HTTPException(
                        status_code=400,
                        detail="instance_name, project_id y zone son requeridos"
                    )

                validator = get_security_validator()
                result = validator.validate_tee_attestation(
                    instance_name=instance_name,
                    project_id=project_id,
                    zone=zone,
                    expected_measurements=expected_measurements
                )

                return result.to_dict()

            except Exception as e:
                logger.error(f"Error en validación de attestación TEE: {e}")
                raise HTTPException(status_code=500, detail=f"Error de attestación: {str(e)}")

        @app.get("/attestation/reference-measurements")
        async def get_reference_measurements():
            """Obtener mediciones de referencia para attestación."""
            try:
                from ..validation.tee_attestation_validator import get_tee_attestation_validator

                validator = get_tee_attestation_validator()
                measurements = {}

                # Obtener todas las mediciones de referencia
                measurements = await self._get_reference_measurements(validator)

                return {"reference_measurements": measurements}

            except Exception as e:
                logger.error(f"Error obteniendo mediciones de referencia: {e}")
                raise HTTPException(status_code=500, detail=f"Error obteniendo mediciones: {str(e)}")

        @app.post("/attestation/reference-measurements")
        async def update_reference_measurements(request: Dict[str, Any]):
            """Actualizar mediciones de referencia para attestación."""
            try:
                from ..validation.tee_attestation_validator import (
                    get_tee_attestation_validator,
                    ReferenceMeasurements
                )

                key = request.get("key", "default")
                measurements_data = request.get("measurements", {})

                # Crear objeto ReferenceMeasurements
                measurements = ReferenceMeasurements(
                    platform_firmware_hash=measurements_data.get("platform_firmware_hash", ""),
                    kernel_hash=measurements_data.get("kernel_hash", ""),
                    initrd_hash=measurements_data.get("initrd_hash", ""),
                    guest_policy=measurements_data.get("guest_policy", ""),
                    family_id=measurements_data.get("family_id"),
                    image_id=measurements_data.get("image_id"),
                    launch_measurement=measurements_data.get("launch_measurement")
                )

                validator = get_tee_attestation_validator()
                validator.update_reference_measurements(key, measurements)

                return {"status": "success", "message": f"Mediciones actualizadas para: {key}"}

            except Exception as e:
                logger.error(f"Error actualizando mediciones de referencia: {e}")
                raise HTTPException(status_code=500, detail=f"Error actualizando mediciones: {str(e)}")

        @app.get("/attestation/health")
        async def get_attestation_health():
            """Obtener estado de salud del sistema de attestación TEE."""
            try:
                from ..validation.tee_attestation_validator import get_tee_attestation_validator

                validator = get_tee_attestation_validator()

                # Verificar conectividad con GCP
                gcp_status = await self._check_gcp_connectivity()

                # Obtener estadísticas de mediciones
                reference_count = len(validator.reference_measurements)

                return {
                    "status": "healthy",
                    "gcp_connectivity": gcp_status,
                    "reference_measurements_count": reference_count,
                    "supported_tee_types": ["SEV_SNP"],
                    "last_updated": max(
                        (m.updated_at for m in validator.reference_measurements.values()),
                        default=None
                    )
                }

            except Exception as e:
                logger.error(f"Error obteniendo estado de attestación: {e}")
                return {
                    "status": "unhealthy",
                    "error": str(e),
                    "gcp_connectivity": "unknown",
                    "reference_measurements_count": 0
                }

        @app.get("/attestation/metrics")
        async def get_attestation_metrics():
            """Obtener métricas de monitoreo de attestación TEE."""
            try:
                from ..validation.tee_attestation_validator import get_tee_attestation_validator

                validator = get_tee_attestation_validator()
                metrics = validator.get_attestation_metrics()

                return metrics

            except Exception as e:
                logger.error(f"Error obteniendo métricas de attestación: {e}")
                raise HTTPException(status_code=500, detail=f"Error obteniendo métricas: {str(e)}")

        return app

    def start_server(self):
        """Iniciar servidor FastAPI."""
        app = self.create_fastapi_app()

        logger.info(f"🌐 Iniciando servidor en {self.config.host}:{self.config.port}")

        uvicorn.run(
            app,
            host=self.config.host,
            port=self.config.port,
            workers=self.config.workers,
            log_level=self.config.log_level.lower()
        )


# Funciones de conveniencia
def create_inference_api(
    model_path: str = "./models/empoorio_lm/v1.0.0",
    device: str = "auto",
    port: int = 8000,
    inference_coordinator=None
) -> EmpoorioLMInferenceAPI:
    """
    Crear API de inferencia con configuración por defecto.

    Args:
        model_path: Ruta del modelo
        device: Dispositivo ('auto', 'cpu', 'cuda', 'mps')
        port: Puerto del servidor
        inference_coordinator: Coordinador de inferencia federada (opcional)

    Returns:
        Instancia de la API
    """
    config = InferenceConfig(
        model_path=model_path,
        device=device,
        port=port
    )

    return EmpoorioLMInferenceAPI(config, inference_coordinator)


async def generate_text(
    prompt: str,
    model_path: str = "./models/empoorio_lm/v1.0.0",
    **kwargs
) -> str:
    """
    Función de conveniencia para generar texto.

    Args:
        prompt: Texto de entrada
        model_path: Ruta del modelo
        **kwargs: Parámetros adicionales

    Returns:
        Texto generado
    """
    api = create_inference_api(model_path)
    await api.load_model()

    request = InferenceRequest(prompt=prompt, **kwargs)
    response = await api.generate(request)

    return response.text


if __name__ == "__main__":
    # Test de la API
    print("🧪 Probando EmpoorioLM Inference API...")

    # Crear API
    api = create_inference_api()

    # Cargar modelo
    success = asyncio.run(api.load_model())

    if success:
        print("✅ API lista para inferencia")

        # Test de generación
        test_prompt = "Hola, ¿cómo estás?"
        print(f"📝 Prompt: {test_prompt}")

        # Generar respuesta
        response = asyncio.run(generate_text(test_prompt))
        print(f"🤖 Respuesta: {response}")

        print("🎉 API funcionando correctamente")
    else:
        print("❌ Falló carga del modelo")