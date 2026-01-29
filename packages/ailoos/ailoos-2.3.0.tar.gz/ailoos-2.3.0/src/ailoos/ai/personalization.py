"""
Servicio de Personalización de IA - Fine-tuning personalizado para EmpoorioLM
============================================================================

Este módulo proporciona funcionalidades completas para fine-tuning personalizado
de EmpoorioLM basado en el perfil de personalización del usuario, incluyendo:

- Preparación de datos de entrenamiento personalizados
- Gestión de sesiones de fine-tuning
- Monitoreo de progreso en tiempo real
- Aplicación de modelos personalizados
- Integración con memoria conversacional
- Gestión de configuraciones de personalización

El servicio está diseñado para trabajar con el sistema federado de AILOOS,
permitiendo personalización individual manteniendo la privacidad y eficiencia.
"""

import logging
import asyncio
import threading
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import json
import uuid
import torch
from torch.utils.data import Dataset, DataLoader
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR

from ..models.empoorio_lm import EmpoorioLM, EmpoorioLMConfig
from ..memory.service import MemoryService
from ..settings.service import SettingsService
from ..core.logging import get_logger

# Configurar logging
logger = get_logger(__name__)


class TrainingCancelled(Exception):
    """Raised when a training session is cancelled."""


@dataclass
class FineTuningConfig:
    """Configuración para una sesión de fine-tuning."""

    # Parámetros de entrenamiento
    learning_rate: float = 5e-5
    batch_size: int = 4
    max_epochs: int = 3
    warmup_steps: int = 100
    weight_decay: float = 0.01
    gradient_clip: float = 1.0

    # Parámetros de datos
    max_seq_length: int = 512
    min_samples: int = 10
    max_samples: int = 1000

    # Parámetros de evaluación
    eval_steps: int = 50
    save_steps: int = 100
    logging_steps: int = 10

    # Configuración específica
    personalization_weight: float = 0.7  # Peso entre datos generales y personales
    memory_importance_threshold: float = 0.6  # Umbral para incluir memoria
    adaptive_learning: bool = True  # Aprendizaje adaptativo basado en feedback


