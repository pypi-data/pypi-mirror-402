#!/usr/bin/env python3
"""
AILOOS PII Scrubber - Motor de Sanitización GDPR/CCPA
======================================================

Este módulo es el corazón de la privacidad en AILOOS. Detecta y elimina
información personal identificable (PII) de los datasets antes de que
entren en el sistema de entrenamiento federado.

Características principales:
- Detección automática de PII usando expresiones regulares avanzadas
- Reemplazo inteligente con marcadores estandarizados
- Validación de cumplimiento GDPR/CCPA
- Estadísticas detalladas de sanitización
- Soporte para múltiples idiomas y formatos

Patrones detectados:
- Emails: user@domain.com
- Teléfonos: +34 666 123 456, 555-123-4567
- DNI/NIE: 12345678Z, X1234567L
- Tarjetas: 4111-1111-1111-1111
- IPs: 192.168.1.100
- URLs personales: facebook.com/user
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

class PIICategory:
    """Categorías de información personal identificable."""
    EMAIL = "email"
    PHONE = "phone"
    DNI_SPANISH = "dni_spanish"
    NIE_SPANISH = "nie_spanish"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    SSN_US = "ssn_us"
    URL_PERSONAL = "url_personal"
    NAME_PERSON = "name_person"
    ADDRESS = "address"

class PIIAction:
    """Acciones disponibles para el tratamiento de PII."""
    REDACT = "redact"      # Reemplazar con marcador
    HASH = "hash"          # Reemplazar con hash SHA256
    REMOVE = "remove"      # Eliminar completamente
    MASK = "mask"          # Enmascarar parcialmente

class PIIScrubber:
    """
    Motor de sanitización PII avanzado.
    Detecta y trata información personal identificable.
    """

    def __init__(self):
        """Inicializa el scrubber con patrones predefinidos."""
        self.patterns = self._load_default_patterns()
        self.stats = {
            "total_processed": 0,
            "pii_found": 0,
            "patterns_matched": {},
            "detection_rate": 0.0,
            "last_processed": None
        }

    def _load_default_patterns(self) -> Dict[str, Dict]:
        """Carga los patrones de detección PII por defecto."""

        return {
            PIICategory.EMAIL: {
                "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                "action": PIIAction.REDACT,
                "marker": "[EMAIL_REDACTED]",
                "description": "Direcciones de correo electrónico"
            },

            PIICategory.PHONE: {
                "pattern": r'\+\d{1,3}[\s.-]?\d{3}[\s.-]?\d{3}[\s.-]?\d{3,4}|\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b',
                "action": PIIAction.REDACT,
                "marker": "[PHONE_REDACTED]",
                "description": "Números de teléfono internacionales y estadounidenses"
            },

            PIICategory.DNI_SPANISH: {
                "pattern": r'\b\d{8}[A-HJ-NP-TV-Z]\b',
                "action": PIIAction.HASH,
                "marker": "SHA256:",
                "description": "DNI español (8 dígitos + letra)"
            },

            PIICategory.NIE_SPANISH: {
                "pattern": r'\b[X-Z]\d{7}[A-Z]\b',
                "action": PIIAction.HASH,
                "marker": "SHA256:",
                "description": "NIE español (letra + 7 dígitos + letra)"
            },

            PIICategory.CREDIT_CARD: {
                "pattern": r'\b\d{4}[\s.-]?\d{4}[\s.-]?\d{4}[\s.-]?\d{4}\b',
                "action": PIIAction.REDACT,
                "marker": "[CREDIT_CARD_REDACTED]",
                "description": "Números de tarjeta de crédito"
            },

            PIICategory.IP_ADDRESS: {
                "pattern": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
                "action": PIIAction.REDACT,
                "marker": "[IP_REDACTED]",
                "description": "Direcciones IP"
            },

            PIICategory.SSN_US: {
                "pattern": r'\b\d{3}-\d{2}-\d{4}\b',
                "action": PIIAction.MASK,
                "marker": "XXX-XX-",
                "description": "Número de Seguridad Social (SSN) estadounidense"
            },

            PIICategory.URL_PERSONAL: {
                "pattern": r'\b(?:facebook|twitter|instagram|linkedin)\.com/[A-Za-z0-9._-]+\b',
                "action": PIIAction.REDACT,
                "marker": "[SOCIAL_URL_REDACTED]",
                "description": "URLs de redes sociales personales"
            }
        }

    def add_pattern(self, category: str, pattern: str, action: str = PIIAction.REDACT,
                   marker: str = "[REDACTED]", description: str = ""):
        """
        Añade un patrón personalizado de detección PII.

        Args:
            category: Nombre de la categoría
            pattern: Expresión regular
            action: Acción a realizar
            marker: Marcador de reemplazo
            description: Descripción del patrón
        """
        self.patterns[category] = {
            "pattern": pattern,
            "action": action,
            "marker": marker,
            "description": description
        }
        logger.info(f"✅ Patrón personalizado añadido: {category}")

    def scrub_text(self, text: str, user_id: Optional[str] = None) -> str:
        """
        Sanitiza texto eliminando información PII.

        Args:
            text: Texto a sanitizar
            user_id: ID del usuario (para logging)

        Returns:
            Texto sanitizado
        """
        if not text:
            return text

        original_text = text
        pii_changes = []

        for category, config in self.patterns.items():
            pattern = config["pattern"]
            action = config["action"]
            marker = config["marker"]

            def replace_match(match):
                original = match.group(0)
                pii_changes.append({
                    "category": category,
                    "original": original,
                    "action": action
                })

                if action == PIIAction.REDACT:
                    return marker
                elif action == PIIAction.HASH:
                    hash_value = hashlib.sha256(original.encode()).hexdigest()
                    return f"{marker}{hash_value}"
                elif action == PIIAction.MASK:
                    # Para SSN: XXX-XX-XXXX
                    if category == PIICategory.SSN_US:
                        return f"XXX-XX-{original[-4:]}"
                    else:
                        return marker
                elif action == PIIAction.REMOVE:
                    return ""
                else:
                    return marker

            # Aplicar el patrón
            text = re.sub(pattern, replace_match, text, flags=re.IGNORECASE)

        # Actualizar estadísticas
        self.stats["total_processed"] += 1
        pii_count = len(pii_changes)
        self.stats["pii_found"] += pii_count

        if pii_count > 0:
            for change in pii_changes:
                cat = change["category"]
                self.stats["patterns_matched"][cat] = self.stats["patterns_matched"].get(cat, 0) + 1

        self.stats["detection_rate"] = (self.stats["pii_found"] / max(self.stats["total_processed"], 1))
        self.stats["last_processed"] = {
            "user_id": user_id,
            "original_length": len(original_text),
            "scrubbed_length": len(text),
            "pii_removed": pii_count
        }

        if pii_count > 0:
            logger.info(f"🧹 Texto sanitizado: {pii_count} instancias PII removidas")

        return text

    def scrub_dataset(self, dataset: List[Dict]) -> List[Dict]:
        """
        Sanitiza un dataset completo (lista de registros).

        Args:
            dataset: Lista de diccionarios con datos

        Returns:
            Dataset sanitizado
        """
        if not dataset:
            return dataset

        sanitized = []

        for record in dataset:
            if isinstance(record, dict):
                sanitized_record = {}
                for key, value in record.items():
                    if isinstance(value, str):
                        sanitized_record[key] = self.scrub_text(value)
                    else:
                        sanitized_record[key] = value
                sanitized.append(sanitized_record)
            else:
                # Si no es un dict, intentar sanitizar como string
                if isinstance(record, str):
                    sanitized.append(self.scrub_text(record))
                else:
                    sanitized.append(record)

        logger.info(f"🧹 Dataset sanitizado: {len(dataset)} registros procesados")
        return sanitized

    def validate_gdpr_compliance(self, text: str) -> Dict:
        """
        Valida el cumplimiento GDPR de un texto.

        Args:
            text: Texto a validar

        Returns:
            Dict con resultado de validación
        """
        pii_found = []
        issues_found = []

        for category, config in self.patterns.items():
            pattern = config["pattern"]
            matches = re.findall(pattern, text, re.IGNORECASE)

            if matches:
                pii_found.extend(matches)
                issues_found.append({
                    "type": category,
                    "description": config["description"],
                    "count": len(matches),
                    "examples": matches[:3]  # Primeros 3 ejemplos
                })

        compliant = len(pii_found) == 0

        result = {
            "gdpr_compliant": compliant,
            "pii_instances": len(pii_found),
            "issues_found": issues_found,
            "recommendations": []
        }

        if not compliant:
            result["recommendations"] = [
                "Ejecutar scrub_text() antes de procesar datos",
                "Considerar hash de campos sensibles en lugar de eliminación",
                "Implementar consentimiento explícito del usuario",
                "Documentar política de retención de datos"
            ]

        return result

    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas del scrubber.

        Returns:
            Dict con estadísticas de uso
        """
        return self.stats.copy()

    def reset_stats(self):
        """Reinicia las estadísticas del scrubber."""
        self.stats = {
            "total_processed": 0,
            "pii_found": 0,
            "patterns_matched": {},
            "detection_rate": 0.0,
            "last_processed": None
        }
        logger.info("🔄 Estadísticas del PII Scrubber reiniciadas")

# Instancia global del scrubber
pii_scrubber = PIIScrubber()