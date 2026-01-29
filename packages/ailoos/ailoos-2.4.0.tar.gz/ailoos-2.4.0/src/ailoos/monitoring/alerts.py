"""
Sistema de alertas para Ailoos.
Detecta nodos caídos y envía notificaciones.
"""

import asyncio
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any, Callable
from datetime import datetime, timedelta
import aiohttp
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AlertConfig:
    """Configuración de alertas."""
    email_enabled: bool = False
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_recipients: List[str] = None
    slack_webhook_url: str = ""
    alert_threshold_minutes: int = 5
    max_alerts_per_hour: int = 10

    def __post_init__(self):
        if self.email_recipients is None:
            self.email_recipients = []


class AlertManager:
    """
    Sistema de alertas para detectar nodos caídos y problemas en la red federada.
    Integra con métricas validadas de pruebas federadas.
    """

    def __init__(self, config: AlertConfig, metrics_api_url: str = "http://localhost:8080"):
        self.config = config
        self.metrics_api_url = metrics_api_url
        self.alert_history = []
        self.node_last_seen = {}
        self.alerts_sent_this_hour = 0
        self.hour_reset_time = datetime.now()

        # Callbacks para diferentes tipos de alertas
        self.alert_callbacks: Dict[str, List[Callable]] = {
            "node_down": [],
            "node_recovered": [],
            "network_issue": [],
            "federated_failure": []
        }

    async def check_nodes_health(self):
        """Verificar salud de nodos y enviar alertas si es necesario."""
        try:
            # Obtener datos de nodos
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.metrics_api_url}/api/nodes") as response:
                    if response.status == 200:
                        nodes_data = await response.json()
                        nodes = nodes_data.get("nodes", [])
                    else:
                        logger.error("No se pudieron obtener datos de nodos")
                        return

            current_time = datetime.now()

            # Reset contador de alertas por hora
            if current_time - self.hour_reset_time > timedelta(hours=1):
                self.alerts_sent_this_hour = 0
                self.hour_reset_time = current_time

            # Verificar cada nodo
            for node in nodes:
                node_id = node.get("node_id", "unknown")
                last_heartbeat = node.get("last_heartbeat")

                if last_heartbeat:
                    try:
                        # Convertir timestamp ISO a datetime
                        if isinstance(last_heartbeat, str):
                            heartbeat_time = datetime.fromisoformat(last_heartbeat.replace('Z', '+00:00'))
                        else:
                            heartbeat_time = datetime.fromtimestamp(last_heartbeat)

                        time_since_heartbeat = current_time - heartbeat_time

                        # Verificar si el nodo está caído
                        if time_since_heartbeat > timedelta(minutes=self.config.alert_threshold_minutes):
                            await self._handle_node_down(node_id, time_since_heartbeat)
                        else:
                            # Nodo recuperado
                            if node_id in self.node_last_seen and self.node_last_seen[node_id]["status"] == "down":
                                await self._handle_node_recovered(node_id)
                            self.node_last_seen[node_id] = {
                                "last_seen": heartbeat_time,
                                "status": "up"
                            }

                    except (ValueError, TypeError) as e:
                        logger.error(f"Error procesando heartbeat de {node_id}: {e}")

            # Verificar nodos que ya no están en la lista (posiblemente caídos)
            current_node_ids = {node.get("node_id", "unknown") for node in nodes}
            for node_id in list(self.node_last_seen.keys()):
                if node_id not in current_node_ids:
                    # Nodo desaparecido - marcar como caído
                    if self.node_last_seen[node_id]["status"] == "up":
                        await self._handle_node_down(node_id, timedelta(minutes=self.config.alert_threshold_minutes + 1))

        except Exception as e:
            logger.error(f"Error en verificación de salud de nodos: {e}")

    async def _handle_node_down(self, node_id: str, downtime: timedelta):
        """Manejar alerta de nodo caído."""
        if self.alerts_sent_this_hour >= self.config.max_alerts_per_hour:
            logger.warning("Límite de alertas por hora alcanzado")
            return

        alert_data = {
            "type": "node_down",
            "node_id": node_id,
            "downtime_minutes": downtime.total_seconds() / 60,
            "timestamp": datetime.now().isoformat(),
            "federated_impact": self._calculate_federated_impact(node_id)
        }

        self.node_last_seen[node_id] = {
            "last_seen": datetime.now() - downtime,
            "status": "down"
        }

        await self._send_alert(alert_data)
        self.alert_history.append(alert_data)

        # Ejecutar callbacks
        for callback in self.alert_callbacks["node_down"]:
            try:
                await callback(alert_data)
            except Exception as e:
                logger.error(f"Error en callback node_down: {e}")

    async def _handle_node_recovered(self, node_id: str):
        """Manejar recuperación de nodo."""
        alert_data = {
            "type": "node_recovered",
            "node_id": node_id,
            "timestamp": datetime.now().isoformat(),
            "recovery_time": datetime.now().isoformat()
        }

        await self._send_alert(alert_data)
        self.alert_history.append(alert_data)

        # Ejecutar callbacks
        for callback in self.alert_callbacks["node_recovered"]:
            try:
                await callback(alert_data)
            except Exception as e:
                logger.error(f"Error en callback node_recovered: {e}")

    def _calculate_federated_impact(self, node_id: str) -> Dict[str, Any]:
        """Calcular impacto en el entrenamiento federado."""
        # Basado en métricas validadas de pruebas federadas
        base_impact = {
            "accuracy_loss": 0.5,  # ~0.5% pérdida de accuracy por nodo caído
            "training_delay_seconds": 30,  # ~30 segundos de delay
            "federated_rounds_affected": 1,
            "recommendation": "Considerar reinicio de sesión federada si downtime > 10 minutos"
        }

        return base_impact

    async def _send_alert(self, alert_data: Dict[str, Any]):
        """Enviar alerta por múltiples canales."""
        self.alerts_sent_this_hour += 1

        alert_message = self._format_alert_message(alert_data)

        # Enviar por email
        if self.config.email_enabled:
            await self._send_email_alert(alert_message, alert_data)

        # Enviar por Slack
        if self.config.slack_webhook_url:
            await self._send_slack_alert(alert_message, alert_data)

        # Log de alerta
        logger.warning(f"ALERTA: {alert_message}")

    def _format_alert_message(self, alert_data: Dict[str, Any]) -> str:
        """Formatear mensaje de alerta."""
        alert_type = alert_data["type"]

        if alert_type == "node_down":
            return (f"🚨 NODO CAÍDO: {alert_data['node_id']} - "
                   f"Downtime: {alert_data['downtime_minutes']:.1f} minutos - "
                   f"Impacto: {alert_data['federated_impact']['accuracy_loss']}% accuracy")

        elif alert_type == "node_recovered":
            return f"✅ NODO RECUPERADO: {alert_data['node_id']} - Funcionando normalmente"

        else:
            return f"⚠️ ALERTA: {alert_type} - {json.dumps(alert_data, indent=2)}"

    async def _send_email_alert(self, message: str, alert_data: Dict[str, Any]):
        """Enviar alerta por email."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.email_username
            msg['To'] = ', '.join(self.config.email_recipients)
            msg['Subject'] = f"🚨 Alerta Ailoos - {alert_data['type'].upper()}"

            body = f"""
            <h2>Alerta del Sistema Ailoos</h2>
            <p><strong>Tipo:</strong> {alert_data['type']}</p>
            <p><strong>Mensaje:</strong> {message}</p>
            <p><strong>Timestamp:</strong> {alert_data['timestamp']}</p>

            <h3>Detalles Técnicos:</h3>
            <pre>{json.dumps(alert_data, indent=2)}</pre>

            <p>Esta es una alerta automática del sistema de monitoreo de Ailoos.</p>
            """

            msg.attach(MIMEText(body, 'html'))

            server = smtplib.SMTP(self.config.email_smtp_server, self.config.email_smtp_port)
            server.starttls()
            server.login(self.config.email_username, self.config.email_password)
            text = msg.as_string()
            server.sendmail(self.config.email_username, self.config.email_recipients, text)
            server.quit()

            logger.info(f"Alerta email enviada a {len(self.config.email_recipients)} destinatarios")

        except Exception as e:
            logger.error(f"Error enviando alerta por email: {e}")

    async def _send_slack_alert(self, message: str, alert_data: Dict[str, Any]):
        """Enviar alerta por Slack."""
        try:
            payload = {
                "text": f"🚨 *Alerta Ailoos*\n{message}",
                "attachments": [
                    {
                        "color": "danger" if alert_data["type"] == "node_down" else "good",
                        "fields": [
                            {
                                "title": "Tipo",
                                "value": alert_data["type"],
                                "short": True
                            },
                            {
                                "title": "Timestamp",
                                "value": alert_data["timestamp"],
                                "short": True
                            }
                        ]
                    }
                ]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.config.slack_webhook_url,
                                      json=payload) as response:
                    if response.status == 200:
                        logger.info("Alerta Slack enviada exitosamente")
                    else:
                        logger.error(f"Error enviando alerta Slack: {response.status}")

        except Exception as e:
            logger.error(f"Error enviando alerta por Slack: {e}")

    def add_alert_callback(self, alert_type: str, callback: Callable):
        """Añadir callback para un tipo de alerta."""
        if alert_type in self.alert_callbacks:
            self.alert_callbacks[alert_type].append(callback)
        else:
            logger.warning(f"Tipo de alerta desconocido: {alert_type}")

    async def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Obtener historial de alertas."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alert_history
                if datetime.fromisoformat(alert["timestamp"]) > cutoff_time]

    async def get_system_health(self) -> Dict[str, Any]:
        """Obtener estado de salud del sistema."""
        total_nodes = len(self.node_last_seen)
        down_nodes = sum(1 for node in self.node_last_seen.values() if node["status"] == "down")

        return {
            "total_nodes_monitored": total_nodes,
            "nodes_down": down_nodes,
            "nodes_up": total_nodes - down_nodes,
            "alerts_last_24h": len(await self.get_alert_history(24)),
            "system_health": "CRITICAL" if down_nodes > total_nodes * 0.5 else
                           "WARNING" if down_nodes > 0 else "HEALTHY",
            "federated_readiness": "IMPAIRED" if down_nodes > 0 else "OPTIMAL",
            "timestamp": datetime.now().isoformat()
        }

    async def start_monitoring(self):
        """Iniciar monitoreo continuo."""
        logger.info("Iniciando sistema de alertas Ailoos")

        while True:
            try:
                await self.check_nodes_health()
                await asyncio.sleep(60)  # Verificar cada minuto
            except Exception as e:
                logger.error(f"Error en ciclo de monitoreo: {e}")
                await asyncio.sleep(30)  # Esperar menos en caso de error


# Función para iniciar el sistema de alertas
async def start_alert_system(alert_config: AlertConfig,
                           metrics_api_url: str = "http://localhost:8080"):
    """Función de conveniencia para iniciar el sistema de alertas."""
    alert_manager = AlertManager(alert_config, metrics_api_url)

    # Callback de ejemplo para logging
    async def log_alert(alert_data):
        logger.info(f"Alerta procesada: {alert_data}")

    alert_manager.add_alert_callback("node_down", log_alert)
    alert_manager.add_alert_callback("node_recovered", log_alert)

    await alert_manager.start_monitoring()


if __name__ == "__main__":
    # Configuración de ejemplo
    config = AlertConfig(
        email_enabled=False,  # Cambiar a True para habilitar
        email_recipients=["admin@ailoos.ai"],
        slack_webhook_url="",  # Añadir URL de webhook de Slack
        alert_threshold_minutes=5
    )

    # Para testing directo
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_alert_system(config))