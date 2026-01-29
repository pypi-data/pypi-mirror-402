"""
Rollback Coordinator - Sistema automático de rollback
Coordinación de rollbacks automáticos con monitoreo continuo y recuperación de fallos.
"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from ..core.logging import get_logger
from .federated_version_manager import FederatedVersionManager, ModelVersion, VersionStatus
from .ipfs_version_distributor import IPFSVersionDistributor, DistributionStrategy
from ..monitoring.monitoring_system import UnifiedMonitoringSystem
from ..monitoring.validation_engine import ValidationEngine
from ..monitoring.security_dashboard import SecurityDashboard

logger = get_logger(__name__)


class RollbackTrigger(Enum):
    """Triggers que pueden iniciar un rollback."""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    HIGH_ERROR_RATE = "high_error_rate"
    SECURITY_VULNERABILITY = "security_vulnerability"
    VALIDATION_FAILURE = "validation_failure"
    MANUAL_TRIGGER = "manual_trigger"
    SYSTEM_HEALTH_CHECK = "system_health_check"


class RollbackStatus(Enum):
    """Estados de rollback."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class RollbackPlan:
    """Plan de rollback detallado."""
    rollback_id: str
    from_version: str
    to_version: str
    trigger: RollbackTrigger
    reason: str
    affected_nodes: List[str]
    risk_assessment: Dict[str, Any]
    estimated_duration: int  # segundos
    created_at: int = field(default_factory=lambda: int(time.time()))
    approved_at: Optional[int] = None
    started_at: Optional[int] = None
    completed_at: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            'rollback_id': self.rollback_id,
            'from_version': self.from_version,
            'to_version': self.to_version,
            'trigger': self.trigger.value,
            'reason': self.reason,
            'affected_nodes': self.affected_nodes,
            'risk_assessment': self.risk_assessment,
            'estimated_duration': self.estimated_duration,
            'created_at': self.created_at,
            'approved_at': self.approved_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at
        }


@dataclass
class RollbackExecution:
    """Ejecución de un rollback."""
    plan: RollbackPlan
    status: RollbackStatus = RollbackStatus.PENDING
    progress: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    rollback_batches: List[List[str]] = field(default_factory=list)
    current_batch: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            'plan': self.plan.to_dict(),
            'status': self.status.value,
            'progress': self.progress,
            'errors': self.errors,
            'rollback_batches': self.rollback_batches,
            'current_batch': self.current_batch
        }


