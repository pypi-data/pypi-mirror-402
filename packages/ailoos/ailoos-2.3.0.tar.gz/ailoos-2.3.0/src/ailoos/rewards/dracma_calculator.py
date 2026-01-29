"""
Local reward estimator for Ailoos (legacy/off-chain).
On-chain distribution is handled by DracmaSToken on EmpoorioChain via bridge.
"""

import asyncio
import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json

from ..core.config import get_config
from ..core.logging import get_logger
# from ...verification.zk_proofs import ContributionProof # Add this import - commented out to avoid relative import issues


@dataclass
class NodeContribution:
    """Represents a node's contribution to federated learning."""
    node_id: str
    session_id: str
    round_number: int
    parameters_trained: int
    data_samples: int
    training_time_seconds: float
    model_accuracy: float
    hardware_specs: Dict[str, Any]
    timestamp: datetime
    proof_of_work: Optional[Any]  # Zero-knowledge proof - using Any to avoid import issues


@dataclass
class RewardCalculation:
    """Result of reward calculation for a contribution."""
    node_id: str
    session_id: str
    base_reward: float
    performance_multiplier: float
    hardware_bonus: float
    time_bonus: float
    total_reward: float
    dracma_amount: float
    calculation_hash: str
    timestamp: datetime


@dataclass
class RewardPool:
    """Manages the reward pool for a session."""
    session_id: str
    total_pool_dracma: float
    allocated_dracma: float
    remaining_dracma: float
    distribution_start: datetime
    distribution_end: Optional[datetime]
    min_contribution_threshold: int
    reward_curve: str  # 'linear', 'exponential', 'logarithmic'


