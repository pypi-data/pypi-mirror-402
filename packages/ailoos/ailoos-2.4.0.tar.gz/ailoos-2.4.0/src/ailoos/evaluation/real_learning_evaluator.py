"""
Evaluador de aprendizaje real para EmpoorioLM.
Mide mejora real del modelo con métricas verificables.
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import statistics
import logging

from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class LearningMetrics:
    """Métricas de aprendizaje en un punto específico."""
    timestamp: float
    round_number: int
    loss: float
    perplexity: float
    accuracy: float
    gradient_norm: float
    learning_rate: float
    convergence_score: float
    validation_confidence: float


@dataclass
class LearningProgressReport:
    """Reporte completo de progreso de aprendizaje."""
    total_rounds: int
    is_learning: bool
    improvement_rate: float
    convergence_achieved: bool
    stagnation_detected: bool
    metrics_history: List[LearningMetrics] = field(default_factory=list)
    statistical_significance: float = 0.0
    confidence_level: float = 0.0


class RealLearningEvaluator:
    """
    Evaluador que mide mejora real del modelo con métricas irrefutables.
    Proporciona evidencia estadística de que EmpoorioLM aprende de verdad.
    """

    def __init__(self, min_rounds_for_evaluation: int = 5, statistical_significance_threshold: float = 0.95):
        self.min_rounds_for_evaluation = min_rounds_for_evaluation
        self.statistical_significance_threshold = statistical_significance_threshold

        # Historial de métricas
        self.metrics_history: List[LearningMetrics] = []
        self.baseline_metrics: Optional[LearningMetrics] = None

        # Estado de evaluación
        self.convergence_achieved = False
        self.stagnation_detected = False
        self.last_evaluation_round = 0

        logger.info("🧠 RealLearningEvaluator initialized")

    def record_metrics(self, round_number: int, loss: float, perplexity: float,
                      accuracy: float, gradient_norm: float, learning_rate: float) -> LearningMetrics:
        """
        Registra métricas de una ronda de entrenamiento.

        Args:
            round_number: Número de ronda
            loss: Valor de loss
            perplexity: Perplexity del modelo
            accuracy: Accuracy del modelo
            gradient_norm: Norma del gradiente
            learning_rate: Learning rate actual

        Returns:
            LearningMetrics registradas
        """
        # Calcular métricas adicionales
        convergence_score = self._calculate_convergence_score()
        validation_confidence = self._calculate_validation_confidence()

        metrics = LearningMetrics(
            timestamp=datetime.now().timestamp(),
            round_number=round_number,
            loss=loss,
            perplexity=perplexity,
            accuracy=accuracy,
            gradient_norm=gradient_norm,
            learning_rate=learning_rate,
            convergence_score=convergence_score,
            validation_confidence=validation_confidence
        )

        self.metrics_history.append(metrics)

        # Establecer baseline si es la primera medición
        if self.baseline_metrics is None:
            self.baseline_metrics = metrics

        logger.debug(f"📊 Metrics recorded for round {round_number}: loss={loss:.4f}, ppl={perplexity:.2f}, acc={accuracy:.4f}")
        return metrics

    def evaluate_learning_progress(self) -> LearningProgressReport:
        """
        Evalúa el progreso de aprendizaje con análisis estadístico.

        Returns:
            Reporte completo de progreso de aprendizaje
        """
        if len(self.metrics_history) < self.min_rounds_for_evaluation:
            return LearningProgressReport(
                total_rounds=len(self.metrics_history),
                is_learning=False,
                improvement_rate=0.0,
                convergence_achieved=False,
                stagnation_detected=False,
                metrics_history=self.metrics_history.copy()
            )

        # Análisis de tendencias
        loss_trend = self._analyze_trend([m.loss for m in self.metrics_history])
        accuracy_trend = self._analyze_trend([m.accuracy for m in self.metrics_history])
        perplexity_trend = self._analyze_trend([m.perplexity for m in self.metrics_history])

        # Calcular tasa de mejora
        improvement_rate = self._calculate_improvement_rate()

        # Evaluar aprendizaje real
        is_learning = self._evaluate_real_learning(loss_trend, accuracy_trend, perplexity_trend)

        # Detectar convergencia
        convergence_achieved = self._detect_convergence()

        # Detectar estancamiento
        stagnation_detected = self._detect_stagnation()

        # Significancia estadística
        statistical_significance = self._calculate_statistical_significance()

        # Nivel de confianza
        confidence_level = self._calculate_overall_confidence()

        report = LearningProgressReport(
            total_rounds=len(self.metrics_history),
            is_learning=is_learning,
            improvement_rate=improvement_rate,
            convergence_achieved=convergence_achieved,
            stagnation_detected=stagnation_detected,
            metrics_history=self.metrics_history.copy(),
            statistical_significance=statistical_significance,
            confidence_level=confidence_level
        )

        self.last_evaluation_round = self.metrics_history[-1].round_number

        logger.info("🧠 Learning evaluation completed:")
        logger.info(f"   Is Learning: {is_learning}")
        logger.info(f"   Improvement Rate: {improvement_rate:.4f}")
        logger.info(f"   Convergence: {convergence_achieved}")
        logger.info(f"   Statistical Significance: {statistical_significance:.3f}")
        logger.info(f"   Confidence Level: {confidence_level:.3f}")

        return report

    def _calculate_convergence_score(self) -> float:
        """Calcula score de convergencia basado en estabilidad de métricas."""
        if len(self.metrics_history) < 3:
            return 0.0

        recent_losses = [m.loss for m in self.metrics_history[-5:]]
        recent_accuracies = [m.accuracy for m in self.metrics_history[-5:]]

        # Convergencia = estabilidad de loss + mejora consistente de accuracy
        loss_stability = 1.0 / (1.0 + np.std(recent_losses))
        accuracy_trend = self._calculate_trend_slope(recent_accuracies)

        convergence_score = (loss_stability * 0.6) + (max(0, accuracy_trend) * 0.4)
        return min(convergence_score, 1.0)

    def _calculate_validation_confidence(self) -> float:
        """Calcula confianza en la validación basada en consistencia de datos."""
        if len(self.metrics_history) < 3:
            return 0.0

        # Confianza basada en variabilidad de métricas
        loss_variability = np.std([m.loss for m in self.metrics_history[-10:]])
        accuracy_variability = np.std([m.accuracy for m in self.metrics_history[-10:]])

        # Menor variabilidad = mayor confianza
        confidence = 1.0 / (1.0 + loss_variability + accuracy_variability)
        return min(confidence, 1.0)

    def _analyze_trend(self, values: List[float]) -> str:
        """Analiza la tendencia de una serie de valores."""
        if len(values) < 3:
            return "insufficient_data"

        slope = self._calculate_trend_slope(values)

        if slope < -0.01:
            return "improving"
        elif slope > 0.01:
            return "degrading"
        else:
            return "stable"

    def _calculate_trend_slope(self, values: List[float]) -> float:
        """Calcula la pendiente de tendencia usando regresión lineal simple."""
        if len(values) < 2:
            return 0.0

        n = len(values)
        x = np.arange(n)
        y = np.array(values)

        # Regresión lineal
        slope = np.polyfit(x, y, 1)[0]
        return slope

    def _calculate_improvement_rate(self) -> float:
        """Calcula la tasa de mejora global."""
        if len(self.metrics_history) < 2:
            return 0.0

        initial_loss = self.metrics_history[0].loss
        final_loss = self.metrics_history[-1].loss

        initial_accuracy = self.metrics_history[0].accuracy
        final_accuracy = self.metrics_history[-1].accuracy

        # Tasa de mejora = mejora relativa en loss + mejora en accuracy
        loss_improvement = (initial_loss - final_loss) / initial_loss if initial_loss > 0 else 0
        accuracy_improvement = (final_accuracy - initial_accuracy) / (1 - initial_accuracy) if initial_accuracy < 1 else 0

        improvement_rate = (loss_improvement * 0.6) + (accuracy_improvement * 0.4)
        return improvement_rate

    def _evaluate_real_learning(self, loss_trend: str, accuracy_trend: str, perplexity_trend: str) -> bool:
        """Evalúa si hay aprendizaje real basado en tendencias."""
        # Criterios para aprendizaje real:
        # 1. Loss mejorando (disminuyendo)
        # 2. Accuracy mejorando (aumentando)
        # 3. Perplexity mejorando (disminuyendo)

        loss_improving = loss_trend == "improving"
        accuracy_improving = accuracy_trend == "improving"
        perplexity_improving = perplexity_trend == "improving"

        # Al menos 2 de 3 métricas deben mostrar mejora
        positive_indicators = sum([loss_improving, accuracy_improving, perplexity_improving])

        return positive_indicators >= 2

    def _detect_convergence(self) -> bool:
        """Detecta si el modelo ha convergido."""
        if len(self.metrics_history) < 10:
            return False

        recent_losses = [m.loss for m in self.metrics_history[-5:]]
        recent_accuracies = [m.accuracy for m in self.metrics_history[-5:]]

        # Convergencia = loss estable y accuracy alta
        loss_std = np.std(recent_losses)
        avg_accuracy = np.mean(recent_accuracies)

        convergence_threshold = 0.01  # 1% variabilidad máxima
        min_accuracy = 0.8  # 80% accuracy mínima

        converged = loss_std < convergence_threshold and avg_accuracy > min_accuracy

        if converged and not self.convergence_achieved:
            self.convergence_achieved = True
            logger.info("🎯 Model convergence achieved!")

        return converged

    def _detect_stagnation(self) -> bool:
        """Detecta si el modelo se ha estancado."""
        if len(self.metrics_history) < 10:
            return False

        recent_losses = [m.loss for m in self.metrics_history[-10:]]
        recent_accuracies = [m.accuracy for m in self.metrics_history[-10:]]

        # Estancamiento = no mejora significativa en las últimas rondas
        loss_slope = self._calculate_trend_slope(recent_losses)
        accuracy_slope = self._calculate_trend_slope(recent_accuracies)

        stagnation_threshold = 0.001  # Muy poca mejora

        stagnated = abs(loss_slope) < stagnation_threshold and abs(accuracy_slope) < stagnation_threshold

        if stagnated and not self.stagnation_detected:
            self.stagnation_detected = True
            logger.warning("⚠️ Learning stagnation detected!")

        return stagnated

    def _calculate_statistical_significance(self) -> float:
        """Calcula significancia estadística de las mejoras."""
        if len(self.metrics_history) < self.min_rounds_for_evaluation:
            return 0.0

        try:
            # Test t-student para comparar baseline vs final
            initial_losses = [m.loss for m in self.metrics_history[:5]]
            final_losses = [m.loss for m in self.metrics_history[-5:]]

            if len(initial_losses) >= 3 and len(final_losses) >= 3:
                # Calcular t-statistic
                t_stat = self._t_test(initial_losses, final_losses)
                # Convertir a p-value aproximado (simplificado)
                p_value = 1.0 / (1.0 + abs(t_stat))
                significance = 1.0 - p_value
            else:
                significance = 0.0

        except Exception as e:
            logger.warning(f"Error calculating statistical significance: {e}")
            significance = 0.0

        return significance

    def _t_test(self, group1: List[float], group2: List[float]) -> float:
        """Test t-student simplificado."""
        mean1, mean2 = np.mean(group1), np.mean(group2)
        std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
        n1, n2 = len(group1), len(group2)

        # t-statistic
        se = np.sqrt((std1**2 / n1) + (std2**2 / n2))
        if se == 0:
            return 0.0

        t = (mean1 - mean2) / se
        return t

    def _calculate_overall_confidence(self) -> float:
        """Calcula confianza general en la evaluación."""
        if len(self.metrics_history) < self.min_rounds_for_evaluation:
            return 0.0

        # Factores de confianza
        data_consistency = self._calculate_data_consistency()
        trend_strength = self._calculate_trend_strength()
        statistical_power = min(self._calculate_statistical_significance() * 2, 1.0)

        confidence = (data_consistency * 0.4) + (trend_strength * 0.4) + (statistical_power * 0.2)
        return confidence

    def _calculate_data_consistency(self) -> float:
        """Calcula consistencia de los datos."""
        if len(self.metrics_history) < 5:
            return 0.0

        # Verificar que no hay valores NaN o infinitos
        losses = [m.loss for m in self.metrics_history]
        accuracies = [m.accuracy for m in self.metrics_history]

        has_invalid = any(np.isnan(losses)) or any(np.isinf(losses)) or \
                     any(np.isnan(accuracies)) or any(np.isinf(accuracies))

        if has_invalid:
            return 0.0

        # Consistencia = baja variabilidad relativa
        loss_cv = np.std(losses) / np.mean(losses) if np.mean(losses) > 0 else 1.0
        accuracy_cv = np.std(accuracies) / np.mean(accuracies) if np.mean(accuracies) > 0 else 1.0

        consistency = 1.0 / (1.0 + loss_cv + accuracy_cv)
        return min(consistency, 1.0)

    def _calculate_trend_strength(self) -> float:
        """Calcula fuerza de las tendencias observadas."""
        if len(self.metrics_history) < 5:
            return 0.0

        loss_slope = abs(self._calculate_trend_slope([m.loss for m in self.metrics_history]))
        accuracy_slope = abs(self._calculate_trend_slope([m.accuracy for m in self.metrics_history]))

        # Normalizar slopes (valores típicos: 0.01-0.1 para slopes significativos)
        normalized_loss_slope = min(loss_slope / 0.05, 1.0)
        normalized_accuracy_slope = min(accuracy_slope / 0.05, 1.0)

        trend_strength = (normalized_loss_slope + normalized_accuracy_slope) / 2.0
        return trend_strength

    def get_evaluation_summary(self) -> Dict[str, Any]:
        """Obtiene resumen completo de la evaluación."""
        if not self.metrics_history:
            return {"status": "no_data"}

        latest_metrics = self.metrics_history[-1]
        report = self.evaluate_learning_progress()

        return {
            "status": "evaluated",
            "total_rounds": len(self.metrics_history),
            "latest_round": latest_metrics.round_number,
            "current_loss": latest_metrics.loss,
            "current_perplexity": latest_metrics.perplexity,
            "current_accuracy": latest_metrics.accuracy,
            "is_learning": report.is_learning,
            "improvement_rate": report.improvement_rate,
            "convergence_achieved": report.convergence_achieved,
            "stagnation_detected": report.stagnation_detected,
            "statistical_significance": report.statistical_significance,
            "confidence_level": report.confidence_level,
            "evaluation_timestamp": datetime.now().isoformat()
        }

    def reset(self):
        """Resetea el evaluador para una nueva sesión."""
        self.metrics_history.clear()
        self.baseline_metrics = None
        self.convergence_achieved = False
        self.stagnation_detected = False
        self.last_evaluation_round = 0
        logger.info("🔄 RealLearningEvaluator reset")