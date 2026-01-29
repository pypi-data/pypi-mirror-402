"""
Validadores para el sistema de notificaciones
===========================================

Este módulo proporciona funciones de validación para notificaciones,
plantillas y preferencias de usuario.
"""

import re
import json
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime

from .models import Notification, NotificationTemplate, UserNotificationPreferences

if TYPE_CHECKING:
    from .models import DiscordIntegration, WebhookIntegration, DiscordMessage, WebhookPayload


class ValidationError(Exception):
    """Error de validación."""
    pass


def validate_notification(notification: Notification) -> List[str]:
    """
    Valida una notificación.

    Args:
        notification: Notificación a validar

    Returns:
        List[str]: Lista de errores de validación
    """
    errors = []

    # Validar ID de usuario
    if notification.user_id <= 0:
        errors.append("user_id debe ser un entero positivo")

    # Validar título
    if not notification.title or not notification.title.strip():
        errors.append("title no puede estar vacío")
    elif len(notification.title) > 200:
        errors.append("title no puede exceder 200 caracteres")

    # Validar cuerpo
    if not notification.body or not notification.body.strip():
        errors.append("body no puede estar vacío")
    elif len(notification.body) > 1000:
        errors.append("body no puede exceder 1000 caracteres")

    # Validar asunto (para emails)
    if notification.subject and len(notification.subject) > 200:
        errors.append("subject no puede exceder 200 caracteres")

    # Validar HTML body
    if notification.html_body and len(notification.html_body) > 5000:
        errors.append("html_body no puede exceder 5000 caracteres")

    # Validar fecha programada
    if notification.scheduled_at and notification.scheduled_at <= datetime.now():
        errors.append("scheduled_at debe ser una fecha futura")

    # Validar reintentos
    if notification.retry_count < 0:
        errors.append("retry_count no puede ser negativo")
    if notification.max_retries < 0 or notification.max_retries > 10:
        errors.append("max_retries debe estar entre 0 y 10")

    return errors


def validate_notification_template(template: NotificationTemplate) -> List[str]:
    """
    Valida una plantilla de notificación.

    Args:
        template: Plantilla a validar

    Returns:
        List[str]: Lista de errores de validación
    """
    errors = []

    # Validar nombre
    if not template.name or not template.name.strip():
        errors.append("name no puede estar vacío")
    elif not re.match(r'^[a-zA-Z0-9_-]+$', template.name):
        errors.append("name solo puede contener letras, números, guiones y guiones bajos")
    elif len(template.name) > 50:
        errors.append("name no puede exceder 50 caracteres")

    # Validar título
    if not template.title or not template.title.strip():
        errors.append("title no puede estar vacío")
    elif len(template.title) > 200:
        errors.append("title no puede exceder 200 caracteres")

    # Validar cuerpo
    if not template.body or not template.body.strip():
        errors.append("body no puede estar vacío")
    elif len(template.body) > 1000:
        errors.append("body no puede exceder 1000 caracteres")

    # Validar asunto (para emails)
    if template.subject and len(template.subject) > 200:
        errors.append("subject no puede exceder 200 caracteres")

    # Validar HTML body
    if template.html_body and len(template.html_body) > 5000:
        errors.append("html_body no puede exceder 5000 caracteres")

    # Validar variables
    if template.variables:
        for var in template.variables:
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var):
                errors.append(f"variable '{var}' no tiene un nombre válido")

    # Validar placeholders en el contenido
    def check_placeholders(text: str, field_name: str):
        if not text:
            return
        # Encontrar todos los placeholders {variable}
        placeholders = re.findall(r'\{([^}]+)\}', text)
        for placeholder in placeholders:
            if placeholder not in template.variables:
                errors.append(f"placeholder '{{{placeholder}}}' en {field_name} no está definido en variables")

    check_placeholders(template.subject, "subject")
    check_placeholders(template.title, "title")
    check_placeholders(template.body, "body")
    if template.html_body:
        check_placeholders(template.html_body, "html_body")

    return errors


