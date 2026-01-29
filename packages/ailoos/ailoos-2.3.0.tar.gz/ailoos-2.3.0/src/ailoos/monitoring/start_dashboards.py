#!/usr/bin/env python3
"""
AILOOS Dashboard System Launcher
Unified script to start all dashboards and the management system.
"""

import asyncio
import argparse
import logging
import signal
import sys
from typing import Optional

from dashboard_manager import DashboardManager, DashboardConfig, start_unified_dashboard_system

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DashboardLauncher:
    """Launcher for the complete AILOOS dashboard system."""

    def __init__(self):
        self.manager: Optional[DashboardManager] = None
        self.running = False

    async def start_system(self, host: str = "0.0.0.0", port: int = 8000,
                          log_level: str = "INFO", enable_cors: bool = True):
        """Start the complete dashboard system."""

        logger.info("🚀 Starting AILOOS Dashboard System...")
        logger.info(f"📍 Server: {host}:{port}")
        logger.info(f"📊 Log Level: {log_level}")
        logger.info(f"🌐 CORS: {'Enabled' if enable_cors else 'Disabled'}")

        # Create configuration
        config = DashboardConfig(
            host=host,
            port=port,
            enable_cors=enable_cors,
            log_level=log_level,
            jwt_secret="ailoos-dashboard-secret-key-change-in-production",
            jwt_expiration_hours=24
        )

        try:
            # Create and start dashboard manager
            self.manager = DashboardManager(config)
            self.running = True

            logger.info("🎛️ Dashboard Manager initialized")
            logger.info("📊 Initializing individual dashboards...")

            # Start the server (this will also start all dashboards)
            await self.manager.start_server(host, port)

        except KeyboardInterrupt:
            logger.info("🛑 Shutdown requested by user")
        except Exception as e:
            logger.error(f"💥 Failed to start dashboard system: {e}")
            raise
        finally:
            if self.manager and self.manager.is_running:
                logger.info("🔄 Shutting down dashboard system...")
                await self.manager.stop_manager()
                logger.info("✅ Dashboard system shut down gracefully")

    async def stop_system(self):
        """Stop the dashboard system gracefully."""
        if self.manager and self.manager.is_running:
            logger.info("🛑 Stopping dashboard system...")
            await self.manager.stop_manager()
            self.running = False
            logger.info("✅ Dashboard system stopped")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"📡 Received signal {signum}, initiating graceful shutdown...")
        if self.running:
            # Create task to stop the system
            asyncio.create_task(self.stop_system())


def print_banner():
    """Print AILOOS dashboard system banner."""
    banner = """
    █████╗ ██╗██╗      ██████╗  ██████╗ ███████╗
    ██╔══██╗██║██║     ██╔═══██╗██╔═══██╗██╔════╝
    ███████║██║██║     ██║   ██║██║   ██║███████╗
    ██╔══██║██║██║     ██║   ██║██║   ██║╚════██║
    ██║  ██║██║███████╗╚██████╔╝╚██████╔╝███████║
    ╚═╝  ╚═╝╚═╝╚══════╝ ╚═════╝  ╚═════╝ ╚══════╝

    Unified Dashboard System v1.0.0
    Enterprise-grade monitoring for federated AI

    🔐 Authentication: JWT-based with role-based access
    📊 Dashboards: Executive, Technical, Security, Federated Learning
    🔄 Real-time: WebSocket updates and live monitoring
    🛡️ Security: Enterprise-grade with compliance tracking

    """
    print(banner)


def print_usage_info(host: str, port: int):
    """Print usage information."""
    print(f"""
    🌐 Dashboard System Started Successfully!
    📍 Access URLs:

    Main Dashboard:     http://{host}:{port}/
    Executive Dashboard: http://{host}:{port}/executive
    Technical Dashboard: http://{host}:{port}/technical
    Security Dashboard:  http://{host}:{port}/security
    Federated Dashboard: http://{host}:{port}/federated
    Admin Panel:        http://{host}:{port}/admin

    🔑 Test Users:
    • admin/admin (Full access)
    • ceo/ceo (Executive access)
    • cto/cto (Executive + Technical)
    • cso/cso (Executive + Security)
    • researcher/researcher (Federated Learning)

    📚 API Documentation:
    • REST API: http://{host}:{port}/docs
    • Health Check: http://{host}:{port}/health

    🛑 To stop: Press Ctrl+C

    """)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="AILOOS Unified Dashboard System Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_dashboards.py                    # Start on 0.0.0.0:8000
  python start_dashboards.py --host 127.0.0.1 --port 3000
  python start_dashboards.py --log-level DEBUG --no-cors
        """
    )

    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Server host (default: 0.0.0.0)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server port (default: 8000)"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)"
    )

    parser.add_argument(
        "--no-cors",
        action="store_true",
        help="Disable CORS (default: enabled)"
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Run integration tests instead of starting server"
    )

    return parser.parse_args()


async def run_tests():
    """Run integration tests."""
    print("🧪 Running Dashboard System Integration Tests...")
    try:
        from test_dashboards_integration import run_integration_tests
        success = await run_integration_tests()
        return 0 if success else 1
    except Exception as e:
        print(f"💥 Test execution failed: {e}")
        return 1


async def main():
    """Main entry point."""
    args = parse_arguments()

    if args.test:
        # Run tests instead of starting server
        exit_code = await run_tests()
        sys.exit(exit_code)

    # Print banner
    print_banner()

    # Create launcher
    launcher = DashboardLauncher()

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, launcher.signal_handler)
    signal.signal(signal.SIGTERM, launcher.signal_handler)

    try:
        # Print startup info
        print_usage_info(args.host, args.port)

        # Start the system
        await launcher.start_system(
            host=args.host,
            port=args.port,
            log_level=args.log_level,
            enable_cors=not args.no_cors
        )

    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Dashboard system shutdown requested")
        sys.exit(0)
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        sys.exit(1)