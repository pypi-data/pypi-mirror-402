"""
Node Discovery System for Ailoos P2P Network.
Automatically discovers and connects federated learning nodes with dynamic capabilities.
Integrates distributed registry, session matching, and health monitoring for scalable federated architecture.
"""

import asyncio
import json
import time
import hashlib
import platform
import psutil
from typing import Dict, Any, List, Optional, Set, Tuple, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
import logging
import os

from .node_registry import NodeRegistry, NodeRegistration
from enum import Enum
from .session_matcher import SessionMatcher, MatchingResult, get_session_matcher
from .health_monitor import HealthMonitor, HealthStatus, get_health_monitor
from ..federated.session import FederatedSession
from ..consensus.distributed_consensus import DistributedConsensusManager
from ..database.distributed_queries import DistributedQueryEngine
from ..infrastructure.ipfs_embedded import IPFSManager

logger = logging.getLogger(__name__)


class NodeStatus(Enum):
    """Estados posibles de un nodo."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


@dataclass
class DiscoveredNode:
    """Information about a discovered node with dynamic capabilities."""
    node_id: str
    ip_address: Optional[str]
    platform: str
    architecture: str
    capabilities: List[str]
    hardware_specs: Dict[str, Any]
    location: Optional[str]
    last_seen: float
    status: str = "online"
    registry_entry: Optional[NodeRegistration] = None
    health_status: HealthStatus = HealthStatus.UNKNOWN
    session_count: int = 0
    load_factor: float = 0.0
    reputation_score: float = 0.5
    dynamic_capabilities: Dict[str, Any] = field(default_factory=dict)


class NodeDiscovery:
    """
    Dynamic node discovery system with distributed registry integration.
    Enables scalable federated learning through intelligent node matching,
    health monitoring, and session management.
    """

    def __init__(self, node_id: Optional[str] = None,
                 consensus_manager: Optional[DistributedConsensusManager] = None,
                 query_engine: Optional[DistributedQueryEngine] = None):
        self.node_id = node_id or self._generate_node_id()
        self.discovered_nodes: Dict[str, DiscoveredNode] = {}
        self.ipfs_client = None
        self.discovery_topic = "ailoos.node.discovery"
        self.heartbeat_topic = "ailoos.node.heartbeat"
        self.capability_topic = "ailoos.node.capabilities"
        self.session_topic = "ailoos.node.sessions"
        self.is_running = False
        self.heartbeat_interval = 30  # seconds
        self.node_timeout = 120  # seconds (2 minutes)
        self.capability_update_interval = 300  # 5 minutes

        # Integrated components
        self.node_registry: Optional[NodeRegistry] = None
        self.session_matcher: Optional[SessionMatcher] = None
        self.health_monitor: Optional[HealthMonitor] = None

        # Dynamic scaling
        self.auto_scaling_enabled = True
        self.target_node_count = 10
        self.scaling_threshold = 0.8

        # Metrics and telemetry
        self.discovery_metrics: Dict[str, Any] = {
            'nodes_discovered': 0,
            'sessions_matched': 0,
            'health_checks': 0,
            'capability_updates': 0,
            'last_scaling_event': None
        }

        # Initialize integrated components if managers provided
        if consensus_manager and query_engine:
            self._initialize_integrated_components(consensus_manager, query_engine)

    def _generate_node_id(self) -> str:
        """Generate unique node ID based on hardware."""
        machine_id = platform.node() + platform.machine()
        return f"node_{hashlib.sha256(machine_id.encode()).hexdigest()[:16]}"

    def _initialize_integrated_components(self, consensus_manager: DistributedConsensusManager,
                                        query_engine: DistributedQueryEngine):
        """Initialize integrated registry, matcher, and monitor components."""
        try:
            # Initialize node registry
            # Note: NodeRegistry requires IPFS manager, using None for now
            self.node_registry = NodeRegistry(self.node_id, None)  # IPFS manager would be passed here

            # Initialize session matcher
            self.session_matcher = get_session_matcher(self.node_registry)

            # Initialize health monitor
            self.health_monitor = get_health_monitor(self.node_registry, self)

            logger.info("✅ Integrated components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize integrated components: {e}")

    def _get_hardware_info(self) -> Dict[str, Any]:
        """Get local hardware information with dynamic capabilities."""
        try:
            base_info = {
                "cpu_count": psutil.cpu_count(),
                "cpu_freq": psutil.cpu_freq().max if psutil.cpu_freq() else None,
                "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
                "disk_gb": round(psutil.disk_usage('/').total / (1024**3), 1),
                "platform": platform.system(),
                "architecture": platform.machine()
            }

            # Add dynamic capabilities based on current system state
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent

            base_info.update({
                "current_cpu_usage": cpu_percent,
                "current_memory_usage": memory_percent,
                "available_memory_gb": round(psutil.virtual_memory().available / (1024**3), 1),
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
                "gpu_available": self._check_gpu_availability(),
                "network_interfaces": len(psutil.net_if_addrs())
            })

            return base_info
        except Exception as e:
            logger.warning(f"Failed to get hardware info: {e}")
            return {
                "cpu_count": 1,
                "memory_gb": 4,
                "platform": platform.system(),
                "architecture": platform.machine(),
                "current_cpu_usage": 0.0,
                "current_memory_usage": 0.0
            }

    def _check_gpu_availability(self) -> bool:
        """Check if GPU is available for computation."""
        try:
            # Simple GPU detection - in production would use more sophisticated methods
            import subprocess
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

    def initialize(self, ipfs_client=None):
        """
        Initialize node discovery.

        Args:
            ipfs_client: IPFS client instance
        """
        self.ipfs_client = ipfs_client
        logger.info(f"🔍 Node discovery initialized: {self.node_id}")

    async def start_discovery(self):
        """Start the dynamic node discovery process with integrated components."""
        if self.is_running:
            logger.warning("⚠️ Node discovery already running")
            return

        self.is_running = True
        logger.info("🚀 Starting dynamic node discovery...")

        # Start integrated components
        if self.node_registry:
            await self.node_registry.start_registry()
        if self.health_monitor:
            await self.health_monitor.start_monitoring()

        # Announce presence with enhanced capabilities
        await self._announce_presence()

        # Start background tasks
        asyncio.create_task(self._heartbeat_loop())
        asyncio.create_task(self._listen_for_discovery())
        asyncio.create_task(self._cleanup_stale_nodes())
        asyncio.create_task(self._capability_update_loop())
        asyncio.create_task(self._auto_scaling_loop())
        asyncio.create_task(self._session_matching_loop())
        asyncio.create_task(self._health_sync_loop())

    async def stop_discovery(self):
        """Stop the node discovery process."""
        self.is_running = False
        logger.info("🛑 Node discovery stopped")

    async def _announce_presence(self):
        """Announce node presence with dynamic capabilities to the network."""
        if not self.ipfs_client:
            return

        # Get current dynamic capabilities
        current_hardware = self._get_hardware_info()
        dynamic_caps = await self._get_dynamic_capabilities()

        node_info = {
            "node_id": self.node_id,
            "platform": platform.system(),
            "architecture": platform.machine(),
            "capabilities": ["federated_learning", "model_training", "inference"],
            "hardware_specs": current_hardware,
            "dynamic_capabilities": dynamic_caps,
            "location": self._get_location(),
            "health_status": self._get_current_health_status(),
            "load_factor": self._calculate_load_factor(),
            "reputation_score": self._get_reputation_score(),
            "registry_synced": self.node_registry is not None,
            "timestamp": time.time(),
            "type": "node_announcement"
        }

        try:
            await self.ipfs_client.publish_message(self.discovery_topic, json.dumps(node_info))
            logger.debug("📢 Dynamic node presence announced")
        except Exception as e:
            logger.warning(f"⚠️ Failed to announce presence: {e}")

    async def _get_dynamic_capabilities(self) -> Dict[str, Any]:
        """Get current dynamic capabilities based on system state."""
        try:
            caps = {
                "available_memory_percent": 100 - psutil.virtual_memory().percent,
                "available_cpu_percent": 100 - psutil.cpu_percent(),
                "network_bandwidth": self._estimate_network_bandwidth(),
                "current_sessions": len(await self._get_active_sessions()) if self.node_registry else 0,
                "last_updated": time.time()
            }
            return caps
        except Exception as e:
            logger.debug(f"Failed to get dynamic capabilities: {e}")
            return {}

    def _get_current_health_status(self) -> str:
        """Get current health status from monitor."""
        if self.health_monitor:
            health = self.health_monitor.get_node_health(self.node_id)
            return health.overall_health.value if health else "unknown"
        return "unknown"

    def _calculate_load_factor(self) -> float:
        """Calculate current load factor (0-1)."""
        try:
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            return min((cpu_percent + memory_percent) / 200.0, 1.0)
        except:
            return 0.0

    def _get_reputation_score(self) -> float:
        """Get current reputation score."""
        if self.health_monitor:
            health = self.health_monitor.get_node_health(self.node_id)
            return health.contribution_score if health else 0.5
        return 0.5

    async def _get_active_sessions(self) -> List[Any]:
        """Get active sessions for this node."""
        if self.node_registry:
            # This would need to be implemented in NodeRegistry
            return []
        return []

    async def _heartbeat_loop(self):
        """Send periodic heartbeats to maintain presence."""
        while self.is_running:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.warning(f"⚠️ Heartbeat failed: {e}")
                await asyncio.sleep(5)

    async def _send_heartbeat(self):
        """Send heartbeat message."""
        if not self.ipfs_client:
            return

        heartbeat = {
            "node_id": self.node_id,
            "timestamp": time.time(),
            "type": "heartbeat"
        }

        try:
            await self.ipfs_client.publish_message(self.heartbeat_topic, json.dumps(heartbeat))
        except Exception as e:
            logger.debug(f"Failed to send heartbeat: {e}")

    async def _listen_for_discovery(self):
        """Listen for node discovery messages with enhanced processing."""
        if not self.ipfs_client:
            return

        while self.is_running:
            try:
                # Subscribe to discovery topic
                messages = await self.ipfs_client.subscribe_topic(self.discovery_topic)
                if messages:
                    for msg in messages:
                        await self._process_discovery_message(msg)

                # Subscribe to heartbeat topic
                heartbeats = await self.ipfs_client.subscribe_topic(self.heartbeat_topic)
                if heartbeats:
                    for msg in heartbeats:
                        await self._process_heartbeat_message(msg)

                # Subscribe to capability updates
                capabilities = await self.ipfs_client.subscribe_topic(self.capability_topic)
                if capabilities:
                    for msg in capabilities:
                        await self._process_capability_message(msg)

                # Subscribe to session updates
                sessions = await self.ipfs_client.subscribe_topic(self.session_topic)
                if sessions:
                    for msg in sessions:
                        await self._process_session_message(msg)

                await asyncio.sleep(1)

            except Exception as e:
                logger.warning(f"⚠️ Discovery listening failed: {e}")
                await asyncio.sleep(5)

    async def _process_discovery_message(self, message: Dict[str, Any]):
        """Process incoming discovery message with registry integration."""
        try:
            if message.get("type") == "node_announcement":
                node_id = message.get("node_id")
                if node_id and node_id != self.node_id:
                    # Get registry entry if available
                    registry_entry = None
                    if self.node_registry:
                        registry_entry = await self.node_registry.get_node(node_id)

                    # Update or add node with enhanced information
                    if node_id in self.discovered_nodes:
                        # Update existing node
                        existing = self.discovered_nodes[node_id]
                        existing.last_seen = time.time()
                        existing.status = "online"
                        existing.health_status = HealthStatus(message.get("health_status", "unknown"))
                        existing.load_factor = message.get("load_factor", 0.0)
                        existing.reputation_score = message.get("reputation_score", 0.5)
                        existing.dynamic_capabilities = message.get("dynamic_capabilities", {})
                        existing.registry_entry = registry_entry
                    else:
                        # Add new node with full dynamic information
                        node = DiscoveredNode(
                            node_id=node_id,
                            ip_address=message.get("ip_address"),
                            platform=message.get("platform", "unknown"),
                            architecture=message.get("architecture", "unknown"),
                            capabilities=message.get("capabilities", []),
                            hardware_specs=message.get("hardware_specs", {}),
                            location=message.get("location"),
                            last_seen=time.time(),
                            registry_entry=registry_entry,
                            health_status=HealthStatus(message.get("health_status", "unknown")),
                            load_factor=message.get("load_factor", 0.0),
                            reputation_score=message.get("reputation_score", 0.5),
                            dynamic_capabilities=message.get("dynamic_capabilities", {})
                        )
                        self.discovered_nodes[node_id] = node
                        self.discovery_metrics['nodes_discovered'] += 1
                        logger.info(f"🔍 Discovered new dynamic node: {node_id}")

                    # Sync with registry if available
                    if self.node_registry and not registry_entry:
                        await self._sync_node_to_registry(node_id, message)

        except Exception as e:
            logger.debug(f"Failed to process discovery message: {e}")

    async def _sync_node_to_registry(self, node_id: str, message: Dict[str, Any]):
        """Sync discovered node to registry."""
        if not self.node_registry:
            return

        try:
            node_info = {
                'node_id': node_id,
                'node_type': 'worker',  # Default type
                'capabilities': message.get('capabilities', {}),
                'hardware_specs': message.get('hardware_specs', {}),
                'network_info': {},
                'location': message.get('location'),
                'metadata': {
                    'discovered_at': time.time(),
                    'dynamic_capabilities': message.get('dynamic_capabilities', {})
                }
            }

            await self.node_registry.register_node(node_info)
            logger.debug(f"📝 Synced node {node_id} to registry")
        except Exception as e:
            logger.debug(f"Failed to sync node {node_id} to registry: {e}")

    async def _process_heartbeat_message(self, message: Dict[str, Any]):
        """Process incoming heartbeat message with health updates."""
        try:
            if message.get("type") == "heartbeat":
                node_id = message.get("node_id")
                if node_id and node_id in self.discovered_nodes:
                    self.discovered_nodes[node_id].last_seen = time.time()
                    self.discovered_nodes[node_id].status = "online"

                    # Update health monitor if available
                    if self.health_monitor:
                        await self.health_monitor.report_node_contribution(
                            node_id, True, message.get("contribution_time")
                        )

        except Exception as e:
            logger.debug(f"Failed to process heartbeat: {e}")

    async def _process_capability_message(self, message: Dict[str, Any]):
        """Process capability update messages."""
        try:
            if message.get("type") == "capability_update":
                node_id = message.get("node_id")
                if node_id and node_id in self.discovered_nodes:
                    # Update dynamic capabilities
                    self.discovered_nodes[node_id].dynamic_capabilities = message.get("capabilities", {})
                    self.discovered_nodes[node_id].load_factor = message.get("load_factor", 0.0)
                    self.discovery_metrics['capability_updates'] += 1

                    logger.debug(f"📊 Updated capabilities for node {node_id}")

        except Exception as e:
            logger.debug(f"Failed to process capability message: {e}")

    async def _process_session_message(self, message: Dict[str, Any]):
        """Process session-related messages."""
        try:
            msg_type = message.get("type")
            if msg_type == "session_started":
                node_id = message.get("node_id")
                if node_id and node_id in self.discovered_nodes:
                    self.discovered_nodes[node_id].session_count += 1
                    self.discovery_metrics['sessions_matched'] += 1

            elif msg_type == "session_ended":
                node_id = message.get("node_id")
                if node_id and node_id in self.discovered_nodes:
                    self.discovered_nodes[node_id].session_count = max(0, self.discovered_nodes[node_id].session_count - 1)

        except Exception as e:
            logger.debug(f"Failed to process session message: {e}")

    async def _cleanup_stale_nodes(self):
        """Remove nodes that haven't been seen recently with registry sync."""
        while self.is_running:
            try:
                current_time = time.time()
                stale_nodes = []

                for node_id, node in self.discovered_nodes.items():
                    if current_time - node.last_seen > self.node_timeout:
                        stale_nodes.append(node_id)

                for node_id in stale_nodes:
                    node = self.discovered_nodes[node_id]
                    node.status = "offline"
                    node.health_status = HealthStatus.CRITICAL

                    # Update registry status
                    if self.node_registry:
                        await self.node_registry.update_node_status(node_id, NodeStatus.INACTIVE)

                    logger.debug(f"📴 Node marked offline: {node_id}")

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.warning(f"⚠️ Cleanup failed: {e}")
                await asyncio.sleep(30)

    async def _capability_update_loop(self):
        """Periodically update and broadcast dynamic capabilities."""
        while self.is_running:
            try:
                if self.ipfs_client:
                    capabilities = await self._get_dynamic_capabilities()
                    update_msg = {
                        "node_id": self.node_id,
                        "capabilities": capabilities,
                        "load_factor": self._calculate_load_factor(),
                        "timestamp": time.time(),
                        "type": "capability_update"
                    }

                    await self.ipfs_client.publish_message(self.capability_topic, json.dumps(update_msg))
                    self.discovery_metrics['capability_updates'] += 1

                await asyncio.sleep(self.capability_update_interval)

            except Exception as e:
                logger.warning(f"⚠️ Capability update failed: {e}")
                await asyncio.sleep(30)

    async def _auto_scaling_loop(self):
        """Monitor and trigger auto-scaling based on demand."""
        while self.is_running:
            try:
                await self._check_auto_scaling()
                await asyncio.sleep(120)  # Check every 2 minutes

            except Exception as e:
                logger.warning(f"⚠️ Auto-scaling check failed: {e}")
                await asyncio.sleep(60)

    async def _check_auto_scaling(self):
        """Check if auto-scaling is needed."""
        if not self.auto_scaling_enabled:
            return

        current_nodes = len(self.get_online_nodes())
        utilization = self._calculate_system_utilization()

        if utilization > self.scaling_threshold and current_nodes < self.target_node_count:
            await self._trigger_scale_up()
        elif utilization < 0.3 and current_nodes > 5:  # Minimum nodes
            await self._trigger_scale_down()

    def _calculate_system_utilization(self) -> float:
        """Calculate overall system utilization."""
        online_nodes = self.get_online_nodes()
        if not online_nodes:
            return 0.0

        total_load = sum(node.load_factor for node in online_nodes)
        return total_load / len(online_nodes)

    async def _trigger_scale_up(self):
        """Trigger scale up by requesting more nodes."""
        logger.info("📈 Triggering scale up - requesting additional nodes")
        self.discovery_metrics['last_scaling_event'] = time.time()

        # In a real implementation, this would send requests to node provisioners
        # For now, just log and update metrics
        scale_msg = {
            "type": "scale_request",
            "action": "scale_up",
            "current_nodes": len(self.get_online_nodes()),
            "target_nodes": self.target_node_count,
            "timestamp": time.time()
        }

        if self.ipfs_client:
            await self.ipfs_client.publish_message("ailoos.scaling", json.dumps(scale_msg))

    async def _trigger_scale_down(self):
        """Trigger scale down by releasing idle nodes."""
        logger.info("📉 Triggering scale down - releasing idle nodes")
        self.discovery_metrics['last_scaling_event'] = time.time()

        # Identify idle nodes to release
        idle_nodes = [node for node in self.get_online_nodes()
                     if node.load_factor < 0.2 and node.session_count == 0]

        scale_msg = {
            "type": "scale_request",
            "action": "scale_down",
            "idle_nodes": [node.node_id for node in idle_nodes],
            "timestamp": time.time()
        }

        if self.ipfs_client:
            await self.ipfs_client.publish_message("ailoos.scaling", json.dumps(scale_msg))

    async def _session_matching_loop(self):
        """Continuously match available sessions with nodes."""
        while self.is_running:
            try:
                await self._perform_session_matching()
                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.warning(f"⚠️ Session matching failed: {e}")
                await asyncio.sleep(15)

    async def _perform_session_matching(self):
        """Perform intelligent session matching."""
        if not self.session_matcher:
            return

        # Get pending sessions (this would need to be implemented)
        # For now, this is a placeholder for the matching logic
        pass

    async def _health_sync_loop(self):
        """Synchronize health status across components."""
        while self.is_running:
            try:
                await self._sync_health_status()
                await asyncio.sleep(60)  # Sync every minute

            except Exception as e:
                logger.warning(f"⚠️ Health sync failed: {e}")
                await asyncio.sleep(30)

    async def _sync_health_status(self):
        """Sync health status between discovery and monitor."""
        if not self.health_monitor:
            return

        # Update discovery nodes with latest health info
        for node_id, discovered_node in self.discovered_nodes.items():
            health = self.health_monitor.get_node_health(node_id)
            if health:
                discovered_node.health_status = health.overall_health
                discovered_node.reputation_score = health.contribution_score

    def _get_location(self) -> Optional[str]:
        """Get approximate location (simplified)."""
        try:
            # In a real implementation, this could use IP geolocation
            return "Madrid, Spain"  # Placeholder
        except Exception:
            return None

    def get_discovered_nodes(self, capability_filter: Optional[str] = None) -> List[DiscoveredNode]:
        """
        Get list of discovered nodes.

        Args:
            capability_filter: Filter by specific capability

        Returns:
            List of discovered nodes
        """
        nodes = list(self.discovered_nodes.values())

        if capability_filter:
            nodes = [n for n in nodes if capability_filter in n.capabilities]

        return nodes

    def get_online_nodes(self, capability_filter: Optional[str] = None) -> List[DiscoveredNode]:
        """
        Get list of online nodes.

        Args:
            capability_filter: Filter by specific capability

        Returns:
            List of online nodes
        """
        nodes = [n for n in self.discovered_nodes.values() if n.status == "online"]

        if capability_filter:
            nodes = [n for n in nodes if capability_filter in n.capabilities]

        return nodes

    async def find_nodes_for_federated_learning_async(self, min_nodes: int = 2,
                                                     session_requirements: Optional[Dict[str, Any]] = None) -> List[DiscoveredNode]:
        """
        Find nodes suitable for federated learning using intelligent matching (async version).

        Args:
            min_nodes: Minimum number of nodes required
            session_requirements: Specific requirements for the session

        Returns:
            List of suitable nodes
        """
        # Use session matcher if available for intelligent matching
        if self.session_matcher and session_requirements:
            # Create a mock session for matching
            mock_session = type('MockSession', (), {
                'session_id': f'match_{int(time.time())}',
                'min_nodes': min_nodes,
                'requirements': session_requirements
            })()

            result = await self.session_matcher.match_nodes_to_session(mock_session)
            matched_ids = result.matched_nodes

            return [node for node in self.discovered_nodes.values()
                   if node.node_id in matched_ids and node.status == "online"]

        # Fallback to basic filtering
        fl_nodes = self.get_online_nodes("federated_learning")

        if len(fl_nodes) >= min_nodes:
            # Sort by comprehensive score (health, reputation, capabilities)
            fl_nodes.sort(key=lambda n: (
                n.reputation_score,  # Primary: reputation
                1 - n.load_factor,   # Secondary: available capacity
                n.hardware_specs.get("memory_gb", 0)  # Tertiary: memory
            ), reverse=True)
            return fl_nodes[:min_nodes]

        return fl_nodes

    def find_nodes_for_federated_learning(self, min_nodes: int = 2,
                                        session_requirements: Optional[Dict[str, Any]] = None) -> List[DiscoveredNode]:
        """
        Find nodes suitable for federated learning using intelligent matching (sync version).

        Args:
            min_nodes: Minimum number of nodes required
            session_requirements: Specific requirements for the session

        Returns:
            List of suitable nodes
        """
        # For sync calls, use basic filtering without session matcher
        fl_nodes = self.get_online_nodes("federated_learning")

        if len(fl_nodes) >= min_nodes:
            # Sort by comprehensive score (health, reputation, capabilities)
            fl_nodes.sort(key=lambda n: (
                n.reputation_score,  # Primary: reputation
                1 - n.load_factor,   # Secondary: available capacity
                n.hardware_specs.get("memory_gb", 0)  # Tertiary: memory
            ), reverse=True)
            return fl_nodes[:min_nodes]

        return fl_nodes

    async def match_session_to_nodes(self, session: FederatedSession) -> Optional[MatchingResult]:
        """
        Match a federated session to optimal nodes using the session matcher.

        Args:
            session: The federated session to match

        Returns:
            Matching result or None if no matcher available
        """
        if not self.session_matcher:
            logger.warning("Session matcher not available for intelligent matching")
            return None

        return await self.session_matcher.match_nodes_to_session(session)

    def get_dynamic_node_info(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive dynamic information about a node.

        Args:
            node_id: ID of the node

        Returns:
            Dynamic node information including health, capabilities, etc.
        """
        if node_id not in self.discovered_nodes:
            return None

        node = self.discovered_nodes[node_id]
        health_info = None
        if self.health_monitor:
            health_info = self.health_monitor.get_node_health(node_id)

        return {
            'node_id': node.node_id,
            'status': node.status,
            'health_status': node.health_status.value if hasattr(node.health_status, 'value') else str(node.health_status),
            'load_factor': node.load_factor,
            'reputation_score': node.reputation_score,
            'session_count': node.session_count,
            'dynamic_capabilities': node.dynamic_capabilities,
            'last_seen': node.last_seen,
            'registry_synced': node.registry_entry is not None,
            'health_metrics': health_info.to_dict() if health_info else None
        }

    def _estimate_network_bandwidth(self) -> float:
        """Estimate available network bandwidth in Mbps."""
        try:
            # Simple estimation based on system info
            # In production, this would use actual network measurements
            return 100.0  # Placeholder: 100 Mbps
        except:
            return 10.0  # Minimum estimate

    def get_network_stats(self) -> Dict[str, Any]:
        """Get comprehensive network discovery statistics."""
        total_nodes = len(self.discovered_nodes)
        online_nodes = len([n for n in self.discovered_nodes.values() if n.status == "online"])
        offline_nodes = total_nodes - online_nodes

        # Count capabilities
        capabilities = {}
        for node in self.discovered_nodes.values():
            for cap in node.capabilities:
                capabilities[cap] = capabilities.get(cap, 0) + 1

        # Health distribution
        health_stats = {}
        for node in self.discovered_nodes.values():
            health = node.health_status.value if hasattr(node.health_status, 'value') else str(node.health_status)
            health_stats[health] = health_stats.get(health, 0) + 1

        # Load and performance metrics
        avg_load = sum(n.load_factor for n in self.discovered_nodes.values()) / total_nodes if total_nodes > 0 else 0
        avg_reputation = sum(n.reputation_score for n in self.discovered_nodes.values()) / total_nodes if total_nodes > 0 else 0

        # Registry integration stats
        registry_synced = len([n for n in self.discovered_nodes.values() if n.registry_entry is not None])

        return {
            "total_discovered": total_nodes,
            "online_nodes": online_nodes,
            "offline_nodes": offline_nodes,
            "capabilities": capabilities,
            "health_distribution": health_stats,
            "average_load_factor": round(avg_load, 3),
            "average_reputation_score": round(avg_reputation, 3),
            "registry_synced_nodes": registry_synced,
            "is_running": self.is_running,
            "local_node_id": self.node_id,
            "discovery_metrics": self.discovery_metrics.copy(),
            "auto_scaling_enabled": self.auto_scaling_enabled,
            "target_node_count": self.target_node_count,
            "current_utilization": round(self._calculate_system_utilization(), 3)
        }

    async def request_node_info(self, target_node_id: str) -> Optional[Dict[str, Any]]:
        """
        Request detailed information from a specific node.

        Args:
            target_node_id: ID of node to query

        Returns:
            Node information if available
        """
        if not self.ipfs_client:
            return None

        # Send info request
        request = {
            "type": "info_request",
            "from_node": self.node_id,
            "target_node": target_node_id,
            "timestamp": time.time()
        }

        try:
            await self.ipfs_client.publish_message(
                f"ailoos.node.{target_node_id}",
                json.dumps(request)
            )

            # In a real implementation, we'd wait for a response
            # For now, return cached info
            if target_node_id in self.discovered_nodes:
                return asdict(self.discovered_nodes[target_node_id])

        except Exception as e:
            logger.warning(f"⚠️ Failed to request node info: {e}")

        return None


@dataclass
class NetworkEvent:
    """Representa un evento de red (nodo uniéndose o dejándose)"""
    event_type: str  # 'node_joined', 'node_left'
    node_id: str
    timestamp: float
    node_info: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None


class NodeDiscoveryManager:
    """
    Manager integrado que combina NodeRegistry, SessionMatcher y HealthMonitor
    con eventos de red dinámicos, persistencia IPFS y integración con coordinator.
    """

    def __init__(self,
                 node_id: Optional[str] = None,
                 consensus_manager: Optional[DistributedConsensusManager] = None,
                 query_engine: Optional[DistributedQueryEngine] = None,
                 coordinator_url: Optional[str] = None):
        self.node_id = node_id or self._generate_node_id()
        self.coordinator_url = coordinator_url or os.getenv('AILOOS_COORDINATOR_URL', 'http://localhost:8000')

        # Componentes integrados
        self.node_discovery: Optional[NodeDiscovery] = None
        self.node_registry: Optional[NodeRegistry] = None
        self.session_matcher: Optional[SessionMatcher] = None
        self.health_monitor: Optional[HealthMonitor] = None

        # IPFS para persistencia
        self.ipfs_manager: Optional[IPFSManager] = None
        self.state_cid: Optional[str] = None  # CID del estado persistido

        # Estado del sistema
        self.is_initialized = False
        self.is_running = False

        # Eventos de red
        self.network_events: List[NetworkEvent] = []
        self.event_callbacks: List[Callable[[NetworkEvent], None]] = []
        self.max_events_history = 1000

        # Persistencia
        self.state_persistence_interval = 300  # 5 minutos
        self.last_state_save = 0

        # Managers externos
        self.consensus_manager = consensus_manager
        self.query_engine = query_engine

        # Estadísticas del manager
        self.stats = {
            'initialized_at': None,
            'total_events_processed': 0,
            'state_saves': 0,
            'coordinator_notifications': 0,
            'errors': 0
        }

    def _generate_node_id(self) -> str:
        """Genera ID único para el nodo"""
        machine_id = platform.node() + platform.machine()
        return f"manager_{hashlib.sha256(machine_id.encode()).hexdigest()[:16]}"

    async def initialize_system(self, ipfs_client=None) -> bool:
        """
        Inicialización completa del sistema de discovery.
        Crea y configura todos los componentes integrados.
        """
        try:
            logger.info("🚀 Inicializando NodeDiscoveryManager...")

            # 1. Inicializar IPFS Manager
            self.ipfs_manager = IPFSManager()
            await self.ipfs_manager.initialize()

            # 2. Crear componentes integrados
            self.node_discovery = NodeDiscovery(
                node_id=self.node_id,
                consensus_manager=self.consensus_manager,
                query_engine=self.query_engine
            )
            self.node_discovery.initialize(ipfs_client)

            # Inicializar componentes internos del discovery
            if self.consensus_manager and self.query_engine:
                self.node_discovery._initialize_integrated_components(
                    self.consensus_manager, self.query_engine
                )

            # 3. Obtener referencias a los componentes
            self.node_registry = self.node_discovery.node_registry
            self.session_matcher = self.node_discovery.session_matcher
            self.health_monitor = self.node_discovery.health_monitor

            # 4. Configurar callbacks de eventos
            self._setup_event_callbacks()

            # 5. Cargar estado persistido si existe
            await self._load_persisted_state()

            # 6. Registrar callbacks de alertas
            if self.health_monitor:
                self.health_monitor.add_alert_callback(self._handle_health_alert)

            self.is_initialized = True
            self.stats['initialized_at'] = datetime.now()

            logger.info("✅ NodeDiscoveryManager inicializado exitosamente")
            return True

        except Exception as e:
            logger.error(f"❌ Error inicializando NodeDiscoveryManager: {e}")
            self.stats['errors'] += 1
            return False

    async def start_system(self) -> bool:
        """Inicia el sistema completo de discovery"""
        if not self.is_initialized:
            logger.error("Sistema no inicializado. Llama initialize_system() primero.")
            return False

        try:
            logger.info("▶️ Iniciando sistema de discovery...")

            # Iniciar componentes en orden
            if self.node_registry:
                await self.node_registry.start()
            if self.health_monitor:
                await self.health_monitor.start_monitoring()
            if self.node_discovery:
                await self.node_discovery.start_discovery()

            # Iniciar tareas del manager
            asyncio.create_task(self._event_processing_loop())
            asyncio.create_task(self._state_persistence_loop())
            asyncio.create_task(self._coordinator_sync_loop())

            self.is_running = True
            logger.info("✅ Sistema de discovery iniciado")
            return True

        except Exception as e:
            logger.error(f"❌ Error iniciando sistema: {e}")
            self.stats['errors'] += 1
            return False

    async def stop_system(self):
        """Detiene el sistema completo"""
        logger.info("⏹️ Deteniendo NodeDiscoveryManager...")

        self.is_running = False

        # Detener componentes en orden inverso
        if self.node_discovery:
            await self.node_discovery.stop_discovery()
        if self.health_monitor:
            await self.health_monitor.stop_monitoring()
        if self.node_registry:
            await self.node_registry.stop()

        # Guardar estado final
        await self._persist_state()

        logger.info("✅ NodeDiscoveryManager detenido")

    def _setup_event_callbacks(self):
        """Configura callbacks para eventos de red"""
        # Callback para cuando se descubre un nuevo nodo
        async def on_node_discovered(node_id: str, node_info: Dict[str, Any]):
            event = NetworkEvent(
                event_type='node_joined',
                node_id=node_id,
                timestamp=time.time(),
                node_info=node_info
            )
            await self._process_network_event(event)

        # Callback para cuando un nodo se desconecta
        async def on_node_left(node_id: str, reason: str = "timeout"):
            event = NetworkEvent(
                event_type='node_left',
                node_id=node_id,
                timestamp=time.time(),
                reason=reason
            )
            await self._process_network_event(event)

        # Aquí se registrarían los callbacks en los componentes
        # (En una implementación real, los componentes tendrían métodos para registrar callbacks)

    async def _process_network_event(self, event: NetworkEvent):
        """Procesa un evento de red"""
        # Agregar a historial
        self.network_events.append(event)
        if len(self.network_events) > self.max_events_history:
            self.network_events.pop(0)

        self.stats['total_events_processed'] += 1

        # Notificar callbacks registrados
        for callback in self.event_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.warning(f"Error en callback de evento: {e}")

        # Notificar al coordinator
        await self._notify_coordinator_event(event)

        logger.info(f"📡 Evento de red procesado: {event.event_type} - {event.node_id}")

    def add_event_callback(self, callback: Callable[[NetworkEvent], None]):
        """Registra un callback para eventos de red"""
        self.event_callbacks.append(callback)

    async def _handle_health_alert(self, alert):
        """Maneja alertas de salud y las convierte en eventos si es necesario"""
        # Convertir alertas críticas en eventos de red
        if alert.severity in ['CRITICAL', 'ERROR']:
            if 'connectivity' in alert.title.lower() or 'unreachable' in alert.title.lower():
                event = NetworkEvent(
                    event_type='node_left',
                    node_id=alert.node_id,
                    timestamp=time.time(),
                    reason=f"Health alert: {alert.title}",
                    node_info={'alert': alert.to_dict()}
                )
                await self._process_network_event(event)

    async def _notify_coordinator_event(self, event: NetworkEvent):
        """Notifica evento al coordinator"""
        try:
            if not self.coordinator_url:
                return

            import aiohttp

            notification = {
                'type': 'network_event',
                'event': {
                    'event_type': event.event_type,
                    'node_id': event.node_id,
                    'timestamp': event.timestamp,
                    'node_info': event.node_info,
                    'reason': event.reason
                },
                'source_manager': self.node_id,
                'timestamp': time.time()
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.coordinator_url}/api/discovery/events",
                    json=notification,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        self.stats['coordinator_notifications'] += 1
                        logger.debug(f"✅ Evento notificado al coordinator: {event.event_type}")
                    else:
                        logger.warning(f"Error notificando evento al coordinator: HTTP {response.status}")

        except Exception as e:
            logger.debug(f"Error notificando evento al coordinator: {e}")

    async def _load_persisted_state(self):
        """Carga estado persistido desde IPFS"""
        try:
            if not self.ipfs_manager or not self.state_cid:
                # Intentar encontrar último estado guardado
                # (En implementación real, buscaría en IPFS por tags o referencias)
                return

            state_data = await self.ipfs_manager.retrieve_data(self.state_cid)
            if state_data:
                state = json.loads(state_data.decode())

                # Restaurar eventos recientes
                self.network_events = [
                    NetworkEvent(**event) for event in state.get('network_events', [])
                ][:self.max_events_history]

                # Restaurar estadísticas
                self.stats.update(state.get('stats', {}))

                logger.info(f"✅ Estado cargado desde IPFS: {self.state_cid}")

        except Exception as e:
            logger.warning(f"Error cargando estado persistido: {e}")

    async def _persist_state(self):
        """Persiste estado actual en IPFS"""
        try:
            if not self.ipfs_manager:
                return

            current_time = time.time()
            if current_time - self.last_state_save < self.state_persistence_interval:
                return

            state = {
                'manager_id': self.node_id,
                'timestamp': current_time,
                'network_events': [asdict(event) for event in self.network_events[-100:]],  # Últimos 100 eventos
                'stats': self.stats,
                'component_states': {
                    'discovery': self.node_discovery.get_network_stats() if self.node_discovery else {},
                    'registry': self.node_registry.get_stats() if self.node_registry else {},
                    'health': self.health_monitor.get_monitor_stats() if self.health_monitor else {},
                    'matcher': self.session_matcher.get_stats() if self.session_matcher else {}
                }
            }

            state_json = json.dumps(state, default=str)
            cid = await self.ipfs_manager.publish_data(
                state_json.encode(),
                {'type': 'discovery_manager_state', 'manager_id': self.node_id}
            )

            if cid:
                self.state_cid = cid
                self.last_state_save = current_time
                self.stats['state_saves'] += 1

                logger.debug(f"💾 Estado persistido en IPFS: {cid}")

        except Exception as e:
            logger.warning(f"Error persistiendo estado: {e}")

    async def _event_processing_loop(self):
        """Loop de procesamiento de eventos"""
        while self.is_running:
            try:
                # Procesar eventos pendientes o lógica adicional
                await asyncio.sleep(10)  # Procesar cada 10 segundos
            except Exception as e:
                logger.error(f"Error en loop de eventos: {e}")
                await asyncio.sleep(5)

    async def _state_persistence_loop(self):
        """Loop de persistencia de estado"""
        while self.is_running:
            try:
                await self._persist_state()
                await asyncio.sleep(self.state_persistence_interval)
            except Exception as e:
                logger.error(f"Error en loop de persistencia: {e}")
                await asyncio.sleep(60)

    async def _coordinator_sync_loop(self):
        """Loop de sincronización con coordinator"""
        while self.is_running:
            try:
                await self._sync_with_coordinator()
                await asyncio.sleep(300)  # Sincronizar cada 5 minutos
            except Exception as e:
                logger.error(f"Error en sync con coordinator: {e}")
                await asyncio.sleep(60)

    async def _sync_with_coordinator(self):
        """Sincroniza estado con el coordinator"""
        try:
            if not self.coordinator_url:
                return

            import aiohttp

            sync_data = {
                'manager_id': self.node_id,
                'timestamp': time.time(),
                'stats': self.stats,
                'network_summary': self.get_network_summary(),
                'state_cid': self.state_cid
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.coordinator_url}/api/discovery/sync",
                    json=sync_data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.debug("✅ Sincronización con coordinator exitosa")
                    else:
                        logger.debug(f"Sincronización con coordinator: HTTP {response.status}")

        except Exception as e:
            logger.debug(f"Error sincronizando con coordinator: {e}")

    # Métodos públicos delegados a componentes
    async def find_nodes_for_session(self, session: FederatedSession) -> Optional[MatchingResult]:
        """Encuentra nodos para una sesión usando el matcher inteligente"""
        if self.session_matcher and self.node_discovery:
            return await self.node_discovery.match_session_to_nodes(session)
        return None

    def get_discovered_nodes(self) -> List[DiscoveredNode]:
        """Obtiene nodos descubiertos"""
        return self.node_discovery.get_discovered_nodes() if self.node_discovery else []

    def get_network_summary(self) -> Dict[str, Any]:
        """Obtiene resumen completo de la red"""
        summary = {
            'manager_id': self.node_id,
            'is_running': self.is_running,
            'is_initialized': self.is_initialized,
            'total_events': len(self.network_events),
            'stats': self.stats.copy()
        }

        if self.node_discovery:
            summary['discovery'] = self.node_discovery.get_network_stats()

        if self.node_registry:
            summary['registry'] = self.node_registry.get_stats()

        if self.health_monitor:
            summary['health'] = self.health_monitor.get_system_health_summary()

        if self.session_matcher:
            summary['matcher'] = self.session_matcher.get_stats()

        return summary

    def get_recent_events(self, limit: int = 50) -> List[NetworkEvent]:
        """Obtiene eventos recientes de red"""
        return self.network_events[-limit:] if self.network_events else []


# Convenience functions with enhanced integration
_discovery_instance = None
_manager_instance = None

def get_node_discovery_manager(consensus_manager: Optional[DistributedConsensusManager] = None,
                              query_engine: Optional[DistributedQueryEngine] = None,
                              coordinator_url: Optional[str] = None) -> NodeDiscoveryManager:
    """Get singleton node discovery manager instance with full integration."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = NodeDiscoveryManager(
            consensus_manager=consensus_manager,
            query_engine=query_engine,
            coordinator_url=coordinator_url
        )
    return _manager_instance

