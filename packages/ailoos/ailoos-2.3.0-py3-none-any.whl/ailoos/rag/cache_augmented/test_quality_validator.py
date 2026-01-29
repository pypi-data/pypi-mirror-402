"""
Tests for CAG Quality Validator

Comprehensive tests for the Cache Augmented RAG quality validation system.
"""

import unittest
import time
from unittest.mock import Mock, patch
import numpy as np

from .quality_validator import CAGQualityValidator


class TestCAGQualityValidator(unittest.TestCase):
    """Test cases for CAG Quality Validator."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'similarity_model': 'all-MiniLM-L6-v2',
            'consistency_threshold': 0.8,
            'factual_validation_enabled': True,
            'cache_comparison_enabled': True,
            'max_consistency_samples': 5
        }
        self.validator = CAGQualityValidator(self.config)

    def test_initialization(self):
        """Test validator initialization."""
        self.assertIsInstance(self.validator, CAGQualityValidator)
        self.assertEqual(self.validator.similarity_model_name, 'all-MiniLM-L6-v2')
        self.assertEqual(self.validator.consistency_threshold, 0.8)
        self.assertTrue(self.validator.factual_validation_enabled)
        self.assertTrue(self.validator.cache_comparison_enabled)

    def test_evaluate_base_metrics(self):
        """Test base metrics evaluation."""
        query = "What is machine learning?"
        response = "Machine learning is a subset of artificial intelligence."
        ground_truth = "Machine learning is a type of AI that learns from data."
        context = [{"content": "Machine learning uses algorithms to learn patterns."}]

        metrics = self.validator.evaluate(query, response, ground_truth, context)

        # Check that base metrics are present
        self.assertIn('relevance', metrics)
        self.assertIn('faithfulness', metrics)
        self.assertIn('informativeness', metrics)
        self.assertIn('cag_overall_score', metrics)

        # Check ranges
        for metric_name, value in metrics.items():
            if metric_name != 'error':
                self.assertGreaterEqual(value, 0.0)
                self.assertLessEqual(value, 1.0)

    def test_evaluate_cache_quality(self):
        """Test cache quality evaluation."""
        response = "This is a cached response."
        cache_metadata = {
            'cache_hit': True,
            'cache_timestamp': time.time() - 3600,  # 1 hour ago
            'cache_similarity': 0.9,
            'original_length': 5
        }

        metrics = self.validator.evaluate("test query", response, cache_metadata=cache_metadata)

        self.assertIn('cache_hit', metrics)
        self.assertIn('cache_freshness', metrics)
        self.assertIn('cache_confidence', metrics)
        self.assertIn('cache_length_consistency', metrics)

        self.assertEqual(metrics['cache_hit'], 1.0)
        self.assertGreater(metrics['cache_freshness'], 0.0)
        self.assertLess(metrics['cache_freshness'], 1.0)
        self.assertEqual(metrics['cache_confidence'], 0.9)

    def test_evaluate_consistency(self):
        """Test consistency evaluation."""
        query = "What is AI?"

        # First response
        response1 = "Artificial Intelligence is a field of computer science."
        metrics1 = self.validator.evaluate(query, response1)

        # Second similar response
        response2 = "AI refers to artificial intelligence in computing."
        metrics2 = self.validator.evaluate(query, response2)

        # Third different response
        response3 = "Machine learning is different from AI."
        metrics3 = self.validator.evaluate(query, response3)

        # Check consistency metrics are present
        self.assertIn('consistency_score', metrics1)
        self.assertIn('consistency_score', metrics2)
        self.assertIn('consistency_score', metrics3)

        # First response should have perfect consistency (only one)
        self.assertEqual(metrics1['consistency_score'], 1.0)

        # Later responses should have consistency scores
        self.assertGreaterEqual(metrics2['consistency_score'], 0.0)
        self.assertLessEqual(metrics2['consistency_score'], 1.0)

    def test_evaluate_factual_accuracy(self):
        """Test factual accuracy evaluation."""
        response = "Paris is the capital of France."
        ground_truth = "Paris is the capital of France."
        context = [{"content": "Paris is the capital and largest city of France."}]

        metrics = self.validator.evaluate("What is the capital of France?", response, ground_truth, context)

        self.assertIn('factual_exact_match', metrics)
        self.assertIn('factual_f1_score', metrics)
        self.assertIn('factual_semantic_similarity', metrics)
        self.assertIn('factual_context_support', metrics)

        # Exact match should be 1.0
        self.assertEqual(metrics['factual_exact_match'], 1.0)
        self.assertEqual(metrics['factual_f1_score'], 1.0)

    def test_evaluate_cache_vs_fresh(self):
        """Test cache vs fresh response comparison."""
        cached_response = "This is a cached response about AI."
        fresh_response = "This is a fresh response about artificial intelligence."

        cache_metadata = {
            'fresh_response': fresh_response,
            'cache_hit': True
        }

        metrics = self.validator.evaluate("What is AI?", cached_response, cache_metadata=cache_metadata)

        self.assertIn('cache_fresh_similarity', metrics)
        self.assertIn('cache_fresh_length_diff', metrics)
        self.assertIn('cache_fresh_word_overlap', metrics)
        self.assertIn('cache_degradation_score', metrics)

        # Check ranges
        self.assertGreaterEqual(metrics['cache_fresh_similarity'], 0.0)
        self.assertLessEqual(metrics['cache_fresh_similarity'], 1.0)
        self.assertGreaterEqual(metrics['cache_degradation_score'], 0.0)
        self.assertLessEqual(metrics['cache_degradation_score'], 1.0)

    def test_overall_score_calculation(self):
        """Test overall CAG score calculation."""
        query = "What is machine learning?"
        response = "Machine learning is a method of data analysis."
        ground_truth = "Machine learning is a type of AI that learns from data."

        metrics = self.validator.evaluate(query, response, ground_truth)

        self.assertIn('cag_overall_score', metrics)
        self.assertGreaterEqual(metrics['cag_overall_score'], 0.0)
        self.assertLessEqual(metrics['cag_overall_score'], 1.0)

    def test_error_handling(self):
        """Test error handling in evaluation."""
        # Test with invalid inputs - should still return valid metrics
        metrics = self.validator.evaluate("", "", None, None)

        # Should not have 'error' key since errors are handled gracefully
        self.assertNotIn('error', metrics)
        self.assertIn('cag_overall_score', metrics)
        self.assertIn('relevance', metrics)
        self.assertIn('consistency_score', metrics)

    def test_consistency_history_management(self):
        """Test consistency history management."""
        # Reset history
        self.validator.reset_consistency_history()

        stats = self.validator.get_consistency_stats()
        self.assertEqual(stats['total_queries_tracked'], 0)
        self.assertEqual(stats['total_responses_stored'], 0)

        # Add some responses
        queries_responses = [
            ("What is AI?", "Artificial Intelligence"),
            ("What is AI?", "AI stands for Artificial Intelligence"),
            ("What is ML?", "Machine Learning"),
        ]

        for query, response in queries_responses:
            self.validator.evaluate(query, response)

        stats = self.validator.get_consistency_stats()
        self.assertGreater(stats['total_queries_tracked'], 0)
        self.assertGreater(stats['total_responses_stored'], 0)

    def test_cache_freshness_calculation(self):
        """Test cache freshness calculation."""
        response = "Test response"

        # Very fresh cache (just created)
        recent_metadata = {
            'cache_hit': True,
            'cache_timestamp': time.time() - 60,  # 1 minute ago
        }

        # Older cache
        old_metadata = {
            'cache_hit': True,
            'cache_timestamp': time.time() - 86400,  # 1 day ago
        }

        recent_metrics = self.validator.evaluate("test", response, cache_metadata=recent_metadata)
        old_metrics = self.validator.evaluate("test", response, cache_metadata=old_metadata)

        # Recent should be fresher than old
        self.assertGreater(recent_metrics['cache_freshness'], old_metrics['cache_freshness'])

    @patch('sentence_transformers.SentenceTransformer')
    def test_similarity_model_failure(self, mock_model):
        """Test handling of similarity model failures."""
        # Mock model to raise exception
        mock_model.side_effect = Exception("Model loading failed")

        # Should still work with basic metrics
        metrics = self.validator.evaluate("query", "response")

        self.assertIn('cag_overall_score', metrics)
        # Should have some default values for similarity-based metrics
        self.assertIn('consistency_score', metrics)

    def test_context_support_evaluation(self):
        """Test context support evaluation."""
        response = "Paris is the capital."
        ground_truth = "Paris is the capital of France."
        context = [
            {"content": "Paris is the capital city of France."},
            {"content": "France is a country in Europe."}
        ]

        metrics = self.validator.evaluate("Capital of France?", response, ground_truth, context)

        self.assertIn('factual_context_support', metrics)
        self.assertGreaterEqual(metrics['factual_context_support'], 0.0)
        self.assertLessEqual(metrics['factual_context_support'], 1.0)

    def test_max_consistency_samples(self):
        """Test that consistency tracking respects max samples limit."""
        query = "Test query"

        # Add more responses than max_consistency_samples
        for i in range(self.validator.max_consistency_samples + 3):
            response = f"Response number {i}"
            self.validator.evaluate(query, response)

        # Check that we don't exceed max samples
        query_key = self.validator._normalize_query(query)
        self.assertLessEqual(len(self.validator.response_embeddings[query_key]),
                           self.validator.max_consistency_samples)


if __name__ == '__main__':
    unittest.main()