"""
Federated Learning Dashboard for AILOOS - Training Progress and Model Metrics
Provides comprehensive monitoring of federated learning training sessions, model performance, and convergence metrics.
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
from ..federated.coordinator import FederatedCoordinator
from ..federated.data_coordinator import FederatedDataCoordinator

logger = get_logger(__name__)


class TrainingStatus(Enum):
    """Estados de entrenamiento."""
    INITIALIZING = "initializing"
    TRAINING = "training"
    AGGREGATING = "aggregating"
    EVALUATING = "evaluating"
    CONVERGED = "converged"
    PAUSED = "paused"
    FAILED = "failed"
    COMPLETED = "completed"


class ModelType(Enum):
    """Tipos de modelo."""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    NLP = "nlp"
    COMPUTER_VISION = "computer_vision"
    GENERATIVE = "generative"


@dataclass
class FederatedSession:
    """Sesión de entrenamiento federado."""
    session_id: str
    model_name: str
    model_type: ModelType
    status: TrainingStatus
    start_time: float
    end_time: Optional[float] = None
    total_rounds: int = 10
    current_round: int = 0
    participants: List[str] = field(default_factory=list)
    global_accuracy: float = 0.0
    global_loss: float = 0.0
    convergence_threshold: float = 0.001
    dataset_size: int = 0
    batch_size: int = 32
    learning_rate: float = 0.001
    optimizer: str = "adam"
    metrics_history: Dict[str, List[float]] = field(default_factory=dict)


@dataclass
class NodeContribution:
    """Contribución de un nodo."""
    node_id: str
    session_id: str
    round_number: int
    local_accuracy: float = 0.0
    local_loss: float = 0.0
    samples_contributed: int = 0
    training_time: float = 0.0
    model_updates_size: int = 0  # bytes
    contribution_timestamp: float = 0.0
    validation_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregationMetrics:
    """Métricas de agregación."""
    round_number: int
    session_id: str
    aggregation_method: str = "fedavg"
    participants_count: int = 0
    total_samples: int = 0
    aggregation_time: float = 0.0
    model_size_before: int = 0  # bytes
    model_size_after: int = 0  # bytes
    compression_ratio: float = 1.0
    privacy_budget_used: float = 0.0
    convergence_improvement: float = 0.0
    timestamp: float = 0.0


@dataclass
class FederatedMetrics:
    """Métricas generales de federated learning."""
    active_sessions: int = 0
    total_sessions: int = 0
    completed_sessions: int = 0
    failed_sessions: int = 0
    total_participants: int = 0
    active_participants: int = 0
    total_training_time: float = 0.0
    average_session_duration: float = 0.0
    models_deployed: int = 0
    total_data_processed: float = 0.0  # GB
    average_accuracy: float = 0.0
    best_accuracy: float = 0.0
    convergence_rate: float = 0.0
    communication_efficiency: float = 0.0


class FederatedLearningDashboard:
    """
    Dashboard especializado para monitoreo de federated learning.
    Proporciona métricas detalladas de entrenamiento, convergencia y rendimiento.
    """

    def __init__(self,
                 federated_coordinator: Optional[FederatedCoordinator] = None,
                 data_coordinator: Optional[FederatedDataCoordinator] = None,
                 jwt_secret: str = "federated-dashboard-secret",
                 update_interval: float = 10.0):  # Actualización cada 10 segundos para FL

        self.config = get_config()
        self.state_manager = get_state_manager()
        self.federated_coordinator = federated_coordinator
        self.data_coordinator = data_coordinator

        # Configuración de seguridad
        self.jwt_secret = jwt_secret
        self.update_interval = update_interval

        # Estado del dashboard
        self.is_running = False
        self.last_update = 0.0

        # Datos de federated learning
        self.active_sessions: Dict[str, FederatedSession] = {}
        self.node_contributions: List[NodeContribution] = []
        self.aggregation_history: List[AggregationMetrics] = []
        self.federated_metrics = FederatedMetrics()

        # Callbacks
        self.update_callbacks: List[Callable] = []
        self.session_callbacks: List[Callable] = []

        # WebSocket connections
        self.websocket_connections: Dict[str, WebSocket] = {}

        # Historial de métricas
        self.metrics_history: Dict[str, List] = {
            'sessions': [],
            'contributions': [],
            'aggregations': [],
            'federated_metrics': []
        }

        # FastAPI application
        self.app = FastAPI(
            title="AILOOS Federated Learning Dashboard API",
            description="Specialized dashboard for federated learning training progress and metrics",
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

        logger.info("🤖 FederatedLearningDashboard initialized")

    def _setup_routes(self):
        """Configurar rutas del dashboard FL."""

        @self.app.get("/")
        async def get_federated_dashboard():
            """Obtener dashboard de federated learning completo."""
            return self.get_federated_dashboard_data()

        @self.app.get("/api/federated/sessions")
        async def get_sessions(user: dict = Depends(get_current_user)):
            """Obtener sesiones de entrenamiento."""
            if not self._has_federated_access(user):
                raise HTTPException(status_code=403, detail="Acceso federated requerido")

            return {
                "sessions": [self._session_to_dict(session) for session in self.active_sessions.values()],
                "active_count": len(self.active_sessions),
                "timestamp": datetime.now().isoformat()
            }

        @self.app.get("/api/federated/sessions/{session_id}")
        async def get_session_details(session_id: str, user: dict = Depends(get_current_user)):
            """Obtener detalles de una sesión específica."""
            if not self._has_federated_access(user):
                raise HTTPException(status_code=403, detail="Acceso federated requerido")

            if session_id not in self.active_sessions:
                raise HTTPException(status_code=404, detail="Sesión no encontrada")

            session = self.active_sessions[session_id]
            contributions = [self._contribution_to_dict(c) for c in self.node_contributions
                           if c.session_id == session_id]

            return {
                "session": self._session_to_dict(session),
                "contributions": contributions,
                "aggregations": [self._aggregation_to_dict(a) for a in self.aggregation_history
                               if a.session_id == session_id],
                "timestamp": datetime.now().isoformat()
            }

        @self.app.get("/api/federated/metrics")
        async def get_federated_metrics(user: dict = Depends(get_current_user)):
            """Obtener métricas generales de FL."""
            if not self._has_federated_access(user):
                raise HTTPException(status_code=403, detail="Acceso federated requerido")

            return {
                "federated_metrics": self._federated_metrics_to_dict(),
                "timestamp": datetime.now().isoformat()
            }

        @self.app.get("/api/federated/contributions")
        async def get_contributions(session_id: Optional[str] = None, limit: int = 50, user: dict = Depends(get_current_user)):
            """Obtener contribuciones de nodos."""
            if not self._has_federated_access(user):
                raise HTTPException(status_code=403, detail="Acceso federated requerido")

            contributions = self.node_contributions
            if session_id:
                contributions = [c for c in contributions if c.session_id == session_id]

            return {
                "contributions": [self._contribution_to_dict(c) for c in contributions[-limit:]],
                "total_count": len(contributions),
                "timestamp": datetime.now().isoformat()
            }

        @self.app.get("/api/federated/aggregations")
        async def get_aggregations(session_id: Optional[str] = None, limit: int = 20, user: dict = Depends(get_current_user)):
            """Obtener historial de agregaciones."""
            if not self._has_federated_access(user):
                raise HTTPException(status_code=403, detail="Acceso federated requerido")

            aggregations = self.aggregation_history
            if session_id:
                aggregations = [a for a in aggregations if a.session_id == session_id]

            return {
                "aggregations": [self._aggregation_to_dict(a) for a in aggregations[-limit:]],
                "total_count": len(aggregations),
                "timestamp": datetime.now().isoformat()
            }

        @self.app.post("/api/federated/sessions/{session_id}/pause")
        async def pause_session(session_id: str, user: dict = Depends(require_admin)):
            """Pausar sesión de entrenamiento."""
            if session_id not in self.active_sessions:
                raise HTTPException(status_code=404, detail="Sesión no encontrada")

            self.active_sessions[session_id].status = TrainingStatus.PAUSED
            return {"message": f"Sesión {session_id} pausada"}

        @self.app.post("/api/federated/sessions/{session_id}/resume")
        async def resume_session(session_id: str, user: dict = Depends(require_admin)):
            """Reanudar sesión de entrenamiento."""
            if session_id not in self.active_sessions:
                raise HTTPException(status_code=404, detail="Sesión no encontrada")

            self.active_sessions[session_id].status = TrainingStatus.TRAINING
            return {"message": f"Sesión {session_id} reanudada"}

        @self.app.get("/api/federated/reports/{report_type}")
        async def generate_federated_report(report_type: str, session_id: Optional[str] = None, user: dict = Depends(get_current_user)):
            """Generar reporte de federated learning."""
            if not self._has_federated_access(user):
                raise HTTPException(status_code=403, detail="Acceso federated requerido")

            try:
                return await self.generate_federated_report(report_type, session_id)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.websocket("/ws/federated")
        async def federated_websocket(websocket: WebSocket, user: dict = Depends(get_current_user)):
            """WebSocket para actualizaciones de FL en tiempo real."""
            if not self._has_federated_access(user):
                await websocket.close(code=1008)
                return

            await self.handle_federated_websocket(websocket, user.get("username"))

        @self.app.get("/api/federated/health")
        async def get_federated_health():
            """Obtener estado de salud del dashboard FL."""
            return self.get_health_status()

    def _has_federated_access(self, user: dict) -> bool:
        """Verificar si el usuario tiene acceso federated."""
        user_roles = user.get("roles", [])
        federated_roles = ["admin", "researcher", "ml_engineer", "data_scientist"]

        return any(role in federated_roles for role in user_roles)

    async def start_monitoring(self):
        """Iniciar monitoreo de federated learning."""
        if self.is_running:
            return

        self.is_running = True
        logger.info("🤖 Starting federated learning monitoring")

        # Tarea de monitoreo continuo
        asyncio.create_task(self._federated_monitoring_loop())

    async def stop_monitoring(self):
        """Detener monitoreo de federated learning."""
        self.is_running = False
        logger.info("🛑 Federated learning monitoring stopped")

    async def _federated_monitoring_loop(self):
        """Loop principal de monitoreo FL."""
        last_broadcast = 0.0

        while self.is_running:
            try:
                await self._update_federated_metrics()
                await self._simulate_training_progress()  # Simulación para demo
                await self._notify_callbacks()

                self.last_update = asyncio.get_event_loop().time()

                # Broadcast WebSocket updates
                current_time = asyncio.get_event_loop().time()
                if current_time - last_broadcast >= 5.0:  # Broadcast cada 5 segundos para FL
                    await self._broadcast_federated_updates()
                    last_broadcast = current_time

            except Exception as e:
                logger.error(f"❌ Error in federated monitoring loop: {e}")

            await asyncio.sleep(self.update_interval)

    async def _update_federated_metrics(self):
        """Actualizar métricas de federated learning."""
        try:
            # Obtener datos reales del coordinador si está disponible
            if self.federated_coordinator:
                active_sessions = self.federated_coordinator.get_active_sessions()
                self.federated_metrics.active_sessions = len(active_sessions)
                self.federated_metrics.total_participants = sum(len(s.get('participants', [])) for s in active_sessions)
                self.federated_metrics.active_participants = self.federated_metrics.total_participants

                # Calcular métricas agregadas
                accuracies = []
                for session in active_sessions:
                    metrics = session.get('metrics', {})
                    accuracy = metrics.get('global_accuracy', 0.0)
                    if accuracy > 0:
                        accuracies.append(accuracy)

                if accuracies:
                    self.federated_metrics.average_accuracy = sum(accuracies) / len(accuracies)
                    self.federated_metrics.best_accuracy = max(accuracies)

            # Simular sesiones activas para demo
            await self._simulate_active_sessions()

        except Exception as e:
            logger.error(f"❌ Error updating federated metrics: {e}")

    async def _simulate_active_sessions(self):
        """Simular sesiones activas para demostración."""
        current_time = asyncio.get_event_loop().time()

        # Crear sesiones de ejemplo si no existen
        if not self.active_sessions:
            sessions_data = [
                {
                    "session_id": "emp_session_001",
                    "model_name": "EmpoorioLM-Classifier",
                    "model_type": ModelType.CLASSIFICATION,
                    "status": TrainingStatus.TRAINING,
                    "start_time": current_time - 3600,  # 1 hora atrás
                    "total_rounds": 10,
                    "current_round": 3,
                    "participants": ["node_001", "node_002", "node_003"],
                    "global_accuracy": 0.82,
                    "global_loss": 0.45,
                    "dataset_size": 50000,
                    "batch_size": 32,
                    "learning_rate": 0.001
                },
                {
                    "session_id": "vision_session_002",
                    "model_name": "FedVision-Net",
                    "model_type": ModelType.COMPUTER_VISION,
                    "status": TrainingStatus.AGGREGATING,
                    "start_time": current_time - 1800,  # 30 min atrás
                    "total_rounds": 15,
                    "current_round": 7,
                    "participants": ["node_004", "node_005"],
                    "global_accuracy": 0.91,
                    "global_loss": 0.23,
                    "dataset_size": 25000,
                    "batch_size": 16,
                    "learning_rate": 0.0005
                }
            ]

            for session_data in sessions_data:
                session = FederatedSession(**session_data)
                # Inicializar historial de métricas
                session.metrics_history = {
                    'accuracy': [0.75, 0.78, 0.80, 0.82],
                    'loss': [0.65, 0.58, 0.52, 0.45],
                    'convergence': [0.0, 0.2, 0.5, 0.7]
                }
                self.active_sessions[session.session_id] = session

        # Actualizar progreso de sesiones activas
        for session in self.active_sessions.values():
            if session.status == TrainingStatus.TRAINING:
                # Simular progreso
                progress_increment = 0.01 + (hash(session.session_id) % 10) * 0.005
                session.global_accuracy = min(0.95, session.global_accuracy + progress_increment)
                session.global_loss = max(0.1, session.global_loss - progress_increment * 2)

                # Actualizar historial
                session.metrics_history['accuracy'].append(session.global_accuracy)
                session.metrics_history['loss'].append(session.global_loss)

                # Mantener solo últimas 20 entradas
                for metric in session.metrics_history:
                    if len(session.metrics_history[metric]) > 20:
                        session.metrics_history[metric].pop(0)

                # Simular contribuciones de nodos
                if (current_time % 60) < 10:  # Cada ~1 minuto
                    for node_id in session.participants:
                        contribution = NodeContribution(
                            node_id=node_id,
                            session_id=session.session_id,
                            round_number=session.current_round,
                            local_accuracy=session.global_accuracy + (hash(node_id) % 20 - 10) * 0.01,
                            local_loss=session.global_loss + (hash(node_id) % 10) * 0.02,
                            samples_contributed=100 + hash(node_id) % 200,
                            training_time=45.0 + (hash(node_id) % 30),
                            model_updates_size=5000000 + hash(node_id) % 1000000,
                            contribution_timestamp=current_time
                        )
                        self.node_contributions.append(contribution)

                        # Mantener solo últimas 100 contribuciones
                        if len(self.node_contributions) > 100:
                            self.node_contributions.pop(0)

                # Simular agregación
                if (current_time % 120) < 10:  # Cada ~2 minutos
                    aggregation = AggregationMetrics(
                        round_number=session.current_round,
                        session_id=session.session_id,
                        aggregation_method="fedavg",
                        participants_count=len(session.participants),
                        total_samples=sum(100 + hash(n) % 200 for n in session.participants),
                        aggregation_time=12.5 + (hash(session.session_id) % 10),
                        model_size_before=10000000,
                        model_size_after=8000000,
                        compression_ratio=0.8,
                        privacy_budget_used=0.05,
                        convergence_improvement=progress_increment * 10,
                        timestamp=current_time
                    )
                    self.aggregation_history.append(aggregation)

                    # Avanzar ronda
                    session.current_round += 1
                    if session.current_round >= session.total_rounds:
                        session.status = TrainingStatus.CONVERGED
                        session.end_time = current_time

                    # Mantener solo últimas 50 agregaciones
                    if len(self.aggregation_history) > 50:
                        self.aggregation_history.pop(0)

    async def _notify_callbacks(self):
        """Notificar callbacks de actualización."""
        for callback in self.update_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self)
                else:
                    await asyncio.get_event_loop().run_in_executor(None, callback, self)
            except Exception as e:
                logger.error(f"Error in federated update callback: {e}")

    async def _broadcast_federated_updates(self):
        """Broadcast updates a conexiones WebSocket."""
        try:
            dashboard_data = self.get_federated_dashboard_data()

            disconnected_clients = []
            for client_id, websocket in self.websocket_connections.items():
                try:
                    await websocket.send_json({
                        "type": "federated_update",
                        "timestamp": asyncio.get_event_loop().time(),
                        "data": dashboard_data
                    })
                except Exception as e:
                    logger.warning(f"Failed to send federated update to {client_id}: {e}")
                    disconnected_clients.append(client_id)

            # Limpiar conexiones desconectadas
            for client_id in disconnected_clients:
                del self.websocket_connections[client_id]

        except Exception as e:
            logger.error(f"Error broadcasting federated updates: {e}")

    async def handle_federated_websocket(self, websocket: WebSocket, client_id: str):
        """Manejar conexión WebSocket para FL."""
        await websocket.accept()
        self.websocket_connections[client_id] = websocket

        logger.info(f"🤖 Federated WebSocket connected: {client_id}")

        try:
            # Enviar datos iniciales
            initial_data = self.get_federated_dashboard_data()
            await websocket.send_json({
                "type": "initial_data",
                "timestamp": asyncio.get_event_loop().time(),
                "data": initial_data
            })

            # Mantener conexión viva
            while True:
                try:
                    message = await asyncio.wait_for(
                        websocket.receive_json(),
                        timeout=60.0
                    )

                    await self._handle_federated_websocket_message(websocket, client_id, message)

                except asyncio.TimeoutError:
                    await websocket.send_json({"type": "ping"})

        except WebSocketDisconnect:
            logger.info(f"🤖 Federated WebSocket disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Federated WebSocket error for {client_id}: {e}")
        finally:
            if client_id in self.websocket_connections:
                del self.websocket_connections[client_id]

    async def _handle_federated_websocket_message(self, websocket: WebSocket, client_id: str, message: Dict[str, Any]):
        """Manejar mensajes WebSocket de FL."""
        try:
            message_type = message.get("type", "unknown")

            if message_type == "subscribe_session":
                session_id = message.get("session_id")
                if session_id and session_id in self.active_sessions:
                    # Enviar datos específicos de la sesión
                    session_data = self.get_session_data(session_id)
                    await websocket.send_json({
                        "type": "session_data",
                        "session_id": session_id,
                        "data": session_data
                    })

            elif message_type == "request_metrics_history":
                session_id = message.get("session_id")
                metric_type = message.get("metric_type", "accuracy")
                limit = message.get("limit", 20)

                if session_id in self.active_sessions:
                    session = self.active_sessions[session_id]
                    history = session.metrics_history.get(metric_type, [])[-limit:]
                    await websocket.send_json({
                        "type": "metrics_history",
                        "session_id": session_id,
                        "metric_type": metric_type,
                        "data": history
                    })

        except Exception as e:
            logger.error(f"Error handling federated WebSocket message: {e}")
            await websocket.send_json({
                "type": "error",
                "message": f"Error processing message: {e}"
            })

    def get_federated_dashboard_data(self) -> Dict[str, Any]:
        """Obtener datos completos del dashboard FL."""
        return {
            "federated_metrics": self._federated_metrics_to_dict(),
            "active_sessions": [self._session_to_dict(session) for session in self.active_sessions.values()],
            "recent_contributions": [self._contribution_to_dict(c) for c in self.node_contributions[-10:]],
            "recent_aggregations": [self._aggregation_to_dict(a) for a in self.aggregation_history[-5:]],
            "last_update": self.last_update,
            "timestamp": asyncio.get_event_loop().time()
        }

    def get_session_data(self, session_id: str) -> Dict[str, Any]:
        """Obtener datos detallados de una sesión."""
        if session_id not in self.active_sessions:
            return {}

        session = self.active_sessions[session_id]
        contributions = [self._contribution_to_dict(c) for c in self.node_contributions
                        if c.session_id == session_id][-20:]
        aggregations = [self._aggregation_to_dict(a) for a in self.aggregation_history
                       if a.session_id == session_id][-10:]

        return {
            "session": self._session_to_dict(session),
            "contributions": contributions,
            "aggregations": aggregations,
            "metrics_history": session.metrics_history
        }

    def _session_to_dict(self, session: FederatedSession) -> Dict[str, Any]:
        """Convertir sesión a diccionario."""
        return {
            "session_id": session.session_id,
            "model_name": session.model_name,
            "model_type": session.model_type.value,
            "status": session.status.value,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "total_rounds": session.total_rounds,
            "current_round": session.current_round,
            "round_progress": (session.current_round / session.total_rounds) * 100 if session.total_rounds > 0 else 0,
            "participants": session.participants,
            "participants_count": len(session.participants),
            "global_accuracy": round(session.global_accuracy, 4),
            "global_loss": round(session.global_loss, 4),
            "convergence_threshold": session.convergence_threshold,
            "dataset_size": session.dataset_size,
            "batch_size": session.batch_size,
            "learning_rate": session.learning_rate,
            "optimizer": session.optimizer,
            "duration_seconds": (asyncio.get_event_loop().time() - session.start_time) if not session.end_time else (session.end_time - session.start_time)
        }

    def _contribution_to_dict(self, contribution: NodeContribution) -> Dict[str, Any]:
        """Convertir contribución a diccionario."""
        return {
            "node_id": contribution.node_id,
            "session_id": contribution.session_id,
            "round_number": contribution.round_number,
            "local_accuracy": round(contribution.local_accuracy, 4),
            "local_loss": round(contribution.local_loss, 4),
            "samples_contributed": contribution.samples_contributed,
            "training_time": round(contribution.training_time, 2),
            "model_updates_size": contribution.model_updates_size,
            "contribution_timestamp": contribution.contribution_timestamp,
            "validation_metrics": contribution.validation_metrics
        }

    def _aggregation_to_dict(self, aggregation: AggregationMetrics) -> Dict[str, Any]:
        """Convertir agregación a diccionario."""
        return {
            "round_number": aggregation.round_number,
            "session_id": aggregation.session_id,
            "aggregation_method": aggregation.aggregation_method,
            "participants_count": aggregation.participants_count,
            "total_samples": aggregation.total_samples,
            "aggregation_time": round(aggregation.aggregation_time, 2),
            "model_size_before": aggregation.model_size_before,
            "model_size_after": aggregation.model_size_after,
            "compression_ratio": round(aggregation.compression_ratio, 3),
            "privacy_budget_used": round(aggregation.privacy_budget_used, 4),
            "convergence_improvement": round(aggregation.convergence_improvement, 4),
            "timestamp": aggregation.timestamp
        }

    def _federated_metrics_to_dict(self) -> Dict[str, Any]:
        """Convertir métricas federated a diccionario."""
        return {
            "active_sessions": self.federated_metrics.active_sessions,
            "total_sessions": self.federated_metrics.total_sessions,
            "completed_sessions": self.federated_metrics.completed_sessions,
            "failed_sessions": self.federated_metrics.failed_sessions,
            "total_participants": self.federated_metrics.total_participants,
            "active_participants": self.federated_metrics.active_participants,
            "total_training_time": round(self.federated_metrics.total_training_time, 2),
            "average_session_duration": round(self.federated_metrics.average_session_duration, 2),
            "models_deployed": self.federated_metrics.models_deployed,
            "total_data_processed": round(self.federated_metrics.total_data_processed, 2),
            "average_accuracy": round(self.federated_metrics.average_accuracy, 4),
            "best_accuracy": round(self.federated_metrics.best_accuracy, 4),
            "convergence_rate": round(self.federated_metrics.convergence_rate, 4),
            "communication_efficiency": round(self.federated_metrics.communication_efficiency, 4)
        }

    def get_metrics_history(self, metric_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtener historial de métricas."""
        if metric_type not in self.metrics_history:
            return []

        return self.metrics_history[metric_type][-limit:]

    def get_health_status(self) -> Dict[str, Any]:
        """Obtener estado de salud del dashboard FL."""
        return {
            "is_running": self.is_running,
            "last_update": self.last_update,
            "active_websocket_connections": len(self.websocket_connections),
            "active_sessions": len(self.active_sessions),
            "total_contributions": len(self.node_contributions),
            "total_aggregations": len(self.aggregation_history),
            "metrics_history_size": {k: len(v) for k, v in self.metrics_history.items()},
            "timestamp": asyncio.get_event_loop().time()
        }

    async def generate_federated_report(self, report_type: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Generar reporte de federated learning."""
        if report_type == "session_summary":
            if not session_id or session_id not in self.active_sessions:
                raise ValueError("Sesión no encontrada")

            session = self.active_sessions[session_id]
            return {
                "report_type": "session_summary",
                "generated_at": datetime.now().isoformat(),
                "session_data": self._session_to_dict(session),
                "performance_analysis": self._analyze_session_performance(session),
                "summary": self._generate_session_summary(session)
            }

        elif report_type == "federated_overview":
            return {
                "report_type": "federated_overview",
                "generated_at": datetime.now().isoformat(),
                "federated_metrics": self._federated_metrics_to_dict(),
                "active_sessions_summary": [self._session_summary(s) for s in self.active_sessions.values()],
                "summary": self._generate_federated_overview_summary()
            }

        elif report_type == "convergence_analysis":
            return {
                "report_type": "convergence_analysis",
                "generated_at": datetime.now().isoformat(),
                "session_id": session_id,
                "convergence_data": self._analyze_convergence(session_id) if session_id else {},
                "summary": self._generate_convergence_summary(session_id)
            }

        else:
            raise ValueError(f"Tipo de reporte desconocido: {report_type}")

    def _session_summary(self, session: FederatedSession) -> Dict[str, Any]:
        """Generar resumen de sesión."""
        return {
            "session_id": session.session_id,
            "model_name": session.model_name,
            "status": session.status.value,
            "progress": f"{session.current_round}/{session.total_rounds}",
            "accuracy": round(session.global_accuracy, 4),
            "participants": len(session.participants),
            "duration": round((asyncio.get_event_loop().time() - session.start_time) / 60, 1)  # minutos
        }

    def _analyze_session_performance(self, session: FederatedSession) -> Dict[str, Any]:
        """Analizar performance de sesión."""
        contributions = [c for c in self.node_contributions if c.session_id == session.session_id]

        if not contributions:
            return {"error": "No hay contribuciones para analizar"}

        avg_accuracy = sum(c.local_accuracy for c in contributions) / len(contributions)
        avg_loss = sum(c.local_loss for c in contributions) / len(contributions)
        avg_training_time = sum(c.training_time for c in contributions) / len(contributions)
        total_samples = sum(c.samples_contributed for c in contributions)

        return {
            "average_node_accuracy": round(avg_accuracy, 4),
            "average_node_loss": round(avg_loss, 4),
            "average_training_time": round(avg_training_time, 2),
            "total_samples_processed": total_samples,
            "nodes_participating": len(set(c.node_id for c in contributions)),
            "communication_efficiency": round(total_samples / len(contributions), 2)
        }

    def _analyze_convergence(self, session_id: Optional[str]) -> Dict[str, Any]:
        """Analizar convergencia."""
        if not session_id or session_id not in self.active_sessions:
            return {}

        session = self.active_sessions[session_id]
        accuracy_history = session.metrics_history.get('accuracy', [])
        loss_history = session.metrics_history.get('loss', [])

        if len(accuracy_history) < 3:
            return {"error": "Insuficientes datos para análisis de convergencia"}

        # Calcular tasa de convergencia
        recent_accuracy = accuracy_history[-3:]
        convergence_rate = (recent_accuracy[-1] - recent_accuracy[0]) / len(recent_accuracy)

        # Calcular estabilidad (varianza)
        accuracy_variance = sum((x - sum(recent_accuracy)/len(recent_accuracy))**2 for x in recent_accuracy) / len(recent_accuracy)

        return {
            "convergence_rate": round(convergence_rate, 6),
            "stability_score": round(1.0 - min(1.0, accuracy_variance * 100), 4),
            "accuracy_trend": "improving" if convergence_rate > 0.001 else "stable" if convergence_rate > -0.001 else "declining",
            "rounds_to_convergence": max(0, session.total_rounds - session.current_round) if convergence_rate > 0 else -1
        }

    def _generate_session_summary(self, session: FederatedSession) -> str:
        """Generar resumen de sesión."""
        duration = (asyncio.get_event_loop().time() - session.start_time) / 60  # minutos
        progress = (session.current_round / session.total_rounds) * 100

        return f"""
        RESUMEN DE SESIÓN FEDERADA - {session.session_id}

        Modelo: {session.model_name} ({session.model_type.value})
        Estado: {session.status.value.upper()}
        Progreso: {session.current_round}/{session.total_rounds} rondas ({progress:.1f}%)

        Rendimiento:
        • Accuracy Global: {session.global_accuracy:.4f}
        • Loss Global: {session.global_loss:.4f}
        • Participantes: {len(session.participants)}
        • Dataset: {session.dataset_size:,} muestras

        Configuración:
        • Batch Size: {session.batch_size}
        • Learning Rate: {session.learning_rate}
        • Optimizer: {session.optimizer}

        Duración: {duration:.1f} minutos
        """

    def _generate_federated_overview_summary(self) -> str:
        """Generar resumen general de FL."""
        return f"""
        RESUMEN GENERAL - FEDERATED LEARNING

        SESIONES ACTIVAS: {self.federated_metrics.active_sessions}
        PARTICIPANTES ACTIVOS: {self.federated_metrics.active_participants}
        MODELOS DESPLEGADOS: {self.federated_metrics.models_deployed}

        MÉTRICAS DE RENDIMIENTO:
        • Accuracy Promedio: {self.federated_metrics.average_accuracy:.4f}
        • Mejor Accuracy: {self.federated_metrics.best_accuracy:.4f}
        • Tasa de Convergencia: {self.federated_metrics.convergence_rate:.4f}
        • Eficiencia de Comunicación: {self.federated_metrics.communication_efficiency:.4f}

        ESTADO GENERAL:
        • Sesiones Completadas: {self.federated_metrics.completed_sessions}
        • Sesiones Fallidas: {self.federated_metrics.failed_sessions}
        • Datos Procesados: {self.federated_metrics.total_data_processed:.2f} GB
        """

    def _generate_convergence_summary(self, session_id: Optional[str]) -> str:
        """Generar resumen de convergencia."""
        if not session_id:
            return "Análisis de convergencia requiere ID de sesión"

        convergence_data = self._analyze_convergence(session_id)
        if "error" in convergence_data:
            return f"Error en análisis: {convergence_data['error']}"

        return f"""
        ANÁLISIS DE CONVERGENCIA - {session_id}

        Tasa de Convergencia: {convergence_data['convergence_rate']}
        Puntaje de Estabilidad: {convergence_data['stability_score']:.4f}
        Tendencia: {convergence_data['accuracy_trend'].upper()}

        Rondas Restantes Estimadas: {convergence_data['rounds_to_convergence']}
        """

    def register_update_callback(self, callback: Callable):
        """Registrar callback para actualizaciones."""
        self.update_callbacks.append(callback)

    def register_session_callback(self, callback: Callable):
        """Registrar callback para sesiones."""
        self.session_callbacks.append(callback)


# Función de conveniencia
def create_federated_learning_dashboard(federated_coordinator: Optional[FederatedCoordinator] = None,
                                       data_coordinator: Optional[FederatedDataCoordinator] = None) -> FederatedLearningDashboard:
    """Crear instancia del dashboard FL."""
    return FederatedLearningDashboard(federated_coordinator=federated_coordinator, data_coordinator=data_coordinator)


# Función para iniciar dashboard FL
async def start_federated_learning_dashboard(federated_coordinator: Optional[FederatedCoordinator] = None,
                                           data_coordinator: Optional[FederatedDataCoordinator] = None):
    """Función de conveniencia para iniciar el dashboard FL."""
    dashboard = create_federated_learning_dashboard(federated_coordinator, data_coordinator)
    await dashboard.start_monitoring()
    return dashboard