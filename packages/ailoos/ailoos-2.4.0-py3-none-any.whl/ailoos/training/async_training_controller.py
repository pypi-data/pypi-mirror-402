"""
AsyncTrainingController - Controlador principal del entrenamiento asíncrono
Coordina el entrenamiento con capacidad de pausa/reanudación y gestión de estado.
"""

import asyncio
import logging
import time
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, Any, Optional, List, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import signal
import threading

from .training_state_manager import TrainingStateManager, TrainingStatus
from .checkpoint_manager import CheckpointManager, CheckpointConfig
from .training_progress_tracker import TrainingProgressTracker

logger = logging.getLogger(__name__)


class TrainingPhase(Enum):
    """Fases del entrenamiento."""
    INITIALIZING = "initializing"
    WARMING_UP = "warming_up"
    TRAINING = "training"
    VALIDATING = "validating"
    CHECKPOINTING = "checkpointing"
    COOLING_DOWN = "cooling_down"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AsyncTrainingConfig:
    """Configuración del controlador de entrenamiento asíncrono."""
    session_id: str
    model: torch.nn.Module
    optimizer: torch.optim.Optimizer
    criterion: torch.nn.Module
    train_dataloader: torch.utils.data.DataLoader
    val_dataloader: Optional[torch.utils.data.DataLoader] = None

    # Configuración de entrenamiento
    max_epochs: int = 100
    patience: int = 10  # Early stopping patience
    checkpoint_interval: int = 1000  # Pasos entre checkpoints
    validation_interval: int = 1  # Épocas entre validaciones
    log_interval: int = 10  # Pasos entre logs

    # Configuración de estado y checkpoints
    state_dir: str = "./training_states"
    checkpoint_dir: str = "./checkpoints"
    checkpoint_config: CheckpointConfig = field(default_factory=CheckpointConfig)

    # Configuración asíncrona
    enable_async_checkpointing: bool = True
    max_concurrent_operations: int = 3

    # Callbacks
    on_epoch_start: Optional[Callable[[int], Awaitable[None]]] = None
    on_epoch_end: Optional[Callable[[int, Dict[str, float]], Awaitable[None]]] = None
    on_batch_end: Optional[Callable[[int, int, Dict[str, float]], Awaitable[None]]] = None
    on_validation_end: Optional[Callable[[Dict[str, float]], Awaitable[None]]] = None
    on_checkpoint_saved: Optional[Callable[[str], Awaitable[None]]] = None

    # Configuración de dispositivo
    device: str = "auto"  # auto, cpu, cuda, mps

    # Configuración de recuperación
    auto_resume: bool = True
    resume_from_checkpoint: Optional[str] = None


