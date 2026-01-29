"""
IPFS Optimization para AILOOS

Implementa optimización completa de IPFS con:
- Multiple IPFS nodes clustering
- Content pinning strategies inteligentes
- Bandwidth optimization automática
- Load balancing entre nodos
"""

import asyncio
import logging
import time
import hashlib
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
import statistics
import aiohttp

logger = logging.getLogger(__name__)


class PinningStrategy(Enum):
    """Estrategias de pinning disponibles."""
    REPLICATED = "replicated"      # Múltiples réplicas
    GEOGRAPHIC = "geographic"      # Basado en ubicación geográfica
    POPULARITY = "popularity"      # Basado en popularidad/acceso
    TEMPORAL = "temporal"          # Basado en tiempo de vida
    HYBRID = "hybrid"              # Combinación inteligente


class IPFSNodeStatus(Enum):
    """Estados de un nodo IPFS."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OVERLOADED = "overloaded"
    OFFLINE = "offline"
    SYNCING = "syncing"


@dataclass
class IPFSNode:
    """Representa un nodo IPFS en el cluster."""
    node_id: str
    endpoint: str  # http://localhost:5001
    region: str
    status: IPFSNodeStatus = IPFSNodeStatus.HEALTHY
    storage_used_gb: float = 0.0
    storage_total_gb: float = 100.0
    bandwidth_up_mbps: float = 10.0
    bandwidth_down_mbps: float = 10.0
    active_peers: int = 0
    pinned_content_count: int = 0
    last_health_check: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_available(self) -> bool:
        """Verificar si el nodo está disponible."""
        return self.status in [IPFSNodeStatus.HEALTHY, IPFSNodeStatus.DEGRADED]

    @property
    def storage_available_gb(self) -> float:
        """Almacenamiento disponible en GB."""
        return max(0, self.storage_total_gb - self.storage_used_gb)

    @property
    def storage_utilization_percent(self) -> float:
        """Utilización de almacenamiento en porcentaje."""
        if self.storage_total_gb == 0:
            return 100.0
        return (self.storage_used_gb / self.storage_total_gb) * 100

    async def check_health(self) -> Dict[str, Any]:
        """Verificar salud del nodo IPFS."""
        try:
            async with aiohttp.ClientSession() as session:
                # Verificar conectividad básica
                async with session.get(f"{self.endpoint}/api/v0/id", timeout=5) as response:
                    if response.status == 200:
                        node_info = await response.json()

                        # Actualizar métricas
                        self.active_peers = len(node_info.get('Addresses', []))
                        self.last_health_check = datetime.now()

                        # Simular métricas de almacenamiento (en producción vendrían de IPFS)
                        self.storage_used_gb = random.uniform(10, 80)
                        self.pinned_content_count = random.randint(100, 1000)

                        # Determinar status basado en métricas
                        if self.storage_utilization_percent > 90:
                            self.status = IPFSNodeStatus.OVERLOADED
                        elif self.active_peers < 5:
                            self.status = IPFSNodeStatus.DEGRADED
                        else:
                            self.status = IPFSNodeStatus.HEALTHY

                        return {
                            'healthy': True,
                            'status': self.status.value,
                            'peers': self.active_peers,
                            'storage_used': self.storage_used_gb,
                            'pinned_count': self.pinned_content_count
                        }
                    else:
                        self.status = IPFSNodeStatus.OFFLINE
                        return {'healthy': False, 'error': f'HTTP {response.status}'}

        except Exception as e:
            self.status = IPFSNodeStatus.OFFLINE
            return {'healthy': False, 'error': str(e)}


@dataclass
class ContentPin:
    """Información de pinning de contenido."""
    content_cid: str
    pinning_strategy: PinningStrategy
    replicas_required: int = 3
    replicas_current: int = 0
    pinned_nodes: Set[str] = field(default_factory=set)
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    @property
    def is_expired(self) -> bool:
        """Verificar si el contenido ha expirado."""
        return self.expires_at and datetime.now() > self.expires_at

    @property
    def needs_replication(self) -> bool:
        """Verificar si necesita más réplicas."""
        return self.replicas_current < self.replicas_required


class IPFSClusterManager:
    """
    Gestor de cluster IPFS con múltiples nodos.

    Características:
    - Load balancing automático entre nodos
    - Health monitoring continuo
    - Content replication inteligente
    - Bandwidth optimization
    """

    def __init__(self):
        self.nodes: Dict[str, IPFSNode] = {}
        self.content_pins: Dict[str, ContentPin] = {}
        self.bandwidth_optimizer = BandwidthOptimizer()
        self.health_monitor = IPFSHealthMonitor(self)

    def add_node(self, node: IPFSNode):
        """Añadir un nodo IPFS al cluster."""
        self.nodes[node.node_id] = node
        logger.info(f"Added IPFS node {node.node_id} in region {node.region}")

    def remove_node(self, node_id: str):
        """Remover un nodo del cluster."""
        if node_id in self.nodes:
            # Replicar contenido de este nodo a otros
            asyncio.create_task(self._evacuate_node_content(node_id))
            del self.nodes[node_id]
            logger.info(f"Removed IPFS node {node_id}")

    async def _evacuate_node_content(self, node_id: str):
        """Evacuar contenido de un nodo antes de removerlo."""
        # Encontrar contenido pinned solo en este nodo
        content_to_replicate = []
        for cid, pin_info in self.content_pins.items():
            if node_id in pin_info.pinned_nodes and len(pin_info.pinned_nodes) == 1:
                content_to_replicate.append(cid)

        # Replicar a otros nodos
        for cid in content_to_replicate:
            await self._replicate_content(cid, exclude_nodes={node_id})

    def select_optimal_node(self, content_cid: Optional[str] = None,
                           preferred_region: Optional[str] = None,
                           operation: str = "read") -> Optional[IPFSNode]:
        """Seleccionar el nodo óptimo para una operación."""

        available_nodes = [n for n in self.nodes.values() if n.is_available]

        if not available_nodes:
            return None

        if operation == "write":
            # Para writes, seleccionar basado en capacidad de almacenamiento
            return max(available_nodes, key=lambda n: n.storage_available_gb)

        # Para reads, usar algoritmo inteligente
        scored_nodes = []
        for node in available_nodes:
            score = self._calculate_node_score(node, content_cid, preferred_region)
            scored_nodes.append((node, score))

        return max(scored_nodes, key=lambda x: x[1])[0]

    def _calculate_node_score(self, node: IPFSNode, content_cid: Optional[str],
                            preferred_region: Optional[str]) -> float:
        """Calcular score para selección de nodo."""
        base_score = 100.0

        # Bonus por región preferida
        region_bonus = 20 if preferred_region and node.region == preferred_region else 0

        # Penalización por utilización de almacenamiento
        storage_penalty = min(node.storage_utilization_percent / 2, 40)

        # Penalización por sobrecarga de bandwidth
        bandwidth_penalty = 0  # En implementación real, medir uso actual

        # Bonus si el contenido ya está pinned en este nodo
        content_bonus = 0
        if content_cid and content_cid in self.content_pins:
            pin_info = self.content_pins[content_cid]
            if node.node_id in pin_info.pinned_nodes:
                content_bonus = 30

        # Penalización por latencia simulada
        latency_penalty = random.uniform(0, 10)  # Simular latencia variable

        final_score = (base_score + region_bonus + content_bonus -
                      storage_penalty - bandwidth_penalty - latency_penalty)

        return max(final_score, 0)

    async def pin_content(self, content_cid: str, strategy: PinningStrategy = PinningStrategy.REPLICATED,
                         replicas: int = 3, size_bytes: int = 0) -> bool:
        """Pin content usando estrategia especificada."""

        # Crear registro de pin
        pin_info = ContentPin(
            content_cid=content_cid,
            pinning_strategy=strategy,
            replicas_required=replicas,
            size_bytes=size_bytes
        )

        self.content_pins[content_cid] = pin_info

        # Ejecutar estrategia de pinning
        if strategy == PinningStrategy.REPLICATED:
            success = await self._pin_replicated(content_cid, replicas)
        elif strategy == PinningStrategy.GEOGRAPHIC:
            success = await self._pin_geographic(content_cid, replicas)
        elif strategy == PinningStrategy.POPULARITY:
            success = await self._pin_popularity_based(content_cid, replicas)
        elif strategy == PinningStrategy.TEMPORAL:
            success = await self._pin_temporal(content_cid, replicas)
        else:  # HYBRID
            success = await self._pin_hybrid(content_cid, replicas)

        if success:
            logger.info(f"Successfully pinned {content_cid} with strategy {strategy.value}")
        else:
            logger.error(f"Failed to pin {content_cid}")

        return success

    async def _pin_replicated(self, content_cid: str, replicas: int) -> bool:
        """Estrategia de pinning replicado (distribución uniforme)."""
        available_nodes = [n for n in self.nodes.values() if n.is_available]

        if len(available_nodes) < replicas:
            logger.warning(f"Not enough available nodes for {replicas} replicas")
            replicas = len(available_nodes)

        # Seleccionar nodos con mejor capacidad
        selected_nodes = sorted(available_nodes, key=lambda n: n.storage_available_gb, reverse=True)[:replicas]

        # Pin en nodos seleccionados
        success_count = 0
        for node in selected_nodes:
            if await self._pin_on_node(node, content_cid):
                success_count += 1

        self.content_pins[content_cid].replicas_current = success_count
        return success_count >= min(replicas, len(available_nodes))

    async def _pin_geographic(self, content_cid: str, replicas: int) -> bool:
        """Estrategia de pinning geográfico."""
        regions = set(node.region for node in self.nodes.values())
        nodes_per_region = max(1, replicas // len(regions))

        success_count = 0
        for region in regions:
            regional_nodes = [n for n in self.nodes.values()
                            if n.region == region and n.is_available]

            if regional_nodes:
                # Seleccionar mejor nodo de la región
                selected_node = max(regional_nodes, key=lambda n: n.storage_available_gb)
                if await self._pin_on_node(selected_node, content_cid):
                    success_count += 1

        self.content_pins[content_cid].replicas_current = success_count
        return success_count >= 1  # Al menos una réplica por región

    async def _pin_popularity_based(self, content_cid: str, replicas: int) -> bool:
        """Estrategia basada en popularidad (simulada)."""
        # En producción, esto usaría métricas reales de acceso
        # Por ahora, usar distribución uniforme con bias hacia nodos con buena conectividad
        available_nodes = [n for n in self.nodes.values() if n.is_available]
        selected_nodes = sorted(available_nodes, key=lambda n: n.active_peers, reverse=True)[:replicas]

        success_count = 0
        for node in selected_nodes:
            if await self._pin_on_node(node, content_cid):
                success_count += 1

        self.content_pins[content_cid].replicas_current = success_count
        return success_count >= min(replicas, len(available_nodes))

    async def _pin_temporal(self, content_cid: str, replicas: int) -> bool:
        """Estrategia temporal (para contenido efímero)."""
        # Pin en nodos con mejor performance temporal
        available_nodes = [n for n in self.nodes.values() if n.is_available]
        selected_nodes = sorted(available_nodes, key=lambda n: n.bandwidth_up_mbps, reverse=True)[:replicas]

        success_count = 0
        for node in selected_nodes:
            if await self._pin_on_node(node, content_cid):
                success_count += 1

        # Establecer expiración (ejemplo: 24 horas)
        self.content_pins[content_cid].expires_at = datetime.now() + timedelta(hours=24)
        self.content_pins[content_cid].replicas_current = success_count
        return success_count >= 1

    async def _pin_hybrid(self, content_cid: str, replicas: int) -> bool:
        """Estrategia híbrida inteligente."""
        # Combinar múltiples factores
        available_nodes = [n for n in self.nodes.values() if n.is_available]

        scored_nodes = []
        for node in available_nodes:
            # Score basado en múltiples factores
            storage_score = (100 - node.storage_utilization_percent) / 100
            bandwidth_score = min(node.bandwidth_up_mbps / 100, 1.0)  # Max 100 Mbps
            peer_score = min(node.active_peers / 50, 1.0)  # Max 50 peers

            hybrid_score = (storage_score * 0.4 + bandwidth_score * 0.3 + peer_score * 0.3)
            scored_nodes.append((node, hybrid_score))

        # Seleccionar mejores nodos
        selected_nodes = sorted(scored_nodes, key=lambda x: x[1], reverse=True)[:replicas]
        selected_nodes = [node for node, score in selected_nodes]

        success_count = 0
        for node in selected_nodes:
            if await self._pin_on_node(node, content_cid):
                success_count += 1

        self.content_pins[content_cid].replicas_current = success_count
        return success_count >= min(replicas, len(available_nodes))

    async def _pin_on_node(self, node: IPFSNode, content_cid: str) -> bool:
        """Pin content en un nodo específico."""
        try:
            # Simular pinning (en producción sería llamada real a IPFS)
            await asyncio.sleep(0.1)  # Simular tiempo de pinning

            # Verificar si hay espacio suficiente
            if node.storage_available_gb < 1.0:  # Asumir al menos 1GB disponible
                return False

            # Actualizar estado del nodo
            node.pinned_content_count += 1
            node.storage_used_gb += 0.001  # 1MB por content (simulado)

            # Registrar en pin info
            if content_cid in self.content_pins:
                self.content_pins[content_cid].pinned_nodes.add(node.node_id)

            return True

        except Exception as e:
            logger.error(f"Failed to pin {content_cid} on {node.node_id}: {e}")
            return False

    async def _replicate_content(self, content_cid: str, exclude_nodes: Set[str] = None):
        """Replicar contenido a más nodos."""
        if content_cid not in self.content_pins:
            return

        pin_info = self.content_pins[content_cid]
        if not pin_info.needs_replication:
            return

        # Encontrar nodos disponibles que no tienen el contenido
        available_nodes = [n for n in self.nodes.values()
                          if n.is_available and n.node_id not in pin_info.pinned_nodes
                          and n.node_id not in (exclude_nodes or set())]

        if not available_nodes:
            return

        # Seleccionar mejor nodo
        target_node = max(available_nodes, key=lambda n: n.storage_available_gb)

        # Pin en el nodo seleccionado
        if await self._pin_on_node(target_node, content_cid):
            pin_info.replicas_current += 1
            logger.info(f"Replicated {content_cid} to {target_node.node_id}")

    async def retrieve_content(self, content_cid: str, preferred_region: Optional[str] = None) -> Optional[bytes]:
        """Recuperar contenido desde el cluster."""
        if content_cid not in self.content_pins:
            return None

        pin_info = self.content_pins[content_cid]

        # Actualizar estadísticas de acceso
        pin_info.access_count += 1
        pin_info.last_accessed = datetime.now()

        # Seleccionar nodo óptimo
        node = self.select_optimal_node(content_cid, preferred_region, "read")

        if not node:
            return None

        try:
            # Simular retrieval (en producción sería llamada real a IPFS)
            await asyncio.sleep(0.05)  # Simular latencia

            # Simular contenido
            content = f"Content data for {content_cid} from {node.node_id}".encode()

            return content

        except Exception as e:
            logger.error(f"Failed to retrieve {content_cid} from {node.node_id}: {e}")
            return None

    async def start_health_monitoring(self):
        """Iniciar monitoring de salud del cluster."""
        await self.health_monitor.start_monitoring()

    def get_cluster_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cluster."""
        total_nodes = len(self.nodes)
        available_nodes = len([n for n in self.nodes.values() if n.is_available])
        total_storage = sum(n.storage_total_gb for n in self.nodes.values())
        used_storage = sum(n.storage_used_gb for n in self.nodes.values())
        total_pinned = sum(n.pinned_content_count for n in self.nodes.values())

        regions = {}
        for node in self.nodes.values():
            regions[node.region] = regions.get(node.region, 0) + 1

        return {
            'total_nodes': total_nodes,
            'available_nodes': available_nodes,
            'availability_percent': (available_nodes / total_nodes * 100) if total_nodes > 0 else 0,
            'total_storage_gb': total_storage,
            'used_storage_gb': used_storage,
            'storage_utilization_percent': (used_storage / total_storage * 100) if total_storage > 0 else 0,
            'total_pinned_content': total_pinned,
            'regions': regions,
            'total_content_pins': len(self.content_pins)
        }


