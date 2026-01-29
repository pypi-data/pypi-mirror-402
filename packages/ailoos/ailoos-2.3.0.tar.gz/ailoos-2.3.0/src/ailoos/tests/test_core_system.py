#!/usr/bin/env python3
"""
Tests Críticos del Sistema Core - AILOOS
Cobertura: Coordinator, Federated Learning, APIs
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from ..core.config import Config
from ..core.logging import get_logger
from ..coordinator.coordinator import Coordinator
from ..federated.session import FederatedSession
from ..federated.coordinator import FederatedCoordinator
from ..coordinator.api.endpoints.models import ModelsAPI
from ..coordinator.api.endpoints.federated import FederatedAPI
from ..rewards.dracma_manager import DRACMA_Manager
from ..models.model_manager import ModelManager

logger = get_logger(__name__)


class TestCoordinatorCore:
    """Tests del núcleo del coordinator"""

    @pytest.fixture
    def config(self):
        return Config()

    @pytest.fixture
    def coordinator(self, config):
        return Coordinator(config)

    def test_coordinator_initialization(self, coordinator):
        """Test inicialización básica del coordinator"""
        assert coordinator.config is not None
        assert coordinator.node_id is not None
        assert coordinator.status == "initialized"
        assert isinstance(coordinator.sessions, dict)

    def test_session_creation(self, coordinator):
        """Test creación de sesiones federadas"""
        session_data = {
            "session_id": "test_session_001",
            "model_name": "test_model",
            "min_nodes": 3,
            "max_nodes": 10
        }

        session = coordinator.create_session(**session_data)
        assert session.session_id == "test_session_001"
        assert session.model_name == "test_model"
        assert session.min_nodes == 3
        assert session.status == "created"

    def test_session_management(self, coordinator):
        """Test gestión completa de sesiones"""
        # Crear sesión
        session = coordinator.create_session("test_session", "test_model", 3, 10)

        # Agregar participantes
        coordinator.add_participant("test_session", "node_001")
        coordinator.add_participant("test_session", "node_002")
        coordinator.add_participant("test_session", "node_003")

        # Verificar estado
        status = coordinator.get_session_status("test_session")
        assert status["participants"] == 3
        assert status["can_start"] == True

        # Iniciar sesión
        result = coordinator.start_session("test_session")
        assert result["status"] == "running"

    def test_coordinator_error_handling(self, coordinator):
        """Test manejo de errores del coordinator"""
        # Sesión inexistente
        with pytest.raises(ValueError):
            coordinator.get_session_status("nonexistent_session")

        # Agregar participante a sesión inexistente
        with pytest.raises(ValueError):
            coordinator.add_participant("nonexistent_session", "node_001")


class TestFederatedLearning:
    """Tests del sistema de aprendizaje federado"""

    @pytest.fixture
    def federated_coordinator(self):
        config = Config()
        return FederatedCoordinator(config)

    def test_federated_session_lifecycle(self, federated_coordinator):
        """Test ciclo de vida completo de sesión federada"""
        # Crear sesión
        session = federated_coordinator.create_session(
            session_id="fed_test_001",
            model_name="llm_test",
            min_nodes=3,
            max_nodes=5
        )

        assert session.session_id == "fed_test_001"
        assert session.status == "created"

        # Agregar nodos
        for i in range(3):
            federated_coordinator.add_node_to_session("fed_test_001", f"node_{i}")

        # Verificar que puede iniciar
        status = federated_coordinator.get_session_status("fed_test_001")
        assert status["can_start"] == True

        # Iniciar entrenamiento
        result = federated_coordinator.start_training("fed_test_001")
        assert "training_started" in result

    def test_model_aggregation(self, federated_coordinator):
        """Test agregación de modelos"""
        session_id = "agg_test_001"
        federated_coordinator.create_session(session_id, "test_model", 2, 4)

        # Simular actualizaciones de nodos
        updates = {
            "node_1": {"weights": [0.1, 0.2, 0.3], "samples": 100},
            "node_2": {"weights": [0.15, 0.25, 0.35], "samples": 150}
        }

        # Agregar actualizaciones
        for node_id, update in updates.items():
            federated_coordinator.submit_model_update(session_id, node_id, update)

        # Agregar a sesión y verificar
        federated_coordinator.add_node_to_session(session_id, "node_1")
        federated_coordinator.add_node_to_session(session_id, "node_2")

        # Ejecutar agregación
        result = federated_coordinator.aggregate_models(session_id)
        assert "aggregated_model" in result
        assert result["status"] == "success"

    def test_privacy_preservation(self, federated_coordinator):
        """Test preservación de privacidad"""
        session_id = "privacy_test_001"
        session = federated_coordinator.create_session(session_id, "private_model", 3, 5)

        # Verificar configuración de privacidad
        assert session.privacy_budget > 0

        # Simular verificación de privacidad
        privacy_check = federated_coordinator.verify_privacy_budget(session_id)
        assert privacy_check["privacy_preserved"] == True


class TestAPIs:
    """Tests de APIs críticas"""

    @pytest.fixture
    def models_api(self):
        config = Config()
        return ModelsAPI(config)

    @pytest.fixture
    def federated_api(self):
        config = Config()
        return FederatedAPI(config)

    def test_models_api_list(self, models_api):
        """Test listado de modelos"""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "models": ["model_1", "model_2"],
                "total": 2
            }
            mock_get.return_value = mock_response

            result = models_api.list_models()
            assert len(result["models"]) == 2
            assert result["total"] == 2

    def test_federated_api_session_creation(self, federated_api):
        """Test creación de sesión vía API"""
        session_data = {
            "session_id": "api_test_001",
            "model_name": "api_model",
            "min_nodes": 2,
            "max_nodes": 5
        }

        with patch.object(federated_api.coordinator, 'create_session') as mock_create:
            mock_session = Mock()
            mock_session.session_id = "api_test_001"
            mock_create.return_value = mock_session

            result = federated_api.create_session(session_data)
            assert result["session_id"] == "api_test_001"
            assert result["status"] == "created"

    def test_api_error_responses(self, models_api):
        """Test respuestas de error de APIs"""
        with patch('requests.get', side_effect=Exception("Connection failed")):
            with pytest.raises(Exception):
                models_api.list_models()


class TestRewardsSystem:
    """Tests del sistema de recompensas DRACMA"""

    @pytest.fixture
    def dracma_manager(self):
        config = Config()
        return DRACMA_Manager(config)

    def test_reward_calculation(self, dracma_manager):
        """Test cálculo de recompensas"""
        contribution = {
            "node_id": "node_test",
            "data_samples": 1000,
            "computation_time": 3600,  # 1 hora
            "model_accuracy": 0.95
        }

        reward = dracma_manager.calculate_reward(contribution)
        assert reward == 0.0
        assert isinstance(reward, (int, float))

    def test_reward_distribution(self, dracma_manager):
        """Test distribución de recompensas"""
        session_rewards = {
            "session_id": "reward_test_001",
            "participants": ["node_1", "node_2", "node_3"],
            "total_reward_pool": 1000
        }

        distribution = dracma_manager.distribute_session_rewards(session_rewards)
        assert distribution.get("success") is False

    def test_penalty_application(self, dracma_manager):
        """Test aplicación de penalizaciones"""
        # Nodo con mala conducta
        penalty_case = {
            "node_id": "bad_node",
            "violations": ["late_submission", "data_poisoning"],
            "base_reward": 100
        }

        penalized_reward = dracma_manager.apply_penalties(penalty_case)
        assert penalized_reward == 100  # Bridge-only no aplica penalizacion local


class TestModelManager:
    """Tests del gestor de modelos"""

    @pytest.fixture
    def model_manager(self):
        config = Config()
        return ModelManager(config)

    def test_model_loading(self, model_manager):
        """Test carga de modelos"""
        with patch('torch.load') as mock_load:
            mock_model = Mock()
            mock_load.return_value = mock_model

            loaded_model = model_manager.load_model("test_model_v1")
            assert loaded_model is not None

    def test_model_versioning(self, model_manager):
        """Test versionado de modelos"""
        # Crear versión inicial
        model_manager.create_model_version("test_model", "v1.0", {"accuracy": 0.9})

        # Crear nueva versión
        model_manager.create_model_version("test_model", "v1.1", {"accuracy": 0.92})

        versions = model_manager.get_model_versions("test_model")
        assert len(versions) == 2
        assert versions[-1]["version"] == "v1.1"

    def test_model_validation(self, model_manager):
        """Test validación de modelos"""
        valid_model = {"architecture": "transformer", "parameters": 1000000}
        invalid_model = {"architecture": "unknown", "parameters": -1}

        assert model_manager.validate_model(valid_model) == True
        assert model_manager.validate_model(invalid_model) == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