def get_node_discovery(consensus_manager: Optional[DistributedConsensusManager] = None,
                      query_engine: Optional[DistributedQueryEngine] = None) -> NodeDiscovery:
    """Get singleton node discovery instance with optional integrated components (legacy)."""
    global _discovery_instance
    if _discovery_instance is None:
        _discovery_instance = NodeDiscovery(consensus_manager=consensus_manager, query_engine=query_engine)
    return _discovery_instance

async def initialize_discovery_system(ipfs_client=None,
                                     consensus_manager: Optional[DistributedConsensusManager] = None,
                                     query_engine: Optional[DistributedQueryEngine] = None,
                                     coordinator_url: Optional[str] = None) -> bool:
    """Initialize complete discovery system with NodeDiscoveryManager."""
    manager = get_node_discovery_manager(consensus_manager, query_engine, coordinator_url)
    return await manager.initialize_system(ipfs_client)

async def start_discovery_system(ipfs_client=None,
                                consensus_manager: Optional[DistributedConsensusManager] = None,
                                query_engine: Optional[DistributedQueryEngine] = None,
                                coordinator_url: Optional[str] = None) -> bool:
    """Start complete discovery system with NodeDiscoveryManager."""
    manager = get_node_discovery_manager(consensus_manager, query_engine, coordinator_url)
    if not manager.is_initialized:
        await manager.initialize_system(ipfs_client)
    return await manager.start_system()

