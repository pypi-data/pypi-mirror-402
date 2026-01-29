"""
GraphQL API para el Grafo de Conocimiento AILOOS.
Proporciona schema GraphQL completo con resolvers para todas las operaciones.
"""

import graphene
from graphene import ObjectType, String, Int, Float, Boolean, List, Field, Mutation, InputObjectType
from graphene.types.datetime import DateTime
import asyncio
from typing import Dict, List as TypingList, Any, Optional, Union
from datetime import datetime

from ...core.logging import get_logger
from ..core import get_knowledge_graph_core, Triple, BackendType, FormatType
from ..query.query_executor import get_query_executor
from ..inference import get_inference_engine, InferenceType, InferenceRule
from ...auditing.audit_manager import get_audit_manager, AuditEventType
from ...auditing.metrics_collector import get_metrics_collector

logger = get_logger(__name__)


# Tipos GraphQL para el dominio
class TripleType(graphene.ObjectType):
    """Tipo GraphQL para triple RDF."""
    subject = String(required=True, description="Sujeto del triple")
    predicate = String(required=True, description="Predicado del triple")
    object = graphene.types.json.JSONString(required=True, description="Objeto del triple")

    def resolve_object(self, info):
        """Resolver para el objeto, convirtiendo tipos."""
        return self.object


class QueryResultType(graphene.ObjectType):
    """Tipo GraphQL para resultado de consulta."""
    query = String(required=True, description="Consulta ejecutada")
    results = List(TripleType, description="Resultados de la consulta")
    execution_time_ms = Float(description="Tiempo de ejecución en ms")
    result_count = Int(description="Número de resultados")
    error = String(description="Mensaje de error si existe")


class InferenceResultType(graphene.ObjectType):
    """Tipo GraphQL para resultado de inferencia."""
    inferred_triples = List(TripleType, description="Triples inferidos")
    rules_applied = List(String, description="Reglas aplicadas")
    execution_time_ms = Float(description="Tiempo de ejecución en ms")
    explanation = List(String, description="Explicación del proceso")
    confidence_score = Float(description="Puntuación de confianza")


class InferenceRuleType(graphene.ObjectType):
    """Tipo GraphQL para regla de inferencia."""
    rule_id = String(required=True, description="ID único de la regla")
    rule_type = String(required=True, description="Tipo de regla")
    name = String(required=True, description="Nombre de la regla")
    description = String(required=True, description="Descripción de la regla")
    sparql_query = String(description="Query SPARQL de la regla")
    conditions = List(String, description="Condiciones de la regla")
    actions = List(String, description="Acciones de la regla")
    priority = Int(description="Prioridad de ejecución")
    enabled = Boolean(description="Si la regla está habilitada")


class GraphStatsType(graphene.ObjectType):
    """Tipo GraphQL para estadísticas del grafo."""
    total_triples = Int(description="Total de triples")
    unique_subjects = Int(description="Sujetos únicos")
    unique_predicates = Int(description="Predicados únicos")
    backend_type = String(description="Tipo de backend")
    storage_health = graphene.types.json.JSONString(description="Estado de salud del storage")


class HealthStatusType(graphene.ObjectType):
    """Tipo GraphQL para estado de salud."""
    service_name = String(required=True, description="Nombre del servicio")
    status = String(required=True, description="Estado del servicio")
    response_time_ms = Float(description="Tiempo de respuesta")
    error_message = String(description="Mensaje de error")
    last_check = DateTime(description="Última verificación")
    uptime_seconds = Int(description="Tiempo de actividad")


# Inputs para mutations
class TripleInput(graphene.InputObjectType):
    """Input para triple RDF."""
    subject = String(required=True)
    predicate = String(required=True)
    object = graphene.types.json.JSONString(required=True)


class QueryInput(graphene.InputObjectType):
    """Input para consulta."""
    query = String(required=True)
    parameters = graphene.types.json.JSONString()
    optimize = Boolean(default_value=True)
    use_cache = Boolean(default_value=True)


