#!/usr/bin/env python3
"""
Deep Optimizer - Multi-level Nested Optimization for Nested Learning

Based on "Nested Learning: The Illusion of Deep Learning Architectures" (Google Research)
Implements hierarchical optimization where architecture and optimization algorithm
are unified into nested optimization problems with different update frequencies.

Key Features:
- Multiple optimization levels with different frequencies
- Associative memory integration for each level
- Probabilistic updates based on level importance
- Gradient flow control between levels
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from typing import Dict, List, Tuple, Optional, Any, Union
import math
import random
from ..models.hope.associative_memory import AssociativeMemory


class OptimizationLevel:
    """
    Single optimization level in the deep optimizer hierarchy.

    Each level has its own optimizer, associative memory, and update frequency.
    """

    def __init__(self,
                 parameters: List[torch.nn.Parameter],
                 optimizer_class: type = optim.Adam,
                 optimizer_kwargs: Dict[str, Any] = None,
                 update_frequency: float = 1.0,
                 memory_size: int = 512,
                 level_name: str = "level"):
        self.parameters = list(parameters)
        self.update_frequency = update_frequency
        self.level_name = level_name

        # Create optimizer for this level
        optimizer_kwargs = optimizer_kwargs or {'lr': 1e-3}
        self.optimizer = optimizer_class(self.parameters, **optimizer_kwargs)

        # Create associative memory for this level
        if len(parameters) > 0:
            # Estimate input dimension from first parameter
            param_shapes = [p.shape for p in parameters]
            total_params = sum(math.prod(shape) for shape in param_shapes)
            input_dim = min(512, max(64, int(math.sqrt(total_params))))  # Reasonable dimension

            self.associative_memory = AssociativeMemory(
                input_dim=input_dim,
                memory_size=memory_size
            )
        else:
            self.associative_memory = None

        # Level statistics
        self.update_count = 0
        self.last_update_step = 0
        self.gradient_norm_history = []

    def should_update(self, global_step: int) -> bool:
        """Determine if this level should update based on frequency and global step."""
        # Probabilistic update based on frequency
        if random.random() < self.update_frequency:
            return True

        # Also update if enough steps have passed (minimum frequency guarantee)
        steps_since_last = global_step - self.last_update_step
        min_steps = max(1, int(1.0 / self.update_frequency))

        return steps_since_last >= min_steps

    def update(self, loss: torch.Tensor, global_step: int):
        """Perform optimization update at this level."""
        if not self.should_update(global_step):
            return

        # Store gradient norm for monitoring
        total_norm = 0
        param_count = 0
        for param in self.parameters:
            if param.grad is not None:
                param_norm = param.grad.data.norm(2)
                total_norm += param_norm.item() ** 2
                param_count += 1

        if param_count > 0:
            total_norm = total_norm ** (1. / 2)
            self.gradient_norm_history.append(total_norm)

        # Standard optimization step
        self.optimizer.zero_grad()
        loss.backward(retain_graph=True)
        self.optimizer.step()

        # Update associative memory if available
        if self.associative_memory is not None:
            # Create pattern from current parameter gradients
            pattern = self._extract_gradient_pattern()
            value = torch.tensor([loss.item()])

            self.associative_memory.update(pattern, value)

        # Update statistics
        self.update_count += 1
        self.last_update_step = global_step

    def _extract_gradient_pattern(self) -> torch.Tensor:
        """Extract gradient pattern for associative memory."""
        gradients = []
        for param in self.parameters:
            if param.grad is not None:
                grad_flat = param.grad.data.flatten()
                # Take a sample of gradients to reduce dimensionality
                if len(grad_flat) > 512:
                    indices = torch.randperm(len(grad_flat))[:512]
                    grad_sample = grad_flat[indices]
                else:
                    grad_sample = grad_flat
                gradients.append(grad_sample)

        if gradients:
            # Concatenate all gradient samples
            pattern = torch.cat(gradients, dim=0)
            # Ensure consistent dimensionality
            if len(pattern) > 512:
                pattern = pattern[:512]
            elif len(pattern) < 512:
                padding = torch.zeros(512 - len(pattern))
                pattern = torch.cat([pattern, padding], dim=0)
        else:
            pattern = torch.zeros(512)

        return pattern

    def get_level_stats(self) -> Dict[str, Any]:
        """Get statistics for this optimization level."""
        return {
            'level_name': self.level_name,
            'update_frequency': self.update_frequency,
            'update_count': self.update_count,
            'last_update_step': self.last_update_step,
            'avg_gradient_norm': sum(self.gradient_norm_history) / max(1, len(self.gradient_norm_history)),
            'memory_stats': self.associative_memory.get_memory_stats() if self.associative_memory else None
        }


class DeepOptimizer:
    """
    Deep Optimizer - Multi-level nested optimization system.

    Implements the core concept of Nested Learning where optimization
    is treated as a hierarchy of nested problems with different
    update frequencies and associative memories.
    """

    def __init__(self,
                 model: nn.Module,
                 num_levels: int = 3,
                 level_configs: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize Deep Optimizer.

        Args:
            model: PyTorch model to optimize
            num_levels: Number of optimization levels
            level_configs: Custom configuration for each level
        """
        self.model = model
        self.num_levels = num_levels
        self.global_step = 0

        # Create default level configurations if not provided
        if level_configs is None:
            level_configs = self._create_default_level_configs()

        # Partition model parameters across levels
        parameter_groups = self._partition_parameters()

        # Create optimization levels
        self.levels = []
        for i, config in enumerate(level_configs):
            level = OptimizationLevel(
                parameters=parameter_groups[i],
                optimizer_class=config.get('optimizer_class', optim.Adam),
                optimizer_kwargs=config.get('optimizer_kwargs', {'lr': 1e-3}),
                update_frequency=config.get('update_frequency', 1.0),
                memory_size=config.get('memory_size', 512),
                level_name=f"level_{i}"
            )
            self.levels.append(level)

        # Cross-level communication
        self.level_communication = self._create_level_communication()

        # Global statistics
        self.optimization_history = []

    def _create_default_level_configs(self) -> List[Dict[str, Any]]:
        """Create default configurations for optimization levels."""
        configs = []

        # Level 0: High-frequency, fast adaptation (inner loop)
        configs.append({
            'optimizer_class': optim.Adam,
            'optimizer_kwargs': {'lr': 1e-3, 'betas': (0.9, 0.999)},
            'update_frequency': 1.0,  # Update every step
            'memory_size': 256
        })

        # Level 1: Medium-frequency, stable learning
        configs.append({
            'optimizer_class': optim.AdamW,
            'optimizer_kwargs': {'lr': 5e-4, 'weight_decay': 0.01},
            'update_frequency': 0.1,  # Update 10% of steps
            'memory_size': 512
        })

        # Level 2: Low-frequency, consolidation (outer loop)
        if self.num_levels > 2:
            configs.append({
                'optimizer_class': optim.SGD,
                'optimizer_kwargs': {'lr': 1e-4, 'momentum': 0.9},
                'update_frequency': 0.01,  # Update 1% of steps
                'memory_size': 1024
            })

        return configs

    def _partition_parameters(self) -> List[List[torch.nn.Parameter]]:
        """Partition model parameters across optimization levels."""
        all_params = list(self.model.parameters())

        if not all_params:
            return [[] for _ in range(self.num_levels)]

        # Simple partitioning: divide parameters equally across levels
        params_per_level = len(all_params) // self.num_levels
        remainder = len(all_params) % self.num_levels

        parameter_groups = []
        start_idx = 0

        for i in range(self.num_levels):
            # Add extra parameter to first levels if there's remainder
            level_size = params_per_level + (1 if i < remainder else 0)
            end_idx = start_idx + level_size

            parameter_groups.append(all_params[start_idx:end_idx])
            start_idx = end_idx

        return parameter_groups

    def _create_level_communication(self) -> nn.ModuleDict:
        """Create communication channels between optimization levels."""
        communication = nn.ModuleDict()

        # Create communication matrices between adjacent levels
        for i in range(self.num_levels - 1):
            level_i_params = sum(math.prod(p.shape) for p in self.levels[i].parameters)
            level_i_plus_1_params = sum(math.prod(p.shape) for p in self.levels[i+1].parameters)

            # Communication matrix from level i to level i+1
            comm_matrix = nn.Linear(level_i_params, level_i_plus_1_params, bias=False)
            nn.init.xavier_uniform_(comm_matrix.weight, gain=0.1)

            communication[f"level_{i}_to_{i+1}"] = comm_matrix

        return communication

    def step(self, loss: torch.Tensor, level_weights: Optional[List[float]] = None):
        """
        Perform nested optimization step.

        Args:
            loss: Loss tensor to optimize
            level_weights: Optional weights for each level's contribution
        """
        if level_weights is None:
            # Default: higher weights for lower levels (more frequent updates)
            level_weights = [1.0 / (i + 1) for i in range(self.num_levels)]

        # Update global step
        self.global_step += 1

        # Perform updates at each level
        level_losses = []
        for level_idx, level in enumerate(self.levels):
            # Compute level-specific loss contribution
            level_loss = loss * level_weights[level_idx]

            # Add regularization from associative memory if available
            if level.associative_memory is not None:
                memory_loss = self._compute_memory_regularization(level, level_idx)
                level_loss += 0.1 * memory_loss  # Small regularization weight

            # Perform level update
            level.update(level_loss, self.global_step)
            level_losses.append(level_loss.item())

        # Cross-level communication (gradient flow)
        self._perform_cross_level_communication()

        # Record optimization step
        self.optimization_history.append({
            'step': self.global_step,
            'loss': loss.item(),
            'level_losses': level_losses,
            'level_updates': [level.update_count for level in self.levels]
        })

    def _compute_memory_regularization(self, level: OptimizationLevel, level_idx: int) -> torch.Tensor:
        """Compute regularization loss from associative memory."""
        if level.associative_memory is None:
            return torch.tensor(0.0)

        # Extract current gradient pattern
        pattern = level._extract_gradient_pattern()

        # Query associative memory for similar patterns
        memory_output = level.associative_memory(pattern)

        # Use memory output as regularization target
        # (This encourages consistency with past successful updates)
        target = torch.zeros_like(memory_output)
        regularization_loss = F.mse_loss(memory_output, target)

        return regularization_loss

    def _perform_cross_level_communication(self):
        """Perform gradient flow between optimization levels."""
        # This implements the "context flow" concept from Nested Learning
        for i in range(self.num_levels - 1):
            # Get gradients from current level
            current_level_grads = []
            for param in self.levels[i].parameters:
                if param.grad is not None:
                    current_level_grads.append(param.grad.flatten())

            if current_level_grads:
                # Concatenate gradients
                level_grads = torch.cat(current_level_grads, dim=0)

                # Transform through communication matrix
                comm_key = f"level_{i}_to_{i+1}"
                if comm_key in self.level_communication:
                    comm_matrix = self.level_communication[comm_key]
                    transformed_grads = comm_matrix(level_grads)

                    # Apply transformed gradients to next level (scaled)
                    grad_chunks = torch.chunk(transformed_grads, len(self.levels[i+1].parameters))
                    for param, grad_chunk in zip(self.levels[i+1].parameters, grad_chunks):
                        if param.grad is not None:
                            # Add small amount of cross-level gradient
                            param.grad.data += 0.01 * grad_chunk.view_as(param.grad)

    def consolidate_memories(self):
        """Consolidate associative memories across all levels."""
        for level in self.levels:
            if level.associative_memory is not None:
                level.associative_memory.consolidate_memory()

    def prune_weak_memories(self, threshold: float = 0.3) -> int:
        """Prune weak memories across all levels."""
        total_pruned = 0
        for level in self.levels:
            if level.associative_memory is not None:
                total_pruned += level.associative_memory.prune_weak_memories(threshold)
        return total_pruned

    def get_optimizer_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the deep optimizer."""
        level_stats = [level.get_level_stats() for level in self.levels]

        return {
            'global_step': self.global_step,
            'num_levels': self.num_levels,
            'level_stats': level_stats,
            'total_updates': sum(level.update_count for level in self.levels),
            'optimization_history_length': len(self.optimization_history),
            'average_level_losses': [
                sum(step['level_losses'][i] for step in self.optimization_history[-100:]) /
                max(1, len(self.optimization_history[-100:]))
                for i in range(self.num_levels)
            ] if self.optimization_history else []
        }

    def save_optimizer_state(self, path: str):
        """Save deep optimizer state."""
        state = {
            'global_step': self.global_step,
            'level_states': [level.get_level_stats() for level in self.levels],
            'optimization_history': self.optimization_history[-1000:],  # Keep last 1000 steps
            'communication_weights': {
                name: module.weight.data for name, module in self.level_communication.items()
            }
        }
        torch.save(state, path)

    def load_optimizer_state(self, path: str):
        """Load deep optimizer state."""
        state = torch.load(path)
        self.global_step = state['global_step']
        self.optimization_history = state['optimization_history']

        # Load communication weights
        for name, weight in state['communication_weights'].items():
            if name in self.level_communication:
                self.level_communication[name].weight.data = weight


class AdaptiveDeepOptimizer(DeepOptimizer):
    """
    Adaptive Deep Optimizer with dynamic level adjustment.

    Extends DeepOptimizer with automatic adjustment of update frequencies
    and level configurations based on training dynamics.
    """

    def __init__(self, model: nn.Module, num_levels: int = 3, adaptation_rate: float = 0.01):
        super().__init__(model, num_levels)
        self.adaptation_rate = adaptation_rate
        self.performance_history = []

    def step(self, loss: torch.Tensor, level_weights: Optional[List[float]] = None):
        """Adaptive optimization step with dynamic adjustment."""
        # Perform standard optimization
        super().step(loss, level_weights)

        # Adapt level configurations based on performance
        self._adapt_level_configurations(loss)

    def _adapt_level_configurations(self, current_loss: float):
        """Adapt level configurations based on recent performance."""
        if len(self.optimization_history) < 10:
            return  # Need some history

        recent_history = self.optimization_history[-10:]
        recent_losses = [step['loss'] for step in recent_history]

        # Compute loss trend
        loss_trend = (recent_losses[-1] - recent_losses[0]) / len(recent_losses)

        # Adapt update frequencies based on loss trend
        for level_idx, level in enumerate(self.levels):
            if loss_trend > 0:  # Loss increasing - increase update frequency for this level
                level.update_frequency = min(1.0, level.update_frequency * (1 + self.adaptation_rate))
            else:  # Loss decreasing - decrease update frequency (more stable)
                level.update_frequency = max(0.001, level.update_frequency * (1 - self.adaptation_rate))

        self.performance_history.append({
            'step': self.global_step,
            'loss': current_loss.item(),
            'loss_trend': loss_trend,
            'adapted_frequencies': [level.update_frequency for level in self.levels]
        })