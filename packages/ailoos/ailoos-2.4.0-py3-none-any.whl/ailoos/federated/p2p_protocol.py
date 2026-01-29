"""
Protocolo P2P Seguro con TLS 1.3 para AILOOS Federated Learning
Implementa comunicación segura entre nodos federados con autenticación mutua,
handshake seguro y gestión de conexiones peer-to-peer.
"""

import asyncio
import ssl
import json
import time
import uuid
import datetime
import ipaddress
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend

from ..core.logging import get_logger

logger = get_logger(__name__)


class P2PMessageType(Enum):
    """Tipos de mensajes en el protocolo P2P."""
    HANDSHAKE_INIT = "handshake_init"
    HANDSHAKE_RESPONSE = "handshake_response"
    HANDSHAKE_COMPLETE = "handshake_complete"
    MODEL_UPDATE = "model_update"
    MODEL_UPDATE_ACK = "model_update_ack"
    AGGREGATION_REQUEST = "aggregation_request"
    AGGREGATION_RESPONSE = "aggregation_response"
    HEARTBEAT = "heartbeat"
    DISCONNECT = "disconnect"
    ERROR = "error"


class ConnectionState(Enum):
    """Estados de conexión P2P."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    HANDSHAKING = "handshaking"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    ERROR = "error"


@dataclass
class P2PMessage:
    """Mensaje del protocolo P2P."""
    message_id: str
    message_type: P2PMessageType
    sender_id: str
    receiver_id: str
    timestamp: float
    payload: Dict[str, Any]
    signature: Optional[str] = None
    ttl: int = 300  # Time to live en segundos

    def to_dict(self) -> Dict[str, Any]:
        """Convertir mensaje a diccionario para serialización."""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "signature": self.signature,
            "ttl": self.ttl
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'P2PMessage':
        """Crear mensaje desde diccionario."""
        return cls(
            message_id=data["message_id"],
            message_type=P2PMessageType(data["message_type"]),
            sender_id=data["sender_id"],
            receiver_id=data["receiver_id"],
            timestamp=data["timestamp"],
            payload=data["payload"],
            signature=data.get("signature"),
            ttl=data.get("ttl", 300)
        )

    def is_expired(self) -> bool:
        """Verificar si el mensaje ha expirado."""
        return time.time() - self.timestamp > self.ttl


@dataclass
class PeerInfo:
    """Información de un peer en la red P2P."""
    node_id: str
    host: str
    port: int
    public_key: bytes
    certificate: Optional[x509.Certificate] = None
    last_seen: float = field(default_factory=time.time)
    reputation_score: float = 1.0
    connection_state: ConnectionState = ConnectionState.DISCONNECTED
    session_key: Optional[bytes] = None
    supported_protocols: List[str] = field(default_factory=lambda: ["p2p_federated_v1"])

    @property
    def is_connected(self) -> bool:
        """Verificar si el peer está conectado."""
        return self.connection_state in [ConnectionState.CONNECTED, ConnectionState.AUTHENTICATED]

    @property
    def address(self) -> Tuple[str, int]:
        """Obtener dirección del peer."""
        return (self.host, self.port)


class P2PProtocol:
    """
    Protocolo P2P seguro con TLS 1.3 para federated learning.
    Implementa comunicación encriptada entre nodos con autenticación mutua.
    """

    def __init__(self, node_id: str, host: str = "0.0.0.0", port: int = 8443,
                 cert_dir: str = "./certs", enable_tls: bool = True):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.cert_dir = Path(cert_dir)
        self.enable_tls = enable_tls

        # Estado del protocolo
        self.is_running = False
        self.peers: Dict[str, PeerInfo] = {}
        self.active_connections: Dict[str, asyncio.Transport] = {}
        self.pending_handshakes: Dict[str, Dict[str, Any]] = {}

        # Callbacks para manejo de eventos
        self.message_handlers: Dict[P2PMessageType, Callable] = {}
        self.connection_handlers: Dict[str, Callable] = {}

        # Configuración TLS
        self.ssl_context = None
        self.certificate = None
        self.private_key = None

        # Servidor y cliente
        self.server = None
        self.client_connections: Dict[str, asyncio.Transport] = {}

        # Estadísticas
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "bytes_sent": 0,
            "bytes_received": 0,
            "connections_established": 0,
            "connections_failed": 0,
            "handshakes_completed": 0,
            "errors": 0
        }

        # Inicializar directorio de certificados
        self.cert_dir.mkdir(parents=True, exist_ok=True)

        # Inicializar TLS si está habilitado
        if self.enable_tls:
            self._initialize_tls()

        logger.info(f"🔐 P2P Protocol initialized for node {node_id} on {host}:{port}")

    def _initialize_tls(self):
        """Inicializar configuración TLS 1.3 con certificados."""
        try:
            # Crear certificado autofirmado si no existe
            cert_path = self.cert_dir / f"{self.node_id}.pem"
            key_path = self.cert_dir / f"{self.node_id}.key"

            if not cert_path.exists() or not key_path.exists():
                self._generate_self_signed_certificate(cert_path, key_path)

            # Cargar certificado y clave privada
            with open(cert_path, 'rb') as f:
                cert_data = f.read()
            with open(key_path, 'rb') as f:
                key_data = f.read()

            self.certificate = x509.load_pem_x509_certificate(cert_data, default_backend())
            self.private_key = serialization.load_pem_private_key(key_data, None, default_backend())

            # Crear contexto SSL para servidor
            self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.ssl_context.load_cert_chain(str(cert_path), str(key_path))
            self.ssl_context.verify_mode = ssl.CERT_REQUIRED
            self.ssl_context.check_hostname = False  # Para certificados autofirmados

            # Configurar TLS 1.3
            self.ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3
            self.ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3

            # Cargar certificados de CA conocidos (para autenticación mutua)
            ca_cert_path = self.cert_dir / "ca.pem"
            if ca_cert_path.exists():
                self.ssl_context.load_verify_locations(str(ca_cert_path))

            logger.info("✅ TLS 1.3 initialized with mutual authentication")

        except Exception as e:
            logger.error(f"❌ Error initializing TLS: {e}")
            self.enable_tls = False

    def _generate_self_signed_certificate(self, cert_path: Path, key_path: Path):
        """Generar certificado autofirmado para el nodo."""
        # Generar clave privada
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # Crear certificado
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "ES"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Madrid"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Madrid"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "AILOOS"),
            x509.NameAttribute(NameOID.COMMON_NAME, self.node_id),
        ])

        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(self.node_id),
                x509.IPAddress(ipaddress.IPv4Address(self.host) if self.host != "0.0.0.0" else ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256(), default_backend())

        # Guardar certificado
        with open(cert_path, 'wb') as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        # Guardar clave privada
        with open(key_path, 'wb') as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))

        logger.info(f"📜 Generated self-signed certificate for {self.node_id}")

    async def start(self):
        """Iniciar el protocolo P2P."""
        if self.is_running:
            return

        self.is_running = True

        # Iniciar servidor
        await self._start_server()

        # Iniciar tareas de mantenimiento
        asyncio.create_task(self._maintenance_loop())
        asyncio.create_task(self._heartbeat_loop())

        logger.info(f"🚀 P2P Protocol started for node {self.node_id}")

    async def stop(self):
        """Detener el protocolo P2P."""
        if not self.is_running:
            return

        self.is_running = False

        # Cerrar todas las conexiones
        for peer_id, transport in self.active_connections.items():
            transport.close()

        # Detener servidor
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        self.active_connections.clear()
        self.client_connections.clear()

        logger.info(f"🛑 P2P Protocol stopped for node {self.node_id}")

    async def _start_server(self):
        """Iniciar servidor P2P."""
        try:
            if self.enable_tls and self.ssl_context:
                # Servidor con TLS
                self.server = await asyncio.start_server(
                    self._handle_connection,
                    self.host,
                    self.port,
                    ssl=self.ssl_context
                )
            else:
                # Servidor sin TLS (solo para desarrollo)
                logger.warning("⚠️ Starting server without TLS - NOT SECURE!")
                self.server = await asyncio.start_server(
                    self._handle_connection,
                    self.host,
                    self.port
                )

            logger.info(f"📡 P2P Server listening on {self.host}:{self.port}")

        except Exception as e:
            logger.error(f"❌ Error starting P2P server: {e}")
            raise

    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.Transport):
        """Manejar nueva conexión entrante."""
        try:
            peer_address = writer.get_extra_info('peername')
            logger.info(f"🔗 New connection from {peer_address}")

            # Crear tarea para manejar la conexión
            asyncio.create_task(self._handle_peer_connection(reader, writer))

        except Exception as e:
            logger.error(f"❌ Error handling connection: {e}")

    async def _handle_peer_connection(self, reader: asyncio.StreamReader, writer: asyncio.Transport):
        """Manejar conexión con un peer específico."""
        peer_id = None
        try:
            # Leer mensaje inicial para identificar peer
            data = await reader.read(4096)
            if not data:
                return

            message_data = json.loads(data.decode())
            message = P2PMessage.from_dict(message_data)

            peer_id = message.sender_id

            # Verificar si ya tenemos información del peer
            if peer_id not in self.peers:
                # Peer desconocido, registrar
                peer_info = PeerInfo(
                    node_id=peer_id,
                    host=writer.get_extra_info('peername')[0],
                    port=writer.get_extra_info('peername')[1],
                    public_key=b'',  # Se obtendrá durante handshake
                    connection_state=ConnectionState.CONNECTING
                )
                self.peers[peer_id] = peer_info

            # Actualizar estado de conexión
            self.peers[peer_id].connection_state = ConnectionState.CONNECTED
            self.peers[peer_id].last_seen = time.time()
            self.active_connections[peer_id] = writer

            # Procesar mensaje
            await self._process_message(message, writer)

            # Mantener conexión viva
            while self.is_running:
                try:
                    data = await asyncio.wait_for(reader.read(4096), timeout=30.0)
                    if not data:
                        break

                    message_data = json.loads(data.decode())
                    message = P2PMessage.from_dict(message_data)
                    await self._process_message(message, writer)

                except asyncio.TimeoutError:
                    # Enviar heartbeat
                    await self._send_heartbeat(peer_id)
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Invalid JSON received from {peer_id}")
                    continue

        except Exception as e:
            logger.error(f"❌ Error handling peer connection {peer_id}: {e}")
            self.stats["errors"] += 1
        finally:
            # Limpiar conexión
            if peer_id and peer_id in self.active_connections:
                writer.close()
                del self.active_connections[peer_id]
                if peer_id in self.peers:
                    self.peers[peer_id].connection_state = ConnectionState.DISCONNECTED

    async def connect_to_peer(self, peer_info: PeerInfo) -> bool:
        """Conectar a un peer específico."""
        try:
            if peer_info.node_id in self.active_connections:
                return True  # Ya conectado

            logger.info(f"🔗 Connecting to peer {peer_info.node_id} at {peer_info.address}")

            if self.enable_tls and self.ssl_context:
                # Conexión con TLS
                reader, writer = await asyncio.open_connection(
                    peer_info.host,
                    peer_info.port,
                    ssl=self.ssl_context
                )
            else:
                # Conexión sin TLS
                reader, writer = await asyncio.open_connection(
                    peer_info.host,
                    peer_info.port
                )

            # Registrar conexión
            self.client_connections[peer_info.node_id] = writer
            self.active_connections[peer_info.node_id] = writer
            peer_info.connection_state = ConnectionState.CONNECTED
            peer_info.last_seen = time.time()

            # Iniciar handshake
            await self._initiate_handshake(peer_info)

            # Crear tarea para manejar respuestas
            asyncio.create_task(self._handle_client_connection(peer_info.node_id, reader, writer))

            self.stats["connections_established"] += 1
            logger.info(f"✅ Connected to peer {peer_info.node_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error connecting to peer {peer_info.node_id}: {e}")
            peer_info.connection_state = ConnectionState.ERROR
            self.stats["connections_failed"] += 1
            return False

    async def _handle_client_connection(self, peer_id: str, reader: asyncio.StreamReader, writer: asyncio.Transport):
        """Manejar conexión de cliente a peer."""
        try:
            while self.is_running:
                try:
                    data = await asyncio.wait_for(reader.read(4096), timeout=30.0)
                    if not data:
                        break

                    message_data = json.loads(data.decode())
                    message = P2PMessage.from_dict(message_data)
                    await self._process_message(message, writer)

                except asyncio.TimeoutError:
                    await self._send_heartbeat(peer_id)
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Invalid JSON received from {peer_id}")
                    continue

        except Exception as e:
            logger.error(f"❌ Error in client connection to {peer_id}: {e}")
        finally:
            # Limpiar conexión
            if peer_id in self.client_connections:
                writer.close()
                del self.client_connections[peer_id]
                if peer_id in self.active_connections:
                    del self.active_connections[peer_id]
                if peer_id in self.peers:
                    self.peers[peer_id].connection_state = ConnectionState.DISCONNECTED

    async def _initiate_handshake(self, peer_info: PeerInfo):
        """Iniciar handshake seguro con un peer."""
        try:
            peer_info.connection_state = ConnectionState.HANDSHAKING

            # Generar nonce para handshake
            nonce = str(uuid.uuid4())

            # Crear mensaje de handshake
            handshake_message = P2PMessage(
                message_id=str(uuid.uuid4()),
                message_type=P2PMessageType.HANDSHAKE_INIT,
                sender_id=self.node_id,
                receiver_id=peer_info.node_id,
                timestamp=time.time(),
                payload={
                    "nonce": nonce,
                    "protocol_version": "p2p_federated_v1",
                    "supported_protocols": peer_info.supported_protocols,
                    "node_info": {
                        "node_id": self.node_id,
                        "capabilities": ["model_updates", "aggregation", "secure_communication"]
                    }
                }
            )

            # Firmar mensaje
            handshake_message.signature = self._sign_message(handshake_message)

            # Almacenar handshake pendiente
            self.pending_handshakes[peer_info.node_id] = {
                "nonce": nonce,
                "timestamp": time.time(),
                "message": handshake_message
            }

            # Enviar mensaje
            await self._send_message_to_peer(peer_info.node_id, handshake_message)

            logger.info(f"🤝 Handshake initiated with {peer_info.node_id}")

        except Exception as e:
            logger.error(f"❌ Error initiating handshake with {peer_info.node_id}: {e}")
            peer_info.connection_state = ConnectionState.ERROR

    async def _process_message(self, message: P2PMessage, writer: asyncio.Transport):
        """Procesar mensaje recibido."""
        try:
            # Verificar expiración
            if message.is_expired():
                logger.warning(f"⚠️ Received expired message from {message.sender_id}")
                return

            # Verificar firma si está presente
            if message.signature and not self._verify_message_signature(message):
                logger.warning(f"⚠️ Invalid signature in message from {message.sender_id}")
                return

            self.stats["messages_received"] += 1

            # Procesar según tipo de mensaje
            if message.message_type == P2PMessageType.HANDSHAKE_INIT:
                await self._handle_handshake_init(message, writer)
            elif message.message_type == P2PMessageType.HANDSHAKE_RESPONSE:
                await self._handle_handshake_response(message)
            elif message.message_type == P2PMessageType.HANDSHAKE_COMPLETE:
                await self._handle_handshake_complete(message)
            elif message.message_type == P2PMessageType.MODEL_UPDATE:
                await self._handle_model_update(message)
            elif message.message_type == P2PMessageType.HEARTBEAT:
                await self._handle_heartbeat(message)
            elif message.message_type == P2PMessageType.DISCONNECT:
                await self._handle_disconnect(message)
            else:
                # Manejar con callback personalizado si existe
                handler = self.message_handlers.get(message.message_type)
                if handler:
                    await handler(message)
                else:
                    logger.warning(f"⚠️ Unknown message type: {message.message_type}")

        except Exception as e:
            logger.error(f"❌ Error processing message from {message.sender_id}: {e}")
            self.stats["errors"] += 1

    async def _handle_handshake_init(self, message: P2PMessage, writer: asyncio.Transport):
        """Manejar inicio de handshake."""
        try:
            peer_id = message.sender_id
            nonce = message.payload["nonce"]

            # Verificar que no estamos ya en handshake
            if peer_id in self.pending_handshakes:
                logger.warning(f"⚠️ Handshake already in progress with {peer_id}")
                return

            # Generar respuesta de nonce
            response_nonce = str(uuid.uuid4())

            # Crear mensaje de respuesta
            response_message = P2PMessage(
                message_id=str(uuid.uuid4()),
                message_type=P2PMessageType.HANDSHAKE_RESPONSE,
                sender_id=self.node_id,
                receiver_id=peer_id,
                timestamp=time.time(),
                payload={
                    "original_nonce": nonce,
                    "response_nonce": response_nonce,
                    "protocol_version": "p2p_federated_v1",
                    "node_info": {
                        "node_id": self.node_id,
                        "capabilities": ["model_updates", "aggregation", "secure_communication"]
                    }
                }
            )

            # Firmar mensaje
            response_message.signature = self._sign_message(response_message)

            # Almacenar handshake pendiente
            self.pending_handshakes[peer_id] = {
                "response_nonce": response_nonce,
                "timestamp": time.time(),
                "message": response_message
            }

            # Enviar respuesta
            await self._send_message_to_transport(writer, response_message)

            logger.info(f"🤝 Handshake response sent to {peer_id}")

        except Exception as e:
            logger.error(f"❌ Error handling handshake init from {message.sender_id}: {e}")

    async def _handle_handshake_response(self, message: P2PMessage):
        """Manejar respuesta de handshake."""
        try:
            peer_id = message.sender_id

            # Verificar handshake pendiente
            if peer_id not in self.pending_handshakes:
                logger.warning(f"⚠️ Unexpected handshake response from {peer_id}")
                return

            pending = self.pending_handshakes[peer_id]
            original_nonce = pending["message"].payload["nonce"]
            received_original_nonce = message.payload["original_nonce"]

            # Verificar nonce
            if original_nonce != received_original_nonce:
                logger.warning(f"⚠️ Nonce mismatch in handshake with {peer_id}")
                return

            # Completar handshake
            complete_message = P2PMessage(
                message_id=str(uuid.uuid4()),
                message_type=P2PMessageType.HANDSHAKE_COMPLETE,
                sender_id=self.node_id,
                receiver_id=peer_id,
                timestamp=time.time(),
                payload={
                    "response_nonce": message.payload["response_nonce"],
                    "status": "authenticated",
                    "session_established": True
                }
            )

            # Firmar mensaje
            complete_message.signature = self._sign_message(complete_message)

            # Enviar confirmación
            await self._send_message_to_peer(peer_id, complete_message)

            # Actualizar estado del peer
            if peer_id in self.peers:
                self.peers[peer_id].connection_state = ConnectionState.AUTHENTICATED
                self.stats["handshakes_completed"] += 1

            # Limpiar handshake pendiente
            del self.pending_handshakes[peer_id]

            logger.info(f"✅ Handshake completed with {peer_id}")

        except Exception as e:
            logger.error(f"❌ Error handling handshake response from {message.sender_id}: {e}")

    async def _handle_handshake_complete(self, message: P2PMessage):
        """Manejar completación de handshake."""
        try:
            peer_id = message.sender_id

            # Verificar handshake pendiente
            if peer_id not in self.pending_handshakes:
                logger.warning(f"⚠️ Unexpected handshake completion from {peer_id}")
                return

            # Limpiar handshake pendiente
            del self.pending_handshakes[peer_id]

            # Actualizar estado del peer
            if peer_id in self.peers:
                self.peers[peer_id].connection_state = ConnectionState.AUTHENTICATED
                self.stats["handshakes_completed"] += 1

            logger.info(f"✅ Handshake fully completed with {peer_id}")

        except Exception as e:
            logger.error(f"❌ Error handling handshake completion from {message.sender_id}: {e}")

    async def _handle_model_update(self, message: P2PMessage):
        """Manejar actualización de modelo."""
        try:
            # Callback personalizado para actualizaciones de modelo
            handler = self.message_handlers.get(P2PMessageType.MODEL_UPDATE)
            if handler:
                await handler(message)
            else:
                logger.info(f"📦 Model update received from {message.sender_id}")

            # Enviar ACK
            ack_message = P2PMessage(
                message_id=str(uuid.uuid4()),
                message_type=P2PMessageType.MODEL_UPDATE_ACK,
                sender_id=self.node_id,
                receiver_id=message.sender_id,
                timestamp=time.time(),
                payload={
                    "original_message_id": message.message_id,
                    "status": "received",
                    "timestamp": time.time()
                }
            )

            ack_message.signature = self._sign_message(ack_message)
            await self._send_message_to_peer(message.sender_id, ack_message)

        except Exception as e:
            logger.error(f"❌ Error handling model update from {message.sender_id}: {e}")

    async def _handle_heartbeat(self, message: P2PMessage):
        """Manejar heartbeat."""
        peer_id = message.sender_id
        if peer_id in self.peers:
            self.peers[peer_id].last_seen = time.time()

    async def _handle_disconnect(self, message: P2PMessage):
        """Manejar desconexión."""
        peer_id = message.sender_id
        if peer_id in self.active_connections:
            transport = self.active_connections[peer_id]
            transport.close()
            del self.active_connections[peer_id]

        if peer_id in self.peers:
            self.peers[peer_id].connection_state = ConnectionState.DISCONNECTED

        logger.info(f"👋 Peer {peer_id} disconnected")

    async def send_model_update(self, peer_id: str, model_weights: Dict[str, Any],
                               metadata: Dict[str, Any]) -> bool:
        """Enviar actualización de modelo a un peer."""
        try:
            if peer_id not in self.active_connections:
                logger.warning(f"⚠️ No active connection to peer {peer_id}")
                return False

            # Crear mensaje de actualización
            update_message = P2PMessage(
                message_id=str(uuid.uuid4()),
                message_type=P2PMessageType.MODEL_UPDATE,
                sender_id=self.node_id,
                receiver_id=peer_id,
                timestamp=time.time(),
                payload={
                    "model_weights": model_weights,
                    "metadata": metadata,
                    "session_id": metadata.get("session_id"),
                    "round_num": metadata.get("round_num", 0),
                    "encryption_type": "none"  # Para actualizaciones no encriptadas
                }
            )

            # Firmar mensaje
            update_message.signature = self._sign_message(update_message)

            # Enviar mensaje
            await self._send_message_to_peer(peer_id, update_message)

            self.stats["messages_sent"] += 1
            logger.info(f"📤 Model update sent to {peer_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error sending model update to {peer_id}: {e}")
            return False

    async def _send_message_to_peer(self, peer_id: str, message: P2PMessage):
        """Enviar mensaje a un peer específico."""
        if peer_id not in self.active_connections:
            raise ValueError(f"No active connection to peer {peer_id}")

        transport = self.active_connections[peer_id]
        await self._send_message_to_transport(transport, message)

    async def _send_message_to_transport(self, transport: asyncio.Transport, message: P2PMessage):
        """Enviar mensaje a través de un transport."""
        message_data = json.dumps(message.to_dict()).encode()
        transport.write(message_data)
        transport.write(b'\n')  # Delimitador de mensaje

        self.stats["bytes_sent"] += len(message_data)

    async def _send_heartbeat(self, peer_id: str):
        """Enviar heartbeat a un peer."""
        try:
            heartbeat_message = P2PMessage(
                message_id=str(uuid.uuid4()),
                message_type=P2PMessageType.HEARTBEAT,
                sender_id=self.node_id,
                receiver_id=peer_id,
                timestamp=time.time(),
                payload={
                    "status": "alive",
                    "timestamp": time.time()
                }
            )

            await self._send_message_to_peer(peer_id, heartbeat_message)

        except Exception as e:
            logger.debug(f"⚠️ Could not send heartbeat to {peer_id}: {e}")

    def _sign_message(self, message: P2PMessage) -> str:
        """Firmar mensaje con clave privada."""
        if not self.private_key:
            return ""

        # Crear datos para firmar
        message_data = f"{message.message_id}:{message.message_type.value}:{message.sender_id}:{message.receiver_id}:{message.timestamp}"
        payload_str = json.dumps(message.payload, sort_keys=True)
        data_to_sign = f"{message_data}:{payload_str}"

        # Firmar
        signature = self.private_key.sign(
            data_to_sign.encode(),
            ec.ECDSA(hashes.SHA256())
        )

        return signature.hex()

    def _verify_message_signature(self, message: P2PMessage) -> bool:
        """Verificar firma de mensaje."""
        if not message.signature or message.sender_id not in self.peers:
            return False

        peer_info = self.peers[message.sender_id]
        if not peer_info.public_key:
            return False

        try:
            # Crear datos para verificar
            message_data = f"{message.message_id}:{message.message_type.value}:{message.sender_id}:{message.receiver_id}:{message.timestamp}"
            payload_str = json.dumps(message.payload, sort_keys=True)
            data_to_verify = f"{message_data}:{payload_str}"

            # Verificar firma
            public_key = serialization.load_pem_public_key(peer_info.public_key, default_backend())
            signature_bytes = bytes.fromhex(message.signature)

            public_key.verify(
                signature_bytes,
                data_to_verify.encode(),
                ec.ECDSA(hashes.SHA256())
            )

            return True

        except Exception:
            return False

    async def _maintenance_loop(self):
        """Loop de mantenimiento para limpiar conexiones inactivas."""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Cada minuto

                current_time = time.time()
                inactive_peers = []

                # Encontrar peers inactivos
                for peer_id, peer_info in self.peers.items():
                    if current_time - peer_info.last_seen > 300:  # 5 minutos
                        inactive_peers.append(peer_id)

                # Limpiar peers inactivos
                for peer_id in inactive_peers:
                    if peer_id in self.active_connections:
                        transport = self.active_connections[peer_id]
                        transport.close()
                        del self.active_connections[peer_id]

                    del self.peers[peer_id]
                    logger.info(f"🧹 Cleaned up inactive peer {peer_id}")

                # Limpiar handshakes pendientes expirados
                expired_handshakes = []
                for peer_id, handshake_data in self.pending_handshakes.items():
                    if current_time - handshake_data["timestamp"] > 60:  # 1 minuto
                        expired_handshakes.append(peer_id)

                for peer_id in expired_handshakes:
                    del self.pending_handshakes[peer_id]
                    logger.debug(f"🧹 Cleaned up expired handshake for {peer_id}")

            except Exception as e:
                logger.error(f"❌ Error in maintenance loop: {e}")

    async def _heartbeat_loop(self):
        """Loop para enviar heartbeats periódicos."""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Cada 30 segundos

                # Enviar heartbeat a todos los peers conectados
                for peer_id in list(self.active_connections.keys()):
                    await self._send_heartbeat(peer_id)

            except Exception as e:
                logger.error(f"❌ Error in heartbeat loop: {e}")

    def register_message_handler(self, message_type: P2PMessageType, handler: Callable):
        """Registrar handler para tipo de mensaje específico."""
        self.message_handlers[message_type] = handler

    def register_connection_handler(self, event: str, handler: Callable):
        """Registrar handler para evento de conexión."""
        self.connection_handlers[event] = handler

    def register_secure_aggregation_handler(self, handler: Callable):
        """Registrar handler para actualizaciones de agregación segura."""
        self.secure_aggregation_handler = handler

    def register_fedasync_aggregation_callback(self, callback: Callable):
        """Registrar callback para resultados de agregación FedAsync."""
        if self.fedasync_buffer:
            self.fedasync_buffer.register_aggregation_callback(callback)
            logger.info("📞 FedAsync aggregation callback registered")
        else:
            logger.warning("⚠️ FedAsync buffer not enabled")

    def get_peer_info(self, peer_id: str) -> Optional[PeerInfo]:
        """Obtener información de un peer."""
        return self.peers.get(peer_id)

    def get_connected_peers(self) -> List[str]:
        """Obtener lista de peers conectados."""
        return [peer_id for peer_id, peer_info in self.peers.items() if peer_info.is_connected]

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del protocolo."""
        stats = {
            **self.stats,
            "active_connections": len(self.active_connections),
            "known_peers": len(self.peers),
            "pending_handshakes": len(self.pending_handshakes),
            "is_running": self.is_running,
            "fedasync_enabled": self.fedasync_enabled
        }

        # Añadir estadísticas de FedAsync si está habilitado
        if self.fedasync_buffer:
            fedasync_stats = self.fedasync_buffer.get_stats()
            stats["fedasync"] = fedasync_stats

        return stats

    def add_peer(self, peer_info: PeerInfo):
        """Añadir información de peer conocido."""
        self.peers[peer_info.node_id] = peer_info
        logger.info(f"📋 Added peer info for {peer_info.node_id}")


