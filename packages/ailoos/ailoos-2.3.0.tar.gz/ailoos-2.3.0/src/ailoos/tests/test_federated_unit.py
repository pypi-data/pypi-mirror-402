"""
Tests unitarios para el módulo federated learning.
Cubre todas las funcionalidades principales del sistema federado.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import json
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.ailoos.federated.aggregator import FederatedAggregator, WeightUpdate
from src.ailoos.federated.coordinator import FederatedCoordinator
from src.ailoos.federated.distributed_trainer import DistributedTrainer, TrainingPhase, NodeStatus
from src.ailoos.federated.node_communicator import NodeCommunicator, CommunicationState, RoundPhase
from src.ailoos.federated.p2p_protocol import P2PProtocol, P2PMessage, P2PMessageType, PeerInfo
from src.ailoos.federated.round_orchestrator import RoundOrchestrator, RoundPhase as RO_RoundPhase
from src.ailoos.federated.secure_aggregator import SecureAggregator, EncryptedWeightUpdate
from src.ailoos.federated.session import FederatedSession
from src.ailoos.federated.trainer import FederatedTrainer, TrainingRound
from src.ailoos.core.config import Config


class TestWeightUpdate:
    """Tests para la clase WeightUpdate."""

    def test_weight_update_creation(self):
        """Test creación básica de actualización de pesos."""
        weights = {"layer1": [0.1, 0.2, 0.3], "layer2": [0.4, 0.5]}
        update = WeightUpdate(
            node_id="node_001",
            weights=weights,
            num_samples=100,
            round_num=1
        )

        assert update.node_id == "node_001"
        assert update.weights == weights
        assert update.num_samples == 100
        assert update.round_num == 1
        assert isinstance(update.timestamp, datetime)

    def test_weight_update_validation(self):
        """Test validación de actualización de pesos."""
        # Actualización válida
        valid_update = WeightUpdate(
            node_id="node_001",
            weights={"layer1": [0.1, 0.2]},
            num_samples=50,
            round_num=1
        )
        assert valid_update.is_valid() is True

        # Actualización inválida - pesos vacíos
        invalid_update = WeightUpdate(
            node_id="node_001",
            weights={},
            num_samples=50,
            round_num=1
        )
        assert invalid_update.is_valid() is False

        # Actualización inválida - num_samples cero
        invalid_update2 = WeightUpdate(
            node_id="node_001",
            weights={"layer1": [0.1]},
            num_samples=0,
            round_num=1
        )
        assert invalid_update2.is_valid() is False


class TestFederatedAggregator:
    """Tests para la clase FederatedAggregator."""

    @pytest.fixture
    def aggregator(self):
        """Instancia de FederatedAggregator para tests."""
        return FederatedAggregator(
            session_id="test_session",
            model_name="test_model"
        )

    def test_aggregator_initialization(self, aggregator):
        """Test inicialización del agregador."""
        assert aggregator.session_id == "test_session"
        assert aggregator.model_name == "test_model"
        assert aggregator.expected_participants == []
        assert aggregator.received_updates == {}
        assert aggregator.is_complete is False

    def test_set_expected_participants(self, aggregator):
        """Test configuración de participantes esperados."""
        participants = ["node_001", "node_002", "node_003"]
        aggregator.set_expected_participants(participants)

        assert aggregator.expected_participants == participants
        assert len(aggregator.expected_participants) == 3

    def test_can_aggregate_insufficient_updates(self, aggregator):
        """Test verificación de capacidad de agregación con actualizaciones insuficientes."""
        aggregator.set_expected_participants(["node_001", "node_002", "node_003"])

        # Sin actualizaciones
        assert aggregator.can_aggregate() is False

        # Con una actualización
        weights = {"layer1": [0.1, 0.2]}
        aggregator.add_weight_update("node_001", weights, 100, 1)
        assert aggregator.can_aggregate() is False

    def test_can_aggregate_sufficient_updates(self, aggregator):
        """Test verificación de capacidad de agregación con actualizaciones suficientes."""
        aggregator.set_expected_participants(["node_001", "node_002"])

        # Agregar actualizaciones de ambos nodos
        weights1 = {"layer1": [0.1, 0.2], "layer2": [0.3]}
        weights2 = {"layer1": [0.15, 0.25], "layer2": [0.35]}

        aggregator.add_weight_update("node_001", weights1, 100, 1)
        aggregator.add_weight_update("node_002", weights2, 150, 1)

        assert aggregator.can_aggregate() is True

    def test_add_weight_update(self, aggregator):
        """Test agregado de actualización de pesos."""
        weights = {"layer1": [0.1, 0.2, 0.3]}
        aggregator.add_weight_update("node_001", weights, 100, 1)

        assert "node_001" in aggregator.received_updates
        update = aggregator.received_updates["node_001"]
        assert update.node_id == "node_001"
        assert update.weights == weights
        assert update.num_samples == 100
        assert update.round_num == 1

    def test_aggregate_weights_fedavg(self, aggregator):
        """Test agregación FedAvg básica."""
        aggregator.set_expected_participants(["node_001", "node_002"])

        # Actualizaciones con pesos diferentes
        weights1 = {"layer1": [0.1, 0.2], "layer2": [0.3]}
        weights2 = {"layer1": [0.15, 0.25], "layer2": [0.35]}

        aggregator.add_weight_update("node_001", weights1, 100, 1)
        aggregator.add_weight_update("node_002", weights2, 150, 1)

        # Agregar pesos
        result = aggregator.aggregate_weights()

        # Verificar resultado (promedio ponderado)
        expected_layer1 = [(0.1 * 100 + 0.15 * 150) / 250, (0.2 * 100 + 0.25 * 150) / 250]
        expected_layer2 = [(0.3 * 100 + 0.35 * 150) / 250]

        assert "layer1" in result
        assert "layer2" in result
        assert len(result["layer1"]) == 2
        assert len(result["layer2"]) == 1

        # Verificar valores aproximados
        for i, expected in enumerate(expected_layer1):
            assert abs(result["layer1"][i] - expected) < 0.001

        for i, expected in enumerate(expected_layer2):
            assert abs(result["layer2"][i] - expected) < 0.001

    def test_reset_for_next_round(self, aggregator):
        """Test reinicio para siguiente ronda."""
        # Agregar participantes y actualizaciones
        aggregator.set_expected_participants(["node_001"])
        aggregator.add_weight_update("node_001", {"layer1": [0.1]}, 100, 1)

        # Verificar estado antes del reset
        assert len(aggregator.received_updates) == 1
        assert aggregator.can_aggregate() is True

        # Reset
        aggregator.reset_for_next_round()

        # Verificar estado después del reset
        assert len(aggregator.received_updates) == 0
        assert aggregator.can_aggregate() is False

    def test_get_round_summary(self, aggregator):
        """Test obtención de resumen de ronda."""
        aggregator.set_expected_participants(["node_001", "node_002", "node_003"])

        # Agregar algunas actualizaciones
        aggregator.add_weight_update("node_001", {"layer1": [0.1]}, 100, 1)
        aggregator.add_weight_update("node_002", {"layer1": [0.2]}, 150, 1)

        summary = aggregator.get_round_summary()

        assert "session_id" in summary
        assert "round_num" in summary
        assert "expected_participants" in summary
        assert "received_updates" in summary
        assert "completion_percentage" in summary
        assert summary["session_id"] == "test_session"
        assert summary["expected_participants"] == 3
        assert summary["received_updates"] == 2
        assert summary["completion_percentage"] == (2/3) * 100

    def test_get_aggregation_stats(self, aggregator):
        """Test obtención de estadísticas de agregación."""
        # Agregar actualizaciones con diferentes tamaños de muestra
        aggregator.add_weight_update("node_001", {"layer1": [0.1, 0.2]}, 100, 1)
        aggregator.add_weight_update("node_002", {"layer1": [0.15, 0.25]}, 200, 1)

        stats = aggregator.get_aggregation_stats()

        assert "total_updates" in stats
        assert "total_samples" in stats
        assert "avg_samples_per_update" in stats
        assert "update_timestamps" in stats
        assert stats["total_updates"] == 2
        assert stats["total_samples"] == 300
        assert stats["avg_samples_per_update"] == 150.0


class TestFederatedCoordinator:
    """Tests para la clase FederatedCoordinator."""

    @pytest.fixture
    def coordinator(self):
        """Instancia de FederatedCoordinator para tests."""
        return FederatedCoordinator()

    def test_coordinator_initialization(self, coordinator):
        """Test inicialización del coordinador."""
        assert coordinator.node_id is not None
        assert coordinator.status == "initialized"
        assert coordinator.sessions == {}
        assert coordinator.registered_nodes == {}

    def test_create_session(self, coordinator):
        """Test creación de sesión federada."""
        session = coordinator.create_session(
            session_id="test_session",
            model_name="test_model",
            min_nodes=3,
            max_rounds=5,
            privacy_budget=1.0
        )

        assert session.session_id == "test_session"
        assert session.model_name == "test_model"
        assert session.min_nodes == 3
        assert session.max_rounds == 5
        assert session.privacy_budget == 1.0
        assert session.status == "created"
        assert "test_session" in coordinator.sessions

    def test_add_node_to_session(self, coordinator):
        """Test agregado de nodo a sesión."""
        # Crear sesión primero
        coordinator.create_session("test_session", "test_model", 2)

        # Agregar nodo
        result = coordinator.add_node_to_session("test_session", "node_001")
        assert result is True

        # Verificar que el nodo fue agregado
        session = coordinator.sessions["test_session"]
        assert "node_001" in session.participants

    def test_get_session_status(self, coordinator):
        """Test obtención de estado de sesión."""
        # Crear sesión
        coordinator.create_session("test_session", "test_model", 2)

        status = coordinator.get_session_status("test_session")

        assert "session_id" in status
        assert "status" in status
        assert "participants" in status
        assert "min_nodes" in status
        assert "current_round" in status
        assert status["session_id"] == "test_session"
        assert status["status"] == "created"

    def test_start_training_insufficient_nodes(self, coordinator):
        """Test inicio de entrenamiento con nodos insuficientes."""
        # Crear sesión que requiere 3 nodos
        coordinator.create_session("test_session", "test_model", 3)

        # Agregar solo 2 nodos
        coordinator.add_node_to_session("test_session", "node_001")
        coordinator.add_node_to_session("test_session", "node_002")

        # Intentar iniciar entrenamiento
        result = coordinator.start_training("test_session")

        # Debería fallar por nodos insuficientes
        assert "error" in result
        assert "insufficient participants" in result["error"].lower()

    def test_start_training_success(self, coordinator):
        """Test inicio exitoso de entrenamiento."""
        # Crear sesión
        coordinator.create_session("test_session", "test_model", 2)

        # Agregar nodos suficientes
        coordinator.add_node_to_session("test_session", "node_001")
        coordinator.add_node_to_session("test_session", "node_002")

        # Iniciar entrenamiento
        result = coordinator.start_training("test_session")

        assert "status" in result
        assert "training_started" in result
        assert result["training_started"] is True

        # Verificar estado de la sesión
        session = coordinator.sessions["test_session"]
        assert session.status == "running"

    def test_submit_model_update(self, coordinator):
        """Test envío de actualización de modelo."""
        # Crear y configurar sesión
        coordinator.create_session("test_session", "test_model", 2)
        coordinator.add_node_to_session("test_session", "node_001")
        coordinator.add_node_to_session("test_session", "node_002")
        coordinator.start_training("test_session")

        # Enviar actualización
        update_data = {
            "weights": {"layer1": [0.1, 0.2]},
            "num_samples": 100,
            "round_num": 1
        }

        result = coordinator.submit_model_update("test_session", "node_001", update_data)
        assert result is True

    def test_aggregate_models(self, coordinator):
        """Test agregación de modelos."""
        # Configurar sesión con actualizaciones
        coordinator.create_session("test_session", "test_model", 2)
        coordinator.add_node_to_session("test_session", "node_001")
        coordinator.add_node_to_session("test_session", "node_002")
        coordinator.start_training("test_session")

        # Enviar actualizaciones de ambos nodos
        update1 = {"weights": {"layer1": [0.1, 0.2]}, "num_samples": 100, "round_num": 1}
        update2 = {"weights": {"layer1": [0.15, 0.25]}, "num_samples": 150, "round_num": 1}

        coordinator.submit_model_update("test_session", "node_001", update1)
        coordinator.submit_model_update("test_session", "node_002", update2)

        # Agregar modelos
        result = coordinator.aggregate_models("test_session")

        assert "aggregated_weights" in result
        assert "layer1" in result["aggregated_weights"]
        assert len(result["aggregated_weights"]["layer1"]) == 2

    def test_verify_privacy_budget(self, coordinator):
        """Test verificación de presupuesto de privacidad."""
        # Crear sesión con presupuesto de privacidad
        coordinator.create_session("test_session", "test_model", 2, privacy_budget=1.0)

        # Verificar presupuesto
        result = coordinator.verify_privacy_budget("test_session")

        assert "privacy_preserved" in result
        assert "budget_remaining" in result
        assert result["privacy_preserved"] is True

    def test_get_active_sessions(self, coordinator):
        """Test obtención de sesiones activas."""
        # Crear múltiples sesiones
        coordinator.create_session("session_1", "model_1", 2)
        coordinator.create_session("session_2", "model_2", 3)

        active_sessions = coordinator.get_active_sessions()

        assert len(active_sessions) == 2
        session_ids = [s["session_id"] for s in active_sessions]
        assert "session_1" in session_ids
        assert "session_2" in session_ids

    def test_remove_session(self, coordinator):
        """Test eliminación de sesión."""
        # Crear sesión
        coordinator.create_session("test_session", "test_model", 2)

        # Verificar que existe
        assert "test_session" in coordinator.sessions

        # Remover sesión
        result = coordinator.remove_session("test_session")
        assert result is True

        # Verificar que fue removida
        assert "test_session" not in coordinator.sessions

    def test_register_node(self, coordinator):
        """Test registro de nodo."""
        result = coordinator.register_node("node_001")

        assert "node_id" in result
        assert "status" in result
        assert result["node_id"] == "node_001"
        assert result["status"] == "registered"

        # Verificar que el nodo está registrado
        assert "node_001" in coordinator.registered_nodes


class TestFederatedSession:
    """Tests para la clase FederatedSession."""

    def test_session_creation(self):
        """Test creación básica de sesión federada."""
        session = FederatedSession(
            session_id="test_session",
            model_name="test_model",
            min_nodes=3,
            max_rounds=5,
            privacy_budget=1.0
        )

        assert session.session_id == "test_session"
        assert session.model_name == "test_model"
        assert session.min_nodes == 3
        assert session.max_rounds == 5
        assert session.privacy_budget == 1.0
        assert session.status == "created"
        assert session.participants == []
        assert session.current_round == 0

    def test_add_participant(self, session):
        """Test agregado de participante."""
        session.add_participant("node_001")
        session.add_participant("node_002")

        assert "node_001" in session.participants
        assert "node_002" in session.participants
        assert len(session.participants) == 2

    def test_remove_participant(self, session):
        """Test eliminación de participante."""
        session.add_participant("node_001")
        session.add_participant("node_002")

        session.remove_participant("node_001")

        assert "node_001" not in session.participants
        assert "node_002" in session.participants
        assert len(session.participants) == 1

    def test_can_start_insufficient_participants(self, session):
        """Test verificación de inicio con participantes insuficientes."""
        session.add_participant("node_001")  # Solo 1 de 3 necesarios

        assert session.can_start() is False

    def test_can_start_sufficient_participants(self, session):
        """Test verificación de inicio con participantes suficientes."""
        session.add_participant("node_001")
        session.add_participant("node_002")
        session.add_participant("node_003")  # Ahora tiene los 3 necesarios

        assert session.can_start() is True

    def test_is_complete_not_started(self, session):
        """Test verificación de completitud en sesión no iniciada."""
        assert session.is_complete() is False

    def test_is_complete_max_rounds_reached(self, session):
        """Test verificación de completitud cuando se alcanzan rondas máximas."""
        session.status = "running"
        session.current_round = session.max_rounds  # Alcanzar rondas máximas

        assert session.is_complete() is True

    def test_next_round(self, session):
        """Test avance a siguiente ronda."""
        initial_round = session.current_round

        session.next_round()

        assert session.current_round == initial_round + 1

    def test_get_status(self, session):
        """Test obtención de estado de sesión."""
        # Agregar algunos participantes
        session.add_participant("node_001")
        session.add_participant("node_002")

        status = session.get_status()

        assert "session_id" in status
        assert "status" in status
        assert "participants" in status
        assert "current_round" in status
        assert "completion_percentage" in status
        assert status["session_id"] == "test_session"
        assert status["status"] == "created"
        assert len(status["participants"]) == 2
        assert status["current_round"] == 0

    def test_update_model_cid(self, session):
        """Test actualización de CID del modelo."""
        new_cid = "QmTest123456789"

        session.update_model_cid(new_cid)

        assert session.model_cid == new_cid


class TestDistributedTrainer:
    """Tests para la clase DistributedTrainer."""

    @pytest.fixture
    def config(self):
        """Configuración mock para tests."""
        config = Mock(spec=Config)
        config.p2p_port = 8443
        config.coordinator_host = "localhost"
        config.coordinator_port = 8444
        return config

    @pytest.fixture
    async def distributed_trainer(self, config):
        """Instancia de DistributedTrainer para tests."""
        trainer = DistributedTrainer(
            session_id="test_session",
            model_name="test_model",
            dataset_name="test_dataset"
        )
        yield trainer
        # Cleanup
        await trainer.shutdown()

    @pytest.mark.asyncio
    async def test_initialization(self, distributed_trainer):
        """Test inicialización del DistributedTrainer."""
        assert distributed_trainer.session_id == "test_session"
        assert distributed_trainer.model_name == "test_model"
        assert distributed_trainer.dataset_name == "test_dataset"
        assert distributed_trainer.status == NodeStatus.INITIALIZING

    @pytest.mark.asyncio
    async def test_register_node(self, distributed_trainer):
        """Test registro de nodo."""
        result = await distributed_trainer.register_node(
            node_id="node_001",
            host="127.0.0.1",
            port=8443
        )

        assert result is True
        assert "node_001" in distributed_trainer.nodes
        assert distributed_trainer.nodes["node_001"]["status"] == NodeStatus.REGISTERED

    @pytest.mark.asyncio
    async def test_connect_to_node(self, distributed_trainer):
        """Test conexión a nodo."""
        # Registrar nodo primero
        await distributed_trainer.register_node("node_001", "127.0.0.1", 8443)

        # Mock de conexión P2P
        with patch.object(distributed_trainer.p2p_protocol, 'connect_to_peer', return_value=True):
            result = await distributed_trainer.connect_to_node("node_001")

            assert result is True

    def test_get_training_status(self, distributed_trainer):
        """Test obtención de estado de entrenamiento."""
        status = distributed_trainer.get_training_status()

        assert "session_id" in status
        assert "status" in status
        assert "current_round" in status
        assert "total_rounds" in status
        assert "active_nodes" in status
        assert status["session_id"] == "test_session"

    def test_get_node_status(self, distributed_trainer):
        """Test obtención de estado de nodo."""
        # Estado de nodo no existente
        status = distributed_trainer.get_node_status("nonexistent")
        assert status is None

        # Agregar nodo y verificar estado
        distributed_trainer.nodes["node_001"] = {
            "host": "127.0.0.1",
            "port": 8443,
            "status": NodeStatus.REGISTERED,
            "last_seen": datetime.now()
        }

        status = distributed_trainer.get_node_status("node_001")
        assert status is not None
        assert status["node_id"] == "node_001"
        assert status["status"] == NodeStatus.REGISTERED

    def test_get_round_history(self, distributed_trainer):
        """Test obtención de historial de rondas."""
        # Agregar algunas rondas al historial
        distributed_trainer.round_history = [
            {
                "round_num": 1,
                "status": "completed",
                "participants": ["node_001", "node_002"],
                "accuracy": 0.85
            },
            {
                "round_num": 2,
                "status": "running",
                "participants": ["node_001", "node_002", "node_003"],
                "accuracy": 0.87
            }
        ]

        history = distributed_trainer.get_round_history()

        assert len(history) == 2
        assert history[0]["round_num"] == 1
        assert history[1]["round_num"] == 2


class TestNodeCommunicator:
    """Tests para la clase NodeCommunicator."""

    @pytest.fixture
    async def communicator(self):
        """Instancia de NodeCommunicator para tests."""
        comm = NodeCommunicator(node_id="test_node")
        yield comm
        # Cleanup
        await comm.shutdown()

    @pytest.mark.asyncio
    async def test_initialization(self, communicator):
        """Test inicialización del NodeCommunicator."""
        assert communicator.node_id == "test_node"
        assert communicator.state == CommunicationState.INITIALIZING
        assert communicator.connected_peers == {}
        assert communicator.current_round is None

    @pytest.mark.asyncio
    async def test_send_model_update_without_protocol(self, communicator):
        """Test envío de actualización sin protocolo P2P."""
        update = Mock()
        update.node_id = "test_node"
        update.round_num = 1

        # Intentar enviar sin protocolo inicializado
        result = await communicator.send_model_update("peer_001", update)

        assert result is False

    @pytest.mark.asyncio
    async def test_broadcast_model_update(self, communicator):
        """Test broadcast de actualización de modelo."""
        update = Mock()
        update.node_id = "test_node"
        update.round_num = 1

        # Mock de peers conectados
        communicator.connected_peers = {"peer_001": Mock(), "peer_002": Mock()}

        # Mock del método de envío
        with patch.object(communicator, '_send_message_to_peer', return_value=True) as mock_send:
            result = await communicator.broadcast_model_update(update)

            assert result is True
            assert mock_send.call_count == 2  # Uno por cada peer

    @pytest.mark.asyncio
    async def test_start_round(self, communicator):
        """Test inicio de ronda."""
        participants = ["node_001", "node_002", "node_003"]

        # Mock del método de notificación
        with patch.object(communicator, '_notify_round_start', return_value=True) as mock_notify:
            result = await communicator.start_round(1, participants)

            assert result is True
            assert communicator.current_round == 1
            assert communicator.round_participants == participants
            mock_notify.assert_called_once_with(participants)

    def test_get_peer_status(self, communicator):
        """Test obtención de estado de peer."""
        # Peer no conectado
        status = communicator.get_peer_status("nonexistent")
        assert status["connected"] is False

        # Agregar peer conectado
        communicator.connected_peers["peer_001"] = {
            "host": "127.0.0.1",
            "port": 8443,
            "connected_at": datetime.now(),
            "last_message": datetime.now()
        }

        status = communicator.get_peer_status("peer_001")
        assert status["connected"] is True
        assert status["host"] == "127.0.0.1"
        assert status["port"] == 8443

    def test_get_connected_peers(self, communicator):
        """Test obtención de peers conectados."""
        # Sin peers conectados
        peers = communicator.get_connected_peers()
        assert peers == []

        # Agregar peers
        communicator.connected_peers = {
            "peer_001": {"host": "127.0.0.1", "port": 8443},
            "peer_002": {"host": "127.0.0.2", "port": 8443}
        }

        peers = communicator.get_connected_peers()
        assert len(peers) == 2
        assert "peer_001" in peers
        assert "peer_002" in peers

    def test_get_communication_stats(self, communicator):
        """Test obtención de estadísticas de comunicación."""
        # Agregar algunos datos de prueba
        communicator.message_counts = {"model_update": 10, "round_start": 5}
        communicator.error_counts = {"connection_failed": 2}
        communicator.connected_peers = {"peer_001": {}, "peer_002": {}}

        stats = communicator.get_communication_stats()

        assert "total_messages" in stats
        assert "total_errors" in stats
        assert "connected_peers" in stats
        assert "messages_by_type" in stats
        assert stats["total_messages"] == 15
        assert stats["total_errors"] == 2
        assert stats["connected_peers"] == 2

    def test_get_current_round_info(self, communicator):
        """Test obtención de información de ronda actual."""
        # Sin ronda activa
        info = communicator.get_current_round_info()
        assert info is None

        # Con ronda activa
        communicator.current_round = 5
        communicator.round_participants = ["node_001", "node_002"]
        communicator.round_start_time = datetime.now()

        info = communicator.get_current_round_info()
        assert info is not None
        assert info["round_num"] == 5
        assert info["participants"] == ["node_001", "node_002"]
        assert "start_time" in info


class TestP2PProtocol:
    """Tests para la clase P2PProtocol."""

    @pytest.fixture
    async def p2p_protocol(self):
        """Instancia de P2PProtocol para tests."""
        protocol = P2PProtocol(node_id="test_node")
        yield protocol
        # Cleanup
        await protocol.stop()

    @pytest.mark.asyncio
    async def test_initialization(self, p2p_protocol):
        """Test inicialización del P2PProtocol."""
        assert p2p_protocol.node_id == "test_node"
        assert p2p_protocol.peers == {}
        assert p2p_protocol.server is None

    def test_generate_self_signed_certificate(self, p2p_protocol):
        """Test generación de certificado autofirmado."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cert_path = Path(temp_dir) / "test_cert.pem"
            key_path = Path(temp_dir) / "test_key.pem"

            p2p_protocol._generate_self_signed_certificate(cert_path, key_path)

            assert cert_path.exists()
            assert key_path.exists()

            # Verificar contenido básico del certificado
            with open(cert_path, 'r') as f:
                cert_content = f.read()
                assert "BEGIN CERTIFICATE" in cert_content

            with open(key_path, 'r') as f:
                key_content = f.read()
                assert "BEGIN PRIVATE KEY" in key_content

    @pytest.mark.asyncio
    async def test_connect_to_peer(self, p2p_protocol):
        """Test conexión a peer."""
        peer_info = PeerInfo(
            node_id="peer_001",
            host="127.0.0.1",
            port=8443,
            public_key="test_key"
        )

        # Mock de conexión
        with patch('asyncio.open_connection') as mock_connect:
            mock_reader = Mock()
            mock_writer = Mock()
            mock_connect.return_value = (mock_reader, mock_writer)

            result = await p2p_protocol.connect_to_peer(peer_info)

            assert result is True
            assert "peer_001" in p2p_protocol.peers

    def test_sign_message(self, p2p_protocol):
        """Test firma de mensaje."""
        message = P2PMessage(
            message_type=P2PMessageType.MODEL_UPDATE,
            sender_id="test_node",
            receiver_id="peer_001",
            payload={"weights": [0.1, 0.2]},
            timestamp=datetime.now()
        )

        signature = p2p_protocol._sign_message(message)

        assert isinstance(signature, str)
        assert len(signature) > 0

    def test_verify_message_signature(self, p2p_protocol):
        """Test verificación de firma de mensaje."""
        message = P2PMessage(
            message_type=P2PMessageType.MODEL_UPDATE,
            sender_id="test_node",
            receiver_id="peer_001",
            payload={"test": "data"},
            timestamp=datetime.now()
        )

        # Firmar mensaje
        signature = p2p_protocol._sign_message(message)
        message.signature = signature

        # Verificar firma
        is_valid = p2p_protocol._verify_message_signature(message)

        assert is_valid is True

    def test_get_stats(self, p2p_protocol):
        """Test obtención de estadísticas del protocolo."""
        # Agregar algunos datos de prueba
        p2p_protocol.peers = {
            "peer_001": {"connected": True, "messages_sent": 10},
            "peer_002": {"connected": True, "messages_sent": 5}
        }
        p2p_protocol.message_counts = {"model_update": 15, "heartbeat": 50}

        stats = p2p_protocol.get_stats()

        assert "total_peers" in stats
        assert "connected_peers" in stats
        assert "total_messages" in stats
        assert "messages_by_type" in stats
        assert stats["total_peers"] == 2
        assert stats["connected_peers"] == 2
        assert stats["total_messages"] == 65


