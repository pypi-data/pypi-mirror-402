"""
EmpoorioLM Configuration with MoE support
Configuración completa de EmpoorioLM con soporte para Mixture of Experts.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json
import torch


@dataclass
class EmpoorioLMConfig:
    """
    Complete configuration for EmpoorioLM with MoE support.
    """

    # Base model parameters
    vocab_size: int = 30000
    hidden_size: int = 768
    num_layers: int = 12
    num_heads: int = 12
    max_position_embeddings: int = 1024
    dropout: float = 0.1
    activation_function: str = "gelu"
    layer_norm_eps: float = 1e-5
    initializer_range: float = 0.02

    # MoE parameters
    use_moe: bool = True
    num_experts: int = 8
    moe_layers: List[int] = field(default_factory=lambda: [4, 7, 10])
    top_k: int = 2
    load_balance_weight: float = 0.01
    expert_quantization: str = "int8"

    # Training parameters
    learning_rate: float = 1e-4
    weight_decay: float = 0.01
    adam_beta1: float = 0.9
    adam_beta2: float = 0.999
    adam_epsilon: float = 1e-8

    # Generation parameters
    max_length: int = 2048
    temperature: float = 1.0
    top_p: float = 0.9
    top_k_gen: int = 50
    repetition_penalty: float = 1.1

    # Device and optimization
    device: str = "auto"  # auto, cpu, cuda, mps
    use_flash_attention: bool = True
    gradient_checkpointing: bool = False
    mixed_precision: bool = True

    # RoPE parameters
    use_rope: bool = True
    max_context_size: int = 8192

    # YaRN parameters (for extending RoPE to longer contexts)
    use_yarn: bool = False
    yarn_scale: float = 2.0  # Default 2x extension
    yarn_original_max_position_embeddings: int = 2048

    # Sliding Window Attention parameters
    use_sliding_window: bool = False
    sliding_window_size: int = 1024
    use_sliding_window_cache: bool = True

    # Flash Attention parameters
    use_flash_attention: bool = True

    # LoRA parameters
    use_lora: bool = False
    lora_r: int = 8
    lora_alpha: float = 16.0
    lora_dropout: float = 0.05
    lora_target_modules: List[str] = field(default_factory=lambda: ["q_proj", "k_proj", "v_proj", "out_proj"])

    # Function calling parameters
    use_function_calling: bool = False
    tool_call_token: str = "<tool_call>"
    tool_call_end_token: str = "</tool_call>"
    max_tool_calls_per_response: int = 3
    tool_choice: str = "auto"  # auto, required, none
    function_call_temperature: float = 0.1  # Lower temperature for more deterministic tool calls

    # MIRAS parameters (Memory Integration for Real-time Adaptive Systems)
    use_miras: bool = False
    miras_layers: List[int] = field(default_factory=lambda: [])  # Layers where MIRAS is applied (every 2-3 layers)
    miras_memory_size: int = 512
    miras_dropout: float = 0.1
    miras_integration_pattern: str = "post_attention"  # post_attention, pre_ffn, post_ffn

    # Liquid Memory parameters (Liquid Titans - Fusión MoE + Memory)
    use_liquid_memory: bool = False
    liquid_memory_total_slots: int = 4096
    liquid_memory_base_per_expert: int = 256
    liquid_memory_adaptation_rate: float = 0.01

    # Model Parallelism parameters
    use_model_parallelism: bool = False
    tensor_parallel_size: int = 1
    pipeline_parallel_size: int = 1
    data_parallel_size: int = 1
    world_size: int = 1  # Computed as tensor_parallel_size * data_parallel_size

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Handle auto device detection
        if isinstance(self.device, str) and self.device == "auto":
            if torch.cuda.is_available():
                self.device = "cuda"
            elif torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = "cpu"

        # Convert to torch.device
        self.device = torch.device(self.device)

        self._validate_config()

    def _validate_config(self):
        """Validate configuration parameters."""
        assert self.hidden_size % self.num_heads == 0, "hidden_size must be divisible by num_heads"
        if self.use_moe:
            assert self.num_experts > 0, "num_experts must be positive"
            assert self.top_k <= self.num_experts, "top_k cannot exceed num_experts"
            assert all(0 <= layer < self.num_layers for layer in self.moe_layers), "moe_layers must be valid layer indices"
        assert self.expert_quantization in ["none", "int8", "int4"], "invalid expert_quantization"
        assert self.device.type in ["cpu", "cuda", "mps"], "invalid device"
        if self.use_lora:
            assert self.lora_r > 0, "lora_r must be positive"
            assert self.lora_alpha > 0, "lora_alpha must be positive"
            assert 0 <= self.lora_dropout < 1, "lora_dropout must be in [0, 1)"
            assert len(self.lora_target_modules) > 0, "lora_target_modules cannot be empty"

        if self.use_function_calling:
            assert self.tool_call_token, "tool_call_token cannot be empty when function calling is enabled"
            assert self.tool_call_end_token, "tool_call_end_token cannot be empty when function calling is enabled"
            assert self.max_tool_calls_per_response > 0, "max_tool_calls_per_response must be positive"
            assert self.tool_choice in ["auto", "required", "none"], "tool_choice must be one of: auto, required, none"
            assert 0 < self.function_call_temperature <= 1.0, "function_call_temperature must be in (0, 1]"

        # Validate YaRN parameters
        if self.use_yarn:
            assert self.yarn_scale > 0, "yarn_scale must be positive"
            assert self.yarn_original_max_position_embeddings > 0, "yarn_original_max_position_embeddings must be positive"
            assert self.max_context_size > self.yarn_original_max_position_embeddings, "max_context_size must be larger than yarn_original_max_position_embeddings"

        # Validate Sliding Window parameters
        if self.use_sliding_window:
            assert self.sliding_window_size > 0, "sliding_window_size must be positive"
            assert self.sliding_window_size <= self.max_context_size, "sliding_window_size cannot exceed max_context_size"

        # Validate MIRAS parameters
        if self.use_miras:
            assert self.miras_memory_size > 0, "miras_memory_size must be positive"
            assert 0 <= self.miras_dropout < 1, "miras_dropout must be in [0, 1)"
            assert self.miras_integration_pattern in ["post_attention", "pre_ffn", "post_ffn"], "invalid miras_integration_pattern"
            if self.miras_layers:
                assert all(0 <= layer < self.num_layers for layer in self.miras_layers), "miras_layers must be valid layer indices"
            else:
                # Auto-configure MIRAS layers every 2-3 layers
                self.miras_layers = list(range(2, self.num_layers, 3))  # Every 3rd layer starting from 2

        # Validate Liquid Memory parameters
        if self.use_liquid_memory:
            assert self.liquid_memory_total_slots > 0, "liquid_memory_total_slots must be positive"
            assert self.liquid_memory_base_per_expert > 0, "liquid_memory_base_per_expert must be positive"
            assert 0 < self.liquid_memory_adaptation_rate <= 1.0, "liquid_memory_adaptation_rate must be in (0, 1]"
            assert self.use_moe, "Liquid Memory requires MoE to be enabled"
            assert self.use_miras, "Liquid Memory requires MIRAS to be enabled"

        # Validate Model Parallelism parameters
        if self.use_model_parallelism:
            assert self.tensor_parallel_size > 0, "tensor_parallel_size must be positive"
            assert self.pipeline_parallel_size > 0, "pipeline_parallel_size must be positive"
            assert self.data_parallel_size > 0, "data_parallel_size must be positive"
            assert self.world_size == self.tensor_parallel_size * self.data_parallel_size, \
                "world_size must equal tensor_parallel_size * data_parallel_size"
            assert self.world_size > 1, "world_size must be > 1 for model parallelism"

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "vocab_size": self.vocab_size,
            "hidden_size": self.hidden_size,
            "num_layers": self.num_layers,
            "num_heads": self.num_heads,
            "max_position_embeddings": self.max_position_embeddings,
            "dropout": self.dropout,
            "activation_function": self.activation_function,
            "layer_norm_eps": self.layer_norm_eps,
            "initializer_range": self.initializer_range,
            "use_moe": self.use_moe,
            "num_experts": self.num_experts,
            "moe_layers": self.moe_layers,
            "top_k": self.top_k,
            "load_balance_weight": self.load_balance_weight,
            "expert_quantization": self.expert_quantization,
            "learning_rate": self.learning_rate,
            "weight_decay": self.weight_decay,
            "adam_beta1": self.adam_beta1,
            "adam_beta2": self.adam_beta2,
            "adam_epsilon": self.adam_epsilon,
            "max_length": self.max_length,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k_gen": self.top_k_gen,
            "repetition_penalty": self.repetition_penalty,
            "device": str(self.device),
            "use_flash_attention": self.use_flash_attention,
            "gradient_checkpointing": self.gradient_checkpointing,
            "mixed_precision": self.mixed_precision,
            "use_rope": self.use_rope,
            "max_context_size": self.max_context_size,
            "use_yarn": self.use_yarn,
            "yarn_scale": self.yarn_scale,
            "yarn_original_max_position_embeddings": self.yarn_original_max_position_embeddings,
            "use_sliding_window": self.use_sliding_window,
            "sliding_window_size": self.sliding_window_size,
            "use_sliding_window_cache": self.use_sliding_window_cache,
            "use_flash_attention": self.use_flash_attention,
            "use_lora": self.use_lora,
            "lora_r": self.lora_r,
            "lora_alpha": self.lora_alpha,
            "lora_dropout": self.lora_dropout,
            "lora_target_modules": self.lora_target_modules,
            "use_function_calling": self.use_function_calling,
            "tool_call_token": self.tool_call_token,
            "tool_call_end_token": self.tool_call_end_token,
            "max_tool_calls_per_response": self.max_tool_calls_per_response,
            "tool_choice": self.tool_choice,
            "function_call_temperature": self.function_call_temperature,
            "use_miras": self.use_miras,
            "miras_layers": self.miras_layers,
            "miras_memory_size": self.miras_memory_size,
            "miras_dropout": self.miras_dropout,
            "miras_integration_pattern": self.miras_integration_pattern,
            "use_liquid_memory": self.use_liquid_memory,
            "liquid_memory_total_slots": self.liquid_memory_total_slots,
            "liquid_memory_base_per_expert": self.liquid_memory_base_per_expert,
            "liquid_memory_adaptation_rate": self.liquid_memory_adaptation_rate,
            "use_model_parallelism": self.use_model_parallelism,
            "tensor_parallel_size": self.tensor_parallel_size,
            "pipeline_parallel_size": self.pipeline_parallel_size,
            "data_parallel_size": self.data_parallel_size,
            "world_size": self.world_size,
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'EmpoorioLMConfig':
        """Create config from dictionary."""
        return cls(**config_dict)

    def save_config(self, path: str):
        """Save configuration to JSON file."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load_config(cls, path: str) -> 'EmpoorioLMConfig':
        """Load configuration from JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        return cls.from_dict(config_dict)

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information summary."""
        total_params_dense = self._calculate_dense_params()
        total_params_moe = self._calculate_moe_params()

        return {
            "model_type": "EmpoorioLM" + ("-MoE" if self.use_moe else ""),
            "architecture": "GPT-2 style transformer with MoE" if self.use_moe else "GPT-2 style transformer",
            "vocab_size": self.vocab_size,
            "hidden_size": self.hidden_size,
            "num_layers": self.num_layers,
            "num_heads": self.num_heads,
            "max_position_embeddings": self.max_position_embeddings,
            "use_moe": self.use_moe,
            "num_experts": self.num_experts if self.use_moe else 0,
            "moe_layers": self.moe_layers if self.use_moe else [],
            "top_k": self.top_k if self.use_moe else 0,
            "expert_quantization": self.expert_quantization if self.use_moe else "none",
            "total_params_dense": total_params_dense,
            "total_params_moe": total_params_moe if self.use_moe else total_params_dense,
            "parameter_efficiency": total_params_moe / total_params_dense if self.use_moe and total_params_dense > 0 else 1.0,
            "use_lora": self.use_lora,
            "lora_r": self.lora_r if self.use_lora else 0,
            "lora_alpha": self.lora_alpha if self.use_lora else 0.0,
            "lora_dropout": self.lora_dropout if self.use_lora else 0.0,
            "lora_target_modules": self.lora_target_modules if self.use_lora else [],
            "use_function_calling": self.use_function_calling,
            "tool_call_token": self.tool_call_token if self.use_function_calling else None,
            "tool_call_end_token": self.tool_call_end_token if self.use_function_calling else None,
            "max_tool_calls_per_response": self.max_tool_calls_per_response if self.use_function_calling else 0,
            "tool_choice": self.tool_choice if self.use_function_calling else "none",
            "function_call_temperature": self.function_call_temperature if self.use_function_calling else 1.0,
            "use_yarn": self.use_yarn,
            "yarn_scale": self.yarn_scale if self.use_yarn else 0.0,
            "yarn_original_max_position_embeddings": self.yarn_original_max_position_embeddings if self.use_yarn else 0,
            "use_sliding_window": self.use_sliding_window,
            "sliding_window_size": self.sliding_window_size if self.use_sliding_window else 0,
            "use_sliding_window_cache": self.use_sliding_window_cache if self.use_sliding_window else False,
            "use_flash_attention": self.use_flash_attention,
            "use_miras": self.use_miras,
            "miras_layers": self.miras_layers if self.use_miras else [],
            "miras_memory_size": self.miras_memory_size if self.use_miras else 0,
            "miras_dropout": self.miras_dropout if self.use_miras else 0.0,
            "miras_integration_pattern": self.miras_integration_pattern if self.use_miras else "none",
            "use_liquid_memory": self.use_liquid_memory,
            "liquid_memory_total_slots": self.liquid_memory_total_slots if self.use_liquid_memory else 0,
            "liquid_memory_base_per_expert": self.liquid_memory_base_per_expert if self.use_liquid_memory else 0,
            "liquid_memory_adaptation_rate": self.liquid_memory_adaptation_rate if self.use_liquid_memory else 0.0,
            "use_model_parallelism": self.use_model_parallelism,
            "tensor_parallel_size": self.tensor_parallel_size if self.use_model_parallelism else 1,
            "pipeline_parallel_size": self.pipeline_parallel_size if self.use_model_parallelism else 1,
            "data_parallel_size": self.data_parallel_size if self.use_model_parallelism else 1,
            "world_size": self.world_size if self.use_model_parallelism else 1,
        }

    def _calculate_dense_params(self) -> int:
        """Calculate total parameters for dense model."""
        # Embedding parameters
        embed_params = self.vocab_size * self.hidden_size + self.max_position_embeddings * self.hidden_size

        # Transformer block parameters
        # Attention: 3 * (hidden_size * hidden_size) for QKV + output projection
        attn_params = 4 * self.hidden_size * self.hidden_size
        # MLP: 2 * (hidden_size * 4 * hidden_size) for FFN
        mlp_params = 8 * self.hidden_size * self.hidden_size
        # Layer norms: 2 * hidden_size each
        ln_params = 4 * self.hidden_size

        block_params = attn_params + mlp_params + ln_params
        transformer_params = self.num_layers * block_params

        # LM head: tied with embeddings
        lm_head_params = 0  # Already counted in embeddings

        total = embed_params + transformer_params + lm_head_params
        return total

    def _calculate_moe_params(self) -> int:
        """Calculate total parameters for MoE model."""
        dense_params = self._calculate_dense_params()

        if not self.use_moe:
            return dense_params

        # MoE parameters
        moe_layer_count = len(self.moe_layers)

        # Router parameters: hidden_size * num_experts
        router_params = self.hidden_size * self.num_experts

        # Expert parameters per MoE layer
        # Each expert: 3 * (hidden_size * 4 * hidden_size) for SwiGLU
        expert_params_per_layer = self.num_experts * 12 * self.hidden_size * self.hidden_size

        # Shared expert: same as dense FFN
        shared_expert_params = 8 * self.hidden_size * self.hidden_size

        # Output projection
        output_proj_params = self.hidden_size * self.hidden_size

        moe_params_per_layer = router_params + expert_params_per_layer + shared_expert_params + output_proj_params

        # Subtract dense FFN params for MoE layers and add MoE params
        dense_ffn_per_layer = 8 * self.hidden_size * self.hidden_size
        dense_subtract = moe_layer_count * dense_ffn_per_layer

        moe_add = moe_layer_count * moe_params_per_layer

        total_moe = dense_params - dense_subtract + moe_add
        return total_moe


