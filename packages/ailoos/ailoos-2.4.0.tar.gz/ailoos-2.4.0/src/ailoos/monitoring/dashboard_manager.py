"""
Dashboard Manager for AILOOS - Unified Dashboard Coordination System
Provides centralized management and coordination of all monitoring dashboards.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable, Type
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import jwt
import uvicorn

from ..core.logging import get_logger
from ..core.config import get_config
from ..core.state_manager import get_state_manager
from ..core.event_system import get_event_system
from ..coordinator.auth.dependencies import get_current_user, require_admin
from ..notifications.service import NotificationService

# Importar dashboards
from .executive_dashboard import ExecutiveDashboard
from .technical_dashboard import TechnicalDashboard
from .security_dashboard import SecurityDashboard
from .federated_learning_dashboard import FederatedLearningDashboard

logger = get_logger(__name__)


class DashboardType(Enum):
    """Tipos de dashboards disponibles."""
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    SECURITY = "security"
    FEDERATED_LEARNING = "federated_learning"


class UserRole(Enum):
    """Roles de usuario del sistema."""
    ADMIN = "admin"
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    SECURITY = "security"
    RESEARCHER = "researcher"
    VIEWER = "viewer"


@dataclass
class DashboardInstance:
    """Instancia de dashboard."""
    dashboard_type: DashboardType
    instance: Any
    is_active: bool = True
    last_health_check: float = 0.0
    health_status: str = "unknown"
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemOverview:
    """Vista general del sistema."""
    total_dashboards: int = 0
    active_dashboards: int = 0
    total_websocket_connections: int = 0
    system_health_score: float = 0.0
    last_system_update: float = 0.0
    active_alerts: int = 0
    system_uptime: float = 0.0
    total_users: int = 0
    active_sessions: int = 0


@dataclass
class DashboardConfig:
    """Configuración del Dashboard Manager."""
    title: str = "AILOOS Unified Dashboard System"
    host: str = "0.0.0.0"
    port: int = 8000
    jwt_secret: str = "dashboard-manager-secret"
    jwt_expiration_hours: int = 24
    enable_cors: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    health_check_interval: float = 30.0
    max_websocket_connections: int = 1000
    enable_metrics_collection: bool = True
    log_level: str = "INFO"


class DashboardManager:
    """
    Gestor unificado de dashboards para AILOOS.
    Coordina todas las instancias de dashboards, proporciona autenticación centralizada,
    y ofrece una interfaz unificada para monitoreo del sistema.
    """

    def __init__(self, config: DashboardConfig = None):
        self.config = config or DashboardConfig()

        # Configurar logging
        logging.getLogger().setLevel(getattr(logging, self.config.log_level))

        # Integración con sistemas centrales
        self.global_config = get_config()
        self.state_manager = get_state_manager()
        self.event_system = get_event_system()

        # Servicios
        self.notification_service = None

        # Estado del manager
        self.is_running = False
        self.start_time = 0.0
        self.last_health_check = 0.0

        # Dashboards gestionados
        self.dashboards: Dict[DashboardType, DashboardInstance] = {}

        # Gestión de usuarios y sesiones
        self.active_users: Dict[str, Dict[str, Any]] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}

        # Sistema de eventos
        self.event_handlers: Dict[str, List[Callable]] = {}

        # FastAPI application
        self.app = FastAPI(
            title=self.config.title,
            description="Unified dashboard management system for AILOOS monitoring",
            version="1.0.0"
        )

        # Configurar aplicación
        self._setup_middleware()
        self._setup_routes()
        self._setup_event_handlers()

        logger.info("🎛️ DashboardManager initialized")

    def _setup_middleware(self):
        """Configurar middleware."""
        if self.config.enable_cors:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=self.config.cors_origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

    def _setup_routes(self):
        """Configurar rutas del Dashboard Manager."""

        # Rutas públicas
        self.app.get("/")(self.render_main_dashboard)
        self.app.get("/login")(self.render_login)
        self.app.post("/api/auth/login")(self.login)
        self.app.get("/health")(self.health_check)

        # Rutas de dashboards individuales
        self.app.get("/executive")(self.render_executive_dashboard)
        self.app.get("/technical")(self.render_technical_dashboard)
        self.app.get("/security")(self.render_security_dashboard)
        self.app.get("/federated")(self.render_federated_dashboard)

        # API unificada
        self.app.get("/api/dashboard/overview")(self.get_system_overview)
        self.app.get("/api/dashboard/{dashboard_type}/status")(self.get_dashboard_status)
        self.app.post("/api/dashboard/{dashboard_type}/start")(self.start_dashboard)
        self.app.post("/api/dashboard/{dashboard_type}/stop")(self.stop_dashboard)
        self.app.get("/api/dashboard/metrics")(self.get_unified_metrics)

        # Gestión de usuarios
        self.app.get("/api/users/active")(self.get_active_users)
        self.app.post("/api/users/{user_id}/logout")(self.logout_user)

        # WebSocket unificado
        self.app.websocket("/ws/dashboard")(self.unified_websocket)

        # Administración
        self.app.get("/admin")(self.render_admin_dashboard)
        self.app.get("/api/admin/system/status")(self.get_system_status)
        self.app.post("/api/admin/system/restart")(self.restart_system)

    def _setup_event_handlers(self):
        """Configurar manejadores de eventos."""
        # Registrar eventos del sistema
        self.event_system.subscribe("system.health_check", self._handle_system_health_event)
        self.event_system.subscribe("dashboard.alert", self._handle_dashboard_alert_event)
        self.event_system.subscribe("user.session_created", self._handle_user_session_event)
        self.event_system.subscribe("user.session_ended", self._handle_user_session_event)

    async def initialize_dashboards(self):
        """Inicializar todos los dashboards."""
        logger.info("🔧 Initializing dashboards...")

        # Executive Dashboard
        try:
            executive_dashboard = ExecutiveDashboard(
                notification_service=self.notification_service,
                jwt_secret=self.config.jwt_secret
            )
            self.dashboards[DashboardType.EXECUTIVE] = DashboardInstance(
                dashboard_type=DashboardType.EXECUTIVE,
                instance=executive_dashboard,
                config={"update_interval": 60.0}
            )
            logger.info("✅ Executive Dashboard initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Executive Dashboard: {e}")

        # Technical Dashboard
        try:
            technical_dashboard = TechnicalDashboard(
                monitoring_level="detailed",
                update_interval=5.0
            )
            self.dashboards[DashboardType.TECHNICAL] = DashboardInstance(
                dashboard_type=DashboardType.TECHNICAL,
                instance=technical_dashboard,
                config={"update_interval": 5.0}
            )
            logger.info("✅ Technical Dashboard initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Technical Dashboard: {e}")

        # Security Dashboard
        try:
            security_dashboard = SecurityDashboard(
                notification_service=self.notification_service,
                jwt_secret=self.config.jwt_secret
            )
            self.dashboards[DashboardType.SECURITY] = DashboardInstance(
                dashboard_type=DashboardType.SECURITY,
                instance=security_dashboard,
                config={"update_interval": 30.0}
            )
            logger.info("✅ Security Dashboard initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Security Dashboard: {e}")

        # Federated Learning Dashboard
        try:
            federated_dashboard = FederatedLearningDashboard(
                jwt_secret=self.config.jwt_secret,
                update_interval=10.0
            )
            self.dashboards[DashboardType.FEDERATED_LEARNING] = DashboardInstance(
                dashboard_type=DashboardType.FEDERATED_LEARNING,
                instance=federated_dashboard,
                config={"update_interval": 10.0}
            )
            logger.info("✅ Federated Learning Dashboard initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Federated Learning Dashboard: {e}")

    async def start_all_dashboards(self):
        """Iniciar todos los dashboards."""
        logger.info("🚀 Starting all dashboards...")

        for dashboard_type, dashboard_instance in self.dashboards.items():
            try:
                if hasattr(dashboard_instance.instance, 'start_monitoring'):
                    await dashboard_instance.instance.start_monitoring()
                    dashboard_instance.is_active = True
                    logger.info(f"✅ {dashboard_type.value} dashboard started")
                else:
                    logger.warning(f"⚠️ {dashboard_type.value} dashboard has no start_monitoring method")
            except Exception as e:
                logger.error(f"❌ Failed to start {dashboard_type.value} dashboard: {e}")
                dashboard_instance.is_active = False

    async def stop_all_dashboards(self):
        """Detener todos los dashboards."""
        logger.info("🛑 Stopping all dashboards...")

        for dashboard_type, dashboard_instance in self.dashboards.items():
            try:
                if hasattr(dashboard_instance.instance, 'stop_monitoring'):
                    await dashboard_instance.instance.stop_monitoring()
                    dashboard_instance.is_active = False
                    logger.info(f"✅ {dashboard_type.value} dashboard stopped")
            except Exception as e:
                logger.error(f"❌ Failed to stop {dashboard_type.value} dashboard: {e}")

    async def start_manager(self):
        """Iniciar el Dashboard Manager."""
        if self.is_running:
            return

        self.is_running = True
        self.start_time = asyncio.get_event_loop().time()

        logger.info("🎛️ Starting Dashboard Manager...")

        # Inicializar dashboards
        await self.initialize_dashboards()

        # Iniciar dashboards
        await self.start_all_dashboards()

        # Iniciar monitoreo del sistema
        asyncio.create_task(self._system_monitoring_loop())

        logger.info("✅ Dashboard Manager started successfully")

    async def stop_manager(self):
        """Detener el Dashboard Manager."""
        if not self.is_running:
            return

        self.is_running = False
        logger.info("🛑 Stopping Dashboard Manager...")

        # Detener todos los dashboards
        await self.stop_all_dashboards()

        # Cerrar conexiones WebSocket
        for websocket in self.websocket_connections.values():
            try:
                await websocket.close()
            except:
                pass

        self.websocket_connections.clear()
        logger.info("✅ Dashboard Manager stopped")

    async def _system_monitoring_loop(self):
        """Loop de monitoreo del sistema."""
        while self.is_running:
            try:
                await self._perform_health_checks()
                await self._update_system_overview()
                await self._cleanup_expired_sessions()

                self.last_health_check = asyncio.get_event_loop().time()

            except Exception as e:
                logger.error(f"❌ Error in system monitoring loop: {e}")

            await asyncio.sleep(self.config.health_check_interval)

    async def _perform_health_checks(self):
        """Realizar verificaciones de salud de todos los dashboards."""
        current_time = asyncio.get_event_loop().time()

        for dashboard_type, dashboard_instance in self.dashboards.items():
            try:
                if hasattr(dashboard_instance.instance, 'get_health_status'):
                    health_status = await dashboard_instance.instance.get_health_status()
                    dashboard_instance.health_status = health_status.get("is_running", False) and "healthy" or "unhealthy"
                else:
                    dashboard_instance.health_status = "unknown"

                dashboard_instance.last_health_check = current_time

            except Exception as e:
                logger.error(f"❌ Health check failed for {dashboard_type.value}: {e}")
                dashboard_instance.health_status = "error"

    async def _update_system_overview(self):
        """Actualizar vista general del sistema."""
        # Esta información se calcula dinámicamente en get_system_overview
        pass

    async def _cleanup_expired_sessions(self):
        """Limpiar sesiones expiradas."""
        current_time = asyncio.get_event_loop().time()
        expired_users = []

        for user_id, user_data in self.active_users.items():
            last_activity = user_data.get("last_activity", 0)
            if current_time - last_activity > (self.config.jwt_expiration_hours * 3600):
                expired_users.append(user_id)

        for user_id in expired_users:
            del self.active_users[user_id]
            logger.info(f"🧹 Cleaned up expired session for user: {user_id}")

    # Event Handlers
    async def _handle_system_health_event(self, event_data: Dict[str, Any]):
        """Manejar eventos de salud del sistema."""
        logger.info(f"🏥 System health event: {event_data}")

    async def _handle_dashboard_alert_event(self, event_data: Dict[str, Any]):
        """Manejar eventos de alertas de dashboards."""
        logger.warning(f"🚨 Dashboard alert: {event_data}")

        # Reenviar a notificaciones si está disponible
        if self.notification_service:
            try:
                await self.notification_service.send_system_alert(event_data)
            except Exception as e:
                logger.error(f"Failed to send system alert: {e}")

    async def _handle_user_session_event(self, event_data: Dict[str, Any]):
        """Manejar eventos de sesiones de usuario."""
        event_type = event_data.get("event_type")
        user_id = event_data.get("user_id")

        if event_type == "session_created":
            self.active_users[user_id] = {
                "login_time": event_data.get("timestamp"),
                "last_activity": event_data.get("timestamp"),
                "roles": event_data.get("roles", [])
            }
        elif event_type == "session_ended":
            if user_id in self.active_users:
                del self.active_users[user_id]

    # Authentication
    def _create_jwt_token(self, user_id: str, roles: List[str]) -> str:
        """Crear token JWT."""
        expiration = datetime.utcnow() + timedelta(hours=self.config.jwt_expiration_hours)

        payload = {
            "user_id": user_id,
            "username": user_id,  # Para compatibilidad
            "roles": roles,
            "exp": expiration.timestamp(),
            "iat": datetime.utcnow().timestamp(),
            "iss": "ailoos-dashboard-manager"
        }

        return jwt.encode(payload, self.config.jwt_secret, algorithm="HS256")

    def _validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validar token JWT."""
        try:
            payload = jwt.decode(token, self.config.jwt_secret, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    # Route Handlers
    async def render_main_dashboard(self, request: Request) -> HTMLResponse:
        """Renderizar dashboard principal."""
        return HTMLResponse(self._get_main_dashboard_html())

    async def render_login(self, request: Request) -> HTMLResponse:
        """Renderizar página de login."""
        return HTMLResponse(self._get_login_html())

    async def login(self, request: Request) -> Dict[str, Any]:
        """Procesar login."""
        try:
            data = await request.json()
            username = data.get("username")
            password = data.get("password")

            # Validación básica (en producción usar sistema de auth real)
            user_roles = self._authenticate_user(username, password)
            if not user_roles:
                raise HTTPException(status_code=401, detail="Credenciales inválidas")

            # Crear token
            token = self._create_jwt_token(username, user_roles)

            # Registrar sesión
            self.active_users[username] = {
                "login_time": asyncio.get_event_loop().time(),
                "last_activity": asyncio.get_event_loop().time(),
                "roles": user_roles
            }

            # Emitir evento
            await self.event_system.publish("user.session_created", {
                "user_id": username,
                "roles": user_roles,
                "timestamp": asyncio.get_event_loop().time()
            })

            return {
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "username": username,
                    "roles": user_roles
                }
            }

        except Exception as e:
            logger.error(f"Error in login: {e}")
            raise HTTPException(status_code=500, detail="Error interno del servidor")

    def _authenticate_user(self, username: str, password: str) -> Optional[List[str]]:
        """Autenticar usuario (simplificado)."""
        # Usuarios de prueba
        test_users = {
            "admin": {"password": "admin", "roles": ["admin", "executive", "technical", "security", "researcher"]},
            "ceo": {"password": "ceo", "roles": ["executive", "viewer"]},
            "cto": {"password": "cto", "roles": ["executive", "technical", "viewer"]},
            "cso": {"password": "cso", "roles": ["executive", "security", "viewer"]},
            "researcher": {"password": "researcher", "roles": ["researcher", "viewer"]},
            "operator": {"password": "operator", "roles": ["technical", "viewer"]},
            "analyst": {"password": "analyst", "roles": ["viewer"]}
        }

        user_data = test_users.get(username)
        if user_data and user_data["password"] == password:
            return user_data["roles"]

        return None

    async def render_executive_dashboard(self, request: Request, user: dict = Depends(get_current_user)) -> HTMLResponse:
        """Renderizar dashboard ejecutivo."""
        if "executive" not in user.get("roles", []) and "admin" not in user.get("roles", []):
            raise HTTPException(status_code=403, detail="Acceso no autorizado")

        return HTMLResponse(self._get_executive_dashboard_html(user))

    async def render_technical_dashboard(self, request: Request, user: dict = Depends(get_current_user)) -> HTMLResponse:
        """Renderizar dashboard técnico."""
        if "technical" not in user.get("roles", []) and "admin" not in user.get("roles", []):
            raise HTTPException(status_code=403, detail="Acceso no autorizado")

        return HTMLResponse(self._get_technical_dashboard_html(user))

    async def render_security_dashboard(self, request: Request, user: dict = Depends(get_current_user)) -> HTMLResponse:
        """Renderizar dashboard de seguridad."""
        if "security" not in user.get("roles", []) and "admin" not in user.get("roles", []):
            raise HTTPException(status_code=403, detail="Acceso no autorizado")

        return HTMLResponse(self._get_security_dashboard_html(user))

    async def render_federated_dashboard(self, request: Request, user: dict = Depends(get_current_user)) -> HTMLResponse:
        """Renderizar dashboard federated learning."""
        if "researcher" not in user.get("roles", []) and "admin" not in user.get("roles", []):
            raise HTTPException(status_code=403, detail="Acceso no autorizado")

        return HTMLResponse(self._get_federated_dashboard_html(user))

    async def render_admin_dashboard(self, request: Request, user: dict = Depends(require_admin)) -> HTMLResponse:
        """Renderizar dashboard de administración."""
        return HTMLResponse(self._get_admin_dashboard_html(user))

    async def get_system_overview(self, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
        """Obtener vista general del sistema."""
        total_dashboards = len(self.dashboards)
        active_dashboards = len([d for d in self.dashboards.values() if d.is_active])
        total_connections = len(self.websocket_connections)
        active_alerts = sum([len(d.instance.executive_alerts) for d in self.dashboards.values()
                           if hasattr(d.instance, 'executive_alerts') and d.instance.executive_alerts], [])

        # Calcular health score
        health_scores = []
        for dashboard in self.dashboards.values():
            if dashboard.health_status == "healthy":
                health_scores.append(100)
            elif dashboard.health_status == "unhealthy":
                health_scores.append(50)
            else:
                health_scores.append(0)

        system_health = sum(health_scores) / len(health_scores) if health_scores else 0

        return {
            "total_dashboards": total_dashboards,
            "active_dashboards": active_dashboards,
            "total_websocket_connections": total_connections,
            "system_health_score": round(system_health, 2),
            "last_system_update": self.last_health_check,
            "active_alerts": active_alerts,
            "system_uptime": round(asyncio.get_event_loop().time() - self.start_time, 2),
            "total_users": len(self.active_users),
            "active_sessions": len(self.active_users),
            "timestamp": asyncio.get_event_loop().time()
        }

    async def get_dashboard_status(self, dashboard_type: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
        """Obtener estado de un dashboard específico."""
        try:
            dashboard_enum = DashboardType(dashboard_type)
            if dashboard_enum not in self.dashboards:
                raise HTTPException(status_code=404, detail="Dashboard no encontrado")

            dashboard = self.dashboards[dashboard_enum]

            return {
                "dashboard_type": dashboard_type,
                "is_active": dashboard.is_active,
                "health_status": dashboard.health_status,
                "last_health_check": dashboard.last_health_check,
                "config": dashboard.config,
                "timestamp": asyncio.get_event_loop().time()
            }

        except ValueError:
            raise HTTPException(status_code=400, detail="Tipo de dashboard inválido")

    async def start_dashboard(self, dashboard_type: str, user: dict = Depends(require_admin)) -> Dict[str, Any]:
        """Iniciar un dashboard específico."""
        try:
            dashboard_enum = DashboardType(dashboard_type)
            if dashboard_enum not in self.dashboards:
                raise HTTPException(status_code=404, detail="Dashboard no encontrado")

            dashboard = self.dashboards[dashboard_enum]

            if hasattr(dashboard.instance, 'start_monitoring'):
                await dashboard.instance.start_monitoring()
                dashboard.is_active = True

            return {"message": f"Dashboard {dashboard_type} iniciado"}

        except ValueError:
            raise HTTPException(status_code=400, detail="Tipo de dashboard inválido")

    async def stop_dashboard(self, dashboard_type: str, user: dict = Depends(require_admin)) -> Dict[str, Any]:
        """Detener un dashboard específico."""
        try:
            dashboard_enum = DashboardType(dashboard_type)
            if dashboard_enum not in self.dashboards:
                raise HTTPException(status_code=404, detail="Dashboard no encontrado")

            dashboard = self.dashboards[dashboard_enum]

            if hasattr(dashboard.instance, 'stop_monitoring'):
                await dashboard.instance.stop_monitoring()
                dashboard.is_active = False

            return {"message": f"Dashboard {dashboard_type} detenido"}

        except ValueError:
            raise HTTPException(status_code=400, detail="Tipo de dashboard inválido")

    async def get_unified_metrics(self, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
        """Obtener métricas unificadas de todos los dashboards."""
        unified_metrics = {}

        for dashboard_type, dashboard_instance in self.dashboards.items():
            try:
                if hasattr(dashboard_instance.instance, 'get_comprehensive_status'):
                    metrics = await dashboard_instance.instance.get_comprehensive_status()
                    unified_metrics[dashboard_type.value] = metrics
                elif hasattr(dashboard_instance.instance, 'get_dashboard_data'):
                    metrics = await dashboard_instance.instance.get_dashboard_data()
                    unified_metrics[dashboard_type.value] = metrics
            except Exception as e:
                logger.error(f"Error getting metrics for {dashboard_type.value}: {e}")
                unified_metrics[dashboard_type.value] = {"error": str(e)}

        return {
            "unified_metrics": unified_metrics,
            "timestamp": asyncio.get_event_loop().time()
        }

    async def get_active_users(self, user: dict = Depends(require_admin)) -> Dict[str, Any]:
        """Obtener usuarios activos."""
        return {
            "active_users": self.active_users,
            "total_active": len(self.active_users),
            "timestamp": asyncio.get_event_loop().time()
        }

    async def logout_user(self, user_id: str, admin: dict = Depends(require_admin)) -> Dict[str, Any]:
        """Forzar logout de usuario."""
        if user_id in self.active_users:
            del self.active_users[user_id]

            # Cerrar conexiones WebSocket del usuario
            connections_to_close = [ws for uid, ws in self.websocket_connections.items() if uid == user_id]
            for websocket in connections_to_close:
                try:
                    await websocket.close()
                except:
                    pass

            # Emitir evento
            await self.event_system.publish("user.session_ended", {
                "user_id": user_id,
                "timestamp": asyncio.get_event_loop().time()
            })

            return {"message": f"Usuario {user_id} desconectado"}
        else:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

    async def unified_websocket(self, websocket: WebSocket, user: dict = Depends(get_current_user)):
        """WebSocket unificado para todos los dashboards."""
        client_id = user.get("username")
        await websocket.accept()
        self.websocket_connections[client_id] = websocket

        logger.info(f"📡 Unified WebSocket connected: {client_id}")

        try:
            # Enviar datos iniciales
            overview = await self.get_system_overview(user)
            await websocket.send_json({
                "type": "initial_overview",
                "data": overview
            })

            # Mantener conexión
            while True:
                try:
                    message = await asyncio.wait_for(
                        websocket.receive_json(),
                        timeout=60.0
                    )

                    await self._handle_unified_websocket_message(websocket, client_id, message, user)

                except asyncio.TimeoutError:
                    # Enviar actualización periódica
                    overview = await self.get_system_overview(user)
                    await websocket.send_json({
                        "type": "system_update",
                        "data": overview
                    })

        except WebSocketDisconnect:
            logger.info(f"📡 Unified WebSocket disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Unified WebSocket error for {client_id}: {e}")
        finally:
            if client_id in self.websocket_connections:
                del self.websocket_connections[client_id]

    async def _handle_unified_websocket_message(self, websocket: WebSocket, client_id: str,
                                              message: Dict[str, Any], user: dict):
        """Manejar mensajes WebSocket unificados."""
        try:
            message_type = message.get("type", "unknown")

            if message_type == "subscribe_dashboard":
                dashboard_type = message.get("dashboard_type")
                try:
                    dashboard_enum = DashboardType(dashboard_type)
                    if dashboard_enum in self.dashboards:
                        dashboard = self.dashboards[dashboard_enum]
                        if hasattr(dashboard.instance, 'get_dashboard_data'):
                            data = await dashboard.instance.get_dashboard_data()
                            await websocket.send_json({
                                "type": "dashboard_data",
                                "dashboard_type": dashboard_type,
                                "data": data
                            })
                except ValueError:
                    pass

            elif message_type == "request_metrics":
                metrics = await self.get_unified_metrics(user)
                await websocket.send_json({
                    "type": "unified_metrics",
                    "data": metrics
                })

        except Exception as e:
            logger.error(f"Error handling unified WebSocket message: {e}")
            await websocket.send_json({
                "type": "error",
                "message": f"Error processing message: {e}"
            })

    async def get_system_status(self, user: dict = Depends(require_admin)) -> Dict[str, Any]:
        """Obtener estado completo del sistema."""
        return {
            "manager_status": {
                "is_running": self.is_running,
                "start_time": self.start_time,
                "uptime": round(asyncio.get_event_loop().time() - self.start_time, 2),
                "last_health_check": self.last_health_check
            },
            "dashboards_status": {
                dashboard_type.value: {
                    "is_active": instance.is_active,
                    "health_status": instance.health_status,
                    "last_health_check": instance.last_health_check
                }
                for dashboard_type, instance in self.dashboards.items()
            },
            "connections": {
                "websocket_connections": len(self.websocket_connections),
                "active_users": len(self.active_users)
            },
            "timestamp": asyncio.get_event_loop().time()
        }

    async def restart_system(self, user: dict = Depends(require_admin)) -> Dict[str, Any]:
        """Reiniciar todo el sistema de dashboards."""
        try:
            logger.info("🔄 Restarting dashboard system...")

            # Detener todo
            await self.stop_manager()

            # Pequeña pausa
            await asyncio.sleep(2)

            # Reiniciar
            await self.start_manager()

            return {"message": "Sistema de dashboards reiniciado exitosamente"}

        except Exception as e:
            logger.error(f"Error restarting system: {e}")
            return {"error": f"Error al reiniciar sistema: {e}"}

    async def health_check(self) -> Dict[str, Any]:
        """Health check del sistema."""
        return {
            "status": "healthy" if self.is_running else "unhealthy",
            "timestamp": asyncio.get_event_loop().time(),
            "uptime": round(asyncio.get_event_loop().time() - self.start_time, 2) if self.is_running else 0
        }

    # HTML Templates (simplified for brevity)
    def _get_main_dashboard_html(self) -> str:
        """Obtener HTML del dashboard principal."""
        return f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{self.config.title}</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-100 min-h-screen">
            <div class="container mx-auto px-4 py-8">
                <h1 class="text-4xl font-bold text-center mb-8">{self.config.title}</h1>
                <div class="text-center">
                    <a href="/login" class="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600">Acceder al Sistema</a>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_login_html(self) -> str:
        """Obtener HTML de login."""
        return """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Login - AILOOS Dashboard</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-100 min-h-screen flex items-center justify-center">
            <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
                <h1 class="text-2xl font-bold text-center mb-6">AILOOS Dashboard</h1>
                <form id="loginForm" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Usuario</label>
                        <input type="text" id="username" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Contraseña</label>
                        <input type="password" id="password" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md">
                    </div>
                    <button type="submit" class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700">
                        Iniciar Sesión
                    </button>
                </form>
                <div id="message" class="mt-4 text-center text-sm text-red-600 hidden"></div>
                <div class="mt-6 text-center text-sm text-gray-600">
                    <p>Usuarios de prueba:</p>
                    <p>admin/admin, ceo/ceo, cto/cto, cso/cso, researcher/researcher</p>
                </div>
            </div>
            <script>
                document.getElementById('loginForm').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    const username = document.getElementById('username').value;
                    const password = document.getElementById('password').value;
                    const messageDiv = document.getElementById('message');

                    try {
                        const response = await fetch('/api/auth/login', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ username, password })
                        });

                        const data = await response.json();

                        if (response.ok) {
                            localStorage.setItem('token', data.access_token);
                            window.location.href = '/executive';
                        } else {
                            messageDiv.textContent = data.detail || 'Error en login';
                            messageDiv.classList.remove('hidden');
                        }
                    } catch (error) {
                        messageDiv.textContent = 'Error de conexión';
                        messageDiv.classList.remove('hidden');
                    }
                });
            </script>
        </body>
        </html>
        """

    def _get_executive_dashboard_html(self, user: dict) -> str:
        """Obtener HTML del dashboard ejecutivo."""
        return f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Executive Dashboard - AILOOS</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        </head>
        <body class="bg-gray-100 min-h-screen">
            <div class="container mx-auto px-4 py-8">
                <div class="flex justify-between items-center mb-8">
                    <h1 class="text-4xl font-bold">Executive Dashboard</h1>
                    <div class="text-right">
                        <p class="text-gray-600">Usuario: {user.get('username')}</p>
                        <button onclick="logout()" class="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">Logout</button>
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8" id="kpi-cards">
                    <!-- KPIs will be loaded dynamically -->
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="bg-white p-6 rounded-lg shadow">
                        <h3 class="text-lg font-semibold mb-4">Strategic Metrics</h3>
                        <canvas id="strategicChart"></canvas>
                    </div>
                    <div class="bg-white p-6 rounded-lg shadow">
                        <h3 class="text-lg font-semibold mb-4">Active Alerts</h3>
                        <div id="alerts-list"></div>
                    </div>
                </div>
            </div>

            <script>
                let strategicChart;

                async function loadExecutiveData() {{
                    try {{
                        const token = localStorage.getItem('token');
                        const response = await fetch('/api/dashboard/executive/status', {{
                            headers: {{ 'Authorization': `Bearer ${{token}}` }}
                        }});

                        if (response.ok) {{
                            const data = await response.json();
                            updateExecutiveDashboard(data);
                        }} else if (response.status === 401) {{
                            window.location.href = '/login';
                        }}
                    }} catch (error) {{
                        console.error('Error loading executive data:', error);
                    }}
                }}

                function updateExecutiveDashboard(data) {{
                    // Update KPIs
                    const kpiContainer = document.getElementById('kpi-cards');
                    kpiContainer.innerHTML = `
                        <div class="bg-white p-6 rounded-lg shadow">
                            <h3 class="text-lg font-semibold mb-2">Total ROI</h3>
                            <p class="text-3xl font-bold text-green-600">${{data.business_kpis?.total_roi || 0}}%</p>
                        </div>
                        <div class="bg-white p-6 rounded-lg shadow">
                            <h3 class="text-lg font-semibold mb-2">System Uptime</h3>
                            <p class="text-3xl font-bold text-blue-600">${{data.business_kpis?.system_uptime_percentage || 0}}%</p>
                        </div>
                        <div class="bg-white p-6 rounded-lg shadow">
                            <h3 class="text-lg font-semibold mb-2">Active Sessions</h3>
                            <p class="text-3xl font-bold text-purple-600">${{data.federated_metrics?.active_sessions || 0}}</p>
                        </div>
                    `;

                    // Update alerts
                    const alertsContainer = document.getElementById('alerts-list');
                    const alerts = data.executive_alerts || [];
                    alertsContainer.innerHTML = alerts.slice(0, 5).map(alert =>
                        `<div class="p-2 border-l-4 border-red-500 mb-2">
                            <p class="font-semibold">${{alert.title}}</p>
                            <p class="text-sm text-gray-600">${{alert.description}}</p>
                        </div>`
                    ).join('');

                    // Update strategic chart
                    updateStrategicChart(data);
                }}

                function updateStrategicChart(data) {{
                    const ctx = document.getElementById('strategicChart');
                    if (strategicChart) strategicChart.destroy();

                    const strategic = data.strategic_metrics || {{}};
                    strategicChart = new Chart(ctx, {{
                        type: 'radar',
                        data: {{
                            labels: ['Market Penetration', 'Competitive Advantage', 'Innovation', 'Customer Satisfaction', 'Scalability'],
                            datasets: [{{
                                label: 'Strategic Metrics',
                                data: [
                                    strategic.market_penetration_percentage || 0,
                                    strategic.competitive_advantage_score || 0,
                                    strategic.innovation_index || 0,
                                    strategic.customer_satisfaction_score || 0,
                                    strategic.scalability_score || 0
                                ],
                                borderColor: 'rgba(54, 162, 235, 1)',
                                backgroundColor: 'rgba(54, 162, 235, 0.2)'
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            scales: {{
                                r: {{
                                    beginAtZero: true,
                                    max: 100
                                }}
                            }}
                        }}
                    }});
                }}

                function logout() {{
                    localStorage.removeItem('token');
                    window.location.href = '/';
                }}

                // Load data on page load and refresh every 60 seconds
                loadExecutiveData();
                setInterval(loadExecutiveData, 60000);
            </script>
        </body>
        </html>
        """

    # Simplified templates for other dashboards (would be more comprehensive in production)
    def _get_technical_dashboard_html(self, user: dict) -> str:
        return f"<h1>Technical Dashboard - {user.get('username')}</h1><p>Dashboard técnico en desarrollo...</p>"

    def _get_security_dashboard_html(self, user: dict) -> str:
        return f"<h1>Security Dashboard - {user.get('username')}</h1><p>Dashboard de seguridad en desarrollo...</p>"

    def _get_federated_dashboard_html(self, user: dict) -> str:
        return f"<h1>Federated Learning Dashboard - {user.get('username')}</h1><p>Dashboard FL en desarrollo...</p>"

    def _get_admin_dashboard_html(self, user: dict) -> str:
        return f"<h1>Admin Dashboard - {user.get('username')}</h1><p>Panel de administración...</p>"

    async def start_server(self, host: str = None, port: int = None):
        """Iniciar servidor del Dashboard Manager."""
        server_host = host or self.config.host
        server_port = port or self.config.port

        # Iniciar manager primero
        await self.start_manager()

        # Configurar uvicorn
        config = uvicorn.Config(
            app=self.app,
            host=server_host,
            port=server_port,
            log_level="info"
        )

        server = uvicorn.Server(config)
        logger.info(f"🚀 Dashboard Manager server starting on {server_host}:{server_port}")

        try:
            await server.serve()
        finally:
            await self.stop_manager()


# Función de conveniencia
def create_dashboard_manager(config: DashboardConfig = None) -> DashboardManager:
    """Crear instancia del Dashboard Manager."""
    return DashboardManager(config)


# Función para iniciar el sistema de dashboards
async def start_unified_dashboard_system(host: str = "0.0.0.0", port: int = 8000):
    """Función de conveniencia para iniciar el sistema unificado de dashboards."""
    manager = create_dashboard_manager(DashboardConfig(host=host, port=port))
    await manager.start_server(host, port)


if __name__ == "__main__":
    # Para testing
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "server":
        # Iniciar servidor
        asyncio.run(start_unified_dashboard_system())
    else:
        # Crear instancia para testing
        manager = create_dashboard_manager()
        print("✅ DashboardManager creado exitosamente")
        print(f"📊 Título: {manager.config.title}")
        print(f"🌐 Host:Port: {manager.config.host}:{manager.config.port}")
        print("🚀 Para iniciar servidor: python dashboard_manager.py server")