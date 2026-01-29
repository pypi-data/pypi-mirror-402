"""
Verificador de Imágenes con Cosign para AILOOS Federated Learning
Implementa verificación de firmas digitales en imágenes Docker antes del despliegue.
"""

import asyncio
import subprocess
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import os

from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ImageVerificationResult:
    """Resultado de verificación de imagen."""

    image_uri: str
    is_verified: bool
    signature_found: bool
    verification_time: datetime
    error_message: Optional[str] = None
    signature_details: Dict[str, Any] = field(default_factory=dict)
    cosign_version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para serialización."""
        return {
            "image_uri": self.image_uri,
            "is_verified": self.is_verified,
            "signature_found": self.signature_found,
            "verification_time": self.verification_time.isoformat(),
            "error_message": self.error_message,
            "signature_details": self.signature_details,
            "cosign_version": self.cosign_version
        }


class CosignImageVerifier:
    """
    Verificador de imágenes usando Cosign.
    Implementa verificación de firmas digitales para asegurar integridad de imágenes.
    """

    def __init__(self, public_key_env: str = "COSIGN_PUBLIC_KEY",
                 cosign_binary: str = "cosign"):
        """
        Inicializar verificador de imágenes.

        Args:
            public_key_env: Variable de entorno con clave pública
            cosign_binary: Ruta al binario de cosign
        """
        self.public_key_env = public_key_env
        self.cosign_binary = cosign_binary
        self.verification_cache: Dict[str, ImageVerificationResult] = {}
        self.cache_ttl_seconds = 3600  # 1 hora

    async def verify_image(self, image_uri: str, force_refresh: bool = False) -> ImageVerificationResult:
        """
        Verificar firma de una imagen Docker.

        Args:
            image_uri: URI de la imagen a verificar
            force_refresh: Forzar verificación aunque esté en cache

        Returns:
            Resultado de la verificación
        """
        # Verificar cache primero
        if not force_refresh and image_uri in self.verification_cache:
            cached_result = self.verification_cache[image_uri]
            # Verificar si el cache no ha expirado
            if (datetime.now() - cached_result.verification_time).seconds < self.cache_ttl_seconds:
                logger.debug(f"Usando resultado de cache para {image_uri}")
                return cached_result

        logger.info(f"🔐 Verificando firma de imagen: {image_uri}")

        try:
            # Ejecutar verificación con cosign
            result = await self._run_cosign_verify(image_uri)

            # Crear resultado
            verification_result = ImageVerificationResult(
                image_uri=image_uri,
                is_verified=result["success"],
                signature_found=result["signature_found"],
                verification_time=datetime.now(),
                error_message=result.get("error"),
                signature_details=result.get("signature_details", {}),
                cosign_version=result.get("cosign_version")
            )

            # Almacenar en cache
            self.verification_cache[image_uri] = verification_result

            if verification_result.is_verified:
                logger.info(f"✅ Imagen {image_uri} verificada exitosamente")
            else:
                logger.warning(f"❌ Verificación fallida para imagen {image_uri}: {verification_result.error_message}")

            return verification_result

        except Exception as e:
            logger.error(f"❌ Error verificando imagen {image_uri}: {e}")
            error_result = ImageVerificationResult(
                image_uri=image_uri,
                is_verified=False,
                signature_found=False,
                verification_time=datetime.now(),
                error_message=str(e)
            )
            self.verification_cache[image_uri] = error_result
            return error_result

    async def verify_images_batch(self, image_uris: List[str]) -> Dict[str, ImageVerificationResult]:
        """
        Verificar múltiples imágenes en paralelo.

        Args:
            image_uris: Lista de URIs de imágenes

        Returns:
            Diccionario con resultados de verificación
        """
        logger.info(f"🔐 Verificando {len(image_uris)} imágenes en lote")

        tasks = [self.verify_image(uri) for uri in image_uris]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        verification_results = {}
        for uri, result in zip(image_uris, results):
            if isinstance(result, Exception):
                verification_results[uri] = ImageVerificationResult(
                    image_uri=uri,
                    is_verified=False,
                    signature_found=False,
                    verification_time=datetime.now(),
                    error_message=str(result)
                )
            else:
                verification_results[uri] = result

        return verification_results

    async def _run_cosign_verify(self, image_uri: str) -> Dict[str, Any]:
        """
        Ejecutar comando cosign verify.

        Args:
            image_uri: URI de la imagen

        Returns:
            Resultado del comando
        """
        # Verificar que la clave pública esté disponible
        public_key = os.getenv(self.public_key_env)
        if not public_key:
            return {
                "success": False,
                "signature_found": False,
                "error": f"Clave pública no encontrada en variable {self.public_key_env}"
            }

        # Construir comando cosign
        cmd = [
            self.cosign_binary, "verify",
            "--key", f"env://{self.public_key_env}",
            image_uri
        ]

        try:
            # Ejecutar comando
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, self.public_key_env: public_key}
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                # Verificación exitosa
                try:
                    signature_data = json.loads(stdout.decode())
                except json.JSONDecodeError:
                    signature_data = {"raw_output": stdout.decode()}

                return {
                    "success": True,
                    "signature_found": True,
                    "signature_details": signature_data,
                    "cosign_version": await self._get_cosign_version()
                }
            else:
                # Verificación fallida
                error_msg = stderr.decode().strip()
                if "no signatures found" in error_msg.lower():
                    return {
                        "success": False,
                        "signature_found": False,
                        "error": "No se encontraron firmas para la imagen"
                    }
                else:
                    return {
                        "success": False,
                        "signature_found": True,  # Firma encontrada pero inválida
                        "error": error_msg
                    }

        except FileNotFoundError:
            return {
                "success": False,
                "signature_found": False,
                "error": f"Binario cosign no encontrado: {self.cosign_binary}"
            }
        except Exception as e:
            return {
                "success": False,
                "signature_found": False,
                "error": f"Error ejecutando cosign: {str(e)}"
            }

    async def _get_cosign_version(self) -> Optional[str]:
        """Obtener versión de cosign."""
        try:
            process = await asyncio.create_subprocess_exec(
                self.cosign_binary, "version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            if process.returncode == 0:
                return stdout.decode().strip()
        except Exception:
            pass
        return None

    def clear_cache(self):
        """Limpiar cache de verificaciones."""
        self.verification_cache.clear()
        logger.info("🧹 Cache de verificaciones limpiado")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache."""
        verified_count = sum(1 for r in self.verification_cache.values() if r.is_verified)
        failed_count = len(self.verification_cache) - verified_count

        return {
            "total_cached": len(self.verification_cache),
            "verified": verified_count,
            "failed": failed_count,
            "cache_ttl_seconds": self.cache_ttl_seconds
        }


# Instancia global del verificador
_image_verifier: Optional[CosignImageVerifier] = None


def get_image_verifier() -> CosignImageVerifier:
    """Obtener instancia global del verificador de imágenes."""
    global _image_verifier
    if _image_verifier is None:
        _image_verifier = CosignImageVerifier()
    return _image_verifier


async def verify_image_signature(image_uri: str) -> bool:
    """
    Función de conveniencia para verificar firma de imagen.

    Args:
        image_uri: URI de la imagen

    Returns:
        True si la imagen está verificada
    """
    verifier = get_image_verifier()
    result = await verifier.verify_image(image_uri)
    return result.is_verified


async def verify_images_batch(image_uris: List[str]) -> Dict[str, bool]:
    """
    Función de conveniencia para verificar múltiples imágenes.

    Args:
        image_uris: Lista de URIs de imágenes

    Returns:
        Diccionario con resultados booleanos
    """
    verifier = get_image_verifier()
    results = await verifier.verify_images_batch(image_uris)
    return {uri: result.is_verified for uri, result in results.items()}