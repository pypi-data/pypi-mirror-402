"""
EmpoorioLM Model with MoE Integration
Modelo completo de EmpoorioLM con integración de Mixture of Experts.
"""

import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from typing import Optional, Dict, Any, Union, List, Tuple
from pathlib import Path
import json
import logging

from .model_config import EmpoorioLMConfig
from .moe import MoELayer, MoEConfig, compute_moe_loss, get_moe_statistics
from .rope import NTKAwareRoPE, create_rope_for_context
from .lora import LoRAModelWrapper
from .tokenizer import EmpoorioBPETokenizer
from ..attention.yarn_rope import YaRNRotaryEmbedding, YaRNConfig
from ..attention.sliding_window_attention import SlidingWindowAttention
from ..attention.flash_attention import FlashAttention, FlashAttentionConfig, create_flash_attention
from ..attention.optimized_attention import OptimizedAttentionEngine
# MIRAS and Liquid Memory imports removed to avoid circular imports
# These will be imported dynamically when needed

logger = logging.getLogger(__name__)


class GPT2Attention(nn.Module):
    """Multi-head attention para GPT-2 con soporte para Flash Attention, YaRN y Sliding Window."""

    def __init__(self, config: EmpoorioLMConfig, rope=None):
        super().__init__()
        self.num_heads = config.num_heads
        self.hidden_size = config.hidden_size
        self.head_dim = config.hidden_size // config.num_heads
        self.config = config

        # Initialize Flash Attention if available
        flash_config = FlashAttentionConfig(
            enable_flash_attention=getattr(config, 'use_flash_attention', True),
            dropout=config.dropout,
            causal=True  # GPT-2 uses causal attention
        )
        self.flash_attention = create_flash_attention(
            self.num_heads, self.head_dim, flash_config
        ) if flash_config.is_available() else None

        # Choose attention mechanism based on configuration
        if config.use_sliding_window:
            # Use Sliding Window Attention (without built-in output projection)
            head_dim = config.hidden_size // config.num_heads
            self.attention = SlidingWindowAttention(
                window_size=config.sliding_window_size,
                num_heads=config.num_heads,
                head_dim=head_dim,
                dropout=config.dropout
            )
            # Remove the output projection from SlidingWindowAttention since we handle it here
            self.attention.out_proj = nn.Identity()
            # We need QKV projections for sliding window attention
            self.q_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=True)
            self.k_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=True)
            self.v_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=True)
            self.out_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=True)
            self.dropout = nn.Dropout(config.dropout)
            self.rope = None  # Sliding Window handles positioning differently
            self.use_sliding_window = True
            self.use_flash = False  # Sliding Window has its own implementation
        else:
            # Use standard/Flash attention with optional YaRN
            self.q_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=True)
            self.k_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=True)
            self.v_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=True)
            self.out_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=True)
            self.dropout = nn.Dropout(config.dropout)

            # Setup RoPE or YaRN
            if config.use_yarn:
                yarn_config = YaRNConfig(
                    scale_factor=config.yarn_scale,
                    original_max_position_embeddings=config.yarn_original_max_position_embeddings,
                    max_position_embeddings=config.max_context_size
                )
                self.rope = YaRNRotaryEmbedding(yarn_config, dim=self.head_dim)
            else:
                self.rope = rope

            self.use_sliding_window = False
            self.use_flash = self.flash_attention is not None

    def forward(self, hidden_states: torch.Tensor, attention_mask: Optional[torch.Tensor] = None, position_ids: Optional[torch.Tensor] = None) -> torch.Tensor:
        if self.use_sliding_window:
            # Use Sliding Window Attention
            batch_size, seq_length, _ = hidden_states.size()

            # Apply QKV projections
            q = self.q_proj(hidden_states).view(batch_size, seq_length, self.num_heads, self.head_dim)
            k = self.k_proj(hidden_states).view(batch_size, seq_length, self.num_heads, self.head_dim)
            v = self.v_proj(hidden_states).view(batch_size, seq_length, self.num_heads, self.head_dim)

            # Call sliding window attention
            output, _ = self.attention(q, k, v, attention_mask)

            # Apply output projection and dropout
            output = self.out_proj(output)
            output = self.dropout(output)

            return output
        else:
            # Use Flash Attention or standard attention with optional YaRN
            batch_size, seq_length, _ = hidden_states.size()

            # Proyecciones lineales
            q = self.q_proj(hidden_states).view(batch_size, seq_length, self.num_heads, self.head_dim)
            k = self.k_proj(hidden_states).view(batch_size, seq_length, self.num_heads, self.head_dim)
            v = self.v_proj(hidden_states).view(batch_size, seq_length, self.num_heads, self.head_dim)

            # Apply RoPE or YaRN if available (before Flash Attention)
            if self.rope is not None:
                # For Flash Attention, we need to transpose to [batch, seq, heads, dim] format
                q_fa = q.transpose(1, 2)  # [batch, seq, heads, dim]
                k_fa = k.transpose(1, 2)  # [batch, seq, heads, dim]

                if hasattr(self.rope, 'apply_rotary_emb'):  # YaRN
                    cos, sin = self.rope(seq_length, self.head_dim)
                    q_fa = self.rope.apply_rotary_emb(q_fa, cos, sin)
                    k_fa = self.rope.apply_rotary_emb(k_fa, cos, sin)
                else:  # Standard RoPE
                    q_fa, k_fa = self.rope(q_fa, position_ids), self.rope(k_fa, position_ids)

                # Convert back to Flash Attention format [batch, heads, seq, dim]
                q = q_fa.transpose(1, 2)
                k = k_fa.transpose(1, 2)

            # Use Optimized Attention Engine (includes Flash Attention 2, Memory Efficient, and Math)
            # Transpose to [batch, heads, seq, dim] format expected by attention engines
            q_attn = q.transpose(1, 2)  # [batch, heads, seq, dim]
            k_attn = k.transpose(1, 2)  # [batch, heads, seq, dim]
            v_attn = v.transpose(1, 2)  # [batch, heads, seq, dim]

            # Use Optimized Attention Engine with automatic kernel selection
            attn_output = OptimizedAttentionEngine.forward(
                query=q_attn,
                key=k_attn,
                value=v_attn,
                attn_mask=attention_mask,
                dropout_p=self.dropout.p if self.training else 0.0,
                is_causal=True  # GPT-2 uses causal attention
            )

            # Reshape and project
            attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, seq_length, self.hidden_size)
            attn_output = self.out_proj(attn_output)

            return attn_output


