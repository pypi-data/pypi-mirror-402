#!/usr/bin/env python3
"""
Optimal Dataset Partitioner for Federated Learning
Automatically partitions datasets across federated nodes based on node capabilities,
geographic distribution, network conditions, and training efficiency requirements.
"""

import asyncio
import math
import time
from typing import Dict, List, Any, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum

from ..core.logging import get_logger

# Lazy import to avoid circular dependencies
if TYPE_CHECKING:
    from .data_coordinator import DatasetInfo

if TYPE_CHECKING:
    from ..discovery.node_discovery import DiscoveredNode

logger = get_logger(__name__)


class PartitionStrategy(Enum):
    """Estrategias de particionamiento disponibles."""
    CAPABILITY_WEIGHTED = "capability_weighted"
    GEOGRAPHIC_BALANCED = "geographic_balanced"
    NETWORK_OPTIMIZED = "network_optimized"
    EFFICIENCY_MAXIMIZED = "efficiency_maximized"
    HYBRID_OPTIMAL = "hybrid_optimal"


@dataclass
class PartitionResult:
    """Resultado del particionamiento de dataset."""
    node_assignments: Dict[str, List[str]] = field(default_factory=dict)  # node_id -> chunk_ids
    partition_stats: Dict[str, Any] = field(default_factory=dict)
    optimization_score: float = 0.0
    strategy_used: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class NodeScore:
    """Puntuación de un nodo para particionamiento."""
    node_id: str
    capability_score: float = 0.0
    geographic_score: float = 0.0
    network_score: float = 0.0
    efficiency_score: float = 0.0
    total_score: float = 0.0
    assigned_chunks: int = 0


