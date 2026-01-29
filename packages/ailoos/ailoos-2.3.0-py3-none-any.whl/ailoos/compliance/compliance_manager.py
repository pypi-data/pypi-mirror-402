"""
ComplianceManager - Gestor completo de compliance para FASE 8.

Integra todos los componentes de compliance:
- GDPRManager: Gestión de GDPR
- HIPAAManager: Gestión de HIPAA
- SOXManager: Gestión de SOX
- DataSubjectRights: Derechos del interesado
- ComplianceAuditor: Auditor automático
- DataRetentionManager: Gestión de retención
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from .gdpr_manager import GDPRManager
from .hipaa_manager import HIPAAManager
from .sox_manager import SOXManager
from .data_subject_rights import DataSubjectRights
from .compliance_auditor import ComplianceAuditor, AuditType, ComplianceRisk
from .data_retention_manager import DataRetentionManager, RetentionRegulation, DataCategory
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ComplianceStatus:
    """Estado general de compliance."""
    overall_score: float = 0.0
    gdpr_compliant: bool = True
    hipaa_compliant: bool = True
    sox_compliant: bool = True
    data_retention_compliant: bool = True
    last_audit_date: Optional[datetime] = None
    next_audit_date: Optional[datetime] = None
    critical_issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ComplianceManager:
    """
    Gestor completo de compliance para AILOOS - FASE 8.

    Coordina todos los aspectos de compliance:
    - Privacidad de datos (GDPR)
    - Datos médicos (HIPAA)
    - Controles financieros (SOX)
    - Derechos del interesado
    - Auditorías automáticas
    - Gestión de retención de datos
    """

    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session

        # Componentes de compliance
        self.gdpr_manager = GDPRManager(db_session)
        self.hipaa_manager = HIPAAManager(db_session)
        self.sox_manager = SOXManager(db_session)
        self.data_subject_rights = DataSubjectRights(db_session)
        self.compliance_auditor = ComplianceAuditor(db_session)
        self.data_retention_manager = DataRetentionManager(db_session)

        # Estado del sistema
        self.status = ComplianceStatus()
        self._initialized = False
        self._background_tasks_running = False

    def initialize(self):
        """Inicializar todos los componentes de compliance."""
        if not self._initialized:
            logger.info("🚀 Inicializando ComplianceManager completo...")

            # Inicializar componentes
            self.gdpr_manager.initialize()
            self.hipaa_manager.initialize()
            self.sox_manager.initialize()
            self.data_subject_rights.initialize()
            self.compliance_auditor.initialize()
            self.data_retention_manager.initialize()

            # Programar auditorías automáticas
            self._schedule_automated_audits()

            # Iniciar tareas en background
            asyncio.create_task(self._start_background_tasks())

            self._initialized = True
            logger.info("✅ ComplianceManager completamente inicializado")

    async def _start_background_tasks(self):
        """Iniciar tareas en background."""
        if self._background_tasks_running:
            return

        self._background_tasks_running = True

        # Tarea de monitoreo continuo
        asyncio.create_task(self._continuous_monitoring())

        # Tarea de limpieza automática de datos
        asyncio.create_task(self._automated_data_cleanup())

        logger.info("🔄 Tareas de background iniciadas")

    async def _continuous_monitoring(self):
        """Monitoreo continuo del estado de compliance."""
        while self._background_tasks_running:
            try:
                await self._update_compliance_status()
                await asyncio.sleep(3600)  # Cada hora
            except Exception as e:
                logger.error(f"Error en monitoreo continuo: {e}")
                await asyncio.sleep(300)  # Reintentar en 5 minutos

    async def _automated_data_cleanup(self):
        """Limpieza automática de datos expirados."""
        while self._background_tasks_running:
            try:
                # Verificar datos para eliminación
                data_to_delete = self.data_retention_manager.check_data_for_deletion()

                if data_to_delete:
                    record_ids = [item["record_id"] for item in data_to_delete]
                    scheduled = self.data_retention_manager.schedule_deletion(record_ids, "system")

                    if scheduled:
                        logger.info(f"🗑️ Programados {len(scheduled)} registros para eliminación automática")

                await asyncio.sleep(86400)  # Una vez al día
            except Exception as e:
                logger.error(f"Error en limpieza automática: {e}")
                await asyncio.sleep(3600)  # Reintentar en 1 hora

    def _schedule_automated_audits(self):
        """Programar auditorías automáticas."""
        now = datetime.now()

        # Auditoría semanal completa
        weekly_audit = now + timedelta(days=7)
        self.compliance_auditor.schedule_audit(
            AuditType.SCHEDULED,
            ["GDPR", "HIPAA", "SOX"],
            "Weekly comprehensive audit",
            weekly_audit,
            "system"
        )

        # Auditoría mensual de retención
        monthly_audit = now + timedelta(days=30)
        self.compliance_auditor.schedule_audit(
            AuditType.SCHEDULED,
            ["GDPR", "HIPAA", "SOX"],
            "Monthly data retention audit",
            monthly_audit,
            "system"
        )

        logger.info("📅 Auditorías automáticas programadas")

    async def _update_compliance_status(self):
        """Actualizar estado general de compliance."""
        try:
            # Obtener dashboard del auditor
            dashboard = self.compliance_auditor.get_compliance_dashboard()

            # Calcular puntuación general
            overall_score = dashboard.get("overall_compliance_score", 0.0) * 100

            # Verificar cumplimiento por regulación
            gdpr_compliant = self._check_gdpr_compliance()
            hipaa_compliant = self._check_hipaa_compliance()
            sox_compliant = self._check_sox_compliance()
            retention_compliant = self._check_retention_compliance()

            # Identificar issues críticos
            critical_issues = []
            warnings = []

            if not gdpr_compliant:
                critical_issues.append("GDPR compliance issues detected")
            if not hipaa_compliant:
                critical_issues.append("HIPAA compliance issues detected")
            if not sox_compliant:
                critical_issues.append("SOX compliance issues detected")
            if not retention_compliant:
                warnings.append("Data retention policy violations")

            # Issues del dashboard
            open_findings = dashboard.get("open_findings_by_severity", {})
            if open_findings.get("critical", 0) > 0:
                critical_issues.append(f"{open_findings['critical']} critical audit findings")
            if open_findings.get("high", 0) > 0:
                warnings.append(f"{open_findings['high']} high severity findings")

            # Actualizar estado
            self.status.overall_score = overall_score
            self.status.gdpr_compliant = gdpr_compliant
            self.status.hipaa_compliant = hipaa_compliant
            self.status.sox_compliant = sox_compliant
            self.status.data_retention_compliant = retention_compliant
            self.status.last_audit_date = datetime.now()
            self.status.critical_issues = critical_issues
            self.status.warnings = warnings

            logger.info(f"📊 Compliance status updated: {overall_score:.1f}% overall score")

        except Exception as e:
            logger.error(f"Error updating compliance status: {e}")

    def _check_gdpr_compliance(self) -> bool:
        """Verificar cumplimiento GDPR básico."""
        # TODO: Implementar verificación real
        # Por ahora, simular cumplimiento
        return True

    def _check_hipaa_compliance(self) -> bool:
        """Verificar cumplimiento HIPAA básico."""
        # TODO: Implementar verificación real
        return True

    def _check_sox_compliance(self) -> bool:
        """Verificar cumplimiento SOX básico."""
        # TODO: Implementar verificación real
        return True

    def _check_retention_compliance(self) -> bool:
        """Verificar cumplimiento de retención de datos."""
        report = self.data_retention_manager.get_retention_report()
        expired_records = report.get("expired_records", 0)
        return expired_records == 0

    # === MÉTODOS DE ACCESO A COMPONENTES ===

    # GDPR
    def grant_gdpr_consent(self, user_id: str, purpose: str, **kwargs) -> str:
        """Otorgar consentimiento GDPR."""
        return self.gdpr_manager.grant_consent(user_id, purpose, **kwargs)

    def withdraw_gdpr_consent(self, user_id: str, purpose: str) -> bool:
        """Retirar consentimiento GDPR."""
        return self.gdpr_manager.withdraw_consent(user_id, purpose)

    def check_gdpr_consent(self, user_id: str, purpose: str) -> bool:
        """Verificar consentimiento GDPR."""
        return self.gdpr_manager.check_consent(user_id, purpose)

    def right_to_be_forgotten(self, user_id: str) -> Dict[str, Any]:
        """Aplicar derecho al olvido."""
        return self.gdpr_manager.right_to_be_forgotten(user_id)

    def export_user_data(self, user_id: str, format: str = "json") -> Dict[str, Any]:
        """Exportar datos del usuario."""
        return self.gdpr_manager.export_user_data(user_id, format)

    # HIPAA
    def request_phi_access(self, patient_id: str, accessor_id: str, accessor_role: str,
                          purpose: str, data_requested: List[str], **kwargs) -> Tuple[str, str]:
        """Solicitar acceso a PHI."""
        from .hipaa_manager import AccessPurpose
        purpose_enum = AccessPurpose(purpose)
        result, message = self.hipaa_manager.request_phi_access(
            patient_id, accessor_id, accessor_role, purpose_enum, data_requested, **kwargs
        )
        return result.value, message

    def report_breach(self, patient_ids: List[str], data_breached: List[str],
                     breach_date: datetime, risk_assessment: str, **kwargs) -> str:
        """Reportar brecha de seguridad."""
        return self.hipaa_manager.report_security_breach(
            patient_ids, data_breached, breach_date, risk_assessment, **kwargs
        )

    # SOX
    def record_financial_transaction(self, transaction_type: str, amount: float,
                                   currency: str, initiator: str, description: str, **kwargs) -> str:
        """Registrar transacción financiera."""
        from .sox_manager import TransactionType
        tx_type = TransactionType(transaction_type)
        return self.sox_manager.record_financial_transaction(
            tx_type, amount, currency, initiator, description, **kwargs
        )

    def approve_transaction(self, transaction_id: str, approver: str) -> bool:
        """Aprobar transacción financiera."""
        return self.sox_manager.approve_transaction(transaction_id, approver)

    # Data Subject Rights
    def submit_data_right_request(self, user_id: str, right: str, **kwargs) -> str:
        """Enviar solicitud de derecho del interesado."""
        from .data_subject_rights import DataSubjectRight
        right_enum = DataSubjectRight(right)
        return self.data_subject_rights.submit_request(user_id, right_enum, **kwargs)

    def process_data_right_request(self, request_id: str, assigned_to: str, status: str, **kwargs) -> bool:
        """Procesar solicitud de derecho."""
        from .data_subject_rights import RequestStatus
        status_enum = RequestStatus(status)
        return self.data_subject_rights.process_request(request_id, assigned_to, status_enum, **kwargs)

    # Compliance Auditor
    def start_compliance_audit(self, audit_type: str, regulations: List[str], scope: str, **kwargs) -> str:
        """Iniciar auditoría."""
        audit_type_enum = AuditType(audit_type)
        return self.compliance_auditor.start_audit(audit_type_enum, regulations, scope, **kwargs)

    def get_audit_report(self, audit_id: str) -> Optional[Dict[str, Any]]:
        """Obtener reporte de auditoría."""
        return self.compliance_auditor.get_audit_report(audit_id)

    def get_compliance_dashboard(self) -> Dict[str, Any]:
        """Obtener dashboard de compliance."""
        return self.compliance_auditor.get_compliance_dashboard()

    # Data Retention
    def register_data_for_retention(self, user_id: Optional[str], data_category: str,
                                  regulation: str, **kwargs) -> str:
        """Registrar datos para retención."""
        category = DataCategory(data_category)
        reg = RetentionRegulation(regulation)
        return self.data_retention_manager.register_data(user_id, category, reg, **kwargs)

    def check_data_deletion_readiness(self) -> List[Dict[str, Any]]:
        """Verificar datos listos para eliminación."""
        return self.data_retention_manager.check_data_for_deletion()

    def schedule_data_deletion(self, record_ids: List[str], **kwargs) -> List[str]:
        """Programar eliminación de datos."""
        return self.data_retention_manager.schedule_deletion(record_ids, **kwargs)

    def get_retention_report(self, **kwargs) -> Dict[str, Any]:
        """Obtener reporte de retención."""
        return self.data_retention_manager.get_retention_report(**kwargs)

    # === MÉTODOS DE ESTADO Y REPORTING ===

    def get_compliance_status(self) -> Dict[str, Any]:
        """Obtener estado completo de compliance."""
        return {
            "overall_score": self.status.overall_score,
            "regulatory_compliance": {
                "gdpr": self.status.gdpr_compliant,
                "hipaa": self.status.hipaa_compliant,
                "sox": self.status.sox_compliant,
                "data_retention": self.status.data_retention_compliant
            },
            "last_audit_date": self.status.last_audit_date.isoformat() if self.status.last_audit_date else None,
            "next_audit_date": self.status.next_audit_date.isoformat() if self.status.next_audit_date else None,
            "critical_issues": self.status.critical_issues,
            "warnings": self.status.warnings,
            "components_status": {
                "gdpr_manager": self.gdpr_manager._initialized,
                "hipaa_manager": self.hipaa_manager._initialized,
                "sox_manager": self.sox_manager._initialized,
                "data_subject_rights": self.data_subject_rights._initialized,
                "compliance_auditor": self.compliance_auditor._initialized,
                "data_retention_manager": self.data_retention_manager._initialized
            },
            "generated_at": datetime.now().isoformat()
        }

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """
        Generar reporte completo de compliance.

        Returns:
            Reporte completo con todos los aspectos
        """
        report = {
            "compliance_status": self.get_compliance_status(),
            "audit_dashboard": self.get_compliance_dashboard(),
            "data_subject_rights_report": self.data_subject_rights.generate_compliance_report(),
            "retention_report": self.get_retention_report(),
            "generated_at": datetime.now().isoformat()
        }

        return report

    def shutdown(self):
        """Apagar el gestor de compliance."""
        logger.info("🛑 Apagando ComplianceManager...")
        self._background_tasks_running = False
        logger.info("✅ ComplianceManager apagado")