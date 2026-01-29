"""
Tests end-to-end para el sistema de auditoría.
Prueba flujos completos desde la recepción de eventos hasta el reporte final.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import json
import time
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.ailoos.auditing.audit_manager import AuditManager
from src.ailoos.auditing.security_monitor import SecurityMonitor
from src.ailoos.auditing.metrics_collector import MetricsCollector
from src.ailoos.auditing.dashboard import AuditDashboard
from src.ailoos.auditing.realtime_monitor import RealtimeMonitor
from src.ailoos.core.config import Config


class TestCompleteAuditLifecycle:
    """Tests del ciclo de vida completo de auditoría."""

    @pytest.fixture
    def config(self):
        """Configuración completa para tests E2E."""
        config = Mock(spec=Config)
        config.audit_log_file = "/tmp/test_e2e_audit.log"
        config.audit_retention_days = 30
        config.security_alert_thresholds = {
            "max_failed_logins_per_hour": 5,
            "max_config_changes_per_hour": 10
        }
        config.websocket_timeout = 30
        config.max_websocket_connections = 100
        config.metrics_collection_interval = 60
        config.metrics_retention_hours = 24
        return config

    @pytest.fixture
    async def complete_audit_system(self, config):
        """Sistema completo de auditoría para tests E2E."""
        # Crear todos los componentes
        audit_manager = AuditManager(config)
        security_monitor = SecurityMonitor(config)
        metrics_collector = MetricsCollector(config)
        dashboard = AuditDashboard(config, audit_manager, metrics_collector)
        realtime_monitor = RealtimeMonitor(config)

        # Inicializar componentes
        await audit_manager._setup_storage()
        await security_monitor._load_default_rules()
        await realtime_monitor.start_monitoring()

        system = {
            'audit_manager': audit_manager,
            'security_monitor': security_monitor,
            'metrics_collector': metrics_collector,
            'dashboard': dashboard,
            'realtime_monitor': realtime_monitor
        }

        yield system

        # Cleanup completo
        await realtime_monitor.stop_monitoring()
        if os.path.exists(audit_manager.audit_log_file):
            os.remove(audit_manager.audit_log_file)

    @pytest.mark.asyncio
    async def test_user_session_lifecycle_audit(self, complete_audit_system):
        """Test ciclo de vida completo de sesión de usuario con auditoría."""
        audit_manager = complete_audit_system['audit_manager']
        security_monitor = complete_audit_system['security_monitor']
        dashboard = complete_audit_system['dashboard']

        user_id = "test_user_123"
        session_id = "session_abc123"
        user_ip = "192.168.1.50"

        # 1. Inicio de sesión exitoso
        await audit_manager.log_event(
            event_type="USER_LOGIN",
            resource="auth",
            action="login_success",
            user_id=user_id,
            details={
                "ip": user_ip,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "session_id": session_id,
                "method": "password"
            }
        )

        # 2. Actividades durante la sesión
        activities = [
            {
                "event_type": "API_REQUEST",
                "resource": "api",
                "action": "get",
                "user_id": user_id,
                "details": {
                    "endpoint": "/api/user/profile",
                    "method": "GET",
                    "status_code": 200,
                    "response_time": 45,
                    "session_id": session_id
                }
            },
            {
                "event_type": "DATA_ACCESS",
                "resource": "user_data",
                "action": "view",
                "user_id": user_id,
                "details": {
                    "data_type": "personal_info",
                    "record_id": "user_123_profile",
                    "purpose": "profile_update",
                    "session_id": session_id
                }
            },
            {
                "event_type": "CONFIG_CHANGE",
                "resource": "user_preferences",
                "action": "update",
                "user_id": user_id,
                "details": {
                    "setting": "theme",
                    "old_value": "light",
                    "new_value": "dark",
                    "session_id": session_id
                }
            }
        ]

        for activity in activities:
            await audit_manager.log_event(**activity)
            await security_monitor.process_event(activity)

        # 3. Cierre de sesión
        await audit_manager.log_event(
            event_type="USER_LOGOUT",
            resource="auth",
            action="logout",
            user_id=user_id,
            details={
                "session_id": session_id,
                "duration_minutes": 45,
                "ip": user_ip,
                "reason": "user_initiated"
            }
        )

        # 4. Verificar que todas las actividades están auditadas
        events = audit_manager.get_audit_events()
        session_events = [e for e in events if e.get("user_id") == user_id]

        assert len(session_events) == 5  # login + 3 activities + logout

        # 5. Verificar estadísticas de sesión
        stats = audit_manager.get_audit_statistics()

        assert stats["total_events"] >= 5
        assert stats["events_by_user"][user_id] == 5
        assert stats["events_by_type"]["USER_LOGIN"] >= 1
        assert stats["events_by_type"]["API_REQUEST"] >= 1

        # 6. Verificar dashboard incluye las actividades
        dashboard_data = await dashboard.get_dashboard_data()

        assert len(dashboard_data["events"]) >= 5
        assert dashboard_data["summary"]["total_events"] >= 5

    @pytest.mark.asyncio
    async def test_security_incident_response_workflow(self, complete_audit_system):
        """Test flujo completo de respuesta a incidente de seguridad."""
        audit_manager = complete_audit_system['audit_manager']
        security_monitor = complete_audit_system['security_monitor']
        dashboard = complete_audit_system['dashboard']
        realtime_monitor = complete_audit_system['realtime_monitor']

        # 1. Configurar monitoreo en tiempo real
        await realtime_monitor.start_monitoring()

        # Conectar cliente de seguridad
        security_ws = Mock()
        security_ws.send_json = AsyncMock()
        await realtime_monitor.add_connection("alerts", security_ws)

        # 2. Simular ataque de fuerza bruta
        attacker_ip = "10.0.0.100"
        target_user = "admin"

        # Generar intentos de login fallidos
        for i in range(8):  # Más que el límite
            event_data = {
                "event_type": "USER_LOGIN",
                "resource": "auth",
                "action": "login_failed",
                "user_id": target_user,
                "details": {
                    "ip": attacker_ip,
                    "reason": "invalid_password",
                    "attempt": i + 1,
                    "user_agent": "MaliciousBot/1.0"
                }
            }

            await audit_manager.log_event(**event_data)
            await security_monitor.process_event(event_data)

        # 3. Esperar procesamiento de alertas
        await asyncio.sleep(0.2)

        # 4. Verificar detección de ataque
        alerts = audit_manager.get_security_alerts()
        brute_force_alerts = [a for a in alerts if "brute force" in a["title"].lower()]

        assert len(brute_force_alerts) > 0
        alert = brute_force_alerts[0]
        assert alert["severity"] == "HIGH"
        assert attacker_ip in alert["description"]

        # 5. Verificar notificación en tiempo real
        security_ws.send_json.assert_called()

        # 6. Simular respuesta del equipo de seguridad
        alert_id = list(audit_manager.security_alerts.keys())[0]
        audit_manager.acknowledge_alert(alert_id, "security_team")

        # 7. Verificar reconocimiento de alerta
        updated_alerts = audit_manager.get_security_alerts()
        acknowledged_alert = None
        for a in updated_alerts:
            if a["id"] == alert_id:
                acknowledged_alert = a
                break

        assert acknowledged_alert["acknowledged"] is True
        assert acknowledged_alert["acknowledged_by"] == "security_team"

        # 8. Verificar que el incidente aparece en el dashboard
        security_overview = await dashboard.get_security_overview()
        assert security_overview["alert_summary"]["HIGH"] >= 1

        # 9. Verificar reporte de incidente
        report = await dashboard.export_dashboard_report(format="json")
        report_data = json.loads(report)

        assert "events" in report_data
        assert "summary" in report_data

        # Cleanup
        await realtime_monitor.stop_monitoring()

    @pytest.mark.asyncio
    async def test_system_maintenance_audit_trail(self, complete_audit_system):
        """Test traza de auditoría completa de mantenimiento del sistema."""
        audit_manager = complete_audit_system['audit_manager']
        metrics_collector = complete_audit_system['metrics_collector']
        dashboard = complete_audit_system['dashboard']

        # 1. Inicio de mantenimiento
        await audit_manager.log_event(
            event_type="SYSTEM_MAINTENANCE",
            resource="system",
            action="maintenance_start",
            user_id="system_admin",
            details={
                "maintenance_type": "security_updates",
                "scheduled_duration": "2_hours",
                "impact": "service_degradation",
                "notification_sent": True
            }
        )

        # 2. Actividades de mantenimiento
        maintenance_activities = [
            {
                "event_type": "SOFTWARE_UPDATE",
                "resource": "system",
                "action": "install",
                "user_id": "system_admin",
                "details": {
                    "package": "security-patch-2024-001",
                    "version": "1.2.3",
                    "restart_required": True
                }
            },
            {
                "event_type": "CONFIG_CHANGE",
                "resource": "security_config",
                "action": "update",
                "user_id": "system_admin",
                "details": {
                    "setting": "max_login_attempts",
                    "old_value": "5",
                    "new_value": "3",
                    "reason": "security_hardening"
                }
            },
            {
                "event_type": "BACKUP_OPERATION",
                "resource": "database",
                "action": "backup",
                "user_id": "system_admin",
                "details": {
                    "backup_type": "full",
                    "size_mb": 1500,
                    "duration_seconds": 180,
                    "status": "success"
                }
            }
        ]

        for activity in maintenance_activities:
            await audit_manager.log_event(**activity)

            # Registrar métricas de rendimiento durante mantenimiento
            if activity["event_type"] == "SOFTWARE_UPDATE":
                metrics_collector.record_response_time(200.0)  # Más lento durante actualización
            else:
                metrics_collector.record_response_time(50.0)   # Normal

        # 3. Finalización de mantenimiento
        await audit_manager.log_event(
            event_type="SYSTEM_MAINTENANCE",
            resource="system",
            action="maintenance_complete",
            user_id="system_admin",
            details={
                "actual_duration": "1.5_hours",
                "issues_encountered": [],
                "system_restart_performed": True,
                "post_maintenance_tests": "passed"
            }
        )

        # 4. Verificar traza completa de mantenimiento
        events = audit_manager.get_audit_events()
        maintenance_events = [e for e in events if "maintenance" in e.get("action", "").lower() or
                             e.get("event_type") in ["SOFTWARE_UPDATE", "BACKUP_OPERATION"]]

        assert len(maintenance_events) >= 5  # start + 3 activities + complete

        # 5. Verificar métricas de rendimiento durante mantenimiento
        latest_metrics = metrics_collector.get_latest_metrics()
        assert "performance" in latest_metrics

        # 6. Generar reporte de mantenimiento
        dashboard_data = await dashboard.get_dashboard_data()
        maintenance_report = await dashboard.export_dashboard_report(format="json")

        report_data = json.loads(maintenance_report)
        assert len(report_data["events"]) >= 5

        # 7. Verificar estadísticas post-mantenimiento
        final_stats = audit_manager.get_audit_statistics()
        assert final_stats["events_by_type"]["SYSTEM_MAINTENANCE"] >= 2  # start y complete
        assert final_stats["events_by_type"]["SOFTWARE_UPDATE"] >= 1
        assert final_stats["events_by_type"]["BACKUP_OPERATION"] >= 1

    @pytest.mark.asyncio
    async def test_compliance_audit_workflow(self, complete_audit_system):
        """Test flujo completo de auditoría de cumplimiento."""
        audit_manager = complete_audit_system['audit_manager']
        dashboard = complete_audit_system['dashboard']

        # 1. Inicio de auditoría de cumplimiento
        await audit_manager.log_event(
            event_type="COMPLIANCE_AUDIT",
            resource="system",
            action="audit_start",
            user_id="compliance_officer",
            details={
                "audit_type": "GDPR_compliance",
                "scope": "user_data_processing",
                "period": "2024_Q1",
                "auditor": "compliance_officer"
            }
        )

        # 2. Recopilar evidencia de cumplimiento
        compliance_checks = [
            {
                "event_type": "DATA_PROCESSING_AUDIT",
                "resource": "user_data",
                "action": "verify_consent",
                "user_id": "compliance_officer",
                "details": {
                    "data_subject": "user_001",
                    "processing_activity": "email_marketing",
                    "consent_obtained": True,
                    "consent_date": "2024-01-15",
                    "consent_method": "web_form"
                }
            },
            {
                "event_type": "DATA_PROCESSING_AUDIT",
                "resource": "user_data",
                "action": "verify_retention",
                "user_id": "compliance_officer",
                "details": {
                    "data_category": "contact_info",
                    "retention_policy": "2_years",
                    "current_retention": "18_months",
                    "compliant": True
                }
            },
            {
                "event_type": "SECURITY_AUDIT",
                "resource": "access_controls",
                "action": "verify_rbac",
                "user_id": "compliance_officer",
                "details": {
                    "control_type": "role_based_access",
                    "roles_defined": ["admin", "user", "guest"],
                    "permissions_assigned": True,
                    "separation_of_duties": True,
                    "compliant": True
                }
            }
        ]

        for check in compliance_checks:
            await audit_manager.log_event(**check)

        # 3. Generar hallazgos de auditoría
        audit_findings = [
            {
                "event_type": "AUDIT_FINDING",
                "resource": "system",
                "action": "finding_logged",
                "user_id": "compliance_officer",
                "details": {
                    "finding_id": "GDPR-001",
                    "severity": "LOW",
                    "category": "documentation",
                    "description": "Privacy policy needs minor updates",
                    "recommendation": "Update privacy policy to reflect new data processing activities",
                    "due_date": "2024-06-30"
                }
            }
        ]

        for finding in audit_findings:
            await audit_manager.log_event(**finding)

        # 4. Completar auditoría
        await audit_manager.log_event(
            event_type="COMPLIANCE_AUDIT",
            resource="system",
            action="audit_complete",
            user_id="compliance_officer",
            details={
                "audit_result": "compliant_with_findings",
                "overall_compliance_score": 95,
                "critical_findings": 0,
                "high_findings": 0,
                "medium_findings": 0,
                "low_findings": 1,
                "report_generated": True,
                "review_date": "2024-06-30"
            }
        )

        # 5. Verificar traza completa de auditoría
        events = audit_manager.get_audit_events()
        audit_events = [e for e in events if "audit" in e.get("event_type", "").lower() or
                       "compliance" in e.get("event_type", "").lower()]

        assert len(audit_events) >= 6  # start + 3 checks + 1 finding + complete

        # 6. Generar reporte de cumplimiento
        compliance_report = await dashboard.export_dashboard_report(format="json")
        report_data = json.loads(compliance_report)

        # 7. Verificar estadísticas de cumplimiento
        compliance_stats = audit_manager.get_audit_statistics()

        assert compliance_stats["events_by_type"]["COMPLIANCE_AUDIT"] >= 2  # start y complete
        assert compliance_stats["events_by_type"]["DATA_PROCESSING_AUDIT"] >= 2
        assert compliance_stats["events_by_type"]["SECURITY_AUDIT"] >= 1
        assert compliance_stats["events_by_type"]["AUDIT_FINDING"] >= 1

    @pytest.mark.asyncio
    async def test_business_continuity_incident_response(self, complete_audit_system):
        """Test respuesta a incidente que afecta continuidad del negocio."""
        audit_manager = complete_audit_system['audit_manager']
        security_monitor = complete_audit_system['security_monitor']
        metrics_collector = complete_audit_system['metrics_collector']
        dashboard = complete_audit_system['dashboard']
        realtime_monitor = complete_audit_system['realtime_monitor']

        # 1. Configurar monitoreo de incidentes
        await realtime_monitor.start_monitoring()

        incident_ws = Mock()
        incident_ws.send_json = AsyncMock()
        await realtime_monitor.add_connection("alerts", incident_ws)

        # 2. Simular incidente de seguridad que afecta servicio
        incident_start = datetime.now()

        # Ataque DDoS simulado
        for i in range(20):
            event_data = {
                "event_type": "UNUSUAL_TRAFFIC",
                "resource": "network",
                "action": "high_traffic_detected",
                "user_id": "system_monitor",
                "details": {
                    "traffic_type": "SYN_flood",
                    "source_ips": [f"192.168.{i%256}.{j}" for j in range(10)],
                    "packets_per_second": 10000 + i * 1000,
                    "affected_service": "web_api",
                    "severity": "CRITICAL" if i > 15 else "HIGH"
                }
            }

            await audit_manager.log_event(**event_data)
            await security_monitor.process_event(event_data)

            # Simular degradación de rendimiento
            metrics_collector.record_response_time(1000 + i * 100)  # Respuestas muy lentas
            metrics_collector.record_error("/api/health", "timeout")

        # 3. Declarar incidente de seguridad
        await audit_manager.log_event(
            event_type="INCIDENT_DECLARED",
            resource="system",
            action="incident_start",
            user_id="security_team",
            details={
                "incident_id": "SEC-2024-001",
                "incident_type": "DDoS_attack",
                "severity": "CRITICAL",
                "affected_services": ["web_api", "user_auth"],
                "business_impact": "service_degradation",
                "response_team": "security_incident_response"
            }
        )

        # 4. Respuesta al incidente
        incident_response = [
            {
                "event_type": "INCIDENT_RESPONSE",
                "resource": "network",
                "action": "mitigation_deployed",
                "user_id": "security_team",
                "details": {
                    "incident_id": "SEC-2024-001",
                    "action": "rate_limiting_enabled",
                    "affected_ips": "blocked_ip_range",
                    "mitigation_time": "5_minutes"
                }
            },
            {
                "event_type": "INCIDENT_RESPONSE",
                "resource": "system",
                "action": "failover_activated",
                "user_id": "devops_team",
                "details": {
                    "incident_id": "SEC-2024-001",
                    "action": "traffic_redirected",
                    "backup_system": "secondary_datacenter",
                    "capacity_increased": "200%"
                }
            }
        ]

        for response in incident_response:
            await audit_manager.log_event(**response)

        # 5. Recuperación del servicio
        await audit_manager.log_event(
            event_type="SERVICE_RECOVERY",
            resource="system",
            action="service_restored",
            user_id="devops_team",
            details={
                "incident_id": "SEC-2024-001",
                "recovery_time": "15_minutes",
                "service_status": "fully_operational",
                "monitoring_active": True
            }
        )

        # 6. Cierre del incidente
        incident_end = datetime.now()
        duration = (incident_end - incident_start).total_seconds() / 60  # minutos

        await audit_manager.log_event(
            event_type="INCIDENT_CLOSED",
            resource="system",
            action="incident_resolved",
            user_id="security_team",
            details={
                "incident_id": "SEC-2024-001",
                "resolution": "attack_mitigated",
                "total_duration_minutes": duration,
                "business_impact": "minimal_downtime",
                "lessons_learned": "Improve_rate_limiting",
                "follow_up_actions": ["security_review", "infrastructure_upgrade"]
            }
        )

        # 7. Verificar traza completa del incidente
        events = audit_manager.get_audit_events()
        incident_events = [e for e in events if "incident" in e.get("event_type", "").lower() or
                          e.get("event_type") in ["UNUSUAL_TRAFFIC", "SERVICE_RECOVERY"]]

        assert len(incident_events) >= 25  # 20 eventos de tráfico + declaración + 2 respuestas + recuperación + cierre

        # 8. Verificar métricas de rendimiento durante incidente
        perf_overview = await dashboard.get_performance_overview()
        assert perf_overview["analysis"]["error_rate"]["status"] == "high"

        # 9. Verificar notificaciones en tiempo real
        incident_ws.send_json.assert_called()

        # 10. Generar reporte de incidente
        incident_report = await dashboard.export_dashboard_report(format="json")
        report_data = json.loads(incident_report)

        assert len(report_data["events"]) >= 25

        # Cleanup
        await realtime_monitor.stop_monitoring()

    @pytest.mark.asyncio
    async def test_regulatory_reporting_workflow(self, complete_audit_system):
        """Test flujo completo de reporte regulatorio."""
        audit_manager = complete_audit_system['audit_manager']
        dashboard = complete_audit_system['dashboard']

        # 1. Inicio del período de reporte
        reporting_period = "2024_Q2"

        await audit_manager.log_event(
            event_type="REGULATORY_REPORTING",
            resource="system",
            action="reporting_period_start",
            user_id="compliance_officer",
            details={
                "period": reporting_period,
                "regulations": ["GDPR", "CCPA", "SOX"],
                "report_types": ["data_processing", "security_incidents", "access_logs"],
                "due_date": "2024-07-31"
            }
        )

        # 2. Recopilar datos para reporte
        regulatory_data = [
            # GDPR Article 30 - Records of processing activities
            {
                "event_type": "DATA_PROCESSING_RECORD",
                "resource": "user_data",
                "action": "processing_documented",
                "user_id": "compliance_officer",
                "details": {
                    "regulation": "GDPR_Article_30",
                    "data_controller": "Ailoos Corp",
                    "processing_activity": "User registration and profile management",
                    "data_categories": ["personal_info", "contact_details", "usage_data"],
                    "data_subjects": 15000,
                    "retention_period": "account_active_plus_2_years",
                    "security_measures": ["encryption", "access_controls", "audit_logging"]
                }
            },
            # Security incident reporting
            {
                "event_type": "SECURITY_INCIDENT_REPORT",
                "resource": "system",
                "action": "incident_logged",
                "user_id": "compliance_officer",
                "details": {
                    "incident_id": "SEC-2024-002",
                    "date_occurred": "2024-04-15",
                    "incident_type": "unauthorized_access_attempt",
                    "affected_data": "user_profiles",
                    "data_subjects_affected": 5,
                    "resolution": "access_blocked",
                    "preventive_measures": "enhanced_monitoring"
                }
            },
            # Data subject access requests (DSAR)
            {
                "event_type": "DSAR_PROCESSING",
                "resource": "user_data",
                "action": "access_request_fulfilled",
                "user_id": "compliance_officer",
                "details": {
                    "regulation": "GDPR_Article_15",
                    "requests_received": 23,
                    "requests_fulfilled": 23,
                    "average_response_time_days": 5,
                    "denial_rate": "0%",
                    "automated_responses": 18
                }
            }
        ]

        for data in regulatory_data:
            await audit_manager.log_event(**data)

        # 3. Generar reportes regulatorios
        reports_generated = [
            {
                "event_type": "REGULATORY_REPORT",
                "resource": "system",
                "action": "report_generated",
                "user_id": "compliance_officer",
                "details": {
                    "report_type": "GDPR_Annual_Report",
                    "period": reporting_period,
                    "sections": ["data_processing", "security_measures", "incident_response"],
                    "page_count": 45,
                    "review_status": "pending_legal_review"
                }
            },
            {
                "event_type": "REGULATORY_REPORT",
                "resource": "system",
                "action": "report_submitted",
                "user_id": "compliance_officer",
                "details": {
                    "report_type": "Data_Protection_Impact_Assessment",
                    "submitted_to": "Data_Protection_Authority",
                    "submission_date": "2024-06-30",
                    "confirmation_received": True,
                    "next_review_date": "2025-06-30"
                }
            }
        ]

        for report in reports_generated:
            await audit_manager.log_event(**report)

        # 4. Completar período de reporte
        await audit_manager.log_event(
            event_type="REGULATORY_REPORTING",
            resource="system",
            action="reporting_period_complete",
            user_id="compliance_officer",
            details={
                "period": reporting_period,
                "reports_submitted": 3,
                "compliance_status": "compliant",
                "audit_findings": "none",
                "next_reporting_period": "2024_Q3",
                "continuous_improvements": ["automated_reporting", "enhanced_monitoring"]
            }
        )

        # 5. Verificar traza completa de reporte regulatorio
        events = audit_manager.get_audit_events()
        regulatory_events = [e for e in events if "regulatory" in e.get("event_type", "").lower() or
                            "report" in e.get("action", "").lower() or
                            e.get("event_type") in ["DATA_PROCESSING_RECORD", "SECURITY_INCIDENT_REPORT", "DSAR_PROCESSING"]]

        assert len(regulatory_events) >= 7  # start + 3 data + 2 reports + complete

        # 6. Generar dashboard de cumplimiento
        compliance_dashboard = await dashboard.get_dashboard_data()

        # 7. Exportar reporte final
        final_report = await dashboard.export_dashboard_report(format="json")
        report_data = json.loads(final_report)

        assert len(report_data["events"]) >= 7

        # 8. Verificar estadísticas regulatorias
        regulatory_stats = audit_manager.get_audit_statistics()

        assert regulatory_stats["events_by_type"]["REGULATORY_REPORTING"] >= 2  # start y complete
        assert regulatory_stats["events_by_type"]["DATA_PROCESSING_RECORD"] >= 1
        assert regulatory_stats["events_by_type"]["SECURITY_INCIDENT_REPORT"] >= 1
        assert regulatory_stats["events_by_type"]["DSAR_PROCESSING"] >= 1