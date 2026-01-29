"""
DLAC - Data Loss and Corruption Advanced System
Sistema avanzado de detección y prevención de pérdida y corrupción de datos para AILOOS.

Este módulo proporciona componentes integrales para:
- Monitoreo continuo de integridad de datos
- Detección de pérdida de datos en entornos P2P
- Verificación de corrupción con checksums avanzados
- Recuperación automática de datos perdidos/corruptos
- Sistema de alertas y notificaciones
- Gestión de backups y redundancia

Diseñado para entornos federados con alta disponibilidad y escalabilidad.
"""

from .data_integrity_monitor import DataIntegrityMonitor
from .loss_detection_engine import LossDetectionEngine
from .corruption_verifier import CorruptionVerifier
from .automatic_recovery import AutomaticRecovery
from .dlac_alert_system import DLACAlertSystem
from .data_backup_manager import DataBackupManager
from .dlac_coordinator import DLACCoordinator

__version__ = "1.0.0"
__author__ = "AILOOS Team"
__description__ = "Advanced Data Loss and Corruption prevention system for federated environments"

__all__ = [
    "DataIntegrityMonitor",
    "LossDetectionEngine",
    "CorruptionVerifier",
    "AutomaticRecovery",
    "DLACAlertSystem",
    "DataBackupManager",
    "DLACCoordinator"
]