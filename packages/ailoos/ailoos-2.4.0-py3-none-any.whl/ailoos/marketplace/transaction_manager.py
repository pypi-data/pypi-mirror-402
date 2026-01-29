"""
Gestor de transacciones para AILOOS Marketplace.
Maneja pagos, escrow y resolución de disputas.
"""

import asyncio
import json
import time
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from ..blockchain.dracma_token import get_token_manager, TransactionResult


class EscrowStatus(Enum):
    PENDING = "pending"
    FUNDED = "funded"
    RELEASED = "released"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class DisputeReason(Enum):
    DATA_NOT_DELIVERED = "data_not_delivered"
    DATA_CORRUPTED = "data_corrupted"
    DATA_LOW_QUALITY = "data_low_quality"
    INCORRECT_DESCRIPTION = "incorrect_description"
    OTHER = "other"


@dataclass
class EscrowTransaction:
    """Transacción en escrow."""
    escrow_id: str
    buyer_address: str
    seller_address: str
    amount_dracma: float
    listing_id: str
    data_hash: str
    ipfs_cid: str
    created_at: float
    funded_at: Optional[float] = None
    released_at: Optional[float] = None
    status: EscrowStatus = EscrowStatus.PENDING
    dispute_reason: Optional[DisputeReason] = None
    dispute_opened_at: Optional[float] = None
    arbitrator_decision: Optional[str] = None