class GPT2MLP(nn.Module):
    """MLP estándar para GPT-2 (usado en capas no-MoE)."""

    def __init__(self, config: EmpoorioLMConfig):
        super().__init__()
        self.fc1 = nn.Linear(config.hidden_size, 4 * config.hidden_size, bias=True)
        self.fc2 = nn.Linear(4 * config.hidden_size, config.hidden_size, bias=True)
        self.act = F.gelu if config.activation_function == "gelu" else F.relu
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        hidden_states = self.fc1(hidden_states)
        hidden_states = self.act(hidden_states)
        hidden_states = self.dropout(hidden_states)
        hidden_states = self.fc2(hidden_states)
        hidden_states = self.dropout(hidden_states)
        return hidden_states


class GPT2Block(nn.Module):
    """Bloque Transformer para GPT-2 con soporte opcional para MoE."""

    def __init__(self, config: EmpoorioLMConfig, layer_idx: int = 0, rope=None):
        super().__init__()
        self.layer_idx = layer_idx
        self.use_moe = config.use_moe and layer_idx in config.moe_layers

        # Layer norms
        self.ln1 = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
        self.ln2 = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)

        # Attention
        self.attn = GPT2Attention(config, rope)

        # Feed-forward: MoE or standard MLP
        if self.use_moe:
            self.ffn = MoELayer(config.hidden_size, config.hidden_size, MoEConfig(
                num_experts=config.num_experts,
                expert_dim=config.hidden_size * 4,  # 4x for FFN expansion
                top_k=config.top_k,
                load_balance_coeff=config.load_balance_weight
            ), layer_idx)
        else:
            self.ffn = GPT2MLP(config)

    def forward(self, hidden_states: torch.Tensor, attention_mask: Optional[torch.Tensor] = None, position_ids: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, Optional[Dict[str, Any]]]:
        # Pre-norm architecture
        residual = hidden_states
        hidden_states = self.ln1(hidden_states)
        attn_output = self.attn(hidden_states, attention_mask, position_ids)
        hidden_states = residual + attn_output  # Residual connection

        # Feed-forward with optional MoE
        residual = hidden_states
        if self.use_moe:
            hidden_states = self.ln2(hidden_states)
            moe_output, aux_info = self.ffn(hidden_states)
            # Ensure moe_output is always a tensor
            if isinstance(moe_output, dict):
                moe_output = moe_output.get('output', moe_output)
            hidden_states = residual + moe_output
        else:
            hidden_states = self.ln2(hidden_states)
            ffn_output = self.ffn(hidden_states)
            hidden_states = residual + ffn_output  # Residual connection
            aux_info = None

        return hidden_states, aux_info


