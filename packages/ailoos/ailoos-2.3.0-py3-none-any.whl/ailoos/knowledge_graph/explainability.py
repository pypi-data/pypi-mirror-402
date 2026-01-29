"""
Sistema de Explainability para explicación de inferencias y decisiones basado en el diseño arquitectónico.
Proporciona explicaciones detalladas de inferencias, planes de ejecución de consultas y decisiones del sistema.
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from ..core.logging import get_logger
from .inference import get_inference_engine, InferenceEngine, InferenceResult
from .query_engine import get_query_engine, QueryEngine, QueryPlan
from ..auditing.audit_manager import get_audit_manager, AuditEventType
from ..auditing.metrics_collector import get_metrics_collector

logger = get_logger(__name__)


class DetailLevel(Enum):
    """Niveles de detalle para explicaciones."""
    BASIC = "basic"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


class OutputFormat(Enum):
    """Formatos de salida para explicaciones."""
    TEXT = "text"
    JSON = "json"
    VISUAL = "visual"


@dataclass
class ExplanationResult:
    """Resultado de una explicación."""
    explanation_id: str
    explanation_type: str
    content: Union[str, Dict[str, Any]]
    detail_level: DetailLevel
    output_format: OutputFormat
    confidence_score: float
    generation_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            "explanation_id": self.explanation_id,
            "explanation_type": self.explanation_type,
            "content": self.content,
            "detail_level": self.detail_level.value,
            "output_format": self.output_format.value,
            "confidence_score": self.confidence_score,
            "generation_time_ms": self.generation_time_ms,
            "metadata": self.metadata
        }


class ExplainabilityEngine:
    """
    Motor de explainability para explicar inferencias, consultas y decisiones del sistema.
    Proporciona explicaciones en múltiples formatos y niveles de detalle.
    """

    def __init__(self, inference_engine: Optional[InferenceEngine] = None,
                 query_engine: Optional[QueryEngine] = None):
        self.inference_engine = inference_engine or get_inference_engine()
        self.query_engine = query_engine or get_query_engine()
        self.audit_manager = get_audit_manager()
        self.metrics_collector = get_metrics_collector()

        # Configuración
        self.max_explanation_length = 10000
        self.confidence_threshold = 0.7

    async def explain_inference(
        self,
        inference_result: InferenceResult,
        detail_level: DetailLevel = DetailLevel.DETAILED,
        output_format: OutputFormat = OutputFormat.TEXT,
        user_id: Optional[str] = None
    ) -> ExplanationResult:
        """
        Explicar una inferencia con trazas detalladas.

        Args:
            inference_result: Resultado de inferencia a explicar
            detail_level: Nivel de detalle de la explicación
            output_format: Formato de salida
            user_id: ID del usuario que solicita la explicación

        Returns:
            ExplanationResult con la explicación
        """
        start_time = time.time()
        explanation_id = f"inf_exp_{int(time.time() * 1000)}"

        try:
            # Generar explicación según formato
            if output_format == OutputFormat.TEXT:
                content = self._explain_inference_text(inference_result, detail_level)
            elif output_format == OutputFormat.JSON:
                content = self._explain_inference_json(inference_result, detail_level)
            elif output_format == OutputFormat.VISUAL:
                content = self._explain_inference_visual(inference_result, detail_level)
            else:
                raise ValueError(f"Formato no soportado: {output_format}")

            generation_time = (time.time() - start_time) * 1000

            # Calcular confianza basada en el resultado de inferencia
            confidence_score = self._calculate_inference_confidence(inference_result)

            result = ExplanationResult(
                explanation_id=explanation_id,
                explanation_type="inference",
                content=content,
                detail_level=detail_level,
                output_format=output_format,
                confidence_score=confidence_score,
                generation_time_ms=generation_time,
                metadata={
                    "inference_rules_applied": len(inference_result.rules_applied),
                    "triples_inferred": len(inference_result.inferred_triples),
                    "inference_execution_time_ms": inference_result.execution_time_ms
                }
            )

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph",
                action="explain_inference",
                user_id=user_id,
                details={
                    "explanation_id": explanation_id,
                    "detail_level": detail_level.value,
                    "output_format": output_format.value,
                    "confidence_score": confidence_score
                },
                success=True,
                processing_time_ms=generation_time
            )

            # Métricas
            self.metrics_collector.record_request("explainability_engine.explain_inference")
            self.metrics_collector.record_response_time(generation_time)

            logger.info(f"Inference explanation generated: {explanation_id}, confidence: {confidence_score:.2f}")
            return result

        except Exception as e:
            generation_time = (time.time() - start_time) * 1000
            error_msg = str(e)

            # Logging de error
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph",
                action="explain_inference",
                user_id=user_id,
                details={
                    "explanation_id": explanation_id,
                    "error": error_msg
                },
                success=False,
                processing_time_ms=generation_time
            )

            self.metrics_collector.record_error("explainability_engine.explain_inference", "explanation_error")
            logger.error(f"Inference explanation failed: {error_msg}")

            return ExplanationResult(
                explanation_id=explanation_id,
                explanation_type="inference",
                content=f"Error generando explicación: {error_msg}",
                detail_level=detail_level,
                output_format=output_format,
                confidence_score=0.0,
                generation_time_ms=generation_time
            )

    async def explain_query(
        self,
        query_plan: QueryPlan,
        query: str,
        detail_level: DetailLevel = DetailLevel.DETAILED,
        output_format: OutputFormat = OutputFormat.TEXT,
        user_id: Optional[str] = None
    ) -> ExplanationResult:
        """
        Explicar el plan de ejecución de una consulta.

        Args:
            query_plan: Plan de ejecución a explicar
            query: La consulta original
            detail_level: Nivel de detalle
            output_format: Formato de salida
            user_id: ID del usuario

        Returns:
            ExplanationResult con la explicación
        """
        start_time = time.time()
        explanation_id = f"query_exp_{int(time.time() * 1000)}"

        try:
            # Generar explicación según formato
            if output_format == OutputFormat.TEXT:
                content = self._explain_query_text(query_plan, query, detail_level)
            elif output_format == OutputFormat.JSON:
                content = self._explain_query_json(query_plan, query, detail_level)
            elif output_format == OutputFormat.VISUAL:
                content = self._explain_query_visual(query_plan, query, detail_level)
            else:
                raise ValueError(f"Formato no soportado: {output_format}")

            generation_time = (time.time() - start_time) * 1000

            # Calcular confianza basada en el plan
            confidence_score = self._calculate_query_confidence(query_plan)

            result = ExplanationResult(
                explanation_id=explanation_id,
                explanation_type="query",
                content=content,
                detail_level=detail_level,
                output_format=output_format,
                confidence_score=confidence_score,
                generation_time_ms=generation_time,
                metadata={
                    "query_steps": len(query_plan.steps),
                    "estimated_cost": query_plan.estimated_cost,
                    "estimated_rows": query_plan.estimated_rows,
                    "backend_used": query_plan.backend_used
                }
            )

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph",
                action="explain_query",
                user_id=user_id,
                details={
                    "explanation_id": explanation_id,
                    "detail_level": detail_level.value,
                    "output_format": output_format.value,
                    "confidence_score": confidence_score
                },
                success=True,
                processing_time_ms=generation_time
            )

            # Métricas
            self.metrics_collector.record_request("explainability_engine.explain_query")
            self.metrics_collector.record_response_time(generation_time)

            logger.info(f"Query explanation generated: {explanation_id}, confidence: {confidence_score:.2f}")
            return result

        except Exception as e:
            generation_time = (time.time() - start_time) * 1000
            error_msg = str(e)

            # Logging de error
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph",
                action="explain_query",
                user_id=user_id,
                details={
                    "explanation_id": explanation_id,
                    "error": error_msg
                },
                success=False,
                processing_time_ms=generation_time
            )

            self.metrics_collector.record_error("explainability_engine.explain_query", "explanation_error")
            logger.error(f"Query explanation failed: {error_msg}")

            return ExplanationResult(
                explanation_id=explanation_id,
                explanation_type="query",
                content=f"Error generando explicación: {error_msg}",
                detail_level=detail_level,
                output_format=output_format,
                confidence_score=0.0,
                generation_time_ms=generation_time
            )

    async def explain_decision(
        self,
        decision_context: Dict[str, Any],
        decision_type: str,
        decision_made: Any,
        detail_level: DetailLevel = DetailLevel.DETAILED,
        output_format: OutputFormat = OutputFormat.TEXT,
        user_id: Optional[str] = None
    ) -> ExplanationResult:
        """
        Explicar una decisión tomada por el sistema.

        Args:
            decision_context: Contexto en el que se tomó la decisión
            decision_type: Tipo de decisión (ej: 'inference_rule_selection', 'query_optimization')
            decision_made: La decisión tomada
            detail_level: Nivel de detalle
            output_format: Formato de salida
            user_id: ID del usuario

        Returns:
            ExplanationResult con la explicación
        """
        start_time = time.time()
        explanation_id = f"decision_exp_{int(time.time() * 1000)}"

        try:
            # Generar explicación según formato
            if output_format == OutputFormat.TEXT:
                content = self._explain_decision_text(decision_context, decision_type, decision_made, detail_level)
            elif output_format == OutputFormat.JSON:
                content = self._explain_decision_json(decision_context, decision_type, decision_made, detail_level)
            elif output_format == OutputFormat.VISUAL:
                content = self._explain_decision_visual(decision_context, decision_type, decision_made, detail_level)
            else:
                raise ValueError(f"Formato no soportado: {output_format}")

            generation_time = (time.time() - start_time) * 1000

            # Calcular confianza basada en el contexto
            confidence_score = self._calculate_decision_confidence(decision_context, decision_type)

            result = ExplanationResult(
                explanation_id=explanation_id,
                explanation_type="decision",
                content=content,
                detail_level=detail_level,
                output_format=output_format,
                confidence_score=confidence_score,
                generation_time_ms=generation_time,
                metadata={
                    "decision_type": decision_type,
                    "decision_made": str(decision_made),
                    "context_keys": list(decision_context.keys())
                }
            )

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph",
                action="explain_decision",
                user_id=user_id,
                details={
                    "explanation_id": explanation_id,
                    "decision_type": decision_type,
                    "detail_level": detail_level.value,
                    "output_format": output_format.value,
                    "confidence_score": confidence_score
                },
                success=True,
                processing_time_ms=generation_time
            )

            # Métricas
            self.metrics_collector.record_request("explainability_engine.explain_decision")
            self.metrics_collector.record_response_time(generation_time)

            logger.info(f"Decision explanation generated: {explanation_id}, confidence: {confidence_score:.2f}")
            return result

        except Exception as e:
            generation_time = (time.time() - start_time) * 1000
            error_msg = str(e)

            # Logging de error
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph",
                action="explain_decision",
                user_id=user_id,
                details={
                    "explanation_id": explanation_id,
                    "error": error_msg
                },
                success=False,
                processing_time_ms=generation_time
            )

            self.metrics_collector.record_error("explainability_engine.explain_decision", "explanation_error")
            logger.error(f"Decision explanation failed: {error_msg}")

            return ExplanationResult(
                explanation_id=explanation_id,
                explanation_type="decision",
                content=f"Error generando explicación: {error_msg}",
                detail_level=detail_level,
                output_format=output_format,
                confidence_score=0.0,
                generation_time_ms=generation_time
            )

    def _explain_inference_text(self, result: InferenceResult, detail_level: DetailLevel) -> str:
        """Generar explicación de inferencia en formato texto."""
        lines = []

        lines.append("EXPLICACIÓN DE INFERENCIA")
        lines.append("=" * 50)
        lines.append("")

        # Información básica
        lines.append(f"Triples inferidos: {len(result.inferred_triples)}")
        lines.append(f"Reglas aplicadas: {len(result.rules_applied)}")
        lines.append(".2f")
        lines.append(".2f")
        lines.append("")

        if detail_level == DetailLevel.BASIC:
            lines.append("Reglas aplicadas:")
            for rule in result.rules_applied:
                lines.append(f"  - {rule}")
            return "\n".join(lines)

        # Detalle de reglas
        lines.append("REGLAS APLICADAS:")
        lines.append("-" * 20)
        for rule in result.rules_applied:
            lines.append(f"  • {rule}")
        lines.append("")

        if detail_level == DetailLevel.DETAILED:
            lines.append("TRAZA DE INFERENCIAS:")
            lines.append("-" * 20)
            for explanation in result.explanation[:20]:  # Limitar
                lines.append(f"  {explanation}")
            if len(result.explanation) > 20:
                lines.append(f"  ... y {len(result.explanation) - 20} inferencias más")
            return "\n".join(lines)

        # Nivel comprehensivo
        lines.append("TRAZA COMPLETA DE INFERENCIAS:")
        lines.append("-" * 30)
        for i, explanation in enumerate(result.explanation, 1):
            lines.append(f"{i:3d}. {explanation}")
        lines.append("")

        lines.append("TRIPLES INFERIDOS:")
        lines.append("-" * 20)
        for triple in result.inferred_triples[:10]:  # Limitar
            lines.append(f"  {triple.subject} -> {triple.predicate} -> {triple.object}")
        if len(result.inferred_triples) > 10:
            lines.append(f"  ... y {len(result.inferred_triples) - 10} triples más")

        return "\n".join(lines)

    def _explain_inference_json(self, result: InferenceResult, detail_level: DetailLevel) -> Dict[str, Any]:
        """Generar explicación de inferencia en formato JSON."""
        data = {
            "type": "inference_explanation",
            "summary": {
                "triples_inferred": len(result.inferred_triples),
                "rules_applied": len(result.rules_applied),
                "execution_time_ms": result.execution_time_ms,
                "confidence_score": result.confidence_score
            }
        }

        if detail_level.value in ["detailed", "comprehensive"]:
            data["rules_applied"] = result.rules_applied
            data["inference_trace"] = result.explanation

        if detail_level == DetailLevel.COMPREHENSIVE:
            data["inferred_triples"] = [t.to_dict() for t in result.inferred_triples]

        return data

    def _explain_inference_visual(self, result: InferenceResult, detail_level: DetailLevel) -> str:
        """Generar explicación de inferencia en formato visual (texto-based)."""
        lines = []

        # Diagrama simple de inferencia
        lines.append("INFERENCE FLOW DIAGRAM")
        lines.append("┌─────────────────┐")
        lines.append("│   Knowledge     │")
        lines.append("│     Graph       │")
        lines.append("└─────────┬───────┘")
        lines.append("          │")
        lines.append("          ▼")
        lines.append("┌─────────────────┐")
        lines.append("│  Inference      │")
        lines.append("│   Engine        │")
        lines.append("└─────────┬───────┘")
        lines.append("          │")
        lines.append(f"          ▼  ({len(result.rules_applied)} rules)")
        lines.append("┌─────────────────┐")
        lines.append("│ Inferred Triples│")
        lines.append(f"│   ({len(result.inferred_triples)})     │")
        lines.append("└─────────────────┘")
        lines.append("")
        lines.append(f"Confidence: {'█' * int(result.confidence_score * 10)}{'░' * (10 - int(result.confidence_score * 10))} {result.confidence_score:.1%}")

        if detail_level.value in ["detailed", "comprehensive"]:
            lines.append("")
            lines.append("RULES APPLIED:")
            for rule in result.rules_applied:
                lines.append(f"  ▶ {rule}")

        return "\n".join(lines)

    def _explain_query_text(self, plan: QueryPlan, query: str, detail_level: DetailLevel) -> str:
        """Generar explicación de consulta en formato texto."""
        lines = []

        lines.append("EXPLICACIÓN DEL PLAN DE EJECUCIÓN DE CONSULTA")
        lines.append("=" * 60)
        lines.append("")

        # Consulta original
        lines.append("CONSULTA ORIGINAL:")
        lines.append(f"  {query}")
        lines.append("")

        # Información del plan
        lines.append("INFORMACIÓN DEL PLAN:")
        lines.append(f"  Backend utilizado: {plan.backend_used}")
        lines.append(",.2f")
        lines.append(f"  Filas estimadas: {plan.estimated_rows}")
        lines.append("")

        if detail_level == DetailLevel.BASIC:
            lines.append("Pasos principales:")
            for step in plan.steps[:3]:
                lines.append(f"  - {step}")
            return "\n".join(lines)

        # Pasos detallados
        lines.append("PASOS DE EJECUCIÓN:")
        lines.append("-" * 20)
        for i, step in enumerate(plan.steps, 1):
            lines.append(f"{i}. {step}")
        lines.append("")

        if detail_level.value in ["detailed", "comprehensive"]:
            lines.append("OPTIMIZACIONES APLICADAS:")
            lines.append("-" * 25)
            if plan.optimizations_applied:
                for opt in plan.optimizations_applied:
                    lines.append(f"  ✓ {opt}")
            else:
                lines.append("  Ninguna optimización aplicada")

        return "\n".join(lines)

    def _explain_query_json(self, plan: QueryPlan, query: str, detail_level: DetailLevel) -> Dict[str, Any]:
        """Generar explicación de consulta en formato JSON."""
        return {
            "type": "query_explanation",
            "query": query,
            "plan": plan.to_dict(),
            "detail_level": detail_level.value
        }

    def _explain_query_visual(self, plan: QueryPlan, query: str, detail_level: DetailLevel) -> str:
        """Generar explicación de consulta en formato visual."""
        lines = []

        lines.append("QUERY EXECUTION PLAN")
        lines.append("┌─────────────────────────────────────┐")

        # Consulta simplificada
        query_short = query[:50] + "..." if len(query) > 50 else query
        lines.append(f"│ Query: {query_short:<28} │")
        lines.append("├─────────────────────────────────────┤")

        # Pasos del plan
        for i, step in enumerate(plan.steps):
            step_short = step[:35] + "..." if len(step) > 35 else step
            lines.append(f"│ {i+1}. {step_short:<32} │")

        lines.append("├─────────────────────────────────────┤")
        lines.append(f"│ Backend: {plan.backend_used:<26} │")
        lines.append(f"│ Cost: {plan.estimated_cost:<29.2f} │")
        lines.append(f"│ Rows: {plan.estimated_rows:<29} │")
        lines.append("└─────────────────────────────────────┘")

        return "\n".join(lines)

    def _explain_decision_text(self, context: Dict[str, Any], decision_type: str,
                              decision_made: Any, detail_level: DetailLevel) -> str:
        """Generar explicación de decisión en formato texto."""
        lines = []

        lines.append("EXPLICACIÓN DE DECISIÓN DEL SISTEMA")
        lines.append("=" * 50)
        lines.append("")

        lines.append(f"Tipo de decisión: {decision_type}")
        lines.append(f"Decisión tomada: {decision_made}")
        lines.append("")

        if detail_level == DetailLevel.BASIC:
            lines.append("Contexto relevante:")
            for key, value in list(context.items())[:5]:
                lines.append(f"  {key}: {str(value)[:50]}")
            return "\n".join(lines)

        lines.append("CONTEXTO DE LA DECISIÓN:")
        lines.append("-" * 25)
        for key, value in context.items():
            lines.append(f"  {key}: {value}")
        lines.append("")

        if detail_level == DetailLevel.COMPREHENSIVE:
            lines.append("ANÁLISIS DETALLADO:")
            lines.append("-" * 20)
            lines.append("Esta decisión se tomó basándose en el análisis del contexto")
            lines.append("proporcionado y las reglas del sistema aplicables.")

        return "\n".join(lines)

    def _explain_decision_json(self, context: Dict[str, Any], decision_type: str,
                              decision_made: Any, detail_level: DetailLevel) -> Dict[str, Any]:
        """Generar explicación de decisión en formato JSON."""
        return {
            "type": "decision_explanation",
            "decision_type": decision_type,
            "decision_made": decision_made,
            "context": context,
            "detail_level": detail_level.value
        }

    def _explain_decision_visual(self, context: Dict[str, Any], decision_type: str,
                                decision_made: Any, detail_level: DetailLevel) -> str:
        """Generar explicación de decisión en formato visual."""
        lines = []

        lines.append("DECISION TREE")
        lines.append("┌─────────────────┐")
        lines.append("│   System        │")
        lines.append("│  Context        │")
        lines.append("└─────────┬───────┘")
        lines.append("          │")
        lines.append("          ▼")
        lines.append("┌─────────────────┐")
        lines.append(f"│ Decision Type   │")
        lines.append(f"│   {decision_type[:13]}    │")
        lines.append("└─────────┬───────┘")
        lines.append("          │")
        lines.append("          ▼")
        lines.append("┌─────────────────┐")
        lines.append("│ Decision Made   │")
        lines.append(f"│   {str(decision_made)[:13]}    │")
        lines.append("└─────────────────┘")

        return "\n".join(lines)

    def _calculate_inference_confidence(self, result: InferenceResult) -> float:
        """Calcular confianza de una explicación de inferencia."""
        base_confidence = result.confidence_score

        # Ajustar basado en número de reglas aplicadas
        if len(result.rules_applied) > 5:
            base_confidence *= 0.9  # Penalizar muchas reglas
        elif len(result.rules_applied) == 0:
            base_confidence = 0.0  # Sin reglas, confianza cero

        # Ajustar basado en tiempo de ejecución
        if result.execution_time_ms > 5000:  # Más de 5 segundos
            base_confidence *= 0.8

        return max(0.0, min(1.0, base_confidence))

    def _calculate_query_confidence(self, plan: QueryPlan) -> float:
        """Calcular confianza de una explicación de consulta."""
        confidence = 0.8  # Base

        # Ajustar basado en costo estimado
        if plan.estimated_cost > 100:
            confidence *= 0.7
        elif plan.estimated_cost < 10:
            confidence *= 1.1

        # Ajustar basado en optimizaciones
        if plan.optimizations_applied:
            confidence *= 1.2

        return max(0.0, min(1.0, confidence))

    def _calculate_decision_confidence(self, context: Dict[str, Any], decision_type: str) -> float:
        """Calcular confianza de una explicación de decisión."""
        # Confianza basada en la completitud del contexto
        context_completeness = len(context) / max(1, len(context) + 5)  # Normalizar
        confidence = 0.6 + (context_completeness * 0.4)

        # Ajustar por tipo de decisión
        if decision_type in ["inference_rule_selection", "query_optimization"]:
            confidence *= 1.1
        elif decision_type == "security_action":
            confidence *= 1.2  # Más confianza en decisiones de seguridad

        return max(0.0, min(1.0, confidence))


# Instancia global
_explainability_engine = None


def get_explainability_engine() -> ExplainabilityEngine:
    """Obtener instancia global del motor de explainability."""
    global _explainability_engine
    if _explainability_engine is None:
        _explainability_engine = ExplainabilityEngine()
    return _explainability_engine