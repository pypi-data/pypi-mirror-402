#!/usr/bin/env python3
"""
Tests de Integración Real de APIs - AILOOS
Tests que usan las APIs reales del sistema
"""

import pytest
import os
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
import json
from datetime import datetime


class TestRealAPIIntegration:
    """Tests de integración con APIs reales"""

    @pytest.fixture
    def test_client(self):
        """Fixture para crear cliente de test de FastAPI"""
        from src.ailoos.coordinator.api.app import create_app
        app = create_app()
        return TestClient(app)

    def test_models_api_list_endpoint(self, test_client):
        """Test endpoint real de listado de modelos"""
        response = test_client.get("/api/v1/models/")

        # Verificar respuesta básica
        assert response.status_code in [200, 401, 403]  # Puede requerir auth

        if response.status_code == 200:
            data = response.json()
            assert "data" in data
            assert "total" in data
            assert isinstance(data["data"], list)

    def test_models_api_create_endpoint(self, test_client):
        """Test endpoint real de creación de modelos"""
        model_data = {
            "name": "test_model_integration",
            "model_type": "federated",
            "description": "Test model for integration testing",
            "config": {"learning_rate": 0.01}
        }

        response = test_client.post("/api/v1/models/", json=model_data)

        # Verificar respuesta (puede requerir auth o permisos)
        assert response.status_code in [200, 201, 401, 403, 422]

        if response.status_code in [200, 201]:
            data = response.json()
            assert "data" in data
            assert data["data"]["name"] == model_data["name"]

    def test_sessions_api_create_endpoint(self, test_client):
        """Test endpoint real de creación de sesiones"""
        session_data = {
            "session_id": "test_session_integration",
            "model_name": "test_model",
            "min_nodes": 3,
            "max_nodes": 10,
            "rounds": 5
        }

        response = test_client.post("/api/v1/sessions/", json=session_data)

        # Verificar respuesta
        assert response.status_code in [200, 201, 401, 403, 422]

        if response.status_code in [200, 201]:
            data = response.json()
            assert "data" in data
            assert data["data"]["session_id"] == session_data["session_id"]

    def test_wallet_api_balance_endpoint(self, test_client):
        """Test endpoint real de balance de wallet"""
        response = test_client.get("/api/v1/wallet/balance")

        # Verificar respuesta
        assert response.status_code in [200, 401, 403]

        if response.status_code == 200:
            data = response.json()
            assert "data" in data
            balance_data = data["data"]
            assert "total_balance" in balance_data
            assert "available_balance" in balance_data

    def test_rewards_api_calculate_endpoint(self, test_client):
        """Test endpoint real de cálculo de recompensas"""
        reward_data = {
            "node_id": "test_node_integration",
            "contribution_type": "data",
            "metrics": {
                "data_samples": 1000,
                "accuracy": 0.95,
                "computation_time": 3600
            }
        }

        response = test_client.post("/api/v1/rewards/calculate", json=reward_data)

        # Verificar respuesta
        assert response.status_code in [200, 401, 403, 422]

        if response.status_code == 200:
            data = response.json()
            assert "data" in data
            assert "dracma_amount" in data["data"]


