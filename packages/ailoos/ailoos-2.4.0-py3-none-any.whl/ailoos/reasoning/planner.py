"""
Problem Decomposer - Advanced Planning and Problem Decomposition
================================================================

Uses EmpoorioLM to break down complex problems into manageable, actionable steps.
Implements hierarchical planning with dependency analysis and resource allocation.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re

from ..inference.api import EmpoorioLMInferenceAPI, InferenceConfig, InferenceRequest

logger = logging.getLogger(__name__)


@dataclass
class ProblemStep:
    """Represents a single step in a decomposed problem."""
    step_id: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    estimated_effort: int = 1  # 1-10 scale
    required_resources: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    priority: int = 5  # 1-10 scale, 10 being highest
    status: str = "pending"  # pending, in_progress, completed, blocked


@dataclass
class ProblemPlan:
    """Complete problem decomposition plan."""
    problem_statement: str
    steps: List[ProblemStep] = field(default_factory=list)
    total_estimated_effort: int = 0
    critical_path: List[str] = field(default_factory=list)
    resource_requirements: Dict[str, int] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    plan_metadata: Dict[str, Any] = field(default_factory=dict)


class ProblemDecomposer:
    """
    Advanced problem decomposer using EmpoorioLM for intelligent planning.

    Features:
    - Hierarchical problem decomposition
    - Dependency analysis and critical path identification
    - Resource allocation optimization
    - Effort estimation and prioritization
    - Success criteria definition
    """

    def __init__(self, inference_api: Optional[EmpoorioLMInferenceAPI] = None):
        """
        Initialize the Problem Decomposer.

        Args:
            inference_api: Pre-configured EmpoorioLM inference API instance
        """
        self.inference_api = inference_api
        self.decomposition_history: List[Dict[str, Any]] = []
        self.templates = self._load_decomposition_templates()

    async def initialize(self) -> bool:
        """Initialize the inference API if not provided."""
        if self.inference_api is None:
            config = InferenceConfig(
                model_path="./src/models/empoorio_lm/versions/empoorio_lm_v1.0.0-trained_267306",
                enable_guidance=True,
                guidance_output_format="inference"
            )
            self.inference_api = EmpoorioLMInferenceAPI(config)
            return await self.inference_api.load_model()
        return True

    def _load_decomposition_templates(self) -> Dict[str, str]:
        """Load problem decomposition templates for different domains."""
        return {
            "software_development": """
Desarrolla un plan detallado para implementar {problem}. Incluye:
1. Análisis de requisitos
2. Diseño de arquitectura
3. Desarrollo de componentes
4. Testing y validación
5. Despliegue y monitoreo

Para cada paso, especifica dependencias, recursos necesarios y criterios de éxito.
""",
            "research": """
Crea un plan de investigación para {problem}. Incluye:
1. Revisión de literatura existente
2. Formulación de hipótesis
3. Diseño experimental/metodológico
4. Recolección de datos
5. Análisis de resultados
6. Redacción y publicación

Identifica dependencias críticas y recursos requeridos.
""",
            "business_strategy": """
Desarrolla una estrategia para {problem}. Considera:
1. Análisis de mercado y competencia
2. Definición de objetivos
3. Desarrollo de plan de acción
4. Asignación de recursos
5. Implementación por fases
6. Medición de resultados y ajustes

Incluye métricas de éxito y puntos de control.
""",
            "general": """
Descompón el problema: {problem}

