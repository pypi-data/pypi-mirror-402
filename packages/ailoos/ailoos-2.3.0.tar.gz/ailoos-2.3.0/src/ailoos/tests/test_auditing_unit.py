"""
Tests unitarios para el módulo de auditoría.
Cubre todas las funcionalidades principales del sistema de auditoría.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import json
import tempfile
import os
from pathlib import Path

from src.ailoos.auditing.audit_manager import (
    AuditManager, AuditEvent, AuditEventType, SecurityAlert,
    SecurityAlertLevel, SystemMetrics
)
from src.ailoos.auditing.structured_logger import StructuredLogger, get_structured_logger
from src.ailoos.auditing.security_monitor import SecurityMonitor, SecurityRule, ThreatIndicator
from src.ailoos.auditing.metrics_collector import MetricsCollector, PerformanceMetrics, ResourceMetrics
from src.ailoos.auditing.dashboard import AuditDashboard
from src.ailoos.auditing.realtime_monitor import RealtimeMonitor
from src.ailoos.core.config import Config


class TestAuditEvent:
    """Tests para la clase AuditEvent."""

    def test_audit_event_creation(self):
        """Test creación básica de evento de auditoría."""
        event = AuditEvent(
            event_type=AuditEventType.USER_LOGIN,
            resource="user_auth",
            action="login_attempt",
            user_id="user123",
            details={"ip": "192.168.1.1", "success": True}
        )

        assert event.event_type == AuditEventType.USER_LOGIN
        assert event.resource == "user_auth"
        assert event.action == "login_attempt"
        assert event.user_id == "user123"
        assert event.details["ip"] == "192.168.1.1"
        assert event.details["success"] is True
        assert isinstance(event.timestamp, datetime)

    def test_audit_event_to_dict(self):
        """Test conversión de evento a diccionario."""
        event = AuditEvent(
            event_type=AuditEventType.CONFIG_CHANGE,
            resource="system_config",
            action="update",
            user_id="admin",
            details={"key": "timeout", "old_value": 30, "new_value": 60}
        )

        event_dict = event.to_dict()

        assert event_dict["event_type"] == "CONFIG_CHANGE"
        assert event_dict["resource"] == "system_config"
        assert event_dict["action"] == "update"
        assert event_dict["user_id"] == "admin"
        assert "timestamp" in event_dict
        assert event_dict["details"]["key"] == "timeout"


class TestSecurityAlert:
    """Tests para la clase SecurityAlert."""

    def test_security_alert_creation(self):
        """Test creación básica de alerta de seguridad."""
        alert = SecurityAlert(
            severity=SecurityAlertLevel.HIGH,
            title="Brute Force Attack Detected",
            description="Multiple failed login attempts from IP 192.168.1.1",
            context={"ip": "192.168.1.1", "attempts": 10, "timeframe": "5min"}
        )

        assert alert.severity == SecurityAlertLevel.HIGH
        assert alert.title == "Brute Force Attack Detected"
        assert alert.description == "Multiple failed login attempts from IP 192.168.1.1"
        assert alert.context["ip"] == "192.168.1.1"
        assert alert.context["attempts"] == 10
        assert isinstance(alert.timestamp, datetime)
        assert alert.acknowledged is False

    def test_security_alert_to_dict(self):
        """Test conversión de alerta a diccionario."""
        alert = SecurityAlert(
            severity=SecurityAlertLevel.MEDIUM,
            title="Suspicious Activity",
            description="Unusual login pattern detected",
            context={"user_id": "user123", "pattern": "multiple_ips"}
        )

        alert_dict = alert.to_dict()

        assert alert_dict["severity"] == "MEDIUM"
        assert alert_dict["title"] == "Suspicious Activity"
        assert alert_dict["description"] == "Unusual login pattern detected"
        assert alert_dict["acknowledged"] is False
        assert "timestamp" in alert_dict


class TestSystemMetrics:
    """Tests para la clase SystemMetrics."""

    def test_system_metrics_creation(self):
        """Test creación básica de métricas del sistema."""
        metrics = SystemMetrics(
            cpu_usage=45.5,
            memory_usage=67.8,
            disk_usage=23.1,
            network_traffic=150.5,
            active_connections=25,
            error_rate=0.02,
            avg_response_time=125.3
        )

        assert metrics.cpu_usage == 45.5
        assert metrics.memory_usage == 67.8
        assert metrics.disk_usage == 23.1
        assert metrics.network_traffic == 150.5
        assert metrics.active_connections == 25
        assert metrics.error_rate == 0.02
        assert metrics.avg_response_time == 125.3
        assert isinstance(metrics.timestamp, datetime)

    def test_system_metrics_to_dict(self):
        """Test conversión de métricas a diccionario."""
        metrics = SystemMetrics(
            cpu_usage=30.0,
            memory_usage=50.0,
            disk_usage=40.0,
            network_traffic=100.0,
            active_connections=10,
            error_rate=0.01,
            avg_response_time=100.0
        )

        metrics_dict = metrics.to_dict()

        assert metrics_dict["cpu_usage"] == 30.0
        assert metrics_dict["memory_usage"] == 50.0
        assert metrics_dict["disk_usage"] == 40.0
        assert metrics_dict["network_traffic"] == 100.0
        assert metrics_dict["active_connections"] == 10
        assert metrics_dict["error_rate"] == 0.01
        assert metrics_dict["avg_response_time"] == 100.0
        assert "timestamp" in metrics_dict


class TestAuditManager:
    """Tests para la clase AuditManager."""

    @pytest.fixture
    def config(self):
        """Configuración mock para tests."""
        config = Mock(spec=Config)
        config.audit_log_file = "/tmp/test_audit.log"
        config.audit_retention_days = 30
        config.security_alert_thresholds = {
            "max_failed_logins_per_hour": 5,
            "max_config_changes_per_hour": 10
        }
        return config

    @pytest.fixture
    async def audit_manager(self, config):
        """Instancia de AuditManager para tests."""
        manager = AuditManager(config)
        yield manager
        # Cleanup
        if os.path.exists(manager.audit_log_file):
            os.remove(manager.audit_log_file)

    @pytest.mark.asyncio
    async def test_audit_manager_initialization(self, audit_manager):
        """Test inicialización del AuditManager."""
        assert audit_manager.audit_log_file.endswith("test_audit.log")
        assert audit_manager.audit_events == []
        assert audit_manager.security_alerts == []
        assert audit_manager.system_metrics == []
        assert audit_manager._background_tasks is not None

    @pytest.mark.asyncio
    async def test_log_event(self, audit_manager):
        """Test logging de eventos."""
        await audit_manager.log_event(
            event_type=AuditEventType.USER_LOGIN,
            resource="auth",
            action="login",
            user_id="user123",
            details={"ip": "192.168.1.1", "success": True}
        )

        assert len(audit_manager.audit_events) == 1
        event = audit_manager.audit_events[0]
        assert event.event_type == AuditEventType.USER_LOGIN
        assert event.resource == "auth"
        assert event.user_id == "user123"

    @pytest.mark.asyncio
    async def test_security_alert_generation(self, audit_manager):
        """Test generación automática de alertas de seguridad."""
        # Generar múltiples eventos de login fallido
        for i in range(6):
            await audit_manager.log_event(
                event_type=AuditEventType.USER_LOGIN,
                resource="auth",
                action="login_failed",
                user_id="user123",
                details={"ip": "192.168.1.1", "reason": "invalid_password"}
            )

        # Esperar procesamiento de alertas
        await asyncio.sleep(0.1)

        # Verificar que se generó una alerta
        alerts = audit_manager.get_security_alerts()
        assert len(alerts) > 0

        # Encontrar alerta de brute force
        brute_force_alert = None
        for alert in alerts:
            if "brute force" in alert["title"].lower():
                brute_force_alert = alert
                break

        assert brute_force_alert is not None
        assert brute_force_alert["severity"] == "HIGH"

    def test_acknowledge_alert(self, audit_manager):
        """Test reconocimiento de alertas."""
        # Crear alerta manualmente para test
        alert = SecurityAlert(
            severity=SecurityAlertLevel.MEDIUM,
            title="Test Alert",
            description="Test description",
            context={}
        )
        alert_id = "test_alert_123"
        audit_manager.security_alerts.append((alert_id, alert))

        # Reconocer alerta
        audit_manager.acknowledge_alert(alert_id, "admin_user")

        # Verificar que fue reconocida
        updated_alert = None
        for aid, a in audit_manager.security_alerts:
            if aid == alert_id:
                updated_alert = a
                break

        assert updated_alert.acknowledged is True
        assert updated_alert.acknowledged_by == "admin_user"

    def test_get_audit_events(self, audit_manager):
        """Test obtención de eventos de auditoría."""
        # Crear algunos eventos de prueba
        events_data = [
            {
                "event_type": AuditEventType.USER_LOGIN,
                "resource": "auth",
                "action": "login",
                "user_id": "user1"
            },
            {
                "event_type": AuditEventType.CONFIG_CHANGE,
                "resource": "system",
                "action": "update",
                "user_id": "admin"
            }
        ]

        for event_data in events_data:
            event = AuditEvent(**event_data)
            audit_manager.audit_events.append(event)

        # Obtener eventos
        events = audit_manager.get_audit_events()

        assert len(events) == 2
        assert events[0]["event_type"] == "USER_LOGIN"
        assert events[1]["event_type"] == "CONFIG_CHANGE"

    def test_get_audit_statistics(self, audit_manager):
        """Test obtención de estadísticas de auditoría."""
        # Crear eventos de prueba
        events_data = [
            {"event_type": AuditEventType.USER_LOGIN, "resource": "auth", "action": "login", "user_id": "user1"},
            {"event_type": AuditEventType.USER_LOGIN, "resource": "auth", "action": "login", "user_id": "user2"},
            {"event_type": AuditEventType.CONFIG_CHANGE, "resource": "system", "action": "update", "user_id": "admin"},
            {"event_type": AuditEventType.API_REQUEST, "resource": "api", "action": "get", "user_id": "user1"},
        ]

        for event_data in events_data:
            event = AuditEvent(**event_data)
            audit_manager.audit_events.append(event)

        # Obtener estadísticas
        stats = audit_manager.get_audit_statistics()

        assert "total_events" in stats
        assert "events_by_type" in stats
        assert "events_by_user" in stats
        assert "events_by_resource" in stats
        assert stats["total_events"] == 4
        assert stats["events_by_type"]["USER_LOGIN"] == 2
        assert stats["events_by_type"]["CONFIG_CHANGE"] == 1
        assert stats["events_by_type"]["API_REQUEST"] == 1


class TestStructuredLogger:
    """Tests para la clase StructuredLogger."""

    @pytest.fixture
    def logger(self):
        """Instancia de StructuredLogger para tests."""
        return StructuredLogger("test_module", audit_events=True)

    def test_logger_initialization(self, logger):
        """Test inicialización del logger."""
        assert logger.name == "test_module"
        assert logger.audit_events is True
        assert logger.context.operation is None
        assert logger.context.user_id is None

    def test_context_setting(self, logger):
        """Test configuración de contexto."""
        logger.with_context(user_id="user123", operation="test_op")

        assert logger.context.user_id == "user123"
        assert logger.context.operation == "test_op"

    def test_start_operation(self, logger):
        """Test inicio de operación."""
        operation_id = logger.start_operation("test_operation", resource="test_resource")

        assert operation_id is not None
        assert isinstance(operation_id, str)
        assert logger.context.operation == "test_operation"
        assert logger.context.resource == "test_resource"

    def test_end_operation_success(self, logger):
        """Test finalización exitosa de operación."""
        operation_id = logger.start_operation("test_operation")

        # Simular finalización exitosa
        logger.end_operation(success=True, result="success_data")

        # Verificar que el contexto se limpió
        assert logger.context.operation is None

    def test_end_operation_failure(self, logger):
        """Test finalización fallida de operación."""
        operation_id = logger.start_operation("test_operation")

        # Simular finalización con error
        test_error = ValueError("Test error")
        logger.end_operation(success=False, error=test_error)

        # Verificar que el contexto se limpió
        assert logger.context.operation is None

    @patch('src.ailoos.auditing.structured_logger.logger')
    def test_log_api_request(self, mock_std_logger, logger):
        """Test logging de requests API."""
        logger.log_api_request(
            method="POST",
            endpoint="/api/test",
            status_code=200,
            duration_ms=150.5,
            user_id="user123"
        )

        # Verificar que se llamó al logger estándar
        mock_std_logger.info.assert_called_once()
        call_args = mock_std_logger.info.call_args
        assert "API Request" in call_args[0][0]
        assert call_args[1]["extra"]["method"] == "POST"
        assert call_args[1]["extra"]["endpoint"] == "/api/test"
        assert call_args[1]["extra"]["status_code"] == 200
        assert call_args[1]["extra"]["duration_ms"] == 150.5

    @patch('src.ailoos.auditing.structured_logger.logger')
    def test_log_security_event(self, mock_std_logger, logger):
        """Test logging de eventos de seguridad."""
        logger.log_security_event(
            event_type="login_attempt",
            details={"ip": "192.168.1.1", "success": False},
            severity=SecurityAlertLevel.HIGH
        )

        mock_std_logger.warning.assert_called_once()
        call_args = mock_std_logger.warning.call_args
        assert "Security Event" in call_args[0][0]
        assert call_args[1]["extra"]["event_type"] == "login_attempt"
        assert call_args[1]["extra"]["severity"] == "HIGH"

    @patch('src.ailoos.auditing.structured_logger.logger')
    def test_log_config_change(self, mock_std_logger, logger):
        """Test logging de cambios de configuración."""
        logger.log_config_change(
            key="timeout",
            old_value=30,
            new_value=60,
            changed_by="admin"
        )

        mock_std_logger.info.assert_called_once()
        call_args = mock_std_logger.info.call_args
        assert "Configuration Change" in call_args[0][0]
        assert call_args[1]["extra"]["key"] == "timeout"
        assert call_args[1]["extra"]["old_value"] == 30
        assert call_args[1]["extra"]["new_value"] == 60

    def test_get_structured_logger(self):
        """Test obtención de instancia de StructuredLogger."""
        logger = get_structured_logger("test_module")

        assert isinstance(logger, StructuredLogger)
        assert logger.name == "test_module"
        assert logger.audit_events is True


class TestSecurityMonitor:
    """Tests para la clase SecurityMonitor."""

    @pytest.fixture
    def config(self):
        """Configuración mock para tests."""
        config = Mock(spec=Config)
        config.security_rules_file = "/tmp/test_security_rules.json"
        config.threat_intelligence_file = "/tmp/test_threats.json"
        return config

    @pytest.fixture
    def security_monitor(self, config):
        """Instancia de SecurityMonitor para tests."""
        monitor = SecurityMonitor(config)
        return monitor

    def test_security_rule_creation(self):
        """Test creación de regla de seguridad."""
        rule = SecurityRule(
            rule_id="test_rule",
            name="Test Rule",
            description="Test security rule",
            severity=SecurityAlertLevel.MEDIUM,
            conditions=[
                {
                    "field": "event_type",
                    "operator": "equals",
                    "value": "USER_LOGIN"
                },
                {
                    "field": "details.success",
                    "operator": "equals",
                    "value": False
                }
            ],
            action="alert"
        )

        assert rule.rule_id == "test_rule"
        assert rule.name == "Test Rule"
        assert rule.severity == SecurityAlertLevel.MEDIUM
        assert len(rule.conditions) == 2

    def test_security_rule_matches(self):
        """Test evaluación de coincidencias de regla de seguridad."""
        rule = SecurityRule(
            rule_id="failed_login",
            name="Failed Login Detection",
            description="Detect failed login attempts",
            severity=SecurityAlertLevel.LOW,
            conditions=[
                {
                    "field": "event_type",
                    "operator": "equals",
                    "value": "USER_LOGIN"
                },
                {
                    "field": "details.success",
                    "operator": "equals",
                    "value": False
                }
            ],
            action="alert"
        )

        # Evento que coincide
        matching_event = {
            "event_type": "USER_LOGIN",
            "details": {"success": False, "ip": "192.168.1.1"}
        }
        assert rule.matches(matching_event) is True

        # Evento que no coincide
        non_matching_event = {
            "event_type": "USER_LOGIN",
            "details": {"success": True, "ip": "192.168.1.1"}
        }
        assert rule.matches(non_matching_event) is False

    def test_threat_indicator_creation(self):
        """Test creación de indicador de amenaza."""
        indicator = ThreatIndicator(
            indicator_id="test_indicator",
            name="Test Indicator",
            type="ip_address",
            value="192.168.1.100",
            severity=SecurityAlertLevel.HIGH,
            description="Known malicious IP",
            tags=["malware", "botnet"]
        )

        assert indicator.indicator_id == "test_indicator"
        assert indicator.name == "Test Indicator"
        assert indicator.type == "ip_address"
        assert indicator.value == "192.168.1.100"
        assert indicator.severity == SecurityAlertLevel.HIGH
        assert indicator.hit_count == 0
        assert isinstance(indicator.first_seen, datetime)
        assert isinstance(indicator.last_seen, datetime)

    def test_threat_indicator_update_hit(self):
        """Test actualización de contador de hits."""
        indicator = ThreatIndicator(
            indicator_id="test",
            name="Test",
            type="ip",
            value="192.168.1.1",
            severity=SecurityAlertLevel.MEDIUM,
            description="Test indicator"
        )

        initial_last_seen = indicator.last_seen

        # Simular hit
        indicator.update_hit()

        assert indicator.hit_count == 1
        assert indicator.last_seen > initial_last_seen

    @pytest.mark.asyncio
    async def test_process_event_with_rule_match(self, security_monitor):
        """Test procesamiento de evento que coincide con regla."""
        # Agregar regla de prueba
        rule = SecurityRule(
            rule_id="test_rule",
            name="Test Rule",
            description="Test rule for unit test",
            severity=SecurityAlertLevel.MEDIUM,
            conditions=[
                {
                    "field": "event_type",
                    "operator": "equals",
                    "value": "TEST_EVENT"
                }
            ],
            action="alert"
        )
        security_monitor.add_security_rule(rule)

        # Procesar evento que coincide
        event_data = {
            "event_type": "TEST_EVENT",
            "resource": "test",
            "action": "test_action",
            "user_id": "test_user"
        }

        with patch.object(security_monitor, '_send_alert') as mock_send:
            await security_monitor.process_event(event_data)

            # Verificar que se envió alerta
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == SecurityAlertLevel.MEDIUM
            assert "Test Rule" in call_args[0][1]

    def test_add_security_rule(self, security_monitor):
        """Test agregado de regla de seguridad."""
        rule = SecurityRule(
            rule_id="new_rule",
            name="New Rule",
            description="New security rule",
            severity=SecurityAlertLevel.LOW,
            conditions=[{"field": "test", "operator": "equals", "value": "test"}],
            action="alert"
        )

        security_monitor.add_security_rule(rule)

        assert "new_rule" in security_monitor.security_rules
        assert security_monitor.security_rules["new_rule"] == rule

    def test_remove_security_rule(self, security_monitor):
        """Test eliminación de regla de seguridad."""
        # Agregar regla primero
        rule = SecurityRule(
            rule_id="rule_to_remove",
            name="Rule to Remove",
            description="Rule for removal test",
            severity=SecurityAlertLevel.LOW,
            conditions=[{"field": "test", "operator": "equals", "value": "test"}],
            action="alert"
        )
        security_monitor.add_security_rule(rule)

        # Verificar que existe
        assert "rule_to_remove" in security_monitor.security_rules

        # Remover regla
        security_monitor.remove_security_rule("rule_to_remove")

        # Verificar que fue removida
        assert "rule_to_remove" not in security_monitor.security_rules

    def test_get_security_status(self, security_monitor):
        """Test obtención de estado de seguridad."""
        status = security_monitor.get_security_status()

        assert "total_rules" in status
        assert "total_indicators" in status
        assert "active_alerts" in status
        assert "last_scan" in status
        assert isinstance(status["total_rules"], int)
        assert isinstance(status["total_indicators"], int)


class TestMetricsCollector:
    """Tests para la clase MetricsCollector."""

    @pytest.fixture
    def config(self):
        """Configuración mock para tests."""
        config = Mock(spec=Config)
        config.metrics_collection_interval = 60
        config.metrics_retention_hours = 24
        return config

    @pytest.fixture
    async def metrics_collector(self, config):
        """Instancia de MetricsCollector para tests."""
        collector = MetricsCollector(config)
        yield collector
        # Cleanup if needed

    @pytest.mark.asyncio
    async def test_metrics_collector_initialization(self, metrics_collector):
        """Test inicialización del MetricsCollector."""
        assert metrics_collector.collection_interval == 60
        assert metrics_collector.retention_hours == 24
        assert metrics_collector.performance_metrics == []
        assert metrics_collector.resource_metrics == []
        assert metrics_collector.application_metrics == []

    def test_performance_metrics_creation(self):
        """Test creación de métricas de rendimiento."""
        metrics = PerformanceMetrics(
            response_time_ms=150.5,
            throughput_req_per_sec=25.3,
            error_rate_percent=0.5,
            cpu_usage_percent=45.2,
            memory_usage_percent=67.8
        )

        assert metrics.response_time_ms == 150.5
        assert metrics.throughput_req_per_sec == 25.3
        assert metrics.error_rate_percent == 0.5
        assert metrics.cpu_usage_percent == 45.2
        assert metrics.memory_usage_percent == 67.8
        assert isinstance(metrics.timestamp, datetime)

    def test_resource_metrics_creation(self):
        """Test creación de métricas de recursos."""
        metrics = ResourceMetrics(
            cpu_percent=30.5,
            memory_percent=60.2,
            disk_percent=25.1,
            network_bytes_sent=1024000,
            network_bytes_recv=2048000,
            active_connections=15
        )

        assert metrics.cpu_percent == 30.5
        assert metrics.memory_percent == 60.2
        assert metrics.disk_percent == 25.1
        assert metrics.network_bytes_sent == 1024000
        assert metrics.network_bytes_recv == 2048000
        assert metrics.active_connections == 15

    def test_application_metrics_creation(self):
        """Test creación de métricas de aplicación."""
        metrics = ResourceMetrics(
            cpu_percent=30.5,
            memory_percent=60.2,
            disk_percent=25.1,
            network_bytes_sent=1024000,
            network_bytes_recv=2048000,
            active_connections=15
        )

        assert metrics.cpu_percent == 30.5
        assert metrics.memory_percent == 60.2
        assert metrics.disk_percent == 25.1
        assert metrics.network_bytes_sent == 1024000
        assert metrics.network_bytes_recv == 2048000
        assert metrics.active_connections == 15

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.net_io_counters')
    def test_collect_resource_metrics(self, mock_net, mock_disk, mock_memory, mock_cpu, metrics_collector):
        """Test recolección de métricas de recursos."""
        # Configurar mocks
        mock_cpu.return_value = 45.5
        mock_memory.return_value = Mock(percent=67.8)
        mock_disk.return_value = Mock(percent=23.1)
        mock_net.return_value = Mock(bytes_sent=1024000, bytes_recv=2048000)

        # Ejecutar recolección
        metrics = metrics_collector._collect_resource_metrics()

        assert metrics.cpu_percent == 45.5
        assert metrics.memory_percent == 67.8
        assert metrics.disk_percent == 23.1
        assert metrics.network_bytes_sent == 1024000
        assert metrics.network_bytes_recv == 2048000

    def test_record_response_time(self, metrics_collector):
        """Test registro de tiempo de respuesta."""
        metrics_collector.record_response_time(150.5)

        # Verificar que se agregó a la lista de tiempos de respuesta
        assert 150.5 in metrics_collector.response_times

    def test_record_error(self, metrics_collector):
        """Test registro de error."""
        metrics_collector.record_error("/api/test", "validation_error")

        # Verificar que se incrementó el contador de errores
        assert metrics_collector.error_counts["/api/test:validation_error"] == 1

    def test_get_latest_metrics(self, metrics_collector):
        """Test obtención de métricas más recientes."""
        # Agregar algunas métricas de prueba
        perf_metrics = PerformanceMetrics(
            response_time_ms=100.0,
            throughput_req_per_sec=20.0,
            error_rate_percent=0.1,
            cpu_usage_percent=30.0,
            memory_usage_percent=50.0
        )
        metrics_collector.performance_metrics.append(perf_metrics)

        res_metrics = ResourceMetrics(
            cpu_percent=30.0,
            memory_percent=50.0,
            disk_percent=40.0,
            network_bytes_sent=1000,
            network_bytes_recv=2000,
            active_connections=10
        )
        metrics_collector.resource_metrics.append(res_metrics)

        # Obtener métricas más recientes
        latest = metrics_collector.get_latest_metrics()

        assert "performance" in latest
        assert "resources" in latest
        assert "application" in latest
        assert latest["performance"]["response_time_ms"] == 100.0
        assert latest["resources"]["cpu_percent"] == 30.0

    def test_get_metrics_history(self, metrics_collector):
        """Test obtención de historial de métricas."""
        # Agregar métricas de prueba con diferentes timestamps
        base_time = datetime.now()

        for i in range(5):
            perf_metrics = PerformanceMetrics(
                response_time_ms=100.0 + i * 10,
                throughput_req_per_sec=20.0,
                error_rate_percent=0.1,
                cpu_usage_percent=30.0,
                memory_usage_percent=50.0
            )
            # Simular timestamp anterior
            perf_metrics.timestamp = base_time - timedelta(hours=i)
            metrics_collector.performance_metrics.append(perf_metrics)

        # Obtener historial de 2 horas
        history = metrics_collector.get_metrics_history(hours=2)

        assert "performance" in history
        assert "resources" in history
        assert "application" in history
        # Debería incluir métricas de las últimas 2 horas
        assert len(history["performance"]) >= 2

    def test_get_health_status(self, metrics_collector):
        """Test obtención de estado de salud."""
        health = metrics_collector.get_health_status()

        assert "overall_status" in health
        assert "services" in health
        assert "last_check" in health
        assert isinstance(health["overall_status"], str)
        assert isinstance(health["services"], dict)


class TestAuditDashboard:
    """Tests para la clase AuditDashboard."""

    @pytest.fixture
    def config(self):
        """Configuración mock para tests."""
        config = Mock(spec=Config)
        return config

    @pytest.fixture
    def audit_manager(self):
        """AuditManager mock para tests."""
        manager = Mock(spec=AuditManager)
        return manager

    @pytest.fixture
    def metrics_collector(self):
        """MetricsCollector mock para tests."""
        collector = Mock(spec=MetricsCollector)
        return collector

    @pytest.fixture
    def dashboard(self, config, audit_manager, metrics_collector):
        """Instancia de AuditDashboard para tests."""
        dashboard = AuditDashboard(config, audit_manager, metrics_collector)
        return dashboard

    @pytest.mark.asyncio
    async def test_get_dashboard_data(self, dashboard, audit_manager, metrics_collector):
        """Test obtención de datos del dashboard."""
        # Configurar mocks
        audit_manager.get_audit_events.return_value = [
            {
                "event_type": "USER_LOGIN",
                "resource": "auth",
                "action": "login",
                "user_id": "user1",
                "timestamp": datetime.now().isoformat()
            }
        ]

        audit_manager.get_security_alerts.return_value = [
            {
                "severity": "HIGH",
                "title": "Test Alert",
                "description": "Test alert description",
                "timestamp": datetime.now().isoformat(),
                "acknowledged": False
            }
        ]

        metrics_collector.get_latest_metrics.return_value = {
            "performance": {"response_time_ms": 100.0, "error_rate_percent": 0.1},
            "resources": {"cpu_percent": 30.0, "memory_percent": 50.0}
        }

        # Obtener datos del dashboard
        data = await dashboard.get_dashboard_data()

        assert "events" in data
        assert "alerts" in data
        assert "metrics" in data
        assert "timeline" in data
        assert "summary" in data
        assert len(data["events"]) == 1
        assert len(data["alerts"]) == 1

    def test_generate_events_timeline(self, dashboard):
        """Test generación de timeline de eventos."""
        events = [
            {
                "event_type": "USER_LOGIN",
                "resource": "auth",
                "action": "login",
                "user_id": "user1",
                "timestamp": datetime.now().isoformat()
            },
            {
                "event_type": "CONFIG_CHANGE",
                "resource": "system",
                "action": "update",
                "user_id": "admin",
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat()
            }
        ]

        timeline = dashboard._generate_events_timeline(events)

        assert len(timeline) == 2
        assert timeline[0]["type"] == "USER_LOGIN"
        assert timeline[1]["type"] == "CONFIG_CHANGE"

    def test_generate_alerts_timeline(self, dashboard):
        """Test generación de timeline de alertas."""
        alerts = [
            {
                "severity": "HIGH",
                "title": "Alert 1",
                "description": "Description 1",
                "timestamp": datetime.now().isoformat(),
                "acknowledged": False
            },
            {
                "severity": "MEDIUM",
                "title": "Alert 2",
                "description": "Description 2",
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "acknowledged": True
            }
        ]

        timeline = dashboard._generate_alerts_timeline(alerts)

        assert len(timeline) == 2
        assert timeline[0]["severity"] == "HIGH"
        assert timeline[1]["severity"] == "MEDIUM"

    @pytest.mark.asyncio
    async def test_get_security_overview(self, dashboard, audit_manager):
        """Test obtención de vista general de seguridad."""
        # Configurar mock de alertas
        audit_manager.get_security_alerts.return_value = [
            {
                "severity": "HIGH",
                "title": "Brute Force",
                "description": "Multiple failed logins",
                "timestamp": datetime.now().isoformat(),
                "acknowledged": False
            },
            {
                "severity": "MEDIUM",
                "title": "Suspicious Activity",
                "description": "Unusual pattern",
                "timestamp": datetime.now().isoformat(),
                "acknowledged": True
            }
        ]

        overview = await dashboard.get_security_overview()

        assert "alert_summary" in overview
        assert "security_score" in overview
        assert "recommendations" in overview
        assert "threat_trends" in overview
        assert overview["alert_summary"]["HIGH"] == 1
        assert overview["alert_summary"]["MEDIUM"] == 1

    def test_calculate_security_score(self, dashboard):
        """Test cálculo de puntuación de seguridad."""
        alerts = [
            {"severity": "HIGH", "acknowledged": False},
            {"severity": "MEDIUM", "acknowledged": False},
            {"severity": "LOW", "acknowledged": True}
        ]

        security_status = {"overall_status": "warning"}

        score = dashboard._calculate_security_score(alerts, security_status)

        # La puntuación debería ser menor a 100 debido a las alertas
        assert isinstance(score, float)
        assert 0 <= score <= 100

    @pytest.mark.asyncio
    async def test_get_performance_overview(self, dashboard, metrics_collector):
        """Test obtención de vista general de rendimiento."""
        # Configurar mock de métricas
        metrics_collector.get_latest_metrics.return_value = {
            "performance": {
                "response_time_ms": 150.0,
                "error_rate_percent": 0.5,
                "throughput_req_per_sec": 25.0
            },
            "resources": {
                "cpu_percent": 45.0,
                "memory_percent": 60.0
            }
        }

        overview = await dashboard.get_performance_overview()

        assert "current_metrics" in overview
        assert "analysis" in overview
        assert "recommendations" in overview
        assert "trends" in overview
        assert overview["current_metrics"]["response_time_ms"] == 150.0

    def test_analyze_response_time(self, dashboard):
        """Test análisis de tiempo de respuesta."""
        # Tiempo de respuesta bueno
        analysis = dashboard._analyze_response_time(100.0)
        assert "good" in analysis.lower() or "excellent" in analysis.lower()

        # Tiempo de respuesta malo
        analysis = dashboard._analyze_response_time(5000.0)
        assert "poor" in analysis.lower() or "slow" in analysis.lower()

    def test_analyze_error_rate(self, dashboard):
        """Test análisis de tasa de error."""
        # Tasa de error baja
        analysis = dashboard._analyze_error_rate(0.01)
        assert "good" in analysis.lower() or "low" in analysis.lower()

        # Tasa de error alta
        analysis = dashboard._analyze_error_rate(0.15)
        assert "high" in analysis.lower() or "concerning" in analysis.lower()

    @pytest.mark.asyncio
    async def test_export_dashboard_report(self, dashboard):
        """Test exportación de reporte del dashboard."""
        # Configurar mocks para datos básicos
        dashboard.audit_manager.get_audit_events.return_value = []
        dashboard.audit_manager.get_security_alerts.return_value = []
        dashboard.metrics_collector.get_latest_metrics.return_value = {
            "performance": {}, "resources": {}, "application": {}
        }

        # Exportar como JSON
        report = await dashboard.export_dashboard_report(format="json")

        assert isinstance(report, str)
        # Debería ser JSON válido
        import json
        data = json.loads(report)
        assert "timestamp" in data
        assert "summary" in data


class TestRealtimeMonitor:
    """Tests para la clase RealtimeMonitor."""

    @pytest.fixture
    def config(self):
        """Configuración mock para tests."""
        config = Mock(spec=Config)
        config.websocket_timeout = 30
        config.max_websocket_connections = 100
        return config

    @pytest.fixture
    async def realtime_monitor(self, config):
        """Instancia de RealtimeMonitor para tests."""
        monitor = RealtimeMonitor(config)
        yield monitor
        # Cleanup
        await monitor.stop_monitoring()

    @pytest.mark.asyncio
    async def test_realtime_monitor_initialization(self, realtime_monitor):
        """Test inicialización del RealtimeMonitor."""
        assert realtime_monitor.connections == {}
        assert realtime_monitor.monitoring_task is None

    @pytest.mark.asyncio
    async def test_start_and_stop_monitoring(self, realtime_monitor):
        """Test inicio y parada del monitoreo."""
        # Iniciar monitoreo
        await realtime_monitor.start_monitoring()
        assert realtime_monitor.monitoring_task is not None
        assert not realtime_monitor.monitoring_task.done()

        # Parar monitoreo
        await realtime_monitor.stop_monitoring()
        assert realtime_monitor.monitoring_task.done()

    def test_register_event_callbacks(self, realtime_monitor):
        """Test registro de callbacks de eventos."""
        # Los callbacks deberían estar registrados durante la inicialización
        assert hasattr(realtime_monitor, '_RealtimeMonitor__alert_callback')
        assert hasattr(realtime_monitor, '_RealtimeMonitor__metrics_callback')

    @pytest.mark.asyncio
    async def test_add_connection(self, realtime_monitor):
        """Test agregado de conexión WebSocket."""
        # Mock de conexión WebSocket
        websocket_mock = Mock()
        websocket_mock.receive_json = AsyncMock(return_value={"type": "subscribe", "channels": ["alerts"]})

        # Agregar conexión
        await realtime_monitor.add_connection("alerts", websocket_mock)

        assert "alerts" in realtime_monitor.connections
        assert len(realtime_monitor.connections["alerts"]) == 1

    @pytest.mark.asyncio
    async def test_remove_connection(self, realtime_monitor):
        """Test eliminación de conexión WebSocket."""
        # Agregar conexión primero
        websocket_mock = Mock()
        await realtime_monitor.add_connection("alerts", websocket_mock)

        # Verificar que existe
        assert len(realtime_monitor.connections["alerts"]) == 1

        # Remover conexión
        await realtime_monitor.remove_connection("alerts", websocket_mock)

        assert len(realtime_monitor.connections["alerts"]) == 0

    def test_get_connection_counts(self, realtime_monitor):
        """Test obtención de conteos de conexiones."""
        counts = realtime_monitor.get_connection_counts()

        assert isinstance(counts, dict)
        assert "total" in counts

    @pytest.mark.asyncio
    async def test_broadcast_custom_event(self, realtime_monitor):
        """Test broadcast de evento personalizado."""
        # Agregar conexión mock
        websocket_mock = Mock()
        websocket_mock.send_json = AsyncMock()
        await realtime_monitor.add_connection("dashboard", websocket_mock)

        # Broadcast evento
        await realtime_monitor.broadcast_custom_event(
            "test_event",
            {"message": "test data", "timestamp": datetime.now().isoformat()}
        )

        # Verificar que se envió el mensaje
        websocket_mock.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_realtime_snapshot(self, realtime_monitor):
        """Test obtención de snapshot en tiempo real."""
        snapshot = await realtime_monitor.get_realtime_snapshot()

        assert "timestamp" in snapshot
        assert "connections" in snapshot
        assert "active_channels" in snapshot
        assert isinstance(snapshot["connections"], dict)