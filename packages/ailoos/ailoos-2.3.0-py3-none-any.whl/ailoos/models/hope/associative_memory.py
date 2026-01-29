#!/usr/bin/env python3
"""
Associative Memory Module - Core component of Nested Learning

Based on "Nested Learning: The Illusion of Deep Learning Architectures" (Google Research)
Implements associative memory for storing and retrieving neural activation patterns.

Key Features:
- Dot-product similarity for pattern matching
- L2 regression loss for better optimization
- Memory consolidation and pruning
- Efficient retrieval of similar patterns
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional, Any
import math


class AssociativeMemory(nn.Module):
    """
    Associative Memory Module for Nested Learning

    Stores and retrieves neural activation patterns using dot-product similarity.
    Implements the associative memory concept from the Nested Learning paper.
    """

    def __init__(self, input_dim: int, memory_size: int, similarity_threshold: float = 0.8):
        super().__init__()
        self.input_dim = input_dim
        self.memory_size = memory_size
        self.similarity_threshold = similarity_threshold

        # Memory matrix: stores patterns as rows
        self.memory_matrix = nn.Parameter(torch.randn(memory_size, input_dim))
        self.memory_values = nn.Parameter(torch.randn(memory_size, 1))  # Associated values/losses

        # Memory usage tracking
        self.memory_age = torch.zeros(memory_size)  # How old each memory entry is
        self.memory_frequency = torch.zeros(memory_size)  # How often accessed
        self.memory_strength = torch.ones(memory_size)  # Memory consolidation strength

        # Gating mechanism for selective updates
        self.update_gate = nn.Sequential(
            nn.Linear(input_dim, input_dim // 4),
            nn.ReLU(),
            nn.Linear(input_dim // 4, 1),
            nn.Sigmoid()
        )

        # Initialize with small values for stability
        nn.init.xavier_uniform_(self.memory_matrix, gain=0.1)
        nn.init.normal_(self.memory_values, mean=0.0, std=0.1)

    def forward(self, query: torch.Tensor, return_similarities: bool = False) -> torch.Tensor:
        """
        Query the associative memory for similar patterns.

        Args:
            query: Input tensor of shape (batch_size, input_dim)
            return_similarities: Whether to return similarity scores

        Returns:
            Retrieved patterns or similarity scores
        """
        batch_size, _ = query.shape

        # Compute similarities: dot product between query and all memory entries
        # query: (batch_size, input_dim)
        # memory_matrix: (memory_size, input_dim)
        # similarities: (batch_size, memory_size)
        similarities = torch.matmul(query, self.memory_matrix.t()) / math.sqrt(self.input_dim)

        # Apply softmax to get attention weights
        attention_weights = F.softmax(similarities, dim=-1)

        # Retrieve weighted combination of memory values
        retrieved_values = torch.matmul(attention_weights, self.memory_values)

        # Update memory access statistics
        self._update_memory_stats(attention_weights)

        if return_similarities:
            return retrieved_values, similarities
        return retrieved_values

    def update(self, pattern: torch.Tensor, value: torch.Tensor, learning_rate: float = 0.01):
        """
        Update associative memory with new pattern-value pair.

        Uses L2 regression loss as described in the Nested Learning paper.

        Args:
            pattern: Input pattern tensor of shape (input_dim,)
            value: Associated value tensor of shape (1,)
            learning_rate: Learning rate for memory update
        """
        # Ensure tensors are on the same device
        device = self.memory_matrix.device
        pattern = pattern.to(device).unsqueeze(0)  # (1, input_dim)
        value = value.to(device).unsqueeze(0)  # (1, 1)

        # Compute current prediction
        current_prediction, similarities = self.forward(pattern, return_similarities=True)
        current_prediction = current_prediction.squeeze(0)  # (1,)

        # Compute L2 regression loss (as suggested in Nested Learning paper)
        loss = F.mse_loss(current_prediction, value.squeeze(0))

        # Compute gradients for memory update
        loss.backward(retain_graph=True)

        # Selective update based on gating mechanism
        gate_value = self.update_gate(pattern.squeeze(0))  # (1,)
        update_strength = gate_value.item()

        if update_strength > 0.5:  # Only update if gate allows it
            # Find most similar memory entry
            best_match_idx = similarities.argmax(dim=-1).item()

            # Update memory entry using gradient descent
            with torch.no_grad():
                # Update memory matrix (pattern storage)
                grad_matrix = self.memory_matrix.grad[best_match_idx] if self.memory_matrix.grad is not None else torch.zeros_like(self.memory_matrix[best_match_idx])
                self.memory_matrix[best_match_idx] -= learning_rate * grad_matrix * update_strength

                # Update memory values
                grad_values = self.memory_values.grad[best_match_idx] if self.memory_values.grad is not None else torch.zeros_like(self.memory_values[best_match_idx])
                self.memory_values[best_match_idx] -= learning_rate * grad_values * update_strength

                # Update memory strength (consolidation)
                self.memory_strength[best_match_idx] = min(1.0, self.memory_strength[best_match_idx] + 0.1)

        # Clear gradients
        self.zero_grad()

    def consolidate_memory(self, consolidation_rate: float = 0.01):
        """
        Consolidate memory entries based on usage and age.

        Implements memory consolidation as described in neuroscience literature
        and adapted for Nested Learning.
        """
        with torch.no_grad():
            # Age-based decay
            self.memory_age += 1
            age_decay = torch.exp(-self.memory_age * 0.001)  # Exponential decay

            # Frequency-based strengthening
            frequency_boost = 1.0 + (self.memory_frequency * 0.01)

            # Update memory strength
            self.memory_strength *= age_decay * frequency_boost

            # Clamp to reasonable range
            self.memory_strength.clamp_(0.1, 1.0)

            # Reset frequency counter for next consolidation period
            self.memory_frequency.zero_()

    def prune_weak_memories(self, threshold: float = 0.3) -> int:
        """
        Remove weak/unused memory entries to free up space.

        Args:
            threshold: Strength threshold below which memories are pruned

        Returns:
            Number of memories pruned
        """
        weak_mask = self.memory_strength < threshold
        n_pruned = weak_mask.sum().item()

        if n_pruned > 0:
            # Keep only strong memories
            strong_mask = ~weak_mask

            self.memory_matrix.data = self.memory_matrix[strong_mask]
            self.memory_values.data = self.memory_values[strong_mask]
            self.memory_age = self.memory_age[strong_mask]
            self.memory_frequency = self.memory_frequency[strong_mask]
            self.memory_strength = self.memory_strength[strong_mask]

            # Pad with zeros if needed to maintain memory_size
            current_size = self.memory_matrix.shape[0]
            if current_size < self.memory_size:
                padding_size = self.memory_size - current_size

                # Add new random memories
                new_memories = torch.randn(padding_size, self.input_dim, device=self.memory_matrix.device) * 0.1
                new_values = torch.randn(padding_size, 1, device=self.memory_values.device) * 0.1
                new_age = torch.zeros(padding_size, device=self.memory_age.device)
                new_frequency = torch.zeros(padding_size, device=self.memory_frequency.device)
                new_strength = torch.ones(padding_size, device=self.memory_strength.device) * 0.5

                self.memory_matrix.data = torch.cat([self.memory_matrix, new_memories], dim=0)
                self.memory_values.data = torch.cat([self.memory_values, new_values], dim=0)
                self.memory_age = torch.cat([self.memory_age, new_age], dim=0)
                self.memory_frequency = torch.cat([self.memory_frequency, new_frequency], dim=0)
                self.memory_strength = torch.cat([self.memory_strength, new_strength], dim=0)

        return n_pruned

    def _update_memory_stats(self, attention_weights: torch.Tensor):
        """Update memory access statistics."""
        # Update frequency based on attention weights
        batch_attention = attention_weights.mean(dim=0)  # Average across batch
        self.memory_frequency += batch_attention.detach()

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics."""
        return {
            'memory_size': self.memory_size,
            'active_memories': (self.memory_strength > 0.5).sum().item(),
            'average_strength': self.memory_strength.mean().item(),
            'max_strength': self.memory_strength.max().item(),
            'min_strength': self.memory_strength.min().item(),
            'average_age': self.memory_age.mean().item(),
            'total_accesses': self.memory_frequency.sum().item()
        }

    def save_memory(self, path: str):
        """Save memory state to file."""
        torch.save({
            'memory_matrix': self.memory_matrix,
            'memory_values': self.memory_values,
            'memory_age': self.memory_age,
            'memory_frequency': self.memory_frequency,
            'memory_strength': self.memory_strength
        }, path)

    def load_memory(self, path: str):
        """Load memory state from file."""
        checkpoint = torch.load(path)
        self.memory_matrix.data = checkpoint['memory_matrix']
        self.memory_values.data = checkpoint['memory_values']
        self.memory_age = checkpoint['memory_age']
        self.memory_frequency = checkpoint['memory_frequency']
        self.memory_strength = checkpoint['memory_strength']


