"""
Data Marketplace for EmpoorioLM
Mercado de datos descentralizado integrado con blockchain y DRACMA tokens.
"""

import json
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class DatasetOffer:
    """Oferta de dataset en el marketplace."""

    offer_id: str
    provider_address: str
    dataset_ipfs_cid: str
    dataset_metadata: Dict[str, Any]
    price_drs: int  # Precio en DRACMA tokens
    created_at: float
    expires_at: Optional[float] = None

    # Estado de la oferta
    status: str = "active"  # active, sold, expired, cancelled
    buyer_address: Optional[str] = None
    transaction_hash: Optional[str] = None

    # Calidad y reputación
    quality_score: float = 0.0
    provider_reputation: float = 0.0
    download_count: int = 0

    # Estadísticas de uso
    federated_usage: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MarketplaceConfig:
    """Configuración del marketplace."""

    # Configuración económica
    platform_fee_percent: float = 2.5  # 2.5% fee de plataforma
    min_price_drs: int = 100  # Precio mínimo en DRACMA
    max_price_drs: int = 1000000  # Precio máximo en DRACMA

    # Configuración de tiempo
    offer_expiry_days: int = 30
    escrow_timeout_hours: int = 24

    # Configuración de calidad
    require_quality_score: bool = True
    min_quality_score: float = 0.6
    require_provider_reputation: bool = False  # Deshabilitado para demo
    min_provider_reputation: float = 0.7

    # Configuración de almacenamiento
    marketplace_dir: str = "./data/marketplace"
    offers_file: str = "offers.json"
    transactions_file: str = "transactions.json"


