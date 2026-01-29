#!/usr/bin/env python3
"""
Protocolo de Mensajería P2P Core para AILOOS
Implementa comunicación peer-to-peer segura con compresión, validación de integridad
y compatibilidad con libp2p/IPFS.
"""

import asyncio
import gzip
import hashlib
import json
import logging
import secrets
import time
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

try:
    import libp2p
    from libp2p import host
    from libp2p.pubsub.pubsub import PubSub
    from libp2p.pubsub.gossipsub import GossipSub
    LIBP2P_AVAILABLE = True
except ImportError:
    LIBP2P_AVAILABLE = False
    logging.warning("libp2p no disponible, usando implementación simulada")

from ..core.logging import get_logger

logger = get_logger(__name__)


class P2PMessageType(Enum):
    """Tipos de mensajes P2P soportados."""
    HANDSHAKE = "handshake"
    WEIGHT_SYNC = "weight_sync"
    MODEL_UPDATE = "model_update"
    HEARTBEAT = "heartbeat"


@dataclass
class P2PMessage:
    """Mensaje P2P con compresión y validación de integridad."""
    message_id: str
    message_type: P2PMessageType
    sender_id: str
    recipient_id: Optional[str] = None  # None para broadcast
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    compressed: bool = False
    integrity_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convertir mensaje a diccionario para serialización."""
        return {
            'message_id': self.message_id,
            'message_type': self.message_type.value,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'payload': self.payload,
            'timestamp': self.timestamp,
            'compressed': self.compressed,
            'integrity_hash': self.integrity_hash
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'P2PMessage':
        """Crear mensaje desde diccionario."""
        return cls(
            message_id=data['message_id'],
            message_type=P2PMessageType(data['message_type']),
            sender_id=data['sender_id'],
            recipient_id=data.get('recipient_id'),
            payload=data.get('payload', {}),
            timestamp=data.get('timestamp', time.time()),
            compressed=data.get('compressed', False),
            integrity_hash=data.get('integrity_hash')
        )

    def calculate_integrity_hash(self) -> str:
        """Calcular hash SHA-256 para validación de integridad."""
        message_data = json.dumps({
            'message_id': self.message_id,
            'message_type': self.message_type.value,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'payload': self.payload,
            'timestamp': self.timestamp
        }, sort_keys=True).encode()

        return hashlib.sha256(message_data).hexdigest()

    def validate_integrity(self) -> bool:
        """Validar integridad del mensaje."""
        if not self.integrity_hash:
            return False
        return self.calculate_integrity_hash() == self.integrity_hash


class P2PMessageHandler:
    """
    Manejador de mensajería P2P con buffers, compresión y validación de integridad.
    Integra con libp2p para compatibilidad IPFS.
    """

    # Buffer size: ~1 MB por nodo
    MAX_BUFFER_SIZE = 1024 * 1024  # 1 MB

    def __init__(self, node_id: str, libp2p_host: Optional[Any] = None):
        """
        Inicializar el manejador de mensajería P2P.

        Args:
            node_id: ID único del nodo
            libp2p_host: Host libp2p opcional para integración
        """
        self.node_id = node_id
        self.libp2p_host = libp2p_host

        # Buffers de mensajes (Queue con límite de tamaño)
        self.message_buffer: asyncio.Queue[P2PMessage] = asyncio.Queue(maxsize=self.MAX_BUFFER_SIZE // 1024)  # ~1024 mensajes

        # Handlers de mensajes
        self.message_handlers: Dict[P2PMessageType, List[Callable]] = {}

        # Estado del handler
        self.is_running = False
        self.receive_task: Optional[asyncio.Task] = None

        # Estadísticas
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'bytes_sent': 0,
            'bytes_received': 0,
            'compression_ratio': 0.0,
            'integrity_failures': 0
        }

        # Protocolo libp2p
        self.protocol_id = "/ailoos/p2p-messaging/1.0.0"

        logger.info(f"🔄 P2PMessageHandler inicializado para nodo {node_id}")

    async def start(self):
        """Iniciar el manejador de mensajería."""
        if self.is_running:
            return

        self.is_running = True

        # Iniciar tarea de recepción
        self.receive_task = asyncio.create_task(self._receive_loop())

        # Configurar protocolo libp2p si disponible
        if LIBP2P_AVAILABLE and self.libp2p_host:
            await self._setup_libp2p_protocol()

        logger.info(f"🚀 P2PMessageHandler iniciado para nodo {self.node_id}")

    async def stop(self):
        """Detener el manejador de mensajería."""
        if not self.is_running:
            return

        self.is_running = False

        # Cancelar tarea de recepción
        if self.receive_task:
            self.receive_task.cancel()
            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass

        logger.info(f"🛑 P2PMessageHandler detenido para nodo {self.node_id}")

    async def send_message(self, message: P2PMessage) -> bool:
        """
        Enviar mensaje de forma asíncrona.

        Args:
            message: Mensaje P2P a enviar

        Returns:
            True si el envío fue exitoso
        """
        try:
            # Preparar mensaje
            await self._prepare_message(message)

            # Enviar según disponibilidad de libp2p
            if LIBP2P_AVAILABLE and self.libp2p_host:
                success = await self._send_via_libp2p(message)
            else:
                success = await self._send_via_fallback(message)

            if success:
                self.stats['messages_sent'] += 1
                self.stats['bytes_sent'] += len(json.dumps(message.to_dict()).encode())

                logger.debug(f"📤 Mensaje {message.message_id} enviado exitosamente")
            else:
                logger.warning(f"❌ Falló envío de mensaje {message.message_id}")

            return success

        except Exception as e:
            logger.error(f"❌ Error enviando mensaje {message.message_id}: {e}")
            return False

    async def receive_message(self) -> Optional[P2PMessage]:
        """
        Recibir mensaje de forma asíncrona.

        Returns:
            Mensaje P2P recibido o None si no hay mensajes
        """
        try:
            # Intentar obtener mensaje del buffer
            message = await asyncio.wait_for(
                self.message_buffer.get(),
                timeout=1.0
            )

            # Procesar mensaje recibido
            await self._process_received_message(message)

            self.stats['messages_received'] += 1
            self.stats['bytes_received'] += len(json.dumps(message.to_dict()).encode())

            logger.debug(f"📥 Mensaje {message.message_id} recibido")

            return message

        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error(f"❌ Error recibiendo mensaje: {e}")
            return None

    def register_message_handler(self, message_type: P2PMessageType, handler: Callable):
        """Registrar handler para tipo de mensaje específico."""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
        logger.debug(f"✅ Handler registrado para {message_type.value}")

    async def _prepare_message(self, message: P2PMessage):
        """Preparar mensaje para envío (compresión, integridad)."""
        # Calcular hash de integridad
        message.integrity_hash = message.calculate_integrity_hash()

        # Comprimir payload si es grande
        if len(json.dumps(message.payload).encode()) > 1024:  # > 1KB
            compressed_payload = gzip.compress(
                json.dumps(message.payload).encode()
            )
            message.payload = {'compressed_data': compressed_payload.hex()}
            message.compressed = True

            # Actualizar hash después de compresión
            message.integrity_hash = message.calculate_integrity_hash()

    async def _process_received_message(self, message: P2PMessage):
        """Procesar mensaje recibido (descompresión, validación)."""
        # Validar integridad si el mensaje tiene hash
        if message.integrity_hash and not message.validate_integrity():
            self.stats['integrity_failures'] += 1
            logger.warning(f"⚠️ Hash de integridad inválido para mensaje {message.message_id}")
            return

        # Descomprimir si es necesario
        if message.compressed and 'compressed_data' in message.payload:
            try:
                compressed_data = bytes.fromhex(message.payload['compressed_data'])
                decompressed_data = gzip.decompress(compressed_data)
                message.payload = json.loads(decompressed_data.decode())
                message.compressed = False
            except Exception as e:
                logger.error(f"❌ Error descomprimiendo mensaje {message.message_id}: {e}")
                return

        # Ejecutar handlers registrados
        handlers = self.message_handlers.get(message.message_type, [])
        for handler in handlers:
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"❌ Error en handler para {message.message_type.value}: {e}")

    async def _receive_loop(self):
        """Loop principal de recepción de mensajes."""
        while self.is_running:
            try:
                if LIBP2P_AVAILABLE and self.libp2p_host:
                    await self._receive_from_libp2p()
                else:
                    await self._receive_from_fallback()

                await asyncio.sleep(0.1)  # Pequeña pausa para evitar uso excesivo de CPU

            except Exception as e:
                logger.error(f"❌ Error en loop de recepción: {e}")
                await asyncio.sleep(1.0)

    async def _setup_libp2p_protocol(self):
        """Configurar protocolo libp2p."""
        if not LIBP2P_AVAILABLE:
            return

        try:
            # Configurar stream handler para el protocolo
            async def stream_handler(stream):
                await self._handle_libp2p_stream(stream)

            self.libp2p_host.set_stream_handler(self.protocol_id, stream_handler)
            logger.info("✅ Protocolo libp2p configurado")

        except Exception as e:
            logger.error(f"❌ Error configurando protocolo libp2p: {e}")

    async def _send_via_libp2p(self, message: P2PMessage) -> bool:
        """Enviar mensaje vía libp2p."""
        if not LIBP2P_AVAILABLE or not self.libp2p_host:
            return False

        try:
            # Serializar mensaje
            message_data = json.dumps(message.to_dict()).encode()

            # Para broadcast o peer específico
            if message.recipient_id:
                # Enviar a peer específico
                peer_id = message.recipient_id
                stream = await self.libp2p_host.new_stream(peer_id, [self.protocol_id])
                await stream.write(message_data)
                await stream.close()
            else:
                # Broadcast vía pubsub (simulado)
                # En implementación real, usar pubsub de libp2p
                logger.debug("📢 Broadcast vía libp2p pubsub (simulado)")

            return True

        except Exception as e:
            logger.error(f"❌ Error enviando vía libp2p: {e}")
            return False

    async def _send_via_fallback(self, message: P2PMessage) -> bool:
        """Enviar mensaje vía mecanismo de fallback."""
        # Implementación simplificada para desarrollo
        # En producción, implementar mecanismo alternativo
        logger.debug(f"📤 Enviando mensaje {message.message_id} vía fallback")
        return True

    async def _receive_from_libp2p(self):
        """Recibir mensajes desde libp2p."""
        # Implementación simplificada
        # En producción, manejar streams entrantes
        pass

    async def _receive_from_fallback(self):
        """Recibir mensajes desde mecanismo de fallback."""
        # Implementación simplificada para desarrollo
        pass

    async def _handle_libp2p_stream(self, stream):
        """Manejar stream libp2p entrante."""
        try:
            data = await stream.read()
            message_data = json.loads(data.decode())
            message = P2PMessage.from_dict(message_data)

            # Añadir al buffer si hay espacio
            if self.message_buffer.qsize() < self.message_buffer.maxsize:
                await self.message_buffer.put(message)
            else:
                logger.warning("⚠️ Buffer de mensajes lleno, descartando mensaje")

        except Exception as e:
            logger.error(f"❌ Error manejando stream libp2p: {e}")
        finally:
            await stream.close()

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del manejador."""
        return {
            **self.stats,
            'buffer_size': self.message_buffer.qsize(),
            'buffer_max_size': self.message_buffer.maxsize,
            'is_running': self.is_running,
            'libp2p_available': LIBP2P_AVAILABLE
        }


# Funciones de conveniencia
def create_p2p_message_handler(node_id: str, libp2p_host: Optional[Any] = None) -> P2PMessageHandler:
    """Crear instancia del manejador de mensajería P2P."""
    return P2PMessageHandler(node_id, libp2p_host)