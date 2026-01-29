#!/usr/bin/env python3
"""
Real-time Monitoring System for Ailoos
Sistema avanzado de monitoreo en tiempo real con métricas, alertas y dashboards
"""

import asyncio
import logging
import time
import threading
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import psutil
import socket
import aiohttp
from collections import deque, defaultdict
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Tipos de métricas disponibles"""
    COUNTER = "counter"           # Valor que solo aumenta
    GAUGE = "gauge"              # Valor que puede subir/bajar
    HISTOGRAM = "histogram"      # Distribución de valores
    SUMMARY = "summary"          # Estadísticas resumidas

class AlertSeverity(Enum):
    """Severidades de alertas"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class MetricData:
    """Datos de una métrica"""
    name: str
    type: MetricType
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AlertRule:
    """Regla de alerta"""
    rule_id: str
    name: str
    description: str
    metric_name: str
    condition: str  # e.g., "value > 90", "rate > 10"
    severity: AlertSeverity
    cooldown_minutes: int = 5
    enabled: bool = True
    last_triggered: Optional[datetime] = None

@dataclass
class Alert:
    """Alerta generada"""
    alert_id: str
    rule_id: str
    severity: AlertSeverity
    message: str
    value: float
    threshold: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class MetricsCollector:
    """Colector de métricas del sistema"""

    def __init__(self):
        self.metrics: Dict[str, MetricData] = {}
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.collection_interval = 5  # seconds

        # System metrics collectors
        self.collectors = {
            'cpu_usage': self._collect_cpu_usage,
            'memory_usage': self._collect_memory_usage,
            'disk_usage': self._collect_disk_usage,
            'network_io': self._collect_network_io,
            'system_load': self._collect_system_load,
            'process_count': self._collect_process_count
        }

    async def collect_system_metrics(self):
        """Collect all system metrics"""
        timestamp = datetime.now()

        for metric_name, collector_func in self.collectors.items():
            try:
                value = await collector_func()
                if value is not None:
                    metric = MetricData(
                        name=metric_name,
                        type=MetricType.GAUGE,
                        value=value,
                        timestamp=timestamp,
                        labels={'host': socket.gethostname()}
                    )

                    self.metrics[metric_name] = metric
                    self.metric_history[metric_name].append(metric)

            except Exception as e:
                logger.warning(f"Failed to collect metric {metric_name}: {e}")

    async def _collect_cpu_usage(self) -> float:
        """Collect CPU usage percentage"""
        return psutil.cpu_percent(interval=1)

    async def _collect_memory_usage(self) -> float:
        """Collect memory usage percentage"""
        return psutil.virtual_memory().percent

    async def _collect_disk_usage(self) -> float:
        """Collect disk usage percentage"""
        return psutil.disk_usage('/').percent

    async def _collect_network_io(self) -> float:
        """Collect network I/O rate (bytes/sec)"""
        net_io = psutil.net_io_counters()
        return net_io.bytes_sent + net_io.bytes_recv

    async def _collect_system_load(self) -> float:
        """Collect system load average"""
        try:
            return psutil.getloadavg()[0]
        except AttributeError:  # Windows
            return psutil.cpu_percent() / 100.0

    async def _collect_process_count(self) -> int:
        """Collect number of running processes"""
        return len(psutil.pids())

    def get_metric(self, name: str) -> Optional[MetricData]:
        """Get current metric value"""
        return self.metrics.get(name)

    def get_metric_history(self, name: str, limit: int = 100) -> List[MetricData]:
        """Get metric history"""
        return list(self.metric_history[name])[-limit:]

    def calculate_metric_stats(self, name: str, window_minutes: int = 5) -> Dict[str, float]:
        """Calculate statistics for a metric over a time window"""
        history = self.get_metric_history(name)
        if not history:
            return {}

        # Filter by time window
        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        recent_values = [m.value for m in history if m.timestamp > cutoff]

        if not recent_values:
            return {}

        return {
            'mean': np.mean(recent_values),
            'median': np.median(recent_values),
            'std': np.std(recent_values),
            'min': np.min(recent_values),
            'max': np.max(recent_values),
            'count': len(recent_values)
        }

