"""
Sistema de auditoría y logging completo para AILOOS.
Incluye logging estructurado, auditoría de cambios, monitoreo de seguridad,
blockchain privada, smart contracts y reportes de compliance.
"""

from .audit_manager import (
    AuditManager,
    AuditEvent,
    AuditEventType,
    SecurityAlert,
    SecurityAlertLevel,
    SystemMetrics,
    get_audit_manager
)

from .structured_logger import (
    StructuredLogger,
    LogContext,
    get_structured_logger,
    log_api_request,
    log_security_event,
    log_config_change,
    log_user_action,
    log_performance,
    log_operation
)

from .security_monitor import (
    SecurityMonitor,
    SecurityRule,
    ThreatIndicator,
    get_security_monitor
)

from .metrics_collector import (
    MetricsCollector,
    PerformanceMetrics,
    ResourceMetrics,
    ApplicationMetrics,
    HealthStatus,
    get_metrics_collector
)

from .zk_auditor import (
    ZKAuditor,
    AuditReport,
    RewardAuditProof,
    NetworkStateProof,
    ComplianceAuditProof
)

from .privacy_auditor import (
    PrivacyAuditor,
    PrivacyAuditReport
)

# Componentes blockchain de auditoría
from .blockchain_auditor import (
    BlockchainAuditor,
    AuditBlock,
    AuditOperation,
    get_blockchain_auditor
)

from .hash_chain_manager import (
    HashChainManager,
    HashChain,
    HashChainEntry,
    get_hash_chain_manager
)

from .audit_smart_contracts import (
    SmartContract,
    ComplianceValidationContract,
    AuditTrailContract,
    RiskAssessmentContract,
    SmartContractManager,
    ContractExecution,
    ContractState,
    get_smart_contract_manager
)

from .audit_query_api import audit_router

from .immutable_log_storage import (
    ImmutableLogStorage,
    LogEntry,
    get_immutable_log_storage
)

from .compliance_reporter import (
    ComplianceReporter,
    ComplianceReport,
    get_compliance_reporter
)

from .blockchain_audit_integration import (
    BlockchainAuditIntegration,
    get_blockchain_audit_integration,
    initialize_blockchain_audit_system
)

from .api_endpoints import router as audit_api_router
from .websocket_endpoints import router as websocket_api_router
from .integration import get_audit_integration, initialize_audit_integration
from .dashboard import get_audit_dashboard
from .realtime_monitor import get_realtime_monitor, get_websocket_handler

__all__ = [
    # Audit Manager
    'AuditManager',
    'AuditEvent',
    'AuditEventType',
    'SecurityAlert',
    'SecurityAlertLevel',
    'SystemMetrics',
    'get_audit_manager',

    # Structured Logger
    'StructuredLogger',
    'LogContext',
    'get_structured_logger',
    'log_api_request',
    'log_security_event',
    'log_config_change',
    'log_user_action',
    'log_performance',
    'log_operation',

    # Security Monitor
    'SecurityMonitor',
    'SecurityRule',
    'ThreatIndicator',
    'get_security_monitor',

    # Metrics Collector
    'MetricsCollector',
    'PerformanceMetrics',
    'ResourceMetrics',
    'ApplicationMetrics',
    'HealthStatus',
    'get_metrics_collector',

    # ZK Auditor
    'ZKAuditor',
    'AuditReport',
    'RewardAuditProof',
    'NetworkStateProof',
    'ComplianceAuditProof',

    # Privacy Auditor
    'PrivacyAuditor',
    'PrivacyAuditReport',

    # Blockchain Audit Components
    'BlockchainAuditor',
    'AuditBlock',
    'AuditOperation',
    'get_blockchain_auditor',

    'HashChainManager',
    'HashChain',
    'HashChainEntry',
    'get_hash_chain_manager',

    'SmartContract',
    'ComplianceValidationContract',
    'AuditTrailContract',
    'RiskAssessmentContract',
    'SmartContractManager',
    'ContractExecution',
    'ContractState',
    'get_smart_contract_manager',

    'audit_router',

    'ImmutableLogStorage',
    'LogEntry',
    'get_immutable_log_storage',

    'ComplianceReporter',
    'ComplianceReport',
    'get_compliance_reporter',

    'BlockchainAuditIntegration',
    'get_blockchain_audit_integration',
    'initialize_blockchain_audit_system',

    # API and Integration
    'audit_api_router',
    'websocket_api_router',
    'get_audit_integration',
    'initialize_audit_integration',
    'get_audit_dashboard',
    'get_realtime_monitor',
    'get_websocket_handler'
]