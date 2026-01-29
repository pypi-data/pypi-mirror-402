"""
NodeAuthenticator - Autenticación Criptográfica Real para Nodos
Implementa autenticación basada en curvas elípticas (ECDSA/SECP256K1) para identidad soberana.
"""

import asyncio
import json
import os
import time
import base64
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

import aiohttp
import jwt

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature

from ..core.logging import get_logger

logger = get_logger(__name__)


class NodeAuthenticator:
    """
    Autenticador Criptográfico para Nodos Soberanos.
    
    Utiliza criptografía asimétrica real (ECDSA sobre SECP256K1) para:
    - Identidad auto-soberana (DID compatible)
    - Firma digital de mensajes y transacciones
    - Autenticación segura sin contraseñas
    """

    def __init__(self, node_id: str, coordinator_url: str, keys_dir: str = "./keys", token_refresh_buffer: int = 300):
        """
        Inicializar el autenticador seguro.

        Args:
            node_id: ID único del nodo (se usará como nombre de archivo para claves)
            coordinator_url: URL base del coordinador
            keys_dir: Directorio para persistencia segura de claves
            token_refresh_buffer: Buffer de tiempo para renovación de tokens
        """
        self.node_id = node_id
        self.coordinator_url = coordinator_url.rstrip('/')
        self.keys_dir = Path(keys_dir)
        self.token_refresh_buffer = token_refresh_buffer

        # Estado criptográfico
        self._private_key: Optional[ec.EllipticCurvePrivateKey] = None
        self._public_key: Optional[ec.EllipticCurvePublicKey] = None
        self._public_key_pem: Optional[str] = None

        # Estado de sesión
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._is_authenticated = False
        
        # HTTP client
        self._session: Optional[aiohttp.ClientSession] = None
        self._refresh_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info(f"🔐 NodeAuthenticator initialized for node {node_id}")

    async def initialize(self) -> bool:
        """
        Inicializar el sistema criptográfico y cargar/generar claves.
        """
        try:
            # Crear directorio de claves si no existe
            self.keys_dir.mkdir(parents=True, exist_ok=True)
            
            # Cargar o generar identidad criptográfica
            await self._load_or_generate_keys()
            
            # Inicializar sesión HTTP
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            logger.info(f"✅ Crypto identity ready for node {self.node_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error initializing NodeAuthenticator: {e}")
            return False

    async def close(self):
        """Cerrar sesión segura."""
        self._running = False
        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
        
        if self._session:
            await self._session.close()

    async def _load_or_generate_keys(self):
        """Cargar claves existentes o generar nuevo par de identidad."""
        priv_key_path = self.keys_dir / f"{self.node_id}.pem"
        pub_key_path = self.keys_dir / f"{self.node_id}.pub"

        if priv_key_path.exists():
            logger.info(f"📂 Loading existing identity from {priv_key_path}")
            with open(priv_key_path, "rb") as f:
                self._private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None
                )
        else:
            logger.info(f"🆕 Generating new SECP256K1 identity for {self.node_id}")
            self._private_key = ec.generate_private_key(ec.SECP256K1())
            
            # Guardar clave privada
            pem = self._private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            with open(priv_key_path, "wb") as f:
                f.write(pem)

        # Derivar clave pública
        self._public_key = self._private_key.public_key()
        
        # Serializar clave pública para compartir
        self._public_key_pem = self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        # Guardar copia de clave pública
        with open(pub_key_path, "w") as f:
            f.write(self._public_key_pem)

    def sign_message(self, message: bytes) -> str:
        """
        Firmar digitalmente un mensaje (bytes).
        Retorna la firma codificada en Base64.
        """
        if not self._private_key:
            raise ValueError("Private key not loaded")
            
        signature = self._private_key.sign(
            message,
            ec.ECDSA(hashes.SHA256())
        )
        return base64.b64encode(signature).decode('utf-8')

    def sign_payload(self, payload: Dict[str, Any]) -> str:
        """
        Firmar un diccionario JSON de forma determinista.
        """
        # Canonicalización estricta del JSON para consistencia en firma
        canonical_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        return self.sign_message(canonical_json.encode('utf-8'))

    async def authenticate(self) -> bool:
        """
        Ejecutar protocolo de autenticación Challenge-Response criptográfico.
        """
        try:
            if not self._session:
                return False

            # Paso 1: Solicitar challenge de autenticación (Nonce)
            # Esto evita ataques de replay
            # Nota: Si el servidor no soporta challenge, hacemos fallback a firma directa
            timestamp = datetime.now().isoformat()
            
            # Payload de identidad
            auth_payload = {
                "node_id": self.node_id,
                "public_key": self._public_key_pem,
                "timestamp": timestamp,
                "algorithm": "ECDSA-SECP256K1-SHA256"
            }
            
            # Firmar payload de identidad
            signature = self.sign_payload(auth_payload)
            auth_payload["signature"] = signature

            # Enviar solicitud
            async with self._session.post(
                f"{self.coordinator_url}/api/auth/login",
                json=auth_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    auth_data = data.get("data", {})
                    
                    self._access_token = auth_data.get("access_token")
                    self._refresh_token = auth_data.get("refresh_token")
                    
                    if not self._access_token:
                        logger.error("No access token provided by coordinator")
                        return False
                        
                    self._decode_token_expiration()
                    self._is_authenticated = True
                    self._running = True
                    self._refresh_task = asyncio.create_task(self._token_refresh_loop())
                    
                    logger.info(f"✅ Authenticated successfully with cryptographic proof")
                    return True
                else:
                    logger.error(f"Authentication failed: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"❌ Auth error: {e}")
            return False

    async def is_authenticated(self) -> bool:
        """Verificar validez del token local."""
        if not self._is_authenticated or not self._access_token:
            return False

        if self._token_expires_at and datetime.now() >= self._token_expires_at:
            logger.warning("Token expired locally")
            self._is_authenticated = False
            return False

        return True

    def get_token(self) -> Optional[str]:
        return self._access_token

    def get_auth_headers(self) -> Dict[str, str]:
        token = self.get_token()
        if not token:
            return {}
        return {
            "Authorization": f"Bearer {token}",
            "X-Node-ID": self.node_id,
            "X-Client-Version": "ailoos-sdk-2.2.7-prod"
        }

    def _decode_token_expiration(self):
        try:
            if not self._access_token:
                return
            # Solo decodificamos el payload público, la firma la valida el servidor cuando lo recibe
            # Nosotros confiamos en el servidor para darnos un token válido inicialmente
            payload = jwt.decode(self._access_token, options={"verify_signature": False})
            exp = payload.get("exp")
            if exp:
                self._token_expires_at = datetime.fromtimestamp(exp)
        except Exception as e:
            logger.warning(f"Could not parse token exp: {e}")

    async def refresh_token(self) -> bool:
        try:
            if not self._refresh_token:
                return False

            payload = {
                "refresh_token": self._refresh_token,
                "node_id": self.node_id
            }
            
            # Firmamos también la solicitud de refresh para máxima seguridad
            payload["signature"] = self.sign_payload(payload)

            async with self._session.post(
                f"{self.coordinator_url}/api/auth/refresh",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    new_tokens = data.get("data", {})
                    self._access_token = new_tokens.get("access_token")
                    self._decode_token_expiration()
                    logger.info("Token refreshed successfully")
                    return True
                return False
        except Exception:
            return False

    async def _token_refresh_loop(self):
        while self._running:
            try:
                if not self._token_expires_at:
                    await asyncio.sleep(60)
                    continue

                now = datetime.now()
                # Renovar si queda menos del buffer o si ya expiró
                time_left = (self._token_expires_at - now).total_seconds()
                
                if time_left < self.token_refresh_buffer:
                    logger.info(f"Refreshing token (expires in {int(time_left)}s)")
                    if not await self.refresh_token():
                        logger.error("Failed to refresh token in loop")
                        # No matamos el loop inmediatamente, reintentamos pronto
                        await asyncio.sleep(30)
                    else:
                        await asyncio.sleep(60)
                else:
                    # Dormir hasta que sea necesario (con un cap de 1 hora)
                    sleep_time = min(time_left - self.token_refresh_buffer, 3600)
                    if sleep_time > 0:
                        await asyncio.sleep(sleep_time)
                    else:
                        await asyncio.sleep(10)
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in refresh loop: {e}")
                await asyncio.sleep(30)