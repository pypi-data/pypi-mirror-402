"""
API REST completa para gestión de modelos de AILOOS.
Proporciona endpoints para marketplace de modelos, gestión de modelos entrenados y operaciones de descarga/subida.
"""

import asyncio
import json
import time
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from ..coordinator.auth.dependencies import get_current_node, get_current_admin, get_current_user
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from ..core.config import get_config
from ..core.logging import get_logger

logger = get_logger(__name__)


# Modelos Pydantic para requests/responses
class ModelInfo(BaseModel):
    id: str
    name: str
    description: str
    type: str  # 'data' | 'llm'
    license: str  # 'public-domain' | 'mit' | 'apache' | 'wikipedia' | 'commercial'
    size_gb: float
    quality_score: float
    price_drs: Optional[float] = None
    provider: str
    tags: List[str] = []
    download_count: int
    status: str  # 'available' | 'downloading' | 'ready'
    download_progress: Optional[float] = None
    created_at: str
    updated_at: str

class ModelStats(BaseModel):
    total_models: int
    total_downloads: int
    active_providers: int
    average_quality: float

class ModelUploadRequest(BaseModel):
    name: str
    description: str
    type: str
    license: str
    size_gb: float
    quality_score: float
    price_drs: Optional[float] = None
    tags: List[str] = []
    file_path: str
    user_id: str

class ModelDownloadRequest(BaseModel):
    model_id: str
    user_id: str

class TrainingRequest(BaseModel):
    model_name: str
    dataset_id: str
    config: Dict[str, Any]
    user_id: str

