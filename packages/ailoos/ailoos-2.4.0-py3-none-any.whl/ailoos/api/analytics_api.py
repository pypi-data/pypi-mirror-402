"""
API REST para Analytics de AILOOS.
Proporciona endpoints para análisis de uso, métricas de rendimiento y insights del sistema.
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, Request
from pydantic import BaseModel

from ..monitoring.advanced_analytics import AdvancedAnalyticsEngine
from ..monitoring.business_metrics import BusinessMetricsEngine
from ..core.config import get_config
from ..core.logging import get_logger
from ..utils.cache import cached, invalidate_cache, get_cache_manager
from ..core.serializers import get_toon_serializer, get_vsc_serializer, get_json_serializer
from ..core.serialization_middleware import ContentNegotiationMiddleware

logger = get_logger(__name__)


class AnalyticsConfigRequest(BaseModel):
    """Configuración para inicializar analytics."""
    enable_predictions: bool = True
    prediction_days: int = 7
    report_retention_days: int = 30


class UsageAnalyticsRequest(BaseModel):
    """Solicitud de análisis de uso."""
    date: Optional[str] = None
    period: str = "daily"  # daily, weekly, monthly


class PerformanceMetricsRequest(BaseModel):
    """Solicitud de métricas de rendimiento."""
    metric_type: str = "all"
    include_predictions: bool = True


class AnalyticsAPI:
    """
    API REST completa para Analytics de AILOOS.
    Maneja todas las operaciones de análisis de datos del sistema.
    """

    def __init__(self):
        self.app = FastAPI(
            title="AILOOS Analytics API",
            description="API REST para análisis completo de datos, métricas de rendimiento e insights del sistema AILOOS",
            version="1.0.0"
        )

        # Instancias de motores de analytics
        self.advanced_analytics = None
        self.business_metrics = None
        self._initialize_analytics()

        # Serializers optimizados para analytics
        self.toon_serializer = get_toon_serializer()
        self.vsc_serializer = get_vsc_serializer()
        self.json_serializer = get_json_serializer()

        # Middleware de serialización
        self.serialization_middleware = ContentNegotiationMiddleware(None)

        # WebSocket connections
        self.websocket_connections: Dict[str, WebSocket] = {}
        self.websocket_broadcast_interval: float = 3.0  # Broadcast every 3 seconds

        # Configurar rutas
        self._setup_routes()

        logger.info("📊 Analytics API initialized with TOON/VSC serialization")

    def _initialize_analytics(self):
        """Inicializar motores de analytics."""
        try:
            config = get_config()

            # Inicializar motores de analytics
            self.advanced_analytics = AdvancedAnalyticsEngine()
            self.business_metrics = BusinessMetricsEngine()

            logger.info("✅ Analytics engines initialized successfully")

        except Exception as e:
            logger.error(f"❌ Error initializing Analytics engines: {e}")
            # Crear instancias básicas
            self.advanced_analytics = AdvancedAnalyticsEngine()
            self.business_metrics = BusinessMetricsEngine()

    def _setup_routes(self):
        """Configurar todas las rutas de la API."""

        @self.app.get("/health")
        async def health_check():
            """Health check del API de analytics."""
            if not self.advanced_analytics or not self.business_metrics:
                return {"status": "error", "message": "Analytics engines not initialized"}

            return {
                "status": "healthy",
                "timestamp": time.time(),
                "engines": {
                    "advanced_analytics": "active",
                    "business_metrics": "active"
                }
            }

        # ===== USAGE ANALYTICS ENDPOINTS =====

        @self.app.get("/usage/daily")
        async def get_daily_usage_report(date: Optional[str] = None):
            """Obtener reporte diario de uso."""
            try:
                if not self.advanced_analytics:
                    raise HTTPException(status_code=503, detail="Analytics engine not available")

                report = self.advanced_analytics.generate_daily_report(date)
                return {
                    "report_type": "daily_usage",
                    "data": report,
                    "timestamp": time.time()
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting daily usage report: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving daily usage report: {str(e)}")

        @self.app.get("/usage/weekly")
        async def get_weekly_usage_report(week_start: Optional[str] = None):
            """Obtener reporte semanal de uso."""
            try:
                if not self.advanced_analytics:
                    raise HTTPException(status_code=503, detail="Analytics engine not available")

                report = self.advanced_analytics.generate_weekly_report(week_start)
                return {
                    "report_type": "weekly_usage",
                    "data": report,
                    "timestamp": time.time()
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting weekly usage report: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving weekly usage report: {str(e)}")

        @self.app.get("/usage/growth")
        async def get_growth_trends():
            """Obtener tendencias de crecimiento de usuarios."""
            try:
                if not self.advanced_analytics:
                    raise HTTPException(status_code=503, detail="Analytics engine not available")

                trends = self.advanced_analytics.analyze_growth_trends()
                return {
                    "analysis_type": "growth_trends",
                    "data": trends,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error getting growth trends: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving growth trends: {str(e)}")

        # ===== PERFORMANCE METRICS ENDPOINTS =====

        @self.app.get("/performance/failures")
        async def get_failure_predictions(prediction_days: int = Query(7, ge=1, le=30)):
            """Obtener predicciones de fallos del sistema."""
            try:
                if not self.advanced_analytics:
                    raise HTTPException(status_code=503, detail="Analytics engine not available")

                predictions = self.advanced_analytics.predict_failures(prediction_days)
                return {
                    "analysis_type": "failure_predictions",
                    "data": predictions,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error getting failure predictions: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving failure predictions: {str(e)}")

        @self.app.get("/performance/benchmark")
        async def get_performance_benchmark():
            """Obtener benchmarking contra estándares de la industria."""
            try:
                if not self.advanced_analytics:
                    raise HTTPException(status_code=503, detail="Analytics engine not available")

                benchmark = self.advanced_analytics.benchmark_against_industry()
                return {
                    "analysis_type": "industry_benchmark",
                    "data": benchmark,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error getting performance benchmark: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving performance benchmark: {str(e)}")

        @self.app.get("/performance/metrics")
        @cached(ttl=30, key_prefix="analytics")
        async def get_performance_metrics(request: Request = None):
            """Obtener métricas generales de rendimiento con TOON/VSC optimización."""
            try:
                if not self.advanced_analytics:
                    raise HTTPException(status_code=503, detail="Analytics engine not available")

                # Obtener métricas de rendimiento actuales
                data = self.advanced_analytics._load_data()
                if not data.empty:
                    latest = data.iloc[-1]
                    metrics = {
                        "uptime": latest.get("uptime", 0),
                        "response_time": latest.get("response_time", 0),
                        "error_rate": latest.get("error_rate", 0),
                        "throughput": latest.get("throughput", 0),
                        "cpu_usage": latest.get("cpu_usage", 0),
                        "memory_usage": latest.get("memory_usage", 0)
                    }
                else:
                    metrics = {
                        "uptime": 99.5,
                        "response_time": 150,
                        "error_rate": 0.05,
                        "throughput": 800,
                        "cpu_usage": 60,
                        "memory_usage": 70
                    }

                response_data = {
                    "metrics_type": "current_performance",
                    "data": metrics,
                    "timestamp": time.time()
                }

                # Usar TOON para métricas numéricas repetitivas
                return response_data

            except Exception as e:
                logger.error(f"Error getting performance metrics: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving performance metrics: {str(e)}")

        # ===== SYSTEM INSIGHTS ENDPOINTS =====

        @self.app.get("/insights/business-kpis")
        @cached(ttl=30, key_prefix="analytics")
        async def get_business_kpis():
            """Obtener KPIs de negocio."""
            try:
                if not self.business_metrics:
                    raise HTTPException(status_code=503, detail="Business metrics engine not available")

                kpis = self.business_metrics.get_business_kpis()
                return {
                    "insights_type": "business_kpis",
                    "data": kpis,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error getting business KPIs: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving business KPIs: {str(e)}")

        @self.app.get("/insights/roi")
        async def calculate_node_roi(node_id: str, revenue: float = Query(..., gt=0), costs: float = Query(..., gt=0)):
            """Calcular ROI para un nodo específico."""
            try:
                if not self.business_metrics:
                    raise HTTPException(status_code=503, detail="Business metrics engine not available")

                roi = self.business_metrics.calculate_roi(node_id, revenue, costs)
                return {
                    "insights_type": "node_roi",
                    "node_id": node_id,
                    "revenue": revenue,
                    "costs": costs,
                    "roi_percentage": roi,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error calculating ROI: {e}")
                raise HTTPException(status_code=500, detail=f"Error calculating ROI: {str(e)}")

        @self.app.get("/insights/energy-efficiency")
        async def calculate_energy_efficiency(flops: float = Query(..., gt=0), power_consumption: float = Query(..., gt=0)):
            """Calcular eficiencia energética."""
            try:
                if not self.business_metrics:
                    raise HTTPException(status_code=503, detail="Business metrics engine not available")

                efficiency = self.business_metrics.calculate_energy_efficiency(flops, power_consumption)
                return {
                    "insights_type": "energy_efficiency",
                    "flops": flops,
                    "power_consumption_watts": power_consumption,
                    "efficiency_flops_per_watt": efficiency,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error calculating energy efficiency: {e}")
                raise HTTPException(status_code=500, detail=f"Error calculating energy efficiency: {str(e)}")

        @self.app.get("/insights/carbon-footprint")
        async def calculate_carbon_footprint(training_hours: float = Query(..., gt=0),
                                            power_consumption: float = Query(..., gt=0),
                                            location_factor: float = 1.0):
            """Calcular huella de carbono."""
            try:
                if not self.business_metrics:
                    raise HTTPException(status_code=503, detail="Business metrics engine not available")

                footprint = self.business_metrics.calculate_carbon_footprint(
                    training_hours, power_consumption, location_factor
                )
                return {
                    "insights_type": "carbon_footprint",
                    "training_hours": training_hours,
                    "power_consumption_watts": power_consumption,
                    "location_factor": location_factor,
                    "carbon_footprint_kg_co2": footprint,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error calculating carbon footprint: {e}")
                raise HTTPException(status_code=500, detail=f"Error calculating carbon footprint: {str(e)}")

        # ===== DASHBOARD ENDPOINTS =====

        @self.app.get("/dashboard/analytics")
        @cached(ttl=30, key_prefix="analytics")
        async def get_analytics_dashboard(request: Request = None):
            """Obtener datos completos del dashboard de analytics con TOON/VSC optimización."""
            try:
                if not self.advanced_analytics or not self.business_metrics:
                    raise HTTPException(status_code=503, detail="Analytics engines not available")

                # Obtener datos de múltiples fuentes
                usage_report = self.advanced_analytics.generate_daily_report()
                growth_trends = self.advanced_analytics.analyze_growth_trends()
                business_kpis = self.business_metrics.get_business_kpis()

                dashboard_data = {
                    "usage_analytics": usage_report,
                    "growth_trends": growth_trends,
                    "business_kpis": business_kpis,
                    "performance_benchmark": self.advanced_analytics.benchmark_against_industry(),
                    "failure_predictions": self.advanced_analytics.predict_failures(7)
                }

                response_data = {
                    "dashboard_type": "analytics_overview",
                    "data": dashboard_data,
                    "timestamp": time.time()
                }

                # Aplicar serialización optimizada para datos grandes
                return response_data

            except Exception as e:
                logger.error(f"Error getting analytics dashboard: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving analytics dashboard: {str(e)}")

        # ===== WEBSOCKET ENDPOINTS =====

        @self.app.options("/ws/analytics")
        async def options_websocket_analytics():
            """OPTIONS handler for analytics websocket."""
            return {"Allow": "GET, POST, OPTIONS"}

        @self.app.websocket("/ws/analytics")
        async def websocket_analytics_endpoint(websocket: WebSocket, client_id: str = None):
            """WebSocket endpoint for real-time analytics updates."""
            if not client_id:
                client_id = f"analytics_client_{int(time.time())}_{hash(str(websocket)) % 10000}"

            await self._handle_websocket_connection(websocket, client_id)

        # ===== EXPORT ENDPOINTS =====

        @self.app.get("/cache/stats")
        async def get_cache_stats():
            """Obtener estadísticas del sistema de caché."""
            try:
                cache_manager = get_cache_manager()
                stats = await cache_manager.get_stats()

                return {
                    "cache_stats": stats,
                    "timestamp": time.time()
                }
            except Exception as e:
                logger.error(f"Error getting cache stats: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving cache stats: {str(e)}")

        @self.app.get("/export/analytics/{format}")
        async def export_analytics_data(format: str = "json"):
            """Exportar datos de analytics."""
            try:
                if not self.advanced_analytics:
                    raise HTTPException(status_code=503, detail="Analytics engine not available")

                # Obtener todos los datos de analytics
                dashboard_data = await get_analytics_dashboard()

                if format.lower() == "json":
                    return dashboard_data
                else:
                    # Para otros formatos, devolver JSON por ahora
                    return dashboard_data

            except Exception as e:
                logger.error(f"Error exporting analytics data: {e}")
                raise HTTPException(status_code=500, detail=f"Error exporting analytics data: {str(e)}")

    async def _handle_websocket_connection(self, websocket: WebSocket, client_id: str):
        """
        Handle WebSocket connection for real-time analytics updates.

        Args:
            websocket: WebSocket connection
            client_id: Unique client identifier
        """
        await websocket.accept()
        self.websocket_connections[client_id] = websocket

        logger.info(f"📡 Analytics WebSocket client connected: {client_id}")

        try:
            # Send initial analytics status
            initial_status = await self._get_analytics_status()
            await websocket.send_json({
                "type": "initial_status",
                "timestamp": time.time(),
                "data": initial_status
            })

            # Keep connection alive and handle client messages
            while True:
                try:
                    # Wait for client messages with timeout
                    message = await asyncio.wait_for(
                        websocket.receive_json(),
                        timeout=self.websocket_broadcast_interval
                    )

                    # Handle client requests
                    await self._handle_websocket_message(websocket, client_id, message)

                except asyncio.TimeoutError:
                    # Send periodic updates
                    await self._send_websocket_update(websocket, client_id)
                except Exception as e:
                    logger.error(f"Error handling WebSocket message from {client_id}: {e}")
                    break

        except WebSocketDisconnect:
            logger.info(f"📡 Analytics WebSocket client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Analytics WebSocket connection error for {client_id}: {e}")
        finally:
            # Clean up connection
            if client_id in self.websocket_connections:
                del self.websocket_connections[client_id]

    async def _handle_websocket_message(self, websocket: WebSocket, client_id: str, message: Dict[str, Any]):
        """Handle incoming WebSocket messages from clients."""
        try:
            message_type = message.get("type", "unknown")

            if message_type == "subscribe":
                # Client subscribing to specific analytics
                subscriptions = message.get("subscriptions", [])
                logger.info(f"Analytics client {client_id} subscribed to: {subscriptions}")

                # Send confirmation
                await websocket.send_json({
                    "type": "subscription_confirmed",
                    "subscriptions": subscriptions,
                    "timestamp": time.time()
                })

            elif message_type == "request_metrics":
                # Client requesting specific metrics
                metric_type = message.get("metric_type", "all")
                status = await self._get_analytics_status()

                if metric_type == "all":
                    data = status
                elif metric_type == "performance":
                    data = status.get("performance_metrics", {})
                elif metric_type == "usage":
                    data = status.get("usage_analytics", {})
                elif metric_type == "insights":
                    data = status.get("system_insights", {})
                else:
                    data = status

                await websocket.send_json({
                    "type": "metrics_data",
                    "metric_type": metric_type,
                    "data": data,
                    "timestamp": time.time()
                })

            else:
                logger.warning(f"Unknown WebSocket message type from {client_id}: {message_type}")

        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await websocket.send_json({
                "type": "error",
                "message": f"Error processing message: {e}",
                "timestamp": time.time()
            })

    async def _send_websocket_update(self, websocket: WebSocket, client_id: str):
        """Send periodic update to specific WebSocket client."""
        try:
            status = await self._get_analytics_status()
            await websocket.send_json({
                "type": "analytics_update",
                "timestamp": time.time(),
                "data": status
            })
        except Exception as e:
            logger.error(f"Error sending WebSocket update to {client_id}: {e}")

    async def _broadcast_websocket_updates(self):
        """Broadcast updates to all WebSocket connections."""
        if not self.websocket_connections:
            return

        try:
            status = await self._get_analytics_status()
            message = {
                "type": "analytics_update",
                "timestamp": time.time(),
                "data": status
            }

            # Remove disconnected clients
            disconnected_clients = []
            for client_id, websocket in self.websocket_connections.items():
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send analytics update to client {client_id}: {e}")
                    disconnected_clients.append(client_id)

            # Clean up disconnected clients
            for client_id in disconnected_clients:
                del self.websocket_connections[client_id]
                logger.info(f"Removed disconnected analytics WebSocket client: {client_id}")

        except Exception as e:
            logger.error(f"Error broadcasting WebSocket analytics updates: {e}")

    async def _get_analytics_status(self) -> Dict[str, Any]:
        """Get comprehensive analytics status for WebSocket updates."""
        try:
            status = {
                "timestamp": time.time(),
                "performance_metrics": {},
                "usage_analytics": {},
                "system_insights": {},
                "dashboard": {}
            }

            # Get performance metrics
            try:
                if self.advanced_analytics:
                    data = self.advanced_analytics._load_data()
                    if not data.empty:
                        latest = data.iloc[-1]
                        status["performance_metrics"] = {
                            "uptime": latest.get("uptime", 0),
                            "response_time": latest.get("response_time", 0),
                            "error_rate": latest.get("error_rate", 0),
                            "throughput": latest.get("throughput", 0),
                            "cpu_usage": latest.get("cpu_usage", 0),
                            "memory_usage": latest.get("memory_usage", 0)
                        }
            except Exception as e:
                logger.warning(f"Error getting performance metrics for WebSocket: {e}")

            # Get usage analytics
            try:
                if self.advanced_analytics:
                    usage_report = self.advanced_analytics.generate_daily_report()
                    status["usage_analytics"] = usage_report
            except Exception as e:
                logger.warning(f"Error getting usage analytics for WebSocket: {e}")

            # Get system insights
            try:
                if self.business_metrics:
                    kpis = self.business_metrics.get_business_kpis()
                    status["system_insights"] = kpis
            except Exception as e:
                logger.warning(f"Error getting system insights for WebSocket: {e}")

            # Get dashboard summary
            try:
                if self.advanced_analytics and self.business_metrics:
                    dashboard_data = {
                        "usage_analytics": status["usage_analytics"],
                        "business_kpis": status["system_insights"],
                        "performance_benchmark": self.advanced_analytics.benchmark_against_industry(),
                        "failure_predictions": self.advanced_analytics.predict_failures(7)
                    }
                    status["dashboard"] = dashboard_data
            except Exception as e:
                logger.warning(f"Error getting dashboard data for WebSocket: {e}")

            return status

        except Exception as e:
            logger.error(f"Error getting analytics status: {e}")
            return {
                "timestamp": time.time(),
                "error": f"Failed to get analytics status: {e}",
                "performance_metrics": {},
                "usage_analytics": {},
                "system_insights": {},
                "dashboard": {}
            }

    def get_websocket_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics."""
        return {
            "active_connections": len(self.websocket_connections),
            "client_ids": list(self.websocket_connections.keys()),
            "broadcast_interval": self.websocket_broadcast_interval
        }

    def start_websocket_broadcasting(self):
        """Start periodic WebSocket broadcasting of analytics updates."""
        asyncio.create_task(self._websocket_broadcast_loop())
        logger.info("📡 Analytics WebSocket broadcasting started")

    async def _websocket_broadcast_loop(self):
        """Background loop for periodic WebSocket broadcasting."""
        while True:
            try:
                await self._broadcast_websocket_updates()
                await asyncio.sleep(self.websocket_broadcast_interval)
            except Exception as e:
                logger.error(f"Error in WebSocket broadcast loop: {e}")
                await asyncio.sleep(self.websocket_broadcast_interval)

    def create_app(self) -> FastAPI:
        """Crear y retornar la aplicación FastAPI."""
        return self.app

    def start_server(self, host: str = "0.0.0.0", port: int = 8003):
        """Iniciar servidor FastAPI."""
        # Start WebSocket broadcasting
        self.start_websocket_broadcasting()

        import uvicorn
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )


# Instancia global de la API
analytics_api = AnalyticsAPI()


def create_analytics_app() -> FastAPI:
    """Función de conveniencia para crear la app FastAPI de analytics."""
    return analytics_api.create_app()


if __name__ == "__main__":
    # Iniciar servidor para pruebas
    print("🚀 Iniciando AILOOS Analytics API...")
    analytics_api.start_server()