"""
Fallback de parsing post-generación usando Pydantic.
Valida y parsea respuestas generadas por LLM contra esquemas JSON Schema usando Pydantic,
como respaldo cuando Guidance falla o no está disponible.
"""

from typing import Dict, Any, Optional, Union, List, Type
import json
import logging
from datetime import datetime
import uuid

try:
    from pydantic import BaseModel, ValidationError, create_model_from_typed_dict
    from pydantic.fields import FieldInfo
    import pydantic_core
    PYDANTIC_AVAILABLE = True
except ImportError:
    pydantic = None
    BaseModel = None
    ValidationError = None
    FieldInfo = Any
    PYDANTIC_AVAILABLE = False

logger = logging.getLogger(__name__)


class PydanticSchemaConverter:
    """
    Convierte esquemas JSON Schema a modelos Pydantic para validación post-generación.
    """

    def __init__(self):
        if not PYDANTIC_AVAILABLE:
            raise ImportError("Pydantic library no está disponible. Instale con: pip install pydantic")

    @staticmethod
    def json_schema_to_pydantic_model(schema: Dict[str, Any], model_name: str = "DynamicModel") -> Type[BaseModel]:
        """
        Convierte un JSON Schema a un modelo Pydantic.

        Args:
            schema: JSON Schema a convertir
            model_name: Nombre del modelo Pydantic generado

        Returns:
            Modelo Pydantic generado

        Raises:
            ValueError: Si el esquema no puede ser convertido
        """
        try:
            # Extraer propiedades del esquema
            properties = schema.get("properties", {})
            required_fields = schema.get("required", [])

            # Crear campos del modelo
            model_fields = {}

            for field_name, field_schema in properties.items():
                field_type = PydanticSchemaConverter._json_schema_type_to_python(field_schema)
                field_info = PydanticSchemaConverter._create_field_info(field_schema, field_name in required_fields)
                model_fields[field_name] = (field_type, field_info)

            # Crear el modelo dinámicamente
            model = type(model_name, (BaseModel,), {
                "__annotations__": {name: typ for name, (typ, _) in model_fields.items()},
                **{name: info for name, (_, info) in model_fields.items()}
            })

            return model

        except Exception as e:
            logger.error(f"Error convirtiendo JSON Schema a Pydantic: {e}")
            raise ValueError(f"No se pudo convertir el esquema: {e}")

    @staticmethod
    def _json_schema_type_to_python(field_schema: Dict[str, Any]) -> Type:
        """
        Convierte tipos JSON Schema a tipos Python/Pydantic.

        Args:
            field_schema: Esquema del campo

        Returns:
            Tipo Python correspondiente
        """
        field_type = field_schema.get("type")

        if field_type == "string":
            return str
        elif field_type == "integer":
            return int
        elif field_type == "number":
            return float
        elif field_type == "boolean":
            return bool
        elif field_type == "array":
            items_schema = field_schema.get("items", {})
            item_type = PydanticSchemaConverter._json_schema_type_to_python(items_schema)
            return List[item_type]
        elif field_type == "object":
            # Para objetos anidados, crear un modelo inline
            nested_properties = field_schema.get("properties", {})
            if nested_properties:
                nested_model = PydanticSchemaConverter.json_schema_to_pydantic_model(
                    field_schema, f"Nested{field_schema.get('title', 'Object')}"
                )
                return nested_model
            else:
                return Dict[str, Any]
        else:
            # Tipo desconocido, usar Any
            return Any

    @staticmethod
    def _create_field_info(field_schema: Dict[str, Any], required: bool) -> FieldInfo:
        """
        Crea FieldInfo de Pydantic para un campo.

        Args:
            field_schema: Esquema del campo
            required: Si el campo es requerido

        Returns:
            FieldInfo configurado
        """
        from pydantic.fields import Field

        # Extraer validaciones comunes
        default_value = ... if required else None
        description = field_schema.get("description", "")

        # Validaciones específicas por tipo
        field_type = field_schema.get("type")

        if field_type == "string":
            min_length = field_schema.get("minLength")
            max_length = field_schema.get("maxLength")
            pattern = field_schema.get("pattern")
            enum_values = field_schema.get("enum")

            if enum_values:
                # Para enums, devolver el tipo literal
                return Field(default=default_value, description=description)
            else:
                return Field(
                    default=default_value,
                    description=description,
                    min_length=min_length,
                    max_length=max_length,
                    pattern=pattern
                )

        elif field_type in ["integer", "number"]:
            minimum = field_schema.get("minimum")
            maximum = field_schema.get("maximum")

            return Field(
                default=default_value,
                description=description,
                ge=minimum,
                le=maximum
            )

        elif field_type == "array":
            min_items = field_schema.get("minItems")
            max_items = field_schema.get("maxItems")

            return Field(
                default=default_value if required else [],
                description=description,
                min_length=min_items,
                max_length=max_items
            )

        else:
            return Field(default=default_value, description=description)


