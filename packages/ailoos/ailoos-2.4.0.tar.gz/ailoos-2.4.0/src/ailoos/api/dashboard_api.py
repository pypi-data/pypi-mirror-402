"""
API unificada para el Dashboard Interactivo de AILOOS.
Integra datos de refinería, hardware, wallets y entrenamiento federado.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

from ..core.logging import get_logger
from ..data.refinery_engine import RefineryEngine
from ..cli.hardware import HardwareMonitor
from ..federated.coordinator import FederatedCoordinator
from ..web.wallet_integration import get_wallet_integration

logger = get_logger(__name__)


class DashboardStatsRequest(BaseModel):
    """Solicitud de estadísticas del dashboard."""
    include_hardware: bool = True
    include_refinery: bool = True
    include_wallets: bool = True
    include_federated: bool = True


class StartFederatedMissionRequest(BaseModel):
    """Solicitud para iniciar una misión federada."""
    session_id: str
    model_name: str = "EmpoorioLM"
    rounds: int = 5
    min_nodes: int = 3
    dataset_name: str = "federated_dataset"


class DashboardAPI:
    """
    API unificada que combina todas las funcionalidades del dashboard.
    Proporciona endpoints para monitoreo integrado y control de misiones.
    """

    def __init__(self):
        self.app = FastAPI(
            title="AILOOS Unified Dashboard API",
            description="API unificada para dashboard interactivo de AILOOS",
            version="1.0.0"
        )

        # Componentes del sistema
        self.refinery_engine = None
        self.hardware_monitor = HardwareMonitor()
        self.federated_coordinator = None
        self.wallet_integration = get_wallet_integration()

        # Estado del sistema
        self.system_status = {
            "last_update": 0,
            "components_health": {},
            "active_missions": []
        }

        # Inicializar componentes
        self._initialize_components()

        # Configurar rutas
        self._setup_routes()

        logger.info("🚀 Unified Dashboard API initialized")

    def _initialize_components(self):
        """Inicializar componentes del sistema."""
        try:
            # Refinery Engine
            try:
                from ..data.refinery_engine import get_refinery_engine
                self.refinery_engine = get_refinery_engine()
                self.system_status["components_health"]["refinery"] = "healthy"
            except Exception as e:
                logger.warning(f"Could not initialize refinery engine: {e}")
                self.system_status["components_health"]["refinery"] = "unavailable"

            # Federated Coordinator
            try:
                from ..federated.coordinator import get_federated_coordinator
                self.federated_coordinator = get_federated_coordinator()
                self.system_status["components_health"]["federated"] = "healthy"
            except Exception as e:
                logger.warning(f"Could not initialize federated coordinator: {e}")
                self.system_status["components_health"]["federated"] = "unavailable"

            # Wallet Integration
            self.system_status["components_health"]["wallets"] = "healthy"

            # Hardware Monitor
            self.system_status["components_health"]["hardware"] = "healthy"

        except Exception as e:
            logger.error(f"Error initializing dashboard components: {e}")

    def _setup_routes(self):
        """Configurar todas las rutas de la API."""

        @self.app.get("/health")
        async def health_check():
            """Health check del dashboard unificado."""
            return {
                "status": "healthy",
                "timestamp": time.time(),
                "components": self.system_status["components_health"],
                "active_missions": len(self.system_status["active_missions"])
            }

        @self.app.get("/stats")
        async def get_dashboard_stats(request: DashboardStatsRequest = None):
            """Obtener estadísticas unificadas del dashboard."""
            if request is None:
                request = DashboardStatsRequest()

            stats = {
                "timestamp": time.time(),
                "system_health": "healthy"
            }

            try:
                # Hardware stats
                if request.include_hardware:
                    hardware_info = self.hardware_monitor.get_all_hardware_info()
                    stats["hardware"] = {
                        "cpu_usage": hardware_info["cpu"]["usage_percent"],
                        "memory_usage": hardware_info["memory"]["usage_percent"],
                        "disk_usage": hardware_info["disk"]["usage_percent"],
                        "gpu_usage": hardware_info["gpu"]["usage_percent"] if hardware_info["gpu"]["usage_percent"] else 0,
                        "status": "healthy" if hardware_info["cpu"]["usage_percent"] < 90 else "warning"
                    }

                # Refinery stats
                if request.include_refinery and self.refinery_engine:
                    refinery_status = await self._get_refinery_stats()
                    stats["refinery"] = refinery_status
                elif request.include_refinery:
                    stats["refinery"] = {"status": "unavailable", "active_pipelines": 0, "processed_data": 0}

                # Wallet stats
                if request.include_wallets:
                    wallet_status = await self._get_wallet_stats()
                    stats["wallets"] = wallet_status

                # Federated stats
                if request.include_federated and self.federated_coordinator:
                    federated_status = await self._get_federated_stats()
                    stats["federated"] = federated_status
                elif request.include_federated:
                    stats["federated"] = {"status": "unavailable", "active_sessions": 0, "total_nodes": 0}

                self.system_status["last_update"] = time.time()

            except Exception as e:
                logger.error(f"Error getting dashboard stats: {e}")
                stats["system_health"] = "error"
                stats["error"] = str(e)

            return stats

        @self.app.post("/missions/federated/start")
        async def start_federated_mission(request: StartFederatedMissionRequest, background_tasks: BackgroundTasks):
            """Iniciar una nueva misión de entrenamiento federado."""
            try:
                if not self.federated_coordinator:
                    raise HTTPException(status_code=503, detail="Federated coordinator not available")

                # Crear sesión federada
                session_data = {
                    "session_id": request.session_id,
                    "model_name": request.model_name,
                    "rounds": request.rounds,
                    "min_nodes": request.min_nodes,
                    "dataset_name": request.dataset_name
                }

                # Iniciar en background
                background_tasks.add_task(self._start_federated_session, session_data)

                # Registrar misión activa
                self.system_status["active_missions"].append({
                    "id": request.session_id,
                    "type": "federated_training",
                    "status": "starting",
                    "start_time": time.time()
                })

                return {
                    "success": True,
                    "mission_id": request.session_id,
                    "status": "starting",
                    "message": "Federated training mission started"
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error starting federated mission: {e}")
                raise HTTPException(status_code=500, detail=f"Error starting mission: {str(e)}")

        @self.app.post("/missions/federated/{mission_id}/stop")
        async def stop_federated_mission(mission_id: str):
            """Detener una misión federada."""
            try:
                if not self.federated_coordinator:
                    raise HTTPException(status_code=503, detail="Federated coordinator not available")

                # Detener sesión
                await self.federated_coordinator.end_session(mission_id)

                # Actualizar estado de la misión
                for mission in self.system_status["active_missions"]:
                    if mission["id"] == mission_id:
                        mission["status"] = "stopped"
                        mission["end_time"] = time.time()
                        break

                return {
                    "success": True,
                    "mission_id": mission_id,
                    "status": "stopped",
                    "message": "Federated training mission stopped"
                }

            except Exception as e:
                logger.error(f"Error stopping federated mission: {e}")
                raise HTTPException(status_code=500, detail=f"Error stopping mission: {str(e)}")

        @self.app.get("/missions/active")
        async def get_active_missions():
            """Obtener misiones activas."""
            return {
                "missions": self.system_status["active_missions"],
                "total": len(self.system_status["active_missions"]),
                "timestamp": time.time()
            }

        @self.app.post("/refinery/start-pipeline")
        async def start_refinery_pipeline(pipeline_config: Dict[str, Any]):
            """Iniciar un pipeline de refinería."""
            try:
                if not self.refinery_engine:
                    raise HTTPException(status_code=503, detail="Refinery engine not available")

                # Iniciar pipeline
                pipeline_id = await self.refinery_engine.start_pipeline(pipeline_config)

                return {
                    "success": True,
                    "pipeline_id": pipeline_id,
                    "status": "started",
                    "message": "Refinery pipeline started"
                }

            except Exception as e:
                logger.error(f"Error starting refinery pipeline: {e}")
                raise HTTPException(status_code=500, detail=f"Error starting pipeline: {str(e)}")

        @self.app.post("/system/refresh")
        async def refresh_system_data():
            """Refrescar todos los datos del sistema."""
            try:
                # Forzar actualización de componentes
                self._initialize_components()

                # Obtener nuevas estadísticas
                stats = await get_dashboard_stats()

                return {
                    "success": True,
                    "message": "System data refreshed",
                    "stats": stats
                }

            except Exception as e:
                logger.error(f"Error refreshing system data: {e}")
                raise HTTPException(status_code=500, detail=f"Error refreshing data: {str(e)}")

    async def _get_refinery_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de la refinería."""
        try:
            if not self.refinery_engine:
                return {"status": "unavailable"}

            # Obtener estado de pipelines
            pipelines = await self.refinery_engine.get_active_pipelines()
            metrics = await self.refinery_engine.get_metrics()

            return {
                "status": "healthy",
                "active_pipelines": len(pipelines),
                "processed_data": metrics.get("total_processed", 0),
                "efficiency": metrics.get("efficiency", 0),
                "pipelines": pipelines
            }

        except Exception as e:
            logger.error(f"Error getting refinery stats: {e}")
            return {"status": "error", "error": str(e)}

    async def _get_wallet_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de wallets."""
        try:
            connected_wallets = self.wallet_integration.get_connected_wallets()

            total_balance = 0
            active_transactions = 0

            for wallet in connected_wallets:
                total_balance += wallet.balance_dracma
                # Contar transacciones activas (simplificado)
                active_transactions += 1 if wallet.is_connected else 0

            return {
                "status": "healthy",
                "connected_wallets": len(connected_wallets),
                "total_balance": total_balance,
                "active_transactions": active_transactions
            }

        except Exception as e:
            logger.error(f"Error getting wallet stats: {e}")
            return {"status": "error", "error": str(e)}

    async def _get_federated_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de entrenamiento federado."""
        try:
            if not self.federated_coordinator:
                return {"status": "unavailable"}

            sessions = self.federated_coordinator.get_active_sessions()
            nodes = await self.federated_coordinator.get_connected_nodes()

            # Calcular progreso total
            total_progress = 0
            if sessions:
                progresses = [s.get("progress", 0) for s in sessions.values()]
                total_progress = sum(progresses) / len(progresses) if progresses else 0

            return {
                "status": "healthy",
                "active_sessions": len(sessions),
                "total_nodes": len(nodes),
                "training_progress": total_progress,
                "sessions": list(sessions.keys())
            }

        except Exception as e:
            logger.error(f"Error getting federated stats: {e}")
            return {"status": "error", "error": str(e)}

    async def _start_federated_session(self, session_data: Dict[str, Any]):
        """Iniciar sesión federada en background."""
        try:
            if not self.federated_coordinator:
                logger.error("Federated coordinator not available")
                return

            # Crear sesión
            await self.federated_coordinator.create_session(
                session_id=session_data["session_id"],
                model_name=session_data["model_name"],
                rounds=session_data["rounds"],
                min_nodes=session_data["min_nodes"],
                dataset_name=session_data["dataset_name"]
            )

            # Iniciar sesión
            await self.federated_coordinator.start_session(session_data["session_id"])

            # Actualizar estado de la misión
            for mission in self.system_status["active_missions"]:
                if mission["id"] == session_data["session_id"]:
                    mission["status"] = "running"
                    break

            logger.info(f"✅ Federated session {session_data['session_id']} started successfully")

        except Exception as e:
            logger.error(f"❌ Error starting federated session {session_data['session_id']}: {e}")

            # Actualizar estado de error
            for mission in self.system_status["active_missions"]:
                if mission["id"] == session_data["session_id"]:
                    mission["status"] = "error"
                    mission["error"] = str(e)
                    break

    def create_app(self) -> FastAPI:
        """Crear y retornar la aplicación FastAPI."""
        return self.app

    def start_server(self, host: str = "0.0.0.0", port: int = 8003):
        """Iniciar servidor FastAPI."""
        import uvicorn
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )


# Instancia global de la API unificada
dashboard_api = DashboardAPI()


def create_dashboard_app() -> FastAPI:
    """Función de conveniencia para crear la app FastAPI del dashboard unificado."""
    return dashboard_api.create_app()


if __name__ == "__main__":
    # Iniciar servidor para pruebas
    print("🚀 Iniciando AILOOS Unified Dashboard API...")
    dashboard_api.start_server()