"""
TrainingAPI - API para controlar el entrenamiento desde el SDK
Proporciona interfaz REST para gestión completa del entrenamiento asíncrono.
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from ..core.logging import get_logger
from .training_state_manager import TrainingStateManager, TrainingStatus
from .checkpoint_manager import CheckpointManager, CheckpointConfig
from .async_training_controller import AsyncTrainingController, AsyncTrainingConfig
from .network_sync_manager import NetworkSyncManager, NetworkConfig, NetworkStatus
from .training_progress_tracker import TrainingProgressTracker

logger = get_logger(__name__)


# Modelos Pydantic para requests/responses
class TrainingSessionRequest(BaseModel):
    """Request para crear una sesión de entrenamiento."""
    model_version: str
    training_config: Dict[str, Any]
    model_configuration: Dict[str, Any]
    session_name: Optional[str] = None


class CheckpointRequest(BaseModel):
    """Request para crear un checkpoint."""
    epoch: int
    batch: int
    global_step: int
    metrics: Optional[Dict[str, float]] = None


class NetworkConfigRequest(BaseModel):
    """Request para configurar sincronización de red."""
    sync_server_url: Optional[str] = None
    websocket_url: Optional[str] = None
    api_key: Optional[str] = None
    enable_auto_sync: Optional[bool] = None
    sync_on_connectivity: Optional[bool] = None


class TrainingAPIConfig:
    """Configuración de la Training API."""
    host: str = "0.0.0.0"
    port: int = 8001
    enable_cors: bool = True
    cors_origins: List[str] = ["*"]
    api_prefix: str = "/api/v1/training"
    enable_docs: bool = True
    log_requests: bool = True


class TrainingAPIService:
    """
    Servicio API para entrenamiento asíncrono.

    Proporciona endpoints REST para:
    - Gestión de sesiones de entrenamiento
    - Control de entrenamiento (start/pause/resume/stop)
    - Checkpoints y recuperación
    - Sincronización de red
    - Monitoreo y métricas
    """

    def __init__(self, config: Optional[TrainingAPIConfig] = None):
        self.config = config or TrainingAPIConfig()
        self.app = FastAPI(
            title="AILOOS Training API",
            description="API para control del entrenamiento asíncrono de EmpoorioLM",
            version="1.0.0",
            docs_url="/docs" if self.config.enable_docs else None,
            redoc_url="/redoc" if self.config.enable_docs else None
        )

        # Configurar CORS
        if self.config.enable_cors:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=self.config.cors_origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

        # Componentes del sistema
        self.state_manager: Optional[TrainingStateManager] = None
        self.checkpoint_manager: Optional[CheckpointManager] = None
        self.training_controller: Optional[AsyncTrainingController] = None
        self.network_sync: Optional[NetworkSyncManager] = None
        self.progress_tracker: Optional[TrainingProgressTracker] = None

        # Estado de sesiones activas
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

        # Configurar rutas
        self._setup_routes()

        # Middleware de logging
        if self.config.log_requests:
            self._setup_logging_middleware()

        logger.info(f"🚀 TrainingAPI inicializada en {self.config.host}:{self.config.port}")

    def _setup_routes(self):
        """Configurar rutas de la API."""

        @self.app.get("/")
        async def root():
            """Endpoint raíz."""
            return {
                "service": "AILOOS Training API",
                "version": "1.0.0",
                "status": "running",
                "endpoints": [
                    f"{self.config.api_prefix}/sessions",
                    f"{self.config.api_prefix}/sessions/{{session_id}}",
                    f"{self.config.api_prefix}/sessions/{{session_id}}/start",
                    f"{self.config.api_prefix}/sessions/{{session_id}}/pause",
                    f"{self.config.api_prefix}/sessions/{{session_id}}/resume",
                    f"{self.config.api_prefix}/sessions/{{session_id}}/stop",
                    f"{self.config.api_prefix}/checkpoints",
                    f"{self.config.api_prefix}/network/status",
                    f"{self.config.api_prefix}/metrics"
                ]
            }

        # Sesiones de entrenamiento
        @self.app.post(f"{self.config.api_prefix}/sessions")
        async def create_session(request: TrainingSessionRequest):
            """Crear una nueva sesión de entrenamiento."""
            try:
                session_id = str(uuid.uuid4())

                # Crear sesión en el state manager
                if self.state_manager:
                    session = await self.state_manager.create_session(
                        session_id=session_id,
                        model_version=request.model_version,
                        training_config=request.training_config,
                        model_config=request.model_configuration
                    )

                    self.active_sessions[session_id] = {
                        'session': session,
                        'created_at': time.time(),
                        'status': 'created'
                    }

                    return {
                        'session_id': session_id,
                        'status': 'created',
                        'message': f'Sesión {session_id} creada exitosamente'
                    }
                else:
                    raise HTTPException(status_code=503, detail="State manager no disponible")

            except Exception as e:
                logger.error(f"Error creando sesión: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get(f"{self.config.api_prefix}/sessions")
        async def list_sessions():
            """Listar todas las sesiones."""
            try:
                if not self.state_manager:
                    raise HTTPException(status_code=503, detail="State manager no disponible")

                sessions = await self.state_manager.list_sessions()
                return {
                    'sessions': [
                        {
                            'session_id': s.session_id,
                            'model_version': s.model_version,
                            'status': s.status.value,
                            'current_epoch': s.current_epoch,
                            'progress': f"{s.current_epoch}/{s.total_epochs}" if s.total_epochs else "N/A"
                        }
                        for s in sessions
                    ],
                    'total': len(sessions)
                }

            except Exception as e:
                logger.error(f"Error listando sesiones: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get(f"{self.config.api_prefix}/sessions/{{session_id}}")
        async def get_session(session_id: str):
            """Obtener información de una sesión específica."""
            try:
                if not self.state_manager:
                    raise HTTPException(status_code=503, detail="State manager no disponible")

                session = await self.state_manager.get_session(session_id)
                if not session:
                    raise HTTPException(status_code=404, detail="Sesión no encontrada")

                return {
                    'session_id': session.session_id,
                    'model_version': session.model_version,
                    'status': session.status.value,
                    'current_epoch': session.current_epoch,
                    'total_epochs': session.total_epochs,
                    'current_batch': session.current_batch,
                    'total_batches': session.total_batches,
                    'loss_history': session.loss_history[-10:],  # Últimos 10 valores
                    'accuracy_history': session.accuracy_history[-10:],
                    'learning_rate': session.learning_rate,
                    'start_time': session.start_time,
                    'last_update': session.last_update
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error obteniendo sesión {session_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post(f"{self.config.api_prefix}/sessions/{{session_id}}/start")
        async def start_training(session_id: str, background_tasks: BackgroundTasks):
            """Iniciar entrenamiento para una sesión."""
            try:
                if not self.training_controller:
                    raise HTTPException(status_code=503, detail="Training controller no disponible")

                # Verificar que la sesión existe
                session = await self.state_manager.get_session(session_id)
                if not session:
                    raise HTTPException(status_code=404, detail="Sesión no encontrada")

                if session.status != TrainingStatus.NOT_STARTED:
                    raise HTTPException(status_code=400, detail="Sesión ya iniciada")

                # Iniciar entrenamiento en background
                background_tasks.add_task(self._start_training_async, session_id)

                return {
                    'session_id': session_id,
                    'status': 'starting',
                    'message': 'Entrenamiento iniciándose en background'
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error iniciando entrenamiento {session_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post(f"{self.config.api_prefix}/sessions/{{session_id}}/pause")
        async def pause_training(session_id: str):
            """Pausar entrenamiento."""
            try:
                if not self.training_controller:
                    raise HTTPException(status_code=503, detail="Training controller no disponible")

                await self.training_controller.pause_training()

                return {
                    'session_id': session_id,
                    'status': 'paused',
                    'message': 'Entrenamiento pausado'
                }

            except Exception as e:
                logger.error(f"Error pausando entrenamiento {session_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post(f"{self.config.api_prefix}/sessions/{{session_id}}/resume")
        async def resume_training(session_id: str):
            """Reanudar entrenamiento."""
            try:
                if not self.training_controller:
                    raise HTTPException(status_code=503, detail="Training controller no disponible")

                await self.training_controller.resume_training()

                return {
                    'session_id': session_id,
                    'status': 'resumed',
                    'message': 'Entrenamiento reanudado'
                }

            except Exception as e:
                logger.error(f"Error reanudando entrenamiento {session_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post(f"{self.config.api_prefix}/sessions/{{session_id}}/stop")
        async def stop_training(session_id: str):
            """Detener entrenamiento."""
            try:
                if not self.training_controller:
                    raise HTTPException(status_code=503, detail="Training controller no disponible")

                await self.training_controller.stop_training()

                return {
                    'session_id': session_id,
                    'status': 'stopped',
                    'message': 'Entrenamiento detenido'
                }

            except Exception as e:
                logger.error(f"Error deteniendo entrenamiento {session_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Checkpoints
        @self.app.post(f"{self.config.api_prefix}/sessions/{{session_id}}/checkpoint")
        async def create_checkpoint(session_id: str, request: CheckpointRequest):
            """Crear un checkpoint manual."""
            try:
                if not self.checkpoint_manager:
                    raise HTTPException(status_code=503, detail="Checkpoint manager no disponible")

                # Aquí necesitaríamos acceso al modelo y optimizer actuales
                # En una implementación completa, esto se obtendría del training controller
                checkpoint_id = f"manual_{session_id}_{int(time.time())}"

                return {
                    'checkpoint_id': checkpoint_id,
                    'session_id': session_id,
                    'status': 'created',
                    'message': 'Checkpoint creado (simulado)'
                }

            except Exception as e:
                logger.error(f"Error creando checkpoint para {session_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get(f"{self.config.api_prefix}/sessions/{{session_id}}/checkpoints")
        async def list_checkpoints(session_id: str):
            """Listar checkpoints de una sesión."""
            try:
                if not self.checkpoint_manager:
                    raise HTTPException(status_code=503, detail="Checkpoint manager no disponible")

                checkpoints = await self.checkpoint_manager.list_checkpoints(session_id)

                return {
                    'session_id': session_id,
                    'checkpoints': [
                        {
                            'checkpoint_id': cp.checkpoint_id,
                            'epoch': cp.epoch,
                            'batch': cp.batch,
                            'timestamp': cp.timestamp,
                            'size_mb': cp.compressed_size_bytes / (1024 * 1024),
                            'metrics': cp.metrics
                        }
                        for cp in checkpoints
                    ],
                    'total': len(checkpoints)
                }

            except Exception as e:
                logger.error(f"Error listando checkpoints para {session_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Red y sincronización
        @self.app.get(f"{self.config.api_prefix}/network/status")
        async def get_network_status():
            """Obtener estado de la red."""
            try:
                if not self.network_sync:
                    return {
                        'status': 'disabled',
                        'message': 'Network sync no configurado'
                    }

                stats = await self.network_sync.get_network_stats()

                return {
                    'network_status': stats['current_status'],
                    'connectivity': {
                        'online': stats['current_status'] == 'online',
                        'limited': stats['current_status'] == 'limited',
                        'offline': stats['current_status'] == 'offline'
                    },
                    'sync_stats': {
                        'total_syncs': stats['total_syncs'],
                        'success_rate': stats['success_rate'],
                        'pending_syncs': stats['pending_syncs']
                    },
                    'data_transfer': {
                        'uploaded_mb': stats['total_data_uploaded'] / (1024 * 1024),
                        'downloaded_mb': stats['total_data_downloaded'] / (1024 * 1024)
                    }
                }

            except Exception as e:
                logger.error(f"Error obteniendo estado de red: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.put(f"{self.config.api_prefix}/network/config")
        async def update_network_config(request: NetworkConfigRequest):
            """Actualizar configuración de red."""
            try:
                if not self.network_sync:
                    raise HTTPException(status_code=503, detail="Network sync no disponible")

                # Actualizar configuración (simplificado)
                # En implementación real, actualizaría la configuración del network_sync

                return {
                    'status': 'updated',
                    'message': 'Configuración de red actualizada'
                }

            except Exception as e:
                logger.error(f"Error actualizando configuración de red: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Métricas y monitoreo
        @self.app.get(f"{self.config.api_prefix}/metrics")
        async def get_training_metrics():
            """Obtener métricas generales del entrenamiento."""
            try:
                metrics = {}

                # Métricas del state manager
                if self.state_manager:
                    state_stats = await self.state_manager.get_stats()
                    metrics['state_manager'] = state_stats

                # Métricas del checkpoint manager
                if self.checkpoint_manager:
                    checkpoint_stats = await self.checkpoint_manager.get_checkpoint_stats()
                    metrics['checkpoint_manager'] = checkpoint_stats

                # Métricas del progress tracker
                if self.progress_tracker:
                    progress = self.progress_tracker.get_progress()
                    metrics['progress_tracker'] = progress

                # Métricas del network sync
                if self.network_sync:
                    network_stats = await self.network_sync.get_network_stats()
                    metrics['network_sync'] = network_stats

                # Estado de sesiones activas
                metrics['active_sessions'] = {
                    'count': len(self.active_sessions),
                    'sessions': list(self.active_sessions.keys())
                }

                return metrics

            except Exception as e:
                logger.error(f"Error obteniendo métricas: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get(f"{self.config.api_prefix}/health")
        async def health_check():
            """Health check del servicio."""
            components_status = {}

            # Verificar componentes
            components_status['state_manager'] = self.state_manager is not None
            components_status['checkpoint_manager'] = self.checkpoint_manager is not None
            components_status['training_controller'] = self.training_controller is not None
            components_status['network_sync'] = self.network_sync is not None
            components_status['progress_tracker'] = self.progress_tracker is not None

            all_healthy = all(components_status.values())

            return {
                'status': 'healthy' if all_healthy else 'degraded',
                'timestamp': time.time(),
                'components': components_status,
                'active_sessions': len(self.active_sessions)
            }

    def _setup_logging_middleware(self):
        """Configurar middleware de logging para requests."""

        @self.app.middleware("http")
        async def log_requests(request: Request, call_next):
            start_time = time.time()

            # Log request
            logger.info(f"📨 {request.method} {request.url.path}")

            # Process request
            response = await call_next(request)

            # Log response
            process_time = time.time() - start_time
            logger.info(f"📤 {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)")

            return response

    async def _start_training_async(self, session_id: str):
        """Iniciar entrenamiento de forma asíncrona."""
        try:
            logger.info(f"🎯 Iniciando entrenamiento asíncrono para sesión {session_id}")

            if not self.training_controller:
                logger.error("Training controller no disponible")
                return

            # Aquí se configuraría el training controller con la sesión específica
            # En una implementación completa, se crearía un nuevo controller para esta sesión

            success = await self.training_controller.start_training()

            if success:
                logger.info(f"✅ Entrenamiento completado para sesión {session_id}")
            else:
                logger.error(f"❌ Entrenamiento falló para sesión {session_id}")

        except Exception as e:
            logger.error(f"❌ Error en entrenamiento asíncrono {session_id}: {e}")

    def initialize_components(
        self,
        state_manager: Optional[TrainingStateManager] = None,
        checkpoint_manager: Optional[CheckpointManager] = None,
        training_controller: Optional[AsyncTrainingController] = None,
        network_sync: Optional[NetworkSyncManager] = None,
        progress_tracker: Optional[TrainingProgressTracker] = None
    ):
        """Inicializar componentes del sistema."""
        self.state_manager = state_manager
        self.checkpoint_manager = checkpoint_manager
        self.training_controller = training_controller
        self.network_sync = network_sync
        self.progress_tracker = progress_tracker

        logger.info("🔧 Componentes de TrainingAPI inicializados")

    def run(self):
        """Ejecutar el servidor API."""
        logger.info(f"🌐 Iniciando servidor TrainingAPI en {self.config.host}:{self.config.port}")

        uvicorn.run(
            self.app,
            host=self.config.host,
            port=self.config.port,
            log_level="info"
        )

    async def run_async(self):
        """Ejecutar el servidor API de forma asíncrona."""
        config = uvicorn.Config(
            self.app,
            host=self.config.host,
            port=self.config.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()


# Función de conveniencia para crear y ejecutar la API
def create_training_api(
    state_manager: Optional[TrainingStateManager] = None,
    checkpoint_manager: Optional[CheckpointManager] = None,
    training_controller: Optional[AsyncTrainingController] = None,
    network_sync: Optional[NetworkSyncManager] = None,
    progress_tracker: Optional[TrainingProgressTracker] = None,
    config: Optional[TrainingAPIConfig] = None
) -> TrainingAPIService:
    """
    Crear instancia de TrainingAPI con componentes inicializados.

    Args:
        state_manager: Gestor de estado de entrenamiento
        checkpoint_manager: Gestor de checkpoints
        training_controller: Controlador de entrenamiento asíncrono
        network_sync: Gestor de sincronización de red
        progress_tracker: Rastreador de progreso
        config: Configuración de la API

    Returns:
        Servicio API configurado
    """
    api = TrainingAPIService(config)
    api.initialize_components(
        state_manager=state_manager,
        checkpoint_manager=checkpoint_manager,
        training_controller=training_controller,
        network_sync=network_sync,
        progress_tracker=progress_tracker
    )

    return api


# Función para ejecutar la API desde línea de comandos
def run_training_api():
    """Ejecutar TrainingAPI desde línea de comandos."""
    import argparse

    parser = argparse.ArgumentParser(description="AILOOS Training API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host para el servidor")
    parser.add_argument("--port", type=int, default=8001, help="Puerto para el servidor")
    parser.add_argument("--state-dir", default="./training_states", help="Directorio de estados")
    parser.add_argument("--checkpoint-dir", default="./checkpoints", help="Directorio de checkpoints")

    args = parser.parse_args()

    # Crear componentes básicos
    state_manager = TrainingStateManager(args.state_dir)
    checkpoint_manager = CheckpointManager(args.checkpoint_dir)

    # Crear API
    config = TrainingAPIConfig(host=args.host, port=args.port)
    api = create_training_api(
        state_manager=state_manager,
        checkpoint_manager=checkpoint_manager,
        config=config
    )

    # Ejecutar
    api.run()


if __name__ == "__main__":
    run_training_api()