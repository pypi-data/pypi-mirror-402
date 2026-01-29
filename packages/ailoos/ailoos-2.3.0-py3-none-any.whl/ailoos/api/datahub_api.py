"""
API REST específica para Data Hub - Gestión de datasets masivos.
Proporciona endpoints para listings de datasets, progreso de descarga,
gestión de chunks y estado de distribución IPFS.
"""

import asyncio
import json
import math
import time
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks, WebSocket, WebSocketDisconnect
from ..coordinator.auth.dependencies import get_current_node, get_current_admin, get_current_user
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from ..marketplace.massive_data_marketplace import massive_data_marketplace, MassiveDatasetInfo
from ..core.config import get_config, DataSourceConfig
from ..core.logging import get_logger
from ..utils.cache import cached, invalidate_cache
from ..infrastructure.ipfs_embedded import IPFSManager, create_ipfs_manager

logger = get_logger(__name__)


# Modelos Pydantic para requests/responses
class DatasetProgressRequest(BaseModel):
    dataset_id: str = Field(..., description="ID del dataset masivo")


class ChunkInfo(BaseModel):
    chunk_id: str
    index: int
    size_bytes: int
    ipfs_cid: Optional[str] = None
    status: str  # pending, uploading, uploaded, failed
    upload_progress: float = 0.0
    error_message: Optional[str] = None


class DownloadProgressResponse(BaseModel):
    dataset_id: str
    status: str
    progress_percentage: float
    downloaded_bytes: int
    total_bytes: int
    estimated_time_remaining: Optional[int] = None
    current_speed_mbps: Optional[float] = None


class ChunkManagementResponse(BaseModel):
    dataset_id: str
    total_chunks: int
    completed_chunks: int
    chunks: List[ChunkInfo]


class IPFSDistributionStatus(BaseModel):
    dataset_id: str
    distribution_status: str  # not_started, in_progress, completed, failed
    total_chunks: int
    distributed_chunks: int
    ipfs_cid: Optional[str] = None
    distribution_progress: float
    estimated_completion_time: Optional[int] = None


class LocalDatasetRegisterRequest(BaseModel):
    name: str = Field(..., description="Nombre del dataset")
    local_path: str = Field(..., description="Ruta local del archivo del dataset")
    dataset_id: Optional[str] = Field(None, description="ID opcional del dataset")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos adicionales")


