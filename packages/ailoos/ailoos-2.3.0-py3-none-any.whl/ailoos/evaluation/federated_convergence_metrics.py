"""
Métricas de convergencia federada con validación estadística.
Evalúa la convergencia del sistema federado completo.
"""

import torch
import numpy as np
import scipy.stats as stats
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
from collections import defaultdict

from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class NodeConvergenceData:
    """Datos de convergencia para un nodo específico."""
    node_id: str
    round_number: int
    local_loss: float
    local_accuracy: float
    gradient_norm: float
    model_divergence: float  # Divergencia respecto al modelo global
    contribution_weight: float  # Peso de contribución del nodo
    timestamp: float


@dataclass
class RoundConvergenceMetrics:
    """Métricas de convergencia para una ronda federada."""
    round_number: int
    global_loss: float
    global_accuracy: float
    convergence_score: float
    heterogeneity_index: float  # Medida de heterogeneidad entre nodos
    consensus_level: float  # Nivel de consenso alcanzado
    statistical_significance: float
    node_count: int
    node_data: List[NodeConvergenceData] = field(default_factory=list)


@dataclass
class FederatedConvergenceReport:
    """Reporte completo de convergencia federada."""
    total_rounds: int
    convergence_achieved: bool
    convergence_round: Optional[int]
    heterogeneity_trend: str
    consensus_stability: float
    statistical_confidence: float
    convergence_rate: float
    final_heterogeneity: float
    rounds_history: List[RoundConvergenceMetrics] = field(default_factory=list)


