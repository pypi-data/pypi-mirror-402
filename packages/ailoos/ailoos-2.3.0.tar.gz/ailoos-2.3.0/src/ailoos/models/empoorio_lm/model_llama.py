#!/usr/bin/env python3
"""
EmpoorioLM - Independent Llama-3 Style Architecture
Completely original implementation with our own copyright.
Inspired by open research, not dependent on any other models.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass

from ...core.config import Config
from ...utils.logging import AiloosLogger


def apply_rotary_pos_emb(tensor: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
    """Apply rotary position embedding to input tensor."""
    x_even = tensor[..., ::2]
    x_odd = tensor[..., 1::2]
    return torch.cat([x_even * cos - x_odd * sin, x_odd * cos + x_even * sin], dim=-1)


@dataclass
class EmpoorioLMConfig:
    """Configuration for EmpoorioLM model."""

    vocab_size: int = 32000
    hidden_size: int = 4096
    num_hidden_layers: int = 32
    num_attention_heads: int = 32
    num_key_value_heads: int = 32  # For GQA
    intermediate_size: int = 11008
    hidden_act: str = "silu"
    max_position_embeddings: int = 4096
    initializer_range: float = 0.02
    rms_norm_eps: float = 1e-6
    use_cache: bool = True
    pad_token_id: Optional[int] = None
    bos_token_id: int = 1
    eos_token_id: int = 2
    tie_word_embeddings: bool = False

    # RoPE parameters
    rope_theta: float = 10000.0
    rope_scaling: Optional[Dict[str, Any]] = None

    # Attention parameters
    attention_bias: bool = False
    attention_dropout: float = 0.0

    # MLP parameters
    mlp_bias: bool = False

    # Quantization
    quantization_config: Optional[Dict[str, Any]] = None

    # Model configuration
    use_return_dict: bool = True
    output_attentions: bool = False
    output_hidden_states: bool = False

    def __post_init__(self):
        if self.num_key_value_heads is None:
            self.num_key_value_heads = self.num_attention_heads


class EmpoorioRMSNorm(nn.Module):
    """RMS Normalization as used in Llama-3."""

    def __init__(self, hidden_size: int, eps: float = 1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(hidden_size))
        self.eps = eps

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        input_dtype = hidden_states.dtype
        hidden_states = hidden_states.to(torch.float32)
        variance = hidden_states.pow(2).mean(-1, keepdim=True)
        hidden_states = hidden_states * torch.rsqrt(variance + self.eps)
        return self.weight * hidden_states.to(input_dtype)


class EmpoorioRotaryEmbedding(nn.Module):
    """Rotary Position Embedding (RoPE) with YaRN support."""

    def __init__(self, dim: int, max_position_embeddings: int = 2048, base: float = 10000.0,
                 scaling_factor: float = 1.0, rope_type: str = "default"):
        super().__init__()
        self.dim = dim
        self.max_position_embeddings = max_position_embeddings
        self.base = base
        self.scaling_factor = scaling_factor
        self.rope_type = rope_type

        # Precompute frequencies
        self._compute_freqs()

    def _compute_freqs(self):
        """Compute rotation frequencies."""
        if self.rope_type == "yarn":
            # YaRN: Yet Another RoPE
            freqs = 1.0 / (self.base ** (torch.arange(0, self.dim, 2).float() / self.dim))
            freqs = freqs * self.scaling_factor
        else:
            # Standard RoPE
            freqs = 1.0 / (self.base ** (torch.arange(0, self.dim, 2).float() / self.dim))

        self.register_buffer("freqs", freqs)

    def forward(self, position_ids: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get cos and sin for rotary embedding."""
        # position_ids: [batch_size, seq_length]

        freqs = self.freqs.to(position_ids.device)

        # Compute cos and sin for each position
        angles = position_ids.unsqueeze(-1) * freqs.unsqueeze(0).unsqueeze(0)  # [batch_size, seq_length, dim//2]
        cos = torch.cos(angles)
        sin = torch.sin(angles)

        # Reshape for broadcasting
        cos = cos.unsqueeze(1)  # [batch_size, 1, seq_length, dim//2]
        sin = sin.unsqueeze(1)

        return cos, sin


