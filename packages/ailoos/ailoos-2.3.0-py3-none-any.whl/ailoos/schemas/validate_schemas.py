#!/usr/bin/env python3
"""
Script de validación para esquemas JSON Schema de AILOOS.
Ejecuta validaciones de todos los esquemas con ejemplos de uso.
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Agregar el directorio padre al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ailoos.schemas.base import BaseLLMResponseSchema
from ailoos.schemas.federated import (
    FederatedSessionResponseSchema,
    FederatedNodeResponseSchema,
    FederatedMetricsResponseSchema,
    FederatedTrainingUpdateSchema
)
from ailoos.schemas.rag import RAGQueryResponseSchema, RAGHealthResponseSchema
from ailoos.schemas.inference import InferenceResponseSchema, InferenceHealthResponseSchema
from ailoos.schemas.serialization import TOONResponseSchema, VSCResponseSchema


def get_base_response_example():
    """Ejemplo de respuesta base LLM."""
    return BaseLLMResponseSchema.create_base_response(
        response_id="550e8400-e29b-41d4-a716-446655440000",
        model_name="EmpoorioLM",
        model_version="v1.0.0",
        total_tokens=150,
        metadata={"request_type": "inference", "user_id": "user123"},
        processing_time_seconds=0.85
    )


def get_federated_session_example():
    """Ejemplo de respuesta de sesión federada."""
    return FederatedSessionResponseSchema.create_session_response(
        session_id="fed-session-001",
        model_name="EmpoorioLM-Federated",
        status="active",
        current_round=3,
        total_rounds=10,
        participants=["node-001", "node-002", "node-003"],
        min_nodes=3,
        max_nodes=10,
        privacy_budget=2.5,
        created_at=datetime.now().isoformat(),
        total_rewards_distributed=150.75
    )


def get_rag_query_example():
    """Ejemplo de respuesta de consulta RAG."""
    return RAGQueryResponseSchema.create_rag_response(
        query="¿Cómo funciona el aprendizaje federado?",
        response="El aprendizaje federado es una técnica de machine learning distribuido que permite entrenar modelos de IA en múltiples dispositivos o servidores manteniendo los datos localizados, preservando la privacidad.",
        context=[
            {
                "content": "El aprendizaje federado permite entrenar modelos de IA sin compartir datos sensibles entre dispositivos.",
                "metadata": {
                    "title": "Introducción al Federated Learning",
                    "author": "Dr. Ana García",
                    "topic": "Machine Learning",
                    "relevance_score": 0.95,
                    "source": "documento_tecnico.pdf"
                },
                "score": 0.92
            }
        ],
        rag_type="CorrectiveRAG",
        metrics={
            "retrieval_time_seconds": 0.123,
            "generation_time_seconds": 0.456,
            "total_context_tokens": 234,
            "context_chunks_count": 3,
            "relevance_score": 0.91,
            "confidence_score": 0.87,
            "cache_hit": False
        }
    )


def get_inference_response_example():
    """Ejemplo de respuesta de inferencia LLM."""
    return InferenceResponseSchema.create_inference_response(
        text="El aprendizaje automático es una rama de la inteligencia artificial que permite a los sistemas aprender y mejorar automáticamente a partir de la experiencia.",
        prompt_tokens=12,
        completion_tokens=45,
        model_name="EmpoorioLM",
        model_version="v1.0.0",
        finish_reason="stop",
        generation_metadata={
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 50,
            "max_tokens": 100
        }
    )


def validate_example(schema_class, example_func, example_name: str):
    """Validar un ejemplo contra su esquema."""
    try:
        example = example_func()
        is_valid = schema_class.validate_response(example)

        return {
            "example": example_name,
            "valid": is_valid,
            "schema_id": schema_class.get_schema().get("$id", "unknown"),
            "errors": [] if is_valid else ["Validation failed"]
        }
    except Exception as e:
        return {
            "example": example_name,
            "valid": False,
            "schema_id": "unknown",
            "errors": [str(e)]
        }


def main():
    """Función principal de validación."""
    print("🔍 Validando esquemas JSON Schema de AILOOS...")
    print("=" * 50)

    validations = []

    # Base schema
    validations.append(validate_example(BaseLLMResponseSchema, get_base_response_example, "Base Response"))

    # Federated schemas
    validations.append(validate_example(FederatedSessionResponseSchema, get_federated_session_example, "Federated Session"))

    # RAG schemas
    validations.append(validate_example(RAGQueryResponseSchema, get_rag_query_example, "RAG Query"))

    # Inference schemas
    validations.append(validate_example(InferenceResponseSchema, get_inference_response_example, "Inference Response"))

    # Serialization schemas
    # validations.append(validate_example(TOONResponseSchema, get_toon_response_example, "TOON Response"))
    # validations.append(validate_example(VSCResponseSchema, get_vsc_response_example, "VSC Response"))

    # Resumen
    total_validations = len(validations)
    successful_validations = len([v for v in validations if v["valid"]])

    print("\n📊 RESULTADOS DE VALIDACIÓN:")
    print(f"   Total de ejemplos: {total_validations}")
    print(f"   Validaciones exitosas: {successful_validations}")
    print(f"   Validaciones fallidas: {total_validations - successful_validations}")
    print(".1f")

    # Mostrar detalles
    print("\n📋 DETALLES:")
    for validation in validations:
        status = "✅" if validation["valid"] else "❌"
        print(f"   {status} {validation['example']}")
        if not validation["valid"]:
            for error in validation["errors"]:
                print(f"      - {error}")

    # Exportar resultados
    results = {
        "summary": {
            "total_examples": total_validations,
            "successful_validations": successful_validations,
            "failed_validations": total_validations - successful_validations,
            "success_rate": successful_validations / total_validations if total_validations > 0 else 0
        },
        "validations": validations,
        "timestamp": datetime.now().isoformat()
    }

    output_file = Path(__file__).parent / "validation_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Resultados guardados en: {output_file}")

    # Código de salida
    if successful_validations == total_validations:
        print("\n🎉 ¡Todas las validaciones pasaron exitosamente!")
        return 0
    else:
        print(f"\n⚠️  {total_validations - successful_validations} validaciones fallaron")
        return 1


if __name__ == "__main__":
    sys.exit(main())