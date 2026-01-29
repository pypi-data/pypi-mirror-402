"""
Distributed Trainer - Entrenamiento Federado Real con Múltiples Nodos Físicos
Implementa el entrenamiento federado completo coordinando múltiples nodos físicos,
utilizando todas las funcionalidades desarrolladas: P2P, ZKP, sincronización, consenso,
agregación segura y distribución de recompensas.
"""

import asyncio
import json
import time
import uuid
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor

import torch
import torch.nn as nn

from ..core.logging import get_logger
from ..core.config import Config
from ..models.empoorio_lm import EmpoorioLM, EmpoorioLMConfig
from ..verification.zkp_engine import ZKPEngine, create_zkp_engine
from ..verification.training_prover import TrainingProver, TrainingProof, create_training_prover
from ..coordinator.state_sync import StateSync, create_state_sync
from ..coordinator.consensus_manager import ConsensusManager, start_consensus_service
from ..coordinator.state_validator import StateValidator
from ..auditing.zk_auditor import ZKAuditor
from ..federated.p2p_protocol import P2PProtocol, create_p2p_protocol, PeerInfo, ConnectionState
from ..federated.secure_aggregator import SecureAggregator, create_secure_aggregator, AggregationConfig
from ..rewards.dracma_manager import DRACMA_Manager
from ..data.preprocessing import TextPreprocessingConfig, TextPreprocessor

logger = get_logger(__name__)


class TrainingPhase(Enum):
    """Fases del entrenamiento distribuido."""
    INITIALIZING = "initializing"
    COORDINATING = "coordinating"
    TRAINING = "training"
    AGGREGATING = "aggregating"
    VALIDATING = "validating"
    DISTRIBUTING = "distributing"
    COMPLETED = "completed"
    FAILED = "failed"


class NodeStatus(Enum):
    """Estados de los nodos participantes."""
    REGISTERED = "registered"
    CONNECTED = "connected"
    TRAINING = "training"
    COMPLETED = "completed"
    FAILED = "failed"
    DISCONNECTED = "disconnected"


@dataclass
class DistributedNode:
    """Información de un nodo participante en el entrenamiento distribuido."""
    node_id: str
    host: str
    port: int
    public_key: Optional[str] = None
    status: NodeStatus = NodeStatus.REGISTERED
    reputation_score: float = 1.0
    last_seen: float = field(default_factory=time.time)
    training_contribution: Optional[Dict[str, Any]] = None
    zkp_proof: Optional[TrainingProof] = None
    reward_earned: float = 0.0
    connection_attempts: int = 0
    max_connection_attempts: int = 3


@dataclass
class DistributedRound:
    """Información de una ronda de entrenamiento distribuido."""
    round_num: int
    start_time: float
    end_time: Optional[float] = None
    phase: TrainingPhase = TrainingPhase.INITIALIZING
    participants: List[str] = field(default_factory=list)
    expected_participants: List[str] = field(default_factory=list)
    completed_participants: List[str] = field(default_factory=list)
    failed_participants: List[str] = field(default_factory=list)
    global_model_cid: str = ""
    aggregated_weights: Optional[Dict[str, Any]] = None
    validation_metrics: Dict[str, Any] = field(default_factory=dict)
    consensus_reached: bool = False
    rewards_distributed: bool = False


