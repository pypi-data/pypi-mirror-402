#!/usr/bin/env python3
"""
Script de validación independiente para esquemas JSON Schema de AILOOS.
Ejecuta validaciones sin importar el módulo completo de ailoos.
"""

import sys
import os
import json
import importlib.util
from datetime import datetime
from pathlib import Path


def load_module_from_file(module_name, filepath):
    """Cargar un módulo desde un archivo."""
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_schemas():
    """Cargar los módulos de esquemas."""
    schemas_dir = Path(__file__).parent

    # Cargar módulos base
    base_module = load_module_from_file("base_schema", schemas_dir / "base.py")
    federated_module = load_module_from_file("federated_schema", schemas_dir / "federated.py")
    rag_module = load_module_from_file("rag_schema", schemas_dir / "rag.py")
    inference_module = load_module_from_file("inference_schema", schemas_dir / "inference.py")

    return {
        "base": base_module,
        "federated": federated_module,
        "rag": rag_module,
        "inference": inference_module
    }


def get_base_response_example():
    """Ejemplo de respuesta base LLM."""
    from base_schema import BaseLLMResponseSchema
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
    from federated_schema import FederatedSessionResponseSchema
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
    from rag_schema import RAGQueryResponseSchema
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
    from inference_schema import InferenceResponseSchema
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

    # Cargar esquemas
    try:
        schemas = load_schemas()
        print("✅ Esquemas cargados exitosamente")
    except Exception as e:
        print(f"❌ Error cargando esquemas: {e}")
        return 1

    validations = []

    # Base schema
    try:
        from base_schema import BaseLLMResponseSchema
        validations.append(validate_example(BaseLLMResponseSchema, get_base_response_example, "Base Response"))
    except Exception as e:
        validations.append({
            "example": "Base Response",
            "valid": False,
            "schema_id": "unknown",
            "errors": [f"Error loading schema: {e}"]
        })

    # Federated schemas
    try:
        from federated_schema import FederatedSessionResponseSchema
        validations.append(validate_example(FederatedSessionResponseSchema, get_federated_session_example, "Federated Session"))
    except Exception as e:
        validations.append({
            "example": "Federated Session",
            "valid": False,
            "schema_id": "unknown",
            "errors": [f"Error loading schema: {e}"]
        })

    # RAG schemas
    try:
        from rag_schema import RAGQueryResponseSchema
        validations.append(validate_example(RAGQueryResponseSchema, get_rag_query_example, "RAG Query"))
    except Exception as e:
        validations.append({
            "example": "RAG Query",
            "valid": False,
            "schema_id": "unknown",
            "errors": [f"Error loading schema: {e}"]
        })

    # Inference schemas
    try:
        from inference_schema import InferenceResponseSchema
        validations.append(validate_example(InferenceResponseSchema, get_inference_response_example, "Inference Response"))
    except Exception as e:
        validations.append({
            "example": "Inference Response",
            "valid": False,
            "schema_id": "unknown",
            "errors": [f"Error loading schema: {e}"]
        })

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