#!/usr/bin/env python3
"""
Demo script for Self RAG

This script demonstrates the Self-RAG technique, which dynamically decides
whether retrieval is needed based on internal confidence assessment.
"""

import sys
import time

sys.path.insert(0, 'src')

from ailoos.rag.techniques.self_rag import SelfRAG
from ailoos.utils.logging import get_logger

logger = get_logger(__name__)


def create_sample_documents():
    """Create sample documents for demonstration."""
    return [
        {
            "content": "AI is a field of computer science focused on creating intelligent machines.",
            "metadata": {"topic": "AI", "source": "academic"}
        },
        {
            "content": "Machine learning enables computers to learn without explicit programming.",
            "metadata": {"topic": "ML", "source": "academic"}
        },
        {
            "content": "Deep learning uses neural networks with multiple layers.",
            "metadata": {"topic": "DL", "source": "academic"}
        }
    ]


def setup_self_rag():
    """Set up SelfRAG with sample configuration."""
    config = {
        'retriever_config': {'chunk_size': 500, 'chunk_overlap': 50},
        'generator_config': {'use_mock': True},
        'evaluator_config': {},
        'reflection_config': {
            'enable_self_assessment': True,
            'confidence_threshold': 0.6,
            'force_retrieval_for_complex_queries': True
        }
    }

    rag = SelfRAG(config)
    sample_docs = create_sample_documents()
    rag.retriever.add_documents(sample_docs)

    logger.info(f"SelfRAG initialized with {len(sample_docs)} documents")
    return rag


def demonstrate_self_rag(rag: SelfRAG):
    """Demonstrate self-reflective RAG functionality."""
    print("="*60)
    print("SELF RAG DEMONSTRATION")
    print("="*60)

    # Test queries with different confidence levels
    queries = [
        "What is AI?",  # Should have high confidence, avoid retrieval
        "Explain the relationship between machine learning and deep learning in detail.",  # Complex, should retrieve
    ]

    for i, query in enumerate(queries, 1):
        print(f"\nQuery {i}: {query}")

        start_time = time.time()
        result = rag.run(query)
        processing_time = time.time() - start_time

        meta = result['metadata']
        retrieval_performed = meta['retrieval_performed']
        confidence = meta['confidence_assessment']['confidence']

        print(f"Retrieval performed: {retrieval_performed}")
        print(f"Confidence level: {meta['confidence_assessment']['confidence_level']} ({confidence:.3f})")
        print(f"Processing time: {processing_time:.2f}s")

        if meta.get('reflection_metadata'):
            reflection = meta['reflection_metadata']
            if reflection.get('issues_identified'):
                print(f"Issues identified: {reflection['issues_identified']}")
            if reflection.get('refinements_applied'):
                print(f"Refinements applied: {len(reflection['refinements_applied'])}")

        print(f"Response: {result['response'][:100]}...")

    # Show efficiency metrics
    print("\nEfficiency Metrics:")
    efficiency = rag._calculate_efficiency_info()
    print(f"  - Efficiency ratio: {efficiency['efficiency_ratio']:.2f}")
    print(f"  - Retrievals avoided: {efficiency['retrieval_avoided']}")
    print(f"  - Retrievals performed: {efficiency['retrieval_performed']}")
    print(f"  - Average confidence: {efficiency['average_confidence']:.3f}")


def main():
    """Main demonstration function."""
    print("Self RAG Demo")
    print("Features: Dynamic retrieval decision-making, confidence assessment, efficiency optimization")

    try:
        rag = setup_self_rag()
        demonstrate_self_rag(rag)
        print("\nDemo completed successfully!")

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()