class AsyncTrainingController:
    """
    Controlador principal del entrenamiento asíncrono.

    Características:
    - Entrenamiento asíncrono con pausa/reanudación
    - Gestión automática de estado y checkpoints
    - Monitoreo de progreso en tiempo real
    - Recuperación automática de fallos
    - Integración con callbacks personalizados
    """

    def __init__(self, config: AsyncTrainingConfig):
        self.config = config

        # Componentes principales
        self.state_manager = TrainingStateManager(config.state_dir)
        self.checkpoint_manager = CheckpointManager(config.checkpoint_dir, config.checkpoint_config)
        self.progress_tracker = TrainingProgressTracker()

        # Estado del controlador
        self.is_running = False
        self.is_paused = False
        self.should_stop = False
        self.current_phase = TrainingPhase.INITIALIZING

        # Estado del entrenamiento
        self.current_epoch = 0
        self.global_step = 0
        self.best_val_loss = float('inf')
        self.epochs_without_improvement = 0

        # Modelo y optimizador
        self.model = config.model
        self.optimizer = config.optimizer
        self.criterion = config.criterion

        # DataLoaders
        self.train_dataloader = config.train_dataloader
        self.val_dataloader = config.val_dataloader

        # Dispositivo
        self.device = self._setup_device(config.device)

        # Mover modelo al dispositivo
        self.model.to(self.device)

        # Semáforos para control de concurrencia
        self.training_semaphore = asyncio.Semaphore(1)
        self.checkpoint_semaphore = asyncio.Semaphore(config.max_concurrent_operations)

        # Tareas en background
        self.background_tasks: List[asyncio.Task] = []

        # Manejo de señales para pausa/reanudación graceful
        self._setup_signal_handlers()

        logger.info(f"🚀 AsyncTrainingController inicializado para sesión {config.session_id}")

    async def start_training(self) -> bool:
        """
        Iniciar el entrenamiento asíncrono.

        Returns:
            True si el entrenamiento se completó exitosamente
        """
        try:
            self.is_running = True
            self.current_phase = TrainingPhase.INITIALIZING

            logger.info(f"🎯 Iniciando entrenamiento asíncrono: {self.config.session_id}")

            # Inicializar componentes
            await self._initialize_training()

            # Intentar reanudar si está configurado
            if self.config.auto_resume:
                resumed = await self._try_resume_training()
                if resumed:
                    logger.info("✅ Entrenamiento reanudado desde checkpoint")
                    return await self._continue_training()

            # Iniciar entrenamiento desde cero
            return await self._start_fresh_training()

        except Exception as e:
            logger.error(f"❌ Error en entrenamiento: {e}")
            await self._handle_training_error(e)
            return False

        finally:
            self.is_running = False
            await self._cleanup()

    async def pause_training(self) -> None:
        """Pausar el entrenamiento."""
        logger.info("⏸️ Pausando entrenamiento...")
        self.is_paused = True
        self.current_phase = TrainingPhase.PAUSED

        # Esperar a que termine el batch actual
        async with self.training_semaphore:
            pass

        logger.info("✅ Entrenamiento pausado")

    async def resume_training(self) -> None:
        """Reanudar el entrenamiento."""
        if not self.is_paused:
            logger.warning("⚠️ El entrenamiento no está pausado")
            return

        logger.info("▶️ Reanudando entrenamiento...")
        self.is_paused = False
        self.current_phase = TrainingPhase.TRAINING

        logger.info("✅ Entrenamiento reanudado")

    async def stop_training(self) -> None:
        """Detener el entrenamiento completamente."""
        logger.info("🛑 Deteniendo entrenamiento...")
        self.should_stop = True
        self.is_paused = False

        # Cancelar tareas en background
        for task in self.background_tasks:
            if not task.done():
                task.cancel()

        # Esperar a que terminen
        await asyncio.gather(*self.background_tasks, return_exceptions=True)

        logger.info("✅ Entrenamiento detenido")

    async def get_training_status(self) -> Dict[str, Any]:
        """Obtener estado completo del entrenamiento."""
        return {
            'session_id': self.config.session_id,
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'current_phase': self.current_phase.value,
            'current_epoch': self.current_epoch,
            'global_step': self.global_step,
            'max_epochs': self.config.max_epochs,
            'progress': self.progress_tracker.get_progress(),
            'best_val_loss': self.best_val_loss,
            'epochs_without_improvement': self.epochs_without_improvement,
            'device': str(self.device),
            'model_info': self._get_model_info()
        }

    async def _initialize_training(self) -> None:
        """Inicializar componentes del entrenamiento."""
        # Cargar estado si existe
        await self.state_manager.load_state()

        # Crear sesión si no existe
        session = await self.state_manager.get_session(self.config.session_id)
        if not session:
            await self.state_manager.create_session(
                session_id=self.config.session_id,
                model_version="empiorio_lm_v1.0",
                training_config=self._get_training_config(),
                model_config=self._get_model_config()
            )

        # Inicializar progress tracker
        await self.progress_tracker.initialize_session(
            self.config.session_id,
            self.config.max_epochs,
            len(self.train_dataloader) if self.train_dataloader else 0
        )

    async def _try_resume_training(self) -> bool:
        """Intentar reanudar entrenamiento desde checkpoint."""
        try:
            # Buscar último checkpoint
            latest_checkpoint = await self.state_manager.get_latest_checkpoint(self.config.session_id)
            if not latest_checkpoint:
                return False

            # Cargar checkpoint
            checkpoint_data = await self.checkpoint_manager.load_checkpoint(latest_checkpoint.checkpoint_id)

            # Restaurar estado del modelo y optimizador
            self.model.load_state_dict(checkpoint_data['model_state'])
            self.optimizer.load_state_dict(checkpoint_data['optimizer_state'])

            # Restaurar estado del entrenamiento
            self.current_epoch = checkpoint_data['epoch']
            self.global_step = checkpoint_data.get('global_step', 0)
            self.best_val_loss = checkpoint_data.get('best_val_loss', float('inf'))

            # Actualizar progress tracker
            await self.progress_tracker.resume_from_checkpoint(
                self.current_epoch,
                self.global_step,
                checkpoint_data.get('metrics', {})
            )

            logger.info(f"📂 Reanudado desde checkpoint: epoch {self.current_epoch}, step {self.global_step}")
            return True

        except Exception as e:
            logger.warning(f"⚠️ No se pudo reanudar desde checkpoint: {e}")
            return False

    async def _start_fresh_training(self) -> bool:
        """Iniciar entrenamiento desde cero."""
        logger.info("🆕 Iniciando entrenamiento desde cero")

        # Fase de warmup
        self.current_phase = TrainingPhase.WARMING_UP
        await self._warmup_phase()

        # Ciclo principal de entrenamiento
        self.current_phase = TrainingPhase.TRAINING
        return await self._training_loop()

    async def _continue_training(self) -> bool:
        """Continuar entrenamiento desde el punto de reanudación."""
        logger.info("🔄 Continuando entrenamiento")

        # Ciclo principal de entrenamiento
        self.current_phase = TrainingPhase.TRAINING
        return await self._training_loop()

    async def _training_loop(self) -> bool:
        """Bucle principal del entrenamiento."""
        try:
            while self.current_epoch < self.config.max_epochs and not self.should_stop:
                # Verificar si está pausado
                if self.is_paused:
                    await asyncio.sleep(0.1)
                    continue

                # Época de entrenamiento
                epoch_start_time = time.time()
                await self._run_epoch()
                epoch_time = time.time() - epoch_start_time

                # Actualizar métricas de progreso
                await self.progress_tracker.update_epoch_progress(
                    self.current_epoch,
                    {'epoch_time': epoch_time}
                )

                # Verificar early stopping
                if self.epochs_without_improvement >= self.config.patience:
                    logger.info(f"🛑 Early stopping activado después de {self.config.patience} épocas sin mejora")
                    break

                self.current_epoch += 1

            # Entrenamiento completado
            if not self.should_stop:
                self.current_phase = TrainingPhase.COMPLETED
                await self._finalize_training()
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"❌ Error en bucle de entrenamiento: {e}")
            self.current_phase = TrainingPhase.FAILED
            return False

    async def _run_epoch(self) -> None:
        """Ejecutar una época completa de entrenamiento."""
        # Callback de inicio de época
        if self.config.on_epoch_start:
            await self.config.on_epoch_start(self.current_epoch)

        # Entrenamiento
        async with self.training_semaphore:
            train_metrics = await self._train_epoch()

        # Validación
        val_metrics = {}
        if self.val_dataloader and self.current_epoch % self.config.validation_interval == 0:
            self.current_phase = TrainingPhase.VALIDATING
            val_metrics = await self._validate_epoch()
            self.current_phase = TrainingPhase.TRAINING

            # Actualizar mejor pérdida de validación
            if val_metrics.get('val_loss', float('inf')) < self.best_val_loss:
                self.best_val_loss = val_metrics['val_loss']
                self.epochs_without_improvement = 0
            else:
                self.epochs_without_improvement += 1

        # Checkpoint periódico
        if self.global_step % self.config.checkpoint_interval == 0:
            self.current_phase = TrainingPhase.CHECKPOINTING
            await self._create_checkpoint(train_metrics, val_metrics)
            self.current_phase = TrainingPhase.TRAINING

        # Callback de fin de época
        if self.config.on_epoch_end:
            all_metrics = {**train_metrics, **val_metrics}
            await self.config.on_epoch_end(self.current_epoch, all_metrics)

    async def _train_epoch(self) -> Dict[str, float]:
        """Entrenar por una época."""
        self.model.train()
        epoch_loss = 0.0
        epoch_correct = 0
        epoch_total = 0

        for batch_idx, (inputs, targets) in enumerate(self.train_dataloader):
            # Verificar pausa
            if self.is_paused or self.should_stop:
                break

            # Mover datos al dispositivo
            inputs, targets = inputs.to(self.device), targets.to(self.device)

            # Forward pass
            self.optimizer.zero_grad()
            outputs = self.model(inputs)
            loss = self.criterion(outputs, targets)

            # Backward pass
            loss.backward()
            self.optimizer.step()

            # Estadísticas
            epoch_loss += loss.item()
            _, predicted = outputs.max(1)
            epoch_correct += predicted.eq(targets).sum().item()
            epoch_total += targets.size(0)

            self.global_step += 1

            # Logging periódico
            if batch_idx % self.config.log_interval == 0:
                current_loss = loss.item()
                current_acc = 100. * epoch_correct / epoch_total
                logger.info(f"Epoch {self.current_epoch} | Batch {batch_idx}/{len(self.train_dataloader)} | "
                          f"Loss: {current_loss:.4f} | Acc: {current_acc:.2f}%")

            # Callback de fin de batch
            if self.config.on_batch_end:
                batch_metrics = {
                    'loss': loss.item(),
                    'batch_acc': 100. * predicted.eq(targets).sum().item() / targets.size(0)
                }
                await self.config.on_batch_end(self.current_epoch, batch_idx, batch_metrics)

        # Métricas finales de la época
        avg_loss = epoch_loss / len(self.train_dataloader)
        avg_acc = 100. * epoch_correct / epoch_total

        metrics = {
            'train_loss': avg_loss,
            'train_accuracy': avg_acc,
            'epoch': self.current_epoch,
            'global_step': self.global_step
        }

        # Actualizar estado
        await self.state_manager.update_session_progress(
            session_id=self.config.session_id,
            epoch=self.current_epoch,
            batch=len(self.train_dataloader),
            loss=avg_loss,
            accuracy=avg_acc,
            learning_rate=self.optimizer.param_groups[0]['lr'],
            optimizer_state=self.optimizer.state_dict()
        )

        return metrics

    async def _validate_epoch(self) -> Dict[str, float]:
        """Validar el modelo."""
        if not self.val_dataloader:
            return {}

        self.model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0

        with torch.no_grad():
            for inputs, targets in self.val_dataloader:
                inputs, targets = inputs.to(self.device), targets.to(self.device)

                outputs = self.model(inputs)
                loss = self.criterion(outputs, targets)

                val_loss += loss.item()
                _, predicted = outputs.max(1)
                val_correct += predicted.eq(targets).sum().item()
                val_total += targets.size(0)

        avg_val_loss = val_loss / len(self.val_dataloader)
        val_acc = 100. * val_correct / val_total

        metrics = {
            'val_loss': avg_val_loss,
            'val_accuracy': val_acc
        }

        logger.info(f"📊 Validación - Loss: {avg_val_loss:.4f}, Accuracy: {val_acc:.2f}%")

        # Callback de validación
        if self.config.on_validation_end:
            await self.config.on_validation_end(metrics)

        return metrics

    async def _create_checkpoint(self, train_metrics: Dict[str, float], val_metrics: Dict[str, float]) -> None:
        """Crear un checkpoint del entrenamiento."""
        try:
            async with self.checkpoint_semaphore:
                # Combinar métricas
                all_metrics = {**train_metrics, **val_metrics}

                # Crear checkpoint
                checkpoint_id = await self.checkpoint_manager.save_checkpoint(
                    session_id=self.config.session_id,
                    model=self.model,
                    optimizer=self.optimizer,
                    epoch=self.current_epoch,
                    batch=len(self.train_dataloader),
                    global_step=self.global_step,
                    metrics=all_metrics,
                    training_config=self._get_training_config(),
                    tags=['auto']
                )

                # Callback de checkpoint guardado
                if self.config.on_checkpoint_saved:
                    await self.config.on_checkpoint_saved(checkpoint_id)

        except Exception as e:
            logger.error(f"❌ Error creando checkpoint: {e}")

    async def _warmup_phase(self) -> None:
        """Fase de warmup del entrenamiento."""
        logger.info("🔥 Ejecutando fase de warmup...")

        # Aquí se podrían hacer operaciones de warmup como:
        # - Compilación del modelo
        # - Optimizaciones iniciales
        # - Pruebas de rendimiento

        await asyncio.sleep(0.1)  # Simular warmup
        logger.info("✅ Warmup completado")

    async def _finalize_training(self) -> None:
        """Finalizar el entrenamiento."""
        logger.info("🎉 Finalizando entrenamiento...")

        # Marcar sesión como completada
        await self.state_manager.complete_session(self.config.session_id)

        # Crear checkpoint final
        await self._create_checkpoint(
            train_metrics={'final_train_loss': 0.0, 'final_train_accuracy': 0.0},
            val_metrics={'final_val_loss': self.best_val_loss, 'final_val_accuracy': 0.0}
        )

        # Fase de cooldown
        self.current_phase = TrainingPhase.COOLING_DOWN
        await self._cooldown_phase()

        logger.info("✅ Entrenamiento finalizado exitosamente")

    async def _cooldown_phase(self) -> None:
        """Fase de cooldown."""
        logger.info("❄️ Ejecutando fase de cooldown...")

        # Aquí se podrían hacer operaciones de cleanup como:
        # - Liberar memoria GPU
        # - Guardar métricas finales
        # - Generar reportes

        await asyncio.sleep(0.1)  # Simular cooldown
        logger.info("✅ Cooldown completado")

    async def _handle_training_error(self, error: Exception) -> None:
        """Manejar errores durante el entrenamiento."""
        logger.error(f"❌ Error durante el entrenamiento: {error}")

        # Marcar sesión como fallida
        await self.state_manager.fail_session(self.config.session_id, str(error))

        # Intentar crear checkpoint de recuperación
        try:
            await self._create_checkpoint(
                train_metrics={'error_train_loss': 0.0, 'error_train_accuracy': 0.0},
                val_metrics={'error_val_loss': float('inf'), 'error_val_accuracy': 0.0}
            )
        except Exception as e:
            logger.error(f"❌ Error creando checkpoint de recuperación: {e}")

    async def _cleanup(self) -> None:
        """Limpiar recursos."""
        logger.info("🧹 Limpiando recursos...")

        # Cancelar tareas pendientes
        for task in self.background_tasks:
            if not task.done():
                task.cancel()

        # Esperar a que terminen
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)

        logger.info("✅ Limpieza completada")

    def _setup_device(self, device_config: str) -> torch.device:
        """Configurar dispositivo de entrenamiento."""
        if device_config == "auto":
            if torch.cuda.is_available():
                device = torch.device("cuda")
                logger.info("🎮 Usando GPU CUDA")
            elif torch.backends.mps.is_available():
                device = torch.device("mps")
                logger.info("🍎 Usando Apple Silicon MPS")
            else:
                device = torch.device("cpu")
                logger.info("💻 Usando CPU")
        else:
            device = torch.device(device_config)
            logger.info(f"🔧 Usando dispositivo configurado: {device_config}")

        return device

    def _setup_signal_handlers(self) -> None:
        """Configurar manejadores de señales para pausa/reanudación."""
        try:
            # Signal para pausa (SIGUSR1)
            signal.signal(signal.SIGUSR1, self._signal_pause_handler)
            # Signal para reanudación (SIGUSR2)
            signal.signal(signal.SIGUSR2, self._signal_resume_handler)
            # Signal para parada graceful (SIGTERM)
            signal.signal(signal.SIGTERM, self._signal_stop_handler)
        except ValueError:
            # En algunos entornos (como Jupyter), las señales no están disponibles
            logger.warning("⚠️ No se pudieron configurar manejadores de señales")

    def _signal_pause_handler(self, signum, frame) -> None:
        """Manejador de señal para pausa."""
        logger.info("📡 Señal de pausa recibida")
        asyncio.create_task(self.pause_training())

    def _signal_resume_handler(self, signum, frame) -> None:
        """Manejador de señal para reanudación."""
        logger.info("📡 Señal de reanudación recibida")
        asyncio.create_task(self.resume_training())

    def _signal_stop_handler(self, signum, frame) -> None:
        """Manejador de señal para parada."""
        logger.info("📡 Señal de parada recibida")
        asyncio.create_task(self.stop_training())

    def _get_training_config(self) -> Dict[str, Any]:
        """Obtener configuración del entrenamiento."""
        return {
            'max_epochs': self.config.max_epochs,
            'patience': self.config.patience,
            'checkpoint_interval': self.config.checkpoint_interval,
            'validation_interval': self.config.validation_interval,
            'batch_size': self.train_dataloader.batch_size if self.train_dataloader else None,
            'device': str(self.device)
        }

    def _get_model_config(self) -> Dict[str, Any]:
        """Obtener configuración del modelo."""
        return {
            'model_type': type(self.model).__name__,
            'num_parameters': sum(p.numel() for p in self.model.parameters()),
            'trainable_parameters': sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        }

    def _get_model_info(self) -> Dict[str, Any]:
        """Obtener información del modelo."""
        return {
            'type': type(self.model).__name__,
            'parameters': sum(p.numel() for p in self.model.parameters()),
            'trainable_parameters': sum(p.numel() for p in self.model.parameters() if p.requires_grad),
            'device': str(next(self.model.parameters()).device)
        }