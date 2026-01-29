"""
Sistema de configuración centralizado para AILOOS.
Gestiona todas las configuraciones del sistema de manera unificada.
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

import logging

logger = logging.getLogger(__name__)

# Load secrets from GCP Secret Manager (preferred) or .env files (fallback)
_secret_manager = None
_gcp_project_id = os.getenv('GCP_PROJECT_ID')
try:
    from ..security.gcp_secret_manager import get_secret_manager
    from ..security.secure_node_id import generate_node_id, get_current_node_fingerprint

    # Initialize GCP Secret Manager for production

    if _gcp_project_id:
        import asyncio
        try:
            # Initialize secret manager asynchronously
            async def init_secrets():
                global _secret_manager
                _secret_manager = await get_secret_manager(_gcp_project_id, os.getenv('AILOOS_ENV', 'development'))
                if _secret_manager:
                    logger.info("✅ GCP Secret Manager initialized for secure configuration")
                return _secret_manager

            # Run in event loop if available, otherwise skip for now
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Schedule for later execution
                    asyncio.create_task(init_secrets())
                else:
                    _secret_manager = loop.run_until_complete(init_secrets())
            except RuntimeError:
                # No event loop, will initialize later
                pass

        except Exception as e:
            logger.warning(f"⚠️ GCP Secret Manager initialization failed: {e}")
            logger.info("🔄 Falling back to .env files")

    # Fallback: Load .env file if GCP is not available
    if not _secret_manager:
        try:
            from dotenv import load_dotenv
            # Load .env from current directory
            env_path = Path.cwd() / ".env"
            if env_path.exists():
                load_dotenv(env_path)
                if os.getenv('AILOOS_ENV') == 'production':
                    logger.warning(f"⚠️ Using insecure .env file: {env_path} - Migrate to GCP Secret Manager for production")
                else:
                    logger.info(f"✅ Loaded configuration from local .env file: {env_path}")
        except ImportError:
            logger.info("ℹ️ python-dotenv not available, skipping .env file loading")

except ImportError as e:
    logger.warning(f"⚠️ Security modules not available: {e}")
    # Fallback to basic .env loading
    try:
        from dotenv import load_dotenv
        env_path = Path.cwd() / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            if os.getenv('AILOOS_ENV') == 'production':
                logger.warning(f"⚠️ Using insecure .env file: {env_path}")
            else:
                logger.info(f"✅ Loaded configuration from local .env file: {env_path}")
    except ImportError:
        logger.info("ℹ️ python-dotenv not available, skipping .env file loading")


@dataclass
class DatabaseConfig:
    """Configuración de base de datos con TLS 1.3 obligatorio."""
    host: str = "localhost"
    port: int = 5432
    database: str = "ailoos"
    user: str = "ailoos"
    password: str = ""
    ssl_mode: str = "require"  # En producción: "verify-full" para máxima seguridad
    ssl_min_protocol_version: str = "TLSv1.3"  # TLS 1.3 obligatorio
    ssl_cert_file: str = ""  # Ruta al certificado cliente (opcional)
    ssl_key_file: str = ""   # Ruta a la clave privada cliente (opcional)
    ssl_ca_file: str = ""    # Ruta al CA certificate
    connection_pool_size: int = 20
    connection_timeout: int = 30

    @property
    def connection_string(self) -> str:
        """Generar connection string con configuración TLS completa."""
        base_url = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

        # Parámetros SSL/TLS
        ssl_params = [f"sslmode={self.ssl_mode}"]

        if self.ssl_mode != "disable" and self.ssl_min_protocol_version:
            ssl_params.append(f"ssl_min_protocol_version={self.ssl_min_protocol_version}")

        if self.ssl_mode != "disable" and self.ssl_cert_file:
            ssl_params.append(f"sslcert={self.ssl_cert_file}")

        if self.ssl_mode != "disable" and self.ssl_key_file:
            ssl_params.append(f"sslkey={self.ssl_key_file}")

        if self.ssl_mode != "disable" and self.ssl_ca_file:
            ssl_params.append(f"sslrootcert={self.ssl_ca_file}")

        return f"{base_url}?{'&'.join(ssl_params)}"


@dataclass
class RedisConfig:
    """Configuración de Redis."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str = ""
    max_connections: int = 20
    socket_timeout: int = 5
    socket_connect_timeout: int = 5


