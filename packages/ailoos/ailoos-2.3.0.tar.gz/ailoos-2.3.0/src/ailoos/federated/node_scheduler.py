"""
Node Scheduler - Planificador de Participación de Nodos
Gestiona la selección y planificación de nodos participantes en rondas federadas,
incluyendo algoritmos de selección, optimización, rotación y adaptación dinámica.
"""

import asyncio
import time
import random
import math
from typing import Dict, List, Any, Optional, Set, Tuple, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
import statistics

from ..core.logging import get_logger
from ..core.config import Config
try:
    from .node_registry import NodeRegistry, NodeEntry, NodeStatus, NodeCapabilities
except ImportError:
    # Fallback para desarrollo - definir tipos básicos
    NodeRegistry = None
    NodeEntry = None
    NodeStatus = None
    NodeCapabilities = None
try:
    from ..federated.session import FederatedSession
except ImportError:
    FederatedSession = None

# Integración con componentes avanzados
from ..coordinator.state_sync import StateSync, create_state_sync
from ..coordinator.consensus_manager import ConsensusManager, start_consensus_service
from ..coordinator.state_validator import StateValidator
from ..auditing.zk_auditor import ZKAuditor
from ..federated.p2p_protocol import P2PProtocol, create_p2p_protocol, PeerInfo
from ..federated.secure_aggregator import SecureAggregator, create_secure_aggregator
from ..rewards.dracma_manager import DRACMA_Manager

logger = get_logger(__name__)


class SelectionAlgorithm(Enum):
    """Algoritmos de selección de nodos disponibles."""
    RANDOM = "random"
    ROUND_ROBIN = "round_robin"
    WEIGHTED_RANDOM = "weighted_random"
    GREEDY_CAPACITY = "greedy_capacity"
    GENETIC_OPTIMIZATION = "genetic_optimization"
    REPUTATION_BASED = "reputation_based"
    LOAD_BALANCED = "load_balanced"
    DIVERSITY_OPTIMIZED = "diversity_optimized"


class OptimizationStrategy(Enum):
    """Estrategias de optimización para selección de nodos."""
    MAXIMIZE_CAPACITY = "maximize_capacity"
    BALANCE_LOAD = "balance_load"
    MAXIMIZE_DIVERSITY = "maximize_diversity"
    MINIMIZE_LATENCY = "minimize_latency"
    MAXIMIZE_RELIABILITY = "maximize_reliability"
    COST_OPTIMIZED = "cost_optimized"


@dataclass
class NodeMetrics:
    """Métricas de rendimiento de un nodo."""
    node_id: str
    computational_capacity: float = 0.0  # 0-1 scale
    memory_capacity: float = 0.0
    network_bandwidth: float = 0.0
    reputation_score: float = 0.5  # 0-1 scale
    availability_score: float = 1.0  # 0-1 scale
    current_load: float = 0.0  # 0-1 scale
    latency_ms: float = 0.0
    success_rate: float = 1.0  # 0-1 scale
    participation_count: int = 0
    last_participation: Optional[float] = None
    total_rewards_earned: float = 0.0
    geographic_location: Optional[str] = None
    hardware_specs: Dict[str, Any] = field(default_factory=dict)

    def get_overall_score(self, weights: Dict[str, float]) -> float:
        """Calcula puntuación general ponderada."""
        score = 0.0
        total_weight = sum(weights.values())

        if total_weight == 0:
            return 0.0

        for metric, weight in weights.items():
            if hasattr(self, metric):
                value = getattr(self, metric)
                score += value * weight

        return score / total_weight


@dataclass
class SelectionCriteria:
    """Criterios para selección de nodos."""
    min_participants: int = 3
    max_participants: int = 100
    required_capabilities: Set[str] = field(default_factory=set)
    min_reputation_score: float = 0.3
    min_availability_score: float = 0.8
    max_load_threshold: float = 0.8
    geographic_constraints: Optional[List[str]] = None
    exclude_nodes: Set[str] = field(default_factory=set)
    prefer_recent_participants: bool = False
    diversity_requirements: Optional[Dict[str, Any]] = None


@dataclass
class SchedulerConfig:
    """Configuración del planificador de nodos."""
    selection_algorithm: SelectionAlgorithm = SelectionAlgorithm.WEIGHTED_RANDOM
    optimization_strategy: OptimizationStrategy = OptimizationStrategy.BALANCE_LOAD
    rotation_enabled: bool = True
    rotation_interval_rounds: int = 5
    adaptation_enabled: bool = True
    adaptation_interval_seconds: int = 300
    metrics_update_interval: int = 60
    cache_ttl_seconds: int = 300
    max_concurrent_selections: int = 10


