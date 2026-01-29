"""
Ejecutor optimizado de consultas para el grafo de conocimiento AILOOS.
Proporciona ejecución con cache inteligente, estadísticas y monitoreo de rendimiento.
"""

import asyncio
import time
import hashlib
import json
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque

from ...core.logging import get_logger
from ..query_engine import get_query_engine, QueryResult, QueryLanguage
from ..core import Triple
from .query_optimizer import get_query_optimizer, OptimizationResult
from ...auditing.audit_manager import get_audit_manager, AuditEventType
from ...auditing.metrics_collector import get_metrics_collector
from ...utils.cache import get_cache_manager

logger = get_logger(__name__)


@dataclass
class QueryExecutionStats:
    """Estadísticas de ejecución de consulta."""
    query_hash: str
    execution_count: int
    total_execution_time_ms: float
    avg_execution_time_ms: float
    min_execution_time_ms: float
    max_execution_time_ms: float
    cache_hit_count: int
    cache_hit_rate: float
    last_executed: datetime
    optimization_applied: bool
    result_size_avg: int
    error_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            "query_hash": self.query_hash,
            "execution_count": self.execution_count,
            "total_execution_time_ms": self.total_execution_time_ms,
            "avg_execution_time_ms": self.avg_execution_time_ms,
            "min_execution_time_ms": self.min_execution_time_ms,
            "max_execution_time_ms": self.max_execution_time_ms,
            "cache_hit_count": self.cache_hit_count,
            "cache_hit_rate": self.cache_hit_rate,
            "last_executed": self.last_executed.isoformat(),
            "optimization_applied": self.optimization_applied,
            "result_size_avg": self.result_size_avg,
            "error_count": self.error_count
        }


@dataclass
class CacheEntry:
    """Entrada de cache para resultados de consulta."""
    query_hash: str
    result: QueryResult
    cached_at: datetime
    ttl_seconds: int
    access_count: int
    last_accessed: datetime
    size_bytes: int

    def is_expired(self) -> bool:
        """Verificar si la entrada ha expirado."""
        return (datetime.now() - self.cached_at).total_seconds() > self.ttl_seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            "query_hash": self.query_hash,
            "result": self.result.to_dict(),
            "cached_at": self.cached_at.isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat(),
            "size_bytes": self.size_bytes
        }