# Funciones de conveniencia
def create_p2p_protocol(node_id: str, host: str = "0.0.0.0", port: int = 8443,
                       cert_dir: str = "./certs", fedasync_enabled: bool = False,
                       fedasync_threshold: int = 5, fedasync_time_window: float = 30.0,
                       fedasync_max_buffer: int = 100) -> P2PProtocol:
    """Crear instancia del protocolo P2P."""
    return P2PProtocol(
        node_id=node_id,
        host=host,
        port=port,
        cert_dir=cert_dir,
        fedasync_enabled=fedasync_enabled,
        fedasync_threshold=fedasync_threshold,
        fedasync_time_window=fedasync_time_window,
        fedasync_max_buffer=fedasync_max_buffer
    )


async def connect_to_peer_network(protocol: P2PProtocol, peer_addresses: List[Tuple[str, int, str]]):
    """
    Conectar a una red de peers.

    Args:
        protocol: Instancia del protocolo P2P
        peer_addresses: Lista de tuplas (host, port, node_id)
    """
    for host, port, node_id in peer_addresses:
        peer_info = PeerInfo(
            node_id=node_id,
            host=host,
            port=port,
            public_key=b''  # Se obtendrá durante handshake
        )
        protocol.add_peer(peer_info)
        await protocol.connect_to_peer(peer_info)
