"""
Mixture of Experts (MoE) Implementation for EmpoorioLM
Implementación completa de arquitectura MoE con routing inteligente y expertos especializados.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING
from dataclasses import dataclass
import math
import logging

# Import from the correct location
try:
    from .empoorio_lm import EmpoorioLMConfig
except ImportError:
    # Fallback for testing
    from ..models.empoorio_lm import EmpoorioLMConfig

if TYPE_CHECKING:
    try:
        from .model import EmpoorioLM
    except ImportError:
        EmpoorioLM = None

logger = logging.getLogger(__name__)


@dataclass
class MoEConfig:
    """Configuración para Mixture of Experts."""
    num_experts: int = 8
    expert_dim: int = 1024
    top_k: int = 2  # Número de expertos a activar por token (como DeepSeek)
    capacity_factor: float = 1.25  # Factor de capacidad para load balancing
    use_load_balancing: bool = True
    expert_dropout: float = 0.1
    router_jitter_noise: float = 0.01  # Ruido para training stability
    router_z_loss_coef: float = 0.001  # Coeficiente para z-loss (auxiliary loss)


class Expert(nn.Module):
    """
    Experto individual especializado en una tarea específica.
    Cada experto es una red feed-forward con capacidad especializada.
    """

    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int, dropout: float = 0.1):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim

        # Arquitectura del experto (similar a MLP pero especializada)
        self.w1 = nn.Linear(input_dim, hidden_dim)
        self.w2 = nn.Linear(hidden_dim, output_dim)
        self.w3 = nn.Linear(input_dim, hidden_dim)  # Para gating como en LLaMA

        self.dropout = nn.Dropout(dropout)
        self.activation = nn.GELU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass del experto.

        Args:
            x: Input tensor [batch_size, seq_len, input_dim]

        Returns:
            Output tensor [batch_size, seq_len, output_dim]
        """
        # Gating mechanism (similar a LLaMA)
        gate = self.activation(self.w3(x))  # [B, T, H]

        # Expert computation with gating
        hidden = self.activation(self.w1(x))  # [B, T, H]
        hidden = hidden * gate  # Element-wise multiplication
        hidden = self.dropout(hidden)

        output = self.w2(hidden)  # [B, T, output_dim]
        return output


