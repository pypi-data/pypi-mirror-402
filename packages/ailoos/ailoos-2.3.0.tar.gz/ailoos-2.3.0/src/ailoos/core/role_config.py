"""
Role-based configuration system for AILOOS nodes.
Loads hardware configurations, applies role-specific settings, and integrates with the existing AILOOS configuration system.
"""

import os
import yaml
import json
import logging
import sys
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

from .node_roles import NodeRole, get_role_capabilities, get_role_config, validate_node_for_role

# Add scripts directory to path for hardware_detector import
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

try:
    from hardware_detector import HardwareDetector
except ImportError:
    logger.warning("HardwareDetector not available, using fallback detection")
    HardwareDetector = None


class RoleConfigManager:
    """
    Manages role-based configurations for AILOOS nodes.

    This class handles:
    - Loading hardware configurations
    - Applying role-specific settings
    - Integrating with the existing AILOOS configuration system
    """

    def __init__(self, config_dir: str = "config", ailoos_config_file: str = "ailoos.yaml"):
        """
        Initialize the role configuration manager.

        Args:
            config_dir: Directory containing configuration files
            ailoos_config_file: Main AILOOS configuration file
        """
        self.config_dir = Path(config_dir)
        self.ailoos_config_file = self.config_dir / ailoos_config_file
        self.hardware_detector = HardwareDetector() if HardwareDetector else None
        self._hardware_config = None
        self._role = None
        self._merged_config = None

    def load_hardware_config(self) -> Dict[str, Any]:
        """
        Load hardware configuration using the hardware detector.

        Returns:
            Dictionary containing hardware capabilities and assigned role
        """
        try:
            logger.info("🔍 Loading hardware configuration...")

            if self.hardware_detector:
                # Use full hardware detector
                capabilities = self.hardware_detector.detect_hardware()
                role_str = self.hardware_detector.assign_role(capabilities)
                role_config = self.hardware_detector.generate_config(role_str, capabilities)
                capabilities_dict = capabilities.__dict__
            else:
                # Fallback detection
                capabilities_dict, role_str, role_config = self._fallback_hardware_detection()

            self._role = NodeRole(role_str.lower())

            # Store hardware config
            self._hardware_config = {
                "capabilities": capabilities_dict,
                "assigned_role": role_str,
                "role_config": role_config
            }

            logger.info(f"✅ Hardware config loaded. Assigned role: {role_str}")
            return self._hardware_config

        except Exception as e:
            logger.error(f"Failed to load hardware config: {e}")
            raise

    def _fallback_hardware_detection(self) -> tuple:
        """
        Fallback hardware detection when HardwareDetector is not available.

        Returns:
            Tuple of (capabilities_dict, role_str, role_config)
        """
        import psutil
        import platform

        # Basic hardware detection
        cpu_count = psutil.cpu_count(logical=True) or 4
        memory_gb = round(psutil.virtual_memory().total / (1024**3), 1)

        # Simple GPU check
        gpu_available = False
        try:
            import torch
            gpu_available = torch.cuda.is_available()
        except ImportError:
            pass

        capabilities = {
            "cpu_cores": cpu_count,
            "total_memory_gb": memory_gb,
            "gpu_available": gpu_available,
            "gpu_memory_gb": 8.0 if gpu_available else 0.0,
            "performance_score": 2.5 if gpu_available else 1.5
        }

        # Assign role based on basic criteria
        role_str = "FORGE" if gpu_available or memory_gb >= 16 else "SCOUT"

        # Generate basic role config
        if role_str == "SCOUT":
            role_config = {
                "inference_config": {"device": "cpu", "max_batch_size": 4, "precision": "fp32"},
                "training_config": {"device": "cpu", "batch_size": 1},
                "resource_limits": {"cpu_limit": "2", "memory_limit": "4Gi"}
            }
        else:
            role_config = {
                "inference_config": {"device": "cuda" if gpu_available else "cpu", "max_batch_size": 8, "precision": "fp16" if gpu_available else "fp32"},
                "training_config": {"device": "cuda" if gpu_available else "cpu", "batch_size": 8},
                "resource_limits": {"cpu_limit": str(cpu_count), "memory_limit": f"{int(memory_gb)}Gi"}
            }

        return capabilities, role_str, role_config

    def apply_role_settings(self, base_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Apply role-specific settings to the configuration.

        Args:
            base_config: Base configuration to extend (optional)

        Returns:
            Merged configuration with role-specific settings applied
        """
        if self._hardware_config is None:
            self.load_hardware_config()

        try:
            logger.info(f"🎯 Applying {self._role.value} role settings...")

            # Get role capabilities and config
            capabilities = get_role_capabilities(self._role)
            role_specific_config = get_role_config(self._role)

            # Start with base config or empty dict
            merged_config = base_config.copy() if base_config else {}

            # Apply role capabilities
            merged_config["role"] = {
                "name": self._role.value,
                "capabilities": capabilities.__dict__,
                "config": role_specific_config.__dict__
            }

            # Apply hardware-specific settings
            hardware_config = self._hardware_config["role_config"]
            merged_config["hardware"] = self._hardware_config["capabilities"]
            merged_config["inference"] = hardware_config.get("inference_config", {})
            merged_config["training"] = hardware_config.get("training_config", {})
            merged_config["resources"] = hardware_config.get("resource_limits", {})
            merged_config["optimization"] = hardware_config.get("optimization_settings", {})

            # Validate node meets role requirements
            node_hardware = self._hardware_config["capabilities"]
            if not validate_node_for_role(node_hardware, self._role):
                logger.warning(f"Node hardware does not fully meet {self._role.value} requirements")

            self._merged_config = merged_config
            logger.info(f"✅ Role settings applied for {self._role.value}")
            return merged_config

        except Exception as e:
            logger.error(f"Failed to apply role settings: {e}")
            raise

    def load_ailoos_config(self) -> Dict[str, Any]:
        """
        Load the existing AILOOS configuration from file.

        Returns:
            Dictionary containing AILOOS configuration
        """
        try:
            if not self.ailoos_config_file.exists():
                logger.warning(f"AILOOS config file not found: {self.ailoos_config_file}")
                return {}

            with open(self.ailoos_config_file, 'r', encoding='utf-8') as f:
                if self.ailoos_config_file.suffix.lower() in ['.yaml', '.yml']:
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)

            logger.info(f"✅ AILOOS config loaded from {self.ailoos_config_file}")
            return config or {}

        except Exception as e:
            logger.error(f"Failed to load AILOOS config: {e}")
            return {}

    def integrate_configs(self, save_to_file: bool = False, output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Integrate role-based config with existing AILOOS configuration.

        Args:
            save_to_file: Whether to save the merged config to file
            output_file: Output file path (optional)

        Returns:
            Fully integrated configuration
        """
        try:
            # Load existing AILOOS config
            ailoos_config = self.load_ailoos_config()

            # Apply role settings to base config
            integrated_config = self.apply_role_settings(ailoos_config)

            # Add metadata
            integrated_config["_metadata"] = {
                "generated_by": "RoleConfigManager",
                "role": self._role.value if self._role else None,
                "hardware_detected": bool(self._hardware_config)
            }

            if save_to_file:
                output_path = Path(output_file) if output_file else self.config_dir / "node_config.yaml"
                self.save_config(integrated_config, output_path)
                logger.info(f"💾 Integrated config saved to {output_path}")

            logger.info("✅ Configuration integration completed")
            return integrated_config

        except Exception as e:
            logger.error(f"Failed to integrate configs: {e}")
            raise

    def save_config(self, config: Dict[str, Any], file_path: Path) -> None:
        """
        Save configuration to file.

        Args:
            config: Configuration dictionary
            file_path: Output file path
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                else:
                    json.dump(config, f, indent=2, ensure_ascii=False)

            logger.info(f"💾 Config saved to {file_path}")

        except Exception as e:
            logger.error(f"Failed to save config to {file_path}: {e}")
            raise

    def get_config(self) -> Optional[Dict[str, Any]]:
        """
        Get the current merged configuration.

        Returns:
            Current configuration or None if not generated
        """
        return self._merged_config

    def get_role(self) -> Optional[NodeRole]:
        """
        Get the current assigned role.

        Returns:
            Current NodeRole or None if not assigned
        """
        return self._role


def load_hardware_config() -> Dict[str, Any]:
    """
    Convenience function to load hardware configuration.

    Returns:
        Hardware configuration dictionary
    """
    manager = RoleConfigManager()
    return manager.load_hardware_config()


def apply_role_settings(base_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function to apply role settings.

    Args:
        base_config: Base configuration to extend

    Returns:
        Configuration with role settings applied
    """
    manager = RoleConfigManager()
    return manager.apply_role_settings(base_config)


def integrate_with_ailoos_config(save_to_file: bool = False, output_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to integrate role config with AILOOS config.

    Args:
        save_to_file: Whether to save the merged config
        output_file: Output file path

    Returns:
        Integrated configuration
    """
    manager = RoleConfigManager()
    return manager.integrate_configs(save_to_file, output_file)