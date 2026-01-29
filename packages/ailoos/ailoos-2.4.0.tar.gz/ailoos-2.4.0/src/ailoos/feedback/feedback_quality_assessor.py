"""
FeedbackQualityAssessor - Evaluación de calidad del feedback recibido
====================================================================

Este módulo proporciona funcionalidades para evaluar la calidad,
confiabilidad y utilidad del feedback recopilado, permitiendo
filtrar y ponderar feedback de manera inteligente.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import re

from .feedback_collector import FeedbackEntry, FeedbackType, FeedbackSource

logger = logging.getLogger(__name__)


class FeedbackQuality(Enum):
    """Niveles de calidad del feedback."""
    EXCELLENT = "excellent"    # Calidad excepcional
    GOOD = "good"             # Buena calidad
    FAIR = "fair"             # Calidad aceptable
    POOR = "poor"             # Calidad baja
    UNRELIABLE = "unreliable" # No confiable


@dataclass
class QualityAssessment:
    """Evaluación de calidad de un feedback."""
    feedback_id: str
    overall_quality: FeedbackQuality
    quality_score: float  # 0.0 - 1.0
    confidence: float     # 0.0 - 1.0
    assessment_timestamp: datetime

    # Componentes de la evaluación
    content_quality: float
    user_reliability: float
    timeliness: float
    consistency: float

    # Razones de la evaluación
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Metadatos
    assessment_method: str = "automated"
    flags: List[str] = field(default_factory=list)  # 'spam', 'inconsistent', 'outdated', etc.

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la evaluación a diccionario."""
        return {
            "feedback_id": self.feedback_id,
            "overall_quality": self.overall_quality.value,
            "quality_score": self.quality_score,
            "confidence": self.confidence,
            "assessment_timestamp": self.assessment_timestamp.isoformat(),
            "content_quality": self.content_quality,
            "user_reliability": self.user_reliability,
            "timeliness": self.timeliness,
            "consistency": self.consistency,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "recommendations": self.recommendations,
            "assessment_method": self.assessment_method,
            "flags": self.flags
        }