class FederatedConvergenceMetrics:
    """
    Métricas de convergencia federada con validación estadística.
    Evalúa si el sistema federado converge de manera efectiva y consistente.
    """

    def __init__(self, convergence_threshold: float = 0.001, min_rounds_for_convergence: int = 5,
                 statistical_significance_level: float = 0.95):
        self.convergence_threshold = convergence_threshold
        self.min_rounds_for_convergence = min_rounds_for_convergence
        self.statistical_significance_level = statistical_significance_level

        # Historial de métricas por ronda
        self.rounds_history: List[RoundConvergenceMetrics] = []

        # Estado de convergencia
        self.convergence_achieved = False
        self.convergence_round: Optional[int] = None

        # Estadísticas acumuladas
        self.node_participation_stats: Dict[str, List[int]] = defaultdict(list)
        self.global_model_history: List[Dict[str, torch.Tensor]] = []

        logger.info("📊 FederatedConvergenceMetrics initialized")

    def record_round_metrics(self, round_number: int, global_loss: float, global_accuracy: float,
                           node_data: List[NodeConvergenceData]) -> RoundConvergenceMetrics:
        """
        Registra métricas de una ronda federada.

        Args:
            round_number: Número de ronda
            global_loss: Loss global del modelo
            global_accuracy: Accuracy global del modelo
            node_data: Datos de convergencia de cada nodo

        Returns:
            RoundConvergenceMetrics calculadas
        """
        # Calcular métricas de convergencia
        convergence_score = self._calculate_convergence_score(node_data, global_loss, global_accuracy)
        heterogeneity_index = self._calculate_heterogeneity_index(node_data)
        consensus_level = self._calculate_consensus_level(node_data)
        statistical_significance = self._calculate_round_significance(node_data)

        # Actualizar estadísticas de participación
        for node in node_data:
            self.node_participation_stats[node.node_id].append(round_number)

        round_metrics = RoundConvergenceMetrics(
            round_number=round_number,
            global_loss=global_loss,
            global_accuracy=global_accuracy,
            convergence_score=convergence_score,
            heterogeneity_index=heterogeneity_index,
            consensus_level=consensus_level,
            statistical_significance=statistical_significance,
            node_count=len(node_data),
            node_data=node_data
        )

        self.rounds_history.append(round_metrics)

        # Verificar convergencia
        if not self.convergence_achieved and self._check_convergence():
            self.convergence_achieved = True
            self.convergence_round = round_number
            logger.info(f"🎯 Federated convergence achieved at round {round_number}")

        logger.debug(f"📊 Round {round_number} convergence: score={convergence_score:.4f}, "
                    f"heterogeneity={heterogeneity_index:.4f}, consensus={consensus_level:.4f}")

        return round_metrics

    def evaluate_federated_convergence(self) -> FederatedConvergenceReport:
        """
        Evalúa la convergencia del sistema federado completo.

        Returns:
            Reporte completo de convergencia federada
        """
        if len(self.rounds_history) < self.min_rounds_for_convergence:
            return FederatedConvergenceReport(
                total_rounds=len(self.rounds_history),
                convergence_achieved=False,
                convergence_round=None,
                heterogeneity_trend="insufficient_data",
                consensus_stability=0.0,
                statistical_confidence=0.0,
                convergence_rate=0.0,
                final_heterogeneity=0.0,
                rounds_history=self.rounds_history.copy()
            )

        # Análisis de tendencias
        heterogeneity_trend = self._analyze_heterogeneity_trend()
        consensus_stability = self._calculate_consensus_stability()
        statistical_confidence = self._calculate_statistical_confidence()
        convergence_rate = self._calculate_convergence_rate()

        # Heterogeneidad final
        final_heterogeneity = self.rounds_history[-1].heterogeneity_index if self.rounds_history else 0.0

        report = FederatedConvergenceReport(
            total_rounds=len(self.rounds_history),
            convergence_achieved=self.convergence_achieved,
            convergence_round=self.convergence_round,
            heterogeneity_trend=heterogeneity_trend,
            consensus_stability=consensus_stability,
            statistical_confidence=statistical_confidence,
            convergence_rate=convergence_rate,
            final_heterogeneity=final_heterogeneity,
            rounds_history=self.rounds_history.copy()
        )

        logger.info("📊 Federated convergence evaluation:")
        logger.info(f"   Convergence Achieved: {self.convergence_achieved}")
        logger.info(f"   Convergence Round: {self.convergence_round}")
        logger.info(f"   Heterogeneity Trend: {heterogeneity_trend}")
        logger.info(f"   Consensus Stability: {consensus_stability:.4f}")
        logger.info(f"   Statistical Confidence: {statistical_confidence:.4f}")

        return report

    def _calculate_convergence_score(self, node_data: List[NodeConvergenceData],
                                   global_loss: float, global_accuracy: float) -> float:
        """Calcula score de convergencia para la ronda."""
        if not node_data:
            return 0.0

        # Factores de convergencia:
        # 1. Consistencia de loss entre nodos
        # 2. Consistencia de accuracy entre nodos
        # 3. Baja divergencia del modelo
        # 4. Mejora respecto a rondas anteriores

        losses = [node.local_loss for node in node_data]
        accuracies = [node.local_accuracy for node in node_data]
        divergences = [node.model_divergence for node in node_data]

        # Consistencia de loss (1 - coeficiente de variación)
        loss_consistency = 1.0 / (1.0 + np.std(losses) / max(np.mean(losses), 1e-6))

        # Consistencia de accuracy
        accuracy_consistency = 1.0 / (1.0 + np.std(accuracies) / max(np.mean(accuracies), 1e-6))

        # Baja divergencia
        avg_divergence = np.mean(divergences)
        divergence_score = 1.0 / (1.0 + avg_divergence)

        # Mejora respecto a rondas anteriores
        improvement_score = self._calculate_round_improvement(global_loss, global_accuracy)

        # Score final ponderado
        convergence_score = (
            loss_consistency * 0.25 +
            accuracy_consistency * 0.25 +
            divergence_score * 0.25 +
            improvement_score * 0.25
        )

        return min(convergence_score, 1.0)

    def _calculate_heterogeneity_index(self, node_data: List[NodeConvergenceData]) -> float:
        """Calcula índice de heterogeneidad entre nodos."""
        if len(node_data) < 2:
            return 0.0

        # Heterogeneidad basada en:
        # 1. Variabilidad de loss
        # 2. Variabilidad de accuracy
        # 3. Variabilidad de contribución

        losses = [node.local_loss for node in node_data]
        accuracies = [node.local_accuracy for node in node_data]
        contributions = [node.contribution_weight for node in node_data]

        loss_heterogeneity = np.std(losses) / max(np.mean(losses), 1e-6)
        accuracy_heterogeneity = np.std(accuracies) / max(np.mean(accuracies), 1e-6)
        contribution_heterogeneity = np.std(contributions) / max(np.mean(contributions), 1e-6)

        # Índice compuesto
        heterogeneity_index = (loss_heterogeneity + accuracy_heterogeneity + contribution_heterogeneity) / 3.0

        return heterogeneity_index

    def _calculate_consensus_level(self, node_data: List[NodeConvergenceData]) -> float:
        """Calcula nivel de consenso alcanzado entre nodos."""
        if not node_data:
            return 0.0

        # Consenso = 1 - heterogeneidad normalizada
        heterogeneity = self._calculate_heterogeneity_index(node_data)

        # Normalizar heterogeneidad (valores típicos 0-2)
        normalized_heterogeneity = min(heterogeneity / 2.0, 1.0)

        consensus_level = 1.0 - normalized_heterogeneity
        return max(consensus_level, 0.0)

    def _calculate_round_significance(self, node_data: List[NodeConvergenceData]) -> float:
        """Calcula significancia estadística de la ronda."""
        if len(node_data) < 3:
            return 0.0

        try:
            # Test estadístico: comparar loss de nodos vs distribución aleatoria
            losses = [node.local_loss for node in node_data]

            # Test de normalidad (Shapiro-Wilk)
            if len(losses) >= 3:
                stat, p_value = stats.shapiro(losses)
                # Si p_value > 0.05, los datos siguen distribución normal (buena señal)
                normality_score = min(p_value * 20, 1.0)  # Escalar para que sea 0-1
            else:
                normality_score = 0.5

            # Consistencia de la muestra
            cv = np.std(losses) / max(np.mean(losses), 1e-6)
            consistency_score = 1.0 / (1.0 + cv)

            significance = (normality_score + consistency_score) / 2.0

        except Exception as e:
            logger.warning(f"Error calculating round significance: {e}")
            significance = 0.0

        return significance

    def _calculate_round_improvement(self, current_loss: float, current_accuracy: float) -> float:
        """Calcula mejora respecto a rondas anteriores."""
        if len(self.rounds_history) < 1:
            return 0.5  # Score neutral para primera ronda

        prev_round = self.rounds_history[-1]

        # Mejora en loss (disminución)
        loss_improvement = (prev_round.global_loss - current_loss) / max(prev_round.global_loss, 1e-6)
        loss_improvement = max(min(loss_improvement, 1.0), -1.0)  # Clamp entre -1 y 1

        # Mejora en accuracy (aumento)
        accuracy_improvement = (current_accuracy - prev_round.global_accuracy) / max(1 - prev_round.global_accuracy, 1e-6)
        accuracy_improvement = max(min(accuracy_improvement, 1.0), -1.0)

        # Score de mejora (0-1)
        improvement_score = (loss_improvement + accuracy_improvement) / 2.0
        improvement_score = (improvement_score + 1.0) / 2.0  # Convertir de [-1,1] a [0,1]

        return improvement_score

    def _check_convergence(self) -> bool:
        """Verifica si se ha alcanzado convergencia."""
        if len(self.rounds_history) < self.min_rounds_for_convergence:
            return False

        recent_rounds = self.rounds_history[-self.min_rounds_for_convergence:]

        # Criterios de convergencia:
        # 1. Convergence score por encima del threshold
        # 2. Heterogeneidad baja y estable
        # 3. Consensus alto

        avg_convergence = np.mean([r.convergence_score for r in recent_rounds])
        avg_heterogeneity = np.mean([r.heterogeneity_index for r in recent_rounds])
        avg_consensus = np.mean([r.consensus_level for r in recent_rounds])

        convergence_met = (
            avg_convergence >= self.convergence_threshold and
            avg_heterogeneity <= 0.5 and  # Heterogeneidad moderada
            avg_consensus >= 0.7  # Alto consenso
        )

        return convergence_met

    def _analyze_heterogeneity_trend(self) -> str:
        """Analiza la tendencia de heterogeneidad."""
        if len(self.rounds_history) < 3:
            return "insufficient_data"

        heterogeneity_values = [r.heterogeneity_index for r in self.rounds_history]

        # Calcular tendencia usando regresión lineal
        x = np.arange(len(heterogeneity_values))
        slope = np.polyfit(x, heterogeneity_values, 1)[0]

        if slope < -0.01:
            return "decreasing"
        elif slope > 0.01:
            return "increasing"
        else:
            return "stable"

    def _calculate_consensus_stability(self) -> float:
        """Calcula estabilidad del consenso."""
        if len(self.rounds_history) < 3:
            return 0.0

        consensus_values = [r.consensus_level for r in self.rounds_history[-10:]]  # Últimas 10 rondas

        # Estabilidad = 1 - variabilidad
        stability = 1.0 / (1.0 + np.std(consensus_values))
        return min(stability, 1.0)

    def _calculate_statistical_confidence(self) -> float:
        """Calcula confianza estadística general."""
        if len(self.rounds_history) < self.min_rounds_for_convergence:
            return 0.0

        # Promedio de significancia estadística de todas las rondas
        significances = [r.statistical_significance for r in self.rounds_history]

        # Peso por recencia (rondas más recientes tienen más peso)
        weights = np.linspace(0.5, 1.0, len(significances))
        weights = weights / np.sum(weights)

        confidence = np.average(significances, weights=weights)
        return confidence

    def _calculate_convergence_rate(self) -> float:
        """Calcula tasa de convergencia."""
        if not self.convergence_achieved or self.convergence_round is None:
            return 0.0

        # Tasa = 1 / (rondas necesarias para converger)
        convergence_rate = 1.0 / max(self.convergence_round, 1)
        return min(convergence_rate, 1.0)

    def get_node_participation_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de participación de nodos."""
        total_rounds = len(self.rounds_history)

        if total_rounds == 0:
            return {"total_nodes": 0, "participation_rates": {}}

        participation_rates = {}
        for node_id, rounds in self.node_participation_stats.items():
            participation_rates[node_id] = len(rounds) / total_rounds

        return {
            "total_nodes": len(self.node_participation_stats),
            "participation_rates": participation_rates,
            "avg_participation": np.mean(list(participation_rates.values())) if participation_rates else 0.0,
            "most_active_node": max(participation_rates.items(), key=lambda x: x[1])[0] if participation_rates else None
        }

    def get_convergence_summary(self) -> Dict[str, Any]:
        """Obtiene resumen completo de convergencia."""
        if not self.rounds_history:
            return {"status": "no_data"}

        latest_round = self.rounds_history[-1]
        report = self.evaluate_federated_convergence()

        return {
            "status": "evaluated",
            "total_rounds": len(self.rounds_history),
            "latest_round": latest_round.round_number,
            "convergence_achieved": report.convergence_achieved,
            "convergence_round": report.convergence_round,
            "current_convergence_score": latest_round.convergence_score,
            "current_heterogeneity": latest_round.heterogeneity_index,
            "current_consensus": latest_round.consensus_level,
            "heterogeneity_trend": report.heterogeneity_trend,
            "consensus_stability": report.consensus_stability,
            "statistical_confidence": report.statistical_confidence,
            "convergence_rate": report.convergence_rate,
            "node_participation": self.get_node_participation_stats(),
            "evaluation_timestamp": datetime.now().isoformat()
        }

    def reset(self):
        """Resetea las métricas para una nueva sesión federada."""
        self.rounds_history.clear()
        self.convergence_achieved = False
        self.convergence_round = None
        self.node_participation_stats.clear()
        self.global_model_history.clear()
        logger.info("🔄 FederatedConvergenceMetrics reset")