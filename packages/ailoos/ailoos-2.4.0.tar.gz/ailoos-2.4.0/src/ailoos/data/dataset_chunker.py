"""
Intelligent Dataset Chunker for Federated Distribution
Sistema de chunking inteligente que divide datasets masivos en chunks óptimos
para entrenamiento federado, considerando capacidades de nodos, ancho de banda
y eficiencia de entrenamiento.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import math

try:
    from ..federated.node_scheduler import NodeMetrics
except ImportError:
    # Fallback para desarrollo
    @dataclass
    class NodeMetrics:
        node_id: str
        computational_capacity: float = 0.0
        memory_capacity: float = 0.0
        network_bandwidth: float = 0.0
        reputation_score: float = 0.5
        availability_score: float = 1.0
        current_load: float = 0.0
        latency_ms: float = 0.0
        success_rate: float = 1.0
        participation_count: int = 0
        last_participation: Optional[float] = None
        total_rewards_earned: float = 0.0
        geographic_location: Optional[str] = None
        hardware_specs: Dict[str, Any] = None

logger = logging.getLogger(__name__)


@dataclass
class ChunkConfig:
    """Configuración para el chunking de datasets."""

    # Límites de tamaño de chunks
    max_chunk_size_mb: float = 100.0
    min_chunk_size_mb: float = 10.0

    # Pesos para optimización
    memory_weight: float = 0.4
    bandwidth_weight: float = 0.3
    compute_weight: float = 0.3

    # Objetivos de eficiencia
    target_utilization: float = 0.8
    max_load_threshold: float = 0.8

    # Configuración de calidad
    enable_quality_filter: bool = True
    balance_factor: float = 0.1  # Factor de balanceo entre nodos


@dataclass
class ChunkMetadata:
    """Metadatos de un chunk."""
    node_id: str
    size_mb: float
    num_items: int
    estimated_transfer_time_sec: float
    estimated_processing_time_sec: float
    quality_score: float
    start_idx: int
    end_idx: int


class DatasetChunker:
    """
    Chunking inteligente de datasets para distribución federada.

    Considera factores como capacidades de nodos, ancho de banda de red,
    carga actual y eficiencia de entrenamiento para crear chunks óptimos.
    """

    def __init__(self, config: Optional[ChunkConfig] = None):
        self.config = config or ChunkConfig()
        self.logger = logger

    def chunk_dataset(
        self,
        dataset: Any,
        node_metrics: List[NodeMetrics],
        strategy: str = "optimized"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Divide el dataset en chunks óptimos para cada nodo.

        Args:
            dataset: Dataset a dividir (lista, DataFrame, etc.)
            node_metrics: Lista de métricas de nodos disponibles
            strategy: Estrategia de chunking ('optimized', 'balanced', 'greedy')

        Returns:
            Dict de node_id -> {'chunk': datos_chunk, 'metadata': ChunkMetadata}
        """
        self.logger.info(f"🔀 Iniciando chunking con estrategia: {strategy}")

        # Filtrar nodos elegibles
        eligible_nodes = self._filter_eligible_nodes(node_metrics)

        if not eligible_nodes:
            self.logger.warning("⚠️ No hay nodos elegibles para chunking")
            return {}

        # Estimar tamaño total del dataset
        total_size_mb = self._estimate_dataset_size(dataset)
        self.logger.info(f"📊 Tamaño total del dataset: {total_size_mb:.2f} MB")

        # Calcular capacidades efectivas de nodos
        node_capacities = self._calculate_node_capacities(eligible_nodes)

        # Optimizar asignación de chunks
        if strategy == "optimized":
            assignments = self._optimize_chunk_assignment(total_size_mb, node_capacities)
        elif strategy == "balanced":
            assignments = self._balance_chunk_assignment(total_size_mb, node_capacities)
        elif strategy == "greedy":
            assignments = self._greedy_chunk_assignment(total_size_mb, node_capacities)
        else:
            raise ValueError(f"Estrategia no soportada: {strategy}")

        # Crear chunks físicos
        chunks = self._create_physical_chunks(dataset, assignments, node_capacities)

        self.logger.info(f"✅ Chunking completado: {len(chunks)} chunks creados")
        return chunks

    def _filter_eligible_nodes(self, node_metrics: List[NodeMetrics]) -> List[NodeMetrics]:
        """Filtra nodos elegibles para participar."""
        eligible = []

        for node in node_metrics:
            # Verificar carga máxima
            if node.current_load > self.config.max_load_threshold:
                continue

            # Verificar disponibilidad
            if node.availability_score < 0.7:
                continue

            # Verificar reputación mínima
            if node.reputation_score < 0.3:
                continue

            eligible.append(node)

        self.logger.debug(f"📋 Nodos elegibles: {len(eligible)}/{len(node_metrics)}")
        return eligible

    def _estimate_dataset_size(self, dataset: Any) -> float:
        """
        Estima el tamaño del dataset en MB.
        """
        try:
            if hasattr(dataset, '__len__'):
                num_items = len(dataset)

                # Estimación basada en tipo de datos
                if hasattr(dataset, 'iloc'):  # DataFrame pandas
                    # Estimar tamaño promedio por fila
                    sample_size = min(100, num_items)
                    avg_row_size = 0

                    for i in range(sample_size):
                        row_str = str(dataset.iloc[i])
                        avg_row_size += len(row_str.encode('utf-8'))

                    avg_row_size /= sample_size
                    total_size_bytes = num_items * avg_row_size

                elif isinstance(dataset, list):
                    # Estimar para lista de textos o datos
                    sample_size = min(100, len(dataset))
                    avg_item_size = sum(len(str(item).encode('utf-8')) for item in dataset[:sample_size]) / sample_size
                    total_size_bytes = num_items * avg_item_size

                else:
                    # Estimación por defecto
                    total_size_bytes = num_items * 1024  # 1KB por item

                # Convertir a MB
                size_mb = total_size_bytes / (1024 * 1024)
                return max(size_mb, 1.0)  # Mínimo 1MB

        except Exception as e:
            self.logger.warning(f"Error estimando tamaño del dataset: {e}")

        return 100.0  # Valor por defecto

    def _calculate_node_capacities(self, nodes: List[NodeMetrics]) -> Dict[str, Dict[str, float]]:
        """
        Calcula capacidades efectivas de cada nodo considerando múltiples factores.
        """
        capacities = {}

        for node in nodes:
            # Capacidad de memoria (cuánto puede almacenar/procesar)
            memory_capacity = node.memory_capacity * self.config.max_chunk_size_mb

            # Capacidad de ancho de banda (velocidad de transferencia)
            # Normalizar bandwidth (asumiendo 0-1 scale representa Mbps relativo)
            bandwidth_capacity = node.network_bandwidth * 50.0  # Hasta 50 Mbps

            # Capacidad computacional (velocidad de procesamiento)
            compute_capacity = node.computational_capacity

            # Factor de carga (reduce capacidad efectiva)
            load_factor = 1.0 - node.current_load

            # Factor de latencia (nodos con baja latencia son preferidos)
            latency_factor = max(0.1, 1.0 - (node.latency_ms / 1000.0))  # Normalizar latencia

            # Capacidad total ponderada
            total_capacity = (
                memory_capacity * self.config.memory_weight * load_factor +
                bandwidth_capacity * self.config.bandwidth_weight * latency_factor +
                compute_capacity * self.config.compute_weight * load_factor
            )

            capacities[node.node_id] = {
                'memory': memory_capacity,
                'bandwidth': bandwidth_capacity,
                'compute': compute_capacity,
                'total': total_capacity,
                'load_factor': load_factor,
                'latency_factor': latency_factor,
                'node': node
            }

        return capacities

    def _optimize_chunk_assignment(
        self,
        total_size_mb: float,
        node_capacities: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """
        Asignación optimizada de chunks usando algoritmo de optimización.
        """
        assignments = {}

        # Calcular capacidad total efectiva
        total_capacity = sum(cap['total'] for cap in node_capacities.values())

        if total_capacity == 0:
            return assignments

        # Primera pasada: asignación proporcional
        for node_id, cap in node_capacities.items():
            proportion = cap['total'] / total_capacity
            base_size = proportion * total_size_mb

            # Aplicar límites y factores de eficiencia
            chunk_size = base_size * self.config.target_utilization

            # Ajustar por balance
            chunk_size = self._apply_balance_factor(chunk_size, cap)

            # Aplicar límites
            chunk_size = max(self.config.min_chunk_size_mb,
                            min(self.config.max_chunk_size_mb, chunk_size))

            assignments[node_id] = chunk_size

        # Segunda pasada: rebalanceo para optimizar eficiencia
        assignments = self._rebalance_assignments(assignments, node_capacities, total_size_mb)

        return assignments

    def _balance_chunk_assignment(
        self,
        total_size_mb: float,
        node_capacities: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """
        Asignación balanceada: intenta igualar tamaños de chunks.
        """
        num_nodes = len(node_capacities)
        if num_nodes == 0:
            return {}

        # Tamaño base igual para todos
        base_size = total_size_mb / num_nodes

        assignments = {}
        for node_id in node_capacities.keys():
            # Ajustar por capacidad del nodo
            cap = node_capacities[node_id]
            adjusted_size = base_size * (cap['total'] / sum(c['total'] for c in node_capacities.values()))

            assignments[node_id] = max(self.config.min_chunk_size_mb,
                                     min(self.config.max_chunk_size_mb, adjusted_size))

        return assignments

    def _greedy_chunk_assignment(
        self,
        total_size_mb: float,
        node_capacities: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """
        Asignación greedy: asigna primero a nodos con mayor capacidad.
        """
        # Ordenar nodos por capacidad descendente
        sorted_nodes = sorted(node_capacities.items(),
                            key=lambda x: x[1]['total'], reverse=True)

        assignments = {}
        remaining_size = total_size_mb

        for node_id, cap in sorted_nodes:
            if remaining_size <= 0:
                break

            # Asignar hasta capacidad máxima o lo restante
            max_assignable = min(cap['total'], remaining_size, self.config.max_chunk_size_mb)
            assignments[node_id] = max(self.config.min_chunk_size_mb, max_assignable)
            remaining_size -= assignments[node_id]

        return assignments

    def _apply_balance_factor(self, chunk_size: float, capacity: Dict[str, float]) -> float:
        """Aplica factor de balanceo para evitar sobrecarga."""
        # Reducir ligeramente para nodos con alta carga
        load_penalty = capacity['load_factor'] * self.config.balance_factor
        return chunk_size * (1.0 - load_penalty)

    def _rebalance_assignments(
        self,
        assignments: Dict[str, float],
        node_capacities: Dict[str, Dict[str, float]],
        total_size_mb: float
    ) -> Dict[str, float]:
        """Rebalancea asignaciones para optimizar eficiencia global."""
        # Calcular eficiencia actual
        current_total = sum(assignments.values())

        if abs(current_total - total_size_mb) > 1.0:  # Si hay discrepancia significativa
            # Ajustar proporcionalmente
            factor = total_size_mb / current_total if current_total > 0 else 1.0

            for node_id in assignments:
                assignments[node_id] *= factor
                assignments[node_id] = max(self.config.min_chunk_size_mb,
                                         min(self.config.max_chunk_size_mb, assignments[node_id]))

        return assignments

    def _create_physical_chunks(
        self,
        dataset: Any,
        assignments: Dict[str, float],
        node_capacities: Dict[str, Dict[str, float]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Crea los chunks físicos del dataset.
        """
        chunks = {}

        # Convertir dataset a lista si no lo es
        if not isinstance(dataset, list):
            try:
                dataset = list(dataset)
            except:
                self.logger.error("Dataset no convertible a lista")
                return chunks

        total_items = len(dataset)
        start_idx = 0

        # Estimar tamaño promedio por item
        avg_item_size_kb = self._estimate_avg_item_size(dataset)

        for node_id, chunk_size_mb in assignments.items():
            # Calcular número de items para este chunk
            chunk_items = int((chunk_size_mb * 1024) / avg_item_size_kb)
            chunk_items = max(1, min(chunk_items, total_items - start_idx))

            end_idx = start_idx + chunk_items
            chunk_data = dataset[start_idx:end_idx]

            # Calcular metadatos
            actual_size_mb = (len(chunk_data) * avg_item_size_kb) / 1024
            metadata = self._create_chunk_metadata(
                node_id, chunk_data, actual_size_mb, start_idx, end_idx, node_capacities[node_id]
            )

            chunks[node_id] = {
                'chunk': chunk_data,
                'metadata': metadata
            }

            start_idx = end_idx
            if start_idx >= total_items:
                break

        return chunks

    def _estimate_avg_item_size(self, dataset: list) -> float:
        """Estima el tamaño promedio por item en KB."""
        if not dataset:
            return 1.0

        sample_size = min(100, len(dataset))
        total_size = 0

        for i in range(sample_size):
            item_str = str(dataset[i])
            total_size += len(item_str.encode('utf-8'))

        avg_size_bytes = total_size / sample_size
        return avg_size_bytes / 1024  # KB

    def _create_chunk_metadata(
        self,
        node_id: str,
        chunk_data: list,
        size_mb: float,
        start_idx: int,
        end_idx: int,
        capacity: Dict[str, float]
    ) -> ChunkMetadata:
        """Crea metadatos para un chunk."""
        # Estimar tiempo de transferencia (segundos)
        transfer_time = (size_mb * 8) / capacity['bandwidth'] if capacity['bandwidth'] > 0 else 60.0

        # Estimar tiempo de procesamiento (segundos)
        processing_time = (len(chunk_data) / 1000) / capacity['compute'] if capacity['compute'] > 0 else 30.0

        # Calcular puntuación de calidad
        quality_score = min(1.0, capacity['total'] / self.config.max_chunk_size_mb)

        return ChunkMetadata(
            node_id=node_id,
            size_mb=size_mb,
            num_items=len(chunk_data),
            estimated_transfer_time_sec=transfer_time,
            estimated_processing_time_sec=processing_time,
            quality_score=quality_score,
            start_idx=start_idx,
            end_idx=end_idx
        )

    def validate_chunks(self, chunks: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Valida la calidad y eficiencia de los chunks creados.
        """
        validation_results = {
            'total_chunks': len(chunks),
            'total_size_mb': 0.0,
            'avg_chunk_size_mb': 0.0,
            'size_variance': 0.0,
            'efficiency_score': 0.0,
            'issues': []
        }

        if not chunks:
            validation_results['issues'].append('No chunks created')
            return validation_results

        sizes = []
        qualities = []

        for node_id, chunk_info in chunks.items():
            metadata = chunk_info['metadata']
            sizes.append(metadata.size_mb)
            qualities.append(metadata.quality_score)
            validation_results['total_size_mb'] += metadata.size_mb

            # Validar límites
            if metadata.size_mb < self.config.min_chunk_size_mb:
                validation_results['issues'].append(
                    f'Chunk {node_id} too small: {metadata.size_mb:.2f} MB'
                )
            if metadata.size_mb > self.config.max_chunk_size_mb:
                validation_results['issues'].append(
                    f'Chunk {node_id} too large: {metadata.size_mb:.2f} MB'
                )

        if sizes:
            validation_results['avg_chunk_size_mb'] = sum(sizes) / len(sizes)
            validation_results['size_variance'] = sum((s - validation_results['avg_chunk_size_mb'])**2 for s in sizes) / len(sizes)

        if qualities:
            validation_results['efficiency_score'] = sum(qualities) / len(qualities)

        return validation_results


# Funciones de conveniencia

def create_dataset_chunker(config: Optional[ChunkConfig] = None) -> DatasetChunker:
    """
    Crea una instancia del chunker de datasets.

    Args:
        config: Configuración opcional

    Returns:
        DatasetChunker: Instancia configurada
    """
    return DatasetChunker(config)


def chunk_dataset_for_federated_training(
    dataset: Any,
    node_metrics: List[NodeMetrics],
    config: Optional[ChunkConfig] = None,
    strategy: str = "optimized"
) -> Dict[str, Dict[str, Any]]:
    """
    Función de conveniencia para chunking de datasets federados.

    Args:
        dataset: Dataset a dividir
        node_metrics: Métricas de nodos disponibles
        config: Configuración opcional
        strategy: Estrategia de chunking

    Returns:
        Dict de chunks por nodo
    """
    chunker = create_dataset_chunker(config)
    return chunker.chunk_dataset(dataset, node_metrics, strategy)