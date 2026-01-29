"""
AILOOS JSON Schema Definitions
Esquemas JSON Schema para validación de respuestas estructuradas de LLM.
"""

from .base import BaseLLMResponseSchema
from .rag import RAGQueryResponseSchema, RAGHealthResponseSchema
from .federated import (
    FederatedSessionResponseSchema,
    FederatedNodeResponseSchema,
    FederatedMetricsResponseSchema,
    FederatedTrainingUpdateSchema
)
from .inference import InferenceResponseSchema, InferenceHealthResponseSchema
from .serialization import TOONResponseSchema, VSCResponseSchema
from .guidance_integration import (
    GuidanceSchemaConverter,
    StructuredOutputGenerator,
    create_structured_inference_response,
    is_guidance_available
)
from .pydantic_fallback import (
    PydanticSchemaConverter,
    PydanticFallbackParser,
    is_pydantic_fallback_available,
    parse_with_pydantic_fallback
)

__all__ = [
    'BaseLLMResponseSchema',
    'RAGQueryResponseSchema',
    'RAGHealthResponseSchema',
    'FederatedSessionResponseSchema',
    'FederatedNodeResponseSchema',
    'FederatedMetricsResponseSchema',
    'FederatedTrainingUpdateSchema',
    'InferenceResponseSchema',
    'InferenceHealthResponseSchema',
    'TOONResponseSchema',
    'VSCResponseSchema',
    'GuidanceSchemaConverter',
    'StructuredOutputGenerator',
    'create_structured_inference_response',
    'is_guidance_available',
    'PydanticSchemaConverter',
    'PydanticFallbackParser',
    'is_pydantic_fallback_available',
    'parse_with_pydantic_fallback'
]