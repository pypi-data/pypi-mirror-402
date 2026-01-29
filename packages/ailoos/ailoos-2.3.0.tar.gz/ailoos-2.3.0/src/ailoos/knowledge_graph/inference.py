"""
Inference Engine para razonamiento automático en grafos de conocimiento.
Implementa motor de inferencia con soporte para reglas OWL y personalizadas.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Union, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import re

from ..core.logging import get_logger
from .core import get_knowledge_graph_core, KnowledgeGraphCore, Triple
from .query_engine import get_query_engine, QueryEngine
from ..auditing.audit_manager import get_audit_manager, AuditEventType
from ..auditing.metrics_collector import get_metrics_collector

logger = get_logger(__name__)


class InferenceType(Enum):
    """Tipos de inferencia soportados."""
    FORWARD_CHAINING = "forward_chaining"
    BACKWARD_CHAINING = "backward_chaining"


class RuleType(Enum):
    """Tipos de reglas."""
    OWL_TRANSITIVITY = "owl_transitivity"
    OWL_SYMMETRY = "owl_symmetry"
    OWL_EQUIVALENCE = "owl_equivalence"
    CUSTOM_SPARQL = "custom_sparql"


@dataclass
class InferenceRule:
    """Regla de inferencia."""
    rule_id: str
    rule_type: RuleType
    name: str
    description: str
    sparql_query: Optional[str] = None
    conditions: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    priority: int = 0
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_type": self.rule_type.value,
            "name": self.name,
            "description": self.description,
            "sparql_query": self.sparql_query,
            "conditions": self.conditions,
            "actions": self.actions,
            "priority": self.priority,
            "enabled": self.enabled
        }


@dataclass
class InferenceResult:
    """Resultado de una inferencia."""
    inferred_triples: List[Triple]
    rules_applied: List[str]
    execution_time_ms: float
    explanation: List[str]
    confidence_score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "inferred_triples": [t.to_dict() for t in self.inferred_triples],
            "rules_applied": self.rules_applied,
            "execution_time_ms": self.execution_time_ms,
            "explanation": self.explanation,
            "confidence_score": self.confidence_score,
            "total_inferred": len(self.inferred_triples)
        }


class InferenceEngine:
    """
    Motor de inferencia para razonamiento automático en grafos de conocimiento.
    Soporta reglas OWL estándar y reglas personalizadas SPARQL.
    """

    def __init__(self, kg_core: Optional[KnowledgeGraphCore] = None, query_engine: Optional[QueryEngine] = None):
        self.kg_core = kg_core or get_knowledge_graph_core()
        self.query_engine = query_engine or get_query_engine()
        self.audit_manager = get_audit_manager()
        self.metrics_collector = get_metrics_collector()

        # Reglas de inferencia
        self.inference_rules: Dict[str, InferenceRule] = {}
        self._initialize_owl_rules()

        # Cache de inferencias
        self.inference_cache: Dict[str, InferenceResult] = {}
        self.cache_enabled = True

        # Configuración
        self.max_inference_depth = 10
        self.max_inferred_triples = 1000
        self.inference_timeout_ms = 30000  # 30 segundos

    def _initialize_owl_rules(self):
        """Inicializar reglas OWL estándar."""

        # Regla de transitividad para rdfs:subClassOf
        transitivity_rule = InferenceRule(
            rule_id="owl_transitivity_subclass",
            rule_type=RuleType.OWL_TRANSITIVITY,
            name="Transitivity of rdfs:subClassOf",
            description="If A subclassOf B and B subclassOf C, then A subclassOf C",
            sparql_query="""
            SELECT ?a ?c WHERE {
                ?a <http://www.w3.org/2000/01/rdf-schema#subClassOf> ?b .
                ?b <http://www.w3.org/2000/01/rdf-schema#subClassOf> ?c .
                FILTER(?a != ?c)
            }
            """,
            priority=10
        )
        self.inference_rules[transitivity_rule.rule_id] = transitivity_rule

        # Regla de transitividad para owl:equivalentClass
        equivalence_rule = InferenceRule(
            rule_id="owl_transitivity_equivalent",
            rule_type=RuleType.OWL_EQUIVALENCE,
            name="Transitivity of owl:equivalentClass",
            description="If A equivalentClass B and B equivalentClass C, then A equivalentClass C",
            sparql_query="""
            SELECT ?a ?c WHERE {
                ?a <http://www.w3.org/2002/07/owl#equivalentClass> ?b .
                ?b <http://www.w3.org/2002/07/owl#equivalentClass> ?c .
                FILTER(?a != ?c)
            }
            """,
            priority=9
        )
        self.inference_rules[equivalence_rule.rule_id] = equivalence_rule

        # Regla de simetría para owl:equivalentClass
        symmetry_rule = InferenceRule(
            rule_id="owl_symmetry_equivalent",
            rule_type=RuleType.OWL_SYMMETRY,
            name="Symmetry of owl:equivalentClass",
            description="If A equivalentClass B, then B equivalentClass A",
            sparql_query="""
            SELECT ?b ?a WHERE {
                ?a <http://www.w3.org/2002/07/owl#equivalentClass> ?b .
                FILTER NOT EXISTS { ?b <http://www.w3.org/2002/07/owl#equivalentClass> ?a }
            }
            """,
            priority=8
        )
        self.inference_rules[symmetry_rule.rule_id] = symmetry_rule

        # Regla de transitividad para propiedades
        property_transitivity_rule = InferenceRule(
            rule_id="owl_property_transitivity",
            rule_type=RuleType.OWL_TRANSITIVITY,
            name="Transitivity of transitive properties",
            description="Apply transitivity for properties marked as owl:TransitiveProperty",
            sparql_query="""
            SELECT ?x ?z WHERE {
                ?p <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#TransitiveProperty> .
                ?x ?p ?y .
                ?y ?p ?z .
                FILTER(?x != ?z)
            }
            """,
            priority=7
        )
        self.inference_rules[property_transitivity_rule.rule_id] = property_transitivity_rule

    async def infer(
        self,
        inference_type: InferenceType = InferenceType.FORWARD_CHAINING,
        rules_to_apply: Optional[List[str]] = None,
        max_depth: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> InferenceResult:
        """
        Ejecutar inferencia automática.

        Args:
            inference_type: Tipo de inferencia (forward/backward chaining)
            rules_to_apply: Lista de IDs de reglas a aplicar (None = todas)
            max_depth: Profundidad máxima de inferencia
            user_id: ID del usuario que ejecuta la inferencia

        Returns:
            InferenceResult con triples inferidos y explicación
        """
        start_time = time.time()
        max_depth = max_depth or self.max_inference_depth

        try:
            # Seleccionar reglas a aplicar
            rules = self._select_rules(rules_to_apply)

            # Generar clave de cache
            cache_key = self._generate_cache_key(inference_type, rules, max_depth)
            if self.cache_enabled and cache_key in self.inference_cache:
                cached_result = self.inference_cache[cache_key]
                logger.info(f"Using cached inference result: {len(cached_result.inferred_triples)} triples")
                return cached_result

            # Ejecutar inferencia
            if inference_type == InferenceType.FORWARD_CHAINING:
                result = await self._forward_chaining(rules, max_depth, user_id)
            else:
                result = await self._backward_chaining(rules, max_depth, user_id)

            execution_time = (time.time() - start_time) * 1000
            result.execution_time_ms = execution_time

            # Optimizar resultado
            result = await self._optimize_inference_result(result)

            # Cachear resultado
            if self.cache_enabled:
                self.inference_cache[cache_key] = result

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.KNOWLEDGE_GRAPH_INFERENCE,
                resource="knowledge_graph",
                action="inference",
                user_id=user_id,
                details={
                    "inference_type": inference_type.value,
                    "rules_applied": len(rules),
                    "triples_inferred": len(result.inferred_triples),
                    "execution_time_ms": execution_time
                },
                success=True,
                processing_time_ms=execution_time
            )

            # Métricas
            self.metrics_collector.record_request("inference_engine.infer")
            self.metrics_collector.record_response_time(execution_time)

            logger.info(f"Inference completed: {len(result.inferred_triples)} triples inferred in {execution_time:.2f}ms")
            return result

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = str(e)

            # Logging de error
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph",
                action="inference",
                user_id=user_id,
                details={
                    "inference_type": inference_type.value,
                    "error": error_msg,
                    "execution_time_ms": execution_time
                },
                success=False,
                processing_time_ms=execution_time
            )

            self.metrics_collector.record_error("inference_engine.infer", "inference_error")
            logger.error(f"Inference failed: {error_msg}")

            return InferenceResult(
                inferred_triples=[],
                rules_applied=[],
                execution_time_ms=execution_time,
                explanation=[f"Error: {error_msg}"],
                confidence_score=0.0
            )

    def _select_rules(self, rules_to_apply: Optional[List[str]]) -> List[InferenceRule]:
        """Seleccionar reglas a aplicar."""
        if rules_to_apply:
            return [self.inference_rules[rule_id] for rule_id in rules_to_apply
                   if rule_id in self.inference_rules and self.inference_rules[rule_id].enabled]
        else:
            return [rule for rule in self.inference_rules.values() if rule.enabled]

    def _generate_cache_key(self, inference_type: InferenceType, rules: List[InferenceRule], max_depth: int) -> str:
        """Generar clave de cache para inferencia."""
        rule_ids = sorted([rule.rule_id for rule in rules])
        return f"{inference_type.value}_{'_'.join(rule_ids)}_{max_depth}"

    async def _forward_chaining(
        self,
        rules: List[InferenceRule],
        max_depth: int,
        user_id: Optional[str]
    ) -> InferenceResult:
        """
        Ejecutar forward chaining: aplicar reglas a hechos existentes para generar nuevos hechos.
        """
        inferred_triples: Set[Tuple[str, str, Union[str, int, float, bool]]] = set()
        rules_applied: List[str] = []
        explanation: List[str] = []
        confidence_score = 1.0

        # Obtener hechos existentes
        existing_triples = await self.kg_core.get_all_triples()
        existing_set = set((t.subject, t.predicate, t.object) for t in existing_triples)

        # Aplicar reglas iterativamente hasta max_depth
        for depth in range(max_depth):
            new_inferences = 0

            for rule in sorted(rules, key=lambda r: r.priority, reverse=True):
                if not rule.enabled:
                    continue

                try:
                    # Ejecutar regla
                    rule_results = await self._execute_rule(rule, user_id)

                    for result_triple in rule_results:
                        triple_tuple = (result_triple.subject, result_triple.predicate, result_triple.object)

                        # Solo agregar si no existe ya
                        if triple_tuple not in existing_set and triple_tuple not in inferred_triples:
                            inferred_triples.add(triple_tuple)
                            new_inferences += 1
                            explanation.append(f"Depth {depth}: Applied rule '{rule.name}' -> {result_triple}")

                    if rule_results:
                        rules_applied.append(rule.rule_id)

                except Exception as e:
                    logger.warning(f"Error executing rule {rule.rule_id}: {e}")
                    confidence_score *= 0.9  # Reducir confianza por error

            # Si no hay nuevas inferencias, terminar
            if new_inferences == 0:
                break

            # Limitar número de inferencias
            if len(inferred_triples) >= self.max_inferred_triples:
                explanation.append(f"Stopped at depth {depth}: Maximum inferences reached ({self.max_inferred_triples})")
                break

        # Convertir a objetos Triple
        inferred_triple_objects = [Triple(s, p, o) for s, p, o in inferred_triples]

        return InferenceResult(
            inferred_triples=inferred_triple_objects,
            rules_applied=rules_applied,
            execution_time_ms=0.0,  # Se establece después
            explanation=explanation,
            confidence_score=confidence_score
        )

    async def _backward_chaining(
        self,
        rules: List[InferenceRule],
        max_depth: int,
        user_id: Optional[str]
    ) -> InferenceResult:
        """
        Backward chaining: comenzar desde una hipótesis y trabajar hacia atrás.
        Implementación simplificada - en producción sería más compleja.
        """
        # Para esta implementación, backward chaining es similar a forward
        # En una implementación completa, comenzaría desde goals específicos
        return await self._forward_chaining(rules, max_depth, user_id)

    async def _execute_rule(self, rule: InferenceRule, user_id: Optional[str]) -> List[Triple]:
        """Ejecutar una regla de inferencia."""
        if not rule.sparql_query:
            return []

        try:
            # Ejecutar query SPARQL
            query_result = await self.query_engine.execute_query(
                rule.sparql_query,
                user_id=user_id
            )

            if not query_result.success:
                logger.warning(f"Rule {rule.rule_id} query failed: {query_result.error}")
                return []

            # Convertir resultados a triples inferidos
            inferred_triples = []

            for result in query_result.results:
                # Dependiendo del tipo de regla, crear diferentes triples
                if rule.rule_type == RuleType.OWL_TRANSITIVITY:
                    if len(query_result.results[0].to_tuple()) >= 2:
                        # Para transitividad: A -> C
                        inferred_triples.append(Triple(
                            result.subject,
                            "http://www.w3.org/2000/01/rdf-schema#subClassOf",
                            result.object
                        ))
                elif rule.rule_type == RuleType.OWL_SYMMETRY:
                    # Para simetría: B -> A
                    inferred_triples.append(Triple(
                        result.object,
                        "http://www.w3.org/2002/07/owl#equivalentClass",
                        result.subject
                    ))
                elif rule.rule_type == RuleType.OWL_EQUIVALENCE:
                    # Para equivalencia transitiva
                    inferred_triples.append(Triple(
                        result.subject,
                        "http://www.w3.org/2002/07/owl#equivalentClass",
                        result.object
                    ))
                elif rule.rule_type == RuleType.CUSTOM_SPARQL:
                    # Para reglas personalizadas, usar el resultado directamente
                    inferred_triples.append(result)

            return inferred_triples

        except Exception as e:
            logger.error(f"Error executing rule {rule.rule_id}: {e}")
            return []

    async def _optimize_inference_result(self, result: InferenceResult) -> InferenceResult:
        """Optimizar resultado de inferencia."""
        # Eliminar duplicados
        seen = set()
        unique_triples = []

        for triple in result.inferred_triples:
            triple_tuple = (triple.subject, triple.predicate, triple.object)
            if triple_tuple not in seen:
                seen.add(triple_tuple)
                unique_triples.append(triple)

        # Limitar número de explicaciones
        if len(result.explanation) > 100:
            result.explanation = result.explanation[:100]
            result.explanation.append(f"... and {len(result.explanation) - 100} more inferences")

        result.inferred_triples = unique_triples
        return result

    async def add_custom_rule(
        self,
        rule_id: str,
        name: str,
        description: str,
        sparql_query: str,
        rule_type: RuleType = RuleType.CUSTOM_SPARQL,
        priority: int = 0,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Agregar una regla personalizada de inferencia.

        Args:
            rule_id: ID único de la regla
            name: Nombre de la regla
            description: Descripción
            sparql_query: Query SPARQL que define la regla
            rule_type: Tipo de regla
            priority: Prioridad de ejecución
            user_id: ID del usuario

        Returns:
            True si se agregó exitosamente
        """
        try:
            if rule_id in self.inference_rules:
                raise ValueError(f"Rule {rule_id} already exists")

            rule = InferenceRule(
                rule_id=rule_id,
                rule_type=rule_type,
                name=name,
                description=description,
                sparql_query=sparql_query,
                priority=priority,
                enabled=True
            )

            self.inference_rules[rule_id] = rule

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.KNOWLEDGE_GRAPH_OPERATION,
                resource="knowledge_graph",
                action="add_inference_rule",
                user_id=user_id,
                details=rule.to_dict(),
                success=True
            )

            # Limpiar cache
            self.inference_cache.clear()

            logger.info(f"Added custom inference rule: {rule_id}")
            return True

        except Exception as e:
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph",
                action="add_inference_rule",
                user_id=user_id,
                details={"rule_id": rule_id, "error": str(e)},
                success=False
            )

            logger.error(f"Failed to add custom rule {rule_id}: {e}")
            return False

    def get_inference_rules(self) -> Dict[str, Dict[str, Any]]:
        """Obtener todas las reglas de inferencia."""
        return {rule_id: rule.to_dict() for rule_id, rule in self.inference_rules.items()}

    def enable_rule(self, rule_id: str) -> bool:
        """Habilitar una regla de inferencia."""
        if rule_id in self.inference_rules:
            self.inference_rules[rule_id].enabled = True
            self.inference_cache.clear()  # Limpiar cache
            return True
        return False

    def disable_rule(self, rule_id: str) -> bool:
        """Deshabilitar una regla de inferencia."""
        if rule_id in self.inference_rules:
            self.inference_rules[rule_id].enabled = False
            self.inference_cache.clear()  # Limpiar cache
            return True
        return False

    def clear_cache(self):
        """Limpiar cache de inferencias."""
        self.inference_cache.clear()
        logger.info("Inference cache cleared")

    async def apply_inference_to_graph(
        self,
        inference_result: InferenceResult,
        user_id: Optional[str] = None
    ) -> int:
        """
        Aplicar resultados de inferencia al grafo de conocimiento.

        Args:
            inference_result: Resultado de inferencia a aplicar
            user_id: ID del usuario

        Returns:
            Número de triples agregados
        """
        added_count = 0

        for triple in inference_result.inferred_triples:
            if await self.kg_core.add_triple(triple, user_id):
                added_count += 1

        logger.info(f"Applied {added_count} inferred triples to knowledge graph")
        return added_count


# Instancia global
_inference_engine = None


def get_inference_engine() -> InferenceEngine:
    """Obtener instancia global del motor de inferencia."""
    global _inference_engine
    if _inference_engine is None:
        _inference_engine = InferenceEngine()
    return _inference_engine