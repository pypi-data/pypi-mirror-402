"""
Training Package - FASE 1, 2, 3 y REAL-5: Entrenamiento Completo de EmpoorioLM

FASE 1: Pipeline síncrono básico
- EmpoorioLMTrainingPipeline: Pipeline completo desde datos hasta despliegue

FASE 2: Entrenamiento asíncrono
- AsyncTrainingController: Control asíncrono con pausa/reanudación
- TrainingStateManager: Gestión persistente del estado
- CheckpointManager: Checkpoints optimizados con compresión
- TrainingProgressTracker: Seguimiento y métricas en tiempo real
- NetworkSyncManager: Sincronización con red P2P
- TrainingAPI: API REST para control remoto

FASE 3: Entrenamiento por nodos
- NodeTrainingIntegration: Integración SDK + entrenamiento asíncrono
- DatasetAdapter: Adaptador para datasets del DataHub
- Sistema completo: Descarga → Entrenamiento → Contribución Federada → Recompensas

FASE REAL-5: Pipeline de datos reales
- RealDataPipeline: Carga y gestión de datasets reales (WikiText, OpenWebText)
- DataPreprocessor: Preprocesamiento con tokenización BPE AILOOS
- EfficientDataLoader: DataLoader optimizado con prefetching y caching
- FederatedDatasetSharder: Particionamiento para entrenamiento federado
- DataQualityValidator: Validación de calidad y diversidad de datos
- RealDataTrainingPipeline: Pipeline completo integrado
"""

# Componentes de la FASE 1 (existentes)
from .pipeline import EmpoorioLMTrainingPipeline, TrainingPipelineConfig
from .massive_federated_trainer import MassiveFederatedTrainer
from .tokenizer_trainer import TokenizerTrainer

# Componentes de la FASE 2 (nuevos)
from .training_state_manager import TrainingStateManager, TrainingStatus, TrainingSession
from .checkpoint_manager import (
    CheckpointManager,
    CheckpointConfig,
    CheckpointMetadata,
    CompressionType,
    CheckpointStrategy
)
from .async_training_controller import (
    AsyncTrainingController,
    AsyncTrainingConfig,
    TrainingPhase
)
from .training_progress_tracker import (
    TrainingProgressTracker,
    ProgressMetrics,
    TrainingStats
)
from .network_sync_manager import (
    NetworkSyncManager,
    NetworkConfig,
    NetworkStatus,
    SyncPriority
)
from .training_api import (
    TrainingAPIService,
    TrainingAPIConfig,
    create_training_api
)

# Componentes de la FASE 3 (entrenamiento por nodos)
from .node_training_integration import (
    NodeTrainingIntegration,
    DatasetAdapter,
    create_node_training_integration
)

# Componentes de la FASE REAL-5 (datos reales) - importaciones lazy para evitar dependencias
try:
    from .real_data_pipeline import RealDataPipeline, DataPipelineConfig
except ImportError:
    RealDataPipeline = None
    DataPipelineConfig = None

try:
    from .efficient_data_loader import EfficientDataLoader, DataLoaderConfig
except ImportError:
    EfficientDataLoader = None
    DataLoaderConfig = None

try:
    from .data_preprocessing import DataPreprocessor, PreprocessingConfig
except ImportError:
    DataPreprocessor = None
    PreprocessingConfig = None

try:
    from .dataset_sharding import FederatedDatasetSharder, ShardingConfig, DatasetShard
except ImportError:
    FederatedDatasetSharder = None
    ShardingConfig = None
    DatasetShard = None

try:
    from .data_quality_validation import DataQualityValidator, QualityValidationConfig
except ImportError:
    DataQualityValidator = None
    QualityValidationConfig = None

try:
    from .real_data_training_pipeline import (
        RealDataTrainingPipeline,
        RealTrainingPipelineConfig,
        create_real_training_pipeline,
        run_real_data_pipeline
    )
except ImportError:
    RealDataTrainingPipeline = None
    RealTrainingPipelineConfig = None
    create_real_training_pipeline = None
    run_real_data_pipeline = None

# Build __all__ dynamically based on what was successfully imported
__all__ = [
    # FASE 1 - Componentes existentes
    'EmpoorioLMTrainingPipeline',
    'TrainingPipelineConfig',
    'MassiveFederatedTrainer',
    'TokenizerTrainer',

    # FASE 2 - Componentes nuevos
    'TrainingStateManager',
    'TrainingStatus',
    'TrainingSession',
    'CheckpointManager',
    'CheckpointConfig',
    'CheckpointMetadata',
    'CompressionType',
    'CheckpointStrategy',
    'AsyncTrainingController',
    'AsyncTrainingConfig',
    'TrainingPhase',
    'TrainingProgressTracker',
    'ProgressMetrics',
    'TrainingStats',
    'NetworkSyncManager',
    'NetworkConfig',
    'NetworkStatus',
    'SyncPriority',
    'TrainingAPIService',
    'TrainingAPIConfig',
    'create_training_api',

    # FASE 3 - Entrenamiento por nodos
    'NodeTrainingIntegration',
    'DatasetAdapter',
    'create_node_training_integration',
]

# Add FASE REAL-5 components only if they were imported successfully
if RealDataPipeline is not None:
    __all__.extend(['RealDataPipeline', 'DataPipelineConfig'])
if EfficientDataLoader is not None:
    __all__.extend(['EfficientDataLoader', 'DataLoaderConfig'])
if DataPreprocessor is not None:
    __all__.extend(['DataPreprocessor', 'PreprocessingConfig'])
if FederatedDatasetSharder is not None:
    __all__.extend(['FederatedDatasetSharder', 'ShardingConfig', 'DatasetShard'])
if DataQualityValidator is not None:
    __all__.extend(['DataQualityValidator', 'QualityValidationConfig'])
if RealDataTrainingPipeline is not None:
    __all__.extend([
        'RealDataTrainingPipeline',
        'RealTrainingPipelineConfig',
        'create_real_training_pipeline',
        'run_real_data_pipeline'
    ])