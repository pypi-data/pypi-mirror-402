"""
IPFS Version Distributor - Distribución de versiones vía IPFS
Sistema de distribución peer-to-peer con optimización de latencia y replicación.
"""

import asyncio
import time
import json
import hashlib
from typing import Dict, List, Any, Optional, Set, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

from ..core.logging import get_logger
from ..infrastructure.ipfs_embedded import IPFSManager
from .federated_version_manager import FederatedVersionManager, ModelVersion

if TYPE_CHECKING:
    from .node_communicator import NodeCommunicator

try:
    from ..coordinator.services.node_version_service import get_node_version_service
except ImportError:
    # Fallback si no est\u00e1 disponible
    get_node_version_service = None

logger = get_logger(__name__)


class DistributionStrategy(Enum):
    """Estrategias de distribución disponibles."""
    BROADCAST = "broadcast"  # Distribución a todos los nodos
    GEOGRAPHIC = "geographic"  # Distribución basada en ubicación geográfica
    LOAD_BALANCED = "load_balanced"  # Balanceo de carga
    PRIORITY_BASED = "priority_based"  # Basado en prioridad de nodos


class DistributionStatus(Enum):
    """Estados de distribución."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class DistributionTask:
    """Tarea de distribución de una versión."""
    version_id: str
    target_nodes: List[str]
    strategy: DistributionStrategy
    status: DistributionStatus = DistributionStatus.PENDING
    started_at: Optional[int] = None
    completed_at: Optional[int] = None
    progress: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            'version_id': self.version_id,
            'target_nodes': self.target_nodes,
            'strategy': self.strategy.value,
            'status': self.status.value,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'progress': self.progress,
            'errors': self.errors
        }


@dataclass
class NodeDistributionInfo:
    """Información de distribución para un nodo."""
    node_id: str
    ipfs_endpoint: str
    region: Optional[str] = None
    bandwidth_mbps: float = 10.0
    last_seen: int = field(default_factory=lambda: int(time.time()))
    success_rate: float = 1.0
    average_latency_ms: float = 100.0
    active_downloads: int = 0


class IPFSVersionDistributor:
    """
    Distribuidor de versiones basado en IPFS.
    Maneja distribución eficiente, replicación y optimización de red.
    """

    def __init__(self, ipfs_manager: IPFSManager,
                 version_manager: FederatedVersionManager,
                 node_communicator: Optional["NodeCommunicator"] = None,
                 max_concurrent_distributions: int = 10,
                 replication_factor: int = 3):
        """
        Inicializar el distribuidor IPFS.

        Args:
            ipfs_manager: Gestor de IPFS
            version_manager: Gestor de versiones
            node_communicator: Comunicador de nodos para enviar notificaciones
            max_concurrent_distributions: Máximo de distribuciones concurrentes
            replication_factor: Factor de replicación mínimo
        """
        self.ipfs_manager = ipfs_manager
        self.version_manager = version_manager
        self.node_communicator = node_communicator
        self.max_concurrent = max_concurrent_distributions
        self.replication_factor = replication_factor
        
        # Servicio de tracking de versiones
        self.version_service = get_node_version_service() if get_node_version_service else None

        # Estado de distribución
        self.active_distributions: Dict[str, DistributionTask] = {}
        self.node_info: Dict[str, NodeDistributionInfo] = {}
        self.distribution_queue: asyncio.Queue[DistributionTask] = asyncio.Queue()
        
        # Tracking de versiones por nodo
        self.node_versions: Dict[str, Set[str]] = defaultdict(set)
        self.pending_acks: Dict[str, Dict[str, float]] = defaultdict(dict)  # {node_id: {version_id: timestamp}}

        # Estadísticas
        self.stats = {
            'total_distributions': 0,
            'successful_distributions': 0,
            'failed_distributions': 0,
            'total_bytes_distributed': 0,
            'average_distribution_time': 0.0
        }

        # Workers de distribución
        self.distribution_workers: List[asyncio.Task] = []
        self.is_running = False

        # Locks
        self.distribution_lock = asyncio.Lock()

        logger.info(f"🚀 IPFSVersionDistributor initialized with {max_concurrent_distributions} workers")

    async def start(self):
        """Iniciar el distribuidor."""
        if self.is_running:
            return

        self.is_running = True

        # Iniciar workers
        self.distribution_workers = []
        for i in range(self.max_concurrent):
            task = asyncio.create_task(self._distribution_worker())
            self.distribution_workers.append(task)
            logger.debug(f"Started distribution worker {i+1}")

        logger.info(f"✅ IPFSVersionDistributor started with {self.max_concurrent} workers")

    async def stop(self):
        """Detener el distribuidor."""
        if not self.is_running:
            return

        self.is_running = False

        # Cancelar workers
        for task in self.distribution_workers:
            task.cancel()

        # Esperar finalización
        if self.distribution_workers:
            await asyncio.gather(*self.distribution_workers, return_exceptions=True)

        logger.info("🛑 IPFSVersionDistributor stopped")

    async def distribute_version(self, version_id: str, target_nodes: List[str],
                               strategy: DistributionStrategy = DistributionStrategy.BROADCAST,
                               priority: int = 1) -> str:
        """
        Iniciar distribución de una versión.

        Args:
            version_id: ID de la versión a distribuir
            target_nodes: Nodos objetivo
            strategy: Estrategia de distribución
            priority: Prioridad (mayor = más prioritario)

        Returns:
            ID de la tarea de distribución
        """
        async with self.distribution_lock:
            try:
                # Verificar que la versión existe
                version = await self.version_manager.get_version(version_id)
                if not version:
                    raise ValueError(f"Version {version_id} not found")

                # Crear tarea de distribución
                task = DistributionTask(
                    version_id=version_id,
                    target_nodes=target_nodes.copy(),
                    strategy=strategy
                )

                task_id = f"{version_id}_{int(time.time())}"

                # Agregar a cola con prioridad
                await self._enqueue_distribution(task, priority)

                self.active_distributions[task_id] = task

                logger.info(f"📤 Queued distribution of {version_id} to {len(target_nodes)} nodes (strategy: {strategy.value})")
                return task_id

            except Exception as e:
                logger.error(f"❌ Failed to queue distribution for {version_id}: {e}")
                raise

    async def _enqueue_distribution(self, task: DistributionTask, priority: int):
        """Agregar tarea a la cola con prioridad."""
        # Para simplificar, usamos una cola prioritaria básica
        # En producción se podría usar una PriorityQueue
        await self.distribution_queue.put((priority, task))

    async def _distribution_worker(self):
        """Worker que procesa tareas de distribución."""
        while self.is_running:
            try:
                # Obtener tarea de la cola
                priority, task = await self.distribution_queue.get()

                try:
                    await self._execute_distribution(task)
                except Exception as e:
                    logger.error(f"❌ Distribution failed for {task.version_id}: {e}")
                    task.status = DistributionStatus.FAILED
                    task.errors.append(str(e))
                finally:
                    self.distribution_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Distribution worker error: {e}")

    async def _execute_distribution(self, task: DistributionTask):
        """Ejecutar distribución de una versión."""
        task.status = DistributionStatus.IN_PROGRESS
        task.started_at = int(time.time())

        logger.info(f"🎯 Starting distribution of {task.version_id} using {task.strategy.value} strategy")

        try:
            # Obtener versión
            version = await self.version_manager.get_version(task.version_id)
            if not version:
                raise ValueError(f"Version {task.version_id} not found")

            # Aplicar estrategia de distribución
            if task.strategy == DistributionStrategy.BROADCAST:
                await self._distribute_broadcast(version, task)
            elif task.strategy == DistributionStrategy.GEOGRAPHIC:
                await self._distribute_geographic(version, task)
            elif task.strategy == DistributionStrategy.LOAD_BALANCED:
                await self._distribute_load_balanced(version, task)
            elif task.strategy == DistributionStrategy.PRIORITY_BASED:
                await self._distribute_priority_based(version, task)
            else:
                raise ValueError(f"Unknown distribution strategy: {task.strategy}")

            # Verificar replicación
            await self._ensure_replication(version)

            # Actualizar estadísticas
            task.status = DistributionStatus.COMPLETED
            task.completed_at = int(time.time())

            self.stats['total_distributions'] += 1
            self.stats['successful_distributions'] += 1

            distribution_time = task.completed_at - (task.started_at or task.completed_at)
            self._update_average_time(distribution_time)

            logger.info(f"✅ Distribution completed for {task.version_id} in {distribution_time}s")

        except Exception as e:
            task.status = DistributionStatus.FAILED
            task.errors.append(str(e))
            self.stats['failed_distributions'] += 1
            raise

    async def _distribute_broadcast(self, version: ModelVersion, task: DistributionTask):
        """Distribución broadcast a todos los nodos."""
        # Agrupar nodos por región para optimización
        regional_groups = self._group_nodes_by_region(task.target_nodes)

        # Distribuir por grupos regionales concurrentemente
        distribution_tasks = []
        for region, nodes in regional_groups.items():
            task_coro = self._distribute_to_node_group(version, nodes, region)
            distribution_tasks.append(task_coro)

        # Ejecutar todas las distribuciones
        results = await asyncio.gather(*distribution_tasks, return_exceptions=True)

        # Procesar resultados
        successful = 0
        failed = 0
        for i, result in enumerate(results):
            region = list(regional_groups.keys())[i]
            if isinstance(result, Exception):
                logger.warning(f"❌ Distribution failed for region {region}: {result}")
                failed += len(regional_groups[region])
                task.errors.append(f"Region {region}: {str(result)}")
            else:
                successful += result

        task.progress = {
            'successful_nodes': successful,
            'failed_nodes': failed,
            'total_nodes': len(task.target_nodes),
            'success_rate': successful / len(task.target_nodes) if task.target_nodes else 0
        }

        if successful < len(task.target_nodes):
            task.status = DistributionStatus.PARTIAL

    async def _distribute_geographic(self, version: ModelVersion, task: DistributionTask):
        """Distribución basada en ubicación geográfica."""
        # Obtener información de nodos
        node_regions = {}
        for node_id in task.target_nodes:
            node_info = self.node_info.get(node_id)
            region = node_info.region if node_info else 'unknown'
            if region not in node_regions:
                node_regions[region] = []
            node_regions[region].append(node_id)

        # Distribuir por región con optimización
        # (Lógica similar a broadcast pero con optimizaciones geográficas)
        await self._distribute_broadcast(version, task)

    async def _distribute_load_balanced(self, version: ModelVersion, task: DistributionTask):
        """Distribución con balanceo de carga."""
        # Ordenar nodos por carga actual (menos carga primero)
        sorted_nodes = sorted(
            task.target_nodes,
            key=lambda nid: self.node_info.get(nid, NodeDistributionInfo(nid, "")).active_downloads
        )

        # Distribuir en lotes para balancear carga
        batch_size = max(1, len(sorted_nodes) // self.max_concurrent)
        batches = [sorted_nodes[i:i + batch_size] for i in range(0, len(sorted_nodes), batch_size)]

        for batch in batches:
            await self._distribute_to_node_group(version, batch, "load_balanced_batch")
            await asyncio.sleep(0.1)  # Pequeña pausa entre lotes

    async def _distribute_priority_based(self, version: ModelVersion, task: DistributionTask):
        """Distribución basada en prioridad de nodos."""
        # Los nodos ya deberían estar ordenados por prioridad en target_nodes
        # Distribuir secuencialmente para asegurar entrega prioritaria
        for node_id in task.target_nodes:
            try:
                await self._distribute_to_single_node(version, node_id)
                task.progress['successful_nodes'] = task.progress.get('successful_nodes', 0) + 1
            except Exception as e:
                logger.warning(f"❌ Failed to distribute to priority node {node_id}: {e}")
                task.errors.append(f"Node {node_id}: {str(e)}")

    async def _distribute_to_node_group(self, version: ModelVersion, node_ids: List[str],
                                      group_name: str) -> int:
        """Distribuir a un grupo de nodos."""
        logger.debug(f"📦 Distributing {version.version_id} to {len(node_ids)} nodes in group {group_name}")

        # Crear tareas para cada nodo
        node_tasks = []
        for node_id in node_ids:
            task = self._distribute_to_single_node(version, node_id)
            node_tasks.append(task)

        # Ejecutar con concurrencia limitada
        semaphore = asyncio.Semaphore(min(5, len(node_ids)))  # Máximo 5 concurrentes por grupo

        async def limited_task(node_task):
            async with semaphore:
                return await node_task

        # Ejecutar todas las tareas
        results = await asyncio.gather(
            *[limited_task(task) for task in node_tasks],
            return_exceptions=True
        )

        # Contar exitosas
        successful = sum(1 for r in results if not isinstance(r, Exception))
        logger.debug(f"📦 Group {group_name}: {successful}/{len(node_ids)} successful distributions")

        return successful

    async def _distribute_to_single_node(self, version: ModelVersion, node_id: str):
        """Distribuir versión a un nodo específico."""
        try:
            # Obtener información del nodo
            node_info = self.node_info.get(node_id)
            if not node_info:
                # Crear info básica si no existe
                node_info = NodeDistributionInfo(node_id, f"http://localhost:5001/api/v0")
                self.node_info[node_id] = node_info

            # Incrementar contador de descargas activas
            node_info.active_downloads += 1

            try:
                start_time = time.time()

                # Verificar si el nodo ya tiene la versión
                if await self._node_has_version(node_id, version.version_id):
                    logger.debug(f"📦 Node {node_id} already has version {version.version_id}")
                    return

                # Distribuir modelo
                await self._send_version_to_node(version, node_id)

                # Actualizar estadísticas del nodo
                latency = (time.time() - start_time) * 1000  # ms
                node_info.average_latency_ms = (node_info.average_latency_ms + latency) / 2
                node_info.success_rate = (node_info.success_rate * 0.9) + 0.1  # Media móvil
                node_info.last_seen = int(time.time())

                self.stats['total_bytes_distributed'] += len(await self.ipfs_manager.get_data(version.model_cid))

                logger.debug(f"📦 Successfully distributed {version.version_id} to {node_id} ({latency:.1f}ms)")

            finally:
                node_info.active_downloads -= 1

        except Exception as e:
            # Actualizar tasa de éxito
            if node_info:
                node_info.success_rate = (node_info.success_rate * 0.9)  # Penalizar fallo
            raise

    async def _send_version_to_node(self, version: ModelVersion, node_id: str):
        """Enviar versión a un nodo específico."""
        try:
            # Verificar que los CIDs sean accesibles
            model_data = await self.ipfs_manager.get_data(version.model_cid)
            metadata_data = await self.ipfs_manager.get_data(version.metadata_cid)
            
            model_size = len(model_data)
            metadata_size = len(metadata_data)
            
            # Calcular hash para verificación
            expected_hash = hashlib.sha256(model_data).hexdigest()

            logger.debug(f"📦 Version {version.version_id} available: model={model_size} bytes, metadata={metadata_size} bytes")
            
            # Enviar notificación al nodo via NodeCommunicator
            if self.node_communicator:
                success = await self.node_communicator.send_model_distribution_notification(
                    node_id=node_id,
                    version_id=version.version_id,
                    model_cid=version.model_cid,
                    metadata_cid=version.metadata_cid,
                    expected_hash=expected_hash
                )
                
                if success:
                    # Marcar como pendiente de ACK
                    self.pending_acks[node_id][version.version_id] = time.time()
                    logger.info(f"📤 Model distribution notification sent to {node_id} for version {version.version_id}")
                else:
                    raise Exception(f"Failed to send notification to {node_id}")
            else:
                logger.warning("No NodeCommunicator available, distribution notification skipped")

        except Exception as e:
            raise Exception(f"Version data not accessible or notification failed: {e}")

    async def _node_has_version(self, node_id: str, version_id: str) -> bool:
        """Verificar si un nodo ya tiene una versión."""
        # Verificar en el tracking local
        return version_id in self.node_versions.get(node_id, set())

    async def _ensure_replication(self, version: ModelVersion, min_replicas: Optional[int] = None):
        """Asegurar replicación adecuada de la versión."""
        if min_replicas is None:
            min_replicas = self.replication_factor

        # Verificar replicación actual
        model_replicas = await self._count_cid_replicas(version.model_cid)
        metadata_replicas = await self._count_cid_replicas(version.metadata_cid)

        logger.debug(f"📊 Replication check for {version.version_id}: model={model_replicas}, metadata={metadata_replicas}")

        # Pinnear en nodos adicionales si es necesario
        if model_replicas < min_replicas:
            await self._increase_replication(version.model_cid, min_replicas - model_replicas)

        if metadata_replicas < min_replicas:
            await self._increase_replication(version.metadata_cid, min_replicas - metadata_replicas)

    async def _count_cid_replicas(self, cid: str) -> int:
        """Contar número de réplicas de un CID."""
        try:
            # Contar cuántos nodos tienen este CID
            replica_count = 0
            for node_id, versions in self.node_versions.items():
                # Para cada versión del nodo, verificar si tiene este CID
                for version_id in versions:
                    version = await self.version_manager.get_version(version_id)
                    if version and (version.model_cid == cid or version.metadata_cid == cid):
                        replica_count += 1
                        break  # Contar solo una vez por nodo
            
            # Añadir 1 si el coordinator tiene el CID
            try:
                await self.ipfs_manager.get_data(cid)
                replica_count += 1
            except:
                pass
            
            return replica_count
        except Exception as e:
            logger.error(f"Error counting replicas for {cid}: {e}")
            return 1  # Asumir al menos 1 réplica

    async def _increase_replication(self, cid: str, additional_replicas: int):
        """Aumentar replicación de un CID."""
        try:
            # Pin el CID en el coordinator's IPFS node
            await self.ipfs_manager.pin_data(cid)
            logger.info(f"📌 Pinned {cid} on coordinator node to increase replication")
            
            # En un cluster IPFS real, aquí se enviarían comandos para pin en nodos adicionales
            # Por ahora, el pinning en el coordinator asegura al menos una réplica persistente
            
        except Exception as e:
            logger.error(f"Error increasing replication for {cid}: {e}")

    def _group_nodes_by_region(self, node_ids: List[str]) -> Dict[str, List[str]]:
        """Agrupar nodos por región."""
        groups = defaultdict(list)
        for node_id in node_ids:
            node_info = self.node_info.get(node_id)
            region = node_info.region if node_info else 'unknown'
            groups[region].append(node_id)
        return dict(groups)

    def _update_average_time(self, distribution_time: float):
        """Actualizar tiempo promedio de distribución."""
        current_avg = self.stats['average_distribution_time']
        total_dist = self.stats['total_distributions']

        if total_dist == 1:
            self.stats['average_distribution_time'] = distribution_time
        else:
            # Media móvil
            self.stats['average_distribution_time'] = (current_avg * (total_dist - 1) + distribution_time) / total_dist

    async def get_distribution_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de una tarea de distribución."""
        task = self.active_distributions.get(task_id)
        if not task:
            return None

        return task.to_dict()

    def register_node(self, node_id: str, ipfs_endpoint: str, region: Optional[str] = None,
                     bandwidth_mbps: float = 10.0):
        """Registrar información de un nodo."""
        self.node_info[node_id] = NodeDistributionInfo(
            node_id=node_id,
            ipfs_endpoint=ipfs_endpoint,
            region=region,
            bandwidth_mbps=bandwidth_mbps
        )
        logger.info(f"📝 Registered node {node_id} in region {region}")

    def get_distribution_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de distribución."""
        return {
            'total_distributions': self.stats['total_distributions'],
            'successful_distributions': self.stats['successful_distributions'],
            'failed_distributions': self.stats['failed_distributions'],
            'success_rate': self.stats['successful_distributions'] / max(1, self.stats['total_distributions']),
            'total_bytes_distributed': self.stats['total_bytes_distributed'],
            'average_distribution_time': self.stats['average_distribution_time'],
            'active_distributions': len(self.active_distributions),
            'registered_nodes': len(self.node_info),
            'queue_size': self.distribution_queue.qsize()
        }

    async def cancel_distribution(self, task_id: str) -> bool:
        """Cancelar una tarea de distribución."""
        # En una implementación completa, esto cancelaría la tarea
        # Por ahora, solo la marcamos como fallida
        if task_id in self.active_distributions:
            self.active_distributions[task_id].status = DistributionStatus.FAILED
            self.active_distributions[task_id].errors.append("Cancelled by user")
            logger.info(f"🛑 Cancelled distribution {task_id}")
            return True
        return False

    async def confirm_node_version(self, node_id: str, version_id: str, verified_hash: str) -> bool:
        """
        Confirmar que un nodo descargó y verificó una versión.
        
        Args:
            node_id: ID del nodo
            version_id: ID de la versión
            verified_hash: Hash verificado por el nodo
            
        Returns:
            True si la confirmación fue exitosa
        """
        try:
            # Verificar que estaba pendiente
            if node_id not in self.pending_acks or version_id not in self.pending_acks[node_id]:
                logger.warning(f"No pending ACK found for {node_id}/{version_id}")
                return False
            
            # Obtener versión para verificar hash
            version = await self.version_manager.get_version(version_id)
            if not version:
                logger.error(f"Version {version_id} not found")
                return False
            
            # Calcular hash esperado
            model_data = await self.ipfs_manager.get_data(version.model_cid)
            expected_hash = hashlib.sha256(model_data).hexdigest()
            
            # Verificar hash
            if verified_hash != expected_hash:
                logger.error(f"Hash mismatch for {node_id}/{version_id}: expected {expected_hash}, got {verified_hash}")
                return False
            
            # Marcar como confirmado
            self.node_versions[node_id].add(version_id)
            del self.pending_acks[node_id][version_id]
            
            logger.info(f"✅ Node {node_id} confirmed version {version_id} (hash verified)")
            return True
            
        except Exception as e:
            logger.error(f"Error confirming version for {node_id}: {e}")
            return False

    async def cleanup_completed_distributions(self, max_age_seconds: int = 3600):
        """Limpiar tareas de distribución completadas."""
        current_time = int(time.time())
        to_remove = []

        for task_id, task in self.active_distributions.items():
            if task.completed_at and (current_time - task.completed_at) > max_age_seconds:
                to_remove.append(task_id)

        for task_id in to_remove:
            del self.active_distributions[task_id]

        if to_remove:
            logger.info(f"🧹 Cleaned up {len(to_remove)} old distribution tasks")