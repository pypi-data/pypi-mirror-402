"""
Do Not Sell Mechanisms para CCPA Compliance

Implementa mecanismos de opt-out de venta de datos según CCPA,
con controles de compartición de datos de terceros y auditoría completa.
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


class DataSaleCategory(Enum):
    """Categorías de venta de datos según CCPA."""
    ANALYTICS = "analytics"              # Datos para análisis
    ADVERTISING = "advertising"          # Datos para publicidad
    MARKETING = "marketing"              # Datos para marketing
    RESEARCH = "research"                # Datos para investigación
    THIRD_PARTY = "third_party"          # Compartir con terceros
    AFFILIATES = "affiliates"            # Compartir con afiliados


class ThirdPartyRecipient(Enum):
    """Destinatarios de terceros para venta de datos."""
    GOOGLE_ANALYTICS = "google_analytics"
    FACEBOOK_PIXEL = "facebook_pixel"
    LINKEDIN_INSIGHT = "linkedin_insight"
    TWITTER_CONVERSION = "twitter_conversion"
    ADROLL = "adroll"
    HUBSPOT = "hubspot"
    SALESFORCE = "salesforce"
    MARKETO = "marketo"
    MAILCHIMP = "mailchimp"
    INTERCOM = "intercom"
    ZENDESK = "zendesk"
    CUSTOM = "custom"


@dataclass
class DoNotSellPreference:
    """Preferencia de Do Not Sell para un usuario."""
    user_id: str
    global_opt_out: bool = False  # Opt-out global de venta de datos
    category_opt_outs: Set[DataSaleCategory] = field(default_factory=set)
    third_party_opt_outs: Set[ThirdPartyRecipient] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    source: str = "website"  # website, api, email, etc.
    verification_token: Optional[str] = None
    expires_at: Optional[datetime] = None

    @property
    def is_active(self) -> bool:
        """Verificar si la preferencia está activa."""
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        return True

    @property
    def effective_opt_out_categories(self) -> Set[DataSaleCategory]:
        """Obtener categorías efectivamente opt-out (incluyendo global)."""
        if self.global_opt_out:
            return set(DataSaleCategory)
        return self.category_opt_outs.copy()


@dataclass
class DataSaleTransaction:
    """Registro de transacción de venta de datos."""
    transaction_id: str
    user_id: str
    recipient: ThirdPartyRecipient
    categories: Set[DataSaleCategory]
    data_types: Set[str]  # tipos de datos vendidos
    price: Optional[float] = None
    currency: str = "USD"
    transaction_date: datetime = field(default_factory=datetime.now)
    purpose: str = ""
    compliance_check: bool = False  # Si se verificó opt-out antes de venta
    opt_out_violation: bool = False  # Si se vendió a pesar de opt-out
    metadata: Dict[str, Any] = field(default_factory=dict)


class DoNotSellManager:
    """
    Gestor de mecanismos Do Not Sell para CCPA compliance.

    Características:
    - Global y granular opt-out preferences
    - Third-party sharing controls
    - Data sale audit logging
    - Compliance verification
    - Privacy dashboard integration
    """

    def __init__(self):
        self.preferences: Dict[str, DoNotSellPreference] = {}
        self.sale_transactions: List[DataSaleTransaction] = []
        self.audit_log: List[Dict[str, Any]] = []

        # Estadísticas
        self.stats = {
            'total_opt_outs': 0,
            'global_opt_outs': 0,
            'category_opt_outs': {},
            'third_party_opt_outs': {},
            'sale_transactions': 0,
            'compliance_violations': 0
        }

        # Configuración por defecto
        self._setup_default_config()
        logger.info("DoNotSellManager initialized")

    def _setup_default_config(self):
        """Configurar opciones por defecto."""
        # Categorías disponibles para opt-out
        self.available_categories = set(DataSaleCategory)

        # Destinatarios de terceros disponibles
        self.available_recipients = set(ThirdPartyRecipient)

        # Categorías por destinatario (para mapeo automático)
        self.recipient_categories = {
            ThirdPartyRecipient.GOOGLE_ANALYTICS: {DataSaleCategory.ANALYTICS},
            ThirdPartyRecipient.FACEBOOK_PIXEL: {DataSaleCategory.ADVERTISING, DataSaleCategory.MARKETING},
            ThirdPartyRecipient.LINKEDIN_INSIGHT: {DataSaleCategory.ANALYTICS, DataSaleCategory.MARKETING},
            ThirdPartyRecipient.TWITTER_CONVERSION: {DataSaleCategory.ADVERTISING},
            ThirdPartyRecipient.ADROLL: {DataSaleCategory.ADVERTISING, DataSaleCategory.MARKETING},
            ThirdPartyRecipient.HUBSPOT: {DataSaleCategory.MARKETING, DataSaleCategory.ANALYTICS},
            ThirdPartyRecipient.SALESFORCE: {DataSaleCategory.MARKETING, DataSaleCategory.RESEARCH},
            ThirdPartyRecipient.MARKETO: {DataSaleCategory.MARKETING},
            ThirdPartyRecipient.MAILCHIMP: {DataSaleCategory.MARKETING},
            ThirdPartyRecipient.INTERCOM: {DataSaleCategory.MARKETING},
            ThirdPartyRecipient.ZENDESK: {DataSaleCategory.MARKETING},
        }

    def set_do_not_sell_preference(self,
                                  user_id: str,
                                  global_opt_out: Optional[bool] = None,
                                  category_opt_outs: Optional[List[DataSaleCategory]] = None,
                                  third_party_opt_outs: Optional[List[ThirdPartyRecipient]] = None,
                                  ip_address: Optional[str] = None,
                                  user_agent: Optional[str] = None,
                                  source: str = "website",
                                  duration_days: Optional[int] = None) -> str:
        """
        Establecer preferencias de Do Not Sell para un usuario.

        Args:
            user_id: ID del usuario
            global_opt_out: Opt-out global (True/False/None para mantener actual)
            category_opt_outs: Lista de categorías para opt-out
            third_party_opt_outs: Lista de terceros para opt-out
            ip_address: Dirección IP
            user_agent: User agent
            source: Fuente de la solicitud
            duration_days: Duración en días (None = permanente)

        Returns:
            Token de verificación
        """
        # Obtener preferencia existente o crear nueva
        preference = self.preferences.get(user_id)
        if not preference:
            preference = DoNotSellPreference(user_id=user_id)
            self.preferences[user_id] = preference

        # Actualizar preferencias
        if global_opt_out is not None:
            preference.global_opt_out = global_opt_out

        if category_opt_outs is not None:
            preference.category_opt_outs = set(category_opt_outs)

        if third_party_opt_outs is not None:
            preference.third_party_opt_outs = set(third_party_opt_outs)

        # Actualizar metadata
        preference.updated_at = datetime.now()
        preference.ip_address = ip_address
        preference.user_agent = user_agent
        preference.source = source

        # Establecer expiración si especificada
        if duration_days:
            preference.expires_at = datetime.now() + timedelta(days=duration_days)

        # Generar token de verificación
        verification_token = self._generate_verification_token(user_id)
        preference.verification_token = verification_token

        # Actualizar estadísticas
        self._update_stats()

        # Registrar en audit log
        self._audit_log('preference_set', user_id, {
            'global_opt_out': preference.global_opt_out,
            'category_opt_outs': list(preference.category_opt_outs),
            'third_party_opt_outs': list(preference.third_party_opt_outs),
            'source': source,
            'verification_token': verification_token
        })

        logger.info(f"Do Not Sell preference set for user {user_id}: global={preference.global_opt_out}")
        return verification_token

    def get_do_not_sell_status(self, user_id: str) -> Dict[str, Any]:
        """Obtener estado completo de Do Not Sell para un usuario."""
        preference = self.preferences.get(user_id)

        if not preference:
            return {
                'user_id': user_id,
                'has_preference': False,
                'global_opt_out': False,
                'category_opt_outs': [],
                'third_party_opt_outs': [],
                'effective_opt_out_categories': [],
                'is_active': False
            }

        return {
            'user_id': user_id,
            'has_preference': True,
            'global_opt_out': preference.global_opt_out,
            'category_opt_outs': list(preference.category_opt_outs),
            'third_party_opt_outs': list(preference.third_party_opt_outs),
            'effective_opt_out_categories': list(preference.effective_opt_out_categories),
            'created_at': preference.created_at.isoformat(),
            'updated_at': preference.updated_at.isoformat(),
            'expires_at': preference.expires_at.isoformat() if preference.expires_at else None,
            'is_active': preference.is_active,
            'source': preference.source
        }

    def check_data_sale_allowed(self,
                               user_id: str,
                               recipient: ThirdPartyRecipient,
                               categories: List[DataSaleCategory]) -> Dict[str, Any]:
        """
        Verificar si se permite la venta de datos según las preferencias del usuario.

        Args:
            user_id: ID del usuario
            recipient: Destinatario de los datos
            categories: Categorías de datos a vender

        Returns:
            Dict con resultado de la verificación
        """
        preference = self.preferences.get(user_id)

        result = {
            'user_id': user_id,
            'recipient': recipient.value,
            'categories_requested': [c.value for c in categories],
            'sale_allowed': True,
            'blocking_reasons': [],
            'compliance_check_passed': True
        }

        if not preference or not preference.is_active:
            # Sin preferencia = venta permitida por defecto
            result['sale_allowed'] = True
            result['compliance_check_passed'] = True
            return result

        # Verificar opt-out global
        if preference.global_opt_out:
            result['sale_allowed'] = False
            result['blocking_reasons'].append('global_opt_out')
            result['compliance_check_passed'] = False
            return result

        # Verificar opt-out por categorías
        blocked_categories = []
        for category in categories:
            if category in preference.effective_opt_out_categories:
                blocked_categories.append(category.value)

        if blocked_categories:
            result['sale_allowed'] = False
            result['blocking_reasons'].append(f'category_opt_out: {blocked_categories}')
            result['compliance_check_passed'] = False
            return result

        # Verificar opt-out por tercero específico
        if recipient in preference.third_party_opt_outs:
            result['sale_allowed'] = False
            result['blocking_reasons'].append(f'third_party_opt_out: {recipient.value}')
            result['compliance_check_passed'] = False
            return result

        return result

    def record_data_sale(self,
                        user_id: str,
                        recipient: ThirdPartyRecipient,
                        categories: List[DataSaleCategory],
                        data_types: List[str],
                        price: Optional[float] = None,
                        purpose: str = "",
                        compliance_verified: bool = True) -> str:
        """
        Registrar una transacción de venta de datos.

        Args:
            user_id: ID del usuario
            recipient: Destinatario de los datos
            categories: Categorías de datos vendidos
            data_types: Tipos de datos específicos
            price: Precio de la transacción
            purpose: Propósito de la venta
            compliance_verified: Si se verificó compliance antes de vender

        Returns:
            ID de la transacción
        """
        transaction_id = f"sale_{user_id}_{recipient.value}_{int(datetime.now().timestamp())}"

        # Verificar compliance antes de registrar
        compliance_check = self.check_data_sale_allowed(user_id, recipient, categories)
        opt_out_violation = not compliance_check['sale_allowed']

        if opt_out_violation and compliance_verified:
            logger.warning(f"Data sale compliance violation for user {user_id}: {compliance_check}")
            self.stats['compliance_violations'] += 1

        transaction = DataSaleTransaction(
            transaction_id=transaction_id,
            user_id=user_id,
            recipient=recipient,
            categories=set(categories),
            data_types=set(data_types),
            price=price,
            purpose=purpose,
            compliance_check=compliance_verified,
            opt_out_violation=opt_out_violation
        )

        self.sale_transactions.append(transaction)
        self.stats['sale_transactions'] += 1

        # Registrar en audit log
        self._audit_log('data_sale', user_id, {
            'transaction_id': transaction_id,
            'recipient': recipient.value,
            'categories': [c.value for c in categories],
            'data_types': data_types,
            'price': price,
            'purpose': purpose,
            'compliance_verified': compliance_verified,
            'opt_out_violation': opt_out_violation
        })

        logger.info(f"Data sale recorded: {transaction_id} for user {user_id} to {recipient.value}")
        return transaction_id

    def get_privacy_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """Obtener datos para el privacy dashboard del usuario."""
        preference = self.preferences.get(user_id)

        # Obtener transacciones de venta recientes
        user_transactions = [
            t for t in self.sale_transactions[-100:]  # Últimas 100 transacciones
            if t.user_id == user_id
        ]

        # Resumir transacciones por destinatario
        sales_summary = {}
        for transaction in user_transactions[-50:]:  # Últimas 50 para dashboard
            recipient = transaction.recipient.value
            if recipient not in sales_summary:
                sales_summary[recipient] = {
                    'total_sales': 0,
                    'categories': set(),
                    'last_sale': None,
                    'total_value': 0.0
                }

            summary = sales_summary[recipient]
            summary['total_sales'] += 1
            summary['categories'].update([c.value for c in transaction.categories])
            if transaction.price:
                summary['total_value'] += transaction.price

            if not summary['last_sale'] or transaction.transaction_date > summary['last_sale']:
                summary['last_sale'] = transaction.transaction_date

        # Convertir sets a listas para JSON
        for summary in sales_summary.values():
            summary['categories'] = list(summary['categories'])
            summary['last_sale'] = summary['last_sale'].isoformat() if summary['last_sale'] else None

        return {
            'user_id': user_id,
            'do_not_sell_status': self.get_do_not_sell_status(user_id),
            'sales_summary': sales_summary,
            'total_sales': len(user_transactions),
            'recent_sales': [
                {
                    'transaction_id': t.transaction_id,
                    'recipient': t.recipient.value,
                    'categories': [c.value for c in t.categories],
                    'date': t.transaction_date.isoformat(),
                    'price': t.price,
                    'purpose': t.purpose,
                    'compliance_issue': t.opt_out_violation
                }
                for t in sorted(user_transactions[-10:], key=lambda x: x.transaction_date, reverse=True)
            ],
            'generated_at': datetime.now().isoformat()
        }

    def get_compliance_report(self,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generar reporte de compliance para CCPA."""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        # Filtrar transacciones por fecha
        period_transactions = [
            t for t in self.sale_transactions
            if start_date <= t.transaction_date <= end_date
        ]

        # Calcular métricas de compliance
        total_sales = len(period_transactions)
        compliance_violations = len([t for t in period_transactions if t.opt_out_violation])
        compliance_rate = (total_sales - compliance_violations) / total_sales * 100 if total_sales > 0 else 100

        # Ventas por destinatario
        sales_by_recipient = {}
        for transaction in period_transactions:
            recipient = transaction.recipient.value
            if recipient not in sales_by_recipient:
                sales_by_recipient[recipient] = {
                    'total_sales': 0,
                    'total_value': 0.0,
                    'violations': 0
                }

            sales_by_recipient[recipient]['total_sales'] += 1
            if transaction.price:
                sales_by_recipient[recipient]['total_value'] += transaction.price
            if transaction.opt_out_violation:
                sales_by_recipient[recipient]['violations'] += 1

        # Preferencias de opt-out
        active_opt_outs = len([p for p in self.preferences.values() if p.is_active])
        global_opt_outs = len([p for p in self.preferences.values() if p.is_active and p.global_opt_out])

        return {
            'report_period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'compliance_metrics': {
                'total_sales': total_sales,
                'compliance_violations': compliance_violations,
                'compliance_rate': round(compliance_rate, 2),
                'active_opt_outs': active_opt_outs,
                'global_opt_outs': global_opt_outs
            },
            'sales_by_recipient': sales_by_recipient,
            'top_violations': sorted([
                {
                    'recipient': recipient,
                    'violations': data['violations'],
                    'violation_rate': round(data['violations'] / data['total_sales'] * 100, 2) if data['total_sales'] > 0 else 0
                }
                for recipient, data in sales_by_recipient.items()
                if data['violations'] > 0
            ], key=lambda x: x['violations'], reverse=True)[:10],
            'generated_at': datetime.now().isoformat()
        }

    def _generate_verification_token(self, user_id: str) -> str:
        """Generar token de verificación para preferencias."""
        data = f"{user_id}:{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _audit_log(self, action: str, user_id: str, details: Dict[str, Any]):
        """Registrar acción en audit log."""
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'user_id': user_id,
            'details': details
        }

        self.audit_log.append(audit_entry)

        # Mantener tamaño del audit log
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-5000:]

    def _update_stats(self):
        """Actualizar estadísticas."""
        total_opt_outs = len([p for p in self.preferences.values() if p.is_active])
        global_opt_outs = len([p for p in self.preferences.values() if p.is_active and p.global_opt_out])

        # Estadísticas por categoría
        category_opt_outs = {}
        for preference in self.preferences.values():
            if preference.is_active:
                for category in preference.category_opt_outs:
                    cat_name = category.value
                    category_opt_outs[cat_name] = category_opt_outs.get(cat_name, 0) + 1

        # Estadísticas por tercero
        third_party_opt_outs = {}
        for preference in self.preferences.values():
            if preference.is_active:
                for recipient in preference.third_party_opt_outs:
                    rec_name = recipient.value
                    third_party_opt_outs[rec_name] = third_party_opt_outs.get(rec_name, 0) + 1

        self.stats.update({
            'total_opt_outs': total_opt_outs,
            'global_opt_outs': global_opt_outs,
            'category_opt_outs': category_opt_outs,
            'third_party_opt_outs': third_party_opt_outs
        })

    def get_audit_trail(self, user_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtener audit trail de acciones de Do Not Sell."""
        audit_entries = self.audit_log.copy()

        if user_id:
            audit_entries = [entry for entry in audit_entries if entry.get('user_id') == user_id]

        # Ordenar por timestamp descendente
        audit_entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        return audit_entries[:limit]


# Instancia global del Do Not Sell manager
_do_not_sell_manager = DoNotSellManager()


def get_do_not_sell_manager() -> DoNotSellManager:
    """Obtener instancia global del Do Not Sell manager."""
    return _do_not_sell_manager


# Funciones de conveniencia

def set_user_do_not_sell_preference(user_id: str, global_opt_out: bool = True,
                                   categories: Optional[List[DataSaleCategory]] = None,
                                   third_parties: Optional[List[ThirdPartyRecipient]] = None) -> str:
    """Establecer preferencia Do Not Sell para usuario."""
    return _do_not_sell_manager.set_do_not_sell_preference(
        user_id=user_id,
        global_opt_out=global_opt_out,
        category_opt_outs=categories,
        third_party_opt_outs=third_parties
    )


def check_data_sale_compliance(user_id: str, recipient: ThirdPartyRecipient,
                              categories: List[DataSaleCategory]) -> bool:
    """Verificar si se permite venta de datos."""
    result = _do_not_sell_manager.check_data_sale_allowed(user_id, recipient, categories)
    return result['sale_allowed']


def record_data_sale_transaction(user_id: str, recipient: ThirdPartyRecipient,
                                categories: List[DataSaleCategory], data_types: List[str],
                                price: Optional[float] = None) -> str:
    """Registrar transacción de venta de datos."""
    return _do_not_sell_manager.record_data_sale(
        user_id=user_id,
        recipient=recipient,
        categories=categories,
        data_types=data_types,
        price=price
    )