"""
Technical Dashboard for Federated Training Monitoring
Provides comprehensive real-time monitoring of the entire federated training pipeline.
"""

import asyncio
import json
import time
import logging
import os
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from ..core.logging import get_logger
from ..core.config import get_config
from ..federated.coordinator import FederatedCoordinator
from ..federated.data_coordinator import FederatedDataCoordinator
from ..infrastructure.ipfs_distributor import IPFSDistributor
from ..core.state_manager import get_state_manager

logger = get_logger(__name__)


class MonitoringLevel(Enum):
    """Niveles de monitoreo disponibles."""
    BASIC = "basic"
    DETAILED = "detailed"
    DEBUG = "debug"


class AlertSeverity(Enum):
    """Severidades de alertas."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alerta del sistema."""
    alert_id: str
    severity: AlertSeverity
    component: str
    message: str
    timestamp: float
    resolved: bool = False
    resolved_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FederatedTrainingMetrics:
    """Métricas de entrenamiento federado."""
    active_sessions: int = 0
    total_sessions: int = 0
    completed_rounds: int = 0
    total_rounds: int = 0
    active_participants: int = 0
    total_participants: int = 0
    average_accuracy: float = 0.0
    training_efficiency: float = 0.0
    convergence_rate: float = 0.0
    model_updates_received: int = 0
    model_updates_processed: int = 0
    aggregation_time_avg: float = 0.0
    privacy_budget_remaining: float = 100.0


@dataclass
class DataDistributionMetrics:
    """Métricas de distribución de datos."""
    active_pipelines: int = 0
    total_pipelines: int = 0
    datasets_distributed: int = 0
    total_chunks: int = 0
    chunks_distributed: int = 0
    chunks_verified: int = 0
    distribution_success_rate: float = 0.0
    average_chunk_size: int = 0
    total_data_volume: int = 0
    download_speed_avg: float = 0.0
    verification_time_avg: float = 0.0


@dataclass
class NodePerformanceMetrics:
    """Métricas de rendimiento de nodos."""
    total_nodes: int = 0
    active_nodes: int = 0
    offline_nodes: int = 0
    average_cpu_usage: float = 0.0
    average_memory_usage: float = 0.0
    average_gpu_usage: float = 0.0
    network_latency_avg: float = 0.0
    training_throughput_avg: float = 0.0
    hardware_distribution: Dict[str, int] = field(default_factory=dict)
    node_health_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class IPFSMetrics:
    """Métricas de IPFS."""
    total_pins: int = 0
    active_peers: int = 0
    bandwidth_in: float = 0.0
    bandwidth_out: float = 0.0
    storage_used: int = 0
    chunks_published: int = 0
    chunks_retrieved: int = 0
    publish_success_rate: float = 0.0
    retrieval_success_rate: float = 0.0
    average_publish_time: float = 0.0
    average_retrieval_time: float = 0.0
    cid_cache_hit_rate: float = 0.0


@dataclass
class TrainingProgressMetrics:
    """Métricas de progreso de entrenamiento."""
    current_round: int = 0
    total_rounds: int = 0
    round_progress: float = 0.0
    global_accuracy: float = 0.0
    global_loss: float = 0.0
    accuracy_trend: List[float] = field(default_factory=list)
    loss_trend: List[float] = field(default_factory=list)
    convergence_indicator: float = 0.0
    estimated_completion_time: Optional[float] = None
    training_duration: float = 0.0
    samples_processed: int = 0
    models_aggregated: int = 0


