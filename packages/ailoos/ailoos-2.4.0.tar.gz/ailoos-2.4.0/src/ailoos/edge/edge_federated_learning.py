"""
Federated Learning para dispositivos edge.

Permite participación en FL desde dispositivos con recursos limitados,
con optimización de recursos, privacidad y funcionamiento offline.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import logging
import time
import threading
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import hashlib

logger = logging.getLogger(__name__)


class EdgeFLState(Enum):
    """Estados del FL en edge."""
    IDLE = "idle"
    WAITING_FOR_ROUND = "waiting_for_round"
    TRAINING = "training"
    AGGREGATING = "aggregating"
    SYNCING = "syncing"
    OFFLINE = "offline"


class EdgeFLParticipation(Enum):
    """Niveles de participación en FL."""
    FULL = "full"  # Participación completa
    PARTIAL = "partial"  # Solo algunas rondas
    CONDITIONAL = "conditional"  # Solo bajo ciertas condiciones
    PASSIVE = "passive"  # Solo recibir actualizaciones


@dataclass
class EdgeFLConfig:
    """Configuración de FL para edge."""
    # Participación
    participation_level: EdgeFLParticipation = EdgeFLParticipation.CONDITIONAL
    max_training_rounds_per_day: int = 5
    min_battery_level_for_training: float = 20.0

    # Entrenamiento
    local_epochs: int = 3
    batch_size: int = 16
    learning_rate: float = 0.001
    max_training_time_seconds: int = 300

    # Recursos
    max_cpu_usage_percent: float = 70.0
    max_memory_usage_mb: int = 256
    enable_adaptive_training: bool = True

    # Privacidad
    enable_differential_privacy: bool = True
    noise_multiplier: float = 0.1
    max_grad_norm: float = 1.0

    # Sincronización
    sync_interval_seconds: int = 1800  # 30 minutos
    enable_offline_training: bool = True
    max_offline_rounds: int = 10

    # Monitoreo
    enable_training_metrics: bool = True
    metrics_report_interval: int = 60


@dataclass
class EdgeFLRound:
    """Ronda de FL en edge."""
    round_id: str
    global_model_version: str
    start_time: float
    deadline: Optional[float] = None
    status: str = "pending"
    local_model_path: Optional[str] = None
    training_metrics: Dict[str, Any] = field(default_factory=dict)
    participation_decision: Optional[bool] = None


@dataclass
class EdgeFLMetrics:
    """Métricas de FL en edge."""
    rounds_participated: int = 0
    rounds_completed: int = 0
    total_training_time_seconds: float = 0.0
    avg_training_accuracy: float = 0.0
    total_data_samples: int = 0
    last_round_timestamp: float = 0.0
    offline_rounds_stored: int = 0
    sync_success_rate: float = 0.0


class EdgeFederatedLearning:
    """
    Sistema de Federated Learning optimizado para dispositivos edge.

    Características principales:
    - Participación inteligente en rondas FL basada en recursos
    - Entrenamiento local optimizado para dispositivos limitados
    - Funcionamiento offline con sincronización diferida
    - Privacidad diferencial integrada
    - Gestión automática de recursos
    - Integración con componentes edge
    """

    def __init__(
        self,
        device_id: str,
        config: EdgeFLConfig,
        resource_manager: Optional[Any] = None,  # ResourceManager
        offline_capabilities: Optional[Any] = None,  # OfflineCapabilities
        edge_sync: Optional[Any] = None  # EdgeSynchronization
    ):
        self.device_id = device_id
        self.config = config

        # Componentes integrados
        self.resource_manager = resource_manager
        self.offline_capabilities = offline_capabilities
        self.edge_sync = edge_sync

        # Estado del sistema
        self.current_state = EdgeFLState.IDLE
        self.current_round: Optional[EdgeFLRound] = None

        # Modelos
        self.global_model: Optional[nn.Module] = None
        self.local_model: Optional[nn.Module] = None
        self.model_optimizer: Optional[optim.Optimizer] = None

        # Datos locales
        self.local_data_loader: Optional[Any] = None
        self.local_dataset_size: int = 0

        # Rondas y métricas
        self.rounds_history: Dict[str, EdgeFLRound] = {}
        self.metrics = EdgeFLMetrics()

        # Hilos
        self.training_thread: Optional[threading.Thread] = None
        self.monitor_thread: Optional[threading.Thread] = None

        # Callbacks
        self.round_callbacks: List[Callable] = []
        self.training_callbacks: List[Callable] = []

        logger.info("🔧 EdgeFederatedLearning inicializado")
        logger.info(f"   Device ID: {device_id}")
        logger.info(f"   Nivel de participación: {config.participation_level.value}")

    def start(self):
        """Iniciar FL en edge."""
        if self.monitor_thread and self.monitor_thread.is_alive():
            logger.warning("⚠️ EdgeFederatedLearning ya está ejecutándose")
            return

        # Iniciar hilo de monitoreo
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

        self.current_state = EdgeFLState.WAITING_FOR_ROUND
        logger.info("🚀 EdgeFederatedLearning iniciado")

    def stop(self):
        """Detener FL en edge."""
        self.current_state = EdgeFLState.IDLE

        # Esperar a que termine el entrenamiento
        if self.training_thread and self.training_thread.is_alive():
            self.training_thread.join(timeout=30.0)

        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)

        logger.info("🛑 EdgeFederatedLearning detenido")

    def set_global_model(self, model: nn.Module, model_version: str):
        """
        Establecer modelo global para la ronda actual.

        Args:
            model: Modelo global
            model_version: Versión del modelo
        """
        self.global_model = model
        self.local_model = self._copy_model(model)

        # Inicializar optimizer
        self.model_optimizer = optim.Adam(
            self.local_model.parameters(),
            lr=self.config.learning_rate
        )

        logger.info(f"📥 Modelo global establecido: {model_version}")

    def set_local_data(self, data_loader: Any, dataset_size: int):
        """
        Establecer datos locales para entrenamiento.

        Args:
            data_loader: DataLoader local
            dataset_size: Tamaño del dataset
        """
        self.local_data_loader = data_loader
        self.local_dataset_size = dataset_size
        self.metrics.total_data_samples = dataset_size

        logger.info(f"📊 Datos locales configurados: {dataset_size} muestras")

    def start_round(self, round_id: str, deadline: Optional[float] = None) -> bool:
        """
        Iniciar nueva ronda de FL.

        Args:
            round_id: ID de la ronda
            deadline: Deadline opcional

        Returns:
            True si se acepta la ronda
        """
        if self.current_state == EdgeFLState.TRAINING:
            logger.warning("⚠️ Ya hay una ronda en entrenamiento")
            return False

        # Verificar condiciones para participar
        if not self._should_participate_in_round():
            logger.info(f"⏭️ Saltando ronda {round_id} (condiciones no cumplidas)")
            return False

        # Crear ronda
        round_obj = EdgeFLRound(
            round_id=round_id,
            global_model_version=getattr(self.global_model, '_version', 'unknown'),
            start_time=time.time(),
            deadline=deadline
        )

        self.current_round = round_obj
        self.rounds_history[round_id] = round_obj
        self.current_state = EdgeFLState.TRAINING

        # Iniciar entrenamiento
        self.training_thread = threading.Thread(target=self._train_local_model, daemon=True)
        self.training_thread.start()

        logger.info(f"🎯 Ronda {round_id} iniciada")
        return True

    def _should_participate_in_round(self) -> bool:
        """Determinar si participar en la ronda actual."""
        # Verificar nivel de participación
        if self.config.participation_level == EdgeFLParticipation.PASSIVE:
            return False

        # Verificar recursos disponibles
        if self.resource_manager:
            status = self.resource_manager.get_resource_status()
            cpu_usage = status['current_usage']['cpu_percent']
            memory_usage = status['current_usage']['memory_percent']

            if cpu_usage > self.config.max_cpu_usage_percent:
                logger.debug("⏭️ CPU demasiado utilizado")
                return False

            if memory_usage > (self.config.max_memory_usage_mb / status['current_usage']['memory_used_mb']) * 100:
                logger.debug("⏭️ Memoria insuficiente")
                return False

        # Verificar batería (si disponible)
        if self.resource_manager:
            battery = self.resource_manager.monitor.get_current_usage().battery_percent
            if battery is not None and battery < self.config.min_battery_level_for_training:
                logger.debug("⏭️ Batería baja")
                return False

        # Verificar límite diario de rondas
        today_rounds = sum(1 for r in self.rounds_history.values()
                          if time.time() - r.start_time < 86400)  # 24 horas

        if today_rounds >= self.config.max_training_rounds_per_day:
            logger.debug("⏭️ Límite diario de rondas alcanzado")
            return False

        # Verificar datos locales
        if not self.local_data_loader or self.local_dataset_size == 0:
            logger.debug("⏭️ No hay datos locales disponibles")
            return False

        return True

    def _train_local_model(self):
        """Entrenar modelo local."""
        try:
            if not self.local_model or not self.local_data_loader:
                logger.error("❌ Modelo o datos locales no disponibles")
                return

            logger.info("🏋️ Iniciando entrenamiento local...")

            start_time = time.time()
            epoch_losses = []
            epoch_accuracies = []

            # Entrenamiento por épocas
            for epoch in range(self.config.local_epochs):
                epoch_loss = 0.0
                epoch_correct = 0
                epoch_total = 0

                # Verificar límites de tiempo
                if time.time() - start_time > self.config.max_training_time_seconds:
                    logger.warning("⏰ Límite de tiempo de entrenamiento alcanzado")
                    break

                # Entrenar con batches
                batch_count = 0
                for batch_data in self._get_training_batches():
                    loss, correct, total = self._train_on_batch(batch_data)

                    epoch_loss += loss
                    epoch_correct += correct
                    epoch_total += total
                    batch_count += 1

                    # Verificar límites de recursos durante entrenamiento
                    if self._should_pause_training():
                        logger.info("⏸️ Entrenamiento pausado por recursos")
                        time.sleep(5)  # Pausa breve

                # Calcular métricas de época
                avg_loss = epoch_loss / batch_count if batch_count > 0 else 0
                accuracy = epoch_correct / epoch_total if epoch_total > 0 else 0

                epoch_losses.append(avg_loss)
                epoch_accuracies.append(accuracy)

                logger.debug(f"   Época {epoch + 1}: loss={avg_loss:.4f}, acc={accuracy:.4f}")

            # Finalizar entrenamiento
            training_time = time.time() - start_time

            # Aplicar privacidad diferencial si está habilitado
            if self.config.enable_differential_privacy:
                self._apply_differential_privacy()

            # Calcular métricas finales
            final_metrics = {
                "training_time_seconds": training_time,
                "epochs_completed": len(epoch_losses),
                "final_loss": epoch_losses[-1] if epoch_losses else 0,
                "final_accuracy": epoch_accuracies[-1] if epoch_accuracies else 0,
                "avg_loss": np.mean(epoch_losses) if epoch_losses else 0,
                "avg_accuracy": np.mean(epoch_accuracies) if epoch_accuracies else 0,
                "total_batches": batch_count
            }

            # Actualizar ronda actual
            if self.current_round:
                self.current_round.status = "completed"
                self.current_round.training_metrics = final_metrics

                # Calcular deltas del modelo
                model_updates = self._calculate_model_updates()

                # Sincronizar actualizaciones
                self._sync_model_updates(model_updates, final_metrics)

            # Actualizar métricas globales
            self._update_global_metrics(final_metrics, training_time)

            self.current_state = EdgeFLState.WAITING_FOR_ROUND
            logger.info(f"✅ Entrenamiento local completado en {training_time:.2f}s")

        except Exception as e:
            logger.error(f"❌ Error en entrenamiento local: {e}")
            if self.current_round:
                self.current_round.status = "failed"
            self.current_state = EdgeFLState.WAITING_FOR_ROUND

    def _get_training_batches(self):
        """Obtener batches de entrenamiento."""
        # Simular batches de datos locales
        for i in range(min(100, self.local_dataset_size // self.config.batch_size)):
            # Simular datos de entrenamiento
            batch_size = min(self.config.batch_size, self.local_dataset_size - i * self.config.batch_size)

            if hasattr(self.local_model, 'input_features'):
                input_size = self.local_model.input_features
            else:
                input_size = 784  # Default para MNIST-like

            inputs = torch.randn(batch_size, input_size)
            targets = torch.randint(0, 10, (batch_size,))

            yield {"inputs": inputs, "targets": targets}

    def _train_on_batch(self, batch_data: Dict[str, torch.Tensor]) -> Tuple[float, int, int]:
        """Entrenar en un batch."""
        try:
            inputs = batch_data["inputs"]
            targets = batch_data["targets"]

            # Forward pass
            outputs = self.local_model(inputs)
            loss = nn.functional.cross_entropy(outputs, targets)

            # Backward pass
            self.model_optimizer.zero_grad()
            loss.backward()

            # Clip gradients si DP está habilitado
            if self.config.enable_differential_privacy:
                torch.nn.utils.clip_grad_norm_(
                    self.local_model.parameters(),
                    max_norm=self.config.max_grad_norm
                )

            self.model_optimizer.step()

            # Calcular accuracy
            _, predicted = torch.max(outputs.data, 1)
            correct = (predicted == targets).sum().item()
            total = targets.size(0)

            return loss.item(), correct, total

        except Exception as e:
            logger.error(f"❌ Error entrenando batch: {e}")
            return 0.0, 0, 0

    def _should_pause_training(self) -> bool:
        """Determinar si pausar entrenamiento por recursos."""
        if not self.resource_manager:
            return False

        status = self.resource_manager.get_resource_status()
        cpu_usage = status['current_usage']['cpu_percent']
        memory_usage = status['current_usage']['memory_percent']

        return (cpu_usage > self.config.max_cpu_usage_percent or
                memory_usage > (self.config.max_memory_usage_mb / status['current_usage']['memory_used_mb']) * 100)

    def _apply_differential_privacy(self):
        """Aplicar privacidad diferencial a los gradients."""
        try:
            for param in self.local_model.parameters():
                if param.grad is not None:
                    # Agregar ruido gaussiano
                    noise = torch.normal(0, self.config.noise_multiplier, param.grad.shape)
                    param.grad.data.add_(noise)
        except Exception as e:
            logger.warning(f"⚠️ Error aplicando DP: {e}")

    def _calculate_model_updates(self) -> Dict[str, Any]:
        """Calcular actualizaciones del modelo."""
        try:
            updates = {}

            if self.global_model and self.local_model:
                for (global_name, global_param), (local_name, local_param) in zip(
                    self.global_model.named_parameters(),
                    self.local_model.named_parameters()
                ):
                    if global_name == local_name:
                        # Calcular delta
                        delta = local_param.data - global_param.data
                        updates[global_name] = delta.cpu().numpy()

            return {
                "round_id": self.current_round.round_id if self.current_round else "unknown",
                "model_updates": updates,
                "num_parameters": len(updates),
                "update_timestamp": time.time()
            }

        except Exception as e:
            logger.error(f"❌ Error calculando updates: {e}")
            return {}

    def _sync_model_updates(self, updates: Dict[str, Any], metrics: Dict[str, Any]):
        """Sincronizar actualizaciones del modelo."""
        try:
            # Usar EdgeSynchronization si está disponible
            if self.edge_sync:
                task_id = self.edge_sync.sync_federated_update(
                    gradients=updates,
                    round_number=int(self.current_round.round_id.split('_')[-1]) if self.current_round else 0,
                    callback=self._on_sync_complete
                )
                logger.info(f"📤 Actualizaciones enviadas: {task_id}")

            # Usar OfflineCapabilities si no hay conectividad
            elif self.offline_capabilities:
                from .offline_capabilities import OfflineOperation
                op_id = self.offline_capabilities.queue_operation(
                    operation_type=OfflineOperation.FEDERATED_UPDATE,
                    data={"updates": updates, "metrics": metrics},
                    priority=4  # Alta prioridad
                )
                logger.info(f"📦 Actualizaciones almacenadas offline: {op_id}")

            else:
                logger.warning("⚠️ No hay sistema de sincronización disponible")

        except Exception as e:
            logger.error(f"❌ Error sincronizando updates: {e}")

    def _on_sync_complete(self, task_id: str, status: str, result: Any):
        """Callback para sincronización completada."""
        logger.info(f"🔄 Sincronización {task_id}: {status}")

        if status == "synced":
            self.metrics.rounds_completed += 1
            self.metrics.sync_success_rate = (
                self.metrics.rounds_completed / self.metrics.rounds_participated
            ) if self.metrics.rounds_participated > 0 else 0

    def _update_global_metrics(self, training_metrics: Dict[str, Any], training_time: float):
        """Actualizar métricas globales."""
        self.metrics.rounds_participated += 1
        self.metrics.total_training_time_seconds += training_time
        self.metrics.last_round_timestamp = time.time()

        # Actualizar accuracy promedio
        if "final_accuracy" in training_metrics:
            current_avg = self.metrics.avg_training_accuracy
            rounds = self.metrics.rounds_participated
            self.metrics.avg_training_accuracy = (
                (current_avg * (rounds - 1)) + training_metrics["final_accuracy"]
            ) / rounds

    def _copy_model(self, model: nn.Module) -> nn.Module:
        """Crear copia de modelo."""
        try:
            model_copy = type(model)()
            model_copy.load_state_dict(model.state_dict())
            return model_copy
        except Exception as e:
            logger.error(f"❌ Error copiando modelo: {e}")
            return model  # Fallback

    def _monitor_loop(self):
        """Bucle de monitoreo."""
        while True:
            try:
                time.sleep(self.config.metrics_report_interval)

                # Reportar métricas si hay callbacks
                if self.training_callbacks:
                    current_metrics = {
                        "state": self.current_state.value,
                        "current_round": self.current_round.round_id if self.current_round else None,
                        "global_metrics": self.metrics.__dict__,
                        "resource_status": self.resource_manager.get_resource_status() if self.resource_manager else {}
                    }

                    for callback in self.training_callbacks:
                        try:
                            callback(current_metrics)
                        except Exception as e:
                            logger.warning(f"⚠️ Error en callback de métricas: {e}")

            except Exception as e:
                logger.error(f"❌ Error en monitoreo: {e}")

    def get_fl_status(self) -> Dict[str, Any]:
        """Obtener estado de FL."""
        return {
            "device_id": self.device_id,
            "current_state": self.current_state.value,
            "current_round": self.current_round.__dict__ if self.current_round else None,
            "participation_level": self.config.participation_level.value,
            "metrics": self.metrics.__dict__,
            "rounds_history_count": len(self.rounds_history),
            "has_local_model": self.local_model is not None,
            "local_dataset_size": self.local_dataset_size
        }

    def add_round_callback(self, callback: Callable):
        """Agregar callback para eventos de rondas."""
        self.round_callbacks.append(callback)

    def add_training_callback(self, callback: Callable):
        """Agregar callback para eventos de entrenamiento."""
        self.training_callbacks.append(callback)


# Funciones de conveniencia
def create_edge_fl_for_mobile(
    device_id: str,
    resource_manager: Optional[Any] = None,
    offline_capabilities: Optional[Any] = None,
    edge_sync: Optional[Any] = None
) -> EdgeFederatedLearning:
    """
    Crear FL optimizado para dispositivos móviles.

    Args:
        device_id: ID único del dispositivo
        resource_manager: Gestor de recursos opcional
        offline_capabilities: Capacidades offline opcionales
        edge_sync: Sincronización edge opcional

    Returns:
        Sistema FL configurado
    """
    config = EdgeFLConfig(
        participation_level=EdgeFLParticipation.CONDITIONAL,
        local_epochs=2,  # Menos épocas para móviles
        batch_size=8,  # Batch más pequeño
        max_training_time_seconds=180,  # Menos tiempo
        max_cpu_usage_percent=60.0,  # Más conservador
        enable_differential_privacy=True
    )

    return EdgeFederatedLearning(device_id, config, resource_manager, offline_capabilities, edge_sync)


def create_edge_fl_for_iot(
    device_id: str,
    resource_manager: Optional[Any] = None,
    offline_capabilities: Optional[Any] = None,
    edge_sync: Optional[Any] = None
) -> EdgeFederatedLearning:
    """
    Crear FL optimizado para dispositivos IoT.

    Args:
        device_id: ID único del dispositivo
        resource_manager: Gestor de recursos opcional
        offline_capabilities: Capacidades offline opcionales
        edge_sync: Sincronización edge opcional

    Returns:
        Sistema FL configurado
    """
    config = EdgeFLConfig(
        participation_level=EdgeFLParticipation.PARTIAL,
        local_epochs=1,  # Una sola época
        batch_size=4,  # Batch muy pequeño
        max_training_time_seconds=60,  # Tiempo muy limitado
        max_cpu_usage_percent=50.0,  # Muy conservador
        max_memory_usage_mb=64,  # Memoria muy limitada
        enable_differential_privacy=True,
        max_training_rounds_per_day=2  # Muy limitado
    )

    return EdgeFederatedLearning(device_id, config, resource_manager, offline_capabilities, edge_sync)


if __name__ == "__main__":
    # Demo de EdgeFederatedLearning
    print("🚀 EdgeFederatedLearning Demo")

    # Crear sistema FL para móvil
    edge_fl = create_edge_fl_for_mobile("mobile_device_001")
    edge_fl.start()

    print("Sistema FL iniciado")
    print(f"Device ID: {edge_fl.device_id}")
    print(f"Nivel de participación: {edge_fl.config.participation_level.value}")

    # Simular modelo simple
    class SimpleModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = nn.Linear(784, 10)

        def forward(self, x):
            return self.linear(x.view(x.size(0), -1))

    model = SimpleModel()
    edge_fl.set_global_model(model, "v1.0")

    # Simular datos locales
    edge_fl.set_local_data("mock_data_loader", 1000)

    # Iniciar ronda
    round_accepted = edge_fl.start_round("round_001")
    if round_accepted:
        print("Ronda aceptada, entrenando...")

        # Esperar un poco
        time.sleep(5)

        # Obtener estado
        status = edge_fl.get_fl_status()
        print(f"Estado actual: {status['current_state']}")
        print(f"Rondas participadas: {status['metrics']['rounds_participated']}")

    edge_fl.stop()
    print("Sistema FL detenido")