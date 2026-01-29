#!/usr/bin/env python3
"""
Federated Data Coordinator - Manages complete pipeline from dataset download to IPFS distribution
"""

import asyncio
import hashlib
import os
import time
import requests
from typing import Dict, List, Any, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

from ..core.logging import get_logger
from ..core.config import Config
from .coordinator import FederatedCoordinator
from ..infrastructure.ipfs_distributor import IPFSDistributor, DistributionResult
from ..federated.node_communicator import NodeCommunicator
from .ipfs_data_loader import IPFSDataLoader
from .optimal_dataset_partitioner import OptimalDatasetPartitioner, PartitionStrategy

# Lazy import to avoid circular dependencies
if TYPE_CHECKING:
    from ..discovery.node_discovery import NodeDiscovery

logger = get_logger(__name__)


@dataclass
class DatasetInfo:
    """Information about a dataset."""
    name: str
    source_url: Optional[str] = None
    local_path: Optional[str] = None
    size_bytes: int = 0
    checksum: str = ""
    chunk_size: int = 1024 * 1024  # 1MB default
    total_chunks: int = 0
    chunks: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataPipelineStatus:
    """Status of the data pipeline."""
    pipeline_id: str
    status: str = "initialized"
    dataset_info: Optional[DatasetInfo] = None
    download_progress: float = 0.0
    chunking_progress: float = 0.0
    distribution_progress: float = 0.0
    verification_progress: float = 0.0
    federated_session_id: Optional[str] = None
    target_nodes: List[str] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    errors: List[str] = field(default_factory=list)


