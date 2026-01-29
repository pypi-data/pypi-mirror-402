"""
API REST para integración de wallets blockchain.
Proporciona endpoints para conectar wallets, gestionar balances y procesar transacciones.
"""

import asyncio
import os
import time
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from ..coordinator.auth.dependencies import get_current_user, get_current_node
from pydantic import BaseModel, Field
import uvicorn

from ..web.wallet_integration import get_wallet_integration, WalletType, TransactionRequest
from ..blockchain.dracma_token import get_token_manager
from ..core.logging import get_logger

logger = get_logger(__name__)

logger = get_logger(__name__)


# Modelos Pydantic
class ConnectWalletRequest(BaseModel):
    wallet_type: str = Field(..., description="Tipo de wallet (metamask, wallet_connect, etc.)")
    user_id: Optional[str] = Field(None, description="ID del usuario opcional")


class TransactionRequestModel(BaseModel):
    to_address: str = Field(..., description="Dirección destinataria")
    amount: float = Field(..., gt=0, description="Cantidad a transferir")
    data: Optional[str] = Field(None, description="Datos adicionales de la transacción")


class StakeRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Cantidad a stakear")


class MarketplacePurchaseRequest(BaseModel):
    seller_address: str = Field(..., description="Dirección del vendedor")
    amount: float = Field(..., gt=0, description="Monto de la compra")
    data_hash: str = Field(..., description="Hash de los datos")
    ipfs_cid: str = Field(..., description="CID de IPFS")


