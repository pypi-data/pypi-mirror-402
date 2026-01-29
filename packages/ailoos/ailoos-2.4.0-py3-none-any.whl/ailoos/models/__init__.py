"""
Models Package
Modelos de IA para Ailoos - incluyendo EmpoorioLM.
"""

# Import MoE components (available)
from .empoorio_lm import (
    MoEConfig,
    MoEExpert,
    NoisyTopKRouter,
    MoELayer,
    StaticMoERouter,
    compute_moe_loss,
    get_moe_statistics
)

# TODO: Implement EmpoorioLM and EmpoorioLMConfig
# from .empoorio_lm import EmpoorioLM, EmpoorioLMConfig

__all__ = [
    # MoE components
    'MoEConfig',
    'MoEExpert',
    'NoisyTopKRouter',
    'MoELayer',
    'StaticMoERouter',
    'compute_moe_loss',
    'get_moe_statistics'

    # TODO: Add when implemented
    # 'EmpoorioLM',
    # 'EmpoorioLMConfig'
]