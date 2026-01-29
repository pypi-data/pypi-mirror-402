"""
FeedbackAnalyzer - Análisis inteligente de feedback para identificar patrones
===========================================================================

Este módulo proporciona funcionalidades para analizar feedback recopilado,
identificando patrones, tendencias y insights que pueden usarse para
mejorar el modelo y el sistema.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass
import re

from .feedback_collector import FeedbackEntry, FeedbackType

logger = logging.getLogger(__name__)


@dataclass
class FeedbackInsight:
    """Insight generado del análisis de feedback."""
    category: str
    title: str
    description: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    confidence: float  # 0.0 to 1.0
    data: Dict[str, Any]
    timestamp: datetime
    recommendations: List[str] = None

    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el insight a diccionario."""
        return {
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "confidence": self.confidence,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "recommendations": self.recommendations
        }


@dataclass
class FeedbackStats:
    """Estadísticas agregadas del feedback."""
    total_entries: int
    entries_by_type: Dict[str, int]
    entries_by_source: Dict[str, int]
    average_rating: Optional[float]
    rating_distribution: Dict[int, int]
    error_types: Dict[str, int]
    time_range: Tuple[datetime, datetime]
    model_versions: List[str]


class FeedbackAnalyzer:
    """
    Analizador inteligente de feedback que identifica patrones y tendencias.

    Este servicio procesa feedback recopilado para generar insights
    accionables que pueden mejorar el rendimiento del modelo.
    """

    def __init__(self):
        """Inicializa el analizador de feedback."""
        self.insights: List[FeedbackInsight] = []
        logger.info("FeedbackAnalyzer inicializado")

    def analyze_feedback(self, feedback_entries: List[FeedbackEntry]) -> List[FeedbackInsight]:
        """
        Analiza una lista de entradas de feedback y genera insights.

        Args:
            feedback_entries: Lista de entradas de feedback

        Returns:
            Lista de insights generados
        """
        if not feedback_entries:
            logger.warning("No hay entradas de feedback para analizar")
            return []

        # Calcular estadísticas básicas
        stats = self._calculate_basic_stats(feedback_entries)

        insights = []

        # Análisis de ratings
        rating_insights = self._analyze_ratings(feedback_entries, stats)
        insights.extend(rating_insights)

        # Análisis de errores
        error_insights = self._analyze_errors(feedback_entries, stats)
        insights.extend(error_insights)

        # Análisis de comentarios
        comment_insights = self._analyze_comments(feedback_entries)
        insights.extend(comment_insights)

        # Análisis de métricas del sistema
        metric_insights = self._analyze_system_metrics(feedback_entries)
        insights.extend(metric_insights)

        # Análisis temporal
        temporal_insights = self._analyze_temporal_patterns(feedback_entries, stats)
        insights.extend(temporal_insights)

        # Análisis por versión del modelo
        version_insights = self._analyze_model_versions(feedback_entries, stats)
        insights.extend(version_insights)

        self.insights.extend(insights)

        logger.info(f"Generados {len(insights)} insights del análisis de {len(feedback_entries)} entradas")

        return insights

    def _calculate_basic_stats(self, entries: List[FeedbackEntry]) -> FeedbackStats:
        """Calcula estadísticas básicas del feedback."""
        if not entries:
            return FeedbackStats(0, {}, {}, None, {}, {}, (datetime.now(), datetime.now()), [])

        # Conteos por tipo y fuente
        types_count = Counter(entry.type.value for entry in entries)
        sources_count = Counter(entry.source.value for entry in entries)

        # Ratings
        ratings = [entry.data.get('rating') for entry in entries
                  if entry.type.value == 'user_rating' and 'rating' in entry.data]
        avg_rating = sum(ratings) / len(ratings) if ratings else None
        rating_dist = Counter(ratings)

        # Errores
        errors = [entry.data.get('error_type') for entry in entries
                 if entry.type.value == 'error_report' and 'error_type' in entry.data]
        error_types = Counter(errors)

        # Rango temporal
        timestamps = [entry.timestamp for entry in entries]
        time_range = (min(timestamps), max(timestamps)) if timestamps else (datetime.now(), datetime.now())

        # Versiones del modelo
        versions = list(set(entry.model_version for entry in entries if entry.model_version))

        return FeedbackStats(
            total_entries=len(entries),
            entries_by_type=dict(types_count),
            entries_by_source=dict(sources_count),
            average_rating=avg_rating,
            rating_distribution=dict(rating_dist),
            error_types=dict(error_types),
            time_range=time_range,
            model_versions=versions
        )

    def _analyze_ratings(self, entries: List[FeedbackEntry], stats: FeedbackStats) -> List[FeedbackInsight]:
        """Analiza ratings de usuarios."""
        insights = []

        if stats.average_rating is None:
            return insights

        avg_rating = stats.average_rating

        # Insight sobre rating promedio
        if avg_rating < 2.0:
            severity = 'critical'
            title = "Rating promedio muy bajo"
            desc = f"El rating promedio es {avg_rating:.1f}, indicando problemas serios de calidad."
            confidence = 0.9
        elif avg_rating < 3.0:
            severity = 'high'
            title = "Rating promedio bajo"
            desc = f"El rating promedio es {avg_rating:.1f}, requiere atención inmediata."
            confidence = 0.8
        elif avg_rating < 4.0:
            severity = 'medium'
            title = "Rating promedio aceptable"
            desc = f"El rating promedio es {avg_rating:.1f}, hay margen de mejora."
            confidence = 0.7
        else:
            severity = 'low'
            title = "Rating promedio bueno"
            desc = f"El rating promedio es {avg_rating:.1f}, el rendimiento es satisfactorio."
            confidence = 0.8

        insights.append(FeedbackInsight(
            category="ratings",
            title=title,
            description=desc,
            severity=severity,
            confidence=confidence,
            data={"average_rating": avg_rating, "total_ratings": len(stats.rating_distribution)},
            timestamp=datetime.now(),
            recommendations=self._generate_rating_recommendations(avg_rating)
        ))

        # Análisis de distribución de ratings
        low_ratings = sum(count for rating, count in stats.rating_distribution.items() if rating <= 2)
        if low_ratings > len(entries) * 0.3:  # Más del 30% son ratings bajos
            insights.append(FeedbackInsight(
                category="ratings",
                title="Alta proporción de ratings bajos",
                description=f"{low_ratings} ratings bajos detectados, representa un {low_ratings/len(entries)*100:.1f}% del total.",
                severity='high',
                confidence=0.85,
                data={"low_ratings": low_ratings, "total_ratings": len(stats.rating_distribution)},
                timestamp=datetime.now(),
                recommendations=["Investigar causas de insatisfacción", "Revisar casos de uso problemáticos"]
            ))

        return insights

    def _generate_rating_recommendations(self, avg_rating: float) -> List[str]:
        """Genera recomendaciones basadas en el rating promedio."""
        if avg_rating < 2.0:
            return [
                "Realizar auditoría completa del modelo",
                "Revisar datos de entrenamiento",
                "Implementar mejoras urgentes en calidad de respuesta",
                "Considerar rollback a versión anterior"
            ]
        elif avg_rating < 3.0:
            return [
                "Analizar patrones de feedback negativo",
                "Mejorar precisión de respuestas",
                "Aumentar cobertura de casos de uso",
                "Implementar validación adicional de respuestas"
            ]
        elif avg_rating < 4.0:
            return [
                "Optimizar rendimiento y velocidad",
                "Mejorar experiencia de usuario",
                "Expandir capacidades del modelo"
            ]
        else:
            return [
                "Mantener estándares de calidad",
                "Continuar monitoreo de métricas",
                "Explorar nuevas funcionalidades"
            ]

    def _analyze_errors(self, entries: List[FeedbackEntry], stats: FeedbackStats) -> List[FeedbackInsight]:
        """Analiza reportes de error."""
        insights = []

        if not stats.error_types:
            return insights

        total_errors = sum(stats.error_types.values())
        most_common_error = max(stats.error_types.items(), key=lambda x: x[1])

        # Insight sobre errores más comunes
        if most_common_error[1] > total_errors * 0.5:  # Más del 50% de los errores
            insights.append(FeedbackInsight(
                category="errors",
                title=f"Error predominante: {most_common_error[0]}",
                description=f"El error '{most_common_error[0]}' representa el {most_common_error[1]/total_errors*100:.1f}% de todos los errores reportados.",
                severity='high',
                confidence=0.9,
                data={"error_type": most_common_error[0], "count": most_common_error[1], "total_errors": total_errors},
                timestamp=datetime.now(),
                recommendations=[f"Priorizar fix para error '{most_common_error[0]}'", "Implementar logging adicional", "Agregar validaciones preventivas"]
            ))

        # Insight sobre frecuencia de errores
        error_rate = total_errors / stats.total_entries if stats.total_entries > 0 else 0
        if error_rate > 0.1:  # Más del 10% son errores
            insights.append(FeedbackInsight(
                category="errors",
                title="Alta tasa de errores",
                description=f"Tasa de error del {error_rate*100:.1f}%, indica problemas de estabilidad.",
                severity='critical' if error_rate > 0.2 else 'high',
                confidence=0.85,
                data={"error_rate": error_rate, "total_errors": total_errors, "total_entries": stats.total_entries},
                timestamp=datetime.now(),
                recommendations=["Implementar circuit breakers", "Mejorar manejo de excepciones", "Aumentar testing de integración"]
            ))

        return insights

    def _analyze_comments(self, entries: List[FeedbackEntry]) -> List[FeedbackInsight]:
        """Analiza comentarios de usuarios."""
        insights = []

        comments = []
        for entry in entries:
            if entry.type.value == 'user_comment' and 'comment' in entry.data:
                comments.append(entry.data['comment'])
            elif entry.type.value == 'user_rating' and 'comment' in entry.data:
                comments.append(entry.data['comment'])

        if not comments:
            return insights

        # Análisis simple de sentimientos (basado en palabras clave)
        positive_words = ['bueno', 'excelente', 'genial', 'perfecto', 'ayuda', 'útil', 'correcto', 'preciso']
        negative_words = ['malo', 'terrible', 'error', 'incorrecto', 'confuso', 'lento', 'problema', 'falla']

        positive_count = 0
        negative_count = 0

        for comment in comments:
            comment_lower = comment.lower()
            pos_matches = sum(1 for word in positive_words if word in comment_lower)
            neg_matches = sum(1 for word in negative_words if word in comment_lower)
            positive_count += pos_matches
            negative_count += neg_matches

        total_sentiment_words = positive_count + negative_count

        if total_sentiment_words > 0:
            sentiment_ratio = positive_count / total_sentiment_words

            if sentiment_ratio < 0.3:
                sentiment = "muy negativo"
                severity = 'high'
            elif sentiment_ratio < 0.5:
                sentiment = "negativo"
                severity = 'medium'
            elif sentiment_ratio > 0.7:
                sentiment = "positivo"
                severity = 'low'
            else:
                sentiment = "neutral"
                severity = 'low'

            insights.append(FeedbackInsight(
                category="comments",
                title=f"Análisis de sentimiento: {sentiment}",
                description=f"De {len(comments)} comentarios analizados, el sentimiento es {sentiment} (ratio: {sentiment_ratio:.2f}).",
                severity=severity,
                confidence=0.7,
                data={"positive_words": positive_count, "negative_words": negative_count, "total_comments": len(comments)},
                timestamp=datetime.now(),
                recommendations=["Revisar comentarios negativos para identificar patrones", "Implementar mejoras basadas en feedback positivo"]
            ))

        return insights

    def _analyze_system_metrics(self, entries: List[FeedbackEntry]) -> List[FeedbackInsight]:
        """Analiza métricas del sistema."""
        insights = []

        metrics = defaultdict(list)
        for entry in entries:
            if entry.type.value == 'system_metric':
                metric_name = entry.data.get('metric_name')
                value = entry.data.get('value')
                if metric_name and value is not None:
                    metrics[metric_name].append(value)

        for metric_name, values in metrics.items():
            if not values:
                continue

            # Análisis básico de métricas
            avg_value = sum(values) / len(values)
            min_value = min(values)
            max_value = max(values)

            # Detección de anomalías (valores extremos)
            threshold = avg_value * 1.5  # Umbral simple
            anomalies = [v for v in values if v > threshold]

            if anomalies:
                insights.append(FeedbackInsight(
                    category="metrics",
                    title=f"Anomalías detectadas en métrica: {metric_name}",
                    description=f"Se detectaron {len(anomalies)} valores anómalos en la métrica '{metric_name}' (promedio: {avg_value:.2f}).",
                    severity='medium',
                    confidence=0.75,
                    data={"metric_name": metric_name, "average": avg_value, "anomalies": len(anomalies), "total_values": len(values)},
                    timestamp=datetime.now(),
                    recommendations=["Investigar causas de anomalías", "Implementar monitoreo avanzado", "Ajustar thresholds de alerta"]
                ))

        return insights

    def _analyze_temporal_patterns(self, entries: List[FeedbackEntry], stats: FeedbackStats) -> List[FeedbackInsight]:
        """Analiza patrones temporales en el feedback."""
        insights = []

        if stats.total_entries < 10:  # Necesitamos datos suficientes
            return insights

        # Agrupar por día
        daily_counts = defaultdict(int)
        for entry in entries:
            day = entry.timestamp.date()
            daily_counts[day] += 1

        # Detectar picos de feedback
        avg_daily = sum(daily_counts.values()) / len(daily_counts)
        peak_days = [day for day, count in daily_counts.items() if count > avg_daily * 2]

        if peak_days:
            insights.append(FeedbackInsight(
                category="temporal",
                title="Picos de feedback detectados",
                description=f"Se detectaron picos de feedback en {len(peak_days)} días, con promedio diario de {avg_daily:.1f} entradas.",
                severity='medium',
                confidence=0.8,
                data={"peak_days": [str(d) for d in peak_days], "avg_daily": avg_daily},
                timestamp=datetime.now(),
                recommendations=["Analizar eventos que causaron picos", "Preparar capacidad adicional para picos similares"]
            ))

        return insights

    def _analyze_model_versions(self, entries: List[FeedbackEntry], stats: FeedbackStats) -> List[FeedbackInsight]:
        """Analiza feedback por versión del modelo."""
        insights = []

        if len(stats.model_versions) < 2:
            return insights

        version_ratings = defaultdict(list)
        version_errors = defaultdict(int)

        for entry in entries:
            version = entry.model_version
            if not version:
                continue

            if entry.type.value == 'user_rating' and 'rating' in entry.data:
                version_ratings[version].append(entry.data['rating'])
            elif entry.type.value == 'error_report':
                version_errors[version] += 1

        # Comparar ratings entre versiones
        if len(version_ratings) > 1:
            version_avgs = {v: sum(ratings)/len(ratings) for v, ratings in version_ratings.items() if ratings}

            if version_avgs:
                best_version = max(version_avgs.items(), key=lambda x: x[1])
                worst_version = min(version_avgs.items(), key=lambda x: x[1])

                if best_version[1] - worst_version[1] > 0.5:  # Diferencia significativa
                    insights.append(FeedbackInsight(
                        category="versions",
                        title="Diferencias significativas entre versiones",
                        description=f"La versión {best_version[0]} tiene mejor rating ({best_version[1]:.1f}) que {worst_version[0]} ({worst_version[1]:.1f}).",
                        severity='medium',
                        confidence=0.8,
                        data={"version_ratings": version_avgs},
                        timestamp=datetime.now(),
                        recommendations=[f"Analizar qué hace mejor a la versión {best_version[0]}", f"Corregir problemas en versión {worst_version[0]}"]
                    ))

        return insights

    def get_insights(self, category: Optional[str] = None, min_severity: Optional[str] = None) -> List[FeedbackInsight]:
        """
        Obtiene insights generados, opcionalmente filtrados.

        Args:
            category: Filtrar por categoría
            min_severity: Filtrar por severidad mínima

        Returns:
            Lista de insights
        """
        insights = self.insights

        if category:
            insights = [i for i in insights if i.category == category]

        if min_severity:
            severity_order = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
            min_level = severity_order.get(min_severity, 0)
            insights = [i for i in insights if severity_order.get(i.severity, 0) >= min_level]

        return insights.copy()

    def clear_insights(self) -> None:
        """Limpia los insights almacenados."""
        self.insights.clear()
        logger.info("Insights limpiados")