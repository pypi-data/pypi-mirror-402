"""
Marketplace principal de AILOOS.
Orquestador de transacciones DracmaS y listings de datos.
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from ..core.logging import get_logger
from .wallet import DRACMAWallet
from .data_listing import data_marketplace, DataCategory, DataListing
from .price_oracle import price_oracle
from ..blockchain.dracma_token import TransactionResult

logger = get_logger(__name__)


class Marketplace:
    """
    Marketplace completo para AILOOS.
    Gestiona wallets, listings de datos y transacciones DRACMA.
    """

    def __init__(self):
        self.wallets: Dict[str, DRACMAWallet] = {}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    def create_wallet(self, user_id: str, label: str = "default") -> DRACMAWallet:
        """
        Crea una nueva wallet para un usuario.

        Args:
            user_id: ID único del usuario
            label: Etiqueta para la dirección

        Returns:
            Wallet creada
        """
        wallet_file = f"./wallets/{user_id}_dracma_wallet.json"
        wallet = DRACMAWallet(wallet_file)
        wallet.create_address(label)
        self.wallets[user_id] = wallet
        return wallet

    def get_wallet(self, user_id: str) -> Optional[DRACMAWallet]:
        """Obtiene wallet de un usuario."""
        return self.wallets.get(user_id)

    def create_data_listing(self, seller_id: str, title: str, description: str,
                           category: str, data_hash: str, ipfs_cid: str,
                           price_dracma: float, data_size_mb: float,
                           sample_count: int, quality_score: float,
                           tags: List[str], duration_days: int = 30) -> str:
        """
        Crea un nuevo listing de datos.

        Args:
            seller_id: ID del vendedor
            title: Título del dataset
            description: Descripción
            category: Categoría de datos
            data_hash: Hash de integridad
            ipfs_cid: CID de IPFS
            price_dracma: Precio en DRACMA
            data_size_mb: Tamaño en MB
            sample_count: Número de muestras
            quality_score: Calidad (0-1)
            tags: Etiquetas
            duration_days: Duración del listing

        Returns:
            ID del listing creado
        """
        wallet = self.get_wallet(seller_id)
        if not wallet:
            raise ValueError(f"Usuario {seller_id} no tiene wallet")

        seller_address = wallet.current_address
        if not seller_address:
            raise ValueError(f"Wallet de {seller_id} no tiene dirección activa")

        # Convertir categoría string a enum
        try:
            data_category = DataCategory(category)
        except ValueError:
            raise ValueError(f"Categoría {category} no válida")

        return data_marketplace.create_listing(
            seller_address=seller_address,
            title=title,
            description=description,
            category=data_category,
            data_hash=data_hash,
            ipfs_cid=ipfs_cid,
            price_dracma=price_dracma,
            data_size_mb=data_size_mb,
            sample_count=sample_count,
            quality_score=quality_score,
            tags=tags,
            duration_days=duration_days
        )

    async def purchase_data(self, buyer_id: str, listing_id: str) -> TransactionResult:
        """
        Compra un dataset del marketplace.

        Args:
            buyer_id: ID del comprador
            listing_id: ID del listing

        Returns:
            Resultado de la transacción
        """
        # Obtener wallets
        buyer_wallet = self.get_wallet(buyer_id)
        if not buyer_wallet:
            raise ValueError(f"Comprador {buyer_id} no tiene wallet")

        # Obtener detalles del listing
        listing = data_marketplace.get_listing_details(listing_id)
        if not listing:
            raise ValueError(f"Listing {listing_id} no existe")

        if listing.status.name != "ACTIVE":
            raise ValueError(f"Listing {listing_id} no está disponible")

        # Verificar balance suficiente
        buyer_balance = await buyer_wallet.get_balance()
        if buyer_balance < listing.price_dracma:
            raise ValueError(f"Balance insuficiente: {buyer_balance} DRACMA, necesita {listing.price_dracma}")

        # Ejecutar compra
        tx_result = await buyer_wallet.purchase_data(
            seller_address=listing.seller_address,
            amount=listing.price_dracma,
            data_hash=listing.data_hash,
            ipfs_cid=listing.ipfs_cid
        )

        if tx_result.success:
            # Registrar compra en marketplace
            data_marketplace.purchase_listing(
                buyer_address=buyer_wallet.current_address,
                listing_id=listing_id,
                transaction_hash=tx_result.transaction_hash
            )

            # Registrar transacción en el oráculo de precios para aprendizaje
            try:
                import asyncio
                asyncio.create_task(price_oracle.record_transaction(
                    listing_id=listing_id,
                    category=listing.category,
                    price=listing.price_dracma,
                    volume=1
                ))
            except Exception as e:
                logger.warning(f"Failed to record transaction in price oracle: {e}")

        return tx_result

    def search_datasets(self, query: str = "", category: str = "",
                       min_price: float = 0, max_price: float = float('inf'),
                       min_quality: float = 0, tags: List[str] = None,
                       limit: int = 20) -> List[Dict[str, Any]]:
        """
        Busca datasets disponibles.

        Returns:
            Lista de datasets formateados
        """
        # Convertir categoría string a enum
        data_category = None
        if category:
            try:
                data_category = DataCategory(category)
            except ValueError:
                pass  # Ignorar categoría inválida

        listings = data_marketplace.search_listings(
            query=query,
            category=data_category,
            min_price=min_price,
            max_price=max_price,
            min_quality=min_quality,
            tags=tags or [],
            limit=limit
        )

        # Formatear resultados
        results = []
        for listing in listings:
            results.append({
                "listing_id": listing.listing_id,
                "title": listing.title,
                "description": listing.description,
                "category": listing.category.value,
                "price_dracma": listing.price_dracma,
                "data_size_mb": listing.data_size_mb,
                "sample_count": listing.sample_count,
                "quality_score": listing.quality_score,
                "tags": listing.tags,
                "seller_address": listing.seller_address,
                "ipfs_cid": listing.ipfs_cid,
                "created_at": listing.created_at,
                "expires_at": listing.expires_at
            })

        return results

    async def get_user_portfolio(self, user_id: str) -> Dict[str, Any]:
        """
        Obtiene portfolio completo de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Información completa del portfolio
        """
        wallet = self.get_wallet(user_id)
        if not wallet:
            return {"error": "Usuario no tiene wallet"}

        portfolio = await wallet.get_portfolio_summary()

        # Añadir listings activos
        user_listings = data_marketplace.get_user_listings(wallet.current_address)
        portfolio["active_listings"] = len([l for l in user_listings if l.status.name == "ACTIVE"])

        # Añadir compras realizadas
        user_purchases = data_marketplace.get_user_purchases(wallet.current_address)
        portfolio["total_purchases"] = len(user_purchases)

        # Calcular valor de listings activos
        active_value = sum(l.price_DracmaS for l in user_listings if l.status.name == "ACTIVE")
        portfolio["active_listings_value"] = active_value

        return portfolio

    def get_market_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del marketplace."""
        return data_marketplace.get_market_stats()

    async def get_price_suggestion(self, category: str, data_quality: float = 0.5,
                                 data_size_mb: float = 1.0) -> Dict[str, Any]:
        """
        Obtiene sugerencia de precio del oráculo.

        Args:
            category: Categoría de datos
            data_quality: Calidad de los datos (0-1)
            data_size_mb: Tamaño en MB

        Returns:
            Sugerencia de precio
        """
        try:
            return await price_oracle.get_price_estimate(
                DataCategory(category), data_quality, data_size_mb
            )
        except Exception as e:
            return {"error": f"Error getting price suggestion: {e}"}

    def get_market_overview(self) -> Dict[str, Any]:
        """Obtiene overview del mercado desde el oráculo."""
        try:
            # Run async function in new event loop if needed
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(price_oracle.get_market_overview())
            loop.close()
            return result
        except Exception as e:
            return {"error": str(e)}

    async def stake_tokens(self, user_id: str, amount: float) -> TransactionResult:
        """
        Stake DracmaS tokens para obtener rewards.

        Args:
            user_id: ID del usuario
            amount: Cantidad a stakear

        Returns:
            Resultado de la transacción
        """
        wallet = self.get_wallet(user_id)
        if not wallet:
            raise ValueError(f"Usuario {user_id} no tiene wallet")

        return await wallet.stake_tokens(amount)

    async def unstake_tokens(self, user_id: str, amount: float) -> TransactionResult:
        """
        Unstake DracmaS tokens.

        Args:
            user_id: ID del usuario
            amount: Cantidad a unstakear

        Returns:
            Resultado de la transacción
        """
        wallet = self.get_wallet(user_id)
        if not wallet:
            raise ValueError(f"Usuario {user_id} no tiene wallet")

        return await wallet.unstake_tokens(amount)

    async def transfer_tokens(self, sender_id: str, receiver_address: str, amount: float) -> TransactionResult:
        """
        Transfiere DracmaS entre usuarios.

        Args:
            sender_id: ID del remitente
            receiver_address: Dirección del destinatario
            amount: Cantidad a transferir

        Returns:
            Resultado de la transacción
        """
        wallet = self.get_wallet(sender_id)
        if not wallet:
            raise ValueError(f"Usuario {sender_id} no tiene wallet")

        return await wallet.transfer(receiver_address, amount)

    async def get_transaction_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Obtiene historial de transacciones de un usuario.

        Args:
            user_id: ID del usuario
            limit: Número máximo de transacciones

        Returns:
            Lista de transacciones formateadas
        """
        wallet = self.get_wallet(user_id)
        if not wallet:
            return []

        transactions = await wallet.get_transaction_history(limit)

        # Formatear transacciones
        formatted_txs = []
        for tx in transactions:
            formatted_txs.append({
                "tx_hash": tx.get("tx_hash", ""),
                "type": tx.get("type", ""),
                "amount": tx.get("amount", 0),
                "timestamp": tx.get("timestamp", 0),
                "status": tx.get("status", ""),
                "sender": tx.get("sender", ""),
                "receiver": tx.get("receiver", ""),
                "data": tx.get("data", {})
            })

        return formatted_txs

    def validate_data_purchase(self, user_id: str, listing_id: str, downloaded_hash: str,
                              metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Valida integridad completa de datos comprados.

        Args:
            user_id: ID del comprador
            listing_id: ID del listing
            downloaded_hash: Hash de los datos descargados
            metadata: Metadatos adicionales para validación

        Returns:
            Dict con resultado de validación detallado
        """
        wallet = self.get_wallet(user_id)
        if not wallet:
            return {"valid": False, "error": "Wallet not found"}

        # Verificar que el usuario compró este listing
        user_purchases = data_marketplace.get_user_purchases(wallet.current_address)
        purchased_ids = [l.listing_id for l in user_purchases]

        if listing_id not in purchased_ids:
            return {"valid": False, "error": "Listing not purchased by user"}

        # Validar integridad completa
        validation_result = data_marketplace.validate_data_integrity(listing_id, downloaded_hash, metadata)

        # Añadir información de compra
        validation_result["purchase_verified"] = True
        validation_result["buyer_address"] = wallet.current_address

        return validation_result

    def create_marketplace_session(self, user_id: str) -> str:
        """
        Crea una sesión de marketplace para un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            ID de la sesión
        """
        session_id = f"marketplace_session_{user_id}_{int(time.time())}"
        self.active_sessions[session_id] = {
            "user_id": user_id,
            "created_at": time.time(),
            "last_activity": time.time()
        }
        return session_id

    def end_marketplace_session(self, session_id: str):
        """Finaliza una sesión de marketplace."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

    def get_recommendations(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Recomienda datasets basados en historial del usuario.

        Args:
            user_id: ID del usuario
            limit: Número de recomendaciones

        Returns:
            Lista de datasets recomendados
        """
        wallet = self.get_wallet(user_id)
        if not wallet:
            return []

        # Obtener historial de compras para inferir preferencias
        purchases = data_marketplace.get_user_purchases(wallet.current_address)

        if not purchases:
            # Usuario nuevo - recomendar datasets populares de alta calidad
            all_listings = data_marketplace.search_listings(
                min_quality=0.8,
                limit=limit * 2
            )
            # Ordenar por precio (más baratos primero para nuevos usuarios)
            all_listings.sort(key=lambda x: x.price_dracma)
            return [{
                "listing_id": l.listing_id,
                "title": l.title,
                "category": l.category.value,
                "price_dracma": l.price_dracma,
                "quality_score": l.quality_score,
                "reason": "Popular dataset de alta calidad"
            } for l in all_listings[:limit]]

        # Usuario existente - recomendar basado en categorías compradas
        categories = {}
        for purchase in purchases:
            cat = purchase.category.value
            categories[cat] = categories.get(cat, 0) + 1

        # Encontrar categoría más comprada
        top_category = max(categories, key=categories.get)
        data_cat = DataCategory(top_category)

        # Buscar más datasets en esa categoría
        recommendations = data_marketplace.search_listings(
            category=data_cat,
            limit=limit + len(purchases)  # Más resultados para filtrar
        )

        # Filtrar datasets ya comprados
        purchased_ids = {p.listing_id for p in purchases}
        new_recommendations = [r for r in recommendations if r.listing_id not in purchased_ids]

        return [{
            "listing_id": r.listing_id,
            "title": r.title,
            "category": r.category.value,
            "price_dracma": r.price_dracma,
            "quality_score": r.quality_score,
            "reason": f"Similar a tus compras en {top_category}"
        } for r in new_recommendations[:limit]]


# Instancia global del marketplace
marketplace = Marketplace()


# Funciones de conveniencia para CLI
def create_user_wallet(user_id: str) -> DRACMAWallet:
    """Crea wallet para un usuario."""
    return marketplace.create_wallet(user_id)


async def get_user_balance(user_id: str) -> float:
    """Obtiene balance de un usuario."""
    wallet = marketplace.get_wallet(user_id)
    return await wallet.get_balance() if wallet else 0.0


def list_available_datasets(limit: int = 10) -> List[Dict[str, Any]]:
    """Lista datasets disponibles."""
    return marketplace.search_datasets(limit=limit)


def show_market_stats() -> Dict[str, Any]:
    """Muestra estadísticas del marketplace."""
    return marketplace.get_market_stats()
