"""
Ejemplos de uso de esquemas JSON Schema para AILOOS.
Contiene ejemplos válidos para cada tipo de respuesta estructurada.
"""

import json
from datetime import datetime
from typing import Dict, Any

# Importar esquemas
from .base import BaseLLMResponseSchema
from .federated import (
    FederatedSessionResponseSchema,
    FederatedNodeResponseSchema,
    FederatedMetricsResponseSchema,
    FederatedTrainingUpdateSchema
)
from .rag import RAGQueryResponseSchema, RAGHealthResponseSchema, RAGEvaluationResponseSchema
from .inference import InferenceResponseSchema, InferenceHealthResponseSchema
from .serialization import TOONResponseSchema, VSCResponseSchema


# ===== EJEMPLOS DE RESPUESTAS =====

def get_base_response_example() -> Dict[str, Any]:
    """Ejemplo de respuesta base LLM."""
    return BaseLLMResponseSchema.create_base_response(
        response_id="550e8400-e29b-41d4-a716-446655440000",
        model_name="EmpoorioLM",
        model_version="v1.0.0",
        total_tokens=150,
        metadata={"request_type": "inference", "user_id": "user123"},
        processing_time_seconds=0.85
    )


def get_federated_session_example() -> Dict[str, Any]:
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


def get_federated_node_example() -> Dict[str, Any]:
    """Ejemplo de respuesta de nodo federado."""
    return FederatedNodeResponseSchema.create_node_response(
        node_id="node-001",
        status="active",
        session_id="fed-session-001",
        hardware_info={
            "cpu_cores": 8,
            "memory_gb": 16,
            "gpu_model": "RTX 3080",
            "gpu_memory_gb": 10
        },
        local_data_info={
            "dataset_size": 50000,
            "data_quality_score": 0.92,
            "privacy_level": "medium"
        },
        contributions=5,
        rewards_earned=25.50,
        reputation_score=0.95
    )


def get_federated_metrics_example() -> Dict[str, Any]:
    """Ejemplo de métricas federadas."""
    return FederatedMetricsResponseSchema.create_metrics_response(
        metrics={
            "performance": {
                "cpu_usage_percent": 65.5,
                "memory_usage_percent": 78.2,
                "network_latency_ms": 12.3,
                "performance_score": 0.87,
                "response_times_history": [10.2, 11.8, 12.3, 9.7, 13.1]
            },
            "contributions": {
                "total_contributions": 15,
                "successful_contributions": 14,
                "session_success_rate": 0.93,
                "contribution_score": 0.89,
                "average_contribution_time": 45.2
            },
            "stability": {
                "stability_score": 0.96,
                "error_rate": 0.02,
                "consecutive_failures": 0,
                "crash_count": 1
            },
            "connectivity": {
                "connectivity_score": 0.98,
                "uptime_ratio": 0.997,
                "last_seen": datetime.now().isoformat(),
                "response_time_ms": 8.5
            }
        },
        node_id="node-001",
        aggregation_level="node"
    )


def get_federated_training_update_example() -> Dict[str, Any]:
    """Ejemplo de actualización de entrenamiento federado."""
    return FederatedTrainingUpdateSchema.create_training_update(
        session_id="fed-session-001",
        node_id="node-001",
        round_num=3,
        weights_hash="a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
        ipfs_cid="QmYwAPJzv5CZsnAzt7HJTgLKFNcKrEM1Tw1DTZR5YLFG4g",
        num_samples=1500,
        metrics={
            "local_accuracy": 0.89,
            "local_loss": 0.234,
            "training_time_seconds": 45.2,
            "privacy_budget_used": 0.8
        },
        compression_info={
            "algorithm": "gzip",
            "compression_ratio": 0.65,
            "original_size_bytes": 5242880,
            "compressed_size_bytes": 3407872
        }
    )


def get_rag_query_example() -> Dict[str, Any]:
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
            },
            {
                "content": "En federated learning, cada dispositivo entrena un modelo local y comparte solo los parámetros del modelo.",
                "metadata": {
                    "title": "Privacy in ML",
                    "author": "Dr. Carlos López",
                    "topic": "Privacy",
                    "relevance_score": 0.88,
                    "source": "articulo_investigacion.pdf"
                },
                "score": 0.87
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
        },
        evaluation={
            "factual_accuracy": 0.94,
            "relevance_score": 0.89,
            "coherence_score": 0.92,
            "groundedness_score": 0.96,
            "correction_applied": True,
            "speculative_candidates": 0,
            "reflection_iterations": 2
        }
    )


