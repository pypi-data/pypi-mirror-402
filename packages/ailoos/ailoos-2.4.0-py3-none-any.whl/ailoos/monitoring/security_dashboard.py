"""
Security Dashboard for AILOOS - Threats, Compliance and Audit Monitoring
Provides comprehensive security monitoring, compliance tracking, and audit capabilities.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import jwt

from ..core.logging import get_logger
from ..core.config import get_config
from ..core.state_manager import get_state_manager
from ..coordinator.auth.dependencies import get_current_user, require_admin
from ..notifications.service import NotificationService
from ..validation.security_validator import SecurityValidator

logger = get_logger(__name__)


class ThreatLevel(Enum):
    """Niveles de amenaza."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceStandard(Enum):
    """Estándares de cumplimiento."""
    GDPR = "gdpr"
    SOX = "sox"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    ISO_27001 = "iso_27001"


@dataclass
class SecurityThreat:
    """Amenaza de seguridad detectada."""
    threat_id: str
    threat_type: str
    severity: ThreatLevel
    source: str
    description: str
    affected_components: List[str]
    detection_time: float
    status: str = "active"  # active, investigating, mitigated, resolved
    mitigation_actions: List[str] = field(default_factory=list)
    assigned_to: Optional[str] = None
    resolved_at: Optional[float] = None
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplianceStatus:
    """Estado de cumplimiento."""
    standard: ComplianceStandard
    compliance_percentage: float
    last_audit_date: Optional[float]
    next_audit_date: Optional[float]
    violations_count: int
    critical_violations: int
    remediation_status: str
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditEvent:
    """Evento de auditoría."""
    event_id: str
    event_type: str
    user_id: str
    resource: str
    action: str
    timestamp: float
    ip_address: str
    user_agent: str
    success: bool
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityMetrics:
    """Métricas de seguridad."""
    active_threats: int = 0
    threats_mitigated_today: int = 0
    threats_mitigated_week: int = 0
    failed_login_attempts: int = 0
    suspicious_activities: int = 0
    blocked_ips: int = 0
    encryption_status: str = "healthy"
    zk_proofs_validated: int = 0
    audit_logs_generated: int = 0
    compliance_score: float = 0.0
    security_incidents: int = 0
    data_breaches_prevented: int = 0


