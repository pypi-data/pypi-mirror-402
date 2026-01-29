"""
Adversarial Dreamer - Crítico de Sueños para Validación de Memoria REM
=======================================================================

Sistema de validación adversarial que actúa como crítico de sueños durante la consolidación
REM, verificando la consistencia de recuerdos y previniendo alucinaciones mediante
análisis adversarial y validación cruzada.

Características principales:
- Validación adversarial de consistencia de memoria
- Detección de alucinaciones y contradicciones
- Análisis de coherencia temporal y lógica
- Puntuación de confianza de recuerdos
- Integración con consolidación REM
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any, Union
import logging
import time
from dataclasses import dataclass, field
from collections import defaultdict
import hashlib
import json

from ...utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MemoryValidationResult:
    """Resultado de validación de un recuerdo."""
    memory_id: str
    is_consistent: bool
    confidence_score: float
    hallucination_probability: float
    contradiction_score: float
    temporal_coherence: float
    logical_consistency: float
    validation_errors: List[str] = field(default_factory=list)
    adversarial_attacks: List[Dict[str, Any]] = field(default_factory=list)
    validation_timestamp: float = field(default_factory=time.time)


@dataclass
class DreamCritiqueResult:
    """Resultado del análisis crítico de un sueño/memoria."""
    overall_consistency: float
    hallucination_risk: float
    recommended_action: str  # "consolidate", "discard", "quarantine", "investigate"
    critical_issues: List[str]
    validation_results: List[MemoryValidationResult]
    critique_timestamp: float = field(default_factory=time.time)


class AdversarialValidator(nn.Module):
    """
    Validador adversarial que intenta encontrar contradicciones e inconsistencias
    en los recuerdos mediante ataques adversariales.
    """

    def __init__(
        self,
        embedding_size: int = 512,
        hidden_size: int = 256,
        num_attention_heads: int = 8,
        dropout: float = 0.1
    ):
        super().__init__()
        self.embedding_size = embedding_size
        self.hidden_size = hidden_size

        # Encoder para recuerdos
        self.memory_encoder = nn.Sequential(
            nn.Linear(embedding_size, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, hidden_size)
        )

        # Mecanismo de atención para relaciones entre recuerdos
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_size,
            num_heads=num_attention_heads,
            dropout=dropout,
            batch_first=True
        )

        # Cabezas de validación
        self.consistency_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, 1),
            nn.Sigmoid()  # Probabilidad de consistencia
        )

        self.hallucination_detector = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, 1),
            nn.Sigmoid()  # Probabilidad de alucinación
        )

        self.contradiction_analyzer = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),  # Para pares de recuerdos
            nn.ReLU(),
            nn.Linear(hidden_size, 1),
            nn.Sigmoid()  # Probabilidad de contradicción
        )

        # Generador adversarial para ataques
        self.adversarial_generator = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, embedding_size),
            nn.Tanh()  # Genera perturbaciones adversariales
        )

    def forward(self, memory_embeddings: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Valida un conjunto de embeddings de memoria.

        Args:
            memory_embeddings: [batch_size, seq_len, embedding_size]

        Returns:
            Diccionario con resultados de validación
        """
        batch_size, seq_len, emb_size = memory_embeddings.shape

        # Codificar recuerdos
        memory_features = self.memory_encoder(memory_embeddings.view(-1, emb_size))
        memory_features = memory_features.view(batch_size, seq_len, -1)

        # Aplicar atención para modelar relaciones
        attended_features, attention_weights = self.attention(
            memory_features, memory_features, memory_features
        )

        # Validar consistencia individual
        consistency_scores = self.consistency_head(attended_features.mean(dim=1))  # [batch_size, 1]

        # Detectar alucinaciones
        hallucination_scores = self.hallucination_detector(attended_features.mean(dim=1))

        # Analizar contradicciones entre pares
        contradiction_scores = self._analyze_contradictions(memory_features)

        return {
            'consistency_scores': consistency_scores.squeeze(-1),
            'hallucination_scores': hallucination_scores.squeeze(-1),
            'contradiction_matrix': contradiction_scores,
            'attention_weights': attention_weights
        }

    def _analyze_contradictions(self, memory_features: torch.Tensor) -> torch.Tensor:
        """
        Analiza contradicciones entre pares de recuerdos.

        Args:
            memory_features: [batch_size, seq_len, hidden_size]

        Returns:
            Matriz de contradicciones [batch_size, seq_len, seq_len]
        """
        batch_size, seq_len, hidden_size = memory_features.shape

        # Crear pares de recuerdos
        pairs = []
        for i in range(seq_len):
            for j in range(i + 1, seq_len):
                pair_features = torch.cat([
                    memory_features[:, i, :],
                    memory_features[:, j, :]
                ], dim=-1)
                pairs.append(pair_features)

        if not pairs:
            return torch.zeros(batch_size, seq_len, seq_len, device=memory_features.device)

        pairs_tensor = torch.stack(pairs, dim=1)  # [batch_size, num_pairs, hidden_size * 2]

        # Analizar contradicciones
        contradiction_scores = self.contradiction_analyzer(pairs_tensor.view(-1, hidden_size * 2))
        contradiction_scores = contradiction_scores.view(batch_size, -1)

        # Reconstruir matriz
        contradiction_matrix = torch.zeros(batch_size, seq_len, seq_len, device=memory_features.device)

        pair_idx = 0
        for i in range(seq_len):
            for j in range(i + 1, seq_len):
                contradiction_matrix[:, i, j] = contradiction_scores[:, pair_idx]
                contradiction_matrix[:, j, i] = contradiction_scores[:, pair_idx]  # Simétrica
                pair_idx += 1

        return contradiction_matrix

    def generate_adversarial_attack(self, memory_embedding: torch.Tensor) -> torch.Tensor:
        """
        Genera un ataque adversarial para probar robustez del recuerdo.

        Args:
            memory_embedding: [embedding_size]

        Returns:
            Perturbación adversarial [embedding_size]
        """
        encoded = self.memory_encoder(memory_embedding.unsqueeze(0))
        adversarial_perturbation = self.adversarial_generator(encoded.squeeze(0))
        return adversarial_perturbation


