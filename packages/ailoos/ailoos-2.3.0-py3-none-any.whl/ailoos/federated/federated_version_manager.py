"""
Federated Version Manager - Sistema de versionado federado completo para AILOOS
Gestión centralizada de versiones del modelo con atomicidad y consistencia.
"""

import asyncio
import hashlib
import json
import time
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import aiofiles
import os

from ..core.logging import get_logger
from ..infrastructure.ipfs_embedded import IPFSManager

logger = get_logger(__name__)


class VersionStatus(Enum):
    """Estados posibles de una versión."""
    DRAFT = "draft"
    VALIDATING = "validating"
    VALIDATED = "validated"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ROLLED_BACK = "rolled_back"


class ValidationStatus(Enum):
    """Estados de validación."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONFLICT = "conflict"


@dataclass
class ModelVersion:
    """Representa una versión del modelo en el sistema federado."""
    version_id: str
    version_name: str
    created_at: int
    description: str

    # Metadatos de federated learning
    federated_info: Dict[str, Any] = field(default_factory=dict)

    # Calidad y métricas
    quality_metrics: Dict[str, Any] = field(default_factory=dict)

    # Información de almacenamiento
    model_cid: str = ""
    metadata_cid: str = ""

    # Estado
    status: VersionStatus = VersionStatus.DRAFT
    is_active: bool = False
    deprecated_at: Optional[int] = None

    # Hashes de integridad
    model_hash: str = ""
    config_hash: str = ""

    # Validación colectiva
    validation_votes: Dict[str, ValidationStatus] = field(default_factory=dict)
    required_validations: int = 3
    validation_deadline: Optional[int] = None

    # Información de rollback
    rollback_from: Optional[str] = None
    rollback_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para serialización."""
        data = asdict(self)
        data['status'] = self.status.value
        for node_id, status in data['validation_votes'].items():
            if isinstance(status, ValidationStatus):
                data['validation_votes'][node_id] = status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelVersion':
        """Crear instancia desde diccionario."""
        data_copy = data.copy()
        data_copy['status'] = VersionStatus(data['status'])
        validation_votes = {}
        for node_id, status in data.get('validation_votes', {}).items():
            validation_votes[node_id] = ValidationStatus(status)
        data_copy['validation_votes'] = validation_votes
        return cls(**data_copy)


@dataclass
class VersionRegistry:
    """Registro completo de versiones."""
    versions: Dict[str, ModelVersion] = field(default_factory=dict)
    history: List[str] = field(default_factory=list)
    latest_version: Optional[str] = None
    last_updated: int = field(default_factory=lambda: int(time.time()))

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            'versions': {vid: v.to_dict() for vid, v in self.versions.items()},
            'history': self.history,
            'latest_version': self.latest_version,
            'last_updated': self.last_updated
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VersionRegistry':
        """Crear instancia desde diccionario."""
        versions = {}
        for vid, vdata in data.get('versions', {}).items():
            versions[vid] = ModelVersion.from_dict(vdata)
        return cls(
            versions=versions,
            history=data.get('history', []),
            latest_version=data.get('latest_version'),
            last_updated=data.get('last_updated', int(time.time()))
        )


