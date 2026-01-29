"""
Self RAG Implementation

This module implements the Self-RAG technique, which enables the model to
dynamically decide whether retrieval is needed based on internal confidence
assessment, optimizing efficiency by avoiding unnecessary searches.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
import time
import re

from .naive_rag import NaiveRAG

logger = logging.getLogger(__name__)


class ConfidenceAssessor:
    """
    Component responsible for assessing the model's confidence in its responses
    without external retrieval.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.confidence_thresholds = config.get('confidence_thresholds', {
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        })

    def assess_confidence(self, query: str, response: str) -> Dict[str, Any]:
        """
        Assess the model's confidence in its response to the query.

        Args:
            query (str): Original query
            response (str): Generated response

        Returns:
            Dict[str, Any]: Confidence assessment results
        """
        assessment = {}

        # Length-based confidence (longer responses often indicate more confidence)
        assessment['length_confidence'] = self._assess_length_confidence(response)

        # Specificity confidence (specific facts vs general statements)
        assessment['specificity_confidence'] = self._assess_specificity_confidence(response)

        # Query-response alignment confidence
        assessment['alignment_confidence'] = self._assess_alignment_confidence(query, response)

        # Uncertainty indicators (words like "maybe", "perhaps", "I think")
        assessment['certainty_confidence'] = self._assess_certainty_confidence(response)

        # Overall confidence score
        assessment['overall_confidence'] = self._calculate_overall_confidence(assessment)

        # Decision on whether retrieval is needed
        assessment['retrieval_needed'] = assessment['overall_confidence'] < self.confidence_thresholds['medium']
        assessment['confidence_level'] = self._get_confidence_level(assessment['overall_confidence'])

        return assessment

    def _assess_length_confidence(self, response: str) -> float:
        """Assess confidence based on response length."""
        word_count = len(response.split())
        if word_count < 10:
            return 0.3  # Very short responses indicate low confidence
        elif word_count < 50:
            return 0.7  # Moderate length
        else:
            return 0.9  # Long, detailed responses

    def _assess_specificity_confidence(self, response: str) -> float:
        """Assess confidence based on response specificity."""
        # Count specific indicators
        specific_indicators = [
            r'\d+',  # Numbers
            r'\b\d{4}\b',  # Years
            r'\b[A-Z][a-z]+\b',  # Proper nouns
            r'\b(specifically|exactly|precisely)\b',  # Specific language
        ]

        specificity_score = 0
        for pattern in specific_indicators:
            matches = len(re.findall(pattern, response))
            specificity_score += min(matches, 3)  # Cap at 3 per indicator

        # Normalize to 0-1 scale
        return min(1.0, specificity_score / 10)

    def _assess_alignment_confidence(self, query: str, response: str) -> float:
        """Assess how well the response aligns with the query."""
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())

        overlap = len(query_words.intersection(response_words))
        coverage = overlap / len(query_words) if query_words else 0

        return min(1.0, coverage * 1.5)  # Boost factor for good alignment

    def _assess_certainty_confidence(self, response: str) -> float:
        """Assess confidence based on certainty indicators."""
        uncertainty_indicators = [
            r'\b(maybe|perhaps|possibly|might|could|may)\b',
            r'\b(I think|I believe|I suspect|seems like|appears to)\b',
            r'\b(not sure|uncertain|unknown|not certain)\b'
        ]

        uncertainty_score = 0
        response_lower = response.lower()

        for pattern in uncertainty_indicators:
            matches = len(re.findall(pattern, response_lower))
            uncertainty_score += matches

        # Convert uncertainty to confidence (inverse relationship)
        confidence = max(0.0, 1.0 - (uncertainty_score * 0.2))
        return confidence

    def _calculate_overall_confidence(self, assessment: Dict[str, float]) -> float:
        """Calculate overall confidence from individual assessments."""
        weights = {
            'length_confidence': 0.2,
            'specificity_confidence': 0.3,
            'alignment_confidence': 0.3,
            'certainty_confidence': 0.2
        }

        overall = sum(
            assessment[metric] * weight
            for metric, weight in weights.items()
            if metric in assessment
        )

        return overall

    def _get_confidence_level(self, confidence: float) -> str:
        """Get confidence level category."""
        if confidence >= self.confidence_thresholds['high']:
            return 'high'
        elif confidence >= self.confidence_thresholds['medium']:
            return 'medium'
        elif confidence >= self.confidence_thresholds['low']:
            return 'low'
        else:
            return 'very_low'