class TemporalCoherenceAnalyzer:
    """
    Analiza la coherencia temporal de los recuerdos.
    """

    def __init__(self, time_window_hours: int = 24):
        self.time_window_hours = time_window_hours
        self.temporal_patterns: Dict[str, List[Tuple[float, torch.Tensor]]] = defaultdict(list)

    def analyze_temporal_coherence(
        self,
        memory_id: str,
        memory_embedding: torch.Tensor,
        timestamp: float
    ) -> float:
        """
        Analiza coherencia temporal de un recuerdo.

        Args:
            memory_id: ID del recuerdo
            memory_embedding: Embedding del recuerdo
            timestamp: Timestamp del recuerdo

        Returns:
            Puntaje de coherencia temporal [0-1]
        """
        # Obtener recuerdos relacionados en ventana temporal
        related_memories = []
        time_window_start = timestamp - (self.time_window_hours * 3600)

        for ts, emb in self.temporal_patterns[memory_id]:
            if ts >= time_window_start and ts <= timestamp:
                related_memories.append((ts, emb))

        if len(related_memories) < 2:
            # No hay suficientes recuerdos para analizar coherencia
            coherence = 0.5  # Neutral
        else:
            # Calcular similitud con recuerdos previos
            similarities = []
            for ts, emb in related_memories:
                if ts < timestamp:  # Solo recuerdos anteriores
                    sim = F.cosine_similarity(memory_embedding, emb, dim=-1).item()
                    similarities.append(sim)

            if similarities:
                # Coherencia = promedio de similitudes con contexto temporal
                coherence = sum(similarities) / len(similarities)
                coherence = max(0.0, min(1.0, coherence))  # Clamp to [0,1]
            else:
                coherence = 0.5

        # Almacenar para análisis futuro
        self.temporal_patterns[memory_id].append((timestamp, memory_embedding.detach().cpu()))

        # Limitar historial
        if len(self.temporal_patterns[memory_id]) > 100:
            self.temporal_patterns[memory_id] = self.temporal_patterns[memory_id][-100:]

        return coherence


