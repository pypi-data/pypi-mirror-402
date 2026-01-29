"""
Blockchain privada para auditoría inmutable de operaciones críticas en AILOOS.
Implementa una blockchain simple con proof-of-work básico para registro inmutable.
"""

import hashlib
import json
import time
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AuditBlock:
    """Bloque de auditoría con operaciones críticas."""
    index: int
    timestamp: float
    operations: List[Dict[str, Any]]
    previous_hash: str
    nonce: int = 0
    hash: str = ""
    merkle_root: str = ""

    def __post_init__(self):
        if not self.hash:
            self.hash = self.calculate_hash()
        if not self.merkle_root:
            self.merkle_root = self.calculate_merkle_root()

    def calculate_hash(self) -> str:
        """Calcula hash del bloque."""
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "operations": self.operations,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "merkle_root": self.merkle_root
        }, sort_keys=True, default=str)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def calculate_merkle_root(self) -> str:
        """Calcula raíz Merkle de las operaciones."""
        if not self.operations:
            return hashlib.sha256(b"empty").hexdigest()

        # Crear lista de hashes de operaciones
        hashes = []
        for op in self.operations:
            op_string = json.dumps(op, sort_keys=True, default=str)
            hashes.append(hashlib.sha256(op_string.encode()).hexdigest())

        # Construir árbol Merkle
        while len(hashes) > 1:
            if len(hashes) % 2 == 1:
                hashes.append(hashes[-1])  # Duplicar último hash si impar

            new_hashes = []
            for i in range(0, len(hashes), 2):
                combined = hashes[i] + hashes[i + 1]
                new_hashes.append(hashlib.sha256(combined.encode()).hexdigest())
            hashes = new_hashes

        return hashes[0]

    def mine_block(self, difficulty: int = 4) -> None:
        """Minado simple del bloque."""
        target = "0" * difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()


@dataclass
class AuditOperation:
    """Operación crítica para auditar."""
    operation_id: str
    operation_type: str
    user_id: str
    timestamp: float
    data: Dict[str, Any]
    signature: Optional[str] = None
    compliance_flags: List[str] = None

    def __post_init__(self):
        if self.compliance_flags is None:
            self.compliance_flags = []

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return asdict(self)


