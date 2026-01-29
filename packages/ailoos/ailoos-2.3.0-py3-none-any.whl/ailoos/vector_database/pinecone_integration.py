"""
Pinecone Integration Module
Complete integration with Pinecone vector database.
"""

from typing import Dict, List, Any, Optional, Tuple
import pinecone
import numpy as np
import logging

logger = logging.getLogger(__name__)


class PineconeIntegration:
    """
    Complete integration with Pinecone vector database.
    """

    def __init__(self, api_key: str, environment: str, index_name: str = "default-index",
                 dimension: int = 384, metric: str = "cosine"):
        """
        Initialize Pinecone integration.

        Args:
            api_key: Pinecone API key
            environment: Pinecone environment
            index_name: Name of the index
            dimension: Vector dimension
            metric: Distance metric
        """
        self.api_key = api_key
        self.environment = environment
        self.index_name = index_name
        self.dimension = dimension
        self.metric = metric

        # Initialize Pinecone
        pinecone.init(api_key=api_key, environment=environment)

        # Check if index exists, create if not
        if index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=index_name,
                dimension=dimension,
                metric=metric
            )

        self.index = pinecone.Index(index_name)
        self._initialized = True
        logger.info(f"PineconeIntegration initialized with index: {index_name}")

    def close(self) -> None:
        """Close Pinecone connection."""
        # Pinecone doesn't require explicit closing
        self._initialized = False
        logger.info("PineconeIntegration closed")

    def insert_vectors(self, vectors: List[np.ndarray], metadata: Optional[List[Dict[str, Any]]] = None,
                      ids: Optional[List[str]] = None) -> List[str]:
        """
        Insert vectors into Pinecone.

        Args:
            vectors: List of vectors to insert
            metadata: Optional metadata for each vector
            ids: Optional custom IDs for vectors

        Returns:
            List of vector IDs
        """
        if metadata is None:
            metadata = [{}] * len(vectors)
        if ids is None:
            ids = [f"vec_{i}" for i in range(len(vectors))]

        # Prepare vectors for Pinecone
        pinecone_vectors = []
        for i, (vec, meta, vec_id) in enumerate(zip(vectors, metadata, ids)):
            pinecone_vectors.append((vec_id, vec.tolist(), meta))

        # Upsert in batches
        batch_size = 100
        for i in range(0, len(pinecone_vectors), batch_size):
            batch = pinecone_vectors[i:i + batch_size]
            self.index.upsert(vectors=batch)

        logger.info(f"Inserted {len(vectors)} vectors into Pinecone")
        return ids

    def search_similar(self, query_vector: np.ndarray, top_k: int = 10,
                      filter_metadata: Optional[Dict[str, Any]] = None) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search for similar vectors in Pinecone.

        Args:
            query_vector: Query vector
            top_k: Number of similar vectors to return
            filter_metadata: Optional metadata filters

        Returns:
            List of (id, score, metadata) tuples
        """
        query_response = self.index.query(
            vector=query_vector.tolist(),
            top_k=top_k,
            include_metadata=True,
            filter=filter_metadata
        )

        results = []
        for match in query_response['matches']:
            results.append((
                match['id'],
                match['score'],
                match.get('metadata', {})
            ))

        return results

    def delete_vectors(self, ids: List[str]) -> bool:
        """
        Delete vectors by IDs.

        Args:
            ids: List of vector IDs to delete

        Returns:
            True if deletion was successful
        """
        try:
            self.index.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} vectors from Pinecone")
            return True
        except Exception as e:
            logger.error(f"Error deleting vectors: {e}")
            return False

    def update_vector(self, vector_id: str, new_vector: np.ndarray,
                     new_metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update an existing vector.

        Args:
            vector_id: ID of vector to update
            new_vector: New vector data
            new_metadata: New metadata (optional)

        Returns:
            True if update was successful
        """
        try:
            metadata = new_metadata if new_metadata is not None else {}
            self.index.upsert(vectors=[(vector_id, new_vector.tolist(), metadata)])
            logger.info(f"Updated vector {vector_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating vector {vector_id}: {e}")
            return False

    def get_vector(self, vector_id: str) -> Optional[Tuple[np.ndarray, Dict[str, Any]]]:
        """
        Retrieve a vector by ID.

        Args:
            vector_id: Vector ID

        Returns:
            Tuple of (vector, metadata) or None if not found
        """
        try:
            fetch_response = self.index.fetch(ids=[vector_id])
            if vector_id in fetch_response['vectors']:
                vector_data = fetch_response['vectors'][vector_id]
                return (
                    np.array(vector_data['values']),
                    vector_data.get('metadata', {})
                )
            return None
        except Exception as e:
            logger.error(f"Error fetching vector {vector_id}: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """
        Get index statistics.

        Returns:
            Dictionary with index statistics
        """
        try:
            stats = self.index.describe_index_stats()
            return {
                'total_vectors': stats['total_vector_count'],
                'dimension': self.dimension,
                'index_name': self.index_name,
                'metric': self.metric
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}

    def clear_database(self) -> None:
        """Clear all vectors from the index."""
        try:
            # Delete all vectors by querying without filters and deleting
            # This is a simplified approach - in production, consider index recreation
            all_ids = []
            query_response = self.index.query(
                vector=[0.0] * self.dimension,  # Dummy vector
                top_k=10000,  # Large number to get all
                include_values=False
            )

            for match in query_response['matches']:
                all_ids.append(match['id'])

            if all_ids:
                self.index.delete(ids=all_ids)

            logger.info(f"Cleared all vectors from index {self.index_name}")
        except Exception as e:
            logger.error(f"Error clearing database: {e}")

    def create_index(self, index_name: str, dimension: int,
                    metric: str = "cosine", **kwargs) -> bool:
        """
        Create a new index.

        Args:
            index_name: Name of the index
            dimension: Vector dimension
            metric: Distance metric
            **kwargs: Additional parameters

        Returns:
            True if index creation was successful
        """
        try:
            if index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    name=index_name,
                    dimension=dimension,
                    metric=metric,
                    **kwargs
                )
                logger.info(f"Created new index: {index_name}")
                return True
            else:
                logger.warning(f"Index {index_name} already exists")
                return False
        except Exception as e:
            logger.error(f"Error creating index {index_name}: {e}")
            return False

    def delete_index(self, index_name: str) -> bool:
        """
        Delete an index.

        Args:
            index_name: Name of the index to delete

        Returns:
            True if deletion was successful
        """
        try:
            pinecone.delete_index(index_name)
            logger.info(f"Deleted index: {index_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting index {index_name}: {e}")
            return False