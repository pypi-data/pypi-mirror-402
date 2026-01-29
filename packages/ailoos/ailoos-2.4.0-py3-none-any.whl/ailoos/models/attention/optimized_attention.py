"""
Optimized Attention Engine using PyTorch SDPA
==============================================

High-performance attention implementation using PyTorch's native Scaled Dot Product Attention (SDPA).
Automatically selects the best available kernel based on hardware capabilities.

Features:
- Automatic kernel selection (Flash Attention 2, Memory Efficient, or Math)
- Hardware-aware optimization for CPU, MPS, and CUDA
- Causal and non-causal attention support
- Dropout and attention masking
- Compatible with existing attention interfaces

Author: AILOOS Team
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import logging
from typing import Optional, Tuple, Dict, Any
import math

logger = logging.getLogger(__name__)

class OptimizedAttentionEngine:
    """
    High-performance attention engine using PyTorch's SDPA.

    Automatically selects the best available kernel:
    - Flash Attention 2 on compatible NVIDIA GPUs
    - Memory Efficient Attention on older GPUs
    - Optimized Math implementation on CPU/MPS
    """

    @staticmethod
    def is_sdpa_available() -> bool:
        """Check if PyTorch SDPA is available."""
        return hasattr(F, 'scaled_dot_product_attention')

    @staticmethod
    def get_optimal_backend(device: torch.device) -> str:
        """Get the optimal attention backend for the given device."""
        if not torch.cuda.is_available():
            return "math"

        # Check PyTorch version for Flash Attention support
        torch_version = torch.__version__.split('.')
        major, minor = int(torch_version[0]), int(torch_version[1])

        if major >= 2:
            # PyTorch 2.0+ has Flash Attention support
            return "flash"
        else:
            return "mem_efficient"

    @staticmethod
    def forward(
        query: torch.Tensor,      # [batch_size, num_heads, seq_len, head_dim]
        key: torch.Tensor,        # [batch_size, num_heads, seq_len, head_dim]
        value: torch.Tensor,      # [batch_size, num_heads, seq_len, head_dim]
        attn_mask: Optional[torch.Tensor] = None,
        dropout_p: float = 0.0,
        is_causal: bool = True,
        scale: Optional[float] = None
    ) -> torch.Tensor:
        """
        Compute optimized attention using PyTorch SDPA.

        Args:
            query: Query tensor [batch, heads, seq_len, head_dim]
            key: Key tensor [batch, heads, seq_len, head_dim]
            value: Value tensor [batch, heads, seq_len, head_dim]
            attn_mask: Attention mask [batch, heads, seq_len_q, seq_len_k] or [seq_len_q, seq_len_k]
            dropout_p: Dropout probability
            is_causal: Whether to apply causal masking
            scale: Scale factor (if None, uses 1/sqrt(head_dim))

        Returns:
            Attention output [batch, heads, seq_len, head_dim]
        """
        if not OptimizedAttentionEngine.is_sdpa_available():
            logger.warning("PyTorch SDPA not available, falling back to manual attention")
            return OptimizedAttentionEngine._manual_attention(
                query, key, value, attn_mask, dropout_p, is_causal, scale
            )

        # Default scale
        if scale is None:
            scale = 1.0 / math.sqrt(query.size(-1))

        # Configure SDPA kernel selection
        device = query.device
        backend = OptimizedAttentionEngine.get_optimal_backend(device)

        # Set kernel preferences based on backend
        if backend == "flash":
            # Prefer Flash Attention 2, fallback to memory efficient
            sdp_kernel = torch.backends.cuda.sdp_kernel(
                enable_flash=True,
                enable_math=True,
                enable_mem_efficient=True
            )
        elif backend == "mem_efficient":
            # Prefer memory efficient, fallback to math
            sdp_kernel = torch.backends.cuda.sdp_kernel(
                enable_flash=False,
                enable_math=True,
                enable_mem_efficient=True
            )
        else:
            # CPU/MPS: use math implementation
            sdp_kernel = None

        try:
            with torch.backends.cuda.sdp_kernel(sdp_kernel) if sdp_kernel else torch.no_grad():
                output = F.scaled_dot_product_attention(
                    query,
                    key,
                    value,
                    attn_mask=attn_mask,
                    dropout_p=dropout_p,
                    is_causal=is_causal,
                    scale=scale
                )

            return output

        except RuntimeError as e:
            logger.warning(f"SDPA failed with {backend} backend: {e}")
            logger.info("Falling back to manual attention implementation")
            return OptimizedAttentionEngine._manual_attention(
                query, key, value, attn_mask, dropout_p, is_causal, scale
            )

    @staticmethod
    def _manual_attention(
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        attn_mask: Optional[torch.Tensor],
        dropout_p: float,
        is_causal: bool,
        scale: float
    ) -> torch.Tensor:
        """
        Fallback manual attention implementation.
        """
        # Compute attention scores
        attn_weights = torch.matmul(query, key.transpose(-2, -1)) * scale

        # Apply causal mask if requested
        if is_causal:
            seq_len = query.size(-2)
            causal_mask = torch.triu(torch.ones(seq_len, seq_len, device=query.device), diagonal=1).bool()
            attn_weights = torch.where(causal_mask, float('-inf'), attn_weights)

        # Apply attention mask if provided
        if attn_mask is not None:
            attn_weights = attn_weights + attn_mask

        # Softmax
        attn_weights = F.softmax(attn_weights, dim=-1)

        # Apply dropout
        if dropout_p > 0.0:
            attn_weights = F.dropout(attn_weights, p=dropout_p, training=True)

        # Apply attention
        output = torch.matmul(attn_weights, value)

        return output

    @staticmethod
    def benchmark_attention(
        batch_size: int = 1,
        seq_len: int = 1024,
        num_heads: int = 8,
        head_dim: int = 64,
        num_runs: int = 10,
        device: str = "auto"
    ) -> Dict[str, Any]:
        """
        Benchmark the optimized attention implementation.

        Returns:
            Dictionary with benchmark results
        """
        if device == "auto":
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            device = torch.device(device)

        # Create test tensors
        query = torch.randn(batch_size, num_heads, seq_len, head_dim, device=device)
        key = torch.randn(batch_size, num_heads, seq_len, head_dim, device=device)
        value = torch.randn(batch_size, num_heads, seq_len, head_dim, device=device)

        # Warmup
        for _ in range(3):
            _ = OptimizedAttentionEngine.forward(query, key, value, is_causal=True)

        # Benchmark
        import time
        times = []

        for _ in range(num_runs):
            torch.cuda.synchronize() if torch.cuda.is_available() else None
            start_time = time.time()

            _ = OptimizedAttentionEngine.forward(query, key, value, is_causal=True)

            torch.cuda.synchronize() if torch.cuda.is_available() else None
            end_time = time.time()
            times.append(end_time - start_time)

        avg_time = sum(times) / len(times)
        backend = OptimizedAttentionEngine.get_optimal_backend(device)

        return {
            "backend": backend,
            "device": str(device),
            "batch_size": batch_size,
            "seq_len": seq_len,
            "num_heads": num_heads,
            "head_dim": head_dim,
            "avg_time": avg_time,
            "num_runs": num_runs,
            "sdpa_available": OptimizedAttentionEngine.is_sdpa_available(),
            "tokens_per_second": (batch_size * seq_len) / avg_time
        }


class OptimizedAttention(nn.Module):
    """
    Drop-in replacement for attention layers using optimized SDPA.
    """

    def __init__(
        self,
        num_heads: int,
        head_dim: int,
        dropout: float = 0.0,
        bias: bool = True
    ):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.dropout = dropout

        # Check if we can use optimized attention
        self.use_optimized = OptimizedAttentionEngine.is_sdpa_available()

        if self.use_optimized:
            backend = OptimizedAttentionEngine.get_optimal_backend(torch.device('cuda' if torch.cuda.is_available() else 'cpu'))
            logger.info(f"🚀 Using Optimized Attention with {backend} backend")
        else:
            logger.info("🔄 Using standard attention (SDPA not available)")

    def forward(
        self,
        query: torch.Tensor,  # [batch, seq, hidden] or [batch, heads, seq, dim]
        key: torch.Tensor,
        value: torch.Tensor,
        attn_mask: Optional[torch.Tensor] = None,
        is_causal: bool = True
    ) -> torch.Tensor:
        """
        Compute attention with automatic optimization.
        """
        # Handle different input formats
        if query.dim() == 3:  # [batch, seq, hidden] - need to reshape
            batch_size, seq_len, hidden_size = query.size()
            query = query.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
            key = key.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
            value = value.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)

            needs_reshape = True
        else:
            needs_reshape = False

        # Apply optimized attention
        if self.use_optimized:
            output = OptimizedAttentionEngine.forward(
                query, key, value,
                attn_mask=attn_mask,
                dropout_p=self.dropout if self.training else 0.0,
                is_causal=is_causal
            )
        else:
            # Fallback to manual attention
            output = OptimizedAttentionEngine._manual_attention(
                query, key, value, attn_mask,
                self.dropout if self.training else 0.0,
                is_causal, 1.0 / math.sqrt(self.head_dim)
            )

        # Reshape back if needed
        if needs_reshape:
            output = output.transpose(1, 2).contiguous().view(batch_size, seq_len, hidden_size)

        return output


# Example usage and testing
if __name__ == "__main__":
    print("🧪 Optimized Attention Engine Test")
    print("=" * 50)

    # Test basic functionality
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    batch_size, seq_len, num_heads, head_dim = 1, 512, 8, 64

    query = torch.randn(batch_size, num_heads, seq_len, head_dim, device=device)
    key = torch.randn(batch_size, num_heads, seq_len, head_dim, device=device)
    value = torch.randn(batch_size, num_heads, seq_len, head_dim, device=device)

    print(f"📊 SDPA Available: {OptimizedAttentionEngine.is_sdpa_available()}")
    print(f"🎯 Optimal Backend: {OptimizedAttentionEngine.get_optimal_backend(device)}")
    print(f"🎮 Device: {device}")

    # Test forward pass
    try:
        output = OptimizedAttentionEngine.forward(query, key, value, is_causal=True)
        print("✅ Optimized Attention test passed")
        print(f"   Input shape: {query.shape}")
        print(f"   Output shape: {output.shape}")
    except Exception as e:
        print(f"❌ Optimized Attention test failed: {e}")

    # Run benchmark
    print("\n📊 Running Benchmark...")
    results = OptimizedAttentionEngine.benchmark_attention(
        batch_size=1, seq_len=512, num_heads=8, head_dim=64, num_runs=5
    )

    print("📈 Benchmark Results:")
    print(f"   Backend: {results['backend']}")
    print(f"   Device: {results['device']}")
    print(f"   Avg Time: {results['avg_time']:.4f}s")
    print(f"   Tokens/sec: {results['tokens_per_second']:.0f}")
    print(f"   SDPA Available: {results['sdpa_available']}")

    print("\n🎉 Optimized Attention Engine is ready!")