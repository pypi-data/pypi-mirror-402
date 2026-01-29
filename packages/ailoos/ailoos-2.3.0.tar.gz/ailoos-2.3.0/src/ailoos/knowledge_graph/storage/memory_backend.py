"""
Backend de almacenamiento en memoria para el grafo de conocimiento.
Implementa almacenamiento volátil de triples usando estructuras de datos en memoria.
"""

import asyncio
from typing import Set, List, Dict, Any, Tuple
from ...core.logging import get_logger
from . import StorageBackend, StorageConfig
from ..core import Triple

logger = get_logger(__name__)


class MemoryBackend(StorageBackend):
    """
    Backend de almacenamiento en memoria.
    Almacena triples en un conjunto para operaciones eficientes de búsqueda.
    """

    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self.triples: Set[Tuple[str, str, Any]] = set()
        self._lock = asyncio.Lock()
        logger.info("Initialized MemoryBackend")

    async def add_triple(self, triple: Triple) -> bool:
        """Agregar un triple al almacenamiento en memoria."""
        async with self._lock:
            return await self._execute_with_metrics(
                'add_triple',
                self._add_triple_impl,
                triple
            )

    async def _add_triple_impl(self, triple: Triple) -> bool:
        """Implementación interna de agregar triple."""
        self.triples.add(triple.to_tuple())
        return True

    async def remove_triple(self, triple: Triple) -> bool:
        """Remover un triple del almacenamiento en memoria."""
        async with self._lock:
            return await self._execute_with_metrics(
                'remove_triple',
                self._remove_triple_impl,
                triple
            )

    async def _remove_triple_impl(self, triple: Triple) -> bool:
        """Implementación interna de remover triple."""
        self.triples.discard(triple.to_tuple())
        return True

    async def query(self, query: str, **kwargs) -> List[Triple]:
        """Ejecutar consulta en el almacenamiento en memoria."""
        async with self._lock:
            return await self._execute_with_metrics(
                'query',
                self._query_impl,
                query,
                **kwargs
            )

    async def _query_impl(self, query: str, **kwargs) -> List[Triple]:
        """Implementación interna de consulta."""
        # Parsear consulta simple: "subject predicate object"
        # Soporta wildcards con '?'
        try:
            parts = query.split()
            if len(parts) != 3:
                raise ValueError("Query must be in format: subject predicate object")

            subj_pattern, pred_pattern, obj_pattern = parts

            # Convertir '?' a None para matching
            subj = None if subj_pattern == '?' else subj_pattern
            pred = None if pred_pattern == '?' else pred_pattern
            obj = None if obj_pattern == '?' else obj_pattern

            # Si obj_pattern es '?', obj debe ser None
            # Si no, intentar convertir a tipo apropiado
            if obj is not None:
                # Intentar conversión básica de tipos
                if obj.isdigit():
                    obj = int(obj)
                elif obj.replace('.', '').isdigit():
                    obj = float(obj)
                elif obj.lower() in ('true', 'false'):
                    obj = obj.lower() == 'true'

            results = []
            for s, p, o in self.triples:
                match = True

                if subj is not None and s != subj:
                    match = False
                if pred is not None and p != pred:
                    match = False
                if obj is not None and o != obj:
                    match = False

                if match:
                    results.append(Triple(s, p, o))

            return results

        except Exception as e:
            logger.error(f"Query parsing error: {e}")
            return []

    async def get_all_triples(self) -> List[Triple]:
        """Obtener todos los triples del almacenamiento."""
        async with self._lock:
            return await self._execute_with_metrics(
                'get_all_triples',
                self._get_all_triples_impl
            )

    async def _get_all_triples_impl(self) -> List[Triple]:
        """Implementación interna de obtener todos los triples."""
        return [Triple(s, p, o) for s, p, o in self.triples]

    async def clear(self) -> bool:
        """Limpiar todos los triples del almacenamiento."""
        async with self._lock:
            return await self._execute_with_metrics(
                'clear',
                self._clear_impl
            )

    async def _clear_impl(self) -> bool:
        """Implementación interna de limpiar."""
        self.triples.clear()
        return True

    async def close(self):
        """Cerrar el backend de memoria (no hay conexiones que cerrar)."""
        logger.info("MemoryBackend closed")

    async def health_check(self) -> bool:
        """Verificar salud del backend de memoria."""
        try:
            # Verificar que podemos acceder a la estructura de datos
            _ = len(self.triples)
            self._last_health_check = asyncio.get_event_loop().time()
            return True
        except Exception as e:
            logger.error(f"MemoryBackend health check failed: {e}")
            return False

    def get_memory_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas específicas de memoria."""
        return {
            "triple_count": len(self.triples),
            "memory_usage_estimate_kb": len(self.triples) * 0.5,  # Estimación aproximada
            "backend_metrics": self.get_metrics()
        }