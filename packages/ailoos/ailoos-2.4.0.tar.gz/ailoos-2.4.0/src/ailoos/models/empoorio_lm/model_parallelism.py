#!/usr/bin/env python3
"""
Model Parallelism for EmpoorioLM
Distributed training and inference across multiple GPUs.
"""

import torch
import torch.nn as nn
import torch.distributed as dist
import torch.multiprocessing as mp
from typing import Dict, Any, Optional, List, Union
import os
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class ModelParallelConfig:
    """Configuration for model parallelism."""

    def __init__(self,
                 world_size: int = 1,
                 rank: int = 0,
                 backend: str = 'nccl',
                 master_addr: str = 'localhost',
                 master_port: str = '12355',
                 pipeline_chunks: int = 1,
                 tensor_parallel_size: int = 1,
                 data_parallel_size: int = 1):
        self.world_size = world_size
        self.rank = rank
        self.backend = backend
        self.master_addr = master_addr
        self.master_port = master_port
        self.pipeline_chunks = pipeline_chunks
        self.tensor_parallel_size = tensor_parallel_size
        self.data_parallel_size = data_parallel_size

        # Validate configuration
        assert self.world_size == self.tensor_parallel_size * self.data_parallel_size, \
            "world_size must equal tensor_parallel_size * data_parallel_size"


class TensorParallelGroup:
    """Manages tensor parallel groups for distributed operations."""

    def __init__(self, config: ModelParallelConfig):
        self.config = config
        self.tensor_parallel_group = None
        self.data_parallel_group = None
        self.pipeline_parallel_group = None

        self._create_groups()

    def _create_groups(self):
        """Create process groups for different parallelism types."""
        world_size = self.config.world_size
        tensor_parallel_size = self.config.tensor_parallel_size
        data_parallel_size = self.config.data_parallel_size

        # Create tensor parallel groups
        self.tensor_parallel_groups = []
        for i in range(data_parallel_size):
            group_ranks = [i * tensor_parallel_size + j for j in range(tensor_parallel_size)]
            group = dist.new_group(ranks=group_ranks)
            self.tensor_parallel_groups.append(group)

        # Create data parallel groups
        self.data_parallel_groups = []
        for i in range(tensor_parallel_size):
            group_ranks = [j * tensor_parallel_size + i for j in range(data_parallel_size)]
            group = dist.new_group(ranks=group_ranks)
            self.data_parallel_groups.append(group)

        # Set current process groups
        rank = self.config.rank
        tensor_group_idx = rank // tensor_parallel_size
        data_group_idx = rank % tensor_parallel_size

        self.tensor_parallel_group = self.tensor_parallel_groups[tensor_group_idx]
        self.data_parallel_group = self.data_parallel_groups[data_group_idx]

    def get_tensor_parallel_rank(self) -> int:
        """Get rank within tensor parallel group."""
        return self.config.rank % self.config.tensor_parallel_size

    def get_tensor_parallel_world_size(self) -> int:
        """Get world size of tensor parallel group."""
        return self.config.tensor_parallel_size

    def get_data_parallel_rank(self) -> int:
        """Get rank within data parallel group."""
        return self.config.rank // self.config.tensor_parallel_size

    def get_data_parallel_world_size(self) -> int:
        """Get world size of data parallel group."""
        return self.config.data_parallel_size


class ColumnParallelLinear(nn.Module):
    """Linear layer with column parallelism."""

    def __init__(self, input_size: int, output_size: int, bias: bool = True,
                 gather_output: bool = True, tp_group: Optional[TensorParallelGroup] = None):
        super().__init__()
        self.input_size = input_size
        self.output_size = output_size
        self.gather_output = gather_output
        self.tp_group = tp_group

        if tp_group is not None:
            tp_rank = tp_group.get_tensor_parallel_rank()
            tp_world_size = tp_group.get_tensor_parallel_world_size()

            # Split output dimension across tensor parallel ranks
            assert output_size % tp_world_size == 0, "output_size must be divisible by tensor_parallel_world_size"
            self.output_size_per_partition = output_size // tp_world_size
        else:
            self.output_size_per_partition = output_size

        self.linear = nn.Linear(input_size, self.output_size_per_partition, bias=bias)

    def forward(self, input_: torch.Tensor) -> torch.Tensor:
        """Forward pass with optional output gathering."""
        output = self.linear(input_)

        if self.tp_group is not None and self.gather_output:
            # Gather outputs from all tensor parallel ranks
            output_list = [torch.empty_like(output) for _ in range(self.tp_group.get_tensor_parallel_world_size())]
            dist.all_gather(output_list, output, group=self.tp_group.tensor_parallel_group)
            output = torch.cat(output_list, dim=-1)

        return output


