"""
Integración de Guidance para generación forzada de salidas estructuradas.
Convierte esquemas JSON Schema a gramáticas Guidance para control de generación.
"""

from typing import Dict, Any, Optional, Union, List
import json
import logging
from pathlib import Path

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    TORCH_AVAILABLE = False

try:
    import guidance
    # Verificar que tenga los atributos necesarios
    if hasattr(guidance, 'Program'):
        GUIDANCE_AVAILABLE = True
    else:
        raise ImportError("Guidance library missing required attributes")
except ImportError:
    guidance = type('MockGuidance', (), {'Program': Any})()  # Mock object
    GUIDANCE_AVAILABLE = False

from .base import BaseLLMResponseSchema
from .inference import InferenceResponseSchema
from .serialization import TOONResponseSchema, VSCResponseSchema
from .pydantic_fallback import (
    is_pydantic_fallback_available,
    parse_with_pydantic_fallback,
    pydantic_fallback_parser
)

logger = logging.getLogger(__name__)


class GuidanceSchemaConverter:
    """
    Convierte esquemas JSON Schema a gramáticas Guidance para generación estructurada.
    """

    def __init__(self):
        if not GUIDANCE_AVAILABLE:
            raise ImportError("Guidance library no está disponible. Instale con: pip install guidance")

    @staticmethod
    def json_schema_to_guidance_grammar(schema: Dict[str, Any]) -> str:
        """
        Convierte un JSON Schema a una gramática Guidance.

        Args:
            schema: JSON Schema a convertir

        Returns:
            Gramática Guidance como string
        """
        return json.dumps(schema)  # Guidance puede usar JSON Schema directamente

    @staticmethod
    def create_inference_grammar(schema_type: str = "inference") -> Dict[str, Any]:
        """
        Crear gramática Guidance para diferentes tipos de esquemas de inferencia.

        Args:
            schema_type: Tipo de esquema ('inference', 'toon', 'vsc')

        Returns:
            Esquema JSON Schema optimizado para Guidance
        """
        if schema_type == "inference":
            return InferenceResponseSchema.get_schema()
        elif schema_type == "toon":
            return TOONResponseSchema.get_schema()
        elif schema_type == "vsc":
            return VSCResponseSchema.get_schema()
        else:
            raise ValueError(f"Tipo de esquema no soportado: {schema_type}")

    def create_guidance_program(
        self,
        prompt: str,
        schema: Dict[str, Any],
        model=None
    ) -> Optional[guidance.Program]:
        """
        Crear un programa Guidance con generación estructurada.

        Args:
            prompt: Prompt de entrada
            schema: JSON Schema para la salida
            model: Modelo Guidance (opcional)

        Returns:
            Programa Guidance configurado
        """
        if not GUIDANCE_AVAILABLE:
            return None

        try:
            # Crear programa con generación JSON forzada
            program = guidance.Program(
                f"""{prompt}

Responde con un JSON válido que cumpla este esquema:
{json.dumps(schema, indent=2)}

Respuesta JSON: {{
{guidance.gen_json(schema=schema)}
}}"""
            )

            return program

        except Exception as e:
            logger.error(f"Error creando programa Guidance: {e}")
            return None

    def generate_structured_output(
        self,
        prompt: str,
        schema: Dict[str, Any],
        model,
        **generation_kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Generar salida estructurada usando Guidance.

        Args:
            prompt: Prompt de entrada
            schema: JSON Schema para validar la salida
            model: Modelo para generación
            **generation_kwargs: Parámetros adicionales de generación

        Returns:
            Salida estructurada como dict, o None si falla
        """
        if not GUIDANCE_AVAILABLE:
            logger.warning("Guidance no disponible, retornando None")
            return None

        try:
            # Crear programa Guidance
            program = self.create_guidance_program(prompt, schema, model)
            if program is None:
                return None

            # Ejecutar generación
            result = program(
                model=model,
                **generation_kwargs
            )

            # Extraer JSON generado
            json_output = result["json_output"] if "json_output" in result else None

            if json_output:
                # Validar contra esquema
                if self.validate_output(json_output, schema):
                    return json_output
                else:
                    logger.warning("Salida generada no cumple con el esquema")
                    return None

            return None

        except Exception as e:
            logger.error(f"Error en generación Guidance: {e}")
            return None

    @staticmethod
    def validate_output(output: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """
        Validar salida contra esquema JSON Schema.

        Args:
            output: Salida a validar
            schema: Esquema para validación

        Returns:
            True si es válida
        """
        try:
            import jsonschema
            jsonschema.validate(output, schema)
            return True
        except (jsonschema.ValidationError, ImportError):
            return False

    def create_inference_guidance(
        self,
        prompt: str,
        output_format: str = "inference",
        model=None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Crear programa Guidance específico para inferencia.

        Args:
            prompt: Prompt del usuario
            output_format: Formato de salida ('inference', 'toon', 'vsc')
            model: Modelo para generación
            **kwargs: Parámetros adicionales

        Returns:
            Resultado de generación estructurada
        """
        # Obtener esquema apropiado
        schema = self.create_inference_grammar(output_format)

        # Generar con Guidance
        return self.generate_structured_output(
            prompt=prompt,
            schema=schema,
            model=model,
            **kwargs
        )


class StructuredOutputGenerator:
    """
    Generador de salidas estructuradas usando Guidance con esquemas AILOOS.
    Incluye fallback Pydantic para parsing post-generación cuando Guidance no está disponible.
    """

    def __init__(self):
        self.converter = GuidanceSchemaConverter() if GUIDANCE_AVAILABLE else None
        self.pydantic_fallback_available = is_pydantic_fallback_available()

        # Métricas para fallback Pydantic
        self.metrics = {
            "pydantic_fallback_attempts": 0,
            "pydantic_fallback_successes": 0,
            "pydantic_fallback_failures": 0,
            "guidance_to_pydantic_fallbacks": 0
        }

    def is_available(self) -> bool:
        """Verificar si Guidance está disponible."""
        return self.converter is not None

    def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del generador estructurado."""
        total_attempts = self.metrics["pydantic_fallback_attempts"]
        success_rate = (self.metrics["pydantic_fallback_successes"] / total_attempts) if total_attempts > 0 else 0.0

        return {
            **self.metrics,
            "pydantic_fallback_success_rate": success_rate,
            "guidance_available": self.is_available(),
            "pydantic_fallback_available": self.pydantic_fallback_available
        }

    def generate_inference_response(
        self,
        prompt: str,
        output_format: str = "inference",
        model=None,
        **generation_kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Generar respuesta de inferencia estructurada con fallback Pydantic.

        Args:
            prompt: Prompt de entrada
            output_format: Formato ('inference', 'toon', 'vsc')
            model: Modelo para generación
            **generation_kwargs: Parámetros de generación

        Returns:
            Respuesta estructurada o None
        """
        # Obtener esquema apropiado
        schema = self.converter.create_inference_grammar(output_format)

        # Usar generate_with_schema que incluye fallback
        return self.generate_with_schema(
            prompt=prompt,
            schema=schema,
            model=model,
            **generation_kwargs
        )

    def generate_with_schema(
        self,
        prompt: str,
        schema: Dict[str, Any],
        model=None,
        **generation_kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Generar salida con esquema personalizado usando Guidance con fallback Pydantic.

        Args:
            prompt: Prompt de entrada
            schema: JSON Schema personalizado
            model: Modelo para generación
            **generation_kwargs: Parámetros de generación

        Returns:
            Salida estructurada o None
        """
        # Intentar primero con Guidance
        if self.is_available():
            guidance_result = self.converter.generate_structured_output(
                prompt=prompt,
                schema=schema,
                model=model,
                **generation_kwargs
            )
            if guidance_result is not None:
                return guidance_result

        # Fallback: Generar texto normal y usar Pydantic para parsing post-generación
        if self.pydantic_fallback_available:
            logger.info("Guidance falló o no disponible, intentando fallback Pydantic")
            self.metrics["guidance_to_pydantic_fallbacks"] += 1
            return self._generate_with_pydantic_fallback(
                prompt=prompt,
                schema=schema,
                model=model,
                **generation_kwargs
            )

        # Ningún método disponible
        logger.warning("Ni Guidance ni fallback Pydantic disponibles")
        return None

    def _generate_with_pydantic_fallback(
        self,
        prompt: str,
        schema: Dict[str, Any],
        model=None,
        **generation_kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Generar texto normal y usar Pydantic para parsing post-generación.

        Args:
            prompt: Prompt de entrada
            schema: JSON Schema para validación
            model: Modelo para generación
            **generation_kwargs: Parámetros de generación

        Returns:
            Respuesta estructurada validada o None
        """
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch no disponible para fallback Pydantic")
            return None

        try:
            self.metrics["pydantic_fallback_attempts"] += 1

            # Crear prompt mejorado para fomentar salida JSON
            enhanced_prompt = f"""{prompt}

Por favor, responde con un JSON válido que cumpla con el siguiente esquema:
{json.dumps(schema, indent=2, ensure_ascii=False)}

Respuesta JSON:"""

            # Generar texto normal (sin Guidance)
            if model is None:
                logger.warning("No se proporcionó modelo para fallback Pydantic")
                self.metrics["pydantic_fallback_failures"] += 1
                return None

            # Generar con el modelo (asumiendo interfaz estándar de transformers)
            inputs = model.tokenizer(enhanced_prompt, return_tensors="pt")
            if hasattr(model, 'device'):
                inputs = {k: v.to(model.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=generation_kwargs.get('max_tokens', 512),
                    temperature=generation_kwargs.get('temperature', 0.7),
                    top_p=generation_kwargs.get('top_p', 0.9),
                    top_k=generation_kwargs.get('top_k', 50),
                    do_sample=generation_kwargs.get('do_sample', True),
                    pad_token_id=model.tokenizer.pad_token_id,
                    eos_token_id=model.tokenizer.eos_token_id
                )

            # Decodificar respuesta
            generated_text = model.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Extraer y validar con Pydantic
            fallback_result = pydantic_fallback_parser.parse_and_validate_response(
                generated_text=generated_text,
                schema=schema,
                model_name="pydantic_fallback_model"
            )

            if fallback_result:
                logger.info("Fallback Pydantic exitoso")
                self.metrics["pydantic_fallback_successes"] += 1
                return fallback_result
            else:
                logger.warning("Fallback Pydantic falló en validación")
                self.metrics["pydantic_fallback_failures"] += 1
                return None

        except Exception as e:
            logger.error(f"Error en fallback Pydantic: {e}")
            self.metrics["pydantic_fallback_failures"] += 1
            return None


# Instancia global para uso en la API
structured_output_generator = StructuredOutputGenerator()


def create_structured_inference_response(
    prompt: str,
    output_format: str = "inference",
    model=None,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """
    Función de conveniencia para generar respuestas estructuradas.

    Args:
        prompt: Prompt de entrada
        output_format: Formato de salida
        model: Modelo para generación
        **kwargs: Parámetros adicionales

    Returns:
        Respuesta estructurada
    """
    return structured_output_generator.generate_inference_response(
        prompt=prompt,
        output_format=output_format,
        model=model,
        **kwargs
    )


def is_guidance_available() -> bool:
    """Verificar disponibilidad de Guidance."""
    return GUIDANCE_AVAILABLE