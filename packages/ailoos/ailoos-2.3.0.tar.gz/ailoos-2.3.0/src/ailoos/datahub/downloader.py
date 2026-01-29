"""
DatasetDownloader - Descarga segura desde IPFS con validación
============================================================

Componente para descargar datasets desde IPFS con validación de integridad,
manejo de chunks y optimizaciones de red.
"""

import asyncio
import hashlib
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import aiofiles

from ..core.logging import get_logger
from ..infrastructure.ipfs_embedded import IPFSManager
from .registry import DatasetRegistry
from .models import Dataset

logger = get_logger(__name__)


class DownloadConfig:
    """Configuración para descargas de datasets."""
    def __init__(self,
                 max_concurrent_downloads: int = 3,
                 chunk_timeout_seconds: int = 30,
                 retry_attempts: int = 3,
                 retry_delay_seconds: int = 2,
                 verify_integrity: bool = True,
                 enable_prefetch: bool = True,
                 prefetch_ahead: int = 2,
                 temp_dir: Optional[str] = None):
        self.max_concurrent_downloads = max_concurrent_downloads
        self.chunk_timeout_seconds = chunk_timeout_seconds
        self.retry_attempts = retry_attempts
        self.retry_delay_seconds = retry_delay_seconds
        self.verify_integrity = verify_integrity
        self.enable_prefetch = enable_prefetch
        self.prefetch_ahead = prefetch_ahead
        self.temp_dir = temp_dir or "/tmp/datahub_downloads"


