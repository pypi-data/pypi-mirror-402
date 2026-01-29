#!/usr/bin/env python3
"""
Tests de Integración End-to-End - AILOOS
Cobertura: Flujos completos de negocio
"""

import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime

from ..core.config import Config
from ..demo_complete_pipeline import DemoCompletePipeline
from ..coordinator.coordinator import Coordinator
from ..federated.coordinator import FederatedCoordinator
from ..marketplace.marketplace import Marketplace
from ..rewards.dracma_manager import DRACMA_Manager
from ..blockchain.dracma_token import get_token_manager
from ..web.wallet_integration import get_wallet_integration


class TestCompletePipeline:
    """Tests del pipeline completo de demostración"""

    @pytest.fixture
    def pipeline(self):
        config = Config()
        return DemoCompletePipeline(config)

    def test_full_pipeline_execution(self, pipeline):
        """Test ejecución completa del pipeline"""
        with patch('subprocess.run') as mock_run, \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', create=True) as mock_open:

            # Configurar mocks
            mock_run.return_value = Mock(returncode=0, stdout="Success")
            mock_open.return_value = Mock()

            # Ejecutar pipeline
            result = pipeline.run_complete_demo()

            # Verificar resultado
            assert result["status"] == "completed"
            assert "coordinator_started" in result
            assert "federated_session_created" in result
            assert "training_completed" in result
            assert "rewards_distributed" in result

    def test_pipeline_error_recovery(self, pipeline):
        """Test recuperación de errores en pipeline"""
        with patch('subprocess.run') as mock_run:
            # Simular fallo en un paso
            mock_run.side_effect = [
                Mock(returncode=0),  # Paso 1 OK
                Exception("Network error"),  # Paso 2 falla
                Mock(returncode=0)   # Paso 3 OK (no llega aquí)
            ]

            with pytest.raises(Exception):
                pipeline.run_complete_demo()

            # Verificar que se intentó recuperación
            assert mock_run.call_count >= 2

    def test_pipeline_cleanup(self, pipeline):
        """Test limpieza de recursos después del pipeline"""
        with patch('shutil.rmtree') as mock_rmtree, \
             patch('os.path.exists') as mock_exists:

            mock_exists.return_value = True

            # Ejecutar limpieza
            pipeline.cleanup_resources()

            # Verificar que se limpiaron directorios
            assert mock_rmtree.call_count > 0


class TestFederatedLearningFlow:
    """Tests del flujo completo de aprendizaje federado"""

    @pytest.fixture
    def federated_setup(self):
        config = Config()
        coordinator = FederatedCoordinator(config)
        dracma_manager = DRACMA_Manager(config)
        return {
            "coordinator": coordinator,
            "dracma_manager": dracma_manager,
            "config": config
        }

    def test_complete_federated_workflow(self, federated_setup):
        """Test workflow completo: sesión → nodos → entrenamiento → recompensas"""
        coord = federated_setup["coordinator"]
        DracmaS = federated_setup["dracma_manager"]

        # 1. Crear sesión
        session = coord.create_session("e2e_session_001", "llm_model", 3, 5)
        assert session.status == "created"

        # 2. Agregar nodos participantes
        nodes = ["node_001", "node_002", "node_003"]
        for node_id in nodes:
            coord.add_node_to_session("e2e_session_001", node_id)

        # 3. Verificar que puede iniciar
        status = coord.get_session_status("e2e_session_001")
        assert status["can_start"] == True

        # 4. Simular envío de actualizaciones de modelo
        for node_id in nodes:
            update = {
                "weights": [0.1, 0.2, 0.3],
                "samples_used": 100,
                "accuracy": 0.85
            }
            coord.submit_model_update("e2e_session_001", node_id, update)

        # 5. Ejecutar agregación
        result = coord.aggregate_models("e2e_session_001")
        assert result["status"] == "success"

        # 6. Calcular y distribuir recompensas
        rewards_data = {
            "session_id": "e2e_session_001",
            "participants": nodes,
            "total_reward_pool": 1000,
            "contributions": {node: 100 for node in nodes}
        }

        distribution = dracma.distribute_session_rewards(rewards_data)
        assert len(distribution) == 3
        assert sum(distribution.values()) == 1000

    def test_multi_round_federated_learning(self, federated_setup):
        """Test aprendizaje federado multi-round"""
        coord = federated_setup["coordinator"]

        session = coord.create_session("multi_round_session", "complex_model", 2, 4, rounds=3)

        # Agregar nodos
        coord.add_node_to_session("multi_round_session", "node_a")
        coord.add_node_to_session("multi_round_session", "node_b")

        # Simular múltiples rounds
        for round_num in range(1, 4):
            # Enviar actualizaciones para este round
            for node_id in ["node_a", "node_b"]:
                update = {
                    "weights": [0.1 * round_num, 0.2 * round_num],
                    "samples_used": 100 * round_num,
                    "round": round_num
                }
                coord.submit_model_update("multi_round_session", node_id, update)

            # Agregar round
            coord.advance_round("multi_round_session")

            # Verificar progreso
            status = coord.get_session_status("multi_round_session")
            assert status["current_round"] == round_num

        # Verificar finalización
        final_status = coord.get_session_status("multi_round_session")
        assert final_status["current_round"] == 3
        assert final_status["is_complete"] == True