class TestRoundOrchestrator:
    """Tests para la clase RoundOrchestrator."""

    @pytest.fixture
    def config(self):
        """Configuración mock para tests."""
        config = Mock(spec=Config)
        config.round_timeout = 300
        config.min_participants_per_round = 3
        return config

    @pytest.fixture
    async def orchestrator(self, config):
        """Instancia de RoundOrchestrator para tests."""
        orch = RoundOrchestrator(session_id="test_session", config=config)
        yield orch
        # Cleanup
        await orch.shutdown()

    @pytest.mark.asyncio
    async def test_initialization(self, orchestrator):
        """Test inicialización del RoundOrchestrator."""
        assert orchestrator.session_id == "test_session"
        assert orchestrator.rounds == {}
        assert orchestrator.current_round_id is None

    @pytest.mark.asyncio
    async def test_create_round(self, orchestrator):
        """Test creación de ronda."""
        round_config = {
            "max_participants": 5,
            "min_participants": 3,
            "timeout_seconds": 300,
            "aggregation_method": "fedavg"
        }

        round_id = await orchestrator.create_round(round_config)

        assert round_id is not None
        assert round_id in orchestrator.rounds
        assert orchestrator.rounds[round_id].config.max_participants == 5

    @pytest.mark.asyncio
    async def test_start_round(self, orchestrator):
        """Test inicio de ronda."""
        # Crear ronda primero
        round_config = {"max_participants": 3, "min_participants": 2}
        round_id = await orchestrator.create_round(round_config)

        # Agregar participantes
        await orchestrator.add_node_to_round(round_id, "node_001")
        await orchestrator.add_node_to_round(round_id, "node_002")

        # Iniciar ronda
        result = await orchestrator.start_round(round_id)

        assert result is True
        round_state = orchestrator.rounds[round_id]
        assert round_state.status == RO_RoundPhase.RUNNING

    @pytest.mark.asyncio
    async def test_add_node_to_round(self, orchestrator):
        """Test agregado de nodo a ronda."""
        # Crear ronda
        round_id = await orchestrator.create_round()

        # Agregar nodo
        result = await orchestrator.add_node_to_round(round_id, "node_001")

        assert result is True
        round_state = orchestrator.rounds[round_id]
        assert "node_001" in round_state.participants

    @pytest.mark.asyncio
    async def test_submit_contribution(self, orchestrator):
        """Test envío de contribución."""
        # Crear y configurar ronda
        round_id = await orchestrator.create_round()
        await orchestrator.add_node_to_round(round_id, "node_001")
        await orchestrator.start_round(round_id)

        # Enviar contribución
        contribution = {
            "node_id": "node_001",
            "weights": {"layer1": [0.1, 0.2]},
            "num_samples": 100,
            "zkp_proof": "mock_proof"
        }

        result = await orchestrator.submit_contribution(round_id, "node_001", contribution)

        assert result is True
        round_state = orchestrator.rounds[round_id]
        assert len(round_state.contributions) == 1

    def test_get_round_status(self, orchestrator):
        """Test obtención de estado de ronda."""
        # Estado de ronda inexistente
        status = orchestrator.get_round_status("nonexistent")
        assert status is None

        # Crear ronda y verificar estado
        round_id = "test_round_001"
        orchestrator.rounds[round_id] = Mock()
        orchestrator.rounds[round_id].status = RO_RoundPhase.WAITING
        orchestrator.rounds[round_id].participants = ["node_001", "node_002"]
        orchestrator.rounds[round_id].get_progress_percentage.return_value = 66.7

        status = orchestrator.get_round_status(round_id)

        assert status is not None
        assert status["round_id"] == round_id
        assert status["status"] == RO_RoundPhase.WAITING
        assert len(status["participants"]) == 2

    def test_get_orchestrator_stats(self, orchestrator):
        """Test obtención de estadísticas del orquestador."""
        # Agregar algunas rondas de prueba
        orchestrator.rounds = {
            "round_001": Mock(status=RO_RoundPhase.COMPLETED),
            "round_002": Mock(status=RO_RoundPhase.RUNNING),
            "round_003": Mock(status=RO_RoundPhase.FAILED)
        }

        stats = orchestrator.get_orchestrator_stats()

        assert "total_rounds" in stats
        assert "active_rounds" in stats
        assert "completed_rounds" in stats
        assert "failed_rounds" in stats
        assert stats["total_rounds"] == 3
        assert stats["active_rounds"] == 1
        assert stats["completed_rounds"] == 1
        assert stats["failed_rounds"] == 1


