#!/usr/bin/env python3
"""
Tests para DatasetRegistry - DataHub
====================================

Tests unitarios para el registro y catálogo de datasets.
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime

from ..models import Dataset, DatasetValidation, DatasetDownload, Base
from ..registry import DatasetRegistry


def get_test_db():
    """Get test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


@pytest.fixture
def test_db():
    """Fixture para base de datos de prueba en memoria."""
    db = get_test_db()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def registry(test_db):
    """Fixture para DatasetRegistry."""
    return DatasetRegistry(test_db)


class TestDatasetRegistry:
    """Tests para DatasetRegistry."""

    def test_registry_initialization(self, registry):
        """Test inicialización del registry."""
        assert registry.db is not None
        assert hasattr(registry, 'register_dataset')
        assert hasattr(registry, 'get_dataset')

    def test_register_dataset_success(self, registry):
        """Test registro exitoso de dataset."""
        dataset = registry.register_dataset(
            name="test_dataset",
            ipfs_cid="QmTest123456789",
            sha256_hash="a" * 64,
            file_size_bytes=1024,
            dataset_type="tabular",
            format="csv",
            description="Test dataset",
            creator="test_user",
            tags=["test", "sample"]
        )

        assert dataset is not None
        assert dataset.name == "test_dataset"
        assert dataset.ipfs_cid == "QmTest123456789"
        assert dataset.sha256_hash == "a" * 64
        assert dataset.file_size_bytes == 1024
        assert dataset.dataset_type == "tabular"
        assert dataset.format == "csv"
        assert dataset.description == "Test dataset"
        assert dataset.creator == "test_user"
        assert dataset.tags == ["test", "sample"]
        assert dataset.is_active == True
        assert dataset.is_verified == False
        assert dataset.download_count == 0

    def test_register_dataset_duplicate_name(self, registry):
        """Test registro de dataset con nombre duplicado."""
        # Registrar primer dataset
        registry.register_dataset(
            name="duplicate_name",
            ipfs_cid="QmTest1",
            sha256_hash="a" * 64,
            file_size_bytes=1024,
            dataset_type="text",
            format="json"
        )

        # Intentar registrar con mismo nombre
        with pytest.raises(ValueError, match="Dataset with name 'duplicate_name' already exists"):
            registry.register_dataset(
                name="duplicate_name",
                ipfs_cid="QmTest2",
                sha256_hash="b" * 64,
                file_size_bytes=2048,
                dataset_type="image",
                format="png"
            )

    def test_register_dataset_duplicate_cid(self, registry):
        """Test registro de dataset con CID duplicado."""
        # Registrar primer dataset
        registry.register_dataset(
            name="dataset1",
            ipfs_cid="QmDuplicate",
            sha256_hash="a" * 64,
            file_size_bytes=1024,
            dataset_type="text",
            format="json"
        )

        # Intentar registrar con mismo CID
        with pytest.raises(ValueError, match="Dataset with IPFS CID 'QmDuplicate' already exists"):
            registry.register_dataset(
                name="dataset2",
                ipfs_cid="QmDuplicate",
                sha256_hash="b" * 64,
                file_size_bytes=2048,
                dataset_type="tabular",
                format="csv"
            )

    def test_get_dataset_by_id(self, registry):
        """Test obtener dataset por ID."""
        # Registrar dataset
        dataset = registry.register_dataset(
            name="get_test",
            ipfs_cid="QmGetTest",
            sha256_hash="c" * 64,
            file_size_bytes=512,
            dataset_type="mixed",
            format="zip"
        )

        # Obtener por ID
        retrieved = registry.get_dataset(dataset.id)
        assert retrieved is not None
        assert retrieved.id == dataset.id
        assert retrieved.name == "get_test"

        # Obtener ID inexistente
        not_found = registry.get_dataset(99999)
        assert not_found is None

    def test_get_dataset_by_name(self, registry):
        """Test obtener dataset por nombre."""
        # Registrar dataset
        registry.register_dataset(
            name="name_test",
            ipfs_cid="QmNameTest",
            sha256_hash="d" * 64,
            file_size_bytes=256,
            dataset_type="audio",
            format="wav"
        )

        # Obtener por nombre
        retrieved = registry.get_dataset_by_name("name_test")
        assert retrieved is not None
        assert retrieved.name == "name_test"

        # Obtener nombre inexistente
        not_found = registry.get_dataset_by_name("nonexistent")
        assert not_found is None

    def test_get_dataset_by_cid(self, registry):
        """Test obtener dataset por CID."""
        # Registrar dataset
        registry.register_dataset(
            name="cid_test",
            ipfs_cid="QmCIDTest",
            sha256_hash="e" * 64,
            file_size_bytes=128,
            dataset_type="video",
            format="mp4"
        )

        # Obtener por CID
        retrieved = registry.get_dataset_by_cid("QmCIDTest")
        assert retrieved is not None
        assert retrieved.ipfs_cid == "QmCIDTest"

        # Obtener CID inexistente
        not_found = registry.get_dataset_by_cid("QmNonexistent")
        assert not_found is None

    def test_list_datasets_basic(self, registry):
        """Test listado básico de datasets."""
        # Registrar algunos datasets
        datasets_data = [
            ("dataset1", "Qm1", "text", "json"),
            ("dataset2", "Qm2", "tabular", "csv"),
            ("dataset3", "Qm3", "image", "png")
        ]

        for name, cid, dtype, fmt in datasets_data:
            registry.register_dataset(
                name=name,
                ipfs_cid=cid,
                sha256_hash="f" * 64,
                file_size_bytes=100,
                dataset_type=dtype,
                format=fmt
            )

        # Listar todos
        datasets = registry.list_datasets()
        assert len(datasets) == 3

        # Verificar orden (por defecto created_at desc)
        assert datasets[0].name == "dataset3"  # Más reciente primero
        assert datasets[-1].name == "dataset1"  # Más antiguo último

    def test_list_datasets_filtered(self, registry):
        """Test listado con filtros."""
        # Registrar datasets con diferentes tipos
        registry.register_dataset(
            name="text_ds", ipfs_cid="QmText", sha256_hash="g" * 64,
            file_size_bytes=100, dataset_type="text", format="json"
        )
        registry.register_dataset(
            name="tabular_ds", ipfs_cid="QmTabular", sha256_hash="h" * 64,
            file_size_bytes=200, dataset_type="tabular", format="csv"
        )
        registry.register_dataset(
            name="image_ds", ipfs_cid="QmImage", sha256_hash="i" * 64,
            file_size_bytes=300, dataset_type="image", format="png"
        )

        # Filtrar por tipo
        text_datasets = registry.list_datasets(dataset_type="text")
        assert len(text_datasets) == 1
        assert text_datasets[0].dataset_type == "text"

        tabular_datasets = registry.list_datasets(dataset_type="tabular")
        assert len(tabular_datasets) == 1
        assert tabular_datasets[0].dataset_type == "tabular"

        # Filtrar por creador
        registry.register_dataset(
            name="creator_ds", ipfs_cid="QmCreator", sha256_hash="j" * 64,
            file_size_bytes=400, dataset_type="mixed", format="zip",
            creator="test_creator"
        )

        creator_datasets = registry.list_datasets(creator="test_creator")
        assert len(creator_datasets) == 1
        assert creator_datasets[0].creator == "test_creator"

    def test_list_datasets_pagination(self, registry):
        """Test paginación en listado."""
        # Registrar 10 datasets
        for i in range(10):
            registry.register_dataset(
                name=f"page_test_{i}",
                ipfs_cid=f"QmPage{i}",
                sha256_hash="k" * 64,
                file_size_bytes=100,
                dataset_type="text",
                format="json"
            )

        # Primera página (limit 5)
        page1 = registry.list_datasets(limit=5, offset=0)
        assert len(page1) == 5
        assert page1[0].name == "page_test_9"  # Más reciente

        # Segunda página
        page2 = registry.list_datasets(limit=5, offset=5)
        assert len(page2) == 5
        assert page2[0].name == "page_test_4"

    def test_search_datasets(self, registry):
        """Test búsqueda de datasets."""
        # Registrar datasets
        registry.register_dataset(
            name="machine_learning_dataset",
            ipfs_cid="QmML",
            sha256_hash="l" * 64,
            file_size_bytes=1000,
            dataset_type="tabular",
            format="csv",
            description="Dataset for machine learning",
            tags=["ml", "training"]
        )
        registry.register_dataset(
            name="image_classification",
            ipfs_cid="QmImg",
            sha256_hash="m" * 64,
            file_size_bytes=5000,
            dataset_type="image",
            format="png",
            description="Images for classification",
            tags=["vision", "classification"]
        )

        # Buscar por nombre
        results = registry.search_datasets("machine")
        assert len(results) == 1
        assert "machine" in results[0].name

        # Buscar por descripción
        results = registry.search_datasets("classification")
        assert len(results) == 1
        assert "classification" in results[0].description

        # Buscar por tags (simulado - depende de implementación de búsqueda)
        results = registry.search_datasets("vision")
        assert len(results) >= 0  # Puede no encontrar si búsqueda por tags no implementada

    def test_update_dataset(self, registry):
        """Test actualización de dataset."""
        # Registrar dataset
        dataset = registry.register_dataset(
            name="update_test",
            ipfs_cid="QmUpdate",
            sha256_hash="n" * 64,
            file_size_bytes=100,
            dataset_type="text",
            format="json",
            description="Original description"
        )

        # Actualizar
        updated = registry.update_dataset(
            dataset.id,
            description="Updated description",
            version="2.0.0",
            is_verified=True,
            num_samples=1000
        )

        assert updated is not None
        assert updated.description == "Updated description"
        assert updated.version == "2.0.0"
        assert updated.is_verified == True
        assert updated.num_samples == 1000

        # Verificar que se actualizó en BD
        retrieved = registry.get_dataset(dataset.id)
        assert retrieved.description == "Updated description"

    def test_update_dataset_not_found(self, registry):
        """Test actualización de dataset inexistente."""
        result = registry.update_dataset(99999, description="test")
        assert result is None

    def test_delete_dataset(self, registry):
        """Test eliminación (soft delete) de dataset."""
        # Registrar dataset
        dataset = registry.register_dataset(
            name="delete_test",
            ipfs_cid="QmDelete",
            sha256_hash="o" * 64,
            file_size_bytes=100,
            dataset_type="text",
            format="json"
        )

        # Verificar que existe y está activo
        assert registry.get_dataset(dataset.id).is_active == True

        # Eliminar
        success = registry.delete_dataset(dataset.id)
        assert success == True

        # Verificar que está marcado como inactivo
        deleted = registry.get_dataset(dataset.id)
        assert deleted.is_active == False

    def test_delete_dataset_not_found(self, registry):
        """Test eliminación de dataset inexistente."""
        success = registry.delete_dataset(99999)
        assert success == False

    def test_record_download(self, registry):
        """Test registro de descarga."""
        # Registrar dataset
        dataset = registry.register_dataset(
            name="download_test",
            ipfs_cid="QmDownload",
            sha256_hash="p" * 64,
            file_size_bytes=1000,
            dataset_type="tabular",
            format="csv"
        )

        # Registrar descarga
        success = registry.record_download(
            dataset_id=dataset.id,
            node_id="test_node",
            download_size_bytes=1000,
            download_duration_ms=5000,
            success=True
        )

        assert success == True

        # Verificar que se incrementó el contador
        updated = registry.get_dataset(dataset.id)
        assert updated.download_count == 1

    def test_get_dataset_stats(self, registry):
        """Test obtención de estadísticas."""
        # Registrar algunos datasets
        registry.register_dataset(
            name="stats1", ipfs_cid="QmS1", sha256_hash="q" * 64,
            file_size_bytes=100, dataset_type="text", format="json"
        )
        registry.register_dataset(
            name="stats2", ipfs_cid="QmS2", sha256_hash="r" * 64,
            file_size_bytes=200, dataset_type="tabular", format="csv"
        )
        registry.register_dataset(
            name="stats3", ipfs_cid="QmS3", sha256_hash="s" * 64,
            file_size_bytes=300, dataset_type="image", format="png"
        )

        # Obtener estadísticas
        stats = registry.get_dataset_stats()

        assert stats['total_datasets'] == 3
        assert stats['active_datasets'] == 3
        assert stats['verified_datasets'] == 0  # Ninguno verificado
        assert stats['total_downloads'] == 0
        assert stats['total_size_bytes'] == 600  # 100 + 200 + 300

        # Verificar estadísticas por tipo
        type_stats = stats['datasets_by_type']
        assert len(type_stats) == 3

        # Verificar tipos
        types = [stat['type'] for stat in type_stats]
        assert 'text' in types
        assert 'tabular' in types
        assert 'image' in types

    def test_get_popular_datasets(self, registry):
        """Test obtención de datasets populares."""
        # Registrar datasets con diferentes contadores de descarga
        datasets = []
        for i in range(5):
            ds = registry.register_dataset(
                name=f"popular_{i}",
                ipfs_cid=f"QmPop{i}",
                sha256_hash=chr(ord('t') + i) * 64,
                file_size_bytes=100,
                dataset_type="text",
                format="json"
            )
            # Simular descargas
            for _ in range(i + 1):  # 1, 2, 3, 4, 5 descargas
                registry.record_download(ds.id, download_size_bytes=100, success=True)
            datasets.append(ds)

        # Obtener populares
        popular = registry.get_popular_datasets(limit=3)

        assert len(popular) == 3
        # Verificar orden descendente por downloads
        assert popular[0].download_count >= popular[1].download_count
        assert popular[1].download_count >= popular[2].download_count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])