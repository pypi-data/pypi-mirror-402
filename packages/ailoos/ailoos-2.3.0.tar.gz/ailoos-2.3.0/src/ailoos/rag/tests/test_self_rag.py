"""
Unit Tests for Self RAG Implementation

This module contains comprehensive unit tests for the SelfRAG class,
testing dynamic retrieval decision-making, confidence assessment,
self-reflection, and efficiency optimization functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time

from ..techniques.self_rag import SelfRAG, ConfidenceAssessor
from ..core.retrievers import VectorRetriever
from ..core.generators import MockGenerator
from ..core.evaluators import BasicRAGEvaluator


class TestConfidenceAssessor(unittest.TestCase):
    """Test cases for ConfidenceAssessor functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.assessor = ConfidenceAssessor({
            'confidence_thresholds': {'high': 0.8, 'medium': 0.6, 'low': 0.4}
        })
        self.query = "What is artificial intelligence?"

    def test_assess_high_confidence_response(self):
        """Test assessment of a high-confidence response."""
        response = "Artificial intelligence (AI) is a field of computer science " \
                  "that focuses on creating systems capable of performing tasks " \
                  "that typically require human intelligence, such as learning, " \
                  "reasoning, and problem-solving."

        assessment = self.assessor.assess_confidence(self.query, response)

        self.assertGreater(assessment['overall_confidence'], 0.7)
        self.assertEqual(assessment['confidence_level'], 'high')
        self.assertFalse(assessment['retrieval_needed'])

    def test_assess_low_confidence_response(self):
        """Test assessment of a low-confidence response."""
        response = "AI is technology."

        assessment = self.assessor.assess_confidence(self.query, response)

        self.assertLess(assessment['overall_confidence'], 0.6)
        self.assertIn(assessment['confidence_level'], ['low', 'very_low'])
        self.assertTrue(assessment['retrieval_needed'])

    def test_length_confidence_evaluation(self):
        """Test confidence assessment based on response length."""
        # Long, detailed response
        long_response = "Artificial intelligence is a comprehensive field " * 10
        score = self.assessor._assess_length_confidence(long_response)
        self.assertGreater(score, 0.8)

        # Short response
        short_response = "AI is good."
        score = self.assessor._assess_length_confidence(short_response)
        self.assertLess(score, 0.5)

    def test_specificity_confidence_evaluation(self):
        """Test confidence assessment based on response specificity."""
        # Specific response with numbers and proper nouns
        specific_response = "In 2023, OpenAI developed GPT-4, achieving state-of-the-art performance."
        score = self.assessor._assess_specificity_confidence(specific_response)
        self.assertGreater(score, 0.5)

        # Generic response
        generic_response = "AI is technology that does things."
        score = self.assessor._assess_specificity_confidence(generic_response)
        self.assertLess(score, 0.3)

    def test_alignment_confidence_evaluation(self):
        """Test confidence assessment based on query-response alignment."""
        aligned_response = "Artificial intelligence is a technology field."
        score = self.assessor._assess_alignment_confidence(self.query, aligned_response)
        self.assertGreater(score, 0.5)

        misaligned_response = "The weather is sunny today."
        score = self.assessor._assess_alignment_confidence(self.query, misaligned_response)
        self.assertLess(score, 0.3)

    def test_certainty_confidence_evaluation(self):
        """Test confidence assessment based on certainty indicators."""
        certain_response = "Artificial intelligence is definitely a field of computer science."
        score = self.assessor._assess_certainty_confidence(certain_response)
        self.assertGreater(score, 0.7)

        uncertain_response = "AI might be a type of computer thing, I think."
        score = self.assessor._assess_certainty_confidence(uncertain_response)
        self.assertLess(score, 0.6)


