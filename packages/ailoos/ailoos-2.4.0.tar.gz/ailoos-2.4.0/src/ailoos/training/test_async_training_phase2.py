"""
Tests unitarios para la FASE 2: Entrenamiento Asíncrono
Cubre todos los componentes: TrainingStateManager, CheckpointManager, AsyncTrainingController, etc.
"""

import asyncio
import pytest
import tempfile
import shutil
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json
import time
from typing import Dict, Any

# Importar componentes a testear
from .training_state_manager import TrainingStateManager, TrainingStatus
from .checkpoint_manager import CheckpointManager, CheckpointConfig, CompressionType
from .async_training_controller import AsyncTrainingController, AsyncTrainingConfig, TrainingPhase
from .training_progress_tracker import TrainingProgressTracker
from .network_sync_manager import NetworkSyncManager, NetworkStatus, SyncOperation
from .training_api import TrainingAPIService, TrainingAPIConfig


class SimpleModel(nn.Module):
    """Modelo simple para tests."""
    def __init__(self, input_size=10, hidden_size=5, output_size=2):
        super().__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        return self.fc2(x)


class TestTrainingStateManager:
    """Tests para TrainingStateManager."""

    @pytest.fixture
    def temp_dir(self):
        """Directorio temporal para tests."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    async def state_manager(self, temp_dir):
        """Instancia de TrainingStateManager para tests."""
        manager = TrainingStateManager(temp_dir)
        yield manager

    @pytest.mark.asyncio
    async def test_create_session(self, state_manager):
        """Test creación de sesión."""
        session = await state_manager.create_session(
            session_id="test_session",
            model_version="v1.0",
            training_config={"epochs": 10},
            model_config={"type": "test"}
        )

        assert session.session_id == "test_session"
        assert session.status == TrainingStatus.NOT_STARTED
        assert session.model_version == "v1.0"

    @pytest.mark.asyncio
    async def test_update_progress(self, state_manager):
        """Test actualización de progreso."""
        # Crear sesión
        await state_manager.create_session("test_session", "v1.0", {}, {})

        # Actualizar progreso
        await state_manager.update_session_progress(
            session_id="test_session",
            epoch=1,
            batch=10,
            loss=0.5,
            accuracy=0.8,
            learning_rate=0.001,
            optimizer_state={}
        )

        # Verificar
        session = await state_manager.get_session("test_session")
        assert session.current_epoch == 1
        assert session.current_batch == 10
        assert session.loss_history == [0.5]
        assert session.accuracy_history == [0.8]

    @pytest.mark.asyncio
    async def test_pause_resume(self, state_manager):
        """Test pausa y reanudación."""
        # Crear sesión
        await state_manager.create_session("test_session", "v1.0", {}, {})

        # Pausar
        await state_manager.pause_session("test_session")
        session = await state_manager.get_session("test_session")
        assert session.status == TrainingStatus.PAUSED

        # Reanudar
        resumed_session = await state_manager.resume_session("test_session")
        assert resumed_session.status == TrainingStatus.RUNNING

    @pytest.mark.asyncio
    async def test_checkpoint_operations(self, state_manager):
        """Test operaciones de checkpoint."""
        # Crear sesión
        await state_manager.create_session("test_session", "v1.0", {}, {})

        # Crear checkpoint
        checkpoint_id = await state_manager.create_checkpoint(
            session_id="test_session",
            model_state={"layer1": torch.randn(5, 5)},
            optimizer_state={},
            epoch=1,
            batch=5,
            metadata={"test": True}
        )

        assert checkpoint_id is not None

        # Listar checkpoints
        checkpoints = await state_manager.list_checkpoints("test_session")
        assert len(checkpoints) == 1
        assert checkpoints[0].checkpoint_id == checkpoint_id

        # Cargar checkpoint
        data = await state_manager.load_checkpoint(checkpoint_id)
        assert "model_state" in data
        assert "epoch" in data
        assert data["epoch"] == 1


class TestCheckpointManager:
    """Tests para CheckpointManager."""

    @pytest.fixture
    def temp_dir(self):
        """Directorio temporal para tests."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    async def checkpoint_manager(self, temp_dir):
        """Instancia de CheckpointManager para tests."""
        config = CheckpointConfig(compression=CompressionType.NONE)  # Sin compresión para tests
        manager = CheckpointManager(temp_dir, config)
        yield manager

    @pytest.mark.asyncio
    async def test_save_load_checkpoint(self, checkpoint_manager):
        """Test guardar y cargar checkpoint."""
        model = SimpleModel()
        optimizer = optim.SGD(model.parameters(), lr=0.01)

        # Guardar checkpoint
        checkpoint_id = await checkpoint_manager.save_checkpoint(
            session_id="test_session",
            model=model,
            optimizer=optimizer,
            epoch=1,
            batch=10,
            global_step=100,
            metrics={"loss": 0.5, "accuracy": 0.8}
        )

        assert checkpoint_id is not None

        # Cargar checkpoint
        data = await checkpoint_manager.load_checkpoint(checkpoint_id)
        assert "model_state" in data
        assert "optimizer_state" in data
        assert data["epoch"] == 1
        assert data["metrics"]["loss"] == 0.5

    @pytest.mark.asyncio
    async def test_list_checkpoints(self, checkpoint_manager):
        """Test listar checkpoints."""
        model = SimpleModel()
        optimizer = optim.SGD(model.parameters(), lr=0.01)

        # Crear varios checkpoints
        for i in range(3):
            await checkpoint_manager.save_checkpoint(
                session_id="test_session",
                model=model,
                optimizer=optimizer,
                epoch=i,
                batch=i*10,
                global_step=i*100,
                metrics={"loss": 0.5 - i*0.1}
            )

        # Listar checkpoints
        checkpoints = await checkpoint_manager.list_checkpoints("test_session")
        assert len(checkpoints) == 3

        # Verificar orden (más recientes primero)
        assert checkpoints[0].epoch > checkpoints[1].epoch

    @pytest.mark.asyncio
    async def test_cleanup_checkpoints(self, checkpoint_manager):
        """Test limpieza de checkpoints antiguos."""
        model = SimpleModel()
        optimizer = optim.SGD(model.parameters(), lr=0.01)

        # Crear varios checkpoints
        for i in range(5):
            await checkpoint_manager.save_checkpoint(
                session_id="test_session",
                model=model,
                optimizer=optimizer,
                epoch=i,
                batch=i*10,
                global_step=i*100
            )

        # Verificar que hay 5 checkpoints
        checkpoints = await checkpoint_manager.list_checkpoints("test_session")
        assert len(checkpoints) == 5

        # Limpiar manteniendo solo 2
        deleted = await checkpoint_manager.cleanup_checkpoints("test_session", keep_last=2)
        assert deleted == 3

        # Verificar que quedan 2
        checkpoints = await checkpoint_manager.list_checkpoints("test_session")
        assert len(checkpoints) == 2


