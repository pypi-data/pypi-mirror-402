"""
Vector Stores Module

This module provides integrations with various vector databases
for efficient similarity search and storage in RAG systems.

Supported stores:
- FAISS: Facebook AI Similarity Search
- ChromaDB: Open-source embedding database
- Pinecone: Managed vector database service
"""

from .faiss_store import FAISSStore
from .chroma_store import ChromaStore
from .pinecone_store import PineconeStore

__all__ = [
    "FAISSStore",
    "ChromaStore",
    "PineconeStore",
]