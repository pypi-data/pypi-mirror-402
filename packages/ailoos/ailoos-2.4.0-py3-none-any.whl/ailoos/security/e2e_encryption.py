#!/usr/bin/env python3
"""
Encriptación End-to-End para Ailoos
Implementa AES-256, ECDH para intercambio de claves, y validación de integridad.
"""

import os
import logging
import secrets
from typing import Optional, Tuple
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag

logger = logging.getLogger(__name__)

class E2EEncryptionManager:
    """
    Gestor de encriptación end-to-end con AES-256 y ECDH.
    """

    def __init__(self):
        self.private_key = x25519.X25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        self.public_key_bytes = self.public_key.public_bytes_raw()
        logger.info("E2EEncryptionManager inicializado con clave ECDH.")

    def get_public_key(self) -> bytes:
        """
        Obtener clave pública para intercambio.
        """
        return self.public_key_bytes

    def secure_key_exchange(self, peer_public_key: bytes) -> bytes:
        """
        Realizar intercambio seguro de claves usando ECDH.

        Args:
            peer_public_key: Clave pública del peer.

        Returns:
            Secreto compartido derivado.
        """
        try:
            peer_key = x25519.X25519PublicKey.from_public_bytes(peer_public_key)
            shared_secret = self.private_key.exchange(peer_key)

            # Derivar clave usando HKDF
            hkdf = HKDF(
                algorithm=hashes.SHA256(),
                length=32,  # 256 bits para AES-256
                salt=None,
                info=b"E2E-Shared-Secret",
                backend=default_backend()
            )
            derived_key = hkdf.derive(shared_secret)
            logger.info("Intercambio de claves ECDH completado.")
            return derived_key
        except Exception as e:
            logger.error(f"Error en secure_key_exchange: {e}")
            raise

    def encrypt_data(self, data: bytes, key: bytes) -> Tuple[bytes, bytes, bytes]:
        """
        Encriptar datos usando AES-256-GCM.

        Args:
            data: Datos a encriptar.
            key: Clave de 32 bytes.

        Returns:
            Tupla (ciphertext, nonce, auth_tag).
        """
        try:
            nonce = os.urandom(12)  # 96 bits para GCM
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(data) + encryptor.finalize()
            auth_tag = encryptor.tag
            logger.debug("Datos encriptados con AES-256-GCM.")
            return ciphertext, nonce, auth_tag
        except Exception as e:
            logger.error(f"Error en encrypt_data: {e}")
            raise

    def decrypt_data(self, ciphertext: bytes, key: bytes, nonce: bytes, auth_tag: bytes) -> bytes:
        """
        Desencriptar datos usando AES-256-GCM y validar integridad.

        Args:
            ciphertext: Datos encriptados.
            key: Clave de 32 bytes.
            nonce: Nonce usado en encriptación.
            auth_tag: Tag de autenticación.

        Returns:
            Datos desencriptados.

        Raises:
            InvalidTag: Si la integridad falla.
        """
        try:
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, auth_tag), backend=default_backend())
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            logger.debug("Datos desencriptados y integridad validada.")
            return plaintext
        except InvalidTag:
            logger.error("Validación de integridad fallida: tag inválido.")
            raise
        except Exception as e:
            logger.error(f"Error en decrypt_data: {e}")
            raise

# Nota: TLS 1.3 se asume implementado en la capa de comunicaciones superior.
# Esta implementación se enfoca en la encriptación E2E de datos sensibles.