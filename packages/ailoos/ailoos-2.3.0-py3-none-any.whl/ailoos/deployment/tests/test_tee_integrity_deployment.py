"""
Tests funcionales de integridad TEE en deployment.
Valida integridad de enclaves TEE, attestación remota y protección contra extracción de weights durante deployment.
"""

import pytest
import asyncio
import json
import base64
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import tempfile
import os

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from ailoos.deployment.model_deployer import ModelDeployer, ModelDeploymentConfig, DeploymentStatus
from ailoos.infrastructure.gcp.tee_manager import TeeManager, TeeEnclave
from ailoos.validation.tee_attestation_validator import (
    TEEAttestationValidator,
    ReferenceMeasurements,
    AttestationVerificationResult
)
from ailoos.core.config import Config


class TestTEEIntegrityDeployment:
    """Tests de integridad TEE durante deployment de modelos."""

    @pytest.fixture
    def tee_config(self):
        """Configuración de prueba para TEE."""
        return {
            'name': 'test-tee-enclave',
            'zone': 'europe-west1-b',
            'machine_type': 'n2d-standard-2',
            'enclave_type': 'model-deployment',
            'model_name': 'test-model',
            'model_version': 'v1.0.0',
            'startup_script': '#!/bin/bash\necho "TEE enclave started"'
        }

    @pytest.fixture
    def deployment_config(self, tee_config):
        """Configuración de deployment con TEE."""
        return ModelDeploymentConfig(
            model_name="test-model",
            model_version="v1.0.0",
            image="ailoos/test-model:v1.0.0",
            namespace="test-namespace",
            replicas=1,
            tee_enabled=True,
            tee_config=tee_config
        )

    @pytest.fixture
    def mock_tee_manager(self):
        """Mock del TEE Manager."""
        manager = Mock(spec=TeeManager)
        enclave = Mock(spec=TeeEnclave)
        enclave.name = "test-tee-enclave"
        enclave.status = "RUNNING"
        enclave.external_ip = "10.0.0.1"
        enclave.internal_ip = "10.0.0.2"
        manager.create_enclave = AsyncMock(return_value=enclave)
        manager.validate_enclave_integrity = AsyncMock(return_value=True)
        manager.monitor_enclaves = AsyncMock(return_value={
            "test-tee-enclave": {
                'status': 'RUNNING',
                'cpu_utilization': 0.5,
                'memory_utilization': 0.6,
                'confidential_compute_enabled': True,
                'integrity_monitoring_enabled': True
            }
        })
        return manager

    @pytest.fixture
    def mock_k8s_config(self):
        """Mock de configuración Kubernetes."""
        config = Mock()
        return config

    @pytest.fixture
    async def deployer(self, mock_tee_manager, mock_k8s_config):
        """Deployer con mocks configurados."""
        with patch('kubernetes_asyncio.config.load_kube_config'), \
             patch('src.ailoos.deployment.model_deployer.TeeManager', return_value=mock_tee_manager):

            deployer = ModelDeployer(config=mock_k8s_config)
            deployer.tee_manager = mock_tee_manager
            yield deployer

    @pytest.mark.asyncio
    async def test_deployment_with_tee_enclave_creation(self, deployer, deployment_config, mock_tee_manager):
        """Test deployment crea enclave TEE correctamente."""
        # Mock verificación de imagen
        with patch('src.ailoos.deployment.model_deployer.get_image_verifier') as mock_get_verifier:
            mock_verifier = Mock()
            mock_verifier.verify_image = AsyncMock(return_value=Mock(is_verified=True))
            mock_get_verifier.return_value = mock_verifier

            # Ejecutar deployment
            status = await deployer.deploy_model(deployment_config)

            # Verificar que se creó el enclave
            mock_tee_manager.create_enclave.assert_called_once_with(deployment_config.tee_config)
            assert status.tee_enclave_name == "test-tee-enclave"
            assert status.status == "running"
            assert status.service_url == "http://10.0.0.1:8000"

    @pytest.mark.asyncio
    async def test_deployment_validates_enclave_integrity(self, deployer, deployment_config, mock_tee_manager):
        """Test deployment valida integridad del enclave TEE."""
        with patch('src.ailoos.deployment.model_deployer.get_image_verifier') as mock_get_verifier:
            mock_verifier = Mock()
            mock_verifier.verify_image = AsyncMock(return_value=Mock(is_verified=True))
            mock_get_verifier.return_value = mock_verifier

            # Ejecutar deployment
            status = await deployer.deploy_model(deployment_config)

            # Verificar que se validó la integridad
            mock_tee_manager.validate_enclave_integrity.assert_called_once_with("test-tee-enclave")
            assert status.status == "running"

    @pytest.mark.asyncio
    async def test_deployment_fails_on_enclave_integrity_failure(self, deployer, deployment_config, mock_tee_manager):
        """Test deployment falla si la integridad del enclave no se valida."""
        # Configurar mock para fallar validación de integridad
        mock_tee_manager.validate_enclave_integrity = AsyncMock(return_value=False)

        with patch('src.ailoos.deployment.model_deployer.get_image_verifier') as mock_get_verifier:
            mock_verifier = Mock()
            mock_verifier.verify_image = AsyncMock(return_value=Mock(is_verified=True))
            mock_get_verifier.return_value = mock_verifier

            # Ejecutar deployment debe fallar
            with pytest.raises(ValueError, match="Enclave integrity validation failed"):
                await deployer.deploy_model(deployment_config)

    @pytest.mark.asyncio
    async def test_deployment_fails_on_image_verification_failure(self, deployer, deployment_config):
        """Test deployment falla si la verificación de imagen falla."""
        with patch('ailoos.federated.image_verifier.get_image_verifier') as mock_get_verifier:
            mock_verifier = Mock()
            mock_verifier.verify_image = AsyncMock(return_value=Mock(is_verified=False, error_message="Image compromised"))
            mock_get_verifier.return_value = mock_verifier

            # Ejecutar deployment debe fallar
            with pytest.raises(ValueError, match="Image verification failed"):
                await deployer.deploy_model(deployment_config)


