"""
Runtime ligero para inferencia en dispositivos edge.

Proporciona un motor de inferencia optimizado para dispositivos móviles/IoT
con gestión eficiente de memoria, APIs simples y monitoreo de rendimiento.
"""

import torch
import torch.nn as nn
import logging
import time
import threading
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import psutil
import os
from concurrent.futures import ThreadPoolExecutor
import queue

logger = logging.getLogger(__name__)


class InferenceBackend(Enum):
    """Backends de inferencia disponibles."""
    PYTORCH_CPU = "pytorch_cpu"
    PYTORCH_GPU = "pytorch_gpu"
    ONNX_RUNTIME = "onnx_runtime"
    TENSORRT = "tensorrt"
    COREML = "coreml"
    NNAPI = "nnapi"


class ModelFormat(Enum):
    """Formatos de modelo soportados."""
    PYTORCH = "pytorch"
    ONNX = "onnx"
    TENSORRT = "tensorrt"
    COREML = "coreml"
    QUANTIZED = "quantized"


@dataclass
class InferenceRequest:
    """Solicitud de inferencia."""
    input_data: Any
    request_id: str
    timestamp: float = field(default_factory=time.time)
    priority: int = 1  # 1=baja, 5=alta
    callback: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InferenceResult:
    """Resultado de inferencia."""
    output: Any
    request_id: str
    latency_ms: float
    memory_usage_mb: float
    confidence_score: Optional[float] = None
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class RuntimeMetrics:
    """Métricas del runtime."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_latency_ms: float = 0.0
    peak_memory_usage_mb: float = 0.0
    current_memory_usage_mb: float = 0.0
    throughput_requests_per_sec: float = 0.0
    uptime_seconds: float = 0.0
    last_request_timestamp: float = 0.0


@dataclass
class LightweightRuntimeConfig:
    """Configuración del runtime ligero."""
    # Backend y formato
    preferred_backend: InferenceBackend = InferenceBackend.PYTORCH_CPU
    supported_formats: List[ModelFormat] = field(default_factory=lambda: [ModelFormat.PYTORCH, ModelFormat.ONNX])

    # Gestión de memoria
    max_memory_usage_mb: int = 512
    enable_memory_pooling: bool = True
    memory_cleanup_interval_seconds: int = 60

    # Procesamiento
    max_concurrent_requests: int = 4
    request_queue_size: int = 100
    enable_async_processing: bool = True

    # Monitoreo
    enable_performance_monitoring: bool = True
    metrics_update_interval_seconds: int = 10
    enable_health_checks: bool = True

    # Optimizaciones
    enable_model_caching: bool = True
    enable_input_preprocessing: bool = True
    enable_output_postprocessing: bool = True


class MemoryPool:
    """Pool de memoria para gestión eficiente."""

    def __init__(self, max_memory_mb: int):
        self.max_memory_mb = max_memory_mb
        self.allocated_memory_mb = 0
        self.memory_blocks: Dict[str, torch.Tensor] = {}
        self.lock = threading.Lock()

    def allocate(self, size_mb: float, key: str) -> bool:
        """Asignar bloque de memoria."""
        with self.lock:
            if self.allocated_memory_mb + size_mb > self.max_memory_mb:
                return False

            self.allocated_memory_mb += size_mb
            # Crear tensor placeholder
            self.memory_blocks[key] = torch.zeros(1)  # Placeholder
            return True

    def deallocate(self, key: str):
        """Liberar bloque de memoria."""
        with self.lock:
            if key in self.memory_blocks:
                # Estimar tamaño (simplificado)
                size_mb = 10  # Placeholder
                self.allocated_memory_mb = max(0, self.allocated_memory_mb - size_mb)
                del self.memory_blocks[key]

    def get_usage(self) -> float:
        """Obtener uso de memoria actual."""
        return self.allocated_memory_mb


class LightweightRuntime:
    """
    Runtime ligero para inferencia en dispositivos edge.

    Características principales:
    - Motor de inferencia optimizado para recursos limitados
    - Gestión inteligente de memoria con pooling
    - Procesamiento asíncrono con cola de solicitudes
    - Monitoreo de rendimiento en tiempo real
    - Soporte para múltiples formatos de modelo
    - APIs simples para integración
    """

    def __init__(self, config: LightweightRuntimeConfig):
        self.config = config

        # Estado del runtime
        self.is_running = False
        self.start_time = time.time()

        # Modelos cargados
        self.loaded_models: Dict[str, Any] = {}
        self.model_metadata: Dict[str, Dict[str, Any]] = {}

        # Gestión de memoria
        self.memory_pool = MemoryPool(config.max_memory_usage_mb)

        # Procesamiento de solicitudes
        self.request_queue = queue.PriorityQueue(maxsize=config.request_queue_size)
        self.executor = ThreadPoolExecutor(max_workers=config.max_concurrent_requests)
        self.processing_thread: Optional[threading.Thread] = None

        # Monitoreo
        self.metrics = RuntimeMetrics()
        self.metrics_thread: Optional[threading.Thread] = None
        self.health_check_thread: Optional[threading.Thread] = None

        # Callbacks
        self.request_callbacks: List[Callable] = []
        self.error_callbacks: List[Callable] = []

        logger.info("🔧 LightweightRuntime inicializado")
        logger.info(f"   Backend preferido: {config.preferred_backend.value}")
        logger.info(f"   Memoria máxima: {config.max_memory_usage_mb}MB")
        logger.info(f"   Solicitudes concurrentes: {config.max_concurrent_requests}")

    def start(self):
        """Iniciar el runtime."""
        if self.is_running:
            logger.warning("⚠️ Runtime ya está ejecutándose")
            return

        self.is_running = True
        self.start_time = time.time()

        # Iniciar hilos de procesamiento
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()

        # Iniciar monitoreo
        if self.config.enable_performance_monitoring:
            self.metrics_thread = threading.Thread(target=self._metrics_loop, daemon=True)
            self.metrics_thread.start()

        if self.config.enable_health_checks:
            self.health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
            self.health_check_thread.start()

        logger.info("🚀 LightweightRuntime iniciado")

    def stop(self):
        """Detener el runtime."""
        if not self.is_running:
            return

        self.is_running = False

        # Esperar a que terminen los hilos
        if self.processing_thread:
            self.processing_thread.join(timeout=5.0)

        if self.metrics_thread:
            self.metrics_thread.join(timeout=2.0)

        if self.health_check_thread:
            self.health_check_thread.join(timeout=2.0)

        # Limpiar recursos
        self.executor.shutdown(wait=True)
        self.memory_pool = MemoryPool(self.config.max_memory_usage_mb)

        logger.info("🛑 LightweightRuntime detenido")

    def load_model(
        self,
        model_path: str,
        model_id: str,
        model_format: ModelFormat = ModelFormat.PYTORCH,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Cargar un modelo en el runtime.

        Args:
            model_path: Ruta del modelo
            model_id: ID único del modelo
            model_format: Formato del modelo
            metadata: Metadatos adicionales

        Returns:
            True si se cargó exitosamente
        """
        try:
            if model_id in self.loaded_models:
                logger.warning(f"⚠️ Modelo {model_id} ya está cargado")
                return True

            # Verificar formato soportado
            if model_format not in self.config.supported_formats:
                logger.error(f"❌ Formato {model_format.value} no soportado")
                return False

            # Estimar tamaño del modelo
            model_size_mb = self._estimate_model_size(model_path)

            # Verificar memoria disponible
            if not self.memory_pool.allocate(model_size_mb, model_id):
                logger.error(f"❌ Memoria insuficiente para cargar modelo {model_id}")
                return False

            # Cargar modelo según formato
            model = self._load_model_by_format(model_path, model_format)

            if model is None:
                self.memory_pool.deallocate(model_id)
                return False

            # Almacenar modelo
            self.loaded_models[model_id] = model
            self.model_metadata[model_id] = {
                "path": model_path,
                "format": model_format,
                "size_mb": model_size_mb,
                "loaded_at": time.time(),
                "load_count": 0,
                **(metadata or {})
            }

            logger.info(f"✅ Modelo {model_id} cargado ({model_size_mb:.1f}MB)")
            return True

        except Exception as e:
            logger.error(f"❌ Error cargando modelo {model_id}: {e}")
            return False

    def unload_model(self, model_id: str) -> bool:
        """Descargar un modelo."""
        try:
            if model_id not in self.loaded_models:
                return True

            # Liberar memoria
            self.memory_pool.deallocate(model_id)

            # Remover modelo
            del self.loaded_models[model_id]
            del self.model_metadata[model_id]

            logger.info(f"🗑️ Modelo {model_id} descargado")
            return True

        except Exception as e:
            logger.error(f"❌ Error descargando modelo {model_id}: {e}")
            return False

    def run_inference(
        self,
        model_id: str,
        input_data: Any,
        request_id: Optional[str] = None,
        priority: int = 1,
        callback: Optional[Callable] = None,
        async_mode: bool = True
    ) -> Union[InferenceResult, str]:
        """
        Ejecutar inferencia.

        Args:
            model_id: ID del modelo
            input_data: Datos de entrada
            request_id: ID de solicitud (opcional)
            priority: Prioridad (1-5)
            callback: Callback para resultados asíncronos
            async_mode: Modo asíncrono

        Returns:
            Resultado de inferencia o ID de solicitud
        """
        if not self.is_running:
            raise RuntimeError("Runtime no está ejecutándose")

        if model_id not in self.loaded_models:
            raise ValueError(f"Modelo {model_id} no está cargado")

        # Generar ID de solicitud
        if request_id is None:
            request_id = f"req_{int(time.time() * 1000)}_{np.random.randint(1000)}"

        # Crear solicitud
        request = InferenceRequest(
            input_data=input_data,
            request_id=request_id,
            priority=priority,
            callback=callback
        )

        if async_mode:
            # Agregar a cola
            try:
                self.request_queue.put((priority, request), timeout=1.0)
                return request_id
            except queue.Full:
                raise RuntimeError("Cola de solicitudes llena")
        else:
            # Procesar inmediatamente
            return self._process_request(request)

    def get_metrics(self) -> RuntimeMetrics:
        """Obtener métricas actuales."""
        self.metrics.uptime_seconds = time.time() - self.start_time
        self.metrics.current_memory_usage_mb = self.memory_pool.get_usage()
        return self.metrics

    def get_loaded_models(self) -> Dict[str, Dict[str, Any]]:
        """Obtener información de modelos cargados."""
        return self.model_metadata.copy()

    def add_request_callback(self, callback: Callable):
        """Agregar callback para solicitudes."""
        self.request_callbacks.append(callback)

    def add_error_callback(self, callback: Callable):
        """Agregar callback para errores."""
        self.error_callbacks.append(callback)

    def _processing_loop(self):
        """Bucle principal de procesamiento."""
        logger.info("🔄 Iniciando bucle de procesamiento")

        while self.is_running:
            try:
                # Obtener solicitud de la cola
                priority, request = self.request_queue.get(timeout=1.0)

                # Procesar solicitud
                result = self._process_request(request)

                # Notificar callbacks
                for callback in self.request_callbacks:
                    try:
                        callback(result)
                    except Exception as e:
                        logger.warning(f"⚠️ Error en callback: {e}")

                # Ejecutar callback específico si existe
                if request.callback:
                    try:
                        request.callback(result)
                    except Exception as e:
                        logger.warning(f"⚠️ Error en callback específico: {e}")

                self.request_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"❌ Error en bucle de procesamiento: {e}")

        logger.info("🛑 Bucle de procesamiento terminado")

    def _process_request(self, request: InferenceRequest) -> InferenceResult:
        """Procesar una solicitud individual."""
        start_time = time.time()

        try:
            # Preparar entrada
            processed_input = self._preprocess_input(request.input_data)

            # Ejecutar inferencia
            model_id = request.metadata.get("model_id", list(self.loaded_models.keys())[0])
            model = self.loaded_models[model_id]

            with torch.no_grad():
                if self.config.preferred_backend == InferenceBackend.PYTORCH_CPU:
                    output = self._run_pytorch_inference(model, processed_input)
                else:
                    # Fallback a PyTorch
                    output = self._run_pytorch_inference(model, processed_input)

            # Post-procesar salida
            final_output = self._postprocess_output(output)

            # Calcular métricas
            latency_ms = (time.time() - start_time) * 1000
            memory_usage_mb = self.memory_pool.get_usage()

            # Estimar confianza (simplificado)
            confidence_score = self._estimate_confidence(final_output)

            # Actualizar estadísticas
            self._update_metrics(latency_ms, success=True)

            # Actualizar metadatos del modelo
            self.model_metadata[model_id]["load_count"] += 1
            self.model_metadata[model_id]["last_used"] = time.time()

            result = InferenceResult(
                output=final_output,
                request_id=request.request_id,
                latency_ms=latency_ms,
                memory_usage_mb=memory_usage_mb,
                confidence_score=confidence_score
            )

            return result

        except Exception as e:
            logger.error(f"❌ Error procesando solicitud {request.request_id}: {e}")

            # Actualizar estadísticas de error
            self._update_metrics((time.time() - start_time) * 1000, success=False)

            # Notificar callbacks de error
            for callback in self.error_callbacks:
                try:
                    callback(request, str(e))
                except Exception as callback_error:
                    logger.warning(f"⚠️ Error en callback de error: {callback_error}")

            return InferenceResult(
                output=None,
                request_id=request.request_id,
                latency_ms=(time.time() - start_time) * 1000,
                memory_usage_mb=self.memory_pool.get_usage(),
                error=str(e)
            )

    def _run_pytorch_inference(self, model: Any, input_data: Any) -> Any:
        """Ejecutar inferencia con PyTorch."""
        # Simular inferencia (en implementación real, ejecutar modelo)
        if isinstance(input_data, torch.Tensor):
            # Simular procesamiento
            time.sleep(0.01)  # Simular latencia
            return torch.randn_like(input_data)
        elif isinstance(input_data, (list, tuple)):
            return [torch.randn(1, 10) for _ in input_data]
        else:
            return torch.randn(1, 10)

    def _preprocess_input(self, input_data: Any) -> Any:
        """Pre-procesar datos de entrada."""
        if not self.config.enable_input_preprocessing:
            return input_data

        # Simular pre-procesamiento
        if isinstance(input_data, (str, int, float)):
            return torch.tensor([float(input_data)])
        elif isinstance(input_data, list):
            return torch.tensor(input_data, dtype=torch.float32)
        else:
            return input_data

    def _postprocess_output(self, output: Any) -> Any:
        """Post-procesar salida del modelo."""
        if not self.config.enable_output_postprocessing:
            return output

        # Simular post-procesamiento
        if isinstance(output, torch.Tensor):
            return output.tolist()
        else:
            return output

    def _estimate_confidence(self, output: Any) -> Optional[float]:
        """Estimar puntuación de confianza."""
        if isinstance(output, list) and len(output) > 0:
            # Para clasificaciones, usar el valor máximo
            if isinstance(output[0], (int, float)):
                return max(output) if output else None
        return None

    def _update_metrics(self, latency_ms: float, success: bool):
        """Actualizar métricas del runtime."""
        self.metrics.total_requests += 1

        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1

        # Actualizar latencia promedio
        total_requests = self.metrics.successful_requests + self.metrics.failed_requests
        if total_requests > 0:
            self.metrics.avg_latency_ms = (
                (self.metrics.avg_latency_ms * (total_requests - 1)) + latency_ms
            ) / total_requests

        # Actualizar uso de memoria
        current_memory = self.memory_pool.get_usage()
        self.metrics.peak_memory_usage_mb = max(
            self.metrics.peak_memory_usage_mb,
            current_memory
        )

        # Actualizar throughput
        uptime = time.time() - self.start_time
        if uptime > 0:
            self.metrics.throughput_requests_per_sec = self.metrics.total_requests / uptime

        self.metrics.last_request_timestamp = time.time()

    def _load_model_by_format(self, model_path: str, model_format: ModelFormat) -> Optional[Any]:
        """Cargar modelo según formato."""
        try:
            if model_format == ModelFormat.PYTORCH:
                # Simular carga de modelo PyTorch
                return {"type": "pytorch", "path": model_path}
            elif model_format == ModelFormat.ONNX:
                # Simular carga de modelo ONNX
                return {"type": "onnx", "path": model_path}
            else:
                logger.warning(f"⚠️ Formato {model_format.value} no implementado completamente")
                return {"type": model_format.value, "path": model_path}

        except Exception as e:
            logger.error(f"❌ Error cargando modelo {model_format.value}: {e}")
            return None

    def _estimate_model_size(self, model_path: str) -> float:
        """Estimar tamaño del modelo en MB."""
        try:
            size_bytes = os.path.getsize(model_path)
            return size_bytes / (1024 * 1024)  # Convertir a MB
        except:
            return 100.0  # Estimación por defecto

    def _metrics_loop(self):
        """Bucle de actualización de métricas."""
        while self.is_running:
            try:
                time.sleep(self.config.metrics_update_interval_seconds)
                # Las métricas se actualizan en _update_metrics()
            except Exception as e:
                logger.error(f"❌ Error en bucle de métricas: {e}")

    def _health_check_loop(self):
        """Bucle de verificación de salud."""
        while self.is_running:
            try:
                time.sleep(30)  # Verificar cada 30 segundos

                # Verificar memoria
                memory_usage = self.memory_pool.get_usage()
                if memory_usage > self.config.max_memory_usage_mb * 0.9:
                    logger.warning(f"⚠️ Uso de memoria alto: {memory_usage:.1f}MB")

                # Verificar modelos cargados
                if len(self.loaded_models) == 0:
                    logger.warning("⚠️ No hay modelos cargados")

                # Verificar cola de solicitudes
                queue_size = self.request_queue.qsize()
                if queue_size > self.config.request_queue_size * 0.8:
                    logger.warning(f"⚠️ Cola de solicitudes casi llena: {queue_size}")

            except Exception as e:
                logger.error(f"❌ Error en health check: {e}")


