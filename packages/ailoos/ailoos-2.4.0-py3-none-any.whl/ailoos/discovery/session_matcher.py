"""
Algoritmo de Matching Nodo-Sesión para Ailoos Federated Learning
Implementa algoritmos avanzados para asignar nodos a sesiones federadas basados en
capacidad computacional, latencia de red, reputación y diversidad geográfica.
"""

import asyncio
import heapq
import math
import time
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import random

from .node_registry import NodeRegistry, NodeRegistration, NodeMetadata
from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SessionConstraints:
    """Restricciones para una sesión federada"""
    min_nodes: int = 3
    max_nodes: int = 10
    required_capabilities: List[str] = field(default_factory=list)
    max_latency_ms: float = 500.0  # Máxima latencia aceptable en ms
    geographical_diversity: bool = True  # Requerir diversidad geográfica
    min_reputation: float = 0.5  # Reputación mínima requerida
    preferred_regions: List[str] = field(default_factory=list)  # Regiones preferidas


@dataclass
class FederatedSession:
    """Representación de una sesión federada"""
    session_id: str
    coordinator_node_id: str
    constraints: SessionConstraints
    model_name: str = ""
    dataset_requirements: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"


@dataclass
class NodeScore:
    """Puntuación de un nodo para una sesión específica"""
    node_id: str
    session_id: str
    total_score: float = 0.0
    capacity_score: float = 0.0  # 40% peso
    latency_score: float = 0.0   # 30% peso
    reputation_score: float = 0.0  # 30% peso
    geographical_score: float = 0.0
    compatibility_score: float = 0.0
    estimated_latency_ms: float = 0.0

    def __lt__(self, other):
        """Para usar en heapq (orden descendente por score)"""
        return self.total_score > other.total_score


@dataclass
class MatchingResult:
    """Resultado del proceso de matching"""
    session_id: str
    matched_nodes: List[str] = field(default_factory=list)
    backup_nodes: List[str] = field(default_factory=list)
    scores: Dict[str, NodeScore] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    diversity_score: float = 0.0
    load_balance_score: float = 0.0

    @property
    def success(self) -> bool:
        """Indica si el matching fue exitoso"""
        return len(self.matched_nodes) >= 1  # Al menos 1 nodo matched

    @property
    def average_score(self) -> float:
        """Puntuación promedio de nodos matched"""
        if not self.matched_nodes:
            return 0.0
        scores = [self.scores[node_id].total_score for node_id in self.matched_nodes if node_id in self.scores]
        return sum(scores) / len(scores) if scores else 0.0


