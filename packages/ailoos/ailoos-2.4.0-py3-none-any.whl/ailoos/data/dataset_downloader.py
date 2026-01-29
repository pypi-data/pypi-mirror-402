"""
Dataset Downloader with resume capability, progress tracking, and integrity verification.
"""

import asyncio
import hashlib
import logging
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Any
from urllib.parse import urlparse

import aiofiles
import aiohttp
import yaml

logger = logging.getLogger(__name__)


@dataclass
class DownloadConfig:
    """Configuration for dataset download."""
    name: str
    description: str
    urls: List[str]
    size: str
    partitioning_strategy: str
    expected_hash: Optional[str] = None
    chunk_size: int = 8192
    max_retries: int = 3
    timeout: int = 300
    resume_enabled: bool = True


@dataclass
class DownloadProgress:
    """Progress information for download."""
    dataset_name: str
    downloaded_bytes: int
    total_bytes: int
    speed_bps: float
    eta_seconds: float
    status: str
    error_message: Optional[str] = None

    @property
    def progress_percentage(self) -> float:
        """Calculate download progress percentage."""
        if self.total_bytes == 0:
            return 0.0
        return (self.downloaded_bytes / self.total_bytes) * 100.0


class DatasetDownloader:
    """
    Handles automatic downloading of large datasets with resume capability,
    progress tracking, and integrity verification.
    """

    def __init__(self, config_path: str, download_dir: Optional[str] = None):
        """
        Initialize the dataset downloader.

        Args:
            config_path: Path to the YAML configuration file
            download_dir: Directory to store downloaded datasets
        """
        self.config_path = Path(config_path)
        self.download_dir = Path(download_dir) if download_dir else Path("datasets")
        self.download_dir.mkdir(parents=True, exist_ok=True)

        self.datasets: Dict[str, DownloadConfig] = {}
        self.active_downloads: Dict[str, asyncio.Task] = {}

        # Load configuration
        self._load_config()

    def _load_config(self):
        """Load dataset configurations from YAML file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            for dataset in config_data.get('datasets', []):
                config = DownloadConfig(
                    name=dataset['name'],
                    description=dataset['description'],
                    urls=dataset['urls'],
                    size=dataset['size'],
                    partitioning_strategy=dataset['partitioning_strategy']
                )
                self.datasets[config.name] = config

            logger.info(f"Loaded {len(self.datasets)} dataset configurations")

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise

    async def download_dataset(
        self,
        dataset_name: str,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
        force_redownload: bool = False
    ) -> bool:
        """
        Download a dataset with progress tracking and resume capability.

        Args:
            dataset_name: Name of the dataset to download
            progress_callback: Callback function for progress updates
            force_redownload: Force redownload even if file exists

        Returns:
            True if download completed successfully
        """
        if dataset_name not in self.datasets:
            raise ValueError(f"Dataset '{dataset_name}' not found in configuration")

        config = self.datasets[dataset_name]
        download_path = self.download_dir / f"{dataset_name.replace(' ', '_').lower()}.dat"

        # Check if already downloaded and verified
        if not force_redownload and download_path.exists():
            if await self._verify_integrity(download_path, config.expected_hash):
                logger.info(f"Dataset {dataset_name} already exists and is valid")
                if progress_callback:
                    progress = DownloadProgress(
                        dataset_name=dataset_name,
                        downloaded_bytes=download_path.stat().st_size,
                        total_bytes=download_path.stat().st_size,
                        speed_bps=0.0,
                        eta_seconds=0.0,
                        status="completed"
                    )
                    progress_callback(progress)
                return True

        # Start download task
        task_key = f"download_{dataset_name}"
        if task_key in self.active_downloads:
            logger.warning(f"Download for {dataset_name} already in progress")
            return False

        task = asyncio.create_task(
            self._download_with_resume(config, download_path, progress_callback)
        )
        self.active_downloads[task_key] = task

        try:
            success = await task
            return success
        finally:
            del self.active_downloads[task_key]

    async def _download_with_resume(
        self,
        config: DownloadConfig,
        download_path: Path,
        progress_callback: Optional[Callable[[DownloadProgress], None]]
    ) -> bool:
        """Download file with resume capability."""
        start_time = asyncio.get_event_loop().time()

        # Determine which URL to use (try first available)
        download_url = config.urls[0]

        # Check for existing partial download
        existing_size = download_path.stat().st_size if download_path.exists() else 0
        resume_supported = config.resume_enabled and existing_size > 0

        headers = {}
        if resume_supported:
            headers['Range'] = f'bytes={existing_size}-'
            logger.info(f"Resuming download from byte {existing_size}")

        for attempt in range(config.max_retries):
            try:
                timeout = aiohttp.ClientTimeout(total=config.timeout)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(download_url, headers=headers) as response:
                        if response.status == 416:
                            # Range not satisfiable - file is already complete
                            logger.info("File already complete")
                            return await self._verify_integrity(download_path, config.expected_hash)

                        if response.status not in (200, 206):
                            raise aiohttp.ClientResponseError(
                                response.request_info,
                                response.history,
                                status=response.status,
                                message=response.reason
                            )

                        # Get total size
                        total_size = int(response.headers.get('content-length', 0))
                        if response.status == 206:
                            total_size += existing_size

                        mode = 'ab' if resume_supported else 'wb'
                        downloaded_bytes = existing_size

                        async with aiofiles.open(download_path, mode) as f:
                            async for chunk in response.content.iter_chunked(config.chunk_size):
                                await f.write(chunk)
                                downloaded_bytes += len(chunk)

                                # Calculate progress
                                elapsed_time = asyncio.get_event_loop().time() - start_time
                                speed_bps = downloaded_bytes / elapsed_time if elapsed_time > 0 else 0
                                remaining_bytes = total_size - downloaded_bytes
                                eta_seconds = remaining_bytes / speed_bps if speed_bps > 0 else 0

                                if progress_callback:
                                    progress = DownloadProgress(
                                        dataset_name=config.name,
                                        downloaded_bytes=downloaded_bytes,
                                        total_bytes=total_size,
                                        speed_bps=speed_bps,
                                        eta_seconds=eta_seconds,
                                        status="downloading"
                                    )
                                    progress_callback(progress)

                # Verify integrity
                if await self._verify_integrity(download_path, config.expected_hash):
                    if progress_callback:
                        progress = DownloadProgress(
                            dataset_name=config.name,
                            downloaded_bytes=downloaded_bytes,
                            total_bytes=total_size,
                            speed_bps=0.0,
                            eta_seconds=0.0,
                            status="completed"
                        )
                        progress_callback(progress)
                    logger.info(f"Successfully downloaded {config.name}")
                    return True
                else:
                    logger.error(f"Integrity verification failed for {config.name}")
                    if progress_callback:
                        progress = DownloadProgress(
                            dataset_name=config.name,
                            downloaded_bytes=downloaded_bytes,
                            total_bytes=total_size,
                            speed_bps=0.0,
                            eta_seconds=0.0,
                            status="failed",
                            error_message="Integrity verification failed"
                        )
                        progress_callback(progress)
                    return False

            except Exception as e:
                logger.error(f"Download attempt {attempt + 1} failed: {e}")
                if attempt == config.max_retries - 1:
                    if progress_callback:
                        progress = DownloadProgress(
                            dataset_name=config.name,
                            downloaded_bytes=downloaded_bytes if 'downloaded_bytes' in locals() else 0,
                            total_bytes=total_size if 'total_size' in locals() else 0,
                            speed_bps=0.0,
                            eta_seconds=0.0,
                            status="failed",
                            error_message=str(e)
                        )
                        progress_callback(progress)
                    return False

                # Wait before retry
                await asyncio.sleep(2 ** attempt)

        return False

    async def _verify_integrity(self, file_path: Path, expected_hash: Optional[str]) -> bool:
        """
        Verify file integrity using SHA256 hash.

        Args:
            file_path: Path to the file to verify
            expected_hash: Expected SHA256 hash (optional)

        Returns:
            True if integrity check passes
        """
        if not expected_hash:
            logger.warning("No expected hash provided, skipping integrity verification")
            return True

        try:
            sha256 = hashlib.sha256()
            async with aiofiles.open(file_path, 'rb') as f:
                while chunk := await f.read(8192):
                    sha256.update(chunk)

            actual_hash = sha256.hexdigest()
            if actual_hash == expected_hash:
                logger.info(f"Integrity verification passed for {file_path.name}")
                return True
            else:
                logger.error(f"Hash mismatch for {file_path.name}: expected {expected_hash}, got {actual_hash}")
                return False

        except Exception as e:
            logger.error(f"Error during integrity verification: {e}")
            return False

    def get_available_datasets(self) -> List[str]:
        """Get list of available dataset names."""
        return list(self.datasets.keys())

    def get_dataset_info(self, dataset_name: str) -> Optional[DownloadConfig]:
        """Get configuration for a specific dataset."""
        return self.datasets.get(dataset_name)

    async def cancel_download(self, dataset_name: str) -> bool:
        """Cancel an active download."""
        task_key = f"download_{dataset_name}"
        if task_key in self.active_downloads:
            task = self.active_downloads[task_key]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.active_downloads[task_key]
            logger.info(f"Cancelled download for {dataset_name}")
            return True
        return False

    def get_active_downloads(self) -> List[str]:
        """Get list of currently active downloads."""
        return [key.replace("download_", "") for key in self.active_downloads.keys()]