class NestedAssociativeMemory(nn.Module):
    """
    Multi-level associative memory for Nested Learning hierarchies.

    Implements multiple associative memory modules at different levels
    of abstraction, as described in the Nested Learning paradigm.
    """

    def __init__(self, input_dims: List[int], memory_sizes: List[int], num_levels: int = 3):
        super().__init__()
        self.num_levels = num_levels

        # Create associative memories for each level
        self.level_memories = nn.ModuleList([
            AssociativeMemory(input_dims[i], memory_sizes[i])
            for i in range(num_levels)
        ])

        # Level transition networks (compress information across levels)
        self.level_transitions = nn.ModuleList([
            nn.Sequential(
                nn.Linear(input_dims[i], input_dims[i+1]),
                nn.ReLU(),
                nn.Linear(input_dims[i+1], input_dims[i+1])
            ) for i in range(num_levels - 1)
        ])

    def forward(self, inputs: List[torch.Tensor]) -> List[torch.Tensor]:
        """
        Process inputs through nested associative memories.

        Args:
            inputs: List of tensors, one for each level

        Returns:
            List of retrieved patterns, one for each level
        """
        assert len(inputs) == self.num_levels, f"Expected {self.num_levels} inputs, got {len(inputs)}"

        outputs = []

        # Process each level
        for level in range(self.num_levels):
            level_input = inputs[level]

            # Apply associative memory at this level
            level_output = self.level_memories[level](level_input)
            outputs.append(level_output)

            # If not the last level, transition to next level
            if level < self.num_levels - 1:
                # Compress current level output for next level
                transition_input = self.level_transitions[level](level_output)
                # This would be used as input for the next level in the hierarchy
                # (In practice, this creates the nested structure)

        return outputs

    def update_hierarchy(self, patterns: List[torch.Tensor], values: List[torch.Tensor],
                        learning_rates: List[float]):
        """Update all levels of the associative memory hierarchy."""
        for level in range(self.num_levels):
            self.level_memories[level].update(
                patterns[level],
                values[level],
                learning_rates[level]
            )

    def consolidate_all_levels(self):
        """Consolidate memories at all levels."""
        for memory in self.level_memories:
            memory.consolidate_memory()

    def prune_all_levels(self, threshold: float = 0.3) -> int:
        """Prune weak memories at all levels."""
        total_pruned = 0
        for memory in self.level_memories:
            total_pruned += memory.prune_weak_memories(threshold)
        return total_pruned