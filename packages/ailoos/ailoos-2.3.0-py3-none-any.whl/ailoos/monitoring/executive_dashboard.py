"""
Executive Dashboard for AILOOS - Business KPIs and Strategic Metrics
Provides executive-level insights into business performance, ROI, and strategic metrics.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import jwt

from ..core.logging import get_logger
from ..core.config import get_config
from ..core.state_manager import get_state_manager
from ..coordinator.auth.dependencies import get_current_user, require_admin
from ..notifications.service import NotificationService
from ..rewards.dracma_manager import DRACMA_Manager

logger = get_logger(__name__)


class ExecutiveRole(Enum):
    """Roles ejecutivos disponibles."""
    CEO = "ceo"
    CTO = "cto"
    CFO = "cfo"
    COO = "coo"
    CMO = "cmo"


@dataclass
class BusinessKPIs:
    """KPIs de negocio principales."""
    roi_per_node: float = 0.0
    total_roi: float = 0.0
    energy_efficiency_flops_per_watt: float = 0.0
    carbon_footprint_kg_co2: float = 0.0
    system_uptime_percentage: float = 0.0
    average_latency_ms: float = 0.0
    total_throughput_requests_per_second: float = 0.0
    federated_tests_completed: int = 0
    average_accuracy_percentage: float = 0.0
    training_rounds_completed: int = 0
    concurrent_nodes_max: int = 0
    convergence_rate_percentage: float = 0.0
    total_rewards_distributed: float = 0.0
    active_users_count: int = 0
    data_processed_gb: float = 0.0
    models_deployed_count: int = 0


@dataclass
class StrategicMetrics:
    """Métricas estratégicas."""
    market_penetration_percentage: float = 0.0
    competitive_advantage_score: float = 0.0
    innovation_index: float = 0.0
    customer_satisfaction_score: float = 0.0
    scalability_score: float = 0.0
    security_compliance_score: float = 0.0
    sustainability_score: float = 0.0
    technology_maturity_level: int = 0


@dataclass
class ExecutiveAlert:
    """Alerta ejecutiva."""
    alert_id: str
    priority: str  # "critical", "high", "medium", "low"
    category: str  # "business", "technical", "security", "operational"
    title: str
    description: str
    impact_assessment: str
    recommended_actions: List[str]
    timestamp: float
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[float] = None


class ExecutiveDashboard:
    """
    Dashboard ejecutivo para métricas de negocio y KPIs estratégicos.
    Proporciona insights en tiempo real para toma de decisiones ejecutivas.
    """

    def __init__(self,
                 notification_service: Optional[NotificationService] = None,
                 jwt_secret: str = "executive-dashboard-secret",
                 update_interval: float = 60.0):  # Actualización cada minuto para ejecutivos

        self.config = get_config()
        self.state_manager = get_state_manager()
        self.notification_service = notification_service
        self.dracma_manager = DRACMA_Manager(self.config)

        # Configuración de seguridad
        self.jwt_secret = jwt_secret
        self.update_interval = update_interval

        # Estado del dashboard
        self.is_running = False
        self.last_update = 0.0

        # Métricas
        self.business_kpis = BusinessKPIs()
        self.strategic_metrics = StrategicMetrics()
        self.executive_alerts: List[ExecutiveAlert] = []

        # Callbacks
        self.update_callbacks: List[Callable] = []
        self.alert_callbacks: List[Callable] = []

        # WebSocket connections por rol ejecutivo
        self.websocket_connections: Dict[str, Dict[str, WebSocket]] = {
            role.value: {} for role in ExecutiveRole
        }

        # Historial de métricas
        self.metrics_history: Dict[str, List] = {
            'business_kpis': [],
            'strategic_metrics': [],
            'alerts': []
        }

        # FastAPI application
        self.app = FastAPI(
            title="AILOOS Executive Dashboard API",
            description="Executive-level business intelligence and strategic metrics dashboard",
            version="1.0.0"
        )

        # Configurar middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Configurar rutas
        self._setup_routes()

        logger.info("🚀 ExecutiveDashboard initialized")

    def _setup_routes(self):
        """Configurar rutas del dashboard ejecutivo."""

        @self.app.get("/")
        async def get_executive_dashboard():
            """Obtener dashboard ejecutivo completo."""
            return self.get_executive_dashboard_data()

        @self.app.get("/api/executive/kpis")
        async def get_business_kpis(user: dict = Depends(get_current_user)):
            """Obtener KPIs de negocio."""
            if not self._has_executive_access(user):
                raise HTTPException(status_code=403, detail="Acceso ejecutivo requerido")

            return {
                "business_kpis": self._business_kpis_to_dict(),
                "timestamp": datetime.now().isoformat()
            }

        @self.app.get("/api/executive/strategic")
        async def get_strategic_metrics(user: dict = Depends(get_current_user)):
            """Obtener métricas estratégicas."""
            if not self._has_executive_access(user):
                raise HTTPException(status_code=403, detail="Acceso ejecutivo requerido")

            return {
                "strategic_metrics": self._strategic_metrics_to_dict(),
                "timestamp": datetime.now().isoformat()
            }

        @self.app.get("/api/executive/alerts")
        async def get_executive_alerts(user: dict = Depends(get_current_user)):
            """Obtener alertas ejecutivas."""
            if not self._has_executive_access(user):
                raise HTTPException(status_code=403, detail="Acceso ejecutivo requerido")

            return {
                "alerts": [self._alert_to_dict(alert) for alert in self.executive_alerts[-20:]],
                "active_count": len([a for a in self.executive_alerts if not a.resolved]),
                "timestamp": datetime.now().isoformat()
            }

        @self.app.post("/api/executive/alerts/{alert_id}/acknowledge")
        async def acknowledge_alert(alert_id: str, user: dict = Depends(get_current_user)):
            """Reconocer alerta ejecutiva."""
            if not self._has_executive_access(user):
                raise HTTPException(status_code=403, detail="Acceso ejecutivo requerido")

            if self._acknowledge_alert(alert_id, user.get("username")):
                return {"message": f"Alerta {alert_id} reconocida por {user.get('username')}"}
            else:
                raise HTTPException(status_code=404, detail="Alerta no encontrada")

        @self.app.get("/api/executive/dashboard")
        async def get_full_dashboard(user: dict = Depends(get_current_user)):
            """Obtener dashboard completo filtrado por rol."""
            if not self._has_executive_access(user):
                raise HTTPException(status_code=403, detail="Acceso ejecutivo requerido")

            return self.get_executive_dashboard_data(user.get("roles", []))

        @self.app.get("/api/executive/reports/{report_type}")
        async def generate_executive_report(report_type: str, user: dict = Depends(get_current_user)):
            """Generar reporte ejecutivo."""
            if not self._has_executive_access(user):
                raise HTTPException(status_code=403, detail="Acceso ejecutivo requerido")

            try:
                return await self.generate_executive_report(report_type)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.websocket("/ws/executive/{role}")
        async def executive_websocket(websocket: WebSocket, role: str, user: dict = Depends(get_current_user)):
            """WebSocket para actualizaciones en tiempo real por rol ejecutivo."""
            if not self._has_executive_access(user) or role not in [r.value for r in ExecutiveRole]:
                await websocket.close(code=1008)  # Policy violation
                return

            await self.handle_executive_websocket(websocket, role, user.get("username"))

        @self.app.get("/api/executive/health")
        async def get_dashboard_health():
            """Obtener estado de salud del dashboard ejecutivo."""
            return self.get_health_status()

    def _has_executive_access(self, user: dict) -> bool:
        """Verificar si el usuario tiene acceso ejecutivo."""
        user_roles = user.get("roles", [])
        executive_roles = ["admin", "ceo", "cto", "cfo", "coo", "cmo"]

        return any(role in executive_roles for role in user_roles)

    async def start_monitoring(self):
        """Iniciar monitoreo ejecutivo."""
        if self.is_running:
            return

        self.is_running = True
        logger.info("📊 Starting executive monitoring")

        # Tarea de monitoreo continuo
        asyncio.create_task(self._executive_monitoring_loop())

    async def stop_monitoring(self):
        """Detener monitoreo ejecutivo."""
        self.is_running = False
        logger.info("🛑 Executive monitoring stopped")

    async def _executive_monitoring_loop(self):
        """Loop principal de monitoreo ejecutivo."""
        last_broadcast = 0.0

        while self.is_running:
            try:
                await self._update_executive_metrics()
                await self._check_executive_alerts()
                await self._notify_callbacks()

                self.last_update = asyncio.get_event_loop().time()

                # Broadcast WebSocket updates
                current_time = asyncio.get_event_loop().time()
                if current_time - last_broadcast >= 30.0:  # Broadcast cada 30 segundos
                    await self._broadcast_executive_updates()
                    last_broadcast = current_time

            except Exception as e:
                logger.error(f"❌ Error in executive monitoring loop: {e}")

            await asyncio.sleep(self.update_interval)

    async def _update_executive_metrics(self):
        """Actualizar métricas ejecutivas."""
        try:
            # Obtener datos del state manager
            system_metrics = self.state_manager.get_system_metrics()
            system_status = self.state_manager.get_system_status()

            # Calcular KPIs de negocio
            await self._calculate_business_kpis(system_metrics, system_status)

            # Calcular métricas estratégicas
            await self._calculate_strategic_metrics(system_metrics, system_status)

            # Almacenar en historial
            self._store_executive_metrics_history()

        except Exception as e:
            logger.error(f"❌ Error updating executive metrics: {e}")

    async def _calculate_business_kpis(self, system_metrics: Any, system_status: Dict[str, Any]):
        """Calcular KPIs de negocio."""
        try:
            active_nodes = system_status.get("total_components", 0)
            federated_sessions = system_metrics.federated_sessions_active

            # KPI reales pendientes de integracion con EmpoorioChain/DracmaSToken
            self.business_kpis.roi_per_node = 0.0
            self.business_kpis.total_roi = 0.0
            self.business_kpis.energy_efficiency_flops_per_watt = 0.0
            self.business_kpis.carbon_footprint_kg_co2 = 0.0

            # Uptime del sistema
            self.business_kpis.system_uptime_percentage = system_status.get("system_uptime_percentage", 99.9)

            # Latencia promedio
            self.business_kpis.average_latency_ms = system_status.get("average_latency_ms", 0.0)

            # Throughput
            self.business_kpis.total_throughput_requests_per_second = system_metrics.total_data_processed / 3600.0

            # Métricas federadas (pendientes de fuente real)
            self.business_kpis.federated_tests_completed = 0
            self.business_kpis.average_accuracy_percentage = getattr(system_metrics, "average_accuracy", 0.0) or 0.0
            self.business_kpis.training_rounds_completed = 0
            self.business_kpis.concurrent_nodes_max = 0
            self.business_kpis.convergence_rate_percentage = 0.0

            # Recompensas distribuidas (bridge)
            try:
                rewards_stats = await self.dracma_manager.get_system_stats()
                totals = rewards_stats.get("totals", {})
                self.business_kpis.total_rewards_distributed = float(
                    totals.get("total_rewards", 0.0)
                )
            except Exception as e:
                logger.warning(f"No se pudo obtener rewards_totals: {e}")
                self.business_kpis.total_rewards_distributed = 0.0

            # Usuarios activos (pendiente de fuente real)
            self.business_kpis.active_users_count = 0

            # Datos procesados
            self.business_kpis.data_processed_gb = system_metrics.total_data_processed / (1024**3)

            # Modelos desplegados
            self.business_kpis.models_deployed_count = system_metrics.models_deployed

        except Exception as e:
            logger.error(f"❌ Error calculating business KPIs: {e}")

    async def _calculate_strategic_metrics(self, system_metrics: Any, system_status: Dict[str, Any]):
        """Calcular métricas estratégicas."""
        try:
            # Metricas estrategicas pendientes de fuente real
            self.strategic_metrics.market_penetration_percentage = 0.0
            self.strategic_metrics.competitive_advantage_score = 0.0
            self.strategic_metrics.innovation_index = 0.0
            self.strategic_metrics.customer_satisfaction_score = 0.0
            self.strategic_metrics.scalability_score = 0.0
            self.strategic_metrics.security_compliance_score = 0.0
            self.strategic_metrics.sustainability_score = 0.0
            self.strategic_metrics.technology_maturity_level = 0

        except Exception as e:
            logger.error(f"❌ Error calculating strategic metrics: {e}")

    async def _check_executive_alerts(self):
        """Verificar condiciones para alertas ejecutivas."""
        try:
            # Alerta crítica: ROI negativo o muy bajo
            if self.business_kpis.roi_per_node < 10.0:
                await self._create_executive_alert(
                    priority="critical",
                    category="business",
                    title="ROI Críticamente Bajo",
                    description=f"ROI por nodo: ${self.business_kpis.roi_per_node:.2f} - Por debajo del umbral mínimo",
                    impact_assessment="Impacto significativo en la rentabilidad del negocio",
                    recommended_actions=[
                        "Revisar estrategia de pricing",
                        "Optimizar costos operativos",
                        "Evaluar eficiencia de recursos"
                    ]
                )

            # Alerta alta: Baja uptime del sistema
            if self.business_kpis.system_uptime_percentage < 99.5:
                await self._create_executive_alert(
                    priority="high",
                    category="operational",
                    title="Degradación de Uptime del Sistema",
                    description=f"Uptime del sistema: {self.business_kpis.system_uptime_percentage:.2f}%",
                    impact_assessment="Posible impacto en SLA y confianza del cliente",
                    recommended_actions=[
                        "Investigar causa raíz",
                        "Implementar medidas de contingencia",
                        "Revisar procedimientos de mantenimiento"
                    ]
                )

            # Alerta media: Alta latencia
            if self.business_kpis.average_latency_ms > 50.0:
                await self._create_executive_alert(
                    priority="medium",
                    category="technical",
                    title="Latencia Elevada Detectada",
                    description=f"Latencia promedio: {self.business_kpis.average_latency_ms:.1f}ms",
                    impact_assessment="Posible degradación en experiencia de usuario",
                    recommended_actions=[
                        "Optimizar infraestructura de red",
                        "Revisar configuración de balanceo de carga",
                        "Implementar caching avanzado"
                    ]
                )

            # Alerta baja: Alta huella de carbono
            if self.business_kpis.carbon_footprint_kg_co2 > 100.0:
                await self._create_executive_alert(
                    priority="low",
                    category="business",
                    title="Huella de Carbono Elevada",
                    description=f"Emisiones CO2: {self.business_kpis.carbon_footprint_kg_co2:.1f}kg",
                    impact_assessment="Impacto en objetivos de sostenibilidad",
                    recommended_actions=[
                        "Evaluar eficiencia energética",
                        "Considerar migración a proveedores verdes",
                        "Implementar medidas de compensación"
                    ]
                )

        except Exception as e:
            logger.error(f"❌ Error checking executive alerts: {e}")

    async def _create_executive_alert(self, priority: str, category: str, title: str,
                                    description: str, impact_assessment: str,
                                    recommended_actions: List[str]):
        """Crear alerta ejecutiva."""
        alert = ExecutiveAlert(
            alert_id=f"exec_alert_{int(asyncio.get_event_loop().time())}_{hash(title) % 10000}",
            priority=priority,
            category=category,
            title=title,
            description=description,
            impact_assessment=impact_assessment,
            recommended_actions=recommended_actions,
            timestamp=asyncio.get_event_loop().time()
        )

        self.executive_alerts.append(alert)

        # Mantener solo últimas 50 alertas
        if len(self.executive_alerts) > 50:
            self.executive_alerts.pop(0)

        # Notificar a través del servicio de notificaciones si está disponible
        if self.notification_service:
            try:
                await self.notification_service.send_executive_alert(alert)
            except Exception as e:
                logger.warning(f"Failed to send executive alert notification: {e}")

        # Notificar callbacks
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    await asyncio.get_event_loop().run_in_executor(None, callback, alert)
            except Exception as e:
                logger.error(f"Error in executive alert callback: {e}")

        logger.warning(f"🚨 Executive Alert Created: {priority.upper()} - {title}")

    def _acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Reconocer alerta ejecutiva."""
        for alert in self.executive_alerts:
            if alert.alert_id == alert_id and not alert.acknowledged:
                alert.acknowledged = True
                alert.acknowledged_by = acknowledged_by
                logger.info(f"✅ Executive alert {alert_id} acknowledged by {acknowledged_by}")
                return True
        return False

    def _store_executive_metrics_history(self):
        """Almacenar métricas en historial."""
        timestamp = asyncio.get_event_loop().time()

        self.metrics_history['business_kpis'].append({
            'timestamp': timestamp,
            'roi_per_node': self.business_kpis.roi_per_node,
            'total_roi': self.business_kpis.total_roi,
            'system_uptime': self.business_kpis.system_uptime_percentage,
            'average_latency': self.business_kpis.average_latency_ms,
            'federated_tests_completed': self.business_kpis.federated_tests_completed
        })

        self.metrics_history['strategic_metrics'].append({
            'timestamp': timestamp,
            'market_penetration': self.strategic_metrics.market_penetration_percentage,
            'competitive_advantage': self.strategic_metrics.competitive_advantage_score,
            'innovation_index': self.strategic_metrics.innovation_index,
            'customer_satisfaction': self.strategic_metrics.customer_satisfaction_score
        })

        # Mantener solo últimas 100 entradas
        for metric_type in self.metrics_history:
            if len(self.metrics_history[metric_type]) > 100:
                self.metrics_history[metric_type].pop(0)

    async def _notify_callbacks(self):
        """Notificar callbacks de actualización."""
        for callback in self.update_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self)
                else:
                    await asyncio.get_event_loop().run_in_executor(None, callback, self)
            except Exception as e:
                logger.error(f"Error in executive update callback: {e}")

    async def _broadcast_executive_updates(self):
        """Broadcast updates a conexiones WebSocket por rol."""
        try:
            dashboard_data = self.get_executive_dashboard_data()

            for role, connections in self.websocket_connections.items():
                role_filtered_data = self._filter_data_by_executive_role(dashboard_data, role)

                disconnected_clients = []
                for client_id, websocket in connections.items():
                    try:
                        await websocket.send_json({
                            "type": "executive_update",
                            "role": role,
                            "timestamp": asyncio.get_event_loop().time(),
                            "data": role_filtered_data
                        })
                    except Exception as e:
                        logger.warning(f"Failed to send executive update to {client_id}: {e}")
                        disconnected_clients.append(client_id)

                # Limpiar conexiones desconectadas
                for client_id in disconnected_clients:
                    del connections[client_id]

        except Exception as e:
            logger.error(f"Error broadcasting executive updates: {e}")

    async def handle_executive_websocket(self, websocket: WebSocket, role: str, client_id: str):
        """Manejar conexión WebSocket para rol ejecutivo específico."""
        await websocket.accept()
        self.websocket_connections[role][client_id] = websocket

        logger.info(f"📡 Executive WebSocket connected: {client_id} ({role})")

        try:
            # Enviar datos iniciales
            initial_data = self.get_executive_dashboard_data([role])
            await websocket.send_json({
                "type": "initial_data",
                "role": role,
                "timestamp": asyncio.get_event_loop().time(),
                "data": initial_data
            })

            # Mantener conexión viva
            while True:
                # Esperar mensajes del cliente o timeout
                try:
                    message = await asyncio.wait_for(
                        websocket.receive_json(),
                        timeout=60.0  # Ping cada minuto
                    )

                    # Procesar mensajes del cliente
                    await self._handle_executive_websocket_message(websocket, role, client_id, message)

                except asyncio.TimeoutError:
                    # Enviar ping para mantener conexión
                    await websocket.send_json({"type": "ping"})

        except WebSocketDisconnect:
            logger.info(f"📡 Executive WebSocket disconnected: {client_id} ({role})")
        except Exception as e:
            logger.error(f"Executive WebSocket error for {client_id}: {e}")
        finally:
            if client_id in self.websocket_connections[role]:
                del self.websocket_connections[role][client_id]

    async def _handle_executive_websocket_message(self, websocket: WebSocket, role: str,
                                                client_id: str, message: Dict[str, Any]):
        """Manejar mensajes WebSocket de clientes ejecutivos."""
        try:
            message_type = message.get("type", "unknown")

            if message_type == "acknowledge_alert":
                alert_id = message.get("alert_id")
                if alert_id and self._acknowledge_alert(alert_id, client_id):
                    await websocket.send_json({
                        "type": "alert_acknowledged",
                        "alert_id": alert_id,
                        "acknowledged_by": client_id
                    })

            elif message_type == "request_history":
                metric_type = message.get("metric_type", "business_kpis")
                limit = message.get("limit", 50)

                history = self.get_metrics_history(metric_type, limit)
                await websocket.send_json({
                    "type": "history_data",
                    "metric_type": metric_type,
                    "data": history
                })

        except Exception as e:
            logger.error(f"Error handling executive WebSocket message: {e}")
            await websocket.send_json({
                "type": "error",
                "message": f"Error processing message: {e}"
            })

    def get_executive_dashboard_data(self, user_roles: List[str] = None) -> Dict[str, Any]:
        """Obtener datos completos del dashboard ejecutivo."""
        return {
            "business_kpis": self._business_kpis_to_dict(),
            "strategic_metrics": self._strategic_metrics_to_dict(),
            "executive_alerts": [self._alert_to_dict(alert) for alert in self.executive_alerts[-10:]],
            "active_alerts_count": len([a for a in self.executive_alerts if not a.resolved]),
            "last_update": self.last_update,
            "timestamp": asyncio.get_event_loop().time(),
            "filtered_by_roles": user_roles or []
        }

    def _filter_data_by_executive_role(self, data: Dict[str, Any], role: str) -> Dict[str, Any]:
        """Filtrar datos según rol ejecutivo."""
        filtered = data.copy()

        # CEO ve todo
        if role == "ceo":
            return filtered

        # CTO enfocado en métricas técnicas y estratégicas
        if role == "cto":
            filtered["business_kpis"] = {k: v for k, v in filtered["business_kpis"].items()
                                       if k in ["federated_tests_completed", "average_accuracy_percentage",
                                              "training_rounds_completed", "convergence_rate_percentage",
                                              "models_deployed_count"]}
            filtered["strategic_metrics"] = {k: v for k, v in filtered["strategic_metrics"].items()
                                           if k in ["innovation_index", "technology_maturity_level",
                                                  "scalability_score"]}

        # CFO enfocado en ROI y costos
        elif role == "cfo":
            filtered["business_kpis"] = {k: v for k, v in filtered["business_kpis"].items()
                                       if "roi" in k or "cost" in k or "reward" in k}
            filtered["strategic_metrics"] = {k: v for k, v in filtered["strategic_metrics"].items()
                                           if k in ["market_penetration_percentage", "sustainability_score"]}

        # COO enfocado en operaciones
        elif role == "coo":
            filtered["business_kpis"] = {k: v for k, v in filtered["business_kpis"].items()
                                       if "uptime" in k or "latency" in k or "throughput" in k}
            filtered["strategic_metrics"] = {k: v for k, v in filtered["strategic_metrics"].items()
                                           if k in ["scalability_score", "customer_satisfaction_score"]}

        return filtered

    def _business_kpis_to_dict(self) -> Dict[str, Any]:
        """Convertir KPIs de negocio a diccionario."""
        return {
            "roi_per_node": round(self.business_kpis.roi_per_node, 2),
            "total_roi": round(self.business_kpis.total_roi, 2),
            "energy_efficiency_flops_per_watt": round(self.business_kpis.energy_efficiency_flops_per_watt, 2),
            "carbon_footprint_kg_co2": round(self.business_kpis.carbon_footprint_kg_co2, 2),
            "system_uptime_percentage": round(self.business_kpis.system_uptime_percentage, 2),
            "average_latency_ms": round(self.business_kpis.average_latency_ms, 2),
            "total_throughput_requests_per_second": round(self.business_kpis.total_throughput_requests_per_second, 2),
            "federated_tests_completed": self.business_kpis.federated_tests_completed,
            "average_accuracy_percentage": round(self.business_kpis.average_accuracy_percentage, 2),
            "training_rounds_completed": self.business_kpis.training_rounds_completed,
            "concurrent_nodes_max": self.business_kpis.concurrent_nodes_max,
            "convergence_rate_percentage": round(self.business_kpis.convergence_rate_percentage, 2),
            "total_rewards_distributed": round(self.business_kpis.total_rewards_distributed, 2),
            "active_users_count": self.business_kpis.active_users_count,
            "data_processed_gb": round(self.business_kpis.data_processed_gb, 2),
            "models_deployed_count": self.business_kpis.models_deployed_count
        }

    def _strategic_metrics_to_dict(self) -> Dict[str, Any]:
        """Convertir métricas estratégicas a diccionario."""
        return {
            "market_penetration_percentage": round(self.strategic_metrics.market_penetration_percentage, 2),
            "competitive_advantage_score": round(self.strategic_metrics.competitive_advantage_score, 2),
            "innovation_index": round(self.strategic_metrics.innovation_index, 2),
            "customer_satisfaction_score": round(self.strategic_metrics.customer_satisfaction_score, 2),
            "scalability_score": round(self.strategic_metrics.scalability_score, 2),
            "security_compliance_score": round(self.strategic_metrics.security_compliance_score, 2),
            "sustainability_score": round(self.strategic_metrics.sustainability_score, 2),
            "technology_maturity_level": self.strategic_metrics.technology_maturity_level
        }

    def _alert_to_dict(self, alert: ExecutiveAlert) -> Dict[str, Any]:
        """Convertir alerta a diccionario."""
        return {
            "alert_id": alert.alert_id,
            "priority": alert.priority,
            "category": alert.category,
            "title": alert.title,
            "description": alert.description,
            "impact_assessment": alert.impact_assessment,
            "recommended_actions": alert.recommended_actions,
            "timestamp": alert.timestamp,
            "acknowledged": alert.acknowledged,
            "acknowledged_by": alert.acknowledged_by,
            "resolved": alert.resolved,
            "resolved_at": alert.resolved_at
        }

    def get_metrics_history(self, metric_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtener historial de métricas."""
        if metric_type not in self.metrics_history:
            return []

        return self.metrics_history[metric_type][-limit:]

    def get_health_status(self) -> Dict[str, Any]:
        """Obtener estado de salud del dashboard ejecutivo."""
        return {
            "is_running": self.is_running,
            "last_update": self.last_update,
            "active_websocket_connections": sum(len(conns) for conns in self.websocket_connections.values()),
            "total_alerts": len(self.executive_alerts),
            "active_alerts": len([a for a in self.executive_alerts if not a.resolved]),
            "metrics_history_size": {k: len(v) for k, v in self.metrics_history.items()},
            "timestamp": asyncio.get_event_loop().time()
        }

    async def generate_executive_report(self, report_type: str) -> Dict[str, Any]:
        """Generar reporte ejecutivo."""
        if report_type == "business_kpis":
            return {
                "report_type": "business_kpis",
                "generated_at": datetime.now().isoformat(),
                "data": self._business_kpis_to_dict(),
                "summary": self._generate_business_kpi_summary()
            }
        elif report_type == "strategic_metrics":
            return {
                "report_type": "strategic_metrics",
                "generated_at": datetime.now().isoformat(),
                "data": self._strategic_metrics_to_dict(),
                "summary": self._generate_strategic_metrics_summary()
            }
        elif report_type == "executive_summary":
            return {
                "report_type": "executive_summary",
                "generated_at": datetime.now().isoformat(),
                "business_kpis": self._business_kpis_to_dict(),
                "strategic_metrics": self._strategic_metrics_to_dict(),
                "active_alerts": [self._alert_to_dict(alert) for alert in self.executive_alerts[-5:]],
                "summary": self._generate_executive_summary()
            }
        else:
            raise ValueError(f"Tipo de reporte desconocido: {report_type}")

    def _generate_business_kpi_summary(self) -> str:
        """Generar resumen de KPIs de negocio."""
        return f"""
        RESUMEN EJECUTIVO - KPIs de Negocio

        Rendimiento Financiero:
        • ROI por Nodo: ${self.business_kpis.roi_per_node:.2f}
        • ROI Total: ${self.business_kpis.total_roi:.2f}
        • Recompensas Distribuidas: ${self.business_kpis.total_rewards_distributed:.2f}

        Eficiencia Operativa:
        • Uptime del Sistema: {self.business_kpis.system_uptime_percentage:.2f}%
        • Latencia Promedio: {self.business_kpis.average_latency_ms:.1f}ms
        • Throughput: {self.business_kpis.total_throughput_requests_per_second:.1f} req/s

        Sostenibilidad:
        • Eficiencia Energética: {self.business_kpis.energy_efficiency_flops_per_watt:.1f} FLOPs/W
        • Huella de Carbono: {self.business_kpis.carbon_footprint_kg_co2:.1f} kg CO2

        Métricas Federadas:
        • Tests Completados: {self.business_kpis.federated_tests_completed}
        • Accuracy Promedio: {self.business_kpis.average_accuracy_percentage:.1f}%
        • Rondas de Entrenamiento: {self.business_kpis.training_rounds_completed}
        • Tasa de Convergencia: {self.business_kpis.convergence_rate_percentage:.1f}%
        """

    def _generate_strategic_metrics_summary(self) -> str:
        """Generar resumen de métricas estratégicas."""
        return f"""
        RESUMEN EJECUTIVO - Métricas Estratégicas

        Posicionamiento de Mercado:
        • Penetración de Mercado: {self.strategic_metrics.market_penetration_percentage:.1f}%
        • Ventaja Competitiva: {self.strategic_metrics.competitive_advantage_score:.1f}/10

        Innovación y Tecnología:
        • Índice de Innovación: {self.strategic_metrics.innovation_index:.1f}/100
        • Nivel de Madurez Tecnológica: {self.strategic_metrics.technology_maturity_level}/5

        Experiencia del Cliente:
        • Satisfacción del Cliente: {self.strategic_metrics.customer_satisfaction_score:.1f}/100
        • Escalabilidad: {self.strategic_metrics.scalability_score:.1f}/100

        Gobernanza:
        • Cumplimiento de Seguridad: {self.strategic_metrics.security_compliance_score:.1f}/100
        • Sostenibilidad: {self.strategic_metrics.sustainability_score:.1f}/100
        """

    def _generate_executive_summary(self) -> str:
        """Generar resumen ejecutivo completo."""
        active_alerts = len([a for a in self.executive_alerts if not a.resolved])

        return f"""
        RESUMEN EJECUTIVO COMPLETO - AILOOS

        ESTADO GENERAL:
        • Sistema Operativo: {'✅ Saludable' if self.business_kpis.system_uptime_percentage > 99.5 else '⚠️ Requiere Atención'}
        • Alertas Activas: {active_alerts}
        • Última Actualización: {datetime.fromtimestamp(self.last_update).strftime('%Y-%m-%d %H:%M:%S')}

        KPIs PRINCIPALES:
        • ROI Total: ${self.business_kpis.total_roi:.2f}
        • Uptime: {self.business_kpis.system_uptime_percentage:.2f}%
        • Accuracy Federado: {self.business_kpis.average_accuracy_percentage:.1f}%
        • Tests Validados: {self.business_kpis.federated_tests_completed}

        MÉTRICAS ESTRATÉGICAS:
        • Ventaja Competitiva: {self.strategic_metrics.competitive_advantage_score:.1f}/10
        • Satisfacción Cliente: {self.strategic_metrics.customer_satisfaction_score:.1f}/100
        • Madurez Tecnológica: Nivel {self.strategic_metrics.technology_maturity_level}

        RECOMENDACIONES:
        {self._generate_recommendations()}
        """

    def _generate_recommendations(self) -> str:
        """Generar recomendaciones basadas en métricas."""
        recommendations = []

        if self.business_kpis.roi_per_node < 20.0:
            recommendations.append("• Optimizar estrategia de monetización para mejorar ROI")

        if self.business_kpis.system_uptime_percentage < 99.9:
            recommendations.append("• Implementar mejoras en alta disponibilidad")

        if self.business_kpis.average_latency_ms > 30.0:
            recommendations.append("• Optimizar performance del sistema")

        if self.strategic_metrics.innovation_index < 80.0:
            recommendations.append("• Acelerar desarrollo de nuevas funcionalidades")

        if not recommendations:
            recommendations.append("• Continuar con la estrategia actual - rendimiento excelente")

        return "\n".join(recommendations)

    def register_update_callback(self, callback: Callable):
        """Registrar callback para actualizaciones."""
        self.update_callbacks.append(callback)

    def register_alert_callback(self, callback: Callable):
        """Registrar callback para alertas."""
        self.alert_callbacks.append(callback)


# Función de conveniencia
def create_executive_dashboard(notification_service: Optional[NotificationService] = None) -> ExecutiveDashboard:
    """Crear instancia del dashboard ejecutivo."""
    return ExecutiveDashboard(notification_service=notification_service)


# Función para iniciar dashboard ejecutivo
async def start_executive_dashboard(notification_service: Optional[NotificationService] = None):
    """Función de conveniencia para iniciar el dashboard ejecutivo."""
    dashboard = create_executive_dashboard(notification_service)
    await dashboard.start_monitoring()
    return dashboard
