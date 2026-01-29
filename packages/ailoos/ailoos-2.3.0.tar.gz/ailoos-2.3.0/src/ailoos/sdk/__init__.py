"""
AILOOS Federated Learning SDK
SDK completo para nodos federados en AILOOS.

Este SDK proporciona todas las herramientas necesarias para que los nodos
participen en el sistema federado de AILOOS, incluyendo:

- Autenticación JWT para nodos
- Gestión de modelos (subida/descarga)
- Participación en sesiones federadas
- Comunicación P2P integrada
- Integración con marketplace DRACMA
- Utilidades de hardware y monitoring

Ejemplo básico de uso:

    from ailoos.sdk import NodeSDK

    # Crear instancia del SDK
    sdk = NodeSDK(node_id='my_node_123', coordinator_url='http://coordinator:5001')

    # Inicializar
    await sdk.initialize()

    # Unirse a una sesión federada
    await sdk.join_federated_session('session_456')

    # Participar en rondas de entrenamiento
    await sdk.participate_in_round(model_weights=my_weights)
"""

import importlib

__version__ = "2.3.0"
_LAZY_EXPORTS = {
    "NodeSDK": (".node_sdk", "NodeSDK"),
    "FederatedClient": (".federated_client", "FederatedClient"),
    "ModelManager": (".model_manager", "ModelManager"),
    "NodeAuthenticator": (".auth", "NodeAuthenticator"),
    "P2PClient": (".p2p_client", "P2PClient"),
    "MarketplaceClient": (".marketplace_client", "MarketplaceClient"),
    "HardwareMonitor": (".hardware_monitor", "HardwareMonitor"),
    "circuit_breaker": (".utils", "circuit_breaker"),
    "retry": (".utils", "retry"),
    "rate_limit": (".utils", "rate_limit"),
    "log_execution_time": (".utils", "log_execution_time"),
    "validate_with_pydantic": (".utils", "validate_with_pydantic"),
    "log_structured": (".utils", "log_structured"),
    "create_structured_logger": (".utils", "create_structured_logger"),
    "gather_with_concurrency": (".utils", "gather_with_concurrency"),
    "cache_async": (".utils", "cache_async"),
    "CircuitBreakerOpenException": (".utils", "CircuitBreakerOpenException"),
    "RateLimitExceededException": (".utils", "RateLimitExceededException"),
}

__all__ = list(_LAZY_EXPORTS.keys())


def __getattr__(name: str):
    """Lazy-load SDK components to keep import overhead low."""
    if name in _LAZY_EXPORTS:
        module_name, attr_name = _LAZY_EXPORTS[name]
        module = importlib.import_module(module_name, __name__)
        value = getattr(module, attr_name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(list(globals().keys()) + list(_LAZY_EXPORTS.keys()))
