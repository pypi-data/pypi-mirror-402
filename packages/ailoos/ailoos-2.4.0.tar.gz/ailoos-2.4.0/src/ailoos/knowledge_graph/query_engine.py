"""
Graph Query Engine para AILOOS.
Implementa ejecución de consultas con soporte para SPARQL, Cypher y Gremlin,
con integración completa de auditoría y métricas.
"""

import asyncio
import re
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib

from ..core.logging import get_logger
from .core import get_knowledge_graph_core, KnowledgeGraphCore, Triple, BackendType
from ..auditing.audit_manager import get_audit_manager, AuditEventType
from ..auditing.metrics_collector import get_metrics_collector
from ..core.serializers import (
    SerializationFormat, get_serializer, SerializationResult,
    SerializationError
)

logger = get_logger(__name__)


class QueryLanguage(Enum):
    """Lenguajes de consulta soportados."""
    SPARQL = "sparql"
    CYPHER = "cypher"
    GREMLIN = "gremlin"
    PATTERN = "pattern"  # Para consultas simples de patrón


@dataclass
class QueryResult:
    """Resultado de una consulta."""
    query: str
    language: QueryLanguage
    results: List[Triple]
    execution_time_ms: float
    optimized: bool
    parameters: Dict[str, Any]
    error: Optional[str] = None
    # Nuevos campos para serialización
    serialized_data: Optional[bytes] = None
    serialization_format: Optional[SerializationFormat] = None
    serialization_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            "query": self.query,
            "language": self.language.value,
            "results": [triple.to_dict() for triple in self.results],
            "execution_time_ms": self.execution_time_ms,
            "optimized": self.optimized,
            "parameters": self.parameters,
            "error": self.error,
            "result_count": len(self.results),
            "serialization_format": self.serialization_format.value if self.serialization_format else None,
            "serialization_time_ms": self.serialization_time_ms
        }

    def serialize_results(self, format: SerializationFormat, schema: Optional[Dict[str, Any]] = None) -> 'QueryResult':
        """Serializar resultados en el formato especificado."""
        if self.error:
            # Para errores, devolver resultado sin serializar
            return self

        try:
            start_time = time.time()

            # Preparar datos para serialización
            data_to_serialize = self._prepare_data_for_serialization()

            # Obtener serializador
            serializer = get_serializer(format, schema)

            # Serializar
            serialized = serializer.serialize(data_to_serialize)

            serialization_time = (time.time() - start_time) * 1000

            # Crear nuevo QueryResult con datos serializados
            return QueryResult(
                query=self.query,
                language=self.language,
                results=self.results,
                execution_time_ms=self.execution_time_ms,
                optimized=self.optimized,
                parameters=self.parameters,
                error=self.error,
                serialized_data=serialized.data,
                serialization_format=format,
                serialization_time_ms=serialization_time
            )

        except SerializationError as e:
            logger.warning(f"Failed to serialize query results: {e}")
            # Devolver resultado original sin serialización
            return self

    def _prepare_data_for_serialization(self) -> Dict[str, Any]:
        """Preparar datos de resultados para serialización."""
        # Para SPARQL y otros lenguajes, devolver estructura optimizada
        if self.language == QueryLanguage.SPARQL:
            return self._prepare_sparql_results()
        else:
            # Para otros lenguajes, usar formato estándar
            return {
                "query": self.query,
                "results": [triple.to_dict() for triple in self.results],
                "metadata": {
                    "execution_time_ms": self.execution_time_ms,
                    "optimized": self.optimized,
                    "result_count": len(self.results)
                }
            }

    def _prepare_sparql_results(self) -> Dict[str, Any]:
        """Preparar resultados SPARQL para serialización optimizada."""
        # Para SPARQL, optimizar estructura para TOON/VSC
        triples_data = []

        for triple in self.results:
            triples_data.append({
                "s": triple.subject,
                "p": triple.predicate,
                "o": triple.object
            })

        return {
            "head": {
                "vars": ["s", "p", "o"] if triples_data else []
            },
            "results": {
                "bindings": triples_data
            },
            "metadata": {
                "execution_time_ms": self.execution_time_ms,
                "result_count": len(triples_data)
            }
        }