class MoERouter(nn.Module):
    """
    Router inteligente que decide qué expertos activar para cada token.
    Implementa Top-K routing con load balancing.
    """

    def __init__(self, input_dim: int, num_experts: int, config: MoEConfig):
        super().__init__()
        self.input_dim = input_dim
        self.num_experts = num_experts
        self.config = config

        # Router network
        self.router = nn.Linear(input_dim, num_experts)
        self.router_jitter_noise = config.router_jitter_noise

        # Load balancing auxiliary loss
        self.aux_loss_coef = config.router_z_loss_coef

    def forward(self, x: torch.Tensor, training: bool = True) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Routing logic con Top-K selection.

        Args:
            x: Input tensor [batch_size, seq_len, input_dim]
            training: Whether in training mode

        Returns:
            Tuple of (routing_weights, expert_indices, auxiliary_loss)
        """
        batch_size, seq_len, _ = x.shape

        # Compute routing logits
        routing_logits = self.router(x)  # [B, T, num_experts]

        # Add noise during training for exploration
        if training and self.router_jitter_noise > 0:
            noise = torch.randn_like(routing_logits) * self.router_jitter_noise
            routing_logits = routing_logits + noise

        # Compute routing probabilities
        routing_probs = F.softmax(routing_logits, dim=-1)  # [B, T, num_experts]

        # Top-K selection
        top_k_probs, top_k_indices = torch.topk(
            routing_probs, self.config.top_k, dim=-1
        )  # [B, T, K], [B, T, K]

        # Normalize top-k probabilities
        routing_weights = top_k_probs / top_k_probs.sum(dim=-1, keepdim=True)  # [B, T, K]

        # Auxiliary loss for load balancing (z-loss)
        auxiliary_loss = self._compute_auxiliary_loss(routing_logits)

        return routing_weights, top_k_indices, auxiliary_loss

    def _compute_auxiliary_loss(self, routing_logits: torch.Tensor) -> torch.Tensor:
        """Compute auxiliary loss for load balancing."""
        if not self.config.use_load_balancing:
            return torch.tensor(0.0, device=routing_logits.device)

        # Compute expert usage frequency
        routing_probs = F.softmax(routing_logits, dim=-1)
        expert_usage = routing_probs.mean(dim=(0, 1))  # [num_experts]

        # Ideal uniform distribution
        ideal_usage = torch.ones_like(expert_usage) / self.num_experts

        # Z-loss: measure deviation from uniform distribution
        z_loss = torch.sum(expert_usage * expert_usage) * self.num_experts

        return z_loss * self.aux_loss_coef


class SparseMoELayer(nn.Module):
    """
    Capa MoE completa que combina routing y expertos.
    Implementa sparse activation para eficiencia.
    """

    def __init__(self, input_dim: int, output_dim: int, config: MoEConfig):
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.config = config

        # Router
        self.router = MoERouter(input_dim, config.num_experts, config)

        # Experts
        self.experts = nn.ModuleList([
            Expert(input_dim, config.expert_dim, output_dim, config.expert_dropout)
            for _ in range(config.num_experts)
        ])

        # Shared expert (optional, for base capabilities)
        self.shared_expert = Expert(input_dim, config.expert_dim, output_dim, config.expert_dropout)

        logger.info(f"Initialized MoE layer with {config.num_experts} experts, top_k={config.top_k}")

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass de la capa MoE.

        Args:
            x: Input tensor [batch_size, seq_len, input_dim]

        Returns:
            Tuple of (output, auxiliary_loss)
        """
        batch_size, seq_len, _ = x.shape

        # Get routing decisions
        routing_weights, expert_indices, aux_loss = self.router(x, self.training)

        # Initialize output tensor
        output = torch.zeros(batch_size, seq_len, self.output_dim, device=x.device)

        # Process each expert
        for expert_idx in range(self.config.num_experts):
            # Find tokens routed to this expert
            mask = (expert_indices == expert_idx).any(dim=-1)  # [B, T]
            if not mask.any():
                continue

            # Get routing weights for this expert
            expert_mask = (expert_indices == expert_idx)
            weights = torch.zeros_like(expert_mask, dtype=routing_weights.dtype, device=x.device)
            weights[expert_mask] = routing_weights[expert_mask]

            # Sum weights across top-k dimension
            expert_weights = weights.sum(dim=-1)  # [B, T]

            # Apply expert to relevant tokens
            expert_input = x[mask]  # [N, input_dim] where N is number of routed tokens
            expert_output = self.experts[expert_idx](expert_input.unsqueeze(0)).squeeze(0)  # [N, output_dim]

            # Weight and add to output
            weighted_output = expert_output * expert_weights[mask].unsqueeze(-1)
            output[mask] += weighted_output

        # Add shared expert contribution
        shared_output = self.shared_expert(x)
        output += shared_output

        return output, aux_loss


class MoETransformerBlock(nn.Module):
    """
    Transformer block con MoE en lugar de MLP estándar.
    Reemplaza el MLP tradicional con una capa MoE.
    """

    def __init__(self, config: EmpoorioLMConfig, moe_config: MoEConfig):
        super().__init__()
        self.config = config
        self.moe_config = moe_config

        # Layer norm
        self.ln_1 = nn.LayerNorm(config.n_embd, eps=config.layer_norm_epsilon)
        self.ln_2 = nn.LayerNorm(config.n_embd, eps=config.layer_norm_epsilon)

        # Simplified attention for MoE testing (avoid circular imports)
        self.attn = nn.MultiheadAttention(
            embed_dim=config.n_embd,
            num_heads=config.n_head,
            batch_first=True
        )

        # MoE layer en lugar de MLP estándar
        self.moe = SparseMoELayer(
            input_dim=config.n_embd,
            output_dim=config.n_embd,
            config=moe_config
        )

        # Residual connections
        self.use_parallel_residual = config.use_parallel_residual

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        past_key_value: Optional[Tuple[torch.Tensor]] = None,
        output_attentions: bool = False,
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor], Optional[Tuple[torch.Tensor]], torch.Tensor]:
        """
        Forward pass del transformer block con MoE.

        Args:
            hidden_states: Input tensor [batch_size, seq_len, n_embd]
            attention_mask: Attention mask
            past_key_value: Past key/value states
            output_attentions: Whether to return attention weights

        Returns:
            Tuple of (output, attentions, past_key_value, aux_loss)
        """
        residual = hidden_states

        # Layer norm and attention
        hidden_states_norm = self.ln_1(hidden_states)
        # Use simplified attention
        attn_output, attentions = self.attn(
            hidden_states_norm, hidden_states_norm, hidden_states_norm,
            key_padding_mask=attention_mask
        )
        present_key_value = None  # Not implemented for simplified version

        if self.use_parallel_residual:
            # Parallel residual: add residual after attention
            hidden_states = residual + attn_output
            residual = hidden_states
        else:
            # Sequential residual
            hidden_states = residual + attn_output

        # Layer norm and MoE
        hidden_states = self.ln_2(hidden_states)
        moe_output, aux_loss = self.moe(hidden_states)

        # Final residual connection
        hidden_states = residual + moe_output

        return hidden_states, attentions, present_key_value, aux_loss


