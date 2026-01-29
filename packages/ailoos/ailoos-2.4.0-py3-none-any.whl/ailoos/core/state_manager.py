"""
Sistema de gestión de estado tensorial para AILOOS.
Serialización de tensores usando safetensors con encriptación homomórfica y gestión de estado persistente.
"""

import os
import json
import hashlib
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

try:
    import torch
    from safetensors.torch import save_file, load_file
except ImportError:
    torch = None
    save_file = None
    load_file = None

try:
    import tenseal as ts
except ImportError:
    ts = None

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from ..utils.logging import get_logger


@dataclass
class TensorMetadata:
    """Metadatos de un tensor serializado."""
    name: str
    shape: Tuple[int, ...]
    dtype: str
    encrypted: bool
    homomorphic_scheme: Optional[str]
    created_at: datetime
    checksum: str
    size_bytes: int
    memory_type: str = "active"  # "active" o "consolidated"
    consolidation_info: Optional[Dict[str, Any]] = None


class HomomorphicEncryptionManager:
    """Gestor de encriptación homomórfica para tensores."""

    def __init__(self, key: Optional[bytes] = None):
        self.logger = get_logger(__name__)
        self.key = key or Fernet.generate_key()
        self.fernet = Fernet(self.key)

        # Contexto homomórfico (placeholder para implementación completa)
        self.context = None
        if ts:
            try:
                self.context = ts.context(
                    ts.SCHEME_TYPE.CKKS,
                    poly_modulus_degree=8192,
                    coeff_mod_bit_sizes=[60, 40, 40, 60]
                )
                self.context.generate_galois_keys()
                self.context.global_scale = 2**40
            except Exception as e:
                self.logger.warning(f"No se pudo inicializar contexto homomórfico: {e}")

    def encrypt_tensor_homomorphic(self, tensor: torch.Tensor) -> bytes:
        """Encriptar tensor usando esquema homomórfico."""
        if not ts or not self.context:
            # Fallback a encriptación simétrica
            return self._encrypt_symmetric(tensor.numpy().tobytes())

        try:
            # Convertir tensor a array plano
            flat_tensor = tensor.flatten().tolist()

            # Encriptar usando CKKS
            encrypted_tensor = ts.ckks_tensor(self.context, flat_tensor)
            encrypted_data = encrypted_tensor.serialize()

            return encrypted_data
        except Exception as e:
            self.logger.error(f"Error en encriptación homomórfica: {e}")
            return self._encrypt_symmetric(tensor.numpy().tobytes())

    def decrypt_tensor_homomorphic(self, data: bytes, shape: Tuple[int, ...], dtype: torch.dtype) -> torch.Tensor:
        """Desencriptar tensor usando esquema homomórfico."""
        if not ts or not self.context:
            # Fallback a desencriptación simétrica
            flat_bytes = self._decrypt_symmetric(data)
            flat_array = torch.frombuffer(flat_bytes, dtype=dtype)
            return flat_array.view(shape)

        try:
            # Deserializar tensor encriptado
            encrypted_tensor = ts.ckks_tensor_from(self.context, data)
            decrypted_list = encrypted_tensor.decrypt()

            # Reconstruir tensor
            tensor = torch.tensor(decrypted_list, dtype=dtype).view(shape)
            return tensor
        except Exception as e:
            self.logger.error(f"Error en desencriptación homomórfica: {e}")
            flat_bytes = self._decrypt_symmetric(data)
            flat_array = torch.frombuffer(flat_bytes, dtype=dtype)
            return flat_array.view(shape)

    def _encrypt_symmetric(self, data: bytes) -> bytes:
        """Encriptación simétrica como fallback."""
        return self.fernet.encrypt(data)

    def _decrypt_symmetric(self, data: bytes) -> bytes:
        """Desencriptación simétrica como fallback."""
        return self.fernet.decrypt(data)


