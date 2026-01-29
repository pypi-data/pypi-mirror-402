"""
CheckpointManager - Sistema de checkpoints del modelo con optimización
Gestiona la creación, almacenamiento y recuperación de checkpoints con optimizaciones.
"""

import asyncio
import logging
import time
import torch
import hashlib
import pickle
import gzip
import lzma
import json
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor
import numpy as np

logger = logging.getLogger(__name__)


class CompressionType(Enum):
    """Tipos de compresión disponibles."""
    NONE = "none"
    GZIP = "gzip"
    LZMA = "lzma"


class CheckpointStrategy(Enum):
    """Estrategias de checkpoint."""
    ALL = "all"  # Guardar todos los checkpoints
    BEST_ONLY = "best_only"  # Solo el mejor checkpoint
    LAST_N = "last_n"  # Últimos N checkpoints
    INTERVAL = "interval"  # Cada N pasos
    ADAPTIVE = "adaptive"  # Adaptativo basado en mejora


@dataclass
class CheckpointConfig:
    """Configuración del sistema de checkpoints."""
    compression: CompressionType = CompressionType.GZIP
    strategy: CheckpointStrategy = CheckpointStrategy.LAST_N
    max_checkpoints: int = 5
    checkpoint_interval: int = 1000  # Pasos entre checkpoints
    min_improvement: float = 0.001  # Mejora mínima para guardar
    auto_cleanup: bool = True
    compression_level: int = 6  # Nivel de compresión (1-9)
    enable_deduplication: bool = True
    max_concurrent_saves: int = 2


@dataclass
class CheckpointMetadata:
    """Metadatos de un checkpoint."""
    checkpoint_id: str
    session_id: str
    epoch: int
    batch: int
    global_step: int
    timestamp: float
    model_size_bytes: int
    compressed_size_bytes: int
    compression_ratio: float
    checksum: str
    compression_type: CompressionType
    metrics: Dict[str, float] = field(default_factory=dict)
    optimizer_stats: Dict[str, Any] = field(default_factory=dict)
    training_config: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


