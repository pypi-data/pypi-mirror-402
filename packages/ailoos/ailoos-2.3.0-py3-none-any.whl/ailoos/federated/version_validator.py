"""
Version Validator - Validación colectiva de versiones por nodos federados
Sistema de validación distribuida con métricas de calidad y consenso.
"""

import asyncio
import hashlib
import json
import time
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import torch
import torch.nn as nn

from ..core.logging import get_logger
from .federated_version_manager import FederatedVersionManager, ModelVersion, ValidationStatus

logger = get_logger(__name__)


class ValidationType(Enum):
    """Tipos de validación disponibles."""
    INTEGRITY = "integrity"  # Verificación de hashes
    PERFORMANCE = "performance"  # Métricas de rendimiento
    COMPATIBILITY = "compatibility"  # Compatibilidad con datos
    SECURITY = "security"  # Verificación de seguridad
    CONSISTENCY = "consistency"  # Consistencia interna


@dataclass
class ValidationResult:
    """Resultado de una validación específica."""
    validation_type: ValidationType
    status: ValidationStatus
    score: float  # 0.0 a 1.0
    details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time: float = 0.0
    timestamp: int = field(default_factory=lambda: int(time.time()))

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            'validation_type': self.validation_type.value,
            'status': self.status.value,
            'score': self.score,
            'details': self.details,
            'error_message': self.error_message,
            'execution_time': self.execution_time,
            'timestamp': self.timestamp
        }


@dataclass
class NodeValidationReport:
    """Reporte completo de validación de un nodo."""
    node_id: str
    version_id: str
    validations: List[ValidationResult] = field(default_factory=list)
    overall_score: float = 0.0
    overall_status: ValidationStatus = ValidationStatus.PENDING
    submitted_at: int = field(default_factory=lambda: int(time.time()))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def calculate_overall_score(self):
        """Calcular puntuación general."""
        if not self.validations:
            self.overall_score = 0.0
            return

        # Ponderación por tipo de validación
        weights = {
            ValidationType.INTEGRITY: 0.3,
            ValidationType.PERFORMANCE: 0.3,
            ValidationType.COMPATIBILITY: 0.2,
            ValidationType.SECURITY: 0.15,
            ValidationType.CONSISTENCY: 0.05
        }

        total_weight = 0.0
        weighted_score = 0.0

        for validation in self.validations:
            weight = weights.get(validation.validation_type, 0.1)
            weighted_score += validation.score * weight
            total_weight += weight

        self.overall_score = weighted_score / total_weight if total_weight > 0 else 0.0

        # Determinar estado general
        if all(v.status == ValidationStatus.APPROVED for v in self.validations):
            self.overall_status = ValidationStatus.APPROVED
        elif any(v.status == ValidationStatus.REJECTED for v in self.validations):
            self.overall_status = ValidationStatus.REJECTED
        else:
            self.overall_status = ValidationStatus.CONFLICT