class SelfRAG(NaiveRAG):
    """
    Self-Reflective RAG implementation.

    This advanced RAG technique enables dynamic decision-making about when
    retrieval is necessary. The model first assesses its own confidence in
    answering without external knowledge, and only performs retrieval when
    confidence is below acceptable thresholds.

    Key features:
    - Internal confidence assessment before retrieval
    - Dynamic retrieval decision-making
    - Efficiency optimization through selective retrieval
    - Self-reflection on response quality
    - Comprehensive confidence metrics
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Self-RAG with configuration.

        Args:
            config (Dict[str, Any]): Configuration dictionary with self-reflection settings
        """
        super().__init__(config)
        self.reflection_config = config.get('reflection_config', {
            'enable_self_assessment': True,
            'confidence_threshold': 0.6,
            'force_retrieval_for_complex_queries': True,
            'max_reflection_iterations': 2,
            'adaptive_retrieval': True
        })

        # Initialize confidence assessor
        self.confidence_assessor = ConfidenceAssessor(config)

        # Performance tracking
        self.self_rag_metrics = {
            'total_queries': 0,
            'retrieval_avoided': 0,
            'retrieval_performed': 0,
            'confidence_assessments': 0,
            'average_initial_confidence': 0.0,
            'efficiency_gain': 0.0
        }

        logger.info("SelfRAG initialized with dynamic retrieval decision-making")

    def run(self, query: str, top_k: int = 5, **kwargs) -> Dict[str, Any]:
        """
        Execute the self-reflective RAG pipeline with dynamic retrieval decisions.

        Args:
            query (str): Input query
            top_k (int): Number of documents to retrieve (if needed)
            **kwargs: Additional parameters

        Returns:
            Dict[str, Any]: Complete RAG result with self-reflection metadata
        """
        try:
            start_time = time.time()
            self.self_rag_metrics['total_queries'] += 1

            # Step 1: Assess if retrieval is needed
            retrieval_decision = self._assess_retrieval_need(query)

            context = []
            response = ""
            confidence_assessment = None

            if retrieval_decision['retrieval_needed']:
                # Perform retrieval and generation
                context = self.retrieve(query, top_k=top_k)
                response = self.generate(query, context, **kwargs)
                self.self_rag_metrics['retrieval_performed'] += 1

                logger.info(f"Retrieval performed. Initial confidence: {retrieval_decision['confidence']:.3f}")
            else:
                # Generate without retrieval
                response = self._generate_without_retrieval(query, **kwargs)
                self.self_rag_metrics['retrieval_avoided'] += 1

                logger.info(f"Retrieval avoided. High confidence: {retrieval_decision['confidence']:.3f}")

            # Step 2: Evaluate the final response
            metrics = self.evaluate(query, response, context=context if context else None)

            # Step 3: Self-reflection and potential refinement
            if self.reflection_config.get('enable_self_assessment', True):
                refined_response, reflection_metadata = self._perform_self_reflection(
                    query, response, context, metrics
                )
                if refined_response != response:
                    response = refined_response
                    # Re-evaluate after refinement
                    metrics = self.evaluate(query, response, context=context if context else None)
                    logger.info("Response refined through self-reflection")

            processing_time = time.time() - start_time

            result = {
                'query': query,
                'response': response,
                'context': context,
                'metrics': metrics,
                'metadata': {
                    'rag_type': self.__class__.__name__,
                    'retrieval_performed': len(context) > 0,
                    'confidence_assessment': retrieval_decision,
                    'reflection_metadata': reflection_metadata if 'reflection_metadata' in locals() else {},
                    'processing_time': processing_time,
                    'self_rag_metrics': self.self_rag_metrics.copy(),
                    'efficiency_info': self._calculate_efficiency_info(),
                    'timestamp': time.time()
                }
            }

            return result

        except Exception as e:
            logger.error(f"Error in self-reflective RAG pipeline: {str(e)}")
            # Fallback to basic RAG
            return super().run(query, top_k=top_k, **kwargs)

    def _assess_retrieval_need(self, query: str) -> Dict[str, Any]:
        """
        Assess whether retrieval is needed for this query based on internal confidence.

        Args:
            query (str): Input query

        Returns:
            Dict[str, Any]: Retrieval decision with confidence assessment
        """
        # Generate a preliminary response without retrieval
        preliminary_response = self._generate_without_retrieval(query)

        # Assess confidence in this response
        assessment = self.confidence_assessor.assess_confidence(query, preliminary_response)
        self.self_rag_metrics['confidence_assessments'] += 1

        # Update average confidence
        total_assessments = self.self_rag_metrics['confidence_assessments']
        current_avg = self.self_rag_metrics['average_initial_confidence']
        self.self_rag_metrics['average_initial_confidence'] = (
            (current_avg * (total_assessments - 1)) + assessment['overall_confidence']
        ) / total_assessments

        # Check for forced retrieval conditions
        force_retrieval = self._should_force_retrieval(query, assessment)

        decision = {
            'retrieval_needed': assessment['retrieval_needed'] or force_retrieval,
            'confidence': assessment['overall_confidence'],
            'confidence_level': assessment['confidence_level'],
            'assessment_details': assessment,
            'forced_retrieval': force_retrieval,
            'preliminary_response': preliminary_response
        }

        return decision

    def _generate_without_retrieval(self, query: str, **kwargs) -> str:
        """
        Generate a response without any retrieval, using only internal knowledge.

        Args:
            query (str): Query to answer
            **kwargs: Generation parameters

        Returns:
            str: Generated response
        """
        # Use the generator with empty context to simulate internal knowledge
        try:
            response = self.generator.generate(query, [], **kwargs)
            return response
        except Exception as e:
            logger.warning(f"Error in internal generation: {e}")
            # Fallback to a basic response
            return f"Based on my internal knowledge, I can provide information about: {query}"

    def _should_force_retrieval(self, query: str, assessment: Dict[str, Any]) -> bool:
        """
        Determine if retrieval should be forced despite high confidence.

        Args:
            query (str): Original query
            assessment (Dict[str, Any]): Confidence assessment

        Returns:
            bool: Whether to force retrieval
        """
        if not self.reflection_config.get('force_retrieval_for_complex_queries', True):
            return False

        # Check for complexity indicators
        complexity_indicators = [
            len(query.split()) > 20,  # Long queries
            '?' in query and len(query.split()) > 10,  # Complex questions
            any(word in query.lower() for word in ['explain', 'describe', 'compare', 'analyze']),  # Analytical queries
            len(re.findall(r'\d+', query)) > 2,  # Queries with many numbers
        ]

        is_complex = any(complexity_indicators)

        # Force retrieval for complex queries with medium confidence
        if is_complex and assessment['confidence_level'] in ['medium', 'low']:
            return True

        return False

    def _perform_self_reflection(self, query: str, response: str, context: List[Dict[str, Any]],
                               metrics: Dict[str, float]) -> Tuple[str, Dict[str, Any]]:
        """
        Perform self-reflection on the generated response and potentially refine it.

        Args:
            query (str): Original query
            response (str): Current response
            context (List[Dict[str, Any]]): Retrieved context (if any)
            metrics (Dict[str, float]): Current evaluation metrics

        Returns:
            Tuple[str, Dict[str, Any]]: (refined_response, reflection_metadata)
        """
        reflection_metadata = {
            'reflection_performed': True,
            'issues_identified': [],
            'refinements_applied': [],
            'iterations': 0
        }

        # Identify potential issues
        issues = self._identify_response_issues(query, response, context, metrics)
        reflection_metadata['issues_identified'] = issues

        if not issues:
            return response, reflection_metadata

        # Apply refinements
        refined_response = response
        max_iterations = self.reflection_config.get('max_reflection_iterations', 2)

        for iteration in range(max_iterations):
            reflection_metadata['iterations'] += 1

            # Apply fixes for identified issues
            fixes_applied = []
            for issue in issues:
                fix = self._apply_refinement_fix(query, refined_response, issue, context)
                if fix != refined_response:
                    refined_response = fix
                    fixes_applied.append(issue)

            reflection_metadata['refinements_applied'].extend(fixes_applied)

            # Re-assess after fixes
            if fixes_applied:
                new_metrics = self.evaluate(query, refined_response, context=context)
                if new_metrics.get('overall_score', 0) > metrics.get('overall_score', 0):
                    logger.debug(f"Refinement improved score: {metrics.get('overall_score', 0):.3f} -> {new_metrics.get('overall_score', 0):.3f}")
                    break  # Stop if improvement achieved
            else:
                break  # No fixes applied

        return refined_response, reflection_metadata

    def _identify_response_issues(self, query: str, response: str, context: List[Dict[str, Any]],
                                metrics: Dict[str, float]) -> List[str]:
        """
        Identify potential issues in the response that need refinement.

        Args:
            query (str): Original query
            response (str): Current response
            context (List[Dict[str, Any]]): Retrieved context
            metrics (Dict[str, float]): Evaluation metrics

        Returns:
            List[str]: List of identified issues
        """
        issues = []

        # Check relevance
        if metrics.get('relevance', 1.0) < 0.6:
            issues.append('low_relevance')

        # Check informativeness
        if metrics.get('informativeness', 1.0) < 0.5:
            issues.append('low_informativeness')

        # Check for factual inconsistencies (basic check)
        if context and self._has_factual_inconsistencies(response, context):
            issues.append('factual_inconsistency')

        # Check response completeness
        if self._is_response_incomplete(query, response):
            issues.append('incomplete_response')

        # Check for uncertainty that could be resolved
        if self._has_resolvable_uncertainty(response):
            issues.append('resolvable_uncertainty')

        return issues

    def _apply_refinement_fix(self, query: str, response: str, issue: str,
                            context: List[Dict[str, Any]]) -> str:
        """
        Apply a specific fix for an identified issue.

        Args:
            query (str): Original query
            response (str): Current response
            issue (str): Issue to fix
            context (List[Dict[str, Any]]): Available context

        Returns:
            str: Fixed response
        """
        if issue == 'low_relevance':
            # Try to make response more relevant to query
            return self._enhance_relevance(query, response, context)

        elif issue == 'low_informativeness':
            # Add more informative content
            return self._enhance_informativeness(query, response, context)

        elif issue == 'factual_inconsistency':
            # Correct factual errors
            return self._correct_factual_issues(response, context)

        elif issue == 'incomplete_response':
            # Complete the response
            return self._complete_response(query, response, context)

        elif issue == 'resolvable_uncertainty':
            # Resolve uncertainty with available information
            return self._resolve_uncertainty(response, context)

        return response  # No fix applied

    def _enhance_relevance(self, query: str, response: str, context: List[Dict[str, Any]]) -> str:
        """Enhance response relevance to the query."""
        # Simple enhancement: regenerate with more focus on query terms
        focused_query = f"Please answer this specific question: {query}"
        if context:
            enhanced = self.generator.generate(focused_query, context)
            return enhanced
        return response

    def _enhance_informativeness(self, query: str, response: str, context: List[Dict[str, Any]]) -> str:
        """Make response more informative."""
        if len(response.split()) < 30 and context:
            # Add more details from context
            informative_query = f"Provide a detailed answer to: {query}"
            enhanced = self.generator.generate(informative_query, context)
            return enhanced
        return response

    def _correct_factual_issues(self, response: str, context: List[Dict[str, Any]]) -> str:
        """Correct factual inconsistencies."""
        # Basic correction: regenerate with fact-checking instruction
        correction_prompt = "Please verify and correct any factual errors in this response, using only reliable information:"
        if context:
            corrected = self.generator.generate(f"{correction_prompt} {response}", context)
            return corrected
        return response

    def _complete_response(self, query: str, response: str, context: List[Dict[str, Any]]) -> str:
        """Complete an incomplete response."""
        if response.endswith(('...', 'etc.', 'and so on')):
            completion_query = f"Complete this response to the question '{query}': {response}"
            if context:
                completed = self.generator.generate(completion_query, context)
                return completed
        return response

    def _resolve_uncertainty(self, response: str, context: List[Dict[str, Any]]) -> str:
        """Resolve resolvable uncertainty in the response."""
        if any(word in response.lower() for word in ['maybe', 'perhaps', 'might', 'could']):
            resolution_query = f"Provide a more certain answer to replace the uncertain parts: {response}"
            if context:
                resolved = self.generator.generate(resolution_query, context)
                return resolved
        return response

    def _has_factual_inconsistencies(self, response: str, context: List[Dict[str, Any]]) -> bool:
        """Check for basic factual inconsistencies."""
        # Placeholder: could implement more sophisticated fact-checking
        return False  # Simplified for now

    def _is_response_incomplete(self, query: str, response: str) -> bool:
        """Check if response seems incomplete."""
        return len(response.split()) < 20 and len(query.split()) > 5

    def _has_resolvable_uncertainty(self, response: str) -> bool:
        """Check if response has resolvable uncertainty."""
        uncertainty_words = ['maybe', 'perhaps', 'might', 'could', 'possibly']
        return any(word in response.lower() for word in uncertainty_words)

    def _calculate_efficiency_info(self) -> Dict[str, Any]:
        """Calculate efficiency metrics for self-RAG."""
        total = self.self_rag_metrics['total_queries']
        if total == 0:
            return {'efficiency_ratio': 0.0}

        avoided = self.self_rag_metrics['retrieval_avoided']
        efficiency_ratio = avoided / total

        return {
            'efficiency_ratio': efficiency_ratio,
            'retrieval_avoided': avoided,
            'retrieval_performed': self.self_rag_metrics['retrieval_performed'],
            'average_confidence': self.self_rag_metrics['average_initial_confidence']
        }

    def get_self_rag_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive Self-RAG performance metrics.

        Returns:
            Dict[str, Any]: Performance metrics
        """
        return {
            'total_queries': self.self_rag_metrics['total_queries'],
            'retrieval_avoided': self.self_rag_metrics['retrieval_avoided'],
            'retrieval_performed': self.self_rag_metrics['retrieval_performed'],
            'confidence_assessments': self.self_rag_metrics['confidence_assessments'],
            'average_initial_confidence': self.self_rag_metrics['average_initial_confidence'],
            'efficiency_info': self._calculate_efficiency_info()
        }

    def get_pipeline_info(self) -> Dict[str, Any]:
        """
        Get information about the self-reflective RAG pipeline.

        Returns:
            Dict[str, Any]: Pipeline information
        """
        info = super().get_pipeline_info()
        info.update({
            'technique': 'SelfRAG',
            'description': 'Dynamic retrieval decision-making with self-reflection and efficiency optimization',
            'reflection_config': self.reflection_config,
            'confidence_assessor': 'active' if self.reflection_config.get('enable_self_assessment') else 'disabled',
            'self_rag_metrics': self.get_self_rag_metrics()
        })
        return info