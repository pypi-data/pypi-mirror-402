#!/usr/bin/env python3
"""
P2P Routing System using Kademlia-like DHT
Implementa routing y descubrimiento de rutas para red P2P con optimización de latencia
"""

import asyncio
import logging
import hashlib
import time
import random
import secrets
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict, deque
import heapq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PeerInfo:
    """Información de un peer en la red DHT"""
    node_id: bytes  # 20-byte node ID
    endpoint: str  # ip:port
    last_seen: Optional[datetime] = None
    latency_ms: float = float('inf')
    reputation_score: float = 0.5
    is_active: bool = True

@dataclass
class Route:
    """Ruta para un mensaje"""
    hops: List[bytes] = field(default_factory=list)  # Lista de node_ids en la ruta
    total_latency: float = 0.0
    hop_count: int = 0
    last_updated: datetime = field(default_factory=datetime.now)

    def add_hop(self, node_id: bytes, latency: float):
        """Agregar un salto a la ruta"""
        self.hops.append(node_id)
        self.total_latency += latency
        self.hop_count += 1
        self.last_updated = datetime.now()

class P2PRouting:
    """
    Sistema de routing P2P usando DHT Kademlia-like
    Optimizado para miles de nodos con latencia baja
    """

    def __init__(self, node_id: str, k: int = 20, alpha: int = 3):
        """
        Inicializar el sistema de routing

        Args:
            node_id: ID del nodo actual (string)
            k: Tamaño de los k-buckets
            alpha: Parámetro alpha para lookups concurrentes
        """
        # Convertir node_id a bytes
        self.node_id = hashlib.sha1(node_id.encode()).digest()
        self.k = k
        self.alpha = alpha

        # K-buckets: lista de listas, índice = distancia XOR
        self.k_buckets: List[List[PeerInfo]] = [[] for _ in range(160)]

        # Tabla de rutas: destino -> lista de rutas posibles
        self.routing_table: Dict[bytes, List[Route]] = defaultdict(list)

        # Cache de latencias recientes
        self.latency_cache: Dict[Tuple[bytes, bytes], float] = {}

        # Estadísticas de rendimiento
        self.stats = {
            'routes_found': 0,
            'routes_failed': 0,
            'avg_lookup_time': 0.0,
            'total_messages_routed': 0,
            're_routing_attempts': 0,
            'successful_re_routes': 0
        }

        # Configuración
        self.max_hops = 5  # Máximo 5 saltos
        self.target_latency_ms = 100  # Objetivo <100ms
        self.route_cache_size = 1000  # Tamaño del cache de rutas
        self.latency_timeout = 300  # Timeout para latencias en segundos

        logger.info(f"🛣️ P2P Routing initialized for node {self.node_id[:8].hex()}")

    def _xor_distance(self, a: bytes, b: bytes) -> int:
        """Calcular distancia XOR entre dos node_ids"""
        return int.from_bytes(a, 'big') ^ int.from_bytes(b, 'big')

    def _bucket_index(self, node_id: bytes) -> int:
        """Calcular índice del bucket para un node_id"""
        distance = self._xor_distance(self.node_id, node_id)
        if distance == 0:
            return -1  # Mismo nodo
        return 159 - distance.bit_length() + 1

    def insert_peer(self, peer: PeerInfo):
        """Insertar peer en los k-buckets"""
        bucket_index = self._bucket_index(peer.node_id)
        if bucket_index < 0 or bucket_index >= 160:
            return

        bucket = self.k_buckets[bucket_index]

        # Verificar si ya existe
        for existing in bucket:
            if existing.node_id == peer.node_id:
                existing.last_seen = datetime.now()
                existing.latency_ms = peer.latency_ms
                existing.is_active = True
                return

        # Si bucket no está lleno, agregar
        if len(bucket) < self.k:
            bucket.append(peer)
            logger.debug(f"Added peer {peer.node_id[:8].hex()} to bucket {bucket_index}")
        else:
            # Bucket lleno, intentar reemplazar el menos visto
            # En implementación completa, ping al menos visto
            # Aquí simplificado: reemplazar aleatoriamente
            if random.random() < 0.1:  # 10% chance
                bucket[random.randint(0, self.k-1)] = peer

    def _find_closest_peers(self, target: bytes, count: Optional[int] = None) -> List[PeerInfo]:
        """Encontrar los peers más cercanos a un target"""
        if count is None:
            count = self.k
        candidates = []

        for bucket in self.k_buckets:
            for peer in bucket:
                if peer.is_active:
                    distance = self._xor_distance(target, peer.node_id)
                    candidates.append((distance, peer))

        # Ordenar por distancia
        candidates.sort(key=lambda x: x[0])
        return [peer for _, peer in candidates[:count]]

    async def lookup(self, target: bytes) -> List[PeerInfo]:
        """
        Lookup Kademlia: encontrar nodos más cercanos al target
        """
        start_time = time.time()

        # Empezar con los más cercanos conocidos
        closest = self._find_closest_peers(target, self.k)
        if not closest:
            return []

        # Conjunto de nodos contactados
        contacted = set()
        candidates = closest.copy()

        while candidates:
            # Tomar alpha nodos no contactados
            to_contact = []
            for peer in candidates:
                if peer.node_id not in contacted and len(to_contact) < self.alpha:
                    to_contact.append(peer)

            if not to_contact:
                break

            # Marcar como contactados
            for peer in to_contact:
                contacted.add(peer.node_id)

            # En simulación, asumir que encontramos más peers
            # En implementación real, enviar FIND_NODE queries
            # Aquí simplificado: agregar peers aleatorios cercanos
            for peer in to_contact:
                # Simular respuesta con peers más cercanos
                new_peers = self._simulate_find_node_response(target, peer.node_id)
                for new_peer in new_peers:
                    if new_peer.node_id not in [p.node_id for p in candidates]:
                        candidates.append(new_peer)

            # Re-ordenar candidatos por distancia
            candidates.sort(key=lambda p: self._xor_distance(target, p.node_id))

            # Limitar a k mejores
            candidates = candidates[:self.k]

        lookup_time = time.time() - start_time
        self.stats['avg_lookup_time'] = (self.stats['avg_lookup_time'] + lookup_time) / 2

        logger.debug(f"Lookup for {target[:8].hex()} completed in {lookup_time:.3f}s, found {len(candidates)} peers")
        return candidates

    def _simulate_find_node_response(self, target: bytes, from_node: bytes) -> List[PeerInfo]:
        """Simular respuesta FIND_NODE (para desarrollo/testing)"""
        # En producción, esto sería una llamada real P2P
        # Aquí generamos peers ficticios cercanos
        peers = []
        for i in range(random.randint(1, 5)):
            # Crear node_id cercano al target
            random_bytes = secrets.token_bytes(20)
            close_id = bytes(a ^ b for a, b in zip(target, random_bytes))
            peers.append(PeerInfo(
                node_id=close_id,
                endpoint=f"127.0.0.1:{8000 + i}",
                latency_ms=random.uniform(10, 50),
                last_seen=datetime.now()
            ))
        return peers

    async def route_message(self, message: Any, destination: bytes) -> Optional[List[bytes]]:
        """
        Enrutar mensaje al destino usando rutas óptimas

        Args:
            message: El mensaje a enrutar
            destination: Node ID del destino

        Returns:
            Lista de hops para la ruta, o None si falla
        """
        start_time = time.time()
        self.stats['total_messages_routed'] += 1

        # Si es el mismo nodo, no routing
        if destination == self.node_id:
            return []

        # Buscar rutas existentes
        existing_routes = self.routing_table.get(destination, [])
        valid_routes = [r for r in existing_routes if r.hop_count <= self.max_hops and r.total_latency < self.target_latency_ms]

        if valid_routes:
            # Seleccionar la mejor ruta (menor latencia)
            best_route = min(valid_routes, key=lambda r: r.total_latency)
            logger.info(f"Using cached route to {destination[:8].hex()}: {best_route.hop_count} hops, {best_route.total_latency:.1f}ms")
            return best_route.hops

        # No hay rutas cached, hacer lookup
        closest_peers = await self.lookup(destination)

        if not closest_peers:
            self.stats['routes_failed'] += 1
            logger.warning(f"No route found to {destination[:8].hex()}")
            return None

        # Construir rutas posibles
        routes = await self._build_routes(destination, closest_peers)

        if not routes:
            self.stats['routes_failed'] += 1
            logger.warning(f"Failed to build route to {destination[:8].hex()}")
            return None

        # Seleccionar mejor ruta
        best_route = min(routes, key=lambda r: r.total_latency)

        # Cache la ruta
        self.routing_table[destination].append(best_route)
        if len(self.routing_table[destination]) > 10:  # Limitar cache
            self.routing_table[destination].sort(key=lambda r: r.total_latency)
            self.routing_table[destination] = self.routing_table[destination][:10]

        self.stats['routes_found'] += 1
        routing_time = time.time() - start_time
        logger.info(f"Routed message to {destination[:8].hex()}: {best_route.hop_count} hops, {best_route.total_latency:.1f}ms, time: {routing_time:.3f}s")

        return best_route.hops

    async def _build_routes(self, destination: bytes, closest_peers: List[PeerInfo]) -> List[Route]:
        """Construir rutas posibles al destino"""
        routes = []

        # Para cada peer cercano, intentar construir ruta
        for peer in closest_peers[:5]:  # Limitar a 5 candidatos
            route = Route()
            current_node = self.node_id
            visited = set([self.node_id])

            # BFS limitado para encontrar ruta
            queue = deque([(current_node, 0.0, [])])  # node, latency_so_far, path

            while queue and route.hop_count < self.max_hops:
                current, latency_so_far, path = queue.popleft()

                if current == destination:
                    # Encontramos el destino
                    route.hops = path
                    route.total_latency = latency_so_far
                    route.hop_count = len(path)
                    routes.append(route)
                    break

                # Encontrar próximos hops desde current
                next_hops = self._find_next_hops(current, destination, visited)

                for next_hop, hop_latency in next_hops:
                    if next_hop not in visited:
                        visited.add(next_hop)
                        new_path = path + [next_hop]
                        new_latency = latency_so_far + hop_latency
                        if new_latency < self.target_latency_ms:
                            queue.append((next_hop, new_latency, new_path))

        return routes

    def _find_next_hops(self, from_node: bytes, destination: bytes, visited: Set[bytes]) -> List[Tuple[bytes, float]]:
        """Encontrar próximos hops desde un nodo hacia el destino"""
        # En simulación, usar peers conocidos
        # En producción, consultar al nodo from_node
        candidates = []

        for bucket in self.k_buckets:
            for peer in bucket:
                if peer.node_id not in visited and peer.is_active:
                    distance_from = self._xor_distance(from_node, peer.node_id)
                    distance_to_dest = self._xor_distance(peer.node_id, destination)
                    # Preferir peers que estén más cerca del destino
                    score = distance_to_dest
                    candidates.append((score, peer))

        candidates.sort(key=lambda x: x[0])
        return [(peer.node_id, peer.latency_ms) for _, peer in candidates[:3]]

    async def re_route_message(self, message: Any, destination: bytes, failed_hops: List[bytes]) -> Optional[List[bytes]]:
        """
        Re-enrutar mensaje evitando hops fallidos
        """
        self.stats['re_routing_attempts'] += 1

        logger.info(f"Attempting re-routing to {destination[:8].hex()}, avoiding {len(failed_hops)} failed hops")

        # Marcar hops fallidos como inactivos temporalmente
        for hop in failed_hops:
            for bucket in self.k_buckets:
                for peer in bucket:
                    if peer.node_id == hop:
                        peer.is_active = False

        # Intentar routing normal
        new_route = await self.route_message(message, destination)

        if new_route:
            self.stats['successful_re_routes'] += 1
            logger.info(f"Re-routing successful: {len(new_route)} hops")
        else:
            logger.warning("Re-routing failed")

        # Restaurar peers (simplificado)
        await asyncio.sleep(60)  # Esperar antes de reactivar
        for hop in failed_hops:
            for bucket in self.k_buckets:
                for peer in bucket:
                    if peer.node_id == hop:
                        peer.is_active = True

        return new_route

    def update_route_latency(self, route_hops: List[bytes], measured_latency: float):
        """Actualizar latencia de una ruta"""
        if not route_hops:
            return

        destination = route_hops[-1]
        routes = self.routing_table.get(destination, [])

        for route in routes:
            if route.hops == route_hops:
                route.total_latency = measured_latency
                route.last_updated = datetime.now()
                break

    def cleanup_stale_routes(self):
        """Limpiar rutas obsoletas"""
        current_time = datetime.now()
        for dest, routes in list(self.routing_table.items()):
            valid_routes = []
            for route in routes:
                if (current_time - route.last_updated).total_seconds() < self.latency_timeout:
                    valid_routes.append(route)
            if valid_routes:
                self.routing_table[dest] = valid_routes
            else:
                del self.routing_table[dest]

    def get_routing_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de routing"""
        return {
            'routes_cached': sum(len(routes) for routes in self.routing_table.values()),
            'peers_known': sum(len(bucket) for bucket in self.k_buckets),
            'active_peers': sum(1 for bucket in self.k_buckets for peer in bucket if peer.is_active),
            **self.stats
        }

    def log_performance_metrics(self):
        """Log de métricas de rendimiento"""
        stats = self.get_routing_stats()
        logger.info(f"📊 Routing Performance: {stats['routes_found']} routes found, "
                   f"{stats['routes_failed']} failed, "
                   f"avg lookup: {stats['avg_lookup_time']:.3f}s, "
                   f"re-route success: {stats['successful_re_routes']}/{stats['re_routing_attempts']}")

# Función de utilidad para crear node_id
def generate_node_id(identifier: str) -> bytes:
    """Generar node ID consistente desde un identificador"""
    return hashlib.sha1(identifier.encode()).digest()

if __name__ == '__main__':
    # Demo básico
    async def demo():
        routing = P2PRouting("demo_node")

        # Agregar algunos peers
        for i in range(10):
            peer_id = generate_node_id(f"peer_{i}")
            peer = PeerInfo(
                node_id=peer_id,
                endpoint=f"127.0.0.1:{8000 + i}",
                latency_ms=random.uniform(10, 100)
            )
            routing.insert_peer(peer)

        print("🛣️ P2P Routing Demo")
        print("=" * 30)

        # Hacer lookup
        target = generate_node_id("target_node")
        closest = await routing.lookup(target)
        print(f"✅ Found {len(closest)} closest peers to target")

        # Routing de mensaje
        route = await routing.route_message("test_message", target)
        if route:
            print(f"✅ Route found: {len(route)} hops")
        else:
            print("❌ No route found")

        # Estadísticas
        stats = routing.get_routing_stats()
        print(f"📈 Stats: {stats['peers_known']} peers known, {stats['routes_cached']} routes cached")

        print("🎉 Demo completed!")

    asyncio.run(demo())