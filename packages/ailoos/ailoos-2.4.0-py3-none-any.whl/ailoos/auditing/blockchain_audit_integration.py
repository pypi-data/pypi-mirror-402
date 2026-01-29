"""
Integración completa del sistema de auditoría blockchain para AILOOS.
Coordina todos los componentes para proporcionar auditoría inmutable y compliance.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import threading
import time

from .blockchain_auditor import get_blockchain_auditor
from .hash_chain_manager import get_hash_chain_manager
from .audit_smart_contracts import get_smart_contract_manager
from .immutable_log_storage import get_immutable_log_storage, LogEntry
from .compliance_reporter import get_compliance_reporter
from ..core.logging import get_logger

logger = get_logger(__name__)


class BlockchainAuditIntegration:
    """
    Integración completa del sistema de auditoría blockchain.
    Coordina todos los componentes para operaciones de auditoría unificadas.
    """

    def __init__(self):
        self.blockchain_auditor = get_blockchain_auditor()
        self.hash_chain_manager = get_hash_chain_manager()
        self.smart_contract_manager = get_smart_contract_manager()
        self.immutable_storage = get_immutable_log_storage()
        self.compliance_reporter = get_compliance_reporter()

        self.monitoring_active = False
        self.monitoring_thread = None

        logger.info("🔗 BlockchainAuditIntegration initialized")

    async def audit_operation(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa una operación crítica a través de todo el sistema de auditoría.

        Args:
            operation: Operación a auditar

        Returns:
            Resultado completo de la auditoría
        """
        operation_id = operation.get("operation_id", f"op_{int(datetime.now().timestamp())}")
        start_time = time.time()

        logger.info(f"🔍 Starting comprehensive audit for operation: {operation_id}")

        # 1. Ejecutar validación de smart contracts
        contract_results = await self.smart_contract_manager.execute_all_contracts(operation)

        # 2. Registrar en blockchain si validación pasa
        blockchain_registered = False
        blockchain_hash = None

        validation_passed = all(exec_result.success for exec_result in contract_results)

        if validation_passed:
            from .blockchain_auditor import AuditOperation
            audit_op = AuditOperation(
                operation_id=operation_id,
                operation_type=operation.get("operation_type", "unknown"),
                user_id=operation.get("user_id", "system"),
                timestamp=operation.get("timestamp", datetime.now().timestamp()),
                data=operation.get("data", {}),
                compliance_flags=[event.get("event", "") for exec in contract_results
                                for event in exec.events]
            )

            blockchain_hash = await self.blockchain_auditor.add_operation(audit_op)
            blockchain_registered = blockchain_hash != "pending"

        # 3. Registrar en hash chain apropiada
        chain_type = operation.get("operation_type", "general")
        hash_entry_id = self.hash_chain_manager.add_log_entry(f"operation_{chain_type}", operation)

        # 4. Almacenar log inmutable
        log_entry = LogEntry(
            log_id=f"log_{operation_id}",
            log_type="operation_audit",
            timestamp=datetime.now(),
            user_id=operation.get("user_id"),
            operation_type=operation.get("operation_type", "unknown"),
            data=operation,
            compliance_status="compliant" if validation_passed else "non_compliant"
        )

        try:
            self.immutable_storage.store_log(log_entry)
            storage_registered = True
        except Exception as e:
            logger.error(f"Failed to store immutable log for {operation_id}: {e}")
            storage_registered = False

        # 5. Actualizar estado de compliance en log si fue registrado en blockchain
        if blockchain_registered and blockchain_hash:
            self.immutable_storage.update_compliance_status(
                f"log_{operation_id}",
                "compliant" if validation_passed else "non_compliant",
                blockchain_hash
            )

        # 6. Preparar resultado completo
        processing_time = time.time() - start_time

        result = {
            "operation_id": operation_id,
            "audit_timestamp": datetime.now().isoformat(),
            "processing_time_seconds": round(processing_time, 3),
            "validation_passed": validation_passed,
            "blockchain_registered": blockchain_registered,
            "blockchain_hash": blockchain_hash,
            "hash_chain_entry": hash_entry_id,
            "storage_registered": storage_registered,
            "contract_validations": [
                {
                    "contract_id": exec.contract_id,
                    "success": exec.success,
                    "result": exec.result,
                    "gas_used": exec.gas_used,
                    "events": exec.events
                }
                for exec in contract_results
            ],
            "overall_status": "success" if (validation_passed and blockchain_registered and storage_registered) else "partial_failure"
        }

        logger.info(f"✅ Comprehensive audit completed for {operation_id} in {processing_time:.3f}s: {result['overall_status']}")

        return result

    async def validate_system_integrity(self) -> Dict[str, Any]:
        """
        Valida la integridad de todo el sistema de auditoría.

        Returns:
            Estado de integridad del sistema
        """
        logger.info("🔍 Validating system integrity")

        integrity_checks = {}

        # Verificar blockchain
        blockchain_valid = self.blockchain_auditor.validate_chain()
        blockchain_info = self.blockchain_auditor.get_chain_info()
        integrity_checks["blockchain"] = {
            "valid": blockchain_valid,
            "total_blocks": blockchain_info["total_blocks"],
            "total_operations": blockchain_info["total_operations"]
        }

        # Verificar hash chains
        hash_chains_valid = self.hash_chain_manager.verify_all_chains()
        integrity_checks["hash_chains"] = {
            "valid": all(hash_chains_valid.values()),
            "chains_status": hash_chains_valid,
            "total_chains": len(hash_chains_valid)
        }

        # Verificar almacenamiento inmutable
        storage_integrity = self.immutable_storage.verify_all_logs_integrity()
        integrity_checks["immutable_storage"] = storage_integrity

        # Estado general
        all_valid = (
            blockchain_valid and
            all(hash_chains_valid.values()) and
            storage_integrity.get("integrity_percentage", 0) == 100
        )

        result = {
            "timestamp": datetime.now().isoformat(),
            "overall_integrity": all_valid,
            "integrity_checks": integrity_checks,
            "recommendations": []
        }

        if not all_valid:
            result["recommendations"] = self._generate_integrity_recommendations(integrity_checks)

        logger.info(f"🔍 System integrity validation: {'PASS' if all_valid else 'FAIL'}")

        return result

    def _generate_integrity_recommendations(self, integrity_checks: Dict) -> List[str]:
        """Genera recomendaciones basadas en fallos de integridad."""
        recommendations = []

        if not integrity_checks["blockchain"]["valid"]:
            recommendations.append("CRITICAL: Blockchain integrity compromised - investigate immediately")

        hash_chains = integrity_checks["hash_chains"]
        if not hash_chains["valid"]:
            invalid_chains = [cid for cid, valid in hash_chains["chains_status"].items() if not valid]
            recommendations.append(f"Hash chain integrity issues in: {', '.join(invalid_chains)}")

        storage = integrity_checks["immutable_storage"]
        invalid_logs = storage.get("invalid_logs", 0)
        if invalid_logs > 0:
            recommendations.append(f"Storage integrity issues: {invalid_logs} corrupted logs detected")

        if not recommendations:
            recommendations.append("System integrity is valid")

        return recommendations

    async def generate_compliance_report(self, report_type: str = "weekly",
                                       days: int = 7) -> Dict[str, Any]:
        """
        Genera un reporte completo de compliance.

        Args:
            report_type: Tipo de reporte
            days: Días a cubrir

        Returns:
            Reporte generado
        """
        logger.info(f"📊 Generating {report_type} compliance report for {days} days")

        report = self.compliance_reporter.generate_compliance_report(report_type, days)

        # Exportar en múltiples formatos
        pdf_path = self.compliance_reporter.export_report_pdf(report)
        json_path = self.compliance_reporter.export_report_json(report)

        result = report.to_dict()
        result["exported_files"] = {
            "pdf": pdf_path,
            "json": json_path
        }

        logger.info(f"📋 Compliance report generated: {report.report_id}")

        return result

    def start_background_monitoring(self, interval_minutes: int = 60):
        """
        Inicia monitoreo automático en background.

        Args:
            interval_minutes: Intervalo entre verificaciones
        """
        if self.monitoring_active:
            logger.warning("Background monitoring already active")
            return

        self.monitoring_active = True

        def monitoring_loop():
            while self.monitoring_active:
                try:
                    # Ejecutar verificación de integridad
                    integrity_result = asyncio.run(self.validate_system_integrity())

                    if not integrity_result["overall_integrity"]:
                        logger.error("❌ System integrity check failed: %s",
                                   integrity_result["recommendations"])

                        # Aquí se podrían enviar alertas, notificaciones, etc.

                    # Verificar si necesitamos generar reportes automáticos
                    # (cada semana, mes, etc.)

                except Exception as e:
                    logger.error(f"Error in background monitoring: {e}")

                # Esperar al próximo intervalo
                time.sleep(interval_minutes * 60)

        self.monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitoring_thread.start()

        logger.info(f"⏰ Started background monitoring every {interval_minutes} minutes")

    def stop_background_monitoring(self):
        """Detiene el monitoreo en background."""
        if not self.monitoring_active:
            return

        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)

        logger.info("⏹️ Stopped background monitoring")

    async def get_system_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado completo del sistema de auditoría.

        Returns:
            Estado del sistema
        """
        # Información de componentes
        blockchain_info = self.blockchain_auditor.get_chain_info()
        hash_chains_info = self.hash_chain_manager.get_all_chains_info()
        contracts_info = self.smart_contract_manager.get_all_contracts_info()
        storage_stats = self.immutable_storage.get_storage_stats()

        # Estado de integridad
        integrity_status = await self.validate_system_integrity()

        return {
            "timestamp": datetime.now().isoformat(),
            "monitoring_active": self.monitoring_active,
            "components": {
                "blockchain": blockchain_info,
                "hash_chains": hash_chains_info,
                "smart_contracts": contracts_info,
                "immutable_storage": storage_stats
            },
            "integrity_status": integrity_status,
            "system_health": "healthy" if integrity_status["overall_integrity"] else "compromised"
        }

    async def cleanup_expired_data(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Limpia datos expirados según políticas de retención.

        Args:
            dry_run: Si True, solo reporta qué se limpiaría

        Returns:
            Resultado de la limpieza
        """
        logger.info(f"🧹 Starting data cleanup (dry_run={dry_run})")

        cutoff_date = datetime.now()
        expired_logs = self.immutable_storage.get_logs_for_retention_cleanup(cutoff_date)

        result = {
            "cutoff_date": cutoff_date.isoformat(),
            "expired_logs_count": len(expired_logs),
            "expired_log_ids": expired_logs[:10],  # Limitar para respuesta
            "dry_run": dry_run,
            "cleanup_performed": False
        }

        if not dry_run and expired_logs:
            # En una implementación real, aquí se haría la limpieza
            # Pero como los logs son inmutables, probablemente solo se marcan
            logger.warning("Data cleanup not implemented for immutable logs")
            result["cleanup_performed"] = False
            result["note"] = "Immutable logs cannot be deleted - consider archiving"

        logger.info(f"🧹 Data cleanup completed: {len(expired_logs)} expired logs found")

        return result


# Instancia global de la integración
blockchain_audit_integration = BlockchainAuditIntegration()


def get_blockchain_audit_integration() -> BlockchainAuditIntegration:
    """Obtiene instancia global de la integración de auditoría blockchain."""
    return blockchain_audit_integration


async def initialize_blockchain_audit_system():
    """
    Inicializa el sistema completo de auditoría blockchain.
    Función de conveniencia para setup inicial.
    """
    integration = get_blockchain_audit_integration()

    # Verificar integridad inicial
    integrity = await integration.validate_system_integrity()

    if not integrity["overall_integrity"]:
        logger.warning("⚠️ System integrity issues detected during initialization")
        for rec in integrity["recommendations"]:
            logger.warning(f"  - {rec}")

    # Iniciar monitoreo en background
    integration.start_background_monitoring()

    logger.info("🚀 Blockchain audit system initialized successfully")

    return integration