class InferenceInput(graphene.InputObjectType):
    """Input para inferencia."""
    inference_type = String(default_value="forward_chaining")
    rules_to_apply = List(String)
    max_depth = Int(default_value=10)


class InferenceRuleInput(graphene.InputObjectType):
    """Input para regla de inferencia."""
    rule_id = String(required=True)
    name = String(required=True)
    description = String(required=True)
    sparql_query = String(required=True)
    priority = Int(default_value=0)


# Mutations
class CreateTriple(Mutation):
    """Mutation para crear triple."""
    class Arguments:
        triple = TripleInput(required=True)

    success = Boolean(required=True)
    message = String(required=True)
    triple = Field(TripleType)

    async def mutate(self, info, triple):
        # Obtener user_id del contexto (de autenticación)
        user_id = getattr(info.context, 'user_id', None)
        if not user_id:
            raise Exception("Autenticación requerida")

        try:
            kg_core = get_knowledge_graph_core()
            kg_triple = Triple(triple.subject, triple.predicate, triple.object)
            success = await kg_core.add_triple(kg_triple, user_id)

            if success:
                return CreateTriple(
                    success=True,
                    message="Triple creado exitosamente",
                    triple=TripleType(
                        subject=triple.subject,
                        predicate=triple.predicate,
                        object=triple.object
                    )
                )
            else:
                return CreateTriple(
                    success=False,
                    message="Error al crear triple",
                    triple=None
                )

        except Exception as e:
            logger.error(f"Error creating triple: {e}")
            return CreateTriple(
                success=False,
                message=str(e),
                triple=None
            )


class DeleteTriple(Mutation):
    """Mutation para eliminar triple."""
    class Arguments:
        triple = TripleInput(required=True)

    success = Boolean(required=True)
    message = String(required=True)

    async def mutate(self, info, triple):
        user_id = getattr(info.context, 'user_id', None)
        if not user_id:
            raise Exception("Autenticación requerida")

        try:
            kg_core = get_knowledge_graph_core()
            kg_triple = Triple(triple.subject, triple.predicate, triple.object)
            success = await kg_core.remove_triple(kg_triple, user_id)

            return DeleteTriple(
                success=success,
                message="Triple eliminado exitosamente" if success else "Triple no encontrado"
            )

        except Exception as e:
            logger.error(f"Error deleting triple: {e}")
            return DeleteTriple(
                success=False,
                message=str(e)
            )


class BulkCreateTriples(Mutation):
    """Mutation para crear múltiples triples."""
    class Arguments:
        triples = List(TripleInput, required=True)

    success = Boolean(required=True)
    message = String(required=True)
    success_count = Int(required=True)
    total_count = Int(required=True)

    async def mutate(self, info, triples):
        user_id = getattr(info.context, 'user_id', None)
        if not user_id:
            raise Exception("Autenticación requerida")

        try:
            kg_core = get_knowledge_graph_core()
            success_count = 0

            for triple_data in triples:
                kg_triple = Triple(triple_data.subject, triple_data.predicate, triple_data.object)
                if await kg_core.add_triple(kg_triple, user_id):
                    success_count += 1

            return BulkCreateTriples(
                success=success_count > 0,
                message=f"Creados {success_count}/{len(triples)} triples",
                success_count=success_count,
                total_count=len(triples)
            )

        except Exception as e:
            logger.error(f"Error in bulk create: {e}")
            return BulkCreateTriples(
                success=False,
                message=str(e),
                success_count=0,
                total_count=len(triples)
            )


