import asyncio
import logging
from typing import Optional, List, Dict, Any, Callable
from waku import WakuNode, WakuMessage, WakuPeer
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization

logger = logging.getLogger(__name__)

class WakuClient:
    def __init__(self, node_key: Optional[str] = None, bootstrap_nodes: Optional[List[str]] = None):
        self.node_key = node_key or self._generate_node_key()
        self.bootstrap_nodes = bootstrap_nodes or [
            "/ip4/127.0.0.1/tcp/60000/p2p/16Uiu2HAmPLe7Mzm8TsYUubgCAW1aJoeFScxrLj8ppHFivPo97bUZ"
        ]
        self.node: Optional[WakuNode] = None
        self.private_key: rsa.RSAPrivateKey = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
        self._message_callbacks: Dict[str, List[Callable]] = {}
        self._topics: List[str] = []

    def _generate_node_key(self) -> str:
        """Generar clave de nodo aleatoria."""
        import secrets
        return secrets.token_hex(32)

    async def connect(self) -> bool:
        """Conectar a la red Waku."""
        try:
            self.node = WakuNode(node_key=self.node_key)
            await self.node.start()
            for bootstrap in self.bootstrap_nodes:
                await self.node.connect_to_peer(bootstrap)
            logger.info("Conectado a la red Waku")
            # Iniciar listener
            asyncio.create_task(self._listen_for_messages())
            return True
        except Exception as e:
            logger.error(f"Error conectando a Waku: {e}")
            return False

    async def disconnect(self):
        """Desconectar de la red Waku."""
        if self.node:
            await self.node.stop()
            logger.info("Desconectado de Waku")

    async def _listen_for_messages(self):
        """Escuchar mensajes entrantes."""
        try:
            while self.node:
                messages = await self.node.receive_messages()
                for msg in messages:
                    topic = msg.topic
                    if topic in self._message_callbacks:
                        decrypted_msg = self._decrypt_message(msg.payload) if msg.payload.startswith(b'encrypted:') else msg.payload.decode()
                        if decrypted_msg:
                            for callback in self._message_callbacks[topic]:
                                await callback(topic, msg.sender, decrypted_msg)
        except Exception as e:
            logger.error(f"Error escuchando mensajes: {e}")

    def add_message_callback(self, topic: str, callback: Callable):
        """Agregar callback para mensajes en un topic."""
        if topic not in self._message_callbacks:
            self._message_callbacks[topic] = []
        self._message_callbacks[topic].append(callback)

    async def send_message(self, topic: str, message: str, encrypt: bool = False, recipient_public_key: Optional[bytes] = None) -> bool:
        """Enviar mensaje a un topic, opcionalmente encriptado."""
        try:
            payload = message.encode()
            if encrypt and recipient_public_key:
                payload = b'encrypted:' + self._encrypt_message(payload, recipient_public_key)
            waku_msg = WakuMessage(topic=topic, payload=payload)
            await self.node.publish(waku_msg)
            logger.info(f"Mensaje enviado a topic {topic}")
            return True
        except Exception as e:
            logger.error(f"Error enviando mensaje: {e}")
            return False

    async def subscribe_topic(self, topic: str) -> bool:
        """Suscribirse a un topic."""
        try:
            await self.node.subscribe(topic)
            self._topics.append(topic)
            logger.info(f"Suscrito a topic {topic}")
            return True
        except Exception as e:
            logger.error(f"Error suscribiendo a topic: {e}")
            return False

    async def unsubscribe_topic(self, topic: str) -> bool:
        """Desuscribirse de un topic."""
        try:
            await self.node.unsubscribe(topic)
            if topic in self._topics:
                self._topics.remove(topic)
            logger.info(f"Desuscrito de topic {topic}")
            return True
        except Exception as e:
            logger.error(f"Error desuscribiendo de topic: {e}")
            return False

    def list_topics(self) -> List[str]:
        """Listar topics suscritos."""
        return self._topics.copy()

    def get_public_key_bytes(self) -> bytes:
        """Obtener clave pública."""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def _encrypt_message(self, message: bytes, recipient_public_key_bytes: bytes) -> bytes:
        """Encriptar mensaje E2E."""
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

    def _decrypt_message(self, encrypted_payload: bytes) -> Optional[str]:
        """Desencriptar mensaje E2E."""
        try:
            if encrypted_payload.startswith(b'encrypted:'):
                encrypted_message = encrypted_payload[10:]  # Remover 'encrypted:'
                decrypted = self.private_key.decrypt(
                    encrypted_message,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                return decrypted.decode()
            return encrypted_payload.decode()
        except Exception as e:
            logger.error(f"Error desencriptando mensaje: {e}")
            return None

    async def create_topic(self, topic_name: str) -> bool:
        """Crear un nuevo topic (simplemente suscribirse)."""
        return await self.subscribe_topic(topic_name)

    async def get_peers(self) -> List[str]:
        """Obtener lista de peers conectados."""
        if self.node:
            peers = await self.node.get_peers()
            return [str(peer) for peer in peers]
        return []