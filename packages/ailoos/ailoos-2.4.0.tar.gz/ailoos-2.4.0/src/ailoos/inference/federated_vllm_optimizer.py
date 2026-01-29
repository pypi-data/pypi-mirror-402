"""
Optimizador de vLLM para entornos federated learning.
Optimizaciones de memoria y batching específicas para FL.
"""

import asyncio
import torch
import logging
import time
import numpy as np
from typing import Dict, List, Any, Optional, Union, AsyncGenerator, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import psutil
import gc

try:
    from vllm import LLM, SamplingParams
    from vllm.engine.arg_utils import EngineArgs
    VLLM_AVAILABLE = True
except ImportError:
    VLLM_AVAILABLE = False
    SamplingParams = Any
    logger = logging.getLogger(__name__)
    logger.warning("vLLM no disponible. Instalar con: pip install vllm")

from .vllm_batching import BatchingConfig, BatchRequest, BatchResponse, DynamicBatcher
from ..federated.federated_data_loader import FederatedDataLoader

logger = logging.getLogger(__name__)


@dataclass
class FederatedVLLMConfig:
    """Configuración específica para vLLM en entornos federados."""

    # Configuración base de vLLM
    base_config: BatchingConfig

    # Optimizaciones federadas
    federated_round_aware: bool = True
    memory_sharing_across_rounds: bool = True
    adaptive_batch_sizing: bool = True
    heterogeneous_hardware_support: bool = True

    # Límites de memoria para FL
    max_memory_per_round_gb: float = 4.0
    memory_reservation_ratio: float = 0.8  # 80% para inferencia, 20% reserva
    kv_cache_sharing_ratio: float = 0.6  # 60% del cache KV puede ser compartido

    # Optimizaciones de batching para FL
    min_batch_size_fl: int = 1  # Mínimo para nodos pequeños
    max_batch_size_fl: int = 16  # Máximo adaptativo
    batch_timeout_fl_ms: int = 100  # Timeout más agresivo para FL

    # Monitoreo de recursos
    resource_monitoring_interval: float = 1.0  # Segundos
    memory_pressure_threshold: float = 0.85  # 85% uso de memoria

    # Optimizaciones específicas de FL
    gradient_accumulation_steps: int = 1
    mixed_precision_inference: bool = True
    model_parallelism_degree: int = 1


