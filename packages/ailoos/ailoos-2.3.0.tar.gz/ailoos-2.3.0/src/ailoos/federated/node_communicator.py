"""
API de Comunicación entre Nodos para Federated Learning
Proporciona una interfaz de alto nivel para comunicación P2P entre nodos federados.
"""

import asyncio
import json
import time
import threading
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import logging

from ..core.logging import get_logger
from .p2p_protocol import P2PProtocol, PeerInfo, P2PMessage, P2PMessageType, ConnectionState
from .auto_healing import AutoHealingCoordinator

logger = get_logger(__name__)


class CommunicationState(Enum):
    """Estados de comunicación del nodo."""
    INITIALIZING = "initializing"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ACTIVE = "active"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class RoundPhase(Enum):
    """Fases de una ronda de entrenamiento."""
    WAITING = "waiting"
    COLLECTING_UPDATES = "collecting_updates"
    AGGREGATING = "aggregating"
    DISTRIBUTING = "distributing"
    COMPLETED = "completed"


@dataclass
class NodeUpdate:
    """Actualización de modelo de un nodo."""
    node_id: str
    round_num: int
    model_weights: Dict[str, Any]
    num_samples: int
    accuracy: float = 0.0
    loss: float = 0.0
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoundInfo:
    """Información de una ronda de entrenamiento."""
    round_num: int
    phase: RoundPhase
    participants: List[str]
    start_time: float
    deadline: Optional[float] = None
    collected_updates: Dict[str, NodeUpdate] = field(default_factory=dict)
    required_participants: int = 0