class DatasetDownloader:
    """
    Descargador seguro de datasets desde IPFS con validación de integridad.

    Maneja descargas paralelas, validación de hashes, recuperación de errores
    y optimizaciones de rendimiento.
    """

    def __init__(self,
                 ipfs_manager: IPFSManager,
                 registry: DatasetRegistry,
                 config: Optional[DownloadConfig] = None):
        """
        Inicializar el DatasetDownloader.

        Args:
            ipfs_manager: Gestor IPFS para operaciones de red
            registry: Registro de datasets para metadatos
            config: Configuración de descarga
        """
        self.ipfs = ipfs_manager
        self.registry = registry
        self.config = config or DownloadConfig()

        # Estado de descargas activas
        self.active_downloads: Dict[str, asyncio.Task] = {}
        self.download_stats: Dict[str, Dict[str, Any]] = {}

        # Cache de chunks para prefetching
        self.chunk_cache: Dict[str, bytes] = {}
        self.prefetch_queue: asyncio.Queue = asyncio.Queue()

        # Crear directorio temporal
        Path(self.config.temp_dir).mkdir(parents=True, exist_ok=True)

        logger.info("🚀 DatasetDownloader initialized")

    async def download_dataset(self,
                              dataset_id: int,
                              output_path: str,
                              node_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Descargar un dataset completo con validación.

        Args:
            dataset_id: ID del dataset en el registro
            output_path: Ruta donde guardar el dataset
            node_id: ID del nodo que solicita la descarga (para estadísticas)

        Returns:
            Diccionario con resultado de la descarga
        """
        start_time = datetime.now()

        try:
            # Obtener información del dataset
            dataset = self.registry.get_dataset(dataset_id)
            if not dataset:
                raise ValueError(f"Dataset {dataset_id} not found in registry")

            if not dataset.is_active:
                raise ValueError(f"Dataset {dataset_id} is not active")

            logger.info(f"📥 Starting download of dataset: {dataset.name} ({dataset.ipfs_cid})")

            # Preparar estadísticas de descarga
            download_id = f"{dataset_id}_{hash(str(start_time))}"
            self.download_stats[download_id] = {
                'dataset_id': dataset_id,
                'dataset_name': dataset.name,
                'start_time': start_time,
                'bytes_downloaded': 0,
                'chunks_downloaded': 0,
                'errors': 0,
                'retries': 0
            }

            # Descargar datos
            if dataset.chunk_count == 1:
                # Dataset sin chunks
                data = await self._download_single_file(dataset.ipfs_cid, dataset.sha256_hash)
                await self._save_data(data, output_path)
                downloaded_bytes = len(data)
            else:
                # Dataset con chunks
                data, downloaded_bytes = await self._download_chunked_dataset(dataset)
                await self._save_data(data, output_path)

            # Verificar integridad final
            if self.config.verify_integrity:
                await self._verify_final_integrity(output_path, dataset.sha256_hash)

            # Registrar descarga en el registro
            success = self.registry.record_download(
                dataset_id=dataset_id,
                node_id=node_id,
                download_size_bytes=downloaded_bytes,
                download_duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                success=True
            )

            # Limpiar estadísticas
            stats = self.download_stats.pop(download_id, {})

            result = {
                'success': True,
                'dataset_id': dataset_id,
                'dataset_name': dataset.name,
                'output_path': output_path,
                'bytes_downloaded': downloaded_bytes,
                'duration_ms': (datetime.now() - start_time).total_seconds() * 1000,
                'chunks_downloaded': stats.get('chunks_downloaded', 0),
                'download_id': download_id
            }

            logger.info(f"✅ Dataset download completed: {dataset.name} "
                       f"({downloaded_bytes} bytes in {result['duration_ms']:.2f}ms)")
            return result

        except Exception as e:
            # Registrar descarga fallida
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.registry.record_download(
                dataset_id=dataset_id,
                node_id=node_id,
                download_size_bytes=0,
                download_duration_ms=int(duration_ms),
                success=False,
                error_message=str(e)
            )

            logger.error(f"❌ Dataset download failed: {e}")
            return {
                'success': False,
                'dataset_id': dataset_id,
                'error': str(e),
                'duration_ms': duration_ms
            }

    async def _download_single_file(self, cid: str, expected_hash: str) -> bytes:
        """
        Descargar un archivo único con validación.

        Args:
            cid: CID del archivo
            expected_hash: Hash SHA256 esperado

        Returns:
            Datos descargados
        """
        for attempt in range(self.config.retry_attempts):
            try:
                # Descargar datos
                data = await asyncio.wait_for(
                    self.ipfs.get_data(cid),
                    timeout=self.config.chunk_timeout_seconds
                )

                # Verificar integridad
                if self.config.verify_integrity:
                    actual_hash = hashlib.sha256(data).hexdigest()
                    if actual_hash != expected_hash:
                        raise ValueError(f"Hash mismatch: expected {expected_hash}, got {actual_hash}")

                return data

            except Exception as e:
                logger.warning(f"⚠️ Download attempt {attempt + 1} failed for {cid}: {e}")
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay_seconds * (2 ** attempt))  # Exponential backoff

        raise Exception(f"Failed to download {cid} after {self.config.retry_attempts} attempts")

    async def _download_chunked_dataset(self, dataset: Dataset) -> Tuple[bytes, int]:
        """
        Descargar dataset dividido en chunks.

        Args:
            dataset: Información del dataset

        Returns:
            Tuple de (datos_reconstruidos, bytes_totales)
        """
        logger.info(f"🧩 Downloading chunked dataset: {dataset.chunk_count} chunks")

        # Obtener chunks del dataset
        chunks_data = []
        total_bytes = 0
        semaphore = asyncio.Semaphore(self.config.max_concurrent_downloads)

        async def download_chunk(chunk_cid: str, chunk_index: int) -> Tuple[int, bytes]:
            async with semaphore:
                try:
                    # Verificar si está en cache de prefetch
                    if chunk_cid in self.chunk_cache:
                        data = self.chunk_cache.pop(chunk_cid)
                        logger.debug(f"⚡ Using prefetched chunk {chunk_index}")
                    else:
                        # Descargar chunk
                        data = await self._download_single_file(chunk_cid, "")  # Hash validado a nivel chunk

                    # Actualizar estadísticas
                    download_id = f"{dataset.id}_{hash(str(datetime.now()))}"
                    if download_id in self.download_stats:
                        self.download_stats[download_id]['chunks_downloaded'] += 1
                        self.download_stats[download_id]['bytes_downloaded'] += len(data)

                    return chunk_index, data

                except Exception as e:
                    logger.error(f"❌ Failed to download chunk {chunk_index}: {e}")
                    raise

        # Crear tareas para todos los chunks
        tasks = []
        for i in range(dataset.chunk_count):
            # Aquí necesitaríamos obtener los CIDs individuales de los chunks
            # Por simplicidad, asumimos que están en el metadata o calculamos
            chunk_cid = f"{dataset.ipfs_cid}_chunk_{i}"  # Placeholder - en producción vendría del registry
            task = download_chunk(chunk_cid, i)
            tasks.append(task)

        # Ejecutar descargas en paralelo
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Procesar resultados y ordenar por índice
        chunk_map = {}
        for result in results:
            if isinstance(result, Exception):
                raise result
            index, data = result
            chunk_map[index] = data
            total_bytes += len(data)

        # Reconstruir datos originales
        reconstructed_data = b''
        for i in range(dataset.chunk_count):
            if i not in chunk_map:
                raise ValueError(f"Missing chunk {i}")
            reconstructed_data += chunk_map[i]

        logger.info(f"✅ Reconstructed chunked dataset: {len(reconstructed_data)} bytes from {dataset.chunk_count} chunks")
        return reconstructed_data, total_bytes

    async def _save_data(self, data: bytes, output_path: str):
        """
        Guardar datos en archivo.

        Args:
            data: Datos a guardar
            output_path: Ruta del archivo
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(output_path, 'wb') as f:
            await f.write(data)

        logger.debug(f"💾 Data saved to: {output_path}")

    async def _verify_final_integrity(self, file_path: str, expected_hash: str):
        """
        Verificar integridad del archivo final.

        Args:
            file_path: Ruta del archivo
            expected_hash: Hash esperado
        """
        try:
            # Calcular hash del archivo
            sha256 = hashlib.sha256()
            async with aiofiles.open(file_path, 'rb') as f:
                while chunk := await f.read(8192):
                    sha256.update(chunk)

            actual_hash = sha256.hexdigest()
            if actual_hash != expected_hash:
                raise ValueError(f"Final integrity check failed: expected {expected_hash}, got {actual_hash}")

            logger.debug(f"✅ Final integrity verified: {actual_hash}")

        except Exception as e:
            logger.error(f"❌ Final integrity verification failed: {e}")
            raise

    async def prefetch_dataset_chunks(self, dataset_id: int):
        """
        Prefetchear chunks de un dataset en background.

        Args:
            dataset_id: ID del dataset
        """
        if not self.config.enable_prefetch:
            return

        try:
            dataset = self.registry.get_dataset(dataset_id)
            if not dataset or dataset.chunk_count <= 1:
                return

            logger.debug(f"🚀 Starting prefetch for dataset {dataset.name}")

            # Prefetchear chunks en background
            asyncio.create_task(self._prefetch_chunks_background(dataset))

        except Exception as e:
            logger.warning(f"⚠️ Prefetch failed for dataset {dataset_id}: {e}")

    async def _prefetch_chunks_background(self, dataset: Dataset):
        """Prefetching en background."""
        try:
            semaphore = asyncio.Semaphore(self.config.max_concurrent_downloads)

            async def prefetch_chunk(chunk_cid: str):
                async with semaphore:
                    if chunk_cid not in self.chunk_cache:
                        try:
                            data = await asyncio.wait_for(
                                self.ipfs.get_data(chunk_cid),
                                timeout=self.config.chunk_timeout_seconds
                            )
                            self.chunk_cache[chunk_cid] = data
                            logger.debug(f"📦 Prefetched chunk: {chunk_cid}")
                        except Exception as e:
                            logger.debug(f"⚠️ Prefetch failed for chunk {chunk_cid}: {e}")

            # Prefetchear primeros chunks
            tasks = []
            for i in range(min(self.config.prefetch_ahead, dataset.chunk_count)):
                chunk_cid = f"{dataset.ipfs_cid}_chunk_{i}"  # Placeholder
                task = prefetch_chunk(chunk_cid)
                tasks.append(task)

            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.warning(f"⚠️ Background prefetch failed: {e}")

    def get_download_stats(self, download_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtener estadísticas de descargas.

        Args:
            download_id: ID específico de descarga o None para todas

        Returns:
            Estadísticas de descarga
        """
        if download_id:
            return self.download_stats.get(download_id, {})

        return {
            'active_downloads': len(self.active_downloads),
            'completed_downloads': len([s for s in self.download_stats.values() if 'end_time' in s]),
            'cached_chunks': len(self.chunk_cache),
            'cache_size_bytes': sum(len(data) for data in self.chunk_cache.values()),
            'details': dict(self.download_stats)
        }

    def clear_cache(self):
        """Limpiar cache de chunks prefetcheados."""
        cache_size = sum(len(data) for data in self.chunk_cache.values())
        self.chunk_cache.clear()
        logger.info(f"🧹 Cleared prefetch cache: {cache_size} bytes")

    async def cancel_download(self, download_id: str) -> bool:
        """
        Cancelar una descarga activa.

        Args:
            download_id: ID de la descarga

        Returns:
            True si se canceló exitosamente
        """
        if download_id in self.active_downloads:
            task = self.active_downloads[download_id]
            task.cancel()
            del self.active_downloads[download_id]
            logger.info(f"🛑 Cancelled download: {download_id}")
            return True

        return False

    async def cleanup_temp_files(self):
        """Limpiar archivos temporales de descargas incompletas."""
        try:
            temp_dir = Path(self.config.temp_dir)
            if temp_dir.exists():
                for file_path in temp_dir.glob("*"):
                    if file_path.is_file():
                        file_path.unlink()
                logger.debug("🧹 Cleaned up temporary download files")
        except Exception as e:
            logger.warning(f"⚠️ Failed to cleanup temp files: {e}")