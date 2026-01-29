"""
Role-based system for Ailoos nodes.
Defines SCOUT (lightweight) and FORGE (training) node roles with their capabilities and configurations.
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class NodeRole(Enum):
    """Enumeration of available node roles."""
    SCOUT = "scout"
    FORGE = "forge"


@dataclass
class RoleCapabilities:
    """Capabilities and resource limits for a node role."""
    can_train: bool = False
    can_infer: bool = False
    can_scout: bool = False
    can_federate: bool = False
    max_memory_gb: float = 4.0
    max_cpu_cores: int = 2
    max_gpu_memory_gb: Optional[float] = None
    max_concurrent_sessions: int = 1
    priority_weight: int = 1  # Higher = more priority in scheduling
    supports_distributed_training: bool = False
    supports_model_compression: bool = False
    supports_quantization: bool = False


@dataclass
class ScoutConfig:
    """Configuration specific to SCOUT role nodes."""
    scouting_batch_size: int = 32
    inference_timeout_seconds: int = 30
    data_scanning_interval_minutes: int = 15
    max_scout_sessions: int = 5
    enable_real_time_scouting: bool = True
    scout_data_categories: list = field(default_factory=lambda: ["text", "images", "audio"])
    quality_threshold: float = 0.7
    enable_auto_discovery: bool = True


@dataclass
class ForgeConfig:
    """Configuration specific to FORGE role nodes."""
    training_batch_size: int = 64
    max_training_epochs: int = 100
    gradient_accumulation_steps: int = 1
    enable_mixed_precision: bool = True
    optimizer_type: str = "adamw"
    learning_rate: float = 1e-4
    weight_decay: float = 0.01
    enable_gradient_checkpointing: bool = False
    max_model_size_gb: float = 10.0
    federated_round_timeout_minutes: int = 30


# Capability mappings for each role
ROLE_CAPABILITIES: Dict[NodeRole, RoleCapabilities] = {
    NodeRole.SCOUT: RoleCapabilities(
        can_train=False,
        can_infer=True,
        can_scout=True,
        can_federate=False,
        max_memory_gb=8.0,
        max_cpu_cores=4,
        max_gpu_memory_gb=4.0,
        max_concurrent_sessions=3,
        priority_weight=2,
        supports_distributed_training=False,
        supports_model_compression=True,
        supports_quantization=True
    ),
    NodeRole.FORGE: RoleCapabilities(
        can_train=True,
        can_infer=True,
        can_scout=False,
        can_federate=True,
        max_memory_gb=64.0,
        max_cpu_cores=16,
        max_gpu_memory_gb=24.0,
        max_concurrent_sessions=1,
        priority_weight=5,
        supports_distributed_training=True,
        supports_model_compression=False,
        supports_quantization=False
    )
}


# Configuration mappings for each role
ROLE_CONFIGS: Dict[NodeRole, Any] = {
    NodeRole.SCOUT: ScoutConfig(),
    NodeRole.FORGE: ForgeConfig()
}


def get_role_capabilities(role: NodeRole) -> RoleCapabilities:
    """
    Get capabilities for a specific node role.

    Args:
        role: The node role to get capabilities for

    Returns:
        RoleCapabilities object with the role's capabilities

    Raises:
        ValueError: If role is not supported
    """
    if role not in ROLE_CAPABILITIES:
        raise ValueError(f"Unsupported node role: {role}")
    return ROLE_CAPABILITIES[role]


def get_role_config(role: NodeRole) -> Any:
    """
    Get configuration object for a specific node role.

    Args:
        role: The node role to get configuration for

    Returns:
        Configuration dataclass instance for the role

    Raises:
        ValueError: If role is not supported
    """
    if role not in ROLE_CONFIGS:
        raise ValueError(f"Unsupported node role: {role}")
    return ROLE_CONFIGS[role]


def validate_node_for_role(node_hardware: Dict[str, Any], role: NodeRole) -> bool:
    """
    Validate if a node's hardware meets the requirements for a role.

    Args:
        node_hardware: Hardware information from node._detect_hardware()
        role: The role to validate against

    Returns:
        True if node meets requirements, False otherwise
    """
    capabilities = get_role_capabilities(role)

    # Check memory
    node_memory = node_hardware.get('memory_gb', 0)
    if node_memory < capabilities.max_memory_gb * 0.8:  # Allow 80% utilization
        logger.warning(f"Node memory {node_memory}GB below role requirement {capabilities.max_memory_gb}GB")
        return False

    # Check CPU cores
    node_cpu = node_hardware.get('cpu_cores', 0)
    if node_cpu < capabilities.max_cpu_cores:
        logger.warning(f"Node CPU cores {node_cpu} below role requirement {capabilities.max_cpu_cores}")
        return False

    # Check GPU if required
    if capabilities.max_gpu_memory_gb is not None:
        gpu_info = node_hardware.get('gpu', '')
        if 'CPU Only' in gpu_info or 'not available' in gpu_info.lower():
            if capabilities.max_gpu_memory_gb > 0:
                logger.warning(f"Role requires GPU but node has: {gpu_info}")
                return False

    return True


def get_available_roles() -> list[NodeRole]:
    """
    Get list of all available node roles.

    Returns:
        List of NodeRole enums
    """
    return list(NodeRole)


def get_role_description(role: NodeRole) -> str:
    """
    Get human-readable description of a node role.

    Args:
        role: The role to describe

    Returns:
        Description string
    """
    descriptions = {
        NodeRole.SCOUT: "Lightweight node optimized for data scouting, inference, and lightweight tasks",
        NodeRole.FORGE: "Heavy-duty node specialized for model training and federated learning"
    }
    return descriptions.get(role, f"Unknown role: {role}")