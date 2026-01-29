"""
Módulo de reporting de trabajo para integración Ailoos-DracmaS.

Proporciona funcionalidades para reportar unidades de trabajo de entrenamiento,
manejar reportes por lotes y validación automática de trabajo.
"""

import asyncio
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import time

from .bridge_client import get_bridge_client, BridgeClient, BridgeClientError
from .dracmas_config import get_dracmas_config, DracmaSConfig
from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class WorkReport:
    """Reporte de trabajo de entrenamiento."""
    node_id: str
    units: int
    dataset_id: str
    timestamp: int
    proof_hash: Optional[str] = None
    validated: bool = False


@dataclass
class BatchWorkReport:
    """Reporte por lotes de trabajo."""
    reports: List[WorkReport]
    batch_id: str
    total_units: int
    submitted_at: int


class WorkReportingError(Exception):
    """Error en operaciones de reporting de trabajo."""
    pass


class WorkReportingManager:
    """
    Gestor de reporting de trabajo para integración Ailoos-DracmaS.

    Maneja el reporte de unidades de trabajo, validación de proofs
    y operaciones por lotes a través del puente cross-chain.
    """

    def __init__(self, bridge_client: Optional[BridgeClient] = None):
        """
        Inicializar gestor de reporting.

        Args:
            bridge_client: Cliente del puente opcional
        """
        self.bridge_client = bridge_client or get_bridge_client()
        self.config = get_dracmas_config()
        logger.info("🔗 WorkReportingManager initialized")

    async def report_training_work(
        self,
        node_id: str,
        units: int,
        dataset_id: str,
        proof_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reportar unidades de trabajo de entrenamiento.

        Args:
            node_id: ID del nodo que realizó el trabajo
            units: Unidades de trabajo realizadas
            dataset_id: ID del dataset usado
            proof_hash: Hash del proof de trabajo (opcional)

        Returns:
            Resultado del reporte

        Raises:
            WorkReportingError: Si hay error en el reporte
        """
        try:
            # Validar parámetros
            self._validate_work_report(node_id, units, dataset_id)

            logger.info(f"📊 Reporting {units} work units for node {node_id} on dataset {dataset_id}")

            # Reportar vía puente
            result = await self.bridge_client.report_work(
                node_id=node_id,
                units=units
            )

            if result.get('success'):
                logger.info(f"✅ Work reported successfully: {units} units for node {node_id}")

                # Crear objeto de reporte para retorno
                report = WorkReport(
                    node_id=node_id,
                    units=units,
                    dataset_id=dataset_id,
                    timestamp=int(time.time()),
                    proof_hash=proof_hash,
                    validated=True
                )

                return {
                    "success": True,
                    "report": report,
                    "transaction_hash": result.get('tx_hash'),
                    "message": "Work reported successfully"
                }
            else:
                error_msg = result.get('error', 'Unknown reporting error')
                logger.error(f"❌ Failed to report work for node {node_id}: {error_msg}")
                raise WorkReportingError(f"Reporting failed: {error_msg}")

        except BridgeClientError as e:
            logger.error(f"❌ Bridge error reporting work for node {node_id}: {e}")
            raise WorkReportingError(f"Bridge communication error: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error reporting work for node {node_id}: {e}")
            raise WorkReportingError(f"Unexpected error: {e}")

    async def batch_report_work(
        self,
        work_reports: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Reportar múltiples sesiones de trabajo en lote.

        Args:
            work_reports: Lista de reportes de trabajo
                Cada reporte debe tener: node_id, units, dataset_id, proof_hash (opcional)

        Returns:
            Resultado del reporte por lotes

        Raises:
            WorkReportingError: Si hay error en el reporte por lotes
        """
        try:
            if not work_reports:
                raise WorkReportingError("Work reports list cannot be empty")

            if len(work_reports) > 100:  # Límite razonable
                raise WorkReportingError("Maximum 100 work reports per batch")

            # Validar todos los reportes
            validated_reports = []
            total_units = 0

            for i, report_data in enumerate(work_reports):
                try:
                    node_id = report_data['node_id']
                    units = report_data['units']
                    dataset_id = report_data['dataset_id']
                    proof_hash = report_data.get('proof_hash')

                    self._validate_work_report(node_id, units, dataset_id)
                    validated_reports.append((node_id, units, dataset_id, proof_hash))
                    total_units += units
                except KeyError as e:
                    raise WorkReportingError(f"Missing required field in report {i}: {e}")
                except Exception as e:
                    raise WorkReportingError(f"Invalid report {i}: {e}")

            logger.info(f"📦 Batch reporting {len(validated_reports)} work sessions, total {total_units} units")

            # Procesar reportes en lotes (simulado - en producción usaría endpoint batch)
            successful_reports = []
            failed_reports = []

            for node_id, units, dataset_id, proof_hash in validated_reports:
                try:
                    result = await self.report_training_work(node_id, units, dataset_id, proof_hash)
                    successful_reports.append(result['report'])
                except Exception as e:
                    logger.warning(f"Failed to report work for node {node_id}: {e}")
                    failed_reports.append({
                        'node_id': node_id,
                        'units': units,
                        'dataset_id': dataset_id,
                        'error': str(e)
                    })

            batch_report = BatchWorkReport(
                reports=successful_reports,
                batch_id=f"batch_{int(time.time())}_{len(work_reports)}",
                total_units=sum(r.units for r in successful_reports),
                submitted_at=int(time.time())
            )

            result = {
                "success": len(successful_reports) > 0,
                "batch_report": batch_report,
                "successful_count": len(successful_reports),
                "failed_count": len(failed_reports),
                "failed_reports": failed_reports,
                "message": f"Batch reporting completed: {len(successful_reports)} successful, {len(failed_reports)} failed"
            }

            logger.info(f"✅ Batch reporting completed: {len(successful_reports)}/{len(work_reports)} successful")
            return result

        except Exception as e:
            logger.error(f"❌ Unexpected error in batch reporting: {e}")
            raise WorkReportingError(f"Batch reporting error: {e}")

    async def validate_and_report(
        self,
        node_id: str,
        units: int,
        dataset_id: str,
        proof: bytes,
        model_hash: str,
        expected_accuracy: str
    ) -> Dict[str, Any]:
        """
        Validar proof y reportar trabajo automáticamente.

        Args:
            node_id: ID del nodo
            units: Unidades de trabajo
            dataset_id: ID del dataset
            proof: Proof de entrenamiento (bytes)
            model_hash: Hash del modelo resultante
            expected_accuracy: Precisión esperada

        Returns:
            Resultado de validación y reporte

        Raises:
            WorkReportingError: Si hay error en validación o reporte
        """
        try:
            # Validar parámetros
            self._validate_work_report(node_id, units, dataset_id)
            self._validate_proof_data(proof, model_hash, expected_accuracy)

            logger.info(f"🔍 Validating and reporting work for node {node_id} on dataset {dataset_id}")

            # Validar proof vía puente
            validation_result = await self.bridge_client.validate_proof(
                node_id=node_id,
                dataset_id=dataset_id,
                compute_power=units,  # Usar units como poder computacional
                proof=proof,
                model_hash=model_hash,
                expected_accuracy=expected_accuracy
            )

            if not validation_result.get('success'):
                error_msg = validation_result.get('error', 'Proof validation failed')
                logger.error(f"❌ Proof validation failed for node {node_id}: {error_msg}")
                raise WorkReportingError(f"Proof validation failed: {error_msg}")

            # Si validación exitosa, reportar trabajo
            report_result = await self.report_training_work(
                node_id=node_id,
                units=units,
                dataset_id=dataset_id,
                proof_hash=model_hash
            )

            result = {
                "success": True,
                "validation_result": validation_result,
                "report_result": report_result,
                "message": "Proof validated and work reported successfully"
            }

            logger.info(f"✅ Proof validated and work reported for node {node_id}")
            return result

        except BridgeClientError as e:
            logger.error(f"❌ Bridge error in validate_and_report for node {node_id}: {e}")
            raise WorkReportingError(f"Bridge communication error: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error in validate_and_report for node {node_id}: {e}")
            raise WorkReportingError(f"Unexpected error: {e}")

    def _validate_work_report(self, node_id: str, units: int, dataset_id: str):
        """Validar datos de reporte de trabajo."""
        if not isinstance(node_id, str) or not node_id.strip():
            raise WorkReportingError("Node ID must be a non-empty string")
        if not isinstance(units, int) or units <= 0:
            raise WorkReportingError("Units must be a positive integer")
        if not isinstance(dataset_id, str) or not dataset_id.strip():
            raise WorkReportingError("Dataset ID must be a non-empty string")

    def _validate_proof_data(self, proof: bytes, model_hash: str, expected_accuracy: str):
        """Validar datos del proof."""
        if not isinstance(proof, bytes) or len(proof) == 0:
            raise WorkReportingError("Proof must be non-empty bytes")
        if not isinstance(model_hash, str) or not model_hash.strip():
            raise WorkReportingError("Model hash must be a non-empty string")
        if not isinstance(expected_accuracy, str) or not expected_accuracy.strip():
            raise WorkReportingError("Expected accuracy must be a non-empty string")


# Instancia global del gestor
_work_reporting_manager: Optional[WorkReportingManager] = None


def get_work_reporting_manager() -> WorkReportingManager:
    """Obtener instancia global del gestor de reporting de trabajo."""
    global _work_reporting_manager
    if _work_reporting_manager is None:
        _work_reporting_manager = WorkReportingManager()
    return _work_reporting_manager


def create_work_reporting_manager(bridge_client: Optional[BridgeClient] = None) -> WorkReportingManager:
    """Crear nueva instancia del gestor de reporting de trabajo."""
    return WorkReportingManager(bridge_client)