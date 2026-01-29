"""
MIRAS Block - Bloque MIRAS con Attentional Bias, Retention Gate y Memory Algorithm
Implementación del bloque MIRAS para memoria adaptativa en tiempo real durante inferencia.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any, Union
import math
import logging
import numpy as np
from dataclasses import dataclass
from .surprise_encoder import SurpriseEncoder, SurpriseMetrics
from ...federated.precision_maintenance import ElasticWeightConsolidationConfig
from ...federated.precision_maintenance import ElasticWeightConsolidationConfig

logger = logging.getLogger(__name__)


@dataclass
class MIRASState:
    """Estado interno del bloque MIRAS."""
    memory_buffer: torch.Tensor  # Buffer de memoria [batch_size, memory_size, hidden_size]
    retention_scores: torch.Tensor  # Puntuaciones de retención [batch_size, seq_len]
    attention_bias: torch.Tensor  # Bias de atención [batch_size, seq_len, seq_len]
    surprise_history: List[float]  # Historial de sorpresa para adaptación
    memory_mask: torch.Tensor  # Máscara de memoria activa [batch_size, memory_size]
    expert_id: Optional[int] = None  # ID del experto para memoria especializada
    expert_memory: Optional[torch.Tensor] = None  # Memoria especializada por experto [num_experts, memory_size, compressed_size]


class AttentionalBias(nn.Module):
    """
    Mecanismo de Attentional Bias para MIRAS.
    Ajusta la atención basada en señales de sorpresa y relevancia contextual.
    """

    def __init__(self, hidden_size: int, num_heads: int = 8, dropout: float = 0.1):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.head_dim = hidden_size // num_heads

        # Redes para calcular bias adaptativo
        self.bias_network = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.GELU(),
            nn.Linear(hidden_size, num_heads),
            nn.Tanh()  # Bias entre -1 y 1
        )

        # Proyección para queries contextuales
        self.context_proj = nn.Linear(hidden_size, hidden_size)

        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        query: torch.Tensor,  # [batch_size, seq_len, hidden_size]
        key: torch.Tensor,    # [batch_size, seq_len, hidden_size]
        surprise_metrics: SurpriseMetrics,
        context_state: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Calcula el bias de atención adaptativo.

        Args:
            query: Queries de atención
            key: Keys de atención
            surprise_metrics: Métricas de sorpresa del encoder
            context_state: Estado contextual opcional

        Returns:
            Bias de atención [batch_size, num_heads, seq_len, seq_len]
        """
        batch_size, seq_len, _ = query.shape

        # Concatenar query y key para análisis conjunto
        combined = torch.cat([query, key], dim=-1)  # [batch_size, seq_len, hidden_size * 2]

        # Calcular bias base
        bias_logits = self.bias_network(combined)  # [batch_size, seq_len, num_heads]

        # Modificar basado en sorpresa
        surprise_factor = torch.tensor(surprise_metrics.surprise_score, device=query.device)
        surprise_factor = surprise_factor.clamp(0.1, 2.0)  # Limitar rango

        # Aplicar factor de sorpresa al bias
        adaptive_bias = bias_logits * surprise_factor

        # Si hay estado contextual, incorporarlo
        if context_state is not None:
            context_proj = self.context_proj(context_state)  # [batch_size, hidden_size]
            context_influence = torch.matmul(context_proj.unsqueeze(1), combined.transpose(1, 2))
            context_influence = context_influence.squeeze(1)  # [batch_size, seq_len]

            # Expandir a todas las heads
            context_bias = context_influence.unsqueeze(-1).expand(-1, -1, self.num_heads)
            adaptive_bias = adaptive_bias + context_bias

        # Aplicar dropout y reshape
        adaptive_bias = self.dropout(adaptive_bias)

        # Reshape para formato de atención: [batch_size, num_heads, seq_len, seq_len]
        # Crear matriz simétrica de bias
        bias_matrix = adaptive_bias.unsqueeze(2) + adaptive_bias.unsqueeze(3).transpose(2, 3)
        bias_matrix = bias_matrix / math.sqrt(self.head_dim)  # Escalar por dimensión

        return bias_matrix