class ExecuteQuery(Mutation):
    """Mutation para ejecutar consulta."""
    class Arguments:
        query_input = QueryInput(required=True)

    result = Field(QueryResultType)

    async def mutate(self, info, query_input):
        user_id = getattr(info.context, 'user_id', None)

        try:
            query_executor = get_query_executor()
            result = await query_executor.execute_query(
                query_input.query,
                parameters=query_input.parameters or {},
                user_id=user_id,
                optimize=query_input.optimize,
                use_cache=query_input.use_cache
            )

            return ExecuteQuery(
                result=QueryResultType(
                    query=result.query,
                    results=[
                        TripleType(subject=r.subject, predicate=r.predicate, object=r.object)
                        for r in result.results
                    ],
                    execution_time_ms=result.execution_time_ms,
                    result_count=len(result.results),
                    error=result.error
                )
            )

        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return ExecuteQuery(
                result=QueryResultType(
                    query=query_input.query,
                    results=[],
                    execution_time_ms=0,
                    result_count=0,
                    error=str(e)
                )
            )


class RunInference(Mutation):
    """Mutation para ejecutar inferencia."""
    class Arguments:
        inference_input = InferenceInput(required=True)

    result = Field(InferenceResultType)

    async def mutate(self, info, inference_input):
        user_id = getattr(info.context, 'user_id', None)
        if not user_id:
            raise Exception("Autenticación requerida")

        try:
            inference_engine = get_inference_engine()

            # Convertir string a enum
            inference_type = InferenceType(inference_input.inference_type)

            result = await inference_engine.infer(
                inference_type=inference_type,
                rules_to_apply=inference_input.rules_to_apply,
                max_depth=inference_input.max_depth,
                user_id=user_id
            )

            return RunInference(
                result=InferenceResultType(
                    inferred_triples=[
                        TripleType(subject=t.subject, predicate=t.predicate, object=t.object)
                        for t in result.inferred_triples
                    ],
                    rules_applied=result.rules_applied,
                    execution_time_ms=result.execution_time_ms,
                    explanation=result.explanation,
                    confidence_score=result.confidence_score
                )
            )

        except Exception as e:
            logger.error(f"Error running inference: {e}")
            return RunInference(
                result=InferenceResultType(
                    inferred_triples=[],
                    rules_applied=[],
                    execution_time_ms=0,
                    explanation=[str(e)],
                    confidence_score=0.0
                )
            )


class AddInferenceRule(Mutation):
    """Mutation para agregar regla de inferencia."""
    class Arguments:
        rule_input = InferenceRuleInput(required=True)

    success = Boolean(required=True)
    message = String(required=True)
    rule = Field(InferenceRuleType)

    async def mutate(self, info, rule_input):
        user_id = getattr(info.context, 'user_id', None)
        if not user_id:
            raise Exception("Autenticación requerida")

        try:
            inference_engine = get_inference_engine()
            success = await inference_engine.add_custom_rule(
                rule_id=rule_input.rule_id,
                name=rule_input.name,
                description=rule_input.description,
                sparql_query=rule_input.sparql_query,
                priority=rule_input.priority,
                user_id=user_id
            )

            if success:
                rules = inference_engine.get_inference_rules()
                rule_data = rules.get(rule_input.rule_id)
                if rule_data:
                    return AddInferenceRule(
                        success=True,
                        message="Regla agregada exitosamente",
                        rule=InferenceRuleType(**rule_data)
                    )

            return AddInferenceRule(
                success=False,
                message="Error al agregar regla",
                rule=None
            )

        except Exception as e:
            logger.error(f"Error adding inference rule: {e}")
            return AddInferenceRule(
                success=False,
                message=str(e),
                rule=None
            )


class ClearGraph(Mutation):
    """Mutation para limpiar el grafo."""
    success = Boolean(required=True)
    message = String(required=True)

    async def mutate(self, info):
        user_id = getattr(info.context, 'user_id', None)
        if not user_id:
            raise Exception("Autenticación requerida")

        try:
            kg_core = get_knowledge_graph_core()
            success = await kg_core.clear(user_id)

            return ClearGraph(
                success=success,
                message="Grafo limpiado exitosamente" if success else "Error al limpiar grafo"
            )

        except Exception as e:
            logger.error(f"Error clearing graph: {e}")
            return ClearGraph(
                success=False,
                message=str(e)
            )


