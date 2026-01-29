"""
DataRetentionManager - Gestión de retención de datos por regulación.

Implementa:
- Políticas de retención por regulación
- Programación automática de eliminación
- Auditoría de retención de datos
- Cumplimiento de períodos mínimos/máximos
- Gestión de excepciones de retención
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from sqlalchemy.orm import Session

from ..utils.logging import get_logger

logger = get_logger(__name__)


class RetentionRegulation(Enum):
    """Regulaciones de retención."""
    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOX = "sox"
    CCPA = "ccpa"
    GENERAL = "general"


class DataCategory(Enum):
    """Categorías de datos."""
    PERSONAL = "personal"
    HEALTH = "health"
    FINANCIAL = "financial"
    COMMUNICATION = "communication"
    LOGS = "logs"
    BACKUP = "backup"


@dataclass
class RetentionPolicy:
    """Política de retención de datos."""
    policy_id: str
    regulation: RetentionRegulation
    data_category: DataCategory
    retention_period_days: int
    minimum_retention_days: Optional[int] = None
    maximum_retention_days: Optional[int] = None
    auto_delete: bool = True
    legal_hold: bool = False
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataRetentionRecord:
    """Registro de retención de datos."""
    record_id: str
    user_id: Optional[str]
    data_category: DataCategory
    regulation: RetentionRegulation
    created_at: datetime
    retention_until: datetime
    last_accessed: Optional[datetime] = None
    deletion_scheduled: bool = False
    deletion_date: Optional[datetime] = None
    legal_hold: bool = False
    hold_reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetentionException:
    """Excepción de retención."""
    exception_id: str
    record_id: str
    exception_type: str  # "extension", "legal_hold", "manual_override"
    requested_by: str
    approved_by: Optional[str] = None
    original_retention_until: datetime
    new_retention_until: datetime
    reason: str = ""
    approved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DataRetentionManager:
    """
    Gestor de retención de datos por regulación.

    Gestiona políticas de retención, programaciones de eliminación
    y cumplimiento de requisitos regulatorios.
    """

    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session
        self.policies: Dict[str, RetentionPolicy] = {}
        self.retention_records: Dict[str, DataRetentionRecord] = {}
        self.retention_exceptions: Dict[str, RetentionException] = {}
        self._initialized = False

    def initialize(self):
        """Inicializar el gestor de retención."""
        if not self._initialized:
            self._load_policies_from_db()
            self._load_retention_records_from_db()
            self._load_exceptions_from_db()
            self._initialize_default_policies()
            self._initialized = True
            logger.info("✅ DataRetentionManager inicializado")

    def _initialize_default_policies(self):
        """Inicializar políticas por defecto."""
        default_policies = [
            # GDPR
            {
                "policy_id": "gdpr_personal_data",
                "regulation": RetentionRegulation.GDPR,
                "data_category": DataCategory.PERSONAL,
                "retention_period_days": 2555,  # 7 años
                "minimum_retention_days": 365,
                "auto_delete": True,
                "description": "GDPR personal data retention"
            },
            {
                "policy_id": "gdpr_consent_logs",
                "regulation": RetentionRegulation.GDPR,
                "data_category": DataCategory.LOGS,
                "retention_period_days": 1825,  # 5 años
                "auto_delete": True,
                "description": "GDPR consent and processing logs"
            },
            # HIPAA
            {
                "policy_id": "hipaa_medical_records",
                "regulation": RetentionRegulation.HIPAA,
                "data_category": DataCategory.HEALTH,
                "retention_period_days": 2555,  # 7 años from discharge
                "minimum_retention_days": 1825,  # 5 años
                "auto_delete": False,  # Manual review required
                "description": "HIPAA medical records retention"
            },
            {
                "policy_id": "hipaa_audit_logs",
                "regulation": RetentionRegulation.HIPAA,
                "data_category": DataCategory.LOGS,
                "retention_period_days": 1825,  # 5 años
                "auto_delete": True,
                "description": "HIPAA audit logs retention"
            },
            # SOX
            {
                "policy_id": "sox_financial_records",
                "regulation": RetentionRegulation.SOX,
                "data_category": DataCategory.FINANCIAL,
                "retention_period_days": 2555,  # 7 años
                "minimum_retention_days": 1825,  # 5 años
                "auto_delete": False,  # Business records
                "description": "SOX financial records retention"
            },
            # General
            {
                "policy_id": "general_logs",
                "regulation": RetentionRegulation.GENERAL,
                "data_category": DataCategory.LOGS,
                "retention_period_days": 365,  # 1 año
                "auto_delete": True,
                "description": "General application logs"
            }
        ]

        for policy_data in default_policies:
            if policy_data["policy_id"] not in self.policies:
                policy = RetentionPolicy(**policy_data)
                self.policies[policy.policy_id] = policy
                self._save_policy_to_db(policy)

    def _load_policies_from_db(self):
        """Cargar políticas desde DB."""
        # TODO: Implementar carga desde DB
        pass

    def _load_retention_records_from_db(self):
        """Cargar registros de retención desde DB."""
        # TODO: Implementar carga desde DB
        pass

    def _load_exceptions_from_db(self):
        """Cargar excepciones desde DB."""
        # TODO: Implementar carga desde DB
        pass

    def register_data(self, user_id: Optional[str], data_category: DataCategory,
                    regulation: RetentionRegulation, created_at: Optional[datetime] = None) -> str:
        """
        Registrar datos para gestión de retención.

        Args:
            user_id: ID del usuario (None para datos no personales)
            data_category: Categoría de datos
            regulation: Regulación aplicable
            created_at: Fecha de creación

        Returns:
            ID del registro de retención
        """
        if not created_at:
            created_at = datetime.now()

        # Encontrar política aplicable
        policy = self._find_applicable_policy(data_category, regulation)
        if not policy:
            logger.warning(f"No retention policy found for {data_category.value}/{regulation.value}")
            return ""

        # Calcular fecha de retención
        retention_until = created_at + timedelta(days=policy.retention_period_days)

        record_id = f"retention_{data_category.value}_{regulation.value}_{datetime.now().timestamp()}"

        record = DataRetentionRecord(
            record_id=record_id,
            user_id=user_id,
            data_category=data_category,
            regulation=regulation,
            created_at=created_at,
            retention_until=retention_until,
            legal_hold=policy.legal_hold
        )

        self.retention_records[record_id] = record
        self._save_retention_record_to_db(record)

        logger.info(f"📋 Data registered for retention: {record_id} until {retention_until.isoformat()}")
        return record_id

    def check_data_for_deletion(self) -> List[Dict[str, Any]]:
        """
        Verificar datos que deben eliminarse.

        Returns:
            Lista de datos listos para eliminación
        """
        now = datetime.now()
        ready_for_deletion = []

        for record in self.retention_records.values():
            if record.deletion_scheduled or record.legal_hold:
                continue

            if record.retention_until <= now:
                # Verificar excepciones
                active_exceptions = [e for e in self.retention_exceptions.values()
                                   if e.record_id == record.record_id
                                   and e.new_retention_until > now]

                if not active_exceptions:
                    ready_for_deletion.append({
                        "record_id": record.record_id,
                        "user_id": record.user_id,
                        "data_category": record.data_category.value,
                        "regulation": record.regulation.value,
                        "created_at": record.created_at.isoformat(),
                        "retention_until": record.retention_until.isoformat(),
                        "days_overdue": (now - record.retention_until).days
                    })

        return ready_for_deletion

    def schedule_deletion(self, record_ids: List[str], scheduled_by: str) -> List[str]:
        """
        Programar eliminación de datos.

        Args:
            record_ids: IDs de registros a eliminar
            scheduled_by: Usuario que programa

        Returns:
            Lista de IDs programados exitosamente
        """
        scheduled = []

        for record_id in record_ids:
            if record_id in self.retention_records:
                record = self.retention_records[record_id]

                # Verificar si puede eliminarse
                if not self._can_delete_record(record):
                    logger.warning(f"Cannot delete record {record_id}: legal hold or exception")
                    continue

                record.deletion_scheduled = True
                record.deletion_date = datetime.now() + timedelta(days=30)  # 30 días de gracia
                record.metadata["scheduled_by"] = scheduled_by
                record.metadata["scheduled_at"] = datetime.now().isoformat()

                self._update_retention_record_in_db(record)
                scheduled.append(record_id)

                logger.info(f"🗑️ Deletion scheduled for record: {record_id}")

        return scheduled

    def request_retention_extension(self, record_id: str, new_retention_days: int,
                                  requested_by: str, reason: str) -> Optional[str]:
        """
        Solicitar extensión de retención.

        Args:
            record_id: ID del registro
            new_retention_days: Nuevos días de retención
            requested_by: Usuario que solicita
            reason: Razón de la extensión

        Returns:
            ID de la excepción si creada
        """
        if record_id not in self.retention_records:
            logger.error(f"Record not found: {record_id}")
            return None

        record = self.retention_records[record_id]
        policy = self._find_applicable_policy(record.data_category, record.regulation)

        if not policy:
            logger.error(f"No policy found for record {record_id}")
            return None

        # Verificar límites
        new_retention_until = record.created_at + timedelta(days=new_retention_days)

        if policy.maximum_retention_days and new_retention_days > policy.maximum_retention_days:
            logger.error(f"Extension exceeds maximum retention for policy {policy.policy_id}")
            return None

        exception_id = f"exception_{record_id}_{datetime.now().timestamp()}"

        exception = RetentionException(
            exception_id=exception_id,
            record_id=record_id,
            exception_type="extension",
            requested_by=requested_by,
            original_retention_until=record.retention_until,
            new_retention_until=new_retention_until,
            reason=reason
        )

        self.retention_exceptions[exception_id] = exception
        self._save_exception_to_db(exception)

        logger.info(f"⏰ Retention extension requested: {exception_id}")
        return exception_id

    def approve_retention_exception(self, exception_id: str, approved_by: str) -> bool:
        """
        Aprobar excepción de retención.

        Args:
            exception_id: ID de la excepción
            approved_by: Usuario que aprueba

        Returns:
            True si aprobada exitosamente
        """
        if exception_id not in self.retention_exceptions:
            logger.error(f"Exception not found: {exception_id}")
            return False

        exception = self.retention_exceptions[exception_id]
        exception.approved_by = approved_by
        exception.approved_at = datetime.now()

        # Actualizar registro de retención
        if exception.record_id in self.retention_records:
            record = self.retention_records[exception.record_id]
            record.retention_until = exception.new_retention_until
            record.metadata["last_extension"] = exception.approved_at.isoformat()
            self._update_retention_record_in_db(record)

        self._update_exception_in_db(exception)

        logger.info(f"✅ Retention exception approved: {exception_id}")
        return True

    def apply_legal_hold(self, record_ids: List[str], hold_reason: str,
                        applied_by: str) -> List[str]:
        """
        Aplicar retención legal (legal hold).

        Args:
            record_ids: IDs de registros
            hold_reason: Razón del hold
            applied_by: Usuario que aplica

        Returns:
            Lista de IDs con hold aplicado
        """
        applied_holds = []

        for record_id in record_ids:
            if record_id in self.retention_records:
                record = self.retention_records[record_id]
                record.legal_hold = True
                record.hold_reason = hold_reason
                record.metadata["hold_applied_by"] = applied_by
                record.metadata["hold_applied_at"] = datetime.now().isoformat()

                self._update_retention_record_in_db(record)
                applied_holds.append(record_id)

                logger.info(f"⚖️ Legal hold applied to record: {record_id}")

        return applied_holds

    def release_legal_hold(self, record_ids: List[str], released_by: str) -> List[str]:
        """
        Liberar retención legal.

        Args:
            record_ids: IDs de registros
            released_by: Usuario que libera

        Returns:
            Lista de IDs liberados
        """
        released = []

        for record_id in record_ids:
            if record_id in self.retention_records:
                record = self.retention_records[record_id]
                record.legal_hold = False
                record.hold_reason = ""
                record.metadata["hold_released_by"] = released_by
                record.metadata["hold_released_at"] = datetime.now().isoformat()

                self._update_retention_record_in_db(record)
                released.append(record_id)

                logger.info(f"🔓 Legal hold released for record: {record_id}")

        return released

    def get_retention_report(self, regulation: Optional[RetentionRegulation] = None,
                           data_category: Optional[DataCategory] = None) -> Dict[str, Any]:
        """
        Generar reporte de retención.

        Args:
            regulation: Filtrar por regulación
            data_category: Filtrar por categoría

        Returns:
            Reporte de retención
        """
        now = datetime.now()
        report = {
            "total_records": 0,
            "active_records": 0,
            "expired_records": 0,
            "scheduled_for_deletion": 0,
            "legal_hold_records": 0,
            "records_by_regulation": {},
            "records_by_category": {},
            "upcoming_expirations": [],
            "generated_at": now.isoformat()
        }

        for record in self.retention_records.values():
            # Aplicar filtros
            if regulation and record.regulation != regulation:
                continue
            if data_category and record.data_category != data_category:
                continue

            report["total_records"] += 1

            # Contadores
            if record.legal_hold:
                report["legal_hold_records"] += 1
            elif record.deletion_scheduled:
                report["scheduled_for_deletion"] += 1
            elif record.retention_until <= now:
                report["expired_records"] += 1
            else:
                report["active_records"] += 1

            # Agrupaciones
            reg_key = record.regulation.value
            cat_key = record.data_category.value

            report["records_by_regulation"][reg_key] = report["records_by_regulation"].get(reg_key, 0) + 1
            report["records_by_category"][cat_key] = report["records_by_category"].get(cat_key, 0) + 1

            # Expiraciones próximas (30 días)
            days_until_expiry = (record.retention_until - now).days
            if 0 <= days_until_expiry <= 30 and not record.deletion_scheduled and not record.legal_hold:
                report["upcoming_expirations"].append({
                    "record_id": record.record_id,
                    "user_id": record.user_id,
                    "data_category": cat_key,
                    "regulation": reg_key,
                    "retention_until": record.retention_until.isoformat(),
                    "days_until_expiry": days_until_expiry
                })

        # Ordenar expiraciones próximas
        report["upcoming_expirations"].sort(key=lambda x: x["days_until_expiry"])

        return report

    def _find_applicable_policy(self, data_category: DataCategory,
                              regulation: RetentionRegulation) -> Optional[RetentionPolicy]:
        """Encontrar política aplicable."""
        for policy in self.policies.values():
            if policy.data_category == data_category and policy.regulation == regulation:
                return policy
        return None

    def _can_delete_record(self, record: DataRetentionRecord) -> bool:
        """Verificar si un registro puede eliminarse."""
        if record.legal_hold:
            return False

        # Verificar excepciones activas
        active_exceptions = [e for e in self.retention_exceptions.values()
                           if e.record_id == record.record_id
                           and e.approved_at
                           and e.new_retention_until > datetime.now()]

        return len(active_exceptions) == 0

    def _save_policy_to_db(self, policy: RetentionPolicy):
        """Guardar política en DB."""
        # TODO: Implementar persistencia
        pass

    def _save_retention_record_to_db(self, record: DataRetentionRecord):
        """Guardar registro de retención en DB."""
        # TODO: Implementar persistencia
        pass

    def _update_retention_record_in_db(self, record: DataRetentionRecord):
        """Actualizar registro de retención en DB."""
        # TODO: Implementar actualización
        pass

    def _save_exception_to_db(self, exception: RetentionException):
        """Guardar excepción en DB."""
        # TODO: Implementar persistencia
        pass

    def _update_exception_in_db(self, exception: RetentionException):
        """Actualizar excepción en DB."""
        # TODO: Implementar actualización
        pass