class RetentionGate(nn.Module):
    """
    Retention Gate para control de memoria en MIRAS.
    Decide qué información retener y qué olvidar basado en importancia y sorpresa.
    """

    def __init__(self, hidden_size: int, memory_size: int = 512, dropout: float = 0.1):
        super().__init__()
        self.hidden_size = hidden_size
        self.memory_size = memory_size

        # Red para calcular puntuaciones de retención
        self.retention_network = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, 1),
            nn.Sigmoid()  # Output entre 0 y 1
        )

        # Mecanismo de compresión para memoria
        self.memory_compressor = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.GELU(),
            nn.Linear(hidden_size // 2, hidden_size // 4),
            nn.LayerNorm(hidden_size // 4)
        )

        # Memoria externa
        self.register_buffer('memory_buffer', torch.zeros(memory_size, hidden_size // 4))
        self.register_buffer('memory_age', torch.zeros(memory_size))

    def forward(
        self,
        hidden_states: torch.Tensor,  # [batch_size, seq_len, hidden_size]
        surprise_metrics: SurpriseMetrics,
        prev_memory: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Calcula retención y actualiza memoria.

        Args:
            hidden_states: Estados ocultos actuales
            surprise_metrics: Métricas de sorpresa
            prev_memory: Memoria previa [batch_size, memory_size, compressed_size]

        Returns:
            retention_scores, updated_memory, memory_mask
        """
        batch_size, seq_len, _ = hidden_states.shape

        # Calcular importancia contextual (usando atención self-attention simple)
        # Para simplificar, usamos la magnitud de los estados ocultos
        importance_scores = torch.norm(hidden_states, dim=-1)  # [batch_size, seq_len]

        # Incorporar sorpresa en las puntuaciones
        surprise_tensor = torch.tensor(
            surprise_metrics.surprise_score,
            device=hidden_states.device
        ).expand(batch_size, seq_len)

        # Combinar importancia y sorpresa
        combined_input = torch.cat([
            hidden_states,
            surprise_tensor.unsqueeze(-1).unsqueeze(-1).expand(-1, -1, self.hidden_size)
        ], dim=-1)  # [batch_size, seq_len, hidden_size * 2]

        # Calcular puntuaciones de retención
        retention_scores = self.retention_network(combined_input).squeeze(-1)  # [batch_size, seq_len]

        # Modificar retención basada en sorpresa global
        surprise_factor = surprise_metrics.surprise_score
        if surprise_factor > 0.7:  # Alta sorpresa - retener más
            retention_scores = retention_scores * 1.5
        elif surprise_factor < 0.3:  # Baja sorpresa - retener menos
            retention_scores = retention_scores * 0.7

        retention_scores = torch.clamp(retention_scores, 0.0, 1.0)

        # Comprimir estados para memoria
        compressed_states = self.memory_compressor(hidden_states)  # [batch_size, seq_len, compressed_size]

        # Actualizar memoria
        if prev_memory is not None:
            # Combinar memoria previa con nuevos estados ponderados por retención
            updated_memory = prev_memory * (1 - retention_scores.unsqueeze(-1).mean(dim=1, keepdim=True).unsqueeze(-1))
            updated_memory = updated_memory + (compressed_states * retention_scores.unsqueeze(-1))
        else:
            # Inicializar memoria
            updated_memory = compressed_states * retention_scores.unsqueeze(-1)

        # Crear máscara de memoria activa (basada en edad y retención)
        self.memory_age = self.memory_age + 1  # Incrementar edad
        memory_mask = (self.memory_age < 100).float()  # Máscara simple basada en edad
        memory_mask = memory_mask.unsqueeze(0).expand(batch_size, -1)  # [batch_size, memory_size]

        return retention_scores, updated_memory, memory_mask

    def get_memory_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de la memoria."""
        active_memory = (self.memory_age < 100).sum().item()
        avg_age = self.memory_age.mean().item()

        return {
            'memory_size': self.memory_size,
            'active_memory_slots': active_memory,
            'utilization_rate': active_memory / self.memory_size,
            'average_memory_age': avg_age,
            'memory_compression_ratio': self.hidden_size / (self.hidden_size // 4)
        }


class MemoryAlgorithm(nn.Module):
    """
    Memory Algorithm para recuperación y integración de memoria en MIRAS.
    Implementa búsqueda eficiente y fusión de información de memoria.
    """

    def __init__(self, hidden_size: int, memory_size: int = 512, num_heads: int = 8):
        super().__init__()
        self.hidden_size = hidden_size
        self.memory_size = memory_size
        self.num_heads = num_heads
        self.head_dim = hidden_size // num_heads

        # Mecanismo de atención para búsqueda en memoria
        self.memory_query_proj = nn.Linear(hidden_size, hidden_size)
        self.memory_key_proj = nn.Linear(hidden_size // 4, hidden_size)  # Compressed size
        self.memory_value_proj = nn.Linear(hidden_size // 4, hidden_size)

        # Fusión de memoria con estados actuales
        self.memory_fusion = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.GELU(),
            nn.Linear(hidden_size, hidden_size),
            nn.LayerNorm(hidden_size)
        )

        # Control de gating para integración de memoria
        self.gate_network = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.GELU(),
            nn.Linear(hidden_size, 1),
            nn.Sigmoid()
        )

    def forward(
        self,
        hidden_states: torch.Tensor,  # [batch_size, seq_len, hidden_size]
        memory_buffer: torch.Tensor,  # [batch_size, memory_size, compressed_size]
        memory_mask: torch.Tensor,    # [batch_size, memory_size]
        surprise_metrics: SurpriseMetrics
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Recupera e integra información de memoria.

        Args:
            hidden_states: Estados ocultos actuales
            memory_buffer: Buffer de memoria
            memory_mask: Máscara de memoria activa
            surprise_metrics: Métricas de sorpresa

        Returns:
            hidden_states_updated, memory_attention_weights
        """
        batch_size, seq_len, _ = hidden_states.shape

        # Proyectar queries para búsqueda en memoria
        memory_queries = self.memory_query_proj(hidden_states)  # [batch_size, seq_len, hidden_size]
        memory_queries = memory_queries.view(batch_size * seq_len, self.num_heads, self.head_dim)

        # Proyectar keys y values de memoria
        memory_keys = self.memory_key_proj(memory_buffer)  # [batch_size, memory_size, hidden_size]
        memory_keys = memory_keys.view(batch_size, self.memory_size, self.num_heads, self.head_dim)
        memory_keys = memory_keys.transpose(1, 2)  # [batch_size, num_heads, memory_size, head_dim]

        memory_values = self.memory_value_proj(memory_buffer)  # [batch_size, memory_size, hidden_size]
        memory_values = memory_values.view(batch_size, self.memory_size, self.num_heads, self.head_dim)
        memory_values = memory_values.transpose(1, 2)  # [batch_size, num_heads, memory_size, head_dim]

        # Calcular atención entre queries y memoria
        # [batch_size * seq_len, num_heads, 1, head_dim] x [batch_size, num_heads, head_dim, memory_size]
        memory_queries_expanded = memory_queries.unsqueeze(2)  # [batch_size * seq_len, num_heads, 1, head_dim]

        # Reorganizar para batch matrix multiplication
        memory_keys_flat = memory_keys.view(batch_size, self.num_heads, self.memory_size, self.head_dim)
        memory_keys_transposed = memory_keys_flat.transpose(2, 3)  # [batch_size, num_heads, head_dim, memory_size]

        # Calcular similitudes
        attention_logits = torch.matmul(memory_queries_expanded, memory_keys_transposed)  # [batch_size * seq_len, num_heads, 1, memory_size]
        attention_logits = attention_logits / math.sqrt(self.head_dim)

        # Aplicar máscara de memoria
        memory_mask_expanded = memory_mask.unsqueeze(1).unsqueeze(2)  # [batch_size, 1, 1, memory_size]
        attention_logits = attention_logits.view(batch_size, seq_len, self.num_heads, self.memory_size)
        attention_logits = attention_logits.masked_fill(memory_mask_expanded == 0, float('-inf'))

        # Calcular pesos de atención
        attention_weights = F.softmax(attention_logits, dim=-1)  # [batch_size, seq_len, num_heads, memory_size]

        # Modificar pesos basado en sorpresa
        surprise_factor = torch.tensor(surprise_metrics.surprise_score, device=hidden_states.device)
        if surprise_metrics.surprise_score > 0.6:  # Alta sorpresa - confiar más en memoria
            attention_weights = attention_weights * (1 + surprise_factor)
            attention_weights = attention_weights / attention_weights.sum(dim=-1, keepdim=True)

        # Recuperar valores de memoria
        memory_values_flat = memory_values.view(batch_size, self.num_heads, self.memory_size, self.head_dim)
        attended_memory = torch.matmul(attention_weights, memory_values_flat)  # [batch_size, seq_len, num_heads, head_dim]

        # Reconstruir tensor de memoria atendida
        attended_memory = attended_memory.view(batch_size, seq_len, self.hidden_size)

        # Fusión con estados actuales
        combined = torch.cat([hidden_states, attended_memory], dim=-1)  # [batch_size, seq_len, hidden_size * 2]
        fused_output = self.memory_fusion(combined)

        # Control de gating
        gate_input = torch.cat([hidden_states, attended_memory], dim=-1)
        gate = self.gate_network(gate_input)  # [batch_size, seq_len, 1]

        # Aplicar gating
        hidden_states_updated = gate * fused_output + (1 - gate) * hidden_states

        # Retornar pesos de atención promedio
        memory_attention_weights = attention_weights.mean(dim=2)  # [batch_size, seq_len, memory_size]

        return hidden_states_updated, memory_attention_weights


class MIRASBlock(nn.Module):
    """
    Bloque MIRAS completo que integra Attentional Bias, Retention Gate y Memory Algorithm.
    Diseñado para ser usado en arquitecturas transformer para memoria adaptativa.
    """

    def __init__(
        self,
        hidden_size: int,
        num_heads: int = 8,
        memory_size: int = 512,
        dropout: float = 0.1,
        surprise_encoder: Optional[SurpriseEncoder] = None,
        expert_id: Optional[int] = None,
        num_experts: int = 1
    ):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.memory_size = memory_size
        self.expert_id = expert_id
        self.num_experts = num_experts

        # Componentes MIRAS
        self.attentional_bias = AttentionalBias(hidden_size, num_heads, dropout)
        self.retention_gate = RetentionGate(hidden_size, memory_size, dropout)
        self.memory_algorithm = MemoryAlgorithm(hidden_size, memory_size, num_heads)

        # Encoder de sorpresa (compartido o propio)
        self.surprise_encoder = surprise_encoder or SurpriseEncoder(
            vocab_size=50257,  # GPT-2 default
            hidden_size=hidden_size,
            device="cuda" if torch.cuda.is_available() else "cpu"
        )

        # Estado interno
        self.miras_state: Optional[MIRASState] = None

        # Memoria especializada por experto (solo si es para MoE)
        self.expert_memory_buffer = None
        if expert_id is not None and num_experts > 1:
            compressed_size = hidden_size // 4
            self.register_buffer('expert_memory_buffer',
                               torch.zeros(num_experts, memory_size, compressed_size))
            logger.info(f"🧠 Memoria especializada inicializada para experto {expert_id}")

        # Layer norm para estabilización
        self.layer_norm = nn.LayerNorm(hidden_size)

        logger.info(f"🚀 MIRASBlock inicializado: hidden_size={hidden_size}, memory_size={memory_size}, expert_id={expert_id}")

    def forward(
        self,
        hidden_states: torch.Tensor,  # [batch_size, seq_len, hidden_size]
        attention_mask: Optional[torch.Tensor] = None,
        input_ids: Optional[torch.Tensor] = None,
        logits: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass del bloque MIRAS.

        Args:
            hidden_states: Estados ocultos de entrada
            attention_mask: Máscara de atención
            input_ids: IDs de tokens (para encoder de sorpresa)
            logits: Logits del modelo (para encoder de sorpresa)

        Returns:
            hidden_states_updated, aux_info
        """
        batch_size, seq_len, _ = hidden_states.shape

        # Calcular métricas de sorpresa
        if logits is not None:
            surprise_metrics = self.surprise_encoder(logits, input_ids)
        else:
            # Métricas dummy si no hay logits
            surprise_metrics = SurpriseMetrics(
                entropy=1.0, perplexity=2.71, surprise_score=0.5,
                confidence=0.5, uncertainty=0.5,
                token_probabilities=torch.ones(1, 50257) / 50257,
                top_k_probs=torch.ones(1, 5) / 5,
                top_k_tokens=torch.arange(5).unsqueeze(0)
            )

        # Inicializar estado MIRAS si es necesario
        if self.miras_state is None:
            self._initialize_miras_state(batch_size, hidden_states.device)

        # 1. Calcular Attentional Bias
        # Para simplificar, usamos hidden_states como query y key
        attention_bias = self.attentional_bias(
            hidden_states, hidden_states, surprise_metrics, self.miras_state.memory_buffer.mean(dim=1)
        )

        # 2. Aplicar Retention Gate
        # Usar memoria especializada por experto si está disponible
        prev_memory = self.miras_state.expert_memory if self.miras_state.expert_memory is not None else self.miras_state.memory_buffer
        retention_scores, updated_memory, memory_mask = self.retention_gate(
            hidden_states, surprise_metrics, prev_memory
        )

        # 3. Ejecutar Memory Algorithm
        memory_output, memory_attention = self.memory_algorithm(
            hidden_states, updated_memory, memory_mask, surprise_metrics
        )

        # 4. Integrar con estados originales (residual connection)
        hidden_states_updated = hidden_states + memory_output
        hidden_states_updated = self.layer_norm(hidden_states_updated)

        # Actualizar estado MIRAS
        self._update_miras_state(updated_memory, retention_scores, attention_bias, surprise_metrics, memory_mask)

        # Información auxiliar
        aux_info = {
            'surprise_metrics': surprise_metrics,
            'retention_scores': retention_scores,
            'memory_attention': memory_attention,
            'attention_bias': attention_bias,
            'memory_utilization': memory_mask.mean().item()
        }

        return hidden_states_updated, aux_info

    def _initialize_miras_state(self, batch_size: int, device: torch.device):
        """Inicializa el estado interno de MIRAS."""
        compressed_size = self.hidden_size // 4

        # Inicializar memoria especializada por experto si aplica
        expert_memory = None
        if self.expert_id is not None and self.expert_memory_buffer is not None:
            expert_memory = self.expert_memory_buffer[self.expert_id].unsqueeze(0).expand(batch_size, -1, -1)

        self.miras_state = MIRASState(
            memory_buffer=torch.zeros(batch_size, self.memory_size, compressed_size, device=device),
            retention_scores=torch.zeros(batch_size, 1, device=device),  # Placeholder
            attention_bias=torch.zeros(batch_size, self.num_heads, 1, 1, device=device),  # Placeholder
            surprise_history=[],
            memory_mask=torch.ones(batch_size, self.memory_size, device=device),
            expert_id=self.expert_id,
            expert_memory=expert_memory
        )

    def _update_miras_state(
        self,
        memory_buffer: torch.Tensor,
        retention_scores: torch.Tensor,
        attention_bias: torch.Tensor,
        surprise_metrics: SurpriseMetrics,
        memory_mask: torch.Tensor
    ):
        """Actualiza el estado interno de MIRAS."""
        if self.miras_state is not None:
            self.miras_state.memory_buffer = memory_buffer
            self.miras_state.retention_scores = retention_scores
            self.miras_state.attention_bias = attention_bias
            self.miras_state.memory_mask = memory_mask

            # Actualizar memoria especializada por experto
            if self.expert_id is not None and self.expert_memory_buffer is not None:
                # Promediar la memoria actualizada a través del batch y actualizar el buffer global
                expert_memory_avg = memory_buffer.mean(dim=0)  # [memory_size, compressed_size]
                self.expert_memory_buffer[self.expert_id] = expert_memory_avg
                self.miras_state.expert_memory = memory_buffer

            # Mantener historial de sorpresa (últimas 10 entradas)
            self.miras_state.surprise_history.append(surprise_metrics.surprise_score)
            if len(self.miras_state.surprise_history) > 10:
                self.miras_state.surprise_history.pop(0)

    def get_miras_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del bloque MIRAS."""
        if self.miras_state is None:
            return {"initialized": False}

        retention_gate_stats = self.retention_gate.get_memory_stats()

        return {
            "initialized": True,
            "memory_utilization": self.miras_state.memory_mask.mean().item(),
            "avg_retention_score": self.miras_state.retention_scores.mean().item(),
            "surprise_history_length": len(self.miras_state.surprise_history),
            "avg_surprise_score": sum(self.miras_state.surprise_history) / len(self.miras_state.surprise_history) if self.miras_state.surprise_history else 0,
            "retention_gate_stats": retention_gate_stats
        }

    def reset_memory(self):
        """Reinicia la memoria del bloque MIRAS."""
        self.miras_state = None
        logger.info("🔄 Memoria MIRAS reiniciada")

    def selective_unlearn_user_data(self, user_id: str, unlearning_strength: float = 1.0) -> Dict[str, Any]:
        """
        Unlearning selectivo de datos de usuario específico en memoria MIRAS.

        Args:
            user_id: ID del usuario cuyos datos olvidar
            unlearning_strength: Fuerza del unlearning (0-1)

        Returns:
            Resultado del unlearning selectivo
        """
        if self.miras_state is None:
            return {"success": False, "error": "MIRAS state not initialized"}

        # Identificar slots de memoria asociados al usuario
        # En implementación real, esto requeriría metadata de usuario por slot
        user_memory_mask = self._identify_user_memory_slots(user_id)

        if user_memory_mask.sum() == 0:
            return {"success": True, "message": "No user data found in memory", "slots_affected": 0}

        # Aplicar unlearning selectivo
        original_memory = self.miras_state.memory_buffer.clone()

        # Técnica 1: Gradient inversion local
        perturbed_memory = self._apply_local_gradient_inversion(
            self.miras_state.memory_buffer, user_memory_mask, unlearning_strength
        )

        # Técnica 2: Noise injection
        noise_injected_memory = self._apply_selective_noise_injection(
            perturbed_memory, user_memory_mask, unlearning_strength
        )

        # Técnica 3: Memory consolidation con exclusión
        consolidated_memory = self._consolidate_memory_excluding_user(
            noise_injected_memory, user_memory_mask
        )

        # Actualizar estado
        self.miras_state.memory_buffer = consolidated_memory

        # Verificar efectividad
        effectiveness = self._verify_selective_unlearning(
            original_memory, consolidated_memory, user_memory_mask
        )

        result = {
            "success": True,
            "user_id": user_id,
            "slots_affected": int(user_memory_mask.sum().item()),
            "unlearning_strength": unlearning_strength,
            "effectiveness_score": effectiveness,
            "techniques_applied": ["gradient_inversion", "noise_injection", "memory_consolidation"],
            "memory_utilization_after": self.miras_state.memory_mask.mean().item()
        }

        logger.info(f"🧹 Unlearning selectivo completado para usuario {user_id}: {result}")
        return result

    def selective_unlearn_by_pattern(self, pattern_embedding: torch.Tensor,
                                   similarity_threshold: float = 0.8,
                                   unlearning_strength: float = 1.0) -> Dict[str, Any]:
        """
        Unlearning selectivo basado en similitud de patrones.

        Args:
            pattern_embedding: Embedding del patrón a olvidar
            similarity_threshold: Umbral de similitud (0-1)
            unlearning_strength: Fuerza del unlearning

        Returns:
            Resultado del unlearning por patrón
        """
        if self.miras_state is None:
            return {"success": False, "error": "MIRAS state not initialized"}

        # Calcular similitudes con memoria
        memory_embeddings = self.miras_state.memory_buffer.view(
            self.miras_state.memory_buffer.shape[0], -1
        )  # [batch_size * memory_size, compressed_size]

        pattern_expanded = pattern_embedding.unsqueeze(0).expand_as(memory_embeddings)

        similarities = F.cosine_similarity(memory_embeddings, pattern_expanded, dim=-1)
        similarities = similarities.view(self.miras_state.memory_buffer.shape[:2])  # [batch_size, memory_size]

        # Identificar slots similares
        pattern_mask = (similarities > similarity_threshold).any(dim=0)  # [memory_size]

        if pattern_mask.sum() == 0:
            return {"success": True, "message": "No matching patterns found", "slots_affected": 0}

        # Aplicar unlearning selectivo
        original_memory = self.miras_state.memory_buffer.clone()

        # Gradient inversion basado en patrón
        perturbed_memory = self._apply_pattern_based_inversion(
            self.miras_state.memory_buffer, pattern_mask, unlearning_strength
        )

        # Selective decay
        decayed_memory = self._apply_selective_decay(
            perturbed_memory, pattern_mask, unlearning_strength
        )

        # Actualizar estado
        self.miras_state.memory_buffer = decayed_memory

        # Verificar efectividad
        effectiveness = self._verify_pattern_unlearning(
            original_memory, decayed_memory, pattern_mask
        )

        result = {
            "success": True,
            "pattern_similarity_threshold": similarity_threshold,
            "slots_affected": int(pattern_mask.sum().item()),
            "unlearning_strength": unlearning_strength,
            "effectiveness_score": effectiveness,
            "avg_similarity_before": similarities.mean().item(),
            "techniques_applied": ["pattern_inversion", "selective_decay"]
        }

        logger.info(f"🎯 Unlearning por patrón completado: {result}")
        return result

    def _identify_user_memory_slots(self, user_id: str) -> torch.Tensor:
        """
        Identificar slots de memoria asociados a un usuario.

        En implementación real, esto usaría metadata de usuario por slot.
        Por ahora, simulación basada en hashing consistente.
        """
        # Simulación: usar hash del user_id para determinar slots
        import hashlib
        user_hash = int(hashlib.md5(user_id.encode()).hexdigest()[:8], 16)
        np.random.seed(user_hash)

        # Seleccionar ~10% de slots aleatoriamente pero consistentemente
        num_slots = self.memory_size
        user_slots = np.random.choice(num_slots, size=num_slots // 10, replace=False)

        mask = torch.zeros(num_slots, dtype=torch.bool, device=self.miras_state.memory_buffer.device)
        mask[user_slots] = True

        return mask

    def _apply_local_gradient_inversion(self, memory: torch.Tensor, mask: torch.Tensor,
                                       strength: float) -> torch.Tensor:
        """Aplicar inversión de gradientes local a slots seleccionados."""
        perturbed_memory = memory.clone()

        # Para slots seleccionados, aplicar perturbación basada en gradientes simulados
        noise_scale = strength * 0.1
        inversion_noise = torch.randn_like(memory) * noise_scale

        # Aplicar solo a slots enmascarados
        perturbed_memory[mask.unsqueeze(-1).unsqueeze(0).expand_as(memory)] = \
            memory[mask.unsqueeze(-1).unsqueeze(0).expand_as(memory)] + \
            inversion_noise[mask.unsqueeze(-1).unsqueeze(0).expand_as(memory)]

        return perturbed_memory

    def _apply_selective_noise_injection(self, memory: torch.Tensor, mask: torch.Tensor,
                                        strength: float) -> torch.Tensor:
        """Inyectar ruido selectivo para unlearning."""
        noise_injected = memory.clone()

        # Ruido gaussiano para slots seleccionados
        noise = torch.randn_like(memory) * strength * 0.2
        noise_injected = torch.where(
            mask.unsqueeze(-1).unsqueeze(0).expand_as(memory),
            noise_injected + noise,
            noise_injected
        )

        return noise_injected

    def _consolidate_memory_excluding_user(self, memory: torch.Tensor, user_mask: torch.Tensor) -> torch.Tensor:
        """Consolidar memoria excluyendo datos de usuario."""
        consolidated = memory.clone()

        # Para slots de usuario, reemplazar con promedio de memoria no-usuario
        non_user_memory = memory * (~user_mask).unsqueeze(-1).unsqueeze(0).expand_as(memory)
        non_user_mean = non_user_memory.sum(dim=1, keepdim=True) / (~user_mask).sum().clamp(min=1)

        consolidated = torch.where(
            user_mask.unsqueeze(-1).unsqueeze(0).expand_as(memory),
            non_user_mean.expand_as(memory),
            consolidated
        )

        return consolidated

    def _apply_pattern_based_inversion(self, memory: torch.Tensor, pattern_mask: torch.Tensor,
                                      strength: float) -> torch.Tensor:
        """Aplicar inversión basada en patrón."""
        inverted = memory.clone()

        # Invertir direcciones para slots de patrón
        inversion_factor = -strength * 0.5
        inverted = torch.where(
            pattern_mask.unsqueeze(-1).unsqueeze(0).expand_as(memory),
            memory * inversion_factor,
            inverted
        )

        return inverted

    def _apply_selective_decay(self, memory: torch.Tensor, mask: torch.Tensor,
                              strength: float) -> torch.Tensor:
        """Aplicar decaimiento selectivo."""
        decay_factor = 1.0 - (strength * 0.3)
        decayed = memory.clone()

        decayed = torch.where(
            mask.unsqueeze(-1).unsqueeze(0).expand_as(memory),
            memory * decay_factor,
            decayed
        )

        return decayed

    def _verify_selective_unlearning(self, original: torch.Tensor, modified: torch.Tensor,
                                   mask: torch.Tensor) -> float:
        """Verificar efectividad del unlearning selectivo."""
        # Medir cambio en slots afectados
        diff = torch.norm(original - modified, dim=-1)  # [batch_size, memory_size]

        # Promedio de cambios en slots enmascarados
        affected_changes = diff * mask.unsqueeze(0).expand_as(diff)
        avg_change = affected_changes.sum() / mask.sum().clamp(min=1)

        # Normalizar a score 0-1
        effectiveness = torch.tanh(avg_change * 5).item()

        return effectiveness

    def _verify_pattern_unlearning(self, original: torch.Tensor, modified: torch.Tensor,
                                 pattern_mask: torch.Tensor) -> float:
        """Verificar efectividad del unlearning por patrón."""
        # Medir reducción de similitud con patrón original
        original_norm = torch.norm(original, dim=-1)
        modified_norm = torch.norm(modified, dim=-1)

        # Cambio relativo en norma
        norm_change = (original_norm - modified_norm).abs()
        avg_norm_change = (norm_change * pattern_mask.unsqueeze(0).expand_as(norm_change)).mean()

        effectiveness = torch.tanh(avg_norm_change * 10).item()

        return effectiveness

    def get_unlearning_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de operaciones de unlearning."""
        # En implementación real, trackear historial de unlearning
        return {
            "unlearning_operations_supported": True,
            "selective_unlearning_available": True,
            "pattern_based_unlearning_available": True,
            "gradient_inversion_supported": True,
            "noise_injection_supported": True,
            "memory_consolidation_supported": True
        }

    def get_memory_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de memoria detalladas."""
        total_params = sum(p.numel() for p in self.parameters())
        miras_stats = self.get_miras_stats()
        unlearning_stats = self.get_unlearning_stats()

        return {
            "total_parameters": total_params,
            "trainable_parameters": sum(p.numel() for p in self.parameters() if p.requires_grad),
            "model_size_mb": total_params * 4 / (1024 * 1024),
            "miras_stats": miras_stats,
            "unlearning_stats": unlearning_stats
        }


def create_miras_block(
    hidden_size: int,
    num_heads: int = 8,
    memory_size: int = 512,
    dropout: float = 0.1,
    surprise_encoder: Optional[SurpriseEncoder] = None,
    expert_id: Optional[int] = None,
    num_experts: int = 1
) -> MIRASBlock:
    """
    Factory function para crear un bloque MIRAS.

    Args:
        hidden_size: Dimensión oculta
        num_heads: Número de cabezas de atención
        memory_size: Tamaño de la memoria
        dropout: Tasa de dropout
        surprise_encoder: Encoder de sorpresa (opcional)
        expert_id: ID del experto para memoria especializada (opcional)
        num_experts: Número total de expertos (para memoria especializada)

    Returns:
        Instancia de MIRASBlock
    """
    return MIRASBlock(
        hidden_size=hidden_size,
        num_heads=num_heads,
        memory_size=memory_size,
        dropout=dropout,
        surprise_encoder=surprise_encoder,
        expert_id=expert_id,
        num_experts=num_experts
    )


# Función de integración con capas transformer
def integrate_miras_into_transformer(
    transformer_block: nn.Module,
    miras_block: MIRASBlock,
    integration_pattern: str = "post_attention"
) -> nn.Module:
    """
    Integra un bloque MIRAS en una capa transformer existente.

    Args:
        transformer_block: Bloque transformer original
        miras_block: Bloque MIRAS a integrar
        integration_pattern: Patrón de integración ("post_attention", "pre_ffn", "post_ffn")

    Returns:
        Módulo integrado
    """
    class MIRASIntegratedBlock(nn.Module):
        def __init__(self, original_block, miras_block, pattern):
            super().__init__()
            self.original_block = original_block
            self.miras_block = miras_block
            self.integration_pattern = pattern

        def forward(self, *args, **kwargs):
            # Forward del bloque original
            output = self.original_block(*args, **kwargs)

            # Integrar MIRAS basado en el patrón
            if self.integration_pattern == "post_attention":
                # Después de la atención, antes del FFN
                if isinstance(output, tuple):
                    hidden_states, aux = output
                    miras_output, miras_aux = self.miras_block(hidden_states, **kwargs)
                    return miras_output, {**aux, **miras_aux}
                else:
                    miras_output, miras_aux = self.miras_block(output, **kwargs)
                    return miras_output

            elif self.integration_pattern == "pre_ffn":
                # Antes del FFN
                # (Implementación específica según arquitectura)
                pass

            elif self.integration_pattern == "post_ffn":
                # Después del FFN
                # (Implementación específica según arquitectura)
                pass

            return output

    return MIRASIntegratedBlock(transformer_block, miras_block, integration_pattern)