class AlertManager:
    """Gestor de alertas y reglas"""

    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.alert_callbacks: List[Callable[[Alert], None]] = []

    def add_rule(self, rule: AlertRule):
        """Add alert rule"""
        self.rules[rule.rule_id] = rule
        logger.info(f"Added alert rule: {rule.name}")

    def remove_rule(self, rule_id: str):
        """Remove alert rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed alert rule: {rule_id}")

    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Add callback for alert notifications"""
        self.alert_callbacks.append(callback)

    async def evaluate_rules(self, metrics_collector: MetricsCollector):
        """Evaluate all alert rules against current metrics"""
        for rule in self.rules.values():
            if not rule.enabled:
                continue

            # Check cooldown
            if rule.last_triggered and \
               (datetime.now() - rule.last_triggered).total_seconds() < rule.cooldown_minutes * 60:
                continue

            try:
                # Get metric value
                metric = metrics_collector.get_metric(rule.metric_name)
                if not metric:
                    continue

                # Evaluate condition
                if self._evaluate_condition(rule.condition, metric.value):
                    await self._trigger_alert(rule, metric)

            except Exception as e:
                logger.error(f"Error evaluating rule {rule.rule_id}: {e}")

    def _evaluate_condition(self, condition: str, value: float) -> bool:
        """Evaluate alert condition"""
        try:
            # Simple condition evaluation (e.g., "value > 90")
            condition = condition.replace('value', str(value))

            # Safe evaluation with limited globals
            allowed_names = {
                "value": value,
                "__builtins__": {},
            }

            return bool(eval(condition, allowed_names))
        except Exception as e:
            logger.warning(f"Failed to evaluate condition '{condition}': {e}")
            return False

    async def _trigger_alert(self, rule: AlertRule, metric: MetricData):
        """Trigger an alert"""
        alert = Alert(
            alert_id=f"alert_{int(time.time())}_{rule.rule_id}",
            rule_id=rule.rule_id,
            severity=rule.severity,
            message=f"{rule.name}: {rule.description} (value: {metric.value:.2f})",
            value=metric.value,
            threshold=rule.condition,
            timestamp=datetime.now()
        )

        self.active_alerts[alert.alert_id] = alert
        self.alert_history.append(alert)
        rule.last_triggered = datetime.now()

        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

        logger.warning(f"🚨 Alert triggered: {alert.message}")

    def resolve_alert(self, alert_id: str):
        """Resolve an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()

            logger.info(f"✅ Alert resolved: {alert.message}")

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        return self.alert_history[-limit:]

class DashboardManager:
    """Gestor de dashboards y visualización"""

    def __init__(self):
        self.dashboards: Dict[str, Dict[str, Any]] = {}
        self.widgets: Dict[str, Dict[str, Any]] = {}

    def create_dashboard(self, dashboard_id: str, name: str, description: str = ""):
        """Create a new dashboard"""
        self.dashboards[dashboard_id] = {
            'name': name,
            'description': description,
            'widgets': [],
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }

    def add_widget_to_dashboard(self, dashboard_id: str, widget_id: str):
        """Add widget to dashboard"""
        if dashboard_id in self.dashboards:
            if widget_id not in self.dashboards[dashboard_id]['widgets']:
                self.dashboards[dashboard_id]['widgets'].append(widget_id)
                self.dashboards[dashboard_id]['updated_at'] = datetime.now()

    def create_metric_widget(self, widget_id: str, metric_name: str,
                           widget_type: str = "line_chart", title: str = ""):
        """Create a metric visualization widget"""
        self.widgets[widget_id] = {
            'type': widget_type,
            'metric': metric_name,
            'title': title or f"Metric: {metric_name}",
            'config': {
                'time_range': '1h',
                'refresh_interval': 30
            },
            'created_at': datetime.now()
        }

    def get_dashboard_data(self, dashboard_id: str,
                          metrics_collector: MetricsCollector) -> Dict[str, Any]:
        """Get dashboard data with current metrics"""
        if dashboard_id not in self.dashboards:
            return {}

        dashboard = self.dashboards[dashboard_id].copy()
        dashboard['widgets_data'] = []

        for widget_id in dashboard['widgets']:
            if widget_id in self.widgets:
                widget = self.widgets[widget_id].copy()
                metric_name = widget.get('metric')

                if metric_name:
                    # Get current metric and history
                    current_metric = metrics_collector.get_metric(metric_name)
                    history = metrics_collector.get_metric_history(metric_name, 50)
                    stats = metrics_collector.calculate_metric_stats(metric_name)

                    widget['current_value'] = current_metric.value if current_metric else None
                    widget['history'] = [
                        {'timestamp': m.timestamp.isoformat(), 'value': m.value}
                        for m in history
                    ]
                    widget['stats'] = stats

                dashboard['widgets_data'].append(widget)

        return dashboard

class RealtimeMonitor:
    """Sistema completo de monitoreo en tiempo real"""

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.dashboard_manager = DashboardManager()

        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None

        # External integrations
        self.external_endpoints: List[str] = []
        self.webhook_urls: List[str] = []

        # Initialize default alert rules
        self._setup_default_alert_rules()

        # Initialize default dashboard
        self._setup_default_dashboard()

        logger.info("📊 Real-time Monitor initialized")

    def _setup_default_alert_rules(self):
        """Setup default alert rules"""
        rules = [
            AlertRule(
                rule_id="high_cpu",
                name="High CPU Usage",
                description="CPU usage is above 90%",
                metric_name="cpu_usage",
                condition="value > 90",
                severity=AlertSeverity.WARNING
            ),
            AlertRule(
                rule_id="high_memory",
                name="High Memory Usage",
                description="Memory usage is above 90%",
                metric_name="memory_usage",
                condition="value > 90",
                severity=AlertSeverity.ERROR
            ),
            AlertRule(
                rule_id="disk_full",
                name="Disk Almost Full",
                description="Disk usage is above 95%",
                metric_name="disk_usage",
                condition="value > 95",
                severity=AlertSeverity.CRITICAL
            ),
            AlertRule(
                rule_id="high_load",
                name="High System Load",
                description="System load is above 5.0",
                metric_name="system_load",
                condition="value > 5.0",
                severity=AlertSeverity.WARNING
            )
        ]

        for rule in rules:
            self.alert_manager.add_rule(rule)

    def _setup_default_dashboard(self):
        """Setup default system dashboard"""
        self.dashboard_manager.create_dashboard(
            "system_overview",
            "System Overview",
            "Real-time system metrics and performance indicators"
        )

        # Create widgets
        widgets = [
            ("cpu_widget", "cpu_usage", "line_chart", "CPU Usage (%)"),
            ("memory_widget", "memory_usage", "line_chart", "Memory Usage (%)"),
            ("disk_widget", "disk_usage", "gauge", "Disk Usage (%)"),
            ("network_widget", "network_io", "line_chart", "Network I/O"),
            ("load_widget", "system_load", "line_chart", "System Load"),
        ]

        for widget_id, metric, chart_type, title in widgets:
            self.dashboard_manager.create_metric_widget(widget_id, metric, chart_type, title)
            self.dashboard_manager.add_widget_to_dashboard("system_overview", widget_id)

    def start_monitoring(self):
        """Start real-time monitoring"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()

        logger.info("▶️ Real-time monitoring started")

    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)

        logger.info("⏹️ Real-time monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while self.monitoring_active:
            try:
                # Collect metrics
                loop.run_until_complete(self.metrics_collector.collect_system_metrics())

                # Evaluate alerts
                loop.run_until_complete(self.alert_manager.evaluate_rules(self.metrics_collector))

                # Send metrics to external endpoints
                loop.run_until_complete(self._send_metrics_to_external())

                time.sleep(self.metrics_collector.collection_interval)

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(5)  # Wait before retrying

    async def _send_metrics_to_external(self):
        """Send metrics to external monitoring endpoints"""
        if not self.external_endpoints:
            return

        metrics_data = {
            'timestamp': datetime.now().isoformat(),
            'metrics': {
                name: {
                    'value': metric.value,
                    'type': metric.type.value,
                    'labels': metric.labels
                }
                for name, metric in self.metrics_collector.metrics.items()
            }
        }

        for endpoint in self.external_endpoints:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(endpoint, json=metrics_data, timeout=5) as response:
                        if response.status != 200:
                            logger.warning(f"Failed to send metrics to {endpoint}: {response.status}")
            except Exception as e:
                logger.warning(f"Error sending metrics to {endpoint}: {e}")

    def add_external_endpoint(self, endpoint_url: str):
        """Add external monitoring endpoint"""
        if endpoint_url not in self.external_endpoints:
            self.external_endpoints.append(endpoint_url)
            logger.info(f"Added external monitoring endpoint: {endpoint_url}")

    def add_alert_webhook(self, webhook_url: str):
        """Add webhook for alert notifications"""
        if webhook_url not in self.webhook_urls:
            self.webhook_urls.append(webhook_url)

            # Add callback for webhook notifications
            async def webhook_callback(alert: Alert):
                try:
                    payload = {
                        'alert_id': alert.alert_id,
                        'severity': alert.severity.value,
                        'message': alert.message,
                        'value': alert.value,
                        'timestamp': alert.timestamp.isoformat()
                    }

                    async with aiohttp.ClientSession() as session:
                        async with session.post(webhook_url, json=payload, timeout=10) as response:
                            if response.status != 200:
                                logger.warning(f"Webhook failed: {response.status}")
                except Exception as e:
                    logger.error(f"Webhook error: {e}")

            self.alert_manager.add_alert_callback(lambda a: asyncio.create_task(webhook_callback(a)))

            logger.info(f"Added alert webhook: {webhook_url}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'monitoring_active': self.monitoring_active,
            'current_metrics': {
                name: {
                    'value': metric.value,
                    'timestamp': metric.timestamp.isoformat(),
                    'type': metric.type.value
                }
                for name, metric in self.metrics_collector.metrics.items()
            },
            'active_alerts': [
                {
                    'id': alert.alert_id,
                    'severity': alert.severity.value,
                    'message': alert.message,
                    'timestamp': alert.timestamp.isoformat()
                }
                for alert in self.alert_manager.get_active_alerts()
            ],
            'recent_alerts': len(self.alert_manager.get_alert_history(10)),
            'dashboards': list(self.dashboard_manager.dashboards.keys()),
            'external_endpoints': len(self.external_endpoints),
            'webhooks': len(self.webhook_urls)
        }

    def get_dashboard_data(self, dashboard_id: str) -> Dict[str, Any]:
        """Get dashboard data"""
        return self.dashboard_manager.get_dashboard_data(dashboard_id, self.metrics_collector)

    def create_custom_alert_rule(self, name: str, metric_name: str, condition: str,
                               severity: AlertSeverity, description: str = ""):
        """Create custom alert rule"""
        rule_id = f"custom_{int(time.time())}_{name.lower().replace(' ', '_')}"

        rule = AlertRule(
            rule_id=rule_id,
            name=name,
            description=description or f"Custom alert for {metric_name}",
            metric_name=metric_name,
            condition=condition,
            severity=severity
        )

        self.alert_manager.add_rule(rule)
        return rule_id

# Global monitor instance
monitor_instance = None

def get_realtime_monitor() -> RealtimeMonitor:
    """Get global real-time monitor instance"""
    global monitor_instance
    if monitor_instance is None:
        monitor_instance = RealtimeMonitor()
    return monitor_instance

if __name__ == '__main__':
    # Demo
    monitor = get_realtime_monitor()

    print("📊 Real-time Monitor Demo")
    print("=" * 50)

    # Start monitoring
    monitor.start_monitoring()
    print("▶️ Monitoring started")

    try:
        # Wait a bit for metrics collection
        time.sleep(10)

        # Get system status
        status = monitor.get_system_status()
        print(f"📈 Current CPU usage: {status['current_metrics'].get('cpu_usage', {}).get('value', 'N/A')}%")
        print(f"📈 Current memory usage: {status['current_metrics'].get('memory_usage', {}).get('value', 'N/A')}%")

        # Get dashboard data
        dashboard = monitor.get_dashboard_data("system_overview")
        print(f"📊 Dashboard has {len(dashboard.get('widgets_data', []))} widgets")

        # Create custom alert
        rule_id = monitor.create_custom_alert_rule(
            "Low Disk Space",
            "disk_usage",
            "value > 50",  # Lower threshold for demo
            AlertSeverity.WARNING,
            "Disk usage is getting high"
        )
        print(f"🔔 Created custom alert rule: {rule_id}")

        # Wait for potential alerts
        time.sleep(5)

        # Check for alerts
        alerts = monitor.get_system_status()['active_alerts']
        print(f"🚨 Active alerts: {len(alerts)}")

    finally:
        monitor.stop_monitoring()
        print("⏹️ Monitoring stopped")

    print("🎉 Real-time Monitor Demo completed!")