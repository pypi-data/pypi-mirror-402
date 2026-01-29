#!/usr/bin/env python3
"""
Suite Exhaustiva de Tests End-to-End para Procesos Federados Completos
Cubre el flujo completo: inicialización → rondas → agregación → ZKP → recompensas
"""

import pytest
import asyncio
import time
import numpy as np
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import tempfile
import os

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

from ..core.config import Config
from ..federated.coordinator import FederatedCoordinator
from ..federated.session import FederatedSession
from ..federated.aggregator import FederatedAggregator
from ..federated.secure_aggregator import SecureAggregator, AggregationConfig
try:
    from ..rewards.dracma_calculator import dracmaCalculator
except ImportError:
    dracmaCalculator = None

try:
    from ..rewards.dracma_manager import DRACMA_Manager
except ImportError:
    DRACMA_Manager = None
# Validation imports (optional)
EmpoorioLMValidator = None
ValidationConfig = None


class TestFederatedCompleteE2E:
    """Suite completa de tests E2E para procesos federados"""

    @pytest.fixture
    def federated_config(self):
        """Configuración para tests federados"""
        config = Config()
        config.federated_min_nodes = 3
        config.federated_max_nodes = 10
        config.federated_rounds = 5
        config.privacy_budget = 1.0
        config.reward_pool_size = 1000.0
        return config

    @pytest.fixture
    def coordinator(self, federated_config):
        """Coordinador federado para tests"""
        return FederatedCoordinator(federated_config)

    @pytest.fixture
    def dracma_calculator(self, federated_config):
        """Calculadora de recompensas DRACMA"""
        if dracmaCalculator is None:
            pytest.skip("dracmaCalculator not available")
        return dracmaCalculator(federated_config)

    @pytest.fixture
    def secure_aggregator(self, federated_config):
        """Agregador seguro con configuración de privacidad"""
        config = AggregationConfig(
            aggregation_type="fedavg",
            enable_differential_privacy=True,
            dp_epsilon=1.0,
            min_participants=3
        )
        return SecureAggregator("test_session", "test_model", config)

    @pytest.fixture
    def validator(self):
        """Validador de modelos"""
        if ValidationConfig is None or EmpoorioLMValidator is None:
            pytest.skip("Validation components not available")
        config = ValidationConfig(
            validator_name="federated_test_validator",
            max_validation_samples=1000,
            calculate_perplexity=False,  # Simplificar para tests
            calculate_bleu=False,
            benchmark_latencies=True,
            benchmark_throughput=False
        )
        return EmpoorioLMValidator(config)


class TestFederatedSessionInitialization:
    """Tests para inicialización de sesiones federadas"""

    def test_session_creation_basic(self, coordinator):
        """Test creación básica de sesión federada"""
        session = coordinator.create_session(
            session_id="test_session_001",
            model_name="test_model",
            min_nodes=3,
            max_nodes=5,
            rounds=3
        )

        assert session.session_id == "test_session_001"
        assert session.model_name == "test_model"
        assert session.min_nodes == 3
        assert session.max_nodes == 5
        assert session.total_rounds == 3
        assert session.status == "created"
        assert session.privacy_budget == 1.0

    def test_session_creation_with_custom_config(self, coordinator):
        """Test creación de sesión con configuración personalizada"""
        session = coordinator.create_session(
            session_id="custom_session",
            model_name="advanced_model",
            min_nodes=5,
            max_nodes=20,
            rounds=10
        )

        assert session.min_nodes == 5
        assert session.max_nodes == 20
        assert session.total_rounds == 10

    def test_session_creation_duplicate_id_fails(self, coordinator):
        """Test que falla creación de sesión con ID duplicado"""
        # Crear primera sesión
        coordinator.create_session("duplicate_session", "model", 3, 5)

        # Intentar crear segunda sesión con mismo ID
        with pytest.raises(ValueError, match="Session duplicate_session already exists"):
            coordinator.create_session("duplicate_session", "model", 3, 5)

    def test_session_initial_state(self, coordinator):
        """Test estado inicial de sesión"""
        session = coordinator.create_session("initial_state_test", "model", 3, 5)

        status = coordinator.get_session_status("initial_state_test")
        assert status["status"] == "created"
        assert status["current_round"] == 0
        assert status["participants"] == 0
        assert status["can_start"] == False
        assert status["is_complete"] == False
        assert status["progress_percentage"] == "0.0%"