class DataHubAPI:
    """
    API REST específica para Data Hub - Gestión especializada de datasets masivos.
    Maneja operaciones avanzadas de datasets masivos con tracking detallado.
    """

    def __init__(self):
        self.app = FastAPI(
            title="AILOOS Data Hub API",
            description="API especializada para gestión de datasets masivos en Data Hub",
            version="1.0.0"
        )

        # Estado del sistema
        self.system_stats = {
            "start_time": time.time(),
            "total_datasets_processed": 0,
            "active_downloads": 0,
            "active_distributions": 0
        }

        # IPFS manager (lazy init)
        self.ipfs_manager: Optional[IPFSManager] = None
        self._ipfs_manager_lock = asyncio.Lock()

        # WebSocket connections for real-time updates
        self.websocket_connections: Dict[str, WebSocket] = {}
        self.dataset_subscriptions: Dict[str, List[str]] = {}  # dataset_id -> list of client_ids

        logger.info("🏪 Data Hub API initialized")

        # Configurar rutas
        self._setup_routes()

    async def _get_ipfs_manager(self) -> IPFSManager:
        """Lazy init del IPFSManager compartido."""
        async with self._ipfs_manager_lock:
            if self.ipfs_manager is None:
                self.ipfs_manager = await create_ipfs_manager()
            return self.ipfs_manager

    def _setup_routes(self):
        """Configurar todas las rutas de la API."""

        @self.app.get("/health")
        async def health_check():
            """Health check del Data Hub."""
            uptime_seconds = time.time() - self.system_stats["start_time"]
            uptime_hours = uptime_seconds / 3600

            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "uptime_hours": f"{uptime_hours:.1f}",
                "total_datasets_processed": self.system_stats["total_datasets_processed"],
                "active_downloads": self.system_stats["active_downloads"],
                "active_distributions": self.system_stats["active_distributions"],
                "massive_datasets": {
                    "total": len(massive_data_marketplace.massive_datasets),
                    "active": len([d for d in massive_data_marketplace.massive_datasets.values() if d.status == "completed"]),
                    "processing": len([d for d in massive_data_marketplace.massive_datasets.values() if d.status in ["processing", "downloading", "chunking", "distributing", "listing"]])
                }
            }

        # ===== DATASET LISTINGS =====

        @self.app.get("/datasets", response_model=List[Dict[str, Any]])
        @cached(ttl=300, key_prefix="datahub")
        async def get_datahub_datasets(
            status: str = Query("", description="Filtrar por estado"),
            source: str = Query("", description="Filtrar por fuente"),
            limit: int = Query(50, ge=1, le=200, description="Límite de resultados")
        ):
            """Obtener lista de datasets masivos en Data Hub."""
            try:
                datasets = massive_data_marketplace.get_massive_datasets()

                # Aplicar filtros
                if status:
                    datasets = [d for d in datasets if d["status"] == status]
                if source:
                    datasets = [d for d in datasets if d["source"] == source]

                # Limitar resultados
                datasets = datasets[:limit]

                return datasets
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error obteniendo datasets: {str(e)}")

        @self.app.post("/datasets/register-local")
        async def register_local_dataset(
            request: LocalDatasetRegisterRequest,
            current_admin: dict = Depends(get_current_admin)
        ):
            """Registrar un dataset local para distribución IPFS."""
            try:
                file_path = Path(request.local_path)
                if not file_path.exists():
                    raise HTTPException(status_code=404, detail="Archivo local no encontrado")

                source_name = "local"
                if source_name not in massive_data_marketplace.active_sources:
                    massive_data_marketplace.active_sources[source_name] = DataSourceConfig(
                        name=source_name,
                        url="file://local",
                        category="custom",
                        enabled=True,
                        update_interval_hours=24,
                        max_size_mb=10_000,
                        quality_threshold=0.0,
                        auto_listing=False,
                        metadata={}
                    )

                dataset_id = request.dataset_id or massive_data_marketplace._generate_massive_dataset_id(
                    source_name, request.name
                )
                if dataset_id in massive_data_marketplace.massive_datasets:
                    raise HTTPException(status_code=409, detail="Dataset ya registrado")

                config = get_config()
                chunk_size = config.data.chunk_size_mb * 1024 * 1024
                total_size = file_path.stat().st_size
                total_chunks = max(1, math.ceil(total_size / chunk_size))

                massive_data_marketplace.massive_datasets[dataset_id] = MassiveDatasetInfo(
                    dataset_id=dataset_id,
                    name=request.name,
                    source_config=massive_data_marketplace.active_sources[source_name],
                    local_path=str(file_path),
                    size_bytes=total_size,
                    chunks_created=total_chunks,
                    status="initialized",
                    metadata=request.metadata,
                    last_updated=time.time()
                )

                return {
                    "success": True,
                    "dataset_id": dataset_id,
                    "total_size": total_size,
                    "total_chunks": total_chunks
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error registrando dataset: {str(e)}")

        @self.app.get("/datasets/{dataset_id}")
        @cached(ttl=600, key_prefix="datahub")
        async def get_datahub_dataset_details(dataset_id: str):
            """Obtener detalles completos de un dataset masivo."""
            try:
                dataset = massive_data_marketplace.get_massive_dataset_details(dataset_id)
                if not dataset:
                    raise HTTPException(status_code=404, detail="Dataset no encontrado")

                return dataset
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error obteniendo detalles del dataset: {str(e)}")

        # ===== DOWNLOAD PROGRESS =====

        @self.app.get("/datasets/{dataset_id}/download-progress", response_model=DownloadProgressResponse)
        @cached(ttl=10, key_prefix="datahub")
        async def get_download_progress(dataset_id: str):
            """Obtener progreso de descarga de un dataset masivo."""
            try:
                dataset = massive_data_marketplace.massive_datasets.get(dataset_id)
                if not dataset:
                    raise HTTPException(status_code=404, detail="Dataset no encontrado")

                # Simular progreso basado en estado (en implementación real, usar datos reales)
                if dataset.status == "downloading":
                    # Simular progreso basado en tiempo transcurrido
                    time_since_start = time.time() - dataset.last_updated
                    progress = min(0.95, time_since_start / 300.0)  # Asumir 5 minutos para completar
                    downloaded_bytes = int(progress * dataset.size_bytes) if dataset.size_bytes > 0 else 0
                    speed_mbps = 50.0  # Simulado
                    eta_seconds = int((1 - progress) * 300) if progress < 1 else 0
                elif dataset.status == "completed":
                    progress = 1.0
                    downloaded_bytes = dataset.size_bytes
                    speed_mbps = None
                    eta_seconds = 0
                else:
                    progress = 0.0
                    downloaded_bytes = 0
                    speed_mbps = None
                    eta_seconds = None

                return DownloadProgressResponse(
                    dataset_id=dataset_id,
                    status=dataset.status,
                    progress_percentage=progress * 100,
                    downloaded_bytes=downloaded_bytes,
                    total_bytes=dataset.size_bytes,
                    estimated_time_remaining=eta_seconds,
                    current_speed_mbps=speed_mbps
                )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error obteniendo progreso de descarga: {str(e)}")

        @self.app.options("/datasets/{dataset_id}/download/cancel")
        async def options_cancel_download(dataset_id: str):
            """OPTIONS handler for cancelling download."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/datasets/{dataset_id}/download/cancel")
        async def cancel_download(dataset_id: str):
            """Cancelar descarga de un dataset masivo."""
            try:
                dataset = massive_data_marketplace.massive_datasets.get(dataset_id)
                if not dataset:
                    raise HTTPException(status_code=404, detail="Dataset no encontrado")

                if dataset.status != "downloading":
                    raise HTTPException(status_code=400, detail="Dataset no está descargándose")

                # Aquí iría la lógica real para cancelar descarga
                dataset.status = "cancelled"
                dataset.error_message = "Descarga cancelada por usuario"

                # Broadcast cancellation update
                await self.broadcast_dataset_progress(dataset_id, "download")

                return {"success": True, "message": "Descarga cancelada"}
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error cancelando descarga: {str(e)}")

        # ===== CHUNK MANAGEMENT =====

        @self.app.get("/datasets/{dataset_id}/chunks", response_model=ChunkManagementResponse)
        async def get_dataset_chunks(dataset_id: str):
            """Obtener información de chunks de un dataset masivo."""
            try:
                dataset = massive_data_marketplace.massive_datasets.get(dataset_id)
                if not dataset:
                    raise HTTPException(status_code=404, detail="Dataset no encontrado")

                # Simular chunks basados en chunks_created
                chunks = []
                if dataset.chunks_created > 0:
                    chunk_size = dataset.size_bytes // dataset.chunks_created if dataset.size_bytes > 0 else 1024*1024
                    for i in range(dataset.chunks_created):
                        # Simular estado de chunks
                        if dataset.status == "completed":
                            status = "uploaded"
                            progress = 1.0
                            cid = f"Qm{dataset.dataset_id[:44]}_chunk_{i}"
                        elif dataset.status == "distributing":
                            status = "uploading" if i % 3 != 0 else "uploaded"
                            progress = 0.5 if status == "uploading" else 1.0
                            cid = f"Qm{dataset.dataset_id[:44]}_chunk_{i}" if status == "uploaded" else None
                        else:
                            status = "pending"
                            progress = 0.0
                            cid = None

                        chunks.append(ChunkInfo(
                            chunk_id=f"{dataset_id}_chunk_{i}",
                            index=i,
                            size_bytes=chunk_size,
                            ipfs_cid=cid,
                            status=status,
                            upload_progress=progress
                        ))

                return ChunkManagementResponse(
                    dataset_id=dataset_id,
                    total_chunks=dataset.chunks_created,
                    completed_chunks=len([c for c in chunks if c.status == "uploaded"]),
                    chunks=chunks
                )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error obteniendo chunks: {str(e)}")

        @self.app.get("/datasets/{dataset_id}/chunks/{chunk_index}")
        async def get_chunk_details(dataset_id: str, chunk_index: int):
            """Obtener detalles de un chunk específico."""
            try:
                dataset = massive_data_marketplace.massive_datasets.get(dataset_id)
                if not dataset:
                    raise HTTPException(status_code=404, detail="Dataset no encontrado")

                if chunk_index >= dataset.chunks_created:
                    raise HTTPException(status_code=404, detail="Chunk no encontrado")

                # Simular detalles del chunk
                chunk_size = dataset.size_bytes // dataset.chunks_created if dataset.size_bytes > 0 else 1024*1024

                if dataset.status == "completed":
                    status = "uploaded"
                    progress = 1.0
                    cid = f"Qm{dataset.dataset_id[:44]}_chunk_{chunk_index}"
                elif dataset.status == "distributing":
                    status = "uploading"
                    progress = 0.7
                    cid = None
                else:
                    status = "pending"
                    progress = 0.0
                    cid = None

                return {
                    "chunk_id": f"{dataset_id}_chunk_{chunk_index}",
                    "dataset_id": dataset_id,
                    "index": chunk_index,
                    "size_bytes": chunk_size,
                    "ipfs_cid": cid,
                    "status": status,
                    "upload_progress": progress,
                    "last_updated": dataset.last_updated
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error obteniendo detalles del chunk: {str(e)}")

        @self.app.post("/datasets/{dataset_id}/chunks/{chunk_index}/retry")
        async def retry_chunk_upload(dataset_id: str, chunk_index: int):
            """Reintentar subida de un chunk fallido."""
            try:
                dataset = massive_data_marketplace.massive_datasets.get(dataset_id)
                if not dataset:
                    raise HTTPException(status_code=404, detail="Dataset no encontrado")

                if chunk_index >= dataset.chunks_created:
                    raise HTTPException(status_code=404, detail="Chunk no encontrado")

                # Aquí iría la lógica real para reintentar subida
                # Por ahora, simular
                return {
                    "success": True,
                    "message": f"Reintento de subida iniciado para chunk {chunk_index}",
                    "chunk_id": f"{dataset_id}_chunk_{chunk_index}"
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error reintentando subida del chunk: {str(e)}")

        # ===== IPFS DISTRIBUTION STATUS =====

        @self.app.get("/datasets/{dataset_id}/ipfs-status", response_model=IPFSDistributionStatus)
        async def get_ipfs_distribution_status(dataset_id: str):
            """Obtener estado de distribución IPFS de un dataset."""
            try:
                data = await self._get_ipfs_data(dataset_id)
                if "error" in data:
                    raise HTTPException(status_code=404, detail=data["error"])

                return IPFSDistributionStatus(**data)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error obteniendo estado IPFS: {str(e)}")

        @self.app.post("/datasets/{dataset_id}/ipfs/distribute")
        async def trigger_ipfs_distribution(dataset_id: str, background_tasks: BackgroundTasks):
            """Disparar distribución IPFS manual para un dataset."""
            try:
                dataset = massive_data_marketplace.massive_datasets.get(dataset_id)
                if not dataset:
                    raise HTTPException(status_code=404, detail="Dataset no encontrado")

                if dataset.status == "distributing":
                    raise HTTPException(status_code=409, detail="Distribución ya en progreso")

                if not dataset.local_path:
                    raise HTTPException(status_code=400, detail="Dataset no tiene ruta local para distribución")

                # Iniciar distribución real en background
                background_tasks.add_task(self._distribute_dataset_ipfs, dataset_id)

                # Broadcast initial distribution update
                await self.broadcast_dataset_progress(dataset_id, "ipfs")

                return {
                    "success": True,
                    "message": "Distribución IPFS iniciada",
                    "dataset_id": dataset_id
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error iniciando distribución IPFS: {str(e)}")

        # ===== WEBSOCKET ENDPOINTS =====

        @self.app.websocket("/ws/datahub/{dataset_id}")
        async def websocket_datahub_endpoint(websocket: WebSocket, dataset_id: str, client_id: str = None):
            """WebSocket endpoint for real-time Data Hub progress updates."""
            if not client_id:
                client_id = f"client_{int(time.time())}_{hash(str(websocket)) % 10000}"

            await self._handle_websocket_connection(websocket, client_id, dataset_id)

    async def _handle_websocket_connection(self, websocket: WebSocket, client_id: str, dataset_id: str):
        """Handle WebSocket connection for dataset progress updates."""
        await websocket.accept()
        self.websocket_connections[client_id] = websocket

        # Subscribe client to dataset updates
        if dataset_id not in self.dataset_subscriptions:
            self.dataset_subscriptions[dataset_id] = []
        if client_id not in self.dataset_subscriptions[dataset_id]:
            self.dataset_subscriptions[dataset_id].append(client_id)

        logger.info(f"📡 Data Hub WebSocket client connected: {client_id} for dataset: {dataset_id}")

        try:
            # Send initial status
            await self._send_initial_dataset_status(websocket, dataset_id)

            # Keep connection alive and handle client messages
            while True:
                try:
                    # Wait for client messages with timeout
                    message = await asyncio.wait_for(
                        websocket.receive_json(),
                        timeout=30.0  # 30 second timeout
                    )

                    # Handle client requests
                    await self._handle_websocket_message(websocket, client_id, dataset_id, message)

                except asyncio.TimeoutError:
                    # Send periodic updates
                    await self._send_dataset_update(websocket, client_id, dataset_id)
                except Exception as e:
                    logger.error(f"Error handling WebSocket message from {client_id}: {e}")
                    break

        except WebSocketDisconnect:
            logger.info(f"📡 Data Hub WebSocket client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"WebSocket connection error for {client_id}: {e}")
        finally:
            # Clean up connection
            if client_id in self.websocket_connections:
                del self.websocket_connections[client_id]

            # Remove from subscriptions
            if dataset_id in self.dataset_subscriptions and client_id in self.dataset_subscriptions[dataset_id]:
                self.dataset_subscriptions[dataset_id].remove(client_id)
                if not self.dataset_subscriptions[dataset_id]:
                    del self.dataset_subscriptions[dataset_id]

    async def _handle_websocket_message(self, websocket: WebSocket, client_id: str, dataset_id: str, message: Dict[str, Any]):
        """Handle incoming WebSocket messages from clients."""
        try:
            message_type = message.get("type", "unknown")

            if message_type == "subscribe":
                # Client subscribing to specific updates
                subscriptions = message.get("subscriptions", ["download", "chunks", "ipfs"])
                logger.info(f"Client {client_id} subscribed to: {subscriptions}")

                # Send confirmation
                await websocket.send_json({
                    "type": "subscription_confirmed",
                    "dataset_id": dataset_id,
                    "subscriptions": subscriptions,
                    "timestamp": time.time()
                })

            elif message_type == "request_status":
                # Client requesting current status
                await self._send_dataset_update(websocket, client_id, dataset_id)

            elif message_type == "unsubscribe":
                # Client unsubscribing
                logger.info(f"Client {client_id} unsubscribed from dataset {dataset_id}")

            else:
                logger.warning(f"Unknown WebSocket message type from {client_id}: {message_type}")

        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await websocket.send_json({
                "type": "error",
                "message": f"Error processing message: {e}",
                "timestamp": time.time()
            })

    async def _send_initial_dataset_status(self, websocket: WebSocket, dataset_id: str):
        """Send initial dataset status to new client."""
        try:
            dataset = massive_data_marketplace.massive_datasets.get(dataset_id)
            if not dataset:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Dataset {dataset_id} not found",
                    "timestamp": time.time()
                })
                return

            # Get current progress data
            download_progress = await self._get_download_progress_data(dataset_id)
            chunk_data = await self._get_chunk_data(dataset_id)
            ipfs_data = await self._get_ipfs_data(dataset_id)

            await websocket.send_json({
                "type": "initial_status",
                "dataset_id": dataset_id,
                "timestamp": time.time(),
                "data": {
                    "download_progress": download_progress,
                    "chunks": chunk_data,
                    "ipfs_distribution": ipfs_data
                }
            })

        except Exception as e:
            logger.error(f"Error sending initial status: {e}")

    async def _send_dataset_update(self, websocket: WebSocket, client_id: str, dataset_id: str):
        """Send dataset update to specific client."""
        try:
            dataset = massive_data_marketplace.massive_datasets.get(dataset_id)
            if not dataset:
                return

            # Get current progress data
            download_progress = await self._get_download_progress_data(dataset_id)
            chunk_data = await self._get_chunk_data(dataset_id)
            ipfs_data = await self._get_ipfs_data(dataset_id)

            await websocket.send_json({
                "type": "dataset_update",
                "dataset_id": dataset_id,
                "timestamp": time.time(),
                "data": {
                    "download_progress": download_progress,
                    "chunks": chunk_data,
                    "ipfs_distribution": ipfs_data
                }
            })

        except Exception as e:
            logger.error(f"Error sending dataset update to {client_id}: {e}")

    async def _get_download_progress_data(self, dataset_id: str) -> Dict[str, Any]:
        """Get download progress data for a dataset."""
        try:
            dataset = massive_data_marketplace.massive_datasets.get(dataset_id)
            if not dataset:
                return {"error": "Dataset not found"}

            # Simulate progress based on status (same logic as REST endpoint)
            if dataset.status == "downloading":
                time_since_start = time.time() - dataset.last_updated
                progress = min(0.95, time_since_start / 300.0)
                downloaded_bytes = int(progress * dataset.size_bytes) if dataset.size_bytes > 0 else 0
                speed_mbps = 50.0
                eta_seconds = int((1 - progress) * 300) if progress < 1 else 0
            elif dataset.status == "completed":
                progress = 1.0
                downloaded_bytes = dataset.size_bytes
                speed_mbps = None
                eta_seconds = 0
            else:
                progress = 0.0
                downloaded_bytes = 0
                speed_mbps = None
                eta_seconds = None

            return {
                "dataset_id": dataset_id,
                "status": dataset.status,
                "progress_percentage": progress * 100,
                "downloaded_bytes": downloaded_bytes,
                "total_bytes": dataset.size_bytes,
                "estimated_time_remaining": eta_seconds,
                "current_speed_mbps": speed_mbps
            }
        except Exception as e:
            logger.error(f"Error getting download progress data: {e}")
            return {"error": str(e)}

    async def _get_chunk_data(self, dataset_id: str) -> Dict[str, Any]:
        """Get chunk data for a dataset."""
        try:
            dataset = massive_data_marketplace.massive_datasets.get(dataset_id)
            if not dataset:
                return {"error": "Dataset not found"}

            chunks = []
            if dataset.chunks_created > 0:
                chunk_size = dataset.size_bytes // dataset.chunks_created if dataset.size_bytes > 0 else 1024 * 1024
                distributed_chunks = int(dataset.metadata.get("ipfs_distributed_chunks", 0))
                manifest_chunks = dataset.metadata.get("ipfs_chunks") or []
                cid_lookup = {chunk.get("index"): chunk.get("cid") for chunk in manifest_chunks}
                for i in range(dataset.chunks_created):
                    if dataset.status == "completed" or i < distributed_chunks:
                        status = "uploaded"
                        progress = 1.0
                        cid = cid_lookup.get(i)
                    elif dataset.status == "distributing" and i == distributed_chunks:
                        status = "uploading"
                        progress = 0.5
                        cid = None
                    else:
                        status = "pending"
                        progress = 0.0
                        cid = None

                    chunks.append({
                        "chunk_id": f"{dataset_id}_chunk_{i}",
                        "index": i,
                        "size_bytes": chunk_size,
                        "ipfs_cid": cid,
                        "status": status,
                        "upload_progress": progress
                    })

            return {
                "dataset_id": dataset_id,
                "total_chunks": dataset.chunks_created,
                "completed_chunks": len([c for c in chunks if c["status"] == "uploaded"]),
                "chunks": chunks
            }
        except Exception as e:
            logger.error(f"Error getting chunk data: {e}")
            return {"error": str(e)}

    async def _get_ipfs_data(self, dataset_id: str) -> Dict[str, Any]:
        """Get IPFS distribution data for a dataset."""
        try:
            dataset = massive_data_marketplace.massive_datasets.get(dataset_id)
            if not dataset:
                return {"error": "Dataset not found"}

            if dataset.status == "completed" and dataset.ipfs_cid:
                distribution_status = "completed"
                distributed_chunks = int(dataset.metadata.get("ipfs_distributed_chunks", dataset.chunks_created))
                progress = 1.0 if dataset.chunks_created else 0.0
                eta = 0
            elif dataset.status == "distributing":
                distribution_status = "in_progress"
                distributed_chunks = int(dataset.metadata.get("ipfs_distributed_chunks", 0))
                total_chunks = dataset.metadata.get("ipfs_total_chunks", dataset.chunks_created)
                progress = (distributed_chunks / total_chunks) if total_chunks else 0.0
                started_at = dataset.metadata.get("ipfs_started_at")
                if started_at and distributed_chunks > 0:
                    elapsed = time.time() - started_at
                    per_chunk = elapsed / distributed_chunks
                    eta = int((total_chunks - distributed_chunks) * per_chunk)
                else:
                    eta = None
            elif dataset.status == "chunking":
                distribution_status = "in_progress"
                distributed_chunks = 0
                progress = 0.2
                eta = 300
            elif dataset.status == "failed":
                distribution_status = "failed"
                distributed_chunks = int(dataset.metadata.get("ipfs_distributed_chunks", 0))
                progress = 0.0
                eta = None
            else:
                distribution_status = "not_started"
                distributed_chunks = 0
                progress = 0.0
                eta = None

            total_chunks = dataset.metadata.get("ipfs_total_chunks", dataset.chunks_created)

            return {
                "dataset_id": dataset_id,
                "distribution_status": distribution_status,
                "total_chunks": total_chunks,
                "distributed_chunks": distributed_chunks,
                "ipfs_cid": dataset.ipfs_cid,
                "distribution_progress": progress * 100,
                "estimated_completion_time": eta
            }
        except Exception as e:
            logger.error(f"Error getting IPFS data: {e}")
            return {"error": str(e)}

    async def _distribute_dataset_ipfs(self, dataset_id: str):
        """Distribuir dataset real a IPFS con progreso incremental."""
        dataset = massive_data_marketplace.massive_datasets.get(dataset_id)
        if not dataset:
            return

        file_path = Path(dataset.local_path or "")
        if not file_path.exists():
            dataset.status = "failed"
            dataset.error_message = "Archivo del dataset no encontrado"
            await self.broadcast_dataset_progress(dataset_id, "ipfs")
            return

        config = get_config()
        chunk_size = config.data.chunk_size_mb * 1024 * 1024
        total_size = file_path.stat().st_size
        total_chunks = max(1, math.ceil(total_size / chunk_size))

        dataset.status = "distributing"
        dataset.error_message = None
        dataset.size_bytes = total_size
        dataset.chunks_created = total_chunks
        dataset.metadata.update({
            "ipfs_total_chunks": total_chunks,
            "ipfs_distributed_chunks": 0,
            "ipfs_started_at": time.time(),
            "ipfs_chunk_size": chunk_size
        })
        self.system_stats["active_distributions"] += 1
        await self.broadcast_dataset_progress(dataset_id, "ipfs")

        ipfs_manager = await self._get_ipfs_manager()
        manifest_chunks: List[Dict[str, Any]] = []

        try:
            with open(file_path, "rb") as handle:
                index = 0
                offset = 0
                while True:
                    chunk = handle.read(chunk_size)
                    if not chunk:
                        break

                    chunk_cid = await ipfs_manager.publish_data(
                        chunk,
                        metadata={
                            "dataset_id": dataset_id,
                            "chunk_index": index,
                            "total_chunks": total_chunks,
                            "filename": file_path.name,
                            "size": len(chunk)
                        }
                    )

                    manifest_chunks.append({
                        "index": index,
                        "cid": chunk_cid,
                        "size": len(chunk),
                        "offset": offset
                    })
                    index += 1
                    offset += len(chunk)

                    dataset.metadata["ipfs_distributed_chunks"] = index
                    dataset.metadata["ipfs_last_update"] = time.time()
                    await self.broadcast_dataset_progress(dataset_id, "ipfs")

            dataset.metadata["ipfs_chunks"] = manifest_chunks

            manifest = {
                "version": "1.0",
                "dataset_id": dataset_id,
                "filename": file_path.name,
                "total_size": total_size,
                "chunk_size": chunk_size,
                "total_chunks": total_chunks,
                "chunks": manifest_chunks,
                "created_at": datetime.utcnow().isoformat()
            }
            manifest_cid = await ipfs_manager.publish_data(
                json.dumps(manifest).encode("utf-8"),
                metadata={
                    "type": "dataset_manifest",
                    "dataset_id": dataset_id,
                    "total_chunks": total_chunks
                }
            )

            dataset.ipfs_cid = manifest_cid
            dataset.status = "completed"
            dataset.metadata["ipfs_manifest_cid"] = manifest_cid
            dataset.metadata["ipfs_completed_at"] = time.time()
            await self.broadcast_dataset_progress(dataset_id, "all")

            logger.info(f"✅ IPFS distribution completed for dataset: {dataset_id}")
        except Exception as e:
            dataset.status = "failed"
            dataset.error_message = str(e)
            logger.error(f"❌ Error in IPFS distribution: {e}")
            await self.broadcast_dataset_progress(dataset_id, "ipfs")
        finally:
            self.system_stats["active_distributions"] = max(
                0, self.system_stats["active_distributions"] - 1
            )

    async def broadcast_dataset_progress(self, dataset_id: str, progress_type: str = "all"):
        """Broadcast progress updates to all subscribed clients for a dataset."""
        if dataset_id not in self.dataset_subscriptions:
            return

        client_ids = self.dataset_subscriptions[dataset_id].copy()
        disconnected_clients = []

        for client_id in client_ids:
            if client_id not in self.websocket_connections:
                disconnected_clients.append(client_id)
                continue

            websocket = self.websocket_connections[client_id]
            try:
                if progress_type in ["all", "download"]:
                    download_data = await self._get_download_progress_data(dataset_id)
                    await websocket.send_json({
                        "type": "download_progress",
                        "dataset_id": dataset_id,
                        "timestamp": time.time(),
                        "data": download_data
                    })

                if progress_type in ["all", "chunks"]:
                    chunk_data = await self._get_chunk_data(dataset_id)
                    await websocket.send_json({
                        "type": "chunk_update",
                        "dataset_id": dataset_id,
                        "timestamp": time.time(),
                        "data": chunk_data
                    })

                if progress_type in ["all", "ipfs"]:
                    ipfs_data = await self._get_ipfs_data(dataset_id)
                    await websocket.send_json({
                        "type": "ipfs_update",
                        "dataset_id": dataset_id,
                        "timestamp": time.time(),
                        "data": ipfs_data
                    })

            except Exception as e:
                logger.warning(f"Failed to send update to client {client_id}: {e}")
                disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            if client_id in self.dataset_subscriptions[dataset_id]:
                self.dataset_subscriptions[dataset_id].remove(client_id)
            if client_id in self.websocket_connections:
                del self.websocket_connections[client_id]

        if not self.dataset_subscriptions[dataset_id]:
            del self.dataset_subscriptions[dataset_id]

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


# Instancia global de la API
datahub_api = DataHubAPI()


def create_datahub_app() -> FastAPI:
    """Función de conveniencia para crear la app FastAPI."""
    return datahub_api.create_app()


if __name__ == "__main__":
    # Iniciar servidor para pruebas
    print("🚀 Iniciando AILOOS Data Hub API...")
    datahub_api.start_server()
