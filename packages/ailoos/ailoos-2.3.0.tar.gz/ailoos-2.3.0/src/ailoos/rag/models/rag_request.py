"""
RAG Request Models

This module defines data models for RAG system requests,
including query requests, document addition requests, and configuration updates.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RAGQueryRequest:
    """
    Request model for RAG queries.

    Attributes:
        query (str): The search query text
        rag_type (str): Type of RAG system to use
        top_k (int): Number of top results to retrieve
        filters (Optional[Dict[str, Any]]): Metadata filters for search
        parameters (Optional[Dict[str, Any]]): Additional query parameters
        streaming (bool): Whether to use streaming response
        timeout (Optional[float]): Request timeout in seconds
    """
    query: str
    rag_type: str = "NaiveRAG"
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    streaming: bool = False
    timeout: Optional[float] = None

    def __post_init__(self):
        """Validate request after initialization."""
        if not self.query or not self.query.strip():
            raise ValueError("Query cannot be empty")
        if self.top_k < 1:
            raise ValueError("top_k must be positive")
        if self.timeout is not None and self.timeout <= 0:
            raise ValueError("timeout must be positive")


@dataclass
class DocumentAdditionRequest:
    """
    Request model for adding documents to RAG system.

    Attributes:
        documents (List[Dict[str, Any]]): List of documents to add
        rag_type (str): Target RAG system
        batch_size (int): Batch size for processing
        embedding_model (Optional[str]): Embedding model to use
        metadata (Optional[Dict[str, Any]]): Additional metadata
    """
    documents: List[Dict[str, Any]]
    rag_type: str = "default"
    batch_size: int = 100
    embedding_model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate request after initialization."""
        if not self.documents:
            raise ValueError("Documents list cannot be empty")
        for doc in self.documents:
            if not isinstance(doc, dict):
                raise ValueError("Each document must be a dictionary")
            if 'content' not in doc and 'text' not in doc:
                raise ValueError("Each document must have 'content' or 'text' field")


@dataclass
class DocumentDeletionRequest:
    """
    Request model for deleting documents from RAG system.

    Attributes:
        document_ids (List[str]): IDs of documents to delete
        rag_type (str): Target RAG system
        cascade (bool): Whether to cascade delete related data
    """
    document_ids: List[str]
    rag_type: str = "default"
    cascade: bool = False

    def __post_init__(self):
        """Validate request after initialization."""
        if not self.document_ids:
            raise ValueError("Document IDs list cannot be empty")
        if not all(isinstance(doc_id, str) for doc_id in self.document_ids):
            raise ValueError("All document IDs must be strings")


@dataclass
class FeedbackSubmissionRequest:
    """
    Request model for submitting user feedback.

    Attributes:
        query_id (str): ID of the query being rated
        rating (int): User rating (1-5)
        feedback_text (Optional[str]): Optional feedback text
        categories (List[str]): Feedback categories
        metadata (Optional[Dict[str, Any]]): Additional metadata
    """
    query_id: str
    rating: int
    feedback_text: Optional[str] = None
    categories: List[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate request after initialization."""
        if not self.query_id:
            raise ValueError("query_id cannot be empty")
        if not 1 <= self.rating <= 5:
            raise ValueError("rating must be between 1 and 5")
        if self.categories is None:
            self.categories = []


@dataclass
class SystemConfigurationRequest:
    """
    Request model for updating system configuration.

    Attributes:
        config_updates (Dict[str, Any]): Configuration updates to apply
        target_systems (List[str]): Systems to update
        validate_only (bool): Whether to only validate without applying
        backup (bool): Whether to create backup before applying
    """
    config_updates: Dict[str, Any]
    target_systems: List[str] = None
    validate_only: bool = False
    backup: bool = True

    def __post_init__(self):
        """Validate request after initialization."""
        if not self.config_updates:
            raise ValueError("config_updates cannot be empty")
        if self.target_systems is None:
            self.target_systems = ["all"]


@dataclass
class BatchQueryRequest:
    """
    Request model for batch query processing.

    Attributes:
        queries (List[RAGQueryRequest]): List of queries to process
        parallel_processing (bool): Whether to process in parallel
        max_concurrent (int): Maximum concurrent queries
        priority_ordering (bool): Whether to order by priority
    """
    queries: List[RAGQueryRequest]
    parallel_processing: bool = True
    max_concurrent: int = 5
    priority_ordering: bool = False

    def __post_init__(self):
        """Validate request after initialization."""
        if not self.queries:
            raise ValueError("queries list cannot be empty")
        if self.max_concurrent < 1:
            raise ValueError("max_concurrent must be positive")


@dataclass
class IndexManagementRequest:
    """
    Request model for index management operations.

    Attributes:
        operation (str): Operation type ('rebuild', 'optimize', 'stats')
        target_indexes (List[str]): Target indexes
        parameters (Optional[Dict[str, Any]]): Operation parameters
    """
    operation: str
    target_indexes: List[str] = None
    parameters: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate request after initialization."""
        valid_operations = ['rebuild', 'optimize', 'stats', 'backup', 'restore']
        if self.operation not in valid_operations:
            raise ValueError(f"operation must be one of {valid_operations}")
        if self.target_indexes is None:
            self.target_indexes = ["all"]