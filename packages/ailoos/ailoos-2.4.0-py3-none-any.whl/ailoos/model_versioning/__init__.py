"""
ModelVersioningAdvanced - Sistema avanzado de versionado de modelos para FASE 9.

Este módulo proporciona un sistema completo de versionado semántico, comparación de modelos,
gestión de versiones con rollback y branching, registro de modelos con metadatos avanzados,
historial completo de cambios y seguimiento de linaje y dependencias.

Componentes principales:
- SemanticVersioning: Versionado semántico completo (MAJOR.MINOR.PATCH)
- ModelComparator: Comparación avanzada entre versiones de modelos
- VersionManager: Gestor de versiones con rollback y branching
- ModelRegistry: Registro de modelos con metadatos avanzados
- VersionHistory: Historial completo de cambios y evoluciones
- ModelLineage: Seguimiento de linaje y dependencias de modelos
"""

from .semantic_versioning import SemanticVersion
from .model_comparator import ModelComparator, ComparisonResult
from .version_manager import VersionManager, VersionEntry, Branch
from .model_registry import ModelRegistry, ModelEntry
from .version_history import VersionHistory, ChangeRecord, EvolutionMetrics
from .model_lineage import ModelLineage, LineageNode, LineageEdge, LineagePath

__all__ = [
    # Semantic Versioning
    'SemanticVersion',

    # Model Comparison
    'ModelComparator',
    'ComparisonResult',

    # Version Management
    'VersionManager',
    'VersionEntry',
    'Branch',

    # Model Registry
    'ModelRegistry',
    'ModelEntry',

    # Version History
    'VersionHistory',
    'ChangeRecord',
    'EvolutionMetrics',

    # Model Lineage
    'ModelLineage',
    'LineageNode',
    'LineageEdge',
    'LineagePath'
]

__version__ = "1.0.0"
__author__ = "Ailoos Team"
__description__ = "Sistema avanzado de versionado de modelos para FASE 9"