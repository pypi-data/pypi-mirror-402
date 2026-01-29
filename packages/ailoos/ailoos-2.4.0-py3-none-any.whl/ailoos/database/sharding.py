"""
Database Sharding Implementation para AILOOS

Implementa sharding horizontal completo con:
- User data sharding
- Transaction history partitioning
- Cross-shard queries optimization
- Shard management automático
"""

import hashlib
import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import threading
import random

logger = logging.getLogger(__name__)


class ShardStrategy(Enum):
    """Estrategias de sharding disponibles."""
    HASH_BASED = "hash_based"          # Sharding basado en hash
    RANGE_BASED = "range_based"        # Sharding basado en rangos
    LIST_BASED = "list_based"          # Sharding basado en listas
    CONSISTENT_HASHING = "consistent"  # Consistent hashing


class ShardStatus(Enum):
    """Estados de un shard."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    FAILED = "failed"
    RECOVERING = "recovering"


@dataclass
class Shard:
    """Representa un shard de base de datos."""
    shard_id: str
    shard_key_range: Tuple[Any, Any]  # (min, max) para range-based
    connection_string: str
    status: ShardStatus = ShardStatus.ACTIVE
    weight: int = 1  # Para weighted distribution
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        """Verificar si el shard está activo."""
        return self.status == ShardStatus.ACTIVE

    @property
    def is_available(self) -> bool:
        """Verificar si el shard está disponible."""
        return self.status in [ShardStatus.ACTIVE, ShardStatus.MAINTENANCE]


@dataclass
class ShardMap:
    """Mapa de shards para una tabla/colección."""
    table_name: str
    strategy: ShardStrategy
    shards: Dict[str, Shard] = field(default_factory=dict)
    shard_key_column: str = "id"
    hash_function: Callable = lambda x: int(hashlib.md5(str(x).encode()).hexdigest(), 16)

    def get_shard_for_key(self, key: Any) -> Optional[Shard]:
        """Obtener shard para una clave específica."""
        if self.strategy == ShardStrategy.HASH_BASED:
            return self._get_hash_based_shard(key)
        elif self.strategy == ShardStrategy.RANGE_BASED:
            return self._get_range_based_shard(key)
        elif self.strategy == ShardStrategy.LIST_BASED:
            return self._get_list_based_shard(key)
        elif self.strategy == ShardStrategy.CONSISTENT_HASHING:
            return self._get_consistent_hash_shard(key)
        else:
            return None

    def _get_hash_based_shard(self, key: Any) -> Optional[Shard]:
        """Sharding basado en hash."""
        hash_value = self.hash_function(key)
        active_shards = [s for s in self.shards.values() if s.is_active]

        if not active_shards:
            return None

        # Distribución uniforme usando hash
        shard_index = hash_value % len(active_shards)
        return active_shards[shard_index]

    def _get_range_based_shard(self, key: Any) -> Optional[Shard]:
        """Sharding basado en rangos."""
        for shard in self.shards.values():
            min_val, max_val = shard.shard_key_range
            if min_val <= key <= max_val and shard.is_active:
                return shard
        return None

    def _get_list_based_shard(self, key: Any) -> Optional[Shard]:
        """Sharding basado en listas."""
        # Para este ejemplo, usamos el primer shard activo
        # En implementación real, tendría listas específicas
        active_shards = [s for s in self.shards.values() if s.is_active]
        return active_shards[0] if active_shards else None

    def _get_consistent_hash_shard(self, key: Any) -> Optional[Shard]:
        """Consistent hashing (simplificado)."""
        hash_value = self.hash_function(key)
        active_shards = sorted([s for s in self.shards.values() if s.is_active],
                              key=lambda s: self.hash_function(s.shard_id))

        if not active_shards:
            return None

        # Encontrar el shard más cercano en el círculo
        for shard in active_shards:
            if hash_value <= self.hash_function(shard.shard_id):
                return shard

        # Wrap around
        return active_shards[0]

    def add_shard(self, shard: Shard):
        """Añadir un nuevo shard."""
        self.shards[shard.shard_id] = shard
        logger.info(f"Added shard {shard.shard_id} to {self.table_name}")

    def remove_shard(self, shard_id: str):
        """Remover un shard."""
        if shard_id in self.shards:
            del self.shards[shard_id]
            logger.info(f"Removed shard {shard_id} from {self.table_name}")

    def get_active_shards(self) -> List[Shard]:
        """Obtener shards activos."""
        return [s for s in self.shards.values() if s.is_active]


class ShardManager:
    """
    Gestor central de sharding para múltiples tablas.

    Características:
    - Sharding automático por tabla
    - Rebalancing dinámico
    - Health monitoring
    - Failover automático
    """

    def __init__(self):
        self.shard_maps: Dict[str, ShardMap] = {}
        self.shard_health_monitor = ShardHealthMonitor()
        self.rebalancer = ShardRebalancer(self)

    def create_shard_map(self, table_name: str, strategy: ShardStrategy,
                        shard_key_column: str = "id", num_shards: int = 4) -> ShardMap:
        """Crear un mapa de shards para una tabla."""
        shard_map = ShardMap(
            table_name=table_name,
            strategy=strategy,
            shard_key_column=shard_key_column
        )

        # Crear shards iniciales
        for i in range(num_shards):
            shard_id = f"{table_name}_shard_{i}"
            connection_string = f"postgresql://user:pass@shard-{i}.db.example.com:5432/{table_name}"

            if strategy == ShardStrategy.RANGE_BASED:
                # Dividir el rango en partes iguales (ejemplo simplificado)
                min_val = (i * 1000) + 1
                max_val = (i + 1) * 1000
                shard_key_range = (min_val, max_val)
            else:
                shard_key_range = (0, 999999)  # Rango amplio para otros tipos

            shard = Shard(
                shard_id=shard_id,
                shard_key_range=shard_key_range,
                connection_string=connection_string
            )

            shard_map.add_shard(shard)

        self.shard_maps[table_name] = shard_map
        logger.info(f"Created shard map for {table_name} with {num_shards} shards")
        return shard_map

    def get_shard_for_record(self, table_name: str, record: Dict[str, Any]) -> Optional[Shard]:
        """Obtener shard para un registro específico."""
        if table_name not in self.shard_maps:
            return None

        shard_map = self.shard_maps[table_name]
        shard_key = record.get(shard_map.shard_key_column)

        if shard_key is None:
            logger.warning(f"No shard key found in record for {table_name}")
            return None

        return shard_map.get_shard_for_key(shard_key)

    def get_all_shards_for_table(self, table_name: str) -> List[Shard]:
        """Obtener todos los shards para una tabla."""
        if table_name not in self.shard_maps:
            return []
        return list(self.shard_maps[table_name].shards.values())

    def rebalance_shards(self, table_name: str):
        """Rebalancear shards para una tabla."""
        if table_name in self.shard_maps:
            self.rebalancer.rebalance_table(table_name)

    async def monitor_shard_health(self):
        """Monitorear salud de todos los shards."""
        await self.shard_health_monitor.monitor_all_shards(self.shard_maps)

    def get_shard_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de sharding."""
        stats = {
            'total_tables': len(self.shard_maps),
            'total_shards': sum(len(sm.shards) for sm in self.shard_maps.values()),
            'active_shards': sum(len(sm.get_active_shards()) for sm in self.shard_maps.values()),
            'tables': {}
        }

        for table_name, shard_map in self.shard_maps.items():
            active_shards = shard_map.get_active_shards()
            stats['tables'][table_name] = {
                'strategy': shard_map.strategy.value,
                'total_shards': len(shard_map.shards),
                'active_shards': len(active_shards),
                'shard_key_column': shard_map.shard_key_column
            }

        return stats


