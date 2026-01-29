"""
Storage Layer para el grafo de conocimiento de AILOOS.
Implementa múltiples backends de almacenamiento con soporte para configuración, failover y métricas.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum
import hashlib

from ...core.logging import get_logger
from ...auditing.audit_manager import get_audit_manager, AuditEventType
from ...auditing.metrics_collector import get_metrics_collector

if TYPE_CHECKING:
    from ..core import Triple

logger = get_logger(__name__)


class StorageBackendType(Enum):
    """Tipos de backend de almacenamiento soportados."""
    MEMORY = "memory"
    NEO4J = "neo4j"
    RDF = "rdf"
    REDIS = "redis"


@dataclass
class StorageConfig:
    """Configuración para backends de almacenamiento."""
    backend_type: StorageBackendType
    connection_params: Dict[str, Any] = field(default_factory=dict)
    failover_enabled: bool = True
    failover_backends: List[StorageBackendType] = field(default_factory=list)
    metrics_enabled: bool = True
    audit_enabled: bool = True
    timeout_seconds: float = 30.0
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0


@dataclass
class StorageMetrics:
    """Métricas de almacenamiento."""
    backend_type: str
    operation: str
    duration_ms: float
    success: bool
    error_message: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


class StorageBackend(ABC):
    """
    Interfaz base para backends de almacenamiento del grafo de conocimiento.
    Define operaciones CRUD abstractas con soporte para métricas y auditoría.
    """

    def __init__(self, config: StorageConfig):
        self.config = config
        self.audit_manager = get_audit_manager() if config.audit_enabled else None
        self.metrics_collector = get_metrics_collector() if config.metrics_enabled else None
        self._operation_count = 0
        self._error_count = 0
        self._last_health_check = time.time()

    @abstractmethod
    async def add_triple(self, triple: 'Triple') -> bool:
        """Agregar un triple al almacenamiento."""
        pass

    @abstractmethod
    async def remove_triple(self, triple: 'Triple') -> bool:
        """Remover un triple del almacenamiento."""
        pass

    @abstractmethod
    async def query(self, query: str, **kwargs) -> List['Triple']:
        """Ejecutar una consulta en el almacenamiento."""
        pass

    @abstractmethod
    async def get_all_triples(self) -> List['Triple']:
        """Obtener todos los triples del almacenamiento."""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """Limpiar todos los triples del almacenamiento."""
        pass

    @abstractmethod
    async def close(self):
        """Cerrar conexiones del backend."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Verificar salud del backend."""
        pass

    async def _execute_with_metrics(self, operation: str, func, *args, **kwargs):
        """Ejecutar operación con métricas y auditoría."""
        start_time = time.time()
        success = False
        error_message = None

        try:
            self._operation_count += 1
            result = await func(*args, **kwargs)
            success = True
            return result

        except Exception as e:
            self._error_count += 1
            error_message = str(e)
            raise

        finally:
            duration_ms = (time.time() - start_time) * 1000

            # Registrar métricas
            if self.metrics_collector:
                self.metrics_collector.record_response_time(duration_ms)
                if not success:
                    self.metrics_collector.record_error(f"storage.{operation}", "storage_error")

            # Registrar auditoría
            if self.audit_manager:
                await self.audit_manager.log_event(
                    event_type=AuditEventType.DATA_ACCESS,
                    resource="knowledge_graph_storage",
                    action=operation,
                    details={
                        "backend_type": self.config.backend_type.value,
                        "duration_ms": duration_ms,
                        "success": success,
                        "error": error_message
                    },
                    success=success,
                    processing_time_ms=duration_ms
                )

            # Log estructurado
            if success:
                logger.info(f"Storage operation completed: {operation}",
                          backend=self.config.backend_type.value,
                          duration_ms=duration_ms)
            else:
                logger.error(f"Storage operation failed: {operation}",
                           backend=self.config.backend_type.value,
                           error=error_message,
                           duration_ms=duration_ms)

    def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del backend."""
        return {
            "backend_type": self.config.backend_type.value,
            "operation_count": self._operation_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(self._operation_count, 1),
            "last_health_check": self._last_health_check
        }


class StorageManager:
    """
    Gestor de almacenamiento con soporte para múltiples backends y failover.
    """

    def __init__(self, primary_config: StorageConfig):
        self.primary_config = primary_config
        self.primary_backend: Optional[StorageBackend] = None
        self.failover_backends: List[StorageBackend] = []
        self.current_backend: Optional[StorageBackend] = None
        self.failover_mode = False

        # Inicializar backends
        self._initialize_backends()

    def _initialize_backends(self):
        """Inicializar backends primarios y de failover."""
        try:
            # Backend primario
            self.primary_backend = self._create_backend(self.primary_config)
            self.current_backend = self.primary_backend

            # Backends de failover
            for backend_type in self.primary_config.failover_backends:
                failover_config = StorageConfig(
                    backend_type=backend_type,
                    failover_enabled=False,  # Evitar recursión
                    metrics_enabled=self.primary_config.metrics_enabled,
                    audit_enabled=self.primary_config.audit_enabled
                )
                backend = self._create_backend(failover_config)
                self.failover_backends.append(backend)

            logger.info(f"Initialized storage manager with {len(self.failover_backends)} failover backends")

        except Exception as e:
            logger.error(f"Failed to initialize storage backends: {e}")
            raise

    def _create_backend(self, config: StorageConfig) -> StorageBackend:
        """Crear instancia de backend según tipo."""
        if config.backend_type == StorageBackendType.MEMORY:
            from .memory_backend import MemoryBackend
            return MemoryBackend(config)
        elif config.backend_type == StorageBackendType.NEO4J:
            from .neo4j_backend import Neo4jBackend
            return Neo4jBackend(config)
        elif config.backend_type == StorageBackendType.RDF:
            from .rdf_backend import RDFBackend
            return RDFBackend(config)
        elif config.backend_type == StorageBackendType.REDIS:
            from .redis_backend import RedisBackend
            return RedisBackend(config)
        else:
            raise ValueError(f"Unsupported backend type: {config.backend_type}")

    async def _execute_with_failover(self, operation: str, *args, **kwargs):
        """Ejecutar operación con failover automático."""
        if not self.primary_config.failover_enabled:
            return await getattr(self.current_backend, operation)(*args, **kwargs)

        # Intentar con backend actual
        try:
            return await getattr(self.current_backend, operation)(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Primary backend failed for {operation}, attempting failover: {e}")

            # Intentar failover
            for backend in [self.primary_backend] + self.failover_backends:
                if backend == self.current_backend:
                    continue

                try:
                    # Verificar salud del backend candidato
                    if await backend.health_check():
                        logger.info(f"Switching to failover backend: {backend.config.backend_type.value}")
                        self.current_backend = backend
                        self.failover_mode = (backend != self.primary_backend)
                        return await getattr(backend, operation)(*args, **kwargs)
                except Exception as failover_e:
                    logger.error(f"Failover backend also failed: {failover_e}")
                    continue

            # Si todos fallan, relanzar error original
            raise e

    # Delegar operaciones al backend actual con failover
    async def add_triple(self, triple: 'Triple') -> bool:
        return await self._execute_with_failover('add_triple', triple)

    async def remove_triple(self, triple: 'Triple') -> bool:
        return await self._execute_with_failover('remove_triple', triple)

    async def query(self, query: str, **kwargs) -> List['Triple']:
        return await self._execute_with_failover('query', query, **kwargs)

    async def get_all_triples(self) -> List['Triple']:
        return await self._execute_with_failover('get_all_triples')

    async def clear(self) -> bool:
        return await self._execute_with_failover('clear')

    async def close(self):
        """Cerrar todos los backends."""
        backends = [self.primary_backend] + self.failover_backends
        for backend in backends:
            if backend:
                try:
                    await backend.close()
                except Exception as e:
                    logger.error(f"Error closing backend {backend.config.backend_type.value}: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Verificar salud de todos los backends."""
        health_status = {
            "primary": await self._check_backend_health(self.primary_backend),
            "failover": [await self._check_backend_health(b) for b in self.failover_backends],
            "current_backend": self.current_backend.config.backend_type.value if self.current_backend else None,
            "failover_mode": self.failover_mode
        }

        # Determinar estado general
        all_healthy = all(h["healthy"] for h in health_status["failover"]) and health_status["primary"]["healthy"]
        health_status["overall_healthy"] = all_healthy

        return health_status

    async def _check_backend_health(self, backend: StorageBackend) -> Dict[str, Any]:
        """Verificar salud de un backend específico."""
        try:
            healthy = await backend.health_check()
            return {
                "type": backend.config.backend_type.value,
                "healthy": healthy,
                "metrics": backend.get_metrics()
            }
        except Exception as e:
            return {
                "type": backend.config.backend_type.value,
                "healthy": False,
                "error": str(e)
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas de todos los backends."""
        return {
            "primary": self.primary_backend.get_metrics() if self.primary_backend else None,
            "failover": [b.get_metrics() for b in self.failover_backends],
            "current_backend": self.current_backend.config.backend_type.value if self.current_backend else None,
            "failover_mode": self.failover_mode
        }


# Instancia global del gestor de almacenamiento
_storage_manager = None

def get_storage_manager(config: Optional[StorageConfig] = None) -> StorageManager:
    """Obtener instancia global del gestor de almacenamiento."""
    global _storage_manager
    if _storage_manager is None:
        if config is None:
            # Configuración por defecto
            config = StorageConfig(backend_type=StorageBackendType.MEMORY)
        _storage_manager = StorageManager(config)
    return _storage_manager