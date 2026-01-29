"""
Audit Event definitions and data structures.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class AuditEventType(Enum):
    """Types of events that can be audited."""
    # Authentication & Authorization
    LOGIN = "login"
    LOGOUT = "logout"
    AUTH_FAILED = "auth_failed"
    PERMISSION_CHANGE = "permission_change"

    # Data Operations
    DATA_ACCESS = "data_access"
    DATA_MODIFY = "data_modify"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"

    # System Operations
    CONFIG_CHANGE = "config_change"
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    BACKUP_START = "backup_start"
    BACKUP_COMPLETE = "backup_complete"

    # Security Events
    SECURITY_ALERT = "security_alert"
    INTRUSION_DETECTED = "intrusion_detected"
    MALWARE_DETECTED = "malware_detected"
    POLICY_VIOLATION = "policy_violation"

    # Business Logic
    TRANSACTION = "transaction"
    MODEL_TRAINING = "model_training"
    INFERENCE_REQUEST = "inference_request"
    FEDERATED_OPERATION = "federated_operation"

    # Compliance
    COMPLIANCE_CHECK = "compliance_check"
    AUDIT_REVIEW = "audit_review"
    RETENTION_POLICY = "retention_policy"


class AuditSeverity(Enum):
    """Severity levels for audit events."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """
    Structured audit event with comprehensive metadata.
    """
    event_type: AuditEventType
    event_id: str
    timestamp: datetime
    resource: str
    action: str

    # Optional fields
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tenant_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    severity: AuditSeverity = AuditSeverity.INFO
    success: bool = True
    details: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    processing_time_ms: Optional[float] = None
    checksum: Optional[str] = None
    correlation_id: Optional[str] = None

    # Metadata for advanced features
    location: Optional[str] = None  # Geographic location
    device_info: Optional[Dict[str, Any]] = None
    compliance_flags: List[str] = field(default_factory=list)
    risk_score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_type": self.event_type.value,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "resource": self.resource,
            "action": self.action,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "tenant_id": self.tenant_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "severity": self.severity.value,
            "success": self.success,
            "details": self.details,
            "tags": self.tags,
            "processing_time_ms": self.processing_time_ms,
            "checksum": self.checksum,
            "correlation_id": self.correlation_id,
            "location": self.location,
            "device_info": self.device_info,
            "compliance_flags": self.compliance_flags,
            "risk_score": self.risk_score
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEvent':
        """Create AuditEvent from dictionary."""
        # Handle enum conversions
        event_type = AuditEventType(data['event_type'])
        severity = AuditSeverity(data.get('severity', 'info'))

        # Handle timestamp
        timestamp = datetime.fromisoformat(data['timestamp']) if isinstance(data['timestamp'], str) else data['timestamp']

        return cls(
            event_type=event_type,
            event_id=data['event_id'],
            timestamp=timestamp,
            resource=data['resource'],
            action=data['action'],
            user_id=data.get('user_id'),
            session_id=data.get('session_id'),
            tenant_id=data.get('tenant_id'),
            ip_address=data.get('ip_address'),
            user_agent=data.get('user_agent'),
            severity=severity,
            success=data.get('success', True),
            details=data.get('details', {}),
            tags=data.get('tags', []),
            processing_time_ms=data.get('processing_time_ms'),
            checksum=data.get('checksum'),
            correlation_id=data.get('correlation_id'),
            location=data.get('location'),
            device_info=data.get('device_info'),
            compliance_flags=data.get('compliance_flags', []),
            risk_score=data.get('risk_score')
        )

    def add_tag(self, tag: str):
        """Add a tag to the event."""
        if tag not in self.tags:
            self.tags.append(tag)

    def add_compliance_flag(self, flag: str):
        """Add a compliance flag."""
        if flag not in self.compliance_flags:
            self.compliance_flags.append(flag)

    def calculate_risk_score(self) -> float:
        """Calculate a risk score based on event characteristics."""
        score = 0.0

        # Base score by severity
        severity_scores = {
            AuditSeverity.DEBUG: 0.1,
            AuditSeverity.INFO: 0.2,
            AuditSeverity.WARNING: 0.5,
            AuditSeverity.ERROR: 0.8,
            AuditSeverity.CRITICAL: 1.0
        }
        score += severity_scores[self.severity]

        # Adjust for failure
        if not self.success:
            score += 0.3

        # Adjust for sensitive resources
        sensitive_resources = ['password', 'key', 'secret', 'admin', 'root']
        if any(sensitive in self.resource.lower() for sensitive in sensitive_resources):
            score += 0.4

        # Adjust for high-risk actions
        high_risk_actions = ['delete', 'modify', 'export', 'grant']
        if any(risk in self.action.lower() for risk in high_risk_actions):
            score += 0.3

        # Cap at 1.0
        self.risk_score = min(score, 1.0)
        return self.risk_score

    def __str__(self) -> str:
        """String representation of the audit event."""
        return f"[{self.timestamp}] {self.event_type.value}: {self.resource}:{self.action} by {self.user_id or 'system'} ({'success' if self.success else 'failed'})"