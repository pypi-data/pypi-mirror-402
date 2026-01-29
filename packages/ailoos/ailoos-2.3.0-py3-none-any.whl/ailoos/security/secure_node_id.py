"""
Generación segura de Node IDs para AILOOS
Sistema criptográfico para identificación única y segura de nodos.
"""

import hashlib
import json
import secrets
import uuid
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SecureNodeIDGenerator:
    """
    Generador seguro de IDs de nodos con propiedades criptográficas.

    Características:
    - Unicidad garantizada
    - Resistencia a colisiones
    - No reversible (hash-based)
    - Incluye fingerprint de hardware
    """

    def __init__(self, namespace: str = "ailoos"):
        self.namespace = namespace

    def generate_secure_node_id(self, hardware_fingerprint: Optional[str] = None) -> str:
        """
        Generar ID de nodo seguro y único.

        Args:
            hardware_fingerprint: Fingerprint opcional del hardware

        Returns:
            ID de nodo único y seguro
        """
        # Componentes del ID
        timestamp = str(uuid.uuid1().time)  # UUID1 incluye timestamp
        random_component = secrets.token_hex(16)  # 32 caracteres aleatorios
        namespace_hash = hashlib.sha256(self.namespace.encode()).hexdigest()[:16]

        # Fingerprint de hardware (si disponible)
        if hardware_fingerprint:
            hw_hash = hashlib.sha256(hardware_fingerprint.encode()).hexdigest()[:16]
        else:
            hw_hash = secrets.token_hex(8)  # Fallback aleatorio

        # Combinar componentes
        combined = f"{namespace_hash}-{timestamp}-{random_component}-{hw_hash}"

        # Hash final para ofuscación
        final_id = hashlib.sha256(combined.encode()).hexdigest()[:32]

        # Formato legible: ailoos-xxxxxxxxxxxx
        node_id = f"ailoos-{final_id}"

        logger.info(f"🔐 Generado ID de nodo seguro: {node_id}")
        return node_id

    def validate_node_id(self, node_id: str) -> bool:
        """
        Validar formato de ID de nodo.

        Args:
            node_id: ID a validar

        Returns:
            True si el formato es válido
        """
        if not node_id.startswith("ailoos-"):
            return False

        # Verificar longitud (prefijo + 32 caracteres)
        if len(node_id) != 39:  # "ailoos-" + 32 chars
            return False

        # Verificar que el resto sean caracteres hexadecimales
        hex_part = node_id[7:]  # Después de "ailoos-"
        try:
            int(hex_part, 16)
            return True
        except ValueError:
            return False

    def get_node_fingerprint(self) -> str:
        """
        Generar fingerprint único del hardware del nodo.

        Returns:
            Fingerprint hash del hardware
        """
        import platform
        import socket
        import getpass

        try:
            # Recopilar información del sistema
            system_info = {
                "platform": platform.platform(),
                "processor": platform.processor(),
                "hostname": socket.gethostname(),
                "username": getpass.getuser(),
                "mac_address": self._get_mac_address(),
                "cpu_count": self._get_cpu_info()
            }

            # Crear fingerprint
            info_string = json.dumps(system_info, sort_keys=True)
            fingerprint = hashlib.sha256(info_string.encode()).hexdigest()

            return fingerprint

        except Exception as e:
            logger.warning(f"⚠️ Error generando hardware fingerprint: {e}")
            # Fallback: usar random
            return secrets.token_hex(32)

    def _get_mac_address(self) -> str:
        """Obtener dirección MAC del sistema."""
        try:
            import uuid
            # Usar UUID del sistema (basado en MAC)
            return str(uuid.getnode())
        except:
            return "unknown"

    def _get_cpu_info(self) -> str:
        """Obtener información básica de CPU."""
        try:
            import psutil
            return str(psutil.cpu_count())
        except:
            return "unknown"


# Instancia global
_node_id_generator = SecureNodeIDGenerator()


def generate_node_id(hardware_fingerprint: Optional[str] = None) -> str:
    """
    Función de conveniencia para generar ID de nodo seguro.

    Args:
        hardware_fingerprint: Fingerprint opcional del hardware

    Returns:
        ID de nodo único
    """
    return _node_id_generator.generate_secure_node_id(hardware_fingerprint)


def get_current_node_fingerprint() -> str:
    """
    Obtener fingerprint del nodo actual.

    Returns:
        Fingerprint del hardware
    """
    return _node_id_generator.get_node_fingerprint()


def validate_node_id_format(node_id: str) -> bool:
    """
    Validar formato de ID de nodo.

    Args:
        node_id: ID a validar

    Returns:
        True si válido
    """
    return _node_id_generator.validate_node_id(node_id)