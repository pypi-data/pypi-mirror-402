"""
Pruebas unitarias para el generador de pruebas de entrenamiento federado.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from .training_prover import (
    TrainingProver, TrainingProof, TrainingParameters,
    create_training_prover, generate_federated_training_proof
)
from .zkp_engine import ZKPEngine, ZKPType, ZKPProof
from ..core.config import Config


class TestTrainingProver:
    """Pruebas para TrainingProver."""

    @pytest.fixture
    def config(self):
        """Configuración de prueba."""
        return Config()

    @pytest.fixture
    def mock_zkp_engine(self):
        """Motor ZKP mockeado."""
        engine = AsyncMock(spec=ZKPEngine)

        # Mock para generate_proof
        async def mock_generate_proof(proof_type, statement, private_inputs, public_inputs, prover_id=None):
            proof = ZKPProof(
                proof_id=f"mock_proof_{statement}",
                proof_type=proof_type,
                statement=statement,
                proof_data={'proof_elements': ['mock_element']},
                public_inputs=public_inputs,
                created_at=datetime.now()
            )
            return proof

        engine.generate_proof = mock_generate_proof

        # Mock para verify_proof
        engine.verify_proof = AsyncMock(return_value=True)

        # Mock para get_engine_stats
        engine.get_engine_stats = MagicMock(return_value={
            'total_proofs': 0,
            'verified_proofs': 0,
            'average_verification_time_ms': 0.0
        })

        return engine

    @pytest.fixture
    def training_prover(self, config, mock_zkp_engine):
        """Instancia de TrainingProver con mocks."""
        prover = TrainingProver(config, mock_zkp_engine)
        return prover

    @pytest.fixture
    def sample_training_data(self):
        """Datos de ejemplo para pruebas."""
        return {
            'training_data_stats': {
                'num_samples': 1000,
                'data_variance': 0.5,
                'distribution_hash': 'abc123'
            },
            'training_parameters': {
                'epochs': 5,
                'batch_size': 32,
                'learning_rate': 0.001,
                'optimizer': 'adam',
                'loss_function': 'cross_entropy',
                'min_accuracy_threshold': 0.8,
                'max_training_time': 3600,
                'required_data_samples': 500
            },
            'training_results': {
                'epochs_completed': 5,
                'batch_size_used': 32,
                'training_time_seconds': 1200,
                'final_accuracy': 0.85,
                'loss_improvement': 0.3,
                'gradient_norm': 0.1,
                'convergence_rate': 0.9,
                'parameter_updates_count': 1000,
                'model_size_mb': 50.0
            },
            'model_parameters': {'layer1': [1, 2, 3], 'layer2': [4, 5, 6]},
            'training_metadata': {'hardware': 'gpu', 'framework': 'pytorch'}
        }

    @pytest.mark.asyncio
    async def test_initialization(self, training_prover):
        """Prueba la inicialización del TrainingProver."""
        assert training_prover.config is not None
        assert training_prover.zkp_engine is not None
        assert training_prover.training_proofs == {}

    @pytest.mark.asyncio
    async def test_generate_training_proof(self, training_prover, sample_training_data):
        """Prueba la generación completa de una prueba de entrenamiento."""
        data = sample_training_data

        # Convertir parámetros
        params = TrainingParameters(**data['training_parameters'])

        # Generar prueba
        proof = await training_prover.generate_training_proof(
            node_id="node_001",
            session_id="session_123",
            round_number=1,
            training_data_stats=data['training_data_stats'],
            training_parameters=params,
            training_results=data['training_results'],
            model_parameters=data['model_parameters'],
            training_metadata=data['training_metadata']
        )

        # Verificar estructura de la prueba
        assert isinstance(proof, TrainingProof)
        assert proof.node_id == "node_001"
        assert proof.session_id == "session_123"
        assert proof.round_number == 1
        assert proof.proof_id is not None
        assert isinstance(proof.data_realness_proof, ZKPProof)
        assert isinstance(proof.parameter_compliance_proof, ZKPProof)
        assert isinstance(proof.contribution_validity_proof, ZKPProof)
        assert isinstance(proof.model_update_proof, ZKPProof)
        assert proof.training_metadata == data['training_metadata']
        assert proof.created_at is not None
        assert not proof.verified  # Aún no verificada

        # Verificar que se almacenó
        stored_proof = training_prover.get_training_proof("node_001", "session_123", 1)
        assert stored_proof is not None
        assert stored_proof.proof_id == proof.proof_id

    @pytest.mark.asyncio
    async def test_verify_training_proof(self, training_prover, sample_training_data):
        """Prueba la verificación de una prueba de entrenamiento."""
        data = sample_training_data
        params = TrainingParameters(**data['training_parameters'])

        # Generar prueba primero
        proof = await training_prover.generate_training_proof(
            "node_001", "session_123", 1,
            data['training_data_stats'], params, data['training_results'],
            data['model_parameters'], data['training_metadata']
        )

        # Verificar la prueba
        is_valid = await training_prover.verify_training_proof(proof)

        assert is_valid
        assert proof.verified
        assert proof.verification_time_ms is not None

    @pytest.mark.asyncio
    async def test_data_realness_proof_insufficient_samples(self, training_prover):
        """Prueba que falle cuando hay muestras insuficientes."""
        data_stats = {
            'num_samples': 100,  # Menos que el mínimo requerido
            'data_variance': 0.5,
            'distribution_hash': 'abc123'
        }

        params = TrainingParameters(
            epochs=5, batch_size=32, learning_rate=0.001, optimizer='adam',
            loss_function='cross_entropy', min_accuracy_threshold=0.8,
            max_training_time=3600, required_data_samples=500
        )

        with pytest.raises(ValueError, match="Insuficientes muestras de datos"):
            await training_prover._prove_data_realness("node_001", data_stats, params)

    @pytest.mark.asyncio
    async def test_parameter_compliance_proof_insufficient_epochs(self, training_prover):
        """Prueba que falle cuando hay epochs insuficientes."""
        training_results = {
            'epochs_completed': 3,  # Menos que los requeridos
            'batch_size_used': 32,
            'training_time_seconds': 1200,
            'final_accuracy': 0.85
        }

        params = TrainingParameters(
            epochs=5, batch_size=32, learning_rate=0.001, optimizer='adam',
            loss_function='cross_entropy', min_accuracy_threshold=0.8,
            max_training_time=3600, required_data_samples=500
        )

        with pytest.raises(ValueError, match="Epochs insuficientes"):
            await training_prover._prove_parameter_compliance("node_001", training_results, params)

    def test_get_prover_stats(self, training_prover):
        """Prueba la obtención de estadísticas del prover."""
        stats = training_prover.get_prover_stats()

        assert 'total_training_proofs' in stats
        assert 'verified_training_proofs' in stats
        assert 'average_verification_time_ms' in stats
        assert 'zkp_engine_stats' in stats

        assert stats['total_training_proofs'] == 0
        assert stats['verified_training_proofs'] == 0

    def test_create_training_prover(self):
        """Prueba la función de conveniencia create_training_prover."""
        prover = create_training_prover()
        assert isinstance(prover, TrainingProver)

    @pytest.mark.asyncio
    async def test_generate_federated_training_proof(self, training_prover, sample_training_data):
        """Prueba la función de conveniencia generate_federated_training_proof."""
        data = sample_training_data

        proof = await generate_federated_training_proof(
            training_prover=training_prover,
            node_id="node_002",
            session_id="session_456",
            round_number=2,
            training_data_stats=data['training_data_stats'],
            training_parameters=data['training_parameters'],
            training_results=data['training_results'],
            model_parameters=data['model_parameters'],
            training_metadata=data['training_metadata']
        )

        assert isinstance(proof, TrainingProof)
        assert proof.node_id == "node_002"
        assert proof.session_id == "session_456"
        assert proof.round_number == 2

    def test_training_parameters_dataclass(self):
        """Prueba la dataclass TrainingParameters."""
        params = TrainingParameters(
            epochs=10,
            batch_size=64,
            learning_rate=0.01,
            optimizer='sgd',
            loss_function='mse',
            min_accuracy_threshold=0.9,
            max_training_time=7200,
            required_data_samples=1000
        )

        assert params.epochs == 10
        assert params.batch_size == 64
        assert params.learning_rate == 0.01
        assert params.optimizer == 'sgd'
        assert params.loss_function == 'mse'
        assert params.min_accuracy_threshold == 0.9
        assert params.max_training_time == 7200
        assert params.required_data_samples == 1000

    def test_training_proof_dataclass(self):
        """Prueba la dataclass TrainingProof."""
        mock_proof = ZKPProof(
            proof_id="mock",
            proof_type=ZKPType.BULLETPROOF,
            statement="test",
            proof_data={},
            public_inputs={},
            created_at=datetime.now()
        )

        proof = TrainingProof(
            node_id="node_001",
            session_id="session_123",
            round_number=1,
            proof_id="proof_123",
            data_realness_proof=mock_proof,
            parameter_compliance_proof=mock_proof,
            contribution_validity_proof=mock_proof,
            model_update_proof=mock_proof,
            training_metadata={'test': 'data'},
            created_at=datetime.now()
        )

        assert proof.node_id == "node_001"
        assert proof.session_id == "session_123"
        assert proof.round_number == 1
        assert proof.proof_id == "proof_123"
        assert not proof.verified
        assert proof.verification_time_ms is None