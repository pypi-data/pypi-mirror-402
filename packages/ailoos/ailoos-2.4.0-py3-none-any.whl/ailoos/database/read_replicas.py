"""
Read Replicas Implementation para AILOOS

Implementa sistema completo de read replicas con:
- Global read distribution
- Replication lag monitoring
- Failover procedures automáticos
- Load balancing inteligente
"""

import asyncio
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
import statistics
import json

logger = logging.getLogger(__name__)


class ReplicaRole(Enum):
    """Roles de réplicas."""
    PRIMARY = "primary"      # Master/Primary database
    REPLICA = "replica"      # Read replica
    STANDBY = "standby"      # Hot standby (puede ser promovido)


class ReplicaStatus(Enum):
    """Estados de una réplica."""
    HEALTHY = "healthy"
    LAGGING = "lagging"
    UNHEALTHY = "unhealthy"
    PROMOTING = "promoting"
    DEMOTING = "demoting"
    OFFLINE = "offline"


@dataclass
class ReadReplica:
    """Representa una read replica."""
    replica_id: str
    host: str
    port: int
    region: str
    role: ReplicaRole = ReplicaRole.REPLICA
    status: ReplicaStatus = ReplicaStatus.HEALTHY
    replication_lag: float = 0.0  # segundos
    connection_pool_size: int = 10
    max_connections: int = 100
    weight: float = 1.0  # Para load balancing weighted
    last_health_check: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_available(self) -> bool:
        """Verificar si la réplica está disponible para reads."""
        return (
            self.status in [ReplicaStatus.HEALTHY, ReplicaStatus.LAGGING] and
            self.role in [ReplicaRole.PRIMARY, ReplicaRole.REPLICA]
        )

    @property
    def connection_string(self) -> str:
        """String de conexión."""
        return f"postgresql://user:pass@{self.host}:{self.port}/ailoos"

    @property
    def is_primary(self) -> bool:
        """Verificar si es la primary."""
        return self.role == ReplicaRole.PRIMARY

    def update_health(self, lag_seconds: float, response_time: float):
        """Actualizar métricas de salud."""
        self.replication_lag = lag_seconds
        self.last_health_check = datetime.now()

        # Determinar status basado en lag
        if lag_seconds > 300:  # 5 minutos
            self.status = ReplicaStatus.UNHEALTHY
        elif lag_seconds > 60:  # 1 minuto
            self.status = ReplicaStatus.LAGGING
        else:
            self.status = ReplicaStatus.HEALTHY

        # Actualizar metadata
        self.metadata.update({
            'last_response_time': response_time,
            'last_check': self.last_health_check.isoformat()
        })


@dataclass
class ReadDistributionStats:
    """Estadísticas de distribución de reads."""
    total_reads: int = 0
    reads_by_replica: Dict[str, int] = field(default_factory=dict)
    avg_response_time: float = 0.0
    response_times: List[float] = field(default_factory=list)
    failover_events: int = 0
    last_failover: Optional[datetime] = None

    def record_read(self, replica_id: str, response_time: float):
        """Registrar una operación de read."""
        self.total_reads += 1
        self.reads_by_replica[replica_id] = self.reads_by_replica.get(replica_id, 0) + 1
        self.response_times.append(response_time)

        # Mantener solo las últimas 1000 mediciones
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]

        # Actualizar promedio
        self.avg_response_time = statistics.mean(self.response_times) if self.response_times else 0

    def get_distribution_percentages(self) -> Dict[str, float]:
        """Obtener porcentajes de distribución."""
        if self.total_reads == 0:
            return {}

        return {
            replica_id: (count / self.total_reads) * 100
            for replica_id, count in self.reads_by_replica.items()
        }


