#!/usr/bin/env python3
"""
Streaming KV Cache para EmpoorioLM
Implementa cache de KV que se actualiza incrementalmente durante generación.
Reduce memoria para contextos largos y es compatible con Flash Attention.
"""

import torch
import torch.nn as nn
from typing import Optional, Tuple, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from .config import EmpoorioLMConfig


@dataclass
class KVCacheConfig:
    """Configuración para Streaming KV Cache."""
    max_context_length: int = 8192
    sliding_window_size: Optional[int] = None  # Si None, no sliding window
    enable_compression: bool = False
    compression_ratio: float = 0.5
    device: str = "auto"


class StreamingKVCache(nn.Module):
    """
    Cache de KV que se actualiza incrementalmente durante generación.

    Características:
    - Actualización incremental para reducir memoria
    - Soporte para sliding window
    - Compatible con Flash Attention
    - Compresión opcional para contextos muy largos
    """

    def __init__(self, config: KVCacheConfig, num_layers: int, num_heads: int, head_dim: int):
        super().__init__()
        self.config = config
        self.num_layers = num_layers
        self.num_heads = num_heads
        self.head_dim = head_dim

        # Determinar device
        if config.device == "auto":
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(config.device)

        # Inicializar caches vacíos
        self.k_caches: Dict[int, torch.Tensor] = {}
        self.v_caches: Dict[int, torch.Tensor] = {}
        self.current_length = 0
        self.max_length = config.max_context_length

        # Para sliding window
        self.sliding_window_size = config.sliding_window_size

    def reset(self):
        """Reiniciar el cache."""
        self.k_caches.clear()
        self.v_caches.clear()
        self.current_length = 0

    def get_cache_size(self) -> Dict[str, Any]:
        """Obtener información del tamaño del cache."""
        total_memory = 0
        for layer_idx in self.k_caches:
            k_size = self.k_caches[layer_idx].numel() * self.k_caches[layer_idx].element_size()
            v_size = self.v_caches[layer_idx].numel() * self.v_caches[layer_idx].element_size()
            total_memory += k_size + v_size

        return {
            "current_length": self.current_length,
            "max_length": self.max_length,
            "num_layers_cached": len(self.k_caches),
            "memory_bytes": total_memory,
            "memory_mb": total_memory / (1024 * 1024),
            "sliding_window": self.sliding_window_size is not None
        }

    def update_cache(self, layer_idx: int, k: torch.Tensor, v: torch.Tensor,
                    position_ids: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Actualizar el cache incrementalmente.

        Args:
            layer_idx: Índice de la capa
            k: Tensor K de shape (batch_size, seq_len, num_heads, head_dim)
            v: Tensor V de shape (batch_size, seq_len, num_heads, head_dim)
            position_ids: IDs de posición (opcional)

        Returns:
            Tupla (k_cache, v_cache) actualizados
        """
        batch_size, seq_len, num_heads, head_dim = k.shape

        # Inicializar cache si no existe
        if layer_idx not in self.k_caches:
            cache_length = min(self.max_length, seq_len)
            self.k_caches[layer_idx] = torch.zeros(
                batch_size, cache_length, num_heads, head_dim,
                dtype=k.dtype, device=self.device
            )
            self.v_caches[layer_idx] = torch.zeros(
                batch_size, cache_length, num_heads, head_dim,
                dtype=v.dtype, device=self.device
            )

        k_cache = self.k_caches[layer_idx]
        v_cache = self.v_caches[layer_idx]

        # Calcular posiciones para actualizar
        start_pos = self.current_length
        end_pos = min(start_pos + seq_len, self.max_length)

        # Actualizar cache
        update_length = end_pos - start_pos
        if update_length > 0:
            k_cache[:, start_pos:end_pos] = k[:, :update_length]
            v_cache[:, start_pos:end_pos] = v[:, :update_length]

        # Aplicar sliding window si está habilitado
        if self.sliding_window_size is not None and self.current_length >= self.sliding_window_size:
            # Mantener solo las últimas N posiciones
            window_start = max(0, self.current_length - self.sliding_window_size + seq_len)
            k_cache = k_cache[:, window_start:]
            v_cache = v_cache[:, window_start:]
            self.k_caches[layer_idx] = k_cache
            self.v_caches[layer_idx] = v_cache

        # Actualizar longitud actual
        self.current_length = min(self.current_length + seq_len, self.max_length)

        return k_cache, v_cache

    def get_cache_for_layer(self, layer_idx: int) -> Tuple[Optional[torch.Tensor], Optional[torch.Tensor]]:
        """Obtener cache para una capa específica."""
        if layer_idx in self.k_caches:
            return self.k_caches[layer_idx], self.v_caches[layer_idx]
        return None, None

    def compress_cache(self, compression_ratio: float = 0.5):
        """Comprimir cache para reducir memoria (experimental)."""
        if not self.config.enable_compression:
            return

        for layer_idx in self.k_caches:
            k_cache = self.k_caches[layer_idx]
            v_cache = self.v_caches[layer_idx]

            # Compresión simple: mantener solo cada N-ésima posición
            keep_indices = torch.arange(0, k_cache.size(1), int(1/compression_ratio))

            self.k_caches[layer_idx] = k_cache[:, keep_indices]
            self.v_caches[layer_idx] = v_cache[:, keep_indices]

    def to_device(self, device: torch.device):
        """Mover cache a dispositivo específico."""
        for layer_idx in self.k_caches:
            self.k_caches[layer_idx] = self.k_caches[layer_idx].to(device)
            self.v_caches[layer_idx] = self.v_caches[layer_idx].to(device)
        self.device = device

    def __repr__(self) -> str:
        cache_info = self.get_cache_size()
        return (f"StreamingKVCache("
                f"layers={self.num_layers}, "
                f"current_length={cache_info['current_length']}, "
                f"max_length={cache_info['max_length']}, "
                f"memory={cache_info['memory_mb']:.1f}MB, "
                f"sliding_window={self.sliding_window_size})")


def create_streaming_kv_cache(config: EmpoorioLMConfig, num_layers: int,
                              num_heads: int, head_dim: int) -> StreamingKVCache:
    """
    Factory function para crear StreamingKVCache.

    Args:
        config: Configuración del modelo
        num_layers: Número de capas
        num_heads: Número de cabezas de atención
        head_dim: Dimensión de cada cabeza

    Returns:
        Instancia de StreamingKVCache configurada
    """
    kv_config = KVCacheConfig(
        max_context_length=getattr(config, 'max_context_size', 8192),
        sliding_window_size=getattr(config, 'sliding_window_size', None),
        enable_compression=getattr(config, 'enable_kv_compression', False),
        compression_ratio=getattr(config, 'kv_compression_ratio', 0.5)
    )

    return StreamingKVCache(kv_config, num_layers, num_heads, head_dim)