@dataclass
class IPFSConfig:
    """Configuración de IPFS."""
    api_host: str = "localhost"
    api_port: int = 5001
    gateway_host: str = "localhost"
    gateway_port: int = 8080
    timeout: int = 30
    max_file_size_mb: int = 100


@dataclass
class BlockchainConfig:
    """Configuración de blockchain."""
    network: str = "emporiochain"
    rpc_url: str = "https://rpc.empooriochain.dev:443"
    chain_id: int = 0  # EmporioChain usa bridge; chain_id EVM no aplica
    gas_limit: int = 2000000
    gas_price_gwei: int = 50
    dracma_contract_address: str = ""
    staking_contract_address: str = ""
    private_key: str = ""  # Solo para desarrollo


@dataclass
class FederatedConfig:
    """Configuración del sistema federado."""
    coordinator_url: str = "http://localhost:5001"
    min_nodes_per_session: int = 3
    max_nodes_per_session: int = 100
    default_rounds: int = 5
    privacy_budget: float = 1.0
    aggregation_algorithm: str = "fedavg"
    enable_differential_privacy: bool = True
    enable_homomorphic_encryption: bool = False
    heartbeat_interval_seconds: int = 30
    session_timeout_minutes: int = 60


@dataclass
class MonitoringConfig:
    """Configuración del sistema de monitoreo."""
    enabled: bool = True
    timescale_host: str = "localhost"
    timescale_port: int = 5432
    timescale_database: str = "ailoos_monitoring"
    timescale_user: str = "ailoos"
    timescale_password: str = ""
    alertmanager_url: str = "http://localhost:9093/api/v2/alerts"
    prometheus_url: str = "http://localhost:9090"
    metrics_interval_seconds: int = 300
    retention_days: int = 90


@dataclass
class DataSourceConfig:
    """Configuración de fuentes de datos."""
    name: str
    url: str
    category: str
    enabled: bool = True
    update_interval_hours: int = 24
    max_size_mb: int = 1000
    quality_threshold: float = 0.5
    auto_listing: bool = True
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class DataConfig:
    """Configuración del sistema de datos."""
    chunk_size_mb: int = 100
    max_concurrent_downloads: int = 3
    download_timeout_seconds: int = 300
    verification_retries: int = 3
    auto_listing_enabled: bool = True
    pricing_strategy: str = "dynamic"  # dynamic, fixed, auction
    min_listing_quality: float = 0.5
    max_listing_size_mb: int = 10000
    federated_integration: bool = True
    sources: List[DataSourceConfig] = None

    def __post_init__(self):
        if self.sources is None:
            self.sources = []


@dataclass
class DeploymentConfig:
    """Configuración del sistema de despliegue."""
    kubernetes_enabled: bool = True
    default_namespace: str = "ailoos"
    default_cpu_request: str = "500m"
    default_memory_request: str = "1Gi"
    default_cpu_limit: str = "2000m"
    default_memory_limit: str = "4Gi"
    enable_hpa: bool = True
    min_replicas: int = 1
    max_replicas: int = 10
    target_cpu_utilization: int = 70
    target_memory_utilization: int = 80


