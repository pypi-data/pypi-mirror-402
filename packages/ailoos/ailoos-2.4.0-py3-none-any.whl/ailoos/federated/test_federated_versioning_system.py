"""
Tests for Federated Versioning System
Pruebas unitarias y de integración para el sistema completo de versionado federado.
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from .federated_versioning_system import FederatedVersioningSystem, SystemConfig
from .federated_version_manager import FederatedVersionManager, ModelVersion, VersionStatus
from .version_validator import VersionValidator, ValidationResult, ValidationType
from .ipfs_version_distributor import IPFSVersionDistributor, DistributionStrategy
from .rollback_coordinator import RollbackCoordinator
from .version_conflict_resolver import VersionConflictResolver, ConflictType
from .version_history_tracker import VersionHistoryTracker, AuditEventType


class TestFederatedVersioningSystem:
    """Pruebas para el sistema completo de versionado federado."""

    @pytest.fixture
    async def mock_ipfs_manager(self):
        """Mock IPFS manager para pruebas."""
        mock_manager = AsyncMock()
        mock_manager.store_data = AsyncMock(return_value="QmTestCID")
        mock_manager.get_data = AsyncMock(return_value=b"test_data")
        mock_manager.start = AsyncMock()
        return mock_manager

    @pytest.fixture
    def system_config(self):
        """Configuración de prueba para el sistema."""
        return SystemConfig(
            registry_path="test_versions.json",
            audit_log_path="test_audit.log",
            ipfs_endpoint="http://localhost:5001/api/v0",
            enable_transactions=False,  # Deshabilitar para pruebas más simples
            enable_auto_recovery=False,
            consistency_check_interval=0
        )

    @pytest.mark.asyncio
    async def test_system_initialization(self, mock_ipfs_manager, system_config):
        """Probar inicialización del sistema."""
        with patch('src.ailoos.federated.federated_versioning_system.IPFSManager', return_value=mock_ipfs_manager):
            system = FederatedVersioningSystem(system_config)

            # Mockear componentes para evitar dependencias reales
            with patch.object(system, '_initialize_components', new_callable=AsyncMock) as mock_init:
                mock_init.return_value = True

                success = await system.initialize()
                assert success

                # Verificar que los componentes principales existen
                assert system.version_manager is not None
                assert system.validator is not None
                assert system.distributor is not None
                assert system.rollback_coordinator is not None
                assert system.conflict_resolver is not None
                assert system.history_tracker is not None

    @pytest.mark.asyncio
    async def test_transaction_execution(self, mock_ipfs_manager, system_config):
        """Probar ejecución de transacciones."""
        with patch('src.ailoos.federated.federated_versioning_system.IPFSManager', return_value=mock_ipfs_manager):
            system = FederatedVersioningSystem(system_config)

            # Mockear inicialización
            with patch.object(system, 'initialize', return_value=True):
                await system.initialize()

            # Habilitar transacciones para esta prueba
            system.config.enable_transactions = True

            # Mockear operaciones
            with patch.object(system, '_execute_operation', new_callable=AsyncMock) as mock_execute:
                operations = [{
                    'type': 'register_version',
                    'data': {
                        'model_data': b'test_model',
                        'metadata': {'version': '1.0.0'},
                        'creator_node': 'test_node'
                    }
                }]

                txn_id = await system.execute_transaction(operations, "Test transaction")
                assert txn_id is not None
                assert txn_id.startswith("txn_")

                # Verificar que se ejecutó la operación
                mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_system_health_monitoring(self, mock_ipfs_manager, system_config):
        """Probar monitoreo de salud del sistema."""
        with patch('src.ailoos.federated.federated_versioning_system.IPFSManager', return_value=mock_ipfs_manager):
            system = FederatedVersioningSystem(system_config)

            # Mockear componentes
            system.ipfs_manager = mock_ipfs_manager
            system.version_manager = Mock()
            system.version_manager.registry = Mock()
            system.version_manager.registry.versions = {}

            health = await system._check_system_health()
            assert health in ['healthy', 'degraded', 'critical']


class TestFederatedVersionManager:
    """Pruebas para el gestor de versiones federadas."""

    @pytest.fixture
    async def mock_ipfs(self):
        """Mock IPFS para pruebas."""
        mock = AsyncMock()
        mock.store_data = AsyncMock(return_value="QmTestCID")
        return mock

    @pytest.fixture
    def version_manager(self, mock_ipfs):
        """Instancia de VersionManager para pruebas."""
        return FederatedVersionManager(
            registry_path="test_registry.json",
            ipfs_manager=mock_ipfs,
            min_validations=2,
            validation_timeout_hours=1
        )

    @pytest.mark.asyncio
    async def test_version_registration(self, version_manager, mock_ipfs):
        """Probar registro de versiones."""
        model_data = b"test_model_data"
        metadata = {
            'model_name': 'test_model',
            'version': '1.0.0',
            'description': 'Test version'
        }

        # Mockear guardado
        with patch.object(version_manager, '_save_registry', new_callable=AsyncMock):
            version_id = await version_manager.register_new_version(
                model_data=model_data,
                metadata=metadata,
                creator_node='test_node'
            )

            assert version_id is not None
            assert 'test_model' in version_id
            assert '1.0.0' in version_id

            # Verificar que se almacenó en IPFS
            mock_ipfs.store_data.assert_called()

    @pytest.mark.asyncio
    async def test_validation_voting(self, version_manager):
        """Probar sistema de votación de validación."""
        # Registrar versión primero
        with patch.object(version_manager, '_save_registry', new_callable=AsyncMock):
            version_id = await version_manager.register_new_version(
                model_data=b"test",
                metadata={'version': '1.0.0'},
                creator_node='node1'
            )

        # Enviar votos
        with patch.object(version_manager, '_save_registry', new_callable=AsyncMock):
            # Voto aprobado
            success1 = await version_manager.submit_validation_vote(
                version_id=version_id,
                node_id='node2',
                vote='approved'
            )
            assert success1

            # Voto rechazado
            success2 = await version_manager.submit_validation_vote(
                version_id=version_id,
                node_id='node3',
                vote='rejected'
            )
            assert success2

        # Verificar estado de validación
        status = await version_manager.get_validation_status(version_id)
        assert status['votes']['node2'] == 'approved'
        assert status['votes']['node3'] == 'rejected'


class TestVersionValidator:
    """Pruebas para el validador de versiones."""

    @pytest.fixture
    def mock_version_manager(self):
        """Mock del gestor de versiones."""
        mock = AsyncMock()
        mock.get_version = AsyncMock(return_value=Mock(version_id="test_version"))
        return mock

    @pytest.fixture
    def validator(self, mock_version_manager):
        """Instancia de validador para pruebas."""
        return VersionValidator(
            version_manager=mock_version_manager,
            validation_timeout_seconds=60,
            min_validation_score=0.5
        )

    @pytest.mark.asyncio
    async def test_integrity_validation(self, validator):
        """Probar validación de integridad."""
        model_data = b"test_model_data"
        metadata = {
            'model_hash': '9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8c1e0c9e6b8