#!/usr/bin/env python3
"""
Network Utility Calculator for Ailoos
Implementa cálculo de utilidad de red usando teoría de juegos
"""

import math
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import asyncio
from collections import defaultdict

from .tokenomics_engine import get_tokenomics_engine, TokenomicsEngine, EconomicAgent

# Importar RoundResult solo para type hinting si es necesario, 
# pero para evitar ciclos usamos Any o importamos dentro del método


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GameTheoryModel(Enum):
    """Modelos de teoría de juegos disponibles"""
    PRISONERS_DILEMMA = "prisoners_dilemma"
    STAG_HUNT = "stag_hunt"
    BATTLE_OF_THE_SEXES = "battle_of_the_sexes"
    CHICKEN_GAME = "chicken_game"
    TRUST_GAME = "trust_game"
    PUBLIC_GOODS_GAME = "public_goods_game"

@dataclass
class UtilityFunction:
    """Función de utilidad para agentes"""
    agent_id: str
    parameters: Dict[str, float] = field(default_factory=dict)
    risk_aversion: float = 0.5  # 0 = risk neutral, 1 = risk averse
    time_preference: float = 0.95  # Discount factor for future utility

    def calculate_utility(self, outcomes: Dict[str, Any]) -> float:
        """Calculate utility for given outcomes"""
        # Base utility from token balances
        balance_utility = outcomes.get('balance_value', 0)

        # Reputation utility
        reputation_utility = outcomes.get('reputation_score', 0) * 10

        # Network participation utility
        participation_utility = outcomes.get('participation_score', 0) * 5

        # Risk adjustment
        total_utility = balance_utility + reputation_utility + participation_utility
        risk_penalty = self.risk_aversion * outcomes.get('volatility', 0) * total_utility

        return total_utility - risk_penalty

@dataclass
class GameStrategy:
    """Estrategia en un juego"""
    strategy_id: str
    name: str
    description: str
    payoffs: Dict[str, float] = field(default_factory=dict)
    probability: float = 1.0

@dataclass
class GameEquilibrium:
    """Equilibrio de un juego"""
    equilibrium_id: str
    game_type: GameTheoryModel
    strategies: Dict[str, str]  # agent_id -> strategy_name
    payoffs: Dict[str, float]   # agent_id -> payoff
    stability_score: float = 0.0
    reached_at: Optional[datetime] = None

