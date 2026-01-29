"""
PubSub Configuration
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PubSubConfig:
    """Configuración del sistema PubSub"""
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    max_connections: int = 10
    message_ttl: int = 3600  # segundos
    enable_monitoring: bool = True