def get_rag_health_example() -> Dict[str, Any]:
    """Ejemplo de respuesta de health check RAG."""
    return RAGHealthResponseSchema.create_health_response(
        status="healthy",
        rag_systems_available=["NaiveRAG", "CorrectiveRAG", "SelfRAG"],
        system_health={
            "vector_store_status": "connected",
            "embedding_service_status": "available",
            "model_service_status": "ready",
            "cache_status": "enabled"
        },
        performance_metrics={
            "average_query_time_seconds": 0.234,
            "queries_per_minute": 45.2,
            "cache_hit_rate": 0.67,
            "error_rate": 0.02,
            "memory_usage_percent": 68.5
        },
        system_info={
            "total_documents": 15420,
            "total_chunks": 89234,
            "vector_dimensions": 768,
            "embedding_model": "text-embedding-ada-002",
            "supported_languages": ["es", "en", "fr"],
            "max_context_length": 4096
        },
        alerts=[
            {
                "alert_id": "cache_high_memory",
                "severity": "warning",
                "title": "Uso alto de memoria cache",
                "message": "La cache está utilizando 85% de la memoria disponible",
                "timestamp": datetime.now().isoformat(),
                "resolved": False
            }
        ]
    )


def get_inference_response_example() -> Dict[str, Any]:
    """Ejemplo de respuesta de inferencia LLM."""
    return InferenceResponseSchema.create_inference_response(
        text="El aprendizaje automático es una rama de la inteligencia artificial que permite a los sistemas aprender y mejorar automáticamente a partir de la experiencia, sin ser programados explícitamente para cada tarea específica.",
        prompt_tokens=12,
        completion_tokens=45,
        model_name="EmpoorioLM",
        model_version="v1.0.0",
        finish_reason="stop",
        generation_metadata={
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 50,
            "max_tokens": 100,
            "repetition_penalty": 1.1
        },
        usage_extra={
            "tokens_per_second": 23.5,
            "estimated_cost": 0.0024
        }
    )


def get_inference_health_example() -> Dict[str, Any]:
    """Ejemplo de respuesta de health check de inferencia."""
    return InferenceHealthResponseSchema.create_health_response(
        status="healthy",
        model_status={
            "loaded": True,
            "model_name": "EmpoorioLM-v1.0",
            "model_size_gb": 7.2,
            "quantization": "none",
            "device": "cuda",
            "memory_usage_gb": 8.5,
            "max_memory_gb": 24.0
        },
        performance_metrics={
            "requests_per_second": 12.3,
            "average_latency_seconds": 0.145,
            "p50_latency_seconds": 0.132,
            "p95_latency_seconds": 0.234,
            "p99_latency_seconds": 0.456,
            "tokens_per_second": 2450.0,
            "queue_size": 2,
            "active_requests": 3
        },
        maturity2_status={
            "quantization_enabled": False,
            "drift_monitoring_enabled": True,
            "vllm_batching_enabled": False,
            "drift_alerts": 0,
            "last_drift_check": datetime.now().isoformat(),
            "vllm_throughput": 0.0,
            "quantization_memory_savings": 0.0
        },
        system_resources={
            "cpu_usage_percent": 45.2,
            "memory_usage_percent": 67.8,
            "gpu_usage_percent": 78.3,
            "gpu_memory_usage_percent": 82.1,
            "disk_usage_percent": 34.5,
            "network_io_mbps": 125.6
        }
    )


def get_toon_response_example() -> Dict[str, Any]:
    """Ejemplo de respuesta con serialización TOON."""
    return TOONResponseSchema.create_toon_response(
        toon_data="VE9PTjEAAAAAAAABAAAAAQAAAAEAAAA=",  # Base64 encoded TOON data
        toon_metadata={
            "original_size_bytes": 1024,
            "compressed_size_bytes": 768,
            "compression_ratio": 1.33,
            "data_type": "array",
            "array_length": 50,
            "schema_hash": "abc123def456"
        },
        preview_data={
            "items": [
                {"id": 1, "value": 42.5, "category": "A"},
                {"id": 2, "value": 38.7, "category": "B"}
            ]
        },
        optimization_metrics={
            "serialization_time_seconds": 0.023,
            "deserialization_time_seconds": 0.018,
            "bandwidth_savings_percent": 25.0,
            "memory_efficiency": 0.92
        }
    )


