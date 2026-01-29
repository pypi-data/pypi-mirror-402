"""
Model Evolution Tracker - Seguimiento de la evolución del modelo
Rastrea cambios, mejoras y posibles problemas en la evolución del modelo.
"""

import asyncio
import json
import time
import torch
import torch.nn as nn
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from pathlib import Path

from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ModelVersion:
    """Versión del modelo con metadatos."""
    version_id: str
    model_cid: str  # IPFS CID
    parent_version: Optional[str]
    created_at: float = field(default_factory=time.time)
    training_round: int = 0
    metrics: Dict[str, float] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    architecture_changes: List[str] = field(default_factory=list)
    domain_adaptations: List[str] = field(default_factory=list)
    curriculum_stage: Optional[str] = None
    privacy_budget_used: float = 0.0
    data_processed: int = 0
    training_time: float = 0.0


@dataclass
class EvolutionEvent:
    """Evento en la evolución del modelo."""
    event_id: str
    event_type: str  # "improvement", "degradation", "adaptation", "reset"
    timestamp: float = field(default_factory=time.time)
    version_from: Optional[str] = None
    version_to: Optional[str] = None
    metrics_change: Dict[str, float] = field(default_factory=dict)
    trigger_reason: str = ""
    impact_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceTrend:
    """Tendencia de rendimiento."""
    metric_name: str
    values: List[float] = field(default_factory=list)
    timestamps: List[float] = field(default_factory=list)
    trend_slope: float = 0.0
    volatility: float = 0.0
    last_updated: float = field(default_factory=time.time)


@dataclass
class ModelHealthIndicator:
    """Indicador de salud del modelo."""
    indicator_name: str
    current_value: float
    threshold: float
    status: str  # "healthy", "warning", "critical"
    trend: str  # "improving", "stable", "degrading"
    last_assessed: float = field(default_factory=time.time)
    recommendations: List[str] = field(default_factory=list)


