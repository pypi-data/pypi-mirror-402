"""
API REST completa para el marketplace DracmaS de AILOOS.
Proporciona endpoints para wallets, transacciones, listings de datos y estadísticas.
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

from ..marketplace import marketplace, massive_data_marketplace, create_user_wallet, get_user_balance, list_available_datasets, show_market_stats
from ..marketplace.data_listing import DataCategory
from ..federated.session import FederatedSession
from ..federated.trainer import FederatedTrainer
from ..infrastructure.ipfs_embedded import IPFSManager
from ..core.config import get_config
from ..core.logging import get_logger

logger = get_logger(__name__)


# Modelos Pydantic para requests/responses
class WalletCreateRequest(BaseModel):
    user_id: str = Field(..., description="ID único del usuario")
    label: str = Field(default="default", description="Etiqueta para la dirección")


class WalletResponse(BaseModel):
    address: str
    balance_dracma: float
    staked_dracma: float
    total_value_dracma: float
    staking_multiplier: float
    estimated_daily_reward: float
    estimated_monthly_reward: float
    recent_transactions: int
    portfolio_health: str


class TransactionRequest(BaseModel):
    sender_id: str
    receiver_address: str
    amount: float
    description: str = ""


class DataListingRequest(BaseModel):
    seller_id: str
    title: str
    description: str
    category: str
    data_hash: str
    ipfs_cid: str
    price_dracma: float
    data_size_mb: float
    sample_count: int
    quality_score: float
    tags: List[str] = []
    duration_days: int = 30


class PurchaseRequest(BaseModel):
    buyer_id: str
    listing_id: str


class NodeRegistrationRequest(BaseModel):
    node_id: str
    hardware_info: Dict[str, Any]
    location: str = "unknown"


class TrainingSessionRequest(BaseModel):
    node_id: str
    session_id: str
    model_version: str = "1.0.0"


class TrainingUpdateRequest(BaseModel):
    session_id: str
    parameters_trained: int = 0
    accuracy: float
    loss: float
    status: str = "running"


class MarketplaceAPI:
    """
    API REST completa para el marketplace DRACMA.
    Maneja todas las operaciones del marketplace, federated learning y wallets.
    """

    def __init__(self):
        self.app = FastAPI(
            title="AILOOS Marketplace API",
            description="API completa para el marketplace DracmaS y federated learning",
            version="1.0.0"
        )

        # Componentes REALES del sistema
        self.ipfs_manager = IPFSManager()
        self.active_sessions: Dict[str, FederatedSession] = {}
        self.node_connections: Dict[str, Dict[str, Any]] = {}

        # Estadísticas del sistema
        self.system_stats = {
            "total_listings_created": 0,
            "total_purchases_made": 0,
            "total_nodes_registered": 0,
            "total_sessions_started": 0,
            "start_time": time.time()
        }

        logger.info("🛒 Marketplace API initialized with real components")

        # Configurar rutas
        self._setup_routes()

    def _setup_routes(self):
        """Configurar todas las rutas de la API."""

        @self.app.get("/health")
        async def health_check():
            """Health check REAL del servicio."""
            # Calcular uptime
            uptime_seconds = time.time() - self.system_stats["start_time"]
            uptime_hours = uptime_seconds / 3600

            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "active_nodes": len(self.node_connections),
                "active_sessions": len(self.active_sessions),
                "total_listings_created": self.system_stats["total_listings_created"],
                "total_purchases_made": self.system_stats["total_purchases_made"],
                "total_nodes_registered": self.system_stats["total_nodes_registered"],
                "total_sessions_started": self.system_stats["total_sessions_started"],
                "system_uptime_hours": f"{uptime_hours:.1f}",
                "marketplace_stats": show_market_stats(),
                "massive_datasets": {
                    "total": len(massive_data_marketplace.massive_datasets),
                    "active": len([d for d in massive_data_marketplace.massive_datasets.values() if d.status == "completed"]),
                    "processing": len([d for d in massive_data_marketplace.massive_datasets.values() if d.status in ["processing", "downloading", "chunking", "distributing", "listing"]])
                }
            }

        # ===== WALLET ENDPOINTS =====

        @self.app.options("/api/wallet/create")
        async def options_wallet_create():
            """OPTIONS handler for wallet creation."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/api/wallet/create", response_model=Dict[str, Any])
        async def create_wallet(request: WalletCreateRequest, current_user: dict = Depends(get_current_user)):
            """Crear una nueva wallet DRACMA."""
            try:
                wallet = marketplace.create_wallet(request.user_id, request.label)
                balance = wallet.get_balance()

                portfolio = wallet.get_portfolio_summary()

                return {
                    "success": True,
                    "wallet": {
                        "address": wallet.current_address,
                        "balance_dracma": balance,
                        "portfolio": portfolio
                    }
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error creando wallet: {str(e)}")

        @self.app.get("/api/wallet/{user_id}/balance")
        async def get_wallet_balance(user_id: str):
            """Obtener balance de wallet."""
            try:
                wallet = marketplace.get_wallet(user_id)
                if not wallet:
                    raise HTTPException(status_code=404, detail="Wallet no encontrada")

                portfolio = wallet.get_portfolio_summary()
                return portfolio
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error obteniendo balance: {str(e)}")

        @self.app.options("/api/wallet/transfer")
        async def options_wallet_transfer():
            """OPTIONS handler for wallet transfer."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/api/wallet/transfer")
        async def transfer_tokens(request: TransactionRequest):
            """Transferir DracmaS entre wallets."""
            try:
                tx_hash = marketplace.transfer_tokens(
                    request.sender_id,
                    request.receiver_address,
                    request.amount
                )

                return {
                    "success": True,
                    "transaction_hash": tx_hash,
                    "amount": request.amount,
                    "from": request.sender_id,
                    "to": request.receiver_address
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error en transferencia: {str(e)}")

        @self.app.options("/api/wallet/stake")
        async def options_wallet_stake():
            """OPTIONS handler for wallet staking."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/api/wallet/stake")
        async def stake_tokens(user_id: str, amount: float):
            """Stake DracmaS tokens."""
            try:
                tx_hash = marketplace.stake_tokens(user_id, amount)

                return {
                    "success": True,
                    "transaction_hash": tx_hash,
                    "amount_staked": amount
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error en staking: {str(e)}")

        @self.app.options("/api/wallet/unstake")
        async def options_wallet_unstake():
            """OPTIONS handler for wallet unstaking."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/api/wallet/unstake")
        async def unstake_tokens(user_id: str, amount: float):
            """Unstake DracmaS tokens."""
            try:
                tx_hash = marketplace.unstake_tokens(user_id, amount)

                return {
                    "success": True,
                    "transaction_hash": tx_hash,
                    "amount_unstaked": amount
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error en unstaking: {str(e)}")

        @self.app.get("/api/wallet/{user_id}/transactions")
        async def get_wallet_transactions(user_id: str, limit: int = Query(20, ge=1, le=100)):
            """Obtener historial de transacciones."""
            try:
                transactions = marketplace.get_transaction_history(user_id, limit)
                return {"transactions": transactions}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error obteniendo transacciones: {str(e)}")

        # ===== MARKETPLACE ENDPOINTS =====

        @self.app.options("/api/marketplace/listing/create")
        async def options_marketplace_listing_create():
            """OPTIONS handler for data listing creation."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/api/marketplace/listing/create")
        async def create_data_listing(request: DataListingRequest):
            """Crear un nuevo listing de datos REAL."""
            try:
                logger.info(f"📦 Creating data listing: {request.title} by {request.seller_id}")

                listing_id = marketplace.create_data_listing(
                    seller_id=request.seller_id,
                    title=request.title,
                    description=request.description,
                    category=request.category,
                    data_hash=request.data_hash,
                    ipfs_cid=request.ipfs_cid,
                    price_dracma=request.price_dracma,
                    data_size_mb=request.data_size_mb,
                    sample_count=request.sample_count,
                    quality_score=request.quality_score,
                    tags=request.tags,
                    duration_days=request.duration_days
                )

                # Actualizar estadísticas
                self.system_stats["total_listings_created"] += 1

                logger.info(f"✅ Data listing created: {listing_id}")

                return {
                    "success": True,
                    "listing_id": listing_id,
                    "message": "Listing creado exitosamente"
                }
            except Exception as e:
                logger.error(f"❌ Error creating data listing: {e}")
                raise HTTPException(status_code=400, detail=f"Error creando listing: {str(e)}")

        @self.app.get("/api/marketplace/listings")
        async def search_listings(
            query: str = Query("", description="Término de búsqueda"),
            category: str = Query("", description="Categoría de datos"),
            min_price: float = Query(0, ge=0, description="Precio mínimo"),
            max_price: float = Query(None, description="Precio máximo"),
            min_quality: float = Query(0, ge=0, le=1, description="Calidad mínima"),
            tags: str = Query("", description="Etiquetas separadas por coma"),
            limit: int = Query(20, ge=1, le=100, description="Límite de resultados")
        ):
            """Buscar listings disponibles."""
            try:
                tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []

                datasets = marketplace.search_datasets(
                    query=query,
                    category=category if category else None,
                    min_price=min_price,
                    max_price=max_price if max_price is not None else float('inf'),
                    min_quality=min_quality,
                    tags=tag_list,
                    limit=limit
                )

                return {"datasets": datasets, "total": len(datasets)}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error buscando datasets: {str(e)}")

        @self.app.options("/api/marketplace/purchase")
        async def options_marketplace_purchase():
            """OPTIONS handler for dataset purchase."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/api/marketplace/purchase")
        async def purchase_dataset(request: PurchaseRequest):
            """Comprar un dataset REAL."""
            try:
                logger.info(f"🛒 Purchasing dataset: {request.listing_id} by {request.buyer_id}")

                tx_hash = marketplace.purchase_data(request.buyer_id, request.listing_id)

                # Actualizar estadísticas
                self.system_stats["total_purchases_made"] += 1

                logger.info(f"✅ Dataset purchased: {request.listing_id} - TX: {tx_hash}")

                return {
                    "success": True,
                    "transaction_hash": tx_hash,
                    "listing_id": request.listing_id,
                    "buyer_id": request.buyer_id
                }
            except Exception as e:
                logger.error(f"❌ Error purchasing dataset: {e}")
                raise HTTPException(status_code=400, detail=f"Error en compra: {str(e)}")

        @self.app.get("/api/marketplace/stats")
        async def get_marketplace_stats():
            """Obtener estadísticas del marketplace."""
            try:
                stats = marketplace.get_market_stats()
                return stats
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")

        @self.app.get("/api/marketplace/user/{user_id}/portfolio")
        async def get_user_portfolio(user_id: str):
            """Obtener portfolio completo de usuario."""
            try:
                portfolio = marketplace.get_user_portfolio(user_id)
                return portfolio
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error obteniendo portfolio: {str(e)}")

        @self.app.get("/api/marketplace/recommendations/{user_id}")
        async def get_recommendations(user_id: str, limit: int = Query(5, ge=1, le=20)):
            """Obtener recomendaciones de datasets."""
            try:
                recommendations = marketplace.get_recommendations(user_id, limit)
                return {"recommendations": recommendations}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error obteniendo recomendaciones: {str(e)}")

        # ===== MASSIVE DATASETS ENDPOINTS =====

        @self.app.get("/api/marketplace/massive/datasets")
        async def get_massive_datasets():
            """Obtener lista de datasets masivos."""
            try:
                datasets = massive_data_marketplace.get_massive_datasets()
                return {"datasets": datasets, "total": len(datasets)}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error obteniendo datasets masivos: {str(e)}")

        @self.app.get("/api/marketplace/massive/datasets/{dataset_id}")
        async def get_massive_dataset_details(dataset_id: str):
            """Obtener detalles de un dataset masivo específico."""
            try:
                dataset = massive_data_marketplace.get_massive_dataset_details(dataset_id)
                if not dataset:
                    raise HTTPException(status_code=404, detail="Dataset masivo no encontrado")
                return dataset
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error obteniendo detalles del dataset: {str(e)}")

        @self.app.options("/api/marketplace/massive/trigger-listing")
        async def options_massive_trigger_listing():
            """OPTIONS handler for massive listing trigger."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/api/marketplace/massive/trigger-listing")
        async def trigger_massive_listing(request: dict):
            """Disparar creación manual de listing para dataset masivo."""
            try:
                source_name = request.get("source_name")
                dataset_info = request.get("dataset_info", {})

                if not source_name or not dataset_info:
                    raise HTTPException(status_code=400, detail="source_name y dataset_info son requeridos")

                dataset_id = await massive_data_marketplace.trigger_manual_listing(source_name, dataset_info)

                return {
                    "success": True,
                    "dataset_id": dataset_id,
                    "message": "Procesamiento de dataset masivo iniciado"
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error iniciando listing masivo: {str(e)}")

        @self.app.options("/api/marketplace/massive/start-auto-listing")
        async def options_massive_start_auto_listing():
            """OPTIONS handler for starting auto-listing."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/api/marketplace/massive/start-auto-listing")
        async def start_auto_listing():
            """Iniciar creación automática de listings."""
            try:
                await massive_data_marketplace.start_auto_listing()
                return {"success": True, "message": "Auto-listing iniciado"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error iniciando auto-listing: {str(e)}")

        @self.app.options("/api/marketplace/massive/stop-auto-listing")
        async def options_massive_stop_auto_listing():
            """OPTIONS handler for stopping auto-listing."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/api/marketplace/massive/stop-auto-listing")
        async def stop_auto_listing():
            """Detener creación automática de listings."""
            try:
                await massive_data_marketplace.stop_auto_listing()
                return {"success": True, "message": "Auto-listing detenido"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error deteniendo auto-listing: {str(e)}")

        @self.app.get("/api/marketplace/massive/stats")
        async def get_massive_marketplace_stats():
            """Obtener estadísticas extendidas del marketplace incluyendo datasets masivos."""
            try:
                stats = massive_data_marketplace.get_marketplace_stats_extended()
                return stats
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas masivas: {str(e)}")

        # ===== DATA SOURCE MANAGEMENT ENDPOINTS =====

        @self.app.get("/api/marketplace/sources")
        async def get_data_sources():
            """Obtener lista de fuentes de datos configuradas."""
            try:
                sources = []
                for name, source in massive_data_marketplace.active_sources.items():
                    sources.append({
                        "name": name,
                        "url": source.url,
                        "category": source.category,
                        "enabled": source.enabled,
                        "update_interval_hours": source.update_interval_hours,
                        "max_size_mb": source.max_size_mb,
                        "quality_threshold": source.quality_threshold,
                        "auto_listing": source.auto_listing,
                        "metadata": source.metadata
                    })
                return {"sources": sources, "total": len(sources)}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error obteniendo fuentes de datos: {str(e)}")

        @self.app.options("/api/marketplace/sources/add")
        async def options_sources_add():
            """OPTIONS handler for adding data source."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/api/marketplace/sources/add")
        async def add_data_source(request: dict):
            """Añadir una nueva fuente de datos."""
            try:
                from ..core.config import DataSourceConfig

                source_data = request.get("source", {})
                if not source_data.get("name") or not source_data.get("url"):
                    raise HTTPException(status_code=400, detail="name y url son requeridos")

                # Create source config
                source_config = DataSourceConfig(**source_data)

                # Add to active sources
                massive_data_marketplace.active_sources[source_config.name] = source_config

                # Add to config if persistence is needed
                config = massive_data_marketplace.config
                config.data.sources.append(source_config)

                return {
                    "success": True,
                    "source_name": source_config.name,
                    "message": "Fuente de datos añadida exitosamente"
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error añadiendo fuente de datos: {str(e)}")

        @self.app.options("/api/marketplace/sources/{source_name}/enable")
        async def options_sources_enable(source_name: str):
            """OPTIONS handler for enabling data source."""
            return {"Allow": "PUT, OPTIONS"}

        @self.app.put("/api/marketplace/sources/{source_name}/enable")
        async def enable_data_source(source_name: str, enabled: bool = True):
            """Habilitar/deshabilitar una fuente de datos."""
            try:
                if source_name not in massive_data_marketplace.active_sources:
                    raise HTTPException(status_code=404, detail="Fuente de datos no encontrada")

                source = massive_data_marketplace.active_sources[source_name]
                source.enabled = enabled

                return {
                    "success": True,
                    "source_name": source_name,
                    "enabled": enabled,
                    "message": f"Fuente de datos {'habilitada' if enabled else 'deshabilitada'}"
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error actualizando fuente de datos: {str(e)}")

        @self.app.options("/api/marketplace/sources/{source_name}")
        async def options_sources_delete(source_name: str):
            """OPTIONS handler for removing data source."""
            return {"Allow": "DELETE, OPTIONS"}

        @self.app.delete("/api/marketplace/sources/{source_name}")
        async def remove_data_source(source_name: str):
            """Eliminar una fuente de datos."""
            try:
                if source_name not in massive_data_marketplace.active_sources:
                    raise HTTPException(status_code=404, detail="Fuente de datos no encontrada")

                # Remove from active sources
                del massive_data_marketplace.active_sources[source_name]

                # Remove from config
                config = massive_data_marketplace.config
                config.data.sources = [s for s in config.data.sources if s.name != source_name]

                return {
                    "success": True,
                    "source_name": source_name,
                    "message": "Fuente de datos eliminada"
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error eliminando fuente de datos: {str(e)}")

        @self.app.options("/api/marketplace/sources/{source_name}/test")
        async def options_sources_test(source_name: str):
            """OPTIONS handler for testing data source."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/api/marketplace/sources/{source_name}/test")
        async def test_data_source(source_name: str):
            """Probar conectividad de una fuente de datos."""
            try:
                if source_name not in massive_data_marketplace.active_sources:
                    raise HTTPException(status_code=404, detail="Fuente de datos no encontrada")

                source = massive_data_marketplace.active_sources[source_name]

                # Test connection
                try:
                    response = requests.head(source.url, timeout=10)
                    connection_ok = response.status_code < 400
                except:
                    connection_ok = False

                return {
                    "source_name": source_name,
                    "url": source.url,
                    "connection_ok": connection_ok,
                    "status_code": response.status_code if 'response' in locals() else None
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error probando fuente de datos: {str(e)}")


        # ===== IPFS ENDPOINTS =====

        @self.app.options("/api/ipfs/publish")
        async def options_ipfs_publish():
            """OPTIONS handler for IPFS publishing."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/api/ipfs/publish")
        async def publish_to_ipfs(data: Dict[str, Any]):
            """Publicar datos en IPFS."""
            try:
                # Serializar datos
                data_str = json.dumps(data, indent=2)
                data_bytes = data_str.encode('utf-8')

                # Publicar en IPFS
                cid = await self.ipfs_manager.publish_data(data_bytes)

                return {
                    "success": True,
                    "cid": cid,
                    "size": len(data_bytes)
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error publicando en IPFS: {str(e)}")

        @self.app.get("/api/ipfs/{cid}")
        async def get_from_ipfs(cid: str):
            """Obtener datos desde IPFS."""
            try:
                data_bytes = await self.ipfs_manager.get_data(cid)
                data = json.loads(data_bytes.decode('utf-8'))

                return {
                    "success": True,
                    "cid": cid,
                    "data": data
                }
            except Exception as e:
                raise HTTPException(status_code=404, detail=f"Error obteniendo desde IPFS: {str(e)}")

    def create_app(self) -> FastAPI:
        """Crear y retornar la aplicación FastAPI."""
        return self.app

    def start_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Iniciar servidor FastAPI."""
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )


# Instancia global de la API
marketplace_api = MarketplaceAPI()


def create_marketplace_app() -> FastAPI:
    """Función de conveniencia para crear la app FastAPI."""
    return marketplace_api.create_app()


if __name__ == "__main__":
    # Iniciar servidor para pruebas
    print("🚀 Iniciando AILOOS Marketplace API...")
    marketplace_api.start_server()