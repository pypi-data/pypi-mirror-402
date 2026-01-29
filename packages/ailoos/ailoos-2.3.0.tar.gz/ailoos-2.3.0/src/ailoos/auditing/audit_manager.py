"""
Sistema centralizado de logging y auditoría completa para AILOOS.
Gestiona logging estructurado, auditoría de cambios, alertas de seguridad y métricas.
"""

import asyncio
import json
import threading
import time
from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import psutil
import structlog
from concurrent.futures import ThreadPoolExecutor

from ..core.logging import get_logger, AiloosLogger
from ..core.config import get_config
from .zk_auditor import ZKAuditor
from .privacy_auditor import PrivacyAuditor
from ..validation.config_auditor import get_config_auditor
from ..coordinator.websocket.notification_service import NotificationService

logger = get_logger(__name__)


class AuditEventType(Enum):
    """Tipos de eventos de auditoría."""
    CONFIG_CHANGE = "config_change"
    SECURITY_ALERT = "security_alert"
    USER_ACTION = "user_action"
    SYSTEM_OPERATION = "system_operation"
    DATA_ACCESS = "data_access"
    NETWORK_EVENT = "network_event"
    PERFORMANCE_ISSUE = "performance_issue"
    # Eventos específicos de Knowledge Graph
    KNOWLEDGE_GRAPH_OPERATION = "knowledge_graph_operation"
    KNOWLEDGE_GRAPH_INFERENCE = "knowledge_graph_inference"
    KNOWLEDGE_GRAPH_QUERY = "knowledge_graph_query"


