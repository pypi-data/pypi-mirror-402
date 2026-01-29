"""
Tests for Graph RAG Implementation

This module contains unit tests for the GraphRAG class.
"""

import unittest
from unittest.mock import Mock, patch


class TestGraphRAG(unittest.TestCase):
    """Test cases for GraphRAG implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'graph_config': {'test': True},
            'retriever_config': {},
            'generator_config': {},
            'evaluator_config': {}
        }

    @patch('ailoos.rag.techniques.graph_rag.NaiveRAG')
    def test_initialization(self, mock_naive_rag):
        """Test GraphRAG initialization."""
        from ailoos.rag.techniques.graph_rag import GraphRAG

        rag = GraphRAG(self.config)

        # Check that graph attribute exists
        self.assertTrue(hasattr(rag, 'knowledge_graph'))

    @patch('ailoos.rag.techniques.graph_rag.NaiveRAG')
    def test_retrieve_with_enhancement(self, mock_naive_rag):
        """Test retrieval with graph enhancement."""
        from ailoos.rag.techniques.graph_rag import GraphRAG

        mock_instance = Mock()
        mock_instance.retrieve.return_value = [{'content': 'base result'}]
        mock_naive_rag.return_value = mock_instance

        rag = GraphRAG(self.config)
        results = rag.retrieve("test query")

        # Should call parent retrieve method
        mock_instance.retrieve.assert_called_once_with("test query", top_k=5, filters=None)

    def test_enhance_with_graph_method_exists(self):
        """Test that graph enhancement method exists."""
        from ailoos.rag.techniques.graph_rag import GraphRAG

        with patch('ailoos.rag.techniques.graph_rag.NaiveRAG'):
            rag = GraphRAG(self.config)

            # Check that enhancement method exists
            self.assertTrue(hasattr(rag, '_enhance_with_graph'))
            self.assertTrue(callable(getattr(rag, '_enhance_with_graph')))

    def test_get_pipeline_info_includes_graph(self):
        """Test that pipeline info includes graph configuration."""
        from ailoos.rag.techniques.graph_rag import GraphRAG

        with patch('ailoos.rag.techniques.graph_rag.NaiveRAG') as mock_naive_rag:
            mock_instance = Mock()
            mock_instance.get_pipeline_info.return_value = {'base': 'info'}
            mock_naive_rag.return_value = mock_instance

            rag = GraphRAG(self.config)
            info = rag.get_pipeline_info()

            # Should include graph-specific information
            self.assertIn('technique', info)
            self.assertEqual(info['technique'], 'GraphRAG')


if __name__ == '__main__':
    unittest.main()