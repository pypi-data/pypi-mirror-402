"""
Similarity Search Utilities

This module provides utilities for performing similarity search operations
across different vector spaces and distance metrics.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class SimilaritySearch:
    """
    Utilities for similarity search operations.

    This class provides methods for searching similar items using
    various distance metrics and search algorithms.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize similarity search utilities.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing:
                - metric: Distance metric ('cosine', 'euclidean', 'manhattan')
                - algorithm: Search algorithm ('brute_force', 'approximate')
                - threshold: Similarity threshold
        """
        self.config = config
        self.metric = config.get('metric', 'cosine')
        self.algorithm = config.get('algorithm', 'brute_force')
        self.threshold = config.get('threshold', 0.0)

    def find_similar(self, query_vector: List[float],
                    candidate_vectors: List[List[float]],
                    top_k: int = 5) -> List[Tuple[int, float]]:
        """
        Find most similar vectors to query.

        Args:
            query_vector (List[float]): Query vector
            candidate_vectors (List[List[float]]): Candidate vectors
            top_k (int): Number of top results

        Returns:
            List[Tuple[int, float]]: List of (index, similarity) pairs
        """
        similarities = []

        for i, candidate in enumerate(candidate_vectors):
            similarity = self._calculate_similarity(query_vector, candidate)
            if similarity >= self.threshold:
                similarities.append((i, similarity))

        # Sort by similarity (descending for cosine, ascending for distance)
        reverse = self.metric in ['cosine', 'dot_product']
        similarities.sort(key=lambda x: x[1], reverse=reverse)

        return similarities[:top_k]

    def _calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate similarity between two vectors.

        Args:
            vec1 (List[float]): First vector
            vec2 (List[float]): Second vector

        Returns:
            float: Similarity score
        """
        if self.metric == 'cosine':
            return self._cosine_similarity(vec1, vec2)
        elif self.metric == 'euclidean':
            return self._euclidean_distance(vec1, vec2)
        elif self.metric == 'manhattan':
            return self._manhattan_distance(vec1, vec2)
        elif self.metric == 'dot_product':
            return self._dot_product(vec1, vec2)
        else:
            raise ValueError(f"Unsupported metric: {self.metric}")

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity."""
        import math

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _euclidean_distance(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate Euclidean distance."""
        return sum((a - b) ** 2 for a, b in zip(vec1, vec2)) ** 0.5

    def _manhattan_distance(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate Manhattan distance."""
        return sum(abs(a - b) for a, b in zip(vec1, vec2))

    def _dot_product(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate dot product."""
        return sum(a * b for a, b in zip(vec1, vec2))

    def batch_search(self, query_vectors: List[List[float]],
                    candidate_vectors: List[List[float]],
                    top_k: int = 5) -> List[List[Tuple[int, float]]]:
        """
        Perform batch similarity search.

        Args:
            query_vectors (List[List[float]]): Query vectors
            candidate_vectors (List[List[float]]): Candidate vectors
            top_k (int): Number of top results per query

        Returns:
            List[List[Tuple[int, float]]]: Results for each query
        """
        results = []

        for query_vec in query_vectors:
            result = self.find_similar(query_vec, candidate_vectors, top_k)
            results.append(result)

        return results

    def rank_by_similarity(self, query_vector: List[float],
                          items: List[Dict[str, Any]],
                          vector_field: str = 'embedding',
                          top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Rank items by similarity to query vector.

        Args:
            query_vector (List[float]): Query vector
            items (List[Dict[str, Any]]): Items with vectors
            vector_field (str): Field name containing vectors
            top_k (int): Number of top results

        Returns:
            List[Dict[str, Any]]: Ranked items with similarity scores
        """
        similarities = []

        for item in items:
            vector = item.get(vector_field, [])
            if vector:
                similarity = self._calculate_similarity(query_vector, vector)
                similarities.append((item, similarity))

        # Sort by similarity
        reverse = self.metric in ['cosine', 'dot_product']
        similarities.sort(key=lambda x: x[1], reverse=reverse)

        # Add similarity scores to items
        ranked_items = []
        for item, similarity in similarities[:top_k]:
            item_copy = item.copy()
            item_copy['similarity_score'] = similarity
            ranked_items.append(item_copy)

        return ranked_items

    def get_search_stats(self) -> Dict[str, Any]:
        """Get statistics about search configuration."""
        return {
            'metric': self.metric,
            'algorithm': self.algorithm,
            'threshold': self.threshold
        }