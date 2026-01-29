#!/usr/bin/env python3
"""
DracmaS Manager - bridge-only integration with EmpoorioChain.
Las recompensas reales viven en EmpoorioChain via bridge; no hay calculos locales.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from ..blockchain.rewards_manager import RewardsManager
from ..blockchain.work_reporting import WorkReportingManager
from ..blockchain.bridge_client import get_bridge_client
from ..core.config import Config
from ..utils.logging import AiloosLogger


class DRACMA_Manager:
    """High-level manager for DracmaS rewards (bridge-only)."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = AiloosLogger(__name__)

        self.rewards_manager = RewardsManager()
        self.work_reporting = WorkReportingManager()
        self.bridge_client = get_bridge_client()

    def _run_async(self, coro):
        """Run async call in sync contexts (CLI/services)."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)

        new_loop = asyncio.new_event_loop()
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()

    def _looks_like_wallet(self, value: Optional[str]) -> bool:
        if not value:
            return False
        return value.startswith("emp1") or value.startswith("empoorio")

    def _resolve_wallet_address(self, node_id: Optional[str], wallet_address: Optional[str]) -> Optional[str]:
        if wallet_address:
            return wallet_address
        if node_id and self._looks_like_wallet(node_id):
            return node_id
        return self.config.get("wallet_address")

    async def calculate_and_distribute_rewards(self, contributions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Report work units to DracmaSToken via bridge (EmpoorioChain)."""
        try:
            reports = []
            failed = []
            total_units = 0

            for contrib in contributions:
                node_id = contrib.get('node_id')
                if not node_id:
                    failed.append({'error': 'missing node_id', 'contribution': contrib})
                    continue

                metrics = contrib.get('metrics', {})
                units = (
                    contrib.get('work_units')
                    or contrib.get('units')
                    or metrics.get('work_units')
                    or metrics.get('compute_power')
                    or metrics.get('parameters_trained')
                    or 0
                )
                dataset_id = (
                    contrib.get('dataset_id')
                    or metrics.get('dataset_id')
                    or 'default'
                )
                if units <= 0:
                    failed.append({'node_id': node_id, 'error': 'invalid work units'})
                    continue

                result = await self.work_reporting.report_training_work(
                    node_id=node_id,
                    units=int(units),
                    dataset_id=dataset_id,
                    proof_hash=metrics.get('proof_hash')
                )
                if result.get('success'):
                    reports.append(result.get('report'))
                    total_units += int(units)
                else:
                    failed.append({'node_id': node_id, 'error': result.get('error')})

            return {
                'success': len(reports) > 0,
                'reported': len(reports),
                'failed': len(failed),
                'total_units': total_units,
                'errors': failed,
                'source': 'bridge'
            }

        except Exception as e:
            self.logger.error(f"Error reporting work units: {e}")
            return {'success': False, 'error': str(e), 'source': 'bridge'}

    async def get_node_balance(self, node_id: str) -> Dict[str, Any]:
        """Get pending rewards info for a node from the bridge."""
        try:
            pending = await self.rewards_manager.get_pending_rewards(node_id)
            claimable_at = pending.claimable_at
            claimable = True
            if claimable_at and int(claimable_at) > int(datetime.now().timestamp()):
                claimable = False

            pending_amount = pending.amount if pending else 0.0
            return {
                'node_id': node_id,
                'balance': 0.0,
                'pending': pending_amount,
                'pending_balance': pending_amount,
                'claimable': claimable,
                'claimable_at': pending.claimable_at,
                'last_updated': pending.last_updated,
                'source': 'bridge_pending_only'
            }
        except Exception as e:
            self.logger.error(f"Error getting balance for {node_id}: {e}")
            return {'error': str(e), 'source': 'bridge_pending_only'}

    async def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics (bridge only)."""
        try:
            totals = await self.bridge_client.get_rewards_totals()
            return {
                'distribution': {'mode': 'bridge', 'chain': 'EmpoorioChain'},
                'totals': {
                    'total_units': totals.get('total_units', 0),
                    'total_rewards': totals.get('total_rewards', 0)
                },
                'timestamp': datetime.now().isoformat(),
                'source': 'bridge'
            }
        except Exception as e:
            self.logger.warning(f"Bridge totals unavailable: {e}")
            return {
                'distribution': {'mode': 'bridge', 'chain': 'EmpoorioChain'},
                'timestamp': datetime.now().isoformat(),
                'note': 'Stats reales dependen de endpoints del bridge.'
            }

    def get_pending_distributions(self) -> List[Dict[str, Any]]:
        """Get pending rewards using bridge (single-node view)."""
        try:
            node_id = self.config.get('node_id', 'default_node')
            pending = self._run_async(self.rewards_manager.get_pending_rewards(node_id))
            if not pending:
                return []
            return [{
                'tx_hash': '',
                'node_id': pending.node_id,
                'dracma_amount': pending.amount,
                'session_id': '',
                'status': 'pending',
                'timestamp': datetime.fromtimestamp(pending.last_updated).isoformat(),
                'source': 'bridge'
            }]
        except Exception as e:
            self.logger.error(f"Error getting pending distributions: {e}")
            return []

    def get_completed_distributions(
        self,
        node_id: Optional[str] = None,
        wallet_address: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Completed distributions are tracked on-chain; fetch from bridge history."""
        try:
            address = self._resolve_wallet_address(node_id, wallet_address)
            if not address:
                return []

            history = self._run_async(self.bridge_client.get_transaction_history(address, limit=limit))
            transactions = (
                history.get("transactions")
                or history.get("history")
                or history.get("txs")
                or []
            )

            completed = []
            for tx in transactions:
                tx_type = str(tx.get("tx_type") or tx.get("type") or "").lower()
                if tx_type and "reward" not in tx_type and "claim" not in tx_type:
                    continue
                completed.append({
                    "tx_hash": tx.get("tx_hash") or tx.get("hash") or "",
                    "node_id": node_id or "",
                    "dracma_amount": tx.get("amount") or tx.get("dracma_amount") or 0.0,
                    "session_id": tx.get("session_id") or "",
                    "status": "completed",
                    "timestamp": tx.get("timestamp"),
                    "source": "bridge"
                })

            return completed
        except Exception as e:
            self.logger.error(f"Error getting completed distributions: {e}")
            return []

    def get_balance(self, node_id: Optional[str] = None, wallet_address: Optional[str] = None) -> Dict[str, Any]:
        """Get pending/claimable rewards and wallet balance (bridge)."""
        try:
            if not node_id:
                node_id = self.config.get('node_id', 'default_node')

            pending = self._run_async(self.rewards_manager.get_pending_rewards(node_id))
            pending_amount = pending.amount if pending else 0.0
            claimable_at = pending.claimable_at if pending else None
            next_claim_eligible = "now"
            if claimable_at:
                next_claim_dt = datetime.fromtimestamp(int(claimable_at))
                next_claim_eligible = next_claim_dt.isoformat()

            address = self._resolve_wallet_address(node_id, wallet_address)
            available_balance = pending_amount
            if address:
                wallet = self._run_async(self.bridge_client.get_wallet_balance(address))
                available_balance = float(
                    wallet.get("balance")
                    or wallet.get("available_balance")
                    or wallet.get("available")
                    or pending_amount
                )

            return {
                'total_balance': pending_amount,
                'available_balance': available_balance,
                'pending_balance': pending_amount,
                'locked_balance': 0.0,
                'reputation_score': 0.0,
                'total_earned': 0.0,
                'sessions_participated': 0,
                'avg_reward_per_session': 0.0,
                'next_claim_eligible': next_claim_eligible,
                'min_claim_amount': 0.0,
                'node_id': node_id,
                'last_updated': datetime.now().isoformat(),
                'source': 'bridge'
            }
        except Exception as e:
            self.logger.error(f"Error getting balance: {e}")
            return {'error': str(e), 'source': 'bridge'}

    def get_history(
        self,
        node_id: Optional[str] = None,
        limit=20,
        start_date=None,
        end_date=None,
        reward_type='all',
        wallet_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get wallet history from bridge."""
        address = self._resolve_wallet_address(node_id, wallet_address)
        if not address:
            return {
                'rewards': [],
                'total_count': 0,
                'has_more': False,
                'node_id': node_id or self.config.get('node_id', 'default_node'),
                'note': 'Wallet address requerida para consultar historial en el bridge.'
            }

        try:
            result = self._run_async(self.bridge_client.get_transaction_history(address, limit))
            entries = result.get('transactions') or result.get('entries') or []
            return {
                'rewards': entries,
                'total_count': len(entries),
                'has_more': len(entries) >= limit,
                'node_id': node_id or self.config.get('node_id', 'default_node'),
                'source': 'bridge'
            }
        except Exception as e:
            self.logger.error(f"Error getting history: {e}")
            return {
                'rewards': [],
                'total_count': 0,
                'has_more': False,
                'node_id': node_id or self.config.get('node_id', 'default_node'),
                'error': str(e),
                'source': 'bridge'
            }

    def claim_rewards(self, amount: Optional[float] = None, wallet_address: Optional[str] = None, node_id: Optional[str] = None) -> Dict[str, Any]:
        """Claim rewards on-chain via bridge (amount is ignored; chain computes claimable)."""
        try:
            if not node_id:
                node_id = self.config.get('node_id', 'default_node')

            result = self._run_async(self.rewards_manager.claim_node_rewards(node_id))
            claim = result.get('claim')
            tx_hash = claim.transaction_hash if claim else ''
            claimed_amount = claim.amount if claim else 0.0

            return {
                'success': True,
                'amount': claimed_amount,
                'wallet_address': wallet_address or '',
                'transaction_hash': tx_hash,
                'confirmed_at': datetime.now().isoformat(),
                'source': 'bridge'
            }
        except Exception as e:
            self.logger.error(f"Claim failed for {node_id}: {e}")
            return {'success': False, 'error': str(e), 'source': 'bridge'}

    def calculate_staking_reward(self, amount, duration_days: int) -> Dict[str, Any]:
        """Estimate staking reward (bridge does final calculation)."""
        multiplier = 1.0 + (duration_days / 365) * 0.5
        estimated_reward = amount * (multiplier - 1.0)
        unlock_date = datetime.now() + timedelta(days=duration_days)

        return {
            'multiplier': round(multiplier, 2),
            'estimated_reward': round(estimated_reward, 4),
            'unlock_date': unlock_date.isoformat(),
            'note': 'Estimate only; final rewards computed on-chain.'
        }

    def stake_tokens(self, amount: float, duration_days: int, address: Optional[str] = None) -> Dict[str, Any]:
        """Stake tokens via bridge (duration handled on-chain)."""
        if not address:
            return {'success': False, 'error': 'Wallet address required for staking.'}
        try:
            result = self._run_async(self.bridge_client.stake_tokens(amount, address))
            return {'success': True, 'result': result, 'source': 'bridge'}
        except Exception as e:
            self.logger.error(f"Error staking tokens: {e}")
            return {'success': False, 'error': str(e), 'source': 'bridge'}

    def unstake_tokens(self, amount: float, address: Optional[str] = None) -> Dict[str, Any]:
        """Unstake tokens via bridge."""
        if not address:
            return {'success': False, 'error': 'Wallet address required for unstaking.'}
        try:
            result = self._run_async(self.bridge_client.unstake_tokens(amount, address))
            return {'success': True, 'result': result, 'source': 'bridge'}
        except Exception as e:
            self.logger.error(f"Error unstaking tokens: {e}")
            return {'success': False, 'error': str(e), 'source': 'bridge'}

    def get_stake_info(self, node_id: str, stake_id: str):
        return {'success': False, 'error': 'Staking info not available via bridge.'}

    def calculate_early_unstake_penalty(self, node_id: str, stake_id: str) -> float:
        return 0.0

    def get_stakes(self, node_id: str) -> Dict[str, Any]:
        return {'stakes': [], 'total_staked': 0.0, 'note': 'Bridge does not expose staking list.'}

    def delegate_tokens(self, node_id: str, amount: float, validator: str, duration_days: int) -> Dict[str, Any]:
        return {'success': False, 'error': 'Delegation not supported via bridge.'}

    def undelegate_tokens(self, node_id: str, delegation_id: str) -> Dict[str, Any]:
        return {'success': False, 'error': 'Undelegation not supported via bridge.'}

    def get_delegations(self, node_id: str) -> Dict[str, Any]:
        return {'delegations': [], 'total_delegated': 0.0, 'note': 'Bridge does not expose delegations.'}

    def update_settings(self, settings):
        return {'success': False, 'error': 'Settings are managed on-chain/bridge.'}

    def get_settings(self) -> Dict[str, Any]:
        return {
            'wallet_address': None,
            'auto_claim': False,
            'min_claim_amount': 0.0,
            'note': 'Settings are managed on-chain/bridge.'
        }

    def get_stats(self, node_id: Optional[str] = None) -> Dict[str, Any]:
        """Bridge-only stats (placeholders until endpoints exist)."""
        if not node_id:
            node_id = self.config.get('node_id', 'default_node')

        return {
            'overall': {
                'total_supply': 0.0,
                'total_distributed': 0.0,
                'active_participants': 0
            },
            'user': {
                'total_earned': 0.0,
                'sessions_participated': 0,
                'avg_reward_per_session': 0.0,
                'rank': 0,
                'node_id': node_id
            },
            'performance': {
                'efficiency_score': 0.0,
                'accuracy_contribution': 0.0,
                'uptime_percentage': 0.0
            },
            'distribution': {'mode': 'bridge', 'chain': 'EmpoorioChain'},
            'note': 'Bridge endpoints for stats are pending.'
        }

    # Legacy local-only APIs kept for compatibility (disabled)
    def calculate_reward(self, contribution: Dict[str, Any]) -> float:
        return 0.0

    def distribute_session_rewards(self, session_rewards: Dict[str, Any]) -> Dict[str, Any]:
        return {'success': False, 'error': 'Legacy distribution disabled in bridge-only mode.'}

    def apply_penalties(self, penalty_case: Dict[str, Any]) -> float:
        return float(penalty_case.get('base_reward', 0.0))

    def apply_slashing(self, base_reward: float, violation: str) -> float:
        return base_reward

    def distribute_fair_rewards(self, contributions: Dict[str, Any], total_pool: float) -> Dict[str, Any]:
        return {'success': False, 'error': 'Legacy distribution disabled in bridge-only mode.'}

    def report_malicious_behavior(self, reporter_id: str, malicious_node_id: str,
                                  behavior_type: str, evidence: Dict[str, Any],
                                  severity: float = 0.5) -> Dict[str, Any]:
        return {'success': False, 'error': 'Slashing reports not supported via bridge.'}

    def vote_on_slashing_report(self, voter_id: str, report_id: str, approve: bool,
                                reasoning: str = "") -> Dict[str, Any]:
        return {'success': False, 'error': 'Slashing votes not supported via bridge.'}

    def get_slashing_reports(self, node_id: Optional[str] = None) -> Dict[str, Any]:
        return {'reports': [], 'note': 'Slashing not supported via bridge.'}

    def get_slashing_stats(self) -> Dict[str, Any]:
        return {'slashing_enabled': False, 'reports_total': 0, 'note': 'Slashing not supported via bridge.'}

    def register_memory_hosting(self, *args, **kwargs) -> Dict[str, Any]:
        return {'success': False, 'error': 'Memory hosting rewards not supported via bridge.'}

    def verify_memory_hosting_integrity(self, *args, **kwargs) -> Dict[str, Any]:
        return {'success': False, 'error': 'Memory hosting rewards not supported via bridge.'}

    def calculate_memory_hosting_rewards(self, *args, **kwargs) -> Dict[str, Any]:
        return {'success': False, 'error': 'Memory hosting rewards not supported via bridge.'}

    def get_memory_hosting_stats(self, node_id: Optional[str] = None) -> Dict[str, Any]:
        return {'success': False, 'error': 'Memory hosting rewards not supported via bridge.'}

    def list_memory_hosts(self) -> Dict[str, Any]:
        return {'hosts': [], 'note': 'Memory hosting rewards not supported via bridge.'}
