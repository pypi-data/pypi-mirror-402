"""
EmpoorioLM model implementations for AILOOS.
"""

from .moe import (
    MoEConfig,
    MoEExpert,
    NoisyTopKRouter,
    MoELayer,
    StaticMoERouter,
    compute_moe_loss,
    get_moe_statistics
)

# Import main model classes
from .model import EmpoorioLM, GPT2Attention, GPT2MLP, GPT2Block
from .model_llama import (
    EmpoorioLMConfig as EmpoorioLlamaConfig,
    EmpoorioModel,
    EmpoorioForCausalLM,
    EmpoorioRMSNorm,
    EmpoorioRotaryEmbedding,
    EmpoorioAttention,
    EmpoorioMLP,
    EmpoorioDecoderLayer,
    create_empoorio_baby_titan,
    create_empoorio_titan,
    create_empoorio_7b,
    create_empoorio_13b,
    create_empoorio_30b,
    create_empoorio_65b,
)

# Vision and multimodal components
from .vision import (
    EmpoorioVisionConfig,
    EmpoorioVisionModel,
    EmpoorioImageProcessor,
    EmpoorioPatchEmbedding,
    EmpoorioVisionAttention,
    EmpoorioVisionMLP,
    EmpoorioVisionLayer,
    EmpoorioVisionEncoder,
    create_empoorio_vision_base,
    create_empoorio_vision_large,
    create_empoorio_vision_huge,
)

from .multimodal import (
    EmpoorioMultimodalConfig,
    EmpoorioMultimodalModel,
    EmpoorioCrossAttention,
    EmpoorioMultimodalLayer,
    create_empoorio_multimodal_base,
    create_empoorio_multimodal_large,
    create_empoorio_multimodal_huge,
)

# Tokenizer
from .tokenizer import (
    EmpoorioTokenizerConfig,
    EmpoorioBPETokenizer,
    create_empoorio_tokenizer,
    train_empoorio_tokenizer,
)
from .model_config import EmpoorioLMConfig, get_config_for_model_size, get_federated_config

# Import advanced configurations
try:
    from .advanced_config import (
        AccuracyOptimizedConfig,
        HighAccuracyConfig,
        get_accuracy_optimized_config,
        get_curriculum_schedule,
        create_accuracy_optimizer,
        create_accuracy_scheduler,
        apply_accuracy_improvements
    )
except ImportError:
    # Advanced config may not be available in all contexts
    pass

__all__ = [
    # MoE components
    'MoEConfig',
    'MoEExpert',
    'NoisyTopKRouter',
    'MoELayer',
    'StaticMoERouter',
    'compute_moe_loss',
    'get_moe_statistics',

    # Main model (GPT-2 style)
    'EmpoorioLM',
    'EmpoorioLMConfig',
    'GPT2Attention',
    'GPT2MLP',
    'GPT2Block',

    # Llama-3 style architecture (independent implementation)
    'EmpoorioLlamaConfig',
    'EmpoorioModel',
    'EmpoorioForCausalLM',
    'EmpoorioRMSNorm',
    'EmpoorioRotaryEmbedding',
    'EmpoorioAttention',
    'EmpoorioMLP',
    'EmpoorioDecoderLayer',
    'create_empoorio_baby_titan',
    'create_empoorio_titan',
    'create_empoorio_7b',
    'create_empoorio_13b',
    'create_empoorio_30b',
    'create_empoorio_65b',

    # Vision components (independent implementation)
    'EmpoorioVisionConfig',
    'EmpoorioVisionModel',
    'EmpoorioImageProcessor',
    'EmpoorioPatchEmbedding',
    'EmpoorioVisionAttention',
    'EmpoorioVisionMLP',
    'EmpoorioVisionLayer',
    'EmpoorioVisionEncoder',
    'create_empoorio_vision_base',
    'create_empoorio_vision_large',
    'create_empoorio_vision_huge',

    # Multimodal integration (independent implementation)
    'EmpoorioMultimodalConfig',
    'EmpoorioMultimodalModel',
    'EmpoorioCrossAttention',
    'EmpoorioMultimodalLayer',
    'create_empoorio_multimodal_base',
    'create_empoorio_multimodal_large',
    'create_empoorio_multimodal_huge',

    # Configuration utilities
    'get_config_for_model_size',
    'get_federated_config',

    # Tokenizer
    'EmpoorioTokenizerConfig',
    'EmpoorioBPETokenizer',
    'create_empoorio_tokenizer',
    'train_empoorio_tokenizer',

    # Advanced configurations (optional)
    'AccuracyOptimizedConfig',
    'HighAccuracyConfig',
    'get_accuracy_optimized_config',
    'get_curriculum_schedule',
    'create_accuracy_optimizer',
    'create_accuracy_scheduler',
    'apply_accuracy_improvements'
]