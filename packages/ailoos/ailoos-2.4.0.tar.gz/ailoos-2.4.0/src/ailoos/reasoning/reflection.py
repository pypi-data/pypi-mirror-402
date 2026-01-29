"""
Reflection Engine - Advanced Reasoning Analysis and Learning
===========================================================

Uses EmpoorioLM to analyze reasoning processes, identify patterns, and learn from
past experiences. Implements reflective learning with continuous improvement capabilities.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
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
class ReasoningStep:
    """Represents a single step in a reasoning process."""
    step_id: str
    description: str
    reasoning_type: str  # analysis, synthesis, evaluation, planning, etc.
    confidence: float  # 0.0 to 1.0
    evidence: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    alternatives_considered: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ReasoningTrace:
    """Complete trace of a reasoning process."""
    trace_id: str
    problem_statement: str
    steps: List[ReasoningStep] = field(default_factory=list)
    final_outcome: str = ""
    success_rating: float = 0.0  # 0.0 to 1.0
    lessons_learned: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReflectionInsight:
    """Insight derived from analyzing reasoning patterns."""
    insight_type: str  # pattern, weakness, strength, opportunity
    description: str
    confidence: float
    affected_reasoning_types: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    discovered_at: datetime = field(default_factory=datetime.now)


class ReflectionEngine:
    """
    Advanced reflection engine using EmpoorioLM for reasoning analysis and learning.

    Features:
    - Reasoning process tracing and analysis
    - Pattern recognition in reasoning approaches
    - Continuous learning from past experiences
    - Insight generation and recommendation system
    - Performance analytics and improvement tracking
    """

    def __init__(self, inference_api: Optional[EmpoorioLMInferenceAPI] = None):
        """
        Initialize the Reflection Engine.

        Args:
            inference_api: Pre-configured EmpoorioLM inference API instance
        """
        self.inference_api = inference_api
        self.reasoning_traces: List[ReasoningTrace] = []
        self.insights: List[ReflectionInsight] = []
        self.reasoning_patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.performance_metrics: Dict[str, Any] = {}
        self.learning_history: List[Dict[str, Any]] = []

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
                logger.info(f"🔧 ReflectionEngine: Forzando contexto largo: {original_max_pos} → 4096 tokens")

                # Recreate position embeddings if they exist
                if hasattr(self.inference_api.model, 'embed_positions') and self.inference_api.model.embed_positions is not None:
                    try:
                        import torch.nn as nn
                        old_embed = self.inference_api.model.embed_positions
                        new_embed = nn.Embedding(4096, old_embed.embedding_dim)
                        with torch.no_grad():
                            new_embed.weight[:original_max_pos] = old_embed.weight[:original_max_pos]
                        self.inference_api.model.embed_positions = new_embed
                        logger.info("✅ ReflectionEngine: Embeddings de posición recreados")
                    except Exception as e:
                        logger.warning(f"⚠️ ReflectionEngine: No se pudieron recrear embeddings: {e}")

            return success
        return True

    async def analyze_reasoning_trace(
        self,
        trace: ReasoningTrace,
        analysis_depth: str = "comprehensive"  # basic, detailed, comprehensive
    ) -> Dict[str, Any]:
        """
        Analyze a reasoning trace to extract insights and lessons.

        Args:
            trace: The reasoning trace to analyze
            analysis_depth: Level of analysis detail

        Returns:
            Comprehensive analysis of the reasoning process
        """
        if not await self.initialize():
            raise RuntimeError("Failed to initialize EmpoorioLM inference API")

        # Create analysis prompt
        prompt = self._create_analysis_prompt(trace, analysis_depth)

        # Generate analysis using EmpoorioLM
        request = InferenceRequest(
            prompt=prompt,
            max_tokens=2048,
            temperature=0.1,  # Low temperature for analytical consistency
            structured_output=True,
            schema=self._get_analysis_schema()
        )

        try:
            analysis_response = await self.inference_api.generate(request)

            # Parse structured analysis
            analysis_data = self._parse_analysis_response(analysis_response.text)

            # Extract and store insights
            new_insights = self._extract_insights_from_analysis(analysis_data, trace)
            self.insights.extend(new_insights)

            # Update reasoning patterns
            self._update_reasoning_patterns(trace, analysis_data)

            # Store analysis in learning history
            self.learning_history.append({
                "trace_id": trace.trace_id,
                "analysis_type": "reasoning_trace",
                "insights_discovered": len(new_insights),
                "analysis_depth": analysis_depth,
                "created_at": datetime.now().isoformat()
            })

            logger.info(f"✅ Analyzed reasoning trace: {len(new_insights)} insights discovered")
            return analysis_data

        except Exception as e:
            logger.error(f"❌ Error analyzing reasoning trace: {e}")
            return self._create_fallback_analysis(trace)

    def _create_analysis_prompt(self, trace: ReasoningTrace, depth: str) -> str:
        """Create a structured prompt for reasoning trace analysis."""
        depth_instructions = {
            "basic": "Proporciona un análisis de alto nivel identificando fortalezas y debilidades principales.",
            "detailed": "Analiza cada paso del razonamiento, evaluando lógica, evidencia y alternativas consideradas.",
            "comprehensive": "Realiza un análisis exhaustivo incluyendo patrones, sesgos potenciales, y oportunidades de mejora específicas."
        }

        # Format reasoning steps
        steps_text = "\n".join([
            f"Paso {i+1} ({step.reasoning_type}): {step.description}"
            f"\n  Confianza: {step.confidence:.2f}"
            f"\n  Evidencia: {', '.join(step.evidence) if step.evidence else 'Ninguna'}"
            f"\n  Suposiciones: {', '.join(step.assumptions) if step.assumptions else 'Ninguna'}"
            f"\n  Alternativas: {', '.join(step.alternatives_considered) if step.alternatives_considered else 'Ninguna'}"
            for i, step in enumerate(trace.steps)
        ])

        return f"""