class TestSecureAggregator:
    """Tests para la clase SecureAggregator."""

    @pytest.fixture
    def secure_aggregator(self):
        """Instancia de SecureAggregator para tests."""
        return SecureAggregator(
            session_id="test_session",
            model_name="test_model"
        )

    def test_initialization(self, secure_aggregator):
        """Test inicialización del SecureAggregator."""
        assert secure_aggregator.session_id == "test_session"
        assert secure_aggregator.model_name == "test_model"
        assert secure_aggregator.expected_participants == []
        assert secure_aggregator.encrypted_updates == {}
        assert not secure_aggregator.is_complete

    def test_set_expected_participants(self, secure_aggregator):
        """Test configuración de participantes esperados."""
        participants = ["node_001", "node_002"]
        secure_aggregator.set_expected_participants(participants)

        assert secure_aggregator.expected_participants == participants

    def test_can_aggregate(self, secure_aggregator):
        """Test verificación de capacidad de agregación."""
        secure_aggregator.set_expected_participants(["node_001", "node_002"])

        # Sin actualizaciones
        assert not secure_aggregator.can_aggregate()

        # Con una actualización
        secure_aggregator.add_encrypted_weight_update(
            "node_001",
            {"layer1": "encrypted_data"},
            100
        )
        assert not secure_aggregator.can_aggregate()

        # Con ambas actualizaciones
        secure_aggregator.add_encrypted_weight_update(
            "node_002",
            {"layer1": "encrypted_data"},
            150
        )
        assert secure_aggregator.can_aggregate()

    def test_add_encrypted_weight_update(self, secure_aggregator):
        """Test agregado de actualización encriptada."""
        encrypted_weights = {"layer1": "encrypted_tensor_data"}
        secure_aggregator.add_encrypted_weight_update(
            "node_001",
            encrypted_weights,
            100
        )

        assert "node_001" in secure_aggregator.encrypted_updates
        update = secure_aggregator.encrypted_updates["node_001"]
        assert update.node_id == "node_001"
        assert update.encrypted_weights == encrypted_weights
        assert update.num_samples == 100

    def test_reset_for_next_round(self, secure_aggregator):
        """Test reinicio para siguiente ronda."""
        # Agregar actualización
        secure_aggregator.add_encrypted_weight_update(
            "node_001",
            {"layer1": "data"},
            100
        )

        # Verificar antes del reset
        assert len(secure_aggregator.encrypted_updates) == 1

        # Reset
        secure_aggregator.reset_for_next_round()

        # Verificar después del reset
        assert len(secure_aggregator.encrypted_updates) == 0
        assert not secure_aggregator.is_complete

    def test_get_round_summary(self, secure_aggregator):
        """Test obtención de resumen de ronda."""
        secure_aggregator.set_expected_participants(["node_001", "node_002", "node_003"])

        # Agregar actualizaciones
        secure_aggregator.add_encrypted_weight_update("node_001", {"layer1": "data1"}, 100)
        secure_aggregator.add_encrypted_weight_update("node_002", {"layer1": "data2"}, 150)

        summary = secure_aggregator.get_round_summary()

        assert "session_id" in summary
        assert "expected_participants" in summary
        assert "received_updates" in summary
        assert "completion_percentage" in summary
        assert summary["session_id"] == "test_session"
        assert summary["expected_participants"] == 3
        assert summary["received_updates"] == 2
        assert summary["completion_percentage"] == (2/3) * 100

    def test_get_aggregation_stats(self, secure_aggregator):
        """Test obtención de estadísticas de agregación."""
        # Agregar actualizaciones
        secure_aggregator.add_encrypted_weight_update("node_001", {"layer1": "data1"}, 100)
        secure_aggregator.add_encrypted_weight_update("node_002", {"layer1": "data2"}, 200)

        stats = secure_aggregator.get_aggregation_stats()

        assert "total_updates" in stats
        assert "total_samples" in stats
        assert "avg_samples_per_update" in stats
        assert stats["total_updates"] == 2
        assert stats["total_samples"] == 300
        assert stats["avg_samples_per_update"] == 150.0


