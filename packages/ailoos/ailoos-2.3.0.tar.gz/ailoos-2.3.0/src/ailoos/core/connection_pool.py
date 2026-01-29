"""
Connection Pool Manager for AILOOS

Advanced connection pooling for PostgreSQL, Redis, and IPFS with:
- Connection health monitoring
- Automatic reconnection
- Resource limits and quotas
- Performance metrics
- Graceful shutdown
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class ConnectionStats:
    """Estadísticas de conexión."""
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)
    use_count: int = 0
    error_count: int = 0
    total_query_time: float = 0.0
    avg_query_time: float = 0.0

    def record_usage(self, query_time: float = 0.0):
        """Registrar uso de conexión."""
        self.last_used = datetime.now()
        self.use_count += 1
        if query_time > 0:
            self.total_query_time += query_time
            self.avg_query_time = self.total_query_time / self.use_count

    def record_error(self):
        """Registrar error de conexión."""
        self.error_count += 1


class ConnectionPool:
    """Base class for connection pools."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pool: Dict[Any, ConnectionStats] = {}
        self.max_connections = config.get('max_connections', 10)
        self.min_connections = config.get('min_connections', 1)
        self.max_idle_time = config.get('max_idle_time', 300)  # 5 minutes
        self.health_check_interval = config.get('health_check_interval', 60)
        self._lock = asyncio.Lock()
        self._health_check_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize the connection pool."""
        await self._create_initial_connections()
        self._start_health_check()

    async def _create_initial_connections(self):
        """Create initial connections."""
        for _ in range(self.min_connections):
            try:
                conn = await self._create_connection()
                self.pool[conn] = ConnectionStats()
            except Exception as e:
                logger.error(f"Failed to create initial connection: {e}")

    def _start_health_check(self):
        """Start background health check task."""
        if self._health_check_task is None:
            self._health_check_task = asyncio.create_task(self._health_check_loop())

    async def _health_check_loop(self):
        """Background health check loop."""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_health_check()
            except Exception as e:
                logger.error(f"Health check error: {e}")

    async def _perform_health_check(self):
        """Perform health check on all connections."""
        async with self._lock:
            to_remove = []
            now = datetime.now()

            for conn, stats in self.pool.items():
                # Check idle time
                if (now - stats.last_used).total_seconds() > self.max_idle_time:
                    to_remove.append(conn)
                    continue

                # Check connection health
                if not await self._is_connection_healthy(conn):
                    to_remove.append(conn)
                    continue

            # Remove unhealthy connections
            for conn in to_remove:
                await self._close_connection(conn)
                del self.pool[conn]

            # Ensure minimum connections
            current_count = len(self.pool)
            if current_count < self.min_connections:
                needed = self.min_connections - current_count
                for _ in range(needed):
                    try:
                        conn = await self._create_connection()
                        self.pool[conn] = ConnectionStats()
                    except Exception as e:
                        logger.error(f"Failed to create replacement connection: {e}")

    async def get_connection(self) -> Any:
        """Get a connection from the pool."""
        async with self._lock:
            # Try to find an available connection
            for conn, stats in self.pool.items():
                if await self._is_connection_healthy(conn):
                    stats.record_usage()
                    return conn

            # Create new connection if under limit
            if len(self.pool) < self.max_connections:
                try:
                    conn = await self._create_connection()
                    self.pool[conn] = ConnectionStats()
                    return conn
                except Exception as e:
                    logger.error(f"Failed to create new connection: {e}")
                    raise

            # Pool exhausted
            raise RuntimeError(f"Connection pool exhausted (max: {self.max_connections})")

    async def return_connection(self, conn: Any):
        """Return a connection to the pool."""
        async with self._lock:
            if conn in self.pool:
                # Connection is still valid, just update stats
                pass
            else:
                # Connection not in pool, close it
                await self._close_connection(conn)

    async def close_all(self):
        """Close all connections in the pool."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        async with self._lock:
            for conn in self.pool:
                await self._close_connection(conn)
            self.pool.clear()

    # Abstract methods to be implemented by subclasses
    async def _create_connection(self) -> Any:
        """Create a new connection."""
        raise NotImplementedError

    async def _close_connection(self, conn: Any):
        """Close a connection."""
        raise NotImplementedError

    async def _is_connection_healthy(self, conn: Any) -> bool:
        """Check if a connection is healthy."""
        raise NotImplementedError