class ModelsAPI:
    """
    API REST completa para gestión de modelos.
    Maneja marketplace de modelos, gestión de modelos entrenados y operaciones de descarga/subida.
    """

    def __init__(self):
        self.app = FastAPI(
            title="AILOOS Models API",
            description="API completa para gestión de modelos de IA y marketplace",
            version="1.0.0"
        )

        # Modelos de ejemplo para simulación
        self.models = [
            {
                "id": "model_001",
                "name": "GPT-2 Small",
                "description": "Modelo de lenguaje GPT-2 pequeño pre-entrenado",
                "type": "llm",
                "license": "mit",
                "size_gb": 0.5,
                "quality_score": 85,
                "price_drs": 100,
                "provider": "OpenAI",
                "tags": ["language", "generation", "gpt"],
                "download_count": 1250,
                "status": "available",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z"
            },
            {
                "id": "model_002",
                "name": "Wikipedia Dataset 9.3GB",
                "description": "Dataset completo de Wikipedia comprimido",
                "type": "data",
                "license": "wikipedia",
                "size_gb": 9.3,
                "quality_score": 95,
                "price_drs": 500,
                "provider": "Wikipedia Foundation",
                "tags": ["wikipedia", "text", "dataset"],
                "download_count": 340,
                "status": "available",
                "created_at": "2024-01-10T08:00:00Z",
                "updated_at": "2024-01-10T08:00:00Z"
            },
            {
                "id": "model_003",
                "name": "Stable Diffusion v1.5",
                "description": "Modelo de generación de imágenes Stable Diffusion",
                "type": "llm",
                "license": "apache",
                "size_gb": 4.2,
                "quality_score": 92,
                "price_drs": 200,
                "provider": "Stability AI",
                "tags": ["image", "generation", "diffusion"],
                "download_count": 890,
                "status": "available",
                "created_at": "2024-01-12T14:00:00Z",
                "updated_at": "2024-01-12T14:00:00Z"
            }
        ]

        # Modelos de usuario
        self.user_models = []

        # Estadísticas del sistema
        self.system_stats = {
            "total_models": len(self.models),
            "total_downloads": sum(m["download_count"] for m in self.models),
            "active_providers": len(set(m["provider"] for m in self.models)),
            "average_quality": sum(m["quality_score"] for m in self.models) / len(self.models)
        }

        logger.info("🧠 Models API initialized")

        # Configurar rutas
        self._setup_routes()

    def _setup_routes(self):
        """Configurar todas las rutas de la API."""

        @self.app.get("/health")
        async def health_check():
            """Health check del servicio de modelos."""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "total_models": len(self.models),
                "total_user_models": len(self.user_models),
                "version": "1.0.0"
            }

        # ===== MODEL MARKETPLACE ENDPOINTS =====

        @self.app.get("/marketplace")
        async def get_models(
            type_filter: str = Query("", description="Tipo de modelo: data, llm"),
            license_filter: str = Query("", description="Licencia del modelo"),
            min_quality: float = Query(0, ge=0, le=100, description="Calidad mínima"),
            max_price: float = Query(None, description="Precio máximo"),
            limit: int = Query(50, ge=1, le=200, description="Límite de resultados")
        ):
            """Obtener lista de modelos disponibles en el marketplace."""
            try:
                filtered_models = self.models.copy()

                # Aplicar filtros
                if type_filter:
                    filtered_models = [m for m in filtered_models if m["type"] == type_filter]

                if license_filter:
                    filtered_models = [m for m in filtered_models if m["license"] == license_filter]

                if min_quality > 0:
                    filtered_models = [m for m in filtered_models if m["quality_score"] >= min_quality]

                if max_price is not None:
                    filtered_models = [m for m in filtered_models if m.get("price_drs", 0) <= max_price]

                # Limitar resultados
                filtered_models = filtered_models[:limit]

                return {"models": filtered_models, "total": len(filtered_models)}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error obteniendo modelos: {str(e)}")

        @self.app.get("/stats")
        async def get_model_stats():
            """Obtener estadísticas del marketplace de modelos."""
            try:
                return self.system_stats
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")

        @self.app.get("/api/models/{model_id}")
        async def get_model_details(model_id: str):
            """Obtener detalles de un modelo específico."""
            try:
                model = next((m for m in self.models if m["id"] == model_id), None)
                if not model:
                    raise HTTPException(status_code=404, detail="Modelo no encontrado")

                return model
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error obteniendo detalles del modelo: {str(e)}")

        @self.app.options("/api/models/{model_id}/download")
        async def options_download_model(model_id: str):
            """OPTIONS handler for model download."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/api/models/{model_id}/download")
        async def download_model(model_id: str, request: ModelDownloadRequest):
            """Iniciar descarga de un modelo."""
            try:
                model = next((m for m in self.models if m["id"] == model_id), None)
                if not model:
                    raise HTTPException(status_code=404, detail="Modelo no encontrado")

                # Simular inicio de descarga
                model["status"] = "downloading"
                model["download_progress"] = 0

                # Simular progreso de descarga en background
                asyncio.create_task(self._simulate_download(model_id))

                return {
                    "success": True,
                    "model_id": model_id,
                    "message": "Descarga iniciada",
                    "status": "downloading"
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error iniciando descarga: {str(e)}")

        # ===== MODEL MANAGEMENT ENDPOINTS =====

        @self.app.get("/api/models/user")
        async def get_user_models(user_id: str = Query(..., description="ID del usuario")):
            """Obtener modelos del usuario."""
            try:
                user_models = [m for m in self.user_models if m.get("user_id") == user_id]
                return {"models": user_models, "total": len(user_models)}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error obteniendo modelos del usuario: {str(e)}")

        @self.app.options("/api/models/upload")
        async def options_upload_model():
            """OPTIONS handler for model upload."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/api/models/upload")
        async def upload_model(request: ModelUploadRequest):
            """Subir un nuevo modelo."""
            try:
                # Crear nuevo modelo
                new_model = {
                    "id": f"user_model_{len(self.user_models) + 1}",
                    "name": request.name,
                    "description": request.description,
                    "type": request.type,
                    "license": request.license,
                    "size_gb": request.size_gb,
                    "quality_score": request.quality_score,
                    "price_drs": request.price_drs,
                    "provider": f"User {request.user_id}",
                    "tags": request.tags,
                    "download_count": 0,
                    "status": "ready",
                    "user_id": request.user_id,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }

                self.user_models.append(new_model)

                return {
                    "success": True,
                    "model_id": new_model["id"],
                    "message": "Modelo subido exitosamente"
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error subiendo modelo: {str(e)}")

        @self.app.options("/api/models/train")
        async def options_train_model():
            """OPTIONS handler for model training."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/api/models/train")
        async def train_model(request: TrainingRequest):
            """Iniciar entrenamiento de un modelo."""
            try:
                # Crear modelo en entrenamiento
                training_model = {
                    "id": f"training_{len(self.user_models) + 1}",
                    "name": request.model_name,
                    "description": f"Entrenamiento de {request.model_name}",
                    "type": "llm",  # Asumir LLM por ahora
                    "license": "mit",
                    "size_gb": 0,  # Se actualizará durante el entrenamiento
                    "quality_score": 0,
                    "provider": f"User {request.user_id}",
                    "tags": ["training", "custom"],
                    "download_count": 0,
                    "status": "training",
                    "training_progress": 0,
                    "training_config": request.config,
                    "user_id": request.user_id,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }

                self.user_models.append(training_model)

                # Simular progreso de entrenamiento
                asyncio.create_task(self._simulate_training(training_model["id"]))

                return {
                    "success": True,
                    "model_id": training_model["id"],
                    "message": "Entrenamiento iniciado",
                    "status": "training"
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error iniciando entrenamiento: {str(e)}")

        @self.app.get("/api/models/{model_id}/training-status")
        async def get_training_status(model_id: str):
            """Obtener estado de entrenamiento de un modelo."""
            try:
                model = next((m for m in self.user_models if m["id"] == model_id), None)
                if not model:
                    raise HTTPException(status_code=404, detail="Modelo no encontrado")

                return {
                    "model_id": model_id,
                    "status": model.get("status", "unknown"),
                    "progress": model.get("training_progress", 0),
                    "config": model.get("training_config", {}),
                    "updated_at": model.get("updated_at")
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error obteniendo estado de entrenamiento: {str(e)}")

        @self.app.options("/api/models/{model_id}/training/stop")
        async def options_stop_training(model_id: str):
            """OPTIONS handler for stopping training."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/api/models/{model_id}/training/stop")
        async def stop_training(model_id: str):
            """Detener entrenamiento de un modelo."""
            try:
                model = next((m for m in self.user_models if m["id"] == model_id), None)
                if not model:
                    raise HTTPException(status_code=404, detail="Modelo no encontrado")

                model["status"] = "stopped"
                model["updated_at"] = datetime.now().isoformat()

                return {
                    "success": True,
                    "model_id": model_id,
                    "message": "Entrenamiento detenido",
                    "status": "stopped"
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error deteniendo entrenamiento: {str(e)}")

        @self.app.delete("/api/models/{model_id}")
        async def delete_model(model_id: str):
            """Eliminar un modelo."""
            try:
                # Buscar en modelos del marketplace
                model_index = next((i for i, m in enumerate(self.models) if m["id"] == model_id), None)
                if model_index is not None:
                    del self.models[model_index]
                else:
                    # Buscar en modelos de usuario
                    user_model_index = next((i for i, m in enumerate(self.user_models) if m["id"] == model_id), None)
                    if user_model_index is not None:
                        del self.user_models[user_model_index]
                    else:
                        raise HTTPException(status_code=404, detail="Modelo no encontrado")

                return {
                    "success": True,
                    "model_id": model_id,
                    "message": "Modelo eliminado exitosamente"
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error eliminando modelo: {str(e)}")

    async def _simulate_download(self, model_id: str):
        """Simular progreso de descarga."""
        try:
            model = next((m for m in self.models if m["id"] == model_id), None)
            if not model:
                return

            # Simular descarga en pasos
            for progress in range(0, 101, 10):
                await asyncio.sleep(0.5)  # Simular tiempo de descarga
                model["download_progress"] = progress

            # Marcar como completado
            model["status"] = "ready"
            model["download_count"] += 1
            model["updated_at"] = datetime.now().isoformat()

        except Exception as e:
            logger.error(f"Error simulating download for {model_id}: {e}")

    async def _simulate_training(self, model_id: str):
        """Simular progreso de entrenamiento."""
        try:
            model = next((m for m in self.user_models if m["id"] == model_id), None)
            if not model:
                return

            # Simular entrenamiento en pasos
            for progress in range(0, 101, 5):
                await asyncio.sleep(1)  # Simular tiempo de entrenamiento
                model["training_progress"] = progress
                model["quality_score"] = min(100, progress + 20)  # Mejorar calidad con el progreso
                model["size_gb"] = progress * 0.1  # Aumentar tamaño
                model["updated_at"] = datetime.now().isoformat()

            # Marcar como completado
            model["status"] = "ready"
            model["updated_at"] = datetime.now().isoformat()

        except Exception as e:
            logger.error(f"Error simulating training for {model_id}: {e}")

    def create_app(self) -> FastAPI:
        """Crear y retornar la aplicación FastAPI."""
        return self.app

    def start_server(self, host: str = "0.0.0.0", port: int = 8002):
        """Iniciar servidor FastAPI."""
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )


# Instancia global de la API
models_api = ModelsAPI()


def create_models_app() -> FastAPI:
    """Función de conveniencia para crear la app FastAPI."""
    return models_api.create_app()


if __name__ == "__main__":
    # Iniciar servidor para pruebas
    print("🚀 Iniciando AILOOS Models API...")
    models_api.start_server()