# Removed old apply_rotary_pos_emb


class EmpoorioAttention(nn.Module):
    """Multi-head attention with GQA (Grouped Query Attention)."""

    def __init__(self, config: EmpoorioLMConfig):
        super().__init__()
        self.config = config
        self.hidden_size = config.hidden_size
        self.num_heads = config.num_attention_heads
        self.head_dim = self.hidden_size // self.num_heads
        self.num_key_value_heads = config.num_key_value_heads
        self.num_key_value_groups = self.num_heads // self.num_key_value_heads
        self.max_position_embeddings = config.max_position_embeddings

        if (self.head_dim * self.num_heads) != self.hidden_size:
            raise ValueError(
                f"hidden_size must be divisible by num_heads (got `hidden_size`: {self.hidden_size}"
                f" and `num_heads`: {self.num_heads})."
            )

        # Attention weights
        self.q_proj = nn.Linear(self.hidden_size, self.num_heads * self.head_dim, bias=config.attention_bias)
        self.k_proj = nn.Linear(self.hidden_size, self.num_key_value_heads * self.head_dim, bias=config.attention_bias)
        self.v_proj = nn.Linear(self.hidden_size, self.num_key_value_heads * self.head_dim, bias=config.attention_bias)
        self.o_proj = nn.Linear(self.num_heads * self.head_dim, self.hidden_size, bias=config.attention_bias)

        self.attention_dropout = config.attention_dropout

        # Rotary embeddings
        self.rotary_emb = EmpoorioRotaryEmbedding(
            self.head_dim,
            max_position_embeddings=self.max_position_embeddings,
            base=config.rope_theta,
        )

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.LongTensor] = None,
        past_key_value: Optional[Tuple[torch.Tensor]] = None,
        output_attentions: bool = False,
        use_cache: bool = False,
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor], Optional[Tuple[torch.Tensor]]]:
        bsz, q_len, _ = hidden_states.size()

        if self.config.num_key_value_heads != self.config.num_attention_heads:
            # GQA: Grouped Query Attention
            query_states = self.q_proj(hidden_states).view(bsz, q_len, self.num_heads, self.head_dim).transpose(1, 2)
            key_states = self.k_proj(hidden_states).view(bsz, q_len, self.num_key_value_heads, self.head_dim).transpose(1, 2)
            value_states = self.v_proj(hidden_states).view(bsz, q_len, self.num_key_value_heads, self.head_dim).transpose(1, 2)
        else:
            # Standard MHA
            query_states = self.q_proj(hidden_states).view(bsz, q_len, self.num_heads, self.head_dim).transpose(1, 2)
            key_states = self.k_proj(hidden_states).view(bsz, q_len, self.num_heads, self.head_dim).transpose(1, 2)
            value_states = self.v_proj(hidden_states).view(bsz, q_len, self.num_heads, self.head_dim).transpose(1, 2)

        kv_seq_len = key_states.shape[-2]
        if past_key_value is not None:
            kv_seq_len += past_key_value[0].shape[-2]

        # Apply RoPE
        if position_ids is None:
            position_ids = torch.arange(q_len, device=hidden_states.device).unsqueeze(0)

        cos, sin = self.rotary_emb(position_ids)
        # Expand cos and sin to match number of heads
        cos = cos.repeat(1, self.num_heads, 1, 1)
        sin = sin.repeat(1, self.num_heads, 1, 1)
        query_states = apply_rotary_pos_emb(query_states, cos, sin)
        key_states = apply_rotary_pos_emb(key_states, cos, sin)

        # Handle past key/value states
        if past_key_value is not None:
            key_states = torch.cat([past_key_value[0], key_states], dim=2)
            value_states = torch.cat([past_key_value[1], value_states], dim=2)

        past_key_value = (key_states, value_states) if use_cache else None

        # Repeat key/value heads for GQA
        if self.num_key_value_groups > 1:
            key_states = key_states.repeat_interleave(self.num_key_value_groups, dim=1)
            value_states = value_states.repeat_interleave(self.num_key_value_groups, dim=1)

        # Attention computation
        attn_weights = torch.matmul(query_states, key_states.transpose(2, 3)) / math.sqrt(self.head_dim)

        if attention_mask is not None:
            attn_weights = attn_weights + attention_mask

        # Upcast attention to fp32 if necessary
        if attn_weights.dtype == torch.float16:
            attn_weights = attn_weights.to(torch.float32)

        attn_weights = F.softmax(attn_weights, dim=-1, dtype=torch.float32).to(query_states.dtype)
        attn_weights = F.dropout(attn_weights, p=self.attention_dropout, training=self.training)

        attn_output = torch.matmul(attn_weights, value_states)

        # Reshape and project
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.reshape(bsz, q_len, self.hidden_size)
        attn_output = self.o_proj(attn_output)

        if not output_attentions:
            attn_weights = None

        return attn_output, attn_weights, past_key_value


