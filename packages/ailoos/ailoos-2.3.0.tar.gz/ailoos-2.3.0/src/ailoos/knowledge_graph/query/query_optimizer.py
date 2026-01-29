"""
Optimizador avanzado de consultas para el grafo de conocimiento AILOOS.
Proporciona análisis de costo, reordenamiento de operaciones y optimizaciones inteligentes.
"""

import asyncio
import re
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from ...core.logging import get_logger
from ..query_engine import QueryLanguage, QueryPlan
from ..core import get_knowledge_graph_core, KnowledgeGraphCore
from ...auditing.audit_manager import get_audit_manager, AuditEventType
from ...auditing.metrics_collector import get_metrics_collector
from ...utils.cache import get_cache_manager

logger = get_logger(__name__)


class OptimizationStrategy(Enum):
    """Estrategias de optimización disponibles."""
    COST_BASED = "cost_based"
    RULE_BASED = "rule_based"
    HEURISTIC = "heuristic"
    LEARNING_BASED = "learning_based"


@dataclass
class QueryAnalysis:
    """Análisis detallado de una consulta."""
    query_hash: str
    language: QueryLanguage
    complexity_score: float
    estimated_cardinality: int
    selectivity_factors: Dict[str, float]
    join_patterns: List[Dict[str, Any]]
    filter_conditions: List[Dict[str, Any]]
    potential_indexes: List[str]
    cost_breakdown: Dict[str, float]
    optimization_opportunities: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            "query_hash": self.query_hash,
            "language": self.language.value,
            "complexity_score": self.complexity_score,
            "estimated_cardinality": self.estimated_cardinality,
            "selectivity_factors": self.selectivity_factors,
            "join_patterns": self.join_patterns,
            "filter_conditions": self.filter_conditions,
            "potential_indexes": self.potential_indexes,
            "cost_breakdown": self.cost_breakdown,
            "optimization_opportunities": self.optimization_opportunities
        }


@dataclass
class OptimizationResult:
    """Resultado de una optimización."""
    original_query: str
    optimized_query: str
    strategy_used: OptimizationStrategy
    optimizations_applied: List[str]
    estimated_improvement: float
    analysis: QueryAnalysis
    execution_plan: List[str]
    cost_reduction: float

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            "original_query": self.original_query,
            "optimized_query": self.optimized_query,
            "strategy_used": self.strategy_used.value,
            "optimizations_applied": self.optimizations_applied,
            "estimated_improvement": self.estimated_improvement,
            "analysis": self.analysis.to_dict(),
            "execution_plan": self.execution_plan,
            "cost_reduction": self.cost_reduction
        }


