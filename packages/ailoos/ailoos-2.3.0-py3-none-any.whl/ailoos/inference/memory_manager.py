"""
Sistema de Memory Paging para AILOOS.
Mueve páginas de memoria neural entre GPU, RAM y disco de forma transparente.
"""

import os
import asyncio
import threading
import time
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import psutil
import gc

try:
    import torch
    import torch.cuda
except ImportError:
    torch = None

from ..utils.logging import get_logger
from ..core.state_manager import get_tensor_state_manager


class MemoryLocation(Enum):
    """Ubicaciones posibles de memoria."""
    GPU = "gpu"
    CPU = "cpu"
    DISK = "disk"


class PagePriority(Enum):
    """Prioridades de paginación."""
    CRITICAL = 0  # Nunca paginar
    HIGH = 1      # Paginar solo si necesario
    MEDIUM = 2    # Paginar normalmente
    LOW = 3       # Paginar primero


@dataclass
class MemoryPage:
    """Página de memoria neural."""
    tensor_id: str
    tensor: Optional[torch.Tensor] = None
    location: MemoryLocation = MemoryLocation.CPU
    size_bytes: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    priority: PagePriority = PagePriority.MEDIUM
    pinned: bool = False  # No paginar si está pinned
    disk_path: Optional[str] = None


@dataclass
class MemoryStats:
    """Estadísticas de memoria."""
    gpu_used: int = 0
    gpu_total: int = 0
    cpu_used: int = 0
    cpu_total: int = 0
    disk_used: int = 0
    pages_gpu: int = 0
    pages_cpu: int = 0
    pages_disk: int = 0
    page_faults: int = 0
    page_hits: int = 0