class ReadReplicaManager:
    """
    Gestor de read replicas con distribución global inteligente.

    Características:
    - Load balancing automático
    - Health monitoring continuo
    - Failover automático
    - Latency-based routing
    """

    def __init__(self):
        self.replicas: Dict[str, ReadReplica] = {}
        self.primary_replica: Optional[ReadReplica] = None
        self.stats = ReadDistributionStats()
        self.health_monitor = ReplicaHealthMonitor()
        self.failover_manager = ReplicaFailoverManager(self)

    def add_replica(self, replica: ReadReplica):
        """Añadir una nueva réplica."""
        self.replicas[replica.replica_id] = replica

        if replica.is_primary:
            self.primary_replica = replica

        logger.info(f"Added replica {replica.replica_id} in region {replica.region}")

    def remove_replica(self, replica_id: str):
        """Remover una réplica."""
        if replica_id in self.replicas:
            replica = self.replicas[replica_id]
            if replica.is_primary:
                self.primary_replica = None
            del self.replicas[replica_id]
            logger.info(f"Removed replica {replica_id}")

    def get_optimal_replica(self, preferred_region: Optional[str] = None,
                           query_type: str = "read") -> Optional[ReadReplica]:
        """Obtener la réplica óptima para una consulta."""

        if query_type == "write":
            # Writes siempre van al primary
            return self.primary_replica if self.primary_replica and self.primary_replica.is_available else None

        # Para reads, usar algoritmo de selección inteligente
        available_replicas = [r for r in self.replicas.values() if r.is_available]

        if not available_replicas:
            return None

        if preferred_region:
            # Priorizar réplicas en la región preferida
            regional_replicas = [r for r in available_replicas if r.region == preferred_region]
            if regional_replicas:
                available_replicas = regional_replicas

        # Seleccionar basado en múltiples factores
        scored_replicas = []
        for replica in available_replicas:
            score = self._calculate_replica_score(replica)
            scored_replicas.append((replica, score))

        # Seleccionar la réplica con mejor score
        optimal_replica = max(scored_replicas, key=lambda x: x[1])[0]

        logger.debug(f"Selected optimal replica: {optimal_replica.replica_id} (score: {max(scored_replicas, key=lambda x: x[1])[1]:.2f})")
        return optimal_replica

    def _calculate_replica_score(self, replica: ReadReplica) -> float:
        """Calcular score para selección de réplica."""
        base_score = 100.0

        # Penalización por lag de replicación
        lag_penalty = min(replica.replication_lag / 10, 50)  # Máximo 50 puntos de penalización

        # Bonus por región (simulado - en producción usaría geolocalización real)
        region_bonus = 10 if replica.region == "us-central1" else 0

        # Penalización por uso actual (simulado)
        usage_penalty = random.uniform(0, 10)  # Simular carga variable

        # Factor de peso configurado
        weight_factor = replica.weight

        final_score = (base_score - lag_penalty + region_bonus - usage_penalty) * weight_factor
        return max(final_score, 0)  # No scores negativos

    async def execute_read_query(self, query: str, preferred_region: Optional[str] = None) -> Dict[str, Any]:
        """Ejecutar query de read usando la réplica óptima."""
        start_time = time.time()

        replica = self.get_optimal_replica(preferred_region, "read")
        if not replica:
            raise Exception("No available replicas for read query")

        try:
            # Simular ejecución de query
            result = await self._execute_query_on_replica(replica, query)

            response_time = time.time() - start_time
            self.stats.record_read(replica.replica_id, response_time)

            return {
                'result': result,
                'replica_used': replica.replica_id,
                'region': replica.region,
                'response_time': response_time,
                'replication_lag': replica.replication_lag
            }

        except Exception as e:
            logger.error(f"Query failed on replica {replica.replica_id}: {e}")
            # Marcar réplica como potencialmente unhealthy
            replica.status = ReplicaStatus.UNHEALTHY
            raise

    async def execute_write_query(self, query: str) -> Dict[str, Any]:
        """Ejecutar query de write en el primary."""
        start_time = time.time()

        if not self.primary_replica or not self.primary_replica.is_available:
            raise Exception("Primary replica not available for write query")

        try:
            result = await self._execute_query_on_replica(self.primary_replica, query)
            response_time = time.time() - start_time

            return {
                'result': result,
                'replica_used': self.primary_replica.replica_id,
                'response_time': response_time
            }

        except Exception as e:
            logger.error(f"Write query failed on primary: {e}")
            raise

    async def _execute_query_on_replica(self, replica: ReadReplica, query: str) -> List[Dict[str, Any]]:
        """Ejecutar query en una réplica específica."""
        # Simular latencia de red + query execution
        network_latency = random.uniform(0.01, 0.05)  # 10-50ms
        query_time = random.uniform(0.001, 0.01)     # 1-10ms

        await asyncio.sleep(network_latency + query_time)

        # Simular resultados
        num_results = random.randint(0, 100)
        results = []

        for i in range(num_results):
            results.append({
                'id': f"record_{i}",
                'data': f"Sample data from {replica.replica_id}",
                'timestamp': datetime.now().isoformat(),
                'replica': replica.replica_id
            })

        return results

    async def start_health_monitoring(self):
        """Iniciar monitoring de salud de réplicas."""
        await self.health_monitor.start_monitoring(self.replicas)

    def get_replica_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de todas las réplicas."""
        stats = {
            'total_replicas': len(self.replicas),
            'available_replicas': len([r for r in self.replicas.values() if r.is_available]),
            'regions': list(set(r.region for r in self.replicas.values())),
            'replicas': {}
        }

        for replica_id, replica in self.replicas.values():
            stats['replicas'][replica_id] = {
                'region': replica.region,
                'role': replica.role.value,
                'status': replica.status.value,
                'replication_lag': replica.replication_lag,
                'last_health_check': replica.last_health_check.isoformat() if replica.last_health_check else None,
                'weight': replica.weight
            }

        return stats

    def get_distribution_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de distribución de carga."""
        return {
            'total_reads': self.stats.total_reads,
            'avg_response_time': round(self.stats.avg_response_time, 3),
            'distribution_percentages': self.stats.get_distribution_percentages(),
            'failover_events': self.stats.failover_events,
            'last_failover': self.stats.last_failover.isoformat() if self.stats.last_failover else None
        }


