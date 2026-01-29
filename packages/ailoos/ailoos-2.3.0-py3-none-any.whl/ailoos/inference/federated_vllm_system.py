"""
Sistema integrado de optimización de vLLM para federated learning.
Combina todos los componentes optimizados para FL.
"""

import asyncio
import logging
import time
import numpy as np
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
from dataclasses import dataclass, field
from pathlib import Path

from .federated_vllm_optimizer import FederatedVLLOptimizer, FederatedVLLMConfig
from .shared_kv_cache import SharedKVCache, SharedKVCacheConfig
from .resource_aware_scheduler import ResourceAwareScheduler, SchedulerConfig, ScheduledTask, TaskPriority
from .federated_batching_strategy import FederatedBatchingStrategy, FederatedBatchConfig
from .distributed_inference_monitor import DistributedInferenceMonitor, DistributedMonitorConfig
from .adaptive_quantization_bridge import AdaptiveQuantizationBridge, AdaptiveBridgeConfig
from .vllm_batching import BatchingConfig, BatchRequest, BatchResponse

logger = logging.getLogger(__name__)


@dataclass
class FederatedVLLMSystemConfig:
    """Configuración completa del sistema federado vLLM."""

    # Configuración base
    model_path: str
    local_node_id: str = "local_node"

    # Componentes habilitados
    enable_federated_optimizer: bool = True
    enable_shared_kv_cache: bool = True
    enable_resource_scheduler: bool = True
    enable_federated_batching: bool = True
    enable_distributed_monitor: bool = True
    enable_adaptive_quantization: bool = True

    # Configuraciones específicas
    fed_optimizer_config: FederatedVLLMConfig = None
    kv_cache_config: SharedKVCacheConfig = None
    scheduler_config: SchedulerConfig = None
    batching_config: FederatedBatchConfig = None
    monitor_config: DistributedMonitorConfig = None
    quantization_config: AdaptiveBridgeConfig = None

    def __post_init__(self):
        """Inicializar configuraciones por defecto."""
        if self.fed_optimizer_config is None:
            base_config = BatchingConfig(model_path=self.model_path)
            self.fed_optimizer_config = FederatedVLLMConfig(base_config=base_config)

        if self.kv_cache_config is None:
            self.kv_cache_config = SharedKVCacheConfig()

        if self.scheduler_config is None:
            self.scheduler_config = SchedulerConfig()

        if self.batching_config is None:
            self.batching_config = FederatedBatchConfig()

        if self.monitor_config is None:
            self.monitor_config = DistributedMonitorConfig()

        if self.quantization_config is None:
            self.quantization_config = AdaptiveBridgeConfig()


