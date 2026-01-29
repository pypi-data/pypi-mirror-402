"""
DataHub API - API REST para acceso al catálogo de datasets
==========================================================

API REST completa que proporciona acceso al sistema DataHub,
incluyendo registro de datasets, descargas, validación y gestión.
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks, Request
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..core.logging import get_logger
from ..coordinator.database.connection import get_db
from ..coordinator.auth.dependencies import conditional_user_auth
from .registry import DatasetRegistry
from .downloader import DatasetDownloader, DownloadConfig
from .validator import DatasetValidator, ValidationConfig
from .manager import DatasetManager, CacheConfig
from .models import Dataset

logger = get_logger(__name__)


# Modelos Pydantic para requests/responses

class DatasetCreateRequest(BaseModel):
    """Request para crear un nuevo dataset."""
    name: str = Field(..., description="Nombre único del dataset")
    description: Optional[str] = Field(None, description="Descripción del dataset")
    ipfs_cid: str = Field(..., description="CID de IPFS del dataset")
    sha256_hash: str = Field(..., description="Hash SHA256 para verificación")
    file_size_bytes: int = Field(..., description="Tamaño del archivo en bytes")
    dataset_type: str = Field(..., description="Tipo de dataset (text, image, tabular, etc.)")
    format: str = Field(..., description="Formato del archivo")
    version: Optional[str] = Field("1.0.0", description="Versión del dataset")
    creator: Optional[str] = Field(None, description="Creador del dataset")
    license: Optional[str] = Field(None, description="Licencia del dataset")
    tags: Optional[List[str]] = Field(None, description="Tags para categorización")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadatos adicionales")
    compression: Optional[str] = Field(None, description="Tipo de compresión")
    num_samples: Optional[int] = Field(None, description="Número de muestras")
    num_features: Optional[int] = Field(None, description="Número de características")
    chunk_count: Optional[int] = Field(1, description="Número de chunks")


class DatasetUpdateRequest(BaseModel):
    """Request para actualizar un dataset."""
    description: Optional[str] = None
    version: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    num_samples: Optional[int] = None
    num_features: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    creator: Optional[str] = None
    license: Optional[str] = None
    tags: Optional[List[str]] = None


class DownloadRequest(BaseModel):
    """Request para descargar un dataset."""
    dataset_id: int = Field(..., description="ID del dataset")
    output_path: str = Field(..., description="Ruta donde guardar el dataset")
    validate: Optional[bool] = Field(True, description="Validar después de descargar")
    node_id: Optional[str] = Field(None, description="ID del nodo solicitante")


class ValidationRequest(BaseModel):
    """Request para validar un dataset."""
    dataset_id: int = Field(..., description="ID del dataset")
    file_path: str = Field(..., description="Ruta del archivo a validar")
    validator_version: Optional[str] = Field("1.0.0", description="Versión del validador")
    validated_by: Optional[str] = Field(None, description="Sistema/usuario validador")


class DatasetResponse(BaseModel):
    """Response con información de un dataset."""
    id: int
    name: str
    description: Optional[str]
    version: str
    ipfs_cid: str
    ipfs_gateway_url: Optional[str]
    sha256_hash: str
    file_size_bytes: int
    chunk_count: int
    dataset_type: str
    format: str
    compression: Optional[str]
    num_samples: Optional[int]
    num_features: Optional[int]
    metadata: Optional[Dict[str, Any]]
    is_active: bool
    is_verified: bool
    download_count: int
    creator: Optional[str]
    license: Optional[str]
    tags: Optional[List[str]]
    created_at: str
    updated_at: str
    last_downloaded_at: Optional[str]


class DownloadResponse(BaseModel):
    """Response de una operación de descarga."""
    success: bool
    dataset_id: Optional[int] = None
    dataset_name: Optional[str] = None
    output_path: Optional[str] = None
    bytes_downloaded: Optional[int] = None
    duration_ms: Optional[float] = None
    chunks_downloaded: Optional[int] = None
    download_id: Optional[str] = None
    error: Optional[str] = None


class ValidationResponse(BaseModel):
    """Response de una operación de validación."""
    dataset_id: int
    is_integrity_valid: bool
    is_quality_valid: bool
    validation_score: float
    integrity_errors: Optional[List[str]] = None
    quality_metrics: Optional[Dict[str, Any]] = None
    validation_report: Optional[Dict[str, Any]] = None
    validator_version: str
    validated_by: Optional[str] = None
    created_at: str


class StatsResponse(BaseModel):
    """Response con estadísticas del sistema."""
    total_datasets: int
    active_datasets: int
    verified_datasets: int
    total_downloads: int
    total_size_bytes: int
    datasets_by_type: List[Dict[str, Any]]


class DataHubAPI:
    """
    API REST completa para el sistema DataHub.

    Proporciona endpoints para todas las operaciones del sistema:
    - Gestión del catálogo de datasets
    - Descargas seguras desde IPFS
    - Validación de integridad y calidad
    - Gestión de cache y almacenamiento local
    """

    def __init__(self):
        self.app = FastAPI(
            title="AILOOS DataHub API",
            description="API REST completa para gestión de datasets en el sistema DataHub",
            version="1.0.0"
        )

        # Componentes del sistema (se inicializarán con dependencias)
        self.registry: Optional[DatasetRegistry] = None
        self.downloader: Optional[DatasetDownloader] = None
        self.validator: Optional[DatasetValidator] = None
        self.manager: Optional[DatasetManager] = None

        # Estado del sistema
        self.system_stats = {
            "start_time": datetime.now(),
            "total_requests": 0,
            "active_operations": 0
        }

        logger.info("🚀 DataHub API initialized")

        # Configurar rutas
        self._setup_routes()
        self._setup_middleware()

    def _setup_middleware(self):
        """Configurar middleware de la aplicación."""
        @self.app.middleware("http")
        async def add_request_tracking(request: Request, call_next):
            self.system_stats["total_requests"] += 1
            response = await call_next(request)
            return response

    def _setup_routes(self):
        """Configurar todas las rutas de la API."""

        # Dependencias
        def get_registry(db: Session = Depends(get_db)) -> DatasetRegistry:
            if not self.registry:
                self.registry = DatasetRegistry(db)
            return self.registry

        def get_downloader(registry: DatasetRegistry = Depends(get_registry)) -> DatasetDownloader:
            if not self.downloader:
                # Aquí necesitaríamos IPFSManager - por ahora creamos básico
                from ..infrastructure.ipfs_embedded import IPFSManager
                ipfs_manager = IPFSManager()
                self.downloader = DatasetDownloader(ipfs_manager, registry)
            return self.downloader

        def get_validator(registry: DatasetRegistry = Depends(get_registry)) -> DatasetValidator:
            if not self.validator:
                self.validator = DatasetValidator(registry)
            return self.validator

        def get_manager(registry: DatasetRegistry = Depends(get_registry),
                       downloader: DatasetDownloader = Depends(get_downloader),
                       validator: DatasetValidator = Depends(get_validator)) -> DatasetManager:
            if not self.manager:
                self.manager = DatasetManager(registry, downloader, validator)
            return self.manager

        # ===== HEALTH CHECK =====

        @self.app.get("/health")
        async def health_check():
            """Health check del sistema DataHub."""
            uptime = datetime.now() - self.system_stats["start_time"]

            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": uptime.total_seconds(),
                "total_requests": self.system_stats["total_requests"],
                "active_operations": self.system_stats["active_operations"],
                "version": "1.0.0"
            }

        # ===== DATASET MANAGEMENT =====

        @self.app.post("/api/datasets", response_model=DatasetResponse)
        async def create_dataset(request: DatasetCreateRequest,
                                current_user: Optional[Dict] = Depends(conditional_user_auth),
                                registry: DatasetRegistry = Depends(get_registry)):
            """Crear un nuevo dataset en el catálogo."""
            try:
                dataset = registry.register_dataset(
                    name=request.name,
                    ipfs_cid=request.ipfs_cid,
                    sha256_hash=request.sha256_hash,
                    file_size_bytes=request.file_size_bytes,
                    dataset_type=request.dataset_type,
                    format=request.format,
                    description=request.description,
                    version=request.version,
                    creator=request.creator,
                    license=request.license,
                    tags=request.tags,
                    metadata=request.metadata,
                    compression=request.compression,
                    num_samples=request.num_samples,
                    num_features=request.num_features,
                    chunk_count=request.chunk_count
                )

                return DatasetResponse(**dataset.to_dict())

            except Exception as e:
                logger.error(f"❌ Error creating dataset: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/api/datasets", response_model=List[DatasetResponse])
        async def list_datasets(
            active_only: bool = Query(True, description="Solo datasets activos"),
            verified_only: bool = Query(False, description="Solo datasets verificados"),
            dataset_type: Optional[str] = Query(None, description="Filtrar por tipo"),
            creator: Optional[str] = Query(None, description="Filtrar por creador"),
            limit: int = Query(50, ge=1, le=200, description="Límite de resultados"),
            offset: int = Query(0, ge=0, description="Desplazamiento"),
            current_user: Optional[Dict] = Depends(conditional_user_auth),
            registry: DatasetRegistry = Depends(get_registry)
        ):
            """Listar datasets con filtros opcionales."""
            try:
                datasets = registry.list_datasets(
                    active_only=active_only,
                    verified_only=verified_only,
                    dataset_type=dataset_type,
                    creator=creator,
                    limit=limit,
                    offset=offset
                )

                return [DatasetResponse(**ds.to_dict()) for ds in datasets]

            except Exception as e:
                logger.error(f"❌ Error listing datasets: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/datasets/{dataset_id}", response_model=DatasetResponse)
        async def get_dataset(dataset_id: int, current_user: Optional[Dict] = Depends(conditional_user_auth), registry: DatasetRegistry = Depends(get_registry)):
            """Obtener detalles de un dataset específico."""
            try:
                dataset = registry.get_dataset(dataset_id)
                if not dataset:
                    raise HTTPException(status_code=404, detail="Dataset not found")

                return DatasetResponse(**dataset.to_dict())

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"❌ Error getting dataset {dataset_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.put("/api/datasets/{dataset_id}", response_model=DatasetResponse)
        async def update_dataset(dataset_id: int,
                                request: DatasetUpdateRequest,
                                current_user: Optional[Dict] = Depends(conditional_user_auth),
                                registry: DatasetRegistry = Depends(get_registry)):
            """Actualizar metadatos de un dataset."""
            try:
                update_data = request.dict(exclude_unset=True)
                dataset = registry.update_dataset(dataset_id, **update_data)

                if not dataset:
                    raise HTTPException(status_code=404, detail="Dataset not found")

                return DatasetResponse(**dataset.to_dict())

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"❌ Error updating dataset {dataset_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.delete("/api/datasets/{dataset_id}")
        async def delete_dataset(dataset_id: int, current_user: Optional[Dict] = Depends(conditional_user_auth), registry: DatasetRegistry = Depends(get_registry)):
            """Eliminar un dataset del catálogo (soft delete)."""
            try:
                success = registry.delete_dataset(dataset_id)
                if not success:
                    raise HTTPException(status_code=404, detail="Dataset not found")

                return {"success": True, "message": "Dataset deleted"}

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"❌ Error deleting dataset {dataset_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # ===== SEARCH =====

        @self.app.get("/api/datasets/search", response_model=List[DatasetResponse])
        async def search_datasets(query: str = Query(..., description="Término de búsqueda"),
                                limit: int = Query(20, ge=1, le=100, description="Límite de resultados"),
                                current_user: Optional[Dict] = Depends(conditional_user_auth),
                                registry: DatasetRegistry = Depends(get_registry)):
            """Buscar datasets por texto."""
            try:
                datasets = registry.search_datasets(query=query, limit=limit)
                return [DatasetResponse(**ds.to_dict()) for ds in datasets]

            except Exception as e:
                logger.error(f"❌ Error searching datasets: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # ===== DOWNLOAD OPERATIONS =====

        @self.app.post("/api/datasets/download", response_model=DownloadResponse)
        async def download_dataset(request: DownloadRequest,
                                  background_tasks: BackgroundTasks,
                                  current_user: Optional[Dict] = Depends(conditional_user_auth),
                                  manager: DatasetManager = Depends(get_manager)):
            """Descargar un dataset."""
            try:
                self.system_stats["active_operations"] += 1

                # Ejecutar descarga en background
                background_tasks.add_task(self._execute_download, request, manager)

                return DownloadResponse(
                    success=True,
                    dataset_id=request.dataset_id,
                    message="Download started in background"
                )

            except Exception as e:
                self.system_stats["active_operations"] -= 1
                logger.error(f"❌ Error starting download: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        async def _execute_download(self, request: DownloadRequest, manager: DatasetManager):
            """Ejecutar descarga en background."""
            try:
                result = await manager.get_dataset(
                    dataset_id=request.dataset_id,
                    validate=request.validate,
                    use_cache=True
                )

                # Aquí podríamos enviar notificaciones o actualizar estado
                logger.info(f"✅ Download completed for dataset {request.dataset_id}")

            except Exception as e:
                logger.error(f"❌ Background download failed for dataset {request.dataset_id}: {e}")
            finally:
                self.system_stats["active_operations"] -= 1

        @self.app.get("/api/download/progress/{download_id}")
        async def get_download_progress(download_id: str,
                                      current_user: Optional[Dict] = Depends(conditional_user_auth),
                                      downloader: DatasetDownloader = Depends(get_downloader)):
            """Obtener progreso de una descarga específica."""
            try:
                stats = downloader.get_download_stats(download_id)
                if not stats:
                    raise HTTPException(status_code=404, detail="Download not found")

                return stats

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"❌ Error getting download progress: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # ===== VALIDATION =====

        @self.app.post("/api/datasets/validate", response_model=ValidationResponse)
        async def validate_dataset(request: ValidationRequest,
                                  background_tasks: BackgroundTasks,
                                  current_user: Optional[Dict] = Depends(conditional_user_auth),
                                  validator: DatasetValidator = Depends(get_validator)):
            """Validar un dataset."""
            try:
                self.system_stats["active_operations"] += 1

                # Ejecutar validación
                validation = await validator.validate_dataset(
                    dataset_id=request.dataset_id,
                    file_path=request.file_path,
                    validator_version=request.validator_version,
                    validated_by=request.validated_by
                )

                self.system_stats["active_operations"] -= 1

                return ValidationResponse(
                    dataset_id=validation.dataset_id,
                    is_integrity_valid=validation.is_integrity_valid,
                    is_quality_valid=validation.is_quality_valid,
                    validation_score=validation.validation_score,
                    integrity_errors=validation.integrity_errors,
                    quality_metrics=validation.quality_metrics,
                    validation_report=validation.validation_report,
                    validator_version=validation.validator_version,
                    validated_by=validation.validated_by,
                    created_at=validation.created_at.isoformat()
                )

            except Exception as e:
                self.system_stats["active_operations"] -= 1
                logger.error(f"❌ Error validating dataset: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/datasets/{dataset_id}/validations")
        async def get_validation_history(dataset_id: int,
                                       limit: int = Query(10, ge=1, le=50, description="Límite de resultados"),
                                       current_user: Optional[Dict] = Depends(conditional_user_auth),
                                       validator: DatasetValidator = Depends(get_validator)):
            """Obtener historial de validaciones de un dataset."""
            try:
                validations = validator.get_validation_history(dataset_id, limit)
                return [ValidationResponse(
                    dataset_id=v.dataset_id,
                    is_integrity_valid=v.is_integrity_valid,
                    is_quality_valid=v.is_quality_valid,
                    validation_score=v.validation_score,
                    integrity_errors=v.integrity_errors,
                    quality_metrics=v.quality_metrics,
                    validation_report=v.validation_report,
                    validator_version=v.validator_version,
                    validated_by=v.validated_by,
                    created_at=v.created_at.isoformat()
                ) for v in validations]

            except Exception as e:
                logger.error(f"❌ Error getting validation history: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # ===== CACHE MANAGEMENT =====

        @self.app.get("/api/cache/info")
        async def get_cache_info(current_user: Optional[Dict] = Depends(conditional_user_auth), manager: DatasetManager = Depends(get_manager)):
            """Obtener información del cache."""
            try:
                return manager.get_cache_info()
            except Exception as e:
                logger.error(f"❌ Error getting cache info: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/cache/cleanup")
        async def cleanup_cache(force: bool = Query(False, description="Forzar limpieza"),
                              current_user: Optional[Dict] = Depends(conditional_user_auth),
                              manager: DatasetManager = Depends(get_manager)):
            """Limpiar cache."""
            try:
                result = await manager.cleanup_cache(force=force)
                return result
            except Exception as e:
                logger.error(f"❌ Error cleaning cache: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # ===== STATISTICS =====

        @self.app.get("/api/stats", response_model=StatsResponse)
        async def get_system_stats(current_user: Optional[Dict] = Depends(conditional_user_auth), registry: DatasetRegistry = Depends(get_registry)):
            """Obtener estadísticas del sistema."""
            try:
                stats = registry.get_dataset_stats()
                return StatsResponse(**stats)
            except Exception as e:
                logger.error(f"❌ Error getting system stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/stats/popular")
        async def get_popular_datasets(limit: int = Query(10, ge=1, le=50, description="Límite de resultados"),
                                     current_user: Optional[Dict] = Depends(conditional_user_auth),
                                     registry: DatasetRegistry = Depends(get_registry)):
            """Obtener datasets más populares."""
            try:
                datasets = registry.get_popular_datasets(limit)
                return [DatasetResponse(**ds.to_dict()) for ds in datasets]
            except Exception as e:
                logger.error(f"❌ Error getting popular datasets: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    def create_app(self) -> FastAPI:
        """Crear y retornar la aplicación FastAPI."""
        return self.app


# Instancia global de la API
datahub_api = DataHubAPI()


def create_datahub_app() -> FastAPI:
    """Función de conveniencia para crear la app FastAPI del DataHub."""
    return datahub_api.create_app()


if __name__ == "__main__":
    # Iniciar servidor para pruebas
    import uvicorn
    print("🚀 Iniciando AILOOS DataHub API...")
    uvicorn.run(
        datahub_api.app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )