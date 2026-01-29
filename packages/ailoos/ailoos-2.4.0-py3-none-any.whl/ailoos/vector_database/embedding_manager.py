"""
Embedding Manager Module
Manager for embeddings and transformations.
"""

from typing import Union, List, Dict, Any, Optional, Tuple
import numpy as np
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """
    Manager for generating and handling text embeddings.
    """

    def __init__(self, default_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding manager.

        Args:
            default_model: Default embedding model to use
        """
        self.default_model = default_model
        self.models = {}
        self._load_model(default_model)
        logger.info(f"EmbeddingManager initialized with default model: {default_model}")

    def _load_model(self, model_name: str) -> None:
        """
        Load an embedding model.

        Args:
            model_name: Name of the model to load
        """
        if model_name not in self.models:
            try:
                self.models[model_name] = SentenceTransformer(model_name)
                logger.info(f"Loaded embedding model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {e}")
                raise

    def embed_text(self, texts: Union[str, List[str]], model: Optional[str] = None) -> Union[np.ndarray, List[np.ndarray]]:
        """
        Generate embeddings for text.

        Args:
            texts: Text or list of texts to embed
            model: Model to use (defaults to default_model)

        Returns:
            Embedding vector(s)
        """
        model_name = model or self.default_model
        if model_name not in self.models:
            self._load_model(model_name)

        model_instance = self.models[model_name]

        if isinstance(texts, str):
            # Single text
            embedding = model_instance.encode(texts, convert_to_numpy=True)
            return embedding
        else:
            # List of texts
            embeddings = model_instance.encode(texts, convert_to_numpy=True, batch_size=32)
            return [emb for emb in embeddings]

    def embed_with_metadata(self, texts: List[str], metadata: Optional[List[Dict[str, Any]]] = None,
                           model: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate embeddings with associated metadata.

        Args:
            texts: List of texts to embed
            metadata: Optional metadata for each text
            model: Model to use

        Returns:
            List of dictionaries with 'embedding' and 'metadata' keys
        """
        embeddings = self.embed_text(texts, model)
        if isinstance(embeddings, np.ndarray):
            embeddings = [embeddings]

        if metadata is None:
            metadata = [{}] * len(texts)

        results = []
        for emb, meta in zip(embeddings, metadata):
            results.append({
                'embedding': emb,
                'metadata': meta
            })

        return results

    def get_model_info(self, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about a model.

        Args:
            model: Model name (defaults to default_model)

        Returns:
            Dictionary with model information
        """
        model_name = model or self.default_model
        if model_name not in self.models:
            self._load_model(model_name)

        model_instance = self.models[model_name]
        return {
            'name': model_name,
            'dimension': model_instance.get_sentence_embedding_dimension(),
            'max_seq_length': model_instance.get_max_seq_length(),
            'loaded': True
        }

    def list_available_models(self) -> List[str]:
        """
        List all loaded models.

        Returns:
            List of loaded model names
        """
        return list(self.models.keys())

    def unload_model(self, model: str) -> bool:
        """
        Unload a model from memory.

        Args:
            model: Model name to unload

        Returns:
            True if successfully unloaded
        """
        if model in self.models:
            del self.models[model]
            logger.info(f"Unloaded model: {model}")
            return True
        return False

    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray,
                           metric: str = "cosine") -> float:
        """
        Calculate similarity between two embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding
            metric: Similarity metric ('cosine', 'euclidean', 'dot')

        Returns:
            Similarity score
        """
        if metric == "cosine":
            # Cosine similarity
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            return dot_product / (norm1 * norm2)
        elif metric == "euclidean":
            # Convert distance to similarity (higher values = more similar)
            distance = np.linalg.norm(embedding1 - embedding2)
            return 1 / (1 + distance)
        elif metric == "dot":
            # Dot product similarity
            return np.dot(embedding1, embedding2)
        else:
            raise ValueError(f"Unsupported metric: {metric}")

    def find_most_similar(self, query_embedding: np.ndarray, embeddings: List[np.ndarray],
                         top_k: int = 5, metric: str = "cosine") -> List[Tuple[int, float]]:
        """
        Find most similar embeddings to a query.

        Args:
            query_embedding: Query embedding
            embeddings: List of embeddings to search
            top_k: Number of results to return
            metric: Similarity metric

        Returns:
            List of (index, similarity_score) tuples
        """
        similarities = []
        for i, emb in enumerate(embeddings):
            sim = self.calculate_similarity(query_embedding, emb, metric)
            similarities.append((i, sim))

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def batch_embed_and_compare(self, texts: List[str], query_text: str,
                               model: Optional[str] = None, metric: str = "cosine",
                               top_k: int = 5) -> List[Tuple[int, float]]:
        """
        Embed texts and find most similar to query.

        Args:
            texts: List of texts to embed
            query_text: Query text
            model: Model to use
            metric: Similarity metric
            top_k: Number of results

        Returns:
            List of (index, similarity_score) tuples
        """
        # Embed all texts
        embeddings = self.embed_text(texts, model)
        if isinstance(embeddings, np.ndarray):
            embeddings = [embeddings]

        # Embed query
        query_embedding = self.embed_text(query_text, model)

        # Find similarities
        return self.find_most_similar(query_embedding, embeddings, top_k, metric)

    def normalize_embeddings(self, embeddings: Union[np.ndarray, List[np.ndarray]]) -> Union[np.ndarray, List[np.ndarray]]:
        """
        Normalize embeddings to unit length.

        Args:
            embeddings: Embedding(s) to normalize

        Returns:
            Normalized embedding(s)
        """
        if isinstance(embeddings, np.ndarray) and embeddings.ndim == 1:
            # Single embedding
            return embeddings / np.linalg.norm(embeddings)
        elif isinstance(embeddings, list):
            # List of embeddings
            normalized = []
            for emb in embeddings:
                normalized.append(emb / np.linalg.norm(emb))
            return normalized
        else:
            # 2D array
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            return embeddings / norms

    def reduce_dimensions(self, embeddings: List[np.ndarray], target_dim: int = 128) -> List[np.ndarray]:
        """
        Reduce dimensionality of embeddings using PCA.

        Args:
            embeddings: List of embeddings
            target_dim: Target dimensionality

        Returns:
            Reduced embeddings
        """
        from sklearn.decomposition import PCA

        # Convert to numpy array
        emb_array = np.array(embeddings)

        # Apply PCA
        pca = PCA(n_components=min(target_dim, len(embeddings), emb_array.shape[1]))
        reduced = pca.fit_transform(emb_array)

        return [emb for emb in reduced]