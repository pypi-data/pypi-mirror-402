"""
Evaluator Component

This module defines the Evaluator component responsible for assessing the
quality and performance of RAG systems. It provides metrics and evaluation
methods for different aspects of RAG performance.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import logging
import re

logger = logging.getLogger(__name__)


class Evaluator(ABC):
    """
    Abstract base class for evaluation components in RAG systems.

    The Evaluator assesses the quality of RAG responses through various metrics
    including relevance, faithfulness, informativeness, and comparison with
    ground truth answers.

    Attributes:
        config (Dict[str, Any]): Configuration for the evaluator
        metrics_config: Settings for different evaluation metrics
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the evaluator with configuration.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing:
                - metrics_config: Settings for evaluation metrics
                - reference_config: Settings for ground truth comparison
                - threshold_config: Thresholds for pass/fail criteria
        """
        self.config = config
        self.metrics_config = config.get('metrics_config', {})
        logger.info(f"Initialized {self.__class__.__name__} evaluator")

    @abstractmethod
    def evaluate(self, query: str, response: str, ground_truth: Optional[str] = None,
                 context: Optional[List[Dict[str, Any]]] = None) -> Dict[str, float]:
        """
        Evaluate the quality of a RAG response.

        Args:
            query (str): The original query
            response (str): The generated response
            ground_truth (Optional[str]): Ground truth answer for comparison
            context (Optional[List[Dict[str, Any]]]): Retrieved context used

        Returns:
            Dict[str, float]: Dictionary of evaluation metrics

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        pass

    def evaluate_relevance(self, query: str, response: str) -> float:
        """
        Evaluate how relevant the response is to the query.

        Args:
            query (str): The original query
            response (str): The generated response

        Returns:
            float: Relevance score (0.0 to 1.0)
        """
        # Simple keyword overlap-based relevance
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        response_words = set(re.findall(r'\b\w+\b', response.lower()))

        if not query_words:
            return 0.0

        overlap = len(query_words.intersection(response_words))
        return min(overlap / len(query_words), 1.0)

    def evaluate_faithfulness(self, response: str, context: List[Dict[str, Any]]) -> float:
        """
        Evaluate how faithful the response is to the provided context.

        Args:
            response (str): The generated response
            context (List[Dict[str, Any]]): Retrieved context documents

        Returns:
            float: Faithfulness score (0.0 to 1.0)
        """
        if not context:
            return 0.0

        # Simple check: ensure key facts from context appear in response
        context_text = ' '.join([doc.get('content', doc.get('text', ''))
                                for doc in context]).lower()
        response_lower = response.lower()

        # Count matching key phrases (simplified)
        context_sentences = re.split(r'[.!?]+', context_text)
        matching_sentences = 0

        for sentence in context_sentences:
            if sentence.strip() and any(word in response_lower for word in sentence.split()[:3]):
                matching_sentences += 1

        return min(matching_sentences / max(len(context_sentences), 1), 1.0)

    def evaluate_informativeness(self, response: str) -> float:
        """
        Evaluate how informative the response is.

        Args:
            response (str): The generated response

        Returns:
            float: Informativeness score (0.0 to 1.0)
        """
        # Simple metrics based on length and diversity
        words = re.findall(r'\b\w+\b', response)
        unique_words = set(words)

        if not words:
            return 0.0

        # Length score (prefer substantial responses)
        length_score = min(len(words) / 50.0, 1.0)  # Max at 50 words

        # Diversity score (prefer varied vocabulary)
        diversity_score = len(unique_words) / len(words)

        return (length_score + diversity_score) / 2.0

    def compare_with_ground_truth(self, response: str, ground_truth: str) -> Dict[str, float]:
        """
        Compare response with ground truth answer.

        Args:
            response (str): Generated response
            ground_truth (str): Ground truth answer

        Returns:
            Dict[str, float]: Comparison metrics
        """
        response_clean = response.strip().lower()
        ground_truth_clean = ground_truth.strip().lower()

        # Exact match
        exact_match = 1.0 if response_clean == ground_truth_clean else 0.0

        # F1 score based on word overlap
        response_words = set(re.findall(r'\b\w+\b', response_clean))
        gt_words = set(re.findall(r'\b\w+\b', ground_truth_clean))

        if not response_words and not gt_words:
            f1 = 1.0
        elif not response_words or not gt_words:
            f1 = 0.0
        else:
            intersection = response_words.intersection(gt_words)
            precision = len(intersection) / len(response_words)
            recall = len(intersection) / len(gt_words)
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            'exact_match': exact_match,
            'f1_score': f1,
            'precision': precision if 'precision' in locals() else 0.0,
            'recall': recall if 'recall' in locals() else 0.0
        }

    def get_overall_score(self, metrics: Dict[str, float]) -> float:
        """
        Calculate an overall quality score from individual metrics.

        Args:
            metrics (Dict[str, float]): Individual metric scores

        Returns:
            float: Overall score (0.0 to 1.0)
        """
        weights = self.metrics_config.get('weights', {
            'relevance': 0.3,
            'faithfulness': 0.3,
            'informativeness': 0.2,
            'ground_truth_f1': 0.2
        })

        score = 0.0
        total_weight = 0.0

        for metric, weight in weights.items():
            if metric in metrics:
                score += metrics[metric] * weight
                total_weight += weight

        return score / total_weight if total_weight > 0 else 0.0

    def __repr__(self) -> str:
        """String representation of the evaluator."""
        return f"{self.__class__.__name__}(config={self.config})"