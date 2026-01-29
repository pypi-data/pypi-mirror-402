import asyncio
import logging
import time
from typing import Dict, Set, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

class PeerManager:
    """
    Gestiona el pool de conexiones P2P, manteniendo peers activos,
    reconexión automática, health checks con pings/heartbeats,
    limpieza de inactivos y límites de concurrencia.
    """

    def __init__(self, max_peers: int = 100, max_concurrent_connections: int = 10, heartbeat_interval: int = 30, inactive_timeout: int = 300):
        self.max_peers = max_peers
        self.max_concurrent_connections = max_concurrent_connections
        self.heartbeat_interval = heartbeat_interval  # segundos
        self.inactive_timeout = inactive_timeout  # 5 minutos

        self.peers: Dict[str, Dict] = {}  # peer_id -> {'address': (host, port), 'last_seen': timestamp, 'connected': bool, 'task': Optional[asyncio.Task]}
        self.active_connections: Set[str] = set()
        self.semaphore = asyncio.Semaphore(max_concurrent_connections)
        self._running = False
        self._health_check_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """Inicia el manager: health checks y limpieza."""
        if self._running:
            return
        self._running = True
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("PeerManager iniciado")

    async def stop(self):
        """Detiene el manager y cierra conexiones."""
        self._running = False
        if self._health_check_task:
            self._health_check_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        for peer_id in list(self.peers.keys()):
            await self._disconnect_peer(peer_id)
        logger.info("PeerManager detenido")

    async def add_peer(self, peer_id: str, address: tuple[str, int]) -> bool:
        """Agrega un peer al pool y intenta conectar."""
        if len(self.peers) >= self.max_peers:
            logger.warning(f"No se puede agregar peer {peer_id}: pool lleno ({self.max_peers})")
            return False
        if peer_id in self.peers:
            logger.info(f"Peer {peer_id} ya existe")
            return True

        self.peers[peer_id] = {
            'address': address,
            'last_seen': time.time(),
            'connected': False,
            'task': None
        }
        logger.info(f"Peer {peer_id} agregado al pool")
        await self._connect_peer(peer_id)
        return True

    async def remove_peer(self, peer_id: str) -> bool:
        """Remueve un peer del pool."""
        if peer_id not in self.peers:
            logger.warning(f"Peer {peer_id} no encontrado")
            return False
        await self._disconnect_peer(peer_id)
        del self.peers[peer_id]
        logger.info(f"Peer {peer_id} removido del pool")
        return True

    async def health_check(self):
        """Realiza health check manual en todos los peers."""
        tasks = []
        for peer_id in list(self.peers.keys()):
            tasks.append(self._ping_peer(peer_id))
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _connect_peer(self, peer_id: str):
        """Conecta a un peer de forma asíncrona."""
        async with self.semaphore:
            if peer_id not in self.peers or self.peers[peer_id]['connected']:
                return
            try:
                # Simulación de conexión (reemplazar con lógica real de conexión P2P)
                await asyncio.sleep(0.1)  # Simular latencia
                self.peers[peer_id]['connected'] = True
                self.peers[peer_id]['last_seen'] = time.time()
                self.active_connections.add(peer_id)
                logger.info(f"Conectado a peer {peer_id}")
                # Iniciar heartbeat si no existe
                if not self.peers[peer_id]['task']:
                    self.peers[peer_id]['task'] = asyncio.create_task(self._heartbeat_peer(peer_id))
            except Exception as e:
                logger.error(f"Error conectando a peer {peer_id}: {e}")
                await self._reconnect_peer(peer_id)

    async def _disconnect_peer(self, peer_id: str):
        """Desconecta a un peer."""
        if peer_id not in self.peers:
            return
        if self.peers[peer_id]['task']:
            self.peers[peer_id]['task'].cancel()
        self.peers[peer_id]['connected'] = False
        self.active_connections.discard(peer_id)
        logger.info(f"Desconectado de peer {peer_id}")

    async def _reconnect_peer(self, peer_id: str):
        """Intenta reconectar a un peer después de un delay."""
        if not self._running or peer_id not in self.peers:
            return
        await asyncio.sleep(5)  # Delay de reconexión
        logger.info(f"Intentando reconectar a peer {peer_id}")
        await self._connect_peer(peer_id)

    async def _ping_peer(self, peer_id: str):
        """Envía ping a un peer."""
        if peer_id not in self.peers or not self.peers[peer_id]['connected']:
            return
        try:
            # Simulación de ping (reemplazar con lógica real)
            await asyncio.sleep(0.05)  # Simular ping
            self.peers[peer_id]['last_seen'] = time.time()
            logger.debug(f"Ping exitoso a peer {peer_id}")
        except Exception as e:
            logger.warning(f"Ping fallido a peer {peer_id}: {e}")
            await self._disconnect_peer(peer_id)
            await self._reconnect_peer(peer_id)

    async def _heartbeat_peer(self, peer_id: str):
        """Envía heartbeats periódicos a un peer."""
        while self._running and peer_id in self.peers and self.peers[peer_id]['connected']:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                await self._ping_peer(peer_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en heartbeat para peer {peer_id}: {e}")
                await self._disconnect_peer(peer_id)
                await self._reconnect_peer(peer_id)

    async def _health_check_loop(self):
        """Loop de health checks periódicos."""
        while self._running:
            await asyncio.sleep(60)  # Cada minuto
            await self.health_check()

    async def _cleanup_loop(self):
        """Loop de limpieza de peers inactivos."""
        while self._running:
            await asyncio.sleep(60)  # Cada minuto
            current_time = time.time()
            to_remove = []
            for peer_id, data in self.peers.items():
                if current_time - data['last_seen'] > self.inactive_timeout:
                    to_remove.append(peer_id)
            for peer_id in to_remove:
                logger.info(f"Removiendo peer inactivo {peer_id}")
                await self.remove_peer(peer_id)