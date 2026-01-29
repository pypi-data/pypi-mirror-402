"""
Modelos de datos para el sistema de notificaciones de AILOOS
========================================================

Este módulo define los modelos de datos para notificaciones push, emails,
plantillas y elementos de cola de envío.
"""

from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class NotificationType(Enum):
    """Tipos de notificaciones disponibles."""
    PUSH = "push"
    EMAIL = "email"
    BOTH = "both"
    WEBSOCKET = "websocket"
    REALTIME = "realtime"  # Combinación de push + websocket
    DISCORD = "discord"    # Notificaciones a Discord
    WEBHOOK = "webhook"    # Notificaciones vía webhooks externos


class NotificationPriority(Enum):
    """Prioridades de notificación."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationStatus(Enum):
    """Estados de una notificación."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"
    DELIVERED = "delivered"  # Para WebSocket - mensaje entregado
    READ = "read"  # Para WebSocket - mensaje leído por el usuario


class WebSocketEventType(Enum):
    """Tipos de eventos WebSocket para notificaciones."""
    AI_RESPONSE = "ai_response"
    TASK_COMPLETED = "task_completed"
    SESSION_UPDATE = "session_update"
    TRAINING_PROGRESS = "training_progress"
    SYSTEM_ALERT = "system_alert"
    USER_MESSAGE = "user_message"
    NODE_STATUS = "node_status"
    REWARD_EARNED = "reward_earned"
    MARKETPLACE_UPDATE = "marketplace_update"
    FEDERATED_EVENT = "federated_event"


@dataclass
class NotificationTemplate:
    """Plantilla de notificación reutilizable."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: NotificationType = NotificationType.BOTH
    subject: str = ""  # Para emails
    title: str = ""    # Para push notifications
    body: str = ""
    html_body: Optional[str] = None  # Para emails HTML
    variables: List[str] = field(default_factory=list)  # Variables disponibles
    websocket_event: Optional[WebSocketEventType] = None  # Evento WebSocket asociado
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la plantilla a diccionario."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'subject': self.subject,
            'title': self.title,
            'body': self.body,
            'html_body': self.html_body,
            'variables': self.variables,
            'websocket_event': self.websocket_event.value if self.websocket_event else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NotificationTemplate':
        """Crea una plantilla desde un diccionario."""
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', ''),
            type=NotificationType(data.get('type', 'both')),
            subject=data.get('subject', ''),
            title=data.get('title', ''),
            body=data.get('body', ''),
            html_body=data.get('html_body'),
            variables=data.get('variables', []),
            websocket_event=WebSocketEventType(data['websocket_event']) if data.get('websocket_event') else None,
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if 'updated_at' in data else datetime.now()
        )


@dataclass
class Notification:
    """Notificación individual."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int = 0
    type: NotificationType = NotificationType.PUSH
    priority: NotificationPriority = NotificationPriority.NORMAL
    template_id: Optional[str] = None
    subject: Optional[str] = None  # Para emails
    title: str = ""  # Para push notifications
    body: str = ""
    html_body: Optional[str] = None  # Para emails HTML
    data: Dict[str, Any] = field(default_factory=dict)  # Datos adicionales
    status: NotificationStatus = NotificationStatus.PENDING
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None  # Para WebSocket - cuando se entrega
    read_at: Optional[datetime] = None  # Para WebSocket - cuando se lee
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None  # Para envío programado
    websocket_event: Optional[str] = None  # Tipo de evento WebSocket
    websocket_room: Optional[str] = None  # Sala WebSocket de destino

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la notificación a diccionario."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type.value,
            'priority': self.priority.value,
            'template_id': self.template_id,
            'subject': self.subject,
            'title': self.title,
            'body': self.body,
            'html_body': self.html_body,
            'data': self.data,
            'status': self.status.value,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'created_at': self.created_at.isoformat(),
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'websocket_event': self.websocket_event,
            'websocket_room': self.websocket_room
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Notification':
        """Crea una notificación desde un diccionario."""
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            user_id=data.get('user_id', 0),
            type=NotificationType(data.get('type', 'push')),
            priority=NotificationPriority(data.get('priority', 'normal')),
            template_id=data.get('template_id'),
            subject=data.get('subject'),
            title=data.get('title', ''),
            body=data.get('body', ''),
            html_body=data.get('html_body'),
            data=data.get('data', {}),
            status=NotificationStatus(data.get('status', 'pending')),
            sent_at=datetime.fromisoformat(data['sent_at']) if data.get('sent_at') else None,
            delivered_at=datetime.fromisoformat(data['delivered_at']) if data.get('delivered_at') else None,
            read_at=datetime.fromisoformat(data['read_at']) if data.get('read_at') else None,
            error_message=data.get('error_message'),
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now(),
            scheduled_at=datetime.fromisoformat(data['scheduled_at']) if data.get('scheduled_at') else None,
            websocket_event=data.get('websocket_event'),
            websocket_room=data.get('websocket_room')
        )

    def mark_as_sent(self):
        """Marca la notificación como enviada."""
        self.status = NotificationStatus.SENT
        self.sent_at = datetime.now()
        self.error_message = None

    def mark_as_delivered(self):
        """Marca la notificación como entregada (para WebSocket)."""
        self.status = NotificationStatus.DELIVERED
        self.delivered_at = datetime.now()

    def mark_as_read(self):
        """Marca la notificación como leída (para WebSocket)."""
        self.status = NotificationStatus.READ
        self.read_at = datetime.now()

    def can_retry(self) -> bool:
        """Verifica si la notificación puede reintentarse."""
        return self.retry_count < self.max_retries

    def is_expired(self) -> bool:
        """Verifica si la notificación ha expirado."""
        if not self.scheduled_at:
            return False
        return datetime.now() > self.scheduled_at


