"""
Cache Metrics Monitor for Distributed Cache System
Provides detailed performance metrics and monitoring
"""

import time
import asyncio
import statistics
from typing import Dict, List, Any, Optional, Callable
from collections import deque
from dataclasses import dataclass, field
import logging

try:
    from prometheus_client import Counter, Gauge, Histogram, Summary
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class OperationMetrics:
    """Metrics for a single operation type"""
    count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    latencies: deque = field(default_factory=lambda: deque(maxlen=1000))

    def record(self, duration: float):
        self.count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.latencies.append(duration)

    def get_stats(self) -> Dict[str, Any]:
        if self.count == 0:
            return {
                'count': 0,
                'avg_time': 0.0,
                'min_time': float('inf'),
                'max_time': 0.0,
                'p50': 0.0,
                'p95': 0.0,
                'p99': 0.0
            }

        sorted_latencies = sorted(self.latencies)
        return {
            'count': self.count,
            'avg_time': self.total_time / self.count,
            'min_time': self.min_time,
            'max_time': self.max_time,
            'p50': sorted_latencies[len(sorted_latencies) // 2],
            'p95': sorted_latencies[int(len(sorted_latencies) * 0.95)],
            'p99': sorted_latencies[int(len(sorted_latencies) * 0.99)]
        }

class CacheMetricsMonitor:
    """Comprehensive cache metrics monitoring"""

    def __init__(self, node_id: str = "default", enable_prometheus: bool = True):
        self.node_id = node_id
        self.start_time = time.time()

        # Core metrics
        self.hits = OperationMetrics()
        self.misses = OperationMetrics()
        self.sets = OperationMetrics()
        self.deletes = OperationMetrics()
        self.invalidations = OperationMetrics()

        # Size metrics
        self.current_entries = 0
        self.total_size_bytes = 0
        self.peak_size_bytes = 0
        self.evictions = 0

        # Compression metrics
        self.compression_operations = 0
        self.decompression_operations = 0
        self.compression_ratio = 0.0
        self.space_saved_bytes = 0

        # Strategy metrics
        self.strategy_switches = 0
        self.current_strategy = "unknown"

        # Network metrics (for distributed)
        self.network_requests = OperationMetrics()
        self.network_failures = 0
        self.sync_operations = OperationMetrics()

        # Time series data
        self.metrics_history: deque = deque(maxlen=1000)  # Store last 1000 metric snapshots
        self.collection_interval = 60  # seconds

        # Prometheus metrics
        self.prometheus_enabled = enable_prometheus and PROMETHEUS_AVAILABLE
        if self.prometheus_enabled:
            self._setup_prometheus_metrics()

        # Alert thresholds
        self.alerts_enabled = True
        self.hit_rate_threshold = 0.5  # Alert if hit rate drops below 50%
        self.latency_threshold = 1.0   # Alert if avg latency > 1 second
        self.alert_callbacks: List[Callable[[str, Any], None]] = []

    def _setup_prometheus_metrics(self):
        """Setup Prometheus metrics"""
        self.prom_cache_hits = Counter(
            'cache_hits_total',
            'Total cache hits',
            ['node_id', 'strategy']
        )
        self.prom_cache_misses = Counter(
            'cache_misses_total',
            'Total cache misses',
            ['node_id', 'strategy']
        )
        self.prom_cache_size = Gauge(
            'cache_size_bytes',
            'Current cache size in bytes',
            ['node_id']
        )
        self.prom_cache_entries = Gauge(
            'cache_entries_total',
            'Current number of cache entries',
            ['node_id']
        )
        self.prom_operation_latency = Histogram(
            'cache_operation_duration_seconds',
            'Cache operation latency',
            ['node_id', 'operation']
        )

    def record_hit(self, latency: float):
        """Record a cache hit"""
        self.hits.record(latency)
        if self.prometheus_enabled:
            self.prom_cache_hits.labels(node_id=self.node_id, strategy=self.current_strategy).inc()

    def record_miss(self, latency: float):
        """Record a cache miss"""
        self.misses.record(latency)
        if self.prometheus_enabled:
            self.prom_cache_misses.labels(node_id=self.node_id, strategy=self.current_strategy).inc()

    def record_set(self, latency: float, size_bytes: int):
        """Record a cache set operation"""
        self.sets.record(latency)
        self.total_size_bytes += size_bytes
        self.peak_size_bytes = max(self.peak_size_bytes, self.total_size_bytes)
        if self.prometheus_enabled:
            self.prom_operation_latency.labels(node_id=self.node_id, operation='set').observe(latency)

    def record_delete(self, latency: float, size_bytes: int):
        """Record a cache delete operation"""
        self.deletes.record(latency)
        self.total_size_bytes = max(0, self.total_size_bytes - size_bytes)
        if self.prometheus_enabled:
            self.prom_operation_latency.labels(node_id=self.node_id, operation='delete').observe(latency)

    def record_invalidation(self, count: int = 1):
        """Record cache invalidations"""
        for _ in range(count):
            self.invalidations.record(0.0)  # No latency for invalidations

    def record_eviction(self):
        """Record a cache eviction"""
        self.evictions += 1

    def record_compression(self, original_size: int, compressed_size: int):
        """Record compression operation"""
        self.compression_operations += 1
        if original_size > 0:
            ratio = compressed_size / original_size
            self.compression_ratio = (self.compression_ratio * (self.compression_operations - 1) + ratio) / self.compression_operations
            self.space_saved_bytes += (original_size - compressed_size)

    def record_decompression(self):
        """Record decompression operation"""
        self.decompression_operations += 1

    def record_strategy_switch(self, new_strategy: str):
        """Record strategy switch"""
        self.strategy_switches += 1
        self.current_strategy = new_strategy

    def record_network_request(self, latency: float, success: bool = True):
        """Record network request for distributed operations"""
        self.network_requests.record(latency)
        if not success:
            self.network_failures += 1

    def update_size_metrics(self, entries: int, size_bytes: int):
        """Update current size metrics"""
        self.current_entries = entries
        self.total_size_bytes = size_bytes
        self.peak_size_bytes = max(self.peak_size_bytes, size_bytes)

        if self.prometheus_enabled:
            self.prom_cache_size.labels(node_id=self.node_id).set(size_bytes)
            self.prom_cache_entries.labels(node_id=self.node_id).set(entries)

    def get_hit_rate(self) -> float:
        """Calculate current hit rate"""
        total_requests = self.hits.count + self.misses.count
        return self.hits.count / total_requests if total_requests > 0 else 0.0

    def get_throughput(self) -> float:
        """Calculate operations per second"""
        uptime = time.time() - self.start_time
        total_ops = self.hits.count + self.misses.count + self.sets.count + self.deletes.count
        return total_ops / uptime if uptime > 0 else 0.0

    def get_memory_efficiency(self) -> float:
        """Calculate memory efficiency (compression ratio)"""
        return self.compression_ratio if self.compression_operations > 0 else 1.0

    def collect_snapshot(self) -> Dict[str, Any]:
        """Collect current metrics snapshot"""
        snapshot = {
            'timestamp': time.time(),
            'node_id': self.node_id,
            'uptime_seconds': time.time() - self.start_time,
            'hit_rate': self.get_hit_rate(),
            'throughput_ops_per_sec': self.get_throughput(),
            'memory_efficiency': self.get_memory_efficiency(),
            'current_entries': self.current_entries,
            'total_size_bytes': self.total_size_bytes,
            'peak_size_bytes': self.peak_size_bytes,
            'evictions': self.evictions,
            'strategy_switches': self.strategy_switches,
            'current_strategy': self.current_strategy,
            'compression_operations': self.compression_operations,
            'decompression_operations': self.decompression_operations,
            'compression_ratio': self.compression_ratio,
            'space_saved_bytes': self.space_saved_bytes,
            'network_failures': self.network_failures,
            'hits': self.hits.get_stats(),
            'misses': self.misses.get_stats(),
            'sets': self.sets.get_stats(),
            'deletes': self.deletes.get_stats(),
            'invalidations': self.invalidations.get_stats(),
            'network_requests': self.network_requests.get_stats()
        }

        self.metrics_history.append(snapshot)
        return snapshot

    def get_aggregated_stats(self, time_window_seconds: int = 3600) -> Dict[str, Any]:
        """Get aggregated statistics over a time window"""
        if not self.metrics_history:
            return self.collect_snapshot()

        current_time = time.time()
        recent_snapshots = [s for s in self.metrics_history if current_time - s['timestamp'] <= time_window_seconds]

        if not recent_snapshots:
            return self.collect_snapshot()

        # Aggregate metrics
        hit_rates = [s['hit_rate'] for s in recent_snapshots]
        throughputs = [s['throughput_ops_per_sec'] for s in recent_snapshots]

        return {
            'time_window_seconds': time_window_seconds,
            'snapshots_count': len(recent_snapshots),
            'avg_hit_rate': statistics.mean(hit_rates) if hit_rates else 0,
            'min_hit_rate': min(hit_rates) if hit_rates else 0,
            'max_hit_rate': max(hit_rates) if hit_rates else 0,
            'avg_throughput': statistics.mean(throughputs) if throughputs else 0,
            'hit_rate_trend': self._calculate_trend(hit_rates),
            'throughput_trend': self._calculate_trend(throughputs)
        }

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return "stable"

        recent = statistics.mean(values[-10:]) if len(values) >= 10 else statistics.mean(values)
        older = statistics.mean(values[:-10]) if len(values) >= 20 else statistics.mean(values[:len(values)//2])

        if recent > older * 1.05:
            return "increasing"
        elif recent < older * 0.95:
            return "decreasing"
        else:
            return "stable"

    def check_alerts(self):
        """Check for alert conditions"""
        if not self.alerts_enabled:
            return

        hit_rate = self.get_hit_rate()
        if hit_rate < self.hit_rate_threshold:
            self._trigger_alert("low_hit_rate", {
                'hit_rate': hit_rate,
                'threshold': self.hit_rate_threshold
            })

        # Check latency alerts
        avg_latency = self.hits.get_stats()['avg_time']
        if avg_latency > self.latency_threshold:
            self._trigger_alert("high_latency", {
                'avg_latency': avg_latency,
                'threshold': self.latency_threshold
            })

    def _trigger_alert(self, alert_type: str, data: Dict[str, Any]):
        """Trigger alert callbacks"""
        for callback in self.alert_callbacks:
            try:
                callback(alert_type, data)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")

    def add_alert_callback(self, callback: Callable[[str, Any], None]):
        """Add alert callback"""
        self.alert_callbacks.append(callback)

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        hit_rate = self.get_hit_rate()
        avg_latency = self.hits.get_stats()['avg_time']

        status = "healthy"
        issues = []

        if hit_rate < 0.3:
            status = "critical"
            issues.append("Very low hit rate")
        elif hit_rate < 0.5:
            status = "warning"
            issues.append("Low hit rate")

        if avg_latency > 2.0:
            status = "critical" if status != "critical" else status
            issues.append("High latency")
        elif avg_latency > 1.0:
            status = "warning" if status == "healthy" else status
            issues.append("Elevated latency")

        if self.network_failures > 10:
            status = "critical" if status != "critical" else status
            issues.append("High network failure rate")

        return {
            'status': status,
            'issues': issues,
            'hit_rate': hit_rate,
            'avg_latency': avg_latency,
            'network_failures': self.network_failures
        }

    async def start_monitoring(self, collection_interval: int = 60):
        """Start periodic metrics collection"""
        self.collection_interval = collection_interval
        while True:
            try:
                self.collect_snapshot()
                self.check_alerts()
                await asyncio.sleep(collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(collection_interval)