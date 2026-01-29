"""
Data management module for Ailoos.
Handles dataset downloading, processing, chunking, and management.
"""

from .dataset_downloader import DatasetDownloader, DownloadConfig, DownloadProgress
from .dataset_chunker import DatasetChunker, ChunkConfig, ChunkMetadata, create_dataset_chunker, chunk_dataset_for_federated_training
from .refinery_engine import RefineryEngine, refinery_engine

__all__ = [
    'DatasetDownloader', 'DownloadConfig', 'DownloadProgress',
    'DatasetChunker', 'ChunkConfig', 'ChunkMetadata',
    'create_dataset_chunker', 'chunk_dataset_for_federated_training',
    'RefineryEngine', 'refinery_engine'
]