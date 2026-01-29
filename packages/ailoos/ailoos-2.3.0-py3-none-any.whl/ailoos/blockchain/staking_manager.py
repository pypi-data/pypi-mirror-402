"""
Staking Manager - Gestor completo de staking DRACMA
Maneja staking de tokens, contratos inteligentes, rewards y gobernanza.
"""

import asyncio
import json
import time
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from ..core.logging import get_logger
from .wallet_manager import get_wallet_manager, WalletManager
from .dracma_token import get_token_manager, DRACMATokenManager

logger = get_logger(__name__)


class StakingTier(Enum):
    """Niveles de staking basados en cantidad."""
    BRONZE = "bronze"      # 0 - 100 DRACMA
    SILVER = "silver"      # 100 - 1000 DRACMA
    GOLD = "gold"          # 1000 - 10000 DRACMA
    PLATINUM = "platinum"  # 10000+ DRACMA


class ProposalStatus(Enum):
    """Estados de propuestas de gobernanza."""
    DRAFT = "draft"
    ACTIVE = "active"
    PASSED = "passed"
    REJECTED = "rejected"
    EXECUTED = "executed"


@dataclass
class StakingPosition:
    """Posición de staking individual."""
    stake_id: str
    wallet_id: str
    amount: float
    tier: StakingTier
    staked_at: datetime
    lock_period_days: int
    unlock_date: datetime
    apr: float  # Annual Percentage Rate
    accumulated_rewards: float = 0.0
    is_active: bool = True
    auto_compound: bool = False

    def calculate_rewards(self, current_time: datetime) -> float:
        """Calcular rewards acumulados hasta ahora."""
        if not self.is_active:
            return self.accumulated_rewards

        days_staked = (current_time - self.staked_at).days
        if days_staked <= 0:
            return 0.0

        # Rewards diarios = (amount * apr / 365)
        daily_reward = (self.amount * self.apr / 365)
        total_rewards = daily_reward * min(days_staked, self.lock_period_days)

        return max(0, total_rewards)

    def can_unstake(self, current_time: datetime) -> bool:
        """Verificar si se puede hacer unstake."""
        return current_time >= self.unlock_date


@dataclass
class GovernanceProposal:
    """Propuesta de gobernanza."""
    proposal_id: str
    title: str
    description: str
    proposer_wallet: str
    proposed_changes: Dict[str, Any]
    stake_requirement: float  # Stake mínimo para proponer
    voting_period_days: int
    created_at: datetime
    status: ProposalStatus = ProposalStatus.DRAFT
    votes_for: float = 0.0  # Total stake votando a favor
    votes_against: float = 0.0  # Total stake votando en contra
    voters: Dict[str, str] = field(default_factory=dict)  # wallet_id -> vote (for/against)
    executed_at: Optional[datetime] = None

    def add_vote(self, wallet_id: str, stake_amount: float, vote_for: bool):
        """Añadir voto a la propuesta."""
        if wallet_id in self.voters:
            # Remover voto anterior
            old_vote = self.voters[wallet_id]
            if old_vote == "for":
                self.votes_for -= stake_amount
            else:
                self.votes_against -= stake_amount

        # Añadir nuevo voto
        if vote_for:
            self.votes_for += stake_amount
            self.voters[wallet_id] = "for"
        else:
            self.votes_against += stake_amount
            self.voters[wallet_id] = "against"

    def get_total_votes(self) -> float:
        """Obtener total de stake votado."""
        return self.votes_for + self.votes_against

    def is_passed(self) -> bool:
        """Verificar si la propuesta pasó."""
        total_votes = self.get_total_votes()
        return total_votes > 0 and (self.votes_for / total_votes) > 0.5

    def can_execute(self, current_time: datetime) -> bool:
        """Verificar si se puede ejecutar la propuesta."""
        voting_end = self.created_at + timedelta(days=self.voting_period_days)
        return current_time >= voting_end and self.status == ProposalStatus.ACTIVE


@dataclass
class StakingContract:
    """Contrato inteligente simulado para staking."""
    contract_id: str
    staker_address: str
    amount: float
    duration_days: int
    apr: float
    created_at: datetime
    bytecode: str = ""  # Simulación de bytecode
    is_active: bool = True

    def execute_unstake(self) -> Dict[str, Any]:
        """Ejecutar unstake del contrato."""
        if not self.is_active:
            return {"success": False, "error": "Contract not active"}

        # Calcular penalización si unstake temprano
        days_remaining = self._calculate_days_remaining()
        penalty = 0.0

        if days_remaining > 0:
            penalty = self.amount * 0.05  # 5% penalty for early unstake

        return {
            "success": True,
            "return_amount": self.amount - penalty,
            "penalty": penalty,
            "rewards": self._calculate_rewards()
        }

    def _calculate_days_remaining(self) -> int:
        """Calcular días restantes del lock period."""
        end_date = self.created_at + timedelta(days=self.duration_days)
        remaining = (end_date - datetime.now()).days
        return max(0, remaining)

    def _calculate_rewards(self) -> float:
        """Calcular rewards acumulados."""
        days_staked = (datetime.now() - self.created_at).days
        daily_reward = self.amount * self.apr / 365
        return daily_reward * min(days_staked, self.duration_days)


