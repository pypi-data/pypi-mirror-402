import logging
import hashlib
import json
import time
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from enum import Enum

from .filecoin_client import FilecoinClient
from .arweave_client import ArweaveClient
from .storj_client import StorjClient

logger = logging.getLogger(__name__)

class StorageType(Enum):
    FILECOIN = "filecoin"
    ARWEAVE = "arweave"
    STORJ = "storj"

@dataclass
class StorageConfig:
    type: StorageType
    config: Dict[str, Any]
    enabled: bool = True
    priority: int = 1  # 1 = highest priority

@dataclass
class StorageResult:
    storage_type: StorageType
    identifier: str  # CID, TX ID, or key
    hash: str
    metadata: Dict[str, Any]

class StorageOrchestrator:
    """
    Orquestador multi-storage que gestiona almacenamiento distribuido
    seleccionando automáticamente el mejor storage basado en criterios.
    """

    def __init__(self, configs: List[StorageConfig]):
        """
        Inicializa el orquestador con configuraciones de storage.

        Args:
            configs: Lista de configuraciones de storage
        """
        self.configs = {config.type: config for config in configs}
        self.clients: Dict[StorageType, Any] = {}
        self._initialize_clients()

    def _initialize_clients(self):
        """Inicializa los clientes de storage habilitados."""
        for storage_type, config in self.configs.items():
            if not config.enabled:
                continue

            try:
                if storage_type == StorageType.FILECOIN:
                    client = FilecoinClient(**config.config)
                elif storage_type == StorageType.ARWEAVE:
                    client = ArweaveClient(**config.config)
                elif storage_type == StorageType.STORJ:
                    client = StorjClient(**config.config)
                else:
                    logger.warning(f"Tipo de storage desconocido: {storage_type}")
                    continue

                self.clients[storage_type] = client
                logger.info(f"Cliente {storage_type.value} inicializado")

            except Exception as e:
                logger.error(f"Error inicializando cliente {storage_type.value}: {e}")

    def store_data(self, data: bytes, criteria: Dict[str, Any] = None) -> StorageResult:
        """
        Almacena datos seleccionando automáticamente el mejor storage.

        Args:
            data: Datos a almacenar
            criteria: Criterios para selección (durability, cost, speed, etc.)

        Returns:
            Resultado del almacenamiento

        Raises:
            Exception: Si falla el almacenamiento
        """
        try:
            data_hash = hashlib.sha256(data).hexdigest()
            logger.info(f"Iniciando almacenamiento orquestado con hash: {data_hash}")

            # Seleccionar storage
            selected_storage = self._select_storage(data, criteria)
            if not selected_storage:
                raise Exception("No suitable storage available")

            client = self.clients[selected_storage]
            logger.info(f"Storage seleccionado: {selected_storage.value}")

            # Almacenar datos
            if selected_storage == StorageType.FILECOIN:
                # Para Filecoin, usar duración por defecto
                duration = criteria.get('duration', 525600)  # 1 año en minutos
                identifier = client.store_data(data, duration)

            elif selected_storage == StorageType.ARWEAVE:
                # Para Arweave, usar tags si se proporcionan
                tags = criteria.get('tags', [])
                identifier = client.store_data(data, tags)

            elif selected_storage == StorageType.STORJ:
                # Para Storj, generar clave única
                key = criteria.get('key', f"data_{data_hash}_{int(time.time())}")
                result = client.store_data(data, key)
                identifier = result.key

            # Crear metadata
            metadata = {
                'storage_type': selected_storage.value,
                'timestamp': int(time.time()),
                'size': len(data),
                'criteria': criteria or {}
            }

            result = StorageResult(
                storage_type=selected_storage,
                identifier=identifier,
                hash=data_hash,
                metadata=metadata
            )

            logger.info(f"Datos almacenados exitosamente en {selected_storage.value} con ID: {identifier}")
            return result

        except Exception as e:
            logger.error(f"Error en almacenamiento orquestado: {e}")
            raise

    def retrieve_data(self, storage_result: StorageResult) -> bytes:
        """
        Recupera datos desde el storage correspondiente.

        Args:
            storage_result: Resultado del almacenamiento original

        Returns:
            Datos recuperados

        Raises:
            Exception: Si falla la recuperación
        """
        try:
            storage_type = storage_result.storage_type
            identifier = storage_result.identifier

            logger.info(f"Recuperando datos desde {storage_type.value} con ID: {identifier}")

            client = self.clients.get(storage_type)
            if not client:
                raise Exception(f"Cliente no disponible para {storage_type.value}")

            if storage_type == StorageType.FILECOIN:
                data = client.retrieve_data(identifier)
            elif storage_type == StorageType.ARWEAVE:
                data = client.retrieve_data(identifier)
            elif storage_type == StorageType.STORJ:
                result = client.retrieve_data(identifier)
                data = result.data

            # Verificar integridad
            actual_hash = hashlib.sha256(data).hexdigest()
            if actual_hash != storage_result.hash:
                raise Exception(f"Integrity check failed. Expected: {storage_result.hash}, Got: {actual_hash}")

            logger.info(f"Datos recuperados exitosamente desde {storage_type.value}")
            return data

        except Exception as e:
            logger.error(f"Error recuperando datos: {e}")
            raise

    def verify_integrity(self, storage_result: StorageResult) -> bool:
        """
        Verifica la integridad de los datos almacenados.

        Args:
            storage_result: Resultado del almacenamiento

        Returns:
            True si la integridad es correcta
        """
        try:
            storage_type = storage_result.storage_type
            identifier = storage_result.identifier
            expected_hash = storage_result.hash

            client = self.clients.get(storage_type)
            if not client:
                return False

            return client.verify_integrity(identifier, expected_hash)

        except Exception as e:
            logger.error(f"Error verificando integridad: {e}")
            return False

    def estimate_cost(self, data_size: int, criteria: Dict[str, Any] = None) -> Dict[str, float]:
        """
        Estima costos para todos los storages disponibles.

        Args:
            data_size: Tamaño de los datos en bytes
            criteria: Criterios adicionales

        Returns:
            Diccionario con costos por storage
        """
        costs = {}
        criteria = criteria or {}

        for storage_type, client in self.clients.items():
            try:
                if storage_type == StorageType.FILECOIN:
                    duration = criteria.get('duration', 525600)
                    cost = client.estimate_cost(data_size, duration)
                elif storage_type == StorageType.ARWEAVE:
                    num_items = criteria.get('num_items', 1)
                    cost = client.estimate_cost(data_size, num_items)
                elif storage_type == StorageType.STORJ:
                    storage_days = criteria.get('storage_days', 30)
                    downloads_gb = criteria.get('downloads_gb', 0)
                    cost = client.estimate_cost(data_size, storage_days, downloads_gb)

                costs[storage_type.value] = cost

            except Exception as e:
                logger.warning(f"Error estimando costo para {storage_type.value}: {e}")
                costs[storage_type.value] = float('inf')

        return costs

    def _select_storage(self, data: bytes, criteria: Dict[str, Any] = None) -> Optional[StorageType]:
        """
        Selecciona el mejor storage basado en criterios.

        Args:
            data: Datos a almacenar
            criteria: Criterios de selección

        Returns:
            Tipo de storage seleccionado
        """
        criteria = criteria or {}

        # Criterios de selección
        durability = criteria.get('durability', 'medium')  # low, medium, high
        cost_sensitivity = criteria.get('cost_sensitivity', 'medium')  # low, medium, high
        speed_requirement = criteria.get('speed_requirement', 'medium')  # low, medium, high

        # Lógica de selección simplificada
        if durability == 'high':
            # Arweave para permanencia máxima
            if StorageType.ARWEAVE in self.clients:
                return StorageType.ARWEAVE
        elif speed_requirement == 'high':
            # Storj para velocidad
            if StorageType.STORJ in self.clients:
                return StorageType.STORJ
        elif durability == 'medium':
            # Filecoin para deals balanceados
            if StorageType.FILECOIN in self.clients:
                return StorageType.FILECOIN

        # Fallback: seleccionar por prioridad
        available_storages = [(t, c) for t, c in self.configs.items() if c.enabled and t in self.clients]
        if available_storages:
            return min(available_storages, key=lambda x: x[1].priority)[0]

        return None

    def get_storage_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene el estado de todos los storages.

        Returns:
            Estado de cada storage
        """
        status = {}

        for storage_type, client in self.clients.items():
            try:
                # Información básica de estado
                status[storage_type.value] = {
                    'enabled': True,
                    'healthy': True,
                    'type': storage_type.value
                }
            except Exception as e:
                status[storage_type.value] = {
                    'enabled': True,
                    'healthy': False,
                    'error': str(e)
                }

        # Agregar storages deshabilitados
        for storage_type, config in self.configs.items():
            if not config.enabled:
                status[storage_type.value] = {
                    'enabled': False,
                    'healthy': False
                }

        return status

    def replicate_data(self, storage_result: StorageResult, target_storages: List[StorageType] = None):
        """
        Replica datos a múltiples storages para redundancia.

        Args:
            storage_result: Resultado original del almacenamiento
            target_storages: Storages objetivo (todos si None)

        Raises:
            Exception: Si falla la replicación
        """
        try:
            # Recuperar datos originales
            data = self.retrieve_data(storage_result)

            target_storages = target_storages or [t for t in self.clients.keys() if t != storage_result.storage_type]

            replications = []
            for storage_type in target_storages:
                try:
                    # Crear criteria para replicación
                    criteria = {
                        'key': f"replica_{storage_result.identifier}_{storage_type.value}",
                        'tags': [{'name': 'replica-of', 'value': storage_result.identifier}]
                    }

                    result = self.store_data(data, criteria)
                    replications.append(result)

                    logger.info(f"Datos replicados a {storage_type.value}")

                except Exception as e:
                    logger.warning(f"Error replicando a {storage_type.value}: {e}")

            if not replications:
                raise Exception("No se pudo replicar a ningún storage")

            logger.info(f"Replicación completada a {len(replications)} storages")

        except Exception as e:
            logger.error(f"Error en replicación: {e}")
            raise

    def close(self):
        """Cierra todas las conexiones de storage."""
        for client in self.clients.values():
            try:
                if hasattr(client, 'close'):
                    client.close()
            except Exception as e:
                logger.warning(f"Error cerrando cliente: {e}")

        logger.info("Todas las conexiones de storage cerradas")