class TestRealFederatedCoordinatorIntegration:
    """Tests de integración con el coordinador federado real"""

    @pytest.fixture
    def real_coordinator(self):
        """Fixture para coordinador real"""
        from src.ailoos.federated.coordinator import FederatedCoordinator
        from src.ailoos.core.config import get_config

        config = get_config()
        coordinator = FederatedCoordinator(config)
        return coordinator

    def test_real_session_creation_and_management(self, real_coordinator):
        """Test creación y gestión real de sesiones"""
        session_id = "real_integration_test_session"
        model_name = "test_model"
        min_nodes = 2
        max_nodes = 5

        # Crear sesión
        session = real_coordinator.create_session(
            session_id=session_id,
            model_name=model_name,
            min_nodes=min_nodes,
            max_nodes=max_nodes
        )

        assert session is not None
        assert session.session_id == session_id
        assert session.model_name == model_name
        assert session.min_nodes == min_nodes
        assert session.max_nodes == max_nodes

        # Verificar que está en sesiones activas
        assert session_id in real_coordinator.active_sessions

        # Obtener sesión
        retrieved_session = real_coordinator.get_session(session_id)
        assert retrieved_session.session_id == session_id

    def test_real_node_registration(self, real_coordinator):
        """Test registro real de nodos"""
        node_id = "real_test_node"

        # Registrar nodo
        result = real_coordinator.register_node(node_id)

        assert result is True
        assert node_id in real_coordinator.node_registry

        # Verificar información del nodo
        node_info = real_coordinator.node_registry[node_id]
        assert node_info["node_id"] == node_id
        assert "registered_at" in node_info
        assert node_info["status"] == "active"

    def test_real_session_node_addition(self, real_coordinator):
        """Test adición real de nodos a sesiones"""
        session_id = "real_session_nodes_test"
        node_id = "real_node_session_test"

        # Crear sesión
        session = real_coordinator.create_session(session_id, "test_model", 2, 5)
        assert session is not None

        # Registrar y agregar nodo
        real_coordinator.register_node(node_id)
        result = real_coordinator.add_node_to_session(session_id, node_id)

        assert result is True
        assert node_id in session.participants

    def test_real_model_aggregation(self, real_coordinator):
        """Test agregación real de modelos"""
        session_id = "real_aggregation_test"

        # Crear sesión y agregar nodos
        session = real_coordinator.create_session(session_id, "test_model", 2, 5)

        nodes = ["node_agg_1", "node_agg_2", "node_agg_3"]
        for node_id in nodes:
            real_coordinator.register_node(node_id)
            real_coordinator.add_node_to_session(session_id, node_id)

        # Simular actualizaciones de modelo
        updates = {}
        for node_id in nodes:
            updates[node_id] = {
                "weights": [0.1, 0.2, 0.3, 0.4, 0.5],
                "samples": 100,
                "round": 1
            }

        # Agregar actualizaciones
        for node_id, update in updates.items():
            result = real_coordinator.submit_model_update(session_id, node_id, update)
            assert result is True

        # Agregar modelos
        aggregated = real_coordinator.aggregate_models(session_id)

        assert aggregated is not None
        assert len(aggregated) == 5  # 5 parámetros

        # Verificar que es el promedio
        expected_avg = sum(0.1 + 0.2 + 0.3 + 0.4 + 0.5 for _ in nodes) / len(nodes) / 5
        assert abs(aggregated[0] - expected_avg) < 0.001


class TestRealRewardsSystemIntegration:
    """Tests de integración con el sistema real de recompensas"""

    @pytest.fixture
    def real_rewards_manager(self):
        """Fixture para manager de recompensas real"""
        if os.getenv("RUN_BRIDGE_TESTS") != "1":
            pytest.skip("Bridge tests disabled (set RUN_BRIDGE_TESTS=1).")
        from src.ailoos.rewards.dracma_manager import DRACMA_Manager
        from src.ailoos.core.config import get_config

        config = get_config()
        manager = DRACMA_Manager(config)
        return manager

    def test_real_reward_calculation(self, real_rewards_manager):
        """Test cálculo real de recompensas"""
        contributions = [
            {
                "node_id": "real_node_1",
                "type": "data",
                "metrics": {
                    "data_samples": 1000,
                    "accuracy": 0.95,
                    "computation_time": 3600
                },
                "session_id": "real_session_1"
            },
            {
                "node_id": "real_node_2",
                "type": "computation",
                "metrics": {
                    "data_samples": 500,
                    "accuracy": 0.92,
                    "computation_time": 1800
                },
                "session_id": "real_session_1"
            }
        ]

        # Calcular recompensas
        result = asyncio.run(real_rewards_manager.calculate_and_distribute_rewards(contributions))

        assert result["success"] is True
        assert result["calculations"] == 2
        assert result["transactions"] == 2
        assert result["total_dracma"] > 0

    def test_real_balance_operations(self, real_rewards_manager):
        """Test operaciones reales de balance"""
        node_id = "real_balance_test_node"

        # Obtener balance inicial
        balance = asyncio.run(real_rewards_manager.get_node_balance(node_id))

        assert "node_id" in balance
        assert "balance" in balance
        assert "total_earned" in balance

        # Verificar que es un diccionario válido
        assert isinstance(balance, dict)

    def test_real_staking_operations(self, real_rewards_manager):
        """Test operaciones reales de staking"""
        node_id = "real_staking_test_node"
        amount = 100.0
        duration_days = 30

        # Hacer stake
        stake_result = real_rewards_manager.stake_tokens(node_id, amount, duration_days)

        assert stake_result["success"] is True
        assert "stake_id" in stake_result
        assert "unlock_date" in stake_result

        # Obtener stakes
        stakes = real_rewards_manager.get_stakes(node_id)

        assert "stakes" in stakes
        assert "total_staked" in stakes
        assert stakes["total_staked"] == amount

    def test_real_delegation_operations(self, real_rewards_manager):
        """Test operaciones reales de delegación"""
        node_id = "real_delegation_test_node"
        amount = 50.0
        validator = "validator_1"
        duration_days = 60

        # Hacer delegación
        delegation_result = real_rewards_manager.delegate_tokens(node_id, amount, validator, duration_days)

        assert delegation_result["success"] is True
        assert "delegation_id" in delegation_result
        assert "apr" in delegation_result
        assert "end_date" in delegation_result

        # Obtener delegaciones
        delegations = real_rewards_manager.get_delegations(node_id)

        assert "delegations" in delegations
        assert "total_delegated" in delegations
        assert delegations["total_delegated"] == amount