class FeedbackQualityAssessor:
    """
    Evaluador de calidad del feedback.

    Analiza diferentes aspectos del feedback para determinar su calidad,
    confiabilidad y utilidad para el proceso de mejora del modelo.
    """

    def __init__(self):
        """Inicializa el evaluador de calidad."""
        self.assessments: Dict[str, QualityAssessment] = {}
        self.user_reliability_scores: Dict[int, float] = {}
        self.quality_thresholds = {
            'excellent': 0.9,
            'good': 0.7,
            'fair': 0.5,
            'poor': 0.3
        }

        # Configuración
        self.enable_user_history_analysis = True
        self.max_assessment_age_days = 30
        self.spam_detection_enabled = True

        logger.info("FeedbackQualityAssessor inicializado")

    def assess_feedback_quality(self, feedback_entry: FeedbackEntry,
                               user_history: Optional[List[FeedbackEntry]] = None) -> QualityAssessment:
        """
        Evalúa la calidad de una entrada de feedback.

        Args:
            feedback_entry: Entrada de feedback a evaluar
            user_history: Historial de feedback del usuario (opcional)

        Returns:
            Evaluación de calidad
        """
        feedback_id = feedback_entry.id

        # Evaluar componentes individuales
        content_quality = self._assess_content_quality(feedback_entry)
        user_reliability = self._assess_user_reliability(feedback_entry, user_history)
        timeliness = self._assess_timeliness(feedback_entry)
        consistency = self._assess_consistency(feedback_entry, user_history)

        # Calcular puntuación general
        weights = {
            'content_quality': 0.4,
            'user_reliability': 0.3,
            'timeliness': 0.15,
            'consistency': 0.15
        }

        overall_score = (
            content_quality * weights['content_quality'] +
            user_reliability * weights['user_reliability'] +
            timeliness * weights['timeliness'] +
            consistency * weights['consistency']
        )

        # Determinar calidad general
        overall_quality = self._score_to_quality(overall_score)

        # Calcular confianza en la evaluación
        confidence = self._calculate_assessment_confidence(feedback_entry, user_history)

        # Generar razones y recomendaciones
        strengths, weaknesses, recommendations, flags = self._generate_assessment_details(
            feedback_entry, content_quality, user_reliability, timeliness, consistency
        )

        assessment = QualityAssessment(
            feedback_id=feedback_id,
            overall_quality=overall_quality,
            quality_score=overall_score,
            confidence=confidence,
            assessment_timestamp=datetime.now(),
            content_quality=content_quality,
            user_reliability=user_reliability,
            timeliness=timeliness,
            consistency=consistency,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            flags=flags
        )

        # Almacenar evaluación
        self.assessments[feedback_id] = assessment

        # Actualizar puntuación de confiabilidad del usuario
        if feedback_entry.user_id:
            self._update_user_reliability(feedback_entry.user_id, overall_score, confidence)

        logger.info(f"Evaluación completada para feedback {feedback_id}: {overall_quality.value} ({overall_score:.2f})")

        return assessment

    def _assess_content_quality(self, feedback_entry: FeedbackEntry) -> float:
        """
        Evalúa la calidad del contenido del feedback.

        Args:
            feedback_entry: Entrada de feedback

        Returns:
            Puntuación de calidad del contenido (0.0 - 1.0)
        """
        score = 0.5  # Base neutral
        data = feedback_entry.data

        if feedback_entry.type == FeedbackType.USER_RATING:
            # Para ratings
            rating = data.get('rating')
            comment = data.get('comment', '')

            if rating is not None:
                # Ratings extremos son más informativos
                if rating in [1, 5]:
                    score += 0.2
                elif rating in [2, 4]:
                    score += 0.1

            # Comentarios detallados mejoran la calidad
            if len(comment) > 20:
                score += 0.2
            elif len(comment) > 10:
                score += 0.1

            # Comentarios constructivos
            constructive_keywords = ['mejorar', 'sugerencia', 'problema', 'ayudaría', 'podría']
            if any(word in comment.lower() for word in constructive_keywords):
                score += 0.1

        elif feedback_entry.type == FeedbackType.USER_COMMENT:
            comment = data.get('comment', '')

            # Longitud del comentario
            if len(comment) > 100:
                score += 0.3
            elif len(comment) > 50:
                score += 0.2
            elif len(comment) > 20:
                score += 0.1

            # Contenido específico vs genérico
            specific_indicators = ['específicamente', 'particularmente', 'concretamente', 'ejemplo']
            if any(word in comment.lower() for word in specific_indicators):
                score += 0.2

            # Evitar comentarios spam
            if self.spam_detection_enabled and self._is_spam_comment(comment):
                score -= 0.5

        elif feedback_entry.type == FeedbackType.ERROR_REPORT:
            error_type = data.get('error_type', '')
            error_message = data.get('error_message', '')

            # Errores con detalles técnicos son más valiosos
            if len(error_message) > 50:
                score += 0.3

            # Tipos de error específicos
            valuable_errors = ['timeout', 'parsing', 'validation', 'connection']
            if any(err in error_type.lower() for err in valuable_errors):
                score += 0.2

        elif feedback_entry.type == FeedbackType.SYSTEM_METRIC:
            # Métricas del sistema generalmente son confiables
            score = 0.9

        # Penalizar contenido vacío o muy corto
        if feedback_entry.type != FeedbackType.SYSTEM_METRIC:
            content_length = len(str(data))
            if content_length < 5:
                score -= 0.3

        return max(0.0, min(1.0, score))

    def _assess_user_reliability(self, feedback_entry: FeedbackEntry,
                                user_history: Optional[List[FeedbackEntry]] = None) -> float:
        """
        Evalúa la confiabilidad del usuario basada en su historial.

        Args:
            feedback_entry: Entrada de feedback
            user_history: Historial del usuario

        Returns:
            Puntuación de confiabilidad del usuario (0.0 - 1.0)
        """
        user_id = feedback_entry.user_id

        if not user_id:
            # Feedback anónimo tiene menor confiabilidad
            return 0.5

        # Usar puntuación histórica si existe
        if user_id in self.user_reliability_scores:
            return self.user_reliability_scores[user_id]

        if not user_history or not self.enable_user_history_analysis:
            return 0.6  # Default para usuarios sin historial

        # Analizar historial del usuario
        total_feedback = len(user_history)
        if total_feedback == 0:
            return 0.6

        # Calcular consistencia en tipos de feedback
        feedback_types = [entry.type for entry in user_history]
        most_common_type = max(set(feedback_types), key=feedback_types.count)
        type_consistency = feedback_types.count(most_common_type) / total_feedback

        # Calcular frecuencia de feedback (usuarios activos son más confiables)
        if total_feedback > 10:
            reliability = 0.8
        elif total_feedback > 5:
            reliability = 0.7
        elif total_feedback > 2:
            reliability = 0.6
        else:
            reliability = 0.5

        # Bonus por consistencia
        reliability += type_consistency * 0.1

        # Penalizar por feedback muy frecuente (posible spam)
        time_span_days = 30  # Analizar último mes
        recent_feedback = [entry for entry in user_history
                          if (datetime.now() - entry.timestamp).days <= time_span_days]

        if recent_feedback:
            avg_daily = len(recent_feedback) / time_span_days
            if avg_daily > 5:  # Más de 5 feedback por día
                reliability -= 0.2

        return max(0.0, min(1.0, reliability))

    def _assess_timeliness(self, feedback_entry: FeedbackEntry) -> float:
        """
        Evalúa la actualidad del feedback.

        Args:
            feedback_entry: Entrada de feedback

        Returns:
            Puntuación de actualidad (0.0 - 1.0)
        """
        age_hours = (datetime.now() - feedback_entry.timestamp).total_seconds() / 3600

        if age_hours < 1:  # Menos de 1 hora
            return 1.0
        elif age_hours < 24:  # Menos de 1 día
            return 0.9
        elif age_hours < 168:  # Menos de 1 semana
            return 0.7
        elif age_hours < 720:  # Menos de 1 mes
            return 0.5
        else:  # Más de 1 mes
            return 0.2

    def _assess_consistency(self, feedback_entry: FeedbackEntry,
                           user_history: Optional[List[FeedbackEntry]] = None) -> float:
        """
        Evalúa la consistencia del feedback con el historial del usuario.

        Args:
            feedback_entry: Entrada de feedback
            user_history: Historial del usuario

        Returns:
            Puntuación de consistencia (0.0 - 1.0)
        """
        if not user_history or len(user_history) < 2:
            return 0.7  # No hay suficiente historial para evaluar consistencia

        user_id = feedback_entry.user_id
        if not user_id:
            return 0.6

        # Para ratings, verificar consistencia en patrones
        if feedback_entry.type == FeedbackType.USER_RATING:
            current_rating = feedback_entry.data.get('rating')
            if current_rating is None:
                return 0.5

            # Obtener ratings previos del usuario
            previous_ratings = []
            for entry in user_history:
                if entry.type == FeedbackType.USER_RATING and entry.id != feedback_entry.id:
                    rating = entry.data.get('rating')
                    if rating is not None:
                        previous_ratings.append(rating)

            if not previous_ratings:
                return 0.7

            # Calcular varianza en ratings
            avg_previous = sum(previous_ratings) / len(previous_ratings)
            variance = sum((r - avg_previous) ** 2 for r in previous_ratings) / len(previous_ratings)

            # Baja varianza = alta consistencia
            if variance < 1:  # Ratings muy consistentes
                consistency = 0.9
            elif variance < 4:  # Moderadamente consistentes
                consistency = 0.7
            else:  # Inconsistentes
                consistency = 0.4

            # Penalizar cambios extremos
            rating_diff = abs(current_rating - avg_previous)
            if rating_diff >= 3:  # Cambio de 3+ puntos
                consistency -= 0.2

            return max(0.0, min(1.0, consistency))

        # Para otros tipos de feedback, consistencia básica
        return 0.7

    def _score_to_quality(self, score: float) -> FeedbackQuality:
        """
        Convierte una puntuación numérica a nivel de calidad.

        Args:
            score: Puntuación (0.0 - 1.0)

        Returns:
            Nivel de calidad
        """
        if score >= self.quality_thresholds['excellent']:
            return FeedbackQuality.EXCELLENT
        elif score >= self.quality_thresholds['good']:
            return FeedbackQuality.GOOD
        elif score >= self.quality_thresholds['fair']:
            return FeedbackQuality.FAIR
        elif score >= self.quality_thresholds['poor']:
            return FeedbackQuality.POOR
        else:
            return FeedbackQuality.UNRELIABLE

    def _calculate_assessment_confidence(self, feedback_entry: FeedbackEntry,
                                       user_history: Optional[List[FeedbackEntry]] = None) -> float:
        """
        Calcula la confianza en la evaluación realizada.

        Args:
            feedback_entry: Entrada de feedback
            user_history: Historial del usuario

        Returns:
            Nivel de confianza (0.0 - 1.0)
        """
        confidence = 0.7  # Base

        # Más confianza con historial del usuario
        if user_history and len(user_history) > 5:
            confidence += 0.1

        # Más confianza en feedback específico vs genérico
        if feedback_entry.type in [FeedbackType.ERROR_REPORT, FeedbackType.SYSTEM_METRIC]:
            confidence += 0.1

        # Menos confianza en feedback anónimo
        if not feedback_entry.user_id:
            confidence -= 0.2

        # Menos confianza en feedback muy antiguo
        age_days = (datetime.now() - feedback_entry.timestamp).days
        if age_days > 7:
            confidence -= 0.1

        return max(0.0, min(1.0, confidence))

    def _generate_assessment_details(self, feedback_entry: FeedbackEntry,
                                   content_quality: float, user_reliability: float,
                                   timeliness: float, consistency: float) -> Tuple[List[str], List[str], List[str], List[str]]:
        """
        Genera detalles de la evaluación: fortalezas, debilidades, recomendaciones y flags.

        Returns:
            Tuple de (strengths, weaknesses, recommendations, flags)
        """
        strengths = []
        weaknesses = []
        recommendations = []
        flags = []

        # Evaluar contenido
        if content_quality > 0.8:
            strengths.append("Contenido detallado y específico")
        elif content_quality < 0.4:
            weaknesses.append("Contenido pobre o genérico")
            recommendations.append("Proporcionar más detalles específicos")

        # Evaluar usuario
        if user_reliability > 0.8:
            strengths.append("Usuario altamente confiable")
        elif user_reliability < 0.5:
            weaknesses.append("Usuario con baja confiabilidad")
            flags.append("low_reliability_user")

        # Evaluar actualidad
        if timeliness > 0.8:
            strengths.append("Feedback muy reciente")
        elif timeliness < 0.5:
            weaknesses.append("Feedback desactualizado")
            flags.append("outdated")

        # Evaluar consistencia
        if consistency > 0.8:
            strengths.append("Consistente con historial del usuario")
        elif consistency < 0.5:
            weaknesses.append("Inconsistente con comportamiento previo")
            flags.append("inconsistent")

        # Detección de spam
        if self._is_spam_comment(str(feedback_entry.data)):
            flags.append("spam")
            weaknesses.append("Posible contenido spam")
            recommendations.append("Verificar autenticidad del feedback")

        # Recomendaciones generales
        if len(strengths) == 0:
            recommendations.append("Considerar feedback similar de otros usuarios para validación")

        return strengths, weaknesses, recommendations, flags

    def _is_spam_comment(self, content: str) -> bool:
        """
        Detecta si un comentario parece spam.

        Args:
            content: Contenido a evaluar

        Returns:
            True si parece spam
        """
        if not content or len(content) < 3:
            return False

        content_lower = content.lower()

        # Patrones de spam comunes
        spam_patterns = [
            r'\b(?:viagra|casino|lottery|winner)\b',  # Productos/promociones
            r'(?:http|www\.|\.com|\.net|\.org)',     # URLs
            r'\b(?:buy|sell|cheap|free|win)\b.*\b(?:now|today|urgent)\b',  # Lenguaje de ventas
            r'[a-zA-Z]{20,}',  # Palabras muy largas (posible ofuscación)
            r'(.)\1{4,}',      # Caracteres repetidos
        ]

        for pattern in spam_patterns:
            if re.search(pattern, content_lower):
                return True

        # Comentarios muy cortos con mayúsculas excesivas
        if len(content) < 10 and content.isupper():
            return True

        return False

    def _update_user_reliability(self, user_id: int, feedback_quality: float, assessment_confidence: float):
        """
        Actualiza la puntuación de confiabilidad de un usuario.

        Args:
            user_id: ID del usuario
            feedback_quality: Calidad del feedback reciente
            assessment_confidence: Confianza en la evaluación
        """
        current_score = self.user_reliability_scores.get(user_id, 0.6)

        # Ponderar actualización por confianza
        weight = assessment_confidence
        new_score = current_score * (1 - weight) + feedback_quality * weight

        self.user_reliability_scores[user_id] = max(0.0, min(1.0, new_score))

    def get_quality_assessment(self, feedback_id: str) -> Optional[QualityAssessment]:
        """
        Obtiene la evaluación de calidad de un feedback específico.

        Args:
            feedback_id: ID del feedback

        Returns:
            Evaluación de calidad o None si no existe
        """
        return self.assessments.get(feedback_id)

    def get_feedback_by_quality(self, min_quality: FeedbackQuality = FeedbackQuality.FAIR,
                               max_items: Optional[int] = None) -> List[Tuple[FeedbackEntry, QualityAssessment]]:
        """
        Obtiene feedback filtrado por calidad mínima.

        Args:
            min_quality: Calidad mínima requerida
            max_items: Número máximo de items a retornar

        Returns:
            Lista de tuplas (feedback_entry, assessment)
        """
        # Este método requeriría acceso al FeedbackCollector
        # En una implementación real, se pasaría como parámetro o se integraría
        logger.warning("get_feedback_by_quality requiere integración con FeedbackCollector")
        return []

    def get_quality_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de calidad del feedback evaluado.

        Returns:
            Estadísticas de calidad
        """
        if not self.assessments:
            return {"total_assessed": 0}

        total_assessed = len(self.assessments)
        quality_counts = {}

        for assessment in self.assessments.values():
            quality = assessment.overall_quality.value
            quality_counts[quality] = quality_counts.get(quality, 0) + 1

        avg_score = sum(a.quality_score for a in self.assessments.values()) / total_assessed
        avg_confidence = sum(a.confidence for a in self.assessments.values()) / total_assessed

        # Calcular distribución porcentual
        quality_distribution = {}
        for quality, count in quality_counts.items():
            quality_distribution[quality] = count / total_assessed

        return {
            "total_assessed": total_assessed,
            "quality_distribution": quality_distribution,
            "average_score": avg_score,
            "average_confidence": avg_confidence,
            "quality_counts": quality_counts
        }

    def get_user_reliability_leaderboard(self, top_n: int = 10) -> List[Tuple[int, float]]:
        """
        Obtiene el ranking de usuarios más confiables.

        Args:
            top_n: Número de usuarios a retornar

        Returns:
            Lista de tuplas (user_id, reliability_score)
        """
        sorted_users = sorted(
            self.user_reliability_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_users[:top_n]

    def cleanup_old_assessments(self, max_age_days: int = 90):
        """
        Limpia evaluaciones antiguas.

        Args:
            max_age_days: Edad máxima en días para mantener evaluaciones
        """
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        old_assessments = []

        for feedback_id, assessment in self.assessments.items():
            if assessment.assessment_timestamp < cutoff_date:
                old_assessments.append(feedback_id)

        for feedback_id in old_assessments:
            del self.assessments[feedback_id]

        if old_assessments:
            logger.info(f"Limpiadas {len(old_assessments)} evaluaciones antiguas")

    def export_quality_report(self, filename: str = "feedback_quality_report.json"):
        """
        Exporta un reporte completo de calidad del feedback.

        Args:
            filename: Nombre del archivo
        """
        try:
            report = {
                "generated_at": datetime.now().isoformat(),
                "quality_stats": self.get_quality_stats(),
                "user_reliability_ranking": self.get_user_reliability_leaderboard(20),
                "assessments": [assessment.to_dict() for assessment in self.assessments.values()]
            }

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            logger.info(f"Reporte de calidad exportado a {filename}")

        except Exception as e:
            logger.error(f"Error exportando reporte de calidad: {e}")