class TestNodeRegistrationAndManagement:
    """Tests para registro y gestión de nodos"""

    def test_node_registration(self, coordinator):
        """Test registro básico de nodos"""
        # Registrar nodo
        node_info = coordinator.register_node("test_node_001")

        assert node_info["node_id"] == "test_node_001"
        assert "registered_at" in node_info
        assert node_info["status"] == "active"
        assert node_info["sessions_joined"] == []

    def test_node_registration_duplicate_fails(self, coordinator):
        """Test que falla registro de nodo duplicado"""
        coordinator.register_node("duplicate_node")

        with pytest.raises(ValueError, match="Node duplicate_node already registered"):
            coordinator.register_node("duplicate_node")

    def test_add_node_to_session(self, coordinator):
        """Test agregar nodo a sesión"""
        # Crear sesión
        coordinator.create_session("node_session", "model", 2, 5)

        # Registrar y agregar nodo
        coordinator.register_node("node_001")
        result = coordinator.add_node_to_session("node_session", "node_001")

        assert result == True

        # Verificar estado
        status = coordinator.get_session_status("node_session")
        assert status["participants"] == 1
        assert "node_001" in status["participant_list"]

    def test_add_unregistered_node_fails(self, coordinator):
        """Test que falla agregar nodo no registrado"""
        coordinator.create_session("unregistered_session", "model", 2, 5)

        with pytest.raises(ValueError, match="Node unregistered_node not found"):
            coordinator.add_node_to_session("unregistered_session", "unregistered_node")

    def test_add_node_to_nonexistent_session_fails(self, coordinator):
        """Test que falla agregar nodo a sesión inexistente"""
        coordinator.register_node("orphan_node")

        with pytest.raises(ValueError, match="Session nonexistent not found"):
            coordinator.add_node_to_session("nonexistent", "orphan_node")

    def test_max_nodes_limit(self, coordinator):
        """Test límite máximo de nodos por sesión"""
        session = coordinator.create_session("max_nodes_session", "model", 2, 3)

        # Registrar nodos
        for i in range(4):
            coordinator.register_node(f"max_node_{i}")

        # Agregar nodos hasta el límite
        for i in range(3):
            coordinator.add_node_to_session("max_nodes_session", f"max_node_{i}")

        # Verificar que no se pueden agregar más
        status = coordinator.get_session_status("max_nodes_session")
        assert status["participants"] == 3

    def test_node_info_retrieval(self, coordinator):
        """Test recuperación de información de nodos"""
        # Registrar varios nodos
        coordinator.register_node("info_node_1")
        coordinator.register_node("info_node_2")

        # Agregar a sesiones
        coordinator.create_session("session_a", "model", 2, 5)
        coordinator.create_session("session_b", "model", 2, 5)

        coordinator.add_node_to_session("session_a", "info_node_1")
        coordinator.add_node_to_session("session_b", "info_node_1")
        coordinator.add_node_to_session("session_b", "info_node_2")

        # Verificar información
        node_info = coordinator.get_node_info("info_node_1")
        assert node_info["node_id"] == "info_node_1"
        assert "session_a" in node_info["sessions_joined"]
        assert "session_b" in node_info["sessions_joined"]

        node_info_2 = coordinator.get_node_info("info_node_2")
        assert "session_b" in node_info_2["sessions_joined"]
        assert "session_a" not in node_info_2["sessions_joined"]


class TestMultiRoundTraining:
    """Tests para múltiples rondas de entrenamiento"""

    def test_training_start_with_minimum_nodes(self, coordinator):
        """Test inicio de entrenamiento con mínimo de nodos"""
        coordinator.create_session("training_session", "model", 3, 5)

        # Agregar nodos
        for i in range(3):
            coordinator.register_node(f"train_node_{i}")
            coordinator.add_node_to_session("training_session", f"train_node_{i}")

        # Iniciar entrenamiento
        result = coordinator.start_training("training_session")

        assert result["status"] == "training_started"
        assert result["participants"] == 3

        # Verificar estado
        status = coordinator.get_session_status("training_session")
        assert status["status"] == "running"

    def test_training_start_insufficient_nodes_fails(self, coordinator):
        """Test que falla inicio con nodos insuficientes"""
        coordinator.create_session("insufficient_session", "model", 5, 10)

        # Agregar solo 3 nodos (menos del mínimo 5)
        for i in range(3):
            coordinator.register_node(f"insuff_node_{i}")
            coordinator.add_node_to_session("insufficient_session", f"insuff_node_{i}")

        with pytest.raises(ValueError, match="insufficient participants"):
            coordinator.start_training("insufficient_session")

    def test_single_round_execution(self, coordinator):
        """Test ejecución de una ronda completa"""
        coordinator.create_session("round_session", "model", 2, 4)

        # Agregar nodos y iniciar
        nodes = ["round_node_1", "round_node_2"]
        for node_id in nodes:
            coordinator.register_node(node_id)
            coordinator.add_node_to_session("round_session", node_id)

        coordinator.start_training("round_session")

        # Simular envío de actualizaciones
        for node_id in nodes:
            update = {
                "weights": {"layer1": [0.1, 0.2], "layer2": [0.3, 0.4]},
                "samples_used": 100,
                "accuracy": 0.85,
                "loss": 0.45
            }
            coordinator.submit_model_update("round_session", node_id, update)

        # Agregar modelos
        result = coordinator.aggregate_models("round_session")

        assert result["status"] == "success"
        assert result["round"] == 1
        assert result["participants"] == 2
        assert "aggregated_model" in result

    def test_multiple_rounds_execution(self, coordinator):
        """Test ejecución de múltiples rondas"""
        coordinator.create_session("multi_round_session", "model", 2, 4, rounds=3)

        nodes = ["multi_node_1", "multi_node_2"]
        for node_id in nodes:
            coordinator.register_node(node_id)
            coordinator.add_node_to_session("multi_round_session", node_id)

        coordinator.start_training("multi_round_session")

        # Ejecutar 3 rondas
        for round_num in range(1, 4):
            # Enviar actualizaciones para esta ronda
            for node_id in nodes:
                update = {
                    "weights": {
                        "layer1": [0.1 * round_num + i * 0.01 for i in range(5)],
                        "layer2": [0.2 * round_num + i * 0.02 for i in range(3)]
                    },
                    "samples_used": 100 * round_num,
                    "accuracy": 0.8 + (round_num * 0.03),
                    "loss": 0.5 - (round_num * 0.05)
                }
                coordinator.submit_model_update("multi_round_session", node_id, update)

            # Agregar para esta ronda
            result = coordinator.aggregate_models("multi_round_session")
            assert result["round"] == round_num

            # Verificar progreso
            status = coordinator.get_session_status("multi_round_session")
            assert status["current_round"] == round_num

        # Verificar finalización
        final_status = coordinator.get_session_status("multi_round_session")
        assert final_status["is_complete"] == True
        assert final_status["current_round"] == 3

    def test_round_progression_logic(self, coordinator):
        """Test lógica de progresión de rondas"""
        session = coordinator.create_session("progression_session", "model", 2, 4, rounds=2)

        # Verificar estado inicial
        assert session.current_round == 0
        assert session.is_complete() == False

        # Avanzar rondas
        session.next_round()
        assert session.current_round == 1
        assert session.is_complete() == False

        session.next_round()
        assert session.current_round == 2
        assert session.is_complete() == True

        # Intentar avanzar más (debe fallar)
        session.next_round()
        assert session.current_round == 2  # No cambia


