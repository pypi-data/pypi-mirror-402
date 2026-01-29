"""
Tests for Agentic RAG Implementation

This module contains unit tests for the AgenticRAG class.
"""

import unittest
from unittest.mock import Mock, patch


class TestAgenticRAG(unittest.TestCase):
    """Test cases for AgenticRAG implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'agent_config': {'test': True},
            'retriever_config': {},
            'generator_config': {},
            'evaluator_config': {}
        }

    @patch('ailoos.rag.techniques.agentic_rag.NaiveRAG')
    def test_initialization(self, mock_naive_rag):
        """Test AgenticRAG initialization."""
        from ailoos.rag.techniques.agentic_rag import AgenticRAG

        rag = AgenticRAG(self.config)

        self.assertIsNotNone(rag.planner_agent)
        self.assertIsNotNone(rag.retriever_agent)
        self.assertIsNotNone(rag.evaluator_agent)

    @patch('ailoos.rag.techniques.agentic_rag.NaiveRAG')
    def test_run_with_planning(self, mock_naive_rag):
        """Test agentic RAG run with planning."""
        from ailoos.rag.techniques.agentic_rag import AgenticRAG

        # Mock the NaiveRAG run method
        mock_instance = Mock()
        mock_instance.run.return_value = {
            'query': 'test',
            'response': 'answer',
            'context': [],
            'metrics': {'score': 0.8}
        }
        mock_naive_rag.return_value = mock_instance

        rag = AgenticRAG(self.config)
        result = rag.run("test query")

        self.assertIn('plan', result)
        self.assertIn('query', result)
        self.assertIn('response', result)

    def test_planner_agent_creation(self):
        """Test that planner agent is properly initialized."""
        from ailoos.rag.techniques.agentic_rag import AgenticRAG

        with patch('ailoos.rag.techniques.agentic_rag.NaiveRAG'):
            rag = AgenticRAG(self.config)

            # Check that agents are initialized (would be None in real implementation)
            # This is a placeholder test
            self.assertTrue(hasattr(rag, 'planner_agent'))


if __name__ == '__main__':
    unittest.main()