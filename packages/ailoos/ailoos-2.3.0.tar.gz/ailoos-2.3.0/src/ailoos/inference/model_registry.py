"""
ModelRegistry - Sistema de registro y versionado de modelos
Gestiona el ciclo de vida completo de los modelos EmpoorioLM.
"""

import asyncio
import json
import logging
import hashlib
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class ModelStatus(Enum):
    """Estados posibles de un modelo."""
    REGISTERING = "registering"
    VALIDATING = "validating"
    TRAINING = "training"
    READY = "ready"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
    FAILED = "failed"


class ModelType(Enum):
    """Tipos de modelo soportados."""
    EmpoorioLM_BASE = "empoorio_lm_base"
    EmpoorioLM_FINETUNED = "empoorio_lm_finetuned"
    EmpoorioLM_QUANTIZED = "empoorio_lm_quantized"
    EmpoorioLM_DISTILLED = "empoorio_lm_distilled"


@dataclass
class ModelMetadata:
    """Metadatos completos de un modelo."""
    model_id: str
    name: str
    version: str
    model_type: ModelType
    status: ModelStatus

    # Información de creación
    created_at: datetime
    created_by: str
    description: str = ""

    # Información técnica
    architecture: str = ""
    num_parameters: int = 0
    vocab_size: int = 0
    max_seq_length: int = 0

    # Información de entrenamiento
    training_config: Dict[str, Any] = field(default_factory=dict)
    training_dataset: str = ""
    training_metrics: Dict[str, Any] = field(default_factory=dict)

    # Información de cuantización
    quantization_config: Dict[str, Any] = field(default_factory=dict)

    # Información de deployment
    deployment_config: Dict[str, Any] = field(default_factory=dict)
    endpoint_url: Optional[str] = None

    # Información de calidad
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    validation_results: Dict[str, Any] = field(default_factory=dict)

    # Información de linaje
    parent_model_id: Optional[str] = None
    child_models: List[str] = field(default_factory=list)
    training_session_id: Optional[str] = None

    # Tags y metadata adicional
    tags: List[str] = field(default_factory=list)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para serialización."""
        return {
            'model_id': self.model_id,
            'name': self.name,
            'version': self.version,
            'model_type': self.model_type.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'description': self.description,
            'architecture': self.architecture,
            'num_parameters': self.num_parameters,
            'vocab_size': self.vocab_size,
            'max_seq_length': self.max_seq_length,
            'training_config': self.training_config,
            'training_dataset': self.training_dataset,
            'training_metrics': self.training_metrics,
            'quantization_config': self.quantization_config,
            'deployment_config': self.deployment_config,
            'endpoint_url': self.endpoint_url,
            'quality_metrics': self.quality_metrics,
            'validation_results': self.validation_results,
            'parent_model_id': self.parent_model_id,
            'child_models': self.child_models,
            'training_session_id': self.training_session_id,
            'tags': self.tags,
            'custom_metadata': self.custom_metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelMetadata':
        """Crear instancia desde diccionario."""
        data_copy = data.copy()
        data_copy['model_type'] = ModelType(data['model_type'])
        data_copy['status'] = ModelStatus(data['status'])
        data_copy['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data_copy)


@dataclass
class ModelVersion:
    """Información de versión específica de modelo."""
    version_id: str
    model_id: str
    version_number: str
    created_at: datetime
    file_path: str
    file_size: int
    checksum: str
    is_active: bool = False

    # Información de compatibilidad
    compatible_versions: List[str] = field(default_factory=list)
    breaking_changes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'version_id': self.version_id,
            'model_id': self.model_id,
            'version_number': self.version_number,
            'created_at': self.created_at.isoformat(),
            'file_path': self.file_path,
            'file_size': self.file_size,
            'checksum': self.checksum,
            'is_active': self.is_active,
            'compatible_versions': self.compatible_versions,
            'breaking_changes': self.breaking_changes
        }


class ModelRegistry:
    """
    Registro centralizado de modelos EmpoorioLM.

    Características:
    - Versionado automático de modelos
    - Linaje y dependencias entre modelos
    - Validación de calidad automática
    - Gestión de ciclo de vida completo
    - Búsqueda y discovery de modelos
    """

    def __init__(self, registry_path: str = "./model_registry"):
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)

        # Archivos de almacenamiento
        self.models_file = self.registry_path / "models.json"
        self.versions_file = self.registry_path / "versions.json"

        # Estado en memoria
        self.models: Dict[str, ModelMetadata] = {}
        self.versions: Dict[str, List[ModelVersion]] = {}
        self.active_models: Dict[str, str] = {}  # name -> model_id

        # Locks para thread safety
        self._lock = asyncio.Lock()

        logger.info(f"📚 ModelRegistry inicializado en {registry_path}")

    async def register_model(
        self,
        name: str,
        model_type: ModelType,
        created_by: str,
        description: str = "",
        training_config: Dict[str, Any] = None,
        training_session_id: Optional[str] = None,
        parent_model_id: Optional[str] = None,
        tags: List[str] = None
    ) -> str:
        """
        Registrar un nuevo modelo.

        Args:
            name: Nombre del modelo
            model_type: Tipo de modelo
            created_by: Usuario que crea el modelo
            description: Descripción del modelo
            training_config: Configuración de entrenamiento
            training_session_id: ID de sesión de entrenamiento
            parent_model_id: ID del modelo padre
            tags: Tags del modelo

        Returns:
            ID del modelo registrado
        """
        async with self._lock:
            # Generar ID único
            model_id = f"model_{uuid.uuid4().hex[:16]}"

            # Crear metadatos
            metadata = ModelMetadata(
                model_id=model_id,
                name=name,
                version="1.0.0",
                model_type=model_type,
                status=ModelStatus.REGISTERING,
                created_at=datetime.now(),
                created_by=created_by,
                description=description,
                training_config=training_config or {},
                training_session_id=training_session_id,
                parent_model_id=parent_model_id,
                tags=tags or []
            )

            # Actualizar linaje si hay modelo padre
            if parent_model_id and parent_model_id in self.models:
                parent_model = self.models[parent_model_id]
                parent_model.child_models.append(model_id)

            # Registrar modelo
            self.models[model_id] = metadata
            self.versions[model_id] = []

            # Marcar como activo si es el primero con este nombre
            if name not in self.active_models:
                self.active_models[name] = model_id

            await self._save_registry()
            logger.info(f"📝 Modelo {name} registrado con ID {model_id}")

            return model_id

    async def update_model_status(self, model_id: str, status: ModelStatus) -> bool:
        """Actualizar estado de un modelo."""
        async with self._lock:
            if model_id not in self.models:
                return False

            self.models[model_id].status = status
            await self._save_registry()

            logger.info(f"📊 Estado de modelo {model_id} actualizado a {status.value}")
            return True

    async def add_model_version(
        self,
        model_id: str,
        version_number: str,
        file_path: str,
        created_by: str,
        compatible_versions: List[str] = None,
        breaking_changes: List[str] = None
    ) -> str:
        """
        Agregar nueva versión a un modelo.

        Args:
            model_id: ID del modelo
            version_number: Número de versión (semver)
            file_path: Ruta del archivo del modelo
            created_by: Usuario que crea la versión
            compatible_versions: Versiones compatibles
            breaking_changes: Cambios que rompen compatibilidad

        Returns:
            ID de la versión creada
        """
        async with self._lock:
            if model_id not in self.models:
                raise ValueError(f"Modelo {model_id} no encontrado")

            # Generar ID único para versión
            version_id = f"ver_{uuid.uuid4().hex[:16]}"

            # Calcular checksum del archivo
            checksum = await self._calculate_file_checksum(file_path)

            # Obtener tamaño del archivo
            file_size = Path(file_path).stat().st_size

            # Crear versión
            version = ModelVersion(
                version_id=version_id,
                model_id=model_id,
                version_number=version_number,
                created_at=datetime.now(),
                file_path=file_path,
                file_size=file_size,
                checksum=checksum,
                compatible_versions=compatible_versions or [],
                breaking_changes=breaking_changes or []
            )

            # Agregar a versiones del modelo
            if model_id not in self.versions:
                self.versions[model_id] = []
            self.versions[model_id].append(version)

            # Actualizar versión del modelo
            self.models[model_id].version = version_number

            await self._save_registry()
            logger.info(f"🏷️ Versión {version_number} agregada al modelo {model_id}")

            return version_id

    async def set_active_version(self, model_id: str, version_id: str) -> bool:
        """Establecer versión activa de un modelo."""
        async with self._lock:
            if model_id not in self.models:
                return False

            if model_id not in self.versions:
                return False

            # Desactivar versiones anteriores
            for version in self.versions[model_id]:
                version.is_active = False

            # Activar nueva versión
            for version in self.versions[model_id]:
                if version.version_id == version_id:
                    version.is_active = True
                    self.models[model_id].version = version.version_number
                    break

            await self._save_registry()
            logger.info(f"✅ Versión {version_id} activada para modelo {model_id}")

            return True

    async def update_model_metrics(
        self,
        model_id: str,
        quality_metrics: Dict[str, Any] = None,
        validation_results: Dict[str, Any] = None,
        training_metrics: Dict[str, Any] = None
    ) -> bool:
        """Actualizar métricas de un modelo."""
        async with self._lock:
            if model_id not in self.models:
                return False

            model = self.models[model_id]
            if quality_metrics:
                model.quality_metrics.update(quality_metrics)
            if validation_results:
                model.validation_results.update(validation_results)
            if training_metrics:
                model.training_metrics.update(training_metrics)

            await self._save_registry()
            return True

    async def get_model(self, model_id: str) -> Optional[ModelMetadata]:
        """Obtener información de un modelo."""
        async with self._lock:
            return self.models.get(model_id)

    async def get_model_by_name(self, name: str) -> Optional[ModelMetadata]:
        """Obtener modelo por nombre."""
        async with self._lock:
            model_id = self.active_models.get(name)
            if model_id:
                return self.models.get(model_id)
            return None

    async def list_models(
        self,
        model_type: Optional[ModelType] = None,
        status: Optional[ModelStatus] = None,
        tags: List[str] = None
    ) -> List[ModelMetadata]:
        """Listar modelos con filtros."""
        async with self._lock:
            models = list(self.models.values())

            if model_type:
                models = [m for m in models if m.model_type == model_type]

            if status:
                models = [m for m in models if m.status == status]

            if tags:
                models = [m for m in models if any(tag in m.tags for tag in tags)]

            return models

    async def get_model_versions(self, model_id: str) -> List[ModelVersion]:
        """Obtener versiones de un modelo."""
        async with self._lock:
            return self.versions.get(model_id, [])

    async def get_active_version(self, model_id: str) -> Optional[ModelVersion]:
        """Obtener versión activa de un modelo."""
        async with self._lock:
            versions = self.versions.get(model_id, [])
            for version in versions:
                if version.is_active:
                    return version
            return None

    async def search_models(self, query: str) -> List[ModelMetadata]:
        """Buscar modelos por texto."""
        async with self._lock:
            query_lower = query.lower()
            results = []

            for model in self.models.values():
                if (query_lower in model.name.lower() or
                    query_lower in model.description.lower() or
                    any(query_lower in tag.lower() for tag in model.tags)):
                    results.append(model)

            return results

    async def get_model_lineage(self, model_id: str) -> Dict[str, Any]:
        """Obtener linaje completo de un modelo."""
        async with self._lock:
            if model_id not in self.models:
                return {}

            model = self.models[model_id]

            # Construir árbol de linaje
            lineage = {
                'model': model.to_dict(),
                'ancestors': [],
                'descendants': []
            }

            # Ancestros
            current_id = model.parent_model_id
            while current_id:
                if current_id in self.models:
                    ancestor = self.models[current_id]
                    lineage['ancestors'].append(ancestor.to_dict())
                    current_id = ancestor.parent_model_id
                else:
                    break

            # Descendientes
            def get_descendants(model_id: str) -> List[Dict[str, Any]]:
                descendants = []
                if model_id in self.models:
                    for child_id in self.models[model_id].child_models:
                        if child_id in self.models:
                            child = self.models[child_id]
                            child_info = child.to_dict()
                            child_info['descendants'] = get_descendants(child_id)
                            descendants.append(child_info)
                return descendants

            lineage['descendants'] = get_descendants(model_id)

            return lineage

    async def archive_model(self, model_id: str) -> bool:
        """Archivar un modelo."""
        async with self._lock:
            if model_id not in self.models:
                return False

            self.models[model_id].status = ModelStatus.ARCHIVED
            await self._save_registry()

            logger.info(f"📦 Modelo {model_id} archivado")
            return True

    async def delete_model(self, model_id: str) -> bool:
        """Eliminar un modelo completamente."""
        async with self._lock:
            if model_id not in self.models:
                return False

            # Verificar que no tenga hijos activos
            model = self.models[model_id]
            for child_id in model.child_models:
                if child_id in self.models and self.models[child_id].status != ModelStatus.ARCHIVED:
                    logger.warning(f"❌ No se puede eliminar modelo con hijos activos: {child_id}")
                    return False

            # Eliminar referencias
            if model.parent_model_id and model.parent_model_id in self.models:
                parent = self.models[model.parent_model_id]
                if model_id in parent.child_models:
                    parent.child_models.remove(model_id)

            # Remover de modelos activos
            if model.name in self.active_models and self.active_models[model.name] == model_id:
                del self.active_models[model.name]

            # Eliminar modelo y versiones
            del self.models[model_id]
            if model_id in self.versions:
                del self.versions[model_id]

            await self._save_registry()
            logger.info(f"🗑️ Modelo {model_id} eliminado")

            return True

    async def _calculate_file_checksum(self, file_path: str) -> str:
        """Calcular checksum SHA256 de un archivo."""
        def calculate():
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, calculate)

    async def _save_registry(self) -> None:
        """Guardar registro en disco."""
        registry_data = {
            'models': {mid: model.to_dict() for mid, model in self.models.items()},
            'versions': {
                mid: [v.to_dict() for v in versions]
                for mid, versions in self.versions.items()
            },
            'active_models': self.active_models,
            'last_updated': datetime.now().isoformat()
        }

        def save():
            with open(self.models_file, 'w', encoding='utf-8') as f:
                json.dump(registry_data, f, indent=2, ensure_ascii=False)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, save)

    async def load_registry(self) -> None:
        """Cargar registro desde disco."""
        async with self._lock:
            if not self.models_file.exists():
                logger.info("📝 No existe registro previo")
                return

            def load():
                with open(self.models_file, 'r', encoding='utf-8') as f:
                    return json.load(f)

            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, load)

            # Restaurar modelos
            self.models = {}
            for mid, model_data in data.get('models', {}).items():
                self.models[mid] = ModelMetadata.from_dict(model_data)

            # Restaurar versiones
            self.versions = {}
            for mid, versions_data in data.get('versions', {}).items():
                parsed_versions = []
                for v in versions_data:
                    v_data = v.copy()
                    created_at = v_data.get("created_at")
                    if isinstance(created_at, str):
                        try:
                            v_data["created_at"] = datetime.fromisoformat(created_at)
                        except ValueError:
                            v_data["created_at"] = datetime.utcnow()
                    parsed_versions.append(ModelVersion(**v_data))
                self.versions[mid] = parsed_versions

            self.active_models = data.get('active_models', {})

            logger.info(f"📚 Registro cargado: {len(self.models)} modelos")

    async def get_registry_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del registro."""
        async with self._lock:
            total_models = len(self.models)
            total_versions = sum(len(versions) for versions in self.versions.values())

            status_counts = {}
            type_counts = {}

            for model in self.models.values():
                status_counts[model.status.value] = status_counts.get(model.status.value, 0) + 1
                type_counts[model.model_type.value] = type_counts.get(model.model_type.value, 0) + 1

            return {
                'total_models': total_models,
                'total_versions': total_versions,
                'status_distribution': status_counts,
                'type_distribution': type_counts,
                'active_models': len(self.active_models),
                'registry_path': str(self.registry_path)
            }