# Predefined configurations for different model sizes
def get_config_for_model_size(size: str, use_moe: bool = True, device: str = "auto") -> EmpoorioLMConfig:
    """Get configuration for different model sizes with optional MoE."""

    base_configs = {
        "small": {
            "hidden_size": 256,
            "num_layers": 6,
            "num_heads": 8,
            "num_experts": 4,
            "moe_layers": [2, 4],
        },
        "medium": {
            "hidden_size": 512,
            "num_layers": 8,
            "num_heads": 8,
            "num_experts": 8,
            "moe_layers": [3, 5, 7],
        },
        "large": {
            "hidden_size": 768,
            "num_layers": 12,
            "num_heads": 12,
            "num_experts": 8,
            "moe_layers": [4, 7, 10],
        },
        "xlarge": {
            "hidden_size": 1024,
            "num_layers": 16,
            "num_heads": 16,
            "num_experts": 16,
            "moe_layers": [5, 8, 11, 14],
        },
        "xxl": {
            "hidden_size": 4096,
            "num_layers": 32,
            "num_heads": 32,
            "num_experts": 64,
            "moe_layers": list(range(4, 32, 4)),  # Every 4th layer: 4,8,12,16,20,24,28
        },
        "xxl_pro": {
            "hidden_size": 8192,
            "num_layers": 48,
            "num_heads": 64,
            "num_experts": 128,
            "moe_layers": list(range(6, 48, 6)),  # Every 6th layer: 6,12,18,24,30,36,42
        },
        "ultra": {
            "hidden_size": 12288,
            "num_layers": 64,
            "num_heads": 96,
            "num_experts": 256,
            "moe_layers": list(range(8, 64, 8)),  # Every 8th layer: 8,16,24,32,40,48,56
        }
    }

    if size not in base_configs:
        raise ValueError(f"Unknown model size: {size}. Available: {list(base_configs.keys())}")

    config_dict = base_configs[size].copy()
    config_dict["use_moe"] = use_moe
    config_dict["device"] = device

    # Special handling for XXL configurations
    if size in ["xxl", "xxl_pro", "ultra"]:
        # Enable advanced features for large models
        config_dict.update({
            "use_moe": True,
            "use_miras": True,
            "use_liquid_memory": True,
            "use_flash_attention": True,
            "gradient_checkpointing": True,
            "mixed_precision": True,
            "expert_quantization": "int8",  # Memory optimization for large models
            "max_context_size": 32768,  # Larger context for XXL models
            "use_yarn": True,
            "yarn_scale": 4.0,  # 4x context extension
        })
    # Habilitar MIRAS por defecto en modelos grandes
    elif size in ["large", "xlarge"]:
        config_dict["use_miras"] = True

    return EmpoorioLMConfig(**config_dict)


# Configuration for federated learning compatibility
def get_federated_config(base_config: EmpoorioLMConfig) -> EmpoorioLMConfig:
    """Get configuration optimized for federated learning."""
    # Create a copy with federated-friendly settings
    config_dict = base_config.to_dict()
    config_dict.update({
        "gradient_checkpointing": True,  # Memory efficient
        "mixed_precision": True,  # Faster training
        "load_balance_weight": 0.05,  # Stronger load balancing for FL
        "expert_quantization": "int8",  # Reduce memory footprint
    })

    return EmpoorioLMConfig(**config_dict)