class StakingManager:
    """
    Gestor completo de staking DracmaS con contratos inteligentes simulados.

    Características:
    - Staking con diferentes tiers y APRs
    - Contratos inteligentes simulados
    - Sistema de rewards automático
    - Gobernanza básica con votaciones por stake
    - Auto-compounding opcional
    - Lock periods flexibles
    """

    def __init__(self):
        self.wallet_manager = get_wallet_manager()
        self.token_manager = get_token_manager()

        # Estado del sistema de staking
        self.staking_positions: Dict[str, List[StakingPosition]] = {}
        self.staking_contracts: Dict[str, StakingContract] = {}
        self.governance_proposals: Dict[str, GovernanceProposal] = {}

        # Configuración de staking
        self.base_apr = 0.05  # 5% base APR
        self.tier_multipliers = {
            StakingTier.BRONZE: 1.0,
            StakingTier.SILVER: 1.2,
            StakingTier.GOLD: 1.5,
            StakingTier.PLATINUM: 2.0
        }

        # Configuración de gobernanza
        self.min_stake_to_propose = 100.0  # DracmaS mínimos para proponer
        self.voting_period_days = 7
        self.execution_delay_hours = 24

        # Estadísticas globales
        self.total_staked = 0.0
        self.total_stakers = 0

        # Tarea de rewards automática
        self.reward_task: Optional[asyncio.Task] = None
        self._start_reward_distribution()

        logger.info("🔒 Staking Manager initialized")

    def _start_reward_distribution(self):
        """Iniciar distribución automática de rewards."""
        self.reward_task = asyncio.create_task(self._distribute_rewards_loop())

    async def _distribute_rewards_loop(self):
        """Loop de distribución de rewards cada hora."""
        while True:
            try:
                await self._distribute_hourly_rewards()
                await asyncio.sleep(3600)  # 1 hora
            except Exception as e:
                logger.error(f"Error in reward distribution: {e}")
                await asyncio.sleep(60)  # Reintentar en 1 minuto

    async def _distribute_hourly_rewards(self):
        """Distribuir rewards por hora."""
        current_time = datetime.now()

        for wallet_id, positions in self.staking_positions.items():
            for position in positions:
                if position.is_active:
                    # Calcular rewards de esta hora
                    hourly_reward = position.amount * position.apr / (365 * 24)

                    if position.auto_compound:
                        # Auto-compound: añadir a stake
                        position.amount += hourly_reward
                        position.accumulated_rewards += hourly_reward
                    else:
                        # Añadir a rewards acumulados
                        position.accumulated_rewards += hourly_reward

                    # Actualizar wallet
                    wallet_info = self.wallet_manager.wallets.get(wallet_id)
                    if wallet_info:
                        wallet_info.rewards_earned += hourly_reward
                        wallet_info.last_activity = current_time

        logger.debug("💰 Hourly staking rewards distributed")

    def _calculate_tier(self, amount: float) -> StakingTier:
        """Calcular tier basado en cantidad staked."""
        if amount >= 10000:
            return StakingTier.PLATINUM
        elif amount >= 1000:
            return StakingTier.GOLD
        elif amount >= 100:
            return StakingTier.SILVER
        else:
            return StakingTier.BRONZE

    def _calculate_apr(self, amount: float, lock_period_days: int) -> float:
        """Calcular APR basado en cantidad y lock period."""
        tier = self._calculate_tier(amount)
        tier_multiplier = self.tier_multipliers[tier]

        # Bonus por lock period (máximo 2x por 365 días)
        lock_bonus = min(lock_period_days / 365, 2.0)

        return self.base_apr * tier_multiplier * (1 + lock_bonus)

    async def stake_tokens(self, wallet_id: str, amount: float,
                           lock_period_days: int = 30,
                           auto_compound: bool = False) -> Dict[str, Any]:
        """
        Stakear tokens con contrato real en DracmaS.

        Args:
            wallet_id: ID de la wallet
            amount: Cantidad a stakear
            lock_period_days: Período de lock en días
            auto_compound: Si auto-compound rewards

        Returns:
            Resultado del staking
        """
        try:
            # Verificar wallet
            if wallet_id not in self.wallet_manager.wallets:
                return {'success': False, 'error': 'Wallet not found'}

            wallet_info = self.wallet_manager.wallets[wallet_id]

            # Verificar balance suficiente
            if wallet_info.balance < amount:
                return {'success': False, 'error': 'Insufficient balance'}

            # Ejecutar staking real a través del token manager
            result = await self.token_manager.stake_tokens(wallet_info.address, amount)

            if not result.success:
                return {'success': False, 'error': result.error_message or 'Staking failed'}

            # Calcular parámetros para tracking local
            apr = self._calculate_apr(amount, lock_period_days)
            tier = self._calculate_tier(amount)
            unlock_date = datetime.now() + timedelta(days=lock_period_days)

            # Crear posición de staking para tracking
            stake_id = f"stake_{wallet_id}_{int(time.time())}_{uuid.uuid4().hex[:8]}"

            position = StakingPosition(
                stake_id=stake_id,
                wallet_id=wallet_id,
                amount=amount,
                tier=tier,
                staked_at=datetime.now(),
                lock_period_days=lock_period_days,
                unlock_date=unlock_date,
                apr=apr,
                auto_compound=auto_compound
            )

            # Actualizar estado local
            if wallet_id not in self.staking_positions:
                self.staking_positions[wallet_id] = []
            self.staking_positions[wallet_id].append(position)

            # Actualizar estadísticas globales
            self.total_staked += amount
            self.total_stakers = len(self.staking_positions)

            # Actualizar wallet
            wallet_info.balance -= amount
            wallet_info.staked_amount += amount
            wallet_info.transaction_count += 1
            wallet_info.last_activity = datetime.now()

            # Guardar cambios
            self.wallet_manager._save_wallet(wallet_id)

            logger.info(f"🔒 Staked {amount} DracmaS for {wallet_id} via real contract (APR: {apr:.1%}, Tier: {tier.value})")

            return {
                'success': True,
                'stake_id': stake_id,
                'tx_hash': result.tx_hash,
                'amount': amount,
                'apr': apr,
                'tier': tier.value,
                'unlock_date': unlock_date.isoformat(),
                'auto_compound': auto_compound
            }

        except Exception as e:
            logger.error(f"Error staking tokens: {e}")
            return {'success': False, 'error': str(e)}

    async def unstake_tokens(self, wallet_id: str, stake_id: str) -> Dict[str, Any]:
        """
        Unstakear tokens específicos.

        Args:
            wallet_id: ID de la wallet
            stake_id: ID del stake a unstake

        Returns:
            Resultado del unstake
        """
        try:
            if wallet_id not in self.staking_positions:
                return {'success': False, 'error': 'No staking positions found'}

            # Encontrar posición
            position = None
            for pos in self.staking_positions[wallet_id]:
                if pos.stake_id == stake_id:
                    position = pos
                    break

            if not position:
                return {'success': False, 'error': 'Staking position not found'}

            current_time = datetime.now()

            # Verificar si se puede unstake
            if not position.can_unstake(current_time):
                days_remaining = (position.unlock_date - current_time).days
                return {
                    'success': False,
                    'error': f'Cannot unstake yet. {days_remaining} days remaining'
                }

            # Ejecutar unstake real
            wallet_info = self.wallet_manager.wallets[wallet_id]
            unstake_result = await self.token_manager.unstake_tokens(wallet_info.address, position.amount)

            if not unstake_result.success:
                return {'success': False, 'error': unstake_result.error_message or 'Unstaking failed'}

            # Calcular rewards locales
            rewards = position.accumulated_rewards
            return_amount = position.amount  # Sin penalización por ahora

            # Actualizar posición
            position.is_active = False

            # Actualizar wallet
            wallet_info.balance += return_amount + rewards
            wallet_info.staked_amount -= position.amount
            wallet_info.rewards_earned += rewards
            wallet_info.last_activity = current_time

            # Actualizar estadísticas globales
            self.total_staked -= position.amount

            # Guardar cambios
            self.wallet_manager._save_wallet(wallet_id)

            logger.info(f"🔓 Unstaked {return_amount} DracmaS for {wallet_id} via real contract (rewards: {rewards})")

            return {
                'success': True,
                'stake_id': stake_id,
                'tx_hash': unstake_result.tx_hash,
                'return_amount': return_amount,
                'penalty': 0.0,
                'rewards': rewards,
                'total_return': return_amount + rewards
            }

        except Exception as e:
            logger.error(f"Error unstaking tokens: {e}")
            return {'success': False, 'error': str(e)}

    def get_staking_info(self, wallet_id: str) -> Dict[str, Any]:
        """
        Obtener información completa de staking de una wallet.

        Args:
            wallet_id: ID de la wallet

        Returns:
            Información de staking
        """
        try:
            positions = self.staking_positions.get(wallet_id, [])
            active_positions = [p for p in positions if p.is_active]

            if not active_positions:
                return {
                    'wallet_id': wallet_id,
                    'total_staked': 0.0,
                    'active_positions': 0,
                    'total_rewards': 0.0,
                    'positions': []
                }

            current_time = datetime.now()
            total_staked = sum(p.amount for p in active_positions)
            total_rewards = sum(p.calculate_rewards(current_time) for p in active_positions)

            positions_info = []
            for pos in active_positions:
                positions_info.append({
                    'stake_id': pos.stake_id,
                    'amount': pos.amount,
                    'tier': pos.tier.value,
                    'apr': pos.apr,
                    'staked_at': pos.staked_at.isoformat(),
                    'unlock_date': pos.unlock_date.isoformat(),
                    'days_remaining': max(0, (pos.unlock_date - current_time).days),
                    'accumulated_rewards': pos.accumulated_rewards,
                    'auto_compound': pos.auto_compound
                })

            return {
                'wallet_id': wallet_id,
                'total_staked': total_staked,
                'active_positions': len(active_positions),
                'total_rewards': total_rewards,
                'average_apr': sum(p.apr for p in active_positions) / len(active_positions),
                'positions': positions_info
            }

        except Exception as e:
            logger.error(f"Error getting staking info for {wallet_id}: {e}")
            return {'error': str(e)}

    async def create_proposal(self, proposer_wallet: str, title: str,
                            description: str, changes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear una nueva propuesta de gobernanza.

        Args:
            proposer_wallet: Wallet del proponente
            title: Título de la propuesta
            description: Descripción detallada
            changes: Cambios propuestos

        Returns:
            Resultado de la creación
        """
        try:
            # Verificar stake mínimo
            staking_info = self.get_staking_info(proposer_wallet)
            if staking_info.get('total_staked', 0) < self.min_stake_to_propose:
                return {
                    'success': False,
                    'error': f'Insufficient stake. Need at least {self.min_stake_to_propose} DracmaS staked'
                }

            # Crear propuesta
            proposal_id = f"proposal_{int(time.time())}_{uuid.uuid4().hex[:8]}"

            proposal = GovernanceProposal(
                proposal_id=proposal_id,
                title=title,
                description=description,
                proposer_wallet=proposer_wallet,
                proposed_changes=changes,
                stake_requirement=self.min_stake_to_propose,
                voting_period_days=self.voting_period_days,
                created_at=datetime.now(),
                status=ProposalStatus.ACTIVE
            )

            self.governance_proposals[proposal_id] = proposal

            logger.info(f"📋 Created governance proposal: {title} by {proposer_wallet}")

            return {
                'success': True,
                'proposal_id': proposal_id,
                'title': title,
                'voting_ends': (datetime.now() + timedelta(days=self.voting_period_days)).isoformat()
            }

        except Exception as e:
            logger.error(f"Error creating proposal: {e}")
            return {'success': False, 'error': str(e)}

    async def vote_on_proposal(self, voter_wallet: str, proposal_id: str,
                             vote_for: bool, reasoning: str = "") -> Dict[str, Any]:
        """
        Votar en una propuesta de gobernanza.

        Args:
            voter_wallet: Wallet del votante
            proposal_id: ID de la propuesta
            vote_for: True para votar a favor
            reasoning: Razón del voto

        Returns:
            Resultado del voto
        """
        try:
            if proposal_id not in self.governance_proposals:
                return {'success': False, 'error': 'Proposal not found'}

            proposal = self.governance_proposals[proposal_id]

            if proposal.status != ProposalStatus.ACTIVE:
                return {'success': False, 'error': 'Proposal not active'}

            # Verificar stake del votante
            staking_info = self.get_staking_info(voter_wallet)
            stake_amount = staking_info.get('total_staked', 0)

            if stake_amount == 0:
                return {'success': False, 'error': 'Must have staked tokens to vote'}

            # Añadir voto
            proposal.add_vote(voter_wallet, stake_amount, vote_for)

            logger.info(f"🗳️ Vote cast on proposal {proposal_id} by {voter_wallet}: {'FOR' if vote_for else 'AGAINST'}")

            return {
                'success': True,
                'proposal_id': proposal_id,
                'vote': 'for' if vote_for else 'against',
                'stake_used': stake_amount
            }

        except Exception as e:
            logger.error(f"Error voting on proposal: {e}")
            return {'success': False, 'error': str(e)}

    def get_proposals(self, status_filter: Optional[ProposalStatus] = None) -> List[Dict[str, Any]]:
        """
        Obtener lista de propuestas de gobernanza.

        Args:
            status_filter: Filtrar por estado

        Returns:
            Lista de propuestas
        """
        try:
            proposals = []
            for proposal in self.governance_proposals.values():
                if status_filter and proposal.status != status_filter:
                    continue

                proposals.append({
                    'proposal_id': proposal.proposal_id,
                    'title': proposal.title,
                    'description': proposal.description,
                    'proposer': proposal.proposer_wallet,
                    'status': proposal.status.value,
                    'created_at': proposal.created_at.isoformat(),
                    'votes_for': proposal.votes_for,
                    'votes_against': proposal.votes_against,
                    'total_votes': proposal.get_total_votes(),
                    'is_passed': proposal.is_passed()
                })

            return proposals

        except Exception as e:
            logger.error(f"Error getting proposals: {e}")
            return []

    async def execute_proposal(self, proposal_id: str) -> Dict[str, Any]:
        """
        Ejecutar una propuesta aprobada.

        Args:
            proposal_id: ID de la propuesta

        Returns:
            Resultado de la ejecución
        """
        try:
            if proposal_id not in self.governance_proposals:
                return {'success': False, 'error': 'Proposal not found'}

            proposal = self.governance_proposals[proposal_id]

            if not proposal.can_execute(datetime.now()):
                return {'success': False, 'error': 'Proposal cannot be executed yet'}

            if not proposal.is_passed():
                proposal.status = ProposalStatus.REJECTED
                return {'success': False, 'error': 'Proposal was rejected'}

            # Ejecutar cambios (simplificado - en producción sería más complejo)
            # Aquí irían los cambios específicos según el tipo de propuesta

            proposal.status = ProposalStatus.EXECUTED
            proposal.executed_at = datetime.now()

            logger.info(f"⚡ Executed governance proposal: {proposal.title}")

            return {
                'success': True,
                'proposal_id': proposal_id,
                'executed_at': proposal.executed_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Error executing proposal: {e}")
            return {'success': False, 'error': str(e)}

    def get_staking_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas globales del sistema de staking.

        Returns:
            Estadísticas del staking
        """
        try:
            total_positions = sum(len(positions) for positions in self.staking_positions.values())
            active_positions = sum(
                len([p for p in positions if p.is_active])
                for positions in self.staking_positions.values()
            )

            # Calcular distribución por tiers
            tier_distribution = {tier.value: 0 for tier in StakingTier}
            for positions in self.staking_positions.values():
                for position in positions:
                    if position.is_active:
                        tier_distribution[position.tier.value] += 1

            return {
                'total_staked': self.total_staked,
                'total_stakers': self.total_stakers,
                'total_positions': total_positions,
                'active_positions': active_positions,
                'average_stake_per_user': self.total_staked / max(1, self.total_stakers),
                'tier_distribution': tier_distribution,
                'base_apr': self.base_apr,
                'governance_proposals': len(self.governance_proposals)
            }

        except Exception as e:
            logger.error(f"Error getting staking stats: {e}")
            return {'error': str(e)}

    async def cleanup_expired_locks(self):
        """Limpiar posiciones expiradas y ejecutar penalizaciones."""
        try:
            current_time = datetime.now()
            expired_positions = []

            for wallet_id, positions in self.staking_positions.items():
                for position in positions:
                    if position.is_active and current_time > position.unlock_date:
                        # Posición expirada - marcar como lista para unstake automático
                        expired_positions.append((wallet_id, position.stake_id))

            # Ejecutar unstake automático para posiciones expiradas
            for wallet_id, stake_id in expired_positions:
                try:
                    await self.unstake_tokens(wallet_id, stake_id)
                    logger.info(f"🔄 Auto-unstaked expired position {stake_id} for {wallet_id}")
                except Exception as e:
                    logger.warning(f"Failed to auto-unstake {stake_id}: {e}")

        except Exception as e:
            logger.error(f"Error cleaning up expired locks: {e}")


# Instancia global del staking manager
_staking_manager: Optional[StakingManager] = None

def get_staking_manager() -> StakingManager:
    """Obtener instancia global del staking manager."""
    global _staking_manager
    if _staking_manager is None:
        _staking_manager = StakingManager()
    return _staking_manager

def create_staking_manager() -> StakingManager:
    """Crear nueva instancia del staking manager."""
    return StakingManager()