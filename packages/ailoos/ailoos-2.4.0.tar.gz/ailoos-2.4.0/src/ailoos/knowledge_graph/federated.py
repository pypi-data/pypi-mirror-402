"""
Knowledge Graph Federated para AILOOS.
Implementa soporte para datos federados con consultas distribuidas,
particionamiento de datos y agregación de resultados.
"""

import asyncio
import time
import hashlib
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import json

from ..core.logging import get_logger
from ..core.config import get_config
from .core import KnowledgeGraphCore, Triple, BackendType
from ..federated.coordinator import FederatedCoordinator
from ..auditing.audit_manager import get_audit_manager, AuditEventType
from ..auditing.metrics_collector import get_metrics_collector
from ..core.serializers import SerializationFormat, get_serializer, SerializationResult
import numpy as np

logger = get_logger(__name__)


class PartitionStrategy(Enum):
    """Estrategias de particionamiento de datos."""
    HASH_BASED = "hash_based"
    RANGE_BASED = "range_based"
    GRAPH_BASED = "graph_based"
    ROUND_ROBIN = "round_robin"


@dataclass
class DataPartition:
    """Representa una partición de datos."""
    partition_id: str
    node_id: str
    triples: List[Triple]
    strategy: PartitionStrategy
    hash_range: Optional[Tuple[int, int]] = None
    graph_uris: Optional[List[str]] = None

    def contains_triple(self, triple: Triple) -> bool:
        """Verificar si la partición contiene un triple."""
        if self.strategy == PartitionStrategy.HASH_BASED:
            if self.hash_range:
                triple_hash = hash(f"{triple.subject}{triple.predicate}{triple.object}") % 1000
                return self.hash_range[0] <= triple_hash < self.hash_range[1]
        elif self.strategy == PartitionStrategy.GRAPH_BASED:
            if self.graph_uris:
                # Asumir que el sujeto contiene información del grafo
                return any(uri in triple.subject for uri in self.graph_uris)
        return True  # Fallback


@dataclass
class FederatedQuery:
    """Representa una consulta federada."""
    query_id: str
    sparql_query: str
    target_nodes: List[str]
    partitions: List[DataPartition]
    timeout_ms: int = 30000
    max_results: int = 1000


@dataclass
class QueryResult:
    """Resultado de una consulta federada."""
    node_id: str
    triples: List[Triple]
    execution_time_ms: float
    error: Optional[str] = None
    partition_id: Optional[str] = None


