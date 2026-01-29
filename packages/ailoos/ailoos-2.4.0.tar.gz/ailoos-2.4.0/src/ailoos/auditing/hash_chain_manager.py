"""
Gestión de hash chains para integridad de logs críticos en AILOOS.
Implementa cadenas de hash para verificar integridad de logs y datos.
"""

import hashlib
import hmac
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import os
import threading

from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class HashChainEntry:
    """Entrada en la cadena de hash."""
    entry_id: str
    timestamp: float
    data_hash: str
    previous_hash: str
    signature: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def calculate_hash(self) -> str:
        """Calcula hash de la entrada."""
        content = {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp,
            "data_hash": self.data_hash,
            "previous_hash": self.previous_hash,
            "metadata": self.metadata
        }
        content_str = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return asdict(self)


@dataclass
class HashChain:
    """Cadena de hash para un tipo específico de logs."""
    chain_id: str
    chain_type: str  # 'audit_logs', 'security_events', 'compliance_data', etc.
    entries: List[HashChainEntry] = None
    current_hash: str = ""
    created_at: float = None
    last_updated: float = None

    def __post_init__(self):
        if self.entries is None:
            self.entries = []
        if self.created_at is None:
            self.created_at = time.time()
        if not self.current_hash:
            self.current_hash = self._calculate_chain_hash()

    def _calculate_chain_hash(self) -> str:
        """Calcula hash actual de la cadena."""
        if not self.entries:
            return hashlib.sha256(f"{self.chain_id}_genesis".encode()).hexdigest()

        # Hash de todos los entries
        combined = "".join(entry.calculate_hash() for entry in self.entries)
        return hashlib.sha256(combined.encode()).hexdigest()

    def add_entry(self, data: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Añade nueva entrada a la cadena.

        Args:
            data: Datos a hashear
            metadata: Metadata adicional

        Returns:
            ID de la entrada
        """
        # Crear hash de los datos
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True, default=str)
        else:
            data_str = str(data)
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()

        # Crear entrada
        entry_id = f"{self.chain_id}_{len(self.entries)}"
        entry = HashChainEntry(
            entry_id=entry_id,
            timestamp=time.time(),
            data_hash=data_hash,
            previous_hash=self.current_hash,
            metadata=metadata or {}
        )

        # Añadir a la cadena
        self.entries.append(entry)
        self.current_hash = self._calculate_chain_hash()
        self.last_updated = time.time()

        logger.debug(f"➕ Added entry {entry_id} to hash chain {self.chain_id}")
        return entry_id

    def verify_integrity(self) -> bool:
        """
        Verifica integridad de toda la cadena.

        Returns:
            True si la cadena es íntegra
        """
        expected_hash = self._calculate_chain_hash()
        return self.current_hash == expected_hash

    def get_entry(self, entry_id: str) -> Optional[HashChainEntry]:
        """Obtiene entrada por ID."""
        for entry in self.entries:
            if entry.entry_id == entry_id:
                return entry
        return None

    def get_entries_since(self, timestamp: float) -> List[HashChainEntry]:
        """Obtiene entradas desde un timestamp."""
        return [entry for entry in self.entries if entry.timestamp >= timestamp]

    def get_chain_info(self) -> Dict[str, Any]:
        """Obtiene información de la cadena."""
        return {
            "chain_id": self.chain_id,
            "chain_type": self.chain_type,
            "total_entries": len(self.entries),
            "current_hash": self.current_hash,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "is_integrity_valid": self.verify_integrity()
        }


class HashChainManager:
    """
    Gestor de múltiples cadenas de hash para diferentes tipos de logs.
    Proporciona integridad verificable para logs críticos del sistema.
    """

    def __init__(self):
        self.chains: Dict[str, HashChain] = {}
        self.lock = threading.Lock()
        self.secret_key = os.getenv('HASH_CHAIN_SECRET', 'ailoos_default_secret')

        # Crear cadenas por defecto
        self._initialize_default_chains()

        logger.info(f"🔐 HashChainManager initialized with {len(self.chains)} default chains")

    def _initialize_default_chains(self):
        """Inicializa cadenas de hash por defecto."""
        default_chains = [
            ("audit_logs", "Registro de operaciones de auditoría"),
            ("security_events", "Eventos de seguridad"),
            ("compliance_data", "Datos de cumplimiento normativo"),
            ("user_actions", "Acciones de usuarios"),
            ("system_metrics", "Métricas del sistema"),
            ("api_requests", "Solicitudes a APIs")
        ]

        for chain_id, description in default_chains:
            self.chains[chain_id] = HashChain(
                chain_id=chain_id,
                chain_type=description
            )

    def get_or_create_chain(self, chain_id: str, chain_type: str = "custom") -> HashChain:
        """
        Obtiene o crea una cadena de hash.

        Args:
            chain_id: ID de la cadena
            chain_type: Tipo de cadena

        Returns:
            Instancia de HashChain
        """
        with self.lock:
            if chain_id not in self.chains:
                self.chains[chain_id] = HashChain(
                    chain_id=chain_id,
                    chain_type=chain_type
                )
                logger.info(f"🆕 Created new hash chain: {chain_id} ({chain_type})")

            return self.chains[chain_id]

    def add_log_entry(self, chain_id: str, data: Any,
                     metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Añade entrada de log a una cadena específica.

        Args:
            chain_id: ID de la cadena
            data: Datos del log
            metadata: Metadata adicional

        Returns:
            ID de la entrada creada
        """
        chain = self.get_or_create_chain(chain_id)
        return chain.add_entry(data, metadata)

    def verify_chain_integrity(self, chain_id: str) -> bool:
        """
        Verifica integridad de una cadena específica.

        Args:
            chain_id: ID de la cadena

        Returns:
            True si la cadena es íntegra
        """
        chain = self.chains.get(chain_id)
        if not chain:
            return False

        is_valid = chain.verify_integrity()
        if not is_valid:
            logger.error("❌ Hash chain integrity violation detected in %s", chain_id)

        return is_valid

    def verify_all_chains(self) -> Dict[str, bool]:
        """
        Verifica integridad de todas las cadenas.

        Returns:
            Diccionario con estado de cada cadena
        """
        results = {}
        for chain_id, chain in self.chains.items():
            results[chain_id] = chain.verify_integrity()

        invalid_chains = [cid for cid, valid in results.items() if not valid]
        if invalid_chains:
            logger.error("❌ Integrity violations in chains: %s", invalid_chains)

        return results

    def get_chain_info(self, chain_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene información de una cadena específica."""
        chain = self.chains.get(chain_id)
        return chain.get_chain_info() if chain else None

    def get_all_chains_info(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene información de todas las cadenas."""
        return {chain_id: chain.get_chain_info() for chain_id, chain in self.chains.items()}

    def search_entries(self, chain_id: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Busca entradas en una cadena por filtros.

        Args:
            chain_id: ID de la cadena
            filters: Filtros de búsqueda

        Returns:
            Lista de entradas que coinciden
        """
        chain = self.chains.get(chain_id)
        if not chain:
            return []

        results = []
        for entry in chain.entries:
            match = True

            for key, value in filters.items():
                if key == "timestamp_from" and entry.timestamp < value:
                    match = False
                    break
                elif key == "timestamp_to" and entry.timestamp > value:
                    match = False
                    break
                elif key in entry.metadata and entry.metadata[key] != value:
                    match = False
                    break

            if match:
                results.append(entry.to_dict())

        return results

    def create_integrity_proof(self, chain_id: str, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        Crea prueba de integridad para una entrada específica.

        Args:
            chain_id: ID de la cadena
            entry_id: ID de la entrada

        Returns:
            Prueba de integridad o None si no existe
        """
        chain = self.chains.get(chain_id)
        if not chain:
            return None

        entry = chain.get_entry(entry_id)
        if not entry:
            return None

        # Crear HMAC para autenticación
        proof_data = {
            "chain_id": chain_id,
            "entry_id": entry_id,
            "entry_hash": entry.calculate_hash(),
            "chain_hash": chain.current_hash,
            "timestamp": time.time()
        }

        proof_str = json.dumps(proof_data, sort_keys=True, default=str)
        proof_signature = hmac.new(
            self.secret_key.encode(),
            proof_str.encode(),
            hashlib.sha256
        ).hexdigest()

        return {
            **proof_data,
            "signature": proof_signature,
            "is_valid": chain.verify_integrity()
        }

    def export_chain(self, chain_id: str) -> Optional[Dict[str, Any]]:
        """
        Exporta una cadena completa para backup o auditoría externa.

        Args:
            chain_id: ID de la cadena

        Returns:
            Datos exportados de la cadena
        """
        chain = self.chains.get(chain_id)
        if not chain:
            return None

        return {
            "chain_info": chain.get_chain_info(),
            "entries": [entry.to_dict() for entry in chain.entries],
            "export_timestamp": time.time(),
            "integrity_verified": chain.verify_integrity()
        }

    def import_chain(self, chain_data: Dict[str, Any]) -> bool:
        """
        Importa una cadena desde datos exportados.

        Args:
            chain_data: Datos de la cadena exportada

        Returns:
            True si la importación fue exitosa
        """
        try:
            chain_info = chain_data["chain_info"]
            entries_data = chain_data["entries"]

            # Recrear entradas
            entries = []
            for entry_data in entries_data:
                entry = HashChainEntry(**entry_data)
                entries.append(entry)

            # Recrear cadena
            chain = HashChain(
                chain_id=chain_info["chain_id"],
                chain_type=chain_info["chain_type"],
                entries=entries,
                current_hash=chain_info["current_hash"],
                created_at=chain_info["created_at"],
                last_updated=chain_info["last_updated"]
            )

            # Verificar integridad antes de importar
            if not chain.verify_integrity():
                logger.error("❌ Imported chain %s has integrity violations", chain.chain_id)
                return False

            with self.lock:
                self.chains[chain.chain_id] = chain

            logger.info("✅ Successfully imported hash chain %s", chain.chain_id)
            return True

        except Exception as e:
            logger.error("❌ Error importing hash chain: %s", e)
            return False


# Instancia global del gestor de hash chains
hash_chain_manager = HashChainManager()


def get_hash_chain_manager() -> HashChainManager:
    """Obtiene instancia global del gestor de hash chains."""
    return hash_chain_manager