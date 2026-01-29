"""
Gestor de IPFS para AILOOS con soporte de State Sharding.
Permite particionar estados de memoria grandes en chunks, encriptarlos y distribuirlos en IPFS.
"""

import asyncio
import hashlib
import json
import os
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor

try:
    import ipfshttpclient
except ImportError:
    ipfshttpclient = None

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from ..utils.logging import get_logger


@dataclass
class ShardMetadata:
    """Metadatos de un shard de estado."""
    state_name: str
    shard_index: int
    total_shards: int
    ipfs_hash: str
    size_bytes: int
    checksum: str
    encrypted: bool
    created_at: datetime


@dataclass
class StateShardManifest:
    """Manifiesto completo de un estado shardeado."""
    state_name: str
    total_shards: int
    total_size: int
    shard_size: int
    encryption_key_hash: Optional[str]
    created_at: datetime
    shards: List[ShardMetadata]


class IPFSShardManager:
    """
    Gestor de IPFS para State Sharding.
    """

    def __init__(self, ipfs_host: str = "/ip4/127.0.0.1/tcp/5001",
                 encryption_key: Optional[str] = None,
                 shard_size_mb: int = 50,
                 auto_pin: bool = True):
        self.logger = get_logger(__name__)
        self.ipfs_host = ipfs_host
        self.shard_size_bytes = shard_size_mb * 1024 * 1024
        self.auto_pin = auto_pin
        self.client = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.lock = threading.RLock()

        # Derivar clave de encriptación
        if encryption_key:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'ailoos_ipfs_salt',
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
        else:
            key = Fernet.generate_key()

        self.fernet = Fernet(key)
        self.encryption_key_hash = hashlib.sha256(key).hexdigest() if encryption_key else None

        # Conectar a IPFS
        self._connect_ipfs()
        self.logger.info(f"IPFSShardManager inicializado con shard size: {shard_size_mb}MB")

    def _connect_ipfs(self):
        """Conectar al cliente IPFS."""
        if ipfshttpclient:
            try:
                self.client = ipfshttpclient.connect(self.ipfs_host)
                self.logger.info("Conectado a IPFS")
            except Exception as e:
                self.logger.error(f"Error conectando a IPFS: {e}")
                self.client = None
        else:
            self.logger.warning("ipfshttpclient no disponible")

    def shard_and_upload_state(self, state_name: str, state_data: bytes,
                             encrypt: bool = True) -> Optional[StateShardManifest]:
        """
        Particionar estado en shards, encriptar y subir a IPFS.

        Args:
            state_name: Nombre del estado
            state_data: Datos del estado como bytes
            encrypt: Si encriptar los shards

        Returns:
            Manifiesto del estado shardeado o None si falla
        """
        if not self.client:
            self.logger.error("Cliente IPFS no disponible")
            return None

        try:
            with self.lock:
                total_size = len(state_data)
                num_shards = max(1, (total_size + self.shard_size_bytes - 1) // self.shard_size_bytes)

                self.logger.info(f"Shardeando estado '{state_name}' en {num_shards} shards")

                shards = []
                manifest = StateShardManifest(
                    state_name=state_name,
                    total_shards=num_shards,
                    total_size=total_size,
                    shard_size=self.shard_size_bytes,
                    encryption_key_hash=self.encryption_key_hash,
                    created_at=datetime.now(),
                    shards=[]
                )

                # Crear shards
                for i in range(num_shards):
                    start = i * self.shard_size_bytes
                    end = min(start + self.shard_size_bytes, total_size)
                    shard_data = state_data[start:end]

                    # Encriptar si se solicita
                    if encrypt:
                        shard_data = self.fernet.encrypt(shard_data)

                    # Calcular checksum
                    checksum = hashlib.sha256(shard_data).hexdigest()

                    # Subir a IPFS
                    result = self.client.add_bytes(shard_data)
                    ipfs_hash = result
                    if self.auto_pin:
                        self.pin_object(ipfs_hash)

                    shard_metadata = ShardMetadata(
                        state_name=state_name,
                        shard_index=i,
                        total_shards=num_shards,
                        ipfs_hash=ipfs_hash,
                        size_bytes=len(shard_data),
                        checksum=checksum,
                        encrypted=encrypt,
                        created_at=datetime.now()
                    )

                    shards.append(shard_metadata)
                    self.logger.debug(f"Shard {i+1}/{num_shards} subido: {ipfs_hash}")

                manifest.shards = shards

                # Subir manifiesto a IPFS
                manifest_data = json.dumps({
                    'state_name': manifest.state_name,
                    'total_shards': manifest.total_shards,
                    'total_size': manifest.total_size,
                    'shard_size': manifest.shard_size,
                    'encryption_key_hash': manifest.encryption_key_hash,
                    'created_at': manifest.created_at.isoformat(),
                    'shards': [{
                        'state_name': s.state_name,
                        'shard_index': s.shard_index,
                        'total_shards': s.total_shards,
                        'ipfs_hash': s.ipfs_hash,
                        'size_bytes': s.size_bytes,
                        'checksum': s.checksum,
                        'encrypted': s.encrypted,
                        'created_at': s.created_at.isoformat()
                    } for s in manifest.shards]
                }, indent=2).encode()

                manifest_result = self.client.add_bytes(manifest_data)
                manifest.ipfs_hash = manifest_result
                if self.auto_pin:
                    self.pin_object(manifest.ipfs_hash)

                self.logger.info(f"Estado '{state_name}' shardeado y subido exitosamente")
                return manifest

        except Exception as e:
            self.logger.error(f"Error shardeando estado '{state_name}': {e}")
            return None

    def download_and_reassemble_state(self, manifest_hash: str,
                                    decryption_key: Optional[str] = None) -> Optional[bytes]:
        """
        Descargar shards desde IPFS y reensamblar el estado.

        Args:
            manifest_hash: Hash IPFS del manifiesto
            decryption_key: Clave para desencriptar (si es necesario)

        Returns:
            Datos del estado reensamblado o None si falla
        """
        if not self.client:
            self.logger.error("Cliente IPFS no disponible")
            return None

        try:
            with self.lock:
                # Descargar manifiesto
                manifest_data = self.client.cat(manifest_hash)
                manifest_dict = json.loads(manifest_data.decode())

                # Reconstruir manifiesto
                manifest = StateShardManifest(
                    state_name=manifest_dict['state_name'],
                    total_shards=manifest_dict['total_shards'],
                    total_size=manifest_dict['total_size'],
                    shard_size=manifest_dict['shard_size'],
                    encryption_key_hash=manifest_dict.get('encryption_key_hash'),
                    created_at=datetime.fromisoformat(manifest_dict['created_at']),
                    shards=[]
                )

                for shard_dict in manifest_dict['shards']:
                    shard = ShardMetadata(
                        state_name=shard_dict['state_name'],
                        shard_index=shard_dict['shard_index'],
                        total_shards=shard_dict['total_shards'],
                        ipfs_hash=shard_dict['ipfs_hash'],
                        size_bytes=shard_dict['size_bytes'],
                        checksum=shard_dict['checksum'],
                        encrypted=shard_dict['encrypted'],
                        created_at=datetime.fromisoformat(shard_dict['created_at'])
                    )
                    manifest.shards.append(shard)

                # Preparar clave de desencriptación
                if manifest.encryption_key_hash and decryption_key:
                    kdf = PBKDF2HMAC(
                        algorithm=hashes.SHA256(),
                        length=32,
                        salt=b'ailoos_ipfs_salt',
                        iterations=100000,
                    )
                    key = base64.urlsafe_b64encode(kdf.derive(decryption_key.encode()))
                    decrypt_fernet = Fernet(key)
                elif manifest.shards[0].encrypted:
                    self.logger.error("Estado encriptado pero no se proporcionó clave de desencriptación")
                    return None
                else:
                    decrypt_fernet = None

                self.logger.info(f"Descargando {manifest.total_shards} shards para estado '{manifest.state_name}'")

                # Descargar y verificar shards
                state_data = bytearray()
                for shard in sorted(manifest.shards, key=lambda s: s.shard_index):
                    shard_data = self.client.cat(shard.ipfs_hash)

                    # Verificar checksum
                    current_checksum = hashlib.sha256(shard_data).hexdigest()
                    if current_checksum != shard.checksum:
                        self.logger.error(f"Checksum mismatch para shard {shard.shard_index}")
                        return None

                    # Desencriptar si es necesario
                    if shard.encrypted and decrypt_fernet:
                        try:
                            shard_data = decrypt_fernet.decrypt(shard_data)
                        except Exception as e:
                            self.logger.error(f"Error desencriptando shard {shard.shard_index}: {e}")
                            return None

                    state_data.extend(shard_data)
                    self.logger.debug(f"Shard {shard.shard_index} descargado y verificado")

                # Verificar tamaño total
                if len(state_data) != manifest.total_size:
                    self.logger.warning(f"Tamaño total mismatch: esperado {manifest.total_size}, obtenido {len(state_data)}")

                self.logger.info(f"Estado '{manifest.state_name}' reensamblado exitosamente")
                return bytes(state_data)

        except Exception as e:
            self.logger.error(f"Error descargando estado desde {manifest_hash}: {e}")
            return None

    def list_ipfs_objects(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Listar objetos en IPFS (limitado para performance)."""
        if not self.client:
            return []

        try:
            # Obtener lista de objetos (esto es limitado en IPFS)
            # En implementación real, se mantendría un índice local
            return []
        except Exception as e:
            self.logger.error(f"Error listando objetos IPFS: {e}")
            return []

    def pin_object(self, ipfs_hash: str) -> bool:
        """Pinear un objeto en IPFS para asegurar persistencia."""
        if not self.client:
            return False

        try:
            self.client.pin.add(ipfs_hash)
            self.logger.info(f"Objeto {ipfs_hash} pineado")
            return True
        except Exception as e:
            self.logger.error(f"Error pineando objeto {ipfs_hash}: {e}")
            return False

    def unpin_object(self, ipfs_hash: str) -> bool:
        """Despinear un objeto en IPFS."""
        if not self.client:
            return False

        try:
            self.client.pin.rm(ipfs_hash)
            self.logger.info(f"Objeto {ipfs_hash} despineado")
            return True
        except Exception as e:
            self.logger.error(f"Error despineando objeto {ipfs_hash}: {e}")
            return False

    def get_object_info(self, ipfs_hash: str) -> Optional[Dict[str, Any]]:
        """Obtener información de un objeto IPFS."""
        if not self.client:
            return None

        try:
            # Obtener información del objeto
            links = self.client.object.links(ipfs_hash)
            stat = self.client.object.stat(ipfs_hash)

            return {
                'hash': ipfs_hash,
                'size': stat['CumulativeSize'],
                'num_links': stat['NumLinks'],
                'links': links.get('Links', [])
            }
        except Exception as e:
            self.logger.error(f"Error obteniendo info de objeto {ipfs_hash}: {e}")
            return None

    async def async_shard_and_upload(self, state_name: str, state_data: bytes,
                                   encrypt: bool = True) -> Optional[StateShardManifest]:
        """Versión asíncrona de shard_and_upload_state."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self.shard_and_upload_state, state_name, state_data, encrypt
        )

    async def async_download_and_reassemble(self, manifest_hash: str,
                                          decryption_key: Optional[str] = None) -> Optional[bytes]:
        """Versión asíncrona de download_and_reassemble_state."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, self.download_and_reassemble_state, manifest_hash, decryption_key
        )


# Instancia global
_ipfs_shard_manager: Optional[IPFSShardManager] = None


def get_ipfs_shard_manager(ipfs_host: str = "/ip4/127.0.0.1/tcp/5001",
                           encryption_key: Optional[str] = None,
                           shard_size_mb: int = 50,
                           auto_pin: bool = True) -> IPFSShardManager:
    """Obtener instancia global del gestor de sharding IPFS."""
    global _ipfs_shard_manager
    if _ipfs_shard_manager is None:
        _ipfs_shard_manager = IPFSShardManager(
            ipfs_host, encryption_key, shard_size_mb, auto_pin=auto_pin
        )
    return _ipfs_shard_manager
