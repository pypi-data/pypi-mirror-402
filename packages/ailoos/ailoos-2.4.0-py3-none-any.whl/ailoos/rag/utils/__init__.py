"""
Utils Module

This module provides utility functions and helpers for RAG operations,
including text processing, embedding management, similarity search,
and federated learning utilities.

Utilities:
- TextSplitter: Text chunking and splitting utilities
- EmbeddingUtils: Embedding generation and management
- SimilaritySearch: Vector similarity search functions
- FederatedUtils: Utilities for federated RAG operations
"""

from .text_splitter import TextSplitter
from .embedding_utils import EmbeddingUtils
from .similarity_search import SimilaritySearch
from .federated_utils import FederatedUtils

__all__ = [
    "TextSplitter",
    "EmbeddingUtils",
    "SimilaritySearch",
    "FederatedUtils",
]