class NodeCommunicator:
    """
    API de alto nivel para comunicación entre nodos federados.
    Abstrae los detalles del protocolo P2P subyacente y proporciona
    una interfaz fácil de usar para el FederatedTrainer.
    """

    def __init__(self, node_id: str, host: str = "0.0.0.0", port: int = 8443,
                  cert_dir: str = "./certs", max_workers: int = 4,
                  auto_healing_coordinator: Optional[AutoHealingCoordinator] = None):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.cert_dir = cert_dir
        self.auto_healing_coordinator = auto_healing_coordinator

        # Estado de comunicación
        self.state = CommunicationState.INITIALIZING
        self.p2p_protocol: Optional[P2PProtocol] = None

        # Gestión de rondas
        self.current_round: Optional[RoundInfo] = None
        self.round_callbacks: Dict[str, Callable] = {}

        # Gestión de peers
        self.peer_states: Dict[str, Dict[str, Any]] = {}
        self.peer_health_monitor: Dict[str, float] = {}

        # Callbacks de eventos
        self.event_callbacks: Dict[str, List[Callable]] = {
            'peer_connected': [],
            'peer_disconnected': [],
            'round_started': [],
            'round_completed': [],
            'update_received': [],
            'model_distribution_received': [],  # Nuevo evento
            'error': []
        }

        # Thread safety
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None

        # Estadísticas
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'updates_sent': 0,
            'updates_received': 0,
            'rounds_completed': 0,
            'errors': 0,
            'start_time': time.time()
        }

        logger.info(f"🔗 NodeCommunicator initialized for node {node_id}")

    async def initialize(self) -> bool:
        """
        Inicializar el comunicador de nodos.
        Returns:
            True si la inicialización fue exitosa
        """
        try:
            with self._lock:
                if self.state != CommunicationState.INITIALIZING:
                    logger.warning(f"NodeCommunicator already initialized (state: {self.state.value})")
                    return True

                # Crear protocolo P2P
                self.p2p_protocol = P2PProtocol(
                    node_id=self.node_id,
                    host=self.host,
                    port=self.port,
                    cert_dir=self.cert_dir,
                    enable_tls=True
                )

                # Registrar handlers de mensajes
                self._register_message_handlers()

                # Iniciar protocolo P2P
                await self.p2p_protocol.start()

                self.state = CommunicationState.CONNECTED
                logger.info(f"✅ NodeCommunicator initialized successfully for node {self.node_id}")

                return True

        except Exception as e:
            logger.error(f"❌ Error initializing NodeCommunicator: {e}")
            self.state = CommunicationState.ERROR
            return False

    async def shutdown(self):
        """Apagar el comunicador de nodos."""
        try:
            with self._lock:
                if self.state in [CommunicationState.DISCONNECTED, CommunicationState.ERROR]:
                    return

                self.state = CommunicationState.DISCONNECTED

                # Detener protocolo P2P
                if self.p2p_protocol:
                    await self.p2p_protocol.stop()

                # Limpiar executor
                self._executor.shutdown(wait=True)

                logger.info(f"🛑 NodeCommunicator shutdown for node {self.node_id}")

        except Exception as e:
            logger.error(f"❌ Error shutting down NodeCommunicator: {e}")

    def _register_message_handlers(self):
        """Registrar handlers para mensajes P2P."""
        if not self.p2p_protocol:
            return

        # Handler para actualizaciones de modelo
        self.p2p_protocol.register_message_handler(
            P2PMessageType.MODEL_UPDATE,
            self._handle_model_update
        )

        # Handler para coordinación de rondas
        self.p2p_protocol.register_message_handler(
            P2PMessageType.AGGREGATION_REQUEST,
            self._handle_round_coordination
        )

        # Handler para respuestas de agregación
        self.p2p_protocol.register_message_handler(
            P2PMessageType.AGGREGATION_RESPONSE,
            self._handle_aggregation_response
        )
        
        # Handler para distribución de modelos (nuevo)
        self.p2p_protocol.register_message_handler(
            P2PMessageType.MODEL_UPDATE,  # Reutilizamos para distribución
            self._handle_model_distribution
        )

    async def connect_to_peers(self, peer_addresses: List[Tuple[str, int, str]]) -> bool:
        """
        Conectar a peers específicos.

        Args:
            peer_addresses: Lista de tuplas (host, port, node_id)

        Returns:
            True si al menos una conexión fue exitosa
        """
        try:
            if not self.p2p_protocol:
                logger.error("P2P protocol not initialized")
                return False

            success_count = 0

            for host, port, node_id in peer_addresses:
                peer_info = PeerInfo(
                    node_id=node_id,
                    host=host,
                    port=port,
                    public_key=b''  # Se obtendrá durante handshake
                )

                # Añadir peer a la lista conocida
                self.p2p_protocol.add_peer(peer_info)

                # Intentar conectar
                if await self.p2p_protocol.connect_to_peer(peer_info):
                    success_count += 1
                    self._update_peer_state(node_id, 'connected', time.time())
                    await self._trigger_event('peer_connected', node_id)
                else:
                    self._update_peer_state(node_id, 'disconnected', time.time())
                    logger.warning(f"Failed to connect to peer {node_id}")

            self.state = CommunicationState.ACTIVE if success_count > 0 else CommunicationState.CONNECTED

            logger.info(f"Connected to {success_count}/{len(peer_addresses)} peers")
            return success_count > 0

        except Exception as e:
            logger.error(f"Error connecting to peers: {e}")
            return False

    async def send_model_update(self, peer_id: str, update: NodeUpdate) -> bool:
        """
        Enviar actualización de modelo a un peer.

        Args:
            peer_id: ID del peer destino
            update: Actualización a enviar

        Returns:
            True si el envío fue exitoso
        """
        try:
            if not self.p2p_protocol:
                return False

            # Convertir NodeUpdate a payload
            payload = {
                "model_weights": update.model_weights,
                "num_samples": update.num_samples,
                "round_num": update.round_num,
                "accuracy": update.accuracy,
                "loss": update.loss,
                "metadata": update.metadata,
                "session_id": update.metadata.get("session_id")
            }

            # Enviar vía P2P
            success = await self.p2p_protocol.send_model_update(
                peer_id=peer_id,
                model_weights=update.model_weights,
                metadata={
                    "round_num": update.round_num,
                    "num_samples": update.num_samples,
                    "accuracy": update.accuracy,
                    "loss": update.loss,
                    "session_id": update.metadata.get("session_id"),
                    **update.metadata
                }
            )

            if success:
                self.stats['updates_sent'] += 1
                self.stats['messages_sent'] += 1
                logger.info(f"📤 Model update sent to {peer_id} (round {update.round_num})")
            else:
                logger.warning(f"Failed to send model update to {peer_id}")

            return success

        except Exception as e:
            logger.error(f"Error sending model update to {peer_id}: {e}")
            self.stats['errors'] += 1
            return False

    async def broadcast_model_update(self, update: NodeUpdate,
                                   exclude_peers: List[str] = None) -> int:
        """
        Broadcast actualización de modelo a todos los peers conectados.

        Args:
            update: Actualización a broadcast
            exclude_peers: Lista de peers a excluir

        Returns:
            Número de peers que recibieron la actualización
        """
        try:
            if not self.p2p_protocol:
                return 0

            exclude_peers = exclude_peers or []
            connected_peers = self.p2p_protocol.get_connected_peers()
            target_peers = [p for p in connected_peers if p not in exclude_peers]

            success_count = 0
            for peer_id in target_peers:
                if await self.send_model_update(peer_id, update):
                    success_count += 1

            logger.info(f"📢 Model update broadcasted to {success_count}/{len(target_peers)} peers")
            return success_count

        except Exception as e:
            logger.error(f"Error broadcasting model update: {e}")
            return 0

    async def start_round(self, round_num: int, participants: List[str],
                         deadline_seconds: int = 300) -> bool:
        """
        Iniciar una nueva ronda de entrenamiento.

        Args:
            round_num: Número de ronda
            participants: Lista de participantes
            deadline_seconds: Timeout en segundos

        Returns:
            True si la ronda se inició correctamente
        """
        try:
            with self._lock:
                if self.current_round and self.current_round.phase != RoundPhase.COMPLETED:
                    logger.warning(f"Round {self.current_round.round_num} still active")
                    return False

                # Crear nueva ronda
                self.current_round = RoundInfo(
                    round_num=round_num,
                    phase=RoundPhase.WAITING,
                    participants=participants.copy(),
                    start_time=time.time(),
                    deadline=time.time() + deadline_seconds,
                    required_participants=len(participants)
                )

                # Cambiar a fase de recolección
                self.current_round.phase = RoundPhase.COLLECTING_UPDATES

                # Notificar a participantes
                await self._notify_round_start(participants)

                # Trigger event
                await self._trigger_event('round_started', self.current_round)

                logger.info(f"🎯 Round {round_num} started with {len(participants)} participants")
                return True

        except Exception as e:
            logger.error(f"Error starting round {round_num}: {e}")
            return False

    async def _notify_round_start(self, participants: List[str]):
        """Notificar inicio de ronda a participantes."""
        try:
            for participant_id in participants:
                message = P2PMessage(
                    message_id=f"round_start_{self.current_round.round_num}_{self.node_id}_{int(time.time())}",
                    message_type=P2PMessageType.AGGREGATION_REQUEST,
                    sender_id=self.node_id,
                    receiver_id=participant_id,
                    timestamp=time.time(),
                    payload={
                        "round_num": self.current_round.round_num,
                        "action": "start_collection",
                        "deadline": self.current_round.deadline,
                        "participants": self.current_round.participants
                    }
                )

                # Firmar mensaje
                message.signature = self.p2p_protocol._sign_message(message)

                await self.p2p_protocol._send_message_to_peer(participant_id, message)

        except Exception as e:
            logger.error(f"Error notifying round start: {e}")

    async def submit_round_update(self, update: NodeUpdate) -> bool:
        """
        Enviar actualización para la ronda actual.

        Args:
            update: Actualización del nodo

        Returns:
            True si se aceptó la actualización
        """
        try:
            with self._lock:
                if not self.current_round:
                    logger.warning("No active round to submit update")
                    return False

                if self.current_round.phase != RoundPhase.COLLECTING_UPDATES:
                    logger.warning(f"Round not in collecting phase (current: {self.current_round.phase.value})")
                    return False

                if update.node_id not in self.current_round.participants:
                    logger.warning(f"Node {update.node_id} not in round participants")
                    return False

                # Almacenar actualización
                self.current_round.collected_updates[update.node_id] = update

                # Verificar si tenemos todas las actualizaciones
                if len(self.current_round.collected_updates) >= self.current_round.required_participants:
                    await self._complete_round_collection()

                logger.info(f"✅ Update submitted by {update.node_id} for round {update.round_num}")
                return True

        except Exception as e:
            logger.error(f"Error submitting round update: {e}")
            return False

    async def _complete_round_collection(self):
        """Completar recolección de actualizaciones de ronda."""
        try:
            with self._lock:
                if not self.current_round:
                    return

                self.current_round.phase = RoundPhase.AGGREGATING

                # Trigger event
                await self._trigger_event('round_completed', self.current_round)

                # Reset para siguiente ronda
                self.current_round = None
                self.stats['rounds_completed'] += 1

                logger.info("✅ Round collection completed")

        except Exception as e:
            logger.error(f"Error completing round collection: {e}")

    async def _handle_model_update(self, message: P2PMessage):
        """Manejar recepción de actualización de modelo."""
        try:
            payload = message.payload

            # Record heartbeat for auto-healing
            if self.auto_healing_coordinator:
                response_time = time.time() - message.timestamp if hasattr(message, 'timestamp') else 0.0
                self.auto_healing_coordinator.health_monitor.record_heartbeat(message.sender_id, response_time)

            # Crear NodeUpdate desde payload
            update = NodeUpdate(
                node_id=message.sender_id,
                round_num=payload.get("round_num", 0),
                model_weights=payload.get("model_weights", {}),
                num_samples=payload.get("num_samples", 0),
                accuracy=payload.get("accuracy", 0.0),
                loss=payload.get("loss", 0.0),
                metadata=payload.get("metadata", {})
            )

            self.stats['updates_received'] += 1
            self.stats['messages_received'] += 1

            # Trigger event
            await self._trigger_event('update_received', update)

            # Si hay ronda activa, submit automáticamente
            if self.current_round and update.round_num == self.current_round.round_num:
                await self.submit_round_update(update)

            logger.info(f"📦 Model update received from {message.sender_id}")

        except Exception as e:
            logger.error(f"Error handling model update: {e}")
            self.stats['errors'] += 1

    async def _handle_round_coordination(self, message: P2PMessage):
        """Manejar mensajes de coordinación de rondas."""
        try:
            payload = message.payload

            if payload.get("action") == "start_collection":
                # Iniciar recolección local
                round_num = payload.get("round_num", 0)
                participants = payload.get("participants", [])
                deadline = payload.get("deadline")

                with self._lock:
                    self.current_round = RoundInfo(
                        round_num=round_num,
                        phase=RoundPhase.COLLECTING_UPDATES,
                        participants=participants,
                        start_time=time.time(),
                        deadline=deadline,
                        required_participants=len(participants)
                    )

                logger.info(f"🎯 Local round {round_num} started by coordinator {message.sender_id}")

        except Exception as e:
            logger.error(f"Error handling round coordination: {e}")

    async def _handle_aggregation_response(self, message: P2PMessage):
        """Manejar respuestas de agregación."""
        try:
            payload = message.payload

            # Trigger callback si existe
            callback = self.round_callbacks.get("aggregation_complete")
            if callback:
                await callback(payload)

            logger.info(f"🔄 Aggregation response received from {message.sender_id}")

        except Exception as e:
            logger.error(f"Error handling aggregation response: {e}")

    async def _handle_model_distribution(self, message: P2PMessage):
        """
        Manejar notificación de distribución de modelo.
        
        Cuando un nodo recibe este mensaje, debe descargar el modelo desde IPFS.
        """
        try:
            payload = message.payload
            
            # Verificar que sea un mensaje de distribución
            if payload.get("action") != "model_distribution":
                # Si no es distribución, manejar como update regular
                await self._handle_model_update(message)
                return
            
            version_id = payload.get("version_id")
            model_cid = payload.get("model_cid")
            metadata_cid = payload.get("metadata_cid")
            expected_hash = payload.get("expected_hash")
            
            logger.info(f"📦 Model distribution notification received for version {version_id}")
            logger.info(f"   Model CID: {model_cid}")
            logger.info(f"   Metadata CID: {metadata_cid}")
            
            # Trigger callback para que el nodo descargue el modelo
            await self._trigger_event('model_distribution_received', {
                'version_id': version_id,
                'model_cid': model_cid,
                'metadata_cid': metadata_cid,
                'expected_hash': expected_hash,
                'sender_id': message.sender_id
            })
            
            # El nodo debe:
            # 1. Descargar el modelo desde IPFS usando model_cid
            # 2. Verificar el hash
            # 3. Enviar ACK al coordinator
            
        except Exception as e:
            logger.error(f"Error handling model distribution: {e}")
            self.stats['errors'] += 1

    async def send_model_distribution_notification(self, node_id: str, version_id: str, 
                                                    model_cid: str, metadata_cid: str,
                                                    expected_hash: str) -> bool:
        """
        Enviar notificación de distribución de modelo a un nodo.
        
        Args:
            node_id: ID del nodo destino
            version_id: ID de la versión del modelo
            model_cid: CID del modelo en IPFS
            metadata_cid: CID de los metadatos en IPFS
            expected_hash: Hash esperado para verificación
            
        Returns:
            True si la notificación se envió correctamente
        """
        try:
            if not self.p2p_protocol:
                return False
            
            message = P2PMessage(
                message_id=f"model_dist_{version_id}_{self.node_id}_{int(time.time())}",
                message_type=P2PMessageType.MODEL_UPDATE,
                sender_id=self.node_id,
                receiver_id=node_id,
                timestamp=time.time(),
                payload={
                    "action": "model_distribution",
                    "version_id": version_id,
                    "model_cid": model_cid,
                    "metadata_cid": metadata_cid,
                    "expected_hash": expected_hash
                }
            )
            
            # Firmar mensaje
            message.signature = self.p2p_protocol._sign_message(message)
            
            # Enviar
            success = await self.p2p_protocol._send_message_to_peer(node_id, message)
            
            if success:
                self.stats['messages_sent'] += 1
                logger.info(f"📤 Model distribution notification sent to {node_id} for version {version_id}")
            else:
                logger.warning(f"Failed to send distribution notification to {node_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending distribution notification to {node_id}: {e}")
            return False

    def _update_peer_state(self, peer_id: str, state: str, timestamp: float):
        """Actualizar estado de un peer."""
        with self._lock:
            if peer_id not in self.peer_states:
                self.peer_states[peer_id] = {}

            self.peer_states[peer_id].update({
                'state': state,
                'last_update': timestamp,
                'last_seen': timestamp
            })

    async def _trigger_event(self, event_type: str, data: Any):
        """Trigger event callbacks."""
        try:
            callbacks = self.event_callbacks.get(event_type, [])
            for callback in callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        # Ejecutar en thread pool si no es coroutine
                        await asyncio.get_event_loop().run_in_executor(
                            self._executor, callback, data
                        )
                except Exception as e:
                    logger.error(f"Error in event callback for {event_type}: {e}")

        except Exception as e:
            logger.error(f"Error triggering event {event_type}: {e}")

    def register_event_callback(self, event_type: str, callback: Callable):
        """
        Registrar callback para eventos.

        Args:
            event_type: Tipo de evento ('peer_connected', 'update_received', etc.)
            callback: Función callback
        """
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []

        self.event_callbacks[event_type].append(callback)
        logger.debug(f"Registered callback for event {event_type}")

    def get_peer_status(self, peer_id: str) -> Dict[str, Any]:
        """Obtener estado de un peer."""
        with self._lock:
            return self.peer_states.get(peer_id, {}).copy()

    def get_connected_peers(self) -> List[str]:
        """Obtener lista de peers conectados."""
        if not self.p2p_protocol:
            return []

        return self.p2p_protocol.get_connected_peers()

    def get_communication_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de comunicación."""
        with self._lock:
            base_stats = self.stats.copy()

            if self.p2p_protocol:
                p2p_stats = self.p2p_protocol.get_stats()
                base_stats.update({
                    'p2p_messages_sent': p2p_stats.get('messages_sent', 0),
                    'p2p_messages_received': p2p_stats.get('messages_received', 0),
                    'active_connections': p2p_stats.get('active_connections', 0),
                    'known_peers': p2p_stats.get('known_peers', 0)
                })

            return base_stats

    def get_current_round_info(self) -> Optional[Dict[str, Any]]:
        """Obtener información de la ronda actual."""
        with self._lock:
            if not self.current_round:
                return None

            return {
                'round_num': self.current_round.round_num,
                'phase': self.current_round.phase.value,
                'participants': self.current_round.participants.copy(),
                'collected_updates': len(self.current_round.collected_updates),
                'required_participants': self.current_round.required_participants,
                'start_time': self.current_round.start_time,
                'deadline': self.current_round.deadline,
                'time_remaining': max(0, (self.current_round.deadline or 0) - time.time())
            }

    # Métodos thread-safe para uso desde FederatedTrainer

    def initialize_sync(self) -> bool:
        """Inicialización síncrona (thread-safe)."""
        try:
            # Crear event loop si no existe
            if not self._event_loop:
                self._event_loop = asyncio.new_event_loop()
                self._loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
                self._loop_thread.start()

            # Ejecutar inicialización en el loop
            future = asyncio.run_coroutine_threadsafe(self.initialize(), self._event_loop)
            return future.result(timeout=30)

        except Exception as e:
            logger.error(f"Error in sync initialization: {e}")
            return False

    def _run_event_loop(self):
        """Ejecutar event loop en thread separado."""
        asyncio.set_event_loop(self._event_loop)
        self._event_loop.run_forever()

    def shutdown_sync(self):
        """Apagado síncrono (thread-safe)."""
        try:
            if self._event_loop:
                future = asyncio.run_coroutine_threadsafe(self.shutdown(), self._event_loop)
                future.result(timeout=10)

                # Detener loop
                self._event_loop.stop()
                if self._loop_thread:
                    self._loop_thread.join(timeout=5)

        except Exception as e:
            logger.error(f"Error in sync shutdown: {e}")

    def send_model_update_sync(self, peer_id: str, update: NodeUpdate) -> bool:
        """Envío síncrono de actualización (thread-safe)."""
        try:
            future = asyncio.run_coroutine_threadsafe(
                self.send_model_update(peer_id, update), self._event_loop
            )
            return future.result(timeout=10)
        except Exception as e:
            logger.error(f"Error in sync send: {e}")
            return False

    def start_round_sync(self, round_num: int, participants: List[str],
                        deadline_seconds: int = 300) -> bool:
        """Inicio síncrono de ronda (thread-safe)."""
        try:
            future = asyncio.run_coroutine_threadsafe(
                self.start_round(round_num, participants, deadline_seconds), self._event_loop
            )
            return future.result(timeout=10)
        except Exception as e:
            logger.error(f"Error in sync round start: {e}")
            return False


# Funciones de conveniencia

def create_node_communicator(node_id: str, **kwargs) -> NodeCommunicator:
    """Crear instancia del comunicador de nodos."""
    return NodeCommunicator(node_id, **kwargs)


async def initialize_communicator(communicator: NodeCommunicator) -> bool:
    """Inicializar comunicador de manera asíncrona."""
    return await communicator.initialize()