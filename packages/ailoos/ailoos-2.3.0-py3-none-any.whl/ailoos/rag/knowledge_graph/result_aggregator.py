"""
Result Aggregator with Ranking

This module provides advanced result aggregation and ranking capabilities
for combining multiple retrieval sources in Graph RAG systems.
"""

from typing import List, Dict, Any, Optional, Tuple, Callable
import logging
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


class ResultAggregator:
    """
    Advanced result aggregation and ranking for Graph RAG.

    This class combines results from multiple sources (vector, graph, etc.)
    and applies sophisticated ranking algorithms.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the result aggregator.

        Args:
            config (Optional[Dict[str, Any]]): Configuration for ranking strategies
        """
        self.config = config or {}
        self.ranking_strategies = {
            'weighted_sum': self._rank_weighted_sum,
            'reciprocal_rank': self._rank_reciprocal_rank,
            'diversity_aware': self._rank_diversity_aware,
            'graph_centrality': self._rank_graph_centrality,
            'semantic_similarity': self._rank_semantic_similarity,
            'temporal_recency': self._rank_temporal_recency
        }

    def aggregate_results(self, result_sets: List[List[Tuple[Dict[str, Any], float]]],
                         strategy: str = 'weighted_sum',
                         weights: Optional[List[float]] = None,
                         top_k: int = 10,
                         **kwargs) -> List[Tuple[Dict[str, Any], float]]:
        """
        Aggregate and rank results from multiple sources.

        Args:
            result_sets (List[List[Tuple[Dict[str, Any], float]]]): List of result sets from different sources
            strategy (str): Ranking strategy to use
            weights (Optional[List[float]]): Weights for each result set
            top_k (int): Number of top results to return
            **kwargs: Additional parameters for ranking strategy

        Returns:
            List[Tuple[Dict[str, Any], float]]: Aggregated and ranked results
        """
        if not result_sets:
            return []

        # Default weights if not provided
        if weights is None:
            weights = [1.0] * len(result_sets)

        # Normalize weights
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]

        # Apply ranking strategy
        if strategy in self.ranking_strategies:
            ranked_results = self.ranking_strategies[strategy](result_sets, weights, **kwargs)
        else:
            logger.warning(f"Unknown ranking strategy: {strategy}, using weighted_sum")
            ranked_results = self._rank_weighted_sum(result_sets, weights)

        # Remove duplicates and apply final ranking
        deduplicated = self._deduplicate_results(ranked_results)

        # Return top_k results
        return deduplicated[:top_k]

    def _rank_weighted_sum(self, result_sets: List[List[Tuple[Dict[str, Any], float]]],
                          weights: List[float]) -> List[Tuple[Dict[str, Any], float]]:
        """
        Rank results using weighted sum of scores.

        Args:
            result_sets: List of result sets
            weights: Weights for each result set

        Returns:
            List of ranked results
        """
        # Collect all results with their weighted scores
        result_map = defaultdict(list)

        for i, results in enumerate(result_sets):
            weight = weights[i] if i < len(weights) else 1.0

            for doc, score in results:
                doc_id = doc.get('id', str(hash(str(doc))))
                result_map[doc_id].append((doc, score * weight))

        # Aggregate scores for each document
        aggregated = []
        for doc_id, scores in result_map.items():
            # Use the document from the highest scoring source
            best_doc = max(scores, key=lambda x: x[1])[0]

            # Combine scores using various methods
            combined_score = self._combine_scores([s for _, s in scores])

            aggregated.append((best_doc, combined_score))

        # Sort by combined score
        aggregated.sort(key=lambda x: x[1], reverse=True)
        return aggregated

    def _rank_reciprocal_rank(self, result_sets: List[List[Tuple[Dict[str, Any], float]]],
                             weights: List[float]) -> List[Tuple[Dict[str, Any], float]]:
        """
        Rank using Reciprocal Rank Fusion (RRF).

        Args:
            result_sets: List of result sets
            weights: Weights for each result set

        Returns:
            List of ranked results
        """
        result_map = defaultdict(lambda: {'scores': [], 'docs': []})

        for i, results in enumerate(result_sets):
            weight = weights[i] if i < len(weights) else 1.0

            for rank, (doc, _) in enumerate(results):
                doc_id = doc.get('id', str(hash(str(doc))))
                # RRF score: weight / (rank + k), where k=60 is standard
                rrf_score = weight / (rank + 60)
                result_map[doc_id]['scores'].append(rrf_score)
                result_map[doc_id]['docs'].append(doc)

        # Aggregate RRF scores
        aggregated = []
        for doc_id, data in result_map.items():
            combined_score = sum(data['scores'])
            # Use the first document (they should be similar)
            best_doc = data['docs'][0]
            aggregated.append((best_doc, combined_score))

        aggregated.sort(key=lambda x: x[1], reverse=True)
        return aggregated

    def _rank_diversity_aware(self, result_sets: List[List[Tuple[Dict[str, Any], float]]],
                             weights: List[float], lambda_param: float = 0.5) -> List[Tuple[Dict[str, Any], float]]:
        """
        Rank with diversity awareness using Maximal Marginal Relevance (MMR).

        Args:
            result_sets: List of result sets
            weights: Weights for each result set
            lambda_param: Balance between relevance and diversity (0-1)

        Returns:
            List of ranked results
        """
        # First get relevance-based ranking
        relevance_results = self._rank_weighted_sum(result_sets, weights)

        if not relevance_results:
            return []

        # Apply MMR for diversity
        selected = []
        remaining = relevance_results.copy()

        while remaining and len(selected) < len(relevance_results):
            if not selected:
                # First item: highest relevance
                best = max(remaining, key=lambda x: x[1])
            else:
                # Subsequent items: balance relevance and diversity
                scores = []
                for doc, rel_score in remaining:
                    # Calculate maximum similarity to already selected documents
                    max_sim = 0
                    for sel_doc, _ in selected:
                        sim = self._calculate_document_similarity(doc, sel_doc)
                        max_sim = max(max_sim, sim)

                    # MMR score: lambda * relevance - (1-lambda) * max_similarity
                    mmr_score = lambda_param * rel_score - (1 - lambda_param) * max_sim
                    scores.append((doc, rel_score, mmr_score))

                best = max(scores, key=lambda x: x[2])

            selected.append((best[0], best[1]))
            remaining.remove((best[0], best[1]))

        return selected

    def _rank_graph_centrality(self, result_sets: List[List[Tuple[Dict[str, Any], float]]],
                              weights: List[float], graph_data: Optional[Dict[str, Any]] = None) -> List[Tuple[Dict[str, Any], float]]:
        """
        Rank considering graph centrality measures.

        Args:
            result_sets: List of result sets
            weights: Weights for each result set
            graph_data: Graph centrality data

        Returns:
            List of ranked results
        """
        base_results = self._rank_weighted_sum(result_sets, weights)

        if not graph_data or 'centrality' not in graph_data:
            return base_results

        centrality_scores = graph_data['centrality']

        # Boost scores based on centrality
        boosted_results = []
        for doc, score in base_results:
            doc_id = doc.get('id', '')
            centrality = centrality_scores.get(doc_id, 0.0)

            # Boost factor based on centrality (0.8 to 1.2)
            boost = 0.8 + (centrality * 0.4)
            boosted_score = score * boost

            boosted_results.append((doc, boosted_score))

        boosted_results.sort(key=lambda x: x[1], reverse=True)
        return boosted_results

    def _rank_semantic_similarity(self, result_sets: List[List[Tuple[Dict[str, Any], float]]],
                                weights: List[float], query_embedding: Optional[List[float]] = None) -> List[Tuple[Dict[str, Any], float]]:
        """
        Rank based on semantic similarity to query.

        Args:
            result_sets: List of result sets
            weights: Weights for each result set
            query_embedding: Query embedding vector

        Returns:
            List of ranked results
        """
        base_results = self._rank_weighted_sum(result_sets, weights)

        if not query_embedding:
            return base_results

        # Calculate semantic similarity for each result
        semantic_results = []
        for doc, score in base_results:
            # Extract or compute document embedding
            doc_embedding = self._get_document_embedding(doc)

            if doc_embedding:
                similarity = np.dot(query_embedding, doc_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
                )
                # Combine base score with semantic similarity
                combined_score = 0.7 * score + 0.3 * similarity
            else:
                combined_score = score

            semantic_results.append((doc, combined_score))

        semantic_results.sort(key=lambda x: x[1], reverse=True)
        return semantic_results

    def _rank_temporal_recency(self, result_sets: List[List[Tuple[Dict[str, Any], float]]],
                              weights: List[float], decay_factor: float = 0.9) -> List[Tuple[Dict[str, Any], float]]:
        """
        Rank considering temporal recency.

        Args:
            result_sets: List of result sets
            weights: Weights for each result set
            decay_factor: Temporal decay factor

        Returns:
            List of ranked results
        """
        base_results = self._rank_weighted_sum(result_sets, weights)

        # Apply temporal decay based on some timestamp field
        temporal_results = []
        for doc, score in base_results:
            # Extract timestamp (could be from metadata)
            timestamp = self._extract_timestamp(doc)

            if timestamp:
                # Calculate age in days
                import time
                current_time = time.time()
                age_days = (current_time - timestamp) / (24 * 3600)

                # Apply exponential decay
                temporal_boost = decay_factor ** age_days
                adjusted_score = score * temporal_boost
            else:
                adjusted_score = score

            temporal_results.append((doc, adjusted_score))

        temporal_results.sort(key=lambda x: x[1], reverse=True)
        return temporal_results

    def _combine_scores(self, scores: List[float]) -> float:
        """
        Combine multiple scores into a single score.

        Args:
            scores: List of scores to combine

        Returns:
            Combined score
        """
        if not scores:
            return 0.0

        # Use harmonic mean for score combination
        if all(s > 0 for s in scores):
            return len(scores) / sum(1/s for s in scores)
        else:
            # Fallback to arithmetic mean
            return sum(scores) / len(scores)

    def _deduplicate_results(self, results: List[Tuple[Dict[str, Any], float]]) -> List[Tuple[Dict[str, Any], float]]:
        """
        Remove duplicate results, keeping the highest scoring version.

        Args:
            results: Results to deduplicate

        Returns:
            Deduplicated results
        """
        seen_ids = set()
        deduplicated = []

        for doc, score in results:
            doc_id = doc.get('id', str(hash(str(doc))))

            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                deduplicated.append((doc, score))
            else:
                # Update score if higher
                for i, (existing_doc, existing_score) in enumerate(deduplicated):
                    if existing_doc.get('id') == doc_id and score > existing_score:
                        deduplicated[i] = (doc, score)
                        break

        return deduplicated

    def _calculate_document_similarity(self, doc1: Dict[str, Any], doc2: Dict[str, Any]) -> float:
        """
        Calculate similarity between two documents.

        Args:
            doc1: First document
            doc2: Second document

        Returns:
            Similarity score (0-1)
        """
        # Simple content-based similarity
        content1 = doc1.get('content', '').lower()
        content2 = doc2.get('content', '').lower()

        if not content1 or not content2:
            return 0.0

        # Jaccard similarity of words
        words1 = set(content1.split())
        words2 = set(content2.split())

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _get_document_embedding(self, doc: Dict[str, Any]) -> Optional[List[float]]:
        """
        Extract or compute document embedding.

        Args:
            doc: Document dictionary

        Returns:
            Document embedding or None
        """
        # Check if embedding is already stored
        if 'embedding' in doc:
            return doc['embedding']

        # Try to get from metadata
        metadata = doc.get('metadata', {})
        if 'embedding' in metadata:
            return metadata['embedding']

        # Could compute embedding here if model available
        return None

    def _extract_timestamp(self, doc: Dict[str, Any]) -> Optional[float]:
        """
        Extract timestamp from document.

        Args:
            doc: Document dictionary

        Returns:
            Timestamp or None
        """
        # Check various timestamp fields
        timestamp_fields = ['timestamp', 'created_at', 'updated_at', 'date']

        for field in timestamp_fields:
            if field in doc:
                timestamp = doc[field]
                if isinstance(timestamp, str):
                    # Try to parse ISO format
                    try:
                        import dateutil.parser
                        dt = dateutil.parser.parse(timestamp)
                        return dt.timestamp()
                    except:
                        continue
                elif isinstance(timestamp, (int, float)):
                    return timestamp

        return None

    def get_available_strategies(self) -> List[str]:
        """Get list of available ranking strategies."""
        return list(self.ranking_strategies.keys())

    def add_custom_strategy(self, name: str, strategy_func: Callable) -> None:
        """
        Add a custom ranking strategy.

        Args:
            name: Strategy name
            strategy_func: Strategy function
        """
        self.ranking_strategies[name] = strategy_func