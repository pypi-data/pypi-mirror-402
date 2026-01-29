"""
AILOOS Edge Computing Module

Este módulo proporciona capacidades de edge computing para ejecutar EmpoorioLM
en dispositivos con recursos limitados, manteniendo eficiencia, seguridad y privacidad.
"""

from .edge_model_optimizer import EdgeModelOptimizer
from .lightweight_runtime import LightweightRuntime
from .edge_synchronization import EdgeSynchronization
from .resource_manager import ResourceManager
from .offline_capabilities import OfflineCapabilities
from .edge_federated_learning import EdgeFederatedLearning

# Nuevos componentes de Fase 4
from .advanced_quantization import AdvancedQuantizer, QuantizationConfig, QuantizationResult
from .onnx_exporter import UniversalExporter, ONNXExporter, CoreMLExporter, TFLiteExporter
from .offline_inference import OfflineInferenceEngine, OfflineConfig, PowerManager, ModelCache

__all__ = [
    # Componentes originales
    'EdgeModelOptimizer',
    'LightweightRuntime',
    'EdgeSynchronization',
    'ResourceManager',
    'OfflineCapabilities',
    'EdgeFederatedLearning',

    # Nuevos componentes de Fase 4
    'AdvancedQuantizer',
    'QuantizationConfig',
    'QuantizationResult',
    'UniversalExporter',
    'ONNXExporter',
    'CoreMLExporter',
    'TFLiteExporter',
    'OfflineInferenceEngine',
    'OfflineConfig',
    'PowerManager',
    'ModelCache'
]