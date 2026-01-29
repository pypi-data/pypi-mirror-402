"""
Advanced configuration optimizations for improved accuracy.
Configuraciones avanzadas optimizadas para máxima precisión en EmpoorioLM.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import math
import torch
import torch.nn as nn
from .config import EmpoorioLMConfig


@dataclass
class AccuracyOptimizedConfig(EmpoorioLMConfig):
    """
    Configuration optimized for maximum accuracy.
    Mejora la precisión mediante técnicas avanzadas de arquitectura y training.
    """

    # Enhanced architecture parameters
    hidden_size: int = 1024  # Increased from 768 for better capacity
    num_layers: int = 24     # Increased from 12 for deeper understanding
    num_heads: int = 16      # Increased from 12 for better attention
    intermediate_size: int = field(default_factory=lambda: 4096)  # 4x hidden_size for better FFN

    # Advanced regularization
    dropout: float = 0.05    # Reduced from 0.1 for better retention
    attention_dropout: float = 0.05
    layer_norm_eps: float = 1e-6  # Tighter normalization
    initializer_range: float = 0.01  # Reduced for more stable initialization

    # Advanced attention mechanisms
    use_parallel_attention: bool = True  # Parallel attention for better context
    use_memory_efficient_attention: bool = True
    attention_bias: bool = True  # Bias in attention layers

    # Enhanced MoE configuration
    use_moe: bool = True
    num_experts: int = 16     # More experts for specialization
    moe_layers: List[int] = field(default_factory=lambda: [6, 12, 18])  # More MoE layers
    top_k: int = 3           # Higher top-k for better expert selection
    expert_capacity_factor: float = 1.5  # Higher capacity per expert

    # Advanced training parameters
    learning_rate: float = 2e-4  # Higher LR for faster convergence
    min_learning_rate: float = 1e-6  # Minimum LR for fine-tuning
    warmup_steps: int = 2000   # Longer warmup
    weight_decay: float = 0.001  # L2 regularization
    max_grad_norm: float = 1.0   # Gradient clipping

    # Curriculum learning
    use_curriculum_learning: bool = True
    curriculum_phases: List[Dict[str, Any]] = field(default_factory=lambda: [
        {"name": "foundation", "max_length": 512, "epochs": 2, "lr": 1e-4},
        {"name": "intermediate", "max_length": 1024, "epochs": 3, "lr": 2e-4},
        {"name": "advanced", "max_length": 2048, "epochs": 4, "lr": 3e-4},
        {"name": "expert", "max_length": 4096, "epochs": 5, "lr": 2e-4}
    ])

    # Advanced optimization
    use_adaptive_optimizer: bool = True  # AdamW with adaptive LR
    use_gradient_checkpointing: bool = True
    use_mixed_precision: bool = True
    use_flash_attention: bool = True

    # Enhanced context handling
    max_context_size: int = 8192  # Larger context window
    use_yarn: bool = True         # YaRN for better long context
    yarn_scale: float = 4.0       # 4x context extension

    # Better generation parameters
    temperature: float = 0.8      # Slightly higher for creativity
    top_p: float = 0.95          # Nucleus sampling
    top_k_gen: int = 40          # Top-k sampling
    repetition_penalty: float = 1.15  # Stronger repetition penalty

    # Advanced features
    use_function_calling: bool = True
    use_lora: bool = False  # Disable LoRA for full fine-tuning

    def __post_init__(self):
        """Enhanced post-initialization with accuracy optimizations."""
        super().__post_init__()

        # Set intermediate_size if not explicitly set
        if not hasattr(self, 'intermediate_size') or self.intermediate_size is None:
            self.intermediate_size = 4 * self.hidden_size

        # Validate advanced parameters
        self._validate_accuracy_config()

    def _validate_accuracy_config(self):
        """Validate accuracy-optimized parameters."""
        assert self.hidden_size >= 512, "hidden_size too small for accuracy optimization"
        assert self.num_layers >= 12, "num_layers too small for accuracy optimization"
        assert self.intermediate_size >= 2 * self.hidden_size, "intermediate_size too small"

        if self.use_moe:
            assert self.num_experts >= 8, "num_experts too small for accuracy"
            assert self.top_k >= 2, "top_k too small for expert diversity"

        if self.use_curriculum_learning:
            assert len(self.curriculum_phases) > 0, "curriculum_phases cannot be empty"
            for phase in self.curriculum_phases:
                assert "max_length" in phase, "curriculum phase missing max_length"
                assert "epochs" in phase, "curriculum phase missing epochs"


@dataclass
class HighAccuracyConfig(AccuracyOptimizedConfig):
    """
    Configuration for maximum accuracy - targets 90%+ performance.
    Configuración para máxima precisión - objetivo 90%+ rendimiento.
    """

    # Maximum capacity architecture
    hidden_size: int = 1536  # Large capacity
    num_layers: int = 32     # Very deep network
    num_heads: int = 24      # Many attention heads
    intermediate_size: int = field(default_factory=lambda: 6144)  # 4x hidden_size

    # Advanced MoE
    num_experts: int = 32    # Many experts
    moe_layers: List[int] = field(default_factory=lambda: [8, 16, 24, 30])  # More MoE layers
    top_k: int = 4          # Higher expert selection
    expert_capacity_factor: float = 2.0

    # Aggressive regularization for stability
    dropout: float = 0.03
    attention_dropout: float = 0.03
    weight_decay: float = 0.0001

    # Advanced training
    learning_rate: float = 1e-4
    warmup_steps: int = 5000
    max_grad_norm: float = 0.5

    # Maximum context
    max_context_size: int = 16384
    yarn_scale: float = 8.0

    # Enhanced curriculum
    curriculum_phases: List[Dict[str, Any]] = field(default_factory=lambda: [
        {"name": "foundation", "max_length": 1024, "epochs": 3, "lr": 5e-5},
        {"name": "intermediate", "max_length": 2048, "epochs": 4, "lr": 1e-4},
        {"name": "advanced", "max_length": 4096, "epochs": 5, "lr": 1.5e-4},
        {"name": "expert", "max_length": 8192, "epochs": 6, "lr": 1e-4},
        {"name": "master", "max_length": 16384, "epochs": 8, "lr": 5e-5}
    ])


def get_accuracy_optimized_config(size: str = "large") -> AccuracyOptimizedConfig:
    """Get accuracy-optimized configuration for different sizes."""

    configs = {
        "medium": AccuracyOptimizedConfig(
            hidden_size=768,
            num_layers=18,
            num_heads=12,
            num_experts=12,
            moe_layers=[6, 12, 16],
            max_context_size=4096,
            yarn_scale=2.0
        ),
        "large": AccuracyOptimizedConfig(
            hidden_size=1024,
            num_layers=24,
            num_heads=16,
            num_experts=16,
            moe_layers=[6, 12, 18],
            max_context_size=8192,
            yarn_scale=4.0
        ),
        "xlarge": AccuracyOptimizedConfig(
            hidden_size=1280,
            num_layers=30,
            num_heads=20,
            num_experts=20,
            moe_layers=[8, 16, 24, 28],
            max_context_size=12288,
            yarn_scale=6.0
        ),
        "max": HighAccuracyConfig()  # Maximum accuracy config
    }

    if size not in configs:
        raise ValueError(f"Unknown accuracy config size: {size}. Available: {list(configs.keys())}")

    return configs[size]


def get_curriculum_schedule(config: AccuracyOptimizedConfig) -> List[Dict[str, Any]]:
    """Get curriculum learning schedule from config."""
    if not config.use_curriculum_learning:
        return [{"name": "standard", "max_length": config.max_context_size, "epochs": 10, "lr": config.learning_rate}]

    return config.curriculum_phases


def create_accuracy_optimizer(model, config: AccuracyOptimizedConfig):
    """
    Create optimizer optimized for accuracy.
    Optimizador optimizado para máxima precisión.
    """
    from torch.optim import AdamW

    # Separate parameters for different learning rates
    decay_params = []
    no_decay_params = []

    for name, param in model.named_parameters():
        if param.requires_grad:
            if any(nd in name for nd in ["bias", "LayerNorm.weight"]):
                no_decay_params.append(param)
            else:
                decay_params.append(param)

    optimizer = AdamW([
        {"params": decay_params, "weight_decay": config.weight_decay, "lr": config.learning_rate},
        {"params": no_decay_params, "weight_decay": 0.0, "lr": config.learning_rate}
    ], betas=(config.adam_beta1, config.adam_beta2), eps=config.adam_epsilon)

    return optimizer


def create_accuracy_scheduler(optimizer, config: AccuracyOptimizedConfig, num_training_steps: int):
    """
    Create learning rate scheduler optimized for accuracy.
    Scheduler de learning rate optimizado para precisión.
    """
    from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts, LinearLR

    # Warmup phase
    warmup_scheduler = LinearLR(optimizer, start_factor=0.1, end_factor=1.0, total_iters=config.warmup_steps)

    # Main training with cosine annealing
    main_scheduler = CosineAnnealingWarmRestarts(
        optimizer,
        T_0=num_training_steps // 4,  # Restart every 1/4 of training
        T_mult=2,  # Double the period each restart
        eta_min=config.min_learning_rate
    )

    return warmup_scheduler, main_scheduler


# Utility functions for accuracy improvement
def apply_accuracy_improvements(model, config: AccuracyOptimizedConfig):
    """
    Apply various accuracy improvements to the model.
    Aplica varias mejoras de precisión al modelo.
    """

    # Enhanced weight initialization
    def init_weights(module):
        if isinstance(module, torch.nn.Linear):
            # Xavier/Glorot initialization with gain
            gain = 1.0
            if hasattr(module, 'activation_function'):
                if module.activation_function == "gelu":
                    gain = math.sqrt(2.0)
                elif module.activation_function == "relu":
                    gain = math.sqrt(2.0)

            torch.nn.init.xavier_uniform_(module.weight, gain=gain)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)

        elif isinstance(module, torch.nn.Embedding):
            # Normal initialization for embeddings
            torch.nn.init.normal_(module.weight, mean=0.0, std=config.initializer_range)

        elif isinstance(module, torch.nn.LayerNorm):
            torch.nn.init.ones_(module.weight)
            torch.nn.init.zeros_(module.bias)

    model.apply(init_weights)

    # Apply gradient checkpointing if enabled
    if config.use_gradient_checkpointing:
        model.gradient_checkpointing_enable()

    return model


__all__ = [
    'AccuracyOptimizedConfig',
    'HighAccuracyConfig',
    'get_accuracy_optimized_config',
    'get_curriculum_schedule',
    'create_accuracy_optimizer',
    'create_accuracy_scheduler',
    'apply_accuracy_improvements'
]