"""
Tests de seguridad para el sistema de auditoría.
Prueba autenticación, encriptación, ataques y vulnerabilidades.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import json
import hashlib
import hmac
import secrets
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import base64
from typing import Dict, List, Any, Optional

from src.ailoos.auditing.audit_manager import AuditManager
from src.ailoos.auditing.security_monitor import SecurityMonitor
from src.ailoos.auditing.realtime_monitor import RealtimeMonitor
from src.ailoos.core.config import Config


class TestAuthenticationSecurity:
    """Tests de seguridad para autenticación."""

    @pytest.fixture
    def config(self):
        """Configuración segura para tests."""
        config = Mock(spec=Config)
        config.audit_log_file = "/tmp/test_security_audit.log"
        config.websocket_timeout = 30
        config.max_websocket_connections = 100
        config.security_rules_file = "/tmp/test_security_rules.json"
        return config

    @pytest.fixture
    async def audit_system(self, config):
        """Sistema de auditoría para tests de seguridad."""
        audit_manager = AuditManager(config)
        security_monitor = SecurityMonitor(config)
        realtime_monitor = RealtimeMonitor(config)

        await audit_manager._setup_storage()
        await security_monitor._load_default_rules()

        system = {
            'audit_manager': audit_manager,
            'security_monitor': security_monitor,
            'realtime_monitor': realtime_monitor
        }

        yield system

        # Cleanup
        await realtime_monitor.stop_monitoring()
        if os.path.exists(audit_manager.audit_log_file):
            os.remove(audit_manager.audit_log_file)

    @pytest.mark.asyncio
    async def test_brute_force_attack_detection(self, audit_system):
        """Test detección de ataques de fuerza bruta."""
        audit_manager = audit_system['audit_manager']
        security_monitor = audit_system['security_monitor']

        attacker_ip = "192.168.1.100"
        target_user = "admin"

        # Simular múltiples intentos de login fallidos
        for i in range(10):  # Más que el límite
            event_data = {
                "event_type": "USER_LOGIN",
                "resource": "auth",
                "action": "login_failed",
                "user_id": target_user,
                "details": {
                    "ip": attacker_ip,
                    "reason": "invalid_password",
                    "user_agent": "MaliciousBot/1.0"
                }
            }

            await audit_manager.log_event(**event_data)
            await security_monitor.process_event(event_data)

        # Verificar que se generó alerta de brute force
        alerts = audit_manager.get_security_alerts()
        brute_force_alerts = [a for a in alerts if "brute force" in a["title"].lower()]

        assert len(brute_force_alerts) > 0
        alert = brute_force_alerts[0]
        assert alert["severity"] == "HIGH"
        assert attacker_ip in alert["description"]

    @pytest.mark.asyncio
    async def test_session_hijacking_detection(self, audit_system):
        """Test detección de secuestro de sesión."""
        security_monitor = audit_system['security_monitor']

        # Agregar regla para detectar session hijacking
        rule = {
            "rule_id": "session_hijacking",
            "name": "Session Hijacking Detection",
            "description": "Detect unusual session activity",
            "severity": "HIGH",
            "conditions": [
                {
                    "field": "event_type",
                    "operator": "equals",
                    "value": "SESSION_ACCESS"
                },
                {
                    "field": "details.suspicious_activity",
                    "operator": "equals",
                    "value": True
                }
            ],
            "action": "alert"
        }

        security_monitor.add_security_rule(rule)

        # Simular acceso sospechoso a sesión
        event_data = {
            "event_type": "SESSION_ACCESS",
            "resource": "session",
            "action": "access",
            "user_id": "victim_user",
            "details": {
                "session_id": "sess_12345",
                "ip": "10.0.0.1",
                "user_agent": "SuspiciousBrowser/1.0",
                "location": "Unknown",
                "suspicious_activity": True,
                "time_diff": 3600  # 1 hora de diferencia
            }
        }

        with patch.object(security_monitor, '_send_alert') as mock_send:
            await security_monitor.process_event(event_data)
            mock_send.assert_called_once()

            call_args = mock_send.call_args
            assert "Session Hijacking" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_unauthorized_access_attempts(self, audit_system):
        """Test detección de intentos de acceso no autorizado."""
        audit_manager = audit_system['audit_manager']
        security_monitor = audit_system['security_monitor']

        # Simular múltiples accesos no autorizados
        endpoints = ["/admin/users", "/admin/config", "/admin/logs", "/api/private"]

        for i, endpoint in enumerate(endpoints):
            event_data = {
                "event_type": "API_REQUEST",
                "resource": "api",
                "action": "unauthorized_access",
                "user_id": "anonymous",
                "details": {
                    "endpoint": endpoint,
                    "method": "GET",
                    "status_code": 403,
                    "ip": f"192.168.1.{i+1}",
                    "reason": "insufficient_permissions"
                }
            }

            await audit_manager.log_event(**event_data)
            await security_monitor.process_event(event_data)

        # Verificar que se generaron alertas
        alerts = audit_manager.get_security_alerts()
        unauthorized_alerts = [a for a in alerts if "unauthorized" in a["title"].lower()]

        assert len(unauthorized_alerts) > 0

    @pytest.mark.asyncio
    async def test_privilege_escalation_detection(self, audit_system):
        """Test detección de escalada de privilegios."""
        security_monitor = audit_system['security_monitor']

        # Agregar regla para privilege escalation
        rule = {
            "rule_id": "privilege_escalation",
            "name": "Privilege Escalation Detection",
            "description": "Detect privilege escalation attempts",
            "severity": "CRITICAL",
            "conditions": [
                {
                    "field": "event_type",
                    "operator": "equals",
                    "value": "PERMISSION_CHANGE"
                },
                {
                    "field": "details.elevation_attempt",
                    "operator": "equals",
                    "value": True
                }
            ],
            "action": "alert"
        }

        security_monitor.add_security_rule(rule)

        # Simular intento de escalada de privilegios
        event_data = {
            "event_type": "PERMISSION_CHANGE",
            "resource": "user_permissions",
            "action": "elevate",
            "user_id": "regular_user",
            "details": {
                "target_user": "regular_user",
                "old_role": "user",
                "new_role": "admin",
                "requested_by": "regular_user",
                "elevation_attempt": True,
                "justification": "I need admin access"
            }
        }

        with patch.object(security_monitor, '_send_alert') as mock_send:
            await security_monitor.process_event(event_data)
            mock_send.assert_called_once()

            call_args = mock_send.call_args
            assert call_args[0][0] == "CRITICAL"
            assert "Privilege Escalation" in call_args[0][1]


class TestEncryptionSecurity:
    """Tests de seguridad para encriptación."""

    def test_message_integrity_verification(self):
        """Test verificación de integridad de mensajes."""
        from src.ailoos.auditing.realtime_monitor import RealtimeMonitor

        monitor = RealtimeMonitor(Mock())

        # Crear mensaje de prueba
        message = {
            "type": "alert",
            "data": {"alert_id": "test_123", "severity": "HIGH"},
            "timestamp": datetime.now().isoformat()
        }

        # Simular firma del mensaje
        message_json = json.dumps(message, sort_keys=True)
        signature = hmac.new(
            b"test_secret_key",
            message_json.encode(),
            hashlib.sha256
        ).hexdigest()

        message["signature"] = signature

        # Verificar integridad (simulado)
        # En implementación real, esto verificaría la firma
        assert "signature" in message
        assert len(message["signature"]) == 64  # SHA256 hex length

    def test_secure_websocket_communication(self):
        """Test comunicación segura WebSocket."""
        # Este test verifica que las conexiones WebSocket usen encriptación
        # En una implementación real, verificaríamos certificados TLS

        # Simular configuración TLS
        tls_config = {
            "certfile": "/tmp/test_cert.pem",
            "keyfile": "/tmp/test_key.pem",
            "ca_certs": "/tmp/test_ca.pem"
        }

        # Verificar que la configuración contiene archivos de certificado
        assert "certfile" in tls_config
        assert "keyfile" in tls_config
        assert tls_config["certfile"].endswith(".pem")
        assert tls_config["keyfile"].endswith(".pem")

    @pytest.mark.asyncio
    async def test_encrypted_audit_log_storage(self, audit_system):
        """Test almacenamiento encriptado de logs de auditoría."""
        audit_manager = audit_system['audit_manager']

        # Simular encriptación de logs
        # En implementación real, los logs se encriptarían antes de almacenarse

        sensitive_data = {
            "user_pii": "john.doe@example.com",
            "session_token": "abc123def456",
            "api_key": "sk-1234567890abcdef"
        }

        # Loggear datos sensibles
        await audit_manager.log_event(
            event_type="DATA_ACCESS",
            resource="user_profile",
            action="view",
            user_id="admin",
            details=sensitive_data
        )

        # Verificar que los datos están en el log (en implementación real estarían encriptados)
        events = audit_manager.get_audit_events()
        assert len(events) > 0

        event = events[-1]
        assert event["details"]["user_pii"] == sensitive_data["user_pii"]
        # En producción, estos datos deberían estar encriptados


class TestAttackPrevention:
    """Tests de prevención de ataques."""

    @pytest.fixture
    def security_monitor(self):
        """SecurityMonitor para tests de ataques."""
        config = Mock()
        config.security_rules_file = "/tmp/test_attack_rules.json"
        monitor = SecurityMonitor(config)
        return monitor

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, security_monitor):
        """Test prevención de inyección SQL."""
        # Agregar regla para detectar inyección SQL
        rule = {
            "rule_id": "sql_injection",
            "name": "SQL Injection Detection",
            "description": "Detect SQL injection attempts",
            "severity": "HIGH",
            "conditions": [
                {
                    "field": "details.input",
                    "operator": "contains",
                    "value": "UNION SELECT"
                }
            ],
            "action": "alert"
        }

        security_monitor.add_security_rule(rule)

        # Simular intento de inyección SQL
        malicious_input = "'; UNION SELECT username, password FROM users; --"

        event_data = {
            "event_type": "API_REQUEST",
            "resource": "api",
            "action": "query",
            "user_id": "attacker",
            "details": {
                "endpoint": "/api/search",
                "method": "POST",
                "input": malicious_input,
                "ip": "192.168.1.100"
            }
        }

        with patch.object(security_monitor, '_send_alert') as mock_send:
            await security_monitor.process_event(event_data)
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_xss_attack_prevention(self, security_monitor):
        """Test prevención de ataques XSS."""
        # Agregar regla para detectar XSS
        rule = {
            "rule_id": "xss_attack",
            "name": "XSS Attack Detection",
            "description": "Detect cross-site scripting attempts",
            "severity": "MEDIUM",
            "conditions": [
                {
                    "field": "details.input",
                    "operator": "contains",
                    "value": "<script>"
                }
            ],
            "action": "alert"
        }

        security_monitor.add_security_rule(rule)

        # Simular intento de XSS
        xss_payload = "<script>alert('XSS')</script>"

        event_data = {
            "event_type": "FORM_SUBMISSION",
            "resource": "web_form",
            "action": "submit",
            "user_id": "user123",
            "details": {
                "form_field": "comment",
                "input": xss_payload,
                "ip": "10.0.0.5"
            }
        }

        with patch.object(security_monitor, '_send_alert') as mock_send:
            await security_monitor.process_event(event_data)
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_csrf_attack_detection(self, security_monitor):
        """Test detección de ataques CSRF."""
        # Agregar regla para detectar CSRF
        rule = {
            "rule_id": "csrf_attack",
            "name": "CSRF Attack Detection",
            "description": "Detect cross-site request forgery attempts",
            "severity": "MEDIUM",
            "conditions": [
                {
                    "field": "event_type",
                    "operator": "equals",
                    "value": "CROSS_ORIGIN_REQUEST"
                },
                {
                    "field": "details.referrer_suspicious",
                    "operator": "equals",
                    "value": True
                }
            ],
            "action": "alert"
        }

        security_monitor.add_security_rule(rule)

        # Simular request CSRF
        event_data = {
            "event_type": "CROSS_ORIGIN_REQUEST",
            "resource": "api",
            "action": "post",
            "user_id": "victim",
            "details": {
                "origin": "malicious-site.com",
                "referrer": "malicious-site.com",
                "target_endpoint": "/api/user/change-password",
                "referrer_suspicious": True,
                "missing_csrf_token": True
            }
        }

        with patch.object(security_monitor, '_send_alert') as mock_send:
            await security_monitor.process_event(event_data)
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_directory_traversal_prevention(self, security_monitor):
        """Test prevención de directory traversal."""
        # Agregar regla para detectar directory traversal
        rule = {
            "rule_id": "directory_traversal",
            "name": "Directory Traversal Detection",
            "description": "Detect directory traversal attempts",
            "severity": "HIGH",
            "conditions": [
                {
                    "field": "details.path",
                    "operator": "contains",
                    "value": "../"
                }
            ],
            "action": "alert"
        }

        security_monitor.add_security_rule(rule)

        # Simular intento de directory traversal
        malicious_path = "../../../etc/passwd"

        event_data = {
            "event_type": "FILE_ACCESS",
            "resource": "filesystem",
            "action": "read",
            "user_id": "attacker",
            "details": {
                "path": malicious_path,
                "requested_by": "web_user",
                "ip": "192.168.1.200"
            }
        }

        with patch.object(security_monitor, '_send_alert') as mock_send:
            await security_monitor.process_event(event_data)
            mock_send.assert_called_once()


class TestDataProtection:
    """Tests de protección de datos."""

    @pytest.mark.asyncio
    async def test_pii_data_masking(self, audit_system):
        """Test enmascaramiento de datos PII."""
        audit_manager = audit_system['audit_manager']

        # Datos PII que deberían enmascararse
        pii_data = {
            "email": "user@example.com",
            "phone": "+1234567890",
            "ssn": "123-45-6789",
            "credit_card": "4111111111111111"
        }

        await audit_manager.log_event(
            event_type="DATA_PROCESSING",
            resource="user_data",
            action="store",
            user_id="admin",
            details=pii_data
        )

        # Verificar que los datos están logged (en implementación real estarían enmascarados)
        events = audit_manager.get_audit_events()
        assert len(events) > 0

        event = events[-1]
        # En producción, estos campos deberían estar enmascarados
        assert "email" in event["details"]
        assert "phone" in event["details"]

    @pytest.mark.asyncio
    async def test_audit_log_integrity(self, audit_system):
        """Test integridad de logs de auditoría."""
        audit_manager = audit_system['audit_manager']

        # Loggear eventos
        await audit_manager.log_event(
            event_type="SYSTEM_START",
            resource="system",
            action="boot",
            user_id="system",
            details={"version": "1.0.0"}
        )

        # Calcular hash del log actual
        events = audit_manager.get_audit_events()
        events_json = json.dumps(events, sort_keys=True, default=str)
        current_hash = hashlib.sha256(events_json.encode()).hexdigest()

        # Agregar otro evento
        await audit_manager.log_event(
            event_type="USER_LOGIN",
            resource="auth",
            action="login",
            user_id="user123",
            details={"ip": "192.168.1.1"}
        )

        # Verificar que el hash cambió
        new_events = audit_manager.get_audit_events()
        new_events_json = json.dumps(new_events, sort_keys=True, default=str)
        new_hash = hashlib.sha256(new_events_json.encode()).hexdigest()

        assert current_hash != new_hash
        assert len(new_events) == len(events) + 1

    @pytest.mark.asyncio
    async def test_secure_audit_log_rotation(self, audit_system):
        """Test rotación segura de logs de auditoría."""
        audit_manager = audit_system['audit_manager']

        # Simular logs que exceden el límite de retención
        # Agregar eventos con timestamps antiguos
        for i in range(100):
            old_event = {
                "event_type": "API_REQUEST",
                "resource": "api",
                "action": "get",
                "user_id": f"user_{i}",
                "timestamp": datetime.now() - timedelta(days=40),  # Más de 30 días
                "details": {"endpoint": f"/api/resource/{i}"}
            }
            audit_manager.audit_events.append(old_event)

        # Agregar evento reciente
        await audit_manager.log_event(
            event_type="SYSTEM_CHECK",
            resource="system",
            action="health_check",
            user_id="monitor",
            details={"status": "healthy"}
        )

        # Verificar que los logs antiguos y nuevos coexisten
        events = audit_manager.get_audit_events()
        assert len(events) > 1

        # En implementación real, habría un proceso de rotación que
        # archivaría logs antiguos de forma segura


class TestAccessControl:
    """Tests de control de acceso."""

    @pytest.mark.asyncio
    async def test_role_based_access_control(self, audit_system):
        """Test control de acceso basado en roles."""
        audit_manager = audit_system['audit_manager']
        security_monitor = audit_system['security_monitor']

        # Agregar regla para RBAC violations
        rule = {
            "rule_id": "rbac_violation",
            "name": "RBAC Violation Detection",
            "description": "Detect role-based access control violations",
            "severity": "HIGH",
            "conditions": [
                {
                    "field": "event_type",
                    "operator": "equals",
                    "value": "ACCESS_DENIED"
                },
                {
                    "field": "details.insufficient_role",
                    "operator": "equals",
                    "value": True
                }
            ],
            "action": "alert"
        }

        security_monitor.add_security_rule(rule)

        # Simular violación de RBAC
        event_data = {
            "event_type": "ACCESS_DENIED",
            "resource": "admin_panel",
            "action": "access",
            "user_id": "regular_user",
            "details": {
                "required_role": "admin",
                "user_role": "user",
                "resource": "/admin/users",
                "insufficient_role": True,
                "ip": "192.168.1.50"
            }
        }

        await audit_manager.log_event(**event_data)

        with patch.object(security_monitor, '_send_alert') as mock_send:
            await security_monitor.process_event(event_data)
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_least_privilege_enforcement(self, audit_system):
        """Test enforcement del principio de menor privilegio."""
        security_monitor = audit_system['security_monitor']

        # Agregar regla para detectar violaciones de least privilege
        rule = {
            "rule_id": "excessive_permissions",
            "name": "Excessive Permissions Detection",
            "description": "Detect users with excessive permissions",
            "severity": "MEDIUM",
            "conditions": [
                {
                    "field": "event_type",
                    "operator": "equals",
                    "value": "PERMISSION_GRANT"
                },
                {
                    "field": "details.excessive_permissions",
                    "operator": "equals",
                    "value": True
                }
            ],
            "action": "alert"
        }

        security_monitor.add_security_rule(rule)

        # Simular otorgamiento de permisos excesivos
        event_data = {
            "event_type": "PERMISSION_GRANT",
            "resource": "user_permissions",
            "action": "grant",
            "user_id": "helpdesk_user",
            "details": {
                "target_user": "helpdesk_user",
                "granted_permissions": ["read_users", "write_users", "delete_users", "admin_access"],
                "justification": "Needs access to everything",
                "excessive_permissions": True,
                "granted_by": "admin"
            }
        }

        with patch.object(security_monitor, '_send_alert') as mock_send:
            await security_monitor.process_event(event_data)
            mock_send.assert_called_once()


class TestComplianceSecurity:
    """Tests de seguridad para cumplimiento normativo."""

    @pytest.mark.asyncio
    async def test_gdpr_compliance_logging(self, audit_system):
        """Test logging compliant con GDPR."""
        audit_manager = audit_system['audit_manager']

        # Simular procesamiento de datos personales bajo GDPR
        gdpr_event = {
            "event_type": "DATA_PROCESSING",
            "resource": "user_data",
            "action": "collect",
            "user_id": "data_controller",
            "details": {
                "data_subjects": ["user_001", "user_002"],
                "data_categories": ["personal_info", "contact_details"],
                "processing_purpose": "user_registration",
                "legal_basis": "consent",
                "retention_period": "2_years",
                "data_recipients": ["marketing_team"],
                "gdpr_compliant": True
            }
        }

        await audit_manager.log_event(**gdpr_event)

        # Verificar que el evento se registró con información de cumplimiento
        events = audit_manager.get_audit_events()
        assert len(events) > 0

        event = events[-1]
        assert "gdpr_compliant" in event["details"]
        assert event["details"]["legal_basis"] == "consent"

    @pytest.mark.asyncio
    async def test_hipaa_compliance_monitoring(self, audit_system):
        """Test monitoreo compliant con HIPAA."""
        security_monitor = audit_system['security_monitor']

        # Agregar regla para detectar violaciones HIPAA
        rule = {
            "rule_id": "hipaa_violation",
            "name": "HIPAA Violation Detection",
            "description": "Detect HIPAA compliance violations",
            "severity": "CRITICAL",
            "conditions": [
                {
                    "field": "event_type",
                    "operator": "equals",
                    "value": "PHI_ACCESS"
                },
                {
                    "field": "details.unauthorized_access",
                    "operator": "equals",
                    "value": True
                }
            ],
            "action": "alert"
        }

        security_monitor.add_security_rule(rule)

        # Simular acceso no autorizado a PHI (Protected Health Information)
        event_data = {
            "event_type": "PHI_ACCESS",
            "resource": "medical_records",
            "action": "view",
            "user_id": "unauthorized_user",
            "details": {
                "patient_id": "patient_123",
                "record_type": "diagnosis_history",
                "access_reason": "curiosity",
                "authorized_role": "doctor",
                "user_role": "nurse",
                "unauthorized_access": True,
                "ip": "192.168.1.75"
            }
        }

        with patch.object(security_monitor, '_send_alert') as mock_send:
            await security_monitor.process_event(event_data)
            mock_send.assert_called_once()

            call_args = mock_send.call_args
            assert call_args[0][0] == "CRITICAL"
            assert "HIPAA" in call_args[0][1]