@dataclass
class APIConfig:
    """Configuración de APIs."""
    compliance_host: str = "0.0.0.0"
    compliance_port: int = 8000
    federated_host: str = "0.0.0.0"
    federated_port: int = 8001
    marketplace_host: str = "0.0.0.0"
    marketplace_port: int = 8002
    wallet_host: str = "0.0.0.0"
    wallet_port: int = 8003
    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 8004
    enable_cors: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    jwt_secret: Optional[str] = None
    jwt_expiration_hours: int = 24

    def get_cors_origins(self, environment: str) -> List[str]:
        """Obtener orígenes CORS según el entorno."""
        if environment == "development":
            return [
                "http://localhost:3000",
                "http://localhost:8000",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8000",
                "http://localhost:5173",  # Vite dev server
                "http://127.0.0.1:5173"
            ]
        elif environment == "staging":
            return [
                "https://staging.ailoos.com",
                "https://api-staging.ailoos.com"
            ]
        elif environment == "production":
            return [
                "https://www.ailoos.com",
                "https://ailoos.com",
                "https://api.ailoos.com"
            ]
        else:
            # Fallback seguro
            return []

    def get_trusted_hosts(self, environment: str) -> List[str]:
        """Obtener hosts confiables según el entorno."""
        if environment == "development":
            return [
                "localhost",
                "127.0.0.1",
                "0.0.0.0"
            ]
        elif environment == "staging":
            return [
                "staging.ailoos.com",
                "api-staging.ailoos.com"
            ]
        elif environment == "production":
            return [
                "www.ailoos.com",
                "ailoos.com",
                "api.ailoos.com"
            ]
        else:
            # Fallback seguro
            return []


@dataclass
class SecurityConfig:
    """Configuración de seguridad."""
    enable_encryption: bool = True
    encryption_algorithm: str = "AES-256-GCM"
    enable_audit_logging: bool = True
    audit_log_retention_days: int = 365
    enable_rate_limiting: bool = True
    rate_limit_requests_per_minute: int = 100
    enable_ip_whitelisting: bool = False
    allowed_ips: List[str] = field(default_factory=list)


@dataclass
class NotificationConfig:
    """Configuración del sistema de notificaciones."""
    enabled: bool = True
    discord_webhook_url: str = ""
    email_smtp_host: str = ""
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    notification_retention_days: int = 30


