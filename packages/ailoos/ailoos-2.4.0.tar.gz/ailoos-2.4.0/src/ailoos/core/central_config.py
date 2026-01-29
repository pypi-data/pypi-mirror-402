"""
Centralized Configuration System for AILOOS

This module provides a unified configuration system that consolidates
all scattered configuration files into a single, hierarchical system.
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AiloosConfig:
    """
    Centralized configuration class for all AILOOS components.

    This replaces scattered config.py files throughout the codebase.
    """

    # Core settings
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4

    # Database settings
    database_url: Optional[str] = None
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Cache settings
    cache_backend: str = "redis"
    cache_host: str = "localhost"
    cache_port: int = 6379
    cache_ttl: int = 3600

    # Security settings
    secret_key: Optional[str] = None
    jwt_secret: Optional[str] = None
    encryption_key: Optional[str] = None

    # Federated Learning settings
    federated_rounds: int = 10
    federated_min_clients: int = 3
    federated_timeout: int = 300

    # Model settings
    model_cache_dir: str = "./models"
    model_max_size_mb: int = 1024

    # Monitoring settings
    monitoring_enabled: bool = True
    monitoring_interval: int = 60

    # Cloud provider settings
    cloud_provider: str = "gcp"
    gcp_project_id: Optional[str] = None
    gcp_region: str = "us-central1"

    # Feature flags
    enable_federated_learning: bool = True
    enable_zero_trust: bool = True
    enable_blockchain_audit: bool = False

    # Module-specific configs
    modules: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> 'AiloosConfig':
        """Create config from environment variables."""
        config = cls()

        # Load from environment
        config.environment = os.getenv('AILOOS_ENV', config.environment)
        config.debug = os.getenv('AILOOS_DEBUG', 'false').lower() == 'true'
        config.api_host = os.getenv('AILOOS_API_HOST', config.api_host)
        config.api_port = int(os.getenv('AILOOS_API_PORT', config.api_port))
        config.database_url = os.getenv('AILOOS_DATABASE_URL', config.database_url)
        config.secret_key = os.getenv('AILOOS_SECRET_KEY', config.secret_key)
        config.gcp_project_id = os.getenv('GCP_PROJECT_ID', config.gcp_project_id)

        return config

    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> 'AiloosConfig':
        """Load config from JSON or YAML file."""
        file_path = Path(file_path)

        if not file_path.exists():
            logger.warning(f"Config file not found: {file_path}")
            return cls.from_env()

        with open(file_path, 'r') as f:
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)

        config = cls.from_env()

        # Update with file data
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)

        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'environment': self.environment,
            'debug': self.debug,
            'log_level': self.log_level,
            'api_host': self.api_host,
            'api_port': self.api_port,
            'api_workers': self.api_workers,
            'database_url': self.database_url,
            'database_pool_size': self.database_pool_size,
            'database_max_overflow': self.database_max_overflow,
            'cache_backend': self.cache_backend,
            'cache_host': self.cache_host,
            'cache_port': self.cache_port,
            'cache_ttl': self.cache_ttl,
            'secret_key': self.secret_key,
            'jwt_secret': self.jwt_secret,
            'encryption_key': self.encryption_key,
            'federated_rounds': self.federated_rounds,
            'federated_min_clients': self.federated_min_clients,
            'federated_timeout': self.federated_timeout,
            'model_cache_dir': self.model_cache_dir,
            'model_max_size_mb': self.model_max_size_mb,
            'monitoring_enabled': self.monitoring_enabled,
            'monitoring_interval': self.monitoring_interval,
            'cloud_provider': self.cloud_provider,
            'gcp_project_id': self.gcp_project_id,
            'gcp_region': self.gcp_region,
            'enable_federated_learning': self.enable_federated_learning,
            'enable_zero_trust': self.enable_zero_trust,
            'enable_blockchain_audit': self.enable_blockchain_audit,
            'modules': self.modules
        }

    def save(self, file_path: Union[str, Path]):
        """Save config to file."""
        file_path = Path(file_path)
        data = self.to_dict()

        with open(file_path, 'w') as f:
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                yaml.dump(data, f, default_flow_style=False)
            else:
                json.dump(data, f, indent=2)

    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Get configuration for a specific module."""
        return self.modules.get(module_name, {})

    def set_module_config(self, module_name: str, config: Dict[str, Any]):
        """Set configuration for a specific module."""
        self.modules[module_name] = config


# Global config instance
_config_instance: Optional[AiloosConfig] = None


def get_config() -> AiloosConfig:
    """Get the global configuration instance."""
    global _config_instance

    if _config_instance is None:
        # Try to load from file first
        config_paths = [
            Path.cwd() / 'ailoos-config.json',
            Path.cwd() / 'ailoos-config.yaml',
            Path.home() / '.ailoos' / 'config.json',
            Path.home() / '.ailoos' / 'config.yaml'
        ]

        for config_path in config_paths:
            if config_path.exists():
                _config_instance = AiloosConfig.from_file(config_path)
                logger.info(f"Loaded config from: {config_path}")
                break
        else:
            # Fall back to environment variables
            _config_instance = AiloosConfig.from_env()
            logger.info("Loaded config from environment variables")

    return _config_instance


def reload_config() -> AiloosConfig:
    """Reload the global configuration."""
    global _config_instance
    _config_instance = None
    return get_config()


# Initialize config on import
config = get_config()