class PostgreSQLConnectionPool(ConnectionPool):
    """PostgreSQL connection pool with advanced features."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.connection_string = config['connection_string']

        # PostgreSQL specific settings
        self.statement_timeout = config.get('statement_timeout', 30000)  # 30 seconds
        self.idle_in_transaction_session_timeout = config.get('idle_in_transaction_session_timeout', 60000)  # 1 minute

    async def _create_connection(self):
        """Create a new PostgreSQL connection."""
        try:
            # Import here to avoid circular imports
            import asyncpg

            conn = await asyncpg.connect(
                self.connection_string,
                statement_cache_size=100,
                max_cached_statement_lifetime=300,
                command_timeout=self.statement_timeout / 1000,  # Convert to seconds
                server_settings={
                    'idle_in_transaction_session_timeout': str(self.idle_in_transaction_session_timeout)
                }
            )

            # Set up connection
            await conn.set_type_codec(
                'json',
                encoder=lambda x: json.dumps(x),
                decoder=lambda x: json.loads(x),
                schema='pg_catalog'
            )

            return conn

        except Exception as e:
            logger.error(f"Failed to create PostgreSQL connection: {e}")
            raise

    async def _close_connection(self, conn):
        """Close a PostgreSQL connection."""
        try:
            await conn.close()
        except Exception as e:
            logger.error(f"Error closing PostgreSQL connection: {e}")

    async def _is_connection_healthy(self, conn) -> bool:
        """Check if PostgreSQL connection is healthy."""
        try:
            # Simple health check query
            result = await conn.fetchval("SELECT 1")
            return result == 1
        except Exception as e:
            logger.warning(f"PostgreSQL connection health check failed: {e}")
            return False


class RedisConnectionPool(ConnectionPool):
    """Redis connection pool with advanced features."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.host = config['host']
        self.port = config['port']
        self.db = config.get('db', 0)
        self.password = config.get('password')
        self.socket_timeout = config.get('socket_timeout', 5)
        self.socket_connect_timeout = config.get('socket_connect_timeout', 5)

    async def _create_connection(self):
        """Create a new Redis connection."""
        try:
            # Import here to avoid circular imports
            import redis.asyncio as redis

            conn = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_connect_timeout,
                retry_on_timeout=True,
                max_connections=self.max_connections,
                decode_responses=True
            )

            # Test connection
            await conn.ping()
            return conn

        except Exception as e:
            logger.error(f"Failed to create Redis connection: {e}")
            raise

    async def _close_connection(self, conn):
        """Close a Redis connection."""
        try:
            await conn.close()
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")

    async def _is_connection_healthy(self, conn) -> bool:
        """Check if Redis connection is healthy."""
        try:
            result = await conn.ping()
            return result is not None
        except Exception as e:
            logger.warning(f"Redis connection health check failed: {e}")
            return False


