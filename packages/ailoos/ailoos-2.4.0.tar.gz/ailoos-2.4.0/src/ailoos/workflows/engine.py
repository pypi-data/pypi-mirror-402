"""
Workflow Engine - Motor de Orquestación Multimodal
=================================================

Sistema de estados finitos que coordina la ejecución de workflows complejos
que combinan visión, expertos especializados y herramientas.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import time

from ..models.empoorio_lm.expert_system import ExpertManager, Domain
from ..inference.api import EmpoorioLMInferenceAPI
from ..reasoning import ProblemDecomposer, ResponseCritic, ReflectionEngine
from ..reasoning.planner import ProblemPlan, ProblemStep
from ..reasoning.critic import ResponseCritique
from ..reasoning.reflection import ReasoningTrace, ReasoningStep

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStep:
    """Paso individual en un workflow."""
    step_id: str
    step_type: str  # 'vision', 'expert', 'tool', 'validation'
    description: str
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # IDs de pasos previos
    timeout_seconds: int = 30

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "step_type": self.step_type,
            "description": self.description,
            "config": self.config,
            "dependencies": self.dependencies,
            "timeout_seconds": self.timeout_seconds
        }


@dataclass
class WorkflowResult:
    """Resultado de la ejecución de un workflow."""
    workflow_id: str
    success: bool
    final_output: Any
    execution_time: float
    steps_executed: List[str]
    step_results: Dict[str, Any]
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "success": self.success,
            "final_output": self.final_output,
            "execution_time": self.execution_time,
            "steps_executed": self.steps_executed,
            "step_results": self.step_results,
            "errors": self.errors,
            "metadata": self.metadata
        }


@dataclass
class ThinkingBudget:
    """Presupuesto de tiempo para razonamiento iterativo."""
    max_time_seconds: int = 300  # 5 minutos por defecto
    max_iterations: int = 5
    min_confidence_threshold: float = 0.7
    time_per_iteration_seconds: int = 60  # 1 minuto por iteración


@dataclass
class IterativeResult:
    """Resultado de ejecución iterativa con reflexión."""
    workflow_id: str
    success: bool
    final_output: Any
    total_iterations: int
    total_time: float
    final_confidence: float
    reasoning_trace: ReasoningTrace
    corrections_applied: List[Dict[str, Any]] = field(default_factory=list)
    budget_exceeded: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "success": self.success,
            "final_output": self.final_output,
            "total_iterations": self.total_iterations,
            "total_time": self.total_time,
            "final_confidence": self.final_confidence,
            "corrections_applied": self.corrections_applied,
            "budget_exceeded": self.budget_exceeded,
            "metadata": self.metadata
        }


class WorkflowEngine:
    """
    Motor de orquestación para workflows multimodales.

    Coordina la ejecución de pasos que pueden incluir:
    - Visión: Extracción de texto/imágenes
    - Expertos: Análisis especializado por dominio
    - Herramientas: Cálculos y validaciones
    - Validaciones: Verificación de resultados
    """

    def __init__(self, expert_manager: ExpertManager, inference_api: EmpoorioLMInferenceAPI):
        self.expert_manager = expert_manager
        self.inference_api = inference_api

        # Componentes de razonamiento para pensamiento iterativo
        self.problem_decomposer = ProblemDecomposer(inference_api)
        self.response_critic = ResponseCritic(inference_api)
        self.reflection_engine = ReflectionEngine(inference_api)

        # Registro de funciones disponibles
        self.step_handlers = {
            'vision': self._handle_vision_step,
            'expert': self._handle_expert_step,
            'tool': self._handle_tool_step,
            'validation': self._handle_validation_step,
            'deep_thinking': self._handle_deep_thinking_step
        }

        # Estado de ejecución
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.active_deep_thinking: Dict[str, Dict[str, Any]] = {}

        logger.info("🚀 WorkflowEngine inicializado con capacidades de pensamiento profundo")

    async def execute_workflow(self, workflow_id: str, steps: List[WorkflowStep],
                              input_data: Any) -> WorkflowResult:
        """
        Ejecutar un workflow completo.

        Args:
            workflow_id: Identificador único del workflow
            steps: Lista ordenada de pasos a ejecutar
            input_data: Datos de entrada iniciales

        Returns:
            Resultado completo de la ejecución
        """
        start_time = datetime.now()
        logger.info(f"🎯 Iniciando workflow: {workflow_id}")

        # Inicializar estado del workflow
        workflow_state = {
            'current_data': input_data,
            'step_results': {},
            'executed_steps': [],
            'errors': []
        }
        self.active_workflows[workflow_id] = workflow_state

        try:
            # Resolver dependencias y orden de ejecución
            execution_order = self._resolve_dependencies(steps)

            # Ejecutar pasos en orden
            for step in execution_order:
                logger.info(f"📍 Ejecutando paso: {step.step_id} ({step.step_type})")

                try:
                    # Ejecutar paso con timeout
                    step_result = await asyncio.wait_for(
                        self._execute_step(step, workflow_state),
                        timeout=step.timeout_seconds
                    )

                    # Almacenar resultado
                    workflow_state['step_results'][step.step_id] = step_result
                    workflow_state['executed_steps'].append(step.step_id)

                    # Actualizar datos para próximos pasos
                    workflow_state['current_data'] = step_result

                    logger.info(f"✅ Paso completado: {step.step_id}")

                except asyncio.TimeoutError:
                    error_msg = f"Timeout en paso {step.step_id} ({step.timeout_seconds}s)"
                    logger.error(f"❌ {error_msg}")
                    workflow_state['errors'].append(error_msg)
                    break

                except Exception as e:
                    error_msg = f"Error en paso {step.step_id}: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    workflow_state['errors'].append(error_msg)
                    break

            # Determinar resultado final
            execution_time = (datetime.now() - start_time).total_seconds()
            success = len(workflow_state['errors']) == 0

            final_output = workflow_state['current_data'] if success else None

            result = WorkflowResult(
                workflow_id=workflow_id,
                success=success,
                final_output=final_output,
                execution_time=execution_time,
                steps_executed=workflow_state['executed_steps'],
                step_results=workflow_state['step_results'],
                errors=workflow_state['errors'],
                metadata={
                    'total_steps': len(steps),
                    'steps_completed': len(workflow_state['executed_steps'])
                }
            )

            logger.info(f"🏁 Workflow {workflow_id} completado: {'✅ Éxito' if success else '❌ Falló'}")
            return result

        finally:
            # Limpiar estado
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]

    async def execute_deep_thinking(
        self,
        workflow_id: str,
        problem_statement: str,
        input_data: Any,
        thinking_budget: Optional[ThinkingBudget] = None,
        domain: str = "general"
    ) -> IterativeResult:
        """
        Ejecutar pensamiento profundo iterativo con descomposición de problemas.

        Args:
            workflow_id: Identificador único del workflow de pensamiento
            problem_statement: Declaración del problema complejo
            input_data: Datos de entrada iniciales
            thinking_budget: Presupuesto de tiempo y iteraciones
            domain: Dominio del problema para descomposición

        Returns:
            Resultado del pensamiento iterativo con reflexión
        """
        if thinking_budget is None:
            thinking_budget = ThinkingBudget()

        start_time = time.time()
        logger.info(f"🧠 Iniciando pensamiento profundo: {workflow_id}")

        # Inicializar estado del pensamiento profundo
        thinking_state = {
            'problem_statement': problem_statement,
            'current_iteration': 0,
            'total_time_spent': 0,
            'reasoning_steps': [],
            'corrections_applied': [],
            'current_plan': None,
            'final_confidence': 0.0
        }
        self.active_deep_thinking[workflow_id] = thinking_state

        try:
            # Paso 1: Descomponer el problema usando ProblemDecomposer
            logger.info("📋 Descomponiendo problema complejo...")
            problem_plan = await self.problem_decomposer.decompose_problem(
                problem_statement=problem_statement,
                domain=domain,
                max_steps=10,
                complexity_level="complex"
            )

            thinking_state['current_plan'] = problem_plan

            # Crear traza de razonamiento inicial
            reasoning_trace = ReasoningTrace(
                trace_id=f"{workflow_id}_trace",
                problem_statement=problem_statement,
                steps=[]
            )

            # Paso 2: Ejecutar iterativamente con reflexión
            final_output = None
            current_confidence = 0.0

            for iteration in range(thinking_budget.max_iterations):
                iteration_start = time.time()
                thinking_state['current_iteration'] = iteration + 1

                logger.info(f"🔄 Iteración {iteration + 1}/{thinking_budget.max_iterations}")

                # Verificar presupuesto de tiempo
                elapsed_time = time.time() - start_time
                if elapsed_time >= thinking_budget.max_time_seconds:
                    logger.warning(f"⏰ Presupuesto de tiempo excedido: {elapsed_time:.1f}s")
                    thinking_state['budget_exceeded'] = True
                    break

                # Ejecutar plan actual
                iteration_result = await self._execute_problem_plan(
                    problem_plan, input_data, iteration
                )

                # Evaluar resultado con ResponseCritic
                critique = await self.response_critic.critique_response(
                    response=str(iteration_result.get('output', '')),
                    context=f"Iteración {iteration + 1} del problema: {problem_statement}",
                    response_type="analytical",
                    user_query=problem_statement
                )

                current_confidence = critique.overall_score

                # Registrar paso de razonamiento
                reasoning_step = ReasoningStep(
                    step_id=f"iteration_{iteration + 1}",
                    description=f"Iteración {iteration + 1}: {iteration_result.get('summary', 'Ejecución del plan')}",
                    reasoning_type="iterative_planning",
                    confidence=current_confidence,
                    evidence=[f"Resultado: {iteration_result.get('output', '')}"],
                    assumptions=[f"Plan válido con {len(problem_plan.steps)} pasos"],
                    alternatives_considered=[f"Plan alternativo {i+1}" for i in range(min(3, len(problem_plan.steps)))]
                )
                reasoning_trace.steps.append(reasoning_step)
                thinking_state['reasoning_steps'].append(reasoning_step)

                # Verificar si la confianza es suficiente
                if current_confidence >= thinking_budget.min_confidence_threshold:
                    logger.info(f"✅ Confianza suficiente alcanzada: {current_confidence:.2f}")
                    final_output = iteration_result.get('output')
                    thinking_state['final_confidence'] = current_confidence
                    break

                # Aplicar correcciones si confianza es baja
                if current_confidence < thinking_budget.min_confidence_threshold:
                    logger.info(f"🔧 Aplicando correcciones (confianza: {current_confidence:.2f})")

                    correction = await self._apply_corrections(
                        critique, problem_plan, iteration_result, iteration
                    )

                    thinking_state['corrections_applied'].append({
                        'iteration': iteration + 1,
                        'critique': critique.to_dict(),
                        'correction_applied': correction
                    })

                    # Optimizar plan basado en correcciones
                    if iteration < thinking_budget.max_iterations - 1:
                        problem_plan = await self.problem_decomposer.optimize_plan(problem_plan)

                # Actualizar tiempo
                iteration_time = time.time() - iteration_start
                thinking_state['total_time_spent'] += iteration_time

                # Limitar tiempo por iteración
                if iteration_time > thinking_budget.time_per_iteration_seconds:
                    logger.warning(f"⚠️ Iteración tomó demasiado tiempo: {iteration_time:.1f}s")

            # Paso 3: Reflexión final y aprendizaje
            reasoning_trace.final_outcome = str(final_output) if final_output else "Sin resultado final"
            reasoning_trace.success_rating = thinking_state.get('final_confidence', current_confidence)

            # Analizar la traza de razonamiento
            analysis = await self.reflection_engine.analyze_reasoning_trace(
                trace=reasoning_trace,
                analysis_depth="comprehensive"
            )

            # Añadir insights a la traza
            reasoning_trace.lessons_learned = analysis.get('lessons_learned', [])
            reasoning_trace.improvement_suggestions = analysis.get('improvement_suggestions', [])

            # Registrar traza para aprendizaje futuro
            self.reflection_engine.add_reasoning_trace(reasoning_trace)

            total_time = time.time() - start_time
            success = final_output is not None and current_confidence >= thinking_budget.min_confidence_threshold

            result = IterativeResult(
                workflow_id=workflow_id,
                success=success,
                final_output=final_output,
                total_iterations=thinking_state['current_iteration'],
                total_time=total_time,
                final_confidence=current_confidence,
                reasoning_trace=reasoning_trace,
                corrections_applied=thinking_state['corrections_applied'],
                budget_exceeded=thinking_state.get('budget_exceeded', False),
                metadata={
                    'problem_plan_steps': len(problem_plan.steps),
                    'analysis_insights': len(analysis.get('strengths', [])),
                    'domain': domain,
                    'budget_used': total_time / thinking_budget.max_time_seconds
                }
            )

            logger.info(f"🏁 Pensamiento profundo completado: {'✅ Éxito' if success else '❌ Falló'} "
                       f"({thinking_state['current_iteration']} iteraciones, {total_time:.1f}s)")

            return result

        finally:
            # Limpiar estado
            if workflow_id in self.active_deep_thinking:
                del self.active_deep_thinking[workflow_id]

    def _resolve_dependencies(self, steps: List[WorkflowStep]) -> List[WorkflowStep]:
        """Resolver dependencias y determinar orden de ejecución."""
        # Por simplicidad, asumir que los pasos están en orden correcto
        # En implementación completa, implementar topological sort
        return steps

    async def _execute_step(self, step: WorkflowStep, workflow_state: Dict[str, Any]) -> Any:
        """Ejecutar un paso individual."""
        if step.step_type not in self.step_handlers:
            raise ValueError(f"Tipo de paso desconocido: {step.step_type}")

        handler = self.step_handlers[step.step_type]
        return await handler(step, workflow_state)

    async def _handle_vision_step(self, step: WorkflowStep, workflow_state: Dict[str, Any]) -> Any:
        """Manejar paso de visión (extracción de texto/imágenes)."""
        input_data = workflow_state['current_data']

        # Simulación: en producción integraría con modelo de visión
        if isinstance(input_data, dict) and 'image_path' in input_data:
            # Simular extracción de texto de imagen
            extracted_text = f"Texto extraído de {input_data['image_path']}: [contenido simulado]"
            logger.info(f"👁️ Visión: {extracted_text[:50]}...")

            return {
                'extracted_text': extracted_text,
                'confidence': 0.95,
                'step_type': 'vision'
            }
        else:
            raise ValueError("Paso de visión requiere input_data con 'image_path'")

    async def _handle_expert_step(self, step: WorkflowStep, workflow_state: Dict[str, Any]) -> Any:
        """Manejar paso de experto especializado."""
        input_data = workflow_state['current_data']
        domain = step.config.get('domain', 'general')

        # Mapear string a enum Domain
        domain_enum = getattr(Domain, domain.upper(), Domain.GENERAL)

        # Cargar experto si no está cargado
        expert_loaded = self.expert_manager.load_expert(domain_enum, f"{domain}_expert")
        if not expert_loaded:
            logger.warning(f"⚠️ Experto no encontrado para dominio {domain}, usando general")

        # Preparar prompt para el experto
        if isinstance(input_data, dict) and 'extracted_text' in input_data:
            prompt = step.config.get('prompt_template', '').format(
                text=input_data['extracted_text']
            )
        else:
            prompt = str(input_data)

        # Ejecutar inferencia con experto
        try:
            from ..inference.api import InferenceRequest

            request = InferenceRequest(
                prompt=prompt,
                max_tokens=step.config.get('max_tokens', 200),
                temperature=0.7
            )

            response = await self.inference_api.generate(request)

            logger.info(f"🧠 Experto {domain}: Respuesta generada")
            return {
                'expert_response': response.text,
                'domain': domain,
                'confidence': 0.88,
                'step_type': 'expert'
            }

        except Exception as e:
            logger.error(f"Error en inferencia de experto: {e}")
            raise

    async def _handle_tool_step(self, step: WorkflowStep, workflow_state: Dict[str, Any]) -> Any:
        """Manejar paso de herramienta (cálculos, validaciones)."""
        input_data = workflow_state['current_data']
        tool_name = step.config.get('tool_name', '')

        if tool_name == 'calculator':
            # Herramienta de cálculo simple
            expression = step.config.get('expression', '')
            if 'tax_amount' in input_data:
                # Calcular IVA
                base_amount = input_data.get('base_amount', 0)
                tax_rate = step.config.get('tax_rate', 0.21)  # 21% IVA por defecto
                tax_amount = base_amount * tax_rate

                result = {
                    'calculation': f"{base_amount} * {tax_rate} = {tax_amount}",
                    'tax_amount': tax_amount,
                    'tax_rate': tax_rate,
                    'step_type': 'tool'
                }

                logger.info(f"🧮 Calculadora: {result['calculation']}")
                return result

        elif tool_name == 'validator':
            # Herramienta de validación
            rules = step.config.get('rules', [])
            validation_results = []

            for rule in rules:
                rule_type = rule.get('type', '')
                if rule_type == 'range':
                    value = input_data.get(rule.get('field', ''), 0)
                    min_val = rule.get('min', 0)
                    max_val = rule.get('max', float('inf'))

                    valid = min_val <= value <= max_val
                    validation_results.append({
                        'rule': rule,
                        'valid': valid,
                        'value': value
                    })

            all_valid = all(r['valid'] for r in validation_results)

            return {
                'validation_results': validation_results,
                'all_valid': all_valid,
                'step_type': 'tool'
            }

        else:
            raise ValueError(f"Herramienta desconocida: {tool_name}")

    async def _handle_validation_step(self, step: WorkflowStep, workflow_state: Dict[str, Any]) -> Any:
        """Manejar paso de validación final."""
        input_data = workflow_state['current_data']

        # Validar estructura del resultado
        required_fields = step.config.get('required_fields', [])
        validation_errors = []

        for field in required_fields:
            if field not in input_data:
                validation_errors.append(f"Campo requerido faltante: {field}")

        # Validar tipos de datos
        type_checks = step.config.get('type_checks', {})
        for field, expected_type in type_checks.items():
            if field in input_data:
                actual_value = input_data[field]
                if not isinstance(actual_value, eval(expected_type)):
                    validation_errors.append(
                        f"Tipo incorrecto para {field}: esperado {expected_type}, "
                        f"obtenido {type(actual_value).__name__}"
                    )

        success = len(validation_errors) == 0

        result = {
            'validation_success': success,
            'validation_errors': validation_errors,
            'validated_data': input_data if success else None,
            'step_type': 'validation'
        }

        if success:
            logger.info("✅ Validación exitosa")
        else:
            logger.warning(f"⚠️ Errores de validación: {validation_errors}")

        return result

    async def _handle_deep_thinking_step(self, step: WorkflowStep, workflow_state: Dict[str, Any]) -> Any:
        """Manejar paso de pensamiento profundo iterativo."""
        input_data = workflow_state['current_data']

        # Extraer parámetros de configuración
        config = step.config
        thinking_budget_config = config.get('thinking_budget', {})
        thinking_budget = ThinkingBudget(
            max_time_seconds=thinking_budget_config.get('max_time_seconds', 300),
            max_iterations=thinking_budget_config.get('max_iterations', 5),
            min_confidence_threshold=thinking_budget_config.get('min_confidence_threshold', 0.7),
            time_per_iteration_seconds=thinking_budget_config.get('time_per_iteration_seconds', 60)
        )

        domain = config.get('domain', 'general')

        # Extraer declaración del problema de los datos de entrada
        if isinstance(input_data, dict) and 'problem_statement' in input_data:
            problem_statement = input_data['problem_statement']
            deep_input_data = input_data.get('input_data', input_data)
        else:
            # Asumir que input_data es la declaración del problema
            problem_statement = str(input_data)
            deep_input_data = input_data

        # Generar ID único para el pensamiento profundo
        deep_thinking_id = f"{workflow_state.get('workflow_id', 'unknown')}_{step.step_id}"

        try:
            # Ejecutar pensamiento profundo
            result = await self.execute_deep_thinking(
                workflow_id=deep_thinking_id,
                problem_statement=problem_statement,
                input_data=deep_input_data,
                thinking_budget=thinking_budget,
                domain=domain
            )

            logger.info(f"🧠 Pensamiento profundo completado: {'✅ Éxito' if result.success else '❌ Falló'}")

            return {
                'deep_thinking_result': result.to_dict(),
                'final_output': result.final_output,
                'confidence': result.final_confidence,
                'iterations': result.total_iterations,
                'reasoning_trace': result.reasoning_trace.to_dict() if result.reasoning_trace else None,
                'step_type': 'deep_thinking'
            }

        except Exception as e:
            logger.error(f"❌ Error en pensamiento profundo: {e}")
            raise

    async def _execute_problem_plan(
        self,
        problem_plan: ProblemPlan,
        input_data: Any,
        iteration: int
    ) -> Dict[str, Any]:
        """Ejecutar un plan de problema descompuesto."""
        logger.info(f"📋 Ejecutando plan con {len(problem_plan.steps)} pasos")

        plan_results = {}
        current_data = input_data

        # Resolver dependencias y orden de ejecución
        execution_order = self._resolve_problem_dependencies(problem_plan.steps)

        for step in execution_order:
            try:
                # Convertir ProblemStep a WorkflowStep para reutilizar lógica
                workflow_step = WorkflowStep(
                    step_id=step.step_id,
                    step_type='expert',  # Usar experto por defecto para pasos de razonamiento
                    description=step.description,
                    config={
                        'domain': 'general',
                        'prompt_template': f"Resuelve este paso del problema: {step.description}\n\nContexto: {{text}}",
                        'max_tokens': 500
                    },
                    dependencies=step.dependencies,
                    timeout_seconds=60
                )

                # Ejecutar paso
                step_result = await self._execute_step(workflow_step, {'current_data': current_data})
                plan_results[step.step_id] = step_result
                current_data = step_result

                logger.info(f"✅ Paso completado: {step.step_id}")

            except Exception as e:
                logger.error(f"❌ Error en paso {step.step_id}: {e}")
                plan_results[step.step_id] = {'error': str(e), 'step_type': 'error'}

        # Sintetizar resultado final
        final_output = self._synthesize_plan_results(plan_results, problem_plan)
        summary = f"Plan ejecutado con {len(plan_results)} pasos, {len([r for r in plan_results.values() if 'error' not in r])} exitosos"

        return {
            'output': final_output,
            'plan_results': plan_results,
            'summary': summary,
            'success_rate': len([r for r in plan_results.values() if 'error' not in r]) / len(plan_results) if plan_results else 0
        }

    def _resolve_problem_dependencies(self, steps: List[ProblemStep]) -> List[ProblemStep]:
        """Resolver dependencias entre pasos de problema (simplificado)."""
        # Por simplicidad, asumir que los pasos están en orden correcto
        # En implementación completa, implementar topological sort
        return steps

    def _synthesize_plan_results(self, plan_results: Dict[str, Any], problem_plan: ProblemPlan) -> str:
        """Sintetizar resultados del plan en una respuesta coherente."""
        successful_steps = [step_id for step_id, result in plan_results.items() if 'error' not in result]

        if not successful_steps:
            return "No se pudieron completar pasos del plan de razonamiento."

        # Combinar resultados de pasos exitosos
        synthesis_parts = []
        for step_id in successful_steps:
            result = plan_results[step_id]
            if isinstance(result, dict) and 'expert_response' in result:
                synthesis_parts.append(f"• {result['expert_response']}")

        if synthesis_parts:
            return "\n".join(synthesis_parts)
        else:
            return f"Plan completado con {len(successful_steps)} pasos exitosos."

    async def _apply_corrections(
        self,
        critique: 'ResponseCritique',
        problem_plan: ProblemPlan,
        iteration_result: Dict[str, Any],
        iteration: int
    ) -> Dict[str, Any]:
        """Aplicar correcciones basadas en la crítica del resultado."""
        logger.info("🔧 Aplicando correcciones basadas en crítica")

        # Identificar áreas que necesitan mejora
        low_score_dimensions = [
            dim for dim in critique.dimensions
            if dim.score < 0.7
        ]

        corrections = {}

        for dimension in low_score_dimensions:
            if dimension.name == "accuracy":
                corrections['accuracy'] = "Mejorar precisión verificando hechos y datos"
            elif dimension.name == "completeness":
                corrections['completeness'] = "Añadir información faltante y detalles relevantes"
            elif dimension.name == "clarity":
                corrections['clarity'] = "Simplificar lenguaje y mejorar estructura"
            elif dimension.name == "relevance":
                corrections['relevance'] = "Enfocarse más en la pregunta del usuario"
            elif dimension.name == "coherence":
                corrections['coherence'] = "Mejorar flujo lógico y conexiones entre ideas"

        # Aplicar correcciones al plan si es necesario
        if corrections:
            # Aquí podríamos modificar el plan basado en las correcciones
            # Por simplicidad, registramos las correcciones para la siguiente iteración
            correction_summary = f"Correcciones aplicadas: {', '.join(corrections.values())}"
            logger.info(f"📝 {correction_summary}")

            return {
                'corrections_identified': corrections,
                'correction_summary': correction_summary,
                'dimensions_improved': list(corrections.keys())
            }
        else:
            return {'corrections_identified': {}, 'correction_summary': 'No se requirieron correcciones mayores'}

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de un workflow en ejecución."""
        return self.active_workflows.get(workflow_id)

    def get_deep_thinking_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de un pensamiento profundo en ejecución."""
        return self.active_deep_thinking.get(workflow_id)

    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancelar un workflow en ejecución."""
        if workflow_id in self.active_workflows:
            del self.active_workflows[workflow_id]
            logger.info(f"🛑 Workflow cancelado: {workflow_id}")
            return True
        return False

    def cancel_deep_thinking(self, workflow_id: str) -> bool:
        """Cancelar un pensamiento profundo en ejecución."""
        if workflow_id in self.active_deep_thinking:
            del self.active_deep_thinking[workflow_id]
            logger.info(f"🛑 Pensamiento profundo cancelado: {workflow_id}")
            return True
        return False