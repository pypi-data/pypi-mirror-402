"""
Performance Test Suite
Executes performance tests to measure system responsiveness, throughput, and resource usage.
"""

import asyncio
import logging
import time
import statistics
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import psutil
import aiohttp


class PerformanceMetric(Enum):
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    LATENCY = "latency"
    ERROR_RATE = "error_rate"


@dataclass
class PerformanceTestConfig:
    name: str
    endpoint: str
    method: str = "GET"
    payload: Optional[Dict] = None
    concurrent_users: int = 10
    duration: int = 60  # seconds
    ramp_up_time: int = 10  # seconds
    headers: Optional[Dict[str, str]] = None


@dataclass
class PerformanceResult:
    metric: PerformanceMetric
    value: float
    unit: str
    timestamp: float


@dataclass
class PerformanceTestResult:
    test_config: PerformanceTestConfig
    success: bool
    metrics: List[PerformanceResult]
    summary: Dict[str, Any]
    errors: List[str]


class PerformanceTestSuite:
    """
    Suite for running performance tests on system endpoints and workflows.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)

        self.base_url = config.get('base_url', 'http://localhost:8000')
        self.max_concurrent = config.get('max_concurrent', 100)
        self.test_timeout = config.get('timeout', 300)

        # Predefined performance tests
        self.test_configs = self._load_test_configs()

    def _load_test_configs(self) -> List[PerformanceTestConfig]:
        """Load predefined performance test configurations."""
        return [
            PerformanceTestConfig(
                name="api_response_time",
                endpoint="/api/health",
                method="GET",
                concurrent_users=50,
                duration=120
            ),
            PerformanceTestConfig(
                name="data_processing_load",
                endpoint="/api/data/process",
                method="POST",
                payload={"data_size": "large", "operations": ["filter", "aggregate", "transform"]},
                concurrent_users=20,
                duration=180,
                ramp_up_time=30
            ),
            PerformanceTestConfig(
                name="federated_training_load",
                endpoint="/api/federated/train",
                method="POST",
                payload={"model_type": "neural_network", "dataset_size": 10000, "epochs": 5},
                concurrent_users=10,
                duration=300,
                ramp_up_time=60
            ),
            PerformanceTestConfig(
                name="file_upload_performance",
                endpoint="/api/files/upload",
                method="POST",
                payload={"file_size": "10MB", "type": "dataset"},
                concurrent_users=5,
                duration=120
            ),
            PerformanceTestConfig(
                name="search_query_performance",
                endpoint="/api/search",
                method="POST",
                payload={"query": "complex federated learning algorithms", "filters": {"year": "2023-2024"}},
                concurrent_users=30,
                duration=90
            )
        ]

    async def run_performance_tests(self, test_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run performance tests.

        Args:
            test_names: List of specific test names to run. If None, runs all.

        Returns:
            Performance test results summary
        """
        self.logger.info("Starting performance test execution")

        if test_names:
            tests_to_run = [tc for tc in self.test_configs if tc.name in test_names]
        else:
            tests_to_run = self.test_configs

        results = []
        total_passed = 0

        for test_config in tests_to_run:
            self.logger.info(f"Running performance test: {test_config.name}")
            result = await self._execute_performance_test(test_config)
            results.append(result)

            if result.success:
                total_passed += 1

        # Calculate overall metrics
        all_metrics = []
        for result in results:
            all_metrics.extend(result.metrics)

        overall_summary = self._calculate_overall_summary(all_metrics)

        return {
            'success': total_passed == len(tests_to_run),
            'total_tests': len(tests_to_run),
            'passed': total_passed,
            'failed': len(tests_to_run) - total_passed,
            'overall_summary': overall_summary,
            'results': [self._serialize_result(r) for r in results],
            'duration': sum(r.summary.get('total_duration', 0) for r in results)
        }

    async def _execute_performance_test(self, test_config: PerformanceTestConfig) -> PerformanceTestResult:
        """Execute a single performance test."""
        start_time = time.time()
        metrics = []
        errors = []

        try:
            # Monitor system resources during test
            system_monitor = asyncio.create_task(self._monitor_system_resources(test_config.duration))

            # Run the actual performance test
            test_metrics = await self._run_load_test(test_config)
            metrics.extend(test_metrics)

            # Wait for system monitoring to complete
            system_metrics = await system_monitor
            metrics.extend(system_metrics)

            success = len(errors) == 0

        except Exception as e:
            self.logger.error(f"Error executing performance test {test_config.name}: {e}")
            errors.append(str(e))
            success = False

        duration = time.time() - start_time

        summary = self._calculate_test_summary(metrics, duration)

        return PerformanceTestResult(
            test_config=test_config,
            success=success,
            metrics=metrics,
            summary=summary,
            errors=errors
        )

    async def _run_load_test(self, test_config: PerformanceTestConfig) -> List[PerformanceResult]:
        """Run load test for a specific endpoint."""
        metrics = []
        response_times = []
        error_count = 0
        total_requests = 0

        # Create session for HTTP requests
        async with aiohttp.ClientSession() as session:
            # Ramp up users gradually
            tasks = []
            for i in range(test_config.concurrent_users):
                task = asyncio.create_task(
                    self._simulate_user_session(session, test_config, i)
                )
                tasks.append(task)

                # Stagger user startup
                if i < test_config.concurrent_users - 1:
                    await asyncio.sleep(test_config.ramp_up_time / test_config.concurrent_users)

            # Run all user sessions
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for result in results:
                if isinstance(result, Exception):
                    error_count += 1
                    continue

                user_times, user_errors = result
                response_times.extend(user_times)
                error_count += user_errors
                total_requests += len(user_times)

            test_duration = time.time() - start_time

            # Calculate metrics
            if response_times:
                metrics.extend([
                    PerformanceResult(
                        metric=PerformanceMetric.RESPONSE_TIME,
                        value=statistics.mean(response_times),
                        unit="seconds",
                        timestamp=time.time()
                    ),
                    PerformanceResult(
                        metric=PerformanceMetric.LATENCY,
                        value=statistics.median(response_times),
                        unit="seconds",
                        timestamp=time.time()
                    ),
                    PerformanceResult(
                        metric=PerformanceMetric.THROUGHPUT,
                        value=total_requests / test_duration,
                        unit="requests/second",
                        timestamp=time.time()
                    )
                ])

            if total_requests > 0:
                error_rate = error_count / total_requests
                metrics.append(PerformanceResult(
                    metric=PerformanceMetric.ERROR_RATE,
                    value=error_rate,
                    unit="percentage",
                    timestamp=time.time()
                ))

        return metrics

    async def _simulate_user_session(self, session: aiohttp.ClientSession,
                                   test_config: PerformanceTestConfig,
                                   user_id: int) -> tuple:
        """Simulate a user session making requests."""
        response_times = []
        errors = 0
        end_time = time.time() + test_config.duration

        while time.time() < end_time:
            try:
                start_request = time.time()

                # Make request
                url = f"{self.base_url}{test_config.endpoint}"
                headers = test_config.headers or {}

                if test_config.method == "GET":
                    async with session.get(url, headers=headers) as response:
                        await response.text()
                elif test_config.method == "POST":
                    async with session.post(url, json=test_config.payload, headers=headers) as response:
                        await response.text()
                # Add other HTTP methods as needed

                response_time = time.time() - start_request
                response_times.append(response_time)

            except Exception as e:
                errors += 1
                self.logger.debug(f"Request error for user {user_id}: {e}")

            # Small delay between requests
            await asyncio.sleep(0.1)

        return response_times, errors

    async def _monitor_system_resources(self, duration: int) -> List[PerformanceResult]:
        """Monitor system resources during test execution."""
        metrics = []
        end_time = time.time() + duration

        while time.time() < end_time:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                metrics.append(PerformanceResult(
                    metric=PerformanceMetric.CPU_USAGE,
                    value=cpu_percent,
                    unit="percentage",
                    timestamp=time.time()
                ))

                # Memory usage
                memory = psutil.virtual_memory()
                metrics.append(PerformanceResult(
                    metric=PerformanceMetric.MEMORY_USAGE,
                    value=memory.percent,
                    unit="percentage",
                    timestamp=time.time()
                ))

            except Exception as e:
                self.logger.debug(f"Resource monitoring error: {e}")

        return metrics

    def _calculate_test_summary(self, metrics: List[PerformanceResult], duration: float) -> Dict[str, Any]:
        """Calculate summary statistics for a test."""
        summary = {
            'total_duration': duration,
            'metrics_count': len(metrics)
        }

        # Group metrics by type
        metric_groups = {}
        for metric in metrics:
            if metric.metric not in metric_groups:
                metric_groups[metric.metric] = []
            metric_groups[metric.metric].append(metric.value)

        # Calculate statistics for each metric type
        for metric_type, values in metric_groups.items():
            if values:
                summary[f'{metric_type.value}_avg'] = statistics.mean(values)
                summary[f'{metric_type.value}_max'] = max(values)
                summary[f'{metric_type.value}_min'] = min(values)
                if len(values) > 1:
                    summary[f'{metric_type.value}_std'] = statistics.stdev(values)

        return summary

    def _calculate_overall_summary(self, all_metrics: List[PerformanceResult]) -> Dict[str, Any]:
        """Calculate overall performance summary across all tests."""
        if not all_metrics:
            return {}

        # Group all metrics
        metric_groups = {}
        for metric in all_metrics:
            if metric.metric not in metric_groups:
                metric_groups[metric.metric] = []
            metric_groups[metric.metric].append(metric.value)

        summary = {}
        for metric_type, values in metric_groups.items():
            summary[f'overall_{metric_type.value}_avg'] = statistics.mean(values)
            summary[f'overall_{metric_type.value}_max'] = max(values)

        return summary

    def _serialize_result(self, result: PerformanceTestResult) -> Dict[str, Any]:
        """Serialize performance test result for reporting."""
        return {
            'test_name': result.test_config.name,
            'endpoint': result.test_config.endpoint,
            'success': result.success,
            'metrics_count': len(result.metrics),
            'summary': result.summary,
            'errors': result.errors
        }

    async def add_custom_performance_test(self, test_config: PerformanceTestConfig) -> bool:
        """
        Add a custom performance test configuration.

        Args:
            test_config: Test configuration to add

        Returns:
            Success status
        """
        try:
            self.test_configs.append(test_config)
            self.logger.info(f"Added custom performance test: {test_config.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add performance test: {e}")
            return False

    def get_available_tests(self) -> List[str]:
        """Get list of available performance test names."""
        return [tc.name for tc in self.test_configs]

    def get_status(self) -> Dict[str, Any]:
        """Get current status of performance test suite."""
        return {
            'base_url': self.base_url,
            'max_concurrent': self.max_concurrent,
            'test_configs_count': len(self.test_configs),
            'timeout': self.test_timeout
        }