class WalletAPI:
    """
    API REST completa para integración de wallets blockchain.
    Maneja conexión, transacciones y gestión de balances.
    """

    def __init__(self):
        self.app = FastAPI(
            title="AILOOS Wallet API",
            description="API para integración de wallets blockchain",
            version="1.0.0"
        )

        # Componentes REALES
        self.wallet_integration = get_wallet_integration()
        self.token_manager = get_token_manager()

        # Estadísticas del sistema
        self.system_stats = {
            "total_wallets_connected": 0,
            "total_transactions_processed": 0,
            "total_staked_amount": 0.0,
            "start_time": time.time()
        }

        logger.info("🔗 Wallet API initialized with real blockchain integration")

        # Configurar rutas
        self._setup_routes()

    def _setup_routes(self):
        """Configurar todas las rutas de la API."""

        @self.app.get("/health")
        async def health_check():
            """Health check REAL de la wallet API."""
            connected_wallets = len(self.wallet_integration.get_connected_wallets())

            # Calcular uptime
            uptime_seconds = time.time() - self.system_stats["start_time"]
            uptime_hours = uptime_seconds / 3600

            return {
                "status": "healthy",
                "connected_wallets": connected_wallets,
                "total_transactions_processed": self.system_stats["total_transactions_processed"],
                "total_staked_amount": self.system_stats["total_staked_amount"],
                "system_uptime_hours": f"{uptime_hours:.1f}",
                "token_info": self.token_manager.get_token_info(),
                "wallet_system_health": "healthy" if connected_wallets > 0 else "idle"
            }

        # ===== WALLET CONNECTION =====

        @self.app.options("/connect")
        async def options_wallet_connect():
            """OPTIONS handler for wallet connection."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/connect")
        async def connect_wallet(request: ConnectWalletRequest, current_user: dict = Depends(get_current_user)):
            """
            Conecta una wallet blockchain REAL.

            Returns información de conexión y balance inicial.
            """
            try:
                # Convertir string a enum
                try:
                    wallet_type = WalletType(request.wallet_type)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Unsupported wallet type: {request.wallet_type}")

                logger.info(f"🔗 Connecting wallet: {wallet_type.value} for user {request.user_id}")

                # Conectar wallet REAL
                result = await self.wallet_integration.connect_wallet(
                    wallet_type,
                    user_id=request.user_id
                )

                if not result['success']:
                    raise HTTPException(status_code=400, detail=result.get('error', 'Connection failed'))

                wallet_info = result['wallet_info']

                # Obtener balance inicial REAL
                balance = await self.wallet_integration.get_wallet_balance(wallet_info.address)

                # Actualizar estadísticas
                self.system_stats["total_wallets_connected"] += 1

                logger.info(f"✅ Wallet connected: {wallet_info.address} ({wallet_type.value})")

                return {
                    "success": True,
                    "wallet": {
                        "address": wallet_info.address,
                        "wallet_type": wallet_info.wallet_type.value,
                        "chain_id": wallet_info.chain_id,
                        "balance": balance,
                        "is_connected": wallet_info.is_connected
                    },
                    "message": result.get('message', 'Wallet connected successfully')
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Wallet connection error: {e}")
                raise HTTPException(status_code=500, detail=f"Connection failed: {str(e)}")

        @self.app.options("/disconnect")
        async def options_wallet_disconnect():
            """OPTIONS handler for wallet disconnection."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/disconnect")
        async def disconnect_wallet(address: str):
            """
            Desconecta una wallet.

            Args:
                address: Dirección de la wallet a desconectar
            """
            try:
                await self.wallet_integration.disconnect_wallet(address)
                return {"success": True, "message": "Wallet disconnected successfully"}

            except Exception as e:
                logger.error(f"Wallet disconnection error: {e}")
                raise HTTPException(status_code=500, detail=f"Disconnection failed: {str(e)}")

        @self.app.get("/balance/{address}")
        async def get_wallet_balance(address: str):
            """
            Obtiene balance de una wallet.

            Args:
                address: Dirección de la wallet
            """
            try:
                balance = await self.wallet_integration.get_wallet_balance(address)
                return {
                    "address": address,
                    "balance": balance,
                    "last_updated": self.wallet_integration.connected_wallets.get(address, {}).last_updated
                }

            except Exception as e:
                logger.error(f"Balance check error: {e}")
                raise HTTPException(status_code=500, detail=f"Balance check failed: {str(e)}")

        @self.app.get("/status")
        async def get_wallet_status():
            """Obtiene estado de todas las wallets conectadas."""
            try:
                wallets = self.wallet_integration.get_connected_wallets()
                return {
                    "connected_wallets": [
                        {
                            "address": w.address,
                            "wallet_type": w.wallet_type.value,
                            "chain_id": w.chain_id,
                            "balance_dracma": w.balance_dracma,
                            "balance_eth": 0.0,
                            "is_connected": w.is_connected,
                            "last_updated": w.last_updated
                        }
                        for w in wallets
                    ],
                    "total_connected": len(wallets)
                }

            except Exception as e:
                logger.error(f"Status check error: {e}")
                raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

        # ===== TRANSACTIONS =====

        @self.app.options("/transfer")
        async def options_wallet_transfer():
            """OPTIONS handler for token transfer."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/transfer")
        async def transfer_tokens(from_address: str, request: TransactionRequestModel):
            """
            Transfiere tokens DracmaS REALES.

            Args:
                from_address: Dirección remitente (desde query params)
            """
            try:
                # Verificar que la wallet esté conectada REAL
                if not self.wallet_integration.is_wallet_connected(from_address):
                    raise HTTPException(status_code=403, detail="Wallet not connected")

                logger.info(f"💸 Transfer request: {from_address} -> {request.to_address} ({request.amount} DRACMA)")

                # Crear solicitud de transacción REAL
                tx_request = TransactionRequest(
                    to_address=request.to_address,
                    amount=request.amount,
                    data=request.data
                )

                # Ejecutar transacción REAL
                result = await self.wallet_integration.send_transaction(from_address, tx_request)

                if result.success:
                    # Actualizar estadísticas
                    self.system_stats["total_transactions_processed"] += 1

                    logger.info(f"✅ Transfer completed: {result.tx_hash}")

                    return {
                        "success": True,
                        "transaction": {
                            "tx_hash": result.tx_hash,
                            "from": from_address,
                            "to": request.to_address,
                            "amount": request.amount,
                            "block_number": result.block_number,
                            "gas_used": result.gas_used
                        }
                    }
                else:
                    raise HTTPException(status_code=400, detail=result.error_message or "Transaction failed")

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Transfer error: {e}")
                raise HTTPException(status_code=500, detail=f"Transfer failed: {str(e)}")

        @self.app.options("/stake")
        async def options_wallet_stake():
            """OPTIONS handler for token staking."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/stake")
        async def stake_tokens(address: str, request: StakeRequest):
            """
            Hace stake de tokens DracmaS REALES.

            Args:
                address: Dirección de la wallet
            """
            try:
                if not self.wallet_integration.is_wallet_connected(address):
                    raise HTTPException(status_code=403, detail="Wallet not connected")

                logger.info(f"🔒 Staking request: {address} staking {request.amount} DRACMA")

                result = await self.wallet_integration.stake_tokens(address, request.amount)

                if result.success:
                    # Actualizar estadísticas
                    self.system_stats["total_staked_amount"] += request.amount

                    logger.info(f"✅ Staking completed: {result.tx_hash}")

                    return {
                        "success": True,
                        "transaction": {
                            "tx_hash": result.tx_hash,
                            "address": address,
                            "amount_staked": request.amount,
                            "block_number": result.block_number
                        }
                    }
                else:
                    raise HTTPException(status_code=400, detail=result.error_message or "Staking failed")

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Staking error: {e}")
                raise HTTPException(status_code=500, detail=f"Staking failed: {str(e)}")

        @self.app.options("/unstake")
        async def options_wallet_unstake():
            """OPTIONS handler for token unstaking."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/unstake")
        async def unstake_tokens(address: str, request: StakeRequest):
            """
            Hace unstake de tokens DRACMA.

            Args:
                address: Dirección de la wallet
            """
            try:
                if not self.wallet_integration.is_wallet_connected(address):
                    raise HTTPException(status_code=403, detail="Wallet not connected")

                result = await self.wallet_integration.unstake_tokens(address, request.amount)

                if result.success:
                    return {
                        "success": True,
                        "transaction": {
                            "tx_hash": result.tx_hash,
                            "address": address,
                            "amount_unstaked": request.amount,
                            "block_number": result.block_number
                        }
                    }
                else:
                    raise HTTPException(status_code=400, detail=result.error_message or "Unstaking failed")

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Unstaking error: {e}")
                raise HTTPException(status_code=500, detail=f"Unstaking failed: {str(e)}")

        @self.app.options("/marketplace/purchase")
        async def options_marketplace_purchase():
            """OPTIONS handler for marketplace purchase."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/marketplace/purchase")
        async def marketplace_purchase(buyer_address: str, request: MarketplacePurchaseRequest):
            """
            Procesa compra REAL en marketplace.

            Args:
                buyer_address: Dirección del comprador
            """
            try:
                if not self.wallet_integration.is_wallet_connected(buyer_address):
                    raise HTTPException(status_code=403, detail="Wallet not connected")

                logger.info(f"🛒 Marketplace purchase: {buyer_address} buying from {request.seller_address} ({request.amount} DRACMA)")

                result = await self.wallet_integration.marketplace_purchase(
                    buyer_address,
                    request.seller_address,
                    request.amount,
                    request.data_hash,
                    request.ipfs_cid
                )

                if result.success:
                    # Actualizar estadísticas
                    self.system_stats["total_transactions_processed"] += 1

                    logger.info(f"✅ Marketplace purchase completed: {result.tx_hash}")

                    return {
                        "success": True,
                        "transaction": {
                            "tx_hash": result.tx_hash,
                            "buyer": buyer_address,
                            "seller": request.seller_address,
                            "amount": request.amount,
                            "data_hash": request.data_hash,
                            "ipfs_cid": request.ipfs_cid,
                            "block_number": result.block_number
                        }
                    }
                else:
                    raise HTTPException(status_code=400, detail=result.error_message or "Purchase failed")

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Marketplace purchase error: {e}")
                raise HTTPException(status_code=500, detail=f"Purchase failed: {str(e)}")

        # ===== INFORMATION =====

        @self.app.get("/transactions/{address}")
        async def get_transaction_history(address: str, limit: int = 20):
            """
            Obtiene historial de transacciones de una wallet.

            Args:
                address: Dirección de la wallet
                limit: Número máximo de transacciones
            """
            try:
                transactions = await self.wallet_integration.get_transaction_history(address, limit)
                return {
                    "address": address,
                    "transactions": transactions,
                    "total": len(transactions)
                }

            except Exception as e:
                logger.error(f"Transaction history error: {e}")
                raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")

        @self.app.get("/staking/{address}")
        async def get_staking_info(address: str):
            """
            Obtiene información de staking de una wallet.

            Args:
                address: Dirección de la wallet
            """
            try:
                staking_info = await self.wallet_integration.get_staking_info(address)
                return {
                    "address": address,
                    "staking_info": staking_info
                }

            except Exception as e:
                logger.error(f"Staking info error: {e}")
                raise HTTPException(status_code=500, detail=f"Staking info retrieval failed: {str(e)}")

        @self.app.get("/token/info")
        async def get_token_info():
            """Obtiene información del token DRACMA."""
            try:
                token_info = self.token_manager.get_token_info()
                return token_info

            except Exception as e:
                logger.error(f"Token info error: {e}")
                raise HTTPException(status_code=500, detail=f"Token info retrieval failed: {str(e)}")

        # ===== UTILITIES =====

        @self.app.options("/initialize/{user_id}")
        async def options_wallet_initialize(user_id: str):
            """OPTIONS handler for wallet initialization."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/initialize/{user_id}")
        async def initialize_user_wallet(user_id: str):
            """
            Inicializa wallet para un nuevo usuario.

            Args:
                user_id: ID del usuario
            """
            try:
                if os.getenv("AILOOS_ALLOW_MOCKS") != "1":
                    raise HTTPException(
                        status_code=400,
                        detail="Wallet initialization requires AILOOS_ALLOW_MOCKS=1 in non-local networks"
                    )
                from ..web.wallet_integration import initialize_wallet_for_user
                address = await initialize_wallet_for_user(user_id)

                return {
                    "success": True,
                    "user_id": user_id,
                    "wallet_address": address,
                    "message": "Wallet initialized with bonus tokens"
                }

            except Exception as e:
                logger.error(f"Wallet initialization error: {e}")
                raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")

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


# Instancia global de la API de wallets
wallet_api = WalletAPI()


def create_wallet_app() -> FastAPI:
    """Función de conveniencia para crear la app FastAPI de wallets."""
    return wallet_api.create_app()


if __name__ == "__main__":
    # Iniciar servidor para pruebas
    print("🚀 Iniciando AILOOS Wallet API...")
    wallet_api.start_server()
