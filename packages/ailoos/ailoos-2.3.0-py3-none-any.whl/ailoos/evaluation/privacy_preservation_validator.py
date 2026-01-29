"""
Validador de preservación de privacidad con TenSEAL.
Verifica que la privacidad se mantiene durante el aprendizaje federado.
"""

import torch
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
from collections import defaultdict

from ..core.logging import get_logger

# Importar TenSEAL si está disponible
try:
    import tenseal as ts
    TENSEAL_AVAILABLE = True
except ImportError:
    TENSEAL_AVAILABLE = False
    ts = None

logger = get_logger(__name__)


@dataclass
class PrivacyLeakageTest:
    """Resultado de una prueba de filtración de privacidad."""
    test_name: str
    leakage_detected: bool
    leakage_score: float  # 0.0 = no leakage, 1.0 = maximum leakage
    confidence_level: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PrivacyValidationResult:
    """Resultado completo de validación de privacidad."""
    round_number: int
    overall_privacy_score: float  # 0.0 = perfect privacy, 1.0 = compromised
    encryption_integrity: bool
    differential_privacy_compliance: bool
    leakage_tests: List[PrivacyLeakageTest] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class PrivacyAuditReport:
    """Reporte completo de auditoría de privacidad."""
    total_rounds_audited: int
    average_privacy_score: float
    encryption_failures: int
    privacy_violations: int
    most_common_leakage: Optional[str]
    compliance_level: str  # "excellent", "good", "fair", "poor", "critical"
    audit_history: List[PrivacyValidationResult] = field(default_factory=list)


