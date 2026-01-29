"""
Massive Data Marketplace - Extended marketplace for handling massive datasets
with automatic listing creation, pricing strategies, and federated integration.
"""

import asyncio
import hashlib
import math
import time
import requests
from typing import Dict, List, Any, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import json

from ..core.logging import get_logger
from ..core.config import get_config, DataSourceConfig
from .data_listing import DataMarketplace, DataCategory, DataListing, ListingStatus
from .price_oracle import price_oracle
from ..infrastructure.ipfs_embedded import create_ipfs_manager

# Lazy import to avoid circular dependencies
if TYPE_CHECKING:
    from ..federated.data_coordinator import FederatedDataCoordinator
    from ..infrastructure.ipfs_distributor import IPFSDistributor
    from ..federated.node_communicator import NodeCommunicator
    from ..federated.ipfs_data_loader import IPFSDataLoader

logger = get_logger(__name__)


@dataclass
class MassiveDatasetInfo:
    """Information about a massive dataset."""
    dataset_id: str
    name: str
    source_config: DataSourceConfig
    local_path: Optional[str] = None
    ipfs_cid: Optional[str] = None
    size_bytes: int = 0
    chunks_created: int = 0
    federated_session_id: Optional[str] = None
    auto_listing_id: Optional[str] = None
    last_updated: float = 0
    status: str = "initialized"  # initialized, downloading, chunking, distributing, listed, failed
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PricingStrategy:
    """Pricing strategy for massive datasets."""
    strategy_type: str  # dynamic, fixed, auction, subscription
    base_price: float = 0.0
    price_per_mb: float = 0.0
    quality_multiplier: float = 1.0
    demand_multiplier: float = 1.0
    subscription_monthly: float = 0.0
    auction_start_price: float = 0.0
    auction_end_time: Optional[float] = None