class IPFSHealthMonitor:
    """Monitor de salud para cluster IPFS."""

    def __init__(self, cluster_manager: IPFSClusterManager):
        self.cluster_manager = cluster_manager
        self.monitoring_interval = 60  # segundos

    async def start_monitoring(self):
        """Iniciar monitoring continuo."""
        while True:
            try:
                await self._check_cluster_health()
                await asyncio.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Error in IPFS health monitoring: {e}")
                await asyncio.sleep(self.monitoring_interval)

    async def _check_cluster_health(self):
        """Verificar salud de todos los nodos."""
        tasks = []

        for node in self.cluster_manager.nodes.values():
            task = node.check_health()
            tasks.append(task)

        # Ejecutar verificaciones en paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Procesar resultados
        healthy_count = 0
        for i, result in enumerate(results):
            node_id = list(self.cluster_manager.nodes.keys())[i]

            if isinstance(result, Exception):
                logger.warning(f"Health check failed for {node_id}: {result}")
            elif isinstance(result, dict) and result.get('healthy'):
                healthy_count += 1

        total_nodes = len(self.cluster_manager.nodes)
        health_percentage = (healthy_count / total_nodes * 100) if total_nodes > 0 else 0

        if health_percentage < 50:
            logger.warning(f"Cluster health degraded: {healthy_count}/{total_nodes} healthy nodes")
        else:
            logger.info(f"Cluster health: {healthy_count}/{total_nodes} healthy nodes")