class PrivacyPreservationValidator:
    """
    Validador que verifica la preservación de privacidad usando TenSEAL.
    Realiza pruebas de integridad de encriptación y detección de filtraciones.
    """

    def __init__(self, enable_differential_privacy: bool = True,
                 privacy_budget_epsilon: float = 1.0,
                 leakage_detection_threshold: float = 0.1):
        self.enable_differential_privacy = enable_differential_privacy
        self.privacy_budget_epsilon = privacy_budget_epsilon
        self.leakage_detection_threshold = leakage_detection_threshold

        # Estado de validación
        self.audit_history: List[PrivacyValidationResult] = []
        self.encryption_contexts: Dict[str, Any] = {}
        self.privacy_budgets: Dict[str, float] = defaultdict(float)

        # Estadísticas de privacidad
        self.encryption_failures = 0
        self.privacy_violations = 0

        if not TENSEAL_AVAILABLE:
            logger.warning("⚠️ TenSEAL not available. Privacy validation will be limited.")
        else:
            logger.info("🔐 PrivacyPreservationValidator initialized with TenSEAL")

    def validate_round_privacy(self, round_number: int, encrypted_gradients: Dict[str, Any],
                              node_contributions: List[Dict[str, Any]]) -> PrivacyValidationResult:
        """
        Valida la preservación de privacidad en una ronda federada.

        Args:
            round_number: Número de ronda
            encrypted_gradients: Gradientes encriptados de nodos
            node_contributions: Contribuciones de nodos con metadatos

        Returns:
            Resultado de validación de privacidad
        """
        leakage_tests = []
        recommendations = []

        # 1. Verificar integridad de encriptación
        encryption_integrity = self._validate_encryption_integrity(encrypted_gradients)
        if not encryption_integrity:
            self.encryption_failures += 1
            recommendations.append("Encryption integrity compromised - check TenSEAL configuration")

        # 2. Probar filtraciones de privacidad
        leakage_tests.extend(self._perform_leakage_tests(encrypted_gradients, node_contributions))

        # 3. Verificar cumplimiento de differential privacy
        dp_compliance = self._validate_differential_privacy(node_contributions)
        if not dp_compliance:
            self.privacy_violations += 1
            recommendations.append("Differential privacy budget exceeded")

        # 4. Calcular score general de privacidad
        overall_score = self._calculate_overall_privacy_score(
            encryption_integrity, dp_compliance, leakage_tests
        )

        # 5. Generar recomendaciones adicionales
        recommendations.extend(self._generate_privacy_recommendations(
            overall_score, leakage_tests
        ))

        result = PrivacyValidationResult(
            round_number=round_number,
            overall_privacy_score=overall_score,
            encryption_integrity=encryption_integrity,
            differential_privacy_compliance=dp_compliance,
            leakage_tests=leakage_tests,
            recommendations=recommendations
        )

        self.audit_history.append(result)

        logger.info(f"🔐 Privacy validation for round {round_number}:")
        logger.info(f"   Overall Score: {overall_score:.4f}")
        logger.info(f"   Encryption Integrity: {encryption_integrity}")
        logger.info(f"   DP Compliance: {dp_compliance}")
        logger.info(f"   Leakage Tests: {len(leakage_tests)} performed")

        return result

    def _validate_encryption_integrity(self, encrypted_gradients: Dict[str, Any]) -> bool:
        """Valida la integridad de la encriptación TenSEAL."""
        if not TENSEAL_AVAILABLE or not encrypted_gradients:
            return False

        try:
            # Verificar que todos los gradientes estén encriptados
            for node_id, gradients in encrypted_gradients.items():
                if not isinstance(gradients, dict):
                    logger.warning(f"❌ Invalid gradient format for {node_id}")
                    return False

                # Verificar estructura de encriptación TenSEAL
                for layer_name, encrypted_tensor in gradients.items():
                    if not hasattr(encrypted_tensor, 'decrypt'):
                        logger.warning(f"❌ Gradient not encrypted for {node_id}:{layer_name}")
                        return False

                    # Intentar desencriptar para verificar integridad
                    try:
                        decrypted = encrypted_tensor.decrypt()
                        if decrypted is None:
                            logger.warning(f"❌ Failed to decrypt gradient for {node_id}:{layer_name}")
                            return False
                    except Exception as e:
                        logger.warning(f"❌ Decryption error for {node_id}:{layer_name}: {e}")
                        return False

            return True

        except Exception as e:
            logger.error(f"❌ Error validating encryption integrity: {e}")
            return False

    def _perform_leakage_tests(self, encrypted_gradients: Dict[str, Any],
                             node_contributions: List[Dict[str, Any]]) -> List[PrivacyLeakageTest]:
        """Realiza pruebas de detección de filtraciones de privacidad."""
        tests = []

        # Test 1: Membership Inference Attack simulation
        membership_test = self._test_membership_inference(encrypted_gradients, node_contributions)
        tests.append(membership_test)

        # Test 2: Gradient Reconstruction Attack
        reconstruction_test = self._test_gradient_reconstruction(encrypted_gradients)
        tests.append(reconstruction_test)

        # Test 3: Model Inversion Attack simulation
        inversion_test = self._test_model_inversion(node_contributions)
        tests.append(inversion_test)

        # Test 4: Differential Privacy Leakage
        dp_leakage_test = self._test_differential_privacy_leakage(node_contributions)
        tests.append(dp_leakage_test)

        return tests

    def _test_membership_inference(self, encrypted_gradients: Dict[str, Any],
                                 node_contributions: List[Dict[str, Any]]) -> PrivacyLeakageTest:
        """Simula ataque de inferencia de membresía."""
        test_name = "Membership Inference Attack"

        try:
            if not encrypted_gradients or len(node_contributions) < 2:
                return PrivacyLeakageTest(
                    test_name=test_name,
                    leakage_detected=False,
                    leakage_score=0.0,
                    confidence_level=0.5,
                    details={"reason": "insufficient_data"}
                )

            # Simular ataque: comparar distribuciones de gradientes
            gradient_norms = []
            for node_id, gradients in encrypted_gradients.items():
                try:
                    # Calcular norma de gradientes encriptados (aproximada)
                    norm_sum = 0
                    param_count = 0
                    for layer_name, encrypted_tensor in gradients.items():
                        if hasattr(encrypted_tensor, 'decrypt'):
                            decrypted = encrypted_tensor.decrypt()
                            if isinstance(decrypted, (list, np.ndarray)):
                                norm_sum += np.linalg.norm(decrypted)
                                param_count += len(decrypted) if hasattr(decrypted, '__len__') else 1

                    if param_count > 0:
                        avg_norm = norm_sum / param_count
                        gradient_norms.append(avg_norm)
                except Exception as e:
                    logger.debug(f"Error calculating gradient norm for {node_id}: {e}")
                    continue

            if len(gradient_norms) < 2:
                return PrivacyLeakageTest(
                    test_name=test_name,
                    leakage_detected=False,
                    leakage_score=0.0,
                    confidence_level=0.5,
                    details={"reason": "insufficient_gradient_data"}
                )

            # Calcular variabilidad - alta variabilidad puede indicar filtración
            norm_std = np.std(gradient_norms)
            norm_mean = np.mean(gradient_norms)
            cv = norm_std / norm_mean if norm_mean > 0 else 0  # Coeficiente de variación

            # Umbral de filtración: CV > 2.0 indica posible filtración
            leakage_score = min(cv / 2.0, 1.0)
            leakage_detected = leakage_score > self.leakage_detection_threshold

            return PrivacyLeakageTest(
                test_name=test_name,
                leakage_detected=leakage_detected,
                leakage_score=leakage_score,
                confidence_level=0.8,
                details={
                    "gradient_norm_cv": cv,
                    "norms_analyzed": len(gradient_norms),
                    "threshold": self.leakage_detection_threshold
                }
            )

        except Exception as e:
            logger.error(f"Error in membership inference test: {e}")
            return PrivacyLeakageTest(
                test_name=test_name,
                leakage_detected=True,  # Asumir filtración por error
                leakage_score=1.0,
                confidence_level=0.9,
                details={"error": str(e)}
            )

    def _test_gradient_reconstruction(self, encrypted_gradients: Dict[str, Any]) -> PrivacyLeakageTest:
        """Prueba reconstrucción de gradientes desde datos encriptados."""
        test_name = "Gradient Reconstruction Attack"

        try:
            if not TENSEAL_AVAILABLE or not encrypted_gradients:
                return PrivacyLeakageTest(
                    test_name=test_name,
                    leakage_detected=False,
                    leakage_score=0.0,
                    confidence_level=0.5,
                    details={"reason": "tenseal_unavailable"}
                )

            # Intentar reconstruir gradientes y medir precisión
            reconstruction_errors = []

            for node_id, gradients in encrypted_gradients.items():
                try:
                    reconstructed = {}
                    for layer_name, encrypted_tensor in gradients.items():
                        if hasattr(encrypted_tensor, 'decrypt'):
                            decrypted = encrypted_tensor.decrypt()
                            reconstructed[layer_name] = decrypted

                    # Calcular error de reconstrucción (comparar con original si disponible)
                    # En la práctica, no tenemos el original, así que usamos heurísticas
                    if reconstructed:
                        # Verificar que los valores desencriptados sean razonables
                        total_params = 0
                        invalid_params = 0

                        for layer_name, tensor in reconstructed.items():
                            if isinstance(tensor, (list, np.ndarray)):
                                total_params += len(tensor)
                                # Contar valores NaN o infinitos
                                if isinstance(tensor, np.ndarray):
                                    invalid_params += np.sum(np.isnan(tensor) | np.isinf(tensor))
                                else:
                                    invalid_params += sum(1 for x in tensor if not np.isfinite(x))

                        if total_params > 0:
                            error_rate = invalid_params / total_params
                            reconstruction_errors.append(error_rate)

                except Exception as e:
                    logger.debug(f"Reconstruction error for {node_id}: {e}")
                    reconstruction_errors.append(1.0)  # Error completo
                    continue

            if not reconstruction_errors:
                return PrivacyLeakageTest(
                    test_name=test_name,
                    leakage_detected=False,
                    leakage_score=0.0,
                    confidence_level=0.5,
                    details={"reason": "no_reconstructions"}
                )

            avg_error = np.mean(reconstruction_errors)
            leakage_score = min(avg_error, 1.0)
            leakage_detected = leakage_score > self.leakage_detection_threshold

            return PrivacyLeakageTest(
                test_name=test_name,
                leakage_detected=leakage_detected,
                leakage_score=leakage_score,
                confidence_level=0.85,
                details={
                    "avg_reconstruction_error": avg_error,
                    "reconstructions_attempted": len(reconstruction_errors),
                    "threshold": self.leakage_detection_threshold
                }
            )

        except Exception as e:
            logger.error(f"Error in gradient reconstruction test: {e}")
            return PrivacyLeakageTest(
                test_name=test_name,
                leakage_detected=True,
                leakage_score=1.0,
                confidence_level=0.9,
                details={"error": str(e)}
            )

    def _test_model_inversion(self, node_contributions: List[Dict[str, Any]]) -> PrivacyLeakageTest:
        """Simula ataque de inversión de modelo."""
        test_name = "Model Inversion Attack"

        try:
            if len(node_contributions) < 3:
                return PrivacyLeakageTest(
                    test_name=test_name,
                    leakage_detected=False,
                    leakage_score=0.0,
                    confidence_level=0.5,
                    details={"reason": "insufficient_contributions"}
                )

            # Analizar correlación entre contribuciones y posibles datos sensibles
            accuracies = [c.get("accuracy", 0.0) for c in node_contributions]
            losses = [c.get("loss", 0.0) for c in node_contributions]
            sample_counts = [c.get("samples_processed", 0) for c in node_contributions]

            # Calcular correlaciones que podrían indicar filtración
            if len(accuracies) > 1 and len(sample_counts) > 1:
                acc_sample_corr = np.corrcoef(accuracies, sample_counts)[0, 1]
                loss_sample_corr = np.corrcoef(losses, sample_counts)[0, 1]

                # Alta correlación entre accuracy/loss y tamaño del dataset puede indicar filtración
                max_corr = max(abs(acc_sample_corr), abs(loss_sample_corr))
                leakage_score = min(max_corr, 1.0)
            else:
                leakage_score = 0.0

            leakage_detected = leakage_score > self.leakage_detection_threshold

            return PrivacyLeakageTest(
                test_name=test_name,
                leakage_detected=leakage_detected,
                leakage_score=leakage_score,
                confidence_level=0.75,
                details={
                    "acc_sample_correlation": acc_sample_corr if 'acc_sample_corr' in locals() else 0.0,
                    "loss_sample_correlation": loss_sample_corr if 'loss_sample_corr' in locals() else 0.0,
                    "max_correlation": max_corr if 'max_corr' in locals() else 0.0,
                    "threshold": self.leakage_detection_threshold
                }
            )

        except Exception as e:
            logger.error(f"Error in model inversion test: {e}")
            return PrivacyLeakageTest(
                test_name=test_name,
                leakage_detected=True,
                leakage_score=1.0,
                confidence_level=0.9,
                details={"error": str(e)}
            )

    def _test_differential_privacy_leakage(self, node_contributions: List[Dict[str, Any]]) -> PrivacyLeakageTest:
        """Prueba filtraciones relacionadas con differential privacy."""
        test_name = "Differential Privacy Leakage"

        try:
            if not self.enable_differential_privacy:
                return PrivacyLeakageTest(
                    test_name=test_name,
                    leakage_detected=False,
                    leakage_score=0.0,
                    confidence_level=1.0,
                    details={"reason": "differential_privacy_disabled"}
                )

            # Verificar uso del presupuesto de privacidad
            total_epsilon_used = sum(self.privacy_budgets.values())

            if total_epsilon_used > self.privacy_budget_epsilon:
                leakage_score = min((total_epsilon_used - self.privacy_budget_epsilon) / self.privacy_budget_epsilon, 1.0)
                leakage_detected = True
            else:
                leakage_score = total_epsilon_used / self.privacy_budget_epsilon
                leakage_detected = False

            return PrivacyLeakageTest(
                test_name=test_name,
                leakage_detected=leakage_detected,
                leakage_score=leakage_score,
                confidence_level=0.95,
                details={
                    "total_epsilon_used": total_epsilon_used,
                    "privacy_budget": self.privacy_budget_epsilon,
                    "budget_exceeded": total_epsilon_used > self.privacy_budget_epsilon
                }
            )

        except Exception as e:
            logger.error(f"Error in differential privacy test: {e}")
            return PrivacyLeakageTest(
                test_name=test_name,
                leakage_detected=True,
                leakage_score=1.0,
                confidence_level=0.9,
                details={"error": str(e)}
            )

    def _validate_differential_privacy(self, node_contributions: List[Dict[str, Any]]) -> bool:
        """Valida cumplimiento de differential privacy."""
        if not self.enable_differential_privacy:
            return True  # No aplicable

        # Verificar que el presupuesto de privacidad no se exceda
        total_epsilon = sum(self.privacy_budgets.values())
        return total_epsilon <= self.privacy_budget_epsilon

    def _calculate_overall_privacy_score(self, encryption_integrity: bool,
                                       dp_compliance: bool,
                                       leakage_tests: List[PrivacyLeakageTest]) -> float:
        """Calcula score general de privacidad."""
        # Factores:
        # 1. Integridad de encriptación (40%)
        # 2. Cumplimiento DP (30%)
        # 3. Pruebas de filtración (30%)

        encryption_score = 0.0 if not encryption_integrity else 1.0
        dp_score = 0.0 if not dp_compliance else 1.0

        if leakage_tests:
            avg_leakage = np.mean([test.leakage_score for test in leakage_tests])
            leakage_score = 1.0 - avg_leakage  # Invertir: menos filtración = mejor score
        else:
            leakage_score = 1.0

        overall_score = (
            encryption_score * 0.4 +
            dp_score * 0.3 +
            leakage_score * 0.3
        )

        return overall_score

    def _generate_privacy_recommendations(self, overall_score: float,
                                        leakage_tests: List[PrivacyLeakageTest]) -> List[str]:
        """Genera recomendaciones para mejorar la privacidad."""
        recommendations = []

        if overall_score < 0.5:
            recommendations.append("Critical: Overall privacy score is very low. Immediate action required.")

        if not any(test.leakage_detected for test in leakage_tests):
            recommendations.append("Good: No privacy leakages detected in current tests.")
        else:
            failed_tests = [test.test_name for test in leakage_tests if test.leakage_detected]
            recommendations.append(f"Warning: Privacy leakages detected in: {', '.join(failed_tests)}")

        if overall_score < 0.7:
            recommendations.append("Consider increasing differential privacy epsilon budget.")
            recommendations.append("Verify TenSEAL encryption parameters and key management.")

        if len(leakage_tests) > 0:
            high_leakage_tests = [test for test in leakage_tests if test.leakage_score > 0.5]
            if high_leakage_tests:
                recommendations.append("High leakage scores detected. Consider additional privacy mechanisms.")

        return recommendations

    def generate_privacy_audit_report(self) -> PrivacyAuditReport:
        """Genera reporte completo de auditoría de privacidad."""
        if not self.audit_history:
            return PrivacyAuditReport(
                total_rounds_audited=0,
                average_privacy_score=0.0,
                encryption_failures=0,
                privacy_violations=0,
                most_common_leakage=None,
                compliance_level="unknown"
            )

        # Calcular estadísticas
        avg_privacy_score = np.mean([result.overall_privacy_score for result in self.audit_history])

        # Encontrar filtración más común
        all_leakages = []
        for result in self.audit_history:
            for test in result.leakage_tests:
                if test.leakage_detected:
                    all_leakages.append(test.test_name)

        most_common_leakage = None
        if all_leakages:
            from collections import Counter
            most_common_leakage = Counter(all_leakages).most_common(1)[0][0]

        # Determinar nivel de cumplimiento
        if avg_privacy_score >= 0.9:
            compliance_level = "excellent"
        elif avg_privacy_score >= 0.8:
            compliance_level = "good"
        elif avg_privacy_score >= 0.6:
            compliance_level = "fair"
        elif avg_privacy_score >= 0.3:
            compliance_level = "poor"
        else:
            compliance_level = "critical"

        return PrivacyAuditReport(
            total_rounds_audited=len(self.audit_history),
            average_privacy_score=avg_privacy_score,
            encryption_failures=self.encryption_failures,
            privacy_violations=self.privacy_violations,
            most_common_leakage=most_common_leakage,
            compliance_level=compliance_level,
            audit_history=self.audit_history.copy()
        )

    def get_privacy_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de privacidad."""
        report = self.generate_privacy_audit_report()

        return {
            "total_rounds_audited": report.total_rounds_audited,
            "average_privacy_score": report.average_privacy_score,
            "encryption_failures": report.encryption_failures,
            "privacy_violations": report.privacy_violations,
            "most_common_leakage": report.most_common_leakage,
            "compliance_level": report.compliance_level,
            "tenseal_available": TENSEAL_AVAILABLE,
            "differential_privacy_enabled": self.enable_differential_privacy,
            "privacy_budget_epsilon": self.privacy_budget_epsilon,
            "latest_audit": self.audit_history[-1].__dict__ if self.audit_history else None
        }

    def reset(self):
        """Resetea el validador de privacidad."""
        self.audit_history.clear()
        self.encryption_contexts.clear()
        self.privacy_budgets.clear()
        self.encryption_failures = 0
        self.privacy_violations = 0
        logger.info("🔄 PrivacyPreservationValidator reset")