"""
Embedding Utilities

This module provides utilities for generating and managing text embeddings
for RAG systems, supporting both OpenAI and local embedding models.
"""

from typing import List, Dict, Any, Optional, Union, Tuple
import logging
import os

logger = logging.getLogger(__name__)


class EmbeddingUtils:
    """
    Utilities for text embedding generation and management.

    This class provides methods for generating embeddings using OpenAI or local models,
    caching, and preprocessing text for embedding models.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize embedding utilities.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing:
                - provider: 'openai' or 'local'
                - model_name: Name of the embedding model
                - api_key: OpenAI API key (if using OpenAI)
                - dimension: Embedding dimension
                - batch_size: Batch size for processing
                - cache_config: Caching configuration
        """
        self.config = config
        self.provider = config.get('provider', 'local')
        self.model_name = config.get('model_name', 'text-embedding-ada-002' if self.provider == 'openai' else 'sentence-transformers/all-MiniLM-L6-v2')
        self.api_key = config.get('api_key', os.getenv('OPENAI_API_KEY'))
        self.dimension = config.get('dimension', 1536 if self.provider == 'openai' else 384)
        self.batch_size = config.get('batch_size', 32)
        self.cache_config = config.get('cache_config', {})

        # Initialize embedding model
        self.model = None
        self.tokenizer = None
        self.cache = {}

        self._initialize_model()
        logger.info(f"EmbeddingUtils initialized with {self.provider} provider: {self.model_name}")

    def _initialize_model(self):
        """Initialize the embedding model based on provider."""
        try:
            if self.provider == 'openai':
                self._initialize_openai()
            elif self.provider == 'local':
                self._initialize_local()
            else:
                raise ValueError(f"Unsupported embedding provider: {self.provider}")
        except Exception as e:
            logger.warning(f"Failed to initialize {self.provider} model: {e}. Using fallback.")
            self._initialize_fallback()

    def _initialize_openai(self):
        """Initialize OpenAI embeddings."""
        try:
            from openai import OpenAI
            self.model = OpenAI(api_key=self.api_key)
            logger.info("OpenAI embedding client initialized")
        except ImportError:
            raise ImportError("openai package required for OpenAI embeddings")

    def _initialize_local(self):
        """Initialize local sentence transformer model."""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Local embedding model loaded: {self.model_name}")
        except ImportError:
            raise ImportError("sentence-transformers package required for local embeddings")

    def _initialize_fallback(self):
        """Initialize fallback dummy embeddings."""
        logger.warning("Using fallback dummy embeddings")
        self.provider = 'dummy'
        self.model = None

    def encode_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text (str): Text to embed

        Returns:
            List[float]: Embedding vector
        """
        # Check cache first
        cache_key = hash(text)
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Preprocess text
        processed_text = self._preprocess_text(text)

        # Generate embedding (placeholder)
        embedding = self._generate_embedding(processed_text)

        # Cache result
        if len(self.cache) < self.cache_config.get('max_size', 10000):
            self.cache[cache_key] = embedding

        return embedding

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts (List[str]): List of texts to embed

        Returns:
            List[List[float]]: List of embedding vectors
        """
        embeddings = []

        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            processed_batch = [self._preprocess_text(text) for text in batch]

            # Generate batch embeddings (placeholder)
            batch_embeddings = self._generate_batch_embeddings(processed_batch)
            embeddings.extend(batch_embeddings)

        return embeddings

    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for embedding.

        Args:
            text (str): Raw text

        Returns:
            str: Preprocessed text
        """
        # Basic preprocessing
        text = text.strip()
        text = ' '.join(text.split())  # Normalize whitespace

        # Truncate if too long
        max_length = self.config.get('max_length', 512)
        if len(text) > max_length:
            text = text[:max_length]

        return text

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        try:
            if self.provider == 'openai':
                return self._generate_openai_embedding(text)
            elif self.provider == 'local':
                return self._generate_local_embedding(text)
            else:  # dummy
                return self._generate_dummy_embedding(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return self._generate_dummy_embedding(text)

    def _generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch of texts."""
        try:
            if self.provider == 'openai':
                return self._generate_openai_batch_embeddings(texts)
            elif self.provider == 'local':
                return self._generate_local_batch_embeddings(texts)
            else:  # dummy
                return [self._generate_dummy_embedding(text) for text in texts]
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return [self._generate_dummy_embedding(text) for text in texts]

    def _generate_openai_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI."""
        response = self.model.embeddings.create(
            input=text,
            model=self.model_name
        )
        return response.data[0].embedding

    def _generate_openai_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate batch embeddings using OpenAI."""
        response = self.model.embeddings.create(
            input=texts,
            model=self.model_name
        )
        return [data.embedding for data in response.data]

    def _generate_local_embedding(self, text: str) -> List[float]:
        """Generate embedding using local model."""
        embedding = self.model.encode(text, convert_to_numpy=False)
        return embedding.tolist()

    def _generate_local_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate batch embeddings using local model."""
        embeddings = self.model.encode(texts, convert_to_numpy=False, batch_size=self.batch_size)
        return [emb.tolist() for emb in embeddings]

    def _generate_dummy_embedding(self, text: str) -> List[float]:
        """Generate dummy embedding for fallback."""
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_int = int(hash_obj.hexdigest(), 16)

        # Generate pseudo-random but deterministic vector
        embedding = []
        for i in range(self.dimension):
            value = ((hash_int >> (i % 32)) & 1) * 2 - 1  # -1 or 1
            embedding.append(float(value))

        return embedding

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1 (List[float]): First vector
            vec2 (List[float]): Second vector

        Returns:
            float: Cosine similarity score
        """
        import math

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def find_similar_texts(self, query_embedding: List[float],
                          text_embeddings: List[List[float]],
                          top_k: int = 5) -> List[Tuple[int, float]]:
        """
        Find most similar texts to query embedding.

        Args:
            query_embedding (List[float]): Query embedding
            text_embeddings (List[List[float]]): Candidate embeddings
            top_k (int): Number of top results

        Returns:
            List[Tuple[int, float]]: List of (index, similarity) pairs
        """
        similarities = []

        for i, text_emb in enumerate(text_embeddings):
            similarity = self.cosine_similarity(query_embedding, text_emb)
            similarities.append((i, similarity))

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

    def get_utils_stats(self) -> Dict[str, Any]:
        """Get statistics about embedding utilities."""
        return {
            'model_name': self.model_name,
            'dimension': self.dimension,
            'batch_size': self.batch_size,
            'cache_size': len(self.cache),
            'max_cache_size': self.cache_config.get('max_size', 10000)
        }