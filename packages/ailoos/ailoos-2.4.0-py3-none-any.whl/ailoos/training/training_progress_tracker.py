"""
TrainingProgressTracker - Seguimiento del progreso y estadísticas del entrenamiento
Monitorea métricas, rendimiento y progreso en tiempo real.
"""

import asyncio
import logging
import time
import threading
from typing import Dict, Any, Optional, List, Callable, Awaitable
from dataclasses import dataclass, field
from collections import deque
import statistics
import psutil
try:
    import GPUtil
    GPU_UTIL_AVAILABLE = True
except ImportError:
    GPU_UTIL_AVAILABLE = False
    GPUtil = None
from datetime import datetime, timedelta

from .metrics import MetricsEvaluator, MetricsConfig, create_default_metrics_config

logger = logging.getLogger(__name__)


@dataclass
class ProgressMetrics:
    """Métricas de progreso del entrenamiento."""
    session_id: str
    current_epoch: int = 0
    total_epochs: int = 0
    current_batch: int = 0
    total_batches_per_epoch: int = 0
    global_step: int = 0

    # Métricas de rendimiento
    epoch_time: float = 0.0
    batch_time: float = 0.0
    loss: float = 0.0
    accuracy: float = 0.0
    learning_rate: float = 0.0

    # Estadísticas históricas
    loss_history: List[float] = field(default_factory=list)
    accuracy_history: List[float] = field(default_factory=list)
    learning_rate_history: List[float] = field(default_factory=list)

    # Métricas de sistema
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    gpu_usage: Optional[float] = None
    gpu_memory: Optional[float] = None

    # Estimaciones
    eta_seconds: float = 0.0
    progress_percentage: float = 0.0

    # Timestamps
    start_time: float = 0.0
    last_update: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            'session_id': self.session_id,
            'current_epoch': self.current_epoch,
            'total_epochs': self.total_epochs,
            'current_batch': self.current_batch,
            'total_batches_per_epoch': self.total_batches_per_epoch,
            'global_step': self.global_step,
            'epoch_time': self.epoch_time,
            'batch_time': self.batch_time,
            'loss': self.loss,
            'accuracy': self.accuracy,
            'learning_rate': self.learning_rate,
            'loss_history': list(self.loss_history),
            'accuracy_history': list(self.accuracy_history),
            'learning_rate_history': list(self.learning_rate_history),
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'gpu_usage': self.gpu_usage,
            'gpu_memory': self.gpu_memory,
            'eta_seconds': self.eta_seconds,
            'progress_percentage': self.progress_percentage,
            'start_time': self.start_time,
            'last_update': self.last_update
        }


@dataclass
class TrainingStats:
    """Estadísticas completas del entrenamiento."""
    total_training_time: float = 0.0
    total_epochs_completed: int = 0
    total_batches_processed: int = 0
    average_epoch_time: float = 0.0
    average_batch_time: float = 0.0
    best_loss: float = float('inf')
    best_accuracy: float = 0.0
    final_loss: float = 0.0
    final_accuracy: float = 0.0
    loss_improvement_rate: float = 0.0
    accuracy_improvement_rate: float = 0.0
    convergence_epoch: Optional[int] = None
    early_stopping_triggered: bool = False

    # Métricas de sistema promedio
    avg_cpu_usage: float = 0.0
    avg_memory_usage: float = 0.0
    avg_gpu_usage: Optional[float] = None
    peak_memory_usage: float = 0.0

    # Eficiencia
    throughput_samples_per_second: float = 0.0
    throughput_tokens_per_second: float = 0.0


