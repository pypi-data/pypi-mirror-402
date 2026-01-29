"""
Pruebas unitarias básicas para el motor ZKP avanzado.
"""

import asyncio
import pytest
from datetime import datetime

from .zkp_engine import (
    ZKPEngine,
    ZKPType,
    KeyManager,
    create_zkp_engine,
    generate_bulletproof_range_proof,
    verify_proof_batch
)
from ..core.config import Config


class TestZKPEngine:
    """Pruebas para el motor ZKP."""

    @pytest.fixture
    def config(self):
        """Configuración de prueba."""
        return Config()

    @pytest.fixture
    def engine(self, config):
        """Instancia del motor ZKP."""
        return ZKPEngine(config)

    @pytest.mark.asyncio
    async def test_engine_initialization(self, engine):
        """Prueba la inicialización del motor."""
        assert engine.key_manager is not None
        assert len(engine.provers) > 0
        assert len(engine.verifiers) > 0
        assert ZKPType.BULLETPROOF in engine.provers
        assert ZKPType.GROTH16 in engine.provers

    @pytest.mark.asyncio
    async def test_bulletproof_range_proof(self, engine):
        """Prueba la generación y verificación de pruebas Bulletproof de rango."""
        # Generar prueba
        proof = await engine.generate_proof(
            ZKPType.BULLETPROOF,
            "range_proof",
            {'value': 0.85},
            {'min_val': 0.0, 'max_val': 1.0},
            "test_node"
        )

        assert proof.proof_type == ZKPType.BULLETPROOF
        assert proof.statement == "value in [0.0, 1.0]"
        assert not proof.verified

        # Verificar prueba
        is_valid = await engine.verify_proof(proof)
        assert is_valid
        assert proof.verified

    @pytest.mark.asyncio
    async def test_groth16_circuit_proof(self, engine):
        """Prueba la generación y verificación de pruebas Groth16."""
        # Generar prueba
        proof = await engine.generate_proof(
            ZKPType.GROTH16,
            "circuit_proof",
            {'input1': 5, 'input2': 10},
            {'expected_output': 50},
            "test_node"
        )

        assert proof.proof_type == ZKPType.GROTH16
        assert proof.statement == "circuit satisfied"

        # Verificar prueba
        is_valid = await engine.verify_proof(proof)
        assert is_valid
        assert proof.verified

    @pytest.mark.asyncio
    async def test_federated_contribution_verification(self, engine):
        """Prueba la verificación de contribuciones federadas."""
        model_params = {'layer1': [1.0, 2.0, 3.0], 'layer2': [4.0, 5.0]}
        data_fingerprint = "abc123"
        accuracy = 0.92
        computation_stats = {
            'training_time': 120.5,
            'cpu_usage': 85.0,
            'memory_usage': 2048
        }

        # Verificar contribución
        proof = await engine.verify_federated_contribution(
            "node_001",
            model_params,
            data_fingerprint,
            accuracy,
            computation_stats
        )

        assert proof is not None
        assert proof.verified

    @pytest.mark.asyncio
    async def test_proof_batch_verification(self, engine):
        """Prueba la verificación por lotes."""
        # Generar múltiples pruebas
        proofs = []
        for i in range(5):
            proof = await engine.generate_proof(
                ZKPType.BULLETPROOF,
                "range_proof",
                {'value': 0.8 + i * 0.01},
                {'min_val': 0.0, 'max_val': 1.0},
                f"node_{i}"
            )
            proofs.append(proof)

        # Verificar por lotes
        results = await verify_proof_batch(engine, proofs)

        assert len(results) == 5
        assert all(results)

        # Verificar que todas las pruebas están marcadas como verificadas
        for proof in proofs:
            assert proof.verified

    @pytest.mark.asyncio
    async def test_convenience_functions(self, config):
        """Prueba las funciones de conveniencia."""
        engine = create_zkp_engine(config)
        assert isinstance(engine, ZKPEngine)

        # Probar generación de prueba Bulletproof
        proof = await generate_bulletproof_range_proof(
            engine, 0.75, 0.0, 1.0, "test_node"
        )
        assert proof.proof_type == ZKPType.BULLETPROOF

    def test_engine_stats(self, engine):
        """Prueba las estadísticas del motor."""
        stats = engine.get_engine_stats()

        assert 'total_proofs' in stats
        assert 'verified_proofs' in stats
        assert 'proof_types' in stats
        assert 'average_verification_time_ms' in stats
        assert 'supported_types' in stats

        assert ZKPType.BULLETPROOF.value in stats['supported_types']
        assert ZKPType.GROTH16.value in stats['supported_types']

    def test_key_manager(self, config):
        """Prueba el gestor de claves."""
        key_manager = KeyManager(config, None)

        # Generar claves
        key_pair = key_manager.generate_key_pair(ZKPType.BULLETPROOF, "test_key")
        assert key_pair.key_type == ZKPType.BULLETPROOF
        assert key_pair.proving_key is not None
        assert key_pair.verification_key is not None

        # Almacenar y recuperar
        key_manager.store_key_pair("test_key", key_pair)
        retrieved = key_manager.get_proving_key("test_key")
        assert retrieved == key_pair

        verification_key = key_manager.get_verification_key("test_key")
        assert verification_key == key_pair.verification_key

    @pytest.mark.asyncio
    async def test_proof_storage(self, engine):
        """Prueba el almacenamiento de pruebas."""
        # Generar prueba
        proof = await engine.generate_proof(
            ZKPType.BULLETPROOF,
            "range_proof",
            {'value': 0.9},
            {'min_val': 0.0, 'max_val': 1.0}
        )

        # Recuperar prueba
        retrieved = engine.get_proof(proof.proof_id)
        assert retrieved == proof

        # Verificar que no existe una prueba inexistente
        nonexistent = engine.get_proof("nonexistent_id")
        assert nonexistent is None

    def test_custom_prover_registration(self, engine):
        """Prueba el registro de provers personalizados."""
        from .zkp_engine import ZKPProver

        class CustomProver(ZKPProver):
            def __init__(self, key_manager):
                self.key_manager = key_manager

            async def generate_proof(self, statement, private_inputs, public_inputs, key_pair):
                # Implementación dummy
                from .zkp_engine import ZKPProof
                return ZKPProof(
                    proof_id="custom_123",
                    proof_type=ZKPType.SIMPLE_RANGE_PROOF,
                    statement=statement,
                    proof_data={},
                    public_inputs=public_inputs,
                    created_at=datetime.now()
                )

        custom_prover = CustomProver(engine.key_manager)
        engine.register_custom_prover(ZKPType.SIMPLE_RANGE_PROOF, custom_prover)

        assert ZKPType.SIMPLE_RANGE_PROOF in engine.provers