class FederatedVersionManager:
    """
    Gestor centralizado de versiones para el sistema federado.
    Maneja registro, validación colectiva y distribución de versiones.
    """

    def __init__(self, registry_path: str, ipfs_manager: IPFSManager,
                 min_validations: int = 3, validation_timeout_hours: int = 24):
        """
        Inicializar el gestor de versiones.

        Args:
            registry_path: Ruta al archivo de registro
            ipfs_manager: Gestor de IPFS para almacenamiento
            min_validations: Validaciones mínimas requeridas
            validation_timeout_hours: Timeout para validación en horas
        """
        self.registry_path = registry_path
        self.ipfs_manager = ipfs_manager
        self.min_validations = min_validations
        self.validation_timeout_seconds = validation_timeout_hours * 3600

        # Estado en memoria
        self.registry: VersionRegistry = VersionRegistry()
        self.active_nodes: Set[str] = set()

        # Locks para atomicidad
        self.registry_lock = asyncio.Lock()
        self.validation_lock = asyncio.Lock()

        # Callbacks para eventos
        self.version_callbacks: List[callable] = []

        logger.info(f"🚀 FederatedVersionManager initialized with registry at {registry_path}")

    async def initialize(self) -> bool:
        """Inicializar el gestor cargando el registro existente."""
        try:
            await self._load_registry()
            logger.info(f"✅ Loaded version registry with {len(self.registry.versions)} versions")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize version manager: {e}")
            return False

    async def register_new_version(self, model_data: bytes, metadata: Dict[str, Any],
                                 creator_node: str) -> str:
        """
        Registrar una nueva versión del modelo.

        Args:
            model_data: Datos binarios del modelo
            metadata: Metadatos de la versión
            creator_node: Nodo que crea la versión

        Returns:
            ID de la versión creada
        """
        async with self.registry_lock:
            try:
                # Generar ID único de versión
                version_id = self._generate_version_id(metadata)

                # Calcular hashes de integridad
                model_hash = self._calculate_hash(model_data)
                config_hash = self._calculate_config_hash(metadata)

                # Almacenar en IPFS
                model_cid = await self.ipfs_manager.store_data(model_data)
                metadata_json = json.dumps(metadata, sort_keys=True)
                metadata_cid = await self.ipfs_manager.store_data(metadata_json.encode())

                # Crear entrada de versión
                version = ModelVersion(
                    version_id=version_id,
                    version_name=metadata.get('version_name', version_id),
                    created_at=int(time.time()),
                    description=metadata.get('description', ''),
                    federated_info=metadata.get('federated_info', {}),
                    quality_metrics=metadata.get('quality_metrics', {}),
                    model_cid=model_cid,
                    metadata_cid=metadata_cid,
                    model_hash=model_hash,
                    config_hash=config_hash,
                    required_validations=self.min_validations,
                    validation_deadline=int(time.time()) + self.validation_timeout_seconds
                )

                # Agregar auto-voto del creador
                version.validation_votes[creator_node] = ValidationStatus.APPROVED

                # Registrar en el sistema
                self.registry.versions[version_id] = version
                self.registry.history.append(version_id)
                self.registry.last_updated = int(time.time())

                # Iniciar proceso de validación colectiva
                version.status = VersionStatus.VALIDATING

                await self._save_registry()

                # Notificar callbacks
                await self._notify_version_event('version_registered', version_id)

                logger.info(f"✅ Registered new version {version_id} by node {creator_node}")
                return version_id

            except Exception as e:
                logger.error(f"❌ Failed to register version: {e}")
                raise

    async def submit_validation_vote(self, version_id: str, node_id: str,
                                   vote: ValidationStatus, reason: str = "") -> bool:
        """
        Enviar voto de validación para una versión.

        Args:
            version_id: ID de la versión
            node_id: ID del nodo votante
            vote: Voto de validación
            reason: Razón del voto (opcional)

        Returns:
            True si el voto fue aceptado
        """
        async with self.validation_lock:
            if version_id not in self.registry.versions:
                raise ValueError(f"Version {version_id} not found")

            version = self.registry.versions[version_id]

            # Verificar que la versión esté en validación
            if version.status != VersionStatus.VALIDATING:
                raise ValueError(f"Version {version_id} is not in validation phase")

            # Verificar deadline
            if time.time() > version.validation_deadline:
                version.status = VersionStatus.REJECTED
                await self._save_registry()
                raise ValueError(f"Validation deadline expired for version {version_id}")

            # Registrar voto
            version.validation_votes[node_id] = vote

            # Verificar si se alcanzó consenso
            await self._check_validation_consensus(version_id)

            await self._save_registry()

            logger.info(f"📝 Validation vote from {node_id} for {version_id}: {vote.value}")
            return True

    async def _check_validation_consensus(self, version_id: str):
        """Verificar si se alcanzó consenso de validación."""
        version = self.registry.versions[version_id]
        votes = version.validation_votes

        approved = sum(1 for v in votes.values() if v == ValidationStatus.APPROVED)
        rejected = sum(1 for v in votes.values() if v == ValidationStatus.REJECTED)

        total_votes = len(votes)

        # Verificar aprobación
        if approved >= version.required_validations:
            version.status = VersionStatus.VALIDATED
            await self._activate_version(version_id)
            await self._notify_version_event('version_validated', version_id)

        # Verificar rechazo (mayoría simple)
        elif rejected > total_votes // 2:
            version.status = VersionStatus.REJECTED
            await self._notify_version_event('version_rejected', version_id)

        # Verificar conflicto
        elif total_votes >= version.required_validations and approved + rejected == total_votes:
            if approved == rejected:
                version.status = VersionStatus.CONFLICT
                await self._notify_version_event('version_conflict', version_id)

    async def _activate_version(self, version_id: str):
        """Activar una versión validada."""
        version = self.registry.versions[version_id]

        # Desactivar versión anterior si existe
        if self.registry.latest_version and self.registry.latest_version != version_id:
            old_version = self.registry.versions[self.registry.latest_version]
            old_version.is_active = False
            old_version.deprecated_at = int(time.time())

        # Activar nueva versión
        version.status = VersionStatus.ACTIVE
        version.is_active = True
        self.registry.latest_version = version_id

        logger.info(f"🎯 Activated version {version_id}")

    async def get_version(self, version_id: str) -> Optional[ModelVersion]:
        """Obtener información de una versión."""
        return self.registry.versions.get(version_id)

    async def get_active_version(self) -> Optional[ModelVersion]:
        """Obtener la versión activa actual."""
        if self.registry.latest_version:
            return self.registry.versions.get(self.registry.latest_version)
        return None

    async def list_versions(self, status_filter: Optional[VersionStatus] = None) -> List[ModelVersion]:
        """Listar versiones con filtro opcional por estado."""
        versions = list(self.registry.versions.values())

        if status_filter:
            versions = [v for v in versions if v.status == status_filter]

        return sorted(versions, key=lambda v: v.created_at, reverse=True)

    async def deprecate_version(self, version_id: str, reason: str = "") -> bool:
        """Deprecar una versión."""
        async with self.registry_lock:
            if version_id not in self.registry.versions:
                return False

            version = self.registry.versions[version_id]
            version.status = VersionStatus.DEPRECATED
            version.is_active = False
            version.deprecated_at = int(time.time())

            await self._save_registry()
            await self._notify_version_event('version_deprecated', version_id)

            logger.info(f"📅 Deprecated version {version_id}: {reason}")
            return True

    def _generate_version_id(self, metadata: Dict[str, Any]) -> str:
        """Generar ID único de versión."""
        base_name = metadata.get('model_name', 'ailoos_model')
        version = metadata.get('version', '1.0.0')
        variant = metadata.get('variant', 'federated')
        timestamp = int(time.time())

        return f"{base_name}_v{version}-{variant}_{timestamp}"

    def _calculate_hash(self, data: bytes) -> str:
        """Calcular hash SHA-256 de datos."""
        return hashlib.sha256(data).hexdigest()

    def _calculate_config_hash(self, config: Dict[str, Any]) -> str:
        """Calcular hash de configuración."""
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()

    async def _load_registry(self):
        """Cargar registro desde archivo."""
        if not os.path.exists(self.registry_path):
            self.registry = VersionRegistry()
            return

        try:
            async with aiofiles.open(self.registry_path, 'r') as f:
                data = json.loads(await f.read())
            self.registry = VersionRegistry.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load registry, creating new one: {e}")
            self.registry = VersionRegistry()

    async def _save_registry(self):
        """Guardar registro a archivo."""
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)

            data = self.registry.to_dict()
            async with aiofiles.open(self.registry_path, 'w') as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))

        except Exception as e:
            logger.error(f"❌ Failed to save registry: {e}")
            raise

    async def _notify_version_event(self, event_type: str, version_id: str):
        """Notificar eventos de versión a callbacks."""
        for callback in self.version_callbacks:
            try:
                await callback(event_type, version_id)
            except Exception as e:
                logger.warning(f"Version callback failed: {e}")

    def add_version_callback(self, callback: callable):
        """Agregar callback para eventos de versión."""
        self.version_callbacks.append(callback)

    async def get_validation_status(self, version_id: str) -> Dict[str, Any]:
        """Obtener estado de validación de una versión."""
        if version_id not in self.registry.versions:
            raise ValueError(f"Version {version_id} not found")

        version = self.registry.versions[version_id]

        return {
            'version_id': version_id,
            'status': version.status.value,
            'votes': {node: status.value for node, status in version.validation_votes.items()},
            'required_validations': version.required_validations,
            'deadline': version.validation_deadline,
            'time_remaining': max(0, version.validation_deadline - int(time.time()))
        }

    async def force_activate_version(self, version_id: str, reason: str = "") -> bool:
        """Forzar activación de una versión (para emergencias)."""
        async with self.registry_lock:
            if version_id not in self.registry.versions:
                return False

            version = self.registry.versions[version_id]
            version.status = VersionStatus.ACTIVE
            version.is_active = True
            self.registry.latest_version = version_id

            await self._save_registry()
            await self._notify_version_event('version_force_activated', version_id)

            logger.warning(f"⚠️ Force activated version {version_id}: {reason}")
            return True