# Queries
class Query(ObjectType):
    """Queries GraphQL principales."""

    # Consultas de triples
    triples = Field(
        List(TripleType),
        subject=String(),
        predicate=String(),
        object=graphene.types.json.JSONString(),
        limit=Int(default_value=100)
    )

    async def resolve_triples(self, info, subject=None, predicate=None, object=None, limit=100):
        """Resolver consulta de triples."""
        try:
            kg_core = get_knowledge_graph_core()
            user_id = getattr(info.context, 'user_id', None)

            # Construir query SPARQL simple
            query_parts = []
            if subject:
                query_parts.append(f"?s = <{subject}>")
            if predicate:
                query_parts.append(f"?p = <{predicate}>")
            if object is not None:
                if isinstance(object, str):
                    query_parts.append(f"?o = '{object}'")
                else:
                    query_parts.append(f"?o = {object}")

            where_clause = " . ".join(query_parts) if query_parts else "true"
            sparql_query = f"SELECT ?s ?p ?o WHERE {{ {where_clause} }} LIMIT {limit}"

            results = await kg_core.query(sparql_query, user_id)

            return [
                TripleType(subject=r.subject, predicate=r.predicate, object=r.object)
                for r in results
            ]

        except Exception as e:
            logger.error(f"Error resolving triples: {e}")
            return []

    # Estadísticas del grafo
    graph_stats = Field(GraphStatsType)

    async def resolve_graph_stats(self, info):
        """Resolver estadísticas del grafo."""
        try:
            kg_core = get_knowledge_graph_core()
            stats = await kg_core.get_stats()

            return GraphStatsType(
                total_triples=stats.get('total_triples', 0),
                unique_subjects=stats.get('unique_subjects', 0),
                unique_predicates=stats.get('unique_predicates', 0),
                backend_type=stats.get('backend_type', 'unknown'),
                storage_health=stats.get('storage_health', {})
            )

        except Exception as e:
            logger.error(f"Error resolving graph stats: {e}")
            return GraphStatsType(
                total_triples=0,
                unique_subjects=0,
                unique_predicates=0,
                backend_type='error',
                storage_health={'error': str(e)}
            )

    # Reglas de inferencia
    inference_rules = Field(List(InferenceRuleType))

    def resolve_inference_rules(self, info):
        """Resolver reglas de inferencia."""
        try:
            inference_engine = get_inference_engine()
            rules = inference_engine.get_inference_rules()

            return [
                InferenceRuleType(**rule_data)
                for rule_data in rules.values()
            ]

        except Exception as e:
            logger.error(f"Error resolving inference rules: {e}")
            return []

    # Estado de salud
    health_status = Field(List(HealthStatusType))

    async def resolve_health_status(self, info):
        """Resolver estado de salud de servicios."""
        try:
            # Simular verificación de salud básica
            services = [
                {
                    'service_name': 'knowledge_graph_core',
                    'status': 'healthy',
                    'last_check': datetime.now(),
                    'uptime_seconds': 3600
                },
                {
                    'service_name': 'query_executor',
                    'status': 'healthy',
                    'last_check': datetime.now(),
                    'uptime_seconds': 3600
                },
                {
                    'service_name': 'inference_engine',
                    'status': 'healthy',
                    'last_check': datetime.now(),
                    'uptime_seconds': 3600
                }
            ]

            return [
                HealthStatusType(**service)
                for service in services
            ]

        except Exception as e:
            logger.error(f"Error resolving health status: {e}")
            return []


# Schema principal
class Mutation(ObjectType):
    """Mutations GraphQL."""
    create_triple = CreateTriple.Field()
    delete_triple = DeleteTriple.Field()
    bulk_create_triples = BulkCreateTriples.Field()
    execute_query = ExecuteQuery.Field()
    run_inference = RunInference.Field()
    add_inference_rule = AddInferenceRule.Field()
    clear_graph = ClearGraph.Field()


