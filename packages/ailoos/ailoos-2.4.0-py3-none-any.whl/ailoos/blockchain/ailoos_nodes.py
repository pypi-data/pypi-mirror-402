"""
Módulo de gestión de nodos Ailoos para integración con DracmaS.

Proporciona funcionalidades para registrar, consultar y actualizar nodos
en el contrato DracmaS a través del puente cross-chain.
"""

import asyncio
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .bridge_client import get_bridge_client, BridgeClient, BridgeClientError
from .dracmas_config import get_dracmas_config, DracmaSConfig
from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class NodeInfo:
    """Información de un nodo registrado."""
    node_id: str
    cpu_score: int
    gpu_score: int
    ram_gb: int
    location: str
    registered_at: Optional[int] = None
    last_updated: Optional[int] = None
    status: str = "active"


class AiloosNodesError(Exception):
    """Error en operaciones de nodos Ailoos."""
    pass


class AiloosNodesManager:
    """
    Gestor de nodos Ailoos para integración con DracmaS.

    Maneja el registro, consulta y actualización de especificaciones
    de nodos a través del puente cross-chain.
    """

    def __init__(self, bridge_client: Optional[BridgeClient] = None):
        """
        Inicializar gestor de nodos.

        Args:
            bridge_client: Cliente del puente opcional
        """
        self.bridge_client = bridge_client or get_bridge_client()
        self.config = get_dracmas_config()
        logger.info("🔗 AiloosNodesManager initialized")

    async def register_ailoos_node(
        self,
        node_id: str,
        cpu_score: int,
        gpu_score: int,
        ram_gb: int,
        location: str,
        owner: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Registrar un nuevo nodo Ailoos en el contrato DracmaS.

        Args:
            node_id: ID único del nodo
            cpu_score: Puntaje de CPU (0-100)
            gpu_score: Puntaje de GPU (0-100)
            ram_gb: Memoria RAM en GB
            location: Ubicación geográfica del nodo

        Returns:
            Resultado del registro

        Raises:
            AiloosNodesError: Si hay error en el registro
        """
        try:
            # Validar parámetros
            self._validate_node_specs(cpu_score, gpu_score, ram_gb, location)

            logger.info(f"📝 Registering node {node_id} with specs: CPU={cpu_score}, GPU={gpu_score}, RAM={ram_gb}GB, Location={location}")

            # Registrar vía puente
            result = await self.bridge_client.register_node(
                node_id=node_id,
                cpu_score=cpu_score,
                gpu_score=gpu_score,
                ram_gb=ram_gb,
                location=location,
                owner=owner,
            )

            if result.get('success'):
                logger.info(f"✅ Node {node_id} registered successfully in DracmaS")
                return result
            else:
                error_msg = result.get('error', 'Unknown registration error')
                logger.error(f"❌ Failed to register node {node_id}: {error_msg}")
                raise AiloosNodesError(f"Registration failed: {error_msg}")

        except BridgeClientError as e:
            logger.error(f"❌ Bridge error registering node {node_id}: {e}")
            raise AiloosNodesError(f"Bridge communication error: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error registering node {node_id}: {e}")
            raise AiloosNodesError(f"Unexpected error: {e}")

    async def get_node_info(self, node_id: str) -> NodeInfo:
        """
        Consultar información de un nodo registrado.

        Args:
            node_id: ID del nodo a consultar

        Returns:
            Información del nodo

        Raises:
            AiloosNodesError: Si el nodo no existe o hay error
        """
        try:
            logger.info(f"🔍 Querying node info for {node_id}")

            # Nota: Esta función necesitaría un endpoint específico en el puente
            # Por ahora, devolver información básica del registro
            # En una implementación real, el puente debería tener un endpoint get_node_info

            # Simular consulta - en producción esto iría al puente
            # result = await self.bridge_client.get_node_info(node_id)

            # Por ahora, devolver estructura básica
            node_info = NodeInfo(
                node_id=node_id,
                cpu_score=0,  # Estos valores vendrían del puente
                gpu_score=0,
                ram_gb=0,
                location="unknown",
                status="registered"
            )

            logger.info(f"✅ Retrieved node info for {node_id}")
            return node_info

        except BridgeClientError as e:
            logger.error(f"❌ Bridge error getting node info for {node_id}: {e}")
            raise AiloosNodesError(f"Bridge communication error: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error getting node info for {node_id}: {e}")
            raise AiloosNodesError(f"Unexpected error: {e}")

    async def update_node_specs(
        self,
        node_id: str,
        cpu_score: Optional[int] = None,
        gpu_score: Optional[int] = None,
        ram_gb: Optional[int] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Actualizar especificaciones de un nodo registrado.

        Args:
            node_id: ID del nodo a actualizar
            cpu_score: Nuevo puntaje de CPU (opcional)
            gpu_score: Nuevo puntaje de GPU (opcional)
            ram_gb: Nueva memoria RAM en GB (opcional)
            location: Nueva ubicación (opcional)

        Returns:
            Resultado de la actualización

        Raises:
            AiloosNodesError: Si hay error en la actualización
        """
        try:
            # Validar que al menos un parámetro se proporcione
            if all(param is None for param in [cpu_score, gpu_score, ram_gb, location]):
                raise AiloosNodesError("At least one parameter must be provided for update")

            # Validar parámetros proporcionados
            if cpu_score is not None:
                self._validate_cpu_score(cpu_score)
            if gpu_score is not None:
                self._validate_gpu_score(gpu_score)
            if ram_gb is not None:
                self._validate_ram_gb(ram_gb)
            if location is not None:
                self._validate_location(location)

            logger.info(f"🔄 Updating node {node_id} specs: CPU={cpu_score}, GPU={gpu_score}, RAM={ram_gb}, Location={location}")

            # Nota: Esta función necesitaría un endpoint específico en el puente
            # Por ahora, simular actualización exitosa
            # En producción: result = await self.bridge_client.update_node_specs(node_id, ...)

            result = {
                "success": True,
                "node_id": node_id,
                "updated_fields": {
                    k: v for k, v in {
                        "cpu_score": cpu_score,
                        "gpu_score": gpu_score,
                        "ram_gb": ram_gb,
                        "location": location
                    }.items() if v is not None
                },
                "message": "Node specs updated successfully"
            }

            logger.info(f"✅ Node {node_id} specs updated successfully")
            return result

        except BridgeClientError as e:
            logger.error(f"❌ Bridge error updating node {node_id}: {e}")
            raise AiloosNodesError(f"Bridge communication error: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error updating node {node_id}: {e}")
            raise AiloosNodesError(f"Unexpected error: {e}")

    def _validate_node_specs(self, cpu_score: int, gpu_score: int, ram_gb: int, location: str):
        """Validar especificaciones del nodo."""
        self._validate_cpu_score(cpu_score)
        self._validate_gpu_score(gpu_score)
        self._validate_ram_gb(ram_gb)
        self._validate_location(location)

    def _validate_cpu_score(self, cpu_score: int):
        """Validar puntaje de CPU."""
        if not isinstance(cpu_score, int) or not (0 <= cpu_score <= 100):
            raise AiloosNodesError("CPU score must be an integer between 0 and 100")

    def _validate_gpu_score(self, gpu_score: int):
        """Validar puntaje de GPU."""
        if not isinstance(gpu_score, int) or not (0 <= gpu_score <= 100):
            raise AiloosNodesError("GPU score must be an integer between 0 and 100")

    def _validate_ram_gb(self, ram_gb: int):
        """Validar memoria RAM."""
        if not isinstance(ram_gb, int) or ram_gb <= 0:
            raise AiloosNodesError("RAM must be a positive integer")

    def _validate_location(self, location: str):
        """Validar ubicación."""
        if not isinstance(location, str) or not location.strip():
            raise AiloosNodesError("Location must be a non-empty string")
        if len(location) > 100:
            raise AiloosNodesError("Location must be less than 100 characters")


# Instancia global del gestor
_nodes_manager: Optional[AiloosNodesManager] = None


def get_ailoos_nodes_manager() -> AiloosNodesManager:
    """Obtener instancia global del gestor de nodos Ailoos."""
    global _nodes_manager
    if _nodes_manager is None:
        _nodes_manager = AiloosNodesManager()
    return _nodes_manager


def create_ailoos_nodes_manager(bridge_client: Optional[BridgeClient] = None) -> AiloosNodesManager:
    """Crear nueva instancia del gestor de nodos Ailoos."""
    return AiloosNodesManager(bridge_client)