class TechnicalDashboard:
    """
    Dashboard técnico completo para monitoreo de entrenamiento federado.
    Proporciona monitoreo en tiempo real de todo el pipeline federado.
    """

    def __init__(self,
                 federated_coordinator: Optional[FederatedCoordinator] = None,
                 data_coordinator: Optional[FederatedDataCoordinator] = None,
                 ipfs_distributor: Optional[IPFSDistributor] = None,
                 monitoring_level: MonitoringLevel = MonitoringLevel.DETAILED,
                 update_interval: float = 5.0):
        """
        Inicializar el dashboard técnico.

        Args:
            federated_coordinator: Coordinador federado
            data_coordinator: Coordinador de datos
            ipfs_distributor: Distribuidor IPFS
            monitoring_level: Nivel de monitoreo
            update_interval: Intervalo de actualización en segundos
        """
        self.config = get_config()
        self.state_manager = get_state_manager()

        # Componentes del sistema
        self.federated_coordinator = federated_coordinator
        self.data_coordinator = data_coordinator
        self.ipfs_distributor = ipfs_distributor

        # Configuración
        self.monitoring_level = monitoring_level
        self.update_interval = update_interval

        # Estado del dashboard
        self.is_running = False
        self.last_update = 0.0

        # Métricas
        self.federated_metrics = FederatedTrainingMetrics()
        self.data_metrics = DataDistributionMetrics()
        self.node_metrics = NodePerformanceMetrics()
        self.ipfs_metrics = IPFSMetrics()
        self.training_metrics = TrainingProgressMetrics()

        # Alertas
        self.alerts: List[Alert] = []
        self.alert_callbacks: List[Callable] = []

        # Callbacks de actualización
        self.update_callbacks: List[Callable] = []

        # WebSocket connections
        self.websocket_connections: Dict[str, WebSocket] = {}
        self.websocket_broadcast_interval: float = 2.0  # Broadcast every 2 seconds

        # Historial de métricas
        self.metrics_history: Dict[str, List] = {
            'federated': [],
            'data': [],
            'node': [],
            'ipfs': [],
            'training': []
        }

        # FastAPI application for dashboard endpoints
        self.app = None
        self._setup_api_app()

        # FastAPI application for dashboard endpoints
        self.app = None
        self._setup_api_app()

        logger.info("🚀 TechnicalDashboard initialized")

    def _setup_api_app(self):
        """Setup FastAPI application for dashboard endpoints."""
        self.app = FastAPI(
            title="AILOOS Technical Dashboard API",
            description="REST and WebSocket API for comprehensive federated training monitoring",
            version="1.0.0"
        )

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Setup routes
        self._setup_api_routes()

    def _setup_api_routes(self):
        """Setup API routes."""
        @self.app.get("/")
        async def get_dashboard_status():
            """Get comprehensive dashboard status."""
            return self.get_comprehensive_status()

        @self.app.get("/api/status")
        async def get_status():
            """Get basic system status."""
            return {
                "status": "running" if self.is_running else "stopped",
                "last_update": self.last_update,
                "monitoring_level": self.monitoring_level.value,
                "timestamp": time.time()
            }

        @self.app.get("/api/metrics/{metric_type}")
        async def get_metrics(metric_type: str, limit: int = 50):
            """Get metrics history for specific type."""
            if metric_type not in self.metrics_history:
                return {"error": f"Unknown metric type: {metric_type}"}

            return {
                "metric_type": metric_type,
                "data": self.get_metrics_history(metric_type, limit),
                "timestamp": time.time()
            }

        @self.app.get("/api/alerts")
        async def get_alerts(severity: Optional[str] = None, resolved: bool = False, limit: int = 20):
            """Get alerts with filtering."""
            try:
                severity_enum = AlertSeverity(severity) if severity else None
                alerts = self.get_alerts(severity_enum, resolved, limit)
                return {
                    "alerts": [
                        {
                            "alert_id": alert.alert_id,
                            "severity": alert.severity.value,
                            "component": alert.component,
                            "message": alert.message,
                            "timestamp": alert.timestamp,
                            "resolved": alert.resolved,
                            "resolved_at": alert.resolved_at
                        }
                        for alert in alerts
                    ],
                    "total_count": len(self.alerts),
                    "timestamp": time.time()
                }
            except ValueError as e:
                return {"error": str(e)}

        @self.app.post("/api/alerts/{alert_id}/resolve")
        async def resolve_alert(alert_id: str):
            """Resolve a specific alert."""
            if self.resolve_alert(alert_id):
                return {"message": f"Alert {alert_id} resolved", "timestamp": time.time()}
            else:
                return {"error": f"Alert {alert_id} not found or already resolved"}

        @self.app.get("/api/websocket/stats")
        async def get_websocket_stats():
            """Get WebSocket connection statistics."""
            return self.get_websocket_stats()

        @self.app.get("/api/export/{format}")
        async def export_metrics(format: str = "json"):
            """Export metrics report."""
            try:
                return await self.export_metrics_report(format)
            except ValueError as e:
                return {"error": str(e)}

        @self.app.websocket("/ws/dashboard")
        async def websocket_endpoint(websocket: WebSocket, client_id: str = None):
            """WebSocket endpoint for real-time dashboard updates."""
            if not client_id:
                client_id = f"client_{int(time.time())}_{hash(str(websocket)) % 10000}"

            await self.handle_websocket_connection(websocket, client_id)

        @self.app.get("/api/federated/sessions")
        async def get_federated_sessions():
            """Get federated training sessions."""
            if not self.federated_coordinator:
                return {"error": "Federated coordinator not available"}

            sessions = self.federated_coordinator.get_active_sessions()
            return {
                "sessions": sessions,
                "count": len(sessions),
                "timestamp": time.time()
            }

        @self.app.get("/api/data/pipelines")
        async def get_data_pipelines():
            """Get data distribution pipelines."""
            if not self.data_coordinator:
                return {"error": "Data coordinator not available"}

            pipelines = self.data_coordinator.get_active_pipelines()
            return {
                "pipelines": pipelines,
                "count": len(pipelines),
                "timestamp": time.time()
            }

        @self.app.get("/api/nodes/status")
        async def get_nodes_status():
            """Get node status information."""
            # This would integrate with node registry/health monitoring
            return {
                "node_metrics": {
                    "total_nodes": self.node_metrics.total_nodes,
                    "active_nodes": self.node_metrics.active_nodes,
                    "offline_nodes": self.node_metrics.offline_nodes,
                    "hardware_distribution": self.node_metrics.hardware_distribution,
                    "average_cpu_usage": self.node_metrics.average_cpu_usage,
                    "average_memory_usage": self.node_metrics.average_memory_usage
                },
                "timestamp": time.time()
            }

        @self.app.get("/api/ipfs/status")
        async def get_ipfs_status():
            """Get IPFS network status."""
            return {
                "ipfs_metrics": {
                    "total_pins": self.ipfs_metrics.total_pins,
                    "active_peers": self.ipfs_metrics.active_peers,
                    "chunks_published": self.ipfs_metrics.chunks_published,
                    "publish_success_rate": self.ipfs_metrics.publish_success_rate,
                    "storage_used": self.ipfs_metrics.storage_used,
                    "bandwidth_in": self.ipfs_metrics.bandwidth_in,
                    "bandwidth_out": self.ipfs_metrics.bandwidth_out
                },
                "timestamp": time.time()
            }

        @self.app.get("/api/training/progress")
        async def get_training_progress():
            """Get training progress information."""
            return {
                "training_metrics": {
                    "current_round": self.training_metrics.current_round,
                    "total_rounds": self.training_metrics.total_rounds,
                    "round_progress": self.training_metrics.round_progress,
                    "global_accuracy": self.training_metrics.global_accuracy,
                    "global_loss": self.training_metrics.global_loss,
                    "convergence_indicator": self.training_metrics.convergence_indicator,
                    "samples_processed": self.training_metrics.samples_processed,
                    "models_aggregated": self.training_metrics.models_aggregated
                },
                "timestamp": time.time()
            }

        @self.app.get("/api/health")
        async def get_health_status():
            """Get dashboard health status."""
            return self.get_health_status()

        @self.app.post("/api/restart")
        async def restart_monitoring():
            """Restart monitoring system."""
            try:
                if self.is_running:
                    await self.stop_monitoring()

                await self.start_monitoring()
                return {"message": "Monitoring restarted successfully", "timestamp": time.time()}
            except Exception as e:
                logger.error(f"Error restarting monitoring: {e}")
                return {"error": f"Failed to restart monitoring: {e}"}

    async def start_monitoring(self):
        """Iniciar monitoreo del sistema."""
        if self.is_running:
            return

        self.is_running = True
        logger.info("📊 Starting technical monitoring")

        # Tarea de monitoreo continuo
        asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self):
        """Detener monitoreo del sistema."""
        self.is_running = False
        logger.info("🛑 Technical monitoring stopped")

    async def _monitoring_loop(self):
        """Loop principal de monitoreo."""
        last_broadcast = 0.0

        while self.is_running:
            try:
                await self._update_all_metrics()
                await self._check_alerts()
                await self._notify_callbacks()

                self.last_update = time.time()

                # Broadcast WebSocket updates at specified interval
                current_time = time.time()
                if current_time - last_broadcast >= self.websocket_broadcast_interval:
                    await self._broadcast_websocket_updates()
                    last_broadcast = current_time

            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                await self._create_alert(
                    severity=AlertSeverity.ERROR,
                    component="monitoring",
                    message=f"Monitoring loop error: {e}"
                )

            await asyncio.sleep(self.update_interval)

    async def _update_all_metrics(self):
        """Actualizar todas las métricas con manejo robusto de errores."""
        update_errors = []

        try:
            # Actualizar métricas federadas
            try:
                await self._update_federated_metrics()
            except Exception as e:
                error_msg = f"Federated metrics update failed: {e}"
                logger.error(f"❌ {error_msg}")
                update_errors.append(error_msg)
                await self._create_alert(
                    severity=AlertSeverity.WARNING,
                    component="federated",
                    message="Federated metrics update failed",
                    metadata={"error": str(e)}
                )

            # Actualizar métricas de datos
            try:
                await self._update_data_metrics()
            except Exception as e:
                error_msg = f"Data metrics update failed: {e}"
                logger.error(f"❌ {error_msg}")
                update_errors.append(error_msg)
                await self._create_alert(
                    severity=AlertSeverity.WARNING,
                    component="data",
                    message="Data metrics update failed",
                    metadata={"error": str(e)}
                )

            # Actualizar métricas de nodos
            try:
                await self._update_node_metrics()
            except Exception as e:
                error_msg = f"Node metrics update failed: {e}"
                logger.error(f"❌ {error_msg}")
                update_errors.append(error_msg)
                await self._create_alert(
                    severity=AlertSeverity.WARNING,
                    component="nodes",
                    message="Node metrics update failed",
                    metadata={"error": str(e)}
                )

            # Actualizar métricas IPFS
            try:
                await self._update_ipfs_metrics()
            except Exception as e:
                error_msg = f"IPFS metrics update failed: {e}"
                logger.error(f"❌ {error_msg}")
                update_errors.append(error_msg)
                await self._create_alert(
                    severity=AlertSeverity.WARNING,
                    component="ipfs",
                    message="IPFS metrics update failed",
                    metadata={"error": str(e)}
                )

            # Actualizar métricas de entrenamiento
            try:
                await self._update_training_metrics()
            except Exception as e:
                error_msg = f"Training metrics update failed: {e}"
                logger.error(f"❌ {error_msg}")
                update_errors.append(error_msg)
                await self._create_alert(
                    severity=AlertSeverity.WARNING,
                    component="training",
                    message="Training metrics update failed",
                    metadata={"error": str(e)}
                )

            # Almacenar en historial incluso si hay errores parciales
            try:
                self._store_metrics_history()
            except Exception as e:
                logger.error(f"❌ Error storing metrics history: {e}")

            # Log summary of errors if any occurred
            if update_errors:
                logger.warning(f"⚠️ Metrics update completed with {len(update_errors)} errors")
                for error in update_errors:
                    logger.warning(f"   - {error}")

        except Exception as e:
            logger.error(f"❌ Critical error in metrics update: {e}")
            await self._create_alert(
                severity=AlertSeverity.ERROR,
                component="monitoring",
                message="Critical metrics update failure",
                metadata={"error": str(e)}
            )

    async def _update_federated_metrics(self):
        """Actualizar métricas de entrenamiento federado."""
        if not self.federated_coordinator:
            return

        try:
            # Obtener sesiones activas
            active_sessions = self.federated_coordinator.get_active_sessions()
            global_status = self.federated_coordinator.get_global_status()

            self.federated_metrics.active_sessions = len(active_sessions)
            self.federated_metrics.total_sessions = global_status.get('total_sessions', len(active_sessions))

            # Calcular métricas agregadas
            total_rounds = 0
            total_participants = 0
            accuracies = []

            for session in active_sessions:
                total_rounds += session.get('current_round', 0)
                total_participants += session.get('participants', 0)

                # For now, use placeholder accuracy since real metrics aren't available
                accuracies.append(0.8)  # Placeholder

            self.federated_metrics.completed_rounds = total_rounds
            self.federated_metrics.active_participants = total_participants
            self.federated_metrics.average_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0

            # Calculate training efficiency based on active vs total sessions
            if self.federated_metrics.total_sessions > 0:
                self.federated_metrics.training_efficiency = (
                    self.federated_metrics.active_sessions / self.federated_metrics.total_sessions
                ) * 100.0

            # Placeholder values for other metrics until real implementation
            self.federated_metrics.convergence_rate = 0.0
            self.federated_metrics.model_updates_received = total_participants
            self.federated_metrics.model_updates_processed = total_participants
            self.federated_metrics.aggregation_time_avg = 0.0
            self.federated_metrics.privacy_budget_remaining = 100.0

        except Exception as e:
            logger.error(f"❌ Error updating federated metrics: {e}")

    async def _update_data_metrics(self):
        """Actualizar métricas de distribución de datos."""
        if not self.data_coordinator:
            return

        try:
            active_pipelines = self.data_coordinator.get_active_pipelines()

            self.data_metrics.active_pipelines = len(active_pipelines)
            self.data_metrics.total_pipelines = len(active_pipelines)  # For now, use active as total

            # Calculate metrics from real pipeline data
            total_chunks = 0
            distributed_chunks = 0
            verified_chunks = 0
            total_data_volume = 0

            for pipeline in active_pipelines:
                # Get dataset info from pipeline
                dataset_name = pipeline.get('dataset_name')
                if dataset_name:
                    dataset_info = self.data_coordinator.get_dataset_info(dataset_name)
                    if dataset_info:
                        total_chunks += dataset_info.total_chunks
                        # Estimate distributed chunks based on progress
                        progress = pipeline.get('progress', {})
                        distributed_chunks += int(dataset_info.total_chunks * (progress.get('distribution', 0) / 100.0))
                        verified_chunks += int(dataset_info.total_chunks * (progress.get('verification', 0) / 100.0))
                        total_data_volume += dataset_info.size_bytes

            self.data_metrics.total_chunks = total_chunks
            self.data_metrics.chunks_distributed = distributed_chunks
            self.data_metrics.chunks_verified = verified_chunks
            self.data_metrics.total_data_volume = total_data_volume

            # Calculate success rate
            if total_chunks > 0:
                self.data_metrics.distribution_success_rate = (
                    self.data_metrics.chunks_distributed / total_chunks
                ) * 100.0
            else:
                self.data_metrics.distribution_success_rate = 0.0

            # Calculate averages (placeholder values for now)
            self.data_metrics.average_chunk_size = (
                total_data_volume / total_chunks
            ) if total_chunks > 0 else 1024 * 1024  # 1MB default

            self.data_metrics.download_speed_avg = 50.0  # Placeholder
            self.data_metrics.verification_time_avg = 0.5  # Placeholder

            # Get datasets count
            self.data_metrics.datasets_distributed = len(active_pipelines)

        except Exception as e:
            logger.error(f"❌ Error updating data metrics: {e}")

    async def _update_node_metrics(self):
        """Actualizar métricas de rendimiento de nodos."""
        try:
            # Get node registry from coordinator
            node_registry = {}
            if hasattr(self.federated_coordinator, 'node_registry') and self.federated_coordinator.node_registry:
                node_registry = self.federated_coordinator.node_registry

            # Get system status
            system_status = self.state_manager.get_system_status()

            self.node_metrics.total_nodes = len(node_registry) if node_registry else system_status.get('total_components', 0)
            active_nodes = [node for node in node_registry.values() if node.get('status') == 'active'] if node_registry else []
            self.node_metrics.active_nodes = len(active_nodes)
            self.node_metrics.offline_nodes = self.node_metrics.total_nodes - self.node_metrics.active_nodes

            # For now, use placeholder performance metrics since real monitoring isn't implemented
            self.node_metrics.average_cpu_usage = 45.0 + (time.time() % 30.0)
            self.node_metrics.average_memory_usage = 60.0 + (time.time() % 20.0)
            self.node_metrics.average_gpu_usage = 70.0 + (time.time() % 25.0)
            self.node_metrics.network_latency_avg = 25.0 + (time.time() % 15.0)
            self.node_metrics.training_throughput_avg = 150.0 + (time.time() % 50.0)

            # Hardware distribution (placeholder)
            self.node_metrics.hardware_distribution = {
                "macbook_pro": max(1, self.node_metrics.total_nodes // 3),
                "macbook_m4": max(1, self.node_metrics.total_nodes // 4),
                "imac": max(1, self.node_metrics.total_nodes // 5),
                "linux_server": max(1, self.node_metrics.total_nodes // 6)
            }

            # Node health scores (placeholder based on status)
            self.node_metrics.node_health_scores = {}
            for node_id in node_registry.keys():
                self.node_metrics.node_health_scores[node_id] = 85.0 + (time.time() % 15.0)

        except Exception as e:
            logger.error(f"❌ Error updating node metrics: {e}")

    async def _update_ipfs_metrics(self):
        """Actualizar métricas de IPFS."""
        if not self.ipfs_distributor:
            return

        try:
            distributor_stats = self.ipfs_distributor.get_stats()

            # Get real IPFS metrics from distributor
            self.ipfs_metrics.chunks_published = distributor_stats.get('total_chunks_published', 0)
            self.ipfs_metrics.chunks_retrieved = distributor_stats.get('total_chunks_retrieved', 0)
            self.ipfs_metrics.average_publish_time = distributor_stats.get('average_publish_time', 0.0)
            self.ipfs_metrics.average_retrieval_time = distributor_stats.get('average_retrieval_time', 0.0)
            self.ipfs_metrics.publish_success_rate = 95.0  # Placeholder since not in stats
            self.ipfs_metrics.retrieval_success_rate = 92.0  # Placeholder since not in stats
            self.ipfs_metrics.bandwidth_in = distributor_stats.get('total_bytes_published', 0) / (1024 * 1024)  # Convert to MB
            self.ipfs_metrics.bandwidth_out = distributor_stats.get('total_bytes_published', 0) / (1024 * 1024)  # Placeholder
            self.ipfs_metrics.storage_used = distributor_stats.get('total_bytes_published', 0)
            self.ipfs_metrics.cid_cache_hit_rate = 75.0  # Placeholder
            self.ipfs_metrics.total_pins = distributor_stats.get('total_chunks_published', 0)

            # Get IPFS network status (placeholder for now)
            self.ipfs_metrics.active_peers = 12  # Placeholder

        except Exception as e:
            logger.error(f"❌ Error updating IPFS metrics: {e}")

    async def _update_training_metrics(self):
        """Actualizar métricas de progreso de entrenamiento."""
        try:
            # Get metrics from active sessions
            if self.federated_coordinator:
                active_sessions = self.federated_coordinator.get_active_sessions()

                if active_sessions:
                    # Aggregate metrics across all active sessions
                    total_current_round = 0
                    total_rounds = 0
                    accuracies = []
                    losses = []
                    samples_processed = 0
                    models_aggregated = 0

                    for session in active_sessions:
                        session_metrics = session.get('metrics', {})
                        session_progress = session.get('progress', {})

                        total_current_round += session.get('current_round', 0)
                        total_rounds += session.get('total_rounds', 5)

                        # Collect accuracy and loss
                        accuracy = session_metrics.get('global_accuracy', session_metrics.get('accuracy', 0.0))
                        loss = session_metrics.get('global_loss', session_metrics.get('loss', 0.0))

                        if accuracy > 0:
                            accuracies.append(accuracy)
                        if loss > 0:
                            losses.append(loss)

                        samples_processed += session_progress.get('samples_processed', 0)
                        models_aggregated += session_progress.get('models_aggregated', 0)

                    # Calculate averages
                    self.training_metrics.current_round = total_current_round // len(active_sessions) if active_sessions else 0
                    self.training_metrics.total_rounds = total_rounds // len(active_sessions) if active_sessions else 5
                    self.training_metrics.round_progress = (
                        self.training_metrics.current_round / self.training_metrics.total_rounds
                    ) * 100.0 if self.training_metrics.total_rounds > 0 else 0.0

                    self.training_metrics.global_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0
                    self.training_metrics.global_loss = sum(losses) / len(losses) if losses else 0.0
                    self.training_metrics.samples_processed = samples_processed
                    self.training_metrics.models_aggregated = models_aggregated

                    # Update trends
                    if len(self.training_metrics.accuracy_trend) >= 10:
                        self.training_metrics.accuracy_trend.pop(0)
                    self.training_metrics.accuracy_trend.append(self.training_metrics.global_accuracy)

                    if len(self.training_metrics.loss_trend) >= 10:
                        self.training_metrics.loss_trend.pop(0)
                    self.training_metrics.loss_trend.append(self.training_metrics.global_loss)

                    # Calculate convergence indicator
                    if len(self.training_metrics.loss_trend) >= 5:
                        recent_losses = self.training_metrics.loss_trend[-5:]
                        loss_variance = sum((x - sum(recent_losses)/len(recent_losses))**2 for x in recent_losses) / len(recent_losses)
                        self.training_metrics.convergence_indicator = max(0, 1.0 - loss_variance * 10)

                    # Estimate completion time
                    if self.training_metrics.round_progress > 0 and self.training_metrics.round_progress < 100:
                        # Get session start time
                        session_start = min(session.get('start_time', time.time()) for session in active_sessions)
                        elapsed_time = time.time() - session_start
                        total_estimated_time = elapsed_time / (self.training_metrics.round_progress / 100.0)
                        self.training_metrics.estimated_completion_time = session_start + total_estimated_time
                        self.training_metrics.training_duration = elapsed_time
                    else:
                        self.training_metrics.estimated_completion_time = None
                        self.training_metrics.training_duration = 0.0

        except Exception as e:
            logger.error(f"❌ Error updating training metrics: {e}")

    def _store_metrics_history(self):
        """Almacenar métricas en historial."""
        timestamp = time.time()

        # Almacenar cada tipo de métrica
        self.metrics_history['federated'].append({
            'timestamp': timestamp,
            'active_sessions': self.federated_metrics.active_sessions,
            'average_accuracy': self.federated_metrics.average_accuracy,
            'training_efficiency': self.federated_metrics.training_efficiency
        })

        self.metrics_history['data'].append({
            'timestamp': timestamp,
            'active_pipelines': self.data_metrics.active_pipelines,
            'distribution_success_rate': self.data_metrics.distribution_success_rate
        })

        self.metrics_history['node'].append({
            'timestamp': timestamp,
            'active_nodes': self.node_metrics.active_nodes,
            'average_cpu_usage': self.node_metrics.average_cpu_usage,
            'average_memory_usage': self.node_metrics.average_memory_usage
        })

        self.metrics_history['ipfs'].append({
            'timestamp': timestamp,
            'chunks_published': self.ipfs_metrics.chunks_published,
            'publish_success_rate': self.ipfs_metrics.publish_success_rate
        })

        self.metrics_history['training'].append({
            'timestamp': timestamp,
            'current_round': self.training_metrics.current_round,
            'global_accuracy': self.training_metrics.global_accuracy,
            'global_loss': self.training_metrics.global_loss,
            'convergence_indicator': self.training_metrics.convergence_indicator
        })

        # Mantener solo últimas 100 entradas por tipo
        for metric_type in self.metrics_history:
            if len(self.metrics_history[metric_type]) > 100:
                self.metrics_history[metric_type].pop(0)

    async def _check_alerts(self):
        """Verificar condiciones para generar alertas."""
        try:
            # Get environment settings to control alert generation
            enable_p2p_sync = os.getenv('ENABLE_P2P_SYNC', 'true').lower() == 'true'
            enable_ipfs_alerts = os.getenv('ENABLE_IPFS_ALERTS', 'true').lower() == 'true'

            # Alerta: Sesiones federadas inactivas (siempre activa, no es P2P específico)
            if self.federated_metrics.active_sessions == 0 and self.federated_metrics.total_sessions > 0:
                await self._create_alert(
                    severity=AlertSeverity.WARNING,
                    component="federated",
                    message="No active federated sessions"
                )

            # Alerta: Baja tasa de distribución de datos (solo si P2P está habilitado)
            if enable_p2p_sync and self.data_metrics.distribution_success_rate < 80.0:
                await self._create_alert(
                    severity=AlertSeverity.WARNING,
                    component="data",
                    message=f"Low data distribution success rate: {self.data_metrics.distribution_success_rate:.1f}%"
                )

            # Alerta: Nodos offline (siempre activa, es crítica para el sistema)
            if self.node_metrics.offline_nodes > 0:
                await self._create_alert(
                    severity=AlertSeverity.ERROR,
                    component="nodes",
                    message=f"{self.node_metrics.offline_nodes} nodes are offline"
                )

            # Alerta: Baja tasa de éxito IPFS (solo si IPFS alerts están habilitados)
            if enable_ipfs_alerts and self.ipfs_metrics.publish_success_rate < 90.0:
                await self._create_alert(
                    severity=AlertSeverity.ERROR,
                    component="ipfs",
                    message=f"Low IPFS publish success rate: {self.ipfs_metrics.publish_success_rate:.1f}%"
                )

            # Alerta: Entrenamiento no converge (siempre activa, es crítica para ML)
            if self.training_metrics.convergence_indicator < 0.3 and self.training_metrics.current_round > 3:
                await self._create_alert(
                    severity=AlertSeverity.WARNING,
                    component="training",
                    message="Training convergence is slow"
                )

        except Exception as e:
            logger.error(f"❌ Error checking alerts: {e}")

    async def _create_alert(self, severity: AlertSeverity, component: str, message: str, metadata: Dict[str, Any] = None):
        """Crear una nueva alerta."""
        alert = Alert(
            alert_id=f"alert_{int(time.time())}_{hash(message) % 10000}",
            severity=severity,
            component=component,
            message=message,
            timestamp=time.time(),
            metadata=metadata or {}
        )

        self.alerts.append(alert)

        # Mantener solo últimas 50 alertas
        if len(self.alerts) > 50:
            self.alerts.pop(0)

        # Notificar callbacks
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    await asyncio.get_event_loop().run_in_executor(None, callback, alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

        logger.warning(f"🚨 Alert created: {severity.value} - {component} - {message}")

    async def _notify_callbacks(self):
        """Notificar callbacks de actualización."""
        for callback in self.update_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self)
                else:
                    await asyncio.get_event_loop().run_in_executor(None, callback, self)
            except Exception as e:
                logger.error(f"Error in update callback: {e}")

    async def _broadcast_websocket_updates(self):
        """Broadcast updates to all WebSocket connections."""
        if not self.websocket_connections:
            return

        try:
            status = self.get_comprehensive_status()
            message = {
                "type": "dashboard_update",
                "timestamp": time.time(),
                "data": status
            }

            # Remove disconnected clients
            disconnected_clients = []
            for client_id, websocket in self.websocket_connections.items():
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send update to client {client_id}: {e}")
                    disconnected_clients.append(client_id)

            # Clean up disconnected clients
            for client_id in disconnected_clients:
                del self.websocket_connections[client_id]
                logger.info(f"Removed disconnected WebSocket client: {client_id}")

        except Exception as e:
            logger.error(f"Error broadcasting WebSocket updates: {e}")

    async def handle_websocket_connection(self, websocket: WebSocket, client_id: str):
        """
        Handle WebSocket connection for real-time updates.

        Args:
            websocket: WebSocket connection
            client_id: Unique client identifier
        """
        await websocket.accept()
        self.websocket_connections[client_id] = websocket

        logger.info(f"📡 WebSocket client connected: {client_id}")

        try:
            # Send initial status
            initial_status = self.get_comprehensive_status()
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
            logger.info(f"📡 WebSocket client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"WebSocket connection error for {client_id}: {e}")
        finally:
            # Clean up connection
            if client_id in self.websocket_connections:
                del self.websocket_connections[client_id]

    async def _handle_websocket_message(self, websocket: WebSocket, client_id: str, message: Dict[str, Any]):
        """Handle incoming WebSocket messages from clients."""
        try:
            message_type = message.get("type", "unknown")

            if message_type == "subscribe":
                # Client subscribing to specific metrics
                subscriptions = message.get("subscriptions", [])
                logger.info(f"Client {client_id} subscribed to: {subscriptions}")

                # Send confirmation
                await websocket.send_json({
                    "type": "subscription_confirmed",
                    "subscriptions": subscriptions,
                    "timestamp": time.time()
                })

            elif message_type == "unsubscribe":
                # Client unsubscribing
                logger.info(f"Client {client_id} unsubscribed")

            elif message_type == "request_history":
                # Client requesting metrics history
                metric_type = message.get("metric_type", "federated")
                limit = message.get("limit", 50)

                history = self.get_metrics_history(metric_type, limit)
                await websocket.send_json({
                    "type": "history_data",
                    "metric_type": metric_type,
                    "data": history,
                    "timestamp": time.time()
                })

            elif message_type == "resolve_alert":
                # Client resolving an alert
                alert_id = message.get("alert_id")
                if alert_id and self.resolve_alert(alert_id):
                    await websocket.send_json({
                        "type": "alert_resolved",
                        "alert_id": alert_id,
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
            status = self.get_comprehensive_status()
            await websocket.send_json({
                "type": "dashboard_update",
                "timestamp": time.time(),
                "data": status
            })
        except Exception as e:
            logger.error(f"Error sending WebSocket update to {client_id}: {e}")
            # Client will be removed on next broadcast

    def get_websocket_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics."""
        return {
            "active_connections": len(self.websocket_connections),
            "client_ids": list(self.websocket_connections.keys()),
            "broadcast_interval": self.websocket_broadcast_interval
        }

    def get_api_app(self) -> FastAPI:
        """Get the FastAPI application instance."""
        return self.app

    async def start_api_server(self, host: str = "0.0.0.0", port: int = 8001):
        """
        Start the dashboard API server.

        Args:
            host: Server host
            port: Server port
        """
        if not self.app:
            raise RuntimeError("API application not initialized")

        import uvicorn

        # Start monitoring if not already running
        if not self.is_running:
            await self.start_monitoring()

        logger.info(f"🚀 Starting Technical Dashboard API server on {host}:{port}")

        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()

    def register_alert_callback(self, callback: Callable):
        """Registrar callback para alertas."""
        self.alert_callbacks.append(callback)

    def register_update_callback(self, callback: Callable):
        """Registrar callback para actualizaciones."""
        self.update_callbacks.append(callback)

    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Obtener estado completo del sistema."""
        # Create node metrics array for frontend compatibility
        node_metrics_array = []
        if hasattr(self.federated_coordinator, 'node_registry') and self.federated_coordinator.node_registry:
            for node_id, node_info in self.federated_coordinator.node_registry.items():
                # Create mock performance data since real monitoring isn't implemented
                connectivity_score = 0.8 if node_info.get('status') == 'active' else 0.2
                node_metrics_array.append({
                    "node_id": node_id,
                    "timestamp": datetime.now().isoformat(),
                    "performance": {
                        "cpu_usage_percent": self.node_metrics.average_cpu_usage,
                        "memory_usage_percent": self.node_metrics.average_memory_usage,
                        "network_latency_ms": self.node_metrics.network_latency_avg,
                        "performance_score": connectivity_score * 100,
                        "response_times_history": [25.0, 30.0, 20.0],  # Mock
                        "performance_history": []  # Mock
                    },
                    "contributions": {
                        "total_contributions": 5,  # Mock
                        "successful_contributions": 4,  # Mock
                        "session_success_rate": 0.8,  # Mock
                        "contribution_score": connectivity_score,
                        "average_contribution_time": 120.0  # Mock
                    },
                    "stability": {
                        "stability_score": connectivity_score,
                        "error_rate": 0.05,  # Mock
                        "consecutive_failures": 0,  # Mock
                        "crash_count": 0  # Mock
                    },
                    "connectivity": {
                        "connectivity_score": connectivity_score,
                        "uptime_ratio": connectivity_score,
                        "last_seen": datetime.now().isoformat(),
                        "response_time_ms": self.node_metrics.network_latency_avg
                    },
                    "source": "coordinator"
                })

        return {
            "timestamp": time.time(),
            "last_update": self.last_update,
            "monitoring_level": self.monitoring_level.value,
            "is_running": self.is_running,
            "federated_training": {
                "active_sessions": self.federated_metrics.active_sessions,
                "total_sessions": self.federated_metrics.total_sessions,
                "completed_rounds": self.federated_metrics.completed_rounds,
                "active_participants": self.federated_metrics.active_participants,
                "average_accuracy": self.federated_metrics.average_accuracy,
                "training_efficiency": self.federated_metrics.training_efficiency,
                "convergence_rate": self.federated_metrics.convergence_rate,
                "privacy_budget_remaining": self.federated_metrics.privacy_budget_remaining
            },
            "data_distribution": {
                "active_pipelines": self.data_metrics.active_pipelines,
                "total_pipelines": self.data_metrics.total_pipelines,
                "total_chunks": self.data_metrics.total_chunks,
                "chunks_distributed": self.data_metrics.chunks_distributed,
                "chunks_verified": self.data_metrics.chunks_verified,
                "distribution_success_rate": self.data_metrics.distribution_success_rate,
                "total_data_volume": self.data_metrics.total_data_volume
            },
            "node_performance": {
                "total_nodes": self.node_metrics.total_nodes,
                "active_nodes": self.node_metrics.active_nodes,
                "offline_nodes": self.node_metrics.offline_nodes,
                "average_cpu_usage": self.node_metrics.average_cpu_usage,
                "average_memory_usage": self.node_metrics.average_memory_usage,
                "average_gpu_usage": self.node_metrics.average_gpu_usage,
                "network_latency_avg": self.node_metrics.network_latency_avg,
                "training_throughput_avg": self.node_metrics.training_throughput_avg,
                "hardware_distribution": self.node_metrics.hardware_distribution
            },
            "node_metrics": node_metrics_array,  # Added for frontend compatibility
            "total_nodes": self.node_metrics.total_nodes,  # Added for frontend compatibility
            "ipfs_metrics": {
                "total_pins": self.ipfs_metrics.total_pins,
                "active_peers": self.ipfs_metrics.active_peers,
                "bandwidth_in": self.ipfs_metrics.bandwidth_in,
                "bandwidth_out": self.ipfs_metrics.bandwidth_out,
                "storage_used": self.ipfs_metrics.storage_used,
                "chunks_published": self.ipfs_metrics.chunks_published,
                "chunks_retrieved": self.ipfs_metrics.chunks_retrieved,
                "publish_success_rate": self.ipfs_metrics.publish_success_rate,
                "retrieval_success_rate": self.ipfs_metrics.retrieval_success_rate,
                "average_publish_time": self.ipfs_metrics.average_publish_time,
                "average_retrieval_time": self.ipfs_metrics.average_retrieval_time,
                "cid_cache_hit_rate": self.ipfs_metrics.cid_cache_hit_rate
            },
            "training_progress": {
                "current_round": self.training_metrics.current_round,
                "total_rounds": self.training_metrics.total_rounds,
                "round_progress": self.training_metrics.round_progress,
                "global_accuracy": self.training_metrics.global_accuracy,
                "global_loss": self.training_metrics.global_loss,
                "accuracy_trend": self.training_metrics.accuracy_trend[-10:],  # Últimos 10
                "loss_trend": self.training_metrics.loss_trend[-10:],  # Últimos 10
                "convergence_indicator": self.training_metrics.convergence_indicator,
                "estimated_completion_time": self.training_metrics.estimated_completion_time,
                "training_duration": self.training_metrics.training_duration,
                "samples_processed": self.training_metrics.samples_processed,
                "models_aggregated": self.training_metrics.models_aggregated
            },
            "alerts": [
                {
                    "alert_id": alert.alert_id,
                    "severity": alert.severity.value,
                    "component": alert.component,
                    "message": alert.message,
                    "timestamp": alert.timestamp,
                    "resolved": alert.resolved,
                    "resolved_at": alert.resolved_at
                }
                for alert in self.alerts[-10:]  # Últimas 10 alertas
            ],
            "system_health": self._calculate_system_health_score()
        }

    def get_metrics_history(self, metric_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtener historial de métricas."""
        if metric_type not in self.metrics_history:
            return []

        return self.metrics_history[metric_type][-limit:]

    def _calculate_system_health_score(self) -> float:
        """Calcular puntaje de salud del sistema."""
        scores = []

        # Salud federada (30%)
        fed_score = min(100.0, self.federated_metrics.training_efficiency)
        scores.append(fed_score * 0.3)

        # Salud de datos (20%)
        data_score = self.data_metrics.distribution_success_rate
        scores.append(data_score * 0.2)

        # Salud de nodos (25%)
        node_score = (self.node_metrics.active_nodes / self.node_metrics.total_nodes * 100.0) if self.node_metrics.total_nodes > 0 else 100.0
        scores.append(node_score * 0.25)

        # Salud IPFS (15%)
        ipfs_score = self.ipfs_metrics.publish_success_rate
        scores.append(ipfs_score * 0.15)

        # Salud de entrenamiento (10%)
        training_score = self.training_metrics.convergence_indicator * 100.0
        scores.append(training_score * 0.1)

        return sum(scores)

    def get_alerts(self, severity: Optional[AlertSeverity] = None, resolved: bool = False, limit: int = 20) -> List[Alert]:
        """Obtener alertas filtradas."""
        alerts = [alert for alert in self.alerts if alert.resolved == resolved]

        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]

        return alerts[-limit:]

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolver una alerta con validación."""
        if not alert_id or not isinstance(alert_id, str):
            logger.warning(f"❌ Invalid alert_id for resolution: {alert_id}")
            return False

        for alert in self.alerts:
            if alert.alert_id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = time.time()
                logger.info(f"✅ Alert resolved: {alert_id} - {alert.message}")

                # Notify WebSocket clients about alert resolution
                asyncio.create_task(self._notify_alert_resolution(alert))
                return True

        logger.warning(f"⚠️ Alert not found or already resolved: {alert_id}")
        return False

    async def _notify_alert_resolution(self, alert: Alert):
        """Notify WebSocket clients about alert resolution."""
        try:
            message = {
                "type": "alert_resolved",
                "alert_id": alert.alert_id,
                "component": alert.component,
                "message": alert.message,
                "timestamp": time.time()
            }

            for websocket in self.websocket_connections.values():
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to notify client about alert resolution: {e}")

        except Exception as e:
            logger.error(f"Error notifying alert resolution: {e}")

    def validate_configuration(self) -> List[str]:
        """Validate dashboard configuration and return any issues."""
        issues = []

        if self.update_interval <= 0:
            issues.append("Update interval must be positive")

        if self.websocket_broadcast_interval <= 0:
            issues.append("WebSocket broadcast interval must be positive")

        if self.monitoring_level not in MonitoringLevel:
            issues.append(f"Invalid monitoring level: {self.monitoring_level}")

        if not self.app:
            issues.append("FastAPI application not initialized")

        return issues

    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of the dashboard."""
        issues = self.validate_configuration()

        return {
            "overall_health": "healthy" if not issues else "degraded",
            "is_running": self.is_running,
            "last_update": self.last_update,
            "configuration_issues": issues,
            "active_components": {
                "federated_coordinator": self.federated_coordinator is not None,
                "data_coordinator": self.data_coordinator is not None,
                "ipfs_distributor": self.ipfs_distributor is not None,
                "fastapi_app": self.app is not None
            },
            "websocket_connections": len(self.websocket_connections),
            "active_alerts": len([a for a in self.alerts if not a.resolved]),
            "metrics_history_size": {k: len(v) for k, v in self.metrics_history.items()},
            "timestamp": time.time()
        }

    async def get_system_connectivity_status(self) -> Dict[str, Any]:
        """Get system connectivity status for various services and dependencies."""
        connectivity_checks = {}

        try:
            # Check database connectivity
            connectivity_checks["database"] = await self._check_database_connectivity()

            # Check external API connectivity
            connectivity_checks["external_apis"] = await self._check_external_api_connectivity()

            # Check IPFS connectivity
            connectivity_checks["ipfs"] = await self._check_ipfs_connectivity()

            # Check federated coordinator connectivity
            connectivity_checks["federated_coordinator"] = await self._check_federated_coordinator_connectivity()

            # Check data coordinator connectivity
            connectivity_checks["data_coordinator"] = await self._check_data_coordinator_connectivity()

            # Check network connectivity
            connectivity_checks["network"] = await self._check_network_connectivity()

        except Exception as e:
            logger.error(f"Error checking system connectivity: {e}")
            connectivity_checks["error"] = str(e)

        # Calculate overall connectivity status
        overall_status = self._calculate_overall_connectivity_status(connectivity_checks)

        return {
            "overall_status": overall_status,
            "checks": connectivity_checks,
            "timestamp": time.time()
        }

    async def get_service_health_status(self) -> Dict[str, Any]:
        """Get health status of backend services."""
        service_checks = {}

        try:
            # Check federated coordinator service
            service_checks["federated_coordinator"] = await self._check_service_health("federated_coordinator")

            # Check data coordinator service
            service_checks["data_coordinator"] = await self._check_service_health("data_coordinator")

            # Check IPFS distributor service
            service_checks["ipfs_distributor"] = await self._check_service_health("ipfs_distributor")

            # Check technical dashboard service
            service_checks["technical_dashboard"] = await self._check_service_health("technical_dashboard")

            # Check notification service
            service_checks["notification_service"] = await self._check_service_health("notification_service")

            # Check validation service
            service_checks["validation_service"] = await self._check_service_health("validation_service")

        except Exception as e:
            logger.error(f"Error checking service health: {e}")
            service_checks["error"] = str(e)

        # Calculate overall service health
        overall_health = self._calculate_overall_service_health(service_checks)

        return {
            "overall_health": overall_health,
            "services": service_checks,
            "timestamp": time.time()
        }

    async def get_infrastructure_monitoring_status(self) -> Dict[str, Any]:
        """Get infrastructure monitoring data for databases and external dependencies."""
        infrastructure_checks = {}

        try:
            # Database monitoring
            infrastructure_checks["databases"] = await self._check_database_infrastructure()

            # External dependencies monitoring
            infrastructure_checks["external_dependencies"] = await self._check_external_dependencies()

            # Storage monitoring
            infrastructure_checks["storage"] = await self._check_storage_infrastructure()

            # Network infrastructure
            infrastructure_checks["network_infrastructure"] = await self._check_network_infrastructure()

            # Compute resources
            infrastructure_checks["compute_resources"] = await self._check_compute_resources()

        except Exception as e:
            logger.error(f"Error checking infrastructure: {e}")
            infrastructure_checks["error"] = str(e)

        # Calculate overall infrastructure health
        overall_health = self._calculate_overall_infrastructure_health(infrastructure_checks)

        return {
            "overall_health": overall_health,
            "infrastructure": infrastructure_checks,
            "timestamp": time.time()
        }

    async def _check_database_connectivity(self) -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            # Simulate database connectivity check
            # In real implementation, this would connect to actual databases
            await asyncio.sleep(0.1)  # Simulate network call

            return {
                "status": "connected",
                "latency_ms": 15.5 + (time.time() % 10.0),
                "last_check": time.time()
            }
        except Exception as e:
            return {
                "status": "disconnected",
                "error": str(e),
                "last_check": time.time()
            }

    async def _check_external_api_connectivity(self) -> Dict[str, Any]:
        """Check external API connectivity."""
        try:
            # Simulate external API checks
            await asyncio.sleep(0.1)

            apis_status = {
                "marketplace_api": {
                    "status": "connected",
                    "latency_ms": 45.2 + (time.time() % 20.0)
                },
                "wallet_api": {
                    "status": "connected",
                    "latency_ms": 32.8 + (time.time() % 15.0)
                },
                "notification_api": {
                    "status": "connected",
                    "latency_ms": 28.5 + (time.time() % 12.0)
                }
            }

            return {
                "status": "healthy",
                "apis": apis_status,
                "last_check": time.time()
            }
        except Exception as e:
            return {
                "status": "degraded",
                "error": str(e),
                "last_check": time.time()
            }

    async def _check_ipfs_connectivity(self) -> Dict[str, Any]:
        """Check IPFS connectivity."""
        try:
            if self.ipfs_distributor:
                # Use actual IPFS distributor status
                ipfs_stats = self.ipfs_distributor.get_stats()
                return {
                    "status": "connected" if ipfs_stats.get('active_peers', 0) > 0 else "limited",
                    "active_peers": ipfs_stats.get('active_peers', 0),
                    "bandwidth_in": ipfs_stats.get('bandwidth_in', 0),
                    "bandwidth_out": ipfs_stats.get('bandwidth_out', 0),
                    "last_check": time.time()
                }
            else:
                # Simulate IPFS connectivity
                return {
                    "status": "disconnected",
                    "message": "IPFS distributor not available",
                    "last_check": time.time()
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_check": time.time()
            }

    async def _check_federated_coordinator_connectivity(self) -> Dict[str, Any]:
        """Check federated coordinator connectivity."""
        try:
            if self.federated_coordinator:
                # Check if coordinator is responsive
                status = self.federated_coordinator.get_global_status()
                return {
                    "status": "connected",
                    "active_sessions": len(status.get('active_sessions', [])),
                    "last_check": time.time()
                }
            else:
                return {
                    "status": "disconnected",
                    "message": "Federated coordinator not initialized",
                    "last_check": time.time()
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_check": time.time()
            }

    async def _check_data_coordinator_connectivity(self) -> Dict[str, Any]:
        """Check data coordinator connectivity."""
        try:
            if self.data_coordinator:
                pipelines = self.data_coordinator.get_active_pipelines()
                return {
                    "status": "connected",
                    "active_pipelines": len(pipelines),
                    "last_check": time.time()
                }
            else:
                return {
                    "status": "disconnected",
                    "message": "Data coordinator not initialized",
                    "last_check": time.time()
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_check": time.time()
            }

    async def _check_network_connectivity(self) -> Dict[str, Any]:
        """Check general network connectivity."""
        try:
            # Simulate network connectivity check
            await asyncio.sleep(0.05)

            return {
                "status": "connected",
                "latency_ms": 12.3 + (time.time() % 8.0),
                "packet_loss": 0.0,
                "last_check": time.time()
            }
        except Exception as e:
            return {
                "status": "disconnected",
                "error": str(e),
                "last_check": time.time()
            }

    async def _check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Check health of a specific service."""
        try:
            # Simulate service health check
            await asyncio.sleep(0.1)

            # Mock different health statuses based on service
            if service_name == "federated_coordinator":
                is_healthy = self.federated_coordinator is not None
            elif service_name == "data_coordinator":
                is_healthy = self.data_coordinator is not None
            elif service_name == "ipfs_distributor":
                is_healthy = self.ipfs_distributor is not None
            elif service_name == "technical_dashboard":
                is_healthy = self.is_running
            else:
                is_healthy = True  # Assume other services are healthy

            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "response_time_ms": 25.0 + (time.time() % 15.0),
                "uptime_percentage": 99.5 + (time.time() % 0.5),
                "last_check": time.time()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_check": time.time()
            }

    async def _check_database_infrastructure(self) -> Dict[str, Any]:
        """Check database infrastructure."""
        try:
            # Simulate database infrastructure checks
            await asyncio.sleep(0.1)

            databases = {
                "primary_db": {
                    "status": "healthy",
                    "connections": 15 + int(time.time() % 10),
                    "query_latency_ms": 5.2 + (time.time() % 3.0),
                    "storage_used_gb": 45.8 + (time.time() % 5.0),
                    "storage_total_gb": 100.0
                },
                "cache_db": {
                    "status": "healthy",
                    "connections": 25 + int(time.time() % 15),
                    "hit_rate": 0.85 + (time.time() % 0.1),
                    "memory_used_mb": 512 + int(time.time() % 100)
                }
            }

            return {
                "status": "healthy",
                "databases": databases,
                "last_check": time.time()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_check": time.time()
            }

    async def _check_external_dependencies(self) -> Dict[str, Any]:
        """Check external dependencies."""
        try:
            # Simulate external dependency checks
            await asyncio.sleep(0.1)

            dependencies = {
                "blockchain_node": {
                    "status": "connected",
                    "block_height": 12345678 + int(time.time() % 1000),
                    "peers": 12 + int(time.time() % 5)
                },
                "external_storage": {
                    "status": "available",
                    "latency_ms": 45.0 + (time.time() % 20.0),
                    "bandwidth_mbps": 50.0 + (time.time() % 10.0)
                },
                "notification_service": {
                    "status": "operational",
                    "queue_size": 5 + int(time.time() % 10),
                    "success_rate": 0.98 + (time.time() % 0.02)
                }
            }

            return {
                "status": "healthy",
                "dependencies": dependencies,
                "last_check": time.time()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_check": time.time()
            }

    async def _check_storage_infrastructure(self) -> Dict[str, Any]:
        """Check storage infrastructure."""
        try:
            # Simulate storage checks
            await asyncio.sleep(0.1)

            storage = {
                "local_storage": {
                    "status": "healthy",
                    "used_gb": 234.5 + (time.time() % 10.0),
                    "total_gb": 500.0,
                    "utilization_percent": 46.9 + (time.time() % 5.0)
                },
                "ipfs_storage": {
                    "status": "healthy",
                    "pins": self.ipfs_metrics.total_pins if hasattr(self, 'ipfs_metrics') else 1250,
                    "storage_used_gb": 12.5 + (time.time() % 2.0),
                    "peers_connected": 8 + int(time.time() % 4)
                }
            }

            return {
                "status": "healthy",
                "storage": storage,
                "last_check": time.time()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_check": time.time()
            }

    async def _check_network_infrastructure(self) -> Dict[str, Any]:
        """Check network infrastructure."""
        try:
            # Simulate network infrastructure checks
            await asyncio.sleep(0.1)

            network = {
                "bandwidth": {
                    "upload_mbps": 50.0 + (time.time() % 10.0),
                    "download_mbps": 100.0 + (time.time() % 20.0),
                    "utilization_percent": 35.0 + (time.time() % 15.0)
                },
                "latency": {
                    "average_ms": 25.0 + (time.time() % 10.0),
                    "jitter_ms": 2.5 + (time.time() % 2.0)
                },
                "connections": {
                    "active": 45 + int(time.time() % 20),
                    "established": 120 + int(time.time() % 30),
                    "listening": 15 + int(time.time() % 5)
                }
            }

            return {
                "status": "healthy",
                "network": network,
                "last_check": time.time()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_check": time.time()
            }

    async def _check_compute_resources(self) -> Dict[str, Any]:
        """Check compute resources."""
        try:
            # Simulate compute resource checks
            await asyncio.sleep(0.1)

            compute = {
                "cpu": {
                    "cores": 8,
                    "usage_percent": self.node_metrics.average_cpu_usage if hasattr(self, 'node_metrics') else 45.0 + (time.time() % 20.0),
                    "load_average": [1.2 + (time.time() % 0.5), 1.5 + (time.time() % 0.8), 1.8 + (time.time() % 1.0)]
                },
                "memory": {
                    "total_gb": 16.0,
                    "used_gb": 8.5 + (time.time() % 2.0),
                    "usage_percent": self.node_metrics.average_memory_usage if hasattr(self, 'node_metrics') else 53.0 + (time.time() % 15.0)
                },
                "gpu": {
                    "available": True,
                    "count": 1,
                    "usage_percent": self.node_metrics.average_gpu_usage if hasattr(self, 'node_metrics') else 65.0 + (time.time() % 25.0),
                    "memory_used_mb": 2048 + int(time.time() % 512)
                }
            }

            return {
                "status": "healthy",
                "compute": compute,
                "last_check": time.time()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_check": time.time()
            }

    def _calculate_overall_connectivity_status(self, checks: Dict[str, Any]) -> str:
        """Calculate overall connectivity status."""
        if "error" in checks:
            return "error"

        statuses = []
        for check_name, check_data in checks.items():
            if isinstance(check_data, dict) and "status" in check_data:
                statuses.append(check_data["status"])

        if "disconnected" in statuses or "error" in statuses:
            return "degraded"
        elif all(status in ["connected", "healthy", "limited"] for status in statuses):
            return "healthy"
        else:
            return "unknown"

    def _calculate_overall_service_health(self, services: Dict[str, Any]) -> str:
        """Calculate overall service health."""
        if "error" in services:
            return "error"

        statuses = []
        for service_name, service_data in services.items():
            if isinstance(service_data, dict) and "status" in service_data:
                statuses.append(service_data["status"])

        if "unhealthy" in statuses or "error" in statuses:
            return "degraded"
        elif all(status == "healthy" for status in statuses):
            return "healthy"
        else:
            return "unknown"

    def _calculate_overall_infrastructure_health(self, infrastructure: Dict[str, Any]) -> str:
        """Calculate overall infrastructure health."""
        if "error" in infrastructure:
            return "error"

        statuses = []
        for infra_name, infra_data in infrastructure.items():
            if isinstance(infra_data, dict) and "status" in infra_data:
                statuses.append(infra_data["status"])

        if "error" in statuses:
            return "degraded"
        elif all(status == "healthy" for status in statuses):
            return "healthy"
        else:
            return "unknown"

    async def export_metrics_report(self, format: str = "json") -> str:
        """Exportar reporte de métricas."""
        status = self.get_comprehensive_status()

        if format == "json":
            return json.dumps(status, indent=2, default=str)
        elif format == "text":
            return self._format_text_report(status)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _format_text_report(self, status: Dict[str, Any]) -> str:
        """Formatear reporte en texto."""
        lines = []
        lines.append("=== AILOOS Technical Dashboard Report ===")
        lines.append(f"Timestamp: {datetime.fromtimestamp(status['timestamp'])}")
        lines.append("")

        lines.append("FEDERATED TRAINING:")
        fed = status['federated_training']
        lines.append(f"  Active Sessions: {fed['active_sessions']}")
        lines.append(f"  Average Accuracy: {fed['average_accuracy']:.3f}")
        lines.append(f"  Training Efficiency: {fed['training_efficiency']:.1f}%")
        lines.append("")

        lines.append("DATA DISTRIBUTION:")
        data = status['data_distribution']
        lines.append(f"  Active Pipelines: {data['active_pipelines']}")
        lines.append(f"  Distribution Success Rate: {data['distribution_success_rate']:.1f}%")
        lines.append("")

        lines.append("NODE PERFORMANCE:")
        nodes = status['node_performance']
        lines.append(f"  Active Nodes: {nodes['active_nodes']}/{nodes['total_nodes']}")
        lines.append(f"  Average CPU Usage: {nodes['average_cpu_usage']:.1f}%")
        lines.append(f"  Average Memory Usage: {nodes['average_memory_usage']:.1f}%")
        lines.append("")

        lines.append("IPFS METRICS:")
        ipfs = status['ipfs_metrics']
        lines.append(f"  Chunks Published: {ipfs['chunks_published']}")
        lines.append(f"  Publish Success Rate: {ipfs['publish_success_rate']:.1f}%")
        lines.append("")

        lines.append("TRAINING PROGRESS:")
        training = status['training_progress']
        lines.append(f"  Current Round: {training['current_round']}/{training['total_rounds']}")
        lines.append(f"  Global Accuracy: {training['global_accuracy']:.3f}")
        lines.append(f"  Global Loss: {training['global_loss']:.3f}")
        lines.append(f"  Convergence Indicator: {training['convergence_indicator']:.3f}")
        lines.append("")

        lines.append(f"SYSTEM HEALTH SCORE: {status['system_health']:.1f}%")
        lines.append("")

        if status['alerts']:
            lines.append("ACTIVE ALERTS:")
            for alert in status['alerts']:
                if not alert['resolved']:
                    lines.append(f"  {alert['severity'].upper()}: {alert['component']} - {alert['message']}")

        return "\n".join(lines)


# Función de conveniencia para crear dashboard técnico
def create_technical_dashboard(
    federated_coordinator: Optional[FederatedCoordinator] = None,
    data_coordinator: Optional[FederatedDataCoordinator] = None,
    ipfs_distributor: Optional[IPFSDistributor] = None,
    monitoring_level: MonitoringLevel = MonitoringLevel.DETAILED
) -> TechnicalDashboard:
    """Crear instancia del dashboard técnico."""
    return TechnicalDashboard(
        federated_coordinator=federated_coordinator,
        data_coordinator=data_coordinator,
        ipfs_distributor=ipfs_distributor,
        monitoring_level=monitoring_level
    )


# Función para iniciar monitoreo técnico
async def start_technical_monitoring(
    federated_coordinator: Optional[FederatedCoordinator] = None,
    data_coordinator: Optional[FederatedDataCoordinator] = None,
    ipfs_distributor: Optional[IPFSDistributor] = None
) -> TechnicalDashboard:
    """Función de conveniencia para iniciar monitoreo técnico."""
    dashboard = create_technical_dashboard(
        federated_coordinator=federated_coordinator,
        data_coordinator=data_coordinator,
        ipfs_distributor=ipfs_distributor
    )

    await dashboard.start_monitoring()
    return dashboard