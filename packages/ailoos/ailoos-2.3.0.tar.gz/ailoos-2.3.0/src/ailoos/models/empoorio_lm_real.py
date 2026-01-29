#!/usr/bin/env python3
"""
EmpoorioLM Real Implementation - GPT-2 Style Transformer
Implementación funcional completa para la Prueba de Fuego Lingüística
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import json
import math
import os
from pathlib import Path
from typing import Optional, Dict, Any, Union, List
from dataclasses import dataclass, asdict

try:
    from transformers import AutoTokenizer, PreTrainedTokenizer, PreTrainedTokenizerFast
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    _TRANSFORMERS_AVAILABLE = False
    print("⚠️  Transformers library not found, using basic features")

# Imports para Fase 2: Contexto Largo
try:
    from models.empoorio_lm.rope import NTKAwareRoPE, create_rope_for_context
    from models.empoorio_lm.flash_attention import FlashAttentionLayer
    from models.empoorio_lm.ring_attention import FederatedRingCoordinator
    _PHASE2_COMPONENTS_AVAILABLE = True
except ImportError:
    _PHASE2_COMPONENTS_AVAILABLE = False
    print("⚠️  Componentes de Fase 2 no disponibles, usando implementación básica")

# Imports para MoE (si está disponible)
try:
    from models.empoorio_lm.moe import MoELayer
    _MOE_AVAILABLE = True
except ImportError:
    _MOE_AVAILABLE = False
    print("⚠️  Componentes MoE no disponibles")

@dataclass
class EmpoorioLMConfig:
    """Configuración completa para EmpoorioLM con soporte para contexto largo."""
    vocab_size: int = 30000
    hidden_size: int = 768
    num_layers: int = 12
    num_heads: int = 12
    max_position_embeddings: int = 1024  # Ahora extensible dinámicamente
    dropout: float = 0.1
    activation_function: str = "gelu"
    layer_norm_eps: float = 1e-5
    initializer_range: float = 0.02

    # Nuevos parámetros para Fase 2: Contexto Largo
    # RoPE configuration
    use_rope: bool = True
    rope_scaling_factor: float = 1.0
    rope_ntk_factor: float = 1.0
    rope_base: float = 10000.0

    # Flash Attention configuration
    use_flash_attention: bool = True
    flash_attention_chunk_size: int = 1024

    # Ring Attention para federated learning
    use_ring_attention: bool = False
    ring_world_size: int = 1
    ring_rank: int = 0

    # Configuración de contexto variable
    context_scaling_mode: str = "auto"  # "auto", "fixed", "dynamic"
    max_context_size: int = 8192  # Máximo contexto soportado
    min_context_size: int = 512   # Mínimo contexto para optimizaciones

    # Optimizaciones de memoria
    memory_efficient_attention: bool = True
    gradient_checkpointing: bool = False

    # Edge inference optimizations
    enable_edge_optimizations: bool = False
    quantization_bits: int = 16  # 16, 8, 4 bits
    use_kv_cache: bool = True

    # MoE integration (para compatibilidad)
    use_moe: bool = False
    moe_layers: list = None
    num_experts: int = 8
    top_k: int = 2

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vocab_size": self.vocab_size,
            "hidden_size": self.hidden_size,
            "num_layers": self.num_layers,
            "num_heads": self.num_heads,
            "max_position_embeddings": self.max_position_embeddings,
            "dropout": self.dropout,
            "activation_function": self.activation_function,
            "layer_norm_eps": self.layer_norm_eps,
            "initializer_range": self.initializer_range,
            # Nuevos parámetros Fase 2
            "use_rope": self.use_rope,
            "rope_scaling_factor": self.rope_scaling_factor,
            "rope_ntk_factor": self.rope_ntk_factor,
            "rope_base": self.rope_base,
            "use_flash_attention": self.use_flash_attention,
            "flash_attention_chunk_size": self.flash_attention_chunk_size,
            "use_ring_attention": self.use_ring_attention,
            "ring_world_size": self.ring_world_size,
            "ring_rank": self.ring_rank,
            "context_scaling_mode": self.context_scaling_mode,
            "max_context_size": self.max_context_size,
            "min_context_size": self.min_context_size,
            "memory_efficient_attention": self.memory_efficient_attention,
            "gradient_checkpointing": self.gradient_checkpointing,
            "enable_edge_optimizations": self.enable_edge_optimizations,
            "quantization_bits": self.quantization_bits,
            "use_kv_cache": self.use_kv_cache,
            "use_moe": self.use_moe,
            "moe_layers": self.moe_layers,
            "num_experts": self.num_experts,
            "top_k": self.top_k,
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'EmpoorioLMConfig':
        # Filter keys that are valid for this class
        valid_keys = cls.__annotations__.keys()
        filtered_dict = {k: v for k, v in config_dict.items() if k in valid_keys}
        return cls(**filtered_dict)

class GPT2Attention(nn.Module):
    """Multi-head attention para GPT-2 con soporte para Flash Attention 2."""

    def __init__(self, config: EmpoorioLMConfig):
        super().__init__()
        self.config = config
        self.num_heads = config.num_heads
        self.hidden_size = config.hidden_size
        self.head_dim = config.hidden_size // config.num_heads

        # Usar Flash Attention si está disponible y habilitado
        if _PHASE2_COMPONENTS_AVAILABLE and config.use_flash_attention:
            self.attention = FlashAttentionLayer(config)
            self.use_flash = True
        else:
            # Fallback a atención estándar
            self.q_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=True)
            self.k_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=True)
            self.v_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=True)
            self.out_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=True)
            self.dropout = nn.Dropout(config.dropout)
            self.use_flash = False

        # RoPE será configurado desde el modelo principal
        self.rope = None

    def set_rope(self, rope):
        """Configurar RoPE para esta capa."""
        self.rope = rope
        if self.use_flash:
            self.attention.set_rope(rope)

    def forward(self, hidden_states: torch.Tensor, attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        if self.use_flash:
            # Usar Flash Attention con RoPE integrado
            return self.attention(hidden_states, attention_mask)
        else:
            # Atención estándar con soporte opcional para RoPE
            return self._standard_attention(hidden_states, attention_mask)

    def _standard_attention(self, hidden_states: torch.Tensor, attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """Atención estándar como fallback."""
        batch_size, seq_length, _ = hidden_states.size()

        # Proyecciones lineales
        q = self.q_proj(hidden_states).view(batch_size, seq_length, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(hidden_states).view(batch_size, seq_length, self.num_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(hidden_states).view(batch_size, seq_length, self.num_heads, self.head_dim).transpose(1, 2)

        # Aplicar RoPE si está disponible
        if self.rope is not None:
            position_ids = torch.arange(seq_length, device=hidden_states.device).unsqueeze(0).expand(batch_size, -1)
            q, k = self.rope.apply_rope_to_attention(q, k, position_ids)

        # Attention scores
        scale = 1.0 / math.sqrt(self.head_dim)
        attn_weights = torch.matmul(q, k.transpose(-2, -1)) * scale

        # Apply attention mask
        if attention_mask is not None:
            attn_weights = attn_weights + attention_mask

        # Softmax
        attn_weights = F.softmax(attn_weights, dim=-1)
        attn_weights = self.dropout(attn_weights)

        # Apply attention
        attn_output = torch.matmul(attn_weights, v)

        # Reshape and project
        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, seq_length, self.hidden_size)
        attn_output = self.out_proj(attn_output)

        return attn_output

class GPT2MLP(nn.Module):
    """MLP para GPT-2."""

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

    def __init__(self, config: EmpoorioLMConfig, layer_idx: int = 0):
        super().__init__()
        self.layer_idx = layer_idx
        self.config = config

        self.ln1 = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
        self.attn = GPT2Attention(config)
        self.ln2 = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)

        # Usar MoE si está configurado y esta capa es MoE
        if (_MOE_AVAILABLE and config.use_moe and
            config.moe_layers is not None and layer_idx in config.moe_layers):
            self.mlp = MoELayer(config, layer_idx)
            self.use_moe = True
        else:
            self.mlp = GPT2MLP(config)
            self.use_moe = False

    def forward(self, hidden_states: torch.Tensor, attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        # Pre-norm architecture
        residual = hidden_states
        hidden_states = self.ln1(hidden_states)
        attn_output = self.attn(hidden_states, attention_mask)
        hidden_states = residual + attn_output  # Residual connection

        residual = hidden_states
        hidden_states = self.ln2(hidden_states)
        mlp_output = self.mlp(hidden_states)
        hidden_states = residual + mlp_output  # Residual connection

        return hidden_states

class EmpoorioLM(nn.Module):
    """EmpoorioLM - GPT-2 Style Transformer con soporte para contexto largo (Fase 2)."""

    def __init__(self, config: EmpoorioLMConfig):
        super().__init__()
        self.config = config

        # Token embeddings
        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size)

        # RoPE initialization
        if _PHASE2_COMPONENTS_AVAILABLE and config.use_rope:
            # Determinar tamaño de contexto basado en configuración
            context_size = self._get_context_size_from_config()
            self.rope = create_rope_for_context(context_size, config.hidden_size // config.num_heads)
        else:
            self.rope = None
            if config.use_rope and _PHASE2_COMPONENTS_AVAILABLE is False:
                print("⚠️ RoPE requested but components not available, falling back to absolute embeddings")

        # Position embeddings - absolute if RoPE is not used or not available
        if self.rope is None:
            self.embed_positions = nn.Embedding(config.max_position_embeddings, config.hidden_size)
        else:
            self.embed_positions = None

        # Ring Attention para federated learning
        if _PHASE2_COMPONENTS_AVAILABLE and config.use_ring_attention:
            self.ring_coordinator = FederatedRingCoordinator(config.ring_world_size, config.ring_rank)
            self.ring_coordinator.setup_ring_attention(config)
        else:
            self.ring_coordinator = None

        # Dropout
        self.dropout = nn.Dropout(config.dropout)

        # Transformer blocks
        self.blocks = nn.ModuleList([
            GPT2Block(config, layer_idx=i) for i in range(config.num_layers)
        ])

        # Configurar RoPE en todas las capas de atención
        if self.rope is not None:
            for block in self.blocks:
                block.attn.set_rope(self.rope)

        # Final layer norm
        self.ln_f = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)

        # Language modeling head (tied weights)
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)
        self.lm_head.weight = self.embed_tokens.weight  # Weight tying

        # Gradient checkpointing
        if config.gradient_checkpointing:
            self.gradient_checkpointing = True

        # Initialize weights
        self.apply(self._init_weights)

    def _get_context_size_from_config(self) -> str:
        """Determinar tamaño de contexto basado en configuración."""
        if self.config.max_context_size <= 1024:
            return "1k"
        elif self.config.max_context_size <= 4096:
            return "4k"
        elif self.config.max_context_size <= 8192:
            return "8k"
        elif self.config.max_context_size <= 16384:
            return "16k"
        else:
            return "32k"

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
        position_ids: Optional[torch.Tensor] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Forward pass del modelo con soporte para contexto largo.

        Args:
            input_ids: Token IDs [batch_size, seq_len]
            attention_mask: Attention mask [batch_size, seq_len]
            labels: Labels para loss calculation [batch_size, seq_len]
            position_ids: Position IDs (opcional, para RoPE)

        Returns:
            Dict con logits y loss (si labels provided)
        """
        batch_size, seq_len = input_ids.size()

        # Create position IDs si no se proporcionan
        if position_ids is None:
            position_ids = torch.arange(seq_len, dtype=torch.long, device=input_ids.device)
            position_ids = position_ids.unsqueeze(0).expand(batch_size, -1)

        # Embeddings
        token_embeds = self.embed_tokens(input_ids)

        if self.rope is not None:
            # Usar RoPE: no necesitamos position embeddings absolutos
            hidden_states = token_embeds
        else:
            # Usar position embeddings absolutos (backward compatibility)
            position_embeds = self.embed_positions(position_ids)
            hidden_states = token_embeds + position_embeds

        hidden_states = self.dropout(hidden_states)

        # Create causal attention mask
        if attention_mask is None:
            attention_mask = torch.ones((batch_size, seq_len), device=input_ids.device)

        # Convert to attention mask format
        attention_mask = attention_mask.unsqueeze(1).unsqueeze(2)  # [batch, 1, 1, seq_len]
        attention_mask = (1.0 - attention_mask) * -10000.0  # Convert to mask

        # Ring Attention: procesar con comunicación distribuida si está habilitado
        if self.ring_coordinator is not None and seq_len > self.config.min_context_size:
            # Usar Ring Attention para secuencias largas
            hidden_states = self._forward_with_ring_attention(
                hidden_states, attention_mask, seq_len
            )
        else:
            # Procesamiento estándar
            hidden_states = self._forward_standard(hidden_states, attention_mask)

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

        return result

    def _forward_standard(self, hidden_states: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """Forward pass estándar para transformer blocks."""
        # Transformer blocks
        for block in self.blocks:
            if self.config.gradient_checkpointing and self.training:
                hidden_states = torch.utils.checkpoint.checkpoint(block, hidden_states, attention_mask)
            else:
                hidden_states = block(hidden_states, attention_mask)
        return hidden_states

    async def _forward_with_ring_attention(
        self,
        hidden_states: torch.Tensor,
        attention_mask: torch.Tensor,
        seq_len: int
    ) -> torch.Tensor:
        """Forward pass con Ring Attention para secuencias distribuidas."""
        # Para simplificar, por ahora usamos procesamiento local
        # En implementación completa, esto distribuiría el cómputo
        return self._forward_standard(hidden_states, attention_mask)

    def get_model_info(self) -> Dict[str, Any]:
        """Información del modelo con detalles de Fase 2."""
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)

        info = {
            "model_type": "EmpoorioLM-GPT2-Fase2",
            "vocab_size": self.config.vocab_size,
            "hidden_size": self.config.hidden_size,
            "num_layers": self.config.num_layers,
            "num_heads": self.config.num_heads,
            "max_position_embeddings": self.config.max_position_embeddings,
            "max_context_size": self.config.max_context_size,
            "total_parameters": total_params,
            "trainable_parameters": trainable_params,
            "architecture": "GPT-2 style transformer con contexto largo",
            # Componentes de Fase 2
            "use_rope": self.config.use_rope,
            "use_flash_attention": self.config.use_flash_attention,
            "use_ring_attention": self.config.use_ring_attention,
            "context_scaling_mode": self.config.context_scaling_mode,
            "memory_efficient_attention": self.config.memory_efficient_attention,
            "gradient_checkpointing": self.config.gradient_checkpointing,
            "edge_optimizations": self.config.enable_edge_optimizations,
        }

        # Información adicional si los componentes están disponibles
        if _PHASE2_COMPONENTS_AVAILABLE:
            info.update({
                "rope_configured": self.rope is not None,
                "flash_attention_available": True,
                "ring_attention_configured": self.ring_coordinator is not None,
            })

            if self.ring_coordinator is not None:
                info["ring_attention_stats"] = self.ring_coordinator.get_communication_stats()

        return info

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
                outputs = self(generated)
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

    def save_pretrained(self, save_directory: Union[str, Path]):
        """
        Save model weights and configuration to a directory.
        Compatible with HuggingFace structure.
        """
        save_directory = Path(save_directory)
        save_directory.mkdir(parents=True, exist_ok=True)

        # Save config
        config_dict = self.config.to_dict()
        with open(save_directory / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2)

        # Save weights
        torch.save(self.state_dict(), save_directory / "pytorch_model.bin")
        
        print(f"✅ Model saved to {save_directory}")

    @classmethod
    def from_pretrained(cls, pretrained_model_name_or_path: Union[str, Path], **kwargs) -> 'EmpoorioLM':
        """
        Load model from a directory or hub.
        """
        model_path = Path(pretrained_model_name_or_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Model path not found: {model_path}")

        # Load config
        config_file = model_path / "config.json"
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found in {model_path}")

        with open(config_file, "r", encoding="utf-8") as f:
            config_dict = json.load(f)
        
        # Override config with kwargs
        config_dict.update(kwargs)
        config = EmpoorioLMConfig.from_dict(config_dict)

        # Initialize model
        model = cls(config)

        # Load weights
        # Load weights
        safetensors_file = model_path / "model.safetensors"
        weights_file = model_path / "pytorch_model.bin"
        
        state_dict = None
        if safetensors_file.exists():
            try:
                from safetensors.torch import load_file
                state_dict = load_file(safetensors_file)
                print(f"✅ Loaded weights from {safetensors_file}")
            except ImportError:
                print("⚠️ safetensors library not found, cannot load .safetensors file.")
            except Exception as e:
                print(f"⚠️ Error loading safetensors: {e}")

        if state_dict is None and weights_file.exists():
            state_dict = torch.load(weights_file, map_location="cpu")
            print(f"✅ Loaded weights from {weights_file}")
            
        if state_dict is not None:
            model.load_state_dict(state_dict, strict=False)
        else:
            print("⚠️ No suitable weights file found (checked model.safetensors and pytorch_model.bin)")


        return model

class EmpoorioLMTokenizer:
    """
    Tokenizer wrapper for EmpoorioLM.
    Wraps AutoTokenizer when available, falls back to simple char-level for testing.
    """

    def __init__(self, vocab_size: int = 30000, base_tokenizer_name: str = "gpt2"):
        self.vocab_size = vocab_size
        self._tokenizer = None
        
        if _TRANSFORMERS_AVAILABLE:
            try:
                # Try to load a real tokenizer
                self._tokenizer = AutoTokenizer.from_pretrained(base_tokenizer_name)
                # Ensure special tokens
                if self._tokenizer.pad_token is None:
                    self._tokenizer.pad_token = self._tokenizer.eos_token
            except Exception as e:
                print(f"⚠️  Could not load base tokenizer '{base_tokenizer_name}': {e}")
        
        # Fallback constants
        self.pad_token_id = self._tokenizer.pad_token_id if self._tokenizer else 0
        self.eos_token_id = self._tokenizer.eos_token_id if self._tokenizer else 2
        self.bos_token_id = self._tokenizer.bos_token_id if self._tokenizer else 1
        self.unk_token_id = self._tokenizer.unk_token_id if self._tokenizer else 3

    def encode(self, text: str, max_length: Optional[int] = None) -> List[int]:
        """Encode text to token IDs."""
        if self._tokenizer:
            # Use real tokenizer
            if max_length:
                 return self._tokenizer.encode(text, truncation=True, max_length=max_length)
            return self._tokenizer.encode(text)
        
        # Fallback: Simple character-level encoding
        tokens = [self.bos_token_id]
        for char in text:
            token_id = ord(char) % (self.vocab_size - 4) + 4
            tokens.append(token_id)

        if max_length and len(tokens) > max_length:
            tokens = tokens[:max_length-1] + [self.eos_token_id]
        else:
            tokens.append(self.eos_token_id)
        return tokens

    def decode(self, token_ids: List[int]) -> str:
        """Decode token IDs to text."""
        if self._tokenizer:
             return self._tokenizer.decode(token_ids, skip_special_tokens=True)
             
        # Fallback decode
        text = ""
        for token_id in token_ids:
            if token_id in [self.bos_token_id, self.eos_token_id, self.pad_token_id]:
                continue
            elif token_id >= 4:
                char_code = (token_id - 4) % 256
                text += chr(char_code)
            else:
                text += f"<{token_id}>"
        return text

    def __call__(self, text: str, return_tensors: str = "pt", max_length: Optional[int] = None, padding: bool = True):
        """HuggingFace-style interface."""
        if self._tokenizer:
            return self._tokenizer(text, return_tensors=return_tensors, max_length=max_length, 
                                 padding="max_length" if padding and max_length else False,
                                 truncation=True if max_length else False)
                                 
        tokens = self.encode(text, max_length)
        if return_tensors == "pt":
            return {"input_ids": torch.tensor([tokens])}
        return {"input_ids": [tokens]}

    def save_pretrained(self, save_directory: Union[str, Path]):
        """Save tokenizer to directory."""
        if self._tokenizer:
            self._tokenizer.save_pretrained(save_directory)
        else:
            # Save dummy config
            config = {"vocab_size": self.vocab_size}
            with open(Path(save_directory) / "tokenizer_config.json", "w") as f:
                json.dump(config, f)

    @classmethod
    def from_pretrained(cls, pretrained_model_name_or_path: Union[str, Path]) -> 'EmpoorioLMTokenizer':
        """Load tokenizer from directory."""
        instance = cls()
        if _TRANSFORMERS_AVAILABLE:
            try:
                instance._tokenizer = AutoTokenizer.from_pretrained(str(pretrained_model_name_or_path))
                return instance
            except:
                pass
        
        # Fallback load logic if simple config
        return instance
    
    @classmethod
    def load(cls, path: Union[str, Path]) -> 'EmpoorioLMTokenizer':
        """Backwards compatibility wrapper for from_pretrained."""
        return cls.from_pretrained(path)

def get_config_for_model_size(size: str) -> EmpoorioLMConfig:
    """Get configuration for different model sizes con soporte para contexto largo."""
    base_config = {
        "use_rope": True,
        "use_flash_attention": True,
        "context_scaling_mode": "auto",
        "max_context_size": 8192,
        "memory_efficient_attention": True,
        "use_kv_cache": True,
    }

    configs = {
        "small": EmpoorioLMConfig(
            hidden_size=256,
            num_layers=6,
            num_heads=8,
            vocab_size=30000,
            max_position_embeddings=4096,  # Contexto extendido
            **base_config
        ),
        "medium": EmpoorioLMConfig(
            hidden_size=512,
            num_layers=8,
            num_heads=8,
            vocab_size=30000,
            max_position_embeddings=8192,  # Contexto largo
            **base_config
        ),
        "large": EmpoorioLMConfig(
            hidden_size=768,
            num_layers=12,
            num_heads=12,
            vocab_size=30000,
            max_position_embeddings=16384,  # Contexto muy largo
            rope_scaling_factor=2.0,
            rope_ntk_factor=1.4,
            **base_config
        ),
        "xlarge": EmpoorioLMConfig(
            hidden_size=1024,
            num_layers=16,
            num_heads=16,
            vocab_size=50000,
            max_position_embeddings=32768,  # Contexto extremo
            rope_scaling_factor=4.0,
            rope_ntk_factor=1.8,
            use_ring_attention=True,
            ring_world_size=4,  # Para federated learning distribuido
            **base_config
        )
    }
    return configs.get(size, configs["small"])

def load_trained_tokenizer(path: Optional[str] = None) -> EmpoorioLMTokenizer:
    """Load trained tokenizer from a config path."""
    if not path:
        # Default to gpt2 if no path provided
        return EmpoorioLMTokenizer(base_tokenizer_name="gpt2")
    return EmpoorioLMTokenizer.from_pretrained(path)

# For backward compatibility
__all__ = [
    'EmpoorioLM',
    'EmpoorioLMConfig',
    'EmpoorioLMTokenizer',
    'get_config_for_model_size',
    'load_trained_tokenizer',
]
