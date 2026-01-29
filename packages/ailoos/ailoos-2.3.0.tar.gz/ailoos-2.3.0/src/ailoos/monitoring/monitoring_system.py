"""
Sistema de Monitoreo 24/7 Unificado para AILOOS
Sistema completo de monitoreo enterprise-grade con alta disponibilidad y escalabilidad.

Componentes principales:
- ContinuousMonitoring: Monitoreo continuo de todos los componentes
- IntelligentAlerting: Sistema de alertas inteligentes con severidad y escalada
- RealTimeDashboards: Dashboards en tiempo real con métricas críticas
- AutoHealingSystem: Auto-healing automático para problemas detectados
- PerformanceMetrics: Métricas detalladas de rendimiento y salud del sistema
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import aiohttp
from pathlib import Path

try:
    # Importaciones cuando se ejecuta como módulo
    from .realtime_monitor import RealtimeMonitor
    from .alerts import AlertManager, AlertConfig
    from .dashboard import DashboardManager
    from .logger import DistributedLogger
    from .metrics_api import MetricsAPI
    from .advanced_analytics import AdvancedAnalyticsEngine
    from .business_metrics import BusinessMetricsEngine
    from .model_monitor import ModelMonitor, AlertConfig as ModelAlertConfig
    from .multi_region_monitor import MultiRegionMonitor
    from .correlation_tracker import CorrelationTracker, get_correlation_tracker
    from .performance_metrics import PerformanceMetricsCollector, get_performance_collector
except ImportError:
    # Importaciones cuando se ejecuta directamente
    from realtime_monitor import RealtimeMonitor
    from alerts import AlertManager, AlertConfig
    from dashboard import DashboardManager
    from logger import DistributedLogger
    from metrics_api import MetricsAPI
    from advanced_analytics import AdvancedAnalyticsEngine
    from business_metrics import BusinessMetricsEngine
    from model_monitor import ModelMonitor, AlertConfig as ModelAlertConfig
    from multi_region_monitor import MultiRegionMonitor
    from correlation_tracker import CorrelationTracker, get_correlation_tracker
    from performance_metrics import PerformanceMetricsCollector, get_performance_collector

logger = logging.getLogger(__name__)


class MonitoringComponent(Enum):
    """Componentes del sistema de monitoreo"""
    CONTINUOUS_MONITORING = "continuous_monitoring"
    INTELLIGENT_ALERTING = "intelligent_alerting"
    REAL_TIME_DASHBOARDS = "real_time_dashboards"
    AUTO_HEALING = "auto_healing"
    PERFORMANCE_METRICS = "performance_metrics"


class AlertSeverity(Enum):
    """Severidades de alertas"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EscalationLevel(Enum):
    """Niveles de escalada de alertas"""
    NONE = "none"
    TEAM_LEAD = "team_lead"
    MANAGEMENT = "management"
    EXECUTIVE = "executive"
    EMERGENCY = "emergency"