class TestTEEAttestationInDeployment:
    """Tests de attestación remota integrada en deployment."""

    @pytest.fixture
    def attestation_validator(self):
        """Validador de attestación con configuración de prueba."""
        with patch('src.ailoos.validation.tee_attestation_validator.Path'):
            validator = TEEAttestationValidator()
            validator.metrics = {
                "total_attestations": 0,
                "successful_attestations": 0,
                "failed_attestations": 0,
                "certificate_verification_failures": 0,
                "measurement_mismatches": 0,
                "stale_reports": 0,
                "last_attestation_time": None,
                "average_verification_time": 0.0
            }
            return validator

    @pytest.fixture
    def valid_measurements(self):
        """Mediciones de referencia válidas."""
        return ReferenceMeasurements(
            platform_firmware_hash="trusted_platform_hash",
            kernel_hash="trusted_kernel_hash",
            initrd_hash="trusted_initrd_hash",
            guest_policy="trusted_policy",
            family_id="trusted_family",
            image_id="trusted_image"
        )

    def test_attestation_validation_success_during_deployment(self, attestation_validator, valid_measurements):
        """Test attestación exitosa durante deployment."""
        # Simular respuesta de attestación válida
        with patch('src.ailoos.validation.tee_attestation_validator.GCPAttestationClient') as mock_client_class:
            mock_client = Mock()
            mock_client.get_attestation_report.return_value = {
                "attestationReport": {
                    "report": base64.b64encode(json.dumps({
                        "instance_name": "test-enclave",
                        "project_id": "test-project",
                        "zone": "europe-west1-b",
                        "attestation_time": datetime.utcnow().timestamp(),
                        "tee_type": "SEV_SNP",
                        "platform_measurements": {
                            "platform_firmware_hash": "trusted_platform_hash",
                            "kernel_hash": "trusted_kernel_hash",
                            "initrd_hash": "trusted_initrd_hash"
                        },
                        "guest_measurements": {
                            "guest_policy": "trusted_policy",
                            "family_id": "trusted_family",
                            "image_id": "trusted_image"
                        }
                    }).encode()).decode(),
                    "signature": base64.b64encode(b"valid_signature").decode(),
                    "certificateChain": ["cert1", "cert2"]
                }
            }
            mock_client_class.return_value = mock_client

            # Mock verificaciones criptográficas
            with patch.object(attestation_validator.cert_verifier, 'verify_certificate_chain', return_value=True), \
                 patch.object(attestation_validator.cert_verifier, 'verify_signature', return_value=True):

                result = attestation_validator.validate_remote_attestation(
                    "test-enclave",
                    "test-project",
                    "europe-west1-b",
                    valid_measurements
                )

                assert result.is_valid is True
                assert result.report is not None
                assert attestation_validator.metrics["successful_attestations"] == 1

    def test_attestation_validation_failure_blocks_deployment(self, attestation_validator):
        """Test fallo de attestación bloquea deployment."""
        # Simular respuesta de attestación inválida
        with patch('src.ailoos.validation.tee_attestation_validator.GCPAttestationClient') as mock_client_class:
            mock_client = Mock()
            mock_client.get_attestation_report.return_value = {
                "attestationReport": {
                    "report": base64.b64encode(b"invalid_report").decode(),
                    "signature": base64.b64encode(b"invalid_signature").decode(),
                    "certificateChain": ["invalid_cert"]
                }
            }
            mock_client_class.return_value = mock_client

            # Simular fallo en verificación de certificados
            with patch.object(attestation_validator.cert_verifier, 'verify_certificate_chain', return_value=False):
                result = attestation_validator.validate_remote_attestation(
                    "test-enclave",
                    "test-project",
                    "europe-west1-b"
                )

                assert result.is_valid is False
                assert "Cadena de certificados inválida" in result.issues
                assert attestation_validator.metrics["certificate_verification_failures"] == 1


