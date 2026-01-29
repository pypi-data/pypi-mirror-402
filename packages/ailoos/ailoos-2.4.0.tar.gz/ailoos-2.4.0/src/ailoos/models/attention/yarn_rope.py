"""
YaRN (Yet another RoPE extensioN) - Advanced RoPE Scaling for Long Context
==========================================================================

Implementation of YaRN: A RoPE extension technique for efficiently extending
context windows of large language models. YaRN enables extending context length
by 8x-32x without full retraining through intelligent position interpolation
and scaling techniques.

Paper: https://arxiv.org/abs/2309.00071
Authors: Jianlin Su, Murtadha Ahmed, Yu Lu, Shengfeng Pan, Wenbo Gao, Yunfeng Liu

Features:
- Position Interpolation for seamless extension
- NTK-aware scaling for better extrapolation
- Temperature scaling for attention stability
- Dynamic scaling factors based on target length
- Zero computational overhead during inference

Usage:
    yarn_config = YaRNConfig(scale_factor=8.0, max_position_embeddings=8192)
    yarn_rope = YaRNRotaryEmbedding(yarn_config)
    cos, sin = yarn_rope(seq_len=8192)
"""

import math
import torch
import torch.nn as nn
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class YaRNConfig:
    """Configuration for YaRN RoPE scaling."""

    # Core scaling parameters
    scale_factor: float = 8.0  # Target context extension factor (e.g., 8.0 for 1k->8k)
    original_max_position_embeddings: int = 2048  # Original context length the model was trained on
    max_position_embeddings: int = 8192  # Target maximum context length

    # NTK-aware scaling parameters
    beta_fast: float = 32.0  # Fast decay factor for NTK scaling
    beta_slow: float = 1.0   # Slow decay factor for NTK scaling

    # Interpolation parameters
    mscale: float = 1.0      # Global scaling factor
    mscale_all_dim: float = 1.0  # Per-dimension scaling factor

    # Temperature scaling for attention stability
    attn_factor: float = 1.0  # Attention temperature scaling

    # Advanced parameters
    extrapolation_factor: float = 1.0  # Extrapolation beyond trained length
    scaling_type: str = "yarn"  # "yarn", "linear", "ntk"

    def __post_init__(self):
        """Validate and compute derived parameters."""
        if self.scale_factor <= 1.0:
            raise ValueError("scale_factor must be > 1.0")

        if self.max_position_embeddings <= self.original_max_position_embeddings:
            raise ValueError("max_position_embeddings must be > original_max_position_embeddings")

        # Compute actual scale factor if not provided
        computed_scale = self.max_position_embeddings / self.original_max_position_embeddings
        if abs(self.scale_factor - computed_scale) > 0.1:
            logger.warning(f"Scale factor {self.scale_factor} doesn't match computed {computed_scale:.2f}")
            self.scale_factor = computed_scale


