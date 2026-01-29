#!/usr/bin/env python3
"""
Multi-Frequency Update Scheduler - Core scheduler for Nested Learning

Based on "Nested Learning: The Illusion of Deep Learning Architectures" (Google Research)
Implements multi-frequency update scheduling where different components of the
nested optimization hierarchy update at different timescales.

Key Features:
- Component-specific update frequencies
- Probabilistic scheduling
- Adaptive frequency adjustment
- Resource-aware scheduling
"""

import torch
import torch.nn as nn
from typing import Dict, List, Tuple, Optional, Any, Union, Callable
import time
import random
import math
from collections import defaultdict


class ComponentScheduler:
    """
    Scheduler for individual components within the nested learning system.

    Manages update timing and frequency for specific model components.
    """

    def __init__(self,
                 component_name: str,
                 base_frequency: float,
                 component_type: str = "parameter",
                 adaptive: bool = True):
        self.component_name = component_name
        self.base_frequency = base_frequency  # Updates per step (0.1 = 10% of steps)
        self.component_type = component_type
        self.adaptive = adaptive

        # Scheduling state
        self.last_update_step = 0
        self.update_count = 0
        self.current_frequency = base_frequency

        # Performance tracking
        self.performance_history = []
        self.frequency_history = []

        # Adaptive parameters
        self.learning_rate = 0.01
        self.momentum = 0.9
        self.previous_gradient = 0.0

    def should_update(self, global_step: int, performance_metric: Optional[float] = None) -> bool:
        """
        Determine if component should update at current step.

        Args:
            global_step: Current global training step
            performance_metric: Optional performance metric for adaptation

        Returns:
            True if component should update
        """
        steps_since_update = global_step - self.last_update_step

        # Minimum frequency guarantee (don't wait too long)
        min_steps = max(1, int(1.0 / self.current_frequency))
        if steps_since_update >= min_steps:
            return True

        # Probabilistic update based on current frequency
        if random.random() < self.current_frequency:
            return True

        return False

    def record_update(self, global_step: int, performance_metric: Optional[float] = None):
        """Record that an update occurred."""
        self.last_update_step = global_step
        self.update_count += 1

        if performance_metric is not None:
            self.performance_history.append(performance_metric)
            self.frequency_history.append(self.current_frequency)

            # Adaptive frequency adjustment
            if self.adaptive:
                self._adapt_frequency(performance_metric)

    def _adapt_frequency(self, performance_metric: float):
        """Adapt update frequency based on performance."""
        if len(self.performance_history) < 2:
            return

        # Compute performance trend
        recent_performance = self.performance_history[-10:]  # Last 10 updates
        if len(recent_performance) >= 2:
            performance_trend = (recent_performance[-1] - recent_performance[0]) / len(recent_performance)

            # Gradient descent on frequency
            gradient = -performance_trend  # We want to increase frequency if performance is improving

            # Add momentum
            gradient = self.momentum * self.previous_gradient + (1 - self.momentum) * gradient
            self.previous_gradient = gradient

            # Update frequency
            frequency_delta = self.learning_rate * gradient
            self.current_frequency = torch.clamp(
                torch.tensor(self.current_frequency + frequency_delta),
                min=0.001, max=1.0
            ).item()

    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        return {
            'component_name': self.component_name,
            'component_type': self.component_type,
            'base_frequency': self.base_frequency,
            'current_frequency': self.current_frequency,
            'update_count': self.update_count,
            'last_update_step': self.last_update_step,
            'adaptive': self.adaptive,
            'avg_performance': sum(self.performance_history) / max(1, len(self.performance_history)),
            'performance_trend': self._compute_performance_trend()
        }

    def _compute_performance_trend(self) -> float:
        """Compute recent performance trend."""
        if len(self.performance_history) < 5:
            return 0.0

        recent = self.performance_history[-5:]
        return (recent[-1] - recent[0]) / len(recent)


