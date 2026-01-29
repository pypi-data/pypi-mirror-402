"""
Automated Testing Demo
Demonstrates the complete automated testing system for DevOps Advanced.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add automated_testing module to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'automated_testing'))

from test_automation_manager import TestAutomationManager
from github_actions_integration import GitHubActionsIntegration
from e2e_test_runner import E2ETestRunner
from performance_test_suite import PerformanceTestSuite
from load_test_automation import LoadTestAutomation
from test_reporting import TestReporting


async def main():
    """Main demo function showcasing the automated testing system."""

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    logger.info("Starting Automated Testing Demo")

    # Configuration for the testing system
    config = {
        'github': {
            'token': 'your_github_token_here',  # Replace with actual token
            'owner': 'your-org',
            'repo': 'your-repo',
            'branch': 'main'
        },
        'e2e': {
            'environment': 'staging',
            'base_url': 'http://localhost:8000',  # Replace with actual staging URL
            'browser': {'headless': True, 'type': 'chromium'},
            'timeout': 300
        },
        'performance': {
            'base_url': 'http://localhost:8000',  # Replace with actual API URL
            'max_concurrent': 50,
            'timeout': 120
        },
        'load': {
            'base_url': 'http://localhost:8000',  # Replace with actual API URL
            'max_concurrent_users': 100,
            'timeout': 300
        },
        'reporting': {
            'reports_dir': 'test_reports'
        }
    }

    try:
        # Initialize the Test Automation Manager
        logger.info("Initializing Test Automation Manager...")
        manager = TestAutomationManager(config)

        # Demonstrate individual component status
        logger.info("Checking component statuses...")
        status = manager.get_test_status()
        logger.info(f"Component Status: {status}")

        # Run a comprehensive test suite
        logger.info("Running comprehensive test suite...")
        test_result = await manager.run_full_test_suite()

        logger.info(f"Test Suite Results: {test_result['overall_success']}")
        logger.info(f"Success Rate: {test_result['overall_success']}")
        logger.info(f"Report Generated: {test_result['report']['files']['html']}")

        # Demonstrate scheduling tests
        logger.info("Scheduling automated tests...")
        schedule_config = {
            'cron': '0 2 * * *',  # Daily at 2 AM
            'branch': 'main'
        }
        schedule_id = await manager.schedule_test_run(
            ['e2e', 'performance'],
            schedule_config
        )
        logger.info(f"Scheduled test run with ID: {schedule_id}")

        # Demonstrate adding custom tests
        logger.info("Adding custom test cases...")

        # Add custom E2E test
        from ailoos.automated_testing.e2e_test_runner import E2ETestCase
        custom_e2e_test = E2ETestCase(
            name="custom_user_journey",
            description="Custom user registration and data upload journey",
            steps=[
                {"action": "navigate", "url": "/register"},
                {"action": "fill_form", "selector": "#email", "value": "custom@example.com"},
                {"action": "fill_form", "selector": "#password", "value": "custompass123"},
                {"action": "click", "selector": "#register-btn"},
                {"action": "wait_for", "selector": ".dashboard"},
                {"action": "navigate", "url": "/upload"},
                {"action": "api_call", "method": "POST", "endpoint": "/api/upload", "data": {"file": "test.csv"}}
            ],
            expected_outcomes=[
                "User registration completes successfully",
                "Dashboard loads after registration",
                "File upload works correctly"
            ]
        )

        await manager.e2e_runner.add_custom_test_case(custom_e2e_test)
        logger.info("Added custom E2E test case")

        # Add custom performance test
        from ailoos.automated_testing.performance_test_suite import PerformanceTestConfig
        custom_perf_test = PerformanceTestConfig(
            name="custom_api_performance",
            endpoint="/api/custom/endpoint",
            method="POST",
            payload={"operation": "custom_processing", "size": "large"},
            concurrent_users=25,
            duration=90
        )

        await manager.performance_suite.add_custom_performance_test(custom_perf_test)
        logger.info("Added custom performance test")

        # Add custom load test
        from ailoos.automated_testing.load_test_automation import LoadTestScenario, LoadPattern
        custom_load_test = LoadTestScenario(
            name="custom_load_test",
            endpoint="/api/heavy-processing",
            method="POST",
            payload={"data": "large_dataset", "iterations": 100},
            load_pattern=LoadPattern.WAVE,
            min_users=10,
            max_users=50,
            duration=180
        )

        await manager.load_automation.add_custom_load_scenario(custom_load_test)
        logger.info("Added custom load test scenario")

        # Run tests with custom additions
        logger.info("Running tests with custom additions...")
        updated_result = await manager.run_full_test_suite()

        logger.info(f"Updated Test Results: Success = {updated_result['overall_success']}")

        # Get test history
        logger.info("Retrieving test history...")
        history = await manager.get_test_history(limit=5)
        logger.info(f"Found {len(history)} historical test runs")

        # Demonstrate report history
        logger.info("Checking report history...")
        report_history = await manager.test_reporting.get_report_history(limit=3)
        logger.info(f"Found {len(report_history)} generated reports")

        logger.info("Automated Testing Demo completed successfully!")

        return {
            'success': True,
            'initial_test_results': test_result,
            'updated_test_results': updated_result,
            'schedule_id': schedule_id,
            'reports_generated': len(report_history) + 2  # Initial + updated
        }

    except Exception as e:
        logger.error(f"Demo failed with error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


async def run_individual_components_demo():
    """Demo showcasing individual components independently."""

    logger = logging.getLogger(__name__)
    logger.info("Running Individual Components Demo")

    # Demo E2E Test Runner
    logger.info("Demo: E2E Test Runner")
    e2e_config = {
        'environment': 'local',
        'base_url': 'http://localhost:8000',
        'browser': {'headless': True},
        'timeout': 60
    }
    e2e_runner = E2ETestRunner(e2e_config)

    available_tests = e2e_runner.get_available_tests()
    logger.info(f"Available E2E tests: {available_tests}")

    # Demo Performance Test Suite
    logger.info("Demo: Performance Test Suite")
    perf_config = {
        'base_url': 'http://localhost:8000',
        'max_concurrent': 20,
        'timeout': 60
    }
    perf_suite = PerformanceTestSuite(perf_config)

    available_perf_tests = perf_suite.get_available_tests()
    logger.info(f"Available performance tests: {available_perf_tests}")

    # Demo Load Test Automation
    logger.info("Demo: Load Test Automation")
    load_config = {
        'base_url': 'http://localhost:8000',
        'max_concurrent_users': 50,
        'timeout': 120
    }
    load_automation = LoadTestAutomation(load_config)

    available_load_scenarios = load_automation.get_available_scenarios()
    logger.info(f"Available load test scenarios: {available_load_scenarios}")

    # Demo Test Reporting
    logger.info("Demo: Test Reporting")
    reporting_config = {
        'reports_dir': 'demo_reports'
    }
    test_reporting = TestReporting(reporting_config)

    status = test_reporting.get_status()
    logger.info(f"Reporting status: {status}")

    logger.info("Individual Components Demo completed")


if __name__ == "__main__":
    print("Automated Testing System Demo")
    print("=" * 50)

    # Run main demo
    result = asyncio.run(main())

    if result['success']:
        print("✅ Main demo completed successfully!")
        print(f"📊 Initial test success: {result['initial_test_results']['overall_success']}")
        print(f"📊 Updated test success: {result['updated_test_results']['overall_success']}")
        print(f"📅 Scheduled test ID: {result['schedule_id']}")
        print(f"📄 Reports generated: {result['reports_generated']}")
    else:
        print(f"❌ Main demo failed: {result['error']}")

    print("\n" + "=" * 50)

    # Run individual components demo
    asyncio.run(run_individual_components_demo())

    print("\nDemo completed! Check the generated reports in the test_reports directory.")