class RollbackCoordinator:
    """
    Coordinador de rollbacks automáticos.
    Monitorea el sistema y ejecuta rollbacks cuando es necesario.
    """

    def __init__(self, version_manager: FederatedVersionManager,
                 distributor: IPFSVersionDistributor,
                 auto_rollback_enabled: bool = True,
                 max_concurrent_rollbacks: int = 1,
                 monitoring_service: UnifiedMonitoringSystem = None,
                 validation_service: ValidationEngine = None,
                 security_service: SecurityDashboard = None):
        """
        Inicializar el coordinador de rollbacks.

        Args:
            version_manager: Gestor de versiones
            distributor: Distribuidor de versiones
            auto_rollback_enabled: Habilitar rollbacks automáticos
            max_concurrent_rollbacks: Máximo de rollbacks concurrentes
            monitoring_service: Servicio de monitoreo unificado
            validation_service: Motor de validación
            security_service: Dashboard de seguridad
        """
        self.version_manager = version_manager
        self.distributor = distributor
        self.auto_rollback_enabled = auto_rollback_enabled
        self.max_concurrent_rollbacks = max_concurrent_rollbacks
        self.monitoring_service = monitoring_service
        self.validation_service = validation_service
        self.security_service = security_service

        # Estado de rollbacks
        self.active_rollbacks: Dict[str, RollbackExecution] = {}
        self.rollback_history: List[RollbackExecution] = []
        self.rollback_queue: asyncio.Queue[RollbackPlan] = asyncio.Queue()

        # Configuración de triggers
        self.rollback_triggers: Dict[RollbackTrigger, Dict[str, Any]] = {
            RollbackTrigger.PERFORMANCE_DEGRADATION: {
                'enabled': True,
                'thresholds': {'accuracy_drop': 0.05, 'latency_increase': 50},  # 5% drop, 50ms increase
                'cooldown_minutes': 30
            },
            RollbackTrigger.HIGH_ERROR_RATE: {
                'enabled': True,
                'thresholds': {'error_rate': 0.1, 'min_samples': 100},  # 10% error rate
                'cooldown_minutes': 15
            },
            RollbackTrigger.SECURITY_VULNERABILITY: {
                'enabled': True,
                'thresholds': {},  # Triggers immediately
                'cooldown_minutes': 0
            },
            RollbackTrigger.VALIDATION_FAILURE: {
                'enabled': True,
                'thresholds': {'failure_rate': 0.3},  # 30% validation failure
                'cooldown_minutes': 10
            }
        }

        # Historial de triggers para cooldown
        self.trigger_history: Dict[RollbackTrigger, int] = {}

        # Callbacks
        self.rollback_callbacks: List[Callable] = []

        # Workers
        self.rollback_workers: List[asyncio.Task] = []
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_running = False

        # Locks
        self.rollback_lock = asyncio.Lock()

        logger.info("🚀 RollbackCoordinator initialized")

    async def start(self):
        """Iniciar el coordinador."""
        if self.is_running:
            return

        self.is_running = True

        # Iniciar workers de rollback
        self.rollback_workers = []
        for i in range(self.max_concurrent_rollbacks):
            task = asyncio.create_task(self._rollback_worker())
            self.rollback_workers.append(task)

        # Iniciar monitoreo continuo
        if self.auto_rollback_enabled:
            self.monitoring_task = asyncio.create_task(self._continuous_monitoring())

        logger.info(f"✅ RollbackCoordinator started with {self.max_concurrent_rollbacks} workers")

    async def stop(self):
        """Detener el coordinador."""
        if not self.is_running:
            return

        self.is_running = False

        # Cancelar tareas
        if self.monitoring_task:
            self.monitoring_task.cancel()

        for task in self.rollback_workers:
            task.cancel()

        # Esperar finalización
        tasks_to_wait = [t for t in [self.monitoring_task] + self.rollback_workers if t]
        if tasks_to_wait:
            await asyncio.gather(*tasks_to_wait, return_exceptions=True)

        logger.info("🛑 RollbackCoordinator stopped")

    async def trigger_rollback(self, from_version: str, to_version: str,
                             trigger: RollbackTrigger, reason: str,
                             affected_nodes: Optional[List[str]] = None) -> str:
        """
        Trigger manual de rollback.

        Args:
            from_version: Versión actual
            to_version: Versión objetivo
            trigger: Tipo de trigger
            reason: Razón del rollback
            affected_nodes: Nodos afectados (None = todos)

        Returns:
            ID del rollback
        """
        async with self.rollback_lock:
            try:
                # Verificar cooldown
                if not self._check_trigger_cooldown(trigger):
                    raise ValueError(f"Trigger {trigger.value} is in cooldown")

                # Validar versiones
                from_ver = await self.version_manager.get_version(from_version)
                to_ver = await self.version_manager.get_version(to_version)

                if not from_ver or not to_ver:
                    raise ValueError("Invalid version IDs")

                if from_ver.status != VersionStatus.ACTIVE:
                    raise ValueError(f"Version {from_version} is not active")

                # Determinar nodos afectados
                if affected_nodes is None:
                    # Obtener nodos que actualmente usan la versión from_version
                    affected_nodes = await self._get_nodes_using_version(from_version)

                # Crear plan de rollback
                rollback_id = f"rollback_{int(time.time())}_{from_version}_{to_version}"
                plan = RollbackPlan(
                    rollback_id=rollback_id,
                    from_version=from_version,
                    to_version=to_version,
                    trigger=trigger,
                    reason=reason,
                    affected_nodes=affected_nodes,
                    risk_assessment=await self._assess_rollback_risk(from_version, to_version, affected_nodes),
                    estimated_duration=self._estimate_rollback_duration(len(affected_nodes))
                )

                # Crear ejecución
                execution = RollbackExecution(plan=plan)
                self.active_rollbacks[rollback_id] = execution

                # Agregar a cola
                await self.rollback_queue.put(plan)

                # Registrar trigger
                self.trigger_history[trigger] = int(time.time())

                # Notificar
                await self._notify_rollback_event('rollback_triggered', rollback_id)

                logger.info(f"🚨 Rollback triggered: {from_version} -> {to_version} ({trigger.value})")
                return rollback_id

            except Exception as e:
                logger.error(f"❌ Failed to trigger rollback: {e}")
                raise

    async def _rollback_worker(self):
        """Worker que procesa rollbacks."""
        while self.is_running:
            try:
                # Obtener plan de rollback
                plan = await self.rollback_queue.get()

                try:
                    await self._execute_rollback(plan.rollback_id)
                except Exception as e:
                    logger.error(f"❌ Rollback execution failed for {plan.rollback_id}: {e}")
                    execution = self.active_rollbacks.get(plan.rollback_id)
                    if execution:
                        execution.status = RollbackStatus.FAILED
                        execution.errors.append(str(e))
                finally:
                    self.rollback_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Rollback worker error: {e}")

    async def _execute_rollback(self, rollback_id: str):
        """Ejecutar un rollback."""
        execution = self.active_rollbacks.get(rollback_id)
        if not execution:
            return

        execution.status = RollbackStatus.IN_PROGRESS
        execution.plan.started_at = int(time.time())

        logger.info(f"🔄 Starting rollback {rollback_id}: {execution.plan.from_version} -> {execution.plan.to_version}")

        try:
            # Crear batches para rollback gradual
            execution.rollback_batches = self._create_rollback_batches(
                execution.plan.affected_nodes,
                batch_size=10  # 10 nodos por batch
            )

            # Ejecutar rollback por batches
            total_batches = len(execution.rollback_batches)
            for i, batch in enumerate(execution.rollback_batches):
                execution.current_batch = i

                try:
                    await self._rollback_batch(execution.plan, batch)
                    execution.progress['completed_batches'] = i + 1
                    execution.progress['total_batches'] = total_batches
                    execution.progress['progress_percentage'] = ((i + 1) / total_batches) * 100

                    logger.info(f"📦 Rollback {rollback_id}: completed batch {i+1}/{total_batches}")

                    # Pequeña pausa entre batches
                    await asyncio.sleep(1)

                except Exception as e:
                    logger.error(f"❌ Rollback batch {i+1} failed: {e}")
                    execution.errors.append(f"Batch {i+1}: {str(e)}")

                    # Decidir si continuar o fallar completamente
                    if self._should_fail_on_batch_error():
                        raise

            # Completar rollback
            execution.status = RollbackStatus.COMPLETED
            execution.plan.completed_at = int(time.time())

            # Actualizar versión activa
            await self.version_manager.deprecate_version(
                execution.plan.from_version,
                reason=f"Rolled back to {execution.plan.to_version}: {execution.plan.reason}"
            )

            # Notificar completación
            await self._notify_rollback_event('rollback_completed', rollback_id)

            # Agregar a historial
            self.rollback_history.append(execution)

            logger.info(f"✅ Rollback {rollback_id} completed successfully")

        except Exception as e:
            execution.status = RollbackStatus.FAILED
            execution.errors.append(str(e))
            await self._notify_rollback_event('rollback_failed', rollback_id)
            raise

    async def _rollback_batch(self, plan: RollbackPlan, batch: List[str]):
        """Ejecutar rollback para un batch de nodos."""
        # Distribuir la versión anterior a los nodos del batch
        distribution_task = await self.distributor.distribute_version(
            version_id=plan.to_version,
            target_nodes=batch,
            strategy=DistributionStrategy.PRIORITY_BASED,
            priority=10  # Alta prioridad para rollbacks
        )

        # Esperar completación de la distribución
        timeout = plan.estimated_duration // len(plan.affected_nodes) * len(batch) + 60  # +60s buffer
        await self._wait_for_distribution(distribution_task, timeout)

        # Verificar que los nodos hayan recibido la versión
        # En producción, esto consultaría a cada nodo
        logger.debug(f"📦 Rollback batch distributed to {len(batch)} nodes")

    async def _wait_for_distribution(self, task_id: str, timeout_seconds: int):
        """Esperar a que una distribución se complete."""
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            status = await self.distributor.get_distribution_status(task_id)
            if status and status['status'] in ['completed', 'partial']:
                if status['status'] == 'partial':
                    logger.warning(f"⚠️ Distribution {task_id} completed partially")
                return
            elif status and status['status'] == 'failed':
                raise Exception(f"Distribution {task_id} failed")

            await asyncio.sleep(5)

        raise Exception(f"Distribution {task_id} timed out after {timeout_seconds}s")

    async def _continuous_monitoring(self):
        """Monitoreo continuo para detectar triggers de rollback."""
        logger.info("👀 Starting continuous rollback monitoring")

        while self.is_running:
            try:
                await self._check_system_health()
                await asyncio.sleep(60)  # Verificar cada minuto

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                await asyncio.sleep(30)  # Esperar antes de reintentar

    async def _check_system_health(self):
        """Verificar salud del sistema y detectar triggers."""
        try:
            # Obtener versión activa
            active_version = await self.version_manager.get_active_version()
            if not active_version:
                return

            # Verificar métricas de rendimiento
            await self._check_performance_metrics(active_version)

            # Verificar tasa de errores
            await self._check_error_rates(active_version)

            # Verificar validaciones
            await self._check_validation_health(active_version)

            # Verificar vulnerabilidades de seguridad
            await self._check_security_alerts(active_version)

        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")

    async def _check_performance_metrics(self, version: ModelVersion):
        """Verificar métricas de rendimiento."""
        trigger_config = self.rollback_triggers[RollbackTrigger.PERFORMANCE_DEGRADATION]
        if not trigger_config['enabled']:
            return

        try:
            # Obtener métricas reales del monitoring service
            if self.monitoring_service:
                system_status = self.monitoring_service.get_system_status()
                performance_metrics = system_status.get('performance_metrics', {})

                # Extraer métricas de modelo específicas
                model_metrics = performance_metrics.get('model_performance', {})
                current_accuracy = model_metrics.get('accuracy', 0.0)
                current_latency = model_metrics.get('latency_ms', 0.0)

                # Obtener métricas baseline de la versión anterior
                baseline_metrics = await self._get_baseline_metrics(version.version_id)
                baseline_accuracy = baseline_metrics.get('accuracy', current_accuracy)
                baseline_latency = baseline_metrics.get('latency_ms', current_latency)

                # Calcular degradación
                accuracy_drop = baseline_accuracy - current_accuracy
                latency_increase = current_latency - baseline_latency

                logger.debug(f"Performance check - Current: acc={current_accuracy:.3f}, lat={current_latency:.1f}ms | "
                           f"Baseline: acc={baseline_accuracy:.3f}, lat={baseline_latency:.1f}ms")

                # Verificar si supera thresholds
                if (accuracy_drop >= trigger_config['thresholds']['accuracy_drop'] or
                    latency_increase >= trigger_config['thresholds']['latency_increase']):

                    # Buscar versión anterior adecuada
                    previous_version = await self._find_previous_version(version.version_id)
                    if previous_version:
                        await self.trigger_rollback(
                            from_version=version.version_id,
                            to_version=previous_version,
                            trigger=RollbackTrigger.PERFORMANCE_DEGRADATION,
                            reason=f"Performance degradation: accuracy_drop={accuracy_drop:.3f}, latency_increase={latency_increase:.1f}ms"
                        )
            else:
                logger.warning("Monitoring service not available for performance metrics check")

        except Exception as e:
            logger.error(f"Error checking performance metrics: {e}")

    async def _get_baseline_metrics(self, version_id: str) -> Dict[str, float]:
        """Obtener métricas baseline para una versión."""
        try:
            # Intentar obtener métricas de versiones anteriores del monitoring service
            if self.monitoring_service:
                # Buscar en historial de métricas
                metrics_history = self.monitoring_service.get_metrics_history('performance_metrics', limit=10)

                # Buscar la entrada más reciente antes de esta versión
                for entry in reversed(metrics_history):
                    if entry.get('version_id') != version_id:
                        model_perf = entry.get('model_performance', {})
                        return {
                            'accuracy': model_perf.get('accuracy', 0.85),
                            'latency_ms': model_perf.get('latency_ms', 100.0)
                        }

            # Fallback: obtener de version manager si tiene métricas almacenadas
            if hasattr(self.version_manager, 'get_version_metrics'):
                version_metrics = await self.version_manager.get_version_metrics(version_id)
                if version_metrics:
                    return {
                        'accuracy': version_metrics.get('accuracy', 0.85),
                        'latency_ms': version_metrics.get('latency_ms', 100.0)
                    }

            # Último fallback: valores por defecto conservadores
            return {
                'accuracy': 0.85,  # Valor conservador
                'latency_ms': 100.0  # Valor conservador
            }

        except Exception as e:
            logger.error(f"Error getting baseline metrics for version {version_id}: {e}")
            return {'accuracy': 0.85, 'latency_ms': 100.0}

    async def _check_error_rates(self, version: ModelVersion):
        """Verificar tasas de error."""
        trigger_config = self.rollback_triggers[RollbackTrigger.HIGH_ERROR_RATE]
        if not trigger_config['enabled']:
            return

        try:
            # Obtener métricas de error del monitoring service
            if self.monitoring_service:
                system_status = self.monitoring_service.get_system_status()
                error_metrics = system_status.get('error_metrics', {})

                # Extraer métricas de error
                current_errors = error_metrics.get('total_errors', 0)
                total_requests = error_metrics.get('total_requests', 0)

                # También verificar errores específicos del modelo
                model_errors = error_metrics.get('model_errors', 0)

                logger.debug(f"Error rate check - Total errors: {current_errors}, Total requests: {total_requests}, Model errors: {model_errors}")

                if total_requests >= trigger_config['thresholds']['min_samples']:
                    error_rate = current_errors / total_requests

                    if error_rate >= trigger_config['thresholds']['error_rate']:
                        previous_version = await self._find_previous_version(version.version_id)
                        if previous_version:
                            await self.trigger_rollback(
                                from_version=version.version_id,
                                to_version=previous_version,
                                trigger=RollbackTrigger.HIGH_ERROR_RATE,
                                reason=f"High error rate: {error_rate:.2%} ({current_errors}/{total_requests})"
                            )
                elif model_errors > 0:
                    # Verificar errores específicos del modelo incluso con pocas requests
                    model_error_rate = model_errors / max(total_requests, 1)
                    if model_error_rate >= trigger_config['thresholds']['error_rate']:
                        previous_version = await self._find_previous_version(version.version_id)
                        if previous_version:
                            await self.trigger_rollback(
                                from_version=version.version_id,
                                to_version=previous_version,
                                trigger=RollbackTrigger.HIGH_ERROR_RATE,
                                reason=f"High model error rate: {model_error_rate:.2%} ({model_errors} model errors)"
                            )
            else:
                logger.warning("Monitoring service not available for error rate check")

        except Exception as e:
            logger.error(f"Error checking error rates: {e}")

    async def _check_validation_health(self, version: ModelVersion):
        """Verificar salud de validaciones."""
        trigger_config = self.rollback_triggers[RollbackTrigger.VALIDATION_FAILURE]
        if not trigger_config['enabled']:
            return

        try:
            # Obtener estado de validación del validation service
            if self.validation_service:
                validation_status = self.validation_service.get_validation_status()

                # Verificar si hay validaciones fallidas recientes
                latest_validation = validation_status.get('latest_validation', {})
                is_valid = latest_validation.get('is_valid', True)

                # Verificar tasa de fallos de validación
                alerts = latest_validation.get('alerts', [])
                validation_failures = len([a for a in alerts if 'validation' in a.get('message', '').lower()])

                # Obtener métricas de validación del monitoring service si está disponible
                validation_failure_rate = 0.0
                if self.monitoring_service:
                    system_status = self.monitoring_service.get_system_status()
                    validation_metrics = system_status.get('validation_metrics', {})
                    total_validations = validation_metrics.get('total_validations', 0)
                    failed_validations = validation_metrics.get('failed_validations', 0)

                    if total_validations > 0:
                        validation_failure_rate = failed_validations / total_validations

                logger.debug(f"Validation health check - Is valid: {is_valid}, Failures: {validation_failures}, Failure rate: {validation_failure_rate:.3f}")

                # Verificar condiciones de rollback
                if not is_valid or validation_failure_rate >= trigger_config['thresholds']['failure_rate']:
                    previous_version = await self._find_previous_version(version.version_id)
                    if previous_version:
                        failure_details = []
                        if not is_valid:
                            failure_details.append("validation failed")
                        if validation_failure_rate > 0:
                            failure_details.append(f"failure rate {validation_failure_rate:.1%}")

                        await self.trigger_rollback(
                            from_version=version.version_id,
                            to_version=previous_version,
                            trigger=RollbackTrigger.VALIDATION_FAILURE,
                            reason=f"Validation failure: {', '.join(failure_details)}"
                        )
            else:
                logger.warning("Validation service not available for validation health check")

        except Exception as e:
            logger.error(f"Error checking validation health: {e}")

    async def _check_security_alerts(self, version: ModelVersion):
        """Verificar alertas de seguridad."""
        trigger_config = self.rollback_triggers[RollbackTrigger.SECURITY_VULNERABILITY]
        if not trigger_config['enabled']:
            return

        try:
            # Obtener estado de seguridad del security service
            if self.security_service:
                security_dashboard = self.security_service.get_security_dashboard_data()

                # Verificar amenazas activas críticas
                active_threats = security_dashboard.get('active_threats', [])
                critical_threats = [t for t in active_threats if t.get('severity') == 'critical']

                # Verificar métricas de seguridad
                security_metrics = security_dashboard.get('security_metrics', {})
                blocked_ips = security_metrics.get('blocked_ips', 0)
                failed_login_attempts = security_metrics.get('failed_login_attempts', 0)
                suspicious_activities = security_metrics.get('suspicious_activities', 0)

                logger.debug(f"Security check - Critical threats: {len(critical_threats)}, Blocked IPs: {blocked_ips}, Failed logins: {failed_login_attempts}")

                # Verificar condiciones de rollback por seguridad
                security_issues = []

                if critical_threats:
                    security_issues.append(f"{len(critical_threats)} amenazas críticas activas")

                if blocked_ips > 10:  # Threshold arbitrario pero razonable
                    security_issues.append(f"{blocked_ips} IPs bloqueadas")

                if failed_login_attempts > 50:  # Threshold arbitrario
                    security_issues.append(f"{failed_login_attempts} intentos de login fallidos")

                if suspicious_activities > 20:  # Threshold arbitrario
                    security_issues.append(f"{suspicious_activities} actividades sospechosas")

                # Si hay problemas de seguridad críticos, trigger rollback
                if security_issues:
                    previous_version = await self._find_previous_version(version.version_id)
                    if previous_version:
                        await self.trigger_rollback(
                            from_version=version.version_id,
                            to_version=previous_version,
                            trigger=RollbackTrigger.SECURITY_VULNERABILITY,
                            reason=f"Security vulnerability detected: {', '.join(security_issues)}"
                        )
            else:
                logger.warning("Security service not available for security alerts check")

        except Exception as e:
            logger.error(f"Error checking security alerts: {e}")

    async def _find_previous_version(self, current_version_id: str) -> Optional[str]:
        """Encontrar versión anterior adecuada para rollback."""
        versions = await self.version_manager.list_versions()
        versions.sort(key=lambda v: v.created_at, reverse=True)

        current_found = False
        for version in versions:
            if version.version_id == current_version_id:
                current_found = True
                continue
            if current_found and version.status == VersionStatus.ACTIVE:
                return version.version_id

        return None

    async def _assess_rollback_risk(self, from_version: str, to_version: str,
                                  affected_nodes: List[str]) -> Dict[str, Any]:
        """Evaluar riesgos de un rollback."""
        return {
            'risk_level': 'medium',  # low, medium, high
            'estimated_downtime': len(affected_nodes) * 30,  # 30s por nodo
            'data_loss_risk': 'low',
            'compatibility_concerns': [],
            'rollback_success_probability': 0.85
        }

    def _estimate_rollback_duration(self, num_nodes: int) -> int:
        """Estimar duración del rollback."""
        return num_nodes * 45  # 45 segundos por nodo

    def _create_rollback_batches(self, nodes: List[str], batch_size: int) -> List[List[str]]:
        """Crear batches para rollback gradual."""
        return [nodes[i:i + batch_size] for i in range(0, len(nodes), batch_size)]

    def _check_trigger_cooldown(self, trigger: RollbackTrigger) -> bool:
        """Verificar si un trigger está en cooldown."""
        if trigger not in self.trigger_history:
            return True

        config = self.rollback_triggers[trigger]
        cooldown_seconds = config['cooldown_minutes'] * 60
        time_since_last = int(time.time()) - self.trigger_history[trigger]

        return time_since_last >= cooldown_seconds

    def _should_fail_on_batch_error(self) -> bool:
        """Decidir si fallar completamente en error de batch."""
        return False  # Por ahora, continuar en caso de error

    async def _get_nodes_using_version(self, version_id: str) -> List[str]:
        """Obtener lista de nodos que están usando una versión específica."""
        try:
            # Consultar al distribuidor para obtener nodos con esta versión
            if hasattr(self.distributor, 'get_nodes_with_version'):
                nodes = await self.distributor.get_nodes_with_version(version_id)
                return nodes if nodes else []

            # Si no hay método específico, consultar al monitoring service
            if self.monitoring_service:
                system_status = self.monitoring_service.get_system_status()
                # Extraer nodos de las métricas del sistema
                current_metrics = system_status.get('current_metrics', {})
                nodes_info = current_metrics.get('nodes', {})

                # Filtrar nodos que usan la versión especificada
                affected_nodes = []
                for node_id, node_data in nodes_info.items():
                    if isinstance(node_data, dict) and node_data.get('current_version') == version_id:
                        affected_nodes.append(node_id)

                return affected_nodes

            # Fallback: consultar version manager si tiene información de nodos
            if hasattr(self.version_manager, 'get_version_usage'):
                usage_info = await self.version_manager.get_version_usage(version_id)
                return usage_info.get('active_nodes', [])

            # Último fallback: devolver lista vacía (requiere intervención manual)
            logger.warning(f"No se pudieron determinar nodos para versión {version_id}, se requiere intervención manual")
            return []

        except Exception as e:
            logger.error(f"Error obteniendo nodos para versión {version_id}: {e}")
            return []

    async def _notify_rollback_event(self, event_type: str, rollback_id: str):
        """Notificar eventos de rollback."""
        for callback in self.rollback_callbacks:
            try:
                await callback(event_type, rollback_id)
            except Exception as e:
                logger.warning(f"Rollback callback failed: {e}")

    def add_rollback_callback(self, callback: Callable):
        """Agregar callback para eventos de rollback."""
        self.rollback_callbacks.append(callback)

    async def get_rollback_status(self, rollback_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de un rollback."""
        execution = self.active_rollbacks.get(rollback_id)
        if execution:
            return execution.to_dict()

        # Buscar en historial
        for historical in self.rollback_history:
            if historical.plan.rollback_id == rollback_id:
                return historical.to_dict()

        return None

    async def cancel_rollback(self, rollback_id: str) -> bool:
        """Cancelar un rollback en progreso."""
        execution = self.active_rollbacks.get(rollback_id)
        if execution and execution.status in [RollbackStatus.PENDING, RollbackStatus.IN_PROGRESS]:
            execution.status = RollbackStatus.CANCELLED
            logger.info(f"🛑 Cancelled rollback {rollback_id}")
            return True
        return False

    def get_rollback_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de rollbacks."""
        total_rollbacks = len(self.rollback_history)
        successful_rollbacks = sum(1 for r in self.rollback_history if r.status == RollbackStatus.COMPLETED)
        failed_rollbacks = sum(1 for r in self.rollback_history if r.status == RollbackStatus.FAILED)

        return {
            'total_rollbacks': total_rollbacks,
            'successful_rollbacks': successful_rollbacks,
            'failed_rollbacks': failed_rollbacks,
            'success_rate': successful_rollbacks / max(1, total_rollbacks),
            'active_rollbacks': len(self.active_rollbacks),
            'queue_size': self.rollback_queue.qsize(),
            'auto_rollback_enabled': self.auto_rollback_enabled
        }

    def configure_trigger(self, trigger: RollbackTrigger, enabled: bool,
                         thresholds: Optional[Dict[str, Any]] = None,
                         cooldown_minutes: Optional[int] = None):
        """Configurar un trigger de rollback."""
        if trigger not in self.rollback_triggers:
            raise ValueError(f"Unknown trigger: {trigger}")

        config = self.rollback_triggers[trigger]
        config['enabled'] = enabled

        if thresholds:
            config['thresholds'].update(thresholds)

        if cooldown_minutes is not None:
            config['cooldown_minutes'] = cooldown_minutes

        logger.info(f"⚙️ Configured trigger {trigger.value}: enabled={enabled}")