class MultiFrequencyScheduler:
    """
    Multi-Frequency Update Scheduler for Nested Learning systems.

    Orchestrates update timing across all components in the nested learning
    hierarchy, ensuring optimal resource utilization and learning dynamics.
    """

    def __init__(self,
                 component_configs: Optional[Dict[str, Dict[str, Any]]] = None,
                 global_update_frequency: float = 1.0):
        """
        Initialize multi-frequency scheduler.

        Args:
            component_configs: Configuration for each component
            global_update_frequency: Global update frequency baseline
        """
        self.global_update_frequency = global_update_frequency
        self.global_step = 0

        # Component schedulers
        self.component_schedulers = nn.ModuleDict()

        # Default component configurations
        if component_configs is None:
            component_configs = self._get_default_component_configs()

        # Initialize component schedulers
        for component_name, config in component_configs.items():
            scheduler = ComponentScheduler(
                component_name=component_name,
                base_frequency=config.get('frequency', 0.1),
                component_type=config.get('type', 'parameter'),
                adaptive=config.get('adaptive', True)
            )
            self.component_schedulers[component_name] = scheduler

        # Scheduling statistics
        self.schedule_history = []
        self.resource_usage = defaultdict(float)

    def _get_default_component_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get default configurations for common components."""
        return {
            # High-frequency components (update often)
            'attention': {
                'frequency': 1.0,  # Every step
                'type': 'attention',
                'adaptive': True
            },
            'feedforward': {
                'frequency': 0.5,  # Every 2 steps
                'type': 'feedforward',
                'adaptive': True
            },

            # Medium-frequency components
            'layer_norm': {
                'frequency': 0.1,  # Every 10 steps
                'type': 'normalization',
                'adaptive': False
            },
            'embeddings': {
                'frequency': 0.05,  # Every 20 steps
                'type': 'embedding',
                'adaptive': True
            },

            # Low-frequency components (update rarely)
            'lm_head': {
                'frequency': 0.01,  # Every 100 steps
                'type': 'output',
                'adaptive': False
            },

            # Memory components
            'associative_memory': {
                'frequency': 0.1,
                'type': 'memory',
                'adaptive': True
            },
            'cms_blocks': {
                'frequency': 0.05,
                'type': 'memory',
                'adaptive': True
            },

            # Optimizer components
            'optimizer_level_0': {
                'frequency': 1.0,
                'type': 'optimizer',
                'adaptive': True
            },
            'optimizer_level_1': {
                'frequency': 0.1,
                'type': 'optimizer',
                'adaptive': True
            },
            'optimizer_level_2': {
                'frequency': 0.01,
                'type': 'optimizer',
                'adaptive': False
            }
        }

    def get_update_schedule(self, performance_metrics: Optional[Dict[str, Any]] = None) -> Dict[str, bool]:
        """
        Get update schedule for current step.

        Args:
            performance_metrics: Optional performance metrics for adaptation

        Returns:
            Dictionary of component_name -> should_update
        """
        self.global_step += 1
        update_schedule = {}

        for component_name, scheduler in self.component_schedulers.items():
            # Get performance metric for this component if available
            component_metric = None
            if performance_metrics and component_name in performance_metrics:
                component_metric = performance_metrics[component_name]

            # Determine if component should update
            should_update = scheduler.should_update(self.global_step, component_metric)
            update_schedule[component_name] = should_update

            # Record update if it happens
            if should_update:
                scheduler.record_update(self.global_step, component_metric)
                self.resource_usage[component_name] += 1

        # Record schedule
        self.schedule_history.append({
            'step': self.global_step,
            'schedule': update_schedule.copy(),
            'performance_metrics': performance_metrics or {}
        })

        return update_schedule

    def apply_schedule(self,
                      model: nn.Module,
                      optimizer: Any,
                      update_schedule: Dict[str, bool],
                      loss_fn: Callable = None,
                      inputs: Any = None) -> Dict[str, Any]:
        """
        Apply update schedule to model components.

        Args:
            model: Model to update
            optimizer: Optimizer (can be DeepOptimizer)
            update_schedule: Schedule from get_update_schedule
            loss_fn: Loss function for computing gradients
            inputs: Model inputs for computing loss

        Returns:
            Update results and statistics
        """
        update_results = {}
        components_updated = []

        # Group components by update status
        components_to_update = [name for name, should_update in update_schedule.items() if should_update]
        components_to_skip = [name for name, should_update in update_schedule.items() if not should_update]

        if components_to_update:
            # Compute loss and gradients for components that need updating
            if loss_fn and inputs:
                loss = self._compute_loss_for_components(model, loss_fn, inputs, components_to_update)
                update_results['loss'] = loss.item()

                # Apply optimizer step for specified components
                if hasattr(optimizer, 'step_with_schedule'):
                    # DeepOptimizer with schedule support
                    optimizer.step_with_schedule(loss, update_schedule)
                else:
                    # Standard optimizer - update all parameters
                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()

                components_updated = components_to_update
            else:
                update_results['error'] = 'No loss function or inputs provided for gradient computation'

        update_results['components_updated'] = components_updated
        update_results['components_skipped'] = components_to_skip
        update_results['update_ratio'] = len(components_updated) / len(update_schedule)

        return update_results

    def _compute_loss_for_components(self,
                                   model: nn.Module,
                                   loss_fn: Callable,
                                   inputs: Any,
                                   components_to_update: List[str]) -> torch.Tensor:
        """
        Compute loss considering only specified components for gradient flow.

        This is a simplified implementation. In practice, you'd need more sophisticated
        gradient masking or component-specific loss computation.
        """
        # For now, compute standard loss
        # In a full implementation, you'd mask gradients for components not in components_to_update
        outputs = model(inputs)
        loss = loss_fn(outputs, inputs)  # Simplified - assumes inputs contain targets

        return loss

    def adapt_frequencies(self, system_performance: Dict[str, Any]):
        """
        Adapt update frequencies based on system-wide performance.

        Args:
            system_performance: System performance metrics
        """
        # Adapt individual component frequencies
        for scheduler in self.component_schedulers.values():
            if scheduler.adaptive:
                # Use system performance as adaptation signal
                performance_signal = system_performance.get('overall_performance', 0.5)
                scheduler._adapt_frequency(performance_signal)

        # Global frequency adaptation
        if 'resource_utilization' in system_performance:
            utilization = system_performance['resource_utilization']
            if utilization > 0.8:  # High utilization - reduce frequencies
                self._adjust_global_frequencies(-0.1)
            elif utilization < 0.3:  # Low utilization - increase frequencies
                self._adjust_global_frequencies(0.1)

    def _adjust_global_frequencies(self, delta: float):
        """Adjust all frequencies by a delta."""
        for scheduler in self.component_schedulers.values():
            scheduler.current_frequency = torch.clamp(
                torch.tensor(scheduler.current_frequency + delta),
                min=0.001, max=1.0
            ).item()

    def get_scheduler_statistics(self) -> Dict[str, Any]:
        """Get comprehensive scheduler statistics."""
        component_stats = {}
        for name, scheduler in self.component_schedulers.items():
            component_stats[name] = scheduler.get_scheduler_stats()

        # Compute aggregate statistics
        total_updates = sum(stats['update_count'] for stats in component_stats.values())
        avg_frequency = sum(stats['current_frequency'] for stats in component_stats.values()) / len(component_stats)

        # Resource usage analysis
        resource_stats = {}
        for component, usage in self.resource_usage.items():
            resource_stats[component] = {
                'total_updates': usage,
                'update_ratio': usage / max(1, self.global_step)
            }

        return {
            'global_step': self.global_step,
            'total_components': len(self.component_schedulers),
            'total_updates': total_updates,
            'average_frequency': avg_frequency,
            'component_stats': component_stats,
            'resource_stats': resource_stats,
            'schedule_history_length': len(self.schedule_history),
            'adaptive_components': sum(1 for s in self.component_schedulers.values() if s.adaptive)
        }

    def save_scheduler_state(self, path: str):
        """Save scheduler state."""
        state = {
            'global_step': self.global_step,
            'global_update_frequency': self.global_update_frequency,
            'component_states': {
                name: {
                    'base_frequency': scheduler.base_frequency,
                    'current_frequency': scheduler.current_frequency,
                    'last_update_step': scheduler.last_update_step,
                    'update_count': scheduler.update_count,
                    'performance_history': scheduler.performance_history,
                    'frequency_history': scheduler.frequency_history
                }
                for name, scheduler in self.component_schedulers.items()
            },
            'resource_usage': dict(self.resource_usage),
            'schedule_history': self.schedule_history[-1000:]  # Keep last 1000 entries
        }
        torch.save(state, path)

    def load_scheduler_state(self, path: str):
        """Load scheduler state."""
        state = torch.load(path)

        self.global_step = state['global_step']
        self.global_update_frequency = state['global_update_frequency']
        self.resource_usage = defaultdict(float, state['resource_usage'])
        self.schedule_history = state['schedule_history']

        # Restore component states
        for name, comp_state in state['component_states'].items():
            if name in self.component_schedulers:
                scheduler = self.component_schedulers[name]
                scheduler.base_frequency = comp_state['base_frequency']
                scheduler.current_frequency = comp_state['current_frequency']
                scheduler.last_update_step = comp_state['last_update_step']
                scheduler.update_count = comp_state['update_count']
                scheduler.performance_history = comp_state['performance_history']
                scheduler.frequency_history = comp_state['frequency_history']

    def reset_statistics(self):
        """Reset scheduler statistics."""
        self.schedule_history.clear()
        self.resource_usage.clear()
        for scheduler in self.component_schedulers.values():
            scheduler.performance_history.clear()
            scheduler.frequency_history.clear()
            scheduler.update_count = 0
            scheduler.last_update_step = 0