class TestFederatedTrainer:
    """Tests para la clase FederatedTrainer."""

    @pytest.fixture
    def trainer(self):
        """Instancia de FederatedTrainer para tests."""
        return FederatedTrainer(
            session_id="test_session",
            model_name="test_model",
            dataset_name="test_dataset"
        )

    def test_initialization(self, trainer):
        """Test inicialización del FederatedTrainer."""
        assert trainer.session_id == "test_session"
        assert trainer.model_name == "test_model"
        assert trainer.dataset_name == "test_dataset"
        assert trainer.rounds == []

    def test_start_new_round(self, trainer):
        """Test inicio de nueva ronda."""
        participants = ["node_001", "node_002", "node_003"]

        round_obj = trainer.start_new_round(participants)

        assert isinstance(round_obj, TrainingRound)
        assert round_obj.round_num == 1
        assert round_obj.participants == participants
        assert round_obj.status == "running"

        # Verificar que se agregó a la lista de rondas
        assert len(trainer.rounds) == 1
        assert trainer.rounds[0] == round_obj

    def test_complete_round(self, trainer):
        """Test completación de ronda."""
        # Iniciar ronda
        round_obj = trainer.start_new_round(["node_001", "node_002"])

        # Completar ronda
        trainer.complete_round(0.85, 0.3)

        # Verificar que la ronda se actualizó
        assert round_obj.accuracy == 0.85
        assert round_obj.loss == 0.3
        assert round_obj.status == "completed"
        assert round_obj.end_time is not None

    def test_get_current_model_info(self, trainer):
        """Test obtención de información del modelo actual."""
        info = trainer.get_current_model_info()

        assert "model_name" in info
        assert "session_id" in info
        assert "total_rounds" in info
        assert "current_accuracy" in info
        assert info["model_name"] == "test_model"
        assert info["session_id"] == "test_session"
        assert info["total_rounds"] == 0

    def test_get_round_history(self, trainer):
        """Test obtención de historial de rondas."""
        # Agregar rondas de prueba
        trainer.rounds = [
            TrainingRound(1, ["node_001", "node_002"], "completed", 0.8, 0.4),
            TrainingRound(2, ["node_001", "node_002", "node_003"], "running", 0.85, 0.3)
        ]

        history = trainer.get_round_history()

        assert len(history) == 2
        assert history[0]["round_num"] == 1
        assert history[0]["status"] == "completed"
        assert history[0]["accuracy"] == 0.8
        assert history[1]["round_num"] == 2
        assert history[1]["status"] == "running"

    def test_get_status(self, trainer):
        """Test obtención de estado del trainer."""
        # Agregar algunas rondas
        trainer.start_new_round(["node_001", "node_002"])
        trainer.complete_round(0.82, 0.35)

        status = trainer.get_status()

        assert "session_id" in status
        assert "model_name" in status
        assert "status" in status
        assert "current_round" in status
        assert "total_rounds" in status
        assert "best_accuracy" in status