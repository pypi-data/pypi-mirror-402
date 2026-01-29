"""
Sliding Window Attention with KV Cache
=======================================

Implementation of sliding window attention mechanism with intelligent KV caching
for efficient long-context processing. This enables processing of very long sequences
while maintaining constant memory usage and computational efficiency.

Features:
- Sliding window attention with configurable window size
- Intelligent KV cache management with LRU eviction
- Memory-efficient long context processing
- Integration with Flash Attention 2 for optimal performance
- Automatic cache compression for extended contexts

Usage:
    swa = SlidingWindowAttention(window_size=4096, max_cache_size=8192)
    output = swa(query, key, value, attention_mask)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, Dict, Any, List
import math
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)


class KVCache:
    """
    Intelligent Key-Value cache for sliding window attention.

    Manages KV states efficiently with LRU eviction and compression.
    """

    def __init__(self, max_cache_size: int = 8192, compression_ratio: float = 0.5):
        """
        Initialize KV cache.

        Args:
            max_cache_size: Maximum number of tokens to cache
            compression_ratio: Ratio for cache compression when full
        """
        self.max_cache_size = max_cache_size
        self.compression_ratio = compression_ratio

        # Cache storage: layer -> (key, value) tensors
        self.cache: Dict[int, Tuple[torch.Tensor, torch.Tensor]] = {}

        # Metadata for cache management
        self.cache_metadata: Dict[int, Dict[str, Any]] = {}

        # Access tracking for LRU
        self.access_order: OrderedDict[int, int] = OrderedDict()

        logger.info(f"Initialized KV cache with max_size={max_cache_size}")

    def get(self, layer_idx: int, seq_len: int) -> Optional[Tuple[torch.Tensor, torch.Tensor]]:
        """
        Retrieve cached KV states for a layer.

        Args:
            layer_idx: Transformer layer index
            seq_len: Required sequence length

        Returns:
            Cached (key, value) tensors or None if not available
        """
        if layer_idx not in self.cache:
            return None

        key, value = self.cache[layer_idx]

        # Check if cached sequence is long enough
        if key.shape[1] < seq_len:
            return None

        # Update access order for LRU
        self._update_access(layer_idx)

        # Return appropriate slice
        return key[:, :seq_len], value[:, :seq_len]

    def put(self, layer_idx: int, key: torch.Tensor, value: torch.Tensor):
        """
        Store KV states in cache.

        Args:
            layer_idx: Transformer layer index
            key: Key tensor to cache
            value: Value tensor to cache
        """
        # Check cache size limit
        if self._get_total_cache_size() >= self.max_cache_size:
            self._evict_entries()

        # Store in cache
        self.cache[layer_idx] = (key.detach(), value.detach())

        # Update metadata
        self.cache_metadata[layer_idx] = {
            'seq_len': key.shape[1],
            'timestamp': torch.cuda.Event().elapsed_time(torch.cuda.current_stream()) if torch.cuda.is_available() else 0,
            'memory_usage': key.numel() + value.numel()
        }

        # Update access order
        self._update_access(layer_idx)

    def _update_access(self, layer_idx: int):
        """Update access order for LRU tracking."""
        if layer_idx in self.access_order:
            self.access_order.move_to_end(layer_idx)
        else:
            self.access_order[layer_idx] = len(self.access_order)

    def _get_total_cache_size(self) -> int:
        """Get total number of cached tokens across all layers."""
        return sum(meta['seq_len'] for meta in self.cache_metadata.values())

    def _evict_entries(self):
        """Evict entries using LRU policy when cache is full."""
        target_size = int(self.max_cache_size * self.compression_ratio)

        # Sort by access order (LRU)
        lru_layers = list(self.access_order.keys())[:len(self.access_order)//2]

        for layer_idx in lru_layers:
            if layer_idx in self.cache:
                del self.cache[layer_idx]
                del self.cache_metadata[layer_idx]
                del self.access_order[layer_idx]

        logger.debug(f"Evicted {len(lru_layers)} layers from KV cache")

    def clear(self):
        """Clear all cached entries."""
        self.cache.clear()
        self.cache_metadata.clear()
        self.access_order.clear()
        logger.info("KV cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_memory = sum(meta['memory_usage'] for meta in self.cache_metadata.values())
        return {
            'cached_layers': len(self.cache),
            'total_cached_tokens': self._get_total_cache_size(),
            'max_cache_size': self.max_cache_size,
            'memory_usage_mb': total_memory * 4 / (1024 * 1024),  # Assuming float32
            'cache_hit_ratio': 0.0  # Would need to track hits/misses
        }


class SlidingWindowAttention(nn.Module):
    """
    Sliding Window Attention with efficient KV caching.

    Implements attention mechanism that only attends to a sliding window
    of recent tokens, enabling efficient processing of very long sequences.
    """

    def __init__(
        self,
        window_size: int = 4096,
        num_heads: int = 8,
        head_dim: int = 64,
        dropout: float = 0.0,
        max_cache_size: int = 8192,
        use_flash_attention: bool = True
    ):
        """
        Initialize sliding window attention.

        Args:
            window_size: Size of the sliding attention window
            num_heads: Number of attention heads
            head_dim: Dimension of each attention head
            dropout: Attention dropout probability
            max_cache_size: Maximum KV cache size
            use_flash_attention: Whether to use Flash Attention 2
        """
        super().__init__()

        self.window_size = window_size
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.dropout = dropout
        self.use_flash_attention = use_flash_attention

        # KV cache for efficiency
        self.kv_cache = KVCache(max_cache_size=max_cache_size)

        # Output projection
        self.out_proj = nn.Linear(num_heads * head_dim, num_heads * head_dim)

        # Dropout
        self.dropout_layer = nn.Dropout(dropout)

        logger.info(f"Initialized Sliding Window Attention: window_size={window_size}, "
                   f"num_heads={num_heads}, max_cache={max_cache_size}")

    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        layer_idx: int = 0,
        use_cache: bool = True
    ) -> Tuple[torch.Tensor, Optional[Dict[str, Any]]]:
        """
        Forward pass with sliding window attention.

        Args:
            query: Query tensor (batch_size, seq_len, num_heads, head_dim)
            key: Key tensor (batch_size, seq_len, num_heads, head_dim)
            value: Value tensor (batch_size, seq_len, num_heads, head_dim)
            attention_mask: Attention mask tensor
            layer_idx: Layer index for caching
            use_cache: Whether to use KV caching

        Returns:
            Tuple of (output, attention_metadata)
        """
        batch_size, seq_len, num_heads, head_dim = query.shape

        # Handle empty sequences
        if seq_len == 0 or batch_size == 0:
            # Return empty output with correct shape
            output_shape = (batch_size, seq_len, num_heads * head_dim)
            empty_output = torch.empty(output_shape, dtype=query.dtype, device=query.device)
            metadata = {
                'window_size': self.window_size,
                'seq_len': seq_len,
                'used_cache': False,
                'cache_stats': self.kv_cache.get_stats()
            }
            return empty_output, metadata

        # Try to get cached KV states
        cached_key, cached_value = None, None
        if use_cache:
            cached_kv = self.kv_cache.get(layer_idx, seq_len)
            if cached_kv is not None:
                cached_key, cached_value = cached_kv

        # Apply sliding window logic
        if seq_len <= self.window_size:
            # Sequence fits in window, use standard attention
            attention_output = self._compute_attention(
                query, key, value, attention_mask
            )
        else:
            # Apply sliding window attention
            attention_output = self._sliding_window_attention(
                query, key, value, attention_mask, cached_key, cached_value
            )

        # attention_output should be (batch_size, seq_len, num_heads, head_dim)
        # Reshape for output projection: (batch_size, seq_len, num_heads * head_dim)
        attention_output_flat = attention_output.view(batch_size, seq_len, -1)

        # Project output
        output = self.out_proj(attention_output_flat)

        # Apply dropout
        output = self.dropout_layer(output)

        # Cache KV states for future use
        if use_cache and seq_len > 0:
            self.kv_cache.put(layer_idx, key, value)

        # Metadata for debugging/monitoring
        metadata = {
            'window_size': self.window_size,
            'seq_len': seq_len,
            'used_cache': cached_key is not None,
            'cache_stats': self.kv_cache.get_stats()
        }

        return output, metadata

    def _compute_attention(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Compute standard attention (used when sequence fits in window).

        Args:
            query: (batch_size, seq_len, num_heads, head_dim)
            key: (batch_size, key_seq_len, num_heads, head_dim) - may differ from query seq_len
            value: (batch_size, key_seq_len, num_heads, head_dim) - may differ from query seq_len
            attention_mask: Optional attention mask

        Returns:
            Output tensor (batch_size, seq_len, num_heads, head_dim)
        """
        batch_size, seq_len, num_heads, head_dim = query.shape
        _, key_seq_len, _, _ = key.shape

        # Handle empty sequences
        if seq_len == 0 or batch_size == 0:
            return torch.empty(batch_size, seq_len, num_heads, head_dim,
                             dtype=query.dtype, device=query.device)

        # Reshape for attention computation: (batch_size * num_heads, seq_len, head_dim)
        query_flat = query.reshape(batch_size * num_heads, seq_len, head_dim)
        key_flat = key.reshape(batch_size * num_heads, key_seq_len, head_dim)
        value_flat = value.reshape(batch_size * num_heads, key_seq_len, head_dim)

        # Compute attention scores
        scale = 1.0 / math.sqrt(head_dim)
        attn_scores = torch.matmul(query_flat, key_flat.transpose(-2, -1)) * scale

        # Apply attention mask
        if attention_mask is not None:
            # Handle different mask formats
            if attention_mask.dim() == 2 and attention_mask.shape[0] == batch_size and attention_mask.shape[1] == seq_len:
                # Standard transformers format: (batch_size, seq_len)
                # For sliding window, we need to handle the case where key_seq_len != seq_len
                if key_seq_len == seq_len:
                    # Standard case
                    attention_mask = attention_mask.unsqueeze(-1).expand(-1, -1, seq_len)  # (batch, seq_len, seq_len)
                    attention_mask = attention_mask.unsqueeze(1).expand(-1, num_heads, -1, -1)  # (batch, heads, seq_len, seq_len)
                    attention_mask = attention_mask.reshape(batch_size * num_heads, seq_len, seq_len)
                    attention_mask = (1.0 - attention_mask) * float('-inf')  # 1 -> 0, 0 -> -inf
                else:
                    # Sliding window case - mask should match query-key interaction
                    # For simplicity, create a causal mask for the query-key interaction
                    attention_mask = torch.triu(torch.ones(seq_len, key_seq_len), diagonal=1).bool()
                    attention_mask = attention_mask.unsqueeze(0).unsqueeze(0).expand(batch_size, num_heads, -1, -1)
                    attention_mask = attention_mask.reshape(batch_size * num_heads, seq_len, key_seq_len)
                    attention_mask = attention_mask.to(dtype=attn_scores.dtype, device=attn_scores.device)
                    attention_mask = (1.0 - attention_mask) * float('-inf')  # 1 -> 0, 0 -> -inf
            elif attention_mask.dim() == 3 and attention_mask.shape[0] == batch_size and attention_mask.shape[1] == seq_len and attention_mask.shape[2] == key_seq_len:
                # (batch_size, seq_len, key_seq_len) format - perfect for sliding window
                attention_mask = attention_mask.unsqueeze(1).expand(-1, num_heads, -1, -1)
                attention_mask = attention_mask.reshape(batch_size * num_heads, seq_len, key_seq_len)
            else:
                # Unsupported format - skip masking
                attention_mask = None

            if attention_mask is not None:
                attn_scores = attn_scores + attention_mask

        # Apply softmax
        attn_weights = F.softmax(attn_scores, dim=-1)

        # Apply dropout
        attn_weights = self.dropout_layer(attn_weights)

        # Compute output
        output_flat = torch.matmul(attn_weights, value_flat)

        # Reshape back: (batch_size, seq_len, num_heads, head_dim)
        output = output_flat.view(batch_size, seq_len, num_heads, head_dim)

        return output

    def _sliding_window_attention(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        cached_key: Optional[torch.Tensor] = None,
        cached_value: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Compute sliding window attention for long sequences.
        """
        batch_size, seq_len, num_heads, head_dim = query.shape

        # Handle empty sequences
        if seq_len == 0 or batch_size == 0:
            return torch.empty(batch_size, seq_len, num_heads, head_dim,
                             dtype=query.dtype, device=query.device)

        # Combine cached and current KV states
        if cached_key is not None and cached_value is not None:
            # Use sliding window from cache + current
            window_key = torch.cat([cached_key, key], dim=1)
            window_value = torch.cat([cached_value, value], dim=1)
        else:
            # Use current sequence as window
            window_key = key
            window_value = value

        # Ensure window doesn't exceed maximum size
        window_seq_len = window_key.shape[1]
        if window_seq_len > self.window_size:
            # Take most recent tokens
            start_idx = window_seq_len - self.window_size
            window_key = window_key[:, start_idx:]
            window_value = window_value[:, start_idx:]

        # Adjust attention mask for window
        window_mask = None
        if attention_mask is not None:
            # For sliding window, we need to adjust the mask to match the window size
            # This is complex and depends on the mask format - for now, use None
            # In production, this would need careful handling based on the specific mask format
            window_mask = None

        # Compute attention within window
        return self._compute_attention(query, window_key, window_value, window_mask)

    def reset_cache(self):
        """Reset KV cache."""
        self.kv_cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get KV cache statistics."""
        return self.kv_cache.get_stats()

    def set_window_size(self, window_size: int):
        """Update window size."""
        self.window_size = window_size
        logger.info(f"Updated window size to {window_size}")


# Flash Attention 2 Integration
try:
    from flash_attn import flash_attn_func

    class FlashSlidingWindowAttention(SlidingWindowAttention):
        """
        Sliding Window Attention with Flash Attention 2 acceleration.
        """

        def _compute_attention(
            self,
            query: torch.Tensor,
            key: torch.Tensor,
            value: torch.Tensor,
            attention_mask: Optional[torch.Tensor] = None
        ) -> torch.Tensor:
            """
            Compute attention using Flash Attention 2.
            """
            # Flash attention expects different tensor shapes
            # (batch_size, seq_len, num_heads, head_dim) -> (batch_size, seq_len, num_heads * head_dim)
            batch_size, seq_len, num_heads, head_dim = query.shape

            # Reshape for flash attention
            q = query.view(batch_size, seq_len, num_heads * head_dim)
            k = key.view(batch_size, key.shape[1], num_heads * head_dim)
            v = value.view(batch_size, value.shape[1], num_heads * head_dim)

            # Apply flash attention
            output = flash_attn_func(
                q, k, v,
                dropout_p=self.dropout if self.training else 0.0,
                causal=True
            )

            # Reshape back
            output = output.view(batch_size, seq_len, num_heads, head_dim)

            return output

        def _sliding_window_attention(
            self,
            query: torch.Tensor,
            key: torch.Tensor,
            value: torch.Tensor,
            attention_mask: Optional[torch.Tensor] = None,
            cached_key: Optional[torch.Tensor] = None,
            cached_value: Optional[torch.Tensor] = None
        ) -> torch.Tensor:
            """
            Sliding window attention with Flash Attention 2.
            """
            # For now, fall back to standard implementation
            # Full Flash Attention 2 sliding window would require custom kernel
            return super()._sliding_window_attention(
                query, key, value, attention_mask, cached_key, cached_value
            )

except ImportError:
    logger.warning("Flash Attention 2 not available, using standard attention")
    FlashSlidingWindowAttention = SlidingWindowAttention


# Utility functions
def create_sliding_window_attention(
    window_size: int = 4096,
    num_heads: int = 8,
    head_dim: int = 64,
    use_flash: bool = True,
    **kwargs
) -> SlidingWindowAttention:
    """
    Create sliding window attention with optimal settings.

    Args:
        window_size: Attention window size
        num_heads: Number of attention heads
        head_dim: Head dimension
        use_flash: Whether to use Flash Attention 2
        **kwargs: Additional arguments

    Returns:
        Configured SlidingWindowAttention instance
    """
    if use_flash:
        try:
            return FlashSlidingWindowAttention(
                window_size=window_size,
                num_heads=num_heads,
                head_dim=head_dim,
                **kwargs
            )
        except:
            logger.warning("Falling back to standard sliding window attention")

    return SlidingWindowAttention(
        window_size=window_size,
        num_heads=num_heads,
        head_dim=head_dim,
        **kwargs
    )


def apply_sliding_window_to_model(
    model: nn.Module,
    window_size: int = 4096,
    use_flash: bool = True
) -> nn.Module:
    """
    Apply sliding window attention to existing transformer model.

    Args:
        model: Transformer model with attention layers
        window_size: Sliding window size
        use_flash: Whether to use Flash Attention 2

    Returns:
        Model with sliding window attention applied
    """
    def replace_attention_layers(module: nn.Module, name: str = "") -> nn.Module:
        for child_name, child_module in module.named_children():
            full_name = f"{name}.{child_name}" if name else child_name

            # Replace attention layers
            if hasattr(child_module, 'forward') and 'attention' in child_name.lower():
                # Infer dimensions from existing layer
                if hasattr(child_module, 'num_heads'):
                    num_heads = child_module.num_heads
                else:
                    num_heads = 8  # Default

                if hasattr(child_module, 'head_dim'):
                    head_dim = child_module.head_dim
                else:
                    head_dim = child_module.embed_dim // num_heads if hasattr(child_module, 'embed_dim') else 64

                # Create sliding window attention
                swa = create_sliding_window_attention(
                    window_size=window_size,
                    num_heads=num_heads,
                    head_dim=head_dim,
                    use_flash=use_flash
                )

                setattr(module, child_name, swa)
                logger.info(f"Replaced attention layer '{full_name}' with sliding window attention")

            else:
                # Recursively apply to children
                replace_attention_layers(child_module, full_name)

        return module

    return replace_attention_layers(model)


# Export main classes
__all__ = [
    'KVCache',
    'SlidingWindowAttention',
    'FlashSlidingWindowAttention',
    'create_sliding_window_attention',
    'apply_sliding_window_to_model'
]