class BaseSelectionAlgorithm(ABC):
    """Clase base para algoritmos de selección."""

    def __init__(self, config: SchedulerConfig):
        self.config = config

    @abstractmethod
    async def select_nodes(self, available_nodes: List[NodeMetrics],
                          criteria: SelectionCriteria,
                          session_context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Selecciona nodos según el algoritmo específico."""
        pass

    def _filter_eligible_nodes(self, nodes: List[NodeMetrics],
                              criteria: SelectionCriteria) -> List[NodeMetrics]:
        """Filtra nodos elegibles según criterios."""
        eligible = []

        for node in nodes:
            if node.node_id in criteria.exclude_nodes:
                continue

            if node.reputation_score < criteria.min_reputation_score:
                continue

            if node.availability_score < criteria.min_availability_score:
                continue

            if node.current_load > criteria.max_load_threshold:
                continue

            # Verificar capacidades requeridas
            # TODO: Implementar verificación de capacidades desde NodeCapabilities

            # Verificar restricciones geográficas
            if criteria.geographic_constraints:
                if not node.geographic_location or \
                   node.geographic_location not in criteria.geographic_constraints:
                    continue

            eligible.append(node)

        return eligible


class RandomSelection(BaseSelectionAlgorithm):
    """Selección aleatoria de nodos."""

    async def select_nodes(self, available_nodes: List[NodeMetrics],
                          criteria: SelectionCriteria,
                          session_context: Optional[Dict[str, Any]] = None) -> List[str]:
        eligible = self._filter_eligible_nodes(available_nodes, criteria)
        if len(eligible) < criteria.min_participants:
            return []

        num_to_select = min(len(eligible), criteria.max_participants)
        selected = random.sample(eligible, num_to_select)
        return [node.node_id for node in selected]


class WeightedRandomSelection(BaseSelectionAlgorithm):
    """Selección aleatoria ponderada por capacidad y reputación."""

    async def select_nodes(self, available_nodes: List[NodeMetrics],
                          criteria: SelectionCriteria,
                          session_context: Optional[Dict[str, Any]] = None) -> List[str]:
        eligible = self._filter_eligible_nodes(available_nodes, criteria)
        if len(eligible) < criteria.min_participants:
            return []

        # Calcular pesos basados en capacidad y reputación
        weights = {}
        for node in eligible:
            # Peso = capacidad_computacional * 0.4 + reputación * 0.4 + disponibilidad * 0.2
            weight = (node.computational_capacity * 0.4 +
                     node.reputation_score * 0.4 +
                     node.availability_score * 0.2)
            weights[node.node_id] = max(weight, 0.1)  # Mínimo peso

        # Selección ponderada
        selected = []
        num_to_select = min(len(eligible), criteria.max_participants)

        for _ in range(num_to_select):
            if not weights:
                break

            # Seleccionar basado en pesos
            total_weight = sum(weights.values())
            pick = random.uniform(0, total_weight)

            current_weight = 0
            for node_id, weight in weights.items():
                current_weight += weight
                if pick <= current_weight:
                    selected.append(node_id)
                    del weights[node_id]
                    break

        return selected


class GreedyCapacitySelection(BaseSelectionAlgorithm):
    """Selección greedy maximizando capacidad total."""

    async def select_nodes(self, available_nodes: List[NodeMetrics],
                          criteria: SelectionCriteria,
                          session_context: Optional[Dict[str, Any]] = None) -> List[str]:
        eligible = self._filter_eligible_nodes(available_nodes, criteria)
        if len(eligible) < criteria.min_participants:
            return []

        # Ordenar por capacidad computacional descendente
        sorted_nodes = sorted(eligible,
                            key=lambda x: x.computational_capacity,
                            reverse=True)

        # Seleccionar los mejores hasta max_participants
        num_to_select = min(len(sorted_nodes), criteria.max_participants)
        selected = sorted_nodes[:num_to_select]

        return [node.node_id for node in selected]


class ReputationBasedSelection(BaseSelectionAlgorithm):
    """Selección basada en reputación y rendimiento histórico."""

    async def select_nodes(self, available_nodes: List[NodeMetrics],
                          criteria: SelectionCriteria,
                          session_context: Optional[Dict[str, Any]] = None) -> List[str]:
        eligible = self._filter_eligible_nodes(available_nodes, criteria)
        if len(eligible) < criteria.min_participants:
            return []

        # Calcular puntuación compuesta: reputación + tasa de éxito + participación reciente
        scored_nodes = []
        current_time = time.time()

        for node in eligible:
            # Factor de recencia (más reciente = mejor)
            recency_factor = 1.0
            if node.last_participation:
                days_since_last = (current_time - node.last_participation) / (24 * 3600)
                recency_factor = max(0.1, math.exp(-days_since_last / 30))  # Decaimiento en 30 días

            # Puntuación total
            total_score = (
                node.reputation_score * 0.5 +
                node.success_rate * 0.3 +
                recency_factor * 0.2
            )

            scored_nodes.append((node, total_score))

        # Ordenar por puntuación descendente
        scored_nodes.sort(key=lambda x: x[1], reverse=True)

        # Seleccionar los mejores
        num_to_select = min(len(scored_nodes), criteria.max_participants)
        selected = [node for node, score in scored_nodes[:num_to_select]]

        return [node.node_id for node in selected]


class LoadBalancedSelection(BaseSelectionAlgorithm):
    """Selección que balancea la carga entre nodos."""

    async def select_nodes(self, available_nodes: List[NodeMetrics],
                          criteria: SelectionCriteria,
                          session_context: Optional[Dict[str, Any]] = None) -> List[str]:
        eligible = self._filter_eligible_nodes(available_nodes, criteria)
        if len(eligible) < criteria.min_participants:
            return []

        # Ordenar por carga actual ascendente (menos cargados primero)
        sorted_nodes = sorted(eligible, key=lambda x: x.current_load)

        # Seleccionar hasta max_participants, priorizando menos cargados
        num_to_select = min(len(sorted_nodes), criteria.max_participants)
        selected = sorted_nodes[:num_to_select]

        return [node.node_id for node in selected]


class DiversityOptimizedSelection(BaseSelectionAlgorithm):
    """Selección optimizada para diversidad geográfica y de capacidades."""

    async def select_nodes(self, available_nodes: List[NodeMetrics],
                          criteria: SelectionCriteria,
                          session_context: Optional[Dict[str, Any]] = None) -> List[str]:
        eligible = self._filter_eligible_nodes(available_nodes, criteria)
        if len(eligible) < criteria.min_participants:
            return []

        selected = []
        remaining = eligible.copy()

        # Seleccionar primero nodos de diferentes ubicaciones geográficas
        if criteria.diversity_requirements and 'geographic' in criteria.diversity_requirements:
            geographic_diversity = criteria.diversity_requirements['geographic']
            locations_selected = set()

            # Primera pasada: asegurar diversidad geográfica
            for node in remaining:
                if node.geographic_location and node.geographic_location not in locations_selected:
                    selected.append(node)
                    locations_selected.add(node.geographic_location)
                    remaining.remove(node)

                    if len(selected) >= criteria.max_participants:
                        break

        # Segunda pasada: completar con nodos de mejor reputación
        if len(selected) < criteria.max_participants and remaining:
            remaining_sorted = sorted(remaining,
                                    key=lambda x: x.reputation_score,
                                    reverse=True)
            needed = criteria.max_participants - len(selected)
            selected.extend(remaining_sorted[:needed])

        return [node.node_id for node in selected]


class NodeScheduler:
    """
    Planificador de participación de nodos en rondas federadas.

    Gestiona la selección inteligente de nodos participantes considerando:
    - Capacidad computacional
    - Reputación y fiabilidad
    - Disponibilidad y carga actual
    - Estrategias de optimización
    - Rotación de nodos
    - Adaptación dinámica a cambios en la red
    """

    def __init__(self, node_registry: NodeRegistry, config: Optional[SchedulerConfig] = None, session_id: str = None):
        self.node_registry = node_registry
        self.config = config or SchedulerConfig()
        self.session_id = session_id or "default_session"

        # Componentes de integración avanzada
        self.state_sync: Optional[StateSync] = None
        self.consensus_manager: Optional[ConsensusManager] = None
        self.state_validator: Optional[StateValidator] = None
        self.zk_auditor: Optional[ZKAuditor] = None
        self.p2p_protocol: Optional[P2PProtocol] = None
        self.secure_aggregator: Optional[SecureAggregator] = None
        self.dracma_manager: Optional[DRACMA_Manager] = None

        # Algoritmos de selección disponibles
        self.algorithms = {
            SelectionAlgorithm.RANDOM: RandomSelection(self.config),
            SelectionAlgorithm.WEIGHTED_RANDOM: WeightedRandomSelection(self.config),
            SelectionAlgorithm.GREEDY_CAPACITY: GreedyCapacitySelection(self.config),
            SelectionAlgorithm.REPUTATION_BASED: ReputationBasedSelection(self.config),
            SelectionAlgorithm.LOAD_BALANCED: LoadBalancedSelection(self.config),
            SelectionAlgorithm.DIVERSITY_OPTIMIZED: DiversityOptimizedSelection(self.config),
        }

        # Estado del planificador
        self.node_metrics: Dict[str, NodeMetrics] = {}
        self.metrics_cache: Dict[str, float] = {}  # node_id -> timestamp
        self.round_participants_history: List[Set[str]] = []
        self.rotation_counter = 0

        # Control de concurrencia
        self.selection_lock = asyncio.Lock()
        self.metrics_lock = asyncio.Lock()

        # Tareas de fondo
        self.adaptation_task: Optional[asyncio.Task] = None
        self.metrics_update_task: Optional[asyncio.Task] = None
        self.is_running = False

        # Callbacks de eventos
        self.event_callbacks: Dict[str, List[Callable]] = {
            'nodes_selected': [],
            'metrics_updated': [],
            'rotation_triggered': [],
            'adaptation_applied': []
        }

        logger.info("🎯 NodeScheduler initialized")

        # Inicializar componentes avanzados si están disponibles
        self._initialize_advanced_components()

    async def start(self):
        """Inicia el planificador de nodos."""
        if self.is_running:
            return

        self.is_running = True
        logger.info("🚀 Starting NodeScheduler")

        # Iniciar tareas de fondo
        if self.config.adaptation_enabled:
            self.adaptation_task = asyncio.create_task(self._adaptation_loop())

        self.metrics_update_task = asyncio.create_task(self._metrics_update_loop())

    async def stop(self):
        """Detiene el planificador de nodos."""
        self.is_running = False

        if self.adaptation_task:
            self.adaptation_task.cancel()
            try:
                await self.adaptation_task
            except asyncio.CancelledError:
                pass

        if self.metrics_update_task:
            self.metrics_update_task.cancel()
            try:
                await self.metrics_update_task
            except asyncio.CancelledError:
                pass

        # Detener componentes avanzados
        if self.p2p_protocol:
            await self.p2p_protocol.stop()

        if self.state_sync:
            await self.state_sync.stop_sync_service()

        if self.consensus_manager:
            await self.consensus_manager.stop_consensus_service()

        # Otros componentes no tienen shutdown específico

        logger.info("🛑 NodeScheduler stopped")

    def _initialize_advanced_components(self):
        """Inicializar componentes avanzados de integración."""
        try:
            # Inicializar sincronización de estado
            self.state_sync = create_state_sync(f"scheduler_{self.session_id}")
            asyncio.create_task(self.state_sync.start_sync_service())

            # Inicializar gestor de consenso
            self.consensus_manager = ConsensusManager(
                node_id=f"scheduler_{self.session_id}",
                total_nodes=50,
                consensus_timeout=30
            )
            asyncio.create_task(self.consensus_manager.start_consensus_service())

            # Inicializar validador de estado
            self.state_validator = StateValidator(self.config)

            # Inicializar auditor ZKP
            self.zk_auditor = ZKAuditor(self.config)

            # Inicializar protocolo P2P
            self.p2p_protocol = create_p2p_protocol(
                node_id=f"scheduler_{self.session_id}",
                host="0.0.0.0",
                port=8445  # Puerto diferente
            )
            asyncio.create_task(self.p2p_protocol.start())

            # Inicializar agregador seguro
            self.secure_aggregator = create_secure_aggregator(
                session_id=self.session_id,
                model_name="scheduler_aggregator",
                config=self.config
            )

            # Inicializar sistema de recompensas
            self.dracma_manager = DRACMA_Manager(self.config)

            logger.info("✅ Advanced components initialized in NodeScheduler")

        except Exception as e:
            logger.warning(f"⚠️ Some advanced components failed to initialize: {e}")

    async def select_round_participants(self, criteria: SelectionCriteria,
                                      session_context: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Selecciona participantes para una ronda federada.

        Args:
            criteria: Criterios de selección
            session_context: Contexto de la sesión federada

        Returns:
            Lista de IDs de nodos seleccionados
        """
        async with self.selection_lock:
            try:
                # Obtener métricas actualizadas de nodos disponibles
                available_nodes = await self._get_available_node_metrics()

                if len(available_nodes) < criteria.min_participants:
                    logger.warning(f"Insufficient available nodes: {len(available_nodes)} < {criteria.min_participants}")
                    return []

                # Aplicar algoritmo de selección
                algorithm = self.algorithms.get(self.config.selection_algorithm)
                if not algorithm:
                    logger.error(f"Unknown selection algorithm: {self.config.selection_algorithm}")
                    return []

                selected_node_ids = await algorithm.select_nodes(
                    available_nodes, criteria, session_context
                )

                if len(selected_node_ids) < criteria.min_participants:
                    logger.warning(f"Selection algorithm returned insufficient nodes: {len(selected_node_ids)}")
                    return []

                # Aplicar rotación si está habilitada
                if self.config.rotation_enabled:
                    selected_node_ids = await self._apply_rotation(selected_node_ids, criteria)

                # Validar selección con consenso si disponible
                if self.consensus_manager and len(selected_node_ids) > 0:
                    consensus_approved = await self._validate_selection_with_consensus(selected_node_ids, criteria)
                    if not consensus_approved:
                        logger.warning("⚠️ Node selection rejected by consensus")
                        return []

                # Registrar selección para historia
                self.round_participants_history.append(set(selected_node_ids))
                if len(self.round_participants_history) > 10:  # Mantener últimas 10 rondas
                    self.round_participants_history.pop(0)

                # Sincronizar selección con peers si disponible
                if self.state_sync:
                    await self._sync_selection_state(selected_node_ids, criteria)

                # Trigger callbacks
                await self._trigger_callbacks('nodes_selected', selected_node_ids, criteria)

                logger.info(f"✅ Selected {len(selected_node_ids)} nodes for round: {selected_node_ids}")
                return selected_node_ids

            except Exception as e:
                logger.error(f"❌ Error selecting round participants: {e}")
                return []

    async def _get_available_node_metrics(self) -> List[NodeMetrics]:
        """Obtiene métricas de nodos disponibles."""
        try:
            # Obtener nodos activos del registro
            active_nodes = await self.node_registry.list_nodes(
                filters={'status': NodeStatus.ACTIVE.value}
            )

            available_metrics = []
            for node_entry in active_nodes:
                # Obtener o crear métricas para este nodo
                metrics = await self._get_node_metrics(node_entry.node_id, node_entry)
                if metrics:
                    available_metrics.append(metrics)

            return available_metrics

        except Exception as e:
            logger.error(f"Error getting available node metrics: {e}")
            return []

    async def _get_node_metrics(self, node_id: str, node_entry: Optional[NodeEntry] = None) -> Optional[NodeMetrics]:
        """Obtiene métricas para un nodo específico."""
        async with self.metrics_lock:
            # Verificar cache
            cache_time = self.metrics_cache.get(node_id, 0)
            if time.time() - cache_time < self.config.cache_ttl_seconds:
                return self.node_metrics.get(node_id)

            # Obtener información del nodo
            if not node_entry:
                node_entry = await self.node_registry.get_node(node_id)
                if not node_entry:
                    return None

            # Calcular métricas desde la información del registro
            metrics = await self._calculate_node_metrics(node_entry)
            if metrics:
                self.node_metrics[node_id] = metrics
                self.metrics_cache[node_id] = time.time()

            return metrics

    async def _calculate_node_metrics(self, node_entry: NodeEntry) -> NodeMetrics:
        """Calcula métricas para un nodo basado en su entrada de registro."""
        try:
            # Extraer información de hardware
            hardware = node_entry.hardware_specs
            cpu_cores = hardware.get('cpu_cores', 1)
            memory_gb = hardware.get('memory_gb', 1)

            # Estimar capacidad computacional (0-1 scale)
            # Normalizar basado en núcleos y memoria
            comp_capacity = min(1.0, (cpu_cores / 16.0) * 0.7 + (memory_gb / 32.0) * 0.3)

            # Estimar capacidad de memoria
            mem_capacity = min(1.0, memory_gb / 64.0)  # 64GB como máximo razonable

            # Estimar ancho de banda de red (simplificado)
            network_capacity = 0.5  # Valor por defecto, podría mejorarse con datos reales

            # Calcular reputación basada en estado y tiempo de registro
            reputation = 0.5  # Base
            if node_entry.status == NodeStatus.ACTIVE:
                reputation += 0.3
            # Podría mejorarse con datos históricos de rendimiento

            # Calcular disponibilidad (simplificada)
            availability = 0.9 if node_entry.status == NodeStatus.ACTIVE else 0.1

            # Carga actual (estimada, podría mejorarse con monitoreo real)
            current_load = 0.2  # Valor conservador por defecto

            # Métricas existentes o por defecto
            existing = self.node_metrics.get(node_entry.node_id)
            participation_count = existing.participation_count if existing else 0
            last_participation = existing.last_participation if existing else None
            total_rewards = existing.total_rewards_earned if existing else 0.0

            return NodeMetrics(
                node_id=node_entry.node_id,
                computational_capacity=comp_capacity,
                memory_capacity=mem_capacity,
                network_bandwidth=network_capacity,
                reputation_score=reputation,
                availability_score=availability,
                current_load=current_load,
                geographic_location=node_entry.location,
                hardware_specs=node_entry.hardware_specs,
                participation_count=participation_count,
                last_participation=last_participation,
                total_rewards_earned=total_rewards
            )

        except Exception as e:
            logger.error(f"Error calculating metrics for node {node_entry.node_id}: {e}")
            return None

    async def _apply_rotation(self, selected_nodes: List[str], criteria: SelectionCriteria) -> List[str]:
        """Aplica rotación de nodos si está habilitada."""
        if not self.config.rotation_enabled or not self.round_participants_history:
            return selected_nodes

        self.rotation_counter += 1

        # Aplicar rotación cada N rondas
        if self.rotation_counter % self.config.rotation_interval_rounds == 0:
            try:
                # Obtener nodos de rondas anteriores
                recent_participants = set()
                for participants in self.round_participants_history[-3:]:  # Últimas 3 rondas
                    recent_participants.update(participants)

                # Encontrar nodos alternativos con buena reputación
                alternative_nodes = []
                for node_id in selected_nodes:
                    if node_id in recent_participants:
                        # Buscar reemplazo
                        metrics = self.node_metrics.get(node_id)
                        if metrics and metrics.reputation_score > 0.7:
                            # Buscar nodos no recientes con reputación similar
                            candidates = [
                                nid for nid, m in self.node_metrics.items()
                                if nid not in recent_participants and
                                m.reputation_score >= metrics.reputation_score * 0.9 and
                                nid not in selected_nodes
                            ]
                            if candidates:
                                alternative = random.choice(candidates)
                                alternative_nodes.append((node_id, alternative))

                # Aplicar rotaciones
                for old_node, new_node in alternative_nodes[:2]:  # Máximo 2 rotaciones por ronda
                    selected_nodes.remove(old_node)
                    selected_nodes.append(new_node)
                    logger.info(f"🔄 Rotated node {old_node} -> {new_node}")

                await self._trigger_callbacks('rotation_triggered', selected_nodes)

            except Exception as e:
                logger.error(f"Error applying rotation: {e}")

        return selected_nodes

    async def update_node_performance(self, node_id: str, performance_data: Dict[str, Any]):
        """Actualiza métricas de rendimiento de un nodo."""
        async with self.metrics_lock:
            metrics = self.node_metrics.get(node_id)
            if not metrics:
                # Crear métricas básicas si no existen
                metrics = NodeMetrics(node_id=node_id)
                self.node_metrics[node_id] = metrics

            # Actualizar métricas basadas en datos de rendimiento
            if 'success' in performance_data:
                success = performance_data['success']
                # Actualizar tasa de éxito usando media móvil
                metrics.success_rate = (metrics.success_rate * 0.9) + (success * 0.1)

            if 'latency' in performance_data:
                metrics.latency_ms = performance_data['latency']

            if 'rewards' in performance_data:
                metrics.total_rewards_earned += performance_data['rewards']

            # Actualizar participación
            metrics.participation_count += 1
            metrics.last_participation = time.time()

            # Ajustar reputación basada en rendimiento
            if success:
                metrics.reputation_score = min(1.0, metrics.reputation_score + 0.01)
            else:
                metrics.reputation_score = max(0.0, metrics.reputation_score - 0.05)

            # Actualizar carga (estimada)
            metrics.current_load = min(1.0, metrics.current_load + 0.1)

            # Invalidar cache
            self.metrics_cache[node_id] = 0

            await self._trigger_callbacks('metrics_updated', node_id, metrics)

    async def _validate_selection_with_consensus(self, selected_nodes: List[str], criteria: SelectionCriteria) -> bool:
        """Validar selección de nodos con consenso."""
        try:
            if not self.consensus_manager:
                return True

            # Crear propuesta de consenso para la selección
            proposal_data = {
                'operation': 'node_selection',
                'selected_nodes': selected_nodes,
                'criteria': criteria.__dict__,
                'session_id': self.session_id,
                'timestamp': time.time()
            }

            # Intentar alcanzar consenso
            consensus_result = await self.consensus_manager.propose_operation(
                operation='node_selection',
                data=proposal_data,
                timeout=30
            )

            return consensus_result['accepted']

        except Exception as e:
            logger.error(f"❌ Error validating selection with consensus: {e}")
            return False

    async def _sync_selection_state(self, selected_nodes: List[str], criteria: SelectionCriteria):
        """Sincronizar estado de selección con peers."""
        try:
            if not self.state_sync:
                return

            # Actualizar estado local
            selection_state = {
                'selected_nodes': selected_nodes,
                'criteria': criteria.__dict__,
                'timestamp': time.time(),
                'session_id': self.session_id
            }

            self.state_sync.update_local_state('node_selection', selection_state)

        except Exception as e:
            logger.error(f"❌ Error syncing selection state: {e}")

    async def _adaptation_loop(self):
        """Loop de adaptación dinámica."""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.adaptation_interval_seconds)

                # Analizar rendimiento reciente
                await self._analyze_recent_performance()

                # Adaptar algoritmo de selección basado en rendimiento
                await self._adapt_selection_algorithm()

                await self._trigger_callbacks('adaptation_applied')

            except Exception as e:
                logger.error(f"Error in adaptation loop: {e}")
                await asyncio.sleep(60)

    async def _analyze_recent_performance(self):
        """Analiza el rendimiento reciente para adaptación."""
        # Implementación simplificada - en producción sería más sofisticada
        if len(self.round_participants_history) < 3:
            return

        # Calcular métricas de diversidad y estabilidad
        recent_rounds = self.round_participants_history[-5:]
        avg_participants = statistics.mean(len(r) for r in recent_rounds)

        # Calcular estabilidad (overlap entre rondas consecutivas)
        stability_scores = []
        for i in range(1, len(recent_rounds)):
            prev = recent_rounds[i-1]
            curr = recent_rounds[i]
            overlap = len(prev.intersection(curr))
            stability = overlap / len(prev.union(curr)) if prev.union(curr) else 0
            stability_scores.append(stability)

        avg_stability = statistics.mean(stability_scores) if stability_scores else 0

        logger.debug(f"📊 Performance analysis: avg_participants={avg_participants:.1f}, stability={avg_stability:.2f}")

    async def _adapt_selection_algorithm(self):
        """Adapta el algoritmo de selección basado en análisis de rendimiento."""
        # Lógica simplificada de adaptación
        # En producción, esto sería más complejo con ML

        if len(self.round_participants_history) < 5:
            return

        # Si estabilidad es muy baja, cambiar a algoritmo más diverso
        recent_stability = await self._calculate_recent_stability()

        if recent_stability < 0.3 and self.config.selection_algorithm == SelectionAlgorithm.WEIGHTED_RANDOM:
            self.config.selection_algorithm = SelectionAlgorithm.DIVERSITY_OPTIMIZED
            logger.info("🔄 Adapted to diversity-optimized selection due to low stability")

        elif recent_stability > 0.8 and self.config.selection_algorithm == SelectionAlgorithm.DIVERSITY_OPTIMIZED:
            self.config.selection_algorithm = SelectionAlgorithm.REPUTATION_BASED
            logger.info("🔄 Adapted to reputation-based selection due to high stability")

    async def _calculate_recent_stability(self) -> float:
        """Calcula estabilidad reciente de selecciones."""
        if len(self.round_participants_history) < 2:
            return 0.0

        recent = self.round_participants_history[-3:]
        stability_scores = []

        for i in range(1, len(recent)):
            prev = recent[i-1]
            curr = recent[i]
            overlap = len(prev.intersection(curr))
            union_size = len(prev.union(curr))
            stability = overlap / union_size if union_size > 0 else 0
            stability_scores.append(stability)

        return statistics.mean(stability_scores) if stability_scores else 0.0

    async def _metrics_update_loop(self):
        """Loop de actualización periódica de métricas."""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.metrics_update_interval)

                # Actualizar métricas de carga (simulación)
                await self._update_load_metrics()

            except Exception as e:
                logger.error(f"Error in metrics update loop: {e}")
                await asyncio.sleep(30)

    async def _update_load_metrics(self):
        """Actualiza métricas de carga de nodos."""
        async with self.metrics_lock:
            for node_id, metrics in self.node_metrics.items():
                # Simular reducción gradual de carga
                metrics.current_load = max(0.0, metrics.current_load - 0.05)

                # Simular recuperación de disponibilidad
                if metrics.availability_score < 1.0:
                    metrics.availability_score = min(1.0, metrics.availability_score + 0.01)

    def register_callback(self, event: str, callback: Callable):
        """Registra callback para evento."""
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)

    async def _trigger_callbacks(self, event: str, *args, **kwargs):
        """Dispara callbacks para un evento."""
        for callback in self.event_callbacks[event]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in callback for {event}: {e}")

    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del planificador."""
        return {
            'algorithm': self.config.selection_algorithm.value,
            'optimization_strategy': self.config.optimization_strategy.value,
            'rotation_enabled': self.config.rotation_enabled,
            'rotation_counter': self.rotation_counter,
            'adaptation_enabled': self.config.adaptation_enabled,
            'tracked_nodes': len(self.node_metrics),
            'rounds_tracked': len(self.round_participants_history),
            'is_running': self.is_running
        }


# Funciones de conveniencia

def create_node_scheduler(node_registry: Optional[NodeRegistry] = None,
                         config: Optional[SchedulerConfig] = None) -> NodeScheduler:
    """
    Crea una instancia del planificador de nodos.

    Args:
        node_registry: Registro de nodos (opcional, puede inicializarse después)
        config: Configuración del planificador

    Returns:
        NodeScheduler: Instancia del planificador
    """
    return NodeScheduler(node_registry, config)


async def initialize_node_scheduler(scheduler: NodeScheduler) -> bool:
    """
    Inicializa el planificador de nodos.

    Args:
        scheduler: Instancia del planificador

    Returns:
        bool: True si se inicializó correctamente
    """
    try:
        await scheduler.start()
        return True
    except Exception as e:
        logger.error(f"Failed to initialize node scheduler: {e}")
        return False


async def select_federated_participants(scheduler: NodeScheduler,
                                      criteria: SelectionCriteria,
                                      session_context: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Función de conveniencia para seleccionar participantes federados.

    Args:
        scheduler: Planificador de nodos
        criteria: Criterios de selección
        session_context: Contexto de sesión

    Returns:
        Lista de IDs de nodos seleccionados
    """
    return await scheduler.select_round_participants(criteria, session_context)


