"""
Physical Nodes - Gestión de dispositivos reales en la red federada.
Incluye detección automática de hardware y conexión al coordinador.
"""

from .physical_node import (
    PhysicalNodeManager,
    NodeCapabilities,
    NodeStatus,
    create_physical_node,
    start_physical_node,
    get_node_capabilities
)

__all__ = [
    'PhysicalNodeManager',
    'NodeCapabilities',
    'NodeStatus',
    'create_physical_node',
    'start_physical_node',
    'get_node_capabilities'
]