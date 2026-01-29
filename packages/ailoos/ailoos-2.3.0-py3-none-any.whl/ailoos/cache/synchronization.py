"""
P2P Cache Synchronization for Distributed Cache System
Handles automatic synchronization between cache nodes using gossip protocol
"""

import asyncio
import time
import random
import hashlib
from typing import Dict, List, Set, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import logging
import json

logger = logging.getLogger(__name__)

@dataclass
class VectorClock:
    """Vector clock for tracking causality"""
    node_clocks: Dict[str, int] = field(default_factory=dict)

    def increment(self, node_id: str):
        """Increment clock for a node"""
        self.node_clocks[node_id] = self.node_clocks.get(node_id, 0) + 1

    def merge(self, other: 'VectorClock'):
        """Merge with another vector clock"""
        for node, clock in other.node_clocks.items():
            self.node_clocks[node] = max(self.node_clocks.get(node, 0), clock)

    def compare(self, other: 'VectorClock') -> int:
        """
        Compare vector clocks
        Returns:
        -1 if self < other
         0 if concurrent
         1 if self > other
        """
        self_greater = False
        other_greater = False

        all_nodes = set(self.node_clocks.keys()) | set(other.node_clocks.keys())

        for node in all_nodes:
            self_clock = self.node_clocks.get(node, 0)
            other_clock = other.node_clocks.get(node, 0)

            if self_clock > other_clock:
                self_greater = True
            elif other_clock > self_clock:
                other_greater = True

        if self_greater and not other_greater:
            return 1
        elif other_greater and not self_greater:
            return -1
        else:
            return 0

    def to_dict(self) -> Dict[str, int]:
        return self.node_clocks.copy()

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'VectorClock':
        return cls(node_clocks=data)

@dataclass
class CacheEntryMetadata:
    """Metadata for cache entries in distributed system"""
    key: str
    version: VectorClock
    last_modified: float
    ttl: Optional[float] = None
    checksum: str = ""

    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return time.time() > self.last_modified + self.ttl

    def update_checksum(self, value: Any):
        """Update checksum based on value"""
        data = json.dumps(value, sort_keys=True)
        self.checksum = hashlib.md5(data.encode()).hexdigest()

@dataclass
class SyncMessage:
    """Message for P2P synchronization"""
    message_type: str  # 'digest', 'request', 'response', 'heartbeat'
    node_id: str
    timestamp: float
    payload: Dict[str, Any]