class TransactionManager:
    """
    Gestor completo de transacciones con sistema de escrow.
    Garantiza seguridad en compras de datos.
    """

    def __init__(self):
        self.escrow_transactions: Dict[str, EscrowTransaction] = {}
        self.disputes: Dict[str, Dict[str, Any]] = {}
        self.arbitrators: List[str] = []  # Direcciones de árbitros autorizados
        self.token_manager = get_token_manager()

        # Automatic settlement configuration
        self.auto_settlement_enabled = True
        self.settlement_check_interval = 300  # 5 minutes
        self.auto_release_delay_hours = 24  # Auto-release after 24 hours if no issues
        self.max_auto_settlement_amount = 1000.0  # Max DracmaS for auto-settlement
        self.settlement_queue: List[str] = []  # Queue of escrows ready for settlement

        # Security and audit configuration
        self.audit_enabled = True
        self.audit_log_path = "./logs/transaction_audit.log"
        self.security_checks_enabled = True
        self.max_transaction_value = 10000.0  # Max DracmaS per transaction
        self.suspicious_activity_threshold = 5  # Transactions per hour
        self.transaction_cooldown_seconds = 10  # Min time between transactions

        # Audit and security tracking
        self.transaction_audit_log: List[Dict[str, Any]] = []
        self.suspicious_activities: Dict[str, List[Dict[str, Any]]] = {}
        self.transaction_limits: Dict[str, Dict[str, Any]] = {}  # address -> limits tracking


        # Initialize audit system
        self._initialize_audit_system()

    def _initialize_audit_system(self):
        """Initialize the transaction audit system."""
        try:
            import os
            os.makedirs(os.path.dirname(self.audit_log_path), exist_ok=True)

            # Log initialization
            self._audit_log("SYSTEM", "AUDIT_SYSTEM_INITIALIZED", {
                "timestamp": time.time(),
                "config": {
                    "audit_enabled": self.audit_enabled,
                    "security_checks_enabled": self.security_checks_enabled,
                    "max_transaction_value": self.max_transaction_value,
                    "suspicious_activity_threshold": self.suspicious_activity_threshold
                }
            })

        except Exception as e:
            print(f"Error initializing audit system: {e}")

    def _audit_log(self, actor: str, action: str, details: Dict[str, Any]):
        """Log an auditable event."""
        if not self.audit_enabled:
            return

        audit_entry = {
            "timestamp": time.time(),
            "actor": actor,
            "action": action,
            "details": details,
            "audit_id": f"audit_{int(time.time() * 1000000)}"
        }

        self.transaction_audit_log.append(audit_entry)

        # Write to file (in production, use proper logging)
        try:
            with open(self.audit_log_path, 'a') as f:
                f.write(json.dumps(audit_entry) + '\n')
        except Exception as e:
            print(f"Error writing audit log: {e}")

    def _check_transaction_security(self, buyer_address: str, seller_address: str,
                                  amount: float) -> Dict[str, Any]:
        """Perform security checks on a transaction."""
        security_result = {
            "approved": True,
            "warnings": [],
            "blocks": [],
            "risk_score": 0.0
        }

        if not self.security_checks_enabled:
            return security_result

        current_time = time.time()

        # 1. Check transaction value limits
        if amount > self.max_transaction_value:
            security_result["blocks"].append(f"Transaction amount {amount} exceeds maximum {self.max_transaction_value}")
            security_result["approved"] = False

        # 2. Check transaction frequency (anti-spam)
        buyer_limits = self.transaction_limits.get(buyer_address, {"last_tx": 0, "count_hour": 0, "hour_start": current_time})
        seller_limits = self.transaction_limits.get(seller_address, {"last_tx": 0, "count_hour": 0, "hour_start": current_time})

        # Reset hourly counter if hour has passed
        if current_time - buyer_limits["hour_start"] > 3600:
            buyer_limits = {"last_tx": current_time, "count_hour": 1, "hour_start": current_time}
        else:
            buyer_limits["count_hour"] += 1

        if current_time - seller_limits["hour_start"] > 3600:
            seller_limits = {"last_tx": current_time, "count_hour": 1, "hour_start": current_time}
        else:
            seller_limits["count_hour"] += 1

        # Check cooldown
        if current_time - buyer_limits["last_tx"] < self.transaction_cooldown_seconds:
            security_result["blocks"].append("Transaction cooldown active")
            security_result["approved"] = False

        # Check suspicious activity
        if buyer_limits["count_hour"] > self.suspicious_activity_threshold:
            security_result["warnings"].append(f"High transaction frequency from buyer: {buyer_limits['count_hour']} tx/hour")
            security_result["risk_score"] += 0.3

        if seller_limits["count_hour"] > self.suspicious_activity_threshold:
            security_result["warnings"].append(f"High transaction frequency from seller: {seller_limits['count_hour']} tx/hour")
            security_result["risk_score"] += 0.3

        # Update limits
        self.transaction_limits[buyer_address] = buyer_limits
        self.transaction_limits[seller_address] = seller_limits

        # 3. Check for self-transaction
        if buyer_address == seller_address:
            security_result["blocks"].append("Self-transaction not allowed")
            security_result["approved"] = False

        # 4. Check for blacklisted addresses (placeholder for future implementation)
        # if self._is_blacklisted(buyer_address) or self._is_blacklisted(seller_address):
        #     security_result["blocks"].append("Address is blacklisted")
        #     security_result["approved"] = False

        # Log security check
        self._audit_log("SECURITY_SYSTEM", "TRANSACTION_SECURITY_CHECK", {
            "buyer_address": buyer_address,
            "seller_address": seller_address,
            "amount": amount,
            "result": security_result
        })

        return security_result

    def create_escrow(self, buyer_address: str, seller_address: str,
                     amount_dracma: float, listing_id: str,
                     data_hash: str, ipfs_cid: str) -> str:
        """
        Crea una transacción en escrow con validaciones de seguridad.

        Args:
            buyer_address: Dirección del comprador
            seller_address: Dirección del vendedor
            amount_dracma: Monto de la transacción
            listing_id: ID del listing
            data_hash: Hash de los datos
            ipfs_cid: CID de IPFS

        Returns:
            ID del escrow creado
        """
        # Perform security checks
        security_check = self._check_transaction_security(buyer_address, seller_address, amount_dracma)
        if not security_check["approved"]:
            raise ValueError(f"Transaction blocked: {', '.join(security_check['blocks'])}")

        escrow_id = self._generate_escrow_id(buyer_address, seller_address, listing_id)

        escrow = EscrowTransaction(
            escrow_id=escrow_id,
            buyer_address=buyer_address,
            seller_address=seller_address,
            amount_dracma=amount_dracma,
            listing_id=listing_id,
            data_hash=data_hash,
            ipfs_cid=ipfs_cid,
            created_at=time.time(),
            status=EscrowStatus.PENDING
        )

        self.escrow_transactions[escrow_id] = escrow

        # Audit log the escrow creation
        self._audit_log(buyer_address, "ESCROW_CREATED", {
            "escrow_id": escrow_id,
            "seller_address": seller_address,
            "amount_dracma": amount_dracma,
            "listing_id": listing_id,
            "security_warnings": security_check["warnings"],
            "risk_score": security_check["risk_score"]
        })

        return escrow_id

    async def fund_escrow(self, escrow_id: str, buyer_address: str) -> bool:
        """
        Fondea el escrow con los tokens del comprador.

        Args:
            escrow_id: ID del escrow
            buyer_address: Dirección del comprador

        Returns:
            True si el fondeo fue exitoso
        """
        if escrow_id not in self.escrow_transactions:
            raise ValueError(f"Escrow {escrow_id} no existe")

        escrow = self.escrow_transactions[escrow_id]

        if escrow.buyer_address != buyer_address:
            raise ValueError("Solo el comprador puede fondear el escrow")

        if escrow.status != EscrowStatus.PENDING:
            raise ValueError(f"Escrow está en estado {escrow.status.value}")

        # Verificar balance suficiente
        buyer_balance = await self.token_manager.get_user_balance(buyer_address)
        if buyer_balance < escrow.amount_dracma:
            raise ValueError(f"Balance insuficiente: {buyer_balance} DRACMA")

        # Transferir fondos al contrato de escrow (usando token manager real)
        escrow_result = await self.token_manager.transfer_tokens(
            from_address=buyer_address,
            to_address="escrow_contract",  # Dirección especial del contrato
            amount=escrow.amount_dracma
        )

        if not escrow_result.success:
            raise ValueError(f"Error al fondear escrow: {escrow_result.error_message}")

        # Actualizar estado del escrow
        escrow.status = EscrowStatus.FUNDED
        escrow.funded_at = time.time()

        # Audit log the funding
        self._audit_log(buyer_address, "ESCROW_FUNDED", {
            "escrow_id": escrow_id,
            "amount_dracma": escrow.amount_dracma,
            "listing_id": escrow.listing_id,
            "transaction_hash": escrow_result.tx_hash if escrow_result.tx_hash else None
        })

        return True

    async def release_escrow(self, escrow_id: str, buyer_address: str) -> bool:
        """
        Libera los fondos del escrow al vendedor.

        Args:
            escrow_id: ID del escrow
            buyer_address: Dirección del comprador

        Returns:
            True si la liberación fue exitosa
        """
        if escrow_id not in self.escrow_transactions:
            raise ValueError(f"Escrow {escrow_id} no existe")

        escrow = self.escrow_transactions[escrow_id]

        if escrow.buyer_address != buyer_address:
            raise ValueError("Solo el comprador puede liberar el escrow")

        if escrow.status != EscrowStatus.FUNDED:
            raise ValueError(f"Escrow debe estar fondeado, está en {escrow.status.value}")

        # Transferir fondos del escrow al vendedor
        release_result = await self.token_manager.transfer_tokens(
            from_address="escrow_contract",
            to_address=escrow.seller_address,
            amount=escrow.amount_dracma
        )

        if not release_result.success:
            raise ValueError(f"Error al liberar escrow: {release_result.error_message}")

        # Actualizar estado
        escrow.status = EscrowStatus.RELEASED
        escrow.released_at = time.time()

        # Audit log the release
        self._audit_log(buyer_address, "ESCROW_RELEASED", {
            "escrow_id": escrow_id,
            "amount_dracma": escrow.amount_dracma,
            "seller_address": escrow.seller_address,
            "transaction_hash": release_result.tx_hash if release_result.tx_hash else None
        })

        return True

    def open_dispute(self, escrow_id: str, initiator_address: str,
                    reason: DisputeReason, description: str) -> str:
        """
        Abre una disputa para un escrow.

        Args:
            escrow_id: ID del escrow
            initiator_address: Dirección que abre la disputa
            reason: Razón de la disputa
            description: Descripción detallada

        Returns:
            ID de la disputa
        """
        if escrow_id not in self.escrow_transactions:
            raise ValueError(f"Escrow {escrow_id} no existe")

        escrow = self.escrow_transactions[escrow_id]

        # Verificar que el iniciador sea parte de la transacción
        if initiator_address not in [escrow.buyer_address, escrow.seller_address]:
            raise ValueError("Solo las partes involucradas pueden abrir disputas")

        if escrow.status not in [EscrowStatus.FUNDED, EscrowStatus.RELEASED]:
            raise ValueError("Solo escrows fondeados pueden tener disputas")

        # Cambiar estado a disputado
        escrow.status = EscrowStatus.DISPUTED
        escrow.dispute_reason = reason
        escrow.dispute_opened_at = time.time()

        # Crear disputa
        dispute_id = f"dispute_{escrow_id}_{int(time.time())}"
        self.disputes[dispute_id] = {
            "dispute_id": dispute_id,
            "escrow_id": escrow_id,
            "initiator": initiator_address,
            "reason": reason.value,
            "description": description,
            "opened_at": time.time(),
            "status": "open",
            "arbitrator": None,
            "decision": None,
            "resolved_at": None
        }

        return dispute_id

    async def resolve_dispute(self, dispute_id: str, arbitrator_address: str,
                             decision: str, notes: str = "") -> bool:
        """
        Resuelve una disputa.

        Args:
            dispute_id: ID de la disputa
            arbitrator_address: Dirección del árbitro
            decision: Decisión ("buyer", "seller", o "split")
            notes: Notas adicionales

        Returns:
            True si la resolución fue exitosa
        """
        if dispute_id not in self.disputes:
            raise ValueError(f"Dispute {dispute_id} no existe")

        dispute = self.disputes[dispute_id]

        if dispute["status"] != "open":
            raise ValueError("Dispute ya está resuelta")

        # Verificar que el árbitro esté autorizado
        if arbitrator_address not in self.arbitrators:
            raise ValueError("Árbitro no autorizado")

        escrow = self.escrow_transactions[dispute["escrow_id"]]

        # Ejecutar decisión
        if decision == "buyer":
            # Devolver fondos al comprador
            refund_result = await self.token_manager.transfer_tokens(
                from_address="escrow_contract",
                to_address=escrow.buyer_address,
                amount=escrow.amount_dracma
            )
            if not refund_result.success:
                raise ValueError(f"Error al devolver fondos: {refund_result.error_message}")
            escrow.status = EscrowStatus.REFUNDED

        elif decision == "seller":
            # Enviar fondos al vendedor
            seller_result = await self.token_manager.transfer_tokens(
                from_address="escrow_contract",
                to_address=escrow.seller_address,
                amount=escrow.amount_dracma
            )
            if not seller_result.success:
                raise ValueError(f"Error al enviar fondos al vendedor: {seller_result.error_message}")
            escrow.status = EscrowStatus.RELEASED

        elif decision == "split":
            # Dividir fondos
            half_amount = escrow.amount_DracmaS / 2
            buyer_result = await self.token_manager.transfer_tokens(
                from_address="escrow_contract",
                to_address=escrow.buyer_address,
                amount=half_amount
            )
            seller_result = await self.token_manager.transfer_tokens(
                from_address="escrow_contract",
                to_address=escrow.seller_address,
                amount=half_amount
            )
            if not buyer_result.success or not seller_result.success:
                raise ValueError("Error al dividir fondos entre las partes")
            escrow.status = EscrowStatus.RELEASED

        else:
            raise ValueError(f"Decisión inválida: {decision}")

        # Actualizar disputa
        dispute["status"] = "resolved"
        dispute["arbitrator"] = arbitrator_address
        dispute["decision"] = decision
        dispute["notes"] = notes
        dispute["resolved_at"] = time.time()

        escrow.arbitrator_decision = decision

        return True

    def cancel_escrow(self, escrow_id: str, canceller_address: str) -> bool:
        """
        Cancela un escrow antes de ser fondeado.

        Args:
            escrow_id: ID del escrow
            canceller_address: Dirección que cancela

        Returns:
            True si la cancelación fue exitosa
        """
        if escrow_id not in self.escrow_transactions:
            raise ValueError(f"Escrow {escrow_id} no existe")

        escrow = self.escrow_transactions[escrow_id]

        if escrow.buyer_address != canceller_address:
            raise ValueError("Solo el comprador puede cancelar el escrow")

        if escrow.status != EscrowStatus.PENDING:
            raise ValueError("Solo escrows pendientes pueden ser cancelados")

        escrow.status = EscrowStatus.CANCELLED
        return True

    def get_escrow_status(self, escrow_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene estado de un escrow."""
        escrow = self.escrow_transactions.get(escrow_id)
        if not escrow:
            return None

        return {
            "escrow_id": escrow.escrow_id,
            "buyer_address": escrow.buyer_address,
            "seller_address": escrow.seller_address,
            "amount_dracma": escrow.amount_dracma,
            "listing_id": escrow.listing_id,
            "status": escrow.status.value,
            "created_at": escrow.created_at,
            "funded_at": escrow.funded_at,
            "released_at": escrow.released_at,
            "dispute_reason": escrow.dispute_reason.value if escrow.dispute_reason else None,
            "dispute_opened_at": escrow.dispute_opened_at
        }

    def get_user_escrows(self, user_address: str) -> List[Dict[str, Any]]:
        """Obtiene escrows de un usuario."""
        user_escrows = []
        for escrow in self.escrow_transactions.values():
            if user_address in [escrow.buyer_address, escrow.seller_address]:
                user_escrows.append(self.get_escrow_status(escrow.escrow_id))
        return user_escrows

    def get_open_disputes(self) -> List[Dict[str, Any]]:
        """Obtiene disputas abiertas."""
        return [d for d in self.disputes.values() if d["status"] == "open"]

    def get_dispute_details(self, dispute_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene detalles de una disputa."""
        return self.disputes.get(dispute_id)

    def add_arbitrator(self, arbitrator_address: str):
        """Añade un árbitro autorizado."""
        if arbitrator_address not in self.arbitrators:
            self.arbitrators.append(arbitrator_address)

    def remove_arbitrator(self, arbitrator_address: str):
        """Remueve un árbitro."""
        if arbitrator_address in self.arbitrators:
            self.arbitrators.remove(arbitrator_address)

    def get_transaction_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de transacciones."""
        total_escrows = len(self.escrow_transactions)
        funded_escrows = len([e for e in self.escrow_transactions.values() if e.status == EscrowStatus.FUNDED])
        released_escrows = len([e for e in self.escrow_transactions.values() if e.status == EscrowStatus.RELEASED])
        disputed_escrows = len([e for e in self.escrow_transactions.values() if e.status == EscrowStatus.DISPUTED])

        total_volume = sum(e.amount_DracmaS for e in self.escrow_transactions.values()
                          if e.status in [EscrowStatus.RELEASED, EscrowStatus.FUNDED])

        open_disputes = len(self.get_open_disputes())

        return {
            "total_escrows": total_escrows,
            "funded_escrows": funded_escrows,
            "released_escrows": released_escrows,
            "disputed_escrows": disputed_escrows,
            "total_volume_dracma": total_volume,
            "open_disputes": open_disputes,
            "resolution_rate": (released_escrows / max(funded_escrows, 1)) * 100
        }

    def _generate_escrow_id(self, buyer: str, seller: str, listing_id: str) -> str:
        """Genera ID único para escrow."""
        data = f"{buyer}_{seller}_{listing_id}_{time.time()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def export_escrows(self, filename: str):
        """Exporta escrows a archivo JSON."""
        data = {
            "escrows": {
                eid: {
                    "escrow_id": e.escrow_id,
                    "buyer_address": e.buyer_address,
                    "seller_address": e.seller_address,
                    "amount_dracma": e.amount_dracma,
                    "listing_id": e.listing_id,
                    "data_hash": e.data_hash,
                    "ipfs_cid": e.ipfs_cid,
                    "created_at": e.created_at,
                    "funded_at": e.funded_at,
                    "released_at": e.released_at,
                    "status": e.status.value,
                    "dispute_reason": e.dispute_reason.value if e.dispute_reason else None,
                    "dispute_opened_at": e.dispute_opened_at,
                    "arbitrator_decision": e.arbitrator_decision
                }
                for eid, e in self.escrow_transactions.items()
            },
            "disputes": self.disputes,
            "arbitrators": self.arbitrators,
            "exported_at": time.time()
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def import_escrows(self, filename: str):
        """Importa escrows desde archivo JSON."""
        with open(filename, 'r') as f:
            data = json.load(f)

        # Reconstruir escrows
        for eid, escrow_data in data["escrows"].items():
            escrow_data["status"] = EscrowStatus(escrow_data["status"])
            if escrow_data["dispute_reason"]:
                escrow_data["dispute_reason"] = DisputeReason(escrow_data["dispute_reason"])
            self.escrow_transactions[eid] = EscrowTransaction(**escrow_data)

        self.disputes = data["disputes"]
        self.arbitrators = data.get("arbitrators", [])

    async def _start_automatic_settlement(self):
        """Start automatic settlement monitoring loop."""
        while True:
            try:
                await self._process_automatic_settlements()
                await asyncio.sleep(self.settlement_check_interval)
            except Exception as e:
                print(f"Error in automatic settlement loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _process_automatic_settlements(self):
        """Process escrows eligible for automatic settlement."""
        if not self.auto_settlement_enabled:
            return

        current_time = time.time()
        processed_count = 0

        for escrow_id, escrow in self.escrow_transactions.items():
            if escrow.status != EscrowStatus.FUNDED:
                continue

            # Check if escrow is eligible for auto-settlement
            if self._is_eligible_for_auto_settlement(escrow, current_time):
                try:
                    success = await self._execute_automatic_settlement(escrow_id)
                    if success:
                        processed_count += 1
                        print(f"✅ Auto-settled escrow {escrow_id}")
                    else:
                        print(f"❌ Failed to auto-settle escrow {escrow_id}")
                except Exception as e:
                    print(f"Error auto-settling escrow {escrow_id}: {e}")

        if processed_count > 0:
            print(f"🔄 Processed {processed_count} automatic settlements")

    def _is_eligible_for_auto_settlement(self, escrow: EscrowTransaction, current_time: float) -> bool:
        """Check if an escrow is eligible for automatic settlement."""
        # Must be funded and not disputed
        if escrow.status != EscrowStatus.FUNDED:
            return False

        # Check amount limit
        if escrow.amount_DracmaS > self.max_auto_settlement_amount:
            return False

        # Check time delay
        funded_time = escrow.funded_at or escrow.created_at
        time_since_funded = current_time - funded_time

        if time_since_funded < (self.auto_release_delay_hours * 60 * 60):
            return False

        # Additional checks could include:
        # - Data integrity verification
        # - Seller reputation
        # - Transaction history
        # - Smart contract confirmations

        return True

    async def _execute_automatic_settlement(self, escrow_id: str) -> bool:
        """Execute automatic settlement for an escrow."""
        try:
            escrow = self.escrow_transactions.get(escrow_id)
            if not escrow or escrow.status != EscrowStatus.FUNDED:
                return False

            # Perform final validations before settlement
            if not await self._validate_settlement_conditions(escrow):
                return False

            # Execute settlement
            success = await self.release_escrow(escrow_id, escrow.buyer_address)

            if success:
                escrow.auto_settled = True
                escrow.settlement_timestamp = time.time()
                print(f"🔄 Auto-settled escrow {escrow_id} for {escrow.amount_dracma} DRACMA")

            return success

        except Exception as e:
            print(f"Error executing automatic settlement for {escrow_id}: {e}")
            return False

    async def _validate_settlement_conditions(self, escrow: EscrowTransaction) -> bool:
        """Validate conditions for automatic settlement."""
        try:
            # Check buyer balance (should still have funds)
            buyer_balance = await self.token_manager.get_user_balance(escrow.buyer_address)
            if buyer_balance < 0:  # Should not be negative
                return False

            # Check if data integrity can be verified
            # This would integrate with data validation systems
            data_integrity_ok = await self._verify_data_integrity(escrow)
            if not data_integrity_ok:
                return False

            # Check for any pending disputes
            active_disputes = [d for d in self.disputes.values()
                             if d.get("escrow_id") == escrow.escrow_id
                             and d.get("status") == "open"]
            if active_disputes:
                return False

            return True

        except Exception as e:
            print(f"Error validating settlement conditions: {e}")
            return False

    async def _verify_data_integrity(self, escrow: EscrowTransaction) -> bool:
        """Verify data integrity for settlement."""
        try:
            # Integrate with data marketplace for integrity verification
            from .data_listing import data_marketplace

            # Check if listing exists and was purchased
            listing = data_marketplace.get_listing_details(escrow.listing_id)
            if not listing:
                print(f"Listing {escrow.listing_id} not found")
                return False

            # Verify buyer actually purchased this listing
            user_purchases = data_marketplace.get_user_purchases(escrow.buyer_address)
            purchased_listing_ids = [p.listing_id for p in user_purchases]

            if escrow.listing_id not in purchased_listing_ids:
                print(f"Buyer {escrow.buyer_address} did not purchase listing {escrow.listing_id}")
                return False

            # Verify transaction hash matches
            if listing.transaction_hash != escrow.listing_id:  # In real implementation, this would be the actual tx hash
                # For now, check if the escrow was created for this listing
                if listing.transaction_hash and escrow.listing_id not in listing.transaction_hash:
                    print(f"Transaction hash mismatch for escrow {escrow.escrow_id}")
                    return False

            # Additional integrity checks
            # 1. Verify data hash consistency
            if listing.data_hash != escrow.data_hash:
                print(f"Data hash mismatch in escrow {escrow.escrow_id}")
                return False

            # 2. Verify IPFS CID consistency
            if listing.ipfs_cid != escrow.ipfs_cid:
                print(f"IPFS CID mismatch in escrow {escrow.escrow_id}")
                return False

            # 3. Check listing is still active/sold (not expired or cancelled)
            if listing.status.value not in ['sold']:
                print(f"Listing {escrow.listing_id} status is {listing.status.value}, not sold")
                return False

            # 4. Verify amount matches listing price
            if abs(escrow.amount_DracmaS - listing.price_dracma) > 0.01:  # Allow small rounding differences
                print(f"Amount mismatch: escrow {escrow.amount_dracma} vs listing {listing.price_dracma}")
                return False

            print(f"✅ Data integrity verified for escrow {escrow.escrow_id}")
            return True

        except Exception as e:
            print(f"Error verifying data integrity: {e}")
            return False

    def enable_automatic_settlement(self, enabled: bool = True):
        """Enable or disable automatic settlement."""
        self.auto_settlement_enabled = enabled
        status = "enabled" if enabled else "disabled"
        print(f"🔄 Automatic settlement {status}")

    def configure_settlement_parameters(self, delay_hours: int = None,
                                      max_amount: float = None,
                                      check_interval: int = None):
        """Configure automatic settlement parameters."""
        if delay_hours is not None:
            self.auto_release_delay_hours = delay_hours
        if max_amount is not None:
            self.max_auto_settlement_amount = max_amount
        if check_interval is not None:
            self.settlement_check_interval = check_interval

        print(f"⚙️ Updated settlement parameters: delay={self.auto_release_delay_hours}h, "
              f"max_amount={self.max_auto_settlement_amount}, interval={self.settlement_check_interval}s")

    def get_settlement_stats(self) -> Dict[str, Any]:
        """Get statistics about automatic settlements."""
        total_escrows = len(self.escrow_transactions)
        funded_escrows = len([e for e in self.escrow_transactions.values()
                             if e.status == EscrowStatus.FUNDED])
        auto_settled = len([e for e in self.escrow_transactions.values()
                           if getattr(e, 'auto_settled', False)])

        return {
            "auto_settlement_enabled": self.auto_settlement_enabled,
            "total_escrows": total_escrows,
            "funded_escrows": funded_escrows,
            "auto_settled_escrows": auto_settled,
            "auto_settlement_rate": auto_settled / max(funded_escrows, 1),
            "settlement_delay_hours": self.auto_release_delay_hours,
            "max_auto_settlement_amount": self.max_auto_settlement_amount,
            "check_interval_seconds": self.settlement_check_interval
        }

    async def force_settlement_check(self) -> Dict[str, Any]:
        """Force an immediate settlement check."""
        try:
            await self._process_automatic_settlements()
            return {"success": True, "message": "Settlement check completed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_audit_logs(self, actor: Optional[str] = None, action: Optional[str] = None,
                      limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get audit logs with optional filtering.

        Args:
            actor: Filter by actor
            action: Filter by action
            limit: Maximum number of logs to return

        Returns:
            List of audit log entries
        """
        logs = self.transaction_audit_log

        # Apply filters
        if actor:
            logs = [log for log in logs if log["actor"] == actor]
        if action:
            logs = [log for log in logs if log["action"] == action]

        # Sort by timestamp (most recent first) and limit
        logs.sort(key=lambda x: x["timestamp"], reverse=True)
        return logs[:limit]

    def get_security_stats(self) -> Dict[str, Any]:
        """
        Get security and audit statistics.

        Returns:
            Security statistics
        """
        total_transactions = len(self.escrow_transactions)
        blocked_transactions = len([log for log in self.transaction_audit_log
                                   if log["action"] == "TRANSACTION_SECURITY_CHECK"
                                   and not log["details"]["result"]["approved"]])

        suspicious_activities = sum(len(activities) for activities in self.suspicious_activities.values())

        return {
            "audit_enabled": self.audit_enabled,
            "security_checks_enabled": self.security_checks_enabled,
            "total_audit_entries": len(self.transaction_audit_log),
            "total_transactions": total_transactions,
            "blocked_transactions": blocked_transactions,
            "block_rate": blocked_transactions / max(total_transactions, 1),
            "suspicious_activities": suspicious_activities,
            "active_limits": len(self.transaction_limits),
            "max_transaction_value": self.max_transaction_value,
            "suspicious_threshold": self.suspicious_activity_threshold,
            "transaction_cooldown": self.transaction_cooldown_seconds
        }

    def export_audit_logs(self, filename: str):
        """
        Export audit logs to file.

        Args:
            filename: Output filename
        """
        try:
            with open(filename, 'w') as f:
                json.dump({
                    "export_timestamp": time.time(),
                    "audit_logs": self.transaction_audit_log,
                    "security_stats": self.get_security_stats()
                }, f, indent=2, default=str)
            print(f"✅ Audit logs exported to {filename}")
        except Exception as e:
            print(f"❌ Error exporting audit logs: {e}")

    def enable_security_features(self, audit: bool = True, security_checks: bool = True):
        """
        Enable or disable security features.

        Args:
            audit: Enable audit logging
            security_checks: Enable security checks
        """
        self.audit_enabled = audit
        self.security_checks_enabled = security_checks

        status = f"audit={'enabled' if audit else 'disabled'}, security_checks={'enabled' if security_checks else 'disabled'}"
        print(f"🔒 Security features updated: {status}")

        self._audit_log("SYSTEM", "SECURITY_FEATURES_UPDATED", {
            "audit_enabled": audit,
            "security_checks_enabled": security_checks
        })


# Instancia global del gestor de transacciones
transaction_manager = TransactionManager()