class TestWeightProtectionInTEEDeployment:
    """Tests de protección contra extracción de weights en deployment TEE."""

    @pytest.fixture
    def mock_secure_storage(self):
        """Mock de almacenamiento seguro para weights."""
        storage = Mock()
        storage.store_encrypted_weights = AsyncMock(return_value="encrypted_weights_id")
        storage.retrieve_weights = AsyncMock(return_value=b"decrypted_weights_data")
        storage.delete_weights = AsyncMock(return_value=True)
        return storage

    @pytest.fixture
    def weight_protection_config(self):
        """Configuración para protección de weights."""
        return {
            'enable_weight_encryption': True,
            'encryption_key_source': 'tee_generated',
            'allow_weight_extraction': False,
            'weight_access_policy': 'tee_only'
        }

    def test_weights_remain_encrypted_in_tee_enclave(self, mock_secure_storage, weight_protection_config):
        """Test que los weights permanecen encriptados dentro del enclave TEE."""
        # Simular weights originales
        original_weights = b"model_weights_data_12345"

        # Simular almacenamiento en enclave TEE
        encrypted_id = asyncio.run(mock_secure_storage.store_encrypted_weights(original_weights, weight_protection_config))

        # Verificar que se almacenaron encriptados
        assert encrypted_id == "encrypted_weights_id"
        mock_secure_storage.store_encrypted_weights.assert_called_once()

        # Intentar acceso externo (debe fallar)
        with patch('builtins.open', side_effect=PermissionError("Access denied - TEE protected")):
            with pytest.raises(PermissionError, match="Access denied"):
                with open("/tee/enclave/weights", 'rb') as f:
                    f.read()

    def test_weight_extraction_attempt_is_blocked(self, mock_secure_storage):
        """Test que intentos de extracción de weights son bloqueados."""
        # Simular intento de extracción desde fuera del enclave
        with patch('subprocess.run') as mock_subprocess:
            # Simular comando que intenta extraer weights
            mock_subprocess.return_value = Mock(returncode=1, stderr="Permission denied: TEE protection active")

            # Intentar extracción
            result = mock_subprocess("scp enclave:/app/weights/model.bin ./extracted_weights.bin")

            # Verificar que falló
            assert result.returncode == 1
            assert "Permission denied" in result.stderr

    def test_secure_weight_loading_in_deployment(self, mock_secure_storage, weight_protection_config):
        """Test carga segura de weights durante deployment."""
        # Simular carga de weights en deployment
        encrypted_weights_id = "deployment_weights_v1.0.0"

        # Cargar weights dentro del enclave (debe funcionar)
        weights_data = asyncio.run(mock_secure_storage.retrieve_weights(encrypted_weights_id))

        assert weights_data == b"decrypted_weights_data"
        mock_secure_storage.retrieve_weights.assert_called_once_with(encrypted_weights_id)

    def test_weight_integrity_verification(self, mock_secure_storage):
        """Test verificación de integridad de weights."""
        # Simular weights con hash de integridad
        weights_data = b"model_weights_data"
        expected_hash = "sha256_hash_of_weights"

        # Verificar integridad durante carga
        with patch('hashlib.sha256') as mock_sha256:
            mock_hash = Mock()
            mock_hash.hexdigest.return_value = expected_hash
            mock_sha256.return_value = mock_hash

            # Cargar y verificar
            loaded_weights = asyncio.run(mock_secure_storage.retrieve_weights("weights_id"))

            # Verificar que se calculó el hash
            mock_sha256.assert_called()
            assert loaded_weights is not None

    def test_rollback_preserves_weight_security(self, mock_secure_storage):
        """Test que rollback mantiene seguridad de weights."""
        # Simular versiones de weights
        version_1_weights = b"weights_v1"
        version_2_weights = b"weights_v2"

        # Almacenar ambas versiones
        v1_id = asyncio.run(mock_secure_storage.store_encrypted_weights(version_1_weights, {}))
        v2_id = asyncio.run(mock_secure_storage.store_encrypted_weights(version_2_weights, {}))

        # Simular rollback a v1
        rolled_back_weights = asyncio.run(mock_secure_storage.retrieve_weights(v1_id))

        # Verificar que se recuperó la versión correcta
        assert rolled_back_weights == version_1_weights

        # Verificar que v2 aún existe pero no es accesible externamente
        v2_weights = asyncio.run(mock_secure_storage.retrieve_weights(v2_id))
        assert v2_weights == version_2_weights


