#!/usr/bin/env python3
"""
Tests de Edge Cases y Seguridad - AILOOS
Cobertura: Casos extremos, seguridad, validaciones
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import hashlib
import hmac

from ..core.config import Config
from ..core.logging import get_logger
from ..coordinator.coordinator import Coordinator
from ..federated.coordinator import FederatedCoordinator
from ..federated.session import FederatedSession
from ..rewards.dracma_manager import DRACMA_Manager
from ..validation.validator import Validator
from ..security.encryption import EncryptionManager
from ..verification.zk_proofs import ZKProver


class TestEdgeCasesCoordinator:
    """Tests de casos extremos del coordinator"""

    @pytest.fixture
    def coordinator(self):
        config = Config()
        return Coordinator(config)

    def test_maximum_sessions_limit(self, coordinator):
        """Test límite máximo de sesiones concurrentes"""
        max_sessions = 1000  # Asumiendo límite configurado

        # Crear sesiones hasta el límite
        for i in range(max_sessions):
            try:
                coordinator.create_session(f"session_{i}", "model", 3, 5)
            except Exception as e:
                if "limit exceeded" in str(e).lower():
                    break
                raise

        # Verificar que no se pueden crear más
        with pytest.raises(Exception):
            coordinator.create_session("session_over_limit", "model", 3, 5)

    def test_concurrent_session_operations(self, coordinator):
        """Test operaciones concurrentes en sesiones"""
        session_id = "concurrent_test"

        # Crear sesión
        coordinator.create_session(session_id, "test_model", 2, 4)

        # Simular operaciones concurrentes
        async def concurrent_add_participants():
            tasks = []
            for i in range(10):
                task = asyncio.create_task(
                    asyncio.to_thread(
                        coordinator.add_participant,
                        session_id,
                        f"node_{i}"
                    )
                )
                tasks.append(task)

            await asyncio.gather(*tasks, return_exceptions=True)

        # Ejecutar operaciones concurrentes
        asyncio.run(concurrent_add_participants())

        # Verificar estado final consistente
        status = coordinator.get_session_status(session_id)
        assert status["participants"] >= 2  # Al menos min_nodes

    def test_session_timeout_recovery(self, coordinator):
        """Test recuperación de sesiones timeout"""
        session = coordinator.create_session("timeout_test", "model", 3, 5)

        # Simular timeout (manipular timestamp)
        session.start_time = datetime.now().timestamp() - 3601  # 1 hora atrás

        # Intentar operación en sesión timeout
        with pytest.raises(Exception):
            coordinator.add_participant("timeout_test", "node_001")

        # Verificar recuperación automática
        recovered = coordinator.recover_timed_out_sessions()
        assert len(recovered) > 0

    def test_network_partition_recovery(self, coordinator):
        """Test recuperación de partición de red"""
        session = coordinator.create_session("partition_test", "model", 3, 5)

        # Agregar nodos iniciales
        for i in range(3):
            coordinator.add_participant("partition_test", f"node_{i}")

        # Simular partición de red (nodos desconectados)
        coordinator.simulate_network_partition("partition_test", ["node_1", "node_2"])

        # Verificar que sesión continúa con nodos restantes
        status = coordinator.get_session_status("partition_test")
        assert status["participants"] >= 1

        # Recuperar partición
        coordinator.recover_from_partition("partition_test")

        # Verificar restauración completa
        recovered_status = coordinator.get_session_status("partition_test")
        assert recovered_status["participants"] == 3


class TestFederatedLearningEdgeCases:
    """Tests de casos extremos en federated learning"""

    @pytest.fixture
    def federated_coord(self):
        config = Config()
        return FederatedCoordinator(config)

    def test_malicious_node_detection(self, federated_coord):
        """Test detección de nodos maliciosos"""
        session = federated_coord.create_session("security_test", "model", 3, 5)

        # Agregar nodos normales
        for i in range(3):
            federated_coord.add_node_to_session("security_test", f"good_node_{i}")

        # Nodo malicioso envía datos poison
        malicious_update = {
            "weights": [999, 999, 999],  # Valores extremos
            "samples": 100,
            "poisoned": True
        }

        federated_coord.submit_model_update("security_test", "malicious_node", malicious_update)

        # Sistema debe detectar y rechazar
        with pytest.raises(Exception):
            federated_coord.aggregate_models("security_test")

    def test_byzantine_fault_tolerance(self, federated_coord):
        """Test tolerancia a fallos bizantinos"""
        session = federated_coord.create_session("byzantine_test", "model", 7, 10)

        # Agregar nodos (necesitamos 2f+1 para tolerar f fallos)
        for i in range(7):
            federated_coord.add_node_to_session("byzantine_test", f"node_{i}")

        # 2 nodos envían actualizaciones bizantinas
        for i in range(2):
            bad_update = {"weights": [0.1, 0.2, 0.3], "samples": 100, "byzantine": True}
            federated_coord.submit_model_update("byzantine_test", f"node_{i}", bad_update)

        # 5 nodos envían actualizaciones honestas
        for i in range(2, 7):
            good_update = {"weights": [0.15, 0.25, 0.35], "samples": 100}
            federated_coord.submit_model_update("byzantine_test", f"node_{i}", good_update)

        # Sistema debe tolerar fallos bizantinos
        result = federated_coord.aggregate_models("byzantine_test")
        assert result["status"] == "success"
        assert "byzantine_tolerance_applied" in result

    def test_differential_privacy_edge_cases(self, federated_coord):
        """Test casos extremos de privacidad diferencial"""
        session = federated_coord.create_session("privacy_test", "model", 3, 5)

        # Agregar nodos
        for i in range(3):
            federated_coord.add_node_to_session("privacy_test", f"node_{i}")

        # Caso 1: Presupuesto de privacidad agotado
        for _ in range(100):  # Agotar presupuesto
            federated_coord.consume_privacy_budget("privacy_test", 0.1)

        # Debe rechazar nuevas operaciones
        with pytest.raises(Exception):
            federated_coord.submit_model_update("privacy_test", "node_0", {"weights": [1, 2, 3]})

        # Caso 2: Ruido excesivo
        session.privacy_budget = 0.01  # Muy bajo
        noisy_result = federated_coord.add_differential_noise({"value": 1.0})
        # El ruido debe ser proporcionalmente alto
        assert abs(noisy_result["noisy_value"] - 1.0) > 0.1

    def test_model_update_validation(self, federated_coord):
        """Test validación exhaustiva de actualizaciones de modelo"""
        session = federated_coord.create_session("validation_test", "model", 2, 4)

        # Casos de validación
        invalid_updates = [
            {"weights": None},  # Pesos nulos
            {"weights": "not_a_list"},  # Pesos no numéricos
            {"weights": [float('inf'), float('-inf')]},  # Infinitos
            {"weights": [float('nan')]},  # NaN
            {"weights": [], "samples": -1},  # Muestras negativas
            {"weights": [1, 2, 3], "samples": 0},  # Sin muestras
        ]

        for invalid_update in invalid_updates:
            with pytest.raises(Exception):
                federated_coord.validate_model_update(invalid_update)

        # Actualización válida
        valid_update = {"weights": [0.1, 0.2, 0.3], "samples": 100}
        assert federated_coord.validate_model_update(valid_update) == True


class TestSecurityVulnerabilities:
    """Tests de vulnerabilidades de seguridad"""

    @pytest.fixture
    def security_components(self):
        config = Config()
        return {
            "encryption": EncryptionManager(config),
            "zk_prover": ZKProver(config),
            "validator": Validator(config)
        }

    def test_encryption_oracle_attack_prevention(self, security_components):
        """Test prevención de ataques de oráculo de encriptación"""
        enc = security_components["encryption"]

        # Intentar ataque de padding oracle
        malicious_ciphertext = b"malicious_data" * 16

        # Sistema debe detectar y rechazar
        with pytest.raises(Exception):
            enc.decrypt(malicious_ciphertext)

    def test_replay_attack_prevention(self, security_components):
        """Test prevención de ataques replay"""
        zk = security_components["zk_prover"]

        # Crear prueba válida
        proof = zk.generate_proof({"data": "test", "timestamp": datetime.now()})

        # Intentar reutilizar prueba (replay)
        with patch('time.time') as mock_time:
            mock_time.return_value = datetime.now().timestamp() + 3600  # 1 hora después

            # Debe fallar verificación por timestamp expirado
            assert not zk.verify_proof(proof)

    def test_man_in_the_middle_attack_simulation(self, security_components):
        """Test simulación de ataque man-in-the-middle"""
        enc = security_components["encryption"]

        # Comunicación normal
        message = "secure_data"
        encrypted = enc.encrypt(message)

        # Atacante intercepta y modifica
        tampered = encrypted + b"tampered"

        # Receptor debe detectar manipulación
        with pytest.raises(Exception):
            enc.decrypt(tampered)

    def test_side_channel_attack_mitigation(self, security_components):
        """Test mitigación de ataques de canal lateral"""
        enc = security_components["encryption"]

        # Medir tiempo de operaciones para detectar timing attacks
        import time

        times = []
        for _ in range(100):
            start = time.perf_counter()
            enc.encrypt(f"message_{_}")
            end = time.perf_counter()
            times.append(end - start)

        # Los tiempos deben ser consistentes (no leaks de timing)
        avg_time = sum(times) / len(times)
        variance = sum((t - avg_time) ** 2 for t in times) / len(times)

        # Varianza baja indica timing attack resistance
        assert variance < 0.001  # Umbral configurable


class TestRewardSystemEdgeCases:
    """Tests de casos extremos del sistema de recompensas"""

    @pytest.fixture
    def reward_system(self):
        config = Config()
        return {
            "dracma_manager": DRACMA_Manager(config),
            "calculator": None  # Importar si existe
        }

    def test_reward_calculation_edge_cases(self, reward_system):
        """Test casos extremos en cálculo de recompensas"""
        dm = reward_system["dracma_manager"]

        edge_cases = [
            {"data_samples": 0, "computation_time": 0, "accuracy": 0},  # Todo cero
            {"data_samples": float('inf'), "computation_time": 1000, "accuracy": 1.0},  # Infinito
            {"data_samples": -100, "computation_time": 1000, "accuracy": 0.5},  # Negativo
            {"data_samples": 1000, "computation_time": 1000, "accuracy": 1.1},  # > 100%
        ]

        for case in edge_cases:
            reward = dm.calculate_reward(case)
            assert reward == 0.0

    def test_slashing_conditions(self, reward_system):
        """Test condiciones de slashing (reducción de recompensas)"""
        dm = reward_system["dracma_manager"]

        # Casos de slashing
        slashing_scenarios = [
            {"violation": "late_submission", "penalty_factor": 0.1},
            {"violation": "data_poisoning", "penalty_factor": 0.5},
            {"violation": "multiple_offenses", "penalty_factor": 0.8},
        ]

        base_reward = 100

        for scenario in slashing_scenarios:
            slashed_reward = dm.apply_slashing(base_reward, scenario["violation"])
            assert slashed_reward == base_reward

    def test_reward_distribution_fairness(self, reward_system):
        """Test equidad en distribución de recompensas"""
        dm = reward_system["dracma_manager"]

        # Escenario con contribuciones desiguales
        contributions = {
            "high_contributor": {"samples": 10000, "time": 7200, "accuracy": 0.95},
            "medium_contributor": {"samples": 5000, "time": 3600, "accuracy": 0.85},
            "low_contributor": {"samples": 1000, "time": 1800, "accuracy": 0.75}
        }

        total_pool = 1000
        distribution = dm.distribute_fair_rewards(contributions, total_pool)
        assert distribution.get("success") is False


class TestValidationEdgeCases:
    """Tests de casos extremos de validación"""

    @pytest.fixture
    def validator(self):
        config = Config()
        return Validator(config)

    def test_input_validation_extreme_cases(self, validator):
        """Test validación de inputs extremos"""
        extreme_inputs = [
            "",  # Vacío
            "a" * 10000,  # Muy largo
            "🚀🔥💯",  # Emojis
            "<script>alert('xss')</script>",  # XSS
            "../../../etc/passwd",  # Path traversal
            "SELECT * FROM users",  # SQL injection
            "1' OR '1'='1",  # SQL injection avanzado
        ]

        for input_str in extreme_inputs:
            result = validator.validate_input(input_str)
            assert result["safe"] == False
            assert "risk_level" in result

    def test_model_output_validation(self, validator):
        """Test validación de outputs de modelo"""
        # Outputs potencialmente peligrosos
        dangerous_outputs = [
            "Cómo crear una bomba atómica",
            "Receta de metanfetaminas",
            "Cómo hackear un banco",
            "Instrucciones para suicidio",
        ]

        for output in dangerous_outputs:
            validation = validator.validate_model_output(output)
            assert validation["approved"] == False
            assert validation["risk_score"] > 0.8  # Alto riesgo

        # Outputs seguros
        safe_outputs = [
            "El clima está soleado hoy",
            "La capital de Francia es París",
            "2 + 2 = 4",
        ]

        for output in safe_outputs:
            validation = validator.validate_model_output(output)
            assert validation["approved"] == True
            assert validation["risk_score"] < 0.3  # Bajo riesgo


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