class MassiveDataMarketplace(DataMarketplace):
    """
    Extended marketplace for massive datasets with automatic operations.
    """

    def __init__(self, config=None):
        super().__init__()

        self.config = config or get_config()
        self.massive_datasets: Dict[str, MassiveDatasetInfo] = {}
        self.active_sources: Dict[str, DataSourceConfig] = {}
        self.pricing_strategies: Dict[str, PricingStrategy] = {}

        # Federated components
        self.federated_coordinator: Optional['FederatedDataCoordinator'] = None
        self.ipfs_distributor: Optional['IPFSDistributor'] = None
        self.node_communicator: Optional['NodeCommunicator'] = None

        # Auto-listing components
        self.auto_listing_tasks: Dict[str, asyncio.Task] = {}
        self.source_monitor_tasks: Dict[str, asyncio.Task] = {}

        # Initialize from config
        self._initialize_from_config()

        logger.info("🏪 MassiveDataMarketplace initialized")

    def _initialize_from_config(self):
        """Initialize from configuration."""
        # Load data sources
        for source in self.config.data.sources:
            if source.enabled:
                self.active_sources[source.name] = source
                logger.info(f"📊 Loaded data source: {source.name} ({source.category})")

        # Initialize pricing strategies
        self._initialize_pricing_strategies()

    def _initialize_pricing_strategies(self):
        """Initialize default pricing strategies."""
        strategies = {
            "dynamic": PricingStrategy(
                strategy_type="dynamic",
                price_per_mb=0.1,
                quality_multiplier=1.5,
                demand_multiplier=1.2
            ),
            "fixed": PricingStrategy(
                strategy_type="fixed",
                base_price=100.0
            ),
            "subscription": PricingStrategy(
                strategy_type="subscription",
                subscription_monthly=50.0
            ),
            "auction": PricingStrategy(
                strategy_type="auction",
                auction_start_price=10.0
            )
        }

        for name, strategy in strategies.items():
            self.pricing_strategies[name] = strategy

    async def initialize_federated_components(self,
                                            federated_coordinator: Optional['FederatedDataCoordinator'] = None,
                                            ipfs_distributor: Optional['IPFSDistributor'] = None,
                                            node_communicator: Optional['NodeCommunicator'] = None):
        """Initialize federated learning components."""
        self.federated_coordinator = federated_coordinator
        self.ipfs_distributor = ipfs_distributor
        self.node_communicator = node_communicator

        if self.federated_coordinator:
            await self.federated_coordinator.initialize()

        logger.info("🔗 Federated components initialized for massive marketplace")

    async def start_auto_listing(self):
        """Start automatic listing creation from configured sources."""
        if not self.config.data.auto_listing_enabled:
            logger.info("🚫 Auto-listing disabled in configuration")
            return

        logger.info("🚀 Starting automatic listing creation")

        # Start monitoring each source
        for source_name, source_config in self.active_sources.items():
            if source_config.auto_listing:
                task = asyncio.create_task(self._monitor_data_source(source_name, source_config))
                self.source_monitor_tasks[source_name] = task
                logger.info(f"👀 Started monitoring source: {source_name}")

    async def stop_auto_listing(self):
        """Stop automatic listing creation."""
        logger.info("🛑 Stopping automatic listing creation")

        # Cancel all monitoring tasks
        for source_name, task in self.source_monitor_tasks.items():
            if not task.done():
                task.cancel()

        # Cancel all auto-listing tasks
        for dataset_id, task in self.auto_listing_tasks.items():
            if not task.done():
                task.cancel()

        self.source_monitor_tasks.clear()
        self.auto_listing_tasks.clear()

    async def _monitor_data_source(self, source_name: str, source_config: DataSourceConfig):
        """Monitor a data source for new datasets."""
        try:
            while True:
                try:
                    # Check for new datasets from source
                    new_datasets = await self._check_source_for_updates(source_config)

                    for dataset_info in new_datasets:
                        # Create massive dataset entry
                        dataset_id = self._generate_massive_dataset_id(source_name, dataset_info['name'])

                        if dataset_id not in self.massive_datasets:
                            # Initialize new massive dataset
                            massive_info = MassiveDatasetInfo(
                                dataset_id=dataset_id,
                                name=dataset_info['name'],
                                source_config=source_config,
                                metadata=dataset_info,
                                last_updated=time.time()
                            )

                            self.massive_datasets[dataset_id] = massive_info

                            # Start auto-listing process
                            task = asyncio.create_task(self._process_massive_dataset(dataset_id))
                            self.auto_listing_tasks[dataset_id] = task

                            logger.info(f"📦 New massive dataset detected: {dataset_id}")

                except Exception as e:
                    logger.error(f"❌ Error monitoring source {source_name}: {e}")

                # Wait before next check
                await asyncio.sleep(source_config.update_interval_hours * 3600)

        except asyncio.CancelledError:
            logger.info(f"🛑 Stopped monitoring source: {source_name}")

    async def _check_source_for_updates(self, source_config: DataSourceConfig) -> List[Dict[str, Any]]:
        """Check a data source for updates/new datasets."""
        # This would be implemented based on the specific source type
        # For now, simulate checking a data repository API

        try:
            # Simulate API call to data source
            # In real implementation, this would call actual APIs like:
            # - Kaggle API
            # - Hugging Face API
            # - Government data portals
            # - Research institution APIs

            response = requests.get(source_config.url, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Extract dataset information
            datasets = []
            if 'datasets' in data:
                for dataset in data['datasets']:
                    if self._meets_quality_threshold(dataset, source_config):
                        datasets.append(dataset)

            return datasets

        except Exception as e:
            logger.warning(f"⚠️ Failed to check source {source_config.name}: {e}")
            return []

    def _meets_quality_threshold(self, dataset_info: Dict[str, Any], source_config: DataSourceConfig) -> bool:
        """Check if dataset meets quality threshold."""
        quality_score = dataset_info.get('quality_score', 0.0)
        size_mb = dataset_info.get('size_mb', 0)

        return (quality_score >= source_config.quality_threshold and
                size_mb <= source_config.max_size_mb)

    async def _process_massive_dataset(self, dataset_id: str):
        """Process a massive dataset through the pipeline."""
        try:
            massive_info = self.massive_datasets[dataset_id]
            massive_info.status = "processing"

            logger.info(f"⚙️ Processing massive dataset: {dataset_id}")

            # Phase 1: Download dataset
            await self._download_massive_dataset(massive_info)

            # Phase 2: Chunk and distribute via IPFS
            await self._chunk_and_distribute_dataset(massive_info)

            # Phase 3: Create marketplace listing
            await self._create_massive_listing(massive_info)

            # Phase 4: Setup federated training (optional)
            if self.config.data.federated_integration:
                await self._setup_federated_training(massive_info)

            massive_info.status = "completed"
            logger.info(f"✅ Massive dataset processed successfully: {dataset_id}")

        except Exception as e:
            logger.error(f"❌ Failed to process massive dataset {dataset_id}: {e}")
            massive_info.status = "failed"
            massive_info.error_message = str(e)

    async def _download_massive_dataset(self, massive_info: MassiveDatasetInfo):
        """Download a massive dataset."""
        massive_info.status = "downloading"

        source_config = massive_info.source_config
        dataset_url = massive_info.metadata.get('download_url')

        if not dataset_url:
            raise ValueError(f"No download URL for dataset {massive_info.dataset_id}")

        logger.info(f"⬇️ Downloading massive dataset: {massive_info.name}")

        # Use federated coordinator for download if available
        if self.federated_coordinator:
            from ..federated.data_coordinator import FederatedDataCoordinator
            pipeline_id = await self.federated_coordinator.create_data_pipeline(
                dataset_name=massive_info.name,
                source_url=dataset_url,
                chunk_size=self.config.data.chunk_size_mb * 1024 * 1024
            )

            result = await self.federated_coordinator.execute_pipeline(pipeline_id)

            if result['success']:
                # Update massive info with pipeline results
                massive_info.local_path = result.get('dataset_path')
                massive_info.size_bytes = result.get('total_size_bytes', 0)
                massive_info.chunks_created = result.get('total_chunks', 0)
                massive_info.federated_session_id = result.get('federated_session_id')
            else:
                raise RuntimeError(f"Pipeline failed: {result.get('error')}")

        else:
            # Fallback: direct download
            await self._direct_download_dataset(massive_info, dataset_url)

        massive_info.last_updated = time.time()

    async def _direct_download_dataset(self, massive_info: MassiveDatasetInfo, url: str):
        """Direct download for massive datasets."""
        response = requests.get(url, stream=True, timeout=self.config.data.download_timeout_seconds)
        response.raise_for_status()

        # Create local path
        local_path = f"./massive_datasets/{massive_info.dataset_id}"
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)

        total_size = 0
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)

        massive_info.local_path = local_path
        massive_info.size_bytes = total_size

    async def _chunk_and_distribute_dataset(self, massive_info: MassiveDatasetInfo):
        """Chunk and distribute dataset via IPFS."""
        if not massive_info.local_path:
            raise RuntimeError("Dataset local path missing for IPFS distribution")

        file_path = Path(massive_info.local_path)
        if not file_path.exists():
            massive_info.status = "failed"
            massive_info.error_message = "Dataset file not found"
            return

        massive_info.status = "distributing"
        logger.info(f"📤 Chunking and distributing: {massive_info.dataset_id}")

        api_endpoint = f"http://{self.config.ipfs.api_host}:{self.config.ipfs.api_port}/api/v0"
        ipfs_manager = await create_ipfs_manager(api_endpoint)
        chunk_size = self.config.data.chunk_size_mb * 1024 * 1024
        total_size = file_path.stat().st_size
        total_chunks = max(1, math.ceil(total_size / chunk_size))

        massive_info.size_bytes = total_size
        massive_info.chunks_created = total_chunks
        massive_info.metadata.update({
            "ipfs_total_chunks": total_chunks,
            "ipfs_distributed_chunks": 0,
            "ipfs_started_at": time.time(),
            "ipfs_chunk_size": chunk_size
        })

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
                            "dataset_id": massive_info.dataset_id,
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

                    massive_info.metadata["ipfs_distributed_chunks"] = index
                    massive_info.metadata["ipfs_last_update"] = time.time()

            massive_info.metadata["ipfs_chunks"] = manifest_chunks

            manifest = {
                "version": "1.0",
                "dataset_id": massive_info.dataset_id,
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
                    "dataset_id": massive_info.dataset_id,
                    "total_chunks": total_chunks
                }
            )

            massive_info.ipfs_cid = manifest_cid
            massive_info.status = "completed"
            massive_info.metadata["ipfs_manifest_cid"] = manifest_cid
            massive_info.metadata["ipfs_completed_at"] = time.time()
            massive_info.last_updated = time.time()
            logger.info(f"✅ IPFS distribution completed: {manifest_cid}")
        except Exception as e:
            massive_info.status = "failed"
            massive_info.error_message = str(e)
            logger.error(f"❌ IPFS distribution failed: {e}")
            raise
        finally:
            await ipfs_manager.stop()

    async def _create_massive_listing(self, massive_info: MassiveDatasetInfo):
        """Create marketplace listing for massive dataset."""
        massive_info.status = "listing"

        # Determine pricing strategy
        pricing_strategy = self._get_pricing_strategy(massive_info)

        # Calculate price
        price = await self._calculate_dataset_price(massive_info, pricing_strategy)

        # Create listing
        listing_id = self.create_listing(
            seller_address="massive_data_marketplace",  # System address
            title=f"[MASSIVE] {massive_info.name}",
            description=massive_info.metadata.get('description', ''),
            category=self._map_category(massive_info.source_config.category),
            data_hash=self._calculate_dataset_hash(massive_info),
            ipfs_cid=massive_info.ipfs_cid or "",
            price_dracma=price,
            data_size_mb=massive_info.size_bytes / (1024 * 1024),
            sample_count=massive_info.metadata.get('sample_count', 0),
            quality_score=massive_info.metadata.get('quality_score', 0.8),
            tags=massive_info.metadata.get('tags', []),
            duration_days=90  # Longer duration for massive datasets
        )

        massive_info.auto_listing_id = listing_id
        logger.info(f"📋 Created massive dataset listing: {listing_id}")

    def _get_pricing_strategy(self, massive_info: MassiveDatasetInfo) -> PricingStrategy:
        """Get pricing strategy for dataset."""
        strategy_name = self.config.data.pricing_strategy
        return self.pricing_strategies.get(strategy_name, self.pricing_strategies["dynamic"])

    async def _calculate_dataset_price(self, massive_info: MassiveDatasetInfo,
                                     pricing_strategy: PricingStrategy) -> float:
        """Calculate price for massive dataset."""
        if pricing_strategy.strategy_type == "dynamic":
            # Use price oracle for dynamic pricing
            category = self._map_category(massive_info.source_config.category)
            quality = massive_info.metadata.get('quality_score', 0.5)
            size_mb = massive_info.size_bytes / (1024 * 1024)

            price_estimate = await price_oracle.get_price_estimate(
                category=category,
                data_quality=quality,
                data_size_mb=size_mb
            )

            if 'estimated_price' in price_estimate:
                return price_estimate['estimated_price']

        elif pricing_strategy.strategy_type == "fixed":
            return pricing_strategy.base_price

        # Default fallback
        return max(10.0, massive_info.size_bytes / (1024 * 1024) * 0.1)  # $0.10 per MB

    async def _setup_federated_training(self, massive_info: MassiveDatasetInfo):
        """Setup federated training for the dataset."""
        if not self.federated_coordinator or not massive_info.federated_session_id:
            return

        from ..federated.data_coordinator import FederatedDataCoordinator
        logger.info(f"🎯 Setting up federated training for: {massive_info.dataset_id}")

        # The federated session should already be created by the coordinator
        # Here we could add additional setup like inviting specific nodes

    def _map_category(self, source_category: str) -> DataCategory:
        """Map source category to DataCategory enum."""
        category_mapping = {
            "image_data": DataCategory.IMAGE_DATA,
            "text_data": DataCategory.TEXT_DATA,
            "audio_data": DataCategory.AUDIO_DATA,
            "tabular_data": DataCategory.TABULAR_DATA,
            "time_series": DataCategory.TIME_SERIES,
            "medical_data": DataCategory.MEDICAL_DATA,
            "financial_data": DataCategory.FINANCIAL_DATA,
            "iot_data": DataCategory.IoT_DATA
        }

        return category_mapping.get(source_category, DataCategory.TABULAR_DATA)

    def _calculate_dataset_hash(self, massive_info: MassiveDatasetInfo) -> str:
        """Calculate hash for massive dataset."""
        if massive_info.local_path and Path(massive_info.local_path).exists():
            # Calculate actual file hash
            hash_sha256 = hashlib.sha256()
            with open(massive_info.local_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        else:
            # Fallback to metadata-based hash
            metadata_str = json.dumps(massive_info.metadata, sort_keys=True)
            return hashlib.sha256(metadata_str.encode()).hexdigest()

    def _generate_massive_dataset_id(self, source_name: str, dataset_name: str) -> str:
        """Generate unique ID for massive dataset."""
        data = f"{source_name}_{dataset_name}_{int(time.time())}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    # Public API methods

    def get_massive_datasets(self) -> List[Dict[str, Any]]:
        """Get all massive datasets."""
        return [
            {
                "dataset_id": info.dataset_id,
                "name": info.name,
                "source": info.source_config.name,
                "category": info.source_config.category,
                "size_bytes": info.size_bytes,
                "status": info.status,
                "chunks_created": info.chunks_created,
                "auto_listing_id": info.auto_listing_id,
                "last_updated": info.last_updated,
                "federated_session_id": info.federated_session_id
            }
            for info in self.massive_datasets.values()
        ]

    def get_massive_dataset_details(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Get details of a massive dataset."""
        info = self.massive_datasets.get(dataset_id)
        if not info:
            return None

        return {
            "dataset_id": info.dataset_id,
            "name": info.name,
            "source_config": {
                "name": info.source_config.name,
                "category": info.source_config.category,
                "url": info.source_config.url,
                "enabled": info.source_config.enabled
            },
            "local_path": info.local_path,
            "ipfs_cid": info.ipfs_cid,
            "size_bytes": info.size_bytes,
            "chunks_created": info.chunks_created,
            "federated_session_id": info.federated_session_id,
            "auto_listing_id": info.auto_listing_id,
            "status": info.status,
            "error_message": info.error_message,
            "last_updated": info.last_updated,
            "metadata": info.metadata
        }

    async def trigger_manual_listing(self, source_name: str, dataset_info: Dict[str, Any]) -> str:
        """Manually trigger listing creation for a dataset."""
        if source_name not in self.active_sources:
            raise ValueError(f"Source {source_name} not configured")

        source_config = self.active_sources[source_name]
        dataset_id = self._generate_massive_dataset_id(source_name, dataset_info['name'])

        # Create massive dataset entry
        massive_info = MassiveDatasetInfo(
            dataset_id=dataset_id,
            name=dataset_info['name'],
            source_config=source_config,
            metadata=dataset_info,
            last_updated=time.time()
        )

        self.massive_datasets[dataset_id] = massive_info

        # Start processing
        task = asyncio.create_task(self._process_massive_dataset(dataset_id))
        self.auto_listing_tasks[dataset_id] = task

        return dataset_id

    def get_marketplace_stats_extended(self) -> Dict[str, Any]:
        """Get extended marketplace statistics including massive datasets."""
        base_stats = self.get_market_stats()

        massive_stats = {
            "total_massive_datasets": len(self.massive_datasets),
            "active_massive_datasets": len([d for d in self.massive_datasets.values() if d.status == "completed"]),
            "processing_massive_datasets": len([d for d in self.massive_datasets.values() if d.status == "processing"]),
            "failed_massive_datasets": len([d for d in self.massive_datasets.values() if d.status == "failed"]),
            "total_massive_data_size_tb": sum(d.size_bytes for d in self.massive_datasets.values()) / (1024**4),
            "auto_listings_created": len([d for d in self.massive_datasets.values() if d.auto_listing_id]),
            "federated_sessions_active": len([d for d in self.massive_datasets.values() if d.federated_session_id])
        }

        base_stats["massive_datasets"] = massive_stats
        return base_stats


# Global instance
massive_data_marketplace = MassiveDataMarketplace()