class ShardHealthMonitor:
    """Monitor de salud para shards."""

    def __init__(self):
        self.health_checks: Dict[str, Dict[str, Any]] = {}
        self.check_interval = 30  # segundos

    async def monitor_all_shards(self, shard_maps: Dict[str, ShardMap]):
        """Monitorear salud de todos los shards."""
        while True:
            try:
                for table_name, shard_map in shard_maps.items():
                    for shard_id, shard in shard_map.shards.items():
                        health = await self._check_shard_health(shard)
                        self.health_checks[f"{table_name}.{shard_id}"] = health

                        # Actualizar status del shard basado en salud
                        if not health['healthy']:
                            shard.status = ShardStatus.FAILED
                        elif health['response_time'] > 1000:  # > 1 segundo
                            shard.status = ShardStatus.DEGRADED
                        else:
                            shard.status = ShardStatus.ACTIVE

                await asyncio.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Error in shard health monitoring: {e}")
                await asyncio.sleep(self.check_interval)

    async def _check_shard_health(self, shard: Shard) -> Dict[str, Any]:
        """Verificar salud de un shard específico."""
        start_time = time.time()

        try:
            # Simular health check (en producción sería una query real)
            await asyncio.sleep(0.01)  # Simular latencia de red

            # Simular algunos fallos aleatorios
            if random.random() < 0.05:  # 5% de probabilidad de fallo
                raise Exception("Simulated shard failure")

            response_time = (time.time() - start_time) * 1000  # ms

            return {
                'healthy': True,
                'response_time': response_time,
                'timestamp': datetime.now(),
                'error': None
            }

        except Exception as e:
            response_time = (time.time() - start_time) * 1000

            return {
                'healthy': False,
                'response_time': response_time,
                'timestamp': datetime.now(),
                'error': str(e)
            }


