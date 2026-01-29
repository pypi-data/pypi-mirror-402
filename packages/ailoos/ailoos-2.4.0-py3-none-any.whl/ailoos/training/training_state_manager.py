"""
TrainingStateManager - Gestión del estado persistente del entrenamiento
Permite guardar, cargar y gestionar el estado del entrenamiento asíncrono.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import hashlib
import pickle
import gzip

logger = logging.getLogger(__name__)


class TrainingStatus(Enum):
    """Estados posibles del entrenamiento."""
    NOT_STARTED = "not_started"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


@dataclass
class TrainingSession:
    """Información de una sesión de entrenamiento."""
    session_id: str
    model_version: str
    start_time: float
    last_update: float
    status: TrainingStatus
    current_epoch: int = 0
    total_epochs: int = 0
    current_batch: int = 0
    total_batches: int = 0
    loss_history: List[float] = field(default_factory=list)
    accuracy_history: List[float] = field(default_factory=list)
    learning_rate: float = 0.001
    optimizer_state: Dict[str, Any] = field(default_factory=dict)
    model_config: Dict[str, Any] = field(default_factory=dict)
    training_config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para serialización."""
        return {
            'session_id': self.session_id,
            'model_version': self.model_version,
            'start_time': self.start_time,
            'last_update': self.last_update,
            'status': self.status.value,
            'current_epoch': self.current_epoch,
            'total_epochs': self.total_epochs,
            'current_batch': self.current_batch,
            'total_batches': self.total_batches,
            'loss_history': self.loss_history,
            'accuracy_history': self.accuracy_history,
            'learning_rate': self.learning_rate,
            'optimizer_state': self.optimizer_state,
            'model_config': self.model_config,
            'training_config': self.training_config,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrainingSession':
        """Crear instancia desde diccionario."""
        return cls(
            session_id=data['session_id'],
            model_version=data['model_version'],
            start_time=data['start_time'],
            last_update=data['last_update'],
            status=TrainingStatus(data['status']),
            current_epoch=data.get('current_epoch', 0),
            total_epochs=data.get('total_epochs', 0),
            current_batch=data.get('current_batch', 0),
            total_batches=data.get('total_batches', 0),
            loss_history=data.get('loss_history', []),
            accuracy_history=data.get('accuracy_history', []),
            learning_rate=data.get('learning_rate', 0.001),
            optimizer_state=data.get('optimizer_state', {}),
            model_config=data.get('model_config', {}),
            training_config=data.get('training_config', {}),
            metadata=data.get('metadata', {})
        )


@dataclass
class CheckpointInfo:
    """Información de un checkpoint."""
    checkpoint_id: str
    session_id: str
    epoch: int
    batch: int
    timestamp: float
    file_path: str
    file_size: int
    checksum: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class TrainingStateManager:
    """
    Gestor del estado persistente del entrenamiento.

    Permite guardar y cargar el estado del entrenamiento para soporte
    de pausa/reanudación asíncrona.
    """

    def __init__(self, state_dir: str = "./training_states"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Archivos de estado
        self.sessions_file = self.state_dir / "training_sessions.json"
        self.checkpoints_dir = self.state_dir / "checkpoints"
        self.checkpoints_dir.mkdir(exist_ok=True)

        # Estado en memoria
        self.active_sessions: Dict[str, TrainingSession] = {}
        self.checkpoints: Dict[str, List[CheckpointInfo]] = {}

        # Locks para thread safety
        self._lock = asyncio.Lock()

        logger.info(f"🚀 TrainingStateManager inicializado en {state_dir}")

    async def create_session(
        self,
        session_id: str,
        model_version: str,
        training_config: Dict[str, Any],
        model_config: Dict[str, Any]
    ) -> TrainingSession:
        """
        Crear una nueva sesión de entrenamiento.

        Args:
            session_id: ID único de la sesión
            model_version: Versión del modelo
            training_config: Configuración del entrenamiento
            model_config: Configuración del modelo

        Returns:
            Sesión creada
        """
        async with self._lock:
            if session_id in self.active_sessions:
                raise ValueError(f"Sesión {session_id} ya existe")

            session = TrainingSession(
                session_id=session_id,
                model_version=model_version,
                start_time=time.time(),
                last_update=time.time(),
                status=TrainingStatus.NOT_STARTED,
                training_config=training_config,
                model_config=model_config
            )

            self.active_sessions[session_id] = session
            self.checkpoints[session_id] = []

            await self._save_sessions()
            logger.info(f"✅ Sesión {session_id} creada")

            return session

    async def update_session_progress(
        self,
        session_id: str,
        epoch: int,
        batch: int,
        loss: float,
        accuracy: float,
        learning_rate: float,
        optimizer_state: Dict[str, Any]
    ) -> None:
        """
        Actualizar progreso de una sesión.

        Args:
            session_id: ID de la sesión
            epoch: Época actual
            batch: Batch actual
            loss: Pérdida actual
            accuracy: Precisión actual
            learning_rate: Tasa de aprendizaje
            optimizer_state: Estado del optimizador
        """
        async with self._lock:
            if session_id not in self.active_sessions:
                raise ValueError(f"Sesión {session_id} no encontrada")

            session = self.active_sessions[session_id]
            session.current_epoch = epoch
            session.current_batch = batch
            session.last_update = time.time()
            session.status = TrainingStatus.RUNNING

            # Actualizar historial (mantener últimos 1000 valores)
            session.loss_history.append(loss)
            session.accuracy_history.append(accuracy)
            if len(session.loss_history) > 1000:
                session.loss_history = session.loss_history[-1000:]
                session.accuracy_history = session.accuracy_history[-1000:]

            session.learning_rate = learning_rate
            session.optimizer_state = optimizer_state

            await self._save_sessions()

    async def pause_session(self, session_id: str) -> None:
        """Pausar una sesión de entrenamiento."""
        async with self._lock:
            if session_id not in self.active_sessions:
                raise ValueError(f"Sesión {session_id} no encontrada")

            session = self.active_sessions[session_id]
            session.status = TrainingStatus.PAUSED
            session.last_update = time.time()

            await self._save_sessions()
            logger.info(f"⏸️ Sesión {session_id} pausada")

    async def resume_session(self, session_id: str) -> TrainingSession:
        """Reanudar una sesión pausada."""
        async with self._lock:
            if session_id not in self.active_sessions:
                raise ValueError(f"Sesión {session_id} no encontrada")

            session = self.active_sessions[session_id]
            if session.status != TrainingStatus.PAUSED:
                raise ValueError(f"Sesión {session_id} no está pausada")

            session.status = TrainingStatus.RUNNING
            session.last_update = time.time()

            await self._save_sessions()
            logger.info(f"▶️ Sesión {session_id} reanudada")

            return session

    async def complete_session(self, session_id: str) -> None:
        """Marcar sesión como completada."""
        async with self._lock:
            if session_id not in self.active_sessions:
                raise ValueError(f"Sesión {session_id} no encontrada")

            session = self.active_sessions[session_id]
            session.status = TrainingStatus.COMPLETED
            session.last_update = time.time()

            await self._save_sessions()
            logger.info(f"🎉 Sesión {session_id} completada")

    async def fail_session(self, session_id: str, error: str) -> None:
        """Marcar sesión como fallida."""
        async with self._lock:
            if session_id not in self.active_sessions:
                raise ValueError(f"Sesión {session_id} no encontrada")

            session = self.active_sessions[session_id]
            session.status = TrainingStatus.FAILED
            session.last_update = time.time()
            session.metadata['error'] = error

            await self._save_sessions()
            logger.error(f"❌ Sesión {session_id} falló: {error}")

    async def create_checkpoint(
        self,
        session_id: str,
        model_state: Dict[str, Any],
        optimizer_state: Dict[str, Any],
        epoch: int,
        batch: int,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Crear un checkpoint del modelo.

        Args:
            session_id: ID de la sesión
            model_state: Estado del modelo
            optimizer_state: Estado del optimizador
            epoch: Época actual
            batch: Batch actual
            metadata: Metadatos adicionales

        Returns:
            ID del checkpoint creado
        """
        async with self._lock:
            if session_id not in self.active_sessions:
                raise ValueError(f"Sesión {session_id} no encontrada")

            # Generar ID único para el checkpoint
            timestamp = time.time()
            checkpoint_id = f"{session_id}_epoch_{epoch}_batch_{batch}_{int(timestamp)}"

            # Preparar datos del checkpoint
            checkpoint_data = {
                'session_id': session_id,
                'epoch': epoch,
                'batch': batch,
                'timestamp': timestamp,
                'model_state': model_state,
                'optimizer_state': optimizer_state,
                'metadata': metadata or {}
            }

            # Serializar y comprimir
            checkpoint_file = self.checkpoints_dir / f"{checkpoint_id}.pkl.gz"
            with gzip.open(checkpoint_file, 'wb') as f:
                pickle.dump(checkpoint_data, f)

            # Calcular checksum
            with open(checkpoint_file, 'rb') as f:
                checksum = hashlib.sha256(f.read()).hexdigest()

            # Obtener tamaño del archivo
            file_size = checkpoint_file.stat().st_size

            # Crear info del checkpoint
            checkpoint_info = CheckpointInfo(
                checkpoint_id=checkpoint_id,
                session_id=session_id,
                epoch=epoch,
                batch=batch,
                timestamp=timestamp,
                file_path=str(checkpoint_file),
                file_size=file_size,
                checksum=checksum,
                metadata=metadata or {}
            )

            # Agregar a la lista de checkpoints
            if session_id not in self.checkpoints:
                self.checkpoints[session_id] = []
            self.checkpoints[session_id].append(checkpoint_info)

            # Mantener solo los últimos 10 checkpoints por sesión
            if len(self.checkpoints[session_id]) > 10:
                oldest = self.checkpoints[session_id].pop(0)
                if oldest.file_path.exists():
                    oldest.file_path.unlink()

            await self._save_sessions()
            logger.info(f"💾 Checkpoint {checkpoint_id} creado ({file_size} bytes)")

            return checkpoint_id

    async def load_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """
        Cargar un checkpoint.

        Args:
            checkpoint_id: ID del checkpoint

        Returns:
            Datos del checkpoint
        """
        async with self._lock:
            # Buscar el checkpoint
            checkpoint_info = None
            for session_checkpoints in self.checkpoints.values():
                for cp in session_checkpoints:
                    if cp.checkpoint_id == checkpoint_id:
                        checkpoint_info = cp
                        break
                if checkpoint_info:
                    break

            if not checkpoint_info:
                raise ValueError(f"Checkpoint {checkpoint_id} no encontrado")

            # Cargar datos
            checkpoint_file = Path(checkpoint_info.file_path)
            if not checkpoint_file.exists():
                raise FileNotFoundError(f"Archivo de checkpoint no encontrado: {checkpoint_file}")

            with gzip.open(checkpoint_file, 'rb') as f:
                data = pickle.load(f)

            # Verificar checksum
            with open(checkpoint_file, 'rb') as f:
                actual_checksum = hashlib.sha256(f.read()).hexdigest()

            if actual_checksum != checkpoint_info.checksum:
                raise ValueError(f"Checksum del checkpoint {checkpoint_id} no coincide")

            logger.info(f"📂 Checkpoint {checkpoint_id} cargado")
            return data

    async def get_latest_checkpoint(self, session_id: str) -> Optional[CheckpointInfo]:
        """Obtener el checkpoint más reciente de una sesión."""
        async with self._lock:
            if session_id not in self.checkpoints:
                return None

            checkpoints = self.checkpoints[session_id]
            return max(checkpoints, key=lambda x: x.timestamp) if checkpoints else None

    async def list_sessions(self) -> List[TrainingSession]:
        """Listar todas las sesiones."""
        async with self._lock:
            return list(self.active_sessions.values())

    async def get_session(self, session_id: str) -> Optional[TrainingSession]:
        """Obtener información de una sesión."""
        async with self._lock:
            return self.active_sessions.get(session_id)

    async def list_checkpoints(self, session_id: str) -> List[CheckpointInfo]:
        """Listar checkpoints de una sesión."""
        async with self._lock:
            return self.checkpoints.get(session_id, [])

    async def cleanup_old_checkpoints(self, session_id: str, keep_last: int = 5) -> int:
        """
        Limpiar checkpoints antiguos de una sesión.

        Args:
            session_id: ID de la sesión
            keep_last: Número de checkpoints a mantener

        Returns:
            Número de checkpoints eliminados
        """
        async with self._lock:
            if session_id not in self.checkpoints:
                return 0

            checkpoints = self.checkpoints[session_id]
            if len(checkpoints) <= keep_last:
                return 0

            # Ordenar por timestamp (más recientes primero)
            checkpoints.sort(key=lambda x: x.timestamp, reverse=True)

            # Eliminar checkpoints antiguos
            to_delete = checkpoints[keep_last:]
            deleted_count = 0

            for cp in to_delete:
                try:
                    Path(cp.file_path).unlink()
                    checkpoints.remove(cp)
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Error eliminando checkpoint {cp.checkpoint_id}: {e}")

            await self._save_sessions()
            logger.info(f"🧹 Eliminados {deleted_count} checkpoints antiguos de {session_id}")

            return deleted_count

    async def _save_sessions(self) -> None:
        """Guardar estado de las sesiones en disco."""
        data = {
            'sessions': {sid: session.to_dict() for sid, session in self.active_sessions.items()},
            'checkpoints': {
                sid: [cp.__dict__ for cp in checkpoints]
                for sid, checkpoints in self.checkpoints.items()
            },
            'saved_at': time.time()
        }

        with open(self.sessions_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

    async def load_state(self) -> None:
        """Cargar estado desde disco."""
        async with self._lock:
            if not self.sessions_file.exists():
                logger.info("📂 No hay estado guardado, empezando desde cero")
                return

            try:
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Cargar sesiones
                self.active_sessions = {}
                for sid, session_data in data.get('sessions', {}).items():
                    self.active_sessions[sid] = TrainingSession.from_dict(session_data)

                # Cargar checkpoints
                self.checkpoints = {}
                for sid, checkpoints_data in data.get('checkpoints', {}).items():
                    self.checkpoints[sid] = [
                        CheckpointInfo(**cp_data) for cp_data in checkpoints_data
                    ]

                logger.info(f"📂 Estado cargado: {len(self.active_sessions)} sesiones, "
                          f"{sum(len(cps) for cps in self.checkpoints.values())} checkpoints")

            except Exception as e:
                logger.error(f"❌ Error cargando estado: {e}")
                # En caso de error, empezar desde cero
                self.active_sessions = {}
                self.checkpoints = {}

    async def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del gestor de estado."""
        async with self._lock:
            total_sessions = len(self.active_sessions)
            active_sessions = sum(1 for s in self.active_sessions.values()
                                if s.status == TrainingStatus.RUNNING)
            paused_sessions = sum(1 for s in self.active_sessions.values()
                                 if s.status == TrainingStatus.PAUSED)
            completed_sessions = sum(1 for s in self.active_sessions.values()
                                   if s.status == TrainingStatus.COMPLETED)
            failed_sessions = sum(1 for s in self.active_sessions.values()
                                 if s.status == TrainingStatus.FAILED)

            total_checkpoints = sum(len(cps) for cps in self.checkpoints.values())
            total_checkpoint_size = sum(
                sum(cp.file_size for cp in cps)
                for cps in self.checkpoints.values()
            )

            return {
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'paused_sessions': paused_sessions,
                'completed_sessions': completed_sessions,
                'failed_sessions': failed_sessions,
                'total_checkpoints': total_checkpoints,
                'total_checkpoint_size_mb': total_checkpoint_size / (1024 * 1024),
                'state_dir': str(self.state_dir)
            }