class NetworkUtilityCalculator:
    """
    Calculadora de utilidad de red usando teoría de juegos avanzada
    Implementa múltiples modelos de juegos cooperativos y no cooperativos
    """

    def __init__(self):
        self.tokenomics = get_tokenomics_engine()

        # Game theory models
        self.game_models: Dict[GameTheoryModel, Dict] = {}
        self._initialize_game_models()

        # Agent utility functions
        self.utility_functions: Dict[str, UtilityFunction] = {}

        # Historical equilibria
        self.equilibria_history: List[GameEquilibrium] = []

        # Network state
        self.network_state = {
            'cooperation_level': 0.5,
            'trust_level': 0.5,
            'participation_rate': 0.7,
            'conflict_resolution_efficiency': 0.6
        }

        logger.info("🧮 Network Utility Calculator initialized")

    def _initialize_game_models(self):
        """Initialize predefined game theory models"""

        # Prisoner's Dilemma
        self.game_models[GameTheoryModel.PRISONERS_DILEMMA] = {
            'payoff_matrix': {
                ('cooperate', 'cooperate'): (3, 3),
                ('cooperate', 'defect'): (0, 5),
                ('defect', 'cooperate'): (5, 0),
                ('defect', 'defect'): (1, 1)
            },
            'strategies': ['cooperate', 'defect'],
            'description': 'Classic cooperation vs defection dilemma'
        }

        # Stag Hunt (Coordination Game)
        self.game_models[GameTheoryModel.STAG_HUNT] = {
            'payoff_matrix': {
                ('stag', 'stag'): (4, 4),
                ('stag', 'hare'): (1, 2),
                ('hare', 'stag'): (2, 1),
                ('hare', 'hare'): (2, 2)
            },
            'strategies': ['stag', 'hare'],
            'description': 'Coordination between risky cooperation and safe defection'
        }

        # Battle of the Sexes
        self.game_models[GameTheoryModel.BATTLE_OF_THE_SEXES] = {
            'payoff_matrix': {
                ('opera', 'opera'): (2, 1),
                ('opera', 'football'): (0, 0),
                ('football', 'opera'): (0, 0),
                ('football', 'football'): (1, 2)
            },
            'strategies': ['opera', 'football'],
            'description': 'Coordination with conflicting preferences'
        }

        # Chicken Game
        self.game_models[GameTheoryModel.CHICKEN_GAME] = {
            'payoff_matrix': {
                ('swerve', 'swerve'): (3, 3),
                ('swerve', 'straight'): (1, 4),
                ('straight', 'swerve'): (4, 1),
                ('straight', 'straight'): (0, 0)
            },
            'strategies': ['swerve', 'straight'],
            'description': 'Escalation and brinkmanship'
        }

        # Trust Game
        self.game_models[GameTheoryModel.TRUST_GAME] = {
            'payoff_matrix': {
                ('trust', 'reciprocate'): (8, 8),
                ('trust', 'exploit'): (2, 10),
                ('distrust', 'reciprocate'): (5, 5),
                ('distrust', 'exploit'): (5, 5)
            },
            'strategies': ['trust', 'distrust'],
            'description': 'Trust and reciprocity dynamics'
        }

        # Public Goods Game
        self.game_models[GameTheoryModel.PUBLIC_GOODS_GAME] = {
            'payoff_matrix': {
                ('contribute', 'contribute'): (6, 6),
                ('contribute', 'free_ride'): (3, 8),
                ('free_ride', 'contribute'): (8, 3),
                ('free_ride', 'free_ride'): (4, 4)
            },
            'strategies': ['contribute', 'free_ride'],
            'description': 'Public goods provision and free-riding'
        }

    def register_utility_function(self, agent_id: str, parameters: Dict[str, float] = None,
                                risk_aversion: float = 0.5) -> UtilityFunction:
        """Register utility function for an agent"""
        if parameters is None:
            parameters = {}

        utility_func = UtilityFunction(
            agent_id=agent_id,
            parameters=parameters,
            risk_aversion=risk_aversion
        )

        self.utility_functions[agent_id] = utility_func
        return utility_func

    def calculate_network_equilibrium(self, game_type: GameTheoryModel = GameTheoryModel.PRISONERS_DILEMMA) -> Dict[str, Any]:
        """
        Calculate Nash equilibrium for the entire network using specified game model
        """
        if game_type not in self.game_models:
            raise ValueError(f"Unknown game type: {game_type}")

        game_model = self.game_models[game_type]
        strategies = game_model['strategies']

        # Get all agents
        agents = list(self.tokenomics.agents.keys())
        if len(agents) < 2:
            return {'error': 'Need at least 2 agents for equilibrium calculation'}

        # Calculate strategy probabilities based on agent profiles
        strategy_probs = {}
        for agent_id in agents:
            probs = self._calculate_strategy_probabilities(agent_id, strategies, game_type)
            strategy_probs[agent_id] = probs

        # Find Nash equilibrium using iterative best response
        equilibrium = self._find_nash_equilibrium_iterative(agents, strategy_probs, game_model)

        # Calculate network-level utilities
        network_payoffs = self._calculate_network_payoffs(equilibrium, game_model)

        # Assess equilibrium stability
        stability = self._assess_equilibrium_stability(equilibrium, strategy_probs, game_model)

        result = {
            'game_type': game_type.value,
            'equilibrium': equilibrium,
            'network_payoffs': network_payoffs,
            'stability_score': stability['score'],
            'stability_analysis': stability['analysis'],
            'participation_rate': len(agents) / max(1, len(self.tokenomics.agents)),
            'cooperation_index': self._calculate_cooperation_index(equilibrium, game_type)
        }

        # Store equilibrium in history
        eq_record = GameEquilibrium(
            equilibrium_id=f"eq_{datetime.now().isoformat()}",
            game_type=game_type,
            strategies=equilibrium,
            payoffs=network_payoffs,
            stability_score=stability['score'],
            reached_at=datetime.now()
        )
        self.equilibria_history.append(eq_record)

        return result

    def _calculate_strategy_probabilities(self, agent_id: str, strategies: List[str],
                                        game_type: GameTheoryModel) -> Dict[str, float]:
        """Calculate probability distribution over strategies for an agent"""
        if agent_id not in self.tokenomics.agents:
            # Default uniform distribution
            prob = 1.0 / len(strategies)
            return {strategy: prob for strategy in strategies}

        agent = self.tokenomics.agents[agent_id]

        # Base probabilities based on agent profile
        base_probs = {}

        for strategy in strategies:
            prob = 0.5  # Base probability

            # Adjust based on agent type
            if agent.agent_type == EconomicAgent.NODE:
                if strategy in ['cooperate', 'contribute', 'stag']:
                    prob += 0.2  # Nodes tend to cooperate more
            elif agent.agent_type == EconomicAgent.VALIDATOR:
                if strategy in ['cooperate', 'trust']:
                    prob += 0.15  # Validators are trustworthy

            # Adjust based on reputation
            reputation_factor = agent.reputation_score / 100.0
            if strategy in ['cooperate', 'trust', 'contribute']:
                prob += reputation_factor * 0.1

            # Adjust based on risk tolerance
            if strategy in ['defect', 'free_ride', 'straight']:
                prob += (1 - agent.risk_tolerance) * 0.1

            base_probs[strategy] = max(0.1, min(0.9, prob))

        # Normalize probabilities
        total = sum(base_probs.values())
        return {strategy: prob/total for strategy, prob in base_probs.items()}

    def _find_nash_equilibrium_iterative(self, agents: List[str],
                                       strategy_probs: Dict[str, Dict[str, float]],
                                       game_model: Dict) -> Dict[str, str]:
        """Find Nash equilibrium using iterative best response"""
        max_iterations = 100
        tolerance = 0.01

        # Initialize with random strategies
        current_strategies = {}
        for agent_id in agents:
            strategies = list(strategy_probs[agent_id].keys())
            current_strategies[agent_id] = np.random.choice(strategies)

        for iteration in range(max_iterations):
            changed = False

            for agent_id in agents:
                # Calculate expected payoffs for each strategy
                expected_payoffs = {}
                strategies = list(strategy_probs[agent_id].keys())

                for strategy in strategies:
                    test_strategies = current_strategies.copy()
                    test_strategies[agent_id] = strategy

                    # Calculate expected payoff against other agents' mixed strategies
                    total_payoff = 0
                    total_prob = 0

                    for opponent_id in agents:
                        if opponent_id == agent_id:
                            continue

                        opponent_strategies = list(strategy_probs[opponent_id].keys())
                        for opp_strategy in opponent_strategies:
                            prob = strategy_probs[opponent_id][opp_strategy]
                            payoff_key = (strategy, opp_strategy) if agent_id < opponent_id else (opp_strategy, strategy)
                            payoff = game_model['payoff_matrix'].get(payoff_key, (0, 0))

                            # Get payoff for current agent
                            agent_payoff = payoff[0] if agent_id < opponent_id else payoff[1]
                            total_payoff += agent_payoff * prob
                            total_prob += prob

                    expected_payoffs[strategy] = total_payoff / max(total_prob, 1)

                # Choose best response
                best_strategy = max(expected_payoffs.items(), key=lambda x: x[1])[0]

                if best_strategy != current_strategies[agent_id]:
                    current_strategies[agent_id] = best_strategy
                    changed = True

            # Check for convergence
            if not changed:
                break

        return current_strategies

    def _calculate_network_payoffs(self, equilibrium: Dict[str, str], game_model: Dict) -> Dict[str, float]:
        """Calculate payoffs for all agents in equilibrium"""
        payoffs = {}

        for agent_id, strategy in equilibrium.items():
            # Simplified: assume symmetric payoffs
            # In reality, would calculate based on all strategy combinations
            payoff_key = (strategy, strategy)  # Assume all play same strategy for simplicity
            payoff_matrix = game_model['payoff_matrix'].get(payoff_key, (1, 1))
            payoffs[agent_id] = payoff_matrix[0]  # Take first payoff

        return payoffs

    def _assess_equilibrium_stability(self, equilibrium: Dict[str, str],
                                    strategy_probs: Dict[str, Dict[str, float]],
                                    game_model: Dict) -> Dict[str, Any]:
        """Assess stability of the equilibrium"""
        stability_score = 1.0
        issues = []

        # Check if anyone wants to deviate
        for agent_id, strategy in equilibrium.items():
            agent_probs = strategy_probs[agent_id]
            strategies = list(agent_probs.keys())

            current_payoff = 0
            # Simplified stability check
            for other_agent, other_strategy in equilibrium.items():
                if other_agent != agent_id:
                    payoff_key = (strategy, other_strategy)
                    payoff = game_model['payoff_matrix'].get(payoff_key, (0, 0))
                    current_payoff += payoff[0]  # Simplified

            # Check alternative strategies
            for alt_strategy in strategies:
                if alt_strategy != strategy:
                    alt_payoff = 0
                    for other_agent, other_strategy in equilibrium.items():
                        if other_agent != agent_id:
                            payoff_key = (alt_strategy, other_strategy)
                            payoff = game_model['payoff_matrix'].get(payoff_key, (0, 0))
                            alt_payoff += payoff[0]

                    if alt_payoff > current_payoff:
                        stability_score -= 0.2
                        issues.append(f"{agent_id} would benefit from switching to {alt_strategy}")

        return {
            'score': max(0.0, stability_score),
            'analysis': {
                'stable': stability_score >= 0.8,
                'issues': issues,
                'recommendations': self._generate_stability_recommendations(issues)
            }
        }

    def _calculate_cooperation_index(self, equilibrium: Dict[str, str],
                                   game_type: GameTheoryModel) -> float:
        """Calculate cooperation index for the equilibrium"""
        cooperative_strategies = {
            GameTheoryModel.PRISONERS_DILEMMA: ['cooperate'],
            GameTheoryModel.STAG_HUNT: ['stag'],
            GameTheoryModel.TRUST_GAME: ['trust'],
            GameTheoryModel.PUBLIC_GOODS_GAME: ['contribute']
        }

        coop_strategies = cooperative_strategies.get(game_type, [])
        total_agents = len(equilibrium)
        cooperating_agents = sum(1 for strategy in equilibrium.values()
                               if strategy in coop_strategies)

        return cooperating_agents / max(total_agents, 1)

    def _generate_stability_recommendations(self, issues: List[str]) -> List[str]:
        """Generate recommendations to improve equilibrium stability"""
        recommendations = []

        if issues:
            recommendations.append("Incentivize cooperative behavior through rewards")
            recommendations.append("Implement reputation systems to discourage defection")
            recommendations.append("Consider mechanism design to align incentives")

        if len(issues) > len(self.tokenomics.agents) * 0.5:
            recommendations.append("Network may need governance intervention")
            recommendations.append("Consider adjusting tokenomics parameters")

        return recommendations

    def simulate_network_evolution(self, steps: int = 50,
                                 game_type: GameTheoryModel = GameTheoryModel.PRISONERS_DILEMMA) -> Dict[str, Any]:
        """Simulate network evolution over time"""
        evolution_data = {
            'time_series': [],
            'equilibria_transitions': [],
            'cooperation_trends': [],
            'utility_distribution': []
        }

        current_state = self.network_state.copy()

        for step in range(steps):
            # Calculate current equilibrium
            equilibrium_result = self.calculate_network_equilibrium(game_type)

            # Update network state based on equilibrium
            cooperation_index = equilibrium_result.get('cooperation_index', 0.5)
            stability_score = equilibrium_result.get('stability_score', 0.5)

            # State evolution (simplified dynamics)
            current_state['cooperation_level'] = 0.9 * current_state['cooperation_level'] + 0.1 * cooperation_index
            current_state['trust_level'] = 0.95 * current_state['trust_level'] + 0.05 * stability_score
            current_state['participation_rate'] = min(1.0, current_state['participation_rate'] + 0.001)

            # Record step data
            step_data = {
                'step': step,
                'cooperation_index': cooperation_index,
                'stability_score': stability_score,
                'network_state': current_state.copy(),
                'equilibrium': equilibrium_result['equilibrium']
            }

            evolution_data['time_series'].append(step_data)

            # Check for phase transitions
            if step > 0:
                prev_coop = evolution_data['time_series'][step-1]['cooperation_index']
                if abs(cooperation_index - prev_coop) > 0.3:
                    evolution_data['equilibria_transitions'].append({
                        'step': step,
                        'transition_type': 'cooperation_jump' if cooperation_index > prev_coop else 'cooperation_drop',
                        'magnitude': abs(cooperation_index - prev_coop)
                    })

        # Analyze trends
        cooperation_trend = self._analyze_trend([s['cooperation_index'] for s in evolution_data['time_series']])
        evolution_data['cooperation_trends'] = cooperation_trend

        return evolution_data

    def _analyze_trend(self, values: List[float]) -> Dict[str, Any]:
        """Analyze trend in a time series"""
        if len(values) < 2:
            return {'trend': 'insufficient_data'}

        # Simple linear regression
        x = np.arange(len(values))
        slope, intercept = np.polyfit(x, values, 1)

        trend_direction = 'increasing' if slope > 0.001 else 'decreasing' if slope < -0.001 else 'stable'

        return {
            'trend': trend_direction,
            'slope': slope,
            'volatility': np.std(values),
            'final_value': values[-1],
            'change_percent': (values[-1] - values[0]) / max(abs(values[0]), 0.001) * 100
        }

    def calculate_optimal_network_parameters(self) -> Dict[str, Any]:
        """Calculate optimal network parameters using game theory"""
        # Use evolutionary game theory to find optimal parameters

        # Test different parameter combinations
        parameter_sets = [
            {'inflation_rate': 0.02, 'staking_reward': 0.08, 'slashing_penalty': 0.1},
            {'inflation_rate': 0.03, 'staking_reward': 0.10, 'slashing_penalty': 0.15},
            {'inflation_rate': 0.015, 'staking_reward': 0.06, 'slashing_penalty': 0.08},
            {'inflation_rate': 0.025, 'staking_reward': 0.09, 'slashing_penalty': 0.12}
        ]

        best_parameters = None
        best_score = -float('inf')

        for params in parameter_sets:
            # Temporarily set parameters
            old_params = {
                'inflation_rate': self.tokenomics.inflation_rate,
                'staking_reward_rate': self.tokenomics.staking_reward_rate,
                'slashing_penalty': self.tokenomics.slashing_penalty
            }

            self.tokenomics.inflation_rate = params['inflation_rate']
            self.tokenomics.staking_reward_rate = params['staking_reward']
            self.tokenomics.slashing_penalty = params['slashing_penalty']

            # Calculate network utility with these parameters
            network_utility = self.tokenomics.calculate_network_utility()
            score = network_utility.get('network_health_score', 0)

            # Restore old parameters
            self.tokenomics.inflation_rate = old_params['inflation_rate']
            self.tokenomics.staking_reward_rate = old_params['staking_reward_rate']
            self.tokenomics.slashing_penalty = old_params['slashing_penalty']

            if score > best_score:
                best_score = score
                best_parameters = params

        return {
            'optimal_parameters': best_parameters,
            'expected_health_score': best_score,
            'parameter_sensitivity': self._analyze_parameter_sensitivity()
        }

    async def update_from_round_result(self, round_result: Any):
        """
        Update network state and agent profiles based on real training round results.
        
        Args:
            round_result: RoundResult object from real_federated_training_loop
        """
        try:
            # Update network state
            if hasattr(round_result, 'global_accuracy'):
                # Map accuracy to trust/cooperation (higher accuracy -> higher trust)
                self.network_state['trust_level'] = 0.9 * self.network_state['trust_level'] + 0.1 * round_result.global_accuracy
            
            if hasattr(round_result, 'participants') and hasattr(round_result, 'total_samples'):
                # Participation rate approximation
                active_count = len(round_result.participants)
                total_known = len(self.tokenomics.agents)
                if total_known > 0:
                    participation = active_count / total_known
                    self.network_state['participation_rate'] = 0.8 * self.network_state['participation_rate'] + 0.2 * participation

            # Update individual agents and distribute rewards
            if hasattr(round_result, 'contributions'):
                for contribution in round_result.contributions:
                    node_id = contribution.node_id
                    
                    # Ensure agent exists in tokenomics engine
                    if node_id not in self.tokenomics.agents:
                        # Register new agent if not exists
                        self.tokenomics.register_agent(node_id, EconomicAgent.NODE)
                    
                    agent = self.tokenomics.agents[node_id]
                    
                    # Update reputation based on contribution quality
                    quality_score = getattr(contribution, 'model_quality_score', 0.5)
                    agent.reputation_score = 0.9 * agent.reputation_score + 0.1 * (quality_score * 100)
                    
                    # Update risk tolerance based on stability (gradient norm)
                    grad_norm = getattr(contribution, 'gradient_norm', 1.0)
                    # Lower gradient norm -> more stable -> higher risk tolerance (simplified)
                    stability = 1.0 / (1.0 + grad_norm)
                    agent.risk_tolerance = 0.9 * agent.risk_tolerance + 0.1 * stability
                    
                    # Distribute Rewards or Slash
                    # Simple formula: reward = quality_score * 10
                    if quality_score < 0.2:
                        # Slash for poor quality
                        await self.tokenomics.slash_agent(
                            agent_id=node_id,
                            amount=50.0, # Fixed penalty
                            reason=f"Low quality contribution ({quality_score:.2f}) in round {getattr(round_result, 'round_number', '?')}"
                        )
                    elif grad_norm > 100.0:
                        # Slash for instability/malicious gradient
                        await self.tokenomics.slash_agent(
                            agent_id=node_id,
                            amount=100.0,
                            reason=f"Unstable gradient (norm {grad_norm:.2f}) in round {getattr(round_result, 'round_number', '?')}"
                        )
                    else:
                        reward_amount = quality_score * 10.0
                        if reward_amount > 0:
                            await self.tokenomics.distribute_reward(
                                agent_id=node_id,
                                amount=reward_amount,
                                reason=f"Training contribution round {getattr(round_result, 'round_number', '?')}"
                            )
                    
            logger.info(f"🔄 Network utility updated from round {getattr(round_result, 'round_number', '?')}")
            
        except Exception as e:
            logger.error(f"❌ Error updating network utility from round result: {e}")

    def _analyze_parameter_sensitivity(self) -> Dict[str, float]:
        """Analyze sensitivity of network health to parameter changes"""
        base_health = self.tokenomics.calculate_network_utility().get('network_health_score', 50)

        sensitivities = {}

        # Test inflation rate sensitivity
        self.tokenomics.inflation_rate *= 1.1
        new_health = self.tokenomics.calculate_network_utility().get('network_health_score', 50)
        sensitivities['inflation_sensitivity'] = (new_health - base_health) / base_health
        self.tokenomics.inflation_rate /= 1.1  # Restore

        # Test staking reward sensitivity
        self.tokenomics.staking_reward_rate *= 1.1
        new_health = self.tokenomics.calculate_network_utility().get('network_health_score', 50)
        sensitivities['staking_sensitivity'] = (new_health - base_health) / base_health
        self.tokenomics.staking_reward_rate /= 1.1  # Restore

        return sensitivities

