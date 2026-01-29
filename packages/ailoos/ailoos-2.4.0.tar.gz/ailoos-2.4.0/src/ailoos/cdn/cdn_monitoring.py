import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import statistics

logger = logging.getLogger(__name__)

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class MetricData:
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str]
    metric_type: MetricType

@dataclass
class AlertRule:
    name: str
    condition: str  # Python expression to evaluate
    severity: AlertSeverity
    description: str
    enabled: bool = True

@dataclass
class Alert:
    rule_name: str
    severity: AlertSeverity
    message: str
    timestamp: float
    resolved: bool = False
    resolved_at: Optional[float] = None

class CDNMonitoring:
    """Comprehensive monitoring and analytics system for CDN"""

    def __init__(self, collection_interval: int = 30, retention_days: int = 30):
        self.collection_interval = collection_interval
        self.retention_days = retention_days
        self.metrics_history: Dict[str, List[MetricData]] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        self._running = False
        self._collection_task: Optional[asyncio.Task] = None
        self._alert_task: Optional[asyncio.Task] = None

        # Component references (to be set externally)
        self.cdn_manager = None
        self.content_distribution = None
        self.edge_computing = None
        self.global_cache = None

    async def start(self) -> None:
        """Start the monitoring system"""
        self._running = True
        self._collection_task = asyncio.create_task(self._metrics_collector())
        self._alert_task = asyncio.create_task(self._alert_checker())
        logger.info("CDN monitoring system started")

    async def stop(self) -> None:
        """Stop the monitoring system"""
        self._running = False
        if self._collection_task:
            self._collection_task.cancel()
        if self._alert_task:
            self._alert_task.cancel()

        await asyncio.gather(
            self._collection_task or asyncio.sleep(0),
            self._alert_task or asyncio.sleep(0),
            return_exceptions=True
        )
        logger.info("CDN monitoring system stopped")

    def set_components(self, cdn_manager=None, content_distribution=None,
                      edge_computing=None, global_cache=None) -> None:
        """Set component references for monitoring"""
        self.cdn_manager = cdn_manager
        self.content_distribution = content_distribution
        self.edge_computing = edge_computing
        self.global_cache = global_cache

    async def record_metric(self, name: str, value: float, tags: Dict[str, str] = None,
                          metric_type: MetricType = MetricType.GAUGE) -> None:
        """Record a custom metric"""
        metric = MetricData(
            name=name,
            value=value,
            timestamp=time.time(),
            tags=tags or {},
            metric_type=metric_type
        )

        if name not in self.metrics_history:
            self.metrics_history[name] = []

        self.metrics_history[name].append(metric)

        # Keep only recent metrics
        cutoff_time = time.time() - (self.retention_days * 24 * 3600)
        self.metrics_history[name] = [
            m for m in self.metrics_history[name] if m.timestamp > cutoff_time
        ]

    async def add_alert_rule(self, rule: AlertRule) -> bool:
        """Add an alert rule"""
        if rule.name in self.alert_rules:
            return False

        self.alert_rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")
        return True

    async def remove_alert_rule(self, rule_name: str) -> bool:
        """Remove an alert rule"""
        if rule_name not in self.alert_rules:
            return False

        del self.alert_rules[rule_name]
        logger.info(f"Removed alert rule: {rule_name}")
        return True

    def add_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """Add callback for alert notifications"""
        self.alert_callbacks.append(callback)

    async def get_current_metrics(self) -> Dict[str, Any]:
        """Get current comprehensive metrics"""
        metrics = {}

        # CDN Manager metrics
        if self.cdn_manager:
            try:
                cdn_metrics = await self.cdn_manager.get_all_metrics()
                metrics['cdn_providers'] = cdn_metrics
            except Exception as e:
                logger.error(f"Failed to get CDN metrics: {e}")

        # Content Distribution metrics
        if self.content_distribution:
            try:
                dist_metrics = await self.content_distribution.get_distribution_metrics()
                metrics['content_distribution'] = dist_metrics
            except Exception as e:
                logger.error(f"Failed to get distribution metrics: {e}")

        # Edge Computing metrics
        if self.edge_computing:
            try:
                edge_metrics = await self.edge_computing.get_edge_metrics()
                metrics['edge_computing'] = edge_metrics
            except Exception as e:
                logger.error(f"Failed to get edge metrics: {e}")

        # Global Cache metrics
        if self.global_cache:
            try:
                cache_metrics = await self.global_cache.get_cache_metrics()
                metrics['global_cache'] = cache_metrics
            except Exception as e:
                logger.error(f"Failed to get cache metrics: {e}")

        # System metrics
        metrics['system'] = {
            'timestamp': time.time(),
            'active_alerts': len(self.active_alerts),
            'total_metrics_collected': sum(len(history) for history in self.metrics_history.values()),
            'alert_rules_count': len(self.alert_rules)
        }

        return metrics

    async def get_metrics_history(self, metric_name: str, hours: int = 24) -> List[MetricData]:
        """Get historical metrics for a specific metric"""
        if metric_name not in self.metrics_history:
            return []

        cutoff_time = time.time() - (hours * 3600)
        return [m for m in self.metrics_history[metric_name] if m.timestamp > cutoff_time]

    async def get_analytics_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive analytics report"""
        report = {
            'period_hours': hours,
            'generated_at': time.time(),
            'metrics_summary': {},
            'performance_analysis': {},
            'recommendations': []
        }

        # Analyze each metric type
        for metric_name, history in self.metrics_history.items():
            recent_data = [m for m in history if m.timestamp > time.time() - (hours * 3600)]

            if not recent_data:
                continue

            values = [m.value for m in recent_data]

            summary = {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'avg': statistics.mean(values),
                'median': statistics.median(values),
                'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
                'latest': values[-1] if values else None
            }

            report['metrics_summary'][metric_name] = summary

            # Performance analysis
            if 'latency' in metric_name.lower():
                if summary['avg'] > 100:  # ms
                    report['performance_analysis'][metric_name] = 'High latency detected'
                    report['recommendations'].append(f"Investigate high latency in {metric_name}")
            elif 'error' in metric_name.lower():
                if summary['avg'] > 0.05:  # 5% error rate
                    report['performance_analysis'][metric_name] = 'High error rate detected'
                    report['recommendations'].append(f"Investigate error rate in {metric_name}")

        # CDN-specific analysis
        current_metrics = await self.get_current_metrics()

        if 'cdn_providers' in current_metrics:
            provider_analysis = self._analyze_provider_performance(current_metrics['cdn_providers'])
            report['performance_analysis'].update(provider_analysis)

        if 'global_cache' in current_metrics:
            cache_analysis = self._analyze_cache_performance(current_metrics['global_cache'])
            report['performance_analysis'].update(cache_analysis)

        return report

    async def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())

    async def resolve_alert(self, alert_name: str) -> bool:
        """Manually resolve an alert"""
        if alert_name not in self.active_alerts:
            return False

        alert = self.active_alerts[alert_name]
        alert.resolved = True
        alert.resolved_at = time.time()

        logger.info(f"Resolved alert: {alert_name}")
        return True

    async def _metrics_collector(self) -> None:
        """Background task to collect metrics periodically"""
        while self._running:
            try:
                await asyncio.sleep(self.collection_interval)

                # Collect system metrics
                await self._collect_system_metrics()

                # Collect component metrics
                await self._collect_component_metrics()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")

    async def _collect_system_metrics(self) -> None:
        """Collect basic system metrics"""
        # CPU, memory, etc. - simplified
        await self.record_metric(
            'system.cpu_usage',
            45.5,  # Mock value
            {'unit': 'percent'}
        )

        await self.record_metric(
            'system.memory_usage',
            68.2,  # Mock value
            {'unit': 'percent'}
        )

    async def _collect_component_metrics(self) -> None:
        """Collect metrics from all components"""
        current_metrics = await self.get_current_metrics()

        # Flatten and record component metrics
        def flatten_metrics(data: Dict[str, Any], prefix: str = '') -> List[tuple]:
            results = []
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    results.extend(flatten_metrics(value, full_key))
                elif isinstance(value, (int, float)):
                    results.append((full_key, value))
            return results

        for component, metrics in current_metrics.items():
            if component == 'system':
                continue

            flattened = flatten_metrics(metrics, component)
            for metric_name, value in flattened:
                await self.record_metric(metric_name, value)

    async def _alert_checker(self) -> None:
        """Background task to check alert conditions"""
        while self._running:
            try:
                await asyncio.sleep(60)  # Check every minute

                for rule_name, rule in self.alert_rules.items():
                    if not rule.enabled:
                        continue

                    try:
                        # Evaluate condition
                        if self._evaluate_condition(rule.condition):
                            if rule_name not in self.active_alerts:
                                # New alert
                                alert = Alert(
                                    rule_name=rule_name,
                                    severity=rule.severity,
                                    message=rule.description,
                                    timestamp=time.time()
                                )
                                self.active_alerts[rule_name] = alert

                                # Notify callbacks
                                for callback in self.alert_callbacks:
                                    try:
                                        callback(alert)
                                    except Exception as e:
                                        logger.error(f"Alert callback error: {e}")

                                logger.warning(f"Alert triggered: {rule_name}")
                        else:
                            # Check if alert should be resolved
                            if rule_name in self.active_alerts:
                                # Auto-resolve if condition no longer met
                                alert = self.active_alerts[rule_name]
                                if not alert.resolved:
                                    alert.resolved = True
                                    alert.resolved_at = time.time()
                                    logger.info(f"Alert resolved: {rule_name}")

                    except Exception as e:
                        logger.error(f"Alert evaluation error for {rule_name}: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Alert checker error: {e}")

    def _evaluate_condition(self, condition: str) -> bool:
        """Evaluate alert condition expression"""
        # Create safe evaluation context
        context = {}

        # Add recent metrics to context
        for metric_name, history in self.metrics_history.items():
            if history:
                context[metric_name.replace('.', '_')] = history[-1].value

        try:
            return bool(eval(condition, {"__builtins__": {}}, context))
        except Exception as e:
            logger.error(f"Condition evaluation error: {e}")
            return False

    def _analyze_provider_performance(self, provider_metrics: Dict[str, Any]) -> Dict[str, str]:
        """Analyze CDN provider performance"""
        analysis = {}

        for provider, metrics in provider_metrics.items():
            hit_rate = metrics.get('cache_hit_ratio', 0)
            uptime = metrics.get('uptime', 0)

            if hit_rate < 0.7:
                analysis[f"{provider}_cache"] = f"Low cache hit rate: {hit_rate:.2%}"
            if uptime < 0.99:
                analysis[f"{provider}_uptime"] = f"Low uptime: {uptime:.2%}"

        return analysis

    def _analyze_cache_performance(self, cache_metrics: Dict[str, Any]) -> Dict[str, str]:
        """Analyze global cache performance"""
        analysis = {}

        hit_rate = cache_metrics.get('overall_hit_rate', 0)
        utilization = cache_metrics.get('memory_utilization', 0)

        if hit_rate < 0.8:
            analysis['cache_hit_rate'] = f"Low cache hit rate: {hit_rate:.2%}"
        if utilization > 0.9:
            analysis['cache_utilization'] = f"High memory utilization: {utilization:.2%}"

        return analysis