class ShardRebalancer:
    """Rebalanceador de shards para distribución óptima."""

    def __init__(self, shard_manager: ShardManager):
        self.shard_manager = shard_manager

    def rebalance_table(self, table_name: str):
        """Rebalancear shards para una tabla."""
        if table_name not in self.shard_manager.shard_maps:
            return

        shard_map = self.shard_manager.shard_maps[table_name]
        logger.info(f"Starting rebalancing for {table_name}")

        # Estrategia simple: redistribuir rangos equitativamente
        if shard_map.strategy == ShardStrategy.RANGE_BASED:
            self._rebalance_range_based(shard_map)
        elif shard_map.strategy == ShardStrategy.HASH_BASED:
            self._rebalance_hash_based(shard_map)

        logger.info(f"Rebalancing completed for {table_name}")

    def _rebalance_range_based(self, shard_map: ShardMap):
        """Rebalancear sharding basado en rangos."""
        active_shards = shard_map.get_active_shards()
        if len(active_shards) == 0:
            return

        # Redistribuir rangos equitativamente
        total_range = 1000000  # Ejemplo: IDs de 1 a 1,000,000
        range_per_shard = total_range // len(active_shards)

        for i, shard in enumerate(active_shards):
            min_val = (i * range_per_shard) + 1
            max_val = (i + 1) * range_per_shard if i < len(active_shards) - 1 else total_range
            shard.shard_key_range = (min_val, max_val)

    def _rebalance_hash_based(self, shard_map: ShardMap):
        """Rebalancear sharding basado en hash."""
        # Para hash-based, solo necesitamos asegurar que todos los shards estén activos
        # La distribución se maneja automáticamente por el hash
        active_shards = shard_map.get_active_shards()
        logger.info(f"Hash-based rebalancing: {len(active_shards)} active shards")


