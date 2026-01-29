"""
NIAH Evaluator - Professional Response Evaluation and Scoring
===========================================================

Advanced evaluation system for NIAH responses with sophisticated scoring metrics.
Implements industry-standard evaluation techniques used by leading AI companies.

Features:
- Multi-dimensional scoring (0-10 scale)
- Fuzzy matching for partial credit
- Contextual accuracy assessment
- Statistical analysis of responses
- Confidence calibration
"""

import logging
import re
import difflib
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass
import statistics

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Result of evaluating a single NIAH response."""
    score: float  # 0.0 to 10.0
    success: bool  # score >= 9.0
    confidence: float  # 0.0 to 1.0
    evaluation_details: Dict[str, Any]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'score': self.score,
            'success': self.success,
            'confidence': self.confidence,
            'evaluation_details': self.evaluation_details,
            'metadata': self.metadata
        }


class NIAHEvaluator:
    """
    Professional NIAH evaluator with advanced scoring algorithms.

    Features:
    - Exact match detection (perfect score)
    - Fuzzy string matching for partial credit
    - Contextual relevance assessment
    - Answer extraction from verbose responses
    - Statistical confidence estimation
    - Multi-criteria evaluation
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the NIAH evaluator.

        Args:
            config: Configuration dictionary
        """
        self.config = config or self._default_config()
        self.evaluation_history: List[Dict[str, Any]] = []

        logger.info("🎯 NIAH Evaluator initialized with professional scoring")

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for evaluation."""
        return {
            'exact_match_threshold': 0.95,  # Similarity for exact match
            'fuzzy_match_threshold': 0.7,   # Minimum similarity for partial credit
            'context_relevance_weight': 0.3,  # Weight for contextual assessment
            'verbosity_penalty_threshold': 200,  # Characters before verbosity penalty
            'enable_confidence_estimation': True,
            'strict_mode': False,  # Require exact matches only
        }

    def evaluate_response(
        self,
        model_response: str,
        expected_answer: str,
        context: Optional[str] = None,
        needle_type: str = 'fact'
    ) -> EvaluationResult:
        """
        Evaluate a model response against the expected answer.

        Args:
            model_response: The model's generated response
            expected_answer: The correct answer
            context: Optional context for relevance assessment
            needle_type: Type of needle ('fact', 'code', 'quote', etc.)

        Returns:
            Detailed evaluation result
        """
        # Clean and normalize responses
        clean_response = self._clean_response(model_response)
        clean_expected = self._clean_expected_answer(expected_answer)

        # Calculate similarity scores
        exact_similarity = self._calculate_similarity(clean_response, clean_expected)
        fuzzy_similarity = self._calculate_fuzzy_similarity(clean_response, clean_expected)

        # Extract answer if response is verbose
        extracted_answer = self._extract_answer(clean_response, needle_type)
        extracted_similarity = self._calculate_similarity(extracted_answer, clean_expected)

        # Determine best match
        best_similarity = max(exact_similarity, fuzzy_similarity, extracted_similarity)

        # Calculate base score (0-10 scale)
        if best_similarity >= self.config['exact_match_threshold']:
            base_score = 10.0  # Perfect match
        elif best_similarity >= self.config['fuzzy_match_threshold']:
            # Partial credit based on similarity
            partial_range = self.config['exact_match_threshold'] - self.config['fuzzy_match_threshold']
            partial_score = (best_similarity - self.config['fuzzy_match_threshold']) / partial_range
            base_score = 7.0 + (partial_score * 3.0)  # 7.0 to 10.0
        else:
            base_score = max(0.0, best_similarity * 7.0)  # 0.0 to 7.0

        # Apply penalties and bonuses
        final_score = self._apply_adjustments(
            base_score, clean_response, clean_expected, context, needle_type
        )

        # Ensure score is within bounds
        final_score = max(0.0, min(10.0, final_score))

        # Calculate confidence
        confidence = self._estimate_confidence(final_score, best_similarity, clean_response)

        # Determine success
        success = final_score >= 9.0

        # Create evaluation details
        evaluation_details = {
            'similarity_scores': {
                'exact': exact_similarity,
                'fuzzy': fuzzy_similarity,
                'extracted': extracted_similarity,
                'best': best_similarity
            },
            'response_analysis': {
                'original_length': len(model_response),
                'cleaned_length': len(clean_response),
                'extracted_answer': extracted_answer,
                'contains_expected': clean_expected.lower() in clean_response.lower()
            },
            'scoring_breakdown': {
                'base_score': base_score,
                'final_score': final_score,
                'adjustments_applied': self._get_adjustment_details(
                    base_score, final_score, clean_response, needle_type
                )
            }
        }

        # Store in history
        self.evaluation_history.append({
            'response_length': len(clean_response),
            'expected_length': len(clean_expected),
            'similarity': best_similarity,
            'score': final_score,
            'success': success,
            'needle_type': needle_type,
            'timestamp': None  # Will be set by caller
        })

        return EvaluationResult(
            score=final_score,
            success=success,
            confidence=confidence,
            evaluation_details=evaluation_details,
            metadata={
                'needle_type': needle_type,
                'response_cleaned': len(clean_response) != len(model_response),
                'extraction_used': extracted_answer != clean_response
            }
        )

    def _clean_response(self, response: str) -> str:
        """Clean and normalize the model response."""
        if not response:
            return ""

        # Remove common prefixes/suffixes
        response = response.strip()

        # Remove prompt remnants
        prompt_markers = [
            "Context:", "Question:", "Answer:", "Response:",
            "According to the context:", "Based on the information:",
            "The answer is:", "Here's what I found:"
        ]

        for marker in prompt_markers:
            if response.lower().startswith(marker.lower()):
                response = response[len(marker):].strip()

        # Remove quotes if they wrap the entire response
        if response.startswith('"') and response.endswith('"'):
            response = response[1:-1].strip()
        elif response.startswith("'") and response.endswith("'"):
            response = response[1:-1].strip()

        # Normalize whitespace
        response = re.sub(r'\s+', ' ', response)

        return response

    def _clean_expected_answer(self, expected: str) -> str:
        """Clean and normalize the expected answer."""
        if not expected:
            return ""

        # Similar cleaning as response
        expected = expected.strip()
        expected = re.sub(r'\s+', ' ', expected)

        return expected

    def _calculate_similarity(self, response: str, expected: str) -> float:
        """Calculate exact string similarity."""
        if not expected:
            return 0.0 if response else 1.0

        if not response:
            return 0.0

        # Exact match gets perfect score
        if response.lower() == expected.lower():
            return 1.0

        # Calculate character-level similarity
        response_lower = response.lower()
        expected_lower = expected.lower()

        # Use difflib for sequence matching
        matcher = difflib.SequenceMatcher(None, response_lower, expected_lower)
        return matcher.ratio()

    def _calculate_fuzzy_similarity(self, response: str, expected: str) -> float:
        """Calculate fuzzy similarity allowing for minor variations."""
        if not expected or not response:
            return 0.0

        # Use multiple similarity measures
        similarities = []

        # 1. Token-based similarity
        response_tokens = set(response.lower().split())
        expected_tokens = set(expected.lower().split())

        if expected_tokens:
            token_overlap = len(response_tokens & expected_tokens) / len(expected_tokens)
            similarities.append(token_overlap)

        # 2. Difflib ratio
        similarities.append(difflib.SequenceMatcher(None, response.lower(), expected.lower()).ratio())

        # 3. Partial ratio (best substring match)
        similarities.append(difflib.SequenceMatcher(None, response.lower(), expected.lower()).quick_ratio())

        return max(similarities) if similarities else 0.0

    def _extract_answer(self, response: str, needle_type: str) -> str:
        """Extract the most likely answer from a verbose response."""
        if len(response) < 100:  # Short responses probably don't need extraction
            return response

        # Different extraction strategies based on needle type
        if needle_type == 'quote':
            # Look for quoted text
            quotes = re.findall(r'"([^"]*)"', response)
            if quotes:
                return quotes[0]

        elif needle_type == 'code':
            # Look for code-like patterns
            code_patterns = [
                r'`([^`]*)`',  # Inline code
                r'```[\w]*\n(.*?)\n```',  # Code blocks
                r'\b\w+\([^)]*\)',  # Function calls
            ]
            for pattern in code_patterns:
                matches = re.findall(pattern, response, re.DOTALL)
                if matches:
                    return matches[0]

        elif needle_type == 'fact':
            # Look for complete sentences
            sentences = re.split(r'[.!?]+', response)
            # Return the longest sentence as likely answer
            if sentences:
                return max(sentences, key=len).strip()

        # Default: return first meaningful sentence
        sentences = re.split(r'[.!?]+', response)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Meaningful length
                return sentence

        return response  # Fallback to original

    def _apply_adjustments(
        self,
        base_score: float,
        response: str,
        expected: str,
        context: Optional[str],
        needle_type: str
    ) -> float:
        """Apply score adjustments based on various factors."""
        adjusted_score = base_score

        # Verbosity penalty (responses that are too long get penalized)
        if len(response) > self.config['verbosity_penalty_threshold']:
            verbosity_ratio = self.config['verbosity_penalty_threshold'] / len(response)
            verbosity_penalty = (1 - verbosity_ratio) * 2.0  # Max 2 points penalty
            adjusted_score -= verbosity_penalty

        # Context relevance bonus (if context is provided)
        if context and expected.lower() in context.lower():
            # Bonus for answers that appear to be extracted from context
            context_bonus = 0.5
            adjusted_score += context_bonus

        # Needle type specific adjustments
        if needle_type == 'code':
            # Code answers get bonus for containing code-like elements
            if re.search(r'[`()\[\]{}]', response):
                adjusted_score += 0.5

        elif needle_type == 'quote':
            # Quote answers get bonus for proper quotation
            if (response.startswith('"') and response.endswith('"')) or \
               (response.startswith("'") and response.endswith("'")):
                adjusted_score += 0.5

        # Strict mode: only exact matches get perfect scores
        if self.config['strict_mode'] and base_score < 10.0:
            adjusted_score = min(adjusted_score, 7.0)

        return adjusted_score

    def _estimate_confidence(self, score: float, similarity: float, response: str) -> float:
        """Estimate confidence in the evaluation."""
        if not self.config['enable_confidence_estimation']:
            return 0.8  # Default confidence

        # Confidence based on score consistency and response characteristics
        confidence_factors = []

        # High scores are more confident
        confidence_factors.append(min(1.0, score / 10.0))

        # High similarity increases confidence
        confidence_factors.append(similarity)

        # Longer responses might be less confident (could be hallucinating)
        length_penalty = 1.0
        if len(response) > 500:
            length_penalty = max(0.5, 500 / len(response))
        confidence_factors.append(length_penalty)

        # Average the confidence factors
        return statistics.mean(confidence_factors) if confidence_factors else 0.5

    def _get_adjustment_details(
        self,
        base_score: float,
        final_score: float,
        response: str,
        needle_type: str
    ) -> List[str]:
        """Get details about score adjustments applied."""
        adjustments = []

        if final_score > base_score:
            adjustments.append(".2f")
        elif final_score < base_score:
            adjustments.append(".2f")

        if len(response) > self.config['verbosity_penalty_threshold']:
            adjustments.append("verbosity penalty applied")

        if needle_type == 'code' and re.search(r'[`()\[\]{}]', response):
            adjustments.append("code pattern bonus")

        if needle_type == 'quote' and \
           ((response.startswith('"') and response.endswith('"')) or \
            (response.startswith("'") and response.endswith("'"))):
            adjustments.append("quotation bonus")

        return adjustments if adjustments else ["no adjustments"]

    def run_batch_evaluation(
        self,
        responses: List[str],
        expected_answers: List[str],
        contexts: Optional[List[str]] = None,
        needle_types: Optional[List[str]] = None
    ) -> List[EvaluationResult]:
        """
        Evaluate multiple responses in batch.

        Args:
            responses: List of model responses
            expected_answers: List of expected answers
            contexts: Optional list of contexts
            needle_types: Optional list of needle types

        Returns:
            List of evaluation results
        """
        if contexts is None:
            contexts = [None] * len(responses)

        if needle_types is None:
            needle_types = ['fact'] * len(responses)

        results = []
        for response, expected, context, needle_type in zip(
            responses, expected_answers, contexts, needle_types
        ):
            result = self.evaluate_response(response, expected, context, needle_type)
            results.append(result)

        return results

    def get_evaluation_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about evaluations performed."""
        if not self.evaluation_history:
            return {'total_evaluations': 0}

        scores = [entry['score'] for entry in self.evaluation_history]
        similarities = [entry['similarity'] for entry in self.evaluation_history]

        # Group by needle type
        type_stats = defaultdict(list)
        for entry in self.evaluation_history:
            type_stats[entry['needle_type']].append(entry['score'])

        return {
            'total_evaluations': len(self.evaluation_history),
            'success_rate': sum(1 for s in scores if s >= 9.0) / len(scores),
            'average_score': statistics.mean(scores),
            'median_score': statistics.median(scores),
            'score_std_dev': statistics.stdev(scores) if len(scores) > 1 else 0.0,
            'average_similarity': statistics.mean(similarities),
            'score_distribution': {
                'excellent': sum(1 for s in scores if s >= 9.0),
                'good': sum(1 for s in scores if 7.0 <= s < 9.0),
                'fair': sum(1 for s in scores if 5.0 <= s < 7.0),
                'poor': sum(1 for s in scores if s < 5.0)
            },
            'by_needle_type': {
                needle_type: {
                    'count': len(type_scores),
                    'average_score': statistics.mean(type_scores),
                    'success_rate': sum(1 for s in type_scores if s >= 9.0) / len(type_scores)
                }
                for needle_type, type_scores in type_stats.items()
            }
        }

    def reset_history(self):
        """Reset evaluation history."""
        self.evaluation_history.clear()
        logger.info("🗑️ Evaluation history reset")

    def export_evaluation_history(self, filepath: str):
        """Export evaluation history to JSON file."""
        import json
        with open(filepath, 'w') as f:
            json.dump(self.evaluation_history, f, indent=2, default=str)
        logger.info(f"📊 Evaluation history exported to {filepath} ")