Proporciona un plan paso a paso que incluya:
- Pasos principales con dependencias
- Recursos necesarios
- Criterios de éxito para cada paso
- Estimación de esfuerzo relativo
- Identificación de riesgos potenciales
"""
        }

    async def decompose_problem(
        self,
        problem_statement: str,
        domain: str = "general",
        max_steps: int = 10,
        complexity_level: str = "medium"  # simple, medium, complex
    ) -> ProblemPlan:
        """
        Decompose a complex problem into manageable steps using EmpoorioLM.

        Args:
            problem_statement: The problem to decompose
            domain: Problem domain for template selection
            max_steps: Maximum number of steps to generate
            complexity_level: Level of detail in decomposition

        Returns:
            Complete problem decomposition plan
        """
        if not await self.initialize():
            raise RuntimeError("Failed to initialize EmpoorioLM inference API")

        # Select appropriate template
        template = self.templates.get(domain, self.templates["general"])

        # Create decomposition prompt
        prompt = self._create_decomposition_prompt(
            problem_statement, template, max_steps, complexity_level
        )

        # Generate decomposition using EmpoorioLM
        request = InferenceRequest(
            prompt=prompt,
            max_tokens=2048,
            temperature=0.3,  # Lower temperature for more structured output
            structured_output=True,
            schema=self._get_decomposition_schema()
        )

        try:
            response = await self.inference_api.generate(request)

            # Parse the structured response
            plan_data = self._parse_decomposition_response(response.text)

            # Create ProblemPlan object
            plan = ProblemPlan(problem_statement=problem_statement)

            # Convert parsed data to ProblemStep objects
            for step_data in plan_data.get("steps", []):
                step = ProblemStep(
                    step_id=step_data.get("id", f"step_{len(plan.steps)}"),
                    description=step_data.get("description", ""),
                    dependencies=step_data.get("dependencies", []),
                    estimated_effort=step_data.get("effort", 1),
                    required_resources=step_data.get("resources", []),
                    success_criteria=step_data.get("success_criteria", []),
                    priority=step_data.get("priority", 5)
                )
                plan.steps.append(step)

            # Calculate plan metrics
            self._calculate_plan_metrics(plan)

            # Store in history
            self.decomposition_history.append({
                "problem": problem_statement,
                "domain": domain,
                "steps_count": len(plan.steps),
                "created_at": datetime.now().isoformat()
            })

            logger.info(f"✅ Decomposed problem into {len(plan.steps)} steps")
            return plan

        except Exception as e:
            logger.error(f"❌ Error decomposing problem: {e}")
            # Return basic fallback plan
            return self._create_fallback_plan(problem_statement)

    def _create_decomposition_prompt(
        self,
        problem: str,
        template: str,
        max_steps: int,
        complexity: str
    ) -> str:
        """Create a structured prompt for problem decomposition."""
        complexity_guidance = {
            "simple": "Mantén el plan conciso con 3-5 pasos principales.",
            "medium": "Proporciona un plan detallado con 5-8 pasos, incluyendo sub-tareas.",
            "complex": "Crea un plan comprehensivo con hasta 10+ pasos, considerando múltiples perspectivas y contingencias."
        }

        return f"""
Eres un experto planificador y analista de problemas. Tu tarea es descomponer problemas complejos en pasos manejables y accionables.

PROBLEMA A DESCOMPONER:
{problem}

INSTRUCCIONES:
{template}

DIRECTRICES ADICIONALES:
- {complexity_guidance.get(complexity, complexity_guidance["medium"])}
- Máximo {max_steps} pasos principales
- Identifica dependencias claras entre pasos
- Estima el esfuerzo relativo (1-10) para cada paso
- Lista recursos específicos necesarios
- Define criterios de éxito medibles para cada paso
- Prioriza pasos críticos (1-10, donde 10 es más crítico)

FORMATO DE RESPUESTA:
Proporciona la respuesta en formato JSON estructurado con los siguientes campos:
- steps: array de objetos con id, description, dependencies, effort, resources, success_criteria, priority
- total_effort: suma de esfuerzos
- critical_path: array de IDs de pasos críticos
- resource_summary: objeto con resumen de recursos

