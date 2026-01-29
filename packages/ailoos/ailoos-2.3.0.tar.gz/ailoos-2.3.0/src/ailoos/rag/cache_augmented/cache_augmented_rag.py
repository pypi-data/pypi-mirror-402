"""
Cache Augmented RAG Implementation

This module implements CacheAugmentedRAG, a RAG technique that integrates
semantic caching with any existing RAG system to improve performance and reduce
latency for similar queries.
"""

import time
from typing import List, Dict, Any, Optional, Type
import logging

from ..core.base_rag import BaseRAG
from .cache_manager import CacheManager
from .quality_validator import CAGQualityValidator

logger = logging.getLogger(__name__)


class CacheAugmentedRAG(BaseRAG):
    """
    Cache-Augmented Retrieval-Augmented Generation.

    This RAG technique wraps any existing RAG implementation with semantic caching
    capabilities. It uses embeddings to detect semantically similar queries and
    serves cached responses when available, significantly improving performance
    for repeated or similar queries.

    Features:
    - Semantic similarity-based caching using sentence transformers
    - LRU/LFU eviction policies
    - Performance metrics tracking
    - Full compatibility with existing RAG techniques
    - Configurable cache parameters
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Cache Augmented RAG.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing:
                - base_rag_class: The RAG class to augment (e.g., NaiveRAG)
                - base_rag_config: Configuration for the base RAG
                - cache_config: Configuration for the cache manager
                    - model_name: Sentence transformer model (default: 'all-MiniLM-L6-v2')
                    - similarity_threshold: Similarity threshold for cache hits (default: 0.8)
                    - max_size: Maximum cache size (default: 1000)
                    - eviction_policy: 'LRU' or 'LFU' (default: 'LRU')
                    - cache_file: Optional file path for persistence
                - cache_enabled: Whether to enable caching (default: True)
        """
        super().__init__(config)

        # Extract configuration
        base_rag_class = config.get('base_rag_class')
        if not base_rag_class:
            raise ValueError("base_rag_class must be specified in config")

        base_rag_config = config.get('base_rag_config', {})
        cache_config = config.get('cache_config', {})
        self.cache_enabled = config.get('cache_enabled', True)

        # Initialize base RAG
        self.base_rag = base_rag_class(base_rag_config)

        # Initialize cache manager if enabled
        if self.cache_enabled:
            self.cache_manager = CacheManager(
                model_name=cache_config.get('model_name', 'all-MiniLM-L6-v2'),
                similarity_threshold=cache_config.get('similarity_threshold', 0.8),
                max_size=cache_config.get('max_size', 1000),
                eviction_policy=cache_config.get('eviction_policy', 'LRU'),
                cache_file=cache_config.get('cache_file')
            )
        else:
            self.cache_manager = None

        # Initialize CAG quality validator
        quality_config = config.get('quality_config', {})
        self.quality_validator = CAGQualityValidator(quality_config)

        # Store last generation metadata for quality validation
        self._last_generation_metadata = {}

        # Performance metrics
        self.cache_metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'total_queries': 0,
            'cache_hit_rate': 0.0,
            'avg_cache_lookup_time': 0.0,
            'total_cache_lookup_time': 0.0
        }

        base_rag_name = getattr(base_rag_class, '__name__', str(base_rag_class))
        logger.info(f"CacheAugmentedRAG initialized with base RAG: {base_rag_name}, cache_enabled: {self.cache_enabled}")

    def retrieve(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents using the base RAG retriever.

        Args:
            query (str): Search query
            top_k (int): Number of documents to retrieve
            filters (Optional[Dict[str, Any]]): Optional filters

        Returns:
            List[Dict[str, Any]]: Retrieved documents
        """
        return self.base_rag.retrieve(query, top_k=top_k, filters=filters)

    def generate(self, query: str, context: List[Dict[str, Any]], **kwargs) -> str:
        """
        Generate response using cache-first approach.

        First checks semantic cache for similar queries. If cache hit, returns
        cached response. Otherwise, generates new response and caches it.

        Args:
            query (str): Original query
            context (List[Dict[str, Any]]): Retrieved documents
            **kwargs: Additional generation parameters

        Returns:
            str: Generated or cached response
        """
        self.cache_metrics['total_queries'] += 1

        # If cache is disabled, generate directly
        if not self.cache_enabled or self.cache_manager is None:
            response = self.base_rag.generate(query, context, **kwargs)
            self._last_generation_metadata = {'cache_hit': False, 'cache_metadata': {}}
            return response

        # Convert context to string for cache key
        context_str = self._context_to_string(context)

        # Check cache
        start_time = time.time()
        cached_response = self.cache_manager.get(query, context_str)
        lookup_time = time.time() - start_time
        self.cache_metrics['total_cache_lookup_time'] += lookup_time

        if cached_response is not None:
            # Cache hit
            self.cache_metrics['cache_hits'] += 1
            logger.debug(f"Cache hit for query: {query[:50]}...")

            # Store metadata for quality validation
            self._last_generation_metadata = {
                'cache_hit': True,
                'cache_metadata': {
                    'cache_hit': True,
                    'cache_similarity': 0.9,  # Default high similarity for cache hits
                    'cache_timestamp': time.time() - 3600,  # Assume 1 hour ago
                    'original_length': len(cached_response.split())
                }
            }
            return cached_response

        # Cache miss - generate new response
        self.cache_metrics['cache_misses'] += 1
        logger.debug(f"Cache miss for query: {query[:50]}..., generating new response")

        response = self.base_rag.generate(query, context, **kwargs)

        # Cache the response
        self.cache_manager.set(query, context_str, response)

        # Update hit rate
        self._update_cache_metrics()

        self._last_generation_metadata = {'cache_hit': False, 'cache_metadata': {}}
        return response

    def evaluate(self, query: str, response: str, ground_truth: Optional[str] = None,
                  context: Optional[List[Dict[str, Any]]] = None,
                  cache_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """
        Evaluate the CAG response quality using specialized CAG validator.

        Args:
            query (str): Original query
            response (str): Generated response
            ground_truth (Optional[str]): Ground truth for comparison
            context (Optional[List[Dict[str, Any]]]): Retrieved context
            cache_metadata (Optional[Dict[str, Any]]): Cache-related metadata

        Returns:
            Dict[str, float]: Comprehensive CAG evaluation metrics
        """
        return self.quality_validator.evaluate(query, response, ground_truth, context, cache_metadata)

    def run(self, query: str, top_k: int = 5, **kwargs) -> Dict[str, Any]:
        """
        Execute the complete cache-augmented RAG pipeline.

        Overrides base run method to include cache metrics and quality validation.

        Args:
            query (str): Input query
            top_k (int): Number of documents to retrieve
            **kwargs: Additional parameters for generation

        Returns:
            Dict[str, Any]: Complete RAG result with cache metrics and quality scores
        """
        try:
            # Step 1: Retrieve relevant context
            context = self.retrieve(query, top_k=top_k)

            # Step 2: Generate response (with caching)
            response = self.generate(query, context, **kwargs)
            cache_hit = self._last_generation_metadata.get('cache_hit', False)
            cache_metadata = self._last_generation_metadata.get('cache_metadata', {})

            # Step 3: Evaluate performance with CAG-specific quality validator
            metrics = self.evaluate(query, response, context=context, cache_metadata=cache_metadata)

            # Step 4: Build result with comprehensive metadata
            result = {
                "query": query,
                "context": context,
                "response": response,
                "metrics": metrics,
                "metadata": {
                    "rag_type": self.__class__.__name__,
                    "base_rag_type": self.base_rag.__class__.__name__,
                    "top_k": top_k,
                    "cache_enabled": self.cache_enabled,
                    "cache_hit": cache_hit,
                    "cache_metrics": self.get_cache_metrics(),
                    "quality_validator_stats": self.quality_validator.get_consistency_stats(),
                    "timestamp": time.time()
                }
            }

            logger.info(f"CacheAugmentedRAG pipeline completed for query: {query[:50]}... (cache_hit: {cache_hit})")
            return result

        except Exception as e:
            logger.error(f"Error in CacheAugmentedRAG pipeline: {str(e)}")
            raise

    def _context_to_string(self, context: List[Dict[str, Any]]) -> str:
        """
        Convert context list to string for caching.

        Creates a deterministic string representation of the context for cache keys.

        Args:
            context: List of context documents

        Returns:
            String representation of context
        """
        # Sort by content for consistent hashing
        sorted_context = sorted(context, key=lambda x: x.get('content', ''))

        # Combine content with metadata
        combined_parts = []
        for doc in sorted_context:
            content = doc.get('content', '')
            # Include score and other metadata for uniqueness
            score = doc.get('score', 0.0)
            title = doc.get('metadata', {}).get('title', '')
            combined_parts.append(f"{title}|{score:.4f}|{content}")

        return '\n'.join(combined_parts)

    def _update_cache_metrics(self):
        """Update derived cache metrics like hit rate."""
        total = self.cache_metrics['total_queries']
        if total > 0:
            self.cache_metrics['cache_hit_rate'] = self.cache_metrics['cache_hits'] / total

        # Update average lookup time
        lookups = self.cache_metrics['cache_hits'] + self.cache_metrics['cache_misses']
        if lookups > 0:
            self.cache_metrics['avg_cache_lookup_time'] = self.cache_metrics['total_cache_lookup_time'] / lookups

    def get_cache_metrics(self) -> Dict[str, Any]:
        """
        Get current cache performance metrics.

        Returns:
            Dict[str, Any]: Cache metrics including hit rate, lookup times, etc.
        """
        if self.cache_manager:
            cache_manager_metrics = self.cache_manager.get_metrics()
        else:
            cache_manager_metrics = {}

        return {
            **self.cache_metrics,
            'cache_manager_metrics': cache_manager_metrics
        }

    def clear_cache(self):
        """Clear all cached entries."""
        if self.cache_manager:
            self.cache_manager.clear()
        self.cache_metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'total_queries': 0,
            'cache_hit_rate': 0.0,
            'avg_cache_lookup_time': 0.0,
            'total_cache_lookup_time': 0.0
        }
        logger.info("Cache cleared")

    def save_cache(self, filepath: Optional[str] = None):
        """
        Save cache state to disk.

        Args:
            filepath: Path to save cache (uses configured file if None)
        """
        if self.cache_manager:
            self.cache_manager.save_cache(filepath)
            logger.info(f"Cache saved to {filepath or self.cache_manager.cache_file}")

    def load_cache(self, filepath: Optional[str] = None):
        """
        Load cache state from disk.

        Args:
            filepath: Path to load cache from (uses configured file if None)
        """
        if self.cache_manager:
            self.cache_manager.load_cache(filepath)
            logger.info(f"Cache loaded from {filepath or self.cache_manager.cache_file}")

    def get_pipeline_info(self) -> Dict[str, Any]:
        """
        Get information about the cache-augmented RAG pipeline.

        Returns:
            Dict[str, Any]: Pipeline information including base RAG and cache config
        """
        base_info = self.base_rag.get_pipeline_info() if hasattr(self.base_rag, 'get_pipeline_info') else {}

        return {
            'technique': 'CacheAugmentedRAG',
            'description': 'Cache-augmented RAG with semantic similarity caching',
            'base_rag': base_info,
            'cache_enabled': self.cache_enabled,
            'cache_config': {
                'model_name': self.cache_manager.model_name if self.cache_manager else None,
                'similarity_threshold': self.cache_manager.similarity_threshold if self.cache_manager else None,
                'max_size': self.cache_manager.max_size if self.cache_manager else None,
                'eviction_policy': self.cache_manager.eviction_policy if self.cache_manager else None,
                'cache_size': len(self.cache_manager) if self.cache_manager else 0
            },
            'cache_metrics': self.get_cache_metrics(),
            'config': self.config
        }