#!/usr/bin/env python3
"""
Pruebas básicas para el Node Registry distribuido
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from src.ailoos.discovery.node_registry import (
    NodeRegistry, NodeEntry, NodeSession, NodeStatus, SessionStatus,
    NodeCapabilities, RegistryStorage, SessionManager, StateSynchronizer
)
from src.ailoos.consensus.distributed_consensus import DistributedConsensusManager, ConsensusAlgorithm
from src.ailoos.database.distributed_queries import DistributedQueryEngine, ConsistencyLevel


class TestNodeRegistry:
    """Pruebas para NodeRegistry"""

    @pytest.fixture
    def mock_consensus_manager(self):
        """Mock del consensus manager"""
        manager = Mock(spec=DistributedConsensusManager)
        manager.propose_value = AsyncMock(return_value="proposal_123")
        return manager

    @pytest.fixture
    def mock_query_engine(self):
        """Mock del query engine"""
        engine = Mock(spec=DistributedQueryEngine)
        # Mock successful query result
        result_mock = Mock()
        result_mock.success = True
        result_mock.data = []
        engine.execute_query = AsyncMock(return_value=result_mock)
        return engine

    @pytest.fixture
    def registry(self, mock_consensus_manager, mock_query_engine):
        """Instancia de NodeRegistry para pruebas"""
        registry = NodeRegistry(
            node_id="test_node_1",
            consensus_manager=mock_consensus_manager,
            query_engine=mock_query_engine
        )
        return registry

    @pytest.mark.asyncio
    async def test_register_node_success(self, registry, mock_consensus_manager, mock_query_engine):
        """Prueba registro exitoso de nodo"""
        # Configurar mocks
        storage_mock = Mock(spec=RegistryStorage)
        storage_mock.store_node = AsyncMock(return_value=True)
        registry.storage = storage_mock

        node_info = {
            'node_type': 'worker',
            'capabilities': {
                'federated_learning': True,
                'model_training': True
            },
            'hardware_specs': {'cpu_count': 4, 'memory_gb': 8},
            'network_info': {'ip': '192.168.1.100'},
            'location': 'Madrid, Spain'
        }

        # Registrar nodo
        node_id = await registry.register_node(node_info)

        # Verificaciones
        assert node_id is not None
        assert node_id.startswith('node_')
        mock_consensus_manager.propose_value.assert_called_once()
        storage_mock.store_node.assert_called_once()

        # Verificar que se almacenó en cache
        cached_node = registry.registry_cache.get(node_id)
        assert cached_node is not None
        assert cached_node.node_type == 'worker'
        assert cached_node.status == NodeStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_register_node_invalid_info(self, registry):
        """Prueba registro con información inválida"""
        # Información incompleta
        invalid_info = {
            'capabilities': {'federated_learning': True}
            # Falta node_type
        }

        node_id = await registry.register_node(invalid_info)
        assert node_id is None

    @pytest.mark.asyncio
    async def test_deregister_node(self, registry, mock_consensus_manager):
        """Prueba desregistro de nodo"""
        # Configurar mocks
        storage_mock = Mock(spec=RegistryStorage)
        storage_mock.update_node_status = AsyncMock(return_value=True)
        registry.storage = storage_mock

        # Simular nodo existente en cache
        node_id = "test_node_123"
        registry.registry_cache[node_id] = NodeEntry(
            node_id=node_id,
            node_type='worker',
            capabilities=NodeCapabilities(),
            hardware_specs={},
            network_info={}
        )

        # Desregistrar
        success = await registry.deregister_node(node_id)

        # Verificaciones
        assert success is True
        mock_consensus_manager.propose_value.assert_called_once()
        storage_mock.update_node_status.assert_called_once_with(node_id, NodeStatus.DEREGISTERED)

        # Verificar que se removió de cache
        assert node_id not in registry.registry_cache

    @pytest.mark.asyncio
    async def test_get_node_from_cache(self, registry):
        """Prueba obtener nodo desde cache"""
        node_id = "cached_node_123"
        node_entry = NodeEntry(
            node_id=node_id,
            node_type='worker',
            capabilities=NodeCapabilities(),
            hardware_specs={},
            network_info={},
            location=None,
            owner_id=None,
            last_updated=datetime.now()
        )

        registry.registry_cache[node_id] = node_entry

        retrieved = await registry.get_node(node_id)
        assert retrieved == node_entry

    @pytest.mark.asyncio
    async def test_list_nodes_with_filters(self, registry, mock_query_engine):
        """Prueba listar nodos con filtros"""
        # Configurar mock para retornar nodos filtrados
        mock_result = Mock()
        mock_result.success = True
        mock_result.data = [
            {
                'node_id': 'node_1',
                'node_type': 'worker',
                'capabilities': {'federated_learning': True},
                'hardware_specs': {},
                'network_info': {},
                'status': 'active',
                'registered_at': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
        ]
        mock_query_engine.execute_query = AsyncMock(return_value=mock_result)

        filters = {'node_type': 'worker'}
        nodes = await registry.list_nodes(filters)

        assert len(nodes) == 1
        assert nodes[0].node_id == 'node_1'
        assert nodes[0].node_type == 'worker'

        # Verificar que se actualizó cache
        assert 'node_1' in registry.registry_cache

    @pytest.mark.asyncio
    async def test_update_node_status(self, registry, mock_consensus_manager):
        """Prueba actualizar estado de nodo"""
        storage_mock = Mock(spec=RegistryStorage)
        storage_mock.update_node_status = AsyncMock(return_value=True)
        registry.storage = storage_mock

        node_id = "test_node_456"
        new_status = NodeStatus.SUSPENDED

        success = await registry.update_node_status(node_id, new_status)

        assert success is True
        mock_consensus_manager.propose_value.assert_called_once()
        storage_mock.update_node_status.assert_called_once_with(node_id, new_status)

    @pytest.mark.asyncio
    async def test_create_session(self, registry):
        """Prueba crear sesión para nodo"""
        # Configurar mocks
        session_manager_mock = Mock(spec=SessionManager)
        test_session = NodeSession(
            session_id="session_123",
            node_id="node_456",
            connection_info={'ip': '192.168.1.100'}
        )
        session_manager_mock.create_session = AsyncMock(return_value=test_session)
        registry.session_manager = session_manager_mock

        # Simular nodo registrado
        registry.registry_cache["node_456"] = NodeEntry(
            node_id="node_456",
            node_type='worker',
            capabilities=NodeCapabilities(),
            hardware_specs={},
            network_info={},
            status=NodeStatus.ACTIVE
        )

        connection_info = {'ip': '192.168.1.100', 'port': 8080}
        session = await registry.create_session("node_456", connection_info)

        assert session == test_session
        session_manager_mock.create_session.assert_called_once_with("node_456", connection_info)

    @pytest.mark.asyncio
    async def test_heartbeat(self, registry):
        """Prueba heartbeat de sesión"""
        session_manager_mock = Mock(spec=SessionManager)
        session_manager_mock.update_heartbeat = AsyncMock(return_value=True)
        registry.session_manager = session_manager_mock

        success = await registry.heartbeat("session_123")

        assert success is True
        session_manager_mock.update_heartbeat.assert_called_once_with("session_123")

    def test_get_registry_stats(self, registry):
        """Prueba obtener estadísticas del registro"""
        # Agregar algunos nodos a la cache
        registry.registry_cache = {
            'node_1': NodeEntry('node_1', 'worker', NodeCapabilities(), {}, {}, None, None, status=NodeStatus.ACTIVE),
            'node_2': NodeEntry('node_2', 'worker', NodeCapabilities(), {}, {}, None, None, status=NodeStatus.INACTIVE),
            'node_3': NodeEntry('node_3', 'coordinator', NodeCapabilities(), {}, {}, None, None, status=NodeStatus.SUSPENDED)
        }

        # Simular sesiones activas
        registry.session_manager.active_sessions = {'session_1': Mock(), 'session_2': Mock()}

        stats = registry.get_registry_stats()

        assert stats['total_nodes'] == 3
        assert stats['active_nodes'] == 1
        assert stats['inactive_nodes'] == 1
        assert stats['suspended_nodes'] == 1
        assert stats['active_sessions'] == 2
        assert stats['is_running'] is False


class TestRegistryStorage:
    """Pruebas para RegistryStorage"""

    @pytest.fixture
    def mock_query_engine(self):
        """Mock del query engine"""
        engine = Mock(spec=DistributedQueryEngine)
        return engine

    @pytest.fixture
    def storage(self, mock_query_engine):
        """Instancia de RegistryStorage para pruebas"""
        return RegistryStorage(mock_query_engine)

    @pytest.mark.asyncio
    async def test_store_node(self, storage, mock_query_engine):
        """Prueba almacenar entrada de nodo"""
        mock_query_engine.execute_query = AsyncMock(return_value=Mock(success=True))

        node = NodeEntry(
            node_id="test_node",
            node_type="worker",
            capabilities=NodeCapabilities(federated_learning=True),
            hardware_specs={'cpu': 4},
            network_info={'ip': '192.168.1.1'},
            location=None,
            owner_id=None
        )

        success = await storage.store_node(node)

        assert success is True
        mock_query_engine.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_node(self, storage, mock_query_engine):
        """Prueba recuperar entrada de nodo"""
        # Mock respuesta de query
        mock_result = Mock()
        mock_result.success = True
        mock_result.data = [{
            'node_id': 'test_node',
            'node_type': 'worker',
            'capabilities': {'federated_learning': True},
            'hardware_specs': {'cpu': 4},
            'network_info': {'ip': '192.168.1.1'},
            'status': 'active',
            'registered_at': datetime.now().isoformat(),
            'last_seen': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'location': None,
            'owner_id': None,
            'metadata': {},
            'version': '1.0.0'
        }]
        mock_query_engine.execute_query = AsyncMock(return_value=mock_result)

        node = await storage.get_node('test_node')

        assert node is not None
        assert node.node_id == 'test_node'
        assert node.node_type == 'worker'
        assert node.status == NodeStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_update_node_status(self, storage, mock_query_engine):
        """Prueba actualizar estado de nodo"""
        mock_query_engine.execute_query = AsyncMock(return_value=Mock(success=True))

        success = await storage.update_node_status('test_node', NodeStatus.SUSPENDED)

        assert success is True
        mock_query_engine.execute_query.assert_called_once()


class TestSessionManager:
    """Pruebas para SessionManager"""

    @pytest.fixture
    def mock_storage(self):
        """Mock del storage"""
        storage = Mock(spec=RegistryStorage)
        storage.store_session = AsyncMock(return_value=True)
        storage.update_session_heartbeat = AsyncMock(return_value=True)
        return storage

    @pytest.fixture
    def session_manager(self, mock_storage):
        """Instancia de SessionManager para pruebas"""
        manager = SessionManager(mock_storage)
        return manager

    @pytest.mark.asyncio
    async def test_create_session(self, session_manager, mock_storage):
        """Prueba crear sesión"""
        connection_info = {'ip': '192.168.1.100', 'port': 8080}

        session = await session_manager.create_session('node_123', connection_info)

        assert session is not None
        assert session.node_id == 'node_123'
        assert session.status == SessionStatus.ACTIVE
        assert session.connection_info == connection_info
        assert session.session_id in session_manager.active_sessions

        mock_storage.store_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_heartbeat(self, session_manager, mock_storage):
        """Prueba actualizar heartbeat"""
        # Crear sesión primero
        session = NodeSession(
            session_id='session_123',
            node_id='node_123',
            last_heartbeat=datetime.now() - timedelta(minutes=10)
        )
        session_manager.active_sessions['session_123'] = session

        old_heartbeat = session.last_heartbeat
        success = await session_manager.update_heartbeat('session_123')

        assert success is True
        assert session.last_heartbeat > old_heartbeat
        mock_storage.update_session_heartbeat.assert_called_once_with('session_123')

    @pytest.mark.asyncio
    async def test_terminate_session(self, session_manager, mock_storage):
        """Prueba terminar sesión"""
        # Crear sesión
        session = NodeSession(session_id='session_123', node_id='node_123')
        session_manager.active_sessions['session_123'] = session

        success = await session_manager.terminate_session('session_123')

        assert success is True
        assert session.status == SessionStatus.TERMINATED
        assert 'session_123' not in session_manager.active_sessions
        mock_storage.store_session.assert_called_once()


if __name__ == '__main__':
    # Ejecutar pruebas
    pytest.main([__file__, '-v'])