class YaRNRotaryEmbedding(nn.Module):
    """
    YaRN Rotary Position Embedding implementation.

    Extends RoPE to support much longer context lengths through intelligent
    position interpolation and scaling techniques.
    """

    def __init__(self, config: YaRNConfig, dim: int = None):
        """
        Initialize YaRN RoPE.

        Args:
            config: YaRN configuration
            dim: Model dimension (if None, will be inferred from context)
        """
        super().__init__()
        self.config = config
        self.dim = dim

        # Cache for computed embeddings
        self._cos_cached: Optional[torch.Tensor] = None
        self._sin_cached: Optional[torch.Tensor] = None
        self._seq_len_cached: Optional[int] = None

        logger.info(f"Initialized YaRN RoPE with scale_factor={config.scale_factor}, "
                   f"max_pos={config.max_position_embeddings}")

    def _compute_yarn_scaling(self, dim: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Compute YaRN scaling factors for position interpolation.

        Returns:
            Tuple of (mscale, mscale_all_dim) scaling tensors
        """
        # Compute position frequencies
        pos_freqs = torch.arange(0, dim, 2).float() / dim

        # NTK-aware scaling
        ntk_alpha = self.config.scale_factor ** (dim / (dim - 2 * len(pos_freqs) * math.log(self.config.scale_factor)))
        ntk_alpha = max(ntk_alpha, 1.0)  # Ensure minimum scaling

        # Compute scaling factors
        # beta_fast and beta_slow control the decay of scaling
        scale_factors = 1.0 / torch.sqrt(
            1.0 + torch.log(pos_freqs / self.config.beta_fast + 1e-8) ** 2 / self.config.beta_slow
        )

        # Apply NTK scaling
        scale_factors = scale_factors * ntk_alpha

        # Global scaling
        mscale = scale_factors.mean().item()
        mscale_all_dim = scale_factors

        return torch.tensor(mscale), mscale_all_dim

    def _compute_freqs(self, seq_len: int, dim: int, device: torch.device) -> torch.Tensor:
        """
        Compute rotary frequencies with YaRN scaling.

        Args:
            seq_len: Sequence length
            dim: Model dimension
            device: Target device

        Returns:
            Frequencies tensor of shape (seq_len, dim//2)
        """
        # Base frequencies (inverse frequencies)
        inv_freq = 1.0 / (10000 ** (torch.arange(0, dim, 2).float() / dim))

        # Compute YaRN scaling
        mscale, mscale_all_dim = self._compute_yarn_scaling(dim)

        # Apply per-dimension scaling
        inv_freq = inv_freq / mscale_all_dim.to(device)

        # Apply global scaling
        inv_freq = inv_freq * mscale

        # Generate position indices
        positions = torch.arange(seq_len, device=device).float()

        # Apply position interpolation for extension
        if seq_len > self.config.original_max_position_embeddings:
            # Interpolate positions to fit within original range
            scale = self.config.original_max_position_embeddings / seq_len
            positions = positions * scale

        # Compute frequencies: positions * inv_freq
        freqs = torch.outer(positions, inv_freq)

        return freqs

    def forward(self, seq_len: int, dim: Optional[int] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Compute rotary embeddings for given sequence length.

        Args:
            seq_len: Sequence length
            dim: Model dimension (uses cached if None)

        Returns:
            Tuple of (cos, sin) tensors for rotary embedding
        """
        if dim is None:
            if self.dim is None:
                raise ValueError("dim must be provided if not set during initialization")
            dim = self.dim

        # Check cache
        if (self._cos_cached is not None and
            self._sin_cached is not None and
            self._seq_len_cached == seq_len and
            self._cos_cached.device == torch.device('cpu')):  # Only cache CPU tensors

            cos_cached, sin_cached = self._cos_cached, self._sin_cached
            # Extend if needed
            if seq_len > cos_cached.shape[0]:
                cos_cached, sin_cached = self._extend_embeddings(seq_len, dim, cos_cached.device)

            return cos_cached[:seq_len], sin_cached[:seq_len]

        # Compute frequencies
        device = torch.device('cpu')  # Compute on CPU for caching
        freqs = self._compute_freqs(seq_len, dim, device)

        # Compute embeddings
        cos = torch.cos(freqs)
        sin = torch.sin(freqs)

        # Apply attention temperature scaling if configured
        if self.config.attn_factor != 1.0:
            cos = cos * self.config.attn_factor
            sin = sin * self.config.attn_factor

        # Cache results
        self._cos_cached = cos
        self._sin_cached = sin
        self._seq_len_cached = seq_len

        return cos, sin

    def _extend_embeddings(self, seq_len: int, dim: int, device: torch.device) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Extend cached embeddings to longer sequence length.

        Args:
            seq_len: New sequence length
            dim: Model dimension
            device: Target device

        Returns:
            Extended (cos, sin) tensors
        """
        # Compute new frequencies for extended length
        freqs = self._compute_freqs(seq_len, dim, device)

        cos = torch.cos(freqs)
        sin = torch.sin(freqs)

        # Apply attention scaling
        if self.config.attn_factor != 1.0:
            cos = cos * self.config.attn_factor
            sin = sin * self.config.attn_factor

        return cos, sin

    def apply_rotary_emb(self, x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
        """
        Apply rotary embeddings to input tensor.

        Args:
            x: Input tensor of shape (batch_size, seq_len, num_heads, head_dim)
            cos: Cosine embeddings
            sin: Sine embeddings

        Returns:
            Tensor with rotary embeddings applied
        """
        batch_size, seq_len, num_heads, head_dim = x.shape

        # Ensure embeddings match sequence length
        if cos.shape[0] < seq_len:
            cos, sin = self._extend_embeddings(seq_len, head_dim, x.device)
        elif cos.shape[0] > seq_len:
            cos = cos[:seq_len]
            sin = sin[:seq_len]

        # Reshape for broadcasting
        cos = cos.unsqueeze(1).unsqueeze(0)  # (seq_len, 1, 1, head_dim//2)
        sin = sin.unsqueeze(1).unsqueeze(0)  # (seq_len, 1, 1, head_dim//2)

        # Split input into even and odd dimensions
        x1, x2 = x[..., ::2], x[..., 1::2]

        # Apply rotation
        rotated = torch.cat([
            x1 * cos - x2 * sin,
            x2 * cos + x1 * sin
        ], dim=-1)

        return rotated

    def get_config(self) -> Dict[str, Any]:
        """Get configuration as dictionary."""
        return {
            "scale_factor": self.config.scale_factor,
            "original_max_position_embeddings": self.config.original_max_position_embeddings,
            "max_position_embeddings": self.config.max_position_embeddings,
            "beta_fast": self.config.beta_fast,
            "beta_slow": self.config.beta_slow,
            "mscale": self.config.mscale,
            "mscale_all_dim": self.config.mscale_all_dim,
            "attn_factor": self.config.attn_factor,
            "extrapolation_factor": self.config.extrapolation_factor,
            "scaling_type": self.config.scaling_type
        }

    def __repr__(self) -> str:
        return (f"YaRNRotaryEmbedding(scale_factor={self.config.scale_factor}, "
                f"max_pos={self.config.max_position_embeddings}, "
                f"dim={self.dim})")


# Convenience functions for easy usage
def create_yarn_config(scale_factor: float, original_max_pos: int = 2048,
                       target_max_pos: Optional[int] = None) -> YaRNConfig:
    """
    Create YaRN configuration with sensible defaults.

    Args:
        scale_factor: Context extension factor
        original_max_pos: Original context length
        target_max_pos: Target context length (computed if None)

    Returns:
        YaRNConfig instance
    """
    if target_max_pos is None:
        target_max_pos = int(original_max_pos * scale_factor)

    return YaRNConfig(
        scale_factor=scale_factor,
        original_max_position_embeddings=original_max_pos,
        max_position_embeddings=target_max_pos
    )


def apply_yarn_to_model(model: nn.Module, yarn_config: YaRNConfig) -> nn.Module:
    """
    Apply YaRN scaling to an existing model.

    This function replaces RoPE layers in the model with YaRN equivalents.

    Args:
        model: PyTorch model with RoPE layers
        yarn_config: YaRN configuration

    Returns:
        Model with YaRN applied
    """
    def replace_rope_layers(module: nn.Module, name: str = "") -> nn.Module:
        for child_name, child_module in module.named_children():
            full_name = f"{name}.{child_name}" if name else child_name

            # Replace rotary embedding layers
            if hasattr(child_module, 'inv_freq'):  # Standard RoPE layer
                dim = len(child_module.inv_freq) * 2
                yarn_layer = YaRNRotaryEmbedding(yarn_config, dim=dim)

                # Copy to same device
                yarn_layer = yarn_layer.to(child_module.inv_freq.device)

                setattr(module, child_name, yarn_layer)
                logger.info(f"Replaced RoPE layer '{full_name}' with YaRN")

            else:
                # Recursively apply to children
                replace_rope_layers(child_module, full_name)

        return module

    return replace_rope_layers(model)


# Export main classes
__all__ = [
    'YaRNConfig',
    'YaRNRotaryEmbedding',
    'create_yarn_config',
    'apply_yarn_to_model'
]