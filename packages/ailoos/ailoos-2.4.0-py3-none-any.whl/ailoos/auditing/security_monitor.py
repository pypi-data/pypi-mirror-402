"""
Sistema de monitoreo de seguridad y alertas para AILOOS.
Detecta amenazas, anomalías y genera alertas automáticas.
"""

import asyncio
import re
import time
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import ipaddress
import hashlib

from ..core.logging import get_logger
from .audit_manager import get_audit_manager, SecurityAlertLevel, AuditEventType
from .structured_logger import get_structured_logger
from ..core.config import get_config

logger = get_logger(__name__)
structured_logger = get_structured_logger("security_monitor")


@dataclass
class SecurityRule:
    """Regla de detección de seguridad."""
    rule_id: str
    name: str
    description: str
    severity: SecurityAlertLevel
    pattern: str  # Regex pattern o condición
    rule_type: str  # 'regex', 'threshold', 'anomaly', 'correlation'
    target_field: str  # Campo del evento a verificar
    threshold: Optional[int] = None
    time_window_seconds: int = 300  # 5 minutos por defecto
    enabled: bool = True
    actions: List[str] = field(default_factory=lambda: ["alert", "log"])

    def matches(self, event_data: Dict[str, Any]) -> bool:
        """Verificar si la regla coincide con los datos del evento."""
        if not self.enabled:
            return False

        value = self._extract_value(event_data, self.target_field)
        if value is None:
            return False

        if self.rule_type == 'regex':
            return bool(re.search(self.pattern, str(value), re.IGNORECASE))
        elif self.rule_type == 'threshold':
            # Para reglas de umbral, se verifica en el monitor
            return False
        elif self.rule_type == 'anomaly':
            # Anomalías se detectan en el monitor con ML/stats
            return False

        return False

    def _extract_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Extraer valor de campo anidado (e.g., 'details.ip_address')."""
        keys = field_path.split('.')
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current


@dataclass
class ThreatIndicator:
    """Indicador de amenaza."""
    indicator_id: str
    indicator_type: str  # 'ip', 'user', 'pattern', 'hash'
    value: str
    severity: SecurityAlertLevel
    description: str
    first_seen: datetime
    last_seen: datetime
    hit_count: int = 0
    blocked: bool = False
    expires_at: Optional[datetime] = None

    def is_expired(self) -> bool:
        """Verificar si el indicador ha expirado."""
        return self.expires_at and datetime.now() > self.expires_at

    def update_hit(self):
        """Actualizar contador de hits."""
        self.hit_count += 1
        self.last_seen = datetime.now()


class SecurityMonitor:
    """
    Monitor de seguridad que detecta amenazas y genera alertas.
    Implementa reglas de detección, indicadores de compromiso y análisis de comportamiento.
    """

    def __init__(self):
        self.config = get_config()
        self.audit_manager = get_audit_manager()
        self.logger = structured_logger

        # Reglas de seguridad
        self.security_rules: Dict[str, SecurityRule] = {}
        self._load_default_rules()

        # Indicadores de amenaza
        self.threat_indicators: Dict[str, ThreatIndicator] = {}
        self._load_threat_intelligence()

        # Estado de monitoreo
        self.event_buffer: deque = deque(maxlen=10000)
        self.ip_activity: Dict[str, List[datetime]] = defaultdict(list)
        self.user_activity: Dict[str, List[datetime]] = defaultdict(list)
        self.failed_logins: Dict[str, List[datetime]] = defaultdict(list)
        self.suspicious_patterns: Dict[str, int] = defaultdict(int)

        # Umbrales configurables
        self.thresholds = {
            'max_failed_logins_per_hour': 5,
            'max_requests_per_minute': 100,
            'max_config_changes_per_hour': 10,
            'suspicious_ip_threshold': 3,
            'brute_force_window_minutes': 15
        }

        # Estado de bloqueo
        self.blocked_ips: Set[str] = set()
        self.blocked_users: Set[str] = set()

        # Callbacks de alertas
        self.alert_callbacks: List[Callable] = []

        # Monitoreo se inicia por separado después de la inicialización

    def _load_default_rules(self):
        """Cargar reglas de seguridad por defecto."""
        default_rules = [
            SecurityRule(
                rule_id="failed_login_burst",
                name="Ráfaga de logins fallidos",
                description="Múltiples intentos de login fallidos desde la misma IP",
                severity=SecurityAlertLevel.HIGH,
                pattern=r".*",
                rule_type="threshold",
                target_field="details.failed_login_count",
                threshold=5,
                time_window_seconds=3600
            ),
            SecurityRule(
                rule_id="suspicious_sql",
                name="Patrones SQL sospechosos",
                description="Detección de posibles inyecciones SQL",
                severity=SecurityAlertLevel.CRITICAL,
                pattern=r"(union|select|insert|update|delete|drop|create|alter).*(\-\-|#|\/\*|\*\/)",
                rule_type="regex",
                target_field="details.query"
            ),
            SecurityRule(
                rule_id="config_sensitive_change",
                name="Cambio en configuración sensible",
                description="Modificación de configuraciones críticas del sistema",
                severity=SecurityAlertLevel.MEDIUM,
                pattern=r"^(jwt_secret|encryption_key|database_url|api_key)",
                rule_type="regex",
                target_field="resource"
            ),
            SecurityRule(
                rule_id="unusual_hour_access",
                name="Acceso en horario inusual",
                description="Acceso al sistema fuera del horario normal",
                severity=SecurityAlertLevel.LOW,
                pattern=r".*",
                rule_type="threshold",
                target_field="timestamp.hour",
                threshold=22  # Después de las 10 PM
            ),
            SecurityRule(
                rule_id="rapid_config_changes",
                name="Cambios rápidos de configuración",
                description="Múltiples cambios de configuración en poco tiempo",
                severity=SecurityAlertLevel.MEDIUM,
                pattern=r".*",
                rule_type="threshold",
                target_field="user_id",
                threshold=10,
                time_window_seconds=3600
            ),
            # Reglas específicas para Knowledge Graph
            SecurityRule(
                rule_id="kg_massive_operations",
                name="Operaciones masivas en Knowledge Graph",
                description="Múltiples operaciones de modificación en KG en poco tiempo",
                severity=SecurityAlertLevel.MEDIUM,
                pattern=r".*",
                rule_type="threshold",
                target_field="action",
                threshold=100,
                time_window_seconds=3600
            ),
            SecurityRule(
                rule_id="kg_destructive_operations",
                name="Operaciones destructivas en Knowledge Graph",
                description="Operaciones que pueden eliminar datos del grafo",
                severity=SecurityAlertLevel.HIGH,
                pattern=r"(clear|remove_triple|DELETE|DROP)",
                rule_type="regex",
                target_field="action"
            ),
            SecurityRule(
                rule_id="kg_complex_queries",
                name="Consultas extremadamente complejas",
                description="Consultas KG que pueden indicar intentos de análisis o ataque",
                severity=SecurityAlertLevel.LOW,
                pattern=r".*",
                rule_type="threshold",
                target_field="details.query_length",
                threshold=10000
            ),
            SecurityRule(
                rule_id="kg_inference_abuse",
                name="Abuso de inferencia",
                description="Inferencias que generan demasiados triples nuevos",
                severity=SecurityAlertLevel.MEDIUM,
                pattern=r".*",
                rule_type="threshold",
                target_field="details.triples_inferred",
                threshold=1000
            )
        ]

        for rule in default_rules:
            self.security_rules[rule.rule_id] = rule

    def _load_threat_intelligence(self):
        """Cargar indicadores de amenaza básicos."""
        # En implementación real, esto vendría de feeds de threat intelligence
        known_bad_ips = [
            "10.0.0.1",  # Ejemplo
            "192.168.1.100"  # Ejemplo
        ]

        for ip in known_bad_ips:
            indicator = ThreatIndicator(
                indicator_id=f"bad_ip_{hash(ip) % 10000}",
                indicator_type="ip",
                value=ip,
                severity=SecurityAlertLevel.HIGH,
                description="IP conocida por actividad maliciosa",
                first_seen=datetime.now() - timedelta(days=1),
                last_seen=datetime.now(),
                blocked=True
            )
            self.threat_indicators[indicator.indicator_id] = indicator

    async def process_event(self, event_data: Dict[str, Any]):
        """
        Procesar un evento para detección de seguridad.

        Args:
            event_data: Datos del evento de auditoría
        """
        # Agregar al buffer
        self.event_buffer.append(event_data)

        # Extraer información relevante
        event_type = event_data.get('event_type')
        user_id = event_data.get('user_id')
        ip_address = event_data.get('ip_address')
        resource = event_data.get('resource', '')
        action = event_data.get('action', '')
        timestamp = datetime.fromisoformat(event_data.get('timestamp', datetime.now().isoformat()))

        # Actualizar contadores de actividad
        if ip_address:
            self.ip_activity[ip_address].append(timestamp)
            # Limpiar actividad antigua
            cutoff = datetime.now() - timedelta(hours=1)
            self.ip_activity[ip_address] = [t for t in self.ip_activity[ip_address] if t > cutoff]

        if user_id:
            self.user_activity[user_id].append(timestamp)
            cutoff = datetime.now() - timedelta(hours=1)
            self.user_activity[user_id] = [t for t in self.user_activity[user_id] if t > cutoff]

        # Verificar reglas de seguridad
        await self._check_security_rules(event_data)

        # Verificar indicadores de amenaza
        await self._check_threat_indicators(event_data)

        # Detección específica por tipo de evento
        if event_type == 'SECURITY_ALERT':
            await self._handle_security_event(event_data)
        elif event_type == 'USER_ACTION' and action == 'login':
            await self._handle_login_attempt(event_data)
        elif event_type == 'CONFIG_CHANGE':
            await self._handle_config_change(event_data)
        elif event_type in ['KNOWLEDGE_GRAPH_OPERATION', 'KNOWLEDGE_GRAPH_INFERENCE', 'KNOWLEDGE_GRAPH_QUERY']:
            await self._handle_kg_event(event_data)

    async def _check_security_rules(self, event_data: Dict[str, Any]):
        """Verificar reglas de seguridad contra el evento."""
        for rule in self.security_rules.values():
            if rule.matches(event_data):
                await self._trigger_rule_alert(rule, event_data)
                break  # Una regla por evento para evitar spam

    async def _check_threat_indicators(self, event_data: Dict[str, Any]):
        """Verificar indicadores de amenaza."""
        # Verificar IPs
        ip_address = event_data.get('ip_address')
        if ip_address:
            for indicator in self.threat_indicators.values():
                if (indicator.indicator_type == 'ip' and
                    indicator.value == ip_address and
                    not indicator.is_expired()):

                    indicator.update_hit()

                    if indicator.blocked:
                        await self._block_ip(ip_address, f"Threat indicator: {indicator.description}")
                    else:
                        await self._trigger_threat_alert(indicator, event_data)
                    break

        # Verificar usuarios
        user_id = event_data.get('user_id')
        if user_id:
            for indicator in self.threat_indicators.values():
                if (indicator.indicator_type == 'user' and
                    indicator.value == user_id and
                    not indicator.is_expired()):

                    indicator.update_hit()
                    await self._trigger_threat_alert(indicator, event_data)
                    break

    async def _handle_security_event(self, event_data: Dict[str, Any]):
        """Manejar eventos de seguridad específicos."""
        alert_type = event_data.get('details', {}).get('alert_type')

        if alert_type == 'failed_login':
            ip_address = event_data.get('ip_address')
            if ip_address:
                self.failed_logins[ip_address].append(datetime.fromisoformat(event_data['timestamp']))

                # Limpiar antiguos
                cutoff = datetime.now() - timedelta(minutes=self.thresholds['brute_force_window_minutes'])
                self.failed_logins[ip_address] = [t for t in self.failed_logins[ip_address] if t > cutoff]

                # Verificar umbral de brute force
                if len(self.failed_logins[ip_address]) >= self.thresholds['max_failed_logins_per_hour']:
                    await self._block_ip(ip_address, "Brute force attack detected")

    async def _handle_login_attempt(self, event_data: Dict[str, Any]):
        """Manejar intentos de login."""
        success = event_data.get('success', True)
        ip_address = event_data.get('ip_address')

        if not success and ip_address:
            # Contar logins fallidos
            recent_failures = len([
                t for t in self.failed_logins.get(ip_address, [])
                if t > datetime.now() - timedelta(hours=1)
            ])

            if recent_failures >= self.thresholds['max_failed_logins_per_hour']:
                await self._trigger_brute_force_alert(ip_address, recent_failures)

    async def _handle_config_change(self, event_data: Dict[str, Any]):
        """Manejar cambios de configuración."""
        user_id = event_data.get('user_id')
        if user_id:
            # Contar cambios recientes por usuario
            recent_changes = len([
                e for e in self.event_buffer
                if (e.get('event_type') == 'CONFIG_CHANGE' and
                    e.get('user_id') == user_id and
                    datetime.fromisoformat(e.get('timestamp', '')) > datetime.now() - timedelta(hours=1))
            ])

            if recent_changes >= self.thresholds['max_config_changes_per_hour']:
                await self._trigger_suspicious_config_alert(user_id, recent_changes)

    async def _handle_kg_event(self, event_data: Dict[str, Any]):
        """Manejar eventos de Knowledge Graph."""
        event_type = event_data.get('event_type')
        action = event_data.get('action', '')
        user_id = event_data.get('user_id')
        details = event_data.get('details', {})

        # Monitorear operaciones destructivas
        if action in ['clear', 'remove_triple'] and not event_data.get('success', True):
            await self._trigger_kg_destructive_failure_alert(action, user_id)

        # Monitorear consultas complejas
        if event_type == 'KNOWLEDGE_GRAPH_QUERY':
            query = details.get('query', '')
            if len(query) > 10000:  # Consultas muy largas
                await self._trigger_kg_complex_query_alert(user_id, len(query))

        # Monitorear inferencias masivas
        if event_type == 'KNOWLEDGE_GRAPH_INFERENCE':
            triples_inferred = details.get('triples_inferred', 0)
            if triples_inferred > 1000:
                await self._trigger_kg_massive_inference_alert(user_id, triples_inferred)

        # Contar operaciones por usuario para detectar abuso
        if user_id:
            recent_kg_ops = len([
                e for e in self.event_buffer
                if (e.get('event_type', '').startswith('KNOWLEDGE_GRAPH') and
                    e.get('user_id') == user_id and
                    datetime.fromisoformat(e.get('timestamp', '')) > datetime.now() - timedelta(hours=1))
            ])

            if recent_kg_ops > 200:  # Umbral de operaciones por hora
                await self._trigger_kg_operation_abuse_alert(user_id, recent_kg_ops)

    async def _trigger_rule_alert(self, rule: SecurityRule, event_data: Dict[str, Any]):
        """Generar alerta por regla de seguridad."""
        alert_title = f"Regla de seguridad activada: {rule.name}"
        alert_description = f"{rule.description}\nEvento: {event_data.get('resource', 'unknown')}"

        await self.audit_manager.log_event(
            event_type=AuditEventType.SECURITY_ALERT,
            resource="security_monitor",
            action="rule_triggered",
            details={
                "rule_id": rule.rule_id,
                "rule_name": rule.name,
                "severity": rule.severity.value,
                "triggered_by": event_data
            },
            severity=rule.severity,
            success=False
        )

        # Ejecutar acciones de la regla
        for action in rule.actions:
            if action == "alert":
                await self._send_alert(rule.severity, alert_title, alert_description, event_data)
            elif action == "block_ip" and event_data.get('ip_address'):
                await self._block_ip(event_data['ip_address'], f"Blocked by rule: {rule.name}")
            elif action == "block_user" and event_data.get('user_id'):
                await self._block_user(event_data['user_id'], f"Blocked by rule: {rule.name}")

    async def _trigger_threat_alert(self, indicator: ThreatIndicator, event_data: Dict[str, Any]):
        """Generar alerta por indicador de amenaza."""
        alert_title = f"Indicador de amenaza detectado: {indicator.indicator_type}"
        alert_description = f"{indicator.description}\nValor: {indicator.value}"

        await self.audit_manager.log_event(
            event_type=AuditEventType.SECURITY_ALERT,
            resource="threat_intelligence",
            action="indicator_match",
            details={
                "indicator_id": indicator.indicator_id,
                "indicator_type": indicator.indicator_type,
                "indicator_value": indicator.value,
                "severity": indicator.severity.value,
                "hit_count": indicator.hit_count
            },
            severity=indicator.severity,
            success=False
        )

    async def _trigger_brute_force_alert(self, ip_address: str, failure_count: int):
        """Generar alerta de ataque de fuerza bruta."""
        alert_title = "Posible ataque de fuerza bruta detectado"
        alert_description = f"Múltiples intentos de login fallidos desde IP {ip_address} ({failure_count} fallos)"

        await self.audit_manager.log_event(
            event_type=AuditEventType.SECURITY_ALERT,
            resource="authentication",
            action="brute_force_detected",
            ip_address=ip_address,
            details={
                "failure_count": failure_count,
                "ip_address": ip_address,
                "alert_type": "brute_force"
            },
            severity=SecurityAlertLevel.CRITICAL,
            success=False
        )

        await self._send_alert(SecurityAlertLevel.CRITICAL, alert_title, alert_description, {"ip_address": ip_address})

    async def _trigger_suspicious_config_alert(self, user_id: str, change_count: int):
        """Generar alerta de cambios sospechosos de configuración."""
        alert_title = "Actividad sospechosa de configuración"
        alert_description = f"Usuario {user_id} realizó {change_count} cambios de configuración en la última hora"

        await self.audit_manager.log_event(
            event_type=AuditEventType.SECURITY_ALERT,
            resource="configuration",
            action="suspicious_config_activity",
            user_id=user_id,
            details={
                "change_count": change_count,
                "user_id": user_id,
                "alert_type": "suspicious_config"
            },
            severity=SecurityAlertLevel.HIGH,
            success=False
        )

        await self._send_alert(SecurityAlertLevel.HIGH, alert_title, alert_description, {"user_id": user_id})

    async def _trigger_kg_destructive_failure_alert(self, action: str, user_id: Optional[str]):
        """Generar alerta por fallo en operación destructiva de KG."""
        alert_title = f"Operación destructiva fallida en Knowledge Graph: {action}"
        alert_description = f"Usuario {user_id} intentó ejecutar '{action}' pero falló, posible intento de manipulación"

        await self.audit_manager.log_event(
            event_type=AuditEventType.SECURITY_ALERT,
            resource="knowledge_graph",
            action="destructive_operation_failed",
            user_id=user_id,
            details={
                "destructive_action": action,
                "alert_type": "kg_destructive_failure"
            },
            severity=SecurityAlertLevel.HIGH,
            success=False
        )

        await self._send_alert(SecurityAlertLevel.HIGH, alert_title, alert_description, {"user_id": user_id, "action": action})

    async def _trigger_kg_complex_query_alert(self, user_id: Optional[str], query_length: int):
        """Generar alerta por consulta compleja en KG."""
        alert_title = "Consulta extremadamente compleja en Knowledge Graph"
        alert_description = f"Usuario {user_id} ejecutó consulta de {query_length} caracteres"

        await self.audit_manager.log_event(
            event_type=AuditEventType.SECURITY_ALERT,
            resource="knowledge_graph",
            action="complex_query_detected",
            user_id=user_id,
            details={
                "query_length": query_length,
                "alert_type": "kg_complex_query"
            },
            severity=SecurityAlertLevel.MEDIUM,
            success=False
        )

        await self._send_alert(SecurityAlertLevel.MEDIUM, alert_title, alert_description, {"user_id": user_id, "query_length": query_length})

    async def _trigger_kg_massive_inference_alert(self, user_id: Optional[str], triples_inferred: int):
        """Generar alerta por inferencia masiva en KG."""
        alert_title = "Inferencia masiva detectada en Knowledge Graph"
        alert_description = f"Usuario {user_id} generó {triples_inferred} triples mediante inferencia"

        await self.audit_manager.log_event(
            event_type=AuditEventType.SECURITY_ALERT,
            resource="knowledge_graph",
            action="massive_inference_detected",
            user_id=user_id,
            details={
                "triples_inferred": triples_inferred,
                "alert_type": "kg_massive_inference"
            },
            severity=SecurityAlertLevel.MEDIUM,
            success=False
        )

        await self._send_alert(SecurityAlertLevel.MEDIUM, alert_title, alert_description, {"user_id": user_id, "triples_inferred": triples_inferred})

    async def _trigger_kg_operation_abuse_alert(self, user_id: str, operation_count: int):
        """Generar alerta por abuso de operaciones en KG."""
        alert_title = "Abuso de operaciones detectado en Knowledge Graph"
        alert_description = f"Usuario {user_id} realizó {operation_count} operaciones en la última hora"

        await self.audit_manager.log_event(
            event_type=AuditEventType.SECURITY_ALERT,
            resource="knowledge_graph",
            action="operation_abuse_detected",
            user_id=user_id,
            details={
                "operation_count": operation_count,
                "alert_type": "kg_operation_abuse"
            },
            severity=SecurityAlertLevel.HIGH,
            success=False
        )

        await self._send_alert(SecurityAlertLevel.HIGH, alert_title, alert_description, {"user_id": user_id, "operation_count": operation_count})

    async def _block_ip(self, ip_address: str, reason: str):
        """Bloquear una dirección IP."""
        if ip_address in self.blocked_ips:
            return

        self.blocked_ips.add(ip_address)

        self.logger.log_security_event(
            "ip_blocked",
            {
                "ip_address": ip_address,
                "reason": reason,
                "blocked_at": datetime.now().isoformat()
            },
            SecurityAlertLevel.HIGH
        )

        # En implementación real, aquí se actualizarían firewalls, etc.
        self.logger.info(f"IP blocked: {ip_address} - {reason}")

    async def _block_user(self, user_id: str, reason: str):
        """Bloquear un usuario."""
        if user_id in self.blocked_users:
            return

        self.blocked_users.add(user_id)

        self.logger.log_security_event(
            "user_blocked",
            {
                "user_id": user_id,
                "reason": reason,
                "blocked_at": datetime.now().isoformat()
            },
            SecurityAlertLevel.CRITICAL
        )

        self.logger.info(f"User blocked: {user_id} - {reason}")

    async def _send_alert(self, severity: SecurityAlertLevel, title: str, description: str, context: Dict[str, Any]):
        """Enviar alerta a través del sistema de notificaciones."""
        # Notificar callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(severity, title, description, context)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {e}")

        # Log de la alerta
        self.logger.warning(f"Security Alert: {title} - {description}")

    def is_ip_blocked(self, ip_address: str) -> bool:
        """Verificar si una IP está bloqueada."""
        return ip_address in self.blocked_ips

    def is_user_blocked(self, user_id: str) -> bool:
        """Verificar si un usuario está bloqueado."""
        return user_id in self.blocked_users

    def add_security_rule(self, rule: SecurityRule):
        """Agregar una regla de seguridad."""
        self.security_rules[rule.rule_id] = rule
        self.logger.info(f"Security rule added: {rule.rule_id}")

    def remove_security_rule(self, rule_id: str):
        """Remover una regla de seguridad."""
        if rule_id in self.security_rules:
            del self.security_rules[rule_id]
            self.logger.info(f"Security rule removed: {rule_id}")

    def add_threat_indicator(self, indicator: ThreatIndicator):
        """Agregar indicador de amenaza."""
        self.threat_indicators[indicator.indicator_id] = indicator
        self.logger.info(f"Threat indicator added: {indicator.indicator_id}")

    def get_security_status(self) -> Dict[str, Any]:
        """Obtener estado actual de seguridad."""
        return {
            "blocked_ips_count": len(self.blocked_ips),
            "blocked_users_count": len(self.blocked_users),
            "active_rules_count": len([r for r in self.security_rules.values() if r.enabled]),
            "threat_indicators_count": len(self.threat_indicators),
            "recent_events_count": len(self.event_buffer),
            "failed_login_attempts": sum(len(failures) for failures in self.failed_logins.values())
        }

    async def _monitoring_loop(self):
        """Loop principal de monitoreo."""
        while True:
            try:
                # Análisis periódico de patrones
                await self._analyze_patterns()

                # Verificar expiración de indicadores
                await self._cleanup_expired_indicators()

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")

            await asyncio.sleep(60)  # Cada minuto

    async def _analyze_patterns(self):
        """Analizar patrones de seguridad."""
        # Detectar IPs con alta actividad
        for ip, timestamps in self.ip_activity.items():
            recent_requests = len([t for t in timestamps if t > datetime.now() - timedelta(minutes=1)])
            if recent_requests > self.thresholds['max_requests_per_minute']:
                await self._trigger_high_activity_alert(ip, recent_requests, "requests_per_minute")

        # Detectar usuarios con alta actividad
        for user_id, timestamps in self.user_activity.items():
            recent_actions = len([t for t in timestamps if t > datetime.now() - timedelta(minutes=5)])
            if recent_actions > 50:  # Umbral arbitrario
                await self._trigger_high_activity_alert(user_id, recent_actions, "actions_per_5min", is_user=True)

    async def _trigger_high_activity_alert(self, identifier: str, count: int, metric: str, is_user: bool = False):
        """Generar alerta de alta actividad."""
        target_type = "user" if is_user else "IP"
        alert_title = f"Alta actividad detectada para {target_type}"
        alert_description = f"{target_type} {identifier}: {count} {metric}"

        await self.audit_manager.log_event(
            event_type=AuditEventType.SECURITY_ALERT,
            resource="activity_monitor",
            action="high_activity_detected",
            user_id=identifier if is_user else None,
            ip_address=identifier if not is_user else None,
            details={
                "target_type": target_type,
                "identifier": identifier,
                "count": count,
                "metric": metric,
                "alert_type": "high_activity"
            },
            severity=SecurityAlertLevel.MEDIUM,
            success=False
        )

    async def _cleanup_expired_indicators(self):
        """Limpiar indicadores de amenaza expirados."""
        expired = [ind_id for ind_id, indicator in self.threat_indicators.items() if indicator.is_expired()]
        for ind_id in expired:
            del self.threat_indicators[ind_id]
            self.logger.info(f"Expired threat indicator removed: {ind_id}")

    async def _cleanup_task(self):
        """Tarea de limpieza periódica."""
        while True:
            try:
                await asyncio.sleep(3600)  # Cada hora

                # Limpiar actividad antigua
                cutoff = datetime.now() - timedelta(hours=24)
                for ip in list(self.ip_activity.keys()):
                    self.ip_activity[ip] = [t for t in self.ip_activity[ip] if t > cutoff]
                    if not self.ip_activity[ip]:
                        del self.ip_activity[ip]

                for user in list(self.user_activity.keys()):
                    self.user_activity[user] = [t for t in self.user_activity[user] if t > cutoff]
                    if not self.user_activity[user]:
                        del self.user_activity[user]

                # Limpiar bloqueos antiguos (desbloquear después de 24 horas)
                # En implementación real, esto sería configurable
                self.blocked_ips.clear()
                self.blocked_users.clear()

                self.logger.info("Security monitor cleanup completed")

            except Exception as e:
                self.logger.error(f"Error in cleanup task: {e}")

    def start_monitoring(self):
        """Iniciar el monitoreo después de la inicialización del servidor."""
        asyncio.create_task(self._monitoring_loop())
        asyncio.create_task(self._cleanup_task())

    def add_alert_callback(self, callback: Callable):
        """Agregar callback para alertas."""
        self.alert_callbacks.append(callback)


# Instancia global
security_monitor = SecurityMonitor()


def get_security_monitor() -> SecurityMonitor:
    """Obtener instancia global del monitor de seguridad."""
    return security_monitor