"""
Vector Manager Module
Main manager for vector database operations.
"""

from typing import Dict, List, Any, Optional, Union, Tuple
from .pinecone_integration import PineconeIntegration
from .qdrant_integration import QdrantIntegration
from .embedding_manager import EmbeddingManager
from .similarity_search import SimilaritySearch
from .vector_indexer import VectorIndexer
import logging
import numpy as np

logger = logging.getLogger(__name__)


class VectorManager:
    """
    Main vector database manager that orchestrates all vector operations.
    Supports multiple vector database backends (Pinecone, Qdrant).
    """

    def __init__(self, backend: str = "pinecone", **kwargs):
        """
        Initialize the vector manager.

        Args:
            backend: Vector database backend ('pinecone' or 'qdrant')
            **kwargs: Backend-specific configuration parameters
        """
        self.backend = backend
        self.embedding_manager = EmbeddingManager()
        self.similarity_search = SimilaritySearch()
        self.vector_indexer = VectorIndexer()

        if backend == "pinecone":
            self.integration = PineconeIntegration(**kwargs)
        elif backend == "qdrant":
            self.integration = QdrantIntegration(**kwargs)
        else:
            raise ValueError(f"Unsupported backend: {backend}")

        self._initialized = True
        logger.info(f"VectorManager initialized with {backend} backend")

    def close(self) -> None:
        """Close all connections and cleanup resources."""
        if hasattr(self, 'integration') and self.integration:
            self.integration.close()
        self._initialized = False
        logger.info("VectorManager closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def insert_vectors(self, vectors: List[np.ndarray], metadata: Optional[List[Dict[str, Any]]] = None,
                      ids: Optional[List[str]] = None) -> List[str]:
        """
        Insert vectors into the database.

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

        return self.integration.insert_vectors(vectors, metadata, ids)

    def search_similar(self, query_vector: np.ndarray, top_k: int = 10,
                      filter_metadata: Optional[Dict[str, Any]] = None) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search for similar vectors.

        Args:
            query_vector: Query vector
            top_k: Number of similar vectors to return
            filter_metadata: Optional metadata filters

        Returns:
            List of (id, score, metadata) tuples
        """
        return self.similarity_search.search(self.integration, query_vector, top_k, filter_metadata)

    def delete_vectors(self, ids: List[str]) -> bool:
        """
        Delete vectors by IDs.

        Args:
            ids: List of vector IDs to delete

        Returns:
            True if deletion was successful
        """
        return self.integration.delete_vectors(ids)

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
        return self.integration.update_vector(vector_id, new_vector, new_metadata)

    def get_vector(self, vector_id: str) -> Optional[Tuple[np.ndarray, Dict[str, Any]]]:
        """
        Retrieve a vector by ID.

        Args:
            vector_id: Vector ID

        Returns:
            Tuple of (vector, metadata) or None if not found
        """
        return self.integration.get_vector(vector_id)

    def batch_insert(self, vectors: List[np.ndarray], metadata: Optional[List[Dict[str, Any]]] = None,
                    ids: Optional[List[str]] = None, batch_size: int = 100) -> List[str]:
        """
        Insert vectors in batches for better performance.

        Args:
            vectors: List of vectors to insert
            metadata: Optional metadata for each vector
            ids: Optional custom IDs for vectors
            batch_size: Size of each batch

        Returns:
            List of all inserted vector IDs
        """
        if metadata is None:
            metadata = [{}] * len(vectors)
        if ids is None:
            ids = [f"vec_{i}" for i in range(len(vectors))]

        all_ids = []
        for i in range(0, len(vectors), batch_size):
            batch_vectors = vectors[i:i + batch_size]
            batch_metadata = metadata[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]

            batch_result = self.insert_vectors(batch_vectors, batch_metadata, batch_ids)
            all_ids.extend(batch_result)

        return all_ids

    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with database statistics
        """
        return self.integration.get_stats()

    def clear_database(self) -> None:
        """Clear all vectors from the database."""
        self.integration.clear_database()

    def create_index(self, index_name: str, dimension: int,
                    metric: str = "cosine", **kwargs) -> bool:
        """
        Create a new vector index.

        Args:
            index_name: Name of the index
            dimension: Vector dimension
            metric: Distance metric ('cosine', 'euclidean', 'dotproduct')
            **kwargs: Additional index parameters

        Returns:
            True if index creation was successful
        """
        return self.vector_indexer.create_index(self.integration, index_name, dimension, metric, **kwargs)

    def optimize_index(self, index_name: str) -> bool:
        """
        Optimize an existing index.

        Args:
            index_name: Name of the index to optimize

        Returns:
            True if optimization was successful
        """
        return self.vector_indexer.optimize_index(self.integration, index_name)

    def embed_text(self, texts: Union[str, List[str]], model: str = "default") -> Union[np.ndarray, List[np.ndarray]]:
        """
        Generate embeddings for text.

        Args:
            texts: Text or list of texts to embed
            model: Embedding model to use

        Returns:
            Embedding vector(s)
        """
        return self.embedding_manager.embed_text(texts, model)

    def embed_and_insert(self, texts: List[str], metadata: Optional[List[Dict[str, Any]]] = None,
                        ids: Optional[List[str]] = None, model: str = "default") -> List[str]:
        """
        Generate embeddings and insert them into the database.

        Args:
            texts: List of texts to embed and insert
            metadata: Optional metadata for each text
            ids: Optional custom IDs
            model: Embedding model to use

        Returns:
            List of inserted vector IDs
        """
        embeddings = self.embedding_manager.embed_text(texts, model)
        if isinstance(embeddings, np.ndarray) and len(texts) == 1:
            embeddings = [embeddings]

        return self.insert_vectors(embeddings, metadata, ids)

    def search_by_text(self, query_text: str, top_k: int = 10,
                      filter_metadata: Optional[Dict[str, Any]] = None,
                      model: str = "default") -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search for similar vectors using text query.

        Args:
            query_text: Text query
            top_k: Number of results to return
            filter_metadata: Optional metadata filters
            model: Embedding model to use

        Returns:
            List of (id, score, metadata) tuples
        """
        query_embedding = self.embedding_manager.embed_text(query_text, model)
        return self.search_similar(query_embedding, top_k, filter_metadata)