class FederatedVLLOptimizer:
    """
    Optimizador de vLLM para federated learning.

    Características principales:
    - Optimización de memoria entre rondas FL
    - Batching adaptativo basado en capacidades del nodo
    - Cache KV compartido entre rondas
    - Monitoreo de recursos en tiempo real
    - Soporte para hardware heterogéneo
    """

    def __init__(self, config: FederatedVLLMConfig):
        self.config = config
        self.base_batcher: Optional[DynamicBatcher] = None
        self.llm: Optional[LLM] = None

        # Estado de optimización federada
        self.current_round_id: Optional[str] = None
        self.round_memory_state: Dict[str, Any] = {}
        self.shared_kv_cache: Dict[str, Any] = {}
        self.resource_monitor_task: Optional[asyncio.Task] = None

        # Métricas de optimización
        self.optimization_metrics = {
            "memory_efficiency": 0.0,
            "batch_utilization": 0.0,
            "cache_hit_ratio": 0.0,
            "resource_adaptation_count": 0,
            "round_transitions": 0
        }

        # Monitoreo de recursos
        self.resource_stats = {
            "gpu_memory_used": 0.0,
            "cpu_memory_used": 0.0,
            "gpu_utilization": 0.0,
            "last_check": time.time()
        }

        # Executor para operaciones CPU intensivas
        self.executor = ThreadPoolExecutor(max_workers=4)

        logger.info("🔧 FederatedVLLOptimizer inicializado")
        logger.info(f"   Memoria por ronda: {config.max_memory_per_round_gb}GB")
        logger.info(f"   Ratio de reserva: {config.memory_reservation_ratio}")
        logger.info(f"   Cache KV compartido: {config.kv_cache_sharing_ratio}")

    async def initialize_for_round(self, round_id: str, node_capabilities: Dict[str, Any]) -> bool:
        """
        Inicializar optimizador para una nueva ronda FL.

        Args:
            round_id: ID de la ronda federada
            node_capabilities: Capacidades del nodo actual

        Returns:
            True si inicialización exitosa
        """
        self.current_round_id = round_id
        logger.info(f"🔄 Inicializando optimizador para ronda: {round_id}")

        try:
            # Limpiar estado anterior si existe
            if self.base_batcher:
                await self._cleanup_previous_round()

            # Adaptar configuración basado en capacidades del nodo
            adapted_config = self._adapt_config_for_node(node_capabilities)

            # Inicializar batcher con configuración adaptada
            self.base_batcher = DynamicBatcher(adapted_config)

            # Inicializar vLLM engine
            success = await self.base_batcher.initialize()
            if not success:
                logger.error("❌ Error inicializando vLLM engine")
                return False

            self.llm = self.base_batcher.llm

            # Inicializar monitoreo de recursos
            self.resource_monitor_task = asyncio.create_task(self._monitor_resources())

            # Preparar estado de memoria para la ronda
            self._prepare_round_memory_state()

            # Cargar cache KV compartido si existe
            await self._load_shared_kv_cache()

            self.optimization_metrics["round_transitions"] += 1
            logger.info("✅ Optimizador inicializado para ronda FL")
            return True

        except Exception as e:
            logger.error(f"❌ Error inicializando optimizador: {e}")
            return False

    def _adapt_config_for_node(self, node_capabilities: Dict[str, Any]) -> BatchingConfig:
        """Adaptar configuración basado en capacidades del nodo."""
        base_config = self.config.base_config

        # Calcular capacidades efectivas
        gpu_memory_gb = node_capabilities.get("gpu_memory_gb", 8.0)
        cpu_cores = node_capabilities.get("cpu_cores", 4)
        network_bandwidth = node_capabilities.get("network_bandwidth_mbps", 100)

        # Adaptar tamaño de batch basado en memoria disponible
        available_memory_ratio = min(gpu_memory_gb / 8.0, 1.0)  # Normalizar a 8GB baseline
        adapted_batch_size = int(self.config.min_batch_size_fl +
                                (self.config.max_batch_size_fl - self.config.min_batch_size_fl) *
                                available_memory_ratio)

        # Adaptar configuración de memoria
        adapted_memory_utilization = min(self.config.base_config.gpu_memory_utilization *
                                       available_memory_ratio, 0.95)

        # Crear configuración adaptada
        adapted_config = BatchingConfig(
            model_path=base_config.model_path,
            tensor_parallel_size=min(base_config.tensor_parallel_size, cpu_cores // 2),
            gpu_memory_utilization=adapted_memory_utilization,
            max_model_len=base_config.max_model_len,
            max_num_seqs=min(base_config.max_num_seqs, adapted_batch_size * 2),
            max_num_batched_tokens=base_config.max_num_batched_tokens,
            dynamic_batching=base_config.dynamic_batching,
            max_batch_size=adapted_batch_size,
            batch_timeout_ms=self.config.batch_timeout_fl_ms,
            max_waiting_requests=min(base_config.max_waiting_requests, adapted_batch_size * 4),
            temperature=base_config.temperature,
            top_p=base_config.top_p,
            top_k=base_config.top_k,
            max_tokens=base_config.max_tokens,
            quantization=base_config.quantization
        )

        logger.info(f"🔧 Configuración adaptada - Batch size: {adapted_batch_size}, Memory: {adapted_memory_utilization:.2f}")
        return adapted_config

    async def _cleanup_previous_round(self):
        """Limpiar estado de ronda anterior."""
        if self.resource_monitor_task:
            self.resource_monitor_task.cancel()
            try:
                await self.resource_monitor_task
            except asyncio.CancelledError:
                pass

        # Guardar estado de cache KV para reutilización
        await self._save_shared_kv_cache()

        # Liberar memoria
        if self.llm:
            # Forzar garbage collection
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        logger.debug("🧹 Estado de ronda anterior limpiado")

    def _prepare_round_memory_state(self):
        """Preparar estado de memoria para la ronda actual."""
        if not self.current_round_id:
            return

        # Calcular límites de memoria para esta ronda
        total_memory = self.config.max_memory_per_round_gb * (1024**3)  # Bytes
        reserved_memory = total_memory * (1 - self.config.memory_reservation_ratio)
        available_memory = total_memory - reserved_memory

        self.round_memory_state = {
            "round_id": self.current_round_id,
            "total_memory_bytes": total_memory,
            "reserved_memory_bytes": reserved_memory,
            "available_memory_bytes": available_memory,
            "kv_cache_limit_bytes": available_memory * self.config.kv_cache_sharing_ratio,
            "inference_limit_bytes": available_memory * (1 - self.config.kv_cache_sharing_ratio),
            "start_time": time.time()
        }

        logger.debug(f"📊 Estado de memoria preparado para ronda {self.current_round_id}")

    async def _monitor_resources(self):
        """Monitoreo continuo de recursos del sistema."""
        while True:
            try:
                # Medir uso de GPU
                if torch.cuda.is_available():
                    gpu_memory_used = torch.cuda.memory_allocated() / torch.cuda.max_memory_allocated()
                    gpu_utilization = torch.cuda.utilization() / 100.0
                else:
                    gpu_memory_used = 0.0
                    gpu_utilization = 0.0

                # Medir uso de CPU y memoria
                cpu_memory = psutil.virtual_memory()
                cpu_memory_used = cpu_memory.percent / 100.0

                self.resource_stats.update({
                    "gpu_memory_used": gpu_memory_used,
                    "cpu_memory_used": cpu_memory_used,
                    "gpu_utilization": gpu_utilization,
                    "last_check": time.time()
                })

                # Verificar presión de memoria
                if gpu_memory_used > self.config.memory_pressure_threshold:
                    await self._handle_memory_pressure()

                await asyncio.sleep(self.config.resource_monitoring_interval)

            except Exception as e:
                logger.warning(f"⚠️ Error en monitoreo de recursos: {e}")
                await asyncio.sleep(5)

    async def _handle_memory_pressure(self):
        """Manejar presión de memoria alta."""
        logger.warning("⚠️ Presión de memoria alta detectada")

        # Reducir tamaño de batch dinámicamente
        if self.base_batcher:
            old_batch_size = self.base_batcher.config.max_batch_size
            new_batch_size = max(1, old_batch_size // 2)

            # Adaptar configuración del batcher
            self.base_batcher.config.max_batch_size = new_batch_size
            self.base_batcher.config.max_waiting_requests = new_batch_size * 4

            logger.info(f"🔧 Batch size reducido: {old_batch_size} -> {new_batch_size}")
            self.optimization_metrics["resource_adaptation_count"] += 1

        # Forzar liberación de memoria
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    async def _load_shared_kv_cache(self):
        """Cargar cache KV compartido de rondas anteriores."""
        if not self.config.memory_sharing_across_rounds or not self.shared_kv_cache:
            return

        try:
            # En implementación real, esto cargaría desde disco/red
            # Por ahora, simular carga
            cache_size = len(self.shared_kv_cache)
            logger.info(f"📥 Cache KV compartido cargado: {cache_size} entradas")

        except Exception as e:
            logger.warning(f"⚠️ Error cargando cache KV compartido: {e}")

    async def _save_shared_kv_cache(self):
        """Guardar cache KV para compartir entre rondas."""
        if not self.config.memory_sharing_across_rounds:
            return

        try:
            # En implementación real, esto guardaría a disco/red
            # Por ahora, mantener en memoria
            logger.debug("💾 Cache KV guardado para reutilización")

        except Exception as e:
            logger.warning(f"⚠️ Error guardando cache KV: {e}")

    async def submit_federated_request(
        self,
        request: BatchRequest,
        round_context: Dict[str, Any]
    ) -> str:
        """
        Enviar request optimizado para FL.

        Args:
            request: Request de batch
            round_context: Contexto de la ronda FL

        Returns:
            ID del request
        """
        if not self.base_batcher:
            raise RuntimeError("Optimizador no inicializado")

        # Adaptar request basado en contexto de ronda
        adapted_request = self._adapt_request_for_round(request, round_context)

        # Enviar al batcher base
        return await self.base_batcher.submit_request(adapted_request)

    def _adapt_request_for_round(
        self,
        request: BatchRequest,
        round_context: Dict[str, Any]
    ) -> BatchRequest:
        """Adaptar request basado en contexto de ronda FL."""
        # Ajustar prioridad basado en importancia para FL
        fl_priority = round_context.get("priority_boost", 0)
        adapted_priority = min(request.priority + fl_priority, 2)

        # Ajustar límites de tokens basado en capacidades del nodo
        max_tokens = request.max_tokens
        if max_tokens and self.round_memory_state:
            # Limitar basado en memoria disponible
            memory_based_limit = int(self.round_memory_state["inference_limit_bytes"] / (1024**2))  # MB aproximado
            max_tokens = min(max_tokens, memory_based_limit // 4)  # Estimación conservadora

        return BatchRequest(
            id=request.id,
            prompt=request.prompt,
            max_tokens=max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k,
            stream=request.stream,
            priority=adapted_priority
        )

    async def get_federated_metrics(self) -> Dict[str, Any]:
        """Obtener métricas específicas de optimización FL."""
        if not self.base_batcher:
            return {}

        base_metrics = self.base_batcher.get_metrics()

        # Calcular eficiencia de memoria
        if self.round_memory_state:
            used_memory = self.round_memory_state.get("available_memory_bytes", 0) * self.resource_stats["gpu_memory_used"]
            total_memory = self.round_memory_state.get("available_memory_bytes", 0)
            memory_efficiency = used_memory / total_memory if total_memory > 0 else 0
            self.optimization_metrics["memory_efficiency"] = memory_efficiency

        # Calcular utilización de batch
        batch_utilization = base_metrics.get("avg_batch_size", 0) / self.config.max_batch_size_fl
        self.optimization_metrics["batch_utilization"] = batch_utilization

        return {
            **base_metrics,
            **self.optimization_metrics,
            "resource_stats": self.resource_stats.copy(),
            "round_memory_state": self.round_memory_state.copy(),
            "current_round": self.current_round_id
        }

    async def optimize_for_next_round(self, next_round_requirements: Dict[str, Any]):
        """
        Optimizar configuración para la siguiente ronda.

        Args:
            next_round_requirements: Requisitos de la siguiente ronda
        """
        logger.info("🔄 Optimizando para siguiente ronda...")

        # Analizar rendimiento actual
        current_metrics = await self.get_federated_metrics()

        # Adaptar configuración basado en métricas
        if current_metrics.get("memory_efficiency", 0) > 0.9:
            # Memoria eficiente, podemos aumentar batch size
            self.config.max_batch_size_fl = min(self.config.max_batch_size_fl + 2, 32)
            logger.info(f"📈 Batch size aumentado a: {self.config.max_batch_size_fl}")

        elif current_metrics.get("memory_efficiency", 0) < 0.7:
            # Problemas de memoria, reducir batch size
            self.config.max_batch_size_fl = max(self.config.max_batch_size_fl - 1, 1)
            logger.info(f"📉 Batch size reducido a: {self.config.max_batch_size_fl}")

        # Adaptar timeout basado en carga
        queue_length = current_metrics.get("queue_length", 0)
        if queue_length > 10:
            self.config.batch_timeout_fl_ms = max(self.config.batch_timeout_fl_ms - 10, 10)
        elif queue_length < 2:
            self.config.batch_timeout_fl_ms = min(self.config.batch_timeout_fl_ms + 5, 200)

        logger.info("✅ Optimización para siguiente ronda completada")

    async def shutdown(self):
        """Apagar optimizador."""
        logger.info("🛑 Apagando FederatedVLLOptimizer...")

        if self.resource_monitor_task:
            self.resource_monitor_task.cancel()
            try:
                await self.resource_monitor_task
            except asyncio.CancelledError:
                pass

        if self.base_batcher:
            await self.base_batcher.stop_processing()

        # Guardar estado final
        await self._save_shared_kv_cache()

        # Limpiar recursos
        self.executor.shutdown(wait=True)
        gc.collect()

        logger.info("✅ FederatedVLLOptimizer apagado")


# Funciones de conveniencia
def create_federated_vllm_optimizer(
    model_path: str,
    max_memory_per_round_gb: float = 4.0,
    heterogeneous_support: bool = True
) -> FederatedVLLOptimizer:
    """
    Crear optimizador federado con configuración optimizada.

    Args:
        model_path: Ruta del modelo
        max_memory_per_round_gb: Memoria máxima por ronda
        heterogeneous_support: Soporte para hardware heterogéneo

    Returns:
        Optimizador configurado
    """
    base_config = BatchingConfig(
        model_path=model_path,
        tensor_parallel_size=1,
        gpu_memory_utilization=0.8,
        max_model_len=4096,
        max_num_seqs=128,
        max_num_batched_tokens=2048,
        dynamic_batching=True,
        max_batch_size=8,
        batch_timeout_ms=50
    )

    fed_config = FederatedVLLMConfig(
        base_config=base_config,
        max_memory_per_round_gb=max_memory_per_round_gb,
        heterogeneous_hardware_support=heterogeneous_support
    )

    return FederatedVLLOptimizer(fed_config)


if __name__ == "__main__":
    # Demo del optimizador federado
    print("🚀 FederatedVLLOptimizer Demo")
    print("Para uso completo, inicializar con modelo y capacidades de nodo")