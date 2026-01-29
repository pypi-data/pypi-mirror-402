#!/usr/bin/env python3
"""
Dataset Integrity Verifier
Validates data integrity throughout the federated pipeline with cryptographic hashing,
chunk verification, and error detection/recovery mechanisms.
"""

import asyncio
import hashlib
import os
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import requests

from ..core.logging import get_logger
from ..core.config import Config

# Lazy imports to avoid circular dependencies
DatasetInfo = None
DataPipelineStatus = None

def _get_federated_types():
    """Lazy import of federated types to avoid circular dependencies."""
    global DatasetInfo, DataPipelineStatus
    if DatasetInfo is None or DataPipelineStatus is None:
        from ..federated.data_coordinator import DatasetInfo as DI, DataPipelineStatus as DPS
        DatasetInfo = DI
        DataPipelineStatus = DPS
    return DatasetInfo, DataPipelineStatus

logger = get_logger(__name__)


@dataclass
class IntegrityCheckResult:
    """Result of an integrity check operation."""
    success: bool
    checked_items: int = 0
    corrupted_items: int = 0
    missing_items: int = 0
    recovered_items: int = 0
    errors: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class CorruptionReport:
    """Report of detected corruption."""
    item_id: str
    item_type: str  # 'file', 'chunk', 'cid'
    expected_hash: str
    actual_hash: Optional[str] = None
    error_type: str = "corruption"  # 'corruption', 'missing', 'inaccessible'
    recoverable: bool = True
    recovery_attempts: int = 0
    last_attempt: Optional[float] = None


