"""
Unit Tests for Corrective RAG Implementation

This module contains comprehensive unit tests for the CorrectiveRAG class,
testing iterative correction loops, confidence-based adjustments, and correction
metrics functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time

from ..techniques.corrective_rag import CorrectiveRAG
from ..core.retrievers import VectorRetriever
from ..core.generators import MockGenerator
from ..core.evaluators import BasicRAGEvaluator


class TestCorrectiveRAG(unittest.TestCase):
    """Test cases for CorrectiveRAG functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'retriever_config': {'chunk_size': 500, 'chunk_overlap': 50},
            'generator_config': {'use_mock': True},
            'evaluator_config': {},
            'correction_config': {
                'max_iterations': 3,
                'confidence_threshold': 0.7,
                'relevance_threshold': 0.5,
                'factuality_threshold': 0.6,
                'adaptive_retrieval': True
            }
        }

        # Mock components
        self.mock_retriever = Mock(spec=VectorRetriever)
        self.mock_generator = Mock(spec=MockGenerator)
        self.mock_evaluator = Mock(spec=BasicRAGEvaluator)

        # Sample data
        self.sample_documents = [
            {
                'content': 'AI is a field of computer science.',
                'metadata': {'source': 'test'},
                'score': 0.8
            },
            {
                'content': 'Machine learning is part of AI.',
                'metadata': {'source': 'test'},
                'score': 0.6
            }
        ]

        self.query = "What is artificial intelligence?"

    def _create_corrective_rag(self):
        """Create a CorrectiveRAG instance with mocked components."""
        rag = CorrectiveRAG(self.config)
        rag.retriever = self.mock_retriever
        rag.generator = self.mock_generator
        rag.evaluator = self.mock_evaluator
        return rag

    def test_initialization(self):
        """Test CorrectiveRAG initialization."""
        rag = self._create_corrective_rag()

        self.assertIsInstance(rag, CorrectiveRAG)
        self.assertEqual(rag.correction_config['max_iterations'], 3)
        self.assertEqual(rag.correction_config['confidence_threshold'], 0.7)
        self.assertIsNotNone(rag.correction_metrics)

    def test_retrieve_with_corrections(self):
        """Test retrieval with correction mechanisms."""
        rag = self._create_corrective_rag()

        # Mock retriever to return documents
        self.mock_retriever.search.return_value = [
            (self.sample_documents[0], 0.8),
            (self.sample_documents[1], 0.4)  # Below threshold
        ]

        result = rag.retrieve(self.query, top_k=5)

        # Should apply corrections and filter low-scoring documents
        self.assertIsInstance(result, list)
        self.mock_retriever.search.assert_called_once_with(self.query, top_k=5, filters=None)

    def test_apply_corrections_filters_low_quality(self):
        """Test that corrections filter out low-quality documents."""
        rag = self._create_corrective_rag()

        documents = [
            {'content': 'High quality content', 'score': 0.9},
            {'content': 'Low quality content', 'score': 0.3},  # Below threshold
            {'content': 'Medium quality content', 'score': 0.6}
        ]

        corrected = rag._apply_corrections(self.query, documents)

        # Should filter out the low-quality document
        self.assertEqual(len(corrected), 2)
        self.assertTrue(all(doc['score'] >= 0.5 for doc in corrected))

    def test_passes_correction_checks(self):
        """Test document correction checks."""
        rag = self._create_corrective_rag()

        # Test passing document
        good_doc = {
            'content': 'This is a comprehensive explanation of AI with specific details.',
            'score': 0.8
        }
        passes, reasons = rag._passes_correction_checks(good_doc, self.query)
        self.assertTrue(passes)
        self.assertEqual(len(reasons), 0)

        # Test failing document
        bad_doc = {
            'content': 'AI',  # Too short
            'score': 0.2  # Low score
        }
        passes, reasons = rag._passes_correction_checks(bad_doc, self.query)
        self.assertFalse(passes)
        self.assertGreater(len(reasons), 0)

    def test_iterative_correction_loop(self):
        """Test the iterative correction loop in run method."""
        rag = self._create_corrective_rag()

        # Mock initial calls
        self.mock_retriever.search.return_value = [(self.sample_documents[0], 0.8)]
        self.mock_generator.generate.return_value = "AI is artificial intelligence."
        self.mock_evaluator.evaluate.return_value = {
            'overall_score': 0.5,  # Below threshold, should trigger correction
            'relevance': 0.6,
            'faithfulness': 0.7
        }

        result = rag.run(self.query)

        # Should have performed corrections
        self.assertIn('correction_history', result['metadata'])
        self.assertGreaterEqual(result['metadata']['total_iterations'], 1)

    def test_confidence_based_correction_decision(self):
        """Test that corrections are applied based on confidence levels."""
        rag = self._create_corrective_rag()

        # Mock low confidence scenario
        self.mock_retriever.search.return_value = [(self.sample_documents[0], 0.8)]
        self.mock_generator.generate.return_value = "AI is technology."
        self.mock_evaluator.evaluate.return_value = {
            'overall_score': 0.8,  # Above threshold, should not need correction
            'relevance': 0.9,
            'faithfulness': 0.8
        }

        result = rag.run(self.query)

        # Should complete in single iteration
        self.assertEqual(result['metadata']['total_iterations'], 0)

    def test_adaptive_retrieval(self):
        """Test adaptive retrieval when confidence is low."""
        rag = self._create_corrective_rag()

        # Mock low confidence and adaptive retrieval
        self.mock_retriever.search.side_effect = [
            [(self.sample_documents[0], 0.8)],  # Initial retrieval
            [(self.sample_documents[0], 0.8), (self.sample_documents[1], 0.7)]  # Additional retrieval
        ]
        self.mock_generator.generate.return_value = "AI explanation."
        self.mock_evaluator.evaluate.side_effect = [
            {'overall_score': 0.4, 'faithfulness': 0.5},  # Low confidence
            {'overall_score': 0.8, 'faithfulness': 0.9}   # Improved after correction
        ]

        result = rag.run(self.query)

        # Should have performed adaptive retrieval
        self.assertGreater(result['metadata']['correction_metrics']['retrieval_adjustments'], 0)

    def test_correction_metrics_tracking(self):
        """Test that correction metrics are properly tracked."""
        rag = self._create_corrective_rag()

        # Perform some operations
        self.mock_retriever.search.return_value = [(self.sample_documents[0], 0.8)]
        self.mock_generator.generate.return_value = "Response"
        self.mock_evaluator.evaluate.return_value = {'overall_score': 0.5}

        rag.run(self.query)

        metrics = rag.get_correction_metrics()
        self.assertIsInstance(metrics, dict)
        self.assertIn('iterations_performed', metrics)
        self.assertIn('corrections_applied', metrics)

    def test_pipeline_info_includes_correction_config(self):
        """Test that pipeline info includes correction configuration."""
        rag = self._create_corrective_rag()

        info = rag.get_pipeline_info()

        self.assertEqual(info['technique'], 'CorrectiveRAG')
        self.assertIn('correction_config', info)
        self.assertIn('correction_metrics', info)

    def test_error_handling_in_correction_loop(self):
        """Test error handling during correction iterations."""
        rag = self._create_corrective_rag()

        # Mock retriever to raise exception during adaptive retrieval
        self.mock_retriever.search.side_effect = Exception("Retrieval error")
        self.mock_generator.generate.return_value = "Response"
        self.mock_evaluator.evaluate.return_value = {'overall_score': 0.5}

        # Should not crash, should fall back gracefully
        result = rag.run(self.query)
        self.assertIn('response', result)

    def test_max_iterations_limit(self):
        """Test that correction loop respects max iterations limit."""
        rag = self._create_corrective_rag()
        rag.correction_config['max_iterations'] = 2

        # Mock persistent low confidence
        self.mock_retriever.search.return_value = [(self.sample_documents[0], 0.8)]
        self.mock_generator.generate.return_value = "Response"
        self.mock_evaluator.evaluate.return_value = {'overall_score': 0.3}  # Always low

        result = rag.run(self.query)

        # Should not exceed max iterations
        self.assertLessEqual(result['metadata']['total_iterations'], 2)

    def test_document_enhancement(self):
        """Test document enhancement with correction metadata."""
        rag = self._create_corrective_rag()

        doc = {'content': 'Test content', 'score': 0.7}

        enhanced = rag._enhance_document(doc, self.query)

        self.assertIn('correction_metadata', enhanced)
        self.assertIn('relevance_score', enhanced['correction_metadata'])
        self.assertTrue(enhanced['correction_metadata']['enhanced'])


if __name__ == '__main__':
    unittest.main()