class EmpoorioMLP(nn.Module):
    """MLP block with SwiGLU activation."""

    def __init__(self, config: EmpoorioLMConfig):
        super().__init__()
        self.config = config
        self.hidden_size = config.hidden_size
        self.intermediate_size = config.intermediate_size

        self.gate_proj = nn.Linear(self.hidden_size, self.intermediate_size, bias=config.mlp_bias)
        self.up_proj = nn.Linear(self.hidden_size, self.intermediate_size, bias=config.mlp_bias)
        self.down_proj = nn.Linear(self.intermediate_size, self.hidden_size, bias=config.mlp_bias)
        self.act_fn = F.silu  # SwiGLU activation

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        down_proj = self.down_proj(self.act_fn(self.gate_proj(x)) * self.up_proj(x))
        return down_proj


class EmpoorioDecoderLayer(nn.Module):
    """Decoder layer with pre-norm architecture."""

    def __init__(self, config: EmpoorioLMConfig):
        super().__init__()
        self.hidden_size = config.hidden_size

        self.self_attn = EmpoorioAttention(config)
        self.mlp = EmpoorioMLP(config)

        self.input_layernorm = EmpoorioRMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.post_attention_layernorm = EmpoorioRMSNorm(config.hidden_size, eps=config.rms_norm_eps)

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.LongTensor] = None,
        past_key_value: Optional[Tuple[torch.Tensor]] = None,
        output_attentions: Optional[bool] = False,
        use_cache: Optional[bool] = False,
    ) -> Tuple[torch.FloatTensor, Optional[Tuple[torch.FloatTensor, torch.FloatTensor]]]:
        """
        Args:
            hidden_states (`torch.FloatTensor`): input to the layer of shape `(batch, seq_len, embed_dim)`
            attention_mask (`torch.FloatTensor`, *optional*): attention mask of size
                `(batch, 1, tgt_len, src_len)` where padding elements are indicated by very large negative values.
            output_attentions (`bool`, *optional*):
                Whether or not to return the attentions tensors of all attention layers.
            use_cache (`bool`, *optional*):
                If set to `True`, `past_key_values` key value states are returned and can be used to speed up decoding
                (see `past_key_values`).
            past_key_value (`Tuple(torch.FloatTensor)`, *optional*): cached past key and value projection states
        """

        residual = hidden_states

        hidden_states = self.input_layernorm(hidden_states)

        # Self Attention
        hidden_states, self_attn_weights, present_key_value = self.self_attn(
            hidden_states=hidden_states,
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_value=past_key_value,
            output_attentions=output_attentions,
            use_cache=use_cache,
        )
        hidden_states = residual + hidden_states

        # Fully Connected
        residual = hidden_states
        hidden_states = self.post_attention_layernorm(hidden_states)
        hidden_states = self.mlp(hidden_states)
        hidden_states = residual + hidden_states

        outputs = (hidden_states,)

        if output_attentions:
            outputs += (self_attn_weights,)

        if use_cache:
            outputs += (present_key_value,)

        return outputs


