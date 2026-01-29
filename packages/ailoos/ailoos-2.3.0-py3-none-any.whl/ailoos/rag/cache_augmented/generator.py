"""
Cache Augmented Generator for RAG systems.

Augments a base generator with caching capabilities to improve performance
for repeated queries with similar context.
"""

from typing import Any, Dict, List, Optional, Protocol
from .cache import Cache


class GeneratorProtocol(Protocol):
    """Protocol for base generators."""

    def generate(self, query: str, context: List[Dict[str, Any]]) -> str:
        """
        Generate a response given query and context.

        Args:
            query: The user query
            context: List of retrieved documents/context

        Returns:
            Generated response
        """
        ...


class CacheAugmentedGenerator:
    """
    Generator that uses caching to augment response generation.

    Checks cache for existing responses before generating new ones.
    """

    def __init__(
        self,
        base_generator: GeneratorProtocol,
        cache: Optional[Cache] = None,
        cache_enabled: bool = True
    ):
        """
        Initialize the cache augmented generator.

        Args:
            base_generator: The underlying generator to augment
            cache: Cache instance to use (creates default if None)
            cache_enabled: Whether to use caching
        """
        self.base_generator = base_generator
        self.cache = cache or Cache()
        self.cache_enabled = cache_enabled
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'total_queries': 0
        }

    def generate(self, query: str, context: List[Dict[str, Any]]) -> str:
        """
        Generate a response, using cache if available.

        Args:
            query: The user query
            context: List of retrieved documents

        Returns:
            Generated response
        """
        self.stats['total_queries'] += 1

        if not self.cache_enabled:
            return self.base_generator.generate(query, context)

        # Create cache key from context
        context_str = self._context_to_string(context)

        # Check cache
        cached_response = self.cache.get(query, context_str)
        if cached_response is not None:
            self.stats['cache_hits'] += 1
            return cached_response

        # Generate new response
        self.stats['cache_misses'] += 1
        response = self.base_generator.generate(query, context)

        # Cache the response
        self.cache.set(query, context_str, response)

        return response

    def _context_to_string(self, context: List[Dict[str, Any]]) -> str:
        """
        Convert context list to string for caching.

        Args:
            context: List of context documents

        Returns:
            String representation of context
        """
        # Sort by content for consistent hashing
        sorted_context = sorted(context, key=lambda x: x.get('content', ''))

        # Combine all content
        combined = []
        for doc in sorted_context:
            content = doc.get('content', '')
            # Include some metadata for better key uniqueness
            title = doc.get('metadata', {}).get('title', '')
            combined.append(f"{title}:{content}")

        return '\n'.join(combined)

    def get_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache hit/miss statistics
        """
        return self.stats.copy()

    def clear_cache(self) -> None:
        """Clear the cache."""
        self.cache.clear()
        self.stats = {'cache_hits': 0, 'cache_misses': 0, 'total_queries': 0}