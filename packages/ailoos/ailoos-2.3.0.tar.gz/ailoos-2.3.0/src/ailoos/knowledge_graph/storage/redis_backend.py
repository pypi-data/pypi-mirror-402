"""
Backend de almacenamiento Redis para el grafo de conocimiento.
Implementa almacenamiento en Redis usando hashes y sets para triples RDF.
"""

import asyncio
import json
import hashlib
from typing import List, Dict, Any, Optional
from ...core.logging import get_logger
from . import StorageBackend, StorageConfig, Triple

logger = get_logger(__name__)

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    try:
        import redis
        REDIS_AVAILABLE = True
    except ImportError:
        REDIS_AVAILABLE = False
        redis = None


class RedisBackend(StorageBackend):
    """
    Backend de almacenamiento Redis.
    Usa Redis para almacenamiento persistente y de alto rendimiento de triples.
    """

    def __init__(self, config: StorageConfig):
        super().__init__(config)

        if not REDIS_AVAILABLE:
            raise ImportError("redis is required for Redis backend")

        self.redis_client: Optional[redis.Redis] = None
        self.host = config.connection_params.get('host', 'localhost')
        self.port = config.connection_params.get('port', 6379)
        self.db = config.connection_params.get('db', 0)
        self.password = config.connection_params.get('password')
        self.key_prefix = config.connection_params.get('key_prefix', 'kg:')

        # Claves Redis
        self.triples_key = f"{self.key_prefix}triples"
        self.subjects_key = f"{self.key_prefix}subjects"
        self.predicates_key = f"{self.key_prefix}predicates"

        # Inicializar conexión
        asyncio.create_task(self._initialize_connection())

    async def _initialize_connection(self):
        """Inicializar conexión con Redis."""
        try:
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )

            # Verificar conexión
            await self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    def _triple_to_key(self, triple: Triple) -> str:
        """Convertir triple a clave única."""
        triple_str = f"{triple.subject}:{triple.predicate}:{triple.object}"
        return hashlib.md5(triple_str.encode()).hexdigest()

    def _key_to_triple(self, key: str, data: str) -> Triple:
        """Convertir clave y datos a triple."""
        try:
            triple_data = json.loads(data)
            return Triple(
                subject=triple_data['subject'],
                predicate=triple_data['predicate'],
                object=triple_data['object']
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error parsing triple data for key {key}: {e}")
            raise

    async def add_triple(self, triple: Triple) -> bool:
        """Agregar un triple a Redis."""
        return await self._execute_with_metrics(
            'add_triple',
            self._add_triple_impl,
            triple
        )

    async def _add_triple_impl(self, triple: Triple) -> bool:
        """Implementación interna de agregar triple."""
        if not self.redis_client:
            raise ConnectionError("Redis client not initialized")

        try:
            triple_key = self._triple_to_key(triple)
            triple_data = json.dumps(triple.to_dict())

            # Almacenar triple
            await self.redis_client.hset(self.triples_key, triple_key, triple_data)

            # Indexar por subject
            await self.redis_client.sadd(f"{self.subjects_key}:{triple.subject}", triple_key)

            # Indexar por predicate
            await self.redis_client.sadd(f"{self.predicates_key}:{triple.predicate}", triple_key)

            return True

        except Exception as e:
            logger.error(f"Error adding triple to Redis: {e}")
            return False

    async def remove_triple(self, triple: Triple) -> bool:
        """Remover un triple de Redis."""
        return await self._execute_with_metrics(
            'remove_triple',
            self._remove_triple_impl,
            triple
        )

    async def _remove_triple_impl(self, triple: Triple) -> bool:
        """Implementación interna de remover triple."""
        if not self.redis_client:
            raise ConnectionError("Redis client not initialized")

        try:
            triple_key = self._triple_to_key(triple)

            # Verificar si existe
            exists = await self.redis_client.hexists(self.triples_key, triple_key)
            if not exists:
                return False

            # Remover de hash principal
            await self.redis_client.hdel(self.triples_key, triple_key)

            # Remover de índices
            await self.redis_client.srem(f"{self.subjects_key}:{triple.subject}", triple_key)
            await self.redis_client.srem(f"{self.predicates_key}:{triple.predicate}", triple_key)

            return True

        except Exception as e:
            logger.error(f"Error removing triple from Redis: {e}")
            return False

    async def query(self, query: str, **kwargs) -> List[Triple]:
        """Ejecutar consulta en Redis."""
        return await self._execute_with_metrics(
            'query',
            self._query_impl,
            query,
            **kwargs
        )

    async def _query_impl(self, query: str, **kwargs) -> List[Triple]:
        """Implementación interna de consulta."""
        if not self.redis_client:
            raise ConnectionError("Redis client not initialized")

        try:
            # Parsear consulta simple
            parts = query.split()
            if len(parts) != 3:
                raise ValueError("Query must be in format: subject predicate object")

            subj_pattern, pred_pattern, obj_pattern = parts

            # Para consultas simples, usar índices
            if subj_pattern != '?' and pred_pattern == '?' and obj_pattern == '?':
                # Consultar por subject
                return await self._query_by_subject(subj_pattern)
            elif pred_pattern != '?' and subj_pattern == '?' and obj_pattern == '?':
                # Consultar por predicate
                return await self._query_by_predicate(pred_pattern)
            else:
                # Consulta general - escanear todos los triples
                return await self._query_all_matching(subj_pattern, pred_pattern, obj_pattern)

        except Exception as e:
            logger.error(f"Query error: {e}")
            return []

    async def _query_by_subject(self, subject: str) -> List[Triple]:
        """Consultar triples por subject."""
        subject_key = f"{self.subjects_key}:{subject}"
        triple_keys = await self.redis_client.smembers(subject_key)

        triples = []
        for key in triple_keys:
            data = await self.redis_client.hget(self.triples_key, key)
            if data:
                triples.append(self._key_to_triple(key, data))

        return triples

    async def _query_by_predicate(self, predicate: str) -> List[Triple]:
        """Consultar triples por predicate."""
        predicate_key = f"{self.predicates_key}:{predicate}"
        triple_keys = await self.redis_client.smembers(predicate_key)

        triples = []
        for key in triple_keys:
            data = await self.redis_client.hget(self.triples_key, key)
            if data:
                triples.append(self._key_to_triple(key, data))

        return triples

    async def _query_all_matching(self, subj_pattern: str, pred_pattern: str, obj_pattern: str) -> List[Triple]:
        """Consultar todos los triples que coincidan con el patrón."""
        # Obtener todos los triples (limitado para rendimiento)
        all_triples_data = await self.redis_client.hgetall(self.triples_key)

        triples = []
        for key, data in all_triples_data.items():
            try:
                triple = self._key_to_triple(key, data)

                match = True
                if subj_pattern != '?' and triple.subject != subj_pattern:
                    match = False
                if pred_pattern != '?' and triple.predicate != pred_pattern:
                    match = False
                if obj_pattern != '?' and str(triple.object) != obj_pattern:
                    match = False

                if match:
                    triples.append(triple)

            except Exception as e:
                logger.warning(f"Error processing triple {key}: {e}")
                continue

        return triples

    async def get_all_triples(self) -> List[Triple]:
        """Obtener todos los triples de Redis."""
        return await self._execute_with_metrics(
            'get_all_triples',
            self._get_all_triples_impl
        )

    async def _get_all_triples_impl(self) -> List[Triple]:
        """Implementación interna de obtener todos los triples."""
        if not self.redis_client:
            raise ConnectionError("Redis client not initialized")

        all_triples_data = await self.redis_client.hgetall(self.triples_key)

        triples = []
        for key, data in all_triples_data.items():
            try:
                triples.append(self._key_to_triple(key, data))
            except Exception as e:
                logger.warning(f"Error processing triple {key}: {e}")
                continue

        return triples

    async def clear(self) -> bool:
        """Limpiar todos los triples de Redis."""
        return await self._execute_with_metrics(
            'clear',
            self._clear_impl
        )

    async def _clear_impl(self) -> bool:
        """Implementación interna de limpiar."""
        if not self.redis_client:
            raise ConnectionError("Redis client not initialized")

        try:
            # Obtener todas las claves relacionadas
            keys_to_delete = [self.triples_key, self.subjects_key, self.predicates_key]

            # Obtener claves de índices
            subject_keys = await self.redis_client.keys(f"{self.subjects_key}:*")
            predicate_keys = await self.redis_client.keys(f"{self.predicates_key}:*")

            keys_to_delete.extend(subject_keys)
            keys_to_delete.extend(predicate_keys)

            if keys_to_delete:
                await self.redis_client.delete(*keys_to_delete)

            return True

        except Exception as e:
            logger.error(f"Error clearing Redis storage: {e}")
            return False

    async def close(self):
        """Cerrar conexión con Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")

    async def health_check(self) -> bool:
        """Verificar salud de la conexión con Redis."""
        try:
            if not self.redis_client:
                return False

            await self.redis_client.ping()
            self._last_health_check = asyncio.get_event_loop().time()
            return True

        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    async def get_redis_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de Redis."""
        if not self.redis_client:
            return {"error": "Redis client not initialized"}

        try:
            info = await self.redis_client.info()
            triple_count = await self.redis_client.hlen(self.triples_key)

            return {
                "triple_count": triple_count,
                "redis_version": info.get('redis_version', 'unknown'),
                "used_memory": info.get('used_memory_human', 'unknown'),
                "connected_clients": info.get('connected_clients', 0),
                "backend_metrics": self.get_metrics()
            }

        except Exception as e:
            logger.error(f"Error getting Redis stats: {e}")
            return {"error": str(e)}