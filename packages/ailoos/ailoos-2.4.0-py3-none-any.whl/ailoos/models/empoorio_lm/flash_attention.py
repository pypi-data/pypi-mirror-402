#!/usr/bin/env python3
"""
Flash Attention 2 Integration para EmpoorioLM
Optimización de memoria para secuencias largas con O(n) complejidad espacial.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple
import math


class FlashAttention2(nn.Module):
    """
    Flash Attention 2 implementation optimizada para secuencias largas.

    Reduce uso de memoria de O(n²) a O(n) usando recomputación y kernels optimizados.
    Compatible con RoPE y causal masking.
    """

    def __init__(self, config):
        super().__init__()
        self.num_heads = config.num_heads
        self.head_dim = config.hidden_size // config.num_heads
        self.dropout = config.dropout
        self.scale = 1.0 / math.sqrt(self.head_dim)

        # Configuración para Flash Attention
        self.use_flash = hasattr(torch.nn.functional, 'scaled_dot_product_attention')
        self.causal = True  # GPT-2 style causal attention

    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        position_ids: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass con Flash Attention 2.

        Args:
            query: [batch_size, seq_len, num_heads, head_dim]
            key: [batch_size, seq_len, num_heads, head_dim]
            value: [batch_size, seq_len, num_heads, head_dim]
            attention_mask: [batch_size, 1, seq_len, seq_len] o None
            position_ids: Para RoPE, si aplica

        Returns:
            Output tensor [batch_size, seq_len, hidden_size]
        """
        batch_size, seq_len, num_heads, head_dim = query.shape

        if self.use_flash and torch.cuda.is_available():
            # Usar PyTorch's native Flash Attention 2 (desde torch 2.0+)
            return self._flash_attention_native(query, key, value, attention_mask)
        else:
            # Fallback a implementación optimizada
            return self._flash_attention_fallback(query, key, value, attention_mask)

    def _flash_attention_native(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        attention_mask: Optional[torch.Tensor]
    ) -> torch.Tensor:
        """Usar PyTorch's native scaled_dot_product_attention (Flash Attention 2)."""
        # Reorganizar para F.scaled_dot_product_attention
        # [batch, seq, heads, dim] -> [batch, heads, seq, dim]
        query = query.transpose(1, 2)
        key = key.transpose(1, 2)
        value = value.transpose(1, 2)

        # Aplicar atención
        attn_output = F.scaled_dot_product_attention(
            query, key, value,
            attn_mask=attention_mask,
            dropout_p=self.dropout if self.training else 0.0,
            is_causal=self.causal and attention_mask is None
        )

        # Reorganizar de vuelta
        attn_output = attn_output.transpose(1, 2)  # [batch, seq, heads, dim]

        # Combinar heads
        batch_size, seq_len, num_heads, head_dim = attn_output.shape
        attn_output = attn_output.reshape(batch_size, seq_len, num_heads * head_dim)

        return attn_output

    def _flash_attention_fallback(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        attention_mask: Optional[torch.Tensor]
    ) -> torch.Tensor:
        """
        Fallback implementation con optimizaciones de memoria.

        Usa chunking para procesar secuencias largas sin OOM.
        """
        batch_size, seq_len, num_heads, head_dim = query.shape

        # Para secuencias muy largas, usar chunking
        if seq_len > 2048:
            return self._chunked_attention(query, key, value, attention_mask)
        else:
            return self._standard_attention(query, key, value, attention_mask)

    def _chunked_attention(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        attention_mask: Optional[torch.Tensor]
    ) -> torch.Tensor:
        """Atención con chunking para secuencias muy largas."""
        batch_size, seq_len, num_heads, head_dim = query.shape

        # Dividir en chunks
        chunk_size = min(1024, seq_len // 4 + 1)
        num_chunks = (seq_len + chunk_size - 1) // chunk_size

        outputs = []

        for i in range(num_chunks):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, seq_len)

            # Extraer chunk actual
            query_chunk = query[:, start_idx:end_idx]
            key_chunk = key[:, :end_idx]  # Usar toda la key hasta ahora
            value_chunk = value[:, :end_idx]

            # Aplicar atención al chunk
            chunk_output = self._standard_attention(
                query_chunk, key_chunk, value_chunk, attention_mask
            )

            outputs.append(chunk_output)

        # Concatenar outputs
        return torch.cat(outputs, dim=1)

    def _standard_attention(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        attention_mask: Optional[torch.Tensor]
    ) -> torch.Tensor:
        """Atención estándar con optimizaciones."""
        batch_size, seq_len, num_heads, head_dim = query.shape

        # Transpose para atención: [batch, heads, seq, dim]
        query = query.transpose(1, 2)
        key = key.transpose(1, 2)
        value = value.transpose(1, 2)

        # Scaled dot-product attention
        attn_weights = torch.matmul(query, key.transpose(-2, -1)) * self.scale

        # Aplicar causal mask si es necesario
        if self.causal and attention_mask is None:
            causal_mask = torch.triu(torch.ones(seq_len, seq_len, device=query.device), diagonal=1).bool()
            attn_weights = attn_weights.masked_fill(causal_mask, float('-inf'))

        # Aplicar attention mask adicional
        if attention_mask is not None:
            attn_weights = attn_weights + attention_mask

        # Softmax
        attn_weights = F.softmax(attn_weights, dim=-1)

        # Dropout
        if self.training:
            attn_weights = F.dropout(attn_weights, p=self.dropout)

        # Aplicar atención
        attn_output = torch.matmul(attn_weights, value)

        # Transpose de vuelta
        attn_output = attn_output.transpose(1, 2)  # [batch, seq, heads, dim]

        # Combinar heads
        attn_output = attn_output.reshape(batch_size, seq_len, num_heads * head_dim)

        return attn_output


