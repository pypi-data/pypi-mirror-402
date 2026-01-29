"""
Esquemas JSON Schema para respuestas de inferencia de modelos LLM en AILOOS.
Define estructuras para generación de texto, health checks y métricas de rendimiento.
"""

from typing import Dict, Any, List, Optional
from .base import BaseLLMResponseSchema


class InferenceResponseSchema(BaseLLMResponseSchema):
    """
    Esquema para respuestas de inferencia de modelos LLM.
    """

    INFERENCE_SCHEMA = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://ailoos.ai/schemas/inference-response",
        "title": "LLM Inference Response",
        "description": "Respuesta estructurada para inferencia de modelos de lenguaje",
        "type": "object",
        "allOf": [
            {"$ref": "https://ailoos.ai/schemas/base-llm-response"},
            {
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Texto generado por el modelo"
                    },
                    "finish_reason": {
                        "type": "string",
                        "enum": ["stop", "length", "content_filter", "function_call"],
                        "description": "Razón por la que terminó la generación"
                    },
                    "usage": {
                        "type": "object",
                        "properties": {
                            "prompt_tokens": {
                                "type": "integer",
                                "minimum": 0,
                                "description": "Número de tokens en el prompt"
                            },
                            "completion_tokens": {
                                "type": "integer",
                                "minimum": 0,
                                "description": "Número de tokens generados"
                            },
                            "total_tokens": {
                                "type": "integer",
                                "minimum": 0,
                                "description": "Total de tokens utilizados"
                            },
                            "tokens_per_second": {
                                "type": "number",
                                "minimum": 0,
                                "description": "Velocidad de generación en tokens/segundo"
                            },
                            "estimated_cost": {
                                "type": "number",
                                "minimum": 0,
                                "description": "Costo estimado de la inferencia"
                            }
                        },
                        "required": ["prompt_tokens", "completion_tokens", "total_tokens"]
                    },
                    "generation_metadata": {
                        "type": "object",
                        "properties": {
                            "model_version": {"type": "string"},
                            "temperature": {"type": "number", "minimum": 0, "maximum": 2},
                            "top_p": {"type": "number", "minimum": 0, "maximum": 1},
                            "top_k": {"type": "integer", "minimum": 0},
                            "max_tokens": {"type": "integer", "minimum": 1},
                            "repetition_penalty": {"type": "number", "minimum": 0},
                            "stop_sequences": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "seed": {"type": "integer"},
                            "logprobs": {"type": "boolean"}
                        }
                    },
                    "logprobs": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "token": {"type": "string"},
                                "logprob": {"type": "number"},
                                "top_logprobs": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "token": {"type": "string"},
                                            "logprob": {"type": "number"}
                                        }
                                    }
                                }
                            }
                        },
                        "description": "Log-probabilidades de tokens (opcional)"
                    },
                    "streaming": {
                        "type": "boolean",
                        "description": "Si la respuesta fue generada en streaming"
                    },
                    "chunks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string"},
                                "timestamp": {"type": "number", "minimum": 0},
                                "finish_reason": {"type": "string"}
                            }
                        },
                        "description": "Chunks de respuesta para streaming (opcional)"
                    },
                    "structured_output": {
                        "type": "boolean",
                        "description": "Indica si la respuesta fue generada con salida estructurada"
                    },
                    "schema_used": {
                        "type": "object",
                        "description": "Esquema JSON Schema utilizado para generación estructurada (opcional)"
                    },
                    "validation_passed": {
                        "type": "boolean",
                        "description": "Indica si la salida estructurada pasó validación de esquema"
                    },
                    "guidance_used": {
                        "type": "boolean",
                        "description": "Indica si se utilizó Guidance para la generación"
                    }
                },
                "required": ["text", "usage"]
            }
        ]
    }

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return cls.INFERENCE_SCHEMA

    @classmethod
    def create_inference_response(
        cls,
        text: str,
        prompt_tokens: int,
        completion_tokens: int,
        model_name: str,
        model_version: str,
        finish_reason: str = "stop",
        structured_output: bool = False,
        schema_used: Optional[Dict[str, Any]] = None,
        validation_passed: Optional[bool] = None,
        guidance_used: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Crear respuesta estructurada para inferencia."""
        return cls.create_base_response(
            response_id=f"inference-{hash(text) % 1000000:06d}",
            model_name=model_name,
            model_version=model_version,
            total_tokens=prompt_tokens + completion_tokens,
            response_type="llm_inference",
            text=text,
            finish_reason=finish_reason,
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                **kwargs.get("usage_extra", {})
            },
            structured_output=structured_output,
            schema_used=schema_used,
            validation_passed=validation_passed,
            guidance_used=guidance_used,
            **kwargs
        )


class InferenceHealthResponseSchema(BaseLLMResponseSchema):
    """
    Esquema para respuestas de health check de servicios de inferencia.
    """

    HEALTH_SCHEMA = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://ailoos.ai/schemas/inference-health-response",
        "title": "Inference Health Response",
        "description": "Respuesta estructurada para estado de salud de servicios de inferencia",
        "type": "object",
        "allOf": [
            {"$ref": "https://ailoos.ai/schemas/base-llm-response"},
            {
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["healthy", "degraded", "unhealthy"],
                        "description": "Estado general del servicio"
                    },
                    "model_status": {
                        "type": "object",
                        "properties": {
                            "loaded": {"type": "boolean"},
                            "model_name": {"type": "string"},
                            "model_size_gb": {"type": "number", "minimum": 0},
                            "quantization": {"type": "string"},
                            "device": {"type": "string"},
                            "memory_usage_gb": {"type": "number", "minimum": 0},
                            "max_memory_gb": {"type": "number", "minimum": 0}
                        }
                    },
                    "performance_metrics": {
                        "type": "object",
                        "properties": {
                            "requests_per_second": {"type": "number", "minimum": 0},
                            "average_latency_seconds": {"type": "number", "minimum": 0},
                            "p50_latency_seconds": {"type": "number", "minimum": 0},
                            "p95_latency_seconds": {"type": "number", "minimum": 0},
                            "p99_latency_seconds": {"type": "number", "minimum": 0},
                            "tokens_per_second": {"type": "number", "minimum": 0},
                            "queue_size": {"type": "integer", "minimum": 0},
                            "active_requests": {"type": "integer", "minimum": 0}
                        }
                    },
                    "maturity2_status": {
                        "type": "object",
                        "properties": {
                            "quantization_enabled": {"type": "boolean"},
                            "drift_monitoring_enabled": {"type": "boolean"},
                            "vllm_batching_enabled": {"type": "boolean"},
                            "drift_alerts": {"type": "integer", "minimum": 0},
                            "last_drift_check": {"type": "string", "format": "date-time"},
                            "vllm_throughput": {"type": "number", "minimum": 0},
                            "quantization_memory_savings": {"type": "number", "minimum": 0}
                        }
                    },
                    "system_resources": {
                        "type": "object",
                        "properties": {
                            "cpu_usage_percent": {"type": "number", "minimum": 0, "maximum": 100},
                            "memory_usage_percent": {"type": "number", "minimum": 0, "maximum": 100},
                            "gpu_usage_percent": {"type": "number", "minimum": 0, "maximum": 100},
                            "gpu_memory_usage_percent": {"type": "number", "minimum": 0, "maximum": 100},
                            "disk_usage_percent": {"type": "number", "minimum": 0, "maximum": 100},
                            "network_io_mbps": {"type": "number", "minimum": 0}
                        }
                    },
                    "configuration": {
                        "type": "object",
                        "properties": {
                            "max_batch_size": {"type": "integer", "minimum": 1},
                            "max_concurrent_requests": {"type": "integer", "minimum": 1},
                            "request_timeout_seconds": {"type": "number", "minimum": 0},
                            "enable_streaming": {"type": "boolean"},
                            "supported_formats": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    }
                },
                "required": ["status"]
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
        model_status: Dict[str, Any] = None,
        performance_metrics: Dict[str, Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Crear respuesta estructurada para health check de inferencia."""
        return cls.create_base_response(
            response_id="inference-health-check",
            model_name="inference-health-monitor",
            model_version="health-v1.0",
            total_tokens=0,
            response_type="inference_health",
            status=status,
            model_status=model_status or {},
            performance_metrics=performance_metrics or {},
            **kwargs
        )


class InferenceBatchResponseSchema(BaseLLMResponseSchema):
    """
    Esquema para respuestas de inferencia por lotes.
    """

    BATCH_SCHEMA = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://ailoos.ai/schemas/inference-batch-response",
        "title": "Inference Batch Response",
        "description": "Respuesta estructurada para inferencia por lotes de modelos LLM",
        "type": "object",
        "allOf": [
            {"$ref": "https://ailoos.ai/schemas/base-llm-response"},
            {
                "properties": {
                    "batch_id": {
                        "type": "string",
                        "description": "ID único del lote de inferencia"
                    },
                    "total_requests": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Número total de requests en el lote"
                    },
                    "successful_requests": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "Número de requests procesados exitosamente"
                    },
                    "failed_requests": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "Número de requests que fallaron"
                    },
                    "responses": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "request_id": {"type": "string"},
                                "text": {"type": "string"},
                                "finish_reason": {"type": "string"},
                                "usage": {
                                    "type": "object",
                                    "properties": {
                                        "prompt_tokens": {"type": "integer", "minimum": 0},
                                        "completion_tokens": {"type": "integer", "minimum": 0},
                                        "total_tokens": {"type": "integer", "minimum": 0}
                                    }
                                },
                                "error": {"type": "string"},
                                "processing_time_seconds": {"type": "number", "minimum": 0}
                            },
                            "required": ["request_id"]
                        },
                        "description": "Respuestas individuales del lote"
                    },
                    "batch_metrics": {
                        "type": "object",
                        "properties": {
                            "total_processing_time_seconds": {"type": "number", "minimum": 0},
                            "average_processing_time_seconds": {"type": "number", "minimum": 0},
                            "total_tokens_processed": {"type": "integer", "minimum": 0},
                            "tokens_per_second": {"type": "number", "minimum": 0},
                            "batch_efficiency": {"type": "number", "minimum": 0, "maximum": 1}
                        }
                    },
                    "errors": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "request_id": {"type": "string"},
                                "error_type": {"type": "string"},
                                "error_message": {"type": "string"},
                                "timestamp": {"type": "string", "format": "date-time"}
                            }
                        },
                        "description": "Errores ocurridos durante el procesamiento del lote"
                    }
                },
                "required": ["batch_id", "total_requests", "responses"]
            }
        ]
    }

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return cls.BATCH_SCHEMA

    @classmethod
    def create_batch_response(
        cls,
        batch_id: str,
        responses: List[Dict[str, Any]],
        model_name: str,
        model_version: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Crear respuesta estructurada para inferencia por lotes."""
        total_requests = len(responses)
        successful_requests = len([r for r in responses if "error" not in r])
        failed_requests = total_requests - successful_requests

        return cls.create_base_response(
            response_id=f"batch-{batch_id}",
            model_name=model_name,
            model_version=model_version,
            total_tokens=sum(r.get("usage", {}).get("total_tokens", 0) for r in responses),
            response_type="inference_batch",
            batch_id=batch_id,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            responses=responses,
            **kwargs
        )