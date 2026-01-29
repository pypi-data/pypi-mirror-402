"""
Advanced Cache Monitoring and Analytics for Distributed Cache System
Provides comprehensive monitoring, alerting, and analytics capabilities
"""

import asyncio
import time
import logging
from typing import Any, Optional, Dict, List, Callable, Tuple
from dataclasses import dataclass, field
from collections import deque
import statistics
import json

try:
    from .metrics import CacheMetricsMonitor
except ImportError:
    # Fallback for direct imports
    from metrics import CacheMetricsMonitor

logger = logging.getLogger(__name__)

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    condition: str  # e.g., "hit_rate < 0.5"
    threshold: float
    duration_seconds: int = 60  # How long condition must be true
    cooldown_seconds: int = 300  # Minimum time between alerts
    severity: str = "warning"  # info, warning, error, critical
    enabled: bool = True

@dataclass
class Alert:
    """Alert instance"""
    rule_name: str
    severity: str
    message: str
    timestamp: float
    value: float
    threshold: float
    resolved: bool = False
    resolved_timestamp: Optional[float] = None

@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot"""
    timestamp: float
    hit_rate: float
    throughput_ops_per_sec: float
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    memory_usage_bytes: int
    cache_size_bytes: int
    evictions_per_sec: float
    compression_ratio: float

class CacheMonitoring:
    """Advanced cache monitoring and analytics system"""

    def __init__(self, node_id: str = "default", enable_prometheus: bool = True):
        self.node_id = node_id
        self.core_metrics = CacheMetricsMonitor(node_id, enable_prometheus)

        # Analytics data
        self.performance_history: deque = deque(maxlen=1000)  # Store last 1000 snapshots
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.alert_callbacks: List[Callable[[Alert], None]] = []

        # Analytics settings
        self.collection_interval = 30  # seconds
        self.analytics_retention_days = 7
        self.anomaly_detection_enabled = True
        self.predictive_alerts_enabled = True

        # Anomaly detection
        self.baseline_metrics = {}
        self.anomaly_threshold = 2.0  # Standard deviations

        # Predictive analytics
        self.trend_analysis_window = 3600  # 1 hour
        self.prediction_horizon = 300  # 5 minutes

        # Monitoring loop
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_monitoring = False

    async def start_monitoring(self):
        """Start the monitoring system"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        await self.core_metrics.start_monitoring()
        logger.info(f"Cache monitoring started for node {self.node_id}")

    async def stop_monitoring(self):
        """Stop the monitoring system"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info(f"Cache monitoring stopped for node {self.node_id}")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                await self._collect_metrics()
                await self._check_alerts()
                if self.anomaly_detection_enabled:
                    await self._detect_anomalies()
                if self.predictive_alerts_enabled:
                    await self._predictive_analysis()

                await asyncio.sleep(self.collection_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.collection_interval)

    async def _collect_metrics(self):
        """Collect comprehensive metrics snapshot"""
        try:
            # Get core metrics
            core_stats = self.core_metrics.get_stats()

            # Calculate derived metrics
            hit_rate = core_stats.get('hit_rate', 0)
            throughput = core_stats.get('throughput_ops_per_sec', 0)
            memory_usage = core_stats.get('total_size_bytes', 0)
            cache_size = core_stats.get('cache_size_bytes', 0)
            evictions = core_stats.get('evictions', 0) / max(self.collection_interval, 1)
            compression_ratio = core_stats.get('compression_ratio', 1.0)

            # Calculate latency percentiles
            hits_latencies = core_stats.get('hits', {}).get('latencies', [])
            if hits_latencies:
                avg_latency = statistics.mean(hits_latencies) * 1000  # Convert to ms
                p95_latency = sorted(hits_latencies)[int(len(hits_latencies) * 0.95)] * 1000
                p99_latency = sorted(hits_latencies)[int(len(hits_latencies) * 0.99)] * 1000
            else:
                avg_latency = p95_latency = p99_latency = 0.0

            # Create performance snapshot
            snapshot = PerformanceMetrics(
                timestamp=time.time(),
                hit_rate=hit_rate,
                throughput_ops_per_sec=throughput,
                avg_latency_ms=avg_latency,
                p95_latency_ms=p95_latency,
                p99_latency_ms=p99_latency,
                memory_usage_bytes=memory_usage,
                cache_size_bytes=cache_size,
                evictions_per_sec=evictions,
                compression_ratio=compression_ratio
            )

            self.performance_history.append(snapshot)

            # Update baseline for anomaly detection
            self._update_baseline(snapshot)

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")

    def _update_baseline(self, snapshot: PerformanceMetrics):
        """Update baseline metrics for anomaly detection"""
        metrics_to_track = [
            'hit_rate', 'throughput_ops_per_sec', 'avg_latency_ms',
            'p95_latency_ms', 'memory_usage_bytes', 'evictions_per_sec'
        ]

        for metric in metrics_to_track:
            value = getattr(snapshot, metric)
            if metric not in self.baseline_metrics:
                self.baseline_metrics[metric] = []

            self.baseline_metrics[metric].append(value)

            # Keep only recent data (last hour)
            max_samples = int(3600 / self.collection_interval)
            if len(self.baseline_metrics[metric]) > max_samples:
                self.baseline_metrics[metric].pop(0)

    async def _check_alerts(self):
        """Check alert conditions"""
        current_time = time.time()

        for rule_name, rule in self.alert_rules.items():
            if not rule.enabled:
                continue

            # Check if alert is in cooldown
            if rule_name in self.active_alerts:
                last_alert = self.active_alerts[rule_name]
                if current_time - last_alert.timestamp < rule.cooldown_seconds:
                    continue

            # Evaluate condition
            if self._evaluate_condition(rule.condition, rule.threshold):
                # Check if condition has been true for required duration
                if self._condition_duration(rule.condition, rule.threshold, rule.duration_seconds):
                    await self._trigger_alert(rule, current_time)
            else:
                # Resolve alert if it was active
                if rule_name in self.active_alerts:
                    await self._resolve_alert(rule_name, current_time)

    def _evaluate_condition(self, condition: str, threshold: float) -> bool:
        """Evaluate alert condition"""
        try:
            # Parse simple conditions like "hit_rate < 0.5"
            if '<' in condition:
                metric, _ = condition.split('<')
                metric = metric.strip()
                value = self._get_current_metric_value(metric)
                return value < threshold
            elif '>' in condition:
                metric, _ = condition.split('>')
                metric = metric.strip()
                value = self._get_current_metric_value(metric)
                return value > threshold
            elif '=' in condition:
                metric, _ = condition.split('=')
                metric = metric.strip()
                value = self._get_current_metric_value(metric)
                return abs(value - threshold) < 0.001  # Approximate equality

        except Exception as e:
            logger.error(f"Error evaluating condition '{condition}': {e}")

        return False

    def _get_current_metric_value(self, metric: str) -> float:
        """Get current value of a metric"""
        if not self.performance_history:
            return 0.0

        latest = self.performance_history[-1]

        # Map metric names to snapshot attributes
        metric_map = {
            'hit_rate': 'hit_rate',
            'throughput': 'throughput_ops_per_sec',
            'avg_latency': 'avg_latency_ms',
            'p95_latency': 'p95_latency_ms',
            'p99_latency': 'p99_latency_ms',
            'memory_usage': 'memory_usage_bytes',
            'cache_size': 'cache_size_bytes',
            'evictions': 'evictions_per_sec',
            'compression_ratio': 'compression_ratio'
        }

        if metric in metric_map:
            return getattr(latest, metric_map[metric])

        return 0.0

    def _condition_duration(self, condition: str, threshold: float, duration: int) -> bool:
        """Check if condition has been true for the required duration"""
        if not self.performance_history:
            return False

        current_time = time.time()
        check_time = current_time - duration

        # Count how many recent snapshots meet the condition
        true_count = 0
        for snapshot in reversed(self.performance_history):
            if snapshot.timestamp < check_time:
                break

            # Evaluate condition for this snapshot
            temp_value = self._get_metric_value_at_time(snapshot, condition.split()[0])
            if self._compare_value(temp_value, condition, threshold):
                true_count += 1
            else:
                true_count = 0  # Reset if condition becomes false

            # If we've found enough consecutive true evaluations
            required_consecutive = max(1, duration // self.collection_interval)
            if true_count >= required_consecutive:
                return True

        return False

    def _get_metric_value_at_time(self, snapshot: PerformanceMetrics, metric: str) -> float:
        """Get metric value from a specific snapshot"""
        metric_map = {
            'hit_rate': snapshot.hit_rate,
            'throughput': snapshot.throughput_ops_per_sec,
            'avg_latency': snapshot.avg_latency_ms,
            'p95_latency': snapshot.p95_latency_ms,
            'p99_latency': snapshot.p99_latency_ms,
            'memory_usage': snapshot.memory_usage_bytes,
            'cache_size': snapshot.cache_size_bytes,
            'evictions': snapshot.evictions_per_sec,
            'compression_ratio': snapshot.compression_ratio
        }
        return metric_map.get(metric, 0.0)

    def _compare_value(self, value: float, condition: str, threshold: float) -> bool:
        """Compare value against condition"""
        if '<' in condition:
            return value < threshold
        elif '>' in condition:
            return value > threshold
        elif '=' in condition:
            return abs(value - threshold) < 0.001
        return False

    async def _trigger_alert(self, rule: AlertRule, timestamp: float):
        """Trigger an alert"""
        current_value = self._get_current_metric_value(rule.condition.split()[0])

        alert = Alert(
            rule_name=rule.name,
            severity=rule.severity,
            message=f"Alert triggered: {rule.condition} (current: {current_value:.2f}, threshold: {rule.threshold})",
            timestamp=timestamp,
            value=current_value,
            threshold=rule.threshold
        )

        self.active_alerts[rule.name] = alert
        self.alert_history.append(alert)

        # Keep alert history manageable
        if len(self.alert_history) > 1000:
            self.alert_history.pop(0)

        # Trigger callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

        logger.warning(f"Alert triggered: {alert.message}")

    async def _resolve_alert(self, rule_name: str, timestamp: float):
        """Resolve an alert"""
        if rule_name in self.active_alerts:
            alert = self.active_alerts[rule_name]
            alert.resolved = True
            alert.resolved_timestamp = timestamp

            # Trigger callbacks for resolution
            for callback in self.alert_callbacks:
                try:
                    await callback(alert)
                except Exception as e:
                    logger.error(f"Error in alert resolution callback: {e}")

            del self.active_alerts[rule_name]
            logger.info(f"Alert resolved: {rule_name}")

    async def _detect_anomalies(self):
        """Detect performance anomalies"""
        if not self.performance_history or len(self.performance_history) < 10:
            return

        latest = self.performance_history[-1]

        for metric, baseline_values in self.baseline_metrics.items():
            if len(baseline_values) < 10:
                continue

            try:
                mean = statistics.mean(baseline_values[:-1])  # Exclude latest
                stdev = statistics.stdev(baseline_values[:-1]) if len(baseline_values) > 1 else 0

                if stdev == 0:
                    continue

                current_value = getattr(latest, metric.replace('_', '_'))  # Handle naming
                z_score = abs(current_value - mean) / stdev

                if z_score > self.anomaly_threshold:
                    # Create anomaly alert
                    anomaly_alert = Alert(
                        rule_name=f"anomaly_{metric}",
                        severity="warning",
                        message=f"Anomaly detected in {metric}: {current_value:.2f} (z-score: {z_score:.2f})",
                        timestamp=time.time(),
                        value=current_value,
                        threshold=mean + (self.anomaly_threshold * stdev)
                    )

                    # Trigger anomaly alert (could be a separate callback type)
                    for callback in self.alert_callbacks:
                        try:
                            await callback(anomaly_alert)
                        except Exception as e:
                            logger.error(f"Error in anomaly callback: {e}")

            except Exception as e:
                logger.error(f"Error detecting anomaly for {metric}: {e}")

    async def _predictive_analysis(self):
        """Perform predictive analysis for potential issues"""
        if len(self.performance_history) < 60:  # Need at least 30 minutes of data
            return

        # Simple trend analysis
        recent_trend = self._calculate_trend('hit_rate', 600)  # Last 10 minutes
        if recent_trend < -0.1:  # Hit rate dropping significantly
            predictive_alert = Alert(
                rule_name="predictive_hit_rate_drop",
                severity="info",
                message=f"Predictive alert: Hit rate trending down ({recent_trend:.2f} per minute)",
                timestamp=time.time(),
                value=recent_trend,
                threshold=-0.1
            )

            for callback in self.alert_callbacks:
                try:
                    await callback(predictive_alert)
                except Exception as e:
                    logger.error(f"Error in predictive callback: {e}")

    def _calculate_trend(self, metric: str, window_seconds: int) -> float:
        """Calculate trend (slope) for a metric over a time window"""
        if len(self.performance_history) < 2:
            return 0.0

        # Get data points within the window
        current_time = time.time()
        window_start = current_time - window_seconds

        data_points = []
        for snapshot in self.performance_history:
            if snapshot.timestamp >= window_start:
                value = getattr(snapshot, metric.replace('_', '_'))
                data_points.append((snapshot.timestamp, value))

        if len(data_points) < 2:
            return 0.0

        # Simple linear regression to calculate slope
        x_values = [t - data_points[0][0] for t, _ in data_points]  # Time from start
        y_values = [v for _, v in data_points]

        n = len(data_points)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_xx = sum(x * x for x in x_values)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x) if (n * sum_xx - sum_x * sum_x) != 0 else 0

        return slope

    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule"""
        self.alert_rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")

    def remove_alert_rule(self, rule_name: str):
        """Remove an alert rule"""
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]
            logger.info(f"Removed alert rule: {rule_name}")

    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Add alert callback"""
        self.alert_callbacks.append(callback)

    def get_performance_analytics(self, time_window_seconds: int = 3600) -> Dict[str, Any]:
        """Get performance analytics for a time window"""
        current_time = time.time()
        window_start = current_time - time_window_seconds

        # Filter snapshots in the window
        window_snapshots = [s for s in self.performance_history if s.timestamp >= window_start]

        if not window_snapshots:
            return {}

        # Calculate analytics
        hit_rates = [s.hit_rate for s in window_snapshots]
        latencies = [s.avg_latency_ms for s in window_snapshots]
        throughputs = [s.throughput_ops_per_sec for s in window_snapshots]

        return {
            'time_window_seconds': time_window_seconds,
            'snapshots_count': len(window_snapshots),
            'hit_rate': {
                'avg': statistics.mean(hit_rates) if hit_rates else 0,
                'min': min(hit_rates) if hit_rates else 0,
                'max': max(hit_rates) if hit_rates else 0,
                'trend': self._calculate_trend('hit_rate', time_window_seconds)
            },
            'latency': {
                'avg': statistics.mean(latencies) if latencies else 0,
                'p95': sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0,
                'trend': self._calculate_trend('avg_latency_ms', time_window_seconds)
            },
            'throughput': {
                'avg': statistics.mean(throughputs) if throughputs else 0,
                'peak': max(throughputs) if throughputs else 0,
                'trend': self._calculate_trend('throughput_ops_per_sec', time_window_seconds)
            }
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        if not self.performance_history:
            return {'status': 'unknown', 'message': 'No performance data available'}

        latest = self.performance_history[-1]
        active_alerts_count = len(self.active_alerts)

        # Determine health based on metrics and alerts
        if active_alerts_count > 0:
            critical_alerts = [a for a in self.active_alerts.values() if a.severity == 'critical']
            if critical_alerts:
                status = 'critical'
                message = f"Critical alerts active: {len(critical_alerts)}"
            else:
                status = 'warning'
                message = f"Alerts active: {active_alerts_count}"
        elif latest.hit_rate < 0.5:
            status = 'warning'
            message = f"Low hit rate: {latest.hit_rate:.2f}"
        elif latest.avg_latency_ms > 100:
            status = 'warning'
            message = f"High latency: {latest.avg_latency_ms:.2f}ms"
        else:
            status = 'healthy'
            message = "All metrics within normal ranges"

        return {
            'status': status,
            'message': message,
            'active_alerts': active_alerts_count,
            'latest_metrics': {
                'hit_rate': latest.hit_rate,
                'avg_latency_ms': latest.avg_latency_ms,
                'throughput_ops_per_sec': latest.throughput_ops_per_sec
            },
            'timestamp': latest.timestamp
        }

    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive monitoring report"""
        return {
            'node_id': self.node_id,
            'monitoring_status': 'active' if self.is_monitoring else 'inactive',
            'collection_interval': self.collection_interval,
            'performance_history_size': len(self.performance_history),
            'alert_rules_count': len(self.alert_rules),
            'active_alerts_count': len(self.active_alerts),
            'alert_history_count': len(self.alert_history),
            'health_status': self.get_health_status(),
            'performance_analytics': self.get_performance_analytics(),
            'core_metrics': self.core_metrics.get_stats(),
            'anomaly_detection_enabled': self.anomaly_detection_enabled,
            'predictive_alerts_enabled': self.predictive_alerts_enabled
        }