class TrainingProgressTracker:
    """
    Rastreador de progreso del entrenamiento.

    Características:
    - Monitoreo en tiempo real de métricas
    - Estimación de tiempo restante (ETA)
    - Estadísticas de rendimiento del sistema
    - Historial de métricas
    - Detección de convergencia
    - Callbacks personalizados
    """

    def __init__(self, history_size: int = 1000, update_interval: float = 1.0):
        self.history_size = history_size
        self.update_interval = update_interval

        # Estado del tracker
        self.metrics: Optional[ProgressMetrics] = None
        self.stats = TrainingStats()

        # Buffers circulares para métricas recientes
        self.recent_batch_times: deque = deque(maxlen=100)
        self.recent_losses: deque = deque(maxlen=100)
        self.recent_accuracies: deque = deque(maxlen=100)

        # Callbacks
        self.on_progress_update: Optional[Callable[[ProgressMetrics], Awaitable[None]]] = None
        self.on_epoch_complete: Optional[Callable[[int, Dict[str, Any]], Awaitable[None]]] = None
        self.on_milestone_reached: Optional[Callable[[str, Any], Awaitable[None]]] = None

        # Hilo de monitoreo del sistema
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_active = False
        self.system_metrics_lock = threading.Lock()
        self.last_system_update = 0.0

        # Control de concurrencia
        self._lock = asyncio.Lock()

        logger.info("🚀 TrainingProgressTracker inicializado")

    async def initialize_session(
        self,
        session_id: str,
        total_epochs: int,
        batches_per_epoch: int
    ) -> None:
        """Inicializar una nueva sesión de entrenamiento."""
        async with self._lock:
            self.metrics = ProgressMetrics(
                session_id=session_id,
                total_epochs=total_epochs,
                total_batches_per_epoch=batches_per_epoch,
                start_time=time.time(),
                last_update=time.time()
            )

            # Reiniciar estadísticas
            self.stats = TrainingStats()

            # Limpiar buffers
            self.recent_batch_times.clear()
            self.recent_losses.clear()
            self.recent_accuracies.clear()

            # Iniciar monitoreo del sistema
            self._start_system_monitoring()

            logger.info(f"📊 Sesión {session_id} inicializada: {total_epochs} épocas, {batches_per_epoch} batches/época")

    async def resume_from_checkpoint(
        self,
        current_epoch: int,
        global_step: int,
        checkpoint_metrics: Dict[str, Any]
    ) -> None:
        """Reanudar desde un checkpoint."""
        async with self._lock:
            if not self.metrics:
                raise ValueError("Sesión no inicializada")

            self.metrics.current_epoch = current_epoch
            self.metrics.global_step = global_step
            self.metrics.last_update = time.time()

            # Restaurar historial si está disponible
            if 'loss_history' in checkpoint_metrics:
                self.metrics.loss_history = checkpoint_metrics['loss_history'][-self.history_size:]
            if 'accuracy_history' in checkpoint_metrics:
                self.metrics.accuracy_history = checkpoint_metrics['accuracy_history'][-self.history_size:]

            logger.info(f"📂 Progreso reanudado: epoch {current_epoch}, step {global_step}")

    async def update_batch_progress(
        self,
        batch_idx: int,
        batch_time: float,
        loss: float,
        accuracy: float,
        learning_rate: float
    ) -> None:
        """Actualizar progreso de un batch."""
        async with self._lock:
            if not self.metrics:
                return

            # Actualizar métricas
            self.metrics.current_batch = batch_idx
            self.metrics.global_step += 1
            self.metrics.batch_time = batch_time
            self.metrics.loss = loss
            self.metrics.accuracy = accuracy
            self.metrics.learning_rate = learning_rate
            self.metrics.last_update = time.time()

            # Actualizar historial
            self.metrics.loss_history.append(loss)
            self.metrics.accuracy_history.append(accuracy)
            self.metrics.learning_rate_history.append(learning_rate)

            # Mantener tamaño del historial
            if len(self.metrics.loss_history) > self.history_size:
                self.metrics.loss_history = self.metrics.loss_history[-self.history_size:]
                self.metrics.accuracy_history = self.metrics.accuracy_history[-self.history_size:]
                self.metrics.learning_rate_history = self.metrics.learning_rate_history[-self.history_size:]

            # Actualizar buffers recientes
            self.recent_batch_times.append(batch_time)
            self.recent_losses.append(loss)
            self.recent_accuracies.append(accuracy)

            # Calcular progreso y ETA
            self._calculate_progress_and_eta()

            # Actualizar métricas de sistema (cada cierto intervalo)
            if time.time() - self.last_system_update >= self.update_interval:
                await self._update_system_metrics()

            # Callback de progreso
            if self.on_progress_update:
                await self.on_progress_update(self.metrics)

    async def update_epoch_progress(self, epoch: int, epoch_metrics: Dict[str, Any]) -> None:
        """Actualizar progreso de una época."""
        async with self._lock:
            if not self.metrics:
                return

            self.metrics.current_epoch = epoch
            self.metrics.epoch_time = epoch_metrics.get('epoch_time', 0.0)
            self.metrics.last_update = time.time()

            # Actualizar estadísticas globales
            self.stats.total_epochs_completed = epoch + 1
            self.stats.total_training_time = time.time() - self.metrics.start_time

            # Calcular promedios
            if self.metrics.loss_history:
                self.stats.final_loss = self.metrics.loss_history[-1]
                self.stats.best_loss = min(self.metrics.loss_history)

            if self.metrics.accuracy_history:
                self.stats.final_accuracy = self.metrics.accuracy_history[-1]
                self.stats.best_accuracy = max(self.metrics.accuracy_history)

            # Calcular métricas de eficiencia
            self._calculate_efficiency_metrics()

            # Detectar milestones
            await self._check_milestones()

            # Callback de época completada
            if self.on_epoch_complete:
                await self.on_epoch_complete(epoch, epoch_metrics)

    async def get_progress(self) -> ProgressMetrics:
        """Obtener métricas de progreso actuales."""
        async with self._lock:
            return self.metrics.copy() if self.metrics else None

    async def get_stats(self) -> TrainingStats:
        """Obtener estadísticas completas del entrenamiento."""
        async with self._lock:
            return self.stats

    async def get_recent_metrics(self, window_size: int = 50) -> Dict[str, List[float]]:
        """Obtener métricas recientes en una ventana deslizante."""
        async with self._lock:
            if not self.metrics:
                return {}

            return {
                'loss': list(self.metrics.loss_history[-window_size:]),
                'accuracy': list(self.metrics.accuracy_history[-window_size:]),
                'learning_rate': list(self.metrics.learning_rate_history[-window_size:]),
                'batch_times': list(self.recent_batch_times)[-window_size:],
                'recent_losses': list(self.recent_losses),
                'recent_accuracies': list(self.recent_accuracies)
            }

    async def finalize_training(self) -> None:
        """Finalizar el entrenamiento y calcular estadísticas finales."""
        async with self._lock:
            if not self.metrics:
                return

            # Detener monitoreo del sistema
            self._stop_system_monitoring()

            # Calcular estadísticas finales
            total_time = time.time() - self.metrics.start_time
            self.stats.total_training_time = total_time

            if self.metrics.loss_history:
                self.stats.final_loss = self.metrics.loss_history[-1]
                self.stats.best_loss = min(self.metrics.loss_history)

            if self.metrics.accuracy_history:
                self.stats.final_accuracy = self.metrics.accuracy_history[-1]
                self.stats.best_accuracy = max(self.metrics.accuracy_history)

            # Calcular tasas de mejora
            self._calculate_improvement_rates()

            # Calcular eficiencia final
            self._calculate_efficiency_metrics()

            logger.info("📊 Entrenamiento finalizado - Estadísticas calculadas")

    def _calculate_progress_and_eta(self) -> None:
        """Calcular progreso porcentual y tiempo estimado restante."""
        if not self.metrics:
            return

        # Calcular progreso total
        total_batches = self.metrics.total_epochs * self.metrics.total_batches_per_epoch
        completed_batches = (self.metrics.current_epoch * self.metrics.total_batches_per_epoch) + self.metrics.current_batch

        if total_batches > 0:
            self.metrics.progress_percentage = (completed_batches / total_batches) * 100.0

            # Calcular ETA
            elapsed_time = time.time() - self.metrics.start_time
            if completed_batches > 0:
                avg_time_per_batch = elapsed_time / completed_batches
                remaining_batches = total_batches - completed_batches
                self.metrics.eta_seconds = avg_time_per_batch * remaining_batches

    def _calculate_improvement_rates(self) -> None:
        """Calcular tasas de mejora de loss y accuracy."""
        if not self.metrics:
            return

        loss_history = self.metrics.loss_history
        acc_history = self.metrics.accuracy_history

        if len(loss_history) > 10:
            # Calcular mejora en loss (debería disminuir)
            early_loss = statistics.mean(loss_history[:10])
            late_loss = statistics.mean(loss_history[-10:])
            if early_loss > 0:
                self.stats.loss_improvement_rate = (early_loss - late_loss) / early_loss

        if len(acc_history) > 10:
            # Calcular mejora en accuracy (debería aumentar)
            early_acc = statistics.mean(acc_history[:10])
            late_acc = statistics.mean(acc_history[-10:])
            self.stats.accuracy_improvement_rate = (late_acc - early_acc) / max(early_acc, 1e-6)

    def _calculate_efficiency_metrics(self) -> None:
        """Calcular métricas de eficiencia."""
        if not self.metrics:
            return

        total_time = time.time() - self.metrics.start_time
        total_batches = self.stats.total_batches_processed

        if total_time > 0 and total_batches > 0:
            self.stats.average_batch_time = total_time / total_batches
            self.stats.throughput_samples_per_second = total_batches / total_time

            # Estimar tokens por segundo (asumiendo secuencia típica)
            avg_sequence_length = 512  # Asumir secuencia típica
            self.stats.throughput_tokens_per_second = self.stats.throughput_samples_per_second * avg_sequence_length

        # Calcular promedios de época
        if self.stats.total_epochs_completed > 0:
            self.stats.average_epoch_time = total_time / self.stats.total_epochs_completed

    async def _check_milestones(self) -> None:
        """Verificar si se alcanzaron milestones importantes."""
        if not self.metrics or not self.on_milestone_reached:
            return

        # Milestone: primera época completada
        if self.metrics.current_epoch == 1:
            await self.on_milestone_reached("first_epoch_completed", {
                'epoch': 1,
                'time': time.time() - self.metrics.start_time
            })

        # Milestone: 25% completado
        if self.metrics.progress_percentage >= 25 and self.metrics.progress_percentage < 26:
            await self.on_milestone_reached("quarter_completed", {
                'progress': self.metrics.progress_percentage,
                'eta': self.metrics.eta_seconds
            })

        # Milestone: 50% completado
        if self.metrics.progress_percentage >= 50 and self.metrics.progress_percentage < 51:
            await self.on_milestone_reached("half_completed", {
                'progress': self.metrics.progress_percentage,
                'eta': self.metrics.eta_seconds
            })

        # Milestone: 75% completado
        if self.metrics.progress_percentage >= 75 and self.metrics.progress_percentage < 76:
            await self.on_milestone_reached("three_quarters_completed", {
                'progress': self.metrics.progress_percentage,
                'eta': self.metrics.eta_seconds
            })

        # Milestone: mejor accuracy alcanzado
        if (self.metrics.accuracy_history and
            len(self.metrics.accuracy_history) > 1 and
            self.metrics.accuracy_history[-1] == max(self.metrics.accuracy_history)):
            await self.on_milestone_reached("best_accuracy_achieved", {
                'accuracy': self.metrics.accuracy_history[-1],
                'epoch': self.metrics.current_epoch
            })

    def _start_system_monitoring(self) -> None:
        """Iniciar monitoreo de métricas del sistema."""
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._system_monitoring_loop, daemon=True)
        self.monitoring_thread.start()

    def _stop_system_monitoring(self) -> None:
        """Detener monitoreo del sistema."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1.0)

    def _system_monitoring_loop(self) -> None:
        """Bucle de monitoreo del sistema."""
        while self.monitoring_active:
            try:
                with self.system_metrics_lock:
                    # CPU
                    self.metrics.cpu_usage = psutil.cpu_percent(interval=None)

                    # Memoria
                    memory = psutil.virtual_memory()
                    self.metrics.memory_usage = memory.percent

                    # GPU (si disponible)
                    if GPU_UTIL_AVAILABLE:
                        try:
                            gpus = GPUtil.getGPUs()
                            if gpus:
                                gpu = gpus[0]  # Primera GPU
                                self.metrics.gpu_usage = gpu.load * 100
                                self.metrics.gpu_memory = gpu.memoryUsed / gpu.memoryTotal * 100
                        except:
                            pass

                self.last_system_update = time.time()
                time.sleep(self.update_interval)

            except Exception as e:
                logger.warning(f"Error en monitoreo del sistema: {e}")
                time.sleep(1.0)

    async def _update_system_metrics(self) -> None:
        """Actualizar métricas del sistema en el objeto metrics."""
        with self.system_metrics_lock:
            # Las métricas ya están actualizadas por el hilo de monitoreo
            pass

    def get_formatted_eta(self) -> str:
        """Obtener ETA formateado como string."""
        if not self.metrics or self.metrics.eta_seconds <= 0:
            return "N/A"

        eta_td = timedelta(seconds=int(self.metrics.eta_seconds))
        return str(eta_td)

    def get_formatted_progress(self) -> str:
        """Obtener progreso formateado como string."""
        if not self.metrics:
            return "No inicializado"

        return (f"Época {self.metrics.current_epoch}/{self.metrics.total_epochs} | "
                f"Batch {self.metrics.current_batch}/{self.metrics.total_batches_per_epoch} | "
                f"Progreso: {self.metrics.progress_percentage:.1f}% | "
                f"ETA: {self.get_formatted_eta()}")

    async def export_metrics_history(self, filepath: str) -> None:
        """Exportar historial completo de métricas a archivo."""
        async with self._lock:
            if not self.metrics:
                return

            data = {
                'session_id': self.metrics.session_id,
                'exported_at': time.time(),
                'metrics_history': self.metrics.to_dict(),
                'training_stats': {
                    'total_training_time': self.stats.total_training_time,
                    'total_epochs_completed': self.stats.total_epochs_completed,
                    'best_loss': self.stats.best_loss,
                    'best_accuracy': self.stats.best_accuracy,
                    'final_loss': self.stats.final_loss,
                    'final_accuracy': self.stats.final_accuracy,
                    'loss_improvement_rate': self.stats.loss_improvement_rate,
                    'accuracy_improvement_rate': self.stats.accuracy_improvement_rate,
                    'throughput_samples_per_second': self.stats.throughput_samples_per_second,
                    'throughput_tokens_per_second': self.stats.throughput_tokens_per_second
                }
            }

            # Guardar como JSON
            import json
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)

            logger.info(f"📊 Historial de métricas exportado a {filepath}")