@dataclass
class QueueItem:
    """Elemento en la cola de envío."""

    notification_id: str
    priority: NotificationPriority
    scheduled_at: Optional[datetime] = None
    added_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el elemento de cola a diccionario."""
        return {
            'notification_id': self.notification_id,
            'priority': self.priority.value,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'added_at': self.added_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueueItem':
        """Crea un elemento de cola desde un diccionario."""
        return cls(
            notification_id=data['notification_id'],
            priority=NotificationPriority(data['priority']),
            scheduled_at=datetime.fromisoformat(data['scheduled_at']) if data.get('scheduled_at') else None,
            added_at=datetime.fromisoformat(data['added_at']) if 'added_at' in data else datetime.now()
        )


@dataclass
class UserNotificationPreferences:
    """Preferencias de notificación de un usuario."""

    user_id: int
    email_enabled: bool = True
    push_enabled: bool = True
    websocket_enabled: bool = True  # Habilitar notificaciones WebSocket
    realtime_enabled: bool = True   # Habilitar notificaciones en tiempo real
    email_address: Optional[str] = None
    push_token: Optional[str] = None  # Token FCM/APNs
    websocket_subscriptions: List[str] = field(default_factory=list)  # Eventos WebSocket suscritos
    quiet_hours_start: Optional[str] = None  # HH:MM
    quiet_hours_end: Optional[str] = None    # HH:MM
    timezone: str = "Europe/Madrid"

    def to_dict(self) -> Dict[str, Any]:
        """Convierte las preferencias a diccionario."""
        return {
            'user_id': self.user_id,
            'email_enabled': self.email_enabled,
            'push_enabled': self.push_enabled,
            'websocket_enabled': self.websocket_enabled,
            'realtime_enabled': self.realtime_enabled,
            'email_address': self.email_address,
            'push_token': self.push_token,
            'websocket_subscriptions': self.websocket_subscriptions,
            'quiet_hours_start': self.quiet_hours_start,
            'quiet_hours_end': self.quiet_hours_end,
            'timezone': self.timezone
        }

    def is_in_quiet_hours(self, current_time: datetime) -> bool:
        """Verifica si la hora actual está en horas de silencio."""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False

        try:
            start = datetime.strptime(self.quiet_hours_start, "%H:%M").time()
            end = datetime.strptime(self.quiet_hours_end, "%H:%M").time()
            current = current_time.time()

            if start <= end:
                return start <= current <= end
            else:  # Cruza medianoche
                return current >= start or current <= end
        except ValueError:
            return False

    def is_subscribed_to_websocket_event(self, event_type: str) -> bool:
        """Verifica si el usuario está suscrito a un evento WebSocket."""
        return event_type in self.websocket_subscriptions or "*" in self.websocket_subscriptions

    def subscribe_to_websocket_event(self, event_type: str):
        """Suscribe al usuario a un evento WebSocket."""
        if event_type not in self.websocket_subscriptions:
            self.websocket_subscriptions.append(event_type)

    def unsubscribe_from_websocket_event(self, event_type: str):
        """Desuscribe al usuario de un evento WebSocket."""
        if event_type in self.websocket_subscriptions:
            self.websocket_subscriptions.remove(event_type)


# Modelos para integraciones con Discord y Webhooks

@dataclass
class DiscordIntegration:
    """Configuración de integración con Discord."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""  # Nombre descriptivo de la integración
    bot_token: str = ""  # Token del bot de Discord
    server_id: str = ""  # ID del servidor (guild)
    channel_id: str = ""  # ID del canal por defecto
    webhook_url: Optional[str] = None  # URL del webhook (alternativa al bot)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la integración a diccionario."""
        return {
            'id': self.id,
            'name': self.name,
            'bot_token': self.bot_token,
            'server_id': self.server_id,
            'channel_id': self.channel_id,
            'webhook_url': self.webhook_url,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DiscordIntegration':
        """Crea una integración desde un diccionario."""
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', ''),
            bot_token=data.get('bot_token', ''),
            server_id=data.get('server_id', ''),
            channel_id=data.get('channel_id', ''),
            webhook_url=data.get('webhook_url'),
            enabled=data.get('enabled', True),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if 'updated_at' in data else datetime.now()
        )


