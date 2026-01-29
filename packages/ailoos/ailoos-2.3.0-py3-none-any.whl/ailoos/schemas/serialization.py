"""
Esquemas JSON Schema para formatos de serialización optimizados en AILOOS.
Define estructuras para respuestas que utilizan TOON y VSC serialization.
"""

from typing import Dict, Any, List
from .base import BaseLLMResponseSchema


class TOONResponseSchema(BaseLLMResponseSchema):
    """
    Esquema para respuestas que utilizan TOON (Typed Object Notation) serialization.
    Optimizado para arrays uniformes y datos estructurados repetitivos.
    """

    TOON_SCHEMA = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://ailoos.ai/schemas/toon-response",
        "title": "TOON Serialized Response",
        "description": "Respuesta estructurada serializada con formato TOON optimizado",
        "type": "object",
        "allOf": [
            {"$ref": "https://ailoos.ai/schemas/base-llm-response"},
            {
                "properties": {
                    "serialization_format": {
                        "type": "string",
                        "const": "TOON",
                        "description": "Formato de serialización utilizado"
                    },
                    "toon_data": {
                        "type": "string",
                        "description": "Datos serializados en formato TOON (base64 encoded)",
                        "pattern": "^[A-Za-z0-9+/]*={0,2}$"
                    },
                    "toon_metadata": {
                        "type": "object",
                        "properties": {
                            "original_size_bytes": {
                                "type": "integer",
                                "minimum": 0,
                                "description": "Tamaño original de los datos sin comprimir"
                            },
                            "compressed_size_bytes": {
                                "type": "integer",
                                "minimum": 0,
                                "description": "Tamaño de los datos comprimidos"
                            },
                            "compression_ratio": {
                                "type": "number",
                                "minimum": 0,
                                "description": "Ratio de compresión (original/comprimido)"
                            },
                            "data_type": {
                                "type": "string",
                                "enum": ["array", "object", "mixed"],
                                "description": "Tipo principal de datos serializados"
                            },
                            "array_length": {
                                "type": "integer",
                                "minimum": 0,
                                "description": "Longitud del array si aplica"
                            },
                            "schema_hash": {
                                "type": "string",
                                "description": "Hash del esquema utilizado para validación"
                            }
                        },
                        "required": ["original_size_bytes", "compressed_size_bytes"]
                    },
                    "preview_data": {
                        "type": "object",
                        "description": "Vista previa de los datos (primeros elementos)",
                        "additionalProperties": True
                    },
                    "optimization_metrics": {
                        "type": "object",
                        "properties": {
                            "serialization_time_seconds": {
                                "type": "number",
                                "minimum": 0,
                                "description": "Tiempo de serialización"
                            },
                            "deserialization_time_seconds": {
                                "type": "number",
                                "minimum": 0,
                                "description": "Tiempo estimado de deserialización"
                            },
                            "bandwidth_savings_percent": {
                                "type": "number",
                                "minimum": 0,
                                "description": "Ahorro de ancho de banda porcentual"
                            },
                            "memory_efficiency": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Eficiencia de memoria (1.0 = óptimo)"
                            }
                        }
                    }
                },
                "required": ["serialization_format", "toon_data", "toon_metadata"]
            }
        ]
    }

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return cls.TOON_SCHEMA

    @classmethod
    def create_toon_response(
        cls,
        toon_data: str,
        toon_metadata: Dict[str, Any],
        model_name: str = "toon-serializer",
        **kwargs
    ) -> Dict[str, Any]:
        """Crear respuesta estructurada con datos TOON."""
        return cls.create_base_response(
            response_id=f"toon-{hash(toon_data) % 1000000:06d}",
            model_name=model_name,
            model_version="toon-v1.0",
            total_tokens=0,  # No aplica para datos serializados
            response_type="toon_serialized",
            serialization_format="TOON",
            toon_data=toon_data,
            toon_metadata=toon_metadata,
            **kwargs
        )


