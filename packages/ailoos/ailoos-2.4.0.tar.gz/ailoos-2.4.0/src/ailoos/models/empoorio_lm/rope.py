#!/usr/bin/env python3
"""
NTK-Aware Rotary Position Embedding (RoPE) Scaling
Implementación para extender contexto de 1024 a 8192+ tokens con Neural Tangent Kernel awareness.
"""

import torch
import torch.nn as nn
import math
from typing import Optional, Tuple


class NTKAwareRoPE(nn.Module):
    """
    NTK-Aware Rotary Position Embedding con scaling dinámico.

    Extiende el contexto usando interpolación matemática y NTK scaling
    para mantener la calidad de atención en secuencias largas.
    """

    def __init__(
        self,
        dim: int,
        max_position_embeddings: int = 8192,
        base: float = 10000.0,
        scaling_factor: float = 1.0,
        ntk_factor: float = 1.0
    ):
        super().__init__()
        self.dim = dim
        self.max_position_embeddings = max_position_embeddings
        self.base = base
        self.scaling_factor = scaling_factor
        self.ntk_factor = ntk_factor

        # Pre-compute frequencies con NTK scaling
        self._build_rope_cache()

    def _build_rope_cache(self):
        """Construir cache de RoPE con NTK scaling."""
        # NTK-aware base scaling
        ntk_base = self.base * (self.ntk_factor ** (self.dim / (self.dim - 2)))

        # Position frequencies
        position = torch.arange(self.max_position_embeddings, dtype=torch.float32)
        freqs = torch.outer(position, 1.0 / (ntk_base ** (torch.arange(0, self.dim, 2).float() / self.dim)))

        # Apply scaling factor for interpolation
        if self.scaling_factor != 1.0:
            freqs = freqs / self.scaling_factor

        # Complex representation
        self.register_buffer("cos_cached", freqs.cos(), persistent=False)
        self.register_buffer("sin_cached", freqs.sin(), persistent=False)

    def _get_cos_sin(self, position_ids: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Obtener cos y sin para las posiciones dadas."""
        cos = self.cos_cached[position_ids]  # [seq_len, dim//2]
        sin = self.sin_cached[position_ids]  # [seq_len, dim//2]
        return cos, sin

    def forward(self, x: torch.Tensor, position_ids: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Aplicar RoPE a la entrada.

        Args:
            x: Tensor de entrada [batch_size, num_heads, seq_len, head_dim]
            position_ids: IDs de posición [batch_size, seq_len]

        Returns:
            Tensor con RoPE aplicado
        """
        batch_size, num_heads, seq_len, head_dim = x.shape

        if position_ids is None:
            position_ids = torch.arange(seq_len, device=x.device).unsqueeze(0).expand(batch_size, -1)

        # Obtener cos y sin
        cos, sin = self._get_cos_sin(position_ids.flatten())  # [batch_size*seq_len, dim//2]

        # Reshape para broadcasting
        cos = cos.view(batch_size, 1, seq_len, head_dim // 2)  # [batch, 1, seq, dim//2]
        sin = sin.view(batch_size, 1, seq_len, head_dim // 2)

        # Split x into even and odd dimensions
        x1, x2 = x[..., ::2], x[..., 1::2]  # [batch, heads, seq, dim//2]

        # Apply rotation
        rotated_x1 = x1 * cos - x2 * sin
        rotated_x2 = x2 * cos + x1 * sin

        # Interleave back
        rotated_x = torch.empty_like(x)
        rotated_x[..., ::2] = rotated_x1
        rotated_x[..., 1::2] = rotated_x2

        return rotated_x

    @staticmethod
    def compute_ntk_factor(original_max_pos: int, target_max_pos: int, dim: int) -> float:
        """
        Calcular factor NTK para scaling óptimo.

        Args:
            original_max_pos: Longitud máxima original (ej: 1024)
            target_max_pos: Longitud máxima objetivo (ej: 8192)
            dim: Dimensión del embedding

        Returns:
            Factor NTK para scaling
        """
        # NTK scaling formula
        scale = math.log(target_max_pos / original_max_pos) / math.log(original_max_pos)
        ntk_factor = (scale * (dim - 2) / dim) + 1
        return ntk_factor

    @staticmethod
    def compute_scaling_factor(original_max_pos: int, target_max_pos: int) -> float:
        """
        Calcular factor de scaling para interpolación.

        Args:
            original_max_pos: Longitud máxima original
            target_max_pos: Longitud máxima objetivo

        Returns:
            Factor de scaling
        """
        return math.sqrt(target_max_pos / original_max_pos)


def apply_rope_to_attention(
    query: torch.Tensor,
    key: torch.Tensor,
    rope: NTKAwareRoPE,
    position_ids: Optional[torch.Tensor] = None
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Aplicar RoPE a queries y keys para atención.

    Args:
        query: Queries [batch, seq, heads, dim]
        key: Keys [batch, seq, heads, dim]
        rope: Instancia de RoPE
        position_ids: IDs de posición

    Returns:
        Tuple de (query_rotated, key_rotated)
    """
    query_rotated = rope(query, position_ids)
    key_rotated = rope(key, position_ids)
    return query_rotated, key_rotated


# Configuración por defecto para diferentes tamaños de contexto
ROPE_CONFIGS = {
    "1k": {
        "max_position_embeddings": 1024,
        "scaling_factor": 1.0,
        "ntk_factor": 1.0
    },
    "4k": {
        "max_position_embeddings": 4096,
        "scaling_factor": 2.0,
        "ntk_factor": 1.2
    },
    "8k": {
        "max_position_embeddings": 8192,
        "scaling_factor": 2.8,
        "ntk_factor": 1.4
    },
    "16k": {
        "max_position_embeddings": 16384,
        "scaling_factor": 4.0,
        "ntk_factor": 1.6
    },
    "32k": {
        "max_position_embeddings": 32768,
        "scaling_factor": 5.6,
        "ntk_factor": 1.8
    }
}


def create_rope_for_context(context_size: str, dim: int) -> NTKAwareRoPE:
    """
    Crear instancia de RoPE optimizada para un tamaño de contexto.

    Args:
        context_size: Tamaño de contexto ("1k", "4k", "8k", "16k", "32k")
        dim: Dimensión del embedding

    Returns:
        Instancia de NTKAwareRoPE configurada
    """
    config = ROPE_CONFIGS.get(context_size, ROPE_CONFIGS["8k"])
    return NTKAwareRoPE(
        dim=dim,
        max_position_embeddings=config["max_position_embeddings"],
        scaling_factor=config["scaling_factor"],
        ntk_factor=config["ntk_factor"]
    )