@dataclass
class WebhookIntegration:
    """Configuración de webhook externo."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""  # Nombre descriptivo del webhook
    url: str = ""  # URL del endpoint del webhook
    method: str = "POST"  # Método HTTP (POST, PUT, etc.)
    headers: Dict[str, str] = field(default_factory=dict)  # Headers personalizados
    secret: Optional[str] = None  # Secret para firma HMAC
    enabled: bool = True
    retry_count: int = 3  # Número de reintentos
    timeout: int = 30  # Timeout en segundos
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el webhook a diccionario."""
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'method': self.method,
            'headers': self.headers,
            'secret': self.secret,
            'enabled': self.enabled,
            'retry_count': self.retry_count,
            'timeout': self.timeout,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebhookIntegration':
        """Crea un webhook desde un diccionario."""
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', ''),
            url=data.get('url', ''),
            method=data.get('method', 'POST'),
            headers=data.get('headers', {}),
            secret=data.get('secret'),
            enabled=data.get('enabled', True),
            retry_count=data.get('retry_count', 3),
            timeout=data.get('timeout', 30),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if 'updated_at' in data else datetime.now()
        )


@dataclass
class DiscordMessage:
    """Mensaje para enviar a Discord."""

    content: str = ""  # Contenido del mensaje
    embeds: List[Dict[str, Any]] = field(default_factory=list)  # Embeds de Discord
    username: Optional[str] = None  # Nombre del usuario/bot
    avatar_url: Optional[str] = None  # URL del avatar
    tts: bool = False  # Text-to-speech

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el mensaje a formato Discord."""
        data = {
            'content': self.content,
            'tts': self.tts
        }
        if self.embeds:
            data['embeds'] = self.embeds
        if self.username:
            data['username'] = self.username
        if self.avatar_url:
            data['avatar_url'] = self.avatar_url
        return data


@dataclass
class WebhookPayload:
    """Payload para webhook externo."""

    event_type: str  # Tipo de evento
    data: Dict[str, Any]  # Datos del evento
    timestamp: datetime = field(default_factory=datetime.now)
    signature: Optional[str] = None  # Firma HMAC si se configura

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el payload a diccionario."""
        return {
            'event_type': self.event_type,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'signature': self.signature
        }