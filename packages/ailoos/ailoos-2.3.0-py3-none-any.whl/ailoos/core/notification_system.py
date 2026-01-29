"""
Sistema de notificaciones integrado para AILOOS.
Gestiona notificaciones a través de múltiples canales basadas en eventos del sistema.
"""

import asyncio
import json
import smtplib
from typing import Dict, List, Any, Optional
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import aiohttp
import discord
from telegram import Bot
from telegram.error import TelegramError

from .config import get_config
from .event_system import get_event_bus, Event, EventAwareComponent
from ..utils.logging import get_logger


class NotificationChannel:
    """Clase base para canales de notificación."""

    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    async def send_notification(self, title: str, message: str, **kwargs) -> bool:
        """Enviar notificación. Override en subclases."""
        raise NotImplementedError

    def is_enabled(self) -> bool:
        """Verificar si el canal está habilitado."""
        return True


class DiscordChannel(NotificationChannel):
    """Canal de notificación para Discord."""

    def __init__(self, webhook_url: str):
        super().__init__("discord")
        self.webhook_url = webhook_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self):
        """Asegurar que hay una sesión HTTP activa."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def send_notification(self, title: str, message: str, **kwargs) -> bool:
        """Enviar notificación a Discord."""
        if not self.webhook_url:
            return False

        try:
            await self._ensure_session()

            embed = {
                "title": title,
                "description": message,
                "color": kwargs.get("color", 0x00ff00),  # Verde por defecto
                "timestamp": datetime.now().isoformat(),
                "footer": {
                    "text": "AILOOS Notification System"
                }
            }

            # Añadir campos adicionales si existen
            if kwargs.get("fields"):
                embed["fields"] = kwargs["fields"]

            payload = {
                "embeds": [embed]
            }

            async with self.session.post(self.webhook_url, json=payload) as response:
                return response.status == 204

        except Exception as e:
            self.logger.error(f"Error enviando notificación Discord: {e}")
            return False

    def is_enabled(self) -> bool:
        return bool(self.webhook_url)

    async def close(self):
        """Cerrar sesión HTTP."""
        if self.session and not self.session.closed:
            await self.session.close()


class EmailChannel(NotificationChannel):
    """Canal de notificación por email."""

    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
        super().__init__("email")
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    async def send_notification(self, title: str, message: str, **kwargs) -> bool:
        """Enviar notificación por email."""
        if not all([self.smtp_host, self.username, self.password]):
            return False

        try:
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = kwargs.get('to', self.username)  # Default to self
            msg['Subject'] = title

            # Añadir cuerpo
            body = f"{message}\n\nTimestamp: {datetime.now().isoformat()}"
            if kwargs.get('details'):
                body += f"\n\nDetails:\n{json.dumps(kwargs['details'], indent=2)}"

            msg.attach(MIMEText(body, 'plain'))

            # Enviar email
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            text = msg.as_string()
            server.sendmail(self.username, msg['To'], text)
            server.quit()

            return True

        except Exception as e:
            self.logger.error(f"Error enviando notificación email: {e}")
            return False

    def is_enabled(self) -> bool:
        return all([self.smtp_host, self.username, self.password])


class TelegramChannel(NotificationChannel):
    """Canal de notificación para Telegram."""

    def __init__(self, bot_token: str, chat_id: str):
        super().__init__("telegram")
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot: Optional[Bot] = None

    async def _ensure_bot(self):
        """Asegurar que el bot está inicializado."""
        if self.bot is None:
            self.bot = Bot(token=self.bot_token)

    async def send_notification(self, title: str, message: str, **kwargs) -> bool:
        """Enviar notificación a Telegram."""
        if not self.bot_token or not self.chat_id:
            return False

        try:
            await self._ensure_bot()

            # Formatear mensaje
            text = f"🚨 *{title}*\n\n{message}"

            if kwargs.get('details'):
                text += f"\n\n📋 Details:\n`{json.dumps(kwargs['details'], indent=2)}`"

            text += f"\n\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )

            return True

        except TelegramError as e:
            self.logger.error(f"Error enviando notificación Telegram: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error inesperado en notificación Telegram: {e}")
            return False

    def is_enabled(self) -> bool:
        return bool(self.bot_token and self.chat_id)


class NotificationManager(EventAwareComponent):
    """
    Gestor central de notificaciones.
    Escucha eventos del sistema y envía notificaciones apropiadas.
    """

    def __init__(self):
        super().__init__("notification_manager")

        self.config = get_config()
        self.channels: Dict[str, NotificationChannel] = {}

        # Configurar canales
        self._setup_channels()

        # Mapeo de tipos de eventos a configuraciones de notificación
        self.event_configs = self._setup_event_configs()

        self.logger.info("NotificationManager inicializado")

    def _setup_channels(self):
        """Configurar canales de notificación."""
        notif_config = self.config.notifications

        # Discord
        if notif_config.discord_webhook_url:
            self.channels["discord"] = DiscordChannel(notif_config.discord_webhook_url)

        # Email
        if all([notif_config.email_smtp_host, notif_config.email_username, notif_config.email_password]):
            self.channels["email"] = EmailChannel(
                notif_config.email_smtp_host,
                notif_config.email_smtp_port,
                notif_config.email_username,
                notif_config.email_password
            )

        # Telegram
        if notif_config.telegram_bot_token and notif_config.telegram_chat_id:
            self.channels["telegram"] = TelegramChannel(
                notif_config.telegram_bot_token,
                notif_config.telegram_chat_id
            )

        self.logger.info(f"Configurados {len(self.channels)} canales de notificación")

    def _setup_event_configs(self) -> Dict[str, Dict[str, Any]]:
        """Configurar cómo manejar diferentes tipos de eventos."""
        return {
            # Eventos críticos del sistema
            "system.critical": {
                "channels": ["discord", "telegram", "email"],
                "title": "🚨 CRITICAL SYSTEM ALERT",
                "color": 0xff0000,  # Rojo
                "priority": "critical"
            },
            "system.error": {
                "channels": ["discord", "telegram"],
                "title": "❌ SYSTEM ERROR",
                "color": 0xff4444,
                "priority": "high"
            },
            "system.warning": {
                "channels": ["discord"],
                "title": "⚠️ SYSTEM WARNING",
                "color": 0xffaa00,
                "priority": "medium"
            },

            # Eventos de componentes
            "component.error": {
                "channels": ["discord", "telegram"],
                "title": "🔴 COMPONENT ERROR",
                "color": 0xff4444,
                "priority": "high"
            },
            "component.degraded": {
                "channels": ["discord"],
                "title": "🟡 COMPONENT DEGRADED",
                "color": 0xffaa00,
                "priority": "medium"
            },

            # Eventos federados
            "federated.session_started": {
                "channels": ["discord"],
                "title": "🚀 FEDERATED SESSION STARTED",
                "color": 0x00ff00,
                "priority": "low"
            },
            "federated.session_completed": {
                "channels": ["discord", "telegram"],
                "title": "✅ FEDERATED SESSION COMPLETED",
                "color": 0x00aa00,
                "priority": "medium"
            },

            # Eventos de blockchain
            "blockchain.transaction": {
                "channels": ["discord"],
                "title": "💰 BLOCKCHAIN TRANSACTION",
                "color": 0x4444ff,
                "priority": "low"
            },

            # Eventos de compliance
            "compliance.violation": {
                "channels": ["discord", "telegram", "email"],
                "title": "🚫 COMPLIANCE VIOLATION",
                "color": 0xff0000,
                "priority": "critical"
            },

            # Eventos de monitoreo
            "monitoring.alert": {
                "channels": ["discord", "telegram"],
                "title": "📊 MONITORING ALERT",
                "color": 0xff6600,
                "priority": "high"
            }
        }

    async def _register_event_handlers(self):
        """Registrar handlers para eventos del sistema."""
        # Registrar handlers para todos los tipos de eventos configurados
        for event_pattern in self.event_configs.keys():
            # Crear patrón más general para matching
            base_pattern = event_pattern.split('.')[0] + '.*'
            self.register_event_handler(
                f"notification_{event_pattern}",
                [base_pattern],
                self._handle_notification_event
            )

        self.logger.info(f"Registrados handlers para {len(self.event_configs)} tipos de eventos")

    async def _handle_notification_event(self, event: Event):
        """Manejar evento de notificación."""
        try:
            # Buscar configuración para este tipo de evento
            config = None
            for pattern, event_config in self.event_configs.items():
                if self._matches_pattern(event.event_type, pattern):
                    config = event_config
                    break

            if not config:
                # Evento no configurado para notificaciones
                return

            # Preparar notificación
            title = config["title"]
            message = self._format_event_message(event)
            color = config.get("color", 0x00ff00)

            # Enviar a todos los canales configurados
            tasks = []
            for channel_name in config["channels"]:
                if channel_name in self.channels and self.channels[channel_name].is_enabled():
                    channel = self.channels[channel_name]
                    task = asyncio.create_task(
                        channel.send_notification(title, message, color=color, details=event.data)
                    )
                    tasks.append(task)

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                self.logger.info(f"Notificación enviada para evento {event.event_type} a {len(tasks)} canales")

        except Exception as e:
            self.logger.error(f"Error manejando evento de notificación: {e}")

    def _matches_pattern(self, event_type: str, pattern: str) -> bool:
        """Verificar si un tipo de evento coincide con un patrón."""
        # Implementación simple de pattern matching
        if pattern.endswith('.*'):
            base_pattern = pattern[:-2]
            return event_type.startswith(base_pattern)
        else:
            return event_type == pattern

    def _format_event_message(self, event: Event) -> str:
        """Formatear mensaje de evento para notificaciones."""
        message = f"**Tipo:** {event.event_type}\n"
        message += f"**Fuente:** {event.source}\n"
        message += f"**Timestamp:** {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Añadir datos del evento
        if event.data:
            message += "**Detalles:**\n"
            for key, value in event.data.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, indent=2)
                message += f"• **{key}:** {value}\n"

        return message

    async def send_custom_notification(self, title: str, message: str,
                                     channels: List[str] = None,
                                     **kwargs) -> bool:
        """Enviar notificación personalizada."""
        channels = channels or list(self.channels.keys())
        success = True

        tasks = []
        for channel_name in channels:
            if channel_name in self.channels and self.channels[channel_name].is_enabled():
                channel = self.channels[channel_name]
                task = asyncio.create_task(
                    channel.send_notification(title, message, **kwargs)
                )
                tasks.append(task)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success = all(not isinstance(r, Exception) for r in results)

        return success

    def get_channel_status(self) -> Dict[str, bool]:
        """Obtener estado de todos los canales."""
        return {name: channel.is_enabled() for name, channel in self.channels.items()}

    async def test_channels(self) -> Dict[str, bool]:
        """Probar todos los canales de notificación."""
        results = {}

        test_title = "🧪 TEST NOTIFICATION"
        test_message = "Esta es una notificación de prueba del sistema AILOOS."

        for name, channel in self.channels.items():
            try:
                success = await channel.send_notification(test_title, test_message)
                results[name] = success
            except Exception as e:
                self.logger.error(f"Error probando canal {name}: {e}")
                results[name] = False

        return results

    async def close(self):
        """Cerrar todos los canales."""
        for channel in self.channels.values():
            if hasattr(channel, 'close'):
                await channel.close()


# Instancia global del notification manager
_notification_manager_instance: Optional[NotificationManager] = None


def get_notification_manager() -> NotificationManager:
    """Obtener instancia global del notification manager."""
    global _notification_manager_instance

    if _notification_manager_instance is None:
        _notification_manager_instance = NotificationManager()

    return _notification_manager_instance


# Funciones de conveniencia
async def send_system_notification(title: str, message: str, **kwargs):
    """Enviar notificación del sistema."""
    manager = get_notification_manager()
    await manager.send_custom_notification(title, message, **kwargs)


async def test_notifications() -> Dict[str, bool]:
    """Probar sistema de notificaciones."""
    manager = get_notification_manager()
    return await manager.test_channels()