class CheckpointManager:
    """
    Gestor optimizado de checkpoints del modelo.

    Características:
    - Compresión automática (gzip, lzma)
    - Deduplicación de parámetros
    - Estrategias inteligentes de retención
    - Guardado asíncrono
    - Verificación de integridad
    """

    def __init__(
        self,
        checkpoint_dir: str = "./checkpoints",
        config: CheckpointConfig = None
    ):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.config = config or CheckpointConfig()
        self.metadata_file = self.checkpoint_dir / "checkpoint_metadata.json"

        # Estado interno
        self.checkpoints: Dict[str, CheckpointMetadata] = {}
        self.session_checkpoints: Dict[str, List[str]] = {}
        self.best_checkpoint: Optional[str] = None
        self.best_metric_value: float = float('-inf')

        # Pool de hilos para operaciones I/O
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_saves)
        self._lock = None  # Se crea cuando se necesita

        # Cache para deduplicación
        self.param_cache: Dict[str, torch.Tensor] = {}
        self.tensor_hashes: Dict[str, str] = {}

        logger.info(f"🚀 CheckpointManager inicializado en {checkpoint_dir}")
        logger.info(f"📊 Configuración: {self.config}")

    async def _get_lock(self):
        """Obtener lock de forma lazy."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def save_checkpoint(
        self,
        session_id: str,
        model: torch.nn.Module,
        optimizer: torch.optim.Optimizer,
        epoch: int,
        batch: int,
        global_step: int,
        metrics: Dict[str, float] = None,
        training_config: Dict[str, Any] = None,
        tags: List[str] = None
    ) -> str:
        """
        Guardar un checkpoint del modelo de forma optimizada.

        Args:
            session_id: ID de la sesión de entrenamiento
            model: Modelo PyTorch
            optimizer: Optimizador
            epoch: Época actual
            batch: Batch actual
            global_step: Paso global
            metrics: Métricas actuales
            training_config: Configuración del entrenamiento
            tags: Etiquetas del checkpoint

        Returns:
            ID del checkpoint creado
        """
        async with await self._get_lock():
            # Generar ID único
            timestamp = time.time()
            checkpoint_id = f"{session_id}_epoch_{epoch}_batch_{batch}_step_{global_step}_{int(timestamp)}"

            # Preparar datos del checkpoint
            model_state = model.state_dict()
            optimizer_state = optimizer.state_dict()

            checkpoint_data = {
                'model_state': model_state,
                'optimizer_state': optimizer_state,
                'epoch': epoch,
                'batch': batch,
                'global_step': global_step,
                'timestamp': timestamp,
                'metrics': metrics or {},
                'training_config': training_config or {},
                'tags': tags or []
            }

            # Optimizar datos antes de guardar
            optimized_data = await self._optimize_checkpoint_data(checkpoint_data)

            # Guardar en background
            save_task = asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._save_checkpoint_sync,
                checkpoint_id,
                optimized_data
            )

            # Crear metadatos
            metadata = CheckpointMetadata(
                checkpoint_id=checkpoint_id,
                session_id=session_id,
                epoch=epoch,
                batch=batch,
                global_step=global_step,
                timestamp=timestamp,
                model_size_bytes=self._calculate_tensor_size(model_state),
                compressed_size_bytes=0,  # Se actualizará después del guardado
                compression_ratio=0.0,
                checksum="",
                compression_type=self.config.compression,
                metrics=metrics or {},
                optimizer_stats=self._extract_optimizer_stats(optimizer_state),
                training_config=training_config or {},
                tags=tags or []
            )

            # Esperar a que termine el guardado
            compressed_size, checksum = await save_task

            # Actualizar metadatos
            metadata.compressed_size_bytes = compressed_size
            metadata.checksum = checksum
            metadata.compression_ratio = compressed_size / metadata.model_size_bytes if metadata.model_size_bytes > 0 else 0

            # Registrar checkpoint
            self.checkpoints[checkpoint_id] = metadata
            if session_id not in self.session_checkpoints:
                self.session_checkpoints[session_id] = []
            self.session_checkpoints[session_id].append(checkpoint_id)

            # Aplicar estrategia de retención
            await self._apply_retention_strategy(session_id)

            # Actualizar mejor checkpoint si aplica
            await self._update_best_checkpoint(checkpoint_id, metrics)

            # Guardar metadatos
            await self._save_metadata()

            logger.info(f"💾 Checkpoint {checkpoint_id} guardado "
                      ".2f"
                      ".2f")

            return checkpoint_id

    async def load_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """
        Cargar un checkpoint.

        Args:
            checkpoint_id: ID del checkpoint

        Returns:
            Datos del checkpoint
        """
        async with await self._get_lock():
            if checkpoint_id not in self.checkpoints:
                raise ValueError(f"Checkpoint {checkpoint_id} no encontrado")

            metadata = self.checkpoints[checkpoint_id]
            checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.pkl"

            if self.config.compression == CompressionType.GZIP:
                opener = gzip.open
            elif self.config.compression == CompressionType.LZMA:
                opener = lzma.open
            else:
                opener = open

            # Cargar en thread pool
            data = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._load_checkpoint_sync,
                checkpoint_file, opener
            )

            # Verificar checksum
            actual_checksum = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._calculate_checksum,
                checkpoint_file
            )

            if actual_checksum != metadata.checksum:
                raise ValueError(f"Checksum del checkpoint {checkpoint_id} no coincide")

            # Restaurar datos optimizados
            restored_data = await self._restore_checkpoint_data(data)

            logger.info(f"📂 Checkpoint {checkpoint_id} cargado")
            return restored_data

    async def list_checkpoints(self, session_id: Optional[str] = None) -> List[CheckpointMetadata]:
        """
        Listar checkpoints disponibles.

        Args:
            session_id: Filtrar por sesión (opcional)

        Returns:
            Lista de metadatos de checkpoints
        """
        async with await self._get_lock():
            if session_id:
                checkpoint_ids = self.session_checkpoints.get(session_id, [])
                return [self.checkpoints[cid] for cid in checkpoint_ids if cid in self.checkpoints]
            else:
                return list(self.checkpoints.values())

    async def get_best_checkpoint(self, session_id: str) -> Optional[CheckpointMetadata]:
        """Obtener el mejor checkpoint de una sesión."""
        async with await self._get_lock():
            if not self.best_checkpoint or self.checkpoints[self.best_checkpoint].session_id != session_id:
                return None
            return self.checkpoints[self.best_checkpoint]

    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Eliminar un checkpoint.

        Args:
            checkpoint_id: ID del checkpoint

        Returns:
            True si se eliminó correctamente
        """
        async with await self._get_lock():
            if checkpoint_id not in self.checkpoints:
                return False

            metadata = self.checkpoints[checkpoint_id]
            checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.pkl"

            # Eliminar archivo
            try:
                if checkpoint_file.exists():
                    checkpoint_file.unlink()
            except Exception as e:
                logger.warning(f"Error eliminando archivo {checkpoint_file}: {e}")

            # Eliminar de registros
            del self.checkpoints[checkpoint_id]
            if metadata.session_id in self.session_checkpoints:
                if checkpoint_id in self.session_checkpoints[metadata.session_id]:
                    self.session_checkpoints[metadata.session_id].remove(checkpoint_id)

            # Actualizar mejor checkpoint si es necesario
            if self.best_checkpoint == checkpoint_id:
                self.best_checkpoint = None
                self.best_metric_value = float('-inf')

            await self._save_metadata()
            logger.info(f"🗑️ Checkpoint {checkpoint_id} eliminado")

            return True

    async def cleanup_checkpoints(
        self,
        session_id: str,
        keep_last: int = None,
        keep_best: bool = True
    ) -> int:
        """
        Limpiar checkpoints antiguos de una sesión.

        Args:
            session_id: ID de la sesión
            keep_last: Número de checkpoints a mantener
            keep_best: Mantener el mejor checkpoint

        Returns:
            Número de checkpoints eliminados
        """
        async with await self._get_lock():
            if session_id not in self.session_checkpoints:
                return 0

            checkpoint_ids = self.session_checkpoints[session_id].copy()
            keep_count = keep_last or self.config.max_checkpoints

            if len(checkpoint_ids) <= keep_count:
                return 0

            # Ordenar por timestamp (más recientes primero)
            checkpoints_with_time = [
                (cid, self.checkpoints[cid].timestamp)
                for cid in checkpoint_ids
                if cid in self.checkpoints
            ]
            checkpoints_with_time.sort(key=lambda x: x[1], reverse=True)

            # Determinar qué checkpoints mantener
            to_keep = set()
            for i, (cid, _) in enumerate(checkpoints_with_time[:keep_count]):
                to_keep.add(cid)

            # Mantener el mejor si se solicita
            if keep_best and self.best_checkpoint and self.best_checkpoint in checkpoint_ids:
                to_keep.add(self.best_checkpoint)

            # Eliminar los demás
            deleted_count = 0
            for cid in checkpoint_ids:
                if cid not in to_keep:
                    await self.delete_checkpoint(cid)
                    deleted_count += 1

            logger.info(f"🧹 Limpiados {deleted_count} checkpoints antiguos de {session_id}")
            return deleted_count

    async def get_checkpoint_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del sistema de checkpoints."""
        async with await self._get_lock():
            total_checkpoints = len(self.checkpoints)
            total_sessions = len(self.session_checkpoints)

            if total_checkpoints == 0:
                return {
                    'total_checkpoints': 0,
                    'total_sessions': 0,
                    'total_size_bytes': 0,
                    'total_compressed_size_bytes': 0,
                    'avg_compression_ratio': 0.0,
                    'checkpoint_dir': str(self.checkpoint_dir)
                }

            total_size = sum(cp.model_size_bytes for cp in self.checkpoints.values())
            total_compressed_size = sum(cp.compressed_size_bytes for cp in self.checkpoints.values())
            avg_compression_ratio = total_compressed_size / total_size if total_size > 0 else 0

            return {
                'total_checkpoints': total_checkpoints,
                'total_sessions': total_sessions,
                'total_size_bytes': total_size,
                'total_compressed_size_bytes': total_compressed_size,
                'avg_compression_ratio': avg_compression_ratio,
                'checkpoint_dir': str(self.checkpoint_dir),
                'best_checkpoint': self.best_checkpoint
            }

    async def _optimize_checkpoint_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimizar datos del checkpoint antes de guardar."""
        optimized = data.copy()

        if self.config.enable_deduplication:
            # Aplicar deduplicación de tensores
            optimized['model_state'] = await self._deduplicate_tensors(data['model_state'])

        return optimized

    async def _deduplicate_tensors(self, state_dict: Dict[str, torch.Tensor]) -> Dict[str, Any]:
        """Deduplicar tensores idénticos."""
        deduplicated = {}
        tensor_refs = {}

        for key, tensor in state_dict.items():
            # Calcular hash del tensor
            tensor_hash = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._tensor_hash,
                tensor
            )

            if tensor_hash in self.tensor_hashes:
                # Tensor ya existe, crear referencia
                existing_key = self.tensor_hashes[tensor_hash]
                tensor_refs[key] = existing_key
            else:
                # Nuevo tensor
                deduplicated[key] = tensor
                self.tensor_hashes[tensor_hash] = key

        return {
            'tensors': deduplicated,
            'refs': tensor_refs
        }

    async def _restore_checkpoint_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Restaurar datos optimizados del checkpoint."""
        restored = data.copy()

        if 'model_state' in data and isinstance(data['model_state'], dict):
            model_state_data = data['model_state']
            if 'tensors' in model_state_data and 'refs' in model_state_data:
                # Restaurar deduplicación
                restored_state = {}
                tensors = model_state_data['tensors']
                refs = model_state_data['refs']

                # Restaurar tensores directos
                for key, tensor in tensors.items():
                    restored_state[key] = tensor

                # Restaurar referencias
                for key, ref_key in refs.items():
                    if ref_key in tensors:
                        restored_state[key] = tensors[ref_key]

                restored['model_state'] = restored_state

        return restored

    async def _apply_retention_strategy(self, session_id: str) -> None:
        """Aplicar estrategia de retención de checkpoints."""
        if not self.config.auto_cleanup:
            return

        if self.config.strategy == CheckpointStrategy.LAST_N:
            await self.cleanup_checkpoints(session_id, keep_last=self.config.max_checkpoints)
        elif self.config.strategy == CheckpointStrategy.ALL:
            # No hacer nada, mantener todos
            pass
        elif self.config.strategy == CheckpointStrategy.BEST_ONLY:
            # Mantener solo el mejor
            if self.best_checkpoint:
                checkpoint_ids = self.session_checkpoints.get(session_id, [])
                for cid in checkpoint_ids:
                    if cid != self.best_checkpoint:
                        await self.delete_checkpoint(cid)

    async def _update_best_checkpoint(self, checkpoint_id: str, metrics: Dict[str, float]) -> None:
        """Actualizar el mejor checkpoint basado en métricas."""
        if not metrics:
            return

        # Asumir que la métrica principal es 'accuracy' o 'val_accuracy'
        metric_value = metrics.get('val_accuracy', metrics.get('accuracy', 0.0))

        if metric_value > self.best_metric_value:
            self.best_metric_value = metric_value
            self.best_checkpoint = checkpoint_id
            logger.info(f"🏆 Nuevo mejor checkpoint: {checkpoint_id} (métrica: {metric_value:.4f})")

    def _save_checkpoint_sync(self, checkpoint_id: str, data: Dict[str, Any]) -> Tuple[int, str]:
        """Guardar checkpoint de forma síncrona."""
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.pkl"

        if self.config.compression == CompressionType.GZIP:
            with gzip.open(checkpoint_file, 'wb', compresslevel=self.config.compression_level) as f:
                pickle.dump(data, f)
        elif self.config.compression == CompressionType.LZMA:
            with lzma.open(checkpoint_file, 'wb', preset=self.config.compression_level) as f:
                pickle.dump(data, f)
        else:
            with open(checkpoint_file, 'wb') as f:
                pickle.dump(data, f)

        # Calcular tamaño y checksum
        file_size = checkpoint_file.stat().st_size
        checksum = self._calculate_checksum(checkpoint_file)

        return file_size, checksum

    def _load_checkpoint_sync(self, checkpoint_file: Path, opener) -> Dict[str, Any]:
        """Cargar checkpoint de forma síncrona."""
        with opener(checkpoint_file, 'rb') as f:
            return pickle.load(f)

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calcular checksum SHA256 de un archivo."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _tensor_hash(self, tensor: torch.Tensor) -> str:
        """Calcular hash de un tensor."""
        # Convertir a bytes y hashear
        tensor_bytes = tensor.detach().cpu().numpy().tobytes()
        return hashlib.sha256(tensor_bytes).hexdigest()

    def _calculate_tensor_size(self, state_dict: Dict[str, torch.Tensor]) -> int:
        """Calcular tamaño total de un state_dict en bytes."""
        total_size = 0
        for tensor in state_dict.values():
            total_size += tensor.numel() * tensor.element_size()
        return total_size

    def _extract_optimizer_stats(self, optimizer_state: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer estadísticas del optimizador."""
        stats = {}
        if 'state' in optimizer_state:
            # Contar parámetros con estado
            stats['params_with_state'] = len(optimizer_state['state'])
        if 'param_groups' in optimizer_state:
            stats['param_groups'] = len(optimizer_state['param_groups'])
        return stats

    async def _save_metadata(self) -> None:
        """Guardar metadatos de checkpoints."""
        metadata = {
            'checkpoints': {cid: {
                'checkpoint_id': cp.checkpoint_id,
                'session_id': cp.session_id,
                'epoch': cp.epoch,
                'batch': cp.batch,
                'global_step': cp.global_step,
                'timestamp': cp.timestamp,
                'model_size_bytes': cp.model_size_bytes,
                'compressed_size_bytes': cp.compressed_size_bytes,
                'compression_ratio': cp.compression_ratio,
                'checksum': cp.checksum,
                'compression_type': cp.compression_type.value,
                'metrics': cp.metrics,
                'optimizer_stats': cp.optimizer_stats,
                'training_config': cp.training_config,
                'tags': cp.tags
            } for cid, cp in self.checkpoints.items()},
            'session_checkpoints': self.session_checkpoints,
            'best_checkpoint': self.best_checkpoint,
            'best_metric_value': self.best_metric_value,
            'saved_at': time.time()
        }

        def save_sync():
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str)

        await asyncio.get_event_loop().run_in_executor(self.executor, save_sync)

    async def load_metadata(self) -> None:
        """Cargar metadatos de checkpoints."""
        async with await self._get_lock():
            if not self.metadata_file.exists():
                return

            def load_sync():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)

            try:
                data = await asyncio.get_event_loop().run_in_executor(self.executor, load_sync)

                # Restaurar checkpoints
                self.checkpoints = {}
                for cid, cp_data in data.get('checkpoints', {}).items():
                    cp_data['compression_type'] = CompressionType(cp_data['compression_type'])
                    self.checkpoints[cid] = CheckpointMetadata(**cp_data)

                self.session_checkpoints = data.get('session_checkpoints', {})
                self.best_checkpoint = data.get('best_checkpoint')
                self.best_metric_value = data.get('best_metric_value', float('-inf'))

                logger.info(f"📂 Metadatos cargados: {len(self.checkpoints)} checkpoints")

            except Exception as e:
                logger.error(f"❌ Error cargando metadatos: {e}")

    async def __aenter__(self):
        """Context manager entry."""
        await self.load_metadata()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self._save_metadata()
        self.executor.shutdown(wait=True)