def get_vsc_response_example() -> Dict[str, Any]:
    """Ejemplo de respuesta con serialización VSC."""
    return VSCResponseSchema.create_vsc_response(
        vsc_data="VlNDLTEAAAAAAAABAAAAAQAAAAEAAAA=",  # Base64 encoded VSC data
        vsc_metadata={
            "data_type": "columnar",
            "num_columns": 4,
            "num_rows": 1000,
            "column_types": {
                "timestamp": "int64",
                "value": "float64",
                "category": "string",
                "quality_score": "float32"
            },
            "total_size_bytes": 25600,
            "compression_info": {
                "algorithm": "lz4",
                "level": 1,
                "ratio": 0.75
            },
            "schema_hash": "def789ghi012"
        },
        column_preview={
            "timestamp": [1640995200, 1640995260, 1640995320],
            "value": [23.5, 24.1, 23.8],
            "category": ["A", "B", "A"],
            "quality_score": [0.95, 0.87, 0.92]
        },
        query_optimization={
            "supports_predicates": ["range", "equality", "like"],
            "indexable_columns": ["timestamp", "category"],
            "estimated_query_time_ms": 15.2,
            "memory_mapped": True
        }
    )


# ===== FUNCIONES DE VALIDACIÓN =====

def validate_example(schema_class, example_func, example_name: str) -> Dict[str, Any]:
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


def run_all_validations() -> Dict[str, Any]:
    """Ejecutar validación de todos los ejemplos."""
    validations = []

    # Base schema
    validations.append(validate_example(BaseLLMResponseSchema, get_base_response_example, "Base Response"))

    # Federated schemas
    validations.append(validate_example(FederatedSessionResponseSchema, get_federated_session_example, "Federated Session"))
    validations.append(validate_example(FederatedNodeResponseSchema, get_federated_node_example, "Federated Node"))
    validations.append(validate_example(FederatedMetricsResponseSchema, get_federated_metrics_example, "Federated Metrics"))
    validations.append(validate_example(FederatedTrainingUpdateSchema, get_federated_training_update_example, "Federated Training Update"))

    # RAG schemas
    validations.append(validate_example(RAGQueryResponseSchema, get_rag_query_example, "RAG Query"))
    validations.append(validate_example(RAGHealthResponseSchema, get_rag_health_example, "RAG Health"))

    # Inference schemas
    validations.append(validate_example(InferenceResponseSchema, get_inference_response_example, "Inference Response"))
    validations.append(validate_example(InferenceHealthResponseSchema, get_inference_health_example, "Inference Health"))

    # Serialization schemas
    validations.append(validate_example(TOONResponseSchema, get_toon_response_example, "TOON Response"))
    validations.append(validate_example(VSCResponseSchema, get_vsc_response_example, "VSC Response"))

    # Resumen
    total_validations = len(validations)
    successful_validations = len([v for v in validations if v["valid"]])

    return {
        "summary": {
            "total_examples": total_validations,
            "successful_validations": successful_validations,
            "failed_validations": total_validations - successful_validations,
            "success_rate": successful_validations / total_validations if total_validations > 0 else 0
        },
        "validations": validations,
        "timestamp": datetime.now().isoformat()
    }


# ===== EXPORTACIÓN DE EJEMPLOS =====

def export_examples_to_file(filepath: str = "schema_examples.json"):
    """Exportar todos los ejemplos a un archivo JSON."""
    examples = {
        "base_response": get_base_response_example(),
        "federated_session": get_federated_session_example(),
        "federated_node": get_federated_node_example(),
        "federated_metrics": get_federated_metrics_example(),
        "federated_training_update": get_federated_training_update_example(),
        "rag_query": get_rag_query_example(),
        "rag_health": get_rag_health_example(),
        "inference_response": get_inference_response_example(),
        "inference_health": get_inference_health_example(),
        "toon_response": get_toon_response_example(),
        "vsc_response": get_vsc_response_example(),
        "validation_results": run_all_validations()
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(examples, f, indent=2, ensure_ascii=False)

    print(f"✅ Ejemplos exportados a {filepath}")


if __name__ == "__main__":
    # Ejecutar validaciones
    results = run_all_validations()
    print("🔍 Resultados de validación de esquemas:")
    print(f"   Total de ejemplos: {results['summary']['total_examples']}")
    print(f"   Validaciones exitosas: {results['summary']['successful_validations']}")
    print(f"   Validaciones fallidas: {results['summary']['failed_validations']}")
    print(".1f")

    # Mostrar errores si los hay
    failed_validations = [v for v in results['validations'] if not v['valid']]
    if failed_validations:
        print("\n❌ Validaciones fallidas:")
        for validation in failed_validations:
            print(f"   - {validation['example']}: {', '.join(validation['errors'])}")

    # Exportar ejemplos
    export_examples_to_file()