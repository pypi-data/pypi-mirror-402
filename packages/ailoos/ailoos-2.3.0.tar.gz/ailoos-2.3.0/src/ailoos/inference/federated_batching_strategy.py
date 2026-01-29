"""
Estrategias de batching optimizadas para federated learning.
Adapta el batching dinámico a las características de entornos FL.
"""

import asyncio
import torch
import logging
import time
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Deque
from dataclasses import dataclass, field
from collections import deque
from concurrent.futures import ThreadPoolExecutor

from .vllm_batching import BatchingConfig, BatchRequest, BatchResponse
from .federated_vllm_optimizer import FederatedVLLMConfig

logger = logging.getLogger(__name__)


@dataclass
class FederatedBatchConfig:
    """Configuración específica para batching federado."""

    # Estrategias de batching
    adaptive_batching: bool = True
    cross_round_optimization: bool = True
    bandwidth_aware_batching: bool = True

    # Límites adaptativos
    min_batch_size_fl: int = 1
    max_batch_size_fl: int = 32
    batch_timeout_fl_ms: int = 100

    # Optimizaciones FL
    prioritize_round_critical: bool = True  # Priorizar tareas críticas para rondas
    balance_node_load: bool = True  # Balancear carga entre nodos
    predict_batch_efficiency: bool = True  # Predecir eficiencia de batch

    # Métricas de red
    network_latency_ms: float = 50.0
    bandwidth_mbps: float = 100.0

    # Historial
    history_window_size: int = 100
    learning_rate_adaptation: float = 0.1


@dataclass
class BatchEfficiencyMetrics:
    """Métricas de eficiencia de batching."""

    batch_size: int
    processing_time: float
    tokens_processed: int
    memory_used_gb: float
    throughput_tokens_per_sec: float
    round_id: str = ""
    node_id: str = ""
    timestamp: float = field(default_factory=time.time)

    @property
    def efficiency_score(self) -> float:
        """Calcular score de eficiencia."""
        if self.processing_time <= 0:
            return 0.0
        # Eficiencia = throughput / (batch_size * memory_used)
        return self.throughput_tokens_per_sec / (self.batch_size * max(0.1, self.memory_used_gb))


