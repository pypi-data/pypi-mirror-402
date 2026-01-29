#!/usr/bin/env python3
"""
Context Flow Manager - Manages nested context flows in Nested Learning

Based on "Nested Learning: The Illusion of Deep Learning Architectures" (Google Research)
Implements context flow management for hierarchical optimization levels,
enabling information transfer between nested learning problems.

Key Features:
- Hierarchical context flow organization
- Dynamic flow creation and management
- Context inheritance and propagation
- Flow consolidation and pruning
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional, Any, Union
import time
import threading
from collections import defaultdict


class ContextFlow:
    """
    Individual context flow within the nested learning hierarchy.

    Represents a distinct information flow at a specific level of abstraction.
    """

    def __init__(self,
                 flow_id: str,
                 embed_dim: int,
                 context_type: str = "general",
                 parent_flow: Optional[str] = None):
        self.flow_id = flow_id
        self.embed_dim = embed_dim
        self.context_type = context_type
        self.parent_flow = parent_flow

        # Flow content
        self.context_vectors = []  # List of context vectors
        self.flow_strength = 1.0   # Flow consolidation strength
        self.last_access = time.time()
        self.access_count = 0

        # Flow metadata
        self.creation_time = time.time()
        self.flow_level = 0  # Hierarchy level
        self.flow_tags = set()  # Semantic tags for flow categorization

        # Child flows (for hierarchy management)
        self.child_flows = set()

    def add_context(self, context_vector: torch.Tensor, metadata: Optional[Dict[str, Any]] = None):
        """Add new context vector to the flow."""
        if isinstance(context_vector, torch.Tensor):
            self.context_vectors.append(context_vector.detach().cpu())
        else:
            self.context_vectors.append(torch.tensor(context_vector))

        self.last_access = time.time()
        self.access_count += 1

        # Update metadata if provided
        if metadata:
            if 'tags' in metadata:
                self.flow_tags.update(metadata['tags'])
            if 'level' in metadata:
                self.flow_level = metadata['level']

    def get_context_representation(self, max_contexts: int = 10) -> torch.Tensor:
        """Get consolidated context representation."""
        if not self.context_vectors:
            return torch.zeros(self.embed_dim)

        # Use most recent contexts (up to max_contexts)
        recent_contexts = self.context_vectors[-max_contexts:]

        # Weighted combination (more recent = higher weight)
        weights = torch.softmax(torch.arange(len(recent_contexts), dtype=torch.float), dim=0)
        weights = weights.unsqueeze(-1).expand(-1, self.embed_dim)

        context_tensor = torch.stack(recent_contexts, dim=0)
        weighted_context = (context_tensor * weights).sum(dim=0)

        return weighted_context * self.flow_strength

    def consolidate_flow(self, consolidation_rate: float = 0.1):
        """Consolidate flow based on usage and age."""
        current_time = time.time()

        # Age-based decay
        age_hours = (current_time - self.creation_time) / 3600.0
        age_decay = torch.exp(-torch.tensor(age_hours * 0.01))

        # Usage-based strengthening
        usage_boost = 1.0 + (self.access_count * 0.001)

        # Update flow strength
        self.flow_strength = float(self.flow_strength * age_decay * usage_boost)
        self.flow_strength = max(0.1, min(1.0, self.flow_strength))

    def should_prune(self, threshold: float = 0.3) -> bool:
        """Determine if flow should be pruned."""
        return self.flow_strength < threshold and len(self.child_flows) == 0

    def get_flow_stats(self) -> Dict[str, Any]:
        """Get flow statistics."""
        return {
            'flow_id': self.flow_id,
            'context_type': self.context_type,
            'flow_level': self.flow_level,
            'flow_strength': self.flow_strength,
            'num_contexts': len(self.context_vectors),
            'access_count': self.access_count,
            'last_access': self.last_access,
            'creation_time': self.creation_time,
            'child_flows': len(self.child_flows),
            'tags': list(self.flow_tags)
        }


class ContextFlowManager:
    """
    Context Flow Manager - Orchestrates nested context flows in Nested Learning.

    Manages the creation, propagation, and consolidation of context flows
    across different levels of the nested optimization hierarchy.
    """

    def __init__(self, embed_dims: List[int], max_flows_per_level: int = 100):
        self.embed_dims = embed_dims
        self.max_flows_per_level = max_flows_per_level

        # Flow storage organized by level
        self.flows_by_level = defaultdict(dict)  # level -> {flow_id: ContextFlow}

        # Flow hierarchy tracking
        self.flow_hierarchy = {}  # flow_id -> parent_flow_id
        self.level_flows = defaultdict(set)  # level -> set of flow_ids

        # Communication matrices between levels
        self.level_communications = self._create_level_communications()

        # Flow statistics
        self.total_flows_created = 0
        self.flows_pruned = 0

        # Thread safety
        self.lock = threading.RLock()

    def _create_level_communications(self) -> nn.ModuleDict:
        """Create communication matrices between hierarchy levels."""
        communications = nn.ModuleDict()

        for i in range(len(self.embed_dims) - 1):
            # Communication from level i to level i+1
            comm_matrix = nn.Linear(self.embed_dims[i], self.embed_dims[i+1], bias=False)
            nn.init.xavier_uniform_(comm_matrix.weight, gain=0.1)
            communications[f"level_{i}_to_{i+1}"] = comm_matrix

        return communications

    def create_nested_flow(self,
                          context_type: str = "general",
                          parent_flow: Optional[str] = None,
                          initial_context: Optional[torch.Tensor] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new nested context flow.

        Args:
            context_type: Type of context flow
            parent_flow: Parent flow ID for hierarchy
            initial_context: Initial context vector
            metadata: Additional metadata

        Returns:
            New flow ID
        """
        with self.lock:
            # Determine flow level
            if parent_flow and parent_flow in self.flow_hierarchy:
                parent_level = self._get_flow_level(parent_flow)
                flow_level = parent_level + 1
            else:
                flow_level = 0

            # Generate unique flow ID
            flow_id = f"{context_type}_{flow_level}_{self.total_flows_created}_{int(time.time())}"
            self.total_flows_created += 1

            # Create flow object
            embed_dim = self.embed_dims[min(flow_level, len(self.embed_dims) - 1)]
            flow = ContextFlow(flow_id, embed_dim, context_type, parent_flow)

            # Set flow level and metadata
            flow.flow_level = flow_level
            if metadata:
                flow.flow_level = metadata.get('level', flow_level)
                if 'tags' in metadata:
                    flow.flow_tags.update(metadata['tags'])

            # Add initial context if provided
            if initial_context is not None:
                flow.add_context(initial_context, metadata)

            # Store flow
            self.flows_by_level[flow_level][flow_id] = flow
            self.level_flows[flow_level].add(flow_id)

            # Update hierarchy
            if parent_flow:
                self.flow_hierarchy[flow_id] = parent_flow
                if parent_flow in self.flows_by_level[flow_level - 1]:
                    parent_flow_obj = self.flows_by_level[flow_level - 1][parent_flow]
                    parent_flow_obj.child_flows.add(flow_id)

            return flow_id

    def update_flow_hierarchy(self,
                             flow_id: str,
                             new_context: torch.Tensor,
                             metadata: Optional[Dict[str, Any]] = None):
        """
        Update flow and propagate changes through hierarchy.

        Args:
            flow_id: Flow to update
            new_context: New context vector
            metadata: Update metadata
        """
        with self.lock:
            if not self._flow_exists(flow_id):
                return

            flow_level = self._get_flow_level(flow_id)
            flow = self.flows_by_level[flow_level][flow_id]

            # Update flow
            flow.add_context(new_context, metadata)

            # Propagate to parent (bottom-up)
            self._propagate_to_parent(flow_id, new_context, flow_level)

            # Propagate to children (top-down)
            self._propagate_to_children(flow_id, new_context, flow_level)

    def _propagate_to_parent(self, flow_id: str, context: torch.Tensor, flow_level: int):
        """Propagate context changes to parent flow."""
        if flow_id not in self.flow_hierarchy:
            return

        parent_id = self.flow_hierarchy[flow_id]
        parent_level = flow_level - 1

        if parent_id in self.flows_by_level[parent_level]:
            parent_flow = self.flows_by_level[parent_level][parent_id]

            # Transform context to parent level dimensionality
            if flow_level > 0:
                comm_key = f"level_{flow_level}_to_{flow_level-1}"
                if comm_key in self.level_communications:
                    comm_matrix = self.level_communications[comm_key]
                    # Note: This is inverse transformation (child to parent)
                    # In practice, you'd want a separate inverse matrix
                    transformed_context = comm_matrix(context.unsqueeze(0)).squeeze(0)
                else:
                    transformed_context = context
            else:
                transformed_context = context

            # Update parent flow
            parent_flow.add_context(transformed_context)

            # Continue propagation
            self._propagate_to_parent(parent_id, transformed_context, parent_level)

    def _propagate_to_children(self, flow_id: str, context: torch.Tensor, flow_level: int):
        """Propagate context changes to child flows."""
        if flow_id not in self.flows_by_level[flow_level]:
            return

        flow = self.flows_by_level[flow_level][flow_id]

        for child_id in flow.child_flows:
            child_level = flow_level + 1
            if child_id in self.flows_by_level[child_level]:
                child_flow = self.flows_by_level[child_level][child_id]

                # Transform context to child level dimensionality
                if child_level < len(self.embed_dims):
                    comm_key = f"level_{flow_level}_to_{child_level}"
                    if comm_key in self.level_communications:
                        comm_matrix = self.level_communications[comm_key]
                        transformed_context = comm_matrix(context.unsqueeze(0)).squeeze(0)
                    else:
                        transformed_context = context
                else:
                    transformed_context = context

                # Update child flow
                child_flow.add_context(transformed_context)

                # Continue propagation
                self._propagate_to_children(child_id, transformed_context, child_level)

    def get_flow_context(self, flow_id: str, max_contexts: int = 10) -> Optional[torch.Tensor]:
        """Get consolidated context from a specific flow."""
        with self.lock:
            if not self._flow_exists(flow_id):
                return None

            flow_level = self._get_flow_level(flow_id)
            flow = self.flows_by_level[flow_level][flow_id]

            return flow.get_context_representation(max_contexts)

    def get_hierarchy_context(self, root_flow_id: str, max_depth: int = 3) -> Dict[str, torch.Tensor]:
        """
        Get context from entire flow hierarchy starting from root.

        Args:
            root_flow_id: Root flow to start from
            max_depth: Maximum hierarchy depth to traverse

        Returns:
            Dictionary of flow_id -> context_tensor
        """
        with self.lock:
            hierarchy_contexts = {}

            def traverse_hierarchy(flow_id: str, current_depth: int):
                if current_depth > max_depth:
                    return

                context = self.get_flow_context(flow_id)
                if context is not None:
                    hierarchy_contexts[flow_id] = context

                # Traverse children
                flow_level = self._get_flow_level(flow_id)
                if flow_id in self.flows_by_level[flow_level]:
                    flow = self.flows_by_level[flow_level][flow_id]
                    for child_id in flow.child_flows:
                        traverse_hierarchy(child_id, current_depth + 1)

            traverse_hierarchy(root_flow_id, 0)
            return hierarchy_contexts

    def consolidate_flows(self, consolidation_rate: float = 0.1):
        """Consolidate all flows based on usage and age."""
        with self.lock:
            for level_flows in self.flows_by_level.values():
                for flow in level_flows.values():
                    flow.consolidate_flow(consolidation_rate)

    def prune_weak_flows(self, threshold: float = 0.3) -> int:
        """
        Prune weak/unused flows to manage memory.

        Args:
            threshold: Strength threshold below which flows are pruned

        Returns:
            Number of flows pruned
        """
        with self.lock:
            flows_to_prune = []

            for level, level_flows in self.flows_by_level.items():
                for flow_id, flow in level_flows.items():
                    if flow.should_prune(threshold):
                        flows_to_prune.append((level, flow_id))

            # Prune flows
            for level, flow_id in flows_to_prune:
                if flow_id in self.flows_by_level[level]:
                    del self.flows_by_level[level][flow_id]
                    self.level_flows[level].discard(flow_id)

                    # Remove from hierarchy
                    if flow_id in self.flow_hierarchy:
                        del self.flow_hierarchy[flow_id]

                    # Remove from parent child lists
                    for parent_level_flows in self.flows_by_level.values():
                        for parent_flow in parent_level_flows.values():
                            parent_flow.child_flows.discard(flow_id)

            pruned_count = len(flows_to_prune)
            self.flows_pruned += pruned_count

            return pruned_count

    def get_flow_statistics(self) -> Dict[str, Any]:
        """Get comprehensive flow statistics."""
        with self.lock:
            level_stats = {}
            total_flows = 0
            total_contexts = 0

            for level, level_flows in self.flows_by_level.items():
                level_stats[level] = {
                    'num_flows': len(level_flows),
                    'total_contexts': sum(len(flow.context_vectors) for flow in level_flows.values()),
                    'avg_strength': sum(flow.flow_strength for flow in level_flows.values()) / max(1, len(level_flows)),
                    'flow_types': list(set(flow.context_type for flow in level_flows.values()))
                }
                total_flows += len(level_flows)
                total_contexts += level_stats[level]['total_contexts']

            return {
                'total_flows': total_flows,
                'total_contexts': total_contexts,
                'flows_pruned': self.flows_pruned,
                'num_levels': len(self.flows_by_level),
                'level_stats': level_stats,
                'hierarchy_size': len(self.flow_hierarchy)
            }

    def save_flow_state(self, path: str):
        """Save context flow state."""
        with self.lock:
            state = {
                'flows_by_level': {
                    level: {
                        flow_id: {
                            'context_type': flow.context_type,
                            'parent_flow': flow.parent_flow,
                            'flow_level': flow.flow_level,
                            'flow_strength': flow.flow_strength,
                            'context_vectors': flow.context_vectors,
                            'flow_tags': list(flow.flow_tags),
                            'child_flows': list(flow.child_flows)
                        }
                        for flow_id, flow in level_flows.items()
                    }
                    for level, level_flows in self.flows_by_level.items()
                },
                'flow_hierarchy': dict(self.flow_hierarchy),
                'total_flows_created': self.total_flows_created,
                'flows_pruned': self.flows_pruned
            }
            torch.save(state, path)

    def load_flow_state(self, path: str):
        """Load context flow state."""
        state = torch.load(path)

        # Restore flows
        for level, level_flows in state['flows_by_level'].items():
            level = int(level)
            for flow_id, flow_data in level_flows.items():
                embed_dim = self.embed_dims[min(level, len(self.embed_dims) - 1)]
                flow = ContextFlow(flow_id, embed_dim,
                                 flow_data['context_type'],
                                 flow_data['parent_flow'])

                flow.flow_level = flow_data['flow_level']
                flow.flow_strength = flow_data['flow_strength']
                flow.context_vectors = flow_data['context_vectors']
                flow.flow_tags = set(flow_data['flow_tags'])
                flow.child_flows = set(flow_data['child_flows'])

                self.flows_by_level[level][flow_id] = flow
                self.level_flows[level].add(flow_id)

        # Restore hierarchy
        self.flow_hierarchy = state['flow_hierarchy']
        self.total_flows_created = state['total_flows_created']
        self.flows_pruned = state['flows_pruned']

    def _flow_exists(self, flow_id: str) -> bool:
        """Check if flow exists."""
        for level_flows in self.flows_by_level.values():
            if flow_id in level_flows:
                return True
        return False

    def _get_flow_level(self, flow_id: str) -> int:
        """Get flow's level in hierarchy."""
        for level, level_flows in self.flows_by_level.items():
            if flow_id in level_flows:
                return level
        return 0