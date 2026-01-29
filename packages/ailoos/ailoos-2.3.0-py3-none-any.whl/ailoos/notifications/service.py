"""
Servicio de notificaciones para AILOOS
====================================

Este módulo implementa el servicio principal de notificaciones,
incluyendo envío push, emails y gestión de preferencias de usuario.
"""

import logging
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json
import requests

from .models import (
    Notification, NotificationTemplate, NotificationType, NotificationPriority,
    NotificationStatus, UserNotificationPreferences, WebSocketEventType
)
from .templates import notification_templates
from .queue import NotificationQueue, AsyncNotificationQueue
from .validators import validate_notification, validate_user_preferences, ValidationError
from ..settings.service import SettingsService


logger = logging.getLogger(__name__)


class NotificationServiceError(Exception):
    """Excepción base para errores del servicio de notificaciones."""
    pass


class EmailProviderError(NotificationServiceError):
    """Error en el proveedor de email."""
    pass


class PushProviderError(NotificationServiceError):
    """Error en el proveedor de push notifications."""
    pass


class NotificationService:
    """
    Servicio principal para gestión de notificaciones.

    Proporciona funcionalidades para enviar notificaciones push y email,
    gestionar plantillas, colas de envío y preferencias de usuario.
    """

    def __init__(self,
                 settings_service: SettingsService,
                 smtp_config: Optional[Dict[str, Any]] = None,
                 push_config: Optional[Dict[str, Any]] = None,
                 websocket_manager = None,
                 use_async_queue: bool = False):
        """
        Inicializa el servicio de notificaciones.

        Args:
            settings_service: Servicio de configuraciones para acceder a preferencias
            smtp_config: Configuración SMTP para emails
            push_config: Configuración para push notifications (FCM/APNs)
            websocket_manager: Gestor de conexiones WebSocket
            use_async_queue: Si usar cola asíncrona en lugar de threading
        """
        self.settings_service = settings_service
        self.smtp_config = smtp_config or {}
        self.push_config = push_config or {}
        self.websocket_manager = websocket_manager
        self.use_async_queue = use_async_queue

        # Configurar cola de envío
        if use_async_queue:
            self.queue = AsyncNotificationQueue(max_workers=4, batch_size=10)
        else:
            self.queue = NotificationQueue(max_workers=4, batch_size=10)

        # Configurar callback de envío
        if use_async_queue:
            # Para async, necesitamos una corrutina
            self.queue.set_send_callback(self.send_notification)
        else:
            self.queue.set_send_callback(self._send_notification_sync)

        # Cache de preferencias de usuario
        self._preferences_cache: Dict[int, UserNotificationPreferences] = {}
        self._cache_ttl = 300  # 5 minutos

        logger.info("Servicio de notificaciones inicializado")

    async def start_queue(self):
        """Inicia la cola de procesamiento de notificaciones."""
        if self.use_async_queue:
            await self.queue.start()
        else:
            self.queue.start()

    async def stop_queue(self):
        """Detiene la cola de procesamiento."""
        if self.use_async_queue:
            await self.queue.stop()
        else:
            self.queue.stop()

    def create_notification(self,
                           user_id: int,
                           title: str,
                           body: str,
                           notification_type: NotificationType = NotificationType.PUSH,
                           priority: NotificationPriority = NotificationPriority.NORMAL,
                           template_id: Optional[str] = None,
                           subject: Optional[str] = None,
                           html_body: Optional[str] = None,
                           data: Optional[Dict[str, Any]] = None,
                           scheduled_at: Optional[datetime] = None,
                           websocket_event: Optional[str] = None,
                           websocket_room: Optional[str] = None,
                           validate: bool = True) -> Notification:
        """
        Crea una nueva notificación.

        Args:
            user_id: ID del usuario destinatario
            title: Título de la notificación
            body: Cuerpo de la notificación
            notification_type: Tipo de notificación
            priority: Prioridad de envío
            template_id: ID de plantilla utilizada
            subject: Asunto (para emails)
            html_body: Cuerpo HTML (para emails)
            data: Datos adicionales
            scheduled_at: Fecha de envío programado
            websocket_event: Tipo de evento WebSocket
            websocket_room: Sala WebSocket de destino
            validate: Si validar la notificación antes de crear

        Returns:
            Notification: Notificación creada

        Raises:
            ValidationError: Si la validación falla
        """
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            priority=priority,
            template_id=template_id,
            subject=subject,
            title=title,
            body=body,
            html_body=html_body,
            data=data or {},
            scheduled_at=scheduled_at,
            websocket_event=websocket_event,
            websocket_room=websocket_room
        )

        # Validar si se solicita
        if validate:
            errors = validate_notification(notification)
            if errors:
                raise ValidationError(f"Errores de validación en notificación: {errors}")

        logger.info(f"Notificación creada: {notification.id} para usuario {user_id}")
        return notification

    def create_from_template(self,
                           user_id: int,
                           template_name: str,
                           variables: Dict[str, Any],
                           priority: NotificationPriority = NotificationPriority.NORMAL,
                           scheduled_at: Optional[datetime] = None) -> Notification:
        """
        Crea una notificación desde una plantilla.

        Args:
            user_id: ID del usuario destinatario
            template_name: Nombre de la plantilla
            variables: Variables para reemplazar en la plantilla
            priority: Prioridad de envío
            scheduled_at: Fecha de envío programado

        Returns:
            Notification: Notificación creada desde plantilla
        """
        # Renderizar plantilla
        rendered_template = notification_templates.render_template(template_name, variables)

        # Crear notificación
        notification = Notification(
            user_id=user_id,
            type=rendered_template.type,
            priority=priority,
            template_id=rendered_template.id,
            subject=rendered_template.subject,
            title=rendered_template.title,
            body=rendered_template.body,
            html_body=rendered_template.html_body,
            data=variables.copy(),
            scheduled_at=scheduled_at
        )

        logger.info(f"Notificación creada desde plantilla '{template_name}' para usuario {user_id}")
        return notification

    async def send_notification(self, notification: Notification) -> bool:
        """
        Envía una notificación inmediatamente.

        Args:
            notification: Notificación a enviar

        Returns:
            bool: True si se envió exitosamente
        """
        try:
            # Verificar preferencias del usuario
            if not await self._check_user_preferences(notification):
                logger.info(f"Notificación {notification.id} bloqueada por preferencias de usuario")
                notification.status = NotificationStatus.CANCELLED
                return False

            success_overall = True

            # Enviar según tipo
            if notification.type in [NotificationType.PUSH, NotificationType.BOTH, NotificationType.REALTIME]:
                success_push = await self._send_push_notification(notification)
                if not success_push and notification.type == NotificationType.PUSH:
                    notification.mark_as_failed("Error enviando push notification")
                    return False
                success_overall = success_overall and success_push

            if notification.type in [NotificationType.EMAIL, NotificationType.BOTH]:
                success_email = await self._send_email_notification(notification)
                if not success_email and notification.type == NotificationType.EMAIL:
                    notification.mark_as_failed("Error enviando email")
                    return False
                success_overall = success_overall and success_email

            if notification.type in [NotificationType.WEBSOCKET, NotificationType.REALTIME]:
                success_websocket = await self._send_websocket_notification(notification)
                if not success_websocket and notification.type == NotificationType.WEBSOCKET:
                    notification.mark_as_failed("Error enviando notificación WebSocket")
                    return False
                success_overall = success_overall and success_websocket

            # Marcar como enviada
            notification.mark_as_sent()
            logger.info(f"Notificación {notification.id} enviada exitosamente")
            return success_overall

        except Exception as e:
            logger.error(f"Error enviando notificación {notification.id}: {e}")
            notification.mark_as_failed(str(e))
            return False

    async def queue_notification(self, notification: Notification) -> bool:
        """
        Agrega una notificación a la cola de envío.

        Args:
            notification: Notificación a encolar

        Returns:
            bool: True si se agregó a la cola
        """
        if self.use_async_queue:
            return await self.queue.enqueue(notification)
        else:
            return self.queue.enqueue(notification)

    async def send_bulk_notifications(self, notifications: List[Notification]) -> Dict[str, int]:
        """
        Envía múltiples notificaciones.

        Args:
            notifications: Lista de notificaciones

        Returns:
            Dict[str, int]: Estadísticas de envío (sent, failed, queued)
        """
        results = {'sent': 0, 'failed': 0, 'queued': 0}

        for notification in notifications:
            try:
                # Intentar envío inmediato para notificaciones de alta prioridad
                if notification.priority in [NotificationPriority.URGENT, NotificationPriority.HIGH]:
                    if await self.send_notification(notification):
                        results['sent'] += 1
                    else:
                        results['failed'] += 1
                else:
                    # Encolar para procesamiento posterior
                    if await self.queue_notification(notification):
                        results['queued'] += 1
                    else:
                        results['failed'] += 1

            except Exception as e:
                logger.error(f"Error procesando notificación {notification.id}: {e}")
                results['failed'] += 1

        return results

    async def get_user_preferences(self, user_id: int) -> UserNotificationPreferences:
        """
        Obtiene las preferencias de notificación de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            UserNotificationPreferences: Preferencias del usuario
        """
        # Verificar cache
        if user_id in self._preferences_cache:
            cached_prefs = self._preferences_cache[user_id]
            # Verificar TTL
            if (datetime.now() - cached_prefs._cache_time).seconds < self._cache_ttl:
                return cached_prefs

        try:
            # Obtener configuraciones del usuario
            settings = self.settings_service.get_user_settings(user_id)

            # Crear preferencias desde configuraciones
            preferences = UserNotificationPreferences(
                user_id=user_id,
                email_enabled=settings.notifications.responses_email or settings.notifications.tasks_email,
                push_enabled=settings.notifications.responses_app or settings.notifications.tasks_app,
                websocket_enabled=True,  # Por defecto habilitado
                realtime_enabled=True,   # Por defecto habilitado
                email_address=settings.account.email,
                websocket_subscriptions=["ai_response", "task_completed", "system_alert"]  # Eventos por defecto
            )

            # Agregar timestamp de cache
            preferences._cache_time = datetime.now()

            # Cachear
            self._preferences_cache[user_id] = preferences

            return preferences

        except Exception as e:
            logger.error(f"Error obteniendo preferencias para usuario {user_id}: {e}")
            # Retornar preferencias por defecto
            return UserNotificationPreferences(user_id=user_id)

    async def update_user_preferences(self,
                                     user_id: int,
                                     email_enabled: Optional[bool] = None,
                                     push_enabled: Optional[bool] = None,
                                     websocket_enabled: Optional[bool] = None,
                                     realtime_enabled: Optional[bool] = None,
                                     email_address: Optional[str] = None,
                                     push_token: Optional[str] = None,
                                     websocket_subscriptions: Optional[List[str]] = None,
                                     validate: bool = True) -> UserNotificationPreferences:
        """
        Actualiza las preferencias de notificación de un usuario.

        Args:
            user_id: ID del usuario
            email_enabled: Si habilitar emails
            push_enabled: Si habilitar push notifications
            websocket_enabled: Si habilitar notificaciones WebSocket
            realtime_enabled: Si habilitar notificaciones en tiempo real
            email_address: Dirección de email
            push_token: Token FCM/APNs
            websocket_subscriptions: Lista de eventos WebSocket suscritos
            validate: Si validar las preferencias

        Returns:
            UserNotificationPreferences: Preferencias actualizadas

        Raises:
            ValidationError: Si la validación falla
        """
        try:
            # Obtener preferencias actuales
            preferences = await self.get_user_preferences(user_id)

            # Actualizar campos
            if email_enabled is not None:
                preferences.email_enabled = email_enabled
            if push_enabled is not None:
                preferences.push_enabled = push_enabled
            if websocket_enabled is not None:
                preferences.websocket_enabled = websocket_enabled
            if realtime_enabled is not None:
                preferences.realtime_enabled = realtime_enabled
            if email_address is not None:
                preferences.email_address = email_address
            if push_token is not None:
                preferences.push_token = push_token
            if websocket_subscriptions is not None:
                preferences.websocket_subscriptions = websocket_subscriptions

            # Validar si se solicita
            if validate:
                errors = validate_user_preferences(preferences)
                if errors:
                    raise ValidationError(f"Errores de validación en preferencias: {errors}")

            # Actualizar cache
            preferences._cache_time = datetime.now()
            self._preferences_cache[user_id] = preferences

            # Actualizar configuraciones del usuario si es necesario
            # (Aquí podríamos mapear de vuelta a las configuraciones de AILOOS)

            logger.info(f"Preferencias actualizadas para usuario {user_id}")
            return preferences

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error actualizando preferencias para usuario {user_id}: {e}")
            raise NotificationServiceError(f"Error actualizando preferencias: {e}")

    async def _check_user_preferences(self, notification: Notification) -> bool:
        """
        Verifica si una notificación puede enviarse según las preferencias del usuario.

        Args:
            notification: Notificación a verificar

        Returns:
            bool: True si puede enviarse
        """
        try:
            preferences = await self.get_user_preferences(notification.user_id)

            # Verificar horas de silencio
            if preferences.is_in_quiet_hours(datetime.now()):
                return False

            # Verificar tipo de notificación
            if notification.type == NotificationType.PUSH and not preferences.push_enabled:
                return False
            if notification.type == NotificationType.EMAIL and not preferences.email_enabled:
                return False
            if notification.type == NotificationType.WEBSOCKET and not preferences.websocket_enabled:
                return False
            if notification.type == NotificationType.REALTIME and not preferences.realtime_enabled:
                return False
            if notification.type == NotificationType.BOTH and not (preferences.push_enabled or preferences.email_enabled):
                return False

            # Verificar suscripción a eventos WebSocket
            if notification.websocket_event and not preferences.is_subscribed_to_websocket_event(notification.websocket_event):
                return False

            return True

        except Exception as e:
            logger.warning(f"Error verificando preferencias para usuario {notification.user_id}: {e}")
            return True  # Por defecto permitir envío

    async def _send_push_notification(self, notification: Notification) -> bool:
        """
        Envía una notificación push.

        Args:
            notification: Notificación a enviar

        Returns:
            bool: True si se envió exitosamente
        """
        try:
            preferences = await self.get_user_preferences(notification.user_id)

            if not preferences.push_token:
                logger.warning(f"No hay token push configurado para usuario {notification.user_id}")
                return False

            # Configurar payload FCM
            fcm_payload = {
                "to": preferences.push_token,
                "notification": {
                    "title": notification.title,
                    "body": notification.body,
                    "icon": "default",
                    "click_action": "FLUTTER_NOTIFICATION_CLICK"
                },
                "data": notification.data
            }

            # Enviar a FCM
            headers = {
                "Authorization": f"key={self.push_config.get('fcm_server_key', '')}",
                "Content-Type": "application/json"
            }

            response = requests.post(
                "https://fcm.googleapis.com/fcm/send",
                json=fcm_payload,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                logger.info(f"Push notification enviada a usuario {notification.user_id}")
                return True
            else:
                logger.error(f"Error FCM: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error enviando push notification: {e}")
            raise PushProviderError(f"Error en push provider: {e}")

    async def _send_email_notification(self, notification: Notification) -> bool:
        """
        Envía una notificación por email.

        Args:
            notification: Notificación a enviar

        Returns:
            bool: True si se envió exitosamente
        """
        try:
            preferences = await self.get_user_preferences(notification.user_id)

            if not preferences.email_address:
                logger.warning(f"No hay email configurado para usuario {notification.user_id}")
                return False

            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['Subject'] = notification.subject or notification.title
            msg['From'] = self.smtp_config.get('from_email', 'noreply@ailoos.com')
            msg['To'] = preferences.email_address

            # Agregar cuerpo texto plano
            text_part = MIMEText(notification.body, 'plain', 'utf-8')
            msg.attach(text_part)

            # Agregar cuerpo HTML si existe
            if notification.html_body:
                html_part = MIMEText(notification.html_body, 'html', 'utf-8')
                msg.attach(html_part)

            # Enviar email
            server = smtplib.SMTP(
                self.smtp_config.get('host', 'smtp.gmail.com'),
                self.smtp_config.get('port', 587)
            )

            if self.smtp_config.get('use_tls', True):
                server.starttls()

            if 'username' in self.smtp_config and 'password' in self.smtp_config:
                server.login(
                    self.smtp_config['username'],
                    self.smtp_config['password']
                )

            server.sendmail(
                msg['From'],
                [msg['To']],
                msg.as_string()
            )

            server.quit()

            logger.info(f"Email enviado a {preferences.email_address}")
            return True

        except Exception as e:
            logger.error(f"Error enviando email: {e}")
            raise EmailProviderError(f"Error en email provider: {e}")

    async def _send_websocket_notification(self, notification: Notification) -> bool:
        """
        Envía una notificación WebSocket.

        Args:
            notification: Notificación a enviar

        Returns:
            bool: True si se envió exitosamente
        """
        try:
            if not self.websocket_manager:
                logger.warning("WebSocket manager no configurado")
                return False

            # Crear mensaje WebSocket
            from ..coordinator.models.schemas import WebSocketMessage
            ws_message = WebSocketMessage(
                type="notification.push",
                data={
                    "id": notification.id,
                    "event_type": notification.websocket_event,
                    "title": notification.title,
                    "body": notification.body,
                    "data": notification.data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            # Enviar a la sala especificada o a usuario específico
            if notification.websocket_room:
                # Enviar a una sala específica
                from ..coordinator.websocket.room_manager import room_manager
                await room_manager.broadcast_to_room(notification.websocket_room, ws_message)
            else:
                # Enviar a sesiones del usuario (convertir user_id a node_id si es necesario)
                # Esto requiere mapear user_id a node_id, por ahora asumimos que son iguales
                node_id = str(notification.user_id)
                await self.websocket_manager.broadcast_to_node_sessions(ws_message, node_id)

            logger.info(f"Notificación WebSocket enviada para usuario {notification.user_id}")
            return True

        except Exception as e:
            logger.error(f"Error enviando notificación WebSocket: {e}")
            return False

    def _send_notification_sync(self, notification: Notification) -> None:
        """
        Callback síncrono para envío de notificaciones (usado por NotificationQueue).
        """
        # Crear event loop si no existe
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Ejecutar envío asíncrono
        loop.run_until_complete(self.send_notification(notification))

    def get_queue_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la cola de notificaciones."""
        if self.use_async_queue:
            # Para async, necesitaríamos await, pero por simplicidad retornamos vacío
            return {}
        else:
            return self.queue.get_stats()

    def get_available_templates(self) -> List[NotificationTemplate]:
        """Obtiene lista de plantillas disponibles."""
        return notification_templates.list_templates()

    def add_template(self, template: NotificationTemplate):
        """Agrega una nueva plantilla."""
        notification_templates.add_template(template)

    def remove_template(self, template_name: str):
        """Elimina una plantilla."""
        notification_templates.remove_template(template_name)

    # Métodos específicos para WebSocket

    async def send_realtime_notification(self,
                                       user_id: int,
                                       event_type: str,
                                       title: str,
                                       message: str,
                                       data: Optional[Dict[str, Any]] = None,
                                       room: Optional[str] = None) -> bool:
        """
        Envía una notificación en tiempo real vía WebSocket.

        Args:
            user_id: ID del usuario
            event_type: Tipo de evento WebSocket
            title: Título de la notificación
            message: Mensaje de la notificación
            data: Datos adicionales
            room: Sala WebSocket específica (opcional)

        Returns:
            bool: True si se envió exitosamente
        """
        notification = self.create_notification(
            user_id=user_id,
            title=title,
            body=message,
            notification_type=NotificationType.REALTIME,
            websocket_event=event_type,
            websocket_room=room,
            data=data
        )

        return await self.send_notification(notification)

    async def broadcast_system_event(self,
                                   event_type: str,
                                   title: str,
                                   message: str,
                                   data: Optional[Dict[str, Any]] = None,
                                   target_users: Optional[List[int]] = None) -> int:
        """
        Broadcast de evento del sistema a múltiples usuarios.

        Args:
            event_type: Tipo de evento
            title: Título del evento
            message: Mensaje del evento
            data: Datos adicionales
            target_users: Lista de usuarios objetivo (None = todos)

        Returns:
            int: Número de notificaciones enviadas exitosamente
        """
        success_count = 0

        if target_users:
            for user_id in target_users:
                if await self.send_realtime_notification(user_id, event_type, title, message, data):
                    success_count += 1
        else:
            # Broadcast a todos los usuarios
            try:
                all_users = self.settings_service.list_users()
                for user in all_users:
                    # El ID puede venir como 'id' o 'user_id' dependiendo del dict devuelto
                    user_id = user.get('id') or user.get('user_id')
                    if user_id:
                        if await self.send_realtime_notification(user_id, event_type, title, message, data):
                            success_count += 1
            except Exception as e:
                logger.error(f"Error en broadcast global: {e}")

        return success_count