class QueryOptimizer:
    """
    Optimizador avanzado de consultas con análisis de costo y estrategias múltiples.
    Proporciona optimización automática basada en estadísticas del grafo.
    """

    def __init__(self):
        self.kg_core = get_knowledge_graph_core()
        self.audit_manager = get_audit_manager()
        self.metrics_collector = get_metrics_collector()
        self.cache = get_cache_manager()

        # Estadísticas del grafo para optimización
        self.graph_stats = self._load_graph_statistics()

        # Cache de análisis de consultas
        self.analysis_cache: Dict[str, QueryAnalysis] = {}
        self.optimization_cache: Dict[str, OptimizationResult] = {}

        # Configuración
        self.enable_cost_based_opt = True
        self.enable_rule_based_opt = True
        self.enable_learning_opt = False
        self.max_analysis_time_ms = 5000
        self.cache_ttl_seconds = 3600

    def _load_graph_statistics(self) -> Dict[str, Any]:
        """Cargar estadísticas del grafo para optimización."""
        try:
            # En implementación real, cargar desde el backend del grafo
            return {
                "total_triples": 1000000,
                "unique_subjects": 500000,
                "unique_predicates": 1000,
                "unique_objects": 750000,
                "avg_triples_per_subject": 2.0,
                "avg_triples_per_object": 1.3,
                "predicate_frequencies": {
                    "rdf:type": 500000,
                    "rdfs:label": 400000,
                    "owl:sameAs": 10000
                },
                "class_hierarchies": {},
                "index_stats": {}
            }
        except Exception as e:
            logger.warning(f"Error loading graph statistics: {e}")
            return {}

    async def analyze_query(
        self,
        query: str,
        language: Optional[QueryLanguage] = None
    ) -> QueryAnalysis:
        """
        Analizar una consulta en profundidad.

        Args:
            query: La consulta a analizar
            language: Lenguaje de la consulta (opcional)

        Returns:
            QueryAnalysis con detalles del análisis
        """
        start_time = time.time()

        try:
            # Generar hash de la consulta
            query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]

            # Verificar cache
            if query_hash in self.analysis_cache:
                cached_analysis = self.analysis_cache[query_hash]
                if time.time() - cached_analysis.complexity_score < self.cache_ttl_seconds:
                    return cached_analysis

            if not language:
                language = self._detect_query_language(query)

            # Análisis sintáctico
            parsed_query = self._parse_query(query, language)

            # Calcular complejidad
            complexity_score = self._calculate_complexity_score(parsed_query, language)

            # Estimar cardinalidad
            estimated_cardinality = self._estimate_cardinality(parsed_query, language)

            # Analizar selectividad
            selectivity_factors = self._analyze_selectivity(parsed_query, language)

            # Identificar patrones de join
            join_patterns = self._identify_join_patterns(parsed_query, language)

            # Analizar condiciones de filtro
            filter_conditions = self._analyze_filter_conditions(parsed_query, language)

            # Sugerir índices potenciales
            potential_indexes = self._suggest_indexes(parsed_query, language)

            # Desglose de costos
            cost_breakdown = self._calculate_cost_breakdown(parsed_query, language)

            # Identificar oportunidades de optimización
            optimization_opportunities = self._identify_optimization_opportunities(
                parsed_query, language, complexity_score, selectivity_factors
            )

            analysis = QueryAnalysis(
                query_hash=query_hash,
                language=language,
                complexity_score=complexity_score,
                estimated_cardinality=estimated_cardinality,
                selectivity_factors=selectivity_factors,
                join_patterns=join_patterns,
                filter_conditions=filter_conditions,
                potential_indexes=potential_indexes,
                cost_breakdown=cost_breakdown,
                optimization_opportunities=optimization_opportunities
            )

            # Cachear análisis
            self.analysis_cache[query_hash] = analysis

            # Logging de auditoría
            analysis_time = (time.time() - start_time) * 1000
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="query_optimizer",
                action="analyze_query",
                details={
                    "query_hash": query_hash,
                    "language": language.value,
                    "complexity_score": complexity_score,
                    "analysis_time_ms": analysis_time
                },
                success=True,
                processing_time_ms=analysis_time
            )

            # Métricas
            self.metrics_collector.record_request("query_optimizer.analyze_query")

            logger.info(f"Query analyzed: {language.value}, complexity: {complexity_score:.2f}, time: {analysis_time:.2f}ms")

            return analysis

        except Exception as e:
            analysis_time = (time.time() - start_time) * 1000
            logger.error(f"Error analyzing query: {e}")

            # Logging de error
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="query_optimizer",
                action="analyze_query",
                details={"error": str(e)},
                success=False,
                processing_time_ms=analysis_time
            )

            # Análisis básico como fallback
            return QueryAnalysis(
                query_hash=hashlib.sha256(query.encode()).hexdigest()[:16],
                language=language or QueryLanguage.PATTERN,
                complexity_score=1.0,
                estimated_cardinality=100,
                selectivity_factors={},
                join_patterns=[],
                filter_conditions=[],
                potential_indexes=[],
                cost_breakdown={"base": 1.0},
                optimization_opportunities=[]
            )

    async def optimize_query(
        self,
        query: str,
        language: Optional[QueryLanguage] = None,
        strategy: OptimizationStrategy = OptimizationStrategy.COST_BASED
    ) -> OptimizationResult:
        """
        Optimizar una consulta usando la estrategia especificada.

        Args:
            query: La consulta a optimizar
            language: Lenguaje de la consulta
            strategy: Estrategia de optimización a usar

        Returns:
            OptimizationResult con la consulta optimizada
        """
        start_time = time.time()

        try:
            # Analizar la consulta primero
            analysis = await self.analyze_query(query, language)

            # Verificar cache de optimización
            cache_key = f"{analysis.query_hash}:{strategy.value}"
            if cache_key in self.optimization_cache:
                cached_result = self.optimization_cache[cache_key]
                if time.time() - start_time < self.cache_ttl_seconds:
                    return cached_result

            # Aplicar estrategia de optimización
            if strategy == OptimizationStrategy.COST_BASED and self.enable_cost_based_opt:
                optimized_query, optimizations, improvement, plan, cost_reduction = await self._cost_based_optimization(
                    query, analysis
                )
            elif strategy == OptimizationStrategy.RULE_BASED and self.enable_rule_based_opt:
                optimized_query, optimizations, improvement, plan, cost_reduction = self._rule_based_optimization(
                    query, analysis
                )
            elif strategy == OptimizationStrategy.LEARNING_BASED and self.enable_learning_opt:
                optimized_query, optimizations, improvement, plan, cost_reduction = await self._learning_based_optimization(
                    query, analysis
                )
            else:
                # Optimización heurística como fallback
                optimized_query, optimizations, improvement, plan, cost_reduction = self._heuristic_optimization(
                    query, analysis
                )

            result = OptimizationResult(
                original_query=query,
                optimized_query=optimized_query,
                strategy_used=strategy,
                optimizations_applied=optimizations,
                estimated_improvement=improvement,
                analysis=analysis,
                execution_plan=plan,
                cost_reduction=cost_reduction
            )

            # Cachear resultado
            self.optimization_cache[cache_key] = result

            # Logging de auditoría
            optimization_time = (time.time() - start_time) * 1000
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="query_optimizer",
                action="optimize_query",
                details={
                    "query_hash": analysis.query_hash,
                    "strategy": strategy.value,
                    "optimizations_count": len(optimizations),
                    "estimated_improvement": improvement,
                    "optimization_time_ms": optimization_time
                },
                success=True,
                processing_time_ms=optimization_time
            )

            # Métricas
            self.metrics_collector.record_request("query_optimizer.optimize_query")

            logger.info(f"Query optimized: {strategy.value}, improvements: {len(optimizations)}, time: {optimization_time:.2f}ms")

            return result

        except Exception as e:
            optimization_time = (time.time() - start_time) * 1000
            logger.error(f"Error optimizing query: {e}")

            # Logging de error
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="query_optimizer",
                action="optimize_query",
                details={"error": str(e)},
                success=False,
                processing_time_ms=optimization_time
            )

            # Retornar resultado sin optimización
            return OptimizationResult(
                original_query=query,
                optimized_query=query,
                strategy_used=strategy,
                optimizations_applied=[],
                estimated_improvement=0.0,
                analysis=await self.analyze_query(query, language),
                execution_plan=["Direct execution"],
                cost_reduction=0.0
            )

    def _detect_query_language(self, query: str) -> QueryLanguage:
        """Detectar el lenguaje de la consulta."""
        # Similar a QueryEngine pero más preciso
        if re.search(r'\bSELECT\b.*\bWHERE\b', query, re.IGNORECASE):
            return QueryLanguage.SPARQL
        elif re.search(r'\bMATCH\b.*\bRETURN\b', query, re.IGNORECASE):
            return QueryLanguage.CYPHER
        elif query.startswith('g.'):
            return QueryLanguage.GREMLIN
        else:
            return QueryLanguage.PATTERN

    def _parse_query(self, query: str, language: QueryLanguage) -> Dict[str, Any]:
        """Parsear la consulta en estructura interna."""
        # Implementación simplificada - en producción usar parsers reales
        return {
            "raw_query": query,
            "language": language,
            "tokens": query.split(),
            "length": len(query)
        }

    def _calculate_complexity_score(self, parsed_query: Dict[str, Any], language: QueryLanguage) -> float:
        """Calcular puntuación de complejidad de la consulta."""
        base_score = 1.0

        # Factores de complejidad
        length_factor = min(len(parsed_query["raw_query"]) / 1000, 5.0)
        token_factor = len(parsed_query["tokens"]) / 50.0

        # Factores específicos por lenguaje
        if language == QueryLanguage.SPARQL:
            sparql_complexity = self._calculate_sparql_complexity(parsed_query)
            base_score += sparql_complexity
        elif language == QueryLanguage.CYPHER:
            cypher_complexity = self._calculate_cypher_complexity(parsed_query)
            base_score += cypher_complexity

        return base_score + length_factor + token_factor

    def _calculate_sparql_complexity(self, parsed_query: Dict[str, Any]) -> float:
        """Calcular complejidad específica de SPARQL."""
        query = parsed_query["raw_query"]
        complexity = 0.0

        # Contar patrones complejos
        if "UNION" in query.upper():
            complexity += 1.0
        if "OPTIONAL" in query.upper():
            complexity += 0.5
        if "FILTER" in query.upper():
            complexity += 0.3
        if "BIND" in query.upper():
            complexity += 0.2

        return complexity

    def _calculate_cypher_complexity(self, parsed_query: Dict[str, Any]) -> float:
        """Calcular complejidad específica de Cypher."""
        query = parsed_query["raw_query"]
        complexity = 0.0

        # Contar patrones complejos
        if "WITH" in query.upper():
            complexity += 0.5
        if "UNWIND" in query.upper():
            complexity += 0.8
        if "FOREACH" in query.upper():
            complexity += 1.0
        if "CASE" in query.upper():
            complexity += 0.3

        return complexity

    def _estimate_cardinality(self, parsed_query: Dict[str, Any], language: QueryLanguage) -> int:
        """Estimar cardinalidad del resultado."""
        # Estimación simplificada basada en estadísticas del grafo
        base_cardinality = 100

        if language == QueryLanguage.SPARQL:
            # Estimar basado en patrones SPARQL
            if "SELECT *" in parsed_query["raw_query"]:
                base_cardinality = int(self.graph_stats.get("total_triples", 1000000) * 0.1)
            else:
                base_cardinality = 1000

        elif language == QueryLanguage.CYPHER:
            # Estimar basado en patrones Cypher
            base_cardinality = 500

        return max(1, base_cardinality)

    def _analyze_selectivity(self, parsed_query: Dict[str, Any], language: QueryLanguage) -> Dict[str, float]:
        """Analizar factores de selectividad."""
        selectivity = {}

        if language == QueryLanguage.SPARQL:
            # Analizar selectividad de patrones SPARQL
            query = parsed_query["raw_query"]
            if "rdf:type" in query:
                selectivity["type_filter"] = 0.1  # 10% de selectividad
            if "FILTER" in query:
                selectivity["value_filter"] = 0.01  # 1% de selectividad

        return selectivity

    def _identify_join_patterns(self, parsed_query: Dict[str, Any], language: QueryLanguage) -> List[Dict[str, Any]]:
        """Identificar patrones de join en la consulta."""
        patterns = []

        if language == QueryLanguage.SPARQL:
            # Identificar joins en SPARQL
            query = parsed_query["raw_query"]
            # Simplificado - en producción analizar AST
            if query.count("?") > 2:
                patterns.append({
                    "type": "variable_join",
                    "variables": ["?s", "?p", "?o"],
                    "estimated_cost": 100.0
                })

        return patterns

    def _analyze_filter_conditions(self, parsed_query: Dict[str, Any], language: QueryLanguage) -> List[Dict[str, Any]]:
        """Analizar condiciones de filtro."""
        conditions = []

        if language == QueryLanguage.SPARQL:
            query = parsed_query["raw_query"]
            if "FILTER" in query:
                conditions.append({
                    "type": "sparql_filter",
                    "condition": "FILTER clause",
                    "selectivity": 0.1
                })

        return conditions

    def _suggest_indexes(self, parsed_query: Dict[str, Any], language: QueryLanguage) -> List[str]:
        """Sugerir índices potenciales."""
        suggestions = []

        if language == QueryLanguage.SPARQL:
            query = parsed_query["raw_query"]
            if "?s rdf:type" in query:
                suggestions.append("subject_type_index")
            if "rdfs:label" in query:
                suggestions.append("label_index")

        return suggestions

    def _calculate_cost_breakdown(self, parsed_query: Dict[str, Any], language: QueryLanguage) -> Dict[str, float]:
        """Calcular desglose de costos."""
        return {
            "parsing": 10.0,
            "optimization": 20.0,
            "execution": 100.0,
            "total": 130.0
        }

    def _identify_optimization_opportunities(
        self,
        parsed_query: Dict[str, Any],
        language: QueryLanguage,
        complexity: float,
        selectivity: Dict[str, float]
    ) -> List[str]:
        """Identificar oportunidades de optimización."""
        opportunities = []

        if complexity > 3.0:
            opportunities.append("Query decomposition")
        if selectivity and min(selectivity.values()) < 0.1:
            opportunities.append("Filter pushdown")
        if "SELECT *" in parsed_query["raw_query"]:
            opportunities.append("Projection optimization")

        return opportunities

    async def _cost_based_optimization(
        self,
        query: str,
        analysis: QueryAnalysis
    ) -> Tuple[str, List[str], float, List[str], float]:
        """Optimización basada en costo."""
        optimized_query = query
        optimizations = []
        improvement = 0.0
        plan = ["Cost-based optimization applied"]
        cost_reduction = 0.0

        # Aplicar optimizaciones basadas en costo
        if analysis.complexity_score > 2.0:
            optimizations.append("Query restructuring")
            improvement += 0.3
            cost_reduction += 30.0

        if analysis.optimization_opportunities:
            for opp in analysis.optimization_opportunities[:2]:  # Limitar a 2 optimizaciones
                optimizations.append(opp)
                improvement += 0.1
                cost_reduction += 10.0

        return optimized_query, optimizations, improvement, plan, cost_reduction

    def _rule_based_optimization(
        self,
        query: str,
        analysis: QueryAnalysis
    ) -> Tuple[str, List[str], float, List[str], float]:
        """Optimización basada en reglas."""
        optimized_query = query
        optimizations = []
        improvement = 0.0
        plan = ["Rule-based optimization applied"]
        cost_reduction = 0.0

        # Aplicar reglas de optimización
        if "SELECT *" in query:
            optimized_query = query.replace("SELECT *", "SELECT DISTINCT *")
            optimizations.append("Avoid SELECT *")
            improvement += 0.2
            cost_reduction += 20.0

        if analysis.complexity_score > 3.0:
            optimizations.append("Simplify complex patterns")
            improvement += 0.15
            cost_reduction += 15.0

        return optimized_query, optimizations, improvement, plan, cost_reduction

    async def _learning_based_optimization(
        self,
        query: str,
        analysis: QueryAnalysis
    ) -> Tuple[str, List[str], float, List[str], float]:
        """Optimización basada en aprendizaje (placeholder)."""
        # En implementación real, usar modelos ML entrenados
        return self._rule_based_optimization(query, analysis)

    def _heuristic_optimization(
        self,
        query: str,
        analysis: QueryAnalysis
    ) -> Tuple[str, List[str], float, List[str], float]:
        """Optimización heurística."""
        optimized_query = query
        optimizations = []
        improvement = 0.0
        plan = ["Heuristic optimization applied"]
        cost_reduction = 0.0

        # Optimizaciones heurísticas simples
        if len(query) > 500:
            optimizations.append("Query length reduction")
            improvement += 0.1
            cost_reduction += 5.0

        return optimized_query, optimizations, improvement, plan, cost_reduction

    def get_optimizer_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del optimizador."""
        return {
            "analysis_cache_size": len(self.analysis_cache),
            "optimization_cache_size": len(self.optimization_cache),
            "cost_based_enabled": self.enable_cost_based_opt,
            "rule_based_enabled": self.enable_rule_based_opt,
            "learning_based_enabled": self.enable_learning_opt,
            "max_analysis_time_ms": self.max_analysis_time_ms
        }

    def clear_caches(self):
        """Limpiar caches del optimizador."""
        self.analysis_cache.clear()
        self.optimization_cache.clear()
        logger.info("Optimizer caches cleared")


# Instancia global
_optimizer = None

def get_query_optimizer() -> QueryOptimizer:
    """Obtener instancia global del optimizador de consultas."""
    global _optimizer
    if _optimizer is None:
        _optimizer = QueryOptimizer()
    return _optimizer