class TensorStateManager:
    """
    Gestor de estado tensorial con serialización segura y persistente.
    """

    def __init__(self, storage_path: str = "./tensor_states", encryption_key: Optional[str] = None):
        self.logger = get_logger(__name__)
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Derivar clave de encriptación
        if encryption_key:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'ailoos_tensor_salt',
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
        else:
            key = None

        self.encryption_manager = HomomorphicEncryptionManager(key)
        self.metadata_store: Dict[str, TensorMetadata] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.lock = threading.RLock()

        # Cargar metadatos existentes
        self._load_metadata()
        self.logger.info(f"TensorStateManager inicializado en {storage_path}")

        # Estadísticas de memoria
        self.consolidated_memory_count = 0
        self.active_memory_count = 0
        self._update_memory_stats()

    def serialize_tensor(self, name: str, tensor: torch.Tensor,
                        use_homomorphic: bool = True,
                        memory_type: str = "active",
                        consolidation_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        Serializar y almacenar un tensor de forma segura.

        Args:
            name: Nombre identificador del tensor
            tensor: Tensor de PyTorch a serializar
            use_homomorphic: Usar encriptación homomórfica si disponible

        Returns:
            True si la serialización fue exitosa
        """
        if torch is None:
            self.logger.error("PyTorch no está disponible")
            return False

        try:
            with self.lock:
                # Crear metadatos
                checksum = hashlib.sha256(tensor.numpy().tobytes()).hexdigest()
                metadata = TensorMetadata(
                    name=name,
                    shape=tensor.shape,
                    dtype=str(tensor.dtype),
                    encrypted=use_homomorphic,
                    homomorphic_scheme="CKKS" if use_homomorphic and ts else None,
                    created_at=datetime.now(),
                    checksum=checksum,
                    size_bytes=tensor.numel() * tensor.element_size(),
                    memory_type=memory_type,
                    consolidation_info=consolidation_info
                )

                # Serializar usando safetensors
                if save_file:
                    tensor_dict = {name: tensor}
                    safe_path = self.storage_path / f"{name}.safetensors"

                    # Encriptar si se solicita
                    if use_homomorphic:
                        encrypted_data = self.encryption_manager.encrypt_tensor_homomorphic(tensor)
                        # Guardar datos encriptados como tensor dummy para safetensors
                        encrypted_tensor = torch.frombuffer(encrypted_data, dtype=torch.uint8)
                        tensor_dict = {f"{name}_encrypted": encrypted_tensor}
                        metadata.encrypted = True
                    else:
                        metadata.encrypted = False

                    save_file(tensor_dict, safe_path)
                else:
                    # Fallback sin safetensors
                    tensor_path = self.storage_path / f"{name}.pt"
                    if use_homomorphic:
                        encrypted_data = self.encryption_manager.encrypt_tensor_homomorphic(tensor)
                        torch.save(encrypted_data, tensor_path)
                        metadata.encrypted = True
                    else:
                        torch.save(tensor, tensor_path)
                        metadata.encrypted = False

                # Guardar metadatos
                self.metadata_store[name] = metadata
                self._update_memory_stats()
                self._save_metadata()

                self.logger.info(f"Tensor '{name}' serializado exitosamente")
                return True

        except Exception as e:
            self.logger.error(f"Error serializando tensor '{name}': {e}")
            return False

    def deserialize_tensor(self, name: str) -> Optional[torch.Tensor]:
        """
        Deserializar un tensor almacenado.

        Args:
            name: Nombre del tensor a deserializar

        Returns:
            Tensor deserializado o None si falla
        """
        if torch is None:
            self.logger.error("PyTorch no está disponible")
            return None

        try:
            with self.lock:
                if name not in self.metadata_store:
                    self.logger.error(f"Tensor '{name}' no encontrado en metadatos")
                    return None

                metadata = self.metadata_store[name]

                if save_file and load_file:
                    safe_path = self.storage_path / f"{name}.safetensors"
                    if not safe_path.exists():
                        self.logger.error(f"Archivo safetensors no encontrado: {safe_path}")
                        return None

                    loaded = load_file(safe_path)

                    if metadata.encrypted:
                        encrypted_data = loaded[f"{name}_encrypted"].numpy().tobytes()
                        tensor = self.encryption_manager.decrypt_tensor_homomorphic(
                            encrypted_data, metadata.shape, getattr(torch, metadata.dtype.split('.')[-1])
                        )
                    else:
                        tensor = loaded[name]
                else:
                    # Fallback sin safetensors
                    tensor_path = self.storage_path / f"{name}.pt"
                    if not tensor_path.exists():
                        self.logger.error(f"Archivo tensor no encontrado: {tensor_path}")
                        return None

                    if metadata.encrypted:
                        encrypted_data = torch.load(tensor_path)
                        tensor = self.encryption_manager.decrypt_tensor_homomorphic(
                            encrypted_data, metadata.shape, getattr(torch, metadata.dtype.split('.')[-1])
                        )
                    else:
                        tensor = torch.load(tensor_path)

                # Verificar checksum
                current_checksum = hashlib.sha256(tensor.numpy().tobytes()).hexdigest()
                if current_checksum != metadata.checksum:
                    self.logger.warning(f"Checksum mismatch para tensor '{name}'")

                self.logger.info(f"Tensor '{name}' deserializado exitosamente")
                return tensor

        except Exception as e:
            self.logger.error(f"Error deserializando tensor '{name}': {e}")
            return None

    def list_tensors(self) -> Dict[str, TensorMetadata]:
        """Listar todos los tensores almacenados."""
        with self.lock:
            return self.metadata_store.copy()

    def delete_tensor(self, name: str) -> bool:
        """Eliminar un tensor almacenado."""
        try:
            with self.lock:
                if name not in self.metadata_store:
                    return False

                # Eliminar archivos
                safe_path = self.storage_path / f"{name}.safetensors"
                tensor_path = self.storage_path / f"{name}.pt"

                if safe_path.exists():
                    safe_path.unlink()
                if tensor_path.exists():
                    tensor_path.unlink()

                # Eliminar metadatos
                del self.metadata_store[name]
                self._save_metadata()

                self.logger.info(f"Tensor '{name}' eliminado")
                return True

        except Exception as e:
            self.logger.error(f"Error eliminando tensor '{name}': {e}")
            return False

    def cleanup_old_tensors(self, days: int = 30) -> int:
        """Limpiar tensores antiguos."""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        deleted = 0

        with self.lock:
            to_delete = []
            for name, metadata in self.metadata_store.items():
                if metadata.created_at.timestamp() < cutoff:
                    to_delete.append(name)

            for name in to_delete:
                if self.delete_tensor(name):
                    deleted += 1

        self.logger.info(f"Eliminados {deleted} tensores antiguos")
        return deleted

    def _update_memory_stats(self):
        """Actualizar estadísticas de memoria consolidada vs activa."""
        self.active_memory_count = 0
        self.consolidated_memory_count = 0

        for metadata in self.metadata_store.values():
            if metadata.memory_type == "consolidated":
                self.consolidated_memory_count += 1
            else:
                self.active_memory_count += 1

    def get_memory_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de memoria por tipo."""
        total_size_active = 0
        total_size_consolidated = 0

        for metadata in self.metadata_store.values():
            if metadata.memory_type == "consolidated":
                total_size_consolidated += metadata.size_bytes
            else:
                total_size_active += metadata.size_bytes

        return {
            'active_memory_count': self.active_memory_count,
            'consolidated_memory_count': self.consolidated_memory_count,
            'total_active_size_mb': total_size_active / (1024 * 1024),
            'total_consolidated_size_mb': total_size_consolidated / (1024 * 1024),
            'total_tensors': len(self.metadata_store)
        }

    def list_tensors_by_type(self, memory_type: str) -> Dict[str, TensorMetadata]:
        """Listar tensores por tipo de memoria."""
        return {
            name: metadata for name, metadata in self.metadata_store.items()
            if metadata.memory_type == memory_type
        }

    def consolidate_tensor(self, name: str, consolidation_info: Optional[Dict[str, Any]] = None) -> bool:
        """Marcar un tensor como consolidado."""
        if name not in self.metadata_store:
            return False

        metadata = self.metadata_store[name]
        metadata.memory_type = "consolidated"
        metadata.consolidation_info = consolidation_info or {}
        self._update_memory_stats()
        self._save_metadata()

        self.logger.info(f"Tensor '{name}' marcado como consolidado")
        return True

    def activate_tensor(self, name: str) -> bool:
        """Marcar un tensor como activo."""
        if name not in self.metadata_store:
            return False

        metadata = self.metadata_store[name]
        metadata.memory_type = "active"
        metadata.consolidation_info = None
        self._update_memory_stats()
        self._save_metadata()

        self.logger.info(f"Tensor '{name}' marcado como activo")
        return True

    def cleanup_consolidated_tensors(self, max_age_days: int = 90) -> int:
        """Limpiar tensores consolidados antiguos."""
        cutoff = datetime.now() - timedelta(days=max_age_days)
        to_delete = []

        for name, metadata in self.metadata_store.items():
            if (metadata.memory_type == "consolidated" and
                metadata.consolidation_info and
                'consolidation_timestamp' in metadata.consolidation_info):
                try:
                    consolidation_time = datetime.fromisoformat(metadata.consolidation_info['consolidation_timestamp'])
                    if consolidation_time < cutoff:
                        to_delete.append(name)
                except:
                    # Si no se puede parsear, asumir que es antiguo
                    to_delete.append(name)

        deleted = 0
        for name in to_delete:
            if self.delete_tensor(name):
                deleted += 1

        self.logger.info(f"Eliminados {deleted} tensores consolidados antiguos")
        return deleted

    def _load_metadata(self):
        """Cargar metadatos desde disco."""
        metadata_path = self.storage_path / "metadata.json"
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for name, meta_dict in data.items():
                        meta_dict['created_at'] = datetime.fromisoformat(meta_dict['created_at'])
                        meta_dict['shape'] = tuple(meta_dict['shape'])
                        # Handle new fields with defaults
                        meta_dict.setdefault('memory_type', 'active')
                        meta_dict.setdefault('consolidation_info', None)
                        self.metadata_store[name] = TensorMetadata(**meta_dict)
                self.logger.info("Metadatos cargados")
            except Exception as e:
                self.logger.error(f"Error cargando metadatos: {e}")

    def _save_metadata(self):
        """Guardar metadatos a disco."""
        metadata_path = self.storage_path / "metadata.json"
        try:
            data = {}
            for name, metadata in self.metadata_store.items():
                meta_dict = metadata.__dict__.copy()
                meta_dict['created_at'] = metadata.created_at.isoformat()
                meta_dict['shape'] = list(metadata.shape)
                data[name] = meta_dict

            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error guardando metadatos: {e}")

    async def async_serialize_tensor(self, name: str, tensor: torch.Tensor,
                                    use_homomorphic: bool = True,
                                    memory_type: str = "active",
                                    consolidation_info: Optional[Dict[str, Any]] = None) -> bool:
        """Versión asíncrona de serialize_tensor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self.serialize_tensor, name, tensor, use_homomorphic, memory_type, consolidation_info
        )

    async def async_deserialize_tensor(self, name: str) -> Optional[torch.Tensor]:
        """Versión asíncrona de deserialize_tensor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.deserialize_tensor, name)


# Instancia global
_tensor_state_manager: Optional[TensorStateManager] = None


def get_tensor_state_manager(storage_path: str = "./tensor_states",
                           encryption_key: Optional[str] = None) -> TensorStateManager:
    """Obtener instancia global del gestor de estado tensorial."""
    global _tensor_state_manager
    if _tensor_state_manager is None:
        _tensor_state_manager = TensorStateManager(storage_path, encryption_key)
    return _tensor_state_manager

# Alias for compatibility
get_state_manager = get_tensor_state_manager