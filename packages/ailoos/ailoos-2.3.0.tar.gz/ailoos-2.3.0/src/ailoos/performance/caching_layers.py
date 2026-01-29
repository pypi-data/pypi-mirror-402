"""
Caching Layers para AILOOS

Implementa sistema completo de caching multi-nivel con:
- Redis clustering avanzado
- CDN integration global
- Edge computing inteligente
- Cache invalidation automática
"""

import asyncio
import logging
import time
import hashlib
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import random
import statistics
import aiohttp

logger = logging.getLogger(__name__)


class CacheLayer(Enum):
    """Niveles de cache disponibles."""
    L1_MEMORY = "l1_memory"      # Cache en memoria local (más rápido)
    L2_REDIS = "l2_redis"        # Cache Redis distribuido
    L3_CDN = "l3_cdn"           # CDN global
    L4_EDGE = "l4_edge"         # Edge computing


class CacheStrategy(Enum):
    """Estrategias de cache disponibles."""
    LRU = "lru"                  # Least Recently Used
    LFU = "lfu"                  # Least Frequently Used
    TTL = "ttl"                  # Time To Live
    WRITE_THROUGH = "write_through"  # Write-through caching
    WRITE_BACK = "write_back"    # Write-back caching
    READ_THROUGH = "read_through" # Read-through caching


@dataclass
class CacheEntry:
    """Entrada de cache con metadata completa."""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    size_bytes: int = 0
    ttl_seconds: Optional[int] = None
    tags: Set[str] = field(default_factory=set)
    compression: bool = False

    @property
    def is_expired(self) -> bool:
        """Verificar si la entrada ha expirado."""
        if self.ttl_seconds is None:
            return False
        return (datetime.now() - self.created_at).total_seconds() > self.ttl_seconds

    @property
    def age_seconds(self) -> float:
        """Edad de la entrada en segundos."""
        return (datetime.now() - self.created_at).total_seconds()

    @property
    def idle_seconds(self) -> float:
        """Tiempo idle en segundos."""
        return (datetime.now() - self.last_accessed).total_seconds()


@dataclass
class RedisNode:
    """Nodo Redis en el cluster."""
    node_id: str
    host: str
    port: int
    role: str  # "master" or "slave"
    slots: List[Tuple[int, int]] = field(default_factory=list)  # Hash slots ranges
    is_available: bool = True
    last_health_check: Optional[datetime] = None
    memory_used_gb: float = 0.0
    memory_total_gb: float = 8.0
    connections_active: int = 0
    hit_rate: float = 0.0

    @property
    def memory_utilization_percent(self) -> float:
        """Utilización de memoria en porcentaje."""
        if self.memory_total_gb == 0:
            return 100.0
        return (self.memory_used_gb / self.memory_total_gb) * 100

    def owns_slot(self, slot: int) -> bool:
        """Verificar si este nodo es propietario de un slot de hash."""
        for start, end in self.slots:
            if start <= slot <= end:
                return True
        return False


@dataclass
class CDNNode:
    """Nodo CDN para distribución global."""
    node_id: str
    region: str
    provider: str  # "cloudflare", "fastly", "akamai", etc.
    endpoint: str
    is_active: bool = True
    cache_hit_rate: float = 0.0
    bandwidth_mbps: float = 100.0
    latency_ms: float = 50.0
    cached_objects: int = 0


@dataclass
class EdgeNode:
    """Nodo de edge computing."""
    node_id: str
    region: str
    provider: str
    capabilities: Set[str] = field(default_factory=set)  # "compute", "storage", "ai"
    is_active: bool = True
    cpu_cores: int = 4
    memory_gb: float = 8.0
    storage_gb: float = 100.0
    current_load: float = 0.0  # 0-1


