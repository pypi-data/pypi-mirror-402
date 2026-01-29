"""
Data Retention Policies para GDPR Compliance

Implementa políticas de retención de datos con eliminación automática
y auditoría completa de compliance.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class DataCategory(Enum):
    """Categorías de datos para políticas de retención."""
    USER_PROFILE = "user_profile"
    TRAINING_DATA = "training_data"
    FEDERATED_MODELS = "federated_models"
    AUDIT_LOGS = "audit_logs"
    CONSENT_RECORDS = "consent_records"
    BLOCKCHAIN_TRANSACTIONS = "blockchain_transactions"
    API_LOGS = "api_logs"
    SESSION_DATA = "session_data"
    MARKETPLACE_DATA = "marketplace_data"


class RetentionPolicy(Enum):
    """Políticas de retención predefinidas."""
    STRICT_GDPR = "strict_gdpr"          # 30 días para datos personales
    MODERATE_COMPLIANCE = "moderate"     # 90 días para datos operacionales
    BUSINESS_CRITICAL = "business"       # 365 días para datos de negocio
    PERMANENT_AUDIT = "permanent"        # Retención permanente para auditoría
    CUSTOM = "custom"                    # Política personalizada


@dataclass
class RetentionRule:
    """Regla de retención para una categoría de datos."""
    category: DataCategory
    policy: RetentionPolicy
    retention_days: int
    auto_delete: bool = True
    anonymize_after_days: Optional[int] = None
    archive_after_days: Optional[int] = None
    notification_days: int = 30  # Notificar X días antes de eliminación
    enabled: bool = True

    def __post_init__(self):
        """Validar configuración de la regla."""
        if self.anonymize_after_days and self.anonymize_after_days >= self.retention_days:
            raise ValueError("anonymize_after_days debe ser menor que retention_days")

        if self.archive_after_days and self.archive_after_days >= self.retention_days:
            raise ValueError("archive_after_days debe ser menor que retention_days")


@dataclass
class DataRetentionRecord:
    """Registro de retención de datos."""
    record_id: str
    category: DataCategory
    user_id: Optional[str]
    data_location: str  # database.table, file_path, etc.
    created_at: datetime
    retention_until: datetime
    status: str = "active"  # active, anonymized, archived, deleted
    last_accessed: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DataRetentionManager:
    """
    Gestor de políticas de retención de datos para GDPR compliance.

    Características:
    - Políticas de retención configurables por categoría
    - Eliminación automática programada
    - Anonimización de datos antiguos
    - Auditoría completa de operaciones
    - Notificaciones de eliminación próxima
    """

    def __init__(self):
        self.retention_rules: Dict[DataCategory, RetentionRule] = {}
        self.retention_records: Dict[str, DataRetentionRecord] = {}
        self.deletion_queue: List[Dict[str, Any]] = []
        self.notification_queue: List[Dict[str, Any]] = []

        # Callbacks para operaciones de datos
        self.deletion_callbacks: Dict[DataCategory, Callable] = {}
        self.anonymization_callbacks: Dict[DataCategory, Callable] = {}
        self.archive_callbacks: Dict[DataCategory, Callable] = {}

        # Estadísticas
        self.stats = {
            'records_processed': 0,
            'records_deleted': 0,
            'records_anonymized': 0,
            'records_archived': 0,
            'notifications_sent': 0
        }

        self._setup_default_policies()
        logger.info("DataRetentionManager initialized")

    def _setup_default_policies(self):
        """Configurar políticas de retención por defecto según GDPR."""
        default_rules = [
            RetentionRule(
                category=DataCategory.USER_PROFILE,
                policy=RetentionPolicy.STRICT_GDPR,
                retention_days=30,  # GDPR: datos personales limitados
                auto_delete=True,
                anonymize_after_days=15,
                notification_days=7
            ),
            RetentionRule(
                category=DataCategory.TRAINING_DATA,
                policy=RetentionPolicy.STRICT_GDPR,
                retention_days=30,
                auto_delete=True,
                anonymize_after_days=15,
                notification_days=7
            ),
            RetentionRule(
                category=DataCategory.FEDERATED_MODELS,
                policy=RetentionPolicy.BUSINESS_CRITICAL,
                retention_days=365,
                auto_delete=False,  # No auto-eliminar modelos
                archive_after_days=180,
                notification_days=30
            ),
            RetentionRule(
                category=DataCategory.AUDIT_LOGS,
                policy=RetentionPolicy.PERMANENT_AUDIT,
                retention_days=2555,  # 7 años según GDPR
                auto_delete=False,
                archive_after_days=365,
                notification_days=90
            ),
            RetentionRule(
                category=DataCategory.CONSENT_RECORDS,
                policy=RetentionPolicy.PERMANENT_AUDIT,
                retention_days=2555,
                auto_delete=False,
                notification_days=90
            ),
            RetentionRule(
                category=DataCategory.BLOCKCHAIN_TRANSACTIONS,
                policy=RetentionPolicy.PERMANENT_AUDIT,
                retention_days=2555,
                auto_delete=False,
                notification_days=90
            ),
            RetentionRule(
                category=DataCategory.API_LOGS,
                policy=RetentionPolicy.MODERATE_COMPLIANCE,
                retention_days=90,
                auto_delete=True,
                anonymize_after_days=30,
                notification_days=14
            ),
            RetentionRule(
                category=DataCategory.SESSION_DATA,
                policy=RetentionPolicy.STRICT_GDPR,
                retention_days=30,
                auto_delete=True,
                notification_days=7
            ),
            RetentionRule(
                category=DataCategory.MARKETPLACE_DATA,
                policy=RetentionPolicy.MODERATE_COMPLIANCE,
                retention_days=180,
                auto_delete=True,
                anonymize_after_days=90,
                notification_days=30
            )
        ]

        for rule in default_rules:
            self.retention_rules[rule.category] = rule

    def register_data_record(self,
                           category: DataCategory,
                           user_id: Optional[str],
                           data_location: str,
                           metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Registrar un nuevo registro de datos para retención.

        Args:
            category: Categoría del dato
            user_id: ID del usuario (opcional)
            data_location: Ubicación del dato (table.column, file_path, etc.)
            metadata: Metadata adicional

        Returns:
            ID del registro de retención
        """
        if category not in self.retention_rules:
            raise ValueError(f"No retention policy defined for category: {category}")

        rule = self.retention_rules[category]
        record_id = f"ret_{category.value}_{user_id or 'system'}_{int(datetime.now().timestamp())}"

        retention_until = datetime.now() + timedelta(days=rule.retention_days)

        record = DataRetentionRecord(
            record_id=record_id,
            category=category,
            user_id=user_id,
            data_location=data_location,
            created_at=datetime.now(),
            retention_until=retention_until,
            metadata=metadata or {}
        )

        self.retention_records[record_id] = record
        self.stats['records_processed'] += 1

        logger.info(f"Registered retention record: {record_id} for {category.value} (expires: {retention_until})")
        return record_id

    def update_last_access(self, record_id: str):
        """Actualizar timestamp de último acceso."""
        if record_id in self.retention_records:
            self.retention_records[record_id].last_accessed = datetime.now()

    async def process_retention_policies(self) -> Dict[str, Any]:
        """
        Procesar todas las políticas de retención.
        Ejecutar eliminación, anonimización y archivado según corresponda.

        Returns:
            Resultados del procesamiento
        """
        results = {
            'notifications_sent': 0,
            'records_anonymized': 0,
            'records_archived': 0,
            'records_deleted': 0,
            'errors': []
        }

        now = datetime.now()

        for record_id, record in list(self.retention_records.items()):
            if record.status != 'active':
                continue

            try:
                rule = self.retention_rules[record.category]

                # Calcular días restantes
                days_until_expiry = (record.retention_until - now).days

                # 1. Enviar notificaciones
                if days_until_expiry <= rule.notification_days and days_until_expiry > 0:
                    await self._send_deletion_notification(record)
                    results['notifications_sent'] += 1

                # 2. Anonimizar si corresponde
                if (rule.anonymize_after_days and
                    (now - record.created_at).days >= rule.anonymize_after_days):
                    await self._anonymize_record(record)
                    results['records_anonymized'] += 1

                # 3. Archivar si corresponde
                if (rule.archive_after_days and
                    (now - record.created_at).days >= rule.archive_after_days):
                    await self._archive_record(record)
                    results['records_archived'] += 1

                # 4. Eliminar si expiró
                if now >= record.retention_until and rule.auto_delete:
                    await self._delete_record(record)
                    results['records_deleted'] += 1
                    del self.retention_records[record_id]

            except Exception as e:
                error_msg = f"Error processing record {record_id}: {e}"
                results['errors'].append(error_msg)
                logger.error(error_msg)

        # Actualizar estadísticas globales
        self.stats['records_anonymized'] += results['records_anonymized']
        self.stats['records_archived'] += results['records_archived']
        self.stats['records_deleted'] += results['records_deleted']
        self.stats['notifications_sent'] += results['notifications_sent']

        logger.info(f"Retention processing completed: {results}")
        return results

    async def force_delete_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Forzar eliminación de todos los datos de un usuario (Right to Erasure).

        Args:
            user_id: ID del usuario

        Returns:
            Resultados de la eliminación
        """
        results = {
            'user_id': user_id,
            'records_found': 0,
            'records_deleted': 0,
            'errors': []
        }

        # Encontrar todos los registros del usuario
        user_records = [
            record for record in self.retention_records.values()
            if record.user_id == user_id and record.status == 'active'
        ]

        results['records_found'] = len(user_records)

        for record in user_records:
            try:
                await self._delete_record(record)
                record.status = 'deleted'
                results['records_deleted'] += 1
                logger.info(f"Force deleted user data: {record.record_id}")
            except Exception as e:
                error_msg = f"Error deleting record {record.record_id}: {e}"
                results['errors'].append(error_msg)
                logger.error(error_msg)

        return results

    async def _send_deletion_notification(self, record: DataRetentionRecord):
        """Enviar notificación de eliminación próxima."""
        # En implementación real, enviar email/SMS/push notification
        logger.warning(f"DATA DELETION NOTICE: {record.category.value} data for user {record.user_id} "
                      f"will be deleted in {(record.retention_until - datetime.now()).days} days")

        # Añadir a cola de notificaciones para procesamiento
        self.notification_queue.append({
            'record_id': record.record_id,
            'user_id': record.user_id,
            'category': record.category.value,
            'deletion_date': record.retention_until.isoformat(),
            'sent_at': datetime.now().isoformat()
        })

    async def _anonymize_record(self, record: DataRetentionRecord):
        """Anonimizar un registro de datos."""
        logger.info(f"Anonymizing record: {record.record_id}")

        # Llamar al callback de anonimización si existe
        callback = self.anonymization_callbacks.get(record.category)
        if callback:
            await callback(record)
        else:
            # Anonimización por defecto (placeholder)
            logger.warning(f"No anonymization callback for {record.category.value}")

        record.status = 'anonymized'

    async def _archive_record(self, record: DataRetentionRecord):
        """Archivar un registro de datos."""
        logger.info(f"Archiving record: {record.record_id}")

        # Llamar al callback de archivado si existe
        callback = self.archive_callbacks.get(record.category)
        if callback:
            await callback(record)
        else:
            # Archivado por defecto (placeholder)
            logger.warning(f"No archive callback for {record.category.value}")

        record.status = 'archived'

    async def _delete_record(self, record: DataRetentionRecord):
        """Eliminar un registro de datos."""
        logger.info(f"Deleting record: {record.record_id}")

        # Llamar al callback de eliminación si existe
        callback = self.deletion_callbacks.get(record.category)
        if callback:
            await callback(record)
        else:
            # Eliminación por defecto (placeholder)
            logger.warning(f"No deletion callback for {record.category.value}")

        record.status = 'deleted'

    def register_deletion_callback(self, category: DataCategory, callback: Callable):
        """Registrar callback para eliminación de datos."""
        self.deletion_callbacks[category] = callback
        logger.info(f"Registered deletion callback for {category.value}")

    def register_anonymization_callback(self, category: DataCategory, callback: Callable):
        """Registrar callback para anonimización de datos."""
        self.anonymization_callbacks[category] = callback
        logger.info(f"Registered anonymization callback for {category.value}")

    def register_archive_callback(self, category: DataCategory, callback: Callable):
        """Registrar callback para archivado de datos."""
        self.archive_callbacks[category] = callback
        logger.info(f"Registered archive callback for {category.value}")

    def get_retention_status(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Obtener estado de retención de datos."""
        records = list(self.retention_records.values())

        if user_id:
            records = [r for r in records if r.user_id == user_id]

        status_by_category = {}
        for record in records:
            cat = record.category.value
            if cat not in status_by_category:
                status_by_category[cat] = {'total': 0, 'by_status': {}}

            status_by_category[cat]['total'] += 1
            status = record.status
            status_by_category[cat]['by_status'][status] = status_by_category[cat]['by_status'].get(status, 0) + 1

        return {
            'total_records': len(records),
            'by_category': status_by_category,
            'stats': self.stats.copy(),
            'generated_at': datetime.now().isoformat()
        }

    def get_expiring_soon(self, days: int = 30) -> List[Dict[str, Any]]:
        """Obtener registros que expiran pronto."""
        cutoff_date = datetime.now() + timedelta(days=days)

        expiring = []
        for record in self.retention_records.values():
            if record.status == 'active' and record.retention_until <= cutoff_date:
                expiring.append({
                    'record_id': record.record_id,
                    'category': record.category.value,
                    'user_id': record.user_id,
                    'expires_in_days': (record.retention_until - datetime.now()).days,
                    'data_location': record.data_location
                })

        return sorted(expiring, key=lambda x: x['expires_in_days'])


# Instancia global del retention manager
_retention_manager = DataRetentionManager()


def get_retention_manager() -> DataRetentionManager:
    """Obtener instancia global del retention manager."""
    return _retention_manager


# Decorador para registrar automáticamente datos con políticas de retención
def retention_tracked(category: DataCategory, user_id_param: str = 'user_id'):
    """Decorador para trackear automáticamente retención de datos."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Ejecutar función
            result = await func(*args, **kwargs)

            # Extraer user_id de parámetros
            user_id = kwargs.get(user_id_param)
            if not user_id and args:
                # Intentar encontrar user_id en args (índice 1 típicamente para métodos de instancia)
                if len(args) > 1 and hasattr(args[1], 'user_id'):
                    user_id = args[1].user_id

            if user_id:
                # Registrar en retention manager
                data_location = f"{func.__module__}.{func.__qualname__}"
                _retention_manager.register_data_record(
                    category=category,
                    user_id=user_id,
                    data_location=data_location,
                    metadata={'function': func.__name__, 'module': func.__module__}
                )

            return result
        return wrapper
    return decorator