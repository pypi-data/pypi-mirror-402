import asyncio
import logging
from typing import Optional, List, Dict, Any, Callable
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from waku import WakuNode, WakuMessage, WakuPeer

logger = logging.getLogger(__name__)

class StatusClient:
    def __init__(self, node_key: Optional[str] = None, bootstrap_nodes: Optional[List[str]] = None):
        self.node_key = node_key or self._generate_node_key()
        self.bootstrap_nodes = bootstrap_nodes or [
            "/ip4/127.0.0.1/tcp/60000/p2p/16Uiu2HAmPLe7Mzm8TsYUubgCAW1aJoeFScxrLj8ppHFivPo97bUZ"
        ]  # Ejemplo de bootstrap para Status
        self.node: Optional[WakuNode] = None
        self.private_key: rsa.RSAPrivateKey = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
        self._message_callbacks: Dict[str, List[Callable]] = {}
        self._channels: List[str] = []

    def _generate_node_key(self) -> str:
        """Generar clave de nodo aleatoria."""
        import secrets
        return secrets.token_hex(32)

    async def connect(self) -> bool:
        """Conectar a la red Status (Waku)."""
        try:
            self.node = WakuNode(node_key=self.node_key)
            await self.node.start()
            for bootstrap in self.bootstrap_nodes:
                await self.node.connect_to_peer(bootstrap)
            logger.info("Conectado a la red Status")
            # Iniciar listener para mensajes
            asyncio.create_task(self._listen_for_messages())
            return True
        except Exception as e:
            logger.error(f"Error conectando a Status: {e}")
            return False

    async def disconnect(self):
        """Desconectar de la red Status."""
        if self.node:
            await self.node.stop()
            logger.info("Desconectado de Status")

    async def _listen_for_messages(self):
        """Escuchar mensajes entrantes."""
        try:
            while self.node:
                messages = await self.node.receive_messages()
                for msg in messages:
                    channel = msg.topic
                    if channel in self._message_callbacks:
                        decrypted_msg = self._decrypt_message(msg.payload)
                        if decrypted_msg:
                            for callback in self._message_callbacks[channel]:
                                await callback(channel, msg.sender, decrypted_msg)
        except Exception as e:
            logger.error(f"Error escuchando mensajes: {e}")

    def add_message_callback(self, channel: str, callback: Callable):
        """Agregar callback para mensajes en un canal."""
        if channel not in self._message_callbacks:
            self._message_callbacks[channel] = []
        self._message_callbacks[channel].append(callback)

    async def send_message(self, channel: str, message: str, recipient_public_key: Optional[bytes] = None) -> bool:
        """Enviar mensaje a un canal, opcionalmente encriptado para un destinatario."""
        try:
            payload = message.encode()
            if recipient_public_key:
                payload = self._encrypt_message(payload, recipient_public_key)
            waku_msg = WakuMessage(topic=channel, payload=payload)
            await self.node.publish(waku_msg)
            logger.info(f"Mensaje enviado a canal {channel}")
            return True
        except Exception as e:
            logger.error(f"Error enviando mensaje: {e}")
            return False

    async def join_channel(self, channel: str) -> bool:
        """Unirse a un canal (topic)."""
        try:
            await self.node.subscribe(channel)
            self._channels.append(channel)
            logger.info(f"Unido a canal {channel}")
            return True
        except Exception as e:
            logger.error(f"Error uniendo a canal: {e}")
            return False

    async def leave_channel(self, channel: str) -> bool:
        """Salir de un canal."""
        try:
            await self.node.unsubscribe(channel)
            if channel in self._channels:
                self._channels.remove(channel)
            logger.info(f"Salido de canal {channel}")
            return True
        except Exception as e:
            logger.error(f"Error saliendo de canal: {e}")
            return False

    def list_channels(self) -> List[str]:
        """Listar canales unidos."""
        return self._channels.copy()

    def get_public_key_bytes(self) -> bytes:
        """Obtener clave pública para compartir."""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def _encrypt_message(self, message: bytes, recipient_public_key_bytes: bytes) -> bytes:
        """Encriptar mensaje para E2E."""
        try:
            recipient_public_key = serialization.load_pem_public_key(recipient_public_key_bytes)
            encrypted = recipient_public_key.encrypt(
                message,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return encrypted
        except Exception as e:
            logger.error(f"Error encriptando mensaje: {e}")
            return message

    def _decrypt_message(self, encrypted_message: bytes) -> Optional[str]:
        """Desencriptar mensaje E2E."""
        try:
            decrypted = self.private_key.decrypt(
                encrypted_message,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Error desencriptando mensaje: {e}")
            return None

    async def create_private_channel(self, with_user: str) -> str:
        """Crear canal privado con un usuario (basado en hash de claves)."""
        # Simplificado: crear topic basado en claves públicas
        channel = f"private_{hash(with_user + self.get_public_key_bytes().decode())}"
        await self.join_channel(channel)
        return channel