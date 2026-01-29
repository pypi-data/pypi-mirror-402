"""
Sistema de alertas centralizado para Ailoos.
Gestiona alertas unificadas de modelos, sistema y seguridad con escalado inteligente,
notificaciones críticas y persistencia en base de datos.
"""

import asyncio
import json
import logging
import sqlite3
import smtplib
import hashlib
import aiohttp
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path

from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AlertConfig:
    """Configuración del sistema de alertas centralizado."""
    # Base de datos
    db_path: str = "alerts.db"

    # Notificaciones
    email_enabled: bool = False
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_recipients: List[str] = None

    discord_webhook_url: str = ""
    webhook_url: str = ""

    # Escalado y deduplicación
    dedup_window_minutes: int = 5
    max_alerts_per_hour: int = 50
    escalation_threshold_count: int = 3
    escalation_window_minutes: int = 10

    # Severidad
    critical_severity_threshold: float = 0.8

    def __post_init__(self):
        if self.email_recipients is None:
            self.email_recipients = []


@dataclass
class Alert:
    """Estructura de una alerta."""
    id: str
    type: str  # model, system, security
    subtype: str  # specific type like accuracy_drop, node_down, etc.
    severity: str  # low, medium, high, critical
    title: str
    message: str
    source: str  # component that generated the alert
    metadata: Dict[str, Any]
    timestamp: datetime
    escalated: bool = False
    escalation_count: int = 0
    last_escalation: Optional[datetime] = None


@dataclass
class NotificationTemplate:
    """Template para notificaciones."""
    name: str
    subject_template: str
    body_template: str
    channels: List[str]  # email, discord, webhook


