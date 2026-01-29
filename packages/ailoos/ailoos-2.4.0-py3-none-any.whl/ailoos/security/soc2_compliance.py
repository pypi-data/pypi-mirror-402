"""
SOC 2 Type II Compliance Framework para AILOOS

Implementa preparación completa para certificación SOC 2 Type II:
- Documentación de controles de seguridad
- Audit trails comprehensivos
- Engagement con auditores externos
- Trust Services Criteria (TSC)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import uuid

logger = logging.getLogger(__name__)


class SOC2TrustServiceCriteria(Enum):
    """Criterios de Servicios de Confianza SOC 2."""
    SECURITY = "security"                    # Seguridad
    AVAILABILITY = "availability"           # Disponibilidad
    PROCESSING_INTEGRITY = "processing_integrity"  # Integridad de procesamiento
    CONFIDENTIALITY = "confidentiality"      # Confidencialidad
    PRIVACY = "privacy"                     # Privacidad


class ControlCategory(Enum):
    """Categorías de controles SOC 2."""
    ACCESS_CONTROL = "access_control"
    CHANGE_MANAGEMENT = "change_management"
    RISK_MANAGEMENT = "risk_management"
    PHYSICAL_SECURITY = "physical_security"
    SYSTEM_OPERATIONS = "system_operations"
    NETWORK_SECURITY = "network_security"
    INCIDENT_RESPONSE = "incident_response"
    BUSINESS_CONTINUITY = "business_continuity"


class ControlStatus(Enum):
    """Estados de controles."""
    IMPLEMENTED = "implemented"
    PARTIALLY_IMPLEMENTED = "partially_implemented"
    PLANNED = "planned"
    NOT_APPLICABLE = "not_applicable"
    INHERITED = "inherited"


class AuditTrailEvent(Enum):
    """Tipos de eventos para audit trails."""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_INCIDENT = "security_incident"
    PRIVILEGE_CHANGE = "privilege_change"
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    BACKUP_COMPLETED = "backup_completed"
    AUDIT_LOG_REVIEW = "audit_log_review"


@dataclass
class SecurityControl:
    """Control de seguridad SOC 2."""
    control_id: str
    name: str
    description: str
    category: ControlCategory
    criteria: Set[SOC2TrustServiceCriteria]
    status: ControlStatus = ControlStatus.IMPLEMENTED
    owner: str = ""
    evidence: List[str] = field(default_factory=list)
    testing_procedures: List[str] = field(default_factory=list)
    exceptions: List[str] = field(default_factory=list)
    last_reviewed: Optional[datetime] = None
    next_review: Optional[datetime] = None
    risk_level: str = "medium"
    implementation_details: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_effective(self) -> bool:
        """Verificar si el control está efectivo."""
        return self.status in [ControlStatus.IMPLEMENTED, ControlStatus.INHERITED]

    @property
    def requires_attention(self) -> bool:
        """Verificar si requiere atención."""
        if self.status == ControlStatus.PARTIALLY_IMPLEMENTED:
            return True
        if self.next_review and datetime.now() > self.next_review:
            return True
        return False


@dataclass
class AuditTrailEntry:
    """Entrada de audit trail."""
    event_id: str
    event_type: AuditTrailEvent
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource: str = ""  # qué recurso fue accedido/modificado
    action: str = ""    # qué acción se realizó
    result: str = "success"  # success, failure, denied
    details: Dict[str, Any] = field(default_factory=dict)
    risk_score: int = 0
    compliance_flags: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para serialización."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'resource': self.resource,
            'action': self.action,
            'result': self.result,
            'details': self.details,
            'risk_score': self.risk_score,
            'compliance_flags': list(self.compliance_flags)
        }


@dataclass
class AuditorEngagement:
    """Engagement con auditor externo."""
    engagement_id: str
    auditor_name: str
    auditor_firm: str
    audit_type: str = "SOC_2_Type_II"
    start_date: datetime = field(default_factory=datetime.now)
    end_date: Optional[datetime] = None
    status: str = "planned"  # planned, in_progress, completed, failed
    scope: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    next_audit_date: Optional[datetime] = None

    @property
    def is_active(self) -> bool:
        """Verificar si el engagement está activo."""
        return self.status in ["planned", "in_progress"]

    @property
    def days_until_completion(self) -> Optional[int]:
        """Días hasta completación."""
        if not self.end_date:
            return None
        return (self.end_date - datetime.now()).days


class SOC2ComplianceManager:
    """
    Gestor de cumplimiento SOC 2 Type II.

    Características:
    - Documentación completa de controles de seguridad
    - Audit trails comprehensivos
    - Preparación para engagement con auditores
    - Trust Services Criteria mapping
    """

    def __init__(self):
        self.controls: Dict[str, SecurityControl] = {}
        self.audit_trails: List[AuditTrailEntry] = []
        self.auditor_engagements: List[AuditorEngagement] = []

        # Configuración
        self.retention_period_days = 365 * 7  # 7 años para SOC 2
        self.max_trail_entries = 1000000  # 1M entradas máximo

        # Estadísticas
        self.stats = {
            'total_controls': 0,
            'implemented_controls': 0,
            'audit_trail_entries': 0,
            'high_risk_events': 0,
            'compliance_violations': 0
        }

        self._initialize_default_controls()
        logger.info("SOC2ComplianceManager initialized")

    def _initialize_default_controls(self):
        """Inicializar controles por defecto SOC 2."""
        default_controls = [
            # Security Criteria
            SecurityControl(
                control_id="SEC-001",
                name="Access Control Policies",
                description="Políticas de control de acceso implementadas y documentadas",
                category=ControlCategory.ACCESS_CONTROL,
                criteria={SOC2TrustServiceCriteria.SECURITY},
                status=ControlStatus.IMPLEMENTED,
                owner="Security Team",
                evidence=["access_control_policy.pdf", "rbac_implementation"],
                testing_procedures=["Review access logs monthly", "Test role-based access"],
                next_review=datetime.now() + timedelta(days=90)
            ),

            SecurityControl(
                control_id="SEC-002",
                name="Encryption at Rest",
                description="Encriptación de datos en reposo",
                category=ControlCategory.NETWORK_SECURITY,
                criteria={SOC2TrustServiceCriteria.SECURITY, SOC2TrustServiceCriteria.CONFIDENTIALITY},
                status=ControlStatus.IMPLEMENTED,
                owner="Infrastructure Team",
                evidence=["encryption_policy.pdf", "gcp_kms_integration"],
                testing_procedures=["Verify encryption keys rotation", "Test backup decryption"],
                next_review=datetime.now() + timedelta(days=180)
            ),

            SecurityControl(
                control_id="SEC-003",
                name="Network Security",
                description="Controles de seguridad de red (firewalls, segmentation)",
                category=ControlCategory.NETWORK_SECURITY,
                criteria={SOC2TrustServiceCriteria.SECURITY},
                status=ControlStatus.IMPLEMENTED,
                owner="DevOps Team",
                evidence=["network_diagram.pdf", "firewall_rules"],
                testing_procedures=["Monthly firewall rule review", "Penetration testing quarterly"],
                next_review=datetime.now() + timedelta(days=90)
            ),

            # Availability Criteria
            SecurityControl(
                control_id="AVA-001",
                name="Business Continuity Plan",
                description="Plan de continuidad de negocio documentado y probado",
                category=ControlCategory.BUSINESS_CONTINUITY,
                criteria={SOC2TrustServiceCriteria.AVAILABILITY},
                status=ControlStatus.IMPLEMENTED,
                owner="Operations Team",
                evidence=["bcp_document.pdf", "disaster_recovery_test_results"],
                testing_procedures=["Annual BCP testing", "Quarterly DR drills"],
                next_review=datetime.now() + timedelta(days=365)
            ),

            SecurityControl(
                control_id="AVA-002",
                name="System Monitoring",
                description="Monitoreo continuo de sistemas y servicios",
                category=ControlCategory.SYSTEM_OPERATIONS,
                criteria={SOC2TrustServiceCriteria.AVAILABILITY},
                status=ControlStatus.IMPLEMENTED,
                owner="DevOps Team",
                evidence=["monitoring_dashboard.pdf", "alert_configuration"],
                testing_procedures=["Weekly monitoring review", "Monthly uptime reports"],
                next_review=datetime.now() + timedelta(days=30)
            ),

            # Processing Integrity Criteria
            SecurityControl(
                control_id="PRI-001",
                name="Data Validation",
                description="Validación de entrada y procesamiento de datos",
                category=ControlCategory.SYSTEM_OPERATIONS,
                criteria={SOC2TrustServiceCriteria.PROCESSING_INTEGRITY},
                status=ControlStatus.IMPLEMENTED,
                owner="Development Team",
                evidence=["input_validation_tests.pdf", "data_processing_logs"],
                testing_procedures=["Automated validation testing", "Manual data integrity checks"],
                next_review=datetime.now() + timedelta(days=90)
            ),

            # Confidentiality Criteria
            SecurityControl(
                control_id="CON-001",
                name="Data Classification",
                description="Clasificación y manejo de datos sensibles",
                category=ControlCategory.RISK_MANAGEMENT,
                criteria={SOC2TrustServiceCriteria.CONFIDENTIALITY},
                status=ControlStatus.IMPLEMENTED,
                owner="Compliance Team",
                evidence=["data_classification_policy.pdf", "sensitivity_labels"],
                testing_procedures=["Annual data classification review", "Access control audits"],
                next_review=datetime.now() + timedelta(days=180)
            ),

            # Privacy Criteria
            SecurityControl(
                control_id="PRV-001",
                name="Privacy Notice",
                description="Aviso de privacidad claro y accesible",
                category=ControlCategory.RISK_MANAGEMENT,
                criteria={SOC2TrustServiceCriteria.PRIVACY},
                status=ControlStatus.IMPLEMENTED,
                owner="Legal Team",
                evidence=["privacy_policy.pdf", "consent_management_system"],
                testing_procedures=["Annual privacy policy review", "User consent verification"],
                next_review=datetime.now() + timedelta(days=365)
            ),

            SecurityControl(
                control_id="PRV-002",
                name="Data Subject Rights",
                description="Implementación de derechos de sujetos de datos",
                category=ControlCategory.RISK_MANAGEMENT,
                criteria={SOC2TrustServiceCriteria.PRIVACY},
                status=ControlStatus.IMPLEMENTED,
                owner="Compliance Team",
                evidence=["gdpr_compliance.pdf", "ccpa_compliance.pdf", "data_portability_api"],
                testing_procedures=["Monthly access request processing", "Annual privacy rights audit"],
                next_review=datetime.now() + timedelta(days=90)
            )
        ]

        for control in default_controls:
            self.controls[control.control_id] = control
            self.stats['total_controls'] += 1
            if control.is_effective:
                self.stats['implemented_controls'] += 1

    def add_security_control(self, control: SecurityControl) -> str:
        """Añadir un control de seguridad."""
        if control.control_id in self.controls:
            raise ValueError(f"Control {control.control_id} already exists")

        self.controls[control.control_id] = control
        self.stats['total_controls'] += 1
        if control.is_effective:
            self.stats['implemented_controls'] += 1

        logger.info(f"Security control added: {control.control_id} - {control.name}")
        return control.control_id

    def update_control_status(self, control_id: str, status: ControlStatus, notes: str = "") -> bool:
        """Actualizar estado de un control."""
        if control_id not in self.controls:
            return False

        control = self.controls[control_id]
        old_status = control.status
        control.status = status
        control.last_reviewed = datetime.now()
        control.next_review = datetime.now() + timedelta(days=90)

        if notes:
            control.implementation_details['status_update_notes'] = notes

        # Actualizar estadísticas
        if old_status != ControlStatus.IMPLEMENTED and status == ControlStatus.IMPLEMENTED:
            self.stats['implemented_controls'] += 1
        elif old_status == ControlStatus.IMPLEMENTED and status != ControlStatus.IMPLEMENTED:
            self.stats['implemented_controls'] -= 1

        # Registrar en audit trail
        self._log_audit_event(
            event_type=AuditTrailEvent.CONFIGURATION_CHANGE,
            resource=f"security_control:{control_id}",
            action="status_update",
            details={
                'old_status': old_status.value,
                'new_status': status.value,
                'notes': notes
            }
        )

        logger.info(f"Control {control_id} status updated: {old_status.value} -> {status.value}")
        return True

    def log_audit_event(self,
                       event_type: AuditTrailEvent,
                       user_id: Optional[str] = None,
                       resource: str = "",
                       action: str = "",
                       result: str = "success",
                       details: Optional[Dict[str, Any]] = None,
                       ip_address: Optional[str] = None,
                       user_agent: Optional[str] = None,
                       session_id: Optional[str] = None) -> str:
        """Registrar evento en audit trail."""
        event_id = f"audit_{uuid.uuid4().hex}"

        entry = AuditTrailEntry(
            event_id=event_id,
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource=resource,
            action=action,
            result=result,
            details=details or {}
        )

        # Calcular risk score
        entry.risk_score = self._calculate_event_risk(entry)

        # Flags de compliance
        entry.compliance_flags = self._check_compliance_flags(entry)

        self.audit_trails.append(entry)
        self.stats['audit_trail_entries'] += 1

        # Actualizar estadísticas de riesgo
        if entry.risk_score >= 7:
            self.stats['high_risk_events'] += 1
        if 'violation' in entry.compliance_flags:
            self.stats['compliance_violations'] += 1

        # Mantener tamaño del audit trail
        if len(self.audit_trails) > self.max_trail_entries:
            # Mantener solo las más recientes
            self.audit_trails = self.audit_trails[-self.max_trail_entries//2:]

        logger.debug(f"Audit event logged: {event_type.value} for user {user_id}")
        return event_id

    def _log_audit_event(self, **kwargs):
        """Método interno para logging de audit events."""
        return self.log_audit_event(**kwargs)

    def _calculate_event_risk(self, entry: AuditTrailEntry) -> int:
        """Calcular score de riesgo para un evento."""
        risk_score = 0

        # Riesgo por tipo de evento
        risk_by_type = {
            AuditTrailEvent.SECURITY_INCIDENT: 10,
            AuditTrailEvent.PRIVILEGE_CHANGE: 8,
            AuditTrailEvent.DATA_MODIFICATION: 6,
            AuditTrailEvent.CONFIGURATION_CHANGE: 7,
            AuditTrailEvent.USER_LOGIN: 2,
            AuditTrailEvent.DATA_ACCESS: 3,
        }

        risk_score += risk_by_type.get(entry.event_type, 1)

        # Riesgo por resultado
        if entry.result == "failure":
            risk_score += 3
        elif entry.result == "denied":
            risk_score += 2

        # Riesgo por usuario (simulado)
        if entry.user_id and len(entry.user_id) > 10:  # IDs largos = potencialmente sospechosos
            risk_score += 1

        return min(risk_score, 10)  # Máximo 10

    def _check_compliance_flags(self, entry: AuditTrailEntry) -> Set[str]:
        """Verificar flags de compliance para un evento."""
        flags = set()

        # SOC 2 relevant flags
        if entry.event_type in [AuditTrailEvent.SECURITY_INCIDENT, AuditTrailEvent.PRIVILEGE_CHANGE]:
            flags.add('security_incident')

        if entry.result == 'denied':
            flags.add('access_denied')

        if entry.risk_score >= 7:
            flags.add('high_risk')

        if entry.event_type == AuditTrailEvent.CONFIGURATION_CHANGE:
            flags.add('change_management')

        # Violations
        if entry.event_type == AuditTrailEvent.SECURITY_INCIDENT:
            flags.add('violation')

        return flags

    def get_audit_trail(self,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None,
                       event_types: Optional[List[AuditTrailEvent]] = None,
                       user_id: Optional[str] = None,
                       min_risk_score: int = 0,
                       limit: int = 1000) -> List[Dict[str, Any]]:
        """Obtener audit trail filtrado."""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        filtered_trails = []

        for entry in self.audit_trails:
            if entry.timestamp < start_date or entry.timestamp > end_date:
                continue
            if event_types and entry.event_type not in event_types:
                continue
            if user_id and entry.user_id != user_id:
                continue
            if entry.risk_score < min_risk_score:
                continue

            filtered_trails.append(entry.to_dict())

        # Ordenar por timestamp descendente
        filtered_trails.sort(key=lambda x: x['timestamp'], reverse=True)

        return filtered_trails[:limit]

    def get_security_controls_report(self) -> Dict[str, Any]:
        """Generar reporte de controles de seguridad."""
        controls_by_category = {}
        controls_by_criteria = {}
        controls_by_status = {}

        for control in self.controls.values():
            # Por categoría
            cat = control.category.value
            if cat not in controls_by_category:
                controls_by_category[cat] = []
            controls_by_category[cat].append({
                'id': control.control_id,
                'name': control.name,
                'status': control.status.value,
                'is_effective': control.is_effective
            })

            # Por criteria
            for criteria in control.criteria:
                crit = criteria.value
                if crit not in controls_by_criteria:
                    controls_by_criteria[crit] = []
                controls_by_criteria[crit].append(control.control_id)

            # Por status
            status = control.status.value
            if status not in controls_by_status:
                controls_by_status[status] = 0
            controls_by_status[status] += 1

        # Controles que requieren atención
        attention_required = [
            {
                'id': control.control_id,
                'name': control.name,
                'status': control.status.value,
                'next_review': control.next_review.isoformat() if control.next_review else None
            }
            for control in self.controls.values()
            if control.requires_attention
        ]

        return {
            'summary': {
                'total_controls': len(self.controls),
                'implemented_controls': sum(1 for c in self.controls.values() if c.is_effective),
                'attention_required': len(attention_required),
                'implementation_rate': round(sum(1 for c in self.controls.values() if c.is_effective) / len(self.controls) * 100, 2)
            },
            'controls_by_category': controls_by_category,
            'controls_by_criteria': controls_by_criteria,
            'controls_by_status': controls_by_status,
            'attention_required': attention_required,
            'generated_at': datetime.now().isoformat()
        }

    def engage_external_auditor(self,
                              auditor_name: str,
                              auditor_firm: str,
                              start_date: datetime,
                              end_date: datetime,
                              scope: List[str]) -> str:
        """Iniciar engagement con auditor externo."""
        engagement_id = f"audit_{uuid.uuid4().hex[:8]}"

        engagement = AuditorEngagement(
            engagement_id=engagement_id,
            auditor_name=auditor_name,
            auditor_firm=auditor_firm,
            start_date=start_date,
            end_date=end_date,
            scope=scope,
            deliverables=[
                "SOC 2 Type II Report",
                "Management Assertion Letter",
                "Control Testing Results",
                "Findings and Recommendations"
            ]
        )

        self.auditor_engagements.append(engagement)

        # Registrar en audit trail
        self._log_audit_event(
            event_type=AuditTrailEvent.CONFIGURATION_CHANGE,
            resource=f"auditor_engagement:{engagement_id}",
            action="engagement_created",
            details={
                'auditor_name': auditor_name,
                'auditor_firm': auditor_firm,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        )

        logger.info(f"External auditor engagement created: {engagement_id} with {auditor_firm}")
        return engagement_id

    def get_auditor_engagements(self) -> List[Dict[str, Any]]:
        """Obtener engagements con auditores."""
        return [
            {
                'engagement_id': e.engagement_id,
                'auditor_name': e.auditor_name,
                'auditor_firm': e.auditor_firm,
                'audit_type': e.audit_type,
                'start_date': e.start_date.isoformat(),
                'end_date': e.end_date.isoformat() if e.end_date else None,
                'status': e.status,
                'scope': e.scope,
                'days_until_completion': e.days_until_completion
            }
            for e in self.auditor_engagements
        ]

    def get_soc2_readiness_report(self) -> Dict[str, Any]:
        """Generar reporte de preparación SOC 2."""
        controls_report = self.get_security_controls_report()

        # Calcular readiness score
        implementation_rate = controls_report['summary']['implementation_rate']
        attention_items = controls_report['summary']['attention_required']

        readiness_score = implementation_rate

        # Penalizar por items que requieren atención
        readiness_score -= (attention_items * 2)

        # Penalizar por audit trail issues
        if self.stats['compliance_violations'] > 0:
            readiness_score -= 5

        readiness_score = max(0, min(100, readiness_score))

        # Determinar nivel de readiness
        if readiness_score >= 90:
            readiness_level = "Ready for Audit"
        elif readiness_score >= 75:
            readiness_level = "Good Progress"
        elif readiness_score >= 60:
            readiness_level = "Needs Improvement"
        else:
            readiness_level = "Not Ready"

        return {
            'readiness_score': round(readiness_score, 1),
            'readiness_level': readiness_level,
            'assessment_date': datetime.now().isoformat(),
            'valid_until': (datetime.now() + timedelta(days=90)).isoformat(),
            'key_metrics': {
                'controls_implemented': controls_report['summary']['implemented_controls'],
                'total_controls': controls_report['summary']['total_controls'],
                'attention_required': controls_report['summary']['attention_required'],
                'audit_trail_entries': self.stats['audit_trail_entries'],
                'compliance_violations': self.stats['compliance_violations'],
                'high_risk_events': self.stats['high_risk_events']
            },
            'recommendations': self._generate_readiness_recommendations(readiness_score),
            'next_steps': [
                "Complete implementation of controls requiring attention",
                "Address any compliance violations identified",
                "Prepare evidence documentation for each control",
                "Conduct internal control testing",
                "Schedule external auditor engagement"
            ] if readiness_score < 90 else [
                "Schedule SOC 2 audit with external auditor",
                "Prepare management assertion letter",
                "Gather all evidence documentation",
                "Conduct pre-audit readiness assessment"
            ]
        }

    def _generate_readiness_recommendations(self, readiness_score: float) -> List[str]:
        """Generar recomendaciones de preparación."""
        recommendations = []

        if readiness_score < 60:
            recommendations.extend([
                "Implement missing security controls immediately",
                "Establish comprehensive audit trail logging",
                "Develop incident response procedures",
                "Create business continuity and disaster recovery plans"
            ])

        elif readiness_score < 75:
            recommendations.extend([
                "Complete partial control implementations",
                "Enhance monitoring and alerting capabilities",
                "Strengthen access control mechanisms",
                "Improve documentation and evidence collection"
            ])

        elif readiness_score < 90:
            recommendations.extend([
                "Conduct internal control testing",
                "Review and update policies and procedures",
                "Enhance audit trail analysis capabilities",
                "Prepare detailed control evidence documentation"
            ])

        else:
            recommendations.extend([
                "Schedule external auditor kickoff meeting",
                "Prepare control testing schedules",
                "Review subcontractor and vendor controls",
                "Conduct final readiness assessment"
            ])

        return recommendations

    def get_compliance_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas generales de compliance."""
        return {
            **self.stats,
            'audit_trail_retention_days': self.retention_period_days,
            'controls_implementation_rate': round(self.stats['implemented_controls'] / self.stats['total_controls'] * 100, 2) if self.stats['total_controls'] > 0 else 0,
            'active_auditor_engagements': len([e for e in self.auditor_engagements if e.is_active]),
            'generated_at': datetime.now().isoformat()
        }


# Instancias globales
_soc2_manager = SOC2ComplianceManager()


def get_soc2_compliance_manager() -> SOC2ComplianceManager:
    """Obtener instancia global del SOC 2 compliance manager."""
    return _soc2_manager


# Funciones de conveniencia

def log_security_event(event_type: AuditTrailEvent, **kwargs) -> str:
    """Registrar evento de seguridad en audit trail."""
    return _soc2_manager.log_audit_event(event_type=event_type, **kwargs)


def get_security_controls_report() -> Dict[str, Any]:
    """Obtener reporte de controles de seguridad."""
    return _soc2_manager.get_security_controls_report()


def get_soc2_readiness() -> Dict[str, Any]:
    """Obtener estado de preparación SOC 2."""
    return _soc2_manager.get_soc2_readiness_report()


def engage_auditor(auditor_name: str, auditor_firm: str, start_date: datetime, end_date: datetime, scope: List[str]) -> str:
    """Iniciar engagement con auditor."""
    return _soc2_manager.engage_external_auditor(auditor_name, auditor_firm, start_date, end_date, scope)