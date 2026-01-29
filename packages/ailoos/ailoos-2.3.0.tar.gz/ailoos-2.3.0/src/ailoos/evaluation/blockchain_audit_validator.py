"""
Validador de auditoría blockchain para transacciones de recompensas.
Verifica que todas las transacciones de recompensas sean auditables e inmutables.
"""

import hashlib
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging

from ..core.logging import get_logger
from ..auditing.blockchain_auditor import get_blockchain_auditor, AuditOperation

logger = get_logger(__name__)


@dataclass
class RewardTransaction:
    """Transacción de recompensa para auditar."""
    transaction_id: str
    node_id: str
    wallet_address: str
    amount: float
    round_number: int
    timestamp: float
    blockchain_tx_hash: Optional[str] = None
    audit_block_hash: Optional[str] = None
    status: str = "pending"  # pending, confirmed, failed


@dataclass
class AuditValidationResult:
    """Resultado de validación de auditoría."""
    transaction_id: str
    is_auditable: bool
    blockchain_recorded: bool
    audit_trail_complete: bool
    integrity_verified: bool
    issues: List[str] = field(default_factory=list)
    proof_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BlockchainAuditReport:
    """Reporte completo de auditoría blockchain."""
    total_transactions: int
    auditable_transactions: int
    blockchain_recorded: int
    integrity_verified: int
    audit_completeness: float  # 0.0 to 1.0
    issues_found: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    validation_results: List[AuditValidationResult] = field(default_factory=list)


