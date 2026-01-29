"""
Verificador de contribuciones federadas para Ailoos.
Verifica las pruebas ZKP generadas por los nodos para asegurar que sus
contribuciones federadas son válidas y honestas. Incluye verificación de
pruebas de entrenamiento, validación de parámetros, y detección de
contribuciones maliciosas o fraudulentas.
"""

import asyncio
import hashlib
import json
import math
import secrets
import time
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

import numpy as np
from ecdsa import VerifyingKey, BadSignatureError, SECP256k1

from ..core.config import Config
from ..utils.logging import AiloosLogger
from .training_prover import TrainingProver
from .zkp_engine import ZKPEngine
from ..validation.validator import EmpoorioLMValidator, ValidationConfig


@dataclass
class ContributionMetrics:
    """Métricas detalladas de una contribución."""

    # Métricas de confianza
    signature_verification_score: float = 0.0  # 0-1, confianza en la firma digital
    zkp_verification_score: float = 0.0  # 0-1, confianza en las pruebas ZKP
    parameter_consistency_score: float = 0.0  # 0-1, consistencia de parámetros
    model_quality_score: float = 0.0  # 0-1, calidad del modelo actualizado
    anomaly_detection_score: float = 0.0  # 0-1, detección de anomalías (1 = normal)

    # Métricas de rendimiento
    verification_time_ms: float = 0.0
    computational_efficiency: float = 0.0  # Eficiencia computacional relativa

    # Métricas de seguridad
    malicious_pattern_score: float = 0.0  # 0-1, probabilidad de patrón malicioso
    data_poisoning_score: float = 0.0  # 0-1, probabilidad de envenenamiento de datos

    # Estadísticas históricas
    node_reputation_score: float = 0.0  # 0-1, reputación histórica del nodo
    session_consistency_score: float = 0.0  # 0-1, consistencia con otras contribuciones

    # Metadatos
    verification_timestamp: float = 0.0
    verification_components: List[str] = field(default_factory=list)


@dataclass
class VerificationResult:
    """Resultado completo de verificación de contribución."""

    node_id: str
    session_id: str
    round_number: int
    contribution_id: str

    # Resultado general
    is_valid: bool = False
    confidence_score: float = 0.0  # 0-1, puntuación global de confianza
    risk_level: str = "high"  # "low", "medium", "high", "critical"

    # Detalles de verificación
    signature_verification_passed: bool = False
    zkp_verification_passed: bool = False
    parameter_validation_passed: bool = False
    anomaly_detection_passed: bool = False

    # Métricas detalladas
    metrics: ContributionMetrics = field(default_factory=ContributionMetrics)

    # Información de fallos
    failure_reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Recomendaciones
    recommended_actions: List[str] = field(default_factory=list)

    # Timestamp
    verified_at: datetime = field(default_factory=datetime.now)


@dataclass
class ContributionVerifierConfig:
    """Configuración del verificador de contribuciones."""

    # Configuración de verificación ZKP
    enable_zkp_verification: bool = True
    zkp_verification_timeout_ms: int = 5000
    min_zkp_confidence_threshold: float = 0.95

    # Configuración de validación de parámetros
    enable_parameter_validation: bool = True
    max_parameter_deviation: float = 0.1  # Máxima desviación permitida
    enable_model_validation: bool = True

    # Configuración de detección de anomalías
    enable_anomaly_detection: bool = True
    anomaly_detection_sensitivity: float = 0.8  # 0-1, sensibilidad
    enable_malware_detection: bool = True

    # Configuración de métricas de confianza
    enable_confidence_scoring: bool = True
    confidence_weights: Dict[str, float] = field(default_factory=lambda: {
        'signature_verification': 0.3,
        'zkp_verification': 0.3,
        'parameter_consistency': 0.2,
        'model_quality': 0.1,
        'anomaly_detection': 0.1
    })

    # Configuración de rendimiento
    enable_parallel_verification: bool = True
    max_concurrent_verifications: int = 100
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600

    # Configuración de seguridad
    enable_fraud_detection: bool = True
    fraud_detection_threshold: float = 0.7
    enable_reputation_system: bool = True

    # Configuración de logging
    enable_detailed_logging: bool = True
    log_verification_failures: bool = True