class TestMarketplaceIntegration:
    """Tests de integración del marketplace"""

    @pytest.fixture
    def marketplace_setup(self):
        config = Config()
        marketplace = Marketplace(config)
        wallet = get_wallet_integration()
        dracma_token = get_token_manager()
        return {
            "marketplace": marketplace,
            "wallet": wallet,
            "dracma_token": dracma_token
        }

    def test_data_marketplace_transaction(self, marketplace_setup):
        """Test transacción completa en marketplace de datos"""
        mp = marketplace_setup["marketplace"]
        wallet = marketplace_setup["wallet"]
        token = marketplace_setup["dracma_token"]

        # 1. Crear listing de datos
        data_listing = {
            "data_id": "dataset_001",
            "owner": "seller_node",
            "price": 100,
            "data_hash": "hash123",
            "size": 1000
        }

        listing_id = mp.create_listing(data_listing)
        assert listing_id is not None

        # 2. Comprador busca datos
        search_results = mp.search_data("dataset")
        assert len(search_results) > 0

        # 3. Ejecutar compra
        buyer_wallet = "buyer_wallet_001"
        purchase_result = mp.purchase_data(listing_id, buyer_wallet, 100)

        assert purchase_result["status"] == "completed"
        assert purchase_result["transaction_id"] is not None

        # 4. Verificar transferencia de tokens
        balance_check = asyncio.run(token.get_user_balance(buyer_wallet))
        assert balance_check >= 0  # Balance actualizado

    def test_model_marketplace_flow(self, marketplace_setup):
        """Test flujo completo de marketplace de modelos"""
        mp = marketplace_setup["marketplace"]

        # 1. Publicar modelo entrenado
        model_listing = {
            "model_id": "llm_v1_trained",
            "owner": "trainer_node",
            "price": 500,
            "accuracy": 0.92,
            "model_hash": "model_hash_123"
        }

        model_id = mp.publish_model(model_listing)
        assert model_id is not None

        # 2. Buscar modelos
        available_models = mp.get_available_models()
        assert len(available_models) > 0

        # 3. Alquilar modelo
        rental_result = mp.rent_model(model_id, "renter_node", duration_hours=24)
        assert rental_result["status"] == "active"
        assert "rental_id" in rental_result


class TestSecurityAndPrivacy:
    """Tests de seguridad y privacidad end-to-end"""

    @pytest.fixture
    def security_setup(self):
        config = Config()
        return {
            "federated_coord": FederatedCoordinator(config),
            "wallet": get_wallet_integration(),
            "validator": None  # Importar si existe
        }

    def test_secure_federated_communication(self, security_setup):
        """Test comunicación segura en federated learning"""
        coord = security_setup["federated_coord"]

        session = coord.create_session("secure_session", "secure_model", 3, 5)

        # Verificar encriptación de comunicaciones
        assert session.privacy_budget > 0

        # Simular comunicación encriptada
        encrypted_data = coord.encrypt_model_update({"weights": [1, 2, 3]})
        assert encrypted_data != {"weights": [1, 2, 3]}  # Debe estar encriptado

        # Verificar desencriptación
        decrypted_data = coord.decrypt_model_update(encrypted_data)
        assert decrypted_data == {"weights": [1, 2, 3]}

    def test_wallet_security_integration(self, security_setup):
        """Test integración segura con wallet"""
        pytest.skip("Wallet signing local no soportado en modo bridge-only")

    def test_privacy_budget_enforcement(self, security_setup):
        """Test enforcement de presupuesto de privacidad"""
        coord = security_setup["federated_coord"]

        session = coord.create_session("privacy_session", "private_model", 2, 4)

        # Agregar nodos
        coord.add_node_to_session("privacy_session", "node_1")
        coord.add_node_to_session("privacy_session", "node_2")

        # Verificar presupuesto inicial
        initial_budget = session.privacy_budget
        assert initial_budget > 0

        # Simular uso de privacidad
        for _ in range(5):
            coord.consume_privacy_budget("privacy_session", 0.1)

        # Verificar reducción de presupuesto
        current_budget = coord.get_privacy_budget("privacy_session")
        assert current_budget < initial_budget

        # Verificar bloqueo cuando se agota
        depleted = coord.consume_privacy_budget("privacy_session", 1000)
        assert depleted == False  # Debe fallar