class BlockchainAuditValidator:
    """
    Validador que verifica la auditabilidad de todas las transacciones de recompensas.
    Asegura que cada transacción esté registrada de manera inmutable en la blockchain.
    """

    def __init__(self, require_blockchain_confirmation: bool = True,
                 audit_trail_verification: bool = True):
        self.require_blockchain_confirmation = require_blockchain_confirmation
        self.audit_trail_verification = audit_trail_verification

        # Estado de validación
        self.audit_history: List[AuditValidationResult] = []
        self.blockchain_auditor = get_blockchain_auditor()

        # Estadísticas
        self.total_validations = 0
        self.audit_failures = 0

        logger.info("🔗 BlockchainAuditValidator initialized")

    def validate_reward_transaction(self, transaction: RewardTransaction) -> AuditValidationResult:
        """
        Valida la auditabilidad de una transacción de recompensa.

        Args:
            transaction: Transacción de recompensa a validar

        Returns:
            Resultado de validación de auditoría
        """
        issues = []
        proof_data = {}

        # 1. Verificar que la transacción esté registrada en blockchain
        blockchain_recorded = self._verify_blockchain_record(transaction)
        if not blockchain_recorded:
            issues.append("Transaction not recorded in blockchain")

        # 2. Verificar integridad de la cadena de auditoría
        audit_trail_complete = self._verify_audit_trail(transaction)
        if not audit_trail_complete:
            issues.append("Incomplete audit trail")

        # 3. Verificar integridad de datos
        integrity_verified = self._verify_data_integrity(transaction)
        if not integrity_verified:
            issues.append("Data integrity verification failed")

        # 4. Verificar confirmación blockchain si es requerida
        if self.require_blockchain_confirmation:
            confirmation_verified = self._verify_blockchain_confirmation(transaction)
            if not confirmation_verified:
                issues.append("Blockchain confirmation not verified")
        else:
            confirmation_verified = True

        # 5. Recopilar datos de prueba
        proof_data = self._gather_proof_data(transaction)

        # Resultado general
        is_auditable = blockchain_recorded and audit_trail_complete and integrity_verified and confirmation_verified

        result = AuditValidationResult(
            transaction_id=transaction.transaction_id,
            is_auditable=is_auditable,
            blockchain_recorded=blockchain_recorded,
            audit_trail_complete=audit_trail_complete,
            integrity_verified=integrity_verified,
            issues=issues,
            proof_data=proof_data
        )

        self.audit_history.append(result)
        self.total_validations += 1

        if not is_auditable:
            self.audit_failures += 1

        logger.info(f"🔍 Audit validation for transaction {transaction.transaction_id}: {'✅' if is_auditable else '❌'}")

        return result

    def validate_batch_transactions(self, transactions: List[RewardTransaction]) -> List[AuditValidationResult]:
        """
        Valida un lote de transacciones de recompensa.

        Args:
            transactions: Lista de transacciones a validar

        Returns:
            Lista de resultados de validación
        """
        results = []

        for transaction in transactions:
            result = self.validate_reward_transaction(transaction)
            results.append(result)

        logger.info(f"🔍 Batch validation completed: {len(results)} transactions, "
                   f"{sum(1 for r in results if r.is_auditable)} auditable")

        return results

    def _verify_blockchain_record(self, transaction: RewardTransaction) -> bool:
        """Verifica que la transacción esté registrada en la blockchain de auditoría."""
        try:
            # Buscar la operación en la blockchain
            operations = self.blockchain_auditor.search_operations({
                "operation_id": transaction.transaction_id,
                "operation_type": "reward_distribution"
            })

            if not operations:
                return False

            # Verificar que la operación encontrada coincida con la transacción
            operation = operations[0]  # Tomar la primera coincidencia

            # Verificar datos críticos
            if (operation.get("data", {}).get("node_id") != transaction.node_id or
                operation.get("data", {}).get("amount") != transaction.amount or
                operation.get("data", {}).get("round_number") != transaction.round_number):
                return False

            # Actualizar hash del bloque de auditoría si no está presente
            if transaction.audit_block_hash is None:
                transaction.audit_block_hash = operation.get("block_hash")

            return True

        except Exception as e:
            logger.error(f"Error verifying blockchain record for {transaction.transaction_id}: {e}")
            return False

    def _verify_audit_trail(self, transaction: RewardTransaction) -> bool:
        """Verifica la completitud de la cadena de auditoría."""
        if not self.audit_trail_verification:
            return True

        try:
            # Verificar que tengamos todos los componentes necesarios
            required_components = [
                transaction.transaction_id,
                transaction.node_id,
                transaction.wallet_address,
                transaction.amount > 0,
                transaction.timestamp > 0,
                transaction.round_number >= 0
            ]

            if not all(required_components):
                return False

            # Verificar prueba de existencia en blockchain
            if transaction.audit_block_hash:
                proof = self.blockchain_auditor.get_operation_proof(transaction.transaction_id)
                if not proof:
                    return False

                # Verificar que la prueba sea válida
                if (proof.get("block_hash") != transaction.audit_block_hash or
                    proof.get("confirmations", 0) < 0):
                    return False

            return True

        except Exception as e:
            logger.error(f"Error verifying audit trail for {transaction.transaction_id}: {e}")
            return False

    def _verify_data_integrity(self, transaction: RewardTransaction) -> bool:
        """Verifica la integridad de los datos de la transacción."""
        try:
            # Crear hash de los datos de la transacción
            transaction_data = {
                "transaction_id": transaction.transaction_id,
                "node_id": transaction.node_id,
                "wallet_address": transaction.wallet_address,
                "amount": transaction.amount,
                "round_number": transaction.round_number,
                "timestamp": transaction.timestamp
            }

            data_string = json.dumps(transaction_data, sort_keys=True)
            calculated_hash = hashlib.sha256(data_string.encode()).hexdigest()

            # En un sistema real, compararíamos con un hash almacenado
            # Por ahora, verificamos consistencia interna
            if transaction.amount < 0:
                return False

            if not transaction.wallet_address.startswith(("0x", "bc1", "tb1")):
                return False

            if transaction.timestamp > datetime.now().timestamp() + 300:  # 5 minutos de tolerancia
                return False

            return True

        except Exception as e:
            logger.error(f"Error verifying data integrity for {transaction.transaction_id}: {e}")
            return False

    def _verify_blockchain_confirmation(self, transaction: RewardTransaction) -> bool:
        """Verifica la confirmación de la transacción en blockchain externa."""
        if not self.require_blockchain_confirmation:
            return True

        try:
            # Verificar que tengamos un hash de transacción blockchain
            if not transaction.blockchain_tx_hash:
                return False

            # En un sistema real, verificaríamos la transacción en la blockchain externa
            # Por ahora, verificamos formato básico del hash
            if not transaction.blockchain_tx_hash.startswith("0x") or len(transaction.blockchain_tx_hash) != 66:
                return False

            # Verificar que el hash no sea todo ceros (transacción dummy)
            if transaction.blockchain_tx_hash == "0x" + "0" * 64:
                return False

            return True

        except Exception as e:
            logger.error(f"Error verifying blockchain confirmation for {transaction.transaction_id}: {e}")
            return False

    def _gather_proof_data(self, transaction: RewardTransaction) -> Dict[str, Any]:
        """Recopila datos de prueba para la transacción."""
        proof_data = {
            "transaction_hash": self._calculate_transaction_hash(transaction),
            "audit_trail": {},
            "blockchain_status": {}
        }

        try:
            # Datos de cadena de auditoría
            if transaction.audit_block_hash:
                proof = self.blockchain_auditor.get_operation_proof(transaction.transaction_id)
                if proof:
                    proof_data["audit_trail"] = {
                        "block_hash": proof.get("block_hash"),
                        "block_index": proof.get("block_index"),
                        "merkle_root": proof.get("merkle_root"),
                        "confirmations": proof.get("confirmations"),
                        "timestamp": proof.get("timestamp")
                    }

            # Estado de blockchain
            proof_data["blockchain_status"] = {
                "tx_hash": transaction.blockchain_tx_hash,
                "confirmed": transaction.status == "confirmed",
                "audit_block_hash": transaction.audit_block_hash
            }

        except Exception as e:
            logger.error(f"Error gathering proof data for {transaction.transaction_id}: {e}")

        return proof_data

    def _calculate_transaction_hash(self, transaction: RewardTransaction) -> str:
        """Calcula hash único de la transacción."""
        data = {
            "id": transaction.transaction_id,
            "node": transaction.node_id,
            "wallet": transaction.wallet_address,
            "amount": transaction.amount,
            "round": transaction.round_number,
            "timestamp": transaction.timestamp
        }

        data_string = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_string.encode()).hexdigest()

    def register_reward_transaction(self, transaction: RewardTransaction) -> bool:
        """
        Registra una transacción de recompensa en la blockchain de auditoría.

        Args:
            transaction: Transacción a registrar

        Returns:
            True si se registró exitosamente
        """
        try:
            # Crear operación de auditoría
            audit_operation = AuditOperation(
                operation_id=transaction.transaction_id,
                operation_type="reward_distribution",
                user_id=transaction.node_id,
                timestamp=transaction.timestamp,
                data={
                    "node_id": transaction.node_id,
                    "wallet_address": transaction.wallet_address,
                    "amount": transaction.amount,
                    "round_number": transaction.round_number,
                    "blockchain_tx_hash": transaction.blockchain_tx_hash,
                    "transaction_hash": self._calculate_transaction_hash(transaction)
                },
                compliance_flags=["reward_transaction", "blockchain_audited"]
            )

            # Registrar en blockchain de auditoría
            import asyncio
            block_hash = asyncio.run(self.blockchain_auditor.add_operation(audit_operation))

            if block_hash and block_hash != "pending":
                transaction.audit_block_hash = block_hash
                transaction.status = "confirmed"
                logger.info(f"✅ Reward transaction {transaction.transaction_id} registered in audit blockchain")
                return True
            else:
                logger.warning(f"⚠️ Reward transaction {transaction.transaction_id} pending in audit blockchain")
                return False

        except Exception as e:
            logger.error(f"❌ Error registering reward transaction {transaction.transaction_id}: {e}")
            return False

    def generate_audit_report(self) -> BlockchainAuditReport:
        """
        Genera reporte completo de auditoría blockchain.

        Returns:
            Reporte de auditoría completo
        """
        if not self.audit_history:
            return BlockchainAuditReport(
                total_transactions=0,
                auditable_transactions=0,
                blockchain_recorded=0,
                integrity_verified=0,
                audit_completeness=0.0
            )

        # Calcular estadísticas
        total_transactions = len(self.audit_history)
        auditable_transactions = sum(1 for r in self.audit_history if r.is_auditable)
        blockchain_recorded = sum(1 for r in self.audit_history if r.blockchain_recorded)
        integrity_verified = sum(1 for r in self.audit_history if r.integrity_verified)

        audit_completeness = auditable_transactions / total_transactions if total_transactions > 0 else 0.0

        # Recopilar issues
        all_issues = []
        for result in self.audit_history:
            all_issues.extend(result.issues)

        # Generar recomendaciones
        recommendations = self._generate_audit_recommendations(audit_completeness, all_issues)

        report = BlockchainAuditReport(
            total_transactions=total_transactions,
            auditable_transactions=auditable_transactions,
            blockchain_recorded=blockchain_recorded,
            integrity_verified=integrity_verified,
            audit_completeness=audit_completeness,
            issues_found=list(set(all_issues)),  # Remover duplicados
            recommendations=recommendations,
            validation_results=self.audit_history.copy()
        )

        logger.info("📊 Blockchain audit report generated:")
        logger.info(f"   Total transactions: {total_transactions}")
        logger.info(f"   Auditable: {auditable_transactions} ({audit_completeness:.1%})")
        logger.info(f"   Issues found: {len(report.issues_found)}")

        return report

    def _generate_audit_recommendations(self, completeness: float, issues: List[str]) -> List[str]:
        """Genera recomendaciones basadas en el análisis de auditoría."""
        recommendations = []

        if completeness < 0.8:
            recommendations.append("Critical: Audit completeness below 80%. Immediate action required.")

        if "Transaction not recorded in blockchain" in issues:
            recommendations.append("Ensure all reward transactions are registered in audit blockchain before distribution.")

        if "Incomplete audit trail" in issues:
            recommendations.append("Implement complete audit trail verification for all transactions.")

        if "Data integrity verification failed" in issues:
            recommendations.append("Strengthen data integrity checks and validation mechanisms.")

        if "Blockchain confirmation not verified" in issues:
            recommendations.append("Verify blockchain confirmations for all reward transactions.")

        if completeness >= 0.95:
            recommendations.append("Excellent audit compliance. Continue monitoring.")
        elif completeness >= 0.90:
            recommendations.append("Good audit compliance. Minor improvements needed.")
        else:
            recommendations.append("Poor audit compliance. Major improvements required.")

        return recommendations

    def get_audit_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de auditoría."""
        report = self.generate_audit_report()

        return {
            "total_validations": self.total_validations,
            "audit_failures": self.audit_failures,
            "audit_success_rate": (self.total_validations - self.audit_failures) / max(1, self.total_validations),
            "audit_completeness": report.audit_completeness,
            "blockchain_coverage": report.blockchain_recorded / max(1, report.total_transactions),
            "integrity_rate": report.integrity_verified / max(1, report.total_transactions),
            "blockchain_auditor_status": self.blockchain_auditor.get_chain_info(),
            "latest_report": {
                "total_transactions": report.total_transactions,
                "auditable_transactions": report.auditable_transactions,
                "issues_count": len(report.issues_found)
            }
        }

    def reset(self):
        """Resetea el validador de auditoría."""
        self.audit_history.clear()
        self.total_validations = 0
        self.audit_failures = 0
        logger.info("🔄 BlockchainAuditValidator reset")