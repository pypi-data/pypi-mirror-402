"""
Tests for Cache Monitoring
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch

from src.ailoos.cache.cache_monitoring import (
    CacheMonitoring, AlertRule, Alert, PerformanceMetrics
)


class TestCacheMonitoring:
    """Test Cache Monitoring functionality"""

    @pytest.fixture
    def cache_monitoring(self):
        """Cache monitoring fixture"""
        return CacheMonitoring(node_id="test_node")

    @pytest.fixture
    def alert_rule(self):
        """Alert rule fixture"""
        return AlertRule(
            name="low_hit_rate",
            condition="hit_rate < 0.5",
            threshold=0.5,
            duration_seconds=60,
            severity="warning"
        )

    @pytest.mark.asyncio
    async def test_initialization(self, cache_monitoring):
        """Test monitoring initialization"""
        assert cache_monitoring.node_id == "test_node"
        assert not cache_monitoring.is_monitoring
        assert len(cache_monitoring.performance_history) == 0
        assert len(cache_monitoring.alert_rules) == 0
        assert len(cache_monitoring.active_alerts) == 0

    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, cache_monitoring):
        """Test starting and stopping monitoring"""
        await cache_monitoring.start_monitoring()
        assert cache_monitoring.is_monitoring
        assert cache_monitoring.monitoring_task is not None

        await cache_monitoring.stop_monitoring()
        assert not cache_monitoring.is_monitoring

    @pytest.mark.asyncio
    async def test_collect_metrics(self, cache_monitoring):
        """Test metrics collection"""
        # Mock core metrics
        with patch.object(cache_monitoring.core_metrics, 'get_stats') as mock_get_stats:
            mock_get_stats.return_value = {
                'hit_rate': 0.85,
                'throughput_ops_per_sec': 100.0,
                'total_size_bytes': 1024000,
                'cache_size_bytes': 1024000,
                'evictions': 5,
                'compression_ratio': 0.7,
                'hits': {'count': 85, 'latencies': [0.001, 0.002, 0.0015]},
                'misses': {'count': 15, 'latencies': [0.005, 0.004]}
            }

            await cache_monitoring._collect_metrics()

            assert len(cache_monitoring.performance_history) == 1
            snapshot = cache_monitoring.performance_history[-1]

            assert snapshot.hit_rate == 0.85
            assert snapshot.throughput_ops_per_sec == 100.0
            assert snapshot.memory_usage_bytes == 1024000
            assert snapshot.compression_ratio == 0.7

    def test_evaluate_condition_less_than(self, cache_monitoring):
        """Test condition evaluation for less than"""
        # Add a snapshot with known values
        snapshot = PerformanceMetrics(
            timestamp=time.time(),
            hit_rate=0.4,
            throughput_ops_per_sec=50.0,
            avg_latency_ms=10.0,
            p95_latency_ms=20.0,
            p99_latency_ms=30.0,
            memory_usage_bytes=1000000,
            cache_size_bytes=1000000,
            evictions_per_sec=1.0,
            compression_ratio=0.8
        )
        cache_monitoring.performance_history.append(snapshot)

        # Test condition evaluation
        assert cache_monitoring._evaluate_condition("hit_rate < 0.5", 0.5) is True
        assert cache_monitoring._evaluate_condition("hit_rate < 0.3", 0.3) is False
        assert cache_monitoring._evaluate_condition("throughput > 40", 40) is True

    def test_condition_duration(self, cache_monitoring):
        """Test condition duration checking"""
        current_time = time.time()

        # Create snapshots where hit_rate < 0.5 for the last 2 minutes
        for i in range(12):  # 12 snapshots = 2 minutes at 10s intervals
            snapshot = PerformanceMetrics(
                timestamp=current_time - (120 - i * 10),
                hit_rate=0.4,
                throughput_ops_per_sec=50.0,
                avg_latency_ms=10.0,
                p95_latency_ms=20.0,
                p99_latency_ms=30.0,
                memory_usage_bytes=1000000,
                cache_size_bytes=1000000,
                evictions_per_sec=1.0,
                compression_ratio=0.8
            )
            cache_monitoring.performance_history.append(snapshot)

        # Should return True since condition has been true for more than 60 seconds
        assert cache_monitoring._condition_duration("hit_rate < 0.5", 0.5, 60) is True

    @pytest.mark.asyncio
    async def test_trigger_alert(self, cache_monitoring, alert_rule):
        """Test alert triggering"""
        alert_triggered = []

        def alert_callback(alert):
            alert_triggered.append(alert)

        cache_monitoring.add_alert_callback(alert_callback)
        cache_monitoring.add_alert_rule(alert_rule)

        # Create a snapshot that triggers the alert
        snapshot = PerformanceMetrics(
            timestamp=time.time(),
            hit_rate=0.3,  # Below threshold
            throughput_ops_per_sec=50.0,
            avg_latency_ms=10.0,
            p95_latency_ms=20.0,
            p99_latency_ms=30.0,
            memory_usage_bytes=1000000,
            cache_size_bytes=1000000,
            evictions_per_sec=1.0,
            compression_ratio=0.8
        )
        cache_monitoring.performance_history.append(snapshot)

        # Set consecutive snapshots to meet duration requirement
        for _ in range(10):
            cache_monitoring.performance_history.append(snapshot)

        await cache_monitoring._check_alerts()

        assert len(alert_triggered) > 0
        assert alert_triggered[0].rule_name == "low_hit_rate"
        assert alert_triggered[0].severity == "warning"

    @pytest.mark.asyncio
    async def test_resolve_alert(self, cache_monitoring, alert_rule):
        """Test alert resolution"""
        cache_monitoring.add_alert_rule(alert_rule)

        # Manually add an active alert
        alert = Alert(
            rule_name="low_hit_rate",
            severity="warning",
            message="Hit rate low",
            timestamp=time.time() - 100,
            value=0.3,
            threshold=0.5
        )
        cache_monitoring.active_alerts["low_hit_rate"] = alert

        # Create a snapshot where condition is no longer true
        snapshot = PerformanceMetrics(
            timestamp=time.time(),
            hit_rate=0.7,  # Above threshold
            throughput_ops_per_sec=50.0,
            avg_latency_ms=10.0,
            p95_latency_ms=20.0,
            p99_latency_ms=30.0,
            memory_usage_bytes=1000000,
            cache_size_bytes=1000000,
            evictions_per_sec=1.0,
            compression_ratio=0.8
        )
        cache_monitoring.performance_history.append(snapshot)

        await cache_monitoring._check_alerts()

        assert "low_hit_rate" not in cache_monitoring.active_alerts
        assert alert.resolved is True

    @pytest.mark.asyncio
    async def test_anomaly_detection(self, cache_monitoring):
        """Test anomaly detection"""
        # Create baseline data
        for i in range(20):
            snapshot = PerformanceMetrics(
                timestamp=time.time() - (200 - i * 10),
                hit_rate=0.8,  # Normal hit rate
                throughput_ops_per_sec=100.0,
                avg_latency_ms=5.0,
                p95_latency_ms=10.0,
                p99_latency_ms=15.0,
                memory_usage_bytes=1000000,
                cache_size_bytes=1000000,
                evictions_per_sec=1.0,
                compression_ratio=0.8
            )
            cache_monitoring.performance_history.append(snapshot)
            cache_monitoring._update_baseline(snapshot)

        # Add anomalous snapshot
        anomaly_snapshot = PerformanceMetrics(
            timestamp=time.time(),
            hit_rate=0.2,  # Anomalous hit rate (much lower)
            throughput_ops_per_sec=100.0,
            avg_latency_ms=5.0,
            p95_latency_ms=10.0,
            p99_latency_ms=15.0,
            memory_usage_bytes=1000000,
            cache_size_bytes=1000000,
            evictions_per_sec=1.0,
            compression_ratio=0.8
        )
        cache_monitoring.performance_history.append(anomaly_snapshot)

        anomaly_triggered = []

        def anomaly_callback(alert):
            anomaly_triggered.append(alert)

        cache_monitoring.add_alert_callback(anomaly_callback)

        await cache_monitoring._detect_anomalies()

        assert len(anomaly_triggered) > 0
        assert "anomaly" in anomaly_triggered[0].rule_name

    @pytest.mark.asyncio
    async def test_predictive_analysis(self, cache_monitoring):
        """Test predictive analysis"""
        # Create trending data (declining hit rate)
        base_time = time.time()
        for i in range(30):
            # Simulate declining hit rate
            hit_rate = 0.9 - (i * 0.01)  # Declining from 0.9 to 0.6
            snapshot = PerformanceMetrics(
                timestamp=base_time - (300 - i * 10),
                hit_rate=hit_rate,
                throughput_ops_per_sec=100.0,
                avg_latency_ms=5.0,
                p95_latency_ms=10.0,
                p99_latency_ms=15.0,
                memory_usage_bytes=1000000,
                cache_size_bytes=1000000,
                evictions_per_sec=1.0,
                compression_ratio=0.8
            )
            cache_monitoring.performance_history.append(snapshot)

        predictive_triggered = []

        def predictive_callback(alert):
            predictive_triggered.append(alert)

        cache_monitoring.add_alert_callback(predictive_callback)

        await cache_monitoring._predictive_analysis()

        # Should trigger predictive alert due to declining trend
        assert len(predictive_triggered) > 0
        assert "predictive" in predictive_triggered[0].rule_name

    def test_get_performance_analytics(self, cache_monitoring):
        """Test performance analytics retrieval"""
        # Add some test data
        for i in range(10):
            snapshot = PerformanceMetrics(
                timestamp=time.time() - (600 - i * 60),
                hit_rate=0.8 + (i * 0.01),
                throughput_ops_per_sec=90 + i,
                avg_latency_ms=5.0 + (i * 0.1),
                p95_latency_ms=10.0 + (i * 0.2),
                p99_latency_ms=15.0 + (i * 0.3),
                memory_usage_bytes=1000000,
                cache_size_bytes=1000000,
                evictions_per_sec=1.0,
                compression_ratio=0.8
            )
            cache_monitoring.performance_history.append(snapshot)

        analytics = cache_monitoring.get_performance_analytics(600)

        assert 'hit_rate' in analytics
        assert 'latency' in analytics
        assert 'throughput' in analytics
        assert analytics['hit_rate']['avg'] > 0
        assert analytics['throughput']['avg'] > 0

    def test_get_health_status(self, cache_monitoring):
        """Test health status retrieval"""
        # Test with no data
        status = cache_monitoring.get_health_status()
        assert status['status'] == 'unknown'

        # Add healthy data
        snapshot = PerformanceMetrics(
            timestamp=time.time(),
            hit_rate=0.9,
            throughput_ops_per_sec=100.0,
            avg_latency_ms=5.0,
            p95_latency_ms=10.0,
            p99_latency_ms=15.0,
            memory_usage_bytes=1000000,
            cache_size_bytes=1000000,
            evictions_per_sec=1.0,
            compression_ratio=0.8
        )
        cache_monitoring.performance_history.append(snapshot)

        status = cache_monitoring.get_health_status()
        assert status['status'] == 'healthy'

        # Add unhealthy data
        unhealthy_snapshot = PerformanceMetrics(
            timestamp=time.time(),
            hit_rate=0.2,  # Very low hit rate
            throughput_ops_per_sec=100.0,
            avg_latency_ms=5.0,
            p95_latency_ms=10.0,
            p99_latency_ms=15.0,
            memory_usage_bytes=1000000,
            cache_size_bytes=1000000,
            evictions_per_sec=1.0,
            compression_ratio=0.8
        )
        cache_monitoring.performance_history.clear()
        cache_monitoring.performance_history.append(unhealthy_snapshot)

        status = cache_monitoring.get_health_status()
        assert status['status'] == 'warning'

    def test_add_remove_alert_rule(self, cache_monitoring, alert_rule):
        """Test adding and removing alert rules"""
        cache_monitoring.add_alert_rule(alert_rule)
        assert "low_hit_rate" in cache_monitoring.alert_rules

        cache_monitoring.remove_alert_rule("low_hit_rate")
        assert "low_hit_rate" not in cache_monitoring.alert_rules

    def test_add_alert_callback(self, cache_monitoring):
        """Test adding alert callback"""
        callback_called = []

        def test_callback(alert):
            callback_called.append(alert)

        cache_monitoring.add_alert_callback(test_callback)

        # Simulate alert
        alert = Alert(
            rule_name="test",
            severity="info",
            message="Test alert",
            timestamp=time.time(),
            value=1.0,
            threshold=0.5
        )

        cache_monitoring.alert_callbacks[0](alert)
        assert len(callback_called) == 1

    def test_get_comprehensive_report(self, cache_monitoring):
        """Test comprehensive monitoring report"""
        report = cache_monitoring.get_comprehensive_report()

        assert 'node_id' in report
        assert 'monitoring_status' in report
        assert 'health_status' in report
        assert 'performance_analytics' in report
        assert report['node_id'] == "test_node"