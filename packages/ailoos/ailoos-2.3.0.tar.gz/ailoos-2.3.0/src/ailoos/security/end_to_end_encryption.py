#!/usr/bin/env python3
"""
End-to-End Encryption System for Ailoos
Implementa encriptación de extremo a extremo con perfect forward secrecy
"""

import asyncio
import logging
import os
import hashlib
import hmac
import json
import time
import secrets
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from cryptography.hazmat.primitives import hashes, hmac as crypto_hmac
from cryptography.hazmat.primitives.asymmetric import x25519, rsa, padding
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EncryptionAlgorithm(Enum):
    """Algoritmos de encriptación disponibles"""
    AES_256_GCM = "aes_256_gcm"
    CHACHA20_POLY1305 = "chacha20_poly1305"
    AES_256_CBC = "aes_256_cbc"

class KeyExchangeProtocol(Enum):
    """Protocolos de intercambio de claves"""
    X25519 = "x25519"              # ECDH con Curve25519
    RSA_OAEP = "rsa_oaep"          # RSA con OAEP padding
    HYBRID = "hybrid"              # Combinación de ambos

@dataclass
class EncryptionKey:
    """Clave de encriptación con metadata"""
    key_id: str
    algorithm: EncryptionAlgorithm
    key_data: bytes
    created_at: datetime
    expires_at: Optional[datetime] = None
    usage_count: int = 0
    max_uses: Optional[int] = None

@dataclass
class SessionKey:
    """Clave de sesión para comunicación E2E"""
    session_id: str
    sender_key: EncryptionKey
    receiver_key: EncryptionKey
    shared_secret: bytes
    established_at: datetime
    last_used: datetime = field(default_factory=datetime.now)
    message_count: int = 0

@dataclass
class EncryptedMessage:
    """Mensaje encriptado"""
    message_id: str
    sender_id: str
    recipient_id: str
    encrypted_data: bytes
    nonce: bytes
    auth_tag: Optional[bytes] = None
    key_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

class X25519KeyExchange:
    """
    Implementación de intercambio de claves ECDH con Curve25519
    """

    def __init__(self):
        self.private_key = x25519.X25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        self.public_key_bytes = self.public_key.public_bytes_raw()

    def get_public_key(self) -> bytes:
        """Obtener clave pública para compartir"""
        return self.public_key_bytes

    def derive_shared_secret(self, peer_public_key: bytes) -> bytes:
        """Derivar secreto compartido con clave pública del peer"""
        peer_key = x25519.X25519PublicKey.from_public_bytes(peer_public_key)
        shared_secret = self.private_key.exchange(peer_key)

        # Usar HKDF para derivar clave final
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"X25519-E2E-Shared-Secret",
            backend=default_backend()
        )

        return hkdf.derive(shared_secret)

class AESGCMEncryption:
    """
    Encriptación AES-256-GCM
    """

    @staticmethod
    def encrypt(plaintext: bytes, key: bytes, associated_data: bytes = b"") -> Tuple[bytes, bytes, bytes]:
        """
        Encriptar datos con AES-GCM

        Args:
            plaintext: Datos a encriptar
            key: Clave de 32 bytes
            associated_data: Datos asociados (no encriptados pero autenticados)

        Returns:
            Tupla de (ciphertext, nonce, auth_tag)
        """
        nonce = os.urandom(12)  # 96 bits para GCM

        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
        encryptor = cipher.encryptor()

        encryptor.authenticate_additional_data(associated_data)
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()

        return ciphertext, nonce, encryptor.tag

    @staticmethod
    def decrypt(ciphertext: bytes, key: bytes, nonce: bytes, auth_tag: bytes,
                associated_data: bytes = b"") -> bytes:
        """
        Desencriptar datos con AES-GCM

        Args:
            ciphertext: Datos encriptados
            key: Clave de 32 bytes
            nonce: Nonce usado en encriptación
            auth_tag: Tag de autenticación
            associated_data: Datos asociados

        Returns:
            Datos desencriptados
        """
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, auth_tag), backend=default_backend())
        decryptor = cipher.decryptor()

        decryptor.authenticate_additional_data(associated_data)
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        return plaintext