class ModelEvolutionTracker:
    """
    Rastreador de evolución del modelo.
    Monitorea cambios, mejoras y salud del modelo a lo largo del tiempo.
    """

    def __init__(self, model_name: str, session_id: str):
        self.model_name = model_name
        self.session_id = session_id

        # Historial de versiones
        self.model_versions: Dict[str, ModelVersion] = {}
        self.version_history: List[str] = []  # Orden cronológico

        # Eventos de evolución
        self.evolution_events: List[EvolutionEvent] = []

        # Tendencias de rendimiento
        self.performance_trends: Dict[str, PerformanceTrend] = {}

        # Indicadores de salud
        self.health_indicators: Dict[str, ModelHealthIndicator] = {}
        self._initialize_health_indicators()

        # Línea base de rendimiento
        self.baseline_version: Optional[str] = None
        self.baseline_metrics: Dict[str, float] = {}

        # Estadísticas de evolución
        self.evolution_stats = {
            "total_versions": 0,
            "total_events": 0,
            "avg_improvement_rate": 0.0,
            "degradation_events": 0,
            "adaptation_events": 0,
            "reset_events": 0,
            "health_score": 1.0,
            "evolution_efficiency": 0.0
        }

        # Configuración de alertas
        self.alert_thresholds = {
            "accuracy_drop": 0.05,
            "f1_drop": 0.05,
            "loss_increase": 0.1,
            "health_critical": 0.3
        }

        logger.info(f"📈 ModelEvolutionTracker initialized for {model_name}")

    def _initialize_health_indicators(self):
        """Inicializar indicadores de salud del modelo."""
        indicators = [
            ("accuracy_stability", 0.85, 0.75),
            ("f1_consistency", 0.82, 0.70),
            ("loss_trend", 0.3, 0.5),  # Menor es mejor
            ("adaptation_success", 0.8, 0.6),
            ("privacy_preservation", 0.9, 0.7),
            ("generalization", 0.75, 0.6)
        ]

        for name, initial_value, threshold in indicators:
            self.health_indicators[name] = ModelHealthIndicator(
                indicator_name=name,
                current_value=initial_value,
                threshold=threshold,
                status="healthy",
                trend="stable"
            )

    def register_model_version(self, version_id: str, model_cid: str,
                             metrics: Dict[str, float], metadata: Dict[str, Any] = None) -> ModelVersion:
        """
        Registrar nueva versión del modelo.

        Args:
            version_id: ID único de la versión
            model_cid: CID de IPFS del modelo
            metrics: Métricas de rendimiento
            metadata: Metadatos adicionales

        Returns:
            Versión registrada
        """
        if version_id in self.model_versions:
            logger.warning(f"⚠️ Version {version_id} already exists, updating")

        # Determinar versión padre
        parent_version = self.version_history[-1] if self.version_history else None

        version = ModelVersion(
            version_id=version_id,
            model_cid=model_cid,
            parent_version=parent_version,
            metrics=metrics.copy(),
            parameters=metadata.get("parameters", {}) if metadata else {},
            architecture_changes=metadata.get("architecture_changes", []) if metadata else [],
            domain_adaptations=metadata.get("domain_adaptations", []) if metadata else [],
            curriculum_stage=metadata.get("curriculum_stage") if metadata else None,
            privacy_budget_used=metadata.get("privacy_budget_used", 0.0) if metadata else 0.0,
            data_processed=metadata.get("data_processed", 0) if metadata else 0,
            training_time=metadata.get("training_time", 0.0) if metadata else 0.0,
            training_round=metadata.get("training_round", 0) if metadata else 0
        )

        self.model_versions[version_id] = version
        self.version_history.append(version_id)
        self.evolution_stats["total_versions"] += 1

        # Actualizar tendencias de rendimiento
        self._update_performance_trends(version)

        # Analizar evolución
        self._analyze_version_evolution(version)

        # Establecer línea base si es la primera versión
        if not self.baseline_version:
            self.baseline_version = version_id
            self.baseline_metrics = metrics.copy()

        logger.info(f"📝 Registered model version {version_id} with CID {model_cid}")
        logger.info(f"   Metrics: {metrics}")

        return version

    def _update_performance_trends(self, version: ModelVersion):
        """Actualizar tendencias de rendimiento con nueva versión."""
        for metric_name, metric_value in version.metrics.items():
            if metric_name not in self.performance_trends:
                self.performance_trends[metric_name] = PerformanceTrend(metric_name=metric_name)

            trend = self.performance_trends[metric_name]
            trend.values.append(metric_value)
            trend.timestamps.append(version.created_at)
            trend.last_updated = time.time()

            # Calcular tendencia (slope) usando regresión lineal simple
            if len(trend.values) >= 3:
                x = np.arange(len(trend.values))
                y = np.array(trend.values)
                trend.trend_slope = np.polyfit(x, y, 1)[0]

                # Calcular volatilidad (desviación estándar de cambios)
                if len(trend.values) >= 2:
                    changes = np.diff(y)
                    trend.volatility = np.std(changes) if len(changes) > 1 else 0.0

    def _analyze_version_evolution(self, new_version: ModelVersion):
        """Analizar evolución desde la versión anterior."""
        if not self.version_history or len(self.version_history) < 2:
            return

        # Obtener versión anterior
        prev_version_id = self.version_history[-2]
        prev_version = self.model_versions[prev_version_id]

        # Calcular cambios en métricas
        metrics_change = {}
        improvement_detected = False
        degradation_detected = False

        for metric in set(prev_version.metrics.keys()) | set(new_version.metrics.keys()):
            prev_value = prev_version.metrics.get(metric, 0.0)
            new_value = new_version.metrics.get(metric, 0.0)

            if prev_value != 0:
                change = (new_value - prev_value) / prev_value
            else:
                change = new_value

            metrics_change[metric] = change

            # Determinar si es mejora o degradación
            # Para accuracy y f1, mayor es mejor
            if metric in ["accuracy", "f1_score", "precision", "recall"]:
                if change > 0.01:  # Mejora > 1%
                    improvement_detected = True
                elif change < -self.alert_thresholds.get(f"{metric}_drop", 0.05):
                    degradation_detected = True
            # Para loss, menor es mejor
            elif metric in ["loss", "mse", "mae"]:
                if change < -0.01:  # Reducción > 1%
                    improvement_detected = True
                elif change > self.alert_thresholds.get("loss_increase", 0.1):
                    degradation_detected = True

        # Crear evento de evolución
        if improvement_detected:
            event_type = "improvement"
            impact_score = sum(abs(change) for change in metrics_change.values() if change > 0)
        elif degradation_detected:
            event_type = "degradation"
            impact_score = sum(abs(change) for change in metrics_change.values() if change < 0)
            self.evolution_stats["degradation_events"] += 1
        else:
            event_type = "adaptation"
            impact_score = sum(abs(change) for change in metrics_change.values())
            self.evolution_stats["adaptation_events"] += 1

        # Determinar razón del trigger
        trigger_reason = "continuous_learning"
        if new_version.domain_adaptations:
            trigger_reason = "domain_adaptation"
        elif new_version.curriculum_stage:
            trigger_reason = "curriculum_progression"
        elif new_version.privacy_budget_used > 0:
            trigger_reason = "privacy_preservation"

        event = EvolutionEvent(
            event_id=f"event_{int(time.time())}_{event_type}",
            event_type=event_type,
            version_from=prev_version_id,
            version_to=new_version.version_id,
            metrics_change=metrics_change,
            trigger_reason=trigger_reason,
            impact_score=impact_score,
            metadata={
                "training_round": new_version.training_round,
                "data_processed": new_version.data_processed,
                "training_time": new_version.training_time
            }
        )

        self.evolution_events.append(event)
        self.evolution_stats["total_events"] += 1

        logger.info(f"🔄 Evolution event: {event_type} ({impact_score:.3f} impact)")
        logger.info(f"   From {prev_version_id} to {new_version.version_id}")

    def assess_model_health(self) -> Dict[str, Any]:
        """
        Evaluar salud general del modelo.

        Returns:
            Estado de salud del modelo
        """
        if not self.model_versions:
            return {"health_score": 0.0, "status": "no_versions", "indicators": {}}

        # Actualizar indicadores de salud
        self._update_health_indicators()

        # Calcular score de salud general
        health_scores = []
        critical_indicators = 0

        for indicator in self.health_indicators.values():
            health_scores.append(indicator.current_value / indicator.threshold)

            if indicator.status == "critical":
                critical_indicators += 1

        overall_health = np.mean(health_scores) if health_scores else 0.0

        # Determinar estado general
        if critical_indicators > 0:
            status = "critical"
        elif overall_health < 0.6:
            status = "warning"
        else:
            status = "healthy"

        self.evolution_stats["health_score"] = overall_health

        health_assessment = {
            "health_score": overall_health,
            "status": status,
            "critical_indicators": critical_indicators,
            "indicators": {
                name: {
                    "value": ind.current_value,
                    "threshold": ind.threshold,
                    "status": ind.status,
                    "trend": ind.trend,
                    "recommendations": ind.recommendations
                }
                for name, ind in self.health_indicators.items()
            },
            "last_assessed": time.time()
        }

        logger.info(f"🏥 Model health assessment: {status} ({overall_health:.3f})")
        return health_assessment

    def _update_health_indicators(self):
        """Actualizar indicadores de salud basados en datos recientes."""
        if not self.performance_trends:
            return

        # Indicador de estabilidad de accuracy
        if "accuracy" in self.performance_trends:
            accuracy_trend = self.performance_trends["accuracy"]
            if len(accuracy_trend.values) >= 5:
                recent_stability = 1.0 - np.std(accuracy_trend.values[-5:])  # Menor varianza = más estable
                self._update_indicator("accuracy_stability", recent_stability)

        # Indicador de consistencia F1
        if "f1_score" in self.performance_trends:
            f1_trend = self.performance_trends["f1_score"]
            if len(f1_trend.values) >= 3:
                consistency = np.mean(f1_trend.values[-3:])
                self._update_indicator("f1_consistency", consistency)

        # Indicador de tendencia de loss
        if "loss" in self.performance_trends:
            loss_trend = self.performance_trends["loss"]
            if len(loss_trend.values) >= 3:
                # Invertir loss para que menor sea mejor (normalizar)
                loss_score = max(0, 1.0 - np.mean(loss_trend.values[-3:]))
                self._update_indicator("loss_trend", loss_score)

        # Indicador de éxito de adaptación
        adaptation_events = [e for e in self.evolution_events if e.event_type == "adaptation"]
        if adaptation_events:
            recent_adaptations = adaptation_events[-5:]
            success_rate = sum(1 for e in recent_adaptations if e.impact_score > 0.01) / len(recent_adaptations)
            self._update_indicator("adaptation_success", success_rate)

        # Indicador de preservación de privacidad
        total_privacy_budget = sum(v.privacy_budget_used for v in self.model_versions.values())
        privacy_efficiency = min(1.0, 1.0 / (1.0 + total_privacy_budget))  # Menor uso = mejor
        self._update_indicator("privacy_preservation", privacy_efficiency)

        # Indicador de generalización
        if len(self.model_versions) >= 3:
            # Medir variabilidad en rendimiento a través de versiones
            generalization_score = 1.0
            for trend in self.performance_trends.values():
                if len(trend.values) >= 3:
                    generalization_score *= (1.0 - trend.volatility)
            generalization_score = generalization_score ** (1.0 / len(self.performance_trends))
            self._update_indicator("generalization", generalization_score)

    def _update_indicator(self, indicator_name: str, new_value: float):
        """Actualizar un indicador de salud específico."""
        if indicator_name not in self.health_indicators:
            return

        indicator = self.health_indicators[indicator_name]
        old_value = indicator.current_value
        indicator.current_value = new_value
        indicator.last_assessed = time.time()

        # Determinar estado
        if new_value < indicator.threshold * 0.5:
            indicator.status = "critical"
        elif new_value < indicator.threshold:
            indicator.status = "warning"
        else:
            indicator.status = "healthy"

        # Determinar tendencia
        if new_value > old_value * 1.05:
            indicator.trend = "improving"
        elif new_value < old_value * 0.95:
            indicator.trend = "degrading"
        else:
            indicator.trend = "stable"

        # Generar recomendaciones
        indicator.recommendations = self._generate_indicator_recommendations(indicator)

    def _generate_indicator_recommendations(self, indicator: ModelHealthIndicator) -> List[str]:
        """Generar recomendaciones para un indicador."""
        recommendations = []

        if indicator.status == "critical":
            if "accuracy" in indicator.indicator_name:
                recommendations.extend(["immediate_retraining", "data_quality_check", "hyperparameter_tuning"])
            elif "loss" in indicator.indicator_name:
                recommendations.extend(["learning_rate_adjustment", "architecture_review", "regularization_increase"])
            elif "adaptation" in indicator.indicator_name:
                recommendations.extend(["domain_adaptation_review", "curriculum_reset"])
            else:
                recommendations.append("comprehensive_model_review")

        elif indicator.status == "warning":
            if indicator.trend == "degrading":
                recommendations.append("monitor_closely")
            elif indicator.trend == "improving":
                recommendations.append("continue_current_strategy")
            else:
                recommendations.append("investigate_stability")

        else:  # healthy
            recommendations.append("maintain_current_performance")

        return recommendations

    def get_evolution_summary(self, time_window_days: int = 30) -> Dict[str, Any]:
        """
        Obtener resumen de evolución en una ventana de tiempo.

        Args:
            time_window_days: Ventana de tiempo en días

        Returns:
            Resumen de evolución
        """
        cutoff_time = time.time() - (time_window_days * 24 * 3600)

        # Filtrar versiones y eventos recientes
        recent_versions = [
            v for v in self.model_versions.values()
            if v.created_at >= cutoff_time
        ]

        recent_events = [
            e for e in self.evolution_events
            if e.timestamp >= cutoff_time
        ]

        # Calcular estadísticas
        if recent_versions:
            latest_version = max(recent_versions, key=lambda v: v.created_at)
            earliest_version = min(recent_versions, key=lambda v: v.created_at)

            improvement_rate = 0.0
            if earliest_version.metrics and latest_version.metrics:
                for metric in set(earliest_version.metrics.keys()) & set(latest_version.metrics.keys()):
                    early_val = earliest_version.metrics[metric]
                    late_val = latest_version.metrics[metric]
                    if early_val != 0:
                        improvement_rate += (late_val - early_val) / early_val

                improvement_rate /= len(set(earliest_version.metrics.keys()) & set(latest_version.metrics.keys()))

            self.evolution_stats["avg_improvement_rate"] = improvement_rate

        summary = {
            "time_window_days": time_window_days,
            "versions_in_window": len(recent_versions),
            "events_in_window": len(recent_events),
            "improvement_events": len([e for e in recent_events if e.event_type == "improvement"]),
            "degradation_events": len([e for e in recent_events if e.event_type == "degradation"]),
            "adaptation_events": len([e for e in recent_events if e.event_type == "adaptation"]),
            "avg_improvement_rate": self.evolution_stats["avg_improvement_rate"],
            "current_health_score": self.evolution_stats["health_score"],
            "evolution_efficiency": len(recent_events) / max(1, len(recent_versions)),
            "latest_version": latest_version.version_id if recent_versions else None,
            "baseline_version": self.baseline_version
        }

        return summary

    def get_evolution_timeline(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Obtener línea de tiempo de evolución.

        Args:
            limit: Número máximo de eventos a retornar

        Returns:
            Eventos de evolución en orden cronológico
        """
        recent_events = sorted(self.evolution_events, key=lambda e: e.timestamp, reverse=True)[:limit]

        return [
            {
                "event_id": e.event_id,
                "event_type": e.event_type,
                "timestamp": e.timestamp,
                "version_from": e.version_from,
                "version_to": e.version_to,
                "impact_score": e.impact_score,
                "trigger_reason": e.trigger_reason,
                "metrics_change": e.metrics_change,
                "metadata": e.metadata
            }
            for e in recent_events
        ]

    def predict_future_performance(self, horizon_versions: int = 5) -> Dict[str, Any]:
        """
        Predecir rendimiento futuro basado en tendencias.

        Args:
            horizon_versions: Número de versiones a predecir

        Returns:
            Predicciones de rendimiento
        """
        predictions = {}

        for metric_name, trend in self.performance_trends.items():
            if len(trend.values) < 3:
                continue

            # Usar regresión lineal para predecir
            x = np.arange(len(trend.values))
            y = np.array(trend.values)

            # Ajustar línea de tendencia
            slope, intercept = np.polyfit(x, y, 1)

            # Predecir valores futuros
            future_x = np.arange(len(y), len(y) + horizon_versions)
            future_y = slope * future_x + intercept

            predictions[metric_name] = {
                "current_trend": slope,
                "predicted_values": future_y.tolist(),
                "confidence_interval": [slope * 0.8, slope * 1.2],  # Intervalo simple
                "prediction_horizon": horizon_versions
            }

        return {
            "predictions": predictions,
            "prediction_timestamp": time.time(),
            "based_on_versions": len(self.version_history)
        }

    def export_evolution_report(self, file_path: str) -> bool:
        """
        Exportar reporte completo de evolución.

        Args:
            file_path: Ruta del archivo para exportar

        Returns:
            True si se exportó correctamente
        """
        try:
            report = {
                "model_name": self.model_name,
                "session_id": self.session_id,
                "export_timestamp": time.time(),
                "evolution_stats": self.evolution_stats,
                "version_history": [
                    {
                        "version_id": vid,
                        "created_at": self.model_versions[vid].created_at,
                        "metrics": self.model_versions[vid].metrics,
                        "training_round": self.model_versions[vid].training_round
                    }
                    for vid in self.version_history
                ],
                "evolution_events": [
                    {
                        "event_id": e.event_id,
                        "event_type": e.event_type,
                        "timestamp": e.timestamp,
                        "impact_score": e.impact_score,
                        "trigger_reason": e.trigger_reason
                    }
                    for e in self.evolution_events
                ],
                "health_assessment": self.assess_model_health(),
                "performance_trends": {
                    name: {
                        "values": trend.values[-10:],  # Últimos 10 valores
                        "trend_slope": trend.trend_slope,
                        "volatility": trend.volatility
                    }
                    for name, trend in self.performance_trends.items()
                }
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"📄 Evolution report exported to {file_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Error exporting evolution report: {e}")
            return False


# Funciones de conveniencia
def create_evolution_tracker(model_name: str, session_id: str) -> ModelEvolutionTracker:
    """Crear un nuevo rastreador de evolución."""
    return ModelEvolutionTracker(model_name, session_id)


async def track_model_evolution(tracker: ModelEvolutionTracker,
                               version_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rastrear evolución del modelo de manera asíncrona.

    Args:
        tracker: Rastreador de evolución
        version_data: Datos de la nueva versión

    Returns:
        Resultados del rastreo
    """
    # Simular procesamiento asíncrono
    await asyncio.sleep(0.05)

    version = tracker.register_model_version(
        version_id=version_data["version_id"],
        model_cid=version_data["model_cid"],
        metrics=version_data["metrics"],
        metadata=version_data.get("metadata")
    )

    health = tracker.assess_model_health()

    return {
        "version_registered": version.version_id,
        "health_assessment": health,
        "evolution_events": len(tracker.evolution_events)
    }