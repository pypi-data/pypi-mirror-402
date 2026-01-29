"""
Tests for Naive RAG Implementation

This module contains unit tests for the NaiveRAG class and its components.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ailoos.rag.techniques.naive_rag import NaiveRAG


class TestNaiveRAG(unittest.TestCase):
    """Test cases for NaiveRAG implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'retriever_config': {'test': True},
            'generator_config': {'test': True},
            'evaluator_config': {'test': True}
        }

    def test_initialization(self):
        """Test NaiveRAG initialization."""
        with patch('ailoos.rag.techniques.naive_rag.Retriever') as mock_retriever, \
             patch('ailoos.rag.techniques.naive_rag.Generator') as mock_generator, \
             patch('ailoos.rag.techniques.naive_rag.Evaluator') as mock_evaluator:

            rag = NaiveRAG(self.config)

            self.assertIsNotNone(rag.retriever)
            self.assertIsNotNone(rag.generator)
            self.assertIsNotNone(rag.evaluator)

            mock_retriever.assert_called_once_with(self.config['retriever_config'])
            mock_generator.assert_called_once_with(self.config['generator_config'])
            mock_evaluator.assert_called_once_with(self.config['evaluator_config'])

    def test_retrieve(self):
        """Test retrieval functionality."""
        with patch('ailoos.rag.techniques.naive_rag.Retriever') as mock_retriever_class, \
             patch('ailoos.rag.techniques.naive_rag.Generator'), \
             patch('ailoos.rag.techniques.naive_rag.Evaluator'):

            mock_retriever = Mock()
            mock_retriever.search.return_value = [('doc1', 0.9), ('doc2', 0.8)]
            mock_retriever_class.return_value = mock_retriever

            rag = NaiveRAG(self.config)
            results = rag.retrieve("test query", top_k=2)

            expected_results = [
                {'content': 'doc1', 'score': 0.9},
                {'content': 'doc2', 'score': 0.8}
            ]

            self.assertEqual(results, expected_results)
            mock_retriever.search.assert_called_once_with("test query", top_k=2, filters=None)

    def test_generate(self):
        """Test generation functionality."""
        with patch('ailoos.rag.techniques.naive_rag.Retriever'), \
             patch('ailoos.rag.techniques.naive_rag.Generator') as mock_generator_class, \
             patch('ailoos.rag.techniques.naive_rag.Evaluator'):

            mock_generator = Mock()
            mock_generator.generate.return_value = "Generated response"
            mock_generator_class.return_value = mock_generator

            rag = NaiveRAG(self.config)
            context = [{'content': 'test context'}]
            response = rag.generate("test query", context)

            self.assertEqual(response, "Generated response")
            mock_generator.generate.assert_called_once_with("test query", context)

    def test_evaluate(self):
        """Test evaluation functionality."""
        with patch('ailoos.rag.techniques.naive_rag.Retriever'), \
             patch('ailoos.rag.techniques.naive_rag.Generator'), \
             patch('ailoos.rag.techniques.naive_rag.Evaluator') as mock_evaluator_class:

            mock_evaluator = Mock()
            mock_evaluator.evaluate.return_value = {'score': 0.85}
            mock_evaluator_class.return_value = mock_evaluator

            rag = NaiveRAG(self.config)
            metrics = rag.evaluate("query", "response")

            self.assertEqual(metrics, {'score': 0.85})
            mock_evaluator.evaluate.assert_called_once_with("query", "response", ground_truth=None, context=None)

    def test_run_pipeline(self):
        """Test complete RAG pipeline execution."""
        with patch('ailoos.rag.techniques.naive_rag.Retriever') as mock_retriever_class, \
             patch('ailoos.rag.techniques.naive_rag.Generator') as mock_generator_class, \
             patch('ailoos.rag.techniques.naive_rag.Evaluator') as mock_evaluator_class:

            # Setup mocks
            mock_retriever = Mock()
            mock_retriever.search.return_value = [('doc', 0.9)]
            mock_retriever_class.return_value = mock_retriever

            mock_generator = Mock()
            mock_generator.generate.return_value = "Response"
            mock_generator_class.return_value = mock_generator

            mock_evaluator = Mock()
            mock_evaluator.evaluate.return_value = {'overall_score': 0.8}
            mock_evaluator_class.return_value = mock_evaluator

            rag = NaiveRAG(self.config)
            result = rag.run("test query")

            self.assertIn('query', result)
            self.assertIn('response', result)
            self.assertIn('context', result)
            self.assertIn('metrics', result)
            self.assertEqual(result['query'], "test query")
            self.assertEqual(result['response'], "Response")

    def test_get_pipeline_info(self):
        """Test pipeline information retrieval."""
        with patch('ailoos.rag.techniques.naive_rag.Retriever') as mock_retriever_class, \
             patch('ailoos.rag.techniques.naive_rag.Generator') as mock_generator_class, \
             patch('ailoos.rag.techniques.naive_rag.Evaluator') as mock_evaluator_class:

            mock_retriever_class.return_value = Mock()
            mock_generator_class.return_value = Mock()
            mock_evaluator_class.return_value = Mock()

            rag = NaiveRAG(self.config)
            info = rag.get_pipeline_info()

            self.assertEqual(info['technique'], 'NaiveRAG')
            self.assertIn('components', info)
            self.assertIn('config', info)


if __name__ == '__main__':
    unittest.main()