"""
Backend de almacenamiento Neo4j para el grafo de conocimiento.
Implementa integración con Neo4j para almacenamiento persistente de grafos.
"""

import asyncio
from typing import List, Dict, Any, Optional
from ...core.logging import get_logger
from . import StorageBackend, StorageConfig, Triple

logger = get_logger(__name__)

try:
    from neo4j import AsyncGraphDatabase, AsyncDriver
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    AsyncDriver = None


class Neo4jBackend(StorageBackend):
    """
    Backend de almacenamiento Neo4j.
    Integra con Neo4j para operaciones CRUD en grafos de conocimiento.
    """

    def __init__(self, config: StorageConfig):
        super().__init__(config)

        if not NEO4J_AVAILABLE:
            raise ImportError("neo4j-driver is required for Neo4j backend")

        self.driver: Optional[AsyncDriver] = None
        self.uri = config.connection_params.get('uri', 'bolt://localhost:7687')
        self.user = config.connection_params.get('user', 'neo4j')
        self.password = config.connection_params.get('password', '')
        self.database = config.connection_params.get('database', 'neo4j')

        # Inicializar conexión
        asyncio.create_task(self._initialize_connection())

    async def _initialize_connection(self):
        """Inicializar conexión con Neo4j."""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60
            )

            # Verificar conexión
            await self.driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {self.uri}")

        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    async def add_triple(self, triple: Triple) -> bool:
        """Agregar un triple a Neo4j."""
        return await self._execute_with_metrics(
            'add_triple',
            self._add_triple_impl,
            triple
        )

    async def _add_triple_impl(self, triple: Triple) -> bool:
        """Implementación interna de agregar triple."""
        if not self.driver:
            raise ConnectionError("Neo4j driver not initialized")

        query = """
        MERGE (s:Resource {uri: $subject})
        MERGE (o:Resource {uri: $object})
        CREATE (s)-[r:RELATION {predicate: $predicate}]->(o)
        RETURN count(r) as created
        """

        async with self.driver.session(database=self.database) as session:
            result = await session.run(
                query,
                subject=triple.subject,
                predicate=triple.predicate,
                object=str(triple.object)
            )
            record = await result.single()
            return record["created"] > 0

    async def remove_triple(self, triple: Triple) -> bool:
        """Remover un triple de Neo4j."""
        return await self._execute_with_metrics(
            'remove_triple',
            self._remove_triple_impl,
            triple
        )

    async def _remove_triple_impl(self, triple: Triple) -> bool:
        """Implementación interna de remover triple."""
        if not self.driver:
            raise ConnectionError("Neo4j driver not initialized")

        query = """
        MATCH (s:Resource {uri: $subject})-[r:RELATION {predicate: $predicate}]->(o:Resource {uri: $object})
        DELETE r
        RETURN count(r) as deleted
        """

        async with self.driver.session(database=self.database) as session:
            result = await session.run(
                query,
                subject=triple.subject,
                predicate=triple.predicate,
                object=str(triple.object)
            )
            record = await result.single()
            return record["deleted"] > 0

    async def query(self, query: str, **kwargs) -> List[Triple]:
        """Ejecutar consulta Cypher en Neo4j."""
        return await self._execute_with_metrics(
            'query',
            self._query_impl,
            query,
            **kwargs
        )

    async def _query_impl(self, query: str, **kwargs) -> List[Triple]:
        """Implementación interna de consulta Cypher."""
        if not self.driver:
            raise ConnectionError("Neo4j driver not initialized")

        # Si es una consulta simple de patrón, convertir a Cypher
        if ' ' in query and not query.upper().startswith(('MATCH', 'CREATE', 'MERGE')):
            query = self._convert_pattern_to_cypher(query)

        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, **kwargs)
            records = await result.fetch()

            triples = []
            for record in records:
                # Asumir que la consulta devuelve subject, predicate, object
                if len(record) >= 3:
                    subject = str(record[0])
                    predicate = str(record[1])
                    object_val = record[2]

                    # Intentar conversión de tipos
                    if isinstance(object_val, str):
                        if object_val.isdigit():
                            object_val = int(object_val)
                        elif object_val.replace('.', '').isdigit():
                            object_val = float(object_val)
                        elif object_val.lower() in ('true', 'false'):
                            object_val = object_val.lower() == 'true'

                    triples.append(Triple(subject, predicate, object_val))

            return triples

    def _convert_pattern_to_cypher(self, pattern: str) -> str:
        """Convertir patrón simple a consulta Cypher."""
        parts = pattern.split()
        if len(parts) != 3:
            raise ValueError("Pattern must be in format: subject predicate object")

        subj, pred, obj = parts

        conditions = []
        params = {}

        if subj != '?':
            conditions.append("s.uri = $subject")
            params["subject"] = subj

        if pred != '?':
            conditions.append("r.predicate = $predicate")
            params["predicate"] = pred

        if obj != '?':
            conditions.append("o.uri = $object")
            params["object"] = str(obj)

        where_clause = " AND ".join(conditions) if conditions else ""

        query = f"""
        MATCH (s:Resource)-[r:RELATION]->(o:Resource)
        {f"WHERE {where_clause}" if where_clause else ""}
        RETURN s.uri, r.predicate, o.uri
        """

        return query

    async def get_all_triples(self) -> List[Triple]:
        """Obtener todos los triples de Neo4j."""
        return await self._execute_with_metrics(
            'get_all_triples',
            self._get_all_triples_impl
        )

    async def _get_all_triples_impl(self) -> List[Triple]:
        """Implementación interna de obtener todos los triples."""
        if not self.driver:
            raise ConnectionError("Neo4j driver not initialized")

        query = """
        MATCH (s:Resource)-[r:RELATION]->(o:Resource)
        RETURN s.uri, r.predicate, o.uri
        LIMIT 10000
        """

        async with self.driver.session(database=self.database) as session:
            result = await session.run(query)
            records = await result.fetch()

            triples = []
            for record in records:
                subject = str(record[0])
                predicate = str(record[1])
                object_val = str(record[2])

                # Intentar conversión de tipos
                if object_val.isdigit():
                    object_val = int(object_val)
                elif object_val.replace('.', '').isdigit():
                    object_val = float(object_val)
                elif object_val.lower() in ('true', 'false'):
                    object_val = object_val.lower() == 'true'

                triples.append(Triple(subject, predicate, object_val))

            return triples

    async def clear(self) -> bool:
        """Limpiar todos los triples de Neo4j."""
        return await self._execute_with_metrics(
            'clear',
            self._clear_impl
        )

    async def _clear_impl(self) -> bool:
        """Implementación interna de limpiar."""
        if not self.driver:
            raise ConnectionError("Neo4j driver not initialized")

        query = """
        MATCH (n)-[r]-()
        DELETE r, n
        """

        async with self.driver.session(database=self.database) as session:
            await session.run(query)
            return True

    async def close(self):
        """Cerrar conexión con Neo4j."""
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j connection closed")

    async def health_check(self) -> bool:
        """Verificar salud de la conexión con Neo4j."""
        try:
            if not self.driver:
                return False

            await self.driver.verify_connectivity()
            self._last_health_check = asyncio.get_event_loop().time()
            return True

        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            return False

    async def get_database_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de la base de datos Neo4j."""
        if not self.driver:
            return {"error": "Driver not initialized"}

        try:
            async with self.driver.session(database=self.database) as session:
                # Contar nodos
                result = await session.run("MATCH (n) RETURN count(n) as node_count")
                node_count = (await result.single())["node_count"]

                # Contar relaciones
                result = await session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
                rel_count = (await result.single())["rel_count"]

                return {
                    "node_count": node_count,
                    "relationship_count": rel_count,
                    "database": self.database,
                    "backend_metrics": self.get_metrics()
                }

        except Exception as e:
            logger.error(f"Error getting Neo4j stats: {e}")
            return {"error": str(e)}