# Global calculator instance
calculator_instance = None

def get_network_utility_calculator() -> NetworkUtilityCalculator:
    """Get global network utility calculator instance"""
    global calculator_instance
    if calculator_instance is None:
        calculator_instance = NetworkUtilityCalculator()
    return calculator_instance

if __name__ == '__main__':
    # Demo
    calculator = get_network_utility_calculator()

    print("🧮 Network Utility Calculator Demo")
    print("=" * 50)

    # Register utility functions for sample agents
    calculator.register_utility_function("node_001", risk_aversion=0.3)
    calculator.register_utility_function("user_001", risk_aversion=0.7)

    print("✅ Utility functions registered")

    # Calculate network equilibrium
    equilibrium = calculator.calculate_network_equilibrium(GameTheoryModel.PRISONERS_DILEMMA)
    print(f"🎯 Network Equilibrium: {equilibrium['cooperation_index']:.2f} cooperation index")

    # Simulate network evolution
    evolution = calculator.simulate_network_evolution(steps=20)
    final_coop = evolution['time_series'][-1]['cooperation_index']
    print(f"🔄 Network Evolution: Final cooperation = {final_coop:.2f}")

    # Calculate optimal parameters
    optimal_params = calculator.calculate_optimal_network_parameters()
    print(f"⚙️ Optimal Parameters: Inflation = {optimal_params['optimal_parameters']['inflation_rate']:.3f}")

    print("🎉 Network Utility Calculator Demo completed!")