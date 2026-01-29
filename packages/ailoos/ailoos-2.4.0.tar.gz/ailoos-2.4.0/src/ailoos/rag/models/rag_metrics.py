"""
RAG Metrics Models

This module defines data models for RAG system metrics and evaluation results,
providing structured representations of performance measurements.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RetrievalMetrics:
    """
    Metrics for retrieval component performance.

    Attributes:
        precision_at_k (Dict[int, float]): Precision at different k values
        recall_at_k (Dict[int, float]): Recall at different k values
        mean_reciprocal_rank (float): Mean Reciprocal Rank
        mean_average_precision (float): Mean Average Precision
        ndcg_at_k (Dict[int, float]): NDCG at different k values
        retrieval_time (float): Time taken for retrieval
        retrieved_count (int): Number of documents retrieved
        relevant_count (int): Number of relevant documents found
    """
    precision_at_k: Dict[int, float]
    recall_at_k: Dict[int, float]
    mean_reciprocal_rank: float
    mean_average_precision: float
    ndcg_at_k: Dict[int, float]
    retrieval_time: float
    retrieved_count: int
    relevant_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'precision_at_k': self.precision_at_k,
            'recall_at_k': self.recall_at_k,
            'mean_reciprocal_rank': self.mean_reciprocal_rank,
            'mean_average_precision': self.mean_average_precision,
            'ndcg_at_k': self.ndcg_at_k,
            'retrieval_time': self.retrieval_time,
            'retrieved_count': self.retrieved_count,
            'relevant_count': self.relevant_count
        }


@dataclass
class GenerationMetrics:
    """
    Metrics for generation component performance.

    Attributes:
        response_length (int): Length of generated response
        response_time (float): Time taken to generate response
        perplexity (Optional[float]): Model perplexity score
        diversity_score (float): Lexical diversity of response
        factual_consistency (float): Factual consistency score
        coherence_score (float): Text coherence score
        fluency_score (float): Language fluency score
        token_count (int): Number of tokens generated
    """
    response_length: int
    response_time: float
    perplexity: Optional[float]
    diversity_score: float
    factual_consistency: float
    coherence_score: float
    fluency_score: float
    token_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'response_length': self.response_length,
            'response_time': self.response_time,
            'perplexity': self.perplexity,
            'diversity_score': self.diversity_score,
            'factual_consistency': self.factual_consistency,
            'coherence_score': self.coherence_score,
            'fluency_score': self.fluency_score,
            'token_count': self.token_count
        }


@dataclass
class EvaluationMetrics:
    """
    Comprehensive evaluation metrics for RAG system.

    Attributes:
        relevance_score (float): Query-response relevance
        faithfulness_score (float): Faithfulness to retrieved context
        informativeness_score (float): Information content score
        ground_truth_f1 (Optional[float]): F1 score against ground truth
        context_utilization (float): How well context was used
        hallucination_score (float): Hallucination detection score
        overall_score (float): Combined overall performance score
        confidence_interval (Optional[Tuple[float, float]]): Score confidence interval
    """
    relevance_score: float
    faithfulness_score: float
    informativeness_score: float
    ground_truth_f1: Optional[float]
    context_utilization: float
    hallucination_score: float
    overall_score: float
    confidence_interval: Optional[tuple]

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'relevance_score': self.relevance_score,
            'faithfulness_score': self.faithfulness_score,
            'informativeness_score': self.informativeness_score,
            'ground_truth_f1': self.ground_truth_f1,
            'context_utilization': self.context_utilization,
            'hallucination_score': self.hallucination_score,
            'overall_score': self.overall_score,
            'confidence_interval': self.confidence_interval
        }


@dataclass
class SystemMetrics:
    """
    System-level performance metrics.

    Attributes:
        total_queries (int): Total queries processed
        average_response_time (float): Average response time
        throughput_qps (float): Queries per second
        error_rate (float): Rate of failed queries
        memory_usage_mb (float): Memory usage in MB
        cpu_usage_percent (float): CPU usage percentage
        cache_hit_rate (float): Cache hit rate
        uptime_seconds (float): System uptime
    """
    total_queries: int
    average_response_time: float
    throughput_qps: float
    error_rate: float
    memory_usage_mb: float
    cpu_usage_percent: float
    cache_hit_rate: float
    uptime_seconds: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'total_queries': self.total_queries,
            'average_response_time': self.average_response_time,
            'throughput_qps': self.throughput_qps,
            'error_rate': self.error_rate,
            'memory_usage_mb': self.memory_usage_mb,
            'cpu_usage_percent': self.cpu_usage_percent,
            'cache_hit_rate': self.cache_hit_rate,
            'uptime_seconds': self.uptime_seconds
        }


@dataclass
class RAGMetrics:
    """
    Complete metrics collection for a RAG operation.

    Attributes:
        query_id (str): Unique query identifier
        timestamp (datetime): Metrics collection timestamp
        retrieval (RetrievalMetrics): Retrieval performance metrics
        generation (GenerationMetrics): Generation performance metrics
        evaluation (EvaluationMetrics): Overall evaluation metrics
        system (SystemMetrics): System performance metrics
        metadata (Dict[str, Any]): Additional metadata
    """
    query_id: str
    timestamp: datetime
    retrieval: RetrievalMetrics
    generation: GenerationMetrics
    evaluation: EvaluationMetrics
    system: SystemMetrics
    metadata: Dict[str, Any]

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert complete metrics to dictionary."""
        return {
            'query_id': self.query_id,
            'timestamp': self.timestamp.isoformat(),
            'retrieval': self.retrieval.to_dict(),
            'generation': self.generation.to_dict(),
            'evaluation': self.evaluation.to_dict(),
            'system': self.system.to_dict(),
            'metadata': self.metadata
        }

    @property
    def overall_performance(self) -> float:
        """Get overall performance score."""
        return self.evaluation.overall_score

    @property
    def is_high_quality(self) -> bool:
        """Check if response meets quality thresholds."""
        return self.overall_performance >= 0.8


@dataclass
class MetricsSummary:
    """
    Summary statistics for multiple RAG operations.

    Attributes:
        total_operations (int): Total number of operations
        time_range (Tuple[datetime, datetime]): Time range covered
        average_metrics (Dict[str, float]): Average values for key metrics
        percentile_metrics (Dict[str, Dict[int, float]]): Percentile values
        trend_analysis (Dict[str, Any]): Performance trends
        alerts (List[str]): Any performance alerts
    """
    total_operations: int
    time_range: tuple
    average_metrics: Dict[str, float]
    percentile_metrics: Dict[str, Dict[int, float]]
    trend_analysis: Dict[str, Any]
    alerts: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert summary to dictionary."""
        return {
            'total_operations': self.total_operations,
            'time_range': [dt.isoformat() for dt in self.time_range],
            'average_metrics': self.average_metrics,
            'percentile_metrics': self.percentile_metrics,
            'trend_analysis': self.trend_analysis,
            'alerts': self.alerts
        }