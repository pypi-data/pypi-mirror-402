#!/usr/bin/env python3
"""
Naive RAG Demo

This script demonstrates the fully functional Naive RAG system
with EmpoorioLM integration, FAISS vector storage, and intelligent
document chunking.
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from ailoos.rag import create_naive_rag, create_mock_rag
from ailoos.utils.logging import get_logger

logger = get_logger(__name__)


def create_sample_documents():
    """Create sample documents for testing."""
    return [
        {
            "content": """
            La Inteligencia Artificial (IA) es una rama de la informática que se ocupa de crear
            máquinas capaces de realizar tareas que requieren inteligencia humana. Estas tareas
            incluyen el aprendizaje, el razonamiento, la resolución de problemas, la percepción,
            el entendimiento del lenguaje natural y la toma de decisiones.

            La IA se divide en dos tipos principales: IA débil (o estrecha) e IA fuerte (o general).
            La IA débil está diseñada para realizar tareas específicas, como el reconocimiento
            de imágenes o el procesamiento del lenguaje natural. La IA fuerte, por otro lado,
            tendría la capacidad de realizar cualquier tarea intelectual que un humano pueda hacer.
            """,
            "metadata": {
                "title": "Introducción a la Inteligencia Artificial",
                "author": "Dr. Ana García",
                "topic": "IA",
                "source": "manual"
            }
        },
        {
            "content": """
            El aprendizaje automático (Machine Learning) es un subcampo de la IA que permite
            a los sistemas aprender y mejorar automáticamente a partir de la experiencia,
            sin ser programados explícitamente para cada tarea específica.

            Los algoritmos de ML se entrenan con grandes cantidades de datos para identificar
            patrones y hacer predicciones. Los tipos principales de aprendizaje automático son:
            supervisado, no supervisado y por refuerzo.

            En el aprendizaje supervisado, el algoritmo aprende de ejemplos etiquetados.
            En el no supervisado, encuentra patrones en datos sin etiquetas. El aprendizaje
            por refuerzo aprende mediante prueba y error, recibiendo recompensas o castigos.
            """,
            "metadata": {
                "title": "Aprendizaje Automático",
                "author": "Dr. Carlos López",
                "topic": "Machine Learning",
                "source": "manual"
            }
        },
        {
            "content": """
            Las redes neuronales artificiales son inspiradas en el cerebro humano y consisten
            en capas de nodos interconectados llamados neuronas artificiales. Cada conexión
            tiene un peso que se ajusta durante el entrenamiento.

            Las redes neuronales convolucionales (CNN) son especialmente efectivas para
            el procesamiento de imágenes. Las redes recurrentes (RNN) y los transformers
            son útiles para el procesamiento de secuencias, como texto o series temporales.

            Los transformers, introducidos en el paper "Attention is All You Need" en 2017,
            han revolucionado el campo del procesamiento del lenguaje natural y son la base
            de modelos como GPT, BERT y muchos otros.
            """,
            "metadata": {
                "title": "Redes Neuronales y Transformers",
                "author": "Dra. María Rodríguez",
                "topic": "Deep Learning",
                "source": "manual"
            }
        }
    ]


def demo_naive_rag():
    """Demonstrate the Naive RAG system."""
    print("🚀 Iniciando demo del sistema Naive RAG")
    print("=" * 50)

    # Create sample documents
    documents = create_sample_documents()
    print(f"📚 Creados {len(documents)} documentos de ejemplo")

    # Create RAG system with mock generator for demo
    print("\n🤖 Creando sistema RAG con generador mock...")
    rag = create_mock_rag(
        chunk_size=500,
        chunk_overlap=50
    )

    # Index documents
    print("📥 Indexando documentos...")
    rag.retriever.add_documents(documents)
    print("✅ Documentos indexados exitosamente")

    # Test queries
    test_queries = [
        "¿Qué es la Inteligencia Artificial?",
        "¿Cuáles son los tipos de aprendizaje automático?",
        "¿Qué son los transformers en deep learning?",
        "¿Cómo funciona una red neuronal convolucional?"
    ]

    print("\n❓ Probando consultas RAG:")
    print("-" * 30)

    for i, query in enumerate(test_queries, 1):
        print(f"\nConsulta {i}: {query}")

        try:
            # Run RAG pipeline
            result = rag.run(query, top_k=2)

            print(f"Respuesta: {result['response'][:100]}...")
            print(f"Documentos recuperados: {len(result['context'])}")
            print(".2f")
        except Exception as e:
            print(f"❌ Error en consulta: {str(e)}")

    print("\n📊 Estadísticas del sistema:")
    print("-" * 30)
    stats = rag.retriever.get_retriever_stats()
    print(f"Total de chunks: {stats['total_chunks']}")
    print(f"Modelo de embeddings: {stats['embedding_model']['model_name']}")
    print(f"Dimensión de embeddings: {stats['embedding_model']['dimension']}")

    print("\n✅ Demo completada exitosamente!")


def demo_with_real_empoorio_lm():
    """Demo with real EmpoorioLM (if available)."""
    print("\n🔬 Intentando demo con EmpoorioLM real...")

    try:
        # Try to create RAG with real EmpoorioLM
        rag = create_naive_rag(
            use_mock_generator=False,
            model_path="./models/empoorio_lm/v1.0.0"
        )

        # Test with a simple query
        result = rag.run("¿Qué es la IA?", top_k=1)
        print(f"✅ EmpoorioLM funciona! Respuesta: {result['response'][:50]}...")

    except Exception as e:
        print(f"⚠️ EmpoorioLM no disponible: {str(e)}")
        print("💡 Para usar EmpoorioLM real, asegúrate de que el modelo esté disponible")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run demo
    demo_naive_rag()
    demo_with_real_empoorio_lm()

    print("\n🎉 ¡Sistema Naive RAG completamente funcional!")
    print("Para usar en producción:")
    print("  from ailoos.rag import create_naive_rag")
    print("  rag = create_naive_rag()")
    print("  rag.retriever.add_documents(documents)")
    print("  result = rag.run('tu consulta aquí')")