class VSCResponseSchema(BaseLLMResponseSchema):
    """
    Esquema para respuestas que utilizan VSC (Vector Serialized Columns) serialization.
    Optimizado para datos columnar densos y numéricos.
    """

    VSC_SCHEMA = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://ailoos.ai/schemas/vsc-response",
        "title": "VSC Serialized Response",
        "description": "Respuesta estructurada serializada con formato VSC optimizado",
        "type": "object",
        "allOf": [
            {"$ref": "https://ailoos.ai/schemas/base-llm-response"},
            {
                "properties": {
                    "serialization_format": {
                        "type": "string",
                        "const": "VSC",
                        "description": "Formato de serialización utilizado"
                    },
                    "vsc_data": {
                        "type": "string",
                        "description": "Datos serializados en formato VSC (base64 encoded)",
                        "pattern": "^[A-Za-z0-9+/]*={0,2}$"
                    },
                    "vsc_metadata": {
                        "type": "object",
                        "properties": {
                            "data_type": {
                                "type": "string",
                                "enum": ["columnar", "time_series", "matrix", "sparse"],
                                "description": "Tipo de datos columnar"
                            },
                            "num_columns": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "Número de columnas"
                            },
                            "num_rows": {
                                "type": "integer",
                                "minimum": 0,
                                "description": "Número de filas"
                            },
                            "column_types": {
                                "type": "object",
                                "description": "Tipos de datos por columna",
                                "patternProperties": {
                                    ".*": {
                                        "type": "string",
                                        "enum": ["uint8", "uint16", "uint32", "uint64", "int8", "int16", "int32", "int64", "float32", "float64", "string", "bool"]
                                    }
                                }
                            },
                            "total_size_bytes": {
                                "type": "integer",
                                "minimum": 0,
                                "description": "Tamaño total de los datos"
                            },
                            "compression_info": {
                                "type": "object",
                                "properties": {
                                    "algorithm": {"type": "string"},
                                    "level": {"type": "integer", "minimum": 0},
                                    "ratio": {"type": "number", "minimum": 0}
                                }
                            },
                            "schema_hash": {
                                "type": "string",
                                "description": "Hash del esquema columnar"
                            }
                        },
                        "required": ["data_type", "num_columns", "num_rows"]
                    },
                    "column_preview": {
                        "type": "object",
                        "description": "Vista previa de las primeras filas de cada columna",
                        "additionalProperties": {
                            "type": "array",
                            "maxItems": 5
                        }
                    },
                    "query_optimization": {
                        "type": "object",
                        "properties": {
                            "supports_predicates": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Predicados soportados para consultas"
                            },
                            "indexable_columns": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Columnas que pueden ser indexadas"
                            },
                            "estimated_query_time_ms": {
                                "type": "number",
                                "minimum": 0,
                                "description": "Tiempo estimado de consulta en ms"
                            },
                            "memory_mapped": {
                                "type": "boolean",
                                "description": "Si los datos están memory-mapped"
                            }
                        }
                    },
                    "performance_metrics": {
                        "type": "object",
                        "properties": {
                            "serialization_time_seconds": {
                                "type": "number",
                                "minimum": 0
                            },
                            "random_access_time_ms": {
                                "type": "number",
                                "minimum": 0,
                                "description": "Tiempo de acceso aleatorio promedio"
                            },
                            "compression_efficiency": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Eficiencia de compresión (1.0 = óptimo)"
                            },
                            "cpu_usage_percent": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                                "description": "Uso de CPU durante serialización"
                            }
                        }
                    }
                },
                "required": ["serialization_format", "vsc_data", "vsc_metadata"]
            }
        ]
    }

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return cls.VSC_SCHEMA

    @classmethod
    def create_vsc_response(
        cls,
        vsc_data: str,
        vsc_metadata: Dict[str, Any],
        model_name: str = "vsc-serializer",
        **kwargs
    ) -> Dict[str, Any]:
        """Crear respuesta estructurada con datos VSC."""
        return cls.create_base_response(
            response_id=f"vsc-{hash(vsc_data) % 1000000:06d}",
            model_name=model_name,
            model_version="vsc-v1.0",
            total_tokens=0,
            response_type="vsc_serialized",
            serialization_format="VSC",
            vsc_data=vsc_data,
            vsc_metadata=vsc_metadata,
            **kwargs
        )


