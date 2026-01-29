"""
Cache Augmented Generation (CAG) module.

This module provides cache-augmented generation capabilities for RAG systems,
improving performance by caching generated responses.
"""

from .cache import Cache
from .cache_manager import CacheManager
from .generator import CacheAugmentedGenerator
from .cache_augmented_rag import CacheAugmentedRAG

__all__ = ['Cache', 'CacheManager', 'CacheAugmentedGenerator', 'CacheAugmentedRAG']