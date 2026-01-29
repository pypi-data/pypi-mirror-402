"""
Sistema de anonimización para analytics en AILOOS
================================================

Este módulo proporciona funcionalidades para anonimizar datos de usuario
antes de enviarlos a sistemas de analytics, conforme a regulaciones de
privacidad como GDPR. Incluye técnicas como hashing, generalización,
supresión y agregación, configurables por tipo de dato y nivel de privacidad.
"""

import hashlib
import json
import logging
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime, date
from dataclasses import dataclass, field
from enum import Enum
import re

logger = logging.getLogger(__name__)


class AnonymizationTechnique(Enum):
    """Técnicas de anonimización disponibles."""
    HASHING = "hashing"
    GENERALIZATION = "generalization"
    SUPPRESSION = "suppression"
    AGGREGATION = "aggregation"
    MASKING = "masking"


class PrivacyLevel(Enum):
    """Niveles de privacidad disponibles."""
    LOW = "low"        # Anonimización mínima
    MEDIUM = "medium"  # Anonimización moderada
    HIGH = "high"      # Anonimización fuerte
    MAXIMUM = "maximum"  # Anonimización máxima


@dataclass
class AnonymizationRule:
    """Regla de anonimización para un campo específico."""
    field_name: str
    technique: AnonymizationTechnique
    privacy_level: PrivacyLevel
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la regla a diccionario."""
        return {
            "field_name": self.field_name,
            "technique": self.technique.value,
            "privacy_level": self.privacy_level.value,
            "parameters": self.parameters
        }


@dataclass
class AnonymizationConfig:
    """Configuración de anonimización."""
    rules: List[AnonymizationRule] = field(default_factory=list)
    default_technique: AnonymizationTechnique = AnonymizationTechnique.HASHING
    default_privacy_level: PrivacyLevel = PrivacyLevel.MEDIUM
    salt: Optional[str] = None
    enable_audit_log: bool = True

    def add_rule(self, rule: AnonymizationRule) -> None:
        """Agrega una regla de anonimización."""
        self.rules.append(rule)

    def get_rule_for_field(self, field_name: str) -> Optional[AnonymizationRule]:
        """Obtiene la regla para un campo específico."""
        for rule in self.rules:
            if rule.field_name == field_name:
                return rule
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la configuración a diccionario."""
        return {
            "rules": [rule.to_dict() for rule in self.rules],
            "default_technique": self.default_technique.value,
            "default_privacy_level": self.default_privacy_level.value,
            "salt": self.salt,
            "enable_audit_log": self.enable_audit_log
        }


