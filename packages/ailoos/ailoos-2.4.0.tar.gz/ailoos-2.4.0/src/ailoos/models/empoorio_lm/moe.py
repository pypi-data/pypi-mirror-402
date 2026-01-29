"""
Mixture of Experts (MoE) implementation for EmpoorioLM.
Resolves device handling issues and provides production-ready MoE layers.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Any, Optional, Tuple, List
import math


class MoEConfig:
    """Configuration for Mixture of Experts layer."""

    def __init__(
        self,
        num_experts: int = 8,
        expert_dim: int = 1024,
        top_k: int = 2,
        use_load_balancing: bool = True,
        load_balance_coeff: float = 0.01,
        router_noise_epsilon: float = 1e-2,
        router_jitter_noise: float = 0.0,
    ):
        self.num_experts = num_experts
        self.expert_dim = expert_dim
        self.top_k = top_k
        self.use_load_balancing = use_load_balancing
        self.load_balance_coeff = load_balance_coeff
        self.router_noise_epsilon = router_noise_epsilon
        self.router_jitter_noise = router_jitter_noise


class MoEExpert(nn.Module):
    """Individual expert in MoE layer."""

    def __init__(self, input_dim: int, output_dim: int, config: MoEConfig):
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.config = config

        # Expert network: simple MLP
        self.w1 = nn.Linear(input_dim, config.expert_dim)
        self.w2 = nn.Linear(config.expert_dim, output_dim)
        self.activation = nn.GELU()

        # Initialize weights properly
        self._initialize_weights()

    def _initialize_weights(self):
        """Initialize expert weights."""
        # Use Xavier initialization for better convergence
        nn.init.xavier_uniform_(self.w1.weight, gain=1.0)
        nn.init.xavier_uniform_(self.w2.weight, gain=1.0)
        nn.init.zeros_(self.w1.bias)
        nn.init.zeros_(self.w2.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through expert."""
        return self.w2(self.activation(self.w1(x)))


