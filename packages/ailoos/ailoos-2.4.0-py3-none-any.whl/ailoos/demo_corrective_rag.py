#!/usr/bin/env python3
"""
Demo script for Corrective RAG

This script demonstrates the Corrective RAG technique, which implements
iterative self-correction loops with confidence-based adjustments to improve
retrieval and generation quality.

Usage:
    python demo_corrective_rag.py

Features demonstrated:
- Iterative correction loops
- Confidence-based retrieval adjustments
- Self-evaluation and refinement
- Comprehensive correction metrics
- Error handling and fallback mechanisms
"""

import sys
import time
from typing import Dict, Any

# Add the src directory to the path
sys.path.insert(0, 'src')

from ailoos.rag.techniques.corrective_rag import CorrectiveRAG
from ailoos.rag.core.retrievers import VectorRetriever
from ailoos.rag.core.generators import EmpoorioLMGenerator
from ailoos.rag.core.evaluators import BasicRAGEvaluator
from ailoos.utils.logging import get_logger

logger = get_logger(__name__)


def create_sample_documents():
    """Create sample documents for demonstration."""
    return [
        {
            "content": """
            Artificial Intelligence (AI) is a branch of computer science that aims to create
            machines capable of intelligent behavior. AI systems can learn from data,
            recognize patterns, make decisions, and solve complex problems that typically
            require human intelligence.

            The field encompasses various subdomains including machine learning, natural
            language processing, computer vision, robotics, and expert systems. AI has
            applications in healthcare, finance, transportation, entertainment, and many
            other sectors.
            """,
            "metadata": {
                "title": "Introduction to Artificial Intelligence",
                "author": "AI Research Institute",
                "topic": "AI Fundamentals",
                "source": "academic",
                "year": 2023
            }
        },
        {
            "content": """
            Machine Learning is a subset of artificial intelligence that enables systems
            to automatically learn and improve from experience without being explicitly
            programmed. ML algorithms build mathematical models based on training data
            to make predictions or decisions.

            There are three main types of machine learning:
            1. Supervised Learning: Uses labeled training data
            2. Unsupervised Learning: Finds patterns in unlabeled data
            3. Reinforcement Learning: Learns through interaction with environment

            Deep learning, a subset of ML using neural networks, has revolutionized
            fields like image recognition, speech processing, and natural language understanding.
            """,
            "metadata": {
                "title": "Machine Learning Fundamentals",
                "author": "ML Research Group",
                "topic": "Machine Learning",
                "source": "academic",
                "year": 2023
            }
        },
        {
            "content": """
            Natural Language Processing (NLP) combines computational linguistics with
            statistical and machine learning models to give computers the ability to
            process and understand human language. NLP enables machines to read,
            decipher, understand, and make sense of human language.

            Key NLP applications include:
            - Text classification and sentiment analysis
            - Machine translation
            - Speech recognition
            - Chatbots and virtual assistants
            - Information extraction and summarization

            Recent advances in transformer architectures like BERT and GPT have
            significantly improved NLP capabilities.
            """,
            "metadata": {
                "title": "Natural Language Processing",
                "author": "NLP Center",
                "topic": "NLP",
                "source": "academic",
                "year": 2024
            }
        },
        {
            "content": """
            Computer Vision is a field of AI that trains computers to interpret and
            understand visual information from the world. CV systems can identify objects,
            people, scenes, and activities in images and videos.

            Core techniques include:
            - Image classification
            - Object detection and localization
            - Image segmentation
            - Facial recognition
            - Optical character recognition (OCR)

            Convolutional Neural Networks (CNNs) are the foundation of modern
            computer vision systems, enabling breakthroughs in autonomous vehicles,
            medical imaging, and surveillance.
            """,
            "metadata": {
                "title": "Computer Vision Technology",
                "author": "CV Research Lab",
                "topic": "Computer Vision",
                "source": "academic",
                "year": 2024
            }
        }
    ]


def setup_corrective_rag():
    """Set up CorrectiveRAG with sample configuration."""
    config = {
        'retriever_config': {
            'chunk_size': 500,
            'chunk_overlap': 50
        },
        'generator_config': {
            'empoorio_api_config': {
                'model_path': 'TinyLlama/TinyLlama-1.1B-Chat-v1.0'
            },
            'generation_config': {
                'max_new_tokens': 512,
                'temperature': 0.7,
                'top_p': 0.9
            }
        },
        'evaluator_config': {},
        'correction_config': {
            'max_iterations': 3,
            'confidence_threshold': 0.7,
            'relevance_threshold': 0.5,
            'factuality_threshold': 0.6,
            'adaptive_retrieval': True,
            'correction_enabled': True
        }
    }

    # Create RAG instance
    rag = CorrectiveRAG(config)

    # Add sample documents
    sample_docs = create_sample_documents()
    rag.retriever.add_documents(sample_docs)

    logger.info(f"✅ CorrectiveRAG initialized with {len(sample_docs)} sample documents")
    return rag


