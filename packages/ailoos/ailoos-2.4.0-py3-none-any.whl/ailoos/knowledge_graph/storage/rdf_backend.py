"""
Backend de almacenamiento RDF para el grafo de conocimiento.
Implementa integración con RDFlib para manejo de grafos RDF.
"""

import asyncio
from typing import List, Dict, Any, Optional
from ...core.logging import get_logger
from . import StorageBackend, StorageConfig, Triple

logger = get_logger(__name__)

try:
    import rdflib
    from rdflib import Graph, URIRef, Literal, BNode
    RDFLIB_AVAILABLE = True
except ImportError:
    RDFLIB_AVAILABLE = False
    Graph = None
    URIRef = None
    Literal = None
    BNode = None


class RDFBackend(StorageBackend):
    """
    Backend de almacenamiento RDF usando RDFlib.
    Soporta múltiples formatos RDF y operaciones SPARQL.
    """

    def __init__(self, config: StorageConfig):
        super().__init__(config)

        if not RDFLIB_AVAILABLE:
            raise ImportError("rdflib is required for RDF backend")

        self.graph: Optional[Graph] = None
        self.store_type = config.connection_params.get('store_type', 'default')
        self.format = config.connection_params.get('format', 'turtle')
        self._lock = asyncio.Lock()

        # Inicializar grafo
        self._initialize_graph()

    def _initialize_graph(self):
        """Inicializar grafo RDF."""
        try:
            self.graph = Graph(store=self.store_type)
            logger.info(f"Initialized RDF graph with store type: {self.store_type}")
        except Exception as e:
            logger.error(f"Failed to initialize RDF graph: {e}")
            raise

    async def add_triple(self, triple: Triple) -> bool:
        """Agregar un triple al grafo RDF."""
        async with self._lock:
            return await self._execute_with_metrics(
                'add_triple',
                self._add_triple_impl,
                triple
            )

    async def _add_triple_impl(self, triple: Triple) -> bool:
        """Implementación interna de agregar triple."""
        try:
            subj = self._to_rdf_term(triple.subject, is_subject=True)
            pred = URIRef(triple.predicate)
            obj = self._to_rdf_term(triple.object, is_subject=False)

            self.graph.add((subj, pred, obj))
            return True

        except Exception as e:
            logger.error(f"Error adding triple to RDF graph: {e}")
            return False

    async def remove_triple(self, triple: Triple) -> bool:
        """Remover un triple del grafo RDF."""
        async with self._lock:
            return await self._execute_with_metrics(
                'remove_triple',
                self._remove_triple_impl,
                triple
            )

    async def _remove_triple_impl(self, triple: Triple) -> bool:
        """Implementación interna de remover triple."""
        try:
            subj = self._to_rdf_term(triple.subject, is_subject=True)
            pred = URIRef(triple.predicate)
            obj = self._to_rdf_term(triple.object, is_subject=False)

            self.graph.remove((subj, pred, obj))
            return True

        except Exception as e:
            logger.error(f"Error removing triple from RDF graph: {e}")
            return False

    async def query(self, query: str, **kwargs) -> List[Triple]:
        """Ejecutar consulta SPARQL en el grafo RDF."""
        async with self._lock:
            return await self._execute_with_metrics(
                'query',
                self._query_impl,
                query,
                **kwargs
            )

    async def _query_impl(self, query: str, **kwargs) -> List[Triple]:
        """Implementación interna de consulta SPARQL."""
        try:
            # Si es una consulta simple de patrón, convertir a SPARQL
            if ' ' in query and not query.upper().startswith(('SELECT', 'ASK', 'CONSTRUCT', 'DESCRIBE')):
                query = self._convert_pattern_to_sparql(query)

            results = self.graph.query(query, **kwargs)
            triples = []

            for row in results:
                if len(row) >= 3:
                    subj = self._from_rdf_term(row[0])
                    pred = self._from_rdf_term(row[1])
                    obj = self._from_rdf_term(row[2])

                    triples.append(Triple(subj, pred, obj))

            return triples

        except Exception as e:
            logger.error(f"SPARQL query error: {e}")
            return []

    def _convert_pattern_to_sparql(self, pattern: str) -> str:
        """Convertir patrón simple a consulta SPARQL."""
        parts = pattern.split()
        if len(parts) != 3:
            raise ValueError("Pattern must be in format: subject predicate object")

        subj, pred, obj = parts

        # Convertir wildcards
        subj_var = "?s" if subj == "?" else f"<{subj}>"
        pred_var = "?p" if pred == "?" else f"<{pred}>"
        obj_var = "?o" if obj == "?" else f'"{obj}"'

        return f"""
        SELECT {subj_var} {pred_var} {obj_var}
        WHERE {{
            {subj_var} {pred_var} {obj_var} .
        }}
        """

    async def get_all_triples(self) -> List[Triple]:
        """Obtener todos los triples del grafo RDF."""
        async with self._lock:
            return await self._execute_with_metrics(
                'get_all_triples',
                self._get_all_triples_impl
            )

    async def _get_all_triples_impl(self) -> List[Triple]:
        """Implementación interna de obtener todos los triples."""
        triples = []
        for subj, pred, obj in self.graph:
            subj_str = self._from_rdf_term(subj)
            pred_str = self._from_rdf_term(pred)
            obj_val = self._from_rdf_term(obj)

            triples.append(Triple(subj_str, pred_str, obj_val))

        return triples

    async def clear(self) -> bool:
        """Limpiar todos los triples del grafo RDF."""
        async with self._lock:
            return await self._execute_with_metrics(
                'clear',
                self._clear_impl
            )

    async def _clear_impl(self) -> bool:
        """Implementación interna de limpiar."""
        try:
            self.graph.remove((None, None, None))
            return True
        except Exception as e:
            logger.error(f"Error clearing RDF graph: {e}")
            return False

    async def close(self):
        """Cerrar el backend RDF."""
        if self.graph:
            # RDFlib no requiere cierre explícito, pero podemos limpiar
            self.graph = None
            logger.info("RDF backend closed")

    async def health_check(self) -> bool:
        """Verificar salud del grafo RDF."""
        try:
            if not self.graph:
                return False

            # Intentar una operación simple
            _ = len(self.graph)
            self._last_health_check = asyncio.get_event_loop().time()
            return True

        except Exception as e:
            logger.error(f"RDF backend health check failed: {e}")
            return False

    def _to_rdf_term(self, value: Any, is_subject: bool = False) -> Any:
        """Convertir valor a término RDF."""
        if isinstance(value, str):
            if value.startswith('http') or ':' in value:
                return URIRef(value)
            else:
                return BNode(value) if is_subject else Literal(value)
        elif isinstance(value, (int, float, bool)):
            return Literal(value)
        else:
            return Literal(str(value))

    def _from_rdf_term(self, term) -> Any:
        """Convertir término RDF a valor Python."""
        if hasattr(term, 'toPython'):
            return term.toPython()
        else:
            return str(term)

    async def serialize_graph(self, format: str = None) -> Optional[str]:
        """Serializar el grafo RDF a string."""
        if not self.graph:
            return None

        format = format or self.format
        try:
            return self.graph.serialize(format=format)
        except Exception as e:
            logger.error(f"Error serializing RDF graph: {e}")
            return None

    async def parse_rdf_string(self, rdf_string: str, format: str = None) -> bool:
        """Parsear string RDF y agregarlo al grafo."""
        if not self.graph:
            return False

        format = format or self.format
        try:
            self.graph.parse(data=rdf_string, format=format)
            return True
        except Exception as e:
            logger.error(f"Error parsing RDF string: {e}")
            return False

    def get_graph_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del grafo RDF."""
        if not self.graph:
            return {"error": "Graph not initialized"}

        try:
            subjects = set()
            predicates = set()

            for s, p, o in self.graph:
                subjects.add(str(s))
                predicates.add(str(p))

            return {
                "triple_count": len(self.graph),
                "unique_subjects": len(subjects),
                "unique_predicates": len(predicates),
                "store_type": self.store_type,
                "backend_metrics": self.get_metrics()
            }

        except Exception as e:
            logger.error(f"Error getting RDF graph stats: {e}")
            return {"error": str(e)}