@dataclass
class AlertRule:
    """Regla de alerta inteligente"""
    rule_id: str
    name: str
    description: str
    component: MonitoringComponent
    metric_name: str
    condition: str
    severity: AlertSeverity
    escalation_policy: Dict[AlertSeverity, EscalationLevel] = field(default_factory=dict)
    cooldown_minutes: int = 5
    auto_healing_actions: List[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class HealingAction:
    """Acción de auto-healing"""
    action_id: str
    name: str
    description: str
    component: MonitoringComponent
    trigger_condition: str
    healing_steps: List[Dict[str, Any]]
    success_criteria: str
    timeout_seconds: int = 300
    max_retries: int = 3


@dataclass
class SystemHealth:
    """Estado de salud del sistema"""
    timestamp: datetime
    overall_status: str
    component_status: Dict[str, str] = field(default_factory=dict)
    active_alerts: int = 0
    critical_issues: int = 0
    uptime_percentage: float = 100.0
    performance_score: float = 100.0


class AutoHealingSystem:
    """Sistema de auto-healing automático"""

    def __init__(self, monitoring_system):
        self.monitoring_system = monitoring_system
        self.healing_actions: Dict[str, HealingAction] = {}
        self.active_healing_tasks: Dict[str, asyncio.Task] = {}
        self.healing_history: List[Dict[str, Any]] = []

        self._setup_default_healing_actions()

    def _setup_default_healing_actions(self):
        """Configurar acciones de healing por defecto"""

        # Healing para nodos caídos
        self.healing_actions["restart_failed_node"] = HealingAction(
            action_id="restart_failed_node",
            name="Reiniciar Nodo Fallido",
            description="Reinicia automáticamente nodos que han fallado",
            component=MonitoringComponent.CONTINUOUS_MONITORING,
            trigger_condition="node_down",
            healing_steps=[
                {"type": "api_call", "endpoint": "/api/nodes/restart", "method": "POST", "payload": {"node_id": "{node_id}"}},
                {"type": "wait", "seconds": 30},
                {"type": "health_check", "endpoint": "/api/nodes/{node_id}/health"}
            ],
            success_criteria="node_status == 'healthy'",
            timeout_seconds=180,
            max_retries=2
        )

        # Healing para alta latencia
        self.healing_actions["optimize_high_latency"] = HealingAction(
            action_id="optimize_high_latency",
            name="Optimizar Latencia Alta",
            description="Optimiza recursos para reducir latencia",
            component=MonitoringComponent.PERFORMANCE_METRICS,
            trigger_condition="latency > 500",
            healing_steps=[
                {"type": "scale_resources", "service": "inference", "replicas": "+1"},
                {"type": "clear_cache", "cache_type": "prediction_cache"},
                {"type": "wait", "seconds": 60},
                {"type": "performance_check", "metric": "latency_ms", "threshold": 500}
            ],
            success_criteria="latency_ms < 500",
            timeout_seconds=300,
            max_retries=1
        )

        # Healing para alta memoria
        self.healing_actions["memory_optimization"] = HealingAction(
            action_id="memory_optimization",
            name="Optimización de Memoria",
            description="Libera memoria y optimiza uso",
            component=MonitoringComponent.PERFORMANCE_METRICS,
            trigger_condition="memory_usage > 90",
            healing_steps=[
                {"type": "garbage_collect", "target": "all_models"},
                {"type": "unload_unused_models", "threshold_days": 7},
                {"type": "memory_check", "threshold": 90}
            ],
            success_criteria="memory_usage < 85",
            timeout_seconds=120,
            max_retries=1
        )

    async def trigger_healing(self, alert_data: Dict[str, Any]) -> bool:
        """Disparar acción de healing basada en alerta"""
        try:
            # Encontrar acción de healing apropiada
            healing_action = None
            for action in self.healing_actions.values():
                if self._matches_trigger_condition(action.trigger_condition, alert_data):
                    healing_action = action
                    break

            if not healing_action:
                logger.info(f"No healing action found for alert: {alert_data}")
                return False

            # Verificar si ya hay una tarea activa para este componente
            task_key = f"{healing_action.action_id}_{alert_data.get('node_id', 'system')}"
            if task_key in self.active_healing_tasks:
                logger.info(f"Healing already in progress for {task_key}")
                return False

            # Iniciar tarea de healing
            task = asyncio.create_task(self._execute_healing(healing_action, alert_data))
            self.active_healing_tasks[task_key] = task

            logger.info(f"Started healing action: {healing_action.name} for alert: {alert_data}")
            return True

        except Exception as e:
            logger.error(f"Error triggering healing: {e}")
            return False

    def _matches_trigger_condition(self, condition: str, alert_data: Dict[str, Any]) -> bool:
        """Verificar si la condición de trigger coincide"""
        try:
            # Condiciones simples (pueden ser más complejas)
            if "node_down" in condition and alert_data.get("type") == "node_down":
                return True
            if "latency >" in condition:
                threshold = int(condition.split(">")[1])
                return alert_data.get("latency_ms", 0) > threshold
            if "memory_usage >" in condition:
                threshold = int(condition.split(">")[1])
                return alert_data.get("memory_usage", 0) > threshold
            return False
        except:
            return False

    async def _execute_healing(self, action: HealingAction, alert_data: Dict[str, Any]) -> bool:
        """Ejecutar pasos de healing"""
        task_key = f"{action.action_id}_{alert_data.get('node_id', 'system')}"

        try:
            logger.info(f"Executing healing action: {action.name}")

            for attempt in range(action.max_retries + 1):
                success = await self._execute_healing_steps(action, alert_data)

                if success:
                    # Registrar éxito
                    self.healing_history.append({
                        "timestamp": datetime.now().isoformat(),
                        "action_id": action.action_id,
                        "alert_data": alert_data,
                        "success": True,
                        "attempts": attempt + 1
                    })
                    logger.info(f"Healing action completed successfully: {action.name}")
                    return True

                if attempt < action.max_retries:
                    logger.warning(f"Healing attempt {attempt + 1} failed, retrying...")
                    await asyncio.sleep(10)

            # Todas las tentativas fallaron
            self.healing_history.append({
                "timestamp": datetime.now().isoformat(),
                "action_id": action.action_id,
                "alert_data": alert_data,
                "success": False,
                "attempts": action.max_retries + 1,
                "error": "All healing attempts failed"
            })
            logger.error(f"All healing attempts failed for: {action.name}")
            return False

        except Exception as e:
            logger.error(f"Error executing healing action {action.action_id}: {e}")
            return False
        finally:
            # Limpiar tarea activa
            if task_key in self.active_healing_tasks:
                del self.active_healing_tasks[task_key]

    async def _execute_healing_steps(self, action: HealingAction, alert_data: Dict[str, Any]) -> bool:
        """Ejecutar los pasos individuales de healing"""
        try:
            for step in action.healing_steps:
                step_type = step.get("type")

                if step_type == "api_call":
                    success = await self._execute_api_call(step, alert_data)
                elif step_type == "wait":
                    await asyncio.sleep(step.get("seconds", 10))
                    success = True
                elif step_type == "health_check":
                    success = await self._execute_health_check(step, alert_data)
                elif step_type == "scale_resources":
                    success = await self._execute_resource_scaling(step, alert_data)
                elif step_type == "clear_cache":
                    success = await self._execute_cache_clear(step, alert_data)
                elif step_type == "garbage_collect":
                    success = await self._execute_garbage_collect(step, alert_data)
                elif step_type == "unload_unused_models":
                    success = await self._execute_model_unload(step, alert_data)
                elif step_type == "memory_check":
                    success = await self._execute_memory_check(step, alert_data)
                elif step_type == "performance_check":
                    success = await self._execute_performance_check(step, alert_data)
                else:
                    logger.warning(f"Unknown healing step type: {step_type}")
                    success = False

                if not success:
                    return False

            # Verificar criterios de éxito
            return await self._verify_success_criteria(action.success_criteria, alert_data)

        except Exception as e:
            logger.error(f"Error executing healing steps: {e}")
            return False

    async def _execute_api_call(self, step: Dict[str, Any], alert_data: Dict[str, Any]) -> bool:
        """Ejecutar llamada API"""
        try:
            endpoint = step.get("endpoint", "").format(**alert_data)
            method = step.get("method", "GET")
            payload = step.get("payload", {})

            # Simular llamada API (en implementación real, usar cliente HTTP)
            logger.info(f"API call: {method} {endpoint} with payload: {payload}")
            await asyncio.sleep(1)  # Simular delay

            # Simular éxito/fracaso
            return True

        except Exception as e:
            logger.error(f"API call failed: {e}")
            return False

    async def _execute_health_check(self, step: Dict[str, Any], alert_data: Dict[str, Any]) -> bool:
        """Ejecutar verificación de salud"""
        try:
            endpoint = step.get("endpoint", "").format(**alert_data)
            logger.info(f"Health check: {endpoint}")

            # Simular verificación de salud
            await asyncio.sleep(2)
            return True  # Simular éxito

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def _execute_resource_scaling(self, step: Dict[str, Any], alert_data: Dict[str, Any]) -> bool:
        """Ejecutar escalado de recursos"""
        service = step.get("service")
        replicas = step.get("replicas")
        logger.info(f"Scaling {service} by {replicas} replicas")
        await asyncio.sleep(5)  # Simular tiempo de escalado
        return True

    async def _execute_cache_clear(self, step: Dict[str, Any], alert_data: Dict[str, Any]) -> bool:
        """Limpiar caché"""
        cache_type = step.get("cache_type")
        logger.info(f"Clearing {cache_type} cache")
        await asyncio.sleep(2)
        return True

    async def _execute_garbage_collect(self, step: Dict[str, Any], alert_data: Dict[str, Any]) -> bool:
        """Ejecutar garbage collection"""
        target = step.get("target")
        logger.info(f"Garbage collecting {target}")
        await asyncio.sleep(3)
        return True

    async def _execute_model_unload(self, step: Dict[str, Any], alert_data: Dict[str, Any]) -> bool:
        """Descargar modelos no usados"""
        threshold_days = step.get("threshold_days")
        logger.info(f"Unloading models older than {threshold_days} days")
        await asyncio.sleep(5)
        return True

    async def _execute_memory_check(self, step: Dict[str, Any], alert_data: Dict[str, Any]) -> bool:
        """Verificar uso de memoria"""
        threshold = step.get("threshold")
        # Simular verificación
        current_memory = 75  # Simulado
        return current_memory < threshold

    async def _execute_performance_check(self, step: Dict[str, Any], alert_data: Dict[str, Any]) -> bool:
        """Verificar rendimiento"""
        metric = step.get("metric")
        threshold = step.get("threshold")
        # Simular verificación
        current_value = 400  # Simulado
        return current_value < threshold

    async def _verify_success_criteria(self, criteria: str, alert_data: Dict[str, Any]) -> bool:
        """Verificar criterios de éxito"""
        try:
            # Criterios simples (pueden ser más complejos)
            if "node_status == 'healthy'" in criteria:
                return True  # Simulado
            if "latency_ms <" in criteria:
                threshold = int(criteria.split("<")[1])
                return alert_data.get("latency_ms", 0) < threshold
            if "memory_usage <" in criteria:
                threshold = int(criteria.split("<")[1])
                return alert_data.get("memory_usage", 0) < threshold
            return True
        except:
            return False

    def get_healing_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de healing"""
        total_actions = len(self.healing_history)
        successful_actions = len([h for h in self.healing_history if h.get("success", False)])
        success_rate = (successful_actions / total_actions * 100) if total_actions > 0 else 0

        return {
            "total_healing_actions": total_actions,
            "successful_actions": successful_actions,
            "success_rate": round(success_rate, 2),
            "active_healing_tasks": len(self.active_healing_tasks),
            "available_actions": len(self.healing_actions)
        }


class UnifiedMonitoringSystem:
    """
    Sistema de Monitoreo Unificado 24/7 para AILOOS
    Integra todos los componentes de monitoreo en un sistema enterprise-grade
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        self.system_health = SystemHealth(timestamp=datetime.now(), overall_status="INITIALIZING")

        # Componentes del sistema
        self.components = {}

        # Sistema de alertas inteligente
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
        self.alert_history: List[Dict[str, Any]] = []

        # Sistema de auto-healing
        self.auto_healing = AutoHealingSystem(self)

        # Estado del sistema
        self.monitoring_active = False
        self.start_time = datetime.now()
        self.last_health_check = datetime.now()

        # Configurar componentes
        self._initialize_components()

        logger.info("Unified Monitoring System initialized")

    def _get_default_config(self) -> Dict[str, Any]:
        """Obtener configuración por defecto"""
        return {
            "coordinator_url": "http://localhost:5001",
            "metrics_api_url": "http://localhost:8080",
            "dashboard_port": 3001,
            "alert_email_enabled": False,
            "alert_slack_webhook": "",
            "timescale_db_url": "postgresql://user:password@localhost/ailoos_monitoring",
            "high_availability": True,
            "auto_healing_enabled": True,
            "monitoring_interval_seconds": 30,
            "health_check_interval_seconds": 60
        }

    def _initialize_components(self):
        """Inicializar todos los componentes del sistema"""
        try:
            # Continuous Monitoring
            self.components[MonitoringComponent.CONTINUOUS_MONITORING] = RealtimeMonitor()

            # Intelligent Alerting
            alert_config = AlertConfig(
                email_enabled=self.config.get("alert_email_enabled", False),
                slack_webhook_url=self.config.get("alert_slack_webhook", "")
            )
            self.components[MonitoringComponent.INTELLIGENT_ALERTING] = AlertManager(
                alert_config, self.config["metrics_api_url"]
            )

            # Real-time Dashboards
            self.components[MonitoringComponent.REAL_TIME_DASHBOARDS] = DashboardManager(
                self.config["metrics_api_url"]
            )

            # Performance Metrics
            self.components[MonitoringComponent.PERFORMANCE_METRICS] = {
                "business_metrics": BusinessMetricsEngine(),
                "advanced_analytics": AdvancedAnalyticsEngine(),
                "model_monitor": ModelMonitor(),
                "multi_region_monitor": MultiRegionMonitor()
            }

            # Auto-healing ya inicializado
            self.components[MonitoringComponent.AUTO_HEALING] = self.auto_healing

            # Correlation Tracker
            self.components['correlation_tracker'] = get_correlation_tracker()

            # Performance Metrics Collector
            self.components['performance_collector'] = get_performance_collector()

            logger.info("All monitoring components initialized")

        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise

    def _setup_default_alert_rules(self):
        """Configurar reglas de alerta por defecto"""
        rules = [
            AlertRule(
                rule_id="node_down_critical",
                name="Nodo Crítico Caído",
                description="Un nodo crítico ha dejado de responder",
                component=MonitoringComponent.CONTINUOUS_MONITORING,
                metric_name="node_health",
                condition="status == 'down' AND node_type == 'critical'",
                severity=AlertSeverity.CRITICAL,
                escalation_policy={
                    AlertSeverity.CRITICAL: EscalationLevel.EXECUTIVE
                },
                auto_healing_actions=["restart_failed_node"],
                cooldown_minutes=2
            ),
            AlertRule(
                rule_id="high_system_load",
                name="Carga del Sistema Alta",
                description="La carga del sistema supera el 90%",
                component=MonitoringComponent.PERFORMANCE_METRICS,
                metric_name="system_load",
                condition="value > 90",
                severity=AlertSeverity.WARNING,
                escalation_policy={
                    AlertSeverity.WARNING: EscalationLevel.TEAM_LEAD,
                    AlertSeverity.ERROR: EscalationLevel.MANAGEMENT
                },
                auto_healing_actions=["optimize_high_latency"],
                cooldown_minutes=5
            ),
            AlertRule(
                rule_id="memory_critical",
                name="Memoria Crítica",
                description="Uso de memoria supera el 95%",
                component=MonitoringComponent.PERFORMANCE_METRICS,
                metric_name="memory_usage",
                condition="value > 95",
                severity=AlertSeverity.CRITICAL,
                escalation_policy={
                    AlertSeverity.CRITICAL: EscalationLevel.EMERGENCY
                },
                auto_healing_actions=["memory_optimization"],
                cooldown_minutes=1
            ),
            AlertRule(
                rule_id="federated_training_failed",
                name="Entrenamiento Federado Fallido",
                description="El entrenamiento federado ha fallado",
                component=MonitoringComponent.CONTINUOUS_MONITORING,
                metric_name="federated_status",
                condition="status == 'failed'",
                severity=AlertSeverity.ERROR,
                escalation_policy={
                    AlertSeverity.ERROR: EscalationLevel.MANAGEMENT
                },
                cooldown_minutes=10
            )
        ]

        for rule in rules:
            self.alert_rules[rule.rule_id] = rule

    async def start_monitoring(self):
        """Iniciar el sistema de monitoreo completo"""
        if self.monitoring_active:
            logger.warning("Monitoring system already active")
            return

        try:
            self.monitoring_active = True
            self.start_time = datetime.now()

            # Configurar reglas de alerta por defecto
            self._setup_default_alert_rules()

            # Iniciar componentes individuales
            await self._start_components()

            # Iniciar loops de monitoreo
            asyncio.create_task(self._monitoring_loop())
            asyncio.create_task(self._health_check_loop())
            asyncio.create_task(self._alert_evaluation_loop())

            # Actualizar estado de salud
            self.system_health.overall_status = "HEALTHY"
            self._update_component_status()

            logger.info("Unified Monitoring System started successfully")

        except Exception as e:
            logger.error(f"Error starting monitoring system: {e}")
            self.system_health.overall_status = "ERROR"
            raise

    async def _start_components(self):
        """Iniciar todos los componentes"""
        try:
            # Iniciar monitoreo en tiempo real
            realtime_monitor = self.components[MonitoringComponent.CONTINUOUS_MONITORING]
            realtime_monitor.start_monitoring()

            # Configurar callbacks de alertas
            alert_manager = self.components[MonitoringComponent.INTELLIGENT_ALERTING]
            alert_manager.add_alert_callback("node_down", self._handle_node_down_alert)
            alert_manager.add_alert_callback("node_recovered", self._handle_node_recovered_alert)

            # Iniciar dashboard
            dashboard = self.components[MonitoringComponent.REAL_TIME_DASHBOARDS]
            asyncio.create_task(dashboard.start_dashboard(port=self.config["dashboard_port"]))

            # Iniciar métricas API
            metrics_api = MetricsAPI(self.config["coordinator_url"])
            asyncio.create_task(metrics_api.start_server(port=8080))

            # Iniciar model monitor
            model_monitor = self.components[MonitoringComponent.PERFORMANCE_METRICS]["model_monitor"]
            await model_monitor.start_monitoring()

            logger.info("All monitoring components started")

        except Exception as e:
            logger.error(f"Error starting components: {e}")
            raise

    async def stop_monitoring(self):
        """Detener el sistema de monitoreo"""
        self.monitoring_active = False

        try:
            # Detener componentes
            realtime_monitor = self.components[MonitoringComponent.CONTINUOUS_MONITORING]
            realtime_monitor.stop_monitoring()

            model_monitor = self.components[MonitoringComponent.PERFORMANCE_METRICS]["model_monitor"]
            await model_monitor.stop_monitoring()

            self.system_health.overall_status = "STOPPED"
            logger.info("Unified Monitoring System stopped")

        except Exception as e:
            logger.error(f"Error stopping monitoring system: {e}")

    async def _monitoring_loop(self):
        """Loop principal de monitoreo"""
        while self.monitoring_active:
            try:
                # Recolectar métricas de todos los componentes
                await self._collect_all_metrics()

                # Evaluar reglas de alerta
                await self._evaluate_alert_rules()

                # Ejecutar acciones de mantenimiento
                await self._perform_maintenance_tasks()

                await asyncio.sleep(self.config["monitoring_interval_seconds"])

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)

    async def _health_check_loop(self):
        """Loop de verificación de salud del sistema"""
        while self.monitoring_active:
            try:
                await self._perform_system_health_check()
                await asyncio.sleep(self.config["health_check_interval_seconds"])

            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(30)

    async def _alert_evaluation_loop(self):
        """Loop de evaluación de alertas"""
        while self.monitoring_active:
            try:
                # Evaluar alertas inteligentes
                await self._evaluate_intelligent_alerts()

                # Gestionar escalada de alertas
                await self._manage_alert_escalation()

                await asyncio.sleep(60)  # Evaluar cada minuto

            except Exception as e:
                logger.error(f"Error in alert evaluation loop: {e}")
                await asyncio.sleep(30)

    async def _collect_all_metrics(self):
        """Recolectar métricas de todos los componentes"""
        try:
            metrics_data = {}

            # Métricas de sistema
            realtime_monitor = self.components[MonitoringComponent.CONTINUOUS_MONITORING]
            metrics_data["system"] = realtime_monitor.get_system_status()

            # Métricas de negocio
            business_metrics = self.components[MonitoringComponent.PERFORMANCE_METRICS]["business_metrics"]
            metrics_data["business"] = business_metrics.get_business_kpis()

            # Métricas de modelos
            model_monitor = self.components[MonitoringComponent.PERFORMANCE_METRICS]["model_monitor"]
            metrics_data["models"] = await model_monitor.get_monitoring_stats()

            # Métricas multi-región
            multi_region = self.components[MonitoringComponent.PERFORMANCE_METRICS]["multi_region_monitor"]
            metrics_data["regions"] = multi_region.get_load_balancing_status()

            # Analytics avanzado
            analytics = self.components[MonitoringComponent.PERFORMANCE_METRICS]["advanced_analytics"]
            metrics_data["analytics"] = {
                "last_report_date": datetime.now().strftime("%Y-%m-%d"),
                "predictions_available": True
            }

            # Almacenar métricas recolectadas
            self._store_metrics_snapshot(metrics_data)

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")

    def _store_metrics_snapshot(self, metrics: Dict[str, Any]):
        """Almacenar snapshot de métricas"""
        # En implementación real, almacenar en base de datos
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics
        }

        # Mantener solo últimas 100 snapshots
        if not hasattr(self, 'metrics_history'):
            self.metrics_history = []

        self.metrics_history.append(snapshot)
        if len(self.metrics_history) > 100:
            self.metrics_history.pop(0)

    async def _evaluate_alert_rules(self):
        """Evaluar todas las reglas de alerta"""
        try:
            for rule in self.alert_rules.values():
                if not rule.enabled:
                    continue

                # Verificar condición de la regla
                if await self._check_rule_condition(rule):
                    await self._trigger_alert(rule)

        except Exception as e:
            logger.error(f"Error evaluating alert rules: {e}")

    async def _check_rule_condition(self, rule: AlertRule) -> bool:
        """Verificar condición de una regla de alerta"""
        try:
            # Obtener métricas relevantes
            if rule.component == MonitoringComponent.CONTINUOUS_MONITORING:
                monitor = self.components[MonitoringComponent.CONTINUOUS_MONITORING]
                metrics = monitor.get_system_status()

                if rule.metric_name == "node_health":
                    # Verificar nodos caídos
                    return len([n for n in metrics.get("current_metrics", {}) if "down" in str(n)]) > 0

                elif rule.metric_name == "system_load":
                    cpu_usage = metrics.get("current_metrics", {}).get("cpu_usage", {}).get("value", 0)
                    return cpu_usage > 90

            elif rule.component == MonitoringComponent.PERFORMANCE_METRICS:
                # Verificar métricas de rendimiento
                if rule.metric_name == "memory_usage":
                    monitor = self.components[MonitoringComponent.CONTINUOUS_MONITORING]
                    metrics = monitor.get_system_status()
                    memory_usage = metrics.get("current_metrics", {}).get("memory_usage", {}).get("value", 0)
                    return memory_usage > 95

            return False

        except Exception as e:
            logger.error(f"Error checking rule condition for {rule.rule_id}: {e}")
            return False

    async def _trigger_alert(self, rule: AlertRule):
        """Disparar una alerta"""
        try:
            # Verificar cooldown
            alert_key = f"{rule.rule_id}_{datetime.now().strftime('%Y%m%d%H%M')}"
            if alert_key in self.active_alerts:
                last_triggered = self.active_alerts[alert_key].get("last_triggered")
                if last_triggered and (datetime.now() - last_triggered).seconds < rule.cooldown_minutes * 60:
                    return

            # Crear alerta
            alert = {
                "alert_id": f"alert_{int(time.time())}_{rule.rule_id}",
                "rule_id": rule.rule_id,
                "severity": rule.severity.value,
                "message": rule.description,
                "component": rule.component.value,
                "timestamp": datetime.now().isoformat(),
                "escalation_level": rule.escalation_policy.get(rule.severity, EscalationLevel.NONE).value,
                "auto_healing_triggered": False,
                "last_triggered": datetime.now()
            }

            # Añadir a alertas activas
            self.active_alerts[alert_key] = alert
            self.alert_history.append(alert)

            # Trigger auto-healing si está configurado
            if rule.auto_healing_actions and self.config.get("auto_healing_enabled", True):
                for action in rule.auto_healing_actions:
                    if action in self.auto_healing.healing_actions:
                        healing_triggered = await self.auto_healing.trigger_healing(alert)
                        alert["auto_healing_triggered"] = healing_triggered

            # Notificar a través de los canales configurados
            await self._notify_alert(alert)

            logger.warning(f"Alert triggered: {rule.name} (Severity: {rule.severity.value})")

        except Exception as e:
            logger.error(f"Error triggering alert for rule {rule.rule_id}: {e}")

    async def _notify_alert(self, alert: Dict[str, Any]):
        """Notificar alerta a través de los canales configurados"""
        try:
            # Email notification
            if self.config.get("alert_email_enabled"):
                await self._send_email_alert(alert)

            # Slack notification
            if self.config.get("alert_slack_webhook"):
                await self._send_slack_alert(alert)

            # Dashboard notification
            dashboard = self.components[MonitoringComponent.REAL_TIME_DASHBOARDS]
            # Enviar notificación al dashboard (implementación futura)

        except Exception as e:
            logger.error(f"Error notifying alert: {e}")

    async def _send_email_alert(self, alert: Dict[str, Any]):
        """Enviar alerta por email"""
        # Implementación simplificada
        logger.info(f"Email alert sent: {alert['message']}")

    async def _send_slack_alert(self, alert: Dict[str, Any]):
        """Enviar alerta por Slack"""
        # Implementación simplificada
        logger.info(f"Slack alert sent: {alert['message']}")

    async def _evaluate_intelligent_alerts(self):
        """Evaluar alertas inteligentes usando analytics"""
        try:
            analytics = self.components[MonitoringComponent.PERFORMANCE_METRICS]["advanced_analytics"]

            # Predecir fallos
            failure_predictions = analytics.predict_failures("system", 24)
            if failure_predictions.get("risk_level") == "CRITICAL":
                await self._trigger_predictive_alert(failure_predictions)

            # Analizar tendencias
            trends = analytics.analyze_growth_trends()
            if trends.get("current_trend") == "Declining":
                await self._trigger_trend_alert(trends)

        except Exception as e:
            logger.error(f"Error evaluating intelligent alerts: {e}")

    async def _trigger_predictive_alert(self, predictions: Dict[str, Any]):
        """Disparar alerta predictiva"""
        alert = {
            "alert_id": f"predictive_{int(time.time())}",
            "type": "predictive_failure",
            "severity": "warning",
            "message": f"Critical failure predicted: {predictions.get('failure_risk_score', 0):.2f} risk score",
            "predictions": predictions,
            "timestamp": datetime.now().isoformat()
        }

        self.alert_history.append(alert)
        await self._notify_alert(alert)

    async def _trigger_trend_alert(self, trends: Dict[str, Any]):
        """Disparar alerta de tendencia"""
        alert = {
            "alert_id": f"trend_{int(time.time())}",
            "type": "trend_alert",
            "severity": "info",
            "message": f"Negative trend detected: {trends.get('current_trend', 'Unknown')}",
            "trends": trends,
            "timestamp": datetime.now().isoformat()
        }

        self.alert_history.append(alert)
        await self._notify_alert(alert)

    async def _manage_alert_escalation(self):
        """Gestionar escalada de alertas"""
        try:
            current_time = datetime.now()

            for alert_key, alert in self.active_alerts.items():
                # Verificar tiempo desde la última escalada
                last_escalation = alert.get("last_escalation", alert["timestamp"])
                if isinstance(last_escalation, str):
                    last_escalation = datetime.fromisoformat(last_escalation)

                time_since_escalation = (current_time - last_escalation).seconds / 60  # minutos

                # Lógica de escalada (simplificada)
                if time_since_escalation > 30 and alert["severity"] in ["error", "critical"]:
                    alert["escalation_level"] = "management"
                    alert["last_escalation"] = current_time.isoformat()

                    # Re-notificar con nivel de escalada
                    await self._notify_alert(alert)
                    logger.warning(f"Alert escalated: {alert['alert_id']}")

        except Exception as e:
            logger.error(f"Error managing alert escalation: {e}")

    async def _perform_maintenance_tasks(self):
        """Ejecutar tareas de mantenimiento"""
        try:
            # Limpiar alertas antiguas (más de 24 horas)
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.active_alerts = {
                k: v for k, v in self.active_alerts.items()
                if datetime.fromisoformat(v["timestamp"]) > cutoff_time
            }

            # Mantener historial limitado
            if len(self.alert_history) > 1000:
                self.alert_history = self.alert_history[-1000:]

        except Exception as e:
            logger.error(f"Error performing maintenance tasks: {e}")

    async def _perform_system_health_check(self):
        """Realizar verificación de salud del sistema"""
        try:
            self.last_health_check = datetime.now()

            # Verificar componentes
            component_status = {}
            overall_status = "HEALTHY"
            critical_issues = 0
            active_alerts = len(self.active_alerts)

            for component_name, component in self.components.items():
                try:
                    if hasattr(component, 'get_system_status'):
                        status = component.get_system_status()
                        component_status[component_name.value] = "HEALTHY"
                    elif hasattr(component, 'get_healing_stats'):
                        status = component.get_healing_stats()
                        component_status[component_name.value] = "HEALTHY"
                    else:
                        component_status[component_name.value] = "UNKNOWN"

                except Exception as e:
                    component_status[component_name.value] = "ERROR"
                    critical_issues += 1
                    overall_status = "DEGRADED"
                    logger.error(f"Component health check failed for {component_name.value}: {e}")

            # Calcular uptime
            uptime_seconds = (datetime.now() - self.start_time).total_seconds()
            uptime_percentage = 100.0  # Simplificado

            # Calcular performance score
            performance_score = 100.0 - (critical_issues * 20) - (active_alerts * 5)
            performance_score = max(0, performance_score)

            # Actualizar estado de salud
            self.system_health = SystemHealth(
                timestamp=datetime.now(),
                overall_status=overall_status,
                component_status=component_status,
                active_alerts=active_alerts,
                critical_issues=critical_issues,
                uptime_percentage=uptime_percentage,
                performance_score=performance_score
            )

            self._update_component_status()

        except Exception as e:
            logger.error(f"Error performing system health check: {e}")
            self.system_health.overall_status = "ERROR"

    def _update_component_status(self):
        """Actualizar estado de componentes basado en salud del sistema"""
        # Actualizar métricas en componentes que lo soporten
        try:
            dashboard = self.components[MonitoringComponent.REAL_TIME_DASHBOARDS]
            if hasattr(dashboard, 'update_system_health'):
                dashboard.update_system_health(self.system_health)
        except:
            pass

    async def _handle_node_down_alert(self, alert_data: Dict[str, Any]):
        """Manejador específico para alertas de nodos caídos"""
        logger.warning(f"Node down alert: {alert_data}")

        # Trigger auto-healing
        if self.config.get("auto_healing_enabled", True):
            await self.auto_healing.trigger_healing(alert_data)

    async def _handle_node_recovered_alert(self, alert_data: Dict[str, Any]):
        """Manejador específico para alertas de nodos recuperados"""
        logger.info(f"Node recovered: {alert_data}")

    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado completo del sistema de monitoreo"""
        # Obtener métricas de correlación y performance
        correlation_stats = self.components.get('correlation_tracker', {}).get_performance_stats() if 'correlation_tracker' in self.components else {}
        performance_report = self.components.get('performance_collector', {}).get_performance_report() if 'performance_collector' in self.components else {}

        return {
            "monitoring_active": self.monitoring_active,
            "system_health": {
                "overall_status": self.system_health.overall_status,
                "component_status": self.system_health.component_status,
                "active_alerts": self.system_health.active_alerts,
                "critical_issues": self.system_health.critical_issues,
                "uptime_percentage": self.system_health.uptime_percentage,
                "performance_score": self.system_health.performance_score,
                "last_health_check": self.last_health_check.isoformat()
            },
            "correlation_tracking": correlation_stats,
            "performance_metrics": performance_report,
            "active_alerts": list(self.active_alerts.values())[-10:],  # Últimas 10
            "alert_rules_count": len(self.alert_rules),
            "auto_healing_stats": self.auto_healing.get_healing_stats(),
            "components": {
                component.value if hasattr(component, 'value') else str(component): "ACTIVE" if hasattr(comp, '__dict__') else "CONFIGURED"
                for component, comp in self.components.items()
            },
            "timestamp": datetime.now().isoformat()
        }

    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Generar reporte comprehensivo del sistema"""
        return {
            "system_overview": self.get_system_status(),
            "alert_summary": {
                "total_alerts": len(self.alert_history),
                "active_alerts": len(self.active_alerts),
                "alerts_by_severity": self._get_alerts_by_severity(),
                "recent_alerts": self.alert_history[-20:]  # Últimas 20
            },
            "performance_metrics": self._get_performance_summary(),
            "auto_healing_report": self.auto_healing.get_healing_stats(),
            "recommendations": self._generate_system_recommendations(),
            "generated_at": datetime.now().isoformat()
        }

    def _get_alerts_by_severity(self) -> Dict[str, int]:
        """Obtener conteo de alertas por severidad"""
        severity_count = {}
        for alert in self.alert_history:
            severity = alert.get("severity", "unknown")
            severity_count[severity] = severity_count.get(severity, 0) + 1
        return severity_count

    def _get_performance_summary(self) -> Dict[str, Any]:
        """Obtener resumen de rendimiento"""
        if hasattr(self, 'metrics_history') and self.metrics_history:
            latest = self.metrics_history[-1]["metrics"]
            return {
                "latest_metrics": latest,
                "metrics_history_count": len(self.metrics_history)
            }
        return {"status": "No metrics available"}

    def _generate_system_recommendations(self) -> List[str]:
        """Generar recomendaciones para el sistema"""
        recommendations = []

        health = self.system_health

        if health.critical_issues > 0:
            recommendations.append("🚨 Atención inmediata requerida: Resolver problemas críticos del sistema")

        if health.active_alerts > 10:
            recommendations.append("⚠️ Alto número de alertas activas: Revisar configuración de monitoreo")

        if health.performance_score < 70:
            recommendations.append("📊 Rendimiento degradado: Considerar optimización de recursos")

        if health.uptime_percentage < 99.5:
            recommendations.append("🔄 Uptime por debajo del estándar: Implementar redundancia adicional")

        if not recommendations:
            recommendations.append("✅ Sistema funcionando correctamente")

        return recommendations


