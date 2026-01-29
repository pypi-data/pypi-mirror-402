"""
DracmaS rewards for Ailoos via EmpoorioChain bridge.
"""

from .dracma_calculator import (
    dracmaCalculator,
    NodeContribution,
    RewardCalculation,
    RewardPool
)
from .dracma_manager import DRACMA_Manager

# Instancias REALES globales - inicialización lazy para evitar errores de config
def get_dracma_calculator():
    """Get dracmaCalculator instance (lazy initialization)."""
    return dracmaCalculator()

# Para compatibilidad backward
dracma_calculator = None  # Se inicializa cuando se necesita

__all__ = [
    'dracmaCalculator',
    'DRACMA_Manager',
    'NodeContribution',
    'RewardCalculation',
    'RewardPool',
    'dracma_calculator'
]
