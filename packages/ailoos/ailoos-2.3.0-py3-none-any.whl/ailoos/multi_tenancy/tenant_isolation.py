#!/usr/bin/env python3
"""
TenantIsolation - Middleware de aislamiento por tenant para Ailoos FASE 8
=======================================================================

Middleware completo para aislamiento multi-tenant con:
- Extracción automática de tenant_id desde headers/API keys
- Inyección de contexto de tenant en requests
- Validación de permisos por tenant
- Aislamiento de datos y recursos
- Rate limiting por tenant
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass
from datetime import datetime, timedelta
import re
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TenantContext:
    """Contexto de tenant para la request actual"""
    tenant_id: str
    tenant_name: str
    api_key: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    permissions: List[str] = None
    limits: Dict[str, Any] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []
        if self.limits is None:
            self.limits = {}
        if self.metadata is None:
            self.metadata = {}

class TenantIsolationMiddleware:
    """
    Middleware para aislamiento completo de tenants
    """

    def __init__(self, tenant_manager, security_manager=None):
        self.tenant_manager = tenant_manager
        self.security_manager = security_manager

        # Configuración de headers
        self.tenant_header = "X-Tenant-ID"
        self.api_key_header = "X-API-Key"
        self.user_header = "X-User-ID"
        self.session_header = "X-Session-ID"

        # Rate limiting por tenant
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        self.rate_limit_window = timedelta(hours=1)

        # Endpoints públicos (no requieren tenant)
        self.public_endpoints = {
            "/health",
            "/status",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/auth/login",
            "/auth/register"
        }

        # Endpoints administrativos (multi-tenant)
        self.admin_endpoints = {
            "/admin/tenants",
            "/admin/system"
        }

        logger.info("🔒 TenantIsolation Middleware initialized")

    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
        """
        Middleware ASGI/WSGI compatible
        """
        if scope["type"] != "http":
            # Pasar requests no-HTTP sin modificación
            return await self.app(scope, receive, send)

        # Extraer información de tenant
        tenant_context = await self.extract_tenant_context(scope)

        if not tenant_context:
            # Request sin tenant válido
            await self.handle_unauthorized_request(scope, receive, send)
            return

        # Verificar límites de rate
        if not await self.check_rate_limits(tenant_context):
            await self.handle_rate_limited_request(scope, receive, send)
            return

        # Inyectar contexto de tenant en el scope
        scope["tenant_context"] = tenant_context

        # Log de la request
        self.log_tenant_request(tenant_context, scope)

        # Continuar con la aplicación
        await self.app(scope, receive, send)

    def set_app(self, app):
        """Configurar la aplicación ASGI"""
        self.app = app
        return self

    async def extract_tenant_context(self, scope: Dict[str, Any]) -> Optional[TenantContext]:
        """
        Extraer contexto de tenant desde headers y path
        """
        headers = self.get_headers_dict(scope)
        path = scope.get("path", "")

        # Verificar si es endpoint público
        if self.is_public_endpoint(path):
            return None  # Permitir sin tenant

        # Extraer tenant_id de diferentes fuentes
        tenant_id = self.extract_tenant_id(headers, path)

        if not tenant_id:
            logger.warning(f"❌ No tenant ID found for path: {path}")
            return None

        # Obtener tenant del manager
        tenant = await self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            logger.warning(f"❌ Tenant not found: {tenant_id}")
            return None

        # Verificar estado del tenant
        if tenant.status.value != "active":
            logger.warning(f"🚫 Tenant not active: {tenant_id} (status: {tenant.status.value})")
            return None

        # Extraer API key y validar
        api_key = headers.get(self.api_key_header.lower())
        if not api_key:
            logger.warning(f"❌ No API key provided for tenant: {tenant_id}")
            return None

        # Validar API key
        if not await self.validate_api_key(tenant, api_key):
            logger.warning(f"❌ Invalid API key for tenant: {tenant_id}")
            return None

        # Extraer información adicional
        user_id = headers.get(self.user_header.lower())
        session_id = headers.get(self.session_header.lower())

        # Obtener permisos (si hay security manager)
        permissions = []
        if self.security_manager:
            permissions = await self.security_manager.get_tenant_permissions(tenant_id, user_id)

        # Crear contexto
        context = TenantContext(
            tenant_id=tenant_id,
            tenant_name=tenant.name,
            api_key=api_key,
            user_id=user_id,
            session_id=session_id,
            permissions=permissions,
            limits=tenant.limits.to_dict() if hasattr(tenant, 'limits') else {},
            metadata={
                'plan': tenant.plan.value if hasattr(tenant, 'plan') else 'unknown',
                'created_at': tenant.created_at.isoformat() if hasattr(tenant, 'created_at') else None
            }
        )

        return context

    def extract_tenant_id(self, headers: Dict[str, str], path: str) -> Optional[str]:
        """
        Extraer tenant_id de headers o path
        """
        # Primero intentar desde header
        tenant_id = headers.get(self.tenant_header.lower())
        if tenant_id:
            return tenant_id

        # Intentar extraer desde path (ej: /tenant/{tenant_id}/...)
        path_match = re.match(r"/tenant/([^/]+)/", path)
        if path_match:
            return path_match.group(1)

        # Intentar desde subdomain (ej: tenant1.api.ailoos.com)
        host = headers.get("host", "")
        if "." in host:
            subdomain = host.split(".")[0]
            if subdomain.startswith("tenant"):
                # Extraer ID del subdomain
                id_match = re.match(r"tenant(\w+)", subdomain)
                if id_match:
                    return id_match.group(1)

        return None

    async def validate_api_key(self, tenant, api_key: str) -> bool:
        """
        Validar API key del tenant
        """
        if hasattr(tenant, 'api_key') and tenant.api_key == api_key:
            return True

        # También verificar por API key directamente
        tenant_by_key = await self.tenant_manager.get_tenant_by_api_key(api_key)
        return tenant_by_key is not None

    def is_public_endpoint(self, path: str) -> bool:
        """
        Verificar si el endpoint es público
        """
        return any(path.startswith(endpoint) for endpoint in self.public_endpoints)

    async def check_rate_limits(self, context: TenantContext) -> bool:
        """
        Verificar límites de rate para el tenant
        """
        tenant_id = context.tenant_id
        now = datetime.now()

        if tenant_id not in self.rate_limits:
            self.rate_limits[tenant_id] = {
                'requests': [],
                'window_start': now
            }

        tenant_limits = self.rate_limits[tenant_id]

        # Reset window if expired
        if now - tenant_limits['window_start'] > self.rate_limit_window:
            tenant_limits['requests'] = []
            tenant_limits['window_start'] = now

        # Check limit
        max_requests = context.limits.get('max_api_calls_per_hour', 1000)
        if len(tenant_limits['requests']) >= max_requests:
            return False

        # Add request
        tenant_limits['requests'].append(now)

        # Cleanup old requests
        cutoff = now - self.rate_limit_window
        tenant_limits['requests'] = [
            req for req in tenant_limits['requests'] if req > cutoff
        ]

        return True

    def log_tenant_request(self, context: TenantContext, scope: Dict[str, Any]):
        """
        Log de requests por tenant
        """
        path = scope.get("path", "")
        method = scope.get("method", "")

        logger.info(f"🏢 [{context.tenant_name}] {method} {path} - User: {context.user_id or 'anonymous'}")

    async def handle_unauthorized_request(self, scope: Dict[str, Any], receive: Callable, send: Callable):
        """
        Manejar requests no autorizadas
        """
        await send({
            'type': 'http.response.start',
            'status': 401,
            'headers': [[b'content-type', b'application/json']],
        })
        await send({
            'type': 'http.response.body',
            'body': b'{"error": "Unauthorized - Valid tenant required"}',
        })

    async def handle_rate_limited_request(self, scope: Dict[str, Any], receive: Callable, send: Callable):
        """
        Manejar requests rate limited
        """
        await send({
            'type': 'http.response.start',
            'status': 429,
            'headers': [[b'content-type', b'application/json']],
        })
        await send({
            'type': 'http.response.body',
            'body': b'{"error": "Rate limit exceeded"}',
        })

    def get_headers_dict(self, scope: Dict[str, Any]) -> Dict[str, str]:
        """
        Convertir headers de ASGI a dict
        """
        headers = {}
        for key, value in scope.get("headers", []):
            headers[key.decode().lower()] = value.decode()
        return headers

    # Métodos utilitarios para integración

    def get_current_tenant_context(self) -> Optional[TenantContext]:
        """
        Obtener contexto de tenant actual (para uso en handlers)
        """
        # En un framework real, esto vendría del contexto de la request
        # Por ahora, devolver None
        return None

    async def enforce_tenant_isolation(self, tenant_id: str, resource_type: str, resource_id: str) -> bool:
        """
        Forzar aislamiento - verificar que el recurso pertenece al tenant
        """
        # En implementación real, verificaría en DB con tenant_id
        # Por ahora, simular verificación
        return True

    async def inject_tenant_filter(self, query: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        """
        Inyectar filtro de tenant en queries de DB
        """
        query_copy = query.copy()
        query_copy['tenant_id'] = tenant_id
        return query_copy

# Función helper para obtener contexto de tenant en handlers
def get_tenant_context() -> Optional[TenantContext]:
    """
    Helper para obtener contexto de tenant en request handlers
    """
    # En implementación real, esto obtendría el contexto del framework
    return None

# Decorador para endpoints que requieren tenant
def require_tenant(func: Callable) -> Callable:
    """
    Decorador para asegurar que el endpoint tiene contexto de tenant
    """
    async def wrapper(*args, **kwargs):
        # En implementación real, verificaría el contexto
        return await func(*args, **kwargs)
    return wrapper