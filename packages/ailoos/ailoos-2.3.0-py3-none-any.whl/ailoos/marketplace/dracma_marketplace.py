"""
🚀 AILOOS DracmaS Marketplace - Sistema Completo de Comercio de IA
================================================================

Plataforma completa para trading de modelos, datos, y capacidades de IA
usando el token DracmaS (DMS) en una economía tokenizada.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import base64

logger = logging.getLogger(__name__)


class AssetType(Enum):
    """Tipos de assets comerciables en el marketplace."""
    MODEL = "model"
    DATASET = "dataset"
    COMPUTE = "compute"
    API_ACCESS = "api_access"
    TRAINING_JOB = "training_job"
    INFERENCE_JOB = "inference_job"


class OrderType(Enum):
    """Tipos de órdenes en el marketplace."""
    BUY = "buy"
    SELL = "sell"
    AUCTION = "auction"
    SUBSCRIPTION = "subscription"


class OrderStatus(Enum):
    """Estados de las órdenes."""
    PENDING = "pending"
    ACTIVE = "active"
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class Asset:
    """Asset comerciable en el marketplace."""
    asset_id: str
    owner_id: str
    asset_type: AssetType
    title: str
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    price_dracma: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "owner_id": self.owner_id,
            "asset_type": self.asset_type.value,
            "title": self.title,
            "description": self.description,
            "metadata": self.metadata,
            "price_dracma": self.price_dracma,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active,
            "tags": self.tags
        }


@dataclass
class Order:
    """Orden de compra/venta en el marketplace."""
    order_id: str
    user_id: str
    asset_id: str
    order_type: OrderType
    quantity: int = 1
    price_dracma: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "asset_id": self.asset_id,
            "order_type": self.order_type.value,
            "quantity": self.quantity,
            "price_dracma": self.price_dracma,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata
        }


@dataclass
class Transaction:
    """Transacción completada en DRACMA."""
    transaction_id: str
    buyer_id: str
    seller_id: str
    asset_id: str
    amount_dracma: float
    fee_dracma: float
    status: str = "completed"
    blockchain_tx_hash: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "buyer_id": self.buyer_id,
            "seller_id": self.seller_id,
            "asset_id": self.asset_id,
            "amount_dracma": self.amount_dracma,
            "fee_dracma": self.fee_dracma,
            "status": self.status,
            "blockchain_tx_hash": self.blockchain_tx_hash,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }


class DracmaWallet:
    """Wallet simplificada para DracmaS (en producción integrar con blockchain real)."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.balance = 1000.0  # Balance inicial para demo
        self.transactions: List[Transaction] = []

    def get_balance(self) -> float:
        """Obtener balance actual."""
        return self.balance

    def transfer(self, to_user_id: str, amount: float, asset_id: str = "") -> bool:
        """Transferir DracmaS (simulado)."""
        if self.balance >= amount:
            self.balance -= amount
            # En producción: integrar con blockchain real
            logger.info(f"Transferred {amount} DracmaS from {self.user_id} to {to_user_id}")
            return True
        return False

    def receive(self, amount: float, from_user_id: str = "") -> None:
        """Recibir DRACMA."""
        self.balance += amount
        logger.info(f"Received {amount} DracmaS to {self.user_id}")


