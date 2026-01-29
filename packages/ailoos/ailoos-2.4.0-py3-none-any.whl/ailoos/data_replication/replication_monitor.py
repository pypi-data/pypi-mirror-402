import asyncio
import logging
import time
import statistics
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Metric:
    name: str
    value: Any
    metric_type: MetricType
    timestamp: float
    labels: Dict[str, str] = None
    description: str = ""

@dataclass
class Alert:
    alert_id: str
    severity: AlertSeverity
    message: str
    source: str
    timestamp: float
    resolved: bool = False
    resolved_at: Optional[float] = None
    metadata: Dict[str, Any] = None

@dataclass
class AlertRule:
    rule_id: str
    name: str
    condition: Callable[[Dict[str, Any]], bool]
    severity: AlertSeverity
    message_template: str
    enabled: bool = True
    cooldown_seconds: int = 300  # 5 minutes

class ReplicationMonitor:
    """Real-time monitoring for data replication system"""

    def __init__(self, replication_manager, consistency_manager, conflict_resolver):
        self.replication_manager = replication_manager
        self.consistency_manager = consistency_manager
        self.conflict_resolver = conflict_resolver

        # Metrics storage
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.current_gauges: Dict[str, Any] = {}

        # Alerts
        self.alerts: Dict[str, Alert] = {}
        self.resolved_alerts: List[Alert] = []
        self.alert_rules: Dict[str, AlertRule] = {}
        self.alert_cooldowns: Dict[str, float] = {}

        # Monitoring configuration
        self.monitoring_interval = 30  # seconds
        self.retention_period = 3600  # 1 hour
        self._monitoring_task: Optional[asyncio.Task] = None
        self._alert_check_task: Optional[asyncio.Task] = None

        # Setup default alert rules
        self._setup_default_alert_rules()

    def _setup_default_alert_rules(self) -> None:
        """Set up default monitoring alert rules"""

        # Replication failure rate alert
        self.add_alert_rule(
            rule_id="high_replication_failure_rate",
            name="High Replication Failure Rate",
            condition=lambda m: m.get("replication_failure_rate", 0) > 0.1,
            severity=AlertSeverity.WARNING,
            message_template="Replication failure rate is {replication_failure_rate:.2%}, above threshold"
        )

        # Node health alert
        self.add_alert_rule(
            rule_id="node_unhealthy",
            name="Node Unhealthy",
            condition=lambda m: m.get("unhealthy_nodes", 0) > 0,
            severity=AlertSeverity.ERROR,
            message_template="{unhealthy_nodes} nodes are unhealthy"
        )

        # High conflict rate alert
        self.add_alert_rule(
            rule_id="high_conflict_rate",
            name="High Conflict Rate",
            condition=lambda m: m.get("conflict_rate_per_hour", 0) > 10,
            severity=AlertSeverity.WARNING,
            message_template="Conflict rate is {conflict_rate_per_hour:.1f} per hour"
        )

        # Replication lag alert
        self.add_alert_rule(
            rule_id="high_replication_lag",
            name="High Replication Lag",
            condition=lambda m: m.get("avg_replication_lag_seconds", 0) > 300,
            severity=AlertSeverity.WARNING,
            message_template="Average replication lag is {avg_replication_lag_seconds:.1f} seconds"
        )

    def add_alert_rule(self, rule_id: str, name: str, condition: Callable[[Dict[str, Any]], bool],
                      severity: AlertSeverity, message_template: str,
                      cooldown_seconds: int = 300) -> None:
        """Add a custom alert rule"""
        rule = AlertRule(
            rule_id=rule_id,
            name=name,
            condition=condition,
            severity=severity,
            message_template=message_template,
            cooldown_seconds=cooldown_seconds
        )

        self.alert_rules[rule_id] = rule
        logger.info(f"Added alert rule: {name}")

    async def start_monitoring(self) -> None:
        """Start the monitoring system"""
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Started replication monitoring")

        if self._alert_check_task is None:
            self._alert_check_task = asyncio.create_task(self._alert_check_loop())
            logger.info("Started alert checking")

    async def stop_monitoring(self) -> None:
        """Stop the monitoring system"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None

        if self._alert_check_task:
            self._alert_check_task.cancel()
            try:
                await self._alert_check_task
            except asyncio.CancelledError:
                pass
            self._alert_check_task = None

        logger.info("Stopped replication monitoring")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while True:
            try:
                await self._collect_metrics()
                await self._cleanup_old_metrics()
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)

    async def _collect_metrics(self) -> None:
        """Collect current metrics"""
        timestamp = time.time()

        # Replication metrics
        replication_stats = await self._get_replication_metrics()
        for name, value in replication_stats.items():
            self.record_metric(name, value, MetricType.GAUGE, timestamp)

        # Consistency metrics
        consistency_stats = self.consistency_manager.get_consistency_stats()
        for name, value in consistency_stats.items():
            self.record_metric(f"consistency_{name}", value, MetricType.GAUGE, timestamp)

        # Conflict metrics
        conflict_stats = self.conflict_resolver.get_conflict_stats()
        for name, value in conflict_stats.items():
            if isinstance(value, dict):
                for sub_name, sub_value in value.items():
                    self.record_metric(f"conflict_{name}_{sub_name}", sub_value, MetricType.GAUGE, timestamp)
            else:
                self.record_metric(f"conflict_{name}", value, MetricType.GAUGE, timestamp)

        # Node health metrics
        node_status = await self.replication_manager.get_all_node_status()
        healthy_nodes = sum(1 for status in node_status.values() if status.get("is_connected", False))
        total_nodes = len(node_status)

        self.record_metric("total_nodes", total_nodes, MetricType.GAUGE, timestamp)
        self.record_metric("healthy_nodes", healthy_nodes, MetricType.GAUGE, timestamp)
        self.record_metric("unhealthy_nodes", total_nodes - healthy_nodes, MetricType.GAUGE, timestamp)

    async def _get_replication_metrics(self) -> Dict[str, Any]:
        """Get replication-specific metrics"""
        metrics = {}

        # Active tasks
        active_tasks = len(self.replication_manager.active_tasks)
        metrics["active_replication_tasks"] = active_tasks

        # Completed tasks in last hour
        one_hour_ago = time.time() - 3600
        recent_completed = [
            task for task in self.replication_manager.completed_tasks
            if task.completed_at and task.completed_at > one_hour_ago
        ]

        metrics["completed_tasks_last_hour"] = len(recent_completed)

        # Success/failure rates
        if recent_completed:
            successful_tasks = sum(1 for task in recent_completed if task.status.name == "COMPLETED")
            metrics["replication_success_rate"] = successful_tasks / len(recent_completed)
            metrics["replication_failure_rate"] = 1 - metrics["replication_success_rate"]

            # Average completion time
            completion_times = [
                task.completed_at - task.created_at
                for task in recent_completed
                if task.completed_at
            ]
            if completion_times:
                metrics["avg_replication_time_seconds"] = statistics.mean(completion_times)

        # Data volume metrics
        total_data_volume = 0
        for node_status in (await self.replication_manager.get_all_node_status()).values():
            total_data_volume += node_status.get("data_count", 0)
        metrics["total_replicated_data_items"] = total_data_volume

        return metrics

    def record_metric(self, name: str, value: Any, metric_type: MetricType,
                     timestamp: Optional[float] = None, labels: Dict[str, str] = None) -> None:
        """Record a metric"""
        if timestamp is None:
            timestamp = time.time()

        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            timestamp=timestamp,
            labels=labels or {}
        )

        self.metrics[name].append(metric)

        if metric_type == MetricType.GAUGE:
            self.current_gauges[name] = value

    async def _alert_check_loop(self) -> None:
        """Alert checking loop"""
        while True:
            try:
                await self._check_alerts()
                await asyncio.sleep(60)  # Check alerts every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert check loop: {e}")
                await asyncio.sleep(60)

    async def _check_alerts(self) -> None:
        """Check all alert rules against current metrics"""
        current_metrics = dict(self.current_gauges)

        for rule in self.alert_rules.values():
            if not rule.enabled:
                continue

            # Check cooldown
            last_alert_time = self.alert_cooldowns.get(rule.rule_id, 0)
            if time.time() - last_alert_time < rule.cooldown_seconds:
                continue

            # Evaluate condition
            try:
                if rule.condition(current_metrics):
                    await self._trigger_alert(rule, current_metrics)
                    self.alert_cooldowns[rule.rule_id] = time.time()
            except Exception as e:
                logger.error(f"Error evaluating alert rule {rule.rule_id}: {e}")

    async def _trigger_alert(self, rule: AlertRule, metrics: Dict[str, Any]) -> None:
        """Trigger an alert"""
        alert_id = f"alert_{rule.rule_id}_{int(time.time())}"

        message = rule.message_template.format(**metrics)

        alert = Alert(
            alert_id=alert_id,
            severity=rule.severity,
            message=message,
            source=rule.rule_id,
            timestamp=time.time(),
            metadata={"rule_name": rule.name, "metrics": metrics}
        )

        self.alerts[alert_id] = alert
        logger.warning(f"Alert triggered: {alert.message}")

    async def resolve_alert(self, alert_id: str, resolution_notes: str = "") -> bool:
        """Manually resolve an alert"""
        if alert_id not in self.alerts:
            return False

        alert = self.alerts[alert_id]
        alert.resolved = True
        alert.resolved_at = time.time()
        alert.metadata["resolution_notes"] = resolution_notes

        self.resolved_alerts.append(alert)
        del self.alerts[alert_id]

        # Keep only last 100 resolved alerts
        if len(self.resolved_alerts) > 100:
            self.resolved_alerts = self.resolved_alerts[-100:]

        logger.info(f"Resolved alert {alert_id}: {resolution_notes}")
        return True

    def get_metrics(self, name: Optional[str] = None, limit: int = 100) -> Dict[str, List[Metric]]:
        """Get metrics, optionally filtered by name"""
        if name:
            return {name: list(self.metrics.get(name, []))[-limit:]}

        result = {}
        for metric_name, metric_deque in self.metrics.items():
            result[metric_name] = list(metric_deque)[-limit:]
        return result

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current gauge values"""
        return dict(self.current_gauges)

    def get_alerts(self, active_only: bool = True) -> List[Alert]:
        """Get alerts"""
        if active_only:
            return list(self.alerts.values())

        all_alerts = list(self.alerts.values()) + self.resolved_alerts
        return sorted(all_alerts, key=lambda a: a.timestamp, reverse=True)

    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        active_alerts = len(self.alerts)
        resolved_alerts = len(self.resolved_alerts)

        severity_counts = defaultdict(int)
        for alert in self.alerts.values():
            severity_counts[alert.severity.value] += 1

        return {
            "active_alerts": active_alerts,
            "resolved_alerts": resolved_alerts,
            "total_alerts": active_alerts + resolved_alerts,
            "severity_breakdown": dict(severity_counts)
        }

    async def _cleanup_old_metrics(self) -> None:
        """Clean up old metrics beyond retention period"""
        cutoff_time = time.time() - self.retention_period

        for metric_deque in self.metrics.values():
            # Remove old metrics from deque
            while metric_deque and metric_deque[0].timestamp < cutoff_time:
                metric_deque.popleft()

    def export_metrics(self, format_type: str = "dict") -> Any:
        """Export metrics in specified format"""
        if format_type == "dict":
            return {
                name: [
                    {
                        "value": metric.value,
                        "timestamp": metric.timestamp,
                        "labels": metric.labels
                    }
                    for metric in metrics
                ]
                for name, metrics in self.get_metrics().items()
            }
        elif format_type == "prometheus":
            # Basic Prometheus format
            lines = []
            for name, metrics in self.get_metrics().items():
                if metrics:
                    latest = metrics[-1]
                    lines.append(f"# HELP {name} Metric {name}")
                    lines.append(f"# TYPE {name} gauge")
                    lines.append(f"{name} {latest.value}")
            return "\n".join(lines)

        return self.get_metrics()

    async def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        current_metrics = self.get_current_metrics()

        # Determine health based on key metrics
        health_score = 100

        # Deduct points for unhealthy nodes
        unhealthy_nodes = current_metrics.get("unhealthy_nodes", 0)
        if unhealthy_nodes > 0:
            health_score -= min(unhealthy_nodes * 20, 40)

        # Deduct points for high failure rate
        failure_rate = current_metrics.get("replication_failure_rate", 0)
        if failure_rate > 0.05:
            health_score -= min(failure_rate * 1000, 30)

        # Deduct points for active alerts
        active_alerts = len(self.alerts)
        if active_alerts > 0:
            health_score -= min(active_alerts * 10, 20)

        health_status = "healthy" if health_score >= 80 else "warning" if health_score >= 60 else "critical"

        return {
            "health_score": health_score,
            "health_status": health_status,
            "metrics": current_metrics,
            "active_alerts": active_alerts,
            "timestamp": time.time()
        }