"""
Unit Tests for Speculative RAG Implementation

This module contains comprehensive unit tests for the SpeculativeRAG class,
testing parallel generation, evidence retrieval, multi-agent verification,
and candidate selection functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time

from ..techniques.speculative_rag import SpeculativeRAG, VerificationAgent
from ..core.retrievers import VectorRetriever
from ..core.generators import MockGenerator
from ..core.evaluators import BasicRAGEvaluator


class TestVerificationAgent(unittest.TestCase):
    """Test cases for VerificationAgent functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.agent = VerificationAgent({})
        self.query = "What is artificial intelligence?"
        self.response = "AI is a field of computer science that creates intelligent machines."
        self.context = [
            {'content': 'AI is artificial intelligence, a field of computer science.'},
            {'content': 'Machine learning is part of AI.'}
        ]

    def test_verify_response_comprehensive(self):
        """Test comprehensive response verification."""
        scores = self.agent.verify_response(self.query, self.response, self.context)

        required_metrics = ['faithfulness', 'relevance', 'informativeness', 'coherence', 'overall']
        for metric in required_metrics:
            self.assertIn(metric, scores)
            self.assertIsInstance(scores[metric], float)
            self.assertGreaterEqual(scores[metric], 0.0)
            self.assertLessEqual(scores[metric], 1.0)

    def test_faithfulness_evaluation(self):
        """Test faithfulness evaluation."""
        # High faithfulness
        faithful_response = "AI is a field of computer science that creates intelligent machines."
        score = self.agent._evaluate_faithfulness(faithful_response, self.context)
        self.assertGreater(score, 0.5)

        # Low faithfulness
        unfaithful_response = "AI is a type of fruit that grows on trees."
        score = self.agent._evaluate_faithfulness(unfaithful_response, self.context)
        self.assertLess(score, 0.5)

    def test_relevance_evaluation(self):
        """Test relevance evaluation."""
        relevant_response = "Artificial intelligence is a branch of computer science."
        score = self.agent._evaluate_relevance(self.query, relevant_response)
        self.assertGreater(score, 0.5)

        irrelevant_response = "The weather is nice today."
        score = self.agent._evaluate_relevance(self.query, irrelevant_response)
        self.assertLess(score, 0.3)

    def test_informativeness_evaluation(self):
        """Test informativeness evaluation."""
        informative_response = "Artificial intelligence (AI) is a field of computer science " \
                             "that focuses on creating systems capable of performing tasks " \
                             "that typically require human intelligence."
        score = self.agent._evaluate_informativeness(informative_response)
        self.assertGreater(score, 0.7)

        uninformative_response = "AI is good."
        score = self.agent._evaluate_informativeness(uninformative_response)
        self.assertLess(score, 0.5)