class MarketplaceEngine:
    """
    Motor principal del marketplace DRACMA.
    Maneja assets, órdenes, transacciones y matching.
    """

    def __init__(self):
        self.assets: Dict[str, Asset] = {}
        self.orders: Dict[str, Order] = {}
        self.transactions: List[Transaction] = []
        self.wallets: Dict[str, DracmaWallet] = {}
        self.marketplace_fee = 0.02  # 2% fee

    def _get_wallet(self, user_id: str) -> DracmaWallet:
        """Obtener o crear wallet para usuario."""
        if user_id not in self.wallets:
            self.wallets[user_id] = DracmaWallet(user_id)
        return self.wallets[user_id]

    async def create_asset(
        self,
        owner_id: str,
        asset_type: AssetType,
        title: str,
        description: str,
        price_dracma: float,
        metadata: Dict[str, Any] = None,
        tags: List[str] = None
    ) -> Asset:
        """Crear nuevo asset en el marketplace."""

        asset_id = str(uuid.uuid4())
        asset = Asset(
            asset_id=asset_id,
            owner_id=owner_id,
            asset_type=asset_type,
            title=title,
            description=description,
            price_dracma=price_dracma,
            metadata=metadata or {},
            tags=tags or []
        )

        self.assets[asset_id] = asset
        logger.info(f"Created asset {asset_id}: {title}")
        return asset

    async def list_assets(
        self,
        asset_type: Optional[AssetType] = None,
        owner_id: Optional[str] = None,
        tags: List[str] = None,
        min_price: float = 0,
        max_price: float = float('inf'),
        limit: int = 50
    ) -> List[Asset]:
        """Listar assets disponibles."""

        assets = list(self.assets.values())

        # Aplicar filtros
        if asset_type:
            assets = [a for a in assets if a.asset_type == asset_type]
        if owner_id:
            assets = [a for a in assets if a.owner_id == owner_id]
        if tags:
            assets = [a for a in assets if any(tag in a.tags for tag in tags)]

        assets = [a for a in assets if min_price <= a.price_DracmaS <= max_price]
        assets = [a for a in assets if a.is_active]

        # Ordenar por fecha de creación (más recientes primero)
        assets.sort(key=lambda x: x.created_at, reverse=True)

        return assets[:limit]

    async def place_order(
        self,
        user_id: str,
        asset_id: str,
        order_type: OrderType,
        quantity: int = 1,
        price_dracma: Optional[float] = None
    ) -> Order:
        """Colocar orden de compra/venta."""

        if asset_id not in self.assets:
            raise ValueError(f"Asset {asset_id} not found")

        asset = self.assets[asset_id]

        # Para órdenes de compra, usar precio del asset si no se especifica
        if price_DracmaS is None:
            if order_type == OrderType.BUY:
                price_DracmaS = asset.price_dracma
            else:
                price_DracmaS = asset.price_dracma

        order_id = str(uuid.uuid4())
        order = Order(
            order_id=order_id,
            user_id=user_id,
            asset_id=asset_id,
            order_type=order_type,
            quantity=quantity,
            price_dracma=price_dracma,
            expires_at=datetime.utcnow() + timedelta(hours=24)  # 24h expiry
        )

        self.orders[order_id] = order

        # Intentar matching inmediato para órdenes de compra
        if order_type == OrderType.BUY:
            await self._try_match_order(order)

        logger.info(f"Placed {order_type.value} order {order_id} for asset {asset_id}")
        return order

    async def _try_match_order(self, buy_order: Order) -> None:
        """Intentar matching de orden de compra con vendedores."""

        asset = self.assets.get(buy_order.asset_id)
        if not asset:
            return

        # Buscar órdenes de venta activas para el mismo asset
        sell_orders = [
            o for o in self.orders.values()
            if o.asset_id == buy_order.asset_id
            and o.order_type == OrderType.SELL
            and o.status == OrderStatus.ACTIVE
            and o.price_DracmaS <= buy_order.price_dracma
        ]

        if not sell_orders:
            # No hay vendedores, marcar orden como activa
            buy_order.status = OrderStatus.ACTIVE
            return

        # Matching con el mejor precio (más bajo)
        sell_orders.sort(key=lambda x: x.price_dracma)
        sell_order = sell_orders[0]

        # Ejecutar transacción
        await self._execute_transaction(buy_order, sell_order)

    async def _execute_transaction(self, buy_order: Order, sell_order: Order) -> None:
        """Ejecutar transacción entre comprador y vendedor."""

        buyer_wallet = self._get_wallet(buy_order.user_id)
        seller_wallet = self._get_wallet(sell_order.user_id)

        asset = self.assets[buy_order.asset_id]
        total_amount = sell_order.price_DracmaS * buy_order.quantity
        fee = total_amount * self.marketplace_fee

        # Verificar que el comprador tenga suficiente balance
        if not buyer_wallet.transfer(sell_order.user_id, total_amount + fee, buy_order.asset_id):
            logger.warning(f"Insufficient balance for user {buy_order.user_id}")
            return

        # Transferir fondos al vendedor
        seller_wallet.receive(total_amount)

        # Marketplace fee (va a un wallet del sistema)
        marketplace_wallet = self._get_wallet("marketplace")
        marketplace_wallet.receive(fee)

        # Crear transacción
        transaction = Transaction(
            transaction_id=str(uuid.uuid4()),
            buyer_id=buy_order.user_id,
            seller_id=sell_order.user_id,
            asset_id=buy_order.asset_id,
            amount_dracma=total_amount,
            fee_dracma=fee,
            metadata={
                "buy_order_id": buy_order.order_id,
                "sell_order_id": sell_order.order_id,
                "quantity": buy_order.quantity,
                "unit_price": sell_order.price_dracma
            }
        )

        self.transactions.append(transaction)

        # Actualizar órdenes
        buy_order.status = OrderStatus.FILLED
        sell_order.status = OrderStatus.FILLED

        # Transferir ownership del asset
        asset.owner_id = buy_order.user_id
        asset.updated_at = datetime.utcnow()

        logger.info(f"Executed transaction: {total_amount} DracmaS for asset {buy_order.asset_id}")

    async def get_market_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del marketplace."""

        total_assets = len([a for a in self.assets.values() if a.is_active])
        total_orders = len([o for o in self.orders.values() if o.status in [OrderStatus.PENDING, OrderStatus.ACTIVE]])
        total_transactions = len(self.transactions)
        total_volume = sum(t.amount_DracmaS for t in self.transactions)

        # Assets por tipo
        assets_by_type = {}
        for asset in self.assets.values():
            if asset.is_active:
                asset_type = asset.asset_type.value
                assets_by_type[asset_type] = assets_by_type.get(asset_type, 0) + 1

        return {
            "total_assets": total_assets,
            "total_orders": total_orders,
            "total_transactions": total_transactions,
            "total_volume_dracma": total_volume,
            "assets_by_type": assets_by_type,
            "marketplace_fee_percent": self.marketplace_fee * 100
        }

    async def get_user_portfolio(self, user_id: str) -> Dict[str, Any]:
        """Obtener portfolio de usuario."""

        user_assets = [a for a in self.assets.values() if a.owner_id == user_id and a.is_active]
        user_orders = [o for o in self.orders.values() if o.user_id == user_id]
        user_transactions = [t for t in self.transactions if t.buyer_id == user_id or t.seller_id == user_id]

        wallet = self._get_wallet(user_id)

        return {
            "user_id": user_id,
            "balance_dracma": wallet.get_balance(),
            "assets_owned": len(user_assets),
            "active_orders": len([o for o in user_orders if o.status in [OrderStatus.PENDING, OrderStatus.ACTIVE]]),
            "total_transactions": len(user_transactions),
            "assets": [a.to_dict() for a in user_assets[:10]],  # Primeros 10
            "recent_transactions": [t.to_dict() for t in user_transactions[-5:]]  # Últimas 5
        }


# Instancia global del marketplace
_marketplace: Optional[MarketplaceEngine] = None


async def get_marketplace() -> MarketplaceEngine:
    """Obtener instancia global del marketplace."""
    global _marketplace
    if _marketplace is None:
        _marketplace = MarketplaceEngine()
        # Inicializar con algunos assets de demo
        await _initialize_demo_assets(_marketplace)
    return _marketplace


async def _initialize_demo_assets(marketplace: MarketplaceEngine) -> None:
    """Inicializar marketplace con assets de demo."""

    demo_assets = [
        {
            "owner_id": "ailoos_official",
            "asset_type": AssetType.MODEL,
            "title": "EmpoorioLM-7B Fine-tuned Legal",
            "description": "Modelo especializado en análisis legal y contratos",
            "price_dracma": 500.0,
            "metadata": {"model_size": "7B", "specialization": "legal", "accuracy": 0.89},
            "tags": ["model", "legal", "enterprise"]
        },
        {
            "owner_id": "ailoos_official",
            "asset_type": AssetType.DATASET,
            "title": "Pile of Law Dataset (50GB)",
            "description": "Dataset masivo de documentos legales tokenizados",
            "price_dracma": 200.0,
            "metadata": {"size_gb": 50, "tokens": 10000000, "domain": "legal"},
            "tags": ["dataset", "legal", "training"]
        },
        {
            "owner_id": "research_lab",
            "asset_type": AssetType.COMPUTE,
            "title": "100 GPU Hours (A100)",
            "description": "Capacidad de cómputo para training distribuido",
            "price_dracma": 1000.0,
            "metadata": {"gpu_type": "A100", "hours": 100, "region": "us-central1"},
            "tags": ["compute", "gpu", "training"]
        },
        {
            "owner_id": "enterprise_user",
            "asset_type": AssetType.API_ACCESS,
            "title": "API Access Pro Tier (Monthly)",
            "description": "Acceso ilimitado a API con rate limiting PRO",
            "price_dracma": 100.0,
            "metadata": {"tier": "pro", "period": "monthly", "requests_limit": "unlimited"},
            "tags": ["api", "subscription", "pro"]
        }
    ]

    for asset_data in demo_assets:
        await marketplace.create_asset(**asset_data)


async def demo_marketplace():
    """Demo interactiva del marketplace DRACMA."""

    print("🚀 AILOOS DracmaS Marketplace Demo")
    print("=" * 50)

    marketplace = await get_marketplace()

    # Mostrar estadísticas iniciales
    stats = await marketplace.get_market_stats()
    print("📊 Estadísticas del Marketplace:")
    print(f"   • Assets totales: {stats['total_assets']}")
    print(f"   • Fee del marketplace: {stats['marketplace_fee_percent']}%")
    print(f"   • Assets por tipo: {stats['assets_by_type']}")

    # Listar assets disponibles
    print("\n🛒 Assets disponibles:")
    assets = await marketplace.list_assets(limit=10)
    for i, asset in enumerate(assets, 1):
        print(f"{i}. {asset.title} - {asset.price_dracma} DRACMA")
        print(f"   {asset.description}")
        print(f"   Tags: {', '.join(asset.tags)}")
        print()

    # Simular transacción
    print("💰 Simulando transacción...")

    # Usuario 1 crea orden de compra
    buyer_id = "demo_buyer"
    asset_to_buy = assets[0]  # Primer asset

    print(f"👤 Comprador {buyer_id} quiere comprar: {asset_to_buy.title}")

    # Verificar balance inicial
    buyer_portfolio = await marketplace.get_user_portfolio(buyer_id)
    print(f"💰 Balance inicial: {buyer_portfolio['balance_dracma']} DRACMA")

    # Colocar orden de compra
    order = await marketplace.place_order(
        user_id=buyer_id,
        asset_id=asset_to_buy.asset_id,
        order_type=OrderType.BUY
    )

    print(f"📋 Orden creada: {order.order_id}")

    # Simular que hay un vendedor
    seller_id = asset_to_buy.owner_id
    sell_order = await marketplace.place_order(
        user_id=seller_id,
        asset_id=asset_to_buy.asset_id,
        order_type=OrderType.SELL,
        price_dracma=asset_to_buy.price_dracma
    )

    print(f"🏪 Vendedor {seller_id} pone en venta el asset")

    # Matching debería ocurrir automáticamente
    await asyncio.sleep(0.1)  # Pequeña pausa para processing

    # Verificar resultado
    final_portfolio = await marketplace.get_user_portfolio(buyer_id)
    print(f"💰 Balance final: {final_portfolio['balance_dracma']} DRACMA")
    print(f"📦 Assets owned: {final_portfolio['assets_owned']}")

    # Mostrar transacciones
    final_stats = await marketplace.get_market_stats()
    print("\n📊 Estadísticas finales:")
    print(f"   • Transacciones totales: {final_stats['total_transactions']}")
    print(f"   • Volumen total: {final_stats['total_volume_dracma']} DRACMA")

    print("\n✅ Demo completada exitosamente!")
    print("🚀 El marketplace DracmaS está listo para trading real de IA!")


if __name__ == "__main__":
    asyncio.run(demo_marketplace())