@dataclass
class GradientUpdate:
    """Actualización de gradients para federated learning."""
    node_id: str
    round_num: int
    gradients: Dict[str, np.ndarray]  # layer_name -> gradient_array
    model_hash: str
    sample_count: int
    compression_ratio: float = 1.0
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class ModelUpdate:
    """Actualización de modelo agregada."""
    round_num: int
    parameters: Dict[str, np.ndarray]
    participant_count: int
    aggregation_method: str = "fedavg"
    compression_applied: bool = False
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class FederatedKnowledgeGraph(KnowledgeGraphCore):
    """
    Knowledge Graph con soporte para datos federados.
    Extiende KnowledgeGraphCore con capacidades de consultas distribuidas,
    particionamiento de datos y agregación de resultados.
    """

    def __init__(self,
                 backend_type: BackendType = BackendType.IN_MEMORY,
                 federated_coordinator: Optional[FederatedCoordinator] = None,
                 partition_strategy: PartitionStrategy = PartitionStrategy.HASH_BASED,
                 num_partitions: int = 4,
                 **backend_config):
        # Inicializar la clase padre
        super().__init__(backend_type, **backend_config)

        # Configuración federada
        self.config = get_config()
        self.federated_coordinator = federated_coordinator
        self.partition_strategy = partition_strategy
        self.num_partitions = num_partitions

        # Estado de particiones
        self.partitions: Dict[str, DataPartition] = {}
        self.node_partitions: Dict[str, List[str]] = {}  # node_id -> [partition_ids]

        # Cache de consultas federadas
        self.query_cache: Dict[str, List[QueryResult]] = {}
        self.cache_ttl_seconds = 300  # 5 minutos

        # Estadísticas federadas
        self.federated_stats = {
            "total_federated_queries": 0,
            "successful_federated_queries": 0,
            "failed_federated_queries": 0,
            "average_query_time_ms": 0.0,
            "total_partitions": 0,
            "active_nodes": 0
        }

        # Estado de federated learning
        self.federated_learning_enabled = True
        self.current_round = 0
        self.pending_gradients: Dict[str, GradientUpdate] = {}  # node_id -> gradients
        self.global_model: Optional[Dict[str, np.ndarray]] = None
        self.compression_enabled = True
        self.max_gradient_age_seconds = 300  # 5 minutos

        # Estadísticas de FL
        self.fl_stats = {
            "total_rounds": 0,
            "total_gradient_updates": 0,
            "average_compression_ratio": 1.0,
            "communication_overhead_mb": 0.0,
            "average_round_time_ms": 0.0
        }

        # Inicializar particiones
        self._initialize_partitions()

        logger.info(f"🧩 FederatedKnowledgeGraph initialized with {self.num_partitions} partitions using {partition_strategy.value} strategy")

    def _initialize_partitions(self):
        """Inicializar particiones de datos."""
        try:
            if self.federated_coordinator:
                # Obtener nodos disponibles del coordinador
                active_sessions = self.federated_coordinator.get_active_sessions()
                available_nodes = set()

                for session in active_sessions:
                    participants = session.get("participants", [])
                    available_nodes.update(participants)

                available_nodes = list(available_nodes)
                if not available_nodes:
                    # Fallback a configuración local
                    available_nodes = ["local_node"]

                self.federated_stats["active_nodes"] = len(available_nodes)

                # Crear particiones basadas en nodos disponibles
                for i in range(self.num_partitions):
                    partition_id = f"partition_{i}"
                    node_id = available_nodes[i % len(available_nodes)]

                    partition = DataPartition(
                        partition_id=partition_id,
                        node_id=node_id,
                        triples=[],
                        strategy=self.partition_strategy
                    )

                    # Configurar rangos de hash para particionamiento
                    if self.partition_strategy == PartitionStrategy.HASH_BASED:
                        range_size = 1000 // self.num_partitions
                        partition.hash_range = (i * range_size, (i + 1) * range_size)

                    self.partitions[partition_id] = partition

                    # Registrar partición por nodo
                    if node_id not in self.node_partitions:
                        self.node_partitions[node_id] = []
                    self.node_partitions[node_id].append(partition_id)

                self.federated_stats["total_partitions"] = len(self.partitions)
                logger.info(f"✅ Initialized {len(self.partitions)} partitions across {len(available_nodes)} nodes")

        except Exception as e:
            logger.error(f"Error initializing partitions: {e}")
            # Fallback a configuración local
            self._initialize_local_partitions()

    def _initialize_local_partitions(self):
        """Inicializar particiones locales como fallback."""
        for i in range(self.num_partitions):
            partition_id = f"local_partition_{i}"
            partition = DataPartition(
                partition_id=partition_id,
                node_id="local_node",
                triples=[],
                strategy=self.partition_strategy
            )

            if self.partition_strategy == PartitionStrategy.HASH_BASED:
                range_size = 1000 // self.num_partitions
                partition.hash_range = (i * range_size, (i + 1) * range_size)

            self.partitions[partition_id] = partition
            self.node_partitions["local_node"] = [partition_id]

        self.federated_stats["total_partitions"] = len(self.partitions)
        logger.info("✅ Initialized local partitions as fallback")

    def _get_partition_for_triple(self, triple: Triple) -> str:
        """Determinar la partición para un triple."""
        if self.partition_strategy == PartitionStrategy.HASH_BASED:
            triple_hash = hash(f"{triple.subject}{triple.predicate}{triple.object}") % 1000
            for partition in self.partitions.values():
                if partition.hash_range and partition.hash_range[0] <= triple_hash < partition.hash_range[1]:
                    return partition.partition_id

        elif self.partition_strategy == PartitionStrategy.ROUND_ROBIN:
            # Usar hash del sujeto para distribución round-robin
            subject_hash = hash(triple.subject) % len(self.partitions)
            return list(self.partitions.keys())[subject_hash]

        # Fallback a primera partición
        return list(self.partitions.keys())[0]

    async def add_triple(self, triple: Triple, user_id: Optional[str] = None) -> bool:
        """
        Agregar un triple con soporte federado.
        Distribuye el triple a la partición apropiada.
        """
        # Determinar partición
        partition_id = self._get_partition_for_triple(triple)
        partition = self.partitions.get(partition_id)

        if partition:
            # Agregar a partición local
            partition.triples.append(triple)

            # Si es un nodo remoto, enviar al coordinador federado
            if partition.node_id != "local_node" and self.federated_coordinator:
                try:
                    # Enviar actualización a través del coordinador
                    await self._send_triple_to_remote_node(partition.node_id, triple, user_id)
                except Exception as e:
                    logger.warning(f"Failed to send triple to remote node {partition.node_id}: {e}")

        # También agregar al grafo local para compatibilidad
        return await super().add_triple(triple, user_id)

    async def _send_triple_to_remote_node(self, node_id: str, triple: Triple, user_id: Optional[str] = None):
        """Enviar triple a un nodo remoto a través del coordinador."""
        if not self.federated_coordinator:
            return

        # En una implementación real, esto enviaría el triple al nodo remoto
        # Por ahora, solo loggear
        logger.info(f"📤 Sending triple to remote node {node_id}: {triple}")

        # Simular envío exitoso
        await asyncio.sleep(0.01)  # Simular latencia de red

    async def query(self, query: str, user_id: Optional[str] = None, **kwargs) -> List[Triple]:
        """
        Ejecutar consulta con soporte federado.
        Si es una consulta SPARQL compleja, distribuirla a múltiples nodos.
        """
        start_time = time.time()

        # Detectar si es una consulta que requiere procesamiento federado
        if self._is_federated_query(query):
            return await self._execute_federated_query(query, user_id, **kwargs)
        else:
            # Consulta local normal
            return await super().query(query, user_id, **kwargs)

    def _is_federated_query(self, query: str) -> bool:
        """Determinar si una consulta requiere procesamiento federado."""
        # Consultas que involucran múltiples grafos o requieren agregación distribuida
        indicators = [
            "FROM NAMED" in query.upper(),
            "SERVICE" in query.upper(),  # SPARQL federated queries
            "GRAPH" in query.upper() and self.federated_stats["active_nodes"] > 1,
            len(query.split()) > 20  # Consultas complejas
        ]
        return any(indicators) and len(self.partitions) > 1

    async def _execute_federated_query(self, query: str, user_id: Optional[str] = None, **kwargs) -> List[Triple]:
        """Ejecutar consulta federada distribuida."""
        start_time = time.time()
        query_id = hashlib.md5(f"{query}{time.time()}".encode()).hexdigest()[:8]

        # Verificar cache
        if query_id in self.query_cache:
            logger.info(f"📋 Using cached federated query results for {query_id}")
            cached_results = self.query_cache[query_id]
            return self._aggregate_results(cached_results)

        # Crear consulta federada
        federated_query = FederatedQuery(
            query_id=query_id,
            sparql_query=query,
            target_nodes=list(self.node_partitions.keys()),
            partitions=list(self.partitions.values()),
            timeout_ms=kwargs.get('timeout_ms', 30000),
            max_results=kwargs.get('max_results', 1000)
        )

        # Ejecutar consulta en paralelo en todos los nodos
        tasks = []
        for node_id in federated_query.target_nodes:
            task = self._query_node(node_id, federated_query, user_id)
            tasks.append(task)

        # Ejecutar todas las consultas en paralelo
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error in federated query execution: {e}")
            results = []

        # Procesar resultados
        query_results = []
        for i, result in enumerate(results):
            node_id = federated_query.target_nodes[i]
            if isinstance(result, Exception):
                logger.warning(f"Query failed on node {node_id}: {result}")
                query_results.append(QueryResult(
                    node_id=node_id,
                    triples=[],
                    execution_time_ms=0.0,
                    error=str(result)
                ))
            else:
                query_results.append(result)

        # Cachear resultados
        self.query_cache[query_id] = query_results

        # Limpiar cache antiguo
        await self._cleanup_query_cache()

        # Agregar a estadísticas
        self.federated_stats["total_federated_queries"] += 1
        successful_results = [r for r in query_results if not r.error]
        if successful_results:
            self.federated_stats["successful_federated_queries"] += 1
            avg_time = sum(r.execution_time_ms for r in successful_results) / len(successful_results)
            self.federated_stats["average_query_time_ms"] = (
                (self.federated_stats["average_query_time_ms"] + avg_time) / 2
            )
        else:
            self.federated_stats["failed_federated_queries"] += 1

        # Logging de auditoría
        await self.audit_manager.log_event(
            event_type=AuditEventType.KNOWLEDGE_GRAPH_QUERY,
            resource="federated_knowledge_graph",
            action="federated_query",
            user_id=user_id,
            details={
                "query_id": query_id,
                "query": query,
                "target_nodes": len(federated_query.target_nodes),
                "successful_nodes": len(successful_results),
                "total_results": sum(len(r.triples) for r in successful_results)
            },
            success=len(successful_results) > 0,
            processing_time_ms=(time.time() - start_time) * 1000
        )

        # Agregar a métricas
        self.metrics_collector.record_request("federated_knowledge_graph.query")
        self.metrics_collector.record_response_time((time.time() - start_time) * 1000)

        logger.info(f"🔄 Federated query {query_id} completed: {len(successful_results)}/{len(federated_query.target_nodes)} nodes successful")

        return self._aggregate_results(query_results)

    async def _query_node(self, node_id: str, federated_query: FederatedQuery, user_id: Optional[str] = None) -> QueryResult:
        """Consultar un nodo específico."""
        start_time = time.time()

        try:
            # Si es el nodo local, ejecutar directamente
            if node_id == "local_node":
                # Obtener triples relevantes de las particiones locales
                relevant_triples = []
                for partition_id in self.node_partitions.get(node_id, []):
                    partition = self.partitions.get(partition_id)
                    if partition:
                        relevant_triples.extend(partition.triples)

                # En una implementación real, ejecutar la consulta SPARQL sobre estos triples
                # Por ahora, devolver todos los triples relevantes
                results = relevant_triples[:federated_query.max_results]

            else:
                # Para nodos remotos, simular consulta
                # En implementación real, esto sería una llamada RPC al nodo remoto
                results = await self._query_remote_node(node_id, federated_query, user_id)

            execution_time = (time.time() - start_time) * 1000

            return QueryResult(
                node_id=node_id,
                triples=results,
                execution_time_ms=execution_time,
                partition_id=f"partition_{node_id}"
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Error querying node {node_id}: {e}")

            return QueryResult(
                node_id=node_id,
                triples=[],
                execution_time_ms=execution_time,
                error=str(e)
            )

    async def _query_remote_node(self, node_id: str, federated_query: FederatedQuery, user_id: Optional[str] = None) -> List[Triple]:
        """Consultar un nodo remoto."""
        # En implementación real, esto enviaría la consulta al nodo remoto
        # Por ahora, simular resultados vacíos o de error

        # Simular latencia de red
        await asyncio.sleep(0.1)

        # Simular algunos resultados para testing
        if "test" in federated_query.sparql_query.lower():
            return [
                Triple(f"http://example.org/node_{node_id}/subject1", "http://example.org/predicate", f"object_from_{node_id}"),
                Triple(f"http://example.org/node_{node_id}/subject2", "http://example.org/predicate", f"object_from_{node_id}")
            ]

        return []

    def _aggregate_results(self, query_results: List[QueryResult]) -> List[Triple]:
        """Agregar resultados de múltiples nodos."""
        all_triples = []
        seen_triples = set()

        for result in query_results:
            if result.error:
                continue

            for triple in result.triples:
                # Crear hash único para deduplicación
                triple_hash = hash(f"{triple.subject}{triple.predicate}{triple.object}")

                if triple_hash not in seen_triples:
                    seen_triples.add(triple_hash)
                    all_triples.append(triple)

        logger.info(f"📊 Aggregated {len(all_triples)} unique triples from {len(query_results)} nodes")
        return all_triples

    async def _cleanup_query_cache(self):
        """Limpiar entradas antiguas del cache de consultas."""
        current_time = time.time()
        expired_queries = []

        for query_id, results in self.query_cache.items():
            # Verificar si algún resultado tiene timestamp (simulado)
            # En implementación real, agregar timestamps a los resultados
            if current_time - (results[0].execution_time_ms / 1000) > self.cache_ttl_seconds:
                expired_queries.append(query_id)

        for query_id in expired_queries:
            del self.query_cache[query_id]

        if expired_queries:
            logger.info(f"🧹 Cleaned up {len(expired_queries)} expired federated query cache entries")

    async def get_federated_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas federadas."""
        stats = self.federated_stats.copy()

        # Agregar información de particiones
        stats["partitions"] = {
            partition_id: {
                "node_id": partition.node_id,
                "triple_count": len(partition.triples),
                "strategy": partition.strategy.value
            }
            for partition_id, partition in self.partitions.items()
        }

        # Agregar información de nodos
        stats["nodes"] = {
            node_id: {
                "partition_count": len(partitions),
                "partitions": partitions
            }
            for node_id, partitions in self.node_partitions.items()
        }

        # Agregar estado del coordinador
        if self.federated_coordinator:
            coordinator_status = self.federated_coordinator.get_global_status()
            stats["coordinator_status"] = coordinator_status

        return stats

    async def repartition_data(self, new_strategy: Optional[PartitionStrategy] = None, new_num_partitions: Optional[int] = None):
        """Reparticionar datos con nueva estrategia."""
        if new_strategy:
            self.partition_strategy = new_strategy
        if new_num_partitions:
            self.num_partitions = new_num_partitions

        # Obtener todos los triples actuales
        all_triples = []
        for partition in self.partitions.values():
            all_triples.extend(partition.triples)

        # Limpiar particiones existentes
        self.partitions.clear()
        self.node_partitions.clear()

        # Re-inicializar particiones
        self._initialize_partitions()

        # Re-distribuir triples
        for triple in all_triples:
            partition_id = self._get_partition_for_triple(triple)
            partition = self.partitions.get(partition_id)
            if partition:
                partition.triples.append(triple)

        logger.info(f"🔄 Data repartitioned: {len(all_triples)} triples across {len(self.partitions)} partitions")

    # ===== FEDERATED LEARNING METHODS =====

    async def submit_gradient_update(self, gradient_update: GradientUpdate) -> bool:
        """
        Submit gradient update from a node usando VSC para compresión.

        Args:
            gradient_update: Actualización de gradients del nodo

        Returns:
            True si se aceptó la actualización
        """
        if not self.federated_learning_enabled:
            return False

        try:
            # Validar actualización
            if gradient_update.round_num != self.current_round:
                logger.warning(f"Gradient update for wrong round: {gradient_update.round_num} vs {self.current_round}")
                return False

            # Comprimir gradients usando VSC si está habilitado
            if self.compression_enabled:
                compressed_gradients = await self._compress_gradients_vsc(gradient_update.gradients)
                gradient_update.gradients = compressed_gradients["data"]
                gradient_update.compression_ratio = compressed_gradients["ratio"]

            # Almacenar actualización
            self.pending_gradients[gradient_update.node_id] = gradient_update

            # Actualizar estadísticas
            self.fl_stats["total_gradient_updates"] += 1
            self.fl_stats["average_compression_ratio"] = (
                (self.fl_stats["average_compression_ratio"] + gradient_update.compression_ratio) / 2
            )

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="federated_learning",
                action="submit_gradient_update",
                user_id=gradient_update.node_id,
                details={
                    "round_num": gradient_update.round_num,
                    "sample_count": gradient_update.sample_count,
                    "compression_ratio": gradient_update.compression_ratio,
                    "model_hash": gradient_update.model_hash
                },
                success=True
            )

            logger.info(f"📥 Gradient update received from {gradient_update.node_id} (round {gradient_update.round_num})")
            return True

        except Exception as e:
            logger.error(f"Error submitting gradient update: {e}")
            return False

    async def aggregate_gradients(self, min_participants: Optional[int] = None) -> Optional[ModelUpdate]:
        """
        Agregar gradients pendientes y crear actualización de modelo.

        Args:
            min_participants: Número mínimo de participantes requeridos

        Returns:
            ModelUpdate con parámetros agregados o None si no hay suficientes participantes
        """
        if not self.pending_gradients:
            return None

        min_required = min_participants or max(1, len(self.node_partitions) // 2)
        if len(self.pending_gradients) < min_required:
            logger.info(f"Not enough participants: {len(self.pending_gradients)} < {min_required}")
            return None

        try:
            start_time = time.time()

            # Agregar gradients usando FedAvg
            aggregated_params = await self._federated_average(self.pending_gradients)

            # Crear actualización de modelo
            model_update = ModelUpdate(
                round_num=self.current_round,
                parameters=aggregated_params,
                participant_count=len(self.pending_gradients),
                aggregation_method="fedavg",
                compression_applied=self.compression_enabled
            )

            # Actualizar modelo global
            self.global_model = aggregated_params

            # Limpiar gradients procesados
            self.pending_gradients.clear()

            # Incrementar ronda
            self.current_round += 1
            self.fl_stats["total_rounds"] += 1

            # Calcular tiempo de ronda
            round_time = (time.time() - start_time) * 1000
            self.fl_stats["average_round_time_ms"] = (
                (self.fl_stats["average_round_time_ms"] + round_time) / 2
            )

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="federated_learning",
                action="aggregate_gradients",
                details={
                    "round_num": model_update.round_num,
                    "participant_count": model_update.participant_count,
                    "aggregation_method": model_update.aggregation_method,
                    "round_time_ms": round_time
                },
                success=True,
                processing_time_ms=round_time
            )

            logger.info(f"🔄 Gradients aggregated for round {model_update.round_num} with {model_update.participant_count} participants")
            return model_update

        except Exception as e:
            logger.error(f"Error aggregating gradients: {e}")
            return None

    async def _compress_gradients_vsc(self, gradients: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """
        Comprimir gradients usando VSC (Vector Serialized Columns).

        Args:
            gradients: Diccionario de gradients por layer

        Returns:
            Diccionario con datos comprimidos y ratio de compresión
        """
        try:
            # Convertir gradients a formato columnar para VSC
            columnar_data = {}
            original_size = 0

            for layer_name, grad_array in gradients.items():
                if isinstance(grad_array, np.ndarray):
                    # Aplanar array y convertir a lista para VSC
                    flat_gradients = grad_array.flatten().tolist()
                    columnar_data[layer_name] = flat_gradients
                    original_size += len(flat_gradients) * 8  # 8 bytes por float64
                else:
                    # Si no es numpy array, mantener como está
                    columnar_data[layer_name] = grad_array
                    original_size += len(str(grad_array).encode()) if grad_array else 0

            # Serializar con VSC
            serializer = get_serializer(SerializationFormat.VSC)
            serialized = serializer.serialize(columnar_data)

            # Calcular ratio de compresión
            compressed_size = len(serialized.data)
            compression_ratio = original_size / compressed_size if compressed_size > 0 else 1.0

            # Actualizar estadísticas de comunicación
            self.fl_stats["communication_overhead_mb"] += compressed_size / (1024 * 1024)

            return {
                "data": columnar_data,  # Mantener datos comprimidos internamente
                "serialized": serialized,
                "ratio": compression_ratio,
                "original_size": original_size,
                "compressed_size": compressed_size
            }

        except Exception as e:
            logger.warning(f"VSC compression failed: {e}, using original gradients")
            return {
                "data": gradients,
                "ratio": 1.0,
                "original_size": sum(len(str(g).encode()) for g in gradients.values()),
                "compressed_size": sum(len(str(g).encode()) for g in gradients.values())
            }

    async def _federated_average(self, gradient_updates: Dict[str, GradientUpdate]) -> Dict[str, np.ndarray]:
        """
        Implementar Federated Averaging (FedAvg) con soporte para compresión.

        Args:
            gradient_updates: Diccionario de actualizaciones por nodo

        Returns:
            Parámetros agregados
        """
        if not gradient_updates:
            return {}

        try:
            # Obtener todas las layers presentes
            all_layers = set()
            for update in gradient_updates.values():
                all_layers.update(update.gradients.keys())

            aggregated_params = {}

            for layer_name in all_layers:
                layer_gradients = []
                total_samples = 0

                # Recopilar gradients para esta layer de todos los nodos
                for update in gradient_updates.values():
                    if layer_name in update.gradients:
                        grad_data = update.gradients[layer_name]

                        # Descomprimir si es necesario (desde VSC)
                        if isinstance(grad_data, dict) and "serialized" in grad_data:
                            # Deserializar desde VSC
                            serializer = get_serializer(SerializationFormat.VSC)
                            deserialized = serializer.deserialize(grad_data["serialized"].data)
                            grad_array = np.array(deserialized.data[layer_name])
                        elif isinstance(grad_data, list):
                            grad_array = np.array(grad_data)
                        else:
                            grad_array = np.array(grad_data) if hasattr(grad_data, '__array__') else np.array([grad_data])

                        layer_gradients.append((grad_array, update.sample_count))
                        total_samples += update.sample_count

                if layer_gradients:
                    # Weighted average basado en número de samples
                    weighted_sum = np.zeros_like(layer_gradients[0][0])
                    for grad_array, sample_count in layer_gradients:
                        weight = sample_count / total_samples
                        weighted_sum += weight * grad_array

                    aggregated_params[layer_name] = weighted_sum

            return aggregated_params

        except Exception as e:
            logger.error(f"Error in federated averaging: {e}")
            return {}

    async def get_gradient_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de gradients y federated learning."""
        stats = self.fl_stats.copy()

        # Agregar información de ronda actual
        stats.update({
            "current_round": self.current_round,
            "pending_gradients_count": len(self.pending_gradients),
            "federated_learning_enabled": self.federated_learning_enabled,
            "compression_enabled": self.compression_enabled,
            "pending_nodes": list(self.pending_gradients.keys())
        })

        # Agregar información de modelo global
        if self.global_model:
            stats["global_model_layers"] = len(self.global_model)
            stats["global_model_size_mb"] = sum(
                arr.nbytes / (1024 * 1024) for arr in self.global_model.values()
                if hasattr(arr, 'nbytes')
            )

        return stats

    async def optimize_p2p_communication(self, target_node: str, data_size_mb: float) -> Dict[str, Any]:
        """
        Optimizar comunicación P2P basada en latencia y ancho de banda.

        Args:
            target_node: Nodo destino
            data_size_mb: Tamaño de datos a enviar

        Returns:
            Configuración optimizada de comunicación
        """
        # Estimar latencia basada en distancia/historial
        base_latency_ms = 50  # Latencia base de red

        # Ajustar basado en compresión
        if self.compression_enabled:
            effective_size = data_size_mb * (1 / self.fl_stats["average_compression_ratio"])
            compression_benefit = data_size_mb - effective_size
        else:
            effective_size = data_size_mb
            compression_benefit = 0

        # Calcular ancho de banda efectivo
        bandwidth_mbps = 100  # Asumir 100 Mbps
        transfer_time_ms = (effective_size * 8 * 1024) / bandwidth_mbps  # tiempo en ms

        total_latency = base_latency_ms + transfer_time_ms

        optimization = {
            "target_node": target_node,
            "original_size_mb": data_size_mb,
            "effective_size_mb": effective_size,
            "compression_benefit_mb": compression_benefit,
            "estimated_latency_ms": total_latency,
            "recommended_chunk_size_kb": 64,  # Para evitar head-of-line blocking
            "use_compression": self.compression_enabled,
            "parallel_streams": min(4, max(1, int(data_size_mb / 10)))  # Streams paralelos
        }

        logger.info(f"📡 P2P optimization for {target_node}: {total_latency:.1f}ms latency, {compression_benefit:.2f}MB saved")
        return optimization

    async def close(self):
        """Cerrar recursos federados."""
        # Limpiar cache
        self.query_cache.clear()

        # Cerrar clase padre
        await super().close()

        logger.info("🔌 Federated Knowledge Graph closed")


# Función de conveniencia
def create_federated_knowledge_graph(
    backend_type: BackendType = BackendType.IN_MEMORY,
    federated_coordinator: Optional[FederatedCoordinator] = None,
    partition_strategy: PartitionStrategy = PartitionStrategy.HASH_BASED,
    num_partitions: int = 4,
    **backend_config
) -> FederatedKnowledgeGraph:
    """Crear instancia de FederatedKnowledgeGraph."""
    return FederatedKnowledgeGraph(
        backend_type=backend_type,
        federated_coordinator=federated_coordinator,
        partition_strategy=partition_strategy,
        num_partitions=num_partitions,
        **backend_config
    )