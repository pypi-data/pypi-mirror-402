"""
Dashboard unificado principal para AILOOS.
Integra dashboards de monitoreo, auditoría y federado en interfaz única.
"""

import asyncio
import json
import logging
import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import jwt
from pydantic import BaseModel

# Importar componentes existentes (lazy loading para evitar inicialización automática)
# from .dashboard import DashboardManager
# from ..auditing.dashboard import AuditDashboard
# from ..federated.coordinator import FederatedCoordinator
from ..coordinator.auth.dependencies import get_current_user, get_current_admin, require_admin
from ..core.config import get_config
from ..core.state_manager import get_state_manager
from ..rewards.dracma_manager import DRACMA_Manager

logger = logging.getLogger(__name__)


class UserSession(BaseModel):
    """Modelo para sesiones de usuario."""
    user_id: str
    username: str
    roles: List[str]
    permissions: List[str]
    login_time: datetime
    last_activity: datetime
    session_id: str


class DashboardConfig(BaseModel):
    """Configuración del dashboard unificado."""
    title: str = "AILOOS Unified Dashboard"
    refresh_interval: int = 30  # segundos
    max_sessions: int = 100
    jwt_secret: str = "your-secret-key-change-in-production"
    jwt_expiration: int = 24  # horas


class UnifiedDashboard:
    """
    Dashboard unificado que integra monitoreo, auditoría y federado.
    Proporciona interfaz web única con autenticación JWT y control de acceso.
    """

    def __init__(self, config: DashboardConfig = None):
        self.config = config or DashboardConfig()

        # Integración con sistemas centrales
        self.global_config = get_config()
        self.state_manager = get_state_manager()
        self.dracma_manager = DRACMA_Manager(self.global_config)

        # Cliente HTTP para APIs
        self.http_client = httpx.AsyncClient(timeout=10.0)

        # Componentes integrados (lazy loading)
        self._monitoring_dashboard = None
        self._audit_dashboard = None
        self._federated_coordinator = None

        # Gestión de sesiones
        self.active_sessions: Dict[str, UserSession] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}

        # Configuración FastAPI
        self.app = FastAPI(
            title=self.config.title,
            description="Dashboard unificado para monitoreo, auditoría y federado de AILOOS",
            version="1.0.0"
        )

        # Configurar middleware
        self._setup_middleware()

        # Configurar rutas
        self._setup_routes()

        # Templates embebidos en el código

        logger.info("✅ UnifiedDashboard inicializado con integración real")

    @property
    def monitoring_dashboard(self):
        """Obtener dashboard de monitoreo (lazy loading)."""
        if self._monitoring_dashboard is None:
            try:
                from .dashboard import DashboardManager
                self._monitoring_dashboard = DashboardManager()
            except Exception as e:
                logger.warning(f"No se pudo cargar DashboardManager: {e}")
                self._monitoring_dashboard = None
        return self._monitoring_dashboard

    @property
    def audit_dashboard(self):
        """Obtener dashboard de auditoría (lazy loading)."""
        if self._audit_dashboard is None:
            try:
                from ..auditing.dashboard import AuditDashboard
                self._audit_dashboard = AuditDashboard()
            except Exception as e:
                logger.warning(f"No se pudo cargar AuditDashboard: {e}")
                self._audit_dashboard = None
        return self._audit_dashboard

    @property
    def federated_coordinator(self):
        """Obtener coordinador federado (lazy loading)."""
        if self._federated_coordinator is None:
            try:
                from ..federated.coordinator import FederatedCoordinator
                self._federated_coordinator = FederatedCoordinator()
            except Exception as e:
                logger.warning(f"No se pudo cargar FederatedCoordinator: {e}")
                self._federated_coordinator = None
        return self._federated_coordinator

    def _setup_middleware(self):
        """Configurar middleware de la aplicación."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        """Configurar rutas del dashboard."""
        # Rutas públicas
        self.app.get("/")(self.render_dashboard)
        self.app.get("/login")(self.render_login)
        self.app.post("/api/auth/login")(self.login)

        # Rutas protegidas
        self.app.get("/dashboard")(self.render_dashboard_protected)
        self.app.get("/api/dashboard/data")(self.get_dashboard_data)
        self.app.websocket("/ws/dashboard")(self.websocket_endpoint)

        # Rutas de administración (solo admin)
        self.app.get("/admin/sessions")(self.get_active_sessions)
        self.app.post("/admin/sessions/{session_id}/terminate")(self.terminate_session)

    async def render_login(self, request: Request) -> HTMLResponse:
        """Renderizar página de login."""
        return HTMLResponse(self._get_login_html())

    async def login(self, request: Request) -> Dict[str, Any]:
        """Procesar login y generar token JWT."""
        try:
            data = await request.json()
            username = data.get("username")
            password = data.get("password")

            # Validación básica (en producción usar base de datos)
            if username == "admin" and password == "admin":
                roles = ["admin", "operator", "viewer"]
                permissions = ["read", "write", "admin"]
            elif username == "operator" and password == "operator":
                roles = ["operator", "viewer"]
                permissions = ["read", "write"]
            elif username == "viewer" and password == "viewer":
                roles = ["viewer"]
                permissions = ["read"]
            else:
                raise HTTPException(status_code=401, detail="Credenciales inválidas")

            # Crear token JWT
            token = self._create_jwt_token(username, roles, permissions)

            # Crear sesión
            session = UserSession(
                user_id=username,
                username=username,
                roles=roles,
                permissions=permissions,
                login_time=datetime.now(),
                last_activity=datetime.now(),
                session_id=f"session_{username}_{datetime.now().timestamp()}"
            )
            self.active_sessions[session.session_id] = session

            return {
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "username": username,
                    "roles": roles,
                    "permissions": permissions
                }
            }

        except Exception as e:
            logger.error(f"Error en login: {e}")
            raise HTTPException(status_code=500, detail="Error interno del servidor")

    def _create_jwt_token(self, username: str, roles: List[str], permissions: List[str]) -> str:
        """Crear token JWT para usuario."""
        expiration = datetime.utcnow() + timedelta(hours=self.config.jwt_expiration)

        payload = {
            "user_id": username,
            "username": username,
            "roles": roles,
            "permissions": permissions,
            "exp": expiration.timestamp(),
            "iat": datetime.utcnow().timestamp(),
            "iss": "ailoos-unified-dashboard"
        }

        return jwt.encode(payload, self.config.jwt_secret, algorithm="HS256")

    async def render_dashboard(self, request: Request) -> HTMLResponse:
        """Renderizar dashboard público (redirige a login si no autenticado)."""
        return HTMLResponse(self._get_login_html())

    async def render_dashboard_protected(self, user: dict = Depends(get_current_user)) -> HTMLResponse:
        """Renderizar dashboard protegido."""
        return HTMLResponse(self._get_dashboard_html(user))

    async def get_dashboard_data(self, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
        """Obtener datos agregados del dashboard."""
        try:
            # Verificar permisos
            if "viewer" not in user.get("roles", []):
                raise HTTPException(status_code=403, detail="Permisos insuficientes")

            # Agregar datos de diferentes componentes desde APIs reales
            monitoring_data = await self._get_monitoring_data()
            audit_data = await self._get_audit_data()
            federated_data = await self._get_federated_data()

            # Filtrar datos según rol del usuario
            user_roles = user.get("roles", [])
            filtered_data = self._filter_data_by_role({
                "monitoring": monitoring_data,
                "auditing": audit_data,
                "federated": federated_data,
                "timestamp": datetime.now().isoformat(),
                "user": {
                    "username": user.get("username"),
                    "roles": user_roles
                }
            }, user_roles)

            return filtered_data

        except Exception as e:
            logger.error(f"Error obteniendo datos del dashboard: {e}")
            raise HTTPException(status_code=500, detail="Error interno del servidor")

    async def _get_monitoring_data(self) -> Dict[str, Any]:
        """Obtener datos del dashboard de monitoreo desde APIs reales."""
        try:
            # Obtener datos del state manager (estado global del sistema)
            system_status = self.state_manager.get_system_status()

            # Intentar obtener datos adicionales de la API de monitoreo
            monitoring_data = {}
            try:
                # Llamar a la API de monitoreo a través del gateway
                gateway_url = f"http://localhost:{self.global_config.api.dashboard_port}"
                async with self.http_client as client:
                    response = await client.get(f"{gateway_url}/api/monitoring/stats", timeout=5.0)
                    if response.status_code == 200:
                        monitoring_data = response.json()
            except Exception as e:
                logger.warning(f"No se pudo obtener datos de API de monitoreo: {e}")

            # Combinar datos del state manager con datos específicos de monitoreo
            return {
                "system_health": system_status.get("system_health", "unknown"),
                "active_nodes": system_status.get("total_components", 0),
                "total_sessions": system_status.get("metrics", {}).get("federated_sessions_active", 0),
                "cpu_usage": system_status.get("metrics", {}).get("cpu_usage_percent", 0.0),
                "memory_usage": system_status.get("metrics", {}).get("memory_usage_mb", 0.0),
                "network_status": "operational" if system_status.get("system_health") == "healthy" else "degraded",
                "uptime_seconds": system_status.get("system_uptime_seconds", 0),
                "components_running": system_status.get("components_running", 0),
                "components_error": system_status.get("components_error", 0),
                "api_stats": monitoring_data
            }
        except Exception as e:
            logger.error(f"Error obteniendo datos de monitoreo: {e}")
            return {"error": "Datos de monitoreo no disponibles"}

    async def _get_audit_data(self) -> Dict[str, Any]:
        """Obtener datos de auditoría desde APIs reales."""
        try:
            # Obtener datos de la API de compliance a través del gateway
            audit_data = {}
            try:
                gateway_url = f"http://localhost:{self.global_config.api.dashboard_port}"
                async with self.http_client as client:
                    # Obtener estadísticas de logs ZK
                    response = await client.get(f"{gateway_url}/api/compliance/health", timeout=5.0)
                    if response.status_code == 200:
                        health_data = response.json()
                        audit_data.update({
                            "zk_logger_status": "healthy" if health_data.get("components", {}).get("zk_audit_logger") else "unavailable",
                            "oracle_auditor_status": "healthy" if health_data.get("components", {}).get("oracle_auditor") else "unavailable",
                            "sybil_protector_status": "healthy" if health_data.get("components", {}).get("sybil_protector") else "unavailable"
                        })
            except Exception as e:
                logger.warning(f"No se pudo obtener datos de API de compliance: {e}")

            # Datos simulados para métricas adicionales (hasta que se implemente en la API)
            return {
                "summary": {
                    "active_alerts": 0,  # TODO: Obtener de API real
                    "total_events_24h": 0,  # TODO: Obtener de API real
                    "compliance_violations": 0  # TODO: Obtener de API real
                },
                "performance": {
                    "response_time_avg": 0.0,  # TODO: Obtener de API real
                    "audit_success_rate": 100.0  # TODO: Obtener de API real
                },
                "security": {
                    "blocked_ips": [],  # TODO: Obtener de API real
                    "blocked_users": [],  # TODO: Obtener de API real
                    "suspicious_activities": 0  # TODO: Obtener de API real
                },
                "components": audit_data,
                "api_data": audit_data
            }
        except Exception as e:
            logger.error(f"Error obteniendo datos de auditoría: {e}")
            return {"error": "Datos de auditoría no disponibles"}

    async def _get_federated_data(self) -> Dict[str, Any]:
        """Obtener datos del sistema federado desde APIs reales."""
        try:
            # Obtener datos de la API federada a través del gateway
            federated_data = {}
            try:
                gateway_url = f"http://localhost:{self.global_config.api.dashboard_port}"
                async with self.http_client as client:
                    response = await client.get(f"{gateway_url}/api/federated/stats", timeout=5.0)
                    if response.status_code == 200:
                        federated_data = response.json()
            except Exception as e:
                logger.warning(f"No se pudo obtener datos de API federada: {e}")

            # Obtener datos adicionales del state manager
            system_metrics = self.state_manager.get_system_metrics()

            # Combinar datos
            total_rewards = 0.0
            try:
                rewards_stats = await self.dracma_manager.get_system_stats()
                totals = rewards_stats.get("totals", {})
                total_rewards = float(totals.get("total_rewards", 0.0))
            except Exception as e:
                logger.warning(f"No se pudo obtener rewards_totals: {e}")

            return {
                "active_sessions": federated_data.get("active_sessions", system_metrics.federated_sessions_active),
                "total_nodes": federated_data.get("total_nodes", 0),
                "completed_rounds": system_metrics.total_data_processed,  # Usar como proxy
                "average_accuracy": federated_data.get("avg_accuracy_trend", 0.0),
                "total_rewards_distributed": total_rewards,
                "network_efficiency": federated_data.get("aggregation_efficiency", 0.0) * 100,
                "federated_sessions_active": system_metrics.federated_sessions_active,
                "models_deployed": system_metrics.models_deployed,
                "api_data": federated_data
            }
        except Exception as e:
            logger.error(f"Error obteniendo datos federados: {e}")
            return {"error": "Datos federados no disponibles"}

    def _filter_data_by_role(self, data: Dict[str, Any], roles: List[str]) -> Dict[str, Any]:
        """Filtrar datos según el rol del usuario."""
        if "admin" in roles:
            return data  # Admin ve todo

        filtered = data.copy()

        if "operator" in roles:
            # Operator ve datos operativos pero no datos sensibles de auditoría
            if "auditing" in filtered:
                audit_data = filtered["auditing"]
                # Remover datos sensibles
                if "security" in audit_data:
                    del audit_data["security"]["blocked_ips"]
                    del audit_data["security"]["blocked_users"]
        else:
            # Viewer solo ve datos básicos
            filtered = {
                "monitoring": data.get("monitoring", {}),
                "federated": data.get("federated", {}),
                "timestamp": data.get("timestamp"),
                "user": data.get("user")
            }

        return filtered

    async def websocket_endpoint(self, websocket: WebSocket, user: dict = Depends(get_current_user)):
        """Endpoint WebSocket para actualizaciones en tiempo real."""
        await websocket.accept()

        session_id = user.get("username")
        self.websocket_connections[session_id] = websocket

        try:
            while True:
                # Enviar actualización cada 30 segundos
                data = await self.get_dashboard_data(user)
                await websocket.send_json({
                    "type": "dashboard_update",
                    "data": data
                })

                await asyncio.sleep(self.config.refresh_interval)

        except WebSocketDisconnect:
            logger.info(f"WebSocket desconectado para usuario: {session_id}")
        except Exception as e:
            logger.error(f"Error en WebSocket: {e}")
        finally:
            if session_id in self.websocket_connections:
                del self.websocket_connections[session_id]

    async def get_active_sessions(self, admin: dict = Depends(require_admin)) -> Dict[str, Any]:
        """Obtener sesiones activas (solo admin)."""
        return {
            "active_sessions": len(self.active_sessions),
            "sessions": [
                {
                    "session_id": session.session_id,
                    "user_id": session.user_id,
                    "username": session.username,
                    "roles": session.roles,
                    "login_time": session.login_time.isoformat(),
                    "last_activity": session.last_activity.isoformat()
                }
                for session in self.active_sessions.values()
            ],
            "websocket_connections": len(self.websocket_connections)
        }

    async def terminate_session(self, session_id: str, admin: dict = Depends(require_admin)) -> Dict[str, Any]:
        """Terminar sesión específica (solo admin)."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

            # Cerrar conexión WebSocket si existe
            if session_id in self.websocket_connections:
                try:
                    await self.websocket_connections[session_id].close()
                    del self.websocket_connections[session_id]
                except:
                    pass

            return {"message": f"Sesión {session_id} terminada"}
        else:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")

    def _get_login_html(self) -> str:
        """Obtener HTML de la página de login."""
        return f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - {self.config.title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex items-center justify-center">
    <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
        <h1 class="text-2xl font-bold text-center mb-6">AILOOS Dashboard</h1>

        <form id="loginForm" class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-gray-700">Usuario</label>
                <input type="text" id="username" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500">
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-700">Contraseña</label>
                <input type="password" id="password" class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500">
            </div>

            <button type="submit" class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
                Iniciar Sesión
            </button>
        </form>

        <div id="message" class="mt-4 text-center text-sm text-red-600 hidden"></div>

        <div class="mt-6 text-center text-sm text-gray-600">
            <p>Usuarios de prueba:</p>
            <p>admin/admin, operator/operator, viewer/viewer</p>
        </div>
    </div>

    <script>
        document.getElementById('loginForm').addEventListener('submit', async (e) => {{
            e.preventDefault();

            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const messageDiv = document.getElementById('message');

            try {{
                const response = await fetch('/api/auth/login', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{ username, password }})
                }});

                const data = await response.json();

                if (response.ok) {{
                    localStorage.setItem('token', data.access_token);
                    window.location.href = '/dashboard';
                }} else {{
                    messageDiv.textContent = data.detail || 'Error en login';
                    messageDiv.classList.remove('hidden');
                }}
            }} catch (error) {{
                messageDiv.textContent = 'Error de conexión';
                messageDiv.classList.remove('hidden');
            }}
        }});
    </script>
