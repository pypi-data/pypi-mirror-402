"""
RAG Response Models

This module defines data models for RAG system responses,
including query results, system status, and error responses.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RAGQueryResponse:
    """
    Response model for RAG queries.

    Attributes:
        query (str): Original query
        response (str): Generated response
        context (List[Dict[str, Any]]): Retrieved context documents
        metrics (Dict[str, float]): Performance metrics
        metadata (Dict[str, Any]): Additional response metadata
        processing_time (float): Time taken to process query
        timestamp (datetime): Response timestamp
    """
    query: str
    response: str
    context: List[Dict[str, Any]]
    metrics: Dict[str, float]
    metadata: Dict[str, Any]
    processing_time: float
    timestamp: datetime

    @property
    def overall_score(self) -> float:
        """Calculate overall quality score from metrics."""
        return self.metrics.get('overall_score', 0.0)

    @property
    def context_count(self) -> int:
        """Get number of context documents."""
        return len(self.context)

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            'query': self.query,
            'response': self.response,
            'context': self.context,
            'metrics': self.metrics,
            'metadata': self.metadata,
            'processing_time': self.processing_time,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class StreamingChunk:
    """
    Model for streaming response chunks.

    Attributes:
        chunk (str): Text chunk
        query_id (str): Associated query ID
        chunk_index (int): Index of this chunk
        is_final (bool): Whether this is the final chunk
        metadata (Optional[Dict[str, Any]]): Additional metadata
    """
    chunk: str
    query_id: str
    chunk_index: int
    is_final: bool = False
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary."""
        return {
            'chunk': self.chunk,
            'query_id': self.query_id,
            'chunk_index': self.chunk_index,
            'is_final': self.is_final,
            'metadata': self.metadata or {}
        }


@dataclass
class DocumentOperationResponse:
    """
    Response model for document operations.

    Attributes:
        operation (str): Operation performed ('add', 'delete', 'update')
        success (bool): Whether operation succeeded
        document_count (int): Number of documents affected
        message (str): Human-readable message
        errors (List[str]): Any errors that occurred
        metadata (Dict[str, Any]): Additional operation metadata
    """
    operation: str
    success: bool
    document_count: int
    message: str
    errors: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize defaults."""
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            'operation': self.operation,
            'success': self.success,
            'document_count': self.document_count,
            'message': self.message,
            'errors': self.errors,
            'metadata': self.metadata
        }


@dataclass
class SystemHealthResponse:
    """
    Response model for system health checks.

    Attributes:
        status (str): System status ('healthy', 'degraded', 'unhealthy')
        version (str): System version
        uptime (float): System uptime in seconds
        components (Dict[str, str]): Status of individual components
        metrics (Dict[str, Any]): System metrics
        timestamp (datetime): Health check timestamp
    """
    status: str
    version: str
    uptime: float
    components: Dict[str, str]
    metrics: Dict[str, Any]
    timestamp: datetime

    def is_healthy(self) -> bool:
        """Check if system is healthy."""
        return self.status == 'healthy'

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            'status': self.status,
            'version': self.version,
            'uptime': self.uptime,
            'components': self.components,
            'metrics': self.metrics,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class FeedbackResponse:
    """
    Response model for feedback submissions.

    Attributes:
        feedback_id (str): Unique feedback identifier
        success (bool): Whether feedback was stored successfully
        message (str): Response message
        stored_at (datetime): When feedback was stored
        metadata (Dict[str, Any]): Additional metadata
    """
    feedback_id: str
    success: bool
    message: str
    stored_at: datetime
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize defaults."""
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            'feedback_id': self.feedback_id,
            'success': self.success,
            'message': self.message,
            'stored_at': self.stored_at.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class BatchQueryResponse:
    """
    Response model for batch query operations.

    Attributes:
        total_queries (int): Total number of queries processed
        successful_queries (int): Number of successful queries
        failed_queries (int): Number of failed queries
        results (List[RAGQueryResponse]): Individual query results
        errors (List[Dict[str, Any]]): Errors for failed queries
        total_processing_time (float): Total time for all queries
        timestamp (datetime): Batch completion timestamp
    """
    total_queries: int
    successful_queries: int
    failed_queries: int
    results: List[RAGQueryResponse]
    errors: List[Dict[str, Any]]
    total_processing_time: float
    timestamp: datetime

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        return self.successful_queries / self.total_queries if self.total_queries > 0 else 0.0

    @property
    def average_processing_time(self) -> float:
        """Calculate average processing time per query."""
        return self.total_processing_time / self.total_queries if self.total_queries > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            'total_queries': self.total_queries,
            'successful_queries': self.successful_queries,
            'failed_queries': self.failed_queries,
            'results': [result.to_dict() for result in self.results],
            'errors': self.errors,
            'total_processing_time': self.total_processing_time,
            'success_rate': self.success_rate,
            'average_processing_time': self.average_processing_time,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ErrorResponse:
    """
    Response model for errors.

    Attributes:
        error_type (str): Type of error
        message (str): Human-readable error message
        details (Optional[str]): Detailed error information
        request_id (Optional[str]): Associated request ID
        timestamp (datetime): Error timestamp
        retryable (bool): Whether the operation can be retried
    """
    error_type: str
    message: str
    details: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: datetime = None
    retryable: bool = False

    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary."""
        return {
            'error_type': self.error_type,
            'message': self.message,
            'details': self.details,
            'request_id': self.request_id,
            'timestamp': self.timestamp.isoformat(),
            'retryable': self.retryable
        }