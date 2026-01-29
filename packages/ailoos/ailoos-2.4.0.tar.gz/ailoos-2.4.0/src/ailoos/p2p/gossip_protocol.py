"""
Gossip Protocol para consenso de metadatos críticos en P2P.
Implementa propagación eficiente de metadatos (claves Cosign, configuración, listas de nodos trusted)
usando gossip protocol ligero con consenso eventual.
"""

import asyncio
import json
import time
import random
import hashlib
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import secrets

from ..core.logging import get_logger
from .p2p_client import P2PClient

logger = get_logger(__name__)


class GossipMessageType(Enum):
    """Tipos de mensajes gossip."""
    METADATA_UPDATE = "metadata_update"
    METADATA_REQUEST = "metadata_request"
    METADATA_DIGEST = "metadata_digest"
    METADATA_SYNC = "metadata_sync"
    HEARTBEAT = "gossip_heartbeat"


class MetadataType(Enum):
    """Tipos de metadatos críticos."""
    COSIGN_KEYS = "cosign_keys"
    CONFIGURATION = "configuration"
    TRUSTED_NODES = "trusted_nodes"
    NODE_CERTIFICATES = "node_certificates"
    NETWORK_TOPOLOGY = "network_topology"


@dataclass
class GossipMessage:
    """Mensaje gossip para metadatos."""
    message_id: str
    message_type: GossipMessageType
    sender_id: str
    metadata_type: MetadataType
    payload: Dict[str, Any]
    timestamp: float
    ttl: int = 32  # Time to live
    hop_count: int = 0
    signature: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para serialización."""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "sender_id": self.sender_id,
            "metadata_type": self.metadata_type.value,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
            "hop_count": self.hop_count,
            "signature": self.signature
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GossipMessage':
        """Crear desde diccionario."""
        return cls(
            message_id=data["message_id"],
            message_type=GossipMessageType(data["message_type"]),
            sender_id=data["sender_id"],
            metadata_type=MetadataType(data["metadata_type"]),
            payload=data["payload"],
            timestamp=data["timestamp"],
            ttl=data.get("ttl", 32),
            hop_count=data.get("hop_count", 0),
            signature=data.get("signature")
        )

    def is_expired(self) -> bool:
        """Verificar si el mensaje expiró."""
        return time.time() - self.timestamp > 300  # 5 minutos


@dataclass
class MetadataEntry:
    """Entrada de metadatos con versión y timestamp."""
    key: str
    value: Any
    version: int
    timestamp: float
    source_node: str
    signature: Optional[str] = None
    ttl: int = 3600  # 1 hora por defecto
    consensus_votes: int = 1  # Votos para consenso

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            "key": self.key,
            "value": self.value,
            "version": self.version,
            "timestamp": self.timestamp,
            "source_node": self.source_node,
            "signature": self.signature,
            "ttl": self.ttl,
            "consensus_votes": self.consensus_votes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MetadataEntry':
        """Crear desde diccionario."""
        return cls(
            key=data["key"],
            value=data["value"],
            version=data["version"],
            timestamp=data["timestamp"],
            source_node=data["source_node"],
            signature=data.get("signature"),
            ttl=data.get("ttl", 3600),
            consensus_votes=data.get("consensus_votes", 1)
        )

    def is_expired(self) -> bool:
        """Verificar si la entrada expiró."""
        return time.time() - self.timestamp > self.ttl

    def get_hash(self) -> str:
        """Obtener hash del contenido para comparación."""
        content = f"{self.key}:{self.value}:{self.version}:{self.timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class ConsensusVote:
    """Voto para consenso de metadatos."""
    key: str
    value_hash: str
    version: int
    voter_node: str
    timestamp: float
    signature: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value_hash": self.value_hash,
            "version": self.version,
            "voter_node": self.voter_node,
            "timestamp": self.timestamp,
            "signature": self.signature
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConsensusVote':
        return cls(
            key=data["key"],
            value_hash=data["value_hash"],
            version=data["version"],
            voter_node=data["voter_node"],
            timestamp=data["timestamp"],
            signature=data.get("signature")
        )


@dataclass
class ConsensusState:
    """Estado de consenso para una clave de metadatos."""
    key: str
    candidates: Dict[str, List[ConsensusVote]]  # hash -> votes
    start_time: float
    timeout: float
    min_votes: int

    def add_vote(self, vote: ConsensusVote):
        """Añadir voto al consenso."""
        if vote.value_hash not in self.candidates:
            self.candidates[vote.value_hash] = []
        self.candidates[vote.value_hash].append(vote)

    def get_winner(self) -> Optional[Tuple[str, int]]:
        """Obtener el candidato ganador (hash, votos)."""
        if not self.candidates:
            return None

        # Encontrar candidato con más votos
        winner_hash = None
        max_votes = 0

        for value_hash, votes in self.candidates.items():
            if len(votes) > max_votes:
                max_votes = len(votes)
                winner_hash = value_hash

        return (winner_hash, max_votes) if winner_hash else None

    def has_consensus(self) -> bool:
        """Verificar si hay consenso."""
        winner = self.get_winner()
        return winner is not None and winner[1] >= self.min_votes

    def is_expired(self) -> bool:
        """Verificar si el consenso expiró."""
        return time.time() - self.start_time > self.timeout


@dataclass
class GossipConfig:
    """Configuración del protocolo gossip."""
    # Parámetros de gossip
    gossip_interval: float = 1.0  # segundos entre gossips
    fanout: int = 3  # número de peers a contactar por gossip
    max_message_hops: int = 32  # máximo número de saltos
    message_ttl: int = 300  # TTL de mensajes en segundos

    # Parámetros de consenso
    min_consensus_peers: int = 3  # mínimo peers para consenso
    consensus_timeout: float = 30.0  # timeout para consenso
    consensus_quorum: float = 0.67  # quorum requerido (67%)
    metadata_sync_interval: float = 60.0  # intervalo de sincronización

    # Parámetros de anti-entropía
    anti_entropy_interval: float = 300.0  # 5 minutos
    digest_size: int = 100  # tamaño máximo del digest

    # Límites
    max_metadata_entries: int = 10000
    max_pending_messages: int = 1000
    max_consensus_states: int = 1000


class GossipProtocol:
    """
    Protocolo Gossip para consenso de metadatos críticos.
    Implementa push-pull gossip con anti-entropía para asegurar consistencia eventual.
    """

    def __init__(self, node_id: str, p2p_client: P2PClient, config: Optional[GossipConfig] = None):
        self.node_id = node_id
        self.p2p_client = p2p_client
        self.config = config or GossipConfig()

        # Estado del protocolo
        self.is_running = False
        self.metadata_store: Dict[str, MetadataEntry] = {}
        self.pending_messages: Dict[str, GossipMessage] = {}
        self.message_history: Set[str] = set()  # IDs de mensajes procesados

        # Sistema de consenso
        self.consensus_states: Dict[str, ConsensusState] = {}  # key -> ConsensusState
        self.consensus_votes: Dict[str, Dict[str, ConsensusVote]] = {}  # key -> {node_id -> vote}

        # Tareas de background
        self.gossip_task: Optional[asyncio.Task] = None
        self.anti_entropy_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        self.consensus_task: Optional[asyncio.Task] = None

        # Callbacks
        self.metadata_callbacks: Dict[MetadataType, List[Callable]] = {}
        self.consensus_callbacks: Dict[str, Callable] = {}

        # Estadísticas
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "metadata_updates": 0,
            "consensus_achieved": 0,
            "gossip_rounds": 0,
            "anti_entropy_rounds": 0
        }

        # Registrar handlers en P2P client
        self._register_p2p_handlers()

        logger.info(f"🗣️ GossipProtocol initialized for node {node_id}")

    def _register_p2p_handlers(self):
        """Registrar handlers de mensajes gossip en el cliente P2P."""
        self.p2p_client.register_message_callback("gossip", self._handle_gossip_message)

    async def start(self):
        """Iniciar el protocolo gossip."""
        if self.is_running:
            return

        self.is_running = True

        # Iniciar tareas de background
        self.gossip_task = asyncio.create_task(self._gossip_loop())
        self.anti_entropy_task = asyncio.create_task(self._anti_entropy_loop())
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.consensus_task = asyncio.create_task(self._consensus_loop())

        logger.info(f"🚀 GossipProtocol started for node {self.node_id}")

    async def stop(self):
        """Detener el protocolo gossip."""
        if not self.is_running:
            return

        self.is_running = False

        # Cancelar tareas
        if self.gossip_task:
            self.gossip_task.cancel()
        if self.anti_entropy_task:
            self.anti_entropy_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()
        if self.consensus_task:
            self.consensus_task.cancel()

        # Esperar que terminen
        try:
            await asyncio.gather(
                self.gossip_task,
                self.anti_entropy_task,
                self.cleanup_task,
                return_exceptions=True
            )
        except asyncio.CancelledError:
            pass

        logger.info(f"🛑 GossipProtocol stopped for node {self.node_id}")

    async def update_metadata(self, metadata_type: MetadataType, key: str, value: Any,
                            source_node: Optional[str] = None) -> bool:
        """
        Actualizar metadatos y propagar vía gossip.

        Args:
            metadata_type: Tipo de metadatos
            key: Clave del metadato
            value: Valor del metadato
            source_node: Nodo origen (None para local)

        Returns:
            True si se actualizó correctamente
        """
        try:
            source_node = source_node or self.node_id

            # Verificar si ya tenemos una versión más reciente
            existing = self.metadata_store.get(key)
            if existing and existing.version >= self._get_next_version(key):
                return False

            # Crear nueva entrada
            entry = MetadataEntry(
                key=key,
                value=value,
                version=self._get_next_version(key),
                timestamp=time.time(),
                source_node=source_node
            )

            # Almacenar localmente
            self.metadata_store[key] = entry
            self.stats["metadata_updates"] += 1

            # Trigger callbacks
            await self._trigger_metadata_callback(metadata_type, key, entry)

            # Propagar vía gossip
            await self._gossip_metadata_update(metadata_type, entry)

            logger.debug(f"📝 Metadata updated: {metadata_type.value}/{key} v{entry.version}")
            return True

        except Exception as e:
            logger.error(f"❌ Error updating metadata {key}: {e}")
            return False

    async def get_metadata(self, key: str) -> Optional[MetadataEntry]:
        """Obtener metadatos por clave."""
        entry = self.metadata_store.get(key)
        if entry and not entry.is_expired():
            return entry
        return None

    async def get_metadata_by_type(self, metadata_type: MetadataType) -> Dict[str, MetadataEntry]:
        """Obtener todos los metadatos de un tipo."""
        result = {}
        prefix = f"{metadata_type.value}."

        for key, entry in self.metadata_store.items():
            if key.startswith(prefix) and not entry.is_expired():
                result[key] = entry

        return result

    async def request_metadata_consensus(self, key: str, timeout: Optional[float] = None) -> Optional[MetadataEntry]:
        """
        Solicitar consenso para un metadato específico.

        Args:
            key: Clave del metadato
            timeout: Timeout para consenso

        Returns:
            Entrada consensuada o None
        """
        timeout = timeout or self.config.consensus_timeout

        # Iniciar proceso de consenso
        await self._initiate_consensus(key, timeout)

        # Esperar consenso
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Verificar si tenemos consenso
            consensus_entry = await self._check_consensus(key)
            if consensus_entry:
                self.stats["consensus_achieved"] += 1
                return consensus_entry

            await asyncio.sleep(0.1)

        logger.warning(f"⚠️ Consensus timeout for metadata {key}")
        return None

    def register_metadata_callback(self, metadata_type: MetadataType, callback: Callable):
        """Registrar callback para actualizaciones de metadatos."""
        if metadata_type not in self.metadata_callbacks:
            self.metadata_callbacks[metadata_type] = []

        self.metadata_callbacks[metadata_type].append(callback)
        logger.debug(f"Registered metadata callback for {metadata_type.value}")

    def register_consensus_callback(self, key: str, callback: Callable):
        """Registrar callback para consenso de metadatos."""
        self.consensus_callbacks[key] = callback
        logger.debug(f"Registered consensus callback for {key}")

    # ==================== ALGORITMO GOSSIP ====================

    async def _gossip_loop(self):
        """Loop principal de gossip."""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.gossip_interval)

                # Seleccionar peers aleatorios
                peers = self._select_gossip_peers()
                if not peers:
                    continue

                # Enviar gossip a peers seleccionados
                for peer_id in peers:
                    await self._send_gossip_to_peer(peer_id)

                self.stats["gossip_rounds"] += 1

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in gossip loop: {e}")
                await asyncio.sleep(1.0)

    async def _anti_entropy_loop(self):
        """Loop de anti-entropía para sincronización completa."""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.anti_entropy_interval)

                # Seleccionar peer para anti-entropía
                peer = self._select_anti_entropy_peer()
                if peer:
                    await self._perform_anti_entropy(peer)

                self.stats["anti_entropy_rounds"] += 1

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in anti-entropy loop: {e}")
                await asyncio.sleep(5.0)

    async def _cleanup_loop(self):
        """Loop de limpieza de metadatos expirados."""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Cada 5 minutos

                # Limpiar metadatos expirados
                expired_keys = []
                for key, entry in self.metadata_store.items():
                    if entry.is_expired():
                        expired_keys.append(key)

                for key in expired_keys:
                    del self.metadata_store[key]

                # Limpiar mensajes pendientes expirados
                expired_messages = []
                for msg_id, message in self.pending_messages.items():
                    if message.is_expired():
                        expired_messages.append(msg_id)

                for msg_id in expired_messages:
                    del self.pending_messages[msg_id]

                # Limpiar estados de consenso expirados
                expired_consensus = []
                for key, state in self.consensus_states.items():
                    if state.is_expired():
                        expired_consensus.append(key)

                for key in expired_consensus:
                    del self.consensus_states[key]
                    if key in self.consensus_votes:
                        del self.consensus_votes[key]

                if expired_keys or expired_messages or expired_consensus:
                    logger.debug(f"🧹 Cleaned up {len(expired_keys)} expired metadata entries, {len(expired_messages)} messages, and {len(expired_consensus)} consensus states")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in cleanup loop: {e}")

    async def _consensus_loop(self):
        """Loop de verificación de consenso."""
        while self.is_running:
            try:
                await asyncio.sleep(2.0)  # Verificar cada 2 segundos

                # Verificar consensos pendientes
                completed_consensus = []
                for key, state in self.consensus_states.items():
                    if state.has_consensus():
                        winner_hash, votes = state.get_winner()
                        await self._resolve_consensus(key, winner_hash, votes)
                        completed_consensus.append(key)
                    elif state.is_expired():
                        # Consensus expirado, usar valor local si existe
                        local_entry = self.metadata_store.get(key)
                        if local_entry:
                            await self._resolve_consensus(key, local_entry.get_hash(), local_entry.consensus_votes)
                        completed_consensus.append(key)

                # Limpiar consensos completados
                for key in completed_consensus:
                    if key in self.consensus_states:
                        del self.consensus_states[key]
                    if key in self.consensus_votes:
                        del self.consensus_votes[key]

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in consensus loop: {e}")
                await asyncio.sleep(1.0)

    def _select_gossip_peers(self) -> List[str]:
        """Seleccionar peers para gossip (fanout aleatorio)."""
        connected_peers = self.p2p_client.get_connected_peers()
        if len(connected_peers) <= self.config.fanout:
            return connected_peers

        return random.sample(connected_peers, self.config.fanout)

    def _select_anti_entropy_peer(self) -> Optional[str]:
        """Seleccionar peer para anti-entropía."""
        connected_peers = self.p2p_client.get_connected_peers()
        return random.choice(connected_peers) if connected_peers else None

    async def _send_gossip_to_peer(self, peer_id: str):
        """Enviar gossip a un peer específico."""
        try:
            # Crear mensaje de digest (push-pull)
            digest = self._create_metadata_digest()

            message = GossipMessage(
                message_id=f"gossip_{secrets.token_hex(8)}",
                message_type=GossipMessageType.METADATA_DIGEST,
                sender_id=self.node_id,
                metadata_type=MetadataType.CONFIGURATION,  # Tipo genérico
                payload={"digest": digest, "node_id": self.node_id},
                timestamp=time.time()
            )

            # Enviar vía P2P client
            success = await self.p2p_client.send_message(peer_id, message.to_dict())
            if success:
                self.stats["messages_sent"] += 1

        except Exception as e:
            logger.error(f"❌ Error sending gossip to {peer_id}: {e}")

    async def _perform_anti_entropy(self, peer_id: str):
        """Realizar anti-entropía con un peer."""
        try:
            # Solicitar digest completo del peer
            message = GossipMessage(
                message_id=f"anti_entropy_{secrets.token_hex(8)}",
                message_type=GossipMessageType.METADATA_REQUEST,
                sender_id=self.node_id,
                metadata_type=MetadataType.CONFIGURATION,
                payload={"request_type": "full_sync"},
                timestamp=time.time()
            )

            success = await self.p2p_client.send_message(peer_id, message.to_dict())
            if success:
                self.stats["messages_sent"] += 1

        except Exception as e:
            logger.error(f"❌ Error performing anti-entropy with {peer_id}: {e}")

    async def _gossip_metadata_update(self, metadata_type: MetadataType, entry: MetadataEntry):
        """Propagar actualización de metadatos vía gossip."""
        try:
            message = GossipMessage(
                message_id=f"update_{secrets.token_hex(8)}",
                message_type=GossipMessageType.METADATA_UPDATE,
                sender_id=self.node_id,
                metadata_type=metadata_type,
                payload=entry.to_dict(),
                timestamp=time.time()
            )

            # Enviar a peers seleccionados
            peers = self._select_gossip_peers()
            for peer_id in peers:
                await self.p2p_client.send_message(peer_id, message.to_dict())
                self.stats["messages_sent"] += 1

        except Exception as e:
            logger.error(f"❌ Error gossiping metadata update: {e}")

    async def _initiate_consensus(self, key: str, timeout: float):
        """Iniciar proceso de consenso para una clave."""
        try:
            # Calcular mínimo de votos basado en peers conectados
            connected_peers = len(self.p2p_client.get_connected_peers())
            min_votes = max(self.config.min_consensus_peers,
                          int(connected_peers * self.config.consensus_quorum))

            # Crear estado de consenso
            consensus_state = ConsensusState(
                key=key,
                candidates={},
                start_time=time.time(),
                timeout=timeout,
                min_votes=min_votes
            )

            self.consensus_states[key] = consensus_state
            self.consensus_votes[key] = {}

            # Añadir nuestro propio voto si tenemos el metadato
            local_entry = self.metadata_store.get(key)
            if local_entry:
                vote = ConsensusVote(
                    key=key,
                    value_hash=local_entry.get_hash(),
                    version=local_entry.version,
                    voter_node=self.node_id,
                    timestamp=time.time()
                )
                consensus_state.add_vote(vote)
                self.consensus_votes[key][self.node_id] = vote

            # Solicitar votos de otros peers
            message = GossipMessage(
                message_id=f"consensus_req_{secrets.token_hex(8)}",
                message_type=GossipMessageType.METADATA_REQUEST,
                sender_id=self.node_id,
                metadata_type=MetadataType.CONFIGURATION,
                payload={"request_type": "consensus", "key": key},
                timestamp=time.time()
            )

            # Enviar a múltiples peers
            peers = self._select_gossip_peers()
            for peer_id in peers:
                await self.p2p_client.send_message(peer_id, message.to_dict())

            logger.debug(f"🎯 Initiated consensus for {key} with {len(peers)} peers, min_votes={min_votes}")

        except Exception as e:
            logger.error(f"❌ Error initiating consensus for {key}: {e}")

    # ==================== MANEJO DE MENSAJES ====================

    async def _handle_gossip_message(self, message_data: Dict[str, Any]):
        """Manejar mensaje gossip recibido."""
        try:
            message = GossipMessage.from_dict(message_data)
            self.stats["messages_received"] += 1

            # Verificar si ya procesamos este mensaje
            if message.message_id in self.message_history:
                return

            # Marcar como procesado
            self.message_history.add(message.message_id)

            # Incrementar hop count
            message.hop_count += 1

            # Procesar según tipo
            if message.message_type == GossipMessageType.METADATA_UPDATE:
                await self._handle_metadata_update(message)
            elif message.message_type == GossipMessageType.METADATA_REQUEST:
                await self._handle_metadata_request(message)
            elif message.message_type == GossipMessageType.METADATA_DIGEST:
                await self._handle_metadata_digest(message)
            elif message.message_type == GossipMessageType.METADATA_SYNC:
                await self._handle_metadata_sync(message)

        except Exception as e:
            logger.error(f"❌ Error handling gossip message: {e}")

    async def _handle_metadata_update(self, message: GossipMessage):
        """Manejar actualización de metadatos."""
        try:
            # Verificar si es un voto de consenso
            if "vote" in message.payload:
                await self._handle_consensus_vote(message)
                return

            entry_data = message.payload
            entry = MetadataEntry.from_dict(entry_data)

            # Verificar si tenemos una versión más reciente
            existing = self.metadata_store.get(entry.key)
            if existing and existing.version >= entry.version:
                return

            # Actualizar localmente
            self.metadata_store[entry.key] = entry

            # Trigger callback
            metadata_type = message.metadata_type
            await self._trigger_metadata_callback(metadata_type, entry.key, entry)

            # Propagar si no excedemos TTL
            if message.hop_count < self.config.max_message_hops:
                await self._forward_message(message)

        except Exception as e:
            logger.error(f"❌ Error handling metadata update: {e}")

    async def _handle_consensus_vote(self, message: GossipMessage):
        """Manejar voto de consenso."""
        try:
            vote_data = message.payload["vote"]
            vote = ConsensusVote.from_dict(vote_data)

            # Verificar si estamos participando en este consenso
            consensus_state = self.consensus_states.get(vote.key)
            if not consensus_state:
                logger.debug(f"Received vote for unknown consensus {vote.key}")
                return

            # Verificar si ya tenemos este voto
            if vote.voter_node in self.consensus_votes[vote.key]:
                return

            # Añadir voto al consenso
            consensus_state.add_vote(vote)
            self.consensus_votes[vote.key][vote.voter_node] = vote

            # Verificar si tenemos la entrada correspondiente localmente
            local_entry = self.metadata_store.get(vote.key)
            if not local_entry or local_entry.get_hash() != vote.value_hash:
                # Solicitar la entrada completa si no la tenemos
                request_message = GossipMessage(
                    message_id=f"request_entry_{secrets.token_hex(8)}",
                    message_type=GossipMessageType.METADATA_REQUEST,
                    sender_id=self.node_id,
                    metadata_type=MetadataType.CONFIGURATION,
                    payload={"request_type": "entry", "key": vote.key},
                    timestamp=time.time()
                )

                await self.p2p_client.send_message(message.sender_id, request_message.to_dict())

            logger.debug(f"📊 Received consensus vote for {vote.key} from {vote.voter_node}")

        except Exception as e:
            logger.error(f"❌ Error handling consensus vote: {e}")

    async def _handle_metadata_request(self, message: GossipMessage):
        """Manejar solicitud de metadatos."""
        try:
            request_type = message.payload.get("request_type")

            if request_type == "consensus":
                key = message.payload.get("key")
                if key:
                    await self._handle_consensus_request(message, key)

            elif request_type == "entry":
                key = message.payload.get("key")
                if key:
                    await self._respond_entry_request(message, key)

            elif request_type == "full_sync":
                await self._respond_full_sync(message)

        except Exception as e:
            logger.error(f"❌ Error handling metadata request: {e}")

    async def _handle_consensus_request(self, message: GossipMessage, key: str):
        """Manejar solicitud de consenso."""
        try:
            # Verificar si tenemos estado de consenso para esta clave
            consensus_state = self.consensus_states.get(key)
            if not consensus_state:
                # No estamos participando en este consenso, responder con nuestros datos locales
                await self._respond_consensus_request(message, key)
                return

            # Participar en el consenso: enviar nuestro voto
            local_entry = self.metadata_store.get(key)
            if local_entry:
                vote = ConsensusVote(
                    key=key,
                    value_hash=local_entry.get_hash(),
                    version=local_entry.version,
                    voter_node=self.node_id,
                    timestamp=time.time()
                )

                # Enviar voto al solicitante
                vote_message = GossipMessage(
                    message_id=f"vote_{secrets.token_hex(8)}",
                    message_type=GossipMessageType.METADATA_UPDATE,
                    sender_id=self.node_id,
                    metadata_type=MetadataType.CONFIGURATION,
                    payload={"vote": vote.to_dict()},
                    timestamp=time.time()
                )

                await self.p2p_client.send_message(message.sender_id, vote_message.to_dict())

                # También añadir nuestro voto localmente si no lo tenemos
                if self.node_id not in self.consensus_votes[key]:
                    consensus_state.add_vote(vote)
                    self.consensus_votes[key][self.node_id] = vote

        except Exception as e:
            logger.error(f"❌ Error handling consensus request for {key}: {e}")

    async def _handle_metadata_digest(self, message: GossipMessage):
        """Manejar digest de metadatos."""
        try:
            peer_digest = message.payload.get("digest", {})
            differences = self._compare_digests(peer_digest)

            if differences:
                # Solicitar metadatos faltantes
                sync_message = GossipMessage(
                    message_id=f"sync_{secrets.token_hex(8)}",
                    message_type=GossipMessageType.METADATA_SYNC,
                    sender_id=self.node_id,
                    metadata_type=MetadataType.CONFIGURATION,
                    payload={"requested_keys": list(differences)},
                    timestamp=time.time()
                )

                await self.p2p_client.send_message(message.sender_id, sync_message.to_dict())

        except Exception as e:
            logger.error(f"❌ Error handling metadata digest: {e}")

    async def _handle_metadata_sync(self, message: GossipMessage):
        """Manejar sincronización de metadatos."""
        try:
            requested_keys = message.payload.get("requested_keys", [])

            # Enviar metadatos solicitados
            for key in requested_keys:
                entry = self.metadata_store.get(key)
                if entry:
                    sync_message = GossipMessage(
                        message_id=f"sync_update_{secrets.token_hex(8)}",
                        message_type=GossipMessageType.METADATA_UPDATE,
                        sender_id=self.node_id,
                        metadata_type=MetadataType.CONFIGURATION,  # TODO: determinar tipo correcto
                        payload=entry.to_dict(),
                        timestamp=time.time()
                    )

                    await self.p2p_client.send_message(message.sender_id, sync_message.to_dict())

        except Exception as e:
            logger.error(f"❌ Error handling metadata sync: {e}")

    # ==================== UTILIDADES ====================

    def _create_metadata_digest(self) -> Dict[str, int]:
        """Crear digest de metadatos locales."""
        digest = {}
        for key, entry in self.metadata_store.items():
            if not entry.is_expired():
                digest[key] = entry.version

        # Limitar tamaño del digest
        if len(digest) > self.config.digest_size:
            # Mantener solo las más recientes
            sorted_items = sorted(digest.items(), key=lambda x: self.metadata_store[x[0]].timestamp, reverse=True)
            digest = dict(sorted_items[:self.config.digest_size])

        return digest

    def _compare_digests(self, peer_digest: Dict[str, int]) -> Set[str]:
        """Comparar digest local con digest de peer."""
        differences = set()

        # Verificar qué tenemos que el peer no tiene o tiene versión más antigua
        for key, local_version in self._create_metadata_digest().items():
            peer_version = peer_digest.get(key, 0)
            if local_version > peer_version:
                differences.add(key)

        # Verificar qué el peer tiene que nosotros no tenemos
        for key, peer_version in peer_digest.items():
            if key not in self.metadata_store:
                differences.add(key)
            elif self.metadata_store[key].version < peer_version:
                differences.add(key)

        return differences

    def _get_next_version(self, key: str) -> int:
        """Obtener siguiente versión para una clave."""
        existing = self.metadata_store.get(key)
        return (existing.version + 1) if existing else 1

    async def _check_consensus(self, key: str) -> Optional[MetadataEntry]:
        """Verificar si hay consenso para una clave."""
        consensus_state = self.consensus_states.get(key)
        if not consensus_state:
            return None

        if consensus_state.has_consensus():
            winner_hash, votes = consensus_state.get_winner()

            # Encontrar la entrada correspondiente al hash ganador
            for entry in self.metadata_store.values():
                if entry.key == key and entry.get_hash() == winner_hash:
                    return entry

        return None

    async def _resolve_consensus(self, key: str, winner_hash: str, votes: int):
        """Resolver consenso alcanzado."""
        try:
            # Encontrar la entrada ganadora
            winner_entry = None
            for entry in self.metadata_store.values():
                if entry.key == key and entry.get_hash() == winner_hash:
                    winner_entry = entry
                    break

            if winner_entry:
                # Actualizar votos de consenso
                winner_entry.consensus_votes = votes

                # Trigger callback de consenso
                callback = self.consensus_callbacks.get(key)
                if callback:
                    await callback(key, winner_entry)

                logger.info(f"✅ Consensus achieved for {key}: {votes} votes, version {winner_entry.version}")
            else:
                logger.warning(f"⚠️ Consensus winner not found locally for {key}")

        except Exception as e:
            logger.error(f"❌ Error resolving consensus for {key}: {e}")

    async def _respond_entry_request(self, message: GossipMessage, key: str):
        """Responder a solicitud de entrada específica."""
        entry = self.metadata_store.get(key)
        if entry:
            response = GossipMessage(
                message_id=f"entry_resp_{secrets.token_hex(8)}",
                message_type=GossipMessageType.METADATA_UPDATE,
                sender_id=self.node_id,
                metadata_type=MetadataType.CONFIGURATION,
                payload=entry.to_dict(),
                timestamp=time.time()
            )

            await self.p2p_client.send_message(message.sender_id, response.to_dict())

    async def _respond_consensus_request(self, message: GossipMessage, key: str):
        """Responder a solicitud de consenso."""
        entry = self.metadata_store.get(key)
        if entry:
            response = GossipMessage(
                message_id=f"consensus_resp_{secrets.token_hex(8)}",
                message_type=GossipMessageType.METADATA_UPDATE,
                sender_id=self.node_id,
                metadata_type=MetadataType.CONFIGURATION,
                payload=entry.to_dict(),
                timestamp=time.time()
            )

            await self.p2p_client.send_message(message.sender_id, response.to_dict())

    async def _respond_full_sync(self, message: GossipMessage):
        """Responder a solicitud de sincronización completa."""
        digest = self._create_metadata_digest()

        response = GossipMessage(
            message_id=f"full_sync_resp_{secrets.token_hex(8)}",
            message_type=GossipMessageType.METADATA_DIGEST,
            sender_id=self.node_id,
            metadata_type=MetadataType.CONFIGURATION,
            payload={"digest": digest, "full_sync": True},
            timestamp=time.time()
        )

        await self.p2p_client.send_message(message.sender_id, response.to_dict())

    async def _forward_message(self, message: GossipMessage):
        """Reenviar mensaje a otros peers."""
        if message.hop_count >= self.config.max_message_hops:
            return

        # Seleccionar peers para forwarding (excluyendo el origen)
        peers = [p for p in self._select_gossip_peers() if p != message.sender_id]
        for peer_id in peers:
            await self.p2p_client.send_message(peer_id, message.to_dict())

    async def _trigger_metadata_callback(self, metadata_type: MetadataType, key: str, entry: MetadataEntry):
        """Trigger callbacks de metadatos."""
        callbacks = self.metadata_callbacks.get(metadata_type, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(key, entry)
                else:
                    await asyncio.get_event_loop().run_in_executor(None, callback, key, entry)
            except Exception as e:
                logger.error(f"Error in metadata callback: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del protocolo gossip."""
        return {
            **self.stats,
            "metadata_entries": len(self.metadata_store),
            "pending_messages": len(self.pending_messages),
            "is_running": self.is_running,
            "config": {
                "gossip_interval": self.config.gossip_interval,
                "fanout": self.config.fanout,
                "min_consensus_peers": self.config.min_consensus_peers
            }
        }


# Funciones de conveniencia

async def create_gossip_protocol(node_id: str, p2p_client: P2PClient,
                               config: Optional[GossipConfig] = None) -> GossipProtocol:
    """
    Crear e inicializar protocolo gossip.

    Args:
        node_id: ID del nodo
        p2p_client: Cliente P2P existente
        config: Configuración del gossip

    Returns:
        Instancia del protocolo gossip
    """
    protocol = GossipProtocol(node_id, p2p_client, config)
    await protocol.start()
    return protocol


def create_gossip_config(**kwargs) -> GossipConfig:
    """Crear configuración de gossip con parámetros personalizados."""
    return GossipConfig(**kwargs)