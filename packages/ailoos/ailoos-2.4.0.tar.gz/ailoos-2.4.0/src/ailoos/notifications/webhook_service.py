"""
Servicio de webhooks externos para AILOOS
=========================================

Este módulo implementa el envío de notificaciones a sistemas externos
vía webhooks HTTP con soporte para firma HMAC y reintentos.
"""

import logging
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json
import hmac
import hashlib
import base64

from .models import (
    WebhookIntegration, WebhookPayload,
    Notification, NotificationStatus
)

logger = logging.getLogger(__name__)


class WebhookServiceError(Exception):
    """Excepción base para errores del servicio de webhooks."""
    pass


class WebhookDeliveryError(WebhookServiceError):
    """Error en la entrega del webhook."""
    pass


class WebhookSignatureError(WebhookServiceError):
    """Error en la firma del webhook."""
    pass


class WebhookService:
    """
    Servicio para envío de webhooks a sistemas externos.

    Soporta firma HMAC, reintentos automáticos y validación de entregas.
    """

    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.session: Optional[aiohttp.ClientSession] = None
        self._integrations: Dict[str, WebhookIntegration] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def initialize(self):
        """Inicializa el servicio."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        logger.info("Servicio de webhooks inicializado")

    async def close(self):
        """Cierra el servicio."""
        if self.session:
            await self.session.close()
            self.session = None
        logger.info("Servicio de webhooks cerrado")

    def register_integration(self, integration: WebhookIntegration):
        """
        Registra una integración de webhook.

        Args:
            integration: Configuración del webhook
        """
        self._integrations[integration.id] = integration
        logger.info(f"Webhook registrado: {integration.name}")

    def unregister_integration(self, integration_id: str):
        """
        Elimina una integración registrada.

        Args:
            integration_id: ID de la integración
        """
        if integration_id in self._integrations:
            del self._integrations[integration_id]
            logger.info(f"Webhook eliminado: {integration_id}")

    def get_integration(self, integration_id: str) -> Optional[WebhookIntegration]:
        """
        Obtiene una integración por ID.

        Args:
            integration_id: ID de la integración

        Returns:
            WebhookIntegration o None si no existe
        """
        return self._integrations.get(integration_id)

    def list_integrations(self) -> List[WebhookIntegration]:
        """Lista todas las integraciones registradas."""
        return list(self._integrations.values())

    async def test_integration(self, integration_id: str) -> Dict[str, Any]:
        """
        Prueba una integración enviando un payload de test.

        Args:
            integration_id: ID de la integración a probar

        Returns:
            Dict con resultado de la prueba
        """
        integration = self.get_integration(integration_id)
        if not integration:
            raise WebhookServiceError(f"Webhook no encontrado: {integration_id}")

        if not integration.enabled:
            raise WebhookServiceError(f"Webhook deshabilitado: {integration_id}")

        try:
            test_payload = WebhookPayload(
                event_type="test",
                data={
                    "message": "Test webhook from AILOOS",
                    "timestamp": datetime.utcnow().isoformat(),
                    "integration_id": integration_id
                }
            )

            success, response = await self.send_payload(integration_id, test_payload)
            return {
                "success": success,
                "integration_id": integration_id,
                "timestamp": datetime.utcnow().isoformat(),
                "response_status": response.get("status") if response else None,
                "response_body": response.get("body") if response else None,
                "message": "Test payload sent successfully" if success else "Failed to send test payload"
            }

        except Exception as e:
            logger.error(f"Error testing webhook {integration_id}: {e}")
            return {
                "success": False,
                "integration_id": integration_id,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }

    async def send_payload(self,
                          integration_id: str,
                          payload: WebhookPayload) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Envía un payload a un webhook.

        Args:
            integration_id: ID de la integración
            payload: Payload a enviar

        Returns:
            Tupla (éxito, respuesta)
        """
        integration = self.get_integration(integration_id)
        if not integration:
            raise WebhookServiceError(f"Webhook no encontrado: {integration_id}")

        if not integration.enabled:
            logger.warning(f"Webhook deshabilitado: {integration_id}")
            return False, None

        async with self._semaphore:
            return await self._send_with_retry(integration, payload)

    async def _send_with_retry(self,
                              integration: WebhookIntegration,
                              payload: WebhookPayload) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Envía un payload con reintentos automáticos.
        """
        last_error = None

        for attempt in range(integration.retry_count + 1):
            try:
                response = await self._send_single_request(integration, payload)
                if response["status"] < 400:  # Considerar 2xx y 3xx como éxito
                    logger.info(f"Webhook {integration.id} enviado exitosamente en intento {attempt + 1}")
                    return True, response
                else:
                    last_error = f"HTTP {response['status']}: {response.get('body', '')}"
                    logger.warning(f"Intento {attempt + 1} fallido para webhook {integration.id}: {last_error}")

            except Exception as e:
                last_error = str(e)
                logger.warning(f"Intento {attempt + 1} fallido para webhook {integration.id}: {last_error}")

            # Esperar antes del siguiente intento (exponential backoff)
            if attempt < integration.retry_count:
                wait_time = 2 ** attempt  # 1s, 2s, 4s, 8s...
                await asyncio.sleep(min(wait_time, 30))  # Máximo 30 segundos

        logger.error(f"Webhook {integration.id} falló después de {integration.retry_count + 1} intentos")
        return False, {"error": last_error}

    async def _send_single_request(self,
                                  integration: WebhookIntegration,
                                  payload: WebhookPayload) -> Dict[str, Any]:
        """
        Envía una sola petición HTTP.
        """
        if not self.session:
            raise WebhookServiceError("Servicio no inicializado")

        # Preparar payload
        payload_dict = payload.to_dict()

        # Generar firma si se configura secret
        if integration.secret:
            payload.signature = self._generate_signature(
                json.dumps(payload_dict, sort_keys=True),
                integration.secret
            )

        # Preparar headers
        headers = integration.headers.copy()
        headers["Content-Type"] = "application/json"
        headers["User-Agent"] = "AILOOS-Webhook/1.0"

        if integration.secret:
            headers["X-Signature"] = payload.signature

        # Enviar petición
        try:
            async with self.session.request(
                method=integration.method,
                url=integration.url,
                json=payload_dict,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=integration.timeout)
            ) as response:
                response_body = await response.text()
                return {
                    "status": response.status,
                    "headers": dict(response.headers),
                    "body": response_body
                }

        except asyncio.TimeoutError:
            raise WebhookDeliveryError(f"Timeout después de {integration.timeout} segundos")
        except aiohttp.ClientError as e:
            raise WebhookDeliveryError(f"Error de conexión: {e}")

    def _generate_signature(self, payload_str: str, secret: str) -> str:
        """
        Genera una firma HMAC-SHA256 para el payload.
        """
        payload_bytes = payload_str.encode('utf-8')
        secret_bytes = secret.encode('utf-8')
        signature = hmac.new(secret_bytes, payload_bytes, hashlib.sha256)
        return base64.b64encode(signature.digest()).decode('utf-8')

    async def send_notification(self,
                               integration_id: str,
                               notification: Notification) -> bool:
        """
        Envía una notificación como webhook.

        Args:
            integration_id: ID de la integración
            notification: Notificación a enviar

        Returns:
            bool: True si se envió exitosamente
        """
        # Crear payload para la notificación
        payload = WebhookPayload(
            event_type="notification",
            data={
                "id": notification.id,
                "user_id": notification.user_id,
                "type": notification.type.value,
                "priority": notification.priority.value,
                "title": notification.title,
                "body": notification.body,
                "data": notification.data,
                "created_at": notification.created_at.isoformat(),
                "template_id": notification.template_id,
                "websocket_event": notification.websocket_event,
                "websocket_room": notification.websocket_room
            }
        )

        success, response = await self.send_payload(integration_id, payload)
        if success:
            notification.mark_as_sent()
        else:
            notification.error_message = f"Webhook delivery failed: {response.get('error', 'Unknown error') if response else 'No response'}"

        return success

    async def broadcast_event(self,
                             event_type: str,
                             data: Dict[str, Any],
                             target_integrations: Optional[List[str]] = None) -> Dict[str, int]:
        """
        Envía un evento a múltiples webhooks.

        Args:
            event_type: Tipo de evento
            data: Datos del evento
            target_integrations: Lista de IDs de integraciones (None = todas)

        Returns:
            Dict con estadísticas de envío
        """
        integrations = target_integrations or [i.id for i in self.list_integrations()]
        results = {"sent": 0, "failed": 0}

        payload = WebhookPayload(event_type=event_type, data=data)

        tasks = []
        for integration_id in integrations:
            task = self.send_payload(integration_id, payload)
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for i, response in enumerate(responses):
            integration_id = integrations[i]
            if isinstance(response, Exception):
                logger.error(f"Error enviando a webhook {integration_id}: {response}")
                results["failed"] += 1
            else:
                success, _ = response
                if success:
                    results["sent"] += 1
                else:
                    results["failed"] += 1

        logger.info(f"Broadcast completado: {results['sent']} enviados, {results['failed']} fallidos")
        return results

    async def validate_webhook_url(self, url: str, method: str = "POST") -> bool:
        """
        Valida si una URL de webhook es accesible.

        Args:
            url: URL a validar
            method: Método HTTP a usar

        Returns:
            bool: True si la URL es válida
        """
        if not self.session:
            return False

        try:
            # Enviar una petición HEAD o OPTIONS para validar
            test_method = "HEAD" if method.upper() == "POST" else "OPTIONS"
            async with self.session.request(test_method, url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                return response.status < 400
        except Exception:
            return False

    def validate_signature(self, payload: str, signature: str, secret: str) -> bool:
        """
        Valida una firma HMAC de un webhook recibido.

        Args:
            payload: Payload recibido (string JSON)
            signature: Firma recibida
            secret: Secret configurado

        Returns:
            bool: True si la firma es válida
        """
        expected_signature = self._generate_signature(payload, secret)
        return hmac.compare_digest(expected_signature, signature)