def demonstrate_basic_query(rag: CorrectiveRAG):
    """Demonstrate a basic query that may need correction."""
    print("\n" + "="*60)
    print("🔍 DEMO 1: Basic Query with Potential Corrections")
    print("="*60)

    query = "What are the main branches of artificial intelligence?"

    print(f"Query: {query}")
    print("\nProcessing with Corrective RAG...")

    start_time = time.time()
    result = rag.run(query)
    processing_time = time.time() - start_time

    print("\n📄 Response:")
    print(result['response'])

    print("\n📊 Metrics:")
    for key, value in result['metrics'].items():
        print(f"  - {key}: {value:.3f}")

    print("\n🔧 Correction Metadata:")
    metadata = result['metadata']
    print(f"  - Total Iterations: {metadata['total_iterations']}")
    print(f"  - Final Confidence: {metadata['final_confidence']:.3f}")
    print(f"  - Processing Time: {processing_time:.2f}s")

    correction_metrics = metadata['correction_metrics']
    print(f"  - Corrections Applied: {correction_metrics['corrections_applied']}")
    print(f"  - Retrieval Adjustments: {correction_metrics['retrieval_adjustments']}")

    if metadata['correction_history']:
        print(f"  - Correction Iterations: {len(metadata['correction_history'])}")
        for i, correction in enumerate(metadata['correction_history']):
            print(f"    Iteration {correction['iteration']}: {correction['corrections_applied']}")


def demonstrate_complex_query(rag: CorrectiveRAG):
    """Demonstrate a complex query requiring multiple corrections."""
    print("\n" + "="*60)
    print("🔍 DEMO 2: Complex Query with Multiple Corrections")
    print("="*60)

    query = "Explain how machine learning and computer vision work together in autonomous vehicles, including specific techniques and challenges."

    print(f"Query: {query}")
    print("\nProcessing with Corrective RAG (this may take longer due to corrections)...")

    start_time = time.time()
    result = rag.run(query)
    processing_time = time.time() - start_time

    print("\n📄 Response:")
    print(result['response'][:500] + "..." if len(result['response']) > 500 else result['response'])

    print("\n📊 Metrics:")
    for key, value in result['metrics'].items():
        print(f"  - {key}: {value:.3f}")

    print("\n🔧 Correction Details:")
    metadata = result['metadata']
    print(f"  - Iterations Performed: {metadata['total_iterations']}")
    print(f"  - Final Confidence: {metadata['final_confidence']:.3f}")
    print(f"  - Total Processing Time: {processing_time:.2f}s")

    if metadata['correction_history']:
        print("  - Correction History:")
        for correction in metadata['correction_history']:
            print(f"    • Iteration {correction['iteration']}: "
                  f"Confidence {correction['old_confidence']:.2f} → {correction['new_confidence']:.2f}, "
                  f"Changes: {correction['corrections_applied']}")


def demonstrate_correction_metrics(rag: CorrectiveRAG):
    """Demonstrate comprehensive correction metrics."""
    print("\n" + "="*60)
    print("📈 DEMO 3: Correction Metrics Overview")
    print("="*60)

    # Run multiple queries to build metrics
    queries = [
        "What is AI?",
        "Explain machine learning algorithms.",
        "How does computer vision work?",
        "What are NLP applications?"
    ]

    print("Running multiple queries to demonstrate metrics accumulation...")

    for i, query in enumerate(queries, 1):
        print(f"  {i}. Processing: {query[:50]}...")
        result = rag.run(query)
        print(f"     → {result['metadata']['total_iterations']} iterations, "
              f"confidence: {result['metadata']['final_confidence']:.2f}")

    # Display accumulated metrics
    print("\n📊 Accumulated Correction Metrics:")
    metrics = rag.get_correction_metrics()
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"  - {key}: {value:.3f}")
        else:
            print(f"  - {key}: {value}")


def demonstrate_error_handling(rag: CorrectiveRAG):
    """Demonstrate error handling and fallback mechanisms."""
    print("\n" + "="*60)
    print("🛡️ DEMO 4: Error Handling and Fallback")
    print("="*60)

    # Temporarily break the retriever to simulate an error
    original_search = rag.retriever.search
    rag.retriever.search = lambda *args, **kwargs: (_ for _ in ()).throw(Exception("Simulated retrieval error"))

    query = "What is artificial intelligence?"

    print(f"Query: {query}")
    print("Simulating retrieval error...")

    try:
        result = rag.run(query)
        print("✅ System handled error gracefully")
        print(f"Response received: {len(result['response'])} characters")
        print(f"Fallback activated: {result['metadata']['correction_metrics']['fallback_activations']} times")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    # Restore original retriever
    rag.retriever.search = original_search


def main():
    """Main demonstration function."""
    print("🤖 Corrective RAG Demonstration")
    print("="*60)
    print("This demo showcases the Corrective RAG technique with:")
    print("• Iterative self-correction loops")
    print("• Confidence-based retrieval adjustments")
    print("• Comprehensive correction metrics")
    print("• Error handling and fallback mechanisms")
    print()

    try:
        # Set up the system
        rag = setup_corrective_rag()

        # Run demonstrations
        demonstrate_basic_query(rag)
        demonstrate_complex_query(rag)
        demonstrate_correction_metrics(rag)
        demonstrate_error_handling(rag)

        print("\n" + "="*60)
        print("✅ Corrective RAG demonstration completed successfully!")
        print("="*60)

        # Display final pipeline info
        print("\n🔧 Final Pipeline Information:")
        info = rag.get_pipeline_info()
        print(f"  - Technique: {info['technique']}")
        print(f"  - Description: {info['description']}")
        print(f"  - Max Iterations: {info['correction_config']['max_iterations']}")
        print(f"  - Confidence Threshold: {info['correction_config']['confidence_threshold']}")

    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        print(f"\n❌ Demonstration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()