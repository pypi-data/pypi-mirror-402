"""
Cache Augmented RAG Quality Validator

This module provides comprehensive quality validation for Cache Augmented RAG (CAG) systems.
It includes metrics for consistency, factual accuracy, relevance, and cache quality assessment.
"""

import time
from typing import List, Dict, Any, Optional, Tuple
import logging
import re
from collections import defaultdict
from sentence_transformers import SentenceTransformer
import numpy as np

from ..core.evaluator import Evaluator

logger = logging.getLogger(__name__)


class CAGQualityValidator(Evaluator):
    """
    Quality validator specifically designed for Cache Augmented RAG systems.

    Provides comprehensive validation including:
    - Consistency across similar queries
    - Factual accuracy validation
    - Enhanced relevance metrics
    - Cache vs fresh response comparison
    - Cache degradation assessment
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize CAG quality validator.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing:
                - similarity_model: Model for semantic similarity (default: 'all-MiniLM-L6-v2')
                - consistency_threshold: Threshold for consistency checks (default: 0.8)
                - factual_validation_enabled: Whether to enable factual validation (default: True)
                - cache_comparison_enabled: Whether to enable cache vs fresh comparison (default: True)
                - max_consistency_samples: Max samples for consistency evaluation (default: 10)
        """
        super().__init__(config)

        # Initialize similarity model for consistency checks
        self.similarity_model_name = config.get('similarity_model', 'all-MiniLM-L6-v2')
        self.similarity_model = SentenceTransformer(self.similarity_model_name)

        # Configuration
        self.consistency_threshold = config.get('consistency_threshold', 0.8)
        self.factual_validation_enabled = config.get('factual_validation_enabled', True)
        self.cache_comparison_enabled = config.get('cache_comparison_enabled', True)
        self.max_consistency_samples = config.get('max_consistency_samples', 10)

        # Storage for consistency tracking
        self.query_history: Dict[str, List[str]] = defaultdict(list)
        self.response_embeddings: Dict[str, List[np.ndarray]] = defaultdict(list)

        logger.info(f"CAGQualityValidator initialized with model: {self.similarity_model_name}")

    def evaluate(self, query: str, response: str, ground_truth: Optional[str] = None,
                 context: Optional[List[Dict[str, Any]]] = None,
                 cache_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """
        Comprehensive evaluation of CAG response quality.

        Args:
            query (str): Original query
            response (str): Generated response
            ground_truth (Optional[str]): Ground truth answer
            context (Optional[List[Dict[str, Any]]]): Retrieved context
            cache_metadata (Optional[Dict[str, Any]]): Cache-related metadata

        Returns:
            Dict[str, float]: Comprehensive quality metrics
        """
        try:
            metrics = {}

            # Base metrics from parent class
            base_metrics = self._evaluate_base_metrics(query, response, ground_truth, context)
            metrics.update(base_metrics)

            # CAG-specific metrics
            if cache_metadata is not None:
                cache_metrics = self._evaluate_cache_quality(response, cache_metadata)
                metrics.update(cache_metrics)

            # Consistency metrics
            consistency_metrics = self._evaluate_consistency(query, response)
            metrics.update(consistency_metrics)

            # Enhanced factual accuracy
            if self.factual_validation_enabled and ground_truth is not None:
                factual_metrics = self._evaluate_factual_accuracy(response, ground_truth, context)
                metrics.update(factual_metrics)

            # Cache vs fresh comparison (if metadata available)
            if self.cache_comparison_enabled and cache_metadata is not None and 'fresh_response' in cache_metadata:
                comparison_metrics = self._evaluate_cache_vs_fresh(response, cache_metadata['fresh_response'])
                metrics.update(comparison_metrics)

            # Overall CAG quality score
            metrics['cag_overall_score'] = self._calculate_cag_overall_score(metrics)

            logger.debug(f"CAG quality metrics: {metrics}")
            return metrics

        except Exception as e:
            logger.error(f"Error during CAG quality evaluation: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {'error': 1.0, 'cag_overall_score': 0.0}

    def _evaluate_base_metrics(self, query: str, response: str,
                              ground_truth: Optional[str] = None,
                              context: Optional[List[Dict[str, Any]]] = None) -> Dict[str, float]:
        """Evaluate base RAG metrics using parent class."""
        try:
            result = super().evaluate(query, response, ground_truth, context)
            if result is None:
                raise ValueError("Parent evaluate returned None")
            return result
        except Exception as e:
            logger.warning(f"Base evaluation failed: {e}, returning basic metrics")
            # Return basic metrics if parent evaluation fails
            base_metrics = {
                'relevance': self.evaluate_relevance(query, response),
                'informativeness': self.evaluate_informativeness(response),
                'overall_score': 0.0
            }

            if context:
                base_metrics['faithfulness'] = self.evaluate_faithfulness(response, context)

            return base_metrics

    def _evaluate_cache_quality(self, response: str, cache_metadata: Dict[str, Any]) -> Dict[str, float]:
        """
        Evaluate cache-specific quality metrics.

        Args:
            response (str): Generated response
            cache_metadata (Dict[str, Any]): Cache metadata

        Returns:
            Dict[str, float]: Cache quality metrics
        """
        metrics = {}

        # Cache hit information
        metrics['cache_hit'] = 1.0 if cache_metadata.get('cache_hit', False) else 0.0

        # Cache age (how old is the cached response)
        if 'cache_timestamp' in cache_metadata:
            cache_age = time.time() - cache_metadata['cache_timestamp']
            # Normalize age (older = lower score, max age considered = 1 week = 604800 seconds)
            metrics['cache_freshness'] = max(0.0, 1.0 - (cache_age / 604800))
        else:
            metrics['cache_freshness'] = 1.0  # Assume fresh if no timestamp

        # Cache confidence (based on similarity score used for retrieval)
        if 'cache_similarity' in cache_metadata:
            metrics['cache_confidence'] = cache_metadata['cache_similarity']
        else:
            metrics['cache_confidence'] = 1.0

        # Response length consistency (cache shouldn't drastically change length)
        if 'original_length' in cache_metadata:
            current_length = len(response.split())
            original_length = cache_metadata['original_length']
            length_ratio = min(current_length, original_length) / max(current_length, original_length)
            metrics['cache_length_consistency'] = length_ratio
        else:
            metrics['cache_length_consistency'] = 1.0

        return metrics

    def _evaluate_consistency(self, query: str, response: str) -> Dict[str, float]:
        """
        Evaluate consistency with previous responses to similar queries.

        Args:
            query (str): Current query
            response (str): Current response

        Returns:
            Dict[str, float]: Consistency metrics
        """
        metrics = {}

        # Compute embedding for current response
        try:
            response_embedding = self.similarity_model.encode(response, convert_to_numpy=True)
        except Exception as e:
            logger.warning(f"Failed to compute response embedding: {e}")
            return {'consistency_score': 0.0, 'consistency_variance': 1.0}

        # Store for future comparisons
        query_key = self._normalize_query(query)
        self.query_history[query_key].append(response)
        self.response_embeddings[query_key].append(response_embedding)

        # Limit history size
        if len(self.query_history[query_key]) > self.max_consistency_samples:
            self.query_history[query_key] = self.query_history[query_key][-self.max_consistency_samples:]
            self.response_embeddings[query_key] = self.response_embeddings[query_key][-self.max_consistency_samples:]

        # Calculate consistency if we have multiple responses
        if len(self.response_embeddings[query_key]) > 1:
            similarities = []
            current_emb = response_embedding

            for prev_emb in self.response_embeddings[query_key][:-1]:  # Exclude current
                similarity = self._cosine_similarity(current_emb, prev_emb)
                similarities.append(similarity)

            metrics['consistency_score'] = np.mean(similarities)
            metrics['consistency_variance'] = np.var(similarities)
            metrics['consistency_min'] = min(similarities)
            metrics['consistency_max'] = max(similarities)
        else:
            metrics['consistency_score'] = 1.0  # Perfect consistency with single response
            metrics['consistency_variance'] = 0.0
            metrics['consistency_min'] = 1.0
            metrics['consistency_max'] = 1.0

        return metrics

    def _evaluate_factual_accuracy(self, response: str, ground_truth: str,
                                  context: Optional[List[Dict[str, Any]]] = None) -> Dict[str, float]:
        """
        Enhanced factual accuracy evaluation.

        Args:
            response (str): Generated response
            ground_truth (str): Ground truth answer
            context (Optional[List[Dict[str, Any]]]): Retrieved context

        Returns:
            Dict[str, float]: Factual accuracy metrics
        """
        metrics = {}

        # Base ground truth comparison
        gt_metrics = self.compare_with_ground_truth(response, ground_truth)
        metrics.update({f'factual_{k}': v for k, v in gt_metrics.items()})

        # Semantic similarity with ground truth
        try:
            response_emb = self.similarity_model.encode(response, convert_to_numpy=True)
            gt_emb = self.similarity_model.encode(ground_truth, convert_to_numpy=True)
            metrics['factual_semantic_similarity'] = self._cosine_similarity(response_emb, gt_emb)
        except Exception as e:
            logger.warning(f"Failed to compute semantic similarity: {e}")
            metrics['factual_semantic_similarity'] = 0.0

        # Context support score (if context available)
        if context:
            metrics['factual_context_support'] = self._evaluate_context_support(response, ground_truth, context)

        return metrics

    def _evaluate_cache_vs_fresh(self, cached_response: str, fresh_response: str) -> Dict[str, float]:
        """
        Compare cached vs fresh responses to detect cache degradation.

        Args:
            cached_response (str): Response from cache
            fresh_response (str): Freshly generated response

        Returns:
            Dict[str, float]: Cache vs fresh comparison metrics
        """
        metrics = {}

        # Semantic similarity
        try:
            cached_emb = self.similarity_model.encode(cached_response, convert_to_numpy=True)
            fresh_emb = self.similarity_model.encode(fresh_response, convert_to_numpy=True)
            metrics['cache_fresh_similarity'] = self._cosine_similarity(cached_emb, fresh_emb)
        except Exception as e:
            logger.warning(f"Failed to compute cache-fresh similarity: {e}")
            metrics['cache_fresh_similarity'] = 0.0

        # Length difference
        cached_len = len(cached_response.split())
        fresh_len = len(fresh_response.split())
        metrics['cache_fresh_length_diff'] = abs(cached_len - fresh_len) / max(cached_len, fresh_len, 1)

        # Word overlap
        cached_words = set(cached_response.lower().split())
        fresh_words = set(fresh_response.lower().split())
        overlap = len(cached_words.intersection(fresh_words))
        union = len(cached_words.union(fresh_words))
        metrics['cache_fresh_word_overlap'] = overlap / union if union > 0 else 0.0

        # Degradation score (lower similarity = higher degradation)
        metrics['cache_degradation_score'] = 1.0 - metrics['cache_fresh_similarity']

        return metrics

    def _evaluate_context_support(self, response: str, ground_truth: str,
                                 context: List[Dict[str, Any]]) -> float:
        """
        Evaluate how well the context supports the response relative to ground truth.

        Args:
            response (str): Generated response
            ground_truth (str): Ground truth answer
            context (List[Dict[str, Any]]): Retrieved context

        Returns:
            float: Context support score (0.0 to 1.0)
        """
        # Simple heuristic: check if key facts from ground truth appear in context
        gt_words = set(re.findall(r'\b\w+\b', ground_truth.lower()))
        context_text = ' '.join([doc.get('content', doc.get('text', '')) for doc in context]).lower()
        context_words = set(re.findall(r'\b\w+\b', context_text))

        # Calculate what fraction of ground truth facts are supported by context
        supported_facts = gt_words.intersection(context_words)
        return len(supported_facts) / len(gt_words) if gt_words else 0.0

    def _calculate_cag_overall_score(self, metrics: Dict[str, float]) -> float:
        """
        Calculate overall CAG quality score from individual metrics.

        Args:
            metrics (Dict[str, float]): Individual metric scores

        Returns:
            float: Overall CAG quality score (0.0 to 1.0)
        """
        # Weights for different aspects of CAG quality
        weights = {
            'relevance': 0.15,
            'faithfulness': 0.15,
            'informativeness': 0.10,
            'factual_f1_score': 0.15,
            'consistency_score': 0.15,
            'cache_freshness': 0.10,
            'cache_degradation_score': 0.10,  # Negative weight (lower degradation = higher score)
            'cache_fresh_similarity': 0.10
        }

        score = 0.0
        total_weight = 0.0

        for metric, weight in weights.items():
            if metric in metrics:
                # Handle negative weights (degradation should reduce score)
                if 'degradation' in metric:
                    metric_score = 1.0 - metrics[metric]  # Invert degradation
                else:
                    metric_score = metrics[metric]

                score += metric_score * weight
                total_weight += weight

        return score / total_weight if total_weight > 0 else 0.0

    def _normalize_query(self, query: str) -> str:
        """Normalize query for consistency tracking."""
        # Simple normalization: lowercase, remove punctuation, sort words
        words = re.findall(r'\b\w+\b', query.lower())
        return ' '.join(sorted(set(words)))

    def _cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings."""
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        return dot_product / (norm1 * norm2) if norm1 and norm2 else 0.0

    def reset_consistency_history(self):
        """Reset consistency tracking history."""
        self.query_history.clear()
        self.response_embeddings.clear()
        logger.info("Consistency history reset")

    def get_consistency_stats(self) -> Dict[str, Any]:
        """Get statistics about consistency tracking."""
        return {
            'total_queries_tracked': len(self.query_history),
            'total_responses_stored': sum(len(responses) for responses in self.query_history.values()),
            'average_responses_per_query': np.mean([len(responses) for responses in self.query_history.values()]) if self.query_history else 0.0
        }