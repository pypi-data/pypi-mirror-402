"""
API Gateway principal para AILOOS.
Punto de entrada unificado para todas las APIs del sistema.
"""

import asyncio
import time
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx

from .config import get_config
from .state_manager import get_state_manager, ComponentStatus
from .event_system import get_event_bus, publish_api_event
from ..utils.logging import get_logger
from ..coordinator.auth.dependencies import get_current_user, get_current_admin


class APIGateway:
    """
    Gateway principal que enruta requests a las APIs especializadas.
    Proporciona autenticación, rate limiting, logging y monitoreo unificado.
    """

    def __init__(self):
        self.config = get_config()
        self.logger = get_logger(__name__)
        self.state_manager = get_state_manager()
        self.event_bus = get_event_bus()

        # Cliente HTTP para proxy
        self.http_client = httpx.AsyncClient(timeout=30.0)

        # Mapeo de rutas a servicios
        self.service_routes = {
            "/api/compliance": f"http://localhost:{self.config.api.compliance_port}",
            "/api/federated": f"http://localhost:{self.config.api.federated_port}",
            "/api/marketplace": f"http://localhost:{self.config.api.marketplace_port}",
            "/api/wallet": f"http://localhost:{self.config.api.wallet_port}",
            "/api/dashboard": f"http://localhost:{self.config.api.dashboard_port}",
        }

        # Estadísticas
        self.stats = {
            "requests_total": 0,
            "requests_success": 0,
            "requests_error": 0,
            "response_time_avg": 0.0,
            "start_time": time.time()
        }

        # Crear aplicación FastAPI
        self.app = self._create_app()

        self.logger.info("API Gateway inicializado")

    def _create_app(self) -> FastAPI:
        """Crear aplicación FastAPI del gateway."""
        app = FastAPI(
            title="AILOOS API Gateway",
            description="Gateway unificado para todas las APIs de AILOOS",
            version="1.0.0"
        )

        # Configurar CORS
        if self.config.api.enable_cors:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=self.config.api.cors_origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

        # Middleware de logging y métricas
        @app.middleware("http")
        async def log_requests(request: Request, call_next):
            start_time = time.time()

            # Procesar request
            try:
                response = await call_next(request)
                process_time = time.time() - start_time

                # Log de request exitoso
                self._log_request(request, response.status_code, process_time)

                # Publicar evento
                await publish_api_event(
                    request.url.path,
                    request.method,
                    response.status_code,
                    process_time
                )

                return response

            except Exception as e:
                process_time = time.time() - start_time
                self._log_request(request, 500, process_time)
                raise

        # Rutas del gateway
        @app.get("/health")
        async def gateway_health():
            """Health check del gateway."""
            return await self._get_gateway_health()

        @app.get("/api/status")
        async def system_status():
            """Estado general del sistema."""
            return self.state_manager.get_system_status()

        @app.get("/api/routes")
        async def list_routes():
            """Listar rutas disponibles."""
            return {
                "routes": list(self.service_routes.keys()),
                "services": self.service_routes
            }

        # Proxy para todas las rutas de API
        @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
        async def proxy_request(request: Request, path: str):
            """Proxy requests a servicios backend."""
            return await self._proxy_request(request, path)

        # Manejo explícito de OPTIONS para CORS preflight
        @app.options("/{path:path}")
        async def handle_options(request: Request, path: str):
            """Manejar OPTIONS requests para CORS preflight."""
            return Response(status_code=200)

        return app

    async def _proxy_request(self, request: Request, path: str) -> Response:
        """Proxy un request a la API correspondiente."""
        # Determinar servicio destino
        target_service = self._get_target_service(path)
        if not target_service:
            raise HTTPException(status_code=404, detail="Servicio no encontrado")

        # Construir URL destino
        target_url = f"{target_service}{request.url.path}"
        if request.url.query:
            target_url += f"?{request.url.query}"

        try:
            # Preparar request
            headers = dict(request.headers)
            # Remover headers que no deben forwardearse
            headers.pop("host", None)

            # Forward request
            response = await self.http_client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=await request.body(),
                timeout=30.0
            )

            # Crear response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )

        except httpx.TimeoutException:
            self.logger.error(f"Timeout proxying request to {target_service}")
            raise HTTPException(status_code=504, detail="Gateway timeout")
        except httpx.RequestError as e:
            self.logger.error(f"Error proxying request to {target_service}: {e}")
            raise HTTPException(status_code=502, detail="Bad gateway")

    def _get_target_service(self, path: str) -> Optional[str]:
        """Determinar servicio destino basado en la ruta."""
        for route_prefix, service_url in self.service_routes.items():
            if path.startswith(route_prefix):
                return service_url
        return None

    def _log_request(self, request: Request, status_code: int, duration: float):
        """Log de request con métricas."""
        self.stats["requests_total"] += 1

        if 200 <= status_code < 400:
            self.stats["requests_success"] += 1
        else:
            self.stats["requests_error"] += 1

        # Actualizar promedio de tiempo de respuesta
        self.stats["response_time_avg"] = (
            (self.stats["response_time_avg"] * (self.stats["requests_total"] - 1)) + duration
        ) / self.stats["requests_total"]

        # Log estructurado
        self.logger.info(
            f"API Gateway: {request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_ms=duration * 1000,
            user_agent=request.headers.get("user-agent", "unknown"),
            remote_addr=self._get_client_ip(request)
        )

    def _get_client_ip(self, request: Request) -> str:
        """Obtener IP del cliente."""
        # Check for forwarded headers
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fallback to direct client
        client = request.client
        return client.host if client else "unknown"

    async def _get_gateway_health(self) -> Dict[str, Any]:
        """Obtener estado de salud del gateway."""
        # Verificar conectividad con servicios backend
        service_health = {}
        for route, url in self.service_routes.items():
            try:
                # Intentar health check básico
                health_url = url.replace("/api/", "/health")
                response = await self.http_client.get(health_url, timeout=5.0)
                service_health[route] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds()
                }
            except Exception:
                service_health[route] = {"status": "unreachable"}

        return {
            "status": "healthy",
            "timestamp": time.time(),
            "uptime_seconds": time.time() - self.stats["start_time"],
            "services": service_health,
            "stats": self.stats
        }

    async def start_gateway(self, host: str = "0.0.0.0", port: int = 8000):
        """Iniciar el API Gateway."""
        import uvicorn

        # Registrar componente en state manager
        self.state_manager.register_component("api_gateway", {
            "host": host,
            "port": port,
            "services": list(self.service_routes.keys())
        })

        # Iniciar event bus
        await self.event_bus.start()

        self.logger.info(f"Iniciando API Gateway en {host}:{port}")

        # Configurar uvicorn
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)

        try:
            # Actualizar estado
            self.state_manager.update_component_status("api_gateway", ComponentStatus.RUNNING)

            await server.serve()
        finally:
            # Cleanup
            await self.http_client.aclose()
            await self.event_bus.stop()
            self.state_manager.update_component_status("api_gateway", ComponentStatus.STOPPED)

    def get_app(self) -> FastAPI:
        """Obtener aplicación FastAPI."""
        return self.app

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del gateway."""
        return self.stats.copy()


# Instancia global del gateway
_gateway_instance: Optional[APIGateway] = None


def get_api_gateway() -> APIGateway:
    """Obtener instancia global del API Gateway."""
    global _gateway_instance

    if _gateway_instance is None:
        _gateway_instance = APIGateway()

    return _gateway_instance


# Función de conveniencia para iniciar el gateway
async def start_api_gateway(host: str = "0.0.0.0", port: int = 8000):
    """Iniciar el API Gateway."""
    gateway = get_api_gateway()
    await gateway.start_gateway(host, port)


# Middleware de autenticación para rutas protegidas
async def require_api_access(request: Request, user: dict = Depends(get_current_user)):
    """Middleware para verificar acceso a APIs."""
    # Aquí se podría implementar lógica adicional de autorización
    # basada en roles, permisos, rate limiting, etc.
    return user


# Función helper para crear rutas autenticadas
def create_authenticated_route(method: str, path: str, endpoint, **kwargs):
    """Crear ruta autenticada en el gateway."""
    gateway = get_api_gateway()

    # Añadir dependencia de autenticación
    dependencies = kwargs.get("dependencies", [])
    dependencies.append(Depends(require_api_access))
    kwargs["dependencies"] = dependencies

    # Registrar ruta
    gateway.app.add_api_route(path, endpoint, methods=[method], **kwargs)