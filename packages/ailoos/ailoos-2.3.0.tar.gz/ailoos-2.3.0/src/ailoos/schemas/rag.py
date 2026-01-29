"""
Esquemas JSON Schema para respuestas de RAG (Retrieval-Augmented Generation) en AILOOS.
Define estructuras para consultas RAG, contextos y diferentes técnicas RAG.
"""

from typing import Dict, Any, List
from .base import BaseLLMResponseSchema


class RAGQueryResponseSchema(BaseLLMResponseSchema):
    """
    Esquema para respuestas de consultas RAG.
    """

    QUERY_SCHEMA = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://ailoos.ai/schemas/rag-query-response",
        "title": "RAG Query Response",
        "description": "Respuesta estructurada para consultas RAG con contexto y metadata",
        "type": "object",
        "allOf": [
            {"$ref": "https://ailoos.ai/schemas/base-llm-response"},
            {
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "La consulta original del usuario"
                    },
                    "response": {
                        "type": "string",
                        "description": "Respuesta generada por el modelo RAG"
                    },
                    "context": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "content": {
                                    "type": "string",
                                    "description": "Contenido del documento recuperado"
                                },
                                "metadata": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "author": {"type": "string"},
                                        "topic": {"type": "string"},
                                        "source": {"type": "string"},
                                        "relevance_score": {"type": "number", "minimum": 0, "maximum": 1},
                                        "chunk_index": {"type": "integer", "minimum": 0},
                                        "document_id": {"type": "string"}
                                    }
                                },
                                "score": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                    "description": "Puntuación de relevancia del contexto"
                                }
                            },
                            "required": ["content", "metadata"]
                        },
                        "description": "Documentos de contexto recuperados"
                    },
                    "rag_type": {
                        "type": "string",
                        "enum": ["NaiveRAG", "CorrectiveRAG", "SpeculativeRAG", "SelfRAG", "CacheAugmentedRAG"],
                        "description": "Tipo de sistema RAG utilizado"
                    },
                    "metrics": {
                        "type": "object",
                        "properties": {
                            "retrieval_time_seconds": {
                                "type": "number",
                                "minimum": 0,
                                "description": "Tiempo de recuperación de documentos"
                            },
                            "generation_time_seconds": {
                                "type": "number",
                                "minimum": 0,
                                "description": "Tiempo de generación de respuesta"
                            },
                            "total_context_tokens": {
                                "type": "integer",
                                "minimum": 0,
                                "description": "Total de tokens en el contexto"
                            },
                            "context_chunks_count": {
                                "type": "integer",
                                "minimum": 0,
                                "description": "Número de chunks de contexto utilizados"
                            },
                            "relevance_score": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Puntuación de relevancia promedio del contexto"
                            },
                            "confidence_score": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Puntuación de confianza de la respuesta"
                            },
                            "cache_hit": {
                                "type": "boolean",
                                "description": "Si se utilizó cache para la respuesta"
                            }
                        }
                    },
                    "evaluation": {
                        "type": "object",
                        "description": "Resultados de evaluación para técnicas avanzadas de RAG",
                        "properties": {
                            "factual_accuracy": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Precisión factual de la respuesta"
                            },
                            "relevance_score": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Relevancia de la respuesta respecto a la consulta"
                            },
                            "coherence_score": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Coherencia de la respuesta"
                            },
                            "groundedness_score": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Qué tan fundamentada está la respuesta en el contexto"
                            },
                            "correction_applied": {
                                "type": "boolean",
                                "description": "Si se aplicó corrección en CorrectiveRAG"
                            },
                            "speculative_candidates": {
                                "type": "integer",
                                "minimum": 0,
                                "description": "Número de candidatos especulativos generados"
                            },
                            "reflection_iterations": {
                                "type": "integer",
                                "minimum": 0,
                                "description": "Número de iteraciones de reflexión en SelfRAG"
                            }
                        }
                    },
                    "processing_metadata": {
                        "type": "object",
                        "properties": {
                            "model_used": {"type": "string"},
                            "tokenizer_used": {"type": "string"},
                            "retrieval_strategy": {"type": "string"},
                            "generation_parameters": {
                                "type": "object",
                                "properties": {
                                    "temperature": {"type": "number", "minimum": 0},
                                    "top_p": {"type": "number", "minimum": 0, "maximum": 1},
                                    "top_k": {"type": "integer", "minimum": 0},
                                    "max_new_tokens": {"type": "integer", "minimum": 1}
                                }
                            },
                            "vector_store": {"type": "string"},
                            "embedding_model": {"type": "string"}
                        }
                    }
                },
                "required": ["query", "response", "context", "rag_type", "metrics"]
            }
        ]
    }

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return cls.QUERY_SCHEMA

    @classmethod
    def create_rag_response(
        cls,
        query: str,
        response: str,
        context: List[Dict[str, Any]],
        rag_type: str,
        metrics: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Crear respuesta estructurada para consulta RAG."""
        return cls.create_base_response(
            response_id=f"rag-{hash(query) % 1000000:06d}",
            model_name=f"{rag_type}-model",
            model_version="rag-v1.0",
            total_tokens=metrics.get("total_context_tokens", 0) + len(response.split()),
            response_type="rag_query",
            query=query,
            response=response,
            context=context,
            rag_type=rag_type,
            metrics=metrics,
            **kwargs
        )


class RAGHealthResponseSchema(BaseLLMResponseSchema):
    """
    Esquema para respuestas de health check de sistemas RAG.
    """

    HEALTH_SCHEMA = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://ailoos.ai/schemas/rag-health-response",
        "title": "RAG Health Response",
        "description": "Respuesta estructurada para estado de salud de sistemas RAG",
        "type": "object",
        "allOf": [
            {"$ref": "https://ailoos.ai/schemas/base-llm-response"},
            {
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["healthy", "degraded", "unhealthy"],
                        "description": "Estado general del sistema RAG"
                    },
                    "rag_systems_available": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["NaiveRAG", "CorrectiveRAG", "SpeculativeRAG", "SelfRAG", "CacheAugmentedRAG"]
                        },
                        "description": "Sistemas RAG disponibles"
                    },
                    "system_health": {
                        "type": "object",
                        "properties": {
                            "vector_store_status": {
                                "type": "string",
                                "enum": ["connected", "disconnected", "error"]
                            },
                            "embedding_service_status": {
                                "type": "string",
                                "enum": ["available", "unavailable", "error"]
                            },
                            "model_service_status": {
                                "type": "string",
                                "enum": ["ready", "loading", "error"]
                            },
                            "cache_status": {
                                "type": "string",
                                "enum": ["enabled", "disabled", "error"]
                            }
                        }
                    },
                    "performance_metrics": {
                        "type": "object",
                        "properties": {
                            "average_query_time_seconds": {"type": "number", "minimum": 0},
                            "queries_per_minute": {"type": "number", "minimum": 0},
                            "cache_hit_rate": {"type": "number", "minimum": 0, "maximum": 1},
                            "error_rate": {"type": "number", "minimum": 0, "maximum": 1},
                            "memory_usage_percent": {"type": "number", "minimum": 0, "maximum": 100},
                            "cpu_usage_percent": {"type": "number", "minimum": 0, "maximum": 100}
                        }
                    },
                    "system_info": {
                        "type": "object",
                        "properties": {
                            "total_documents": {"type": "integer", "minimum": 0},
                            "total_chunks": {"type": "integer", "minimum": 0},
                            "vector_dimensions": {"type": "integer", "minimum": 1},
                            "embedding_model": {"type": "string"},
                            "supported_languages": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "max_context_length": {"type": "integer", "minimum": 1}
                        }
                    },
                    "alerts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "alert_id": {"type": "string"},
                                "severity": {"type": "string", "enum": ["info", "warning", "error", "critical"]},
                                "title": {"type": "string"},
                                "message": {"type": "string"},
                                "timestamp": {"type": "string", "format": "date-time"},
                                "resolved": {"type": "boolean"}
                            },
                            "required": ["alert_id", "severity", "title", "message"]
                        }
                    }
                },
                "required": ["status", "rag_systems_available"]
            }
        ]
    }

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return cls.HEALTH_SCHEMA

    @classmethod
    def create_health_response(
        cls,
        status: str,
        rag_systems_available: List[str],
        system_health: Dict[str, Any] = None,
        performance_metrics: Dict[str, Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Crear respuesta estructurada para health check de RAG."""
        return cls.create_base_response(
            response_id="rag-health-check",
            model_name="rag-health-monitor",
            model_version="health-v1.0",
            total_tokens=0,
            response_type="rag_health",
            status=status,
            rag_systems_available=rag_systems_available,
            system_health=system_health or {},
            performance_metrics=performance_metrics or {},
            **kwargs
        )


class RAGEvaluationResponseSchema(BaseLLMResponseSchema):
    """
    Esquema para respuestas de evaluación de RAG.
    """

    EVALUATION_SCHEMA = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://ailoos.ai/schemas/rag-evaluation-response",
        "title": "RAG Evaluation Response",
        "description": "Respuesta estructurada para evaluación de respuestas RAG",
        "type": "object",
        "allOf": [
            {"$ref": "https://ailoos.ai/schemas/base-llm-response"},
            {
                "properties": {
                    "evaluation_target": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "response": {"type": "string"},
                            "rag_type": {"type": "string"},
                            "context_used": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["query", "response"]
                    },
                    "evaluation_results": {
                        "type": "object",
                        "properties": {
                            "overall_score": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Puntuación general de calidad"
                            },
                            "criteria_scores": {
                                "type": "object",
                                "properties": {
                                    "relevance": {"type": "number", "minimum": 0, "maximum": 1},
                                    "accuracy": {"type": "number", "minimum": 0, "maximum": 1},
                                    "completeness": {"type": "number", "minimum": 0, "maximum": 1},
                                    "coherence": {"type": "number", "minimum": 0, "maximum": 1},
                                    "groundedness": {"type": "number", "minimum": 0, "maximum": 1},
                                    "conciseness": {"type": "number", "minimum": 0, "maximum": 1}
                                }
                            },
                            "evaluation_method": {
                                "type": "string",
                                "enum": ["automated", "human", "hybrid"]
                            },
                            "confidence_interval": {
                                "type": "object",
                                "properties": {
                                    "lower_bound": {"type": "number", "minimum": 0, "maximum": 1},
                                    "upper_bound": {"type": "number", "minimum": 0, "maximum": 1}
                                }
                            }
                        },
                        "required": ["overall_score", "criteria_scores"]
                    },
                    "evaluation_metadata": {
                        "type": "object",
                        "properties": {
                            "evaluator_model": {"type": "string"},
                            "evaluation_timestamp": {"type": "string", "format": "date-time"},
                            "evaluation_duration_seconds": {"type": "number", "minimum": 0},
                            "reference_answers": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "evaluation_criteria": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    },
                    "improvement_suggestions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "aspect": {"type": "string"},
                                "suggestion": {"type": "string"},
                                "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                                "expected_impact": {"type": "number", "minimum": 0, "maximum": 1}
                            }
                        }
                    }
                },
                "required": ["evaluation_target", "evaluation_results"]
            }
        ]
    }

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return cls.EVALUATION_SCHEMA

    @classmethod
    def create_evaluation_response(
        cls,
        evaluation_target: Dict[str, Any],
        evaluation_results: Dict[str, Any],
        evaluation_metadata: Dict[str, Any] = None,
        improvement_suggestions: List[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Crear respuesta estructurada para evaluación de RAG."""
        return cls.create_base_response(
            response_id=f"rag-eval-{hash(str(evaluation_target)) % 1000000:06d}",
            model_name="rag-evaluator",
            model_version="eval-v1.0",
            total_tokens=len(str(evaluation_results).split()),
            response_type="rag_evaluation",
            evaluation_target=evaluation_target,
            evaluation_results=evaluation_results,
            evaluation_metadata=evaluation_metadata or {},
            improvement_suggestions=improvement_suggestions or [],
            **kwargs
        )