class SecurityDashboard:
    """
    Dashboard de seguridad completo para monitoreo de amenazas, cumplimiento y auditoría.
    Proporciona monitoreo en tiempo real de la postura de seguridad.
    """

    def __init__(self,
                 security_validator: Optional[SecurityValidator] = None,
                 notification_service: Optional[NotificationService] = None,
                 jwt_secret: str = "security-dashboard-secret",
                 update_interval: float = 30.0):  # Actualización cada 30 segundos para seguridad

        self.config = get_config()
        self.state_manager = get_state_manager()
        self.security_validator = security_validator
        self.notification_service = notification_service

        # Configuración de seguridad
        self.jwt_secret = jwt_secret
        self.update_interval = update_interval

        # Estado del dashboard
        self.is_running = False
        self.last_update = 0.0

        # Datos de seguridad
        self.security_metrics = SecurityMetrics()
        self.active_threats: List[SecurityThreat] = []
        self.compliance_status: Dict[str, ComplianceStatus] = {}
        self.audit_events: List[AuditEvent] = []

        # Callbacks
        self.update_callbacks: List[Callable] = []
        self.threat_callbacks: List[Callable] = []

        # WebSocket connections
        self.websocket_connections: Dict[str, WebSocket] = {}

        # Historial de métricas
        self.metrics_history: Dict[str, List] = {
            'security_metrics': [],
            'threats': [],
            'compliance': [],
            'audit_events': []
        }

        # FastAPI application
        self.app = FastAPI(
            title="AILOOS Security Dashboard API",
            description="Comprehensive security monitoring, compliance tracking, and audit dashboard",
            version="1.0.0"
        )

        # Configurar middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Configurar rutas
        self._setup_routes()

        # Inicializar estados de cumplimiento
        self._initialize_compliance_status()

        logger.info("🛡️ SecurityDashboard initialized")

    def _initialize_compliance_status(self):
        """Inicializar estados de cumplimiento."""
        current_time = asyncio.get_event_loop().time()

        for standard in ComplianceStandard:
            self.compliance_status[standard.value] = ComplianceStatus(
                standard=standard,
                compliance_percentage=95.0 + (hash(standard.value) % 5),  # 95-99%
                last_audit_date=current_time - (7 * 24 * 3600),  # Hace 1 semana
                next_audit_date=current_time + (30 * 24 * 3600),  # En 30 días
                violations_count=0,
                critical_violations=0,
                remediation_status="compliant"
            )

    def _setup_routes(self):
        """Configurar rutas del dashboard de seguridad."""

        @self.app.get("/")
        async def get_security_dashboard():
            """Obtener dashboard de seguridad completo."""
            return self.get_security_dashboard_data()

        @self.app.get("/api/security/threats")
        async def get_security_threats(user: dict = Depends(get_current_user)):
            """Obtener amenazas de seguridad."""
            if not self._has_security_access(user):
                raise HTTPException(status_code=403, detail="Acceso de seguridad requerido")

            return {
                "threats": [self._threat_to_dict(threat) for threat in self.active_threats[-20:]],
                "active_count": len(self.active_threats),
                "timestamp": datetime.now().isoformat()
            }

        @self.app.get("/api/security/compliance")
        async def get_compliance_status(user: dict = Depends(get_current_user)):
            """Obtener estado de cumplimiento."""
            if not self._has_security_access(user):
                raise HTTPException(status_code=403, detail="Acceso de seguridad requerido")

            return {
                "compliance": {k: self._compliance_to_dict(v) for k, v in self.compliance_status.items()},
                "overall_score": self.security_metrics.compliance_score,
                "timestamp": datetime.now().isoformat()
            }

        @self.app.get("/api/security/audit")
        async def get_audit_events(user: dict = Depends(get_current_user), limit: int = 50):
            """Obtener eventos de auditoría."""
            if not self._has_security_access(user):
                raise HTTPException(status_code=403, detail="Acceso de seguridad requerido")

            return {
                "audit_events": [self._audit_event_to_dict(event) for event in self.audit_events[-limit:]],
                "total_count": len(self.audit_events),
                "timestamp": datetime.now().isoformat()
            }

        @self.app.get("/api/security/metrics")
        async def get_security_metrics(user: dict = Depends(get_current_user)):
            """Obtener métricas de seguridad."""
            if not self._has_security_access(user):
                raise HTTPException(status_code=403, detail="Acceso de seguridad requerido")

            return {
                "security_metrics": self._security_metrics_to_dict(),
                "timestamp": datetime.now().isoformat()
            }

        @self.app.post("/api/security/threats/{threat_id}/mitigate")
        async def mitigate_threat(threat_id: str, mitigation_data: Dict[str, Any], user: dict = Depends(get_current_user)):
            """Mitigar amenaza de seguridad."""
            if not self._has_security_access(user):
                raise HTTPException(status_code=403, detail="Acceso de seguridad requerido")

            if self._mitigate_threat(threat_id, mitigation_data, user.get("username")):
                return {"message": f"Amenaza {threat_id} mitigada"}
            else:
                raise HTTPException(status_code=404, detail="Amenaza no encontrada")

        @self.app.post("/api/security/compliance/{standard}/audit")
        async def trigger_compliance_audit(standard: str, user: dict = Depends(require_admin)):
            """Disparar auditoría de cumplimiento."""
            if standard not in [s.value for s in ComplianceStandard]:
                raise HTTPException(status_code=400, detail="Estándar no válido")

            await self._trigger_compliance_audit(standard)
            return {"message": f"Auditoría de {standard} iniciada"}

        @self.app.get("/api/security/reports/{report_type}")
        async def generate_security_report(report_type: str, user: dict = Depends(get_current_user)):
            """Generar reporte de seguridad."""
            if not self._has_security_access(user):
                raise HTTPException(status_code=403, detail="Acceso de seguridad requerido")

            try:
                return await self.generate_security_report(report_type)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.websocket("/ws/security")
        async def security_websocket(websocket: WebSocket, user: dict = Depends(get_current_user)):
            """WebSocket para actualizaciones de seguridad en tiempo real."""
            if not self._has_security_access(user):
                await websocket.close(code=1008)
                return

            await self.handle_security_websocket(websocket, user.get("username"))

        @self.app.get("/api/security/health")
        async def get_security_health():
            """Obtener estado de salud del dashboard de seguridad."""
            return self.get_health_status()

    def _has_security_access(self, user: dict) -> bool:
        """Verificar si el usuario tiene acceso de seguridad."""
        user_roles = user.get("roles", [])
        security_roles = ["admin", "security", "auditor", "compliance_officer"]

        return any(role in security_roles for role in user_roles)

    async def start_monitoring(self):
        """Iniciar monitoreo de seguridad."""
        if self.is_running:
            return

        self.is_running = True
        logger.info("🛡️ Starting security monitoring")

        # Tarea de monitoreo continuo
        asyncio.create_task(self._security_monitoring_loop())

    async def stop_monitoring(self):
        """Detener monitoreo de seguridad."""
        self.is_running = False
        logger.info("🛑 Security monitoring stopped")

    async def _security_monitoring_loop(self):
        """Loop principal de monitoreo de seguridad."""
        last_broadcast = 0.0

        while self.is_running:
            try:
                await self._update_security_metrics()
                await self._check_security_threats()
                await self._monitor_compliance()
                await self._audit_system_events()
                await self._notify_callbacks()

                self.last_update = asyncio.get_event_loop().time()

                # Broadcast WebSocket updates
                current_time = asyncio.get_event_loop().time()
                if current_time - last_broadcast >= 15.0:  # Broadcast cada 15 segundos para seguridad
                    await self._broadcast_security_updates()
                    last_broadcast = current_time

            except Exception as e:
                logger.error(f"❌ Error in security monitoring loop: {e}")

            await asyncio.sleep(self.update_interval)

    async def _update_security_metrics(self):
        """Actualizar métricas de seguridad."""
        try:
            # Obtener datos del security validator si está disponible
            if self.security_validator:
                security_status = await self.security_validator.get_security_status()
                self.security_metrics.encryption_status = security_status.get("encryption_status", "unknown")
                self.security_metrics.zk_proofs_validated = security_status.get("zk_proofs_validated", 0)
                self.security_metrics.failed_login_attempts = security_status.get("failed_logins", 0)
                self.security_metrics.blocked_ips = security_status.get("blocked_ips", 0)

            # Calcular métricas adicionales
            self.security_metrics.active_threats = len(self.active_threats)
            self.security_metrics.audit_logs_generated = len(self.audit_events)

            # Calcular compliance score promedio
            if self.compliance_status:
                compliance_scores = [status.compliance_percentage for status in self.compliance_status.values()]
                self.security_metrics.compliance_score = sum(compliance_scores) / len(compliance_scores)
            else:
                self.security_metrics.compliance_score = 95.0

            # Métricas simuladas para demo (en producción vendrían de sistemas reales)
            self.security_metrics.threats_mitigated_today = 3
            self.security_metrics.threats_mitigated_week = 12
            self.security_metrics.suspicious_activities = 7
            self.security_metrics.security_incidents = 0
            self.security_metrics.data_breaches_prevented = 2

        except Exception as e:
            logger.error(f"❌ Error updating security metrics: {e}")

    async def _check_security_threats(self):
        """Verificar amenazas de seguridad."""
        try:
            current_time = asyncio.get_event_loop().time()

            # Amenazas simuladas para demo (en producción vendrían de sistemas de detección reales)
            threat_scenarios = [
                {
                    "type": "unauthorized_access_attempt",
                    "description": "Intento de acceso no autorizado detectado",
                    "severity": ThreatLevel.MEDIUM,
                    "source": "authentication_system",
                    "affected_components": ["auth_service"]
                },
                {
                    "type": "suspicious_network_activity",
                    "description": "Actividad de red sospechosa desde IP externa",
                    "severity": ThreatLevel.HIGH,
                    "source": "network_monitor",
                    "affected_components": ["api_gateway", "coordinator"]
                },
                {
                    "type": "data_exfiltration_attempt",
                    "description": "Posible intento de exfiltración de datos",
                    "severity": ThreatLevel.CRITICAL,
                    "source": "data_monitor",
                    "affected_components": ["federated_data", "privacy_system"]
                }
            ]

            # Crear amenazas aleatorias (solo para demo)
            if len(self.active_threats) < 2 and (current_time % 300) < 30:  # Máximo 2 amenazas activas
                threat_data = threat_scenarios[len(self.active_threats) % len(threat_scenarios)]

                threat = SecurityThreat(
                    threat_id=f"threat_{int(current_time)}_{hash(threat_data['type']) % 10000}",
                    threat_type=threat_data["type"],
                    severity=threat_data["severity"],
                    source=threat_data["source"],
                    description=threat_data["description"],
                    affected_components=threat_data["affected_components"],
                    detection_time=current_time
                )

                self.active_threats.append(threat)

                # Notificar
                if self.notification_service:
                    try:
                        await self.notification_service.send_security_alert(threat)
                    except Exception as e:
                        logger.warning(f"Failed to send security alert notification: {e}")

                logger.warning(f"🚨 Security Threat Detected: {threat.threat_type} - {threat.severity.value}")

        except Exception as e:
            logger.error(f"❌ Error checking security threats: {e}")

    async def _monitor_compliance(self):
        """Monitorear cumplimiento."""
        try:
            current_time = asyncio.get_event_loop().time()

            # Simular cambios en cumplimiento (en producción vendría de auditorías reales)
            for standard, status in self.compliance_status.items():
                # Pequeñas variaciones aleatorias
                variation = (hash(f"{standard}_{int(current_time / 3600)}") % 3) - 1  # -1, 0, 1
                status.compliance_percentage = max(85.0, min(100.0, status.compliance_percentage + variation * 0.1))

                # Verificar si necesita re-auditoría
                if current_time > status.next_audit_date:
                    status.violations_count += 1
                    status.remediation_status = "needs_audit"

        except Exception as e:
            logger.error(f"❌ Error monitoring compliance: {e}")

    async def _audit_system_events(self):
        """Auditar eventos del sistema."""
        try:
            current_time = asyncio.get_event_loop().time()

            # Simular eventos de auditoría (en producción vendrían de logs del sistema)
            audit_events = [
                {
                    "event_type": "user_login",
                    "user_id": "user_123",
                    "resource": "dashboard",
                    "action": "login",
                    "success": True,
                    "ip_address": "192.168.1.100",
                    "user_agent": "Mozilla/5.0...",
                    "details": {"method": "jwt"}
                },
                {
                    "event_type": "api_access",
                    "user_id": "service_account",
                    "resource": "federated_api",
                    "action": "read",
                    "success": True,
                    "ip_address": "10.0.0.50",
                    "user_agent": "Python/3.9",
                    "details": {"endpoint": "/api/federated/status"}
                },
                {
                    "event_type": "data_access",
                    "user_id": "researcher_456",
                    "resource": "training_data",
                    "action": "download",
                    "success": False,
                    "ip_address": "203.0.113.1",
                    "user_agent": "curl/7.68.0",
                    "details": {"error": "insufficient_permissions"}
                }
            ]

            # Agregar eventos aleatorios
            if (current_time % 120) < 30:  # Un evento cada ~2 minutos
                event_data = audit_events[int(current_time) % len(audit_events)]

                audit_event = AuditEvent(
                    event_id=f"audit_{int(current_time)}_{hash(event_data['event_type']) % 10000}",
                    event_type=event_data["event_type"],
                    user_id=event_data["user_id"],
                    resource=event_data["resource"],
                    action=event_data["action"],
                    timestamp=current_time,
                    ip_address=event_data["ip_address"],
                    user_agent=event_data["user_agent"],
                    success=event_data["success"],
                    details=event_data["details"]
                )

                self.audit_events.append(audit_event)

                # Mantener solo últimos 1000 eventos
                if len(self.audit_events) > 1000:
                    self.audit_events.pop(0)

        except Exception as e:
            logger.error(f"❌ Error auditing system events: {e}")

    def _mitigate_threat(self, threat_id: str, mitigation_data: Dict[str, Any], mitigated_by: str) -> bool:
        """Mitigar amenaza."""
        for threat in self.active_threats:
            if threat.threat_id == threat_id and threat.status == "active":
                threat.status = "mitigated"
                threat.mitigation_actions = mitigation_data.get("actions", [])
                threat.assigned_to = mitigated_by
                threat.resolved_at = asyncio.get_event_loop().time()

                # Mover a historial
                self.metrics_history['threats'].append(self._threat_to_dict(threat))
                self.active_threats.remove(threat)

                logger.info(f"✅ Security threat {threat_id} mitigated by {mitigated_by}")
                return True
        return False

    async def _trigger_compliance_audit(self, standard: str):
        """Disparar auditoría de cumplimiento."""
        if standard in self.compliance_status:
            status = self.compliance_status[standard]
            current_time = asyncio.get_event_loop().time()

            # Simular auditoría
            status.last_audit_date = current_time
            status.next_audit_date = current_time + (30 * 24 * 3600)  # 30 días

            # Reset violations después de auditoría
            status.violations_count = 0
            status.critical_violations = 0
            status.remediation_status = "compliant"

            logger.info(f"🔍 Compliance audit triggered for {standard}")

    def _store_security_metrics_history(self):
        """Almacenar métricas en historial."""
        timestamp = asyncio.get_event_loop().time()

        self.metrics_history['security_metrics'].append({
            'timestamp': timestamp,
            'active_threats': self.security_metrics.active_threats,
            'compliance_score': self.security_metrics.compliance_score,
            'failed_login_attempts': self.security_metrics.failed_login_attempts,
            'blocked_ips': self.security_metrics.blocked_ips
        })

        # Mantener solo últimas 100 entradas
        for metric_type in self.metrics_history:
            if len(self.metrics_history[metric_type]) > 100:
                self.metrics_history[metric_type].pop(0)

    async def _notify_callbacks(self):
        """Notificar callbacks de actualización."""
        for callback in self.update_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self)
                else:
                    await asyncio.get_event_loop().run_in_executor(None, callback, self)
            except Exception as e:
                logger.error(f"Error in security update callback: {e}")

    async def _broadcast_security_updates(self):
        """Broadcast updates a conexiones WebSocket."""
        try:
            dashboard_data = self.get_security_dashboard_data()

            disconnected_clients = []
            for client_id, websocket in self.websocket_connections.items():
                try:
                    await websocket.send_json({
                        "type": "security_update",
                        "timestamp": asyncio.get_event_loop().time(),
                        "data": dashboard_data
                    })
                except Exception as e:
                    logger.warning(f"Failed to send security update to {client_id}: {e}")
                    disconnected_clients.append(client_id)

            # Limpiar conexiones desconectadas
            for client_id in disconnected_clients:
                del self.websocket_connections[client_id]

        except Exception as e:
            logger.error(f"Error broadcasting security updates: {e}")

    async def handle_security_websocket(self, websocket: WebSocket, client_id: str):
        """Manejar conexión WebSocket para seguridad."""
        await websocket.accept()
        self.websocket_connections[client_id] = websocket

        logger.info(f"🛡️ Security WebSocket connected: {client_id}")

        try:
            # Enviar datos iniciales
            initial_data = self.get_security_dashboard_data()
            await websocket.send_json({
                "type": "initial_data",
                "timestamp": asyncio.get_event_loop().time(),
                "data": initial_data
            })

            # Mantener conexión viva
            while True:
                try:
                    message = await asyncio.wait_for(
                        websocket.receive_json(),
                        timeout=60.0
                    )

                    await self._handle_security_websocket_message(websocket, client_id, message)

                except asyncio.TimeoutError:
                    await websocket.send_json({"type": "ping"})

        except WebSocketDisconnect:
            logger.info(f"🛡️ Security WebSocket disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Security WebSocket error for {client_id}: {e}")
        finally:
            if client_id in self.websocket_connections:
                del self.websocket_connections[client_id]

    async def _handle_security_websocket_message(self, websocket: WebSocket, client_id: str, message: Dict[str, Any]):
        """Manejar mensajes WebSocket de seguridad."""
        try:
            message_type = message.get("type", "unknown")

            if message_type == "mitigate_threat":
                threat_id = message.get("threat_id")
                mitigation_data = message.get("mitigation_data", {})
                if threat_id and self._mitigate_threat(threat_id, mitigation_data, client_id):
                    await websocket.send_json({
                        "type": "threat_mitigated",
                        "threat_id": threat_id
                    })

            elif message_type == "request_audit_trail":
                resource = message.get("resource")
                limit = message.get("limit", 50)

                audit_trail = [self._audit_event_to_dict(event) for event in self.audit_events[-limit:]
                             if event.resource == resource]
                await websocket.send_json({
                    "type": "audit_trail",
                    "resource": resource,
                    "data": audit_trail
                })

        except Exception as e:
            logger.error(f"Error handling security WebSocket message: {e}")
            await websocket.send_json({
                "type": "error",
                "message": f"Error processing message: {e}"
            })

    def get_security_dashboard_data(self) -> Dict[str, Any]:
        """Obtener datos completos del dashboard de seguridad."""
        return {
            "security_metrics": self._security_metrics_to_dict(),
            "active_threats": [self._threat_to_dict(threat) for threat in self.active_threats[-10:]],
            "compliance_status": {k: self._compliance_to_dict(v) for k, v in self.compliance_status.items()},
            "recent_audit_events": [self._audit_event_to_dict(event) for event in self.audit_events[-20:]],
            "last_update": self.last_update,
            "timestamp": asyncio.get_event_loop().time()
        }

    def _security_metrics_to_dict(self) -> Dict[str, Any]:
        """Convertir métricas de seguridad a diccionario."""
        return {
            "active_threats": self.security_metrics.active_threats,
            "threats_mitigated_today": self.security_metrics.threats_mitigated_today,
            "threats_mitigated_week": self.security_metrics.threats_mitigated_week,
            "failed_login_attempts": self.security_metrics.failed_login_attempts,
            "suspicious_activities": self.security_metrics.suspicious_activities,
            "blocked_ips": self.security_metrics.blocked_ips,
            "encryption_status": self.security_metrics.encryption_status,
            "zk_proofs_validated": self.security_metrics.zk_proofs_validated,
            "audit_logs_generated": self.security_metrics.audit_logs_generated,
            "compliance_score": round(self.security_metrics.compliance_score, 2),
            "security_incidents": self.security_metrics.security_incidents,
            "data_breaches_prevented": self.security_metrics.data_breaches_prevented
        }

    def _threat_to_dict(self, threat: SecurityThreat) -> Dict[str, Any]:
        """Convertir amenaza a diccionario."""
        return {
            "threat_id": threat.threat_id,
            "threat_type": threat.threat_type,
            "severity": threat.severity.value,
            "source": threat.source,
            "description": threat.description,
            "affected_components": threat.affected_components,
            "detection_time": threat.detection_time,
            "status": threat.status,
            "mitigation_actions": threat.mitigation_actions,
            "assigned_to": threat.assigned_to,
            "resolved_at": threat.resolved_at,
            "evidence": threat.evidence
        }

    def _compliance_to_dict(self, compliance: ComplianceStatus) -> Dict[str, Any]:
        """Convertir estado de cumplimiento a diccionario."""
        return {
            "standard": compliance.standard.value,
            "compliance_percentage": round(compliance.compliance_percentage, 2),
            "last_audit_date": compliance.last_audit_date,
            "next_audit_date": compliance.next_audit_date,
            "violations_count": compliance.violations_count,
            "critical_violations": compliance.critical_violations,
            "remediation_status": compliance.remediation_status,
            "evidence": compliance.evidence
        }

    def _audit_event_to_dict(self, event: AuditEvent) -> Dict[str, Any]:
        """Convertir evento de auditoría a diccionario."""
        return {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "user_id": event.user_id,
            "resource": event.resource,
            "action": event.action,
            "timestamp": event.timestamp,
            "ip_address": event.ip_address,
            "user_agent": event.user_agent,
            "success": event.success,
            "details": event.details
        }

    def get_metrics_history(self, metric_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtener historial de métricas."""
        if metric_type not in self.metrics_history:
            return []

        return self.metrics_history[metric_type][-limit:]

    def get_health_status(self) -> Dict[str, Any]:
        """Obtener estado de salud del dashboard de seguridad."""
        return {
            "is_running": self.is_running,
            "last_update": self.last_update,
            "active_websocket_connections": len(self.websocket_connections),
            "active_threats": len(self.active_threats),
            "total_audit_events": len(self.audit_events),
            "compliance_standards_monitored": len(self.compliance_status),
            "metrics_history_size": {k: len(v) for k, v in self.metrics_history.items()},
            "timestamp": asyncio.get_event_loop().time()
        }

    async def generate_security_report(self, report_type: str) -> Dict[str, Any]:
        """Generar reporte de seguridad."""
        if report_type == "threat_summary":
            return {
                "report_type": "threat_summary",
                "generated_at": datetime.now().isoformat(),
                "data": {
                    "active_threats": len(self.active_threats),
                    "threats_by_severity": self._get_threats_by_severity(),
                    "recent_threats": [self._threat_to_dict(t) for t in self.active_threats[-5:]]
                },
                "summary": self._generate_threat_summary()
            }
        elif report_type == "compliance_report":
            return {
                "report_type": "compliance_report",
                "generated_at": datetime.now().isoformat(),
                "data": {k: self._compliance_to_dict(v) for k, v in self.compliance_status.items()},
                "summary": self._generate_compliance_summary()
            }
        elif report_type == "audit_report":
            return {
                "report_type": "audit_report",
                "generated_at": datetime.now().isoformat(),
                "data": {
                    "total_events": len(self.audit_events),
                    "failed_events": len([e for e in self.audit_events if not e.success]),
                    "recent_events": [self._audit_event_to_dict(e) for e in self.audit_events[-10:]]
                },
                "summary": self._generate_audit_summary()
            }
        elif report_type == "security_posture":
            return {
                "report_type": "security_posture",
                "generated_at": datetime.now().isoformat(),
                "data": self._security_metrics_to_dict(),
                "summary": self._generate_security_posture_summary()
            }
        else:
            raise ValueError(f"Tipo de reporte desconocido: {report_type}")

    def _get_threats_by_severity(self) -> Dict[str, int]:
        """Obtener amenazas por severidad."""
        severity_count = {}
        for threat in self.active_threats:
            severity = threat.severity.value
            severity_count[severity] = severity_count.get(severity, 0) + 1
        return severity_count

    def _generate_threat_summary(self) -> str:
        """Generar resumen de amenazas."""
        active_count = len(self.active_threats)
        severity_count = self._get_threats_by_severity()

        return f"""
        RESUMEN DE AMENAZAS - AILOOS

        Amenazas Activas: {active_count}
        Amenazas por Severidad:
        • Críticas: {severity_count.get('critical', 0)}
        • Altas: {severity_count.get('high', 0)}
        • Medias: {severity_count.get('medium', 0)}
        • Bajas: {severity_count.get('low', 0)}

        Amenazas Mitigadas (Hoy): {self.security_metrics.threats_mitigated_today}
        Amenazas Mitigadas (Semana): {self.security_metrics.threats_mitigated_week}

        Estado General: {'🔴 CRÍTICO' if severity_count.get('critical', 0) > 0 else '🟡 ATENCIÓN' if severity_count.get('high', 0) > 0 else '🟢 SEGURO'}
        """

    def _generate_compliance_summary(self) -> str:
        """Generar resumen de cumplimiento."""
        standards = list(self.compliance_status.keys())
        avg_compliance = sum(s.compliance_percentage for s in self.compliance_status.values()) / len(self.compliance_status)

        return f"""
        RESUMEN DE CUMPLIMIENTO - AILOOS

        Estándares Monitoreados: {', '.join(standards).upper()}
        Cumplimiento Promedio: {avg_compliance:.1f}%

        Detalle por Estándar:
        {chr(10).join(f"• {k.upper()}: {v.compliance_percentage:.1f}%" for k, v in self.compliance_status.items())}

        Estado General: {'🟢 CUMPLIENTE' if avg_compliance >= 95 else '🟡 REQUIERE ATENCIÓN' if avg_compliance >= 90 else '🔴 NO CUMPLIENTE'}
        """

    def _generate_audit_summary(self) -> str:
        """Generar resumen de auditoría."""
        total_events = len(self.audit_events)
        failed_events = len([e for e in self.audit_events if not e.success])
        success_rate = ((total_events - failed_events) / total_events * 100) if total_events > 0 else 100

        return f"""
        RESUMEN DE AUDITORÍA - AILOOS

        Total Eventos Auditados: {total_events}
        Eventos Fallidos: {failed_events}
        Tasa de Éxito: {success_rate:.1f}%

        Tipos de Eventos Recientes:
        {chr(10).join(f"• {e.event_type}: {e.action} en {e.resource}" for e in self.audit_events[-3:])}

        Estado General: {'🟢 NORMAL' if success_rate >= 99 else '🟡 REQUIERE REVISIÓN' if success_rate >= 95 else '🔴 CRÍTICO'}
        """

    def _generate_security_posture_summary(self) -> str:
        """Generar resumen de postura de seguridad."""
        return f"""
        POSTURA DE SEGURIDAD - AILOOS

        MÉTRICAS PRINCIPALES:
        • Amenazas Activas: {self.security_metrics.active_threats}
        • Intentos de Login Fallidos: {self.security_metrics.failed_login_attempts}
        • IPs Bloqueadas: {self.security_metrics.blocked_ips}
        • Puntuación de Cumplimiento: {self.security_metrics.compliance_score:.1f}%

        SISTEMA DE ENCRIPTACIÓN:
        • Estado: {self.security_metrics.encryption_status.upper()}
        • ZK-Proofs Validados: {self.security_metrics.zk_proofs_validated}

        ACTIVIDADES RECIENTES:
        • Logs de Auditoría Generados: {self.security_metrics.audit_logs_generated}
        • Incidentes de Seguridad: {self.security_metrics.security_incidents}
        • Brechas de Datos Prevendas: {self.security_metrics.data_breaches_prevented}

        EVALUACIÓN GENERAL: {'🟢 EXCELENTE' if self.security_metrics.compliance_score >= 95 and self.security_metrics.active_threats == 0 else '🟡 BUENA' if self.security_metrics.compliance_score >= 90 else '🔴 REQUIERE MEJORA'}
        """

    def register_update_callback(self, callback: Callable):
        """Registrar callback para actualizaciones."""
        self.update_callbacks.append(callback)

    def register_threat_callback(self, callback: Callable):
        """Registrar callback para amenazas."""
        self.threat_callbacks.append(callback)


# Función de conveniencia
def create_security_dashboard(security_validator: Optional[SecurityValidator] = None,
                           notification_service: Optional[NotificationService] = None) -> SecurityDashboard:
    """Crear instancia del dashboard de seguridad."""
    return SecurityDashboard(security_validator=security_validator, notification_service=notification_service)


# Función para iniciar dashboard de seguridad
async def start_security_dashboard(security_validator: Optional[SecurityValidator] = None,
                                 notification_service: Optional[NotificationService] = None):
    """Función de conveniencia para iniciar el dashboard de seguridad."""
    dashboard = create_security_dashboard(security_validator, notification_service)
    await dashboard.start_monitoring()
    return dashboard