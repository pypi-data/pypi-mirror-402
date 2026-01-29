"""
Esquema base para respuestas estructuradas de LLM en AILOOS.
Define la estructura común para todas las respuestas de modelos de lenguaje.
"""

from typing import Dict, Any, Optional
import json
from datetime import datetime


class BaseLLMResponseSchema:
    """
    Esquema base para respuestas estructuradas de LLM.

    Todas las respuestas de LLM en AILOOS deben seguir esta estructura base
    para asegurar consistencia y facilitar el parsing estructurado.
    """

    # Versión del esquema
    SCHEMA_VERSION = "1.0.0"

    # Definición JSON Schema base
    BASE_SCHEMA = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://ailoos.ai/schemas/base-llm-response",
        "title": "Base LLM Response",
        "description": "Esquema base para respuestas estructuradas de LLM en AILOOS",
        "type": "object",
        "properties": {
            "response_id": {
                "type": "string",
                "description": "Identificador único de la respuesta",
                "pattern": "^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$"
            },
            "timestamp": {
                "type": "string",
                "format": "date-time",
                "description": "Timestamp ISO 8601 de cuando se generó la respuesta"
            },
            "model": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Nombre del modelo utilizado"
                    },
                    "version": {
                        "type": "string",
                        "description": "Versión del modelo"
                    },
                    "provider": {
                        "type": "string",
                        "description": "Proveedor del modelo (EmpoorioLM, OpenAI, etc.)"
                    }
                },
                "required": ["name", "version"]
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
                    "processing_time_seconds": {
                        "type": "number",
                        "minimum": 0,
                        "description": "Tiempo de procesamiento en segundos"
                    }
                },
                "required": ["total_tokens"]
            },
            "metadata": {
                "type": "object",
                "description": "Metadata adicional específica del dominio",
                "additionalProperties": True
            },
            "validation": {
                "type": "object",
                "properties": {
                    "schema_version": {
                        "type": "string",
                        "description": "Versión del esquema utilizado"
                    },
                    "validated_at": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Cuando se validó la respuesta"
                    },
                    "is_valid": {
                        "type": "boolean",
                        "description": "Si la respuesta cumple con el esquema"
                    }
                }
            }
        },
        "required": ["response_id", "timestamp", "model", "usage"]
    }

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Obtener el esquema JSON Schema completo."""
        return cls.BASE_SCHEMA

    @classmethod
    def validate_response(cls, response: Dict[str, Any]) -> bool:
        """
        Validar una respuesta contra el esquema base.

        Args:
            response: Respuesta a validar

        Returns:
            True si la respuesta es válida
        """
        try:
            import jsonschema
            jsonschema.validate(response, cls.BASE_SCHEMA)
            return True
        except (jsonschema.ValidationError, ImportError):
            return False

    @classmethod
    def create_base_response(
        cls,
        response_id: str,
        model_name: str,
        model_version: str,
        total_tokens: int,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Crear una respuesta base con estructura estándar.

        Args:
            response_id: ID único de la respuesta
            model_name: Nombre del modelo
            model_version: Versión del modelo
            total_tokens: Total de tokens utilizados
            metadata: Metadata adicional
            **kwargs: Campos adicionales específicos del dominio

        Returns:
            Respuesta estructurada
        """
        base_response = {
            "response_id": response_id,
            "timestamp": datetime.now().isoformat(),
            "model": {
                "name": model_name,
                "version": model_version,
                "provider": "EmpoorioLM"  # Default para AILOOS
            },
            "usage": {
                "total_tokens": total_tokens,
                "prompt_tokens": kwargs.get("prompt_tokens", 0),
                "completion_tokens": kwargs.get("completion_tokens", 0),
                "processing_time_seconds": kwargs.get("processing_time_seconds", 0.0)
            },
            "metadata": metadata or {},
            "validation": {
                "schema_version": cls.SCHEMA_VERSION,
                "validated_at": datetime.now().isoformat(),
                "is_valid": True
            }
        }

        # Agregar campos específicos del dominio
        for key, value in kwargs.items():
            if key not in ["prompt_tokens", "completion_tokens", "processing_time_seconds"]:
                base_response[key] = value

        return base_response

    @classmethod
    def add_domain_fields(cls, schema: Dict[str, Any], domain_fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agregar campos específicos del dominio a un esquema existente.

        Args:
            schema: Esquema base
            domain_fields: Campos específicos del dominio

        Returns:
            Esquema extendido
        """
        extended_schema = schema.copy()

        # Agregar campos del dominio a properties
        if "properties" not in extended_schema:
            extended_schema["properties"] = {}

        extended_schema["properties"].update(domain_fields)

        return extended_schema


# Funciones de utilidad para validación
def validate_llm_response(response: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Validar una respuesta de LLM contra un esquema.

    Args:
        response: Respuesta a validar
        schema: Esquema a utilizar (usa base si no se proporciona)

    Returns:
        Dict con resultado de validación
    """
    if schema is None:
        schema = BaseLLMResponseSchema.get_schema()

    try:
        import jsonschema
        jsonschema.validate(response, schema)

        return {
            "valid": True,
            "schema_version": schema.get("$id", "unknown"),
            "errors": []
        }
    except jsonschema.ValidationError as e:
        return {
            "valid": False,
            "schema_version": schema.get("$id", "unknown"),
            "errors": [str(e)]
        }
    except ImportError:
        return {
            "valid": False,
            "schema_version": "unknown",
            "errors": ["jsonschema library not available"]
        }


def create_structured_response(
    response_type: str,
    response_id: str,
    model_name: str,
    model_version: str,
    content: Any,
    **kwargs
) -> Dict[str, Any]:
    """
    Crear una respuesta estructurada con tipo específico.

    Args:
        response_type: Tipo de respuesta (rag, federated, inference, etc.)
        response_id: ID único de la respuesta
        model_name: Nombre del modelo
        model_version: Versión del modelo
        content: Contenido específico de la respuesta
        **kwargs: Parámetros adicionales

    Returns:
        Respuesta estructurada completa
    """
    base_response = BaseLLMResponseSchema.create_base_response(
        response_id=response_id,
        model_name=model_name,
        model_version=model_version,
        total_tokens=kwargs.get("total_tokens", 0),
        metadata={
            "response_type": response_type,
            **kwargs.get("metadata", {})
        },
        **kwargs
    )

    # Agregar contenido específico
    base_response["content"] = content

    return base_response