class CentralizedAlertManager:
    """
    Gestor centralizado de alertas para Ailoos.

    Características:
    - Alertas unificadas de modelos, sistema y seguridad
    - Escalado automático de severidad basado en patrones
    - Notificaciones críticas (webhooks, Discord, email)
    - Deduplicación inteligente
    - Persistencia en SQLite
    - Manejo de concurrencia con asyncio
    """

    def __init__(self, config: AlertConfig = None):
        self.config = config or AlertConfig()

        # Base de datos
        self.db_path = Path(self.config.db_path)
        self.db_lock = asyncio.Lock()
        self._setup_database()

        # Estado del sistema
        self.alert_history: List[Alert] = []
        self.dedup_cache: Dict[str, datetime] = {}  # hash -> last_seen
        self.alert_counts: Dict[str, List[datetime]] = {}  # type -> timestamps
        self.active_alerts: Dict[str, Alert] = {}

        # Templates de notificación
        self.notification_templates = self._setup_templates()

        # Estadísticas
        self.stats = {
            'total_alerts': 0,
            'escalated_alerts': 0,
            'notifications_sent': 0,
            'duplicates_prevented': 0
        }

        logger.info("CentralizedAlertManager inicializado", extra={
            'db_path': str(self.db_path),
            'dedup_window': self.config.dedup_window_minutes,
            'max_alerts_hour': self.config.max_alerts_per_hour
        })

    def _setup_database(self):
        """Configurar base de datos SQLite."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id TEXT PRIMARY KEY,
                        type TEXT NOT NULL,
                        subtype TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        title TEXT NOT NULL,
                        message TEXT NOT NULL,
                        source TEXT NOT NULL,
                        metadata TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        escalated INTEGER DEFAULT 0,
                        escalation_count INTEGER DEFAULT 0,
                        last_escalation TEXT
                    )
                """)

                # Índices para rendimiento
                conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")

                conn.commit()

            logger.info("Base de datos de alertas configurada")

        except Exception as e:
            logger.error(f"Error configurando base de datos: {e}")
            raise

    def _setup_templates(self) -> Dict[str, NotificationTemplate]:
        """Configurar templates de notificación."""
        return {
            'critical': NotificationTemplate(
                name='critical',
                subject_template='🚨 ALERTA CRÍTICA: {title}',
                body_template="""
                **ALERTA CRÍTICA DETECTADA**

                **Tipo:** {type}
                **Severidad:** {severity}
                **Fuente:** {source}
                **Mensaje:** {message}

                **Detalles:**
                {metadata}

                **Timestamp:** {timestamp}

                Esta alerta requiere atención inmediata.
                """,
                channels=['email', 'discord', 'webhook']
            ),
            'high': NotificationTemplate(
                name='high',
                subject_template='⚠️ ALERTA ALTA: {title}',
                body_template="""
                **ALERTA DE ALTA PRIORIDAD**

                **Tipo:** {type}
                **Severidad:** {severity}
                **Fuente:** {source}
                **Mensaje:** {message}

                **Detalles:**
                {metadata}

                **Timestamp:** {timestamp}
                """,
                channels=['email', 'discord']
            ),
            'medium': NotificationTemplate(
                name='medium',
                subject_template='📢 ALERTA MEDIA: {title}',
                body_template="""
                **ALERTA MEDIA**

                **Tipo:** {type}
                **Severidad:** {severity}
                **Fuente:** {source}
                **Mensaje:** {message}

                **Timestamp:** {timestamp}
                """,
                channels=['email']
            )
        }

    async def process_alert(self, alert_data: Dict[str, Any]) -> str:
        """
        Procesar una nueva alerta con enrutamiento inteligente.

        Args:
            alert_data: Datos de la alerta

        Returns:
            ID de la alerta procesada
        """
        try:
            # Crear objeto Alert
            alert = self._create_alert(alert_data)

            # Verificar deduplicación
            if await self._is_duplicate(alert):
                self.stats['duplicates_prevented'] += 1
                logger.debug(f"Alerta duplicada prevenida: {alert.id}")
                return alert.id

            # Calcular severidad basada en patrones
            alert.severity = await self._calculate_severity(alert)

            # Verificar escalado automático
            await self.escalate_alert(alert)

            # Almacenar alerta
            await self._store_alert(alert)

            # Enviar notificaciones si es crítica
            if alert.severity in ['high', 'critical']:
                await self.send_notification(alert)

            # Actualizar estadísticas
            self.stats['total_alerts'] += 1
            if alert.escalated:
                self.stats['escalated_alerts'] += 1

            # Mantener en memoria
            self.active_alerts[alert.id] = alert
            self.alert_history.append(alert)

            # Limpiar historial antiguo
            await self._cleanup_old_alerts()

            logger.info(f"Alerta procesada: {alert.type}:{alert.subtype} - {alert.severity}", extra={
                'alert_id': alert.id,
                'severity': alert.severity,
                'escalated': alert.escalated
            })

            return alert.id

        except Exception as e:
            logger.error(f"Error procesando alerta: {e}", extra={'alert_data': alert_data})
            raise

    def _create_alert(self, alert_data: Dict[str, Any]) -> Alert:
        """Crear objeto Alert desde datos."""
        alert_id = alert_data.get('id') or hashlib.md5(
            f"{alert_data.get('type', '')}:{alert_data.get('subtype', '')}:{alert_data.get('source', '')}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        return Alert(
            id=alert_id,
            type=alert_data.get('type', 'unknown'),
            subtype=alert_data.get('subtype', 'unknown'),
            severity=alert_data.get('severity', 'low'),
            title=alert_data.get('title', 'Alerta sin título'),
            message=alert_data.get('message', 'Mensaje no especificado'),
            source=alert_data.get('source', 'unknown'),
            metadata=alert_data.get('metadata', {}),
            timestamp=datetime.now()
        )

    async def _is_duplicate(self, alert: Alert) -> bool:
        """Verificar si la alerta es duplicada."""
        # Crear hash de la alerta
        alert_hash = hashlib.md5(
            f"{alert.type}:{alert.subtype}:{alert.source}:{alert.title}".encode()
        ).hexdigest()

        now = datetime.now()
        window_start = now - timedelta(minutes=self.config.dedup_window_minutes)

        # Verificar en caché
        if alert_hash in self.dedup_cache:
            last_seen = self.dedup_cache[alert_hash]
            if last_seen > window_start:
                return True

        # Actualizar caché
        self.dedup_cache[alert_hash] = now

        # Limpiar caché antigua
        to_remove = [k for k, v in self.dedup_cache.items() if v < window_start]
        for k in to_remove:
            del self.dedup_cache[k]

        return False

    async def _calculate_severity(self, alert: Alert) -> str:
        """Calcular severidad basada en patrones y contexto."""
        base_severity = alert.severity

        # Analizar patrones de frecuencia
        alert_type = f"{alert.type}:{alert.subtype}"
        now = datetime.now()
        window_start = now - timedelta(minutes=self.config.escalation_window_minutes)

        if alert_type not in self.alert_counts:
            self.alert_counts[alert_type] = []

        # Filtrar timestamps recientes
        recent_counts = [t for t in self.alert_counts[alert_type] if t > window_start]
        self.alert_counts[alert_type] = recent_counts

        # Agregar timestamp actual
        self.alert_counts[alert_type].append(now)

        # Escalar basado en frecuencia
        count = len(recent_counts) + 1
        if count >= 5:
            base_severity = 'critical'
        elif count >= 3:
            base_severity = 'high'
        elif count >= 2:
            base_severity = 'medium'

        # Escalar basado en tipo específico
        if alert.type == 'security':
            severity_levels = {'low': 'medium', 'medium': 'high', 'high': 'critical'}
            base_severity = severity_levels.get(base_severity, base_severity)
        elif alert.type == 'system' and alert.subtype == 'node_down':
            severity_levels = {'low': 'high', 'medium': 'high', 'high': 'critical'}
            base_severity = severity_levels.get(base_severity, base_severity)

        return base_severity

    async def escalate_alert(self, alert: Alert):
        """
        Escalar alerta automáticamente basado en patrones.

        Args:
            alert: Alerta a escalar
        """
        try:
            alert_type = f"{alert.type}:{alert.subtype}"
            now = datetime.now()

            # Verificar umbral de escalado
            if alert_type in self.alert_counts:
                recent_count = len([t for t in self.alert_counts[alert_type]
                                  if t > now - timedelta(minutes=self.config.escalation_window_minutes)])

                if recent_count >= self.config.escalation_threshold_count:
                    # Escalar severidad
                    severity_escalation = {
                        'low': 'medium',
                        'medium': 'high',
                        'high': 'critical'
                    }

                    old_severity = alert.severity
                    alert.severity = severity_escalation.get(alert.severity, alert.severity)

                    if alert.severity != old_severity:
                        alert.escalated = True
                        alert.escalation_count += 1
                        alert.last_escalation = now

                        logger.warning(f"Alerta escalada: {alert.id} de {old_severity} a {alert.severity}", extra={
                            'alert_id': alert.id,
                            'old_severity': old_severity,
                            'new_severity': alert.severity,
                            'escalation_count': alert.escalation_count
                        })

        except Exception as e:
            logger.error(f"Error escalando alerta {alert.id}: {e}")

    async def send_notification(self, alert: Alert, channels: Optional[List[str]] = None):
        """
        Enviar notificación usando templates configurables.

        Args:
            alert: Alerta a notificar
            channels: Canales específicos (opcional)
        """
        try:
            # Determinar template basado en severidad
            template = self.notification_templates.get(alert.severity,
                                                     self.notification_templates.get('medium'))

            if not template:
                logger.warning(f"No template encontrado para severidad {alert.severity}")
                return

            # Usar canales especificados o del template
            target_channels = channels or template.channels

            # Preparar datos para template
            template_data = {
                'type': alert.type,
                'subtype': alert.subtype,
                'severity': alert.severity.upper(),
                'title': alert.title,
                'message': alert.message,
                'source': alert.source,
                'metadata': json.dumps(alert.metadata, indent=2),
                'timestamp': alert.timestamp.isoformat(),
                'escalated': 'SÍ' if alert.escalated else 'NO'
            }

            # Renderizar templates
            subject = template.subject_template.format(**template_data)
            body = template.body_template.format(**template_data)

            # Enviar por cada canal
            tasks = []
            for channel in target_channels:
                if channel == 'email' and self.config.email_enabled:
                    tasks.append(self._send_email_notification(subject, body, alert))
                elif channel == 'discord' and self.config.discord_webhook_url:
                    tasks.append(self._send_discord_notification(subject, body, alert))
                elif channel == 'webhook' and self.config.webhook_url:
                    tasks.append(self._send_webhook_notification(subject, body, alert))

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                self.stats['notifications_sent'] += len(tasks)

                logger.info(f"Notificación enviada para alerta {alert.id}", extra={
                    'alert_id': alert.id,
                    'channels': target_channels,
                    'severity': alert.severity
                })

        except Exception as e:
            logger.error(f"Error enviando notificación para alerta {alert.id}: {e}")

    async def _send_email_notification(self, subject: str, body: str, alert: Alert):
        """Enviar notificación por email."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.email_username
            msg['To'] = ', '.join(self.config.email_recipients)
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(self.config.email_smtp_server, self.config.email_smtp_port)
            server.starttls()
            server.login(self.config.email_username, self.config.email_password)
            text = msg.as_string()
            server.sendmail(self.config.email_username, self.config.email_recipients, text)
            server.quit()

            logger.debug(f"Email enviado a {len(self.config.email_recipients)} destinatarios")

        except Exception as e:
            logger.error(f"Error enviando email: {e}")

    async def _send_discord_notification(self, subject: str, body: str, alert: Alert):
        """Enviar notificación a Discord."""
        try:
            payload = {
                "content": f"**{subject}**\n\n{body}",
                "embeds": [{
                    "title": alert.title,
                    "description": alert.message,
                    "color": self._get_severity_color(alert.severity),
                    "fields": [
                        {"name": "Tipo", "value": alert.type, "inline": True},
                        {"name": "Severidad", "value": alert.severity.upper(), "inline": True},
                        {"name": "Fuente", "value": alert.source, "inline": True}
                    ],
                    "timestamp": alert.timestamp.isoformat()
                }]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.config.discord_webhook_url, json=payload) as response:
                    if response.status != 204:
                        logger.error(f"Error enviando a Discord: {response.status}")

        except Exception as e:
            logger.error(f"Error enviando a Discord: {e}")

    async def _send_webhook_notification(self, subject: str, body: str, alert: Alert):
        """Enviar notificación por webhook."""
        try:
            payload = {
                "alert_id": alert.id,
                "type": alert.type,
                "severity": alert.severity,
                "title": subject,
                "message": body,
                "metadata": alert.metadata,
                "timestamp": alert.timestamp.isoformat(),
                "escalated": alert.escalated
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.config.webhook_url, json=payload) as response:
                    if response.status not in [200, 201, 202]:
                        logger.error(f"Error enviando webhook: {response.status}")

        except Exception as e:
            logger.error(f"Error enviando webhook: {e}")

    def _get_severity_color(self, severity: str) -> int:
        """Obtener color para Discord basado en severidad."""
        colors = {
            'low': 0x00FF00,      # Verde
            'medium': 0xFFFF00,   # Amarillo
            'high': 0xFFA500,     # Naranja
            'critical': 0xFF0000  # Rojo
        }
        return colors.get(severity, 0x000000)

    async def _store_alert(self, alert: Alert):
        """Almacenar alerta en base de datos."""
        async with self.db_lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT INTO alerts (
                            id, type, subtype, severity, title, message, source,
                            metadata, timestamp, escalated, escalation_count, last_escalation
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        alert.id, alert.type, alert.subtype, alert.severity,
                        alert.title, alert.message, alert.source,
                        json.dumps(alert.metadata), alert.timestamp.isoformat(),
                        1 if alert.escalated else 0, alert.escalation_count,
                        alert.last_escalation.isoformat() if alert.last_escalation else None
                    ))
                    conn.commit()

            except Exception as e:
                logger.error(f"Error almacenando alerta {alert.id}: {e}")

    async def _cleanup_old_alerts(self):
        """Limpiar alertas antiguas de memoria."""
        cutoff_time = datetime.now() - timedelta(hours=24)

        # Limpiar historial
        self.alert_history = [a for a in self.alert_history if a.timestamp > cutoff_time]

        # Limpiar alertas activas antiguas
        to_remove = [aid for aid, alert in self.active_alerts.items()
                    if alert.timestamp < cutoff_time]
        for aid in to_remove:
            del self.active_alerts[aid]

    async def get_alert_history(self, hours: int = 24, alert_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtener historial de alertas."""
        async with self.db_lock:
            try:
                cutoff_time = datetime.now() - timedelta(hours=hours)

                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    if alert_type:
                        cursor.execute("""
                            SELECT * FROM alerts
                            WHERE timestamp > ? AND type = ?
                            ORDER BY timestamp DESC
                        """, (cutoff_time.isoformat(), alert_type))
                    else:
                        cursor.execute("""
                            SELECT * FROM alerts
                            WHERE timestamp > ?
                            ORDER BY timestamp DESC
                        """, (cutoff_time.isoformat(),))

                    rows = cursor.fetchall()

                    alerts = []
                    for row in rows:
                        alerts.append({
                            'id': row[0],
                            'type': row[1],
                            'subtype': row[2],
                            'severity': row[3],
                            'title': row[4],
                            'message': row[5],
                            'source': row[6],
                            'metadata': json.loads(row[7]),
                            'timestamp': row[8],
                            'escalated': bool(row[9]),
                            'escalation_count': row[10],
                            'last_escalation': row[11]
                        })

                    return alerts

            except Exception as e:
                logger.error(f"Error obteniendo historial de alertas: {e}")
                return []

    async def get_system_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del sistema de alertas."""
        return {
            'total_alerts_processed': self.stats['total_alerts'],
            'escalated_alerts': self.stats['escalated_alerts'],
            'notifications_sent': self.stats['notifications_sent'],
            'duplicates_prevented': self.stats['duplicates_prevented'],
            'active_alerts': len(self.active_alerts),
            'alert_types': list(self.alert_counts.keys()),
            'dedup_cache_size': len(self.dedup_cache),
            'db_path': str(self.db_path),
            'timestamp': datetime.now().isoformat()
        }

    async def clear_old_data(self, days: int = 30):
        """Limpiar datos antiguos de la base de datos."""
        async with self.db_lock:
            try:
                cutoff_time = datetime.now() - timedelta(days=days)

                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM alerts WHERE timestamp < ?",
                               (cutoff_time.isoformat(),))
                    deleted_count = conn.total_changes
                    conn.commit()

                logger.info(f"Datos antiguos limpiados: {deleted_count} alertas eliminadas")

            except Exception as e:
                logger.error(f"Error limpiando datos antiguos: {e}")


# Función de conveniencia
def create_centralized_alert_manager(config: AlertConfig = None) -> CentralizedAlertManager:
    """Crear instancia del gestor de alertas centralizado."""
    return CentralizedAlertManager(config)


# Ejemplo de uso
if __name__ == "__main__":
    async def demo():
        # Configuración de ejemplo
        config = AlertConfig(
            email_enabled=False,
            email_recipients=["admin@ailoos.ai"],
            discord_webhook_url="",  # Configurar URL real
            webhook_url="http://localhost:8080/webhook"
        )

        # Crear manager
        manager = CentralizedAlertManager(config)

        # Procesar algunas alertas de ejemplo
        alerts = [
            {
                'type': 'model',
                'subtype': 'accuracy_drop',
                'severity': 'medium',
                'title': 'Caída de Accuracy en Modelo de Fraude',
                'message': 'Accuracy cayó por debajo del 85%',
                'source': 'model_monitor',
                'metadata': {'model_id': 'fraud_v1', 'old_accuracy': 0.92, 'new_accuracy': 0.82}
            },
            {
                'type': 'system',
                'subtype': 'node_down',
                'severity': 'high',
                'title': 'Nodo Caído',
                'message': 'Nodo worker-03 no responde',
                'source': 'node_monitor',
                'metadata': {'node_id': 'worker-03', 'last_seen': '2024-01-01T10:00:00Z'}
            },
            {
                'type': 'security',
                'subtype': 'unauthorized_access',
                'severity': 'critical',
                'title': 'Acceso No Autorizado Detectado',
                'message': 'Intento de acceso desde IP sospechosa',
                'source': 'security_monitor',
                'metadata': {'ip': '192.168.1.100', 'attempts': 5}
            }
        ]

        for alert_data in alerts:
            alert_id = await manager.process_alert(alert_data)
            print(f"Alerta procesada: {alert_id}")

            # Esperar un poco entre alertas
            await asyncio.sleep(1)

        # Obtener estadísticas
        stats = await manager.get_system_stats()
        print(f"Estadísticas: {stats}")

        # Obtener historial
        history = await manager.get_alert_history(hours=1)
        print(f"Alertas en la última hora: {len(history)}")

    asyncio.run(demo())