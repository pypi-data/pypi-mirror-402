"""
Load Test Automation
Automates load testing to simulate high traffic and stress test system capacity.
"""

import asyncio
import logging
import time
import statistics
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import aiohttp
import numpy as np


class LoadPattern(Enum):
    CONSTANT = "constant"
    RAMP_UP = "ramp_up"
    SPIKE = "spike"
    WAVE = "wave"
    RANDOM = "random"


@dataclass
class LoadTestScenario:
    name: str
    endpoint: str
    method: str = "GET"
    payload: Optional[Dict] = None
    headers: Optional[Dict[str, str]] = None
    load_pattern: LoadPattern = LoadPattern.RAMP_UP
    min_users: int = 1
    max_users: int = 100
    duration: int = 300  # 5 minutes
    spawn_rate: float = 1.0  # users per second


@dataclass
class LoadTestResult:
    scenario: LoadTestScenario
    success: bool
    total_requests: int
    successful_requests: int
    failed_requests: int
    response_times: List[float]
    throughput: float  # requests per second
    error_rate: float
    percentiles: Dict[str, float]
    summary: Dict[str, Any]


class LoadTestAutomation:
    """
    Automated load testing system for stress testing and capacity planning.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)

        self.base_url = config.get('base_url', 'http://localhost:8000')
        self.max_concurrent_users = config.get('max_concurrent_users', 1000)
        self.test_timeout = config.get('timeout', 600)  # 10 minutes

        # Predefined load test scenarios
        self.scenarios = self._load_scenarios()

    def _load_scenarios(self) -> List[LoadTestScenario]:
        """Load predefined load test scenarios."""
        return [
            LoadTestScenario(
                name="basic_api_load",
                endpoint="/api/health",
                method="GET",
                load_pattern=LoadPattern.RAMP_UP,
                min_users=10,
                max_users=200,
                duration=180,
                spawn_rate=5.0
            ),
            LoadTestScenario(
                name="data_processing_stress",
                endpoint="/api/data/process",
                method="POST",
                payload={"operation": "heavy_computation", "data_size": "large"},
                load_pattern=LoadPattern.CONSTANT,
                min_users=50,
                max_users=50,
                duration=240
            ),
            LoadTestScenario(
                name="federated_network_load",
                endpoint="/api/federated/sync",
                method="POST",
                payload={"nodes": 100, "data_transfer": "high"},
                load_pattern=LoadPattern.WAVE,
                min_users=20,
                max_users=100,
                duration=300,
                spawn_rate=2.0
            ),
            LoadTestScenario(
                name="file_upload_stress",
                endpoint="/api/files/upload",
                method="POST",
                payload={"file_size": "50MB", "concurrent_uploads": True},
                load_pattern=LoadPattern.SPIKE,
                min_users=1,
                max_users=20,
                duration=120
            ),
            LoadTestScenario(
                name="search_high_load",
                endpoint="/api/search",
                method="POST",
                payload={"query": "complex query with filters", "result_limit": 1000},
                load_pattern=LoadPattern.RANDOM,
                min_users=100,
                max_users=500,
                duration=360,
                spawn_rate=10.0
            )
        ]

    async def run_load_tests(self, scenario_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run load tests for specified scenarios.

        Args:
            scenario_names: List of scenario names to run. If None, runs all.

        Returns:
            Load test results summary
        """
        self.logger.info("Starting load test execution")

        if scenario_names:
            scenarios_to_run = [s for s in self.scenarios if s.name in scenario_names]
        else:
            scenarios_to_run = self.scenarios

        results = []
        total_passed = 0

        for scenario in scenarios_to_run:
            self.logger.info(f"Running load test scenario: {scenario.name}")
            result = await self._execute_load_test(scenario)
            results.append(result)

            if result.success:
                total_passed += 1

        # Calculate overall statistics
        overall_stats = self._calculate_overall_statistics(results)

        return {
            'success': total_passed == len(scenarios_to_run),
            'total_scenarios': len(scenarios_to_run),
            'passed': total_passed,
            'failed': len(scenarios_to_run) - total_passed,
            'overall_statistics': overall_stats,
            'results': [self._serialize_result(r) for r in results],
            'total_duration': sum(r.summary.get('duration', 0) for r in results)
        }

    async def _execute_load_test(self, scenario: LoadTestScenario) -> LoadTestResult:
        """Execute a single load test scenario."""
        start_time = time.time()
        response_times = []
        successful_requests = 0
        failed_requests = 0

        try:
            # Generate user load pattern
            user_pattern = self._generate_user_pattern(scenario)

            # Run load test with the pattern
            async with aiohttp.ClientSession() as session:
                tasks = []

                for user_count in user_pattern:
                    # Create tasks for current user count
                    user_tasks = [
                        self._simulate_user_request(session, scenario, i)
                        for i in range(user_count)
                    ]
                    tasks.extend(user_tasks)

                    # Limit concurrent tasks to avoid overwhelming the system
                    if len(tasks) > self.max_concurrent_users:
                        # Execute in batches
                        batch_results = await asyncio.gather(*tasks[:self.max_concurrent_users], return_exceptions=True)
                        tasks = tasks[self.max_concurrent_users:]

                        # Process batch results
                        for result in batch_results:
                            if isinstance(result, Exception):
                                failed_requests += 1
                            else:
                                response_times.append(result)
                                successful_requests += 1

                # Execute remaining tasks
                if tasks:
                    remaining_results = await asyncio.gather(*tasks, return_exceptions=True)
                    for result in remaining_results:
                        if isinstance(result, Exception):
                            failed_requests += 1
                        else:
                            response_times.append(result)
                            successful_requests += 1

            total_requests = successful_requests + failed_requests
            duration = time.time() - start_time
            throughput = total_requests / duration if duration > 0 else 0
            error_rate = failed_requests / total_requests if total_requests > 0 else 0

            # Calculate percentiles
            percentiles = {}
            if response_times:
                sorted_times = sorted(response_times)
                percentiles = {
                    '50th': np.percentile(sorted_times, 50),
                    '75th': np.percentile(sorted_times, 75),
                    '90th': np.percentile(sorted_times, 90),
                    '95th': np.percentile(sorted_times, 95),
                    '99th': np.percentile(sorted_times, 99)
                }

            success = error_rate < 0.1  # Less than 10% error rate

            summary = {
                'duration': duration,
                'total_requests': total_requests,
                'throughput_rps': throughput,
                'avg_response_time': statistics.mean(response_times) if response_times else 0,
                'min_response_time': min(response_times) if response_times else 0,
                'max_response_time': max(response_times) if response_times else 0,
                'error_rate': error_rate
            }

            return LoadTestResult(
                scenario=scenario,
                success=success,
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                response_times=response_times,
                throughput=throughput,
                error_rate=error_rate,
                percentiles=percentiles,
                summary=summary
            )

        except Exception as e:
            self.logger.error(f"Error executing load test {scenario.name}: {e}")
            duration = time.time() - start_time

            return LoadTestResult(
                scenario=scenario,
                success=False,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                response_times=[],
                throughput=0,
                error_rate=1.0,
                percentiles={},
                summary={'duration': duration, 'error': str(e)}
            )

    def _generate_user_pattern(self, scenario: LoadTestScenario) -> List[int]:
        """Generate user load pattern based on scenario configuration."""
        pattern = []

        if scenario.load_pattern == LoadPattern.CONSTANT:
            # Constant load
            users_per_second = scenario.max_users
            total_seconds = scenario.duration
            pattern = [users_per_second] * total_seconds

        elif scenario.load_pattern == LoadPattern.RAMP_UP:
            # Linear ramp up
            total_seconds = scenario.duration
            for i in range(total_seconds):
                progress = i / total_seconds
                current_users = int(scenario.min_users + (scenario.max_users - scenario.min_users) * progress)
                pattern.append(current_users)

        elif scenario.load_pattern == LoadPattern.SPIKE:
            # Spike pattern: low -> high -> low
            total_seconds = scenario.duration
            spike_start = total_seconds // 3
            spike_end = 2 * total_seconds // 3

            for i in range(total_seconds):
                if spike_start <= i < spike_end:
                    pattern.append(scenario.max_users)
                else:
                    pattern.append(scenario.min_users)

        elif scenario.load_pattern == LoadPattern.WAVE:
            # Sine wave pattern
            total_seconds = scenario.duration
            import math
            for i in range(total_seconds):
                # Sine wave between min and max users
                wave = math.sin(2 * math.pi * i / 60)  # 60 second period
                normalized = (wave + 1) / 2  # 0 to 1
                current_users = int(scenario.min_users + (scenario.max_users - scenario.min_users) * normalized)
                pattern.append(current_users)

        elif scenario.load_pattern == LoadPattern.RANDOM:
            # Random pattern
            total_seconds = scenario.duration
            import random
            for _ in range(total_seconds):
                current_users = random.randint(scenario.min_users, scenario.max_users)
                pattern.append(current_users)

        return pattern

    async def _simulate_user_request(self, session: aiohttp.ClientSession,
                                   scenario: LoadTestScenario,
                                   user_id: int) -> float:
        """Simulate a single user request and return response time."""
        start_time = time.time()

        try:
            url = f"{self.base_url}{scenario.endpoint}"
            headers = scenario.headers or {}

            if scenario.method == "GET":
                async with session.get(url, headers=headers) as response:
                    await response.text()
            elif scenario.method == "POST":
                async with session.post(url, json=scenario.payload, headers=headers) as response:
                    await response.text()
            # Add other methods as needed

            response_time = time.time() - start_time
            return response_time

        except Exception as e:
            # Re-raise exception to be caught by caller
            raise e

    def _calculate_overall_statistics(self, results: List[LoadTestResult]) -> Dict[str, Any]:
        """Calculate overall statistics across all load test results."""
        if not results:
            return {}

        total_requests = sum(r.total_requests for r in results)
        total_successful = sum(r.successful_requests for r in results)
        total_failed = sum(r.failed_requests for r in results)

        all_response_times = []
        for r in results:
            all_response_times.extend(r.response_times)

        stats = {
            'total_requests_all_scenarios': total_requests,
            'total_successful_all_scenarios': total_successful,
            'total_failed_all_scenarios': total_failed,
            'overall_error_rate': total_failed / total_requests if total_requests > 0 else 0
        }

        if all_response_times:
            stats.update({
                'overall_avg_response_time': statistics.mean(all_response_times),
                'overall_median_response_time': statistics.median(all_response_times),
                'overall_max_response_time': max(all_response_times),
                'overall_min_response_time': min(all_response_times)
            })

        return stats

    def _serialize_result(self, result: LoadTestResult) -> Dict[str, Any]:
        """Serialize load test result for reporting."""
        return {
            'scenario_name': result.scenario.name,
            'endpoint': result.scenario.endpoint,
            'success': result.success,
            'total_requests': result.total_requests,
            'successful_requests': result.successful_requests,
            'failed_requests': result.failed_requests,
            'throughput_rps': result.throughput,
            'error_rate': result.error_rate,
            'percentiles': result.percentiles,
            'summary': result.summary
        }

    async def add_custom_load_scenario(self, scenario: LoadTestScenario) -> bool:
        """
        Add a custom load test scenario.

        Args:
            scenario: Scenario to add

        Returns:
            Success status
        """
        try:
            self.scenarios.append(scenario)
            self.logger.info(f"Added custom load scenario: {scenario.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add load scenario: {e}")
            return False

    def get_available_scenarios(self) -> List[str]:
        """Get list of available load test scenario names."""
        return [s.name for s in self.scenarios]

    def get_status(self) -> Dict[str, Any]:
        """Get current status of load test automation."""
        return {
            'base_url': self.base_url,
            'max_concurrent_users': self.max_concurrent_users,
            'scenarios_count': len(self.scenarios),
            'timeout': self.test_timeout
        }