"""
Modelos SQLAlchemy para DataHub - Gestión de datasets
=====================================================

Este módulo define los modelos SQLAlchemy para almacenar información
de datasets en la base de datos del sistema DataHub.
"""

from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, JSON, Index, CheckConstraint, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Dataset(Base):
    """Modelo principal para datasets registrados en DataHub."""
    __tablename__ = "datahub_datasets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=False, default="1.0.0")

    # Ubicación en IPFS
    ipfs_cid = Column(String(100), nullable=False, unique=True, index=True)
    ipfs_gateway_url = Column(String(500), nullable=True)

    # Metadatos de integridad
    sha256_hash = Column(String(64), nullable=False, index=True)
    file_size_bytes = Column(Integer, nullable=False)
    chunk_count = Column(Integer, nullable=False, default=1)

    # Metadatos del dataset
    dataset_type = Column(String(50), nullable=False)  # 'text', 'image', 'tabular', 'mixed'
    format = Column(String(50), nullable=False)  # 'json', 'csv', 'parquet', 'images', etc.
    compression = Column(String(20), nullable=True)  # 'gzip', 'bz2', 'none'

    # Estadísticas del dataset
    num_samples = Column(Integer, nullable=True)
    num_features = Column(Integer, nullable=True)
    metadata_json = Column(JSON, nullable=True)  # Metadatos adicionales

    # Estado y control
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    download_count = Column(Integer, nullable=False, default=0)

    # Información del creador/proveedor
    creator = Column(String(255), nullable=True)
    license = Column(String(100), nullable=True)
    tags = Column(JSON, nullable=True)  # Lista de tags como JSON

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_downloaded_at = Column(DateTime, nullable=True)

    # Relaciones
    chunks = relationship("DatasetChunk", back_populates="dataset", cascade="all, delete-orphan")
    validations = relationship("DatasetValidation", back_populates="dataset", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("dataset_type IN ('text', 'image', 'tabular', 'audio', 'video', 'mixed')", name="check_dataset_type"),
        CheckConstraint("format IN ('json', 'jsonl', 'csv', 'parquet', 'png', 'jpg', 'wav', 'mp4', 'zip', 'tar.gz')", name="check_format"),
        CheckConstraint("compression IN ('none', 'gzip', 'bz2', 'xz', 'zip')", name="check_compression"),
        CheckConstraint("file_size_bytes > 0", name="check_file_size_positive"),
        CheckConstraint("chunk_count > 0", name="check_chunk_count_positive"),
        CheckConstraint("download_count >= 0", name="check_download_count_non_negative"),
        Index('idx_datasets_active_verified', 'is_active', 'is_verified'),
        Index('idx_datasets_type_format', 'dataset_type', 'format'),
        Index('idx_datasets_created_at', 'created_at'),
        Index('idx_datasets_creator', 'creator'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el dataset a diccionario."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'ipfs_cid': self.ipfs_cid,
            'ipfs_gateway_url': self.ipfs_gateway_url,
            'sha256_hash': self.sha256_hash,
            'file_size_bytes': self.file_size_bytes,
            'chunk_count': self.chunk_count,
            'dataset_type': self.dataset_type,
            'format': self.format,
            'compression': self.compression,
            'num_samples': self.num_samples,
            'num_features': self.num_features,
            'metadata_json': self.metadata_json,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'download_count': self.download_count,
            'creator': self.creator,
            'license': self.license,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_downloaded_at': self.last_downloaded_at.isoformat() if self.last_downloaded_at else None,
        }


class DatasetChunk(Base):
    """Modelo para chunks individuales de un dataset."""
    __tablename__ = "datahub_dataset_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("datahub_datasets.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    ipfs_cid = Column(String(100), nullable=False, unique=True, index=True)
    sha256_hash = Column(String(64), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    metadata_json = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    dataset = relationship("Dataset", back_populates="chunks")

    # Constraints
    __table_args__ = (
        CheckConstraint("chunk_index >= 0", name="check_chunk_index_non_negative"),
        CheckConstraint("size_bytes > 0", name="check_chunk_size_positive"),
        Index('idx_chunks_dataset_index', 'dataset_id', 'chunk_index'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el chunk a diccionario."""
        return {
            'id': self.id,
            'dataset_id': self.dataset_id,
            'chunk_index': self.chunk_index,
            'ipfs_cid': self.ipfs_cid,
            'sha256_hash': self.sha256_hash,
            'size_bytes': self.size_bytes,
            'metadata_json': self.metadata_json,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class DatasetValidation(Base):
    """Modelo para registros de validación de datasets."""
    __tablename__ = "datahub_dataset_validations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("datahub_datasets.id"), nullable=False, index=True)

    # Resultados de validación
    is_integrity_valid = Column(Boolean, nullable=False)
    is_quality_valid = Column(Boolean, nullable=False)
    validation_score = Column(Float, nullable=True)  # 0.0 a 1.0

    # Detalles de validación
    integrity_errors = Column(JSON, nullable=True)  # Lista de errores de integridad
    quality_metrics = Column(JSON, nullable=True)  # Métricas de calidad
    validation_report = Column(JSON, nullable=True)  # Reporte completo

    # Metadata
    validator_version = Column(String(20), nullable=False)
    validated_by = Column(String(100), nullable=True)  # Sistema o usuario que validó

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    dataset = relationship("Dataset", back_populates="validations")

    # Constraints
    __table_args__ = (
        CheckConstraint("validation_score >= 0.0 AND validation_score <= 1.0", name="check_validation_score_range"),
        Index('idx_validations_dataset_created', 'dataset_id', 'created_at'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la validación a diccionario."""
        return {
            'id': self.id,
            'dataset_id': self.dataset_id,
            'is_integrity_valid': self.is_integrity_valid,
            'is_quality_valid': self.is_quality_valid,
            'validation_score': self.validation_score,
            'integrity_errors': self.integrity_errors,
            'quality_metrics': self.quality_metrics,
            'validation_report': self.validation_report,
            'validator_version': self.validator_version,
            'validated_by': self.validated_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class DatasetDownload(Base):
    """Modelo para registro de descargas de datasets."""
    __tablename__ = "datahub_dataset_downloads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("datahub_datasets.id"), nullable=False, index=True)
    node_id = Column(String(100), nullable=True, index=True)  # ID del nodo que descargó
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6

    # Detalles de la descarga
    download_size_bytes = Column(Integer, nullable=False)
    download_duration_ms = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=False)

    # Metadata
    user_agent = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Constraints
    __table_args__ = (
        CheckConstraint("download_size_bytes >= 0", name="check_download_size_non_negative"),
        CheckConstraint("download_duration_ms >= 0", name="check_download_duration_non_negative"),
        Index('idx_downloads_dataset_created', 'dataset_id', 'created_at'),
        Index('idx_downloads_node_created', 'node_id', 'created_at'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la descarga a diccionario."""
        return {
            'id': self.id,
            'dataset_id': self.dataset_id,
            'node_id': self.node_id,
            'ip_address': self.ip_address,
            'download_size_bytes': self.download_size_bytes,
            'download_duration_ms': self.download_duration_ms,
            'success': self.success,
            'user_agent': self.user_agent,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# Índices adicionales para optimización
Index('idx_datasets_sha256', Dataset.sha256_hash)
Index('idx_datasets_ipfs_cid', Dataset.ipfs_cid)
Index('idx_chunks_ipfs_cid', DatasetChunk.ipfs_cid)
Index('idx_validations_dataset_score', DatasetValidation.dataset_id, DatasetValidation.validation_score)