class BlockchainAuditor:
    """
    Auditor blockchain privada para registro inmutable de operaciones críticas.
    Implementa blockchain con proof-of-work y validación de integridad.
    """

    def __init__(self, difficulty: int = 4, max_block_size: int = 100):
        self.chain: List[AuditBlock] = []
        self.pending_operations: List[AuditOperation] = []
        self.difficulty = difficulty
        self.max_block_size = max_block_size
        self.lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=2)

        # Crear bloque génesis
        self._create_genesis_block()

        logger.info(f"🔗 BlockchainAuditor initialized with difficulty {difficulty}")

    def _create_genesis_block(self) -> None:
        """Crea el bloque génesis."""
        genesis_operation = AuditOperation(
            operation_id="genesis",
            operation_type="system_init",
            user_id="system",
            timestamp=time.time(),
            data={"message": "AILOOS Audit Blockchain Genesis Block"}
        )

        genesis_block = AuditBlock(
            index=0,
            timestamp=time.time(),
            operations=[genesis_operation.to_dict()],
            previous_hash="0"
        )
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)

    async def add_operation(self, operation: AuditOperation) -> str:
        """
        Añade operación crítica a la blockchain.

        Args:
            operation: Operación a registrar

        Returns:
            Hash del bloque donde se incluyó la operación
        """
        with self.lock:
            self.pending_operations.append(operation)

            # Si hay suficientes operaciones, crear nuevo bloque
            if len(self.pending_operations) >= self.max_block_size:
                return await self._mine_new_block()

        return "pending"

    async def _mine_new_block(self) -> str:
        """Mina un nuevo bloque con las operaciones pendientes."""
        if not self.pending_operations:
            return ""

        # Preparar operaciones para el bloque
        operations_data = [op.to_dict() for op in self.pending_operations]

        # Crear nuevo bloque
        new_block = AuditBlock(
            index=len(self.chain),
            timestamp=time.time(),
            operations=operations_data,
            previous_hash=self.chain[-1].hash
        )

        # Minar bloque en thread pool para no bloquear
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, new_block.mine_block, self.difficulty)

        # Añadir bloque a la cadena
        with self.lock:
            self.chain.append(new_block)
            self.pending_operations.clear()

        logger.info(f"⛏️ Mined new audit block #{new_block.index} with {len(operations_data)} operations")

        return new_block.hash

    def get_block(self, block_hash: str) -> Optional[AuditBlock]:
        """Obtiene bloque por hash."""
        for block in self.chain:
            if block.hash == block_hash:
                return block
        return None

    def get_block_by_index(self, index: int) -> Optional[AuditBlock]:
        """Obtiene bloque por índice."""
        if 0 <= index < len(self.chain):
            return self.chain[index]
        return None

    def validate_chain(self) -> bool:
        """Valida integridad de toda la cadena."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # Verificar hash del bloque actual
            if current.hash != current.calculate_hash():
                logger.error("❌ Block #%d hash mismatch", i)
                return False

            # Verificar conexión con bloque anterior
            if current.previous_hash != previous.hash:
                logger.error("❌ Block #%d previous hash mismatch", i)
                return False

            # Verificar proof-of-work
            if not current.hash.startswith("0" * self.difficulty):
                logger.error("❌ Block #%d invalid proof-of-work", i)
                return False

            # Verificar Merkle root
            if current.merkle_root != current.calculate_merkle_root():
                logger.error("❌ Block #%d Merkle root mismatch", i)
                return False

        logger.info("✅ Blockchain validation successful")
        return True

    def get_chain_info(self) -> Dict[str, Any]:
        """Obtiene información general de la cadena."""
        return {
            "total_blocks": len(self.chain),
            "total_operations": sum(len(block.operations) for block in self.chain),
            "pending_operations": len(self.pending_operations),
            "difficulty": self.difficulty,
            "latest_block_hash": self.chain[-1].hash if self.chain else None,
            "is_valid": self.validate_chain()
        }

    def search_operations(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Busca operaciones en la blockchain por filtros.

        Args:
            filters: Diccionario con filtros (operation_type, user_id, date_range, etc.)

        Returns:
            Lista de operaciones que coinciden
        """
        results = []

        for block in self.chain:
            for operation in block.operations:
                match = True

                for key, value in filters.items():
                    if key == "date_from" and operation.get("timestamp", 0) < value:
                        match = False
                        break
                    elif key == "date_to" and operation.get("timestamp", 0) > value:
                        match = False
                        break
                    elif key in operation and operation[key] != value:
                        match = False
                        break

                if match:
                    results.append({
                        **operation,
                        "block_hash": block.hash,
                        "block_index": block.index,
                        "confirmed_at": block.timestamp
                    })

        return results

    async def force_mine_block(self) -> str:
        """Fuerza la creación de un nuevo bloque aunque no esté lleno."""
        with self.lock:
            if not self.pending_operations:
                return ""

        return await self._mine_new_block()

    def get_operation_proof(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene prueba de existencia de una operación en la blockchain.

        Returns:
            Prueba con block hash, Merkle proof, etc.
        """
        for block in self.chain:
            for i, operation in enumerate(block.operations):
                if operation.get("operation_id") == operation_id:
                    return {
                        "operation_id": operation_id,
                        "block_hash": block.hash,
                        "block_index": block.index,
                        "merkle_root": block.merkle_root,
                        "operation_index": i,
                        "timestamp": block.timestamp,
                        "confirmations": len(self.chain) - block.index - 1
                    }
        return None


# Instancia global del auditor blockchain
blockchain_auditor = BlockchainAuditor()


def get_blockchain_auditor() -> BlockchainAuditor:
    """Obtiene instancia global del auditor blockchain."""
    return blockchain_auditor