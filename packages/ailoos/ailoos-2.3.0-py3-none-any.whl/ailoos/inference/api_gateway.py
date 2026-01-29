"""
APIGateway - Gateway principal con routing inteligente para EmpoorioLM
Punto de entrada unificado para todas las operaciones de inferencia y gestión de modelos.
"""

import asyncio
import logging
import time
import json
import hashlib
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import aiohttp
from aiohttp import web
import jwt
from enum import Enum

from .load_balancer import LoadBalancer
from .model_registry import ModelRegistry
from .model_lifecycle_manager import ModelLifecycleManager, Environment
from .authentication_manager import AuthenticationManager
from .authorization_manager import AuthorizationManager
from .rate_limiter import RateLimiter
from .audit_logger import AuditLogger

logger = logging.getLogger(__name__)


class APIVersion(Enum):
    """Versiones de API soportadas."""
    V1 = "v1"
    V2 = "v2"


class RequestPriority(Enum):
    """Prioridades de request."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class GatewayConfig:
    """Configuración del API Gateway."""
    host: str = "0.0.0.0"
    port: int = 8080
    api_version: APIVersion = APIVersion.V1
    enable_cors: bool = True
    enable_metrics: bool = True
    request_timeout: float = 300.0
    max_request_size: int = 10 * 1024 * 1024  # 10MB

    # Configuración de seguridad
    enable_authentication: bool = True
    enable_authorization: bool = True
    enable_rate_limiting: bool = True
    enable_audit_logging: bool = True

    # Configuración de routing
    default_model_timeout: float = 60.0
    streaming_timeout: float = 600.0  # 10 minutos para streaming

    # Configuración de circuit breaker
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout: int = 60

    # Configuración de cache
    enable_response_cache: bool = True
    cache_ttl_seconds: int = 300  # 5 minutos


@dataclass
class GatewayRequest:
    """Request procesada por el gateway."""
    request_id: str
    client_ip: str
    user_id: Optional[str]
    model_name: str
    method: str
    path: str
    headers: Dict[str, str]
    query_params: Dict[str, str]
    body: Any
    priority: RequestPriority
    timestamp: datetime
    api_version: APIVersion

    # Metadata de procesamiento
    authenticated: bool = False
    authorized: bool = False
    rate_limited: bool = False
    cached_response: Optional[Any] = None


@dataclass
class GatewayResponse:
    """Response del gateway."""
    status_code: int
    headers: Dict[str, str]
    body: Any
    processing_time: float
    cached: bool = False
    error_message: Optional[str] = None


class APIGateway:
    """
    API Gateway principal para EmpoorioLM.

    Características:
    - Routing inteligente basado en modelos y versiones
    - Autenticación y autorización integrada
    - Rate limiting por usuario/organización
    - Load balancing inteligente
    - Caching de responses
    - Circuit breaker pattern
    - Logging de auditoría completo
    - Métricas y monitoreo
    - Soporte para streaming
    """

    def __init__(
        self,
        config: GatewayConfig,
        model_registry: ModelRegistry,
        lifecycle_manager: ModelLifecycleManager,
        load_balancer: LoadBalancer
    ):
        self.config = config
        self.model_registry = model_registry
        self.lifecycle_manager = lifecycle_manager
        self.load_balancer = load_balancer

        # Componentes de seguridad
        self.auth_manager: Optional[AuthenticationManager] = None
        self.authz_manager: Optional[AuthorizationManager] = None
        self.rate_limiter: Optional[RateLimiter] = None
        self.audit_logger: Optional[AuditLogger] = None

        # Cache de responses
        self.response_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_timestamps: Dict[str, float] = {}

        # Servidor web
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None

        # Métricas
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0,
            'rate_limited_requests': 0,
            'cached_responses': 0,
            'auth_failures': 0,
            'active_connections': 0
        }

        # Callbacks
        self.on_request_processed: Optional[Callable[[GatewayRequest, GatewayResponse], Awaitable[None]]] = None

        logger.info(f"🚪 API Gateway inicializado en {config.host}:{config.port}")

    async def initialize_security_components(self) -> None:
        """Inicializar componentes de seguridad."""
        if self.config.enable_authentication:
            from .authentication_manager import AuthenticationManager
            self.auth_manager = AuthenticationManager()

        if self.config.enable_authorization:
            from .authorization_manager import AuthorizationManager
            self.authz_manager = AuthorizationManager()

        if self.config.enable_rate_limiting:
            from .rate_limiter import RateLimiter
            self.rate_limiter = RateLimiter()

        if self.config.enable_audit_logging:
            from .audit_logger import AuditLogger
            self.audit_logger = AuditLogger()

        logger.info("🔐 Componentes de seguridad inicializados")

    async def create_application(self) -> web.Application:
        """Crear aplicación web FastAPI/AIOHTTP."""
        self.app = web.Application(
            middlewares=[
                self._cors_middleware,
                self._logging_middleware,
                self._metrics_middleware
            ]
        )

        # Configurar rutas
        self._setup_routes()

        # Configurar cleanup
        self.app.on_startup.append(self._on_startup)
        self.app.on_shutdown.append(self._on_shutdown)

        return self.app

    def _setup_routes(self) -> None:
        """Configurar rutas de la API."""
        # Health check
        self.app.router.add_get("/health", self._health_check_handler)
        self.app.router.add_get("/api/v1/health", self._health_check_handler)
        self.app.router.add_get("/api/v2/health", self._health_check_handler)

        # Model management
        self.app.router.add_get("/api/v1/models", self._list_models_handler)
        self.app.router.add_post("/api/v1/models", self._register_model_handler)
        self.app.router.add_get("/api/v1/models/{model_name}", self._get_model_handler)
        self.app.router.add_put("/api/v1/models/{model_name}", self._update_model_handler)
        self.app.router.add_delete("/api/v1/models/{model_name}", self._delete_model_handler)

        # Inference endpoints
        self.app.router.add_post("/api/v1/inference/{model_name}", self._inference_handler)
        self.app.router.add_post("/api/v1/inference/{model_name}/stream", self._streaming_inference_handler)

        # Batch inference
        self.app.router.add_post("/api/v1/batch/{model_name}", self._batch_inference_handler)

        # Model lifecycle
        self.app.router.add_post("/api/v1/models/{model_name}/promote", self._promote_model_handler)
        self.app.router.add_post("/api/v1/models/{model_name}/rollback", self._rollback_model_handler)

        # Metrics and monitoring
        self.app.router.add_get("/api/v1/metrics", self._metrics_handler)
        self.app.router.add_get("/api/v1/models/{model_name}/metrics", self._model_metrics_handler)

        # Admin endpoints
        self.app.router.add_get("/api/v1/admin/status", self._admin_status_handler)
        self.app.router.add_post("/api/v1/admin/cache/clear", self._clear_cache_handler)

    async def _on_startup(self, app: web.Application) -> None:
        """Handler de startup."""
        await self.initialize_security_components()
        await self.load_balancer.start_background_tasks()

        logger.info("🚀 API Gateway iniciado correctamente")

    async def _on_shutdown(self, app: web.Application) -> None:
        """Handler de shutdown."""
        await self.load_balancer.stop_background_tasks()

        if self.runner:
            await self.runner.cleanup()

        logger.info("⏹️ API Gateway detenido")

    # Middleware
    @web.middleware
    async def _cors_middleware(self, request: web.Request, handler):
        """Middleware CORS."""
        if not self.config.enable_cors:
            return await handler(request)

        response = await handler(request)

        response.headers.update({
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-API-Key'
        })

        return response

    @web.middleware
    async def _logging_middleware(self, request: web.Request, handler):
        """Middleware de logging."""
        start_time = time.time()
        self.metrics['active_connections'] += 1

        try:
            response = await handler(request)
            processing_time = time.time() - start_time

            logger.info(f"{request.method} {request.path} - {response.status} - {processing_time:.3f}s")
            return response

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"{request.method} {request.path} - ERROR - {processing_time:.3f}s - {e}")
            raise

        finally:
            self.metrics['active_connections'] -= 1

    @web.middleware
    async def _metrics_middleware(self, request: web.Request, handler):
        """Middleware de métricas."""
        if not self.config.enable_metrics:
            return await handler(request)

        self.metrics['total_requests'] += 1
        start_time = time.time()

        try:
            response = await handler(request)
            processing_time = time.time() - start_time

            # Actualizar métricas promedio
            prev_avg = self.metrics['avg_response_time']
            total_reqs = self.metrics['total_requests']
            self.metrics['avg_response_time'] = (prev_avg * (total_reqs - 1) + processing_time) / total_reqs

            if 200 <= response.status < 400:
                self.metrics['successful_requests'] += 1
            else:
                self.metrics['failed_requests'] += 1

            return response

        except Exception:
            self.metrics['failed_requests'] += 1
            raise

    # Route handlers
    async def _health_check_handler(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': self.config.api_version.value,
            'components': {
                'model_registry': 'healthy',
                'lifecycle_manager': 'healthy',
                'load_balancer': 'healthy',
                'authentication': 'healthy' if not self.config.enable_authentication else ('healthy' if self.auth_manager else 'unhealthy'),
                'rate_limiting': 'healthy' if not self.config.enable_rate_limiting else ('healthy' if self.rate_limiter else 'unhealthy')
            }
        }

        return web.json_response(health_status)

    async def _list_models_handler(self, request: web.Request) -> web.Response:
        """Listar modelos disponibles."""
        gateway_request = await self._parse_request(request)

        # Verificar autenticación y autorización
        if not await self._authenticate_request(gateway_request):
            return web.json_response({'error': 'Authentication failed'}, status=401)

        if not await self._authorize_request(gateway_request, 'models:list'):
            return web.json_response({'error': 'Authorization failed'}, status=403)

        # Obtener modelos
        models = await self.model_registry.list_models()

        response_data = {
            'models': [{
                'name': model.name,
                'version': model.version,
                'status': model.status.value,
                'description': model.description,
                'created_at': model.created_at.isoformat(),
                'tags': model.tags
            } for model in models]
        }

        await self._log_audit_event(gateway_request, 'models:list', True)
        return web.json_response(response_data)

    async def _inference_handler(self, request: web.Request) -> web.Response:
        """Handler principal de inferencia."""
        gateway_request = await self._parse_request(request)
        model_name = request.match_info['model_name']

        # Verificar autenticación y autorización
        if not await self._authenticate_request(gateway_request):
            return web.json_response({'error': 'Authentication failed'}, status=401)

        if not await self._authorize_request(gateway_request, f'models:{model_name}:inference'):
            return web.json_response({'error': 'Authorization failed'}, status=403)

        # Verificar rate limiting
        if not await self._check_rate_limit(gateway_request):
            self.metrics['rate_limited_requests'] += 1
            return web.json_response({'error': 'Rate limit exceeded'}, status=429)

        # Verificar cache
        cache_key = self._generate_cache_key(gateway_request)
        if self.config.enable_response_cache:
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                self.metrics['cached_responses'] += 1
                await self._log_audit_event(gateway_request, 'inference:cached', True)
                return web.json_response(cached_response, status=200)

        try:
            # Routing inteligente
            instance_id = await self.load_balancer.select_instance(
                model_name,
                gateway_request.client_ip,
                gateway_request.user_id
            )

            if not instance_id:
                return web.json_response({'error': 'No available instances'}, status=503)

            # Forward request
            response_data = await self._forward_inference_request(
                instance_id, gateway_request
            )

            # Cache response
            if self.config.enable_response_cache:
                self._cache_response(cache_key, response_data)

            await self._log_audit_event(gateway_request, 'inference:success', True)
            return web.json_response(response_data)

        except Exception as e:
            logger.error(f"Error in inference: {e}")
            await self._log_audit_event(gateway_request, 'inference:error', False, str(e))
            return web.json_response({'error': 'Inference failed'}, status=500)

    async def _streaming_inference_handler(self, request: web.Request) -> web.StreamingResponse:
        """Handler de inferencia con streaming."""
        gateway_request = await self._parse_request(request)
        model_name = request.match_info['model_name']

        # Verificaciones de seguridad (igual que inference regular)
        if not await self._authenticate_request(gateway_request):
            return web.json_response({'error': 'Authentication failed'}, status=401)

        if not await self._authorize_request(gateway_request, f'models:{model_name}:inference'):
            return web.json_response({'error': 'Authorization failed'}, status=403)

        if not await self._check_rate_limit(gateway_request):
            return web.json_response({'error': 'Rate limit exceeded'}, status=429)

        # Streaming response
        async def generate():
            try:
                instance_id = await self.load_balancer.select_instance(
                    model_name, gateway_request.client_ip, gateway_request.user_id
                )

                if not instance_id:
                    yield f"data: {json.dumps({'error': 'No available instances'})}\n\n"
                    return

                # Forward streaming request
                async for chunk in self._forward_streaming_request(instance_id, gateway_request):
                    yield chunk

            except Exception as e:
                logger.error(f"Error in streaming inference: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return web.StreamingResponse(
            generate(),
            content_type='text/plain',
            headers={'Cache-Control': 'no-cache'}
        )

    # Métodos auxiliares
    async def _parse_request(self, request: web.Request) -> GatewayRequest:
        """Parsear request HTTP a GatewayRequest."""
        body = await request.read()
        body_data = None
        if body:
            try:
                body_data = json.loads(body.decode('utf-8'))
            except:
                body_data = body.decode('utf-8')

        # Extraer user_id de JWT si está presente
        user_id = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            try:
                token = auth_header[7:]
                payload = jwt.decode(token, options={"verify_signature": False})
                user_id = payload.get('sub')
            except:
                pass

        return GatewayRequest(
            request_id=request.headers.get('X-Request-ID', f"req_{int(time.time())}"),
            client_ip=self._get_client_ip(request),
            user_id=user_id,
            model_name=request.match_info.get('model_name', ''),
            method=request.method,
            path=str(request.path),
            headers=dict(request.headers),
            query_params=dict(request.query),
            body=body_data,
            priority=RequestPriority.NORMAL,
            timestamp=datetime.now(),
            api_version=self.config.api_version
        )

    def _get_client_ip(self, request: web.Request) -> str:
        """Obtener IP real del cliente."""
        # Check common proxy headers
        for header in ['X-Forwarded-For', 'X-Real-IP', 'CF-Connecting-IP']:
            ip = request.headers.get(header)
            if ip:
                return ip.split(',')[0].strip()

        # Fallback to peer name
        peer_name = request.transport.get_extra_info('peername')
        return peer_name[0] if peer_name else 'unknown'

    async def _authenticate_request(self, gateway_request: GatewayRequest) -> bool:
        """Autenticar request."""
        if not self.config.enable_authentication or not self.auth_manager:
            return True

        try:
            # Implementar lógica de autenticación
            return await self.auth_manager.authenticate(gateway_request)
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    async def _authorize_request(self, gateway_request: GatewayRequest, permission: str) -> bool:
        """Autorizar request."""
        if not self.config.enable_authorization or not self.authz_manager:
            return True

        try:
            return await self.authz_manager.authorize(gateway_request, permission)
        except Exception as e:
            logger.error(f"Authorization error: {e}")
            return False

    async def _check_rate_limit(self, gateway_request: GatewayRequest) -> bool:
        """Verificar rate limiting."""
        if not self.config.enable_rate_limiting or not self.rate_limiter:
            return True

        try:
            return await self.rate_limiter.check_limit(gateway_request)
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            return False

    async def _log_audit_event(
        self,
        gateway_request: GatewayRequest,
        action: str,
        success: bool,
        details: str = None
    ) -> None:
        """Log event de auditoría."""
        if not self.config.enable_audit_logging or not self.audit_logger:
            return

        try:
            await self.audit_logger.log_event(
                user_id=gateway_request.user_id,
                action=action,
                resource=f"model:{gateway_request.model_name}",
                success=success,
                details=details,
                ip_address=gateway_request.client_ip,
                user_agent=gateway_request.headers.get('User-Agent')
            )
        except Exception as e:
            logger.error(f"Audit logging error: {e}")

    def _generate_cache_key(self, gateway_request: GatewayRequest) -> str:
        """Generar clave de cache para request."""
        # Crear hash determinístico basado en contenido relevante
        cache_content = {
            'model': gateway_request.model_name,
            'method': gateway_request.method,
            'path': gateway_request.path,
            'query': gateway_request.query_params,
            'body': gateway_request.body
        }

        content_str = json.dumps(cache_content, sort_keys=True)
        return hashlib.md5(content_str.encode()).hexdigest()

    def _get_cached_response(self, cache_key: str) -> Optional[Any]:
        """Obtener response cacheada."""
        if cache_key in self.response_cache:
            cached_data = self.response_cache[cache_key]
            cache_time = self.cache_timestamps.get(cache_key, 0)

            # Verificar TTL
            if time.time() - cache_time < self.config.cache_ttl_seconds:
                return cached_data

            # Cache expirado, limpiar
            del self.response_cache[cache_key]
            del self.cache_timestamps[cache_key]

        return None

    def _cache_response(self, cache_key: str, response_data: Any) -> None:
        """Cachear response."""
        self.response_cache[cache_key] = response_data
        self.cache_timestamps[cache_key] = time.time()

    async def _forward_inference_request(
        self,
        instance_id: str,
        gateway_request: GatewayRequest
    ) -> Dict[str, Any]:
        """Forward request a instancia específica."""
        # Construir URL destino (asumiendo instance_id es base URL o host:port)
        base_url = instance_id if instance_id.startswith("http") else f"http://{instance_id}"
        url = f"{base_url}/api/v1/internal/inference"

        timeout = aiohttp.ClientTimeout(total=self.config.default_model_timeout)
        
        start_time = time.time()
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    url, 
                    json=gateway_request.body,
                    headers={"X-Request-ID": gateway_request.request_id}
                ) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        raise Exception(f"Instance error {response.status}: {error_text}")
                    
                    result = await response.json()
                    
                    # Añadir metadata de procesamiento del gateway
                    result['gateway_processing_time'] = time.time() - start_time
                    return result

        except asyncio.TimeoutError:
            logger.error(f"Timeout forwarding to {instance_id}")
            raise Exception("Inference request timed out")
        except Exception as e:
            logger.error(f"Error forwarding to {instance_id}: {e}")
            raise

    async def _forward_streaming_request(
        self,
        instance_id: str,
        gateway_request: GatewayRequest
    ):
        """Forward streaming request."""
        base_url = instance_id if instance_id.startswith("http") else f"http://{instance_id}"
        url = f"{base_url}/api/v1/internal/inference/stream"
        
        timeout = aiohttp.ClientTimeout(total=self.config.streaming_timeout)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    url, 
                    json=gateway_request.body,
                    headers={"X-Request-ID": gateway_request.request_id}
                ) as response:
                    
                    if response.status >= 400:
                        error_text = await response.text()
                        yield f"data: {json.dumps({'error': f'Instance error {response.status}: {error_text}'})}\n\n"
                        return

                    # Reenviar chunks del stream
                    async for chunk in response.content.iter_any():
                        if chunk:
                            yield chunk

        except Exception as e:
            logger.error(f"Error forwarding stream to {instance_id}: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    async def start_server(self) -> None:
        """Iniciar servidor."""
        if not self.app:
            self.app = await self.create_application()

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        self.site = web.TCPSite(self.runner, self.config.host, self.config.port)
        await self.site.start()

        logger.info(f"🌐 API Gateway listening on {self.config.host}:{self.config.port}")

    async def stop_server(self) -> None:
        """Detener servidor."""
        if self.site:
            await self.site.stop()

        if self.runner:
            await self.runner.cleanup()

        logger.info("🛑 API Gateway stopped")

    def get_gateway_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del gateway."""
        return {
            'metrics': self.metrics.copy(),
            'config': {
                'host': self.config.host,
                'port': self.config.port,
                'api_version': self.config.api_version.value,
                'enable_authentication': self.config.enable_authentication,
                'enable_rate_limiting': self.config.enable_rate_limiting
            },
            'cache_size': len(self.response_cache)
        }