class MoEEmpoorioLM(nn.Module):
    """
    EmpoorioLM con arquitectura Mixture of Experts.
    Reemplaza los MLP estándar con capas MoE para mayor eficiencia y especialización.
    """

    def __init__(self, config: EmpoorioLMConfig, moe_config: Optional[MoEConfig] = None):
        super().__init__()
        self.config = config
        self.moe_config = moe_config or MoEConfig()

        # Token and position embeddings (igual que el modelo base)
        self.wte = nn.Embedding(config.vocab_size, config.n_embd)
        self.wpe = nn.Embedding(config.n_positions, config.n_embd)
        self.drop = nn.Dropout(config.embd_pdrop)

        # Transformer blocks con MoE
        self.h = nn.ModuleList([
            MoETransformerBlock(config, self.moe_config)
            for _ in range(config.n_layer)
        ])

        # Final layer norm
        self.ln_f = nn.LayerNorm(config.n_embd, eps=config.layer_norm_epsilon)

        # Language modeling head
        self.lm_head = nn.Linear(config.n_embd, config.vocab_size, bias=False)

        # Tie weights
        self.lm_head.weight = self.wte.weight

        # Initialize weights
        self.apply(self._init_weights)

        logger.info(f"MoEEmpoorioLM initialized with {self.moe_config.num_experts} experts per layer")

    def _init_weights(self, module):
        """Initialize model weights."""
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)
        elif isinstance(module, nn.LayerNorm):
            torch.nn.init.zeros_(module.bias)
            torch.nn.init.ones_(module.weight)

    def get_num_parameters(self) -> int:
        """Get total number of parameters."""
        return sum(p.numel() for p in self.parameters())

    def get_num_trainable_parameters(self) -> int:
        """Get number of trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
        use_cache: bool = False,
        output_attentions: bool = False,
        output_hidden_states: bool = False,
    ) -> Dict[str, Any]:
        """
        Forward pass del modelo MoE.

        Args:
            input_ids: Input token IDs [batch_size, seq_len]
            attention_mask: Attention mask [batch_size, seq_len]
            labels: Labels for language modeling [batch_size, seq_len]
            use_cache: Whether to return past key/values
            output_attentions: Whether to return attention weights
            output_hidden_states: Whether to return hidden states

        Returns:
            Dictionary with model outputs
        """
        device = input_ids.device
        batch_size, seq_len = input_ids.size()

        # Token and position embeddings
        token_embeddings = self.wte(input_ids)
        position_ids = torch.arange(seq_len, dtype=torch.long, device=device)
        position_ids = position_ids.unsqueeze(0).expand(batch_size, -1)
        position_embeddings = self.wpe(position_ids)
        hidden_states = token_embeddings + position_embeddings
        hidden_states = self.drop(hidden_states)

        # Initialize outputs
        all_hidden_states = () if output_hidden_states else None
        all_attentions = () if output_attentions else None
        all_past_key_values = () if use_cache else None
        total_aux_loss = 0.0

        # Transformer blocks
        for i, block in enumerate(self.h):
            if output_hidden_states:
                all_hidden_states = all_hidden_states + (hidden_states,)

            outputs = block(
                hidden_states,
                attention_mask=attention_mask,
                past_key_value=None,  # TODO: Implement past key values for MoE
                output_attentions=output_attentions,
            )

            hidden_states, attentions, present_key_value, aux_loss = outputs
            total_aux_loss += aux_loss

            if output_attentions:
                all_attentions = all_attentions + (attentions,)

            if use_cache:
                all_past_key_values = all_past_key_values + (present_key_value,)

        # Final layer norm
        hidden_states = self.ln_f(hidden_states)

        if output_hidden_states:
            all_hidden_states = all_hidden_states + (hidden_states,)

        # Language modeling logits
        lm_logits = self.lm_head(hidden_states)

        # Loss calculation
        loss = None
        if labels is not None:
            shift_logits = lm_logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()

            loss_fct = nn.CrossEntropyLoss()
            lm_loss = loss_fct(
                shift_logits.view(-1, shift_logits.size(-1)),
                shift_labels.view(-1)
            )

            # Add auxiliary loss for load balancing
            loss = lm_loss + total_aux_loss

        return {
            "loss": loss,
            "logits": lm_logits,
            "past_key_values": all_past_key_values,
            "hidden_states": all_hidden_states,
            "attentions": all_attentions,
            "auxiliary_loss": total_aux_loss,
        }

    @torch.no_grad()
    def generate(
        self,
        input_ids: torch.Tensor,
        max_length: int = 50,
        temperature: float = 1.0,
        top_k: Optional[int] = None,
        top_p: Optional[float] = None,
        do_sample: bool = True,
        pad_token_id: int = 0,
        eos_token_id: int = 2,
        repetition_penalty: float = 1.0,
    ) -> torch.Tensor:
        """
        Generate text using MoE model.
        """
        self.eval()

        batch_size = input_ids.shape[0]
        generated = input_ids.clone()

        for _ in range(max_length - input_ids.shape[1]):
            outputs = self(generated)
            next_token_logits = outputs["logits"][:, -1, :]

            # Apply temperature
            if temperature != 1.0:
                next_token_logits = next_token_logits / temperature

            # Apply repetition penalty
            if repetition_penalty != 1.0:
                for batch_idx in range(batch_size):
                    for token_id in set(generated[batch_idx].tolist()):
                        next_token_logits[batch_idx, token_id] /= repetition_penalty

            # Apply top-k sampling
            if top_k is not None:
                top_k_logits, _ = torch.topk(next_token_logits, top_k, dim=-1)
                next_token_logits = torch.where(
                    next_token_logits < top_k_logits[:, -1:],
                    torch.full_like(next_token_logits, float('-inf')),
                    next_token_logits
                )

            # Apply top-p sampling
            if top_p is not None:
                sorted_logits, sorted_indices = torch.sort(next_token_logits, descending=True)
                sorted_probs = F.softmax(sorted_logits, dim=-1)
                cumulative_probs = torch.cumsum(sorted_probs, dim=-1)

                sorted_logits = torch.where(
                    cumulative_probs > top_p,
                    torch.full_like(sorted_logits, float('-inf')),
                    sorted_logits
                )

                next_token_logits = torch.gather(
                    sorted_logits,
                    dim=-1,
                    index=torch.argsort(sorted_indices, dim=-1)
                )

            # Sample next token
            if do_sample:
                probs = F.softmax(next_token_logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)
            else:
                next_token = torch.argmax(next_token_logits, dim=-1, keepdim=True)

            generated = torch.cat([generated, next_token], dim=1)

            if eos_token_id is not None and (next_token == eos_token_id).any():
                break

        return generated

    def get_expert_utilization_stats(self) -> Dict[str, Any]:
        """Get statistics about expert utilization across layers."""
        stats = {}

        for layer_idx, block in enumerate(self.h):
            if hasattr(block, 'moe') and hasattr(block.moe, 'router'):
                # Get expert usage statistics from router
                # This would require tracking during forward passes
                stats[f"layer_{layer_idx}"] = {
                    "num_experts": self.moe_config.num_experts,
                    "top_k": self.moe_config.top_k,
                    # Add more stats as needed
                }

        return stats


def create_moe_empoorio_lm(
    base_config: EmpoorioLMConfig,
    moe_config: Optional[MoEConfig] = None
) -> MoEEmpoorioLM:
    """
    Factory function para crear EmpoorioLM con MoE.

    Args:
        base_config: Configuración base del modelo
        moe_config: Configuración específica de MoE

    Returns:
        Modelo MoE inicializado
    """
    return MoEEmpoorioLM(base_config, moe_config)


# Función de conveniencia para convertir modelo base a MoE
def convert_to_moe_model(
    base_model: 'EmpoorioLM',
    moe_config: Optional[MoEConfig] = None
) -> MoEEmpoorioLM:
    """
    Convierte un modelo EmpoorioLM base a arquitectura MoE.

    Args:
        base_model: Modelo base a convertir
        moe_config: Configuración MoE

    Returns:
        Modelo convertido con MoE
    """
    moe_config = moe_config or MoEConfig()

    # Crear modelo MoE con la misma configuración base
    moe_model = MoEEmpoorioLM(base_model.config, moe_config)

    # Copiar embeddings y head del modelo base
    moe_model.wte.load_state_dict(base_model.wte.state_dict())
    moe_model.wpe.load_state_dict(base_model.wpe.state_dict())
    moe_model.lm_head.load_state_dict(base_model.lm_head.state_dict())
    moe_model.ln_f.load_state_dict(base_model.ln_f.state_dict())

    # Para los transformer blocks, solo copiar attention layers
    # Los MoE layers se inicializan desde cero
    for moe_block, base_block in zip(moe_model.h, base_model.h):
        moe_block.attn.load_state_dict(base_block.attn.state_dict())
        moe_block.ln_1.load_state_dict(base_block.ln_1.state_dict())
        moe_block.ln_2.load_state_dict(base_block.ln_2.state_dict())

    logger.info("Converted base EmpoorioLM to MoE architecture")
    return moe_model