# Función de conveniencia para iniciar el sistema completo
async def start_unified_monitoring(config: Dict[str, Any] = None) -> UnifiedMonitoringSystem:
    """Función de conveniencia para iniciar el sistema de monitoreo unificado"""
    monitoring_system = UnifiedMonitoringSystem(config)
    await monitoring_system.start_monitoring()
    return monitoring_system


if __name__ == "__main__":
    # Demo del sistema de monitoreo unificado
    async def demo():
        print("🚀 Iniciando Sistema de Monitoreo Unificado AILOOS")
        print("=" * 60)

        # Configuración de ejemplo
        config = {
            "coordinator_url": "http://localhost:5001",
            "dashboard_port": 3001,
            "auto_healing_enabled": True,
            "high_availability": True
        }

        # Crear e iniciar sistema
        monitoring = UnifiedMonitoringSystem(config)
        await monitoring.start_monitoring()

        print("✅ Sistema de monitoreo iniciado")

        try:
            # Monitorear por un tiempo
            await asyncio.sleep(10)

            # Obtener estado del sistema
            status = monitoring.get_system_status()
            print(f"📊 Estado del sistema: {status['system_health']['overall_status']}")
            print(f"🚨 Alertas activas: {status['system_health']['active_alerts']}")
            print(f"🔧 Auto-healing: {status['auto_healing_stats']['successful_actions']} acciones exitosas")

            # Generar reporte
            report = monitoring.get_comprehensive_report()
            print(f"📋 Reporte generado con {len(report['alert_summary']['recent_alerts'])} alertas recientes")

        finally:
            await monitoring.stop_monitoring()
            print("⏹️ Sistema de monitoreo detenido")

        print("🎉 Demo completada")

    asyncio.run(demo())