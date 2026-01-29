"""
Comprehensive tests for Cache Augmented RAG Implementation

Tests verify CacheAugmentedRAG functionality with mocks and real implementations.
"""

import unittest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from src.ailoos.rag.cache_augmented.cache_augmented_rag import CacheAugmentedRAG
from src.ailoos.rag.cache_augmented.cache_manager import CacheManager


class TestCacheAugmentedRAG(unittest.TestCase):
    """Test cases for CacheAugmentedRAG."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock base RAG class
        self.mock_base_rag_class = Mock()
        self.mock_base_rag_instance = Mock()
        self.mock_base_rag_class.return_value = self.mock_base_rag_instance

        # Mock base RAG methods
        self.mock_base_rag_instance.retrieve.return_value = [
            {'content': 'test document', 'score': 0.9}
        ]
        self.mock_base_rag_instance.generate.return_value = 'test response'
        self.mock_base_rag_instance.evaluate.return_value = {'accuracy': 0.8}

    def test_initialization_with_cache_enabled(self):
        """Test initialization with cache enabled."""
        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_config': {
                'model_name': 'all-MiniLM-L6-v2',
                'similarity_threshold': 0.8,
                'max_size': 100
            },
            'cache_enabled': True
        }

        rag = CacheAugmentedRAG(config)

        self.assertIsNotNone(rag.base_rag)
        self.assertIsNotNone(rag.cache_manager)
        self.assertTrue(rag.cache_enabled)
        self.assertEqual(rag.cache_manager.similarity_threshold, 0.8)
        self.assertEqual(rag.cache_manager.max_size, 100)

    def test_initialization_with_cache_disabled(self):
        """Test initialization with cache disabled."""
        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_enabled': False
        }

        rag = CacheAugmentedRAG(config)

        self.assertIsNotNone(rag.base_rag)
        self.assertIsNone(rag.cache_manager)
        self.assertFalse(rag.cache_enabled)

    def test_initialization_missing_base_rag_class(self):
        """Test initialization fails without base_rag_class."""
        config = {
            'base_rag_config': {},
            'cache_enabled': True
        }

        with self.assertRaises(ValueError):
            CacheAugmentedRAG(config)

    @patch('src.ailoos.rag.cache_augmented.cache_augmented_rag.time.time')
    def test_generate_cache_miss(self, mock_time):
        """Test generate method on cache miss."""
        mock_time.return_value = 1000.0

        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_enabled': True
        }

        rag = CacheAugmentedRAG(config)

        query = "test query"
        context = [{'content': 'test doc', 'score': 0.9}]

        response = rag.generate(query, context)

        # Should call base RAG generate
        self.mock_base_rag_instance.generate.assert_called_once_with(query, context)

        # Should cache the response (cache should not be empty after set)
        self.assertGreater(len(rag.cache_manager.cache), 0)

        # Check metrics
        self.assertEqual(rag.cache_metrics['total_queries'], 1)
        self.assertEqual(rag.cache_metrics['cache_misses'], 1)
        self.assertEqual(rag.cache_metrics['cache_hits'], 0)

    def test_retrieve_delegates_to_base_rag(self):
        """Test retrieve method delegates to base RAG."""
        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_enabled': True
        }

        rag = CacheAugmentedRAG(config)

        query = "test query"
        result = rag.retrieve(query, top_k=5)

        self.mock_base_rag_instance.retrieve.assert_called_once_with(query, top_k=5, filters=None)
        self.assertEqual(result, [{'content': 'test document', 'score': 0.9}])

    def test_evaluate_delegates_to_base_rag(self):
        """Test evaluate method delegates to base RAG."""
        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_enabled': True
        }

        rag = CacheAugmentedRAG(config)

        metrics = rag.evaluate("query", "response", "ground_truth", [])

        self.mock_base_rag_instance.evaluate.assert_called_once_with(
            "query", "response", "ground_truth", []
        )
        self.assertEqual(metrics, {'accuracy': 0.8})

    def test_get_cache_metrics(self):
        """Test getting cache metrics."""
        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_enabled': True
        }

        rag = CacheAugmentedRAG(config)

        metrics = rag.get_cache_metrics()

        expected_keys = [
            'cache_hits', 'cache_misses', 'total_queries',
            'cache_hit_rate', 'avg_cache_lookup_time', 'total_cache_lookup_time',
            'cache_manager_metrics'
        ]

        for key in expected_keys:
            self.assertIn(key, metrics)

    def test_clear_cache(self):
        """Test clearing cache."""
        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_enabled': True
        }

        rag = CacheAugmentedRAG(config)

        # Simulate some metrics
        rag.cache_metrics['total_queries'] = 10
        rag.cache_metrics['cache_hits'] = 7

        rag.clear_cache()

        self.assertEqual(rag.cache_metrics['total_queries'], 0)
        self.assertEqual(rag.cache_metrics['cache_hits'], 0)

    def test_context_to_string(self):
        """Test context to string conversion."""
        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_enabled': True
        }

        rag = CacheAugmentedRAG(config)

        context = [
            {'content': 'doc1', 'score': 0.9, 'metadata': {'title': 'Title1'}},
            {'content': 'doc2', 'score': 0.8, 'metadata': {'title': 'Title2'}}
        ]

        result = rag._context_to_string(context)

        # Should contain both documents in sorted order
        self.assertIn('Title1', result)
        self.assertIn('Title2', result)
        self.assertIn('doc1', result)
        self.assertIn('doc2', result)

    def test_generate_cache_hit(self):
        """Test generate method on cache hit."""
        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_enabled': True
        }

        rag = CacheAugmentedRAG(config)

        query = "test query"
        context = [{'content': 'test doc', 'score': 0.9}]

        # First call - cache miss
        response1 = rag.generate(query, context)
        self.assertEqual(response1, 'test response')
        self.assertEqual(rag.cache_metrics['cache_misses'], 1)
        self.assertEqual(rag.cache_metrics['cache_hits'], 0)

        # Second call with same query/context - should be cache hit
        response2 = rag.generate(query, context)
        self.assertEqual(response2, 'test response')  # Same response from cache

        # Base RAG generate should only be called once
        self.assertEqual(self.mock_base_rag_instance.generate.call_count, 1)

        # Check metrics
        self.assertEqual(rag.cache_metrics['total_queries'], 2)
        self.assertEqual(rag.cache_metrics['cache_hits'], 1)
        self.assertEqual(rag.cache_metrics['cache_misses'], 1)

    def test_generate_cache_disabled(self):
        """Test generate method with cache disabled."""
        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_enabled': False
        }

        rag = CacheAugmentedRAG(config)

        query = "test query"
        context = [{'content': 'test doc', 'score': 0.9}]

        response = rag.generate(query, context)

        # Should call base RAG directly
        self.mock_base_rag_instance.generate.assert_called_once_with(query, context)
        self.assertEqual(response, 'test response')

        # Cache should be None
        self.assertIsNone(rag.cache_manager)

    def test_run_method_integration(self):
        """Test the complete run method."""
        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_enabled': True
        }

        rag = CacheAugmentedRAG(config)

        result = rag.run("test query", top_k=5)

        expected_keys = ['query', 'context', 'response', 'metrics', 'metadata']
        for key in expected_keys:
            self.assertIn(key, result)

        self.assertEqual(result['query'], "test query")
        self.assertEqual(result['response'], 'test response')
        self.assertEqual(result['context'], [{'content': 'test document', 'score': 0.9}])
        self.assertEqual(result['metrics'], {'accuracy': 0.8})

        # Check metadata
        self.assertIn('rag_type', result['metadata'])
        self.assertIn('base_rag_type', result['metadata'])
        self.assertIn('cache_enabled', result['metadata'])
        self.assertIn('cache_metrics', result['metadata'])

    def test_cache_metrics_calculation(self):
        """Test cache metrics calculation."""
        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_enabled': True
        }

        rag = CacheAugmentedRAG(config)

        # Simulate some cache activity
        rag.cache_metrics['total_queries'] = 10
        rag.cache_metrics['cache_hits'] = 7
        rag.cache_metrics['cache_misses'] = 3
        rag.cache_metrics['total_cache_lookup_time'] = 5.0

        # Update derived metrics
        rag._update_cache_metrics()

        metrics = rag.get_cache_metrics()

        self.assertEqual(metrics['cache_hit_rate'], 0.7)
        self.assertEqual(metrics['avg_cache_lookup_time'], 5.0 / 10)

    def test_save_load_cache(self):
        """Test saving and loading cache state."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as tmp:
            cache_file = tmp.name

        try:
            config = {
                'base_rag_class': self.mock_base_rag_class,
                'base_rag_config': {},
                'cache_enabled': True
            }

            rag = CacheAugmentedRAG(config)

            # Generate some cache entries
            rag.generate("query1", [{'content': 'doc1', 'score': 0.9}])
            rag.generate("query2", [{'content': 'doc2', 'score': 0.8}])

            # Save cache
            rag.save_cache(cache_file)

            # Create new instance and load
            rag2 = CacheAugmentedRAG(config)
            rag2.load_cache(cache_file)

            # Check that cache was loaded
            self.assertGreater(len(rag2.cache_manager), 0)

        finally:
            if os.path.exists(cache_file):
                os.unlink(cache_file)

    def test_get_pipeline_info(self):
        """Test getting pipeline information."""
        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {'test_param': 'value'},
            'cache_config': {
                'model_name': 'all-MiniLM-L6-v2',
                'similarity_threshold': 0.8,
                'max_size': 100
            },
            'cache_enabled': True
        }

        rag = CacheAugmentedRAG(config)

        info = rag.get_pipeline_info()

        self.assertEqual(info['technique'], 'CacheAugmentedRAG')
        self.assertEqual(info['cache_enabled'], True)
        self.assertIn('cache_config', info)
        self.assertIn('cache_metrics', info)
        self.assertIn('config', info)

    def test_context_to_string_edge_cases(self):
        """Test context to string conversion with edge cases."""
        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_enabled': True
        }

        rag = CacheAugmentedRAG(config)

        # Empty context
        result = rag._context_to_string([])
        self.assertEqual(result, "")

        # Context without metadata
        context = [{'content': 'doc1', 'score': 0.9}]
        result = rag._context_to_string(context)
        self.assertIn('doc1', result)
        self.assertIn('0.9000', result)

        # Context with missing fields
        context = [{'content': 'doc1'}]
        result = rag._context_to_string(context)
        self.assertIn('doc1', result)

    def test_cache_semantic_similarity(self):
        """Test that cache uses semantic similarity correctly."""
        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_config': {'similarity_threshold': 0.5},  # Lower threshold
            'cache_enabled': True
        }

        rag = CacheAugmentedRAG(config)

        # Set up base RAG to return different responses
        self.mock_base_rag_instance.generate.side_effect = ['response1', 'response2']

        # First query
        response1 = rag.generate("What is AI?", [{'content': 'AI is artificial intelligence'}])

        # Similar query should hit cache
        response2 = rag.generate("What does AI mean?", [{'content': 'Artificial intelligence explained'}])

        # Should be the same response (from cache)
        self.assertEqual(response1, response2)

        # Base RAG should only be called once
        self.assertEqual(self.mock_base_rag_instance.generate.call_count, 1)

    def test_cache_different_contexts(self):
        """Test that different contexts don't hit cache."""
        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_enabled': True
        }

        rag = CacheAugmentedRAG(config)

        # Set up base RAG to return different responses
        self.mock_base_rag_instance.generate.side_effect = ['response1', 'response2']

        # Same query, very different contexts
        response1 = rag.generate("What is AI?", [{'content': 'Artificial intelligence is a field of computer science'}])
        response2 = rag.generate("What is AI?", [{'content': 'Cooking pasta requires boiling water first'}])

        # Should be different responses (different contexts should not cache)
        self.assertNotEqual(response1, response2)

        # Base RAG should be called twice
        self.assertEqual(self.mock_base_rag_instance.generate.call_count, 2)

    def test_error_handling_in_run(self):
        """Test error handling in run method."""
        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_enabled': True
        }

        rag = CacheAugmentedRAG(config)

        # Make retrieve raise an exception
        self.mock_base_rag_instance.retrieve.side_effect = Exception("Retrieval error")

        with self.assertRaises(Exception):
            rag.run("test query")

    def test_cache_performance_metrics(self):
        """Test cache performance metrics tracking."""
        config = {
            'base_rag_class': self.mock_base_rag_class,
            'base_rag_config': {},
            'cache_enabled': True
        }

        rag = CacheAugmentedRAG(config)

        # Perform several operations (all misses initially)
        for i in range(5):
            rag.generate(f"query {i}", [{'content': f'doc {i}'}])

        # Check that we have cache misses
        self.assertEqual(rag.cache_metrics['cache_misses'], 5)
        self.assertEqual(rag.cache_metrics['total_queries'], 5)

        # Hit cache (same queries/contexts)
        for i in range(3):
            rag.generate(f"query {i}", [{'content': f'doc {i}'}])

        # Check hits
        self.assertEqual(rag.cache_metrics['cache_hits'], 3)
        self.assertEqual(rag.cache_metrics['total_queries'], 8)


if __name__ == '__main__':
    unittest.main()