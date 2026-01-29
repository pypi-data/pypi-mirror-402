"""
FEDERATED NUTRITION (DataHub) MODULE
===================================
Orquesta la ingesta de datos desde fuentes descentralizadas (IPFS) para
el entrenamiento de modelos (Federated Learning).

Implementa el patrón: "Source -> Refinery -> Menu -> Feast -> Synapse"
"""

from .nutrition_client import NutritionClient, FederatedDiet

__all__ = ["NutritionClient", "FederatedDiet"]