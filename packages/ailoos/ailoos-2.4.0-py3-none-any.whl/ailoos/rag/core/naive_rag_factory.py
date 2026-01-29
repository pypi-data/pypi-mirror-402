"""
Naive RAG Factory

This module provides factory functions for creating fully functional
Naive RAG systems with sensible defaults.
"""

from typing import Dict, Any, Optional
import logging

from .retrievers import VectorRetriever
from .generators import EmpoorioLMGenerator, MockGenerator
from .evaluators import BasicRAGEvaluator
from ..techniques.naive_rag import NaiveRAG

logger = logging.getLogger(__name__)


def create_naive_rag(
    embedding_provider: str = 'local',
    embedding_model: str = 'sentence-transformers/all-MiniLM-L6-v2',
    use_mock_generator: bool = False,
    **kwargs
) -> NaiveRAG:
    """
    Create a fully functional Naive RAG system.

    Args:
        embedding_provider (str): 'openai' or 'local'
        embedding_model (str): Embedding model name
        use_mock_generator (bool): Use mock generator instead of EmpoorioLM
        **kwargs: Additional configuration options

    Returns:
        NaiveRAG: Configured and ready-to-use RAG system
    """
    # Embedding configuration
    embedding_config = {
        'provider': embedding_provider,
        'model_name': embedding_model,
        'dimension': 1536 if embedding_provider == 'openai' else 384,
        'batch_size': kwargs.get('embedding_batch_size', 32),
        'cache_config': {'max_size': kwargs.get('cache_size', 10000)}
    }

    if embedding_provider == 'openai':
        embedding_config['api_key'] = kwargs.get('openai_api_key')

    # Vector store configuration
    vector_store_config = {
        'index_type': 'IndexFlatIP',
        'dimension': embedding_config['dimension'],
        'metric': 'cosine',
        'index_file': kwargs.get('index_file', './data/rag_index.faiss')
    }

    # Text splitter configuration
    text_splitter_config = {
        'chunk_size': kwargs.get('chunk_size', 1000),
        'chunk_overlap': kwargs.get('chunk_overlap', 200),
        'separators': ['\n\n', '\n', '. ', ' ', '']
    }

    # Retriever configuration
    retriever_config = {
        'embedding_config': embedding_config,
        'vector_store_config': vector_store_config,
        'text_splitter_config': text_splitter_config
    }

    # Generator configuration
    if use_mock_generator:
        generator_config = {
            'response_templates': kwargs.get('mock_templates', [
                "Basándome en la información proporcionada, {query}",
                "Según el contexto, {query}",
                "La información indica que {query}"
            ])
        }
        generator_class = MockGenerator
    else:
        generator_config = {
            'empoorio_api_config': {
                'model_path': kwargs.get('model_path', './models/empoorio_lm/v1.0.0'),
                'device': kwargs.get('device', 'auto'),
                'max_batch_size': kwargs.get('max_batch_size', 4)
            },
            'generation_config': {
                'temperature': kwargs.get('temperature', 0.7),
                'max_tokens': kwargs.get('max_tokens', 512),
                'top_p': kwargs.get('top_p', 0.9),
                'top_k': kwargs.get('top_k', 50)
            },
            'prompt_template': kwargs.get('prompt_template',
                "Utiliza la siguiente información para responder la pregunta de manera precisa y fundamentada.\n\n"
                "Contexto:\n{context}\n\n"
                "Pregunta: {query}\n\n"
                "Respuesta:"
            )
        }
        generator_class = EmpoorioLMGenerator

    # Evaluator configuration
    evaluator_config = {
        'metrics_config': {
            'weights': {
                'relevance': 0.3,
                'faithfulness': 0.3,
                'informativeness': 0.2,
                'ground_truth_f1': 0.2
            }
        }
    }

    # Complete RAG configuration
    rag_config = {
        'retriever_class': VectorRetriever,
        'generator_class': generator_class,
        'evaluator_class': BasicRAGEvaluator,

        'retriever_config': retriever_config,
        'generator_config': generator_config,
        'evaluator_config': evaluator_config
    }

    # Create and return RAG system
    rag = NaiveRAG(rag_config)
    logger.info(f"Created Naive RAG with {embedding_provider} embeddings and {'mock' if use_mock_generator else 'EmpoorioLM'} generator")

    return rag


def create_simple_rag(
    documents: Optional[list] = None,
    use_mock: bool = True,
    **kwargs
) -> NaiveRAG:
    """
    Create a simple RAG system for quick testing.

    Args:
        documents: Optional list of documents to index
        use_mock: Use mock components for testing
        **kwargs: Additional configuration

    Returns:
        NaiveRAG: Simple RAG system
    """
    rag = create_naive_rag(
        embedding_provider='local',
        use_mock_generator=use_mock,
        **kwargs
    )

    # Add documents if provided
    if documents:
        rag.retriever.add_documents(documents)
        logger.info(f"Indexed {len(documents)} documents")

    return rag


# Convenience functions for common use cases
def create_openai_rag(api_key: str, **kwargs) -> NaiveRAG:
    """Create RAG with OpenAI embeddings."""
    return create_naive_rag(
        embedding_provider='openai',
        embedding_model='text-embedding-ada-002',
        openai_api_key=api_key,
        **kwargs
    )


def create_local_rag(**kwargs) -> NaiveRAG:
    """Create RAG with local embeddings."""
    return create_naive_rag(
        embedding_provider='local',
        **kwargs
    )


def create_mock_rag(**kwargs) -> NaiveRAG:
    """Create RAG with mock components for testing."""
    return create_naive_rag(
        use_mock_generator=True,
        **kwargs
    )