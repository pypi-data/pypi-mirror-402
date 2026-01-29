"""
Qdrant Integration Module
Complete integration with Qdrant vector database.
"""

from typing import Dict, List, Any, Optional, Tuple
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
import numpy as np
import logging

logger = logging.getLogger(__name__)


class QdrantIntegration:
    """
    Complete integration with Qdrant vector database.
    """

    def __init__(self, url: str = "http://localhost:6333", api_key: Optional[str] = None,
                 collection_name: str = "default-collection", dimension: int = 384,
                 distance: str = "Cosine"):
        """
        Initialize Qdrant integration.

        Args:
            url: Qdrant server URL
            api_key: API key for authentication (optional)
            collection_name: Name of the collection
            dimension: Vector dimension
            distance: Distance metric ('Cosine', 'Euclid', 'Dot')
        """
        self.url = url
        self.api_key = api_key
        self.collection_name = collection_name
        self.dimension = dimension
        self.distance = distance

        # Initialize Qdrant client
        self.client = QdrantClient(url=url, api_key=api_key)

        # Create collection if it doesn't exist
        distance_map = {
            "Cosine": Distance.COSINE,
            "Euclid": Distance.EUCLID,
            "Dot": Distance.DOT
        }

        if not self.client.collection_exists(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=dimension,
                    distance=distance_map.get(distance, Distance.COSINE)
                )
            )

        self._initialized = True
        logger.info(f"QdrantIntegration initialized with collection: {collection_name}")

    def close(self) -> None:
        """Close Qdrant connection."""
        # Qdrant client doesn't require explicit closing
        self._initialized = False
        logger.info("QdrantIntegration closed")

    def insert_vectors(self, vectors: List[np.ndarray], metadata: Optional[List[Dict[str, Any]]] = None,
                      ids: Optional[List[str]] = None) -> List[str]:
        """
        Insert vectors into Qdrant.

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

        # Prepare points for Qdrant
        points = []
        for i, (vec, meta, vec_id) in enumerate(zip(vectors, metadata, ids)):
            # Convert string ID to integer for Qdrant
            point_id = hash(vec_id) % (2**63)  # Convert to int64
            points.append(models.PointStruct(
                id=point_id,
                vector=vec.tolist(),
                payload={**meta, "_id": vec_id}  # Store original ID in payload
            ))

        # Upsert in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch
            )

        logger.info(f"Inserted {len(vectors)} vectors into Qdrant")
        return ids

    def search_similar(self, query_vector: np.ndarray, top_k: int = 10,
                      filter_metadata: Optional[Dict[str, Any]] = None) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search for similar vectors in Qdrant.

        Args:
            query_vector: Query vector
            top_k: Number of similar vectors to return
            filter_metadata: Optional metadata filters

        Returns:
            List of (id, score, metadata) tuples
        """
        # Build filter if provided
        filter_obj = None
        if filter_metadata:
            must_conditions = []
            for key, value in filter_metadata.items():
                must_conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value)
                    )
                )
            filter_obj = models.Filter(must=must_conditions)

        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector.tolist(),
            limit=top_k,
            query_filter=filter_obj
        )

        results = []
        for scored_point in search_result:
            # Extract original ID from payload
            original_id = scored_point.payload.get("_id", str(scored_point.id))
            metadata = {k: v for k, v in scored_point.payload.items() if k != "_id"}
            results.append((
                original_id,
                scored_point.score,
                metadata
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
            # Convert string IDs to integer IDs
            point_ids = [hash(vec_id) % (2**63) for vec_id in ids]

            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=point_ids
                )
            )
            logger.info(f"Deleted {len(ids)} vectors from Qdrant")
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
            point_id = hash(vector_id) % (2**63)
            payload = new_metadata if new_metadata is not None else {}
            payload["_id"] = vector_id

            self.client.upsert(
                collection_name=self.collection_name,
                points=[models.PointStruct(
                    id=point_id,
                    vector=new_vector.tolist(),
                    payload=payload
                )]
            )
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
            point_id = hash(vector_id) % (2**63)
            points = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[point_id]
            )

            if points:
                point = points[0]
                metadata = {k: v for k, v in point.payload.items() if k != "_id"}
                return (
                    np.array(point.vector),
                    metadata
                )
            return None
        except Exception as e:
            logger.error(f"Error fetching vector {vector_id}: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics.

        Returns:
            Dictionary with collection statistics
        """
        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                'total_vectors': collection_info.points_count,
                'dimension': self.dimension,
                'collection_name': self.collection_name,
                'distance': self.distance
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}

    def clear_database(self) -> None:
        """Clear all vectors from the collection."""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.Filter()  # Empty filter matches all
            )
            logger.info(f"Cleared all vectors from collection {self.collection_name}")
        except Exception as e:
            logger.error(f"Error clearing database: {e}")

    def create_collection(self, collection_name: str, dimension: int,
                         distance: str = "Cosine", **kwargs) -> bool:
        """
        Create a new collection.

        Args:
            collection_name: Name of the collection
            dimension: Vector dimension
            distance: Distance metric
            **kwargs: Additional parameters

        Returns:
            True if collection creation was successful
        """
        try:
            distance_map = {
                "Cosine": Distance.COSINE,
                "Euclid": Distance.EUCLID,
                "Dot": Distance.DOT
            }

            if not self.client.collection_exists(collection_name):
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=dimension,
                        distance=distance_map.get(distance, Distance.COSINE)
                    ),
                    **kwargs
                )
                logger.info(f"Created new collection: {collection_name}")
                return True
            else:
                logger.warning(f"Collection {collection_name} already exists")
                return False
        except Exception as e:
            logger.error(f"Error creating collection {collection_name}: {e}")
            return False

    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection.

        Args:
            collection_name: Name of the collection to delete

        Returns:
            True if deletion was successful
        """
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection {collection_name}: {e}")
            return False