class PydanticFallbackParser:
    """
    Parser de fallback que usa Pydantic para validar respuestas LLM post-generación.
    """

    def __init__(self):
        if not PYDANTIC_AVAILABLE:
            raise ImportError("Pydantic no disponible para fallback parsing")

        self.converter = PydanticSchemaConverter()

    def parse_and_validate_response(
        self,
        generated_text: str,
        schema: Dict[str, Any],
        model_name: str = "fallback_model"
    ) -> Optional[Dict[str, Any]]:
        """
        Intenta parsear el texto generado como JSON y validarlo contra el esquema usando Pydantic.

        Args:
            generated_text: Texto generado por el LLM
            schema: JSON Schema para validación
            model_name: Nombre del modelo Pydantic a generar

        Returns:
            Dict validado si el parsing y validación tienen éxito, None si falla
        """
        try:
            # Paso 1: Intentar parsear como JSON
            parsed_json = self._extract_json_from_text(generated_text)
            if parsed_json is None:
                logger.debug("No se pudo extraer JSON válido del texto generado")
                return None

            # Paso 2: Convertir esquema a modelo Pydantic
            pydantic_model = self.converter.json_schema_to_pydantic_model(schema, model_name)

            # Paso 3: Validar usando Pydantic
            validated_instance = pydantic_model(**parsed_json)

            # Paso 4: Convertir de vuelta a dict
            validated_dict = validated_instance.model_dump()

            logger.info("Validación Pydantic exitosa para respuesta post-generación")
            return validated_dict

        except ValidationError as e:
            logger.warning(f"Validación Pydantic falló: {e}")
            return None
        except Exception as e:
            logger.error(f"Error en parsing Pydantic fallback: {e}")
            return None

    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extrae JSON válido del texto generado por LLM.

        Args:
            text: Texto que puede contener JSON

        Returns:
            Dict JSON parseado o None si no se encuentra JSON válido
        """
        import re

        # Estrategias para extraer JSON:
        # 1. Buscar bloques JSON delimitados por ```json ... ```
        json_block_pattern = r'```json\s*\n(.*?)\n```'
        match = re.search(json_block_pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # 2. Buscar objetos JSON entre llaves { ... }
        # Encontrar el objeto JSON más grande (más externo)
        brace_pattern = r'\{.*\}'
        matches = re.findall(brace_pattern, text, re.DOTALL)
        if matches:
            # Probar desde el más largo hacia el más corto
            for potential_json in sorted(matches, key=len, reverse=True):
                try:
                    parsed = json.loads(potential_json)
                    if isinstance(parsed, dict):
                        return parsed
                except json.JSONDecodeError:
                    continue

        # 3. Intentar parsear todo el texto como JSON
        try:
            parsed = json.loads(text.strip())
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        # 4. Buscar arrays JSON [ ... ]
        array_pattern = r'\[.*\]'
        matches = re.findall(array_pattern, text, re.DOTALL)
        if matches:
            for potential_json in sorted(matches, key=len, reverse=True):
                try:
                    parsed = json.loads(potential_json)
                    if isinstance(parsed, list) and len(parsed) > 0:
                        # Si es un array, wrap en un objeto
                        return {"items": parsed}
                except json.JSONDecodeError:
                    continue

        return None

    def create_structured_response_from_text(
        self,
        generated_text: str,
        schema: Dict[str, Any],
        model_name: str = "EmpoorioLM",
        model_version: str = "v1.0.0",
        prompt_tokens: int = 0,
        completion_tokens: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Crea una respuesta estructurada completa usando el fallback Pydantic.

        Args:
            generated_text: Texto generado por LLM
            schema: JSON Schema utilizado
            model_name: Nombre del modelo
            model_version: Versión del modelo
            prompt_tokens: Tokens del prompt
            completion_tokens: Tokens de completion

        Returns:
            Respuesta estructurada completa o None si falla
        """
        validated_content = self.parse_and_validate_response(generated_text, schema)
        if validated_content is None:
            return None

        # Crear respuesta estructurada completa
        from .base import BaseLLMResponseSchema

        response = BaseLLMResponseSchema.create_base_response(
            response_id=str(uuid.uuid4()),
            model_name=model_name,
            model_version=model_version,
            total_tokens=prompt_tokens + completion_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            processing_time_seconds=0.0,  # No medido en fallback
            metadata={
                "parsing_method": "pydantic_fallback",
                "validation_passed": True,
                "schema_validated": True
            },
            content=validated_content,
            validation={
                "schema_version": schema.get("$id", "unknown"),
                "validated_at": datetime.now().isoformat(),
                "is_valid": True,
                "validation_method": "pydantic_post_generation"
            }
        )

        return response


# Instancia global para uso en la API
try:
    pydantic_fallback_parser = PydanticFallbackParser()
    PYDANTIC_FALLBACK_AVAILABLE = True
except ImportError:
    pydantic_fallback_parser = None
    PYDANTIC_FALLBACK_AVAILABLE = False


def is_pydantic_fallback_available() -> bool:
    """Verificar si el fallback Pydantic está disponible."""
    return PYDANTIC_FALLBACK_AVAILABLE


def parse_with_pydantic_fallback(
    generated_text: str,
    schema: Dict[str, Any],
    **kwargs
) -> Optional[Dict[str, Any]]:
    """
    Función de conveniencia para usar el fallback Pydantic.

    Args:
        generated_text: Texto generado por LLM
        schema: JSON Schema para validación
        **kwargs: Parámetros adicionales para create_structured_response_from_text

    Returns:
        Respuesta estructurada o None
    """
    if not PYDANTIC_FALLBACK_AVAILABLE:
        logger.warning("Fallback Pydantic no disponible")
        return None

    return pydantic_fallback_parser.create_structured_response_from_text(
        generated_text=generated_text,
        schema=schema,
        **kwargs
    )