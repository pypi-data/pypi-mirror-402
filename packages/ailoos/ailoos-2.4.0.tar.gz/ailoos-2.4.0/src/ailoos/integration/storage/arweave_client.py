import logging
import hashlib
import json
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import arweave  # Requiere instalación: pip install arweave-python

logger = logging.getLogger(__name__)

@dataclass
class BundleItem:
    id: str
    data: bytes
    tags: List[Dict[str, str]]

@dataclass
class TransactionInfo:
    id: str
    status: str
    fee: int
    block_height: Optional[int]

class ArweaveClient:
    """
    Cliente para interactuar con Arweave para almacenamiento permanente con bundling.
    Maneja almacenamiento, recuperación, verificación de integridad y gestión de costos.
    """

    def __init__(self, wallet_path: str, bundler_url: str = "https://bundler.arweave.net"):
        """
        Inicializa el cliente Arweave.

        Args:
            wallet_path: Ruta al archivo de wallet JSON
            bundler_url: URL del bundler (opcional)
        """
        self.wallet_path = wallet_path
        self.bundler_url = bundler_url
        self.wallet = None
        self.arweave = arweave.Arweave()

        self._load_wallet()

    def _load_wallet(self):
        """Carga la wallet desde el archivo."""
        try:
            with open(self.wallet_path, 'r') as f:
                wallet_data = json.load(f)
            self.wallet = arweave.Wallet(wallet_data)
            logger.info("Wallet cargada exitosamente")
        except Exception as e:
            logger.error(f"Error cargando wallet: {e}")
            raise

    def store_data(self, data: bytes, tags: List[Dict[str, str]] = None) -> str:
        """
        Almacena datos en Arweave usando bundling.

        Args:
            data: Datos a almacenar
            tags: Tags adicionales para la transacción

        Returns:
            ID de la transacción

        Raises:
            Exception: Si falla el almacenamiento
        """
        try:
            data_hash = hashlib.sha256(data).hexdigest()
            logger.info(f"Iniciando almacenamiento de datos con hash: {data_hash}")

            # Crear transacción
            transaction = arweave.Transaction(self.wallet, data=data)

            # Agregar tags
            if tags:
                for tag in tags:
                    transaction.add_tag(tag['name'], tag['value'])

            # Agregar tag de hash para integridad
            transaction.add_tag('Data-Hash', data_hash)

            # Firmar transacción
            transaction.sign()

            # Enviar transacción
            result = transaction.send()

            if result['status'] != 200:
                raise Exception(f"Failed to send transaction: {result}")

            tx_id = transaction.id
            logger.info(f"Transacción enviada con ID: {tx_id}")

            # Esperar confirmación
            self._wait_for_confirmation(tx_id)

            return tx_id

        except Exception as e:
            logger.error(f"Error almacenando datos en Arweave: {e}")
            raise

    def store_bundle(self, items: List[BundleItem]) -> str:
        """
        Almacena múltiples items en un bundle de Arweave.

        Args:
            items: Lista de items a bundlear

        Returns:
            ID del bundle

        Raises:
            Exception: Si falla el bundling
        """
        try:
            logger.info(f"Creando bundle con {len(items)} items")

            # Crear bundle
            bundle = arweave.Bundle()

            for item in items:
                bundle_item = arweave.BundleItem(data=item.data)
                if item.tags:
                    for tag in item.tags:
                        bundle_item.add_tag(tag['name'], tag['value'])
                bundle.add_item(bundle_item)

            # Crear transacción del bundle
            transaction = arweave.BundleTransaction(bundle, self.wallet)
            transaction.sign()

            # Enviar
            result = transaction.send()

            if result['status'] != 200:
                raise Exception(f"Failed to send bundle: {result}")

            bundle_id = transaction.id
            logger.info(f"Bundle enviado con ID: {bundle_id}")

            self._wait_for_confirmation(bundle_id)

            return bundle_id

        except Exception as e:
            logger.error(f"Error creando bundle en Arweave: {e}")
            raise

    def retrieve_data(self, tx_id: str) -> bytes:
        """
        Recupera datos desde Arweave usando el ID de transacción.

        Args:
            tx_id: ID de la transacción

        Returns:
            Datos recuperados

        Raises:
            Exception: Si falla la recuperación
        """
        try:
            logger.info(f"Recuperando datos de transacción: {tx_id}")

            transaction = self.arweave.transactions.get(tx_id)
            data = transaction.get_data()

            logger.info(f"Datos recuperados exitosamente de transacción: {tx_id}")
            return data

        except Exception as e:
            logger.error(f"Error recuperando datos desde Arweave: {e}")
            raise

    def retrieve_bundle_items(self, bundle_id: str) -> List[bytes]:
        """
        Recupera items de un bundle.

        Args:
            bundle_id: ID del bundle

        Returns:
            Lista de datos de los items

        Raises:
            Exception: Si falla la recuperación
        """
        try:
            logger.info(f"Recuperando items del bundle: {bundle_id}")

            bundle = self.arweave.bundles.get(bundle_id)
            items_data = []

            for item in bundle.items:
                items_data.append(item.get_data())

            logger.info(f"Items recuperados exitosamente del bundle: {bundle_id}")
            return items_data

        except Exception as e:
            logger.error(f"Error recuperando bundle desde Arweave: {e}")
            raise

    def verify_integrity(self, tx_id: str, expected_hash: str) -> bool:
        """
        Verifica la integridad de los datos almacenados comparando hashes.

        Args:
            tx_id: ID de la transacción
            expected_hash: Hash SHA256 esperado

        Returns:
            True si la integridad es correcta, False en caso contrario
        """
        try:
            logger.info(f"Verificando integridad de transacción: {tx_id}")

            data = self.retrieve_data(tx_id)
            actual_hash = hashlib.sha256(data).hexdigest()

            is_valid = actual_hash == expected_hash
            if not is_valid:
                logger.warning(f"Integridad comprometida. Esperado: {expected_hash}, Actual: {actual_hash}")
            else:
                logger.info("Integridad verificada correctamente")

            return is_valid

        except Exception as e:
            logger.error(f"Error verificando integridad: {e}")
            return False

    def estimate_cost(self, data_size: int, num_items: int = 1) -> float:
        """
        Estima el costo de almacenamiento en AR.

        Args:
            data_size: Tamaño total de los datos en bytes
            num_items: Número de items (afecta fees de bundle)

        Returns:
            Costo estimado en AR
        """
        try:
            # Obtener precio base por byte
            price_per_byte = self.arweave.price.get_price(data_size)

            # Fee adicional por transacción/bundle
            base_fee = 0.000000000001 * num_items  # Aproximado

            total_cost = price_per_byte + base_fee

            # Convertir winstons a AR
            total_ar = total_cost / 1000000000000

            logger.info(f"Costo estimado: {total_ar} AR para {data_size} bytes en {num_items} items")
            return total_ar

        except Exception as e:
            logger.error(f"Error estimando costo: {e}")
            # Valor por defecto aproximado
            return (data_size / 1000000) * 0.0001  # ~0.0001 AR por MB

    def get_transaction_status(self, tx_id: str) -> TransactionInfo:
        """
        Obtiene el estado de una transacción.

        Args:
            tx_id: ID de la transacción

        Returns:
            Información de la transacción
        """
        try:
            status = self.arweave.transactions.get_status(tx_id)
            return TransactionInfo(
                id=tx_id,
                status=status['status'],
                fee=int(status.get('fee', 0)),
                block_height=status.get('block_height')
            )
        except Exception as e:
            logger.error(f"Error obteniendo estado de transacción: {e}")
            raise

    def _wait_for_confirmation(self, tx_id: str, timeout: int = 600):
        """Espera confirmación de la transacción."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                status = self.get_transaction_status(tx_id)
                if status.status == 'confirmed':
                    logger.info(f"Transacción {tx_id} confirmada")
                    return
                elif status.status == 'failed':
                    raise Exception(f"Transaction {tx_id} failed")
            except Exception as e:
                logger.warning(f"Error checking transaction status: {e}")

            time.sleep(30)

        raise Exception(f"Transacción {tx_id} no se confirmó en {timeout} segundos")