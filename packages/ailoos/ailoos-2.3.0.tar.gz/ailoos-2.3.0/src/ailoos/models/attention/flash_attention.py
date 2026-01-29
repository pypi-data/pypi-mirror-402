"""
Flash Attention 2 Implementation for EmpoorioLM
===============================================

High-performance attention mechanism using Flash Attention 2.
Provides significant speedup and memory savings for transformer models.

Features:
- IO-aware attention computation
- Automatic kernel selection based on hardware
- Fused attention operations for maximum efficiency
- Support for causal and non-causal attention
- Compatible with existing attention interfaces

Author: AILOOS Team
"""

import torch
import torch.nn as nn
import math
from typing import Optional, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)

try:
    from flash_attn import flash_attn_func, flash_attn_varlen_func
    FLASH_ATTENTION_AVAILABLE = True
    logger.info("✅ Flash Attention 2 available")
except ImportError:
    FLASH_ATTENTION_AVAILABLE = False
    logger.info("ℹ️ Optimized Mode: Flash Attention 2 not available (using standard attention)")


class FlashAttention(nn.Module):
    """
    Flash Attention 2 wrapper for EmpoorioLM.

    Provides high-performance attention computation with automatic
    fallback to standard attention when Flash Attention is not available.
    """

    def __init__(
        self,
        num_heads: int,
        head_dim: int,
        dropout: float = 0.0,
        causal: bool = True,
        use_varlen: bool = False
    ):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.dropout = dropout
        self.causal = causal
        self.use_varlen = use_varlen

        # Check if we can use Flash Attention
        self.use_flash = FLASH_ATTENTION_AVAILABLE and torch.cuda.is_available()

        if self.use_flash:
            logger.info(f"🚀 Using Flash Attention 2: {num_heads} heads, {head_dim} head_dim")
        else:
            logger.info("🔄 Using standard attention (Flash Attention not available)")

    def forward(
        self,
        q: torch.Tensor,  # [batch_size, num_heads, seq_len, head_dim]
        k: torch.Tensor,  # [batch_size, num_heads, seq_len, head_dim]
        v: torch.Tensor,  # [batch_size, num_heads, seq_len, head_dim]
        attention_mask: Optional[torch.Tensor] = None,
        cu_seqlens_q: Optional[torch.Tensor] = None,
        cu_seqlens_k: Optional[torch.Tensor] = None,
        max_seqlen_q: Optional[int] = None,
        max_seqlen_k: Optional[int] = None
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        Compute attention using Flash Attention 2 or fallback.

        Args:
            q: Query tensor
            k: Key tensor
            v: Value tensor
            attention_mask: Attention mask (not used in Flash Attention)
            cu_seqlens_q: Cumulative sequence lengths for variable length (optional)
            cu_seqlens_k: Cumulative sequence lengths for variable length (optional)
            max_seqlen_q: Maximum sequence length for queries
            max_seqlen_k: Maximum sequence length for keys

        Returns:
            Tuple of (output, attention_weights)
        """
        if self.use_flash:
            return self._flash_attention_forward(
                q, k, v, cu_seqlens_q, cu_seqlens_k, max_seqlen_q, max_seqlen_k
            )
        else:
            return self._standard_attention_forward(q, k, v, attention_mask)

    def _flash_attention_forward(
        self,
        q: torch.Tensor,
        k: torch.Tensor,
        v: torch.Tensor,
        cu_seqlens_q: Optional[torch.Tensor] = None,
        cu_seqlens_k: Optional[torch.Tensor] = None,
        max_seqlen_q: Optional[int] = None,
        max_seqlen_k: Optional[int] = None
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """Forward pass using Flash Attention 2."""
        try:
            # Flash Attention expects different tensor shapes
            # Convert from [batch, heads, seq, dim] to [batch, seq, heads, dim]
            q_fa = q.transpose(1, 2)  # [batch, seq, heads, dim]
            k_fa = k.transpose(1, 2)  # [batch, seq, heads, dim]
            v_fa = v.transpose(1, 2)  # [batch, seq, heads, dim]

            if self.use_varlen and cu_seqlens_q is not None and cu_seqlens_k is not None:
                # Variable length sequences
                output = flash_attn_varlen_func(
                    q_fa, k_fa, v_fa,
                    cu_seqlens_q=cu_seqlens_q,
                    cu_seqlens_k=cu_seqlens_k,
                    max_seqlen_q=max_seqlen_q,
                    max_seqlen_k=max_seqlen_k,
                    dropout_p=self.dropout,
                    causal=self.causal,
                    return_attn_probs=False
                )
            else:
                # Standard fixed-length sequences
                output = flash_attn_func(
                    q_fa, k_fa, v_fa,
                    dropout_p=self.dropout,
                    causal=self.causal,
                    return_attn_probs=False
                )

            # Convert back to expected shape [batch, heads, seq, dim]
            output = output.transpose(1, 2)

            return output, None  # Flash Attention doesn't return attention weights

        except Exception as e:
            logger.warning(f"⚠️  Flash Attention failed, falling back to standard attention: {e}")
            # Fallback to standard attention
            self.use_flash = False
            attention_mask = None  # Create causal mask if needed
            if self.causal:
                seq_len = q.shape[2]
                attention_mask = torch.triu(torch.ones(seq_len, seq_len), diagonal=1).bool()
                attention_mask = attention_mask.to(q.device)
            return self._standard_attention_forward(q, k, v, attention_mask)

    def _standard_attention_forward(
        self,
        q: torch.Tensor,  # [batch_size, num_heads, seq_len, head_dim]
        k: torch.Tensor,  # [batch_size, num_heads, seq_len, head_dim]
        v: torch.Tensor,  # [batch_size, num_heads, seq_len, head_dim]
        attention_mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """Fallback standard attention computation."""
        # Compute attention scores
        scale = 1.0 / math.sqrt(self.head_dim)
        attn_weights = torch.matmul(q, k.transpose(-2, -1)) * scale

        # Apply causal mask if needed
        if self.causal and attention_mask is None:
            seq_len = q.shape[2]
            causal_mask = torch.triu(torch.ones(seq_len, seq_len), diagonal=1).bool()
            causal_mask = causal_mask.to(q.device)
            attn_weights = torch.where(causal_mask, float('-inf'), attn_weights)

        # Apply attention mask
        if attention_mask is not None:
            if attention_mask.dtype == torch.bool:
                attn_weights = torch.where(attention_mask, float('-inf'), attn_weights)
            else:
                attn_weights = attn_weights + attention_mask

        # Softmax
        attn_weights = torch.softmax(attn_weights, dim=-1)

        # Apply dropout
        if self.dropout > 0.0:
            attn_weights = torch.dropout(attn_weights, p=self.dropout, train=self.training)

        # Apply attention
        output = torch.matmul(attn_weights, v)

        return output, attn_weights


class FlashAttentionConfig:
    """Configuration for Flash Attention."""

    def __init__(
        self,
        enable_flash_attention: bool = True,
        use_varlen: bool = False,
        dropout: float = 0.0,
        causal: bool = True
    ):
        self.enable_flash_attention = enable_flash_attention and FLASH_ATTENTION_AVAILABLE
        self.use_varlen = use_varlen
        self.dropout = dropout
        self.causal = causal

    def is_available(self) -> bool:
        """Check if Flash Attention is available and enabled."""
        return self.enable_flash_attention and FLASH_ATTENTION_AVAILABLE and torch.cuda.is_available()


def create_flash_attention(
    num_heads: int,
    head_dim: int,
    config: Optional[FlashAttentionConfig] = None
) -> FlashAttention:
    """
    Factory function to create Flash Attention instance.

    Args:
        num_heads: Number of attention heads
        head_dim: Dimension of each head
        config: Flash Attention configuration

    Returns:
        FlashAttention instance
    """
    if config is None:
        config = FlashAttentionConfig()

    return FlashAttention(
        num_heads=num_heads,
        head_dim=head_dim,
        dropout=config.dropout,
        causal=config.causal,
        use_varlen=config.use_varlen
    )


# Benchmarking utilities
def benchmark_flash_attention(
    batch_size: int = 1,
    seq_len: int = 1024,
    num_heads: int = 8,
    head_dim: int = 64,
    num_runs: int = 10
) -> Dict[str, Any]:
    """
    Benchmark Flash Attention vs Standard Attention.

    Returns:
        Dictionary with benchmark results
    """
    import time

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Create test tensors
    q = torch.randn(batch_size, num_heads, seq_len, head_dim, device=device)
    k = torch.randn(batch_size, num_heads, seq_len, head_dim, device=device)
    v = torch.randn(batch_size, num_heads, seq_len, head_dim, device=device)

    # Flash Attention
    flash_attn = FlashAttention(num_heads, head_dim, causal=True)
    flash_times = []

    for _ in range(num_runs):
        if torch.cuda.is_available():
            torch.cuda.synchronize()

        start_time = time.time()

        with torch.no_grad():
            _ = flash_attn(q, k, v)

        if torch.cuda.is_available():
            torch.cuda.synchronize()

        end_time = time.time()
        flash_times.append(end_time - start_time)

    # Standard Attention (manual implementation)
    standard_times = []
    scale = 1.0 / math.sqrt(head_dim)

    for _ in range(num_runs):
        if torch.cuda.is_available():
            torch.cuda.synchronize()

        start_time = time.time()

        with torch.no_grad():
            # Manual attention computation
            attn_weights = torch.matmul(q, k.transpose(-2, -1)) * scale
            causal_mask = torch.triu(torch.ones(seq_len, seq_len), diagonal=1).bool().to(device)
            attn_weights = torch.where(causal_mask, float('-inf'), attn_weights)
            attn_weights = torch.softmax(attn_weights, dim=-1)
            _ = torch.matmul(attn_weights, v)

        if torch.cuda.is_available():
            torch.cuda.synchronize()

        end_time = time.time()
        standard_times.append(end_time - start_time)

    # Calculate statistics
    if flash_times and standard_times:
        flash_avg = sum(flash_times) / len(flash_times)
        standard_avg = sum(standard_times) / len(standard_times)
        speedup = standard_avg / flash_avg if flash_avg > 0 else 0

        return {
            "flash_attention_available": FLASH_ATTENTION_AVAILABLE,
            "device": str(device),
            "batch_size": batch_size,
            "seq_len": seq_len,
            "num_heads": num_heads,
            "head_dim": head_dim,
            "flash_time_avg": flash_avg,
            "standard_time_avg": standard_avg,
            "speedup": speedup,
            "memory_efficient": flash_attn.use_flash,
            "num_runs": num_runs
        }
    else:
        return {
            "error": "Benchmarking failed - no timing data collected",
            "flash_attention_available": FLASH_ATTENTION_AVAILABLE,
            "device": str(device),
            "num_runs": num_runs
        }


if __name__ == "__main__":
    # Quick test and benchmark
    print("🧪 Flash Attention 2 Test")
    print("=" * 40)

    # Test basic functionality
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    batch_size, seq_len, num_heads, head_dim = 1, 512, 8, 64

    q = torch.randn(batch_size, num_heads, seq_len, head_dim, device=device)
    k = torch.randn(batch_size, num_heads, seq_len, head_dim, device=device)
    v = torch.randn(batch_size, num_heads, seq_len, head_dim, device=device)

    flash_attn = FlashAttention(num_heads, head_dim, causal=True)

    try:
        output, _ = flash_attn(q, k, v)
        print(f"✅ Flash Attention test passed: output shape {output.shape}")
    except Exception as e:
        print(f"❌ Flash Attention test failed: {e}")

    # Run benchmark
    print("\n📊 Benchmarking...")
    results = benchmark_flash_attention(batch_size, seq_len, num_heads, head_dim, 5)

    if "speedup" in results:
        print(f"✅ Flash Attention: {results['flash_time_avg']:.2f}s avg")
        print(f"🐌 Standard Attention: {results['standard_time_avg']:.3f}s avg")
        print(f"🚀 Speedup: {results['speedup']:.1f}x")
        print(f"💾 Memory Efficient: {results['memory_efficient']}")
    else:
        print(f"❌ Benchmark failed: {results.get('error', 'Unknown error')}")

    print(f"\n🔧 Flash Attention Available: {FLASH_ATTENTION_AVAILABLE}")
    print(f"🎯 CUDA Available: {torch.cuda.is_available()}")