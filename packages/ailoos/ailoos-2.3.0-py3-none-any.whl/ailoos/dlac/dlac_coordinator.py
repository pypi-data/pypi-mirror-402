#!/usr/bin/env python3
"""
DLAC Coordinator - Coordinador principal del sistema DLAC
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

from ..utils.logging import get_logger
from .data_integrity_monitor import DataIntegrityMonitor
from .loss_detection_engine import LossDetectionEngine, LossEvent
from .corruption_verifier import CorruptionVerifier, CorruptionReport
from .automatic_recovery import AutomaticRecovery
from .dlac_alert_system import DLACAlertSystem, AlertType, AlertSeverity
from .data_backup_manager import DataBackupManager

logger = get_logger(__name__)


@dataclass
class DLACSystemStatus:
    """Estado general del sistema DLAC."""
    is_active: bool = False
    components_status: Dict[str, bool] = field(default_factory=dict)
    last_health_check: Optional[datetime] = None
    active_monitors: int = 0
    pending_recoveries: int = 0
    active_alerts: int = 0
    total_backups: int = 0


class DLACCoordinator:
    """
    Coordinador principal del sistema DLAC.

    Integra todos los componentes DLAC y proporciona una interfaz unificada
    para monitoreo, detección y recuperación en entornos federados.
    """

    def __init__(self,
                 federated_coordinator: Optional[Any] = None,
                 ipfs_client: Optional[Any] = None,
                 alert_webhook: Optional[str] = None,
                 backup_directory: str = "./backups",
                 alert_callback: Optional[Callable] = None):
        """
        Inicializar coordinador DLAC.

        Args:
            federated_coordinator: Instancia del coordinador federado
            ipfs_client: Cliente IPFS para almacenamiento distribuido
            alert_webhook: URL de webhook para alertas
            backup_directory: Directorio para backups
        """
        self.federated_coordinator = federated_coordinator
        self.ipfs_client = ipfs_client

        # Componentes DLAC
        self.integrity_monitor = DataIntegrityMonitor()
        self.loss_detector = LossDetectionEngine()
        self.corruption_verifier = CorruptionVerifier()
        self.recovery_system = AutomaticRecovery(
            backup_manager=None,  # Se asignará después
            ipfs_client=ipfs_client
        )
        self.alert_system = DLACAlertSystem(
            discord_webhook=alert_webhook
        )
        self.backup_manager = DataBackupManager(
            backup_directory=backup_directory,
            ipfs_client=ipfs_client
        )

        # Configurar alert_callback si se proporciona
        if alert_callback:
            self.alert_system.alert_callback = alert_callback

        # Conectar componentes
        self.recovery_system.backup_manager = self.backup_manager

        # Estado del sistema
        self.status = DLACSystemStatus()
        self.is_running = False

        # Callbacks para integración
        self._setup_component_callbacks()

        logger.info("🎯 DLAC Coordinator initialized")

    def _setup_component_callbacks(self):
        """Configurar callbacks entre componentes."""
        # Alertas del monitor de integridad
        self.integrity_monitor.alert_callback = self._handle_integrity_alert

        # Alertas del detector de pérdida
        self.loss_detector.alert_callback = self._handle_loss_alert

        # Alertas del verificador de corrupción
        self.corruption_verifier.alert_callback = self._handle_corruption_alert

        # Alertas del sistema de recuperación
        self.recovery_system.alert_callback = self._handle_recovery_alert

    def _handle_integrity_alert(self, alert_type: str, alert_data: Dict[str, Any]):
        """Manejar alertas del monitor de integridad."""
        severity_map = {
            'integrity_failure': AlertSeverity.HIGH
        }

        severity = severity_map.get(alert_type, AlertSeverity.MEDIUM)

        self.alert_system.trigger_alert(
            alert_type=AlertType.INTEGRITY_FAILURE,
            severity=severity,
            title="Data Integrity Failure",
            message=f"Data integrity check failed: {alert_data.get('data_id', 'unknown')}",
            source_component="integrity_monitor",
            affected_data=[alert_data.get('data_id')],
            affected_nodes=[alert_data.get('node_id')],
            metadata=alert_data
        )

    def _handle_loss_alert(self, alert_type: str, alert_data: Dict[str, Any]):
        """Manejar alertas del detector de pérdida."""
        severity_map = {
            'loss_detected': AlertSeverity.CRITICAL,
            'cross_node_inconsistency': AlertSeverity.HIGH
        }

        severity = severity_map.get(alert_type, AlertSeverity.MEDIUM)

        alert_type_map = {
            'loss_detected': AlertType.LOSS_DETECTED,
            'cross_node_inconsistency': AlertType.CROSS_NODE_INCONSISTENCY
        }

        mapped_type = alert_type_map.get(alert_type, AlertType.LOSS_DETECTED)

        self.alert_system.trigger_alert(
            alert_type=mapped_type,
            severity=severity,
            title="Data Loss Detected",
            message=alert_data.get('description', 'Data loss event detected'),
            source_component="loss_detector",
            affected_data=alert_data.get('affected_data', []),
            affected_nodes=alert_data.get('affected_nodes', []),
            metadata=alert_data
        )

    def _handle_corruption_alert(self, alert_type: str, alert_data: Dict[str, Any]):
        """Manejar alertas del verificador de corrupción."""
        severity_map = {
            'corruption_detected': AlertSeverity.CRITICAL
        }

        severity = severity_map.get(alert_type, AlertSeverity.HIGH)

        self.alert_system.trigger_alert(
            alert_type=AlertType.CORRUPTION_DETECTED,
            severity=severity,
            title="Data Corruption Detected",
            message=f"Data corruption detected: {alert_data.get('data_id', 'unknown')}",
            source_component="corruption_verifier",
            affected_data=[alert_data.get('data_id')],
            metadata=alert_data
        )

    def _handle_recovery_alert(self, alert_type: str, alert_data: Dict[str, Any]):
        """Manejar alertas del sistema de recuperación."""
        severity_map = {
            'recovery_failed': AlertSeverity.HIGH,
            'recovery_started': AlertSeverity.MEDIUM,
            'recovery_success': AlertSeverity.LOW
        }

        severity = severity_map.get(alert_type, AlertSeverity.MEDIUM)

        alert_type_map = {
            'recovery_started': AlertType.RECOVERY_STARTED,
            'recovery_success': AlertType.RECOVERY_SUCCESS,
            'recovery_failed': AlertType.RECOVERY_FAILED
        }

        mapped_type = alert_type_map.get(alert_type, AlertType.RECOVERY_STARTED)

        self.alert_system.trigger_alert(
            alert_type=mapped_type,
            severity=severity,
            title=f"Recovery {alert_type.split('_')[1].title()}",
            message=f"Recovery operation {alert_type}: {alert_data.get('data_id', 'unknown')}",
            source_component="recovery_system",
            affected_data=[alert_data.get('data_id')],
            metadata=alert_data
        )

    async def start_dlac_system(self):
        """Iniciar el sistema DLAC completo."""
        if self.is_running:
            logger.warning("⚠️ DLAC system already running")
            return

        try:
            logger.info("🚀 Starting DLAC system...")

            # Iniciar componentes
            self.integrity_monitor.start_monitoring()
            self.loss_detector.start_detection()
            self.alert_system.start_alert_system()
            self.backup_manager.start_backup_manager()
            await self.recovery_system.start_recovery_system()

            # Registrar nodos del sistema federado
            if self.federated_coordinator:
                await self._register_federated_nodes()

            self.is_running = True
            self.status.is_active = True
            self._update_system_status()

            logger.info("✅ DLAC system started successfully")

        except Exception as e:
            logger.error(f"❌ Failed to start DLAC system: {e}")
            raise

    async def stop_dlac_system(self):
        """Detener el sistema DLAC completo."""
        if not self.is_running:
            return

        try:
            logger.info("🛑 Stopping DLAC system...")

            # Detener componentes
            self.integrity_monitor.stop_monitoring()
            self.loss_detector.stop_detection()
            self.alert_system.stop_alert_system()
            self.backup_manager.stop_backup_manager()
            await self.recovery_system.stop_recovery_system()

            self.is_running = False
            self.status.is_active = False

            logger.info("✅ DLAC system stopped")

        except Exception as e:
            logger.error(f"❌ Error stopping DLAC system: {e}")

    async def register_data_for_monitoring(self, data_id: str, data: Any,
                                         node_id: str, data_type: str = 'unknown',
                                         enable_backup: bool = True):
        """
        Registrar datos para monitoreo completo DLAC.

        Args:
            data_id: ID único de los datos
            data: Los datos a monitorear
            node_id: ID del nodo que contiene los datos
            data_type: Tipo de datos
            enable_backup: Si crear backup automático
        """
        try:
            # Registrar en monitor de integridad
            success = self.integrity_monitor.register_data(
                data_id=data_id,
                data=data,
                node_id=node_id,
                data_type=data_type
            )

            if not success:
                logger.error(f"❌ Failed to register data {data_id} for integrity monitoring")
                return False

            # Registrar en verificador de corrupción
            success = self.corruption_verifier.register_data(
                data_id=data_id,
                data=data
            )

            if not success:
                logger.error(f"❌ Failed to register data {data_id} for corruption verification")
                return False

            # Registrar nodo en detector de pérdida
            self.loss_detector.register_node(node_id, expected_data=[data_id])

            # Crear backup si está habilitado
            if enable_backup:
                await self.backup_manager.create_backup(
                    data_id=data_id,
                    data=data,
                    metadata={'node_id': node_id, 'data_type': data_type}
                )

                # Crear política de backup
                from .data_backup_manager import BackupType
                self.backup_manager.create_backup_policy(
                    data_id=data_id,
                    backup_type=BackupType.FULL
                )

            logger.info(f"📝 Data {data_id} registered for complete DLAC monitoring")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to register data {data_id} for DLAC monitoring: {e}")
            return False

    async def check_data_integrity(self, data_id: str, current_data: Any, node_id: str) -> Dict[str, Any]:
        """
        Verificar integridad completa de datos.

        Args:
            data_id: ID de los datos
            current_data: Datos actuales
            node_id: ID del nodo

        Returns:
            Resultado de verificación
        """
        results = {
            'data_id': data_id,
            'node_id': node_id,
            'integrity_check': None,
            'corruption_check': None,
            'overall_status': 'unknown',
            'issues': [],
            'recommendations': []
        }

        try:
            # Verificación de integridad
            integrity_result = self.integrity_monitor.check_integrity(data_id, current_data, node_id)
            results['integrity_check'] = {
                'is_ok': integrity_result.is_integrity_ok,
                'issues': integrity_result.issues
            }

            # Verificación de corrupción
            corruption_ok, corruption_report = self.corruption_verifier.verify_integrity(
                data_id, current_data
            )
            results['corruption_check'] = {
                'is_ok': corruption_ok,
                'report': corruption_report.__dict__ if corruption_report else None
            }

            # Determinar estado general
            integrity_ok = integrity_result.is_integrity_ok
            corruption_ok = corruption_ok

            if integrity_ok and corruption_ok:
                results['overall_status'] = 'healthy'
            elif not integrity_ok and corruption_ok:
                results['overall_status'] = 'integrity_issue'
                results['issues'].extend(integrity_result.issues)
                results['recommendations'].append("Check data source and update integrity records")
            elif integrity_ok and not corruption_ok:
                results['overall_status'] = 'corruption_detected'
                if corruption_report:
                    results['issues'].append(f"Corruption: {corruption_report.corruption_type.value}")
                    results['recommendations'].extend(corruption_report.recovery_suggestions)
            else:
                results['overall_status'] = 'critical'
                results['issues'].extend(integrity_result.issues)
                if corruption_report:
                    results['issues'].append(f"Corruption: {corruption_report.corruption_type.value}")
                    results['recommendations'].extend(corruption_report.recovery_suggestions)

                # Iniciar recuperación automática
                recovery_id = self.recovery_system.submit_recovery_task(
                    data_id=data_id,
                    corruption_report=corruption_report.__dict__ if corruption_report else None
                )
                results['recovery_task_id'] = recovery_id
                results['recommendations'].append(f"Automatic recovery initiated: {recovery_id}")

            return results

        except Exception as e:
            logger.error(f"❌ Integrity check failed for {data_id}: {e}")
            results['overall_status'] = 'error'
            results['issues'].append(str(e))
            return results

    async def handle_node_heartbeat(self, node_id: str, data_status: Dict[str, Any]):
        """
        Manejar heartbeat de nodo con información de datos.

        Args:
            node_id: ID del nodo
            data_status: Estado de los datos en el nodo
        """
        try:
            # Actualizar detector de pérdida
            self.loss_detector.update_heartbeat(node_id, data_status.get('data_availability', {}))

            # Verificar integridad de datos reportados
            for data_id, is_available in data_status.get('data_availability', {}).items():
                if is_available:
                    # Aquí podríamos verificar integridad si tenemos los datos actuales
                    # Por ahora, solo registramos la disponibilidad
                    pass

            logger.debug(f"💓 Processed heartbeat from node {node_id}")

        except Exception as e:
            logger.error(f"❌ Error processing heartbeat from {node_id}: {e}")

    async def _register_federated_nodes(self):
        """Registrar nodos del sistema federado para monitoreo."""
        if not self.federated_coordinator:
            return

        try:
            # Obtener información de nodos del coordinador federado
            # Esto depende de la API específica del coordinador
            federated_nodes = getattr(self.federated_coordinator, 'node_registry', {})

            for node_id in federated_nodes.keys():
                self.loss_detector.register_node(node_id)

            logger.info(f"📝 Registered {len(federated_nodes)} federated nodes for DLAC monitoring")

        except Exception as e:
            logger.error(f"❌ Failed to register federated nodes: {e}")

    def _update_system_status(self):
        """Actualizar estado del sistema DLAC."""
        self.status.components_status = {
            'integrity_monitor': self.integrity_monitor.is_monitoring,
            'loss_detector': self.loss_detector.is_detecting,
            'corruption_verifier': True,  # Siempre activo
            'recovery_system': self.recovery_system.is_running,
            'alert_system': self.alert_system.is_running,
            'backup_manager': self.backup_manager.is_running
        }

        self.status.last_health_check = datetime.now()
        self.status.active_monitors = sum(self.status.components_status.values())
        self.status.pending_recoveries = len(self.recovery_system.active_tasks)
        self.status.active_alerts = len([a for a in self.alert_system.active_alerts.values()
                                       if not a.resolved])
        self.status.total_backups = len(self.backup_manager.backups)

    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado completo del sistema DLAC."""
        self._update_system_status()

        return {
            'is_active': self.status.is_active,
            'is_running': self.is_running,
            'components_status': self.status.components_status,
            'last_health_check': self.status.last_health_check.isoformat() if self.status.last_health_check else None,
            'active_monitors': self.status.active_monitors,
            'pending_recoveries': self.status.pending_recoveries,
            'active_alerts': self.status.active_alerts,
            'total_backups': self.status.total_backups,
            'integridad_stats': self.integrity_monitor.get_monitor_stats(),
            'loss_stats': self.loss_detector.get_detection_stats(),
            'corruption_stats': self.corruption_verifier.get_global_stats(),
            'recovery_stats': self.recovery_system.get_recovery_stats(),
            'alert_stats': self.alert_system.get_alert_stats(),
            'backup_stats': self.backup_manager.get_backup_stats()
        }

    async def perform_system_health_check(self) -> Dict[str, Any]:
        """
        Realizar verificación de salud completa del sistema DLAC.

        Returns:
            Resultado de la verificación de salud
        """
        health_check = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'component_health': {},
            'issues': [],
            'recommendations': []
        }

        try:
            # Verificar componentes
            components_to_check = [
                ('integrity_monitor', self.integrity_monitor),
                ('loss_detector', self.loss_detector),
                ('corruption_verifier', self.corruption_verifier),
                ('recovery_system', self.recovery_system),
                ('alert_system', self.alert_system),
                ('backup_manager', self.backup_manager)
            ]

            for component_name, component in components_to_check:
                try:
                    # Verificar si el componente está operativo
                    if hasattr(component, 'is_monitoring'):
                        is_healthy = component.is_monitoring
                    elif hasattr(component, 'is_detecting'):
                        is_healthy = component.is_detecting
                    elif hasattr(component, 'is_running'):
                        is_healthy = component.is_running
                    else:
                        is_healthy = True  # Asumir saludable si no hay indicador

                    health_check['component_health'][component_name] = {
                        'status': 'healthy' if is_healthy else 'unhealthy',
                        'details': f"Component is {'active' if is_healthy else 'inactive'}"
                    }

                    if not is_healthy:
                        health_check['issues'].append(f"{component_name} is not active")
                        health_check['overall_status'] = 'degraded'

                except Exception as e:
                    health_check['component_health'][component_name] = {
                        'status': 'error',
                        'details': str(e)
                    }
                    health_check['issues'].append(f"{component_name} health check failed: {e}")
                    health_check['overall_status'] = 'unhealthy'

            # Verificar alertas activas críticas
            critical_alerts = [a for a in self.alert_system.active_alerts.values()
                             if a.severity == AlertSeverity.CRITICAL and not a.acknowledged]

            if critical_alerts:
                health_check['issues'].append(f"{len(critical_alerts)} critical alerts unacknowledged")
                health_check['overall_status'] = 'critical'
                health_check['recommendations'].append("Review and acknowledge critical alerts")

            # Verificar backups recientes
            recent_backups = sum(1 for b in self.backup_manager.backups.values()
                               if (datetime.now() - b.created_at).days < 1)

            if recent_backups == 0:
                health_check['issues'].append("No recent backups found")
                health_check['recommendations'].append("Ensure backup policies are active")

            logger.info(f"🏥 DLAC health check completed: {health_check['overall_status']}")

        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            health_check['overall_status'] = 'error'
            health_check['issues'].append(f"Health check system error: {e}")

        return health_check