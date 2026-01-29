"""
Comprehensive unit tests for CacheManager functionality.
"""

import os
import tempfile
import time
import unittest
import numpy as np
from unittest.mock import patch, MagicMock
from src.ailoos.rag.cache_augmented.cache_manager import CacheManager, CacheEntry


class TestCacheManager(unittest.TestCase):
    """Comprehensive test suite for CacheManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.cache = CacheManager(max_size=10, similarity_threshold=0.8)

    def tearDown(self):
        """Clean up after tests."""
        self.cache.clear()

    def test_initialization_default(self):
        """Test CacheManager initialization with default parameters."""
        cache = CacheManager()
        self.assertEqual(cache.model_name, 'all-MiniLM-L6-v2')
        self.assertEqual(cache.similarity_threshold, 0.8)
        self.assertEqual(cache.max_size, 1000)
        self.assertEqual(cache.eviction_policy, 'LRU')
        self.assertIsNone(cache.cache_file)
        self.assertIsInstance(cache.cache, dict)
        self.assertIsNone(cache.lfu_counters)

    def test_initialization_custom_params(self):
        """Test CacheManager initialization with custom parameters."""
        # Use a valid model name that exists
        cache = CacheManager(
            model_name='all-MiniLM-L6-v2',  # Use the default model
            similarity_threshold=0.9,
            max_size=50,
            eviction_policy='LFU',
            cache_file='/tmp/test.pkl'
        )
        self.assertEqual(cache.model_name, 'all-MiniLM-L6-v2')
        self.assertEqual(cache.similarity_threshold, 0.9)
        self.assertEqual(cache.max_size, 50)
        self.assertEqual(cache.eviction_policy, 'LFU')
        self.assertEqual(cache.cache_file, '/tmp/test.pkl')
        self.assertIsInstance(cache.lfu_counters, dict)

    def test_initialization_invalid_eviction_policy(self):
        """Test initialization with invalid eviction policy."""
        # The code doesn't validate eviction policy, just converts to upper
        cache = CacheManager(eviction_policy='invalid')
        self.assertEqual(cache.eviction_policy, 'INVALID')
        # Should default to OrderedDict for non-LFU policies
        self.assertIsInstance(cache.cache, dict)
        self.assertIsNone(cache.lfu_counters)

    @patch('src.ailoos.rag.cache_augmented.cache_manager.SentenceTransformer')
    def test_load_model_failure(self, mock_sentence_transformer):
        """Test model loading failure."""
        mock_sentence_transformer.side_effect = Exception("Model load failed")

        with self.assertRaises(RuntimeError):
            CacheManager()

    def test_empty_cache_operations(self):
        """Test operations on empty cache."""
        # Get from empty cache
        result = self.cache.get("test query", "test context")
        self.assertIsNone(result)
        self.assertEqual(len(self.cache), 0)

        # Metrics should reflect miss
        metrics = self.cache.get_metrics()
        self.assertEqual(metrics['total_queries'], 1)
        self.assertEqual(metrics['cache_misses'], 1)
        self.assertEqual(metrics['cache_hits'], 0)

    def test_basic_set_get_operations(self):
        """Test basic set and get operations."""
        query = "What is AI?"
        context = "AI is artificial intelligence"
        response = "AI stands for Artificial Intelligence"

        # Set entry
        self.cache.set(query, context, response)
        self.assertEqual(len(self.cache), 1)

        # Get exact match
        result = self.cache.get(query, context)
        self.assertEqual(result, response)

        # Verify metrics
        metrics = self.cache.get_metrics()
        self.assertEqual(metrics['total_queries'], 1)
        self.assertEqual(metrics['cache_hits'], 1)
        self.assertEqual(metrics['cache_size'], 1)

    def test_semantic_similarity_matching(self):
        """Test semantic similarity-based cache hits."""
        # Set original entry
        self.cache.set("What is machine learning?", "ML is a subset of AI", "ML response")

        # Test similar queries that should hit
        similar_queries = [
            ("What is ML?", "Machine learning is part of AI"),
            ("Explain machine learning", "ML subset of artificial intelligence"),
            ("Tell me about ML", "Machine learning field")
        ]

        for query, context in similar_queries:
            result = self.cache.get(query, context)
            self.assertIsNotNone(result, f"Query '{query}' should hit cache")

    def test_dissimilar_queries_miss(self):
        """Test that dissimilar queries result in cache misses."""
        # Set AI-related entry
        self.cache.set("What is AI?", "AI context", "AI response")

        # Test dissimilar queries
        dissimilar_queries = [
            ("How to cook pasta?", "Cooking instructions"),
            ("Weather forecast", "Meteorology data"),
            ("Stock prices", "Financial data")
        ]

        for query, context in dissimilar_queries:
            result = self.cache.get(query, context)
            self.assertIsNone(result, f"Dissimilar query '{query}' should miss cache")

    def test_similarity_threshold_edge_cases(self):
        """Test similarity threshold edge cases."""
        # Threshold 0.0 - should match everything
        cache_low = CacheManager(max_size=10, similarity_threshold=0.0)
        cache_low.set("AI query", "AI context", "AI response")

        result = cache_low.get("Completely different query", "Unrelated context")
        self.assertIsNotNone(result)  # Should hit due to 0.0 threshold

        # Threshold 1.0 - should match nothing except exact
        cache_high = CacheManager(max_size=10, similarity_threshold=1.0)
        cache_high.set("Exact query", "Exact context", "Exact response")

        result = cache_high.get("Exact query", "Exact context")
        self.assertEqual(result, "Exact response")  # Exact match should work

        result = cache_high.get("Slightly different query", "Slightly different context")
        self.assertIsNone(result)  # Should miss

    def test_lru_eviction_policy(self):
        """Test LRU eviction policy."""
        cache = CacheManager(max_size=2, eviction_policy='LRU')

        # Use very different texts
        cache.set("What is the capital of France?", "France is in Europe", "Paris")
        cache.set("How to cook spaghetti?", "Spaghetti is pasta", "Boil water")
        cache.set("What is machine learning?", "ML is AI", "ML response")  # Should evict first query

        self.assertEqual(len(cache), 2)
        self.assertIsNone(cache.get("What is the capital of France?", "France is in Europe"))  # Evicted
        self.assertEqual(cache.get("How to cook spaghetti?", "Spaghetti is pasta"), "Boil water")
        self.assertEqual(cache.get("What is machine learning?", "ML is AI"), "ML response")

    def test_lfu_eviction_policy(self):
        """Test LFU eviction policy."""
        cache = CacheManager(max_size=2, eviction_policy='LFU')

        # Use very different texts to avoid semantic similarity
        cache.set("What is the capital of France?", "France is in Europe", "Paris")
        cache.set("How to cook spaghetti?", "Spaghetti is pasta", "Boil water")

        # Access first query multiple times
        cache.get("What is the capital of France?", "France is in Europe")
        cache.get("What is the capital of France?", "France is in Europe")
        cache.get("What is the capital of France?", "France is in Europe")  # 3 accesses

        cache.get("How to cook spaghetti?", "Spaghetti is pasta")  # 1 access

        # Add third query - should evict the least frequently used (spaghetti query)
        cache.set("What is machine learning?", "ML is AI", "ML response")

        self.assertEqual(len(cache), 2)
        self.assertIsNone(cache.get("How to cook spaghetti?", "Spaghetti is pasta"))  # Evicted
        self.assertEqual(cache.get("What is the capital of France?", "France is in Europe"), "Paris")
        self.assertEqual(cache.get("What is machine learning?", "ML is AI"), "ML response")

    def test_cache_clear(self):
        """Test cache clearing."""
        # Add some entries
        self.cache.set("Query 1", "Context 1", "Response 1")
        self.cache.set("Query 2", "Context 2", "Response 2")

        self.assertEqual(len(self.cache), 2)

        # Clear cache
        self.cache.clear()

        self.assertEqual(len(self.cache), 0)

        # After clear, metrics should be reset, but get() calls will increment them
        # So we check metrics before any get() calls
        metrics = self.cache.get_metrics()
        self.assertEqual(metrics['total_queries'], 0)
        self.assertEqual(metrics['cache_hits'], 0)
        self.assertEqual(metrics['cache_misses'], 0)

        # Now test that gets return None (and will increment metrics)
        self.assertIsNone(self.cache.get("Query 1", "Context 1"))
        self.assertIsNone(self.cache.get("Query 2", "Context 2"))

    def test_max_size_zero(self):
        """Test cache with max_size=0."""
        cache = CacheManager(max_size=0)

        # Should not store anything due to max_size=0
        cache.set("Query", "Context", "Response")
        # The cache should remain empty or not store the entry
        # (implementation may vary, but should not crash)

        result = cache.get("Query", "Context")
        self.assertIsNone(result)  # Should not find anything

    def test_access_count_tracking(self):
        """Test access count tracking."""
        self.cache.set("Query", "Context", "Response")

        # Initial access count should be 0
        entry = list(self.cache.cache.values())[0]
        self.assertEqual(entry.access_count, 0)

        # Get should increment access count
        self.cache.get("Query", "Context")
        entry = list(self.cache.cache.values())[0]
        self.assertEqual(entry.access_count, 1)

        # Another get should increment further
        self.cache.get("Query", "Context")
        entry = list(self.cache.cache.values())[0]
        self.assertEqual(entry.access_count, 2)

    def test_serialization_save_load(self):
        """Test cache serialization and deserialization."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as tmp:
            cache_file = tmp.name

        try:
            # Create and populate cache (without cache_file to avoid auto-loading)
            cache1 = CacheManager(max_size=10)
            cache1.set("Test query", "Test context", "Test response")
            cache1.set("Another query", "Another context", "Another response")

            # Save cache
            cache1.save_cache(cache_file)

            # Load in new instance
            cache2 = CacheManager(max_size=10)
            cache2.load_cache(cache_file)

            # Test that data was loaded
            self.assertEqual(len(cache2), 2)
            self.assertEqual(cache2.get("Test query", "Test context"), "Test response")
            self.assertEqual(cache2.get("Another query", "Another context"), "Another response")

            # Test configuration preservation
            self.assertEqual(cache2.model_name, cache1.model_name)
            self.assertEqual(cache2.similarity_threshold, cache1.similarity_threshold)
            self.assertEqual(cache2.max_size, cache1.max_size)

        finally:
            if os.path.exists(cache_file):
                os.unlink(cache_file)

    def test_serialization_no_file_specified(self):
        """Test serialization without file specified."""
        cache = CacheManager()

        with self.assertRaises(ValueError):
            cache.save_cache()

        with self.assertRaises(ValueError):
            cache.load_cache()

    def test_serialization_file_not_found(self):
        """Test loading non-existent cache file."""
        cache = CacheManager(cache_file='/nonexistent/file.pkl')
        # Should not raise error, just start empty
        self.assertEqual(len(cache), 0)

    def test_serialization_corrupt_file(self):
        """Test loading non-existent cache file."""
        cache = CacheManager()

        # Should not raise error for non-existent file
        cache.load_cache('/tmp/nonexistent.pkl')
        self.assertEqual(len(cache), 0)

    def test_metrics_comprehensive(self):
        """Test comprehensive metrics tracking."""
        # Use very different texts to avoid semantic similarity
        self.cache.set("What is the capital of France?", "France is a country in Europe", "Paris")
        self.cache.get("What is the capital of France?", "France is a country in Europe")  # Hit
        self.cache.get("How to cook spaghetti?", "Spaghetti is a type of pasta")  # Miss - different topic
        self.cache.get("What is machine learning?", "ML is a subset of AI")  # Miss - different topic

        metrics = self.cache.get_metrics()

        self.assertEqual(metrics['total_queries'], 3)
        self.assertEqual(metrics['cache_hits'], 1)
        self.assertEqual(metrics['cache_misses'], 2)
        self.assertEqual(metrics['hit_rate'], 1/3)
        self.assertEqual(metrics['cache_size'], 1)
        self.assertEqual(metrics['evictions'], 0)  # No evictions in this test

        # Check timing metrics exist
        self.assertIn('avg_similarity_search_time', metrics)
        self.assertIn('avg_embedding_time', metrics)

    def test_cache_entry_dataclass(self):
        """Test CacheEntry dataclass functionality."""
        import time
        timestamp = time.time()

        entry = CacheEntry(
            query="test query",
            context="test context",
            response="test response",
            embedding=np.array([0.1, 0.2, 0.3]),
            timestamp=timestamp,
            access_count=5,
            last_accessed=timestamp + 10
        )

        self.assertEqual(entry.query, "test query")
        self.assertEqual(entry.context, "test context")
        self.assertEqual(entry.response, "test response")
        self.assertTrue(np.array_equal(entry.embedding, np.array([0.1, 0.2, 0.3])))
        self.assertEqual(entry.timestamp, timestamp)
        self.assertEqual(entry.access_count, 5)
        self.assertEqual(entry.last_accessed, timestamp + 10)

    def test_embedding_computation(self):
        """Test embedding computation."""
        text = "This is a test text for embedding"
        embedding = self.cache._compute_embedding(text)

        self.assertIsInstance(embedding, np.ndarray)
        self.assertGreater(len(embedding), 0)  # Should have some dimensions

        # Check that metrics were updated
        self.assertGreater(self.cache.metrics['avg_embedding_time'], 0)

    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        emb1 = np.array([1.0, 0.0, 0.0])
        emb2 = np.array([0.0, 1.0, 0.0])
        emb3 = np.array([1.0, 1.0, 0.0])

        # Orthogonal vectors
        similarity = self.cache._cosine_similarity(emb1, emb2)
        self.assertAlmostEqual(similarity, 0.0, places=5)

        # Identical vectors
        similarity = self.cache._cosine_similarity(emb1, emb1)
        self.assertAlmostEqual(similarity, 1.0, places=5)

        # 45-degree angle
        similarity = self.cache._cosine_similarity(emb1, emb3)
        expected = 1.0 / np.sqrt(2)  # cos(45°) = 1/√2
        self.assertAlmostEqual(similarity, expected, places=5)

    def test_zero_length_embeddings(self):
        """Test cosine similarity with zero-length embeddings."""
        emb1 = np.array([0.0, 0.0, 0.0])
        emb2 = np.array([1.0, 1.0, 1.0])

        similarity = self.cache._cosine_similarity(emb1, emb2)
        self.assertEqual(similarity, 0.0)

    def test_large_cache_operations(self):
        """Test operations with larger cache sizes."""
        large_cache = CacheManager(max_size=100)

        # Add many entries
        for i in range(50):
            large_cache.set(f"Query {i}", f"Context {i}", f"Response {i}")

        self.assertEqual(len(large_cache), 50)

        # Test retrieval
        for i in range(50):
            result = large_cache.get(f"Query {i}", f"Context {i}")
            self.assertEqual(result, f"Response {i}")

    def test_unicode_support(self):
        """Test Unicode string support."""
        query = "Qué es la inteligencia artificial?"
        context = "La IA es una rama de la informática"
        response = "La IA significa Inteligencia Artificial"

        self.cache.set(query, context, response)
        result = self.cache.get(query, context)

        self.assertEqual(result, response)

    def test_empty_strings(self):
        """Test handling of empty strings."""
        # Empty query/context should still work
        self.cache.set("", "", "empty response")
        result = self.cache.get("", "")
        self.assertEqual(result, "empty response")

    def test_very_long_strings(self):
        """Test handling of very long strings."""
        long_text = "A" * 10000  # 10k character string
        self.cache.set(long_text, long_text, "long response")
        result = self.cache.get(long_text, long_text)
        self.assertEqual(result, "long response")


if __name__ == '__main__':
    unittest.main()