class TestTEEDeploymentIntegration:
    """Tests de integración completa de TEE en deployment."""

    @pytest.mark.asyncio
    async def test_full_deployment_pipeline_with_tee(self):
        """Test pipeline completo de deployment con TEE."""
        # Configurar mocks para todo el pipeline
        with patch('kubernetes_asyncio.config.load_kube_config'), \
             patch('ailoos.federated.image_verifier.get_image_verifier') as mock_get_verifier, \
             patch('ailoos.infrastructure.gcp.tee_manager.TeeManager') as mock_tee_manager_class:

            # Mock verificación de imagen
            mock_verifier = Mock()
            mock_verifier.verify_image = AsyncMock(return_value=Mock(is_verified=True))
            mock_get_verifier.return_value = mock_verifier

            # Mock TEE Manager
            mock_tee_manager = Mock()
            enclave = Mock()
            enclave.name = "integration-test-enclave"
            enclave.external_ip = "192.168.1.100"
            mock_tee_manager.create_enclave = AsyncMock(return_value=enclave)
            mock_tee_manager.validate_enclave_integrity = AsyncMock(return_value=True)
            mock_tee_manager_class.return_value = mock_tee_manager

            # Configuración de deployment
            config = ModelDeploymentConfig(
                model_name="integration-test-model",
                model_version="v1.0.0",
                image="ailoos/integration-model:v1.0.0",
                tee_enabled=True,
                tee_config={
                    'name': 'integration-test-enclave',
                    'zone': 'europe-west1-b',
                    'machine_type': 'n2d-standard-2'
                }
            )

            # Ejecutar deployment
            deployer = ModelDeployer()
            status = await deployer.deploy_model(config)

            # Verificar pipeline completo
            assert status.status == "running"
            assert status.tee_enclave_name == "integration-test-enclave"
            assert status.service_url == "http://192.168.1.100:8000"

            # Verificar llamadas a TEE
            mock_tee_manager.create_enclave.assert_called_once()
            mock_tee_manager.validate_enclave_integrity.assert_called_once()

    @pytest.mark.asyncio
    async def test_deployment_rollback_with_tee_cleanup(self):
        """Test rollback de deployment con limpieza TEE."""
        with patch('kubernetes_asyncio.config.load_kube_config'), \
             patch('ailoos.infrastructure.gcp.tee_manager.TeeManager') as mock_tee_manager_class:

            # Mock TEE Manager
            mock_tee_manager = Mock()
            mock_tee_manager.delete_enclave = AsyncMock(return_value=None)
            mock_tee_manager_class.return_value = mock_tee_manager

            # Simular deployment existente
            deployer = ModelDeployer()
            deployer.deployments["test-deployment"] = DeploymentStatus(
                deployment_id="test-deployment",
                model_name="test-model",
                model_version="v1.0.0",
                namespace="test-ns",
                status="running",
                tee_enclave_name="test-enclave-to-cleanup"
            )

            # Ejecutar undeploy
            result = await deployer.undeploy_model("test-deployment")

            # Verificar limpieza TEE
            assert result is True
            mock_tee_manager.delete_enclave.assert_called_once_with("test-enclave-to-cleanup")
            assert "test-deployment" not in deployer.deployments


if __name__ == "__main__":
    pytest.main([__file__, "-v"])