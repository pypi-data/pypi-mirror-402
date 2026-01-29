"""
Semantic Cache Manager for RAG systems.

Provides semantic caching using sentence embeddings and cosine similarity,
with LRU/LFU eviction policies, performance metrics, and full serialization.
"""

import json
import pickle
import time
from collections import OrderedDict
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from sentence_transformers import SentenceTransformer


@dataclass
class CacheEntry:
    """Represents a cached entry with semantic information."""
    query: str
    context: str
    response: str
    embedding: np.ndarray
    timestamp: float
    access_count: int = 0
    last_accessed: float = 0.0


class CacheManager:
    """
    Semantic cache manager using sentence embeddings for similarity-based retrieval.

    Features:
    - Semantic similarity using sentence-transformers and cosine similarity
    - LRU and LFU eviction policies
    - Performance metrics tracking
    - Full serialization/deserialization support
    """

    def __init__(
        self,
        model_name: str = 'all-MiniLM-L6-v2',
        similarity_threshold: float = 0.8,
        max_size: int = 1000,
        eviction_policy: str = 'LRU',  # 'LRU' or 'LFU'
        cache_file: Optional[str] = None
    ):
        """
        Initialize the semantic cache manager.

        Args:
            model_name: Sentence transformer model name
            similarity_threshold: Minimum similarity for cache hit (0-1)
            max_size: Maximum number of entries in cache
            eviction_policy: 'LRU' or 'LFU'
            cache_file: Path to load/save cache state
        """
        self.model_name = model_name
        self.similarity_threshold = similarity_threshold
        self.max_size = max_size
        self.eviction_policy = eviction_policy.upper()
        self.cache_file = cache_file

        # Initialize model
        self.model = self._load_model()

        # Cache storage: OrderedDict for LRU, dict for LFU
        self.cache: Union[OrderedDict[str, CacheEntry], Dict[str, CacheEntry]] = (
            OrderedDict() if self.eviction_policy == 'LRU' else {}
        )
        self.lfu_counters: Dict[str, int] = {} if self.eviction_policy == 'LFU' else None

        # Performance metrics
        self.metrics = {
            'total_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_similarity_search_time': 0.0,
            'avg_embedding_time': 0.0,
            'evictions': 0
        }

        # Load cache if file provided
        if cache_file:
            self.load_cache()

    def _load_model(self) -> SentenceTransformer:
        """Load the sentence transformer model."""
        try:
            return SentenceTransformer(self.model_name)
        except Exception as e:
            raise RuntimeError(f"Failed to load model {self.model_name}: {e}")

    def _compute_embedding(self, text: str) -> np.ndarray:
        """Compute embedding for given text."""
        start_time = time.time()
        embedding = self.model.encode(text, convert_to_numpy=True)
        self._update_metric('avg_embedding_time', time.time() - start_time)
        return embedding

    def _cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings."""
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        return dot_product / (norm1 * norm2) if norm1 and norm2 else 0.0

    def _find_most_similar(self, query_embedding: np.ndarray) -> Tuple[Optional[str], float]:
        """Find the most similar cached entry."""
        start_time = time.time()
        max_similarity = 0.0
        best_key = None

        # Create a snapshot of cache items to avoid "dictionary changed size during iteration"
        cache_items = list(self.cache.items())

        for key, entry in cache_items:
            similarity = self._cosine_similarity(query_embedding, entry.embedding)
            if similarity > max_similarity:
                max_similarity = similarity
                best_key = key

        self._update_metric('avg_similarity_search_time', time.time() - start_time)
        return best_key, max_similarity

    def _update_metric(self, metric: str, value: float):
        """Update running average metrics."""
        current = self.metrics[metric]
        total = self.metrics['total_queries']
        if total > 0:
            self.metrics[metric] = (current * (total - 1) + value) / total
        else:
            self.metrics[metric] = value

    def _evict_if_needed(self):
        """Evict entries based on eviction policy if cache is full."""
        if self.max_size == 0:
            # Special case: cache disabled - don't store anything
            return

        while len(self.cache) >= self.max_size:
            if self.eviction_policy == 'LRU':
                # Remove least recently used
                evicted_key, _ = self.cache.popitem(last=False)
            elif self.eviction_policy == 'LFU':
                # Remove least frequently used
                evicted_key = min(self.lfu_counters, key=self.lfu_counters.get)
                del self.cache[evicted_key]
                del self.lfu_counters[evicted_key]

            self.metrics['evictions'] += 1

    def _update_access(self, key: str):
        """Update access patterns for eviction policies."""
        if self.eviction_policy == 'LRU':
            # Move to end (most recently used)
            self.cache.move_to_end(key)
        elif self.eviction_policy == 'LFU':
            self.lfu_counters[key] += 1

    def get(self, query: str, context: str) -> Optional[str]:
        """
        Retrieve cached response using semantic similarity.

        Args:
            query: The user query
            context: The retrieved context

        Returns:
            Cached response if similarity > threshold, None otherwise
        """
        self.metrics['total_queries'] += 1

        if not self.cache:
            self.metrics['cache_misses'] += 1
            return None

        # Create combined text for embedding
        combined_text = f"{query} {context}"
        query_embedding = self._compute_embedding(combined_text)

        # Find most similar entry
        best_key, similarity = self._find_most_similar(query_embedding)

        if best_key and similarity >= self.similarity_threshold:
            self.metrics['cache_hits'] += 1
            entry = self.cache[best_key]
            entry.access_count += 1
            entry.last_accessed = time.time()
            self._update_access(best_key)
            return entry.response

        self.metrics['cache_misses'] += 1
        return None

    def set(self, query: str, context: str, response: str):
        """
        Store a response in the semantic cache.

        Args:
            query: The user query
            context: The retrieved context
            response: The generated response
        """
        # Evict if needed (before adding new entry)
        self._evict_if_needed()

        # Create combined text and embedding
        combined_text = f"{query} {context}"
        embedding = self._compute_embedding(combined_text)

        # Create cache key (use hash of combined text)
        import hashlib
        key = hashlib.md5(combined_text.encode()).hexdigest()

        # Create entry
        entry = CacheEntry(
            query=query,
            context=context,
            response=response,
            embedding=embedding,
            timestamp=time.time(),
            access_count=0,
            last_accessed=time.time()
        )

        # Add to cache
        self.cache[key] = entry
        if self.eviction_policy == 'LFU':
            self.lfu_counters[key] = 0

    def clear(self):
        """Clear all cached entries."""
        self.cache.clear()
        if self.lfu_counters:
            self.lfu_counters.clear()
        self.metrics = {
            'total_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_similarity_search_time': 0.0,
            'avg_embedding_time': 0.0,
            'evictions': 0
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        metrics = self.metrics.copy()
        metrics['cache_size'] = len(self.cache)
        metrics['hit_rate'] = (
            metrics['cache_hits'] / metrics['total_queries']
            if metrics['total_queries'] > 0 else 0.0
        )
        return metrics

    def save_cache(self, filepath: Optional[str] = None):
        """
        Serialize and save the cache state to disk.

        Args:
            filepath: Path to save cache (uses self.cache_file if None)
        """
        filepath = filepath or self.cache_file
        if not filepath:
            raise ValueError("No filepath provided for saving cache")

        # Prepare serializable data
        cache_data = {
            'model_name': self.model_name,
            'similarity_threshold': self.similarity_threshold,
            'max_size': self.max_size,
            'eviction_policy': self.eviction_policy,
            'metrics': self.metrics,
            'entries': []
        }

        # Convert entries to serializable format
        for key, entry in self.cache.items():
            entry_dict = asdict(entry)
            entry_dict['embedding'] = entry.embedding.tolist()  # Convert numpy to list
            entry_dict['key'] = key
            cache_data['entries'].append(entry_dict)

        if self.lfu_counters:
            cache_data['lfu_counters'] = self.lfu_counters

        # Save to file
        with open(filepath, 'wb') as f:
            pickle.dump(cache_data, f)

    def load_cache(self, filepath: Optional[str] = None):
        """
        Load and deserialize cache state from disk.

        Args:
            filepath: Path to load cache from (uses self.cache_file if None)
        """
        filepath = filepath or self.cache_file
        if not filepath:
            raise ValueError("No filepath provided for loading cache")

        try:
            with open(filepath, 'rb') as f:
                cache_data = pickle.load(f)

            # Restore configuration
            self.model_name = cache_data['model_name']
            self.similarity_threshold = cache_data.get('similarity_threshold', 0.8)
            self.max_size = cache_data['max_size']
            self.eviction_policy = cache_data['eviction_policy']
            self.metrics = cache_data['metrics']

            # Reinitialize model if changed
            # Note: SentenceTransformer doesn't have model_name_or_path, check model name directly
            try:
                current_model_name = getattr(self.model, 'model_name_or_path', None) or str(self.model)
                if self.model_name not in current_model_name:
                    self.model = self._load_model()
            except:
                # If we can't check, reload to be safe
                self.model = self._load_model()

            # Reinitialize cache structure
            self.cache = (
                OrderedDict() if self.eviction_policy == 'LRU' else {}
            )
            self.lfu_counters = cache_data.get('lfu_counters', {})

            # Restore entries
            for entry_data in cache_data['entries']:
                entry = CacheEntry(
                    query=entry_data['query'],
                    context=entry_data['context'],
                    response=entry_data['response'],
                    embedding=np.array(entry_data['embedding']),
                    timestamp=entry_data['timestamp'],
                    access_count=entry_data['access_count'],
                    last_accessed=entry_data['last_accessed']
                )
                key = entry_data['key']
                self.cache[key] = entry

        except FileNotFoundError:
            # Cache file doesn't exist, start fresh
            pass
        except Exception as e:
            # Re-raise the exception for testing purposes
            raise RuntimeError(f"Failed to load cache from {filepath}: {e}")

    def __len__(self) -> int:
        """Return the number of entries in cache."""
        return len(self.cache)