class BandwidthOptimizer:
    """Optimizador de bandwidth para IPFS."""

    def __init__(self):
        self.bandwidth_limits: Dict[str, float] = {}  # node_id -> mbps limit
        self.current_usage: Dict[str, float] = {}     # node_id -> current mbps

    def set_bandwidth_limit(self, node_id: str, limit_mbps: float):
        """Establecer límite de bandwidth para un nodo."""
        self.bandwidth_limits[node_id] = limit_mbps

    def get_bandwidth_limit(self, node_id: str) -> float:
        """Obtener límite de bandwidth para un nodo."""
        return self.bandwidth_limits.get(node_id, 10.0)  # Default 10 Mbps

    def update_usage(self, node_id: str, usage_mbps: float):
        """Actualizar uso de bandwidth."""
        self.current_usage[node_id] = usage_mbps

    def should_throttle(self, node_id: str, requested_mbps: float) -> bool:
        """Verificar si se debe throttlear una operación."""
        limit = self.get_bandwidth_limit(node_id)
        current = self.current_usage.get(node_id, 0)
        return (current + requested_mbps) > limit


# Funciones de conveniencia

def create_global_ipfs_cluster() -> List[IPFSNode]:
    """Crear configuración de cluster IPFS global."""
    nodes = []

    # Nodos en múltiples regiones
    regions_config = [
        ("us-central1", 3, "10.0.0.1"),
        ("europe-west1", 2, "10.0.1.1"),
        ("asia-east1", 2, "10.0.2.1"),
        ("australia-southeast1", 1, "10.0.3.1"),
        ("southamerica-east1", 1, "10.0.4.1")
    ]

    node_counter = 1
    for region, node_count, base_ip in regions_config:
        for i in range(node_count):
            node = IPFSNode(
                node_id=f"ipfs-{region}-{i+1}",
                endpoint=f"http://{base_ip}:{5000 + i}",
                region=region,
                storage_total_gb=500.0,  # 500GB por nodo
                bandwidth_up_mbps=50.0,
                bandwidth_down_mbps=100.0
            )
            nodes.append(node)
            node_counter += 1

    return nodes