Eres un analista experto en procesos de razonamiento. Tu tarea es analizar el siguiente proceso de razonamiento y extraer insights valiosos.

PROCESO DE RAZONAMIENTO A ANALIZAR:
Problema: {trace.problem_statement}

Pasos del razonamiento:
{steps_text}

Resultado final: {trace.final_outcome}
Calificación de éxito: {trace.success_rating:.2f}/1.0

INSTRUCCIONES DE ANÁLISIS:
{depth_instructions.get(depth, depth_instructions["comprehensive"])}

Evalúa aspectos como:
- Lógica y coherencia del razonamiento
- Uso efectivo de evidencia y suposiciones
- Consideración de alternativas
- Fortalezas y debilidades del enfoque
- Patrones identificables
- Oportunidades de mejora
- Lecciones aprendidas

FORMATO DE RESPUESTA:
Proporciona tu análisis en formato JSON con:
- overall_assessment: evaluación general del proceso
- strengths: array de fortalezas identificadas
- weaknesses: array de debilidades identificadas
- patterns_identified: array de patrones encontrados
- lessons_learned: array de lecciones aprendidas
- improvement_suggestions: array de sugerencias específicas
- confidence_in_analysis: confianza en el análisis (0.0-1.0)

ANÁLISIS:
"""

    def _get_analysis_schema(self) -> Dict[str, Any]:
        """Get JSON schema for structured analysis output."""
        return {
            "type": "object",
            "properties": {
                "overall_assessment": {"type": "string"},
                "strengths": {"type": "array", "items": {"type": "string"}},
                "weaknesses": {"type": "array", "items": {"type": "string"}},
                "patterns_identified": {"type": "array", "items": {"type": "string"}},
                "lessons_learned": {"type": "array", "items": {"type": "string"}},
                "improvement_suggestions": {"type": "array", "items": {"type": "string"}},
                "confidence_in_analysis": {"type": "number", "minimum": 0.0, "maximum": 1.0}
            },
            "required": ["overall_assessment", "strengths", "weaknesses", "patterns_identified", "lessons_learned", "improvement_suggestions"]
        }

    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the structured analysis response from EmpoorioLM."""
        try:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON analysis response, creating fallback structure")
            return self._extract_analysis_from_text(response_text)

    def _extract_analysis_from_text(self, text: str) -> Dict[str, Any]:
        """Extract analysis elements from plain text as fallback."""
        return {
            "overall_assessment": "Análisis básico generado automáticamente",
            "strengths": ["Proceso estructurado identificado"],
            "weaknesses": ["Análisis detallado no disponible"],
            "patterns_identified": ["Patrón básico de razonamiento secuencial"],
            "lessons_learned": ["Documentar procesos de razonamiento mejora la reflexión"],
            "improvement_suggestions": ["Implementar análisis más detallado"],
            "confidence_in_analysis": 0.5
        }

    def _extract_insights_from_analysis(self, analysis_data: Dict[str, Any], trace: ReasoningTrace) -> List[ReflectionInsight]:
        """Extract actionable insights from analysis data."""
        insights = []

        # Extract insights from weaknesses
        for weakness in analysis_data.get("weaknesses", []):
            if "confianza" in weakness.lower() or "confidence" in weakness.lower():
                insights.append(ReflectionInsight(
                    insight_type="weakness",
                    description=f"Mejora necesaria en evaluación de confianza: {weakness}",
                    confidence=0.8,
                    affected_reasoning_types=["evaluation", "analysis"],
                    recommended_actions=["Implementar métricas de confianza más rigurosas"],
                    examples=[f"Traza {trace.trace_id}: {weakness}"]
                ))

        # Extract insights from patterns
        for pattern in analysis_data.get("patterns_identified", []):
            insights.append(ReflectionInsight(
                insight_type="pattern",
                description=f"Patrón identificado: {pattern}",
                confidence=0.7,
                affected_reasoning_types=["general"],
                recommended_actions=["Documentar y reutilizar este patrón"],
                examples=[f"Traza {trace.trace_id}: {pattern}"]
            ))

        # Extract insights from lessons learned
        for lesson in analysis_data.get("lessons_learned", []):
            insights.append(ReflectionInsight(
                insight_type="opportunity",
                description=f"Lección aprendida: {lesson}",
                confidence=0.9,
                affected_reasoning_types=["general"],
                recommended_actions=["Aplicar esta lección en futuros razonamientos"],
                examples=[f"Traza {trace.trace_id}: {lesson}"]
            ))

        return insights

    def _update_reasoning_patterns(self, trace: ReasoningTrace, analysis_data: Dict[str, Any]):
        """Update reasoning patterns database."""
        for step in trace.steps:
            pattern_entry = {
                "step_type": step.reasoning_type,
                "confidence": step.confidence,
                "evidence_count": len(step.evidence),
                "alternatives_count": len(step.alternatives_considered),
                "success_rating": trace.success_rating,
                "trace_id": trace.trace_id,
                "timestamp": datetime.now().isoformat()
            }
            self.reasoning_patterns[step.reasoning_type].append(pattern_entry)

    def _create_fallback_analysis(self, trace: ReasoningTrace) -> Dict[str, Any]:
        """Create a basic fallback analysis when AI analysis fails."""
        return {
            "overall_assessment": f"Análisis básico del proceso de razonamiento para: {trace.problem_statement[:50]}...",
            "strengths": ["Proceso estructurado identificado", "Pasos lógicos definidos"],
            "weaknesses": ["Análisis detallado no disponible", "Métricas de confianza limitadas"],
            "patterns_identified": ["Razonamiento secuencial estándar"],
            "lessons_learned": ["Documentar procesos mejora la reflexión futura"],
            "improvement_suggestions": [
                "Implementar métricas más detalladas de confianza",
                "Considerar más alternativas en cada paso",
                "Añadir validación de evidencia"
            ],
            "confidence_in_analysis": 0.6
        }

    async def generate_reasoning_improvements(
        self,
        reasoning_type: str,
        current_performance: float,
        historical_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate specific improvements for a reasoning type based on historical analysis.

        Args:
            reasoning_type: Type of reasoning to improve
            current_performance: Current performance metric (0.0-1.0)
            historical_data: Optional additional historical data

        Returns:
            Improvement recommendations and strategies
        """
        if not await self.initialize():
            return {"error": "Failed to initialize inference API"}

        # Gather relevant historical data
        pattern_data = self.reasoning_patterns.get(reasoning_type, [])
        relevant_insights = [
            insight for insight in self.insights
            if reasoning_type in insight.affected_reasoning_types
        ]

        # Create improvement prompt
        prompt = self._create_improvement_prompt(reasoning_type, current_performance, pattern_data, relevant_insights)

        # Generate improvements using EmpoorioLM
        request = InferenceRequest(
            prompt=prompt,
            max_tokens=1536,
            temperature=0.3,
            structured_output=True,
            schema=self._get_improvement_schema()
        )

        try:
            improvement_response = await self.inference_api.generate(request)
            improvements = self._parse_improvement_response(improvement_response.text)

            # Store improvement generation in learning history
            self.learning_history.append({
                "reasoning_type": reasoning_type,
                "improvement_type": "reasoning_improvements",
                "current_performance": current_performance,
                "recommendations_generated": len(improvements.get("recommendations", [])),
                "created_at": datetime.now().isoformat()
            })

            logger.info(f"✅ Generated {len(improvements.get('recommendations', []))} improvements for {reasoning_type}")
            return improvements

        except Exception as e:
            logger.error(f"❌ Error generating reasoning improvements: {e}")
            return self._create_fallback_improvements(reasoning_type, current_performance)

    def _create_improvement_prompt(
        self,
        reasoning_type: str,
        performance: float,
        pattern_data: List[Dict[str, Any]],
        insights: List[ReflectionInsight]
    ) -> str:
        """Create a prompt for generating reasoning improvements."""
        # Format pattern data
        pattern_summary = f"Analizados {len(pattern_data)} casos de {reasoning_type}"
        if pattern_data:
            avg_confidence = sum(p["confidence"] for p in pattern_data) / len(pattern_data)
            avg_success = sum(p["success_rating"] for p in pattern_data) / len(pattern_data)
            pattern_summary += f"\nConfianza promedio: {avg_confidence:.2f}"
            pattern_summary += f"\nÉxito promedio: {avg_success:.2f}"

        # Format insights
        insights_text = "\n".join([
            f"- {insight.insight_type.upper()}: {insight.description}"
            for insight in insights[:5]  # Limit to top 5 insights
        ])

        return f"""
Eres un experto en mejora de procesos de razonamiento. Tu tarea es analizar el rendimiento actual del tipo de razonamiento "{reasoning_type}" y generar recomendaciones específicas de mejora.

RENDIMIENTO ACTUAL:
- Tipo de razonamiento: {reasoning_type}
- Puntuación de rendimiento: {performance:.2f}/1.0

DATOS HISTÓRICOS:
{pattern_summary}

INSIGHTS IDENTIFICADOS:
{insights_text}

INSTRUCCIONES:
Analiza los datos proporcionados y genera recomendaciones específicas para mejorar el razonamiento de tipo "{reasoning_type}". Considera:

1. Fortalezas actuales a mantener
2. Debilidades específicas a abordar
3. Estrategias concretas de mejora
4. Métricas para medir el progreso
5. Recursos o técnicas adicionales recomendadas

FORMATO DE RESPUESTA:
Proporciona tus recomendaciones en formato JSON con:
- current_assessment: evaluación del estado actual
- key_strengths: array de fortalezas a mantener
- priority_improvements: array de mejoras prioritarias
- specific_strategies: array de estrategias concretas
- success_metrics: array de métricas para medir mejora
- implementation_priority: orden de implementación sugerido (high, medium, low)

RECOMENDACIONES:
"""

    def _get_improvement_schema(self) -> Dict[str, Any]:
        """Get JSON schema for structured improvement output."""
        return {
            "type": "object",
            "properties": {
                "current_assessment": {"type": "string"},
                "key_strengths": {"type": "array", "items": {"type": "string"}},
                "priority_improvements": {"type": "array", "items": {"type": "string"}},
                "specific_strategies": {"type": "array", "items": {"type": "string"}},
                "success_metrics": {"type": "array", "items": {"type": "string"}},
                "implementation_priority": {"type": "string", "enum": ["high", "medium", "low"]}
            },
            "required": ["current_assessment", "key_strengths", "priority_improvements", "specific_strategies"]
        }

    def _parse_improvement_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the structured improvement response."""
        try:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON improvement response, creating fallback")
            return self._extract_improvements_from_text(response_text)

    def _extract_improvements_from_text(self, text: str) -> Dict[str, Any]:
        """Extract improvement recommendations from plain text."""
        lines = text.split('\n')
        recommendations = []

        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or re.match(r'\d+\.', line)):
                recommendations.append(line.lstrip('-•1234567890. '))

        return {
            "current_assessment": "Evaluación básica del rendimiento actual",
            "key_strengths": ["Estructura básica identificada"],
            "priority_improvements": recommendations[:3] if recommendations else ["Mejorar documentación de procesos"],
            "specific_strategies": recommendations[3:6] if len(recommendations) > 3 else ["Implementar métricas de seguimiento"],
            "success_metrics": ["Mejorar puntuación de rendimiento en 0.1 puntos"],
            "implementation_priority": "medium"
        }

    def _create_fallback_improvements(self, reasoning_type: str, performance: float) -> Dict[str, Any]:
        """Create fallback improvements when AI generation fails."""
        return {
            "current_assessment": f"Rendimiento actual de {reasoning_type}: {performance:.2f}/1.0 - requiere mejoras",
            "key_strengths": ["Proceso básico establecido"],
            "priority_improvements": [
                "Aumentar la evaluación de evidencia",
                "Mejorar consideración de alternativas",
                "Implementar métricas de confianza más rigurosas"
            ],
            "specific_strategies": [
                "Documentar cada paso del razonamiento",
                "Implementar revisiones por pares",
                "Añadir validación de suposiciones"
            ],
            "success_metrics": [
                "Aumento de 15% en puntuación de rendimiento",
                "Reducción de 20% en errores de razonamiento",
                "Mejora en evaluación de confianza"
            ],
            "implementation_priority": "high"
        }

    def add_reasoning_trace(self, trace: ReasoningTrace):
        """Add a reasoning trace to the analysis database."""
        self.reasoning_traces.append(trace)

        # Update performance metrics
        self._update_performance_metrics()

    def _update_performance_metrics(self):
        """Update overall performance metrics based on traces."""
        if not self.reasoning_traces:
            return

        total_traces = len(self.reasoning_traces)
        avg_success = sum(trace.success_rating for trace in self.reasoning_traces) / total_traces
        avg_steps = sum(len(trace.steps) for trace in self.reasoning_traces) / total_traces

        reasoning_type_counts = defaultdict(int)
        for trace in self.reasoning_traces:
            for step in trace.steps:
                reasoning_type_counts[step.reasoning_type] += 1

        self.performance_metrics = {
            "total_traces": total_traces,
            "average_success_rate": avg_success,
            "average_steps_per_trace": avg_steps,
            "reasoning_type_distribution": dict(reasoning_type_counts),
            "insights_discovered": len(self.insights),
            "last_updated": datetime.now().isoformat()
        }

    async def generate_comprehensive_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive report on reasoning performance and insights.

        Returns:
            Complete analysis report
        """
        if not await self.initialize():
            return {"error": "Failed to initialize inference API"}

        # Gather all data
        report_data = {
            "performance_metrics": self.performance_metrics,
            "insights_summary": self._summarize_insights(),
            "reasoning_patterns": dict(self.reasoning_patterns),
            "learning_history": self.learning_history[-10:],  # Last 10 entries
            "recommendations": await self._generate_global_recommendations()
        }

        return report_data

    def _summarize_insights(self) -> Dict[str, Any]:
        """Summarize insights by type and impact."""
        insight_counts = defaultdict(int)
        high_confidence_insights = []

        for insight in self.insights:
            insight_counts[insight.insight_type] += 1
            if insight.confidence > 0.8:
                high_confidence_insights.append({
                    "type": insight.insight_type,
                    "description": insight.description,
                    "confidence": insight.confidence
                })

        return {
            "total_insights": len(self.insights),
            "insights_by_type": dict(insight_counts),
            "high_confidence_insights": high_confidence_insights[:5]  # Top 5
        }

    async def _generate_global_recommendations(self) -> List[str]:
        """Generate global recommendations based on all analysis."""
        if not self.insights:
            return ["Continuar recopilando datos de razonamiento para análisis"]

        # Create prompt for global recommendations
        insights_text = "\n".join([
            f"- {insight.insight_type}: {insight.description} (confianza: {insight.confidence:.2f})"
            for insight in self.insights[-10:]  # Last 10 insights
        ])

        prompt = f"""
