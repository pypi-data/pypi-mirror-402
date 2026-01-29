"""
Concrete Retriever Implementations

This module contains concrete implementations of the Retriever component
for different retrieval strategies and vector stores.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
import numpy as np

from .preprocessing import DocumentPreprocessingPipeline, DocumentPreprocessingConfig, DeduplicationStep
from .retriever import Retriever
from ..utils.embedding_utils import EmbeddingUtils
from ..utils.text_splitter import TextSplitter
from ..vector_stores.faiss_store import FAISSStore

logger = logging.getLogger(__name__)


class VectorRetriever(Retriever):
    """
    Vector-based retriever using embeddings and similarity search.

    This retriever combines text chunking, embedding generation, and
    vector similarity search for efficient document retrieval.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize vector retriever.

        Args:
            config (Dict[str, Any]): Configuration containing:
                - embedding_config: Configuration for embedding utils
                - vector_store_config: Configuration for vector store
                - text_splitter_config: Configuration for text splitting
                - deduplication_config: Configuration for document deduplication
        """
        super().__init__(config)

        # Initialize components
        self.embedding_utils = EmbeddingUtils(config.get('embedding_config', {}))
        self.text_splitter = TextSplitter(config.get('text_splitter_config', {}))
        self.vector_store = FAISSStore(config.get('vector_store_config', {}))

        # Document storage
        self.document_chunks = []  # Store chunked documents

        # Initialize deduplication if configured
        deduplication_config = config.get('deduplication_config', {})
        self.document_preprocessing_pipeline = None

        if deduplication_config.get('enabled', False):
            from ..core.deduplication import create_document_deduplicator

            # Create deduplicator
            deduplicator = create_document_deduplicator(
                ipfs_endpoint=deduplication_config.get('ipfs_endpoint', "http://localhost:5001/api/v0"),
                node_id=deduplication_config.get('node_id', f"node_{id(self)}")
            )

            # Create preprocessing pipeline with deduplication
            preprocessing_config = DocumentPreprocessingConfig()
            preprocessing_config.add_step(DeduplicationStep(deduplicator))
            self.document_preprocessing_pipeline = DocumentPreprocessingPipeline(preprocessing_config)

            logger.info("Document deduplication enabled in VectorRetriever")

        logger.info("VectorRetriever initialized")

    def search(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None,
               threshold: Optional[float] = None) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search for relevant documents using vector similarity.

        Args:
            query (str): Search query
            top_k (int): Number of results to return
            filters (Optional[Dict[str, Any]]): Metadata filters
            threshold (Optional[float]): Similarity threshold

        Returns:
            List[Tuple[Dict[str, Any], float]]: (document, score) pairs
        """
        try:
            # Get query embedding
            query_embedding = self.embedding_utils.encode_text(query)

            # Search in vector store
            results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                filters=filters,
                threshold=threshold
            )

            logger.debug(f"Vector search returned {len(results)} results for query: {query[:50]}...")
            return results

        except Exception as e:
            logger.error(f"Error in vector search: {str(e)}")
            raise

    async def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Add documents to the retriever (preprocess, chunk and index).

        Args:
            documents (List[Dict[str, Any]]): Documents to add
        """
        try:
            # Apply document preprocessing pipeline if enabled
            if self.document_preprocessing_pipeline:
                preprocessing_result = await self.document_preprocessing_pipeline.preprocess_documents(documents)
                processed_documents = preprocessing_result['processed_documents']
                skipped_count = preprocessing_result['duplicate_count']

                logger.info(f"Preprocessing completado: {len(processed_documents)} documentos procesados, {skipped_count} duplicados omitidos")
            else:
                processed_documents = documents

            # Split documents into chunks
            all_chunks = self.text_splitter.split_documents(processed_documents)

            # Generate embeddings for chunks
            texts = [chunk['content'] for chunk in all_chunks]
            embeddings = self.embedding_utils.encode_batch(texts)

            # Add to vector store
            self.vector_store.add_documents(all_chunks, embeddings)

            # Store chunks for reference
            self.document_chunks.extend(all_chunks)

            logger.info(f"Added {len(processed_documents)} documents ({len(all_chunks)} chunks) to vector retriever")

        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise

    def remove_documents(self, document_ids: List[str]) -> None:
        """
        Remove documents from the retriever.

        Args:
            document_ids (List[str]): IDs of documents to remove
        """
        try:
            self.vector_store.remove_documents(document_ids)

            # Remove from chunk storage
            self.document_chunks = [
                chunk for chunk in self.document_chunks
                if chunk.get('metadata', {}).get('document_id') not in document_ids
            ]

            logger.info(f"Removed documents: {document_ids}")

        except Exception as e:
            logger.error(f"Error removing documents: {str(e)}")
            raise

    def get_retriever_stats(self) -> Dict[str, Any]:
        """Get statistics about the retriever."""
        return {
            'total_chunks': len(self.document_chunks),
            'embedding_model': self.embedding_utils.get_utils_stats(),
            'vector_store': self.vector_store.get_stats(),
            'text_splitter': self.text_splitter.get_splitter_stats()
        }

    def save_index(self, filepath: Optional[str] = None) -> None:
        """Save the vector index."""
        self.vector_store.save_index(filepath)

    def load_index(self, filepath: Optional[str] = None) -> None:
        """Load the vector index."""
        self.vector_store.load_index(filepath)


class HybridRetriever(Retriever):
    """
    Hybrid retriever combining multiple retrieval strategies.

    This retriever can combine vector similarity search with other
    retrieval methods like BM25 or keyword matching.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Initialize vector retriever
        self.vector_retriever = VectorRetriever(config)

        # Additional retrieval methods can be added here
        self.bm25_retriever = None  # Placeholder for BM25

        # Fusion weights
        self.vector_weight = config.get('vector_weight', 0.7)
        self.bm25_weight = config.get('bm25_weight', 0.3)

    def search(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None,
               threshold: Optional[float] = None) -> List[Tuple[Dict[str, Any], float]]:
        """
        Hybrid search combining multiple retrieval methods.

        Args:
            query (str): Search query
            top_k (int): Number of results to return
            filters (Optional[Dict[str, Any]]): Metadata filters
            threshold (Optional[float]): Similarity threshold

        Returns:
            List[Tuple[Dict[str, Any], float]]: Fused results
        """
        try:
            # Get vector search results
            vector_results = self.vector_retriever.search(query, top_k=top_k*2, filters=filters)

            # For now, just return vector results
            # TODO: Implement BM25 and result fusion
            results = vector_results[:top_k]

            logger.debug(f"Hybrid search returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Error in hybrid search: {str(e)}")
            raise

    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Add documents to all retrievers."""
        self.vector_retriever.add_documents(documents)
        # TODO: Add to BM25 retriever

    def remove_documents(self, document_ids: List[str]) -> None:
        """Remove documents from all retrievers."""
        self.vector_retriever.remove_documents(document_ids)
        # TODO: Remove from BM25 retriever