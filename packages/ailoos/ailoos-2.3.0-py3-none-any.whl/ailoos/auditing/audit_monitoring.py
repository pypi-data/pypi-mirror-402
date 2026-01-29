"""
Advanced Audit Monitoring with real-time monitoring and alerts.
Provides live dashboards, anomaly detection, and automated alerting.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Callable, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from collections import defaultdict, deque
import statistics

from ..core.config import get_config
from ..core.logging import get_logger
from .audit_event import AuditEvent, AuditEventType, AuditSeverity
from .audit_query_engine import AuditQueryEngine, QuerySpec
from .audit_logger import AuditLogger


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MonitoringMetric(Enum):
    """Monitoring metrics."""
    EVENT_RATE = "event_rate"
    ERROR_RATE = "error_rate"
    SECURITY_INCIDENTS = "security_incidents"
    COMPLIANCE_VIOLATIONS = "compliance_violations"
    SYSTEM_PERFORMANCE = "system_performance"
    USER_ACTIVITY = "user_activity"


@dataclass
class AlertRule:
    """Alert rule configuration."""
    rule_id: str
    name: str
    description: str
    metric: MonitoringMetric
    condition: str  # Python expression to evaluate
    threshold: Any
    level: AlertLevel
    cooldown_minutes: int = 5
    enabled: bool = True
    last_triggered: Optional[datetime] = None


@dataclass
class Alert:
    """Alert instance."""
    alert_id: str
    rule_id: str
    level: AlertLevel
    title: str
    message: str
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None


@dataclass
class MetricSnapshot:
    """Snapshot of monitoring metrics."""
    timestamp: datetime
    metrics: Dict[str, Any]
    anomalies: List[Dict[str, Any]]


class AuditMonitoring:
    """
    Advanced audit monitoring with real-time dashboards and alerting.
    Provides live monitoring, anomaly detection, and automated alerts.
    """

    def __init__(self, query_engine: AuditQueryEngine, audit_logger: AuditLogger):
        self.query_engine = query_engine
        self.audit_logger = audit_logger
        self.logger = get_logger("audit_monitoring")

        # Alert rules
        self.alert_rules: Dict[str, AlertRule] = {}
        self._load_default_alert_rules()

        # Active alerts
        self.active_alerts: Dict[str, Alert] = {}

        # Metric history
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.metric_snapshots: List[MetricSnapshot] = []

        # Real-time subscribers
        self.subscribers: Set[Callable] = set()

        # Monitoring configuration
        self.monitoring_interval_seconds = 30
        self.anomaly_detection_window = 10  # Number of snapshots for anomaly detection
        self.max_snapshots = 100

        # Background tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None

        # Statistics
        self.stats = {
            'alerts_triggered': 0,
            'alerts_resolved': 0,
            'anomalies_detected': 0,
            'monitoring_cycles': 0
        }

    def _load_default_alert_rules(self):
        """Load default alert rules."""
        default_rules = [
            AlertRule(
                rule_id="high_error_rate",
                name="High Error Rate",
                description="Error rate exceeds threshold",
                metric=MonitoringMetric.ERROR_RATE,
                condition="value > threshold",
                threshold=0.05,  # 5%
                level=AlertLevel.WARNING,
                cooldown_minutes=10
            ),
            AlertRule(
                rule_id="security_incident_spike",
                name="Security Incident Spike",
                description="Sudden increase in security incidents",
                metric=MonitoringMetric.SECURITY_INCIDENTS,
                condition="value > threshold",
                threshold=5,
                level=AlertLevel.CRITICAL,
                cooldown_minutes=5
            ),
            AlertRule(
                rule_id="low_event_rate",
                name="Low Event Rate",
                description="Event rate below minimum threshold",
                metric=MonitoringMetric.EVENT_RATE,
                condition="value < threshold",
                threshold=1.0,  # events per minute
                level=AlertLevel.WARNING,
                cooldown_minutes=15
            ),
            AlertRule(
                rule_id="compliance_violation",
                name="Compliance Violation",
                description="Compliance violation detected",
                metric=MonitoringMetric.COMPLIANCE_VIOLATIONS,
                condition="value > threshold",
                threshold=0,
                level=AlertLevel.ERROR,
                cooldown_minutes=1
            ),
            AlertRule(
                rule_id="performance_degradation",
                name="Performance Degradation",
                description="System performance degradation detected",
                metric=MonitoringMetric.SYSTEM_PERFORMANCE,
                condition="value < threshold",
                threshold=0.8,  # 80% performance
                level=AlertLevel.WARNING,
                cooldown_minutes=5
            )
        ]

        for rule in default_rules:
            self.alert_rules[rule.rule_id] = rule

    def add_alert_rule(self, rule: AlertRule):
        """Add a custom alert rule."""
        self.alert_rules[rule.rule_id] = rule
        self.logger.info(f"Added alert rule: {rule.name}")

    def remove_alert_rule(self, rule_id: str):
        """Remove an alert rule."""
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
            self.logger.info(f"Removed alert rule: {rule_id}")

    def start_monitoring(self):
        """Start real-time monitoring."""
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())

        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        self.logger.info("Audit monitoring started")

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while True:
            try:
                await asyncio.sleep(self.monitoring_interval_seconds)

                # Collect metrics
                metrics = await self._collect_metrics()

                # Store metric snapshot
                snapshot = MetricSnapshot(
                    timestamp=datetime.now(),
                    metrics=metrics,
                    anomalies=[]
                )

                # Detect anomalies
                anomalies = self._detect_anomalies(snapshot)
                snapshot.anomalies = anomalies

                # Store snapshot
                self.metric_snapshots.append(snapshot)
                if len(self.metric_snapshots) > self.max_snapshots:
                    self.metric_snapshots.pop(0)

                # Update metric history
                for key, value in metrics.items():
                    self.metric_history[key].append((snapshot.timestamp, value))

                # Evaluate alert rules
                await self._evaluate_alert_rules(metrics)

                # Notify subscribers
                await self._notify_subscribers(snapshot)

                self.stats['monitoring_cycles'] += 1

            except Exception as e:
                self.logger.error(f"Monitoring cycle error: {e}")
                await asyncio.sleep(60)  # Wait before retry

    async def _collect_metrics(self) -> Dict[str, Any]:
        """Collect current monitoring metrics."""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        one_hour_ago = now - timedelta(hours=1)

        # Query recent events
        query_spec = QuerySpec(time_range=(one_minute_ago, now))
        result = await self.query_engine.execute_query(query_spec)

        events = result.events

        # Calculate metrics
        metrics = {
            'event_rate': len(events) / self.monitoring_interval_seconds * 60,  # events per minute
            'error_rate': len([e for e in events if not e.success]) / max(len(events), 1),
            'security_incidents': len([e for e in events if e.event_type == AuditEventType.SECURITY_ALERT]),
            'compliance_violations': len([e for e in events if e.details.get('compliance_violation', False)]),
            'system_performance': self._calculate_performance_score(events),
            'user_activity': len(set(e.user_id for e in events if e.user_id)),
            'total_events': len(events),
            'unique_resources': len(set(e.resource for e in events)),
            'severity_distribution': {
                'debug': len([e for e in events if e.severity == AuditSeverity.DEBUG]),
                'info': len([e for e in events if e.severity == AuditSeverity.INFO]),
                'warning': len([e for e in events if e.severity == AuditSeverity.WARNING]),
                'error': len([e for e in events if e.severity == AuditSeverity.ERROR]),
                'critical': len([e for e in events if e.severity == AuditSeverity.CRITICAL])
            }
        }

        return metrics

    def _calculate_performance_score(self, events: List[AuditEvent]) -> float:
        """Calculate system performance score."""
        if not events:
            return 1.0

        # Calculate average processing time
        processing_times = [e.processing_time_ms for e in events if e.processing_time_ms is not None]
        if processing_times:
            avg_time = statistics.mean(processing_times)
            # Score based on processing time (lower is better)
            # Assume 100ms is good performance
            return max(0, 1 - (avg_time / 1000))  # Convert to seconds

        return 0.8  # Default score

    def _detect_anomalies(self, snapshot: MetricSnapshot) -> List[Dict[str, Any]]:
        """Detect anomalies in metric snapshot."""
        anomalies = []

        if len(self.metric_snapshots) < self.anomaly_detection_window:
            return anomalies

        # Get recent snapshots
        recent = self.metric_snapshots[-self.anomaly_detection_window:]

        for metric_name, current_value in snapshot.metrics.items():
            if not isinstance(current_value, (int, float)):
                continue

            # Get historical values
            historical_values = []
            for snap in recent[:-1]:  # Exclude current snapshot
                if metric_name in snap.metrics:
                    historical_values.append(snap.metrics[metric_name])

            if len(historical_values) < 3:
                continue

            try:
                # Calculate statistics
                mean = statistics.mean(historical_values)
                stdev = statistics.stdev(historical_values) if len(historical_values) > 1 else 0

                if stdev > 0:
                    z_score = abs(current_value - mean) / stdev

                    # Anomaly if z-score > 3 (3 standard deviations)
                    if z_score > 3:
                        anomalies.append({
                            'metric': metric_name,
                            'current_value': current_value,
                            'expected_value': mean,
                            'z_score': z_score,
                            'severity': 'high' if z_score > 5 else 'medium',
                            'description': f"Anomalous {metric_name}: {current_value} (expected ~{mean:.2f})"
                        })

            except statistics.StatisticsError:
                continue

        self.stats['anomalies_detected'] += len(anomalies)
        return anomalies

    async def _evaluate_alert_rules(self, metrics: Dict[str, Any]):
        """Evaluate alert rules against current metrics."""
        now = datetime.now()

        for rule in self.alert_rules.values():
            if not rule.enabled:
                continue

            # Check cooldown
            if rule.last_triggered and (now - rule.last_triggered).seconds < rule.cooldown_minutes * 60:
                continue

            # Get metric value
            if rule.metric.value not in metrics:
                continue

            value = metrics[rule.metric.value]

            # Evaluate condition
            try:
                # Simple condition evaluation
                condition_met = False
                if rule.condition == "value > threshold":
                    condition_met = value > rule.threshold
                elif rule.condition == "value < threshold":
                    condition_met = value < rule.threshold
                elif rule.condition == "value >= threshold":
                    condition_met = value >= rule.threshold
                elif rule.condition == "value <= threshold":
                    condition_met = value <= rule.threshold
                elif rule.condition == "value == threshold":
                    condition_met = value == rule.threshold

                if condition_met:
                    await self._trigger_alert(rule, value, metrics)

            except Exception as e:
                self.logger.error(f"Error evaluating alert rule {rule.rule_id}: {e}")

    async def _trigger_alert(self, rule: AlertRule, value: Any, metrics: Dict[str, Any]):
        """Trigger an alert."""
        alert_id = f"alert_{rule.rule_id}_{int(datetime.now().timestamp())}"

        alert = Alert(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            level=rule.level,
            title=f"{rule.name}: {value}",
            message=f"{rule.description} - Current value: {value}, Threshold: {rule.threshold}",
            triggered_at=datetime.now(),
            metadata={
                'metric': rule.metric.value,
                'current_value': value,
                'threshold': rule.threshold,
                'all_metrics': metrics
            }
        )

        self.active_alerts[alert_id] = alert
        rule.last_triggered = alert.triggered_at

        self.stats['alerts_triggered'] += 1

        # Log alert as audit event
        await self.audit_logger.log_event(
            event_type=AuditEventType.SECURITY_ALERT,
            resource="audit_monitoring",
            action="alert_triggered",
            details={
                'alert_id': alert_id,
                'rule_id': rule.rule_id,
                'level': rule.level.value,
                'title': alert.title,
                'message': alert.message
            },
            severity=AuditSeverity.WARNING if rule.level == AlertLevel.WARNING else AuditSeverity.ERROR
        )

        self.logger.warning(f"🚨 Alert triggered: {alert.title}")

        # Auto-resolve after cooldown if not acknowledged
        asyncio.create_task(self._auto_resolve_alert(alert_id, rule.cooldown_minutes))

    async def _auto_resolve_alert(self, alert_id: str, delay_minutes: int):
        """Auto-resolve alert after delay."""
        await asyncio.sleep(delay_minutes * 60)

        if alert_id in self.active_alerts and not self.active_alerts[alert_id].acknowledged:
            alert = self.active_alerts[alert_id]
            alert.resolved_at = datetime.now()

            self.stats['alerts_resolved'] += 1
            self.logger.info(f"✅ Alert auto-resolved: {alert.title}")

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Acknowledge an alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.acknowledged = True
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.now()

            self.logger.info(f"👁️ Alert acknowledged by {acknowledged_by}: {alert.title}")

    def resolve_alert(self, alert_id: str):
        """Manually resolve an alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved_at = datetime.now()

            self.stats['alerts_resolved'] += 1
            self.logger.info(f"✅ Alert manually resolved: {alert.title}")

    async def _notify_subscribers(self, snapshot: MetricSnapshot):
        """Notify subscribers of new snapshot."""
        for subscriber in self.subscribers:
            try:
                await subscriber(snapshot)
            except Exception as e:
                self.logger.error(f"Error notifying subscriber: {e}")

    def subscribe(self, callback: Callable):
        """Subscribe to real-time monitoring updates."""
        self.subscribers.add(callback)

    def unsubscribe(self, callback: Callable):
        """Unsubscribe from monitoring updates."""
        self.subscribers.discard(callback)

    async def _cleanup_loop(self):
        """Cleanup old data periodically."""
        while True:
            try:
                await asyncio.sleep(3600)  # Clean up every hour

                # Remove old resolved alerts (older than 7 days)
                cutoff_date = datetime.now() - timedelta(days=7)
                old_alerts = [
                    alert_id for alert_id, alert in self.active_alerts.items()
                    if alert.resolved_at and alert.resolved_at < cutoff_date
                ]

                for alert_id in old_alerts:
                    del self.active_alerts[alert_id]

                # Clean up old metric history (keep last 24 hours)
                cutoff_time = datetime.now() - timedelta(hours=24)
                for metric_queue in self.metric_history.values():
                    while metric_queue and metric_queue[0][0] < cutoff_time:
                        metric_queue.popleft()

                self.logger.debug(f"Cleaned up {len(old_alerts)} old alerts")

            except Exception as e:
                self.logger.error(f"Cleanup error: {e}")

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current monitoring metrics."""
        if not self.metric_snapshots:
            return {}

        return self.metric_snapshots[-1].metrics.copy()

    def get_metric_history(self, metric: str, hours: int = 24) -> List[Tuple[datetime, Any]]:
        """Get historical data for a metric."""
        if metric not in self.metric_history:
            return []

        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [(ts, val) for ts, val in self.metric_history[metric] if ts >= cutoff_time]

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return [alert for alert in self.active_alerts.values() if alert.resolved_at is None]

    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            alert for alert in self.active_alerts.values()
            if alert.triggered_at >= cutoff_time
        ]

    def get_anomaly_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get anomaly detection history."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        anomalies = []

        for snapshot in self.metric_snapshots:
            if snapshot.timestamp >= cutoff_time:
                anomalies.extend(snapshot.anomalies)

        return anomalies

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        current_metrics = self.get_current_metrics()
        active_alerts = self.get_active_alerts()

        # Get recent trends
        event_rate_history = self.get_metric_history('event_rate', hours=1)
        error_rate_history = self.get_metric_history('error_rate', hours=1)

        return {
            'current_metrics': current_metrics,
            'active_alerts': [self._alert_to_dict(alert) for alert in active_alerts],
            'alert_summary': {
                'total_active': len(active_alerts),
                'by_level': {
                    'info': len([a for a in active_alerts if a.level == AlertLevel.INFO]),
                    'warning': len([a for a in active_alerts if a.level == AlertLevel.WARNING]),
                    'error': len([a for a in active_alerts if a.level == AlertLevel.ERROR]),
                    'critical': len([a for a in active_alerts if a.level == AlertLevel.CRITICAL])
                }
            },
            'trends': {
                'event_rate': [{'timestamp': ts.isoformat(), 'value': val} for ts, val in event_rate_history],
                'error_rate': [{'timestamp': ts.isoformat(), 'value': val} for ts, val in error_rate_history]
            },
            'anomalies_recent': self.get_anomaly_history(hours=1),
            'system_status': self._calculate_system_status(current_metrics, active_alerts)
        }

    def _alert_to_dict(self, alert: Alert) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            'alert_id': alert.alert_id,
            'rule_id': alert.rule_id,
            'level': alert.level.value,
            'title': alert.title,
            'message': alert.message,
            'triggered_at': alert.triggered_at.isoformat(),
            'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
            'acknowledged': alert.acknowledged,
            'acknowledged_by': alert.acknowledged_by,
            'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            'metadata': alert.metadata
        }

    def _calculate_system_status(self, metrics: Dict[str, Any], alerts: List[Alert]) -> str:
        """Calculate overall system status."""
        if not metrics:
            return "unknown"

        # Check for critical alerts
        critical_alerts = [a for a in alerts if a.level == AlertLevel.CRITICAL]
        if critical_alerts:
            return "critical"

        # Check error rate
        error_rate = metrics.get('error_rate', 0)
        if error_rate > 0.1:  # 10%
            return "error"

        # Check performance
        performance = metrics.get('system_performance', 1.0)
        if performance < 0.5:
            return "warning"

        # Check for any warnings
        warning_alerts = [a for a in alerts if a.level == AlertLevel.WARNING]
        if warning_alerts:
            return "warning"

        return "healthy"

    def stop_monitoring(self):
        """Stop monitoring."""
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()

        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()

        self.logger.info("Audit monitoring stopped")

    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        return {
            **self.stats,
            'active_alerts': len(self.get_active_alerts()),
            'configured_rules': len(self.alert_rules),
            'active_subscribers': len(self.subscribers),
            'monitoring_active': self._monitoring_task is not None and not self._monitoring_task.done()
        }