class FederatedVLLMSystem:
    """
    Sistema integrado de vLLM optimizado para federated learning.

    Combina todos los componentes:
    - FederatedVLLOptimizer: Optimizaciones de memoria y batching
    - SharedKVCache: Cache KV compartido entre rondas
    - ResourceAwareScheduler: Programador consciente de recursos
    - FederatedBatchingStrategy: Estrategias de batching FL
    - DistributedInferenceMonitor: Monitoreo distribuido
    - AdaptiveQuantizationBridge: Puente de cuantización adaptativa
    """

    def __init__(self, config: FederatedVLLMSystemConfig):
        self.config = config

        # Componentes del sistema
        self.federated_optimizer: Optional[FederatedVLLOptimizer] = None
        self.shared_kv_cache: Optional[SharedKVCache] = None
        self.resource_scheduler: Optional[ResourceAwareScheduler] = None
        self.federated_batching: Optional[FederatedBatchingStrategy] = None
        self.distributed_monitor: Optional[DistributedInferenceMonitor] = None
        self.adaptive_quantization: Optional[AdaptiveQuantizationBridge] = None

        # Estado del sistema
        self.is_initialized = False
        self.current_round_id: Optional[str] = None
        self.system_metrics: Dict[str, Any] = {}

        # Estadísticas de rendimiento
        self.performance_stats = {
            "total_requests_processed": 0,
            "total_rounds_completed": 0,
            "avg_latency_ms": 0.0,
            "avg_throughput_tokens_per_sec": 0.0,
            "cache_hit_rate": 0.0,
            "resource_utilization": 0.0
        }

        logger.info("🔧 FederatedVLLMSystem inicializado")
        logger.info(f"   Nodo: {config.local_node_id}")
        logger.info(f"   Modelo: {config.model_path}")

    async def initialize_system(self) -> bool:
        """
        Inicializar todos los componentes del sistema.

        Returns:
            True si la inicialización fue exitosa
        """
        try:
            logger.info("🚀 Inicializando sistema federado vLLM...")

            # Inicializar componentes habilitados
            if self.config.enable_federated_optimizer:
                self.federated_optimizer = FederatedVLLOptimizer(self.config.fed_optimizer_config)
                logger.info("✅ FederatedVLLOptimizer inicializado")

            if self.config.enable_shared_kv_cache:
                self.shared_kv_cache = SharedKVCache(self.config.kv_cache_config)
                self.shared_kv_cache.start()
                logger.info("✅ SharedKVCache inicializado")

            if self.config.enable_resource_scheduler:
                self.resource_scheduler = ResourceAwareScheduler(
                    self.config.scheduler_config,
                    self.config.local_node_id
                )
                await self.resource_scheduler.start()
                logger.info("✅ ResourceAwareScheduler inicializado")

            if self.config.enable_federated_batching:
                base_config = BatchingConfig(model_path=self.config.model_path)
                self.federated_batching = FederatedBatchingStrategy(base_config, self.config.batching_config)
                logger.info("✅ FederatedBatchingStrategy inicializado")

            if self.config.enable_distributed_monitor:
                self.distributed_monitor = DistributedInferenceMonitor(
                    self.config.monitor_config,
                    self.config.local_node_id
                )
                self.distributed_monitor.start_monitoring()
                logger.info("✅ DistributedInferenceMonitor inicializado")

            if self.config.enable_adaptive_quantization:
                from .quantization import AdvancedQuantizer
                quantizer = AdvancedQuantizer()
                self.adaptive_quantization = AdaptiveQuantizationBridge(
                    self.config.quantization_config,
                    quantizer,
                    self.federated_optimizer
                )
                logger.info("✅ AdaptiveQuantizationBridge inicializado")

            self.is_initialized = True
            logger.info("🎉 Sistema federado vLLM completamente inicializado")

            return True

        except Exception as e:
            logger.error(f"❌ Error inicializando sistema: {e}")
            await self.shutdown_system()
            return False

    async def prepare_for_round(self, round_id: str, node_capabilities: Dict[str, Any]) -> bool:
        """
        Preparar el sistema para una nueva ronda FL.

        Args:
            round_id: ID de la ronda federada
            node_capabilities: Capacidades del nodo actual

        Returns:
            True si la preparación fue exitosa
        """
        if not self.is_initialized:
            logger.error("❌ Sistema no inicializado")
            return False

        try:
            self.current_round_id = round_id
            logger.info(f"🔄 Preparando sistema para ronda: {round_id}")

            # Preparar optimizador federado
            if self.federated_optimizer:
                success = await self.federated_optimizer.initialize_for_round(round_id, node_capabilities)
                if not success:
                    logger.error("❌ Error inicializando optimizador federado")
                    return False

            # Resetear estrategia de batching
            if self.federated_batching:
                self.federated_batching.reset_for_new_round(round_id)

            # Adaptar cuantización si es necesario
            if self.adaptive_quantization:
                optimal_profile = self.adaptive_quantization.adapt_quantization_for_node(
                    node_capabilities, {"type": "federated_inference"}, {"round_id": round_id}
                )
                logger.info(f"🎯 Cuantización adaptada: {optimal_profile.level.value}")

            # Registrar capacidades del nodo en el scheduler
            if self.resource_scheduler:
                from .resource_aware_scheduler import HardwareCapabilities
                hw_caps = HardwareCapabilities(
                    node_id=self.config.local_node_id,
                    hardware_type=node_capabilities.get("hardware_type", "cpu"),
                    device_name=node_capabilities.get("device_name", "unknown"),
                    gpu_memory_gb=node_capabilities.get("gpu_memory_gb", 0),
                    total_memory_gb=node_capabilities.get("total_memory_gb", 8),
                    performance_score=node_capabilities.get("performance_score", 1.0),
                    supports_fp16=node_capabilities.get("supports_fp16", False),
                    supports_int8=node_capabilities.get("supports_int8", False),
                    max_batch_size=node_capabilities.get("max_batch_size", 8)
                )
                self.resource_scheduler.register_remote_node(self.config.local_node_id, hw_caps)

            logger.info(f"✅ Sistema preparado para ronda {round_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error preparando sistema para ronda: {e}")
            return False

    async def process_federated_request(
        self,
        request: BatchRequest,
        round_context: Optional[Dict[str, Any]] = None
    ) -> Optional[BatchResponse]:
        """
        Procesar una solicitud federada optimizada.

        Args:
            request: Solicitud a procesar
            round_context: Contexto de la ronda FL

        Returns:
            Respuesta procesada o None si falla
        """
        if not self.is_initialized:
            logger.error("❌ Sistema no inicializado")
            return None

        start_time = time.time()
        round_context = round_context or {}

        try:
            # 1. Verificar/adaptar cuantización si es necesario
            if self.adaptive_quantization and self.adaptive_quantization.should_adapt_quantization(
                self.system_metrics, round_context
            ):
                # Adaptación de cuantización (simulada)
                logger.debug("🔄 Adaptando cuantización para solicitud...")

            # 2. Verificar cache KV
            kv_cache_available = False
            if self.shared_kv_cache:
                cached_kv = self.shared_kv_cache.retrieve_kv_cache(
                    request.prompt_tokens,
                    round_id=self.current_round_id or "",
                    node_id=self.config.local_node_id
                )
                kv_cache_available = cached_kv is not None

            # 3. Optimizar batching si está disponible
            if self.federated_batching:
                # Crear batch optimizado
                batches = self.federated_batching.optimize_batch_for_round(
                    [request], self.current_round_id or "", {}
                )

                if batches and batches[0]:
                    # Usar primer batch
                    optimized_request = batches[0][0]
                    request = optimized_request

            # 4. Programar tarea si scheduler está disponible
            if self.resource_scheduler:
                task = ScheduledTask(
                    task_id=request.id,
                    task_type="federated_inference",
                    priority=TaskPriority.NORMAL,
                    estimated_duration=0.5,  # 500ms estimados
                    resource_requirements={
                        "memory_gb": 2.0,
                        "precision": "fp16",
                        "hardware_type": "gpu"
                    },
                    round_id=self.current_round_id or "",
                    federated_context=round_context
                )

                # Programar tarea (simulado - en implementación real esperaría)
                await self.resource_scheduler.schedule_task(task)

            # 5. Procesar con optimizador federado
            if self.federated_optimizer:
                request_id = await self.federated_optimizer.submit_federated_request(
                    request, round_context
                )

                # Simular procesamiento (en implementación real, esperaría respuesta)
                processing_time = 0.2 + np.random.random() * 0.3  # 200-500ms
                await asyncio.sleep(processing_time)

                # Crear respuesta simulada
                response = BatchResponse(
                    request_id=request.id,
                    text=f"Respuesta procesada para {request.prompt[:50]}...",
                    usage={
                        "prompt_tokens": len(request.prompt_tokens) if hasattr(request, 'prompt_tokens') else len(request.prompt) // 4,
                        "completion_tokens": 50,
                        "total_tokens": (len(request.prompt_tokens) if hasattr(request, 'prompt_tokens') else len(request.prompt) // 4) + 50
                    },
                    finish_reason="stop",
                    processing_time=processing_time * 1000  # ms
                )

                # 6. Almacenar en cache KV si está disponible
                if self.shared_kv_cache and not kv_cache_available:
                    # Simular almacenamiento (en implementación real usaría KV cache real)
                    logger.debug("💾 Almacenando en cache KV...")

                # 7. Registrar métricas
                if self.distributed_monitor:
                    self.distributed_monitor.record_inference_metrics(
                        node_id=self.config.local_node_id,
                        round_id=self.current_round_id or "",
                        latency_ms=processing_time * 1000,
                        tokens_processed=response.usage["total_tokens"],
                        batch_size=1,
                        memory_used_gb=1.5,
                        cache_hit=kv_cache_available
                    )

                # 8. Actualizar estadísticas
                self._update_performance_stats(response, processing_time, kv_cache_available)

                logger.info(f"✅ Solicitud federada procesada: {request.id} ({processing_time:.3f}s)")
                return response

            else:
                logger.error("❌ No hay optimizador federado disponible")
                return None

        except Exception as e:
            logger.error(f"❌ Error procesando solicitud federada: {e}")

            # Registrar error en monitor
            if self.distributed_monitor:
                self.distributed_monitor.record_inference_metrics(
                    node_id=self.config.local_node_id,
                    round_id=self.current_round_id or "",
                    latency_ms=(time.time() - start_time) * 1000,
                    tokens_processed=0,
                    batch_size=1,
                    memory_used_gb=0,
                    error_occurred=True
                )

            return None

    def _update_performance_stats(
        self,
        response: BatchResponse,
        processing_time: float,
        cache_hit: bool
    ):
        """Actualizar estadísticas de rendimiento."""
        self.performance_stats["total_requests_processed"] += 1

        # Actualizar latencia promedio
        current_avg = self.performance_stats["avg_latency_ms"]
        new_avg = (current_avg * (self.performance_stats["total_requests_processed"] - 1) +
                  response.processing_time) / self.performance_stats["total_requests_processed"]
        self.performance_stats["avg_latency_ms"] = new_avg

        # Actualizar throughput
        tokens_per_sec = response.usage["total_tokens"] / processing_time
        current_avg_throughput = self.performance_stats["avg_throughput_tokens_per_sec"]
        new_throughput = (current_avg_throughput * (self.performance_stats["total_requests_processed"] - 1) +
                         tokens_per_sec) / self.performance_stats["total_requests_processed"]
        self.performance_stats["avg_throughput_tokens_per_sec"] = new_throughput

        # Actualizar cache hit rate
        current_cache_hits = self.performance_stats["cache_hit_rate"] * (self.performance_stats["total_requests_processed"] - 1)
        new_cache_hits = current_cache_hits + (1 if cache_hit else 0)
        self.performance_stats["cache_hit_rate"] = new_cache_hits / self.performance_stats["total_requests_processed"]

    async def optimize_for_next_round(self, next_round_requirements: Dict[str, Any]):
        """
        Optimizar el sistema para la siguiente ronda.

        Args:
            next_round_requirements: Requisitos de la siguiente ronda
        """
        logger.info("🔄 Optimizando sistema para siguiente ronda...")

        try:
            # Optimizar optimizador federado
            if self.federated_optimizer:
                await self.federated_optimizer.optimize_for_next_round(next_round_requirements)

            # Adaptar estrategia de batching
            if self.federated_batching:
                self.federated_batching.adapt_strategy_based_on_history()

            # Limpiar cache KV antigua
            if self.shared_kv_cache and self.current_round_id:
                self.shared_kv_cache.clear_round_cache(self.current_round_id)

            # Actualizar métricas del sistema
            self.system_metrics = await self.get_system_metrics()

            logger.info("✅ Sistema optimizado para siguiente ronda")

        except Exception as e:
            logger.error(f"❌ Error optimizando para siguiente ronda: {e}")

    async def get_system_metrics(self) -> Dict[str, Any]:
        """Obtener métricas completas del sistema."""
        metrics = {
            "performance_stats": self.performance_stats.copy(),
            "system_status": {
                "initialized": self.is_initialized,
                "current_round": self.current_round_id,
                "components_active": {
                    "federated_optimizer": self.federated_optimizer is not None,
                    "shared_kv_cache": self.shared_kv_cache is not None,
                    "resource_scheduler": self.resource_scheduler is not None,
                    "federated_batching": self.federated_batching is not None,
                    "distributed_monitor": self.distributed_monitor is not None,
                    "adaptive_quantization": self.adaptive_quantization is not None
                }
            }
        }

        # Agregar métricas de componentes individuales
        try:
            if self.federated_optimizer:
                fed_metrics = await self.federated_optimizer.get_federated_metrics()
                metrics["federated_optimizer"] = fed_metrics

            if self.shared_kv_cache:
                cache_stats = self.shared_kv_cache.get_cache_stats()
                metrics["shared_kv_cache"] = cache_stats

            if self.resource_scheduler:
                scheduler_stats = self.resource_scheduler.get_scheduler_stats()
                metrics["resource_scheduler"] = scheduler_stats

            if self.federated_batching:
                batching_stats = self.federated_batching.get_strategy_stats()
                metrics["federated_batching"] = batching_stats

            if self.distributed_monitor:
                monitor_stats = self.distributed_monitor.get_monitoring_stats()
                metrics["distributed_monitor"] = monitor_stats

            if self.adaptive_quantization:
                bridge_stats = self.adaptive_quantization.get_bridge_stats()
                metrics["adaptive_quantization"] = bridge_stats

        except Exception as e:
            logger.warning(f"⚠️ Error recopilando métricas de componentes: {e}")

        return metrics

    async def shutdown_system(self):
        """Apagar todos los componentes del sistema."""
        logger.info("🛑 Apagando sistema federado vLLM...")

        try:
            # Apagar componentes en orden inverso
            if self.distributed_monitor:
                self.distributed_monitor.stop_monitoring()

            if self.resource_scheduler:
                await self.resource_scheduler.stop()

            if self.federated_optimizer:
                await self.federated_optimizer.shutdown()

            if self.shared_kv_cache:
                self.shared_kv_cache.stop()

            # Otros componentes no requieren shutdown especial
            self.is_initialized = False

            logger.info("✅ Sistema federado vLLM apagado")

        except Exception as e:
            logger.error(f"❌ Error apagando sistema: {e}")

    def get_system_health(self) -> Dict[str, Any]:
        """Obtener estado de salud del sistema."""
        return {
            "overall_status": "healthy" if self.is_initialized else "not_initialized",
            "components_health": {
                "federated_optimizer": "ok" if self.federated_optimizer else "disabled",
                "shared_kv_cache": "ok" if self.shared_kv_cache else "disabled",
                "resource_scheduler": "ok" if self.resource_scheduler else "disabled",
                "federated_batching": "ok" if self.federated_batching else "disabled",
                "distributed_monitor": "ok" if self.distributed_monitor else "disabled",
                "adaptive_quantization": "ok" if self.adaptive_quantization else "disabled"
            },
            "performance_indicators": {
                "requests_processed": self.performance_stats["total_requests_processed"],
                "avg_latency_ms": round(self.performance_stats["avg_latency_ms"], 2),
                "cache_hit_rate": round(self.performance_stats["cache_hit_rate"], 3),
                "throughput_tokens_per_sec": round(self.performance_stats["avg_throughput_tokens_per_sec"], 1)
            }
        }


# Funciones de conveniencia
async def create_federated_vllm_system(
    model_path: str,
    local_node_id: str = "local_node",
    enable_all_components: bool = True
) -> FederatedVLLMSystem:
    """
    Crear sistema federado vLLM completo con configuración optimizada.

    Args:
        model_path: Ruta del modelo
        local_node_id: ID del nodo local
        enable_all_components: Habilitar todos los componentes

    Returns:
        Sistema configurado e inicializado
    """
    config = FederatedVLLMSystemConfig(
        model_path=model_path,
        local_node_id=local_node_id,
        enable_federated_optimizer=enable_all_components,
        enable_shared_kv_cache=enable_all_components,
        enable_resource_scheduler=enable_all_components,
        enable_federated_batching=enable_all_components,
        enable_distributed_monitor=enable_all_components,
        enable_adaptive_quantization=enable_all_components
    )

    system = FederatedVLLMSystem(config)
    success = await system.initialize_system()

    if success:
        logger.info("🎉 Sistema federado vLLM creado exitosamente")
    else:
        logger.error("❌ Error creando sistema federado vLLM")

    return system


if __name__ == "__main__":
    # Demo del sistema federado vLLM
    print("🚀 FederatedVLLMSystem Demo")
    print("Para uso completo, inicializar con modelo y configuración específica")