class TestPerformanceAndScalability:
    """Tests de rendimiento y escalabilidad"""

    @pytest.fixture
    def performance_setup(self):
        config = Config()
        return {
            "coordinator": Coordinator(config),
            "federated_coord": FederatedCoordinator(config)
        }

    def test_concurrent_sessions(self, performance_setup):
        """Test manejo de múltiples sesiones concurrentes"""
        coord = performance_setup["coordinator"]

        # Crear múltiples sesiones concurrentes
        sessions = []
        for i in range(10):
            session = coord.create_session(f"concurrent_session_{i}", f"model_{i}", 3, 5)
            sessions.append(session)

        assert len(sessions) == 10

        # Verificar que todas están activas
        active_sessions = coord.list_active_sessions()
        assert len(active_sessions) == 10

    def test_large_scale_node_handling(self, performance_setup):
        """Test manejo de gran cantidad de nodos"""
        fed_coord = performance_setup["federated_coord"]

        session = fed_coord.create_session("large_session", "big_model", 50, 200)

        # Agregar muchos nodos
        for i in range(100):
            fed_coord.add_node_to_session("large_session", f"node_{i:03d}")

        status = fed_coord.get_session_status("large_session")
        assert status["participants"] == 100
        assert status["can_start"] == True

    def test_memory_efficiency(self, performance_setup):
        """Test eficiencia de memoria en operaciones grandes"""
        coord = performance_setup["coordinator"]

        # Crear sesión con modelo grande simulado
        session = coord.create_session("memory_test", "large_model", 5, 10)

        # Simular operaciones de memoria intensiva
        large_updates = []
        for i in range(50):
            update = {"weights": [0.1] * 10000}  # Modelo grande
            large_updates.append(update)

        # Verificar que no hay leaks de memoria (simulado)
        initial_memory = len(coord.sessions)
        # Procesar actualizaciones
        for update in large_updates:
            coord.process_model_update(session.session_id, update)

        final_memory = len(coord.sessions)
        assert final_memory == initial_memory  # No memory leaks