class RowParallelLinear(nn.Module):
    """Linear layer with row parallelism."""

    def __init__(self, input_size: int, output_size: int, bias: bool = True,
                 input_is_parallel: bool = False, tp_group: Optional[TensorParallelGroup] = None):
        super().__init__()
        self.input_size = input_size
        self.output_size = output_size
        self.input_is_parallel = input_is_parallel
        self.tp_group = tp_group

        if tp_group is not None:
            tp_rank = tp_group.get_tensor_parallel_rank()
            tp_world_size = tp_group.get_tensor_parallel_world_size()

            # Split input dimension across tensor parallel ranks
            assert input_size % tp_world_size == 0, "input_size must be divisible by tensor_parallel_world_size"
            self.input_size_per_partition = input_size // tp_world_size
        else:
            self.input_size_per_partition = input_size

        self.linear = nn.Linear(self.input_size_per_partition, output_size, bias=bias)

    def forward(self, input_: torch.Tensor) -> torch.Tensor:
        """Forward pass with optional input reduction."""
        if self.tp_group is not None and not self.input_is_parallel:
            # Split input across tensor parallel ranks
            tp_world_size = self.tp_group.get_tensor_parallel_world_size()
            input_list = torch.chunk(input_, tp_world_size, dim=-1)
            input_parallel = input_list[self.tp_group.get_tensor_parallel_rank()]
        else:
            input_parallel = input_

        output = self.linear(input_parallel)

        if self.tp_group is not None:
            # Reduce outputs across tensor parallel ranks
            dist.all_reduce(output, group=self.tp_group.tensor_parallel_group)

        return output


class ParallelEmbedding(nn.Module):
    """Embedding layer with tensor parallelism."""

    def __init__(self, num_embeddings: int, embedding_dim: int,
                 tp_group: Optional[TensorParallelGroup] = None):
        super().__init__()
        self.num_embeddings = num_embeddings
        self.embedding_dim = embedding_dim
        self.tp_group = tp_group

        if tp_group is not None:
            tp_world_size = tp_group.get_tensor_parallel_world_size()
            assert embedding_dim % tp_world_size == 0, "embedding_dim must be divisible by tensor_parallel_world_size"
            self.embedding_dim_per_partition = embedding_dim // tp_world_size
        else:
            self.embedding_dim_per_partition = embedding_dim

        self.embedding = nn.Embedding(num_embeddings, self.embedding_dim_per_partition)

    def forward(self, input_: torch.Tensor) -> torch.Tensor:
        """Forward pass with optional output gathering."""
        output = self.embedding(input_)

        if self.tp_group is not None:
            # Gather outputs from all tensor parallel ranks
            output_list = [torch.empty_like(output) for _ in range(self.tp_group.get_tensor_parallel_world_size())]
            dist.all_gather(output_list, output, group=self.tp_group.tensor_parallel_group)
            output = torch.cat(output_list, dim=-1)

        return output