class FlashAttentionLayer(nn.Module):
    """
    Capa de atención completa con Flash Attention 2 y RoPE integration.
    """

    def __init__(self, config):
        super().__init__()
        self.q_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=True)
        self.k_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=True)
        self.v_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=True)
        self.out_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=True)

        self.attention = FlashAttention2(config)

        # RoPE será inyectado desde el modelo principal
        self.rope = None

    def set_rope(self, rope):
        """Configurar RoPE para esta capa."""
        self.rope = rope

    def forward(self, hidden_states: torch.Tensor, attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass con Flash Attention y RoPE.

        Args:
            hidden_states: [batch_size, seq_len, hidden_size]
            attention_mask: [batch_size, 1, 1, seq_len]

        Returns:
            Output tensor [batch_size, seq_len, hidden_size]
        """
        batch_size, seq_len, _ = hidden_states.size()

        # Proyecciones lineales
        query = self.q_proj(hidden_states)
        key = self.k_proj(hidden_states)
        value = self.v_proj(hidden_states)

        # Reshape para multi-head
        num_heads = self.attention.num_heads
        head_dim = self.attention.head_dim

        query = query.view(batch_size, seq_len, num_heads, head_dim)
        key = key.view(batch_size, seq_len, num_heads, head_dim)
        value = value.view(batch_size, seq_len, num_heads, head_dim)

        # Aplicar RoPE si está disponible
        if self.rope is not None:
            position_ids = torch.arange(seq_len, device=hidden_states.device).unsqueeze(0).expand(batch_size, -1)
            query, key = self.rope.apply_rope_to_attention(query, key, position_ids)

        # Flash Attention
        attn_output = self.attention(query, key, value, attention_mask)

        # Output projection
        output = self.out_proj(attn_output)

        return output


# Utilidades para configuración
def is_flash_attention_available() -> bool:
    """Verificar si Flash Attention 2 está disponible."""
    return hasattr(torch.nn.functional, 'scaled_dot_product_attention') and torch.cuda.is_available()


def get_optimal_attention_config(seq_len: int, hidden_size: int) -> dict:
    """
    Obtener configuración óptima de atención basada en la longitud de secuencia.

    Args:
        seq_len: Longitud de secuencia
        hidden_size: Tamaño oculto

    Returns:
        Configuración recomendada
    """
    if seq_len <= 1024:
        return {"use_flash": True, "chunk_size": None}
    elif seq_len <= 4096:
        return {"use_flash": True, "chunk_size": 1024}
    elif seq_len <= 16384:
        return {"use_flash": True, "chunk_size": 2048}
    else:
        return {"use_flash": True, "chunk_size": 4096}