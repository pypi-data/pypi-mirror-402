"""
Cache interface for Cache Augmented Generation.

Provides a simple caching layer to store and retrieve generated responses.
"""

import hashlib
from typing import Any, Optional
from cachetools import TTLCache


class Cache:
    """
    Simple TTL cache for storing generated responses.

    Uses an in-memory TTL cache with automatic expiration.
    """

    def __init__(self, maxsize: int = 1000, ttl: int = 3600):
        """
        Initialize the cache.

        Args:
            maxsize: Maximum number of items in cache
            ttl: Time to live in seconds for cache entries
        """
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)

    def _get_key(self, query: str, context: str) -> str:
        """
        Generate a cache key from query and context.

        Args:
            query: The user query
            context: The retrieved context

        Returns:
            A hash key for the cache
        """
        combined = f"{query}|{context}"
        return hashlib.md5(combined.encode()).hexdigest()

    def get(self, query: str, context: str) -> Optional[str]:
        """
        Retrieve a cached response.

        Args:
            query: The user query
            context: The retrieved context

        Returns:
            Cached response if exists, None otherwise
        """
        key = self._get_key(query, context)
        return self.cache.get(key)

    def set(self, query: str, context: str, response: str) -> None:
        """
        Store a response in cache.

        Args:
            query: The user query
            context: The retrieved context
            response: The generated response
        """
        key = self._get_key(query, context)
        self.cache[key] = response

    def clear(self) -> None:
        """Clear all cached entries."""
        self.cache.clear()

    def __len__(self) -> int:
        """Return the number of items in cache."""
        return len(self.cache)