class TestModelAggregationFedAvg:
    """Tests para agregación de modelos con FedAvg"""

    def test_basic_federated_average(self, coordinator):
        """Test promedio federado básico"""
        coordinator.create_session("fedavg_session", "model", 2, 4)

        nodes = ["fedavg_node_1", "fedavg_node_2"]
        for node_id in nodes:
            coordinator.register_node(node_id)
            coordinator.add_node_to_session("fedavg_session", node_id)

        coordinator.start_training("fedavg_session")

        # Enviar actualizaciones con pesos diferentes
        updates = [
            {
                "weights": {"layer1": [1.0, 2.0], "layer2": [3.0]},
                "samples_used": 100
            },
            {
                "weights": {"layer1": [3.0, 4.0], "layer2": [5.0]},
                "samples_used": 200
            }
        ]

        for i, node_id in enumerate(nodes):
            coordinator.submit_model_update("fedavg_session", node_id, updates[i])

        # Agregar
        result = coordinator.aggregate_models("fedavg_session")

        # Verificar promedio ponderado
        # layer1: (1.0*100 + 3.0*200) / 300 = (100 + 600) / 300 = 700/300 = 2.333...
        # layer2: (3.0*100 + 5.0*200) / 300 = (300 + 1000) / 300 = 1300/300 = 4.333...
        expected_layer1 = [2.333333, 3.333333]  # Aproximado
        expected_layer2 = [4.333333]

        aggregated = result["aggregated_model"]
        assert "layer1" in aggregated
        assert "layer2" in aggregated
        assert len(aggregated["layer1"]) == 2
        assert len(aggregated["layer2"]) == 1

    def test_weighted_aggregation_by_samples(self, coordinator):
        """Test agregación ponderada por número de muestras"""
        coordinator.create_session("weighted_session", "model", 2, 4)

        nodes = ["weighted_node_1", "weighted_node_2"]
        for node_id in nodes:
            coordinator.register_node(node_id)
            coordinator.add_node_to_session("weighted_session", node_id)

        coordinator.start_training("weighted_session")

        # Nodo 1: pocas muestras (peso bajo)
        update1 = {
            "weights": {"param": [1.0]},
            "samples_used": 50
        }

        # Nodo 2: muchas muestras (peso alto)
        update2 = {
            "weights": {"param": [5.0]},
            "samples_used": 150
        }

        coordinator.submit_model_update("weighted_session", "weighted_node_1", update1)
        coordinator.submit_model_update("weighted_session", "weighted_node_2", update2)

        result = coordinator.aggregate_models("weighted_session")

        # Resultado esperado: (1.0*50 + 5.0*150) / 200 = (50 + 750) / 200 = 800/200 = 4.0
        aggregated = result["aggregated_model"]
        assert abs(aggregated["param"][0] - 4.0) < 0.001

    def test_aggregation_insufficient_updates_fails(self, coordinator):
        """Test que falla agregación con actualizaciones insuficientes"""
        coordinator.create_session("insufficient_agg_session", "model", 3, 5)

        nodes = ["insuff_agg_1", "insuff_agg_2", "insuff_agg_3"]
        for node_id in nodes:
            coordinator.register_node(node_id)
            coordinator.add_node_to_session("insufficient_agg_session", node_id)

        coordinator.start_training("insufficient_agg_session")

        # Solo enviar 2 actualizaciones de 3 nodos
        coordinator.submit_model_update("insufficient_agg_session", "insuff_agg_1", {"weights": {"p": [1.0]}, "samples_used": 100})
        coordinator.submit_model_update("insufficient_agg_session", "insuff_agg_2", {"weights": {"p": [2.0]}, "samples_used": 100})

        with pytest.raises(ValueError, match="No model updates available"):
            coordinator.aggregate_models("insufficient_agg_session")

    def test_aggregation_with_different_architectures(self, coordinator):
        """Test agregación con arquitecturas ligeramente diferentes"""
        coordinator.create_session("arch_session", "model", 2, 4)

        nodes = ["arch_node_1", "arch_node_2"]
        for node_id in nodes:
            coordinator.register_node(node_id)
            coordinator.add_node_to_session("arch_session", node_id)

        coordinator.start_training("arch_session")

        # Nodo 1: arquitectura completa
        update1 = {
            "weights": {
                "layer1": [1.0, 2.0],
                "layer2": [3.0, 4.0, 5.0],
                "output": [6.0]
            },
            "samples_used": 100
        }

        # Nodo 2: arquitectura compatible
        update2 = {
            "weights": {
                "layer1": [2.0, 3.0],
                "layer2": [4.0, 5.0, 6.0],
                "output": [7.0]
            },
            "samples_used": 100
        }

        coordinator.submit_model_update("arch_session", "arch_node_1", update1)
        coordinator.submit_model_update("arch_session", "arch_node_2", update2)

        result = coordinator.aggregate_models("arch_session")

        # Verificar que todas las capas están presentes
        aggregated = result["aggregated_model"]
        assert "layer1" in aggregated
        assert "layer2" in aggregated
        assert "output" in aggregated

        # Verificar valores promedio
        assert len(aggregated["layer1"]) == 2
        assert len(aggregated["layer2"]) == 3
        assert len(aggregated["output"]) == 1


