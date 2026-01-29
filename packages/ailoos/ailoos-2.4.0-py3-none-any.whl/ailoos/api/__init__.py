"""
AILOOS APIs - Interfaces REST para el sistema completo.
Incluye marketplace, federated learning, gestión de nodos y wallets blockchain.
"""

import os

from .settings_api import SettingsAPI, create_settings_app, settings_api

MarketplaceAPI = None
create_marketplace_app = None
marketplace_api = None
FederatedAPI = None
create_federated_app = None
federated_api = None
WalletAPI = None
create_wallet_app = None
wallet_api = None
EmpoorioLMApi = None
EmpoorioLMAPI = None
create_empoorio_app = None
empoorio_lm_api = None
TechnicalDashboardAPI = None
create_technical_dashboard_app = None
technical_dashboard_api = None
RAGAPI = None
create_rag_app = None
rag_api = None
ModelsAPI = None
create_models_app = None
models_api = None
AnalyticsAPI = None
create_analytics_app = None
analytics_api = None
SystemToolsAPI = None
create_system_tools_app = None
system_tools_api = None
DataHubAPI = None
create_datahub_app = None
datahub_api = None

if os.getenv("AILOOS_API_IMPORT_ALL") == "1":
    try:
        from .marketplace_api import MarketplaceAPI, create_marketplace_app, marketplace_api
    except Exception:  # pragma: no cover - optional dependencies
        pass

    try:
        from .federated_api import FederatedAPI, create_federated_app, federated_api
    except Exception:  # pragma: no cover
        pass

    try:
        from .wallet_api import WalletAPI, create_wallet_app, wallet_api
    except Exception:  # pragma: no cover
        pass

    try:
        from .empoorio_api import EmpoorioLMApi, EmpoorioLMAPI, create_empoorio_app, empoorio_lm_api
    except Exception:  # pragma: no cover
        pass

    try:
        from .technical_dashboard_api import TechnicalDashboardAPI, create_technical_dashboard_app, technical_dashboard_api
    except Exception:  # pragma: no cover
        pass

    try:
        from .rag_api import RAGAPI, create_rag_app, rag_api
    except Exception:  # pragma: no cover
        pass

    try:
        from .models_api import ModelsAPI, create_models_app, models_api
    except Exception:  # pragma: no cover
        pass

    try:
        from .analytics_api import AnalyticsAPI, create_analytics_app, analytics_api
    except Exception:  # pragma: no cover
        pass

    try:
        from .system_tools_api import SystemToolsAPI, create_system_tools_app, system_tools_api
    except Exception:  # pragma: no cover
        pass

    try:
        from .datahub_api import DataHubAPI, create_datahub_app, datahub_api
    except Exception:  # pragma: no cover
        pass

__all__ = [
    'MarketplaceAPI',
    'FederatedAPI',
    'WalletAPI',
    'EmpoorioLMApi',
    'EmpoorioLMAPI',
    'TechnicalDashboardAPI',
    'ModelsAPI',
    'SettingsAPI',
    'create_marketplace_app',
    'create_federated_app',
    'create_wallet_app',
    'create_empoorio_app',
    'create_technical_dashboard_app',
    'create_rag_app',
    'create_models_app',
    'create_settings_app',
    'marketplace_api',
    'federated_api',
    'wallet_api',
    'empoorio_lm_api',
    'technical_dashboard_api',
    'models_api',
    'settings_api'
]