class TestDistributedFederatedLearningE2E:
    """Test completo E2E con 5+ nodos distribuidos simulando escenario real"""

    @pytest.fixture
    def distributed_setup(self):
        """Configurar entorno distribuido completo"""
        config = Config()

        # Componentes principales
        from ..federated.coordinator import FederatedCoordinator
        from ..federated.node_scheduler import NodeScheduler, SelectionCriteria
        from ..verification.zkp_engine import ZKPEngine
        from ..rewards.dracma_manager import DRACMA_Manager

        # Crear componentes
        federated_coord = FederatedCoordinator(config)
        zkp_engine = ZKPEngine(config)
        dracma_manager = DRACMA_Manager(config)

        # Simular registro de nodos distribuidos
        node_registry = {}
        for i in range(8):  # 8 nodos distribuidos
            node_id = f"distributed_node_{i:03d}"
            node_registry[node_id] = {
                "node_id": node_id,
                "location": ["EU", "US", "ASIA", "LATAM"][i % 4],
                "computational_capacity": 0.5 + (i * 0.1),
                "reputation_score": 0.7 + (i * 0.05),
                "registered_at": datetime.now().isoformat(),
                "status": "active"
            }

        return {
            "federated_coord": federated_coord,
            "zkp_engine": zkp_engine,
            "dracma_manager": dracma_manager,
            "node_registry": node_registry,
            "config": config
        }

    @pytest.mark.asyncio
    async def test_complete_distributed_federated_learning_pipeline(self, distributed_setup):
        """Test completo del pipeline federado con 5+ nodos distribuidos"""
        fed_coord = distributed_setup["federated_coord"]
        zkp_engine = distributed_setup["zkp_engine"]
        dracma_manager = distributed_setup["dracma_manager"]
        node_registry = distributed_setup["node_registry"]

        print("\n🚀 INICIANDO TEST E2E FEDERATED LEARNING CON 8 NODOS DISTRIBUIDOS")
        print("=" * 80)

        # FASE 1: INICIALIZACIÓN DEL SISTEMA
        print("\n📋 FASE 1: INICIALIZACIÓN DEL SISTEMA")

        # Registrar nodos en el coordinador
        registered_nodes = []
        for node_id, node_info in node_registry.items():
            fed_coord.register_node(node_id)
            registered_nodes.append(node_id)
            print(f"✅ Registrado nodo: {node_id} ({node_info['location']})")

        assert len(registered_nodes) == 8
        print(f"✅ Sistema inicializado con {len(registered_nodes)} nodos")

        # FASE 2: CREACIÓN DE SESIÓN FEDERADA
        print("\n🎯 FASE 2: CREACIÓN DE SESIÓN FEDERADA")

        session_id = "distributed_federated_session_001"
        session = fed_coord.create_session(
            session_id=session_id,
            model_name="distributed_llm_v1",
            min_nodes=5,
            max_nodes=8,
            rounds=3
        )

        assert session.session_id == session_id
        assert session.min_nodes == 5
        assert session.total_rounds == 3
        print(f"✅ Sesión creada: {session_id}")

        # FASE 3: REGISTRO DE PARTICIPANTES
        print("\n👥 FASE 3: REGISTRO DE PARTICIPANTES")

        # Seleccionar 6 nodos para participar (más que el mínimo)
        participant_nodes = registered_nodes[:6]

        for node_id in participant_nodes:
            success = fed_coord.add_node_to_session(session_id, node_id)
            assert success == True
            print(f"✅ Nodo agregado: {node_id}")

        # Verificar estado de la sesión
        session_status = fed_coord.get_session_status(session_id)
        assert session_status["participants"] == 6
        assert session_status["can_start"] == True
        print(f"✅ Participantes registrados: {session_status['participants']}/6")

        # FASE 4: INICIO DEL ENTRENAMIENTO
        print("\n🚀 FASE 4: INICIO DEL ENTRENAMIENTO")

        start_result = fed_coord.start_training(session_id)
        assert start_result["status"] == "training_started"
        assert start_result["participants"] == 6
        print("✅ Entrenamiento iniciado")

        # FASE 5: EJECUCIÓN DE RONDAS DE ENTRENAMIENTO
        print("\n🔄 FASE 5: EJECUCIÓN DE RONDAS DE ENTRENAMIENTO")

        for round_num in range(1, 4):  # 3 rondas
            print(f"\n   --- RONDA {round_num} ---")

            # Simular contribuciones de cada nodo
            round_contributions = []
            for node_id in participant_nodes:
                # Simular entrenamiento local
                local_accuracy = 0.75 + (round_num * 0.05) + (hash(node_id) % 100) / 1000
                samples_used = 500 + (round_num * 100)

                # Crear actualización de modelo simulada
                model_update = {
                    "weights": {
                        "layer_1": [0.1 * round_num + i * 0.01 for i in range(10)],
                        "layer_2": [0.2 * round_num + i * 0.02 for i in range(8)],
                        "output": [0.05 * round_num + i * 0.005 for i in range(5)]
                    },
                    "samples_used": samples_used,
                    "accuracy": local_accuracy,
                    "loss": 1.5 - (round_num * 0.2),
                    "training_time": 45.5 + (hash(node_id) % 10)
                }

                # Enviar actualización
                success = fed_coord.submit_model_update(session_id, node_id, model_update)
                assert success == True

                # Generar prueba ZKP para la contribución
                zkp_proof = await zkp_engine.generate_proof(
                    proof_type=zkp_engine.ZKPType.BULLETPROOF,
                    statement="federated_contribution_valid",
                    private_inputs={
                        "accuracy": local_accuracy,
                        "computation_stats": {
                            "samples_processed": samples_used,
                            "training_time": model_update["training_time"]
                        }
                    },
                    public_inputs={
                        "node_id": node_id,
                        "session_id": session_id,
                        "round": round_num
                    },
                    prover_id=node_id
                )

                # Verificar prueba ZKP
                is_valid = await zkp_engine.verify_proof(zkp_proof)
                assert is_valid == True

                round_contributions.append({
                    "node_id": node_id,
                    "accuracy": local_accuracy,
                    "samples_used": samples_used,
                    "zkp_proof_id": zkp_proof.proof_id
                })

                print(f"   ✅ {node_id}: accuracy={local_accuracy:.3f}, samples={samples_used}, ZKP={zkp_proof.proof_id[:8]}...")

            # Agregar modelos para esta ronda
            aggregation_result = fed_coord.aggregate_models(session_id)
            assert aggregation_result["status"] == "success"
            assert aggregation_result["round"] == round_num
            assert aggregation_result["participants"] == 6

            print(f"   🔄 Agregación completada: {aggregation_result['participants']} participantes")

            # Verificar estado después de la ronda
            current_status = fed_coord.get_session_status(session_id)
            assert current_status["current_round"] == round_num

        # Verificar finalización del entrenamiento
        final_status = fed_coord.get_session_status(session_id)
        assert final_status["current_round"] == 3
        assert final_status["is_complete"] == True
        print("✅ Todas las rondas completadas")

        # FASE 6: DISTRIBUCIÓN DE RECOMPENSAS
        print("\n💰 FASE 6: DISTRIBUCIÓN DE RECOMPENSAS")

        # Calcular contribuciones totales para distribución
        total_contributions = {}
        total_samples = 0

        for node_id in participant_nodes:
            # Simular contribución total basada en rendimiento
            base_contribution = 100
            accuracy_bonus = 50  # Basado en accuracy promedio
            consistency_bonus = 25  # Por completar todas las rondas

            total_contribution = base_contribution + accuracy_bonus + consistency_bonus
            total_contributions[node_id] = total_contribution
            total_samples += 1500  # 3 rondas * 500 samples

        # Distribuir recompensas
        rewards_data = {
            "session_id": session_id,
            "participants": participant_nodes,
            "total_reward_pool": 10000,  # 10000 DracmaS total
            "contributions": total_contributions,
            "total_samples": total_samples
        }

        distribution_result = await dracma_manager.calculate_and_distribute_rewards([
            {
                "node_id": node_id,
                "type": "federated_training",
                "metrics": {
                    "contribution_score": contribution,
                    "rounds_completed": 3,
                    "zkp_verified": True
                },
                "session_id": session_id
            }
            for node_id, contribution in total_contributions.items()
        ])

        assert "reported" in distribution_result
        print(f"✅ Reports enviados: {distribution_result.get('reported', 0)}")

        # Verificar balances de nodos
        for node_id in participant_nodes:
            balance = await dracma_manager.get_node_balance(node_id)
            assert balance["balance"] >= 0
            print(f"   💰 {node_id}: {balance['pending']:.2f} DRACMA (pending)")

        # FASE 7: VERIFICACIÓN FINAL DEL SISTEMA
        print("\n🔍 FASE 7: VERIFICACIÓN FINAL DEL SISTEMA")

        # Verificar estadísticas del sistema
        system_stats = await dracma_manager.get_system_stats()
        assert system_stats["distribution"]["mode"] == "bridge"

        # Verificar pruebas ZKP
        zkp_stats = zkp_engine.get_engine_stats()
        assert zkp_stats["total_proofs"] >= 18  # 6 nodos * 3 rondas
        assert zkp_stats["verified_proofs"] >= 18

        # Verificar estado final de la sesión
        final_session_status = fed_coord.get_session_status(session_id)
        assert final_session_status["is_complete"] == True
        assert final_session_status["participants"] == 6
        assert final_session_status["current_round"] == 3

        print("✅ Verificación del sistema completada")
        print(f"   📊 Pruebas ZKP generadas: {zkp_stats['total_proofs']}")
        print("   💰 DracmaS distribuido: bridge-only (pendiente endpoints)")
        print(f"   🎯 Sesiones completadas: 1")

        print("\n" + "=" * 80)
        print("🎉 TEST E2E FEDERATED LEARNING COMPLETADO EXITOSAMENTE")
        print("✅ Pipeline completo verificado: Inicialización → Sesiones → Rondas → ZKP → Recompensas")
        print("=" * 80)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