if __name__ == "__main__":
    # Ejecutar pruebas básicas sin pytest
    async def run_basic_tests():
        config = Config()
        engine = ZKPEngine(config)

        print("Testing ZKP Engine initialization...")
        assert engine.key_manager is not None
        print("✓ Engine initialized successfully")

        print("Testing Bulletproof range proof...")
        proof = await engine.generate_proof(
            ZKPType.BULLETPROOF,
            "range_proof",
            {'value': 0.85},
            {'min_val': 0.0, 'max_val': 1.0},
            "test_node"
        )
        is_valid = await engine.verify_proof(proof)
        assert is_valid
        print("✓ Bulletproof range proof generated and verified")

        print("Testing Groth16 circuit proof...")
        proof2 = await engine.generate_proof(
            ZKPType.GROTH16,
            "circuit_proof",
            {'input1': 5, 'input2': 10},
            {'expected_output': 50},
            "test_node"
        )
        is_valid2 = await engine.verify_proof(proof2)
        assert is_valid2
        print("✓ Groth16 circuit proof generated and verified")

        print("Testing federated contribution verification...")
        proof3 = await engine.verify_federated_contribution(
            "node_001",
            {'layer1': [1.0, 2.0]},
            "abc123",
            0.92,
            {'training_time': 120.5, 'cpu_usage': 85.0}
        )
        assert proof3.verified
        print("✓ Federated contribution verified")

        stats = engine.get_engine_stats()
        print(f"Engine stats: {stats}")

        print("All basic tests passed! ✓")

    asyncio.run(run_basic_tests())