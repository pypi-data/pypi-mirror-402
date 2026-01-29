"""
Federated Data Loader - Componente para manejo de datos locales en nodos federados
Implementa carga de datos sin compartirlos, con privacidad y escalabilidad.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
import torch
from pathlib import Path

from ..core.logging import get_logger
from .ipfs_data_loader import IPFSDataLoader
from ..infrastructure.ipfs_embedded import IPFSManager

logger = get_logger(__name__)


@dataclass
class DataLoadConfig:
    """Configuración para carga de datos federados."""
    max_memory_mb: int = 500
    prefetch_workers: int = 4
    cache_enabled: bool = True
    compression_enabled: bool = True
    batch_size: int = 32
    num_workers: int = 2
    pin_important_data: bool = True
    enable_data_augmentation: bool = False


@dataclass
class DataBatch:
    """Lote de datos para entrenamiento."""
    inputs: torch.Tensor
    targets: torch.Tensor
    metadata: Dict[str, Any] = field(default_factory=dict)
    batch_id: str = ""
    node_id: str = ""
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())


class FederatedDataLoader:
    """
    Data loader para nodos federados que mantiene datos locales sin compartirlos.
    Implementa carga eficiente, caching y preprocesamiento con privacidad.
    """

    def __init__(self,
                 node_id: str,
                 ipfs_endpoint: str = "http://localhost:5001/api/v0",
                 config: Optional[DataLoadConfig] = None):
        """
        Inicializar el Federated Data Loader.

        Args:
            node_id: ID único del nodo
            ipfs_endpoint: Endpoint de IPFS
            config: Configuración de carga de datos
        """
        self.node_id = node_id
        self.config = config or DataLoadConfig()

        # Componentes subyacentes
        self.ipfs_manager = IPFSManager(api_endpoint=ipfs_endpoint)
        self.ipfs_loader = IPFSDataLoader(
            ipfs_manager=self.ipfs_manager,
            max_memory_mb=self.config.max_memory_mb,
            prefetch_workers=self.config.prefetch_workers
        )

        # Estado del loader
        self.is_initialized = False
        self.local_data_cids: List[str] = []
        self.data_metadata: Dict[str, Any] = {}
        self.current_epoch = 0
        self.total_samples = 0

        # Estadísticas
        self.stats = {
            'batches_loaded': 0,
            'samples_processed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'load_time_ms': 0,
            'errors': 0
        }

        logger.info(f"🚀 FederatedDataLoader initialized for node {node_id}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.shutdown()

    async def initialize(self):
        """Inicializar componentes."""
        try:
            await self.ipfs_manager.start()
            await self.ipfs_loader.start()
            self.is_initialized = True
            logger.info(f"✅ FederatedDataLoader initialized for node {self.node_id}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize FederatedDataLoader: {e}")
            raise

    async def shutdown(self):
        """Apagar componentes."""
        try:
            await self.ipfs_loader.stop()
            await self.ipfs_manager.stop()
            logger.info(f"🛑 FederatedDataLoader shutdown for node {self.node_id}")
        except Exception as e:
            logger.error(f"❌ Error shutting down FederatedDataLoader: {e}")

    async def load_local_dataset(self, data_cids: List[str],
                               metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Cargar dataset local desde CIDs de IPFS.

        Args:
            data_cids: Lista de CIDs de datos
            metadata: Metadatos del dataset

        Returns:
            True si carga exitosa
        """
        try:
            self.local_data_cids = data_cids.copy()
            self.data_metadata = metadata or {}

            # Verificar disponibilidad de datos
            available_cids = []
            for cid in data_cids:
                try:
                    # Verificar que el CID existe (sin cargar datos completos)
                    await self.ipfs_manager.get_data_size(cid)
                    available_cids.append(cid)
                except Exception as e:
                    logger.warning(f"⚠️ CID {cid} not available: {e}")

            if not available_cids:
                raise ValueError("No data CIDs available for loading")

            self.local_data_cids = available_cids

            # Precargar datos importantes si está habilitado
            if self.config.pin_important_data:
                await self._pin_important_data()

            # Calcular estadísticas del dataset
            await self._calculate_dataset_stats()

            logger.info(f"✅ Loaded local dataset with {len(self.local_data_cids)} chunks for node {self.node_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to load local dataset: {e}")
            self.stats['errors'] += 1
            return False

    async def _pin_important_data(self):
        """Pinnear datos importantes para asegurar disponibilidad."""
        try:
            # Pinnear primeros y últimos chunks (más críticos)
            cids_to_pin = []
            if self.local_data_cids:
                cids_to_pin.append(self.local_data_cids[0])  # Primer chunk
                if len(self.local_data_cids) > 1:
                    cids_to_pin.append(self.local_data_cids[-1])  # Último chunk

            for cid in cids_to_pin:
                await self.ipfs_manager.pin_cid(cid)
                logger.debug(f"📌 Pinned important CID: {cid}")

        except Exception as e:
            logger.warning(f"⚠️ Failed to pin important data: {e}")

    async def _calculate_dataset_stats(self):
        """Calcular estadísticas del dataset."""
        try:
            total_size = 0
            for cid in self.local_data_cids:
                size = await self.ipfs_manager.get_data_size(cid)
                total_size += size

            self.total_samples = len(self.local_data_cids)  # Estimación simplificada
            self.data_metadata['total_size_bytes'] = total_size
            self.data_metadata['num_chunks'] = len(self.local_data_cids)

            logger.info(f"📊 Dataset stats: {self.total_samples} samples, {total_size} bytes")

        except Exception as e:
            logger.warning(f"⚠️ Failed to calculate dataset stats: {e}")

    async def get_next_batch(self) -> Optional[DataBatch]:
        """
        Obtener siguiente lote de datos para entrenamiento.

        Returns:
            DataBatch o None si no hay más datos
        """
        try:
            start_time = datetime.now()

            # Seleccionar CID para este batch (round-robin simplificado)
            if not self.local_data_cids:
                return None

            cid_index = self.stats['batches_loaded'] % len(self.local_data_cids)
            cid = self.local_data_cids[cid_index]

            # Cargar datos del CID
            data_bytes = await self.ipfs_loader.load_data(cid)

            # Procesar datos (simplificado - en producción sería más complejo)
            inputs, targets = self._process_raw_data(data_bytes, cid)

            # Crear batch
            batch = DataBatch(
                inputs=inputs,
                targets=targets,
                batch_id=f"batch_{self.node_id}_{self.stats['batches_loaded']}",
                node_id=self.node_id,
                metadata={
                    'cid': cid,
                    'epoch': self.current_epoch,
                    'batch_index': self.stats['batches_loaded']
                }
            )

            # Actualizar estadísticas
            self.stats['batches_loaded'] += 1
            self.stats['samples_processed'] += inputs.size(0)
            load_time = (datetime.now() - start_time).total_seconds() * 1000
            self.stats['load_time_ms'] += load_time

            logger.debug(f"📦 Loaded batch {batch.batch_id} in {load_time:.2f}ms")
            return batch

        except Exception as e:
            logger.error(f"❌ Failed to get next batch: {e}")
            self.stats['errors'] += 1
            return None

    def _process_raw_data(self, data_bytes: bytes, cid: str) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Procesar datos crudos en tensores (implementación simplificada).

        Args:
            data_bytes: Datos crudos
            cid: CID de origen

        Returns:
            Tuple de (inputs, targets)
        """
        try:
            # En una implementación real, esto parsearía el formato específico de datos
            # Aquí simulamos con datos aleatorios para fines de ejemplo

            # Simular datos de imagen (28x28) o texto tokenizado
            if len(data_bytes) > 1000:  # Asumir datos de imagen
                # Simular batch de imágenes MNIST
                batch_size = min(self.config.batch_size, 64)  # Limitar para memoria
                inputs = torch.randn(batch_size, 1, 28, 28)
                targets = torch.randint(0, 10, (batch_size,))
            else:
                # Simular datos de texto
                seq_length = 128
                vocab_size = 50000
                batch_size = min(self.config.batch_size, 32)
                inputs = torch.randint(0, vocab_size, (batch_size, seq_length))
                targets = torch.randint(0, vocab_size, (batch_size, seq_length))

            return inputs, targets

        except Exception as e:
            logger.error(f"❌ Failed to process raw data from {cid}: {e}")
            # Fallback: datos dummy
            return torch.zeros(self.config.batch_size, 10), torch.zeros(self.config.batch_size, dtype=torch.long)

    def reset_epoch(self):
        """Resetear para nueva época."""
        self.current_epoch += 1
        self.stats['batches_loaded'] = 0
        logger.info(f"🔄 Reset for epoch {self.current_epoch}")

    async def prefetch_data(self, cids: List[str]):
        """
        Precargar datos en background.

        Args:
            cids: CIDs a precargar
        """
        try:
            await self.ipfs_loader.prefetch_cids(cids)
            logger.debug(f"🚀 Prefetched {len(cids)} CIDs")
        except Exception as e:
            logger.warning(f"⚠️ Failed to prefetch data: {e}")

    def get_loader_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del loader.

        Returns:
            Diccionario con estadísticas
        """
        cache_stats = self.ipfs_loader.get_cache_stats()

        return {
            'node_id': self.node_id,
            'is_initialized': self.is_initialized,
            'current_epoch': self.current_epoch,
            'total_samples': self.total_samples,
            'data_chunks': len(self.local_data_cids),
            'data_metadata': self.data_metadata.copy(),
            'loader_stats': self.stats.copy(),
            'cache_stats': cache_stats,
            'config': {
                'max_memory_mb': self.config.max_memory_mb,
                'prefetch_workers': self.config.prefetch_workers,
                'batch_size': self.config.batch_size
            }
        }

    def clear_cache(self):
        """Limpiar cache de datos."""
        self.ipfs_loader.clear_cache()
        logger.info("🧹 Cache cleared")

    async def verify_data_integrity(self) -> Dict[str, Any]:
        """
        Verificar integridad de datos locales.

        Returns:
            Resultado de verificación
        """
        try:
            verification_results = {}
            for cid in self.local_data_cids:
                try:
                    # Verificar que podemos cargar el dato
                    data = await self.ipfs_loader.load_data(cid)
                    verification_results[cid] = {
                        'available': True,
                        'size': len(data),
                        'error': None
                    }
                except Exception as e:
                    verification_results[cid] = {
                        'available': False,
                        'size': 0,
                        'error': str(e)
                    }

            total_available = sum(1 for r in verification_results.values() if r['available'])
            success_rate = total_available / len(self.local_data_cids) if self.local_data_cids else 0

            return {
                'success': success_rate > 0.8,  # 80% threshold
                'total_chunks': len(self.local_data_cids),
                'available_chunks': total_available,
                'success_rate': success_rate,
                'details': verification_results
            }

        except Exception as e:
            logger.error(f"❌ Data integrity verification failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }