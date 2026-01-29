"""Configuracion de pytest para Ailoos."""

import warnings

warnings.filterwarnings(
    "ignore",
    message="websockets\\.legacy is deprecated.*",
    category=DeprecationWarning,
)