# API GraphQL principal
class KnowledgeGraphGraphQLAPI:
    """
    API GraphQL completa para el grafo de conocimiento.
    Incluye schema completo con queries y mutations.
    """

    def __init__(self):
        self.schema = graphene.Schema(query=Query, mutation=Mutation)

        # Componentes del sistema
        self.kg_core = get_knowledge_graph_core()
        self.query_executor = get_query_executor()
        self.inference_engine = get_inference_engine()
        self.audit_manager = get_audit_manager()
        self.metrics_collector = get_metrics_collector()

    def get_schema(self):
        """Obtener schema GraphQL."""
        return self.schema

    async def execute_query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ejecutar query GraphQL.

        Args:
            query: Query GraphQL
            variables: Variables de la query
            context: Contexto de ejecución (incluye user_id, etc.)

        Returns:
            Resultado de la ejecución
        """
        try:
            # Preparar contexto
            context_value = context or {}
            context_value.update({
                'kg_core': self.kg_core,
                'query_executor': self.query_executor,
                'inference_engine': self.inference_engine,
                'audit_manager': self.audit_manager,
                'metrics_collector': self.metrics_collector
            })

            # Ejecutar query
            result = await self.schema.execute_async(
                query,
                variable_values=variables,
                context_value=context_value
            )

            # Log de auditoría
            user_id = context_value.get('user_id')
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph_graphql",
                action="execute_query",
                user_id=user_id,
                details={
                    "query_length": len(query),
                    "has_errors": bool(result.errors),
                    "error_count": len(result.errors) if result.errors else 0
                },
                success=not bool(result.errors)
            )

            # Métricas
            self.metrics_collector.record_request("graphql.execute_query")

            if result.errors:
                logger.error(f"GraphQL execution errors: {result.errors}")
                self.metrics_collector.record_error("graphql.execute_query", "graphql_error")

            return {
                "data": result.data,
                "errors": [str(error) for error in result.errors] if result.errors else None
            }

        except Exception as e:
            logger.error(f"Error executing GraphQL query: {e}")

            # Log de error
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph_graphql",
                action="execute_query",
                user_id=context.get('user_id') if context else None,
                details={"error": str(e)},
                success=False
            )

            self.metrics_collector.record_error("graphql.execute_query", "execution_error")

            return {
                "data": None,
                "errors": [str(e)]
            }

    def get_introspection_query(self) -> str:
        """Obtener query de introspección para documentación."""
        return """
        query IntrospectionQuery {
          __schema {
            queryType { name }
            mutationType { name }
            subscriptionType { name }
            types {
              ...FullType
            }
            directives {
              name
              description
              locations
              args {
                ...InputValue
              }
            }
          }
        }

        fragment FullType on __Type {
          kind
          name
          description
          fields(includeDeprecated: true) {
            name
            description
            args {
              ...InputValue
            }
            type {
              ...TypeRef
            }
            isDeprecated
            deprecationReason
          }
          inputFields {
            ...InputValue
          }
          interfaces {
            ...TypeRef
          }
          enumValues(includeDeprecated: true) {
            name
            description
            isDeprecated
            deprecationReason
          }
          possibleTypes {
            ...TypeRef
          }
        }

        fragment InputValue on __InputValue {
          name
          description
          type { ...TypeRef }
          defaultValue
        }

        fragment TypeRef on __Type {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
                ofType {
                  kind
                  name
                  ofType {
                    kind
                    name
                    ofType {
                      kind
                      name
                      ofType {
                        kind
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """

    def get_schema_sdl(self) -> str:
        """Obtener SDL (Schema Definition Language) del schema."""
        try:
            return graphene.utilities.print_schema(self.schema)
        except Exception as e:
            logger.error(f"Error generating schema SDL: {e}")
            return ""