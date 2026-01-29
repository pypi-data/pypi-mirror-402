import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import json
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class MonitoringBackend(Enum):
    PROMETHEUS = "prometheus"
    GRAFANA = "grafana"
    JAEGER = "jaeger"
    ELASTICSEARCH = "elasticsearch"
    INFLUXDB = "influxdb"

@dataclass
class Metric:
    name: str
    type: MetricType
    value: Any
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    description: str = ""

@dataclass
class TraceSpan:
    trace_id: str
    span_id: str
    name: str
    parent_span_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration: Optional[float] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class LogEntry:
    timestamp: float = field(default_factory=time.time)
    level: str = "INFO"
    message: str
    service: str = ""
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AlertRule:
    name: str
    condition: str
    threshold: float
    duration: int  # seconds
    severity: str = "warning"
    description: str = ""

class MetricsCollector:
    """Collect and aggregate metrics"""

    def __init__(self):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.aggregates: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def record_metric(self, metric: Metric):
        """Record a metric"""
        async with self._lock:
            key = f"{metric.name}_{json.dumps(metric.labels, sort_keys=True)}"
            self.metrics[key].append(metric)

            # Update aggregates
            await self._update_aggregates(metric.name, metric)

    async def get_metric(self, name: str, labels: Dict[str, str] = None) -> Optional[Metric]:
        """Get the latest metric value"""
        async with self._lock:
            if labels:
                key = f"{name}_{json.dumps(labels, sort_keys=True)}"
            else:
                # Find any metric with this name
                matching_keys = [k for k in self.metrics.keys() if k.startswith(f"{name}_")]
                key = matching_keys[0] if matching_keys else None

            if key and self.metrics[key]:
                return self.metrics[key][-1]
            return None

    async def get_metric_history(self, name: str, labels: Dict[str, str] = None,
                               time_range: int = 300) -> List[Metric]:
        """Get metric history for the specified time range"""
        async with self._lock:
            cutoff_time = time.time() - time_range

            if labels:
                key = f"{name}_{json.dumps(labels, sort_keys=True)}"
                if key in self.metrics:
                    return [m for m in self.metrics[key] if m.timestamp >= cutoff_time]
            else:
                # Aggregate all metrics with this name
                result = []
                for key, metrics in self.metrics.items():
                    if key.startswith(f"{name}_"):
                        result.extend([m for m in metrics if m.timestamp >= cutoff_time])
                return sorted(result, key=lambda m: m.timestamp)

            return []

    async def get_aggregated_metrics(self, name: str) -> Dict[str, Any]:
        """Get aggregated metrics for a metric name"""
        async with self._lock:
            return self.aggregates.get(name, {})

    async def _update_aggregates(self, name: str, metric: Metric):
        """Update aggregated statistics for a metric"""
        if name not in self.aggregates:
            self.aggregates[name] = {
                "count": 0,
                "sum": 0,
                "min": float('inf'),
                "max": float('-inf'),
                "avg": 0,
                "last_value": 0,
                "last_timestamp": 0
            }

        agg = self.aggregates[name]
        agg["count"] += 1
        agg["last_value"] = metric.value
        agg["last_timestamp"] = metric.timestamp

        if isinstance(metric.value, (int, float)):
            agg["sum"] += metric.value
            agg["min"] = min(agg["min"], metric.value)
            agg["max"] = max(agg["max"], metric.value)
            agg["avg"] = agg["sum"] / agg["count"]

class TracingSystem:
    """Distributed tracing system"""

    def __init__(self):
        self.active_spans: Dict[str, TraceSpan] = {}
        self.completed_traces: Dict[str, List[TraceSpan]] = {}
        self._lock = asyncio.Lock()

    async def start_span(self, name: str, trace_id: Optional[str] = None,
                        parent_span_id: Optional[str] = None,
                        tags: Dict[str, Any] = None) -> str:
        """Start a new trace span"""
        async with self._lock:
            span_id = self._generate_id()
            if not trace_id:
                trace_id = self._generate_id()

            span = TraceSpan(
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                name=name,
                tags=tags or {}
            )

            self.active_spans[span_id] = span
            return span_id

    async def finish_span(self, span_id: str, tags: Dict[str, Any] = None):
        """Finish a trace span"""
        async with self._lock:
            if span_id not in self.active_spans:
                return

            span = self.active_spans[span_id]
            span.end_time = time.time()
            span.duration = span.end_time - span.start_time

            if tags:
                span.tags.update(tags)

            # Move to completed traces
            if span.trace_id not in self.completed_traces:
                self.completed_traces[span.trace_id] = []
            self.completed_traces[span.trace_id].append(span)

            del self.active_spans[span_id]

    async def add_span_log(self, span_id: str, message: str, fields: Dict[str, Any] = None):
        """Add a log entry to a span"""
        async with self._lock:
            if span_id in self.active_spans:
                span = self.active_spans[span_id]
                log_entry = {
                    "timestamp": time.time(),
                    "message": message,
                    "fields": fields or {}
                }
                span.logs.append(log_entry)

    async def get_trace(self, trace_id: str) -> List[TraceSpan]:
        """Get all spans for a trace"""
        async with self._lock:
            return self.completed_traces.get(trace_id, [])

    async def get_active_spans(self) -> List[TraceSpan]:
        """Get all active spans"""
        async with self._lock:
            return list(self.active_spans.values())

    def _generate_id(self) -> str:
        """Generate a unique ID"""
        return hex(int(time.time() * 1000000))[2:]