class ReplicaHealthMonitor:
    """Monitor de salud para read replicas."""

    def __init__(self):
        self.monitoring_interval = 30  # segundos
        self.max_lag_threshold = 300   # 5 minutos máximo lag aceptable

    async def start_monitoring(self, replicas: Dict[str, ReadReplica]):
        """Iniciar monitoring continuo."""
        while True:
            try:
                await self._check_all_replicas_health(replicas)
                await asyncio.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Error in replica health monitoring: {e}")
                await asyncio.sleep(self.monitoring_interval)

    async def _check_all_replicas_health(self, replicas: Dict[str, ReadReplica]):
        """Verificar salud de todas las réplicas."""
        tasks = []

        for replica in replicas.values():
            task = self._check_replica_health(replica)
            tasks.append(task)

        # Ejecutar verificaciones en paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            replica_id = list(replicas.keys())[i]
            if isinstance(result, Exception):
                logger.warning(f"Health check failed for {replica_id}: {result}")
            else:
                lag, response_time = result
                replicas[replica_id].update_health(lag, response_time)

    async def _check_replica_health(self, replica: ReadReplica) -> Tuple[float, float]:
        """Verificar salud de una réplica específica."""
        start_time = time.time()

        try:
            # Simular health check (en producción sería una query real)
            await asyncio.sleep(0.01)  # Simular latencia

            # Simular lag de replicación
            if replica.is_primary:
                replication_lag = 0.0  # Primary no tiene lag
            else:
                # Lag simulado: 0-300 segundos
                replication_lag = random.uniform(0, 300)

            response_time = time.time() - start_time

            return replication_lag, response_time

        except Exception as e:
            # En caso de error, asumir lag máximo
            response_time = time.time() - start_time
            return self.max_lag_threshold + 60, response_time  # Lag alto + tiempo de respuesta


class ReplicaFailoverManager:
    """Gestor de failover para read replicas."""

    def __init__(self, replica_manager: ReadReplicaManager):
        self.replica_manager = replica_manager
        self.failover_history: List[Dict[str, Any]] = []
        self.failover_lock = asyncio.Lock()

    async def handle_primary_failure(self):
        """Manejar fallo del primary y promover una réplica."""
        async with self.failover_lock:
            logger.warning("Primary replica failure detected, initiating failover...")

            # Encontrar la mejor réplica para promover
            candidates = [r for r in self.replica_manager.replicas.values()
                         if r.role == ReplicaRole.REPLICA and r.status == ReplicaStatus.HEALTHY]

            if not candidates:
                logger.error("No healthy replicas available for failover!")
                return False

            # Seleccionar candidate con menor lag
            new_primary = min(candidates, key=lambda r: r.replication_lag)

            # Simular proceso de promoción
            logger.info(f"Promoting replica {new_primary.replica_id} to primary...")
            new_primary.status = ReplicaStatus.PROMOTING

            # Simular tiempo de promoción
            await asyncio.sleep(5)

            # Completar promoción
            old_primary = self.replica_manager.primary_replica
            if old_primary:
                old_primary.role = ReplicaRole.STANDBY
                old_primary.status = ReplicaStatus.OFFLINE

            new_primary.role = ReplicaRole.PRIMARY
            new_primary.status = ReplicaStatus.HEALTHY
            self.replica_manager.primary_replica = new_primary

            # Registrar failover
            failover_event = {
                'timestamp': datetime.now().isoformat(),
                'old_primary': old_primary.replica_id if old_primary else None,
                'new_primary': new_primary.replica_id,
                'reason': 'primary_failure',
                'candidates_count': len(candidates)
            }

            self.failover_history.append(failover_event)
            self.replica_manager.stats.failover_events += 1
            self.replica_manager.stats.last_failover = datetime.now()

            logger.info(f"Failover completed: {old_primary.replica_id if old_primary else 'None'} -> {new_primary.replica_id}")
            return True

    async def demote_primary_to_standby(self, new_primary: ReadReplica):
        """Demover primary actual a standby y promover nueva réplica."""
        async with self.failover_lock:
            current_primary = self.replica_manager.primary_replica

            if current_primary:
                logger.info(f"Demoting current primary {current_primary.replica_id} to standby")
                current_primary.status = ReplicaStatus.DEMOTING

                # Simular tiempo de democión
                await asyncio.sleep(2)

                current_primary.role = ReplicaRole.STANDBY
                current_primary.status = ReplicaStatus.HEALTHY

            # Promover nueva réplica
            logger.info(f"Promoting {new_primary.replica_id} to primary")
            new_primary.role = ReplicaRole.PRIMARY
            new_primary.status = ReplicaStatus.HEALTHY
            self.replica_manager.primary_replica = new_primary

    def get_failover_history(self) -> List[Dict[str, Any]]:
        """Obtener historial de failovers."""
        return self.failover_history


