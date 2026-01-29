"""
Node management for decentralized AI training.
Handles node registration, heartbeat, and communication with the network.
"""

import asyncio
import json
import logging
import platform
import psutil
import socket
import time
from datetime import datetime
from typing import Dict, Optional, Any
import aiohttp

logger = logging.getLogger(__name__)


class Node:
    """
    Represents a training node in the Ailoos decentralized network.

    This class handles:
    - Node registration with the network
    - Heartbeat monitoring
    - Hardware detection and reporting
    - Training session management
    - Communication with coordinator nodes

    Example:
        node = Node(node_id="my_training_node")
        await node.start()
        await node.join_training_session("session_123")
    """

    def __init__(
        self,
        node_id: str,
        coordinator_url: str = "http://localhost:8000",
        heartbeat_interval: int = 30,
        hardware_info: Optional[Dict[str, Any]] = None,
        data_dir: str = "./data",
        models_dir: str = "./models",
        logger: Optional[Any] = None
    ):
        """
        Initialize a training node.

        Args:
            node_id: Unique identifier for this node
            coordinator_url: URL of the coordinator API server
            heartbeat_interval: Seconds between heartbeat messages
            hardware_info: Optional hardware information override
            data_dir: Directory for data storage
            models_dir: Directory for model storage
            logger: Optional logger instance
        """
        self.node_id = node_id
        self.coordinator_url = coordinator_url
        self.heartbeat_interval = heartbeat_interval
        self.hardware_info = hardware_info or self._detect_hardware()
        self.data_dir = data_dir
        self.models_dir = models_dir
        self.logger = logger or logging.getLogger(__name__)
        self.is_running = False
        self.session = None
        self._heartbeat_task: Optional[asyncio.Task] = None

    def _detect_hardware(self) -> Dict[str, Any]:
        """Automatically detect hardware capabilities."""
        try:
            # CPU info
            cpu_count = psutil.cpu_count(logical=True)
            cpu_physical = psutil.cpu_count(logical=False)

            # Memory info
            memory = psutil.virtual_memory()
            memory_gb = round(memory.total / (1024**3), 1)

            # GPU detection (simplified - would need torch/cuda detection in real impl)
            gpu_info = "Unknown"
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_info = torch.cuda.get_device_name(0)
                else:
                    gpu_info = "CPU Only"
            except ImportError:
                gpu_info = "PyTorch not available"

            return {
                "cpu_cores": cpu_count,
                "cpu_physical": cpu_physical,
                "memory_gb": memory_gb,
                "gpu": gpu_info,
                "platform": platform.system(),
                "architecture": platform.machine()
            }
        except Exception as e:
            logger.warning(f"Hardware detection failed: {e}")
            return {"error": "Hardware detection failed"}

    async def start(self) -> bool:
        """
        Start the node and register with the network.

        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Save node_id to file for detection
            import os
            from pathlib import Path
            node_id_file = Path.home() / '.ailoos' / 'node_id'
            node_id_file.parent.mkdir(parents=True, exist_ok=True)
            with open(node_id_file, 'w') as f:
                f.write(self.node_id)

            # Register with coordinator
            async with aiohttp.ClientSession() as session:
                payload = {
                    "node_id": self.node_id,
                    "ip_address": self._get_local_ip(),
                    "hardware_specs": self.hardware_info,
                    "location": "Unknown"  # Could be detected via IP geolocation
                }

                async with session.post(
                    f"{self.coordinator_url}/api/nodes/register",
                    json=payload
                ) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        logger.info(f"Node {self.node_id} registered successfully")
                        self.is_running = True

                        # Note: Simple coordinator doesn't have heartbeat endpoint
                        # Heartbeat functionality disabled for now
                        # self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                        return True
                    else:
                        error = await response.text()
                        logger.error(f"Registration failed: {error}")
                        return False

        except Exception as e:
            logger.error(f"Failed to start node: {e}")
            return False

    async def stop(self):
        """Stop the node and cleanup resources."""
        self.is_running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        logger.info(f"Node {self.node_id} stopped")

    async def _heartbeat_loop(self):
        """Send periodic heartbeat to coordinator."""
        while self.is_running:
            try:
                # Collect current metrics
                metrics = self._collect_metrics()

                # Determine current status
                status = "training" if self.session else "idle"

                payload = {
                    "node_id": self.node_id,
                    "status": status,
                    "last_update": datetime.now().isoformat()
                }

                # Only include optional fields if they have values
                if self.session is not None:
                    payload["current_session"] = self.session
                if metrics:
                    payload["metrics"] = metrics

                logger.debug(f"Heartbeat payload: {json.dumps(payload, indent=2)}")

                async with aiohttp.ClientSession() as session:
                async with session.put(
                    f"{self.coordinator_url}/api/nodes/{self.node_id}/heartbeat",
                    json=payload
                ) as response:
                        if response.status != 200:
                            response_text = await response.text()
                            logger.warning(f"Heartbeat failed: {response.status} - {response_text}")
                            logger.debug(f"Coordinator URL: {self.coordinator_url}")
                        else:
                            logger.debug("Heartbeat successful")
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

            await asyncio.sleep(self.heartbeat_interval)

    async def join_training_session(self, session_id: str) -> bool:
        """
        Join a federated training session.

        Args:
            session_id: ID of the training session to join

        Returns:
            True if joined successfully
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "node_id": self.node_id,
                    "session_id": session_id,
                    "model_version": "1.0.0"
                }

                async with session.post(
                    f"{self.coordinator_url}/sessions/{session_id}/join",
                    json={"node_id": self.node_id, "node_info": payload}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.session = session_id
                        logger.info(f"Joined training session {session_id}")
                        return True
                    else:
                        error = await response.text()
                        logger.error(f"Failed to join session: {error}")
                        return False

        except Exception as e:
            logger.error(f"Error joining session: {e}")
            return False

    async def update_training_progress(
        self,
        parameters_trained: int,
        accuracy: float,
        loss: float,
        status: str = "running"
    ):
        """
        Update training progress for current session.

        Args:
            parameters_trained: Number of parameters trained
            accuracy: Current accuracy
            loss: Current loss
            status: Training status
        """
        if not self.session:
            logger.warning("No active training session")
            return

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "session_id": self.session,
                    "parameters_trained": parameters_trained,
                    "accuracy": accuracy,
                    "loss": loss,
                    "status": status
                }

                async with session.post(
                    f"{self.coordinator_url}/api/training/update",
                    json=payload
                ) as response:
                    if response.status == 200:
                        logger.debug(f"Progress updated for session {self.session}")
                    else:
                        logger.warning(f"Progress update failed: {response.status}")

        except Exception as e:
            logger.error(f"Error updating progress: {e}")

    def _collect_metrics(self) -> Dict[str, Any]:
        """Collect current node metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent

            # Network I/O (simplified)
            net_io = psutil.net_io_counters()
            bytes_sent = net_io.bytes_sent
            bytes_recv = net_io.bytes_recv

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
                "network_sent_mb": round(bytes_sent / (1024**2), 2),
                "network_recv_mb": round(bytes_recv / (1024**2), 2),
                "uptime_seconds": time.time() - psutil.boot_time(),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"Failed to collect metrics: {e}")
            return {"error": "Metrics collection failed"}

    def _get_local_ip(self) -> str:
        """Get local IP address."""
        try:
            # Create a socket to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    async def get_network_stats(self) -> Optional[Dict[str, Any]]:
        """Get current network statistics."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.coordinator_url}/api/stats") as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            logger.error(f"Error getting network stats: {e}")
        return None

    @property
    def status(self) -> Dict[str, Any]:
        """Get current node status."""
        return {
            "node_id": self.node_id,
            "is_running": self.is_running,
            "session": self.session,
            "hardware": self.hardware_info,
            "coordinator": self.coordinator_url,
            "last_update": datetime.now().isoformat()
        }
