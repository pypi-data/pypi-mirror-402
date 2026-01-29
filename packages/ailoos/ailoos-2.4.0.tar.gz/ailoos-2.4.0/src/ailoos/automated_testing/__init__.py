"""
Automated Testing Module for DevOps Advanced
Provides comprehensive test automation capabilities including
unit tests, integration tests, E2E tests, performance tests, and load tests.
"""

# Direct imports to avoid dependency on main ailoos package
from test_automation_manager import TestAutomationManager
from github_actions_integration import GitHubActionsIntegration
from e2e_test_runner import E2ETestRunner
from performance_test_suite import PerformanceTestSuite
from load_test_automation import LoadTestAutomation
from test_reporting import TestReporting

__all__ = [
    'TestAutomationManager',
    'GitHubActionsIntegration',
    'E2ETestRunner',
    'PerformanceTestSuite',
    'LoadTestAutomation',
    'TestReporting'
]