@dataclass
class TrainingSession:
    """Representa una sesión de entrenamiento activa."""

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: int = 0
    status: str = "initialized"  # initialized, preparing, training, evaluating, completed, failed
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # Configuración
    config: FineTuningConfig = field(default_factory=FineTuningConfig)

    # Datos de entrenamiento
    training_samples: int = 0
    validation_samples: int = 0

    # Métricas
    current_epoch: int = 0
    current_step: int = 0
    total_steps: int = 0
    training_loss: float = 0.0
    validation_loss: float = 0.0
    best_loss: float = float('inf')

    # Modelo
    model_path: Optional[str] = None
    base_model_path: Optional[str] = None

    # Metadatos
    metadata: Dict[str, Any] = field(default_factory=dict)
    progress_callbacks: List[callable] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la sesión a diccionario."""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'config': self.config.__dict__,
            'training_samples': self.training_samples,
            'validation_samples': self.validation_samples,
            'current_epoch': self.current_epoch,
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'training_loss': self.training_loss,
            'validation_loss': self.validation_loss,
            'best_loss': self.best_loss,
            'model_path': self.model_path,
            'base_model_path': self.base_model_path,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrainingSession':
        """Crea una sesión desde un diccionario."""
        config = FineTuningConfig(**data.get('config', {}))
        session = cls(
            session_id=data['session_id'],
            user_id=data['user_id'],
            status=data['status'],
            config=config,
            training_samples=data.get('training_samples', 0),
            validation_samples=data.get('validation_samples', 0),
            current_epoch=data.get('current_epoch', 0),
            current_step=data.get('current_step', 0),
            total_steps=data.get('total_steps', 0),
            training_loss=data.get('training_loss', 0.0),
            validation_loss=data.get('validation_loss', 0.0),
            best_loss=data.get('best_loss', float('inf')),
            model_path=data.get('model_path'),
            base_model_path=data.get('base_model_path'),
            metadata=data.get('metadata', {})
        )

        if data.get('start_time'):
            session.start_time = datetime.fromisoformat(data['start_time'])
        if data.get('end_time'):
            session.end_time = datetime.fromisoformat(data['end_time'])

        return session


class PersonalizationDataset(Dataset):
    """Dataset personalizado para fine-tuning."""

    def __init__(self, data: List[Dict[str, Any]], tokenizer=None, max_length: int = 512):
        """
        Inicializa el dataset.

        Args:
            data: Lista de muestras de entrenamiento
            tokenizer: Tokenizador (placeholder por ahora)
            max_length: Longitud máxima de secuencia
        """
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """Obtiene un item del dataset."""
        item = self.data[idx]

        # Placeholder para tokenización - en implementación real usar tokenizador apropiado
        text = item.get('text', '')
        # Simular tokenización básica
        input_ids = torch.randint(0, 50257, (self.max_length,))  # GPT-2 vocab size
        attention_mask = torch.ones(self.max_length, dtype=torch.long)
        labels = input_ids.clone()

        return {
            'input_ids': input_ids,
            'attention_mask': attention_mask,
            'labels': labels
        }


class PersonalizationService:
    """
    Servicio principal para personalización de IA mediante fine-tuning.

    Proporciona una interfaz completa para gestionar el ciclo de vida
    del fine-tuning personalizado de modelos de lenguaje.
    """

    def __init__(self, models_dir: str = "models/personalized",
                 memory_service: Optional[MemoryService] = None,
                 settings_service: Optional[SettingsService] = None):
        """
        Inicializa el servicio de personalización.

        Args:
            models_dir: Directorio para almacenar modelos personalizados
            memory_service: Servicio de memoria conversacional
            settings_service: Servicio de configuraciones
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self.memory_service = memory_service
        self.settings_service = settings_service

        # Gestión de sesiones
        self.active_sessions: Dict[str, TrainingSession] = {}
        self.sessions_lock = threading.RLock()

        # Pool de threads para entrenamiento
        self.training_executor = None
        self._stop_training = threading.Event()
        self._stop_flags: Dict[str, threading.Event] = {}

        logger.info("Servicio de personalización inicializado")

    # ==================== GESTIÓN DE SESIONES ====================

    def create_training_session(self, user_id: int,
                               config: Optional[FineTuningConfig] = None,
                               session_id: Optional[str] = None) -> TrainingSession:
        """
        Crea una nueva sesión de entrenamiento.

        Args:
            user_id: ID del usuario
            config: Configuración personalizada (opcional)

        Returns:
            TrainingSession: Sesión creada
        """
        with self.sessions_lock:
            session = TrainingSession(
                session_id=session_id or str(uuid.uuid4()),
                user_id=user_id,
                config=config or FineTuningConfig()
            )

            self.active_sessions[session.session_id] = session
            self._stop_flags[session.session_id] = threading.Event()
            logger.info(f"Sesión de entrenamiento creada: {session.session_id} para usuario {user_id}")

            return session

    def get_training_session(self, session_id: str) -> Optional[TrainingSession]:
        """
        Obtiene una sesión de entrenamiento.

        Args:
            session_id: ID de la sesión

        Returns:
            Optional[TrainingSession]: Sesión encontrada o None
        """
        with self.sessions_lock:
            return self.active_sessions.get(session_id)

    def list_user_sessions(self, user_id: int) -> List[TrainingSession]:
        """
        Lista todas las sesiones de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            List[TrainingSession]: Lista de sesiones
        """
        with self.sessions_lock:
            return [s for s in self.active_sessions.values() if s.user_id == user_id]

    def cancel_training_session(self, session_id: str) -> bool:
        """
        Cancela una sesión de entrenamiento.

        Args:
            session_id: ID de la sesión

        Returns:
            bool: True si se canceló exitosamente
        """
        with self.sessions_lock:
            session = self.active_sessions.get(session_id)
            if session and session.status in ['initialized', 'preparing', 'training']:
                stop_flag = self._stop_flags.get(session_id)
                if stop_flag:
                    stop_flag.set()
                session.status = 'cancelled'
                session.end_time = datetime.now()
                logger.info(f"Sesión cancelada: {session_id}")
                return True
            return False

    # ==================== PREPARACIÓN DE DATOS ====================

    def prepare_personalization_data(self, user_id: int,
                                   session: TrainingSession) -> List[Dict[str, Any]]:
        """
        Prepara datos de entrenamiento personalizados para un usuario.

        Args:
            user_id: ID del usuario
            session: Sesión de entrenamiento

        Returns:
            List[Dict[str, Any]]: Datos preparados para entrenamiento
        """
        logger.info(f"Preparando datos de personalización para usuario {user_id}")

        training_data = []

        # 1. Obtener datos de memoria conversacional
        if self.memory_service:
            memory_data = self._extract_memory_data(user_id, session.config)
            training_data.extend(memory_data)

        # 2. Obtener datos de configuraciones de personalización
        if self.settings_service:
            personalization_data = self._extract_personalization_data(user_id)
            training_data.extend(personalization_data)

        # 3. Generar datos sintéticos si es necesario
        if len(training_data) < session.config.min_samples:
            synthetic_data = self._generate_synthetic_data(user_id, session.config)
            training_data.extend(synthetic_data)

        # 4. Limitar cantidad de datos
        if len(training_data) > session.config.max_samples:
            # Mantener los más importantes
            training_data.sort(key=lambda x: x.get('importance', 0), reverse=True)
            training_data = training_data[:session.config.max_samples]

        # 5. Preparar formato final
        formatted_data = self._format_training_data(training_data)

        session.training_samples = len(formatted_data)
        logger.info(f"Datos preparados: {len(formatted_data)} muestras para usuario {user_id}")

        return formatted_data

    def _extract_memory_data(self, user_id: int, config: FineTuningConfig) -> List[Dict[str, Any]]:
        """Extrae datos relevantes de la memoria conversacional."""
        if not self.memory_service:
            return []

        try:
            # Obtener ítems de memoria importantes
            important_memories = self.memory_service.get_important_memories(
                user_id, min_importance=config.memory_importance_threshold, limit=200
            )

            memory_data = []
            for memory in important_memories:
                memory_data.append({
                    'text': memory.content,
                    'importance': memory.importance,
                    'category': memory.category,
                    'source': 'memory',
                    'metadata': memory.metadata
                })

            return memory_data

        except Exception as e:
            logger.warning(f"Error al extraer datos de memoria para usuario {user_id}: {e}")
            return []

    def _extract_personalization_data(self, user_id: int) -> List[Dict[str, Any]]:
        """Extrae datos de las configuraciones de personalización."""
        if not self.settings_service:
            return []

        try:
            settings = self.settings_service.get_user_settings(user_id)
            personalization = settings.personalization

            personalization_data = []

            # Información personal
            if personalization.nickname:
                personalization_data.append({
                    'text': f"Mi nombre es {personalization.nickname}",
                    'importance': 0.9,
                    'category': 'personal',
                    'source': 'settings'
                })

            if personalization.occupation:
                personalization_data.append({
                    'text': f"Mi ocupación es {personalization.occupation}",
                    'importance': 0.8,
                    'category': 'personal',
                    'source': 'settings'
                })

            if personalization.more_about_you:
                personalization_data.append({
                    'text': personalization.more_about_you,
                    'importance': 0.7,
                    'category': 'personal',
                    'source': 'settings'
                })

            # Preferencias - verificar atributos disponibles
            if hasattr(personalization, 'base_style_tone') and personalization.base_style_tone:
                personalization_data.append({
                    'text': f"Mi estilo de comunicación es {personalization.base_style_tone}",
                    'importance': 0.8,
                    'category': 'preference',
                    'source': 'settings'
                })

            return personalization_data

        except Exception as e:
            logger.warning(f"Error al extraer datos de personalización para usuario {user_id}: {e}")
            return []

    def _generate_synthetic_data(self, user_id: int, config: FineTuningConfig) -> List[Dict[str, Any]]:
        """Genera datos sintéticos cuando hay pocos datos reales."""
        # Placeholder para generación de datos sintéticos
        # En implementación real, usar técnicas como data augmentation
        synthetic_data = []

        base_prompts = [
            "Hola, ¿cómo estás?",
            "¿Puedes ayudarme con una tarea?",
            "Me gustaría aprender sobre...",
            "¿Cuál es tu opinión sobre...?",
            "Necesito información sobre..."
        ]

        for i, prompt in enumerate(base_prompts):
            synthetic_data.append({
                'text': prompt,
                'importance': 0.5,
                'category': 'synthetic',
                'source': 'generated'
            })

        return synthetic_data[:config.min_samples]

    def _format_training_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Formatea los datos crudos para entrenamiento."""
        formatted_data = []

        for item in raw_data:
            # Crear pares de entrenamiento (input, target)
            text = item['text']

            # Para fine-tuning causal, input y target son el mismo texto
            formatted_item = {
                'text': text,
                'importance': item.get('importance', 0.5),
                'category': item.get('category', 'general'),
                'source': item.get('source', 'unknown')
            }

            formatted_data.append(formatted_item)

        return formatted_data

    # ==================== ENTRENAMIENTO ====================

    def start_fine_tuning(self, session_id: str, run_async: bool = True) -> bool:
        """
        Inicia el proceso de fine-tuning para una sesión.

        Args:
            session_id: ID de la sesión

        Returns:
            bool: True si se inició exitosamente
        """
        with self.sessions_lock:
            session = self.active_sessions.get(session_id)
            if not session:
                logger.error(f"Sesión no encontrada: {session_id}")
                return False

            if session.status != 'initialized':
                logger.error(f"Sesión en estado inválido: {session.status}")
                return False

            # Cambiar estado y iniciar
            session.status = 'preparing'
            session.start_time = datetime.now()

            if run_async:
                # Iniciar entrenamiento en thread separado
                training_thread = threading.Thread(
                    target=self._run_training_pipeline,
                    args=(session,),
                    daemon=True
                )
                training_thread.start()
            else:
                self._run_training_pipeline(session)

            logger.info(f"Fine-tuning iniciado para sesión: {session_id}")
            return True

    def _run_training_pipeline(self, session: TrainingSession) -> None:
        """Ejecuta el pipeline completo de entrenamiento."""
        try:
            # 1. Preparar datos
            session.status = 'preparing'
            self._notify_progress(session, "Preparando datos...")

            training_data = self.prepare_personalization_data(session.user_id, session)

            if len(training_data) < session.config.min_samples:
                raise ValueError(f"Insuficientes datos de entrenamiento: {len(training_data)}")

            # 2. Configurar modelo
            self._notify_progress(session, "Configurando modelo...")
            model = self._setup_model(session)

            # 3. Crear datasets
            train_dataset, val_dataset = self._create_datasets(training_data, session.config)
            session.training_samples = len(train_dataset)
            session.validation_samples = len(val_dataset)

            # 4. Entrenar
            session.status = 'training'
            self._notify_progress(session, "Iniciando entrenamiento...")

            trained_model = self._train_model(model, train_dataset, val_dataset, session)

            # 5. Evaluar y guardar
            session.status = 'evaluating'
            self._notify_progress(session, "Evaluando modelo...")

            self._evaluate_and_save_model(trained_model, session)

            # 6. Completar
            session.status = 'completed'
            session.end_time = datetime.now()
            self._notify_progress(session, "Fine-tuning completado exitosamente")

            logger.info(f"Entrenamiento completado para sesión: {session.session_id}")

        except TrainingCancelled:
            session.status = 'cancelled'
            session.end_time = datetime.now()
            session.metadata['error'] = "Training cancelled"
            self._notify_progress(session, "Entrenamiento cancelado por el usuario")
            logger.info(f"Entrenamiento cancelado para sesión {session.session_id}")
        except Exception as e:
            session.status = 'failed'
            session.end_time = datetime.now()
            session.metadata['error'] = str(e)
            self._notify_progress(session, f"Error en entrenamiento: {e}")
            logger.error(f"Error en entrenamiento de sesión {session.session_id}: {e}")
        finally:
            with self.sessions_lock:
                self._stop_flags.pop(session.session_id, None)

    def _setup_model(self, session: TrainingSession) -> EmpoorioLM:
        """Configura el modelo para fine-tuning."""
        # Cargar modelo base
        config = EmpoorioLMConfig()
        model = EmpoorioLM(config)

        # Congelar capas base si es necesario (LoRA, etc.)
        # Por ahora, fine-tuning completo

        session.base_model_path = "models/empoorio_lm_base"
        return model

    def _create_datasets(self, data: List[Dict[str, Any]], config: FineTuningConfig) -> Tuple[Dataset, Dataset]:
        """Crea datasets de entrenamiento y validación."""
        # Dividir datos (80% train, 20% val)
        split_idx = int(len(data) * 0.8)
        train_data = data[:split_idx]
        val_data = data[split_idx:]

        train_dataset = PersonalizationDataset(train_data, max_length=config.max_seq_length)
        val_dataset = PersonalizationDataset(val_data, max_length=config.max_seq_length)

        return train_dataset, val_dataset

    def _train_model(self, model: EmpoorioLM, train_dataset: Dataset,
                    val_dataset: Dataset, session: TrainingSession) -> EmpoorioLM:
        """Entrena el modelo."""
        config = session.config

        # Configurar optimizador
        optimizer = optim.AdamW(
            model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay
        )

        # Configurar scheduler
        total_steps = len(train_dataset) * config.max_epochs // config.batch_size
        scheduler = CosineAnnealingLR(optimizer, T_max=total_steps)

        # DataLoaders
        train_loader = DataLoader(train_dataset, batch_size=config.batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=config.batch_size)

        session.total_steps = total_steps

        # Ciclo de entrenamiento
        best_loss = float('inf')
        patience = 3
        patience_counter = 0

        for epoch in range(config.max_epochs):
            stop_flag = self._stop_flags.get(session.session_id)
            if stop_flag and stop_flag.is_set():
                raise TrainingCancelled()
            session.current_epoch = epoch + 1

            # Entrenamiento
            model.train()
            epoch_loss = 0.0

            for step, batch in enumerate(train_loader):
                stop_flag = self._stop_flags.get(session.session_id)
                if stop_flag and stop_flag.is_set():
                    raise TrainingCancelled()
                session.current_step = step + 1

                # Forward pass
                outputs = model(**batch)
                loss = outputs.get('loss', torch.tensor(0.0))

                # Backward pass
                optimizer.zero_grad()
                loss.backward()

                # Gradient clipping
                torch.nn.utils.clip_grad_norm_(model.parameters(), config.gradient_clip)

                optimizer.step()
                scheduler.step()

                epoch_loss += loss.item()
                session.training_loss = epoch_loss / (step + 1)

                # Logging
                if step % config.logging_steps == 0:
                    self._notify_progress(session, f"Epoch {epoch+1}, Step {step+1}, Loss: {loss.item():.4f}")

            # Validación
            val_loss = self._validate_model(model, val_loader)
            session.validation_loss = val_loss

            # Early stopping
            if val_loss < best_loss:
                best_loss = val_loss
                session.best_loss = best_loss
                patience_counter = 0
                # Guardar mejor modelo
                self._save_checkpoint(model, session, is_best=True)
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    logger.info(f"Early stopping en epoch {epoch+1}")
                    break

            # Guardar checkpoint periódico
            if epoch % config.save_steps == 0:
                self._save_checkpoint(model, session, is_best=False)

        return model

    def _validate_model(self, model: EmpoorioLM, val_loader: DataLoader) -> float:
        """Valida el modelo en el conjunto de validación."""
        model.eval()
        total_loss = 0.0
        num_batches = 0

        with torch.no_grad():
            for batch in val_loader:
                outputs = model(**batch)
                loss = outputs.get('loss', torch.tensor(0.0))
                total_loss += loss.item()
                num_batches += 1

        return total_loss / num_batches if num_batches > 0 else 0.0

    def _save_checkpoint(self, model: EmpoorioLM, session: TrainingSession, is_best: bool = False) -> None:
        """Guarda un checkpoint del modelo."""
        checkpoint_dir = self.models_dir / f"user_{session.user_id}" / session.session_id
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        if is_best:
            model_path = checkpoint_dir / "best_model.pt"
        else:
            model_path = checkpoint_dir / f"checkpoint_epoch_{session.current_epoch}.pt"

        torch.save({
            'model_state_dict': model.state_dict(),
            'config': model.config.__dict__,
            'session': session.to_dict()
        }, model_path)

        if is_best:
            session.model_path = str(model_path)

        logger.debug(f"Checkpoint guardado: {model_path}")

    def _evaluate_and_save_model(self, model: EmpoorioLM, session: TrainingSession) -> None:
        """Evalúa y guarda el modelo final."""
        # Guardar modelo final
        final_model_path = self.models_dir / f"user_{session.user_id}" / f"{session.session_id}_final"
        final_model_path.mkdir(parents=True, exist_ok=True)

        model.save_pretrained(str(final_model_path))
        session.model_path = str(final_model_path / "pytorch_model.bin")

        # Calcular métricas finales
        session.metadata.update({
            'final_training_loss': session.training_loss,
            'final_validation_loss': session.validation_loss,
            'total_epochs': session.current_epoch,
            'model_size_mb': self._calculate_model_size(model)
        })

    def _calculate_model_size(self, model: nn.Module) -> float:
        """Calcula el tamaño del modelo en MB."""
        param_size = 0
        for param in model.parameters():
            param_size += param.nelement() * param.element_size()
        buffer_size = 0
        for buffer in model.buffers():
            buffer_size += buffer.nelement() * buffer.element_size()
        return (param_size + buffer_size) / 1024 / 1024

    # ==================== MONITOREO Y PROGRESO ====================

    def add_progress_callback(self, session_id: str, callback: callable) -> None:
        """
        Agrega un callback para monitorear el progreso.

        Args:
            session_id: ID de la sesión
            callback: Función a llamar con actualizaciones
        """
        with self.sessions_lock:
            session = self.active_sessions.get(session_id)
            if session:
                session.progress_callbacks.append(callback)

    def _notify_progress(self, session: TrainingSession, message: str) -> None:
        """Notifica progreso a todos los callbacks registrados."""
        for callback in session.progress_callbacks:
            try:
                callback(session.session_id, session.status, message, session.to_dict())
            except Exception as e:
                logger.warning(f"Error en callback de progreso: {e}")

    def get_training_progress(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el progreso actual de una sesión de entrenamiento.

        Args:
            session_id: ID de la sesión

        Returns:
            Optional[Dict[str, Any]]: Información de progreso o None
        """
        session = self.get_training_session(session_id)
        if not session:
            return None

        progress = {
            'session_id': session.session_id,
            'status': session.status,
            'progress_percentage': self._calculate_progress_percentage(session),
            'current_epoch': session.current_epoch,
            'current_step': session.current_step,
            'total_steps': session.total_steps,
            'training_loss': session.training_loss,
            'validation_loss': session.validation_loss,
            'estimated_time_remaining': self._estimate_time_remaining(session),
            'message': self._get_progress_message(session)
        }

        return progress

    def _calculate_progress_percentage(self, session: TrainingSession) -> float:
        """Calcula el porcentaje de progreso."""
        if session.status == 'completed':
            return 100.0
        elif session.status == 'failed':
            return 0.0
        elif session.status in ['initialized', 'preparing']:
            return 5.0
        elif session.status == 'training':
            if session.total_steps > 0:
                return 10.0 + (session.current_step / session.total_steps) * 85.0
            else:
                return 10.0 + (session.current_epoch / session.config.max_epochs) * 85.0
        elif session.status == 'evaluating':
            return 95.0
        else:
            return 0.0

    def _estimate_time_remaining(self, session: TrainingSession) -> Optional[str]:
        """Estima el tiempo restante de entrenamiento."""
        if not session.start_time or session.total_steps == 0:
            return None

        elapsed = datetime.now() - session.start_time
        elapsed_seconds = elapsed.total_seconds()

        if session.current_step > 0:
            avg_time_per_step = elapsed_seconds / session.current_step
            remaining_steps = session.total_steps - session.current_step
            remaining_seconds = avg_time_per_step * remaining_steps

            return f"{remaining_seconds:.0f}s"
        else:
            return "Calculando..."

    def _get_progress_message(self, session: TrainingSession) -> str:
        """Obtiene un mensaje descriptivo del progreso."""
        if session.status == 'preparing':
            return "Preparando datos de entrenamiento..."
        elif session.status == 'training':
            return f"Entrenando modelo (Epoch {session.current_epoch}/{session.config.max_epochs})"
        elif session.status == 'evaluating':
            return "Evaluando modelo final..."
        elif session.status == 'completed':
            return "Entrenamiento completado exitosamente"
        elif session.status == 'failed':
            return f"Error en entrenamiento: {session.metadata.get('error', 'Desconocido')}"
        elif session.status == 'cancelled':
            return "Entrenamiento cancelado por el usuario"
        else:
            return "Sesión inicializada"

    # ==================== APLICACIÓN DE MODELOS ====================

    def apply_personalized_model(self, user_id: int, model_path: Optional[str] = None) -> bool:
        """
        Aplica un modelo personalizado para un usuario.

        Args:
            user_id: ID del usuario
            model_path: Ruta al modelo (opcional, usa el más reciente)

        Returns:
            bool: True si se aplicó exitosamente
        """
        try:
            if not model_path:
                model_path = self._find_latest_model(user_id)

            if not model_path or not Path(model_path).exists():
                logger.warning(f"No se encontró modelo personalizado para usuario {user_id}")
                return False

            # Cargar modelo
            model = EmpoorioLM.from_pretrained(str(Path(model_path).parent))

            # Aquí se integraría con el sistema de inferencia
            # Por ahora, solo registrar que el modelo está activo

            logger.info(f"Modelo personalizado aplicado para usuario {user_id}: {model_path}")
            return True

        except Exception as e:
            logger.error(f"Error al aplicar modelo personalizado para usuario {user_id}: {e}")
            return False

    def _find_latest_model(self, user_id: int) -> Optional[str]:
        """Encuentra el modelo más reciente para un usuario."""
        user_dir = self.models_dir / f"user_{user_id}"
        if not user_dir.exists():
            return None

        # Buscar sesiones completadas
        model_paths = []
        for session_dir in user_dir.iterdir():
            if session_dir.is_dir():
                final_model = session_dir / "pytorch_model.bin"
                if final_model.exists():
                    model_paths.append(str(final_model))

        # Retornar el más reciente (por nombre de directorio)
        if model_paths:
            return max(model_paths, key=lambda x: Path(x).parent.name)

        return None

    def get_personalized_model_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene información sobre el modelo personalizado activo.

        Args:
            user_id: ID del usuario

        Returns:
            Optional[Dict[str, Any]]: Información del modelo o None
        """
        model_path = self._find_latest_model(user_id)
        if not model_path:
            return None

        model_dir = Path(model_path).parent

        # Cargar información del modelo
        info_path = model_dir / "model_info.json"
        if info_path.exists():
            with open(info_path, 'r') as f:
                info = json.load(f)
        else:
            info = {"model_type": "EmpoorioLM", "version": "personalized"}

        # Agregar información adicional
        info.update({
            'model_path': model_path,
            'last_updated': datetime.fromtimestamp(model_dir.stat().st_mtime).isoformat(),
            'size_mb': Path(model_path).stat().st_size / 1024 / 1024
        })

        return info

    # ==================== GESTIÓN DE RECURSOS ====================

    def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """
        Limpia sesiones antiguas completadas.

        Args:
            max_age_days: Días de antigüedad máxima

        Returns:
            int: Número de sesiones limpiadas
        """
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        cleaned_count = 0

        with self.sessions_lock:
            to_remove = []
            for session_id, session in self.active_sessions.items():
                if (session.status in ['completed', 'failed', 'cancelled'] and
                    session.end_time and session.end_time < cutoff_date):
                    to_remove.append(session_id)

            for session_id in to_remove:
                del self.active_sessions[session_id]
                cleaned_count += 1

        if cleaned_count > 0:
            logger.info(f"Sesiones antiguas limpiadas: {cleaned_count}")

        return cleaned_count

    def get_service_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del servicio.

        Returns:
            Dict[str, Any]: Estadísticas del servicio
        """
        with self.sessions_lock:
            total_sessions = len(self.active_sessions)
            active_sessions = sum(1 for s in self.active_sessions.values()
                                if s.status == 'training')
            completed_sessions = sum(1 for s in self.active_sessions.values()
                                   if s.status == 'completed')

        return {
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'completed_sessions': completed_sessions,
            'models_dir_size_mb': self._calculate_dir_size(self.models_dir)
        }

    def _calculate_dir_size(self, path: Path) -> float:
        """Calcula el tamaño de un directorio en MB."""
        total_size = 0
        for file_path in path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size / 1024 / 1024

    # ==================== MÉTODOS DE INTEGRACIÓN ====================

    def set_memory_service(self, memory_service: MemoryService) -> None:
        """
        Establece el servicio de memoria para integración.

        Args:
            memory_service: Instancia del servicio de memoria
        """
        self.memory_service = memory_service
        logger.info("Servicio de memoria integrado con personalización")

    def set_settings_service(self, settings_service: SettingsService) -> None:
        """
        Establece el servicio de configuraciones para integración.

        Args:
            settings_service: Instancia del servicio de configuraciones
        """
        self.settings_service = settings_service
        logger.info("Servicio de configuraciones integrado con personalización")

    # ==================== MÉTODOS DE UTILIDAD ====================

    def validate_training_config(self, config: FineTuningConfig) -> List[str]:
        """
        Valida una configuración de entrenamiento.

        Args:
            config: Configuración a validar

        Returns:
            List[str]: Lista de errores de validación
        """
        errors = []

        if config.learning_rate <= 0:
            errors.append("Learning rate debe ser positivo")

        if config.batch_size <= 0:
            errors.append("Batch size debe ser positivo")

        if config.max_epochs <= 0:
            errors.append("Max epochs debe ser positivo")

        if not (0.0 <= config.personalization_weight <= 1.0):
            errors.append("Personalization weight debe estar entre 0.0 y 1.0")

        if config.max_seq_length > 1024:
            errors.append("Max sequence length no puede exceder 1024")

        return errors
