"""
Dataset Exchange para Federated Learning
Implementa intercambio seguro y privado de datasets entre nodos federados.
"""

import asyncio
import hashlib
import json
import time
import uuid
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import logging

from ...core.logging import get_logger
from ...federated.node_communicator import NodeCommunicator
from ...infrastructure.ipfs_embedded import IPFSManager
from ...federated.differential_privacy import DifferentialPrivacyEngine
from ...federated.homomorphic_encryption import HomomorphicEncryptionManager

logger = get_logger(__name__)


@dataclass
class FederatedDataset:
    """Dataset federado compuesto de shards de múltiples nodos."""
    dataset_id: str
    name: str
    description: str
    shards: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # node_id -> shard_info
    metadata: Dict[str, Any] = field(default_factory=dict)
    total_samples: int = 0
    features: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    privacy_level: str = "high"  # low, medium, high
    ipfs_cid: Optional[str] = None


@dataclass
class DatasetShard:
    """Shard individual de dataset."""
    shard_id: str
    node_id: str
    dataset_id: str
    sample_count: int
    features: List[str]
    hash_salt: str = field(default_factory=lambda: str(uuid.uuid4()))
    privacy_metadata: Dict[str, Any] = field(default_factory=dict)
    ipfs_cid: Optional[str] = None
    created_at: float = field(default_factory=time.time)