class TestSelfRAG(unittest.TestCase):
    """Test cases for SelfRAG functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'retriever_config': {'chunk_size': 500, 'chunk_overlap': 50},
            'generator_config': {'use_mock': True},
            'evaluator_config': {},
            'reflection_config': {
                'enable_self_assessment': True,
                'confidence_threshold': 0.6,
                'force_retrieval_for_complex_queries': True,
                'max_reflection_iterations': 2,
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

    def _create_self_rag(self):
        """Create a SelfRAG instance with mocked components."""
        rag = SelfRAG(self.config)
        rag.retriever = self.mock_retriever
        rag.generator = self.mock_generator
        rag.evaluator = self.mock_evaluator
        return rag

    def test_initialization(self):
        """Test SelfRAG initialization."""
        rag = self._create_self_rag()

        self.assertIsInstance(rag, SelfRAG)
        self.assertIsInstance(rag.confidence_assessor, ConfidenceAssessor)
        self.assertEqual(rag.reflection_config['confidence_threshold'], 0.6)
        self.assertIsNotNone(rag.self_rag_metrics)

    def test_retrieval_needed_high_confidence(self):
        """Test that retrieval is avoided when confidence is high."""
        rag = self._create_self_rag()

        # Mock high-confidence internal response
        self.mock_generator.generate.return_value = \
            "Artificial intelligence is a comprehensive field of computer science " \
            "that develops systems capable of performing tasks requiring human intelligence."

        decision = rag._assess_retrieval_need(self.query)

        self.assertFalse(decision['retrieval_needed'])
        self.assertGreater(decision['confidence'], 0.6)
        self.assertEqual(decision['confidence_level'], 'high')

    def test_retrieval_needed_low_confidence(self):
        """Test that retrieval is performed when confidence is low."""
        rag = self._create_self_rag()

        # Mock low-confidence internal response
        self.mock_generator.generate.return_value = "AI is technology."

        decision = rag._assess_retrieval_need(self.query)

        self.assertTrue(decision['retrieval_needed'])
        self.assertLess(decision['confidence'], 0.6)

    def test_force_retrieval_for_complex_queries(self):
        """Test forced retrieval for complex queries."""
        rag = self._create_self_rag()

        complex_query = "Explain in detail how artificial intelligence algorithms " \
                       "work and provide examples of their applications in healthcare."

        # Even with high confidence, complex queries should force retrieval
        self.mock_generator.generate.return_value = \
            "AI algorithms work by processing data and making predictions. " \
            "They are used in healthcare for diagnostics."

        decision = rag._assess_retrieval_need(complex_query)

        self.assertTrue(decision['forced_retrieval'])

    def test_run_method_retrieval_avoided(self):
        """Test run method when retrieval is avoided."""
        rag = self._create_self_rag()

        # Mock high confidence scenario
        self.mock_generator.generate.side_effect = [
            "High confidence internal response about AI.",  # Internal assessment
            "This should not be called"  # Should not generate again
        ]
        self.mock_evaluator.evaluate.return_value = {'overall_score': 0.8}

        result = rag.run(self.query)

        # Should not have performed retrieval
        self.assertEqual(len(result['context']), 0)
        self.assertIn('retrieval_performed', result['metadata'])
        self.assertFalse(result['metadata']['retrieval_performed'])
        self.assertIn('confidence_assessment', result['metadata'])

    def test_run_method_retrieval_performed(self):
        """Test run method when retrieval is performed."""
        rag = self._create_self_rag()

        # Mock low confidence scenario
        self.mock_generator.generate.side_effect = [
            "Low confidence response.",  # Internal assessment - low confidence
            "Retrieved response with context."  # Final generation with context
        ]
        self.mock_retriever.search.return_value = [(self.sample_documents[0], 0.8)]
        self.mock_evaluator.evaluate.return_value = {'overall_score': 0.8}

        result = rag.run(self.query)

        # Should have performed retrieval
        self.assertGreater(len(result['context']), 0)
        self.assertTrue(result['metadata']['retrieval_performed'])

    def test_self_reflection_and_correction(self):
        """Test self-reflection and response correction."""
        rag = self._create_self_rag()

        # Mock scenario with issues that need correction
        self.mock_generator.generate.side_effect = [
            "AI is technology.",  # Low confidence - triggers retrieval
            "AI is artificial intelligence.",  # Initial retrieved response
            "AI is artificial intelligence, a field of computer science."  # Corrected response
        ]
        self.mock_retriever.search.return_value = [(self.sample_documents[0], 0.8)]
        self.mock_evaluator.evaluate.side_effect = [
            {'overall_score': 0.8, 'relevance': 0.9},  # Initial evaluation
            {'overall_score': 0.9, 'relevance': 0.95}  # After correction
        ]

        result = rag.run(self.query)

        # Should have performed self-reflection
        self.assertIn('reflection_metadata', result['metadata'])
        reflection = result['metadata']['reflection_metadata']
        self.assertIn('reflection_performed', reflection)

    def test_identify_response_issues(self):
        """Test identification of response issues."""
        rag = self._create_self_rag()

        # Test response with multiple issues
        poor_response = "AI is good."
        context = self.sample_documents
        metrics = {'overall_score': 0.3, 'relevance': 0.4, 'informativeness': 0.2}

        issues = rag._identify_response_issues(self.query, poor_response, context, metrics)

        self.assertIn('low_relevance', issues)
        self.assertIn('low_informativeness', issues)

    def test_apply_refinement_fixes(self):
        """Test application of specific refinement fixes."""
        rag = self._create_self_rag()

        # Test relevance enhancement
        irrelevant_response = "The weather is nice."
        fixed = rag._apply_refinement_fix(self.query, irrelevant_response, 'low_relevance', self.sample_documents)

        # Should attempt to generate a more relevant response
        self.assertNotEqual(fixed, irrelevant_response)

    def test_efficiency_metrics_calculation(self):
        """Test calculation of efficiency metrics."""
        rag = self._create_self_rag()

        # Simulate some queries
        rag.self_rag_metrics['total_queries'] = 10
        rag.self_rag_metrics['retrieval_avoided'] = 7
        rag.self_rag_metrics['retrieval_performed'] = 3

        efficiency_info = rag._calculate_efficiency_info()

        self.assertAlmostEqual(efficiency_info['efficiency_ratio'], 0.7)
        self.assertEqual(efficiency_info['retrieval_avoided'], 7)
        self.assertEqual(efficiency_info['retrieval_performed'], 3)

    def test_self_rag_metrics_tracking(self):
        """Test that SelfRAG metrics are properly tracked."""
        rag = self._create_self_rag()

        # Perform operations
        self.mock_generator.generate.return_value = "High confidence response."
        self.mock_evaluator.evaluate.return_value = {'overall_score': 0.8}

        rag.run(self.query)

        metrics = rag.get_self_rag_metrics()
        self.assertIsInstance(metrics, dict)
        self.assertIn('total_queries', metrics)
        self.assertIn('retrieval_avoided', metrics)
        self.assertIn('efficiency_info', metrics)

    def test_pipeline_info_includes_reflection_config(self):
        """Test that pipeline info includes reflection configuration."""
        rag = self._create_self_rag()

        info = rag.get_pipeline_info()

        self.assertEqual(info['technique'], 'SelfRAG')
        self.assertIn('reflection_config', info)
        self.assertIn('confidence_assessor', info)
        self.assertIn('self_rag_metrics', info)

    def test_error_handling_in_confidence_assessment(self):
        """Test error handling during confidence assessment."""
        rag = self._create_self_rag()

        # Mock generator to raise exception
        self.mock_generator.generate.side_effect = Exception("Generation failed")

        # Should handle error gracefully
        decision = rag._assess_retrieval_need(self.query)

        # Should still return a decision (fallback behavior)
        self.assertIn('retrieval_needed', decision)

    def test_generate_without_retrieval(self):
        """Test generation without retrieval using empty context."""
        rag = self._create_self_rag()

        response = rag._generate_without_retrieval(self.query)

        # Should generate a response
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)

    def test_complex_query_detection(self):
        """Test detection of complex queries requiring forced retrieval."""
        rag = self._create_self_rag()

        simple_query = "What is AI?"
        complex_query = "Compare and contrast supervised and unsupervised machine learning " \
                       "algorithms, providing specific examples and use cases for each."

        # Simple query should not force retrieval if confidence is high
        self.assertFalse(rag._should_force_retrieval(simple_query, {'overall_confidence': 0.8}))

        # Complex query should force retrieval regardless of confidence
        self.assertTrue(rag._should_force_retrieval(complex_query, {'overall_confidence': 0.9}))

    def test_response_completeness_check(self):
        """Test checking if response is complete."""
        rag = self._create_self_rag()

        complete_response = "Artificial intelligence is a field of computer science " \
                          "that creates intelligent systems capable of learning and reasoning."
        self.assertFalse(rag._is_response_incomplete(self.query, complete_response))

        incomplete_response = "AI is"
        self.assertTrue(rag._is_response_incomplete(self.query, incomplete_response))


if __name__ == '__main__':
    unittest.main()