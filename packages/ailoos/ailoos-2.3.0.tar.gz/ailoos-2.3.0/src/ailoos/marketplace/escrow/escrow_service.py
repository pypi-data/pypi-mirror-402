"""
Servicio de Escrow para AILOOS Marketplace.
Implementa sistema de escrow seguro con smart contracts, liberación automática,
manejo de disputas y optimización para alto volumen de transacciones.
"""

import asyncio
import json
import time
import hashlib
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

from ...blockchain.dracma_token import get_token_manager, TransactionResult
from ...core.logging import get_logger

logger = get_logger(__name__)


class EscrowStatus(Enum):
    """Estados posibles de un escrow."""
    PENDING = "pending"
    DEPLOYING = "deploying"
    FUNDED = "funded"
    VERIFICATION_PENDING = "verification_pending"
    RELEASED = "released"
    REFUNDED = "refunded"
    DISPUTED = "disputed"
    TIMED_OUT = "timed_out"
    FAILED = "failed"


class DisputeReason(Enum):
    """Razones para disputas."""
    DATA_NOT_DELIVERED = "data_not_delivered"
    DATA_CORRUPTED = "data_corrupted"
    DATA_LOW_QUALITY = "data_low_quality"
    INCORRECT_DESCRIPTION = "incorrect_description"
    PAYMENT_ISSUE = "payment_issue"
    OTHER = "other"


class VerificationMethod(Enum):
    """Métodos de verificación para liberación automática."""
    ORACLE = "oracle"
    CONSENSUS = "consensus"
    SMART_CONTRACT = "smart_contract"
    MANUAL = "manual"


@dataclass
class EscrowTransaction:
    """Transacción de escrow."""
    escrow_id: str
    buyer_address: str
    seller_address: str
    amount_dracma: float
    listing_id: str
    data_hash: str
    ipfs_cid: str
    created_at: float
    contract_address: Optional[str] = None
    funded_at: Optional[float] = None
    released_at: Optional[float] = None
    status: EscrowStatus = EscrowStatus.PENDING
    dispute_reason: Optional[DisputeReason] = None
    dispute_opened_at: Optional[float] = None
    arbitrator_decision: Optional[str] = None
    timeout_hours: int = 72  # 3 días por defecto
    verification_method: VerificationMethod = VerificationMethod.ORACLE
    events: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EscrowEvent:
    """Evento de escrow."""
    event_type: str
    escrow_id: str
    timestamp: float
    data: Dict[str, Any]