class CrossShardQueryOptimizer:
    """
    Optimizador de queries cross-shard.

    Características:
    - Query planning inteligente
    - Parallel execution
    - Result aggregation
    - Performance optimization
    """

    def __init__(self, shard_manager: ShardManager):
        self.shard_manager = shard_manager

    async def execute_cross_shard_query(self, table_name: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Ejecutar query que involucra múltiples shards."""
        if table_name not in self.shard_manager.shard_maps:
            return []

        shard_map = self.shard_manager.shard_maps[table_name]

        # Determinar qué shards necesitan ser consultados
        relevant_shards = self._determine_relevant_shards(shard_map, query)

        if not relevant_shards:
            return []

        # Ejecutar queries en paralelo
        tasks = []
        for shard in relevant_shards:
            task = self._execute_query_on_shard(shard, query)
            tasks.append(task)

        # Esperar resultados
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Agregar resultados
        aggregated_results = []
        for result in results:
            if isinstance(result, list):
                aggregated_results.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Query failed on shard: {result}")

        return aggregated_results

    def _determine_relevant_shards(self, shard_map: ShardMap, query: Dict[str, Any]) -> List[Shard]:
        """Determinar qué shards son relevantes para la query."""
        # Análisis simple: si hay filtro por shard_key, usar solo ese shard
        shard_key_column = shard_map.shard_key_column

        if shard_key_column in query.get('filters', {}):
            shard_key_value = query['filters'][shard_key_column]
            shard = shard_map.get_shard_for_key(shard_key_value)
            return [shard] if shard else []

        # Si no hay filtro específico, consultar todos los shards activos
        return shard_map.get_active_shards()

    async def _execute_query_on_shard(self, shard: Shard, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Ejecutar query en un shard específico."""
        try:
            # Simular ejecución de query (en producción sería una conexión real a la DB)
            await asyncio.sleep(0.05)  # Simular latencia

            # Generar resultados simulados
            num_results = random.randint(0, 100)
            results = []

            for i in range(num_results):
                result = {
                    'id': f"{shard.shard_id}_record_{i}",
                    'shard_id': shard.shard_id,
                    'data': f"Sample data from {shard.shard_id}",
                    'timestamp': datetime.now().isoformat()
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Query execution failed on {shard.shard_id}: {e}")
            return []


# Funciones de conveniencia para sharding de usuarios y transacciones

def create_user_sharding_config() -> ShardMap:
    """Crear configuración de sharding para usuarios."""
    return ShardMap(
        table_name="users",
        strategy=ShardStrategy.HASH_BASED,
        shard_key_column="user_id"
    )


def create_transaction_sharding_config() -> ShardMap:
    """Crear configuración de sharding para historial de transacciones."""
    return ShardMap(
        table_name="transactions",
        strategy=ShardStrategy.RANGE_BASED,
        shard_key_column="timestamp"
    )


async def initialize_database_sharding() -> ShardManager:
    """Inicializar sharding completo de base de datos."""
    manager = ShardManager()

    # Crear sharding para usuarios
    user_sharding = manager.create_shard_map(
        table_name="users",
        strategy=ShardStrategy.HASH_BASED,
        shard_key_column="user_id",
        num_shards=8
    )

    # Crear sharding para transacciones
    transaction_sharding = manager.create_shard_map(
        table_name="transactions",
        strategy=ShardStrategy.RANGE_BASED,
        shard_key_column="timestamp",
        num_shards=12  # Más shards para transacciones (más datos)
    )

    # Crear sharding para sesiones federated learning
    session_sharding = manager.create_shard_map(
        table_name="federated_sessions",
        strategy=ShardStrategy.HASH_BASED,
        shard_key_column="session_id",
        num_shards=4
    )

    # Iniciar monitoring de salud
    asyncio.create_task(manager.monitor_shard_health())

    logger.info("Database sharding initialized successfully")
    return manager


# Ejemplo de uso
async def example_sharding_usage():
    """Ejemplo de uso del sistema de sharding."""
    # Inicializar sharding
    shard_manager = await initialize_database_sharding()

    # Crear query optimizer
    query_optimizer = CrossShardQueryOptimizer(shard_manager)

    # Ejemplo: buscar usuario específico (single shard)
    user_query = {
        'table': 'users',
        'filters': {'user_id': 'user_12345'},
        'limit': 1
    }

    user_results = await query_optimizer.execute_cross_shard_query('users', user_query)
    print(f"User query results: {len(user_results)} records")

    # Ejemplo: buscar transacciones en un rango de tiempo (multiple shards)
    transaction_query = {
        'table': 'transactions',
        'filters': {
            'timestamp': {'$gte': '2024-01-01', '$lt': '2024-02-01'}
        },
        'limit': 1000
    }

    transaction_results = await query_optimizer.execute_cross_shard_query('transactions', transaction_query)
    print(f"Transaction query results: {len(transaction_results)} records")

    # Obtener estadísticas
    stats = shard_manager.get_shard_stats()
    print(f"Sharding stats: {stats}")

    return shard_manager