# ==================== EJEMPLOS DE USO ====================

"""
Ejemplos de uso del NodeScheduler:

1. Selección básica con criterios simples:
```python
from ailoos.federated.node_scheduler import (
    create_node_scheduler, SelectionCriteria, SchedulerConfig,
    SelectionAlgorithm
)

# Crear planificador
scheduler = create_node_scheduler(node_registry=my_registry)

# Configurar criterios de selección
criteria = SelectionCriteria(
    min_participants=5,
    max_participants=20,
    min_reputation_score=0.7,
    max_load_threshold=0.8
)

# Seleccionar nodos
selected_nodes = await scheduler.select_round_participants(criteria)
```

2. Selección con diversidad geográfica:
```python
criteria = SelectionCriteria(
    min_participants=10,
    max_participants=15,
    geographic_constraints=['EU', 'US', 'ASIA'],
    diversity_requirements={
        'geographic': True,
        'min_regions': 3
    }
)
```

3. Configuración personalizada del planificador:
```python
config = SchedulerConfig(
    selection_algorithm=SelectionAlgorithm.REPUTATION_BASED,
    optimization_strategy=OptimizationStrategy.MAXIMIZE_DIVERSITY,
    rotation_enabled=True,
    adaptation_enabled=True
)

scheduler = create_node_scheduler(node_registry, config)
```

4. Integración con RoundOrchestrator:
```python
# El RoundOrchestrator ahora incluye automáticamente el NodeScheduler
orchestrator = create_round_orchestrator(session_id, config)

# Crear ronda - automáticamente selecciona nodos óptimos
round_id = await orchestrator.create_round()  # Sin participantes especificados
```

5. Actualización de métricas de rendimiento:
```python
# Después de completar una contribución exitosa
await scheduler.update_node_performance(
    node_id="node_123",
    performance_data={
        'success': True,
        'latency': 150.5,  # ms
        'rewards': 0.05    # DRACMA
    }
)
```

6. Monitoreo y estadísticas:
```python
# Obtener estadísticas del planificador
stats = scheduler.get_scheduler_stats()
print(f"Algoritmo activo: {stats['algorithm']}")
print(f"Nodos rastreados: {stats['tracked_nodes']}")
print(f"Rotación activada: {stats['rotation_enabled']}")
```
"""