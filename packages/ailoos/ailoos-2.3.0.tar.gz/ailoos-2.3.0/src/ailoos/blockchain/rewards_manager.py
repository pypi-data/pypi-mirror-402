"""
Módulo de gestión de recompensas para integración Ailoos-DracmaS.

Proporciona funcionalidades para reclamar recompensas de nodos,
consultar recompensas pendientes y operaciones por lotes.
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
class PendingRewards:
    """Recompensas pendientes de un nodo."""
    node_id: str
    amount: float
    last_updated: int
    claimable_at: Optional[int] = None


@dataclass
class RewardClaim:
    """Reclamo de recompensas."""
    node_id: str
    amount: float
    transaction_hash: str
    claimed_at: int
    status: str


@dataclass
class BatchRewardClaim:
    """Reclamo por lotes de recompensas."""
    claims: List[RewardClaim]
    batch_id: str
    total_amount: float
    processed_at: int


class RewardsManagerError(Exception):
    """Error en operaciones de gestión de recompensas."""
    pass


class RewardsManager:
    """
    Gestor de recompensas para integración Ailoos-DracmaS.

    Maneja el reclamo de recompensas, consulta de pendientes
    y operaciones por lotes a través del puente cross-chain.
    """

    def __init__(self, bridge_client: Optional[BridgeClient] = None):
        """
        Inicializar gestor de recompensas.

        Args:
            bridge_client: Cliente del puente opcional
        """
        self.bridge_client = bridge_client or get_bridge_client()
        self.config = get_dracmas_config()
        logger.info("🔗 RewardsManager initialized")

    async def claim_node_rewards(self, node_id: str) -> Dict[str, Any]:
        """
        Reclamar recompensas para un nodo específico.

        Args:
            node_id: ID del nodo

        Returns:
            Resultado del reclamo

        Raises:
            RewardsManagerError: Si hay error en el reclamo
        """
        try:
            # Validar node_id
            self._validate_node_id(node_id)

            logger.info(f"💰 Claiming rewards for node {node_id}")

            # Reclamar vía puente
            result = await self.bridge_client.claim_rewards(node_id=node_id)

            if result.get('success'):
                # Extraer información del reclamo
                amount = result.get('amount', 0.0)
                tx_hash = result.get('transaction_hash', '')

                claim = RewardClaim(
                    node_id=node_id,
                    amount=amount,
                    transaction_hash=tx_hash,
                    claimed_at=int(time.time()),
                    status='completed'
                )

                logger.info(f"✅ Rewards claimed successfully for node {node_id}: {amount} tokens")

                return {
                    "success": True,
                    "claim": claim,
                    "message": f"Successfully claimed {amount} tokens for node {node_id}"
                }
            else:
                error_msg = result.get('error', 'Unknown claim error')
                logger.error(f"❌ Failed to claim rewards for node {node_id}: {error_msg}")
                raise RewardsManagerError(f"Claim failed: {error_msg}")

        except BridgeClientError as e:
            logger.error(f"❌ Bridge error claiming rewards for node {node_id}: {e}")
            raise RewardsManagerError(f"Bridge communication error: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error claiming rewards for node {node_id}: {e}")
            raise RewardsManagerError(f"Unexpected error: {e}")

    async def get_pending_rewards(self, node_id: str) -> PendingRewards:
        """
        Consultar recompensas pendientes para un nodo.

        Args:
            node_id: ID del nodo

        Returns:
            Recompensas pendientes

        Raises:
            RewardsManagerError: Si hay error en consulta
        """
        try:
            # Validar node_id
            self._validate_node_id(node_id)

            logger.info(f"🔍 Querying pending rewards for node {node_id}")
            result = await self.bridge_client.get_pending_rewards(node_id)
            pending_amount = (
                result.get('amount')
                or result.get('pending_amount')
                or result.get('pending')
                or 0.0
            )
            claimable_at = result.get('claimable_at') or result.get('next_claim_at')
            last_updated = result.get('last_updated', int(time.time()))

            pending_rewards = PendingRewards(
                node_id=node_id,
                amount=float(pending_amount),
                last_updated=int(last_updated),
                claimable_at=int(claimable_at) if claimable_at else None
            )

            logger.info(f"✅ Pending rewards for node {node_id}: {pending_rewards.amount} tokens")
            return pending_rewards

        except BridgeClientError as e:
            logger.error(f"❌ Bridge error getting pending rewards for node {node_id}: {e}")
            raise RewardsManagerError(f"Bridge communication error: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error getting pending rewards for node {node_id}: {e}")
            raise RewardsManagerError(f"Unexpected error: {e}")

    async def batch_claim_rewards(self, node_ids: List[str]) -> Dict[str, Any]:
        """
        Reclamar recompensas para múltiples nodos en lote.

        Args:
            node_ids: Lista de IDs de nodos

        Returns:
            Resultado del reclamo por lotes

        Raises:
            RewardsManagerError: Si hay error en reclamo por lotes
        """
        try:
            if not node_ids:
                raise RewardsManagerError("Node IDs list cannot be empty")

            if len(node_ids) > 50:  # Límite razonable
                raise RewardsManagerError("Maximum 50 nodes per batch claim")

            # Validar todos los node_ids
            for node_id in node_ids:
                self._validate_node_id(node_id)

            logger.info(f"📦 Batch claiming rewards for {len(node_ids)} nodes")

            # Procesar reclamos en lote
            successful_claims = []
            failed_claims = []
            total_amount = 0.0

            for node_id in node_ids:
                try:
                    result = await self.claim_node_rewards(node_id)
                    claim = result['claim']
                    successful_claims.append(claim)
                    total_amount += claim.amount
                except Exception as e:
                    logger.warning(f"Failed to claim rewards for node {node_id}: {e}")
                    failed_claims.append({
                        'node_id': node_id,
                        'error': str(e)
                    })

            batch_claim = BatchRewardClaim(
                claims=successful_claims,
                batch_id=f"batch_claim_{int(time.time())}_{len(node_ids)}",
                total_amount=total_amount,
                processed_at=int(time.time())
            )

            result = {
                "success": len(successful_claims) > 0,
                "batch_claim": batch_claim,
                "successful_count": len(successful_claims),
                "failed_count": len(failed_claims),
                "failed_claims": failed_claims,
                "message": f"Batch claim completed: {len(successful_claims)} successful, {len(failed_claims)} failed"
            }

            logger.info(f"✅ Batch claim completed: {len(successful_claims)}/{len(node_ids)} successful, total {total_amount} tokens")
            return result

        except Exception as e:
            logger.error(f"❌ Unexpected error in batch claim: {e}")
            raise RewardsManagerError(f"Batch claim error: {e}")

    def _validate_node_id(self, node_id: str):
        """Validar ID del nodo."""
        if not isinstance(node_id, str) or not node_id.strip():
            raise RewardsManagerError("Node ID must be a non-empty string")
        if len(node_id) > 100:
            raise RewardsManagerError("Node ID must be less than 100 characters")

    def _calculate_pending_rewards(self, node_id: str) -> float:
        """
        Calcular recompensas pendientes para un nodo (simulado).

        En producción, esto consultaría el contrato inteligente
        basado en el historial de trabajo del nodo.
        """
        # Simulación basada en hash del node_id para consistencia
        import hashlib
        hash_value = int(hashlib.md5(node_id.encode()).hexdigest()[:8], 16)
        # Generar un valor entre 0.1 y 10.0 tokens
        pending_amount = 0.1 + (hash_value % 100) * 0.099
        return round(pending_amount, 4)

    def _calculate_proportional_distribution(
        self,
        total_rewards: float,
        node_contributions: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calcular distribución proporcional de recompensas.

        Args:
            total_rewards: Total de recompensas a distribuir
            node_contributions: Contribuciones de cada nodo

        Returns:
            Distribución proporcional por nodo
        """
        total_contribution = sum(node_contributions.values())

        if total_contribution == 0:
            return {node_id: 0.0 for node_id in node_contributions.keys()}

        distribution = {}
        for node_id, contribution in node_contributions.items():
            proportional_reward = (contribution / total_contribution) * total_rewards
            distribution[node_id] = round(proportional_reward, 6)

        return distribution


# Instancia global del gestor
_rewards_manager: Optional[RewardsManager] = None


def get_rewards_manager() -> RewardsManager:
    """Obtener instancia global del gestor de recompensas."""
    global _rewards_manager
    if _rewards_manager is None:
        _rewards_manager = RewardsManager()
    return _rewards_manager


def create_rewards_manager(bridge_client: Optional[BridgeClient] = None) -> RewardsManager:
    """Crear nueva instancia del gestor de recompensas."""
    return RewardsManager(bridge_client)
