#!/usr/bin/env python3
"""
DLAC Alert System - Sistema de alertas y notificaciones para DLAC
"""

import asyncio
import threading
import time
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

from ..utils.logging import get_logger

logger = get_logger(__name__)


class AlertSeverity(Enum):
    """Severidad de las alertas."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """Tipos de alertas DLAC."""
    INTEGRITY_FAILURE = "integrity_failure"
    LOSS_DETECTED = "loss_detected"
    CORRUPTION_DETECTED = "corruption_detected"
    RECOVERY_STARTED = "recovery_started"
    RECOVERY_SUCCESS = "recovery_success"
    RECOVERY_FAILED = "recovery_failed"
    BACKUP_FAILURE = "backup_failure"
    SYSTEM_DEGRADED = "system_degraded"
    CROSS_NODE_INCONSISTENCY = "cross_node_inconsistency"


@dataclass
class DLACAlert:
    """Alerta del sistema DLAC."""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    source_component: str  # 'integrity_monitor', 'loss_detector', etc.
    affected_data: List[str] = field(default_factory=list)
    affected_nodes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    escalation_level: int = 0  # 0-3, para escalada automática


@dataclass
class AlertRule:
    """Regla para procesamiento de alertas."""
    rule_id: str
    alert_types: List[AlertType]
    severity_filter: List[AlertSeverity]
    conditions: Dict[str, Any]  # Condiciones para activar la regla
    actions: List[Dict[str, Any]]  # Acciones a tomar
    enabled: bool = True
    cooldown_minutes: int = 5  # Tiempo entre alertas similares


class DLACAlertSystem:
    """
    Sistema de alertas para el sistema DLAC.

    Características:
    - Recepción y procesamiento de alertas
    - Filtrado y priorización
    - Escalada automática
    - Integración con notificaciones
    - Historial y resolución de alertas
    """

    def __init__(self,
                 notification_service: Optional[Any] = None,  # NotificationService
                 discord_webhook: Optional[str] = None,
                 alert_retention_days: int = 30,
                 max_concurrent_alerts: int = 100):
        """
        Inicializar sistema de alertas DLAC.

        Args:
            notification_service: Servicio de notificaciones para envío
            discord_webhook: URL de webhook de Discord
            alert_retention_days: Días para retener alertas
            max_concurrent_alerts: Máximo número de alertas activas
        """
        self.notification_service = notification_service
        self.discord_webhook = discord_webhook
        self.alert_retention_days = alert_retention_days
        self.max_concurrent_alerts = max_concurrent_alerts

        # Almacenamiento de alertas
        self.active_alerts: Dict[str, DLACAlert] = {}
        self.alert_history: List[DLACAlert] = []
        self.alert_counter = 0

        # Reglas de procesamiento
        self.alert_rules: Dict[str, AlertRule] = {}
        self._load_default_rules()

        # Estado del sistema
        self.is_running = False
        self.alert_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # Callback para alertas externas
        self.alert_callback = None

        # Estadísticas
        self.stats = {
            'total_alerts': 0,
            'active_alerts': 0,
            'resolved_alerts': 0,
            'escalated_alerts': 0,
            'notifications_sent': 0,
            'last_alert_time': None
        }

        logger.info("🔔 DLAC Alert System initialized")

    def trigger_alert(self, alert_type: Union[AlertType, str], severity: Union[AlertSeverity, str],
                     title: str, message: str, source_component: str,
                     affected_data: List[str] = None, affected_nodes: List[str] = None,
                     metadata: Dict[str, Any] = None) -> str:
        """
        Disparar una nueva alerta.

        Args:
            alert_type: Tipo de alerta
            severity: Severidad
            title: Título de la alerta
            message: Mensaje detallado
            source_component: Componente que genera la alerta
            affected_data: Datos afectados
            affected_nodes: Nodos afectados
            metadata: Metadatos adicionales

        Returns:
            ID de la alerta generada
        """
        # Convertir strings a enums si es necesario
        if isinstance(alert_type, str):
            alert_type = AlertType(alert_type)
        if isinstance(severity, str):
            severity = AlertSeverity(severity)

        self.alert_counter += 1
        alert_id = f"alert_{self.alert_counter}"

        alert = DLACAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            timestamp=datetime.now(),
            source_component=source_component,
            affected_data=affected_data or [],
            affected_nodes=affected_nodes or [],
            metadata=metadata or {}
        )

        # Verificar límites
        if len(self.active_alerts) >= self.max_concurrent_alerts:
            logger.warning("⚠️ Maximum concurrent alerts reached, dropping alert")
            return alert_id

        # Agregar a alertas activas
        self.active_alerts[alert_id] = alert
        self.stats['total_alerts'] += 1
        self.stats['active_alerts'] += 1
        self.stats['last_alert_time'] = datetime.now()

        # Procesar reglas de alerta
        self._process_alert_rules(alert)

        # Enviar notificaciones
        self._send_alert_notifications(alert)

        logger.warning(f"🚨 DLAC Alert triggered: {title} (severity: {severity.value})")
        return alert_id

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "system") -> bool:
        """
        Reconocer una alerta.

        Args:
            alert_id: ID de la alerta
            acknowledged_by: Quién reconoce la alerta

        Returns:
            True si se reconoció exitosamente
        """
        if alert_id not in self.active_alerts:
            return False

        alert = self.active_alerts[alert_id]
        alert.acknowledged = True
        alert.acknowledged_at = datetime.now()
        alert.acknowledged_by = acknowledged_by

        logger.info(f"✅ Alert {alert_id} acknowledged by {acknowledged_by}")
        return True

    def resolve_alert(self, alert_id: str, resolution_note: str = "") -> bool:
        """
        Resolver una alerta.

        Args:
            alert_id: ID de la alerta
            resolution_note: Nota de resolución

        Returns:
            True si se resolvió exitosamente
        """
        if alert_id not in self.active_alerts:
            return False

        alert = self.active_alerts[alert_id]
        alert.resolved = True
        alert.resolved_at = datetime.now()
        alert.metadata['resolution_note'] = resolution_note

        # Mover a historial
        self.alert_history.append(alert)
        del self.active_alerts[alert_id]

        self.stats['active_alerts'] -= 1
        self.stats['resolved_alerts'] += 1

        logger.info(f"✅ Alert {alert_id} resolved")
        return True

    def get_active_alerts(self, severity_filter: List[AlertSeverity] = None,
                         type_filter: List[AlertType] = None) -> List[Dict[str, Any]]:
        """
        Obtener alertas activas.

        Args:
            severity_filter: Filtrar por severidad
            type_filter: Filtrar por tipo

        Returns:
            Lista de alertas activas
        """
        alerts = list(self.active_alerts.values())

        if severity_filter:
            alerts = [a for a in alerts if a.severity in severity_filter]

        if type_filter:
            alerts = [a for a in alerts if a.alert_type in type_filter]

        return [self._alert_to_dict(a) for a in alerts]

    def get_alert_history(self, limit: int = 50, days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Obtener historial de alertas.

        Args:
            limit: Número máximo de alertas
            days_back: Días hacia atrás

        Returns:
            Lista de alertas del historial
        """
        cutoff = datetime.now() - timedelta(days=days_back)
        history = [a for a in self.alert_history if a.timestamp > cutoff]

        # Ordenar por timestamp descendente
        history.sort(key=lambda x: x.timestamp, reverse=True)

        return [self._alert_to_dict(a) for a in history[:limit]]

    def add_alert_rule(self, rule: AlertRule):
        """
        Agregar una regla de procesamiento de alertas.

        Args:
            rule: Regla a agregar
        """
        self.alert_rules[rule.rule_id] = rule
        logger.info(f"📋 Added alert rule: {rule.rule_id}")

    def remove_alert_rule(self, rule_id: str):
        """Remover una regla de alertas."""
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
            logger.info(f"🗑️ Removed alert rule: {rule_id}")

    def start_alert_system(self):
        """Iniciar sistema de alertas."""
        if self.is_running:
            logger.warning("⚠️ Alert system already running")
            return

        self.is_running = True
        self.stop_event.clear()
        self.alert_thread = threading.Thread(target=self._alert_monitor_loop, daemon=True)
        self.alert_thread.start()

        logger.info("🚀 Started DLAC Alert System")

    def stop_alert_system(self):
        """Detener sistema de alertas."""
        if not self.is_running:
            return

        self.is_running = False
        self.stop_event.set()

        if self.alert_thread:
            self.alert_thread.join(timeout=5)

        logger.info("⏹️ Stopped DLAC Alert System")

    def _process_alert_rules(self, alert: DLACAlert):
        """Procesar reglas para una alerta."""
        for rule in self.alert_rules.values():
            if not rule.enabled:
                continue

            if alert.alert_type not in rule.alert_types or alert.severity not in rule.severity_filter:
                continue

            # Verificar condiciones
            if self._check_rule_conditions(alert, rule):
                self._execute_rule_actions(alert, rule)

    def _check_rule_conditions(self, alert: DLACAlert, rule: AlertRule) -> bool:
        """Verificar si una alerta cumple las condiciones de una regla."""
        conditions = rule.conditions

        # Verificar severidad mínima
        if 'min_severity' in conditions:
            min_severity_level = ['low', 'medium', 'high', 'critical'].index(conditions['min_severity'])
            alert_severity_level = ['low', 'medium', 'high', 'critical'].index(alert.severity.value)
            if alert_severity_level < min_severity_level:
                return False

        # Verificar número de datos afectados
        if 'min_affected_data' in conditions:
            if len(alert.affected_data) < conditions['min_affected_data']:
                return False

        # Verificar número de nodos afectados
        if 'min_affected_nodes' in conditions:
            if len(alert.affected_nodes) < conditions['min_affected_nodes']:
                return False

        # Verificar cooldown (última alerta similar)
        if rule.cooldown_minutes > 0:
            cutoff = datetime.now() - timedelta(minutes=rule.cooldown_minutes)
            recent_similar = [a for a in self.alert_history
                            if a.alert_type == alert.alert_type and a.timestamp > cutoff]
            if recent_similar:
                return False

        return True

    def _execute_rule_actions(self, alert: DLACAlert, rule: AlertRule):
        """Ejecutar acciones de una regla."""
        for action in rule.actions:
            action_type = action.get('type')

            if action_type == 'escalate':
                alert.escalation_level = min(3, alert.escalation_level + 1)
                logger.info(f"⬆️ Alert {alert.alert_id} escalated to level {alert.escalation_level}")

            elif action_type == 'auto_acknowledge':
                self.acknowledge_alert(alert.alert_id, "auto_rule")

            elif action_type == 'set_priority':
                # Aquí podríamos ajustar prioridad de procesamiento
                pass

            elif action_type == 'custom_callback':
                callback = action.get('callback')
                if callback and callable(callback):
                    try:
                        callback(alert)
                    except Exception as e:
                        logger.error(f"❌ Error in custom callback: {e}")

    def _send_alert_notifications(self, alert: DLACAlert):
        """Enviar notificaciones para una alerta."""
        try:
            # Notificación por Discord
            if self.discord_webhook:
                self._send_discord_alert(alert)

            # Notificación por el servicio de notificaciones
            if self.notification_service:
                self._send_service_alert(alert)

            self.stats['notifications_sent'] += 1

        except Exception as e:
            logger.error(f"❌ Error sending alert notifications: {e}")

    def _send_discord_alert(self, alert: DLACAlert):
        """Enviar alerta por Discord."""
        try:
            import requests

            # Crear embed de Discord
            embed = {
                "title": f"🚨 DLAC Alert: {alert.title}",
                "description": alert.message,
                "color": self._get_severity_color(alert.severity),
                "fields": [
                    {
                        "name": "Severity",
                        "value": alert.severity.value.upper(),
                        "inline": True
                    },
                    {
                        "name": "Type",
                        "value": alert.alert_type.value.replace('_', ' ').title(),
                        "inline": True
                    },
                    {
                        "name": "Source",
                        "value": alert.source_component,
                        "inline": True
                    }
                ],
                "timestamp": alert.timestamp.isoformat(),
                "footer": {
                    "text": f"Alert ID: {alert.alert_id}"
                }
            }

            # Agregar campos adicionales si hay datos afectados
            if alert.affected_data:
                embed["fields"].append({
                    "name": "Affected Data",
                    "value": ", ".join(alert.affected_data[:5]),  # Máximo 5
                    "inline": False
                })

            if alert.affected_nodes:
                embed["fields"].append({
                    "name": "Affected Nodes",
                    "value": ", ".join(alert.affected_nodes[:5]),  # Máximo 5
                    "inline": False
                })

            payload = {
                "embeds": [embed]
            }

            response = requests.post(self.discord_webhook, json=payload, timeout=5)
            response.raise_for_status()

        except Exception as e:
            logger.error(f"❌ Error sending Discord alert: {e}")

    def _send_service_alert(self, alert: DLACAlert):
        """Enviar alerta usando el servicio de notificaciones."""
        try:
            # Crear notificación para administradores (user_id=0 podría ser sistema)
            # En implementación real, esto debería enviar a usuarios específicos
            asyncio.run(self.notification_service.send_realtime_notification(
                user_id=0,  # Sistema
                event_type=f"dlac.{alert.alert_type.value}",
                title=alert.title,
                message=alert.message,
                data={
                    'alert_id': alert.alert_id,
                    'severity': alert.severity.value,
                    'source': alert.source_component,
                    'affected_data': alert.affected_data,
                    'affected_nodes': alert.affected_nodes,
                    'metadata': alert.metadata
                }
            ))

        except Exception as e:
            logger.error(f"❌ Error sending service alert: {e}")

    def _alert_monitor_loop(self):
        """Bucle de monitoreo de alertas."""
        while not self.stop_event.is_set():
            try:
                # Verificar alertas para escalada automática
                self._check_alert_escalation()

                # Limpiar alertas antiguas
                self._cleanup_old_alerts()

            except Exception as e:
                logger.error(f"❌ Alert monitor error: {e}")

            # Esperar 60 segundos
            self.stop_event.wait(60)

    def _check_alert_escalation(self):
        """Verificar escalada automática de alertas."""
        now = datetime.now()

        for alert in list(self.active_alerts.values()):
            if alert.acknowledged:
                continue

            # Escalar basado en tiempo sin reconocer
            age_minutes = (now - alert.timestamp).total_seconds() / 60

            if age_minutes > 30 and alert.escalation_level < 1:
                alert.escalation_level = 1
                self.stats['escalated_alerts'] += 1
                logger.warning(f"⬆️ Alert {alert.alert_id} auto-escalated to level 1")

            elif age_minutes > 120 and alert.escalation_level < 2:
                alert.escalation_level = 2
                logger.warning(f"⬆️ Alert {alert.alert_id} auto-escalated to level 2")

            elif age_minutes > 480 and alert.escalation_level < 3:  # 8 horas
                alert.escalation_level = 3
                logger.error(f"🚨 Alert {alert.alert_id} auto-escalated to level 3 (CRITICAL)")

    def _cleanup_old_alerts(self):
        """Limpiar alertas antiguas del historial."""
        cutoff = datetime.now() - timedelta(days=self.alert_retention_days)
        self.alert_history = [a for a in self.alert_history if a.timestamp > cutoff]

    def _load_default_rules(self):
        """Cargar reglas de alertas por defecto."""
        # Regla para corrupción crítica
        corruption_rule = AlertRule(
            rule_id="critical_corruption",
            alert_types=[AlertType.CORRUPTION_DETECTED],
            severity_filter=[AlertSeverity.CRITICAL],
            conditions={'min_affected_data': 1},
            actions=[
                {'type': 'escalate'},
                {'type': 'auto_acknowledge'}
            ],
            cooldown_minutes=10
        )

        # Regla para pérdida de nodos
        node_loss_rule = AlertRule(
            rule_id="node_loss",
            alert_types=[AlertType.LOSS_DETECTED],
            severity_filter=[AlertSeverity.HIGH, AlertSeverity.CRITICAL],
            conditions={'min_affected_nodes': 1},
            actions=[
                {'type': 'escalate'}
            ],
            cooldown_minutes=5
        )

        self.alert_rules.update({
            corruption_rule.rule_id: corruption_rule,
            node_loss_rule.rule_id: node_loss_rule
        })

    def _get_severity_color(self, severity: AlertSeverity) -> int:
        """Obtener color de Discord para severidad."""
        colors = {
            AlertSeverity.LOW: 0x00FF00,      # Verde
            AlertSeverity.MEDIUM: 0xFFFF00,   # Amarillo
            AlertSeverity.HIGH: 0xFF8000,     # Naranja
            AlertSeverity.CRITICAL: 0xFF0000  # Rojo
        }
        return colors.get(severity, 0x808080)

    def _alert_to_dict(self, alert: DLACAlert) -> Dict[str, Any]:
        """Convertir alerta a diccionario."""
        return {
            'alert_id': alert.alert_id,
            'alert_type': alert.alert_type.value,
            'severity': alert.severity.value,
            'title': alert.title,
            'message': alert.message,
            'timestamp': alert.timestamp.isoformat(),
            'source_component': alert.source_component,
            'affected_data': alert.affected_data,
            'affected_nodes': alert.affected_nodes,
            'metadata': alert.metadata,
            'acknowledged': alert.acknowledged,
            'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            'acknowledged_by': alert.acknowledged_by,
            'resolved': alert.resolved,
            'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
            'escalation_level': alert.escalation_level
        }

    def get_alert_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del sistema de alertas."""
        return {
            **self.stats,
            'active_alerts_count': len(self.active_alerts),
            'history_alerts_count': len(self.alert_history),
            'rules_count': len(self.alert_rules),
            'is_running': self.is_running
        }

    def export_alerts(self, filepath: str, format: str = 'json'):
        """
        Exportar alertas a archivo.

        Args:
            filepath: Ruta del archivo
            format: Formato ('json' o 'csv')
        """
        try:
            if format == 'json':
                data = {
                    'active_alerts': [self._alert_to_dict(a) for a in self.active_alerts.values()],
                    'alert_history': [self._alert_to_dict(a) for a in self.alert_history],
                    'exported_at': datetime.now().isoformat()
                }
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

            elif format == 'csv':
                import csv
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    # Header
                    writer.writerow(['alert_id', 'type', 'severity', 'title', 'timestamp',
                                   'source', 'acknowledged', 'resolved'])

                    # Active alerts
                    for alert in self.active_alerts.values():
                        writer.writerow([
                            alert.alert_id, alert.alert_type.value, alert.severity.value,
                            alert.title, alert.timestamp.isoformat(), alert.source_component,
                            alert.acknowledged, alert.resolved
                        ])

                    # History
                    for alert in self.alert_history:
                        writer.writerow([
                            alert.alert_id, alert.alert_type.value, alert.severity.value,
                            alert.title, alert.timestamp.isoformat(), alert.source_component,
                            alert.acknowledged, alert.resolved
                        ])

            logger.info(f"📄 Alerts exported to {filepath}")

        except Exception as e:
            logger.error(f"❌ Error exporting alerts: {e}")