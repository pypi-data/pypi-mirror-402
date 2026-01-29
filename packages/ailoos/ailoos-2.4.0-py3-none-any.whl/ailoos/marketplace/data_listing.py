"""
Sistema de listings de datos para AILOOS Marketplace.
Publicación y gestión de datasets para venta.
"""

import json
import time
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class DataCategory(Enum):
    IMAGE_DATA = "image_data"
    TEXT_DATA = "text_data"
    AUDIO_DATA = "audio_data"
    TABULAR_DATA = "tabular_data"
    TIME_SERIES = "time_series"
    MEDICAL_DATA = "medical_data"
    FINANCIAL_DATA = "financial_data"
    IoT_DATA = "iot_data"


class ListingStatus(Enum):
    ACTIVE = "active"
    SOLD = "sold"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class DataListing:
    """Listing de datos en el marketplace."""
    listing_id: str
    seller_address: str
    title: str
    description: str
    category: DataCategory
    data_hash: str
    ipfs_cid: str
    price_dracma: float
    data_size_mb: float
    sample_count: int
    quality_score: float
    tags: List[str]
    created_at: float
    expires_at: float
    status: ListingStatus
    transaction_hash: Optional[str] = None
    buyer_address: Optional[str] = None


class DataMarketplace:
    """
    Marketplace para intercambio de datos entre nodos federados.
    Gestiona listings, transacciones y reputación.
    """

    def __init__(self):
        self.listings: Dict[str, DataListing] = {}
        self.user_listings: Dict[str, List[str]] = {}  # address -> listing_ids
        self.purchases: Dict[str, List[str]] = {}  # address -> purchased_listing_ids

    def create_listing(self, seller_address: str, title: str, description: str,
                      category: DataCategory, data_hash: str, ipfs_cid: str,
                      price_dracma: float, data_size_mb: float, sample_count: int,
                      quality_score: float, tags: List[str], duration_days: int = 30) -> str:
        """
        Crea un nuevo listing de datos.

        Args:
            seller_address: Dirección del vendedor
            title: Título del dataset
            description: Descripción detallada
            category: Categoría de datos
            data_hash: Hash de integridad de los datos
            ipfs_cid: CID de IPFS donde están almacenados
            price_dracma: Precio en DRACMA
            data_size_mb: Tamaño en MB
            sample_count: Número de muestras
            quality_score: Puntaje de calidad (0-1)
            tags: Etiquetas para búsqueda
            duration_days: Días que dura el listing

        Returns:
            ID del listing creado
        """
        listing_id = self._generate_listing_id(seller_address, data_hash)

        # Validar calidad mínima
        if quality_score < 0.5:
            raise ValueError("La calidad del dataset debe ser al menos 0.5")

        # Validar precio razonable
        if price_DracmaS <= 0:
            raise ValueError("El precio debe ser mayor a 0 DRACMA")

        listing = DataListing(
            listing_id=listing_id,
            seller_address=seller_address,
            title=title,
            description=description,
            category=category,
            data_hash=data_hash,
            ipfs_cid=ipfs_cid,
            price_dracma=price_dracma,
            data_size_mb=data_size_mb,
            sample_count=sample_count,
            quality_score=quality_score,
            tags=tags,
            created_at=time.time(),
            expires_at=time.time() + (duration_days * 24 * 60 * 60),
            status=ListingStatus.ACTIVE
        )

        self.listings[listing_id] = listing

        # Registrar en listings del usuario
        if seller_address not in self.user_listings:
            self.user_listings[seller_address] = []
        self.user_listings[seller_address].append(listing_id)

        return listing_id

    def purchase_listing(self, buyer_address: str, listing_id: str,
                        transaction_hash: str) -> bool:
        """
        Compra un listing de datos.

        Args:
            buyer_address: Dirección del comprador
            listing_id: ID del listing
            transaction_hash: Hash de la transacción DRACMA

        Returns:
            True si la compra fue exitosa
        """
        if listing_id not in self.listings:
            raise ValueError(f"Listing {listing_id} no existe")

        listing = self.listings[listing_id]

        if listing.status != ListingStatus.ACTIVE:
            raise ValueError(f"Listing {listing_id} no está disponible")

        if listing.seller_address == buyer_address:
            raise ValueError("No puedes comprar tu propio listing")

        if time.time() > listing.expires_at:
            listing.status = ListingStatus.EXPIRED
            raise ValueError(f"Listing {listing_id} ha expirado")

        # Marcar como vendido
        listing.status = ListingStatus.SOLD
        listing.buyer_address = buyer_address
        listing.transaction_hash = transaction_hash

        # Registrar compra
        if buyer_address not in self.purchases:
            self.purchases[buyer_address] = []
        self.purchases[buyer_address].append(listing_id)

        return True

    def search_listings(self, query: str = "", category: Optional[DataCategory] = None,
                       min_price: float = 0, max_price: float = float('inf'),
                       min_quality: float = 0, tags: List[str] = None,
                       limit: int = 50) -> List[DataListing]:
        """
        Busca listings disponibles.

        Args:
            query: Término de búsqueda en título/descripción
            category: Filtrar por categoría
            min_price: Precio mínimo
            max_price: Precio máximo
            min_quality: Calidad mínima
            tags: Etiquetas requeridas
            limit: Máximo número de resultados

        Returns:
            Lista de listings que coinciden
        """
        results = []

        for listing in self.listings.values():
            # Filtros básicos
            if listing.status != ListingStatus.ACTIVE:
                continue

            if time.time() > listing.expires_at:
                listing.status = ListingStatus.EXPIRED
                continue

            if not (min_price <= listing.price_DracmaS <= max_price):
                continue

            if listing.quality_score < min_quality:
                continue

            if category and listing.category != category:
                continue

            # Filtro de etiquetas
            if tags:
                if not all(tag in listing.tags for tag in tags):
                    continue

            # Búsqueda de texto
            if query:
                search_text = f"{listing.title} {listing.description}".lower()
                if query.lower() not in search_text:
                    continue

            results.append(listing)

        # Ordenar por calidad y precio (mejor calidad primero, luego precio)
        results.sort(key=lambda x: (-x.quality_score, x.price_dracma))

        return results[:limit]

    def get_listing_details(self, listing_id: str) -> Optional[DataListing]:
        """Obtiene detalles de un listing específico."""
        return self.listings.get(listing_id)

    def get_user_listings(self, user_address: str) -> List[DataListing]:
        """Obtiene listings de un usuario."""
        listing_ids = self.user_listings.get(user_address, [])
        return [self.listings[lid] for lid in listing_ids if lid in self.listings]

    def get_user_purchases(self, user_address: str) -> List[DataListing]:
        """Obtiene compras de un usuario."""
        listing_ids = self.purchases.get(user_address, [])
        return [self.listings[lid] for lid in listing_ids if lid in self.listings]

    def cancel_listing(self, seller_address: str, listing_id: str) -> bool:
        """
        Cancela un listing (solo el vendedor).

        Args:
            seller_address: Dirección del vendedor
            listing_id: ID del listing

        Returns:
            True si se canceló exitosamente
        """
        if listing_id not in self.listings:
            return False

        listing = self.listings[listing_id]

        if listing.seller_address != seller_address:
            raise ValueError("Solo el vendedor puede cancelar el listing")

        if listing.status != ListingStatus.ACTIVE:
            raise ValueError("Solo se pueden cancelar listings activos")

        listing.status = ListingStatus.CANCELLED
        return True

    def get_market_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del marketplace."""
        active_listings = [l for l in self.listings.values() if l.status == ListingStatus.ACTIVE]
        sold_listings = [l for l in self.listings.values() if l.status == ListingStatus.SOLD]

        total_volume = sum(l.price_DracmaS for l in sold_listings)
        avg_price = total_volume / len(sold_listings) if sold_listings else 0

        # Estadísticas por categoría
        category_stats = {}
        for listing in active_listings + sold_listings:
            cat = listing.category.value
            if cat not in category_stats:
                category_stats[cat] = {"count": 0, "avg_price": 0, "total_value": 0}
            category_stats[cat]["count"] += 1
            category_stats[cat]["total_value"] += listing.price_dracma

        for cat in category_stats:
            stats = category_stats[cat]
            stats["avg_price"] = stats["total_value"] / stats["count"] if stats["count"] > 0 else 0

        return {
            "total_listings": len(self.listings),
            "active_listings": len(active_listings),
            "sold_listings": len(sold_listings),
            "total_volume_dracma": total_volume,
            "average_price_dracma": avg_price,
            "unique_sellers": len(self.user_listings),
            "unique_buyers": len(self.purchases),
            "category_stats": category_stats
        }

    def validate_data_integrity(self, listing_id: str, downloaded_hash: str,
                               metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Valida la integridad completa de datos descargados.

        Args:
            listing_id: ID del listing
            downloaded_hash: Hash de los datos descargados
            metadata: Metadatos adicionales para validación

        Returns:
            Dict con resultado de validación y detalles
        """
        validation_result = {
            "valid": False,
            "checks": {},
            "errors": [],
            "warnings": []
        }

        listing = self.get_listing_details(listing_id)
        if not listing:
            validation_result["errors"].append("Listing not found")
            return validation_result

        # 1. Hash validation
        hash_valid = listing.data_hash == downloaded_hash
        validation_result["checks"]["hash_integrity"] = hash_valid
        if not hash_valid:
            validation_result["errors"].append(f"Hash mismatch: expected {listing.data_hash}, got {downloaded_hash}")

        # 2. Metadata validation
        if metadata:
            metadata_valid = self._validate_metadata_integrity(listing, metadata)
            validation_result["checks"]["metadata_integrity"] = metadata_valid
            if not metadata_valid:
                validation_result["errors"].append("Metadata validation failed")

        # 3. Size validation
        if metadata and "file_size_bytes" in metadata:
            expected_size = listing.data_size_mb * 1024 * 1024  # Convert MB to bytes
            actual_size = metadata["file_size_bytes"]
            size_tolerance = 0.05  # 5% tolerance
            size_valid = abs(expected_size - actual_size) / expected_size <= size_tolerance
            validation_result["checks"]["size_validation"] = size_valid
            if not size_valid:
                validation_result["warnings"].append(f"Size mismatch: expected ~{expected_size}, got {actual_size}")

        # 4. Sample count validation (if applicable)
        if metadata and "sample_count" in metadata:
            expected_samples = listing.sample_count
            actual_samples = metadata["sample_count"]
            samples_valid = abs(expected_samples - actual_samples) / max(expected_samples, 1) <= 0.1  # 10% tolerance
            validation_result["checks"]["sample_validation"] = samples_valid
            if not samples_valid:
                validation_result["warnings"].append(f"Sample count mismatch: expected {expected_samples}, got {actual_samples}")

        # 5. IPFS validation (if available)
        if hasattr(self, '_validate_ipfs_integrity'):
            ipfs_valid = self._validate_ipfs_integrity(listing)
            validation_result["checks"]["ipfs_validation"] = ipfs_valid

        # 6. Temporal validation
        current_time = time.time()
        if current_time > listing.expires_at:
            validation_result["warnings"].append("Listing has expired")
        if current_time < listing.created_at:
            validation_result["errors"].append("Invalid timestamp: data from future")

        # 7. Transaction validation
        if listing.transaction_hash:
            tx_valid = self._validate_transaction_integrity(listing)
            validation_result["checks"]["transaction_validation"] = tx_valid

        # Overall validation
        critical_checks = ["hash_integrity", "metadata_integrity"]
        validation_result["valid"] = all(
            validation_result["checks"].get(check, False)
            for check in critical_checks
        ) and len(validation_result["errors"]) == 0

        return validation_result

    def _validate_metadata_integrity(self, listing: DataListing, metadata: Dict[str, Any]) -> bool:
        """Validate metadata integrity."""
        try:
            # Check required metadata fields
            required_fields = ["data_format", "encoding", "compression"]
            for field in required_fields:
                if field not in metadata:
                    return False

            # Validate data format matches category
            data_format = metadata.get("data_format", "").lower()
            category_formats = {
                DataCategory.IMAGE_DATA: ["jpg", "png", "jpeg", "tiff", "bmp"],
                DataCategory.TEXT_DATA: ["txt", "json", "csv", "xml"],
                DataCategory.AUDIO_DATA: ["wav", "mp3", "flac", "ogg"],
                DataCategory.TABULAR_DATA: ["csv", "json", "parquet", "feather"],
                DataCategory.TIME_SERIES: ["csv", "json", "parquet"],
                DataCategory.MEDICAL_DATA: ["dicom", "nifti", "json"],
                DataCategory.FINANCIAL_DATA: ["csv", "json", "xml"],
                DataCategory.IoT_DATA: ["json", "csv", "parquet"]
            }

            expected_formats = category_formats.get(listing.category, [])
            if expected_formats and data_format not in expected_formats:
                return False

            # Validate quality score consistency
            if "quality_score" in metadata:
                metadata_quality = metadata["quality_score"]
                if abs(metadata_quality - listing.quality_score) > 0.1:  # 10% tolerance
                    return False

            return True

        except Exception:
            return False

    def _validate_ipfs_integrity(self, listing: DataListing) -> bool:
        """Validate IPFS data integrity."""
        try:
            # This would integrate with IPFS validation
            # For now, basic checks
            if not listing.ipfs_cid:
                return False

            # Check CID format (basic validation)
            if not listing.ipfs_cid.startswith("Qm") and not listing.ipfs_cid.startswith("bafy"):
                return False

            # Could add: IPFS pinning status, gateway accessibility, etc.
            return True

        except Exception:
            return False

    def _validate_transaction_integrity(self, listing: DataListing) -> bool:
        """Validate transaction integrity."""
        try:
            # This would integrate with blockchain validation
            # For now, basic checks
            if not listing.transaction_hash:
                return False

            # Check transaction hash format
            if not listing.transaction_hash.startswith("0x") or len(listing.transaction_hash) != 66:
                return False

            # Could add: blockchain confirmation checks, etc.
            return True

        except Exception:
            return False

    def validate_purchase_eligibility(self, buyer_address: str, listing_id: str) -> Dict[str, Any]:
        """
        Validate if a buyer is eligible to purchase a listing.

        Args:
            buyer_address: Address of the buyer
            listing_id: ID of the listing

        Returns:
            Validation result
        """
        result = {
            "eligible": False,
            "checks": {},
            "reasons": []
        }

        listing = self.get_listing_details(listing_id)
        if not listing:
            result["reasons"].append("Listing not found")
            return result

        # Check if listing is available
        if listing.status != ListingStatus.ACTIVE:
            result["reasons"].append(f"Listing status is {listing.status.value}")
            return result

        # Check expiration
        if time.time() > listing.expires_at:
            result["reasons"].append("Listing has expired")
            return result

        # Check if buyer is not the seller
        if buyer_address == listing.seller_address:
            result["reasons"].append("Cannot purchase own listing")
            return result

        # Check if buyer hasn't already purchased
        if listing.buyer_address and listing.buyer_address == buyer_address:
            result["reasons"].append("Already purchased this listing")
            return result

        # All checks passed
        result["eligible"] = True
        result["checks"] = {
            "listing_active": True,
            "not_expired": True,
            "not_own_listing": True,
            "not_already_purchased": True
        }

        return result

    def generate_data_certificate(self, listing_id: str, buyer_address: str) -> Optional[Dict[str, Any]]:
        """
        Generate a data authenticity certificate.

        Args:
            listing_id: ID of the listing
            buyer_address: Address of the buyer

        Returns:
            Certificate data or None
        """
        listing = self.get_listing_details(listing_id)
        if not listing or listing.buyer_address != buyer_address:
            return None

        certificate = {
            "certificate_id": f"cert_{listing_id}_{buyer_address}_{int(time.time())}",
            "listing_id": listing_id,
            "buyer_address": buyer_address,
            "seller_address": listing.seller_address,
            "data_hash": listing.data_hash,
            "ipfs_cid": listing.ipfs_cid,
            "purchase_timestamp": listing.created_at,
            "certificate_timestamp": time.time(),
            "validity_period_days": 365,
            "verification_methods": [
                "hash_integrity",
                "metadata_validation",
                "transaction_verification"
            ]
        }

        # Add cryptographic signature (simplified)
        import hashlib
        cert_str = json.dumps(certificate, sort_keys=True)
        certificate["signature"] = hashlib.sha256(cert_str.encode()).hexdigest()

        return certificate

    def _generate_listing_id(self, seller_address: str, data_hash: str) -> str:
        """Genera ID único para un listing."""
        data = f"{seller_address}_{data_hash}_{time.time()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def export_listings(self, filename: str):
        """Exporta todos los listings a archivo JSON."""
        data = {
            "listings": {
                lid: {
                    "listing_id": l.listing_id,
                    "seller_address": l.seller_address,
                    "title": l.title,
                    "description": l.description,
                    "category": l.category.value,
                    "data_hash": l.data_hash,
                    "ipfs_cid": l.ipfs_cid,
                    "price_dracma": l.price_dracma,
                    "data_size_mb": l.data_size_mb,
                    "sample_count": l.sample_count,
                    "quality_score": l.quality_score,
                    "tags": l.tags,
                    "created_at": l.created_at,
                    "expires_at": l.expires_at,
                    "status": l.status.value,
                    "transaction_hash": l.transaction_hash,
                    "buyer_address": l.buyer_address
                }
                for lid, l in self.listings.items()
            },
            "exported_at": time.time()
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def import_listings(self, filename: str):
        """Importa listings desde archivo JSON."""
        with open(filename, 'r') as f:
            data = json.load(f)

        for lid, listing_data in data["listings"].items():
            listing_data["category"] = DataCategory(listing_data["category"])
            listing_data["status"] = ListingStatus(listing_data["status"])
            self.listings[lid] = DataListing(**listing_data)


# Instancia global del marketplace
data_marketplace = DataMarketplace()