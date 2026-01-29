"""
Servicio de integración con Discord para AILOOS
==============================================

Este módulo implementa la integración con Discord para envío de notificaciones
a canales y servidores específicos.
"""

import logging
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json
import hmac
import hashlib

from .models import (
    DiscordIntegration, DiscordMessage, WebhookPayload,
    Notification, NotificationStatus
)

logger = logging.getLogger(__name__)


class DiscordServiceError(Exception):
    """Excepción base para errores del servicio de Discord."""
    pass


class DiscordAPIError(DiscordServiceError):
    """Error en la API de Discord."""
    pass


class DiscordWebhookError(DiscordServiceError):
    """Error en webhook de Discord."""
    pass


class DiscordService:
    """
    Servicio para integración con Discord.

    Permite enviar mensajes a canales de Discord usando bots o webhooks.
    """

    def __init__(self):
        self.base_url = "https://discord.com/api/v10"
        self.session: Optional[aiohttp.ClientSession] = None
        self._integrations: Dict[str, DiscordIntegration] = {}

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def initialize(self):
        """Inicializa el servicio."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        logger.info("Servicio de Discord inicializado")

    async def close(self):
        """Cierra el servicio."""
        if self.session:
            await self.session.close()
            self.session = None
        logger.info("Servicio de Discord cerrado")

    def register_integration(self, integration: DiscordIntegration):
        """
        Registra una integración con Discord.

        Args:
            integration: Configuración de la integración
        """
        self._integrations[integration.id] = integration
        logger.info(f"Integración Discord registrada: {integration.name}")

    def unregister_integration(self, integration_id: str):
        """
        Elimina una integración registrada.

        Args:
            integration_id: ID de la integración
        """
        if integration_id in self._integrations:
            del self._integrations[integration_id]
            logger.info(f"Integración Discord eliminada: {integration_id}")

    def get_integration(self, integration_id: str) -> Optional[DiscordIntegration]:
        """
        Obtiene una integración por ID.

        Args:
            integration_id: ID de la integración

        Returns:
            DiscordIntegration o None si no existe
        """
        return self._integrations.get(integration_id)

    def list_integrations(self) -> List[DiscordIntegration]:
        """Lista todas las integraciones registradas."""
        return list(self._integrations.values())

    async def test_integration(self, integration_id: str) -> Dict[str, Any]:
        """
        Prueba una integración enviando un mensaje de test.

        Args:
            integration_id: ID de la integración a probar

        Returns:
            Dict con resultado de la prueba
        """
        integration = self.get_integration(integration_id)
        if not integration:
            raise DiscordServiceError(f"Integración no encontrada: {integration_id}")

        if not integration.enabled:
            raise DiscordServiceError(f"Integración deshabilitada: {integration_id}")

        try:
            test_message = DiscordMessage(
                content="🧪 **Test Message**\n\nEsta es una prueba de integración con AILOOS.",
                embeds=[{
                    "title": "Test de Integración",
                    "description": "Mensaje enviado automáticamente para verificar la configuración.",
                    "color": 0x00ff00,
                    "timestamp": datetime.utcnow().isoformat(),
                    "footer": {
                        "text": "AILOOS Integration Test"
                    }
                }]
            )

            success = await self.send_message(integration_id, test_message)
            return {
                "success": success,
                "integration_id": integration_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Test message sent successfully" if success else "Failed to send test message"
            }

        except Exception as e:
            logger.error(f"Error testing Discord integration {integration_id}: {e}")
            return {
                "success": False,
                "integration_id": integration_id,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }

    async def send_message(self,
                          integration_id: str,
                          message: DiscordMessage,
                          channel_id: Optional[str] = None) -> bool:
        """
        Envía un mensaje a Discord.

        Args:
            integration_id: ID de la integración a usar
            message: Mensaje a enviar
            channel_id: ID del canal (opcional, usa el de la integración por defecto)

        Returns:
            bool: True si se envió exitosamente
        """
        integration = self.get_integration(integration_id)
        if not integration:
            raise DiscordServiceError(f"Integración no encontrada: {integration_id}")

        if not integration.enabled:
            logger.warning(f"Integración deshabilitada: {integration_id}")
            return False

        target_channel = channel_id or integration.channel_id
        if not target_channel:
            raise DiscordServiceError("No se especificó canal de destino")

        try:
            if integration.webhook_url:
                # Usar webhook
                return await self._send_via_webhook(integration, message, target_channel)
            else:
                # Usar bot API
                return await self._send_via_bot(integration, message, target_channel)

        except Exception as e:
            logger.error(f"Error enviando mensaje Discord: {e}")
            raise DiscordAPIError(f"Error enviando mensaje: {e}")

    async def _send_via_webhook(self,
                               integration: DiscordIntegration,
                               message: DiscordMessage,
                               channel_id: str) -> bool:
        """
        Envía mensaje usando webhook de Discord.
        """
        if not self.session:
            raise DiscordServiceError("Servicio no inicializado")

        url = integration.webhook_url
        if not url:
            raise DiscordWebhookError("URL de webhook no configurada")

        # Preparar payload
        payload = message.to_dict()

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 204:  # Discord retorna 204 para webhooks exitosos
                    logger.info(f"Mensaje enviado vía webhook a canal {channel_id}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Error webhook Discord: {response.status} - {error_text}")
                    return False

        except aiohttp.ClientError as e:
            logger.error(f"Error de conexión webhook: {e}")
            raise DiscordWebhookError(f"Error de conexión: {e}")

    async def _send_via_bot(self,
                           integration: DiscordIntegration,
                           message: DiscordMessage,
                           channel_id: str) -> bool:
        """
        Envía mensaje usando la API de bot de Discord.
        """
        if not self.session:
            raise DiscordServiceError("Servicio no inicializado")

        if not integration.bot_token:
            raise DiscordAPIError("Token de bot no configurado")

        url = f"{self.base_url}/channels/{channel_id}/messages"
        headers = {
            "Authorization": f"Bot {integration.bot_token}",
            "Content-Type": "application/json"
        }

        # Preparar payload (remover campos específicos de webhook)
        payload = message.to_dict()
        payload.pop('username', None)
        payload.pop('avatar_url', None)

        try:
            async with self.session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Mensaje enviado vía bot a canal {channel_id}, ID: {data.get('id')}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Error API Discord: {response.status} - {error_text}")
                    return False

        except aiohttp.ClientError as e:
            logger.error(f"Error de conexión API Discord: {e}")
            raise DiscordAPIError(f"Error de conexión: {e}")

    async def send_embed(self,
                        integration_id: str,
                        title: str,
                        description: str,
                        color: int = 0x0099ff,
                        fields: Optional[List[Dict[str, str]]] = None,
                        channel_id: Optional[str] = None) -> bool:
        """
        Envía un embed de Discord.

        Args:
            integration_id: ID de la integración
            title: Título del embed
            description: Descripción del embed
            color: Color del embed (decimal)
            fields: Lista de campos del embed
            channel_id: Canal específico (opcional)

        Returns:
            bool: True si se envió exitosamente
        """
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.utcnow().isoformat()
        }

        if fields:
            embed["fields"] = fields

        message = DiscordMessage(embeds=[embed])
        return await self.send_message(integration_id, message, channel_id)

    async def send_notification(self,
                               integration_id: str,
                               notification: Notification,
                               channel_id: Optional[str] = None) -> bool:
        """
        Envía una notificación como mensaje de Discord.

        Args:
            integration_id: ID de la integración
            notification: Notificación a enviar
            channel_id: Canal específico (opcional)

        Returns:
            bool: True si se envió exitosamente
        """
        # Crear embed para la notificación
        embed = {
            "title": notification.title,
            "description": notification.body,
            "color": self._get_color_for_priority(notification.priority),
            "timestamp": notification.created_at.isoformat(),
            "footer": {
                "text": f"AILOOS Notification - Priority: {notification.priority.value.upper()}"
            }
        }

        # Agregar campos adicionales si hay datos
        if notification.data:
            fields = []
            for key, value in notification.data.items():
                if isinstance(value, (str, int, float, bool)):
                    fields.append({
                        "name": key.replace('_', ' ').title(),
                        "value": str(value),
                        "inline": True
                    })
            if fields:
                embed["fields"] = fields

        message = DiscordMessage(
            content="",  # El contenido va en el embed
            embeds=[embed]
        )

        success = await self.send_message(integration_id, message, channel_id)
        if success:
            notification.mark_as_sent()
        else:
            notification.error_message = "Failed to send Discord message"

        return success

    def _get_color_for_priority(self, priority) -> int:
        """Obtiene el color de Discord para una prioridad."""
        colors = {
            "low": 0x00ff00,      # Verde
            "normal": 0x0099ff,   # Azul
            "high": 0xffa500,     # Naranja
            "urgent": 0xff0000    # Rojo
        }
        return colors.get(priority.value, 0x0099ff)

    async def get_channel_info(self, integration_id: str, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de un canal de Discord.

        Args:
            integration_id: ID de la integración
            channel_id: ID del canal

        Returns:
            Dict con información del canal o None si falla
        """
        integration = self.get_integration(integration_id)
        if not integration or not integration.bot_token:
            return None

        if not self.session:
            return None

        url = f"{self.base_url}/channels/{channel_id}"
        headers = {
            "Authorization": f"Bot {integration.bot_token}"
        }

        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Error obteniendo info del canal: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error obteniendo info del canal: {e}")
            return None

    async def validate_bot_token(self, bot_token: str) -> bool:
        """
        Valida si un token de bot de Discord es válido.

        Args:
            bot_token: Token a validar

        Returns:
            bool: True si el token es válido
        """
        if not self.session:
            return False

        url = f"{self.base_url}/users/@me"
        headers = {
            "Authorization": f"Bot {bot_token}"
        }

        try:
            async with self.session.get(url, headers=headers) as response:
                return response.status == 200
        except Exception:
            return False

    async def validate_webhook_url(self, webhook_url: str) -> bool:
        """
        Valida si una URL de webhook de Discord es válida.

        Args:
            webhook_url: URL a validar

        Returns:
            bool: True si la URL es válida
        """
        if not self.session:
            return False

        try:
            async with self.session.get(webhook_url) as response:
                return response.status == 200
        except Exception:
            return False