class DatasetExchange:
    """
    Exchange para datasets federados con sharding y privacidad preservada.
    Coordina la creación y distribución de datasets entre nodos federados.
    """

    def __init__(self, node_communicator: NodeCommunicator,
                 ipfs_manager: IPFSManager,
                 privacy_engine: Optional[DifferentialPrivacyEngine] = None,
                 encryption_manager: Optional[HomomorphicEncryptionManager] = None,
                 max_concurrent_operations: int = 5):
        """
        Inicializar DatasetExchange.

        Args:
            node_communicator: Comunicador para coordinación con nodos
            ipfs_manager: Gestor IPFS para persistencia
            privacy_engine: Motor de privacidad diferencial
            encryption_manager: Gestor de encriptación homomórfica
            max_concurrent_operations: Máximo de operaciones concurrentes
        """
        self.node_communicator = node_communicator
        self.ipfs_manager = ipfs_manager
        self.privacy_engine = privacy_engine
        self.encryption_manager = encryption_manager

        # Gestión de datasets
        self.datasets: Dict[str, FederatedDataset] = {}
        self.shards: Dict[str, DatasetShard] = {}

        # Configuración
        self.max_concurrent_operations = max_concurrent_operations
        self.chunk_size = 1024 * 1024  # 1MB para procesamiento de datasets grandes
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_operations)

        # Estadísticas
        self.stats = {
            'datasets_created': 0,
            'shards_created': 0,
            'total_samples_processed': 0,
            'privacy_operations': 0,
            'ipfs_operations': 0
        }

        logger.info("🚀 DatasetExchange initialized")

    async def create_federated_dataset(self, name: str, description: str,
                                     participant_nodes: List[str],
                                     dataset_requirements: Dict[str, Any],
                                     privacy_level: str = "high") -> str:
        """
        Crear dataset federado coordinando con múltiples nodos.

        Args:
            name: Nombre del dataset
            description: Descripción
            participant_nodes: Lista de nodos participantes
            dataset_requirements: Requisitos del dataset (features, min_samples, etc.)
            privacy_level: Nivel de privacidad (low, medium, high)

        Returns:
            ID del dataset creado
        """
        try:
            dataset_id = str(uuid.uuid4())

            # Crear dataset base
            dataset = FederatedDataset(
                dataset_id=dataset_id,
                name=name,
                description=description,
                privacy_level=privacy_level,
                metadata={
                    'requirements': dataset_requirements,
                    'participant_nodes': participant_nodes,
                    'creation_status': 'initializing'
                }
            )

            self.datasets[dataset_id] = dataset
            logger.info(f"📊 Created federated dataset {dataset_id}: {name}")

            # Coordinar con nodos para recolectar datos
            await self._coordinate_data_collection(dataset, participant_nodes, dataset_requirements)

            # Validar privacidad del dataset
            await self._validate_dataset_privacy(dataset)

            # Consolidar y persistir
            await self._consolidate_dataset(dataset)

            self.stats['datasets_created'] += 1
            logger.info(f"✅ Federated dataset {dataset_id} created successfully")

            return dataset_id

        except Exception as e:
            logger.error(f"❌ Error creating federated dataset: {e}")
            if dataset_id in self.datasets:
                del self.datasets[dataset_id]
            raise

    async def shard_dataset(self, dataset_id: str, shard_config: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Dividir dataset preservando privacidad usando Private Set Intersection.

        Args:
            dataset_id: ID del dataset a shardear
            shard_config: Configuración del sharding (num_shards, overlap, etc.)

        Returns:
            Diccionario con shard IDs por nodo
        """
        try:
            if dataset_id not in self.datasets:
                raise ValueError(f"Dataset {dataset_id} not found")

            dataset = self.datasets[dataset_id]
            logger.info(f"🔄 Starting PSI-based sharding for dataset {dataset_id}")

            # Realizar Private Set Intersection entre nodos
            intersection_sets = await self._perform_private_set_intersection(
                list(dataset.shards.keys()), shard_config
            )

            # Crear shards basados en la intersección
            shard_assignments = await self._create_privacy_preserving_shards(
                dataset, intersection_sets, shard_config
            )

            logger.info(f"✅ Dataset {dataset_id} sharded into {len(shard_assignments)} node groups")
            return shard_assignments

        except Exception as e:
            logger.error(f"❌ Error sharding dataset {dataset_id}: {e}")
            raise

    async def _coordinate_data_collection(self, dataset: FederatedDataset,
                                        participant_nodes: List[str],
                                        requirements: Dict[str, Any]):
        """Coordinar recolección de datos con nodos participantes."""
        try:
            logger.info(f"📡 Coordinating data collection with {len(participant_nodes)} nodes")

            # Crear tareas de recolección concurrentes
            tasks = []
            for node_id in participant_nodes:
                task = self._collect_node_data(dataset, node_id, requirements)
                tasks.append(task)

            # Limitar concurrencia
            semaphore = asyncio.Semaphore(self.max_concurrent_operations)
            async def limited_collect(task):
                async with semaphore:
                    return await task

            # Ejecutar recolección
            results = await asyncio.gather(*[limited_collect(task) for task in tasks],
                                         return_exceptions=True)

            # Procesar resultados
            successful_collections = 0
            for i, result in enumerate(results):
                node_id = participant_nodes[i]
                if isinstance(result, Exception):
                    logger.warning(f"⚠️ Data collection failed for node {node_id}: {result}")
                else:
                    successful_collections += 1
                    logger.info(f"✅ Data collected from node {node_id}")

            if successful_collections == 0:
                raise RuntimeError("No data collected from any participant node")

            dataset.metadata['collection_status'] = 'completed'
            dataset.metadata['successful_collections'] = successful_collections

        except Exception as e:
            logger.error(f"❌ Error coordinating data collection: {e}")
            raise

    async def _collect_node_data(self, dataset: FederatedDataset, node_id: str,
                               requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Recolectar datos de un nodo específico."""
        try:
            # Enviar solicitud de datos al nodo
            request_payload = {
                'action': 'collect_dataset_contribution',
                'dataset_id': dataset.dataset_id,
                'requirements': requirements,
                'privacy_level': dataset.privacy_level
            }

            # Timeout para respuesta
            timeout = requirements.get('collection_timeout', 300)  # 5 minutos default

            # Aquí iría la comunicación real con el nodo
            # Por simplicidad, simulamos la respuesta
            await asyncio.sleep(0.1)  # Simular latencia de red

            # Simular respuesta del nodo
            node_data = {
                'node_id': node_id,
                'sample_count': requirements.get('min_samples_per_node', 1000),
                'features': requirements.get('features', ['feature1', 'feature2']),
                'data_hash': hashlib.sha256(f"{node_id}_{dataset.dataset_id}".encode()).hexdigest(),
                'privacy_metadata': {
                    'differential_privacy_applied': dataset.privacy_level == 'high',
                    'encryption_used': dataset.privacy_level in ['medium', 'high']
                }
            }

            # Crear shard para este nodo
            shard = DatasetShard(
                shard_id=str(uuid.uuid4()),
                node_id=node_id,
                dataset_id=dataset.dataset_id,
                sample_count=node_data['sample_count'],
                features=node_data['features'],
                privacy_metadata=node_data['privacy_metadata']
            )

            # Persistir shard en IPFS
            shard_data = {
                'shard_info': {
                    'shard_id': shard.shard_id,
                    'node_id': shard.node_id,
                    'sample_count': shard.sample_count,
                    'features': shard.features
                },
                'data_hash': node_data['data_hash'],
                'privacy_metadata': shard.privacy_metadata
            }

            shard_cid = await self.ipfs_manager.publish_data(
                json.dumps(shard_data).encode(),
                {'type': 'dataset_shard', 'dataset_id': dataset.dataset_id}
            )

            shard.ipfs_cid = shard_cid
            self.shards[shard.shard_id] = shard
            dataset.shards[node_id] = {
                'shard_id': shard.shard_id,
                'sample_count': shard.sample_count,
                'ipfs_cid': shard_cid
            }

            dataset.total_samples += shard.sample_count
            self.stats['shards_created'] += 1
            self.stats['total_samples_processed'] += shard.sample_count

            return node_data

        except Exception as e:
            logger.error(f"❌ Error collecting data from node {node_id}: {e}")
            raise

    async def _validate_dataset_privacy(self, dataset: FederatedDataset):
        """Validar que el dataset cumple con los requisitos de privacidad."""
        try:
            logger.info(f"🔒 Validating privacy for dataset {dataset.dataset_id}")

            if self.privacy_engine:
                # Verificar presupuesto de privacidad
                if not self.privacy_engine.is_privacy_budget_available():
                    raise RuntimeError("Insufficient privacy budget for dataset creation")

                self.stats['privacy_operations'] += 1

            # Validar que todos los shards tienen metadatos de privacidad
            for node_id, shard_info in dataset.shards.items():
                shard = self.shards.get(shard_info['shard_id'])
                if not shard or not shard.privacy_metadata:
                    raise ValueError(f"Missing privacy metadata for shard from node {node_id}")

            dataset.metadata['privacy_validated'] = True
            logger.info(f"✅ Privacy validation passed for dataset {dataset.dataset_id}")

        except Exception as e:
            logger.error(f"❌ Privacy validation failed: {e}")
            raise

    async def _consolidate_dataset(self, dataset: FederatedDataset):
        """Consolidar dataset y persistir metadatos en IPFS."""
        try:
            # Crear metadatos consolidados
            consolidated_metadata = {
                'dataset_id': dataset.dataset_id,
                'name': dataset.name,
                'description': dataset.description,
                'total_samples': dataset.total_samples,
                'features': list(set().union(*[self.shards[s['shard_id']].features
                                             for s in dataset.shards.values()])),
                'shards': dataset.shards,
                'privacy_level': dataset.privacy_level,
                'created_at': dataset.created_at,
                'metadata': dataset.metadata
            }

            # Persistir en IPFS
            metadata_json = json.dumps(consolidated_metadata, indent=2)
            dataset.ipfs_cid = await self.ipfs_manager.publish_data(
                metadata_json.encode(),
                {'type': 'federated_dataset', 'dataset_id': dataset.dataset_id}
            )

            self.stats['ipfs_operations'] += 1
            dataset.metadata['consolidation_status'] = 'completed'

            logger.info(f"💾 Dataset {dataset.dataset_id} consolidated and persisted to IPFS: {dataset.ipfs_cid}")

        except Exception as e:
            logger.error(f"❌ Error consolidating dataset: {e}")
            raise

    async def _perform_private_set_intersection(self, node_ids: List[str],
                                              shard_config: Dict[str, Any]) -> Dict[str, Set[str]]:
        """
        Realizar Private Set Intersection entre nodos para sharding.
        Usa un protocolo simplificado basado en hashes comprometidos.
        """
        try:
            logger.info(f"🔐 Performing PSI with {len(node_ids)} nodes")

            # Recolectar hashes de cada nodo (simulación de PSI)
            node_hashes = {}
            for node_id in node_ids:
                # En implementación real, esto sería un protocolo de PSI multi-party
                # Aquí simulamos recolectando hashes de features/samples
                shard = None
                for dataset in self.datasets.values():
                    if node_id in dataset.shards:
                        shard = self.shards[dataset.shards[node_id]['shard_id']]
                        break

                if shard:
                    # Generar hashes de features para PSI
                    feature_hashes = set()
                    for feature in shard.features:
                        hash_input = f"{feature}_{shard.hash_salt}_{node_id}".encode()
                        feature_hash = hashlib.sha256(hash_input).hexdigest()
                        feature_hashes.add(feature_hash)

                    node_hashes[node_id] = feature_hashes

            # Encontrar intersecciones (simplificado)
            intersection_sets = {}
            all_features = set()
            for hashes in node_hashes.values():
                all_features.update(hashes)

            # Asignar features a nodos basados en configuración
            num_shards = shard_config.get('num_shards', len(node_ids))
            features_per_shard = len(all_features) // num_shards

            feature_list = list(all_features)
            for i, node_id in enumerate(node_ids):
                start_idx = i * features_per_shard
                end_idx = start_idx + features_per_shard if i < num_shards - 1 else len(feature_list)
                intersection_sets[node_id] = set(feature_list[start_idx:end_idx])

            return intersection_sets

        except Exception as e:
            logger.error(f"❌ Error in PSI: {e}")
            raise

    async def _create_privacy_preserving_shards(self, dataset: FederatedDataset,
                                              intersection_sets: Dict[str, Set[str]],
                                              shard_config: Dict[str, Any]) -> Dict[str, List[str]]:
        """Crear shards preservando privacidad basados en PSI."""
        try:
            shard_assignments = {}

            for node_id, feature_set in intersection_sets.items():
                # Crear nuevo shard basado en las features intersectadas
                original_shard = self.shards[dataset.shards[node_id]['shard_id']]

                # Filtrar features que están en la intersección
                intersected_features = [f for f in original_shard.features
                                      if hashlib.sha256(f"{f}_{original_shard.hash_salt}_{node_id}".encode()).hexdigest() in feature_set]

                if intersected_features:
                    new_shard = DatasetShard(
                        shard_id=str(uuid.uuid4()),
                        node_id=node_id,
                        dataset_id=f"{dataset.dataset_id}_sharded",
                        sample_count=original_shard.sample_count,  # Mantener count por simplicidad
                        features=intersected_features,
                        privacy_metadata={
                            **original_shard.privacy_metadata,
                            'psi_applied': True,
                            'intersection_size': len(feature_set)
                        }
                    )

                    # Persistir nuevo shard
                    shard_data = {
                        'shard_info': {
                            'shard_id': new_shard.shard_id,
                            'node_id': new_shard.node_id,
                            'sample_count': new_shard.sample_count,
                            'features': new_shard.features
                        },
                        'privacy_metadata': new_shard.privacy_metadata
                    }

                    new_shard.ipfs_cid = await self.ipfs_manager.publish_data(
                        json.dumps(shard_data).encode(),
                        {'type': 'privacy_preserved_shard', 'original_dataset': dataset.dataset_id}
                    )

                    self.shards[new_shard.shard_id] = new_shard
                    shard_assignments[node_id] = [new_shard.shard_id]

                    self.stats['shards_created'] += 1
                    self.stats['ipfs_operations'] += 1

            return shard_assignments

        except Exception as e:
            logger.error(f"❌ Error creating privacy-preserving shards: {e}")
            raise

    # Métodos de gestión de datasets

    def list_datasets(self) -> List[Dict[str, Any]]:
        """Listar todos los datasets federados."""
        return [{
            'dataset_id': ds.dataset_id,
            'name': ds.name,
            'description': ds.description,
            'total_samples': ds.total_samples,
            'shard_count': len(ds.shards),
            'privacy_level': ds.privacy_level,
            'created_at': ds.created_at,
            'ipfs_cid': ds.ipfs_cid
        } for ds in self.datasets.values()]

    async def get_dataset(self, dataset_id: str) -> Optional[FederatedDataset]:
        """Obtener dataset por ID."""
        return self.datasets.get(dataset_id)

    async def delete_dataset(self, dataset_id: str) -> bool:
        """Eliminar dataset y sus shards."""
        try:
            if dataset_id not in self.datasets:
                return False

            dataset = self.datasets[dataset_id]

            # Eliminar shards
            for shard_info in dataset.shards.values():
                shard_id = shard_info['shard_id']
                if shard_id in self.shards:
                    # Intentar despinear de IPFS
                    if self.shards[shard_id].ipfs_cid:
                        await self.ipfs_manager.unpin_content(self.shards[shard_id].ipfs_cid)
                    del self.shards[shard_id]

            # Eliminar dataset
            if dataset.ipfs_cid:
                await self.ipfs_manager.unpin_content(dataset.ipfs_cid)

            del self.datasets[dataset_id]
            logger.info(f"🗑️ Deleted dataset {dataset_id}")

            return True

        except Exception as e:
            logger.error(f"❌ Error deleting dataset {dataset_id}: {e}")
            return False

    def get_dataset_stats(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estadísticas de un dataset."""
        dataset = self.datasets.get(dataset_id)
        if not dataset:
            return None

        return {
            'dataset_id': dataset_id,
            'total_samples': dataset.total_samples,
            'shard_count': len(dataset.shards),
            'features': dataset.features,
            'privacy_level': dataset.privacy_level,
            'created_at': dataset.created_at,
            'metadata': dataset.metadata
        }

    def get_exchange_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del exchange."""
        return {
            **self.stats,
            'active_datasets': len(self.datasets),
            'total_shards': len(self.shards),
            'uptime': time.time()  # Placeholder
        }

    async def cleanup_expired_datasets(self, max_age_hours: int = 24):
        """Limpiar datasets expirados."""
        try:
            current_time = time.time()
            expired_datasets = []

            for dataset_id, dataset in self.datasets.items():
                age_hours = (current_time - dataset.created_at) / 3600
                if age_hours > max_age_hours:
                    expired_datasets.append(dataset_id)

            for dataset_id in expired_datasets:
                await self.delete_dataset(dataset_id)

            if expired_datasets:
                logger.info(f"🧹 Cleaned up {len(expired_datasets)} expired datasets")

        except Exception as e:
            logger.error(f"❌ Error cleaning up expired datasets: {e}")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup_expired_datasets()