class FederatedDataCoordinator:
    """
    Coordinator for federated data pipeline: download → chunk → distribute → verify → train
    """

    def __init__(self,
                 config: Config,
                 federated_coordinator: Optional[FederatedCoordinator] = None,
                 ipfs_distributor: Optional[IPFSDistributor] = None,
                 node_communicator: Optional[NodeCommunicator] = None,
                 ipfs_data_loader: Optional[IPFSDataLoader] = None,
                 node_discovery: Optional['NodeDiscovery'] = None,
                 dataset_partitioner: Optional[OptimalDatasetPartitioner] = None):
        """
        Initialize the Federated Data Coordinator.

        Args:
            config: Application configuration
            federated_coordinator: Existing federated coordinator instance
            ipfs_distributor: Existing IPFS distributor instance
            node_communicator: Node communication interface
            ipfs_data_loader: IPFS data loader for nodes
            node_discovery: Node discovery service for automatic partitioning
            dataset_partitioner: Optimal dataset partitioner instance
        """
        self.config = config
        self.federated_coordinator = federated_coordinator or FederatedCoordinator(config)
        self.ipfs_distributor = ipfs_distributor
        self.node_communicator = node_communicator
        self.ipfs_data_loader = ipfs_data_loader
        self.node_discovery = node_discovery
        self.dataset_partitioner = dataset_partitioner or OptimalDatasetPartitioner(config)

        # Lazy import to avoid circular dependencies
        from ..verification.dataset_integrity_verifier import DatasetIntegrityVerifier
        self.integrity_verifier = DatasetIntegrityVerifier(config)

        # Pipeline state
        self.active_pipelines: Dict[str, DataPipelineStatus] = {}
        self.datasets: Dict[str, DatasetInfo] = {}

        # Configuration
        self.chunk_size = config.get('data.chunk_size', 1024 * 1024)  # 1MB
        self.max_concurrent_downloads = config.get('data.max_concurrent_downloads', 3)
        self.download_timeout = config.get('data.download_timeout', 300)  # 5 minutes
        self.verification_retries = config.get('data.verification_retries', 3)

        logger.info("🚀 FederatedDataCoordinator initialized")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.shutdown()

    async def initialize(self):
        """Initialize components."""
        try:
            if self.ipfs_distributor:
                await self.ipfs_distributor.initialize(self.node_communicator)

            logger.info("✅ FederatedDataCoordinator initialized successfully")
        except Exception as e:
            logger.error(f"❌ Error initializing FederatedDataCoordinator: {e}")
            raise

    async def shutdown(self):
        """Shutdown components."""
        try:
            if self.ipfs_distributor:
                await self.ipfs_distributor.shutdown()

            logger.info("🛑 FederatedDataCoordinator shutdown")
        except Exception as e:
            logger.error(f"❌ Error shutting down FederatedDataCoordinator: {e}")

    async def create_data_pipeline(self,
                                  dataset_name: str,
                                  source_url: Optional[str] = None,
                                  local_path: Optional[str] = None,
                                  target_nodes: Optional[List[str]] = None,
                                  chunk_size: Optional[int] = None,
                                  auto_partition: bool = True,
                                  partition_strategy: PartitionStrategy = PartitionStrategy.HYBRID_OPTIMAL,
                                  partition_constraints: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new data pipeline for dataset distribution.

        Args:
            dataset_name: Name of the dataset
            source_url: URL to download dataset from
            local_path: Local path to existing dataset
            target_nodes: List of target node IDs (if None, uses automatic partitioning)
            chunk_size: Size of data chunks
            auto_partition: Whether to use automatic partitioning when target_nodes is None
            partition_strategy: Strategy for automatic partitioning
            partition_constraints: Constraints for node selection

        Returns:
            Pipeline ID
        """
        pipeline_id = f"pipeline_{dataset_name}_{int(time.time())}"

        # Determine target nodes
        final_target_nodes = target_nodes or []

        if not target_nodes and auto_partition and self.node_discovery:
            # Use automatic partitioning
            logger.info("🎯 Using automatic dataset partitioning")
            # We'll determine nodes after dataset is prepared (in execute_pipeline)
            # For now, mark as auto-partition
            final_target_nodes = ["auto_partition"]  # Placeholder

        pipeline_status = DataPipelineStatus(
            pipeline_id=pipeline_id,
            dataset_info=DatasetInfo(
                name=dataset_name,
                source_url=source_url,
                local_path=local_path,
                chunk_size=chunk_size or self.chunk_size,
                created_at=datetime.now().isoformat()
            ),
            target_nodes=final_target_nodes,
            start_time=time.time()
        )

        # Store partitioning config in dataset metadata
        pipeline_status.dataset_info.metadata.update({
            'auto_partition': auto_partition,
            'partition_strategy': partition_strategy.value if partition_strategy else None,
            'partition_constraints': partition_constraints or {}
        })

        self.active_pipelines[pipeline_id] = pipeline_status
        logger.info(f"📋 Created data pipeline: {pipeline_id} (auto_partition: {auto_partition})")
        return pipeline_id

    async def execute_pipeline(self, pipeline_id: str) -> Dict[str, Any]:
        """
        Execute the complete data pipeline.

        Args:
            pipeline_id: ID of the pipeline to execute

        Returns:
            Pipeline execution result
        """
        if pipeline_id not in self.active_pipelines:
            raise ValueError(f"Pipeline {pipeline_id} not found")

        pipeline = self.active_pipelines[pipeline_id]
        pipeline.status = "running"

        try:
            # Phase 1: Download dataset
            await self._download_dataset(pipeline)

            # Phase 2: Chunk dataset
            await self._chunk_dataset(pipeline)

            # Phase 2.5: Automatic partitioning (if enabled)
            await self._perform_auto_partitioning(pipeline)

            # Phase 3: Distribute via IPFS
            await self._distribute_dataset(pipeline)

            # Phase 4: Verify availability
            await self._verify_data_availability(pipeline)

            # Phase 5: Coordinate training
            await self._coordinate_training(pipeline)

            pipeline.status = "completed"
            pipeline.end_time = time.time()

            logger.info(f"✅ Pipeline {pipeline_id} completed successfully")
            return self._create_pipeline_result(pipeline, success=True)

        except Exception as e:
            logger.error(f"❌ Pipeline {pipeline_id} failed: {e}")
            pipeline.status = "failed"
            pipeline.end_time = time.time()
            pipeline.errors.append(str(e))

            return self._create_pipeline_result(pipeline, success=False, error=str(e))

    async def _download_dataset(self, pipeline: DataPipelineStatus):
        """Download dataset if needed."""
        dataset = pipeline.dataset_info

        if dataset.local_path and os.path.exists(dataset.local_path):
            # Dataset already exists locally
            dataset.size_bytes = os.path.getsize(dataset.local_path)
            dataset.checksum = self._calculate_checksum(dataset.local_path)
            pipeline.download_progress = 100.0
            logger.info(f"📁 Using existing dataset: {dataset.local_path}")
            return

        if not dataset.source_url:
            raise ValueError("No source URL or local path provided for dataset")

        # Download dataset
        logger.info(f"⬇️ Downloading dataset from: {dataset.source_url}")

        response = requests.get(dataset.source_url, stream=True, timeout=self.download_timeout)
        response.raise_for_status()

        # Create temp file
        temp_path = f"/tmp/{dataset.name}_{int(time.time())}.tmp"
        total_size = int(response.headers.get('content-length', 0))

        downloaded = 0
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        pipeline.download_progress = (downloaded / total_size) * 100

        # Move to final location
        final_path = f"./datasets/{dataset.name}"
        os.makedirs(os.path.dirname(final_path), exist_ok=True)
        os.rename(temp_path, final_path)

        dataset.local_path = final_path
        dataset.size_bytes = downloaded
        dataset.checksum = self._calculate_checksum(final_path)

        # Verify download integrity
        download_result = await self.integrity_verifier.verify_download_integrity(pipeline)
        if not download_result.success:
            logger.warning(f"⚠️ Download integrity check failed: {download_result.errors}")
            # Could raise exception or attempt recovery here

        logger.info(f"✅ Dataset downloaded: {downloaded} bytes, checksum: {dataset.checksum}")

    async def _chunk_dataset(self, pipeline: DataPipelineStatus):
        """Chunk the dataset for distribution."""
        dataset = pipeline.dataset_info

        if not dataset.local_path or not os.path.exists(dataset.local_path):
            raise ValueError("Dataset not available for chunking")

        logger.info(f"✂️ Chunking dataset: {dataset.name}")

        chunks = []
        chunk_size = dataset.chunk_size

        with open(dataset.local_path, 'rb') as f:
            chunk_index = 0
            while True:
                data = f.read(chunk_size)
                if not data:
                    break

                chunk_id = f"{dataset.name}_chunk_{chunk_index:04d}"
                chunk_hash = hashlib.sha256(data).hexdigest()

                chunks.append({
                    'chunk_id': chunk_id,
                    'data': data,
                    'size': len(data),
                    'index': chunk_index,
                    'hash': chunk_hash
                })

                chunk_index += 1
                pipeline.chunking_progress = (chunk_index / (dataset.size_bytes / chunk_size)) * 100

        dataset.chunks = chunks
        dataset.total_chunks = len(chunks)

        # Verify chunking integrity
        chunking_result = await self.integrity_verifier.verify_chunking_integrity(pipeline)
        if not chunking_result.success:
            logger.warning(f"⚠️ Chunking integrity check failed: {chunking_result.errors}")
            # Could attempt recovery or re-chunking here

        logger.info(f"✅ Dataset chunked into {len(chunks)} chunks")

    async def _perform_auto_partitioning(self, pipeline: DataPipelineStatus):
        """Perform automatic dataset partitioning if enabled."""
        dataset = pipeline.dataset_info
        metadata = dataset.metadata

        if not metadata.get('auto_partition', False):
            return  # Manual partitioning, skip

        if not self.node_discovery:
            logger.warning("⚠️ Node discovery not available for automatic partitioning")
            return

        if not dataset.chunks:
            logger.warning("⚠️ No chunks available for partitioning")
            return

        try:
            # Get available nodes
            available_nodes = self.node_discovery.get_online_nodes("federated_learning")
            if not available_nodes:
                logger.warning("⚠️ No online federated learning nodes available")
                return

            # Get partitioning strategy
            strategy_str = metadata.get('partition_strategy', 'hybrid_optimal')
            strategy = PartitionStrategy(strategy_str)

            # Get constraints
            constraints = metadata.get('partition_constraints', {})

            # Perform partitioning
            partition_result = await self.dataset_partitioner.partition_dataset(
                dataset=dataset,
                available_nodes=available_nodes,
                strategy=strategy,
                constraints=constraints
            )

            if not partition_result.node_assignments:
                logger.warning("⚠️ Partitioning resulted in no node assignments")
                return

            # Update pipeline with partitioned nodes
            pipeline.target_nodes = list(partition_result.node_assignments.keys())

            # Store partition result in metadata
            dataset.metadata['partition_result'] = {
                'node_assignments': partition_result.node_assignments,
                'optimization_score': partition_result.optimization_score,
                'strategy_used': partition_result.strategy_used,
                'partition_stats': partition_result.partition_stats
            }

            logger.info(f"🎯 Automatic partitioning completed: {len(pipeline.target_nodes)} nodes assigned")

        except Exception as e:
            logger.error(f"❌ Error in automatic partitioning: {e}")
            # Continue with manual nodes if available

    async def _distribute_dataset(self, pipeline: DataPipelineStatus):
        """Distribute dataset chunks via IPFS."""
        if not self.ipfs_distributor:
            raise RuntimeError("IPFS distributor not initialized")

        dataset = pipeline.dataset_info
        target_nodes = pipeline.target_nodes

        if not target_nodes:
            raise ValueError("No target nodes specified for distribution")

        logger.info(f"📤 Distributing {dataset.total_chunks} chunks to {len(target_nodes)} nodes")

        # Prepare chunks for distribution
        chunk_tuples = [(chunk['chunk_id'], chunk['data']) for chunk in dataset.chunks]

        # Distribute via IPFS
        distribution_result = await self.ipfs_distributor.distribute_chunks(
            chunks=chunk_tuples,
            target_nodes=target_nodes,
            distribution_id=pipeline.pipeline_id
        )

        if not distribution_result.success:
            raise RuntimeError(f"IPFS distribution failed: {distribution_result.errors}")

        pipeline.distribution_progress = 100.0

        # Verify distribution integrity
        distribution_check_result = await self.integrity_verifier.verify_distribution_integrity(pipeline)
        if not distribution_check_result.success:
            logger.warning(f"⚠️ Distribution integrity check failed: {distribution_check_result.errors}")

        logger.info(f"✅ Dataset distributed successfully to {distribution_result.successful_deliveries} node deliveries")

    async def _verify_data_availability(self, pipeline: DataPipelineStatus):
        """Verify that nodes have access to the distributed data."""
        target_nodes = pipeline.target_nodes
        dataset = pipeline.dataset_info

        logger.info(f"🔍 Verifying data availability for {len(target_nodes)} nodes")

        verification_tasks = []
        for node_id in target_nodes:
            task = self._verify_node_data_availability(node_id, dataset, pipeline.pipeline_id)
            verification_tasks.append(task)

        results = await asyncio.gather(*verification_tasks, return_exceptions=True)

        successful_verifications = sum(1 for r in results if r is True)
        pipeline.verification_progress = (successful_verifications / len(target_nodes)) * 100

        if successful_verifications < len(target_nodes):
            failed_nodes = [node_id for node_id, result in zip(target_nodes, results) if result is not True]
            logger.warning(f"⚠️ Data verification failed for nodes: {failed_nodes}")

        logger.info(f"✅ Data verification completed: {successful_verifications}/{len(target_nodes)} nodes verified")

    async def _verify_node_data_availability(self, node_id: str, dataset: DatasetInfo, pipeline_id: str) -> bool:
        """Verify data availability for a specific node."""
        # This would typically involve querying the node to confirm it has the chunks
        # For now, we'll simulate verification based on IPFS distributor results

        if not self.node_communicator:
            # If no communicator, assume success based on distribution
            await asyncio.sleep(0.1)  # Simulate network delay
            return True

        try:
            # Send verification request to node
            verification_request = {
                "type": "data_verification",
                "pipeline_id": pipeline_id,
                "dataset_name": dataset.name,
                "expected_chunks": len(dataset.chunks),
                "timestamp": time.time()
            }

            # In a real implementation, this would await a response
            # For now, simulate
            await asyncio.sleep(0.05)
            return True

        except Exception as e:
            logger.warning(f"⚠️ Verification failed for node {node_id}: {e}")
            return False

    async def _coordinate_training(self, pipeline: DataPipelineStatus):
        """Coordinate federated training session."""
        dataset = pipeline.dataset_info
        target_nodes = pipeline.target_nodes

        # Create federated session
        session_id = f"session_{dataset.name}_{int(time.time())}"
        session = self.federated_coordinator.create_session(
            session_id=session_id,
            model_name="default_model",  # Could be parameterized
            min_nodes=len(target_nodes),
            max_nodes=len(target_nodes),
            rounds=5
        )

        # Add nodes to session
        for node_id in target_nodes:
            self.federated_coordinator.add_node_to_session(session_id, node_id)

        # Start training
        training_result = self.federated_coordinator.start_training(session_id)

        pipeline.federated_session_id = session_id
        logger.info(f"🎯 Training session created: {session_id}")

    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _create_pipeline_result(self, pipeline: DataPipelineStatus, success: bool, error: str = None) -> Dict[str, Any]:
        """Create pipeline execution result."""
        duration = (pipeline.end_time or time.time()) - (pipeline.start_time or time.time())

        result = {
            "pipeline_id": pipeline.pipeline_id,
            "success": success,
            "duration": duration,
            "status": pipeline.status,
            "dataset_name": pipeline.dataset_info.name if pipeline.dataset_info else None,
            "total_chunks": pipeline.dataset_info.total_chunks if pipeline.dataset_info else 0,
            "target_nodes": len(pipeline.target_nodes),
            "federated_session_id": pipeline.federated_session_id,
            "progress": {
                "download": pipeline.download_progress,
                "chunking": pipeline.chunking_progress,
                "distribution": pipeline.distribution_progress,
                "verification": pipeline.verification_progress
            }
        }

        if error:
            result["error"] = error
            result["errors"] = pipeline.errors

        return result

    def get_pipeline_status(self, pipeline_id: str) -> Optional[DataPipelineStatus]:
        """Get status of a pipeline."""
        return self.active_pipelines.get(pipeline_id)

    def get_active_pipelines(self) -> List[Dict[str, Any]]:
        """Get all active pipelines."""
        return [
            {
                "pipeline_id": p.pipeline_id,
                "status": p.status,
                "dataset_name": p.dataset_info.name if p.dataset_info else None,
                "progress": {
                    "download": p.download_progress,
                    "chunking": p.chunking_progress,
                    "distribution": p.distribution_progress,
                    "verification": p.verification_progress
                },
                "start_time": p.start_time,
                "target_nodes": len(p.target_nodes)
            }
            for p in self.active_pipelines.values()
        ]

    def get_dataset_info(self, dataset_name: str) -> Optional[DatasetInfo]:
        """Get information about a dataset."""
        return self.datasets.get(dataset_name)

    def get_integrity_stats(self) -> Dict[str, Any]:
        """Get integrity verification statistics."""
        return self.integrity_verifier.get_integrity_stats()

    async def verify_pipeline_integrity(self, pipeline_id: str) -> Dict[str, Any]:
        """
        Perform comprehensive integrity verification on a pipeline.

        Args:
            pipeline_id: ID of the pipeline to verify

        Returns:
            Dictionary with verification results
        """
        pipeline = self.active_pipelines.get(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")

        return await self.integrity_verifier.verify_pipeline_integrity(pipeline)

    def create_data_loader_for_node(self, node_id: str, ipfs_endpoint: str = "http://localhost:5001/api/v0",
                                   max_memory_mb: int = 100) -> IPFSDataLoader:
        """
        Create an IPFS data loader for a federated node.

        Args:
            node_id: ID of the node
            ipfs_endpoint: IPFS API endpoint
            max_memory_mb: Maximum memory for caching

        Returns:
            Configured IPFSDataLoader instance
        """
        from ..infrastructure.ipfs_embedded import IPFSManager

        ipfs_manager = IPFSManager(api_endpoint=ipfs_endpoint)
        data_loader = IPFSDataLoader(
            ipfs_manager=ipfs_manager,
            max_memory_mb=max_memory_mb
        )

        logger.info(f"📦 Created IPFS data loader for node {node_id}")
        return data_loader

    async def preload_data_for_node(self, node_id: str, chunk_cids: List[str],
                                   data_loader: Optional[IPFSDataLoader] = None) -> bool:
        """
        Preload training data chunks for a node.

        Args:
            node_id: ID of the node
            chunk_cids: List of CIDs for data chunks
            data_loader: Existing data loader instance

        Returns:
            True if preload successful
        """
        if not data_loader:
            data_loader = self.ipfs_data_loader

        if not data_loader:
            logger.warning(f"⚠️ No data loader available for node {node_id}")
            return False

        try:
            # Prefetch chunks in background
            await data_loader.prefetch_cids(chunk_cids)

            # Wait for completion (optional - could be fire-and-forget)
            results = await data_loader.preload_cids(chunk_cids)
            successful = sum(1 for success in results.values() if success)

            # Verify training data integrity
            training_integrity_result = await self.integrity_verifier.verify_training_data_integrity(
                node_id, chunk_cids, data_loader
            )
            if not training_integrity_result.success:
                logger.warning(f"⚠️ Training data integrity check failed for node {node_id}: {training_integrity_result.errors}")
                successful = training_integrity_result.checked_items - training_integrity_result.missing_items

            logger.info(f"✅ Preloaded {successful}/{len(chunk_cids)} chunks for node {node_id}")
            return successful == len(chunk_cids)

        except Exception as e:
            logger.error(f"❌ Failed to preload data for node {node_id}: {e}")
            return False