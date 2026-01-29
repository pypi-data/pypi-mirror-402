"""
Handshake Seguro P2P para AILOOS
Implementa autenticación y establecimiento de canal encriptado con X.509, Diffie-Hellman y RSA-PSS.
"""

import asyncio
import secrets
import time
import hashlib
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding, dh
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography import x509
from cryptography.x509.oid import NameOID
from datetime import datetime, timedelta, timezone

from ..core.logging import get_logger
from ..sdk.auth import NodeAuthenticator

logger = get_logger(__name__)


@dataclass
class EncryptedChannel:
    """Canal encriptado establecido."""
    session_key: bytes
    peer_id: str
    established_at: float
    nonce: bytes

    def encrypt(self, data: bytes) -> bytes:
        """Encriptar datos con AES-GCM."""
        iv = secrets.token_bytes(12)
        cipher = Cipher(algorithms.AES(self.session_key), modes.GCM(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        return iv + encryptor.tag + ciphertext

    def decrypt(self, data: bytes) -> bytes:
        """Desencriptar datos con AES-GCM."""
        iv, tag, ciphertext = data[:12], data[12:28], data[28:]
        cipher = Cipher(algorithms.AES(self.session_key), modes.GCM(iv, tag))
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()


class P2PHandshake:
    """
    Handshake seguro P2P con autenticación X.509 y encriptación Diffie-Hellman.

    Implementa:
    - Generación de nonce aleatorio
    - Verificación de firma digital X.509
    - Negociación de claves Diffie-Hellman
    - Establecimiento de canal encriptado
    - Integración con NodeAuthenticator para JWT/RSA-PSS
    """

    def __init__(self, node_id: str, authenticator: NodeAuthenticator):
        """
        Inicializar handshake P2P.

        Args:
            node_id: ID del nodo local
            authenticator: Instancia de NodeAuthenticator para JWT/RSA-PSS
        """
        self.node_id = node_id
        self.authenticator = authenticator

        # Claves criptográficas
        self._private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self._public_key = self._private_key.public_key()

        # Certificado X.509 auto-firmado
        self._certificate = self._generate_certificate()

        # Parámetros Diffie-Hellman
        self._dh_parameters = dh.generate_parameters(generator=2, key_size=2048)
        self._dh_private_key = self._dh_parameters.generate_private_key()

        # Estadísticas
        self.handshake_times: list = []
        self.success_count = 0
        self.failure_count = 0

        logger.info(f"🔐 P2PHandshake inicializado para nodo {node_id}")

    def _generate_certificate(self) -> x509.Certificate:
        """Generar certificado X.509 auto-firmado."""
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
            self._public_key
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
        ).sign(self._private_key, hashes.SHA256())

        return cert

    def _generate_nonce(self) -> bytes:
        """Generar nonce aleatorio de 32 bytes."""
        return secrets.token_bytes(32)

    def _sign_payload(self, payload: bytes) -> bytes:
        """Firmar payload con RSA-PSS."""
        return self._private_key.sign(
            payload,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

    def _verify_signature(self, payload: bytes, signature: bytes, peer_cert: x509.Certificate) -> bool:
        """Verificar firma con clave pública del peer."""
        try:
            peer_cert.public_key().verify(
                signature,
                payload,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception as e:
            logger.warning(f"❌ Verificación de firma fallida: {e}")
            return False

    def _validate_certificate(self, cert: x509.Certificate) -> bool:
        """Validar certificado X.509 (básico)."""
        try:
            # Verificar fechas de validez
            now = datetime.now(timezone.utc)
            if now < cert.not_valid_before_utc or now > cert.not_valid_after_utc:
                logger.warning("❌ Certificado expirado o no válido aún")
                return False

            # Verificar firma (auto-firmado por simplicidad)
            cert.public_key().verify(
                cert.signature,
                cert.tbs_certificate_bytes,
                padding.PKCS1v15(),
                cert.signature_hash_algorithm
            )
            return True
        except Exception as e:
            logger.warning(f"❌ Validación de certificado fallida: {e}")
            return False

    def _derive_session_key(self, shared_key: bytes) -> bytes:
        """Derivar clave de sesión de clave compartida DH."""
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"AILOOS P2P Session Key"
        )
        return hkdf.derive(shared_key)

    async def establish_connection(self, peer_id: str, peer_address: str) -> Optional[EncryptedChannel]:
        """
        Establecer conexión segura con peer.

        Args:
            peer_id: ID del peer
            peer_address: Dirección del peer (IP:puerto)

        Returns:
            EncryptedChannel si exitoso, None si falla
        """
        start_time = time.time()
        nonce = self._generate_nonce()

        try:
            logger.info(f"🔗 Iniciando handshake con peer {peer_id} en {peer_address}")

            # Paso 1: Preparar mensaje de handshake inicial
            handshake_payload = {
                "node_id": self.node_id,
                "peer_id": peer_id,
                "nonce": nonce.hex(),
                "certificate": self._certificate.public_bytes(serialization.Encoding.PEM).decode(),
                "dh_public_key": self._dh_private_key.public_key().public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ).decode(),
                "timestamp": time.time()
            }

            # Obtener token JWT del authenticator
            jwt_token = self.authenticator.get_token()
            if not jwt_token:
                logger.error("❌ No hay token JWT válido")
                self.failure_count += 1
                return None

            handshake_payload["jwt_token"] = jwt_token

            # Serializar y firmar
            payload_bytes = str(handshake_payload).encode()
            signature = self._sign_payload(payload_bytes)
            handshake_payload["signature"] = signature.hex()

            # Enviar mensaje de handshake (simulado - en producción usar P2PMessageHandler)
            # Aquí asumimos que enviamos y recibimos respuestas de forma síncrona para simplicidad
            peer_response = await self._send_handshake_message(peer_address, handshake_payload)

            if not peer_response:
                logger.error("❌ No se recibió respuesta del peer")
                self.failure_count += 1
                return None

            # Paso 2: Verificar respuesta del peer
            peer_cert_pem = peer_response.get("certificate")
            if not peer_cert_pem:
                logger.error("❌ Certificado del peer faltante")
                self.failure_count += 1
                return None

            peer_cert = x509.load_pem_x509_certificate(peer_cert_pem.encode())
            if not self._validate_certificate(peer_cert):
                logger.error("❌ Certificado del peer inválido")
                self.failure_count += 1
                return None

            # Verificar firma del peer
            peer_payload = str({k: v for k, v in peer_response.items() if k != "signature"}).encode()
            peer_signature = bytes.fromhex(peer_response["signature"])
            if not self._verify_signature(peer_payload, peer_signature, peer_cert):
                logger.error("❌ Firma del peer inválida")
                self.failure_count += 1
                return None

            # Verificar nonce (debe coincidir)
            if peer_response.get("nonce") != nonce.hex():
                logger.error("❌ Nonce no coincide")
                self.failure_count += 1
                return None

            # Verificar JWT del peer (simulado - en producción validar contra coordinator)
            peer_jwt = peer_response.get("jwt_token")
            if not peer_jwt or not await self.authenticator.validate_token(peer_jwt):
                logger.error("❌ Token JWT del peer inválido")
                self.failure_count += 1
                return None

            # Paso 3: Negociar Diffie-Hellman
            peer_dh_public_key_pem = peer_response.get("dh_public_key")
            if not peer_dh_public_key_pem:
                logger.error("❌ Clave pública DH del peer faltante")
                self.failure_count += 1
                return None

            peer_dh_public_key = serialization.load_pem_public_key(peer_dh_public_key_pem.encode())
            shared_key = self._dh_private_key.exchange(peer_dh_public_key)

            # Paso 4: Derivar clave de sesión
            session_key = self._derive_session_key(shared_key)

            # Paso 5: Establecer canal encriptado
            channel = EncryptedChannel(
                session_key=session_key,
                peer_id=peer_id,
                established_at=time.time(),
                nonce=nonce
            )

            # Medir tiempo
            handshake_time = time.time() - start_time
            self.handshake_times.append(handshake_time)

            if handshake_time > 1.0:
                logger.warning(f"⚠️ Handshake tomó {handshake_time:.3f}s (>1s)")
            else:
                logger.info(f"✅ Handshake completado en {handshake_time:.3f}s")

            self.success_count += 1
            logger.info(f"🔒 Canal encriptado establecido con {peer_id}")
            return channel

        except Exception as e:
            logger.error(f"❌ Error en handshake con {peer_id}: {e}")
            self.failure_count += 1
            return None

    async def _send_handshake_message(self, peer_address: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Enviar mensaje de handshake al peer (simulado).

        En producción, esto usaría P2PMessageHandler para enviar mensajes reales.
        """
        # Simulación: asumir respuesta exitosa del peer
        # En implementación real, enviar vía socket/TCP/UDP y esperar respuesta

        await asyncio.sleep(0.01)  # Simular latencia de red mínima

        # Respuesta simulada del peer (con datos válidos)
        return {
            "node_id": "peer_123",
            "peer_id": self.node_id,
            "nonce": payload["nonce"],
            "certificate": self._certificate.public_bytes(serialization.Encoding.PEM).decode(),  # Simular peer cert
            "dh_public_key": self._dh_private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode(),
            "jwt_token": "simulated_jwt_token",
            "signature": "simulated_signature",
            "timestamp": time.time()
        }

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del handshake."""
        avg_time = sum(self.handshake_times) / len(self.handshake_times) if self.handshake_times else 0
        return {
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "total_handshakes": self.success_count + self.failure_count,
            "avg_handshake_time": avg_time,
            "max_handshake_time": max(self.handshake_times) if self.handshake_times else 0,
            "handshakes_under_1s": sum(1 for t in self.handshake_times if t < 1.0)
        }


# Pruebas de seguridad
def test_security_validations():
    """Ejecutar pruebas de seguridad básicas."""
    from ..sdk.auth import create_node_authenticator

    async def run_tests():
        # Crear authenticator simulado
        auth = await create_node_authenticator("test_node", "http://localhost:8000")

        # Crear handshake
        handshake = P2PHandshake("test_node", auth)

        # Prueba 1: Generación de nonce
        nonce1 = handshake._generate_nonce()
        nonce2 = handshake._generate_nonce()
        assert nonce1 != nonce2, "Nonces deben ser únicos"
        assert len(nonce1) == 32, "Nonce debe ser 32 bytes"

        # Prueba 2: Firma y verificación
        test_payload = b"test message"
        signature = handshake._sign_payload(test_payload)
        assert handshake._verify_signature(test_payload, signature, handshake._certificate), "Firma debe verificarse"

        # Prueba 3: Certificado válido
        assert handshake._validate_certificate(handshake._certificate), "Certificado debe ser válido"

        # Prueba 4: Derivación de clave de sesión
        shared_key = secrets.token_bytes(32)
        session_key = handshake._derive_session_key(shared_key)
        assert len(session_key) == 32, "Clave de sesión debe ser 32 bytes"

        logger.info("✅ Todas las pruebas de seguridad pasaron")

    asyncio.run(run_tests())


if __name__ == "__main__":
    test_security_validations()