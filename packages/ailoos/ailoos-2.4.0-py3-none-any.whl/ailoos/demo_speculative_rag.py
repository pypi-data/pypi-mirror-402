#!/usr/bin/env python3
"""
Demo script for Speculative RAG

This script demonstrates the Speculative RAG technique, which generates multiple
response drafts in parallel, retrieves additional evidence for each draft, and
uses verification agents to select the optimal response.
"""

import sys
import time

sys.path.insert(0, 'src')

from ailoos.rag.techniques.speculative_rag import SpeculativeRAG
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


def setup_speculative_rag():
    """Set up SpeculativeRAG with sample configuration."""
    config = {
        'retriever_config': {'chunk_size': 500, 'chunk_overlap': 50},
        'generator_config': {'use_mock': True},
        'evaluator_config': {},
        'speculative_config': {
            'num_candidates': 3,
            'verification_agents': 2,
            'evidence_retrieval': True,
            'selection_threshold': 0.7
        }
    }

    rag = SpeculativeRAG(config)
    sample_docs = create_sample_documents()
    rag.retriever.add_documents(sample_docs)

    logger.info(f"SpeculativeRAG initialized with {len(sample_docs)} documents")
    return rag


def demonstrate_speculative_rag(rag: SpeculativeRAG):
    """Demonstrate speculative RAG functionality."""
    print("="*60)
    print("SPECULATIVE RAG DEMONSTRATION")
    print("="*60)

    query = "What is the relationship between AI and machine learning?"

    print(f"Query: {query}")
    print("Generating multiple candidates with evidence retrieval...")

    start_time = time.time()
    result = rag.run(query)
    processing_time = time.time() - start_time

    print(f"\nSelected Response: {result['response']}")

    print("\nMetrics:")
    for key, value in result['metrics'].items():
        print(f"  - {key}: {value:.3f}")

    print("\nSpeculative Metadata:")
    meta = result['metadata']
    print(f"  - Candidates generated: {meta['candidates_generated']}")
    print(f"  - Selected candidate score: {meta['selected_candidate_score']:.3f}")
    print(f"  - Evidence retrievals: {meta['evidence_retrievals']}")
    print(f"  - Processing time: {processing_time:.2f}s")

    print("\nCandidate Scores:")
    for score_info in meta['candidate_scores']:
        print(f"  - Candidate {score_info['candidate_id']}: {score_info['overall_score']:.3f}")

    print("\nSpeculative Metrics:")
    spec_metrics = rag.get_speculative_metrics()
    for key, value in spec_metrics.items():
        print(f"  - {key}: {value}")


def main():
    """Main demonstration function."""
    print("Speculative RAG Demo")
    print("Features: Parallel generation, evidence retrieval, multi-agent verification")

    try:
        rag = setup_speculative_rag()
        demonstrate_speculative_rag(rag)
        print("\nDemo completed successfully!")

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()