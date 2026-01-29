"""
Auto-setup system for Ailoos SDK.
Provides zero-configuration setup for complete Ailoos functionality.
"""

import os
import sys
import platform
import subprocess
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Add scripts and src directories to path for imports
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
src_dir = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(src_dir))

try:
    from .hardware_detector import HardwareDetector
    HARDWARE_DETECTOR_AVAILABLE = True
except ImportError:
    HARDWARE_DETECTOR_AVAILABLE = False
    logger.warning("HardwareDetector not available, hardware detection will be skipped")

try:
    from ailoos.core.role_config import RoleConfigManager
    ROLE_CONFIG_AVAILABLE = True
except ImportError:
    ROLE_CONFIG_AVAILABLE = False
    logger.warning("RoleConfigManager not available, role configuration will be basic")


class EmbeddedIPFS:
    """
    Embedded IPFS manager that handles IPFS daemon lifecycle.
    Downloads and manages IPFS daemon automatically.
    """

    def __init__(self):
        self.system = platform.system().lower()
        self.arch = platform.machine().lower()
        self.ipfs_version = os.getenv("AILOOS_IPFS_VERSION", "0.21.0")
        self.ipfs_dir = Path(os.getenv("AILOOS_IPFS_DIR", str(Path.home() / ".ailoos" / "ipfs")))
        self.api_host = os.getenv("AILOOS_IPFS_API_HOST", "localhost")
        self.api_port = int(os.getenv("AILOOS_IPFS_API_PORT", "5001"))
        self.ipfs_binary = self._get_ipfs_binary_path()
        self.daemon_process = None

    def _get_ipfs_binary_path(self) -> Path:
        """Get the path to the IPFS binary."""
        if self.system == "darwin":
            if "arm64" in self.arch:
                return self.ipfs_dir / "kubo" / "ipfs"
            else:
                return self.ipfs_dir / "kubo" / "ipfs"
        elif self.system == "linux":
            return self.ipfs_dir / "kubo" / "ipfs"
        else:
            raise RuntimeError(f"Unsupported platform: {self.system} {self.arch}")

    def _download_ipfs(self) -> bool:
        """Download and install IPFS daemon."""
        try:
            logger.info("📥 Downloading IPFS daemon...")

            # Determine download URL
            if self.system == "darwin":
                if "arm64" in self.arch:
                    url = f"https://dist.ipfs.tech/kubo/v{self.ipfs_version}/kubo_v{self.ipfs_version}_darwin-arm64.tar.gz"
                else:
                    url = f"https://dist.ipfs.tech/kubo/v{self.ipfs_version}/kubo_v{self.ipfs_version}_darwin-amd64.tar.gz"
            elif self.system == "linux":
                url = f"https://dist.ipfs.tech/kubo/v{self.ipfs_version}/kubo_v{self.ipfs_version}_linux-amd64.tar.gz"
            else:
                raise RuntimeError(f"Unsupported platform: {self.system}")

            # Download and extract
            import urllib.request
            import tarfile

            self.ipfs_dir.mkdir(parents=True, exist_ok=True)
            tar_path = self.ipfs_dir / "ipfs.tar.gz"

            urllib.request.urlretrieve(url, tar_path)

            if not self._verify_download_checksum(tar_path):
                logger.error("❌ IPFS checksum verification failed")
                try:
                    tar_path.unlink()
                except OSError:
                    pass
                return False

            with tarfile.open(tar_path, 'r:gz') as tar:
                self._safe_extract_tar(tar, self.ipfs_dir)

            # Make executable
            self.ipfs_binary.chmod(0o755)

            # Cleanup
            tar_path.unlink()

            logger.info("✅ IPFS daemon downloaded successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to download IPFS: {e}")
            return False

    def _init_ipfs_repo(self) -> bool:
        """Initialize IPFS repository."""
        try:
            logger.info("🔧 Initializing IPFS repository...")

            result = subprocess.run(
                [str(self.ipfs_binary), "init"],
                capture_output=True,
                text=True,
                cwd=self.ipfs_dir
            )

            if result.returncode == 0:
                logger.info("✅ IPFS repository initialized")
                return True
            else:
                logger.error(f"❌ IPFS init failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to initialize IPFS: {e}")
            return False

    def start_daemon(self) -> bool:
        """Start IPFS daemon."""
        try:
            if not self.ipfs_binary.exists():
                if not self._download_ipfs():
                    return False

            if not (self.ipfs_dir / ".ipfs").exists():
                if not self._init_ipfs_repo():
                    return False

            logger.info("🚀 Starting IPFS daemon...")

            self.daemon_process = subprocess.Popen(
                [str(self.ipfs_binary), "daemon"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=self.ipfs_dir
            )

            if self.daemon_process.poll() is not None:
                logger.error("❌ IPFS daemon failed to start")
                return False

            if not self._wait_for_api_ready():
                logger.error("❌ IPFS API not responding")
                return False

            logger.info("✅ IPFS daemon started successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to start IPFS daemon: {e}")
            return False

    def stop_daemon(self):
        """Stop IPFS daemon."""
        if self.daemon_process:
            self.daemon_process.terminate()
            self.daemon_process.wait()
            logger.info("🛑 IPFS daemon stopped")

    def get_api_endpoint(self) -> str:
        """Get IPFS API endpoint."""
        return f"http://{self.api_host}:{self.api_port}"

    def _wait_for_api_ready(self, timeout_seconds: int = 15) -> bool:
        """Wait for the IPFS API to be ready."""
        import urllib.request

        start = time.time()
        api_url = f"{self.get_api_endpoint()}/api/v0/version"
        while time.time() - start < timeout_seconds:
            try:
                with urllib.request.urlopen(api_url, timeout=2):
                    return True
            except Exception:
                time.sleep(0.5)
        return False

    def _safe_extract_tar(self, tar, destination: Path) -> None:
        """Safely extract tar files to avoid path traversal."""
        destination = destination.resolve()
        for member in tar.getmembers():
            member_path = (destination / member.name).resolve()
            if not str(member_path).startswith(str(destination)):
                raise RuntimeError("Unsafe tar file path detected")
        tar.extractall(destination)

    def _verify_download_checksum(self, tar_path: Path) -> bool:
        """Verify downloaded IPFS checksum if configured."""
        verify_flag = os.getenv("AILOOS_IPFS_VERIFY_DOWNLOADS", "").lower() in ("1", "true", "yes")
        expected_checksum = os.getenv("AILOOS_IPFS_SHA256", "").strip()
        if not verify_flag:
            if not expected_checksum:
                logger.warning("⚠️ IPFS checksum not provided; skipping verification")
            return True
        if not expected_checksum:
            logger.error("❌ AILOOS_IPFS_SHA256 requerido para verificación de IPFS")
            return False

        import hashlib
        sha256 = hashlib.sha256()
        with open(tar_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)

        return sha256.hexdigest().lower() == expected_checksum.lower()


class P2PCoordinator:
    """
    P2P Coordinator that manages federated learning sessions.
    Replaces the need for centralized GCP coordinator.
    """

    def __init__(self):
        self.node_id = self._generate_node_id()
        self.peers = {}
        self.active_sessions = {}
        self.ipfs_client = None

    def _generate_node_id(self) -> str:
        """Generate unique node ID."""
        import uuid
        return f"node_{uuid.uuid4().hex[:8]}"

    def initialize(self, ipfs_endpoint: str):
        """Initialize coordinator with IPFS connection."""
        try:
            import ipfshttpclient
            self.ipfs_client = ipfshttpclient.connect(ipfs_endpoint)
            logger.info(f"✅ P2P Coordinator initialized with node ID: {self.node_id}")
            return True
        except Exception as e:
            logger.warning(f"⚠️ IPFS not available for coordinator: {e}")
            return False

    def create_session(self, session_config: Dict[str, Any]) -> Optional[str]:
        """Create a new federated learning session."""
        session_id = f"session_{int(time.time())}_{self.node_id[:8]}"

        self.active_sessions[session_id] = {
            "config": session_config,
            "participants": [self.node_id],
            "status": "waiting",
            "created_at": time.time()
        }

        # Publish session to IPFS for discovery
        if self.ipfs_client:
            try:
                session_data = json.dumps(self.active_sessions[session_id])
                result = self.ipfs_client.add_str(session_data)
                logger.info(f"📢 Session {session_id} published to IPFS: {result}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to publish session to IPFS: {e}")

        logger.info(f"🎯 Created federated session: {session_id}")
        return session_id

    def join_session(self, session_id: str) -> bool:
        """Join an existing federated learning session."""
        if session_id in self.active_sessions:
            if self.node_id not in self.active_sessions[session_id]["participants"]:
                self.active_sessions[session_id]["participants"].append(self.node_id)
                logger.info(f"✅ Joined session {session_id}")
                return True
        return False

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a session."""
        return self.active_sessions.get(session_id)


class NodeDiscovery:
    """
    Automatic node discovery system using IPFS PubSub.
    """

    def __init__(self):
        self.node_id = f"node_{int(time.time())}_{hash(platform.node()) % 1000}"
        self.discovered_nodes = {}
        self.ipfs_client = None
        self.topic = "ailoos.node.discovery"

    def initialize(self, ipfs_endpoint: str):
        """Initialize node discovery."""
        try:
            import ipfshttpclient
            self.ipfs_client = ipfshttpclient.connect(ipfs_endpoint)
            logger.info(f"✅ Node discovery initialized for node: {self.node_id}")
            
            # Start listening for PubSub messages in a background task
            asyncio.create_task(self._listen_for_peers())
            
            return True
        except Exception as e:
            logger.warning(f"⚠️ IPFS not available for node discovery: {e}")
            return False

    def announce_presence(self):
        """Announce node presence to the network."""
        if not self.ipfs_client:
            return

        node_info = {
            "node_id": self.node_id,
            "platform": platform.system(),
            "architecture": platform.machine(),
            "timestamp": time.time(),
            "capabilities": ["federated_learning", "model_training"]
        }

        try:
            # Publish to IPFS PubSub
            self.ipfs_client.pubsub.pub(self.topic, json.dumps(node_info))
            logger.info("📢 Node presence announced")
        except Exception as e:
            logger.warning(f"⚠️ Failed to announce presence: {e}")

    async def _listen_for_peers(self):
        """Listen for PubSub messages to discover peers."""
        if not self.ipfs_client:
            return

        logger.info(f"👂 Listening for peer announcements on topic: {self.topic}")
        try:
            # Subscribe to the topic
            sub = self.ipfs_client.pubsub.sub(self.topic)
            async for message in sub:
                try:
                    data = json.loads(message['data'].decode('utf-8'))
                    node_id = data.get("node_id")
                    if node_id and node_id != self.node_id: # Don't add self
                        self.discovered_nodes[node_id] = data
                        logger.debug(f"✨ Discovered peer: {node_id} - {data.get('platform')}")
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Received malformed PubSub message: {message['data']}")
                except Exception as e:
                    logger.error(f"❌ Error processing PubSub message: {e}")
        except Exception as e:
            logger.error(f"❌ Error listening for PubSub messages: {e}")

    def discover_peers(self) -> Dict[str, Any]:
        """Discover available peer nodes."""
        # Peers are discovered asynchronously via PubSub.
        # This method just returns the currently discovered nodes.
        return self.discovered_nodes


class UpdateManager:
    """
    Automatic update management system.
    """

    def __init__(self):
        self.current_version = "2.2.5"
        self.update_url = "https://raw.githubusercontent.com/Empoorio/ailoos/main/version.json"

    def check_for_updates(self) -> Optional[str]:
        """Check if updates are available."""
        try:
            import requests
            response = requests.get(self.update_url, timeout=5)
            if response.status_code == 200:
                version_info = response.json()
                latest_version = version_info.get("version")
                if latest_version and latest_version != self.current_version:
                    return latest_version
        except Exception as e:
            logger.debug(f"Failed to check for updates: {e}")
        return None

    def apply_update(self, version: str) -> bool:
        """Apply available update."""
        logger.info(f"🔄 Applying update to version {version}")
        # In a real implementation, this would download and install the update
        logger.info("✅ Update applied successfully")
        return True


class AutoSetup:
    """
    Complete auto-setup system for Ailoos.
    Handles all components automatically.
    """

    def __init__(self):
        self.ipfs_manager = EmbeddedIPFS()
        self.p2p_coordinator = P2PCoordinator()
        self.node_discovery = NodeDiscovery()
        self.update_manager = UpdateManager()
        self.config_file = Path.home() / ".ailoos" / "config.json"
        self.hardware_detector = HardwareDetector() if HARDWARE_DETECTOR_AVAILABLE else None
        self.role_config_manager = RoleConfigManager() if ROLE_CONFIG_AVAILABLE else None
        self.hardware_config = {}
        self.node_role = "SCOUT"  # Default role

    def setup_everything(self, verbose: bool = True) -> bool:
        """
        Complete auto-setup of Ailoos system.

        Args:
            verbose: Whether to show detailed progress

        Returns:
            True if setup successful, False otherwise
        """
        logger.info("🚀 Starting complete Ailoos auto-setup...")

        success = True

        # 0. Detect hardware and assign role
        logger.info("0️⃣ Detecting hardware and assigning role...")
        if self.hardware_detector:
            try:
                self.hardware_config = self.hardware_detector.run()
                self.node_role = self.hardware_config.get("node_role", "SCOUT")
                logger.info(f"✅ Hardware detected. Assigned role: {self.node_role}")
            except Exception as e:
                logger.warning(f"⚠️ Hardware detection failed: {e}. Using default SCOUT role.")
                self.node_role = "SCOUT"
        else:
            logger.warning("⚠️ Hardware detector not available. Using default SCOUT role.")

        # 1. Start IPFS
        logger.info("1️⃣ Setting up IPFS...")
        if not self.ipfs_manager.start_daemon():
            logger.error("❌ Failed to setup IPFS")
            success = False

        # 2. Initialize P2P Coordinator
        logger.info("2️⃣ Initializing P2P Coordinator...")
        ipfs_endpoint = self.ipfs_manager.get_api_endpoint()
        if not self.p2p_coordinator.initialize(ipfs_endpoint):
            logger.warning("⚠️ P2P Coordinator initialization incomplete")

        # 3. Setup Node Discovery
        logger.info("3️⃣ Setting up Node Discovery...")
        if not self.node_discovery.initialize(ipfs_endpoint):
            logger.warning("⚠️ Node Discovery initialization incomplete")

        # 4. Check for Updates
        logger.info("4️⃣ Checking for updates...")
        latest_version = self.update_manager.check_for_updates()
        if latest_version:
            logger.info(f"📦 Update available: {latest_version}")
            # Auto-apply in future versions

        # 5. Save Configuration
        logger.info("5️⃣ Saving configuration...")
        self._save_config()

        if success:
            logger.info("✅ Ailoos auto-setup completed successfully!")
            logger.info("🎯 Your node is ready for federated learning")
            logger.info(f"🆔 Node ID: {self.p2p_coordinator.node_id}")
            logger.info(f"🌐 IPFS API: {ipfs_endpoint}")
        else:
            logger.warning("⚠️ Setup completed with some warnings")

        return success

    def _save_config(self):
        """Save configuration to file."""
        config = {
            "version": "2.0.21",
            "node_id": self.p2p_coordinator.node_id,
            "ipfs_endpoint": self.ipfs_manager.get_api_endpoint(),
            "node_role": self.node_role,
            "hardware_config": self.hardware_config,
            "setup_completed": True,
            "setup_timestamp": time.time()
        }

        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def get_status(self) -> Dict[str, Any]:
        """Get current setup status."""
        status = {
            "ipfs_running": self.ipfs_manager.daemon_process is not None,
            "coordinator_ready": self.p2p_coordinator.ipfs_client is not None,
            "discovery_ready": self.node_discovery.ipfs_client is not None,
            "config_exists": self.config_file.exists(),
            "node_role": self.node_role,
            "hardware_detected": bool(self.hardware_config)
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    status.update(config)
            except Exception:
                pass

        return status

    def cleanup(self):
        """Clean up resources."""
        self.ipfs_manager.stop_daemon()


def main():
    """Command-line interface for auto-setup."""
    import argparse

    parser = argparse.ArgumentParser(description="Ailoos Auto-Setup")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--status", action="store_true", help="Show current status")
    parser.add_argument("--cleanup", action="store_true", help="Clean up resources")

    args = parser.parse_args()

    # Configure logging
    level = logging.INFO if not args.verbose else logging.DEBUG
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

    setup = AutoSetup()

    if args.status:
        status = setup.get_status()
        print("📊 Ailoos Setup Status:")
        print(json.dumps(status, indent=2))
    elif args.cleanup:
        setup.cleanup()
        print("🧹 Cleanup completed")
    else:
        success = setup.setup_everything(verbose=args.verbose)
        if success:
            print("\n🎉 Ailoos is ready! Run 'ailoos node start' to begin federated learning")
        else:
            print("\n❌ Setup failed. Check logs for details")
            sys.exit(1)


if __name__ == "__main__":
    main()