class P2PCacheSynchronization:
    """P2P cache synchronization using gossip protocol"""

    def __init__(self,
                 node_id: str,
                 known_nodes: List[str] = None,
                 gossip_interval: float = 1.0,
                 heartbeat_interval: float = 5.0,
                 max_gossip_fanout: int = 3):
        self.node_id = node_id
        self.known_nodes = set(known_nodes or [])
        self.gossip_interval = gossip_interval
        self.heartbeat_interval = heartbeat_interval
        self.max_gossip_fanout = max_gossip_fanout

        # Local state
        self.local_metadata: Dict[str, CacheEntryMetadata] = {}
        self.vector_clock = VectorClock()
        self.vector_clock.increment(node_id)

        # Network state
        self.node_states: Dict[str, Dict[str, VectorClock]] = defaultdict(dict)  # node -> {key -> version}
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.active_connections: Dict[str, Any] = {}  # Mock for actual connections

        # Gossip state
        self.gossip_round = 0
        self.last_heartbeat: Dict[str, float] = {}

        # Callbacks
        self.on_entry_update: Optional[Callable[[str, Any, VectorClock], None]] = None
        self.on_entry_invalidate: Optional[Callable[[str], None]] = None
        self.send_message_callback: Optional[Callable[[str, SyncMessage], None]] = None

        # Tasks
        self.gossip_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None

        # Stats
        self.messages_sent = 0
        self.messages_received = 0
        self.conflicts_resolved = 0
        self.entries_synchronized = 0

    async def start(self):
        """Start synchronization"""
        logger.info(f"Starting P2P cache sync for node {self.node_id}")
        self.gossip_task = asyncio.create_task(self._gossip_loop())
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """Stop synchronization"""
        if self.gossip_task:
            self.gossip_task.cancel()
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()

        try:
            await asyncio.gather(
                self.gossip_task,
                self.heartbeat_task,
                self.cleanup_task,
                return_exceptions=True
            )
        except asyncio.CancelledError:
            pass

    def update_local_entry(self, key: str, value: Any, ttl: Optional[float] = None):
        """Update local cache entry and prepare for sync"""
        self.vector_clock.increment(self.node_id)

        if key not in self.local_metadata:
            self.local_metadata[key] = CacheEntryMetadata(
                key=key,
                version=VectorClock(),
                last_modified=time.time(),
                ttl=ttl
            )

        metadata = self.local_metadata[key]
        metadata.version = self.vector_clock.copy()
        metadata.last_modified = time.time()
        metadata.ttl = ttl
        metadata.update_checksum(value)

        logger.debug(f"Updated local entry: {key}")

    def invalidate_local_entry(self, key: str):
        """Invalidate local cache entry"""
        if key in self.local_metadata:
            del self.local_metadata[key]
            self.vector_clock.increment(self.node_id)
            logger.debug(f"Invalidated local entry: {key}")

    async def _gossip_loop(self):
        """Main gossip protocol loop"""
        while True:
            try:
                await self._perform_gossip_round()
                await asyncio.sleep(self.gossip_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Gossip loop error: {e}")
                await asyncio.sleep(self.gossip_interval)

    async def _perform_gossip_round(self):
        """Perform one round of gossip"""
        if not self.known_nodes:
            return

        # Select random peers
        peers = random.sample(list(self.known_nodes), min(self.max_gossip_fanout, len(self.known_nodes)))

        for peer in peers:
            if peer != self.node_id:
                await self._send_digest_to_peer(peer)

        self.gossip_round += 1

    async def _send_digest_to_peer(self, peer: str):
        """Send digest of local state to peer"""
        # Create digest: key -> version mapping
        digest = {key: metadata.version.to_dict() for key, metadata in self.local_metadata.items()}

        message = SyncMessage(
            message_type='digest',
            node_id=self.node_id,
            timestamp=time.time(),
            payload={'digest': digest}
        )

        await self._send_message(peer, message)

    async def _heartbeat_loop(self):
        """Send periodic heartbeats"""
        while True:
            try:
                await self._send_heartbeats()
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
                await asyncio.sleep(self.heartbeat_interval)

    async def _send_heartbeats(self):
        """Send heartbeat to all known nodes"""
        for node in self.known_nodes:
            if node != self.node_id:
                message = SyncMessage(
                    message_type='heartbeat',
                    node_id=self.node_id,
                    timestamp=time.time(),
                    payload={'status': 'alive'}
                )
                await self._send_message(node, message)

    async def _cleanup_loop(self):
        """Cleanup expired entries and failed nodes"""
        while True:
            try:
                await self._cleanup_expired_entries()
                await self._cleanup_failed_nodes()
                await asyncio.sleep(30)  # Cleanup every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(30)

    async def _cleanup_expired_entries(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = []

        for key, metadata in self.local_metadata.items():
            if metadata.is_expired():
                expired_keys.append(key)

        for key in expired_keys:
            del self.local_metadata[key]
            if self.on_entry_invalidate:
                await self.on_entry_invalidate(key)

    async def _cleanup_failed_nodes(self):
        """Remove nodes that haven't sent heartbeats recently"""
        current_time = time.time()
        failed_nodes = []

        for node, last_heartbeat in self.last_heartbeat.items():
            if current_time - last_heartbeat > self.heartbeat_interval * 3:
                failed_nodes.append(node)

        for node in failed_nodes:
            self.known_nodes.discard(node)
            del self.last_heartbeat[node]
            logger.warning(f"Removed failed node: {node}")

    async def handle_message(self, message: SyncMessage):
        """Handle incoming synchronization message"""
        self.messages_received += 1

        if message.message_type == 'digest':
            await self._handle_digest(message)
        elif message.message_type == 'request':
            await self._handle_request(message)
        elif message.message_type == 'response':
            await self._handle_response(message)
        elif message.message_type == 'heartbeat':
            await self._handle_heartbeat(message)

    async def _handle_digest(self, message: SyncMessage):
        """Handle digest message from peer"""
        peer_digest = message.payload.get('digest', {})
        self.node_states[message.node_id] = {key: VectorClock.from_dict(vc) for key, vc in peer_digest.items()}

        # Find keys that need synchronization
        keys_to_request = []
        for key, remote_version in self.node_states[message.node_id].items():
            local_version = self.local_metadata.get(key)
            if local_version is None or local_version.version.compare(remote_version) < 0:
                keys_to_request.append(key)

        if keys_to_request:
            request_message = SyncMessage(
                message_type='request',
                node_id=self.node_id,
                timestamp=time.time(),
                payload={'keys': keys_to_request}
            )
            await self._send_message(message.node_id, request_message)

    async def _handle_request(self, message: SyncMessage):
        """Handle request for specific keys"""
        requested_keys = message.payload.get('keys', [])
        response_data = {}

        for key in requested_keys:
            if key in self.local_metadata:
                metadata = self.local_metadata[key]
                response_data[key] = {
                    'version': metadata.version.to_dict(),
                    'last_modified': metadata.last_modified,
                    'ttl': metadata.ttl,
                    'checksum': metadata.checksum
                }

        if response_data:
            response_message = SyncMessage(
                message_type='response',
                node_id=self.node_id,
                timestamp=time.time(),
                payload={'entries': response_data}
            )
            await self._send_message(message.node_id, response_message)

    async def _handle_response(self, message: SyncMessage):
        """Handle response with entry data"""
        entries = message.payload.get('entries', {})

        for key, entry_data in entries.items():
            remote_version = VectorClock.from_dict(entry_data['version'])
            local_metadata = self.local_metadata.get(key)

            if local_metadata is None:
                # New entry
                self.local_metadata[key] = CacheEntryMetadata(
                    key=key,
                    version=remote_version,
                    last_modified=entry_data['last_modified'],
                    ttl=entry_data['ttl'],
                    checksum=entry_data['checksum']
                )
                self.entries_synchronized += 1

                # Notify about new entry (value would come separately in real implementation)
                if self.on_entry_update:
                    await self.on_entry_update(key, None, remote_version)

            elif local_metadata.version.compare(remote_version) < 0:
                # Remote is newer
                local_metadata.version = remote_version
                local_metadata.last_modified = entry_data['last_modified']
                local_metadata.ttl = entry_data['ttl']
                local_metadata.checksum = entry_data['checksum']
                self.entries_synchronized += 1

                if self.on_entry_update:
                    await self.on_entry_update(key, None, remote_version)

            elif local_metadata.version.compare(remote_version) == 0:
                # Concurrent - resolve conflict
                await self._resolve_conflict(key, local_metadata, remote_version, entry_data)

    async def _handle_heartbeat(self, message: SyncMessage):
        """Handle heartbeat message"""
        self.last_heartbeat[message.node_id] = message.timestamp

    async def _resolve_conflict(self, key: str, local_metadata: CacheEntryMetadata,
                               remote_version: VectorClock, remote_data: Dict[str, Any]):
        """Resolve version conflicts"""
        # Simple strategy: last write wins
        if remote_data['last_modified'] > local_metadata.last_modified:
            local_metadata.version = remote_version
            local_metadata.last_modified = remote_data['last_modified']
            local_metadata.ttl = remote_data['ttl']
            local_metadata.checksum = remote_data['checksum']

            if self.on_entry_update:
                await self.on_entry_update(key, None, remote_version)

        self.conflicts_resolved += 1
        logger.debug(f"Resolved conflict for key: {key}")

    async def _send_message(self, target_node: str, message: SyncMessage):
        """Send message to target node"""
        if self.send_message_callback:
            await self.send_message_callback(target_node, message)
            self.messages_sent += 1
        else:
            logger.warning(f"No send callback configured, dropping message to {target_node}")

    def add_node(self, node_id: str):
        """Add a new node to the known nodes list"""
        self.known_nodes.add(node_id)
        logger.info(f"Added node to sync: {node_id}")

    def remove_node(self, node_id: str):
        """Remove a node from the known nodes list"""
        self.known_nodes.discard(node_id)
        if node_id in self.node_states:
            del self.node_states[node_id]
        if node_id in self.last_heartbeat:
            del self.last_heartbeat[node_id]
        logger.info(f"Removed node from sync: {node_id}")

    def get_stats(self) -> Dict[str, Any]:
        """Get synchronization statistics"""
        return {
            'node_id': self.node_id,
            'known_nodes': len(self.known_nodes),
            'local_entries': len(self.local_metadata),
            'gossip_rounds': self.gossip_round,
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'entries_synchronized': self.entries_synchronized,
            'conflicts_resolved': self.conflicts_resolved,
            'active_connections': len(self.active_connections)
        }

    def set_message_callback(self, callback: Callable[[str, SyncMessage], None]):
        """Set callback for sending messages"""
        self.send_message_callback = callback

    def set_entry_update_callback(self, callback: Callable[[str, Any, VectorClock], None]):
        """Set callback for entry updates"""
        self.on_entry_update = callback

    def set_invalidation_callback(self, callback: Callable[[str], None]):
        """Set callback for entry invalidations"""
        self.on_entry_invalidate = callback