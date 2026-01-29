"""
Registro Distribuido de Nodos usando IPFS PubSub
Implementación completa de registro de nodos federados con firma X.509,
validación de firmas, cache local con TTL, replicación y compresión.
"""

import asyncio
import json
import time
import hashlib
import uuid
import zlib
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
import base64

try:
    import ipfshttpclient
    IPFS_AVAILABLE = True
except ImportError:
    IPFS_AVAILABLE = False

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend

from ..infrastructure.ipfs_embedded import IPFSManager
from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class NodeMetadata:
    """Metadatos completos de un nodo"""
    node_id: str
    hardware_capacity: Dict[str, Any]  # CPU, RAM, GPU, etc.
    reputation_score: float = 0.0
    location: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)
    registered_at: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    status: str = "active"  # active, inactive, suspended


@dataclass
class NodeRegistration:
    """Registro completo de un nodo con firma"""
    metadata: NodeMetadata
    signature: str  # Firma X.509 del metadato
    certificate_pem: str  # Certificado X.509
    public_key_pem: str  # Clave pública
    timestamp: datetime = field(default_factory=datetime.now)


class NodeRegistry:
    """
    Registro distribuido de nodos usando IPFS PubSub
    """

    def __init__(self, node_id: str, ipfs_manager: IPFSManager,
                 registry_topic: str = "ailoos_node_registry",
                 heartbeat_topic: str = "ailoos_node_heartbeat"):
        self.node_id = node_id
        self.ipfs = ipfs_manager
        self.registry_topic = registry_topic
        self.heartbeat_topic = heartbeat_topic

        # Cache local con TTL
        self.local_cache: Dict[str, Tuple[NodeRegistration, float]] = {}  # node_id -> (registration, expiry_time)
        self.cache_ttl = 300  # 5 minutos

        # Certificado y claves para este nodo
        self.private_key = None
        self.certificate = None
        self.public_key_pem = None

        # Estado del registro
        self.is_running = False
        self.known_nodes: Set[str] = set()

        # Compresión
        self.compression_level = 6

        # Replicación
        self.replication_factor = 3
        self.registry_cid = None  # CID del registro completo

    async def start(self):
        """Inicia el registro de nodos"""
        if self.is_running:
            return

        self.is_running = True
        logger.info(f"🚀 Starting NodeRegistry for {self.node_id}")

        # Generar certificado X.509 si no existe
        await self._ensure_certificate()

        # Suscribirse a topics
        await self._subscribe_topics()

        # Iniciar tareas de mantenimiento
        asyncio.create_task(self._maintenance_loop())
        asyncio.create_task(self._heartbeat_loop())

        # Auto-registrar este nodo
        await self._auto_register()

    async def stop(self):
        """Detiene el registro de nodos"""
        self.is_running = False
        logger.info("🛑 NodeRegistry stopped")

    async def register_node(self, metadata: NodeMetadata) -> bool:
        """
        Registra un nodo con firma X.509

        Args:
            metadata: Metadatos del nodo

        Returns:
            True si se registró exitosamente
        """
        try:
            # Crear registro con firma
            registration = await self._create_signed_registration(metadata)

            # Validar firma propia
            if not await self._validate_registration(registration):
                logger.error("Failed to validate own registration signature")
                return False

            # Comprimir y publicar
            compressed_data = self._compress_registration(registration)
            message = {
                'type': 'node_registration',
                'node_id': metadata.node_id,
                'data': base64.b64encode(compressed_data).decode(),
                'timestamp': datetime.now().isoformat()
            }

            # Publicar en PubSub
            await self._publish_to_topic(self.registry_topic, message)

            # Actualizar cache local
            self._update_cache(metadata.node_id, registration)

            # Replicar registro completo
            await self._replicate_registry()

            logger.info(f"✅ Registered node {metadata.node_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to register node {metadata.node_id}: {e}")
            return False

    async def discover_nodes(self, filters: Optional[Dict[str, Any]] = None) -> List[NodeRegistration]:
        """
        Descubre nodos con filtrado por criterios

        Args:
            filters: Criterios de filtrado

        Returns:
            Lista de registros que coinciden
        """
        try:
            # Obtener nodos de cache y red
            all_registrations = await self._get_all_registrations()

            # Aplicar filtros
            filtered = []
            for reg in all_registrations:
                if self._matches_filters(reg, filters):
                    filtered.append(reg)

            logger.debug(f"🔍 Discovered {len(filtered)} nodes matching filters")
            return filtered

        except Exception as e:
            logger.error(f"❌ Failed to discover nodes: {e}")
            return []

    async def deregister_node(self, node_id: str) -> bool:
        """
        Desregistra un nodo (desconexión automática)

        Args:
            node_id: ID del nodo

        Returns:
            True si se desregistró exitosamente
        """
        try:
            # Verificar que somos el propietario o autorizados
            if node_id != self.node_id:
                logger.warning(f"Cannot deregister node {node_id}: not authorized")
                return False

            # Publicar mensaje de desregistro
            message = {
                'type': 'node_deregistration',
                'node_id': node_id,
                'timestamp': datetime.now().isoformat()
            }

            await self._publish_to_topic(self.registry_topic, message)

            # Remover de cache local
            self.local_cache.pop(node_id, None)
            self.known_nodes.discard(node_id)

            # Replicar registro actualizado
            await self._replicate_registry()

            logger.info(f"✅ Deregistered node {node_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to deregister node {node_id}: {e}")
            return False

    async def _create_signed_registration(self, metadata: NodeMetadata) -> NodeRegistration:
        """Crea un registro firmado con X.509"""
        # Serializar metadatos
        metadata_dict = asdict(metadata)
        metadata_json = json.dumps(metadata_dict, sort_keys=True, default=str)

        # Firmar con clave privada
        signature = self.private_key.sign(
            metadata_json.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        # Crear registro
        registration = NodeRegistration(
            metadata=metadata,
            signature=base64.b64encode(signature).decode(),
            certificate_pem=self.certificate.public_bytes(serialization.Encoding.PEM).decode(),
            public_key_pem=self.public_key_pem
        )

        return registration

    async def _validate_registration(self, registration: NodeRegistration) -> bool:
        """
        Valida la firma de un registro para prevenir Sybil attacks
        """
        try:
            # Verificar certificado
            cert = x509.load_pem_x509_certificate(
                registration.certificate_pem.encode(),
                default_backend()
            )

            # Verificar que no haya expirado
            now = datetime.now()
            if now < cert.not_valid_before or now > cert.not_valid_after:
                logger.warning("Certificate expired or not yet valid")
                return False

            # Extraer clave pública
            public_key = cert.public_key()

            # Verificar firma
            metadata_dict = asdict(registration.metadata)
            metadata_json = json.dumps(metadata_dict, sort_keys=True, default=str)

            signature_bytes = base64.b64decode(registration.signature)

            public_key.verify(
                signature_bytes,
                metadata_json.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

            # Verificar reputación mínima (anti-Sybil)
            if registration.metadata.reputation_score < -10.0:
                logger.warning(f"Node {registration.metadata.node_id} has bad reputation")
                return False

            return True

        except Exception as e:
            logger.warning(f"Signature validation failed: {e}")
            return False

    def _compress_registration(self, registration: NodeRegistration) -> bytes:
        """Comprime un registro para transmisión eficiente"""
        data = json.dumps(asdict(registration), default=str).encode()
        return zlib.compress(data, level=self.compression_level)

    def _decompress_registration(self, compressed_data: bytes) -> NodeRegistration:
        """Descomprime un registro"""
        data = zlib.decompress(compressed_data)
        reg_dict = json.loads(data.decode())

        # Reconstruir objetos
        metadata = NodeMetadata(**reg_dict['metadata'])
        metadata.registered_at = datetime.fromisoformat(reg_dict['metadata']['registered_at'])
        metadata.last_seen = datetime.fromisoformat(reg_dict['metadata']['last_seen'])

        registration = NodeRegistration(
            metadata=metadata,
            signature=reg_dict['signature'],
            certificate_pem=reg_dict['certificate_pem'],
            public_key_pem=reg_dict['public_key_pem'],
            timestamp=datetime.fromisoformat(reg_dict['timestamp'])
        )

        return registration

    async def _publish_to_topic(self, topic: str, message: Dict[str, Any]):
        """Publica mensaje en topic IPFS PubSub"""
        try:
            if self.ipfs.use_real_ipfs and self.ipfs.ipfs_client:
                # Usar IPFS real
                message_json = json.dumps(message)
                self.ipfs.ipfs_client.pubsub.pub(topic, message_json)
            else:
                # Simulación - en producción requeriría IPFS
                logger.debug(f"📤 Would publish to {topic}: {message}")
        except Exception as e:
            logger.error(f"Failed to publish to topic {topic}: {e}")

    async def _subscribe_topics(self):
        """Suscribe a topics de PubSub"""
        try:
            if self.ipfs.use_real_ipfs and self.ipfs.ipfs_client:
                # Suscribirse a topics
                self.ipfs.ipfs_client.pubsub.sub(self.registry_topic, self._handle_registry_message)
                self.ipfs.ipfs_client.pubsub.sub(self.heartbeat_topic, self._handle_heartbeat_message)
                logger.info(f"📡 Subscribed to topics: {self.registry_topic}, {self.heartbeat_topic}")
            else:
                logger.warning("IPFS not available - PubSub subscriptions disabled")
        except Exception as e:
            logger.error(f"Failed to subscribe to topics: {e}")

    def _handle_registry_message(self, topic, data):
        """Maneja mensajes del topic de registro"""
        try:
            message = json.loads(data['data'].decode())
            msg_type = message.get('type')

            if msg_type == 'node_registration':
                asyncio.create_task(self._handle_node_registration(message))
            elif msg_type == 'node_deregistration':
                asyncio.create_task(self._handle_node_deregistration(message))

        except Exception as e:
            logger.error(f"Failed to handle registry message: {e}")

    def _handle_heartbeat_message(self, topic, data):
        """Maneja mensajes de heartbeat"""
        try:
            message = json.loads(data['data'].decode())
            node_id = message.get('node_id')

            if node_id and node_id in self.known_nodes:
                # Actualizar last_seen
                if node_id in self.local_cache:
                    reg, _ = self.local_cache[node_id]
                    reg.metadata.last_seen = datetime.now()
                    self._update_cache(node_id, reg)

        except Exception as e:
            logger.error(f"Failed to handle heartbeat message: {e}")

    async def _handle_node_registration(self, message: Dict[str, Any]):
        """Procesa registro de nuevo nodo"""
        try:
            node_id = message['node_id']
            compressed_data = base64.b64decode(message['data'])
            registration = self._decompress_registration(compressed_data)

            # Validar firma
            if not await self._validate_registration(registration):
                logger.warning(f"Invalid registration for node {node_id}")
                return

            # Actualizar cache
            self._update_cache(node_id, registration)
            self.known_nodes.add(node_id)

            logger.info(f"📥 Received registration for node {node_id}")

        except Exception as e:
            logger.error(f"Failed to handle node registration: {e}")

    async def _handle_node_deregistration(self, message: Dict[str, Any]):
        """Procesa desregistro de nodo"""
        try:
            node_id = message['node_id']

            # Remover de cache
            self.local_cache.pop(node_id, None)
            self.known_nodes.discard(node_id)

            logger.info(f"📤 Node {node_id} deregistered")

        except Exception as e:
            logger.error(f"Failed to handle node deregistration: {e}")

    def _update_cache(self, node_id: str, registration: NodeRegistration):
        """Actualiza cache local con TTL"""
        expiry_time = time.time() + self.cache_ttl
        self.local_cache[node_id] = (registration, expiry_time)

    async def _get_all_registrations(self) -> List[NodeRegistration]:
        """Obtiene todos los registros conocidos"""
        # Limpiar cache expirada
        self._cleanup_expired_cache()

        # Retornar registros válidos
        return [reg for reg, _ in self.local_cache.values()]

    def _cleanup_expired_cache(self):
        """Limpia entradas expiradas de la cache"""
        current_time = time.time()
        expired = [node_id for node_id, (_, expiry) in self.local_cache.items()
                  if current_time > expiry]

        for node_id in expired:
            del self.local_cache[node_id]

        if expired:
            logger.debug(f"🧹 Cleaned {len(expired)} expired cache entries")

    def _matches_filters(self, registration: NodeRegistration, filters: Optional[Dict[str, Any]]) -> bool:
        """Verifica si un registro coincide con los filtros"""
        if not filters:
            return True

        meta = registration.metadata

        # Filtrar por capacidades
        if 'capabilities' in filters:
            required_caps = set(filters['capabilities'])
            node_caps = set(meta.capabilities)
            if not required_caps.issubset(node_caps):
                return False

        # Filtrar por ubicación
        if 'location' in filters and meta.location != filters['location']:
            return False

        # Filtrar por reputación mínima
        if 'min_reputation' in filters and meta.reputation_score < filters['min_reputation']:
            return False

        # Filtrar por capacidad hardware
        if 'min_hardware' in filters:
            hw_req = filters['min_hardware']
            hw_node = meta.hardware_capacity

            for key, min_val in hw_req.items():
                if key not in hw_node or hw_node[key] < min_val:
                    return False

        return True

    async def _ensure_certificate(self):
        """Asegura que tenemos un certificado X.509 válido"""
        if self.private_key and self.certificate:
            return

        # Generar clave privada RSA
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # Generar clave pública
        public_key = self.private_key.public_key()
        self.public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

        # Crear certificado auto-firmado
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "ES"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Madrid"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Madrid"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "AILOOS"),
            x509.NameAttribute(NameOID.COMMON_NAME, f"node-{self.node_id}"),
        ])

        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            public_key
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(f"node-{self.node_id}.ailoos.local"),
            ]),
            critical=False,
        ).sign(self.private_key, hashes.SHA256(), default_backend())

        self.certificate = cert
        logger.info("🔐 Generated X.509 certificate for node")

    async def _auto_register(self):
        """Auto-registra este nodo"""
        # Obtener metadatos del sistema (simplificado)
        metadata = NodeMetadata(
            node_id=self.node_id,
            hardware_capacity={
                'cpu_cores': 4,  # En producción, detectar real
                'ram_gb': 8,
                'gpu_count': 0
            },
            reputation_score=1.0,
            location="Madrid, ES",  # En producción, detectar
            capabilities=['federated_learning', 'coordination']
        )

        await self.register_node(metadata)

    async def _maintenance_loop(self):
        """Loop de mantenimiento"""
        while self.is_running:
            try:
                # Limpiar cache expirada
                self._cleanup_expired_cache()

                # Verificar salud de nodos conocidos
                await self._check_node_health()

                await asyncio.sleep(60)  # Cada minuto

            except Exception as e:
                logger.error(f"Maintenance loop error: {e}")
                await asyncio.sleep(30)

    async def _heartbeat_loop(self):
        """Envía heartbeats periódicos"""
        while self.is_running:
            try:
                # Enviar heartbeat
                message = {
                    'type': 'heartbeat',
                    'node_id': self.node_id,
                    'timestamp': datetime.now().isoformat()
                }

                await self._publish_to_topic(self.heartbeat_topic, message)
                await asyncio.sleep(30)  # Cada 30 segundos

            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
                await asyncio.sleep(10)

    async def _check_node_health(self):
        """Verifica salud de nodos conocidos"""
        now = datetime.now()
        inactive_nodes = []

        for node_id, (reg, _) in self.local_cache.items():
            # Marcar como inactivo si no heartbeat reciente
            if now - reg.metadata.last_seen > timedelta(minutes=2):
                if reg.metadata.status == 'active':
                    reg.metadata.status = 'inactive'
                    inactive_nodes.append(node_id)
                    logger.warning(f"💔 Node {node_id} marked as inactive")

        # Podría publicar actualizaciones de estado, pero por simplicidad omitido

    async def _replicate_registry(self):
        """Replica el registro completo para fault tolerance"""
        try:
            # Obtener todos los registros
            all_regs = await self._get_all_registrations()

            # Crear snapshot comprimido
            snapshot = {
                'version': datetime.now().isoformat(),
                'nodes': [asdict(reg) for reg in all_regs]
            }
            snapshot_json = json.dumps(snapshot, default=str)
            compressed_snapshot = zlib.compress(snapshot_json.encode(), level=self.compression_level)

            # Publicar en IPFS
            cid = await self.ipfs.publish_data(compressed_snapshot, {'type': 'node_registry_snapshot'})

            # Actualizar CID conocido
            self.registry_cid = cid

            # Podría publicar el CID en PubSub para que otros lo conozcan
            message = {
                'type': 'registry_snapshot',
                'cid': cid,
                'timestamp': datetime.now().isoformat()
            }
            await self._publish_to_topic(self.registry_topic, message)

            logger.debug(f"🔄 Replicated registry to IPFS: {cid}")

        except Exception as e:
            logger.error(f"Failed to replicate registry: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del registro"""
        return {
            'known_nodes': len(self.known_nodes),
            'cached_nodes': len(self.local_cache),
            'active_nodes': len([reg for reg, _ in self.local_cache.values()
                               if reg.metadata.status == 'active']),
            'registry_cid': self.registry_cid,
            'is_running': self.is_running
        }


# Singleton instance
_node_registry_instance: Optional[NodeRegistry] = None


def get_node_registry(ipfs_manager: Optional[IPFSManager] = None,
                     node_id: Optional[str] = None) -> Optional[NodeRegistry]:
    """
    Obtiene la instancia singleton del NodeRegistry

    Args:
        ipfs_manager: Instancia de IPFSManager (opcional)
        node_id: ID del nodo (opcional, por defecto usa UUID)

    Returns:
        Instancia de NodeRegistry o None si no se puede inicializar
    """
    global _node_registry_instance

    if _node_registry_instance is None:
        try:
            from ..infrastructure.ipfs_embedded import IPFSManager

            # Usar IPFS manager proporcionado o crear uno
            if ipfs_manager is None:
                ipfs_manager = IPFSManager()

            # Generar node_id si no se proporciona
            if node_id is None:
                node_id = str(uuid.uuid4())[:8]

            _node_registry_instance = NodeRegistry(node_id, ipfs_manager)

        except Exception as e:
            logger.error(f"Failed to initialize NodeRegistry: {e}")
            return None

    return _node_registry_instance