class EscrowService:
    """
    Servicio de escrow con smart contracts, liberación automática y resolución de disputas.
    Optimizado para alto volumen de transacciones.
    """

    def __init__(self, max_workers: int = 10):
        self.escrow_transactions: Dict[str, EscrowTransaction] = {}
        self.disputes: Dict[str, Dict[str, Any]] = {}
        self.arbitrators: List[str] = []
        self.token_manager = get_token_manager()

        # Configuración para alto volumen
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.verification_queue: asyncio.Queue = asyncio.Queue()

        # Configuración de timeouts y verificación
        self.default_timeout_hours = 72
        self.verification_timeout_seconds = 300  # 5 minutos
        self.auto_release_delay_hours = 24
        self.max_concurrent_verifications = 50

        # Estadísticas y monitoreo
        self.stats = {
            "total_escrows": 0,
            "successful_releases": 0,
            "disputes": 0,
            "timeouts": 0,
            "failed_deployments": 0
        }

        # Callbacks para eventos
        self.event_callbacks: Dict[str, List[Callable]] = {}

        # Iniciar tareas en background
        self._running = True
        self._verification_task = None
        self._timeout_task = None
        self._event_processor_task = None

        logger.info("🔐 EscrowService initialized")

    async def start_background_tasks(self):
        """Inicia tareas en background para procesamiento automático."""
        self._verification_task = asyncio.create_task(self._process_verifications())
        self._timeout_task = asyncio.create_task(self._process_timeouts())
        self._event_processor_task = asyncio.create_task(self._process_events())

        logger.info("🚀 Background tasks started")

    async def stop_background_tasks(self):
        """Detiene tareas en background."""
        self._running = False

        if self._verification_task:
            self._verification_task.cancel()
        if self._timeout_task:
            self._timeout_task.cancel()
        if self._event_processor_task:
            self._event_processor_task.cancel()

        await asyncio.gather(
            self._verification_task or asyncio.sleep(0),
            self._timeout_task or asyncio.sleep(0),
            self._event_processor_task or asyncio.sleep(0),
            return_exceptions=True
        )

        self.executor.shutdown(wait=True)
        logger.info("🛑 Background tasks stopped")

    async def create_escrow(self, buyer_address: str, seller_address: str,
                           amount_dracma: float, listing_id: str,
                           data_hash: str, ipfs_cid: str,
                           timeout_hours: Optional[int] = None,
                           verification_method: VerificationMethod = VerificationMethod.ORACLE) -> str:
        """
        Crea un nuevo escrow desplegando un smart contract y lockeando fondos.

        Args:
            buyer_address: Dirección del comprador
            seller_address: Dirección del vendedor
            amount_dracma: Monto en DRACMA
            listing_id: ID del listing
            data_hash: Hash de los datos
            ipfs_cid: CID de IPFS
            timeout_hours: Horas para timeout (opcional)
            verification_method: Método de verificación

        Returns:
            ID del escrow creado
        """
        try:
            # Generar ID único
            escrow_id = self._generate_escrow_id(buyer_address, seller_address, listing_id)

            # Crear transacción de escrow
            escrow = EscrowTransaction(
                escrow_id=escrow_id,
                buyer_address=buyer_address,
                seller_address=seller_address,
                amount_dracma=amount_dracma,
                listing_id=listing_id,
                data_hash=data_hash,
                ipfs_cid=ipfs_cid,
                created_at=time.time(),
                timeout_hours=timeout_hours or self.default_timeout_hours,
                verification_method=verification_method,
                status=EscrowStatus.DEPLOYING
            )

            self.escrow_transactions[escrow_id] = escrow
            self.stats["total_escrows"] += 1

            # Desplegar smart contract (simulado)
            contract_address = await self._deploy_escrow_contract(escrow)

            if not contract_address:
                escrow.status = EscrowStatus.FAILED
                self.stats["failed_deployments"] += 1
                raise ValueError("Failed to deploy escrow contract")

            escrow.contract_address = contract_address
            escrow.status = EscrowStatus.PENDING

            # Lockear fondos del comprador
            lock_result = await self._lock_funds(escrow)

            if not lock_result.success:
                escrow.status = EscrowStatus.FAILED
                raise ValueError(f"Failed to lock funds: {lock_result.error_message}")

            escrow.status = EscrowStatus.FUNDED
            escrow.funded_at = time.time()

            # Registrar evento
            await self._emit_event("escrow_created", escrow_id, {
                "buyer": buyer_address,
                "seller": seller_address,
                "amount": amount_dracma,
                "contract_address": contract_address
            })

            # Agregar a cola de verificación si es automática
            if verification_method in [VerificationMethod.ORACLE, VerificationMethod.CONSENSUS]:
                await self.verification_queue.put(escrow_id)

            logger.info(f"✅ Escrow {escrow_id} created and funded for {amount_dracma} DRACMA")
            return escrow_id

        except Exception as e:
            logger.error(f"❌ Error creating escrow: {e}")
            if escrow_id in self.escrow_transactions:
                self.escrow_transactions[escrow_id].status = EscrowStatus.FAILED
            raise

    async def release_funds(self, escrow_id: str, verification_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Libera fondos automáticamente tras verificación (oracle/consenso).

        Args:
            escrow_id: ID del escrow
            verification_data: Datos de verificación (opcional)

        Returns:
            True si la liberación fue exitosa
        """
        if escrow_id not in self.escrow_transactions:
            raise ValueError(f"Escrow {escrow_id} not found")

        escrow = self.escrow_transactions[escrow_id]

        if escrow.status != EscrowStatus.FUNDED:
            raise ValueError(f"Escrow must be funded, current status: {escrow.status.value}")

        try:
            # Verificar condiciones de liberación
            verification_passed = await self._verify_release_conditions(escrow, verification_data)

            if not verification_passed:
                escrow.status = EscrowStatus.VERIFICATION_PENDING
                await self._emit_event("verification_failed", escrow_id, {"reason": "verification_failed"})
                return False

            # Liberar fondos al vendedor
            release_result = await self.token_manager.transfer_tokens(
                from_address=escrow.contract_address or "escrow_contract",
                to_address=escrow.seller_address,
                amount=escrow.amount_dracma
            )

            if not release_result.success:
                raise ValueError(f"Failed to release funds: {release_result.error_message}")

            escrow.status = EscrowStatus.RELEASED
            escrow.released_at = time.time()
            self.stats["successful_releases"] += 1

            # Registrar evento
            await self._emit_event("funds_released", escrow_id, {
                "seller": escrow.seller_address,
                "amount": escrow.amount_dracma,
                "tx_hash": release_result.tx_hash
            })

            logger.info(f"💰 Funds released for escrow {escrow_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error releasing funds for escrow {escrow_id}: {e}")
            escrow.status = EscrowStatus.FAILED
            raise

    async def refund(self, escrow_id: str, reason: str = "buyer_request") -> bool:
        """
        Procesa devolución de fondos al comprador.

        Args:
            escrow_id: ID del escrow
            reason: Razón de la devolución

        Returns:
            True si el refund fue exitoso
        """
        if escrow_id not in self.escrow_transactions:
            raise ValueError(f"Escrow {escrow_id} not found")

        escrow = self.escrow_transactions[escrow_id]

        if escrow.status not in [EscrowStatus.FUNDED, EscrowStatus.DISPUTED]:
            raise ValueError(f"Cannot refund escrow in status: {escrow.status.value}")

        try:
            # Devolver fondos al comprador
            refund_result = await self.token_manager.transfer_tokens(
                from_address=escrow.contract_address or "escrow_contract",
                to_address=escrow.buyer_address,
                amount=escrow.amount_dracma
            )

            if not refund_result.success:
                raise ValueError(f"Failed to refund funds: {refund_result.error_message}")

            escrow.status = EscrowStatus.REFUNDED
            self.stats["successful_releases"] += 1  # Contar como liberación exitosa

            # Registrar evento
            await self._emit_event("funds_refunded", escrow_id, {
                "buyer": escrow.buyer_address,
                "amount": escrow.amount_dracma,
                "reason": reason,
                "tx_hash": refund_result.tx_hash
            })

            logger.info(f"↩️ Funds refunded for escrow {escrow_id}: {reason}")
            return True

        except Exception as e:
            logger.error(f"❌ Error refunding escrow {escrow_id}: {e}")
            raise

    async def dispute_resolution(self, escrow_id: str, initiator_address: str,
                                reason: DisputeReason, description: str,
                                arbitrator_address: Optional[str] = None) -> str:
        """
        Inicia resolución de conflicto para un escrow.

        Args:
            escrow_id: ID del escrow
            initiator_address: Dirección que inicia la disputa
            reason: Razón de la disputa
            description: Descripción detallada
            arbitrator_address: Árbitro asignado (opcional)

        Returns:
            ID de la disputa
        """
        if escrow_id not in self.escrow_transactions:
            raise ValueError(f"Escrow {escrow_id} not found")

        escrow = self.escrow_transactions[escrow_id]

        # Verificar que el iniciador sea parte de la transacción
        if initiator_address not in [escrow.buyer_address, escrow.seller_address]:
            raise ValueError("Only transaction parties can initiate disputes")

        if escrow.status not in [EscrowStatus.FUNDED, EscrowStatus.VERIFICATION_PENDING]:
            raise ValueError(f"Cannot dispute escrow in status: {escrow.status.value}")

        try:
            # Cambiar estado a disputado
            escrow.status = EscrowStatus.DISPUTED
            escrow.dispute_reason = reason
            escrow.dispute_opened_at = time.time()

            # Crear disputa
            dispute_id = f"dispute_{escrow_id}_{int(time.time())}"
            dispute = {
                "dispute_id": dispute_id,
                "escrow_id": escrow_id,
                "initiator": initiator_address,
                "reason": reason.value,
                "description": description,
                "opened_at": time.time(),
                "status": "open",
                "arbitrator": arbitrator_address or self._select_arbitrator(),
                "decision": None,
                "resolved_at": None,
                "evidence": []
            }

            self.disputes[dispute_id] = dispute
            self.stats["disputes"] += 1

            # Registrar evento
            await self._emit_event("dispute_opened", escrow_id, {
                "dispute_id": dispute_id,
                "initiator": initiator_address,
                "reason": reason.value,
                "arbitrator": dispute["arbitrator"]
            })

            logger.info(f"⚖️ Dispute opened for escrow {escrow_id}: {reason.value}")
            return dispute_id

        except Exception as e:
            logger.error(f"❌ Error opening dispute for escrow {escrow_id}: {e}")
            raise

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
            raise ValueError(f"Dispute {dispute_id} not found")

        dispute = self.disputes[dispute_id]
        escrow = self.escrow_transactions[dispute["escrow_id"]]

        # Verificar árbitro autorizado
        if arbitrator_address not in self.arbitrators and arbitrator_address != dispute["arbitrator"]:
            raise ValueError("Unauthorized arbitrator")

        if dispute["status"] != "open":
            raise ValueError("Dispute already resolved")

        try:
            # Ejecutar decisión
            if decision == "buyer":
                success = await self.refund(dispute["escrow_id"], "dispute_resolution")
            elif decision == "seller":
                success = await self.release_funds(dispute["escrow_id"])
            elif decision == "split":
                success = await self._split_funds(dispute["escrow_id"])
            else:
                raise ValueError(f"Invalid decision: {decision}")

            if success:
                dispute["status"] = "resolved"
                dispute["decision"] = decision
                dispute["notes"] = notes
                dispute["resolved_at"] = time.time()

                escrow.arbitrator_decision = decision

                # Registrar evento
                await self._emit_event("dispute_resolved", dispute["escrow_id"], {
                    "dispute_id": dispute_id,
                    "decision": decision,
                    "arbitrator": arbitrator_address
                })

                logger.info(f"⚖️ Dispute {dispute_id} resolved: {decision}")
                return True

        except Exception as e:
            logger.error(f"❌ Error resolving dispute {dispute_id}: {e}")
            raise

    # Métodos internos

    async def _deploy_escrow_contract(self, escrow: EscrowTransaction) -> Optional[str]:
        """Despliega smart contract de escrow (simulado)."""
        try:
            # Simular deployment
            contract_address = f"0x{hashlib.sha256(f'escrow_{escrow.escrow_id}'.encode()).hexdigest()[:40]}"

            # En implementación real, aqui iria el deployment via bridge EmpoorioChain
            await asyncio.sleep(0.1)  # Simular tiempo de deployment

            logger.info(f"📄 Deployed escrow contract: {contract_address}")
            return contract_address

        except Exception as e:
            logger.error(f"❌ Error deploying escrow contract: {e}")
            return None

    async def _lock_funds(self, escrow: EscrowTransaction) -> TransactionResult:
        """Lockea fondos del comprador en el contrato."""
        return await self.token_manager.transfer_tokens(
            from_address=escrow.buyer_address,
            to_address=escrow.contract_address or "escrow_contract",
            amount=escrow.amount_dracma
        )

    async def _verify_release_conditions(self, escrow: EscrowTransaction,
                                       verification_data: Optional[Dict[str, Any]] = None) -> bool:
        """Verifica condiciones para liberación automática."""
        try:
            if escrow.verification_method == VerificationMethod.ORACLE:
                return await self._verify_with_oracle(escrow, verification_data)
            elif escrow.verification_method == VerificationMethod.CONSENSUS:
                return await self._verify_with_consensus(escrow, verification_data)
            elif escrow.verification_method == VerificationMethod.SMART_CONTRACT:
                return await self._verify_with_smart_contract(escrow)
            else:
                return False
        except Exception as e:
            logger.error(f"❌ Error verifying release conditions: {e}")
            return False

    async def _verify_with_oracle(self, escrow: EscrowTransaction,
                                 verification_data: Optional[Dict[str, Any]] = None) -> bool:
        """Verificación usando oracle (simulado)."""
        # Simular verificación de oracle
        await asyncio.sleep(0.05)  # Simular consulta a oracle

        # Verificar hash de datos (simulado)
        if verification_data and verification_data.get("data_hash") == escrow.data_hash:
            return True

        # Verificación básica: tiempo mínimo transcurrido
        time_since_funded = time.time() - (escrow.funded_at or escrow.created_at)
        return time_since_funded > (self.auto_release_delay_hours * 3600)

    async def _verify_with_consensus(self, escrow: EscrowTransaction,
                                    verification_data: Optional[Dict[str, Any]] = None) -> bool:
        """Verificación usando consenso (simulado)."""
        # Simular consenso de nodos
        await asyncio.sleep(0.1)

        # Simular aprobación por mayoría
        consensus_votes = sum(1 for _ in range(5) if asyncio.get_event_loop().time() % 2 == 0)
        return consensus_votes >= 3

    async def _verify_with_smart_contract(self, escrow: EscrowTransaction) -> bool:
        """Verificación usando smart contract (simulado)."""
        # Simular llamada a contrato
        await asyncio.sleep(0.02)
        return True  # Siempre pasa en simulación

    async def _split_funds(self, escrow_id: str) -> bool:
        """Divide fondos entre comprador y vendedor."""
        escrow = self.escrow_transactions[escrow_id]
        half_amount = escrow.amount_DracmaS / 2

        buyer_result = await self.token_manager.transfer_tokens(
            from_address=escrow.contract_address or "escrow_contract",
            to_address=escrow.buyer_address,
            amount=half_amount
        )

        seller_result = await self.token_manager.transfer_tokens(
            from_address=escrow.contract_address or "escrow_contract",
            to_address=escrow.seller_address,
            amount=half_amount
        )

        if buyer_result.success and seller_result.success:
            escrow.status = EscrowStatus.RELEASED
            escrow.arbitrator_decision = "split"
            return True
        return False

    def _select_arbitrator(self) -> str:
        """Selecciona árbitro aleatoriamente."""
        if self.arbitrators:
            return self.arbitrators[int(time.time()) % len(self.arbitrators)]
        return "default_arbitrator"

    async def _emit_event(self, event_type: str, escrow_id: str, data: Dict[str, Any]):
        """Emite evento de escrow."""
        event = EscrowEvent(
            event_type=event_type,
            escrow_id=escrow_id,
            timestamp=time.time(),
            data=data
        )

        await self.event_queue.put(event)

        # Llamar callbacks registrados
        if event_type in self.event_callbacks:
            for callback in self.event_callbacks[event_type]:
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"Error in event callback: {e}")

    async def _process_verifications(self):
        """Procesa verificaciones en background."""
        while self._running:
            try:
                escrow_id = await asyncio.wait_for(
                    self.verification_queue.get(),
                    timeout=1.0
                )

                if escrow_id in self.escrow_transactions:
                    escrow = self.escrow_transactions[escrow_id]
                    if escrow.status == EscrowStatus.FUNDED:
                        try:
                            success = await self.release_funds(escrow_id)
                            if success:
                                logger.info(f"🔄 Auto-released escrow {escrow_id}")
                        except Exception as e:
                            logger.error(f"Error auto-releasing escrow {escrow_id}: {e}")

                self.verification_queue.task_done()

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in verification processor: {e}")

    async def _process_timeouts(self):
        """Procesa timeouts de escrows."""
        while self._running:
            try:
                await asyncio.sleep(300)  # Revisar cada 5 minutos

                current_time = time.time()
                timed_out = []

                for escrow_id, escrow in self.escrow_transactions.items():
                    if escrow.status in [EscrowStatus.FUNDED, EscrowStatus.VERIFICATION_PENDING]:
                        timeout_time = escrow.created_at + (escrow.timeout_hours * 3600)
                        if current_time > timeout_time:
                            timed_out.append(escrow_id)

                for escrow_id in timed_out:
                    escrow = self.escrow_transactions[escrow_id]
                    escrow.status = EscrowStatus.TIMED_OUT
                    self.stats["timeouts"] += 1

                    # Refund automático en timeout
                    try:
                        await self.refund(escrow_id, "timeout")
                        await self._emit_event("escrow_timeout", escrow_id, {"refunded": True})
                        logger.info(f"⏰ Escrow {escrow_id} timed out and refunded")
                    except Exception as e:
                        logger.error(f"Error refunding timed out escrow {escrow_id}: {e}")

            except Exception as e:
                logger.error(f"Error in timeout processor: {e}")

    async def _process_events(self):
        """Procesa cola de eventos."""
        while self._running:
            try:
                event = await self.event_queue.get()
                # Aquí se podría enviar a un sistema de eventos externo
                logger.debug(f"📢 Event: {event.event_type} for escrow {event.escrow_id}")
                self.event_queue.task_done()
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    def _generate_escrow_id(self, buyer: str, seller: str, listing_id: str) -> str:
        """Genera ID único para escrow."""
        data = f"{buyer}_{seller}_{listing_id}_{time.time()}_{hashlib.sha256(buyer.encode()).hexdigest()[:8]}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    # Métodos públicos adicionales

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
            "status": escrow.status.value,
            "created_at": escrow.created_at,
            "funded_at": escrow.funded_at,
            "released_at": escrow.released_at,
            "contract_address": escrow.contract_address,
            "timeout_hours": escrow.timeout_hours,
            "verification_method": escrow.verification_method.value,
            "dispute_reason": escrow.dispute_reason.value if escrow.dispute_reason else None
        }

    def get_escrow_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del servicio de escrow."""
        return {
            **self.stats,
            "active_escrows": len([e for e in self.escrow_transactions.values()
                                  if e.status in [EscrowStatus.FUNDED, EscrowStatus.VERIFICATION_PENDING]]),
            "pending_verifications": self.verification_queue.qsize(),
            "open_disputes": len([d for d in self.disputes.values() if d["status"] == "open"])
        }

    def add_arbitrator(self, arbitrator_address: str):
        """Añade árbitro autorizado."""
        if arbitrator_address not in self.arbitrators:
            self.arbitrators.append(arbitrator_address)

    def register_event_callback(self, event_type: str, callback: Callable):
        """Registra callback para eventos."""
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        self.event_callbacks[event_type].append(callback)

    async def force_verification_check(self, escrow_id: str) -> bool:
        """Fuerza verificación de un escrow."""
        if escrow_id not in self.escrow_transactions:
            return False

        escrow = self.escrow_transactions[escrow_id]
        if escrow.status == EscrowStatus.FUNDED:
            return await self.release_funds(escrow_id)
        return False