class NoisyTopKRouter(nn.Module):
    """Router that selects top-k experts with noise for load balancing."""

    def __init__(self, input_dim: int, num_experts: int, config: MoEConfig):
        super().__init__()
        self.input_dim = input_dim
        self.num_experts = num_experts
        self.config = config

        # Router network
        self.router_weights = nn.Linear(input_dim, num_experts)

        # Initialize router weights
        nn.init.xavier_uniform_(self.router_weights.weight, gain=1.0)
        nn.init.zeros_(self.router_weights.bias)

    def forward(
        self,
        x: torch.Tensor,
        training: bool = True
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Route inputs to experts.

        Args:
            x: Input tensor [batch_size, seq_len, hidden_dim]
            training: Whether in training mode

        Returns:
            routing_weights: [batch_size, seq_len, num_experts]
            expert_indices: [batch_size, seq_len, top_k]
            aux_loss: Load balancing loss
        """
        batch_size, seq_len, hidden_dim = x.shape

        # Flatten for routing
        x_flat = x.view(-1, hidden_dim)  # [batch_size * seq_len, hidden_dim]

        # Get raw routing logits
        logits = self.router_weights(x_flat)  # [batch_size * seq_len, num_experts]

        # Add noise during training for load balancing
        if training and self.config.router_noise_epsilon > 0:
            noise = torch.randn_like(logits) * self.config.router_noise_epsilon
            logits = logits + noise

        # Add jitter noise if specified
        if self.config.router_jitter_noise > 0:
            jitter = torch.randn_like(logits) * self.config.router_jitter_noise
            logits = logits + jitter

        # Get routing probabilities
        routing_weights = F.softmax(logits, dim=-1)  # [batch_size * seq_len, num_experts]

        # Select top-k experts
        top_k_weights, top_k_indices = torch.topk(
            routing_weights, self.config.top_k, dim=-1
        )  # Both [batch_size * seq_len, top_k]

        # Normalize top-k weights
        top_k_weights = top_k_weights / top_k_weights.sum(dim=-1, keepdim=True)

        # Reshape back to sequence dimension
        routing_weights = routing_weights.view(batch_size, seq_len, self.num_experts)
        expert_indices = top_k_indices.view(batch_size, seq_len, self.config.top_k)
        top_k_weights = top_k_weights.view(batch_size, seq_len, self.config.top_k)

        # Calculate auxiliary loss for load balancing
        aux_loss = torch.tensor(0.0, device=x.device)
        if self.config.use_load_balancing and training:
            # Calculate expert utilization
            expert_usage = routing_weights.mean(dim=[0, 1])  # [num_experts]
            target_usage = torch.ones_like(expert_usage) / self.num_experts

            # Load balancing loss
            aux_loss = self.config.load_balance_coeff * (
                (expert_usage - target_usage) ** 2
            ).sum()

        return top_k_weights, expert_indices, aux_loss


class MoELayer(nn.Module):
    """Mixture of Experts layer with proper device handling."""

    def __init__(self, input_dim: int, output_dim: int, config: MoEConfig, layer_idx: int = 0):
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.config = config
        self.layer_idx = layer_idx

        # Shared expert (always active)
        self.shared_expert = MoEExpert(input_dim, output_dim, config)

        # Routed experts
        self.experts = nn.ModuleList([
            MoEExpert(input_dim, output_dim, config)
            for _ in range(config.num_experts)
        ])

        # Router
        self.router = NoisyTopKRouter(input_dim, config.num_experts, config)

        # Layer norms
        self.pre_norm = nn.LayerNorm(input_dim)
        self.post_norm = nn.LayerNorm(output_dim)

        # Expert utilization tracking
        self.register_buffer('expert_counts', torch.zeros(config.num_experts))

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass through MoE layer.

        Args:
            x: Input tensor [batch_size, seq_len, input_dim]

        Returns:
            output: [batch_size, seq_len, output_dim]
            aux_info: Auxiliary information for loss calculation
        """
        # Ensure input is on correct device
        if x.device != next(self.parameters()).device:
            x = x.to(next(self.parameters()).device)

        batch_size, seq_len, hidden_dim = x.shape

        # Pre-normalization
        x_norm = self.pre_norm(x)

        # Get routing decisions
        training = self.training
        routing_weights, expert_indices, aux_loss = self.router(x_norm, training)

        # Flatten for expert processing
        x_flat = x_norm.view(-1, hidden_dim)  # [batch_size * seq_len, hidden_dim]

        # Process through shared expert
        shared_output = self.shared_expert(x_flat)  # [batch_size * seq_len, output_dim]

        # Combine expert outputs using routing weights
        combined_output = torch.zeros_like(shared_output)  # [batch_size * seq_len, output_dim]

        # Add shared expert contribution (weighted equally across all tokens)
        combined_output = combined_output + shared_output * (1.0 / (self.config.num_experts + 1))

        # Add routed expert contributions
        # expert_indices contains the selected expert IDs for each position
        # routing_weights contains the corresponding weights
        for token_idx in range(batch_size * seq_len):
            batch_idx = token_idx // seq_len
            seq_idx = token_idx % seq_len

            # Get the top-k experts selected for this token
            selected_experts = expert_indices[batch_idx, seq_idx]  # [top_k]
            selected_weights = routing_weights[batch_idx, seq_idx]  # [top_k]

            for k in range(self.config.top_k):
                expert_id = selected_experts[k].item()
                weight = selected_weights[k]

                # Only process if this expert was actually selected for this token
                if weight > 0:
                    # Get the input for this token
                    token_input = x_flat[token_idx:token_idx+1]  # [1, hidden_dim]

                    # Process through the selected expert
                    expert_out = self.experts[expert_id](token_input)  # [1, output_dim]

                    # Add weighted contribution
                    combined_output[token_idx:token_idx+1] += expert_out * weight

        # Reshape back to sequence dimension
        output = combined_output.view(batch_size, seq_len, self.output_dim)

        # Post-normalization
        output = self.post_norm(output)

        # Update expert utilization stats
        if training:
            with torch.no_grad():
                for i in range(self.config.num_experts):
                    expert_count = (expert_indices == i).sum().item()
                    self.expert_counts[i] = self.expert_counts[i] * 0.9 + expert_count * 0.1

        # Auxiliary information
        aux_info = {
            'routing_weights': routing_weights,
            'expert_indices': expert_indices,
            'aux_loss': aux_loss,
            'expert_counts': self.expert_counts.clone(),
            'layer_idx': self.layer_idx
        }

        return output, aux_info


def compute_moe_loss(aux_info: Dict[str, Any]) -> torch.Tensor:
    """Compute total MoE loss including auxiliary losses."""
    total_loss = torch.tensor(0.0, device=aux_info['aux_loss'].device)
    total_loss = total_loss + aux_info['aux_loss']
    return total_loss


def get_moe_statistics(aux_info: Dict[str, Any]) -> Dict[str, Any]:
    """Get MoE statistics for monitoring."""
    expert_counts = aux_info['expert_counts'].cpu().numpy()
    total_tokens = expert_counts.sum()

    return {
        'expert_utilization': expert_counts / total_tokens if total_tokens > 0 else expert_counts,
        'total_experts': len(expert_counts),
        'most_used_expert': int(expert_counts.argmax()),
        'least_used_expert': int(expert_counts.argmin()),
        'load_balance_score': min(1.0, 1.0 / (expert_counts.std() / (expert_counts.mean() + 1e-8) + 1e-8))
    }


# Static router for ONNX export compatibility
class StaticMoERouter(nn.Module):
    """Static router for ONNX export - always routes to first k experts."""

    def __init__(self, original_router: NoisyTopKRouter):
        super().__init__()
        self.num_experts = original_router.num_experts
        self.top_k = original_router.config.top_k

    def forward(self, x: torch.Tensor, training: bool = False) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Static routing for ONNX compatibility."""
        batch_size, seq_len = x.shape[:2]

        # Always route to first top_k experts equally
        routing_weights = torch.ones(batch_size, seq_len, self.top_k, device=x.device) / self.top_k
        expert_indices = torch.arange(self.top_k, device=x.device).unsqueeze(0).unsqueeze(0).expand(batch_size, seq_len, -1)
        aux_loss = torch.tensor(0.0, device=x.device)

        return routing_weights, expert_indices, aux_loss