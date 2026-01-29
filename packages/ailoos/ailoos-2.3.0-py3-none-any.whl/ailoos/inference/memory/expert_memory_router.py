"""
Expert Memory Router - Router Inteligente para MoE con Memoria
Sistema de routing inteligente que decide qué experto usar basado en contexto y memoria histórica.
Implementa selección adaptativa de expertos, balanceo de carga y optimización de memoria.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any, Union
import math
import logging
from dataclasses import dataclass
from collections import defaultdict
import threading

from .liquid_memory import LiquidMemoryManager

logger = logging.getLogger(__name__)


@dataclass
class RoutingDecision:
    """Decisión de routing para un token específico."""
    token_idx: int
    selected_experts: List[int]  # Lista de expertos seleccionados (top-k)
    routing_weights: List[float]  # Pesos de routing correspondientes
    confidence_score: float  # Puntaje de confianza en la decisión
    domain_classification: str  # Clasificación de dominio ("math", "code", "language", etc.)
    memory_context_used: bool  # Si se usó contexto de memoria para la decisión


@dataclass
class ExpertPerformanceMetrics:
    """Métricas de rendimiento para un experto."""
    expert_id: int
    accuracy_score: float  # Precisión en su dominio
    efficiency_score: float  # Eficiencia de procesamiento
    memory_utilization: float  # Utilización de memoria
    load_factor: float  # Factor de carga actual
    specialization_score: float  # Puntaje de especialización
    last_used: float  # Timestamp del último uso
    usage_count: int  # Número total de usos


class ExpertMemoryRouter(nn.Module):
    """
    Router inteligente que combina análisis contextual con memoria histórica
    para seleccionar los mejores expertos MoE.
    """

    def __init__(
        self,
        num_experts: int,
        hidden_size: int,
        top_k: int = 2,
        context_window: int = 512,
        memory_influence: float = 0.3,
        adaptation_rate: float = 0.01,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        super().__init__()
        self.num_experts = num_experts
        self.hidden_size = hidden_size
        self.top_k = top_k
        self.context_window = context_window
        self.memory_influence = memory_influence
        self.adaptation_rate = adaptation_rate
        self.device = device

        # Redes de análisis contextual
        self.context_analyzer = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.GELU(),
            nn.Linear(hidden_size // 2, hidden_size // 4),
            nn.LayerNorm(hidden_size // 4)
        )

        # Clasificador de dominio
        self.domain_classifier = nn.Sequential(
            nn.Linear(hidden_size // 4, hidden_size // 8),
            nn.GELU(),
            nn.Linear(hidden_size // 8, 8),  # 8 dominios predefinidos
            nn.Softmax(dim=-1)
        )

        # Router principal con memoria
        self.memory_aware_router = nn.Sequential(
            nn.Linear(hidden_size // 4 + num_experts, hidden_size // 2),
            nn.GELU(),
            nn.Linear(hidden_size // 2, num_experts),
            nn.Softmax(dim=-1)
        )

        # Memoria de rendimiento de expertos
        self.expert_metrics = {}
        self._initialize_expert_metrics()

        # Memoria histórica de decisiones
        self.routing_history = []
        self.max_history_size = 1000

        # Estadísticas de routing
        self.routing_stats = {
            "total_routings": 0,
            "domain_distributions": defaultdict(int),
            "expert_load_balance": defaultdict(int),
            "memory_influence_usage": 0
        }

        # Lock para acceso thread-safe
        self.lock = threading.Lock()

        # Mover a dispositivo
        self.to(device)

        logger.info(f"🎯 ExpertMemoryRouter inicializado: {num_experts} expertos, top_k={top_k}")

    def _initialize_expert_metrics(self):
        """Inicializa métricas de rendimiento para cada experto."""
        domain_templates = [
            "mathematics", "language", "code", "science",
            "reasoning", "analysis", "creativity", "general"
        ]

        for i in range(self.num_experts):
            domain = domain_templates[i % len(domain_templates)]
            metrics = ExpertPerformanceMetrics(
                expert_id=i,
                accuracy_score=0.5,  # Inicial neutral
                efficiency_score=1.0,
                memory_utilization=0.0,
                load_factor=0.0,
                specialization_score=0.5,
                last_used=0.0,
                usage_count=0
            )
            self.expert_metrics[i] = metrics

    def forward(
        self,
        hidden_states: torch.Tensor,  # [batch_size, seq_len, hidden_size]
        attention_mask: Optional[torch.Tensor] = None,
        liquid_memory_manager: Optional[LiquidMemoryManager] = None
    ) -> Tuple[torch.Tensor, List[RoutingDecision]]:
        """
        Realiza routing inteligente basado en contexto y memoria.

        Args:
            hidden_states: Estados ocultos de entrada
            attention_mask: Máscara de atención
            liquid_memory_manager: Administrador de memoria líquida (opcional)

        Returns:
            routing_weights: [batch_size, seq_len, num_experts]
            routing_decisions: Lista de decisiones de routing
        """
        batch_size, seq_len, _ = hidden_states.shape

        # Analizar contexto
        context_features = self.context_analyzer(hidden_states)  # [batch_size, seq_len, hidden_size//4]

        # Clasificar dominio para cada posición
        domain_logits = self.domain_classifier(context_features)  # [batch_size, seq_len, 8]
        domain_probs = F.softmax(domain_logits, dim=-1)

        # Obtener información de memoria si está disponible
        memory_context = self._get_memory_context(liquid_memory_manager, batch_size, seq_len)

        # Combinar contexto con información de memoria
        combined_input = torch.cat([context_features, memory_context], dim=-1)

        # Routing con conciencia de memoria
        routing_logits = self.memory_aware_router(combined_input)  # [batch_size, seq_len, num_experts]

        # Aplicar corrección basada en métricas de expertos
        corrected_routing = self._apply_expert_correction(routing_logits, domain_probs)

        # Aplicar máscara de atención si existe
        if attention_mask is not None:
            attention_mask = attention_mask.unsqueeze(-1).expand(-1, -1, self.num_experts)
            corrected_routing = corrected_routing.masked_fill(attention_mask == 0, 0.0)

        # Normalizar
        routing_weights = F.softmax(corrected_routing, dim=-1)

        # Crear decisiones de routing detalladas
        routing_decisions = self._create_routing_decisions(
            routing_weights, domain_probs, memory_context
        )

        # Actualizar estadísticas
        self._update_routing_stats(routing_decisions)

        return routing_weights, routing_decisions

    def _get_memory_context(
        self,
        liquid_memory_manager: Optional[LiquidMemoryManager],
        batch_size: int,
        seq_len: int
    ) -> torch.Tensor:
        """Obtiene contexto de memoria para el routing."""
        if liquid_memory_manager is None:
            # Contexto dummy si no hay memoria líquida
            return torch.zeros(batch_size, seq_len, self.num_experts, device=self.device)

        # Obtener métricas de memoria para cada experto
        memory_context = []
        for expert_id in range(self.num_experts):
            utilization = liquid_memory_manager.liquid_state.memory_utilization.get(expert_id, 0.0)
            efficiency = liquid_memory_manager.liquid_state.expert_profiles[expert_id].memory_efficiency
            specialization = liquid_memory_manager.liquid_state.expert_profiles[expert_id].specialization_score

            # Combinar métricas en un vector
            expert_memory_vector = torch.tensor([
                utilization, efficiency, specialization
            ], device=self.device)

            memory_context.append(expert_memory_vector)

        # Stack y expandir
        memory_context = torch.stack(memory_context, dim=0)  # [num_experts, 3]
        memory_context = memory_context.unsqueeze(0).unsqueeze(0)  # [1, 1, num_experts, 3]
        memory_context = memory_context.expand(batch_size, seq_len, -1, -1)  # [batch_size, seq_len, num_experts, 3]

        # Reducir a [batch_size, seq_len, num_experts]
        memory_context = memory_context.mean(dim=-1)

        return memory_context

    def _apply_expert_correction(
        self,
        routing_logits: torch.Tensor,
        domain_probs: torch.Tensor
    ) -> torch.Tensor:
        """Aplica corrección basada en métricas de rendimiento de expertos."""
        batch_size, seq_len, num_experts = routing_logits.shape

        # Crear tensor de corrección basado en métricas
        correction_factors = torch.zeros(num_experts, device=self.device)

        for expert_id in range(num_experts):
            metrics = self.expert_metrics[expert_id]
            # Factor de corrección basado en precisión, eficiencia y especialización
            correction = (
                metrics.accuracy_score * 0.4 +
                metrics.efficiency_score * 0.3 +
                metrics.specialization_score * 0.3
            )
            correction_factors[expert_id] = correction

        # Aplicar corrección temporal (evitar expertos sobrecargados)
        load_factors = torch.tensor([
            self.expert_metrics[i].load_factor for i in range(num_experts)
        ], device=self.device)

        # Penalizar expertos con alta carga
        load_penalty = torch.sigmoid(load_factors - 0.7)  # Penalizar si carga > 0.7
        correction_factors = correction_factors * (1 - load_penalty * 0.3)

        # Aplicar corrección a los logits
        correction_factors = correction_factors.unsqueeze(0).unsqueeze(0)  # [1, 1, num_experts]
        corrected_logits = routing_logits + correction_factors

        return corrected_logits

    def _create_routing_decisions(
        self,
        routing_weights: torch.Tensor,
        domain_probs: torch.Tensor,
        memory_context: torch.Tensor
    ) -> List[RoutingDecision]:
        """Crea decisiones de routing detalladas."""
        batch_size, seq_len, num_experts = routing_weights.shape
        routing_decisions = []

        domain_names = ["mathematics", "language", "code", "science",
                       "reasoning", "analysis", "creativity", "general"]

        for b in range(batch_size):
            for t in range(seq_len):
                # Obtener top-k expertos
                expert_weights, expert_indices = torch.topk(
                    routing_weights[b, t], self.top_k, dim=-1
                )

                selected_experts = expert_indices.tolist()
                routing_weights_list = expert_weights.tolist()

                # Determinar dominio principal
                domain_idx = torch.argmax(domain_probs[b, t]).item()
                domain_name = domain_names[domain_idx]

                # Calcular confianza (entropía normalizada inversa)
                entropy = -torch.sum(routing_weights[b, t] * torch.log(routing_weights[b, t] + 1e-10))
                max_entropy = math.log(num_experts)
                confidence = 1.0 - (entropy / max_entropy).item()

                # Verificar si se usó memoria
                memory_used = torch.sum(torch.abs(memory_context[b, t])) > 0.01

                decision = RoutingDecision(
                    token_idx=t,
                    selected_experts=selected_experts,
                    routing_weights=routing_weights_list,
                    confidence_score=confidence,
                    domain_classification=domain_name,
                    memory_context_used=memory_used
                )

                routing_decisions.append(decision)

        return routing_decisions

    def _update_routing_stats(self, routing_decisions: List[RoutingDecision]):
        """Actualiza estadísticas de routing."""
        with self.lock:
            self.routing_stats["total_routings"] += len(routing_decisions)

            for decision in routing_decisions:
                # Actualizar distribución de dominios
                self.routing_stats["domain_distributions"][decision.domain_classification] += 1

                # Actualizar balance de carga de expertos
                for expert_id in decision.selected_experts:
                    self.routing_stats["expert_load_balance"][expert_id] += 1

                # Actualizar uso de memoria
                if decision.memory_context_used:
                    self.routing_stats["memory_influence_usage"] += 1

                # Actualizar métricas de expertos
                for expert_id in decision.selected_experts:
                    self.expert_metrics[expert_id].usage_count += 1
                    self.expert_metrics[expert_id].last_used = torch.cuda.Event().elapsed_time() if torch.cuda.is_available() else 0.0

            # Mantener historial limitado
            self.routing_history.extend(routing_decisions)
            if len(self.routing_history) > self.max_history_size:
                self.routing_history = self.routing_history[-self.max_history_size:]

    def update_expert_performance(
        self,
        expert_id: int,
        accuracy: float,
        efficiency: float,
        memory_utilization: float
    ):
        """Actualiza métricas de rendimiento de un experto."""
        with self.lock:
            metrics = self.expert_metrics[expert_id]

            # Actualización exponencial suavizada
            alpha = self.adaptation_rate
            metrics.accuracy_score = alpha * accuracy + (1 - alpha) * metrics.accuracy_score
            metrics.efficiency_score = alpha * efficiency + (1 - alpha) * metrics.efficiency_score
            metrics.memory_utilization = memory_utilization

            # Calcular factor de carga basado en uso reciente
            recent_usage = sum(1 for d in self.routing_history[-100:]
                             if expert_id in d.selected_experts)
            metrics.load_factor = min(1.0, recent_usage / 50.0)  # Normalizar

            # Actualizar puntaje de especialización basado en consistencia
            if metrics.usage_count > 10:
                domain_consistency = self._calculate_domain_consistency(expert_id)
                metrics.specialization_score = domain_consistency

    def _calculate_domain_consistency(self, expert_id: int) -> float:
        """Calcula consistencia de dominio para un experto."""
        recent_decisions = [d for d in self.routing_history[-200:]
                          if expert_id in d.selected_experts]

        if len(recent_decisions) < 5:
            return 0.5

        # Contar dominios más frecuentes
        domain_counts = defaultdict(int)
        for decision in recent_decisions:
            domain_counts[decision.domain_classification] += 1

        # Calcular entropía de distribución de dominios
        total = len(recent_decisions)
        domain_probs = [count / total for count in domain_counts.values()]

        entropy = -sum(p * math.log(p + 1e-10) for p in domain_probs)
        max_entropy = math.log(len(domain_counts))

        # Consistencia = 1 - (entropía normalizada)
        consistency = 1.0 - (entropy / max_entropy if max_entropy > 0 else 0)
        return consistency

    def get_routing_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas completas de routing."""
        with self.lock:
            expert_stats = {}
            for expert_id, metrics in self.expert_metrics.items():
                expert_stats[f"expert_{expert_id}"] = {
                    "accuracy_score": metrics.accuracy_score,
                    "efficiency_score": metrics.efficiency_score,
                    "memory_utilization": metrics.memory_utilization,
                    "load_factor": metrics.load_factor,
                    "specialization_score": metrics.specialization_score,
                    "usage_count": metrics.usage_count,
                    "last_used": metrics.last_used
                }

            return {
                "total_routings": self.routing_stats["total_routings"],
                "domain_distributions": dict(self.routing_stats["domain_distributions"]),
                "expert_load_balance": dict(self.routing_stats["expert_load_balance"]),
                "memory_influence_usage": self.routing_stats["memory_influence_usage"],
                "memory_influence_ratio": (
                    self.routing_stats["memory_influence_usage"] /
                    self.routing_stats["total_routings"] if self.routing_stats["total_routings"] > 0 else 0
                ),
                "expert_stats": expert_stats,
                "routing_history_size": len(self.routing_history)
            }

    def reset_routing_history(self):
        """Reinicia el historial de routing."""
        with self.lock:
            self.routing_history.clear()
            self.routing_stats = {
                "total_routings": 0,
                "domain_distributions": defaultdict(int),
                "expert_load_balance": defaultdict(int),
                "memory_influence_usage": 0
            }
            logger.info("🔄 Historial de routing reiniciado")


def create_expert_memory_router(
    num_experts: int,
    hidden_size: int,
    top_k: int = 2,
    context_window: int = 512,
    memory_influence: float = 0.3,
    adaptation_rate: float = 0.01,
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
) -> ExpertMemoryRouter:
    """
    Factory function para crear un router de memoria de expertos.

    Args:
        num_experts: Número de expertos
        hidden_size: Dimensión oculta
        top_k: Número de expertos a seleccionar
        context_window: Ventana de contexto
        memory_influence: Influencia de la memoria en el routing
        adaptation_rate: Tasa de adaptación
        device: Dispositivo

    Returns:
        ExpertMemoryRouter instance
    """
    return ExpertMemoryRouter(
        num_experts=num_experts,
        hidden_size=hidden_size,
        top_k=top_k,
        context_window=context_window,
        memory_influence=memory_influence,
        adaptation_rate=adaptation_rate,
        device=device
    )