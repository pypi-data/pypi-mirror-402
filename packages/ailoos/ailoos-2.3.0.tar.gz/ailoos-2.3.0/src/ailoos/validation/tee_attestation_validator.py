"""
Validador de attestación remota para enclaves TEE en GCP Confidential Computing.
Implementa verificación de integridad de enclaves usando certificados de attestación de GCP.
"""

import base64
import hashlib
import json
import time
import os
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import requests
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature

from ..core.logging import get_logger
from ..core.config import get_config

logger = get_logger(__name__)


@dataclass
class AttestationReport:
    """Reporte de attestación de GCP Confidential Computing."""
    instance_name: str
    project_id: str
    zone: str
    attestation_time: datetime
    tee_type: str  # "SEV_SNP" para AMD SEV-SNP
    platform_measurements: Dict[str, Any]
    guest_measurements: Dict[str, Any]
    signature: str
    certificate_chain: List[str]
    raw_report: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AttestationVerificationResult:
    """Resultado de verificación de attestación."""
    is_valid: bool
    report: Optional[AttestationReport] = None
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReferenceMeasurements:
    """Mediciones de referencia para verificación."""
    platform_firmware_hash: str
    kernel_hash: str
    initrd_hash: str
    guest_policy: str
    family_id: Optional[str] = None
    image_id: Optional[str] = None
    launch_measurement: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class GCPAttestationClient:
    """
    Cliente para obtener reportes de attestación de GCP Confidential Computing.
    """

    def __init__(self, project_id: str, zone: str):
        self.project_id = project_id
        self.zone = zone
        self.base_url = "https://compute.googleapis.com/compute/v1"
        self.metadata_url = "http://metadata.google.internal/computeMetadata/v1"

    def get_attestation_report(self, instance_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el reporte de attestación de una instancia confidencial.

        Args:
            instance_name: Nombre de la instancia

        Returns:
            Reporte de attestación en formato dict o None si falla
        """
        try:
            # URL para obtener el reporte de attestación
            url = f"{self.base_url}/projects/{self.project_id}/zones/{self.zone}/instances/{instance_name}/getShieldedVmIdentity"

            # En un entorno real, esto requeriría autenticación con GCP
            # Por ahora, simulamos la respuesta
            logger.info(f"Obteniendo reporte de attestación para instancia: {instance_name}")

            # Simulación de respuesta de GCP
            return self._simulate_attestation_report(instance_name)

        except Exception as e:
            logger.error(f"Error obteniendo reporte de attestación: {e}")
            return None

    def _simulate_attestation_report(self, instance_name: str) -> Dict[str, Any]:
        """
        Simula un reporte de attestación de GCP (para desarrollo/testing).
        En producción, esto vendría de la API real de GCP.
        """
        current_time = int(time.time())

        return {
            "kind": "compute#shieldedVmIdentity",
            "signingKey": {
                "ekCert": base64.b64encode(b"simulated_ek_cert").decode(),
                "ekPub": base64.b64encode(b"simulated_ek_pub").decode()
            },
            "attestationReport": {
                "report": base64.b64encode(json.dumps({
                    "instance_name": instance_name,
                    "project_id": self.project_id,
                    "zone": self.zone,
                    "attestation_time": current_time,
                    "tee_type": "SEV_SNP",
                    "platform_measurements": {
                        "platform_firmware_hash": "a1b2c3d4e5f6...",
                        "kernel_hash": "f6e5d4c3b2a1...",
                        "initrd_hash": "1a2b3c4d5e6f..."
                    },
                    "guest_measurements": {
                        "guest_policy": "010203040506...",
                        "family_id": "family123",
                        "image_id": "image456",
                        "launch_measurement": "launch789"
                    }
                }).encode()).decode(),
                "signature": base64.b64encode(b"simulated_signature").decode(),
                "certificateChain": [
                    base64.b64encode(b"cert1").decode(),
                    base64.b64encode(b"cert2").decode()
                ]
            }
        }


class CertificateVerifier:
    """
    Verificador de certificados para attestación de GCP.
    """

    # Certificados raíz de GCP para Confidential Computing
    GCP_ROOT_CERTS = [
        # En producción, estos serían los certificados reales de GCP
        "simulated_gcp_root_cert"
    ]

    def verify_certificate_chain(self, certificate_chain: List[str]) -> bool:
        """
        Verifica la cadena de certificados del reporte de attestación.

        Args:
            certificate_chain: Lista de certificados en base64

        Returns:
            True si la cadena es válida
        """
        try:
            # Decodificar certificados
            certs = []
            for cert_b64 in certificate_chain:
                cert_der = base64.b64decode(cert_b64)
                cert = x509.load_der_x509_certificate(cert_der, default_backend())
                certs.append(cert)

            # Verificar cadena de confianza
            # En producción, verificar contra certificados raíz de GCP
            for i in range(len(certs) - 1):
                # Verificar firma del certificado actual con el siguiente
                public_key = certs[i + 1].public_key()
                public_key.verify(
                    certs[i].signature,
                    certs[i].tbs_certificate_bytes,
                    padding.PKCS1v15(),
                    certs[i].signature_hash_algorithm
                )

            logger.info("Cadena de certificados verificada correctamente")
            return True

        except (InvalidSignature, Exception) as e:
            logger.error(f"Error verificando cadena de certificados: {e}")
            return False

    def verify_signature(self, data: bytes, signature: bytes, certificate: str) -> bool:
        """
        Verifica la firma del reporte usando el certificado.

        Args:
            data: Datos firmados
            signature: Firma en bytes
            certificate: Certificado en base64

        Returns:
            True si la firma es válida
        """
        try:
            cert_der = base64.b64decode(certificate)
            cert = x509.load_der_x509_certificate(cert_der, default_backend())
            public_key = cert.public_key()

            public_key.verify(
                signature,
                data,
                padding.PKCS1v15(),
                hashes.SHA256()
            )

            logger.info("Firma del reporte verificada correctamente")
            return True

        except (InvalidSignature, Exception) as e:
            logger.error(f"Error verificando firma: {e}")
            return False


class TEEAttestationValidator:
    """
    Validador principal de attestación remota para enclaves TEE.
    """

    def __init__(self):
        self.config = get_config()
        self.cert_verifier = CertificateVerifier()
        self.reference_measurements_file = Path("./data/tee_reference_measurements.json")
        self.reference_measurements_file.parent.mkdir(parents=True, exist_ok=True)
        self.reference_measurements = self._load_reference_measurements()

        # Métricas de monitoreo
        self.metrics = {
            "total_attestations": 0,
            "successful_attestations": 0,
            "failed_attestations": 0,
            "certificate_verification_failures": 0,
            "measurement_mismatches": 0,
            "stale_reports": 0,
            "last_attestation_time": None,
            "average_verification_time": 0.0
        }

    def _load_reference_measurements(self) -> Dict[str, ReferenceMeasurements]:
        """
        Carga las mediciones de referencia desde archivo JSON persistente.
        """
        try:
            if self.reference_measurements_file.exists():
                with open(self.reference_measurements_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                measurements = {}
                for key, measurement_data in data.items():
                    measurements[key] = ReferenceMeasurements(
                        platform_firmware_hash=measurement_data["platform_firmware_hash"],
                        kernel_hash=measurement_data["kernel_hash"],
                        initrd_hash=measurement_data["initrd_hash"],
                        guest_policy=measurement_data["guest_policy"],
                        family_id=measurement_data.get("family_id"),
                        image_id=measurement_data.get("image_id"),
                        launch_measurement=measurement_data.get("launch_measurement"),
                        created_at=datetime.fromisoformat(measurement_data["created_at"]),
                        updated_at=datetime.fromisoformat(measurement_data["updated_at"])
                    )

                logger.info(f"Cargadas {len(measurements)} mediciones de referencia desde {self.reference_measurements_file}")
                return measurements
            else:
                # Crear mediciones por defecto si no existe el archivo
                logger.info("Creando mediciones de referencia por defecto")
                return {
                    "default": ReferenceMeasurements(
                        platform_firmware_hash="expected_platform_hash",
                        kernel_hash="expected_kernel_hash",
                        initrd_hash="expected_initrd_hash",
                        guest_policy="expected_policy",
                        family_id="expected_family",
                        image_id="expected_image"
                    )
                }

        except Exception as e:
            logger.error(f"Error cargando mediciones de referencia: {e}")
            # Fallback a mediciones por defecto
            return {
                "default": ReferenceMeasurements(
                    platform_firmware_hash="expected_platform_hash",
                    kernel_hash="expected_kernel_hash",
                    initrd_hash="expected_initrd_hash",
                    guest_policy="expected_policy",
                    family_id="expected_family",
                    image_id="expected_image"
                )
            }

    def validate_remote_attestation(
        self,
        instance_name: str,
        project_id: str,
        zone: str,
        expected_measurements: Optional[ReferenceMeasurements] = None
    ) -> AttestationVerificationResult:
        """
        Realiza attestación remota completa de un enclave TEE.

        Args:
            instance_name: Nombre de la instancia
            project_id: ID del proyecto GCP
            zone: Zona de GCP
            expected_measurements: Mediciones esperadas (opcional)

        Returns:
            Resultado de la verificación
        """
        start_time = time.time()
        result = AttestationVerificationResult(is_valid=False)

        # Actualizar métricas
        self.metrics["total_attestations"] += 1

        try:
            # 1. Obtener reporte de attestación
            client = GCPAttestationClient(project_id, zone)
            raw_report = client.get_attestation_report(instance_name)

            if not raw_report:
                result.issues.append("No se pudo obtener el reporte de attestación")
                return result

            # 2. Parsear y validar el reporte
            attestation_report = self._parse_attestation_report(raw_report)
            if not attestation_report:
                result.issues.append("Error parseando el reporte de attestación")
                return result

            result.report = attestation_report

            # 3. Verificar cadena de certificados
            if not self.cert_verifier.verify_certificate_chain(attestation_report.certificate_chain):
                result.issues.append("Cadena de certificados inválida")
                self.metrics["certificate_verification_failures"] += 1
                return result

            # 4. Verificar firma del reporte
            report_data = json.dumps(attestation_report.raw_report, sort_keys=True).encode()
            signature = base64.b64decode(attestation_report.signature)

            if not self.cert_verifier.verify_signature(
                report_data,
                signature,
                attestation_report.certificate_chain[0]  # Certificado hoja
            ):
                result.issues.append("Firma del reporte inválida")
                self.metrics["certificate_verification_failures"] += 1
                return result

            # 5. Verificar mediciones contra referencias
            measurements_result = self._verify_measurements(
                attestation_report,
                expected_measurements or self.reference_measurements.get("default")
            )

            if not measurements_result[0]:
                result.issues.extend(measurements_result[1])
                self.metrics["measurement_mismatches"] += 1
                return result

            # 6. Verificar tiempo de attestación (no demasiado antiguo)
            if self._is_attestation_too_old(attestation_report.attestation_time):
                result.warnings.append("El reporte de attestación es antiguo")
                self.metrics["stale_reports"] += 1

            # 7. Metadata adicional
            result.metadata = {
                "instance_name": instance_name,
                "project_id": project_id,
                "zone": zone,
                "attestation_time": attestation_report.attestation_time.isoformat(),
                "tee_type": attestation_report.tee_type,
                "verification_time": datetime.utcnow().isoformat()
            }

            result.is_valid = True
            self.metrics["successful_attestations"] += 1
            self.metrics["last_attestation_time"] = datetime.utcnow().isoformat()

            # Calcular tiempo promedio de verificación
            verification_time = time.time() - start_time
            self.metrics["average_verification_time"] = (
                (self.metrics["average_verification_time"] * (self.metrics["total_attestations"] - 1)) +
                verification_time
            ) / self.metrics["total_attestations"]

            logger.info(f"Attestación remota exitosa para instancia: {instance_name}")

        except Exception as e:
            logger.error(f"Error en attestación remota: {e}")
            result.issues.append(f"Error interno: {str(e)}")
            self.metrics["failed_attestations"] += 1

        return result

    def _parse_attestation_report(self, raw_report: Dict[str, Any]) -> Optional[AttestationReport]:
        """
        Parsea el reporte de attestación crudo en un objeto AttestationReport.
        """
        try:
            attestation_data = raw_report.get("attestationReport", {})
            report_b64 = attestation_data.get("report", "")
            report_json = base64.b64decode(report_b64)
            report_dict = json.loads(report_json.decode())

            return AttestationReport(
                instance_name=report_dict.get("instance_name", ""),
                project_id=report_dict.get("project_id", ""),
                zone=report_dict.get("zone", ""),
                attestation_time=datetime.fromtimestamp(report_dict.get("attestation_time", 0)),
                tee_type=report_dict.get("tee_type", "UNKNOWN"),
                platform_measurements=report_dict.get("platform_measurements", {}),
                guest_measurements=report_dict.get("guest_measurements", {}),
                signature=attestation_data.get("signature", ""),
                certificate_chain=attestation_data.get("certificateChain", []),
                raw_report=report_dict
            )

        except Exception as e:
            logger.error(f"Error parseando reporte de attestación: {e}")
            return None

    def _verify_measurements(
        self,
        report: AttestationReport,
        expected: ReferenceMeasurements
    ) -> Tuple[bool, List[str]]:
        """
        Verifica las mediciones del reporte contra las referencias.

        Returns:
            Tupla de (is_valid, issues)
        """
        issues = []

        # Verificar mediciones de plataforma
        platform = report.platform_measurements
        if platform.get("platform_firmware_hash") != expected.platform_firmware_hash:
            issues.append("Hash de firmware de plataforma no coincide")

        if platform.get("kernel_hash") != expected.kernel_hash:
            issues.append("Hash del kernel no coincide")

        if platform.get("initrd_hash") != expected.initrd_hash:
            issues.append("Hash del initrd no coincide")

        # Verificar mediciones de guest
        guest = report.guest_measurements
        if guest.get("guest_policy") != expected.guest_policy:
            issues.append("Política de guest no coincide")

        if expected.family_id and guest.get("family_id") != expected.family_id:
            issues.append("Family ID no coincide")

        if expected.image_id and guest.get("image_id") != expected.image_id:
            issues.append("Image ID no coincide")

        if expected.launch_measurement and guest.get("launch_measurement") != expected.launch_measurement:
            issues.append("Medición de lanzamiento no coincide")

        return len(issues) == 0, issues

    def _is_attestation_too_old(self, attestation_time: datetime, max_age_hours: int = 24) -> bool:
        """
        Verifica si el reporte de attestación es demasiado antiguo.
        """
        age = datetime.utcnow() - attestation_time
        return age > timedelta(hours=max_age_hours)

    def update_reference_measurements(
        self,
        key: str,
        measurements: ReferenceMeasurements
    ) -> None:
        """
        Actualiza las mediciones de referencia y las guarda persistentemente.

        Args:
            key: Clave identificadora
            measurements: Nuevas mediciones de referencia
        """
        measurements.updated_at = datetime.utcnow()
        self.reference_measurements[key] = measurements

        # Guardar en archivo JSON
        try:
            data = {}
            for k, m in self.reference_measurements.items():
                data[k] = {
                    "platform_firmware_hash": m.platform_firmware_hash,
                    "kernel_hash": m.kernel_hash,
                    "initrd_hash": m.initrd_hash,
                    "guest_policy": m.guest_policy,
                    "family_id": m.family_id,
                    "image_id": m.image_id,
                    "launch_measurement": m.launch_measurement,
                    "created_at": m.created_at.isoformat(),
                    "updated_at": m.updated_at.isoformat()
                }

            with open(self.reference_measurements_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Mediciones de referencia actualizadas y guardadas para: {key}")

        except Exception as e:
            logger.error(f"Error guardando mediciones de referencia: {e}")
            raise

    def get_reference_measurements(self, key: str) -> Optional[ReferenceMeasurements]:
        """
        Obtiene mediciones de referencia por clave.
        """
        return self.reference_measurements.get(key)

    def get_attestation_metrics(self) -> Dict[str, Any]:
        """
        Obtiene métricas de monitoreo de attestación.

        Returns:
            Diccionario con métricas de attestación
        """
        metrics = self.metrics.copy()

        # Calcular tasas de éxito/error
        if metrics["total_attestations"] > 0:
            metrics["success_rate"] = metrics["successful_attestations"] / metrics["total_attestations"]
            metrics["failure_rate"] = metrics["failed_attestations"] / metrics["total_attestations"]
        else:
            metrics["success_rate"] = 0.0
            metrics["failure_rate"] = 0.0

        # Información adicional
        metrics["reference_measurements_count"] = len(self.reference_measurements)
        metrics["supported_tee_types"] = ["SEV_SNP"]

        return metrics


# Instancia global
tee_attestation_validator = TEEAttestationValidator()


def get_tee_attestation_validator() -> TEEAttestationValidator:
    """Obtener instancia global del validador de attestación TEE."""
    return tee_attestation_validator