"""
Sistema de Deduplicación de Datos RAG con Hashing Distribuido
===============================================================

Este módulo implementa un sistema de deduplicación para documentos RAG usando
hashing SHA-256 y registro distribuido con protocolo P2P a través de IPFS.
"""

import hashlib
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

from ...core.logging import get_logger
from ...infrastructure.ipfs_embedded import IPFSManager

logger = get_logger(__name__)


@dataclass
class DocumentHash:
    """Representa el hash de un documento con metadata."""
    document_hash: str
    document_id: str
    content_length: int
    timestamp: str
    node_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return {
            'document_hash': self.document_hash,
            'document_id': self.document_id,
            'content_length': self.content_length,
            'timestamp': self.timestamp,
            'node_id': self.node_id,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentHash':
        """Crea instancia desde diccionario."""
        return cls(
            document_hash=data['document_hash'],
            document_id=data['document_id'],
            content_length=data['content_length'],
            timestamp=data['timestamp'],
            node_id=data['node_id'],
            metadata=data.get('metadata', {})
        )


class DistributedHashRegistry:
    """
    Registro distribuido de hashes de documentos usando IPFS P2P.

    Mantiene un registro de hashes conocidos de documentos para evitar
    almacenamiento redundante en sistemas RAG distribuidos.
    """

    def __init__(self, ipfs_manager: IPFSManager, node_id: str,
                 registry_cid: Optional[str] = None):
        """
        Inicializa el registro distribuido.

        Args:
            ipfs_manager: Gestor IPFS para operaciones P2P
            node_id: ID único del nodo actual
            registry_cid: CID del registro actual (opcional)
        """
        self.ipfs_manager = ipfs_manager
        self.node_id = node_id
        self.registry_cid = registry_cid
        self.local_hashes: Set[str] = set()
        self.hash_registry: Dict[str, DocumentHash] = {}
        self.is_initialized = False

        logger.info(f"DistributedHashRegistry inicializado para nodo {node_id}")

    async def initialize(self) -> None:
        """Inicializa el registro cargando datos existentes desde IPFS."""
        if self.is_initialized:
            return

        try:
            if self.registry_cid:
                # Cargar registro existente desde IPFS
                registry_data = await self.ipfs_manager.get_data(self.registry_cid)
                registry_json = json.loads(registry_data.decode('utf-8'))

                # Reconstruir hashes locales y registro
                for hash_data in registry_json.get('hashes', []):
                    doc_hash = DocumentHash.from_dict(hash_data)
                    self.hash_registry[doc_hash.document_hash] = doc_hash
                    self.local_hashes.add(doc_hash.document_hash)

                logger.info(f"Cargado registro existente con {len(self.hash_registry)} hashes")

            self.is_initialized = True
            logger.info("DistributedHashRegistry inicializado correctamente")

        except Exception as e:
            logger.error(f"Error inicializando registro distribuido: {e}")
            # Continuar con registro vacío si falla la carga
            self.is_initialized = True

    async def register_document_hash(self, document_hash: DocumentHash) -> bool:
        """
        Registra un nuevo hash de documento en el registro distribuido.

        Args:
            document_hash: Hash del documento a registrar

        Returns:
            True si se registró correctamente, False si ya existía
        """
        await self.initialize()

        hash_value = document_hash.document_hash

        if hash_value in self.hash_registry:
            logger.debug(f"Hash ya registrado: {hash_value}")
            return False

        # Agregar al registro local
        self.hash_registry[hash_value] = document_hash
        self.local_hashes.add(hash_value)

        # Actualizar registro en IPFS
        await self._update_distributed_registry()

        logger.info(f"Hash registrado: {hash_value} para documento {document_hash.document_id}")
        return True

    async def is_document_known(self, document_hash: str) -> bool:
        """
        Verifica si un hash de documento es conocido en el registro distribuido.

        Args:
            document_hash: Hash del documento a verificar

        Returns:
            True si el documento es conocido
        """
        await self.initialize()

        # Verificar en registro local primero
        if document_hash in self.hash_registry:
            return True

        # Intentar sincronizar con otros nodos (simplificado)
        # En implementación completa, aquí se haría gossiping P2P
        await self._sync_with_peers()

        return document_hash in self.hash_registry

    async def get_document_info(self, document_hash: str) -> Optional[DocumentHash]:
        """
        Obtiene información de un documento por su hash.

        Args:
            document_hash: Hash del documento

        Returns:
            Información del documento o None si no existe
        """
        await self.initialize()
        return self.hash_registry.get(document_hash)

    async def _update_distributed_registry(self) -> None:
        """Actualiza el registro distribuido en IPFS."""
        try:
            # Preparar datos para IPFS
            registry_data = {
                'node_id': self.node_id,
                'timestamp': datetime.now().isoformat(),
                'hashes': [h.to_dict() for h in self.hash_registry.values()]
            }

            # Serializar y subir a IPFS
            json_data = json.dumps(registry_data, ensure_ascii=False)
            new_cid = await self.ipfs_manager.add_data(json_data.encode('utf-8'))

            # Actualizar CID del registro
            self.registry_cid = new_cid

            logger.debug(f"Registro actualizado en IPFS: {new_cid}")

        except Exception as e:
            logger.error(f"Error actualizando registro distribuido: {e}")

    async def _sync_with_peers(self) -> None:
        """
        Sincroniza el registro con otros nodos P2P.

        Nota: Esta es una implementación simplificada. En producción,
        se implementaría un protocolo de gossiping completo.
        """
        # Placeholder para sincronización P2P
        # En implementación real, aquí se contactaría con peers conocidos
        # y se fusionarían registros usando CRDT o similar
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del registro."""
        return {
            'total_hashes': len(self.hash_registry),
            'local_hashes': len(self.local_hashes),
            'registry_cid': self.registry_cid,
            'node_id': self.node_id,
            'is_initialized': self.is_initialized
        }


class DocumentDeduplicator:
    """
    Deduplicador de documentos usando hashing SHA-256 y registro distribuido.
    """

    def __init__(self, hash_registry: DistributedHashRegistry):
        """
        Inicializa el deduplicador.

        Args:
            hash_registry: Registro distribuido de hashes
        """
        self.hash_registry = hash_registry
        self.stats = {
            'documents_processed': 0,
            'duplicates_found': 0,
            'storage_saved_bytes': 0
        }

    @staticmethod
    def calculate_document_hash(document: Dict[str, Any]) -> str:
        """
        Calcula el hash SHA-256 de un documento.

        Args:
            document: Documento a hashear

        Returns:
            Hash SHA-256 en formato hexadecimal
        """
        # Normalizar contenido del documento para hashing consistente
        content = document.get('content', document.get('text', ''))

        # Incluir metadata relevante en el hash para evitar colisiones
        metadata_keys = ['title', 'source', 'author', 'date']
        metadata_str = ''
        for key in metadata_keys:
            if key in document:
                metadata_str += f"{key}:{document[key]}|"

        # Crear string canónico para hashing
        canonical_content = f"{content}|{metadata_str}"

        # Calcular hash SHA-256
        hash_obj = hashlib.sha256(canonical_content.encode('utf-8'))
        return hash_obj.hexdigest()

    async def should_process_document(self, document: Dict[str, Any]) -> bool:
        """
        Determina si un documento debe procesarse o si es duplicado.

        Args:
            document: Documento a verificar

        Returns:
            True si debe procesarse, False si es duplicado
        """
        document_hash = self.calculate_document_hash(document)
        document_id = document.get('id', f"doc_{hash(document_hash) % 1000000}")

        # Crear objeto DocumentHash
        doc_hash_obj = DocumentHash(
            document_hash=document_hash,
            document_id=document_id,
            content_length=len(document.get('content', document.get('text', ''))),
            timestamp=datetime.now().isoformat(),
            node_id=self.hash_registry.node_id,
            metadata={
                'title': document.get('title', ''),
                'source': document.get('source', ''),
                'processed_at': datetime.now().isoformat()
            }
        )

        # Verificar si ya existe
        is_known = await self.hash_registry.is_document_known(document_hash)

        self.stats['documents_processed'] += 1

        if is_known:
            self.stats['duplicates_found'] += 1
            self.stats['storage_saved_bytes'] += doc_hash_obj.content_length
            logger.info(f"Documento duplicado detectado: {document_id} (hash: {document_hash[:16]}...)")
            return False

        # Registrar nuevo documento
        await self.hash_registry.register_document_hash(doc_hash_obj)
        logger.debug(f"Nuevo documento registrado: {document_id} (hash: {document_hash[:16]}...)")
        return True

    async def deduplicate_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filtra una lista de documentos removiendo duplicados.

        Args:
            documents: Lista de documentos a deduplicar

        Returns:
            Lista de documentos únicos
        """
        unique_documents = []

        for doc in documents:
            if await self.should_process_document(doc):
                unique_documents.append(doc)

        logger.info(f"Deduplicación completada: {len(documents)} -> {len(unique_documents)} documentos")
        return unique_documents

    def get_deduplication_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de deduplicación."""
        total_processed = self.stats['documents_processed']
        duplicates = self.stats['duplicates_found']

        return {
            'documents_processed': total_processed,
            'duplicates_found': duplicates,
            'unique_documents': total_processed - duplicates,
            'duplication_rate': duplicates / max(1, total_processed),
            'storage_saved_bytes': self.stats['storage_saved_bytes'],
            'registry_stats': self.hash_registry.get_stats()
        }


# Funciones de conveniencia

async def create_distributed_hash_registry(ipfs_endpoint: str = "http://localhost:5001/api/v0",
                                         node_id: str = "default_node",
                                         registry_cid: Optional[str] = None) -> DistributedHashRegistry:
    """
    Crea un registro distribuido de hashes con configuración por defecto.

    Args:
        ipfs_endpoint: Endpoint del nodo IPFS
        node_id: ID del nodo actual
        registry_cid: CID del registro existente (opcional)

    Returns:
        Registro distribuido configurado
    """
    ipfs_manager = IPFSManager(api_endpoint=ipfs_endpoint)
    await ipfs_manager.start()

    registry = DistributedHashRegistry(ipfs_manager, node_id, registry_cid)
    await registry.initialize()

    return registry


async def create_document_deduplicator(ipfs_endpoint: str = "http://localhost:5001/api/v0",
                                     node_id: str = "default_node") -> DocumentDeduplicator:
    """
    Crea un deduplicador de documentos con configuración por defecto.

    Args:
        ipfs_endpoint: Endpoint del nodo IPFS
        node_id: ID del nodo actual

    Returns:
        Deduplicador configurado
    """
    registry = await create_distributed_hash_registry(ipfs_endpoint, node_id)
    return DocumentDeduplicator(registry)