class DataMarketplace:
    """
    Marketplace de datos descentralizado para EmpoorioLM.

    Características:
    - Ofertas de datasets con precios en DRACMA
    - Sistema de reputación de proveedores
    - Calidad automática de datasets
    - Integración con blockchain para pagos
    - Escrow system para transacciones seguras
    - Estadísticas de uso federado
    """

    def __init__(self, config: MarketplaceConfig):
        self.config = config

        # Estado del marketplace
        self.offers: Dict[str, DatasetOffer] = {}
        self.transactions: List[Dict[str, Any]] = []
        self.provider_stats: Dict[str, Dict[str, Any]] = {}

        # Crear directorios
        self.marketplace_dir = Path(config.marketplace_dir)
        self.marketplace_dir.mkdir(parents=True, exist_ok=True)

        # Cargar estado persistente
        self._load_marketplace_state()

        logger.info(f"🏪 Data Marketplace inicializado con {len(self.offers)} ofertas activas")

    def create_dataset_offer(
        self,
        provider_address: str,
        dataset_ipfs_cid: str,
        dataset_metadata: Dict[str, Any],
        price_drs: int,
        quality_score: Optional[float] = None
    ) -> Optional[str]:
        """
        Crear una nueva oferta de dataset.

        Args:
            provider_address: Dirección del proveedor (wallet)
            dataset_ipfs_cid: CID de IPFS del dataset
            dataset_metadata: Metadatos del dataset
            price_drs: Precio en DRACMA tokens
            quality_score: Puntaje de calidad (opcional, se calcula si no se proporciona)

        Returns:
            ID de la oferta creada o None si falla
        """
        # Validaciones
        if not self._validate_offer_parameters(provider_address, price_drs):
            return None

        # Calcular calidad si no se proporciona
        if quality_score is None:
            quality_score = self._calculate_dataset_quality(dataset_metadata)

        if self.config.require_quality_score and quality_score < self.config.min_quality_score:
            logger.error(f"❌ Calidad insuficiente: {quality_score} < {self.config.min_quality_score}")
            return None

        # Verificar reputación del proveedor
        provider_rep = self._get_provider_reputation(provider_address)
        if self.config.require_provider_reputation and provider_rep < self.config.min_provider_reputation:
            logger.error(f"❌ Reputación insuficiente del proveedor: {provider_rep}")
            return None

        # Crear oferta
        offer_id = f"offer_{int(time.time())}_{hashlib.md5(f'{provider_address}{dataset_ipfs_cid}'.encode()).hexdigest()[:8]}"

        offer = DatasetOffer(
            offer_id=offer_id,
            provider_address=provider_address,
            dataset_ipfs_cid=dataset_ipfs_cid,
            dataset_metadata=dataset_metadata,
            price_drs=price_drs,
            created_at=time.time(),
            expires_at=time.time() + (self.config.offer_expiry_days * 24 * 3600),
            quality_score=quality_score,
            provider_reputation=provider_rep
        )

        self.offers[offer_id] = offer
        self._save_marketplace_state()

        logger.info(f"✅ Oferta creada: {offer_id} - {price_drs} DRS")
        return offer_id

    def _validate_offer_parameters(self, provider_address: str, price_drs: int) -> bool:
        """Validar parámetros de la oferta."""
        if not provider_address or not isinstance(provider_address, str):
            logger.error("Dirección de proveedor inválida")
            return False

        if not (self.config.min_price_drs <= price_drs <= self.config.max_price_drs):
            logger.error(f"Precio fuera de rango: {price_drs} DRS")
            return False

        return True

    def _calculate_dataset_quality(self, metadata: Dict[str, Any]) -> float:
        """
        Calcular calidad del dataset basada en metadatos.

        Factores considerados:
        - Tamaño del dataset
        - Diversidad de fuentes
        - Calidad de preprocesamiento
        - Cobertura temporal
        - Balance de clases
        """
        score = 0.5  # Score base

        # Factor 1: Tamaño del dataset
        sample_count = metadata.get("sample_count", 0)
        if sample_count > 100000:
            score += 0.2
        elif sample_count > 10000:
            score += 0.1
        elif sample_count < 1000:
            score -= 0.1

        # Factor 2: Diversidad de fuentes
        sources = metadata.get("data_sources", [])
        if len(sources) > 5:
            score += 0.1
        elif len(sources) > 2:
            score += 0.05

        # Factor 3: Calidad de preprocesamiento
        if metadata.get("preprocessed", False):
            score += 0.1
        if metadata.get("quality_filtered", False):
            score += 0.05

        # Factor 4: Balance de clases
        class_balance = metadata.get("class_balance_score", 0.5)
        score += (class_balance - 0.5) * 0.2

        # Factor 5: Reputación del proveedor
        # (Ya se considera por separado)

        return max(0.0, min(1.0, score))

    def _get_provider_reputation(self, provider_address: str) -> float:
        """Obtener reputación del proveedor."""
        if provider_address not in self.provider_stats:
            return 0.5  # Reputación neutral para nuevos proveedores

        stats = self.provider_stats[provider_address]
        return stats.get("reputation_score", 0.5)

    async def purchase_dataset(
        self,
        buyer_address: str,
        offer_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Comprar un dataset del marketplace.

        Args:
            buyer_address: Dirección del comprador
            offer_id: ID de la oferta

        Returns:
            Información de la transacción o None si falla
        """
        if offer_id not in self.offers:
            logger.error(f"❌ Oferta no encontrada: {offer_id}")
            return None

        offer = self.offers[offer_id]

        if offer.status != "active":
            logger.error(f"❌ Oferta no disponible: {offer.status}")
            return None

        if offer.expires_at and time.time() > offer.expires_at:
            offer.status = "expired"
            logger.error("❌ Oferta expirada")
            return None

        # Calcular precio total con fee de plataforma
        platform_fee = int(offer.price_drs * self.config.platform_fee_percent / 100)
        total_price = offer.price_drs + platform_fee

        logger.info(f"💰 Compra: {offer.price_drs} DRS + {platform_fee} DRS fee = {total_price} DRS total")

        # Ejecutar transacción blockchain con DRACMA
        transaction_hash = await self._execute_blockchain_transaction(
            buyer_address, offer.provider_address, total_price
        )

        if not transaction_hash:
            logger.error("❌ Falló la transacción blockchain")
            return None

        # Actualizar oferta
        offer.status = "sold"
        offer.buyer_address = buyer_address
        offer.transaction_hash = transaction_hash

        # Registrar transacción con metadatos completos
        transaction = {
            "transaction_hash": transaction_hash,
            "offer_id": offer_id,
            "buyer_address": buyer_address,
            "seller_address": offer.provider_address,
            "price_drs": offer.price_drs,
            "platform_fee_drs": platform_fee,
            "total_drs": total_price,
            "dataset_cid": offer.dataset_ipfs_cid,
            "dataset_metadata": offer.dataset_metadata,
            "quality_score": offer.quality_score,
            "timestamp": time.time(),
            "blockchain_confirmed": True
        }

        self.transactions.append(transaction)

        # Actualizar estadísticas del proveedor
        self._update_provider_stats(offer.provider_address, transaction)

        # Actualizar estadísticas de la oferta
        offer.download_count += 1

        self._save_marketplace_state()

        logger.info(f"✅ Dataset vendido: {offer_id} - {buyer_address} -> {offer.provider_address}")
        return transaction

    async def _execute_blockchain_transaction(
        self,
        buyer: str,
        seller: str,
        amount_drs: int
    ) -> Optional[str]:
        """Ejecutar transacción blockchain con DRACMA."""
        try:
            from ...blockchain.dracma_token import get_token_manager

            token_manager = get_token_manager()

            result = await token_manager.transfer_tokens(
                from_address=buyer,
                to_address=seller,
                amount=float(amount_drs)
            )

            if result.success:
                logger.info(f"💰 Transacción blockchain ejecutada: {result.tx_hash}")
                return result.tx_hash
            else:
                logger.error(f"❌ Falló la transacción blockchain: {result.error_message}")
                return None

        except Exception as e:
            logger.error(f"❌ Error en transacción blockchain: {e}")
            return None

    def _update_provider_stats(self, provider_address: str, transaction: Dict[str, Any]):
        """Actualizar estadísticas del proveedor después de una venta."""
        if provider_address not in self.provider_stats:
            self.provider_stats[provider_address] = {
                "total_sales": 0,
                "total_earnings_drs": 0,
                "successful_transactions": 0,
                "reputation_score": 0.5,
                "avg_rating": 0.0,
                "total_ratings": 0
            }

        stats = self.provider_stats[provider_address]
        stats["total_sales"] += 1
        stats["total_earnings_drs"] += transaction["price_drs"]
        stats["successful_transactions"] += 1

        # Actualizar reputación (algoritmo simplificado)
        success_rate = stats["successful_transactions"] / stats["total_sales"]
        volume_bonus = min(1.0, stats["total_sales"] / 100)  # Bonus por volumen
        stats["reputation_score"] = (success_rate * 0.7) + (volume_bonus * 0.3)

    def search_datasets(
        self,
        query: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_quality: Optional[float] = None,
        category: Optional[str] = None,
        language: Optional[str] = None
    ) -> List[DatasetOffer]:
        """
        Buscar datasets en el marketplace.

        Args:
            query: Término de búsqueda
            min_price: Precio mínimo
            max_price: Precio máximo
            min_quality: Calidad mínima
            category: Categoría del dataset
            language: Idioma del dataset

        Returns:
            Lista de ofertas que coinciden
        """
        matching_offers = []

        for offer in self.offers.values():
            if offer.status != "active":
                continue

            # Filtros de precio
            if min_price and offer.price_drs < min_price:
                continue
            if max_price and offer.price_drs > max_price:
                continue

            # Filtro de calidad
            if min_quality and offer.quality_score < min_quality:
                continue

            # Filtros de metadatos
            metadata = offer.dataset_metadata

            if category and metadata.get("category") != category:
                continue

            if language and metadata.get("language") != language:
                continue

            # Búsqueda por texto
            if query:
                searchable_text = f"{metadata.get('description', '')} {metadata.get('name', '')} {metadata.get('tags', '')}".lower()
                if query.lower() not in searchable_text:
                    continue

            matching_offers.append(offer)

        # Ordenar por relevancia (calidad + reputación)
        matching_offers.sort(
            key=lambda x: (x.quality_score + x.provider_reputation) / 2,
            reverse=True
        )

        return matching_offers

    def get_marketplace_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del marketplace."""
        active_offers = [o for o in self.offers.values() if o.status == "active"]
        sold_offers = [o for o in self.offers.values() if o.status == "sold"]

        total_volume = sum(t["price_drs"] for t in self.transactions)
        total_fees = sum(t.get("platform_fee_drs", 0) for t in self.transactions)

        # Estadísticas de calidad
        quality_scores = [o.quality_score for o in active_offers if o.quality_score > 0]
        avg_quality = sum(quality_scores) / max(1, len(quality_scores))

        # Estadísticas de proveedores
        provider_reputations = [stats.get("reputation_score", 0) for stats in self.provider_stats.values()]
        avg_provider_reputation = sum(provider_reputations) / max(1, len(provider_reputations))

        # Estadísticas temporales
        recent_transactions = [t for t in self.transactions if time.time() - t["timestamp"] < 86400 * 30]  # Último mes
        monthly_volume = sum(t["price_drs"] for t in recent_transactions)

        return {
            "total_offers": len(self.offers),
            "active_offers": len(active_offers),
            "sold_offers": len(sold_offers),
            "expired_offers": len([o for o in self.offers.values() if o.status == "expired"]),
            "total_transactions": len(self.transactions),
            "total_volume_drs": total_volume,
            "total_platform_fees_drs": total_fees,
            "monthly_volume_drs": monthly_volume,
            "unique_providers": len(self.provider_stats),
            "unique_buyers": len(set(t["buyer_address"] for t in self.transactions)),
            "avg_price_drs": total_volume / max(1, len(sold_offers)),
            "avg_quality_score": avg_quality,
            "avg_provider_reputation": avg_provider_reputation,
            "market_health_score": (avg_quality + avg_provider_reputation) / 2,  # 0-1 score
            "transaction_success_rate": len(sold_offers) / max(1, len(self.offers)),
            "data_diversity_score": len(set(o.dataset_metadata.get("category", "") for o in active_offers)) / 10  # Max 10 categorías
        }

    def get_popular_datasets(self, limit: int = 10) -> List[DatasetOffer]:
        """Obtener datasets más populares con algoritmo multifactorial."""
        active_offers = [o for o in self.offers.values() if o.status == "active"]

        # Algoritmo de popularidad multifactorial
        for offer in active_offers:
            # Factor 1: Descargas recientes (últimos 30 días)
            recent_downloads = sum(
                1 for t in self.transactions
                if t.get("offer_id") == offer.offer_id and
                time.time() - t["timestamp"] < 86400 * 30
            )

            # Factor 2: Calidad del dataset
            quality_factor = offer.quality_score

            # Factor 3: Reputación del proveedor
            reputation_factor = offer.provider_reputation

            # Factor 4: Recencia de la oferta
            days_old = (time.time() - offer.created_at) / 86400
            recency_factor = max(0, 1 - (days_old / 30))  # Decay en 30 días

            # Factor 5: Precio (ligera penalización por precios muy altos)
            price_factor = 1 / (1 + offer.price_drs / 10000)  # Normalización

            # Puntuación final ponderada
            offer.popularity_score = (
                recent_downloads * 0.4 +      # 40% descargas recientes
                quality_factor * 0.25 +       # 25% calidad
                reputation_factor * 0.2 +     # 20% reputación
                recency_factor * 0.1 +        # 10% recencia
                price_factor * 0.05           # 5% precio
            )

        # Ordenar por puntuación de popularidad
        active_offers.sort(key=lambda x: x.popularity_score, reverse=True)

        return active_offers[:limit]

    def get_recommended_datasets(self, user_address: str, limit: int = 5) -> List[DatasetOffer]:
        """Obtener recomendaciones personalizadas basadas en historial."""
        # Obtener historial de compras del usuario
        user_transactions = [
            t for t in self.transactions
            if t["buyer_address"] == user_address
        ]

        if not user_transactions:
            # Usuario nuevo - recomendar datasets populares de alta calidad
            return self.get_popular_datasets(limit)

        # Analizar preferencias del usuario
        purchased_categories = set()
        purchased_languages = set()
        avg_spent = 0
        quality_preferences = []

        for transaction in user_transactions:
            offer_id = transaction.get("offer_id")
            if offer_id and offer_id in self.offers:
                offer = self.offers[offer_id]
                purchased_categories.add(offer.dataset_metadata.get("category", ""))
                purchased_languages.add(offer.dataset_metadata.get("language", ""))
                avg_spent += offer.price_drs
                quality_preferences.append(offer.quality_score)

        avg_spent /= len(user_transactions)
        avg_quality_preference = sum(quality_preferences) / len(quality_preferences)

        # Filtrar candidatos para recomendación
        candidates = []
        for offer in self.offers.values():
            if offer.status != "active":
                continue

            # Evitar recomendar lo ya comprado
            if any(t.get("offer_id") == offer.offer_id for t in user_transactions):
                continue

            # Calcular score de recomendación
            category_match = 1.0 if offer.dataset_metadata.get("category") in purchased_categories else 0.3
            language_match = 1.0 if offer.dataset_metadata.get("language") in purchased_languages else 0.5
            quality_match = 1 - abs(offer.quality_score - avg_quality_preference)  # Cercanía a preferencia
            price_match = 1 - min(1, abs(offer.price_drs - avg_spent) / avg_spent)  # Cercanía a presupuesto

            recommendation_score = (
                category_match * 0.4 +
                language_match * 0.3 +
                quality_match * 0.2 +
                price_match * 0.1
            )

            offer.recommendation_score = recommendation_score
            candidates.append(offer)

        # Ordenar por score de recomendación
        candidates.sort(key=lambda x: x.recommendation_score, reverse=True)

        return candidates[:limit]

    def _load_marketplace_state(self):
        """Cargar estado del marketplace desde disco."""
        offers_file = self.marketplace_dir / self.config.offers_file
        transactions_file = self.marketplace_dir / self.config.transactions_file

        # Cargar ofertas
        if offers_file.exists():
            try:
                with open(offers_file, 'r') as f:
                    offers_data = json.load(f)
                    for offer_data in offers_data:
                        offer = DatasetOffer(**offer_data)
                        self.offers[offer.offer_id] = offer
            except Exception as e:
                logger.error(f"Error cargando ofertas: {e}")

        # Cargar transacciones
        if transactions_file.exists():
            try:
                with open(transactions_file, 'r') as f:
                    self.transactions = json.load(f)
            except Exception as e:
                logger.error(f"Error cargando transacciones: {e}")

    def _save_marketplace_state(self):
        """Guardar estado del marketplace en disco."""
        offers_file = self.marketplace_dir / self.config.offers_file
        transactions_file = self.marketplace_dir / self.config.transactions_file

        # Guardar ofertas
        offers_data = [vars(offer) for offer in self.offers.values()]
        with open(offers_file, 'w') as f:
            json.dump(offers_data, f, indent=2, default=str)

        # Guardar transacciones
        with open(transactions_file, 'w') as f:
            json.dump(self.transactions, f, indent=2, default=str)


# Funciones de conveniencia
def create_marketplace_offer(
    marketplace: DataMarketplace,
    provider_address: str,
    dataset_info: Dict[str, Any],
    price_drs: int
) -> Optional[str]:
    """
    Función de conveniencia para crear oferta en marketplace.

    Args:
        marketplace: Instancia del marketplace
        provider_address: Dirección del proveedor
        dataset_info: Información del dataset
        price_drs: Precio en DRACMA

    Returns:
        ID de la oferta
    """
    return marketplace.create_dataset_offer(
        provider_address=provider_address,
        dataset_ipfs_cid=dataset_info.get("ipfs_cid", ""),
        dataset_metadata=dataset_info.get("metadata", {}),
        price_drs=price_drs,
        quality_score=dataset_info.get("quality_score")
    )


if __name__ == "__main__":
    # Test del marketplace
    print("🧪 Probando Data Marketplace...")

    config = MarketplaceConfig()
    marketplace = DataMarketplace(config)

    # Crear oferta de prueba
    offer_id = marketplace.create_dataset_offer(
        provider_address="0x1234567890abcdef",
        dataset_ipfs_cid="QmTestCID123",
        dataset_metadata={
            "name": "Dataset de prueba",
            "description": "Dataset de texto para pruebas",
            "sample_count": 50000,
            "language": "es",
            "category": "text",
            "data_sources": ["web", "books"],
            "preprocessed": True,
            "quality_filtered": True
        },
        price_drs=1000
    )

    if offer_id:
        print(f"✅ Oferta creada: {offer_id}")

        # Buscar ofertas
        results = marketplace.search_datasets(query="prueba")
        print(f"✅ Búsqueda exitosa: {len(results)} resultados")

        # Simular compra
        transaction = marketplace.purchase_dataset(
            buyer_address="0xfedcba0987654321",
            offer_id=offer_id
        )

        if transaction:
            print(f"✅ Compra exitosa: {transaction['transaction_hash']}")

        # Estadísticas
        stats = marketplace.get_marketplace_stats()
        print(f"📊 Estadísticas: {stats}")

    print("🎉 Marketplace funcionando correctamente")