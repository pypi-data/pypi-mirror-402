#!/usr/bin/env python3
"""
Continuum Memory System (CMS) Block - Core component of Nested Learning

Based on "Nested Learning: The Illusion of Deep Learning Architectures" (Google Research)
Implements continuum memory systems where memory is organized as a spectrum of modules
with different update frequencies, enabling efficient long-context processing.

Key Features:
- Multi-frequency memory updates (short-term to long-term)
- Sparse attention patterns for O(n) complexity
- Memory consolidation and pruning
- Hierarchical memory organization
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional, Any, Union
import math
import random


class MemoryModule(nn.Module):
    """
    Individual memory module within the continuum memory system.

    Each module has its own update frequency and memory characteristics.
    """

    def __init__(self,
                 embed_dim: int,
                 memory_size: int,
                 update_frequency: float,
                 memory_type: str = "dense"):
        super().__init__()
        self.embed_dim = embed_dim
        self.memory_size = memory_size
        self.update_frequency = update_frequency
        self.memory_type = memory_type

        # Memory storage
        if memory_type == "dense":
            self.memory = nn.Parameter(torch.randn(memory_size, embed_dim))
        elif memory_type == "sparse":
            # Sparse memory with fixed sparsity pattern
            self.memory = nn.Parameter(torch.randn(memory_size, embed_dim))
            self.sparsity_mask = self._create_sparsity_mask()
        elif memory_type == "associative":
            # Associative memory for pattern matching
            self.memory_keys = nn.Parameter(torch.randn(memory_size, embed_dim))
            self.memory_values = nn.Parameter(torch.randn(memory_size, embed_dim))

        # Update tracking
        self.last_update = 0
        self.access_count = 0
        self.memory_strength = torch.ones(memory_size)

        # Gating mechanism for selective updates
        self.update_gate = nn.Sequential(
            nn.Linear(embed_dim, embed_dim // 4),
            nn.ReLU(),
            nn.Linear(embed_dim // 4, 1),
            nn.Sigmoid()
        )

    def _create_sparsity_mask(self) -> torch.Tensor:
        """Create sparsity pattern for sparse memory."""
        # Create a block-sparse pattern (similar to BigBird)
        mask = torch.zeros(self.memory_size, self.embed_dim)

        # Local connections (diagonal blocks)
        block_size = min(32, self.embed_dim // 4)
        for i in range(0, self.memory_size, block_size):
            for j in range(0, self.embed_dim, block_size):
                end_i = min(i + block_size, self.memory_size)
                end_j = min(j + block_size, self.embed_dim)
                mask[i:end_i, j:end_j] = 1

        # Global connections (random sparse)
        global_sparsity = 0.1  # 10% density for global tokens
        global_mask = torch.rand(self.memory_size, self.embed_dim) < global_sparsity
        mask = torch.logical_or(mask, global_mask)

        return mask

    def should_update(self, global_step: int) -> bool:
        """Determine if this memory module should update."""
        steps_since_update = global_step - self.last_update
        min_steps = max(1, int(1.0 / self.update_frequency))

        # Probabilistic update based on frequency
        if random.random() < self.update_frequency:
            return True

        # Guarantee minimum update frequency
        return steps_since_update >= min_steps

    def forward(self, query: torch.Tensor, global_step: int) -> torch.Tensor:
        """Retrieve from memory based on query."""
        if self.memory_type == "dense":
            return self._dense_retrieval(query)
        elif self.memory_type == "sparse":
            return self._sparse_retrieval(query)
        elif self.memory_type == "associative":
            return self._associative_retrieval(query)

        # Update access statistics
        self.access_count += 1
        return query  # Pass-through if unknown type

    def _dense_retrieval(self, query: torch.Tensor) -> torch.Tensor:
        """Dense memory retrieval using attention."""
        # query: (batch_size, seq_len, embed_dim)
        batch_size, seq_len, _ = query.shape

        # Compute attention scores
        # query: (batch_size, seq_len, embed_dim)
        # memory: (memory_size, embed_dim)
        # scores: (batch_size, seq_len, memory_size)
        scores = torch.matmul(query, self.memory.t()) / math.sqrt(self.embed_dim)

        # Apply softmax and retrieve
        attention_weights = F.softmax(scores, dim=-1)
        retrieved = torch.matmul(attention_weights, self.memory)

        # Residual connection
        return query + retrieved

    def _sparse_retrieval(self, query: torch.Tensor) -> torch.Tensor:
        """Sparse memory retrieval for efficiency."""
        # Apply sparsity mask to memory
        sparse_memory = self.memory * self.sparsity_mask.to(self.memory.device)

        # Compute sparse attention
        scores = torch.matmul(query, sparse_memory.t()) / math.sqrt(self.embed_dim)
        attention_weights = F.softmax(scores, dim=-1)
        retrieved = torch.matmul(attention_weights, sparse_memory)

        return query + retrieved

    def _associative_retrieval(self, query: torch.Tensor) -> torch.Tensor:
        """Associative memory retrieval using key-value pairs."""
        # Compute similarity with keys
        scores = torch.matmul(query, self.memory_keys.t()) / math.sqrt(self.embed_dim)
        attention_weights = F.softmax(scores, dim=-1)

        # Retrieve values
        retrieved = torch.matmul(attention_weights, self.memory_values)

        return query + retrieved

    def update_memory(self, keys: torch.Tensor, values: torch.Tensor, global_step: int):
        """Update memory with new key-value pairs."""
        if not self.should_update(global_step):
            return

        # Selective update based on gating
        gate_values = self.update_gate(keys.mean(dim=1))  # (batch_size, 1)
        update_mask = gate_values.squeeze(-1) > 0.5

        if update_mask.any():
            # Update memory entries where gate allows
            with torch.no_grad():
                if self.memory_type == "dense":
                    # Simple memory update (could be more sophisticated)
                    update_indices = torch.randperm(self.memory_size)[:keys.shape[0]]
                    self.memory.data[update_indices] = keys[update_mask[:len(update_indices)]]

                elif self.memory_type == "associative":
                    # Update key-value pairs
                    update_indices = torch.randperm(self.memory_size)[:keys.shape[0]]
                    self.memory_keys.data[update_indices] = keys[update_mask[:len(update_indices)]]
                    self.memory_values.data[update_indices] = values[update_mask[:len(update_indices)]]

                # Update memory strength
                self.memory_strength[update_indices] += 0.1
                self.memory_strength.clamp_(0.1, 1.0)

        self.last_update = global_step

    def consolidate_memory(self):
        """Consolidate memory based on usage and strength."""
        with torch.no_grad():
            # Age-based decay (simulate forgetting)
            age_decay = torch.exp(-torch.arange(self.memory_size, dtype=torch.float) * 0.001)
            self.memory_strength *= age_decay.to(self.memory.device)

            # Usage-based strengthening
            usage_boost = 1.0 + (self.access_count / 1000.0)  # Boost based on access frequency
            self.memory_strength *= usage_boost

            # Clamp to reasonable range
            self.memory_strength.clamp_(0.1, 1.0)

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory module statistics."""
        return {
            'memory_type': self.memory_type,
            'memory_size': self.memory_size,
            'update_frequency': self.update_frequency,
            'last_update': self.last_update,
            'access_count': self.access_count,
            'avg_memory_strength': self.memory_strength.mean().item(),
            'active_memories': (self.memory_strength > 0.5).sum().item()
        }


