"""
Servicio de notificaciones de seguridad para AILOOS
==================================================

Este módulo implementa el envío automático de notificaciones push
para eventos de seguridad importantes como cambios de contraseña,
inicios de sesión, actividad sospechosa, etc.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .service import NotificationService
from ..settings.service import SettingsService

logger = logging.getLogger(__name__)


class SecurityNotificationService:
    """
    Servicio para enviar notificaciones de seguridad automáticamente.

    Maneja eventos como:
    - Cambios de contraseña
    - Inicios de sesión desde nuevos dispositivos
    - Actividad sospechosa
    - Activación/desactivación de 2FA
    - Intentos de acceso fallidos
    """

    def __init__(self, notification_service: NotificationService, settings_service: SettingsService):
        self.notification_service = notification_service
        self.settings_service = settings_service

    async def notify_password_change(self, user_id: int, ip_address: Optional[str] = None) -> bool:
        """
        Notifica cambio de contraseña.

        Args:
            user_id: ID del usuario
            ip_address: Dirección IP desde donde se realizó el cambio

        Returns:
            bool: True si la notificación se envió exitosamente
        """
        try:
            # Verificar si el usuario tiene activadas las notificaciones de cambio de contraseña
            # Por ahora asumimos que siempre se envía para seguridad

            title = "Contraseña Cambiada"
            body = "Tu contraseña ha sido cambiada exitosamente."
            if ip_address:
                body += f" Desde: {ip_address}"

            success = await self.notification_service.send_notification(
                self.notification_service.create_notification(
                    user_id=user_id,
                    title=title,
                    body=body,
                    notification_type=self.notification_service.NotificationType.PUSH,
                    priority=self.notification_service.NotificationPriority.HIGH,
                    data={
                        "type": "password_change",
                        "ip_address": ip_address,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            )

            if success:
                logger.info(f"Notificación de cambio de contraseña enviada a usuario {user_id}")
            else:
                logger.warning(f"No se pudo enviar notificación de cambio de contraseña a usuario {user_id}")

            return success

        except Exception as e:
            logger.error(f"Error enviando notificación de cambio de contraseña: {e}")
            return False

    async def notify_login_alert(self, user_id: int, device_info: Optional[Dict[str, Any]] = None, ip_address: Optional[str] = None) -> bool:
        """
        Notifica inicio de sesión desde un nuevo dispositivo.

        Args:
            user_id: ID del usuario
            device_info: Información del dispositivo (user_agent, browser, etc.)
            ip_address: Dirección IP del inicio de sesión

        Returns:
            bool: True si la notificación se envió exitosamente
        """
        try:
            # Verificar si el usuario tiene activadas las alertas de login
            user_settings = self.settings_service.get_user_settings(user_id)
            if not user_settings.security.login_alerts:
                logger.info(f"Usuario {user_id} tiene desactivadas las alertas de login")
                return True  # No es un error, solo está desactivado

            device_str = "dispositivo desconocido"
            if device_info:
                browser = device_info.get('browser', 'Desconocido')
                os = device_info.get('os', 'Desconocido')
                device_str = f"{browser} en {os}"

            title = "Nuevo Inicio de Sesión"
            body = f"Se ha iniciado sesión en tu cuenta desde un nuevo {device_str}."
            if ip_address:
                body += f" IP: {ip_address}"

            success = await self.notification_service.send_notification(
                self.notification_service.create_notification(
                    user_id=user_id,
                    title=title,
                    body=body,
                    notification_type=self.notification_service.NotificationType.PUSH,
                    priority=self.notification_service.NotificationPriority.NORMAL,
                    data={
                        "type": "login",
                        "device_info": device_info,
                        "ip_address": ip_address,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            )

            if success:
                logger.info(f"Notificación de login enviada a usuario {user_id}")
            else:
                logger.warning(f"No se pudo enviar notificación de login a usuario {user_id}")

            return success

        except Exception as e:
            logger.error(f"Error enviando notificación de login: {e}")
            return False

    async def notify_suspicious_activity(self, user_id: int, activity_type: str, details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Notifica actividad sospechosa.

        Args:
            user_id: ID del usuario
            activity_type: Tipo de actividad sospechosa
            details: Detalles adicionales de la actividad

        Returns:
            bool: True si la notificación se envió exitosamente
        """
        try:
            title = "Actividad Sospechosa Detectada"
            body = f"Se ha detectado actividad sospechosa: {activity_type}"

            if details:
                if 'ip_address' in details:
                    body += f" desde IP: {details['ip_address']}"
                if 'attempts' in details:
                    body += f" ({details['attempts']} intentos)"
                if 'location' in details:
                    body += f" en {details['location']}"

            success = await self.notification_service.send_notification(
                self.notification_service.create_notification(
                    user_id=user_id,
                    title=title,
                    body=body,
                    notification_type=self.notification_service.NotificationType.PUSH,
                    priority=self.notification_service.NotificationPriority.URGENT,
                    data={
                        "type": "suspicious_activity",
                        "activity_type": activity_type,
                        "details": details,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            )

            if success:
                logger.info(f"Notificación de actividad sospechosa enviada a usuario {user_id}")
            else:
                logger.warning(f"No se pudo enviar notificación de actividad sospechosa a usuario {user_id}")

            return success

        except Exception as e:
            logger.error(f"Error enviando notificación de actividad sospechosa: {e}")
            return False

    async def notify_2fa_enabled(self, user_id: int) -> bool:
        """
        Notifica activación de 2FA.

        Args:
            user_id: ID del usuario

        Returns:
            bool: True si la notificación se envió exitosamente
        """
        try:
            title = "2FA Activado"
            body = "La autenticación de dos factores ha sido activada en tu cuenta."

            success = await self.notification_service.send_notification(
                self.notification_service.create_notification(
                    user_id=user_id,
                    title=title,
                    body=body,
                    notification_type=self.notification_service.NotificationType.PUSH,
                    priority=self.notification_service.NotificationPriority.NORMAL,
                    data={
                        "type": "2fa_enabled",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            )

            if success:
                logger.info(f"Notificación de 2FA activado enviada a usuario {user_id}")
            else:
                logger.warning(f"No se pudo enviar notificación de 2FA activado a usuario {user_id}")

            return success

        except Exception as e:
            logger.error(f"Error enviando notificación de 2FA activado: {e}")
            return False

    async def notify_2fa_disabled(self, user_id: int) -> bool:
        """
        Notifica desactivación de 2FA.

        Args:
            user_id: ID del usuario

        Returns:
            bool: True si la notificación se envió exitosamente
        """
        try:
            title = "2FA Desactivado"
            body = "La autenticación de dos factores ha sido desactivada en tu cuenta."

            success = await self.notification_service.send_notification(
                self.notification_service.create_notification(
                    user_id=user_id,
                    title=title,
                    body=body,
                    notification_type=self.notification_service.NotificationType.PUSH,
                    priority=self.notification_service.NotificationPriority.HIGH,
                    data={
                        "type": "2fa_disabled",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            )

            if success:
                logger.info(f"Notificación de 2FA desactivado enviada a usuario {user_id}")
            else:
                logger.warning(f"No se pudo enviar notificación de 2FA desactivado a usuario {user_id}")

            return success

        except Exception as e:
            logger.error(f"Error enviando notificación de 2FA desactivado: {e}")
            return False

    async def notify_failed_login_attempts(self, user_id: int, attempts: int, ip_address: Optional[str] = None) -> bool:
        """
        Notifica múltiples intentos fallidos de inicio de sesión.

        Args:
            user_id: ID del usuario
            attempts: Número de intentos fallidos
            ip_address: Dirección IP de los intentos

        Returns:
            bool: True si la notificación se envió exitosamente
        """
        try:
            title = "Intentos de Acceso Fallidos"
            body = f"Se han detectado {attempts} intentos fallidos de inicio de sesión en tu cuenta."
            if ip_address:
                body += f" Desde IP: {ip_address}"

            success = await self.notification_service.send_notification(
                self.notification_service.create_notification(
                    user_id=user_id,
                    title=title,
                    body=body,
                    notification_type=self.notification_service.NotificationType.PUSH,
                    priority=self.notification_service.NotificationPriority.HIGH,
                    data={
                        "type": "failed_login_attempts",
                        "attempts": attempts,
                        "ip_address": ip_address,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            )

            if success:
                logger.info(f"Notificación de intentos fallidos enviada a usuario {user_id}")
            else:
                logger.warning(f"No se pudo enviar notificación de intentos fallidos a usuario {user_id}")

            return success

        except Exception as e:
            logger.error(f"Error enviando notificación de intentos fallidos: {e}")
            return False

    async def notify_security_alert(self, user_id: int, alert_type: str, message: str, details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Notifica una alerta de seguridad genérica.

        Args:
            user_id: ID del usuario
            alert_type: Tipo de alerta
            message: Mensaje de la alerta
            details: Detalles adicionales

        Returns:
            bool: True si la notificación se envió exitosamente
        """
        try:
            title = f"Alerta de Seguridad: {alert_type}"
            body = message

            success = await self.notification_service.send_notification(
                self.notification_service.create_notification(
                    user_id=user_id,
                    title=title,
                    body=body,
                    notification_type=self.notification_service.NotificationType.PUSH,
                    priority=self.notification_service.NotificationPriority.URGENT,
                    data={
                        "type": "security_alert",
                        "alert_type": alert_type,
                        "details": details,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            )

            if success:
                logger.info(f"Notificación de alerta de seguridad enviada a usuario {user_id}")
            else:
                logger.warning(f"No se pudo enviar notificación de alerta de seguridad a usuario {user_id}")

            return success

        except Exception as e:
            logger.error(f"Error enviando notificación de alerta de seguridad: {e}")
            return False