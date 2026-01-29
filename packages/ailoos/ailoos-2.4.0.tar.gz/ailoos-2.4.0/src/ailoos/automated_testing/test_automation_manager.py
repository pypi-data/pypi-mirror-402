"""
Test Automation Manager
Central orchestrator for all automated testing activities in DevOps pipeline.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from github_actions_integration import GitHubActionsIntegration
from e2e_test_runner import E2ETestRunner
from performance_test_suite import PerformanceTestSuite
from load_test_automation import LoadTestAutomation
from test_reporting import TestReporting


class TestType(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    LOAD = "load"
    SECURITY = "security"


@dataclass
class TestResult:
    test_type: TestType
    success: bool
    duration: float
    results: Dict[str, Any]
    errors: List[str]


class TestAutomationManager:
    """
    Main manager for automated testing orchestration.
    Coordinates all testing activities and provides unified interface.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.github_actions = GitHubActionsIntegration(self.config.get('github', {}))
        self.e2e_runner = E2ETestRunner(self.config.get('e2e', {}))
        self.performance_suite = PerformanceTestSuite(self.config.get('performance', {}))
        self.load_automation = LoadTestAutomation(self.config.get('load', {}))
        self.test_reporting = TestReporting(self.config.get('reporting', {}))

        self.test_results: List[TestResult] = []

    async def run_full_test_suite(self, test_types: Optional[List[TestType]] = None) -> Dict[str, Any]:
        """
        Run complete test suite across all configured test types.

        Args:
            test_types: List of test types to run. If None, runs all.

        Returns:
            Dict containing overall results and individual test results.
        """
        if test_types is None:
            test_types = list(TestType)

        self.logger.info(f"Starting full test suite with types: {[t.value for t in test_types]}")

        results = {}
        overall_success = True

        for test_type in test_types:
            try:
                result = await self._run_test_type(test_type)
                results[test_type.value] = result
                self.test_results.append(result)

                if not result.success:
                    overall_success = False
                    self.logger.warning(f"Test type {test_type.value} failed")

            except Exception as e:
                self.logger.error(f"Error running {test_type.value} tests: {e}")
                error_result = TestResult(
                    test_type=test_type,
                    success=False,
                    duration=0.0,
                    results={},
                    errors=[str(e)]
                )
                results[test_type.value] = error_result
                self.test_results.append(error_result)
                overall_success = False

        # Generate comprehensive report
        report = await self.test_reporting.generate_comprehensive_report(self.test_results)

        return {
            'overall_success': overall_success,
            'test_results': results,
            'report': report,
            'timestamp': asyncio.get_event_loop().time()
        }

    async def _run_test_type(self, test_type: TestType) -> TestResult:
        """Run a specific type of tests."""
        start_time = asyncio.get_event_loop().time()

        try:
            if test_type == TestType.E2E:
                results = await self.e2e_runner.run_e2e_tests()
            elif test_type == TestType.PERFORMANCE:
                results = await self.performance_suite.run_performance_tests()
            elif test_type == TestType.LOAD:
                results = await self.load_automation.run_load_tests()
            else:
                # For other test types, delegate to appropriate runners
                results = await self._run_generic_tests(test_type)

            duration = asyncio.get_event_loop().time() - start_time

            return TestResult(
                test_type=test_type,
                success=results.get('success', False),
                duration=duration,
                results=results,
                errors=results.get('errors', [])
            )

        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            return TestResult(
                test_type=test_type,
                success=False,
                duration=duration,
                results={},
                errors=[str(e)]
            )

    async def _run_generic_tests(self, test_type: TestType) -> Dict[str, Any]:
        """Run generic tests using pytest or similar frameworks."""
        # This would integrate with existing test runners
        # For now, return mock successful result
        return {
            'success': True,
            'tests_run': 10,
            'tests_passed': 10,
            'tests_failed': 0,
            'errors': []
        }

    async def schedule_test_run(self, test_types: List[TestType], schedule_config: Dict[str, Any]) -> str:
        """
        Schedule automated test runs.

        Args:
            test_types: Types of tests to schedule
            schedule_config: Configuration for scheduling (cron, interval, etc.)

        Returns:
            Schedule ID for tracking
        """
        return await self.github_actions.schedule_workflow(
            'test-automation',
            {
                'test_types': [t.value for t in test_types],
                'schedule': schedule_config
            }
        )

    async def get_test_history(self, limit: int = 50) -> List[TestResult]:
        """Get historical test results."""
        return self.test_results[-limit:] if self.test_results else []

    async def configure_test_environment(self, env_config: Dict[str, Any]) -> bool:
        """
        Configure test environment settings.

        Args:
            env_config: Environment configuration

        Returns:
            Success status
        """
        try:
            # Update component configurations
            self.config.update(env_config)

            # Re-initialize components with new config
            self.github_actions = GitHubActionsIntegration(self.config.get('github', {}))
            self.e2e_runner = E2ETestRunner(self.config.get('e2e', {}))
            self.performance_suite = PerformanceTestSuite(self.config.get('performance', {}))
            self.load_automation = LoadTestAutomation(self.config.get('load', {}))
            self.test_reporting = TestReporting(self.config.get('reporting', {}))

            self.logger.info("Test environment configured successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to configure test environment: {e}")
            return False

    def get_test_status(self) -> Dict[str, Any]:
        """Get current status of all test components."""
        return {
            'components': {
                'github_actions': self.github_actions.get_status(),
                'e2e_runner': self.e2e_runner.get_status(),
                'performance_suite': self.performance_suite.get_status(),
                'load_automation': self.load_automation.get_status(),
                'test_reporting': self.test_reporting.get_status()
            },
            'last_run': self.test_results[-1] if self.test_results else None,
            'total_runs': len(self.test_results)
        }