class EmpoorioPreTrainedModel(nn.Module):
    """Base class for EmpoorioLM models."""

    def __init__(self, config: EmpoorioLMConfig):
        super().__init__()
        self.config = config

    def _init_weights(self, module):
        """Initialize weights."""
        std = self.config.initializer_range
        if isinstance(module, nn.Linear):
            module.weight.data.normal_(mean=0.0, std=std)
            if module.bias is not None:
                module.bias.data.zero_()
        elif isinstance(module, nn.Embedding):
            module.weight.data.normal_(mean=0.0, std=std)
            if module.padding_idx is not None:
                module.weight.data[module.padding_idx].zero_()


class EmpoorioModel(EmpoorioPreTrainedModel):
    """EmpoorioLM model without head."""

    def __init__(self, config: EmpoorioLMConfig):
        super().__init__(config)
        self.padding_idx = config.pad_token_id
        self.vocab_size = config.vocab_size

        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size, self.padding_idx)
        self.layers = nn.ModuleList(
            [EmpoorioDecoderLayer(config) for _ in range(config.num_hidden_layers)]
        )
        self.norm = EmpoorioRMSNorm(config.hidden_size, eps=config.rms_norm_eps)

        self.apply(self._init_weights)

    def get_input_embeddings(self):
        return self.embed_tokens

    def set_input_embeddings(self, value):
        self.embed_tokens = value

    def forward(
        self,
        input_ids: torch.LongTensor = None,
        attention_mask: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.LongTensor] = None,
        past_key_values: Optional[List[torch.FloatTensor]] = None,
        inputs_embeds: Optional[torch.FloatTensor] = None,
        use_cache: Optional[bool] = None,
        output_attentions: Optional[bool] = False,
        output_hidden_states: Optional[bool] = False,
        return_dict: Optional[bool] = None,
    ) -> Dict[str, Any]:
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        use_cache = use_cache if use_cache is not None else self.config.use_cache

        return_dict = return_dict if return_dict is not None else self.config.use_return_dict

        # retrieve input_ids and inputs_embeds
        if input_ids is not None and inputs_embeds is not None:
            raise ValueError("You cannot specify both input_ids and inputs_embeds at the same time")
        elif input_ids is not None:
            batch_size, seq_length = input_ids.shape
        elif inputs_embeds is not None:
            batch_size, seq_length, _ = inputs_embeds.shape
        else:
            raise ValueError("You have to specify either input_ids or inputs_embeds")

        seq_length_with_past = seq_length
        past_key_values_length = 0

        if past_key_values is not None:
            past_key_values_length = past_key_values[0][0].shape[2]
            seq_length_with_past = seq_length_with_past + past_key_values_length

        if position_ids is None:
            device = input_ids.device if input_ids is not None else inputs_embeds.device
            position_ids = torch.arange(
                past_key_values_length, seq_length + past_key_values_length, dtype=torch.long, device=device
            )
            position_ids = position_ids.unsqueeze(0).expand(batch_size, -1)

        if inputs_embeds is None:
            inputs_embeds = self.embed_tokens(input_ids)

        # embed positions
        if hasattr(self, "embed_positions"):
            # Legacy RoPE-less models
            positions = self.embed_positions(input_ids)
            hidden_states = inputs_embeds + positions
        else:
            hidden_states = inputs_embeds

        # Create causal attention mask
        # if attention_mask is None:
        #     attention_mask = torch.ones((batch_size, seq_length), device=inputs_embeds.device)

        # # Create causal mask for self-attention
        # causal_mask = torch.triu(torch.ones(seq_length, seq_length, device=inputs_embeds.device), diagonal=1).bool()
        # causal_mask = causal_mask.unsqueeze(0).unsqueeze(1)  # [1, 1, seq_len, seq_len]

        # # Combine with attention_mask if provided
        # attention_mask = attention_mask.unsqueeze(1).unsqueeze(2)  # [batch, 1, 1, seq_len]
        # attention_mask = attention_mask.expand(-1, -1, seq_length, -1)  # [batch, 1, seq_len, seq_len]
        # attention_mask = attention_mask.masked_fill(causal_mask, float('-inf'))

        # decoder layers
        all_hidden_states = () if output_hidden_states else None
        all_self_attns = () if output_attentions else None
        next_decoder_cache = () if use_cache else None

        for idx, decoder_layer in enumerate(self.layers):
            if output_hidden_states:
                all_hidden_states += (hidden_states,)

            past_key_value = past_key_values[idx] if past_key_values is not None else None

            layer_outputs = decoder_layer(
                hidden_states,
                attention_mask=attention_mask,
                position_ids=position_ids,
                past_key_value=past_key_value,
                output_attentions=output_attentions,
                use_cache=use_cache,
            )

            hidden_states = layer_outputs[0]

            if use_cache:
                next_decoder_cache += (layer_outputs[2 if output_attentions else 1],)

            if output_attentions:
                all_self_attns += (layer_outputs[1],)

        hidden_states = self.norm(hidden_states)

        # add hidden states from the last decoder layer
        if output_hidden_states:
            all_hidden_states += (hidden_states,)

        next_cache = next_decoder_cache if use_cache else None

        return {
            "last_hidden_state": hidden_states,
            "past_key_values": next_cache,
            "hidden_states": all_hidden_states,
            "attentions": all_self_attns,
        }


