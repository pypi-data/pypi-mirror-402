"""
Middleware de Content Negotiation para serialización AILOOS.
Implementa negociación automática de contenido entre JSON/TOON/VSC.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Callable, Union
from fastapi import Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from ..core.logging import get_logger
from ..core.config import get_config
from .serializers import (
    SerializationFormat, SerializationResult, DeserializationResult,
    get_serializer, detect_format, convert_format, SerializationError
)

logger = get_logger(__name__)


class ContentNegotiationMiddleware(BaseHTTPMiddleware):
    """
    Middleware para negociación automática de contenido.
    Detecta Accept headers y convierte entre formatos JSON/TOON/VSC.
    """

    # Mapeo de tipos MIME a formatos
    MIME_TYPES = {
        "application/json": SerializationFormat.JSON,
        "application/toon": SerializationFormat.TOON,
        "application/vsc": SerializationFormat.VSC,
        "application/x-toon": SerializationFormat.TOON,  # Alias
        "application/x-vsc": SerializationFormat.VSC,    # Alias
    }

    # Mapeo inverso
    FORMAT_MIME_TYPES = {v: k for k, v in MIME_TYPES.items()}

    def __init__(self, app, feature_flags: Optional[Dict[str, bool]] = None):
        super().__init__(app)
        self.config = get_config()

        # Feature flags para control gradual
        self.feature_flags = feature_flags or {
            "serialization_enabled": True,
            "toon_enabled": True,
            "vsc_enabled": True,
            "auto_conversion": True,
            "compression": False,
            "fallback_to_json": True,
        }

        # Estadísticas de uso
        self.stats = {
            "requests_processed": 0,
            "conversions_performed": 0,
            "errors": 0,
            "format_usage": {fmt.value: 0 for fmt in SerializationFormat},
            "conversion_times": [],
        }

        # Cache de esquemas por endpoint
        self.endpoint_schemas: Dict[str, Dict[str, Any]] = {}

        logger.info(f"🧩 ContentNegotiationMiddleware initialized with feature flags: {self.feature_flags}")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Procesar request/response con negociación de contenido."""
        if not self.feature_flags["serialization_enabled"]:
            return await call_next(request)

        start_time = time.time()
        self.stats["requests_processed"] += 1

        try:
            # Procesar request (deserialización si es necesario)
            processed_request = await self._process_request(request)

            # Llamar al endpoint
            response = await call_next(processed_request)

            # Procesar response (serialización/conversión si es necesario)
            final_response = await self._process_response(request, response)

            processing_time = time.time() - start_time
            logger.debug(f"Content negotiation processed in {processing_time:.3f}s")

            return final_response

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Content negotiation error: {e}")

            # Fallback seguro a JSON
            if self.feature_flags["fallback_to_json"]:
                return JSONResponse(
                    status_code=500,
                    content={"error": "Serialization error", "details": str(e)}
                )
            else:
                raise

    async def _process_request(self, request: Request) -> Request:
        """Procesar request entrante (deserialización)."""
        content_type = request.headers.get("content-type", "").lower()

        # Solo procesar si el content-type es uno de nuestros formatos
        if content_type not in self.MIME_TYPES:
            return request

        # Detectar formato
        target_format = self.MIME_TYPES[content_type]

        # Leer body
        body = await request.body()

        if not body:
            return request

        try:
            # Detectar formato actual (por si acaso)
            detected_format = detect_format(body)
            if detected_format and detected_format != target_format:
                logger.warning(f"Content-Type {content_type} doesn't match detected format {detected_format}")

            # Obtener esquema para validación
            schema = self._get_endpoint_schema(request.url.path, "request")

            # Deserializar
            serializer = get_serializer(target_format, schema)
            deserialized = serializer.deserialize(body)

            # Crear nuevo request con datos deserializados
            # Nota: En FastAPI, modificar el body del request es complejo
            # Por ahora, almacenamos los datos deserializados en el estado del request
            request.state.deserialized_data = deserialized.data
            request.state.original_format = target_format

            logger.info(f"📥 Deserialized request from {target_format.value} format")

        except SerializationError as e:
            logger.warning(f"Failed to deserialize request: {e}")
            # Continuar con request original

        return request

    async def _process_response(self, request: Request, response: Response) -> Response:
        """Procesar response saliente (serialización/conversión)."""
        # Determinar formato deseado desde Accept header
        accept_header = request.headers.get("accept", "application/json")
        desired_format = self._parse_accept_header(accept_header)

        # Si no hay conversión necesaria y response ya está en formato correcto
        if not self._needs_conversion(response, desired_format):
            self.stats["format_usage"][desired_format.value] += 1
            return response

        # Obtener datos de la response
        response_data = await self._extract_response_data(response)

        if response_data is None:
            return response

        try:
            # Obtener esquema para el endpoint
            schema = self._get_endpoint_schema(request.url.path, "response")

            # Serializar al formato deseado
            serializer = get_serializer(desired_format, schema)
            serialized = serializer.serialize(response_data)

            # Crear nueva response
            new_response = await self._create_formatted_response(
                serialized, desired_format, response.status_code, response.headers
            )

            self.stats["conversions_performed"] += 1
            self.stats["format_usage"][desired_format.value] += 1

            logger.info(f"📤 Converted response to {desired_format.value} format")

            return new_response

        except SerializationError as e:
            logger.error(f"Failed to serialize response: {e}")

            # Fallback a JSON si está habilitado
            if self.feature_flags["fallback_to_json"]:
                return JSONResponse(
                    status_code=response.status_code,
                    content={"error": "Serialization failed", "original_data": str(response_data)}
                )
            else:
                raise

    def _parse_accept_header(self, accept_header: str) -> SerializationFormat:
        """Parsear Accept header para determinar formato deseado."""
        # Soporte básico para quality values (q=)
        accepts = [a.strip() for a in accept_header.split(',')]

        for accept in accepts:
            # Remover quality value
            mime_type = accept.split(';')[0].strip()

            if mime_type in self.MIME_TYPES:
                format_type = self.MIME_TYPES[mime_type]

                # Verificar si el formato está habilitado
                if format_type == SerializationFormat.TOON and not self.feature_flags["toon_enabled"]:
                    continue
                if format_type == SerializationFormat.VSC and not self.feature_flags["vsc_enabled"]:
                    continue

                return format_type

            # Wildcard support
            if mime_type == "*/*" or mime_type == "application/*":
                # Preferir formatos eficientes si están habilitados
                if self.feature_flags["vsc_enabled"]:
                    return SerializationFormat.VSC
                elif self.feature_flags["toon_enabled"]:
                    return SerializationFormat.TOON
                else:
                    return SerializationFormat.JSON

        # Default fallback
        return SerializationFormat.JSON

    def _needs_conversion(self, response: Response, desired_format: SerializationFormat) -> bool:
        """Determinar si la response necesita conversión."""
        if not self.feature_flags["auto_conversion"]:
            return False

        # Verificar content-type actual
        content_type = response.headers.get("content-type", "").lower()

        # Si ya está en el formato deseado
        if content_type == self.FORMAT_MIME_TYPES.get(desired_format, ""):
            return False

        # Si es JSON y el formato deseado es JSON
        if desired_format == SerializationFormat.JSON and "json" in content_type:
            return False

        return True

    async def _extract_response_data(self, response: Response) -> Any:
        """Extraer datos de la response para serialización."""
        try:
            # Para JSONResponse
            if hasattr(response, 'body'):
                import json
                body_str = response.body.decode('utf-8')
                return json.loads(body_str)

            # Para responses con .data
            if hasattr(response, 'data'):
                return response.data

            # Para responses de FastAPI que tienen body
            if hasattr(response, 'body') and response.body:
                import json
                return json.loads(response.body.decode('utf-8'))

            # Intentar acceder al body de la response
            # Nota: Esto puede no funcionar para todos los tipos de response
            logger.warning("Unable to extract data from response type: %s", type(response))
            return None

        except Exception as e:
            logger.error(f"Error extracting response data: {e}")
            return None

    async def _create_formatted_response(self, serialized: SerializationResult,
                                       format_type: SerializationFormat, status_code: int,
                                       original_headers: Dict[str, str]) -> Response:
        """Crear response en el formato especificado."""
        mime_type = self.FORMAT_MIME_TYPES[format_type]

        # Crear headers
        headers = dict(original_headers)
        headers["content-type"] = mime_type
        headers["x-serialization-format"] = format_type.value

        if serialized.schema_hash:
            headers["x-schema-hash"] = serialized.schema_hash

        if serialized.compressed:
            headers["content-encoding"] = "deflate"  # O el algoritmo usado

        # Metadata adicional
        if serialized.metadata:
            headers["x-serialization-size"] = str(serialized.metadata.get("size", len(serialized.data)))

        # Crear response
        return Response(
            content=serialized.data,
            status_code=status_code,
            headers=headers,
            media_type=mime_type
        )

    def _get_endpoint_schema(self, path: str, direction: str) -> Optional[Dict[str, Any]]:
        """Obtener esquema para un endpoint específico."""
        key = f"{path}:{direction}"
        return self.endpoint_schemas.get(key)

    def register_endpoint_schema(self, path: str, request_schema: Optional[Dict[str, Any]] = None,
                               response_schema: Optional[Dict[str, Any]] = None):
        """Registrar esquemas para un endpoint específico."""
        if request_schema:
            self.endpoint_schemas[f"{path}:request"] = request_schema
        if response_schema:
            self.endpoint_schemas[f"{path}:response"] = response_schema

        logger.info(f"📋 Registered schemas for endpoint {path}")

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del middleware."""
        stats = self.stats.copy()

        # Calcular métricas adicionales
        if stats["conversion_times"]:
            stats["avg_conversion_time"] = sum(stats["conversion_times"]) / len(stats["conversion_times"])
            stats["max_conversion_time"] = max(stats["conversion_times"])
            stats["min_conversion_time"] = min(stats["conversion_times"])

        # Calcular tasas de error
        if stats["requests_processed"] > 0:
            stats["error_rate"] = stats["errors"] / stats["requests_processed"]
            stats["conversion_rate"] = stats["conversions_performed"] / stats["requests_processed"]

        return stats

    def update_feature_flags(self, flags: Dict[str, bool]):
        """Actualizar feature flags en runtime."""
        self.feature_flags.update(flags)
        logger.info(f"🔧 Updated feature flags: {self.feature_flags}")


# Instancia global del middleware
_negotiation_middleware = None

def get_content_negotiation_middleware(feature_flags: Optional[Dict[str, bool]] = None) -> ContentNegotiationMiddleware:
    """Obtener instancia global del middleware de negociación de contenido."""
    global _negotiation_middleware
    if _negotiation_middleware is None:
        _negotiation_middleware = ContentNegotiationMiddleware(None, feature_flags)
    return _negotiation_middleware

def create_content_negotiation_middleware(feature_flags: Optional[Dict[str, bool]] = None) -> ContentNegotiationMiddleware:
    """Crear nueva instancia del middleware de negociación de contenido."""
    return ContentNegotiationMiddleware(None, feature_flags)


# Utilidades para integración con FastAPI
def setup_content_negotiation(app, feature_flags: Optional[Dict[str, bool]] = None,
                            endpoint_schemas: Optional[Dict[str, Dict[str, Any]]] = None):
    """
    Configurar negociación de contenido en una aplicación FastAPI.

    Args:
        app: Instancia de FastAPI
        feature_flags: Flags para controlar funcionalidades
        endpoint_schemas: Esquemas por endpoint (path -> {"request": schema, "response": schema})
    """
    middleware = ContentNegotiationMiddleware(app, feature_flags)

    # Registrar esquemas si se proporcionan
    if endpoint_schemas:
        for path, schemas in endpoint_schemas.items():
            middleware.register_endpoint_schema(
                path,
                schemas.get("request"),
                schemas.get("response")
            )

    # Agregar middleware a la app
    app.add_middleware(ContentNegotiationMiddleware, feature_flags=feature_flags)

    logger.info("✅ Content negotiation configured for FastAPI app")
    return middleware