"""
Physical Node Manager - Gestión de nodos físicos para federated learning.
Conecta dispositivos reales al coordinador federado.
"""

import asyncio
import socket
import psutil
import platform
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import threading

from ..core.logging import get_logger
from ..federated.session import FederatedSession
from ..federated.trainer import FederatedTrainer
from ..infrastructure.ipfs_embedded import IPFSManager
from ..blockchain import get_token_manager

logger = get_logger(__name__)

logger = get_logger(__name__)


@dataclass
class NodeCapabilities:
    """Capacidades de un nodo físico."""
    cpu_cores: int
    memory_gb: float
    gpu_available: bool
    gpu_memory_gb: Optional[float] = None
    gpu_name: Optional[str] = None
    network_speed_mbps: Optional[float] = None
    storage_gb: float = 0.0
    supports_cuda: bool = False
    supports_metal: bool = False  # Para Apple Silicon
    supports_opencl: bool = False


@dataclass
class NodeStatus:
    """Estado actual de un nodo."""
    node_id: str
    is_online: bool
    is_training: bool
    current_session: Optional[str] = None
    last_heartbeat: float = 0.0
    total_training_time: float = 0.0
    total_samples_processed: int = 0
    dracma_earned: float = 0.0
    capabilities: NodeCapabilities = None
    ip_address: Optional[str] = None
    coordinator_url: Optional[str] = None


