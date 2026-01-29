"""
API REST para el sistema federado de AILOOS.
Gestiona sesiones de entrenamiento, nodos participantes y agregación FedAvg.
"""

import asyncio
import json
import os
import time
import statistics
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, WebSocket, WebSocketDisconnect, Request
from pydantic import BaseModel, Field
import uvicorn

from ..federated.session import FederatedSession
from ..federated.trainer import FederatedTrainer
from ..federated.aggregator import FederatedAggregator
from ..infrastructure.ipfs_embedded import IPFSManager
from ..discovery.node_registry import NodeRegistry, get_node_registry
from ..discovery.health_monitor import HealthMonitor, get_health_monitor
from ..monitoring.realtime_monitor import get_realtime_monitor
from ..federated.node_communicator import NodeCommunicator
from ..core.config import get_config
from ..core.logging import get_logger
from ..coordinator.auth.dependencies import conditional_node_auth, get_current_admin
from ..auditing.realtime_monitor import get_realtime_monitor
from ..utils.cache import cached, invalidate_cache, get_cache_manager
from ..core.serializers import get_toon_serializer, get_vsc_serializer, get_json_serializer
from ..core.serialization_middleware import ContentNegotiationMiddleware

logger = get_logger(__name__)


# Modelos Pydantic
class SessionCreateRequest(BaseModel):
    session_id: str = Field(..., description="ID único de la sesión")
    model_name: str = Field(..., description="Nombre del modelo")
    rounds: int = Field(5, ge=1, le=100, description="Número de rondas")
    min_nodes: int = Field(3, ge=1, description="Mínimo de nodos requeridos")
    max_nodes: int = Field(100, ge=1, description="Máximo de nodos permitidos")
    dataset_name: str = Field(..., description="Nombre del dataset")
    privacy_budget: float = Field(1.0, ge=0.1, le=10.0, description="Presupuesto de privacidad")


class NodeJoinRequest(BaseModel):
    session_id: str
    node_id: str
    hardware_info: Dict[str, Any]
    local_data_info: Dict[str, Any]


class WeightUpdateRequest(BaseModel):
    session_id: str
    node_id: str
    round_num: int
    weights_hash: str
    ipfs_cid: str
    num_samples: int
    metrics: Dict[str, Any]


class SessionConfigUpdateRequest(BaseModel):
    rounds: Optional[int] = Field(None, ge=1, le=100, description="Número de rondas")
    min_nodes: Optional[int] = Field(None, ge=1, description="Mínimo de nodos requeridos")
    max_nodes: Optional[int] = Field(None, ge=1, description="Máximo de nodos permitidos")
    privacy_budget: Optional[float] = Field(None, ge=0.1, le=10.0, description="Presupuesto de privacidad")


