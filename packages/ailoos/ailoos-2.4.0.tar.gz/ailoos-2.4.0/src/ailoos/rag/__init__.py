"""
AILOOS RAG Module

This module contains the Retrieval-Augmented Generation system components
for the AILOOS platform. It provides various RAG techniques, vector stores,
knowledge graphs, agents, and utilities for building advanced AI applications.

Modules:
- core: Base classes and core components
- techniques: Different RAG implementation techniques
- vector_stores: Vector database integrations
- knowledge_graph: Graph-based knowledge representations
- agents: AI agents for RAG operations
- api: REST and WebSocket APIs
- models: Data models and schemas
- utils: Utility functions
- config: Configuration management
- tests: Unit and integration tests
"""

__version__ = "1.0.0"

# Import main classes for easy access
from .core.base_rag import BaseRAG
from .core.retriever import Retriever
from .core.generator import Generator
from .core.evaluator import Evaluator

# Import concrete implementations
from .core.retrievers import VectorRetriever, HybridRetriever
from .core.generators import EmpoorioLMGenerator, MockGenerator
from .core.evaluators import BasicRAGEvaluator, AdvancedRAGEvaluator

# Import RAG techniques
from .techniques.naive_rag import NaiveRAG
from .techniques.corrective_rag import CorrectiveRAG
from .techniques.speculative_rag import SpeculativeRAG
from .techniques.self_rag import SelfRAG

# Import factory functions
from .core.naive_rag_factory import (
    create_naive_rag,
    create_simple_rag,
    create_openai_rag,
    create_local_rag,
    create_mock_rag
)

# Import utilities
from .utils.embedding_utils import EmbeddingUtils
from .utils.text_splitter import TextSplitter
from .vector_stores.faiss_store import FAISSStore

__all__ = [
    # Base classes
    "BaseRAG",
    "Retriever",
    "Generator",
    "Evaluator",

    # Concrete implementations
    "VectorRetriever",
    "HybridRetriever",
    "EmpoorioLMGenerator",
    "MockGenerator",
    "BasicRAGEvaluator",
    "AdvancedRAGEvaluator",

    # RAG techniques
    "NaiveRAG",
    "CorrectiveRAG",
    "SpeculativeRAG",
    "SelfRAG",

    # Factory functions
    "create_naive_rag",
    "create_simple_rag",
    "create_openai_rag",
    "create_local_rag",
    "create_mock_rag",

    # Utilities
    "EmbeddingUtils",
    "TextSplitter",
    "FAISSStore",
]