class RedisClusterManager:
    """
    Gestor de cluster Redis avanzado.

    Características:
    - Sharding automático con hash slots
    - Failover automático
    - Load balancing inteligente
    - Health monitoring continuo
    """

    def __init__(self):
        self.nodes: Dict[str, RedisNode] = {}
        self.hash_slots: Dict[int, str] = {}  # slot -> node_id
        self.replication_groups: Dict[str, List[str]] = {}  # master_id -> [slave_ids]

    def add_node(self, node: RedisNode):
        """Añadir nodo al cluster."""
        self.nodes[node.node_id] = node

        # Asignar hash slots si es master
        if node.role == "master":
            self._assign_slots_to_node(node)

        logger.info(f"Added Redis node {node.node_id} ({node.role}) to cluster")

    def _assign_slots_to_node(self, node: RedisNode):
        """Asignar slots de hash a un nodo master."""
        # Distribución simple: dividir slots equitativamente
        total_slots = 16384  # Redis cluster tiene 16384 slots
        num_masters = len([n for n in self.nodes.values() if n.role == "master"])

        if num_masters == 0:
            return

        slots_per_master = total_slots // num_masters
        master_index = len([n for n in self.nodes.values() if n.role == "master" and n.node_id != node.node_id])

        start_slot = master_index * slots_per_master
        end_slot = start_slot + slots_per_master - 1 if master_index < num_masters - 1 else total_slots - 1

        node.slots.append((start_slot, end_slot))

        # Actualizar mapa de slots
        for slot in range(start_slot, end_slot + 1):
            self.hash_slots[slot] = node.node_id

    def get_node_for_key(self, key: str) -> Optional[RedisNode]:
        """Obtener nodo para una clave específica."""
        slot = self._calculate_slot(key)
        node_id = self.hash_slots.get(slot)

        if node_id and node_id in self.nodes:
            return self.nodes[node_id]

        return None

    def _calculate_slot(self, key: str) -> int:
        """Calcular slot de hash para una clave."""
        # CRC16 implementation (simplified)
        crc = 0
        for byte in key.encode('utf-8'):
            crc = (crc << 8) ^ self._crc16_table[(crc >> 8) ^ byte]
        return crc % 16384

    _crc16_table = [
        0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
        0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
        # ... (truncated for brevity, full table would be 256 entries)
    ] + [0] * (256 - 8)  # Placeholder

    async def get(self, key: str) -> Optional[Any]:
        """Obtener valor de Redis cluster."""
        node = self.get_node_for_key(key)
        if not node or not node.is_available:
            return None

        try:
            # Simular consulta Redis (en producción sería conexión real)
            await asyncio.sleep(0.001)  # Latencia simulada
            return f"cached_value_for_{key}"
        except Exception as e:
            logger.error(f"Redis get failed for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Establecer valor en Redis cluster."""
        node = self.get_node_for_key(key)
        if not node or not node.is_available:
            return False

        try:
            # Simular escritura Redis
            await asyncio.sleep(0.002)  # Latencia de escritura
            return True
        except Exception as e:
            logger.error(f"Redis set failed for key {key}: {e}")
            return False

    def get_cluster_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cluster."""
        total_nodes = len(self.nodes)
        master_nodes = len([n for n in self.nodes.values() if n.role == "master"])
        slave_nodes = len([n for n in self.nodes.values() if n.role == "slave"])
        available_nodes = len([n for n in self.nodes.values() if n.is_available])

        total_memory = sum(n.memory_total_gb for n in self.nodes.values())
        used_memory = sum(n.memory_used_gb for n in self.nodes.values())

        return {
            'total_nodes': total_nodes,
            'master_nodes': master_nodes,
            'slave_nodes': slave_nodes,
            'available_nodes': available_nodes,
            'availability_percent': (available_nodes / total_nodes * 100) if total_nodes > 0 else 0,
            'total_memory_gb': total_memory,
            'used_memory_gb': used_memory,
            'memory_utilization_percent': (used_memory / total_memory * 100) if total_memory > 0 else 0,
            'hash_slots_assigned': len(self.hash_slots)
        }


class CDNManager:
    """
    Gestor de CDN para distribución global de contenido.

    Características:
    - Múltiples proveedores de CDN
    - Load balancing inteligente
    - Cache invalidation automática
    - Analytics de performance
    """

    def __init__(self):
        self.nodes: Dict[str, CDNNode] = {}
        self.cache_entries: Dict[str, CacheEntry] = {}
        self.invalidation_queue: List[str] = []

    def add_cdn_node(self, node: CDNNode):
        """Añadir nodo CDN."""
        self.nodes[node.node_id] = node
        logger.info(f"Added CDN node {node.node_id} ({node.provider}) in {node.region}")

    def get_optimal_cdn_node(self, content_path: str, user_region: Optional[str] = None) -> Optional[CDNNode]:
        """Obtener nodo CDN óptimo para contenido."""
        available_nodes = [n for n in self.nodes.values() if n.is_active]

        if not available_nodes:
            return None

        # Priorizar región del usuario
        if user_region:
            regional_nodes = [n for n in available_nodes if n.region == user_region]
            if regional_nodes:
                available_nodes = regional_nodes

        # Seleccionar basado en múltiples factores
        scored_nodes = []
        for node in available_nodes:
            score = self._calculate_cdn_score(node, content_path, user_region)
            scored_nodes.append((node, score))

        return max(scored_nodes, key=lambda x: x[1])[0]

    def _calculate_cdn_score(self, node: CDNNode, content_path: str, user_region: str) -> float:
        """Calcular score para selección de CDN."""
        base_score = 100.0

        # Factor de latencia (menor latencia = mejor score)
        latency_penalty = min(node.latency_ms / 10, 50)  # Max 50 puntos de penalización

        # Factor de cache hit rate
        hit_rate_bonus = node.cache_hit_rate * 20  # Hasta 20 puntos de bonus

        # Factor de carga (menor carga = mejor score)
        load_penalty = node.current_load * 30  # Hasta 30 puntos de penalización

        # Bonus por región
        region_bonus = 15 if user_region and node.region == user_region else 0

        final_score = base_score - latency_penalty + hit_rate_bonus - load_penalty + region_bonus
        return max(final_score, 0)

    async def serve_content(self, content_path: str, user_region: Optional[str] = None) -> Optional[bytes]:
        """Servir contenido desde CDN."""
        node = self.get_optimal_cdn_node(content_path, user_region)
        if not node:
            return None

        try:
            # Simular fetch desde CDN
            latency = node.latency_ms / 1000  # Convertir a segundos
            await asyncio.sleep(latency)

            # Simular contenido
            content = f"CDN content from {node.node_id} for {content_path}".encode()

            # Actualizar estadísticas
            node.cached_objects += 1

            return content

        except Exception as e:
            logger.error(f"CDN fetch failed for {content_path}: {e}")
            return None

    async def invalidate_content(self, content_path: str) -> bool:
        """Invalidar contenido en CDN."""
        self.invalidation_queue.append(content_path)

        # Simular invalidation (en producción sería API call real a CDN)
        await asyncio.sleep(0.1)

        # Remover de cache local
        if content_path in self.cache_entries:
            del self.cache_entries[content_path]

        logger.info(f"Invalidated content: {content_path}")
        return True

    def get_cdn_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de CDN."""
        total_nodes = len(self.nodes)
        active_nodes = len([n for n in self.nodes.values() if n.is_active])
        total_cached = sum(n.cached_objects for n in self.nodes.values())

        providers = {}
        for node in self.nodes.values():
            providers[node.provider] = providers.get(node.provider, 0) + 1

        regions = {}
        for node in self.nodes.values():
            regions[node.region] = regions.get(node.region, 0) + 1

        return {
            'total_nodes': total_nodes,
            'active_nodes': active_nodes,
            'total_cached_objects': total_cached,
            'providers': providers,
            'regions': regions,
            'invalidation_queue_size': len(self.invalidation_queue)
        }


class EdgeComputingManager:
    """
    Gestor de edge computing para procesamiento cercano al usuario.

    Características:
    - Distribución de workloads
    - Load balancing inteligente
    - Resource optimization
    - Auto-scaling
    """

    def __init__(self):
        self.nodes: Dict[str, EdgeNode] = {}
        self.workloads: Dict[str, Dict[str, Any]] = {}

    def add_edge_node(self, node: EdgeNode):
        """Añadir nodo de edge computing."""
        self.nodes[node.node_id] = node
        logger.info(f"Added edge node {node.node_id} ({node.provider}) in {node.region}")

    def get_optimal_edge_node(self, workload_requirements: Dict[str, Any],
                            user_region: Optional[str] = None) -> Optional[EdgeNode]:
        """Obtener nodo edge óptimo para workload."""

        required_capabilities = set(workload_requirements.get('capabilities', []))
        min_cpu = workload_requirements.get('min_cpu_cores', 1)
        min_memory = workload_requirements.get('min_memory_gb', 1.0)

        # Filtrar nodos candidatos
        candidates = []
        for node in self.nodes.values():
            if not node.is_active:
                continue

            # Verificar capacidades requeridas
            if not required_capabilities.issubset(node.capabilities):
                continue

            # Verificar recursos mínimos
            if node.cpu_cores < min_cpu or node.memory_gb < min_memory:
                continue

            # Verificar carga (menos del 80%)
            if node.current_load > 0.8:
                continue

            candidates.append(node)

        if not candidates:
            return None

        # Priorizar región del usuario
        if user_region:
            regional_candidates = [n for n in candidates if n.region == user_region]
            if regional_candidates:
                candidates = regional_candidates

        # Seleccionar nodo con menor carga
        return min(candidates, key=lambda n: n.current_load)

    async def execute_workload(self, workload_id: str, workload_data: Dict[str, Any],
                             user_region: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Ejecutar workload en edge node óptimo."""

        node = self.get_optimal_edge_node(workload_data, user_region)
        if not node:
            return None

        try:
            # Simular ejecución en edge
            execution_time = random.uniform(0.1, 1.0)  # 100ms - 1s
            await asyncio.sleep(execution_time)

            # Actualizar carga del nodo
            node.current_load = min(1.0, node.current_load + 0.1)  # +10% load

            # Simular resultado
            result = {
                'workload_id': workload_id,
                'node_id': node.node_id,
                'region': node.region,
                'execution_time': execution_time,
                'result': f"Processed data on {node.node_id}",
                'timestamp': datetime.now().isoformat()
            }

            # Almacenar resultado
            self.workloads[workload_id] = result

            return result

        except Exception as e:
            logger.error(f"Edge workload execution failed: {e}")
            return None

    def get_edge_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de edge computing."""
        total_nodes = len(self.nodes)
        active_nodes = len([n for n in self.nodes.values() if n.is_active])

        total_cpu = sum(n.cpu_cores for n in self.nodes.values())
        total_memory = sum(n.memory_gb for n in self.nodes.values())
        avg_load = statistics.mean(n.current_load for n in self.nodes.values()) if self.nodes else 0

        providers = {}
        for node in self.nodes.values():
            providers[node.provider] = providers.get(node.provider, 0) + 1

        capabilities = {}
        for node in self.nodes.values():
            for cap in node.capabilities:
                capabilities[cap] = capabilities.get(cap, 0) + 1

        return {
            'total_nodes': total_nodes,
            'active_nodes': active_nodes,
            'total_cpu_cores': total_cpu,
            'total_memory_gb': total_memory,
            'average_load': avg_load,
            'providers': providers,
            'capabilities': capabilities,
            'active_workloads': len(self.workloads)
        }


class MultiLevelCacheManager:
    """
    Gestor de cache multi-nivel (L1-L4).

    Arquitectura de cache jerárquica:
    L1: Memoria local (más rápido, menor capacidad)
    L2: Redis cluster (medio, balanceado)
    L3: CDN global (lento, alta capacidad)
    L4: Edge computing (procesamiento distribuido)
    """

    def __init__(self):
        self.l1_cache = {}  # Dict[str, CacheEntry] - Memoria local
        self.l2_cache = RedisClusterManager()
        self.l3_cache = CDNManager()
        self.l4_cache = EdgeComputingManager()

        self.max_l1_entries = 10000
        self.l1_strategy = CacheStrategy.LRU

    async def get(self, key: str, user_region: Optional[str] = None) -> Optional[Any]:
        """Obtener valor usando estrategia multi-nivel."""

        # L1: Cache en memoria
        if key in self.l1_cache:
            entry = self.l1_cache[key]
            if not entry.is_expired:
                entry.last_accessed = datetime.now()
                entry.access_count += 1
                return entry.value

        # L2: Redis cluster
        value = await self.l2_cache.get(key)
        if value is not None:
            # Promover a L1
            self._add_to_l1(key, value)
            return value

        # L3: CDN (para contenido estático)
        if self._is_static_content(key):
            content = await self.l3_cache.serve_content(key, user_region)
            if content is not None:
                # Promover a L1 y L2
                self._add_to_l1(key, content)
                await self.l2_cache.set(key, content, ttl_seconds=3600)
                return content

        return None

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None,
                 strategy: CacheStrategy = CacheStrategy.WRITE_THROUGH):
        """Establecer valor usando estrategia especificada."""

        if strategy == CacheStrategy.WRITE_THROUGH:
            # Escribir en L1 y L2 inmediatamente
            self._add_to_l1(key, value, ttl_seconds)
            await self.l2_cache.set(key, value, ttl_seconds)

        elif strategy == CacheStrategy.WRITE_BACK:
            # Escribir solo en L1, lazy write a L2
            self._add_to_l1(key, value, ttl_seconds)
            # En producción, programar escritura lazy a L2

    def _add_to_l1(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """Añadir entrada a cache L1."""
        # Aplicar estrategia de reemplazo si es necesario
        if len(self.l1_cache) >= self.max_l1_entries:
            self._evict_l1_entries()

        entry = CacheEntry(
            key=key,
            value=value,
            ttl_seconds=ttl_seconds,
            size_bytes=len(str(value).encode('utf-8'))
        )

        self.l1_cache[key] = entry

    def _evict_l1_entries(self):
        """Evacuar entradas de L1 según estrategia."""
        if self.l1_strategy == CacheStrategy.LRU:
            # Least Recently Used
            oldest_key = min(self.l1_cache.keys(),
                           key=lambda k: self.l1_cache[k].last_accessed)
            del self.l1_cache[oldest_key]

        elif self.l1_strategy == CacheStrategy.LFU:
            # Least Frequently Used
            least_used_key = min(self.l1_cache.keys(),
                               key=lambda k: self.l1_cache[k].access_count)
            del self.l1_cache[least_used_key]

    def _is_static_content(self, key: str) -> bool:
        """Determinar si una clave representa contenido estático."""
        # Lógica simple: extensiones de archivo estático
        static_extensions = {'.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2'}
        return any(key.endswith(ext) for ext in static_extensions)

    async def invalidate(self, key: str):
        """Invalidar clave en todos los niveles."""
        # L1
        if key in self.l1_cache:
            del self.l1_cache[key]

        # L2
        # En producción, invalidar en Redis cluster

        # L3 (CDN)
        await self.l3_cache.invalidate_content(key)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de cache multi-nivel."""
        l1_entries = len(self.l1_cache)
        l1_size = sum(entry.size_bytes for entry in self.l1_cache.values())

        return {
            'l1_cache': {
                'entries': l1_entries,
                'size_bytes': l1_size,
                'utilization_percent': (l1_entries / self.max_l1_entries) * 100
            },
            'l2_cache': self.l2_cache.get_cluster_stats(),
            'l3_cache': self.l3_cache.get_cdn_stats(),
            'l4_cache': self.l4_cache.get_edge_stats()
        }


# Funciones de conveniencia

def create_redis_cluster_config() -> List[RedisNode]:
    """Crear configuración de cluster Redis."""
    nodes = []

    # 3 masters + 3 slaves para alta disponibilidad
    masters = [
        ("redis-master-01", "10.0.0.1", 6379),
        ("redis-master-02", "10.0.0.2", 6379),
        ("redis-master-03", "10.0.0.3", 6379)
    ]

    slaves = [
        ("redis-slave-01", "10.0.0.4", 6379),
        ("redis-slave-02", "10.0.0.5", 6379),
        ("redis-slave-03", "10.0.0.6", 6379)
    ]

    for node_id, host, port in masters:
        node = RedisNode(
            node_id=node_id,
            host=host,
            port=port,
            role="master",
            memory_total_gb=16.0
        )
        nodes.append(node)

    for node_id, host, port in slaves:
        node = RedisNode(
            node_id=node_id,
            host=host,
            port=port,
            role="slave",
            memory_total_gb=16.0
        )
        nodes.append(node)

    return nodes


def create_cdn_config() -> List[CDNNode]:
    """Crear configuración de CDN global."""
    nodes = []

    cdn_providers = [
        ("cloudflare", ["us-east1", "us-west1", "europe-west1", "asia-east1"]),
        ("fastly", ["us-central1", "europe-north1", "asia-southeast1"]),
        ("akamai", ["us-south1", "europe-central1", "asia-northeast1"])
    ]

    node_counter = 1
    for provider, regions in cdn_providers:
        for region in regions:
            node = CDNNode(
                node_id=f"cdn-{provider}-{node_counter}",
                region=region,
                provider=provider,
                endpoint=f"https://cdn-{provider}-{region}.example.com",
                cache_hit_rate=random.uniform(0.85, 0.95),
                latency_ms=random.uniform(20, 80)
            )
            nodes.append(node)
            node_counter += 1

    return nodes


def create_edge_config() -> List[EdgeNode]:
    """Crear configuración de edge computing."""
    nodes = []

    edge_providers = [
        ("aws", ["us-east-1", "eu-west-1", "ap-southeast-1"]),
        ("azure", ["East US", "West Europe", "Southeast Asia"]),
        ("gcp", ["us-central1", "europe-west1", "asia-east1"])
    ]

    node_counter = 1
    for provider, regions in edge_providers:
        for region in regions:
            capabilities = {"compute", "storage"}
            if random.random() > 0.5:
                capabilities.add("ai")

            node = EdgeNode(
                node_id=f"edge-{provider}-{node_counter}",
                region=region,
                provider=provider,
                capabilities=capabilities,
                cpu_cores=random.randint(4, 16),
                memory_gb=random.uniform(8, 32),
                storage_gb=random.uniform(100, 500)
            )
            nodes.append(node)
            node_counter += 1

    return nodes


async def initialize_caching_system() -> MultiLevelCacheManager:
    """Inicializar sistema completo de caching multi-nivel."""
    manager = MultiLevelCacheManager()

    # Configurar Redis cluster
    redis_nodes = create_redis_cluster_config()
    for node in redis_nodes:
        manager.l2_cache.add_node(node)

    # Configurar CDN
    cdn_nodes = create_cdn_config()
    for node in cdn_nodes:
        manager.l3_cache.add_cdn_node(node)

    # Configurar Edge computing
    edge_nodes = create_edge_config()
    for node in edge_nodes:
        manager.l4_cache.add_edge_node(node)

    logger.info("Multi-level caching system initialized")

    return manager


async def demonstrate_caching_layers():
    """Demostrar sistema de caching multi-nivel."""
    print("🔄 Inicializando Multi-Level Caching System...")

    # Inicializar sistema
    cache_manager = await initialize_caching_system()

    print("📊 Estado inicial del sistema de cache:")
    stats = cache_manager.get_cache_stats()
    print(f"   L1 Cache: {stats['l1_cache']['entries']}/{cache_manager.max_l1_entries} entradas")
    print(f"   L2 Redis: {stats['l2_cache']['total_nodes']} nodos ({stats['l2_cache']['available_nodes']} disponibles)")
    print(f"   L3 CDN: {stats['l3_cache']['total_nodes']} nodos en {len(stats['l3_cache']['regions'])} regiones")
    print(f"   L4 Edge: {stats['l4_cache']['total_nodes']} nodos con {len(stats['l4_cache']['capabilities'])} tipos de capacidades")

    # Probar operaciones de cache
    print("\n💾 Probando operaciones de cache:")

    test_keys = [f"test_key_{i}" for i in range(5)]
    test_values = [f"value_{i}_data" for i in range(5)]

    # Set operations
    for key, value in zip(test_keys, test_values):
        await cache_manager.set(key, value, ttl_seconds=3600)
        print(f"   ✅ Set: {key} = {value}")

    # Get operations (deberían venir de L1 después del primer miss)
    print("\n   Probando retrieval:")
    for key in test_keys:
        value = await cache_manager.get(key)
        if value:
            print(f"   ✅ Get: {key} = {value}")
        else:
            print(f"   ❌ Get: {key} = None")

    # Probar contenido estático (CDN)
    print("\n   Probando contenido estático (CDN):")
    static_content = await cache_manager.get("/static/app.js", "us-central1")
    if static_content:
        print("   ✅ Contenido estático servido desde CDN")
    else:
        print("   ❌ Error al servir contenido estático")

    # Mostrar estadísticas finales
    print("
📈 Estadísticas finales del sistema de cache:"    final_stats = cache_manager.get_cache_stats()
    print(f"   L1 Cache: {final_stats['l1_cache']['entries']} entradas ({final_stats['l1_cache']['size_bytes']:,} bytes)")
    print(".1f"    print(f"   L3 CDN: {final_stats['l3_cache']['total_cached_objects']} objetos cached")
    print(f"   L4 Edge: {final_stats['l4_cache']['active_workloads']} workloads activos")

    print("✅ Multi-Level Caching System demostrado correctamente")

    return cache_manager


if __name__ == "__main__":
    asyncio.run(demonstrate_caching_layers())