class ContributionVerifier:
    """
    Verificador avanzado de contribuciones federadas.

    Verifica la validez de las contribuciones usando múltiples capas:
    - Verificación de pruebas ZKP de entrenamiento
    - Validación de parámetros del modelo
    - Detección de anomalías y comportamientos maliciosos
    - Sistema de métricas de confianza escalable
    """

    def __init__(self, config: Config, verifier_config: Optional[ContributionVerifierConfig] = None):
        self.config = config
        self.verifier_config = verifier_config or ContributionVerifierConfig()
        self.logger = AiloosLogger(__name__)

        # Componentes de verificación
        self.zkp_engine = ZKPEngine()
        self.training_prover = TrainingProver()
        self.model_validator = EmpoorioLMValidator(ValidationConfig())

        # Estado y caché
        self.verification_cache: Dict[str, VerificationResult] = {}
        self.node_reputation: Dict[str, float] = defaultdict(lambda: 0.5)  # Inicial 0.5
        self.session_stats: Dict[str, Dict[str, Any]] = {}

        # Estadísticas de rendimiento
        self.verification_stats = {
            'total_verifications': 0,
            'successful_verifications': 0,
            'failed_verifications': 0,
            'average_verification_time_ms': 0.0,
            'zkp_failures': 0,
            'parameter_failures': 0,
            'anomaly_detections': 0
        }

        self.logger.info("🛡️ ContributionVerifier inicializado")

    async def verify_contribution(
        self,
        node_id: str,
        session_id: str,
        round_number: int,
        contribution_id: str,
        training_proof: Dict[str, Any],
        model_parameters: Dict[str, Any],
        training_metadata: Dict[str, Any],
        node_signature: str,
        node_public_key: str,
        session_context: Optional[Dict[str, Any]] = None
    ) -> VerificationResult:
        """
        Verifica una contribución federada completa.

        Args:
            node_id: ID del nodo contribuyente
            session_id: ID de la sesión federada
            round_number: Número de ronda
            contribution_id: ID único de la contribución
            training_proof: Prueba ZKP de entrenamiento
            model_parameters: Parámetros del modelo actualizado
            training_metadata: Metadatos del entrenamiento
            session_context: Contexto adicional de la sesión

        Returns:
            VerificationResult: Resultado completo de verificación
        """
        start_time = time.time()
        self.logger.info(f"🔍 Verificando contribución {contribution_id} de nodo {node_id}")

        # Inicializar resultado
        result = VerificationResult(
            node_id=node_id,
            session_id=session_id,
            round_number=round_number,
            contribution_id=contribution_id,
            is_valid=False,
            confidence_score=0.0,
            risk_level="high",
            zkp_verification_passed=False,
            parameter_validation_passed=False,
            anomaly_detection_passed=False,
            metrics=ContributionMetrics()
        )

        try:
            # Preparar datos para verificación de firma
            contribution_data = {
                'node_id': node_id,
                'session_id': session_id,
                'round_number': round_number,
                'contribution_id': contribution_id,
                'training_proof': training_proof,
                'model_parameters': model_parameters,
                'training_metadata': training_metadata
            }

            # 0. Verificación de firma digital del nodo
            signature_result = self._verify_node_signature(node_signature, node_public_key, contribution_data)
            result.signature_verification_passed = signature_result['passed']
            result.metrics.signature_verification_score = signature_result['score']
            result.metrics.verification_components.append('signature_verification')
            if not signature_result['passed']:
                result.failure_reasons.extend(signature_result['reasons'])

            # 1. Verificación de pruebas ZKP
            if self.verifier_config.enable_zkp_verification:
                zkp_result = await self._verify_zkp_proof(training_proof)
                result.zkp_verification_passed = zkp_result['passed']
                result.metrics.zkp_verification_score = zkp_result['score']
                result.metrics.verification_components.append('zkp_verification')
                if not zkp_result['passed']:
                    result.failure_reasons.extend(zkp_result['reasons'])

            # 2. Validación de parámetros del modelo
            if self.verifier_config.enable_parameter_validation:
                param_result = await self._validate_model_parameters(
                    model_parameters, training_metadata, session_context
                )
                result.parameter_validation_passed = param_result['passed']
                result.metrics.parameter_consistency_score = param_result['score']
                result.metrics.verification_components.append('parameter_validation')
                if not param_result['passed']:
                    result.failure_reasons.extend(param_result['reasons'])

            # 3. Detección de anomalías y comportamientos maliciosos
            if self.verifier_config.enable_anomaly_detection:
                anomaly_result = await self._detect_anomalies(
                    training_proof, model_parameters, training_metadata, session_context
                )
                result.anomaly_detection_passed = anomaly_result['passed']
                result.metrics.anomaly_detection_score = anomaly_result['score']
                result.metrics.malicious_pattern_score = anomaly_result.get('malicious_score', 0.0)
                result.metrics.data_poisoning_score = anomaly_result.get('poisoning_score', 0.0)
                result.metrics.verification_components.append('anomaly_detection')
                if not anomaly_result['passed']:
                    result.failure_reasons.extend(anomaly_result['reasons'])

            # 4. Calcular métricas de confianza adicionales
            await self._calculate_confidence_metrics(result, session_context)

            # 5. Evaluar resultado general
            result.is_valid, result.confidence_score = self._evaluate_overall_validity(result)
            result.risk_level = self._calculate_risk_level(result.confidence_score)

            # 6. Generar recomendaciones
            result.recommended_actions = self._generate_recommendations(result)

            # Actualizar estadísticas
            verification_time = (time.time() - start_time) * 1000
            result.metrics.verification_time_ms = verification_time
            self._update_verification_stats(result, verification_time)

            # Cachear resultado si está habilitado
            if self.verifier_config.enable_caching:
                cache_key = f"{node_id}_{session_id}_{round_number}_{contribution_id}"
                self.verification_cache[cache_key] = result

            self.logger.info(f"✅ Verificación completada: {'VÁLIDA' if result.is_valid else 'INVÁLIDA'} "
                           ".2f")
        except Exception as e:
            self.logger.error(f"❌ Error durante verificación de contribución {contribution_id}: {e}")
            result.failure_reasons.append(f"Error interno: {str(e)}")
            result.risk_level = "critical"
        finally:
            return result

    async def _verify_zkp_proof(self, training_proof: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica las pruebas ZKP de entrenamiento."""
        try:
            start_time = time.time()

            # Verificar la prueba completa usando el training prover
            is_valid = await self.training_prover.verify_training_proof(training_proof)

            verification_time = (time.time() - start_time) * 1000

            if is_valid:
                # Verificar que el tiempo de verificación esté dentro de límites razonables
                if verification_time > self.verifier_config.zkp_verification_timeout_ms:
                    return {
                        'passed': False,
                        'score': 0.5,
                        'reasons': [f"Tiempo de verificación ZKP excesivo: {verification_time:.2f}ms"]
                    }

                # Calcular score basado en la complejidad de la prueba
                proof_complexity = self._calculate_proof_complexity(training_proof)
                confidence_score = min(1.0, proof_complexity / 10.0)  # Normalizar

                return {
                    'passed': True,
                    'score': confidence_score,
                    'reasons': []
                }
            else:
                return {
                    'passed': False,
                    'score': 0.0,
                    'reasons': ['Verificación ZKP fallida']
                }

        except Exception as e:
            self.logger.error(f"Error verificando prueba ZKP: {e}")
            return {
                'passed': False,
                'score': 0.0,
                'reasons': [f'Error en verificación ZKP: {str(e)}']
            }

    def _verify_node_signature(
        self,
        node_signature: str,
        node_public_key: str,
        contribution_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Verifica la firma digital ECDSA del nodo usando la clave pública.

        Args:
            node_signature: Firma ECDSA en formato hex
            node_public_key: Clave pública ECDSA en formato hex
            contribution_data: Datos de la contribución a verificar

        Returns:
            Dict con resultado de verificación
        """
        try:
            # Crear hash de los datos de contribución
            data_hash = self._hash_contribution_data(contribution_data)

            # Decodificar clave pública
            try:
                vk = VerifyingKey.from_secret_exponent(int(node_public_key, 16), curve=SECP256k1)
            except Exception as e:
                return {
                    'passed': False,
                    'score': 0.0,
                    'reasons': [f'Clave pública inválida: {str(e)}']
                }

            # Decodificar firma
            try:
                signature_bytes = bytes.fromhex(node_signature)
            except ValueError:
                return {
                    'passed': False,
                    'score': 0.0,
                    'reasons': ['Firma en formato inválido']
                }

            # Verificar firma
            try:
                vk.verify(signature_bytes, data_hash, hashfunc=hashlib.sha256)
                return {
                    'passed': True,
                    'score': 1.0,
                    'reasons': []
                }
            except BadSignatureError:
                return {
                    'passed': False,
                    'score': 0.0,
                    'reasons': ['Firma digital inválida']
                }

        except Exception as e:
            self.logger.error(f"Error verificando firma del nodo: {e}")
            return {
                'passed': False,
                'score': 0.0,
                'reasons': [f'Error en verificación de firma: {str(e)}']
            }

    def _hash_contribution_data(self, contribution_data: Dict[str, Any]) -> bytes:
        """
        Crea un hash SHA-256 de los datos de contribución para firma.
        Incluye node_id, session_id, round_number, training_proof, model_parameters, training_metadata.
        """
        # Crear representación canónica de los datos
        canonical_data = {
            'node_id': contribution_data.get('node_id', ''),
            'session_id': contribution_data.get('session_id', ''),
            'round_number': contribution_data.get('round_number', 0),
            'contribution_id': contribution_data.get('contribution_id', ''),
            'training_proof': json.dumps(contribution_data.get('training_proof', {}), sort_keys=True),
            'model_parameters': json.dumps(contribution_data.get('model_parameters', {}), sort_keys=True),
            'training_metadata': json.dumps(contribution_data.get('training_metadata', {}), sort_keys=True)
        }

        # Serializar y hashear
        data_str = json.dumps(canonical_data, sort_keys=True)
        return hashlib.sha256(data_str.encode('utf-8')).digest()

    async def _validate_model_parameters(
        self,
        model_parameters: Dict[str, Any],
        training_metadata: Dict[str, Any],
        session_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Valida los parámetros del modelo actualizado."""
        try:
            issues = []
            score = 1.0

            # 1. Verificar estructura básica de parámetros
            if not model_parameters or not isinstance(model_parameters, dict):
                return {
                    'passed': False,
                    'score': 0.0,
                    'reasons': ['Parámetros del modelo inválidos o vacíos']
                }

            # 2. Verificar tamaño razonable del modelo
            param_count = self._count_parameters(model_parameters)
            if param_count < 1000:
                issues.append('Modelo demasiado pequeño')
                score *= 0.7
            elif param_count > 10000000:  # 10M parámetros
                issues.append('Modelo demasiado grande')
                score *= 0.8

            # 3. Verificar valores numéricos razonables
            nan_count, inf_count = self._check_parameter_values(model_parameters)
            if nan_count > 0:
                issues.append(f'Parámetros NaN detectados: {nan_count}')
                score *= 0.5
            if inf_count > 0:
                issues.append(f'Parámetros infinitos detectados: {inf_count}')
                score *= 0.6

            # 4. Verificar consistencia con metadatos de entrenamiento
            if training_metadata:
                metadata_consistency = self._check_metadata_consistency(
                    model_parameters, training_metadata
                )
                if not metadata_consistency['consistent']:
                    issues.extend(metadata_consistency['issues'])
                    score *= 0.8

            # 5. Comparar con estadísticas de sesión si disponibles
            if session_context:
                session_consistency = self._check_session_consistency(
                    model_parameters, session_context
                )
                if not session_consistency['consistent']:
                    issues.extend(session_consistency['issues'])
                    score *= 0.9

            passed = len(issues) == 0 or score >= 0.7  # Permitir algunos problemas menores

            return {
                'passed': passed,
                'score': score,
                'reasons': issues
            }

        except Exception as e:
            self.logger.error(f"Error validando parámetros del modelo: {e}")
            return {
                'passed': False,
                'score': 0.0,
                'reasons': [f'Error en validación de parámetros: {str(e)}']
            }

    async def _detect_anomalies(
        self,
        training_proof: Dict[str, Any],
        model_parameters: Dict[str, Any],
        training_metadata: Dict[str, Any],
        session_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Detecta anomalías y comportamientos potencialmente maliciosos."""
        try:
            issues = []
            anomaly_score = 1.0  # 1.0 = normal, 0.0 = altamente anómalo
            malicious_score = 0.0
            poisoning_score = 0.0

            # 1. Detectar patrones de entrenamiento sospechosos
            training_anomalies = self._detect_training_anomalies(training_proof, training_metadata)
            if training_anomalies['detected']:
                issues.extend(training_anomalies['issues'])
                anomaly_score *= training_anomalies['severity']
                malicious_score = max(malicious_score, training_anomalies.get('malicious_prob', 0.0))

            # 2. Detectar anomalías en parámetros del modelo
            parameter_anomalies = self._detect_parameter_anomalies(model_parameters)
            if parameter_anomalies['detected']:
                issues.extend(parameter_anomalies['issues'])
                anomaly_score *= parameter_anomalies['severity']
                poisoning_score = max(poisoning_score, parameter_anomalies.get('poisoning_prob', 0.0))

            # 3. Detectar comportamientos de Sybil o colusión
            if session_context:
                sybil_detection = self._detect_sybil_patterns(
                    training_proof.node_id, session_context
                )
                if sybil_detection['detected']:
                    issues.extend(sybil_detection['issues'])
                    anomaly_score *= sybil_detection['severity']
                    malicious_score = max(malicious_score, 0.8)  # Alta probabilidad de malicioso

            # 4. Verificar reputación histórica del nodo
            node_reputation = self.node_reputation.get(training_proof.node_id, 0.5)
            if node_reputation < 0.3:
                issues.append('.2f')
                anomaly_score *= 0.7
                malicious_score = max(malicious_score, 0.6)

            # 5. Detectar manipulación de timestamps
            timestamp_anomalies = self._detect_timestamp_anomalies(training_proof, training_metadata)
            if timestamp_anomalies['detected']:
                issues.extend(timestamp_anomalies['issues'])
                anomaly_score *= 0.8

            # Determinar si pasa la detección de anomalías
            threshold = 1.0 - self.verifier_config.anomaly_detection_sensitivity
            passed = anomaly_score >= threshold

            return {
                'passed': passed,
                'score': anomaly_score,
                'malicious_score': malicious_score,
                'poisoning_score': poisoning_score,
                'reasons': issues
            }

        except Exception as e:
            self.logger.error(f"Error en detección de anomalías: {e}")
            return {
                'passed': False,
                'score': 0.0,
                'malicious_score': 0.5,
                'poisoning_score': 0.5,
                'reasons': [f'Error en detección de anomalías: {str(e)}']
            }

    async def _calculate_confidence_metrics(
        self,
        result: VerificationResult,
        session_context: Optional[Dict[str, Any]] = None
    ):
        """Calcula métricas adicionales de confianza."""
        try:
            # Calcular reputación del nodo
            result.metrics.node_reputation_score = self.node_reputation.get(result.node_id, 0.5)

            # Calcular consistencia con la sesión
            if session_context:
                session_consistency = self._calculate_session_consistency(
                    result.node_id, result.session_id, session_context
                )
                result.metrics.session_consistency_score = session_consistency

            # Calcular eficiencia computacional
            if result.metrics.verification_time_ms > 0:
                # Eficiencia relativa (menor tiempo = mayor eficiencia)
                result.metrics.computational_efficiency = min(1.0, 5000 / result.metrics.verification_time_ms)

            # Calcular calidad del modelo (basado en metadatos disponibles)
            # Esto sería más sofisticado en una implementación real
            result.metrics.model_quality_score = 0.8  # Placeholder

        except Exception as e:
            self.logger.error(f"Error calculando métricas de confianza: {e}")

    def _evaluate_overall_validity(self, result: VerificationResult) -> Tuple[bool, float]:
        """Evalúa la validez general basada en todas las verificaciones."""
        try:
            weights = self.verifier_config.confidence_weights

            # Calcular puntuación ponderada
            confidence_score = (
                result.metrics.signature_verification_score * weights['signature_verification'] +
                result.metrics.zkp_verification_score * weights['zkp_verification'] +
                result.metrics.parameter_consistency_score * weights['parameter_consistency'] +
                result.metrics.model_quality_score * weights['model_quality'] +
                result.metrics.anomaly_detection_score * weights['anomaly_detection']
            )

            # Bonus/malus por reputación
            reputation_factor = result.metrics.node_reputation_score
            confidence_score = confidence_score * (0.8 + 0.4 * reputation_factor)  # 0.8-1.2

            # Asegurar límites
            confidence_score = max(0.0, min(1.0, confidence_score))

            # Determinar validez
            is_valid = (
                result.signature_verification_passed and
                result.zkp_verification_passed and
                result.parameter_validation_passed and
                result.anomaly_detection_passed and
                confidence_score >= self.verifier_config.min_zkp_confidence_threshold
            )

            return is_valid, confidence_score

        except Exception as e:
            self.logger.error(f"Error evaluando validez general: {e}")
            return False, 0.0

    def _calculate_risk_level(self, confidence_score: float) -> str:
        """Calcula el nivel de riesgo basado en la puntuación de confianza."""
        if confidence_score >= 0.9:
            return "low"
        elif confidence_score >= 0.7:
            return "medium"
        elif confidence_score >= 0.5:
            return "high"
        else:
            return "critical"

    def _generate_recommendations(self, result: VerificationResult) -> List[str]:
        """Genera recomendaciones basadas en el resultado de verificación."""
        recommendations = []

        if not result.is_valid:
            recommendations.append("Rechazar contribución por fallos críticos")

        if result.metrics.zkp_verification_score < 0.8:
            recommendations.append("Mejorar generación de pruebas ZKP")

        if result.metrics.anomaly_detection_score < 0.7:
            recommendations.append("Investigar posibles anomalías en el entrenamiento")

        if result.metrics.node_reputation_score < 0.5:
            recommendations.append("Monitorear comportamiento futuro del nodo")

        if result.risk_level in ["high", "critical"]:
            recommendations.append("Aplicar validación adicional manual")

        if result.metrics.malicious_pattern_score > 0.5:
            recommendations.append("Reportar posible comportamiento malicioso")

        return recommendations

    # Métodos auxiliares para validaciones específicas

    def _calculate_proof_complexity(self, training_proof: Dict[str, Any]) -> float:
        """Calcula la complejidad de una prueba ZKP."""
        complexity = 0.0

        # Contar elementos de prueba
        for proof in [training_proof.data_realness_proof,
                     training_proof.parameter_compliance_proof,
                     training_proof.contribution_validity_proof,
                     training_proof.model_update_proof]:
            if proof and proof.proof_data:
                elements = proof.proof_data.get('proof_elements', [])
                complexity += len(elements)

        return complexity

    def _count_parameters(self, model_parameters: Dict[str, Any]) -> int:
        """Cuenta el número total de parámetros en el modelo."""
        count = 0
        for key, value in model_parameters.items():
            if isinstance(value, (list, tuple)):
                count += len(value)
            elif isinstance(value, dict):
                count += self._count_parameters(value)
            elif isinstance(value, (int, float)):
                count += 1
        return count

    def _check_parameter_values(self, model_parameters: Dict[str, Any]) -> Tuple[int, int]:
        """Verifica valores NaN e infinitos en parámetros."""
        nan_count = 0
        inf_count = 0

        def check_value(val):
            nonlocal nan_count, inf_count
            if isinstance(val, float):
                if math.isnan(val):
                    nan_count += 1
                elif math.isinf(val):
                    inf_count += 1
            elif isinstance(val, (list, tuple)):
                for item in val:
                    check_value(item)
            elif isinstance(val, dict):
                for v in val.values():
                    check_value(v)

        check_value(model_parameters)
        return nan_count, inf_count

    def _check_metadata_consistency(
        self,
        model_parameters: Dict[str, Any],
        training_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verifica consistencia entre parámetros y metadatos."""
        issues = []
        consistent = True

        # Verificar framework
        framework = training_metadata.get('framework', '').lower()
        if framework and 'pytorch' in framework:
            # Verificaciones específicas de PyTorch
            pass  # Implementar verificaciones específicas si es necesario

        # Verificar hardware
        hardware = training_metadata.get('hardware', '').lower()
        if hardware:
            # Verificaciones específicas de hardware
            pass

        return {
            'consistent': consistent,
            'issues': issues
        }

    def _check_session_consistency(
        self,
        model_parameters: Dict[str, Any],
        session_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verifica consistencia con el contexto de sesión."""
        issues = []
        consistent = True

        # Implementar verificaciones de consistencia de sesión
        # Por ejemplo, comparar con estadísticas de otros nodos

        return {
            'consistent': consistent,
            'issues': issues
        }

    def _detect_training_anomalies(
        self,
        training_proof: Dict[str, Any],
        training_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detecta anomalías en el proceso de entrenamiento."""
        detected = False
        issues = []
        severity = 1.0
        malicious_prob = 0.0

        # Verificar tiempos de entrenamiento irrealmente rápidos
        training_time = training_metadata.get('training_time_seconds', 0)
        if training_time < 10:  # Menos de 10 segundos
            detected = True
            issues.append("Tiempo de entrenamiento sospechosamente corto")
            severity *= 0.7
            malicious_prob = 0.3

        # Verificar precisión demasiado perfecta
        final_accuracy = training_metadata.get('final_accuracy', 0.0)
        if final_accuracy > 0.99:  # Precisión > 99%
            detected = True
            issues.append("Precisión de entrenamiento sospechosamente alta")
            severity *= 0.8
            malicious_prob = 0.4

        # Verificar pérdida que no mejora
        loss_improvement = training_metadata.get('loss_improvement', 0.0)
        if loss_improvement <= 0:
            detected = True
            issues.append("Mejora de pérdida insuficiente o negativa")
            severity *= 0.6
            malicious_prob = 0.5

        return {
            'detected': detected,
            'issues': issues,
            'severity': severity,
            'malicious_prob': malicious_prob
        }

    def _detect_parameter_anomalies(self, model_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Detecta anomalías en los parámetros del modelo."""
        detected = False
        issues = []
        severity = 1.0
        poisoning_prob = 0.0

        # Verificar distribución de parámetros
        param_values = self._extract_parameter_values(model_parameters)
        if param_values:
            # Verificar valores extremos
            mean_val = np.mean(param_values)
            std_val = np.std(param_values)

            # Detectar outliers (más de 5 desviaciones estándar)
            outliers = [v for v in param_values if abs(v - mean_val) > 5 * std_val]
            if len(outliers) > len(param_values) * 0.1:  # Más del 10% son outliers
                detected = True
                issues.append("Demasiados valores extremos en parámetros")
                severity *= 0.7
                poisoning_prob = 0.6

            # Verificar si todos los parámetros son iguales (ataque trivial)
            if len(set(param_values[:100])) == 1:  # Primeros 100 son iguales
                detected = True
                issues.append("Parámetros idénticos detectados")
                severity *= 0.5
                poisoning_prob = 0.8

        return {
            'detected': detected,
            'issues': issues,
            'severity': severity,
            'poisoning_prob': poisoning_prob
        }

    def _detect_sybil_patterns(self, node_id: str, session_context: Dict[str, Any]) -> Dict[str, Any]:
        """Detecta patrones de ataque Sybil."""
        detected = False
        issues = []
        severity = 1.0

        # Implementar detección de Sybil basada en patrones de contribución
        # Por ahora, placeholder simple
        return {
            'detected': detected,
            'issues': issues,
            'severity': severity
        }

    def _detect_timestamp_anomalies(
        self,
        training_proof: Dict[str, Any],
        training_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detecta anomalías en timestamps."""
        detected = False
        issues = []

        # Verificar timestamps futuros
        now = datetime.now().timestamp()
        proof_time = training_proof.created_at.timestamp()

        if proof_time > now + 60:  # Más de 1 minuto en el futuro
            detected = True
            issues.append("Timestamp de prueba en el futuro")

        return {
            'detected': detected,
            'issues': issues
        }

    def _calculate_session_consistency(
        self,
        node_id: str,
        session_id: str,
        session_context: Dict[str, Any]
    ) -> float:
        """Calcula consistencia con otras contribuciones de la sesión."""
        # Placeholder - implementar lógica real basada en estadísticas de sesión
        return 0.8

    def _extract_parameter_values(self, model_parameters: Dict[str, Any]) -> List[float]:
        """Extrae valores numéricos de parámetros del modelo."""
        values = []

        def extract_values(obj):
            if isinstance(obj, (int, float)):
                values.append(float(obj))
            elif isinstance(obj, (list, tuple)):
                for item in obj:
                    extract_values(item)
            elif isinstance(obj, dict):
                for v in obj.values():
                    extract_values(v)

        extract_values(model_parameters)
        return values[:10000]  # Limitar para rendimiento

    def _update_verification_stats(self, result: VerificationResult, verification_time: float):
        """Actualiza estadísticas de verificación."""
        self.verification_stats['total_verifications'] += 1

        if result.is_valid:
            self.verification_stats['successful_verifications'] += 1
        else:
            self.verification_stats['failed_verifications'] += 1

        if not result.zkp_verification_passed:
            self.verification_stats['zkp_failures'] += 1

        if not result.parameter_validation_passed:
            self.verification_stats['parameter_failures'] += 1

        if not result.anomaly_detection_passed:
            self.verification_stats['anomaly_detections'] += 1

        # Actualizar tiempo promedio
        current_avg = self.verification_stats['average_verification_time_ms']
        total_count = self.verification_stats['total_verifications']
        self.verification_stats['average_verification_time_ms'] = (
            (current_avg * (total_count - 1)) + verification_time
        ) / total_count

        # Actualizar reputación del nodo
        current_reputation = self.node_reputation[result.node_id]
        if result.is_valid:
            # Aumentar reputación por contribución válida
            self.node_reputation[result.node_id] = min(1.0, current_reputation + 0.1)
        else:
            # Disminuir reputación por contribución inválida
            self.node_reputation[result.node_id] = max(0.0, current_reputation - 0.2)

    def get_verifier_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del verificador."""
        return {
            'verification_stats': self.verification_stats.copy(),
            'node_reputation_summary': {
                'total_nodes': len(self.node_reputation),
                'high_reputation_nodes': len([r for r in self.node_reputation.values() if r >= 0.8]),
                'low_reputation_nodes': len([r for r in self.node_reputation.values() if r < 0.5])
            },
            'cache_stats': {
                'cached_results': len(self.verification_cache)
            }
        }

    async def batch_verify_contributions(
        self,
        contributions: List[Dict[str, Any]]
    ) -> List[VerificationResult]:
        """
        Verifica múltiples contribuciones en lote para mayor eficiencia.

        Args:
            contributions: Lista de diccionarios con datos de contribución

        Returns:
            Lista de resultados de verificación
        """
        if not self.verifier_config.enable_parallel_verification:
            # Verificación secuencial
            results = []
            for contrib in contributions:
                result = await self.verify_contribution(**contrib)
                results.append(result)
            return results

        # Verificación en paralelo con límite de concurrencia
        semaphore = asyncio.Semaphore(self.verifier_config.max_concurrent_verifications)

        async def verify_with_semaphore(contrib):
            async with semaphore:
                return await self.verify_contribution(**contrib)

        tasks = [verify_with_semaphore(contrib) for contrib in contributions]
        return await asyncio.gather(*tasks)

    def clear_cache(self):
        """Limpia la caché de verificaciones."""
        self.verification_cache.clear()
        self.logger.info("Cache de verificaciones limpiada")


# Funciones de conveniencia
def create_contribution_verifier(
    config: Optional[Config] = None,
    verifier_config: Optional[ContributionVerifierConfig] = None
) -> ContributionVerifier:
    """Crea una instancia del verificador de contribuciones."""
    if config is None:
        from ..core.config import Config
        config = Config()
    return ContributionVerifier(config, verifier_config)


async def verify_federated_contribution(
    node_id: str,
    session_id: str,
    round_number: int,
    contribution_id: str,
    training_proof: Dict[str, Any],
    model_parameters: Dict[str, Any],
    training_metadata: Dict[str, Any],
    node_signature: str,
    node_public_key: str,
    verifier_config: Optional[ContributionVerifierConfig] = None
) -> VerificationResult:
    """
    Función de conveniencia para verificar una contribución federada.

    Returns:
        Resultado de verificación
    """
    verifier = create_contribution_verifier(verifier_config=verifier_config)
    return await verifier.verify_contribution(
        node_id=node_id,
        session_id=session_id,
        round_number=round_number,
        contribution_id=contribution_id,
        training_proof=training_proof,
        model_parameters=model_parameters,
        training_metadata=training_metadata,
        node_signature=node_signature,
        node_public_key=node_public_key
    )