class DatasetIntegrityVerifier:
    """
    Verifies dataset integrity throughout the federated learning pipeline.
    Provides cryptographic hashing, chunk verification, and error recovery.
    """

    def __init__(self, config: Config):
        """
        Initialize the Dataset Integrity Verifier.

        Args:
            config: Application configuration
        """
        self.config = config

        # Hashing configuration
        self.hash_algorithm = config.get('integrity.hash_algorithm', 'sha256')
        self.chunk_size = config.get('integrity.chunk_size', 1024 * 1024)  # 1MB

        # Recovery configuration
        self.max_recovery_attempts = config.get('integrity.max_recovery_attempts', 3)
        self.recovery_timeout = config.get('integrity.recovery_timeout', 300)  # 5 minutes
        self.enable_auto_recovery = config.get('integrity.enable_auto_recovery', True)

        # Statistics
        self.stats = {
            'total_checks': 0,
            'successful_checks': 0,
            'corruption_detected': 0,
            'recovery_attempts': 0,
            'successful_recoveries': 0,
            'failed_recoveries': 0
        }

        logger.info("🔐 DatasetIntegrityVerifier initialized")

    # Cryptographic Hashing Methods

    def calculate_file_hash(self, file_path: str, algorithm: str = None) -> str:
        """
        Calculate cryptographic hash of a file.

        Args:
            file_path: Path to the file
            algorithm: Hash algorithm ('sha256', 'md5', etc.)

        Returns:
            Hexadecimal hash string
        """
        if algorithm is None:
            algorithm = self.hash_algorithm

        hash_func = self._get_hash_function(algorithm)

        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)

        return hash_func.hexdigest()

    def calculate_chunk_hash(self, chunk_data: bytes, algorithm: str = None) -> str:
        """
        Calculate cryptographic hash of chunk data.

        Args:
            chunk_data: Raw chunk bytes
            algorithm: Hash algorithm

        Returns:
            Hexadecimal hash string
        """
        if algorithm is None:
            algorithm = self.hash_algorithm

        hash_func = self._get_hash_function(algorithm)
        hash_func.update(chunk_data)
        return hash_func.hexdigest()

    def _get_hash_function(self, algorithm: str):
        """Get hash function object for specified algorithm."""
        if algorithm == 'sha256':
            return hashlib.sha256()
        elif algorithm == 'md5':
            return hashlib.md5()
        elif algorithm == 'sha1':
            return hashlib.sha1()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    # Integrity Verification Methods

    def verify_file_integrity(self, file_path: str, expected_hash: str,
                            algorithm: str = None) -> Tuple[bool, str]:
        """
        Verify file integrity against expected hash.

        Args:
            file_path: Path to file
            expected_hash: Expected hash value
            algorithm: Hash algorithm

        Returns:
            Tuple of (is_valid, actual_hash)
        """
        if not os.path.exists(file_path):
            return False, ""

        actual_hash = self.calculate_file_hash(file_path, algorithm)
        is_valid = actual_hash == expected_hash

        self.stats['total_checks'] += 1
        if is_valid:
            self.stats['successful_checks'] += 1
        else:
            self.stats['corruption_detected'] += 1

        return is_valid, actual_hash

    def verify_chunk_integrity(self, chunk_data: bytes, expected_hash: str,
                              algorithm: str = None) -> Tuple[bool, str]:
        """
        Verify chunk integrity against expected hash.

        Args:
            chunk_data: Chunk bytes
            expected_hash: Expected hash
            algorithm: Hash algorithm

        Returns:
            Tuple of (is_valid, actual_hash)
        """
        actual_hash = self.calculate_chunk_hash(chunk_data, algorithm)
        is_valid = actual_hash == expected_hash

        self.stats['total_checks'] += 1
        if is_valid:
            self.stats['successful_checks'] += 1
        else:
            self.stats['corruption_detected'] += 1

        return is_valid, actual_hash

    async def verify_dataset_chunks(self, dataset_info: Any) -> IntegrityCheckResult:
        """
        Verify integrity of all chunks in a dataset.

        Args:
            dataset_info: Dataset information with chunks

        Returns:
            Integrity check result
        """
        result = IntegrityCheckResult(success=True)

        if not dataset_info.chunks:
            result.errors.append("No chunks found in dataset")
            result.success = False
            return result

        for chunk in dataset_info.chunks:
            chunk_id = chunk['chunk_id']
            expected_hash = chunk['hash']
            chunk_data = chunk['data']

            is_valid, actual_hash = self.verify_chunk_integrity(chunk_data, expected_hash)

            if not is_valid:
                result.corrupted_items += 1
                result.success = False
                result.errors.append(f"Chunk {chunk_id} corrupted: expected {expected_hash}, got {actual_hash}")
                result.details[chunk_id] = {
                    'expected': expected_hash,
                    'actual': actual_hash,
                    'corrupted': True
                }
            else:
                result.details[chunk_id] = {'valid': True}

            result.checked_items += 1

        return result

    # Error Detection and Recovery

    async def detect_corruption(self, dataset_info: Any) -> List[CorruptionReport]:
        """
        Detect corruption in dataset chunks.

        Args:
            dataset_info: Dataset information

        Returns:
            List of corruption reports
        """
        reports = []

        if not dataset_info.chunks:
            return reports

        for chunk in dataset_info.chunks:
            chunk_id = chunk['chunk_id']
            expected_hash = chunk['hash']
            chunk_data = chunk['data']

            is_valid, actual_hash = self.verify_chunk_integrity(chunk_data, expected_hash)

            if not is_valid:
                report = CorruptionReport(
                    item_id=chunk_id,
                    item_type='chunk',
                    expected_hash=expected_hash,
                    actual_hash=actual_hash,
                    error_type='corruption',
                    recoverable=True
                )
                reports.append(report)

        return reports

    async def recover_corrupted_chunks(self, dataset_info: Any,
                                     corruption_reports: List[CorruptionReport]) -> IntegrityCheckResult:
        """
        Attempt to recover corrupted chunks.

        Args:
            dataset_info: Dataset information
            corruption_reports: List of corruption reports

        Returns:
            Recovery result
        """
        result = IntegrityCheckResult(success=True)

        if not self.enable_auto_recovery:
            result.errors.append("Auto-recovery disabled")
            result.success = False
            return result

        for report in corruption_reports:
            if report.item_type != 'chunk':
                continue

            # Find chunk in dataset
            chunk_data = None
            for chunk in dataset_info.chunks:
                if chunk['chunk_id'] == report.item_id:
                    chunk_data = chunk['data']
                    break

            if chunk_data is None:
                result.errors.append(f"Chunk {report.item_id} not found in dataset")
                continue

            # Attempt recovery by re-calculating (for now, just verify if it's recoverable)
            # In a real implementation, this might involve re-downloading or reconstructing
            new_hash = self.calculate_chunk_hash(chunk_data)

            if new_hash == report.expected_hash:
                result.recovered_items += 1
                report.recovery_attempts += 1
                report.last_attempt = time.time()
                self.stats['successful_recoveries'] += 1
            else:
                result.errors.append(f"Failed to recover chunk {report.item_id}")
                self.stats['failed_recoveries'] += 1

            result.checked_items += 1
            self.stats['recovery_attempts'] += 1

        return result

    # Pipeline Phase Verification

    async def verify_download_integrity(self, pipeline: Any) -> IntegrityCheckResult:
        """
        Verify integrity after download phase.

        Args:
            pipeline: Pipeline status

        Returns:
            Integrity check result
        """
        result = IntegrityCheckResult(success=True)
        dataset = pipeline.dataset_info

        if not dataset or not dataset.local_path:
            result.errors.append("No dataset available for download verification")
            result.success = False
            return result

        # Verify file exists and size matches
        if not os.path.exists(dataset.local_path):
            result.errors.append(f"Downloaded file not found: {dataset.local_path}")
            result.success = False
            return result

        actual_size = os.path.getsize(dataset.local_path)
        if actual_size != dataset.size_bytes:
            result.errors.append(f"File size mismatch: expected {dataset.size_bytes}, got {actual_size}")
            result.success = False

        # Verify checksum if available
        if dataset.checksum:
            is_valid, actual_hash = self.verify_file_integrity(dataset.local_path, dataset.checksum)
            if not is_valid:
                result.errors.append(f"File checksum mismatch: expected {dataset.checksum}, got {actual_hash}")
                result.success = False
            else:
                result.details['checksum_valid'] = True

        result.checked_items = 1
        return result

    async def verify_chunking_integrity(self, pipeline: Any) -> IntegrityCheckResult:
        """
        Verify integrity after chunking phase.

        Args:
            pipeline: Pipeline status

        Returns:
            Integrity check result
        """
        dataset = pipeline.dataset_info

        if not dataset:
            return IntegrityCheckResult(success=False, errors=["No dataset info available"])

        return await self.verify_dataset_chunks(dataset)

    async def verify_distribution_integrity(self, pipeline: Any,
                                          ipfs_manager=None) -> IntegrityCheckResult:
        """
        Verify integrity after distribution phase.

        Args:
            pipeline: Pipeline status
            ipfs_manager: IPFS manager for verification

        Returns:
            Integrity check result
        """
        result = IntegrityCheckResult(success=True)
        dataset = pipeline.dataset_info

        if not dataset or not dataset.chunks:
            result.errors.append("No chunks available for distribution verification")
            result.success = False
            return result

        # For now, verify chunks are properly formed
        # In a full implementation, this would verify IPFS CIDs and accessibility
        for chunk in dataset.chunks:
            if 'hash' not in chunk or 'data' not in chunk:
                result.errors.append(f"Malformed chunk: {chunk.get('chunk_id', 'unknown')}")
                result.success = False
                result.corrupted_items += 1
            else:
                result.checked_items += 1

        return result

    async def verify_training_data_integrity(self, node_id: str, chunk_cids: List[str],
                                           data_loader=None) -> IntegrityCheckResult:
        """
        Verify integrity of training data loaded by a node.

        Args:
            node_id: Node identifier
            chunk_cids: List of chunk CIDs
            data_loader: Data loader instance

        Returns:
            Integrity check result
        """
        result = IntegrityCheckResult(success=True)

        if not data_loader:
            result.errors.append("No data loader provided for training data verification")
            result.success = False
            return result

        for cid in chunk_cids:
            try:
                # Load data and verify it's accessible
                data = await data_loader.load_data(cid)
                if not data:
                    result.errors.append(f"Empty data loaded for CID {cid}")
                    result.missing_items += 1
                    result.success = False
                else:
                    result.checked_items += 1
                    result.details[cid] = {'size': len(data), 'valid': True}

            except Exception as e:
                result.errors.append(f"Failed to load data for CID {cid}: {e}")
                result.missing_items += 1
                result.success = False

        return result

    async def verify_pipeline_integrity(self, pipeline: Any,
                                      ipfs_manager=None, data_loader=None) -> Dict[str, IntegrityCheckResult]:
        """
        Comprehensive pipeline integrity verification.

        Args:
            pipeline: Pipeline status
            ipfs_manager: IPFS manager
            data_loader: Data loader

        Returns:
            Dictionary of phase verification results
        """
        results = {}

        # Verify each phase
        results['download'] = await self.verify_download_integrity(pipeline)
        results['chunking'] = await self.verify_chunking_integrity(pipeline)
        results['distribution'] = await self.verify_distribution_integrity(pipeline, ipfs_manager)

        # If training session exists, verify training data
        if pipeline.federated_session_id and data_loader:
            # This would need actual chunk CIDs from the session
            # For now, skip or implement based on available data
            pass

        return results

    def get_integrity_stats(self) -> Dict[str, Any]:
        """
        Get integrity verification statistics.

        Returns:
            Statistics dictionary
        """
        total_checks = self.stats['total_checks']
        successful_checks = self.stats['successful_checks']
        corruption_rate = self.stats['corruption_detected'] / max(1, total_checks)

        recovery_attempts = self.stats['recovery_attempts']
        recovery_success_rate = self.stats['successful_recoveries'] / max(1, recovery_attempts)

        return {
            'total_checks': total_checks,
            'successful_checks': successful_checks,
            'success_rate': successful_checks / max(1, total_checks),
            'corruption_detected': self.stats['corruption_detected'],
            'corruption_rate': corruption_rate,
            'recovery_attempts': recovery_attempts,
            'successful_recoveries': self.stats['successful_recoveries'],
            'recovery_success_rate': recovery_success_rate,
            'failed_recoveries': self.stats['failed_recoveries']
        }


# Convenience functions

def create_dataset_integrity_verifier(config: Config) -> DatasetIntegrityVerifier:
    """
    Create a Dataset Integrity Verifier instance.

    Args:
        config: Application configuration

    Returns:
        Configured DatasetIntegrityVerifier
    """
    return DatasetIntegrityVerifier(config)