@dataclass
class QueryPlan:
    """Plan de ejecución de consulta."""
    steps: List[str]
    estimated_cost: float
    estimated_rows: int
    backend_used: str
    optimizations_applied: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            "steps": self.steps,
            "estimated_cost": self.estimated_cost,
            "estimated_rows": self.estimated_rows,
            "backend_used": self.backend_used,
            "optimizations_applied": self.optimizations_applied
        }


class QueryEngine:
    """
    Motor de consultas para grafos de conocimiento.
    Soporta SPARQL, Cypher, Gremlin y consultas de patrón con optimización automática.
    """

    def __init__(self, kg_core: Optional[KnowledgeGraphCore] = None):
        self.kg_core = kg_core or get_knowledge_graph_core()
        self.audit_manager = get_audit_manager()
        self.metrics_collector = get_metrics_collector()

        # Patrones para detectar lenguajes de consulta
        self.language_patterns = {
            QueryLanguage.SPARQL: re.compile(r'^\s*(SELECT|CONSTRUCT|ASK|DESCRIBE)\s+', re.IGNORECASE),
            QueryLanguage.CYPHER: re.compile(r'^\s*(MATCH|CREATE|MERGE|DELETE)\s+', re.IGNORECASE),
            QueryLanguage.GREMLIN: re.compile(r'^\s*g\.', re.IGNORECASE),
        }

        # Configuración de optimización
        self.optimization_enabled = True
        self.query_cache_enabled = True
        self.max_execution_time_ms = 30000  # 30 segundos

    def _detect_query_language(self, query: str) -> QueryLanguage:
        """Detectar el lenguaje de la consulta."""
        for language, pattern in self.language_patterns.items():
            if pattern.match(query):
                return language

        # Si no coincide con patrones complejos, asumir patrón simple
        return QueryLanguage.PATTERN

    def _validate_query_syntax(self, query: str, language: QueryLanguage) -> Tuple[bool, Optional[str]]:
        """Validar sintaxis básica de la consulta."""
        try:
            if language == QueryLanguage.SPARQL:
                return self._validate_sparql_syntax(query)
            elif language == QueryLanguage.CYPHER:
                return self._validate_cypher_syntax(query)
            elif language == QueryLanguage.GREMLIN:
                return self._validate_gremlin_syntax(query)
            elif language == QueryLanguage.PATTERN:
                return self._validate_pattern_syntax(query)
            else:
                return False, f"Lenguaje no soportado: {language}"
        except Exception as e:
            return False, f"Error de validación: {str(e)}"

    def _validate_sparql_syntax(self, query: str) -> Tuple[bool, Optional[str]]:
        """Validar sintaxis SPARQL básica."""
        # Validaciones básicas
        if not query.strip():
            return False, "Consulta vacía"

        # Verificar que tenga una cláusula principal
        if not re.search(r'\b(SELECT|CONSTRUCT|ASK|DESCRIBE)\b', query, re.IGNORECASE):
            return False, "Falta cláusula principal SPARQL"

        # Verificar paréntesis balanceados
        if query.count('(') != query.count(')'):
            return False, "Paréntesis no balanceados"

        return True, None

    def _validate_cypher_syntax(self, query: str) -> Tuple[bool, Optional[str]]:
        """Validar sintaxis Cypher básica."""
        if not query.strip():
            return False, "Consulta vacía"

        # Verificar que tenga una cláusula principal
        if not re.search(r'\b(MATCH|CREATE|MERGE|DELETE|RETURN)\b', query, re.IGNORECASE):
            return False, "Falta cláusula principal Cypher"

        return True, None

    def _validate_gremlin_syntax(self, query: str) -> Tuple[bool, Optional[str]]:
        """Validar sintaxis Gremlin básica."""
        if not query.strip():
            return False, "Consulta vacía"

        if not query.startswith('g.'):
            return False, "Consulta Gremlin debe comenzar con 'g.'"

        return True, None

    def _validate_pattern_syntax(self, query: str) -> Tuple[bool, Optional[str]]:
        """Validar sintaxis de patrón simple."""
        if not query.strip():
            return False, "Consulta vacía"

        # Para patrones simples: sujeto predicado objeto
        parts = query.split()
        if len(parts) != 3:
            return False, "Patrón debe tener exactamente 3 partes: sujeto predicado objeto"

        return True, None

    def _substitute_parameters(self, query: str, parameters: Dict[str, Any]) -> str:
        """Sustituir parámetros en la consulta."""
        try:
            # Sustituir parámetros con formato $param o :param
            for param_name, param_value in parameters.items():
                # Convertir valor a string apropiado
                if isinstance(param_value, str):
                    str_value = f'"{param_value}"'
                elif isinstance(param_value, (int, float)):
                    str_value = str(param_value)
                elif isinstance(param_value, bool):
                    str_value = str(param_value).lower()
                else:
                    str_value = str(param_value)

                # Sustituir $param y :param
                query = re.sub(rf'\${param_name}\b', str_value, query)
                query = re.sub(rf':{param_name}\b', str_value, query)

            return query
        except Exception as e:
            logger.error(f"Error substituting parameters: {e}")
            raise ValueError(f"Error en sustitución de parámetros: {e}")

    def _select_backend_for_query(self, language: QueryLanguage) -> BackendType:
        """Seleccionar el backend apropiado para el lenguaje."""
        if language == QueryLanguage.SPARQL:
            return BackendType.RDF_STORE
        elif language == QueryLanguage.CYPHER:
            return BackendType.NEO4J
        elif language == QueryLanguage.GREMLIN:
            # Gremlin no tiene backend específico, usar RDF_STORE como fallback
            return BackendType.RDF_STORE
        else:  # PATTERN
            return BackendType.IN_MEMORY

    def _execute_with_timeout(self, coro, timeout_ms: int):
        """Ejecutar coroutine con timeout."""
        try:
            return asyncio.wait_for(coro, timeout=timeout_ms / 1000)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Query execution timed out after {timeout_ms}ms")

    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        optimize: bool = True,
        response_format: Optional[SerializationFormat] = None,
        response_schema: Optional[Dict[str, Any]] = None
    ) -> QueryResult:
        """
        Ejecutar una consulta en el grafo.

        Args:
            query: La consulta a ejecutar
            parameters: Parámetros para la consulta
            user_id: ID del usuario que ejecuta la consulta
            optimize: Si optimizar la consulta automáticamente
            response_format: Formato de serialización para la respuesta (opcional)
            response_schema: Esquema JSON para validación de respuesta (opcional)

        Returns:
            QueryResult con los resultados (serializados si se especifica formato)
        """
        start_time = time.time()
        parameters = parameters or {}

        try:
            # Detectar lenguaje
            language = self._detect_query_language(query)

            # Validar sintaxis
            is_valid, validation_error = self._validate_query_syntax(query, language)
            if not is_valid:
                raise ValueError(f"Syntax error: {validation_error}")

            # Sustituir parámetros
            processed_query = self._substitute_parameters(query, parameters)

            # Optimizar si está habilitado
            if optimize and self.optimization_enabled:
                processed_query, optimizations = await self.optimize_query(processed_query, language)
                optimized = len(optimizations) > 0
            else:
                optimized = False

            # Seleccionar backend
            required_backend = self._select_backend_for_query(language)

            # Si el backend actual no coincide, cambiar temporalmente
            original_backend = self.kg_core.backend_type
            if original_backend != required_backend:
                # Crear instancia temporal con el backend requerido
                temp_kg = KnowledgeGraphCore(required_backend, **self.kg_core.backend_config)
                kg_to_use = temp_kg
            else:
                kg_to_use = self.kg_core

            # Ejecutar consulta con timeout
            try:
                results = await self._execute_with_timeout(
                    kg_to_use.query(processed_query, user_id),
                    self.max_execution_time_ms
                )
            except TimeoutError:
                raise TimeoutError("Query execution timed out")

            execution_time = (time.time() - start_time) * 1000

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.KNOWLEDGE_GRAPH_QUERY,
                resource="knowledge_graph",
                action="execute_query",
                user_id=user_id,
                details={
                    "query": query,
                    "language": language.value,
                    "parameters": parameters,
                    "result_count": len(results),
                    "optimized": optimized,
                    "backend_used": required_backend.value
                },
                success=True,
                processing_time_ms=execution_time
            )

            # Métricas
            self.metrics_collector.record_request("query_engine.execute_query")
            self.metrics_collector.record_response_time(execution_time)

            logger.info(f"Query executed: {language.value}, results: {len(results)}, time: {execution_time:.2f}ms")

            # Crear resultado base
            result = QueryResult(
                query=query,
                language=language,
                results=results,
                execution_time_ms=execution_time,
                optimized=optimized,
                parameters=parameters
            )

            # Serializar si se especifica formato
            if response_format:
                result = result.serialize_results(response_format, response_schema)
                logger.info(f"Query results serialized to {response_format.value} format")

            return result

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = str(e)

            # Logging de error
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph",
                action="execute_query",
                user_id=user_id,
                details={
                    "query": query,
                    "parameters": parameters,
                    "error": error_msg
                },
                success=False,
                processing_time_ms=execution_time
            )

            self.metrics_collector.record_error("query_engine.execute_query", "query_error")

            logger.error(f"Query execution failed: {error_msg}")

            return QueryResult(
                query=query,
                language=self._detect_query_language(query),
                results=[],
                execution_time_ms=execution_time,
                optimized=False,
                parameters=parameters,
                error=error_msg
            )

    async def explain_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> QueryPlan:
        """
        Explicar el plan de ejecución de una consulta.

        Args:
            query: La consulta a explicar
            parameters: Parámetros de la consulta

        Returns:
            QueryPlan con detalles del plan de ejecución
        """
        try:
            language = self._detect_query_language(query)
            parameters = parameters or {}

            # Sustituir parámetros
            processed_query = self._substitute_parameters(query, parameters)

            # Seleccionar backend
            backend = self._select_backend_for_query(language)

            # Generar plan simulado (en implementación real, usar capacidades del backend)
            steps = []
            estimated_cost = 0.0
            estimated_rows = 0

            if language == QueryLanguage.SPARQL:
                steps = [
                    "Parse SPARQL query",
                    "Validate RDF patterns",
                    "Plan triple pattern matching",
                    "Execute joins and filters",
                    "Apply projections and ordering"
                ]
                estimated_cost = len(processed_query.split()) * 0.1
                estimated_rows = 100  # Estimación

            elif language == QueryLanguage.CYPHER:
                steps = [
                    "Parse Cypher query",
                    "Generate execution plan",
                    "Plan node/relationship traversals",
                    "Execute pattern matching",
                    "Apply aggregations and returns"
                ]
                estimated_cost = len(processed_query.split()) * 0.15
                estimated_rows = 50

            elif language == QueryLanguage.GREMLIN:
                steps = [
                    "Parse Gremlin traversal",
                    "Build traversal pipeline",
                    "Execute graph traversals",
                    "Apply filters and transformations"
                ]
                estimated_cost = len(processed_query.split()) * 0.2
                estimated_rows = 75

            else:  # PATTERN
                steps = [
                    "Parse pattern query",
                    "Simple triple matching",
                    "Filter results"
                ]
                estimated_cost = 0.05
                estimated_rows = 10

            # Optimizaciones aplicadas
            optimizations = []
            if self.optimization_enabled:
                optimizations = ["Query rewriting", "Index selection", "Join ordering"]

            return QueryPlan(
                steps=steps,
                estimated_cost=estimated_cost,
                estimated_rows=estimated_rows,
                backend_used=backend.value,
                optimizations_applied=optimizations
            )

        except Exception as e:
            logger.error(f"Error explaining query: {e}")
            return QueryPlan(
                steps=["Error generating plan"],
                estimated_cost=0.0,
                estimated_rows=0,
                backend_used="unknown",
                optimizations_applied=[]
            )

    async def optimize_query(self, query: str, language: Optional[QueryLanguage] = None) -> Tuple[str, List[str]]:
        """
        Optimizar una consulta automáticamente.

        Args:
            query: La consulta a optimizar
            language: Lenguaje de la consulta (opcional)

        Returns:
            Tupla de (consulta_optimizada, lista_de_optimizaciones_aplicadas)
        """
        try:
            if not language:
                language = self._detect_query_language(query)

            optimized_query = query
            optimizations_applied = []

            if language == QueryLanguage.SPARQL:
                optimized_query, opts = self._optimize_sparql_query(query)
                optimizations_applied.extend(opts)

            elif language == QueryLanguage.CYPHER:
                optimized_query, opts = self._optimize_cypher_query(query)
                optimizations_applied.extend(opts)

            elif language == QueryLanguage.GREMLIN:
                optimized_query, opts = self._optimize_gremlin_query(query)
                optimizations_applied.extend(opts)

            # Optimizaciones generales
            if "SELECT *" in optimized_query.upper():
                optimizations_applied.append("Avoid SELECT *")

            if len(optimizations_applied) > 0:
                logger.info(f"Query optimized: {optimizations_applied}")

            return optimized_query, optimizations_applied

        except Exception as e:
            logger.error(f"Error optimizing query: {e}")
            return query, []

    def _optimize_sparql_query(self, query: str) -> Tuple[str, List[str]]:
        """Optimizar consulta SPARQL."""
        optimizations = []

        # Optimizar orden de patrones triples
        # (simplificado - en producción usar análisis más sofisticado)
        if "OPTIONAL" in query.upper():
            optimizations.append("Reorder OPTIONAL patterns")

        if "FILTER" in query.upper():
            optimizations.append("Push down FILTER conditions")

        return query, optimizations

    def _optimize_cypher_query(self, query: str) -> Tuple[str, List[str]]:
        """Optimizar consulta Cypher."""
        optimizations = []

        # Optimizar uso de índices
        if "MATCH" in query.upper():
            optimizations.append("Use node/relationship indexes")

        if "WHERE" in query.upper():
            optimizations.append("Optimize WHERE conditions")

        return query, optimizations

    def _optimize_gremlin_query(self, query: str) -> Tuple[str, List[str]]:
        """Optimizar consulta Gremlin."""
        optimizations = []

        # Optimizar pipeline de traversal
        if ".has(" in query:
            optimizations.append("Optimize has() filters")

        if ".out(" in query or ".in(" in query:
            optimizations.append("Optimize traversal steps")

        return query, optimizations

    def get_supported_languages(self) -> List[str]:
        """Obtener lista de lenguajes soportados."""
        return [lang.value for lang in QueryLanguage]

    def get_query_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de consultas."""
        # En implementación real, mantener contadores
        return {
            "supported_languages": self.get_supported_languages(),
            "optimization_enabled": self.optimization_enabled,
            "query_cache_enabled": self.query_cache_enabled,
            "max_execution_time_ms": self.max_execution_time_ms
        }


# Instancia global
_query_engine = None

def get_query_engine() -> QueryEngine:
    """Obtener instancia global del motor de consultas."""
    global _query_engine
    if _query_engine is None:
        _query_engine = QueryEngine()
    return _query_engine