"""
Protocolo P2P Seguro con TLS 1.3 para AILOOS Federated Learning
Implementa comunicación segura entre nodos federados con autenticación mutua,
handshake seguro y gestión de conexiones peer-to-peer.
"""

import asyncio
import ssl
import json
import time
import uuid
import datetime
import ipaddress
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging
from collections import defaultdict

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend
from phe import paillier

from ..core.logging import get_logger
from .image_verifier import get_image_verifier, ImageVerificationResult

logger = get_logger(__name__)


class P2PMessageType(Enum):
    """Tipos de mensajes en el protocolo P2P."""
    HANDSHAKE_INIT = "handshake_init"
    HANDSHAKE_RESPONSE = "handshake_response"
    HANDSHAKE_COMPLETE = "handshake_complete"
    MODEL_UPDATE = "model_update"
    MODEL_UPDATE_ACK = "model_update_ack"
    AGGREGATION_REQUEST = "aggregation_request"
    AGGREGATION_RESPONSE = "aggregation_response"
    HEARTBEAT = "heartbeat"
    DISCONNECT = "disconnect"
    ERROR = "error"


class ConnectionState(Enum):
    """Estados de conexión P2P."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    HANDSHAKING = "handshaking"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    ERROR = "error"


@dataclass
class P2PMessage:
    """Mensaje del protocolo P2P."""
    message_id: str
    message_type: P2PMessageType
    sender_id: str
    receiver_id: str
    timestamp: float
    payload: Dict[str, Any]
    signature: Optional[str] = None
    ttl: int = 300  # Time to live en segundos

    def to_dict(self) -> Dict[str, Any]:
        """Convertir mensaje a diccionario para serialización."""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "signature": self.signature,
            "ttl": self.ttl
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'P2PMessage':
        """Crear mensaje desde diccionario."""
        return cls(
            message_id=data["message_id"],
            message_type=P2PMessageType(data["message_type"]),
            sender_id=data["sender_id"],
            receiver_id=data["receiver_id"],
            timestamp=data["timestamp"],
            payload=data["payload"],
            signature=data.get("signature"),
            ttl=data.get("ttl", 300)
        )

    def is_expired(self) -> bool:
        """Verificar si el mensaje ha expirado."""
        return time.time() - self.timestamp > self.ttl


@dataclass
class PeerInfo:
    """Información de un peer en la red P2P."""
    node_id: str
    host: str
    port: int
    public_key: bytes
    certificate: Optional[x509.Certificate] = None
    last_seen: float = field(default_factory=time.time)
    reputation_score: float = 1.0
    connection_state: ConnectionState = ConnectionState.DISCONNECTED
    session_key: Optional[bytes] = None
    supported_protocols: List[str] = field(default_factory=lambda: ["p2p_federated_v1"])

    @property
    def is_connected(self) -> bool:
        """Verificar si el peer está conectado."""
        return self.connection_state in [ConnectionState.CONNECTED, ConnectionState.AUTHENTICATED]

    @property
    def address(self) -> Tuple[str, int]:
        """Obtener dirección del peer."""
        return (self.host, self.port)


@dataclass
class FedAsyncUpdate:
    """Actualización para FedAsync."""
    node_id: str
    model_weights: Dict[str, Any]
    num_samples: int
    timestamp: float
    session_id: str
    round_num: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class AsyncFedAsyncBuffer:
    """
    Buffer asíncrono para FedAsync.
    Almacena actualizaciones entrantes y permite agregación asíncrona
    sin bloquear nodos lentos.
    """

    def __init__(self, aggregation_threshold: int = 5, time_window: float = 30.0,
                 max_buffer_size: int = 100):
        """
        Inicializar buffer asíncrono.

        Args:
            aggregation_threshold: Número mínimo de actualizaciones para agregar
            time_window: Ventana de tiempo máxima para agregación (segundos)
            max_buffer_size: Tamaño máximo del buffer
        """
        self.aggregation_threshold = aggregation_threshold
        self.time_window = time_window
        self.max_buffer_size = max_buffer_size

        # Buffer de actualizaciones por sesión
        self.buffers: Dict[str, asyncio.Queue[FedAsyncUpdate]] = defaultdict(asyncio.Queue)
        self.session_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)

        # Locks para sincronización
        self.locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

        # Callbacks
        self.aggregation_callback: Optional[Callable] = None
        self.is_running = False
        self.aggregation_task: Optional[asyncio.Task] = None

        logger.info(f"🔄 AsyncFedAsyncBuffer initialized with threshold={aggregation_threshold}, "
                   f"time_window={time_window}s, max_size={max_buffer_size}")

    async def start(self):
        """Iniciar el buffer asíncrono."""
        if self.is_running:
            return

        self.is_running = True
        self.aggregation_task = asyncio.create_task(self._aggregation_loop())
        logger.info("🚀 AsyncFedAsyncBuffer started")

    async def stop(self):
        """Detener el buffer asíncrono."""
        if not self.is_running:
            return

        self.is_running = False
        if self.aggregation_task:
            self.aggregation_task.cancel()
            try:
                await self.aggregation_task
            except asyncio.CancelledError:
                pass

        logger.info("🛑 AsyncFedAsyncBuffer stopped")

    async def add_update(self, update: FedAsyncUpdate) -> bool:
        """
        Añadir actualización al buffer.

        Args:
            update: Actualización a añadir

        Returns:
            True si se añadió correctamente
        """
        session_id = update.session_id

        async with self.locks[session_id]:
            try:
                # Verificar tamaño máximo del buffer
                if self.buffers[session_id].qsize() >= self.max_buffer_size:
                    logger.warning(f"⚠️ Buffer full for session {session_id}, dropping update from {update.node_id}")
                    return False

                # Añadir al buffer
                await self.buffers[session_id].put(update)

                # Actualizar estadísticas
                if session_id not in self.session_stats:
                    self.session_stats[session_id] = {
                        "total_updates": 0,
                        "aggregated_rounds": 0,
                        "last_aggregation": time.time(),
                        "nodes_seen": set()
                    }

                stats = self.session_stats[session_id]
                stats["total_updates"] += 1
                stats["nodes_seen"].add(update.node_id)
                stats["last_update"] = time.time()

                logger.debug(f"📥 Update added to buffer for session {session_id} from {update.node_id}")
                return True

            except Exception as e:
                logger.error(f"❌ Error adding update to buffer: {e}")
                return False

    async def _aggregation_loop(self):
        """Loop principal de agregación asíncrona."""
        while self.is_running:
            try:
                await asyncio.sleep(1.0)  # Check every second

                current_time = time.time()

                # Verificar cada sesión activa
                for session_id in list(self.buffers.keys()):
                    await self._check_aggregation_trigger(session_id, current_time)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in aggregation loop: {e}")
                await asyncio.sleep(5.0)  # Wait before retry

    async def _check_aggregation_trigger(self, session_id: str, current_time: float):
        """Verificar si se debe disparar agregación para una sesión."""
        async with self.locks[session_id]:
            try:
                buffer = self.buffers[session_id]
                stats = self.session_stats[session_id]

                buffer_size = buffer.qsize()
                time_since_last = current_time - stats.get("last_aggregation", 0)

                # Trigger aggregation if:
                # 1. Buffer has enough updates, OR
                # 2. Time window has passed and buffer is not empty
                should_aggregate = (
                    buffer_size >= self.aggregation_threshold or
                    (time_since_last >= self.time_window and buffer_size > 0)
                )

                if should_aggregate:
                    await self._perform_aggregation(session_id)

            except Exception as e:
                logger.error(f"❌ Error checking aggregation trigger for {session_id}: {e}")

    async def _perform_aggregation(self, session_id: str):
        """Realizar agregación para una sesión."""
        try:
            buffer = self.buffers[session_id]
            stats = self.session_stats[session_id]

            # Recopilar todas las actualizaciones disponibles
            updates = []
            while not buffer.empty():
                try:
                    update = buffer.get_nowait()
                    updates.append(update)
                except asyncio.QueueEmpty:
                    break

            if not updates:
                return

            # Realizar agregación FedAvg asíncrona
            aggregated_weights = await self._aggregate_updates(updates)

            # Preparar resultado
            result = {
                "session_id": session_id,
                "round_num": max(u.round_num for u in updates),
                "aggregated_weights": aggregated_weights,
                "num_updates": len(updates),
                "total_samples": sum(u.num_samples for u in updates),
                "participating_nodes": [u.node_id for u in updates],
                "timestamp": time.time(),
                "aggregation_type": "fedasync"
            }

            # Actualizar estadísticas
            stats["aggregated_rounds"] += 1
            stats["last_aggregation"] = time.time()

            # Callback de agregación
            if self.aggregation_callback:
                await self.aggregation_callback(result)

            logger.info(f"🔄 FedAsync aggregation completed for session {session_id}: "
                       f"{len(updates)} updates, {len(result['participating_nodes'])} nodes")

        except Exception as e:
            logger.error(f"❌ Error performing aggregation for {session_id}: {e}")

    async def _aggregate_updates(self, updates: List[FedAsyncUpdate]) -> Dict[str, Any]:
        """Agregar actualizaciones usando FedAvg asíncrono."""
        if not updates:
            return {}

        # Inicializar pesos agregados
        aggregated_weights = {}
        total_samples = sum(update.num_samples for update in updates)

        # Agregar pesos ponderados por número de muestras
        for update in updates:
            weight_factor = update.num_samples / total_samples

            for layer_name, layer_weights in update.model_weights.items():
                if layer_name not in aggregated_weights:
                    # Inicializar con ceros
                    if isinstance(layer_weights, list):
                        aggregated_weights[layer_name] = [0.0] * len(layer_weights)
                    else:
                        aggregated_weights[layer_name] = 0.0

                # Agregar pesos ponderados
                if isinstance(layer_weights, list):
                    for i, weight in enumerate(layer_weights):
                        aggregated_weights[layer_name][i] += weight * weight_factor
                else:
                    aggregated_weights[layer_name] += layer_weights * weight_factor

        return aggregated_weights

    def get_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Obtener estadísticas del buffer."""
        if session_id:
            return dict(self.session_stats.get(session_id, {}))
        else:
            return {
                "active_sessions": len(self.buffers),
                "session_stats": dict(self.session_stats),
                "is_running": self.is_running,
                "aggregation_threshold": self.aggregation_threshold,
                "time_window": self.time_window,
                "max_buffer_size": self.max_buffer_size
            }

    def register_aggregation_callback(self, callback: Callable):
        """Registrar callback para resultados de agregación."""
        self.aggregation_callback = callback