Basándote en los siguientes insights de análisis de razonamiento, genera 5 recomendaciones globales para mejorar el sistema de razonamiento:

INSIGHTS RECIENTES:
{insights_text}

MÉTRICAS DE RENDIMIENTO:
{json.dumps(self.performance_metrics, indent=2)}

Genera recomendaciones prácticas y accionables que puedan implementarse para mejorar el rendimiento general del razonamiento.
"""

        request = InferenceRequest(
            prompt=prompt,
            max_tokens=512,
            temperature=0.2,
            structured_output=False
        )

        try:
            response = await self.inference_api.generate(request)
            recommendations = response.text.strip().split('\n')
            return [rec.strip('- •1234567890.') for rec in recommendations if rec.strip()]
        except Exception:
            return [
                "Implementar seguimiento más detallado de procesos de razonamiento",
                "Desarrollar métricas de calidad más específicas",
                "Aumentar la frecuencia de análisis y reflexión",
                "Mejorar la documentación de lecciones aprendidas",
                "Implementar validación cruzada de razonamientos"
            ]

    def get_reflection_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the reflection engine."""
        return {
            "traces_analyzed": len(self.reasoning_traces),
            "insights_discovered": len(self.insights),
            "reasoning_types_covered": list(self.reasoning_patterns.keys()),
            "learning_sessions": len(self.learning_history),
            "performance_metrics": self.performance_metrics,
            "insights_by_type": self._summarize_insights()
        }