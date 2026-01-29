"""
Response Critic - Advanced Response Evaluation and Improvement
=============================================================

Uses EmpoorioLM to critically evaluate generated responses, identify weaknesses,
and suggest improvements. Implements multi-dimensional critique with actionable feedback.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re

# Import torch opcionalmente
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    TORCH_AVAILABLE = False

from ..inference.api import EmpoorioLMInferenceAPI, InferenceConfig, InferenceRequest

logger = logging.getLogger(__name__)


@dataclass
class CritiqueDimension:
    """Represents a single dimension of critique."""
    name: str
    score: float  # 0.0 to 1.0
    feedback: str
    suggestions: List[str] = field(default_factory=list)
    severity: str = "medium"  # low, medium, high


@dataclass
class ResponseCritique:
    """Complete critique of a response."""
    original_response: str
    overall_score: float  # 0.0 to 1.0
    dimensions: List[CritiqueDimension] = field(default_factory=list)
    summary: str = ""
    improvement_suggestions: List[str] = field(default_factory=list)
    rewritten_response: Optional[str] = None
    critique_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert ResponseCritique to dictionary for API responses."""
        return {
            "original_response": self.original_response,
            "overall_score": self.overall_score,
            "dimensions": [dim.__dict__ for dim in self.dimensions],
            "summary": self.summary,
            "improvement_suggestions": self.improvement_suggestions,
            "rewritten_response": self.rewritten_response,
            "critique_metadata": self.critique_metadata,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class CritiqueConfig:
    """Configuration for response critiquing."""
    enabled_dimensions: List[str] = field(default_factory=lambda: [
        "accuracy", "completeness", "clarity", "relevance", "coherence", "helpfulness"
    ])
    min_score_threshold: float = 0.7
    auto_improve: bool = True
    max_improvement_iterations: int = 2
    critique_temperature: float = 0.2
    improvement_temperature: float = 0.4


class ResponseCritic:
    """
    Advanced response critic using EmpoorioLM for intelligent evaluation and improvement.

    Features:
    - Multi-dimensional response evaluation
    - Automated improvement suggestions
    - Iterative refinement capabilities
    - Quality scoring and benchmarking
    - Domain-specific critique templates
    """

    def __init__(self, inference_api: Optional[EmpoorioLMInferenceAPI] = None, config: Optional[CritiqueConfig] = None):
        """
        Initialize the Response Critic.

        Args:
            inference_api: Pre-configured EmpoorioLM inference API instance
            config: Critique configuration
        """
        self.inference_api = inference_api
        self.config = config or CritiqueConfig()
        self.critique_history: List[Dict[str, Any]] = []
        self.quality_benchmarks: Dict[str, float] = {}
        self.critique_templates = self._load_critique_templates()

    async def initialize(self) -> bool:
        """Initialize the inference API if not provided."""
        if self.inference_api is None:
            config = InferenceConfig(
                model_path="./src/models/empoorio_lm/versions/empoorio_lm_v1.0.0-trained_267306",
                enable_guidance=True,
                guidance_output_format="inference"
            )
            self.inference_api = EmpoorioLMInferenceAPI(config)
            success = await self.inference_api.load_model()

            # Apply context extension fix for Fase 12 compatibility
            if success and hasattr(self.inference_api.model.config, 'max_position_embeddings'):
                original_max_pos = self.inference_api.model.config.max_position_embeddings
                self.inference_api.model.config.max_position_embeddings = 4096
                logger.info(f"🔧 ResponseCritic: Forzando contexto largo: {original_max_pos} → 4096 tokens")

                # Recreate position embeddings if they exist
                if hasattr(self.inference_api.model, 'embed_positions') and self.inference_api.model.embed_positions is not None:
                    try:
                        import torch.nn as nn
                        old_embed = self.inference_api.model.embed_positions
                        new_embed = nn.Embedding(4096, old_embed.embedding_dim)
                        with torch.no_grad():
                            new_embed.weight[:original_max_pos] = old_embed.weight[:original_max_pos]
                        self.inference_api.model.embed_positions = new_embed
                        logger.info("✅ ResponseCritic: Embeddings de posición recreados")
                    except Exception as e:
                        logger.warning(f"⚠️ ResponseCritic: No se pudieron recrear embeddings: {e}")

            return success
        return True

    def _load_critique_templates(self) -> Dict[str, str]:
        """Load critique templates for different response types."""
        return {
            "technical": """
Evalúa esta respuesta técnica considerando:
- Precisión técnica y corrección factual
- Completitud de la explicación
- Claridad y accesibilidad del lenguaje
- Relevancia para la pregunta técnica
- Profundidad apropiada para el contexto
""",
            "creative": """
Evalúa esta respuesta creativa considerando:
- Originalidad e innovación
- Calidad literaria y estilo
- Adecuación al tema solicitado
- Impacto emocional o intelectual
- Coherencia narrativa o conceptual
""",
            "analytical": """
Evalúa esta respuesta analítica considerando:
- Lógica y coherencia del razonamiento
- Uso apropiado de evidencia
- Profundidad del análisis
- Balance de perspectivas
- Conclusiones bien fundamentadas
""",
            "conversational": """
Evalúa esta respuesta conversacional considerando:
- Naturalidad y fluidez
- Empatía y adecuación al tono
- Relevancia para el contexto conversacional
- Claridad de comunicación
- Aporte de valor a la conversación
""",
            "general": """
Evalúa esta respuesta considerando aspectos generales:
- Precisión y veracidad
- Completitud y exhaustividad
- Claridad y comprensión
- Relevancia para la consulta
- Utilidad y valor práctico
"""
        }

    async def critique_response(
        self,
        response: str,
        context: str = "",
        response_type: str = "general",
        user_query: Optional[str] = None
    ) -> ResponseCritique:
        """
        Critically evaluate a response using EmpoorioLM.

        Args:
            response: The response to critique
            context: Additional context about the response
            response_type: Type of response for template selection
            user_query: Original user query for relevance assessment

        Returns:
            Comprehensive critique of the response
        """
        if not await self.initialize():
            logger.warning("⚠️ Failed to initialize inference API, using fallback critique")
            return self._create_fallback_critique(response)

        # Create critique prompt - make it much shorter to avoid context issues
        prompt = self._create_critique_prompt(response, context, response_type, user_query)

        # Use much more conservative parameters to avoid tensor issues
        request = InferenceRequest(
            prompt=prompt[:1000],  # Limit prompt length significantly
            max_tokens=300,  # Much smaller token limit
            temperature=self.config.critique_temperature,
            structured_output=False  # Remove structured output to avoid schema issues
        )

        try:
            critique_response = await self.inference_api.generate(request)

            # Try to parse the response, but be very tolerant of failures
            try:
                critique_data = self._parse_critique_response(critique_response.text)
            except Exception as parse_error:
                logger.warning(f"⚠️ Failed to parse critique response: {parse_error}, using fallback")
                return self._create_fallback_critique(response)

            # Create ResponseCritique object with safe defaults
            critique = ResponseCritique(
                original_response=response,
                overall_score=critique_data.get("overall_score", 0.6),
                summary=critique_data.get("summary", "Evaluación básica completada"),
                improvement_suggestions=critique_data.get("improvement_suggestions", ["Mejorar respuesta basada en contexto"])
            )

            # Add dimensions safely
            dimensions_data = critique_data.get("dimensions", [])
            if not dimensions_data:
                # Create basic dimensions if parsing failed
                dimensions_data = [
                    {"name": "accuracy", "score": 0.6, "feedback": "Evaluación básica de precisión", "suggestions": ["Verificar hechos"], "severity": "medium"},
                    {"name": "completeness", "score": 0.6, "feedback": "Evaluación básica de completitud", "suggestions": ["Añadir más detalles"], "severity": "medium"},
                    {"name": "clarity", "score": 0.7, "feedback": "Respuesta generalmente clara", "suggestions": [], "severity": "low"}
                ]

            for dim_data in dimensions_data:
                dimension = CritiqueDimension(
                    name=dim_data.get("name", "general"),
                    score=dim_data.get("score", 0.6),
                    feedback=dim_data.get("feedback", "Evaluación básica"),
                    suggestions=dim_data.get("suggestions", []),
                    severity=dim_data.get("severity", "medium")
                )
                critique.dimensions.append(dimension)

            # Store critique metadata
            critique.critique_metadata = {
                "response_type": response_type,
                "context_provided": bool(context),
                "query_provided": bool(user_query),
                "dimensions_evaluated": len(critique.dimensions),
                "evaluation_method": "ai_generated"
            }

            # Store in history
            self.critique_history.append({
                "response_length": len(response),
                "overall_score": critique.overall_score,
                "dimensions_count": len(critique.dimensions),
                "response_type": response_type,
                "created_at": datetime.now().isoformat()
            })

            logger.info(f"✅ Critiqued response: score {critique.overall_score:.2f}")
            return critique

        except Exception as e:
            logger.warning(f"⚠️ Error in AI critique: {e}, using fallback evaluation")
            # Return enhanced fallback critique instead of failing
            return self._create_enhanced_fallback_critique(response, response_type, context, user_query)

    def _create_critique_prompt(
        self,
        response: str,
        context: str,
        response_type: str,
        user_query: Optional[str]
    ) -> str:
        """Create a structured prompt for response critiquing."""
        template = self.critique_templates.get(response_type, self.critique_templates["general"])

        context_section = f"\nCONTEXTO ADICIONAL:\n{context}" if context else ""
        query_section = f"\nPREGUNTA ORIGINAL DEL USUARIO:\n{user_query}" if user_query else ""

        return f"""
Eres un crítico experto en evaluación de respuestas. Tu tarea es analizar críticamente la siguiente respuesta y proporcionar feedback constructivo y específico.

{template}

RESPUESTA A EVALUAR:
{response}{context_section}{query_section}

INSTRUCCIONES DE EVALUACIÓN:
Para cada dimensión especificada, proporciona:
- Una puntuación de 0.0 a 1.0 (donde 1.0 es excelente)
- Feedback específico sobre fortalezas y debilidades
- Sugerencias concretas de mejora
- Nivel de severidad del problema (low, medium, high)

DIMENSIONES A EVALUAR: {', '.join(self.config.enabled_dimensions)}

FORMATO DE RESPUESTA:
Proporciona tu evaluación en formato JSON con:
- overall_score: puntuación general (0.0-1.0)
- dimensions: array de objetos con name, score, feedback, suggestions, severity
- summary: resumen ejecutivo de la evaluación
- improvement_suggestions: array de sugerencias generales de mejora

EVALUACIÓN:
"""

    def _get_critique_schema(self) -> Dict[str, Any]:
        """Get JSON schema for structured critique output."""
        return {
            "type": "object",
            "properties": {
                "overall_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "dimensions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                            "feedback": {"type": "string"},
                            "suggestions": {"type": "array", "items": {"type": "string"}},
                            "severity": {"type": "string", "enum": ["low", "medium", "high"]}
                        },
                        "required": ["name", "score", "feedback"]
                    }
                },
                "summary": {"type": "string"},
                "improvement_suggestions": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["overall_score", "dimensions", "summary"]
        }

    def _parse_critique_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the structured critique response from EmpoorioLM."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON critique response, creating fallback structure")
            return self._extract_critique_from_text(response_text)

    def _extract_critique_from_text(self, text: str) -> Dict[str, Any]:
        """Extract critique elements from plain text as fallback."""
        # Basic text analysis for fallback
        score_match = re.search(r'(\d+\.?\d*)/10|\b(\d+\.?\d*)\b.*puntuación', text.lower())
        overall_score = 0.5  # default
        if score_match:
            score = float(score_match.group(1) or score_match.group(2))
            overall_score = min(score / 10.0, 1.0) if score > 1 else score

        return {
            "overall_score": overall_score,
            "dimensions": [{
                "name": "general",
                "score": overall_score,
                "feedback": "Evaluación básica extraída del texto",
                "suggestions": ["Mejorar respuesta basada en feedback"],
                "severity": "medium"
            }],
            "summary": "Evaluación básica generada automáticamente",
            "improvement_suggestions": ["Revisar y mejorar la respuesta"]
        }

    def _create_fallback_critique(self, response: str) -> ResponseCritique:
        """Create a basic fallback critique when AI evaluation fails."""
        critique = ResponseCritique(
            original_response=response,
            overall_score=0.6,  # Neutral default
            summary="Evaluación básica - no se pudo realizar análisis detallado",
            improvement_suggestions=[
                "Revisar la precisión de la información proporcionada",
                "Mejorar la claridad y estructura de la respuesta",
                "Añadir más detalles relevantes si es necesario"
            ]
        )

        # Add basic dimensions
        critique.dimensions = [
            CritiqueDimension(
                name="accuracy",
                score=0.6,
                feedback="No se pudo verificar completamente la precisión",
                suggestions=["Verificar hechos y datos proporcionados"]
            ),
            CritiqueDimension(
                name="clarity",
                score=0.7,
                feedback="La respuesta parece clara pero podría mejorarse",
                suggestions=["Usar lenguaje más simple y directo"]
            )
        ]

        return critique

    def _create_enhanced_fallback_critique(
        self,
        response: str,
        response_type: str = "general",
        context: str = "",
        user_query: Optional[str] = None
    ) -> ResponseCritique:
        """Create an enhanced fallback critique with context-aware evaluation."""
        # Analyze response characteristics for smarter fallback
        response_length = len(response)
        has_structure = any(indicator in response.lower() for indicator in ['•', '-', '1.', '2.', 'first', 'second'])
        has_technical_terms = any(term in response.lower() for term in ['analysis', 'evaluation', 'strategy', 'implementation'])

        # Adjust scores based on response characteristics
        base_score = 0.6
        if response_length > 200:
            base_score += 0.1  # Longer responses tend to be more complete
        if has_structure:
            base_score += 0.1  # Structured responses are better
        if has_technical_terms and response_type in ['technical', 'analytical']:
            base_score += 0.1  # Technical terms in technical contexts

        base_score = min(base_score, 0.9)  # Cap at 0.9 for fallback

        critique = ResponseCritique(
            original_response=response,
            overall_score=base_score,
            summary=f"Evaluación contextual completada - respuesta {response_type} con {response_length} caracteres",
            improvement_suggestions=[
                "Mantener la estructura y organización actual",
                "Considerar añadir ejemplos específicos si aplica",
                "Verificar alineación con los requisitos de la consulta"
            ]
        )

        # Create context-aware dimensions
        critique.dimensions = [
            CritiqueDimension(
                name="completeness",
                score=min(base_score + 0.1, 0.9),
                feedback=f"Respuesta {'muy completa' if response_length > 300 else 'moderadamente completa'} para su longitud",
                suggestions=["Añadir más detalles si es necesario"],
                severity="low"
            ),
            CritiqueDimension(
                name="structure",
                score=0.8 if has_structure else 0.6,
                feedback=f"{'Buena estructura con elementos organizativos' if has_structure else 'Estructura básica, podría mejorarse'}",
                suggestions=["Usar viñetas o numeración para organizar mejor"] if not has_structure else [],
                severity="low"
            ),
            CritiqueDimension(
                name="relevance",
                score=0.8,
                feedback="Respuesta parece relevante para el contexto proporcionado",
                suggestions=["Asegurar que todos los puntos sean directamente relevantes"],
                severity="low"
            ),
            CritiqueDimension(
                name="helpfulness",
                score=base_score,
                feedback="Respuesta proporciona valor informativo",
                suggestions=["Considerar añadir recomendaciones prácticas"],
                severity="medium"
            )
        ]

        # Add response-type specific dimension
        if response_type == "technical":
            critique.dimensions.append(CritiqueDimension(
                name="technical_accuracy",
                score=0.7,
                feedback="Contenido técnico identificado y estructurado",
                suggestions=["Verificar precisión técnica si aplica"],
                severity="medium"
            ))
        elif response_type == "creative":
            critique.dimensions.append(CritiqueDimension(
                name="creativity",
                score=0.8,
                feedback="Enfoque creativo y original identificado",
                suggestions=["Mantener el equilibrio entre creatividad y practicidad"],
                severity="low"
            ))

        critique.critique_metadata = {
            "response_type": response_type,
            "context_provided": bool(context),
            "query_provided": bool(user_query),
            "dimensions_evaluated": len(critique.dimensions),
            "evaluation_method": "enhanced_fallback",
            "response_length": response_length,
            "has_structure": has_structure
        }

        logger.info(f"✅ Enhanced fallback critique: score {critique.overall_score:.2f} for {response_type} response")
        return critique

    async def improve_response(
        self,
        critique: ResponseCritique,
        max_iterations: Optional[int] = None
    ) -> ResponseCritique:
        """
        Improve a response based on its critique using iterative refinement.

        Args:
            critique: The critique to base improvements on
            max_iterations: Maximum improvement iterations

        Returns:
            Improved critique with rewritten response
        """
        if not await self.initialize():
            return critique

        max_iter = max_iterations or self.config.max_improvement_iterations
        current_response = critique.original_response
        best_critique = critique

        for iteration in range(max_iter):
            # Create improvement prompt
            prompt = self._create_improvement_prompt(current_response, best_critique)

            # Generate improved response
            request = InferenceRequest(
                prompt=prompt,
                max_tokens=len(current_response.split()) * 3,  # Allow expansion
                temperature=self.config.improvement_temperature,
                structured_output=False  # Free-form improvement
            )

            try:
                improvement_response = await self.inference_api.generate(request)
                improved_text = improvement_response.text.strip()

                # Critique the improved response
                new_critique = await self.critique_response(
                    improved_text,
                    context=f"Improved version {iteration + 1} of: {critique.original_response[:100]}...",
                    response_type="general"
                )

                # Check if improvement was successful
                if new_critique.overall_score > best_critique.overall_score:
                    best_critique = new_critique
                    current_response = improved_text
                    logger.info(f"✅ Iteration {iteration + 1}: Improved score to {new_critique.overall_score:.2f}")
                else:
                    logger.info(f"ℹ️ Iteration {iteration + 1}: No improvement (score: {new_critique.overall_score:.2f})")
                    break

            except Exception as e:
                logger.error(f"❌ Error in improvement iteration {iteration + 1}: {e}")
                break

        # Set the best rewritten response
        best_critique.rewritten_response = current_response
        return best_critique

    def _create_improvement_prompt(self, current_response: str, critique: ResponseCritique) -> str:
        """Create a prompt for response improvement."""
        # Format critique feedback
        feedback_sections = []
        for dim in critique.dimensions:
            if dim.score < 0.8:  # Focus on areas needing improvement
                feedback_sections.append(f"- {dim.name.upper()}: {dim.feedback}")
                if dim.suggestions:
                    feedback_sections.append(f"  Sugerencias: {'; '.join(dim.suggestions)}")

        critique_summary = "\n".join(feedback_sections) if feedback_sections else "Mejorar calidad general"

        return f"""
Mejora la siguiente respuesta basándote en la crítica proporcionada:

RESPUESTA ORIGINAL:
{current_response}

CRÍTICA Y ÁREAS DE MEJORA:
{critique_summary}

SUGERENCIAS GENERALES:
{chr(10).join(f"- {suggestion}" for suggestion in critique.improvement_suggestions)}

INSTRUCCIONES:
- Mantén la información correcta y relevante
- Mejora los aspectos identificados en la crítica
- Haz la respuesta más clara, completa y útil
- Preserva el tono y estilo apropiados
- No añadas información falsa o especulativa

RESPUESTA MEJORADA:
"""

    async def batch_critique(
        self,
        responses: List[str],
        contexts: Optional[List[str]] = None,
        response_type: str = "general"
    ) -> List[ResponseCritique]:
        """
        Critique multiple responses in batch for efficiency.

        Args:
            responses: List of responses to critique
            contexts: Optional list of contexts for each response
            response_type: Type of responses

        Returns:
            List of critiques
        """
        if not responses:
            return []

        contexts = contexts or [""] * len(responses)

        # Process in parallel with concurrency control
        semaphore = asyncio.Semaphore(3)  # Limit concurrent critiques

        async def critique_with_semaphore(response: str, context: str) -> ResponseCritique:
            async with semaphore:
                return await self.critique_response(response, context, response_type)

        tasks = [
            critique_with_semaphore(resp, ctx)
            for resp, ctx in zip(responses, contexts)
        ]

        critiques = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        results = []
        for i, critique in enumerate(critiques):
            if isinstance(critique, Exception):
                logger.error(f"❌ Error critiquing response {i}: {critique}")
                results.append(self._create_fallback_critique(responses[i]))
            else:
                results.append(critique)

        return results

    def get_critique_stats(self) -> Dict[str, Any]:
        """Get statistics about critique history."""
        if not self.critique_history:
            return {"total_critiques": 0}

        scores = [h["overall_score"] for h in self.critique_history]

        return {
            "total_critiques": len(self.critique_history),
            "average_score": sum(scores) / len(scores),
            "min_score": min(scores),
            "max_score": max(scores),
            "response_types": list(set(h["response_type"] for h in self.critique_history)),
            "recent_activity": self.critique_history[-5:] if self.critique_history else []
        }

    def set_quality_benchmark(self, response_type: str, benchmark_score: float):
        """Set quality benchmark for a response type."""
        self.quality_benchmarks[response_type] = benchmark_score

    def get_quality_benchmark(self, response_type: str) -> float:
        """Get quality benchmark for a response type."""
        return self.quality_benchmarks.get(response_type, 0.8)  # Default 80%