class SecurityAlertLevel(Enum):
    """Niveles de alerta de seguridad."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Evento de auditoría estructurado."""
    event_type: AuditEventType
    event_id: str
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource: str = ""
    action: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    severity: SecurityAlertLevel = SecurityAlertLevel.LOW
    success: bool = True
    processing_time_ms: Optional[float] = None
    checksum: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para serialización."""
        return {
            "event_type": self.event_type.value,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "resource": self.resource,
            "action": self.action,
            "details": self.details,
            "severity": self.severity.value,
            "success": self.success,
            "processing_time_ms": self.processing_time_ms,
            "checksum": self.checksum
        }


@dataclass
class SecurityAlert:
    """Alerta de seguridad."""
    alert_id: str
    level: SecurityAlertLevel
    title: str
    description: str
    triggered_by: AuditEvent
    timestamp: datetime
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    auto_resolved: bool = False
    resolution_details: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "level": self.level.value,
            "title": self.title,
            "description": self.description,
            "triggered_by": self.triggered_by.to_dict(),
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "auto_resolved": self.auto_resolved,
            "resolution_details": self.resolution_details
        }


@dataclass
class SystemMetrics:
    """Métricas del sistema."""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_connections: int
    active_threads: int
    active_sessions: int
    pending_tasks: int
    error_rate: float
    response_time_avg: float
    uptime_seconds: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "disk_usage": self.disk_usage,
            "network_connections": self.network_connections,
            "active_threads": self.active_threads,
            "active_sessions": self.active_sessions,
            "pending_tasks": self.pending_tasks,
            "error_rate": self.error_rate,
            "response_time_avg": self.response_time_avg,
            "uptime_seconds": self.uptime_seconds
        }


class AuditManager:
    """
    Gestor centralizado de auditoría y logging para AILOOS.
    Maneja logging estructurado, auditoría de cambios, alertas de seguridad y métricas.
    """

    def __init__(self):
        self.config = get_config()
        self.logger = get_logger("audit_manager")

        # Componentes de auditoría
        self.zk_auditor = ZKAuditor(self.config)
        self.privacy_auditor = PrivacyAuditor(self.config)
        self.config_auditor = get_config_auditor()

        # Almacenamiento de eventos
        self.audit_events: List[AuditEvent] = []
        self.security_alerts: List[SecurityAlert] = []
        self.system_metrics: List[SystemMetrics] = []

        # Configuración
        self.max_events = getattr(self.config, 'audit_max_events', 100000)
        self.max_alerts = getattr(self.config, 'audit_max_alerts', 10000)
        self.max_metrics = getattr(self.config, 'audit_max_metrics', 10000)
        self.audit_log_file = Path(getattr(self.config, 'audit_log_file', './data/audit.log'))
        self.metrics_interval = getattr(self.config, 'metrics_interval_seconds', 60)

        # Alertas de seguridad
        self.alert_thresholds = {
            'failed_logins_per_hour': 5,
            'config_changes_per_hour': 10,
            'suspicious_ips_per_hour': 3,
            'error_rate_threshold': 0.05  # 5%
        }

        # Callbacks para alertas y eventos
        self.alert_callbacks: List[Callable] = []
        self.event_callbacks: List[Callable] = []

        # Estado del sistema
        self.system_start_time = datetime.now()
        self.active_sessions: Set[str] = set()
        self.error_counts: Dict[str, int] = {}
        self.response_times: List[float] = []

        # Servicios
        self.notification_service: Optional[NotificationService] = None

        # Inicialización
        self._setup_storage()
        # Background tasks started separately after server initialization

    def _setup_storage(self):
        """Configurar almacenamiento persistente."""
        self.audit_log_file.parent.mkdir(parents=True, exist_ok=True)

        # Cargar eventos existentes si existe el archivo
        if self.audit_log_file.exists():
            self._load_audit_log()

    def _load_audit_log(self):
        """Cargar log de auditoría existente."""
        try:
            with open(self.audit_log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            entry = json.loads(line.strip())
                            if 'event_type' in entry:
                                # Es un evento de auditoría
                                event = AuditEvent(
                                    event_type=AuditEventType(entry['event_type']),
                                    event_id=entry['event_id'],
                                    timestamp=datetime.fromisoformat(entry['timestamp']),
                                    user_id=entry.get('user_id'),
                                    session_id=entry.get('session_id'),
                                    ip_address=entry.get('ip_address'),
                                    user_agent=entry.get('user_agent'),
                                    resource=entry.get('resource', ''),
                                    action=entry.get('action', ''),
                                    details=entry.get('details', {}),
                                    severity=SecurityAlertLevel(entry.get('severity', 'low')),
                                    success=entry.get('success', True),
                                    processing_time_ms=entry.get('processing_time_ms'),
                                    checksum=entry.get('checksum')
                                )
                                self.audit_events.append(event)
                        except (json.JSONDecodeError, KeyError, ValueError) as e:
                            self.logger.warning(f"Error parsing audit log entry: {e}")
                            continue

            self.logger.info(f"📋 Loaded {len(self.audit_events)} audit events from log")

        except Exception as e:
            self.logger.error(f"Error loading audit log: {e}")

    def start_background_tasks(self):
        """Iniciar tareas en segundo plano después de la inicialización del servidor."""
        # Recolector de métricas
        asyncio.create_task(self._metrics_collector())

        # Limpiador de logs antiguos
        asyncio.create_task(self._log_cleanup_task())

        # Verificador de alertas
        asyncio.create_task(self._alert_monitor())

        # Iniciar auditorías periódicas
        self.zk_auditor.start_periodic_audits()
        self.privacy_auditor.start_periodic_privacy_audits()
        self.security_monitor.start_monitoring()
        self.metrics_collector.start_collection()

    async def log_event(
        self,
        event_type: AuditEventType,
        resource: str,
        action: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: SecurityAlertLevel = SecurityAlertLevel.LOW,
        success: bool = True,
        processing_time_ms: Optional[float] = None
    ) -> str:
        """
        Registrar un evento de auditoría.

        Returns:
            ID del evento registrado
        """
        import secrets
        import hashlib

        event_id = secrets.token_hex(8)

        event = AuditEvent(
            event_type=event_type,
            event_id=event_id,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource=resource,
            action=action,
            details=details or {},
            severity=severity,
            success=success,
            processing_time_ms=processing_time_ms
        )

        # Generar checksum
        event_data = f"{event.event_type.value}:{event.resource}:{event.action}:{event.timestamp.isoformat()}"
        event.checksum = hashlib.sha256(event_data.encode()).hexdigest()[:16]

        # Agregar a memoria
        self.audit_events.append(event)

        # Limitar tamaño en memoria
        if len(self.audit_events) > self.max_events:
            self.audit_events = self.audit_events[-self.max_events:]

        # Persistir
        await self._persist_event(event)

        # Verificar si genera alerta de seguridad
        await self._check_security_alerts(event)

        # Notificar callbacks de eventos
        for callback in self.event_callbacks:
            try:
                await callback(event)
            except Exception as e:
                self.logger.error(f"Error in event callback: {e}")

        # Logging estructurado
        log_data = {
            "event_id": event_id,
            "event_type": event_type.value,
            "resource": resource,
            "action": action,
            "user_id": user_id,
            "severity": severity.value,
            "success": success
        }

        if processing_time_ms:
            log_data["processing_time_ms"] = processing_time_ms

        self.logger.info(f"Audit event: {event_type.value} {resource}:{action}", **log_data)

        return event_id

    async def _persist_event(self, event: AuditEvent):
        """Persistir evento en archivo."""
        try:
            with open(self.audit_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + '\n')
        except Exception as e:
            self.logger.error(f"Error persisting audit event: {e}")

    async def _check_security_alerts(self, event: AuditEvent):
        """Verificar si un evento debe generar alerta de seguridad."""
        alert_triggered = False
        alert_title = ""
        alert_description = ""

        # Verificar diferentes tipos de alertas
        if event.event_type == AuditEventType.SECURITY_ALERT:
            if event.details.get('alert_type') == 'failed_login':
                # Contar logins fallidos por hora
                recent_failed_logins = self._count_events_last_hour(
                    AuditEventType.SECURITY_ALERT,
                    lambda e: e.details.get('alert_type') == 'failed_login' and e.ip_address == event.ip_address
                )

                if recent_failed_logins >= self.alert_thresholds['failed_logins_per_hour']:
                    alert_triggered = True
                    alert_title = "Múltiples intentos de login fallidos"
                    alert_description = f"Detectados {recent_failed_logins} intentos de login fallidos desde IP {event.ip_address}"

            elif event.details.get('alert_type') == 'suspicious_config_change':
                recent_config_changes = self._count_events_last_hour(
                    AuditEventType.CONFIG_CHANGE,
                    lambda e: e.user_id == event.user_id
                )

                if recent_config_changes >= self.alert_thresholds['config_changes_per_hour']:
                    alert_triggered = True
                    alert_title = "Cambios de configuración sospechosos"
                    alert_description = f"Usuario {event.user_id} realizó {recent_config_changes} cambios de configuración en la última hora"

        elif event.event_type == AuditEventType.CONFIG_CHANGE:
            # Verificar cambios en configuraciones críticas
            if event.resource in ['jwt_secret', 'encryption_key', 'database_url'] and not event.success:
                alert_triggered = True
                alert_title = "Cambio fallido en configuración crítica"
                alert_description = f"Falló el cambio de {event.resource} por usuario {event.user_id}"

        # Verificar alertas específicas de Knowledge Graph
        elif event.event_type == AuditEventType.KNOWLEDGE_GRAPH_OPERATION:
            await self._check_kg_security_alerts(event)

        elif event.event_type == AuditEventType.KNOWLEDGE_GRAPH_INFERENCE:
            # Verificar inferencias sospechosas
            if event.details.get('inference_type') == 'forward_chaining' and event.details.get('triples_inferred', 0) > 1000:
                alert_triggered = True
                alert_title = "Inferencia masiva detectada"
                alert_description = f"Inferencia generó {event.details['triples_inferred']} triples, posible abuso de recursos"

        elif event.event_type == AuditEventType.KNOWLEDGE_GRAPH_QUERY:
            # Verificar consultas complejas o potencialmente peligrosas
            query = event.details.get('query', '').upper()
            if 'DROP' in query or 'DELETE' in query or 'CLEAR' in query:
                if not event.success:
                    alert_triggered = True
                    alert_title = "Operación destructiva fallida en Knowledge Graph"
                    alert_description = f"Operación destructiva '{event.action}' falló, posible intento de manipulación"

        if alert_triggered:
            await self._trigger_security_alert(
                SecurityAlertLevel.HIGH if "crítico" in alert_title.lower() else SecurityAlertLevel.MEDIUM,
                alert_title,
                alert_description,
                event
            )

    async def _check_kg_security_alerts(self, event: AuditEvent):
        """Verificar alertas de seguridad específicas para operaciones de Knowledge Graph."""
        alert_triggered = False
        alert_title = ""
        alert_description = ""
        alert_level = SecurityAlertLevel.MEDIUM

        action = event.action
        details = event.details

        # Verificar operaciones de modificación masiva
        if action in ['add_triple', 'remove_triple']:
            # Contar operaciones similares en la última hora
            recent_ops = self._count_events_last_hour(
                AuditEventType.KNOWLEDGE_GRAPH_OPERATION,
                lambda e: e.action == action and e.user_id == event.user_id
            )

            if recent_ops > 100:  # Umbral configurable
                alert_triggered = True
                alert_title = f"Operaciones masivas de {action} detectadas"
                alert_description = f"Usuario {event.user_id} realizó {recent_ops} operaciones {action} en la última hora"
                alert_level = SecurityAlertLevel.HIGH

        # Verificar consultas complejas o potencialmente peligrosas
        elif action == 'query':
            query_length = len(details.get('query', ''))
            if query_length > 10000:  # Consultas muy largas
                alert_triggered = True
                alert_title = "Consulta extremadamente compleja detectada"
                alert_description = f"Consulta de {query_length} caracteres ejecutada por {event.user_id}"
                alert_level = SecurityAlertLevel.MEDIUM

        # Verificar carga de datos desde formatos externos
        elif action == 'load_from_format':
            format_type = details.get('format')
            total_triples = details.get('total_triples', 0)
            if total_triples > 50000:  # Carga masiva
                alert_triggered = True
                alert_title = "Carga masiva de datos detectada"
                alert_description = f"Carga de {total_triples} triples desde formato {format_type}"
                alert_level = SecurityAlertLevel.MEDIUM

        # Verificar operaciones de limpieza del grafo
        elif action == 'clear':
            alert_triggered = True
            alert_title = "Limpieza completa del Knowledge Graph"
            alert_description = f"Usuario {event.user_id} ejecutó limpieza completa del grafo"
            alert_level = SecurityAlertLevel.HIGH

        if alert_triggered:
            await self._trigger_security_alert(alert_level, alert_title, alert_description, event)

    def _count_events_last_hour(self, event_type: AuditEventType, filter_func: Callable = None) -> int:
        """Contar eventos del último hora."""
        one_hour_ago = datetime.now() - timedelta(hours=1)
        count = 0

        for event in reversed(self.audit_events):
            if event.timestamp < one_hour_ago:
                break
            if event.event_type == event_type and (filter_func is None or filter_func(event)):
                count += 1

        return count

    async def _trigger_security_alert(
        self,
        level: SecurityAlertLevel,
        title: str,
        description: str,
        triggered_by: AuditEvent
    ):
        """Generar alerta de seguridad."""
        import secrets

        alert = SecurityAlert(
            alert_id=secrets.token_hex(8),
            level=level,
            title=title,
            description=description,
            triggered_by=triggered_by,
            timestamp=datetime.now()
        )

        self.security_alerts.append(alert)

        # Limitar tamaño
        if len(self.security_alerts) > self.max_alerts:
            self.security_alerts = self.security_alerts[-self.max_alerts:]

        # Notificar callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {e}")

        # Notificar vía WebSocket si disponible
        if self.notification_service:
            await self.notification_service.send_security_notification(
                node_id="system",
                event_type="security_alert",
                details=f"{title}: {description}"
            )

        # Auto-resolver alertas menores después de un tiempo
        if level in [SecurityAlertLevel.LOW, SecurityAlertLevel.MEDIUM]:
            asyncio.create_task(self._auto_resolve_alert(alert.alert_id, delay_minutes=30))

        self.logger.warning(f"🚨 Security Alert: {title}", alert_id=alert.alert_id, level=level.value)

    async def _auto_resolve_alert(self, alert_id: str, delay_minutes: int):
        """Auto-resolver alerta después de un delay."""
        await asyncio.sleep(delay_minutes * 60)

        for alert in self.security_alerts:
            if alert.alert_id == alert_id and not alert.acknowledged:
                alert.auto_resolved = True
                alert.resolution_details = f"Auto-resuelta después de {delay_minutes} minutos"
                self.logger.info(f"✅ Auto-resolved alert: {alert_id}")
                break

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Marcar alerta como reconocida."""
        for alert in self.security_alerts:
            if alert.alert_id == alert_id and not alert.acknowledged:
                alert.acknowledged = True
                alert.acknowledged_by = acknowledged_by
                alert.acknowledged_at = datetime.now()
                self.logger.info(f"👁️ Alert acknowledged: {alert_id} by {acknowledged_by}")
                return True
        return False

    async def _metrics_collector(self):
        """Recolector de métricas del sistema."""
        while True:
            try:
                # Recopilar métricas del sistema
                cpu_usage = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                network = psutil.net_connections()

                metrics = SystemMetrics(
                    timestamp=datetime.now(),
                    cpu_usage=cpu_usage,
                    memory_usage=memory.percent,
                    disk_usage=disk.percent,
                    network_connections=len(network),
                    active_threads=threading.active_count(),
                    active_sessions=len(self.active_sessions),
                    pending_tasks=len(asyncio.all_tasks()) if hasattr(asyncio, 'all_tasks') else 0,
                    error_rate=self._calculate_error_rate(),
                    response_time_avg=self._calculate_avg_response_time(),
                    uptime_seconds=int((datetime.now() - self.system_start_time).total_seconds())
                )

                self.system_metrics.append(metrics)

                # Limitar tamaño
                if len(self.system_metrics) > self.max_metrics:
                    self.system_metrics = self.system_metrics[-self.max_metrics:]

                # Log métricas cada 5 minutos
                if metrics.uptime_seconds % 300 == 0:
                    self.logger.info("System metrics update",
                                    cpu_usage=cpu_usage,
                                    memory_usage=memory.percent,
                                    active_sessions=len(self.active_sessions))

            except Exception as e:
                self.logger.error(f"Error collecting metrics: {e}")

            await asyncio.sleep(self.metrics_interval)

    def _calculate_error_rate(self) -> float:
        """Calcular tasa de error."""
        if not self.audit_events:
            return 0.0

        recent_events = [e for e in self.audit_events[-1000:] if not e.success]
        return len(recent_events) / max(len(self.audit_events[-1000:]), 1)

    def _calculate_avg_response_time(self) -> float:
        """Calcular tiempo de respuesta promedio."""
        if not self.response_times:
            return 0.0

        # Mantener solo las últimas 1000 mediciones
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]

        return sum(self.response_times) / len(self.response_times)

    async def _log_cleanup_task(self):
        """Limpiar logs antiguos periódicamente."""
        while True:
            try:
                await asyncio.sleep(3600)  # Cada hora

                cutoff_date = datetime.now() - timedelta(days=getattr(self.config, 'audit_retention_days', 90))

                # Limpiar eventos antiguos
                original_count = len(self.audit_events)
                self.audit_events = [e for e in self.audit_events if e.timestamp > cutoff_date]

                # Limpiar métricas antiguas (mantener solo últimos 7 días)
                metrics_cutoff = datetime.now() - timedelta(days=7)
                self.system_metrics = [m for m in self.system_metrics if m.timestamp > metrics_cutoff]

                if len(self.audit_events) < original_count:
                    self.logger.info(f"🧹 Cleaned up {original_count - len(self.audit_events)} old audit events")

            except Exception as e:
                self.logger.error(f"Error in log cleanup: {e}")

    async def _alert_monitor(self):
        """Monitorear y gestionar alertas."""
        while True:
            try:
                await asyncio.sleep(300)  # Cada 5 minutos

                # Verificar alertas críticas sin reconocer
                critical_alerts = [a for a in self.security_alerts
                                 if a.level == SecurityAlertLevel.CRITICAL and not a.acknowledged]

                if critical_alerts:
                    self.logger.warning(f"⚠️ {len(critical_alerts)} critical alerts unacknowledged")

                # Auto-resolver alertas antiguas
                old_alerts = [a for a in self.security_alerts
                            if (datetime.now() - a.timestamp).days > 7 and not a.acknowledged]

                for alert in old_alerts:
                    alert.auto_resolved = True
                    alert.resolution_details = "Auto-resuelta por antigüedad"

            except Exception as e:
                self.logger.error(f"Error in alert monitor: {e}")

    def add_alert_callback(self, callback: Callable):
        """Agregar callback para alertas."""
        self.alert_callbacks.append(callback)

    def add_event_callback(self, callback: Callable):
        """Agregar callback para eventos de auditoría."""
        self.event_callbacks.append(callback)

    def set_notification_service(self, service: NotificationService):
        """Configurar servicio de notificaciones."""
        self.notification_service = service

    def track_response_time(self, response_time_ms: float):
        """Registrar tiempo de respuesta."""
        self.response_times.append(response_time_ms)

    def track_session_start(self, session_id: str):
        """Registrar inicio de sesión."""
        self.active_sessions.add(session_id)

    def track_session_end(self, session_id: str):
        """Registrar fin de sesión."""
        self.active_sessions.discard(session_id)

    def track_error(self, error_type: str):
        """Registrar error."""
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

    # Métodos de consulta
    def get_audit_events(
        self,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Obtener eventos de auditoría filtrados."""
        filtered_events = self.audit_events

        if event_type:
            filtered_events = [e for e in filtered_events if e.event_type == event_type]
        if user_id:
            filtered_events = [e for e in filtered_events if e.user_id == user_id]
        if resource:
            filtered_events = [e for e in filtered_events if e.resource == resource]
        if start_date:
            filtered_events = [e for e in filtered_events if e.timestamp >= start_date]
        if end_date:
            filtered_events = [e for e in filtered_events if e.timestamp <= end_date]

        return sorted(filtered_events[-limit:], key=lambda e: e.timestamp, reverse=True)

    def get_security_alerts(
        self,
        level: Optional[SecurityAlertLevel] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 50
    ) -> List[SecurityAlert]:
        """Obtener alertas de seguridad filtradas."""
        filtered_alerts = self.security_alerts

        if level:
            filtered_alerts = [a for a in filtered_alerts if a.level == level]
        if acknowledged is not None:
            filtered_alerts = [a for a in filtered_alerts if a.acknowledged == acknowledged]

        return sorted(filtered_alerts[-limit:], key=lambda a: a.timestamp, reverse=True)

    def get_system_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[SystemMetrics]:
        """Obtener métricas del sistema."""
        filtered_metrics = self.system_metrics

        if start_date:
            filtered_metrics = [m for m in filtered_metrics if m.timestamp >= start_date]
        if end_date:
            filtered_metrics = [m for m in filtered_metrics if m.timestamp <= end_date]

        return filtered_metrics[-limit:]

    def get_audit_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas de auditoría."""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)

        events_24h = [e for e in self.audit_events if e.timestamp > last_24h]
        events_7d = [e for e in self.audit_events if e.timestamp > last_7d]

        return {
            "total_events": len(self.audit_events),
            "events_last_24h": len(events_24h),
            "events_last_7d": len(events_7d),
            "total_alerts": len(self.security_alerts),
            "unacknowledged_alerts": len([a for a in self.security_alerts if not a.acknowledged]),
            "critical_alerts": len([a for a in self.security_alerts if a.level == SecurityAlertLevel.CRITICAL]),
            "events_by_type": self._count_by_field(self.audit_events, lambda e: e.event_type.value),
            "events_by_user": self._count_by_field(events_24h, lambda e: e.user_id),
            "alerts_by_level": self._count_by_field(self.security_alerts, lambda a: a.level.value),
            "error_rate": self._calculate_error_rate(),
            "avg_response_time": self._calculate_avg_response_time()
        }

    def _count_by_field(self, items: List, field_func: Callable) -> Dict[str, int]:
        """Contar elementos por campo."""
        counts = {}
        for item in items:
            field_value = field_func(item)
            if field_value:
                counts[field_value] = counts.get(field_value, 0) + 1
        return counts

    async def generate_audit_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_metrics: bool = True,
        include_zk_audit: bool = True
    ) -> Dict[str, Any]:
        """Generar reporte completo de auditoría."""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        # Recopilar datos
        events = self.get_audit_events(start_date=start_date, end_date=end_date, limit=10000)
        alerts = self.get_security_alerts(limit=1000)
        metrics = self.get_system_metrics(start_date=start_date, end_date=end_date, limit=1000) if include_metrics else []

        report = {
            "report_id": f"audit_report_{int(time.time())}",
            "generated_at": datetime.now().isoformat(),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "statistics": self.get_audit_statistics(),
            "events_summary": {
                "total": len(events),
                "by_type": self._count_by_field(events, lambda e: e.event_type.value),
                "by_severity": self._count_by_field(events, lambda e: e.severity.value),
                "success_rate": len([e for e in events if e.success]) / max(len(events), 1)
            },
            "alerts_summary": {
                "total": len(alerts),
                "by_level": self._count_by_field(alerts, lambda a: a.level.value),
                "unacknowledged": len([a for a in alerts if not a.acknowledged])
            },
            "events": [e.to_dict() for e in events[:100]],  # Solo los más recientes
            "alerts": [a.to_dict() for a in alerts[:50]],
            "metrics": [m.to_dict() for m in metrics] if include_metrics else []
        }

        # Incluir auditoría ZK si se solicita
        if include_zk_audit:
            try:
                zk_report = await self.zk_auditor.generate_comprehensive_audit_report(
                    audit_period_days=(end_date - start_date).days
                )
                report["zk_audit"] = {
                    "audit_id": zk_report.audit_id,
                    "total_transactions": zk_report.total_transactions,
                    "total_amount": zk_report.total_amount,
                    "anomalies_detected": zk_report.anomalies_detected,
                    "compliance_score": zk_report.compliance_score,
                    "recommendations": zk_report.recommendations
                }
            except Exception as e:
                self.logger.error(f"Error generating ZK audit report: {e}")

        return report


# Instancia global
audit_manager = AuditManager()


def get_audit_manager() -> AuditManager:
    """Obtener instancia global del gestor de auditoría."""
    return audit_manager