RESPUESTA:
"""

    def _get_decomposition_schema(self) -> Dict[str, Any]:
        """Get JSON schema for structured decomposition output."""
        return {
            "type": "object",
            "properties": {
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "description": {"type": "string"},
                            "dependencies": {"type": "array", "items": {"type": "string"}},
                            "effort": {"type": "integer", "minimum": 1, "maximum": 10},
                            "resources": {"type": "array", "items": {"type": "string"}},
                            "success_criteria": {"type": "array", "items": {"type": "string"}},
                            "priority": {"type": "integer", "minimum": 1, "maximum": 10}
                        },
                        "required": ["id", "description"]
                    }
                },
                "total_effort": {"type": "integer"},
                "critical_path": {"type": "array", "items": {"type": "string"}},
                "resource_summary": {"type": "object"}
            },
            "required": ["steps"]
        }

    def _parse_decomposition_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the structured response from EmpoorioLM."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback: try parsing the entire response as JSON
                return json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON response, creating fallback structure")
            # Create a basic structure from text analysis
            return self._extract_steps_from_text(response_text)

    def _extract_steps_from_text(self, text: str) -> Dict[str, Any]:
        """Extract steps from plain text response as fallback."""
        lines = text.split('\n')
        steps = []
        step_count = 1

        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Extract step description
                description = re.sub(r'^[\d\-\•\.\s]*', '', line).strip()
                if description:
                    steps.append({
                        "id": f"step_{step_count}",
                        "description": description,
                        "dependencies": [],
                        "effort": 1,
                        "resources": [],
                        "success_criteria": [f"Completar {description}"],
                        "priority": 5
                    })
                    step_count += 1

        return {"steps": steps[:10]}  # Limit to 10 steps

    def _calculate_plan_metrics(self, plan: ProblemPlan):
        """Calculate comprehensive metrics for the problem plan."""
        # Calculate total effort
        plan.total_estimated_effort = sum(step.estimated_effort for step in plan.steps)

        # Identify critical path (simplified: steps with no dependencies first)
        completed_steps = set()
        critical_path = []

        while len(completed_steps) < len(plan.steps):
            available_steps = [
                step for step in plan.steps
                if step.step_id not in completed_steps and
                all(dep in completed_steps for dep in step.dependencies)
            ]

            if not available_steps:
                break

            # Select highest priority available step
            next_step = max(available_steps, key=lambda s: s.priority)
            critical_path.append(next_step.step_id)
            completed_steps.add(next_step.step_id)

        plan.critical_path = critical_path

        # Aggregate resource requirements
        for step in plan.steps:
            for resource in step.required_resources:
                plan.resource_requirements[resource] = plan.resource_requirements.get(resource, 0) + 1

    def _create_fallback_plan(self, problem_statement: str) -> ProblemPlan:
        """Create a basic fallback plan when AI decomposition fails."""
        plan = ProblemPlan(problem_statement=problem_statement)

        # Create basic 3-step plan
        plan.steps = [
            ProblemStep(
                step_id="step_1",
                description="Analizar y entender el problema completamente",
                estimated_effort=2,
                success_criteria=["Tener claro el alcance y objetivos"]
            ),
            ProblemStep(
                step_id="step_2",
                description="Desarrollar una solución o plan de acción",
                dependencies=["step_1"],
                estimated_effort=5,
                success_criteria=["Tener un plan viable definido"]
            ),
            ProblemStep(
                step_id="step_3",
                description="Implementar y validar la solución",
                dependencies=["step_2"],
                estimated_effort=3,
                success_criteria=["Solución funcionando correctamente"]
            )
        ]

        self._calculate_plan_metrics(plan)
        return plan

    async def optimize_plan(self, plan: ProblemPlan) -> ProblemPlan:
        """
        Optimize an existing plan for better efficiency and resource utilization.

        Args:
            plan: The plan to optimize

        Returns:
            Optimized plan
        """
        if not await self.initialize():
            return plan

        # Create optimization prompt
        prompt = f"""
Optimiza el siguiente plan de problema para mejorar eficiencia y reducir riesgos:

PROBLEMA: {plan.problem_statement}

PLAN ACTUAL:
{json.dumps([{
    "id": step.step_id,
    "description": step.description,
    "effort": step.estimated_effort,
    "dependencies": step.dependencies,
    "resources": step.required_resources
} for step in plan.steps], indent=2)}

INSTRUCCIONES:
- Identifica pasos que pueden paralelizarse
- Sugiere optimizaciones de recursos
- Reduce esfuerzo total si posible
- Mejora la secuencia lógica
- Añade pasos de mitigación de riesgos si necesario

Proporciona el plan optimizado en el mismo formato JSON.
"""

        request = InferenceRequest(
            prompt=prompt,
            max_tokens=1536,
            temperature=0.2,
            structured_output=True,
            schema=self._get_decomposition_schema()
        )

        try:
            response = await self.inference_api.generate(request)
            optimized_data = self._parse_decomposition_response(response.text)

            # Create optimized plan
            optimized_plan = ProblemPlan(problem_statement=plan.problem_statement)

            for step_data in optimized_data.get("steps", []):
                step = ProblemStep(
                    step_id=step_data.get("id", f"opt_step_{len(optimized_plan.steps)}"),
                    description=step_data.get("description", ""),
                    dependencies=step_data.get("dependencies", []),
                    estimated_effort=step_data.get("effort", 1),
                    required_resources=step_data.get("resources", []),
                    success_criteria=step_data.get("success_criteria", []),
                    priority=step_data.get("priority", 5)
                )
                optimized_plan.steps.append(step)

            self._calculate_plan_metrics(optimized_plan)

            logger.info(f"✅ Optimized plan: {len(plan.steps)} → {len(optimized_plan.steps)} steps")
            return optimized_plan

        except Exception as e:
            logger.error(f"❌ Error optimizing plan: {e}")
            return plan

    def get_decomposition_stats(self) -> Dict[str, Any]:
        """Get statistics about decomposition history."""
        if not self.decomposition_history:
            return {"total_decompositions": 0}

        return {
            "total_decompositions": len(self.decomposition_history),
            "average_steps": sum(h["steps_count"] for h in self.decomposition_history) / len(self.decomposition_history),
            "domains_used": list(set(h["domain"] for h in self.decomposition_history)),
            "recent_activity": self.decomposition_history[-5:] if self.decomposition_history else []
        }