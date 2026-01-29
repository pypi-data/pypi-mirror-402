"""
Round Orchestrator - Orquestador de Rondas Federadas
Gestiona el ciclo completo de rondas de entrenamiento federado, incluyendo
coordinación de nodos, timeouts, recopilación de contribuciones, validación,
y escalado dinámico.
"""

import asyncio
import time
import uuid
import torch
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import threading

from ..core.logging import get_logger
from ..core.config import Config
from .session import FederatedSession
from ..verification.zkp_engine import ZKPEngine, create_zkp_engine
from ..coordinator.state_sync import StateSync, create_state_sync
from ..coordinator.consensus_manager import ConsensusManager, start_consensus_service
from ..coordinator.state_validator import StateValidator
from ..auditing.zk_auditor import ZKAuditor
from ..federated.p2p_protocol import P2PProtocol, create_p2p_protocol, PeerInfo
from ..federated.secure_aggregator import SecureAggregator, create_secure_aggregator, encrypt_model_weights
from ..federated.node_scheduler import NodeScheduler, create_node_scheduler, SelectionCriteria, SchedulerConfig
from ..rewards.dracma_manager import DRACMA_Manager
from ..marketplace.price_oracle import price_oracle

logger = get_logger(__name__)


class RoundPhase(Enum):
    """Fases de una ronda federada."""
    INITIALIZING = "initializing"
    COORDINATING = "coordinating"
    COLLECTING = "collecting"
    VALIDATING = "validating"
    AGGREGATING = "aggregating"
    DISTRIBUTING = "distributing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class RoundStatus(Enum):
    """Estados posibles de una ronda."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NodeParticipationStatus(Enum):
    """Estados de participación de nodos en una ronda."""
    INVITED = "invited"
    ACCEPTED = "accepted"
    CONTRIBUTING = "contributing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    DISCONNECTED = "disconnected"


@dataclass
class RoundConfig:
    """Configuración para una ronda federada."""
    round_timeout: int = 1800  # 30 minutos
    node_timeout: int = 300    # 5 minutos por nodo
    min_participants: int = 3
    max_participants: int = 100
    consensus_threshold: float = 0.67  # 67% para consenso
    enable_zkp_validation: bool = True
    enable_secure_aggregation: bool = True
    reward_distribution_enabled: bool = True
    allow_dynamic_scaling: bool = True
    max_concurrent_rounds: int = 5


@dataclass
class NodeParticipation:
    """Información de participación de un nodo en una ronda."""
    node_id: str
    status: NodeParticipationStatus = NodeParticipationStatus.INVITED
    invited_at: float = field(default_factory=time.time)
    accepted_at: Optional[float] = None
    contributed_at: Optional[float] = None
    completed_at: Optional[float] = None
    contribution: Optional[Dict[str, Any]] = None
    zkp_proof: Optional[Any] = None
    reward_earned: float = 0.0
    failure_reason: Optional[str] = None
    reconnection_attempts: int = 0
    max_reconnection_attempts: int = 3


@dataclass
class RoundState:
    """Estado completo de una ronda federada."""
    round_id: str
    session_id: str
    round_number: int
    phase: RoundPhase = RoundPhase.INITIALIZING
    status: RoundStatus = RoundStatus.PENDING
    config: RoundConfig = field(default_factory=RoundConfig)

    # Temporización
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    deadline: Optional[float] = None

    # Participantes
    expected_participants: List[str] = field(default_factory=list)
    participants: Dict[str, NodeParticipation] = field(default_factory=dict)
    active_participants: Set[str] = field(default_factory=set)
    completed_participants: Set[str] = field(default_factory=set)
    failed_participants: Set[str] = field(default_factory=set)

    # Datos de la ronda
    global_model_cid: str = ""
    aggregated_weights: Optional[Dict[str, Any]] = None
    contributions: List[Dict[str, Any]] = field(default_factory=list)
    validation_results: Dict[str, Any] = field(default_factory=dict)

    # Métricas y estadísticas
    total_contributions: int = 0
    valid_contributions: int = 0
    consensus_reached: bool = False
    rewards_distributed: float = 0.0

    # Control de concurrencia
    lock: threading.RLock = field(default_factory=threading.RLock)

    def can_start(self) -> bool:
        """Verificar si la ronda puede comenzar."""
        return (
            len(self.active_participants) >= self.config.min_participants and
            self.status == RoundStatus.PENDING
        )

    def is_complete(self) -> bool:
        """Verificar si la ronda está completa."""
        return self.status in [RoundStatus.COMPLETED, RoundStatus.FAILED, RoundStatus.CANCELLED]

    def get_progress_percentage(self) -> float:
        """Obtener porcentaje de progreso de la ronda."""
        if not self.expected_participants:
            return 0.0
        return (len(self.completed_participants) / len(self.expected_participants)) * 100.0

    def get_time_remaining(self) -> Optional[float]:
        """Obtener tiempo restante antes del timeout."""
        if not self.deadline:
            return None
        return max(0, self.deadline - time.time())


class RoundOrchestrator:
    """
    Orquestador de rondas federadas que gestiona el ciclo completo de entrenamiento,
    incluyendo coordinación de nodos, timeouts, recopilación de contribuciones,
    validación y escalado dinámico.
    """

    def __init__(self, session_id: str, config: Optional[Config] = None):
        self.session_id = session_id
        self.config = config or Config()

        # Estado de rondas
        self.active_rounds: Dict[str, RoundState] = {}
        self.completed_rounds: List[RoundState] = []
        self.current_round_number = 0

        # Componentes principales
        self.session: Optional[FederatedSession] = None
        self.p2p_protocol: Optional[P2PProtocol] = None
        self.zkp_engine: Optional[ZKPEngine] = None
        self.secure_aggregator: Optional[SecureAggregator] = None
        self.dracma_manager: Optional[DRACMA_Manager] = None
        self.node_scheduler: Optional[NodeScheduler] = None

        # Componentes de sincronización y validación
        self.state_sync: Optional[StateSync] = None
        self.consensus_manager: Optional[ConsensusManager] = None
        self.state_validator: Optional[StateValidator] = None
        self.zk_auditor: Optional[ZKAuditor] = None

        # Sistema de auto-healing
        self.auto_healing_coordinator: Optional[Any] = None

        # Configuración por defecto
        self.default_round_config = RoundConfig()

        # Control de concurrencia
        self.round_lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=10)

        # Callbacks de eventos
        self.event_callbacks: Dict[str, List[Callable]] = {
            'round_created': [],
            'round_started': [],
            'round_completed': [],
            'round_failed': [],
            'node_joined': [],
            'node_contributed': [],
            'node_failed': [],
            'consensus_reached': [],
            'rewards_distributed': []
        }

        # Estadísticas globales
        self.total_rounds_orchestrated = 0
        self.total_participants_served = 0
        self.total_rewards_distributed = 0.0

        logger.info(f"🎼 RoundOrchestrator initialized for session {session_id}")

    async def initialize(self, session: FederatedSession) -> bool:
        """Inicializar el orquestador con una sesión federada."""
        try:
            self.session = session

            # Inicializar componentes
            await self._initialize_p2p_protocol()
            await self._initialize_zkp_engine()
            await self._initialize_secure_aggregator()
            await self._initialize_dracma_manager()
            await self._initialize_node_scheduler()

            # Inicializar sincronización de estado
            await self._initialize_state_sync()

            # Inicializar gestor de consenso
            await self._initialize_consensus_manager()

            # Inicializar validador de estado
            await self._initialize_state_validator()

            # Inicializar auditor ZKP
            await self._initialize_zk_auditor()

            # Inicializar sistema de auto-healing
            await self._initialize_auto_healing()

            # Registrar handlers de eventos
            await self._register_event_handlers()

            logger.info("✅ RoundOrchestrator initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Error initializing RoundOrchestrator: {e}")
            return False

    async def _initialize_p2p_protocol(self):
        """Inicializar protocolo P2P para comunicación."""
        try:
            self.p2p_protocol = create_p2p_protocol(
                node_id=f"orchestrator_{self.session_id}",
                host="0.0.0.0",
                port=8444  # Puerto diferente al coordinator
            )
            await self.p2p_protocol.start()
            logger.info("✅ P2P protocol initialized for round orchestration")
        except Exception as e:
            logger.error(f"❌ Error initializing P2P protocol: {e}")
            raise

    async def _initialize_zkp_engine(self):
        """Inicializar motor ZKP para validación."""
        try:
            self.zkp_engine = create_zkp_engine(self.config)
            logger.info("✅ ZKP engine initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing ZKP engine: {e}")
            raise

    async def _initialize_secure_aggregator(self):
        """Inicializar agregador seguro."""
        try:
            self.secure_aggregator = create_secure_aggregator(
                session_id=self.session_id,
                model_name=self.session.model_name,
                config=self.default_round_config
            )
            logger.info("✅ Secure aggregator initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing secure aggregator: {e}")
            raise

    async def _initialize_dracma_manager(self):
        """Inicializar sistema de recompensas DRACMA."""
        try:
            self.dracma_manager = DRACMA_Manager(self.config)
            logger.info("✅ DracmaS manager initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing DracmaS manager: {e}")
            raise

    async def _initialize_node_scheduler(self):
        """Inicializar planificador de nodos."""
        try:
            # Obtener registro de nodos del sistema
            from ..discovery.node_registry import get_node_registry
            node_registry = get_node_registry()

            self.node_scheduler = create_node_scheduler(node_registry)
            await self.node_scheduler.start()
            logger.info("✅ Node scheduler initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing node scheduler: {e}")
            raise

    async def _initialize_state_sync(self):
        """Inicializar sincronización de estado."""
        try:
            self.state_sync = create_state_sync(f"orchestrator_{self.session_id}")
            await self.state_sync.start_sync_service()
            logger.info("✅ State sync initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing state sync: {e}")
            raise

    async def _initialize_consensus_manager(self):
        """Inicializar gestor de consenso."""
        try:
            self.consensus_manager = ConsensusManager(
                node_id=f"orchestrator_{self.session_id}",
                total_nodes=50,  # Configurable
                consensus_timeout=60
            )
            await self.consensus_manager.start_consensus_service()
            logger.info("✅ Consensus manager initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing consensus manager: {e}")
            raise

    async def _initialize_state_validator(self):
        """Inicializar validador de estado."""
        try:
            self.state_validator = StateValidator(self.config)
            logger.info("✅ State validator initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing state validator: {e}")
            raise

    async def _initialize_zk_auditor(self):
        """Inicializar auditor ZKP."""
        try:
            self.zk_auditor = ZKAuditor(self.config)
            logger.info("✅ ZK auditor initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing ZK auditor: {e}")
            raise

    async def _initialize_auto_healing(self):
        """Inicializar sistema de auto-healing."""
        try:
            from ..federated.auto_healing import create_auto_healing_coordinator
            self.auto_healing_coordinator = create_auto_healing_coordinator(
                session=self.session,
                orchestrator=self,
                node_scheduler=self.node_scheduler
            )
            logger.info("✅ Auto-healing coordinator initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing auto-healing coordinator: {e}")
            raise

    async def _register_event_handlers(self):
        """Registrar handlers para eventos del protocolo P2P."""
        if self.p2p_protocol:
            self.p2p_protocol.register_message_handler('round_join_request', self._handle_round_join_request)
            self.p2p_protocol.register_message_handler('round_contribution', self._handle_round_contribution)
            self.p2p_protocol.register_message_handler('round_status_update', self._handle_round_status_update)

    # ==================== GESTIÓN DE RONDAS ====================

    async def create_round(self, round_config: Optional[RoundConfig] = None,
                           expected_participants: Optional[List[str]] = None) -> str:
        """Crear una nueva ronda federada."""
        with self.round_lock:
            round_id = str(uuid.uuid4())
            self.current_round_number += 1

            config = round_config or self.default_round_config
            participants = expected_participants or (self.session.participants if self.session else [])

            # Si no hay participantes especificados y tenemos node_scheduler, usar selección inteligente
            if not participants and self.node_scheduler:
                criteria = SelectionCriteria(
                    min_participants=config.min_participants,
                    max_participants=config.max_participants
                )
                selected_nodes = await self.node_scheduler.select_round_participants(criteria)
                participants = selected_nodes

            round_state = RoundState(
                round_id=round_id,
                session_id=self.session_id,
                round_number=self.current_round_number,
                config=config,
                expected_participants=participants.copy()
            )

            # Inicializar participantes
            for node_id in participants:
                participation = NodeParticipation(node_id=node_id)
                round_state.participants[node_id] = participation

            self.active_rounds[round_id] = round_state
            self.total_rounds_orchestrated += 1

            await self._trigger_callbacks('round_created', round_id)
            logger.info(f"🎯 Created round {round_id} (#{self.current_round_number}) with {len(participants)} expected participants")

            return round_id

    async def start_round(self, round_id: str) -> bool:
        """Iniciar una ronda federada."""
        round_state = self.active_rounds.get(round_id)
        if not round_state:
            logger.error(f"Round {round_id} not found")
            return False

        with round_state.lock:
            if not round_state.can_start():
                logger.error(f"Round {round_id} cannot start: insufficient participants")
                return False

            # Cambiar estado
            round_state.status = RoundStatus.ACTIVE
            round_state.phase = RoundPhase.COORDINATING
            round_state.started_at = time.time()
            round_state.deadline = time.time() + round_state.config.round_timeout

            # Activar participantes iniciales
            round_state.active_participants = set(round_state.expected_participants)

            await self._trigger_callbacks('round_started', round_id)

            # Iniciar sistema de auto-healing si está disponible
            if self.auto_healing_coordinator:
                await self.auto_healing_coordinator.start_auto_healing()
                logger.info(f"🛠️ Auto-healing enabled for round {round_id}")

            # Iniciar tareas de la ronda
            asyncio.create_task(self._orchestrate_round(round_state))

            logger.info(f"🚀 Started round {round_id} with {len(round_state.active_participants)} participants")
            return True

    async def _orchestrate_round(self, round_state: RoundState):
        """Orquestar el ciclo completo de una ronda."""
        try:
            round_id = round_state.round_id

            # Fase 1: Validar estado antes de comenzar
            await self._validate_round_state(round_state)

            # Fase 2: Coordinación inicial
            await self._coordinate_round_participants(round_state)

            # Fase 3: Recopilación de contribuciones
            await self._collect_round_contributions(round_state)

            # Fase 3: Validación
            if round_state.config.enable_zkp_validation:
                await self._validate_round_contributions(round_state)

            # Fase 4: Agregación
            if round_state.config.enable_secure_aggregation:
                await self._aggregate_round_contributions(round_state)

            # Fase 5: Distribución de recompensas
            if round_state.config.reward_distribution_enabled:
                await self._distribute_round_rewards(round_state)

            # Fase 6: Auditar ronda con ZKP
            await self._audit_round_with_zkp(round_state)

            # Completar ronda
            await self._complete_round(round_state)

        except Exception as e:
            logger.error(f"❌ Error orchestrating round {round_state.round_id}: {e}")
            await self._fail_round(round_state, str(e))

    async def cancel_round(self, round_id: str, reason: str = "Cancelled by orchestrator") -> bool:
        """Cancelar una ronda."""
        round_state = self.active_rounds.get(round_id)
        if not round_state:
            return False

        with round_state.lock:
            round_state.status = RoundStatus.CANCELLED
            round_state.phase = RoundPhase.FAILED

            await self._trigger_callbacks('round_failed', round_id, reason)
            logger.info(f"🚫 Cancelled round {round_id}: {reason}")

            # Mover a completadas
            self.completed_rounds.append(round_state)
            del self.active_rounds[round_id]

            return True

    # ==================== COORDINACIÓN DE NODOS ====================

    async def _coordinate_round_participants(self, round_state: RoundState):
        """Coordinar participantes de la ronda."""
        round_state.phase = RoundPhase.COORDINATING

        # Enviar invitaciones a participantes
        invitation_tasks = []
        for node_id in round_state.expected_participants:
            task = self._send_round_invitation(round_state.round_id, node_id)
            invitation_tasks.append(task)

        # Esperar respuestas de aceptación
        await asyncio.gather(*invitation_tasks, return_exceptions=True)

        # Verificar participantes activos
        active_count = len(round_state.active_participants)
        min_required = round_state.config.min_participants

        if active_count < min_required:
            raise ValueError(f"Insufficient active participants: {active_count} < {min_required}")

        logger.info(f"👥 Round {round_state.round_id} coordinated with {active_count} active participants")

    async def _send_round_invitation(self, round_id: str, node_id: str):
        """Enviar invitación para unirse a la ronda."""
        if not self.p2p_protocol:
            return

        invitation = {
            'type': 'round_invitation',
            'round_id': round_id,
            'session_id': self.session_id,
            'round_number': self.active_rounds[round_id].round_number,
            'deadline': self.active_rounds[round_id].deadline,
            'config': self.active_rounds[round_id].config.__dict__
        }

        try:
            await self.p2p_protocol.send_model_update(node_id, {}, invitation)
            logger.debug(f"📨 Sent round invitation to {node_id} for round {round_id}")
        except Exception as e:
            logger.warning(f"Failed to send invitation to {node_id}: {e}")

    async def add_node_to_round(self, round_id: str, node_id: str) -> bool:
        """Agregar dinámicamente un nodo a una ronda activa."""
        round_state = self.active_rounds.get(round_id)
        if not round_state or not round_state.config.allow_dynamic_scaling:
            return False

        with round_state.lock:
            if node_id in round_state.participants:
                return False

            # Agregar participante
            participation = NodeParticipation(node_id=node_id)
            round_state.participants[node_id] = participation
            round_state.expected_participants.append(node_id)

            # Enviar invitación
            await self._send_round_invitation(round_id, node_id)

            logger.info(f"➕ Dynamically added node {node_id} to round {round_id}")
            return True

    async def remove_node_from_round(self, round_id: str, node_id: str, reason: str = "Removed by orchestrator"):
        """Remover un nodo de una ronda."""
        round_state = self.active_rounds.get(round_id)
        if not round_state:
            return False

        with round_state.lock:
            if node_id not in round_state.participants:
                return False

            participation = round_state.participants[node_id]
            participation.status = NodeParticipationStatus.FAILED
            participation.failure_reason = reason

            round_state.active_participants.discard(node_id)
            round_state.failed_participants.add(node_id)

            await self._trigger_callbacks('node_failed', round_id, node_id, reason)
            logger.info(f"➖ Removed node {node_id} from round {round_id}: {reason}")

            return True

    # ==================== RECOPILACIÓN DE CONTRIBUCIONES ====================

    async def _collect_round_contributions(self, round_state: RoundState):
        """Recopilar contribuciones de los participantes."""
        round_state.phase = RoundPhase.COLLECTING

        logger.info(f"📦 Starting contribution collection for round {round_state.round_id}")

        # Esperar contribuciones con timeout
        timeout = round_state.config.round_timeout
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Verificar si tenemos suficientes contribuciones
            completed_count = len(round_state.completed_participants)
            active_count = len(round_state.active_participants)

            if completed_count >= round_state.config.min_participants:
                break

            # Verificar timeouts de nodos individuales
            await self._check_node_timeouts(round_state)

            # Esperar un poco antes de verificar nuevamente
            await asyncio.sleep(5)

        # Verificar resultado final
        final_completed = len(round_state.completed_participants)
        min_required = round_state.config.min_participants

        if final_completed < min_required:
            raise ValueError(f"Insufficient contributions: {final_completed} < {min_required}")

        logger.info(f"📦 Collected {final_completed} contributions for round {round_state.round_id}")

    async def _check_node_timeouts(self, round_state: RoundState):
        """Verificar timeouts de nodos individuales."""
        current_time = time.time()
        node_timeout = round_state.config.node_timeout

        timed_out_nodes = []
        for node_id in list(round_state.active_participants):
            participation = round_state.participants[node_id]
            if participation.contributed_at and (current_time - participation.contributed_at) > node_timeout:
                timed_out_nodes.append(node_id)

        # Marcar nodos timeout
        for node_id in timed_out_nodes:
            await self.remove_node_from_round(round_state.round_id, node_id, "Node timeout")

    async def submit_contribution(self, round_id: str, node_id: str,
                                contribution: Dict[str, Any]) -> bool:
        """Enviar contribución de un nodo."""
        round_state = self.active_rounds.get(round_id)
        if not round_state:
            return False

        with round_state.lock:
            if node_id not in round_state.participants:
                logger.warning(f"Contribution from unknown node {node_id} for round {round_id}")
                return False

            participation = round_state.participants[node_id]

            # Validar contribución básica
            if not self._validate_contribution(contribution):
                participation.status = NodeParticipationStatus.FAILED
                participation.failure_reason = "Invalid contribution format"
                return False

            # Almacenar contribución
            participation.contribution = contribution
            participation.contributed_at = time.time()
            participation.status = NodeParticipationStatus.CONTRIBUTING

            round_state.contributions.append(contribution)
            round_state.total_contributions += 1

            await self._trigger_callbacks('node_contributed', round_id, node_id)

            logger.info(f"📦 Contribution received from {node_id} for round {round_id}")
            return True

    def _validate_contribution(self, contribution: Dict[str, Any]) -> bool:
        """Validar formato básico de contribución."""
        required_fields = ['node_id', 'model_weights', 'num_samples', 'round_num']
        return all(field in contribution for field in required_fields)

    # ==================== VALIDACIÓN DE RONDAS ====================

    async def _validate_round_contributions(self, round_state: RoundState):
        """Validar contribuciones de la ronda usando ZKP."""
        round_state.phase = RoundPhase.VALIDATING

        if not self.zkp_engine:
            logger.warning("ZKP engine not available, skipping validation")
            return

        logger.info(f"🔐 Starting ZKP validation for round {round_state.round_id}")

        validation_tasks = []
        for contribution in round_state.contributions:
            task = self._validate_single_contribution(contribution)
            validation_tasks.append(task)

        # Ejecutar validaciones en paralelo
        validation_results = await asyncio.gather(*validation_tasks, return_exceptions=True)

        # Procesar resultados
        valid_count = 0
        for i, result in enumerate(validation_results):
            contribution = round_state.contributions[i]
            node_id = contribution['node_id']

            if isinstance(result, Exception):
                logger.warning(f"ZKP validation failed for {node_id}: {result}")
                continue

            if result:  # Validación exitosa
                valid_count += 1
                participation = round_state.participants[node_id]
                participation.status = NodeParticipationStatus.COMPLETED
                participation.completed_at = time.time()
                round_state.completed_participants.add(node_id)
            else:
                logger.warning(f"ZKP validation failed for {node_id}")
                await self.remove_node_from_round(round_state.round_id, node_id, "ZKP validation failed")

        round_state.valid_contributions = valid_count
        round_state.validation_results = {
            'total_validated': len(validation_results),
            'valid_contributions': valid_count,
            'validation_rate': valid_count / len(validation_results) if validation_results else 0
        }

        logger.info(f"🔐 ZKP validation completed: {valid_count}/{len(validation_results)} contributions valid")

    async def _validate_single_contribution(self, contribution: Dict[str, Any]) -> bool:
        """Validar una contribución individual con ZKP."""
        try:
            if not self.zkp_engine:
                logger.warning("ZKP engine not available, skipping validation")
                return False

            # Verificar que tenga prueba ZKP
            if 'zkp_proof' not in contribution:
                logger.warning("No ZKP proof in contribution")
                return False

            zkp_data = contribution['zkp_proof']

            # Verificar estructura de la prueba ZKP
            if not isinstance(zkp_data, dict) or 'commitment' not in zkp_data or 'proof' not in zkp_data:
                logger.warning("Invalid ZKP proof structure")
                return False

            commitment = zkp_data['commitment']
            proof = zkp_data['proof']

            # Verificar prueba ZKP usando el motor
            is_valid = self.zkp_engine.verify_proof(commitment, proof)

            if is_valid:
                logger.debug("ZKP validation successful")
            else:
                logger.warning("ZKP validation failed")

            return is_valid

        except Exception as e:
            logger.error(f"Error validating contribution: {e}")
            return False

    # ==================== AGREGACIÓN ====================

    async def _aggregate_round_contributions(self, round_state: RoundState):
        """Agregar contribuciones de la ronda."""
        round_state.phase = RoundPhase.AGGREGATING

        if not self.secure_aggregator:
            logger.warning("Secure aggregator not available, skipping aggregation")
            return

        logger.info(f"🔒 Starting secure aggregation for round {round_state.round_id}")

        try:
            # Preparar actualizaciones para agregación
            valid_contributions = [
                c for c in round_state.contributions
                if round_state.participants[c['node_id']].status == NodeParticipationStatus.COMPLETED
            ]

            if not valid_contributions:
                raise ValueError("No valid contributions to aggregate")

            # Configurar agregador
            participant_ids = [c['node_id'] for c in valid_contributions]
            self.secure_aggregator.set_expected_participants(participant_ids)

            # Añadir actualizaciones encriptadas (simuladas)
            for contrib in valid_contributions:
                # En implementación real, los pesos ya vendrían encriptados
                self.secure_aggregator.add_encrypted_weight_update(
                    contrib['node_id'],
                    contrib['model_weights'],  # Ya deberían estar encriptados
                    contrib['num_samples'],
                    self.secure_aggregator.get_public_key()
                )

            # Realizar agregación
            aggregated_weights = self.secure_aggregator.aggregate_weights()
            round_state.aggregated_weights = aggregated_weights

            # Resetear agregador
            self.secure_aggregator.reset_for_next_round()

            logger.info(f"🔒 Secure aggregation completed for round {round_state.round_id}")

        except Exception as e:
            logger.error(f"❌ Error in secure aggregation: {e}")
            raise

    # ==================== DISTRIBUCIÓN DE RECOMPENSAS ====================

    async def _distribute_round_rewards(self, round_state: RoundState):
        """Distribuir recompensas por participación en la ronda."""
        if not self.dracma_manager:
            logger.warning("DracmaS manager not available, skipping reward distribution")
            return

        logger.info(f"💰 Distributing rewards for round {round_state.round_id}")

        try:
            # Preparar datos de contribución para recompensas
            contributions_for_rewards = []
            for contrib in round_state.contributions:
                node_id = contrib['node_id']
                participation = round_state.participants[node_id]

                if participation.status == NodeParticipationStatus.COMPLETED:
                    reward_calc = {
                        'node_id': node_id,
                        'type': 'federated_round_contribution',
                        'metrics': {
                            'accuracy': contrib.get('accuracy', 0.8),
                            'loss': contrib.get('loss', 0.5),
                            'samples_used': contrib['num_samples'],
                            'zkp_verified': True,
                            'round_number': round_state.round_number
                        },
                        'session_id': self.session_id
                    }
                    contributions_for_rewards.append(reward_calc)

            # Calcular y distribuir recompensas
            result = await self.dracma_manager.calculate_and_distribute_rewards(contributions_for_rewards)

            if result['success']:
                total_dracma = result['total_dracma']
                round_state.rewards_distributed = total_dracma
                self.total_rewards_distributed += total_dracma

                # Actualizar recompensas en participantes
                for contrib in contributions_for_rewards:
                    node_id = contrib['node_id']
                    participation = round_state.participants[node_id]
                    # Estimar recompensa por nodo
                    node_reward = total_dracma / len(contributions_for_rewards)
                    participation.reward_earned = node_reward

                await self._trigger_callbacks('rewards_distributed', round_state.round_id, total_dracma)
                logger.info(f"💰 Distributed {total_dracma:.4f} DracmaS rewards for round {round_state.round_id}")

                # Integrar con price oracle - las contribuciones federadas afectan precios de datasets
                await self._update_price_oracle_with_contributions(contributions_for_rewards)

            else:
                logger.error("Failed to distribute rewards")

        except Exception as e:
            logger.error(f"❌ Error distributing rewards: {e}")

    async def _update_price_oracle_with_contributions(self, contributions: List[Dict[str, Any]]):
        """Actualizar price oracle con señales de contribuciones federadas."""
        try:
            # Mapear tipos de datos de la sesión a categorías del marketplace
            session_data_category = self._map_session_to_data_category()

            if not session_data_category:
                return

            # Agregar señales de contribución al price oracle
            for contrib in contributions:
                node_id = contrib['node_id']
                metrics = contrib.get('metrics', {})
                quality_score = metrics.get('accuracy', 0.8)  # Usar accuracy como proxy de calidad
                contribution_value = metrics.get('samples_used', 100) * quality_score

                # Registrar contribución federada en el price oracle
                await price_oracle.record_federated_contribution(
                    node_id=node_id,
                    category=session_data_category,
                    contribution_value=contribution_value,
                    quality_score=quality_score
                )

            logger.info(f"📊 Updated price oracle with {len(contributions)} federated contributions for {session_data_category.value}")

        except Exception as e:
            logger.error(f"❌ Error updating price oracle with federated contributions: {e}")

    def _map_session_to_data_category(self) -> Optional[Any]:
        """Mapear tipo de sesión federada a categoría de datos del marketplace."""
        try:
            from ..marketplace.data_listing import DataCategory

            if not self.session:
                return None

            # Mapear basado en el nombre del modelo o tipo de sesión
            model_name = self.session.model_name.lower() if self.session.model_name else ""

            if "image" in model_name or "vision" in model_name:
                return DataCategory.IMAGE_DATA
            elif "text" in model_name or "nlp" in model_name or "language" in model_name:
                return DataCategory.TEXT_DATA
            elif "audio" in model_name or "speech" in model_name:
                return DataCategory.AUDIO_DATA
            elif "tabular" in model_name or "regression" in model_name:
                return DataCategory.TABULAR_DATA
            elif "time" in model_name or "series" in model_name:
                return DataCategory.TIME_SERIES
            elif "medical" in model_name or "health" in model_name:
                return DataCategory.MEDICAL_DATA
            elif "financial" in model_name or "finance" in model_name:
                return DataCategory.FINANCIAL_DATA
            elif "iot" in model_name or "sensor" in model_name:
                return DataCategory.IoT_DATA
            else:
                # Default to text data for general ML models
                return DataCategory.TEXT_DATA

        except Exception as e:
            logger.error(f"Error mapping session to data category: {e}")
            return None

    async def _validate_round_state(self, round_state: RoundState):
        """Validar estado de la ronda usando StateValidator."""
        try:
            if self.state_validator:
                # Obtener sesión de base de datos real
                from ..coordinator.database.connection import get_db
                db_session = next(get_db())

                try:
                    is_valid, issues = await self.state_validator.validate_global_state(db_session)

                    if not is_valid:
                        logger.warning(f"⚠️ Round state validation failed for {round_state.round_id}: {len(issues)} issues")
                        # En producción, podría detener la ronda o tomar acciones correctivas
                        for issue in issues:
                            logger.warning(f"  - {issue}")
                    else:
                        logger.info(f"✅ Round state validation passed for {round_state.round_id}")

                finally:
                    db_session.close()

        except Exception as e:
            logger.error(f"❌ Error validating round state: {e}")

    async def _audit_round_with_zkp(self, round_state: RoundState):
        """Auditar ronda completada con ZKP."""
        try:
            if self.zk_auditor and round_state.contributions:
                # Preparar datos para auditoría
                calculations = []
                for contrib in round_state.contributions:
                    node_id = contrib['node_id']
                    participation = round_state.participants.get(node_id)
                    if participation and participation.status == NodeParticipationStatus.COMPLETED:
                        calc = {
                            'node_id': node_id,
                            'dracma_amount': participation.reward_earned,
                            'accuracy': contrib.get('accuracy', 0.8),
                            'loss': contrib.get('loss', 0.5),
                            'samples_used': contrib['num_samples']
                        }
                        calculations.append(calc)

                if calculations:
                    # Realizar auditoría ZKP
                    audit_result = await self.zk_auditor.audit_reward_calculations(
                        session_id=self.session_id,
                        calculations=calculations,
                        pool_balance=1000.0  # Mock balance
                    )

                    logger.info(f"🔐 ZKP audit completed for round {round_state.round_id}: {audit_result.total_rewards_calculated} DRACMA")

        except Exception as e:
            logger.error(f"❌ Error auditing round with ZKP: {e}")

    # ==================== COMPLETACIÓN DE RONDAS ====================

    async def _complete_round(self, round_state: RoundState):
        """Completar una ronda exitosamente."""
        with round_state.lock:
            round_state.status = RoundStatus.COMPLETED
            round_state.phase = RoundPhase.COMPLETED
            round_state.completed_at = time.time()

            await self._trigger_callbacks('round_completed', round_state.round_id)

            # Mover a rondas completadas
            self.completed_rounds.append(round_state)
            del self.active_rounds[round_state.round_id]

            # Actualizar estadísticas
            self.total_participants_served += len(round_state.completed_participants)

            logger.info(f"✅ Round {round_state.round_id} completed successfully")
            logger.info(f"   📊 Participants: {len(round_state.completed_participants)}/{len(round_state.expected_participants)}")
            logger.info(f"   💰 Rewards distributed: {round_state.rewards_distributed:.4f} DRACMA")

    async def _fail_round(self, round_state: RoundState, reason: str):
        """Marcar una ronda como fallida."""
        with round_state.lock:
            round_state.status = RoundStatus.FAILED
            round_state.phase = RoundPhase.FAILED
            round_state.completed_at = time.time()

            await self._trigger_callbacks('round_failed', round_state.round_id, reason)

            # Mover a rondas completadas
            self.completed_rounds.append(round_state)
            del self.active_rounds[round_state.round_id]

            logger.error(f"❌ Round {round_state.round_id} failed: {reason}")

    # ==================== MANEJO DE EVENTOS ====================

    async def _handle_round_join_request(self, message):
        """Manejar solicitud de unirse a una ronda."""
        try:
            payload = message.payload
            node_id = message.sender_id
            round_id = payload.get('round_id')

            if round_id not in self.active_rounds:
                logger.warning(f"Join request for unknown round {round_id} from {node_id}")
                return

            round_state = self.active_rounds[round_id]

            # Agregar nodo si es permitido
            if await self.add_node_to_round(round_id, node_id):
                # Confirmar aceptación
                confirmation = {
                    'type': 'round_join_accepted',
                    'round_id': round_id,
                    'node_id': node_id
                }
                await self.p2p_protocol.send_model_update(node_id, {}, confirmation)

                await self._trigger_callbacks('node_joined', round_id, node_id)

        except Exception as e:
            logger.error(f"❌ Error handling round join request: {e}")

    async def _handle_round_contribution(self, message):
        """Manejar contribución de un nodo."""
        try:
            payload = message.payload
            node_id = message.sender_id
            round_id = payload.get('round_id')

            # Extraer contribución del payload
            contribution = {
                'node_id': node_id,
                'model_weights': payload.get('model_weights', {}),
                'num_samples': payload.get('num_samples', 0),
                'accuracy': payload.get('accuracy', 0.0),
                'loss': payload.get('loss', 0.0),
                'round_num': payload.get('round_num', 0),
                'zkp_proof': payload.get('zkp_proof')
            }

            await self.submit_contribution(round_id, node_id, contribution)

        except Exception as e:
            logger.error(f"❌ Error handling round contribution: {e}")

    async def _handle_round_status_update(self, message):
        """Manejar actualización de estado de ronda."""
        try:
            payload = message.payload
            node_id = message.sender_id
            round_id = payload.get('round_id')

            if round_id not in self.active_rounds:
                logger.warning(f"Status update for unknown round {round_id} from {node_id}")
                return

            round_state = self.active_rounds[round_id]
            new_status = payload.get('status')
            new_phase = payload.get('phase')

            with round_state.lock:
                # Actualizar estado si es válido
                if new_status and new_status in [s.value for s in RoundStatus]:
                    old_status = round_state.status
                    round_state.status = RoundStatus(new_status)
                    logger.info(f"Round {round_id} status updated from {old_status.value} to {new_status} by {node_id}")

                # Actualizar fase si es válida
                if new_phase and new_phase in [p.value for p in RoundPhase]:
                    old_phase = round_state.phase
                    round_state.phase = RoundPhase(new_phase)
                    logger.info(f"Round {round_id} phase updated from {old_phase.value} to {new_phase} by {node_id}")

                # Actualizar métricas adicionales si se proporcionan
                if 'progress' in payload:
                    # Podría actualizar métricas de progreso
                    pass

                if 'error' in payload:
                    # Manejar errores reportados por nodos
                    error_msg = payload['error']
                    logger.warning(f"Round {round_id} error reported by {node_id}: {error_msg}")

                    # Marcar nodo como fallido si es necesario
                    if node_id in round_state.participants:
                        participation = round_state.participants[node_id]
                        if participation.status != NodeParticipationStatus.FAILED:
                            participation.status = NodeParticipationStatus.FAILED
                            participation.failure_reason = error_msg
                            round_state.failed_participants.add(node_id)
                            round_state.active_participants.discard(node_id)

                            await self._trigger_callbacks('node_failed', round_id, node_id, error_msg)

        except Exception as e:
            logger.error(f"❌ Error handling round status update: {e}")

    # ==================== CALLBACKS Y EVENTOS ====================

    def register_callback(self, event: str, callback: Callable):
        """Registrar callback para evento."""
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)

    async def _trigger_callbacks(self, event: str, *args, **kwargs):
        """Disparar callbacks para un evento."""
        for callback in self.event_callbacks[event]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"❌ Error in callback for {event}: {e}")

    # ==================== CONSULTA DE ESTADO ====================

    def get_round_status(self, round_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de una ronda específica."""
        round_state = self.active_rounds.get(round_id)
        if not round_state:
            # Buscar en rondas completadas
            for completed in self.completed_rounds:
                if completed.round_id == round_id:
                    round_state = completed
                    break

        if not round_state:
            return None

        return {
            'round_id': round_state.round_id,
            'round_number': round_state.round_number,
            'phase': round_state.phase.value,
            'status': round_state.status.value,
            'progress_percentage': round_state.get_progress_percentage(),
            'time_remaining': round_state.get_time_remaining(),
            'participants': {
                'expected': len(round_state.expected_participants),
                'active': len(round_state.active_participants),
                'completed': len(round_state.completed_participants),
                'failed': len(round_state.failed_participants)
            },
            'contributions': {
                'total': round_state.total_contributions,
                'valid': round_state.valid_contributions
            },
            'rewards_distributed': round_state.rewards_distributed,
            'created_at': round_state.created_at,
            'started_at': round_state.started_at,
            'completed_at': round_state.completed_at
        }

    def get_active_rounds(self) -> List[Dict[str, Any]]:
        """Obtener lista de rondas activas."""
        return [self.get_round_status(rid) for rid in self.active_rounds.keys()]

    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del orquestador."""
        return {
            'session_id': self.session_id,
            'total_rounds_orchestrated': self.total_rounds_orchestrated,
            'active_rounds': len(self.active_rounds),
            'completed_rounds': len(self.completed_rounds),
            'total_participants_served': self.total_participants_served,
            'total_rewards_distributed': self.total_rewards_distributed,
            'uptime_seconds': time.time() - (self.session.start_time if self.session else time.time())
        }

    # ==================== APAGADO ====================

    async def shutdown(self):
        """Apagar el orquestador de rondas."""
        try:
            logger.info("🛑 Shutting down RoundOrchestrator...")

            # Cancelar rondas activas
            active_ids = list(self.active_rounds.keys())
            for round_id in active_ids:
                await self.cancel_round(round_id, "Orchestrator shutdown")

            # Apagar componentes
            if self.p2p_protocol:
                await self.p2p_protocol.stop()

            if self.node_scheduler:
                await self.node_scheduler.stop()

            if self.state_sync:
                await self.state_sync.stop_sync_service()

            if self.consensus_manager:
                await self.consensus_manager.stop_consensus_service()

            # Apagar servicios de validación y auditoría
            if self.zk_auditor:
                try:
                    self.zk_auditor.stop_periodic_audits()
                    logger.info("✅ ZK auditor stopped")
                except Exception as e:
                    logger.warning(f"Error stopping ZK auditor: {e}")

            if self.state_validator:
                # StateValidator no tiene método shutdown específico
                logger.info("✅ State validator shutdown (no specific shutdown needed)")

            self.executor.shutdown(wait=True)

            logger.info("✅ RoundOrchestrator shut down successfully")

        except Exception as e:
            logger.error(f"❌ Error shutting down RoundOrchestrator: {e}")


# ==================== FUNCIONES DE CONVENIENCIA ====================

def create_round_orchestrator(session_id: str, config: Optional[Config] = None) -> RoundOrchestrator:
    """Crear una instancia del orquestador de rondas."""
    return RoundOrchestrator(session_id, config)


async def initialize_round_orchestrator(orchestrator: RoundOrchestrator,
                                      session: FederatedSession) -> bool:
    """Inicializar orquestador con una sesión."""
    return await orchestrator.initialize(session)


async def orchestrate_federated_round(session: FederatedSession,
                                    round_config: Optional[RoundConfig] = None,
                                    config: Optional[Config] = None) -> RoundOrchestrator:
    """
    Función de conveniencia para orquestar una ronda federada completa.

    Args:
        session: Sesión federada
        round_config: Configuración de la ronda
        config: Configuración general

    Returns:
        RoundOrchestrator: Orquestador inicializado
    """
    orchestrator = create_round_orchestrator(session.session_id, config)

    if not await orchestrator.initialize(session):
        raise RuntimeError("Failed to initialize round orchestrator")

    # Crear y iniciar ronda
    round_id = await orchestrator.create_round(round_config)

    if not await orchestrator.start_round(round_id):
        raise RuntimeError(f"Failed to start round {round_id}")

    return orchestrator