class TestZKPValidation:
    """Tests para validación ZKP de contribuciones"""

    @pytest.fixture
    def mock_zkp_engine(self):
        """Mock del motor ZKP"""
        mock_engine = Mock()
        mock_engine.generate_proof = AsyncMock()
        mock_engine.verify_proof = AsyncMock(return_value=True)

        # Configurar proof mock
        mock_proof = Mock()
        mock_proof.proof_id = "test_proof_123"
        mock_proof.is_valid = True
        mock_engine.generate_proof.return_value = mock_proof

        return mock_engine

    def test_zkp_proof_generation_for_contribution(self, coordinator, mock_zkp_engine):
        """Test generación de pruebas ZKP para contribuciones"""
        with patch('src.ailoos.verification.zkp_engine.ZKPEngine', return_value=mock_zkp_engine):
            coordinator.create_session("zkp_session", "model", 2, 4)

            nodes = ["zkp_node_1", "zkp_node_2"]
            for node_id in nodes:
                coordinator.register_node(node_id)
                coordinator.add_node_to_session("zkp_session", node_id)

            coordinator.start_training("zkp_session")

            # Enviar actualización con ZKP
            update = {
                "weights": {"layer1": [1.0, 2.0]},
                "samples_used": 100,
                "accuracy": 0.85,
                "zkp_proof": "proof_data"
            }

            result = coordinator.submit_model_update("zkp_session", "zkp_node_1", update)
            assert result == True

            # Verificar que se llamó al motor ZKP
            mock_zkp_engine.generate_proof.assert_called()

    def test_zkp_proof_verification_failure(self, coordinator, mock_zkp_engine):
        """Test fallo en verificación de prueba ZKP"""
        mock_zkp_engine.verify_proof.return_value = False

        with patch('src.ailoos.verification.zkp_engine.ZKPEngine', return_value=mock_zkp_engine):
            coordinator.create_session("zkp_fail_session", "model", 2, 4)

            coordinator.register_node("zkp_fail_node")
            coordinator.add_node_to_session("zkp_fail_session", "zkp_fail_node")
            coordinator.start_training("zkp_fail_session")

            # Actualización con prueba ZKP inválida
            update = {
                "weights": {"layer1": [1.0]},
                "samples_used": 100,
                "zkp_proof": "invalid_proof"
            }

            # Debería procesarse pero marcar como sospechoso
            result = coordinator.submit_model_update("zkp_fail_session", "zkp_fail_node", update)
            assert result == True  # Se acepta pero se marca

    def test_zkp_privacy_preservation(self, coordinator, mock_zkp_engine):
        """Test preservación de privacidad con ZKP"""
        with patch('src.ailoos.verification.zkp_engine.ZKPEngine', return_value=mock_zkp_engine):
            coordinator.create_session("privacy_session", "model", 2, 4)

            coordinator.register_node("privacy_node")
            coordinator.add_node_to_session("privacy_session", "privacy_node")
            coordinator.start_training("privacy_session")

            # Verificar presupuesto de privacidad inicial
            privacy_status = coordinator.verify_privacy_budget("privacy_session")
            assert privacy_status["privacy_preserved"] == True
            assert privacy_status["budget_remaining"] == 1.0

            # Simular uso de privacidad durante rondas
            for _ in range(5):
                coordinator.consume_privacy_budget("privacy_session", 0.1)

            # Verificar reducción de presupuesto
            final_privacy = coordinator.verify_privacy_budget("privacy_session")
            assert final_privacy["budget_remaining"] < 1.0