class FederatedAPI:
    """
    API REST completa para el sistema federado de AILOOS.
    Maneja sesiones de entrenamiento distribuido, agregación de pesos y coordinación de nodos.
    """

    def __init__(self):
        self.app = FastAPI(
            title="AILOOS Federated Learning API",
            description="API para coordinación de entrenamiento federado",
            version="1.0.0"
        )

        # Configuración
        self.config = get_config()
        self.allow_mocks = self._resolve_allow_mocks()

        # Componentes del sistema REALES
        self.active_sessions: Dict[str, FederatedSession] = {}
        self.session_trainers: Dict[str, FederatedTrainer] = {}
        self.session_aggregators: Dict[str, FederatedAggregator] = {}
        self.node_registrations: Dict[str, Dict[str, Any]] = {}
        self.ipfs_manager = IPFSManager()

        # Componentes para monitoreo de nodos federados
        self.node_registry = None
        self.health_monitor = None
        self.realtime_monitor = None
        self.node_communicator = None
        self.websocket_realtime_monitor = get_realtime_monitor()
        self._initialize_node_components()

        # Estadísticas del sistema
        self.system_stats = {
            "total_sessions_created": 0,
            "total_nodes_registered": 0,
            "total_rounds_completed": 0,
            "total_data_processed": 0,
            "start_time": time.time()
        }

        # Serializers optimizados para federated learning
        self.toon_serializer = get_toon_serializer()
        self.vsc_serializer = get_vsc_serializer()
        self.json_serializer = get_json_serializer()

        # Middleware de serialización
        self.serialization_middleware = ContentNegotiationMiddleware(None)

        logger.info("🚀 Federated API initialized with real components and TOON/VSC serialization")

        # Configurar rutas
        self._setup_routes()

    def _initialize_node_components(self):
        """Inicializar componentes para monitoreo de nodos federados."""
        try:
            # Inicializar Node Registry
            self.node_registry = get_node_registry()
            if self.node_registry:
                logger.info("✅ Node Registry initialized")
            else:
                logger.warning("⚠️ Node Registry not available")

            # Inicializar Health Monitor
            self.health_monitor = get_health_monitor()
            if self.health_monitor:
                logger.info("✅ Health Monitor initialized")
            else:
                logger.warning("⚠️ Health Monitor not available")

            # Inicializar Realtime Monitor
            self.realtime_monitor = get_realtime_monitor()
            if self.realtime_monitor:
                logger.info("✅ Realtime Monitor initialized")
            else:
                logger.warning("⚠️ Realtime Monitor not available")

            # Inicializar Node Communicator si se expone desde el runtime
            self.node_communicator = None
            logger.info("ℹ️ Node Communicator components ready")

        except Exception as e:
            logger.error(f"❌ Error initializing node components: {e}")

    def _setup_routes(self):
        """Configurar todas las rutas de la API."""

        @self.app.get("/health")
        async def health_check():
            """Health check del servicio federado."""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "active_sessions": len(self.active_sessions),
                "registered_nodes": len(self.node_registrations)
            }

        # ===== SESSION MANAGEMENT =====

        @self.app.options("/session/create")
        async def options_session_create():
            """OPTIONS handler for session creation."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/session/create")
        async def create_session(request: SessionCreateRequest, current_admin: dict = Depends(get_current_admin)):
            """Crear una nueva sesión de entrenamiento federado REAL."""
            try:
                # Verificar que no existe ya
                if request.session_id in self.active_sessions:
                    raise HTTPException(status_code=409, detail="Session already exists")

                logger.info(f"🎯 Creating federated session: {request.session_id}")

                # Crear sesión REAL
                session = FederatedSession(
                    session_id=request.session_id,
                    model_name=request.model_name,
                    rounds=request.rounds,
                    min_nodes=request.min_nodes,
                    max_nodes=request.max_nodes
                )

                # Crear trainer REAL con modelo EmpoorioLM
                trainer = FederatedTrainer(
                    session_id=request.session_id,
                    model_name=request.model_name,
                    dataset_name=request.dataset_name,
                    privacy_budget=request.privacy_budget
                )

                # Crear aggregator REAL con algoritmo FedAvg
                aggregator = FederatedAggregator(
                    session_id=request.session_id,
                    model_name=request.model_name
                )

                # Distribuir modelo inicial REAL
                initial_cid = await trainer.distribute_initial_model()

                # Almacenar componentes REALES
                self.active_sessions[request.session_id] = session
                self.session_trainers[request.session_id] = trainer
                self.session_aggregators[request.session_id] = aggregator

                # Actualizar estadísticas
                self.system_stats["total_sessions_created"] += 1

                # Invalidate related caches
                cache_manager = get_cache_manager()
                await cache_manager.clear_pattern("federated:*")

                logger.info(f"✅ Session {request.session_id} created with initial model CID: {initial_cid}")

                return {
                    "success": True,
                    "session_id": request.session_id,
                    "status": "created",
                    "initial_model_cid": initial_cid,
                    "message": "Federated session created successfully with real components"
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"❌ Error creating session: {e}")
                raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")

        @self.app.get("/sessions")
        async def list_sessions(current_node: dict = Depends(conditional_node_auth)):
            """Listar todas las sesiones activas."""
            try:
                sessions = []
                for session_id, session in self.active_sessions.items():
                    session_data = session.get_status()
                    session_data["trainer_info"] = self.session_trainers[session_id].get_status()
                    session_data["aggregator_info"] = self.session_aggregators[session_id].get_status()
                    sessions.append(session_data)

                return {
                    "sessions": sessions,
                    "total": len(sessions)
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")

        @self.app.get("/session/{session_id}")
        async def get_session_status(session_id: str):
            """Obtener estado detallado de una sesión."""
            try:
                if session_id not in self.active_sessions:
                    raise HTTPException(status_code=404, detail="Session not found")

                session = self.active_sessions[session_id]
                trainer = self.session_trainers[session_id]
                aggregator = self.session_aggregators[session_id]

                return {
                    "session": session.get_status(),
                    "trainer": trainer.get_status(),
                    "aggregator": aggregator.get_status(),
                    "participants": [
                        {
                            "node_id": node_id,
                            "info": info,
                            "last_update": info.get("last_update")
                        }
                        for node_id, info in self.node_registrations.items()
                        if info.get("session_id") == session_id
                    ]
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error getting session status: {str(e)}")

        @self.app.options("/session/{session_id}")
        async def options_session_delete(session_id: str):
            """OPTIONS handler for session deletion."""
            return {"Allow": "DELETE, OPTIONS"}

        @self.app.delete("/session/{session_id}")
        async def end_session(session_id: str):
            """Finalizar una sesión de entrenamiento."""
            try:
                if session_id not in self.active_sessions:
                    raise HTTPException(status_code=404, detail="Session not found")

                # Limpiar componentes
                del self.active_sessions[session_id]
                if session_id in self.session_trainers:
                    del self.session_trainers[session_id]
                if session_id in self.session_aggregators:
                    del self.session_aggregators[session_id]

                # Limpiar registros de nodos
                nodes_to_remove = [
                    node_id for node_id, info in self.node_registrations.items()
                    if info.get("session_id") == session_id
                ]
                for node_id in nodes_to_remove:
                    del self.node_registrations[node_id]

                return {
                    "success": True,
                    "message": f"Session {session_id} ended successfully"
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error ending session: {str(e)}")

        @self.app.options("/session/{session_id}/start")
        async def options_session_start(session_id: str):
            """OPTIONS handler for starting session."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/session/{session_id}/start")
        async def start_session(session_id: str, current_admin: dict = Depends(get_current_admin)):
            """Iniciar explícitamente una sesión de entrenamiento federado."""
            try:
                if session_id not in self.active_sessions:
                    raise HTTPException(status_code=404, detail="Session not found")

                session = self.active_sessions[session_id]
                session.start_session()

                return {
                    "success": True,
                    "session_id": session_id,
                    "status": session.status,
                    "message": f"Session {session_id} started successfully"
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error starting session: {str(e)}")

        @self.app.options("/session/{session_id}/pause")
        async def options_session_pause(session_id: str):
            """OPTIONS handler for pausing session."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/session/{session_id}/pause")
        async def pause_session(session_id: str, current_admin: dict = Depends(get_current_admin)):
            """Pausar una sesión de entrenamiento federado."""
            try:
                if session_id not in self.active_sessions:
                    raise HTTPException(status_code=404, detail="Session not found")

                session = self.active_sessions[session_id]
                session.pause_session()

                return {
                    "success": True,
                    "session_id": session_id,
                    "status": session.status,
                    "message": f"Session {session_id} paused successfully"
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error pausing session: {str(e)}")

        @self.app.options("/session/{session_id}/resume")
        async def options_session_resume(session_id: str):
            """OPTIONS handler for resuming session."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/session/{session_id}/resume")
        async def resume_session(session_id: str, current_admin: dict = Depends(get_current_admin)):
            """Reanudar una sesión de entrenamiento federado pausada."""
            try:
                if session_id not in self.active_sessions:
                    raise HTTPException(status_code=404, detail="Session not found")

                session = self.active_sessions[session_id]
                session.resume_session()

                return {
                    "success": True,
                    "session_id": session_id,
                    "status": session.status,
                    "message": f"Session {session_id} resumed successfully"
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error resuming session: {str(e)}")

        @self.app.options("/session/{session_id}/cancel")
        async def options_session_cancel(session_id: str):
            """OPTIONS handler for cancelling session."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/session/{session_id}/cancel")
        async def cancel_session(session_id: str, current_admin: dict = Depends(get_current_admin)):
            """Cancelar una sesión de entrenamiento federado."""
            try:
                if session_id not in self.active_sessions:
                    raise HTTPException(status_code=404, detail="Session not found")

                session = self.active_sessions[session_id]
                session.cancel_session()

                return {
                    "success": True,
                    "session_id": session_id,
                    "status": session.status,
                    "message": f"Session {session_id} cancelled successfully"
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error cancelling session: {str(e)}")

        @self.app.options("/session/{session_id}/config")
        async def options_session_config_update(session_id: str):
            """OPTIONS handler for updating session config."""
            return {"Allow": "PUT, OPTIONS"}

        @self.app.put("/session/{session_id}/config")
        async def update_session_config(session_id: str, config: SessionConfigUpdateRequest, current_admin: dict = Depends(get_current_admin)):
            """Actualizar la configuración de una sesión de entrenamiento federado."""
            try:
                if session_id not in self.active_sessions:
                    raise HTTPException(status_code=404, detail="Session not found")

                session = self.active_sessions[session_id]

                # Solo permitir actualizaciones si la sesión no ha empezado realmente
                if session.current_round > 0:
                    raise HTTPException(status_code=409, detail="Cannot update config: session already started training")

                # Actualizar campos permitidos
                updated_fields = []
                if config.rounds is not None:
                    session.total_rounds = config.rounds
                    updated_fields.append("rounds")
                if config.min_nodes is not None:
                    session.min_nodes = config.min_nodes
                    updated_fields.append("min_nodes")
                if config.max_nodes is not None:
                    session.max_nodes = config.max_nodes
                    updated_fields.append("max_nodes")
                if config.privacy_budget is not None:
                    session.privacy_budget = config.privacy_budget
                    updated_fields.append("privacy_budget")

                logger.info(f"⚙️ Updated session {session_id} config: {updated_fields}")

                return {
                    "success": True,
                    "session_id": session_id,
                    "updated_fields": updated_fields,
                    "current_config": {
                        "rounds": session.total_rounds,
                        "min_nodes": session.min_nodes,
                        "max_nodes": session.max_nodes,
                        "privacy_budget": session.privacy_budget
                    },
                    "message": f"Session {session_id} configuration updated successfully"
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error updating session config: {str(e)}")

        @self.app.get("/session/{session_id}/logs")
        async def get_session_logs(session_id: str, limit: int = 100, offset: int = 0):
            """Obtener logs e historial de una sesión de entrenamiento federado."""
            try:
                if session_id not in self.active_sessions:
                    raise HTTPException(status_code=404, detail="Session not found")

                session = self.active_sessions[session_id]

                logs = []
                trainer = self.session_trainers.get(session_id)
                round_history = trainer.get_round_history() if trainer else []

                # Log de creación
                logs.append({
                    "timestamp": session.created_at,
                    "level": "INFO",
                    "event": "session_created",
                    "message": f"Session {session_id} created with model {session.model_name}",
                    "details": {
                        "model_name": session.model_name,
                        "dataset_name": session.dataset_name,
                        "total_rounds": session.total_rounds,
                        "min_nodes": session.min_nodes,
                        "max_nodes": session.max_nodes
                    }
                })

                # Logs de participantes
                for participant in session.participants:
                    node_info = self.node_registrations.get(participant, {})
                    logs.append({
                        "timestamp": node_info.get("joined_at", session.created_at),
                        "level": "INFO",
                        "event": "participant_joined",
                        "message": f"Node {participant} joined session {session_id}",
                        "details": {
                            "node_id": participant,
                            "hardware_info": node_info.get("hardware_info", {}),
                            "local_data_info": node_info.get("local_data_info", {})
                        }
                    })

                # Logs de rondas (historial real del trainer)
                for entry in round_history:
                    if not entry.get("end_time"):
                        continue
                    start_ts = entry.get("start_time")
                    end_ts = entry.get("end_time")
                    logs.append({
                        "timestamp": datetime.fromtimestamp(end_ts).isoformat(),
                        "level": "INFO",
                        "event": "round_completed",
                        "message": f"Round {entry['round_num']} completed for session {session_id}",
                        "details": {
                            "round_num": entry["round_num"],
                            "session_id": session_id,
                            "start_time": datetime.fromtimestamp(start_ts).isoformat() if start_ts else None,
                            "end_time": datetime.fromtimestamp(end_ts).isoformat(),
                            "duration": entry.get("duration"),
                            "participants": entry.get("participants", []),
                            "model_cid": entry.get("model_cid"),
                            "global_accuracy": entry.get("global_accuracy"),
                            "global_loss": entry.get("global_loss")
                        }
                    })

                # Logs de estado actual
                if session.paused:
                    logs.append({
                        "timestamp": datetime.fromtimestamp(session.paused_at or time.time()).isoformat(),
                        "level": "WARNING",
                        "event": "session_paused",
                        "message": f"Session {session_id} paused at round {session.current_round}",
                        "details": {"current_round": session.current_round}
                    })
                elif session.is_complete():
                    logs.append({
                        "timestamp": datetime.fromtimestamp(session.end_time).isoformat() if session.end_time else datetime.now().isoformat(),
                        "level": "INFO",
                        "event": "session_completed",
                        "message": f"Session {session_id} completed after {session.current_round} rounds",
                        "details": {
                            "final_round": session.current_round,
                            "total_rewards": session.total_rewards_distributed
                        }
                    })

                # Aplicar paginación
                total_logs = len(logs)
                start_idx = max(0, total_logs - offset - limit)
                end_idx = max(0, total_logs - offset)
                paginated_logs = logs[start_idx:end_idx]

                return {
                    "session_id": session_id,
                    "logs": paginated_logs,
                    "total_logs": total_logs,
                    "returned_logs": len(paginated_logs),
                    "limit": limit,
                    "offset": offset,
                    "has_more": end_idx < total_logs
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error getting session logs: {str(e)}")

        # ===== NODE MANAGEMENT =====

        @self.app.options("/node/join")
        async def options_node_join():
            """OPTIONS handler for node joining session."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/node/join")
        async def join_session(request: NodeJoinRequest):
            """Unir un nodo REAL a una sesión de entrenamiento federado."""
            try:
                if request.session_id not in self.active_sessions:
                    raise HTTPException(status_code=404, detail="Session not found")

                session = self.active_sessions[request.session_id]
                trainer = self.session_trainers[request.session_id]

                logger.info(f"🔗 Node {request.node_id} joining session {request.session_id}")

                # Verificar límites REALES
                if len(session.participants) >= session.max_nodes:
                    raise HTTPException(status_code=409, detail="Session is full")

                # Añadir participante REAL
                session.add_participant(request.node_id)

                # Registrar nodo REAL con información completa
                self.node_registrations[request.node_id] = {
                    "session_id": request.session_id,
                    "node_id": request.node_id,
                    "hardware_info": request.hardware_info,
                    "local_data_info": request.local_data_info,
                    "joined_at": datetime.now().isoformat(),
                    "last_update": datetime.now().isoformat(),
                    "status": "active",
                    "contributions": 0,
                    "rewards_earned": 0.0
                }

                # Actualizar estadísticas
                self.system_stats["total_nodes_registered"] += 1

                # Obtener modelo inicial REAL desde trainer
                model_cid = trainer.get_initial_model_cid()

                logger.info(f"✅ Node {request.node_id} joined session {request.session_id}")

                # Broadcast node status update
                node_update_data = {
                    "node_id": request.node_id,
                    "action": "joined",
                    "session_id": request.session_id,
                    "status": "active",
                    "hardware_info": request.hardware_info,
                    "local_data_info": request.local_data_info,
                    "joined_at": self.node_registrations[request.node_id]["joined_at"]
                }
                await self._broadcast_node_status_update(node_update_data)

                # Broadcast registry update
                registry_data = await self._get_federated_node_registry()
                await self._broadcast_registry_update(registry_data)

                # Broadcast training participants update
                participants_data = await self._get_session_participants_data(request.session_id)
                await self._broadcast_training_participants_update(request.session_id, participants_data)

                # Broadcast training progress update
                progress_data = await self._get_session_training_progress(request.session_id)
                await self._broadcast_training_progress_update(request.session_id, progress_data)

                return {
                    "success": True,
                    "session_id": request.session_id,
                    "node_id": request.node_id,
                    "initial_model_cid": model_cid,
                    "current_round": session.current_round,
                    "total_rounds": session.total_rounds,
                    "message": "Node successfully joined federated session"
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"❌ Error joining session: {e}")
                raise HTTPException(status_code=500, detail=f"Error joining session: {str(e)}")

        @self.app.options("/node/leave")
        async def options_node_leave():
            """OPTIONS handler for node leaving session."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/node/leave")
        async def leave_session(session_id: str, node_id: str):
            """Remover un nodo de una sesión."""
            try:
                if session_id not in self.active_sessions:
                    raise HTTPException(status_code=404, detail="Session not found")

                session = self.active_sessions[session_id]
                session.remove_participant(node_id)

                if node_id in self.node_registrations:
                    del self.node_registrations[node_id]

                # Broadcast node status update
                node_update_data = {
                    "node_id": node_id,
                    "action": "left",
                    "session_id": session_id,
                    "status": "inactive"
                }
                await self._broadcast_node_status_update(node_update_data)

                # Broadcast registry update
                registry_data = await self._get_federated_node_registry()
                await self._broadcast_registry_update(registry_data)

                return {
                    "success": True,
                    "message": f"Node {node_id} left session {session_id}"
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error leaving session: {str(e)}")

        @self.app.get("/sessions/{session_id}/nodes")
        async def get_session_nodes(session_id: str):
            """Obtener nodos participantes en una sesión."""
            try:
                if session_id not in self.active_sessions:
                    raise HTTPException(status_code=404, detail="Session not found")

                session_nodes = [
                    info for info in self.node_registrations.values()
                    if info.get("session_id") == session_id
                ]

                return {
                    "session_id": session_id,
                    "nodes": session_nodes,
                    "total": len(session_nodes)
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error getting session nodes: {str(e)}")

        @self.app.get("/nodes/")
        async def get_nodes_basic():
            """Obtener información básica de nodos."""
            try:
                nodes = []
                for node_id, info in self.node_registrations.items():
                    nodes.append({
                        "node_id": node_id,
                        "status": info.get("status", "unknown"),
                        "session_id": info.get("session_id"),
                        "joined_at": info.get("joined_at")
                    })

                return {
                    "nodes": nodes,
                    "total": len(nodes)
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error getting nodes: {str(e)}")

        # ===== FEDERATED NODES REGISTRY ENDPOINTS =====

        @self.app.get("/nodes/registry")
        @cached(ttl=60, key_prefix="federated")
        async def get_federated_node_registry():
            """Obtener registro completo de nodos federados."""
            try:
                if not self.node_registry:
                    # Fallback: usar datos de sesiones activas
                    all_nodes = {}
                    for session_id, session in self.active_sessions.items():
                        for node_id, info in self.node_registrations.items():
                            if info.get("session_id") == session_id:
                                all_nodes[node_id] = {
                                    "node_id": node_id,
                                    "status": info.get("status", "unknown"),
                                    "last_seen": info.get("last_update"),
                                    "hardware_info": info.get("hardware_info", {}),
                                    "local_data_info": info.get("local_data_info", {}),
                                    "reputation_score": 1.0,  # Default
                                    "capabilities": ["federated_learning"],
                                    "registered_at": info.get("joined_at"),
                                    "location": "Unknown"
                                }

                    return {
                        "nodes": list(all_nodes.values()),
                        "total_nodes": len(all_nodes),
                        "active_nodes": len([n for n in all_nodes.values() if n["status"] == "active"]),
                        "timestamp": datetime.now().isoformat(),
                        "source": "session_fallback"
                    }

                # Usar NodeRegistry real
                nodes = await self.node_registry.discover_nodes()
                registry_stats = self.node_registry.get_stats()

                return {
                    "nodes": [
                        {
                            "node_id": node.metadata.node_id,
                            "status": node.metadata.status,
                            "last_seen": node.metadata.last_seen.isoformat() if node.metadata.last_seen else None,
                            "hardware_capacity": node.metadata.hardware_capacity,
                            "reputation_score": node.metadata.reputation_score,
                            "capabilities": node.metadata.capabilities,
                            "location": node.metadata.location,
                            "registered_at": node.metadata.registered_at.isoformat(),
                            "certificate_valid": True  # Validado por registry
                        }
                        for node in nodes
                    ],
                    "total_nodes": registry_stats.get("known_nodes", 0),
                    "active_nodes": registry_stats.get("active_nodes", 0),
                    "cached_nodes": registry_stats.get("cached_nodes", 0),
                    "registry_cid": registry_stats.get("registry_cid"),
                    "timestamp": datetime.now().isoformat(),
                    "source": "node_registry"
                }
            except Exception as e:
                logger.error(f"Error getting federated node registry: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving node registry: {str(e)}")

        @self.app.get("/nodes/registry/{node_id}")
        async def get_federated_node_details(node_id: str):
            """Obtener detalles específicos de un nodo federado."""
            try:
                if not self.node_registry:
                    # Fallback: buscar en registros de sesión
                    for info in self.node_registrations.values():
                        if info.get("node_id") == node_id:
                            return {
                                "node_id": node_id,
                                "status": info.get("status", "unknown"),
                                "last_seen": info.get("last_update"),
                                "hardware_info": info.get("hardware_info", {}),
                                "local_data_info": info.get("local_data_info", {}),
                                "reputation_score": 1.0,
                                "capabilities": ["federated_learning"],
                                "registered_at": info.get("joined_at"),
                                "location": "Unknown",
                                "contributions": info.get("contributions", 0),
                                "rewards_earned": info.get("rewards_earned", 0.0),
                                "source": "session_fallback"
                            }
                    raise HTTPException(status_code=404, detail="Node not found")

                # Usar NodeRegistry real
                nodes = await self.node_registry.discover_nodes({"node_id": node_id})
                if not nodes:
                    raise HTTPException(status_code=404, detail="Node not found")

                node = nodes[0]
                return {
                    "node_id": node.metadata.node_id,
                    "status": node.metadata.status,
                    "last_seen": node.metadata.last_seen.isoformat() if node.metadata.last_seen else None,
                    "hardware_capacity": node.metadata.hardware_capacity,
                    "reputation_score": node.metadata.reputation_score,
                    "capabilities": node.metadata.capabilities,
                    "location": node.metadata.location,
                    "registered_at": node.metadata.registered_at.isoformat(),
                    "certificate_pem": node.certificate_pem,
                    "public_key_pem": node.public_key_pem,
                    "timestamp": node.timestamp.isoformat(),
                    "source": "node_registry"
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting federated node details: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving node details: {str(e)}")

        # ===== WEBSOCKET ENDPOINTS FOR REAL-TIME UPDATES =====

        @self.app.websocket("/ws/federated/nodes")
        async def federated_nodes_websocket(websocket: WebSocket):
            """WebSocket para actualizaciones en tiempo real de nodos federados."""
            await websocket.accept()
            logger.info("Federated nodes WebSocket connection established")

            try:
                # Enviar datos iniciales
                initial_status = await self._get_realtime_node_status()
                await websocket.send_json({
                    "type": "initial_status",
                    "data": initial_status
                })

                while True:
                    # Mantener conexión viva y esperar desconexión
                    try:
                        await websocket.receive_text()
                    except WebSocketDisconnect:
                        break

            except Exception as e:
                logger.error(f"Federated nodes WebSocket error: {e}")
            finally:
                logger.info("Federated nodes WebSocket connection closed")

        @self.app.websocket("/ws/federated/registry")
        async def federated_registry_websocket(websocket: WebSocket):
            """WebSocket para actualizaciones en tiempo real del registro de nodos."""
            await websocket.accept()
            logger.info("Federated registry WebSocket connection established")

            try:
                # Enviar datos iniciales del registro
                initial_registry = await self._get_federated_node_registry()
                await websocket.send_json({
                    "type": "initial_registry",
                    "data": initial_registry
                })

                while True:
                    # Mantener conexión viva y esperar desconexión
                    try:
                        await websocket.receive_text()
                    except WebSocketDisconnect:
                        break

            except Exception as e:
                logger.error(f"Federated registry WebSocket error: {e}")
            finally:
                logger.info("Federated registry WebSocket connection closed")

        @self.app.websocket("/ws/federated/health")
        async def federated_health_websocket(websocket: WebSocket):
            """WebSocket para actualizaciones en tiempo real de la salud de la red."""
            await websocket.accept()
            logger.info("Federated health WebSocket connection established")

            try:
                # Enviar datos iniciales de salud
                initial_health = await self._get_network_health_status()
                await websocket.send_json({
                    "type": "initial_health",
                    "data": initial_health
                })

                while True:
                    # Mantener conexión viva y esperar desconexión
                    try:
                        await websocket.receive_text()
                    except WebSocketDisconnect:
                        break

            except Exception as e:
                logger.error(f"Federated health WebSocket error: {e}")
            finally:
                logger.info("Federated health WebSocket connection closed")

        # ===== TRAINING PROGRESS WEBSOCKET ENDPOINTS =====

        @self.app.websocket("/ws/federated/training/{session_id}")
        async def training_progress_websocket(websocket: WebSocket, session_id: str):
            """WebSocket para actualizaciones en tiempo real del progreso de entrenamiento."""
            await websocket.accept()
            logger.info(f"Training progress WebSocket connection established for session {session_id}")

            try:
                # Verificar que la sesión existe
                if session_id not in self.active_sessions:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Session {session_id} not found"
                    })
                    await websocket.close(code=1008)
                    return

                # Enviar datos iniciales de progreso
                initial_progress = await self._get_session_training_progress(session_id)
                await websocket.send_json({
                    "type": "initial_progress",
                    "data": initial_progress
                })

                while True:
                    # Mantener conexión viva y esperar desconexión
                    try:
                        await websocket.receive_text()
                    except WebSocketDisconnect:
                        break

            except Exception as e:
                logger.error(f"Training progress WebSocket error for session {session_id}: {e}")
            finally:
                logger.info(f"Training progress WebSocket connection closed for session {session_id}")

        @self.app.websocket("/ws/federated/training/{session_id}/participants")
        async def training_participants_websocket(websocket: WebSocket, session_id: str):
            """WebSocket para actualizaciones en tiempo real de participantes."""
            await websocket.accept()
            logger.info(f"Training participants WebSocket connection established for session {session_id}")

            try:
                # Verificar que la sesión existe
                if session_id not in self.active_sessions:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Session {session_id} not found"
                    })
                    await websocket.close(code=1008)
                    return

                # Enviar datos iniciales de participantes
                initial_participants = await self._get_session_participants_data(session_id)
                await websocket.send_json({
                    "type": "initial_participants",
                    "data": initial_participants
                })

                while True:
                    # Mantener conexión viva y esperar desconexión
                    try:
                        await websocket.receive_text()
                    except WebSocketDisconnect:
                        break

            except Exception as e:
                logger.error(f"Training participants WebSocket error for session {session_id}: {e}")
            finally:
                logger.info(f"Training participants WebSocket connection closed for session {session_id}")

        @self.app.websocket("/ws/federated/training/{session_id}/metrics")
        async def training_metrics_websocket(websocket: WebSocket, session_id: str):
            """WebSocket para actualizaciones en tiempo real de métricas de entrenamiento."""
            await websocket.accept()
            logger.info(f"Training metrics WebSocket connection established for session {session_id}")

            try:
                # Verificar que la sesión existe
                if session_id not in self.active_sessions:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Session {session_id} not found"
                    })
                    await websocket.close(code=1008)
                    return

                # Enviar datos iniciales de métricas
                initial_metrics = await self._get_session_training_metrics(session_id)
                await websocket.send_json({
                    "type": "initial_metrics",
                    "data": initial_metrics
                })

                while True:
                    # Mantener conexión viva y esperar desconexión
                    try:
                        await websocket.receive_text()
                    except WebSocketDisconnect:
                        break

            except Exception as e:
                logger.error(f"Training metrics WebSocket error for session {session_id}: {e}")
            finally:
                logger.info(f"Training metrics WebSocket connection closed for session {session_id}")

        # ===== REAL-TIME NODE STATUS ENDPOINTS =====

        @self.app.get("/nodes/status")
        async def get_realtime_node_status():
            """Obtener estado en tiempo real de todos los nodos federados."""
            try:
                node_statuses = {}

                # Obtener datos de health monitor si disponible
                if self.health_monitor:
                    health_metrics = self.health_monitor.get_all_health_metrics()
                    for node_id, metrics in health_metrics.items():
                        node_statuses[node_id] = {
                            "node_id": node_id,
                            "health_status": metrics.overall_health.value,
                            "connectivity_score": metrics.connectivity_score,
                            "performance_score": metrics.performance_score,
                            "contribution_score": metrics.contribution_score,
                            "stability_score": metrics.stability_score,
                            "last_health_check": metrics.last_health_check.isoformat() if metrics.last_health_check else None,
                            "last_seen": metrics.last_seen.isoformat() if metrics.last_seen else None,
                            "response_time_ms": metrics.response_time_ms,
                            "cpu_usage_percent": metrics.cpu_usage_percent,
                            "memory_usage_percent": metrics.memory_usage_percent,
                            "network_latency_ms": metrics.network_latency_ms,
                            "consecutive_failures": metrics.consecutive_failures,
                            "total_contributions": metrics.total_contributions,
                            "successful_contributions": metrics.successful_contributions,
                            "session_success_rate": metrics.session_success_rate,
                            "source": "health_monitor"
                        }

                # Complementar con datos de sesiones activas
                for node_id, info in self.node_registrations.items():
                    if node_id not in node_statuses:
                        node_statuses[node_id] = {
                            "node_id": node_id,
                            "health_status": "unknown",
                            "connectivity_score": 0.0,
                            "performance_score": 0.5,
                            "contribution_score": 0.5,
                            "stability_score": 1.0,
                            "last_health_check": info.get("last_update"),
                            "last_seen": info.get("last_update"),
                            "response_time_ms": None,
                            "cpu_usage_percent": None,
                            "memory_usage_percent": None,
                            "network_latency_ms": None,
                            "consecutive_failures": 0,
                            "total_contributions": info.get("contributions", 0),
                            "successful_contributions": info.get("contributions", 0),
                            "session_success_rate": 1.0 if info.get("contributions", 0) > 0 else 0.0,
                            "source": "session_data"
                        }
                    else:
                        # Actualizar con datos de sesión si son más recientes
                        session_update = info.get("last_update")
                        if session_update and (not node_statuses[node_id].get("last_seen") or
                                              session_update > node_statuses[node_id]["last_seen"]):
                            node_statuses[node_id]["last_seen"] = session_update
                            node_statuses[node_id]["total_contributions"] = info.get("contributions", 0)

                return {
                    "node_statuses": list(node_statuses.values()),
                    "total_nodes": len(node_statuses),
                    "healthy_nodes": len([n for n in node_statuses.values() if n["health_status"] == "healthy"]),
                    "degraded_nodes": len([n for n in node_statuses.values() if n["health_status"] == "degraded"]),
                    "unhealthy_nodes": len([n for n in node_statuses.values() if n["health_status"] in ["unhealthy", "critical"]]),
                    "timestamp": datetime.now().isoformat(),
                    "monitoring_active": self.health_monitor is not None
                }
            except Exception as e:
                logger.error(f"Error getting realtime node status: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving node status: {str(e)}")

        # ===== PERFORMANCE METRICS ENDPOINTS =====

        @self.app.get("/nodes/metrics")
        async def get_federated_node_metrics(request: Request = None):
            """Obtener métricas de rendimiento de nodos federados con TOON/VSC optimización."""
            try:
                metrics_data = {}

                # Obtener métricas del health monitor
                if self.health_monitor:
                    health_metrics = self.health_monitor.get_all_health_metrics()
                    for node_id, metrics in health_metrics.items():
                        metrics_data[node_id] = {
                            "node_id": node_id,
                            "timestamp": datetime.now().isoformat(),
                            "performance": {
                                "cpu_usage_percent": metrics.cpu_usage_percent,
                                "memory_usage_percent": metrics.memory_usage_percent,
                                "network_latency_ms": metrics.network_latency_ms,
                                "performance_score": metrics.performance_score,
                                "response_times_history": metrics.response_times_history[-10:],  # Últimas 10
                                "performance_history": metrics.performance_history[-10:]  # Últimas 10
                            },
                            "contributions": {
                                "total_contributions": metrics.total_contributions,
                                "successful_contributions": metrics.successful_contributions,
                                "session_success_rate": metrics.session_success_rate,
                                "contribution_score": metrics.contribution_score,
                                "average_contribution_time": metrics.average_contribution_time
                            },
                            "stability": {
                                "stability_score": metrics.stability_score,
                                "error_rate": metrics.error_rate,
                                "consecutive_failures": metrics.consecutive_failures,
                                "crash_count": metrics.crash_count
                            },
                            "connectivity": {
                                "connectivity_score": metrics.connectivity_score,
                                "uptime_ratio": metrics.uptime_ratio,
                                "last_seen": metrics.last_seen.isoformat() if metrics.last_seen else None,
                                "response_time_ms": metrics.response_time_ms
                            },
                            "source": "health_monitor"
                        }

                # Obtener métricas del realtime monitor
                if self.realtime_monitor:
                    system_status = self.realtime_monitor.get_system_status()
                    current_metrics = system_status.get("current_metrics", {})

                    # Agregar métricas del sistema local como nodo especial
                    metrics_data["local_system"] = {
                        "node_id": "local_system",
                        "timestamp": datetime.now().isoformat(),
                        "performance": {
                            "cpu_usage_percent": current_metrics.get("cpu_usage", {}).get("value"),
                            "memory_usage_percent": current_metrics.get("memory_usage", {}).get("value"),
                            "network_latency_ms": None,
                            "performance_score": None,
                            "response_times_history": [],
                            "performance_history": []
                        },
                        "contributions": {
                            "total_contributions": 0,
                            "successful_contributions": 0,
                            "session_success_rate": 0.0,
                            "contribution_score": 0.0,
                            "average_contribution_time": None
                        },
                        "stability": {
                            "stability_score": 1.0,
                            "error_rate": 0.0,
                            "consecutive_failures": 0,
                            "crash_count": 0
                        },
                        "connectivity": {
                            "connectivity_score": 1.0,
                            "uptime_ratio": 1.0,
                            "last_seen": datetime.now().isoformat(),
                            "response_time_ms": 0
                        },
                        "source": "realtime_monitor"
                    }

                # Complementar con datos básicos de sesiones
                for node_id, info in self.node_registrations.items():
                    if node_id not in metrics_data:
                        metrics_data[node_id] = {
                            "node_id": node_id,
                            "timestamp": datetime.now().isoformat(),
                            "performance": {
                                "cpu_usage_percent": None,
                                "memory_usage_percent": None,
                                "network_latency_ms": None,
                                "performance_score": 0.8,
                                "response_times_history": [],
                                "performance_history": []
                            },
                            "contributions": {
                                "total_contributions": info.get("contributions", 0),
                                "successful_contributions": info.get("contributions", 0),
                                "session_success_rate": 1.0,
                                "contribution_score": 0.9,
                                "average_contribution_time": None
                            },
                            "stability": {
                                "stability_score": 0.95,
                                "error_rate": 0.0,
                                "consecutive_failures": 0,
                                "crash_count": 0
                            },
                            "connectivity": {
                                "connectivity_score": 1.0 if info.get("status") == "active" else 0.0,
                                "uptime_ratio": 0.99,
                                "last_seen": info.get("last_update"),
                                "response_time_ms": None
                            },
                            "source": "session_fallback"
                        }

                response_data = {
                    "node_metrics": list(metrics_data.values()),
                    "total_nodes": len(metrics_data),
                    "timestamp": datetime.now().isoformat(),
                    "monitors_active": {
                        "health_monitor": self.health_monitor is not None,
                        "realtime_monitor": self.realtime_monitor is not None
                    }
                }

                # Usar VSC para arrays de métricas repetitivas y TOON para valores numéricos
                return self.serialization_middleware.optimize_response(
                    response_data,
                    request,
                    self.toon_serializer,
                    self.vsc_serializer,
                    self.json_serializer
                )

            except Exception as e:
                logger.error(f"Error getting federated node metrics: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving node metrics: {str(e)}")

        # ===== NETWORK HEALTH MONITORING ENDPOINTS =====

        @self.app.get("/network/health")
        async def get_network_health_status():
            """Obtener estado de salud de la red federada."""
            try:
                network_health = {
                    "timestamp": datetime.now().isoformat(),
                    "network_status": "unknown",
                    "connectivity_score": 0.0,
                    "performance_score": 0.0,
                    "stability_score": 0.0,
                    "active_nodes": 0,
                    "total_nodes": 0,
                    "network_efficiency": 0.0,
                    "average_latency_ms": None,
                    "packet_loss_rate": 0.0,
                    "bandwidth_utilization": 0.0,
                    "alerts": [],
                    "recommendations": []
                }

                # Obtener datos del health monitor
                if self.health_monitor:
                    summary = self.health_monitor.get_system_health_summary()
                    optimization = self.health_monitor.get_optimization_metrics()

                    network_health.update({
                        "network_status": summary.get("status", "unknown"),
                        "connectivity_score": summary.get("average_connectivity", 0.0),
                        "performance_score": summary.get("average_performance", 0.0),
                        "stability_score": 1.0,  # Placeholder
                        "active_nodes": summary.get("healthy_nodes", 0) + summary.get("degraded_nodes", 0),
                        "total_nodes": summary.get("total_nodes", 0),
                        "network_efficiency": (summary.get("healthy_nodes", 0) / max(summary.get("total_nodes", 1), 1)) * 100,
                        "alerts": [alert.to_dict() for alert in self.health_monitor.get_active_alerts()],
                        "recommendations": optimization.get("recommended_actions", [])
                    })

                    # Calcular latencia promedio
                    all_metrics = self.health_monitor.get_all_health_metrics()
                    latencies = [m.network_latency_ms for m in all_metrics.values() if m.network_latency_ms is not None]
                    if latencies:
                        network_health["average_latency_ms"] = statistics.mean(latencies)

                # Complementar con datos de sesiones
                session_nodes = len(self.node_registrations)
                active_session_nodes = len([n for n in self.node_registrations.values() if n.get("status") == "active"])

                if not self.health_monitor:
                    network_health.update({
                        "network_status": "active" if active_session_nodes > 0 else "idle",
                        "connectivity_score": 0.9 if active_session_nodes > 0 else 0.1,
                        "performance_score": 0.8,
                        "stability_score": 0.95,
                        "active_nodes": active_session_nodes,
                        "total_nodes": session_nodes,
                        "network_efficiency": (active_session_nodes / max(session_nodes, 1)) * 100,
                        "source": "session_fallback"
                    })

                # Obtener métricas de red del realtime monitor
                if self.realtime_monitor:
                    system_status = self.realtime_monitor.get_system_status()
                    current_metrics = system_status.get("current_metrics", {})

                    network_metrics = current_metrics.get("network_io", {})
                    if network_metrics:
                        network_health["bandwidth_utilization"] = network_metrics.get("bytes_sent", 0) + network_metrics.get("bytes_recv", 0)

                return network_health

            except Exception as e:
                logger.error(f"Error getting network health status: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving network health: {str(e)}")

        @self.app.get("/network/topology")
        async def get_network_topology():
            """Obtener topología de la red federada."""
            try:
                topology = {
                    "timestamp": datetime.now().isoformat(),
                    "nodes": [],
                    "connections": [],
                    "regions": {},
                    "network_stats": {}
                }

                # Obtener nodos del registry
                if self.node_registry:
                    nodes = await self.node_registry.discover_nodes()
                    topology["nodes"] = [
                        {
                            "id": node.metadata.node_id,
                            "status": node.metadata.status,
                            "location": node.metadata.location,
                            "capabilities": node.metadata.capabilities,
                            "reputation_score": node.metadata.reputation_score,
                            "last_seen": node.metadata.last_seen.isoformat() if node.metadata.last_seen else None
                        }
                        for node in nodes
                    ]

                    # Agrupar por región
                    regions = {}
                    for node in nodes:
                        location = node.metadata.location or "Unknown"
                        if location not in regions:
                            regions[location] = []
                        regions[location].append(node.metadata.node_id)
                    topology["regions"] = regions

                else:
                    # Fallback: usar datos de sesiones
                    topology["nodes"] = [
                        {
                            "id": info["node_id"],
                            "status": info.get("status", "unknown"),
                            "location": "Unknown",
                            "capabilities": ["federated_learning"],
                            "reputation_score": 1.0,
                            "last_seen": info.get("last_update")
                        }
                        for info in self.node_registrations.values()
                    ]

                # Calcular estadísticas de red
                total_nodes = len(topology["nodes"])
                active_nodes = len([n for n in topology["nodes"] if n["status"] == "active"])

                topology["network_stats"] = {
                    "total_nodes": total_nodes,
                    "active_nodes": active_nodes,
                    "inactive_nodes": total_nodes - active_nodes,
                    "regions_count": len(topology["regions"]),
                    "average_reputation": statistics.mean([n["reputation_score"] for n in topology["nodes"]]) if topology["nodes"] else 0.0,
                    "network_density": (active_nodes / max(total_nodes, 1)) * 100
                }

                # Simular conexiones (en implementación real vendrían del P2P network)
                topology["connections"] = []
                if self.node_communicator:
                    connected_peers = self.node_communicator.get_connected_peers()
                    for peer_id in connected_peers:
                        topology["connections"].append({
                            "source": self.node_communicator.node_id,
                            "target": peer_id,
                            "status": "active",
                            "latency_ms": None
                        })

                return topology

            except Exception as e:
                logger.error(f"Error getting network topology: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving network topology: {str(e)}")

        @self.app.get("/network/alerts")
        async def get_network_alerts():
            """Obtener alertas de red federada."""
            try:
                alerts = []

                # Obtener alertas del health monitor
                if self.health_monitor:
                    alerts.extend([alert.to_dict() for alert in self.health_monitor.get_active_alerts()])

                # Agregar alertas derivadas si no hay health monitor (solo si se permite)
                if not self.health_monitor and self.allow_mocks:
                    # Verificar nodos inactivos
                    inactive_nodes = [info for info in self.node_registrations.values() if info.get("status") != "active"]
                    if inactive_nodes:
                        alerts.append({
                            "alert_id": "network_inactive_nodes",
                            "severity": "warning",
                            "title": "Inactive Nodes Detected",
                            "message": f"{len(inactive_nodes)} nodes are currently inactive",
                            "timestamp": datetime.now().isoformat(),
                            "resolved": False,
                            "metadata": {"inactive_count": len(inactive_nodes)}
                        })

                    # Verificar conectividad baja
                    active_nodes = len([n for n in self.node_registrations.values() if n.get("status") == "active"])
                    total_nodes = len(self.node_registrations)
                    if total_nodes > 0 and (active_nodes / total_nodes) < 0.5:
                        alerts.append({
                            "alert_id": "network_low_connectivity",
                            "severity": "error",
                            "title": "Low Network Connectivity",
                            "message": f"Only {active_nodes}/{total_nodes} nodes are active",
                            "timestamp": datetime.now().isoformat(),
                            "resolved": False,
                            "metadata": {"active_nodes": active_nodes, "total_nodes": total_nodes}
                        })

                if not self.health_monitor and not self.allow_mocks:
                    return {
                        "alerts": [],
                        "total_alerts": 0,
                        "critical_alerts": 0,
                        "warning_alerts": 0,
                        "error_alerts": 0,
                        "timestamp": datetime.now().isoformat(),
                        "note": "health_monitor_unavailable"
                    }

                return {
                    "alerts": alerts,
                    "total_alerts": len(alerts),
                    "critical_alerts": len([a for a in alerts if a.get("severity") == "critical"]),
                    "warning_alerts": len([a for a in alerts if a.get("severity") == "warning"]),
                    "error_alerts": len([a for a in alerts if a.get("severity") == "error"]),
                    "timestamp": datetime.now().isoformat()
                }

            except Exception as e:
                logger.error(f"Error getting network alerts: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving network alerts: {str(e)}")

        @self.app.get("/nodes/metrics/{node_id}")
        async def get_node_performance_metrics(node_id: str):
            """Obtener métricas de rendimiento de un nodo específico."""
            try:
                # Buscar en health monitor
                if self.health_monitor:
                    metrics = self.health_monitor.get_node_health(node_id)
                    if metrics:
                        return {
                            "node_id": node_id,
                            "timestamp": datetime.now().isoformat(),
                            "performance": {
                                "cpu_usage_percent": metrics.cpu_usage_percent,
                                "memory_usage_percent": metrics.memory_usage_percent,
                                "network_latency_ms": metrics.network_latency_ms,
                                "performance_score": metrics.performance_score,
                                "response_times_history": metrics.response_times_history[-20:],  # Últimas 20
                                "performance_history": metrics.performance_history[-20:]  # Últimas 20
                            },
                            "contributions": {
                                "total_contributions": metrics.total_contributions,
                                "successful_contributions": metrics.successful_contributions,
                                "session_success_rate": metrics.session_success_rate,
                                "contribution_score": metrics.contribution_score,
                                "average_contribution_time": metrics.average_contribution_time
                            },
                            "stability": {
                                "stability_score": metrics.stability_score,
                                "error_rate": metrics.error_rate,
                                "consecutive_failures": metrics.consecutive_failures,
                                "crash_count": metrics.crash_count
                            },
                            "connectivity": {
                                "connectivity_score": metrics.connectivity_score,
                                "uptime_ratio": metrics.uptime_ratio,
                                "last_seen": metrics.last_seen.isoformat() if metrics.last_seen else None,
                                "response_time_ms": metrics.response_time_ms
                            },
                            "source": "health_monitor"
                        }

                # Fallback: buscar en registros de sesión
                for info in self.node_registrations.values():
                    if info.get("node_id") == node_id:
                        return {
                            "node_id": node_id,
                            "timestamp": datetime.now().isoformat(),
                            "performance": {
                                "cpu_usage_percent": None,
                                "memory_usage_percent": None,
                                "network_latency_ms": None,
                                "performance_score": 0.8,
                                "response_times_history": [],
                                "performance_history": []
                            },
                            "contributions": {
                                "total_contributions": info.get("contributions", 0),
                                "successful_contributions": info.get("contributions", 0),
                                "session_success_rate": 1.0,
                                "contribution_score": 0.9,
                                "average_contribution_time": None
                            },
                            "stability": {
                                "stability_score": 0.95,
                                "error_rate": 0.0,
                                "consecutive_failures": 0,
                                "crash_count": 0
                            },
                            "connectivity": {
                                "connectivity_score": 1.0 if info.get("status") == "active" else 0.0,
                                "uptime_ratio": 0.99,
                                "last_seen": info.get("last_update"),
                                "response_time_ms": None
                            },
                            "source": "session_fallback"
                        }

                raise HTTPException(status_code=404, detail="Node not found")
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting node performance metrics: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving node metrics: {str(e)}")

        @self.app.get("/nodes/status/{node_id}")
        async def get_node_realtime_status(node_id: str):
            """Obtener estado en tiempo real de un nodo específico."""
            try:
                # Buscar en health monitor
                if self.health_monitor:
                    metrics = self.health_monitor.get_node_health(node_id)
                    if metrics:
                        return {
                            "node_id": node_id,
                            "health_status": metrics.overall_health.value,
                            "connectivity_score": metrics.connectivity_score,
                            "performance_score": metrics.performance_score,
                            "contribution_score": metrics.contribution_score,
                            "stability_score": metrics.stability_score,
                            "last_health_check": metrics.last_health_check.isoformat() if metrics.last_health_check else None,
                            "last_seen": metrics.last_seen.isoformat() if metrics.last_seen else None,
                            "response_time_ms": metrics.response_time_ms,
                            "cpu_usage_percent": metrics.cpu_usage_percent,
                            "memory_usage_percent": metrics.memory_usage_percent,
                            "network_latency_ms": metrics.network_latency_ms,
                            "consecutive_failures": metrics.consecutive_failures,
                            "total_contributions": metrics.total_contributions,
                            "successful_contributions": metrics.successful_contributions,
                            "session_success_rate": metrics.session_success_rate,
                            "error_rate": metrics.error_rate,
                            "uptime_ratio": metrics.uptime_ratio,
                            "average_contribution_time": metrics.average_contribution_time,
                            "timestamp": datetime.now().isoformat(),
                            "source": "health_monitor"
                        }

                # Fallback: buscar en registros de sesión
                for info in self.node_registrations.values():
                    if info.get("node_id") == node_id:
                        return {
                            "node_id": node_id,
                            "health_status": "active" if info.get("status") == "active" else "unknown",
                            "connectivity_score": 1.0 if info.get("status") == "active" else 0.0,
                            "performance_score": 0.8,
                            "contribution_score": 0.9,
                            "stability_score": 0.95,
                            "last_health_check": info.get("last_update"),
                            "last_seen": info.get("last_update"),
                            "response_time_ms": None,
                            "cpu_usage_percent": None,
                            "memory_usage_percent": None,
                            "network_latency_ms": None,
                            "consecutive_failures": 0,
                            "total_contributions": info.get("contributions", 0),
                            "successful_contributions": info.get("contributions", 0),
                            "session_success_rate": 1.0,
                            "error_rate": 0.0,
                            "uptime_ratio": 0.99,
                            "average_contribution_time": None,
                            "timestamp": datetime.now().isoformat(),
                            "source": "session_fallback"
                        }

                raise HTTPException(status_code=404, detail="Node not found")
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting node realtime status: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving node status: {str(e)}")

        # ===== TRAINING COORDINATION =====

        @self.app.options("/training/update")
        async def options_training_update():
            """OPTIONS handler for training weight update."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.options("/training/update")
        async def options_training_update():
            """OPTIONS handler for training weight update."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/training/update")
        async def submit_weight_update(request: WeightUpdateRequest, background_tasks: BackgroundTasks):
            """Enviar actualización REAL de pesos desde un nodo federado."""
            try:
                if request.session_id not in self.active_sessions:
                    raise HTTPException(status_code=404, detail="Session not found")

                session = self.active_sessions[request.session_id]
                aggregator = self.session_aggregators[request.session_id]
                trainer = self.session_trainers[request.session_id]

                logger.info(f"📦 Weight update from node {request.node_id} for session {request.session_id}")

                # Verificar que el nodo está registrado REAL
                if request.node_id not in self.node_registrations:
                    raise HTTPException(status_code=403, detail="Node not registered")

                # Verificar ronda correcta REAL
                if request.round_num != session.current_round:
                    raise HTTPException(status_code=409, detail=f"Wrong round: expected {session.current_round}, got {request.round_num}")

                # Descargar pesos REALES desde IPFS
                weights_data = await self.ipfs_manager.get_data(request.ipfs_cid)
                weights = json.loads(weights_data.decode('utf-8'))

                # Agregar actualización REAL al aggregator FedAvg
                aggregator.add_weight_update(
                    node_id=request.node_id,
                    weights=weights,
                    num_samples=request.num_samples,
                    metrics=request.metrics
                )

                # Actualizar info REAL del nodo
                self.node_registrations[request.node_id]["last_update"] = datetime.now().isoformat()
                self.node_registrations[request.node_id]["contributions"] += 1

                # Actualizar estadísticas del sistema
                self.system_stats["total_data_processed"] += request.num_samples

                # Broadcast node activity update
                node_update_data = {
                    "node_id": request.node_id,
                    "action": "contribution",
                    "session_id": request.session_id,
                    "round_num": request.round_num,
                    "contributions": self.node_registrations[request.node_id]["contributions"],
                    "last_update": self.node_registrations[request.node_id]["last_update"]
                }
                await self._broadcast_node_status_update(node_update_data)

                # Broadcast training progress update
                progress_data = await self._get_session_training_progress(request.session_id)
                await self._broadcast_training_progress_update(request.session_id, progress_data)

                # Broadcast training participants update
                participants_data = await self._get_session_participants_data(request.session_id)
                await self._broadcast_training_participants_update(request.session_id, participants_data)

                # Broadcast training metrics update
                metrics_data = await self._get_session_training_metrics(request.session_id)
                await self._broadcast_training_metrics_update(request.session_id, metrics_data)

                logger.info(f"✅ Weight update processed from {request.node_id}")

                # Verificar si podemos avanzar de ronda REAL
                if aggregator.can_aggregate():
                    logger.info(f"🎯 Ready to aggregate round {session.current_round} for session {request.session_id}")
                    background_tasks.add_task(self._advance_round, request.session_id)

                return {
                    "success": True,
                    "session_id": request.session_id,
                    "round_num": request.round_num,
                    "updates_received": len(aggregator.weight_updates),
                    "required_updates": len(session.participants),
                    "can_aggregate": aggregator.can_aggregate(),
                    "message": "Weight update processed successfully"
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"❌ Error submitting weights: {e}")
                raise HTTPException(status_code=500, detail=f"Error submitting weights: {str(e)}")

        async def _advance_round(self, session_id: str):
            """Avanzar REALMENTE a la siguiente ronda de entrenamiento federado."""
            try:
                session = self.active_sessions[session_id]
                aggregator = self.session_aggregators[session_id]
                trainer = self.session_trainers[session_id]

                logger.info(f"🔄 Advancing round for session {session_id}")

                # Agregar pesos REALES con algoritmo FedAvg
                global_weights = aggregator.aggregate_weights()

                # Publicar nuevos pesos REALES en IPFS
                weights_json = json.dumps(global_weights, default=str)
                new_cid = await self.ipfs_manager.publish_data(weights_json.encode('utf-8'))

                # Actualizar trainer REAL con nuevos pesos
                trainer.update_global_model(global_weights, new_cid)

                # Avanzar ronda REAL
                session.next_round()

                # Resetear aggregator REAL para nueva ronda
                aggregator.reset_for_next_round()

                # Actualizar estadísticas del sistema
                self.system_stats["total_rounds_completed"] += 1

                # Broadcast training progress update after round advancement
                progress_data = await self._get_session_training_progress(session_id)
                await self._broadcast_training_progress_update(session_id, progress_data)

                # Broadcast training metrics update
                metrics_data = await self._get_session_training_metrics(session_id)
                await self._broadcast_training_metrics_update(session_id, metrics_data)

                logger.info(f"✅ Session {session_id} advanced to round {session.current_round} with CID: {new_cid}")

            except Exception as e:
                logger.error(f"❌ Error advancing round for session {session_id}: {e}")

        @self.app.get("/training/model/{session_id}")
        async def get_current_model(session_id: str):
            """Obtener el modelo global actual para una sesión."""
            try:
                if session_id not in self.session_trainers:
                    raise HTTPException(status_code=404, detail="Session trainer not found")

                trainer = self.session_trainers[session_id]
                model_info = trainer.get_current_model_info()

                return model_info
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error getting model: {str(e)}")

        # ===== STATISTICS AND MONITORING =====

        @self.app.get("/stats")
        @cached(ttl=30, key_prefix="federated")
        async def get_federated_stats():
            """Obtener estadísticas REALES globales del sistema federado."""
            try:
                total_sessions = len(self.active_sessions)
                total_nodes = len(self.node_registrations)
                active_nodes = len([
                    node for node in self.node_registrations.values()
                    if node["status"] == "active"
                ])

                # Calcular métricas REALES agregadas
                total_rounds_completed = sum(
                    session.current_round for session in self.active_sessions.values()
                )

                total_parameters_trained = sum(
                    trainer.total_parameters_trained
                    for trainer in self.session_trainers.values()
                )

                # Calcular uptime del sistema
                uptime_seconds = time.time() - self.system_stats["start_time"]
                uptime_hours = uptime_seconds / 3600

                # Calcular eficiencia de la red
                network_efficiency = (active_nodes / max(total_nodes, 1)) * 100

                return {
                    "total_sessions": total_sessions,
                    "total_nodes": total_nodes,
                    "active_nodes": active_nodes,
                    "total_rounds_completed": total_rounds_completed,
                    "total_parameters_trained": total_parameters_trained,
                    "total_data_processed": self.system_stats["total_data_processed"],
                    "network_status": "active" if active_nodes > 0 else "idle",
                    "network_efficiency": f"{network_efficiency:.1f}%",
                    "system_uptime_hours": f"{uptime_hours:.1f}",
                    "sessions_created": self.system_stats["total_sessions_created"],
                    "nodes_registered": self.system_stats["total_nodes_registered"],
                    "timestamp": datetime.now().isoformat(),
                    "federated_system_health": "healthy" if active_nodes > 0 else "idle"
                }
            except Exception as e:
                logger.error(f"❌ Error getting federated stats: {e}")
                raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

        @self.app.get("/session/{session_id}/round/{round_num}/status")
        async def get_round_status(session_id: str, round_num: int):
            """Obtener estado de una ronda específica."""
            try:
                if session_id not in self.active_sessions:
                    raise HTTPException(status_code=404, detail="Session not found")

                session = self.active_sessions[session_id]
                aggregator = self.session_aggregators[session_id]

                return {
                    "session_id": session_id,
                    "round_num": round_num,
                    "current_round": session.current_round,
                    "updates_received": len(aggregator.weight_updates),
                    "required_updates": len(session.participants),
                    "can_aggregate": aggregator.can_aggregate(),
                    "participants": list(session.participants),
                    "status": "completed" if round_num < session.current_round else "in_progress"
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error getting round status: {str(e)}")

        @self.app.get("/session/{session_id}/progress")
        async def get_session_progress(session_id: str):
            """Obtener progreso detallado de entrenamiento de una sesión."""
            try:
                if session_id not in self.active_sessions:
                    raise HTTPException(status_code=404, detail="Session not found")

                session = self.active_sessions[session_id]
                aggregator = self.session_aggregators.get(session_id)

                # Información de rondas completadas
                rounds_progress = []
                for round_num in range(1, session.current_round + 1):
                    rounds_progress.append({
                        "round_num": round_num,
                        "status": "completed",
                        "completed_at": datetime.now().isoformat(),  # Placeholder
                        "participants_contributed": len(session.participants),
                        "total_samples": sum(
                            self.node_registrations.get(p, {}).get("contributions", 0) * 1000  # Estimación
                            for p in session.participants
                        )
                    })

                # Información de ronda actual
                current_round_info = None
                if aggregator and session.current_round <= session.total_rounds:
                    current_round_info = {
                        "round_num": session.current_round,
                        "status": "in_progress" if not session.paused else "paused",
                        "updates_received": len(aggregator.weight_updates),
                        "required_updates": len(session.participants),
                        "progress_percentage": (len(aggregator.weight_updates) / len(session.participants)) * 100 if session.participants else 0,
                        "can_aggregate": aggregator.can_aggregate(),
                        "participants_pending": [
                            p for p in session.participants
                            if not any(update.get("node_id") == p for update in aggregator.weight_updates)
                        ],
                        "participants_completed": [
                            update.get("node_id") for update in aggregator.weight_updates
                        ]
                    }

                # Estadísticas de participantes
                participant_stats = []
                for node_id in session.participants:
                    node_info = self.node_registrations.get(node_id, {})
                    participant_stats.append({
                        "node_id": node_id,
                        "contributions": node_info.get("contributions", 0),
                        "last_contribution": node_info.get("last_update"),
                        "status": node_info.get("status", "unknown"),
                        "rewards_earned": node_info.get("rewards_earned", 0.0),
                        "hardware_info": node_info.get("hardware_info", {}),
                        "data_info": node_info.get("local_data_info", {})
                    })

                # Métricas de rendimiento globales
                total_contributions = sum(p["contributions"] for p in participant_stats)
                avg_contributions_per_node = total_contributions / len(participant_stats) if participant_stats else 0

                return {
                    "session_id": session_id,
                    "overall_progress": {
                        "current_round": session.current_round,
                        "total_rounds": session.total_rounds,
                        "progress_percentage": (session.current_round / session.total_rounds) * 100 if session.total_rounds > 0 else 0,
                        "status": session.status,
                        "is_complete": session.is_complete(),
                        "estimated_completion_time": session._estimate_completion_time()
                    },
                    "rounds_completed": rounds_progress,
                    "current_round": current_round_info,
                    "participant_stats": participant_stats,
                    "global_metrics": {
                        "total_participants": len(session.participants),
                        "active_participants": len([p for p in participant_stats if p["status"] == "active"]),
                        "total_contributions": total_contributions,
                        "avg_contributions_per_node": avg_contributions_per_node,
                        "total_rewards_distributed": session.total_rewards_distributed,
                        "session_uptime": session.get_status()["uptime_seconds"]
                    },
                    "timestamp": datetime.now().isoformat()
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error getting session progress: {str(e)}")

    # ===== WEBSOCKET HELPER METHODS =====

    async def _get_realtime_node_status(self) -> Dict[str, Any]:
        """Obtener estado en tiempo real de nodos para WebSocket."""
        try:
            node_statuses = {}

            # Obtener datos de health monitor si disponible
            if self.health_monitor:
                health_metrics = self.health_monitor.get_all_health_metrics()
                for node_id, metrics in health_metrics.items():
                    node_statuses[node_id] = {
                        "node_id": node_id,
                        "health_status": metrics.overall_health.value,
                        "connectivity_score": metrics.connectivity_score,
                        "performance_score": metrics.performance_score,
                        "contribution_score": metrics.contribution_score,
                        "stability_score": metrics.stability_score,
                        "last_health_check": metrics.last_health_check.isoformat() if metrics.last_health_check else None,
                        "last_seen": metrics.last_seen.isoformat() if metrics.last_seen else None,
                        "response_time_ms": metrics.response_time_ms,
                        "cpu_usage_percent": metrics.cpu_usage_percent,
                        "memory_usage_percent": metrics.memory_usage_percent,
                        "network_latency_ms": metrics.network_latency_ms,
                        "consecutive_failures": metrics.consecutive_failures,
                        "total_contributions": metrics.total_contributions,
                        "successful_contributions": metrics.successful_contributions,
                        "session_success_rate": metrics.session_success_rate,
                        "source": "health_monitor"
                    }

            # Complementar con datos de sesiones activas
            for node_id, info in self.node_registrations.items():
                if node_id not in node_statuses:
                    node_statuses[node_id] = {
                        "node_id": node_id,
                        "health_status": "unknown",
                        "connectivity_score": 0.0,
                        "performance_score": 0.5,
                        "contribution_score": 0.5,
                        "stability_score": 1.0,
                        "last_health_check": info.get("last_update"),
                        "last_seen": info.get("last_update"),
                        "response_time_ms": None,
                        "cpu_usage_percent": None,
                        "memory_usage_percent": None,
                        "network_latency_ms": None,
                        "consecutive_failures": 0,
                        "total_contributions": info.get("contributions", 0),
                        "successful_contributions": info.get("contributions", 0),
                        "session_success_rate": 1.0 if info.get("contributions", 0) > 0 else 0.0,
                        "source": "session_data"
                    }
                else:
                    # Actualizar con datos de sesión si son más recientes
                    session_update = info.get("last_update")
                    if session_update and (not node_statuses[node_id].get("last_seen") or
                                          session_update > node_statuses[node_id]["last_seen"]):
                        node_statuses[node_id]["last_seen"] = session_update
                        node_statuses[node_id]["total_contributions"] = info.get("contributions", 0)

            return {
                "node_statuses": list(node_statuses.values()),
                "total_nodes": len(node_statuses),
                "healthy_nodes": len([n for n in node_statuses.values() if n["health_status"] == "healthy"]),
                "degraded_nodes": len([n for n in node_statuses.values() if n["health_status"] == "degraded"]),
                "unhealthy_nodes": len([n for n in node_statuses.values() if n["health_status"] in ["unhealthy", "critical"]]),
                "timestamp": datetime.now().isoformat(),
                "monitoring_active": self.health_monitor is not None
            }
        except Exception as e:
            logger.error(f"Error getting realtime node status for WebSocket: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def _get_federated_node_registry(self) -> Dict[str, Any]:
        """Obtener registro de nodos federados para WebSocket."""
        try:
            if not self.node_registry:
                # Fallback: usar datos de sesiones activas
                all_nodes = {}
                for session_id, session in self.active_sessions.items():
                    for node_id, info in self.node_registrations.items():
                        if info.get("session_id") == session_id:
                            all_nodes[node_id] = {
                                "node_id": node_id,
                                "status": info.get("status", "unknown"),
                                "last_seen": info.get("last_update"),
                                "hardware_info": info.get("hardware_info", {}),
                                "local_data_info": info.get("local_data_info", {}),
                                "reputation_score": 1.0,  # Default
                                "capabilities": ["federated_learning"],
                                "registered_at": info.get("joined_at"),
                                "location": "Unknown"
                            }

                return {
                    "nodes": list(all_nodes.values()),
                    "total_nodes": len(all_nodes),
                    "active_nodes": len([n for n in all_nodes.values() if n["status"] == "active"]),
                    "timestamp": datetime.now().isoformat(),
                    "source": "session_fallback"
                }

            # Usar NodeRegistry real
            nodes = await self.node_registry.discover_nodes()
            registry_stats = self.node_registry.get_stats()

            return {
                "nodes": [
                    {
                        "node_id": node.metadata.node_id,
                        "status": node.metadata.status,
                        "last_seen": node.metadata.last_seen.isoformat() if node.metadata.last_seen else None,
                        "hardware_capacity": node.metadata.hardware_capacity,
                        "reputation_score": node.metadata.reputation_score,
                        "capabilities": node.metadata.capabilities,
                        "location": node.metadata.location,
                        "registered_at": node.metadata.registered_at.isoformat(),
                        "certificate_valid": True  # Validado por registry
                    }
                    for node in nodes
                ],
                "total_nodes": registry_stats.get("known_nodes", 0),
                "active_nodes": registry_stats.get("active_nodes", 0),
                "cached_nodes": registry_stats.get("cached_nodes", 0),
                "registry_cid": registry_stats.get("registry_cid"),
                "timestamp": datetime.now().isoformat(),
                "source": "node_registry"
            }
        except Exception as e:
            logger.error(f"Error getting federated node registry for WebSocket: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def _get_network_health_status(self) -> Dict[str, Any]:
        """Obtener estado de salud de la red federada para WebSocket."""
        try:
            network_health = {
                "timestamp": datetime.now().isoformat(),
                "network_status": "unknown",
                "connectivity_score": 0.0,
                "performance_score": 0.0,
                "stability_score": 0.0,
                "active_nodes": 0,
                "total_nodes": 0,
                "network_efficiency": 0.0,
                "average_latency_ms": None,
                "packet_loss_rate": 0.0,
                "bandwidth_utilization": 0.0,
                "alerts": [],
                "recommendations": []
            }

            # Obtener datos del health monitor
            if self.health_monitor:
                summary = self.health_monitor.get_system_health_summary()
                optimization = self.health_monitor.get_optimization_metrics()

                network_health.update({
                    "network_status": summary.get("status", "unknown"),
                    "connectivity_score": summary.get("average_connectivity", 0.0),
                    "performance_score": summary.get("average_performance", 0.0),
                    "stability_score": 1.0,  # Placeholder
                    "active_nodes": summary.get("healthy_nodes", 0) + summary.get("degraded_nodes", 0),
                    "total_nodes": summary.get("total_nodes", 0),
                    "network_efficiency": (summary.get("healthy_nodes", 0) / max(summary.get("total_nodes", 1), 1)) * 100,
                    "alerts": [alert.to_dict() for alert in self.health_monitor.get_active_alerts()],
                    "recommendations": optimization.get("recommended_actions", [])
                })

                # Calcular latencia promedio
                all_metrics = self.health_monitor.get_all_health_metrics()
                latencies = [m.network_latency_ms for m in all_metrics.values() if m.network_latency_ms is not None]
                if latencies:
                    network_health["average_latency_ms"] = statistics.mean(latencies)

            # Complementar con datos de sesiones
            session_nodes = len(self.node_registrations)
            active_session_nodes = len([n for n in self.node_registrations.values() if n.get("status") == "active"])

            if not self.health_monitor:
                network_health.update({
                    "network_status": "active" if active_session_nodes > 0 else "idle",
                    "connectivity_score": 0.9 if active_session_nodes > 0 else 0.1,
                    "performance_score": 0.8,
                    "stability_score": 0.95,
                    "active_nodes": active_session_nodes,
                    "total_nodes": session_nodes,
                    "network_efficiency": (active_session_nodes / max(session_nodes, 1)) * 100,
                    "source": "session_fallback"
                })

            # Obtener métricas de red del realtime monitor
            if self.realtime_monitor:
                system_status = self.realtime_monitor.get_system_status()
                current_metrics = system_status.get("current_metrics", {})

                network_metrics = current_metrics.get("network_io", {})
                if network_metrics:
                    network_health["bandwidth_utilization"] = network_metrics.get("bytes_sent", 0) + network_metrics.get("bytes_recv", 0)

            return network_health
        except Exception as e:
            logger.error(f"Error getting network health status for WebSocket: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def _get_session_training_progress(self, session_id: str) -> Dict[str, Any]:
        """Obtener progreso de entrenamiento de una sesión para WebSocket."""
        try:
            if session_id not in self.active_sessions:
                return {"error": f"Session {session_id} not found"}

            session = self.active_sessions[session_id]
            aggregator = self.session_aggregators.get(session_id)

            # Información de rondas completadas
            rounds_progress = []
            for round_num in range(1, session.current_round + 1):
                rounds_progress.append({
                    "round_num": round_num,
                    "status": "completed",
                    "completed_at": datetime.now().isoformat(),  # Placeholder
                    "participants_contributed": len(session.participants),
                    "total_samples": sum(
                        self.node_registrations.get(p, {}).get("contributions", 0) * 1000  # Estimación
                        for p in session.participants
                    )
                })

            # Información de ronda actual
            current_round_info = None
            if aggregator and session.current_round <= session.total_rounds:
                current_round_info = {
                    "round_num": session.current_round,
                    "status": "in_progress" if not session.paused else "paused",
                    "updates_received": len(aggregator.weight_updates),
                    "required_updates": len(session.participants),
                    "progress_percentage": (len(aggregator.weight_updates) / len(session.participants)) * 100 if session.participants else 0,
                    "can_aggregate": aggregator.can_aggregate(),
                    "participants_pending": [
                        p for p in session.participants
                        if not any(update.get("node_id") == p for update in aggregator.weight_updates)
                    ],
                    "participants_completed": [
                        update.get("node_id") for update in aggregator.weight_updates
                    ]
                }

            return {
                "session_id": session_id,
                "overall_progress": {
                    "current_round": session.current_round,
                    "total_rounds": session.total_rounds,
                    "progress_percentage": (session.current_round / session.total_rounds) * 100 if session.total_rounds > 0 else 0,
                    "status": session.status,
                    "is_complete": session.is_complete(),
                    "estimated_completion_time": session._estimate_completion_time()
                },
                "rounds_completed": rounds_progress,
                "current_round": current_round_info,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting session training progress for WebSocket: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def _get_session_participants_data(self, session_id: str) -> Dict[str, Any]:
        """Obtener datos de participantes de una sesión para WebSocket."""
        try:
            if session_id not in self.active_sessions:
                return {"error": f"Session {session_id} not found"}

            session = self.active_sessions[session_id]

            # Estadísticas de participantes
            participant_stats = []
            for node_id in session.participants:
                node_info = self.node_registrations.get(node_id, {})
                participant_stats.append({
                    "node_id": node_id,
                    "contributions": node_info.get("contributions", 0),
                    "last_contribution": node_info.get("last_update"),
                    "status": node_info.get("status", "unknown"),
                    "rewards_earned": node_info.get("rewards_earned", 0.0),
                    "hardware_info": node_info.get("hardware_info", {}),
                    "data_info": node_info.get("local_data_info", {}),
                    "joined_at": node_info.get("joined_at"),
                    "last_seen": node_info.get("last_update")
                })

            # Métricas de rendimiento globales
            total_contributions = sum(p["contributions"] for p in participant_stats)
            avg_contributions_per_node = total_contributions / len(participant_stats) if participant_stats else 0

            return {
                "session_id": session_id,
                "participant_stats": participant_stats,
                "global_metrics": {
                    "total_participants": len(session.participants),
                    "active_participants": len([p for p in participant_stats if p["status"] == "active"]),
                    "total_contributions": total_contributions,
                    "avg_contributions_per_node": avg_contributions_per_node,
                    "total_rewards_distributed": session.total_rewards_distributed,
                    "session_uptime": session.get_status()["uptime_seconds"]
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting session participants data for WebSocket: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def _get_session_training_metrics(self, session_id: str) -> Dict[str, Any]:
        """Obtener métricas de entrenamiento de una sesión para WebSocket."""
        try:
            if session_id not in self.active_sessions:
                return {"error": f"Session {session_id} not found"}

            session = self.active_sessions[session_id]
            trainer = self.session_trainers.get(session_id)
            aggregator = self.session_aggregators.get(session_id)

            metrics_data = {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "training_metrics": {},
                "performance_metrics": {},
                "aggregation_metrics": {},
                "system_metrics": {}
            }

            # Métricas de entrenamiento del trainer
            if trainer:
                trainer_status = trainer.get_status()
                metrics_data["training_metrics"] = {
                    "model_name": trainer_status.get("model_name"),
                    "dataset_name": trainer_status.get("dataset_name"),
                    "current_round": trainer_status.get("current_round", 0),
                    "total_parameters": trainer_status.get("total_parameters", 0),
                    "privacy_budget_used": trainer_status.get("privacy_budget_used", 0.0),
                    "model_accuracy": trainer_status.get("model_accuracy", 0.0),
                    "training_loss": trainer_status.get("training_loss", 0.0),
                    "validation_accuracy": trainer_status.get("validation_accuracy", 0.0)
                }

            # Métricas de agregación
            if aggregator:
                aggregator_status = aggregator.get_status()
                metrics_data["aggregation_metrics"] = {
                    "total_weight_updates": aggregator_status.get("total_weight_updates", 0),
                    "successful_aggregations": aggregator_status.get("successful_aggregations", 0),
                    "failed_aggregations": aggregator_status.get("failed_aggregations", 0),
                    "average_aggregation_time": aggregator_status.get("average_aggregation_time", 0.0),
                    "last_aggregation_cid": aggregator_status.get("last_aggregation_cid"),
                    "fedavg_efficiency": aggregator_status.get("fedavg_efficiency", 0.0)
                }

            # Métricas de rendimiento de participantes
            participant_performance = []
            for node_id in session.participants:
                node_info = self.node_registrations.get(node_id, {})
                participant_performance.append({
                    "node_id": node_id,
                    "contributions": node_info.get("contributions", 0),
                    "contribution_frequency": node_info.get("contribution_frequency", 0.0),
                    "average_response_time": node_info.get("average_response_time", 0.0),
                    "data_quality_score": node_info.get("data_quality_score", 0.8),
                    "hardware_utilization": node_info.get("hardware_utilization", {}),
                    "last_activity": node_info.get("last_update")
                })

            metrics_data["performance_metrics"] = {
                "participant_performance": participant_performance,
                "average_contribution_time": statistics.mean([p["average_response_time"] for p in participant_performance]) if participant_performance else 0.0,
                "total_active_participants": len([p for p in participant_performance if p["contributions"] > 0]),
                "network_reliability": len([p for p in participant_performance if p["contributions"] > 0]) / len(participant_performance) if participant_performance else 0.0
            }

            # Métricas del sistema
            metrics_data["system_metrics"] = {
                "session_uptime_seconds": session.get_status()["uptime_seconds"],
                "total_data_processed": self.system_stats["total_data_processed"],
                "total_rounds_completed": self.system_stats["total_rounds_completed"],
                "network_efficiency": (len([p for p in participant_performance if p["contributions"] > 0]) / len(participant_performance)) * 100 if participant_performance else 0.0,
                "average_round_duration": session.get_status()["uptime_seconds"] / max(session.current_round, 1)
            }

            return metrics_data
        except Exception as e:
            logger.error(f"Error getting session training metrics for WebSocket: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    # ===== BROADCASTING METHODS =====

    async def _broadcast_node_status_update(self, node_data: Dict[str, Any]):
        """Broadcast actualización de estado de nodo."""
        try:
            await self.websocket_realtime_monitor.broadcast_federated_node_update(node_data)
        except Exception as e:
            logger.error(f"Error broadcasting node status update: {e}")

    async def _broadcast_registry_update(self, registry_data: Dict[str, Any]):
        """Broadcast actualización del registro de nodos."""
        try:
            await self.websocket_realtime_monitor.broadcast_federated_registry_update(registry_data)
        except Exception as e:
            logger.error(f"Error broadcasting registry update: {e}")

    async def _broadcast_health_update(self, health_data: Dict[str, Any]):
        """Broadcast actualización de salud de la red."""
        try:
            await self.websocket_realtime_monitor.broadcast_federated_health_update(health_data)
        except Exception as e:
            logger.error(f"Error broadcasting health update: {e}")

    async def _broadcast_training_progress_update(self, session_id: str, progress_data: Dict[str, Any]):
        """Broadcast actualización de progreso de entrenamiento."""
        try:
            await self.websocket_realtime_monitor.broadcast_training_progress_update(session_id, progress_data)
        except Exception as e:
            logger.error(f"Error broadcasting training progress update for session {session_id}: {e}")

    async def _broadcast_training_participants_update(self, session_id: str, participants_data: Dict[str, Any]):
        """Broadcast actualización de participantes de entrenamiento."""
        try:
            await self.websocket_realtime_monitor.broadcast_training_participants_update(session_id, participants_data)
        except Exception as e:
            logger.error(f"Error broadcasting training participants update for session {session_id}: {e}")

    async def _broadcast_training_metrics_update(self, session_id: str, metrics_data: Dict[str, Any]):
        """Broadcast actualización de métricas de entrenamiento."""
        try:
            await self.websocket_realtime_monitor.broadcast_training_metrics_update(session_id, metrics_data)
        except Exception as e:
            logger.error(f"Error broadcasting training metrics update for session {session_id}: {e}")

    def _resolve_allow_mocks(self) -> bool:
        """Resolver si se permiten mocks/simulaciones según entorno."""
        allow_env = os.getenv("AILOOS_ALLOW_MOCKS", "").lower() in ("1", "true", "yes")
        return allow_env or self.config.environment != "production"

    def create_app(self) -> FastAPI:
        """Crear y retornar la aplicación FastAPI."""
        return self.app

    def start_server(self, host: str = "0.0.0.0", port: int = 8001):
        """Iniciar servidor FastAPI."""
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )


# Instancia global de la API federada
federated_api = FederatedAPI()


def create_federated_app() -> FastAPI:
    """Función de conveniencia para crear la app FastAPI federada."""
    return federated_api.create_app()


if __name__ == "__main__":
    # Iniciar servidor para pruebas
    print("🚀 Iniciando AILOOS Federated Learning API...")
    federated_api.start_server()
