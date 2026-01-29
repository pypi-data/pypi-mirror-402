"""
Sistema de notificaciones push/email para AILOOS
===============================================

Este módulo proporciona un sistema completo de notificaciones que incluye:

- Envío de notificaciones push al navegador
- Envío de emails con plantillas HTML
- Sistema de colas de envío asíncrono
- Gestión de preferencias de usuario
- Plantillas de notificación reutilizables
- Integración con el servicio de configuraciones

Uso básico:
    from src.ailoos.notifications import NotificationService, NotificationType, NotificationPriority

    # Crear servicio
    service = NotificationService(settings_service)

    # Crear notificación simple
    notification = service.create_notification(
        user_id=123,
        title="¡Hola!",
        body="Tienes una nueva notificación",
        notification_type=NotificationType.BOTH
    )

    # Enviar inmediatamente
    await service.send_notification(notification)

    # O crear desde plantilla
    notification = service.create_from_template(
        user_id=123,
        template_name="welcome",
        variables={"user_name": "Juan"}
    )

    # Enviar múltiples notificaciones
    results = await service.send_bulk_notifications([notification1, notification2])
"""

from .models import (
    Notification,
    NotificationTemplate,
    NotificationType,
    NotificationPriority,
    NotificationStatus,
    UserNotificationPreferences,
    QueueItem
)

from .service import (
    NotificationService,
    NotificationServiceError,
    EmailProviderError,
    PushProviderError
)

from .templates import notification_templates

from .queue import NotificationQueue, AsyncNotificationQueue

from .event_types import (
    NotificationEventType, NotificationEvent, NotificationEventFactory,
    DEFAULT_EVENT_SUBSCRIPTIONS, EVENT_PRIORITIES, PERSISTENT_EVENTS
)

__all__ = [
    # Modelos
    'Notification',
    'NotificationTemplate',
    'NotificationType',
    'NotificationPriority',
    'NotificationStatus',
    'UserNotificationPreferences',
    'QueueItem',

    # Servicio
    'NotificationService',
    'NotificationServiceError',
    'EmailProviderError',
    'PushProviderError',

    # Plantillas
    'notification_templates',

    # Colas
    'NotificationQueue',
    'AsyncNotificationQueue',

    # Tipos de eventos
    'NotificationEventType',
    'NotificationEvent',
    'NotificationEventFactory',
    'DEFAULT_EVENT_SUBSCRIPTIONS',
    'EVENT_PRIORITIES',
    'PERSISTENT_EVENTS'
]

# Información de versión
__version__ = "1.0.0"
__author__ = "AILOOS Team"
__description__ = "Sistema de notificaciones push/email para AILOOS"