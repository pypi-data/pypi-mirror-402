"""
ModelManager - Gestor de modelos para nodos federados
Maneja subida, descarga y gestión de modelos en el sistema AILOOS.
Implementación completa con compresión, cache inteligente y soporte IPFS.
"""

import asyncio
import json
import os
import hashlib
import gzip
import lzma
import aiofiles
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime, timedelta
from collections import OrderedDict
import aiohttp
from urllib.parse import urlencode

from ..core.logging import get_logger
from ..core.logging import get_logger
from .auth import NodeAuthenticator

if False:  # TYPE_CHECKING hack to avoid runtime import issues if circular
    from ..infrastructure.ipfs_embedded import IPFSManager

logger = get_logger(__name__)


class ModelFormat:
    """Formatos de modelo soportados."""
    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"
    ONNX = "onnx"
    H5 = "h5"
    PKL = "pkl"
    JOBLIB = "joblib"
    TFLITE = "tflite"
    PROTOBUF = "protobuf"


class CompressionType:
    """Tipos de compresión soportados."""
    NONE = "none"
    GZIP = "gzip"
    LZMA = "lzma"


class ModelCache:
    """Cache inteligente para modelos con TTL y LRU."""

    def __init__(self, max_size: int = 100, ttl_hours: int = 24):
        self.max_size = max_size
        self.ttl = timedelta(hours=ttl_hours)
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._access_times: Dict[str, datetime] = {}
        self.hit_count = 0
        self.miss_count = 0

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Obtener elemento del cache."""
        if key in self._cache:
            # Verificar TTL
            if datetime.now() - self._access_times[key] > self.ttl:
                self._remove(key)
                self.miss_count += 1
                return None

            # Hit
            self.hit_count += 1
            # Mover a final (LRU)
            self._cache.move_to_end(key)
            self._access_times[key] = datetime.now()
            return self._cache[key]
        # Miss
        self.miss_count += 1
        return None

    def put(self, key: str, value: Dict[str, Any]):
        """Agregar elemento al cache."""
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self.max_size:
                # Remover el menos recientemente usado
                oldest_key, _ = self._cache.popitem(last=False)
                del self._access_times[oldest_key]

        self._cache[key] = value
        self._access_times[key] = datetime.now()

    def _remove(self, key: str):
        """Remover elemento del cache."""
        if key in self._cache:
            del self._cache[key]
            del self._access_times[key]

    def clear_expired(self):
        """Limpiar elementos expirados."""
        now = datetime.now()
        expired_keys = [
            key for key, access_time in self._access_times.items()
            if now - access_time > self.ttl
        ]
        for key in expired_keys:
            self._remove(key)

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache."""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0.0
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "ttl_hours": self.ttl.total_seconds() / 3600,
            "hit_rate": hit_rate,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "total_requests": total_requests
        }