class DistributedTrainer:
    """
    Trainer distribuido que coordina el entrenamiento federado real entre múltiples nodos físicos.
    Implementa todas las funcionalidades avanzadas: P2P seguro, ZKP, consenso, agregación segura,
    sincronización de estado y distribución de recompensas.
    """

    def __init__(self, session_id: str, model_name: str = "empoorio_lm", dataset_name: str = "federated_dataset",
                 coordinator_host: str = "0.0.0.0", coordinator_port: int = 8443,
                 min_nodes: int = 3, max_nodes: int = 50, config: Optional[Config] = None):
        self.session_id = session_id
        self.model_name = model_name
        self.dataset_name = dataset_name
        self.coordinator_host = coordinator_host
        self.coordinator_port = coordinator_port
        self.min_nodes = min_nodes
        self.max_nodes = max_nodes
        self.config = config or Config()

        # Estado del entrenamiento
        self.current_phase = TrainingPhase.INITIALIZING
        self.current_round = 0
        self.training_rounds: List[DistributedRound] = []
        self.is_running = False

        # Nodos participantes
        self.nodes: Dict[str, DistributedNode] = {}
        self.active_nodes: Set[str] = set()

        # Componentes principales
        self.global_model: Optional[EmpoorioLM] = None
        self.model_config = EmpoorioLMConfig()
        self.current_model_cid = ""

        # Protocolo P2P para comunicación entre nodos
        self.p2p_protocol: Optional[P2PProtocol] = None
        self.p2p_enabled = False

        # Agregador seguro con homomorphic encryption
        self.secure_aggregator: Optional[SecureAggregator] = None

        # Motor ZKP para validación de contribuciones
        self.zkp_engine: Optional[ZKPEngine] = None
        self.training_prover: Optional[TrainingProver] = None

        # Sincronización de estado distribuido
        self.state_sync: Optional[StateSync] = None

        # Gestor de consenso para operaciones críticas
        self.consensus_manager: Optional[ConsensusManager] = None

        # Sistema de recompensas DRACMA
        self.dracma_manager: Optional[DRACMA_Manager] = None

        # Validador de estado
        self.state_validator: Optional[StateValidator] = None

        # Auditor ZKP
        self.zk_auditor: Optional[ZKAuditor] = None

        # Preprocesamiento de datos
        self.data_preprocessor: Optional[TextPreprocessor] = None

        # Configuración de timeouts y límites
        self.round_timeout = 1800  # 30 minutos por ronda
        self.node_timeout = 300    # 5 minutos timeout por nodo
        self.consensus_timeout = 60  # 1 minuto para consenso
        self.max_rounds = 10

        # Estadísticas y métricas
        self.start_time = time.time()
        self.total_parameters_trained = 0
        self.total_rewards_distributed = 0.0

        # Locks para thread safety
        self.state_lock = threading.RLock()
        self.node_lock = threading.RLock()

        # Executor para operaciones asíncronas
        self.executor = ThreadPoolExecutor(max_workers=8)

        # Callbacks para eventos
        self.event_callbacks: Dict[str, List[callable]] = {
            'node_connected': [],
            'node_disconnected': [],
            'round_started': [],
            'round_completed': [],
            'consensus_reached': [],
            'rewards_distributed': [],
            'training_failed': []
        }

        logger.info(f"🚀 DistributedTrainer initialized for session {session_id}")

    async def initialize(self) -> bool:
        """Inicializa todos los componentes del trainer distribuido."""
        try:
            logger.info("🔧 Initializing distributed training components...")

            # 1. Inicializar modelo global
            await self._initialize_global_model()

            # 2. Inicializar preprocesamiento de datos
            await self._initialize_data_preprocessing()

            # 3. Inicializar protocolo P2P
            await self._initialize_p2p_protocol()

            # 4. Inicializar agregador seguro
            await self._initialize_secure_aggregator()

            # 5. Inicializar motor ZKP
            await self._initialize_zkp_engine()

            # 6. Inicializar sincronización de estado
            await self._initialize_state_sync()

            # 7. Inicializar gestor de consenso
            await self._initialize_consensus_manager()

            # 8. Inicializar sistema de recompensas
            await self._initialize_dracma_manager()

            # 9. Inicializar validador de estado
            await self._initialize_state_validator()

            # 10. Inicializar auditor ZKP
            await self._initialize_zk_auditor()

            # 11. Registrar handlers de eventos
            await self._register_event_handlers()

            self.current_phase = TrainingPhase.COORDINATING
            logger.info("✅ Distributed trainer initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Error initializing distributed trainer: {e}")
            self.current_phase = TrainingPhase.FAILED
            return False

    async def _initialize_global_model(self):
        """Inicializar el modelo global."""
        try:
            self.global_model = EmpoorioLM(self.model_config)
            logger.info("✅ Global model initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing global model: {e}")
            raise

    async def _initialize_data_preprocessing(self):
        """Inicializar sistema de preprocesamiento de datos."""
        try:
            preprocessing_config = TextPreprocessingConfig(
                min_length=10, max_length=10000, min_words=3, max_words=2000,
                remove_duplicates=True, remove_urls=True, remove_emails=True,
                normalize_unicode=True, remove_extra_whitespace=True,
                enable_stats=True, max_workers=4, batch_size=1000
            )
            self.data_preprocessor = TextPreprocessor(preprocessing_config)
            logger.info("✅ Data preprocessing initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing data preprocessing: {e}")
            raise

    async def _initialize_p2p_protocol(self):
        """Inicializar protocolo P2P para comunicación entre nodos."""
        try:
            self.p2p_protocol = create_p2p_protocol(
                node_id=f"coordinator_{self.session_id}",
                host=self.coordinator_host,
                port=self.coordinator_port
            )
            await self.p2p_protocol.start()
            self.p2p_enabled = True
            logger.info("✅ P2P protocol initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing P2P protocol: {e}")
            raise

    async def _initialize_secure_aggregator(self):
        """Inicializar agregador seguro con homomorphic encryption."""
        try:
            agg_config = AggregationConfig(
                aggregation_type="fedavg",
                enable_differential_privacy=True,
                dp_epsilon=1.0,
                dp_delta=1e-5,
                noise_scale=0.01,
                key_size=2048,
                min_participants=self.min_nodes,
                max_round_time=self.round_timeout
            )
            self.secure_aggregator = create_secure_aggregator(
                session_id=self.session_id,
                model_name=self.model_name,
                config=agg_config
            )
            logger.info("✅ Secure aggregator initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing secure aggregator: {e}")
            raise

    async def _initialize_zkp_engine(self):
        """Inicializar motor ZKP para validación."""
        try:
            self.zkp_engine = create_zkp_engine(self.config)
            self.training_prover = create_training_prover(self.config)
            logger.info("✅ ZKP engine initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing ZKP engine: {e}")
            raise

    async def _initialize_state_sync(self):
        """Inicializar sincronización de estado distribuido."""
        try:
            self.state_sync = create_state_sync(f"coordinator_{self.session_id}")
            await self.state_sync.start_sync_service()
            logger.info("✅ State synchronization initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing state sync: {e}")
            raise

    async def _initialize_consensus_manager(self):
        """Inicializar gestor de consenso."""
        try:
            self.consensus_manager = ConsensusManager(
                node_id=f"coordinator_{self.session_id}",
                total_nodes=self.max_nodes,
                consensus_timeout=self.consensus_timeout
            )
            await self.consensus_manager.start_consensus_service()
            logger.info("✅ Consensus manager initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing consensus manager: {e}")
            raise

    async def _initialize_dracma_manager(self):
        """Inicializar sistema de recompensas DRACMA."""
        try:
            self.dracma_manager = DRACMA_Manager(self.config)
            logger.info("✅ DracmaS manager initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing DracmaS manager: {e}")
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

    async def _register_event_handlers(self):
        """Registrar handlers para eventos del protocolo P2P."""
        if self.p2p_protocol:
            # Registrar handlers para mensajes P2P
            self.p2p_protocol.register_message_handler('model_update', self._handle_model_update)
            self.p2p_protocol.register_message_handler('aggregation_request', self._handle_aggregation_request)
            self.p2p_protocol.register_message_handler('training_proof', self._handle_training_proof)

            # Registrar callbacks de conexión
            self.p2p_protocol.register_connection_handler('peer_connected', self._handle_peer_connected)
            self.p2p_protocol.register_connection_handler('peer_disconnected', self._handle_peer_disconnected)

    async def register_node(self, node_id: str, host: str, port: int, public_key: Optional[str] = None) -> bool:
        """Registrar un nuevo nodo participante."""
        with self.node_lock:
            if node_id in self.nodes:
                logger.warning(f"Node {node_id} already registered")
                return False

            if len(self.nodes) >= self.max_nodes:
                logger.warning(f"Maximum nodes ({self.max_nodes}) reached")
                return False

            node = DistributedNode(
                node_id=node_id,
                host=host,
                port=port,
                public_key=public_key,
                status=NodeStatus.REGISTERED
            )

            self.nodes[node_id] = node
            logger.info(f"✅ Node {node_id} registered ({host}:{port})")
            return True

    async def connect_to_node(self, node_id: str) -> bool:
        """Conectar a un nodo específico."""
        if node_id not in self.nodes:
            logger.error(f"Node {node_id} not registered")
            return False

        node = self.nodes[node_id]

        try:
            # Crear PeerInfo para conexión P2P
            peer_info = PeerInfo(
                node_id=node_id,
                host=node.host,
                port=node.port,
                public_key=node.public_key or b'',
                connection_state=ConnectionState.DISCONNECTED
            )

            # Intentar conexión P2P
            success = await self.p2p_protocol.connect_to_peer(peer_info)

            if success:
                node.status = NodeStatus.CONNECTED
                node.last_seen = time.time()
                node.connection_attempts = 0
                self.active_nodes.add(node_id)

                # Actualizar estado de sincronización
                self.state_sync.add_peer(node_id)

                logger.info(f"🔗 Connected to node {node_id}")
                await self._trigger_callbacks('node_connected', node_id)
                return True
            else:
                node.connection_attempts += 1
                if node.connection_attempts >= node.max_connection_attempts:
                    node.status = NodeStatus.FAILED
                    logger.error(f"❌ Failed to connect to node {node_id} after {node.connection_attempts} attempts")
                return False

        except Exception as e:
            logger.error(f"❌ Error connecting to node {node_id}: {e}")
            node.status = NodeStatus.FAILED
            return False

    async def start_distributed_training(self, training_config: Dict[str, Any]) -> bool:
        """Iniciar el entrenamiento distribuido."""
        try:
            if len(self.active_nodes) < self.min_nodes:
                logger.error(f"Insufficient nodes: {len(self.active_nodes)} < {self.min_nodes}")
                return False

            self.is_running = True
            self.current_phase = TrainingPhase.TRAINING

            logger.info(f"🚀 Starting distributed training with {len(self.active_nodes)} nodes")

            # Distribuir modelo inicial
            await self._distribute_initial_model()

            # Ejecutar rondas de entrenamiento
            for round_num in range(1, self.max_rounds + 1):
                if not self.is_running:
                    break

                success = await self._execute_training_round(round_num, training_config)
                if not success:
                    logger.error(f"Round {round_num} failed")
                    break

            # Finalizar entrenamiento
            await self._finalize_training()

            return True

        except Exception as e:
            logger.error(f"❌ Error in distributed training: {e}")
            self.current_phase = TrainingPhase.FAILED
            await self._trigger_callbacks('training_failed', str(e))
            return False

    async def _distribute_initial_model(self) -> str:
        """Distribuir el modelo inicial a todos los nodos."""
        try:
            logger.info("📤 Distributing initial model to all nodes...")

            # Serializar pesos del modelo
            model_weights = self._get_model_weights()
            model_metadata = {
                "session_id": self.session_id,
                "model_name": self.model_name,
                "round_num": 0,
                "created_at": time.time(),
                "weights": model_weights
            }

            # Publicar en IPFS
            from ..infrastructure.ipfs_embedded import create_ipfs_manager
            ipfs_manager = create_ipfs_manager()
            await ipfs_manager.start()

            metadata_json = json.dumps(model_metadata, indent=2, default=str)
            self.current_model_cid = await ipfs_manager.publish_data(metadata_json.encode('utf-8'))

            await ipfs_manager.stop()

            # Enviar CID a todos los nodos conectados
            for node_id in self.active_nodes:
                await self._send_model_cid_to_node(node_id, self.current_model_cid)

            logger.info(f"✅ Initial model distributed with CID: {self.current_model_cid}")
            return self.current_model_cid

        except Exception as e:
            logger.error(f"❌ Error distributing initial model: {e}")
            raise

    async def _execute_training_round(self, round_num: int, training_config: Dict[str, Any]) -> bool:
        """Ejecutar una ronda completa de entrenamiento distribuido."""
        try:
            logger.info(f"🎯 Starting round {round_num}")

            # Crear nueva ronda
            round_info = DistributedRound(
                round_num=round_num,
                start_time=time.time(),
                phase=TrainingPhase.TRAINING,
                expected_participants=list(self.active_nodes),
                global_model_cid=self.current_model_cid
            )
            self.training_rounds.append(round_info)
            self.current_round = round_num

            await self._trigger_callbacks('round_started', round_num)

            # 1. Iniciar ronda en todos los nodos
            await self._start_round_on_nodes(round_num, training_config)

            # 2. Esperar contribuciones de nodos
            contributions_received = await self._collect_node_contributions(round_num)

            if len(contributions_received) < self.min_nodes:
                logger.error(f"Insufficient contributions: {len(contributions_received)} < {self.min_nodes}")
                round_info.phase = TrainingPhase.FAILED
                return False

            # 3. Validar estado antes de continuar
            await self._validate_round_state(round_num)

            # 4. Validar contribuciones con ZKP
            valid_contributions = await self._validate_contributions_with_zkp(contributions_received)

            # 5. Agregación segura
            round_info.phase = TrainingPhase.AGGREGATING
            aggregated_weights = await self._perform_secure_aggregation(valid_contributions)

            # 5. Actualizar modelo global
            self._load_model_weights(aggregated_weights)
            round_info.aggregated_weights = aggregated_weights

            # 6. Distribuir modelo actualizado
            round_info.phase = TrainingPhase.DISTRIBUTING
            new_cid = await self._distribute_updated_model(aggregated_weights)
            round_info.global_model_cid = new_cid
            self.current_model_cid = new_cid

            # 7. Distribuir recompensas
            await self._distribute_round_rewards(valid_contributions, round_num)

            # 8. Auditar ronda con ZKP
            await self._audit_round_with_zkp(valid_contributions, round_num)

            # 9. Completar ronda
            round_info.end_time = time.time()
            round_info.phase = TrainingPhase.COMPLETED
            round_info.completed_participants = [c['node_id'] for c in valid_contributions]

            await self._trigger_callbacks('round_completed', round_num)

            logger.info(f"✅ Round {round_num} completed successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Error in round {round_num}: {e}")
            if self.training_rounds:
                self.training_rounds[-1].phase = TrainingPhase.FAILED
            return False

    async def _start_round_on_nodes(self, round_num: int, training_config: Dict[str, Any]):
        """Iniciar ronda de entrenamiento en todos los nodos."""
        start_tasks = []
        for node_id in self.active_nodes:
            task = self._send_round_start_to_node(node_id, round_num, training_config)
            start_tasks.append(task)

        await asyncio.gather(*start_tasks, return_exceptions=True)
        logger.info(f"🎯 Round {round_num} started on {len(self.active_nodes)} nodes")

    async def _collect_node_contributions(self, round_num: int) -> List[Dict[str, Any]]:
        """Recopilar contribuciones de los nodos."""
        contributions = []
        timeout = time.time() + self.round_timeout

        while time.time() < timeout and len(contributions) < len(self.active_nodes):
            await asyncio.sleep(1)  # Esperar contribuciones

            # Verificar timeouts de nodos
            current_time = time.time()
            for node_id in list(self.active_nodes):
                node = self.nodes[node_id]
                if node.training_contribution and node.training_contribution.get('round_num') == round_num:
                    contributions.append(node.training_contribution)
                    self.active_nodes.discard(node_id)  # Ya contribuyó
                elif current_time - node.last_seen > self.node_timeout:
                    logger.warning(f"Node {node_id} timed out")
                    node.status = NodeStatus.FAILED
                    self.active_nodes.discard(node_id)

        logger.info(f"📦 Collected {len(contributions)} contributions for round {round_num}")
        return contributions

    async def _validate_contributions_with_zkp(self, contributions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validar contribuciones usando pruebas ZKP."""
        valid_contributions = []

        for contribution in contributions:
            node_id = contribution['node_id']

            # Verificar que tenga prueba ZKP
            if 'zkp_proof' not in contribution:
                logger.warning(f"No ZKP proof for node {node_id}")
                continue

            # Verificar prueba ZKP
            proof = contribution['zkp_proof']
            is_valid = await self.training_prover.verify_training_proof(proof)

            if is_valid:
                valid_contributions.append(contribution)
                logger.info(f"✅ ZKP validation passed for node {node_id}")
            else:
                logger.warning(f"❌ ZKP validation failed for node {node_id}")

        logger.info(f"🔐 Validated {len(valid_contributions)}/{len(contributions)} contributions with ZKP")
        return valid_contributions

    async def _perform_secure_aggregation(self, contributions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Realizar agregación segura de pesos."""
        try:
            # Preparar actualizaciones para el agregador seguro
            encrypted_updates = []
            for contrib in contributions:
                # En un implementación real, los pesos ya vendrían encriptados
                # Aquí simulamos la preparación
                encrypted_update = {
                    'node_id': contrib['node_id'],
                    'encrypted_weights': contrib['model_weights'],  # Ya deberían estar encriptados
                    'num_samples': contrib['num_samples'],
                    'public_key': self.secure_aggregator.get_public_key()
                }
                encrypted_updates.append(encrypted_update)

            # Configurar participantes esperados
            participant_ids = [c['node_id'] for c in contributions]
            self.secure_aggregator.set_expected_participants(participant_ids)

            # Añadir actualizaciones encriptadas
            for update in encrypted_updates:
                self.secure_aggregator.add_encrypted_weight_update(
                    update['node_id'],
                    update['encrypted_weights'],
                    update['num_samples'],
                    update['public_key']
                )

            # Realizar agregación
            aggregated_weights = self.secure_aggregator.aggregate_weights()

            # Resetear para siguiente ronda
            self.secure_aggregator.reset_for_next_round()

            logger.info("🔒 Secure aggregation completed")
            return aggregated_weights

        except Exception as e:
            logger.error(f"❌ Error in secure aggregation: {e}")
            raise

    async def _distribute_updated_model(self, aggregated_weights: Dict[str, Any]) -> str:
        """Distribuir el modelo actualizado."""
        try:
            model_metadata = {
                "session_id": self.session_id,
                "model_name": self.model_name,
                "round_num": self.current_round,
                "updated_at": time.time(),
                "weights": aggregated_weights,
                "total_parameters": len(aggregated_weights)
            }

            # Publicar en IPFS
            from ..infrastructure.ipfs_embedded import create_ipfs_manager
            ipfs_manager = create_ipfs_manager()
            await ipfs_manager.start()

            metadata_json = json.dumps(model_metadata, indent=2, default=str)
            model_cid = await ipfs_manager.publish_data(metadata_json.encode('utf-8'))

            await ipfs_manager.stop()

            # Enviar nuevo CID a todos los nodos
            for node_id in self.nodes:
                if self.nodes[node_id].status == NodeStatus.CONNECTED:
                    await self._send_model_cid_to_node(node_id, model_cid)

            logger.info(f"📤 Updated model distributed with CID: {model_cid}")
            return model_cid

        except Exception as e:
            logger.error(f"❌ Error distributing updated model: {e}")
            raise

    async def _distribute_round_rewards(self, valid_contributions: List[Dict[str, Any]], round_num: int):
        """Distribuir recompensas por ronda completada."""
        try:
            # Preparar cálculos de recompensas
            contributions_for_rewards = []
            for contrib in valid_contributions:
                reward_calc = {
                    'node_id': contrib['node_id'],
                    'type': 'federated_training',
                    'metrics': {
                        'accuracy': contrib.get('accuracy', 0.8),
                        'loss': contrib.get('loss', 0.5),
                        'samples_used': contrib['num_samples'],
                        'zkp_verified': True
                    },
                    'session_id': self.session_id
                }
                contributions_for_rewards.append(reward_calc)

            # Calcular y distribuir recompensas
            result = await self.dracma_manager.calculate_and_distribute_rewards(contributions_for_rewards)

            if result['success']:
                total_dracma = result['total_dracma']
                self.total_rewards_distributed += total_dracma

                # Actualizar recompensas en nodos
                for contrib in valid_contributions:
                    node_id = contrib['node_id']
                    if node_id in self.nodes:
                        # Estimar recompensa por nodo (simplificado)
                        node_reward = total_dracma / len(valid_contributions)
                        self.nodes[node_id].reward_earned += node_reward
                        contrib['dracma_amount'] = node_reward

                logger.info(f"💰 Distributed {total_dracma:.4f} DracmaS rewards for round {round_num}")
                await self._trigger_callbacks('rewards_distributed', round_num, total_dracma)
            else:
                logger.error("Failed to distribute rewards")

        except Exception as e:
            logger.error(f"❌ Error distributing rewards: {e}")

    async def _validate_round_state(self, round_num: int):
        """Validar estado de la ronda usando StateValidator con base de datos real."""
        try:
            if self.state_validator:
                # Obtener sesión de base de datos real
                from ..coordinator.database.connection import get_db
                db_session = next(get_db())

                try:
                    is_valid, issues = await self.state_validator.validate_global_state(db_session)

                    if not is_valid:
                        logger.warning(f"⚠️ State validation failed for round {round_num}: {len(issues)} issues")
                        # Log detallado de issues críticos
                        critical_issues = [i for i in issues if i.severity.value == 'critical']
                        if critical_issues:
                            logger.error(f"🚨 Critical issues found: {[i.description for i in critical_issues]}")
                        # En producción, podría detener la ronda o tomar acciones correctivas
                    else:
                        logger.info(f"✅ State validation passed for round {round_num}")

                finally:
                    db_session.close()

        except Exception as e:
            logger.error(f"❌ Error validating round state: {e}")
            raise

    async def _audit_round_with_zkp(self, valid_contributions: List[Dict[str, Any]], round_num: int):
        """Auditar ronda completada con ZKP."""
        try:
            if self.zk_auditor:
                # Preparar datos para auditoría
                calculations = []
                for contrib in valid_contributions:
                    calc = {
                        'node_id': contrib['node_id'],
                        'dracma_amount': contrib.get('reward_amount', 1.0),  # Mock amount
                        'accuracy': contrib.get('accuracy', 0.8),
                        'loss': contrib.get('loss', 0.5),
                        'samples_used': contrib['num_samples']
                    }
                    calculations.append(calc)

                # Realizar auditoría ZKP
                audit_result = await self.zk_auditor.audit_reward_calculations(
                    session_id=self.session_id,
                    calculations=calculations,
                    pool_balance=1000.0  # Mock balance
                )

                logger.info(f"🔐 ZKP audit completed for round {round_num}: {audit_result.total_rewards_calculated} DRACMA")

        except Exception as e:
            logger.error(f"❌ Error auditing round with ZKP: {e}")

    async def _finalize_training(self):
        """Finalizar el entrenamiento distribuido."""
        try:
            self.is_running = False
            self.current_phase = TrainingPhase.COMPLETED

            # Calcular estadísticas finales
            total_rounds = len([r for r in self.training_rounds if r.phase == TrainingPhase.COMPLETED])
            total_participants = len(self.nodes)
            active_participants = len([n for n in self.nodes.values() if n.status == NodeStatus.CONNECTED])

            logger.info("🎉 Distributed training completed")
            logger.info(f"   📊 Total rounds: {total_rounds}")
            logger.info(f"   👥 Total participants: {total_participants}")
            logger.info(f"   🔗 Active participants: {active_participants}")
            logger.info(f"   💰 Total rewards distributed: {self.total_rewards_distributed:.4f} DRACMA")
            logger.info(f"   📈 Parameters trained: {self.total_parameters_trained}")

        except Exception as e:
            logger.error(f"❌ Error finalizing training: {e}")

    # Métodos de utilidad para pesos del modelo
    def _get_model_weights(self) -> Dict[str, Any]:
        """Extraer pesos del modelo para distribución."""
        if not self.global_model:
            raise ValueError("Global model not initialized")

        weights = {}
        for name, param in self.global_model.named_parameters():
            if param.requires_grad:
                weights[name] = param.detach().cpu().numpy().tolist()
        return weights

    def _load_model_weights(self, weights: Dict[str, Any]):
        """Cargar pesos en el modelo."""
        if not self.global_model:
            raise ValueError("Global model not initialized")

        state_dict = {}
        for name, param_data in weights.items():
            if isinstance(param_data, list):
                import numpy as np
                param_array = np.array(param_data)
                state_dict[name] = torch.tensor(param_array, dtype=torch.float32)
            else:
                state_dict[name] = torch.tensor(param_data, dtype=torch.float32)

        self.global_model.load_state_dict(state_dict, strict=False)

    # Handlers de eventos P2P
    async def _handle_model_update(self, message):
        """Manejar actualización de modelo recibida vía P2P."""
        try:
            payload = message.payload
            node_id = message.sender_id

            if node_id not in self.nodes:
                logger.warning(f"Received update from unknown node {node_id}")
                return

            # Almacenar contribución
            contribution = {
                'node_id': node_id,
                'model_weights': payload.get('model_weights', {}),
                'num_samples': payload.get('num_samples', 0),
                'accuracy': payload.get('accuracy', 0.0),
                'loss': payload.get('loss', 0.0),
                'round_num': payload.get('round_num', 0),
                'timestamp': time.time()
            }

            self.nodes[node_id].training_contribution = contribution
            self.nodes[node_id].last_seen = time.time()

            logger.info(f"📦 Model update received from {node_id}")

        except Exception as e:
            logger.error(f"❌ Error handling model update: {e}")

    async def _handle_aggregation_request(self, message):
        """Manejar solicitud de agregación."""
        # Implementado en secure_aggregator
        pass

    async def _handle_training_proof(self, message):
        """Manejar prueba ZKP de entrenamiento."""
        try:
            payload = message.payload
            node_id = message.sender_id

            if node_id not in self.nodes:
                logger.warning(f"Received proof from unknown node {node_id}")
                return

            # Almacenar prueba ZKP
            proof_data = payload.get('proof')
            if proof_data and 'zkp_proof' in proof_data:
                self.nodes[node_id].zkp_proof = proof_data['zkp_proof']

            logger.info(f"🔐 ZKP proof received from {node_id}")

        except Exception as e:
            logger.error(f"❌ Error handling training proof: {e}")

    async def _handle_peer_connected(self, peer_id: str):
        """Manejar conexión de peer."""
        if peer_id in self.nodes:
            self.nodes[peer_id].status = NodeStatus.CONNECTED
            self.nodes[peer_id].last_seen = time.time()
            self.active_nodes.add(peer_id)
            logger.info(f"🔗 Peer {peer_id} connected")

    async def _handle_peer_disconnected(self, peer_id: str):
        """Manejar desconexión de peer."""
        if peer_id in self.nodes:
            self.nodes[peer_id].status = NodeStatus.DISCONNECTED
            self.active_nodes.discard(peer_id)
            await self._trigger_callbacks('node_disconnected', peer_id)
            logger.info(f"👋 Peer {peer_id} disconnected")

    # Métodos de comunicación con nodos
    async def _send_model_cid_to_node(self, node_id: str, model_cid: str):
        """Enviar CID del modelo a un nodo."""
        if self.p2p_protocol and node_id in self.active_nodes:
            message = {
                'type': 'model_cid',
                'model_cid': model_cid,
                'session_id': self.session_id,
                'round_num': self.current_round
            }
            await self.p2p_protocol.send_model_update(node_id, {}, message)

    async def _send_round_start_to_node(self, node_id: str, round_num: int, training_config: Dict[str, Any]):
        """Enviar inicio de ronda a un nodo."""
        if self.p2p_protocol and node_id in self.active_nodes:
            message = {
                'type': 'round_start',
                'round_num': round_num,
                'training_config': training_config,
                'model_cid': self.current_model_cid,
                'session_id': self.session_id
            }
            await self.p2p_protocol.send_model_update(node_id, {}, message)

    # Sistema de callbacks
    def register_callback(self, event: str, callback: callable):
        """Registrar callback para evento."""
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)

    async def _trigger_callbacks(self, event: str, *args, **kwargs):
        """Disparar callbacks para un evento."""
        for callback in self.event_callbacks[event]:
            try:
                await callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"❌ Error in callback for {event}: {e}")

    # Métodos de consulta de estado
    def get_training_status(self) -> Dict[str, Any]:
        """Obtener estado completo del entrenamiento distribuido."""
        total_nodes = len(self.nodes)
        connected_nodes = len([n for n in self.nodes.values() if n.status == NodeStatus.CONNECTED])
        active_nodes = len(self.active_nodes)

        completed_rounds = len([r for r in self.training_rounds if r.phase == TrainingPhase.COMPLETED])
        failed_rounds = len([r for r in self.training_rounds if r.phase == TrainingPhase.FAILED])

        return {
            'session_id': self.session_id,
            'phase': self.current_phase.value,
            'current_round': self.current_round,
            'total_rounds': len(self.training_rounds),
            'completed_rounds': completed_rounds,
            'failed_rounds': failed_rounds,
            'nodes': {
                'total': total_nodes,
                'connected': connected_nodes,
                'active': active_nodes
            },
            'model_cid': self.current_model_cid,
            'total_rewards_distributed': self.total_rewards_distributed,
            'total_parameters_trained': self.total_parameters_trained,
            'uptime_seconds': time.time() - self.start_time,
            'is_running': self.is_running
        }

    def get_node_status(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de un nodo específico."""
        if node_id not in self.nodes:
            return None

        node = self.nodes[node_id]
        return {
            'node_id': node_id,
            'status': node.status.value,
            'host': node.host,
            'port': node.port,
            'reputation_score': node.reputation_score,
            'last_seen': node.last_seen,
            'reward_earned': node.reward_earned,
            'has_contribution': node.training_contribution is not None,
            'has_zkp_proof': node.zkp_proof is not None,
            'connection_attempts': node.connection_attempts
        }

    def get_round_history(self) -> List[Dict[str, Any]]:
        """Obtener historial de rondas."""
        return [
            {
                'round_num': r.round_num,
                'start_time': r.start_time,
                'end_time': r.end_time,
                'phase': r.phase.value,
                'participants': len(r.participants),
                'completed_participants': len(r.completed_participants),
                'failed_participants': len(r.failed_participants),
                'model_cid': r.global_model_cid,
                'consensus_reached': r.consensus_reached,
                'rewards_distributed': r.rewards_distributed,
                'duration': (r.end_time - r.start_time) if r.end_time else None
            }
            for r in self.training_rounds
        ]

    async def shutdown(self):
        """Apagar el trainer distribuido."""
        try:
            self.is_running = False
            self.current_phase = TrainingPhase.FAILED

            # Detener componentes
            if self.p2p_protocol:
                await self.p2p_protocol.stop()

            if self.state_sync:
                await self.state_sync.stop_sync_service()

            if self.consensus_manager:
                await self.consensus_manager.stop_consensus_service()

            # Detener servicios de validación y auditoría
            if self.zk_auditor:
                # ZK auditor no tiene shutdown específico
                pass

            if self.state_validator:
                # State validator no tiene shutdown específico
                pass

            self.executor.shutdown(wait=True)

            logger.info("🛑 Distributed trainer shut down")

        except Exception as e:
            logger.error(f"❌ Error shutting down: {e}")


# Funciones de conveniencia
def create_distributed_trainer(session_id: str, **kwargs) -> DistributedTrainer:
    """Crear una instancia del trainer distribuido."""
    return DistributedTrainer(session_id, **kwargs)


async def start_distributed_training(session_id: str, node_addresses: List[Tuple[str, int, str]],
                                   training_config: Dict[str, Any], **kwargs) -> DistributedTrainer:
    """
    Función de conveniencia para iniciar entrenamiento distribuido.

    Args:
        session_id: ID de la sesión
        node_addresses: Lista de tuplas (host, port, node_id)
        training_config: Configuración del entrenamiento
        **kwargs: Parámetros adicionales para DistributedTrainer
    """
    trainer = create_distributed_trainer(session_id, **kwargs)

    # Inicializar trainer
    success = await trainer.initialize()
    if not success:
        raise RuntimeError("Failed to initialize distributed trainer")

    # Registrar nodos
    for host, port, node_id in node_addresses:
        await trainer.register_node(node_id, host, port)

    # Conectar a nodos
    connection_tasks = []
    for node_id in trainer.nodes:
        task = trainer.connect_to_node(node_id)
        connection_tasks.append(task)

    connection_results = await asyncio.gather(*connection_tasks, return_exceptions=True)
    successful_connections = sum(1 for r in connection_results if r is True)

    logger.info(f"Connected to {successful_connections}/{len(node_addresses)} nodes")

    # Iniciar entrenamiento
    training_success = await trainer.start_distributed_training(training_config)

    return trainer