async def start_node_discovery(consensus_manager: Optional[DistributedConsensusManager] = None,
                              query_engine: Optional[DistributedQueryEngine] = None):
    """Start node discovery service with integrated components (legacy)."""
    discovery = get_node_discovery(consensus_manager, query_engine)
    await discovery.start_discovery()

async def stop_discovery_system():
    """Stop complete discovery system."""
    global _manager_instance
    if _manager_instance:
        await _manager_instance.stop_system()
        _manager_instance = None

async def stop_node_discovery():
    """Stop node discovery service and integrated components (legacy)."""
    global _discovery_instance
    if _discovery_instance:
        await _discovery_instance.stop_discovery()
        # Stop integrated components
        if _discovery_instance.node_registry:
            await _discovery_instance.node_registry.stop_registry()
        if _discovery_instance.health_monitor:
            await _discovery_instance.health_monitor.stop_monitoring()
        _discovery_instance = None

def find_federated_nodes(min_nodes: int = 2, session_requirements: Optional[Dict[str, Any]] = None) -> List[DiscoveredNode]:
    """Find nodes suitable for federated learning with optional requirements."""
    # Try manager first, fallback to legacy discovery
    if _manager_instance and _manager_instance.is_initialized:
        discovery = _manager_instance.node_discovery
    else:
        discovery = get_node_discovery()

    if discovery:
        return discovery.find_nodes_for_federated_learning(min_nodes, session_requirements)
    return []