@dataclass
class AiloosConfig:
    """
    Configuración centralizada de AILOOS.
    Contiene todas las configuraciones del sistema.
    """

    # Metadata
    version: str = "1.0.0"
    environment: str = "development"  # development, staging, production
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Componentes principales
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    ipfs: IPFSConfig = field(default_factory=IPFSConfig)
    blockchain: BlockchainConfig = field(default_factory=BlockchainConfig)
    federated: FederatedConfig = field(default_factory=FederatedConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    deployment: DeploymentConfig = field(default_factory=DeploymentConfig)
    api: APIConfig = field(default_factory=APIConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    data: DataConfig = field(default_factory=DataConfig)

    # Configuraciones adicionales
    log_level: str = "INFO"
    debug_mode: bool = False
    enable_telemetry: bool = True
    telemetry_endpoint: str = ""
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    backup_retention_days: int = 30

    def __post_init__(self):
        """Validar configuración después de inicialización."""
        self._validate_config()

    def _validate_config(self):
        """Validar configuración."""
        errors = []

        # Validar URLs
        if self.api.compliance_port < 1 or self.api.compliance_port > 65535:
            errors.append("compliance_port debe estar entre 1 y 65535")

        if self.database.port < 1 or self.database.port > 65535:
            errors.append("database.port debe estar entre 1 y 65535")

        if self.redis.port < 1 or self.redis.port > 65535:
            errors.append("redis.port debe estar entre 1 y 65535")

        # Validar entornos
        valid_environments = ["development", "staging", "production"]
        if self.environment not in valid_environments:
            errors.append(f"environment debe ser uno de: {valid_environments}")

        # Validar configuración de seguridad CORS y TrustedHost
        cors_origins = self.api.get_cors_origins(self.environment)
        trusted_hosts = self.api.get_trusted_hosts(self.environment)

        if not cors_origins:
            errors.append(f"CORS origins cannot be empty for environment {self.environment}")
        elif "*" in cors_origins and self.environment in ["staging", "production"]:
            errors.append(f"CORS origins cannot contain '*' in {self.environment} environment")

        if not trusted_hosts:
            errors.append(f"Trusted hosts cannot be empty for environment {self.environment}")
        elif "*" in trusted_hosts:
            errors.append("Trusted hosts cannot contain '*' - too insecure")

        if errors:
            raise ValueError(f"Errores de configuración: {', '.join(errors)}")

    def validate_jwt_secret(self):
        """Validar JWT secret después de cargar configuración."""
        if not self.api.jwt_secret:
            raise ValueError("JWT secret is required for security")
        elif len(self.api.jwt_secret) < 32:
            raise ValueError("JWT secret must be at least 32 characters long for adequate security")

    def validate_security_config(self):
        """Validar configuración de seguridad de manera diferida."""
        # Validar JWT secret si está configurado
        if self.api.jwt_secret is not None:
            if len(self.api.jwt_secret) < 32:
                raise ValueError("JWT secret must be at least 32 characters long for adequate security")

    def ensure_secure_config(self):
        """Asegurar configuración segura obligatoria para entornos de producción."""
        errors = []

        # JWT secret es obligatorio en entornos no desarrollo
        if self.environment != "development":
            if not self.api.jwt_secret:
                errors.append("JWT_SECRET is required for security in non-development environments")
            elif len(self.api.jwt_secret) < 32:
                errors.append("JWT secret must be at least 32 characters long for adequate security")

        if errors:
            raise ValueError(f"Security configuration errors: {'; '.join(errors)}")

        logger.info("✅ Security configuration validated successfully")

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'AiloosConfig':
        """Crear configuración desde diccionario."""
        # Convertir diccionarios anidados a objetos de configuración
        if 'database' in config_dict:
            config_dict['database'] = DatabaseConfig(**config_dict['database'])
        if 'redis' in config_dict:
            config_dict['redis'] = RedisConfig(**config_dict['redis'])
        if 'ipfs' in config_dict:
            config_dict['ipfs'] = IPFSConfig(**config_dict['ipfs'])
        if 'blockchain' in config_dict:
            config_dict['blockchain'] = BlockchainConfig(**config_dict['blockchain'])
        if 'federated' in config_dict:
            config_dict['federated'] = FederatedConfig(**config_dict['federated'])
        if 'monitoring' in config_dict:
            config_dict['monitoring'] = MonitoringConfig(**config_dict['monitoring'])
        if 'deployment' in config_dict:
            config_dict['deployment'] = DeploymentConfig(**config_dict['deployment'])
        if 'api' in config_dict:
            config_dict['api'] = APIConfig(**config_dict['api'])
        if 'security' in config_dict:
            config_dict['security'] = SecurityConfig(**config_dict['security'])
        if 'notifications' in config_dict:
            config_dict['notifications'] = NotificationConfig(**config_dict['notifications'])
        if 'data' in config_dict:
            data_config = config_dict['data']
            if 'sources' in data_config and data_config['sources']:
                data_config['sources'] = [DataSourceConfig(**source) for source in data_config['sources']]
            config_dict['data'] = DataConfig(**data_config)

        return cls(**config_dict)

    @classmethod
    def from_file(cls, file_path: str) -> 'AiloosConfig':
        """Cargar configuración desde archivo."""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Archivo de configuración no encontrado: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                config_dict = yaml.safe_load(f)
            elif path.suffix.lower() == '.json':
                config_dict = json.load(f)
            else:
                raise ValueError(f"Formato de archivo no soportado: {path.suffix}")

        config = cls.from_dict(config_dict)
        config.ensure_secure_config()
        return config

    @classmethod
    async def from_env_secure(cls) -> 'AiloosConfig':
        """Crear configuración desde variables de entorno y GCP Secret Manager."""
        config = cls()

        # Get environment
        environment = os.getenv('AILOOS_ENV', 'development')

        # Try to get secret manager
        secret_manager = None
        if _secret_manager:
            secret_manager = _secret_manager
        elif _gcp_project_id:
            try:
                secret_manager = await get_secret_manager(_gcp_project_id, environment)
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize secret manager: {e}")

        # Helper function to get secret with fallback to env vars
        async def get_secret(key: str, env_fallback: str = None) -> str:
            if secret_manager:
                try:
                    secret_value = await secret_manager.get_secret(key)
                    if secret_value:
                        logger.debug(f"✅ Loaded secret from GCP: {key}")
                        return secret_value
                except Exception as e:
                    logger.warning(f"⚠️ Failed to load secret {key} from GCP: {e}")

            # Fallback to environment variables
            env_value = os.getenv(env_fallback or key)
            if env_value:
                if os.getenv('AILOOS_ENV') == 'production':
                    logger.warning(f"⚠️ Using insecure env var for {key} - migrate to GCP Secret Manager")
                else:
                    pass # Silent for dev/local or use debug log
                return env_value

            return None

        # Database configuration
        config.database.host = await get_secret('db_host', 'DB_HOST') or config.database.host
        port_str = await get_secret('db_port', 'DB_PORT')
        config.database.port = int(port_str) if port_str else config.database.port
        config.database.database = await get_secret('db_name', 'DB_NAME') or config.database.database
        config.database.user = await get_secret('db_user', 'DB_USER') or config.database.user
        config.database.password = await get_secret('db_password', 'DB_PASSWORD') or config.database.password
        config.database.ssl_mode = await get_secret('db_ssl_mode', 'DB_SSL_MODE') or config.database.ssl_mode
        config.database.ssl_min_protocol_version = await get_secret(
            'db_ssl_min_protocol_version', 'DB_SSL_MIN_PROTOCOL_VERSION'
        ) or config.database.ssl_min_protocol_version
        config.database.ssl_cert_file = await get_secret('db_ssl_cert_file', 'DB_SSL_CERT_FILE') or config.database.ssl_cert_file
        config.database.ssl_key_file = await get_secret('db_ssl_key_file', 'DB_SSL_KEY_FILE') or config.database.ssl_key_file
        config.database.ssl_ca_file = await get_secret('db_ssl_ca_file', 'DB_SSL_CA_FILE') or config.database.ssl_ca_file

        # Redis configuration
        config.redis.host = await get_secret('redis_host', 'REDIS_HOST') or config.redis.host
        port_str = await get_secret('redis_port', 'REDIS_PORT')
        config.redis.port = int(port_str) if port_str else config.redis.port
        config.redis.password = await get_secret('redis_password', 'REDIS_PASSWORD') or config.redis.password

        # Environment settings
        config.environment = os.getenv('AILOOS_ENV', config.environment)
        config.log_level = os.getenv('LOG_LEVEL', config.log_level)
        config.debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'

        # P2P and monitoring settings for development
        enable_p2p_sync = os.getenv('ENABLE_P2P_SYNC', 'true').lower() == 'true'
        enable_ipfs_alerts = os.getenv('ENABLE_IPFS_ALERTS', 'true').lower() == 'true'
        disable_health_checks = os.getenv('DISABLE_HEALTH_CHECKS', 'false').lower() == 'true'

        # API configuration
        jwt_secret = await get_secret('jwt_secret', 'JWT_SECRET')
        if jwt_secret:
            config.api.jwt_secret = jwt_secret

        # Blockchain configuration
        rpc_url = await get_secret('blockchain_rpc_url', 'BLOCKCHAIN_RPC_URL')
        if rpc_url:
            config.blockchain.rpc_url = rpc_url

        contract_addr = await get_secret('dracma_contract_address', 'DRACMA_CONTRACT_ADDRESS')
        if contract_addr:
            config.blockchain.dracma_contract_address = contract_addr

        config.ensure_secure_config()
        return config

    @classmethod
    def from_env(cls) -> 'AiloosConfig':
        """Crear configuración desde variables de entorno (síncrono para compatibilidad)."""
        # For synchronous environments, try to get from cache or create basic config
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Can't run async code, fall back to basic env loading
                logger.warning("⚠️ Async config loading not available, using basic env vars")
                return cls._from_env_basic()
            else:
                return loop.run_until_complete(cls.from_env_secure())
        except RuntimeError:
            # No event loop
            logger.warning("⚠️ No event loop available, using basic env vars")
            return cls._from_env_basic()

    @classmethod
    def _from_env_basic(cls) -> 'AiloosConfig':
        """Fallback básico para cuando async no está disponible."""
        config = cls()

        # Basic environment loading (less secure)
        config.database.host = os.getenv('DB_HOST', config.database.host)
        config.database.port = int(os.getenv('DB_PORT', config.database.port))
        config.database.database = os.getenv('DB_NAME', config.database.database)
        config.database.user = os.getenv('DB_USER', config.database.user)
        config.database.password = os.getenv('DB_PASSWORD', config.database.password)
        config.database.ssl_mode = os.getenv('DB_SSL_MODE', config.database.ssl_mode)
        config.database.ssl_min_protocol_version = os.getenv(
            'DB_SSL_MIN_PROTOCOL_VERSION',
            config.database.ssl_min_protocol_version
        )
        config.database.ssl_cert_file = os.getenv('DB_SSL_CERT_FILE', config.database.ssl_cert_file)
        config.database.ssl_key_file = os.getenv('DB_SSL_KEY_FILE', config.database.ssl_key_file)
        config.database.ssl_ca_file = os.getenv('DB_SSL_CA_FILE', config.database.ssl_ca_file)

        config.redis.host = os.getenv('REDIS_HOST', config.redis.host)
        config.redis.port = int(os.getenv('REDIS_PORT', config.redis.port))
        config.redis.password = os.getenv('REDIS_PASSWORD', config.redis.password)

        config.environment = os.getenv('AILOOS_ENV', config.environment)
        config.log_level = os.getenv('LOG_LEVEL', config.log_level)
        config.debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'

        # JWT secret
        jwt_secret = os.getenv('JWT_SECRET')
        if jwt_secret:
            config.api.jwt_secret = jwt_secret

        config.blockchain.rpc_url = os.getenv('BLOCKCHAIN_RPC_URL', config.blockchain.rpc_url)
        config.blockchain.dracma_contract_address = os.getenv('DRACMA_CONTRACT_ADDRESS', config.blockchain.dracma_contract_address)

        config.ensure_secure_config()
        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convertir configuración a diccionario."""
        return {
            'version': self.version,
            'environment': self.environment,
            'created_at': self.created_at,
            'database': self.database.__dict__,
            'redis': self.redis.__dict__,
            'ipfs': self.ipfs.__dict__,
            'blockchain': self.blockchain.__dict__,
            'federated': self.federated.__dict__,
            'monitoring': self.monitoring.__dict__,
            'deployment': self.deployment.__dict__,
            'api': self.api.__dict__,
            'security': self.security.__dict__,
            'notifications': self.notifications.__dict__,
            'data': {
                'chunk_size_mb': self.data.chunk_size_mb,
                'max_concurrent_downloads': self.data.max_concurrent_downloads,
                'download_timeout_seconds': self.data.download_timeout_seconds,
                'verification_retries': self.data.verification_retries,
                'auto_listing_enabled': self.data.auto_listing_enabled,
                'pricing_strategy': self.data.pricing_strategy,
                'min_listing_quality': self.data.min_listing_quality,
                'max_listing_size_mb': self.data.max_listing_size_mb,
                'federated_integration': self.data.federated_integration,
                'sources': [source.__dict__ for source in self.data.sources]
            },
            'log_level': self.log_level,
            'debug_mode': self.debug_mode,
            'enable_telemetry': self.enable_telemetry,
            'telemetry_endpoint': self.telemetry_endpoint,
            'backup_enabled': self.backup_enabled,
            'backup_interval_hours': self.backup_interval_hours,
            'backup_retention_days': self.backup_retention_days
        }

    def save_to_file(self, file_path: str):
        """Guardar configuración a archivo."""
        path = Path(file_path)
        config_dict = self.to_dict()

        with open(path, 'w', encoding='utf-8') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            elif path.suffix.lower() == '.json':
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            else:
                raise ValueError(f"Formato de archivo no soportado: {path.suffix}")

    def get(self, key: str, default=None):
        """
        Obtener valor de configuración por clave (compatibilidad con dict).

        Args:
            key: Clave de configuración (puede usar notación de punto para nested)
            default: Valor por defecto si no se encuentra

        Returns:
            Valor de configuración o default
        """
        try:
            # Support nested keys with dot notation
            keys = key.split('.')
            value = self

            for k in keys:
                if hasattr(value, k):
                    value = getattr(value, k)
                elif isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default

            return value
        except (AttributeError, KeyError):
            return default


# Instancia global de configuración
_config_instance: Optional[AiloosConfig] = None

# Alias para compatibilidad hacia atrás
Config = AiloosConfig


def get_config() -> AiloosConfig:
    """Obtener instancia global de configuración."""
    global _config_instance

    if _config_instance is None:
        _config_instance = _load_config()
        # Validar configuración segura al cargar para API
        _config_instance.ensure_secure_config()

    return _config_instance


def _load_config() -> AiloosConfig:
    """Cargar configuración desde múltiples fuentes."""
    # Prioridad: archivo > variables de entorno > valores por defecto

    # Intentar cargar desde archivo
    config_paths = [
        Path.cwd() / "config.yaml",
        Path.cwd() / "config.yml",
        Path.cwd() / "config.json",
        Path.home() / ".ailoos" / "config.yaml",
        Path.home() / ".ailoos" / "config.json"
    ]

    for config_path in config_paths:
        if config_path.exists():
            try:
                logger.info(f"Cargando configuración desde: {config_path}")
                return AiloosConfig.from_file(str(config_path))
            except Exception as e:
                logger.warning(f"Error cargando configuración desde {config_path}: {e}")

    # Intentar cargar desde variables de entorno
    try:
        logger.info("Cargando configuración desde variables de entorno")
        return AiloosConfig.from_env()
    except Exception as e:
        logger.warning(f"Error cargando configuración desde entorno: {e}")

    # Usar configuración por defecto
    logger.info("Usando configuración por defecto")
    return AiloosConfig()


def reload_config() -> AiloosConfig:
    """Recargar configuración."""
    global _config_instance
    _config_instance = _load_config()
    # Revalidar seguridad después de recargar
    _config_instance.ensure_secure_config()
    logger.info("Configuración recargada")
    return _config_instance


def validate_config(config: AiloosConfig) -> List[str]:
    """Validar configuración completa."""
    errors = []

    try:
        config._validate_config()
    except ValueError as e:
        errors.append(str(e))

    # Validaciones adicionales
    if config.database.connection_pool_size < 1:
        errors.append("database.connection_pool_size debe ser al menos 1")

    if config.redis.max_connections < 1:
        errors.append("redis.max_connections debe ser al menos 1")

    if config.federated.privacy_budget <= 0:
        errors.append("federated.privacy_budget debe ser mayor que 0")

    return errors


# Función de conveniencia para testing
def create_test_config() -> AiloosConfig:
    """Crear configuración para testing."""
    config = AiloosConfig()
    config.environment = "test"
    config.database.database = "ailoos_test"
    config.redis.db = 1
    config.debug_mode = True
    config.enable_telemetry = False
    return config
