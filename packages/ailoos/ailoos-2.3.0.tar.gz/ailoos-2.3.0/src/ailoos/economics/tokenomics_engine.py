#!/usr/bin/env python3
"""
Tokenomics Engine for Ailoos Network.
Basado en DracmaS (EmpoorioChain) y sus constantes canonicas.
"""

import math
import json
import os
from pathlib import Path
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import asyncio
from collections import defaultdict

# Import system components for real data integration
try:
    from ..federated.coordinator import FederatedCoordinator
    from ..core.config import get_config
    from ..core.logging import get_logger
except ImportError:
    # Fallback for testing or when modules not available
    FederatedCoordinator = None
    get_config = lambda: {}
    get_logger = lambda name: logging.getLogger(name)

logger = get_logger(__name__)

def _load_dracmas_tokenomics() -> Dict[str, Any]:
    defaults = {
        "name": "DracmaS",
        "symbol": "DMS",
        "decimals": 18,
        "initial_supply": 1_000_000_000,
        "max_supply": 3_500_000_000,
        "emission_rate_percent": 2,
        "transfer_burn_bps": 10,
        "staking_minimum": 100,
    }

    env_path = os.getenv("DRACMAS_TOKENOMICS_PATH")
    root = Path(__file__).resolve().parents[4]
    json_path = Path(env_path) if env_path else root / "DracmaSToken" / "tokenomics.json"
    if not json_path.exists():
        return defaults

    try:
        with json_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return {**defaults, **data}
    except Exception as exc:
        logger.warning(f"No se pudo cargar tokenomics desde {json_path}: {exc}")
        return defaults


_TOKENOMICS = _load_dracmas_tokenomics()

# DracmaS constants (source: DracmaSToken/tokenomics.json)
DMS_TOKEN_NAME = _TOKENOMICS["name"]
DMS_TOKEN_SYMBOL = _TOKENOMICS["symbol"]
DMS_DECIMALS = _TOKENOMICS["decimals"]
DMS_INITIAL_SUPPLY = _TOKENOMICS["initial_supply"]
DMS_MAX_SUPPLY = _TOKENOMICS["max_supply"]
DMS_EMISSION_RATE_PERCENT = _TOKENOMICS["emission_rate_percent"]
DMS_TRANSFER_BURN_BPS = _TOKENOMICS["transfer_burn_bps"]
DMS_STAKING_MINIMUM = _TOKENOMICS["staking_minimum"]

class TokenType(Enum):
    """Tipos de tokens en el sistema"""
    DRACMAS = "dracmas"

class EconomicAgent(Enum):
    """Tipos de agentes económicos"""
    NODE = "node"
    USER = "user"
    VALIDATOR = "validator"
    DEVELOPER = "developer"

@dataclass
class TokenMetrics:
    """Métricas de un token"""
    token_type: TokenType
    total_supply: float
    circulating_supply: float
    market_cap: float = 0.0
    price: float = 1.0
    volume_24h: float = 0.0
    holders: int = 0
    transactions_24h: int = 0

@dataclass
class AgentProfile:
    """Perfil económico de un agente"""
    agent_id: str
    agent_type: EconomicAgent
    balance: Dict[TokenType, float] = field(default_factory=dict)
    reputation_score: float = 0.0
    stake_amount: float = 0.0
    contribution_score: float = 0.0
    risk_tolerance: float = 0.5
    last_activity: Optional[datetime] = None
    economic_history: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class EconomicEvent:
    """Evento económico"""
    event_id: str
    event_type: str
    timestamp: datetime
    participants: List[str]
    token_flows: Dict[str, Dict[TokenType, float]]
    metadata: Dict[str, Any] = field(default_factory=dict)