class EmpoorioLM(nn.Module):
    """
    EmpoorioLM - GPT-2 Style Transformer con soporte completo para MoE.
    Arquitectura híbrida que combina capas densas con capas MoE.
    """

    def __init__(self, config: EmpoorioLMConfig):
        super().__init__()
        self.config = config

        # Token embeddings
        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size)

        # Position embeddings (only if not using RoPE)
        if not config.use_rope:
            self.embed_positions = nn.Embedding(config.max_position_embeddings, config.hidden_size)
        else:
            self.embed_positions = None

        # Dropout
        self.dropout = nn.Dropout(config.dropout)

        # RoPE for positional encoding (only if explicitly enabled and not using YaRN or Sliding Window)
        if config.use_rope and not config.use_yarn and not config.use_sliding_window:
            # Determine context size for RoPE config
            if config.max_context_size <= 1024:
                context_key = "1k"
            elif config.max_context_size <= 4096:
                context_key = "4k"
            elif config.max_context_size <= 8192:
                context_key = "8k"
            elif config.max_context_size <= 16384:
                context_key = "16k"
            else:
                context_key = "32k"
            self.rope = create_rope_for_context(context_key, config.hidden_size // config.num_heads)
        else:
            self.rope = None

        # Transformer blocks (some may be MoE)
        self.blocks = nn.ModuleList([
            GPT2Block(config, layer_idx=i, rope=self.rope) for i in range(config.num_layers)
        ])

        # MIRAS blocks (Memory Integration for Real-time Adaptive Systems)
        self.miras_blocks = nn.ModuleList()
        self.miras_layer_indices = []  # Lista de índices de capas donde aplicar MIRAS
        self.surprise_encoder = None

        # Liquid Memory Manager (Liquid Titans - Fusión MoE + Memory)
        self.liquid_memory_manager = None

        if config.use_miras:
            # Import dynamically to avoid circular imports
            try:
                from ...inference.memory.miras_block import create_miras_block
                from ...inference.memory.surprise_encoder import create_surprise_encoder
                from ...inference.memory.liquid_memory import (
                    create_liquid_memory_manager, create_liquid_memory_miras_block
                )

                # Crear encoder de sorpresa compartido
                self.surprise_encoder = create_surprise_encoder(
                    vocab_size=config.vocab_size,
                    hidden_size=config.hidden_size,
                    device=str(config.device)
                )

                # Inicializar Liquid Memory si está habilitado
                if config.use_liquid_memory and config.use_moe:
                    self.liquid_memory_manager = create_liquid_memory_manager(
                        num_experts=config.num_experts,
                        hidden_size=config.hidden_size,
                        total_memory_slots=config.liquid_memory_total_slots,
                        base_memory_per_expert=config.liquid_memory_base_per_expert,
                        adaptation_rate=config.liquid_memory_adaptation_rate,
                        device=str(config.device)
                    )
                    logger.info(f"🧠 Liquid Memory inicializado: {config.num_experts} expertos, {config.liquid_memory_total_slots} slots totales")

                # Crear bloques MIRAS para las capas especificadas
                for layer_idx in config.miras_layers:
                    if config.use_liquid_memory and config.use_moe and layer_idx in config.moe_layers:
                        # Usar Liquid Memory MIRAS Blocks para capas MoE
                        miras_block = create_liquid_memory_miras_block(
                            liquid_memory_manager=self.liquid_memory_manager,
                            expert_id=0,  # Será asignado dinámicamente durante el forward
                            hidden_size=config.hidden_size,
                            num_heads=config.num_heads,
                            dropout=config.miras_dropout
                        )
                    else:
                        # Usar MIRAS blocks estándar
                        miras_block = create_miras_block(
                            hidden_size=config.hidden_size,
                            num_heads=config.num_heads,
                            memory_size=config.miras_memory_size,
                            dropout=config.miras_dropout,
                            surprise_encoder=self.surprise_encoder
                        )
                    self.miras_blocks.append(miras_block)
                    self.miras_layer_indices.append(layer_idx)

                logger.info(f"🧠 MIRAS activado en capas: {config.miras_layers}")
                if config.use_liquid_memory:
                    logger.info(f"🧠 Liquid Memory integrado con MIRAS")
            except ImportError as e:
                logger.warning(f"MIRAS/Liquid Memory components not available: {e}")
                config.use_miras = False
                config.use_liquid_memory = False

        # Final layer norm
        self.ln_f = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)

        # Language modeling head (tied weights)
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)
        self.lm_head.weight = self.embed_tokens.weight  # Weight tying

        # Initialize weights
        self.apply(self._init_weights)

        # Apply LoRA if configured
        self.lora_wrapper = None
        if self.config.use_lora:
            self.lora_wrapper = LoRAModelWrapper(self, self.config)
            logger.info(f"🎯 LoRA aplicado a {len(self.lora_wrapper.applied_modules)} módulos")

        # Move to device
        self.to(self.config.device)

        logger.info(f"🚀 EmpoorioLM inicializado: {config.get_model_info()}")

    def _init_weights(self, module):
        """Initialize weights following GPT-2 scheme."""
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)
        elif isinstance(module, nn.LayerNorm):
            torch.nn.init.zeros_(module.bias)
            torch.nn.init.ones_(module.weight)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Forward pass del modelo.

        Args:
            input_ids: Token IDs [batch_size, seq_len]
            attention_mask: Attention mask [batch_size, seq_len]
            labels: Labels para loss calculation [batch_size, seq_len]

        Returns:
            Dict con logits, loss (si labels provided), y info auxiliar MoE
        """
        batch_size, seq_len = input_ids.size()

        # Create position IDs
        position_ids = torch.arange(seq_len, dtype=torch.long, device=input_ids.device)
        position_ids = position_ids.unsqueeze(0).expand(batch_size, -1)

        # Embeddings
        token_embeds = self.embed_tokens(input_ids)
        if self.embed_positions is not None:
            position_embeds = self.embed_positions(position_ids)
            hidden_states = token_embeds + position_embeds
        else:
            hidden_states = token_embeds
        hidden_states = self.dropout(hidden_states)

        # Create causal attention mask
        if attention_mask is None:
            attention_mask = torch.ones((batch_size, seq_len), device=input_ids.device)

        # Convert to attention mask format (add head and seq dimensions)
        attention_mask = attention_mask.unsqueeze(1).unsqueeze(2)  # [batch, 1, 1, seq_len]
        attention_mask = (1.0 - attention_mask) * -10000.0  # Convert to mask

        # Transformer blocks with optional MIRAS integration
        moe_aux_info = {}
        miras_aux_info = {}
        liquid_memory_aux_info = {}

        # Crear contexto embedding para Liquid Memory (promedio de tokens de entrada)
        context_embedding = None
        if self.config.use_liquid_memory and self.liquid_memory_manager is not None:
            context_embedding = hidden_states.mean(dim=1)  # [batch_size, hidden_size]

        for i, block in enumerate(self.blocks):
            hidden_states, aux_info = block(hidden_states, attention_mask, position_ids)
            if aux_info is not None:
                moe_aux_info[f"layer_{i}"] = aux_info

            # Aplicar MIRAS si está configurado para esta capa
            miras_layer_idx = None
            if self.config.use_miras and i in self.miras_layer_indices:
                miras_layer_idx = self.miras_layer_indices.index(i)
                miras_block = self.miras_blocks[miras_layer_idx]

                # Manejar Liquid Memory para capas MoE
                if (self.config.use_liquid_memory and
                    self.liquid_memory_manager is not None and
                    hasattr(miras_block, 'liquid_memory_manager')):
                    # Es un LiquidMemoryMIRASBlock - aplicar con contexto
                    hidden_states, miras_aux = miras_block(
                        hidden_states=hidden_states,
                        attention_mask=attention_mask,
                        context_embedding=context_embedding
                    )
                else:
                    # Calcular logits intermedios para surprise encoder (opcional)
                    intermediate_logits = None
                    if self.surprise_encoder is not None:
                        intermediate_hidden = self.ln_f(hidden_states)  # Layer norm antes de LM head
                        intermediate_logits = self.lm_head(intermediate_hidden)

                    # Aplicar bloque MIRAS estándar
                    hidden_states, miras_aux = miras_block(
                        hidden_states=hidden_states,
                        attention_mask=attention_mask,
                        input_ids=None,  # No tenemos input_ids en este contexto
                        logits=intermediate_logits
                    )

                miras_aux_info[f"layer_{i}"] = miras_aux

                # Recopilar información de Liquid Memory
                if 'liquid_memory' in miras_aux:
                    liquid_memory_aux_info[f"layer_{i}"] = miras_aux['liquid_memory']

        # Final layer norm
        hidden_states = self.ln_f(hidden_states)

        # Language modeling head
        logits = self.lm_head(hidden_states)

        result = {"logits": logits}

        # Calculate loss if labels provided
        if labels is not None:
            # Shift logits and labels for next-token prediction
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()

            loss = F.cross_entropy(
                shift_logits.view(-1, shift_logits.size(-1)),
                shift_labels.view(-1),
                ignore_index=-100
            )
            result["loss"] = loss

            # Calculate perplexity
            perplexity = torch.exp(loss)
            result["perplexity"] = perplexity

        # Add MoE auxiliary loss if present
        if moe_aux_info:
            try:
                moe_loss = compute_moe_loss(moe_aux_info)
                if "loss" in result:
                    result["loss"] = result["loss"] + moe_loss
                else:
                    result["loss"] = moe_loss

                result["moe_aux_loss"] = moe_loss
            except (KeyError, TypeError):
                # Handle cases where aux_loss is not available
                moe_loss = torch.tensor(0.0, device=self.config.device)
                result["moe_aux_loss"] = moe_loss

            result["moe_aux_info"] = moe_aux_info

            # Add MIRAS auxiliary information
            if miras_aux_info:
                result["miras_aux_info"] = miras_aux_info

            # Add Liquid Memory auxiliary information
            if liquid_memory_aux_info:
                result["liquid_memory_aux_info"] = liquid_memory_aux_info

        return result

    def _get_architecture_description(self, moe_count: int, miras_count: int, liquid_memory_enabled: bool) -> str:
        """Generate architecture description string."""
        components = ["GPT-2 style transformer"]

        if moe_count > 0:
            components.append("MoE")
        if miras_count > 0:
            components.append("MIRAS")
        if liquid_memory_enabled:
            components.append("Liquid Memory")

        return " + ".join(components)

    def get_model_info(self) -> Dict[str, Any]:
        """Información completa del modelo."""
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)

        # Count MoE layers
        moe_layers_count = sum(1 for block in self.blocks if hasattr(block.ffn, 'router'))

        # Count MIRAS layers
        miras_layers_count = len(self.miras_blocks) if self.config.use_miras else 0

        # Get LoRA stats
        lora_stats = self.get_lora_memory_stats()

        # Get MIRAS stats
        miras_stats = {}
        if self.config.use_miras and self.miras_blocks:
            miras_stats = self.miras_blocks[0].get_miras_stats()  # Get stats from first MIRAS block

        # Get Liquid Memory stats
        liquid_memory_stats = {}
        if self.config.use_liquid_memory and self.liquid_memory_manager is not None:
            liquid_memory_stats = self.liquid_memory_manager.get_memory_stats()

        info = self.config.get_model_info()
        info.update({
            "total_parameters": total_params,
            "trainable_parameters": trainable_params if not self.config.use_lora else len(self.get_trainable_parameters()),
            "moe_layers_active": moe_layers_count,
            "miras_layers_active": miras_layers_count,
            "architecture": self._get_architecture_description(moe_layers_count, miras_layers_count, self.config.use_liquid_memory),
            "lora_enabled": self.config.use_lora,
            "lora_memory_stats": lora_stats,
            "miras_enabled": self.config.use_miras,
            "miras_stats": miras_stats,
            "liquid_memory_enabled": self.config.use_liquid_memory,
            "liquid_memory_stats": liquid_memory_stats,
        })

        return info

    def get_moe_stats(self) -> Optional[Dict[str, Any]]:
        """Get MoE statistics if MoE is enabled."""
        moe_aux_info = {}
        for i, block in enumerate(self.blocks):
            if hasattr(block.ffn, 'get_expert_usage_stats'):
                moe_aux_info[f"layer_{i}"] = block.ffn.get_expert_usage_stats()

        if moe_aux_info:
            return get_moe_statistics(moe_aux_info)
        return None

    def get_miras_stats(self) -> Optional[Dict[str, Any]]:
        """Get MIRAS statistics if MIRAS is enabled."""
        if not self.config.use_miras or not self.miras_blocks:
            return None

        miras_stats = {}
        for i, miras_block in enumerate(self.miras_blocks):
            layer_idx = self.miras_layer_indices[i]
            miras_stats[f"layer_{layer_idx}"] = miras_block.get_miras_stats()

        # Agregar estadísticas globales
        total_memory_utilization = sum(
            stats.get('memory_utilization', 0) for stats in miras_stats.values()
            if isinstance(stats, dict) and 'memory_utilization' in stats
        ) / len(miras_stats) if miras_stats else 0

        return {
            "miras_layers": len(self.miras_blocks),
            "layers": list(miras_stats.keys()),
            "avg_memory_utilization": total_memory_utilization,
            "layer_stats": miras_stats
        }

    def reset_miras_memory(self):
        """Reset MIRAS memory for all MIRAS blocks."""
        if self.config.use_miras:
            for miras_block in self.miras_blocks:
                miras_block.reset_memory()
            logger.info("🔄 Memoria MIRAS reiniciada en todas las capas")
        else:
            logger.warning("MIRAS no está habilitado en este modelo")

    def optimize_liquid_memory(self):
        """Optimize Liquid Memory allocation."""
        if self.config.use_liquid_memory and self.liquid_memory_manager is not None:
            self.liquid_memory_manager.optimize_memory_allocation()
            logger.info("⚖️ Memoria líquida optimizada")
        else:
            logger.warning("Liquid Memory no está habilitado en este modelo")

    def get_liquid_memory_stats(self) -> Optional[Dict[str, Any]]:
        """Get Liquid Memory statistics."""
        if self.config.use_liquid_memory and self.liquid_memory_manager is not None:
            return self.liquid_memory_manager.get_memory_stats()
        return None

    def merge_lora_weights(self):
        """Merge LoRA weights into base layers."""
        if self.lora_wrapper:
            self.lora_wrapper.merge_weights()
        else:
            logger.warning("LoRA no está habilitado en este modelo")

    def unmerge_lora_weights(self):
        """Unmerge LoRA weights from base layers."""
        if self.lora_wrapper:
            self.lora_wrapper.unmerge_weights()
        else:
            logger.warning("LoRA no está habilitado en este modelo")

    def save_lora_adapters(self, path: Union[str, Path]):
        """Save only LoRA adapters."""
        if self.lora_wrapper:
            self.lora_wrapper.save_lora_adapters(path)
        else:
            logger.warning("LoRA no está habilitado en este modelo")

    def load_lora_adapters(self, path: Union[str, Path]):
        """Load LoRA adapters."""
        if self.lora_wrapper:
            self.lora_wrapper.load_lora_adapters(path)
        else:
            logger.warning("LoRA no está habilitado en este modelo")

    def get_lora_memory_stats(self) -> Optional[Dict[str, Any]]:
        """Get LoRA memory statistics."""
        if self.lora_wrapper:
            return self.lora_wrapper.get_memory_stats()
        return None

    def get_trainable_parameters(self) -> List[nn.Parameter]:
        """Get trainable parameters (LoRA if enabled, otherwise all)."""
        if self.lora_wrapper:
            return self.lora_wrapper.get_trainable_parameters()
        else:
            return list(self.parameters())

    def generate(
        self,
        input_ids: torch.Tensor,
        max_length: int = 50,
        temperature: float = 1.0,
        top_k: Optional[int] = None,
        top_p: Optional[float] = None,
        do_sample: bool = True,
        pad_token_id: int = 0,
        eos_token_id: Optional[int] = None
    ) -> torch.Tensor:
        """Generate text from input_ids."""
        self.eval()
        batch_size, seq_len = input_ids.size()

        generated = input_ids.clone()

        with torch.no_grad():
            for _ in range(max_length - seq_len):
                # Get logits for the last token
                outputs = self(input_ids=generated)
                next_token_logits = outputs["logits"][:, -1, :]

                # Apply temperature
                if temperature != 1.0:
                    next_token_logits = next_token_logits / temperature

                # Apply top-k sampling
                if top_k is not None:
                    top_k_logits, top_k_indices = torch.topk(next_token_logits, top_k, dim=-1)
                    next_token_logits = torch.full_like(next_token_logits, float('-inf'))
                    next_token_logits.scatter_(-1, top_k_indices, top_k_logits)

                # Apply top-p sampling
                if top_p is not None:
                    sorted_logits, sorted_indices = torch.sort(next_token_logits, descending=True)
                    sorted_probs = F.softmax(sorted_logits, dim=-1)
                    cumulative_probs = torch.cumsum(sorted_probs, dim=-1)

                    # Remove tokens with cumulative probability above the threshold
                    sorted_probs[cumulative_probs > top_p] = 0

                    # Renormalize
                    sorted_probs = sorted_probs / sorted_probs.sum(dim=-1, keepdim=True)

                    # Sample from the filtered distribution
                    next_token = torch.multinomial(sorted_probs, num_samples=1)
                    next_token = sorted_indices.gather(-1, next_token).squeeze(-1)
                elif do_sample:
                    probs = F.softmax(next_token_logits, dim=-1)
                    next_token = torch.multinomial(probs, num_samples=1).squeeze(-1)
                else:
                    next_token = torch.argmax(next_token_logits, dim=-1)

                # Append to sequence
                generated = torch.cat([generated, next_token.unsqueeze(-1)], dim=-1)

                # Stop if EOS token generated
                if eos_token_id is not None and next_token.item() == eos_token_id:
                    break

        return generated

    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Generate text from a text prompt (async wrapper for API compatibility).

        Args:
            prompt: Input text prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional generation parameters

        Returns:
            Generated text response
        """
        tokenizer = kwargs.pop("tokenizer", None)
        tokenizer_path = kwargs.pop("tokenizer_path", None) or os.getenv("EMPOORIO_TOKENIZER_PATH")
        if tokenizer is None and tokenizer_path:
            tokenizer = EmpoorioBPETokenizer.load(tokenizer_path)

        if tokenizer is None:
            raise ValueError("Tokenizer requerido para generar texto")

        input_ids = tokenizer.encode(prompt, add_special_tokens=True)
        device = next(self.parameters()).device
        input_tensor = torch.tensor([input_ids], dtype=torch.long, device=device)

        max_context = getattr(self.config, "max_context_size", len(input_ids) + max_tokens)
        target_length = min(len(input_ids) + max_tokens, max_context)

        eos_token_id = tokenizer.special_tokens.get(tokenizer.config.eos_token)
        pad_token_id = tokenizer.special_tokens.get(tokenizer.config.pad_token)

        generated = self.generate(
            input_ids=input_tensor,
            max_length=target_length,
            temperature=temperature,
            top_k=kwargs.get("top_k"),
            top_p=kwargs.get("top_p"),
            do_sample=kwargs.get("do_sample", True),
            pad_token_id=pad_token_id,
            eos_token_id=eos_token_id
        )

        output_ids = generated[0].tolist()
        return tokenizer.decode(output_ids, skip_special_tokens=True)

    @classmethod
    def from_pretrained(cls, model_path: Union[str, Path], config: Optional[EmpoorioLMConfig] = None) -> 'EmpoorioLM':
        """Load model from pretrained checkpoint."""
        model_path = Path(model_path)

        # Load config if not provided
        if config is None:
            config_path = model_path / "config.json"
            if config_path.exists():
                config = EmpoorioLMConfig.load_config(str(config_path))
            else:
                raise FileNotFoundError(f"Config file not found: {config_path}")

        # Create model
        model = cls(config)

        # Load state dict
        model_file = model_path / "pytorch_model.bin"
        if model_file.exists():
            state_dict = torch.load(model_file, map_location='cpu')
            strict_load = os.getenv("AILOOS_STRICT_MODEL_LOAD", "false").lower() in ("1", "true", "yes")
            try:
                model.load_state_dict(state_dict)
            except RuntimeError as exc:
                if strict_load:
                    raise
                missing, unexpected = model.load_state_dict(state_dict, strict=False)
                logger.warning(
                    "Non-strict model load applied; set AILOOS_STRICT_MODEL_LOAD=true to fail on mismatches"
                )
                if missing:
                    logger.warning(f"Missing keys: {missing}")
                if unexpected:
                    logger.warning(f"Unexpected keys: {unexpected}")
            logger.info(f"✅ Model loaded from {model_file}")
        else:
            allow_random = os.getenv("AILOOS_ALLOW_RANDOM_WEIGHTS", "false").lower() == "true"
            if not allow_random:
                raise FileNotFoundError(f"Model file not found: {model_file}")
            logger.warning(f"⚠️  Model file not found: {model_file}, using random weights")

        return model

    def save_pretrained(self, save_path: Union[str, Path]):
        """Save model and config."""
        save_path = Path(save_path)
        save_path.mkdir(parents=True, exist_ok=True)

        # Save config
        config_path = save_path / "config.json"
        self.config.save_config(str(config_path))

        # Save model
        model_path = save_path / "pytorch_model.bin"
        torch.save(self.state_dict(), model_path)

        logger.info(f"✅ Model saved to {save_path}")


# Utility functions
def create_empoorio_lm_model(config: EmpoorioLMConfig) -> EmpoorioLM:
    """Factory function to create EmpoorioLM model."""
    return EmpoorioLM(config)


def get_model_config_for_size(size: str, use_moe: bool = True) -> EmpoorioLMConfig:
    """Get model configuration for a specific size."""
    from .config import get_config_for_model_size
    return get_config_for_model_size(size, use_moe)


# For backward compatibility
__all__ = [
    'EmpoorioLM',
    'EmpoorioLMConfig',
    'create_empoorio_lm_model',
    'get_model_config_for_size',
]