class LogAggregator:
    """Centralized logging system"""

    def __init__(self):
        self.logs: deque = deque(maxlen=10000)
        self._lock = asyncio.Lock()

    async def log(self, entry: LogEntry):
        """Add a log entry"""
        async with self._lock:
            self.logs.append(entry)

    async def get_logs(self, service: str = None, level: str = None,
                      time_range: int = 3600) -> List[LogEntry]:
        """Get filtered logs"""
        async with self._lock:
            cutoff_time = time.time() - time_range
            filtered_logs = []

            for log in self.logs:
                if log.timestamp < cutoff_time:
                    continue
                if service and log.service != service:
                    continue
                if level and log.level != level:
                    continue
                filtered_logs.append(log)

            return filtered_logs

    async def search_logs(self, query: str, time_range: int = 3600) -> List[LogEntry]:
        """Search logs by query"""
        async with self._lock:
            cutoff_time = time.time() - time_range
            matching_logs = []

            for log in self.logs:
                if log.timestamp < cutoff_time:
                    continue
                if query.lower() in log.message.lower():
                    matching_logs.append(log)

            return matching_logs

class AlertManager:
    """Alert management system"""

    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
        self.alert_callbacks: List[Callable] = []
        self._lock = asyncio.Lock()

    async def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule"""
        async with self._lock:
            self.rules[rule.name] = rule

    async def remove_alert_rule(self, name: str):
        """Remove an alert rule"""
        async with self._lock:
            if name in self.rules:
                del self.rules[name]

    async def check_alerts(self, metrics_collector: MetricsCollector):
        """Check all alert rules against current metrics"""
        async with self._lock:
            for rule_name, rule in self.rules.items():
                alert_key = f"{rule_name}_{rule.condition}"

                # Evaluate condition (simplified)
                if await self._evaluate_condition(rule, metrics_collector):
                    if alert_key not in self.active_alerts:
                        # Trigger new alert
                        alert = {
                            "rule_name": rule_name,
                            "severity": rule.severity,
                            "description": rule.description,
                            "triggered_at": time.time(),
                            "value": await self._get_metric_value(rule, metrics_collector)
                        }
                        self.active_alerts[alert_key] = alert

                        # Notify callbacks
                        for callback in self.alert_callbacks:
                            try:
                                await callback(alert)
                            except Exception as e:
                                logger.error(f"Error in alert callback: {e}")
                else:
                    # Clear alert if it exists
                    if alert_key in self.active_alerts:
                        del self.active_alerts[alert_key]

    async def add_alert_callback(self, callback: Callable):
        """Add alert callback"""
        async with self._lock:
            self.alert_callbacks.append(callback)

    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        async with self._lock:
            return list(self.active_alerts.values())

    async def _evaluate_condition(self, rule: AlertRule, metrics_collector: MetricsCollector) -> bool:
        """Evaluate alert condition"""
        # Simplified condition evaluation
        try:
            # Parse simple conditions like "metric_name > threshold"
            parts = rule.condition.split()
            if len(parts) == 3:
                metric_name, operator, threshold_str = parts
                threshold = float(threshold_str)

                metric = await metrics_collector.get_metric(metric_name)
                if metric and isinstance(metric.value, (int, float)):
                    if operator == ">":
                        return metric.value > threshold
                    elif operator == "<":
                        return metric.value < threshold
                    elif operator == ">=":
                        return metric.value >= threshold
                    elif operator == "<=":
                        return metric.value <= threshold
                    elif operator == "==":
                        return metric.value == threshold
        except Exception as e:
            logger.error(f"Error evaluating condition {rule.condition}: {e}")

        return False

    async def _get_metric_value(self, rule: AlertRule, metrics_collector: MetricsCollector) -> Any:
        """Get current metric value for alert"""
        try:
            parts = rule.condition.split()
            if len(parts) >= 1:
                metric_name = parts[0]
                metric = await metrics_collector.get_metric(metric_name)
                return metric.value if metric else None
        except Exception:
            pass
        return None

class MeshMonitoring:
    """Complete mesh monitoring and observability system"""

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.tracing_system = TracingSystem()
        self.log_aggregator = LogAggregator()
        self.alert_manager = AlertManager()
        self.backends: Dict[MonitoringBackend, Any] = {}
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False

    async def start_monitoring(self):
        """Start the monitoring system"""
        if self._running:
            return

        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Mesh monitoring started")

    async def stop_monitoring(self):
        """Stop the monitoring system"""
        if not self._running:
            return

        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Mesh monitoring stopped")

    async def record_request_metric(self, service: str, method: str, status_code: int,
                                  response_time: float, request_size: int = 0,
                                  response_size: int = 0):
        """Record HTTP request metrics"""
        labels = {"service": service, "method": method, "status": str(status_code)}

        await self.metrics_collector.record_metric(Metric(
            name="http_requests_total",
            type=MetricType.COUNTER,
            value=1,
            labels=labels,
            description="Total number of HTTP requests"
        ))

        await self.metrics_collector.record_metric(Metric(
            name="http_request_duration_seconds",
            type=MetricType.HISTOGRAM,
            value=response_time,
            labels={"service": service, "method": method},
            description="HTTP request duration in seconds"
        ))

        if request_size > 0:
            await self.metrics_collector.record_metric(Metric(
                name="http_request_size_bytes",
                type=MetricType.HISTOGRAM,
                value=request_size,
                labels={"service": service},
                description="HTTP request size in bytes"
            ))

        if response_size > 0:
            await self.metrics_collector.record_metric(Metric(
                name="http_response_size_bytes",
                type=MetricType.HISTOGRAM,
                value=response_size,
                labels={"service": service},
                description="HTTP response size in bytes"
            ))

    async def record_service_health(self, service: str, healthy: bool):
        """Record service health status"""
        await self.metrics_collector.record_metric(Metric(
            name="service_health_status",
            type=MetricType.GAUGE,
            value=1 if healthy else 0,
            labels={"service": service},
            description="Service health status (1=healthy, 0=unhealthy)"
        ))

    async def log_request(self, service: str, level: str, message: str,
                         trace_id: str = None, span_id: str = None,
                         metadata: Dict[str, Any] = None):
        """Log a request-related message"""
        await self.log_aggregator.log(LogEntry(
            level=level,
            message=message,
            service=service,
            trace_id=trace_id,
            span_id=span_id,
            metadata=metadata or {}
        ))

    async def start_request_trace(self, service: str, operation: str,
                                trace_id: str = None, parent_span_id: str = None) -> str:
        """Start tracing a request"""
        return await self.tracing_system.start_span(
            name=f"{service}.{operation}",
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            tags={"service": service, "operation": operation}
        )

    async def finish_request_trace(self, span_id: str, tags: Dict[str, Any] = None):
        """Finish tracing a request"""
        await self.tracing_system.finish_span(span_id, tags)

    async def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule"""
        await self.alert_manager.add_alert_rule(rule)

    async def get_mesh_metrics(self) -> Dict[str, Any]:
        """Get comprehensive mesh metrics"""
        metrics = {}

        # Collect all metric aggregates
        for name in ["http_requests_total", "http_request_duration_seconds",
                    "service_health_status", "http_request_size_bytes", "http_response_size_bytes"]:
            agg = await self.metrics_collector.get_aggregated_metrics(name)
            if agg:
                metrics[name] = agg

        # Add system metrics
        metrics["active_traces"] = len(await self.tracing_system.get_active_spans())
        metrics["total_logs"] = len(await self.log_aggregator.get_logs())
        metrics["active_alerts"] = len(await self.alert_manager.get_active_alerts())

        return metrics

    async def get_service_dashboard(self, service: str) -> Dict[str, Any]:
        """Get dashboard data for a specific service"""
        return {
            "metrics": await self.metrics_collector.get_aggregated_metrics(f"http_requests_total"),
            "logs": await self.log_aggregator.get_logs(service=service, time_range=3600),
            "traces": [],  # Would need to filter traces by service
            "alerts": await self.alert_manager.get_active_alerts()
        }

    async def export_metrics(self, backend: MonitoringBackend) -> bool:
        """Export metrics to external monitoring backend"""
        try:
            if backend == MonitoringBackend.PROMETHEUS:
                return await self._export_to_prometheus()
            elif backend == MonitoringBackend.GRAFANA:
                return await self._export_to_grafana()
            elif backend == MonitoringBackend.JAEGER:
                return await self._export_to_jaeger()
            elif backend == MonitoringBackend.ELASTICSEARCH:
                return await self._export_to_elasticsearch()
            elif backend == MonitoringBackend.INFLUXDB:
                return await self._export_to_influxdb()
        except Exception as e:
            logger.error(f"Failed to export metrics to {backend.value}: {e}")
        return False

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                # Check alerts
                await self.alert_manager.check_alerts(self.metrics_collector)

                # Clean up old data periodically
                await self._cleanup_old_data()

                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)

    async def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        # This would implement retention policies
        pass

    # Placeholder export methods
    async def _export_to_prometheus(self) -> bool:
        # Implement Prometheus export
        return True

    async def _export_to_grafana(self) -> bool:
        # Implement Grafana export
        return True

    async def _export_to_jaeger(self) -> bool:
        # Implement Jaeger export
        return True

    async def _export_to_elasticsearch(self) -> bool:
        # Implement Elasticsearch export
        return True

    async def _export_to_influxdb(self) -> bool:
        # Implement InfluxDB export
        return True