class MemoryManager:
    """
    Gestor de memoria con paginación transparente entre GPU, CPU y disco.
    """

    def __init__(self, gpu_memory_limit: float = 0.8,
                 cpu_memory_limit: float = 0.7,
                 disk_cache_path: str = "./memory_cache",
                 page_size_mb: int = 100):
        self.logger = get_logger(__name__)

        self.gpu_memory_limit = gpu_memory_limit
        self.cpu_memory_limit = cpu_memory_limit
        self.page_size_bytes = page_size_mb * 1024 * 1024

        self.disk_cache_path = Path(disk_cache_path)
        self.disk_cache_path.mkdir(parents=True, exist_ok=True)

        # Estado de páginas
        self.pages: Dict[str, MemoryPage] = {}
        self.stats = MemoryStats()

        # Locks para thread safety
        self.lock = threading.RLock()
        self.stats_lock = threading.RLock()

        # Tensor state manager para persistencia
        self.tensor_state_manager = get_tensor_state_manager(
            storage_path=str(self.disk_cache_path / "persistent")
        )

        # Tarea de monitoreo
        self.monitoring_task: Optional[asyncio.Task] = None
        self.monitoring_active = False

        # Configuración de dispositivos
        self.has_cuda = torch and torch.cuda.is_available()
        if self.has_cuda:
            self.gpu_count = torch.cuda.device_count()
            self.logger.info(f"CUDA disponible con {self.gpu_count} GPUs")
        else:
            self.gpu_count = 0
            self.logger.info("CUDA no disponible, usando solo CPU")

        # Actualizar estadísticas iniciales
        self._update_memory_stats()
        self.logger.info(f"MemoryManager inicializado con límites GPU:{gpu_memory_limit}, CPU:{cpu_memory_limit}")

    async def start_monitoring(self):
        """Iniciar monitoreo continuo de memoria."""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Monitoreo de memoria iniciado")

    async def stop_monitoring(self):
        """Detener monitoreo de memoria."""
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Monitoreo de memoria detenido")

    def register_tensor(self, tensor_id: str, tensor: torch.Tensor,
                       priority: PagePriority = PagePriority.MEDIUM,
                       pinned: bool = False) -> bool:
        """
        Registrar un tensor en el sistema de paginación.

        Args:
            tensor_id: ID único del tensor
            tensor: Tensor de PyTorch
            priority: Prioridad de paginación
            pinned: Si el tensor no debe ser paginado

        Returns:
            True si el registro fue exitoso
        """
        if torch is None:
            self.logger.error("PyTorch no disponible")
            return False

        try:
            with self.lock:
                if tensor_id in self.pages:
                    self.logger.warning(f"Tensor {tensor_id} ya registrado, actualizando")
                    self.unregister_tensor(tensor_id)

                # Determinar ubicación inicial
                if tensor.is_cuda:
                    location = MemoryLocation.GPU
                else:
                    location = MemoryLocation.CPU

                size_bytes = tensor.numel() * tensor.element_size()

                page = MemoryPage(
                    tensor_id=tensor_id,
                    tensor=tensor,
                    location=location,
                    size_bytes=size_bytes,
                    priority=priority,
                    pinned=pinned,
                    last_accessed=datetime.now()
                )

                self.pages[tensor_id] = page
                self._update_memory_stats()

                self.logger.info(f"Tensor '{tensor_id}' registrado ({size_bytes} bytes, {location.value})")
                return True

        except Exception as e:
            self.logger.error(f"Error registrando tensor '{tensor_id}': {e}")
            return False

    def unregister_tensor(self, tensor_id: str) -> bool:
        """Desregistrar un tensor del sistema de paginación."""
        try:
            with self.lock:
                if tensor_id not in self.pages:
                    return False

                page = self.pages[tensor_id]

                # Liberar recursos
                if page.disk_path and os.path.exists(page.disk_path):
                    os.remove(page.disk_path)

                # Liberar tensor si existe
                if page.tensor is not None:
                    del page.tensor
                    gc.collect()
                    if torch and torch.cuda.is_available():
                        torch.cuda.empty_cache()

                del self.pages[tensor_id]
                self._update_memory_stats()

                self.logger.info(f"Tensor '{tensor_id}' desregistrado")
                return True

        except Exception as e:
            self.logger.error(f"Error desregistrando tensor '{tensor_id}': {e}")
            return False

    def access_tensor(self, tensor_id: str, device: Optional[str] = None) -> Optional[torch.Tensor]:
        """
        Acceder a un tensor, moviéndolo a la ubicación deseada si es necesario.

        Args:
            tensor_id: ID del tensor
            device: Dispositivo destino ('cpu', 'cuda', 'cuda:0', etc.)

        Returns:
            Tensor en la ubicación solicitada o None si falla
        """
        try:
            with self.lock:
                if tensor_id not in self.pages:
                    self.logger.error(f"Tensor '{tensor_id}' no registrado")
                    return None

                page = self.pages[tensor_id]
                page.last_accessed = datetime.now()
                page.access_count += 1

                # Si está pinned y no en la ubicación correcta, error
                if page.pinned and device and not self._tensor_on_device(page.tensor, device):
                    self.logger.error(f"Tensor '{tensor_id}' está pinned y no puede moverse")
                    return None

                # Page in si es necesario
                if page.location == MemoryLocation.DISK:
                    if not self._page_in_tensor(tensor_id, device):
                        return None
                elif device and not self._tensor_on_device(page.tensor, device):
                    # Mover a dispositivo solicitado
                    if not self._move_tensor_to_device(page, device):
                        return None

                with self.stats_lock:
                    self.stats.page_hits += 1

                return page.tensor

        except Exception as e:
            self.logger.error(f"Error accediendo tensor '{tensor_id}': {e}")
            with self.stats_lock:
                self.stats.page_faults += 1
            return None

    def _page_in_tensor(self, tensor_id: str, target_device: Optional[str] = None) -> bool:
        """Traer un tensor desde disco a memoria."""
        try:
            page = self.pages[tensor_id]

            if not page.disk_path or not os.path.exists(page.disk_path):
                self.logger.error(f"Path de disco no válido para tensor '{tensor_id}'")
                return False

            # Cargar desde disco usando tensor state manager
            tensor = self.tensor_state_manager.deserialize_tensor(page.disk_path)

            if tensor is None:
                self.logger.error(f"Error cargando tensor '{tensor_id}' desde disco")
                return False

            # Mover a dispositivo si se especifica
            if target_device:
                tensor = tensor.to(target_device)

            page.tensor = tensor
            page.location = MemoryLocation.GPU if tensor.is_cuda else MemoryLocation.CPU
            page.disk_path = None

            self._update_memory_stats()
            self.logger.info(f"Tensor '{tensor_id}' traído desde disco")
            return True

        except Exception as e:
            self.logger.error(f"Error en page-in de tensor '{tensor_id}': {e}")
            return False

    def _move_tensor_to_device(self, page: MemoryPage, device: str) -> bool:
        """Mover un tensor a un dispositivo específico."""
        try:
            if page.tensor is None:
                return False

            page.tensor = page.tensor.to(device)
            page.location = MemoryLocation.GPU if 'cuda' in device else MemoryLocation.CPU

            self.logger.debug(f"Tensor '{page.tensor_id}' movido a {device}")
            return True

        except Exception as e:
            self.logger.error(f"Error moviendo tensor '{page.tensor_id}' a {device}: {e}")
            return False

    def _tensor_on_device(self, tensor: torch.Tensor, device: str) -> bool:
        """Verificar si un tensor está en el dispositivo especificado."""
        if tensor is None:
            return False
        return str(tensor.device) == device

    def page_out_least_recently_used(self, target_location: MemoryLocation = MemoryLocation.DISK,
                                   force: bool = False) -> int:
        """
        Paginar los tensores menos recientemente usados.

        Args:
            target_location: Ubicación destino (DISK o CPU)
            force: Forzar paginación incluso de tensores pinned

        Returns:
            Número de tensores paginados
        """
        try:
            with self.lock:
                candidates = []

                for page in self.pages.values():
                    if page.pinned and not force:
                        continue
                    if page.priority == PagePriority.CRITICAL:
                        continue
                    if page.location == target_location:
                        continue

                    candidates.append(page)

                # Ordenar por prioridad y luego por último acceso
                candidates.sort(key=lambda p: (p.priority.value, p.last_accessed))

                paged_out = 0
                for page in candidates:
                    if self._page_out_tensor(page.tensor_id, target_location):
                        paged_out += 1

                        # Verificar si hemos liberado suficiente memoria
                        self._update_memory_stats()
                        if self._memory_pressure_relieved():
                            break

                self.logger.info(f"Paginated out {paged_out} tensors to {target_location.value}")
                return paged_out

        except Exception as e:
            self.logger.error(f"Error en page-out LRU: {e}")
            return 0

    def _page_out_tensor(self, tensor_id: str, target_location: MemoryLocation) -> bool:
        """Paginar un tensor específico a la ubicación destino."""
        try:
            page = self.pages[tensor_id]

            if target_location == MemoryLocation.DISK:
                # Guardar a disco
                success = self.tensor_state_manager.serialize_tensor(
                    f"page_{tensor_id}_{int(time.time())}",
                    page.tensor,
                    use_homomorphic=False
                )
                if success:
                    page.disk_path = f"page_{tensor_id}_{int(time.time())}"
                    page.location = MemoryLocation.DISK
                    # Liberar tensor de memoria
                    del page.tensor
                    page.tensor = None
                    gc.collect()
                    if torch and torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    return True

            elif target_location == MemoryLocation.CPU and page.location == MemoryLocation.GPU:
                # Mover de GPU a CPU
                if page.tensor.is_cuda:
                    page.tensor = page.tensor.cpu()
                    page.location = MemoryLocation.CPU
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error en page-out de tensor '{tensor_id}': {e}")
            return False

    def _memory_pressure_relieved(self) -> bool:
        """Verificar si la presión de memoria se ha aliviado."""
        gpu_usage = self.stats.gpu_used / self.stats.gpu_total if self.stats.gpu_total > 0 else 0
        cpu_usage = self.stats.cpu_used / self.stats.cpu_total if self.stats.cpu_total > 0 else 0

        return gpu_usage < self.gpu_memory_limit * 0.9 and cpu_usage < self.cpu_memory_limit * 0.9

    def _update_memory_stats(self):
        """Actualizar estadísticas de memoria."""
        try:
            with self.stats_lock:
                # Memoria GPU
                if self.has_cuda:
                    self.stats.gpu_used = torch.cuda.memory_allocated()
                    self.stats.gpu_total = torch.cuda.get_device_properties(0).total_memory
                else:
                    self.stats.gpu_used = 0
                    self.stats.gpu_total = 0

                # Memoria CPU
                memory = psutil.virtual_memory()
                self.stats.cpu_used = memory.used
                self.stats.cpu_total = memory.total

                # Memoria disco (solo cache)
                try:
                    disk = psutil.disk_usage(str(self.disk_cache_path))
                    self.stats.disk_used = disk.used
                except:
                    self.stats.disk_used = 0

                # Contar páginas por ubicación
                self.stats.pages_gpu = sum(1 for p in self.pages.values() if p.location == MemoryLocation.GPU)
                self.stats.pages_cpu = sum(1 for p in self.pages.values() if p.location == MemoryLocation.CPU)
                self.stats.pages_disk = sum(1 for p in self.pages.values() if p.location == MemoryLocation.DISK)

        except Exception as e:
            self.logger.warning(f"Error actualizando estadísticas de memoria: {e}")

    def get_memory_stats(self) -> MemoryStats:
        """Obtener estadísticas actuales de memoria."""
        with self.stats_lock:
            return self.stats

    def get_page_info(self, tensor_id: str) -> Optional[MemoryPage]:
        """Obtener información de una página específica."""
        with self.lock:
            return self.pages.get(tensor_id)

    def list_pages(self) -> Dict[str, MemoryPage]:
        """Listar todas las páginas registradas."""
        with self.lock:
            return self.pages.copy()

    async def _monitoring_loop(self):
        """Loop de monitoreo continuo de memoria."""
        while self.monitoring_active:
            try:
                self._update_memory_stats()

                # Verificar presión de memoria
                gpu_usage = self.stats.gpu_used / self.stats.gpu_total if self.stats.gpu_total > 0 else 0
                cpu_usage = self.stats.cpu_used / self.stats.cpu_total if self.stats.cpu_total > 0 else 0

                if gpu_usage > self.gpu_memory_limit:
                    self.logger.warning(f"Presión de memoria GPU: {gpu_usage:.2%}")
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.page_out_least_recently_used, MemoryLocation.CPU
                    )

                if cpu_usage > self.cpu_memory_limit:
                    self.logger.warning(f"Presión de memoria CPU: {cpu_usage:.2%}")
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.page_out_least_recently_used, MemoryLocation.DISK
                    )

                # Limpiar cache periódicamente
                if len(self.pages) > 1000:  # Umbral arbitrario
                    await asyncio.get_event_loop().run_in_executor(
                        None, self._cleanup_old_pages
                    )

                await asyncio.sleep(30)  # Verificar cada 30 segundos

            except Exception as e:
                self.logger.error(f"Error en monitoring loop: {e}")
                await asyncio.sleep(10)

    def _cleanup_old_pages(self):
        """Limpiar páginas antiguas que no se usan."""
        cutoff = datetime.now() - timedelta(hours=1)
        to_remove = []

        with self.lock:
            for tensor_id, page in self.pages.items():
                if page.last_accessed < cutoff and page.priority == PagePriority.LOW:
                    to_remove.append(tensor_id)

            for tensor_id in to_remove:
                self.unregister_tensor(tensor_id)

        if to_remove:
            self.logger.info(f"Limpiadas {len(to_remove)} páginas antiguas")


# Instancia global
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager(gpu_memory_limit: float = 0.8,
                      cpu_memory_limit: float = 0.7,
                      disk_cache_path: str = "./memory_cache") -> MemoryManager:
    """Obtener instancia global del gestor de memoria."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager(gpu_memory_limit, cpu_memory_limit, disk_cache_path)
    return _memory_manager