class EmpoorioForCausalLM(EmpoorioPreTrainedModel):
    """EmpoorioLM model with causal language modeling head."""

    def __init__(self, config: EmpoorioLMConfig):
        super().__init__(config)
        self.model = EmpoorioModel(config)
        self.vocab_size = config.vocab_size
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)

        # Initialize weights and apply final processing
        self.apply(self._init_weights)

    def get_input_embeddings(self):
        return self.model.embed_tokens

    def set_input_embeddings(self, value):
        self.model.embed_tokens = value

    def get_output_embeddings(self):
        return self.lm_head

    def set_output_embeddings(self, new_embeddings):
        self.lm_head = new_embeddings

    def set_decoder(self, decoder):
        self.model = decoder

    def get_decoder(self):
        return self.model

    def forward(
        self,
        input_ids: torch.LongTensor = None,
        attention_mask: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.LongTensor] = None,
        past_key_values: Optional[List[torch.FloatTensor]] = None,
        inputs_embeds: Optional[torch.FloatTensor] = None,
        labels: Optional[torch.LongTensor] = None,
        use_cache: Optional[bool] = None,
        output_attentions: Optional[bool] = False,
        output_hidden_states: Optional[bool] = False,
        return_dict: Optional[bool] = None,
    ) -> Dict[str, Any]:
        r"""
        Args:
            labels (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
                Labels for computing the masked language modeling loss. Indices should either be in `[0, ...,
                config.vocab_size]` or -100 (see `input_ids` docstring). Tokens with indices set to `-100` are ignored
                (masked), the loss is only computed for the tokens with labels in `[0, ..., config.vocab_size]`.

        Returns:
            Dict containing:
            - loss: Optional language modeling loss
            - logits: Prediction scores
            - past_key_values: Past key values for caching
            - hidden_states: Hidden states if requested
            - attentions: Attention weights if requested
        """

        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.use_return_dict

        # decoder outputs consists of (dec_features, layer_state, dec_hidden, dec_attn)
        outputs = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_values=past_key_values,
            inputs_embeds=inputs_embeds,
            use_cache=use_cache,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        hidden_states = outputs["last_hidden_state"]
        logits = self.lm_head(hidden_states)
        logits = logits.float()

        loss = None
        if labels is not None:
            # Shift so that tokens < n predict n
            if attention_mask is not None:
                shift_attention_mask = attention_mask[..., 1:]
                shift_logits = logits[..., :-1, :][shift_attention_mask.to(logits.device) != 0].contiguous()
                shift_labels = labels[..., 1:][shift_attention_mask.to(labels.device) != 0].contiguous()
            else:
                shift_logits = logits[..., :-1, :].contiguous()
                shift_labels = labels[..., 1:].contiguous()

            # Flatten the tokens
            loss_fct = nn.CrossEntropyLoss()
            shift_logits = shift_logits.view(-1, self.config.vocab_size)
            shift_labels = shift_labels.view(-1)
            # Enable model parallelism
            shift_labels = shift_labels.to(shift_logits.device)
            loss = loss_fct(shift_logits, shift_labels)

        return {
            "loss": loss,
            "logits": logits,
            "past_key_values": outputs["past_key_values"],
            "hidden_states": outputs["hidden_states"],
            "attentions": outputs["attentions"],
        }

    @staticmethod
    def _reorder_cache(past_key_values, beam_idx):
        reordered_past = ()
        for layer_past in past_key_values:
            reordered_past += (
                tuple(past_state.index_select(0, beam_idx.to(past_state.device)) for past_state in layer_past),
            )
        return reordered_past