class VersionValidator:
    """
    Validador colectivo de versiones para el sistema federado.
    Coordina validaciones distribuidas por múltiples nodos.
    """

    def __init__(self, version_manager: FederatedVersionManager,
                 validation_timeout_seconds: int = 3600,
                 min_validation_score: float = 0.7):
        """
        Inicializar el validador de versiones.

        Args:
            version_manager: Gestor de versiones federadas
            validation_timeout_seconds: Timeout para validaciones
            min_validation_score: Puntuación mínima requerida
        """
        self.version_manager = version_manager
        self.validation_timeout = validation_timeout_seconds
        self.min_score = min_validation_score

        # Estado de validaciones
        self.validation_reports: Dict[str, Dict[str, NodeValidationReport]] = {}  # version_id -> node_id -> report
        self.active_validations: Dict[str, asyncio.Task] = {}

        # Validadores registrados
        self.validators: Dict[ValidationType, Callable] = {}

        # Locks para concurrencia
        self.validation_lock = asyncio.Lock()

        # Registrar validadores por defecto
        self._register_default_validators()

        logger.info("🚀 VersionValidator initialized")

    def _register_default_validators(self):
        """Registrar validadores por defecto."""
        self.register_validator(ValidationType.INTEGRITY, self._validate_integrity)
        self.register_validator(ValidationType.PERFORMANCE, self._validate_performance)
        self.register_validator(ValidationType.COMPATIBILITY, self._validate_compatibility)
        self.register_validator(ValidationType.SECURITY, self._validate_security)
        self.register_validator(ValidationType.CONSISTENCY, self._validate_consistency)

    def register_validator(self, validation_type: ValidationType, validator_func: Callable):
        """
        Registrar una función validadora personalizada.

        Args:
            validation_type: Tipo de validación
            validator_func: Función que toma (model_data, metadata, node_context) y retorna ValidationResult
        """
        self.validators[validation_type] = validator_func
        logger.info(f"📝 Registered validator for {validation_type.value}")

    async def start_validation(self, version_id: str, node_ids: List[str]) -> bool:
        """
        Iniciar proceso de validación colectiva para una versión.

        Args:
            version_id: ID de la versión a validar
            node_ids: IDs de nodos participantes

        Returns:
            True si la validación se inició correctamente
        """
        async with self.validation_lock:
            try:
                # Verificar que la versión existe
                version = await self.version_manager.get_version(version_id)
                if not version:
                    raise ValueError(f"Version {version_id} not found")

                # Inicializar estructura de validación
                if version_id not in self.validation_reports:
                    self.validation_reports[version_id] = {}

                # Crear tarea de validación colectiva
                task = asyncio.create_task(self._run_collective_validation(version_id, node_ids))
                self.active_validations[version_id] = task

                logger.info(f"🎯 Started collective validation for {version_id} with {len(node_ids)} nodes")
                return True

            except Exception as e:
                logger.error(f"❌ Failed to start validation for {version_id}: {e}")
                return False

    async def submit_node_validation(self, version_id: str, node_id: str,
                                   validation_results: List[ValidationResult],
                                   node_context: Dict[str, Any] = None) -> bool:
        """
        Enviar resultados de validación desde un nodo.

        Args:
            version_id: ID de la versión
            node_id: ID del nodo
            validation_results: Resultados de validaciones
            node_context: Contexto adicional del nodo

        Returns:
            True si se aceptó el reporte
        """
        async with self.validation_lock:
            try:
                # Crear reporte del nodo
                report = NodeValidationReport(
                    node_id=node_id,
                    version_id=version_id,
                    validations=validation_results,
                    metadata=node_context or {}
                )

                # Calcular puntuación general
                report.calculate_overall_score()

                # Almacenar reporte
                if version_id not in self.validation_reports:
                    self.validation_reports[version_id] = {}
                self.validation_reports[version_id][node_id] = report

                # Enviar voto al version manager
                await self.version_manager.submit_validation_vote(
                    version_id=version_id,
                    node_id=node_id,
                    vote=report.overall_status,
                    reason=f"Validation score: {report.overall_score:.2f}"
                )

                logger.info(f"📨 Received validation report from {node_id} for {version_id}: score={report.overall_score:.2f}")
                return True

            except Exception as e:
                logger.error(f"❌ Failed to submit validation from {node_id}: {e}")
                return False

    async def _run_collective_validation(self, version_id: str, node_ids: List[str]):
        """Ejecutar validación colectiva con timeout."""
        try:
            # Esperar validaciones con timeout
            await asyncio.wait_for(
                self._wait_for_validations(version_id, node_ids),
                timeout=self.validation_timeout
            )

            # Procesar resultados finales
            await self._finalize_validation(version_id)

        except asyncio.TimeoutError:
            logger.warning(f"⏰ Validation timeout for {version_id}")
            await self._handle_validation_timeout(version_id)
        except Exception as e:
            logger.error(f"❌ Collective validation failed for {version_id}: {e}")

    async def _wait_for_validations(self, version_id: str, node_ids: List[str]):
        """Esperar a que todos los nodos envíen sus validaciones."""
        required_validations = len(node_ids)
        received_validations = 0

        while received_validations < required_validations:
            await asyncio.sleep(1)  # Polling interval

            current_reports = self.validation_reports.get(version_id, {})
            received_validations = len(current_reports)

            # Log progreso
            if received_validations > 0 and received_validations % 5 == 0:
                logger.info(f"📊 Validation progress for {version_id}: {received_validations}/{required_validations}")

    async def _finalize_validation(self, version_id: str):
        """Finalizar proceso de validación."""
        reports = self.validation_reports.get(version_id, {})

        if not reports:
            logger.warning(f"No validation reports received for {version_id}")
            return

        # Calcular estadísticas
        scores = [report.overall_score for report in reports.values()]
        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)

        approved_count = sum(1 for r in reports.values() if r.overall_status == ValidationStatus.APPROVED)
        rejected_count = sum(1 for r in reports.values() if r.overall_status == ValidationStatus.REJECTED)

        logger.info(f"✅ Validation finalized for {version_id}:")
        logger.info(f"   📊 Average score: {avg_score:.2f}")
        logger.info(f"   📈 Score range: {min_score:.2f} - {max_score:.2f}")
        logger.info(f"   👍 Approved: {approved_count}, 👎 Rejected: {rejected_count}")

        # Limpiar tarea activa
        if version_id in self.active_validations:
            del self.active_validations[version_id]

    async def _handle_validation_timeout(self, version_id: str):
        """Manejar timeout de validación."""
        # Rechazar automáticamente versiones sin suficientes validaciones
        await self.version_manager.deprecate_version(
            version_id,
            reason="Validation timeout - insufficient validations received"
        )

        # Limpiar estado
        if version_id in self.validation_reports:
            del self.validation_reports[version_id]
        if version_id in self.active_validations:
            del self.active_validations[version_id]

    async def _validate_integrity(self, model_data: bytes, metadata: Dict[str, Any],
                                node_context: Dict[str, Any]) -> ValidationResult:
        """Validar integridad del modelo."""
        start_time = time.time()

        try:
            # Verificar hash del modelo
            calculated_hash = hashlib.sha256(model_data).hexdigest()
            expected_hash = metadata.get('model_hash', '')

            if calculated_hash != expected_hash:
                return ValidationResult(
                    validation_type=ValidationType.INTEGRITY,
                    status=ValidationStatus.REJECTED,
                    score=0.0,
                    error_message=f"Model hash mismatch: {calculated_hash} != {expected_hash}",
                    execution_time=time.time() - start_time
                )

            # Verificar hash de configuración
            config_hash = hashlib.sha256(json.dumps(metadata.get('config', {}), sort_keys=True).encode()).hexdigest()
            expected_config_hash = metadata.get('config_hash', '')

            if config_hash != expected_config_hash:
                return ValidationResult(
                    validation_type=ValidationType.INTEGRITY,
                    status=ValidationStatus.REJECTED,
                    score=0.5,
                    error_message=f"Config hash mismatch: {config_hash} != {expected_config_hash}",
                    execution_time=time.time() - start_time
                )

            return ValidationResult(
                validation_type=ValidationType.INTEGRITY,
                status=ValidationStatus.APPROVED,
                score=1.0,
                details={'model_hash': calculated_hash, 'config_hash': config_hash},
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return ValidationResult(
                validation_type=ValidationType.INTEGRITY,
                status=ValidationStatus.REJECTED,
                score=0.0,
                error_message=str(e),
                execution_time=time.time() - start_time
            )

    async def _validate_performance(self, model_data: bytes, metadata: Dict[str, Any],
                                  node_context: Dict[str, Any]) -> ValidationResult:
        """Validar rendimiento del modelo."""
        start_time = time.time()

        try:
            # Obtener métricas de calidad del metadata
            quality_metrics = metadata.get('quality_metrics', {})

            # Verificar métricas mínimas requeridas
            required_metrics = ['accuracy', 'loss', 'perplexity']
            missing_metrics = [m for m in required_metrics if m not in quality_metrics]

            if missing_metrics:
                return ValidationResult(
                    validation_type=ValidationType.PERFORMANCE,
                    status=ValidationStatus.REJECTED,
                    score=0.0,
                    error_message=f"Missing required metrics: {missing_metrics}",
                    execution_time=time.time() - start_time
                )

            # Evaluar métricas
            accuracy = quality_metrics.get('accuracy', 0.0)
            loss = quality_metrics.get('loss', float('inf'))
            perplexity = quality_metrics.get('perplexity', float('inf'))

            # Calcular puntuación basada en thresholds
            accuracy_score = min(1.0, accuracy / 0.9)  # Esperamos al menos 90% accuracy
            loss_score = max(0.0, 1.0 - (loss / 5.0))  # Loss máximo esperado 5.0
            perplexity_score = max(0.0, 1.0 - (perplexity / 50.0))  # Perplexity máxima 50

            overall_score = (accuracy_score + loss_score + perplexity_score) / 3.0

            status = ValidationStatus.APPROVED if overall_score >= self.min_score else ValidationStatus.REJECTED

            return ValidationResult(
                validation_type=ValidationType.PERFORMANCE,
                status=status,
                score=overall_score,
                details={
                    'accuracy': accuracy,
                    'loss': loss,
                    'perplexity': perplexity,
                    'accuracy_score': accuracy_score,
                    'loss_score': loss_score,
                    'perplexity_score': perplexity_score
                },
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return ValidationResult(
                validation_type=ValidationType.PERFORMANCE,
                status=ValidationStatus.REJECTED,
                score=0.0,
                error_message=str(e),
                execution_time=time.time() - start_time
            )

    async def _validate_compatibility(self, model_data: bytes, metadata: Dict[str, Any],
                                    node_context: Dict[str, Any]) -> ValidationResult:
        """Validar compatibilidad del modelo."""
        start_time = time.time()

        try:
            # Verificar información federada
            federated_info = metadata.get('federated_info', {})

            # Verificar que tenga información de federated learning
            if not federated_info:
                return ValidationResult(
                    validation_type=ValidationType.COMPATIBILITY,
                    status=ValidationStatus.REJECTED,
                    score=0.0,
                    error_message="Missing federated learning information",
                    execution_time=time.time() - start_time
                )

            # Verificar métricas de compatibilidad
            participants = federated_info.get('participants', 0)
            total_samples = federated_info.get('total_samples', 0)
            rounds = federated_info.get('rounds', 0)

            # Calcular score basado en participación
            participation_score = min(1.0, participants / 10.0)  # Ideal: al menos 10 participantes
            sample_score = min(1.0, total_samples / 100000.0)  # Ideal: al menos 100k samples
            round_score = min(1.0, rounds / 5.0)  # Ideal: al menos 5 rondas

            overall_score = (participation_score + sample_score + round_score) / 3.0

            status = ValidationStatus.APPROVED if overall_score >= 0.5 else ValidationStatus.REJECTED

            return ValidationResult(
                validation_type=ValidationType.COMPATIBILITY,
                status=status,
                score=overall_score,
                details={
                    'participants': participants,
                    'total_samples': total_samples,
                    'rounds': rounds,
                    'participation_score': participation_score,
                    'sample_score': sample_score,
                    'round_score': round_score
                },
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return ValidationResult(
                validation_type=ValidationType.COMPATIBILITY,
                status=ValidationStatus.REJECTED,
                score=0.0,
                error_message=str(e),
                execution_time=time.time() - start_time
            )

    async def _validate_security(self, model_data: bytes, metadata: Dict[str, Any],
                               node_context: Dict[str, Any]) -> ValidationResult:
        """Validar aspectos de seguridad."""
        start_time = time.time()

        try:
            # Verificar tamaño del modelo (no demasiado grande)
            model_size_mb = len(model_data) / (1024 * 1024)
            if model_size_mb > 500:  # Máximo 500MB
                return ValidationResult(
                    validation_type=ValidationType.SECURITY,
                    status=ValidationStatus.REJECTED,
                    score=0.0,
                    error_message=f"Model too large: {model_size_mb:.1f}MB > 500MB limit",
                    execution_time=time.time() - start_time
                )

            # Verificar que no contenga código ejecutable obvio
            # (Esto es una verificación básica; en producción se necesitaría más análisis)
            if b'exec(' in model_data or b'eval(' in model_data:
                return ValidationResult(
                    validation_type=ValidationType.SECURITY,
                    status=ValidationStatus.REJECTED,
                    score=0.0,
                    error_message="Potentially unsafe code detected in model",
                    execution_time=time.time() - start_time
                )

            # Verificar metadatos de privacidad
            privacy_budget = metadata.get('federated_info', {}).get('privacy_budget_used', 1.0)
            if privacy_budget > 1.0:
                return ValidationResult(
                    validation_type=ValidationType.SECURITY,
                    status=ValidationStatus.REJECTED,
                    score=0.0,
                    error_message=f"Privacy budget exceeded: {privacy_budget} > 1.0",
                    execution_time=time.time() - start_time
                )

            return ValidationResult(
                validation_type=ValidationType.SECURITY,
                status=ValidationStatus.APPROVED,
                score=1.0,
                details={
                    'model_size_mb': model_size_mb,
                    'privacy_budget': privacy_budget
                },
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return ValidationResult(
                validation_type=ValidationType.SECURITY,
                status=ValidationStatus.REJECTED,
                score=0.0,
                error_message=str(e),
                execution_time=time.time() - start_time
            )

    async def _validate_consistency(self, model_data: bytes, metadata: Dict[str, Any],
                                  node_context: Dict[str, Any]) -> ValidationResult:
        """Validar consistencia interna del modelo."""
        start_time = time.time()

        try:
            # Intentar cargar el modelo para verificar consistencia
            try:
                # Esto es un placeholder - en producción se necesitaría el framework específico
                # Por ahora solo verificamos que los datos no estén corruptos
                if len(model_data) == 0:
                    raise ValueError("Empty model data")

                # Verificar que sea un archivo pickle/torch válido (básico)
                if model_data.startswith(b'\x80'):  # Pickle protocol
                    pass  # Podría ser un modelo PyTorch
                elif b'torch' in model_data[:100]:  # Contiene 'torch'
                    pass  # Probablemente un modelo PyTorch
                else:
                    return ValidationResult(
                        validation_type=ValidationType.CONSISTENCY,
                        status=ValidationStatus.REJECTED,
                        score=0.5,
                        error_message="Unrecognized model format",
                        execution_time=time.time() - start_time
                    )

            except Exception as load_error:
                return ValidationResult(
                    validation_type=ValidationType.CONSISTENCY,
                    status=ValidationStatus.REJECTED,
                    score=0.0,
                    error_message=f"Model loading failed: {str(load_error)}",
                    execution_time=time.time() - start_time
                )

            return ValidationResult(
                validation_type=ValidationType.CONSISTENCY,
                status=ValidationStatus.APPROVED,
                score=1.0,
                details={'model_size': len(model_data)},
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return ValidationResult(
                validation_type=ValidationType.CONSISTENCY,
                status=ValidationStatus.REJECTED,
                score=0.0,
                error_message=str(e),
                execution_time=time.time() - start_time
            )

    async def get_validation_report(self, version_id: str, node_id: Optional[str] = None) -> Dict[str, Any]:
        """Obtener reporte de validación."""
        if version_id not in self.validation_reports:
            raise ValueError(f"No validation reports for version {version_id}")

        reports = self.validation_reports[version_id]

        if node_id:
            if node_id not in reports:
                raise ValueError(f"No validation report from node {node_id} for version {version_id}")
            report = reports[node_id]
            return {
                'version_id': version_id,
                'node_id': node_id,
                'overall_score': report.overall_score,
                'overall_status': report.overall_status.value,
                'validations': [v.to_dict() for v in report.validations],
                'submitted_at': report.submitted_at,
                'metadata': report.metadata
            }

        # Reporte agregado
        all_scores = [r.overall_score for r in reports.values()]
        return {
            'version_id': version_id,
            'total_reports': len(reports),
            'average_score': sum(all_scores) / len(all_scores) if all_scores else 0.0,
            'min_score': min(all_scores) if all_scores else 0.0,
            'max_score': max(all_scores) if all_scores else 0.0,
            'node_reports': {nid: r.overall_score for nid, r in reports.items()}
        }

    async def run_node_validation(self, version_id: str, node_id: str,
                                node_context: Dict[str, Any] = None) -> List[ValidationResult]:
        """
        Ejecutar todas las validaciones en un nodo específico.

        Args:
            version_id: ID de la versión
            node_id: ID del nodo
            node_context: Contexto del nodo

        Returns:
            Lista de resultados de validación
        """
        try:
            # Obtener datos de la versión
            version = await self.version_manager.get_version(version_id)
            if not version:
                raise ValueError(f"Version {version_id} not found")

            # Descargar modelo desde IPFS
            model_data = await self.version_manager.ipfs_manager.get_data(version.model_cid)
            metadata = await self.version_manager.ipfs_manager.get_data(version.metadata_cid)
            metadata = json.loads(metadata.decode())

            # Ejecutar todas las validaciones
            validation_results = []
            for validation_type, validator_func in self.validators.items():
                try:
                    result = await validator_func(model_data, metadata, node_context or {})
                    validation_results.append(result)
                    logger.debug(f"✅ {validation_type.value} validation completed: {result.status.value} ({result.score:.2f})")
                except Exception as e:
                    logger.error(f"❌ {validation_type.value} validation failed: {e}")
                    # Crear resultado de error
                    error_result = ValidationResult(
                        validation_type=validation_type,
                        status=ValidationStatus.REJECTED,
                        score=0.0,
                        error_message=str(e),
                        execution_time=0.0
                    )
                    validation_results.append(error_result)

            return validation_results

        except Exception as e:
            logger.error(f"❌ Node validation failed for {node_id}: {e}")
            raise