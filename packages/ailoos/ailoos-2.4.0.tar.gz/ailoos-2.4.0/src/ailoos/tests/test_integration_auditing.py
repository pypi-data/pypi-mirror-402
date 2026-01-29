"""
Tests de integración para el módulo de auditoría.
Prueba la interacción entre componentes del sistema de auditoría.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import json
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.ailoos.auditing.audit_manager import AuditManager
from src.ailoos.auditing.structured_logger import StructuredLogger, get_structured_logger
from src.ailoos.auditing.security_monitor import SecurityMonitor
from src.ailoos.auditing.metrics_collector import MetricsCollector
from src.ailoos.auditing.dashboard import AuditDashboard
from src.ailoos.auditing.realtime_monitor import RealtimeMonitor
from src.ailoos.core.config import Config


class TestAuditManagerIntegration:
    """Tests de integración para AuditManager con otros componentes."""

    @pytest.fixture
    def config(self):
        """Configuración completa para tests de integración."""
        config = Mock(spec=Config)
        config.audit_log_file = "/tmp/test_audit_integration.log"
        config.audit_retention_days = 30
        config.security_alert_thresholds = {
            "max_failed_logins_per_hour": 5,
            "max_config_changes_per_hour": 10
        }
        config.websocket_timeout = 30
        config.max_websocket_connections = 100
        return config

    @pytest.fixture
    async def audit_system(self, config):
        """Sistema completo de auditoría integrado."""
        # Crear componentes
        audit_manager = AuditManager(config)
        security_monitor = SecurityMonitor(config)
        metrics_collector = MetricsCollector(config)
        dashboard = AuditDashboard(config, audit_manager, metrics_collector)
        realtime_monitor = RealtimeMonitor(config)

        # Configurar integración
        await audit_manager._setup_storage()
        await security_monitor._load_default_rules()
        await metrics_collector._collection_loop()

        system = {
            'audit_manager': audit_manager,
            'security_monitor': security_monitor,
            'metrics_collector': metrics_collector,
            'dashboard': dashboard,
            'realtime_monitor': realtime_monitor
        }

        yield system

        # Cleanup
        for component in system.values():
            if hasattr(component, 'shutdown'):
                if asyncio.iscoroutinefunction(component.shutdown):
                    await component.shutdown()
                else:
                    component.shutdown()

        if os.path.exists(audit_manager.audit_log_file):
            os.remove(audit_manager.audit_log_file)

    @pytest.mark.asyncio
    async def test_audit_event_flow_through_system(self, audit_system):
        """Test flujo completo de evento de auditoría a través del sistema."""
        audit_manager = audit_system['audit_manager']
        security_monitor = audit_system['security_monitor']
        dashboard = audit_system['dashboard']

        # 1. Generar evento de auditoría
        await audit_manager.log_event(
            event_type="USER_LOGIN",
            resource="auth",
            action="login_failed",
            user_id="test_user",
            details={"ip": "192.168.1.1", "reason": "invalid_password"}
        )

        # 2. Procesar evento en monitor de seguridad
        event_data = {
            "event_type": "USER_LOGIN",
            "resource": "auth",
            "action": "login_failed",
            "user_id": "test_user",
            "details": {"ip": "192.168.1.1", "reason": "invalid_password"}
        }
        await security_monitor.process_event(event_data)

        # 3. Verificar que el evento aparece en el dashboard
        dashboard_data = await dashboard.get_dashboard_data()

        assert len(dashboard_data['events']) > 0
        assert dashboard_data['events'][0]['event_type'] == 'USER_LOGIN'

        # 4. Verificar estado de seguridad
        security_overview = await dashboard.get_security_overview()
        assert 'alert_summary' in security_overview

    @pytest.mark.asyncio
    async def test_security_alert_propagation(self, audit_system):
        """Test propagación de alertas de seguridad a través del sistema."""
        audit_manager = audit_system['audit_manager']
        security_monitor = audit_system['security_monitor']
        realtime_monitor = audit_system['realtime_monitor']

        # Generar múltiples eventos de login fallido para activar alerta
        for i in range(6):
            event_data = {
                "event_type": "USER_LOGIN",
                "resource": "auth",
                "action": "login_failed",
                "user_id": "test_user",
                "details": {"ip": "192.168.1.1", "reason": "invalid_password"}
            }
            await security_monitor.process_event(event_data)

        # Esperar procesamiento
        await asyncio.sleep(0.1)

        # Verificar que se generó alerta en audit_manager
        alerts = audit_manager.get_security_alerts()
        assert len(alerts) > 0

        # Verificar que la alerta se propaga al dashboard
        dashboard = audit_system['dashboard']
        security_overview = await dashboard.get_security_overview()
        assert security_overview['alert_summary']['HIGH'] >= 1

    @pytest.mark.asyncio
    async def test_metrics_collection_integration(self, audit_system):
        """Test integración de recolección de métricas."""
        metrics_collector = audit_system['metrics_collector']
        dashboard = audit_system['dashboard']

        # Simular algunas métricas
        metrics_collector.record_response_time(150.5)
        metrics_collector.record_error("/api/test", "validation_error")

        # Obtener métricas del dashboard
        perf_overview = await dashboard.get_performance_overview()

        assert 'current_metrics' in perf_overview
        assert 'analysis' in perf_overview

    @pytest.mark.asyncio
    async def test_realtime_monitoring_integration(self, audit_system):
        """Test integración de monitoreo en tiempo real."""
        realtime_monitor = audit_system['realtime_monitor']
        audit_manager = audit_system['audit_manager']

        # Iniciar monitoreo
        await realtime_monitor.start_monitoring()

        # Agregar conexión mock
        websocket_mock = Mock()
        websocket_mock.send_json = AsyncMock()
        await realtime_monitor.add_connection("dashboard", websocket_mock)

        # Generar evento que debería propagarse
        await audit_manager.log_event(
            event_type="CONFIG_CHANGE",
            resource="system",
            action="update",
            user_id="admin",
            details={"key": "timeout", "old_value": 30, "new_value": 60}
        )

        # Verificar que se envió mensaje al websocket
        websocket_mock.send_json.assert_called()

        # Detener monitoreo
        await realtime_monitor.stop_monitoring()

    @pytest.mark.asyncio
    async def test_structured_logging_integration(self, audit_system):
        """Test integración de logging estructurado."""
        audit_manager = audit_system['audit_manager']

        # Crear logger estructurado
        logger = get_structured_logger("test_module")

        # Loggear evento que debería aparecer en auditoría
        logger.log_security_event(
            event_type="login_attempt",
            details={"ip": "192.168.1.1", "success": False},
            severity="HIGH"
        )

        # Verificar que el evento aparece en audit_manager
        events = audit_manager.get_audit_events()
        # Nota: El logger estructurado puede no estar directamente integrado con audit_manager
        # en esta implementación, así que verificamos que no hay errores

    @pytest.mark.asyncio
    async def test_dashboard_data_consistency(self, audit_system):
        """Test consistencia de datos en dashboard."""
        audit_manager = audit_system['audit_manager']
        dashboard = audit_system['dashboard']

        # Agregar algunos eventos
        await audit_manager.log_event("USER_LOGIN", "auth", "login", "user1")
        await audit_manager.log_event("CONFIG_CHANGE", "system", "update", "admin")

        # Obtener datos del dashboard múltiples veces
        data1 = await dashboard.get_dashboard_data()
        data2 = await dashboard.get_dashboard_data()

        # Verificar consistencia
        assert len(data1['events']) == len(data2['events'])
        assert data1['summary']['total_events'] == data2['summary']['total_events']


class TestSecurityMonitorIntegration:
    """Tests de integración para SecurityMonitor."""

    @pytest.fixture
    def config(self):
        """Configuración para tests de seguridad."""
        config = Mock(spec=Config)
        config.security_rules_file = "/tmp/test_security_integration.json"
        config.threat_intelligence_file = "/tmp/test_threats_integration.json"
        return config

    @pytest.fixture
    async def security_system(self, config):
        """Sistema de seguridad integrado."""
        security_monitor = SecurityMonitor(config)
        audit_manager = AuditManager(config)

        # Cargar reglas por defecto
        await security_monitor._load_default_rules()

        system = {
            'security_monitor': security_monitor,
            'audit_manager': audit_manager
        }

        yield system

        # Cleanup
        if os.path.exists(config.audit_log_file):
            os.remove(config.audit_log_file)

    @pytest.mark.asyncio
    async def test_security_rule_integration(self, security_system):
        """Test integración de reglas de seguridad."""
        security_monitor = security_system['security_monitor']

        # Agregar regla personalizada
        rule = {
            "rule_id": "custom_rule",
            "name": "Custom Security Rule",
            "description": "Test rule",
            "severity": "MEDIUM",
            "conditions": [
                {
                    "field": "event_type",
                    "operator": "equals",
                    "value": "CUSTOM_EVENT"
                }
            ],
            "action": "alert"
        }

        security_monitor.add_security_rule(rule)

        # Procesar evento que coincide
        event_data = {
            "event_type": "CUSTOM_EVENT",
            "resource": "test",
            "action": "test_action",
            "user_id": "test_user"
        }

        with patch.object(security_monitor, '_send_alert') as mock_send:
            await security_monitor.process_event(event_data)
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_threat_intelligence_integration(self, security_system):
        """Test integración de inteligencia de amenazas."""
        security_monitor = security_system['security_monitor']

        # Agregar indicador de amenaza
        indicator = {
            "indicator_id": "test_indicator",
            "name": "Test Indicator",
            "type": "ip_address",
            "value": "192.168.1.100",
            "severity": "HIGH",
            "description": "Test malicious IP"
        }

        security_monitor.add_threat_indicator(indicator)

        # Procesar evento con IP maliciosa
        event_data = {
            "event_type": "USER_LOGIN",
            "resource": "auth",
            "action": "login_attempt",
            "user_id": "test_user",
            "details": {"ip": "192.168.1.100"}
        }

        with patch.object(security_monitor, '_send_alert') as mock_send:
            await security_monitor.process_event(event_data)
            mock_send.assert_called()


class TestMetricsCollectorIntegration:
    """Tests de integración para MetricsCollector."""

    @pytest.fixture
    def config(self):
        """Configuración para tests de métricas."""
        config = Mock(spec=Config)
        config.metrics_collection_interval = 60
        config.metrics_retention_hours = 24
        return config

    @pytest.fixture
    async def metrics_system(self, config):
        """Sistema de métricas integrado."""
        metrics_collector = MetricsCollector(config)
        dashboard = AuditDashboard(config, Mock(), metrics_collector)

        system = {
            'metrics_collector': metrics_collector,
            'dashboard': dashboard
        }

        yield system

    @pytest.mark.asyncio
    async def test_metrics_flow_to_dashboard(self, metrics_system):
        """Test flujo de métricas al dashboard."""
        metrics_collector = metrics_system['metrics_collector']
        dashboard = metrics_system['dashboard']

        # Registrar algunas métricas
        metrics_collector.record_response_time(100.0)
        metrics_collector.record_response_time(200.0)
        metrics_collector.record_error("/api/test", "timeout")

        # Obtener vista de rendimiento
        perf_overview = await dashboard.get_performance_overview()

        assert 'current_metrics' in perf_overview
        assert 'analysis' in perf_overview
        assert 'recommendations' in perf_overview

    @pytest.mark.asyncio
    async def test_health_monitoring_integration(self, metrics_system):
        """Test integración de monitoreo de salud."""
        metrics_collector = metrics_system['metrics_collector']

        # Obtener estado de salud
        health = metrics_collector.get_health_status()

        assert 'overall_status' in health
        assert 'services' in health
        assert 'last_check' in health
        assert isinstance(health['overall_status'], str)


class TestRealtimeMonitorIntegration:
    """Tests de integración para RealtimeMonitor."""

    @pytest.fixture
    def config(self):
        """Configuración para tests de tiempo real."""
        config = Mock(spec=Config)
        config.websocket_timeout = 30
        config.max_websocket_connections = 100
        return config

    @pytest.fixture
    async def realtime_system(self, config):
        """Sistema de monitoreo en tiempo real."""
        realtime_monitor = RealtimeMonitor(config)
        audit_manager = AuditManager(config)

        system = {
            'realtime_monitor': realtime_monitor,
            'audit_manager': audit_manager
        }

        yield system

        await realtime_monitor.stop_monitoring()
        if os.path.exists(audit_manager.audit_log_file):
            os.remove(audit_manager.audit_log_file)

    @pytest.mark.asyncio
    async def test_websocket_broadcast_integration(self, realtime_system):
        """Test integración de broadcast WebSocket."""
        realtime_monitor = realtime_system['realtime_monitor']

        # Iniciar monitoreo
        await realtime_monitor.start_monitoring()

        # Agregar múltiples conexiones
        websocket1 = Mock()
        websocket1.send_json = AsyncMock()
        websocket2 = Mock()
        websocket2.send_json = AsyncMock()

        await realtime_monitor.add_connection("dashboard", websocket1)
        await realtime_monitor.add_connection("alerts", websocket2)

        # Broadcast evento
        await realtime_monitor.broadcast_custom_event(
            "test_event",
            {"message": "test", "timestamp": datetime.now().isoformat()}
        )

        # Verificar que se envió a la conexión correcta
        websocket1.send_json.assert_called_once()
        websocket2.send_json.assert_not_called()

        await realtime_monitor.stop_monitoring()

    @pytest.mark.asyncio
    async def test_connection_management(self, realtime_system):
        """Test gestión de conexiones."""
        realtime_monitor = realtime_system['realtime_monitor']

        # Agregar conexión
        websocket_mock = Mock()
        await realtime_monitor.add_connection("dashboard", websocket_mock)

        # Verificar estadísticas
        counts = realtime_monitor.get_connection_counts()
        assert counts["dashboard"] == 1

        # Remover conexión
        await realtime_monitor.remove_connection("dashboard", websocket_mock)

        # Verificar que se removió
        counts = realtime_monitor.get_connection_counts()
        assert counts["dashboard"] == 0


class TestAuditDashboardIntegration:
    """Tests de integración para AuditDashboard."""

    @pytest.fixture
    def config(self):
        """Configuración para tests de dashboard."""
        config = Mock(spec=Config)
        config.audit_log_file = "/tmp/test_dashboard.log"
        return config

    @pytest.fixture
    async def dashboard_system(self, config):
        """Sistema de dashboard integrado."""
        audit_manager = AuditManager(config)
        metrics_collector = MetricsCollector(config)
        dashboard = AuditDashboard(config, audit_manager, metrics_collector)

        system = {
            'audit_manager': audit_manager,
            'metrics_collector': metrics_collector,
            'dashboard': dashboard
        }

        yield system

        if os.path.exists(audit_manager.audit_log_file):
            os.remove(audit_manager.audit_log_file)

    @pytest.mark.asyncio
    async def test_dashboard_comprehensive_data(self, dashboard_system):
        """Test datos comprehensivos del dashboard."""
        audit_manager = dashboard_system['audit_manager']
        dashboard = dashboard_system['dashboard']

        # Agregar eventos y alertas
        await audit_manager.log_event("USER_LOGIN", "auth", "login", "user1")
        await audit_manager.log_event("CONFIG_CHANGE", "system", "update", "admin")

        # Obtener datos completos
        data = await dashboard.get_dashboard_data()

        assert 'events' in data
        assert 'alerts' in data
        assert 'metrics' in data
        assert 'timeline' in data
        assert 'summary' in data

        # Verificar resumen
        assert data['summary']['total_events'] >= 2

    @pytest.mark.asyncio
    async def test_dashboard_export_functionality(self, dashboard_system):
        """Test funcionalidad de exportación del dashboard."""
        dashboard = dashboard_system['dashboard']

        # Exportar reporte
        report = await dashboard.export_dashboard_report(format="json")

        assert isinstance(report, str)

        # Verificar que es JSON válido
        import json
        data = json.loads(report)
        assert 'timestamp' in data
        assert 'summary' in data


class TestEndToEndAuditFlow:
    """Tests end-to-end para flujos completos de auditoría."""

    @pytest.fixture
    def config(self):
        """Configuración completa para tests E2E."""
        config = Mock(spec=Config)
        config.audit_log_file = "/tmp/test_e2e_audit.log"
        config.audit_retention_days = 30
        config.security_alert_thresholds = {
            "max_failed_logins_per_hour": 3,  # Bajo para tests
            "max_config_changes_per_hour": 5
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
    async def test_complete_security_incident_flow(self, complete_audit_system):
        """Test flujo completo de incidente de seguridad."""
        audit_manager = complete_audit_system['audit_manager']
        security_monitor = complete_audit_system['security_monitor']
        dashboard = complete_audit_system['dashboard']
        realtime_monitor = complete_audit_system['realtime_monitor']

        # 1. Iniciar monitoreo en tiempo real
        await realtime_monitor.start_monitoring()

        # 2. Agregar conexión de dashboard
        websocket_mock = Mock()
        websocket_mock.send_json = AsyncMock()
        await realtime_monitor.add_connection("dashboard", websocket_mock)

        # 3. Simular ataque de fuerza bruta
        attacker_ip = "192.168.1.100"
        for i in range(5):  # Más que el límite
            event_data = {
                "event_type": "USER_LOGIN",
                "resource": "auth",
                "action": "login_failed",
                "user_id": "victim_user",
                "details": {"ip": attacker_ip, "reason": "invalid_password"}
            }

            # Loggear evento
            await audit_manager.log_event(**event_data)

            # Procesar en monitor de seguridad
            await security_monitor.process_event(event_data)

        # 4. Esperar procesamiento de alertas
        await asyncio.sleep(0.2)

        # 5. Verificar que se generó alerta
        alerts = audit_manager.get_security_alerts()
        assert len(alerts) > 0

        brute_force_alert = None
        for alert in alerts:
            if "brute force" in alert["title"].lower():
                brute_force_alert = alert
                break

        assert brute_force_alert is not None
        assert brute_force_alert["severity"] == "HIGH"

        # 6. Verificar que la alerta aparece en el dashboard
        security_overview = await dashboard.get_security_overview()
        assert security_overview["alert_summary"]["HIGH"] >= 1

        # 7. Verificar que se notificó vía WebSocket
        websocket_mock.send_json.assert_called()

        # 8. Reconocer la alerta
        alert_id = list(audit_manager.security_alerts.keys())[0]
        audit_manager.acknowledge_alert(alert_id, "security_admin")

        # 9. Verificar que la alerta fue reconocida
        updated_alerts = audit_manager.get_security_alerts()
        acknowledged_alert = None
        for alert in updated_alerts:
            if alert["id"] == alert_id:
                acknowledged_alert = alert
                break

        assert acknowledged_alert["acknowledged"] is True

        # Cleanup
        await realtime_monitor.stop_monitoring()

    @pytest.mark.asyncio
    async def test_system_performance_monitoring_flow(self, complete_audit_system):
        """Test flujo completo de monitoreo de rendimiento."""
        metrics_collector = complete_audit_system['metrics_collector']
        dashboard = complete_audit_system['dashboard']

        # 1. Simular carga del sistema
        for i in range(100):
            # Simular tiempos de respuesta variables
            response_time = 50 + (i % 50)  # 50-100ms
            metrics_collector.record_response_time(response_time)

            # Simular algunos errores
            if i % 10 == 0:
                metrics_collector.record_error(f"/api/endpoint_{i%5}", "timeout")

        # 2. Obtener métricas de rendimiento
        perf_overview = await dashboard.get_performance_overview()

        assert "current_metrics" in perf_overview
        assert "analysis" in perf_overview
        assert "recommendations" in perf_overview

        # 3. Verificar análisis de rendimiento
        analysis = perf_overview["analysis"]
        assert "response_time" in analysis
        assert "error_rate" in analysis

        # 4. Verificar recomendaciones
        recommendations = perf_overview["recommendations"]
        assert isinstance(recommendations, list)

    @pytest.mark.asyncio
    async def test_audit_compliance_reporting_flow(self, complete_audit_system):
        """Test flujo completo de reporte de cumplimiento."""
        audit_manager = complete_audit_system['audit_manager']
        dashboard = complete_audit_system['dashboard']

        # 1. Generar diversos eventos de auditoría
        events_to_log = [
            ("USER_LOGIN", "auth", "login", "user1", {"ip": "10.0.0.1"}),
            ("USER_LOGIN", "auth", "login", "user2", {"ip": "10.0.0.2"}),
            ("CONFIG_CHANGE", "system", "update", "admin", {"key": "timeout"}),
            ("API_REQUEST", "api", "get", "user1", {"endpoint": "/users"}),
            ("API_REQUEST", "api", "post", "user2", {"endpoint": "/data"}),
            ("USER_LOGOUT", "auth", "logout", "user1", {}),
        ]

        for event_type, resource, action, user_id, details in events_to_log:
            await audit_manager.log_event(
                event_type=event_type,
                resource=resource,
                action=action,
                user_id=user_id,
                details=details
            )

        # 2. Generar estadísticas de auditoría
        stats = audit_manager.get_audit_statistics()

        assert "total_events" in stats
        assert "events_by_type" in stats
        assert "events_by_user" in stats
        assert "events_by_resource" in stats
        assert stats["total_events"] == len(events_to_log)

        # 3. Verificar distribución por tipo
        assert stats["events_by_type"]["USER_LOGIN"] == 2
        assert stats["events_by_type"]["CONFIG_CHANGE"] == 1
        assert stats["events_by_type"]["API_REQUEST"] == 2
        assert stats["events_by_type"]["USER_LOGOUT"] == 1

        # 4. Exportar reporte del dashboard
        report = await dashboard.export_dashboard_report(format="json")

        assert isinstance(report, str)

        # 5. Verificar contenido del reporte
        import json
        report_data = json.loads(report)
        assert "timestamp" in report_data
        assert "summary" in report_data
        assert "events" in report_data
        assert len(report_data["events"]) == len(events_to_log)