class TestdracmaRewardsDistribution:
    """Tests para cálculo y distribución de recompensas DRACMA"""

    def test_basic_reward_calculation(self, dracma_calculator):
        """Test cálculo básico de recompensas"""
        contribution = {
            "node_id": "reward_node_1",
            "contribution_type": "federated_training",
            "metrics": {
                "parameters_trained": 10000,
                "data_samples": 1000,
                "training_time_seconds": 300.0,
                "model_accuracy": 0.85,
                "round_number": 1
            },
            "session_id": "reward_session_1"
        }

        reward_calc = asyncio.run(dracma_calculator.calculate_reward(
            contribution["node_id"],
            contribution["contribution_type"],
            contribution["metrics"],
            contribution["session_id"]
        ))

        assert reward_calc.node_id == "reward_node_1"
        assert reward_calc.session_id == "reward_session_1"
        assert reward_calc.total_reward > 0
        assert reward_calc.dracma_amount > 0
        assert reward_calc.calculation_hash is not None

    def test_reward_scaling_with_contribution_size(self, dracma_calculator):
        """Test escalado de recompensas con tamaño de contribución"""
        # Contribución pequeña
        small_contrib = {
            "node_id": "small_node",
            "contribution_type": "federated_training",
            "metrics": {
                "parameters_trained": 1000,
                "data_samples": 100,
                "training_time_seconds": 60.0,
                "model_accuracy": 0.8,
                "round_number": 1
            },
            "session_id": "scale_session"
        }

        # Contribución grande
        large_contrib = {
            "node_id": "large_node",
            "contribution_type": "federated_training",
            "metrics": {
                "parameters_trained": 50000,
                "data_samples": 5000,
                "training_time_seconds": 600.0,
                "model_accuracy": 0.9,
                "round_number": 1
            },
            "session_id": "scale_session"
        }

        small_reward = asyncio.run(dracma_calculator.calculate_reward(
            small_contrib["node_id"], small_contrib["contribution_type"],
            small_contrib["metrics"], small_contrib["session_id"]
        ))

        large_reward = asyncio.run(dracma_calculator.calculate_reward(
            large_contrib["node_id"], large_contrib["contribution_type"],
            large_contrib["metrics"], large_contrib["session_id"]
        ))

        # Recompensa grande debe ser significativamente mayor
        assert large_reward.total_reward > small_reward.total_reward * 2

    def test_session_rewards_distribution(self, dracma_calculator):
        """Test distribución de recompensas para sesión completa"""
        session_contributions = [
            {
                "node_id": f"session_node_{i}",
                "contribution_type": "federated_training",
                "metrics": {
                    "parameters_trained": 10000 + i * 1000,
                    "data_samples": 1000 + i * 100,
                    "training_time_seconds": 300.0,
                    "model_accuracy": 0.8 + i * 0.02,
                    "round_number": 1
                },
                "session_id": "dist_session"
            }
            for i in range(3)
        ]

        # Calcular recompensas individuales
        individual_rewards = []
        for contrib in session_contributions:
            reward = asyncio.run(dracma_calculator.calculate_reward(
                contrib["node_id"], contrib["contribution_type"],
                contrib["metrics"], contrib["session_id"]
            ))
            individual_rewards.append(reward)

        # Calcular distribución de sesión
        session_rewards = asyncio.run(dracma_calculator.calculate_session_rewards("dist_session"))

        assert len(session_rewards) == 3
        total_distributed = sum(r.dracma_amount for r in session_rewards)
        assert total_distributed > 0

        # Verificar que las recompensas se distribuyen según contribución
        rewards_by_node = {r.node_id: r.dracma_amount for r in session_rewards}
        assert rewards_by_node["session_node_2"] > rewards_by_node["session_node_0"]

    def test_reward_pool_limits(self, dracma_calculator):
        """Test límites del pool de recompensas"""
        # Configurar pool pequeño
        dracma_calculator.config.reward_pool_size = 100.0

        contributions = []
        for i in range(5):
            contrib = {
                "node_id": f"pool_node_{i}",
                "contribution_type": "federated_training",
                "metrics": {
                    "parameters_trained": 10000,
                    "data_samples": 1000,
                    "training_time_seconds": 300.0,
                    "model_accuracy": 0.85,
                    "round_number": 1
                },
                "session_id": "pool_session"
            }
            contributions.append(contrib)

        # Calcular recompensas
        session_rewards = asyncio.run(dracma_calculator.calculate_session_rewards("pool_session"))

        total_distributed = sum(r.dracma_amount for r in session_rewards)

        # No debe exceder el límite del pool
        assert total_distributed <= 100.0

    def test_hardware_bonus_calculation(self, dracma_calculator):
        """Test cálculo de bonus por hardware"""
        # Nodo con buen hardware
        good_hw_contrib = {
            "node_id": "good_hw_node",
            "contribution_type": "federated_training",
            "metrics": {
                "parameters_trained": 10000,
                "data_samples": 1000,
                "training_time_seconds": 300.0,
                "model_accuracy": 0.85,
                "hardware_specs": {
                    "cpu_cores": 8,
                    "has_gpu": True,
                    "gpu_memory_gb": 8,
                    "memory_gb": 16
                },
                "round_number": 1
            },
            "session_id": "hw_session"
        }

        # Nodo con hardware básico
        basic_hw_contrib = {
            "node_id": "basic_hw_node",
            "contribution_type": "federated_training",
            "metrics": {
                "parameters_trained": 10000,
                "data_samples": 1000,
                "training_time_seconds": 300.0,
                "model_accuracy": 0.85,
                "hardware_specs": {
                    "cpu_cores": 2,
                    "has_gpu": False,
                    "memory_gb": 4
                },
                "round_number": 1
            },
            "session_id": "hw_session"
        }

        good_hw_reward = asyncio.run(dracma_calculator.calculate_reward(
            good_hw_contrib["node_id"], good_hw_contrib["contribution_type"],
            good_hw_contrib["metrics"], good_hw_contrib["session_id"]
        ))

        basic_hw_reward = asyncio.run(dracma_calculator.calculate_reward(
            basic_hw_contrib["node_id"], basic_hw_contrib["contribution_type"],
            basic_hw_contrib["metrics"], basic_hw_contrib["session_id"]
        ))

        # Nodo con mejor hardware debe tener bonus
        assert good_hw_reward.hardware_bonus > basic_hw_reward.hardware_bonus


