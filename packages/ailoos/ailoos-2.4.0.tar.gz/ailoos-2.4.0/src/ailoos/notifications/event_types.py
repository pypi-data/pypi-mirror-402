"""
Tipos de eventos para notificaciones WebSocket en AILOOS
=======================================================

Este módulo define los tipos de eventos disponibles para notificaciones
en tiempo real a través de WebSocket.
"""

from enum import Enum
from typing import Dict, Any, List
from dataclasses import dataclass


class NotificationEventType(Enum):
    """Tipos de eventos de notificación disponibles."""

    # Eventos de IA y chat
    AI_RESPONSE = "ai_response"
    AI_ERROR = "ai_error"
    CHAT_MESSAGE = "chat_message"
    CONVERSATION_START = "conversation_start"
    CONVERSATION_END = "conversation_end"

    # Eventos de tareas
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_PROGRESS = "task_progress"
    TASK_ASSIGNED = "task_assigned"
    TASK_CANCELLED = "task_cancelled"

    # Eventos de sesiones federadas
    SESSION_UPDATE = "session_update"
    SESSION_START = "session_start"
    SESSION_COMPLETE = "session_complete"
    SESSION_ERROR = "session_error"
    SESSION_PARTICIPANT_JOIN = "session_participant_join"
    SESSION_PARTICIPANT_LEAVE = "session_participant_leave"

    # Eventos de entrenamiento
    TRAINING_ROUND_START = "training_round_start"
    TRAINING_ROUND_COMPLETE = "training_round_complete"
    TRAINING_METRICS = "training_metrics"
    TRAINING_PROGRESS = "training_progress"
    TRAINING_ERROR = "training_error"

    # Eventos de nodos
    NODE_STATUS = "node_status"
    NODE_CONNECT = "node_connect"
    NODE_DISCONNECT = "node_disconnect"
    NODE_HEARTBEAT = "node_heartbeat"

    # Eventos de recompensas
    REWARD_EARNED = "reward_earned"
    REWARD_DISTRIBUTED = "reward_distributed"
    REWARD_CLAIMED = "reward_claimed"
    REWARD_FAILED = "reward_failed"

    # Eventos del marketplace
    MARKETPLACE_UPDATE = "marketplace_update"
    DATA_LISTING_CREATED = "data_listing_created"
    DATA_LISTING_SOLD = "data_listing_sold"
    DATA_PURCHASED = "data_purchased"

    # Eventos del sistema
    SYSTEM_ALERT = "system_alert"
    SYSTEM_MAINTENANCE = "system_maintenance"
    SYSTEM_UPDATE = "system_update"
    SYSTEM_ERROR = "system_error"

    # Eventos de seguridad
    SECURITY_ALERT = "security_alert"
    LOGIN_ATTEMPT = "login_attempt"
    PASSWORD_CHANGE = "password_change"

    # Eventos de configuración
    SETTINGS_UPDATE = "settings_update"
    PREFERENCES_UPDATE = "preferences_update"