def validate_user_preferences(preferences: UserNotificationPreferences) -> List[str]:
    """
    Valida las preferencias de notificación de un usuario.

    Args:
        preferences: Preferencias a validar

    Returns:
        List[str]: Lista de errores de validación
    """
    errors = []

    # Validar ID de usuario
    if preferences.user_id <= 0:
        errors.append("user_id debe ser un entero positivo")

    # Validar email
    if preferences.email_address and not _is_valid_email(preferences.email_address):
        errors.append("email_address debe ser una dirección de email válida")

    # Validar token push (debe ser una cadena no vacía si está presente)
    if preferences.push_token and not preferences.push_token.strip():
        errors.append("push_token no puede estar vacío si se proporciona")

    # Validar horas de silencio
    if preferences.quiet_hours_start:
        if not _is_valid_time(preferences.quiet_hours_start):
            errors.append("quiet_hours_start debe tener formato HH:MM")
    if preferences.quiet_hours_end:
        if not _is_valid_time(preferences.quiet_hours_end):
            errors.append("quiet_hours_end debe tener formato HH:MM")

    # Validar zona horaria
    if not preferences.timezone:
        errors.append("timezone no puede estar vacío")

    return errors


def validate_notification_data(data: Dict[str, Any]) -> List[str]:
    """
    Valida datos adicionales de notificación.

    Args:
        data: Datos a validar

    Returns:
        List[str]: Lista de errores de validación
    """
    errors = []

    # Validar tamaño total
    data_str = str(data)
    if len(data_str) > 10000:  # 10KB límite
        errors.append("data no puede exceder 10KB")

    # Validar tipos de datos (solo tipos serializables)
    try:
        import json
        json.dumps(data)
    except (TypeError, ValueError) as e:
        errors.append(f"data contiene tipos no serializables: {e}")

    return errors


def validate_smtp_config(config: Dict[str, Any]) -> List[str]:
    """
    Valida configuración SMTP.

    Args:
        config: Configuración SMTP a validar

    Returns:
        List[str]: Lista de errores de validación
    """
    errors = []

    # Campos requeridos
    required_fields = ['host', 'port', 'username', 'password', 'from_email']
    for field in required_fields:
        if field not in config or not config[field]:
            errors.append(f"Campo requerido faltante: {field}")

    # Validar host
    if 'host' in config and config['host']:
        if not _is_valid_hostname(config['host']):
            errors.append("host debe ser un hostname válido")

    # Validar puerto
    if 'port' in config and config['port']:
        try:
            port = int(config['port'])
            if port < 1 or port > 65535:
                errors.append("port debe estar entre 1 y 65535")
        except (ValueError, TypeError):
            errors.append("port debe ser un número entero")

    # Validar email del remitente
    if 'from_email' in config and config['from_email']:
        if not _is_valid_email(config['from_email']):
            errors.append("from_email debe ser una dirección de email válida")

    return errors


def validate_push_config(config: Dict[str, Any]) -> List[str]:
    """
    Valida configuración de push notifications.

    Args:
        config: Configuración push a validar

    Returns:
        List[str]: Lista de errores de validación
    """
    errors = []

    # Validar FCM server key
    if 'fcm_server_key' in config and config['fcm_server_key']:
        if not config['fcm_server_key'].strip():
            errors.append("fcm_server_key no puede estar vacío")
        elif len(config['fcm_server_key']) < 20:
            errors.append("fcm_server_key parece ser inválido (muy corto)")

    # Validar APNs certificate path
    if 'apns_cert_path' in config and config['apns_cert_path']:
        if not config['apns_cert_path'].strip():
            errors.append("apns_cert_path no puede estar vacío")

    # Validar APNs key id
    if 'apns_key_id' in config and config['apns_key_id']:
        if not config['apns_key_id'].strip():
            errors.append("apns_key_id no puede estar vacío")

    return errors


def _is_valid_email(email: str) -> bool:
    """Valida si una cadena es un email válido."""
    pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    return bool(pattern.match(email))


