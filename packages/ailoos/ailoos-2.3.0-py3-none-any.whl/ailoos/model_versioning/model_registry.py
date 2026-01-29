from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import json
import uuid
from pathlib import Path
from .semantic_versioning import SemanticVersion
from .version_manager import VersionManager


@dataclass
class ModelEntry:
    """Entrada completa de un modelo en el registro."""
    model_id: str
    name: str
    description: str
    created_at: datetime
    created_by: str
    tags: Set[str] = field(default_factory=set)

    # Metadatos técnicos
    architecture: str = ""
    framework: str = ""
    num_parameters: int = 0
    input_shape: Optional[List[int]] = None
    output_shape: Optional[List[int]] = None

    # Información de calidad
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    validation_results: Dict[str, Any] = field(default_factory=dict)

    # Linaje
    parent_models: List[str] = field(default_factory=list)
    child_models: List[str] = field(default_factory=list)

    # Versionado
    current_version: Optional[SemanticVersion] = None
    version_manager: Optional[VersionManager] = None

    # Metadata adicional
    custom_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para serialización."""
        return {
            'model_id': self.model_id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'tags': list(self.tags),
            'architecture': self.architecture,
            'framework': self.framework,
            'num_parameters': self.num_parameters,
            'input_shape': self.input_shape,
            'output_shape': self.output_shape,
            'quality_metrics': self.quality_metrics,
            'validation_results': self.validation_results,
            'parent_models': self.parent_models,
            'child_models': self.child_models,
            'current_version': str(self.current_version) if self.current_version else None,
            'custom_metadata': self.custom_metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelEntry':
        """Crear instancia desde diccionario."""
        data_copy = data.copy()
        data_copy['created_at'] = datetime.fromisoformat(data['created_at'])
        data_copy['tags'] = set(data.get('tags', []))
        if data.get('current_version'):
            data_copy['current_version'] = SemanticVersion(data['current_version'])
        else:
            data_copy['current_version'] = None
        data_copy['version_manager'] = None  # No serializamos el manager
        return cls(**data_copy)


class ModelRegistry:
    """
    Registro avanzado de modelos con metadatos completos y versionado.
    Gestiona el ciclo de vida de modelos con información detallada.
    """

    def __init__(self, storage_path: str = "./model_registry_advanced"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.registry_file = self.storage_path / "registry.json"
        self.models: Dict[str, ModelEntry] = {}
        self.name_to_id: Dict[str, str] = {}  # name -> model_id

        self._load_registry()

    def register_model(self,
                      name: str,
                      description: str,
                      created_by: str,
                      architecture: str = "",
                      framework: str = "",
                      tags: Optional[List[str]] = None,
                      parent_models: Optional[List[str]] = None,
                      custom_metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Registrar un nuevo modelo.

        Args:
            name: Nombre único del modelo
            description: Descripción del modelo
            created_by: Usuario que registra el modelo
            architecture: Arquitectura del modelo
            framework: Framework usado
            tags: Tags para categorización
            parent_models: IDs de modelos padre
            custom_metadata: Metadata adicional

        Returns:
            ID del modelo registrado
        """
        if name in self.name_to_id:
            raise ValueError(f"Modelo con nombre '{name}' ya existe")

        model_id = f"model_{uuid.uuid4().hex[:16]}"

        # Crear entrada del modelo
        entry = ModelEntry(
            model_id=model_id,
            name=name,
            description=description,
            created_at=datetime.now(),
            created_by=created_by,
            architecture=architecture,
            framework=framework,
            tags=set(tags or []),
            parent_models=parent_models or [],
            custom_metadata=custom_metadata or {}
        )

        # Inicializar version manager
        entry.version_manager = VersionManager()

        # Actualizar referencias de linaje
        for parent_id in entry.parent_models:
            if parent_id in self.models:
                self.models[parent_id].child_models.append(model_id)

        # Registrar
        self.models[model_id] = entry
        self.name_to_id[name] = model_id

        self._save_registry()
        return model_id

    def add_model_version(self,
                         model_id: str,
                         model_data: Dict[str, Any],
                         metadata: Dict[str, Any],
                         increment_type: str = "patch",
                         commit_message: str = "") -> SemanticVersion:
        """
        Agregar nueva versión a un modelo existente.

        Args:
            model_id: ID del modelo
            model_data: Datos del modelo
            metadata: Metadatos de la versión
            increment_type: Tipo de incremento de versión
            commit_message: Mensaje del commit

        Returns:
            Nueva versión creada
        """
        if model_id not in self.models:
            raise ValueError(f"Modelo {model_id} no encontrado")

        entry = self.models[model_id]
        if not entry.version_manager:
            entry.version_manager = VersionManager()

        # Crear nueva versión
        new_version = entry.version_manager.create_version(
            model_data=model_data,
            metadata=metadata,
            commit_message=commit_message,
            increment_type=increment_type
        )

        # Actualizar versión actual
        entry.current_version = new_version

        # Actualizar métricas si están en metadata
        if 'quality_metrics' in metadata:
            entry.quality_metrics.update(metadata['quality_metrics'])
        if 'validation_results' in metadata:
            entry.validation_results.update(metadata['validation_results'])

        self._save_registry()
        return new_version

    def get_model(self, model_id: str) -> Optional[ModelEntry]:
        """Obtener información de un modelo por ID."""
        return self.models.get(model_id)

    def get_model_by_name(self, name: str) -> Optional[ModelEntry]:
        """Obtener información de un modelo por nombre."""
        model_id = self.name_to_id.get(name)
        if model_id:
            return self.models.get(model_id)
        return None

    def update_model_metadata(self,
                             model_id: str,
                             quality_metrics: Optional[Dict[str, float]] = None,
                             validation_results: Optional[Dict[str, Any]] = None,
                             custom_metadata: Optional[Dict[str, Any]] = None,
                             tags: Optional[List[str]] = None) -> bool:
        """
        Actualizar metadatos de un modelo.

        Returns:
            True si se actualizó correctamente
        """
        if model_id not in self.models:
            return False

        entry = self.models[model_id]

        if quality_metrics:
            entry.quality_metrics.update(quality_metrics)
        if validation_results:
            entry.validation_results.update(validation_results)
        if custom_metadata:
            entry.custom_metadata.update(custom_metadata)
        if tags:
            entry.tags.update(tags)

        self._save_registry()
        return True

    def list_models(self,
                   tags: Optional[List[str]] = None,
                   architecture: Optional[str] = None,
                   framework: Optional[str] = None,
                   created_by: Optional[str] = None) -> List[ModelEntry]:
        """
        Listar modelos con filtros.

        Args:
            tags: Filtrar por tags (debe tener al menos uno)
            architecture: Filtrar por arquitectura
            framework: Filtrar por framework
            created_by: Filtrar por creador

        Returns:
            Lista de modelos que coinciden con los filtros
        """
        models = list(self.models.values())

        if tags:
            models = [m for m in models if any(tag in m.tags for tag in tags)]

        if architecture:
            models = [m for m in models if m.architecture == architecture]

        if framework:
            models = [m for m in models if m.framework == framework]

        if created_by:
            models = [m for m in models if m.created_by == created_by]

        return models

    def search_models(self, query: str) -> List[ModelEntry]:
        """
        Buscar modelos por texto en nombre, descripción o tags.

        Args:
            query: Texto de búsqueda

        Returns:
            Lista de modelos que coinciden
        """
        query_lower = query.lower()
        results = []

        for model in self.models.values():
            if (query_lower in model.name.lower() or
                query_lower in model.description.lower() or
                any(query_lower in tag.lower() for tag in model.tags)):
                results.append(model)

        return results

    def get_model_lineage(self, model_id: str) -> Dict[str, Any]:
        """
        Obtener linaje completo de un modelo.

        Returns:
            Diccionario con ancestros y descendientes
        """
        if model_id not in self.models:
            return {}

        entry = self.models[model_id]

        lineage = {
            'model': entry.to_dict(),
            'ancestors': [],
            'descendants': []
        }

        # Ancestros
        for parent_id in entry.parent_models:
            if parent_id in self.models:
                parent = self.models[parent_id]
                lineage['ancestors'].append(parent.to_dict())

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

    def get_model_versions(self, model_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Obtener historial de versiones de un modelo.

        Args:
            model_id: ID del modelo
            limit: Número máximo de versiones a retornar

        Returns:
            Lista de versiones en orden cronológico inverso
        """
        if model_id not in self.models:
            return []

        entry = self.models[model_id]
        if not entry.version_manager:
            return []

        versions = entry.version_manager.get_version_history(limit=limit)
        return [self._version_entry_to_dict(v) for v in versions]

    def rollback_model(self, model_id: str, target_version: SemanticVersion, create_new: bool = True) -> Optional[SemanticVersion]:
        """
        Hacer rollback de un modelo a una versión anterior.

        Args:
            model_id: ID del modelo
            target_version: Versión a la que hacer rollback
            create_new: Si crear nueva versión o solo cambiar head

        Returns:
            Nueva versión resultante o None si falla
        """
        if model_id not in self.models:
            return None

        entry = self.models[model_id]
        if not entry.version_manager:
            return None

        new_version = entry.version_manager.rollback_to_version(target_version, create_new)
        if new_version:
            entry.current_version = new_version

        self._save_registry()
        return new_version

    def delete_model(self, model_id: str) -> bool:
        """
        Eliminar un modelo del registro.

        Returns:
            True si se eliminó correctamente
        """
        if model_id not in self.models:
            return False

        entry = self.models[model_id]

        # Remover referencias de linaje
        for parent_id in entry.parent_models:
            if parent_id in self.models:
                parent = self.models[parent_id]
                if model_id in parent.child_models:
                    parent.child_models.remove(model_id)

        for child_id in entry.child_models:
            if child_id in self.models:
                child = self.models[child_id]
                if model_id in child.parent_models:
                    child.parent_models.remove(model_id)

        # Remover del registro
        name = entry.name
        del self.models[model_id]
        if name in self.name_to_id:
            del self.name_to_id[name]

        self._save_registry()
        return True

    def get_registry_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del registro."""
        total_models = len(self.models)
        total_versions = sum(len(self.get_model_versions(mid)) for mid in self.models.keys())

        architectures = {}
        frameworks = {}
        creators = {}

        for model in self.models.values():
            arch = model.architecture or "unknown"
            fw = model.framework or "unknown"
            creator = model.created_by

            architectures[arch] = architectures.get(arch, 0) + 1
            frameworks[fw] = frameworks.get(fw, 0) + 1
            creators[creator] = creators.get(creator, 0) + 1

        return {
            'total_models': total_models,
            'total_versions': total_versions,
            'architectures': architectures,
            'frameworks': frameworks,
            'creators': creators,
            'storage_path': str(self.storage_path)
        }

    def _version_entry_to_dict(self, version_entry) -> Dict[str, Any]:
        """Convertir VersionEntry a diccionario."""
        return {
            'version': str(version_entry.version),
            'created_at': version_entry.created_at.isoformat(),
            'branch': version_entry.branch,
            'commit_message': version_entry.commit_message,
            'tags': list(version_entry.tags),
            'metadata': version_entry.metadata
        }

    def _save_registry(self):
        """Guardar registro en disco."""
        registry_data = {
            'models': {mid: model.to_dict() for mid, model in self.models.items()},
            'name_to_id': self.name_to_id,
            'last_updated': datetime.now().isoformat()
        }

        with open(self.registry_file, 'w', encoding='utf-8') as f:
            json.dump(registry_data, f, indent=2, ensure_ascii=False)

    def _load_registry(self):
        """Cargar registro desde disco."""
        if not self.registry_file.exists():
            return

        with open(self.registry_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.models = {}
        for mid, model_data in data.get('models', {}).items():
            self.models[mid] = ModelEntry.from_dict(model_data)

        self.name_to_id = data.get('name_to_id', {})