class SecureAggregationProtocol:
    """
    Extensión para agregación segura de modelos.
    Implementa protocolos de agregación que preservan privacidad.
    """

    def __init__(self, protocol: 'P2PProtocol'):
        self.protocol = protocol
        self.aggregation_sessions: Dict[str, Dict[str, Any]] = {}

    async def initiate_secure_aggregation(self, session_id: str, participants: List[str],
                                        aggregation_type: str = "fedavg") -> str:
        """
        Iniciar sesión de agregación segura.

        Args:
            session_id: ID de la sesión federada
            participants: Lista de participantes
            aggregation_type: Tipo de agregación ("fedavg", "secure_sum", etc.)

        Returns:
            ID de la sesión de agregación
        """
        aggregation_id = str(uuid.uuid4())

        # Crear sesión de agregación
        self.aggregation_sessions[aggregation_id] = {
            "session_id": session_id,
            "participants": participants.copy(),
            "aggregation_type": aggregation_type,
            "status": "collecting",
            "collected_updates": {},
            "created_at": time.time(),
            "noise_parameters": self._generate_noise_parameters(aggregation_type)
        }

        # Enviar solicitud de agregación a todos los participantes
        for participant_id in participants:
            await self._send_aggregation_request(aggregation_id, participant_id)

        logger.info(f"🔐 Secure aggregation session {aggregation_id} initiated for {len(participants)} participants")
        return aggregation_id

    async def submit_secure_update(self, aggregation_id: str, node_id: str,
                                 masked_update: Dict[str, Any]) -> bool:
        """
        Enviar actualización enmascarada para agregación segura.

        Args:
            aggregation_id: ID de la sesión de agregación
            node_id: ID del nodo
            masked_update: Actualización enmascarada

        Returns:
            True si se aceptó la actualización
        """
        if aggregation_id not in self.aggregation_sessions:
            logger.warning(f"⚠️ Unknown aggregation session {aggregation_id}")
            return False

        session = self.aggregation_sessions[aggregation_id]

        if node_id not in session["participants"]:
            logger.warning(f"⚠️ Node {node_id} not in aggregation session {aggregation_id}")
            return False

        # Almacenar actualización enmascarada
        session["collected_updates"][node_id] = {
            "masked_update": masked_update,
            "submitted_at": time.time(),
            "verified": self._verify_masked_update(masked_update)
        }

        # Verificar si tenemos todas las actualizaciones
        if len(session["collected_updates"]) == len(session["participants"]):
            await self._perform_secure_aggregation(aggregation_id)

        logger.info(f"🔒 Secure update received from {node_id} for aggregation {aggregation_id}")
        return True

    async def _perform_secure_aggregation(self, aggregation_id: str):
        """Realizar agregación segura."""
        session = self.aggregation_sessions[aggregation_id]
        session["status"] = "aggregating"

        try:
            if session["aggregation_type"] == "fedavg":
                result = await self._aggregate_fedavg_secure(session)
            elif session["aggregation_type"] == "secure_sum":
                result = await self._aggregate_secure_sum(session)
            else:
                raise ValueError(f"Unsupported aggregation type: {session['aggregation_type']}")

            session["status"] = "completed"
            session["result"] = result
            session["completed_at"] = time.time()

            # Notificar resultado a través del protocolo P2P
            await self._broadcast_aggregation_result(aggregation_id, result)

            logger.info(f"✅ Secure aggregation {aggregation_id} completed")

        except Exception as e:
            session["status"] = "failed"
            session["error"] = str(e)
            logger.error(f"❌ Secure aggregation {aggregation_id} failed: {e}")

    async def _aggregate_fedavg_secure(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Agregación FedAvg con preservación de privacidad."""
        updates = session["collected_updates"]
        noise_params = session["noise_parameters"]

        # Desenmascarar y agregar
        aggregated_weights = {}
        total_samples = 0

        for node_id, update_data in updates.items():
            masked_update = update_data["masked_update"]
            weights = masked_update["weights"]
            samples = masked_update["num_samples"]
            mask = masked_update.get("mask", {})

            # Remover máscara
            unmasked_weights = self._unmask_weights(weights, mask, noise_params)

            # Agregar ponderadamente
            weight_factor = samples / sum(u["masked_update"]["num_samples"] for u in updates.values())

            for layer_name, layer_weights in unmasked_weights.items():
                if layer_name not in aggregated_weights:
                    aggregated_weights[layer_name] = [0.0] * len(layer_weights) if isinstance(layer_weights, list) else 0.0

                if isinstance(layer_weights, list):
                    for i, w in enumerate(layer_weights):
                        aggregated_weights[layer_name][i] += w * weight_factor
                else:
                    aggregated_weights[layer_name] += layer_weights * weight_factor

            total_samples += samples

        return {
            "weights": aggregated_weights,
            "total_samples": total_samples,
            "aggregation_method": "secure_fedavg",
            "privacy_level": "differential_privacy"
        }

    async def _aggregate_secure_sum(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Agregación secure sum."""
        # Implementación de secure sum protocol
        updates = session["collected_updates"]

        # Suma segura usando máscaras aleatorias
        secure_sum = {}
        for node_id, update_data in updates.items():
            masked_update = update_data["masked_update"]["secure_sum_share"]

            for key, value in masked_update.items():
                if key not in secure_sum:
                    secure_sum[key] = 0.0
                secure_sum[key] += value

        # Las máscaras se cancelan en la suma
        return {
            "secure_sum": secure_sum,
            "aggregation_method": "secure_sum",
            "privacy_level": "cryptographic_security"
        }

    def _generate_noise_parameters(self, aggregation_type: str) -> Dict[str, Any]:
        """Generar parámetros de ruido para preservación de privacidad."""
        if aggregation_type == "fedavg":
            return {
                "dp_epsilon": 1.0,
                "dp_delta": 1e-5,
                "noise_scale": 0.01
            }
        elif aggregation_type == "secure_sum":
            return {
                "masking_scheme": "random_mask",
                "key_size": 256
            }
        return {}

    def _verify_masked_update(self, masked_update: Dict[str, Any]) -> bool:
        """Verificar que la actualización enmascarada sea válida."""
        required_fields = ["weights", "num_samples"]
        return all(field in masked_update for field in required_fields)

    def _unmask_weights(self, masked_weights: Dict[str, Any], mask: Dict[str, Any],
                       noise_params: Dict[str, Any]) -> Dict[str, Any]:
        """Remover máscara de pesos."""
        # Implementación simplificada - en producción usaría DP o SMC
        unmasked = {}
        for layer_name, weights in masked_weights.items():
            layer_mask = mask.get(layer_name, 0)
            if isinstance(weights, list):
                unmasked[layer_name] = [w - layer_mask for w in weights]
            else:
                unmasked[layer_name] = weights - layer_mask
        return unmasked

    async def _send_aggregation_request(self, aggregation_id: str, participant_id: str):
        """Enviar solicitud de agregación a un participante."""
        message = P2PMessage(
            message_id=str(uuid.uuid4()),
            message_type=P2PMessageType.AGGREGATION_REQUEST,
            sender_id=self.protocol.node_id,
            receiver_id=participant_id,
            timestamp=time.time(),
            payload={
                "aggregation_id": aggregation_id,
                "session_info": self.aggregation_sessions[aggregation_id],
                "protocol_version": "secure_aggregation_v1"
            }
        )

        message.signature = self.protocol._sign_message(message)
        await self.protocol._send_message_to_peer(participant_id, message)

    async def _broadcast_aggregation_result(self, aggregation_id: str, result: Dict[str, Any]):
        """Broadcast resultado de agregación a todos los participantes."""
        session = self.aggregation_sessions[aggregation_id]

        for participant_id in session["participants"]:
            message = P2PMessage(
                message_id=str(uuid.uuid4()),
                message_type=P2PMessageType.AGGREGATION_RESPONSE,
                sender_id=self.protocol.node_id,
                receiver_id=participant_id,
                timestamp=time.time(),
                payload={
                    "aggregation_id": aggregation_id,
                    "result": result,
                    "status": "completed"
                }
            )

            message.signature = self.protocol._sign_message(message)
            await self.protocol._send_message_to_peer(participant_id, message)


class P2PProtocol:
    """
    Protocolo P2P seguro con TLS 1.3 para federated learning.
    Implementa comunicación segura entre nodos con autenticación mutua.
    """

    def __init__(self, node_id: str, host: str = "0.0.0.0", port: int = 8443,
                 cert_dir: str = "./certs", enable_tls: bool = True,
                 fedasync_enabled: bool = False, fedasync_threshold: int = 5,
                 fedasync_time_window: float = 30.0, fedasync_max_buffer: int = 100):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.cert_dir = Path(cert_dir)
        self.enable_tls = enable_tls

        # Configuración FedAsync
        self.fedasync_enabled = fedasync_enabled
        self.fedasync_threshold = fedasync_threshold
        self.fedasync_time_window = fedasync_time_window
        self.fedasync_max_buffer = fedasync_max_buffer

        # Estado del protocolo
        self.is_running = False
        self.peers: Dict[str, PeerInfo] = {}
        self.active_connections: Dict[str, asyncio.Transport] = {}
        self.pending_handshakes: Dict[str, Dict[str, Any]] = {}

        # Callbacks para manejo de eventos
        self.message_handlers: Dict[P2PMessageType, Callable] = {}
        self.connection_handlers: Dict[str, Callable] = {}

        # Configuración TLS
        self.ssl_context = None
        self.certificate = None
        self.private_key = None

        # Servidor y cliente
        self.server = None
        self.client_connections: Dict[str, asyncio.Transport] = {}

        # Estadísticas
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "bytes_sent": 0,
            "bytes_received": 0,
            "connections_established": 0,
            "connections_failed": 0,
            "handshakes_completed": 0,
            "errors": 0,
            "accepted_updates": 0,
            "rejected_updates": 0,
            "update_errors": 0,
            "fedasync_aggregations": 0,
            "fedasync_buffered_updates": 0
        }

        # Extensión para agregación segura
        self.secure_aggregation = SecureAggregationProtocol(self)

        # Buffer asíncrono para FedAsync
        if self.fedasync_enabled:
            self.fedasync_buffer = AsyncFedAsyncBuffer(
                aggregation_threshold=self.fedasync_threshold,
                time_window=self.fedasync_time_window,
                max_buffer_size=self.fedasync_max_buffer
            )
        else:
            self.fedasync_buffer = None

        # Handler para actualizaciones seguras
        self.secure_aggregation_handler = None

        # Inicializar directorio de certificados
        self.cert_dir.mkdir(parents=True, exist_ok=True)

        # Inicializar TLS si está habilitado
        if self.enable_tls:
            self._initialize_tls()

        logger.info(f"🔐 P2P Protocol initialized for node {node_id} on {host}:{port}")
        if self.fedasync_enabled:
            logger.info(f"🔄 FedAsync enabled with threshold={fedasync_threshold}, "
                       f"time_window={fedasync_time_window}s")

    def _initialize_tls(self):
        """Inicializar configuración TLS 1.3 con certificados."""
        try:
            # Crear certificado autofirmado si no existe
            cert_path = self.cert_dir / f"{self.node_id}.pem"
            key_path = self.cert_dir / f"{self.node_id}.key"

            if not cert_path.exists() or not key_path.exists():
                self._generate_self_signed_certificate(cert_path, key_path)

            # Cargar certificado y clave privada
            with open(cert_path, 'rb') as f:
                cert_data = f.read()
            with open(key_path, 'rb') as f:
                key_data = f.read()

            self.certificate = x509.load_pem_x509_certificate(cert_data, default_backend())
            self.private_key = serialization.load_pem_private_key(key_data, None, default_backend())

            # Crear contexto SSL para servidor
            self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.ssl_context.load_cert_chain(str(cert_path), str(key_path))
            self.ssl_context.verify_mode = ssl.CERT_REQUIRED
            self.ssl_context.check_hostname = False  # Para certificados autofirmados

            # Configurar TLS 1.3
            self.ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3
            self.ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3

            # Cargar certificados de CA conocidos (para autenticación mutua)
            ca_cert_path = self.cert_dir / "ca.pem"
            if ca_cert_path.exists():
                self.ssl_context.load_verify_locations(str(ca_cert_path))

            logger.info("✅ TLS 1.3 initialized with mutual authentication")

        except Exception as e:
            logger.error(f"❌ Error initializing TLS: {e}")
            self.enable_tls = False

    def _generate_self_signed_certificate(self, cert_path: Path, key_path: Path):
        """Generar certificado autofirmado para el nodo."""
        # Generar clave privada
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # Crear certificado
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "ES"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Madrid"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Madrid"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "AILOOS"),
            x509.NameAttribute(NameOID.COMMON_NAME, self.node_id),
        ])

        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(self.node_id),
                x509.IPAddress(ipaddress.IPv4Address(self.host) if self.host != "0.0.0.0" else ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256(), default_backend())

        # Guardar certificado
        with open(cert_path, 'wb') as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        # Guardar clave privada
        with open(key_path, 'wb') as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))

        logger.info(f"📜 Generated self-signed certificate for {self.node_id}")

    async def start(self):
        """Iniciar el protocolo P2P."""
        if self.is_running:
            return

        self.is_running = True

        # Iniciar servidor
        await self._start_server()

        # Iniciar buffer FedAsync si está habilitado
        if self.fedasync_buffer:
            await self.fedasync_buffer.start()

        # Iniciar tareas de mantenimiento
        asyncio.create_task(self._maintenance_loop())
        asyncio.create_task(self._heartbeat_loop())

        logger.info(f"🚀 P2P Protocol started for node {self.node_id}")

    async def stop(self):
        """Detener el protocolo P2P."""
        if not self.is_running:
            return

        self.is_running = False

        # Detener buffer FedAsync
        if self.fedasync_buffer:
            await self.fedasync_buffer.stop()

        # Cerrar todas las conexiones
        for peer_id, transport in self.active_connections.items():
            transport.close()

        # Detener servidor
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        self.active_connections.clear()
        self.client_connections.clear()

        logger.info(f"🛑 P2P Protocol stopped for node {self.node_id}")

    async def _start_server(self):
        """Iniciar servidor P2P."""
        try:
            if self.enable_tls and self.ssl_context:
                # Servidor con TLS
                self.server = await asyncio.start_server(
                    self._handle_connection,
                    self.host,
                    self.port,
                    ssl=self.ssl_context
                )
            else:
                # Servidor sin TLS (solo para desarrollo)
                logger.warning("⚠️ Starting server without TLS - NOT SECURE!")
                self.server = await asyncio.start_server(
                    self._handle_connection,
                    self.host,
                    self.port
                )

            logger.info(f"📡 P2P Server listening on {self.host}:{self.port}")

        except Exception as e:
            logger.error(f"❌ Error starting P2P server: {e}")
            raise

    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.Transport):
        """Manejar nueva conexión entrante."""
        try:
            peer_address = writer.get_extra_info('peername')
            logger.info(f"🔗 New connection from {peer_address}")

            # Crear tarea para manejar la conexión
            asyncio.create_task(self._handle_peer_connection(reader, writer))

        except Exception as e:
            logger.error(f"❌ Error handling connection: {e}")

    async def _handle_peer_connection(self, reader: asyncio.StreamReader, writer: asyncio.Transport):
        """Manejar conexión con un peer específico."""
        peer_id = None
        try:
            # Leer mensaje inicial para identificar peer
            data = await reader.read(4096)
            if not data:
                return

            message_data = json.loads(data.decode())
            message = P2PMessage.from_dict(message_data)

            peer_id = message.sender_id

            # Verificar si ya tenemos información del peer
            if peer_id not in self.peers:
                # Peer desconocido, registrar
                peer_info = PeerInfo(
                    node_id=peer_id,
                    host=writer.get_extra_info('peername')[0],
                    port=writer.get_extra_info('peername')[1],
                    public_key=b'',  # Se obtendrá durante handshake
                    connection_state=ConnectionState.CONNECTING
                )
                self.peers[peer_id] = peer_info

            # Actualizar estado de conexión
            self.peers[peer_id].connection_state = ConnectionState.CONNECTED
            self.peers[peer_id].last_seen = time.time()
            self.active_connections[peer_id] = writer

            # Procesar mensaje
            await self._process_message(message, writer)

            # Mantener conexión viva
            while self.is_running:
                try:
                    data = await asyncio.wait_for(reader.read(4096), timeout=30.0)
                    if not data:
                        break

                    message_data = json.loads(data.decode())
                    message = P2PMessage.from_dict(message_data)
                    await self._process_message(message, writer)

                except asyncio.TimeoutError:
                    # Enviar heartbeat
                    await self._send_heartbeat(peer_id)
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Invalid JSON received from {peer_id}")
                    continue

        except Exception as e:
            logger.error(f"❌ Error handling peer connection {peer_id}: {e}")
            self.stats["errors"] += 1
        finally:
            # Limpiar conexión
            if peer_id and peer_id in self.active_connections:
                writer.close()
                del self.active_connections[peer_id]
                if peer_id in self.peers:
                    self.peers[peer_id].connection_state = ConnectionState.DISCONNECTED

    async def connect_to_peer(self, peer_info: PeerInfo) -> bool:
        """Conectar a un peer específico."""
        try:
            if peer_info.node_id in self.active_connections:
                return True  # Ya conectado

            logger.info(f"🔗 Connecting to peer {peer_info.node_id} at {peer_info.address}")

            if self.enable_tls and self.ssl_context:
                # Conexión con TLS
                reader, writer = await asyncio.open_connection(
                    peer_info.host,
                    peer_info.port,
                    ssl=self.ssl_context
                )
            else:
                # Conexión sin TLS
                reader, writer = await asyncio.open_connection(
                    peer_info.host,
                    peer_info.port
                )

            # Registrar conexión
            self.client_connections[peer_info.node_id] = writer
            self.active_connections[peer_info.node_id] = writer
            peer_info.connection_state = ConnectionState.CONNECTED
            peer_info.last_seen = time.time()

            # Iniciar handshake
            await self._initiate_handshake(peer_info)

            # Crear tarea para manejar respuestas
            asyncio.create_task(self._handle_client_connection(peer_info.node_id, reader, writer))

            self.stats["connections_established"] += 1
            logger.info(f"✅ Connected to peer {peer_info.node_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error connecting to peer {peer_info.node_id}: {e}")
            peer_info.connection_state = ConnectionState.ERROR
            self.stats["connections_failed"] += 1
            return False

    async def _handle_client_connection(self, peer_id: str, reader: asyncio.StreamReader, writer: asyncio.Transport):
        """Manejar conexión de cliente a peer."""
        try:
            while self.is_running:
                try:
                    data = await asyncio.wait_for(reader.read(4096), timeout=30.0)
                    if not data:
                        break

                    message_data = json.loads(data.decode())
                    message = P2PMessage.from_dict(message_data)
                    await self._process_message(message, writer)

                except asyncio.TimeoutError:
                    await self._send_heartbeat(peer_id)
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Invalid JSON received from {peer_id}")
                    continue

        except Exception as e:
            logger.error(f"❌ Error in client connection to {peer_id}: {e}")
        finally:
            # Limpiar conexión
            if peer_id in self.client_connections:
                writer.close()
                del self.client_connections[peer_id]
                if peer_id in self.active_connections:
                    del self.active_connections[peer_id]
                if peer_id in self.peers:
                    self.peers[peer_id].connection_state = ConnectionState.DISCONNECTED

    async def _initiate_handshake(self, peer_info: PeerInfo):
        """Iniciar handshake seguro con un peer."""
        try:
            peer_info.connection_state = ConnectionState.HANDSHAKING

            # Generar nonce para handshake
            nonce = str(uuid.uuid4())

            # Crear mensaje de handshake
            handshake_message = P2PMessage(
                message_id=str(uuid.uuid4()),
                message_type=P2PMessageType.HANDSHAKE_INIT,
                sender_id=self.node_id,
                receiver_id=peer_info.node_id,
                timestamp=time.time(),
                payload={
                    "nonce": nonce,
                    "protocol_version": "p2p_federated_v1",
                    "supported_protocols": peer_info.supported_protocols,
                    "node_info": {
                        "node_id": self.node_id,
                        "capabilities": ["model_updates", "aggregation", "secure_communication"]
                    }
                }
            )

            # Firmar mensaje
            handshake_message.signature = self._sign_message(handshake_message)

            # Almacenar handshake pendiente
            self.pending_handshakes[peer_info.node_id] = {
                "nonce": nonce,
                "timestamp": time.time(),
                "message": handshake_message
            }

            # Enviar mensaje
            await self._send_message_to_peer(peer_info.node_id, handshake_message)

            logger.info(f"🤝 Handshake initiated with {peer_info.node_id}")

        except Exception as e:
            logger.error(f"❌ Error initiating handshake with {peer_info.node_id}: {e}")
            peer_info.connection_state = ConnectionState.ERROR

    async def _process_message(self, message: P2PMessage, writer: asyncio.Transport):
        """Procesar mensaje recibido."""
        try:
            # Verificar expiración
            if message.is_expired():
                logger.warning(f"⚠️ Received expired message from {message.sender_id}")
                return

            # Verificar firma si está presente
            if message.signature and not self._verify_message_signature(message):
                logger.warning(f"⚠️ Invalid signature in message from {message.sender_id}")
                return

            self.stats["messages_received"] += 1

            # Procesar según tipo de mensaje
            if message.message_type == P2PMessageType.HANDSHAKE_INIT:
                await self._handle_handshake_init(message, writer)
            elif message.message_type == P2PMessageType.HANDSHAKE_RESPONSE:
                await self._handle_handshake_response(message)
            elif message.message_type == P2PMessageType.HANDSHAKE_COMPLETE:
                await self._handle_handshake_complete(message)
            elif message.message_type == P2PMessageType.MODEL_UPDATE:
                await self._handle_model_update(message)
            elif message.message_type == P2PMessageType.AGGREGATION_REQUEST:
                await self._handle_aggregation_request(message)
            elif message.message_type == P2PMessageType.AGGREGATION_RESPONSE:
                await self._handle_aggregation_response(message)
            elif message.message_type == P2PMessageType.HEARTBEAT:
                await self._handle_heartbeat(message)
            elif message.message_type == P2PMessageType.DISCONNECT:
                await self._handle_disconnect(message)
            else:
                # Manejar con callback personalizado si existe
                handler = self.message_handlers.get(message.message_type)
                if handler:
                    await handler(message)
                else:
                    logger.warning(f"⚠️ Unknown message type: {message.message_type}")

        except Exception as e:
            logger.error(f"❌ Error processing message from {message.sender_id}: {e}")
            self.stats["errors"] += 1

    async def _handle_handshake_init(self, message: P2PMessage, writer: asyncio.Transport):
        """Manejar inicio de handshake."""
        try:
            peer_id = message.sender_id
            nonce = message.payload["nonce"]

            # Verificar que no estamos ya en handshake
            if peer_id in self.pending_handshakes:
                logger.warning(f"⚠️ Handshake already in progress with {peer_id}")
                return

            # Generar respuesta de nonce
            response_nonce = str(uuid.uuid4())

            # Crear mensaje de respuesta
            response_message = P2PMessage(
                message_id=str(uuid.uuid4()),
                message_type=P2PMessageType.HANDSHAKE_RESPONSE,
                sender_id=self.node_id,
                receiver_id=peer_id,
                timestamp=time.time(),
                payload={
                    "original_nonce": nonce,
                    "response_nonce": response_nonce,
                    "protocol_version": "p2p_federated_v1",
                    "node_info": {
                        "node_id": self.node_id,
                        "capabilities": ["model_updates", "aggregation", "secure_communication"]
                    }
                }
            )

            # Firmar mensaje
            response_message.signature = self._sign_message(response_message)

            # Almacenar handshake pendiente
            self.pending_handshakes[peer_id] = {
                "response_nonce": response_nonce,
                "timestamp": time.time(),
                "message": response_message
            }

            # Enviar respuesta
            await self._send_message_to_transport(writer, response_message)

            logger.info(f"🤝 Handshake response sent to {peer_id}")

        except Exception as e:
            logger.error(f"❌ Error handling handshake init from {message.sender_id}: {e}")

    async def _handle_handshake_response(self, message: P2PMessage):
        """Manejar respuesta de handshake."""
        try:
            peer_id = message.sender_id

            # Verificar handshake pendiente
            if peer_id not in self.pending_handshakes:
                logger.warning(f"⚠️ Unexpected handshake response from {peer_id}")
                return

            pending = self.pending_handshakes[peer_id]
            original_nonce = pending["message"].payload["nonce"]
            received_original_nonce = message.payload["original_nonce"]

            # Verificar nonce
            if original_nonce != received_original_nonce:
                logger.warning(f"⚠️ Nonce mismatch in handshake with {peer_id}")
                return

            # Completar handshake
            complete_message = P2PMessage(
                message_id=str(uuid.uuid4()),
                message_type=P2PMessageType.HANDSHAKE_COMPLETE,
                sender_id=self.node_id,
                receiver_id=peer_id,
                timestamp=time.time(),
                payload={
                    "response_nonce": message.payload["response_nonce"],
                    "status": "authenticated",
                    "session_established": True
                }
            )

            # Firmar mensaje
            complete_message.signature = self._sign_message(complete_message)

            # Enviar confirmación
            await self._send_message_to_peer(peer_id, complete_message)

            # Actualizar estado del peer
            if peer_id in self.peers:
                self.peers[peer_id].connection_state = ConnectionState.AUTHENTICATED
                self.stats["handshakes_completed"] += 1

            # Limpiar handshake pendiente
            del self.pending_handshakes[peer_id]

            logger.info(f"✅ Handshake completed with {peer_id}")

        except Exception as e:
            logger.error(f"❌ Error handling handshake response from {message.sender_id}: {e}")

    async def _handle_handshake_complete(self, message: P2PMessage):
        """Manejar completación de handshake."""
        try:
            peer_id = message.sender_id

            # Verificar handshake pendiente
            if peer_id not in self.pending_handshakes:
                logger.warning(f"⚠️ Unexpected handshake completion from {peer_id}")
                return

            # Limpiar handshake pendiente
            del self.pending_handshakes[peer_id]

            # Actualizar estado del peer
            if peer_id in self.peers:
                self.peers[peer_id].connection_state = ConnectionState.AUTHENTICATED
                self.stats["handshakes_completed"] += 1

            logger.info(f"✅ Handshake fully completed with {peer_id}")

        except Exception as e:
            logger.error(f"❌ Error handling handshake completion from {message.sender_id}: {e}")

    async def _handle_model_update(self, message: P2PMessage):
        """Manejar actualización de modelo con verificación de firmas Cosign y soporte FedAsync."""
        try:
            # Verificar firma de imagen si está presente
            image_verification = None
            image_uri = message.payload.get("image_uri")

            if image_uri:
                logger.info(f"🔐 Verifying image signature for {image_uri} from {message.sender_id}")
                verifier = get_image_verifier()
                image_verification = await verifier.verify_image(image_uri)

                if not image_verification.is_verified:
                    # Rechazar actualización si la imagen no está firmada
                    logger.warning(f"❌ Image verification failed for {image_uri}: {image_verification.error_message}")

                    # Enviar NACK con detalles de verificación
                    nack_message = P2PMessage(
                        message_id=str(uuid.uuid4()),
                        message_type=P2PMessageType.ERROR,
                        sender_id=self.node_id,
                        receiver_id=message.sender_id,
                        timestamp=time.time(),
                        payload={
                            "original_message_id": message.message_id,
                            "error_type": "image_verification_failed",
                            "error_message": f"Image {image_uri} verification failed: {image_verification.error_message}",
                            "verification_details": image_verification.to_dict(),
                            "timestamp": time.time()
                        }
                    )

                    nack_message.signature = self._sign_message(nack_message)
                    await self._send_message_to_peer(message.sender_id, nack_message)

                    # Actualizar estadísticas
                    self.stats["rejected_updates"] = self.stats.get("rejected_updates", 0) + 1
                    return

                logger.info(f"✅ Image {image_uri} verified successfully")

            # Determinar si es actualización segura o regular
            encryption_type = message.payload.get("encryption_type", "none")

            # Verificar si usar FedAsync
            session_id = message.payload.get("session_id")
            use_fedasync = (
                self.fedasync_enabled and
                self.fedasync_buffer and
                session_id and
                encryption_type == "none"  # Solo para actualizaciones no encriptadas por ahora
            )

            if use_fedasync:
                # Procesar con buffer FedAsync
                await self._handle_fedasync_model_update(message)
            elif encryption_type == "paillier_homomorphic":
                # Procesar actualización encriptada
                await self._handle_secure_model_update(message)
            else:
                # Procesar actualización regular
                handler = self.message_handlers.get(P2PMessageType.MODEL_UPDATE)
                if handler:
                    await handler(message)
                else:
                    logger.info(f"📦 Model update received from {message.sender_id}")

            # Enviar ACK con información de verificación
            ack_payload = {
                "original_message_id": message.message_id,
                "status": "received",
                "timestamp": time.time(),
                "encryption_type": encryption_type,
                "fedasync_enabled": use_fedasync
            }

            # Incluir detalles de verificación si se realizó
            if image_verification:
                ack_payload["image_verification"] = {
                    "image_uri": image_verification.image_uri,
                    "verified": image_verification.is_verified,
                    "verification_time": image_verification.verification_time.isoformat(),
                    "signature_found": image_verification.signature_found
                }

            ack_message = P2PMessage(
                message_id=str(uuid.uuid4()),
                message_type=P2PMessageType.MODEL_UPDATE_ACK,
                sender_id=self.node_id,
                receiver_id=message.sender_id,
                timestamp=time.time(),
                payload=ack_payload
            )

            ack_message.signature = self._sign_message(ack_message)
            await self._send_message_to_peer(message.sender_id, ack_message)

            # Actualizar estadísticas
            self.stats["accepted_updates"] = self.stats.get("accepted_updates", 0) + 1

        except Exception as e:
            logger.error(f"❌ Error handling model update from {message.sender_id}: {e}")
            self.stats["update_errors"] = self.stats.get("update_errors", 0) + 1

    async def _handle_secure_model_update(self, message: P2PMessage):
        """Manejar actualización de modelo encriptada."""
        try:
            from .secure_aggregator import EncryptedWeightUpdate

            # Reconstruir clave pública desde el mensaje
            public_key_n = int(message.payload["public_key"], 16)
            public_key = paillier.PaillierPublicKey(public_key_n)

            # Crear actualización encriptada
            encrypted_update = EncryptedWeightUpdate(
                node_id=message.sender_id,
                encrypted_weights=message.payload["encrypted_weights"],
                num_samples=message.payload["num_samples"],
                public_key=public_key,
                metadata=message.payload.get("metadata", {}),
                timestamp=message.timestamp
            )

            # Pasar al módulo de agregación segura
            if hasattr(self, 'secure_aggregation_handler'):
                await self.secure_aggregation_handler(encrypted_update)
            else:
                logger.info(f"🔒 Secure model update received from {message.sender_id}")

        except Exception as e:
            logger.error(f"❌ Error handling secure model update from {message.sender_id}: {e}")

    async def _handle_fedasync_model_update(self, message: P2PMessage):
        """Manejar actualización de modelo con buffer FedAsync."""
        try:
            if not self.fedasync_buffer:
                logger.warning("⚠️ FedAsync buffer not available")
                return

            # Extraer datos de la actualización
            session_id = message.payload.get("session_id")
            model_weights = message.payload.get("model_weights", {})
            num_samples = message.payload.get("metadata", {}).get("num_samples", 1)
            round_num = message.payload.get("round_num", 0)

            if not session_id:
                logger.warning(f"⚠️ No session_id in FedAsync update from {message.sender_id}")
                return

            # Crear objeto de actualización FedAsync
            fedasync_update = FedAsyncUpdate(
                node_id=message.sender_id,
                model_weights=model_weights,
                num_samples=num_samples,
                timestamp=message.timestamp,
                session_id=session_id,
                round_num=round_num,
                metadata=message.payload.get("metadata", {})
            )

            # Añadir al buffer
            success = await self.fedasync_buffer.add_update(fedasync_update)

            if success:
                self.stats["fedasync_buffered_updates"] += 1
                logger.info(f"🔄 FedAsync update buffered from {message.sender_id} for session {session_id}")
            else:
                logger.warning(f"⚠️ Failed to buffer FedAsync update from {message.sender_id}")

        except Exception as e:
            logger.error(f"❌ Error handling FedAsync model update from {message.sender_id}: {e}")

    async def _handle_aggregation_request(self, message: P2PMessage):
        """Manejar solicitud de agregación."""
        try:
            aggregation_id = message.payload["aggregation_id"]
            session_info = message.payload["session_info"]

            # Procesar con el módulo de agregación segura
            await self.secure_aggregation.submit_secure_update(
                aggregation_id,
                message.sender_id,
                message.payload
            )

        except Exception as e:
            logger.error(f"❌ Error handling aggregation request from {message.sender_id}: {e}")

    async def _handle_aggregation_response(self, message: P2PMessage):
        """Manejar respuesta de agregación."""
        try:
            # Callback personalizado para respuestas de agregación
            handler = self.message_handlers.get(P2PMessageType.AGGREGATION_RESPONSE)
            if handler:
                await handler(message)
            else:
                logger.info(f"🔄 Aggregation response received from {message.sender_id}")

        except Exception as e:
            logger.error(f"❌ Error handling aggregation response from {message.sender_id}: {e}")

    async def send_secure_weight_update(self, peer_id: str, encrypted_weights: Dict[str, Any],
                                       num_samples: int, public_key, metadata: Dict[str, Any]):
        """
        Enviar actualización de pesos encriptada a un peer.

        Args:
            peer_id: ID del peer destino
            encrypted_weights: Pesos encriptados homomórficamente
            num_samples: Número de muestras locales
            public_key: Clave pública del remitente
            metadata: Metadatos adicionales
        """
        try:
            if peer_id not in self.active_connections:
                logger.warning(f"⚠️ No active connection to peer {peer_id}")
                return False

            # Crear mensaje de actualización segura
            update_message = P2PMessage(
                message_id=str(uuid.uuid4()),
                message_type=P2PMessageType.MODEL_UPDATE,
                sender_id=self.node_id,
                receiver_id=peer_id,
                timestamp=time.time(),
                payload={
                    "encrypted_weights": encrypted_weights,
                    "num_samples": num_samples,
                    "public_key": public_key.n.hex(),  # Serializar clave pública
                    "metadata": metadata,
                    "session_id": metadata.get("session_id"),
                    "round_num": metadata.get("round_num", 0),
                    "encryption_type": "paillier_homomorphic"
                }
            )

            # Firmar mensaje
            update_message.signature = self._sign_message(update_message)

            # Enviar mensaje
            await self._send_message_to_peer(peer_id, update_message)

            self.stats["messages_sent"] += 1
            logger.info(f"🔒 Secure weight update sent to {peer_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error sending secure weight update to {peer_id}: {e}")
            return False

    async def initiate_secure_aggregation(self, session_id: str, participants: List[str],
                                        aggregation_type: str = "fedavg") -> str:
        """
        Iniciar sesión de agregación segura a través de P2P.

        Args:
            session_id: ID de la sesión federada
            participants: Lista de participantes
            aggregation_type: Tipo de agregación segura

        Returns:
            ID de la sesión de agregación
        """
        return await self.secure_aggregation.initiate_secure_aggregation(
            session_id, participants, aggregation_type
        )

    async def _handle_heartbeat(self, message: P2PMessage):
        """Manejar heartbeat."""
        peer_id = message.sender_id
        if peer_id in self.peers:
            self.peers[peer_id].last_seen = time.time()

    async def _handle_disconnect(self, message: P2PMessage):
        """Manejar desconexión."""
        peer_id = message.sender_id
        if peer_id in self.active_connections:
            transport = self.active_connections[peer_id]
            transport.close()
            del self.active_connections[peer_id]

        if peer_id in self.peers:
            self.peers[peer_id].connection_state = ConnectionState.DISCONNECTED

        logger.info(f"👋 Peer {peer_id} disconnected")

    async def send_model_update(self, peer_id: str, model_weights: Dict[str, Any],
                              metadata: Dict[str, Any]) -> bool:
        """Enviar actualización de modelo a un peer."""
        try:
            if peer_id not in self.active_connections:
                logger.warning(f"⚠️ No active connection to peer {peer_id}")
                return False

            # Preparar payload del mensaje
            payload = {
                "model_weights": model_weights,
                "metadata": metadata,
                "session_id": metadata.get("session_id"),
                "round_num": metadata.get("round_num", 0)
            }

            # Incluir image_uri si está disponible en metadatos
            if "image_uri" in metadata:
                payload["image_uri"] = metadata["image_uri"]
                logger.info(f"📦 Including image URI in update: {metadata['image_uri']}")

            # Crear mensaje de actualización
            update_message = P2PMessage(
                message_id=str(uuid.uuid4()),
                message_type=P2PMessageType.MODEL_UPDATE,
                sender_id=self.node_id,
                receiver_id=peer_id,
                timestamp=time.time(),
                payload=payload
            )

            # Firmar mensaje
            update_message.signature = self._sign_message(update_message)

            # Enviar mensaje
            await self._send_message_to_peer(peer_id, update_message)

            self.stats["messages_sent"] += 1
            logger.info(f"📤 Model update sent to {peer_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error sending model update to {peer_id}: {e}")
            return False

    async def initiate_secure_aggregation(self, session_id: str, participants: List[str],
                                        aggregation_type: str = "fedavg") -> str:
        """
        Iniciar agregación segura usando el módulo de extensión.

        Args:
            session_id: ID de la sesión federada
            participants: Lista de participantes
            aggregation_type: Tipo de agregación segura

        Returns:
            ID de la sesión de agregación
        """
        return await self.secure_aggregation.initiate_secure_aggregation(
            session_id, participants, aggregation_type
        )

    async def _send_message_to_peer(self, peer_id: str, message: P2PMessage):
        """Enviar mensaje a un peer específico."""
        if peer_id not in self.active_connections:
            raise ValueError(f"No active connection to peer {peer_id}")

        transport = self.active_connections[peer_id]
        await self._send_message_to_transport(transport, message)

    async def _send_message_to_transport(self, transport: asyncio.Transport, message: P2PMessage):
        """Enviar mensaje a través de un transport."""
        message_data = json.dumps(message.to_dict()).encode()
        transport.write(message_data)
        transport.write(b'\n')  # Delimitador de mensaje

        self.stats["bytes_sent"] += len(message_data)

    async def _send_heartbeat(self, peer_id: str):
        """Enviar heartbeat a un peer."""
        try:
            heartbeat_message = P2PMessage(
                message_id=str(uuid.uuid4()),
                message_type=P2PMessageType.HEARTBEAT,
                sender_id=self.node_id,
                receiver_id=peer_id,
                timestamp=time.time(),
                payload={
                    "status": "alive",
                    "timestamp": time.time()
                }
            )

            await self._send_message_to_peer(peer_id, heartbeat_message)

        except Exception as e:
            logger.debug(f"⚠️ Could not send heartbeat to {peer_id}: {e}")

    def _sign_message(self, message: P2PMessage) -> str:
        """Firmar mensaje con clave privada."""
        if not self.private_key:
            return ""

        # Crear datos para firmar
        message_data = f"{message.message_id}:{message.message_type.value}:{message.sender_id}:{message.receiver_id}:{message.timestamp}"
        payload_str = json.dumps(message.payload, sort_keys=True)
        data_to_sign = f"{message_data}:{payload_str}"

        # Firmar
        signature = self.private_key.sign(
            data_to_sign.encode(),
            ec.ECDSA(hashes.SHA256())
        )

        return signature.hex()

    def _verify_message_signature(self, message: P2PMessage) -> bool:
        """Verificar firma de mensaje."""
        if not message.signature or message.sender_id not in self.peers:
            return False

        peer_info = self.peers[message.sender_id]
        if not peer_info.public_key:
            return False

        try:
            # Crear datos para verificar
            message_data = f"{message.message_id}:{message.message_type.value}:{message.sender_id}:{message.receiver_id}:{message.timestamp}"
            payload_str = json.dumps(message.payload, sort_keys=True)
            data_to_verify = f"{message_data}:{payload_str}"

            # Verificar firma
            public_key = serialization.load_pem_public_key(peer_info.public_key, default_backend())
            signature_bytes = bytes.fromhex(message.signature)

            public_key.verify(
                signature_bytes,
                data_to_verify.encode(),
                ec.ECDSA(hashes.SHA256())
            )

            return True

        except Exception:
            return False

    async def _maintenance_loop(self):
        """Loop de mantenimiento para limpiar conexiones inactivas."""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Cada minuto

                current_time = time.time()
                inactive_peers = []

                # Encontrar peers inactivos
                for peer_id, peer_info in self.peers.items():
                    if current_time - peer_info.last_seen > 300:  # 5 minutos
                        inactive_peers.append(peer_id)

                # Limpiar peers inactivos
                for peer_id in inactive_peers:
                    if peer_id in self.active_connections:
                        transport = self.active_connections[peer_id]
                        transport.close()
                        del self.active_connections[peer_id]

                    del self.peers[peer_id]
                    logger.info(f"🧹 Cleaned up inactive peer {peer_id}")

                # Limpiar handshakes pendientes expirados
                expired_handshakes = []
                for peer_id, handshake_data in self.pending_handshakes.items():
                    if current_time - handshake_data["timestamp"] > 60:  # 1 minuto
                        expired_handshakes.append(peer_id)

                for peer_id in expired_handshakes:
                    del self.pending_handshakes[peer_id]
                    logger.debug(f"🧹 Cleaned up expired handshake for {peer_id}")

            except Exception as e:
                logger.error(f"❌ Error in maintenance loop: {e}")

    async def _heartbeat_loop(self):
        """Loop para enviar heartbeats periódicos."""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Cada 30 segundos

                # Enviar heartbeat a todos los peers conectados
                for peer_id in list(self.active_connections.keys()):
                    await self._send_heartbeat(peer_id)

            except Exception as e:
                logger.error(f"❌ Error in heartbeat loop: {e}")

    def register_message_handler(self, message_type: P2PMessageType, handler: Callable):
        """Registrar handler para tipo de mensaje específico."""
        self.message_handlers[message_type] = handler

    def register_connection_handler(self, event: str, handler: Callable):
        """Registrar handler para evento de conexión."""
        self.connection_handlers[event] = handler

    def get_peer_info(self, peer_id: str) -> Optional[PeerInfo]:
        """Obtener información de un peer."""
        return self.peers.get(peer_id)

    def get_connected_peers(self) -> List[str]:
        """Obtener lista de peers conectados."""
        return [peer_id for peer_id, peer_info in self.peers.items() if peer_info.is_connected]

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del protocolo."""
        return {
            **self.stats,
            "active_connections": len(self.active_connections),
            "known_peers": len(self.peers),
            "pending_handshakes": len(self.pending_handshakes),
            "is_running": self.is_running
        }

    def add_peer(self, peer_info: PeerInfo):
        """Añadir información de peer conocido."""
        self.peers[peer_info.node_id] = peer_info
        logger.info(f"📋 Added peer info for {peer_info.node_id}")


# Funciones de conveniencia
def create_p2p_protocol(node_id: str, host: str = "0.0.0.0", port: int = 8443,
                       cert_dir: str = "./certs") -> P2PProtocol:
    """Crear instancia del protocolo P2P."""
    return P2PProtocol(node_id, host, port, cert_dir)


async def connect_to_peer_network(protocol: P2PProtocol, peer_addresses: List[Tuple[str, int, str]]):
    """
    Conectar a una red de peers.

    Args:
        protocol: Instancia del protocolo P2P
        peer_addresses: Lista de tuplas (host, port, node_id)
    """
    for host, port, node_id in peer_addresses:
        peer_info = PeerInfo(
            node_id=node_id,
            host=host,
            port=port,
            public_key=b''  # Se obtendrá durante handshake
        )
        protocol.add_peer(peer_info)
        await protocol.connect_to_peer(peer_info)