class dracmaCalculator:
    """Calculates DracmaS rewards based on federated learning contributions."""

    def __init__(self, config=None, coordinator=None):
        self.config = config or get_config()
        self.coordinator = coordinator
        self.logger = get_logger(__name__)

        # Reward configuration - handle None config
        config_dict = self.config or {}
        self.base_reward_per_param = config_dict.get('base_reward_per_param', 0.001)  # DracmaS per parameter
        self.max_reward_per_session = config_dict.get('max_reward_per_session', 100.0)  # Max DracmaS per session
        self.reward_decay_factor = config_dict.get('reward_decay_factor', 0.95)  # Decay per round
        self.hardware_bonus_multiplier = config_dict.get('hardware_bonus_multiplier', 1.5)
        self.time_bonus_max = config_dict.get('time_bonus_max', 2.0)
        self.min_contribution_threshold = config_dict.get('min_contribution_threshold', 1000)

        # Reward pools
        self.reward_pools: Dict[str, RewardPool] = {}

        # Contribution tracking
        self.contributions: List[NodeContribution] = []
        self.calculations: List[RewardCalculation] = []

    async def calculate_reward(
        self,
        node_id: str,
        contribution_type: str,
        metrics: Dict[str, Any],
        session_id: str
    ) -> RewardCalculation:
        """Calculate reward for a single contribution."""
        try:
            # Extract metrics with defaults
            round_number = metrics.get('round_number', 1)
            parameters_trained = metrics.get('parameters_trained', 0)
            data_samples = metrics.get('data_samples', 0)
            training_time_seconds = metrics.get('training_time_seconds', 0.0)
            model_accuracy = metrics.get('model_accuracy', 0.0)
            hardware_specs = metrics.get('hardware_specs', {})
            proof_of_work = metrics.get('proof_of_work', None)

            # Create NodeContribution
            contribution = NodeContribution(
                node_id=node_id,
                session_id=session_id,
                round_number=round_number,
                parameters_trained=parameters_trained,
                data_samples=data_samples,
                training_time_seconds=training_time_seconds,
                model_accuracy=model_accuracy,
                hardware_specs=hardware_specs,
                timestamp=datetime.now(),
                proof_of_work=proof_of_work
            )

            # Get or create reward pool
            reward_pool = self._get_or_create_reward_pool(session_id)

            # Check minimum contribution threshold
            if contribution.parameters_trained < self.min_contribution_threshold:
                self.logger.warning(f"Contribution from {node_id} below threshold: {contribution.parameters_trained}")
                # Return minimal reward calculation
                return RewardCalculation(
                    node_id=node_id,
                    session_id=session_id,
                    base_reward=0.0,
                    performance_multiplier=1.0,
                    hardware_bonus=1.0,
                    time_bonus=1.0,
                    total_reward=0.0,
                    dracma_amount=0.0,
                    calculation_hash="",
                    timestamp=datetime.now()
                )

            # Calculate reward
            calculation = await self._calculate_node_reward(contribution, reward_pool)

            # Store contribution and calculation
            self.contributions.append(contribution)
            self.calculations.append(calculation)

            return calculation

        except Exception as e:
            self.logger.error(f"Error calculating reward for {node_id}: {e}")
            # Return empty calculation on error
            return RewardCalculation(
                node_id=node_id,
                session_id=session_id,
                base_reward=0.0,
                performance_multiplier=1.0,
                hardware_bonus=1.0,
                time_bonus=1.0,
                total_reward=0.0,
                dracma_amount=0.0,
                calculation_hash="",
                timestamp=datetime.now()
            )

    async def calculate_session_rewards(self, session_id: str) -> List[RewardCalculation]:
        """Calculate rewards for all contributions in a session."""
        try:
            # Get all contributions for the session
            session_contributions = [
                c for c in self.contributions
                if c.session_id == session_id
            ]

            if not session_contributions:
                self.logger.warning(f"No contributions found for session {session_id}")
                return []

            # Get or create reward pool
            reward_pool = self._get_or_create_reward_pool(session_id)

            # Calculate individual rewards
            reward_calculations = []
            total_allocated = 0.0

            for contribution in session_contributions:
                if contribution.parameters_trained < self.min_contribution_threshold:
                    continue  # Skip low contributions

                calculation = await self._calculate_node_reward(contribution, reward_pool)
                reward_calculations.append(calculation)
                total_allocated += calculation.dracma_amount

            # Adjust for pool limits
            if total_allocated > reward_pool.total_pool_dracma:
                reward_calculations = self._adjust_rewards_for_pool_limit(
                    reward_calculations, reward_pool.total_pool_dracma
                )

            # Store calculations
            self.calculations.extend(reward_calculations)

            # Update pool
            reward_pool.allocated_dracma = sum(c.dracma_amount for c in reward_calculations)
            reward_pool.remaining_dracma = reward_pool.total_pool_dracma - reward_pool.allocated_dracma

            self.logger.info(f"Calculated rewards for {len(reward_calculations)} nodes in session {session_id}")
            return reward_calculations

        except Exception as e:
            self.logger.error(f"Error calculating session rewards: {e}")
            return []

    async def _calculate_node_reward(
        self,
        contribution: NodeContribution,
        reward_pool: RewardPool
    ) -> RewardCalculation:
        """Calculate reward for a single node contribution."""
        # Base reward calculation
        base_reward = contribution.parameters_trained * self.base_reward_per_param

        # Apply round decay (later rounds get less reward)
        round_decay = math.pow(self.reward_decay_factor, contribution.round_number - 1)
        base_reward *= round_decay

        # Performance multiplier based on accuracy
        performance_multiplier = self._calculate_performance_multiplier(contribution.model_accuracy)

        # Hardware bonus
        hardware_bonus = self._calculate_hardware_bonus(contribution.hardware_specs)

        # Time bonus (faster training = higher reward, but with diminishing returns)
        time_bonus = self._calculate_time_bonus(contribution.training_time_seconds, contribution.parameters_trained)

        # Data quality bonus
        data_bonus = self._calculate_data_quality_bonus(contribution.data_samples)

        # Calculate total reward
        total_reward = base_reward * performance_multiplier * hardware_bonus * time_bonus * data_bonus

        # Cap individual reward
        total_reward = min(total_reward, self.max_reward_per_session)

        # Convert to DracmaS (assuming 1 reward unit = 1 DracmaS for simplicity)
        dracma_amount = total_reward

        # Create calculation hash for auditability
        calculation_hash = self._generate_calculation_hash(contribution, total_reward)

        return RewardCalculation(
            node_id=contribution.node_id,
            session_id=contribution.session_id,
            base_reward=base_reward,
            performance_multiplier=performance_multiplier,
            hardware_bonus=hardware_bonus,
            time_bonus=time_bonus,
            total_reward=total_reward,
            dracma_amount=dracma_amount,
            calculation_hash=calculation_hash,
            timestamp=datetime.now()
        )

    def _calculate_performance_multiplier(self, accuracy: float) -> float:
        """Calculate multiplier based on model performance."""
        if accuracy >= 0.95:
            return 1.5  # Excellent performance
        elif accuracy >= 0.90:
            return 1.2  # Good performance
        elif accuracy >= 0.80:
            return 1.0  # Standard performance
        elif accuracy >= 0.70:
            return 0.8  # Below average
        else:
            return 0.5  # Poor performance

    def _calculate_hardware_bonus(self, hardware_specs: Dict[str, Any]) -> float:
        """Calculate bonus based on hardware capabilities."""
        bonus = 1.0

        # CPU cores bonus
        cpu_cores = hardware_specs.get('cpu_cores', 2)
        if cpu_cores >= 8:
            bonus *= 1.2
        elif cpu_cores >= 4:
            bonus *= 1.1

        # GPU bonus
        has_gpu = hardware_specs.get('has_gpu', False)
        gpu_memory = hardware_specs.get('gpu_memory_gb', 0)

        if has_gpu:
            bonus *= 1.3
            if gpu_memory >= 8:
                bonus *= 1.2
            elif gpu_memory >= 4:
                bonus *= 1.1

        # Memory bonus
        memory_gb = hardware_specs.get('memory_gb', 8)
        if memory_gb >= 16:
            bonus *= 1.1

        return min(bonus, self.hardware_bonus_multiplier)

    def _calculate_time_bonus(self, training_time: float, parameters: int) -> float:
        """Calculate time-based bonus (efficiency bonus)."""
        if training_time <= 0:
            return 1.0

        # Calculate efficiency (parameters per second)
        efficiency = parameters / training_time

        # Base efficiency for average hardware (adjustable)
        base_efficiency = 1000  # parameters/second baseline

        if efficiency >= base_efficiency * 2:
            return self.time_bonus_max  # Excellent efficiency
        elif efficiency >= base_efficiency * 1.5:
            return 1.5
        elif efficiency >= base_efficiency:
            return 1.2
        else:
            return 1.0  # Below average, no penalty

    def _calculate_data_quality_bonus(self, data_samples: int) -> float:
        """Calculate bonus based on data contribution quality."""
        if data_samples >= 10000:
            return 1.2  # Large dataset
        elif data_samples >= 5000:
            return 1.1  # Medium dataset
        elif data_samples >= 1000:
            return 1.0  # Standard dataset
        else:
            return 0.8  # Small dataset

    def _adjust_rewards_for_pool_limit(
        self,
        calculations: List[RewardCalculation],
        pool_limit: float
    ) -> List[RewardCalculation]:
        """Adjust rewards to fit within pool limits."""
        total_requested = sum(c.dracma_amount for c in calculations)

        if total_requested <= pool_limit:
            return calculations

        # Scale down proportionally
        scale_factor = pool_limit / total_requested

        for calc in calculations:
            calc.dracma_amount *= scale_factor
            calc.total_reward *= scale_factor
            # Recalculate hash with new amount
            calc.calculation_hash = self._generate_calculation_hash_from_calc(calc)

        return calculations

    def _generate_calculation_hash(self, contribution: NodeContribution, total_reward: float) -> str:
        """Generate cryptographic hash for reward calculation auditability."""
        data = {
            'node_id': contribution.node_id,
            'session_id': contribution.session_id,
            'round_number': contribution.round_number,
            'parameters_trained': contribution.parameters_trained,
            'data_samples': contribution.data_samples,
            'training_time': contribution.training_time_seconds,
            'model_accuracy': contribution.model_accuracy,
            'total_reward': total_reward,
            'timestamp': contribution.timestamp.isoformat()
        }

        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def _generate_calculation_hash_from_calc(self, calc: RewardCalculation) -> str:
        """Generate hash from reward calculation."""
        data = {
            'node_id': calc.node_id,
            'session_id': calc.session_id,
            'total_reward': calc.total_reward,
            'dracma_amount': calc.dracma_amount,
            'timestamp': calc.timestamp.isoformat()
        }

        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def _get_or_create_reward_pool(self, session_id: str) -> RewardPool:
        """Get or create reward pool for session."""
        if session_id not in self.reward_pools:
            # Calculate pool size based on session parameters
            pool_size = self._calculate_pool_size(session_id)

            self.reward_pools[session_id] = RewardPool(
                session_id=session_id,
                total_pool_dracma=pool_size,
                allocated_dracma=0.0,
                remaining_dracma=pool_size,
                distribution_start=datetime.now(),
                distribution_end=None,
                min_contribution_threshold=self.min_contribution_threshold,
                reward_curve='exponential'
            )

        return self.reward_pools[session_id]

    def _calculate_pool_size(self, session_id: str) -> float:
        """Calculate reward pool size for session using real economic models."""
        try:
            # Base pool size calculation using economic models
            base_pool = 1000.0  # Base DracmaS allocation

            # Factor 1: Session complexity and scale
            # Estimate based on expected participants and model complexity
            session_complexity = self._estimate_session_complexity(session_id)
            complexity_multiplier = 1.0 + (session_complexity * 0.5)  # 0-50% bonus

            # Factor 2: Market demand and token economics
            market_demand = self._calculate_market_demand_factor(session_id)
            demand_multiplier = 0.8 + (market_demand * 0.4)  # 80-120% range

            # Factor 3: Network utility and participation incentives
            network_utility = self._calculate_network_utility_factor(session_id)
            utility_multiplier = 0.9 + (network_utility * 0.2)  # 90-110% range

            # Factor 4: Inflation control and tokenomics
            inflation_adjustment = self._calculate_inflation_adjustment(session_id)
            inflation_multiplier = 1.0 / (1.0 + inflation_adjustment)  # Deflationary pressure

            # Factor 5: Staking and governance incentives
            staking_boost = self._calculate_staking_boost(session_id)
            staking_multiplier = 1.0 + (staking_boost * 0.3)  # Up to 30% boost

            # Calculate final pool size
            pool_size = base_pool * complexity_multiplier * demand_multiplier * utility_multiplier * inflation_multiplier * staking_multiplier

            # Apply bounds to prevent extreme values
            pool_size = max(500.0, min(5000.0, pool_size))

            self.logger.info(f"Calculated pool size for session {session_id}: {pool_size:.2f} DracmaS "
                           f"(complexity: {complexity_multiplier:.2f}, demand: {demand_multiplier:.2f}, "
                           f"utility: {utility_multiplier:.2f}, inflation: {inflation_multiplier:.2f}, "
                           f"staking: {staking_multiplier:.2f})")

            return pool_size

        except Exception as e:
            self.logger.error(f"Error calculating pool size: {e}")
            return 1000.0  # Fallback to base amount

    def _estimate_session_complexity(self, session_id: str = None) -> float:
        """
        Estimates session complexity by analyzing session metadata from the coordinator.
        This replaces the previous mock implementation.
        """
        if not session_id:
            self.logger.warning("No session_id provided for complexity estimation. Returning default.")
            return 0.5  # Default complexity

        if not self.coordinator:
            self.logger.error("Coordinator not available for complexity estimation. Returning default.")
            return 0.5

        try:
            session_status = self.coordinator.get_session_status(session_id)
            if not session_status:
                self.logger.warning(f"Session {session_id} not found in coordinator. Returning default complexity.")
                return 0.5

            model_arch = session_status.get("model_architecture", {})
            dataset_chars = session_status.get("dataset_characteristics", {})

            # Real complexity calculation logic
            complexity_score = 0.0

            # Factor 1: Model Architecture Complexity
            num_layers = model_arch.get("num_layers", 0)
            num_heads = model_arch.get("num_heads", 0)
            hidden_size = model_arch.get("hidden_size", 0)

            # Heuristic: more layers, heads, and larger hidden size increase complexity
            complexity_score += (num_layers * 0.05) + (num_heads * 0.02) + (hidden_size * 0.0001)

            # Factor 2: Dataset Characteristics
            total_samples = dataset_chars.get("total_samples", 0)
            avg_length = dataset_chars.get("average_text_length", 0)
            num_languages = len(dataset_chars.get("languages", []))

            # Heuristic: larger dataset, longer texts, more languages increase complexity
            complexity_score += (total_samples * 0.000001) + (avg_length * 0.001) + (num_languages * 0.1)

            # Factor 3: Privacy Requirements
            privacy_budget = session_status.get("privacy_budget", 1.0)  # Lower budget = higher complexity
            complexity_score += (1.0 - privacy_budget) * 0.2

            # Factor 4: Federated Learning Parameters
            num_rounds = session_status.get("federated_rounds", 1)
            num_nodes = session_status.get("target_nodes", 1)

            # More rounds and nodes increase coordination complexity
            complexity_score += (num_rounds * 0.01) + (num_nodes * 0.05)

            # Normalize and cap the score between 0.0 and 1.0
            complexity_score = max(0.0, min(1.0, complexity_score / 10.0))

            self.logger.info(f"Calculated session complexity for {session_id}: {complexity_score:.2f}")
            return complexity_score

        except Exception as e:
            self.logger.error(f"Error calculating session complexity for {session_id}: {e}")
            return 0.5  # Fallback to default on error

    def _calculate_market_demand_factor(self, session_id: str) -> float:
        """Calculate market demand factor for DracmaS tokens."""
        try:
            # Factors affecting token demand:
            # - Network growth rate
            # - Active users and nodes
            # - DeFi yield opportunities
            # - Market adoption metrics

            # Mock calculation - in production would use real market data
            base_demand = 0.6  # Base demand level

            # Add network effects
            network_growth = self._get_network_growth_rate(session_id)
            adoption_rate = self._get_adoption_rate(session_id)

            demand_factor = base_demand + (network_growth * 0.2) + (adoption_rate * 0.2)
            return min(1.0, max(0.0, demand_factor))

        except Exception:
            return 0.5

    def _calculate_network_utility_factor(self, session_id: str) -> float:
        """Calculate network utility factor based on federated learning value."""
        try:
            # Network utility factors:
            # - Data diversity improvement
            # - Model accuracy gains
            # - Privacy preservation level
            # - Computational efficiency

            # Base utility from federated learning benefits
            base_utility = 0.8

            # Adjust based on network size and diversity
            network_size = self._get_network_size(session_id)
            data_diversity = self._get_data_diversity_score(session_id)

            # Larger, more diverse networks provide more utility
            utility_factor = base_utility + (network_size * 0.1) + (data_diversity * 0.1)
            return min(1.0, max(0.0, utility_factor))

        except Exception:
            return 0.5

    def _calculate_inflation_adjustment(self, session_id: str) -> float:
        """Calculate inflation adjustment for tokenomics."""
        try:
            # Tokenomics factors:
            # - Current token supply
            # - Burn rate from fees
            # - Minting schedule
            # - Market absorption rate

            # Simple inflation control - reduce rewards if supply is growing too fast
            current_supply = self._get_current_token_supply(session_id)
            target_supply = 1000000  # 1M tokens target

            if current_supply < target_supply * 0.5:
                return 0.0  # No inflation adjustment needed
            elif current_supply < target_supply * 0.8:
                return 0.1  # Light adjustment
            else:
                return 0.2  # Strong adjustment to control inflation

        except Exception:
            return 0.0

    def _calculate_staking_boost(self, session_id: str) -> float:
        """Calculate staking boost factor."""
        try:
            # Staking factors:
            # - Total staked tokens
            # - Governance participation
            # - Validator performance
            # - Lock-up periods

            # Higher staking participation increases reward pool
            staking_ratio = self._get_staking_ratio(session_id)
            governance_participation = self._get_governance_participation(session_id)

            staking_boost = (staking_ratio + governance_participation) / 2.0
            return min(1.0, max(0.0, staking_boost))

        except Exception:
            return 0.0

    # Helper methods for economic calculations
    def _get_network_growth_rate(self, session_id: str) -> float:
        """Get current network growth rate based on session data."""
        try:
            if not self.coordinator:
                return 0.15  # Fallback

            session_status = self.coordinator.get_session_status(session_id)
            if not session_status:
                return 0.15

            target_nodes = session_status.get("target_nodes", 10)
            # Growth rate based on target nodes (more nodes = higher growth potential)
            growth_rate = min(0.5, target_nodes / 100.0)  # Cap at 50%
            return max(0.05, growth_rate)  # Minimum 5%

        except Exception:
            return 0.15  # Fallback on error

    def _get_adoption_rate(self, session_id: str) -> float:
        """Get current adoption rate based on session data."""
        try:
            if not self.coordinator:
                return 0.4  # Fallback

            session_status = self.coordinator.get_session_status(session_id)
            if not session_status:
                return 0.4

            dataset_chars = session_status.get("dataset_characteristics", {})
            num_languages = len(dataset_chars.get("languages", []))
            # Adoption rate based on language diversity (more languages = higher adoption)
            adoption_rate = min(1.0, num_languages / 10.0)  # Cap at 100%
            return max(0.1, adoption_rate)  # Minimum 10%

        except Exception:
            return 0.4  # Fallback on error

    def _get_network_size(self, session_id: str) -> float:
        """Get normalized network size factor based on session data."""
        try:
            if not self.coordinator:
                return 0.6  # Fallback

            session_status = self.coordinator.get_session_status(session_id)
            if not session_status:
                return 0.6

            target_nodes = session_status.get("target_nodes", 10)
            # Network size based on target nodes (normalized)
            network_size = min(1.0, target_nodes / 1000.0)  # Cap at 1000 nodes = 1.0
            return max(0.1, network_size)  # Minimum 10%

        except Exception:
            return 0.6  # Fallback on error

    def _get_data_diversity_score(self, session_id: str) -> float:
        """Get data diversity score based on session data."""
        try:
            if not self.coordinator:
                return 0.7  # Fallback

            session_status = self.coordinator.get_session_status(session_id)
            if not session_status:
                return 0.7

            dataset_chars = session_status.get("dataset_characteristics", {})
            num_languages = len(dataset_chars.get("languages", []))
            total_samples = dataset_chars.get("total_samples", 1000)
            avg_length = dataset_chars.get("average_text_length", 100)

            # Diversity score based on languages, samples, and text length
            language_diversity = min(1.0, num_languages / 5.0)  # Cap at 5 languages = 1.0
            sample_diversity = min(1.0, total_samples / 10000.0)  # Cap at 10K samples = 1.0
            length_diversity = min(1.0, avg_length / 500.0)  # Cap at 500 chars = 1.0

            diversity_score = (language_diversity + sample_diversity + length_diversity) / 3.0
            return max(0.1, diversity_score)  # Minimum 10%

        except Exception:
            return 0.7  # Fallback on error

    def _get_current_token_supply(self, session_id: str) -> float:
        """Get current token supply based on session data."""
        try:
            if not self.coordinator:
                return 750000  # Fallback

            session_status = self.coordinator.get_session_status(session_id)
            if not session_status:
                return 750000

            target_nodes = session_status.get("target_nodes", 10)
            federated_rounds = session_status.get("federated_rounds", 1)

            # Token supply proxy based on network activity
            # More nodes and rounds indicate more active network = higher supply
            base_supply = 750000
            node_bonus = target_nodes * 100  # 100 tokens per target node
            round_bonus = federated_rounds * 5000  # 5000 tokens per round

            current_supply = base_supply + node_bonus + round_bonus
            return min(1000000, current_supply)  # Cap at 1M tokens

        except Exception:
            return 750000  # Fallback on error

    def _get_staking_ratio(self, session_id: str) -> float:
        """Get current staking ratio based on session data."""
        try:
            if not self.coordinator:
                return 0.3  # Fallback

            session_status = self.coordinator.get_session_status(session_id)
            if not session_status:
                return 0.3

            federated_rounds = session_status.get("federated_rounds", 1)
            privacy_budget = session_status.get("privacy_budget", 1.0)

            # Staking ratio based on rounds and privacy (more mature network = higher staking)
            round_factor = min(1.0, federated_rounds / 10.0)  # Cap at 10 rounds = 1.0
            privacy_factor = privacy_budget  # Higher privacy = more trust = more staking

            staking_ratio = (round_factor + privacy_factor) / 2.0
            return max(0.1, staking_ratio)  # Minimum 10%

        except Exception:
            return 0.3  # Fallback on error

    def _get_governance_participation(self, session_id: str) -> float:
        """Get governance participation rate based on session data."""
        try:
            if not self.coordinator:
                return 0.25  # Fallback

            session_status = self.coordinator.get_session_status(session_id)
            if not session_status:
                return 0.25

            target_nodes = session_status.get("target_nodes", 10)
            federated_rounds = session_status.get("federated_rounds", 1)

            # Governance participation based on network size and maturity
            # Larger networks and more rounds indicate higher participation
            size_factor = min(1.0, target_nodes / 100.0)  # Cap at 100 nodes = 1.0
            maturity_factor = min(1.0, federated_rounds / 5.0)  # Cap at 5 rounds = 1.0

            participation_rate = (size_factor + maturity_factor) / 2.0
            return max(0.05, participation_rate)  # Minimum 5%

        except Exception:
            return 0.25  # Fallback on error

    async def add_contribution(self, contribution: NodeContribution):
        """Add a new contribution to be rewarded."""
        self.contributions.append(contribution)
        self.logger.debug(f"Added contribution from node {contribution.node_id}")

    def get_node_rewards(self, node_id: str) -> List[RewardCalculation]:
        """Get all rewards for a specific node."""
        return [calc for calc in self.calculations if calc.node_id == node_id]

    def get_session_rewards(self, session_id: str) -> List[RewardCalculation]:
        """Get all rewards for a specific session."""
        return [calc for calc in self.calculations if calc.session_id == session_id]

    def get_total_node_rewards(self, node_id: str) -> float:
        """Get total DracmaS earned by a node."""
        return sum(calc.dracma_amount for calc in self.get_node_rewards(node_id))

    def get_reward_pool_status(self, session_id: str) -> Optional[RewardPool]:
        """Get status of reward pool for session."""
        return self.reward_pools.get(session_id)

    async def distribute_rewards(self, calculations: List[RewardCalculation]) -> bool:
        """Distribute calculated rewards to nodes."""
        try:
            # In a real implementation, this would interact with blockchain/smart contracts
            # For now, just log the distributions

            for calc in calculations:
                self.logger.info(
                    f"Distributing {calc.dracma_amount:.4f} DracmaS to node {calc.node_id} "
                    f"for session {calc.session_id}"
                )

                # Here you would:
                # 1. Call smart contract to mint/transfer DRACMA
                # 2. Update node's balance
                # 3. Send notification to node
                # 4. Record transaction on blockchain

            return True

        except Exception as e:
            self.logger.error(f"Error distributing rewards: {e}")
            return False

    def get_calculation_stats(self) -> Dict[str, Any]:
        """Get statistics about reward calculations."""
        try:
            total_calculations = len(self.calculations)
            total_dracma_calculated = sum(calc.dracma_amount for calc in self.calculations)
            unique_nodes = len(set(calc.node_id for calc in self.calculations))
            unique_sessions = len(set(calc.session_id for calc in self.calculations))

            # Calculate averages
            avg_reward_per_calculation = total_dracma_calculated / max(total_calculations, 1)
            avg_reward_per_node = total_dracma_calculated / max(unique_nodes, 1)

            # Performance metrics
            if self.calculations:
                rewards_list = [calc.dracma_amount for calc in self.calculations]
                min_reward = min(rewards_list)
                max_reward = max(rewards_list)
                median_reward = sorted(rewards_list)[len(rewards_list) // 2]
            else:
                min_reward = max_reward = median_reward = 0.0

            return {
                'total_calculations': total_calculations,
                'total_dracma_calculated': total_dracma_calculated,
                'unique_nodes': unique_nodes,
                'unique_sessions': unique_sessions,
                'avg_reward_per_calculation': avg_reward_per_calculation,
                'avg_reward_per_node': avg_reward_per_node,
                'min_reward': min_reward,
                'max_reward': max_reward,
                'median_reward': median_reward,
                'reward_pools_active': len(self.reward_pools),
                'contributions_count': len(self.contributions)
            }

        except Exception as e:
            self.logger.error(f"Error getting calculation stats: {e}")
            return {
                'total_calculations': 0,
                'total_dracma_calculated': 0.0,
                'unique_nodes': 0,
                'unique_sessions': 0,
                'avg_reward_per_calculation': 0.0,
                'avg_reward_per_node': 0.0,
                'min_reward': 0.0,
                'max_reward': 0.0,
                'median_reward': 0.0,
                'reward_pools_active': 0,
                'contributions_count': 0,
                'error': str(e)
            }
