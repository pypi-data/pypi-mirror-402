import os
import time
import logging
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


class P2PEncryption:
    """
    Clase para encriptación end-to-end P2P usando AES-256-GCM.
    Las claves se derivan del wallet DracmaS usando HKDF.
    Rotación de claves cada sesión (~1 hora).
    Integración preparada para TLS 1.3 (no implementada aún).
    """

    def __init__(self, master_key: bytes):
        """
        Inicializa la encriptación con la clave maestra del wallet DracmaS.
        :param master_key: Clave maestra derivada del wallet (bytes de 32+).
        """
        if len(master_key) < 32:
            raise ValueError("Master key must be at least 32 bytes")
        self.master_key = master_key
        self.logger = logging.getLogger(__name__)
        self.session_duration = 3600  # 1 hora en segundos

    def _derive_session_key(self, session_id: str) -> bytes:
        """
        Deriva una clave de sesión usando HKDF desde la clave maestra.
        :param session_id: Identificador único de la sesión.
        :return: Clave de sesión de 32 bytes.
        """
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,  # AES-256
            salt=session_id.encode('utf-8'),
            info=b'p2p_session_key_derivation',
            backend=default_backend()
        )
        return hkdf.derive(self.master_key)

    def _get_current_session_id(self) -> str:
        """
        Genera un ID de sesión basado en el tiempo actual, rotando cada hora.
        :return: ID de sesión como string.
        """
        current_time = int(time.time())
        session_start = (current_time // self.session_duration) * self.session_duration
        return str(session_start)

    def encrypt_payload(self, payload: bytes) -> bytes:
        """
        Encripta un payload usando AES-256-GCM con clave de sesión actual.
        Incluye nonce y tag para integridad (MAC).
        :param payload: Datos a encriptar.
        :return: Payload encriptado (nonce + tag + ciphertext).
        """
        try:
            session_id = self._get_current_session_id()
            key = self._derive_session_key(session_id)
            nonce = os.urandom(12)  # 96 bits para GCM
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(payload) + encryptor.finalize()
            # Retornar: nonce (12) + tag (16) + ciphertext
            encrypted_data = nonce + encryptor.tag + ciphertext
            self.logger.info(f"Payload encrypted successfully for session {session_id}")
            return encrypted_data
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise RuntimeError("Failed to encrypt payload") from e

    def decrypt_payload(self, encrypted_payload: bytes) -> bytes:
        """
        Desencripta un payload usando AES-256-GCM con clave de sesión actual.
        Valida integridad usando el tag (MAC).
        :param encrypted_payload: Datos encriptados (nonce + tag + ciphertext).
        :return: Payload desencriptado.
        :raises ValueError: Si el payload es inválido o la desencriptación falla.
        """
        try:
            if len(encrypted_payload) < 28:  # nonce (12) + tag (16) mínimo
                raise ValueError("Encrypted payload too short")
            nonce = encrypted_payload[:12]
            tag = encrypted_payload[12:28]
            ciphertext = encrypted_payload[28:]
            session_id = self._get_current_session_id()
            key = self._derive_session_key(session_id)
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            self.logger.info(f"Payload decrypted successfully for session {session_id}")
            return plaintext
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise ValueError("Decryption failed - invalid data or key mismatch") from e

    # Placeholder para integración futura con TLS 1.3
    def prepare_for_tls_integration(self):
        """
        Método placeholder para futura integración con TLS 1.3.
        Actualmente no implementado.
        """
        self.logger.info("TLS 1.3 integration not yet implemented")
        pass