"""
DatasetRegistry - Registro y catálogo de datasets disponibles
===========================================================

Componente para gestionar el registro, búsqueda y metadatos de datasets
disponibles en el sistema DataHub.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, text

from ..core.logging import get_logger
from .models import Dataset, DatasetChunk, DatasetValidation, DatasetDownload

logger = get_logger(__name__)


class DatasetRegistry:
    """
    Registro centralizado de datasets para el sistema DataHub.

    Gestiona el catálogo de datasets disponibles, incluyendo metadatos,
    validaciones y estadísticas de uso.
    """

    def __init__(self, db_session: Session):
        """
        Inicializar el DatasetRegistry.

        Args:
            db_session: Sesión de base de datos SQLAlchemy
        """
        self.db = db_session
        logger.info("🚀 DatasetRegistry initialized")

    def register_dataset(self,
                        name: str,
                        ipfs_cid: str,
                        sha256_hash: str,
                        file_size_bytes: int,
                        dataset_type: str,
                        format: str,
                        description: Optional[str] = None,
                        version: str = "1.0.0",
                        creator: Optional[str] = None,
                        license: Optional[str] = None,
                        tags: Optional[List[str]] = None,
                        metadata: Optional[Dict[str, Any]] = None,
                        compression: Optional[str] = None,
                        num_samples: Optional[int] = None,
                        num_features: Optional[int] = None,
                        chunk_count: int = 1) -> Dataset:
        """
        Registrar un nuevo dataset en el catálogo.

        Args:
            name: Nombre único del dataset
            ipfs_cid: CID de IPFS del dataset
            sha256_hash: Hash SHA256 para verificación de integridad
            file_size_bytes: Tamaño del archivo en bytes
            dataset_type: Tipo de dataset ('text', 'image', 'tabular', etc.)
            format: Formato del archivo ('json', 'csv', etc.)
            description: Descripción del dataset
            version: Versión del dataset
            creator: Creador/proveedor del dataset
            license: Licencia del dataset
            tags: Lista de tags para categorización
            metadata: Metadatos adicionales como JSON
            compression: Tipo de compresión ('gzip', 'bz2', etc.)
            num_samples: Número de muestras en el dataset
            num_features: Número de características
            chunk_count: Número de chunks en que está dividido el dataset

        Returns:
            Dataset registrado

        Raises:
            ValueError: Si el dataset ya existe o parámetros inválidos
        """
        try:
            # Verificar que no exista un dataset con el mismo nombre o CID
            existing = self.db.query(Dataset).filter(
                or_(Dataset.name == name, Dataset.ipfs_cid == ipfs_cid)
            ).first()

            if existing:
                if existing.name == name:
                    raise ValueError(f"Dataset with name '{name}' already exists")
                else:
                    raise ValueError(f"Dataset with IPFS CID '{ipfs_cid}' already exists")

            # Crear nuevo dataset
            dataset = Dataset(
                name=name,
                description=description,
                version=version,
                ipfs_cid=ipfs_cid,
                sha256_hash=sha256_hash,
                file_size_bytes=file_size_bytes,
                chunk_count=chunk_count,
                dataset_type=dataset_type,
                format=format,
                compression=compression or 'none',
                num_samples=num_samples,
                num_features=num_features,
                metadata_json=metadata,
                creator=creator,
                license=license,
                tags=tags or [],
                is_active=True,
                is_verified=False,
                download_count=0
            )

            self.db.add(dataset)
            self.db.commit()
            self.db.refresh(dataset)

            logger.info(f"✅ Registered new dataset: {name} (CID: {ipfs_cid})")
            return dataset

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to register dataset {name}: {e}")
            raise

    def get_dataset(self, dataset_id: int) -> Optional[Dataset]:
        """
        Obtener un dataset por ID.

        Args:
            dataset_id: ID del dataset

        Returns:
            Dataset o None si no existe
        """
        try:
            return self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
        except Exception as e:
            logger.error(f"❌ Failed to get dataset {dataset_id}: {e}")
            return None

    def get_dataset_by_name(self, name: str) -> Optional[Dataset]:
        """
        Obtener un dataset por nombre.

        Args:
            name: Nombre del dataset

        Returns:
            Dataset o None si no existe
        """
        try:
            return self.db.query(Dataset).filter(Dataset.name == name).first()
        except Exception as e:
            logger.error(f"❌ Failed to get dataset by name {name}: {e}")
            return None

    def get_dataset_by_cid(self, ipfs_cid: str) -> Optional[Dataset]:
        """
        Obtener un dataset por CID de IPFS.

        Args:
            ipfs_cid: CID de IPFS

        Returns:
            Dataset o None si no existe
        """
        try:
            return self.db.query(Dataset).filter(Dataset.ipfs_cid == ipfs_cid).first()
        except Exception as e:
            logger.error(f"❌ Failed to get dataset by CID {ipfs_cid}: {e}")
            return None

    def list_datasets(self,
                     active_only: bool = True,
                     verified_only: bool = False,
                     dataset_type: Optional[str] = None,
                     creator: Optional[str] = None,
                     tags: Optional[List[str]] = None,
                     limit: int = 50,
                     offset: int = 0,
                     order_by: str = 'created_at',
                     order_desc: bool = True) -> List[Dataset]:
        """
        Listar datasets con filtros opcionales.

        Args:
            active_only: Solo datasets activos
            verified_only: Solo datasets verificados
            dataset_type: Filtrar por tipo de dataset
            creator: Filtrar por creador
            tags: Filtrar por tags (debe contener al menos uno)
            limit: Número máximo de resultados
            offset: Desplazamiento para paginación
            order_by: Campo para ordenar ('created_at', 'name', 'download_count')
            order_desc: Orden descendente

        Returns:
            Lista de datasets
        """
        try:
            query = self.db.query(Dataset)

            # Filtros básicos
            if active_only:
                query = query.filter(Dataset.is_active == True)
            if verified_only:
                query = query.filter(Dataset.is_verified == True)
            if dataset_type:
                query = query.filter(Dataset.dataset_type == dataset_type)
            if creator:
                query = query.filter(Dataset.creator == creator)

            # Filtro por tags (JSON contains)
            if tags:
                tag_filters = []
                for tag in tags:
                    tag_filters.append(func.json_contains(Dataset.tags, f'"{tag}"'))
                query = query.filter(or_(*tag_filters))

            # Ordenamiento
            order_column = {
                'created_at': Dataset.created_at,
                'name': Dataset.name,
                'download_count': Dataset.download_count,
                'file_size_bytes': Dataset.file_size_bytes
            }.get(order_by, Dataset.created_at)

            if order_desc:
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(order_column)

            # Paginación
            query = query.limit(limit).offset(offset)

            return query.all()

        except Exception as e:
            logger.error(f"❌ Failed to list datasets: {e}")
            return []

    def search_datasets(self,
                       query: str,
                       active_only: bool = True,
                       limit: int = 20) -> List[Dataset]:
        """
        Buscar datasets por texto en nombre, descripción o tags.

        Args:
            query: Término de búsqueda
            active_only: Solo datasets activos
            limit: Número máximo de resultados

        Returns:
            Lista de datasets que coinciden
        """
        try:
            search_filter = or_(
                Dataset.name.ilike(f'%{query}%'),
                Dataset.description.ilike(f'%{query}%'),
                func.json_search(Dataset.tags, 'one', f'%{query}%').isnot(None)
            )

            db_query = self.db.query(Dataset).filter(search_filter)

            if active_only:
                db_query = db_query.filter(Dataset.is_active == True)

            return db_query.limit(limit).all()

        except Exception as e:
            logger.error(f"❌ Failed to search datasets with query '{query}': {e}")
            return []

    def update_dataset(self,
                      dataset_id: int,
                      **updates) -> Optional[Dataset]:
        """
        Actualizar metadatos de un dataset.

        Args:
            dataset_id: ID del dataset
            **updates: Campos a actualizar

        Returns:
            Dataset actualizado o None si no existe
        """
        try:
            dataset = self.get_dataset(dataset_id)
            if not dataset:
                return None

            # Campos permitidos para actualización
            allowed_fields = {
                'description', 'version', 'is_active', 'is_verified',
                'num_samples', 'num_features', 'metadata_json',
                'creator', 'license', 'tags'
            }

            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(dataset, field, value)

            dataset.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(dataset)

            logger.info(f"✅ Updated dataset {dataset_id}")
            return dataset

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to update dataset {dataset_id}: {e}")
            return None

    def delete_dataset(self, dataset_id: int) -> bool:
        """
        Eliminar un dataset del registro (soft delete).

        Args:
            dataset_id: ID del dataset

        Returns:
            True si eliminado exitosamente
        """
        try:
            dataset = self.get_dataset(dataset_id)
            if not dataset:
                return False

            # Soft delete - marcar como inactivo
            dataset.is_active = False
            dataset.updated_at = datetime.utcnow()

            self.db.commit()

            logger.info(f"✅ Soft deleted dataset {dataset_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to delete dataset {dataset_id}: {e}")
            return False

    def record_download(self,
                       dataset_id: int,
                       node_id: Optional[str] = None,
                       ip_address: Optional[str] = None,
                       download_size_bytes: int = 0,
                       download_duration_ms: Optional[int] = None,
                       success: bool = True,
                       error_message: Optional[str] = None,
                       user_agent: Optional[str] = None) -> bool:
        """
        Registrar una descarga de dataset.

        Args:
            dataset_id: ID del dataset descargado
            node_id: ID del nodo que descargó
            ip_address: Dirección IP del cliente
            download_size_bytes: Tamaño descargado en bytes
            download_duration_ms: Duración de la descarga en ms
            success: Si la descarga fue exitosa
            error_message: Mensaje de error si falló
            user_agent: User-Agent del cliente

        Returns:
            True si registrado exitosamente
        """
        try:
            # Crear registro de descarga
            download = DatasetDownload(
                dataset_id=dataset_id,
                node_id=node_id,
                ip_address=ip_address,
                download_size_bytes=download_size_bytes,
                download_duration_ms=download_duration_ms,
                success=success,
                error_message=error_message,
                user_agent=user_agent
            )

            self.db.add(download)

            # Actualizar contador de descargas y timestamp
            dataset = self.get_dataset(dataset_id)
            if dataset:
                dataset.download_count += 1
                dataset.last_downloaded_at = datetime.utcnow()

            self.db.commit()

            logger.debug(f"📥 Recorded download for dataset {dataset_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Failed to record download for dataset {dataset_id}: {e}")
            return False

    def get_dataset_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas generales del registro de datasets.

        Returns:
            Diccionario con estadísticas
        """
        try:
            # Estadísticas básicas
            total_datasets = self.db.query(func.count(Dataset.id)).scalar() or 0
            active_datasets = self.db.query(func.count(Dataset.id)).filter(Dataset.is_active == True).scalar() or 0
            verified_datasets = self.db.query(func.count(Dataset.id)).filter(Dataset.is_verified == True).scalar() or 0

            # Estadísticas por tipo
            type_stats = self.db.query(
                Dataset.dataset_type,
                func.count(Dataset.id).label('count'),
                func.sum(Dataset.file_size_bytes).label('total_size')
            ).filter(Dataset.is_active == True).group_by(Dataset.dataset_type).all()

            # Estadísticas de descargas
            total_downloads = self.db.query(func.sum(Dataset.download_count)).scalar() or 0

            # Tamaño total
            total_size = self.db.query(func.sum(Dataset.file_size_bytes)).filter(Dataset.is_active == True).scalar() or 0

            return {
                'total_datasets': total_datasets,
                'active_datasets': active_datasets,
                'verified_datasets': verified_datasets,
                'total_downloads': total_downloads,
                'total_size_bytes': total_size,
                'datasets_by_type': [
                    {
                        'type': stat.dataset_type,
                        'count': stat.count,
                        'total_size_bytes': stat.total_size or 0
                    } for stat in type_stats
                ]
            }

        except Exception as e:
            logger.error(f"❌ Failed to get dataset stats: {e}")
            return {}

    def get_popular_datasets(self, limit: int = 10) -> List[Dataset]:
        """
        Obtener datasets más populares por número de descargas.

        Args:
            limit: Número máximo de resultados

        Returns:
            Lista de datasets ordenados por popularidad
        """
        try:
            return self.db.query(Dataset).filter(
                Dataset.is_active == True
            ).order_by(desc(Dataset.download_count)).limit(limit).all()

        except Exception as e:
            logger.error(f"❌ Failed to get popular datasets: {e}")
            return []