class LogicalConsistencyChecker:
    """
    Verifica consistencia lógica de los recuerdos.
    """

    def __init__(self):
        self.logical_rules = {
            'causality': self._check_causality,
            'temporal_order': self._check_temporal_order,
            'factual_consistency': self._check_factual_consistency,
            'semantic_coherence': self._check_semantic_coherence
        }

    def check_logical_consistency(
        self,
        memory_content: Dict[str, Any],
        context_memories: List[Dict[str, Any]]
    ) -> Tuple[float, List[str]]:
        """
        Verifica consistencia lógica de un recuerdo.

        Args:
            memory_content: Contenido del recuerdo a validar
            context_memories: Recuerdos de contexto

        Returns:
            (puntaje_consistencia, lista_errores)
        """
        errors = []
        consistency_scores = []

        for rule_name, rule_func in self.logical_rules.items():
            try:
                score, rule_errors = rule_func(memory_content, context_memories)
                consistency_scores.append(score)
                errors.extend(rule_errors)
            except Exception as e:
                logger.warning(f"Error aplicando regla lógica {rule_name}: {e}")
                consistency_scores.append(0.5)  # Neutral en caso de error

        # Puntaje promedio de consistencia
        overall_consistency = sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.5

        return overall_consistency, errors

    def _check_causality(self, memory: Dict[str, Any], context: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Verifica relaciones causales."""
        errors = []
        score = 1.0

        # Implementación simplificada - en producción analizaría relaciones causales
        # entre eventos en los recuerdos
        cause_events = memory.get('causes', [])
        effect_events = memory.get('effects', [])

        if cause_events and effect_events:
            # Verificar que causas precedan efectos
            for cause in cause_events:
                for effect in effect_events:
                    if cause.get('timestamp', 0) > effect.get('timestamp', 0):
                        errors.append(f"Causa posterior a efecto: {cause} -> {effect}")
                        score *= 0.7

        return score, errors

    def _check_temporal_order(self, memory: Dict[str, Any], context: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Verifica orden temporal."""
        errors = []
        score = 1.0

        memory_time = memory.get('timestamp', 0)

        # Verificar consistencia con contexto temporal
        for ctx_memory in context:
            ctx_time = ctx_memory.get('timestamp', 0)
            if abs(memory_time - ctx_time) > 86400:  # 24 horas
                continue

            # Verificar orden lógico de eventos
            if memory_time < ctx_time and memory.get('type') == 'effect' and ctx_memory.get('type') == 'cause':
                errors.append("Orden temporal invertido con recuerdo de contexto")
                score *= 0.8

        return score, errors

    def _check_factual_consistency(self, memory: Dict[str, Any], context: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Verifica consistencia factual."""
        errors = []
        score = 1.0

        facts = memory.get('facts', [])

        for fact in facts:
            # Verificar contra hechos conocidos en contexto
            for ctx_memory in context:
                ctx_facts = ctx_memory.get('facts', [])
                for ctx_fact in ctx_facts:
                    if self._facts_contradict(fact, ctx_fact):
                        errors.append(f"Hecho contradictorio: {fact} vs {ctx_fact}")
                        score *= 0.6

        return score, errors

    def _check_semantic_coherence(self, memory: Dict[str, Any], context: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Verifica coherencia semántica."""
        errors = []
        score = 1.0

        # Implementación simplificada - verificar similitud semántica
        memory_semantics = memory.get('semantic_tags', [])
        context_semantics = []

        for ctx in context:
            context_semantics.extend(ctx.get('semantic_tags', []))

        if memory_semantics and context_semantics:
            # Calcular overlap semántico
            memory_set = set(memory_semantics)
            context_set = set(context_semantics)
            overlap = len(memory_set.intersection(context_set))
            total = len(memory_set.union(context_set))

            if total > 0:
                semantic_similarity = overlap / total
                if semantic_similarity < 0.1:  # Muy diferente
                    errors.append("Baja coherencia semántica con contexto")
                    score *= 0.9

        return score, errors

    def _facts_contradict(self, fact1: Dict[str, Any], fact2: Dict[str, Any]) -> bool:
        """Verifica si dos hechos se contradicen."""
        # Implementación simplificada
        if fact1.get('subject') == fact2.get('subject') and fact1.get('predicate') != fact2.get('predicate'):
            return True
        return False


class AdversarialDreamer:
    """
    Crítico de sueños que valida consistencia de recuerdos durante consolidación REM.
    """

    def __init__(
        self,
        embedding_size: int = 512,
        validation_threshold: float = 0.7,
        hallucination_threshold: float = 0.3,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.embedding_size = embedding_size
        self.validation_threshold = validation_threshold
        self.hallucination_threshold = hallucination_threshold
        self.device = device

        # Componentes del crítico
        self.adversarial_validator = AdversarialValidator(embedding_size=embedding_size)
        self.temporal_analyzer = TemporalCoherenceAnalyzer()
        self.logical_checker = LogicalConsistencyChecker()

        # Estadísticas
        self.validation_stats = {
            'total_validations': 0,
            'consistent_memories': 0,
            'hallucinations_detected': 0,
            'contradictions_found': 0,
            'quarantined_memories': 0
        }

        # Mover a dispositivo
        self.adversarial_validator.to(device)

        logger.info(f"🧠 AdversarialDreamer inicializado con threshold {validation_threshold}")

    def critique_memory_dream(
        self,
        memory_batch: List[Dict[str, Any]],
        context_memories: Optional[List[Dict[str, Any]]] = None
    ) -> DreamCritiqueResult:
        """
        Realiza crítica adversarial de un lote de recuerdos durante "sueño".

        Args:
            memory_batch: Lote de recuerdos a validar
            context_memories: Recuerdos de contexto para comparación

        Returns:
            Resultado del análisis crítico
        """
        if context_memories is None:
            context_memories = []

        validation_results = []
        critical_issues = []
        total_consistency = 0.0
        total_hallucination_risk = 0.0

        # Preparar embeddings para validación adversarial
        memory_embeddings = []
        for memory in memory_batch:
            embedding = self._extract_memory_embedding(memory)
            if embedding is not None:
                memory_embeddings.append(embedding)

        if memory_embeddings:
            embeddings_tensor = torch.stack(memory_embeddings).to(self.device)

            # Validación adversarial
            adversarial_results = self.adversarial_validator(embeddings_tensor)

            consistency_scores = adversarial_results['consistency_scores'].cpu().numpy()
            hallucination_scores = adversarial_results['hallucination_scores'].cpu().numpy()
            contradiction_matrix = adversarial_results['contradiction_matrix'].cpu().numpy()

        # Validar cada recuerdo individualmente
        for i, memory in enumerate(memory_batch):
            memory_id = memory.get('id', f'memory_{i}')

            # Resultados adversariales
            consistency_score = consistency_scores[i] if memory_embeddings else 0.5
            hallucination_prob = hallucination_scores[i] if memory_embeddings else 0.5

            # Análisis de contradicciones
            contradiction_score = contradiction_matrix[i].mean() if memory_embeddings else 0.0

            # Coherencia temporal
            embedding = memory_embeddings[i] if memory_embeddings else None
            temporal_coherence = 0.5
            if embedding is not None:
                timestamp = memory.get('timestamp', time.time())
                temporal_coherence = self.temporal_analyzer.analyze_temporal_coherence(
                    memory_id, embedding, timestamp
                )

            # Consistencia lógica
            logical_consistency, logical_errors = self.logical_checker.check_logical_consistency(
                memory, context_memories
            )

            # Calcular confianza general
            confidence_score = (
                consistency_score * 0.3 +
                (1 - hallucination_prob) * 0.3 +
                (1 - contradiction_score) * 0.2 +
                temporal_coherence * 0.1 +
                logical_consistency * 0.1
            )

            # Recopilar errores de validación
            validation_errors = logical_errors.copy()

            if hallucination_prob > self.hallucination_threshold:
                validation_errors.append(f"Alucinación detectada (prob={hallucination_prob:.3f})")
                critical_issues.append(f"Alucinación detectada en {memory_id}")

            if contradiction_score > 0.5:
                validation_errors.append(f"Contradicciones encontradas (score={contradiction_score:.3f})")
                critical_issues.append(f"Contradicciones encontradas en {memory_id}")

            if temporal_coherence < 0.3:
                validation_errors.append(f"Incoherencia temporal (score={temporal_coherence:.3f})")
                critical_issues.append(f"Incoherencia temporal en {memory_id}")

            # Crear resultado de validación
            validation_result = MemoryValidationResult(
                memory_id=memory_id,
                is_consistent=confidence_score >= self.validation_threshold,
                confidence_score=confidence_score,
                hallucination_probability=hallucination_prob,
                contradiction_score=contradiction_score,
                temporal_coherence=temporal_coherence,
                logical_consistency=logical_consistency,
                validation_errors=validation_errors
            )

            validation_results.append(validation_result)

            # Actualizar estadísticas
            self.validation_stats['total_validations'] += 1
            if validation_result.is_consistent:
                self.validation_stats['consistent_memories'] += 1
            if hallucination_prob > self.hallucination_threshold:
                self.validation_stats['hallucinations_detected'] += 1
            if contradiction_score > 0.5:
                self.validation_stats['contradictions_found'] += 1

            total_consistency += confidence_score
            total_hallucination_risk += hallucination_prob

        # Calcular resultados generales
        num_memories = len(memory_batch)
        overall_consistency = total_consistency / num_memories if num_memories > 0 else 0.0
        hallucination_risk = total_hallucination_risk / num_memories if num_memories > 0 else 0.0

        # Determinar acción recomendada
        if overall_consistency >= self.validation_threshold and hallucination_risk <= self.hallucination_threshold:
            recommended_action = "consolidate"
        elif hallucination_risk > 0.7:
            recommended_action = "discard"
            self.validation_stats['quarantined_memories'] += num_memories
        elif overall_consistency < 0.4:
            recommended_action = "quarantine"
            self.validation_stats['quarantined_memories'] += num_memories
        else:
            recommended_action = "investigate"

        return DreamCritiqueResult(
            overall_consistency=overall_consistency,
            hallucination_risk=hallucination_risk,
            recommended_action=recommended_action,
            critical_issues=critical_issues,
            validation_results=validation_results
        )

    def _extract_memory_embedding(self, memory: Dict[str, Any]) -> Optional[torch.Tensor]:
        """
        Extrae embedding de un recuerdo.

        Args:
            memory: Diccionario con datos del recuerdo

        Returns:
            Embedding del recuerdo o None si no disponible
        """
        # Intentar diferentes fuentes de embedding
        if 'embedding' in memory:
            embedding = memory['embedding']
            if isinstance(embedding, torch.Tensor):
                return embedding
            elif isinstance(embedding, list):
                return torch.tensor(embedding, dtype=torch.float32)

        if 'vector' in memory:
            vector = memory['vector']
            if isinstance(vector, torch.Tensor):
                return vector
            elif isinstance(vector, list):
                return torch.tensor(vector, dtype=torch.float32)

        # Fallback: generar embedding basado en contenido
        content = memory.get('content', '')
        if content:
            # Hash simple del contenido como embedding
            hash_obj = hashlib.sha256(content.encode())
            hash_bytes = hash_obj.digest()
            # Convertir a tensor float
            embedding_values = [float(b) / 255.0 for b in hash_bytes]
            # Repetir para alcanzar embedding_size
            while len(embedding_values) < self.embedding_size:
                embedding_values.extend(embedding_values)
            embedding_values = embedding_values[:self.embedding_size]
            return torch.tensor(embedding_values, dtype=torch.float32)

        return None

    def get_validation_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de validación."""
        stats = self.validation_stats.copy()
        stats.update({
            'consistency_rate': (
                stats['consistent_memories'] / stats['total_validations']
                if stats['total_validations'] > 0 else 0
            ),
            'hallucination_rate': (
                stats['hallucinations_detected'] / stats['total_validations']
                if stats['total_validations'] > 0 else 0
            ),
            'quarantine_rate': (
                stats['quarantined_memories'] / stats['total_validations']
                if stats['total_validations'] > 0 else 0
            )
        })
        return stats

    def reset_stats(self):
        """Reinicia estadísticas de validación."""
        self.validation_stats = {
            'total_validations': 0,
            'consistent_memories': 0,
            'hallucinations_detected': 0,
            'contradictions_found': 0,
            'quarantined_memories': 0
        }


# Función factory
def create_adversarial_dreamer(
    embedding_size: int = 512,
    validation_threshold: float = 0.7,
    hallucination_threshold: float = 0.3,
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
) -> AdversarialDreamer:
    """
    Factory function para crear un Adversarial Dreamer.

    Args:
        embedding_size: Dimensión de los embeddings
        validation_threshold: Threshold para considerar recuerdo consistente
        hallucination_threshold: Threshold para detectar alucinaciones
        device: Dispositivo para cómputo

    Returns:
        AdversarialDreamer instance
    """
    return AdversarialDreamer(
        embedding_size=embedding_size,
        validation_threshold=validation_threshold,
        hallucination_threshold=hallucination_threshold,
        device=device
    )