class SerializationHealthResponseSchema(BaseLLMResponseSchema):
    """
    Esquema para respuestas de health check de servicios de serialización.
    """

    HEALTH_SCHEMA = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://ailoos.ai/schemas/serialization-health-response",
        "title": "Serialization Health Response",
        "description": "Estado de salud de servicios de serialización TOON/VSC",
        "type": "object",
        "allOf": [
            {"$ref": "https://ailoos.ai/schemas/base-llm-response"},
            {
                "properties": {
                    "serialization_status": {
                        "type": "object",
                        "properties": {
                            "toon_available": {"type": "boolean"},
                            "vsc_available": {"type": "boolean"},
                            "json_fallback": {"type": "boolean"},
                            "compression_enabled": {"type": "boolean"}
                        }
                    },
                    "performance_stats": {
                        "type": "object",
                        "properties": {
                            "total_serializations": {"type": "integer", "minimum": 0},
                            "total_deserializations": {"type": "integer", "minimum": 0},
                            "average_toon_serialization_time": {"type": "number", "minimum": 0},
                            "average_vsc_serialization_time": {"type": "number", "minimum": 0},
                            "average_compression_ratio": {"type": "number", "minimum": 0},
                            "cache_hit_rate": {"type": "number", "minimum": 0, "maximum": 1}
                        }
                    },
                    "format_usage": {
                        "type": "object",
                        "properties": {
                            "toon_usage_percent": {"type": "number", "minimum": 0, "maximum": 100},
                            "vsc_usage_percent": {"type": "number", "minimum": 0, "maximum": 100},
                            "json_usage_percent": {"type": "number", "minimum": 0, "maximum": 100},
                            "most_used_format": {"type": "string", "enum": ["TOON", "VSC", "JSON"]}
                        }
                    },
                    "memory_stats": {
                        "type": "object",
                        "properties": {
                            "schema_cache_size": {"type": "integer", "minimum": 0},
                            "active_schemas": {"type": "integer", "minimum": 0},
                            "memory_usage_mb": {"type": "number", "minimum": 0},
                            "gc_pressure": {"type": "string", "enum": ["low", "medium", "high"]}
                        }
                    },
                    "error_stats": {
                        "type": "object",
                        "properties": {
                            "total_errors": {"type": "integer", "minimum": 0},
                            "validation_errors": {"type": "integer", "minimum": 0},
                            "serialization_errors": {"type": "integer", "minimum": 0},
                            "deserialization_errors": {"type": "integer", "minimum": 0},
                            "error_rate_percent": {"type": "number", "minimum": 0, "maximum": 100}
                        }
                    }
                },
                "required": ["serialization_status"]
            }
        ]
    }

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return cls.HEALTH_SCHEMA

    @classmethod
    def create_health_response(
        cls,
        serialization_status: Dict[str, Any],
        performance_stats: Dict[str, Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Crear respuesta estructurada para health check de serialización."""
        return cls.create_base_response(
            response_id="serialization-health-check",
            model_name="serialization-health-monitor",
            model_version="health-v1.0",
            total_tokens=0,
            response_type="serialization_health",
            serialization_status=serialization_status,
            performance_stats=performance_stats or {},
            **kwargs
        )


class OptimizedResponseSchema(BaseLLMResponseSchema):
    """
    Esquema genérico para respuestas optimizadas con auto-detección de formato.
    """

    OPTIMIZED_SCHEMA = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://ailoos.ai/schemas/optimized-response",
        "title": "Optimized Response",
        "description": "Respuesta optimizada con formato de serialización automático",
        "type": "object",
        "allOf": [
            {"$ref": "https://ailoos.ai/schemas/base-llm-response"},
            {
                "properties": {
                    "optimization_applied": {
                        "type": "boolean",
                        "description": "Si se aplicó optimización de serialización"
                    },
                    "detected_format": {
                        "type": "string",
                        "enum": ["TOON", "VSC", "JSON"],
                        "description": "Formato detectado automáticamente"
                    },
                    "original_payload": {
                        "type": ["object", "array", "string"],
                        "description": "Payload original antes de optimización"
                    },
                    "optimized_payload": {
                        "type": "string",
                        "description": "Payload optimizado (base64 encoded)"
                    },
                    "optimization_metadata": {
                        "type": "object",
                        "properties": {
                            "size_reduction_percent": {
                                "type": "number",
                                "minimum": 0,
                                "description": "Reducción de tamaño porcentual"
                            },
                            "estimated_bandwidth_savings": {
                                "type": "number",
                                "minimum": 0,
                                "description": "Ahorro estimado de ancho de banda en bytes"
                            },
                            "processing_overhead_ms": {
                                "type": "number",
                                "minimum": 0,
                                "description": "Overhead de procesamiento en ms"
                            },
                            "compatibility_score": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Puntuación de compatibilidad con el formato elegido"
                            }
                        }
                    },
                    "fallback_available": {
                        "type": "boolean",
                        "description": "Si está disponible un fallback JSON"
                    }
                },
                "required": ["optimization_applied", "detected_format"]
            }
        ]
    }

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return cls.OPTIMIZED_SCHEMA

    @classmethod
    def create_optimized_response(
        cls,
        detected_format: str,
        optimized_payload: str,
        optimization_metadata: Dict[str, Any],
        model_name: str = "optimized-responses",
        **kwargs
    ) -> Dict[str, Any]:
        """Crear respuesta optimizada con formato automático."""
        return cls.create_base_response(
            response_id=f"opt-{hash(optimized_payload) % 1000000:06d}",
            model_name=model_name,
            model_version="optimized-v1.0",
            total_tokens=0,
            response_type="optimized_response",
            optimization_applied=True,
            detected_format=detected_format,
            optimized_payload=optimized_payload,
            optimization_metadata=optimization_metadata,
            **kwargs
        )