# Factory functions for different model sizes
def create_empoorio_baby_titan() -> EmpoorioForCausalLM:
    """Create EmpoorioLM Baby Titan model (small curriculum starting point)."""
    config = EmpoorioLMConfig(
        hidden_size=512,
        num_hidden_layers=6,
        num_attention_heads=8,
        intermediate_size=2048,
        max_position_embeddings=2048,  # Smaller context for efficiency
    )
    return EmpoorioForCausalLM(config)


def create_empoorio_titan() -> EmpoorioForCausalLM:
    """Create EmpoorioLM Titan model (medium curriculum step)."""
    config = EmpoorioLMConfig(
        hidden_size=1024,
        num_hidden_layers=12,
        num_attention_heads=16,
        intermediate_size=4096,
        max_position_embeddings=2048,
    )
    return EmpoorioForCausalLM(config)


def create_empoorio_7b() -> EmpoorioForCausalLM:
    """Create EmpoorioLM 7B model."""
    config = EmpoorioLMConfig(
        hidden_size=4096,
        num_hidden_layers=32,
        num_attention_heads=32,
        intermediate_size=11008,
    )
    return EmpoorioForCausalLM(config)


def create_empoorio_13b() -> EmpoorioForCausalLM:
    """Create EmpoorioLM 13B model."""
    config = EmpoorioLMConfig(
        hidden_size=5120,
        num_hidden_layers=40,
        num_attention_heads=40,
        intermediate_size=13824,
    )
    return EmpoorioForCausalLM(config)


def create_empoorio_30b() -> EmpoorioForCausalLM:
    """Create EmpoorioLM 30B model."""
    config = EmpoorioLMConfig(
        hidden_size=6656,
        num_hidden_layers=60,
        num_attention_heads=52,
        intermediate_size=17920,
    )
    return EmpoorioForCausalLM(config)


def create_empoorio_65b() -> EmpoorioForCausalLM:
    """Create EmpoorioLM 65B model."""
    config = EmpoorioLMConfig(
        hidden_size=8192,
        num_hidden_layers=80,
        num_attention_heads=64,
        intermediate_size=22016,
    )
    return EmpoorioForCausalLM(config)