class OptimalDatasetPartitioner:
    """
    Particionador óptimo de datasets para aprendizaje federado.
    Distribuye automáticamente los chunks de datos entre nodos considerando
    capacidades hardware, distribución geográfica, condiciones de red y eficiencia de entrenamiento.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializar el particionador.

        Args:
            config: Configuración opcional
        """
        self.config = config or {}

        # Pesos para diferentes factores de scoring
        self.capability_weights = {
            'cpu_cores': 0.3,
            'memory_gb': 0.3,
            'gpu_available': 0.2,
            'available_memory_percent': 0.1,
            'available_cpu_percent': 0.1
        }

        self.geographic_weights = {
            'region_balance': 0.6,
            'latency_penalty': 0.4
        }

        self.network_weights = {
            'bandwidth_estimate': 0.5,
            'connection_stability': 0.3,
            'load_factor': 0.2
        }

        self.efficiency_weights = {
            'reputation_score': 0.4,
            'current_load': 0.3,
            'session_count': 0.3
        }

        # Configuración por defecto
        self.max_chunks_per_node = self.config.get('max_chunks_per_node', 100)
        self.min_chunks_per_node = self.config.get('min_chunks_per_node', 1)
        self.geographic_regions = self.config.get('geographic_regions', ['EU', 'US', 'ASIA', 'OTHER'])

        logger.info("🚀 OptimalDatasetPartitioner initialized")

    async def partition_dataset(self,
                              dataset: 'DatasetInfo',
                              available_nodes: List['DiscoveredNode'],
                              strategy: PartitionStrategy = PartitionStrategy.HYBRID_OPTIMAL,
                              constraints: Optional[Dict[str, Any]] = None) -> PartitionResult:
        """
        Particionar dataset entre nodos disponibles usando estrategia óptima.

        Args:
            dataset: Información del dataset a particionar
            available_nodes: Lista de nodos disponibles
            strategy: Estrategia de particionamiento
            constraints: Restricciones adicionales

        Returns:
            Resultado del particionamiento
        """
        try:
            if not dataset.chunks:
                raise ValueError("Dataset must have chunks to partition")

            if not available_nodes:
                raise ValueError("No available nodes for partitioning")

            constraints = constraints or {}

            # Filtrar nodos por restricciones básicas
            filtered_nodes = self._filter_nodes_by_constraints(available_nodes, constraints)

            if not filtered_nodes:
                logger.warning("No nodes passed filtering constraints")
                return PartitionResult(strategy_used=strategy.value)

            # Calcular scores para cada nodo
            node_scores = await self._calculate_node_scores(filtered_nodes, dataset, strategy)

            # Aplicar estrategia de particionamiento
            result = await self._apply_partitioning_strategy(
                dataset, node_scores, strategy, constraints
            )

            result.strategy_used = strategy.value

            # Calcular estadísticas del particionamiento
            result.partition_stats = self._calculate_partition_stats(result, dataset, node_scores)

            logger.info(f"✅ Dataset partitioned using {strategy.value} strategy: "
                       f"{len(result.node_assignments)} nodes, "
                       f"{sum(len(chunks) for chunks in result.node_assignments.values())} chunks")

            return result

        except Exception as e:
            logger.error(f"❌ Error partitioning dataset: {e}")
            return PartitionResult(strategy_used=strategy.value)

    def _filter_nodes_by_constraints(self,
                                   nodes: List['DiscoveredNode'],
                                   constraints: Dict[str, Any]) -> List['DiscoveredNode']:
        """Filtrar nodos por restricciones básicas."""
        filtered = []

        for node in nodes:
            # Verificar estado básico
            if node.status != "online":
                continue

            # Verificar capacidades mínimas
            min_cpu = constraints.get('min_cpu_cores', 1)
            min_memory = constraints.get('min_memory_gb', 2)

            node_cpu = node.hardware_specs.get('cpu_count', 0)
            node_memory = node.hardware_specs.get('memory_gb', 0)

            if node_cpu < min_cpu or node_memory < min_memory:
                continue

            # Verificar reputación mínima
            min_reputation = constraints.get('min_reputation', 0.0)
            if node.reputation_score < min_reputation:
                continue

            # Verificar región si especificada
            required_region = constraints.get('required_region')
            if required_region and node.location != required_region:
                continue

            filtered.append(node)

        return filtered

    async def _calculate_node_scores(self,
                                   nodes: List['DiscoveredNode'],
                                   dataset: 'DatasetInfo',
                                   strategy: PartitionStrategy) -> List[NodeScore]:
        """Calcular scores para todos los nodos."""
        node_scores = []

        for node in nodes:
            score = NodeScore(node_id=node.node_id)

            # Score de capacidad
            score.capability_score = self._calculate_capability_score(node)

            # Score geográfico
            score.geographic_score = self._calculate_geographic_score(node, nodes)

            # Score de red
            score.network_score = self._calculate_network_score(node)

            # Score de eficiencia
            score.efficiency_score = self._calculate_efficiency_score(node)

            # Score total ponderado según estrategia
            score.total_score = self._calculate_total_score(score, strategy)

            node_scores.append(score)

        # Normalizar scores
        self._normalize_scores(node_scores)

        return node_scores

    def _calculate_capability_score(self, node: 'DiscoveredNode') -> float:
        """Calcular score basado en capacidades hardware."""
        specs = node.hardware_specs
        dynamic = node.dynamic_capabilities

        score = 0.0

        # CPU cores
        cpu_cores = specs.get('cpu_count', 1)
        score += self.capability_weights['cpu_cores'] * min(cpu_cores / 8.0, 1.0)  # Normalizar a 8 cores

        # Memoria
        memory_gb = specs.get('memory_gb', 4)
        score += self.capability_weights['memory_gb'] * min(memory_gb / 16.0, 1.0)  # Normalizar a 16GB

        # GPU disponible
        gpu_available = specs.get('gpu_available', False) or dynamic.get('gpu_available', False)
        score += self.capability_weights['gpu_available'] * (1.0 if gpu_available else 0.0)

        # Memoria disponible (%)
        available_memory = dynamic.get('available_memory_percent', 50.0)
        score += self.capability_weights['available_memory_percent'] * (available_memory / 100.0)

        # CPU disponible (%)
        available_cpu = dynamic.get('available_cpu_percent', 50.0)
        score += self.capability_weights['available_cpu_percent'] * (available_cpu / 100.0)

        return score

    def _calculate_geographic_score(self, node: 'DiscoveredNode', all_nodes: List['DiscoveredNode']) -> float:
        """Calcular score basado en distribución geográfica."""
        # Contar nodos por región
        region_counts = {}
        for n in all_nodes:
            region = self._get_node_region(n)
            region_counts[region] = region_counts.get(region, 0) + 1

        node_region = self._get_node_region(node)
        total_nodes = len(all_nodes)

        # Balance de región: favorecer regiones subrepresentadas
        region_balance = 1.0 - (region_counts.get(node_region, 0) / total_nodes)
        score = self.geographic_weights['region_balance'] * region_balance

        # Penalización por latencia (simplificada)
        # En implementación real, calcular latencia real entre nodos
        latency_penalty = 0.1  # Penalización base baja
        score += self.geographic_weights['latency_penalty'] * (1.0 - latency_penalty)

        return score

    def _calculate_network_score(self, node: 'DiscoveredNode') -> float:
        """Calcular score basado en condiciones de red."""
        dynamic = node.dynamic_capabilities

        score = 0.0

        # Ancho de banda estimado
        bandwidth = dynamic.get('network_bandwidth', 50.0)  # Mbps
        score += self.network_weights['bandwidth_estimate'] * min(bandwidth / 100.0, 1.0)

        # Estabilidad de conexión (basada en load factor inverso)
        stability = 1.0 - node.load_factor
        score += self.network_weights['connection_stability'] * stability

        # Factor de carga actual
        load_penalty = 1.0 - node.load_factor
        score += self.network_weights['load_factor'] * load_penalty

        return score

    def _calculate_efficiency_score(self, node: 'DiscoveredNode') -> float:
        """Calcular score basado en eficiencia de entrenamiento."""
        score = 0.0

        # Puntuación de reputación
        reputation = node.reputation_score
        score += self.efficiency_weights['reputation_score'] * reputation

        # Carga actual (inversa)
        current_load = node.load_factor
        score += self.efficiency_weights['current_load'] * (1.0 - current_load)

        # Número de sesiones (penalizar nodos sobrecargados)
        session_count = node.session_count
        session_penalty = min(session_count / 5.0, 1.0)  # Máximo 5 sesiones
        score += self.efficiency_weights['session_count'] * (1.0 - session_penalty)

        return score

    def _calculate_total_score(self, score: NodeScore, strategy: PartitionStrategy) -> float:
        """Calcular score total según estrategia."""
        if strategy == PartitionStrategy.CAPABILITY_WEIGHTED:
            return score.capability_score
        elif strategy == PartitionStrategy.GEOGRAPHIC_BALANCED:
            return score.geographic_score
        elif strategy == PartitionStrategy.NETWORK_OPTIMIZED:
            return score.network_score
        elif strategy == PartitionStrategy.EFFICIENCY_MAXIMIZED:
            return score.efficiency_score
        else:  # HYBRID_OPTIMAL
            # Ponderación equilibrada
            return (0.4 * score.capability_score +
                   0.2 * score.geographic_score +
                   0.2 * score.network_score +
                   0.2 * score.efficiency_score)

    def _normalize_scores(self, node_scores: List[NodeScore]):
        """Normalizar scores para que estén en rango [0,1]."""
        if not node_scores:
            return

        # Encontrar min/max para cada tipo de score
        capability_scores = [s.capability_score for s in node_scores]
        geographic_scores = [s.geographic_score for s in node_scores]
        network_scores = [s.network_score for s in node_scores]
        efficiency_scores = [s.efficiency_score for s in node_scores]
        total_scores = [s.total_score for s in node_scores]

        def normalize_values(values):
            min_val = min(values)
            max_val = max(values)
            if max_val == min_val:
                return [1.0 for _ in values]
            return [(v - min_val) / (max_val - min_val) for v in values]

        cap_norm = normalize_values(capability_scores)
        geo_norm = normalize_values(geographic_scores)
        net_norm = normalize_values(network_scores)
        eff_norm = normalize_values(efficiency_scores)
        total_norm = normalize_values(total_scores)

        for i, score in enumerate(node_scores):
            score.capability_score = cap_norm[i]
            score.geographic_score = geo_norm[i]
            score.network_score = net_norm[i]
            score.efficiency_score = eff_norm[i]
            score.total_score = total_norm[i]

    async def _apply_partitioning_strategy(self,
                                         dataset: 'DatasetInfo',
                                         node_scores: List[NodeScore],
                                         strategy: PartitionStrategy,
                                         constraints: Dict[str, Any]) -> PartitionResult:
        """Aplicar estrategia de particionamiento específica."""
        result = PartitionResult()

        # Ordenar nodos por score total (descendente)
        sorted_nodes = sorted(node_scores, key=lambda s: s.total_score, reverse=True)

        # Calcular distribución de chunks
        total_chunks = len(dataset.chunks)
        total_score = sum(s.total_score for s in sorted_nodes)

        if total_score == 0:
            # Distribución equitativa si todos tienen score 0
            chunks_per_node = total_chunks // len(sorted_nodes)
            remainder = total_chunks % len(sorted_nodes)

            for i, node_score in enumerate(sorted_nodes):
                assigned = chunks_per_node + (1 if i < remainder else 0)
                node_score.assigned_chunks = min(assigned, self.max_chunks_per_node)
        else:
            # Distribución proporcional al score
            for node_score in sorted_nodes:
                proportion = node_score.total_score / total_score
                assigned = int(total_chunks * proportion)
                assigned = max(self.min_chunks_per_node, min(assigned, self.max_chunks_per_node))
                node_score.assigned_chunks = assigned

        # Asignar chunks específicos a nodos
        chunk_index = 0
        for node_score in sorted_nodes:
            if node_score.assigned_chunks > 0:
                assigned_chunks = []
                for _ in range(node_score.assigned_chunks):
                    if chunk_index < total_chunks:
                        chunk_id = dataset.chunks[chunk_index]['chunk_id']
                        assigned_chunks.append(chunk_id)
                        chunk_index += 1

                if assigned_chunks:
                    result.node_assignments[node_score.node_id] = assigned_chunks

        # Calcular score de optimización
        result.optimization_score = self._calculate_optimization_score(result, node_scores, strategy)

        return result

    def _calculate_optimization_score(self,
                                    result: PartitionResult,
                                    node_scores: List[NodeScore],
                                    strategy: PartitionStrategy) -> float:
        """Calcular score de optimización del particionamiento."""
        if not result.node_assignments:
            return 0.0

        # Score basado en balance de carga
        assigned_counts = [len(chunks) for chunks in result.node_assignments.values()]
        if not assigned_counts:
            return 0.0

        mean_chunks = sum(assigned_counts) / len(assigned_counts)
        variance = sum((count - mean_chunks) ** 2 for count in assigned_counts) / len(assigned_counts)
        balance_score = 1.0 / (1.0 + variance)  # Score más alto = mejor balance

        # Score basado en capacidades utilizadas
        capability_utilization = 0.0
        for node_score in node_scores:
            if node_score.node_id in result.node_assignments:
                chunks_assigned = len(result.node_assignments[node_score.node_id])
                max_possible = self.max_chunks_per_node
                utilization = chunks_assigned / max_possible if max_possible > 0 else 0
                capability_utilization += utilization * node_score.capability_score

        capability_score = capability_utilization / len(result.node_assignments) if result.node_assignments else 0.0

        # Score combinado
        return 0.6 * balance_score + 0.4 * capability_score

    def _calculate_partition_stats(self,
                                 result: PartitionResult,
                                 dataset: 'DatasetInfo',
                                 node_scores: List[NodeScore]) -> Dict[str, Any]:
        """Calcular estadísticas del particionamiento."""
        stats = {
            'total_chunks': len(dataset.chunks),
            'assigned_chunks': sum(len(chunks) for chunks in result.node_assignments.values()),
            'assigned_nodes': len(result.node_assignments),
            'unassigned_chunks': len(dataset.chunks) - sum(len(chunks) for chunks in result.node_assignments.values()),
            'avg_chunks_per_node': 0.0,
            'chunk_distribution': {},
            'node_scores': {}
        }

        if result.node_assignments:
            stats['avg_chunks_per_node'] = stats['assigned_chunks'] / len(result.node_assignments)

            # Distribución de chunks
            chunk_counts = [len(chunks) for chunks in result.node_assignments.values()]
            stats['chunk_distribution'] = {
                'min': min(chunk_counts),
                'max': max(chunk_counts),
                'median': sorted(chunk_counts)[len(chunk_counts) // 2]
            }

        # Scores de nodos
        for score in node_scores:
            stats['node_scores'][score.node_id] = {
                'total_score': score.total_score,
                'capability_score': score.capability_score,
                'geographic_score': score.geographic_score,
                'network_score': score.network_score,
                'efficiency_score': score.efficiency_score,
                'assigned_chunks': score.assigned_chunks
            }

        return stats

    def _get_node_region(self, node: 'DiscoveredNode') -> str:
        """Determinar región geográfica de un nodo."""
        location = node.location or ""

        # Mapeo simplificado de ubicaciones a regiones
        if any(term in location.upper() for term in ['EUROPE', 'EU', 'SPAIN', 'FRANCE', 'GERMANY', 'UK']):
            return 'EU'
        elif any(term in location.upper() for term in ['US', 'USA', 'AMERICA', 'CALIFORNIA', 'NEW YORK']):
            return 'US'
        elif any(term in location.upper() for term in ['ASIA', 'CHINA', 'JAPAN', 'INDIA', 'KOREA']):
            return 'ASIA'
        else:
            return 'OTHER'

    async def repartition_dataset(self,
                                current_result: PartitionResult,
                                updated_nodes: List['DiscoveredNode'],
                                dataset: 'DatasetInfo',
                                strategy: PartitionStrategy = PartitionStrategy.HYBRID_OPTIMAL) -> PartitionResult:
        """
        Reparticionar dataset cuando cambian las condiciones de los nodos.

        Args:
            current_result: Resultado actual del particionamiento
            updated_nodes: Lista actualizada de nodos
            dataset: Información del dataset
            strategy: Nueva estrategia a usar

        Returns:
            Nuevo resultado del particionamiento
        """
        logger.info("🔄 Repartitioning dataset due to node changes")

        # Crear nuevo particionamiento
        new_result = await self.partition_dataset(dataset, updated_nodes, strategy)

        # Log cambios
        old_assignments = set(current_result.node_assignments.keys())
        new_assignments = set(new_result.node_assignments.keys())

        added_nodes = new_assignments - old_assignments
        removed_nodes = old_assignments - new_assignments

        if added_nodes:
            logger.info(f"➕ Added nodes to partition: {added_nodes}")
        if removed_nodes:
            logger.info(f"➖ Removed nodes from partition: {removed_nodes}")

        return new_result