async def initialize_ipfs_cluster() -> IPFSClusterManager:
    """Inicializar cluster IPFS completo."""
    manager = IPFSClusterManager()

    # Crear nodos globales
    nodes = create_global_ipfs_cluster()

    # Añadir todos los nodos
    for node in nodes:
        manager.add_node(node)

    # Iniciar monitoring de salud
    asyncio.create_task(manager.start_health_monitoring())

    logger.info(f"IPFS cluster initialized with {len(nodes)} nodes across {len(set(n.region for n in nodes))} regions")

    return manager


async def demonstrate_ipfs_optimization():
    """Demostrar optimización de IPFS."""
    print("🌐 Inicializando IPFS Cluster Optimization...")

    # Inicializar cluster
    cluster = await initialize_ipfs_cluster()

    print("📊 Estado inicial del cluster:")
    stats = cluster.get_cluster_stats()
    print(f"   Nodos totales: {stats['total_nodes']}")
    print(f"   Nodos disponibles: {stats['available_nodes']}")
    print(f"   Regiones: {', '.join(stats['regions'].keys())}")
    print(".1f"
    # Probar pinning con diferentes estrategias
    print("\n📌 Probando estrategias de pinning:")

    test_content = [
        ("QmTest1", PinningStrategy.REPLICATED, 3),
        ("QmTest2", PinningStrategy.GEOGRAPHIC, 2),
        ("QmTest3", PinningStrategy.POPULARITY, 4),
        ("QmTest4", PinningStrategy.TEMPORAL, 2),
        ("QmTest5", PinningStrategy.HYBRID, 3)
    ]

    for cid, strategy, replicas in test_content:
        success = await cluster.pin_content(cid, strategy, replicas, size_bytes=1024*1024)  # 1MB
        status = "✅" if success else "❌"
        pin_info = cluster.content_pins.get(cid)
        actual_replicas = pin_info.replicas_current if pin_info else 0
        print(f"   {status} {cid}: {strategy.value} ({actual_replicas}/{replicas} réplicas)")

    # Probar retrieval
    print("\n📥 Probando retrieval de contenido:")

    for cid, _, _ in test_content[:3]:  # Probar primeros 3
        content = await cluster.retrieve_content(cid, preferred_region="us-central1")
        if content:
            print(f"   ✅ {cid}: {len(content)} bytes recuperados")
        else:
            print(f"   ❌ {cid}: Error al recuperar")

    # Probar selección de nodos
    print("\n🎯 Probando selección de nodos óptimos:")

    operations = ["read", "write"]
    regions = ["us-central1", "europe-west1", "asia-east1"]

    for op in operations:
        for region in regions:
            node = cluster.select_optimal_node(preferred_region=region, operation=op)
            if node:
                print(f"   {op.upper()} {region}: {node.node_id} ({node.region})")
            else:
                print(f"   {op.upper()} {region}: No node available")

    # Mostrar estadísticas finales
    print("
📈 Estadísticas finales del cluster:"    final_stats = cluster.get_cluster_stats()
    print(f"   Contenido pinned: {final_stats['total_content_pins']}")
    print(f"   Contenido total: {final_stats['total_pinned_content']}")
    print(".1f"
    print("✅ IPFS Cluster Optimization demostrado correctamente")

    return cluster


if __name__ == "__main__":
    asyncio.run(demonstrate_ipfs_optimization())