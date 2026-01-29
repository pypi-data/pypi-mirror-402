#!/usr/bin/env python3
"""
Memory Tokenomics - Legacy module.
Deshabilitado: el token canonico es DracmaS en EmpoorioChain.
"""

import asyncio
import math
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..core.logging import get_logger
from ..core.config import get_config

logger = get_logger(__name__)


class MemoryTokenType(Enum):
    """Tipos de tokens de memoria."""
    MEMORY_ACCESS = "memory_access"      # Token para acceso a memoria
    MEMORY_STAKE = "memory_stake"        # Token para staking de memoria
    MEMORY_YIELD = "memory_yield"        # Token para rendimiento de memoria
    MEMORY_GOVERNANCE = "memory_governance"  # Token para gobernanza de memoria


class EconomicModel(Enum):
    """Modelos económicos disponibles."""
    UTILITY_TOKEN = "utility_token"      # Modelo de token de utilidad
    SECURITY_TOKEN = "security_token"    # Modelo de token de seguridad
    YIELD_TOKEN = "yield_token"          # Modelo de token de rendimiento
    GOVERNANCE_TOKEN = "governance_token"  # Modelo de token de gobernanza


@dataclass
class MemoryTokenMetrics:
    """Métricas económicas de tokens de memoria."""
    token_type: MemoryTokenType
    circulating_supply: float
    total_supply: float
    market_cap: float
    price_per_token: float
    volume_24h: float
    staking_ratio: float
    yield_rate: float
    timestamp: datetime


@dataclass
class MemoryEconomicEvent:
    """Evento económico en el sistema de memoria."""
    event_type: str
    node_id: str
    token_amount: float
    token_type: MemoryTokenType
    economic_impact: float
    timestamp: datetime
    metadata: Dict[str, Any]