class TokenomicsEngine:
    """
    Motor de tokenomics avanzado con teoría de juegos
    Implementa modelos económicos complejos para la red Ailoos
    """

    def __init__(self, federated_coordinator=None, dracma_calculator=None):
        # Token supplies and metrics
        self.tokens: Dict[TokenType, TokenMetrics] = {}
        self._initialize_tokens()

        # Agent registry
        self.agents: Dict[str, AgentProfile] = {}

        # Economic events history
        self.economic_events: List[EconomicEvent] = []

        # Game theory models
        self.prisoners_dilemma_matrix = self._initialize_prisoners_dilemma()
        self.staking_game_matrix = self._initialize_staking_game()

        # Economic parameters
        self.inflation_rate = 0.02  # 2% annual inflation
        self.staking_reward_rate = 0.08  # 8% APY for staking
        self.contribution_reward_rate = 0.05  # 5% for contributions
        self.slashing_penalty = 0.1  # 10% slashing for misbehavior

        # Market dynamics
        self.price_elasticity = 0.3
        self.volatility_factor = 0.15

        # System integration - real data sources
        self.federated_coordinator = federated_coordinator
        if dracma_calculator:
            logger.warning("dracma_calculator legacy ignored in favor of DracmaSToken canonical data")
        self.dracma_calculator = None
        
        # Real Token Provider
        self.token_provider = None
        self.treasury_private_key = os.getenv("DRACMA_TREASURY_KEY") # Key for signing reward transfers

        # Initialize with real system data if available
        self._initialize_from_system_data()

        logger.info("💰 Tokenomics Engine initialized with real system integration")

    def set_token_provider(self, provider):
        """Set the real token provider for blockchain interactions."""
        self.token_provider = provider
        logger.info("🔗 Token provider connected to TokenomicsEngine")

    async def distribute_reward(self, agent_id: str, amount: float, reason: str) -> bool:
        """
        Distribute real token rewards to an agent.
        
        Args:
            agent_id: ID of the agent (must be a valid address for blockchain)
            amount: Amount of tokens to reward
            reason: Reason for the reward (for logging)
            
        Returns:
            True if successful
        """
        if not self.token_provider:
            logger.warning(f"⚠️ No token provider connected. Cannot distribute {amount} DMS to {agent_id}")
            return False
            
        if not self.treasury_private_key:
            logger.warning("⚠️ No treasury private key configured. Cannot sign reward transaction.")
            return False

        try:
            # Verify agent exists and has an address
            if agent_id not in self.agents:
                logger.warning(f"⚠️ Agent {agent_id} not found in registry")
                return False
                
            # Assuming agent_id IS the wallet address for simplicity, 
            # or we store it in AgentProfile. In AgentProfile it's just 'agent_id'.
            # We'll assume agent_id is the wallet address.
            recipient_address = agent_id
            
            # Treasury address (derived from key)
            # We let the provider handle derivation if we pass the key
            
            logger.info(f"💸 Distributing {amount} DMS to {agent_id} for {reason}")
            
            # Execute transfer
            result = await self.token_provider.transfer(
                from_address=None, # Provider derives from key
                to_address=recipient_address,
                amount=amount,
                private_key=self.treasury_private_key
            )
            
            if result.success:
                logger.info(f"✅ Reward distributed: {result.tx_hash}")
                
                # Update local balance tracking
                if agent_id in self.agents:
                    current = self.agents[agent_id].balance.get(TokenType.DRACMAS, 0.0)
                    self.agents[agent_id].balance[TokenType.DRACMAS] = current + amount
                    
                return True
            else:
                logger.error(f"❌ Reward distribution failed: {result.error_message}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error distributing reward: {e}")
            return False

        except Exception as e:
            logger.error(f"❌ Error distributing reward: {e}")
            return False

    async def slash_agent(self, agent_id: str, amount: float, reason: str) -> bool:
        """
        Slash an agent's stake/balance for misbehavior.
        
        Args:
            agent_id: ID of the agent
            amount: Amount to slash
            reason: Reason for slashing
            
        Returns:
            True if successful
        """
        try:
            if agent_id not in self.agents:
                logger.warning(f"⚠️ Cannot slash unknown agent {agent_id}")
                return False
                
            agent = self.agents[agent_id]
            
            # 1. Reduce Reputation (Heavy penalty)
            agent.reputation_score = max(0.0, agent.reputation_score - 20.0)
            
            # 2. Reduce Stake (Internal tracking)
            # In a real system, this would call the Staking Contract's slash function
            current_stake = agent.stake_amount
            slashed_amount = min(current_stake, amount)
            agent.stake_amount = current_stake - slashed_amount
            
            logger.warning(f"🔪 Slashed agent {agent_id}: {slashed_amount} tokens (Reason: {reason})")
            
            # 3. Try to execute blockchain slashing if provider supports it
            # Currently RealTokenProvider doesn't expose slash, but we'd call it here.
            # if self.token_provider and hasattr(self.token_provider, 'slash'):
            #     await self.token_provider.slash(agent_id, slashed_amount)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error slashing agent: {e}")
            return False

    def _initialize_tokens(self):
        """Initialize token supplies and metrics"""
        # DracmaS (token canonico del ecosistema Empoorio)
        self.tokens[TokenType.DRACMAS] = TokenMetrics(
            token_type=TokenType.DRACMAS,
            total_supply=DMS_MAX_SUPPLY,
            circulating_supply=DMS_INITIAL_SUPPLY,
            price=1.0,
            holders=0
        )

    def _initialize_from_system_data(self):
        """Initialize engine with real system data from federated coordinator and rewards"""
        try:
            # Initialize federated coordinator if not provided
            if self.federated_coordinator is None and FederatedCoordinator is not None:
                config = get_config()
                self.federated_coordinator = FederatedCoordinator(config=config)

            # Load real agent data from federated coordinator
            if self.federated_coordinator:
                self._load_agents_from_coordinator()

            logger.info("✅ Initialized tokenomics engine with real system data")

        except Exception as e:
            logger.warning(f"Could not initialize with real system data: {e}. Using defaults.")

    def _initialize_prisoners_dilemma(self) -> Dict[Tuple[str, str], Tuple[float, float]]:
        """Initialize Prisoner's Dilemma payoff matrix"""
        # (action_agent1, action_agent2): (payoff_agent1, payoff_agent2)
        return {
            ("cooperate", "cooperate"): (3, 3),      # Mutual cooperation
            ("cooperate", "defect"): (0, 5),         # Agent 1 cooperates, Agent 2 defects
            ("defect", "cooperate"): (5, 0),         # Agent 1 defects, Agent 2 cooperates
            ("defect", "defect"): (1, 1)             # Mutual defection
        }

    def _initialize_staking_game(self) -> Dict[Tuple[str, str], Tuple[float, float]]:
        """Initialize Staking Game payoff matrix"""
        # Simplified staking game: (stake_high, stake_low)
        return {
            ("high", "high"): (2, 2),        # Both stake high - balanced rewards
            ("high", "low"): (1.5, 2.5),     # High staker gets less, low staker gets more
            ("low", "high"): (2.5, 1.5),     # Low staker gets more, high staker gets less
            ("low", "low"): (1, 1)           # Both stake low - minimal rewards
        }

    def register_agent(self, agent_id: str, agent_type: EconomicAgent,
                      initial_balance: Dict[TokenType, float] = None) -> AgentProfile:
        """Register new economic agent"""
        if initial_balance is None:
            initial_balance = {TokenType.DRACMAS: 0.0}

        profile = AgentProfile(
            agent_id=agent_id,
            agent_type=agent_type,
            balance=initial_balance.copy(),
            last_activity=datetime.now()
        )

        self.agents[agent_id] = profile

        # Update token metrics
        for token_type, amount in initial_balance.items():
            if token_type in self.tokens:
                self.tokens[token_type].holders += 1

        logger.info(f"👤 Agent registered: {agent_id} ({agent_type.value})")
        return profile

    def calculate_nash_equilibrium(self, game_matrix: Dict[Tuple[str, str], Tuple[float, float]],
                                 strategies: List[str]) -> Dict[str, Any]:
        """
        Calculate Nash Equilibrium for a given game
        Returns the equilibrium strategies and payoffs
        """
        nash_equilibria = []

        # Check all possible strategy combinations
        for strategy1 in strategies:
            for strategy2 in strategies:
                payoff1, payoff2 = game_matrix[(strategy1, strategy2)]

                # Check if this is a Nash equilibrium
                is_nash = True

                # Check if agent 1 would deviate
                for alt_strategy1 in strategies:
                    if alt_strategy1 != strategy1:
                        alt_payoff1, _ = game_matrix[(alt_strategy1, strategy2)]
                        if alt_payoff1 > payoff1:
                            is_nash = False
                            break

                if not is_nash:
                    continue

                # Check if agent 2 would deviate
                for alt_strategy2 in strategies:
                    if alt_strategy2 != strategy2:
                        _, alt_payoff2 = game_matrix[(strategy1, alt_strategy2)]
                        if alt_payoff2 > payoff2:
                            is_nash = False
                            break

                if is_nash:
                    nash_equilibria.append({
                        'strategy1': strategy1,
                        'strategy2': strategy2,
                        'payoff1': payoff1,
                        'payoff2': payoff2
                    })

        return {
            'equilibria': nash_equilibria,
            'num_equilibria': len(nash_equilibria),
            'strategies': strategies
        }

    def analyze_prisoners_dilemma(self, agent1_id: str, agent2_id: str) -> Dict[str, Any]:
        """Analyze Prisoner's Dilemma between two agents"""
        if agent1_id not in self.agents or agent2_id not in self.agents:
            raise ValueError("Agents not found")

        agent1 = self.agents[agent1_id]
        agent2 = self.agents[agent2_id]

        # Calculate cooperation probability based on reputation and history
        coop_prob1 = self._calculate_cooperation_probability(agent1)
        coop_prob2 = self._calculate_cooperation_probability(agent2)

        # Calculate deterministic expected payoffs based on cooperation probabilities
        expected_payoffs = self._calculate_expected_payoffs(coop_prob1, coop_prob2)

        # Calculate Nash equilibrium
        nash_analysis = self.calculate_nash_equilibrium(
            self.prisoners_dilemma_matrix,
            ["cooperate", "defect"]
        )

        return {
            'agent1_cooperation_prob': coop_prob1,
            'agent2_cooperation_prob': coop_prob2,
            'expected_payoffs': expected_payoffs,
            'nash_equilibrium': nash_analysis,
            'recommended_strategy': self._recommend_pd_strategy(coop_prob1, coop_prob2)
        }

    def _calculate_cooperation_probability(self, agent: AgentProfile) -> float:
        """Calculate probability of cooperation based on agent profile"""
        base_prob = 0.5  # Base 50% cooperation

        # Adjust based on reputation
        reputation_factor = agent.reputation_score / 100.0  # Assume 0-100 scale
        base_prob += reputation_factor * 0.3

        # Adjust based on stake amount (higher stake = more cooperative)
        stake_factor = min(agent.stake_amount / 10000.0, 1.0)
        base_prob += stake_factor * 0.2

        # Adjust based on contribution score
        contribution_factor = agent.contribution_score / 100.0
        base_prob += contribution_factor * 0.1

        return max(0.0, min(1.0, base_prob))

    def _calculate_expected_payoffs(self, coop_prob1: float, coop_prob2: float) -> Dict[str, float]:
        """Calculate expected payoffs deterministically based on cooperation probabilities"""
        # Expected payoff for agent 1
        # P(CC) * payoff_CC + P(CD) * payoff_CD + P(DC) * payoff_DC + P(DD) * payoff_DD
        expected_payoff1 = (
            coop_prob1 * coop_prob2 * self.prisoners_dilemma_matrix[("cooperate", "cooperate")][0] +
            coop_prob1 * (1 - coop_prob2) * self.prisoners_dilemma_matrix[("cooperate", "defect")][0] +
            (1 - coop_prob1) * coop_prob2 * self.prisoners_dilemma_matrix[("defect", "cooperate")][0] +
            (1 - coop_prob1) * (1 - coop_prob2) * self.prisoners_dilemma_matrix[("defect", "defect")][0]
        )

        # Expected payoff for agent 2
        expected_payoff2 = (
            coop_prob1 * coop_prob2 * self.prisoners_dilemma_matrix[("cooperate", "cooperate")][1] +
            coop_prob1 * (1 - coop_prob2) * self.prisoners_dilemma_matrix[("cooperate", "defect")][1] +
            (1 - coop_prob1) * coop_prob2 * self.prisoners_dilemma_matrix[("defect", "cooperate")][1] +
            (1 - coop_prob1) * (1 - coop_prob2) * self.prisoners_dilemma_matrix[("defect", "defect")][1]
        )

        return {
            'expected_payoff_agent1': expected_payoff1,
            'expected_payoff_agent2': expected_payoff2,
            'cooperation_probability_product': coop_prob1 * coop_prob2,
            'defection_probability_product': (1 - coop_prob1) * (1 - coop_prob2)
        }

    def _recommend_pd_strategy(self, coop_prob1: float, coop_prob2: float) -> str:
        """Recommend strategy for Prisoner's Dilemma"""
        avg_coop = (coop_prob1 + coop_prob2) / 2

        if avg_coop > 0.7:
            return "cooperate"  # High trust environment
        elif avg_coop > 0.4:
            return "tit_for_tat"  # Mixed strategy
        else:
            return "defect"  # Low trust environment

    def calculate_staking_rewards(self, agent_id: str, time_period_days: int = 30) -> Dict[str, Any]:
        """Calculate staking rewards using game theory"""
        if agent_id not in self.agents:
            raise ValueError("Agent not found")

        agent = self.agents[agent_id]
        stake_amount = agent.stake_amount

        if stake_amount <= 0:
            return {'rewards': 0, 'reason': 'No stake amount'}

        # Base reward calculation
        base_reward = stake_amount * self.staking_reward_rate * (time_period_days / 365)

        # Game theory adjustment based on network participation
        network_participation = self._calculate_network_participation(agent)
        game_multiplier = self._calculate_staking_game_multiplier(agent, network_participation)

        total_reward = base_reward * game_multiplier

        # Calculate opportunity cost (what they could earn elsewhere)
        opportunity_cost = stake_amount * 0.03 * (time_period_days / 365)  # 3% alternative APY

        return {
            'base_reward': base_reward,
            'game_multiplier': game_multiplier,
            'total_reward': total_reward,
            'opportunity_cost': opportunity_cost,
            'net_utility': total_reward - opportunity_cost,
            'staking_strategy': 'optimal' if game_multiplier > 1.0 else 'suboptimal'
        }

    def _calculate_network_participation(self, agent: AgentProfile) -> float:
        """Calculate agent's network participation score"""
        # Simplified calculation based on activity and contributions
        activity_score = 1.0 if agent.last_activity and \
                        (datetime.now() - agent.last_activity).days < 7 else 0.5

        contribution_score = agent.contribution_score / 100.0
        reputation_score = agent.reputation_score / 100.0

        return (activity_score + contribution_score + reputation_score) / 3.0

    def _calculate_staking_game_multiplier(self, agent: AgentProfile, participation: float) -> float:
        """Calculate game theory multiplier for staking rewards"""
        # Higher participation leads to higher rewards (cooperative equilibrium)
        base_multiplier = 1.0

        if participation > 0.8:
            base_multiplier = 1.5  # High participation bonus
        elif participation > 0.6:
            base_multiplier = 1.2  # Medium participation bonus
        elif participation < 0.3:
            base_multiplier = 0.8  # Low participation penalty

        # Risk adjustment based on agent's risk tolerance
        risk_adjustment = 1.0 + (agent.risk_tolerance - 0.5) * 0.2

        return base_multiplier * risk_adjustment

    def simulate_token_economics(self, time_steps: int = 100) -> Dict[str, Any]:
        """
        Calculate deterministic economic equilibrium instead of simulation.
        Uses real economic models to find stable states based on supply-demand equilibrium,
        agent utilities, and market clearing conditions.
        """
        logger.info("Calculating deterministic economic equilibrium.")

        # Calculate economic equilibrium deterministically
        equilibrium_state = self._calculate_economic_equilibrium()

        # Generate time series based on convergence to equilibrium
        time_series = self._generate_equilibrium_time_series(equilibrium_state, time_steps)

        # Analyze equilibria
        equilibria = self._analyze_equilibria(equilibrium_state)

        logger.info("Deterministic economic equilibrium calculation completed.")
        return {
            'equilibrium_state': equilibrium_state,
            'time_series': time_series,
            'equilibria': equilibria,
            'market_events': []  # No random events in deterministic model
        }

    def _calculate_economic_equilibrium(self) -> Dict[str, Any]:
        """Calculate deterministic economic equilibrium using supply-demand models"""
        # Calculate market clearing prices using supply-demand equilibrium
        equilibrium_prices = self._calculate_market_clearing_prices()

        # Calculate optimal agent allocations based on utility maximization
        equilibrium_balances = self._calculate_optimal_agent_allocations(equilibrium_prices)

        # Calculate total value locked at equilibrium
        total_value_locked = sum(
            sum(amount * equilibrium_prices[token_type] for token_type, amount in balances.items())
            for balances in equilibrium_balances.values()
        )

        # Get real activity metrics from federated coordinator
        active_agents = self._get_real_active_agents_count()

        return {
            'equilibrium_prices': equilibrium_prices,
            'equilibrium_balances': equilibrium_balances,
            'total_value_locked': total_value_locked,
            'active_agents': active_agents,
            'market_stability_score': self._calculate_market_stability_score(equilibrium_prices, equilibrium_balances)
        }

    def _calculate_market_clearing_prices(self) -> Dict[TokenType, float]:
        """Calculate market clearing prices using supply-demand equilibrium"""
        equilibrium_prices = {}

        for token_type, token_metrics in self.tokens.items():
            # Supply: total circulating supply
            supply = token_metrics.circulating_supply

            # Demand: based on agent preferences and utility functions
            demand = self._calculate_token_demand(token_type)

            # Market clearing price: where supply = demand
            # Using simple linear demand curve: P = a - b * Q
            # At equilibrium: supply = demand => P = a - b * supply
            base_price = token_metrics.price
            price_elasticity = self.price_elasticity

            # Adjust price based on supply-demand gap
            supply_demand_ratio = demand / max(supply, 1)
            price_adjustment = (supply_demand_ratio - 1) * price_elasticity

            equilibrium_price = base_price * (1 + price_adjustment)
            equilibrium_prices[token_type] = max(0.001, equilibrium_price)

        return equilibrium_prices

    def _calculate_token_demand(self, token_type: TokenType) -> float:
        """Calculate demand for a token based on agent preferences and real system data"""
        total_demand = 0.0

        # Base demand from registered agents
        for agent in self.agents.values():
            # Agent demand based on utility maximization
            agent_demand = self._calculate_agent_token_demand(agent, token_type)
            total_demand += agent_demand

        # Additional demand from federated learning activity
        if self.federated_coordinator:
            fl_demand = self._calculate_federated_learning_demand(token_type)
            total_demand += fl_demand

        return total_demand

    def _calculate_agent_token_demand(self, agent: AgentProfile, token_type: TokenType) -> float:
        """Calculate individual agent's demand for a token"""
        # Simplified demand based on agent type and current balance
        base_demand = 100.0  # Base demand

        # Adjust based on agent type preferences
        type_multiplier = 1.0

        # Adjust based on current balance (diminishing marginal utility)
        current_balance = agent.balance.get(token_type, 0.0)
        balance_adjustment = 1.0 / (1.0 + current_balance / 1000.0)  # Diminishing returns

        return base_demand * type_multiplier * balance_adjustment

    def _calculate_optimal_agent_allocations(self, prices: Dict[TokenType, float]) -> Dict[str, Dict[TokenType, float]]:
        """Calculate optimal token allocations for agents based on utility maximization"""
        optimal_balances = {}

        for agent_id, agent in self.agents.items():
            # Calculate optimal portfolio allocation
            optimal_allocation = self._optimize_agent_portfolio(agent, prices)
            optimal_balances[agent_id] = optimal_allocation

        return optimal_balances

    def _optimize_agent_portfolio(self, agent: AgentProfile, prices: Dict[TokenType, float]) -> Dict[TokenType, float]:
        """Optimize agent's token portfolio using mean-variance optimization"""
        # Simplified portfolio optimization
        total_wealth = sum(amount * prices[token_type] for token_type, amount in agent.balance.items())

        if total_wealth <= 0:
            return agent.balance.copy()

        # Target allocations based on agent type and risk tolerance
        target_allocations = self._calculate_target_allocations(agent)

        # Calculate optimal amounts
        optimal_amounts = {}
        for token_type, target_weight in target_allocations.items():
            optimal_amounts[token_type] = (total_wealth * target_weight) / prices[token_type]

        return optimal_amounts

    def _calculate_target_allocations(self, agent: AgentProfile) -> Dict[TokenType, float]:
        """Calculate target portfolio allocations based on agent profile"""
        # Base allocations
        return {TokenType.DRACMAS: 1.0}

    def _calculate_market_stability_score(self, prices: Dict[TokenType, float],
                                        balances: Dict[str, Dict[TokenType, float]]) -> float:
        """Calculate market stability score based on equilibrium conditions"""
        # Price stability (lower volatility is better)
        price_values = list(prices.values())
        price_volatility = np.std(price_values) / max(np.mean(price_values), 0.001)

        # Balance distribution entropy (higher entropy = more balanced)
        total_balances = defaultdict(float)
        for agent_balances in balances.values():
            for token_type, amount in agent_balances.items():
                total_balances[token_type] += amount

        balance_entropy = self._calculate_distribution_entropy(list(total_balances.values()))

        # Combine metrics (0-100 scale)
        stability_score = 100 * (1 - min(price_volatility, 1.0)) * (balance_entropy)
        return max(0.0, min(100.0, stability_score))

    def _generate_equilibrium_time_series(self, equilibrium_state: Dict[str, Any], time_steps: int) -> List[Dict[str, Any]]:
        """Generate time series showing convergence to equilibrium with real system data"""
        time_series = []

        # Start from current state
        current_prices = {token_type: metrics.price for token_type, metrics in self.tokens.items()}
        current_balances = {agent_id: agent.balance.copy() for agent_id, agent in self.agents.items()}

        # Target equilibrium
        target_prices = equilibrium_state['equilibrium_prices']
        target_balances = equilibrium_state['equilibrium_balances']

        for step in range(time_steps):
            # Exponential convergence to equilibrium
            convergence_rate = 0.05  # 5% convergence per step

            # Interpolate prices
            step_prices = {}
            for token_type in current_prices:
                current = current_prices[token_type]
                target = target_prices.get(token_type, current)
                step_prices[token_type] = current + (target - current) * convergence_rate

            # Interpolate balances
            step_balances = {}
            for agent_id in current_balances:
                agent_current = current_balances[agent_id]
                agent_target = target_balances.get(agent_id, agent_current)
                agent_step = {}
                for token_type in agent_current:
                    current_amt = agent_current.get(token_type, 0.0)
                    target_amt = agent_target.get(token_type, current_amt)
                    agent_step[token_type] = current_amt + (target_amt - current_amt) * convergence_rate
                step_balances[agent_id] = agent_step

            # Calculate step metrics with real data
            total_value_locked = sum(
                sum(amount * step_prices[token_type] for token_type, amount in balances.items())
                for balances in step_balances.values()
            )

            # Get real active agents count
            active_agents = self._get_real_active_agents_count()

            step_data = {
                'step': step,
                'token_prices': step_prices,
                'total_value_locked': total_value_locked,
                'active_agents': active_agents
            }

            time_series.append(step_data)

            # Update for next step
            current_prices = step_prices
            current_balances = step_balances

        return time_series

    def _analyze_equilibria(self, equilibrium_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze the calculated economic equilibria"""
        equilibria = []

        # Check for price stability equilibrium
        price_volatility = np.std(list(equilibrium_state['equilibrium_prices'].values()))
        if price_volatility < 0.05:
            equilibria.append({
                'type': 'price_stability',
                'total_value_locked': equilibrium_state['total_value_locked'],
                'price_volatility': price_volatility,
                'description': 'Market prices have reached stable equilibrium'
            })

        # Check for balanced distribution equilibrium
        token_totals = defaultdict(float)
        for agent_balances in equilibrium_state['equilibrium_balances'].values():
            for token_type, amount in agent_balances.items():
                token_totals[token_type] += amount

        distribution_entropy = self._calculate_distribution_entropy(list(token_totals.values()))
        if distribution_entropy > 0.8:
            equilibria.append({
                'type': 'balanced_distribution',
                'distribution_entropy': distribution_entropy,
                'description': 'Token distribution is well-balanced at equilibrium'
            })

        # Check for utility maximization equilibrium
        if equilibrium_state['market_stability_score'] > 80:
            equilibria.append({
                'type': 'utility_maximization',
                'stability_score': equilibrium_state['market_stability_score'],
                'description': 'Agents have reached optimal utility-maximizing allocations'
            })

        return equilibria

    def _detect_economic_equilibrium(self, prices: Dict[TokenType, float],
                                   balances: Dict[str, Dict[TokenType, float]]) -> Optional[Dict[str, Any]]:
        """Detect if the system has reached economic equilibrium"""
        # Simplified equilibrium detection
        # In a real implementation, this would use more sophisticated economic indicators

        total_value = sum(sum(balance.values()) for balance in balances.values())
        price_stability = np.std(list(prices.values()))

        # Check for price stability (low volatility)
        if price_stability < 0.05:
            return {
                'type': 'price_stability',
                'total_value_locked': total_value,
                'price_volatility': price_stability,
                'description': 'Market prices have stabilized'
            }

        # Check for balanced token distribution
        token_totals = defaultdict(float)
        for balance in balances.values():
            for token_type, amount in balance.items():
                token_totals[token_type] += amount

        distribution_entropy = self._calculate_distribution_entropy(list(token_totals.values()))
        if distribution_entropy > 0.8:  # High entropy = balanced distribution
            return {
                'type': 'balanced_distribution',
                'distribution_entropy': distribution_entropy,
                'description': 'Token distribution is well-balanced'
            }

        return None

    def _calculate_distribution_entropy(self, values: List[float]) -> float:
        """Calculate Shannon entropy of a distribution"""
        total = sum(values)
        if total == 0:
            return 0.0

        probabilities = [v/total for v in values]
        entropy = -sum(p * math.log2(p) for p in probabilities if p > 0)

        # Normalize by maximum possible entropy
        max_entropy = math.log2(len(values))
        return entropy / max_entropy if max_entropy > 0 else 0.0

    def calculate_network_utility(self) -> Dict[str, Any]:
        """Calculate overall network utility using game theory"""
        if not self.agents:
            return {'network_utility': 0, 'reason': 'No agents registered'}

        # Calculate individual utilities
        agent_utilities = {}
        for agent_id, agent in self.agents.items():
            utility = self._calculate_agent_utility(agent)
            agent_utilities[agent_id] = utility

        # Calculate network-level metrics
        total_utility = sum(agent_utilities.values())
        avg_utility = total_utility / len(agent_utilities)

        # Calculate Pareto efficiency
        pareto_efficient = self._check_pareto_efficiency(agent_utilities)

        # Calculate Nash equilibrium status
        nash_status = self._analyze_network_nash_equilibrium()

        return {
            'total_network_utility': total_utility,
            'average_agent_utility': avg_utility,
            'pareto_efficient': pareto_efficient,
            'nash_equilibrium_reached': nash_status['reached'],
            'agent_utilities': agent_utilities,
            'network_health_score': self._calculate_network_health_score(agent_utilities, nash_status)
        }

    def _calculate_agent_utility(self, agent: AgentProfile) -> float:
        """Calculate utility for an individual agent"""
        # Utility = balance_value + reputation_bonus + contribution_bonus - risk_penalty
        balance_value = sum(amount * self.tokens[token_type].price
                          for token_type, amount in agent.balance.items())

        reputation_bonus = agent.reputation_score * 10
        contribution_bonus = agent.contribution_score * 5
        risk_penalty = agent.risk_tolerance * balance_value * 0.1  # Risk-adjusted penalty

        return balance_value + reputation_bonus + contribution_bonus - risk_penalty

    def _check_pareto_efficiency(self, agent_utilities: Dict[str, float]) -> bool:
        """Check if current allocation is Pareto efficient"""
        # Simplified check: if any agent can be made better off without making others worse
        # In practice, this requires checking all possible reallocations
        utilities = list(agent_utilities.values())

        # Check if utilities are reasonably balanced (simplified Pareto check)
        avg_utility = sum(utilities) / len(utilities)
        max_deviation = max(abs(u - avg_utility) for u in utilities) / avg_utility

        return max_deviation < 0.5  # Within 50% of average

    def _analyze_network_nash_equilibrium(self) -> Dict[str, Any]:
        """Analyze if network has reached Nash equilibrium"""
        # Simplified analysis: check if agents are satisfied with current strategies
        satisfied_agents = 0

        for agent in self.agents.values():
            # Agent is satisfied if their utility is above threshold
            utility = self._calculate_agent_utility(agent)
            threshold = 1000  # Arbitrary threshold

            if utility > threshold:
                satisfied_agents += 1

        satisfaction_ratio = satisfied_agents / len(self.agents) if self.agents else 0

        return {
            'reached': satisfaction_ratio > 0.8,  # 80% of agents satisfied
            'satisfaction_ratio': satisfaction_ratio,
            'satisfied_agents': satisfied_agents,
            'total_agents': len(self.agents)
        }

    def _calculate_network_health_score(self, agent_utilities: Dict[str, float],
                                      nash_status: Dict[str, Any]) -> float:
        """Calculate overall network health score"""
        # Combine multiple factors
        utility_score = min(100, sum(agent_utilities.values()) / len(agent_utilities) / 10)
        nash_score = 100 if nash_status['reached'] else 50
        participation_score = len(self.agents) * 2  # More agents = healthier network

        # Weighted average
        health_score = (utility_score * 0.4 + nash_score * 0.4 + participation_score * 0.2)
        return min(100, max(0, health_score))

    def _load_agents_from_coordinator(self):
        """Load real agent data from federated coordinator"""
        if not self.federated_coordinator:
            return

        try:
            # Get active sessions and extract node information
            active_sessions = self.federated_coordinator.get_active_sessions()

            for session_info in active_sessions:
                session_id = session_info['session_id']
                participants = session_info.get('participants', 0)

                # Register nodes as agents if not already registered
                # Note: In real implementation, we'd get actual node IDs from coordinator
                for i in range(participants):
                    node_id = f"node_{session_id}_{i}"
                    if node_id not in self.agents:
                        # Determine agent type based on session data
                        agent_type = EconomicAgent.NODE  # Default to NODE

                        # Create agent profile with real data
                        self.register_agent(
                            agent_id=node_id,
                            agent_type=agent_type,
                            initial_balance={
                                TokenType.DRACMAS: 0.0
                            }
                        )

                        # Update last activity
                        self.agents[node_id].last_activity = datetime.now()

            logger.info(f"✅ Loaded {len(self.agents)} agents from federated coordinator")

        except Exception as e:
            logger.warning(f"Could not load agents from coordinator: {e}")

    def _load_economic_metrics_from_rewards(self):
        """Load real economic metrics from rewards system"""
        return

    def _get_real_active_agents_count(self) -> int:
        """Get real count of active agents from federated coordinator"""
        if not self.federated_coordinator:
            # Fallback to registered agents with recent activity
            return len([a for a in self.agents.values()
                       if a.last_activity and (datetime.now() - a.last_activity).days < 30])

        try:
            active_sessions = self.federated_coordinator.get_active_sessions()
            total_participants = sum(session.get('participants', 0) for session in active_sessions)
            return max(total_participants, len(self.agents))
        except Exception:
            return len(self.agents)

    def _calculate_federated_learning_demand(self, token_type: TokenType) -> float:
        """Calculate additional demand from federated learning activity"""
        if not self.federated_coordinator:
            return 0.0

        try:
            active_sessions = self.federated_coordinator.get_active_sessions()
            total_demand = 0.0

            for session in active_sessions:
                participants = session.get('participants', 0)
                rounds = session.get('current_round', 0)

                total_demand += participants * 5.0 * (rounds + 1)

            return total_demand

        except Exception:
            return 0.0

    def _calculate_rewards_system_demand(self, token_type: TokenType) -> float:
        """Calculate additional demand from rewards system activity"""
        return 0.0

# Global tokenomics engine instance
tokenomics_instance = None

def get_tokenomics_engine(federated_coordinator=None, dracma_calculator=None) -> TokenomicsEngine:
    """Get global tokenomics engine instance with optional system integration"""
    global tokenomics_instance
    if tokenomics_instance is None:
        tokenomics_instance = TokenomicsEngine(
            federated_coordinator=federated_coordinator,
            dracma_calculator=dracma_calculator
        )
    return tokenomics_instance

if __name__ == '__main__':
    # Demo
    engine = get_tokenomics_engine()

    print("💰 Tokenomics Engine Demo")
    print("=" * 50)

    # Register sample agents
    agent1 = engine.register_agent("node_001", EconomicAgent.NODE, {TokenType.DRACMAS: 5000})
    agent2 = engine.register_agent("user_001", EconomicAgent.USER, {TokenType.DRACMAS: 2000})

    print("✅ Sample agents registered")

    # Analyze Prisoner's Dilemma
    pd_analysis = engine.analyze_prisoners_dilemma("node_001", "user_001")
    print(f"🎲 PD Analysis: Recommended strategy = {pd_analysis['recommended_strategy']}")

    # Calculate staking rewards
    staking_rewards = engine.calculate_staking_rewards("node_001")
    print(f"🏦 Staking Rewards: ${staking_rewards['total_reward']:.2f}")

    # Calculate network utility
    network_utility = engine.calculate_network_utility()
    print(f"🌐 Network Utility: ${network_utility['total_network_utility']:.2f}")
    print("🎉 Tokenomics Engine Demo completed!")
