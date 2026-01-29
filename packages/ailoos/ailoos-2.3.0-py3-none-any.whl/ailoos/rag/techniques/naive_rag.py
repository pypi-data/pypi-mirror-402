"""
Naive RAG Implementation

This module implements the basic Naive RAG technique, which performs a simple
retrieve-then-generate pipeline without any advanced processing or refinement.
"""

from typing import List, Dict, Any, Optional
import logging

from ..core.base_rag import BaseRAG
from ..core.retrievers import VectorRetriever
from ..core.generators import EmpoorioLMGenerator
from ..core.evaluators import BasicRAGEvaluator

logger = logging.getLogger(__name__)


class NaiveRAG(BaseRAG):
    """
    Naive Retrieval-Augmented Generation implementation.

    This is the most basic RAG approach that simply retrieves relevant documents
    and uses them directly to generate a response without any additional processing,
    filtering, or refinement steps.

    The pipeline follows:
    1. Retrieve top-k relevant documents
    2. Format query + context into prompt
    3. Generate response
    4. Evaluate result
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Naive RAG with configuration.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing:
                - retriever_class: Class to use for retrieval
                - generator_class: Class to use for generation
                - evaluator_class: Class to use for evaluation
                - Component-specific configs
        """
        super().__init__(config)

        # Initialize components with concrete implementations
        retriever_class = config.get('retriever_class', VectorRetriever)
        generator_class = config.get('generator_class', EmpoorioLMGenerator)
        evaluator_class = config.get('evaluator_class', BasicRAGEvaluator)

        # Use unified configuration for EmpoorioLM
        generator_config = config.get('generator_config', {})
        if generator_class == EmpoorioLMGenerator and 'empoorio_api_config' in generator_config:
            # Merge EmpoorioLM specific configs
            full_generator_config = {
                **generator_config,
                'empoorio_api_config': generator_config.get('empoorio_api_config', {}),
                'rate_limiting': generator_config.get('rate_limiting', {}),
                'caching': generator_config.get('caching', {}),
                'conversation': generator_config.get('conversation', {}),
                'fallback': generator_config.get('fallback', {}),
                'metrics': generator_config.get('metrics', {}),
                'ab_testing': generator_config.get('ab_testing', {}),
                'models': generator_config.get('models', {}),
                'current_model': generator_config.get('current_model', 'empoorio-lm-v1')
            }
        else:
            full_generator_config = generator_config

        self.retriever = retriever_class(config.get('retriever_config', {}))
        self.generator = generator_class(full_generator_config)
        self.evaluator = evaluator_class(config.get('evaluator_config', {}))

        logger.info("NaiveRAG initialized with components")

    def retrieve(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents using the configured retriever.

        Args:
            query (str): Search query
            top_k (int): Number of documents to retrieve
            filters (Optional[Dict[str, Any]]): Optional filters

        Returns:
            List[Dict[str, Any]]: Retrieved documents
        """
        try:
            results = self.retriever.search(query, top_k=top_k, filters=filters)
            # Convert (doc, score) tuples to documents with scores
            documents = []
            for doc, score in results:
                doc_with_score = {**doc, 'score': score}
                documents.append(doc_with_score)

            logger.debug(f"Retrieved {len(documents)} documents for query: {query[:50]}...")
            return documents

        except Exception as e:
            logger.error(f"Error during retrieval: {str(e)}")
            raise

    def generate(self, query: str, context: List[Dict[str, Any]], **kwargs) -> str:
        """
        Generate response using retrieved context.

        Args:
            query (str): Original query
            context (List[Dict[str, Any]]): Retrieved documents
            **kwargs: Additional generation parameters

        Returns:
            str: Generated response
        """
        try:
            response = self.generator.generate(query, context, **kwargs)
            logger.debug(f"Generated response for query: {query[:50]}...")
            return response

        except Exception as e:
            logger.error(f"Error during generation: {str(e)}")
            raise

    def evaluate(self, query: str, response: str, ground_truth: Optional[str] = None,
                 context: Optional[List[Dict[str, Any]]] = None) -> Dict[str, float]:
        """
        Evaluate the RAG response quality.

        Args:
            query (str): Original query
            response (str): Generated response
            ground_truth (Optional[str]): Ground truth for comparison
            context (Optional[List[Dict[str, Any]]]): Retrieved context

        Returns:
            Dict[str, float]: Evaluation metrics
        """
        try:
            metrics = self.evaluator.evaluate(query, response, ground_truth, context)
            logger.debug(f"Evaluation metrics: {metrics}")
            return metrics

        except Exception as e:
            logger.error(f"Error during evaluation: {str(e)}")
            raise

    def get_pipeline_info(self) -> Dict[str, Any]:
        """
        Get information about the RAG pipeline configuration.

        Returns:
            Dict[str, Any]: Pipeline information
        """
        return {
            'technique': 'NaiveRAG',
            'description': 'Basic retrieve-then-generate RAG',
            'components': {
                'retriever': self.retriever.__class__.__name__,
                'generator': self.generator.__class__.__name__,
                'evaluator': self.evaluator.__class__.__name__
            },
            'config': self.config
        }