class TestTrainingProgressTracker:
    """Tests para TrainingProgressTracker."""

    @pytest.fixture
    async def progress_tracker(self):
        """Instancia de TrainingProgressTracker para tests."""
        tracker = TrainingProgressTracker()
        yield tracker

    @pytest.mark.asyncio
    async def test_initialization(self, progress_tracker):
        """Test inicialización."""
        await progress_tracker.initialize_session(
            session_id="test_session",
            total_epochs=10,
            batches_per_epoch=100
        )

        progress = await progress_tracker.get_progress()
        assert progress.session_id == "test_session"
        assert progress.total_epochs == 10
        assert progress.total_batches_per_epoch == 100

    @pytest.mark.asyncio
    async def test_progress_updates(self, progress_tracker):
        """Test actualizaciones de progreso."""
        await progress_tracker.initialize_session("test_session", 10, 100)

        # Actualizar batch
        await progress_tracker.update_batch_progress(
            batch_idx=5,
            batch_time=0.1,
            loss=0.5,
            accuracy=0.8,
            learning_rate=0.001
        )

        progress = await progress_tracker.get_progress()
        assert progress.current_batch == 5
        assert progress.loss == 0.5
        assert progress.accuracy == 0.8
        assert len(progress.loss_history) == 1

        # Actualizar época
        await progress_tracker.update_epoch_progress(1, {"epoch_time": 10.0})

        progress = await progress_tracker.get_progress()
        assert progress.current_epoch == 1

    @pytest.mark.asyncio
    async def test_milestones(self, progress_tracker):
        """Test detección de milestones."""
        milestones_reached = []

        async def milestone_callback(name, data):
            milestones_reached.append((name, data))

        progress_tracker.on_milestone_reached = milestone_callback

        await progress_tracker.initialize_session("test_session", 10, 100)

        # Primera época
        await progress_tracker.update_epoch_progress(1, {})
        await asyncio.sleep(0.1)  # Dar tiempo a callbacks

        assert len(milestones_reached) >= 1
        assert milestones_reached[0][0] == "first_epoch_completed"

    @pytest.mark.asyncio
    async def test_resume_from_checkpoint(self, progress_tracker):
        """Test reanudación desde checkpoint."""
        await progress_tracker.initialize_session("test_session", 10, 100)

        # Simular checkpoint data
        checkpoint_data = {
            "loss_history": [0.8, 0.6, 0.4],
            "accuracy_history": [0.6, 0.7, 0.8],
            "metrics": {"val_loss": 0.5}
        }

        await progress_tracker.resume_from_checkpoint(
            current_epoch=3,
            global_step=300,
            checkpoint_metrics=checkpoint_data
        )

        progress = await progress_tracker.get_progress()
        assert progress.current_epoch == 3
        assert progress.global_step == 300
        assert progress.loss_history == [0.8, 0.6, 0.4]