class TestSpeculativeRAG(unittest.TestCase):
    """Test cases for SpeculativeRAG functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'retriever_config': {'chunk_size': 500, 'chunk_overlap': 50},
            'generator_config': {'use_mock': True},
            'evaluator_config': {},
            'speculative_config': {
                'num_candidates': 3,
                'verification_agents': 2,
                'parallel_generation': True,
                'evidence_retrieval': True,
                'selection_threshold': 0.7
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

    def _create_speculative_rag(self):
        """Create a SpeculativeRAG instance with mocked components."""
        rag = SpeculativeRAG(self.config)
        rag.retriever = self.mock_retriever
        rag.generator = self.mock_generator
        rag.evaluator = self.mock_evaluator
        return rag

    def test_initialization(self):
        """Test SpeculativeRAG initialization."""
        rag = self._create_speculative_rag()

        self.assertIsInstance(rag, SpeculativeRAG)
        self.assertEqual(len(rag.verification_agents), 2)
        self.assertEqual(rag.speculative_config['num_candidates'], 3)
        self.assertIsNotNone(rag.speculative_metrics)

    def test_generate_candidates_with_evidence(self):
        """Test generation of multiple candidates with evidence retrieval."""
        rag = self._create_speculative_rag()

        # Mock responses
        self.mock_generator.generate.side_effect = [
            "AI is artificial intelligence.",
            "AI stands for artificial intelligence.",
            "Artificial intelligence is AI."
        ]

        self.mock_retriever.search.side_effect = [
            [(self.sample_documents[0], 0.8)],  # Initial retrieval
            [(self.sample_documents[1], 0.7)],  # Evidence for candidate 0
            [(self.sample_documents[0], 0.9)],  # Evidence for candidate 1
            [(self.sample_documents[1], 0.6)]   # Evidence for candidate 2
        ]

        candidates = rag._generate_candidates_with_evidence(self.query, self.sample_documents)

        self.assertEqual(len(candidates), 3)
        for candidate in candidates:
            self.assertIn('response', candidate)
            self.assertIn('context', candidate)
            self.assertIn('evidence_retrieved', candidate)

    def test_parallel_candidate_generation(self):
        """Test parallel generation of candidates."""
        rag = self._create_speculative_rag()
        rag.speculative_config['parallel_generation'] = True

        self.mock_generator.generate.return_value = "AI response"
        self.mock_retriever.search.return_value = [(self.sample_documents[0], 0.8)]

        start_time = time.time()
        candidates = rag._generate_candidates_with_evidence(self.query, self.sample_documents)
        parallel_time = time.time() - start_time

        # Should generate candidates (parallel execution may not be faster in test environment)
        self.assertEqual(len(candidates), 3)

    def test_evidence_query_creation(self):
        """Test creation of evidence queries from responses."""
        rag = self._create_speculative_rag()

        original_query = "What is AI?"
        response = "AI stands for artificial intelligence and is used in machine learning."

        evidence_query = rag._create_evidence_query(original_query, response)

        # Should include both original query and new terms from response
        self.assertIn("AI", evidence_query)
        self.assertIn("artificial intelligence", evidence_query.lower())
        self.assertIn("machine learning", evidence_query.lower())

    def test_candidate_verification(self):
        """Test verification of candidates using multiple agents."""
        rag = self._create_speculative_rag()

        candidates = [
            {
                'candidate_id': 0,
                'response': 'AI is artificial intelligence.',
                'context': self.sample_documents
            },
            {
                'candidate_id': 1,
                'response': 'AI stands for artificial intelligence.',
                'context': self.sample_documents
            }
        ]

        verified_candidates = rag._verify_candidates_parallel(self.query, candidates)

        self.assertEqual(len(verified_candidates), 2)
        for candidate in verified_candidates:
            self.assertIn('scores', candidate)
            self.assertIn('overall_score', candidate)
            self.assertIn('agent_scores', candidate)

    def test_optimal_candidate_selection(self):
        """Test selection of the optimal candidate."""
        rag = self._create_speculative_rag()

        verified_candidates = [
            {
                'candidate_id': 0,
                'response': 'Poor response',
                'context': self.sample_documents,
                'overall_score': 0.4
            },
            {
                'candidate_id': 1,
                'response': 'Good response',
                'context': self.sample_documents,
                'overall_score': 0.9
            },
            {
                'candidate_id': 2,
                'response': 'Medium response',
                'context': self.sample_documents,
                'overall_score': 0.7
            }
        ]

        selected = rag._select_optimal_candidate(verified_candidates)

        # Should select the highest scoring candidate
        self.assertEqual(selected['candidate_id'], 1)
        self.assertEqual(selected['overall_score'], 0.9)

    def test_selection_threshold_fallback(self):
        """Test fallback selection when best candidate is below threshold."""
        rag = self._create_speculative_rag()
        rag.speculative_config['selection_threshold'] = 0.8

        verified_candidates = [
            {
                'candidate_id': 0,
                'response': 'Below threshold response',
                'context': self.sample_documents,
                'overall_score': 0.6  # Below threshold
            },
            {
                'candidate_id': 1,
                'response': 'Still below but better',
                'context': self.sample_documents,
                'overall_score': 0.7  # Still below threshold
            }
        ]

        selected = rag._select_optimal_candidate(verified_candidates)

        # Should still select the best available candidate
        self.assertEqual(selected['candidate_id'], 1)

    def test_speculative_metrics_tracking(self):
        """Test that speculative metrics are properly tracked."""
        rag = self._create_speculative_rag()

        # Mock components
        self.mock_retriever.search.return_value = [(self.sample_documents[0], 0.8)]
        self.mock_generator.generate.side_effect = ["Response 1", "Response 2", "Response 3"]
        self.mock_evaluator.evaluate.return_value = {'overall_score': 0.8}

        rag.run(self.query)

        metrics = rag.get_speculative_metrics()
        self.assertIsInstance(metrics, dict)
        self.assertIn('candidates_generated', metrics)
        self.assertIn('evidence_retrievals', metrics)
        self.assertIn('verifications_performed', metrics)

    def test_run_method_integration(self):
        """Test complete run method integration."""
        rag = self._create_speculative_rag()

        # Mock all components
        self.mock_retriever.search.side_effect = [
            [(self.sample_documents[0], 0.8)],  # Initial retrieval
            [(self.sample_documents[1], 0.7)],  # Evidence retrieval
            [(self.sample_documents[0], 0.9)],
            [(self.sample_documents[1], 0.6)]
        ]
        self.mock_generator.generate.side_effect = [
            "AI is artificial intelligence.",
            "AI stands for artificial intelligence.",
            "Artificial intelligence is AI."
        ]
        self.mock_evaluator.evaluate.return_value = {
            'overall_score': 0.8,
            'relevance': 0.9,
            'faithfulness': 0.8
        }

        result = rag.run(self.query)

        # Verify result structure
        self.assertIn('query', result)
        self.assertIn('response', result)
        self.assertIn('context', result)
        self.assertIn('metrics', result)
        self.assertIn('metadata', result)

        # Verify speculative metadata
        metadata = result['metadata']
        self.assertIn('candidates_generated', metadata)
        self.assertIn('selected_candidate_score', metadata)
        self.assertIn('speculative_metrics', metadata)

    def test_pipeline_info_includes_speculative_config(self):
        """Test that pipeline info includes speculative configuration."""
        rag = self._create_speculative_rag()

        info = rag.get_pipeline_info()

        self.assertEqual(info['technique'], 'SpeculativeRAG')
        self.assertIn('speculative_config', info)
        self.assertIn('verification_agents', info)
        self.assertIn('speculative_metrics', info)

    def test_error_handling_in_candidate_generation(self):
        """Test error handling during candidate generation."""
        rag = self._create_speculative_rag()

        # Mock generator to raise exception for one candidate
        self.mock_generator.generate.side_effect = [
            "Good response",
            Exception("Generation failed"),
            "Another good response"
        ]
        self.mock_retriever.search.return_value = [(self.sample_documents[0], 0.8)]

        candidates = rag._generate_candidates_with_evidence(self.query, self.sample_documents)

        # Should still generate valid candidates despite one failure
        self.assertGreater(len(candidates), 0)
        for candidate in candidates:
            self.assertIn('response', candidate)

    def test_document_deduplication_in_context(self):
        """Test that duplicate documents are not added to context."""
        rag = self._create_speculative_rag()

        doc1 = {'content': 'AI is artificial intelligence.', 'score': 0.8}
        doc2 = {'content': 'AI is artificial intelligence.', 'score': 0.7}  # Duplicate content

        context = [doc1]
        is_duplicate = rag._document_in_context(doc2, context)

        self.assertTrue(is_duplicate)


if __name__ == '__main__':
    unittest.main()