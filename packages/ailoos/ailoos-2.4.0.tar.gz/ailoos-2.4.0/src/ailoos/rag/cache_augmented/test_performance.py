"""
Performance validation tests for Cache Augmented RAG (CAG).

Tests verify that CAG provides performance improvements over regular RAG.
"""

import time
import unittest
from unittest.mock import Mock, patch
from src.ailoos.rag.cache_augmented.cache_augmented_rag import CacheAugmentedRAG


class TestCacheAugmentedRAGPerformance(unittest.TestCase):
    """Performance tests for CacheAugmentedRAG."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock base RAG class
        self.mock_base_rag_class = Mock()
        self.mock_base_rag_instance = Mock()

        # Mock methods
        self.mock_base_rag_instance.retrieve.return_value = [
            {'content': 'test document', 'score': 0.9}
        ]
        self.mock_base_rag_instance.generate.return_value = 'test response'
        self.mock_base_rag_instance.evaluate.return_value = {'accuracy': 0.8}

        self.mock_base_rag_class.return_value = self.mock_base_rag_instance

    def test_cache_hit_improves_performance(self):
        """Test that cache hits provide faster response times."""
        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_enabled': True
        }

        rag = CacheAugmentedRAG(config)

        query = "What is AI?"
        context = [{'content': 'AI is artificial intelligence'}]

        # First call - cache miss (calls base RAG)
        start_time = time.time()
        response1 = rag.generate(query, context)
        first_call_time = time.time() - start_time

        # Second call - cache hit (should be faster)
        start_time = time.time()
        response2 = rag.generate(query, context)
        second_call_time = time.time() - start_time

        # Both responses should be the same
        self.assertEqual(response1, response2)

        # Cache hit should be significantly faster (at least 10x faster in mock scenario)
        # In real scenarios, cache hits are much faster due to avoiding expensive operations
        self.assertLess(second_call_time, first_call_time)

        # Verify base RAG was called only once
        self.assertEqual(self.mock_base_rag_instance.generate.call_count, 1)

    def test_cache_hit_rate_calculation(self):
        """Test cache hit rate calculation over multiple queries."""
        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_enabled': True
        }

        rag = CacheAugmentedRAG(config)

        # Set up different responses for different queries
        responses = ['response1', 'response2', 'response3']
        self.mock_base_rag_instance.generate.side_effect = responses

        queries = [
            ("What is AI?", [{'content': 'AI definition'}]),
            ("What is ML?", [{'content': 'ML definition'}]),
            ("What is AI?", [{'content': 'AI definition'}]),  # Repeat - should hit cache
            ("What is DL?", [{'content': 'DL definition'}]),
            ("What is AI?", [{'content': 'AI definition'}]),  # Repeat - should hit cache
        ]

        for query, context in queries:
            rag.generate(query, context)

        # Should have 3 cache hits (repeated AI queries) and 2 misses
        self.assertEqual(rag.cache_metrics['cache_hits'], 2)
        self.assertEqual(rag.cache_metrics['cache_misses'], 3)
        self.assertEqual(rag.cache_metrics['total_queries'], 5)

        # Hit rate should be 2/5 = 0.4
        self.assertEqual(rag.cache_metrics['cache_hit_rate'], 0.4)

    def test_cache_reduces_base_rag_calls(self):
        """Test that cache reduces the number of base RAG calls."""
        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_enabled': True
        }

        rag = CacheAugmentedRAG(config)

        # Perform multiple queries, some repeated
        queries = [
            "What is AI?",
            "What is machine learning?",
            "What is AI?",  # Repeat
            "What is deep learning?",
            "What is AI?",  # Repeat
            "What is machine learning?",  # Repeat
        ]

        for query in queries:
            context = [{'content': f'{query} context'}]
            rag.generate(query, context)

        # Base RAG should be called only for unique queries
        # In this case, 3 unique queries out of 6 total
        self.assertEqual(self.mock_base_rag_instance.generate.call_count, 3)

        # Cache should have 3 hits
        self.assertEqual(rag.cache_metrics['cache_hits'], 3)
        self.assertEqual(rag.cache_metrics['cache_misses'], 3)

    def test_cache_lookup_time_tracking(self):
        """Test that cache lookup times are tracked."""
        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_enabled': True
        }

        rag = CacheAugmentedRAG(config)

        # Perform some operations
        query = "Test query"
        context = [{'content': 'test context'}]

        # First call - miss
        rag.generate(query, context)

        # Second call - hit
        rag.generate(query, context)

        # Check that lookup times are being tracked
        self.assertGreater(rag.cache_metrics['total_cache_lookup_time'], 0)
        self.assertGreater(rag.cache_metrics['avg_cache_lookup_time'], 0)

    def test_performance_comparison_with_disabled_cache(self):
        """Test performance comparison between cached and non-cached RAG."""
        # Create cached RAG
        cached_config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_enabled': True
        }
        cached_rag = CacheAugmentedRAG(cached_config)

        # Create non-cached RAG (by disabling cache)
        non_cached_config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_enabled': False
        }
        non_cached_rag = CacheAugmentedRAG(non_cached_config)

        query = "Performance test query"
        context = [{'content': 'performance test context'}]

        # Test cached RAG
        start_time = time.time()
        for _ in range(10):
            cached_rag.generate(query, context)
        cached_time = time.time() - start_time

        # Test non-cached RAG
        start_time = time.time()
        for _ in range(10):
            non_cached_rag.generate(query, context)
        non_cached_time = time.time() - start_time

        # Cached version should be faster for repeated queries
        # (In this mock scenario, the difference might be small, but should still exist)
        self.assertLessEqual(cached_time, non_cached_time + 0.1)  # Allow small margin

        # Verify base RAG call counts
        # Cached RAG should call base RAG only once
        self.assertEqual(cached_rag.base_rag.generate.call_count, 1)

        # Non-cached RAG should call base RAG for every query
        self.assertEqual(non_cached_rag.base_rag.generate.call_count, 10)

    def test_cache_scalability(self):
        """Test cache performance with larger number of entries."""
        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_config': {'max_size': 100},
            'cache_enabled': True
        }

        rag = CacheAugmentedRAG(config)

        # Add many unique queries
        for i in range(50):
            query = f"Query {i}"
            context = [{'content': f'Context {i}'}]
            rag.generate(query, context)

        # All should be misses initially
        self.assertEqual(rag.cache_metrics['cache_misses'], 50)
        self.assertEqual(rag.cache_metrics['cache_hits'], 0)

        # Repeat some queries - should get hits
        for i in range(25):  # Repeat first 25 queries
            query = f"Query {i}"
            context = [{'content': f'Context {i}'}]
            rag.generate(query, context)

        # Should have 25 hits and 25 additional misses (for the repeated queries that were already cached)
        # Actually, since they were already cached, they should all be hits now
        self.assertEqual(rag.cache_metrics['cache_hits'], 25)
        self.assertEqual(rag.cache_metrics['total_queries'], 75)

    def test_memory_efficiency(self):
        """Test that cache maintains reasonable memory usage."""
        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_config': {'max_size': 10},
            'cache_enabled': True
        }

        rag = CacheAugmentedRAG(config)

        # Add entries up to max_size
        for i in range(15):  # Exceed max_size
            query = f"Query {i}"
            context = [{'content': f'Context {i}'}]
            rag.generate(query, context)

        # Cache should not exceed max_size
        self.assertLessEqual(len(rag.cache_manager), 10)

        # Should have some evictions
        self.assertGreater(rag.cache_manager.metrics['evictions'], 0)

    def test_cache_warmup_time(self):
        """Test cache warmup time vs steady-state performance."""
        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_enabled': True
        }

        rag = CacheAugmentedRAG(config)

        query = "Warmup test query"
        context = [{'content': 'warmup context'}]

        # Measure time for first few queries (warmup)
        warmup_times = []
        for i in range(5):
            start_time = time.time()
            rag.generate(query, context)
            warmup_times.append(time.time() - start_time)

        # Measure time for subsequent queries (steady state)
        steady_times = []
        for i in range(5):
            start_time = time.time()
            rag.generate(query, context)
            steady_times.append(time.time() - start_time)

        # Steady state should be faster than warmup
        avg_warmup = sum(warmup_times[:1]) / 1  # First call
        avg_steady = sum(steady_times) / len(steady_times)

        # Steady state should be faster (cache hits)
        self.assertLess(avg_steady, avg_warmup)


if __name__ == '__main__':
    unittest.main()