class CMSBlock(nn.Module):
    """
    Continuum Memory System Block - The heart of Nested Learning memory architecture.

    Implements a spectrum of memory modules with different update frequencies,
    enabling efficient processing of both short-term and long-term dependencies.
    """

    def __init__(self,
                 embed_dim: int,
                 num_memory_modules: int = 4,
                 memory_sizes: Optional[List[int]] = None,
                 update_frequencies: Optional[List[float]] = None,
                 memory_types: Optional[List[str]] = None):
        super().__init__()

        self.embed_dim = embed_dim
        self.num_memory_modules = num_memory_modules

        # Default configurations for memory modules
        if memory_sizes is None:
            # Exponentially increasing memory sizes
            memory_sizes = [256, 512, 1024, 2048][:num_memory_modules]

        if update_frequencies is None:
            # Exponentially decreasing update frequencies
            update_frequencies = [1.0, 0.1, 0.01, 0.001][:num_memory_modules]

        if memory_types is None:
            # Mix of memory types for different timescales
            memory_types = ["dense", "sparse", "associative", "dense"][:num_memory_modules]

        # Create memory modules
        self.memory_modules = nn.ModuleList([
            MemoryModule(embed_dim, memory_sizes[i], update_frequencies[i], memory_types[i])
            for i in range(num_memory_modules)
        ])

        # Cross-module communication (context flow)
        self.cross_module_communication = self._create_cross_module_communication()

        # Global step tracking
        self.global_step = 0

        # Memory statistics
        self.memory_stats_history = []

    def _create_cross_module_communication(self) -> nn.ModuleDict:
        """Create communication channels between memory modules."""
        communication = nn.ModuleDict()

        # Create communication matrices between adjacent modules
        for i in range(self.num_memory_modules - 1):
            comm_matrix = nn.Linear(self.embed_dim, self.embed_dim, bias=False)
            nn.init.xavier_uniform_(comm_matrix.weight, gain=0.1)
            communication[f"module_{i}_to_{i+1}"] = comm_matrix

        return communication

    def forward(self, x: torch.Tensor, context_flow: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Process input through continuum memory system.

        Args:
            x: Input tensor of shape (batch_size, seq_len, embed_dim)
            context_flow: Optional context flow from previous layers

        Returns:
            Processed tensor with memory-enhanced representations
        """
        self.global_step += 1
        batch_size, seq_len, _ = x.shape

        # Initialize context flow if not provided
        if context_flow is None:
            context_flow = torch.zeros_like(x)

        # Process through memory modules
        memory_outputs = []

        for i, memory_module in enumerate(self.memory_modules):
            # Combine input with context flow
            module_input = x + context_flow

            # Retrieve from memory
            memory_output = memory_module(module_input, self.global_step)
            memory_outputs.append(memory_output)

            # Update context flow for next module
            if i < self.num_memory_modules - 1:
                comm_key = f"module_{i}_to_{i+1}"
                if comm_key in self.cross_module_communication:
                    comm_matrix = self.cross_module_communication[comm_key]
                    # Transform through communication matrix
                    context_flow = comm_matrix(memory_output.mean(dim=1, keepdim=True))
                    context_flow = context_flow.unsqueeze(1).expand(-1, seq_len, -1)

        # Combine all memory outputs (weighted combination)
        # Higher-level memories get higher weights for long-term dependencies
        weights = torch.softmax(torch.arange(self.num_memory_modules, dtype=torch.float), dim=0)
        weights = weights.to(x.device).view(1, 1, -1, 1)

        combined_memory = torch.stack(memory_outputs, dim=2)  # (batch, seq, modules, dim)
        combined_memory = combined_memory * weights
        combined_memory = combined_memory.sum(dim=2)  # (batch, seq, dim)

        # Final output combines original input with memory-enhanced representation
        output = x + combined_memory

        return output

    def update_memories(self, keys: torch.Tensor, values: torch.Tensor):
        """
        Update all memory modules with new information.

        Args:
            keys: Key tensors for memory updates
            values: Value tensors for memory updates
        """
        for memory_module in self.memory_modules:
            memory_module.update_memory(keys, values, self.global_step)

    def consolidate_all_memories(self):
        """Consolidate all memory modules."""
        for memory_module in self.memory_modules:
            memory_module.consolidate_memory()

    def get_cms_stats(self) -> Dict[str, Any]:
        """Get comprehensive CMS statistics."""
        module_stats = [module.get_memory_stats() for module in self.memory_modules]

        return {
            'global_step': self.global_step,
            'num_memory_modules': self.num_memory_modules,
            'module_stats': module_stats,
            'total_memory_size': sum(stat['memory_size'] for stat in module_stats),
            'avg_memory_strength': sum(stat['avg_memory_strength'] for stat in module_stats) / len(module_stats),
            'total_access_count': sum(stat['access_count'] for stat in module_stats)
        }

    def save_cms_state(self, path: str):
        """Save CMS state to file."""
        state = {
            'global_step': self.global_step,
            'memory_stats_history': self.memory_stats_history[-100:],  # Keep last 100 entries
            'communication_weights': {
                name: module.weight.data for name, module in self.cross_module_communication.items()
            }
        }
        torch.save(state, path)

    def load_cms_state(self, path: str):
        """Load CMS state from file."""
        state = torch.load(path)
        self.global_step = state['global_step']
        self.memory_stats_history = state['memory_stats_history']

        # Load communication weights
        for name, weight in state['communication_weights'].items():
            if name in self.cross_module_communication:
                self.cross_module_communication[name].weight.data = weight


class AdaptiveCMSBlock(CMSBlock):
    """
    Adaptive CMS Block with dynamic memory allocation and frequency adjustment.

    Extends CMSBlock with automatic adaptation based on task requirements
    and resource availability.
    """

    def __init__(self, embed_dim: int, num_memory_modules: int = 4, adaptation_rate: float = 0.01):
        super().__init__(embed_dim, num_memory_modules)
        self.adaptation_rate = adaptation_rate
        self.task_history = []

    def adapt_to_task(self, task_complexity: float, resource_availability: float):
        """
        Adapt memory configuration based on task requirements.

        Args:
            task_complexity: Measure of task complexity (0-1)
            resource_availability: Available memory resources (0-1)
        """
        # Adapt update frequencies based on task complexity
        for i, module in enumerate(self.memory_modules):
            if task_complexity > 0.7:  # Complex task - increase high-frequency updates
                if i < self.num_memory_modules // 2:
                    module.update_frequency = min(1.0, module.update_frequency * (1 + self.adaptation_rate))
                else:
                    module.update_frequency = max(0.001, module.update_frequency * (1 - self.adaptation_rate))
            else:  # Simple task - focus on consolidation
                if i >= self.num_memory_modules // 2:
                    module.update_frequency = min(1.0, module.update_frequency * (1 + self.adaptation_rate))

        # Adapt memory sizes based on resource availability
        if resource_availability < 0.5:  # Limited resources - reduce memory sizes
            for module in self.memory_modules:
                # This would trigger memory pruning/consolidation
                module.consolidate_memory()

        self.task_history.append({
            'step': self.global_step,
            'task_complexity': task_complexity,
            'resource_availability': resource_availability,
            'adapted_frequencies': [module.update_frequency for module in self.memory_modules]
        })


class HierarchicalCMS(nn.Module):
    """
    Hierarchical Continuum Memory System for multi-level Nested Learning.

    Organizes multiple CMS blocks in a hierarchy, enabling complex
    nested optimization across different levels of abstraction.
    """

    def __init__(self,
                 embed_dims: List[int],
                 num_blocks_per_level: List[int],
                 hierarchy_levels: int = 3):
        super().__init__()

        self.hierarchy_levels = hierarchy_levels
        self.embed_dims = embed_dims

        # Create hierarchical CMS blocks
        self.cms_hierarchy = nn.ModuleList()
        for level in range(hierarchy_levels):
            cms_block = CMSBlock(
                embed_dim=embed_dims[level],
                num_memory_modules=num_blocks_per_level[level]
            )
            self.cms_hierarchy.append(cms_block)

        # Inter-level communication
        self.inter_level_communication = self._create_inter_level_communication()

    def _create_inter_level_communication(self) -> nn.ModuleDict:
        """Create communication between hierarchy levels."""
        communication = nn.ModuleDict()

        for level in range(self.hierarchy_levels - 1):
            # Projection from level to level+1
            projection = nn.Linear(self.embed_dims[level], self.embed_dims[level + 1], bias=False)
            nn.init.xavier_uniform_(projection.weight, gain=0.1)
            communication[f"level_{level}_to_{level+1}"] = projection

        return communication

    def forward(self, inputs: List[torch.Tensor]) -> List[torch.Tensor]:
        """
        Process inputs through hierarchical CMS.

        Args:
            inputs: List of tensors, one for each hierarchy level

        Returns:
            List of processed tensors for each level
        """
        assert len(inputs) == self.hierarchy_levels, f"Expected {self.hierarchy_levels} inputs, got {len(inputs)}"

        outputs = []
        context_flow = None

        for level in range(self.hierarchy_levels):
            level_input = inputs[level]

            # Add context flow from previous level
            if context_flow is not None:
                level_input = level_input + context_flow

            # Process through CMS block
            level_output = self.cms_hierarchy[level](level_input)
            outputs.append(level_output)

            # Create context flow for next level
            if level < self.hierarchy_levels - 1:
                comm_key = f"level_{level}_to_{level+1}"
                if comm_key in self.inter_level_communication:
                    projection = self.inter_level_communication[comm_key]
                    # Project to next level's embedding dimension
                    context_flow = projection(level_output.mean(dim=1))

                    # Expand to sequence dimension
                    seq_len = inputs[level + 1].shape[1]
                    context_flow = context_flow.unsqueeze(1).expand(-1, seq_len, -1)

        return outputs

    def update_hierarchy(self, level_inputs: List[torch.Tensor], level_targets: List[torch.Tensor]):
        """Update all levels of the hierarchy."""
        for level in range(self.hierarchy_levels):
            self.cms_hierarchy[level].update_memories(level_inputs[level], level_targets[level])

    def consolidate_hierarchy(self):
        """Consolidate memories across all hierarchy levels."""
        for cms_block in self.cms_hierarchy:
            cms_block.consolidate_all_memories()