async def find_federated_nodes_async(min_nodes: int = 2, session_requirements: Optional[Dict[str, Any]] = None) -> List[DiscoveredNode]:
    """Find nodes suitable for federated learning asynchronously."""
    # Try manager first, fallback to legacy discovery
    if _manager_instance and _manager_instance.is_initialized:
        discovery = _manager_instance.node_discovery
    else:
        discovery = get_node_discovery()

    if discovery:
        return await discovery.find_nodes_for_federated_learning_async(min_nodes, session_requirements)
    return []

async def match_session_async(session: FederatedSession) -> Optional[MatchingResult]:
    """Match a session to optimal nodes asynchronously."""
    # Try manager first for intelligent matching, fallback to legacy
    if _manager_instance and _manager_instance.is_initialized:
        return await _manager_instance.find_nodes_for_session(session)
    else:
        discovery = get_node_discovery()
        return await discovery.match_session_to_nodes(session)

def get_discovery_stats() -> Dict[str, Any]:
    """Get comprehensive discovery system statistics."""
    # Try manager first for complete stats, fallback to legacy
    if _manager_instance and _manager_instance.is_initialized:
        return _manager_instance.get_network_summary()
    else:
        discovery = get_node_discovery()
        stats = discovery.get_network_stats()

        # Add component-specific stats
        if discovery.node_registry:
            stats['registry_stats'] = discovery.node_registry.get_registry_stats()

        if discovery.session_matcher:
            stats['matcher_stats'] = discovery.session_matcher.get_stats()

        if discovery.health_monitor:
            stats['health_stats'] = discovery.health_monitor.get_monitor_stats()

        return stats

def get_network_events(limit: int = 50) -> List[NetworkEvent]:
    """Get recent network events from the manager."""
    if _manager_instance and _manager_instance.is_initialized:
        return _manager_instance.get_recent_events(limit)
    return []

def add_network_event_callback(callback: Callable[[NetworkEvent], None]):
    """Add callback for network events."""
    if _manager_instance and _manager_instance.is_initialized:
        _manager_instance.add_event_callback(callback)