class TestRealModelManagerIntegration:
    """Tests de integración con el gestor real de modelos"""

    @pytest.fixture
    def real_model_manager(self):
        """Fixture para model manager real"""
        from src.ailoos.coordinator.empoorio_lm.model_manager import ModelManager
        from src.ailoos.core.config import get_config

        config = get_config()
        manager = ModelManager(config)
        return manager

    def test_real_model_operations(self, real_model_manager):
        """Test operaciones reales de modelos"""
        model_name = "real_integration_test_model"
        model_type = "federated"
        version = "1.0.0"

        # Crear modelo
        model = real_model_manager.create_model(
            name=model_name,
            model_type=model_type,
            version=version,
            config={"learning_rate": 0.01}
        )

        assert model is not None
        assert model.name == model_name
        assert model.model_type == model_type
        assert model.version == version

        # Obtener modelo
        retrieved = real_model_manager.get_model(model.id)
        assert retrieved.id == model.id
        assert retrieved.name == model_name

        # Listar modelos
        models = real_model_manager.list_models()
        assert len(models) > 0
        assert any(m.name == model_name for m in models)

    def test_real_model_versioning(self, real_model_manager):
        """Test versionado real de modelos"""
        model_name = "real_versioning_test_model"
        model_type = "federated"

        # Crear versiones
        versions = ["1.0.0", "1.1.0", "2.0.0"]
        created_models = []

        for version in versions:
            model = real_model_manager.create_model(
                name=model_name,
                model_type=model_type,
                version=version
            )
            created_models.append(model)

        # Obtener versiones
        model_versions = real_model_manager.get_model_versions(model_name, model_type)

        assert len(model_versions) == len(versions)
        version_strings = [m.version for m in model_versions]
        assert all(v in version_strings for v in versions)

        # Obtener versión más reciente
        latest = real_model_manager.get_latest_model_version(model_name, model_type)
        assert latest.version == "2.0.0"


class TestRealValidationIntegration:
    """Tests de integración con el sistema real de validación"""

    @pytest.fixture
    def real_validator(self):
        """Fixture para validador real"""
        from src.ailoos.validation.validator import EmpoorioLMValidator
        from src.ailoos.core.config import get_config

        config = get_config()
        validator = EmpoorioLMValidator(config)
        return validator

    def test_real_model_validation(self, real_validator):
        """Test validación real de modelos"""
        # Modelo válido
        valid_model = {
            "name": "valid_test_model",
            "type": "federated",
            "config": {
                "learning_rate": 0.01,
                "batch_size": 32,
                "epochs": 10
            },
            "metrics": {
                "accuracy": 0.95,
                "loss": 0.05
            }
        }

        result = real_validator.validate_model(valid_model)
        assert result.is_valid is True
        assert len(result.errors) == 0

        # Modelo inválido
        invalid_model = {
            "name": "",  # Nombre vacío
            "type": "invalid_type",
            "config": {},
            "metrics": {}
        }

        result = real_validator.validate_model(invalid_model)
        assert result.is_valid is False
        assert len(result.errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
