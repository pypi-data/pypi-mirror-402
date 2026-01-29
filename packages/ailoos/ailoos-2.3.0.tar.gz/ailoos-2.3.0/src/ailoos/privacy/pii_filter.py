"""
PII Detection and Filtering for RAG Systems
============================================

Este módulo proporciona funcionalidades para detectar y filtrar información personal
identificable (PII) en texto, específicamente diseñado para sistemas RAG/CAG.
Incluye detección de patrones comunes de PII y técnicas de anonimización.

Características:
- Detección de emails, teléfonos, direcciones, números de identificación
- Anonimización configurable por tipo de PII
- Integración con pipelines de preprocesamiento RAG
- Logging de auditoría para compliance
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple, Pattern, Callable
from dataclasses import dataclass, field
from enum import Enum
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)


class PIICategory(Enum):
    """Categorías de información personal identificable."""
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    SSN = "ssn"  # Social Security Number
    CREDIT_CARD = "credit_card"
    NAME = "name"
    DATE_OF_BIRTH = "date_of_birth"
    IP_ADDRESS = "ip_address"
    LICENSE_PLATE = "license_plate"
    PASSPORT = "passport"
    TAX_ID = "tax_id"


class PIIAction(Enum):
    """Acciones a tomar cuando se detecta PII."""
    ANONYMIZE = "anonymize"  # Reemplazar con placeholder
    REMOVE = "remove"        # Eliminar completamente
    MASK = "mask"           # Enmascarar parcialmente
    ALLOW = "allow"         # Permitir sin cambios


@dataclass
class PIIPattern:
    """Patrón para detectar un tipo específico de PII."""
    category: PIICategory
    regex: Pattern[str]
    action: PIIAction = PIIAction.ANONYMIZE
    replacement: str = "[REDACTED]"
    description: str = ""


@dataclass
class PIIFilterConfig:
    """Configuración del filtro de PII."""
    patterns: List[PIIPattern] = field(default_factory=list)
    enable_audit_log: bool = True
    salt: Optional[str] = None
    case_sensitive: bool = False

    def add_pattern(self, pattern: PIIPattern) -> None:
        """Agrega un patrón de PII."""
        self.patterns.append(pattern)

    def get_patterns_for_category(self, category: PIICategory) -> List[PIIPattern]:
        """Obtiene patrones para una categoría específica."""
        return [p for p in self.patterns if p.category == category]


class PIIDetector:
    """
    Detector de información personal identificable en texto.

    Utiliza expresiones regulares y reglas heurísticas para identificar
    diferentes tipos de PII en texto plano.
    """

    def __init__(self, config: Optional[PIIFilterConfig] = None):
        """
        Inicializa el detector de PII.

        Args:
            config: Configuración del detector. Si no se proporciona,
                   se usa configuración por defecto.
        """
        self.config = config or self._create_default_config()
        self.audit_log: List[Dict[str, Any]] = []

    def _create_default_config(self) -> PIIFilterConfig:
        """Crea configuración por defecto con patrones comunes."""
        config = PIIFilterConfig()

        # Patrón para emails
        email_pattern = PIIPattern(
            category=PIICategory.EMAIL,
            regex=re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            action=PIIAction.ANONYMIZE,
            replacement="[EMAIL]",
            description="Direcciones de correo electrónico"
        )
        config.add_pattern(email_pattern)

        # Patrón para teléfonos (formato internacional y local)
        phone_pattern = PIIPattern(
            category=PIICategory.PHONE,
            regex=re.compile(r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'),
            action=PIIAction.MASK,
            replacement="[PHONE]",
            description="Números de teléfono"
        )
        config.add_pattern(phone_pattern)

        # Patrón para direcciones IP
        ip_pattern = PIIPattern(
            category=PIICategory.IP_ADDRESS,
            regex=re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
            action=PIIAction.ANONYMIZE,
            replacement="[IP]",
            description="Direcciones IP"
        )
        config.add_pattern(ip_pattern)

        # Patrón para números de seguridad social (EEUU)
        ssn_pattern = PIIPattern(
            category=PIICategory.SSN,
            regex=re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            action=PIIAction.MASK,
            replacement="XXX-XX-XXXX",
            description="Números de Seguridad Social"
        )
        config.add_pattern(ssn_pattern)

        # Patrón para tarjetas de crédito (patrón básico)
        cc_pattern = PIIPattern(
            category=PIICategory.CREDIT_CARD,
            regex=re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
            action=PIIAction.MASK,
            replacement="XXXX-XXXX-XXXX-XXXX",
            description="Números de tarjetas de crédito"
        )
        config.add_pattern(cc_pattern)

        # Patrón para fechas de nacimiento (formato común)
        dob_pattern = PIIPattern(
            category=PIICategory.DATE_OF_BIRTH,
            regex=re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'),
            action=PIIAction.ANONYMIZE,
            replacement="[DOB]",
            description="Fechas de nacimiento"
        )
        config.add_pattern(dob_pattern)

        return config

    def detect_pii(self, text: str) -> List[Dict[str, Any]]:
        """
        Detecta PII en el texto proporcionado.

        Args:
            text: Texto a analizar

        Returns:
            Lista de detecciones con información detallada
        """
        detections = []

        for pattern in self.config.patterns:
            matches = pattern.regex.findall(text)
            if matches:
                for match in matches:
                    detection = {
                        "category": pattern.category.value,
                        "value": match,
                        "action": pattern.action.value,
                        "replacement": pattern.replacement,
                        "description": pattern.description,
                        "start_pos": text.find(match),
                        "end_pos": text.find(match) + len(match)
                    }
                    detections.append(detection)

        return detections

    def filter_pii(self, text: str, user_id: Optional[int] = None) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Filtra PII del texto según la configuración.

        Args:
            text: Texto a filtrar
            user_id: ID del usuario para auditoría

        Returns:
            Tupla de (texto_filtrado, lista_de_cambios)
        """
        filtered_text = text
        changes = []
        timestamp = datetime.now().isoformat()

        detections = self.detect_pii(text)

        # Procesar detecciones en orden inverso para mantener posiciones
        for detection in sorted(detections, key=lambda x: x['start_pos'], reverse=True):
            original_value = detection['value']
            action = PIIAction(detection['action'])
            replacement = detection['replacement']

            if action == PIIAction.ANONYMIZE:
                # Aplicar anonimización con hash si hay salt
                if self.config.salt:
                    hashed = hashlib.sha256(f"{self.config.salt}{original_value}".encode()).hexdigest()[:8]
                    replacement = f"[{detection['category'].upper()}-{hashed}]"
                filtered_text = filtered_text[:detection['start_pos']] + replacement + filtered_text[detection['end_pos']:]

            elif action == PIIAction.REMOVE:
                filtered_text = filtered_text[:detection['start_pos']] + filtered_text[detection['end_pos']:]

            elif action == PIIAction.MASK:
                # Enmascarar parcialmente
                masked = self._mask_value(original_value, detection['category'])
                filtered_text = filtered_text[:detection['start_pos']] + masked + filtered_text[detection['end_pos']:]

            elif action == PIIAction.ALLOW:
                continue  # No hacer cambios

            # Registrar cambio para auditoría
            change_record = {
                "timestamp": timestamp,
                "user_id": user_id,
                "category": detection['category'],
                "original_value": original_value,
                "action": action.value,
                "replacement": replacement if action != PIIAction.REMOVE else "[REMOVED]"
            }
            changes.append(change_record)

            if self.config.enable_audit_log:
                self.audit_log.append(change_record)

        return filtered_text, changes

    def _mask_value(self, value: str, category: str) -> str:
        """Enmascara parcialmente un valor según su categoría."""
        if category == PIICategory.PHONE.value:
            # Mantener primeros 3 dígitos y enmascarar el resto
            if len(value) >= 10:
                return value[:3] + "-" + "*" * 3 + "-" + "*" * 4
        elif category == PIICategory.CREDIT_CARD.value:
            # Mantener primeros 4 y últimos 4 dígitos
            digits = re.sub(r'\D', '', value)
            if len(digits) >= 8:
                return digits[:4] + "-" + "*" * (len(digits) - 8) + "-" + digits[-4:]
        elif category == PIICategory.SSN.value:
            return "XXX-XX-" + value[-4:] if len(value) >= 9 else "*" * len(value)

        # Enmascaramiento por defecto: mostrar primeros y últimos caracteres
        if len(value) <= 4:
            return "*" * len(value)
        return value[0] + "*" * (len(value) - 2) + value[-1]

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Obtiene el log de auditoría."""
        return self.audit_log.copy()

    def clear_audit_log(self) -> None:
        """Limpia el log de auditoría."""
        self.audit_log.clear()


class PIIFilterService:
    """
    Servicio completo para filtrado de PII en pipelines RAG.

    Combina detección, filtrado y auditoría para asegurar compliance
    en sistemas de recuperación aumentada por generación.
    """

    def __init__(self, config: Optional[PIIFilterConfig] = None):
        """
        Inicializa el servicio de filtrado PII.

        Args:
            config: Configuración del servicio
        """
        self.detector = PIIDetector(config)
        self.config = config or self.detector.config
        logger.info("PIIFilterService inicializado")

    def preprocess_query(self, query: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Preprocesa una query para RAG, filtrando PII.

        Args:
            query: Query original del usuario
            user_id: ID del usuario

        Returns:
            Diccionario con query procesada y metadata
        """
        filtered_query, changes = self.detector.filter_pii(query, user_id)

        result = {
            "original_query": query,
            "filtered_query": filtered_query,
            "pii_detected": len(changes) > 0,
            "pii_changes": changes,
            "processing_timestamp": datetime.now().isoformat()
        }

        if changes:
            logger.warning(f"PII detectada y filtrada en query de usuario {user_id}: {len(changes)} elementos")

        return result

    def preprocess_documents(self, documents: List[Dict[str, Any]],
                           user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Preprocesa documentos para indexing en RAG, filtrando PII.

        Args:
            documents: Lista de documentos con contenido
            user_id: ID del usuario

        Returns:
            Documentos procesados
        """
        processed_docs = []

        for doc in documents:
            content = doc.get('content', '')
            filtered_content, changes = self.detector.filter_pii(content, user_id)

            processed_doc = doc.copy()
            processed_doc['original_content'] = content
            processed_doc['filtered_content'] = filtered_content
            processed_doc['pii_filtered'] = len(changes) > 0
            processed_doc['pii_changes'] = changes
            processed_doc['processing_timestamp'] = datetime.now().isoformat()

            processed_docs.append(processed_doc)

        return processed_docs

    def validate_compliance(self, text: str) -> Dict[str, Any]:
        """
        Valida si un texto cumple con políticas de PII.

        Args:
            text: Texto a validar

        Returns:
            Resultado de validación con detalles
        """
        detections = self.detector.detect_pii(text)

        result = {
            "compliant": len(detections) == 0,
            "pii_detections": detections,
            "risk_level": self._calculate_risk_level(detections),
            "recommendations": self._generate_recommendations(detections)
        }

        return result

    def _calculate_risk_level(self, detections: List[Dict[str, Any]]) -> str:
        """Calcula el nivel de riesgo basado en detecciones."""
        if not detections:
            return "LOW"

        high_risk_categories = {PIICategory.SSN.value, PIICategory.CREDIT_CARD.value,
                              PIICategory.PASSPORT.value, PIICategory.TAX_ID.value}

        has_high_risk = any(d['category'] in high_risk_categories for d in detections)

        if has_high_risk or len(detections) > 5:
            return "HIGH"
        elif len(detections) > 2:
            return "MEDIUM"
        else:
            return "LOW"

    def _generate_recommendations(self, detections: List[Dict[str, Any]]) -> List[str]:
        """Genera recomendaciones basadas en detecciones."""
        recommendations = []

        if not detections:
            return ["Texto cumple con políticas de privacidad"]

        categories = set(d['category'] for d in detections)

        if PIICategory.EMAIL.value in categories:
            recommendations.append("Considerar anonimización de emails antes de procesamiento")

        if PIICategory.PHONE.value in categories:
            recommendations.append("Revisar política de retención de números telefónicos")

        if PIICategory.SSN.value in categories or PIICategory.CREDIT_CARD.value in categories:
            recommendations.append("ALERTA: Información financiera sensible detectada - revisión inmediata requerida")

        return recommendations