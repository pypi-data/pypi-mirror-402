"""
FeedbackCollector - Recolección de feedback de usuarios y sistemas automáticos
=============================================================================

Este módulo proporciona funcionalidades para recopilar feedback de usuarios
y sistemas automáticos, asegurando la privacidad mediante anonimización
antes del almacenamiento.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from ..privacy.anonymization import AnonymizationService, AnonymizationConfig, AnonymizationRule, AnonymizationTechnique, PrivacyLevel

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Tipos de feedback disponibles."""
    USER_RATING = "user_rating"
    USER_COMMENT = "user_comment"
    SYSTEM_METRIC = "system_metric"
    ERROR_REPORT = "error_report"
    FEATURE_REQUEST = "feature_request"
    PERFORMANCE_FEEDBACK = "performance_feedback"


class FeedbackSource(Enum):
    """Fuentes de feedback."""
    USER_DIRECT = "user_direct"
    SYSTEM_AUTOMATIC = "system_automatic"
    API_RESPONSE = "api_response"
    MONITORING_SYSTEM = "monitoring_system"


@dataclass
class FeedbackEntry:
    """Entrada de feedback individual."""
    id: str
    type: FeedbackType
    source: FeedbackSource
    data: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    model_version: Optional[str] = None
    anonymized_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la entrada a diccionario."""
        return {
            "id": self.id,
            "type": self.type.value,
            "source": self.source.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "model_version": self.model_version,
            "anonymized_data": self.anonymized_data
        }


class FeedbackCollector:
    """
    Recolector de feedback que anonimiza datos sensibles antes del almacenamiento.

    Este servicio recopila feedback de diferentes fuentes, aplica anonimización
    para proteger la privacidad del usuario, y almacena los datos de manera segura.
    """

    def __init__(self, anonymization_config: Optional[AnonymizationConfig] = None):
        """
        Inicializa el recolector de feedback.

        Args:
            anonymization_config: Configuración de anonimización. Si no se proporciona,
                                 se usa configuración por defecto para feedback.
        """
        self.anonymization_service = AnonymizationService(anonymization_config or self._create_default_config())
        self.feedback_store: List[FeedbackEntry] = []
        self.feedback_count = 0

        logger.info("FeedbackCollector inicializado")

    def _create_default_config(self) -> AnonymizationConfig:
        """Crea configuración de anonimización por defecto para feedback."""
        config = AnonymizationConfig(
            default_technique=AnonymizationTechnique.HASHING,
            default_privacy_level=PrivacyLevel.HIGH,
            enable_audit_log=True
        )

        # Reglas específicas para campos comunes en feedback
        config.add_rule(AnonymizationRule(
            field_name="user_email",
            technique=AnonymizationTechnique.HASHING,
            privacy_level=PrivacyLevel.MAXIMUM
        ))
        config.add_rule(AnonymizationRule(
            field_name="user_name",
            technique=AnonymizationTechnique.GENERALIZATION,
            privacy_level=PrivacyLevel.HIGH
        ))
        config.add_rule(AnonymizationRule(
            field_name="ip_address",
            technique=AnonymizationTechnique.MASKING,
            privacy_level=PrivacyLevel.HIGH
        ))
        config.add_rule(AnonymizationRule(
            field_name="device_info",
            technique=AnonymizationTechnique.GENERALIZATION,
            privacy_level=PrivacyLevel.MEDIUM
        ))

        return config

    def collect_feedback(self, feedback_type: FeedbackType, source: FeedbackSource,
                        data: Dict[str, Any], user_id: Optional[int] = None,
                        session_id: Optional[str] = None, model_version: Optional[str] = None) -> str:
        """
        Recopila y procesa una entrada de feedback.

        Args:
            feedback_type: Tipo de feedback
            source: Fuente del feedback
            data: Datos del feedback
            user_id: ID del usuario (opcional)
            session_id: ID de sesión (opcional)
            model_version: Versión del modelo (opcional)

        Returns:
            ID único del feedback recopilado
        """
        try:
            # Generar ID único
            feedback_id = f"fb_{self.feedback_count}_{int(datetime.now().timestamp())}"
            self.feedback_count += 1

            # Anonimizar datos sensibles
            anonymized_data = self.anonymization_service.anonymize_data(data, user_id)

            # Crear entrada de feedback
            entry = FeedbackEntry(
                id=feedback_id,
                type=feedback_type,
                source=source,
                data=data,
                timestamp=datetime.now(),
                user_id=user_id,
                session_id=session_id,
                model_version=model_version,
                anonymized_data=anonymized_data
            )

            # Almacenar entrada
            self.feedback_store.append(entry)

            logger.info(f"Feedback recopilado: {feedback_id} (tipo: {feedback_type.value})")

            return feedback_id

        except Exception as e:
            logger.error(f"Error recopilando feedback: {e}")
            raise

    def collect_user_rating(self, rating: int, comment: Optional[str] = None,
                           user_id: Optional[int] = None, session_id: Optional[str] = None,
                           model_version: Optional[str] = None) -> str:
        """
        Recopila feedback de calificación de usuario.

        Args:
            rating: Calificación (1-5)
            comment: Comentario opcional
            user_id: ID del usuario
            session_id: ID de sesión
            model_version: Versión del modelo

        Returns:
            ID del feedback
        """
        data = {"rating": rating}
        if comment:
            data["comment"] = comment

        return self.collect_feedback(
            FeedbackType.USER_RATING,
            FeedbackSource.USER_DIRECT,
            data,
            user_id,
            session_id,
            model_version
        )

    def collect_system_metric(self, metric_name: str, value: Any,
                             context: Optional[Dict[str, Any]] = None,
                             model_version: Optional[str] = None) -> str:
        """
        Recopila métricas del sistema.

        Args:
            metric_name: Nombre de la métrica
            value: Valor de la métrica
            context: Contexto adicional
            model_version: Versión del modelo

        Returns:
            ID del feedback
        """
        data = {
            "metric_name": metric_name,
            "value": value
        }
        if context:
            data["context"] = context

        return self.collect_feedback(
            FeedbackType.SYSTEM_METRIC,
            FeedbackSource.SYSTEM_AUTOMATIC,
            data,
            model_version=model_version
        )

    def collect_error_report(self, error_type: str, error_message: str,
                            stack_trace: Optional[str] = None, user_id: Optional[int] = None,
                            session_id: Optional[str] = None, model_version: Optional[str] = None) -> str:
        """
        Recopila reportes de error.

        Args:
            error_type: Tipo de error
            error_message: Mensaje de error
            stack_trace: Traza de pila (opcional)
            user_id: ID del usuario
            session_id: ID de sesión
            model_version: Versión del modelo

        Returns:
            ID del feedback
        """
        data = {
            "error_type": error_type,
            "error_message": error_message
        }
        if stack_trace:
            data["stack_trace"] = stack_trace

        return self.collect_feedback(
            FeedbackType.ERROR_REPORT,
            FeedbackSource.SYSTEM_AUTOMATIC,
            data,
            user_id,
            session_id,
            model_version
        )

    def get_feedback_entries(self, limit: Optional[int] = None) -> List[FeedbackEntry]:
        """
        Obtiene entradas de feedback almacenadas.

        Args:
            limit: Número máximo de entradas a retornar

        Returns:
            Lista de entradas de feedback
        """
        entries = self.feedback_store
        if limit:
            entries = entries[-limit:]
        return entries.copy()

    def get_feedback_by_type(self, feedback_type: FeedbackType) -> List[FeedbackEntry]:
        """
        Obtiene feedback de un tipo específico.

        Args:
            feedback_type: Tipo de feedback

        Returns:
            Lista de entradas de ese tipo
        """
        return [entry for entry in self.feedback_store if entry.type == feedback_type]

    def get_anonymization_audit_log(self) -> List[Dict[str, Any]]:
        """
        Obtiene el log de auditoría de anonimización.

        Returns:
            Log de auditoría
        """
        return self.anonymization_service.get_audit_log()

    def clear_feedback_store(self) -> None:
        """Limpia el almacén de feedback (para testing)."""
        self.feedback_store.clear()
        self.feedback_count = 0
        logger.info("Almacén de feedback limpiado")