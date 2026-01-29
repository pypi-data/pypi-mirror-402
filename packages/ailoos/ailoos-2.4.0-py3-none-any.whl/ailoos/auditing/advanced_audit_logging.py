"""
Advanced Audit Logging System for FASE 8.
Complete enterprise-grade auditing solution with all components integrated.
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..core.config import get_config
from ..core.logging import get_logger
from .audit_event import AuditEvent, AuditEventType, AuditSeverity
from .audit_logger import AuditLogger
from .audit_storage import AuditStorage, StorageConfig, StorageBackend
from .audit_query_engine import AuditQueryEngine, QuerySpec
from .audit_retention import AuditRetention
from .audit_compliance import AuditCompliance, ReportType, ComplianceStandard, ExportFormat
from .audit_monitoring import AuditMonitoring


@dataclass
class AuditSystemConfig:
    """Configuration for the complete audit system."""
    storage_backend: StorageBackend = StorageBackend.SQLITE
    storage_path: str = "./data/audit.db"
    enable_monitoring: bool = True
    enable_retention: bool = True
    enable_compliance: bool = True
    monitoring_interval_seconds: int = 30
    retention_cleanup_hours: int = 24
    max_events_in_memory: int = 10000
    enable_realtime_alerts: bool = True


class AdvancedAuditLogging:
    """
    Complete Advanced Audit Logging system for FASE 8.
    Integrates all audit components: Logger, Storage, Query Engine, Retention, Compliance, and Monitoring.
    """

    def __init__(self, config: Optional[AuditSystemConfig] = None):
        self.config = config or AuditSystemConfig()
        self.logger = get_logger("advanced_audit_logging")

        # Core components
        self.audit_logger: Optional[AuditLogger] = None
        self.audit_storage: Optional[AuditStorage] = None
        self.query_engine: Optional[AuditQueryEngine] = None
        self.retention_manager: Optional[AuditRetention] = None
        self.compliance_manager: Optional[AuditCompliance] = None
        self.monitoring_system: Optional[AuditMonitoring] = None

        # System state
        self.initialized = False
        self.running = False

        # Statistics
        self.stats = {
            'events_processed': 0,
            'queries_executed': 0,
            'reports_generated': 0,
            'alerts_triggered': 0,
            'start_time': None,
            'uptime_seconds': 0
        }

    async def initialize(self):
        """Initialize the complete audit system."""
        try:
            self.logger.info("Initializing Advanced Audit Logging system...")

            # 1. Initialize Storage
            storage_config = StorageConfig(
                backend=self.config.storage_backend,
                connection_string=self.config.storage_path
            )
            self.audit_storage = AuditStorage(storage_config)

            # 2. Initialize Logger
            self.audit_logger = AuditLogger()

            # 3. Initialize Query Engine
            self.query_engine = AuditQueryEngine(self.audit_storage)

            # 4. Initialize Retention Manager
            if self.config.enable_retention:
                self.retention_manager = AuditRetention(self.audit_storage)
                self.retention_manager.start_automated_cleanup()

            # 5. Initialize Compliance Manager
            if self.config.enable_compliance:
                self.compliance_manager = AuditCompliance(self.query_engine)

            # 6. Initialize Monitoring System
            if self.config.enable_monitoring:
                self.monitoring_system = AuditMonitoring(self.query_engine, self.audit_logger)
                self.monitoring_system.start_monitoring()

            self.initialized = True
            self.stats['start_time'] = datetime.now()

            self.logger.info("✅ Advanced Audit Logging system initialized successfully")

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize audit system: {e}")
            raise

    async def start(self):
        """Start the audit system."""
        if not self.initialized:
            await self.initialize()

        self.running = True
        self.logger.info("🚀 Advanced Audit Logging system started")

    async def stop(self):
        """Stop the audit system gracefully."""
        self.running = False

        # Stop monitoring
        if self.monitoring_system:
            self.monitoring_system.stop_monitoring()

        # Stop retention cleanup
        if self.retention_manager:
            self.retention_manager.stop_automated_cleanup()

        # Shutdown logger
        if self.audit_logger:
            await self.audit_logger.shutdown()

        # Shutdown storage
        if self.audit_storage:
            await self.audit_storage.shutdown()

        self.logger.info("🛑 Advanced Audit Logging system stopped")

    async def log_event(
        self,
        event_type: AuditEventType,
        resource: str,
        action: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        success: bool = True,
        processing_time_ms: Optional[float] = None
    ) -> str:
        """
        Log an audit event through the complete system.

        Returns:
            Event ID of the logged event
        """
        if not self.running:
            raise RuntimeError("Audit system is not running")

        # Create audit event
        import secrets
        event_id = secrets.token_hex(8)

        event = AuditEvent(
            event_type=event_type,
            event_id=event_id,
            timestamp=datetime.now(),
            resource=resource,
            action=action,
            user_id=user_id,
            session_id=session_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
            severity=severity,
            success=success,
            processing_time_ms=processing_time_ms
        )

        # Calculate risk score
        event.calculate_risk_score()

        # Log through logger
        await self.audit_logger.log_event(event)

        # Store in storage
        await self.audit_storage.store_event(event)

        self.stats['events_processed'] += 1

        return event_id

    async def query_events(self, query_spec: QuerySpec) -> Dict[str, Any]:
        """Query audit events."""
        if not self.query_engine:
            raise RuntimeError("Query engine not initialized")

        result = await self.query_engine.execute_query(query_spec)
        self.stats['queries_executed'] += 1

        return {
            'events': [event.to_dict() for event in result.events],
            'total_count': result.total_count,
            'execution_time_ms': result.execution_time_ms,
            'aggregations': result.aggregations,
            'groups': result.groups
        }

    async def generate_compliance_report(
        self,
        report_type: ReportType,
        standard: ComplianceStandard,
        days: int = 30
    ) -> Dict[str, Any]:
        """Generate a compliance report."""
        if not self.compliance_manager:
            raise RuntimeError("Compliance manager not enabled")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        report = await self.compliance_manager.generate_compliance_report(
            report_type=report_type,
            standard=standard,
            period_start=start_date,
            period_end=end_date
        )

        self.stats['reports_generated'] += 1

        return {
            'report_id': report.report_id,
            'report_type': report.report_type.value,
            'standard': report.standard.value,
            'compliance_score': report.compliance_score,
            'findings': [f.__dict__ if hasattr(f, '__dict__') else f for f in report.findings],
            'recommendations': report.recommendations,
            'generated_at': report.generated_at.isoformat()
        }

    async def export_audit_data(
        self,
        query_spec: QuerySpec,
        format: ExportFormat,
        destination: str,
        compression: bool = False
    ) -> Dict[str, Any]:
        """Export audit data."""
        if not self.compliance_manager:
            raise RuntimeError("Compliance manager not enabled")

        job = await self.compliance_manager.export_audit_data(
            query_spec=query_spec,
            format=format,
            destination=destination,
            compression=compression
        )

        return {
            'job_id': job.job_id,
            'status': job.status,
            'format': job.format.value,
            'destination': job.destination,
            'created_at': job.created_at.isoformat()
        }

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        uptime = 0
        if self.stats['start_time']:
            uptime = (datetime.now() - self.stats['start_time']).total_seconds()

        status = {
            'system_running': self.running,
            'system_initialized': self.initialized,
            'uptime_seconds': uptime,
            'stats': self.stats.copy(),
            'components': {}
        }

        # Component statuses
        if self.audit_storage:
            status['components']['storage'] = {
                'active': True,
                'stats': self.audit_storage.get_stats()
            }

        if self.audit_logger:
            status['components']['logger'] = {
                'active': True,
                'stats': self.audit_logger.get_stats()
            }

        if self.query_engine:
            status['components']['query_engine'] = {
                'active': True,
                'stats': self.query_engine.get_stats()
            }

        if self.monitoring_system:
            status['components']['monitoring'] = {
                'active': self.monitoring_system._monitoring_task is not None,
                'stats': self.monitoring_system.get_stats()
            }

        if self.retention_manager:
            status['components']['retention'] = {
                'active': self.retention_manager._cleanup_task is not None,
                'stats': self.retention_manager.get_stats()
            }

        if self.compliance_manager:
            status['components']['compliance'] = {
                'active': True,
                'stats': self.compliance_manager.get_stats()
            }

        return status

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data for monitoring."""
        if not self.monitoring_system:
            return {'error': 'Monitoring system not enabled'}

        return await self.monitoring_system.get_dashboard_data()

    async def run_maintenance(self) -> Dict[str, Any]:
        """Run system maintenance tasks."""
        results = {}

        # Retention cleanup
        if self.retention_manager:
            retention_result = await self.retention_manager.apply_retention_policies()
            results['retention_cleanup'] = retention_result

        # Compliance checks
        if self.compliance_manager:
            compliance_data = await self.compliance_manager.get_compliance_dashboard_data()
            results['compliance_status'] = compliance_data

        # Storage optimization
        if self.audit_storage:
            # Cleanup expired data
            await self.audit_storage.cleanup_expired_data()
            results['storage_cleanup'] = {'status': 'completed'}

        return results

    # Convenience methods for common audit operations

    async def log_user_action(
        self,
        user_id: str,
        action: str,
        resource: str,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> str:
        """Log a user action."""
        return await self.log_event(
            event_type=AuditEventType.USER_ACTION,
            resource=resource,
            action=action,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            details=details,
            success=success,
            severity=AuditSeverity.INFO
        )

    async def log_security_event(
        self,
        event_type: str,
        resource: str,
        action: str,
        severity: AuditSeverity = AuditSeverity.WARNING,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> str:
        """Log a security event."""
        return await self.log_event(
            event_type=AuditEventType.SECURITY_ALERT,
            resource=resource,
            action=action,
            user_id=user_id,
            ip_address=ip_address,
            details={'security_event_type': event_type, **(details or {})},
            severity=severity,
            success=False
        )

    async def log_data_access(
        self,
        user_id: str,
        resource: str,
        action: str,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
        processing_time_ms: Optional[float] = None
    ) -> str:
        """Log data access."""
        return await self.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            resource=resource,
            action=action,
            user_id=user_id,
            details=details,
            success=success,
            severity=AuditSeverity.INFO if success else AuditSeverity.WARNING,
            processing_time_ms=processing_time_ms
        )

    async def log_system_operation(
        self,
        operation: str,
        resource: str,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
        processing_time_ms: Optional[float] = None
    ) -> str:
        """Log system operation."""
        return await self.log_event(
            event_type=AuditEventType.SYSTEM_OPERATION,
            resource=resource,
            action=operation,
            details=details,
            success=success,
            severity=AuditSeverity.INFO if success else AuditSeverity.ERROR,
            processing_time_ms=processing_time_ms
        )


# Global instance
_advanced_audit_system: Optional[AdvancedAuditLogging] = None


async def get_advanced_audit_system() -> AdvancedAuditLogging:
    """Get the global advanced audit system instance."""
    global _advanced_audit_system
    if _advanced_audit_system is None:
        _advanced_audit_system = AdvancedAuditLogging()
        await _advanced_audit_system.initialize()
        await _advanced_audit_system.start()
    return _advanced_audit_system


def get_audit_system() -> Optional[AdvancedAuditLogging]:
    """Get the current audit system instance (synchronous)."""
    global _advanced_audit_system
    return _advanced_audit_system


# Convenience functions for easy auditing
async def audit_log(
    event_type: AuditEventType,
    resource: str,
    action: str,
    **kwargs
) -> str:
    """Convenience function for logging audit events."""
    system = await get_advanced_audit_system()
    return await system.log_event(event_type, resource, action, **kwargs)


async def audit_user_action(
    user_id: str,
    action: str,
    resource: str,
    **kwargs
) -> str:
    """Convenience function for logging user actions."""
    system = await get_advanced_audit_system()
    return await system.log_user_action(user_id, action, resource, **kwargs)


async def audit_security_event(
    event_type: str,
    resource: str,
    action: str,
    **kwargs
) -> str:
    """Convenience function for logging security events."""
    system = await get_advanced_audit_system()
    return await system.log_security_event(event_type, resource, action, **kwargs)


async def audit_data_access(
    user_id: str,
    resource: str,
    action: str,
    **kwargs
) -> str:
    """Convenience function for logging data access."""
    system = await get_advanced_audit_system()
    return await system.log_data_access(user_id, resource, action, **kwargs)


async def audit_system_operation(
    operation: str,
    resource: str,
    **kwargs
) -> str:
    """Convenience function for logging system operations."""
    system = await get_advanced_audit_system()
    return await system.log_system_operation(operation, resource, **kwargs)