</body>
</html>
        """

    def _get_dashboard_html(self, user: dict) -> str:
        """Obtener HTML del dashboard principal."""
        return f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.config.title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <div class="flex justify-between items-center mb-8">
            <div>
                <h1 class="text-4xl font-bold text-gray-800">{self.config.title}</h1>
                <p class="text-gray-600">Usuario: {user.get('username')} | Roles: {', '.join(user.get('roles', []))}</p>
            </div>
            <div class="space-x-4">
                <button onclick="logout()" class="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">Logout</button>
            </div>
        </div>

        <!-- Navigation -->
        <div class="mb-8">
            <nav class="flex space-x-4">
                <button onclick="showSection('overview')" class="bg-blue-500 text-white px-4 py-2 rounded">Vista General</button>
                <button onclick="showSection('monitoring')" class="bg-gray-500 text-white px-4 py-2 rounded">Monitoreo</button>
                <button onclick="showSection('auditing')" class="bg-gray-500 text-white px-4 py-2 rounded">Auditoría</button>
                <button onclick="showSection('federated')" class="bg-gray-500 text-white px-4 py-2 rounded">Federado</button>
            </nav>
        </div>

        <!-- Content Sections -->
        <div id="overview" class="section">
            <h2 class="text-2xl font-bold mb-4">Vista General del Sistema</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6" id="overview-cards">
                <!-- Cards will be populated by JavaScript -->
            </div>
        </div>

        <div id="monitoring" class="section hidden">
            <h2 class="text-2xl font-bold mb-4">Monitoreo del Sistema</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="bg-white p-6 rounded-lg shadow">
                    <h3 class="text-lg font-semibold mb-4">Uso de Recursos</h3>
                    <canvas id="resourceChart"></canvas>
                </div>
                <div class="bg-white p-6 rounded-lg shadow">
                    <h3 class="text-lg font-semibold mb-4">Estado de Nodos</h3>
                    <div id="node-status"></div>
                </div>
            </div>
        </div>

        <div id="auditing" class="section hidden">
            <h2 class="text-2xl font-bold mb-4">Auditoría y Seguridad</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="bg-white p-6 rounded-lg shadow">
                    <h3 class="text-lg font-semibold mb-4">Alertas Activas</h3>
                    <div id="audit-alerts"></div>
                </div>
                <div class="bg-white p-6 rounded-lg shadow">
                    <h3 class="text-lg font-semibold mb-4">Métricas de Rendimiento</h3>
                    <canvas id="performanceChart"></canvas>
                </div>
            </div>
        </div>

        <div id="federated" class="section hidden">
            <h2 class="text-2xl font-bold mb-4">Sistema Federado</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="bg-white p-6 rounded-lg shadow">
                    <h3 class="text-lg font-semibold mb-4">Sesiones Activas</h3>
                    <div id="federated-sessions"></div>
                </div>
                <div class="bg-white p-6 rounded-lg shadow">
                    <h3 class="text-lg font-semibold mb-4">Métricas de Red</h3>
                    <canvas id="federatedChart"></canvas>
                </div>
            </div>
        </div>
    </div>

    <script>
        let resourceChart, performanceChart, federatedChart;
        let currentSection = 'overview';

        async function loadDashboardData() {{
            try {{
                const token = localStorage.getItem('token');
                const response = await fetch('/api/dashboard/data', {{
                    headers: {{
                        'Authorization': `Bearer ${{token}}`
                    }}
                }});

                if (response.ok) {{
                    const data = await response.json();
                    updateDashboard(data);
                }} else if (response.status === 401) {{
                    window.location.href = '/';
                }}
            }} catch (error) {{
                console.error('Error loading dashboard data:', error);
            }}
        }}

        function updateDashboard(data) {{
            // Update overview cards
            const overviewCards = document.getElementById('overview-cards');
            const monitoring = data.monitoring || {{}};
            const auditing = data.auditing || {{}};
            const federated = data.federated || {{}};

            overviewCards.innerHTML = `
                <div class="bg-white p-6 rounded-lg shadow">
                    <h3 class="text-lg font-semibold mb-2">Estado del Sistema</h3>
                    <p class="text-2xl font-bold text-green-600">${{monitoring.system_health || 'N/A'}}</p>
                </div>
                <div class="bg-white p-6 rounded-lg shadow">
                    <h3 class="text-lg font-semibold mb-2">Nodos Activos</h3>
                    <p class="text-2xl font-bold text-blue-600">${{monitoring.active_nodes || 0}}</p>
                </div>
                <div class="bg-white p-6 rounded-lg shadow">
                    <h3 class="text-lg font-semibold mb-2">Sesiones Federadas</h3>
                    <p class="text-2xl font-bold text-purple-600">${{federated.active_sessions || 0}}</p>
                </div>
            `;

            // Update monitoring section
            document.getElementById('node-status').innerHTML = `
                <p>CPU: ${{monitoring.cpu_usage || 0}}%</p>
                <p>Memoria: ${{monitoring.memory_usage || 0}}%</p>
                <p>Red: ${{monitoring.network_status || 'N/A'}}</p>
            `;

            // Update auditing section
            document.getElementById('audit-alerts').innerHTML = `
                <p>Alertas activas: ${{auditing.summary ? auditing.summary.active_alerts : 0}}</p>
                <p>Eventos últimas 24h: ${{auditing.summary ? auditing.summary.total_events_24h : 0}}</p>
            `;

            // Update federated section
            document.getElementById('federated-sessions').innerHTML = `
                <p>Sesiones activas: ${{federated.active_sessions || 0}}</p>
                <p>Nodos totales: ${{federated.total_nodes || 0}}</p>
                <p>Rondas completadas: ${{federated.completed_rounds || 0}}</p>
            `;

            // Update charts
            updateCharts(data);
        }}

        function updateCharts(data) {{
            const monitoring = data.monitoring || {{}};

            // Resource Chart
            const resourceCtx = document.getElementById('resourceChart');
            if (resourceCtx) {{
                if (resourceChart) resourceChart.destroy();
                resourceChart = new Chart(resourceCtx, {{
                    type: 'doughnut',
                    data: {{
                        labels: ['CPU', 'Memoria', 'Disponible'],
                        datasets: [{{
                            data: [monitoring.cpu_usage || 0, monitoring.memory_usage || 0, 100 - (monitoring.cpu_usage || 0)],
                            backgroundColor: ['#FF6384', '#36A2EB', '#E7E7E7']
                        }}]
                    }}
                }});
            }}

            // Performance Chart
            const perfCtx = document.getElementById('performanceChart');
            if (perfCtx) {{
                if (performanceChart) performanceChart.destroy();
                performanceChart = new Chart(perfCtx, {{
                    type: 'line',
                    data: {{
                        labels: ['Ahora'],
                        datasets: [{{
                            label: 'Respuesta (ms)',
                            data: [data.auditing?.performance?.response_time_avg || 0],
                            borderColor: '#FF6384'
                        }}]
                    }}
                }});
            }}

            // Federated Chart
            const fedCtx = document.getElementById('federatedChart');
            if (fedCtx) {{
                if (federatedChart) federatedChart.destroy();
                federatedChart = new Chart(fedCtx, {{
                    type: 'bar',
                    data: {{
                        labels: ['Accuracy', 'Eficiencia'],
                        datasets: [{{
                            data: [data.federated?.average_accuracy || 0, data.federated?.network_efficiency || 0],
                            backgroundColor: ['#36A2EB', '#FF6384']
                        }}]
                    }}
                }});
            }}
        }}

        function showSection(sectionName) {{
            // Hide all sections
            document.querySelectorAll('.section').forEach(section => {{
                section.classList.add('hidden');
            }});

            // Show selected section
            document.getElementById(sectionName).classList.remove('hidden');

            // Update navigation buttons
            document.querySelectorAll('nav button').forEach(btn => {{
                btn.classList.remove('bg-blue-500');
                btn.classList.add('bg-gray-500');
            }});

            event.target.classList.remove('bg-gray-500');
            event.target.classList.add('bg-blue-500');

            currentSection = sectionName;
        }}

        function logout() {{
            localStorage.removeItem('token');
            window.location.href = '/';
        }}

        // Load data on page load
        loadDashboardData();

        // Refresh data every 30 seconds
        setInterval(loadDashboardData, 30000);
    </script>
</body>
</html>
        """

    def create_app(self) -> FastAPI:
        """Crear y retornar la aplicación FastAPI."""
        return self.app

    async def start_server(self, host: str = "0.0.0.0", port: int = 8003):
        """Iniciar servidor del dashboard unificado."""
        import uvicorn

        logger.info(f"Iniciando dashboard unificado en {host}:{port}")
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()


# Función de conveniencia
def create_unified_dashboard(config: DashboardConfig = None) -> UnifiedDashboard:
    """Crear instancia del dashboard unificado."""
    return UnifiedDashboard(config)


# Función para iniciar el dashboard
async def start_unified_dashboard(host: str = "0.0.0.0", port: int = 8003):
    """Función de conveniencia para iniciar el dashboard unificado."""
    dashboard = create_unified_dashboard()
    await dashboard.start_server(host, port)


if __name__ == "__main__":
    # Para testing directo
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "server":
        # Iniciar servidor
        asyncio.run(start_unified_dashboard())
    else:
        # Crear instancia para testing
        dashboard = create_unified_dashboard()
        print("✅ UnifiedDashboard creado exitosamente")
        print(f"📊 Título: {dashboard.config.title}")
        print(f"🔄 Intervalo de refresh: {dashboard.config.refresh_interval}s")
        print("🚀 Para iniciar servidor: python unified_dashboard.py server")