class PhysicalNodeManager:
    """
    Gestor de nodos físicos que conecta dispositivos reales al sistema federado.
    Maneja registro, monitoreo y comunicación con el coordinador.
    """

    def __init__(self, coordinator_url: str = "http://136.119.191.184:8000"):
        self.coordinator_url = coordinator_url
        self.node_id = self._generate_node_id()
        self.capabilities = self._detect_capabilities()
        self.status = NodeStatus(
            node_id=self.node_id,
            is_online=False,
            is_training=False,
            capabilities=self.capabilities,
            coordinator_url=coordinator_url
        )

        # Componentes REALES
        self.ipfs_manager: Optional[IPFSManager] = None
        self.trainer: Optional[FederatedTrainer] = None
        self.token_manager = get_token_manager()

        # Estado REAL
        self.heartbeat_interval = 30  # segundos
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.is_running = False

        # Sesiones activas REALES
        self.active_sessions: Dict[str, FederatedSession] = {}

        # Estadísticas del nodo REALES
        self.system_stats = {
            "sessions_joined": 0,
            "total_training_time": 0.0,
            "total_rewards_earned": 0.0,
            "data_processed_gb": 0.0,
            "start_time": time.time()
        }

        logger.info(f"🖥️ Physical Node Manager initialized with REAL components: {self.node_id}")

    def _generate_node_id(self) -> str:
        """Genera ID único para el nodo basado en hardware."""
        system_info = f"{platform.node()}_{platform.machine()}_{socket.gethostname()}"
        return f"node_{hashlib.sha256(system_info.encode()).hexdigest()[:16]}"

    def _detect_capabilities(self) -> NodeCapabilities:
        """Detecta capacidades del hardware disponible."""
        # CPU
        cpu_cores = psutil.cpu_count(logical=True)
        physical_cores = psutil.cpu_count(logical=False)

        # Memoria
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)

        # Almacenamiento
        disk = psutil.disk_usage('/')
        storage_gb = disk.total / (1024**3)

        # GPU (simplificado - en producción usar librerías específicas)
        gpu_available = False
        gpu_memory_gb = None
        gpu_name = None
        supports_cuda = False
        supports_metal = False
        supports_opencl = False

        try:
            # Detectar GPU
            if platform.system() == "Darwin":  # macOS
                # Apple Silicon detection
                import subprocess
                result = subprocess.run(['system_profiler', 'SPHardwareDataType'],
                                      capture_output=True, text=True)
                if "Apple M" in result.stdout:
                    gpu_available = True
                    gpu_name = "Apple Silicon GPU"
                    supports_metal = True
                    # Estimar memoria GPU (típico para M1/M2)
                    gpu_memory_gb = 8.0 if "M1" in result.stdout else 16.0
            else:
                # Linux/Windows - buscar NVIDIA
                try:
                    import GPUtil
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        gpu = gpus[0]  # Usar primera GPU
                        gpu_available = True
                        gpu_name = gpu.name
                        gpu_memory_gb = gpu.memoryTotal / 1024  # GB
                        supports_cuda = "NVIDIA" in gpu.name.upper()
                        supports_opencl = True
                except ImportError:
                    logger.warning("GPUtil not available, GPU detection limited")

        except Exception as e:
            logger.warning(f"GPU detection failed: {e}")

        # Red (estimación básica)
        network_speed_mbps = None
        try:
            # Medir velocidad de red básica
            import speedtest
            st = speedtest.Speedtest()
            st.get_best_server()
            download_speed = st.download() / 1_000_000  # Mbps
            network_speed_mbps = download_speed
        except ImportError:
            logger.debug("speedtest not available, network speed not measured")
        except Exception as e:
            logger.warning(f"Network speed detection failed: {e}")

        return NodeCapabilities(
            cpu_cores=cpu_cores,
            memory_gb=round(memory_gb, 1),
            gpu_available=gpu_available,
            gpu_memory_gb=round(gpu_memory_gb, 1) if gpu_memory_gb else None,
            gpu_name=gpu_name,
            network_speed_mbps=round(network_speed_mbps, 1) if network_speed_mbps else None,
            storage_gb=round(storage_gb, 1),
            supports_cuda=supports_cuda,
            supports_metal=supports_metal,
            supports_opencl=supports_opencl
        )

    async def start_node(self) -> bool:
        """
        Inicia el nodo físico REAL y lo registra con el coordinador.

        Returns:
            True si el inicio fue exitoso
        """
        try:
            logger.info("🚀 Starting physical node with REAL components...")

            # Inicializar IPFS REAL
            self.ipfs_manager = IPFSManager()
            await self.ipfs_manager.start()

            # Inicializar trainer REAL
            self.trainer = FederatedTrainer(node_id=self.node_id)

            # Registrar con coordinador REAL
            success = await self._register_with_coordinator()
            if not success:
                logger.error("❌ Failed to register with coordinator")
                return False

            # Marcar como online REAL
            self.status.is_online = True
            self.status.last_heartbeat = time.time()
            self.status.ip_address = self._get_local_ip()
            self.is_running = True

            # Iniciar heartbeat REAL
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self.heartbeat_thread.start()

            logger.info(f"✅ Physical node started successfully with REAL components: {self.node_id}")
            logger.info(f"   📍 IP: {self.status.ip_address}")
            logger.info(f"   🖥️ CPU: {self.capabilities.cpu_cores} cores")
            logger.info(f"   💾 RAM: {self.capabilities.memory_gb} GB")
            logger.info(f"   🎮 GPU: {self.capabilities.gpu_name or 'None'}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to start physical node: {e}")
            return False

    async def stop_node(self):
        """Detiene el nodo físico."""
        logger.info("🛑 Stopping physical node...")

        self.is_running = False
        self.status.is_online = False

        # Detener heartbeat
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=5)

        # Cerrar conexiones
        if self.ipfs_manager:
            await self.ipfs_manager.stop()

        # Limpiar sesiones activas
        self.active_sessions.clear()

        logger.info("✅ Physical node stopped")

    async def _register_with_coordinator(self) -> bool:
        """
        Registra el nodo con el coordinador federado.

        Returns:
            True si el registro fue exitoso
        """
        try:
            import aiohttp

            registration_data = {
                "node_id": self.node_id,
                "capabilities": asdict(self.capabilities),
                "ip_address": self._get_local_ip(),
                "registration_time": time.time()
            }

            async with aiohttp.ClientSession() as session:
                url = f"{self.coordinator_url}/api/nodes/register"
                async with session.post(url, json=registration_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"✅ Node registered with coordinator: {result}")
                        return True
                    else:
                        error = await response.text()
                        logger.error(f"❌ Registration failed: {error}")
                        return False

        except Exception as e:
            logger.error(f"❌ Registration error: {e}")
            return False

    def _heartbeat_loop(self):
        """Loop de heartbeat que se ejecuta en un thread separado."""
        while self.is_running:
            try:
                # Ejecutar heartbeat de manera asíncrona
                asyncio.run(self._send_heartbeat())
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

            time.sleep(self.heartbeat_interval)

    async def _send_heartbeat(self):
        """Envía heartbeat al coordinador."""
        try:
            import aiohttp

            heartbeat_data = {
                "node_id": self.node_id,
                "timestamp": time.time(),
                "status": asdict(self.status),
                "capabilities": asdict(self.capabilities)
            }

            async with aiohttp.ClientSession() as session:
                url = f"{self.coordinator_url}/api/nodes/{self.node_id}/heartbeat"
                async with session.post(url, json=heartbeat_data) as response:
                    if response.status == 200:
                        # Actualizar estado local
                        self.status.last_heartbeat = time.time()
                    else:
                        logger.warning(f"Heartbeat failed: {response.status}")

        except Exception as e:
            logger.error(f"Heartbeat send error: {e}")

    async def join_federated_session(self, session_id: str) -> bool:
        """
        Une el nodo a una sesión de entrenamiento federado REAL.

        Args:
            session_id: ID de la sesión

        Returns:
            True si se unió exitosamente
        """
        try:
            if not self.trainer:
                logger.error("Trainer not initialized")
                return False

            logger.info(f"🔗 Joining federated session: {session_id}")

            # Unirse a la sesión REAL
            success = await self.trainer.join_session(session_id, self.coordinator_url)
            if success:
                self.status.is_training = True
                self.status.current_session = session_id
                self.active_sessions[session_id] = self.trainer.current_session

                # Actualizar estadísticas REALES
                self.system_stats["sessions_joined"] += 1

                logger.info(f"✅ Joined federated session: {session_id}")
                logger.info(f"   📊 Total sessions joined: {self.system_stats['sessions_joined']}")
                return True
            else:
                logger.error(f"❌ Failed to join session: {session_id}")
                return False

        except Exception as e:
            logger.error(f"Error joining session: {e}")
            return False

    async def leave_federated_session(self, session_id: str):
        """
        Abandona una sesión de entrenamiento federado.

        Args:
            session_id: ID de la sesión
        """
        try:
            if session_id in self.active_sessions:
                # Aquí iría la lógica para notificar al coordinador
                del self.active_sessions[session_id]

            if self.status.current_session == session_id:
                self.status.is_training = False
                self.status.current_session = None

            logger.info(f"✅ Left federated session: {session_id}")

        except Exception as e:
            logger.error(f"Error leaving session: {e}")

    async def get_node_status(self) -> Dict[str, Any]:
        """
        Obtiene estado completo del nodo REAL.

        Returns:
            Información del estado del nodo
        """
        # Actualizar métricas en tiempo real REALES
        self._update_realtime_metrics()

        # Calcular uptime
        uptime_seconds = time.time() - self.system_stats["start_time"]
        uptime_hours = uptime_seconds / 3600

        return {
            "node_id": self.node_id,
            "status": asdict(self.status),
            "capabilities": asdict(self.capabilities),
            "active_sessions": list(self.active_sessions.keys()),
            "system_info": self._get_system_info(),
            "performance_metrics": self._get_performance_metrics(),
            "system_stats": {
                "sessions_joined": self.system_stats["sessions_joined"],
                "total_training_time": self.system_stats["total_training_time"],
                "total_rewards_earned": self.system_stats["total_rewards_earned"],
                "data_processed_gb": self.system_stats["data_processed_gb"],
                "uptime_hours": f"{uptime_hours:.1f}",
                "node_health": "healthy" if self.status.is_online else "offline"
            }
        }

    def _update_realtime_metrics(self):
        """Actualiza métricas en tiempo real."""
        try:
            # CPU y memoria
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            # Actualizar estado (esto sería usado por el trainer)
            if self.trainer and hasattr(self.trainer, 'performance_metrics'):
                self.trainer.performance_metrics.update({
                    "cpu_usage": cpu_percent,
                    "memory_usage": memory.percent,
                    "memory_used_gb": memory.used / (1024**3)
                })

        except Exception as e:
            logger.debug(f"Metrics update failed: {e}")

    def _get_system_info(self) -> Dict[str, Any]:
        """Obtiene información del sistema."""
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "hostname": socket.gethostname(),
            "ip_address": self._get_local_ip(),
            "uptime": time.time() - psutil.boot_time()
        }

    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de rendimiento."""
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": round(memory.used / (1024**3), 1),
                "memory_total_gb": round(memory.total / (1024**3), 1),
                "disk_used_gb": round(disk.used / (1024**3), 1),
                "disk_total_gb": round(disk.total / (1024**3), 1),
                "disk_percent": disk.percent
            }
        except Exception as e:
            logger.error(f"Performance metrics error: {e}")
            return {}

    def _get_local_ip(self) -> str:
        """Obtiene IP local."""
        try:
            # Crear socket para obtener IP local
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # Conectar a Google DNS
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"

    async def update_capabilities(self):
        """Actualiza capacidades del nodo (útil si cambia el hardware)."""
        self.capabilities = self._detect_capabilities()
        self.status.capabilities = self.capabilities
        logger.info("🔄 Node capabilities updated")


# Funciones de conveniencia
async def create_physical_node(coordinator_url: str = None) -> PhysicalNodeManager:
    """
    Crea y configura un nuevo nodo físico.

    Args:
        coordinator_url: URL del coordinador (opcional)

    Returns:
        Nodo físico configurado
    """
    if coordinator_url is None:
        coordinator_url = "http://136.119.191.184:8000"  # Default coordinator

    node = PhysicalNodeManager(coordinator_url=coordinator_url)
    return node


async def start_physical_node(coordinator_url: str = None) -> PhysicalNodeManager:
    """
    Crea e inicia un nodo físico.

    Args:
        coordinator_url: URL del coordinador

    Returns:
        Nodo físico iniciado
    """
    node = await create_physical_node(coordinator_url)
    success = await node.start_node()

    if success:
        return node
    else:
        raise RuntimeError("Failed to start physical node")


def get_node_capabilities() -> Dict[str, Any]:
    """
    Obtiene capacidades del dispositivo actual sin crear un nodo completo.

    Returns:
        Capacidades del hardware
    """
    temp_node = PhysicalNodeManager()
    return asdict(temp_node.capabilities)