class MemoryTokenomicsEngine:
    """
    Motor de tokenomics para memoria distribuida.
    Gestiona la creación, distribución y economía de tokens de memoria.
    """

    def __init__(self, config=None):
        raise NotImplementedError(
            "MemoryTokenomicsEngine deshabilitado. "
            "Usa DracmaS/EmpoorioChain como unica fuente canonica."
        )
        self.config = config or get_config()
        self.logger = logger

        # Configuración económica
        self.base_memory_token_supply = self.config.get('base_memory_token_supply', 1000000)
        self.memory_token_inflation_rate = self.config.get('memory_token_inflation_rate', 0.02)  # 2% anual
        self.memory_staking_reward_rate = self.config.get('memory_staking_reward_rate', 0.08)  # 8% APY
        self.memory_yield_boost_max = self.config.get('memory_yield_boost_max', 2.0)  # 2x max boost

        # Estado económico
        self.memory_tokens: Dict[MemoryTokenType, MemoryTokenMetrics] = {}
        self.economic_events: List[MemoryEconomicEvent] = []
        self.memory_economy_stats: Dict[str, Any] = {
            'total_value_locked': 0.0,
            'total_memory_utilization': 0.0,
            'network_memory_capacity': 0.0,
            'active_memory_providers': 0,
            'memory_token_velocity': 0.0,
            'economic_stability_index': 1.0
        }

        # Modelos económicos por tipo de memoria
        self.economic_models: Dict[str, EconomicModel] = {
            'standard': EconomicModel.UTILITY_TOKEN,
            'premium': EconomicModel.SECURITY_TOKEN,
            'persistent': EconomicModel.YIELD_TOKEN,
            'secure': EconomicModel.GOVERNANCE_TOKEN
        }

        # Cache de precios y demanda
        self.price_oracles: Dict[str, float] = {}
        self.demand_indicators: Dict[str, float] = {}

        self._initialize_memory_tokens()
        logger.info("💰 Memory Tokenomics Engine initialized")

    def _initialize_memory_tokens(self):
        """Inicializar tokens de memoria para cada tipo."""
        for token_type in MemoryTokenType:
            initial_supply = self._calculate_initial_supply(token_type)
            initial_price = self._calculate_initial_price(token_type)

            self.memory_tokens[token_type] = MemoryTokenMetrics(
                token_type=token_type,
                circulating_supply=initial_supply * 0.1,  # 10% en circulación inicialmente
                total_supply=initial_supply,
                market_cap=initial_supply * 0.1 * initial_price,
                price_per_token=initial_price,
                volume_24h=0.0,
                staking_ratio=0.0,
                yield_rate=self._calculate_base_yield_rate(token_type),
                timestamp=datetime.now()
            )

    def _calculate_initial_supply(self, token_type: MemoryTokenType) -> float:
        """Calcular suministro inicial para un tipo de token."""
        base_supply = self.base_memory_token_supply

        multipliers = {
            MemoryTokenType.MEMORY_ACCESS: 1.0,
            MemoryTokenType.MEMORY_STAKE: 0.8,
            MemoryTokenType.MEMORY_YIELD: 0.6,
            MemoryTokenType.MEMORY_GOVERNANCE: 0.4
        }

        return base_supply * multipliers.get(token_type, 1.0)

    def _calculate_initial_price(self, token_type: MemoryTokenType) -> float:
        """Calcular precio inicial para un tipo de token."""
        base_price = 1.0  # 1 DRACMA base

        price_multipliers = {
            MemoryTokenType.MEMORY_ACCESS: 1.0,
            MemoryTokenType.MEMORY_STAKE: 1.2,
            MemoryTokenType.MEMORY_YIELD: 1.5,
            MemoryTokenType.MEMORY_GOVERNANCE: 2.0
        }

        return base_price * price_multipliers.get(token_type, 1.0)

    def _calculate_base_yield_rate(self, token_type: MemoryTokenType) -> float:
        """Calcular tasa de rendimiento base para un tipo de token."""
        base_rates = {
            MemoryTokenType.MEMORY_ACCESS: 0.02,    # 2% APY
            MemoryTokenType.MEMORY_STAKE: 0.08,     # 8% APY
            MemoryTokenType.MEMORY_YIELD: 0.12,     # 12% APY
            MemoryTokenType.MEMORY_GOVERNANCE: 0.06  # 6% APY
        }

        return base_rates.get(token_type, 0.05)

    async def mint_memory_tokens(self, node_id: str, memory_capacity_gb: float,
                               memory_type: str, duration_hours: int) -> Dict[str, Any]:
        """
        Mintear tokens de memoria basados en capacidad proporcionada.

        Args:
            node_id: ID del nodo proveedor de memoria
            memory_capacity_gb: Capacidad de memoria en GB
            memory_type: Tipo de memoria ('standard', 'premium', etc.)
            duration_hours: Duración del compromiso en horas

        Returns:
            Resultado del minting de tokens
        """
        try:
            # Determinar tipo de token basado en tipo de memoria
            token_type = self._get_token_type_for_memory(memory_type)
            economic_model = self.economic_models.get(memory_type, EconomicModel.UTILITY_TOKEN)

            # Calcular cantidad de tokens a mintear
            token_amount = self._calculate_memory_token_amount(
                memory_capacity_gb, memory_type, duration_hours
            )

            # Aplicar modelo económico específico
            adjusted_amount = self._apply_economic_model(
                token_amount, economic_model, memory_capacity_gb, duration_hours
            )

            # Actualizar métricas del token
            token_metrics = self.memory_tokens[token_type]
            token_metrics.circulating_supply += adjusted_amount
            token_metrics.market_cap = token_metrics.circulating_supply * token_metrics.price_per_token

            # Registrar evento económico
            event = MemoryEconomicEvent(
                event_type="token_mint",
                node_id=node_id,
                token_amount=adjusted_amount,
                token_type=token_type,
                economic_impact=adjusted_amount * token_metrics.price_per_token,
                timestamp=datetime.now(),
                metadata={
                    'memory_capacity_gb': memory_capacity_gb,
                    'memory_type': memory_type,
                    'duration_hours': duration_hours,
                    'economic_model': economic_model.value
                }
            )
            self.economic_events.append(event)

            # Actualizar estadísticas económicas
            self._update_economy_stats()

            self.logger.info(f"💰 Minted {adjusted_amount:.2f} {token_type.value} tokens for node {node_id} "
                           f"({memory_capacity_gb}GB {memory_type})")

            return {
                'success': True,
                'token_type': token_type.value,
                'token_amount': adjusted_amount,
                'economic_value': adjusted_amount * token_metrics.price_per_token,
                'minting_fee': self._calculate_minting_fee(adjusted_amount, token_type)
            }

        except Exception as e:
            self.logger.error(f"Error minting memory tokens for {node_id}: {e}")
            return {'success': False, 'error': str(e)}

    def _get_token_type_for_memory(self, memory_type: str) -> MemoryTokenType:
        """Determinar tipo de token basado en tipo de memoria."""
        type_mapping = {
            'standard': MemoryTokenType.MEMORY_ACCESS,
            'premium': MemoryTokenType.MEMORY_STAKE,
            'persistent': MemoryTokenType.MEMORY_YIELD,
            'secure': MemoryTokenType.MEMORY_GOVERNANCE
        }

        return type_mapping.get(memory_type, MemoryTokenType.MEMORY_ACCESS)
    def _calculate_memory_token_amount(self, capacity_gb: float, memory_type: str,
                                     duration_hours: int) -> float:
        """Calcular cantidad de tokens basada en capacidad y duración."""
        # Fórmula base: tokens = capacidad * duración * tipo_multiplier
        base_rate = 1.0  # 1 token por GB por hora base

        type_multipliers = {
            'standard': 1.0,
            'premium': 1.5,
            'persistent': 2.0,
            'secure': 3.0
        }

        multiplier = type_multipliers.get(memory_type, 1.0)
        duration_days = duration_hours / 24.0

        # Aplicar economía de escala (rendimientos decrecientes)
        scale_factor = min(capacity_gb / 100, 1.0)  # Capacidad normalizada a 100GB

        token_amount = capacity_gb * duration_days * base_rate * multiplier * (1 + scale_factor)

        return token_amount

    def _apply_economic_model(self, base_amount: float, model: EconomicModel,
                            capacity_gb: float, duration_hours: int) -> float:
        """Aplicar modelo económico específico para ajustar cantidad de tokens."""
        if model == EconomicModel.UTILITY_TOKEN:
            # Modelo de utilidad: basado en demanda actual
            demand_multiplier = self.demand_indicators.get('network_demand', 1.0)
            return base_amount * demand_multiplier

        elif model == EconomicModel.SECURITY_TOKEN:
            # Modelo de seguridad: incentiva estabilidad a largo plazo
            duration_bonus = min(duration_hours / (24 * 30), 2.0)  # Máximo 2x por mes
            return base_amount * (1 + duration_bonus)

        elif model == EconomicModel.YIELD_TOKEN:
            # Modelo de rendimiento: incentiva alta capacidad
            capacity_bonus = min(capacity_gb / 1000, 1.5)  # Máximo 1.5x por TB
            return base_amount * (1 + capacity_bonus)

        elif model == EconomicModel.GOVERNANCE_TOKEN:
            # Modelo de gobernanza: incentiva participación activa
            governance_multiplier = self._calculate_governance_multiplier()
            return base_amount * governance_multiplier

        return base_amount

    def _calculate_governance_multiplier(self) -> float:
        """Calcular multiplicador de gobernanza basado en participación."""
        # En una implementación real, esto se basaría en métricas de gobernanza
        base_multiplier = 1.2
        participation_bonus = min(self.memory_economy_stats.get('governance_participation', 0.5), 0.5)
        return base_multiplier + participation_bonus

    def _calculate_minting_fee(self, token_amount: float, token_type: MemoryTokenType) -> float:
        """Calcular tarifa de minting."""
        base_fee_rate = 0.001  # 0.1% base

        type_multipliers = {
            MemoryTokenType.MEMORY_ACCESS: 1.0,
            MemoryTokenType.MEMORY_STAKE: 1.2,
            MemoryTokenType.MEMORY_YIELD: 1.5,
            MemoryTokenType.MEMORY_GOVERNANCE: 2.0
        }

        fee_rate = base_fee_rate * type_multipliers.get(token_type, 1.0)
        return token_amount * fee_rate

    async def calculate_memory_yield(self, node_id: str, staked_tokens: float,
                                   token_type: MemoryTokenType, lock_period_days: int) -> Dict[str, Any]:
        """
        Calcular rendimiento de staking de tokens de memoria.

        Args:
            node_id: ID del nodo
            staked_tokens: Cantidad de tokens stakeados
            token_type: Tipo de token
            lock_period_days: Período de bloqueo en días

        Returns:
            Cálculo de rendimiento
        """
        try:
            token_metrics = self.memory_tokens[token_type]

            # Calcular tasa de rendimiento base
            base_apy = token_metrics.yield_rate

            # Aplicar bonus por período de bloqueo
            lock_bonus = min(lock_period_days / 365, 1.0)  # Máximo 100% bonus por año
            effective_apy = base_apy * (1 + lock_bonus)

            # Calcular rendimiento diario
            daily_yield_rate = effective_apy / 365
            daily_yield = staked_tokens * daily_yield_rate

            # Calcular rendimiento total por período
            total_yield = staked_tokens * effective_apy * (lock_period_days / 365)

            # Actualizar ratio de staking
            token_metrics.staking_ratio = self._calculate_staking_ratio(token_type)

            return {
                'success': True,
                'effective_apy': effective_apy,
                'daily_yield': daily_yield,
                'total_yield': total_yield,
                'lock_bonus': lock_bonus,
                'staking_ratio': token_metrics.staking_ratio
            }

        except Exception as e:
            self.logger.error(f"Error calculating memory yield for {node_id}: {e}")
            return {'success': False, 'error': str(e)}

    def _calculate_staking_ratio(self, token_type: MemoryTokenType) -> float:
        """Calcular ratio de staking para un tipo de token."""
        token_metrics = self.memory_tokens[token_type]

        # En una implementación real, esto se calcularía del estado de staking
        # Por ahora, simulamos basado en suministro circulante
        staking_ratio = min(token_metrics.circulating_supply * 0.3 / token_metrics.total_supply, 1.0)
        return staking_ratio

    async def update_memory_token_prices(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualizar precios de tokens de memoria basado en datos de mercado.

        Args:
            market_data: Datos del mercado (volumen, demanda, etc.)

        Returns:
            Resultado de la actualización de precios
        """
        try:
            updated_tokens = []

            for token_type, token_metrics in self.memory_tokens.items():
                # Calcular nuevo precio basado en oferta/demanda
                new_price = self._calculate_dynamic_price(token_type, market_data)

                # Aplicar suavizado para evitar volatilidad extrema
                price_change = (new_price - token_metrics.price_per_token) / token_metrics.price_per_token
                max_change = 0.1  # Máximo 10% cambio por actualización

                if abs(price_change) > max_change:
                    new_price = token_metrics.price_per_token * (1 + max_change * (1 if price_change > 0 else -1))

                # Actualizar métricas
                old_market_cap = token_metrics.market_cap
                token_metrics.price_per_token = new_price
                token_metrics.market_cap = token_metrics.circulating_supply * new_price
                token_metrics.volume_24h = market_data.get(f'{token_type.value}_volume', 0.0)
                token_metrics.timestamp = datetime.now()

                # Calcular impacto económico
                market_cap_change = token_metrics.market_cap - old_market_cap

                updated_tokens.append({
                    'token_type': token_type.value,
                    'old_price': token_metrics.price_per_token,
                    'new_price': new_price,
                    'price_change_percent': price_change * 100,
                    'market_cap_change': market_cap_change
                })

            # Actualizar estadísticas económicas
            self._update_economy_stats()

            self.logger.info(f"💹 Updated prices for {len(updated_tokens)} memory tokens")

            return {
                'success': True,
                'updated_tokens': updated_tokens,
                'economic_stability_index': self.memory_economy_stats['economic_stability_index']
            }

        except Exception as e:
            self.logger.error(f"Error updating memory token prices: {e}")
            return {'success': False, 'error': str(e)}

    def _calculate_dynamic_price(self, token_type: MemoryTokenType, market_data: Dict[str, Any]) -> float:
        """Calcular precio dinámico basado en factores de mercado."""
        token_metrics = self.memory_tokens[token_type]

        # Factores de precio
        base_price = self._calculate_initial_price(token_type)

        # Factor de oferta/demanda
        supply_demand_ratio = market_data.get('supply_demand_ratio', 1.0)
        supply_factor = 1.0 / (1.0 + math.exp(supply_demand_ratio - 1.0))  # Función sigmoide

        # Factor de utilidad de red
        network_utility = market_data.get('network_memory_utilization', 0.5)
        utility_factor = 0.8 + (network_utility * 0.4)  # 0.8-1.2 rango

        # Factor de staking
        staking_factor = 1.0 + (token_metrics.staking_ratio * 0.2)  # Hasta 20% bonus

        # Factor de volumen
        volume_factor = 1.0
        if token_metrics.volume_24h > 0:
            avg_volume = token_metrics.market_cap * 0.01  # 1% del market cap como volumen base
            volume_factor = min(token_metrics.volume_24h / avg_volume, 2.0)

        # Calcular precio final
        dynamic_price = base_price * supply_factor * utility_factor * staking_factor * volume_factor

        return dynamic_price

    def _update_economy_stats(self):
        """Actualizar estadísticas económicas globales."""
        try:
            # Calcular TVL (Total Value Locked)
            total_tvl = sum(
                token.market_cap * token.staking_ratio
                for token in self.memory_tokens.values()
            )

            # Calcular utilización de memoria de red
            memory_utilization = self.demand_indicators.get('network_utilization', 0.0)

            # Calcular capacidad total de memoria
            network_capacity = self.demand_indicators.get('total_capacity_gb', 1000.0)

            # Calcular velocidad de token (volumen / market cap)
            total_volume = sum(token.volume_24h for token in self.memory_tokens.values())
            total_market_cap = sum(token.market_cap for token in self.memory_tokens.values())
            token_velocity = total_volume / max(total_market_cap, 1.0)

            # Calcular índice de estabilidad económica
            price_volatility = self._calculate_price_volatility()
            stability_index = 1.0 / (1.0 + price_volatility)

            self.memory_economy_stats.update({
                'total_value_locked': total_tvl,
                'total_memory_utilization': memory_utilization,
                'network_memory_capacity': network_capacity,
                'memory_token_velocity': token_velocity,
                'economic_stability_index': stability_index,
                'last_updated': datetime.now().isoformat()
            })

        except Exception as e:
            self.logger.error(f"Error updating economy stats: {e}")

    def _calculate_price_volatility(self) -> float:
        """Calcular volatilidad de precios de tokens de memoria."""
        try:
            if len(self.economic_events) < 2:
                return 0.0

            # Calcular cambios de precio recientes
            recent_events = [e for e in self.economic_events[-100:]  # Últimos 100 eventos
                           if e.event_type == 'price_update']

            if len(recent_events) < 2:
                return 0.0

            price_changes = []
            for i in range(1, len(recent_events)):
                if 'old_price' in recent_events[i].metadata and 'new_price' in recent_events[i].metadata:
                    change = abs(recent_events[i].metadata['new_price'] - recent_events[i].metadata['old_price'])
                    change_pct = change / recent_events[i].metadata['old_price']
                    price_changes.append(change_pct)

            if not price_changes:
                return 0.0

            # Calcular volatilidad como desviación estándar de cambios porcentuales
            mean_change = sum(price_changes) / len(price_changes)
            variance = sum((x - mean_change) ** 2 for x in price_changes) / len(price_changes)
            volatility = math.sqrt(variance)

            return volatility

        except Exception:
            return 0.0

    def get_memory_economy_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas económicas de memoria.

        Returns:
            Estadísticas económicas completas
        """
        try:
            token_stats = {}
            for token_type, metrics in self.memory_tokens.items():
                token_stats[token_type.value] = {
                    'circulating_supply': metrics.circulating_supply,
                    'total_supply': metrics.total_supply,
                    'market_cap': metrics.market_cap,
                    'price_per_token': metrics.price_per_token,
                    'volume_24h': metrics.volume_24h,
                    'staking_ratio': metrics.staking_ratio,
                    'yield_rate': metrics.yield_rate,
                    'last_updated': metrics.timestamp.isoformat()
                }

            return {
                'token_stats': token_stats,
                'economy_stats': self.memory_economy_stats,
                'recent_events': [
                    {
                        'event_type': event.event_type,
                        'node_id': event.node_id,
                        'token_amount': event.token_amount,
                        'token_type': event.token_type.value,
                        'economic_impact': event.economic_impact,
                        'timestamp': event.timestamp.isoformat()
                    }
                    for event in self.economic_events[-50:]  # Últimos 50 eventos
                ],
                'price_oracles': self.price_oracles,
                'demand_indicators': self.demand_indicators
            }

        except Exception as e:
            self.logger.error(f"Error getting memory economy stats: {e}")
            return {'error': str(e)}

    async def simulate_memory_economic_event(self, event_type: str,
                                           parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simular evento económico en el sistema de memoria.

        Args:
            event_type: Tipo de evento ('supply_shock', 'demand_spike', etc.)
            parameters: Parámetros del evento

        Returns:
            Resultado de la simulación
        """
        try:
            if event_type == 'supply_shock':
                # Simular aumento/disminución de suministro
                supply_change = parameters.get('supply_change_pct', 0.1)
                affected_token = parameters.get('token_type', 'memory_access')

                token_metrics = self.memory_tokens[MemoryTokenType(affected_token)]
                old_supply = token_metrics.circulating_supply
                new_supply = old_supply * (1 + supply_change)

                # Calcular impacto en precio (ley de oferta/demanda simple)
                price_impact = -supply_change * 0.5  # 50% passthrough
                new_price = token_metrics.price_per_token * (1 + price_impact)

                token_metrics.circulating_supply = new_supply
                token_metrics.price_per_token = new_price
                token_metrics.market_cap = new_supply * new_price

            elif event_type == 'demand_spike':
                # Simular aumento de demanda
                demand_multiplier = parameters.get('demand_multiplier', 1.5)

                for token_metrics in self.memory_tokens.values():
                    # Aumento de precio por demanda
                    new_price = token_metrics.price_per_token * demand_multiplier
                    token_metrics.price_per_token = new_price
                    token_metrics.market_cap = token_metrics.circulating_supply * new_price
                    token_metrics.volume_24h *= demand_multiplier

            # Registrar evento
            event = MemoryEconomicEvent(
                event_type=f"simulated_{event_type}",
                node_id="system",
                token_amount=0.0,
                token_type=MemoryTokenType.MEMORY_ACCESS,
                economic_impact=parameters.get('economic_impact', 0.0),
                timestamp=datetime.now(),
                metadata=parameters
            )
            self.economic_events.append(event)

            self._update_economy_stats()

            return {
                'success': True,
                'event_type': event_type,
                'simulated_impact': parameters.get('economic_impact', 0.0),
                'affected_tokens': list(self.memory_tokens.keys())
            }

        except Exception as e:
            self.logger.error(f"Error simulating economic event {event_type}: {e}")
            return {'success': False, 'error': str(e)}


# Funciones de conveniencia
def create_memory_tokenomics_engine(config=None) -> MemoryTokenomicsEngine:
    """Crear una nueva instancia del motor de tokenomics de memoria."""
    raise NotImplementedError(
        "MemoryTokenomicsEngine deshabilitado. "
        "Usa DracmaS/EmpoorioChain como unica fuente canonica."
    )


async def calculate_optimal_memory_token_allocation(memory_capacity_gb: float,
                                                  memory_type: str,
                                                  market_conditions: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcular asignación óptima de tokens de memoria basada en condiciones de mercado.

    Args:
        memory_capacity_gb: Capacidad de memoria
        memory_type: Tipo de memoria
        market_conditions: Condiciones actuales del mercado

    Returns:
        Recomendación de asignación óptima
    """
    try:
        raise NotImplementedError(
            "Memory tokenomics deshabilitado. "
            "Usa DracmaS/EmpoorioChain como unica fuente canonica."
        )
        # Lógica de optimización basada en mercado
        base_allocation = memory_capacity_gb * 10  # 10 tokens por GB base

        # Ajustes por condiciones de mercado
        demand_multiplier = market_conditions.get('demand_multiplier', 1.0)
        supply_pressure = market_conditions.get('supply_pressure', 1.0)
        yield_opportunity = market_conditions.get('yield_opportunity', 0.08)

        optimal_allocation = base_allocation * demand_multiplier / supply_pressure

        # Calcular rendimiento esperado
        expected_yield = optimal_allocation * yield_opportunity

        return {
            'optimal_allocation': optimal_allocation,
            'expected_yield': expected_yield,
            'confidence_score': min(demand_multiplier / supply_pressure, 1.0),
            'recommendation': 'increase' if demand_multiplier > supply_pressure else 'decrease'
        }

    except Exception:
        return {
            'optimal_allocation': memory_capacity_gb * 10,
            'expected_yield': 0.0,
            'confidence_score': 0.5,
            'recommendation': 'hold'}
