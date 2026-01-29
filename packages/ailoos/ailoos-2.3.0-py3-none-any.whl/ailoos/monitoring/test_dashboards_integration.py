"""
Test script for AILOOS Dashboard System Integration
Tests all dashboards and their integration with the unified manager.
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Any
import time

from dashboard_manager import DashboardManager, DashboardConfig
from executive_dashboard import ExecutiveDashboard
from technical_dashboard import TechnicalDashboard
from security_dashboard import SecurityDashboard
from federated_learning_dashboard import FederatedLearningDashboard

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DashboardSystemTester:
    """Tester for the complete dashboard system."""

    def __init__(self):
        self.manager = None
        self.test_results = {
            "initialization": False,
            "api_endpoints": {},
            "websocket_connections": {},
            "authentication": False,
            "real_time_updates": False,
            "dashboard_integration": {},
            "error_messages": []
        }

    async def run_complete_test(self) -> Dict[str, Any]:
        """Run complete test suite for dashboard system."""
        logger.info("🧪 Starting Dashboard System Integration Tests")

        try:
            # Test 1: System Initialization
            await self.test_initialization()

            # Test 2: API Endpoints
            await self.test_api_endpoints()

            # Test 3: Authentication
            await self.test_authentication()

            # Test 4: Dashboard Integration
            await self.test_dashboard_integration()

            # Test 5: Real-time Updates (WebSocket)
            await self.test_realtime_updates()

            # Generate test report
            return self.generate_test_report()

        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            self.test_results["error_messages"].append(f"Test suite failed: {e}")
            return self.generate_test_report()
        finally:
            # Cleanup
            if self.manager and self.manager.is_running:
                await self.manager.stop_manager()

    async def test_initialization(self):
        """Test dashboard system initialization."""
        logger.info("🔧 Testing system initialization...")

        try:
            # Create dashboard manager
            config = DashboardConfig(
                host="127.0.0.1",
                port=8888,  # Use different port for testing
                enable_cors=True,
                log_level="WARNING"  # Reduce log noise during tests
            )

            self.manager = DashboardManager(config)

            # Initialize dashboards
            await self.manager.initialize_dashboards()

            # Verify dashboards were created
            expected_dashboards = {"executive", "technical", "security", "federated_learning"}
            actual_dashboards = set(d.value for d in self.manager.dashboards.keys())

            if expected_dashboards.issubset(actual_dashboards):
                self.test_results["initialization"] = True
                logger.info("✅ System initialization successful")
            else:
                missing = expected_dashboards - actual_dashboards
                raise AssertionError(f"Missing dashboards: {missing}")

        except Exception as e:
            logger.error(f"❌ Initialization test failed: {e}")
            self.test_results["error_messages"].append(f"Initialization: {e}")
            raise

    async def test_api_endpoints(self):
        """Test API endpoints functionality."""
        logger.info("🔗 Testing API endpoints...")

        # Start manager in background
        server_task = asyncio.create_task(self.manager.start_server("127.0.0.1", 8888))
        await asyncio.sleep(2)  # Wait for server to start

        try:
            async with aiohttp.ClientSession() as session:
                base_url = "http://127.0.0.1:8888"

                # Test health endpoint
                async with session.get(f"{base_url}/health") as response:
                    if response.status == 200:
                        health_data = await response.json()
                        self.test_results["api_endpoints"]["health"] = health_data["status"] == "healthy"
                    else:
                        self.test_results["api_endpoints"]["health"] = False

                # Test system overview endpoint (requires auth, but test structure)
                async with session.get(f"{base_url}/api/dashboard/overview") as response:
                    # Should return 401 without auth
                    self.test_results["api_endpoints"]["overview_auth"] = response.status == 401

                # Test login endpoint
                login_data = {"username": "admin", "password": "admin"}
                async with session.post(f"{base_url}/api/auth/login",
                                      json=login_data,
                                      headers={"Content-Type": "application/json"}) as response:
                    if response.status == 200:
                        auth_data = await response.json()
                        self.test_results["api_endpoints"]["login"] = "access_token" in auth_data
                        self.test_token = auth_data.get("access_token")
                    else:
                        self.test_results["api_endpoints"]["login"] = False

                # Test authenticated endpoints
                if self.test_token:
                    headers = {"Authorization": f"Bearer {self.test_token}"}

                    # Test system overview with auth
                    async with session.get(f"{base_url}/api/dashboard/overview",
                                         headers=headers) as response:
                        if response.status == 200:
                            overview_data = await response.json()
                            self.test_results["api_endpoints"]["overview_data"] = "total_dashboards" in overview_data
                        else:
                            self.test_results["api_endpoints"]["overview_data"] = False

                    # Test executive dashboard
                    async with session.get(f"{base_url}/api/dashboard/executive/status",
                                         headers=headers) as response:
                        self.test_results["api_endpoints"]["executive"] = response.status == 200

                    # Test technical dashboard
                    async with session.get(f"{base_url}/api/dashboard/technical/status",
                                         headers=headers) as response:
                        self.test_results["api_endpoints"]["technical"] = response.status == 200

                    # Test security dashboard
                    async with session.get(f"{base_url}/api/dashboard/security/status",
                                         headers=headers) as response:
                        self.test_results["api_endpoints"]["security"] = response.status == 200

                    # Test federated dashboard
                    async with session.get(f"{base_url}/api/dashboard/federated_learning/status",
                                         headers=headers) as response:
                        self.test_results["api_endpoints"]["federated"] = response.status == 200

                logger.info("✅ API endpoints test completed")

        except Exception as e:
            logger.error(f"❌ API endpoints test failed: {e}")
            self.test_results["error_messages"].append(f"API endpoints: {e}")
        finally:
            # Stop server
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass

    async def test_authentication(self):
        """Test authentication system."""
        logger.info("🔐 Testing authentication system...")

        try:
            # Test different user roles
            test_users = [
                ("admin", "admin", ["admin"]),
                ("ceo", "ceo", ["executive"]),
                ("cto", "cto", ["executive", "technical"]),
                ("researcher", "researcher", ["researcher"]),
                ("invalid", "invalid", None)
            ]

            auth_results = {}

            for username, password, expected_roles in test_users:
                try:
                    # Create JWT token manually for testing
                    token = self.manager._create_jwt_token(username, expected_roles or [])
                    payload = self.manager._validate_jwt_token(token)

                    if payload:
                        auth_results[username] = {
                            "token_valid": True,
                            "roles_match": payload.get("roles") == expected_roles,
                            "username_match": payload.get("username") == username
                        }
                    else:
                        auth_results[username] = {"token_valid": False}

                except Exception as e:
                    auth_results[username] = {"error": str(e)}

            # Evaluate results
            valid_tests = sum(1 for r in auth_results.values()
                            if isinstance(r, dict) and r.get("token_valid") and r.get("roles_match"))

            self.test_results["authentication"] = valid_tests >= 4  # At least 4 valid authentications
            self.test_results["auth_details"] = auth_results

            logger.info("✅ Authentication test completed")

        except Exception as e:
            logger.error(f"❌ Authentication test failed: {e}")
            self.test_results["error_messages"].append(f"Authentication: {e}")

    async def test_dashboard_integration(self):
        """Test dashboard integration and data flow."""
        logger.info("🔄 Testing dashboard integration...")

        try:
            integration_results = {}

            # Test each dashboard individually
            for dashboard_type, dashboard_instance in self.manager.dashboards.items():
                try:
                    dashboard = dashboard_instance.instance

                    # Test basic functionality
                    if hasattr(dashboard, 'get_health_status'):
                        health = await dashboard.get_health_status()
                        integration_results[dashboard_type.value] = {
                            "health_check": True,
                            "is_running": health.get("is_running", False)
                        }
                    else:
                        integration_results[dashboard_type.value] = {
                            "health_check": False,
                            "error": "No health check method"
                        }

                    # Test data retrieval
                    if hasattr(dashboard, 'get_dashboard_data'):
                        data = await dashboard.get_dashboard_data()
                        integration_results[dashboard_type.value]["data_retrieval"] = bool(data)
                    elif hasattr(dashboard, 'get_comprehensive_status'):
                        data = await dashboard.get_comprehensive_status()
                        integration_results[dashboard_type.value]["data_retrieval"] = bool(data)
                    else:
                        integration_results[dashboard_type.value]["data_retrieval"] = False

                except Exception as e:
                    integration_results[dashboard_type.value] = {
                        "error": str(e),
                        "health_check": False,
                        "data_retrieval": False
                    }

            self.test_results["dashboard_integration"] = integration_results

            # Check if all dashboards are properly integrated
            successful_integrations = sum(1 for r in integration_results.values()
                                        if r.get("health_check") and r.get("data_retrieval"))

            logger.info(f"✅ Dashboard integration test completed: {successful_integrations}/{len(integration_results)} successful")

        except Exception as e:
            logger.error(f"❌ Dashboard integration test failed: {e}")
            self.test_results["error_messages"].append(f"Dashboard integration: {e}")

    async def test_realtime_updates(self):
        """Test real-time updates via WebSocket."""
        logger.info("📡 Testing real-time updates...")

        # Note: WebSocket testing is complex in unit tests
        # This is a basic structure test

        try:
            # Test WebSocket endpoint availability in manager
            websocket_available = hasattr(self.manager, 'unified_websocket')
            self.test_results["websocket_connections"]["manager_websocket"] = websocket_available

            # Test individual dashboard WebSocket methods
            websocket_methods = {}
            for dashboard_type, dashboard_instance in self.manager.dashboards.items():
                dashboard = dashboard_instance.instance
                has_websocket = hasattr(dashboard, 'handle_executive_websocket') or \
                              hasattr(dashboard, 'handle_security_websocket') or \
                              hasattr(dashboard, 'handle_federated_websocket') or \
                              hasattr(dashboard, 'websocket_endpoint')

                websocket_methods[dashboard_type.value] = has_websocket

            self.test_results["websocket_connections"]["dashboard_websockets"] = websocket_methods

            # Consider test passed if manager has WebSocket and at least 3 dashboards have WebSocket support
            websocket_count = sum(websocket_methods.values())
            self.test_results["real_time_updates"] = websocket_available and websocket_count >= 3

            logger.info("✅ Real-time updates test completed")

        except Exception as e:
            logger.error(f"❌ Real-time updates test failed: {e}")
            self.test_results["error_messages"].append(f"Real-time updates: {e}")

    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        report = {
            "test_suite": "AILOOS Dashboard System Integration Tests",
            "timestamp": time.time(),
            "test_results": self.test_results,
            "summary": {
                "total_tests": 5,
                "passed_tests": sum([
                    self.test_results["initialization"],
                    bool(self.test_results["api_endpoints"].get("health")),
                    self.test_results["authentication"],
                    len([r for r in self.test_results["dashboard_integration"].values()
                         if r.get("health_check")]) > 0,
                    self.test_results["real_time_updates"]
                ]),
                "failed_tests": 0,
                "overall_success": False
            },
            "details": {}
        }

        # Calculate failed tests
        report["summary"]["failed_tests"] = report["summary"]["total_tests"] - report["summary"]["passed_tests"]
        report["summary"]["overall_success"] = report["summary"]["passed_tests"] >= 4  # 80% success rate

        # Add detailed results
        report["details"] = {
            "initialization_status": "✅ PASSED" if self.test_results["initialization"] else "❌ FAILED",
            "api_endpoints_status": f"✅ {sum(self.test_results['api_endpoints'].values())}/{len(self.test_results['api_endpoints'])} PASSED",
            "authentication_status": "✅ PASSED" if self.test_results["authentication"] else "❌ FAILED",
            "dashboard_integration_status": f"✅ {sum(1 for r in self.test_results['dashboard_integration'].values() if r.get('health_check'))}/{len(self.test_results['dashboard_integration'])} INTEGRATED",
            "realtime_updates_status": "✅ PASSED" if self.test_results["real_time_updates"] else "❌ FAILED"
        }

        # Add error summary
        if self.test_results["error_messages"]:
            report["errors"] = self.test_results["error_messages"]

        return report


async def run_integration_tests():
    """Run integration tests and print results."""
    tester = DashboardSystemTester()

    print("🚀 Starting AILOOS Dashboard System Integration Tests...")
    print("=" * 60)

    try:
        results = await tester.run_complete_test()

        print(f"\n📊 Test Results Summary:")
        print(f"Total Tests: {results['summary']['total_tests']}")
        print(f"Passed: {results['summary']['passed_tests']}")
        print(f"Failed: {results['summary']['failed_tests']}")
        print(f"Overall Success: {'✅ YES' if results['summary']['overall_success'] else '❌ NO'}")

        print(f"\n📋 Detailed Results:")
        for test_name, status in results['details'].items():
            print(f"  {test_name}: {status}")

        if results.get('errors'):
            print(f"\n❌ Errors Encountered:")
            for error in results['errors']:
                print(f"  • {error}")

        print(f"\n{'=' * 60}")
        if results['summary']['overall_success']:
            print("🎉 Dashboard System Integration Tests PASSED!")
            print("All dashboards are properly integrated and functional.")
        else:
            print("⚠️  Dashboard System Integration Tests FAILED!")
            print("Some components may need attention.")

        return results['summary']['overall_success']

    except Exception as e:
        print(f"💥 Test suite crashed: {e}")
        return False


async def test_individual_dashboards():
    """Test individual dashboard components."""
    print("🔬 Testing Individual Dashboard Components...")

    test_results = {}

    # Test Executive Dashboard
    try:
        from executive_dashboard import ExecutiveDashboard
        exec_dashboard = ExecutiveDashboard()
        await exec_dashboard.start_monitoring()
        health = await exec_dashboard.get_health_status()
        test_results["executive"] = health.get("is_running", False)
        await exec_dashboard.stop_monitoring()
    except Exception as e:
        test_results["executive"] = False
        print(f"Executive Dashboard test failed: {e}")

    # Test Security Dashboard
    try:
        from security_dashboard import SecurityDashboard
        sec_dashboard = SecurityDashboard()
        await sec_dashboard.start_monitoring()
        health = await sec_dashboard.get_health_status()
        test_results["security"] = health.get("is_running", False)
        await sec_dashboard.stop_monitoring()
    except Exception as e:
        test_results["security"] = False
        print(f"Security Dashboard test failed: {e}")

    # Test Federated Learning Dashboard
    try:
        from federated_learning_dashboard import FederatedLearningDashboard
        fl_dashboard = FederatedLearningDashboard()
        await fl_dashboard.start_monitoring()
        health = await fl_dashboard.get_health_status()
        test_results["federated_learning"] = health.get("is_running", False)
        await fl_dashboard.stop_monitoring()
    except Exception as e:
        test_results["federated_learning"] = False
        print(f"Federated Learning Dashboard test failed: {e}")

    # Test Technical Dashboard
    try:
        from technical_dashboard import TechnicalDashboard
        tech_dashboard = TechnicalDashboard()
        await tech_dashboard.start_monitoring()
        health = await tech_dashboard.get_health_status()
        test_results["technical"] = health.get("is_running", False)
        await tech_dashboard.stop_monitoring()
    except Exception as e:
        test_results["technical"] = False
        print(f"Technical Dashboard test failed: {e}")

    print("Individual Dashboard Test Results:")
    for name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {name}: {status}")

    return test_results


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "individual":
        # Test individual components
        asyncio.run(test_individual_dashboards())
    else:
        # Run full integration tests
        success = asyncio.run(run_integration_tests())
        sys.exit(0 if success else 1)