class ModelParallelTransformerBlock(nn.Module):
    """Transformer block with model parallelism support."""

    def __init__(self, config, layer_idx: int = 0, tp_group: Optional[TensorParallelGroup] = None):
        super().__init__()
        self.layer_idx = layer_idx
        self.tp_group = tp_group

        # Layer norms (replicated across all ranks)
        self.ln1 = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
        self.ln2 = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)

        # Attention with tensor parallelism
        self.attn = ParallelAttention(config, tp_group=tp_group)

        # Feed-forward with tensor parallelism
        if config.use_moe and layer_idx in config.moe_layers:
            # MoE layer with parallelism
            self.ffn = ParallelMoELayer(config, tp_group=tp_group)
        else:
            # Standard MLP with parallelism
            self.ffn = ParallelMLP(config, tp_group=tp_group)

    def forward(self, hidden_states: torch.Tensor, attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        # Pre-norm architecture
        residual = hidden_states
        hidden_states = self.ln1(hidden_states)
        attn_output = self.attn(hidden_states, attention_mask)
        hidden_states = residual + attn_output

        # Feed-forward
        residual = hidden_states
        hidden_states = self.ln2(hidden_states)
        ffn_output = self.ffn(hidden_states)
        hidden_states = residual + ffn_output

        return hidden_states


class ParallelAttention(nn.Module):
    """Multi-head attention with tensor parallelism."""

    def __init__(self, config, tp_group: Optional[TensorParallelGroup] = None):
        super().__init__()
        self.num_heads = config.num_heads
        self.hidden_size = config.hidden_size
        self.head_dim = config.hidden_size // config.num_heads
        self.tp_group = tp_group

        if tp_group is not None:
            tp_world_size = tp_group.get_tensor_parallel_world_size()
            assert config.num_heads % tp_world_size == 0, "num_heads must be divisible by tensor_parallel_world_size"
            self.num_heads_per_partition = config.num_heads // tp_world_size
        else:
            self.num_heads_per_partition = config.num_heads

        # Parallel linear layers
        self.q_proj = ColumnParallelLinear(config.hidden_size, config.hidden_size, tp_group=tp_group)
        self.k_proj = ColumnParallelLinear(config.hidden_size, config.hidden_size, tp_group=tp_group)
        self.v_proj = ColumnParallelLinear(config.hidden_size, config.hidden_size, tp_group=tp_group)
        self.out_proj = RowParallelLinear(config.hidden_size, config.hidden_size, tp_group=tp_group)

        self.dropout = nn.Dropout(config.dropout)

    def forward(self, hidden_states: torch.Tensor, attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        batch_size, seq_len, _ = hidden_states.size()

        # Apply projections
        q = self.q_proj(hidden_states).view(batch_size, seq_len, self.num_heads_per_partition, self.head_dim)
        k = self.k_proj(hidden_states).view(batch_size, seq_len, self.num_heads_per_partition, self.head_dim)
        v = self.v_proj(hidden_states).view(batch_size, seq_len, self.num_heads_per_partition, self.head_dim)

        # Transpose for attention computation
        q = q.transpose(1, 2)  # [batch, heads, seq, dim]
        k = k.transpose(1, 2)
        v = v.transpose(1, 2)

        # Scaled dot-product attention
        scale = 1.0 / (self.head_dim ** 0.5)
        attn_weights = torch.matmul(q, k.transpose(-2, -1)) * scale

        if attention_mask is not None:
            attn_weights = attn_weights + attention_mask

        attn_weights = torch.softmax(attn_weights, dim=-1)
        attn_weights = self.dropout(attn_weights)

        attn_output = torch.matmul(attn_weights, v)

        # Transpose back and reshape
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.view(batch_size, seq_len, self.num_heads_per_partition * self.head_dim)

        # Output projection
        output = self.out_proj(attn_output)

        return output


class ParallelMLP(nn.Module):
    """MLP with tensor parallelism."""

    def __init__(self, config, tp_group: Optional[TensorParallelGroup] = None):
        super().__init__()
        self.tp_group = tp_group

        # Parallel linear layers
        self.fc1 = ColumnParallelLinear(config.hidden_size, 4 * config.hidden_size, tp_group=tp_group)
        self.fc2 = RowParallelLinear(4 * config.hidden_size, config.hidden_size, tp_group=tp_group)

        self.act = nn.GELU()
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        hidden_states = self.fc1(hidden_states)
        hidden_states = self.act(hidden_states)
        hidden_states = self.dropout(hidden_states)
        hidden_states = self.fc2(hidden_states)
        hidden_states = self.dropout(hidden_states)
        return hidden_states


class ParallelMoELayer(nn.Module):
    """MoE layer with tensor parallelism support."""

    def __init__(self, config, tp_group: Optional[TensorParallelGroup] = None):
        super().__init__()
        self.config = config
        self.tp_group = tp_group

        # Router (replicated across all ranks)
        self.router = nn.Linear(config.hidden_size, config.num_experts)

        # Expert networks with tensor parallelism
        self.experts = nn.ModuleList([
            ParallelMLP(config, tp_group=tp_group) for _ in range(config.num_experts)
        ])

        # Shared expert (optional)
        self.shared_expert = ParallelMLP(config, tp_group=tp_group)

        self.top_k = config.top_k
        self.load_balance_weight = config.load_balance_weight

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        batch_size, seq_len, hidden_size = hidden_states.size()

        # Compute routing logits
        routing_logits = self.router(hidden_states.view(-1, hidden_size))
        routing_probs = torch.softmax(routing_logits, dim=-1)

        # Select top-k experts
        top_k_probs, top_k_indices = torch.topk(routing_probs, self.top_k, dim=-1)

        # Normalize probabilities
        top_k_probs = top_k_probs / top_k_probs.sum(dim=-1, keepdim=True)

        # Compute expert outputs
        expert_outputs = []
        for i, expert in enumerate(self.experts):
            expert_mask = (top_k_indices == i).any(dim=-1)
            if expert_mask.any():
                expert_input = hidden_states.view(-1, hidden_size)[expert_mask]
                expert_output = expert(expert_input)
                expert_outputs.append((expert_output, expert_mask))
            else:
                expert_outputs.append((torch.empty(0, hidden_size, device=hidden_states.device), expert_mask))

        # Combine expert outputs
        combined_output = torch.zeros_like(hidden_states.view(-1, hidden_size))

        for i, (expert_output, expert_mask) in enumerate(expert_outputs):
            if expert_mask.any():
                expert_probs = top_k_probs[expert_mask, top_k_indices[expert_mask].eq(i).nonzero(as_tuple=True)[1]]
                combined_output[expert_mask] += expert_output * expert_probs.unsqueeze(-1)

        # Add shared expert
        shared_output = self.shared_expert(hidden_states)
        combined_output += shared_output.view(-1, hidden_size)

        return combined_output.view(batch_size, seq_len, hidden_size)


class ModelParallelEmpoorioLM(nn.Module):
    """EmpoorioLM with model parallelism support."""

    def __init__(self, config, mp_config: ModelParallelConfig):
        super().__init__()
        self.config = config
        self.mp_config = mp_config

        # Initialize tensor parallel group
        self.tp_group = TensorParallelGroup(mp_config)

        # Parallel embeddings
        self.embed_tokens = ParallelEmbedding(config.vocab_size, config.hidden_size, tp_group=self.tp_group)

        # Position embeddings (if not using RoPE)
        if not config.use_rope:
            self.embed_positions = ParallelEmbedding(config.max_position_embeddings, config.hidden_size, tp_group=self.tp_group)
        else:
            self.embed_positions = None

        self.dropout = nn.Dropout(config.dropout)

        # Parallel transformer blocks
        self.blocks = nn.ModuleList([
            ModelParallelTransformerBlock(config, layer_idx=i, tp_group=self.tp_group)
            for i in range(config.num_layers)
        ])

        # Final layer norm
        self.ln_f = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)

        # LM head (tied with embeddings)
        self.lm_head = ColumnParallelLinear(config.hidden_size, config.vocab_size, bias=False, tp_group=self.tp_group)
        # Weight tying would need special handling in parallel setup

    def forward(self, input_ids: torch.Tensor, attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        # Embeddings
        token_embeds = self.embed_tokens(input_ids)

        if self.embed_positions is not None:
            position_ids = torch.arange(input_ids.size(1), device=input_ids.device).unsqueeze(0)
            position_embeds = self.embed_positions(position_ids)
            hidden_states = token_embeds + position_embeds
        else:
            hidden_states = token_embeds

        hidden_states = self.dropout(hidden_states)

        # Transformer blocks
        for block in self.blocks:
            hidden_states = block(hidden_states, attention_mask)

        # Final layer norm
        hidden_states = self.ln_f(hidden_states)

        # LM head
        logits = self.lm_head(hidden_states)

        return logits


def setup_model_parallel(mp_config: ModelParallelConfig) -> None:
    """Setup distributed training environment."""
    os.environ['MASTER_ADDR'] = mp_config.master_addr
    os.environ['MASTER_PORT'] = mp_config.master_port

    # Initialize process group
    dist.init_process_group(
        backend=mp_config.backend,
        rank=mp_config.rank,
        world_size=mp_config.world_size
    )

    # Set device
    torch.cuda.set_device(mp_config.rank)

    logger.info(f"Model parallelism initialized: rank {mp_config.rank}/{mp_config.world_size}")


def cleanup_model_parallel() -> None:
    """Clean up distributed training environment."""
    dist.destroy_process_group()


@contextmanager
def model_parallel_context(mp_config: ModelParallelConfig):
    """Context manager for model parallelism."""
    try:
        setup_model_parallel(mp_config)
        yield
    finally:
        cleanup_model_parallel()


def create_parallel_model(config, mp_config: ModelParallelConfig) -> ModelParallelEmpoorioLM:
    """Factory function to create model parallel EmpoorioLM."""
    return ModelParallelEmpoorioLM(config, mp_config)


# Utility functions for distributed training
def reduce_tensor(tensor: torch.Tensor, group: Optional[Any] = None) -> torch.Tensor:
    """Reduce tensor across all processes."""
    if dist.is_initialized():
        dist.all_reduce(tensor, group=group)
    return tensor


def gather_tensor(tensor: torch.Tensor, dst: int = 0, group: Optional[Any] = None) -> torch.Tensor:
    """Gather tensor from all processes to destination rank."""
    if dist.is_initialized():
        gathered_list = [torch.empty_like(tensor) for _ in range(dist.get_world_size(group))]
        dist.all_gather(gathered_list, tensor, group=group)
        return torch.cat(gathered_list, dim=0) if dist.get_rank(group) == dst else tensor
    return tensor


def scatter_tensor(tensor: torch.Tensor, src: int = 0, group: Optional[Any] = None) -> torch.Tensor:
    """Scatter tensor from source rank to all processes."""
    if dist.is_initialized():
        world_size = dist.get_world_size(group)
        scattered_list = torch.chunk(tensor, world_size, dim=0)
        return scattered_list[dist.get_rank(group)]
    return tensor