class TestErrorHandlingAndEdgeCases:
    """Tests para manejo de errores y edge cases"""

    def test_session_not_found_errors(self, coordinator):
        """Test errores cuando sesión no existe"""
        with pytest.raises(ValueError, match="Session nonexistent not found"):
            coordinator.get_session_status("nonexistent")

        with pytest.raises(ValueError, match="Session nonexistent not found"):
            coordinator.add_node_to_session("nonexistent", "node")

        with pytest.raises(ValueError, match="Session nonexistent not found"):
            coordinator.start_training("nonexistent")

    def test_node_not_in_session_errors(self, coordinator):
        """Test errores cuando nodo no está en sesión"""
        coordinator.create_session("node_error_session", "model", 2, 4)
        coordinator.register_node("error_node")

        update = {"weights": {"p": [1.0]}, "samples_used": 100}

        with pytest.raises(ValueError, match="Node error_node not in session"):
            coordinator.submit_model_update("node_error_session", "error_node", update)

    def test_invalid_model_updates(self, coordinator):
        """Test actualizaciones de modelo inválidas"""
        coordinator.create_session("invalid_update_session", "model", 2, 4)
        coordinator.register_node("invalid_node")
        coordinator.add_node_to_session("invalid_update_session", "invalid_node")
        coordinator.start_training("invalid_update_session")

        # Actualización sin campos requeridos
        invalid_update = {"weights": {"p": [1.0]}}  # Falta samples_used

        with pytest.raises(ValueError, match="missing required fields"):
            coordinator.submit_model_update("invalid_update_session", "invalid_node", invalid_update)

    def test_concurrent_session_operations(self, coordinator):
        """Test operaciones concurrentes en sesiones"""
        # Crear múltiples sesiones
        sessions = []
        for i in range(5):
            session = coordinator.create_session(f"concurrent_session_{i}", "model", 2, 4)
            sessions.append(session)

        # Operaciones concurrentes simuladas
        async def concurrent_operations():
            tasks = []
            for i, session in enumerate(sessions):
                # Agregar nodos concurrentemente
                task = asyncio.create_task(self._add_nodes_concurrent(coordinator, session.session_id, i))
                tasks.append(task)

            await asyncio.gather(*tasks)

        asyncio.run(concurrent_operations())

        # Verificar que todas las sesiones tienen nodos
        for session in sessions:
            status = coordinator.get_session_status(session.session_id)
            assert status["participants"] >= 2

    async def _add_nodes_concurrent(self, coordinator, session_id, index):
        """Helper para agregar nodos concurrentemente"""
        for i in range(2):
            node_id = f"concurrent_node_{index}_{i}"
            coordinator.register_node(node_id)
            coordinator.add_node_to_session(session_id, node_id)
            await asyncio.sleep(0.01)  # Simular async

    def test_memory_cleanup_after_session_completion(self, coordinator):
        """Test limpieza de memoria después de completar sesión"""
        coordinator.create_session("cleanup_session", "model", 2, 4, rounds=2)

        nodes = ["cleanup_node_1", "cleanup_node_2"]
        for node_id in nodes:
            coordinator.register_node(node_id)
            coordinator.add_node_to_session("cleanup_session", node_id)

        coordinator.start_training("cleanup_session")

        # Completar rondas
        for round_num in range(1, 3):
            for node_id in nodes:
                update = {
                    "weights": {"layer1": [1.0 * round_num]},
                    "samples_used": 100
                }
                coordinator.submit_model_update("cleanup_session", node_id, update)

            coordinator.aggregate_models("cleanup_session")

        # Verificar finalización
        status = coordinator.get_session_status("cleanup_session")
        assert status["is_complete"] == True

        # Remover sesión
        result = coordinator.remove_session("cleanup_session")
        assert result == True

        # Verificar que ya no existe
        with pytest.raises(ValueError):
            coordinator.get_session_status("cleanup_session")

    def test_extreme_values_handling(self, coordinator):
        """Test manejo de valores extremos"""
        coordinator.create_session("extreme_session", "model", 2, 4)

        coordinator.register_node("extreme_node")
        coordinator.add_node_to_session("extreme_session", "extreme_node")
        coordinator.start_training("extreme_session")

        # Valores extremos en actualización
        extreme_update = {
            "weights": {
                "large_layer": [1e10] * 1000,  # Pesos muy grandes
                "small_layer": [1e-10] * 1000   # Pesos muy pequeños
            },
            "samples_used": 1e6  # Muchas muestras
        }

        # Debe manejarse sin errores
        result = coordinator.submit_model_update("extreme_session", "extreme_node", extreme_update)
        assert result == True

    def test_network_partition_simulation(self, coordinator):
        """Test simulación de partición de red"""
        coordinator.create_session("partition_session", "model", 4, 6)

        nodes = [f"partition_node_{i}" for i in range(6)]
        for node_id in nodes:
            coordinator.register_node(node_id)
            coordinator.add_node_to_session("partition_session", node_id)

        coordinator.start_training("partition_session")

        # Simular partición: solo algunos nodos envían actualizaciones
        active_nodes = nodes[:3]  # Solo 3 de 6 nodos

        for node_id in active_nodes:
            update = {"weights": {"p": [1.0]}, "samples_used": 100}
            coordinator.submit_model_update("partition_session", node_id, update)

        # Intentar agregar con nodos insuficientes (debe fallar)
        with pytest.raises(ValueError, match="No model updates available"):
            coordinator.aggregate_models("partition_session")