class AnonymizationService:
    """
    Servicio principal para anonimización de datos de usuario.

    Este servicio permite anonimizar datos personales antes de enviarlos
    a sistemas de analytics, utilizando diferentes técnicas configurables
    según el tipo de dato y el nivel de privacidad requerido.
    """

    def __init__(self, config: Optional[AnonymizationConfig] = None):
        """
        Inicializa el servicio de anonimización.

        Args:
            config: Configuración de anonimización. Si no se proporciona,
                   se usa configuración por defecto.
        """
        self.config = config or AnonymizationConfig()
        self.audit_log: List[Dict[str, Any]] = []

        logger.info("AnonymizationService inicializado")

    def anonymize_data(self, data: Dict[str, Any], user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Anonimiza un diccionario de datos según las reglas configuradas.

        Args:
            data: Datos a anonimizar
            user_id: ID del usuario (opcional, para auditoría)

        Returns:
            Datos anonimizados
        """
        anonymized_data = {}
        timestamp = datetime.now().isoformat()

        for field_name, value in data.items():
            rule = self.config.get_rule_for_field(field_name)
            if rule:
                anonymized_value = self._apply_technique(value, rule)
                anonymized_data[field_name] = anonymized_value

                if self.config.enable_audit_log:
                    self._log_anonymization(field_name, rule.technique, user_id, timestamp)
            else:
                # Aplicar regla por defecto si no hay regla específica
                default_rule = AnonymizationRule(
                    field_name=field_name,
                    technique=self.config.default_technique,
                    privacy_level=self.config.default_privacy_level
                )
                anonymized_value = self._apply_technique(value, default_rule)
                anonymized_data[field_name] = anonymized_value

                if self.config.enable_audit_log:
                    self._log_anonymization(field_name, default_rule.technique, user_id, timestamp)

        return anonymized_data

    def anonymize_batch(self, data_list: List[Dict[str, Any]], user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Anonimiza una lista de diccionarios de datos.

        Args:
            data_list: Lista de datos a anonimizar
            user_id: ID del usuario (opcional, para auditoría)

        Returns:
            Lista de datos anonimizados
        """
        return [self.anonymize_data(data, user_id) for data in data_list]

    def _apply_technique(self, value: Any, rule: AnonymizationRule) -> Any:
        """
        Aplica la técnica de anonimización especificada.

        Args:
            value: Valor a anonimizar
            rule: Regla de anonimización

        Returns:
            Valor anonimizado
        """
        try:
            if rule.technique == AnonymizationTechnique.HASHING:
                return self._apply_hashing(value, rule)
            elif rule.technique == AnonymizationTechnique.GENERALIZATION:
                return self._apply_generalization(value, rule)
            elif rule.technique == AnonymizationTechnique.SUPPRESSION:
                return self._apply_suppression(value, rule)
            elif rule.technique == AnonymizationTechnique.AGGREGATION:
                return self._apply_aggregation(value, rule)
            elif rule.technique == AnonymizationTechnique.MASKING:
                return self._apply_masking(value, rule)
            else:
                logger.warning(f"Técnica no soportada: {rule.technique}")
                return value
        except Exception as e:
            logger.error(f"Error aplicando técnica {rule.technique} a {rule.field_name}: {e}")
            return value

    def _apply_hashing(self, value: Any, rule: AnonymizationRule) -> str:
        """
        Aplica hashing al valor.

        Args:
            value: Valor a hashear
            rule: Regla de anonimización

        Returns:
            Hash del valor
        """
        if value is None:
            return ""

        # Convertir valor a string
        str_value = str(value)

        # Agregar salt si está configurado
        if self.config.salt:
            str_value = f"{self.config.salt}{str_value}"

        # Elegir algoritmo según nivel de privacidad
        if rule.privacy_level == PrivacyLevel.MAXIMUM:
            # Usar SHA-256 para máxima privacidad
            hash_obj = hashlib.sha256(str_value.encode('utf-8'))
        else:
            # Usar MD5 para compatibilidad (menos seguro pero más rápido)
            hash_obj = hashlib.md5(str_value.encode('utf-8'))

        return hash_obj.hexdigest()

    def _apply_generalization(self, value: Any, rule: AnonymizationRule) -> Any:
        """
        Aplica generalización al valor.

        Args:
            value: Valor a generalizar
            rule: Regla de anonimización

        Returns:
            Valor generalizado
        """
        if value is None:
            return None

        # Generalización por tipo de dato
        if isinstance(value, str):
            return self._generalize_string(value, rule)
        elif isinstance(value, (int, float)):
            return self._generalize_number(value, rule)
        elif isinstance(value, date):
            return self._generalize_date(value, rule)
        elif isinstance(value, datetime):
            return self._generalize_datetime(value, rule)
        else:
            return str(value)

    def _generalize_string(self, value: str, rule: AnonymizationRule) -> str:
        """Generaliza una cadena de texto."""
        privacy_level = rule.privacy_level

        if privacy_level == PrivacyLevel.LOW:
            # Mantener primeros 3 caracteres
            return value[:3] + "*" * (len(value) - 3) if len(value) > 3 else value
        elif privacy_level == PrivacyLevel.MEDIUM:
            # Mantener solo primer caracter
            return value[0] + "*" * (len(value) - 1) if len(value) > 1 else value
        elif privacy_level == PrivacyLevel.HIGH:
            # Reemplazar con categoría genérica
            length = len(value)
            if length <= 5:
                return "SHORT"
            elif length <= 10:
                return "MEDIUM"
            else:
                return "LONG"
        else:  # MAXIMUM
            return "ANONYMIZED"

    def _generalize_number(self, value: Union[int, float], rule: AnonymizationRule) -> Union[int, str]:
        """Generaliza un número."""
        privacy_level = rule.privacy_level

        if privacy_level == PrivacyLevel.LOW:
            # Redondear a decenas
            return round(value / 10) * 10
        elif privacy_level == PrivacyLevel.MEDIUM:
            # Redondear a centenas
            return round(value / 100) * 100
        elif privacy_level == PrivacyLevel.HIGH:
            # Categorizar en rangos
            if value < 10:
                return "SMALL"
            elif value < 100:
                return "MEDIUM"
            elif value < 1000:
                return "LARGE"
            else:
                return "VERY_LARGE"
        else:  # MAXIMUM
            return "ANONYMIZED"

    def _generalize_date(self, value: date, rule: AnonymizationRule) -> str:
        """Generaliza una fecha."""
        privacy_level = rule.privacy_level

        if privacy_level == PrivacyLevel.LOW:
            # Ocultar día
            return value.strftime("%Y-%m-**")
        elif privacy_level == PrivacyLevel.MEDIUM:
            # Ocultar día y mes
            return value.strftime("%Y-**-**")
        elif privacy_level == PrivacyLevel.HIGH:
            # Solo año
            return str(value.year)
        else:  # MAXIMUM
            return "ANONYMIZED"

    def _generalize_datetime(self, value: datetime, rule: AnonymizationRule) -> str:
        """Generaliza una fecha y hora."""
        privacy_level = rule.privacy_level

        if privacy_level == PrivacyLevel.LOW:
            # Ocultar minutos y segundos
            return value.strftime("%Y-%m-%d %H:00:00")
        elif privacy_level == PrivacyLevel.MEDIUM:
            # Ocultar hora, minutos y segundos
            return value.strftime("%Y-%m-%d 00:00:00")
        elif privacy_level == PrivacyLevel.HIGH:
            # Solo fecha
            return value.strftime("%Y-%m-%d")
        else:  # MAXIMUM
            return "ANONYMIZED"

    def _apply_suppression(self, value: Any, rule: AnonymizationRule) -> Any:
        """
        Aplica supresión al valor.

        Args:
            value: Valor a suprimir
            rule: Regla de anonimización

        Returns:
            Valor suprimido (None o valor por defecto)
        """
        # La supresión siempre retorna None o un valor por defecto
        default_value = rule.parameters.get('default_value', None)
        return default_value

    def _apply_aggregation(self, value: Any, rule: AnonymizationRule) -> Any:
        """
        Aplica agregación al valor.

        Nota: La agregación requiere contexto de múltiples valores.
        Este método es un placeholder para agregación simple.

        Args:
            value: Valor a agregar
            rule: Regla de anonimización

        Returns:
            Valor agregado (en este caso, mantiene el valor original
            ya que la agregación real requiere múltiples valores)
        """
        # Para agregación real, se necesitaría implementar lógica
        # específica según el contexto (ej: promedio, suma, etc.)
        logger.warning("Agregación aplicada a valor individual - considere usar anonymize_batch para mejor resultado")
        return value

    def _apply_masking(self, value: Any, rule: AnonymizationRule) -> str:
        """
        Aplica enmascaramiento al valor.

        Args:
            value: Valor a enmascarar
            rule: Regla de anonimización

        Returns:
            Valor enmascarado
        """
        if value is None:
            return ""

        str_value = str(value)
        privacy_level = rule.privacy_level

        if privacy_level == PrivacyLevel.LOW:
            # Mostrar primeros y últimos caracteres
            if len(str_value) <= 4:
                return str_value
            return str_value[:2] + "*" * (len(str_value) - 4) + str_value[-2:]
        elif privacy_level == PrivacyLevel.MEDIUM:
            # Mostrar solo primeros y últimos caracteres
            if len(str_value) <= 2:
                return str_value
            return str_value[0] + "*" * (len(str_value) - 2) + str_value[-1]
        elif privacy_level == PrivacyLevel.HIGH:
            # Solo asteriscos
            return "*" * len(str_value)
        else:  # MAXIMUM
            return "ANONYMIZED"

    def _log_anonymization(self, field_name: str, technique: AnonymizationTechnique,
                          user_id: Optional[int], timestamp: str) -> None:
        """
        Registra una operación de anonimización en el log de auditoría.

        Args:
            field_name: Nombre del campo anonimizado
            technique: Técnica utilizada
            user_id: ID del usuario
            timestamp: Timestamp de la operación
        """
        log_entry = {
            "timestamp": timestamp,
            "field_name": field_name,
            "technique": technique.value,
            "user_id": user_id
        }
        self.audit_log.append(log_entry)

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """
        Obtiene el log de auditoría de operaciones de anonimización.

        Returns:
            Lista de entradas del log de auditoría
        """
        return self.audit_log.copy()

    def clear_audit_log(self) -> None:
        """Limpia el log de auditoría."""
        self.audit_log.clear()

    def create_config_from_dict(self, config_dict: Dict[str, Any]) -> AnonymizationConfig:
        """
        Crea una configuración desde un diccionario.

        Args:
            config_dict: Diccionario con configuración

        Returns:
            Configuración de anonimización
        """
        config = AnonymizationConfig(
            default_technique=AnonymizationTechnique(config_dict.get('default_technique', 'hashing')),
            default_privacy_level=PrivacyLevel(config_dict.get('default_privacy_level', 'medium')),
            salt=config_dict.get('salt'),
            enable_audit_log=config_dict.get('enable_audit_log', True)
        )

        for rule_dict in config_dict.get('rules', []):
            rule = AnonymizationRule(
                field_name=rule_dict['field_name'],
                technique=AnonymizationTechnique(rule_dict['technique']),
                privacy_level=PrivacyLevel(rule_dict['privacy_level']),
                parameters=rule_dict.get('parameters', {})
            )
            config.add_rule(rule)

        return config

    def validate_config(self, config: AnonymizationConfig) -> List[str]:
        """
        Valida una configuración de anonimización.

        Args:
            config: Configuración a validar

        Returns:
            Lista de errores de validación
        """
        errors = []

        if not config.rules and config.default_technique is None:
            errors.append("Debe especificar reglas o una técnica por defecto")

        for rule in config.rules:
            if not rule.field_name:
                errors.append("Todas las reglas deben tener un nombre de campo")
            if rule.technique not in AnonymizationTechnique:
                errors.append(f"Técnica no válida: {rule.technique}")
            if rule.privacy_level not in PrivacyLevel:
                errors.append(f"Nivel de privacidad no válido: {rule.privacy_level}")

        return errors