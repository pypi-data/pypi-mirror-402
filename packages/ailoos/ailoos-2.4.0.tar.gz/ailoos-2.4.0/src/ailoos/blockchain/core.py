"""
Blockchain Core - Implementación completa de blockchain con criptografía real
Incluye proof-of-work, criptografía asimétrica, wallets y transacciones verificadas.
"""

import hashlib
import os
import json
import time
import secrets
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding, ec
from cryptography.hazmat.primitives.asymmetric.utils import Prehashed
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
import base64

from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Transaction:
    """Transacción blockchain con firma digital."""
    tx_id: str
    sender: str  # Dirección del remitente (hash de clave pública)
    recipient: str  # Dirección del destinatario
    amount: float
    timestamp: float
    signature: Optional[str] = None
    public_key: Optional[str] = None
    nonce: int = 0
    data: Dict[str, Any] = None

    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if not self.tx_id:
            self.tx_id = self.calculate_hash()

    def calculate_hash(self) -> str:
        """Calcula hash de la transacción."""
        tx_data = {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "data": self.data
        }
        tx_string = json.dumps(tx_data, sort_keys=True, default=str)
        return hashlib.sha256(tx_string.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return asdict(self)

    def sign(self, private_key_pem: str) -> None:
        """Firma la transacción con clave privada."""
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None,
            backend=default_backend()
        )

        # Datos a firmar (hash de la transacción)
        tx_hash = self.calculate_hash().encode()

        # Firmar usando PSS padding
        signature = private_key.sign(
            tx_hash,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        self.signature = base64.b64encode(signature).decode()
        self.public_key = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

    def verify_signature(self) -> bool:
        """Verifica la firma de la transacción."""
        if not self.signature or not self.public_key:
            return False

        try:
            # Cargar clave pública
            public_key = serialization.load_pem_public_key(
                self.public_key.encode(),
                backend=default_backend()
            )

            # Datos firmados
            tx_hash = self.calculate_hash().encode()
            signature = base64.b64decode(self.signature)

            # Verificar firma
            public_key.verify(
                signature,
                tx_hash,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True

        except (InvalidSignature, Exception) as e:
            logger.warning(f"Signature verification failed: {e}")
            return False


@dataclass
class Block:
    """Bloque blockchain con proof-of-work real."""
    index: int
    timestamp: float
    transactions: List[Transaction]
    previous_hash: str
    nonce: int = 0
    hash: str = ""
    merkle_root: str = ""
    difficulty: int = 4

    def __post_init__(self):
        if not self.hash:
            self.hash = self.calculate_hash()
        if not self.merkle_root:
            self.merkle_root = self.calculate_merkle_root()

    def calculate_hash(self) -> str:
        """Calcula hash del bloque con proof-of-work."""
        block_data = {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "merkle_root": self.merkle_root
        }
        block_string = json.dumps(block_data, sort_keys=True, default=str)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def calculate_merkle_root(self) -> str:
        """Calcula raíz Merkle de las transacciones."""
        if not self.transactions:
            return hashlib.sha256(b"empty").hexdigest()

        # Crear lista de hashes de transacciones
        hashes = [tx.calculate_hash() for tx in self.transactions]

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

    def mine_block(self) -> None:
        """Minado real del bloque con proof-of-work."""
        target = "0" * self.difficulty
        start_time = time.time()

        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()

            # Protección contra bucle infinito (aunque muy improbable)
            if time.time() - start_time > 300:  # 5 minutos máximo
                logger.warning(f"Block mining timeout for block {self.index}")
                break

    def is_valid(self) -> bool:
        """Verifica si el bloque es válido."""
        # Verificar hash
        if self.hash != self.calculate_hash():
            return False

        # Verificar proof-of-work
        if not self.hash.startswith("0" * self.difficulty):
            return False

        # Verificar Merkle root
        if self.merkle_root != self.calculate_merkle_root():
            return False

        # Verificar todas las firmas de transacciones
        for tx in self.transactions:
            if not tx.verify_signature():
                logger.warning(f"Invalid signature in transaction {tx.tx_id}")
                return False

        return True


@dataclass
class Wallet:
    """Wallet con criptografía asimétrica real."""
    address: str
    public_key: str
    private_key: Optional[str] = None  # Solo en wallets locales
    balance: float = 0.0
    nonce: int = 0

    @classmethod
    def create_wallet(cls) -> 'Wallet':
        """Crea una nueva wallet con claves generadas."""
        # Generar clave privada RSA
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # Obtener clave pública
        public_key = private_key.public_key()

        # Calcular dirección (hash de clave pública)
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        address = hashlib.sha256(public_key_pem).hexdigest()

        # Clave privada en formato PEM
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()

        return cls(
            address=address,
            public_key=public_key_pem.decode(),
            private_key=private_key_pem,
            balance=0.0,
            nonce=0
        )

    def sign_transaction(self, tx: Transaction) -> None:
        """Firma una transacción con la clave privada de la wallet."""
        if not self.private_key:
            raise ValueError("Wallet does not have private key")

        tx.sign(self.private_key)

    def create_transaction(self, recipient: str, amount: float, data: Dict[str, Any] = None) -> Transaction:
        """Crea una transacción desde esta wallet."""
        tx = Transaction(
            tx_id="",
            sender=self.address,
            recipient=recipient,
            amount=amount,
            timestamp=time.time(),
            nonce=self.nonce,
            data=data or {}
        )

        # Incrementar nonce
        self.nonce += 1

        return tx


class Blockchain:
    """
    Blockchain completa con proof-of-work real y criptografía asimétrica.

    Características:
    - Proof-of-work real con dificultad ajustable
    - Criptografía asimétrica (RSA) para firmas
    - Merkle trees para integridad
    - Validación completa de transacciones
    - Gestión de wallets con claves reales
    """

    def __init__(self, difficulty: int = 4, block_time: int = 60):
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.wallets: Dict[str, Wallet] = {}
        self.difficulty = difficulty
        self.block_time = block_time  # Tiempo objetivo entre bloques en segundos
        self.mining_reward = 10.0  # Recompensa por minar bloque

        self.lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.mining_active = False

        # Crear bloque génesis
        self._create_genesis_block()

        logger.info(f"🔗 Blockchain initialized with difficulty {difficulty}")

    def _create_genesis_block(self) -> None:
        """Crea el bloque génesis."""
        # Transacción génesis
        genesis_tx = Transaction(
            tx_id="genesis",
            sender="0",
            recipient="network",
            amount=1000000.0,  # Suministro inicial
            timestamp=time.time(),
            data={"type": "genesis", "message": "AILOOS Blockchain Genesis Block"}
        )

        genesis_block = Block(
            index=0,
            timestamp=time.time(),
            transactions=[genesis_tx],
            previous_hash="0",
            difficulty=self.difficulty
        )

        # El bloque génesis no requiere minado
        genesis_block.hash = genesis_block.calculate_hash()
        self.chain.append(genesis_block)

        # Crear wallet de red
        network_wallet = Wallet.create_wallet()
        network_wallet.address = "network"
        network_wallet.balance = 1000000.0
        self.wallets["network"] = network_wallet

        logger.info("🎯 Genesis block created")

    def create_wallet(self) -> Wallet:
        """Crea una nueva wallet."""
        wallet = Wallet.create_wallet()
        self.wallets[wallet.address] = wallet
        logger.info(f"👛 New wallet created: {wallet.address[:16]}...")
        return wallet

    def get_wallet(self, address: str) -> Optional[Wallet]:
        """Obtiene wallet por dirección."""
        return self.wallets.get(address)

    def add_transaction(self, transaction: Transaction) -> bool:
        """
        Añade transacción a la lista de pendientes.

        Args:
            transaction: Transacción a añadir

        Returns:
            True si se añadió correctamente
        """
        # Validar transacción
        if not self._validate_transaction(transaction):
            return False

        with self.lock:
            self.pending_transactions.append(transaction)

        logger.info(f"📝 Transaction added: {transaction.tx_id[:16]}... ({transaction.amount} tokens)")
        return True

    def _validate_transaction(self, tx: Transaction) -> bool:
        """Valida una transacción."""
        # Verificar firma
        if not tx.verify_signature():
            logger.warning(f"Invalid signature for transaction {tx.tx_id}")
            return False

        # Verificar balance del remitente
        sender_wallet = self.get_wallet(tx.sender)
        if not sender_wallet:
            logger.warning(f"Sender wallet not found: {tx.sender}")
            return False

        if sender_wallet.balance < tx.amount:
            logger.warning(f"Insufficient balance: {sender_wallet.balance} < {tx.amount}")
            return False

        # Verificar nonce
        if tx.nonce != sender_wallet.nonce:
            logger.warning(f"Invalid nonce: {tx.nonce} != {sender_wallet.nonce}")
            return False

        return True

    async def mine_block(self, miner_address: str) -> Optional[Block]:
        """
        Mina un nuevo bloque.

        Args:
            miner_address: Dirección del minero que recibe la recompensa

        Returns:
            Nuevo bloque minado o None si no hay transacciones
        """
        with self.lock:
            if not self.pending_transactions:
                return None

            # Preparar transacciones para el bloque
            block_transactions = self.pending_transactions.copy()

            # Añadir transacción de recompensa
            reward_tx = Transaction(
                tx_id=f"reward_{len(self.chain)}_{int(time.time())}",
                sender="network",
                recipient=miner_address,
                amount=self.mining_reward,
                timestamp=time.time(),
                data={"type": "mining_reward", "block_index": len(self.chain)}
            )
            block_transactions.append(reward_tx)

            # Crear nuevo bloque
            new_block = Block(
                index=len(self.chain),
                timestamp=time.time(),
                transactions=block_transactions,
                previous_hash=self.chain[-1].hash,
                difficulty=self.difficulty
            )

        # Minar bloque en thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, new_block.mine_block)

        # Añadir bloque a la cadena
        with self.lock:
            self.chain.append(new_block)
            self.pending_transactions.clear()

            # Actualizar balances
            self._update_balances(block_transactions)

        mining_time = time.time() - new_block.timestamp
        logger.info(f"⛏️ Block #{new_block.index} mined in {mining_time:.2f}s with nonce {new_block.nonce}")
        logger.info(f"💰 Mining reward sent to {miner_address[:16]}...")

        return new_block

    def _update_balances(self, transactions: List[Transaction]) -> None:
        """Actualiza balances después de confirmar transacciones."""
        for tx in transactions:
            # Deduct from sender (except for rewards)
            if tx.sender != "network":
                sender_wallet = self.get_wallet(tx.sender)
                if sender_wallet:
                    sender_wallet.balance -= tx.amount

            # Add to recipient
            recipient_wallet = self.get_wallet(tx.recipient)
            if recipient_wallet:
                recipient_wallet.balance += tx.amount
            else:
                # Crear wallet si no existe
                new_wallet = Wallet(
                    address=tx.recipient,
                    public_key="",  # No tenemos clave pública
                    balance=tx.amount
                )
                self.wallets[tx.recipient] = new_wallet

    def validate_chain(self) -> bool:
        """Valida integridad completa de la cadena."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # Verificar hash del bloque
            if not current.is_valid():
                logger.error(f"❌ Block #{i} is invalid")
                return False

            # Verificar conexión con bloque anterior
            if current.previous_hash != previous.hash:
                logger.error(f"❌ Block #{i} previous hash mismatch")
                return False

        logger.info("✅ Blockchain validation successful")
        return True

    def get_balance(self, address: str) -> float:
        """Obtiene balance de una dirección."""
        wallet = self.get_wallet(address)
        return wallet.balance if wallet else 0.0

    def get_block(self, block_index: int) -> Optional[Block]:
        """Obtiene bloque por índice."""
        if 0 <= block_index < len(self.chain):
            return self.chain[block_index]
        return None

    def get_transaction(self, tx_id: str) -> Optional[Tuple[Transaction, int, int]]:
        """
        Busca transacción por ID.

        Returns:
            Tupla de (transacción, block_index, tx_index) o None
        """
        for block_idx, block in enumerate(self.chain):
            for tx_idx, tx in enumerate(block.transactions):
                if tx.tx_id == tx_id:
                    return (tx, block_idx, tx_idx)
        return None

    def get_chain_info(self) -> Dict[str, Any]:
        """Obtiene información de la cadena."""
        total_transactions = sum(len(block.transactions) for block in self.chain)

        return {
            "total_blocks": len(self.chain),
            "total_transactions": total_transactions,
            "pending_transactions": len(self.pending_transactions),
            "difficulty": self.difficulty,
            "latest_block_hash": self.chain[-1].hash if self.chain else None,
            "total_wallets": len(self.wallets),
            "is_valid": self.validate_chain()
        }

    async def start_mining(self, miner_address: str) -> None:
        """Inicia minado continuo."""
        if self.mining_active:
            return

        self.mining_active = True
        logger.info(f"⛏️ Started continuous mining for {miner_address[:16]}...")

        while self.mining_active:
            try:
                block = await self.mine_block(miner_address)
                if block:
                    logger.info(f"✅ Block #{block.index} mined successfully")
                else:
                    # Esperar antes de intentar de nuevo
                    await asyncio.sleep(self.block_time)
            except Exception as e:
                logger.error(f"❌ Mining error: {e}")
                await asyncio.sleep(1)

    def stop_mining(self) -> None:
        """Detiene minado continuo."""
        self.mining_active = False
        logger.info("🛑 Mining stopped")

    def adjust_difficulty(self) -> None:
        """Ajusta dificultad basada en tiempo de bloque."""
        if len(self.chain) < 10:  # No ajustar hasta tener suficientes bloques
            return

        # Calcular tiempo promedio de los últimos 10 bloques
        recent_blocks = self.chain[-10:]
        total_time = recent_blocks[-1].timestamp - recent_blocks[0].timestamp
        avg_time = total_time / 9  # 9 intervalos entre 10 bloques

        # Ajustar dificultad
        if avg_time < self.block_time * 0.9:  # Muy rápido
            self.difficulty += 1
            logger.info(f"📈 Difficulty increased to {self.difficulty}")
        elif avg_time > self.block_time * 1.1:  # Muy lento
            self.difficulty = max(1, self.difficulty - 1)
            logger.info(f"📉 Difficulty decreased to {self.difficulty}")


    def save_to_disk(self, filepath: str = "storage/blockchain_data.json"):
        """Guardar estado de la blockchain en disco."""
        try:
            data = {
                "chain": [asdict(block) for block in self.chain],
                # Solo guardamos wallets públicas (direcciones y balances). 
                # Las claves privadas se manejan en WalletManager.
                "wallets": {
                    addr: {
                        "address": w.address,
                        "public_key": w.public_key,
                        "balance": w.balance,
                        "nonce": w.nonce
                    } for addr, w in self.wallets.items()
                },
                "difficulty": self.difficulty,
                "timestamp": time.time()
            }
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"💾 Blockchain state saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving blockchain: {e}")
            return False

    def load_from_disk(self, filepath: str = "storage/blockchain_data.json"):
        """Cargar estado de la blockchain desde disco."""
        try:
            if not os.path.exists(filepath):
                logger.warning("⚠️ No stored blockchain found, starting fresh.")
                return False

            with open(filepath, 'r') as f:
                data = json.load(f)

            # Restaurar cadena
            self.chain = []
            for block_data in data["chain"]:
                # Reconstruir objetos Transaction
                txs = [Transaction(**tx) for tx in block_data["transactions"]]
                block_data["transactions"] = txs
                self.chain.append(Block(**block_data))

            # Restaurar wallets (estado de ledger)
            self.wallets = {}
            for addr, w_data in data["wallets"].items():
                self.wallets[addr] = Wallet(**w_data)

            self.difficulty = data.get("difficulty", self.difficulty)
            
            logger.info(f"📂 Blockchain loaded: {len(self.chain)} blocks, {len(self.wallets)} wallets")
            return True
        except Exception as e:
            logger.error(f"❌ Error loading blockchain: {e}")
            return False


# Instancia global de blockchain
blockchain = Blockchain()


def get_blockchain() -> Blockchain:
    """Obtiene instancia global de blockchain."""
    return blockchain


async def create_transaction(
    sender_wallet: Wallet,
    recipient_address: str,
    amount: float,
    data: Dict[str, Any] = None
) -> Transaction:
    """
    Crea y firma una transacción.

    Args:
        sender_wallet: Wallet del remitente
        recipient_address: Dirección del destinatario
        amount: Cantidad a enviar
        data: Datos adicionales

    Returns:
        Transacción firmada
    """
    # Crear transacción
    tx = sender_wallet.create_transaction(recipient_address, amount, data)

    # Firmar
    sender_wallet.sign_transaction(tx)

    return tx


async def send_transaction(tx: Transaction) -> bool:
    """
    Envía transacción a la blockchain.

    Args:
        tx: Transacción a enviar

    Returns:
        True si se envió correctamente
    """
    blockchain = get_blockchain()
    return blockchain.add_transaction(tx)


def generate_keypair() -> Tuple[str, str]:
    """
    Genera un par de claves RSA.

    Returns:
        Tupla de (private_key_pem, public_key_pem)
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()

    return private_pem, public_pem


def address_from_public_key(public_key_pem: str) -> str:
    """
    Calcula dirección desde clave pública.

    Args:
        public_key_pem: Clave pública en formato PEM

    Returns:
        Dirección de la wallet
    """
    return hashlib.sha256(public_key_pem.encode()).hexdigest()