class SmartCache:
    """
    Cache inteligente con políticas de reemplazo avanzadas.
    """

    def __init__(self, max_size_mb: int = 100, default_ttl_seconds: int = 3600):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.default_ttl = default_ttl_seconds
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: deque = deque()
        self.current_size_bytes = 0

        # Políticas de cache
        self.enable_lru = True
        self.enable_frequency_based = True
        self.compression_threshold = 1000  # bytes

    def get(self, key: str) -> Optional[QueryResult]:
        """Obtener entrada del cache."""
        if key not in self.cache:
            return None

        entry = self.cache[key]
        if entry.is_expired():
            self._remove_entry(key)
            return None

        # Actualizar estadísticas de acceso
        entry.access_count += 1
        entry.last_accessed = datetime.now()

        # Mover al final de la cola LRU
        if self.enable_lru and key in self.access_order:
            self.access_order.remove(key)
            self.access_order.append(key)

        return entry.result

    def put(self, key: str, result: QueryResult, ttl_seconds: Optional[int] = None):
        """Almacenar entrada en el cache."""
        ttl = ttl_seconds or self.default_ttl

        # Calcular tamaño aproximado
        size_bytes = self._calculate_size(result)

        # Verificar si necesitamos hacer espacio
        if self.current_size_bytes + size_bytes > self.max_size_bytes:
            self._evict_entries(size_bytes)

        # Crear entrada
        entry = CacheEntry(
            query_hash=key,
            result=result,
            cached_at=datetime.now(),
            ttl_seconds=ttl,
            access_count=1,
            last_accessed=datetime.now(),
            size_bytes=size_bytes
        )

        # Almacenar
        self.cache[key] = entry
        self.current_size_bytes += size_bytes
        self.access_order.append(key)

    def _remove_entry(self, key: str):
        """Remover entrada del cache."""
        if key in self.cache:
            entry = self.cache[key]
            self.current_size_bytes -= entry.size_bytes
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)

    def _evict_entries(self, required_space: int):
        """Evitar entradas para hacer espacio."""
        space_needed = required_space - (self.max_size_bytes - self.current_size_bytes)

        while space_needed > 0 and self.access_order:
            # Política LRU con frecuencia
            if self.enable_frequency_based:
                # Encontrar entrada menos frecuentemente usada
                victim_key = min(
                    self.access_order,
                    key=lambda k: self.cache[k].access_count
                )
            else:
                # LRU simple
                victim_key = self.access_order.popleft()

            if victim_key in self.cache:
                entry = self.cache[victim_key]
                space_needed -= entry.size_bytes
                self._remove_entry(victim_key)

    def _calculate_size(self, result: QueryResult) -> int:
        """Calcular tamaño aproximado del resultado."""
        # Estimación simple basada en número de triples
        base_size = 100  # overhead
        triple_size = len(result.results) * 50  # ~50 bytes por triple
        return base_size + triple_size

    def clear_expired(self):
        """Limpiar entradas expiradas."""
        expired_keys = [k for k, v in self.cache.items() if v.is_expired()]
        for key in expired_keys:
            self._remove_entry(key)

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache."""
        total_accesses = sum(entry.access_count for entry in self.cache.values())
        return {
            "entries_count": len(self.cache),
            "current_size_mb": self.current_size_bytes / (1024 * 1024),
            "max_size_mb": self.max_size_bytes / (1024 * 1024),
            "utilization_percent": (self.current_size_bytes / self.max_size_bytes) * 100,
            "total_accesses": total_accesses,
            "avg_accesses_per_entry": total_accesses / max(len(self.cache), 1)
        }


class QueryExecutor:
    """
    Ejecutor optimizado de consultas con cache inteligente y monitoreo.
    """

    def __init__(self):
        self.query_engine = get_query_engine()
        self.optimizer = get_query_optimizer()
        self.audit_manager = get_audit_manager()
        self.metrics_collector = get_metrics_collector()
        self.cache = get_cache_manager()

        # Cache inteligente para resultados
        self.result_cache = SmartCache(max_size_mb=200, default_ttl_seconds=1800)

        # Estadísticas de ejecución
        self.execution_stats: Dict[str, QueryExecutionStats] = {}
        self.recent_executions: deque = deque(maxlen=1000)

        # Configuración
        self.enable_caching = True
        self.enable_optimization = True
        self.max_execution_time_ms = 30000
        self.cache_warmup_enabled = True

        # Callbacks para eventos
        self.execution_callbacks: List[Callable] = []

    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        optimize: bool = True,
        use_cache: bool = True
    ) -> QueryResult:
        """
        Ejecutar consulta con optimización y cache.

        Args:
            query: La consulta a ejecutar
            parameters: Parámetros de la consulta
            user_id: ID del usuario
            optimize: Si optimizar la consulta
            use_cache: Si usar cache

        Returns:
            QueryResult con los resultados
        """
        start_time = time.time()
        parameters = parameters or {}

        try:
            # Generar hash de la consulta para cache y estadísticas
            query_signature = self._generate_query_signature(query, parameters)
            query_hash = hashlib.sha256(query_signature.encode()).hexdigest()[:16]

            # Verificar cache primero
            if use_cache and self.enable_caching:
                cached_result = self.result_cache.get(query_hash)
                if cached_result:
                    # Actualizar estadísticas de cache hit
                    self._update_cache_hit_stats(query_hash)

                    # Logging de cache hit
                    await self.audit_manager.log_event(
                        event_type=AuditEventType.DATA_ACCESS,
                        resource="query_executor",
                        action="cache_hit",
                        user_id=user_id,
                        details={
                            "query_hash": query_hash,
                            "cached_result_size": len(cached_result.results)
                        },
                        success=True,
                        processing_time_ms=0
                    )

                    logger.info(f"Cache hit for query: {query_hash}")
                    return cached_result

            # Optimizar consulta si está habilitado
            optimized_query = query
            optimization_result = None
            if optimize and self.enable_optimization:
                try:
                    optimization_result = await self.optimizer.optimize_query(query)
                    optimized_query = optimization_result.optimized_query
                except Exception as e:
                    logger.warning(f"Optimization failed, using original query: {e}")

            # Ejecutar consulta usando QueryEngine
            result = await self.query_engine.execute_query(
                optimized_query,
                parameters=parameters,
                user_id=user_id,
                optimize=False  # Ya optimizamos aquí
            )

            # Almacenar en cache si está habilitado
            if use_cache and self.enable_caching and not result.error:
                self.result_cache.put(query_hash, result)

            # Actualizar estadísticas
            execution_time = (time.time() - start_time) * 1000
            self._update_execution_stats(query_hash, execution_time, result, optimization_result)

            # Notificar callbacks
            for callback in self.execution_callbacks:
                try:
                    await callback({
                        "query_hash": query_hash,
                        "execution_time_ms": execution_time,
                        "result_size": len(result.results),
                        "optimized": optimization_result is not None,
                        "cached": False
                    })
                except Exception as e:
                    logger.error(f"Error in execution callback: {e}")

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="query_executor",
                action="execute_query",
                user_id=user_id,
                details={
                    "query_hash": query_hash,
                    "original_query_length": len(query),
                    "optimized": optimization_result is not None,
                    "cached": False,
                    "result_count": len(result.results),
                    "execution_time_ms": execution_time
                },
                success=not bool(result.error),
                processing_time_ms=execution_time
            )

            # Métricas
            self.metrics_collector.record_request("query_executor.execute_query")
            self.metrics_collector.record_response_time(execution_time)

            logger.info(f"Query executed: {query_hash}, results: {len(result.results)}, time: {execution_time:.2f}ms")

            return result

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = str(e)

            # Logging de error
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="query_executor",
                action="execute_query",
                user_id=user_id,
                details={
                    "query": query[:500],  # Limitar longitud
                    "parameters": parameters,
                    "error": error_msg
                },
                success=False,
                processing_time_ms=execution_time
            )

            self.metrics_collector.record_error("query_executor.execute_query", "execution_error")

            logger.error(f"Query execution failed: {error_msg}")

            # Retornar resultado de error
            return QueryResult(
                query=query,
                language=QueryLanguage.PATTERN,
                results=[],
                execution_time_ms=execution_time,
                optimized=False,
                parameters=parameters,
                error=error_msg
            )

    async def execute_batch(
        self,
        queries: List[Dict[str, Any]],
        user_id: Optional[str] = None,
        max_concurrent: int = 5
    ) -> List[QueryResult]:
        """
        Ejecutar múltiples consultas en batch.

        Args:
            queries: Lista de diccionarios con 'query' y 'parameters'
            user_id: ID del usuario
            max_concurrent: Máximo número de consultas concurrentes

        Returns:
            Lista de QueryResult
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_single(query_data: Dict[str, Any]) -> QueryResult:
            async with semaphore:
                return await self.execute_query(
                    query_data["query"],
                    parameters=query_data.get("parameters"),
                    user_id=user_id,
                    optimize=query_data.get("optimize", True),
                    use_cache=query_data.get("use_cache", True)
                )

        tasks = [execute_single(q) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Manejar excepciones
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch query {i} failed: {result}")
                final_results.append(QueryResult(
                    query=queries[i]["query"],
                    language=QueryLanguage.PATTERN,
                    results=[],
                    execution_time_ms=0,
                    optimized=False,
                    parameters=queries[i].get("parameters", {}),
                    error=str(result)
                ))
            else:
                final_results.append(result)

        return final_results

    def _generate_query_signature(self, query: str, parameters: Dict[str, Any]) -> str:
        """Generar firma única para la consulta."""
        # Normalizar consulta removiendo espacios extra
        normalized_query = " ".join(query.split())

        # Incluir parámetros en la firma
        param_str = json.dumps(parameters, sort_keys=True)

        return f"{normalized_query}|{param_str}"

    def _update_cache_hit_stats(self, query_hash: str):
        """Actualizar estadísticas de cache hit."""
        if query_hash in self.execution_stats:
            stats = self.execution_stats[query_hash]
            stats.cache_hit_count += 1
            stats.cache_hit_rate = stats.cache_hit_count / stats.execution_count

    def _update_execution_stats(
        self,
        query_hash: str,
        execution_time: float,
        result: QueryResult,
        optimization_result: Optional[OptimizationResult]
    ):
        """Actualizar estadísticas de ejecución."""
        if query_hash not in self.execution_stats:
            self.execution_stats[query_hash] = QueryExecutionStats(
                query_hash=query_hash,
                execution_count=0,
                total_execution_time_ms=0,
                avg_execution_time_ms=0,
                min_execution_time_ms=float('inf'),
                max_execution_time_ms=0,
                cache_hit_count=0,
                cache_hit_rate=0.0,
                last_executed=datetime.now(),
                optimization_applied=optimization_result is not None,
                result_size_avg=0,
                error_count=0
            )

        stats = self.execution_stats[query_hash]
        stats.execution_count += 1
        stats.total_execution_time_ms += execution_time
        stats.avg_execution_time_ms = stats.total_execution_time_ms / stats.execution_count
        stats.min_execution_time_ms = min(stats.min_execution_time_ms, execution_time)
        stats.max_execution_time_ms = max(stats.max_execution_time_ms, execution_time)
        stats.last_executed = datetime.now()

        # Actualizar tamaño promedio de resultado
        if stats.execution_count == 1:
            stats.result_size_avg = len(result.results)
        else:
            stats.result_size_avg = (
                (stats.result_size_avg * (stats.execution_count - 1)) + len(result.results)
            ) / stats.execution_count

        if result.error:
            stats.error_count += 1

        # Actualizar si se aplicó optimización
        if optimization_result:
            stats.optimization_applied = True

    async def warmup_cache(self, common_queries: List[str]):
        """
        Pre-cargar cache con consultas comunes.

        Args:
            common_queries: Lista de consultas comunes
        """
        if not self.cache_warmup_enabled:
            return

        logger.info(f"Warming up cache with {len(common_queries)} queries")

        for query in common_queries:
            try:
                # Ejecutar sin optimización para warmup
                result = await self.execute_query(query, optimize=False, use_cache=False)
                if not result.error:
                    query_hash = hashlib.sha256(
                        self._generate_query_signature(query, {}).encode()
                    ).hexdigest()[:16]
                    self.result_cache.put(query_hash, result, ttl_seconds=7200)  # 2 horas TTL

            except Exception as e:
                logger.warning(f"Cache warmup failed for query: {e}")

        logger.info("Cache warmup completed")

    def clear_cache(self):
        """Limpiar cache de resultados."""
        self.result_cache = SmartCache(max_size_mb=200, default_ttl_seconds=1800)
        logger.info("Query result cache cleared")

    def get_execution_stats(self, query_hash: Optional[str] = None) -> Dict[str, Any]:
        """Obtener estadísticas de ejecución."""
        if query_hash:
            stats = self.execution_stats.get(query_hash)
            return stats.to_dict() if stats else {}

        # Estadísticas globales
        total_queries = len(self.execution_stats)
        total_executions = sum(s.execution_count for s in self.execution_stats.values())
        total_cache_hits = sum(s.cache_hit_count for s in self.execution_stats.values())
        avg_cache_hit_rate = total_cache_hits / max(total_executions, 1)

        return {
            "total_unique_queries": total_queries,
            "total_executions": total_executions,
            "total_cache_hits": total_cache_hits,
            "avg_cache_hit_rate": avg_cache_hit_rate,
            "cache_stats": self.result_cache.get_stats(),
            "recent_executions": list(self.recent_executions)[-10:]  # Últimas 10
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Obtener métricas de rendimiento."""
        if not self.execution_stats:
            return {}

        execution_times = [s.avg_execution_time_ms for s in self.execution_stats.values()]
        result_sizes = [s.result_size_avg for s in self.execution_stats.values()]

        return {
            "avg_execution_time_ms": sum(execution_times) / len(execution_times),
            "max_execution_time_ms": max(execution_times),
            "min_execution_time_ms": min(execution_times),
            "avg_result_size": sum(result_sizes) / len(result_sizes),
            "total_errors": sum(s.error_count for s in self.execution_stats.values()),
            "optimization_rate": sum(1 for s in self.execution_stats.values() if s.optimization_applied) / len(self.execution_stats)
        }

    def add_execution_callback(self, callback: Callable):
        """Agregar callback para eventos de ejecución."""
        self.execution_callbacks.append(callback)

    def cleanup_expired_cache(self):
        """Limpiar entradas expiradas del cache."""
        self.result_cache.clear_expired()


# Instancia global
_executor = None

def get_query_executor() -> QueryExecutor:
    """Obtener instancia global del ejecutor de consultas."""
    global _executor
    if _executor is None:
        _executor = QueryExecutor()
    return _executor