@dataclass
class NotificationEvent:
    """Representa un evento de notificación."""

    type: NotificationEventType
    title: str
    message: str
    data: Dict[str, Any]
    priority: str = "normal"  # "low", "normal", "high", "urgent"
    user_id: int = None
    room: str = None
    persistent: bool = True  # Si debe guardarse en la base de datos

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el evento a diccionario."""
        return {
            "type": self.type.value,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "priority": self.priority,
            "user_id": self.user_id,
            "room": self.room,
            "persistent": self.persistent
        }


class NotificationEventFactory:
    """Fábrica para crear eventos de notificación comunes."""

    @staticmethod
    def ai_response(user_id: int, response_text: str, conversation_id: str = None) -> NotificationEvent:
        """Crea un evento de respuesta de IA."""
        return NotificationEvent(
            type=NotificationEventType.AI_RESPONSE,
            title="Respuesta de IA",
            message=f"Nueva respuesta disponible",
            data={
                "response_text": response_text[:100] + "..." if len(response_text) > 100 else response_text,
                "conversation_id": conversation_id,
                "full_response": response_text
            },
            user_id=user_id,
            priority="normal"
        )

    @staticmethod
    def task_completed(user_id: int, task_name: str, task_id: str) -> NotificationEvent:
        """Crea un evento de tarea completada."""
        return NotificationEvent(
            type=NotificationEventType.TASK_COMPLETED,
            title="Tarea Completada",
            message=f"La tarea '{task_name}' se ha completado exitosamente",
            data={"task_id": task_id, "task_name": task_name},
            user_id=user_id,
            priority="normal"
        )

    @staticmethod
    def session_update(session_id: str, update_type: str, data: Dict[str, Any]) -> NotificationEvent:
        """Crea un evento de actualización de sesión."""
        return NotificationEvent(
            type=NotificationEventType.SESSION_UPDATE,
            title="Actualización de Sesión",
            message=f"Sesión {session_id}: {update_type}",
            data={"session_id": session_id, "update_type": update_type, **data},
            room=f"session_{session_id}",
            priority="normal"
        )

    @staticmethod
    def training_progress(session_id: str, round_number: int, progress: float) -> NotificationEvent:
        """Crea un evento de progreso de entrenamiento."""
        return NotificationEvent(
            type=NotificationEventType.TRAINING_PROGRESS,
            title="Progreso de Entrenamiento",
            message=f"Ronda {round_number}: {progress:.1f}% completado",
            data={"session_id": session_id, "round_number": round_number, "progress": progress},
            room=f"session_{session_id}",
            priority="low"
        )

    @staticmethod
    def reward_earned(user_id: int, amount: float, reason: str) -> NotificationEvent:
        """Crea un evento de recompensa ganada."""
        return NotificationEvent(
            type=NotificationEventType.REWARD_EARNED,
            title="¡Recompensa Ganada!",
            message=f"Has ganado {amount:.2f} DracmaS por {reason}",
            data={"amount": amount, "reason": reason},
            user_id=user_id,
            priority="high"
        )

    @staticmethod
    def system_alert(alert_type: str, message: str, data: Dict[str, Any] = None) -> NotificationEvent:
        """Crea un evento de alerta del sistema."""
        priority = "high" if alert_type in ["error", "critical"] else "normal"
        return NotificationEvent(
            type=NotificationEventType.SYSTEM_ALERT,
            title="Alerta del Sistema",
            message=message,
            data=data or {"alert_type": alert_type},
            priority=priority,
            persistent=True
        )

    @staticmethod
    def node_status(node_id: str, status: str, data: Dict[str, Any] = None) -> NotificationEvent:
        """Crea un evento de cambio de estado de nodo."""
        return NotificationEvent(
            type=NotificationEventType.NODE_STATUS,
            title="Estado de Nodo",
            message=f"Nodo {node_id}: {status}",
            data={"node_id": node_id, "status": status, **(data or {})},
            room=f"node_{node_id}",
            priority="normal"
        )


# Mapeo de eventos a suscripciones por defecto
DEFAULT_EVENT_SUBSCRIPTIONS = {
    "ai_response": True,
    "task_completed": True,
    "session_update": True,
    "training_progress": False,  # Opcional por defecto
    "system_alert": True,
    "reward_earned": True,
    "node_status": False,  # Solo para administradores
    "marketplace_update": False,
    "security_alert": True
}

# Configuración de prioridades por tipo de evento
EVENT_PRIORITIES = {
    NotificationEventType.AI_RESPONSE: "normal",
    NotificationEventType.TASK_COMPLETED: "normal",
    NotificationEventType.SESSION_UPDATE: "normal",
    NotificationEventType.TRAINING_PROGRESS: "low",
    NotificationEventType.REWARD_EARNED: "high",
    NotificationEventType.SYSTEM_ALERT: "high",
    NotificationEventType.SECURITY_ALERT: "urgent",
    NotificationEventType.SYSTEM_ERROR: "urgent",
    NotificationEventType.NODE_DISCONNECT: "high"
}

# Eventos que requieren persistencia
PERSISTENT_EVENTS = {
    NotificationEventType.AI_RESPONSE,
    NotificationEventType.TASK_COMPLETED,
    NotificationEventType.REWARD_EARNED,
    NotificationEventType.SYSTEM_ALERT,
    NotificationEventType.SECURITY_ALERT,
    NotificationEventType.SYSTEM_ERROR
}