"""
DatasetManager - Gestión local de datasets en nodos
====================================================

Componente para gestionar datasets descargados localmente en nodos,
incluyendo cache inteligente, limpieza automática y optimización de almacenamiento.
"""

import asyncio
import json
import logging
import shutil
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import aiofiles
import os

from ..core.logging import get_logger
from .registry import DatasetRegistry
from .downloader import DatasetDownloader
from .validator import DatasetValidator
from .models import Dataset

logger = get_logger(__name__)


class CacheConfig:
    """Configuración de cache para DatasetManager."""
    def __init__(self,
                 max_cache_size_gb: float = 10.0,
                 cache_dir: str = "./datahub_cache",
                 cleanup_interval_hours: int = 24,
                 max_age_days: int = 30,
                 min_free_space_gb: float = 2.0,
                 enable_compression: bool = True):
        self.max_cache_size_gb = max_cache_size_gb
        self.cache_dir = Path(cache_dir)
        self.cleanup_interval_hours = cleanup_interval_hours
        self.max_age_days = max_age_days
        self.min_free_space_gb = min_free_space_gb
        self.enable_compression = enable_compression


class DatasetManager:
    """
    Gestor de datasets locales para nodos DataHub.

    Maneja el almacenamiento local, cache inteligente, limpieza automática
    y optimización del uso de disco para datasets descargados.
    """

    def __init__(self,
                 registry: DatasetRegistry,
                 downloader: DatasetDownloader,
                 validator: Optional[DatasetValidator] = None,
                 config: Optional[CacheConfig] = None,
                 node_id: Optional[str] = None):
        """
        Inicializar el DatasetManager.

        Args:
            registry: Registro de datasets
            downloader: Descargador de datasets
            validator: Validador de datasets (opcional)
            config: Configuración de cache
            node_id: ID del nodo local
        """
        self.registry = registry
        self.downloader = downloader
        self.validator = validator
        self.config = config or CacheConfig()
        self.node_id = node_id or f"node_{hash(str(datetime.now()))}"

        # Estado del manager
        self.cache_dir = self.config.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Metadata de cache
        self.cache_metadata: Dict[str, Dict[str, Any]] = {}
        self._load_cache_metadata()

        # Tarea de limpieza automática
        self.cleanup_task: Optional[asyncio.Task] = None
        self.last_cleanup = datetime.now()

        # Estadísticas
        self.stats = {
            'total_datasets_cached': 0,
            'cache_size_bytes': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'downloads_initiated': 0,
            'cleanups_performed': 0,
            'space_saved_bytes': 0
        }

        logger.info(f"🚀 DatasetManager initialized for node {self.node_id}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()

    async def start(self):
        """Iniciar el DatasetManager."""
        # Iniciar limpieza automática
        self.cleanup_task = asyncio.create_task(self._auto_cleanup_loop())
        logger.info("✅ DatasetManager started")

    async def stop(self):
        """Detener el DatasetManager."""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        await self._save_cache_metadata()
        logger.info("🛑 DatasetManager stopped")

    async def get_dataset(self,
                         dataset_id: int,
                         validate: bool = True,
                         use_cache: bool = True) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Obtener un dataset localmente, descargándolo si es necesario.

        Args:
            dataset_id: ID del dataset
            validate: Si validar el dataset después de obtenerlo
            use_cache: Si usar cache local

        Returns:
            Tuple de (ruta_local, metadata)
        """
        try:
            dataset = self.registry.get_dataset(dataset_id)
            if not dataset:
                return None, {'error': 'Dataset not found in registry'}

            # Verificar si está en cache
            if use_cache:
                cached_path = self._get_cached_path(dataset)
                if cached_path and cached_path.exists():
                    # Verificar que el cache es válido
                    if self._is_cache_valid(dataset, cached_path):
                        self.stats['cache_hits'] += 1
                        metadata = {
                            'source': 'cache',
                            'path': str(cached_path),
                            'size_bytes': cached_path.stat().st_size,
                            'cached_at': self.cache_metadata.get(str(dataset_id), {}).get('cached_at')
                        }

                        # Actualizar acceso al cache
                        self._update_cache_access(dataset_id)

                        if validate and self.validator:
                            # Validación rápida (solo integridad)
                            validation = await self.validator.validate_dataset(
                                dataset_id, str(cached_path)
                            )
                            if not validation.is_integrity_valid:
                                logger.warning(f"⚠️ Cached dataset {dataset_id} failed integrity check, re-downloading")
                                cached_path.unlink()
                            else:
                                return str(cached_path), metadata

            # No está en cache o cache inválido - descargar
            self.stats['cache_misses'] += 1
            self.stats['downloads_initiated'] += 1

            download_path = self._get_download_path(dataset)
            download_result = await self.downloader.download_dataset(
                dataset_id, str(download_path), node_id=self.node_id
            )

            if not download_result['success']:
                return None, {'error': download_result.get('error', 'Download failed')}

            # Validar si se solicita
            if validate and self.validator:
                validation = await self.validator.validate_dataset(
                    dataset_id, str(download_path)
                )
                if not validation.is_integrity_valid:
                    download_path.unlink()
                    return None, {'error': 'Dataset integrity validation failed'}

            # Añadir a cache si es exitoso
            if use_cache:
                await self._add_to_cache(dataset_id, download_path)

            metadata = {
                'source': 'download',
                'path': str(download_path),
                'size_bytes': download_path.stat().st_size,
                'downloaded_at': download_result.get('duration_ms', 0)
            }

            return str(download_path), metadata

        except Exception as e:
            logger.error(f"❌ Failed to get dataset {dataset_id}: {e}")
            return None, {'error': str(e)}

    async def prefetch_datasets(self, dataset_ids: List[int], priority: str = 'normal'):
        """
        Prefetchear múltiples datasets en background.

        Args:
            dataset_ids: IDs de datasets a prefetchear
            priority: Prioridad ('low', 'normal', 'high')
        """
        try:
            logger.info(f"🚀 Starting prefetch of {len(dataset_ids)} datasets with {priority} priority")

            # Limitar concurrencia basada en prioridad
            semaphore_limits = {'low': 2, 'normal': 3, 'high': 5}
            semaphore = asyncio.Semaphore(semaphore_limits.get(priority, 3))

            async def prefetch_single(dataset_id: int):
                async with semaphore:
                    try:
                        dataset = self.registry.get_dataset(dataset_id)
                        if not dataset:
                            return

                        cached_path = self._get_cached_path(dataset)
                        if cached_path and cached_path.exists():
                            return  # Ya está en cache

                        # Descargar sin validación para prefetch
                        download_path = self._get_download_path(dataset)
                        result = await self.downloader.download_dataset(
                            dataset_id, str(download_path), node_id=self.node_id
                        )

                        if result['success']:
                            await self._add_to_cache(dataset_id, download_path)

                    except Exception as e:
                        logger.debug(f"⚠️ Prefetch failed for dataset {dataset_id}: {e}")

            # Ejecutar prefetch en paralelo
            tasks = [prefetch_single(did) for did in dataset_ids]
            await asyncio.gather(*tasks, return_exceptions=True)

            logger.info(f"✅ Prefetch completed for {len(dataset_ids)} datasets")

        except Exception as e:
            logger.error(f"❌ Prefetch failed: {e}")

    def get_cache_info(self, dataset_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtener información del cache.

        Args:
            dataset_id: ID específico de dataset o None para info general

        Returns:
            Información del cache
        """
        if dataset_id is not None:
            cache_info = self.cache_metadata.get(str(dataset_id))
            if cache_info:
                cached_path = self._get_cached_path_from_id(dataset_id)
                return {
                    'dataset_id': dataset_id,
                    'cached': cached_path.exists() if cached_path else False,
                    'path': str(cached_path) if cached_path else None,
                    'size_bytes': cached_path.stat().st_size if cached_path and cached_path.exists() else 0,
                    'cached_at': cache_info.get('cached_at'),
                    'last_accessed': cache_info.get('last_accessed'),
                    'access_count': cache_info.get('access_count', 0)
                }
            return {'dataset_id': dataset_id, 'cached': False}

        # Información general del cache
        total_size = sum(
            self._get_cached_path_from_id(int(did)).stat().st_size
            for did, info in self.cache_metadata.items()
            if self._get_cached_path_from_id(int(did)).exists()
        )

        return {
            'total_datasets_cached': len(self.cache_metadata),
            'cache_size_bytes': total_size,
            'cache_size_gb': total_size / (1024**3),
            'max_cache_size_gb': self.config.max_cache_size_gb,
            'cache_utilization': total_size / (self.config.max_cache_size_gb * 1024**3),
            'cache_dir': str(self.cache_dir),
            'last_cleanup': self.last_cleanup.isoformat()
        }

    async def cleanup_cache(self,
                           max_age_days: Optional[int] = None,
                           force: bool = False) -> Dict[str, Any]:
        """
        Limpiar cache eliminando datasets antiguos o para liberar espacio.

        Args:
            max_age_days: Máxima edad en días (usa config si None)
            force: Forzar limpieza incluso si no es necesario

        Returns:
            Resultado de la limpieza
        """
        try:
            max_age = max_age_days or self.config.max_age_days
            cutoff_date = datetime.now() - timedelta(days=max_age)

            cleaned_datasets = []
            space_freed = 0

            # Identificar datasets a limpiar
            for dataset_id_str, metadata in list(self.cache_metadata.items()):
                dataset_id = int(dataset_id_str)
                cached_path = self._get_cached_path_from_id(dataset_id)

                should_clean = force

                if not should_clean:
                    # Verificar edad
                    cached_at = metadata.get('cached_at')
                    if cached_at and isinstance(cached_at, str):
                        cached_at = datetime.fromisoformat(cached_at)

                    if cached_at and cached_at < cutoff_date:
                        should_clean = True

                # Verificar espacio si es necesario
                if not should_clean and not force:
                    current_usage = self.get_cache_info()['cache_utilization']
                    if current_usage > 0.9:  # >90% uso
                        # Limpiar menos accedidos primero
                        last_accessed = metadata.get('last_accessed')
                        if last_accessed and isinstance(last_accessed, str):
                            last_accessed = datetime.fromisoformat(last_accessed)

                        # Datasets no accedidos en la última semana
                        if last_accessed and (datetime.now() - last_accessed).days > 7:
                            should_clean = True

                if should_clean and cached_path.exists():
                    size = cached_path.stat().st_size
                    cached_path.unlink()
                    del self.cache_metadata[dataset_id_str]

                    cleaned_datasets.append(dataset_id)
                    space_freed += size

            # Actualizar estadísticas
            self.stats['cleanups_performed'] += 1
            self.stats['space_saved_bytes'] += space_freed
            self.last_cleanup = datetime.now()

            await self._save_cache_metadata()

            result = {
                'success': True,
                'datasets_cleaned': len(cleaned_datasets),
                'space_freed_bytes': space_freed,
                'space_freed_gb': space_freed / (1024**3),
                'remaining_datasets': len(self.cache_metadata)
            }

            logger.info(f"🧹 Cache cleanup completed: {result}")
            return result

        except Exception as e:
            logger.error(f"❌ Cache cleanup failed: {e}")
            return {'success': False, 'error': str(e)}

    def clear_cache(self, dataset_id: Optional[int] = None) -> bool:
        """
        Limpiar cache completamente o para un dataset específico.

        Args:
            dataset_id: ID del dataset o None para limpiar todo

        Returns:
            True si exitoso
        """
        try:
            if dataset_id is not None:
                # Limpiar cache para un dataset específico
                cached_path = self._get_cached_path_from_id(dataset_id)
                if cached_path.exists():
                    size = cached_path.stat().st_size
                    cached_path.unlink()
                    self.cache_metadata.pop(str(dataset_id), None)
                    self.stats['space_saved_bytes'] += size
                    logger.info(f"🗑️ Cleared cache for dataset {dataset_id}")
            else:
                # Limpiar todo el cache
                total_size = 0
                for dataset_id_str in list(self.cache_metadata.keys()):
                    cached_path = self._get_cached_path_from_id(int(dataset_id_str))
                    if cached_path.exists():
                        total_size += cached_path.stat().st_size
                        cached_path.unlink()
                    self.cache_metadata.pop(dataset_id_str, None)

                self.stats['space_saved_bytes'] += total_size
                logger.info(f"🗑️ Cleared entire cache ({total_size} bytes)")

            asyncio.create_task(self._save_cache_metadata())
            return True

        except Exception as e:
            logger.error(f"❌ Failed to clear cache: {e}")
            return False

    def get_manager_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del DatasetManager."""
        cache_info = self.get_cache_info()

        return {
            'node_id': self.node_id,
            'cache_info': cache_info,
            'performance': {
                'cache_hit_rate': (self.stats['cache_hits'] /
                                 max(1, self.stats['cache_hits'] + self.stats['cache_misses'])),
                'total_requests': self.stats['cache_hits'] + self.stats['cache_misses'],
                'downloads_initiated': self.stats['downloads_initiated']
            },
            'maintenance': {
                'last_cleanup': self.last_cleanup.isoformat(),
                'cleanups_performed': self.stats['cleanups_performed'],
                'space_saved_bytes': self.stats['space_saved_bytes']
            },
            'config': {
                'max_cache_size_gb': self.config.max_cache_size_gb,
                'max_age_days': self.config.max_age_days,
                'cleanup_interval_hours': self.config.cleanup_interval_hours
            }
        }

    # Métodos privados

    def _get_cached_path(self, dataset: Dataset) -> Path:
        """Obtener ruta del archivo en cache."""
        return self.cache_dir / f"dataset_{dataset.id}_{dataset.sha256_hash[:8]}.{dataset.format}"

    def _get_cached_path_from_id(self, dataset_id: int) -> Path:
        """Obtener ruta del cache por ID (necesita buscar en metadata)."""
        metadata = self.cache_metadata.get(str(dataset_id))
        if metadata and metadata.get('filename'):
            return self.cache_dir / metadata['filename']

        # Fallback: buscar archivos que coincidan con el patrón
        pattern = f"dataset_{dataset_id}_*.{{}}"
        for ext in ['csv', 'json', 'parquet', 'zip', 'tar.gz']:
            candidates = list(self.cache_dir.glob(pattern.format(ext)))
            if candidates:
                return candidates[0]

        return self.cache_dir / f"dataset_{dataset_id}_unknown"

    def _get_download_path(self, dataset: Dataset) -> Path:
        """Obtener ruta para descarga temporal."""
        return self.cache_dir / f"download_{dataset.id}_{hash(str(datetime.now()))}.{dataset.format}"

    def _is_cache_valid(self, dataset: Dataset, cached_path: Path) -> bool:
        """Verificar si el cache es válido."""
        try:
            if not cached_path.exists():
                return False

            # Verificar tamaño aproximado (con tolerancia para compresión)
            actual_size = cached_path.stat().st_size
            expected_size = dataset.file_size_bytes

            # Tolerancia del 10% para posibles diferencias de compresión/metadata
            size_tolerance = 0.1
            if abs(actual_size - expected_size) / expected_size > size_tolerance:
                logger.debug(f"⚠️ Cache size mismatch for dataset {dataset.id}: {actual_size} vs {expected_size}")
                return False

            # Verificar que no es demasiado antiguo (comparado con la config)
            metadata = self.cache_metadata.get(str(dataset.id))
            if metadata:
                cached_at = metadata.get('cached_at')
                if cached_at:
                    if isinstance(cached_at, str):
                        cached_at = datetime.fromisoformat(cached_at)
                    if (datetime.now() - cached_at).days > self.config.max_age_days:
                        return False

            return True

        except Exception as e:
            logger.debug(f"⚠️ Cache validation failed for dataset {dataset.id}: {e}")
            return False

    async def _add_to_cache(self, dataset_id: int, source_path: Path):
        """Añadir archivo descargado al cache."""
        try:
            dataset = self.registry.get_dataset(dataset_id)
            if not dataset:
                return

            # Verificar espacio disponible antes de copiar
            if not self._has_space_for_file(source_path.stat().st_size):
                await self.cleanup_cache(force=True)

            cached_path = self._get_cached_path(dataset)

            # Copiar al cache
            if source_path != cached_path:
                await asyncio.get_event_loop().run_in_executor(
                    None, shutil.copy2, str(source_path), str(cached_path)
                )

            # Actualizar metadata del cache
            self.cache_metadata[str(dataset_id)] = {
                'filename': cached_path.name,
                'cached_at': datetime.now().isoformat(),
                'last_accessed': datetime.now().isoformat(),
                'access_count': 1,
                'size_bytes': cached_path.stat().st_size,
                'dataset_sha256': dataset.sha256_hash
            }

            self.stats['total_datasets_cached'] += 1
            await self._save_cache_metadata()

            logger.debug(f"📦 Added dataset {dataset_id} to cache")

        except Exception as e:
            logger.error(f"❌ Failed to add dataset {dataset_id} to cache: {e}")

    def _update_cache_access(self, dataset_id: int):
        """Actualizar metadata de acceso al cache."""
        metadata = self.cache_metadata.get(str(dataset_id))
        if metadata:
            metadata['last_accessed'] = datetime.now().isoformat()
            metadata['access_count'] = metadata.get('access_count', 0) + 1

    def _has_space_for_file(self, file_size_bytes: int) -> bool:
        """Verificar si hay espacio para el archivo en cache."""
        try:
            # Obtener espacio disponible en disco
            stat = os.statvfs(self.cache_dir)
            free_bytes = stat.f_bavail * stat.f_frsize

            # Verificar límite de espacio libre mínimo
            min_free_bytes = self.config.min_free_space_gb * 1024**3
            if free_bytes - file_size_bytes < min_free_bytes:
                return False

            # Verificar límite de tamaño del cache
            current_cache_size = self.get_cache_info()['cache_size_bytes']
            max_cache_bytes = self.config.max_cache_size_gb * 1024**3

            return current_cache_size + file_size_bytes <= max_cache_bytes

        except Exception as e:
            logger.warning(f"⚠️ Could not check disk space: {e}")
            return True  # Permitir por defecto si no se puede verificar

    async def _auto_cleanup_loop(self):
        """Loop de limpieza automática."""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval_hours * 3600)

                # Verificar si necesita limpieza
                cache_info = self.get_cache_info()
                utilization = cache_info['cache_utilization']

                if utilization > 0.8:  # >80% uso
                    logger.info(f"🧹 Auto cleanup triggered (utilization: {utilization:.2f})")
                    await self.cleanup_cache()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Auto cleanup failed: {e}")

    def _load_cache_metadata(self):
        """Cargar metadata del cache desde disco."""
        try:
            metadata_file = self.cache_dir / "cache_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    self.cache_metadata = json.load(f)

                # Convertir timestamps string a datetime si es necesario
                for metadata in self.cache_metadata.values():
                    for key in ['cached_at', 'last_accessed']:
                        if key in metadata and isinstance(metadata[key], str):
                            # Ya están como ISO strings, se convertirán cuando se necesiten
                            pass

                logger.debug(f"📋 Loaded cache metadata for {len(self.cache_metadata)} datasets")

        except Exception as e:
            logger.warning(f"⚠️ Failed to load cache metadata: {e}")
            self.cache_metadata = {}

    async def _save_cache_metadata(self):
        """Guardar metadata del cache en disco."""
        try:
            metadata_file = self.cache_dir / "cache_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(self.cache_metadata, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Failed to save cache metadata: {e}")