"""
Surprise Encoder - Motor de sorpresa que calcula entropía/perplejidad en tiempo real
Calcula métricas de sorpresa basadas en la distribución de probabilidad de tokens.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any
import math
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SurpriseMetrics:
    """Métricas de sorpresa calculadas por el encoder."""
    entropy: float  # Entropía de la distribución de probabilidad
    perplexity: float  # Perplejidad (exp(entropy))
    surprise_score: float  # Puntuación de sorpresa normalizada [0,1]
    confidence: float  # Confianza en la predicción (prob del token más probable)
    uncertainty: float  # Incertidumbre (1 - confidence)
    token_probabilities: torch.Tensor  # Probabilidades de tokens
    top_k_probs: torch.Tensor  # Top-K probabilidades
    top_k_tokens: torch.Tensor  # Top-K tokens


class SurpriseEncoder(nn.Module):
    """
    Motor de sorpresa que calcula entropía y perplejidad en tiempo real.

    Características:
    - Cálculo eficiente de entropía usando operaciones vectorizadas
    - Perplejidad en tiempo real para evaluación de sorpresa
    - Métricas de confianza e incertidumbre
    - Soporte para análisis top-K
    """

    def __init__(
        self,
        vocab_size: int = 50257,  # GPT-2 vocab size por defecto
        hidden_size: int = 768,
        num_layers: int = 2,
        dropout: float = 0.1,
        device: str = "auto"
    ):
        """
        Inicializa el Surprise Encoder.

        Args:
            vocab_size: Tamaño del vocabulario
            hidden_size: Dimensión de las representaciones ocultas
            num_layers: Número de capas del encoder
            dropout: Tasa de dropout
            device: Dispositivo para computación
        """
        super().__init__()

        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout = dropout

        # Capa de embedding para tokens (opcional, para análisis contextual)
        self.token_embeddings = nn.Embedding(vocab_size, hidden_size)

        # Encoder transformer ligero para análisis contextual
        encoder_layers = []
        for i in range(num_layers):
            encoder_layers.extend([
                nn.Linear(hidden_size, hidden_size * 4),
                nn.GELU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_size * 4, hidden_size),
                nn.LayerNorm(hidden_size)
            ])

        self.encoder = nn.Sequential(*encoder_layers)

        # Capa de atención para ponderar importancia de tokens
        self.attention_weights = nn.Linear(hidden_size, 1)

        # Capa de salida para predicción de sorpresa
        self.surprise_predictor = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, 1),
            nn.Sigmoid()  # Output entre 0 y 1
        )

        # Configuración del dispositivo
        if device == "auto":
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        self.to(self.device)

        logger.info(f"🚀 SurpriseEncoder inicializado en {self.device}")

    def compute_entropy(self, logits: torch.Tensor) -> torch.Tensor:
        """
        Calcula la entropía de la distribución de probabilidad.

        Args:
            logits: Logits del modelo [batch_size, seq_len, vocab_size]

        Returns:
            Entropía por posición [batch_size, seq_len]
        """
        # Convertir logits a probabilidades
        probs = F.softmax(logits, dim=-1)

        # Calcular entropía: -sum(p * log(p))
        # Usamos log_softmax + nll_loss para estabilidad numérica
        log_probs = F.log_softmax(logits, dim=-1)
        entropy = -torch.sum(probs * log_probs, dim=-1)

        return entropy

    def compute_perplexity(self, logits: torch.Tensor) -> torch.Tensor:
        """
        Calcula la perplejidad de la distribución.

        Args:
            logits: Logits del modelo [batch_size, seq_len, vocab_size]

        Returns:
            Perplejidad por posición [batch_size, seq_len]
        """
        entropy = self.compute_entropy(logits)
        perplexity = torch.exp(entropy)
        return perplexity

    def compute_confidence_metrics(self, logits: torch.Tensor, top_k: int = 5) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Calcula métricas de confianza e incertidumbre.

        Args:
            logits: Logits del modelo [batch_size, seq_len, vocab_size]
            top_k: Número de top tokens a considerar

        Returns:
            confidence, uncertainty, top_k_probs, top_k_tokens
        """
        probs = F.softmax(logits, dim=-1)

        # Confianza: probabilidad del token más probable
        confidence = torch.max(probs, dim=-1)[0]

        # Incertidumbre: 1 - confianza
        uncertainty = 1.0 - confidence

        # Top-K probabilidades e índices
        top_k_probs, top_k_indices = torch.topk(probs, top_k, dim=-1)

        return confidence, uncertainty, top_k_probs, top_k_indices

    def forward(
        self,
        logits: torch.Tensor,
        input_ids: Optional[torch.Tensor] = None,
        attention_mask: Optional[torch.Tensor] = None
    ) -> SurpriseMetrics:
        """
        Calcula todas las métricas de sorpresa.

        Args:
            logits: Logits del modelo [batch_size, seq_len, vocab_size]
            input_ids: IDs de tokens de entrada (opcional) [batch_size, seq_len]
            attention_mask: Máscara de atención (opcional) [batch_size, seq_len]

        Returns:
            SurpriseMetrics con todas las métricas calculadas
        """
        batch_size, seq_len, vocab_size = logits.shape

        # Calcular métricas básicas
        entropy = self.compute_entropy(logits)  # [batch_size, seq_len]
        perplexity = self.compute_perplexity(logits)  # [batch_size, seq_len]
        confidence, uncertainty, top_k_probs, top_k_tokens = self.compute_confidence_metrics(logits)

        # Calcular puntuación de sorpresa contextual si hay input_ids
        if input_ids is not None:
            # Obtener embeddings contextuales
            token_embeds = self.token_embeddings(input_ids)  # [batch_size, seq_len, hidden_size]

            # Aplicar encoder transformer
            context_features = self.encoder(token_embeds)  # [batch_size, seq_len, hidden_size]

            # Calcular pesos de atención
            attention_scores = self.attention_weights(context_features).squeeze(-1)  # [batch_size, seq_len]

            if attention_mask is not None:
                attention_scores = attention_scores.masked_fill(attention_mask == 0, float('-inf'))

            attention_weights = F.softmax(attention_scores, dim=-1)  # [batch_size, seq_len]

            # Ponderar características por atención
            weighted_features = torch.sum(context_features * attention_weights.unsqueeze(-1), dim=1)  # [batch_size, hidden_size]

            # Predecir sorpresa contextual
            contextual_surprise = self.surprise_predictor(weighted_features).squeeze(-1)  # [batch_size]

            # Combinar con perplejidad local
            avg_perplexity = perplexity.mean(dim=-1)  # [batch_size]
            surprise_score = (contextual_surprise + torch.sigmoid(avg_perplexity - 10)) / 2  # Normalizar
        else:
            # Solo usar perplejidad si no hay contexto
            avg_perplexity = perplexity.mean(dim=-1)
            surprise_score = torch.sigmoid(avg_perplexity - 10)  # Normalizar alrededor de perplexity=10

        # Convertir a valores escalares para el último token (más relevante)
        metrics = SurpriseMetrics(
            entropy=entropy[:, -1].mean().item(),
            perplexity=perplexity[:, -1].mean().item(),
            surprise_score=surprise_score.mean().item(),
            confidence=confidence[:, -1].mean().item(),
            uncertainty=uncertainty[:, -1].mean().item(),
            token_probabilities=F.softmax(logits[:, -1], dim=-1),
            top_k_probs=top_k_probs[:, -1],
            top_k_tokens=top_k_tokens[:, -1]
        )

        return metrics

    def get_surprise_thresholds(self) -> Dict[str, float]:
        """
        Retorna umbrales recomendados para clasificación de sorpresa.

        Returns:
            Diccionario con umbrales para diferentes niveles de sorpresa
        """
        return {
            "low_surprise": 0.2,      # Perplejidad baja, predicción confiada
            "medium_surprise": 0.5,   # Perplejidad moderada
            "high_surprise": 0.8      # Perplejidad alta, alta incertidumbre
        }

    def classify_surprise_level(self, metrics: SurpriseMetrics) -> str:
        """
        Clasifica el nivel de sorpresa basado en las métricas.

        Args:
            metrics: SurpriseMetrics calculadas

        Returns:
            Nivel de sorpresa: "low", "medium", "high"
        """
        thresholds = self.get_surprise_thresholds()

        if metrics.surprise_score < thresholds["low_surprise"]:
            return "low"
        elif metrics.surprise_score < thresholds["medium_surprise"]:
            return "medium"
        else:
            return "high"

    def get_memory_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de uso de memoria."""
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)

        return {
            "total_parameters": total_params,
            "trainable_parameters": trainable_params,
            "model_size_mb": total_params * 4 / (1024 * 1024),  # Aproximado en float32
            "device": str(self.device)
        }


def create_surprise_encoder(
    vocab_size: int = 50257,
    hidden_size: int = 768,
    device: str = "auto"
) -> SurpriseEncoder:
    """
    Factory function para crear un SurpriseEncoder.

    Args:
        vocab_size: Tamaño del vocabulario
        hidden_size: Dimensión oculta
        device: Dispositivo

    Returns:
        Instancia de SurpriseEncoder
    """
    return SurpriseEncoder(
        vocab_size=vocab_size,
        hidden_size=hidden_size,
        device=device
    )


# Funciones de conveniencia para análisis en tiempo real
def compute_realtime_surprise(
    logits: torch.Tensor,
    input_ids: Optional[torch.Tensor] = None,
    encoder: Optional[SurpriseEncoder] = None
) -> SurpriseMetrics:
    """
    Función de conveniencia para calcular sorpresa en tiempo real.

    Args:
        logits: Logits del modelo
        input_ids: IDs de entrada (opcional)
        encoder: Encoder pre-entrenado (opcional, se crea si no se proporciona)

    Returns:
        Métricas de sorpresa
    """
    if encoder is None:
        vocab_size = logits.shape[-1]
        encoder = create_surprise_encoder(vocab_size=vocab_size)

    return encoder(logits, input_ids)


def get_surprise_alert_level(metrics: SurpriseMetrics) -> str:
    """
    Determina el nivel de alerta basado en las métricas de sorpresa.

    Args:
        metrics: SurpriseMetrics

    Returns:
        Nivel de alerta: "normal", "warning", "critical"
    """
    if metrics.perplexity > 50 or metrics.surprise_score > 0.9:
        return "critical"
    elif metrics.perplexity > 20 or metrics.surprise_score > 0.7:
        return "warning"
    else:
        return "normal"