def _is_valid_time(time_str: str) -> bool:
    """Valida si una cadena tiene formato HH:MM."""
    pattern = re.compile(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    return bool(pattern.match(time_str))


def _is_valid_hostname(hostname: str) -> bool:
    """Valida si una cadena es un hostname válido."""
    if not hostname or len(hostname) > 253:
        return False

    # Remover puerto si existe
    hostname = hostname.split(':')[0]

    # Validar caracteres y estructura
    pattern = re.compile(
        r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
    )

    return bool(pattern.match(hostname))


def validate_discord_integration(integration: 'DiscordIntegration') -> List[str]:
    """
    Valida una integración con Discord.

    Args:
        integration: Integración a validar

    Returns:
        List[str]: Lista de errores de validación
    """
    errors = []

    # Validar nombre
    if not integration.name or not integration.name.strip():
        errors.append("name no puede estar vacío")
    elif len(integration.name) > 100:
        errors.append("name no puede exceder 100 caracteres")

    # Validar IDs de Discord (deben ser numéricos)
    if not integration.server_id or not integration.server_id.strip():
        errors.append("server_id no puede estar vacío")
    elif not integration.server_id.isdigit() or len(integration.server_id) < 15:
        errors.append("server_id debe ser un ID válido de Discord (numérico, mínimo 15 dígitos)")

    if not integration.channel_id or not integration.channel_id.strip():
        errors.append("channel_id no puede estar vacío")
    elif not integration.channel_id.isdigit() or len(integration.channel_id) < 15:
        errors.append("channel_id debe ser un ID válido de Discord (numérico, mínimo 15 dígitos)")

    # Validar credenciales (al menos una debe estar presente)
    has_bot_token = bool(integration.bot_token and integration.bot_token.strip())
    has_webhook = bool(integration.webhook_url and integration.webhook_url.strip())

    if not has_bot_token and not has_webhook:
        errors.append("Debe proporcionar bot_token o webhook_url")

    # Validar webhook URL si está presente
    if has_webhook:
        if not integration.webhook_url.startswith('https://discord.com/api/webhooks/'):
            errors.append("webhook_url debe ser una URL válida de Discord webhook")
        if len(integration.webhook_url) < 80:  # URLs de Discord son bastante largas
            errors.append("webhook_url parece ser inválida (muy corta)")

    return errors


def validate_webhook_integration(integration: 'WebhookIntegration') -> List[str]:
    """
    Valida una integración de webhook.

    Args:
        integration: Integración a validar

    Returns:
        List[str]: Lista de errores de validación
    """
    errors = []

    # Validar nombre
    if not integration.name or not integration.name.strip():
        errors.append("name no puede estar vacío")
    elif len(integration.name) > 100:
        errors.append("name no puede exceder 100 caracteres")

    # Validar URL
    if not integration.url or not integration.url.strip():
        errors.append("url no puede estar vacío")
    elif not integration.url.startswith(('http://', 'https://')):
        errors.append("url debe comenzar con http:// o https://")
    elif len(integration.url) > 2000:
        errors.append("url no puede exceder 2000 caracteres")

    # Validar método HTTP
    valid_methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
    if integration.method.upper() not in valid_methods:
        errors.append(f"method debe ser uno de: {', '.join(valid_methods)}")

    # Validar headers (si están presentes)
    if integration.headers:
        for key, value in integration.headers.items():
            if not key or not key.strip():
                errors.append("header keys no pueden estar vacíos")
            if len(key) > 100:
                errors.append(f"header key '{key}' es demasiado largo")
            if len(str(value)) > 1000:
                errors.append(f"header value para '{key}' es demasiado largo")

    # Validar configuración de reintentos y timeout
    if integration.retry_count < 0 or integration.retry_count > 10:
        errors.append("retry_count debe estar entre 0 y 10")

    if integration.timeout < 1 or integration.timeout > 300:
        errors.append("timeout debe estar entre 1 y 300 segundos")

    return errors


def validate_discord_message(message: 'DiscordMessage') -> List[str]:
    """
    Valida un mensaje de Discord.

    Args:
        message: Mensaje a validar

    Returns:
        List[str]: Lista de errores de validación
    """
    errors = []

    # Validar contenido
    if not message.content and not message.embeds:
        errors.append("El mensaje debe tener content o embeds")

    if message.content and len(message.content) > 2000:
        errors.append("content no puede exceder 2000 caracteres")

    # Validar embeds
    if message.embeds:
        if len(message.embeds) > 10:
            errors.append("No puede haber más de 10 embeds")

        for i, embed in enumerate(message.embeds):
            if len(str(embed)) > 6000:  # Límite aproximado de Discord
                errors.append(f"Embed {i+1} es demasiado largo")

            # Validar campos requeridos de embed
            if 'title' in embed and len(embed['title']) > 256:
                errors.append(f"Título del embed {i+1} no puede exceder 256 caracteres")

            if 'description' in embed and len(embed['description']) > 4096:
                errors.append(f"Descripción del embed {i+1} no puede exceder 4096 caracteres")

    # Validar URLs si están presentes
    if message.avatar_url and not message.avatar_url.startswith(('http://', 'https://')):
        errors.append("avatar_url debe ser una URL válida")

    return errors


def validate_webhook_payload(payload: 'WebhookPayload') -> List[str]:
    """
    Valida un payload de webhook.

    Args:
        payload: Payload a validar

    Returns:
        List[str]: Lista de errores de validación
    """
    errors = []

    # Validar tipo de evento
    if not payload.event_type or not payload.event_type.strip():
        errors.append("event_type no puede estar vacío")
    elif len(payload.event_type) > 100:
        errors.append("event_type no puede exceder 100 caracteres")
    elif not payload.event_type.replace('_', '').replace('-', '').isalnum():
        errors.append("event_type solo puede contener letras, números, guiones y guiones bajos")

    # Validar datos
    if payload.data is not None:
        try:
            # Intentar serializar para verificar que es JSON válido
            json.dumps(payload.data)
        except (TypeError, ValueError) as e:
            errors.append(f"data no es serializable a JSON: {e}")

        # Verificar tamaño (límite aproximado)
        data_str = json.dumps(payload.data)
        if len(data_str) > 100000:  # 100KB límite
            errors.append("data no puede exceder 100KB")

    # Validar firma si está presente
    if payload.signature and len(payload.signature) < 20:
        errors.append("signature parece ser inválida (muy corta)")

    return errors


def validate_all(notification: Optional[Notification] = None,
                template: Optional[NotificationTemplate] = None,
                preferences: Optional[UserNotificationPreferences] = None,
                data: Optional[Dict[str, Any]] = None,
                discord_integration: Optional['DiscordIntegration'] = None,
                webhook_integration: Optional['WebhookIntegration'] = None,
                discord_message: Optional['DiscordMessage'] = None,
                webhook_payload: Optional['WebhookPayload'] = None) -> Dict[str, List[str]]:
    """
    Valida todos los componentes proporcionados.

    Args:
        notification: Notificación a validar
        template: Plantilla a validar
        preferences: Preferencias a validar
        data: Datos adicionales a validar
        discord_integration: Integración de Discord a validar
        webhook_integration: Integración de webhook a validar
        discord_message: Mensaje de Discord a validar
        webhook_payload: Payload de webhook a validar

    Returns:
        Dict[str, List[str]]: Diccionario con errores por componente
    """
    errors = {}

    if notification:
        notif_errors = validate_notification(notification)
        if notif_errors:
            errors['notification'] = notif_errors

    if template:
        template_errors = validate_notification_template(template)
        if template_errors:
            errors['template'] = template_errors

    if preferences:
        prefs_errors = validate_user_preferences(preferences)
        if prefs_errors:
            errors['preferences'] = prefs_errors

    if data:
        data_errors = validate_notification_data(data)
        if data_errors:
            errors['data'] = data_errors

    if discord_integration:
        discord_errors = validate_discord_integration(discord_integration)
        if discord_errors:
            errors['discord_integration'] = discord_errors

    if webhook_integration:
        webhook_errors = validate_webhook_integration(webhook_integration)
        if webhook_errors:
            errors['webhook_integration'] = webhook_errors

    if discord_message:
        message_errors = validate_discord_message(discord_message)
        if message_errors:
            errors['discord_message'] = message_errors

    if webhook_payload:
        payload_errors = validate_webhook_payload(webhook_payload)
        if payload_errors:
            errors['webhook_payload'] = payload_errors

    return errors