# Funciones de conveniencia
def create_lightweight_runtime_for_mobile(
    max_memory_mb: int = 512,
    max_concurrent_requests: int = 2
) -> LightweightRuntime:
    """
    Crear runtime optimizado para dispositivos móviles.

    Args:
        max_memory_mb: Memoria máxima en MB
        max_concurrent_requests: Máximo de solicitudes concurrentes

    Returns:
        Runtime configurado
    """
    config = LightweightRuntimeConfig(
        preferred_backend=InferenceBackend.PYTORCH_CPU,
        max_memory_usage_mb=max_memory_mb,
        max_concurrent_requests=max_concurrent_requests,
        enable_memory_pooling=True,
        enable_async_processing=True
    )

    return LightweightRuntime(config)


def create_lightweight_runtime_for_iot(
    max_memory_mb: int = 128,
    max_concurrent_requests: int = 1
) -> LightweightRuntime:
    """
    Crear runtime optimizado para dispositivos IoT.

    Args:
        max_memory_mb: Memoria máxima en MB
        max_concurrent_requests: Máximo de solicitudes concurrentes

    Returns:
        Runtime configurado
    """
    config = LightweightRuntimeConfig(
        preferred_backend=InferenceBackend.PYTORCH_CPU,
        max_memory_mb=max_memory_mb,
        max_concurrent_requests=max_concurrent_requests,
        enable_memory_pooling=True,
        enable_async_processing=False,  # IoT devices may prefer synchronous
        supported_formats=[ModelFormat.PYTORCH, ModelFormat.QUANTIZED]
    )

    return LightweightRuntime(config)


if __name__ == "__main__":
    # Demo del runtime ligero
    print("🚀 LightweightRuntime Demo")

    # Crear runtime para móvil
    runtime = create_lightweight_runtime_for_mobile()
    runtime.start()

    print("Runtime iniciado")
    print(f"Memoria máxima: {runtime.config.max_memory_usage_mb}MB")
    print(f"Solicitudes concurrentes: {runtime.config.max_concurrent_requests}")

    # Simular carga de modelo
    success = runtime.load_model("/fake/model/path", "test_model")
    print(f"Carga de modelo: {'Exitosa' if success else 'Fallida'}")

    # Simular inferencia
    try:
        result = runtime.run_inference("test_model", [1.0, 2.0, 3.0], async_mode=False)
        print(f"Inferencia completada en {result.latency_ms:.2f}ms")
        print(f"Resultado: {result.output}")
    except Exception as e:
        print(f"Error en inferencia: {e}")

    # Obtener métricas
    metrics = runtime.get_metrics()
    print(f"Solicitudes totales: {metrics.total_requests}")
    print(f"Latencia promedio: {metrics.avg_latency_ms:.2f}ms")

    runtime.stop()
    print("Runtime detenido")