"""
Consent Management System para GDPR Compliance

Implementa gestión completa de consentimientos con:
- Cookie consent banners
- Granular privacy preferences
- Audit trail de consentimientos
- Withdrawal y modification capabilities
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib

logger = logging.getLogger(__name__)


class ConsentCategory(Enum):
    """Categorías de consentimiento según GDPR."""
    ESSENTIAL = "essential"              # Cookies técnicas esenciales
    ANALYTICS = "analytics"              # Cookies de analítica
    MARKETING = "marketing"              # Cookies de marketing
    FUNCTIONAL = "functional"            # Cookies funcionales
    PERSONALIZATION = "personalization"  # Cookies de personalización
    SOCIAL_MEDIA = "social_media"        # Cookies de redes sociales
    THIRD_PARTY = "third_party"          # Cookies de terceros


class ConsentPurpose(Enum):
    """Propósitos específicos de procesamiento de datos."""
    ACCOUNT_CREATION = "account_creation"
    FEDERATED_TRAINING = "federated_training"
    MARKETPLACE_TRANSACTIONS = "marketplace_transactions"
    ANALYTICS_TRACKING = "analytics_tracking"
    MARKETING_COMMUNICATIONS = "marketing_communications"
    PERSONALIZATION = "personalization"
    ERROR_REPORTING = "error_reporting"
    PERFORMANCE_MONITORING = "performance_monitoring"


@dataclass
class ConsentRecord:
    """Registro de consentimiento de un usuario."""
    consent_id: str
    user_id: str
    categories: Set[ConsentCategory]
    purposes: Set[ConsentPurpose]
    granted_at: datetime
    expires_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    source: str = "website"  # website, api, mobile_app
    version: str = "1.0"
    withdrawn_at: Optional[datetime] = None
    withdrawal_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        """Verificar si el consentimiento está activo."""
        if self.withdrawn_at:
            return False
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        return True

    @property
    def is_expired(self) -> bool:
        """Verificar si el consentimiento ha expirado."""
        return self.expires_at and datetime.now() > self.expires_at


@dataclass
class ConsentTemplate:
    """Plantilla de consentimiento para categorías específicas."""
    category: ConsentCategory
    title: str
    description: str
    required: bool = False  # Si es obligatorio (essential cookies)
    default_granted: bool = False
    retention_days: int = 365
    purposes: Set[ConsentPurpose] = field(default_factory=set)


class ConsentManager:
    """
    Gestor completo de consentimientos para GDPR compliance.

    Características:
    - Gestión granular de consentimientos por categoría
    - Cookie consent banners dinámicos
    - Audit trail completo
    - Withdrawal y modification capabilities
    - Integration con data retention policies
    """

    def __init__(self):
        self.consent_records: Dict[str, ConsentRecord] = {}
        self.consent_templates: Dict[ConsentCategory, ConsentTemplate] = {}
        self.audit_log: List[Dict[str, Any]] = []

        # Estadísticas
        self.stats = {
            'total_consents': 0,
            'active_consents': 0,
            'withdrawn_consents': 0,
            'expired_consents': 0,
            'consent_by_category': {},
            'consent_by_purpose': {}
        }

        self._setup_default_templates()
        logger.info("ConsentManager initialized")

    def _setup_default_templates(self):
        """Configurar plantillas de consentimiento por defecto."""
        templates = [
            ConsentTemplate(
                category=ConsentCategory.ESSENTIAL,
                title="Cookies Esenciales",
                description="Cookies necesarias para el funcionamiento básico del sitio web y servicios esenciales.",
                required=True,
                default_granted=True,
                retention_days=2555,  # 7 años
                purposes={ConsentPurpose.ACCOUNT_CREATION, ConsentPurpose.ERROR_REPORTING}
            ),
            ConsentTemplate(
                category=ConsentCategory.ANALYTICS,
                title="Cookies de Analítica",
                description="Cookies que nos ayudan a entender cómo los usuarios interactúan con nuestro sitio web.",
                required=False,
                default_granted=False,
                retention_days=730,  # 2 años
                purposes={ConsentPurpose.ANALYTICS_TRACKING, ConsentPurpose.PERFORMANCE_MONITORING}
            ),
            ConsentTemplate(
                category=ConsentCategory.MARKETING,
                title="Cookies de Marketing",
                description="Cookies utilizadas para mostrar anuncios relevantes y medir la efectividad de campañas publicitarias.",
                required=False,
                default_granted=False,
                retention_days=365,
                purposes={ConsentPurpose.MARKETING_COMMUNICATIONS}
            ),
            ConsentTemplate(
                category=ConsentCategory.FUNCTIONAL,
                title="Cookies Funcionales",
                description="Cookies que mejoran la funcionalidad del sitio web, como recordar preferencias del usuario.",
                required=False,
                default_granted=False,
                retention_days=365,
                purposes={ConsentPurpose.PERSONALIZATION}
            ),
            ConsentTemplate(
                category=ConsentCategory.PERSONALIZATION,
                title="Cookies de Personalización",
                description="Cookies que permiten personalizar la experiencia del usuario basado en sus preferencias.",
                required=False,
                default_granted=False,
                retention_days=365,
                purposes={ConsentPurpose.PERSONALIZATION, ConsentPurpose.FEDERATED_TRAINING}
            ),
            ConsentTemplate(
                category=ConsentCategory.SOCIAL_MEDIA,
                title="Cookies de Redes Sociales",
                description="Cookies de plataformas de redes sociales integradas en nuestro sitio.",
                required=False,
                default_granted=False,
                retention_days=365,
                purposes={ConsentPurpose.MARKETING_COMMUNICATIONS}
            ),
            ConsentTemplate(
                category=ConsentCategory.THIRD_PARTY,
                title="Cookies de Terceros",
                description="Cookies establecidas por servicios de terceros que utilizamos.",
                required=False,
                default_granted=False,
                retention_days=365,
                purposes={ConsentPurpose.ANALYTICS_TRACKING, ConsentPurpose.MARKETING_COMMUNICATIONS}
            )
        ]

        for template in templates:
            self.consent_templates[template.category] = template

    def grant_consent(self,
                     user_id: str,
                     categories: List[ConsentCategory],
                     purposes: List[ConsentPurpose],
                     ip_address: Optional[str] = None,
                     user_agent: Optional[str] = None,
                     source: str = "website",
                     duration_days: Optional[int] = None) -> str:
        """
        Otorgar consentimiento para categorías y propósitos específicos.

        Args:
            user_id: ID del usuario
            categories: Categorías de consentimiento
            purposes: Propósitos de procesamiento
            ip_address: Dirección IP del usuario
            user_agent: User agent del navegador
            source: Fuente del consentimiento (website, api, etc.)
            duration_days: Duración en días (None = no expira)

        Returns:
            ID del consentimiento otorgado
        """
        consent_id = f"consent_{user_id}_{int(datetime.now().timestamp())}"

        expires_at = None
        if duration_days:
            expires_at = datetime.now() + timedelta(days=duration_days)

        # Si no se especifica duración, usar la máxima de las categorías
        if not expires_at:
            max_retention = max(
                self.consent_templates[cat].retention_days
                for cat in categories
                if cat in self.consent_templates
            )
            expires_at = datetime.now() + timedelta(days=max_retention)

        consent = ConsentRecord(
            consent_id=consent_id,
            user_id=user_id,
            categories=set(categories),
            purposes=set(purposes),
            granted_at=datetime.now(),
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            source=source
        )

        self.consent_records[consent_id] = consent
        self._update_stats()

        # Registrar en audit log
        self._audit_log('grant', consent)

        logger.info(f"Consent granted: {consent_id} for user {user_id} ({len(categories)} categories)")
        return consent_id

    def withdraw_consent(self,
                        user_id: str,
                        categories: Optional[List[ConsentCategory]] = None,
                        reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Retirar consentimiento parcial o total.

        Args:
            user_id: ID del usuario
            categories: Categorías específicas a retirar (None = todas)
            reason: Razón del retiro

        Returns:
            Resultados del retiro
        """
        results = {
            'user_id': user_id,
            'consents_withdrawn': 0,
            'categories_affected': set(),
            'errors': []
        }

        # Encontrar consentimientos activos del usuario
        user_consents = [
            consent for consent in self.consent_records.values()
            if consent.user_id == user_id and consent.is_active
        ]

        for consent in user_consents:
            try:
                if categories is None:
                    # Retirar todas las categorías
                    consent.withdrawn_at = datetime.now()
                    consent.withdrawal_reason = reason
                    results['categories_affected'].update(consent.categories)
                    results['consents_withdrawn'] += 1
                else:
                    # Retirar categorías específicas
                    categories_to_remove = set(categories) & consent.categories
                    if categories_to_remove:
                        consent.categories -= categories_to_remove
                        results['categories_affected'].update(categories_to_remove)
                        results['consents_withdrawn'] += 1

                        # Si no quedan categorías, marcar como withdrawn
                        if not consent.categories:
                            consent.withdrawn_at = datetime.now()
                            consent.withdrawal_reason = reason

                # Registrar en audit log
                self._audit_log('withdraw', consent, {'reason': reason, 'categories': categories})

            except Exception as e:
                error_msg = f"Error withdrawing consent {consent.consent_id}: {e}"
                results['errors'].append(error_msg)
                logger.error(error_msg)

        self._update_stats()
        logger.info(f"Consent withdrawal completed for user {user_id}: {results}")
        return results

    def modify_consent(self,
                      user_id: str,
                      add_categories: Optional[List[ConsentCategory]] = None,
                      remove_categories: Optional[List[ConsentCategory]] = None,
                      add_purposes: Optional[List[ConsentPurpose]] = None,
                      remove_purposes: Optional[List[ConsentPurpose]] = None) -> Dict[str, Any]:
        """
        Modificar consentimiento existente.

        Args:
            user_id: ID del usuario
            add_categories: Categorías a añadir
            remove_categories: Categorías a remover
            add_purposes: Propósitos a añadir
            remove_purposes: Propósitos a remover

        Returns:
            Resultados de la modificación
        """
        results = {
            'user_id': user_id,
            'consent_modified': False,
            'categories_added': set(),
            'categories_removed': set(),
            'purposes_added': set(),
            'purposes_removed': set()
        }

        # Encontrar consentimiento activo más reciente del usuario
        user_consents = [
            consent for consent in self.consent_records.values()
            if consent.user_id == user_id and consent.is_active
        ]

        if not user_consents:
            return results

        # Usar el consentimiento más reciente
        consent = max(user_consents, key=lambda c: c.granted_at)

        # Modificar categorías
        if add_categories:
            consent.categories.update(add_categories)
            results['categories_added'].update(add_categories)

        if remove_categories:
            consent.categories -= set(remove_categories)
            results['categories_removed'].update(remove_categories)

        # Modificar propósitos
        if add_purposes:
            consent.purposes.update(add_purposes)
            results['purposes_added'].update(add_purposes)

        if remove_purposes:
            consent.purposes -= set(remove_purposes)
            results['purposes_removed'].update(remove_purposes)

        if any([add_categories, remove_categories, add_purposes, remove_purposes]):
            results['consent_modified'] = True
            self._audit_log('modify', consent, {
                'added_categories': list(results['categories_added']),
                'removed_categories': list(results['categories_removed']),
                'added_purposes': list(results['purposes_added']),
                'removed_purposes': list(results['purposes_removed'])
            })

        logger.info(f"Consent modified for user {user_id}: {results}")
        return results

    def check_consent(self,
                     user_id: str,
                     category: ConsentCategory,
                     purpose: Optional[ConsentPurpose] = None) -> bool:
        """
        Verificar si un usuario ha consentido una categoría y propósito específicos.

        Args:
            user_id: ID del usuario
            category: Categoría a verificar
            purpose: Propósito específico (opcional)

        Returns:
            True si el consentimiento está otorgado y activo
        """
        # Encontrar consentimientos activos del usuario
        user_consents = [
            consent for consent in self.consent_records.values()
            if consent.user_id == user_id and consent.is_active
        ]

        for consent in user_consents:
            if category in consent.categories:
                if purpose is None or purpose in consent.purposes:
                    return True

        return False

    def get_user_consent_status(self, user_id: str) -> Dict[str, Any]:
        """Obtener estado completo de consentimientos de un usuario."""
        user_consents = [
            consent for consent in self.consent_records.values()
            if consent.user_id == user_id
        ]

        # Consentimiento activo más reciente
        active_consents = [c for c in user_consents if c.is_active]
        latest_consent = max(active_consents, key=lambda c: c.granted_at) if active_consents else None

        return {
            'user_id': user_id,
            'has_active_consent': len(active_consents) > 0,
            'total_consents': len(user_consents),
            'active_consents': len(active_consents),
            'latest_consent': {
                'consent_id': latest_consent.consent_id if latest_consent else None,
                'categories': [c.value for c in (latest_consent.categories if latest_consent else set())],
                'purposes': [p.value for p in (latest_consent.purposes if latest_consent else set())],
                'granted_at': latest_consent.granted_at.isoformat() if latest_consent else None,
                'expires_at': latest_consent.expires_at.isoformat() if latest_consent and latest_consent.expires_at else None
            } if latest_consent else None,
            'consent_history': [
                {
                    'consent_id': c.consent_id,
                    'status': 'active' if c.is_active else ('withdrawn' if c.withdrawn_at else 'expired'),
                    'granted_at': c.granted_at.isoformat(),
                    'categories': [cat.value for cat in c.categories]
                }
                for c in sorted(user_consents, key=lambda x: x.granted_at, reverse=True)
            ]
        }

    def get_consent_banner_config(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtener configuración para cookie consent banner.

        Args:
            user_id: ID del usuario (opcional, para personalizar basado en consentimientos existentes)

        Returns:
            Configuración del banner
        """
        banner_config = {
            'show_banner': True,
            'categories': {},
            'required_categories': [],
            'default_preferences': {}
        }

        # Verificar si el usuario ya tiene consentimientos
        if user_id:
            user_status = self.get_user_consent_status(user_id)
            if user_status['has_active_consent']:
                banner_config['show_banner'] = False
                return banner_config

        # Configurar categorías para el banner
        for category, template in self.consent_templates.items():
            banner_config['categories'][category.value] = {
                'title': template.title,
                'description': template.description,
                'required': template.required,
                'default': template.default_granted
            }

            if template.required:
                banner_config['required_categories'].append(category.value)

            banner_config['default_preferences'][category.value] = template.default_granted

        return banner_config

    def get_consent_audit_trail(self,
                               user_id: Optional[str] = None,
                               limit: int = 100) -> List[Dict[str, Any]]:
        """Obtener audit trail de consentimientos."""
        audit_entries = self.audit_log.copy()

        if user_id:
            audit_entries = [entry for entry in audit_entries if entry.get('user_id') == user_id]

        # Ordenar por timestamp descendente
        audit_entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        return audit_entries[:limit]

    def _audit_log(self, action: str, consent: ConsentRecord, extra_data: Optional[Dict] = None):
        """Registrar acción en audit log."""
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'consent_id': consent.consent_id,
            'user_id': consent.user_id,
            'categories': [c.value for c in consent.categories],
            'purposes': [p.value for p in consent.purposes],
            'source': consent.source,
            'ip_address': consent.ip_address,
            'user_agent': consent.user_agent
        }

        if extra_data:
            audit_entry.update(extra_data)

        self.audit_log.append(audit_entry)

        # Mantener tamaño del audit log
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-5000:]  # Mantener últimos 5000

    def _update_stats(self):
        """Actualizar estadísticas."""
        total_consents = len(self.consent_records)
        active_consents = len([c for c in self.consent_records.values() if c.is_active])
        withdrawn_consents = len([c for c in self.consent_records.values() if c.withdrawn_at])
        expired_consents = len([c for c in self.consent_records.values() if c.is_expired and not c.withdrawn_at])

        # Estadísticas por categoría
        consent_by_category = {}
        for consent in self.consent_records.values():
            for category in consent.categories:
                cat_name = category.value
                if cat_name not in consent_by_category:
                    consent_by_category[cat_name] = 0
                consent_by_category[cat_name] += 1

        # Estadísticas por propósito
        consent_by_purpose = {}
        for consent in self.consent_records.values():
            for purpose in consent.purposes:
                purp_name = purpose.value
                if purp_name not in consent_by_purpose:
                    consent_by_purpose[purp_name] = 0
                consent_by_purpose[purp_name] += 1

        self.stats.update({
            'total_consents': total_consents,
            'active_consents': active_consents,
            'withdrawn_consents': withdrawn_consents,
            'expired_consents': expired_consents,
            'consent_by_category': consent_by_category,
            'consent_by_purpose': consent_by_purpose
        })

    def get_consent_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas generales de consentimientos."""
        return {
            **self.stats,
            'generated_at': datetime.now().isoformat()
        }


# Instancia global del consent manager
_consent_manager = ConsentManager()


def get_consent_manager() -> ConsentManager:
    """Obtener instancia global del consent manager."""
    return _consent_manager


# Funciones de conveniencia

def check_user_consent(user_id: str, category: ConsentCategory, purpose: Optional[ConsentPurpose] = None) -> bool:
    """Verificar consentimiento de usuario."""
    return _consent_manager.check_consent(user_id, category, purpose)


def grant_user_consent(user_id: str, categories: List[ConsentCategory], purposes: List[ConsentPurpose],
                      ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> str:
    """Otorgar consentimiento a usuario."""
    return _consent_manager.grant_consent(user_id, categories, purposes, ip_address, user_agent)


def withdraw_user_consent(user_id: str, categories: Optional[List[ConsentCategory]] = None,
                         reason: Optional[str] = None) -> Dict[str, Any]:
    """Retirar consentimiento de usuario."""
    return _consent_manager.withdraw_consent(user_id, categories, reason)