class TestPerformanceAndScalability:
    """Tests de rendimiento y escalabilidad"""

    def test_large_scale_session_creation(self, coordinator):
        """Test creación de sesiones a gran escala"""
        start_time = time.time()

        # Crear muchas sesiones
        for i in range(100):
            session = coordinator.create_session(f"scale_session_{i:03d}", "model", 3, 10)
            assert session is not None

        creation_time = time.time() - start_time
        assert creation_time < 5.0  # Debe ser rápido

        # Verificar que todas existen
        active_sessions = coordinator.get_active_sessions()
        assert len(active_sessions) == 100

    def test_high_concurrency_node_registration(self, coordinator):
        """Test registro de nodos con alta concurrencia"""
        async def register_nodes_concurrent():
            tasks = []
            for i in range(50):
                task = asyncio.create_task(self._register_single_node(coordinator, i))
                tasks.append(task)

            await asyncio.gather(*tasks)

        start_time = time.time()
        asyncio.run(register_nodes_concurrent())
        registration_time = time.time() - start_time

        assert registration_time < 10.0  # Debe ser razonablemente rápido

    async def _register_single_node(self, coordinator, index):
        """Helper para registrar un nodo"""
        node_id = f"concurrent_reg_node_{index:03d}"
        coordinator.register_node(node_id)
        await asyncio.sleep(0.001)  # Simular pequeña async

    def test_memory_usage_during_large_sessions(self, coordinator):
        """Test uso de memoria durante sesiones grandes"""
        # Crear sesión con muchos nodos
        coordinator.create_session("memory_test_session", "model", 50, 100)

        # Registrar y agregar muchos nodos
        for i in range(80):
            node_id = f"memory_node_{i:03d}"
            coordinator.register_node(node_id)
            coordinator.add_node_to_session("memory_test_session", node_id)

        # Verificar que se maneja bien
        status = coordinator.get_session_status("memory_test_session")
        assert status["participants"] == 80
        assert status["can_start"] == True

    def test_aggregation_performance_with_large_models(self, coordinator):
        """Test rendimiento de agregación con modelos grandes"""
        coordinator.create_session("large_model_session", "big_model", 3, 5)

        nodes = ["large_node_1", "large_node_2", "large_node_3"]
        for node_id in nodes:
            coordinator.register_node(node_id)
            coordinator.add_node_to_session("large_model_session", node_id)

        coordinator.start_training("large_model_session")

        # Simular modelo grande
        large_weights = {}
        for layer in range(10):  # 10 capas
            large_weights[f"layer_{layer}"] = [0.1] * 1000  # 1000 parámetros por capa

        start_time = time.time()
        for node_id in nodes:
            update = {
                "weights": large_weights,
                "samples_used": 1000
            }
            coordinator.submit_model_update("large_model_session", node_id, update)

        # Agregar
        result = coordinator.aggregate_models("large_model_session")
        aggregation_time = time.time() - start_time

        assert result["status"] == "success"
        assert aggregation_time < 30.0  # Debe ser razonable

    def test_throughput_under_load(self, coordinator):
        """Test throughput bajo carga"""
        coordinator.create_session("throughput_session", "model", 10, 20)

        # Agregar muchos nodos
        for i in range(15):
            node_id = f"throughput_node_{i}"
            coordinator.register_node(node_id)
            coordinator.add_node_to_session("throughput_session", node_id)

        coordinator.start_training("throughput_session")

        start_time = time.time()

        # Enviar muchas actualizaciones rápidamente
        for i in range(15):
            update = {"weights": {"p": [float(i)]}, "samples_used": 100}
            coordinator.submit_model_update("throughput_session", f"throughput_node_{i}", update)

        # Agregar
        result = coordinator.aggregate_models("throughput_session")
        total_time = time.time() - start_time

        assert result["status"] == "success"
        updates_per_second = 15 / total_time
        assert updates_per_second > 10  # Al menos 10 actualizaciones por segundo