class TestNetworkSyncManager:
    """Tests para NetworkSyncManager."""

    @pytest.fixture
    async def network_manager(self):
        """Instancia de NetworkSyncManager para tests."""
        manager = NetworkSyncManager(node_id="test_node", listen_port=8766)
        yield manager
        await manager.stop()

    @pytest.mark.asyncio
    async def test_initialization(self, network_manager):
        """Test inicialización."""
        status = await network_manager.get_network_status()
        assert status["node_id"] == "test_node"
        assert status["listen_port"] == 8766
        assert status["status"] in [NetworkStatus.OFFLINE.value, NetworkStatus.ONLINE.value]

    @pytest.mark.asyncio
    async def test_peer_management(self, network_manager):
        """Test gestión de peers."""
        # Añadir peer
        await network_manager.add_peer("peer1", "192.168.1.100", 8765)

        status = await network_manager.get_network_status()
        assert status["peers_count"] == 1
        assert "peer1" in status["peers"]

        # Remover peer
        await network_manager.remove_peer("peer1")

        status = await network_manager.get_network_status()
        assert status["peers_count"] == 0

    @pytest.mark.asyncio
    async def test_sync_operations(self, network_manager):
        """Test operaciones de sincronización."""
        # Añadir peer mock
        await network_manager.add_peer("peer1", "127.0.0.1", 8767)

        # Mock de conexión
        with patch.object(network_manager, 'active_connections', {"peer1": Mock()}):
            with patch.object(network_manager, '_send_request_to_peer', new_callable=AsyncMock) as mock_send:
                mock_send.return_value = Mock(success=True, data={"received": True})

                # Sincronizar métricas
                responses = await network_manager.sync_metrics(
                    session_id="test_session",
                    metrics={"loss": 0.5}
                )

                assert len(responses) == 1
                assert responses[0].success == True


class TestAsyncTrainingController:
    """Tests para AsyncTrainingController."""

    @pytest.fixture
    def temp_dir(self):
        """Directorio temporal para tests."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    def model_and_data(self):
        """Modelo y datos de prueba."""
        model = SimpleModel()
        optimizer = optim.SGD(model.parameters(), lr=0.01)
        criterion = nn.CrossEntropyLoss()

        # Crear dataset dummy
        train_data = [(torch.randn(10), torch.randint(0, 2, (1,)).squeeze()) for _ in range(20)]
        train_loader = torch.utils.data.DataLoader(train_data, batch_size=4)

        return model, optimizer, criterion, train_loader

    @pytest.fixture
    async def training_controller(self, temp_dir, model_and_data):
        """Instancia de AsyncTrainingController para tests."""
        model, optimizer, criterion, train_loader = model_and_data

        config = AsyncTrainingConfig(
            session_id="test_session",
            model=model,
            optimizer=optimizer,
            criterion=criterion,
            train_dataloader=train_loader,
            max_epochs=2,
            checkpoint_interval=1000,  # No crear checkpoints en test
            state_dir=temp_dir,
            checkpoint_dir=temp_dir
        )

        controller = AsyncTrainingController(config)
        yield controller

    @pytest.mark.asyncio
    async def test_initialization(self, training_controller):
        """Test inicialización."""
        status = await training_controller.get_training_status()
        assert status["session_id"] == "test_session"
        assert status["current_phase"] == TrainingPhase.INITIALIZING.value
        assert not status["is_running"]

    @pytest.mark.asyncio
    async def test_pause_resume(self, training_controller):
        """Test pausa y reanudación."""
        # Pausar (debería fallar porque no está corriendo)
        await training_controller.pause_training()
        assert training_controller.is_paused

        # Reanudar
        await training_controller.resume_training()
        assert not training_controller.is_paused

    @pytest.mark.asyncio
    async def test_control_methods(self, training_controller):
        """Test métodos de control."""
        # Detener
        await training_controller.stop_training()
        assert training_controller.should_stop

        # Verificar estado
        status = await training_controller.get_training_status()
        assert status["is_running"] == False


class TestTrainingAPI:
    """Tests para TrainingAPI."""

    @pytest.fixture
    def temp_dir(self):
        """Directorio temporal para tests."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    async def api_service(self, temp_dir):
        """Instancia de TrainingAPIService para tests."""
        config = TrainingAPIConfig(
            host="127.0.0.1",
            port=8002,  # Puerto diferente para tests
            node_id="test_api_node",
            state_dir=temp_dir,
            checkpoint_dir=temp_dir,
            enable_docs=False  # Deshabilitar docs para tests
        )

        service = TrainingAPIService(config)
        yield service

    def test_api_initialization(self, api_service):
        """Test inicialización de API."""
        assert api_service.config.node_id == "test_api_node"
        assert api_service.config.port == 8002
        assert len(api_service.app.routes) > 0  # Debería tener rutas

    @pytest.mark.asyncio
    async def test_health_endpoint(self, api_service):
        """Test endpoint de health check."""
        from fastapi.testclient import TestClient
        client = TestClient(api_service.app)

        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "node_id" in data
        assert data["node_id"] == "test_api_node"

    @pytest.mark.asyncio
    async def test_session_management(self, api_service):
        """Test gestión de sesiones vía API."""
        from fastapi.testclient import TestClient
        client = TestClient(api_service.app)

        # Crear sesión
        session_data = {
            "session_id": "api_test_session",
            "model_config": {"type": "test"},
            "training_config": {"epochs": 5}
        }

        response = client.post("/api/v1/training/sessions", json=session_data)
        assert response.status_code == 200

        data = response.json()
        assert data["session_id"] == "api_test_session"

        # Listar sesiones
        response = client.get("/api/v1/training/sessions")
        assert response.status_code == 200

        data = response.json()
        assert len(data["sessions"]) >= 1
        assert any(s["session_id"] == "api_test_session" for s in data["sessions"])


