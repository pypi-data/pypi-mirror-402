"""
Automatic Cache Compression for Distributed Cache System
Provides compression/decompression of cache values to save memory
"""

import zlib
import json
import time
from typing import Any, Optional, Union
import logging

try:
    import lz4.frame
    LZ4_AVAILABLE = True
except ImportError:
    LZ4_AVAILABLE = False
    lz4 = None

logger = logging.getLogger(__name__)

class CacheCompression:
    """Handles automatic compression of cache values"""

    COMPRESSION_TYPES = {
        'zlib': 'zlib',
        'gzip': 'gzip',
        'lz4': 'lz4' if LZ4_AVAILABLE else None
    }

    def __init__(self,
                 compression_type: str = 'zlib',
                 compression_level: int = 6,
                 min_size_threshold: int = 1024,
                 auto_compress: bool = True):
        """
        Initialize compression handler

        Args:
            compression_type: Type of compression ('zlib', 'gzip', 'lz4')
            compression_level: Compression level (1-9 for zlib/gzip)
            min_size_threshold: Minimum size in bytes to compress
            auto_compress: Whether to compress automatically
        """
        if compression_type not in self.COMPRESSION_TYPES or self.COMPRESSION_TYPES[compression_type] is None:
            raise ValueError(f"Unsupported compression type: {compression_type}")

        self.compression_type = compression_type
        self.compression_level = compression_level
        self.min_size_threshold = min_size_threshold
        self.auto_compress = auto_compress

        # Compression stats
        self.compression_count = 0
        self.decompression_count = 0
        self.original_bytes = 0
        self.compressed_bytes = 0

    def should_compress(self, data: Any) -> bool:
        """Determine if data should be compressed"""
        if not self.auto_compress:
            return False

        try:
            serialized = json.dumps(data)
            return len(serialized.encode('utf-8')) >= self.min_size_threshold
        except (TypeError, ValueError):
            return False

    def compress(self, data: Any) -> tuple:
        """
        Compress data if appropriate

        Returns:
            (compressed_data, was_compressed, original_size, compressed_size)
        """
        try:
            serialized = json.dumps(data)
            original_bytes = len(serialized.encode('utf-8'))

            if not self.should_compress(data):
                return data, False, original_bytes, original_bytes

            compressed_data = self._compress_data(serialized)
            compressed_size = len(compressed_data)

            # Only use compression if it actually saves space
            if compressed_size >= original_bytes:
                return data, False, original_bytes, original_bytes

            self.compression_count += 1
            self.original_bytes += original_bytes
            self.compressed_bytes += compressed_size

            logger.debug(f"Compressed {original_bytes} -> {compressed_size} bytes")
            return compressed_data, True, original_bytes, compressed_size

        except Exception as e:
            logger.warning(f"Compression failed: {e}")
            original_bytes = len(str(data).encode('utf-8'))
            return data, False, original_bytes, original_bytes

    def decompress(self, compressed_data: Any, was_compressed: bool) -> Any:
        """Decompress data if it was compressed"""
        if not was_compressed:
            return compressed_data

        try:
            self.decompression_count += 1
            decompressed = self._decompress_data(compressed_data)
            return json.loads(decompressed)
        except Exception as e:
            logger.error(f"Decompression failed: {e}")
            return compressed_data

    def _compress_data(self, data: str) -> bytes:
        """Internal compression method"""
        if self.compression_type == 'zlib':
            return zlib.compress(data.encode('utf-8'), level=self.compression_level)
        elif self.compression_type == 'gzip':
            import gzip
            return gzip.compress(data.encode('utf-8'), compresslevel=self.compression_level)
        elif self.compression_type == 'lz4' and LZ4_AVAILABLE:
            return lz4.frame.compress(data.encode('utf-8'), compression_level=self.compression_level)
        else:
            raise ValueError(f"Unsupported compression type: {self.compression_type}")

    def _decompress_data(self, compressed_data: bytes) -> str:
        """Internal decompression method"""
        if self.compression_type == 'zlib':
            return zlib.decompress(compressed_data).decode('utf-8')
        elif self.compression_type == 'gzip':
            import gzip
            return gzip.decompress(compressed_data).decode('utf-8')
        elif self.compression_type == 'lz4' and LZ4_AVAILABLE:
            return lz4.frame.decompress(compressed_data).decode('utf-8')
        else:
            raise ValueError(f"Unsupported compression type: {self.compression_type}")

    def get_stats(self) -> dict:
        """Get compression statistics"""
        total_operations = self.compression_count + self.decompression_count
        compression_ratio = self.compressed_bytes / self.original_bytes if self.original_bytes > 0 else 1.0
        space_saved = self.original_bytes - self.compressed_bytes

        return {
            'compression_type': self.compression_type,
            'compression_count': self.compression_count,
            'decompression_count': self.decompression_count,
            'total_operations': total_operations,
            'original_bytes': self.original_bytes,
            'compressed_bytes': self.compressed_bytes,
            'compression_ratio': compression_ratio,
            'space_saved': space_saved,
            'space_saved_percentage': (space_saved / self.original_bytes * 100) if self.original_bytes > 0 else 0
        }

    def reset_stats(self):
        """Reset compression statistics"""
        self.compression_count = 0
        self.decompression_count = 0
        self.original_bytes = 0
        self.compressed_bytes = 0

class CompressedCacheEntry:
    """Cache entry that handles compression automatically"""

    def __init__(self, key: str, value: Any, compression: CacheCompression, ttl: Optional[float] = None):
        self.key = key
        self.compression = compression
        self.ttl = ttl
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl if ttl else None

        # Compress value
        self.compressed_value, self.was_compressed, self.original_size, self.compressed_size = compression.compress(value)

    def get_value(self) -> Any:
        """Get decompressed value"""
        return self.compression.decompress(self.compressed_value, self.was_compressed)

    def is_expired(self) -> bool:
        return self.expires_at is not None and time.time() > self.expires_at

    def get_size(self) -> int:
        """Get the size used in cache (compressed size)"""
        return self.compressed_size if self.was_compressed else self.original_size

    def get_metadata(self) -> dict:
        """Get entry metadata"""
        return {
            'key': self.key,
            'was_compressed': self.was_compressed,
            'original_size': self.original_size,
            'compressed_size': self.compressed_size,
            'compression_ratio': self.compressed_size / self.original_size if self.original_size > 0 else 1.0,
            'ttl': self.ttl,
            'expires_at': self.expires_at,
            'created_at': self.created_at
        }