class ChaCha20Poly1305Encryption:
    """
    Encriptación ChaCha20-Poly1305
    """

    @staticmethod
    def encrypt(plaintext: bytes, key: bytes, associated_data: bytes = b"") -> Tuple[bytes, bytes, bytes]:
        """
        Encriptar datos con ChaCha20-Poly1305
        """
        nonce = os.urandom(12)  # 96 bits

        cipher = Cipher(algorithms.ChaCha20(key, nonce), modes.ChaCha20Poly1305(), backend=default_backend())
        encryptor = cipher.encryptor()

        encryptor.authenticate_additional_data(associated_data)
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()

        return ciphertext, nonce, encryptor.tag

    @staticmethod
    def decrypt(ciphertext: bytes, key: bytes, nonce: bytes, auth_tag: bytes,
                associated_data: bytes = b"") -> bytes:
        """
        Desencriptar datos con ChaCha20-Poly1305
        """
        cipher = Cipher(algorithms.ChaCha20(key, nonce), modes.ChaCha20Poly1305(auth_tag), backend=default_backend())
        decryptor = cipher.decryptor()

        decryptor.authenticate_additional_data(associated_data)
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        return plaintext

class EndToEndEncryptionManager:
    """
    Gestor de encriptación de extremo a extremo con perfect forward secrecy
    """

    def __init__(self, node_id: str, key_exchange: KeyExchangeProtocol = KeyExchangeProtocol.X25519,
                 encryption: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM):
        self.node_id = node_id
        self.key_exchange_protocol = key_exchange
        self.encryption_algorithm = encryption

        # Key management
        self.key_exchange_instances: Dict[str, Any] = {}  # peer_id -> key exchange instance
        self.session_keys: Dict[str, SessionKey] = {}     # session_id -> session key
        self.encryption_keys: Dict[str, EncryptionKey] = {}  # key_id -> encryption key

        # Message handling
        self.pending_messages: Dict[str, EncryptedMessage] = {}
        self.message_history: List[EncryptedMessage] = []

        # Security parameters
        self.key_rotation_interval = timedelta(hours=24)  # Rotate keys every 24 hours
        self.max_session_messages = 1000  # Rotate session after 1000 messages
        self.key_size = 32  # 256 bits

        # Initialize key exchange
        self._initialize_key_exchange()

        logger.info(f"🔐 E2E Encryption initialized for node {node_id}")

    def _initialize_key_exchange(self):
        """Initialize key exchange protocol"""
        if self.key_exchange_protocol == KeyExchangeProtocol.X25519:
            self.key_exchange_instances[self.node_id] = X25519KeyExchange()
        elif self.key_exchange_protocol == KeyExchangeProtocol.RSA_OAEP:
            # RSA would be implemented here
            pass
        elif self.key_exchange_protocol == KeyExchangeProtocol.HYBRID:
            # Hybrid approach would be implemented here
            pass

    async def establish_session(self, peer_id: str, peer_public_key: bytes) -> Optional[str]:
        """
        Establecer sesión encriptada con un peer

        Args:
            peer_id: ID del peer
            peer_public_key: Clave pública del peer

        Returns:
            ID de sesión o None si falla
        """
        try:
            # Get our key exchange instance
            our_key_exchange = self.key_exchange_instances.get(self.node_id)
            if not our_key_exchange:
                return None

            # Derive shared secret
            shared_secret = our_key_exchange.derive_shared_secret(peer_public_key)

            # Create session keys
            session_id = f"session_{self.node_id}_{peer_id}_{int(time.time())}"

            # Create encryption keys for this session
            sender_key = EncryptionKey(
                key_id=f"sender_{session_id}",
                algorithm=self.encryption_algorithm,
                key_data=shared_secret[:self.key_size],
                created_at=datetime.now()
            )

            receiver_key = EncryptionKey(
                key_id=f"receiver_{session_id}",
                algorithm=self.encryption_algorithm,
                key_data=shared_secret[self.key_size:2*self.key_size],
                created_at=datetime.now()
            )

            # Create session
            session = SessionKey(
                session_id=session_id,
                sender_key=sender_key,
                receiver_key=receiver_key,
                shared_secret=shared_secret,
                established_at=datetime.now()
            )

            self.session_keys[session_id] = session
            self.encryption_keys[sender_key.key_id] = sender_key
            self.encryption_keys[receiver_key.key_id] = receiver_key

            logger.info(f"🔗 E2E session established: {session_id}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to establish session with {peer_id}: {e}")
            return None

    async def encrypt_message(self, message: Any, recipient_id: str,
                            session_id: Optional[str] = None) -> Optional[EncryptedMessage]:
        """
        Encriptar mensaje para envío

        Args:
            message: Mensaje a encriptar
            recipient_id: ID del destinatario
            session_id: ID de sesión (opcional, usa la más reciente si no se especifica)

        Returns:
            Mensaje encriptado o None si falla
        """
        try:
            # Get or find session
            if not session_id:
                session_id = self._find_active_session(recipient_id)

            if not session_id or session_id not in self.session_keys:
                logger.warning(f"No active session found for {recipient_id}")
                return None

            session = self.session_keys[session_id]

            # Check if session needs rotation
            if self._should_rotate_session(session):
                await self._rotate_session(session_id)

            # Serialize message
            if isinstance(message, (dict, list)):
                plaintext = json.dumps(message, ensure_ascii=False).encode('utf-8')
            elif isinstance(message, str):
                plaintext = message.encode('utf-8')
            else:
                plaintext = str(message).encode('utf-8')

            # Get encryption key
            encryption_key = session.sender_key

            # Associated data for authentication
            associated_data = f"{self.node_id}:{recipient_id}:{datetime.now().isoformat()}".encode()

            # Encrypt
            if self.encryption_algorithm == EncryptionAlgorithm.AES_256_GCM:
                ciphertext, nonce, auth_tag = AESGCMEncryption.encrypt(
                    plaintext, encryption_key.key_data, associated_data
                )
            elif self.encryption_algorithm == EncryptionAlgorithm.CHACHA20_POLY1305:
                ciphertext, nonce, auth_tag = ChaCha20Poly1305Encryption.encrypt(
                    plaintext, encryption_key.key_data, associated_data
                )
            else:
                raise ValueError(f"Unsupported encryption algorithm: {self.encryption_algorithm}")

            # Create encrypted message
            encrypted_msg = EncryptedMessage(
                message_id=f"msg_{secrets.token_hex(8)}",
                sender_id=self.node_id,
                recipient_id=recipient_id,
                encrypted_data=ciphertext,
                nonce=nonce,
                auth_tag=auth_tag,
                key_id=encryption_key.key_id,
                metadata={
                    'session_id': session_id,
                    'algorithm': self.encryption_algorithm.value,
                    'compressed': False  # Could add compression
                }
            )

            # Update session stats
            session.message_count += 1
            session.last_used = datetime.now()
            encryption_key.usage_count += 1

            # Store in history
            self.message_history.append(encrypted_msg)

            return encrypted_msg

        except Exception as e:
            logger.error(f"Failed to encrypt message for {recipient_id}: {e}")
            return None

    async def decrypt_message(self, encrypted_msg: EncryptedMessage) -> Optional[Any]:
        """
        Desencriptar mensaje recibido

        Args:
            encrypted_msg: Mensaje encriptado

        Returns:
            Mensaje desencriptado o None si falla
        """
        try:
            # Get encryption key
            encryption_key = self.encryption_keys.get(encrypted_msg.key_id)
            if not encryption_key:
                logger.warning(f"Unknown encryption key: {encrypted_msg.key_id}")
                return None

            # Get associated data
            associated_data = f"{encrypted_msg.sender_id}:{encrypted_msg.recipient_id}:{encrypted_msg.timestamp.isoformat()}".encode()

            # Decrypt
            if encryption_key.algorithm == EncryptionAlgorithm.AES_256_GCM:
                plaintext = AESGCMEncryption.decrypt(
                    encrypted_msg.encrypted_data,
                    encryption_key.key_data,
                    encrypted_msg.nonce,
                    encrypted_msg.auth_tag,
                    associated_data
                )
            elif encryption_key.algorithm == EncryptionAlgorithm.CHACHA20_POLY1305:
                plaintext = ChaCha20Poly1305Encryption.decrypt(
                    encrypted_msg.encrypted_data,
                    encryption_key.key_data,
                    encrypted_msg.nonce,
                    encrypted_msg.auth_tag,
                    associated_data
                )
            else:
                raise ValueError(f"Unsupported encryption algorithm: {encryption_key.algorithm}")

            # Parse message
            try:
                message = json.loads(plaintext.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                message = plaintext.decode('utf-8')

            # Update key usage
            encryption_key.usage_count += 1

            return message

        except Exception as e:
            logger.error(f"Failed to decrypt message {encrypted_msg.message_id}: {e}")
            return None

    def _find_active_session(self, peer_id: str) -> Optional[str]:
        """Find active session for peer"""
        # Find most recent session for this peer
        peer_sessions = [
            session_id for session_id, session in self.session_keys.items()
            if peer_id in session_id and session.message_count < self.max_session_messages
        ]

        if peer_sessions:
            # Return most recently used
            return max(peer_sessions, key=lambda s: self.session_keys[s].last_used)

        return None

    def _should_rotate_session(self, session: SessionKey) -> bool:
        """Check if session should be rotated"""
        time_since_established = datetime.now() - session.established_at
        return (time_since_established > self.key_rotation_interval or
                session.message_count >= self.max_session_messages)

    async def _rotate_session(self, session_id: str):
        """Rotate session keys for perfect forward secrecy"""
        if session_id not in self.session_keys:
            return

        old_session = self.session_keys[session_id]

        # Generate new keys (simplified - in practice would do new key exchange)
        new_shared_secret = secrets.token_bytes(64)

        new_sender_key = EncryptionKey(
            key_id=f"sender_{session_id}_rotated_{int(time.time())}",
            algorithm=self.encryption_algorithm,
            key_data=new_shared_secret[:self.key_size],
            created_at=datetime.now()
        )

        new_receiver_key = EncryptionKey(
            key_id=f"receiver_{session_id}_rotated_{int(time.time())}",
            algorithm=self.encryption_algorithm,
            key_data=new_shared_secret[self.key_size:2*self.key_size],
            created_at=datetime.now()
        )

        # Update session
        old_session.sender_key = new_sender_key
        old_session.receiver_key = new_receiver_key
        old_session.shared_secret = new_shared_secret
        old_session.message_count = 0

        # Store new keys
        self.encryption_keys[new_sender_key.key_id] = new_sender_key
        self.encryption_keys[new_receiver_key.key_id] = new_receiver_key

        logger.info(f"🔄 Session rotated: {session_id}")

    def get_public_key(self) -> bytes:
        """Get public key for key exchange"""
        key_exchange = self.key_exchange_instances.get(self.node_id)
        if key_exchange:
            return key_exchange.get_public_key()
        return b""

    def get_encryption_status(self) -> Dict[str, Any]:
        """Get encryption system status"""
        return {
            'node_id': self.node_id,
            'key_exchange_protocol': self.key_exchange_protocol.value,
            'encryption_algorithm': self.encryption_algorithm.value,
            'active_sessions': len(self.session_keys),
            'total_keys': len(self.encryption_keys),
            'messages_processed': len(self.message_history),
            'pending_messages': len(self.pending_messages)
        }

    async def cleanup_expired_keys(self):
        """Clean up expired or overused keys"""
        current_time = datetime.now()
        expired_keys = []

        for key_id, key in self.encryption_keys.items():
            if key.expires_at and current_time > key.expires_at:
                expired_keys.append(key_id)
            elif key.max_uses and key.usage_count >= key.max_uses:
                expired_keys.append(key_id)

        for key_id in expired_keys:
            del self.encryption_keys[key_id]

        if expired_keys:
            logger.info(f"🧹 Cleaned up {len(expired_keys)} expired keys")

# Global E2E encryption manager instance
e2e_manager_instance = None

def get_e2e_encryption_manager(node_id: str, **kwargs) -> EndToEndEncryptionManager:
    """Get global E2E encryption manager instance"""
    global e2e_manager_instance
    if e2e_manager_instance is None:
        e2e_manager_instance = EndToEndEncryptionManager(node_id, **kwargs)
    return e2e_manager_instance

if __name__ == '__main__':
    # Demo
    async def main():
        # Initialize two nodes
        alice = get_e2e_encryption_manager("alice")
        bob = get_e2e_encryption_manager("bob")

        print("🔐 End-to-End Encryption Demo")
        print("=" * 50)

        # Exchange public keys
        alice_public_key = alice.get_public_key()
        bob_public_key = bob.get_public_key()

        print("🔑 Public keys exchanged")

        # Establish sessions
        alice_session = await alice.establish_session("bob", bob_public_key)
        bob_session = await bob.establish_session("alice", alice_public_key)

        if alice_session and bob_session:
            print("🔗 E2E sessions established")

            # Alice encrypts a message
            message = {"text": "Hello Bob! This is a secret message.", "timestamp": datetime.now().isoformat()}
            encrypted_msg = await alice.encrypt_message(message, "bob", alice_session)

            if encrypted_msg:
                print("📤 Message encrypted by Alice")

                # Bob decrypts the message
                decrypted_msg = await bob.decrypt_message(encrypted_msg)

                if decrypted_msg:
                    print("📥 Message decrypted by Bob")
                    print(f"💬 Message content: {decrypted_msg}")

                    # Verify integrity
                    if decrypted_msg == message:
                        print("✅ Message integrity verified")
                    else:
                        print("❌ Message integrity check failed")
                else:
                    print("❌ Failed to decrypt message")
            else:
                print("❌ Failed to encrypt message")
        else:
            print("❌ Failed to establish sessions")

        # Show status
        alice_status = alice.get_encryption_status()
        print(f"📊 Alice encryption status: {alice_status['active_sessions']} sessions, {alice_status['messages_processed']} messages")

        print("🎉 End-to-End Encryption Demo completed!")

    asyncio.run(main())