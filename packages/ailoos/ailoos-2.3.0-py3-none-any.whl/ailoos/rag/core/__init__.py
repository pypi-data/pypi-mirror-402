"""
Core RAG Components Module

This module contains the fundamental building blocks for RAG systems:
- BaseRAG: Abstract base class for all RAG implementations
- Retriever: Component for retrieving relevant information
- Generator: Component for generating responses
- Evaluator: Component for evaluating RAG performance
- Preprocessing: Pipeline for input data preprocessing and PII filtering
- AccessControl: Document Level Access Control (DLAC) for secure retrieval
"""

from .base_rag import BaseRAG
from .retriever import Retriever
from .generator import Generator
from .evaluator import Evaluator
from .preprocessing import (
    RAGPreprocessingPipeline,
    PreprocessingConfig,
    PIIFilteringStep,
    TextNormalizationStep,
    ComplianceValidationStep
)
from .access_control import (
    AccessControlEngine,
    DocumentAccessFilter,
    AccessPolicy,
    UserContext,
    DocumentMetadata,
    AccessLevel,
    AccessDecision
)

__all__ = [
    "BaseRAG",
    "Retriever",
    "Generator",
    "Evaluator",
    "RAGPreprocessingPipeline",
    "PreprocessingConfig",
    "PIIFilteringStep",
    "TextNormalizationStep",
    "ComplianceValidationStep",
    "AccessControlEngine",
    "DocumentAccessFilter",
    "AccessPolicy",
    "UserContext",
    "DocumentMetadata",
    "AccessLevel",
    "AccessDecision",
]