class ModelManager:
    """
    Gestor de modelos para nodos federados.

    Maneja:
    - Subida de modelos al sistema
    - Descarga de modelos del sistema
    - Verificación de integridad
    - Gestión de versiones de modelos
    - Compresión/descompresión
    """

    def __init__(self, node_id: str, models_dir: str, coordinator_url: str,
            authenticator: NodeAuthenticator,
            chunk_size: int = 1024 * 1024,
            compression: str = CompressionType.GZIP, 
            cache_size: int = 50,
            cache_ttl_hours: int = 24, 
            ipfs_gateway: Optional[str] = None,
            ipfs_manager: Optional['IPFSManager'] = None):
        """
        Inicializar el gestor de modelos.

        Args:
            node_id: ID del nodo
            models_dir: Directorio para almacenar modelos
            coordinator_url: URL del coordinador
            authenticator: Autenticador para requests
            chunk_size: Tamaño de chunk para uploads/downloads
            compression: Tipo de compresión (none, gzip, lzma)
            cache_size: Tamaño máximo del cache
            cache_ttl_hours: TTL del cache en horas
            ipfs_gateway: URL del gateway IPFS (opcional)
            ipfs_manager: Instancia de IPFSManager (opcional, para descargas P2P reales)
        """
        self.node_id = node_id
        self.models_dir = Path(models_dir)
        self.coordinator_url = coordinator_url.rstrip('/')
        self.auth = authenticator
        self.chunk_size = chunk_size
        self.compression = compression
        self.ipfs_gateway = ipfs_gateway or "https://gateway.ipfs.io/ipfs/"
        self.ipfs_manager = ipfs_manager

        # Crear directorios si no existen
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._compressed_dir = self.models_dir / "compressed"
        self._compressed_dir.mkdir(exist_ok=True)

        # HTTP client
        self._session: Optional[aiohttp.ClientSession] = None

        # Cache inteligente
        self._model_cache = ModelCache(max_size=cache_size, ttl_hours=cache_ttl_hours)

        # Cache de modelos locales (legacy)
        self._local_models: Dict[str, Dict[str, Any]] = {}

        # Extensiones de modelo soportadas
        self._supported_extensions = {
            '.pt': ModelFormat.PYTORCH,
            '.pth': ModelFormat.PYTORCH,
            '.h5': ModelFormat.H5,
            '.pkl': ModelFormat.PKL,
            '.joblib': ModelFormat.JOBLIB,
            '.onnx': ModelFormat.ONNX,
            '.pb': ModelFormat.PROTOBUF,
            '.tflite': ModelFormat.TFLITE
        }

        logger.info(f"📦 ModelManager initialized for node {node_id} with compression={compression}")

    async def initialize(self) -> bool:
        """
        Inicializar el gestor de modelos.

        Returns:
            True si la inicialización fue exitosa
        """
        try:
            # Crear HTTP session
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=300)  # 5 minutos timeout
            )

            # Escanear modelos locales existentes
            await self._scan_local_models()

            logger.info(f"✅ ModelManager initialized for node {self.node_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error initializing ModelManager: {e}")
            return False

    async def close(self):
        """Cerrar el gestor y limpiar recursos."""
        if self._session:
            await self._session.close()

        logger.info(f"🔒 ModelManager closed for node {self.node_id}")

    async def upload_model(self, model_path: str, metadata: Dict[str, Any],
                          compress: bool = True) -> Optional[str]:
        """
        Subir un modelo al sistema con compresión automática.

        Args:
            model_path: Ruta al archivo del modelo
            metadata: Metadatos del modelo
            compress: Si comprimir el modelo antes de subir

        Returns:
            ID del modelo subido o None si falló
        """
        try:
            model_file = Path(model_path)
            if not model_file.exists():
                logger.error(f"Model file does not exist: {model_path}")
                return None

            # Detectar formato del modelo
            model_format = self._detect_model_format(model_file)
            if not model_format:
                logger.warning(f"Unknown model format for {model_file.name}, proceeding anyway")

            # Preparar archivo para upload (comprimir si es necesario)
            upload_file = model_file
            compression_used = CompressionType.NONE

            if compress and self.compression != CompressionType.NONE:
                compressed_path = await self._compress_model(model_file)
                if compressed_path:
                    upload_file = compressed_path
                    compression_used = self.compression
                    logger.info(f"📦 Model compressed: {model_file.name} -> {upload_file.name}")

            # Calcular hashes del archivo
            hashes = await self._calculate_file_hashes(upload_file)

            # Preparar metadata enriquecida
            model_metadata = self._prepare_model_metadata(
                model_file, upload_file, metadata, model_format, compression_used, hashes
            )

            # Subir usando multipart/form-data
            model_id = await self._upload_model_multipart(upload_file, model_metadata)
            if model_id:
                # Cachear información local
                cache_entry = {
                    "local_path": str(model_file),
                    "compressed_path": str(upload_file) if upload_file != model_file else None,
                    "metadata": model_metadata,
                    "uploaded_at": datetime.now().isoformat(),
                    "hashes": hashes,
                    "format": model_format,
                    "compression": compression_used
                }
                self._model_cache.put(model_id, cache_entry)
                self._local_models[model_id] = cache_entry

                logger.info(f"📤 Model uploaded successfully: {model_id} ({model_format})")
                return model_id

            return None

        except Exception as e:
            logger.error(f"❌ Error uploading model {model_path}: {e}")
            return None

    async def download_model(self, model_id: str, save_path: str,
                           verify_integrity: bool = True) -> bool:
        """
        Descargar un modelo del sistema (coordinador o IPFS).

        Args:
            model_id: ID del modelo
            save_path: Ruta donde guardar el modelo
            verify_integrity: Si verificar integridad después de descargar

        Returns:
            True si la descarga fue exitosa
        """
        try:
            save_file = Path(save_path)
            save_file.parent.mkdir(parents=True, exist_ok=True)

            # Verificar cache primero
            cached_info = self._model_cache.get(model_id)
            if cached_info and cached_info.get("local_path"):
                cached_path = Path(cached_info["local_path"])
                if cached_path.exists():
                    logger.info(f"📋 Model {model_id} found in cache")
                    # Copiar del cache
                    await self._copy_file(cached_path, save_file)
                    return True

            # Obtener información del modelo
            model_info = await self.get_model_info(model_id)
            if not model_info:
                logger.error(f"Model {model_id} not found")
                return False

            # Intentar descarga del coordinador primero
            success = await self._download_from_coordinator(model_id, save_file, model_info)
            if not success:
                # Fallback a IPFS si está disponible
                ipfs_cid = model_info.get("ipfs_cid")
                if ipfs_cid:
                    logger.info(f"🔄 Falling back to IPFS download for {model_id}")
                    success = await self._download_from_ipfs(ipfs_cid, save_file, model_info)
                else:
                    logger.error(f"No IPFS CID available for model {model_id}")
                    return False

            if not success:
                return False

            # Descomprimir si es necesario
            final_path = await self._decompress_if_needed(save_file, model_info)
            if final_path != save_file:
                save_file = final_path

            # Verificar integridad
            if verify_integrity:
                success = await self._verify_model_integrity(save_file, model_info)
                if not success:
                    save_file.unlink()  # Eliminar archivo corrupto
                    return False

            # Cachear información local
            cache_entry = {
                "local_path": str(save_file),
                "metadata": model_info,
                "downloaded_at": datetime.now().isoformat(),
                "hashes": model_info.get("hashes", {}),
                "format": model_info.get("format"),
                "compression": model_info.get("compression", CompressionType.NONE)
            }
            self._model_cache.put(model_id, cache_entry)
            self._local_models[model_id] = cache_entry

            logger.info(f"📥 Model downloaded successfully: {model_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error downloading model {model_id}: {e}")
            return False

    async def list_models(self, filters: Optional[Dict[str, Any]] = None,
                         include_local: bool = True) -> List[Dict[str, Any]]:
        """
        Listar modelos disponibles con filtros avanzados.

        Args:
            filters: Filtros opcionales (framework, format, version, tags, etc.)
            include_local: Incluir modelos locales en el resultado

        Returns:
            Lista de modelos
        """
        try:
            models = []

            # Obtener modelos del coordinador
            if self._session:
                coordinator_models = await self._list_models_from_coordinator(filters)
                models.extend(coordinator_models)

            # Incluir modelos locales si se solicita
            if include_local:
                local_models = await self._list_local_models(filters)
                models.extend(local_models)

            # Aplicar filtros adicionales localmente
            if filters:
                models = self._apply_local_filters(models, filters)

            # Remover duplicados por ID
            seen_ids = set()
            unique_models = []
            for model in models:
                model_id = model.get("id") or model.get("model_id")
                if model_id and model_id not in seen_ids:
                    seen_ids.add(model_id)
                    unique_models.append(model)

            return unique_models

        except Exception as e:
            logger.error(f"❌ Error listing models: {e}")
            return []

    async def _list_models_from_coordinator(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Listar modelos del coordinador."""
        try:
            if not self._session:
                return []

            # Preparar query parameters
            params = {}
            if filters:
                for key, value in filters.items():
                    if isinstance(value, list):
                        params[key] = ",".join(str(v) for v in value)
                    elif isinstance(value, bool):
                        params[key] = "true" if value else "false"
                    else:
                        params[key] = str(value)

            headers = self.auth.get_auth_headers()
            async with self._session.get(
                f"{self.coordinator_url}/api/models/list",
                params=params,
                headers=headers
            ) as response:

                if response.status == 200:
                    result = await response.json()
                    return result.get("data", [])
                else:
                    logger.warning(f"Failed to list models from coordinator: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error listing models from coordinator: {e}")
            return []

    async def _list_local_models(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Listar modelos locales."""
        models = []
        for model_id, info in self._local_models.items():
            model_data = {
                "id": model_id,
                "name": info.get("metadata", {}).get("filename", "unknown"),
                "model_type": info.get("metadata", {}).get("model_type", "unknown"),
                "version": info.get("metadata", {}).get("version", "unknown"),
                "framework": info.get("metadata", {}).get("framework", "unknown"),
                "format": info.get("format"),
                "compression": info.get("compression"),
                "file_size": info.get("metadata", {}).get("original_size"),
                "tags": info.get("metadata", {}).get("tags", []),
                "is_local": True,
                "uploaded_at": info.get("uploaded_at"),
                "metadata": info.get("metadata", {})
            }
            models.append(model_data)

        return models

    def _apply_local_filters(self, models: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Aplicar filtros adicionales localmente."""
        filtered = models.copy()

        if "framework" in filters:
            framework = filters["framework"]
            filtered = [m for m in filtered if m.get("framework") == framework]

        if "format" in filters:
            format_filter = filters["format"]
            filtered = [m for m in filtered if m.get("format") == format_filter]

        if "min_size" in filters:
            min_size = filters["min_size"]
            filtered = [m for m in filtered if m.get("file_size", 0) >= min_size]

        if "max_size" in filters:
            max_size = filters["max_size"]
            filtered = [m for m in filtered if m.get("file_size", 0) <= max_size]

        if "tags" in filters:
            required_tags = set(filters["tags"]) if isinstance(filters["tags"], list) else {filters["tags"]}
            filtered = [m for m in filtered if required_tags.issubset(set(m.get("tags", [])))]

        if "has_compression" in filters:
            has_compression = filters["has_compression"]
            if has_compression:
                filtered = [m for m in filtered if m.get("compression") != CompressionType.NONE]
            else:
                filtered = [m for m in filtered if m.get("compression") == CompressionType.NONE]

        return filtered

    async def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener información de un modelo.

        Args:
            model_id: ID del modelo

        Returns:
            Información del modelo o None
        """
        try:
            if not self._session:
                return None

            headers = self.auth.get_auth_headers()
            async with self._session.get(
                f"{self.coordinator_url}/api/models/{model_id}",
                headers=headers
            ) as response:

                if response.status == 200:
                    payload = await response.json()
                    if isinstance(payload, dict) and "data" in payload:
                        payload = payload.get("data")
                    if isinstance(payload, dict) and "file_hash" in payload and "hashes" not in payload:
                        payload["hashes"] = {"sha256": payload["file_hash"]}
                    return payload

                else:
                    logger.warning(f"Failed to get model info for {model_id}: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"❌ Error getting model info for {model_id}: {e}")
            return None

    async def delete_model(self, model_id: str) -> bool:
        """
        Eliminar un modelo del sistema.

        Args:
            model_id: ID del modelo

        Returns:
            True si se eliminó exitosamente
        """
        try:
            if not self._session:
                return False

            headers = self.auth.get_auth_headers()
            async with self._session.delete(
                f"{self.coordinator_url}/api/models/{model_id}",
                headers=headers
            ) as response:

                if response.status == 200:
                    # Remover de cache local
                    if model_id in self._local_models:
                        del self._local_models[model_id]

                    logger.info(f"🗑️ Model deleted: {model_id}")
                    return True

                else:
                    logger.warning(f"Failed to delete model {model_id}: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"❌ Error deleting model {model_id}: {e}")
            return False

    def get_local_models(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtener modelos locales cacheados.

        Returns:
            Diccionario de modelos locales
        """
        return self._local_models.copy()

    def get_local_model_path(self, model_id: str) -> Optional[str]:
        """
        Obtener ruta local de un modelo.

        Args:
            model_id: ID del modelo

        Returns:
            Ruta local o None si no existe
        """
        model_info = self._local_models.get(model_id)
        return model_info.get("local_path") if model_info else None

    # ==================== MÉTODOS AUXILIARES ====================

    def _detect_model_format(self, file_path: Path) -> Optional[str]:
        """Detectar formato del modelo basado en extensión."""
        return self._supported_extensions.get(file_path.suffix.lower())

    def _prepare_model_metadata(self, original_file: Path, upload_file: Path,
                               metadata: Dict[str, Any], model_format: Optional[str],
                               compression: str, hashes: Dict[str, str]) -> Dict[str, Any]:
        """Preparar metadata completa del modelo."""
        return {
            "node_id": self.node_id,
            "filename": original_file.name,
            "original_size": original_file.stat().st_size,
            "upload_size": upload_file.stat().st_size,
            "compression": compression,
            "compression_ratio": round(upload_file.stat().st_size / original_file.stat().st_size, 3) if original_file != upload_file else 1.0,
            "hashes": hashes,
            "format": model_format,
            "upload_time": datetime.now().isoformat(),
            "model_type": metadata.get("model_type", model_format or "unknown"),
            "framework": metadata.get("framework", self._infer_framework(model_format)),
            "version": metadata.get("version", "1.0.0"),
            "description": metadata.get("description", ""),
            "tags": metadata.get("tags", []),
            "metrics": metadata.get("metrics", {}),
            "architecture": metadata.get("architecture", {}),
            "hyperparameters": metadata.get("hyperparameters", {}),
            "training_info": metadata.get("training_info", {}),
            **metadata
        }

    def _infer_framework(self, model_format: Optional[str]) -> str:
        """Inferir framework basado en formato."""
        framework_map = {
            ModelFormat.PYTORCH: "pytorch",
            ModelFormat.TENSORFLOW: "tensorflow",
            ModelFormat.ONNX: "onnx",
            ModelFormat.H5: "keras",
            ModelFormat.PKL: "sklearn",
            ModelFormat.JOBLIB: "sklearn",
            ModelFormat.TFLITE: "tflite",
            ModelFormat.PROTOBUF: "tensorflow"
        }
        return framework_map.get(model_format, "unknown")

    async def _compress_model(self, file_path: Path) -> Optional[Path]:
        """Comprimir un modelo."""
        try:
            compressed_name = f"{file_path.stem}_compressed"
            if self.compression == CompressionType.GZIP:
                compressed_path = self._compressed_dir / f"{compressed_name}.gz"
                await self._compress_gzip(file_path, compressed_path)
            elif self.compression == CompressionType.LZMA:
                compressed_path = self._compressed_dir / f"{compressed_name}.xz"
                await self._compress_lzma(file_path, compressed_path)
            else:
                return None

            return compressed_path
        except Exception as e:
            logger.warning(f"Failed to compress {file_path}: {e}")
            return None

    async def _compress_gzip(self, input_path: Path, output_path: Path):
        """Comprimir con GZIP."""
        async with aiofiles.open(input_path, 'rb') as f_in:
            with gzip.open(output_path, 'wb') as f_out:
                while True:
                    chunk = await f_in.read(self.chunk_size)
                    if not chunk:
                        break
                    f_out.write(chunk)

    async def _compress_lzma(self, input_path: Path, output_path: Path):
        """Comprimir con LZMA."""
        async with aiofiles.open(input_path, 'rb') as f_in:
            with lzma.open(output_path, 'wb') as f_out:
                while True:
                    chunk = await f_in.read(self.chunk_size)
                    if not chunk:
                        break
                    f_out.write(chunk)

    async def _decompress_if_needed(self, file_path: Path, model_info: Dict[str, Any]) -> Path:
        """Descomprimir archivo si es necesario."""
        compression = model_info.get("compression", CompressionType.NONE)
        if compression == CompressionType.NONE:
            return file_path

        try:
            decompressed_path = file_path.parent / file_path.stem
            if compression == CompressionType.GZIP:
                await self._decompress_gzip(file_path, decompressed_path)
            elif compression == CompressionType.LZMA:
                await self._decompress_lzma(file_path, decompressed_path)

            # Eliminar archivo comprimido y retornar descomprimido
            file_path.unlink()
            return decompressed_path
        except Exception as e:
            logger.warning(f"Failed to decompress {file_path}: {e}")
            return file_path

    async def _decompress_gzip(self, input_path: Path, output_path: Path):
        """Descomprimir GZIP."""
        with gzip.open(input_path, 'rb') as f_in:
            async with aiofiles.open(output_path, 'wb') as f_out:
                while True:
                    chunk = f_in.read(self.chunk_size)
                    if not chunk:
                        break
                    await f_out.write(chunk)

    async def _decompress_lzma(self, input_path: Path, output_path: Path):
        """Descomprimir LZMA."""
        with lzma.open(input_path, 'rb') as f_in:
            async with aiofiles.open(output_path, 'wb') as f_out:
                while True:
                    chunk = f_in.read(self.chunk_size)
                    if not chunk:
                        break
                    await f_out.write(chunk)

    async def _copy_file(self, src: Path, dst: Path):
        """Copiar archivo de forma asíncrona."""
        async with aiofiles.open(src, 'rb') as f_src:
            async with aiofiles.open(dst, 'wb') as f_dst:
                while True:
                    chunk = await f_src.read(self.chunk_size)
                    if not chunk:
                        break
                    await f_dst.write(chunk)

    async def _upload_model_multipart(self, file_path: Path, metadata: Dict[str, Any]) -> Optional[str]:
        """Subir modelo usando multipart/form-data."""
        try:
            if not self._session:
                return None

            # Preparar datos del formulario
            form_data = aiohttp.FormData()

            # Archivo
            async with aiofiles.open(file_path, 'rb') as f:
                file_content = await f.read()
                form_data.add_field('file', file_content, filename=file_path.name,
                                  content_type='application/octet-stream')

            # Metadatos como campos separados
            for key, value in metadata.items():
                if isinstance(value, (list, dict)):
                    form_data.add_field(key, json.dumps(value))
                else:
                    form_data.add_field(key, str(value))

            headers = self.auth.get_auth_headers()
            async with self._session.post(
                f"{self.coordinator_url}/api/models/upload",
                data=form_data,
                headers=headers
            ) as response:

                if response.status == 200:
                    result = await response.json()
                    return result.get("data", {}).get("id")
                else:
                    error_text = await response.text()
                    logger.error(f"Upload failed: {response.status} - {error_text}")
                    return None

        except Exception as e:
            logger.error(f"Error in multipart upload: {e}")
            return None

    async def _download_from_coordinator(self, model_id: str, save_path: Path,
                                       model_info: Dict[str, Any]) -> bool:
        """Descargar modelo del coordinador."""
        try:
            if not self._session:
                return False

            headers = self.auth.get_auth_headers()
            async with self._session.get(
                f"{self.coordinator_url}/api/models/download/{model_id}",
                headers=headers
            ) as response:

                if response.status == 200:
                    async with aiofiles.open(save_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(self.chunk_size):
                            await f.write(chunk)
                    return True
                else:
                    logger.warning(f"Coordinator download failed: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"Error downloading from coordinator: {e}")
            return False

    async def _download_from_ipfs(self, ipfs_cid: str, save_path: Path,
                                model_info: Dict[str, Any]) -> bool:
        """Descargar modelo desde IPFS."""
        try:
            # 1. Usar IPFSManager si está disponible (P2P real)
            if self.ipfs_manager:
                logger.info(f"🏗️ Downloading {ipfs_cid} via IPFSManager (P2P)...")
                try:
                    data = await self.ipfs_manager.get_data(ipfs_cid)
                    if data:
                        async with aiofiles.open(save_path, 'wb') as f:
                            await f.write(data)
                        return True
                    else:
                        logger.warning(f"IPFSManager could not find data for {ipfs_cid}, trying gateway fallback")
                except Exception as e:
                    logger.error(f"IPFSManager download failed: {e}")

            # 2. Fallback a HTTP Gateway
            if not self._session:
                return False

            ipfs_url = f"{self.ipfs_gateway.rstrip('/')}/{ipfs_cid}"
            async with self._session.get(ipfs_url) as response:
                if response.status == 200:
                    async with aiofiles.open(save_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(self.chunk_size):
                            await f.write(chunk)
                    return True
                else:
                    logger.warning(f"IPFS download failed: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"Error downloading from IPFS: {e}")
            return False

    async def _verify_model_integrity(self, file_path: Path, model_info: Dict[str, Any]) -> bool:
        """Verificar integridad del modelo descargado."""
        try:
            expected_hashes = model_info.get("hashes", {})
            if not expected_hashes:
                logger.warning("No hash information available for integrity check")
                return True

            actual_hashes = await self._calculate_file_hashes(file_path)

            # Verificar múltiples algoritmos si están disponibles
            for algo in ["sha256", "sha512", "md5"]:
                expected = expected_hashes.get(algo)
                actual = actual_hashes.get(algo)
                if expected and actual:
                    if expected != actual:
                        logger.error(f"Hash mismatch for {algo}: expected {expected}, got {actual}")
                        return False
                    logger.debug(f"✅ {algo.upper()} verification passed")

            return True
        except Exception as e:
            logger.error(f"Error verifying integrity: {e}")
            return False

    # ==================== MÉTODOS INTERNOS ====================

    async def _scan_local_models(self):
        """Escanear modelos locales existentes."""
        try:
            # Buscar archivos de modelo comunes
            model_extensions = {'.h5', '.pkl', '.pt', '.pth', '.onnx', '.pb', '.tflite'}

            for file_path in self.models_dir.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in model_extensions:
                    model_id = f"local_{file_path.stem}_{hash(str(file_path)) % 10000}"

                    self._local_models[model_id] = {
                        "local_path": str(file_path),
                        "filename": file_path.name,
                        "file_size": file_path.stat().st_size,
                        "metadata": {
                            "model_type": "unknown",
                            "framework": "unknown",
                            "version": "unknown"
                        },
                        "scanned_at": datetime.now().isoformat()
                    }

            logger.info(f"📂 Scanned {len(self._local_models)} local models")

        except Exception as e:
            logger.warning(f"Error scanning local models: {e}")

    async def _calculate_file_hashes(self, file_path: Path) -> Dict[str, str]:
        """
        Calcular múltiples hashes de un archivo para verificación robusta.

        Args:
            file_path: Ruta del archivo

        Returns:
            Diccionario con diferentes hashes
        """
        hash_sha256 = hashlib.sha256()
        hash_sha512 = hashlib.sha512()
        hash_md5 = hashlib.md5()

        async with aiofiles.open(file_path, 'rb') as f:
            while True:
                chunk = await f.read(self.chunk_size)
                if not chunk:
                    break
                hash_sha256.update(chunk)
                hash_sha512.update(chunk)
                hash_md5.update(chunk)

        return {
            "sha256": hash_sha256.hexdigest(),
            "sha512": hash_sha512.hexdigest(),
            "md5": hash_md5.hexdigest()
        }

    async def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calcular hash SHA256 de un archivo (legacy method).

        Args:
            file_path: Ruta del archivo

        Returns:
            Hash SHA256 del archivo
        """
        hashes = await self._calculate_file_hashes(file_path)
        return hashes["sha256"]


    # ==================== MÉTODOS DE UTILIDAD ====================

    def get_manager_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas completas del gestor.

        Returns:
            Estadísticas detalladas del gestor
        """
        # Estadísticas de modelos locales
        local_stats = self._get_local_models_stats()

        # Estadísticas del cache
        cache_stats = self._model_cache.get_stats()

        # Estadísticas de compresión
        compression_stats = self._get_compression_stats()

        # Estadísticas de formatos
        format_stats = self._get_format_stats()

        return {
            "node_id": self.node_id,
            "models_dir": str(self.models_dir),
            "coordinator_url": self.coordinator_url,
            "ipfs_gateway": self.ipfs_gateway,
            "compression_type": self.compression,
            "local_models": local_stats,
            "cache": cache_stats,
            "compression": compression_stats,
            "formats": format_stats,
            "timestamp": datetime.now().isoformat()
        }

    def _get_local_models_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de modelos locales."""
        total_size = 0
        compressed_size = 0
        formats = {}
        frameworks = {}

        for info in self._local_models.values():
            metadata = info.get("metadata", {})
            size = metadata.get("original_size", 0)
            comp_size = metadata.get("upload_size", size)

            total_size += size
            compressed_size += comp_size

            # Contar formatos
            fmt = info.get("format")
            if fmt:
                formats[fmt] = formats.get(fmt, 0) + 1

            # Contar frameworks
            fw = metadata.get("framework")
            if fw:
                frameworks[fw] = frameworks.get(fw, 0) + 1

        compression_ratio = compressed_size / total_size if total_size > 0 else 1.0

        return {
            "count": len(self._local_models),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "compressed_size_mb": round(compressed_size / (1024 * 1024), 2),
            "compression_ratio": round(compression_ratio, 3),
            "space_saved_mb": round((total_size - compressed_size) / (1024 * 1024), 2),
            "formats": formats,
            "frameworks": frameworks
        }

    def _get_compression_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de compresión."""
        compression_usage = {}
        total_compressed = 0

        for info in self._local_models.values():
            comp = info.get("compression", CompressionType.NONE)
            compression_usage[comp] = compression_usage.get(comp, 0) + 1
            if comp != CompressionType.NONE:
                total_compressed += 1

        return {
            "total_compressed": total_compressed,
            "compression_methods": compression_usage,
            "compression_enabled": self.compression != CompressionType.NONE
        }

    def _get_format_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de formatos soportados."""
        supported_count = 0
        used_formats = set()

        for info in self._local_models.values():
            fmt = info.get("format")
            if fmt:
                used_formats.add(fmt)
                if fmt in self._supported_extensions.values():
                    supported_count += 1

        return {
            "supported_formats": list(self._supported_extensions.values()),
            "used_formats": list(used_formats),
            "supported_models_count": supported_count,
            "total_supported_formats": len(set(self._supported_extensions.values()))
        }


    # ==================== GESTIÓN DE VERSIONES ====================

    async def get_model_versions(self, model_name: str, model_type: str) -> List[Dict[str, Any]]:
        """
        Obtener todas las versiones de un modelo específico.

        Args:
            model_name: Nombre del modelo
            model_type: Tipo del modelo

        Returns:
            Lista de versiones del modelo
        """
        try:
            filters = {"name": model_name, "model_type": model_type}
            models = await self.list_models(filters, include_local=True)

            # Ordenar por versión (asumiendo formato semver)
            def version_key(model):
                version = model.get("version", "0.0.0")
                try:
                    # Parsear versión semver básica
                    parts = version.split('.')
                    return tuple(int(x) for x in parts[:3])
                except:
                    return (0, 0, 0)

            models.sort(key=version_key, reverse=True)
            return models

        except Exception as e:
            logger.error(f"Error getting model versions for {model_name}: {e}")
            return []

    async def get_latest_version(self, model_name: str, model_type: str) -> Optional[Dict[str, Any]]:
        """
        Obtener la versión más reciente de un modelo.

        Args:
            model_name: Nombre del modelo
            model_type: Tipo del modelo

        Returns:
            Información de la versión más reciente o None
        """
        versions = await self.get_model_versions(model_name, model_type)
        return versions[0] if versions else None

    # ==================== GESTIÓN DE CACHE ====================

    def clear_cache(self, expired_only: bool = False):
        """
        Limpiar el cache de modelos.

        Args:
            expired_only: Si solo limpiar elementos expirados
        """
        if expired_only:
            self._model_cache.clear_expired()
        else:
            self._model_cache = ModelCache(max_size=self._model_cache.max_size,
                                         ttl_hours=self._model_cache.ttl.total_seconds() / 3600)

        logger.info(f"Cache cleared (expired_only={expired_only})")

    def preload_cache(self, model_ids: List[str]):
        """
        Precargar modelos en el cache.

        Args:
            model_ids: Lista de IDs de modelos a precargar
        """
        # Este método podría implementarse para precargar modelos frecuentemente usados
        logger.info(f"Preloading {len(model_ids)} models into cache")

    # ==================== UTILIDADES AVANZADAS ====================

    async def validate_model_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validar y analizar un archivo de modelo.

        Args:
            file_path: Ruta al archivo del modelo

        Returns:
            Información de validación del modelo
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return {"valid": False, "error": "File does not exist"}

            # Detectar formato
            model_format = self._detect_model_format(path)

            # Calcular hashes
            hashes = await self._calculate_file_hashes(path)

            # Información básica
            stat = path.stat()
            info = {
                "valid": True,
                "filename": path.name,
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "format": model_format,
                "extension": path.suffix,
                "hashes": hashes,
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "is_supported": model_format is not None
            }

            # Verificar si ya existe en el sistema
            existing_models = await self.list_models({"filename": path.name})
            info["exists_in_system"] = len(existing_models) > 0

            return info

        except Exception as e:
            return {"valid": False, "error": str(e)}

    async def compare_models(self, model_id1: str, model_id2: str) -> Dict[str, Any]:
        """
        Comparar dos modelos.

        Args:
            model_id1: ID del primer modelo
            model_id2: ID del segundo modelo

        Returns:
            Comparación detallada de los modelos
        """
        try:
            info1 = await self.get_model_info(model_id1)
            info2 = await self.get_model_info(model_id2)

            if not info1 or not info2:
                return {"error": "One or both models not found"}

            comparison = {
                "model1": {"id": model_id1, "info": info1},
                "model2": {"id": model_id2, "info": info2},
                "differences": {}
            }

            # Comparar campos clave
            fields_to_compare = ["version", "framework", "format", "file_size", "compression"]
            for field in fields_to_compare:
                val1 = info1.get(field)
                val2 = info2.get(field)
                if val1 != val2:
                    comparison["differences"][field] = {"model1": val1, "model2": val2}

            # Comparar hashes si están disponibles
            hashes1 = info1.get("hashes", {})
            hashes2 = info2.get("hashes", {})
            if hashes1 and hashes2:
                hash_diffs = {}
                for algo in ["sha256", "md5"]:
                    if hashes1.get(algo) != hashes2.get(algo):
                        hash_diffs[algo] = "different"
                    else:
                        hash_diffs[algo] = "same"
                comparison["hash_comparison"] = hash_diffs

            return comparison

        except Exception as e:
            return {"error": str(e)}

    def get_supported_formats(self) -> Dict[str, Any]:
        """
        Obtener información de formatos soportados.

        Returns:
            Información de formatos soportados
        """
        return {
            "formats": list(set(self._supported_extensions.values())),
            "extensions": self._supported_extensions,
            "compression_types": [CompressionType.NONE, CompressionType.GZIP, CompressionType.LZMA],
            "features": {
                "compression": self.compression != CompressionType.NONE,
                "ipfs_fallback": bool(self.ipfs_gateway),
                "integrity_check": True,
                "cache_enabled": True
            }
        }


# Funciones de conveniencia

async def create_model_manager(node_id: str, models_dir: str, coordinator_url: str,
                              authenticator: NodeAuthenticator, compression: str = CompressionType.GZIP,
                              cache_size: int = 50, cache_ttl_hours: int = 24,
                              ipfs_gateway: Optional[str] = None) -> ModelManager:
    """
    Crear e inicializar un gestor de modelos con configuración avanzada.

    Args:
        node_id: ID del nodo
        models_dir: Directorio de modelos
        coordinator_url: URL del coordinador
        authenticator: Autenticador
        compression: Tipo de compresión (none, gzip, lzma)
        cache_size: Tamaño máximo del cache
        cache_ttl_hours: TTL del cache en horas
        ipfs_gateway: URL del gateway IPFS (opcional)

    Returns:
        Instancia inicializada del gestor
    """
    manager = ModelManager(
        node_id=node_id,
        models_dir=models_dir,
        coordinator_url=coordinator_url,
        authenticator=authenticator,
        compression=compression,
        cache_size=cache_size,
        cache_ttl_hours=cache_ttl_hours,
        ipfs_gateway=ipfs_gateway
    )
    success = await manager.initialize()
    if not success:
        raise RuntimeError(f"Failed to initialize model manager for node {node_id}")
    return manager


def get_model_file_info(file_path: str) -> Dict[str, Any]:
    """
    Obtener información básica de un archivo de modelo.

    Args:
        file_path: Ruta del archivo

    Returns:
        Información del archivo
    """
    path = Path(file_path)
    if not path.exists():
        return {"error": "File does not exist"}

    stat = path.stat()

    return {
        "filename": path.name,
        "file_size": stat.st_size,
        "file_size_mb": round(stat.st_size / (1024 * 1024), 2),
        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "extension": path.suffix,
        "is_model_file": path.suffix.lower() in {'.h5', '.pkl', '.pt', '.pth', '.onnx', '.pb', '.tflite'}
    }
