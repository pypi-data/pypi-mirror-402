"""
Módulo de integración cuántica para validación de trabajo Ailoos-DracmaS.

Proporciona funcionalidades para generar proofs de entrenamiento,
validación local y envío de trabajo validado al puente.
"""

import asyncio
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
import hashlib
import json
import time

from .bridge_client import get_bridge_client, BridgeClient, BridgeClientError
from .dracmas_config import get_dracmas_config, DracmaSConfig
from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TrainingProof:
    """Proof de entrenamiento cuántico."""
    node_id: str
    dataset_id: str
    compute_power: int
    proof_data: bytes
    model_hash: str
    expected_accuracy: str
    timestamp: int
    quantum_signature: Optional[str] = None


@dataclass
class ValidationResult:
    """Resultado de validación local."""
    is_valid: bool
    confidence_score: float
    validation_hash: str
    errors: Optional[List[str]] = None


class QuantumIntegrationError(Exception):
    """Error en operaciones de integración cuántica."""
    pass


class QuantumIntegrationManager:
    """
    Gestor de integración cuántica para validación de trabajo.

    Maneja la generación de proofs, validación local y envío
    de trabajo validado a través del puente cross-chain.
    """

    def __init__(self, bridge_client: Optional[BridgeClient] = None):
        """
        Inicializar gestor de integración cuántica.

        Args:
            bridge_client: Cliente del puente opcional
        """
        self.bridge_client = bridge_client or get_bridge_client()
        self.config = get_dracmas_config()
        logger.info("🔗 QuantumIntegrationManager initialized")

    async def generate_training_proof(
        self,
        node_id: str,
        dataset_id: str,
        compute_power: int,
        model_weights: bytes,
        training_metrics: Dict[str, Any],
        quantum_entropy: Optional[bytes] = None
    ) -> TrainingProof:
        """
        Generar proof de entrenamiento compatible con contrato DracmaS.

        Args:
            node_id: ID del nodo
            dataset_id: ID del dataset
            compute_power: Poder computacional usado
            model_weights: Pesos del modelo entrenado (bytes)
            training_metrics: Métricas de entrenamiento
            quantum_entropy: Entropía cuántica opcional

        Returns:
            Proof de entrenamiento generado

        Raises:
            QuantumIntegrationError: Si hay error en generación
        """
        try:
            # Validar parámetros
            self._validate_proof_inputs(node_id, dataset_id, compute_power, model_weights)

            logger.info(f"🔬 Generating training proof for node {node_id} on dataset {dataset_id}")

            # Calcular hash del modelo
            model_hash = hashlib.sha256(model_weights).hexdigest()

            # Extraer precisión esperada de métricas
            expected_accuracy = self._extract_expected_accuracy(training_metrics)

            # Generar proof data (simulado - en producción usaría algoritmos cuánticos)
            proof_data = self._generate_proof_data(
                node_id, dataset_id, compute_power, model_weights,
                training_metrics, quantum_entropy
            )

            # Crear firma cuántica (simulada)
            quantum_signature = self._generate_quantum_signature(proof_data)

            proof = TrainingProof(
                node_id=node_id,
                dataset_id=dataset_id,
                compute_power=compute_power,
                proof_data=proof_data,
                model_hash=model_hash,
                expected_accuracy=expected_accuracy,
                timestamp=int(time.time()),
                quantum_signature=quantum_signature
            )

            logger.info(f"✅ Training proof generated for node {node_id}")
            return proof

        except Exception as e:
            logger.error(f"❌ Error generating training proof for node {node_id}: {e}")
            raise QuantumIntegrationError(f"Proof generation error: {e}")

    async def validate_training_locally(
        self,
        proof: TrainingProof,
        validation_params: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validar proof de entrenamiento localmente antes de enviar.

        Args:
            proof: Proof a validar
            validation_params: Parámetros de validación opcionales

        Returns:
            Resultado de la validación local

        Raises:
            QuantumIntegrationError: Si hay error en validación
        """
        try:
            logger.info(f"🔍 Performing local validation for proof of node {proof.node_id}")

            # Validar estructura del proof
            self._validate_proof_structure(proof)

            # Realizar validaciones locales
            validation_errors = []
            confidence_score = 1.0

            # Validar hash del modelo
            if not self._validate_model_hash(proof):
                validation_errors.append("Model hash validation failed")
                confidence_score *= 0.5

            # Validar firma cuántica
            if not self._validate_quantum_signature(proof):
                validation_errors.append("Quantum signature validation failed")
                confidence_score *= 0.7

            # Validar coherencia de datos
            if not self._validate_proof_coherence(proof):
                validation_errors.append("Proof coherence validation failed")
                confidence_score *= 0.8

            # Validar parámetros adicionales si se proporcionan
            if validation_params:
                param_validation = self._validate_additional_params(proof, validation_params)
                if not param_validation['valid']:
                    validation_errors.extend(param_validation['errors'])
                    confidence_score *= 0.9

            # Calcular hash de validación
            validation_hash = self._calculate_validation_hash(proof, confidence_score)

            is_valid = len(validation_errors) == 0 and confidence_score >= 0.8

            result = ValidationResult(
                is_valid=is_valid,
                confidence_score=confidence_score,
                validation_hash=validation_hash,
                errors=validation_errors if validation_errors else None
            )

            if is_valid:
                logger.info(f"✅ Local validation passed for node {proof.node_id} (confidence: {confidence_score:.2f})")
            else:
                logger.warning(f"⚠️ Local validation failed for node {proof.node_id}: {validation_errors}")

            return result

        except Exception as e:
            logger.error(f"❌ Error in local validation for node {proof.node_id}: {e}")
            raise QuantumIntegrationError(f"Local validation error: {e}")

    async def submit_validated_work(
        self,
        proof: TrainingProof,
        validation_result: ValidationResult,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Enviar trabajo validado al puente para validación final.

        Args:
            proof: Proof validado
            validation_result: Resultado de validación local
            additional_data: Datos adicionales opcionales

        Returns:
            Resultado del envío

        Raises:
            QuantumIntegrationError: Si hay error en envío
        """
        try:
            # Verificar que la validación local fue exitosa
            if not validation_result.is_valid:
                raise QuantumIntegrationError("Cannot submit work with failed local validation")

            logger.info(f"📤 Submitting validated work for node {proof.node_id} to bridge")

            # Preparar datos para envío
            submission_data = {
                "proof": proof,
                "validation_result": validation_result,
                "additional_data": additional_data or {},
                "submission_timestamp": int(time.time())
            }

            # Enviar vía puente usando validate_proof
            result = await self.bridge_client.validate_proof(
                node_id=proof.node_id,
                dataset_id=proof.dataset_id,
                compute_power=proof.compute_power,
                proof=proof.proof_data,
                model_hash=proof.model_hash,
                expected_accuracy=proof.expected_accuracy
            )

            if result.get('success'):
                logger.info(f"✅ Validated work submitted successfully for node {proof.node_id}")

                return {
                    "success": True,
                    "submission_data": submission_data,
                    "bridge_result": result,
                    "message": "Validated work submitted to bridge successfully"
                }
            else:
                error_msg = result.get('error', 'Bridge validation failed')
                logger.error(f"❌ Bridge validation failed for node {proof.node_id}: {error_msg}")
                raise QuantumIntegrationError(f"Bridge validation failed: {error_msg}")

        except BridgeClientError as e:
            logger.error(f"❌ Bridge error submitting validated work for node {proof.node_id}: {e}")
            raise QuantumIntegrationError(f"Bridge communication error: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error submitting validated work for node {proof.node_id}: {e}")
            raise QuantumIntegrationError(f"Unexpected error: {e}")

    def _validate_proof_inputs(self, node_id: str, dataset_id: str, compute_power: int, model_weights: bytes):
        """Validar entradas para generación de proof."""
        if not isinstance(node_id, str) or not node_id.strip():
            raise QuantumIntegrationError("Node ID must be a non-empty string")
        if not isinstance(dataset_id, str) or not dataset_id.strip():
            raise QuantumIntegrationError("Dataset ID must be a non-empty string")
        if not isinstance(compute_power, int) or compute_power <= 0:
            raise QuantumIntegrationError("Compute power must be a positive integer")
        if not isinstance(model_weights, bytes) or len(model_weights) == 0:
            raise QuantumIntegrationError("Model weights must be non-empty bytes")

    def _extract_expected_accuracy(self, training_metrics: Dict[str, Any]) -> str:
        """Extraer precisión esperada de métricas de entrenamiento."""
        accuracy = training_metrics.get('accuracy', training_metrics.get('val_accuracy', 0.0))
        return f"{accuracy:.4f}"

    def _generate_proof_data(
        self,
        node_id: str,
        dataset_id: str,
        compute_power: int,
        model_weights: bytes,
        training_metrics: Dict[str, Any],
        quantum_entropy: Optional[bytes]
    ) -> bytes:
        """Generar datos del proof (simulado)."""
        proof_dict = {
            "node_id": node_id,
            "dataset_id": dataset_id,
            "compute_power": compute_power,
            "model_hash": hashlib.sha256(model_weights).hexdigest(),
            "training_metrics": training_metrics,
            "timestamp": int(time.time()),
            "quantum_entropy": quantum_entropy.hex() if quantum_entropy else None
        }

        proof_json = json.dumps(proof_dict, sort_keys=True)
        return proof_json.encode('utf-8')

    def _generate_quantum_signature(self, proof_data: bytes) -> str:
        """Generar firma cuántica (simulada)."""
        # En producción, esto usaría algoritmos cuánticos reales
        signature_data = hashlib.sha256(proof_data + b"quantum_salt").hexdigest()
        return f"quantum_sig_{signature_data[:32]}"

    def _validate_proof_structure(self, proof: TrainingProof):
        """Validar estructura del proof."""
        if not proof.node_id or not proof.dataset_id:
            raise QuantumIntegrationError("Proof missing required fields")
        if proof.compute_power <= 0:
            raise QuantumIntegrationError("Invalid compute power in proof")
        if not proof.proof_data:
            raise QuantumIntegrationError("Proof data is empty")

    def _validate_model_hash(self, proof: TrainingProof) -> bool:
        """Validar hash del modelo."""
        # Simular validación - en producción sería más compleja
        return len(proof.model_hash) == 64 and proof.model_hash.isalnum()

    def _validate_quantum_signature(self, proof: TrainingProof) -> bool:
        """Validar firma cuántica."""
        # Simular validación
        return proof.quantum_signature and proof.quantum_signature.startswith("quantum_sig_")

    def _validate_proof_coherence(self, proof: TrainingProof) -> bool:
        """Validar coherencia del proof."""
        # Verificar que los datos sean consistentes
        try:
            proof_dict = json.loads(proof.proof_data.decode('utf-8'))
            return (
                proof_dict.get('node_id') == proof.node_id and
                proof_dict.get('dataset_id') == proof.dataset_id and
                proof_dict.get('compute_power') == proof.compute_power
            )
        except:
            return False

    def _validate_additional_params(self, proof: TrainingProof, validation_params: Dict[str, Any]) -> Dict[str, Any]:
        """Validar parámetros adicionales."""
        errors = []
        # Implementar validaciones específicas según parámetros
        return {"valid": len(errors) == 0, "errors": errors}

    def _calculate_validation_hash(self, proof: TrainingProof, confidence_score: float) -> str:
        """Calcular hash de validación."""
        hash_data = f"{proof.node_id}{proof.dataset_id}{proof.compute_power}{confidence_score}{proof.timestamp}"
        return hashlib.sha256(hash_data.encode()).hexdigest()


# Instancia global del gestor
_quantum_integration_manager: Optional[QuantumIntegrationManager] = None


def get_quantum_integration_manager() -> QuantumIntegrationManager:
    """Obtener instancia global del gestor de integración cuántica."""
    global _quantum_integration_manager
    if _quantum_integration_manager is None:
        _quantum_integration_manager = QuantumIntegrationManager()
    return _quantum_integration_manager


def create_quantum_integration_manager(bridge_client: Optional[BridgeClient] = None) -> QuantumIntegrationManager:
    """Crear nueva instancia del gestor de integración cuántica."""
    return QuantumIntegrationManager(bridge_client)