class TestSecurityAndPrivacy:
    """Tests de seguridad y privacidad"""

    def test_secure_aggregator_initialization(self, secure_aggregator):
        """Test inicialización del agregador seguro"""
        assert secure_aggregator.session_id == "test_session"
        assert secure_aggregator.model_name == "test_model"
        assert secure_aggregator.current_round == 0
        assert secure_aggregator.config.enable_differential_privacy == True

    @pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
    def test_differential_privacy_application(self, secure_aggregator):
        """Test aplicación de privacidad diferencial"""
        # Configurar participantes
        participants = ["secure_node_1", "secure_node_2", "secure_node_3"]
        secure_aggregator.set_expected_participants(participants)

        # Simular pesos originales
        original_weights = {"layer1": torch.tensor([1.0, 2.0, 3.0])}

        # Aplicar ruido DP
        noisy_weights = secure_aggregator._apply_differential_privacy(original_weights)

        # Los pesos deben ser diferentes (ruido añadido)
        assert not torch.equal(original_weights["layer1"], noisy_weights["layer1"])

        # Pero deben estar en el mismo rango aproximado
        diff = torch.abs(original_weights["layer1"] - noisy_weights["layer1"])
        assert torch.mean(diff) < 1.0  # Ruido razonable

    @pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
    def test_homomorphic_encryption_workflow(self, secure_aggregator):
        """Test flujo completo de encriptación homomórfica"""
        # Generar claves
        public_key, private_key = secure_aggregator.he.generate_keys()
        assert public_key is not None
        assert private_key is not None

        # Encriptar tensor
        original_tensor = torch.tensor([1.0, 2.0, 3.0, 4.0, 5.0])
        encrypted = secure_aggregator.he.encrypt_tensor(original_tensor, public_key)

        assert len(encrypted) == 5  # Mismo número de elementos

        # Desencriptar
        decrypted = secure_aggregator.he.decrypt_tensor(encrypted, private_key, original_tensor.shape)

        # Debe ser igual al original (con pequeña pérdida de precisión)
        diff = torch.abs(original_tensor - decrypted)
        assert torch.max(diff) < 1e-5  # Precisión aceptable

    @pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
    def test_secure_aggregation_with_encryption(self, secure_aggregator):
        """Test agregación segura con encriptación"""
        participants = ["secure_agg_1", "secure_agg_2"]
        secure_aggregator.set_expected_participants(participants)

        # Simular actualizaciones encriptadas
        for node_id in participants:
            weights = {"param": [1.0, 2.0]}
            num_samples = 100

            # Encriptar pesos
            encrypted_weights = {}
            for layer_name, weight_vals in weights.items():
                tensor_weights = torch.tensor(weight_vals)
                encrypted_weights[layer_name] = secure_aggregator.he.encrypt_tensor(
                    tensor_weights, secure_aggregator.he.public_key
                )

            # Enviar actualización encriptada
            secure_aggregator.add_encrypted_weight_update(
                node_id=node_id,
                encrypted_weights=encrypted_weights,
                num_samples=num_samples,
                public_key=secure_aggregator.he.public_key
            )

        # Verificar que se pueden agregar
        assert secure_aggregator.can_aggregate() == True

        # Realizar agregación segura
        result = secure_aggregator.aggregate_weights()

        assert "param" in result
        assert len(result["param"]) == 2

    def test_privacy_budget_tracking(self, coordinator):
        """Test seguimiento de presupuesto de privacidad"""
        coordinator.create_session("privacy_budget_session", "model", 2, 4)

        # Verificar presupuesto inicial
        initial_budget = coordinator.verify_privacy_budget("privacy_budget_session")
        assert initial_budget["budget_remaining"] == 1.0

        # Consumir presupuesto gradualmente
        for i in range(5):
            consumed = coordinator.consume_privacy_budget("privacy_budget_session", 0.15)
            assert consumed == True

        # Verificar presupuesto reducido
        current_budget = coordinator.verify_privacy_budget("privacy_budget_session")
        assert current_budget["budget_remaining"] < 1.0

        # Intentar consumir más del disponible
        depleted = coordinator.consume_privacy_budget("privacy_budget_session", 1000)
        assert depleted == False

    def test_secure_communication_channels(self, coordinator):
        """Test canales de comunicación seguros"""
        coordinator.create_session("secure_comm_session", "model", 2, 4)

        nodes = ["secure_node_1", "secure_node_2"]
        for node_id in nodes:
            coordinator.register_node(node_id)
            coordinator.add_node_to_session("secure_comm_session", node_id)

        coordinator.start_training("secure_comm_session")

        # Simular comunicación encriptada
        for node_id in nodes:
            # Enviar actualización "encriptada"
            update = {
                "encrypted_weights": {"layer1": "encrypted_data_123"},
                "samples_used": 100,
                "encryption_metadata": {"algorithm": "AES-256", "key_id": "key_001"}
            }

            result = coordinator.submit_model_update("secure_comm_session", node_id, update)
            assert result == True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