# Tests de integración
class TestIntegration:
    """Tests de integración entre componentes."""

    @pytest.fixture
    def temp_dir(self):
        """Directorio temporal para tests."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.mark.asyncio
    async def test_full_training_workflow(self, temp_dir):
        """Test workflow completo de entrenamiento."""
        # Crear componentes
        state_manager = TrainingStateManager(temp_dir)
        checkpoint_manager = CheckpointManager(temp_dir)
        progress_tracker = TrainingProgressTracker()

        # Crear sesión
        session = await state_manager.create_session(
            session_id="integration_test",
            model_version="v1.0",
            training_config={"max_epochs": 1},
            model_config={"type": "test"}
        )

        assert session.session_id == "integration_test"
        assert session.status == TrainingStatus.NOT_STARTED

        # Simular progreso
        await state_manager.update_session_progress(
            session_id="integration_test",
            epoch=0,
            batch=5,
            loss=0.7,
            accuracy=0.75,
            learning_rate=0.01,
            optimizer_state={}
        )

        # Verificar progreso
        updated_session = await state_manager.get_session("integration_test")
        assert updated_session.current_batch == 5
        assert updated_session.loss_history == [0.7]

        # Completar sesión
        await state_manager.complete_session("integration_test")

        final_session = await state_manager.get_session("integration_test")
        assert final_session.status == TrainingStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_checkpoint_workflow(self, temp_dir):
        """Test workflow de checkpoints."""
        checkpoint_manager = CheckpointManager(temp_dir)

        # Crear modelo dummy
        model = SimpleModel()
        optimizer = optim.SGD(model.parameters(), lr=0.01)

        # Guardar checkpoint
        checkpoint_id = await checkpoint_manager.save_checkpoint(
            session_id="checkpoint_test",
            model=model,
            optimizer=optimizer,
            epoch=1,
            batch=10,
            global_step=100,
            metrics={"loss": 0.5}
        )

        assert checkpoint_id is not None

        # Cargar checkpoint
        data = await checkpoint_manager.load_checkpoint(checkpoint_id)
        assert data["epoch"] == 1
        assert data["metrics"]["loss"] == 0.5

        # Listar checkpoints
        checkpoints = await checkpoint_manager.list_checkpoints("checkpoint_test")
        assert len(checkpoints) == 1

        # Limpiar
        deleted = await checkpoint_manager.cleanup_checkpoints("checkpoint_test", keep_last=0)
        assert deleted == 1

        checkpoints = await checkpoint_manager.list_checkpoints("checkpoint_test")
        assert len(checkpoints) == 0


if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v"])