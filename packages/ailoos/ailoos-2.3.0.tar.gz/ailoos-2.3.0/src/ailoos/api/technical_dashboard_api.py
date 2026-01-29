"""
API REST para el Technical Dashboard de AILOOS.
Proporciona endpoints para monitoreo de métricas federadas, distribución de datos, rendimiento de nodos e IPFS.
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, Query, WebSocket
from pydantic import BaseModel

from ..monitoring.technical_dashboard import TechnicalDashboard, MonitoringLevel
from ..federated.coordinator import FederatedCoordinator
from ..federated.data_coordinator import FederatedDataCoordinator
from ..infrastructure.ipfs_distributor import IPFSDistributor
from ..core.config import get_config
from ..core.logging import get_logger

logger = get_logger(__name__)


class DashboardConfigRequest(BaseModel):
    """Configuración para inicializar el dashboard."""
    monitoring_level: str = "detailed"
    update_interval: float = 5.0


class MetricsHistoryRequest(BaseModel):
    """Solicitud de historial de métricas."""
    metric_type: str
    limit: int = 50


class TechnicalDashboardAPI:
    """
    API REST completa para el Technical Dashboard.
    Maneja todas las operaciones de monitoreo técnico del sistema federado.
    """

    def __init__(self):
        self.app = FastAPI(
            title="AILOOS Technical Dashboard API",
            description="API REST para monitoreo completo del sistema federado de AILOOS",
            version="1.0.0"
        )

        # Instancia del dashboard técnico
        self.dashboard = None
        self._initialize_dashboard()

        # Configurar rutas
        self._setup_routes()

        logger.info("📊 Technical Dashboard API initialized")

    def _initialize_dashboard(self):
        """Inicializar el dashboard técnico con componentes del sistema."""
        try:
            config = get_config()

            # Intentar obtener componentes del sistema
            federated_coordinator = None
            data_coordinator = None
            ipfs_distributor = None

            try:
                # Importar dinámicamente para evitar dependencias circulares
                from ..federated.coordinator import get_federated_coordinator
                federated_coordinator = get_federated_coordinator()
            except Exception as e:
                logger.warning(f"Could not get federated coordinator: {e}")

            try:
                from ..federated.data_coordinator import get_data_coordinator
                data_coordinator = get_data_coordinator()
            except Exception as e:
                logger.warning(f"Could not get data coordinator: {e}")

            try:
                from ..infrastructure.ipfs_distributor import get_ipfs_distributor
                ipfs_distributor = get_ipfs_distributor()
            except Exception as e:
                logger.warning(f"Could not get IPFS distributor: {e}")

            # Crear dashboard
            self.dashboard = TechnicalDashboard(
                federated_coordinator=federated_coordinator,
                data_coordinator=data_coordinator,
                ipfs_distributor=ipfs_distributor,
                monitoring_level=MonitoringLevel.DETAILED,
                update_interval=5.0
            )

            logger.info("✅ Technical Dashboard initialized successfully")

            # Start monitoring automatically
            asyncio.create_task(self.dashboard.start_monitoring())
            logger.info("📊 Technical Dashboard monitoring started")

        except Exception as e:
            logger.error(f"❌ Error initializing Technical Dashboard: {e}")
            # Crear dashboard básico sin componentes
            self.dashboard = TechnicalDashboard()

    def _setup_routes(self):
        """Configurar todas las rutas de la API."""

        @self.app.get("/health")
        async def health_check():
            """Health check del dashboard técnico."""
            if not self.dashboard:
                return {"status": "error", "message": "Dashboard not initialized"}

            health = self.dashboard.get_health_status()
            return {
                "status": "healthy" if health.get("overall_health") == "healthy" else "degraded",
                "timestamp": time.time(),
                "dashboard_running": self.dashboard.is_running,
                "monitoring_level": self.dashboard.monitoring_level.value,
                "active_components": health.get("active_components", {}),
                "websocket_connections": health.get("websocket_connections", 0)
            }

        # ===== FEDERATED TRAINING METRICS ENDPOINTS =====

        @self.app.get("/api/federated/metrics")
        async def get_federated_metrics():
            """Obtener métricas de entrenamiento federado."""
            try:
                if not self.dashboard:
                    raise HTTPException(status_code=503, detail="Dashboard not available")

                status = self.dashboard.get_comprehensive_status()
                return {
                    "federated_training": status.get("federated_training", {}),
                    "timestamp": time.time()
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting federated metrics: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving federated metrics: {str(e)}")

        @self.app.get("/api/federated/sessions")
        async def get_federated_sessions():
            """Obtener sesiones activas de entrenamiento federado."""
            try:
                if not self.dashboard:
                    raise HTTPException(status_code=503, detail="Dashboard not available")

                # Usar el método existente del dashboard
                sessions = await self.dashboard.app.router.routes[17].endpoint()  # /api/federated/sessions endpoint
                return sessions
            except Exception as e:
                logger.error(f"Error getting federated sessions: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving federated sessions: {str(e)}")

        @self.app.get("/api/federated/history")
        async def get_federated_history(limit: int = Query(50, ge=1, le=100)):
            """Obtener historial de métricas federadas."""
            try:
                if not self.dashboard:
                    raise HTTPException(status_code=503, detail="Dashboard not available")

                history = self.dashboard.get_metrics_history("federated", limit)
                return {
                    "metric_type": "federated",
                    "history": history,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error getting federated history: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving federated history: {str(e)}")

        # ===== DATA DISTRIBUTION STATUS ENDPOINTS =====

        @self.app.get("/api/data/metrics")
        async def get_data_metrics():
            """Obtener métricas de distribución de datos."""
            try:
                if not self.dashboard:
                    raise HTTPException(status_code=503, detail="Dashboard not available")

                status = self.dashboard.get_comprehensive_status()
                return {
                    "data_distribution": status.get("data_distribution", {}),
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error getting data metrics: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving data metrics: {str(e)}")

        @self.app.get("/api/data/pipelines")
        async def get_data_pipelines():
            """Obtener pipelines activos de distribución de datos."""
            try:
                if not self.dashboard:
                    raise HTTPException(status_code=503, detail="Dashboard not available")

                # Usar el método existente del dashboard
                pipelines = await self.dashboard.app.router.routes[18].endpoint()  # /api/data/pipelines endpoint
                return pipelines
            except Exception as e:
                logger.error(f"Error getting data pipelines: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving data pipelines: {str(e)}")

        @self.app.get("/api/data/history")
        async def get_data_history(limit: int = Query(50, ge=1, le=100)):
            """Obtener historial de métricas de datos."""
            try:
                if not self.dashboard:
                    raise HTTPException(status_code=503, detail="Dashboard not available")

                history = self.dashboard.get_metrics_history("data", limit)
                return {
                    "metric_type": "data",
                    "history": history,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error getting data history: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving data history: {str(e)}")

        # ===== NODE PERFORMANCE ENDPOINTS =====

        @self.app.get("/api/nodes/metrics")
        async def get_node_metrics():
            """Obtener métricas de rendimiento de nodos."""
            try:
                if not self.dashboard:
                    raise HTTPException(status_code=503, detail="Dashboard not available")

                status = self.dashboard.get_comprehensive_status()
                return {
                    "node_performance": status.get("node_performance", {}),
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error getting node metrics: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving node metrics: {str(e)}")

        @self.app.get("/api/nodes/status")
        async def get_nodes_status():
            """Obtener estado detallado de nodos."""
            try:
                if not self.dashboard:
                    raise HTTPException(status_code=503, detail="Dashboard not available")

                # Usar el método existente del dashboard
                nodes = await self.dashboard.app.router.routes[19].endpoint()  # /api/nodes/status endpoint
                return nodes
            except Exception as e:
                logger.error(f"Error getting nodes status: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving nodes status: {str(e)}")

        @self.app.get("/api/nodes/history")
        async def get_node_history(limit: int = Query(50, ge=1, le=100)):
            """Obtener historial de métricas de nodos."""
            try:
                if not self.dashboard:
                    raise HTTPException(status_code=503, detail="Dashboard not available")

                history = self.dashboard.get_metrics_history("node", limit)
                return {
                    "metric_type": "node",
                    "history": history,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error getting node history: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving node history: {str(e)}")

        # ===== IPFS METRICS ENDPOINTS =====

        @self.app.get("/api/ipfs/metrics")
        async def get_ipfs_metrics():
            """Obtener métricas de IPFS."""
            try:
                if not self.dashboard:
                    raise HTTPException(status_code=503, detail="Dashboard not available")

                status = self.dashboard.get_comprehensive_status()
                return {
                    "ipfs_metrics": status.get("ipfs_metrics", {}),
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error getting IPFS metrics: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving IPFS metrics: {str(e)}")

        @self.app.get("/api/ipfs/status")
        async def get_ipfs_status():
            """Obtener estado detallado de IPFS."""
            try:
                if not self.dashboard:
                    raise HTTPException(status_code=503, detail="Dashboard not available")

                # Usar el método existente del dashboard
                ipfs = await self.dashboard.app.router.routes[20].endpoint()  # /api/ipfs/status endpoint
                return ipfs
            except Exception as e:
                logger.error(f"Error getting IPFS status: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving IPFS status: {str(e)}")

        @self.app.get("/api/ipfs/history")
        async def get_ipfs_history(limit: int = Query(50, ge=1, le=100)):
            """Obtener historial de métricas IPFS."""
            try:
                if not self.dashboard:
                    raise HTTPException(status_code=503, detail="Dashboard not available")

                history = self.dashboard.get_metrics_history("ipfs", limit)
                return {
                    "metric_type": "ipfs",
                    "history": history,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error getting IPFS history: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving IPFS history: {str(e)}")

        # ===== TRAINING PROGRESS ENDPOINTS =====

        @self.app.get("/api/training/progress")
        async def get_training_progress():
            """Obtener métricas de progreso de entrenamiento."""
            try:
                if not self.dashboard:
                    raise HTTPException(status_code=503, detail="Dashboard not available")

                status = self.dashboard.get_comprehensive_status()
                return {
                    "training_progress": status.get("training_progress", {}),
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error getting training progress: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving training progress: {str(e)}")

        @self.app.get("/api/training/history")
        async def get_training_history(limit: int = Query(50, ge=1, le=100)):
            """Obtener historial de métricas de entrenamiento."""
            try:
                if not self.dashboard:
                    raise HTTPException(status_code=503, detail="Dashboard not available")

                history = self.dashboard.get_metrics_history("training", limit)
                return {
                    "metric_type": "training",
                    "history": history,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error getting training history: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving training history: {str(e)}")

        # ===== DASHBOARD CONTROL ENDPOINTS =====

        @self.app.get("/api/dashboard/status")
        async def get_dashboard_status():
            """Obtener estado completo del dashboard."""
            try:
                if not self.dashboard:
                    raise HTTPException(status_code=503, detail="Dashboard not available")

                status = self.dashboard.get_comprehensive_status()
                return status
            except Exception as e:
                logger.error(f"Error getting dashboard status: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving dashboard status: {str(e)}")

        @self.app.options("/api/dashboard/start")
        async def options_dashboard_start():
            """OPTIONS handler for starting dashboard."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/api/dashboard/start")
        async def start_dashboard():
            """Iniciar el monitoreo del dashboard."""
            try:
                if not self.dashboard:
                    raise HTTPException(status_code=503, detail="Dashboard not available")

                if not self.dashboard.is_running:
                    await self.dashboard.start_monitoring()

                return {
                    "message": "Dashboard monitoring started",
                    "is_running": self.dashboard.is_running,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error starting dashboard: {e}")
                raise HTTPException(status_code=500, detail=f"Error starting dashboard monitoring: {str(e)}")

        @self.app.post("/api/dashboard/stop")
        async def stop_dashboard():
            """Detener el monitoreo del dashboard."""
            try:
                if not self.dashboard:
                    raise HTTPException(status_code=503, detail="Dashboard not available")

                if self.dashboard.is_running:
                    await self.dashboard.stop_monitoring()

                return {
                    "message": "Dashboard monitoring stopped",
                    "is_running": self.dashboard.is_running,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error stopping dashboard: {e}")
                raise HTTPException(status_code=500, detail=f"Error stopping dashboard monitoring: {str(e)}")

        @self.app.post("/api/dashboard/restart")
        async def restart_dashboard():
            """Reiniciar el monitoreo del dashboard."""
            try:
                if not self.dashboard:
                    raise HTTPException(status_code=503, detail="Dashboard not available")

                # Usar el método existente del dashboard
                result = await self.dashboard.app.router.routes[21].endpoint()  # /api/restart endpoint
                return result
            except Exception as e:
                logger.error(f"Error restarting dashboard: {e}")
                raise HTTPException(status_code=500, detail=f"Error restarting dashboard monitoring: {str(e)}")

        # ===== ALERTS ENDPOINTS =====

        @self.app.get("/api/alerts")
        async def get_alerts(
            severity: Optional[str] = None,
            resolved: bool = False,
            limit: int = Query(20, ge=1, le=100)
        ):
            """Obtener alertas del sistema."""
            try:
                if not self.dashboard:
                    raise HTTPException(status_code=503, detail="Dashboard not available")

                # Usar el método existente del dashboard
                alerts = await self.dashboard.app.router.routes[13].endpoint(severity=severity, resolved=resolved, limit=limit)  # /api/alerts endpoint
                return alerts
            except Exception as e:
                logger.error(f"Error getting alerts: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving alerts: {str(e)}")

        @self.app.post("/api/alerts/{alert_id}/resolve")
        async def resolve_alert(alert_id: str):
            """Resolver una alerta específica."""
            try:
                if not self.dashboard:
                    raise HTTPException(status_code=503, detail="Dashboard not available")

                # Usar el método existente del dashboard
                result = await self.dashboard.app.router.routes[14].endpoint(alert_id)  # /api/alerts/{alert_id}/resolve endpoint
                return result
            except Exception as e:
                logger.error(f"Error resolving alert: {e}")
                raise HTTPException(status_code=500, detail=f"Error resolving alert: {str(e)}")

        # ===== EXPORT ENDPOINTS =====

        @self.app.get("/api/export/{format}")
        async def export_metrics(format: str = "json"):
            """Exportar métricas del dashboard."""
            try:
                if not self.dashboard:
                    raise HTTPException(status_code=503, detail="Dashboard not available")

                # Usar el método existente del dashboard
                result = await self.dashboard.app.router.routes[16].endpoint(format=format)  # /api/export/{format} endpoint
                return result
            except Exception as e:
                logger.error(f"Error exporting metrics: {e}")
                raise HTTPException(status_code=500, detail=f"Error exporting metrics: {str(e)}")

        # ===== SYSTEM STATUS ENDPOINTS =====

        @self.app.get("/api/system/connectivity")
        async def get_system_connectivity():
            """Obtener estado de conectividad del sistema."""
            try:
                if not self.dashboard:
                    raise HTTPException(status_code=503, detail="Dashboard not available")

                connectivity_status = await self.dashboard.get_system_connectivity_status()
                return {
                    "connectivity": connectivity_status,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error getting system connectivity: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving system connectivity: {str(e)}")

        @self.app.get("/api/system/health/services")
        async def get_service_health():
            """Obtener estado de salud de servicios."""
            try:
                if not self.dashboard:
                    raise HTTPException(status_code=503, detail="Dashboard not available")

                service_health = await self.dashboard.get_service_health_status()
                return {
                    "services": service_health,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error getting service health: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving service health: {str(e)}")

        @self.app.get("/api/system/infrastructure")
        async def get_infrastructure_status():
            """Obtener estado de infraestructura."""
            try:
                if not self.dashboard:
                    raise HTTPException(status_code=503, detail="Dashboard not available")

                infrastructure_status = await self.dashboard.get_infrastructure_monitoring_status()
                return {
                    "infrastructure": infrastructure_status,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error getting infrastructure status: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving infrastructure status: {str(e)}")

        # ===== WEBSOCKET ENDPOINTS =====

        @self.app.websocket("/ws/dashboard")
        async def websocket_dashboard_endpoint(websocket: WebSocket, client_id: str = None):
            """WebSocket endpoint for real-time dashboard updates."""
            if not self.dashboard:
                await websocket.close(code=1011)  # Internal server error
                return

            # Delegate to dashboard's WebSocket handler
            await self.dashboard.handle_websocket_connection(websocket, client_id)

    def create_app(self) -> FastAPI:
        """Crear y retornar la aplicación FastAPI."""
        return self.app

    def start_server(self, host: str = "0.0.0.0", port: int = 8002):
        """Iniciar servidor FastAPI."""
        import uvicorn
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )


# Instancia global de la API
technical_dashboard_api = TechnicalDashboardAPI()


def create_technical_dashboard_app() -> FastAPI:
    """Función de conveniencia para crear la app FastAPI del dashboard técnico."""
    return technical_dashboard_api.create_app()


if __name__ == "__main__":
    # Iniciar servidor para pruebas
    print("🚀 Iniciando AILOOS Technical Dashboard API...")
    technical_dashboard_api.start_server()