class FederatedBatchingStrategy:
    """
    Estrategia de batching optimizada para federated learning.

    Características principales:
    - Batching adaptativo basado en capacidades de nodo
    - Optimización cross-round para reutilización de contexto
    - Balanceo de carga entre nodos heterogéneos
    - Predicción de eficiencia de batch
    - Adaptación automática basada en métricas de red
    """

    def __init__(self, base_config: BatchingConfig, fed_config: FederatedBatchConfig):
        self.base_config = base_config
        self.fed_config = fed_config

        # Estado de batching
        self.current_round_id: Optional[str] = None
        self.active_batches: Dict[str, List[BatchRequest]] = {}
        self.pending_requests: Deque[BatchRequest] = deque()

        # Historial de eficiencia
        self.efficiency_history: Deque[BatchEfficiencyMetrics] = deque(maxlen=fed_config.history_window_size)
        self.node_performance: Dict[str, Deque[float]] = {}

        # Adaptación dinámica
        self.optimal_batch_sizes: Dict[str, int] = {}  # node_id -> optimal_batch_size
        self.adaptation_counters: Dict[str, int] = {}

        # Estadísticas
        self.stats = {
            "total_batches_processed": 0,
            "total_requests_processed": 0,
            "avg_batch_efficiency": 0.0,
            "avg_adaptation_rate": 0.0,
            "cross_round_reuse_rate": 0.0,
            "network_optimization_savings": 0.0
        }

        # Executor para operaciones pesadas
        self.executor = ThreadPoolExecutor(max_workers=2)

        logger.info("🔧 FederatedBatchingStrategy inicializado")
        logger.info(f"   Batch size range: {fed_config.min_batch_size_fl}-{fed_config.max_batch_size_fl}")
        logger.info(f"   Adaptive batching: {fed_config.adaptive_batching}")

    def optimize_batch_for_round(
        self,
        requests: List[BatchRequest],
        round_id: str,
        node_capabilities: Dict[str, Any]
    ) -> List[List[BatchRequest]]:
        """
        Optimizar batching para una ronda FL específica.

        Args:
            requests: Lista de requests a procesar
            round_id: ID de la ronda FL
            node_capabilities: Capacidades del nodo actual

        Returns:
            Lista de batches optimizados
        """
        self.current_round_id = round_id

        # Filtrar y priorizar requests
        filtered_requests = self._filter_and_prioritize_requests(requests, round_id)

        # Calcular tamaño óptimo de batch para este nodo
        optimal_batch_size = self._calculate_optimal_batch_size(node_capabilities, round_id)

        # Crear batches usando estrategia federada
        batches = self._create_federated_batches(filtered_requests, optimal_batch_size, node_capabilities)

        logger.info(f"📦 Optimizados {len(requests)} requests en {len(batches)} batches para ronda {round_id}")
        return batches

    def _filter_and_prioritize_requests(
        self,
        requests: List[BatchRequest],
        round_id: str
    ) -> List[BatchRequest]:
        """Filtrar y priorizar requests para FL."""
        # Priorizar requests de la ronda actual
        round_requests = []
        other_requests = []

        for req in requests:
            if req.priority == req.priority.CRITICAL or (hasattr(req, 'round_id') and req.round_id == round_id):
                round_requests.append(req)
            else:
                other_requests.append(req)

        # Combinar con prioridad
        prioritized = round_requests + other_requests

        # Limitar por capacidades
        max_requests = self.fed_config.max_batch_size_fl * 4  # Máximo 4 batches
        return prioritized[:max_requests]

    def _calculate_optimal_batch_size(
        self,
        node_capabilities: Dict[str, Any],
        round_id: str
    ) -> int:
        """Calcular tamaño óptimo de batch basado en capacidades y historial."""
        node_id = node_capabilities.get("node_id", "unknown")

        # Base del historial
        if node_id in self.optimal_batch_sizes:
            base_size = self.optimal_batch_sizes[node_id]
        else:
            # Estimación inicial basada en memoria
            memory_gb = node_capabilities.get("gpu_memory_gb", 8.0)
            base_size = min(self.fed_config.max_batch_size_fl, max(self.fed_config.min_batch_size_fl, int(memory_gb)))

        # Ajustar por rendimiento histórico
        if node_id in self.node_performance and len(self.node_performance[node_id]) > 5:
            recent_performance = list(self.node_performance[node_id])[-5:]
            avg_performance = np.mean(recent_performance)

            # Ajustar batch size basado en rendimiento
            if avg_performance > 1.2:  # Bueno, aumentar
                base_size = min(self.fed_config.max_batch_size_fl, base_size + 1)
            elif avg_performance < 0.8:  # Malo, reducir
                base_size = max(self.fed_config.min_batch_size_fl, base_size - 1)

        # Ajustar por restricciones de red si está habilitado
        if self.fed_config.bandwidth_aware_batching:
            bandwidth_factor = min(1.0, self.fed_config.bandwidth_mbps / 50.0)  # Normalizar a 50Mbps baseline
            base_size = int(base_size * bandwidth_factor)

        # Ajustar por latencia de red
        if self.fed_config.network_latency_ms > 100:  # Alta latencia
            base_size = max(self.fed_config.min_batch_size_fl, base_size // 2)

        self.optimal_batch_sizes[node_id] = base_size
        return base_size

    def _create_federated_batches(
        self,
        requests: List[BatchRequest],
        optimal_batch_size: int,
        node_capabilities: Dict[str, Any]
    ) -> List[List[BatchRequest]]:
        """Crear batches optimizados para FL."""
        if not requests:
            return []

        batches = []
        current_batch = []
        current_tokens = 0
        max_tokens_per_batch = self.base_config.max_num_batched_tokens

        # Ordenar requests por prioridad y similitud
        sorted_requests = self._sort_requests_for_batching(requests)

        for request in sorted_requests:
            estimated_tokens = self._estimate_request_tokens(request)

            # Verificar si cabe en el batch actual
            if (len(current_batch) >= optimal_batch_size or
                current_tokens + estimated_tokens > max_tokens_per_batch) and current_batch:

                # Crear nuevo batch
                batches.append(current_batch)
                current_batch = []
                current_tokens = 0

            current_batch.append(request)
            current_tokens += estimated_tokens

        # Agregar último batch si tiene elementos
        if current_batch:
            batches.append(current_batch)

        # Optimizar batches finales
        if self.fed_config.adaptive_batching:
            batches = self._optimize_batch_distribution(batches, node_capabilities)

        return batches

    def _sort_requests_for_batching(self, requests: List[BatchRequest]) -> List[BatchRequest]:
        """Ordenar requests para optimizar batching."""
        def sort_key(req: BatchRequest) -> Tuple[int, int, int]:
            # Prioridad (menor número = mayor prioridad)
            priority_score = req.priority.value

            # Tamaño estimado (para balancear batches)
            size_score = self._estimate_request_tokens(req)

            # Afinidad FL (requests de la misma ronda primero)
            round_score = 0 if (hasattr(req, 'round_id') and req.round_id == self.current_round_id) else 1

            return (priority_score, round_score, size_score)

        return sorted(requests, key=sort_key)

    def _estimate_request_tokens(self, request: BatchRequest) -> int:
        """Estimar número de tokens en un request."""
        # Estimación simple: ~4 caracteres por token
        return len(request.prompt) // 4

    def _optimize_batch_distribution(
        self,
        batches: List[List[BatchRequest]],
        node_capabilities: Dict[str, Any]
    ) -> List[List[BatchRequest]]:
        """Optimizar distribución de batches."""
        if len(batches) <= 1:
            return batches

        # Calcular tamaños actuales
        batch_sizes = [len(batch) for batch in batches]
        avg_size = np.mean(batch_sizes)

        # Identificar batches que necesitan rebalanceo
        optimized_batches = []
        current_batch = []

        for batch in batches:
            current_batch.extend(batch)

            # Si el batch actual es demasiado grande, dividirlo
            if len(current_batch) > self.fed_config.max_batch_size_fl:
                # Dividir en chunks más pequeños
                chunk_size = self.fed_config.max_batch_size_fl
                for i in range(0, len(current_batch), chunk_size):
                    optimized_batches.append(current_batch[i:i + chunk_size])
                current_batch = []
            elif len(current_batch) >= avg_size * 0.8:  # Batch razonable
                optimized_batches.append(current_batch)
                current_batch = []

        # Agregar batch restante
        if current_batch:
            optimized_batches.append(current_batch)

        return optimized_batches

    def record_batch_metrics(
        self,
        batch: List[BatchRequest],
        processing_time: float,
        memory_used_gb: float,
        node_id: str,
        round_id: str = ""
    ):
        """
        Registrar métricas de un batch procesado.

        Args:
            batch: Batch procesado
            processing_time: Tiempo de procesamiento
            memory_used_gb: Memoria usada
            node_id: ID del nodo
            round_id: ID de la ronda
        """
        total_tokens = sum(self._estimate_request_tokens(req) for req in batch)
        batch_size = len(batch)

        if processing_time > 0:
            throughput = total_tokens / processing_time
        else:
            throughput = 0.0

        # Crear métricas
        metrics = BatchEfficiencyMetrics(
            batch_size=batch_size,
            processing_time=processing_time,
            tokens_processed=total_tokens,
            memory_used_gb=memory_used_gb,
            throughput_tokens_per_sec=throughput,
            round_id=round_id or self.current_round_id or "",
            node_id=node_id
        )

        # Registrar en historial
        self.efficiency_history.append(metrics)

        # Actualizar rendimiento por nodo
        if node_id not in self.node_performance:
            self.node_performance[node_id] = deque(maxlen=20)

        efficiency = metrics.efficiency_score
        self.node_performance[node_id].append(efficiency)

        # Actualizar estadísticas globales
        self.stats["total_batches_processed"] += 1
        self.stats["total_requests_processed"] += batch_size

        # Recalcular promedios
        if self.efficiency_history:
            efficiencies = [m.efficiency_score for m in self.efficiency_history]
            self.stats["avg_batch_efficiency"] = np.mean(efficiencies)

        logger.debug(f"📊 Batch metrics - Size: {batch_size}, Throughput: {throughput:.1f} t/s, Efficiency: {efficiency:.3f}")

    def adapt_strategy_based_on_history(self):
        """Adaptar estrategia basada en historial de rendimiento."""
        if len(self.efficiency_history) < 10:
            return  # Necesitamos datos suficientes

        # Analizar tendencias
        recent_metrics = list(self.efficiency_history)[-10:]
        efficiencies = [m.efficiency_score for m in recent_metrics]

        # Calcular tendencias
        efficiency_trend = np.polyfit(range(len(efficiencies)), efficiencies, 1)[0]

        # Adaptar configuración basado en tendencias
        if efficiency_trend > 0.01:  # Mejorando
            # Mantener o ligeramente aumentar batch sizes
            for node_id in self.optimal_batch_sizes:
                current = self.optimal_batch_sizes[node_id]
                self.optimal_batch_sizes[node_id] = min(self.fed_config.max_batch_size_fl, current + 1)

            logger.info("📈 Rendimiento mejorando, ajustando batch sizes hacia arriba")

        elif efficiency_trend < -0.01:  # Empeorando
            # Reducir batch sizes
            for node_id in self.optimal_batch_sizes:
                current = self.optimal_batch_sizes[node_id]
                self.optimal_batch_sizes[node_id] = max(self.fed_config.min_batch_size_fl, current - 1)

            logger.info("📉 Rendimiento empeorando, ajustando batch sizes hacia abajo")

        # Adaptar timeout basado en latencia de red
        avg_processing_time = np.mean([m.processing_time for m in recent_metrics])
        if avg_processing_time > 1.0:  # Procesamiento lento
            self.fed_config.batch_timeout_fl_ms = min(500, self.fed_config.batch_timeout_fl_ms + 10)
        elif avg_processing_time < 0.2:  # Procesamiento rápido
            self.fed_config.batch_timeout_fl_ms = max(10, self.fed_config.batch_timeout_fl_ms - 5)

    def predict_batch_efficiency(
        self,
        batch_size: int,
        node_capabilities: Dict[str, Any]
    ) -> float:
        """
        Predecir eficiencia de un batch.

        Args:
            batch_size: Tamaño del batch
            node_capabilities: Capacidades del nodo

        Returns:
            Score de eficiencia predicho
        """
        if not self.fed_config.predict_batch_efficiency or not self.efficiency_history:
            return 0.5  # Score neutral por defecto

        # Buscar batches similares en el historial
        similar_batches = [
            m for m in self.efficiency_history
            if abs(m.batch_size - batch_size) <= 2  # Tamaño similar
        ]

        if not similar_batches:
            return 0.5

        # Promedio de eficiencias similares
        return np.mean([m.efficiency_score for m in similar_batches])

    def get_strategy_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de la estrategia."""
        return {
            **self.stats,
            "optimal_batch_sizes": self.optimal_batch_sizes.copy(),
            "efficiency_history_size": len(self.efficiency_history),
            "node_performance_count": len(self.node_performance),
            "current_round": self.current_round_id,
            "pending_requests": len(self.pending_requests)
        }

    def reset_for_new_round(self, round_id: str):
        """Reiniciar estado para nueva ronda."""
        self.current_round_id = round_id
        self.active_batches.clear()

        # Adaptar estrategia basada en historial
        self.adapt_strategy_based_on_history()

        logger.info(f"🔄 Estrategia reiniciada para ronda {round_id}")


# Funciones de conveniencia
def create_federated_batching_strategy(
    max_batch_size: int = 16,
    adaptive_batching: bool = True,
    bandwidth_aware: bool = True
) -> FederatedBatchingStrategy:
    """
    Crear estrategia de batching federada optimizada.

    Args:
        max_batch_size: Tamaño máximo de batch
        adaptive_batching: Habilitar batching adaptativo
        bandwidth_aware: Considerar ancho de banda

    Returns:
        Estrategia configurada
    """
    base_config = BatchingConfig(max_batch_size=max_batch_size)
    fed_config = FederatedBatchConfig(
        adaptive_batching=adaptive_batching,
        bandwidth_aware_batching=bandwidth_aware,
        max_batch_size_fl=max_batch_size
    )

    return FederatedBatchingStrategy(base_config, fed_config)


if __name__ == "__main__":
    # Demo de la estrategia de batching federada
    print("🚀 FederatedBatchingStrategy Demo")
    print("Para uso completo, inicializar con configuración específica")