class SessionMatcher:
    """
    Algoritmo avanzado de matching nodo-sesión para federated learning
    Optimiza asignación considerando capacidad, latencia, reputación y diversidad geográfica
    """

    # Pesos de scoring según especificación
    CAPACITY_WEIGHT = 0.40
    LATENCY_WEIGHT = 0.30
    REPUTATION_WEIGHT = 0.30

    def __init__(self, node_registry: NodeRegistry):
        self.node_registry = node_registry

        # Caché para optimización
        self.score_cache: Dict[Tuple[str, str], NodeScore] = {}
        self.cache_ttl = timedelta(minutes=5)

        # Estadísticas de rendimiento
        self.stats = {
            'total_matchings': 0,
            'successful_matchings': 0,
            'average_execution_time_ms': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'nodes_processed': 0
        }

        # Estado de carga de nodos para balance
        self.node_load_state: Dict[str, int] = {}  # node_id -> current_sessions

    async def match_nodes_to_session(
        self,
        session: FederatedSession,
        required_nodes: Optional[int] = None,
        constraints: Optional[SessionConstraints] = None
    ) -> MatchingResult:
        """
        Asignar nodos a una sesión federada usando algoritmos avanzados de scoring

        Args:
            session: Sesión federada a la que asignar nodos
            required_nodes: Número de nodos requeridos (opcional, usa constraints si no se especifica)
            constraints: Restricciones adicionales (opcional, usa session.constraints si no se especifica)

        Returns:
            Resultado del matching con nodos asignados y métricas
        """
        start_time = time.time()

        # Usar constraints de sesión si no se proporcionan
        constraints = constraints or session.constraints
        required_nodes = required_nodes or constraints.min_nodes

        logger.info(f"🔍 Starting node matching for session {session.session_id}, "
                   f"requiring {required_nodes} nodes")

        try:
            # Obtener nodos candidatos del registry
            candidate_nodes = await self._get_candidate_nodes(session, constraints)

            if not candidate_nodes:
                logger.warning(f"No candidate nodes found for session {session.session_id}")
                return MatchingResult(session_id=session.session_id, execution_time_ms=0.0)

            # Calcular scores para todos los candidatos
            node_scores = await self._calculate_node_scores(session, candidate_nodes)

            # Aplicar algoritmo de matching optimizado
            matched_nodes, backup_nodes = await self._apply_optimized_matching(
                session, node_scores, required_nodes, constraints
            )

            # Calcular métricas adicionales
            diversity_score = self._calculate_diversity_score(matched_nodes, candidate_nodes)
            load_balance_score = self._calculate_load_balance_score(matched_nodes)

            # Actualizar estado de carga
            self._update_load_state(matched_nodes, backup_nodes)

            # Crear resultado
            result = MatchingResult(
                session_id=session.session_id,
                matched_nodes=matched_nodes,
                backup_nodes=backup_nodes,
                scores=node_scores,
                execution_time_ms=(time.time() - start_time) * 1000,
                diversity_score=diversity_score,
                load_balance_score=load_balance_score
            )

            # Actualizar estadísticas
            self._update_stats(result, len(candidate_nodes))

            # Notificar al coordinator (placeholder)
            await self._notify_coordinator(session, result)

            logger.info(f"✅ Matching completed for session {session.session_id}: "
                       f"{len(matched_nodes)}/{required_nodes} nodes matched "
                       f"(avg score: {result.average_score:.3f})")

            return result

        except Exception as e:
            logger.error(f"❌ Matching failed for session {session.session_id}: {e}")
            return MatchingResult(session_id=session.session_id, execution_time_ms=(time.time() - start_time) * 1000)

    def calculate_score(self, node: NodeRegistration, session: FederatedSession) -> NodeScore:
        """
        Calcular puntuación completa para un nodo según criterios ponderados

        Args:
            node: Registro del nodo a evaluar
            session: Sesión para la que calcular el score

        Returns:
            NodeScore con todos los componentes calculados
        """
        score = NodeScore(node_id=node.metadata.node_id, session_id=session.session_id)

        # 1. Capacidad computacional (40%)
        score.capacity_score = self._calculate_capacity_score(node.metadata)

        # 2. Latencia de red (30%) - inversa, menor latencia = mayor score
        estimated_latency = self._estimate_network_latency(node.metadata, session)
        score.estimated_latency_ms = estimated_latency
        score.latency_score = self._calculate_latency_score(estimated_latency, session.constraints.max_latency_ms)

        # 3. Reputación (30%)
        score.reputation_score = self._calculate_reputation_score(node.metadata)

        # Calcular score total ponderado
        score.total_score = (
            self.CAPACITY_WEIGHT * score.capacity_score +
            self.LATENCY_WEIGHT * score.latency_score +
            self.REPUTATION_WEIGHT * score.reputation_score
        )

        # Calcular score de compatibilidad adicional
        score.compatibility_score = self._calculate_compatibility_score(node.metadata, session)
        score.geographical_score = self._calculate_geographical_score(node.metadata, session)

        return score

    def _calculate_capacity_score(self, node_metadata: NodeMetadata) -> float:
        """Calcular score de capacidad computacional (0-1)"""
        hw_capacity = node_metadata.hardware_capacity

        # Extraer métricas de hardware
        cpu_cores = hw_capacity.get('cpu_cores', 1)
        ram_gb = hw_capacity.get('ram_gb', 4)
        gpu_count = hw_capacity.get('gpu_count', 0)

        # Normalizar y ponderar
        cpu_score = min(cpu_cores / 16.0, 1.0)  # Máximo razonable 16 cores
        ram_score = min(ram_gb / 64.0, 1.0)    # Máximo razonable 64GB
        gpu_score = min(gpu_count / 4.0, 1.0)  # Máximo razonable 4 GPUs

        # Score compuesto con pesos
        capacity_score = (
            cpu_score * 0.4 +
            ram_score * 0.4 +
            gpu_score * 0.2
        )

        return min(capacity_score, 1.0)

    def _calculate_latency_score(self, estimated_latency_ms: float, max_acceptable_latency: float) -> float:
        """Calcular score de latencia (0-1), menor latencia = mayor score"""
        if estimated_latency_ms <= 0:
            return 1.0  # Latencia perfecta

        # Score inversamente proporcional a la latencia
        # Score = 1 / (1 + latency/max_acceptable)
        normalized_latency = estimated_latency_ms / max_acceptable_latency
        latency_score = 1.0 / (1.0 + normalized_latency)

        return max(latency_score, 0.0)

    def _calculate_reputation_score(self, node_metadata: NodeMetadata) -> float:
        """Calcular score de reputación (0-1)"""
        # Usar el campo reputation_score directo, con validación
        reputation = max(0.0, min(1.0, node_metadata.reputation_score))

        # Bonus por tiempo activo (last_seen reciente)
        now = datetime.now()
        hours_since_seen = (now - node_metadata.last_seen).total_seconds() / 3600

        # Penalización por inactividad
        activity_penalty = min(hours_since_seen / 24.0, 0.3)  # Máx 30% penalty por 24h inactivo

        final_reputation = reputation * (1.0 - activity_penalty)

        return max(final_reputation, 0.0)

    def _estimate_network_latency(self, node_metadata: NodeMetadata, session: FederatedSession) -> float:
        """Estimar latencia de red en ms entre nodo y coordinator"""
        # Estimación simplificada basada en ubicación geográfica
        node_location = node_metadata.location or "unknown"
        coordinator_location = "Madrid, ES"  # Asumir coordinator en Madrid

        # Distancia aproximada en km
        distance_km = self._calculate_geographical_distance(node_location, coordinator_location)

        # Latencia base por distancia (aprox 1ms por 100km + jitter de red)
        base_latency = distance_km * 0.01  # 0.01ms por km

        # Jitter de red y factores adicionales
        network_jitter = random.uniform(5, 50)  # 5-50ms jitter típico
        congestion_factor = random.uniform(0.8, 1.2)  # Factor de congestión

        estimated_latency = (base_latency + network_jitter) * congestion_factor

        return max(estimated_latency, 1.0)  # Mínimo 1ms

    def _calculate_geographical_distance(self, loc1: str, loc2: str) -> float:
        """Calcular distancia aproximada entre ubicaciones en km"""
        if not loc1 or not loc2 or loc1 == loc2:
            return 0.0

        # Diccionario simplificado de distancias (ejemplo España)
        distances = {
            ("Madrid, ES", "Barcelona, ES"): 620,
            ("Madrid, ES", "Valencia, ES"): 350,
            ("Madrid, ES", "Sevilla, ES"): 390,
            ("Madrid, ES", "Bilbao, ES"): 400,
            ("Barcelona, ES", "Valencia, ES"): 340,
            ("Barcelona, ES", "Sevilla, ES"): 1000,
            ("Valencia, ES", "Sevilla, ES"): 650,
        }

        # Normalizar nombres de ubicación
        loc1_norm = loc1.lower().strip()
        loc2_norm = loc2.lower().strip()

        key = tuple(sorted([loc1_norm, loc2_norm]))
        return distances.get(key, 500)  # Distancia por defecto 500km

    def _calculate_compatibility_score(self, node_metadata: NodeMetadata, session: FederatedSession) -> float:
        """Calcular score de compatibilidad general"""
        score = 1.0

        # Verificar capacidades requeridas
        required_caps = set(session.constraints.required_capabilities)
        node_caps = set(node_metadata.capabilities)

        if not required_caps.issubset(node_caps):
            missing_caps = len(required_caps - node_caps)
            score -= missing_caps * 0.2  # Penalización por capacidad faltante

        # Verificar reputación mínima
        if node_metadata.reputation_score < session.constraints.min_reputation:
            score -= 0.3

        # Verificar región preferida
        if session.constraints.preferred_regions:
            node_region = self._extract_region_from_location(node_metadata.location)
            if node_region not in session.constraints.preferred_regions:
                score -= 0.1

        return max(score, 0.0)

    def _calculate_geographical_score(self, node_metadata: NodeMetadata, session: FederatedSession) -> float:
        """Calcular score geográfico para diversidad"""
        # Score basado en qué tan bien contribuye a la diversidad
        # Implementación simplificada - en producción analizar distribución actual
        return 0.8  # Placeholder

    async def _get_candidate_nodes(self, session: FederatedSession, constraints: SessionConstraints) -> List[NodeRegistration]:
        """Obtener nodos candidatos filtrados por constraints"""
        try:
            # Obtener todos los registros del registry
            all_registrations = await self.node_registry.discover_nodes()

            candidates = []
            for reg in all_registrations:
                meta = reg.metadata

                # Filtros básicos
                if meta.status != "active":
                    continue

                # Filtrar por reputación mínima
                if meta.reputation_score < constraints.min_reputation:
                    continue

                # Filtrar por capacidades requeridas
                if not set(constraints.required_capabilities).issubset(set(meta.capabilities)):
                    continue

                # Filtrar por carga actual (evitar sobrecarga)
                current_load = self.node_load_state.get(meta.node_id, 0)
                if current_load >= 5:  # Máximo 5 sesiones por nodo
                    continue

                candidates.append(reg)

            logger.debug(f"Found {len(candidates)} candidate nodes for session {session.session_id}")
            return candidates

        except Exception as e:
            logger.error(f"Failed to get candidate nodes: {e}")
            return []

    async def _calculate_node_scores(self, session: FederatedSession, nodes: List[NodeRegistration]) -> Dict[str, NodeScore]:
        """Calcular scores para múltiples nodos de forma optimizada"""
        scores = {}

        for node_reg in nodes:
            # Verificar caché
            cache_key = (node_reg.metadata.node_id, session.session_id)
            if cache_key in self.score_cache:
                # Verificar TTL
                cached_score = self.score_cache[cache_key]
                if (datetime.now() - cached_score.timestamp) < self.cache_ttl:
                    scores[node_reg.metadata.node_id] = cached_score
                    self.stats['cache_hits'] += 1
                    continue

            # Calcular score nuevo
            node_score = self.calculate_score(node_reg, session)
            node_score.timestamp = datetime.now()  # Agregar timestamp para caché

            scores[node_reg.metadata.node_id] = node_score
            self.score_cache[cache_key] = node_score
            self.stats['cache_misses'] += 1

        return scores

    async def _apply_optimized_matching(
        self,
        session: FederatedSession,
        node_scores: Dict[str, NodeScore],
        required_nodes: int,
        constraints: SessionConstraints
    ) -> Tuple[List[str], List[str]]:
        """Aplicar algoritmo de matching optimizado para miles de nodos"""

        # Convertir a lista para procesamiento
        score_list = list(node_scores.values())

        # Algoritmo optimizado: usar heap para top-k selection con constraints
        matched = []
        backup = []

        # Crear heap con scores (máximo heap usando negative scores)
        heap = []
        for score in score_list:
            heapq.heappush(heap, (-score.total_score, score.node_id, score))

        # Aplicar constraints de diversidad geográfica si requerido
        if constraints.geographical_diversity:
            matched, backup = self._select_with_geographical_diversity(
                heap, required_nodes, node_scores, constraints.max_nodes
            )
        else:
            # Selección greedy optimizada
            matched, backup = self._select_top_nodes(heap, required_nodes, constraints.max_nodes)

        return matched, backup

    def _select_top_nodes(self, score_heap: List, required: int, max_nodes: int) -> Tuple[List[str], List[str]]:
        """Seleccionar top nodes usando heap (eficiente para miles de nodos)"""
        matched = []
        backup = []

        target_matched = min(required, max_nodes)

        while score_heap and len(matched) < target_matched:
            neg_score, node_id, score = heapq.heappop(score_heap)
            matched.append(node_id)

        # Los siguientes como backup
        while score_heap and len(backup) < (max_nodes - target_matched):
            neg_score, node_id, score = heapq.heappop(score_heap)
            backup.append(node_id)

        return matched, backup

    def _select_with_geographical_diversity(
        self,
        score_heap: List,
        required: int,
        node_scores: Dict[str, NodeScore],
        max_nodes: int
    ) -> Tuple[List[str], List[str]]:
        """Seleccionar nodos con diversidad geográfica garantizada"""
        matched = []
        backup = []
        selected_regions = set()

        # Primera pasada: asegurar al menos un nodo por región importante
        region_heap = {}  # region -> [(score, node_id), ...]

        # Agrupar por región
        for neg_score, node_id, score in score_heap:
            # Extraer región del node_id o metadata (simplificado)
            region = self._extract_region_from_node_id(node_id)
            if region not in region_heap:
                region_heap[region] = []
            region_heap[region].append((neg_score, node_id, score))

        # Seleccionar mejor nodo por región primero
        for region, nodes_in_region in region_heap.items():
            if nodes_in_region:
                # Tomar el mejor de esta región
                best_in_region = min(nodes_in_region)  # min porque neg_score
                neg_score, node_id, score = best_in_region
                matched.append(node_id)
                selected_regions.add(region)

                if len(matched) >= required:
                    break

        # Segunda pasada: completar con mejores nodos restantes
        remaining_heap = []
        for neg_score, node_id, score in score_heap:
            if node_id not in matched:
                heapq.heappush(remaining_heap, (neg_score, node_id, score))

        while remaining_heap and len(matched) < max_nodes:
            neg_score, node_id, score = heapq.heappop(remaining_heap)
            if len(matched) < required:
                matched.append(node_id)
            else:
                backup.append(node_id)

        return matched, backup

    def _extract_region_from_node_id(self, node_id: str) -> str:
        """Extraer región del node_id (simplificado)"""
        # Lógica simplificada - en producción usar metadata de ubicación
        if "eu" in node_id.lower():
            return "EU"
        elif "us" in node_id.lower():
            return "US"
        elif "asia" in node_id.lower():
            return "ASIA"
        else:
            return "UNKNOWN"

    def _extract_region_from_location(self, location: str) -> str:
        """Extraer región de string de ubicación"""
        if not location:
            return "UNKNOWN"

        loc_lower = location.lower()
        if "es" in loc_lower or "spain" in loc_lower:
            return "EU"
        elif "us" in loc_lower or "usa" in loc_lower:
            return "US"
        elif "asia" in loc_lower:
            return "ASIA"
        else:
            return "UNKNOWN"

    def _calculate_diversity_score(self, matched_nodes: List[str], all_nodes: List[NodeRegistration]) -> float:
        """Calcular score de diversidad geográfica"""
        if not matched_nodes:
            return 0.0

        regions = set()
        for node_id in matched_nodes:
            region = self._extract_region_from_node_id(node_id)
            regions.add(region)

        # Score basado en número de regiones únicas
        diversity_score = len(regions) / 4.0  # Normalizar a 4 regiones posibles
        return min(diversity_score, 1.0)

    def _calculate_load_balance_score(self, matched_nodes: List[str]) -> float:
        """Calcular score de balance de carga"""
        if not matched_nodes:
            return 0.0

        loads = [self.node_load_state.get(node_id, 0) for node_id in matched_nodes]
        avg_load = sum(loads) / len(loads)

        # Score inversamente proporcional a la varianza de carga
        variance = sum((load - avg_load) ** 2 for load in loads) / len(loads)
        balance_score = 1.0 / (1.0 + variance)

        return balance_score

    def _update_load_state(self, matched_nodes: List[str], backup_nodes: List[str]):
        """Actualizar estado de carga de nodos"""
        for node_id in matched_nodes:
            self.node_load_state[node_id] = self.node_load_state.get(node_id, 0) + 1

        # Backup nodes también tienen carga ligera
        for node_id in backup_nodes:
            self.node_load_state[node_id] = self.node_load_state.get(node_id, 0) + 0.1

    def _update_stats(self, result: MatchingResult, nodes_processed: int):
        """Actualizar estadísticas de rendimiento"""
        self.stats['total_matchings'] += 1
        self.stats['nodes_processed'] += nodes_processed

        if result.success:
            self.stats['successful_matchings'] += 1

        # Actualizar tiempo promedio
        current_avg = self.stats['average_execution_time_ms']
        new_avg = (current_avg * (self.stats['total_matchings'] - 1) + result.execution_time_ms) / self.stats['total_matchings']
        self.stats['average_execution_time_ms'] = new_avg

    async def _notify_coordinator(self, session: FederatedSession, result: MatchingResult):
        """Notificar al coordinator sobre el resultado del matching (placeholder)"""
        # TODO: Implementar notificación WebSocket real al coordinator
        # Por ahora, solo log
        logger.debug(f"📡 Notifying coordinator {session.coordinator_node_id} "
                    f"about matching result for session {session.session_id}: "
                    f"{len(result.matched_nodes)} nodes matched")

        # Placeholder para integración WebSocket futura
        # await websocket_manager.send_to_coordinator(
        #     session.coordinator_node_id,
        #     {
        #         "type": "matching_result",
        #         "session_id": session.session_id,
        #         "matched_nodes": result.matched_nodes,
        #         "backup_nodes": result.backup_nodes,
        #         "average_score": result.average_score
        #     }
        # )

    async def get_fallback_nodes(self, session: FederatedSession, failed_nodes: List[str]) -> List[str]:
        """Obtener nodos de respaldo para reemplazar nodos fallidos"""
        try:
            # Obtener nodos backup disponibles
            backup_candidates = await self._get_candidate_nodes(session, session.constraints)

            # Filtrar nodos que no estén en failed_nodes y no sobrecargados
            available_backup = []
            for reg in backup_candidates:
                node_id = reg.metadata.node_id
                if (node_id not in failed_nodes and
                    self.node_load_state.get(node_id, 0) < 5):
                    available_backup.append(node_id)

            # Retornar hasta el número requerido
            return available_backup[:len(failed_nodes)]

        except Exception as e:
            logger.error(f"Failed to get fallback nodes: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del matcher"""
        success_rate = (self.stats['successful_matchings'] / self.stats['total_matchings']
                       if self.stats['total_matchings'] > 0 else 0.0)

        cache_hit_rate = (self.stats['cache_hits'] / (self.stats['cache_hits'] + self.stats['cache_misses'])
                         if (self.stats['cache_hits'] + self.stats['cache_misses']) > 0 else 0.0)

        return {
            'total_matchings': self.stats['total_matchings'],
            'successful_matchings': self.stats['successful_matchings'],
            'success_rate': f"{success_rate:.2%}",
            'average_execution_time_ms': f"{self.stats['average_execution_time_ms']:.2f}ms",
            'cache_size': len(self.score_cache),
            'cache_hit_rate': f"{cache_hit_rate:.2%}",
            'nodes_processed': self.stats['nodes_processed'],
            'active_load_managed_nodes': len(self.node_load_state)
        }

    def clear_cache(self):
        """Limpiar caché de scores"""
        self.score_cache.clear()
        logger.info("🧹 Session matcher cache cleared")


# Instancia global del matcher
_matcher_instance: Optional[SessionMatcher] = None

def get_session_matcher(node_registry: NodeRegistry) -> SessionMatcher:
    """Obtener instancia global del session matcher"""
    global _matcher_instance
    if _matcher_instance is None:
        _matcher_instance = SessionMatcher(node_registry)
    return _matcher_instance