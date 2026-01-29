"""
Base RAG Class

This module defines the abstract base class for all RAG (Retrieval-Augmented Generation)
implementations in the AILOOS system. It provides the fundamental interface and
common functionality that all RAG techniques must implement.

The BaseRAG class establishes the contract for:
- Retrieval of relevant information from knowledge sources
- Generation of responses based on retrieved context
- Evaluation of RAG performance and quality metrics
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
import logging
from datetime import datetime

from .preprocessing import RAGPreprocessingPipeline, PreprocessingConfig
from .access_control import DocumentAccessFilter, UserContext, AccessControlEngine, AccessLevel

logger = logging.getLogger(__name__)


class BaseRAG(ABC):
    """
    Abstract base class for all RAG implementations.

    This class defines the standard interface that all RAG techniques must follow,
    ensuring consistency and interoperability across different RAG approaches.

    Attributes:
        config (Dict[str, Any]): Configuration parameters for the RAG system
        retriever: Component responsible for information retrieval
        generator: Component responsible for response generation
        evaluator: Component responsible for performance evaluation
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the RAG system with configuration.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing:
                - retriever_config: Settings for the retrieval component
                - generator_config: Settings for the generation component
                - evaluator_config: Settings for the evaluation component
                - preprocessing_config: Settings for input preprocessing
                - access_control_config: Settings for document access control
                - general settings like temperature, max_tokens, etc.
        """
        self.config = config
        self.retriever = None
        self.generator = None
        self.evaluator = None

        # Initialize preprocessing pipeline
        preprocessing_config = config.get('preprocessing_config')
        if preprocessing_config:
            self.preprocessing = RAGPreprocessingPipeline(preprocessing_config)
        else:
            self.preprocessing = RAGPreprocessingPipeline()

        # Initialize access control
        access_control_config = config.get('access_control_config')
        if access_control_config:
            access_engine = AccessControlEngine(access_control_config.get('policies', []))
            self.access_filter = DocumentAccessFilter(access_engine)
        else:
            self.access_filter = DocumentAccessFilter()

        logger.info(f"Initialized {self.__class__.__name__} with config: {config}")

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant information for a given query.

        Args:
            query (str): The input query string
            top_k (int): Number of top results to retrieve
            filters (Optional[Dict[str, Any]]): Optional filters for retrieval

        Returns:
            List[Dict[str, Any]]: List of retrieved documents/contexts with metadata

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        pass

    @abstractmethod
    def generate(self, query: str, context: List[Dict[str, Any]], **kwargs) -> str:
        """
        Generate a response based on the query and retrieved context.

        Args:
            query (str): The original input query
            context (List[Dict[str, Any]]): Retrieved context documents
            **kwargs: Additional generation parameters

        Returns:
            str: Generated response text

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        pass

    @abstractmethod
    def evaluate(self, query: str, response: str, ground_truth: Optional[str] = None,
                 context: Optional[List[Dict[str, Any]]] = None) -> Dict[str, float]:
        """
        Evaluate the quality of the RAG response.

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

    def run(self, query: str, top_k: int = 5, user_context: Optional[UserContext] = None, **kwargs) -> Dict[str, Any]:
        """
        Execute the complete RAG pipeline: preprocess -> retrieve -> filter -> generate -> evaluate.

        Args:
            query (str): Input query
            top_k (int): Number of documents to retrieve
            user_context (Optional[UserContext]): User context for access control
            **kwargs: Additional parameters for generation

        Returns:
            Dict[str, Any]: Complete RAG result containing:
                - query: Original query
                - processed_query: Query after preprocessing
                - context: Retrieved and filtered documents
                - response: Generated answer
                - metrics: Evaluation metrics
                - metadata: Additional pipeline information
                - security_info: Information about PII filtering and access control
        """
        try:
            # Step 0: Preprocess query (PII filtering, normalization, compliance)
            preprocessing_result = self.preprocessing.preprocess(query, user_context.user_id if user_context else None)
            processed_query = preprocessing_result['processed_query']

            # Step 1: Retrieve relevant context
            raw_context = self.retrieve(processed_query, top_k=top_k)

            # Step 2: Apply access control filtering
            if user_context:
                filtered_context = self.access_filter.filter_results(user_context, raw_context)
            else:
                # If no user context, assume public access
                public_user = UserContext(user_id=None, clearance_level=AccessLevel.PUBLIC)
                filtered_context = self.access_filter.filter_results(public_user, raw_context)

            # Step 3: Generate response
            response = self.generate(processed_query, [doc for doc, _ in filtered_context], **kwargs)

            # Step 4: Evaluate performance
            metrics = self.evaluate(processed_query, response, context=[doc for doc, _ in filtered_context])

            result = {
                "query": query,
                "processed_query": processed_query,
                "context": filtered_context,  # List of (document, score) tuples
                "response": response,
                "metrics": metrics,
                "metadata": {
                    "rag_type": self.__class__.__name__,
                    "top_k": top_k,
                    "retrieved_docs": len(raw_context),
                    "filtered_docs": len(filtered_context),
                    "timestamp": datetime.now().isoformat()
                },
                "security_info": {
                    "pii_detected": preprocessing_result['processing_details'].get('pii_detected', False),
                    "pii_changes_count": len(preprocessing_result['processing_details'].get('pii_changes', [])),
                    "user_id": user_context.user_id if user_context else None,
                    "access_level": user_context.clearance_level.value if user_context else "public"
                }
            }

            logger.info(f"RAG pipeline completed for user {user_context.user_id if user_context else 'anonymous'}: {query[:50]}...")
            return result

        except Exception as e:
            logger.error(f"Error in RAG pipeline: {str(e)}")
            raise

    def __repr__(self) -> str:
        """String representation of the RAG instance."""
        return f"{self.__class__.__name__}(config={self.config})"