# Funciones de conveniencia

def create_global_read_replicas_config() -> List[ReadReplica]:
    """Crear configuración de read replicas globales."""
    replicas = []

    # Primary en US Central
    primary = ReadReplica(
        replica_id="primary-us-central1",
        host="primary.db.us-central1.example.com",
        port=5432,
        region="us-central1",
        role=ReplicaRole.PRIMARY,
        weight=1.0
    )
    replicas.append(primary)

    # Read replicas en múltiples regiones
    regions = [
        ("us-east1", "replica-us-east1"),
        ("us-west1", "replica-us-west1"),
        ("europe-west1", "replica-europe-west1"),
        ("asia-east1", "replica-asia-east1"),
        ("australia-southeast1", "replica-australia-southeast1")
    ]

    for region, replica_id in regions:
        replica = ReadReplica(
            replica_id=replica_id,
            host=f"replica.db.{region}.example.com",
            port=5432,
            region=region,
            role=ReplicaRole.REPLICA,
            weight=0.8  # Slightly lower weight for replicas
        )
        replicas.append(replica)

    return replicas


async def initialize_read_replicas_system() -> ReadReplicaManager:
    """Inicializar sistema completo de read replicas."""
    manager = ReadReplicaManager()

    # Crear configuración global
    replicas = create_global_read_replicas_config()

    # Añadir todas las réplicas
    for replica in replicas:
        manager.add_replica(replica)

    # Iniciar monitoring de salud
    asyncio.create_task(manager.start_health_monitoring())

    logger.info(f"Read replicas system initialized with {len(replicas)} replicas across {len(set(r.region for r in replicas))} regions")

    return manager


async def demonstrate_read_replicas():
    """Demostrar funcionamiento del sistema de read replicas."""
    print("🚀 Inicializando sistema de Read Replicas...")

    # Inicializar sistema
    manager = await initialize_read_replicas_system()

    print("📊 Estado inicial del sistema:")
    stats = manager.get_replica_stats()
    print(f"   Total réplicas: {stats['total_replicas']}")
    print(f"   Réplicas disponibles: {stats['available_replicas']}")
    print(f"   Regiones: {', '.join(stats['regions'])}")

    # Demostrar selección de réplicas
    print("\n🎯 Probando selección de réplicas óptimas:")

    regions_to_test = ["us-central1", "europe-west1", "asia-east1", None]

    for region in regions_to_test:
        replica = manager.get_optimal_replica(region)
        if replica:
            print(f"   Región preferida '{region}': {replica.replica_id} ({replica.region}) - Lag: {replica.replication_lag:.1f}s")
        else:
            print(f"   Región preferida '{region}': No replica available")

    # Simular algunas queries de read
    print("\n📖 Ejecutando queries de read de prueba...")

    for i in range(10):
        try:
            result = await manager.execute_read_query(f"SELECT * FROM users LIMIT {random.randint(10, 100)}")
            print(f"   Query {i+1}: {len(result['result'])} registros desde {result['replica_used']} ({result['region']}) - {result['response_time']:.3f}s")
        except Exception as e:
            print(f"   Query {i+1}: Error - {e}")

    # Mostrar estadísticas finales
    print("\n📈 Estadísticas finales:")
    dist_stats = manager.get_distribution_stats()
    print(f"   Total reads: {dist_stats['total_reads']}")
    print(f"   Avg response time: {dist_stats['avg_response_time']:.3f}s")

    if dist_stats['distribution_percentages']:
        print("   Distribución por réplica:")
        for replica_id, percentage in dist_stats['distribution_percentages'].items():
            print(f"     {replica_id}: {percentage:.1f}%")
    # Simular failover
    print("\n🔄 Simulando failover del primary...")
    if manager.primary_replica:
        print(f"   Primary actual: {manager.primary_replica.replica_id}")

        # Simular fallo
        manager.primary_replica.status = ReplicaStatus.UNHEALTHY

        # Trigger failover
        success = await manager.failover_manager.handle_primary_failure()

        if success:
            print(f"   ✅ Failover exitoso: Nuevo primary {manager.primary_replica.replica_id}")
        else:
            print("   ❌ Failover fallido")

    print("\n✅ Demostración de Read Replicas completada")

    return manager


if __name__ == "__main__":
    asyncio.run(demonstrate_read_replicas())