class IPFSConnectionPool:
    """IPFS connection manager with retry logic."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_host = config['api_host']
        self.api_port = config['api_port']
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 1.0)
        self._client = None
        self._last_health_check = 0
        self._health_check_interval = 60

    async def get_client(self):
        """Get IPFS client with automatic retry."""
        try:
            import aiohttp
        except ImportError:
            raise RuntimeError("aiohttp is required for IPFS connections")

        if self._client is None or not await self._is_healthy():
            self._client = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                connector=aiohttp.TCPConnector(limit=10, ttl_dns_cache=300)
            )

        return self._client

    async def _is_healthy(self) -> bool:
        """Check if IPFS connection is healthy."""
        now = time.time()
        if now - self._last_health_check < self._health_check_interval:
            return True

        self._last_health_check = now

        try:
            import aiohttp
            client = await self.get_client()
            url = f"http://{self.api_host}:{self.api_port}/api/v0/id"

            async with client.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                return response.status == 200

        except Exception as e:
            logger.warning(f"IPFS health check failed: {e}")
            return False

    async def execute_with_retry(self, operation: Callable, *args, **kwargs):
        """Execute IPFS operation with retry logic."""
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                client = await self.get_client()
                return await operation(client, *args, **kwargs)

            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    logger.warning(f"IPFS operation failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"IPFS operation failed after {self.max_retries} attempts: {e}")

        raise last_exception

    async def close(self):
        """Close IPFS client."""
        if self._client:
            await self._client.close()
            self._client = None


class ConnectionPoolManager:
    """Central manager for all connection pools."""

    def __init__(self):
        self.pools: Dict[str, ConnectionPool] = {}
        self.ipfs_pool: Optional[IPFSConnectionPool] = None

    async def initialize_from_config(self, config):
        """Initialize all connection pools from AILOOS config."""

        # PostgreSQL pool
        if hasattr(config, 'database'):
            db_config = {
                'max_connections': config.database.connection_pool_size,
                'min_connections': max(1, config.database.connection_pool_size // 4),
                'max_idle_time': 300,
                'health_check_interval': 60,
                'connection_string': config.database.connection_string,
                'statement_timeout': 30000,
                'idle_in_transaction_session_timeout': 60000
            }
            self.pools['postgresql'] = PostgreSQLConnectionPool(db_config)
            await self.pools['postgresql'].initialize()

        # Redis pool
        if hasattr(config, 'redis'):
            redis_config = {
                'max_connections': config.redis.max_connections,
                'min_connections': max(1, config.redis.max_connections // 4),
                'max_idle_time': 300,
                'health_check_interval': 30,
                'host': config.redis.host,
                'port': config.redis.port,
                'db': getattr(config.redis, 'db', 0),
                'password': config.redis.password,
                'socket_timeout': config.redis.socket_timeout,
                'socket_connect_timeout': config.redis.socket_connect_timeout
            }
            self.pools['redis'] = RedisConnectionPool(redis_config)
            await self.pools['redis'].initialize()

        # IPFS connection manager
        if hasattr(config, 'ipfs'):
            ipfs_config = {
                'api_host': config.ipfs.api_host,
                'api_port': config.ipfs.api_port,
                'timeout': config.ipfs.timeout,
                'max_retries': 3,
                'retry_delay': 1.0
            }
            self.ipfs_pool = IPFSConnectionPool(ipfs_config)

    @asynccontextmanager
    async def get_postgresql_connection(self):
        """Get a PostgreSQL connection from the pool."""
        pool = self.pools.get('postgresql')
        if not pool:
            raise RuntimeError("PostgreSQL connection pool not initialized")

        conn = await pool.get_connection()
        try:
            yield conn
        finally:
            await pool.return_connection(conn)

    @asynccontextmanager
    async def get_redis_connection(self):
        """Get a Redis connection from the pool."""
        pool = self.pools.get('redis')
        if not pool:
            raise RuntimeError("Redis connection pool not initialized")

        conn = await pool.get_connection()
        try:
            yield conn
        finally:
            await pool.return_connection(conn)

    def get_ipfs_client(self):
        """Get IPFS client."""
        if not self.ipfs_pool:
            raise RuntimeError("IPFS connection pool not initialized")
        return self.ipfs_pool

    async def get_pool_stats(self) -> Dict[str, Any]:
        """Get statistics for all connection pools."""
        stats = {}

        for name, pool in self.pools.items():
            pool_stats = {
                'active_connections': len(pool.pool),
                'max_connections': pool.max_connections,
                'min_connections': pool.min_connections,
                'connections': []
            }

            for conn, conn_stats in pool.pool.items():
                pool_stats['connections'].append({
                    'created_at': conn_stats.created_at.isoformat(),
                    'last_used': conn_stats.last_used.isoformat(),
                    'use_count': conn_stats.use_count,
                    'error_count': conn_stats.error_count,
                    'avg_query_time': conn_stats.avg_query_time
                })

            stats[name] = pool_stats

        return stats

    async def close_all(self):
        """Close all connection pools."""
        for pool in self.pools.values():
            await pool.close_all()

        if self.ipfs_pool:
            await self.ipfs_pool.close()


# Global connection pool manager instance
_connection_manager: Optional[ConnectionPoolManager] = None


async def get_connection_manager() -> ConnectionPoolManager:
    """Get the global connection pool manager."""
    global _connection_manager

    if _connection_manager is None:
        _connection_manager = ConnectionPoolManager()

        # Initialize from current config
        from .config import get_config
        config = get_config()
        await _connection_manager.initialize_from_config(config)

    return _connection_manager


# Convenience functions for easy access
async def get_postgresql_connection():
    """Get a PostgreSQL connection (context manager)."""
    manager = await get_connection_manager()
    return manager.get_postgresql_connection()


async def get_redis_connection():
    """Get a Redis connection (context manager)."""
    manager = await get_connection_manager()
    return manager.get_redis_connection()


def get_ipfs_client():
    """Get IPFS client."""
    if _connection_manager is None:
        raise RuntimeError("Connection manager not initialized. Call get_connection_manager() first.")
    return _connection_manager.get_ipfs_client()