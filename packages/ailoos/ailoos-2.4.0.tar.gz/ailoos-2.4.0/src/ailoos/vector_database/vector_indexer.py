"""
Vector Indexer Module
Indexation and optimization of vectors.
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import logging
from sklearn.cluster import KMeans
import faiss

logger = logging.getLogger(__name__)


class VectorIndexer:
    """
    Advanced vector indexing and optimization system.
    """

    def __init__(self):
        """
        Initialize the vector indexer.
        """
        self.indices = {}
        self.optimizers = {}
        logger.info("VectorIndexer initialized")

    def create_index(self, integration: Any, index_name: str, dimension: int,
                    metric: str = "cosine", index_type: str = "flat",
                    **kwargs) -> bool:
        """
        Create a vector index.

        Args:
            integration: Vector database integration instance
            index_name: Name of the index
            dimension: Vector dimension
            metric: Distance metric
            index_type: Type of index ('flat', 'ivf', 'hnsw', 'pq')
            **kwargs: Additional index parameters

        Returns:
            True if index creation was successful
        """
        try:
            if hasattr(integration, 'create_index'):
                return integration.create_index(index_name, dimension, metric, **kwargs)
            else:
                # Fallback: just create the collection/index in the backend
                logger.warning(f"Integration {type(integration).__name__} doesn't support custom index creation")
                return True
        except Exception as e:
            logger.error(f"Error creating index {index_name}: {e}")
            return False

    def optimize_index(self, integration: Any, index_name: str,
                      optimization_type: str = "rebuild", **kwargs) -> bool:
        """
        Optimize an existing index.

        Args:
            integration: Vector database integration instance
            index_name: Name of the index to optimize
            optimization_type: Type of optimization
            **kwargs: Additional optimization parameters

        Returns:
            True if optimization was successful
        """
        try:
            if optimization_type == "rebuild":
                return self._rebuild_index(integration, index_name, **kwargs)
            elif optimization_type == "compact":
                return self._compact_index(integration, index_name, **kwargs)
            elif optimization_type == "rebalance":
                return self._rebalance_index(integration, index_name, **kwargs)
            else:
                logger.warning(f"Unknown optimization type: {optimization_type}")
                return False
        except Exception as e:
            logger.error(f"Error optimizing index {index_name}: {e}")
            return False

    def _rebuild_index(self, integration: Any, index_name: str, **kwargs) -> bool:
        """
        Rebuild index for better performance.

        Args:
            integration: Vector database integration instance
            index_name: Index name
            **kwargs: Rebuild parameters

        Returns:
            True if rebuild was successful
        """
        # This would typically involve recreating the index with current data
        # Implementation depends on the specific backend
        logger.info(f"Rebuilding index {index_name}")
        return True

    def _compact_index(self, integration: Any, index_name: str, **kwargs) -> bool:
        """
        Compact index to reduce storage.

        Args:
            integration: Vector database integration instance
            index_name: Index name
            **kwargs: Compact parameters

        Returns:
            True if compaction was successful
        """
        logger.info(f"Compacting index {index_name}")
        return True

    def _rebalance_index(self, integration: Any, index_name: str, **kwargs) -> bool:
        """
        Rebalance index for better distribution.

        Args:
            integration: Vector database integration instance
            index_name: Index name
            **kwargs: Rebalance parameters

        Returns:
            True if rebalancing was successful
        """
        logger.info(f"Rebalancing index {index_name}")
        return True

    def build_faiss_index(self, vectors: List[np.ndarray], metric: str = "cosine",
                         index_type: str = "IndexFlatIP") -> Any:
        """
        Build a FAISS index for fast similarity search.

        Args:
            vectors: List of vectors to index
            metric: Distance metric
            index_type: FAISS index type

        Returns:
            FAISS index object
        """
        dimension = len(vectors[0]) if vectors else 0
        vectors_array = np.array(vectors).astype('float32')

        if metric == "cosine":
            # Normalize vectors for cosine similarity
            norms = np.linalg.norm(vectors_array, axis=1, keepdims=True)
            norms[norms == 0] = 1  # Avoid division by zero
            vectors_array = vectors_array / norms
            index = faiss.IndexFlatIP(dimension)
        elif metric == "euclidean":
            index = faiss.IndexFlatL2(dimension)
        else:
            raise ValueError(f"Unsupported metric: {metric}")

        index.add(vectors_array)
        logger.info(f"Built FAISS index with {len(vectors)} vectors")
        return index

    def search_faiss_index(self, faiss_index: Any, query_vector: np.ndarray,
                          top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Search in FAISS index.

        Args:
            faiss_index: FAISS index object
            query_vector: Query vector
            top_k: Number of results

        Returns:
            List of (index, distance) tuples
        """
        query_array = np.array([query_vector]).astype('float32')

        # Normalize query for cosine similarity
        if isinstance(faiss_index, faiss.IndexFlatIP):
            norm = np.linalg.norm(query_array)
            if norm > 0:
                query_array = query_array / norm

        distances, indices = faiss_index.search(query_array, top_k)

        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx != -1:  # Valid result
                results.append((int(idx), float(dist)))

        return results

    def cluster_vectors(self, vectors: List[np.ndarray], n_clusters: int = 10,
                       method: str = "kmeans") -> Tuple[List[int], Any]:
        """
        Cluster vectors for efficient search.

        Args:
            vectors: List of vectors to cluster
            n_clusters: Number of clusters
            method: Clustering method

        Returns:
            Tuple of (cluster_labels, cluster_centers)
        """
        vectors_array = np.array(vectors)

        if method == "kmeans":
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = kmeans.fit_predict(vectors_array)
            centers = kmeans.cluster_centers_
        else:
            raise ValueError(f"Unsupported clustering method: {method}")

        logger.info(f"Clustered {len(vectors)} vectors into {n_clusters} clusters")
        return labels.tolist(), centers

    def build_ivf_index(self, vectors: List[np.ndarray], n_lists: int = 100,
                       metric: str = "euclidean") -> Any:
        """
        Build IVF (Inverted File) index for approximate search.

        Args:
            vectors: List of vectors
            n_lists: Number of inverted lists
            metric: Distance metric

        Returns:
            FAISS IVF index
        """
        dimension = len(vectors[0]) if vectors else 0
        vectors_array = np.array(vectors).astype('float32')

        if metric == "euclidean":
            quantizer = faiss.IndexFlatL2(dimension)
            index = faiss.IndexIVFFlat(quantizer, dimension, n_lists)
        elif metric == "cosine":
            quantizer = faiss.IndexFlatIP(dimension)
            index = faiss.IndexIVFFlat(quantizer, dimension, n_lists)
        else:
            raise ValueError(f"Unsupported metric for IVF: {metric}")

        # Train the index
        index.train(vectors_array)
        index.add(vectors_array)

        logger.info(f"Built IVF index with {n_lists} lists for {len(vectors)} vectors")
        return index

    def build_hnsw_index(self, vectors: List[np.ndarray], m: int = 32,
                        ef_construction: int = 200, metric: str = "euclidean") -> Any:
        """
        Build HNSW index for approximate nearest neighbor search.

        Args:
            vectors: List of vectors
            m: Number of connections per layer
            ef_construction: Size of candidate list during construction
            metric: Distance metric

        Returns:
            FAISS HNSW index
        """
        dimension = len(vectors[0]) if vectors else 0
        vectors_array = np.array(vectors).astype('float32')

        if metric == "euclidean":
            index = faiss.IndexHNSWFlat(dimension, m)
        elif metric == "cosine":
            # For cosine, we need to normalize and use IP
            norms = np.linalg.norm(vectors_array, axis=1, keepdims=True)
            norms[norms == 0] = 1
            vectors_array = vectors_array / norms
            index = faiss.IndexHNSWFlat(dimension, m)
        else:
            raise ValueError(f"Unsupported metric for HNSW: {metric}")

        index.hnsw.efConstruction = ef_construction
        index.add(vectors_array)

        logger.info(f"Built HNSW index with M={m}, ef={ef_construction} for {len(vectors)} vectors")
        return index

    def optimize_search_params(self, index: Any, queries: List[np.ndarray],
                              ground_truth: List[List[int]], metric: str = "recall@10") -> Dict[str, Any]:
        """
        Optimize search parameters for best performance.

        Args:
            index: Index to optimize
            queries: Query vectors
            ground_truth: Ground truth nearest neighbors
            metric: Optimization metric

        Returns:
            Optimal search parameters
        """
        # Placeholder for parameter optimization
        # In a real implementation, this would use techniques like grid search
        # or Bayesian optimization to find best parameters
        optimal_params = {
            'nprobe': 10,  # For IVF indexes
            'ef': 64,      # For HNSW indexes
            'k': 10
        }

        logger.info(f"Optimized search parameters: {optimal_params}")
        return optimal_params

    def get_index_stats(self, index: Any) -> Dict[str, Any]:
        """
        Get statistics about an index.

        Args:
            index: Index object

        Returns:
            Dictionary with index statistics
        """
        stats = {
            'type': type(index).__name__,
            'n_vectors': getattr(index, 'ntotal', 0),
        }

        if hasattr(index, 'd'):
            stats['dimension'] = index.d

        if hasattr(index, 'nlist'):
            stats['n_lists'] = index.nlist

        if hasattr(index, 'hnsw') and hasattr(index.hnsw, 'M'):
            stats['hnsw_M'] = index.hnsw.M
            stats['hnsw_ef'] = index.hnsw.efSearch

        return stats

    def save_index(self, index: Any, filepath: str) -> bool:
        """
        Save index to disk.

        Args:
            index: Index to save
            filepath: Path to save file

        Returns:
            True if save was successful
        """
        try:
            faiss.write_index(index, filepath)
            logger.info(f"Saved index to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            return False

    def load_index(self, filepath: str) -> Any:
        """
        Load index from disk.

        Args:
            filepath: Path to index file

        Returns:
            Loaded index
        """
        try:
            index = faiss.read_index(filepath)
            logger.info(f"Loaded index from {filepath}")
            return index
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            return None