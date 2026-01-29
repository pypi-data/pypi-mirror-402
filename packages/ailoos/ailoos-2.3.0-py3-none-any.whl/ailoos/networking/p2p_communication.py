#!/usr/bin/env python3
"""
Peer-to-Peer Communication System for Ailoos
Implementa comunicación peer-to-peer entre nodos con discovery automático y enrutamiento
"""

import asyncio
import logging
import socket
import json
import time
import hashlib
import secrets
from typing import Dict, List, Any, Optional, Tuple, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import aiohttp
import aiofiles
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
import random
from collections import defaultdict, deque

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Tipos de mensajes P2P"""
    HANDSHAKE = "handshake"
    HEARTBEAT = "heartbeat"
    DATA_REQUEST = "data_request"
    DATA_RESPONSE = "data_response"
    PEER_DISCOVERY = "peer_discovery"
    PEER_ANNOUNCEMENT = "peer_announcement"
    CONSENSUS_PROPOSAL = "consensus_proposal"
    CONSENSUS_VOTE = "consensus_vote"
    BLOCK_PROPOSAL = "block_proposal"
    TRANSACTION = "transaction"

class NodeState(Enum):
    """Estados de un nodo"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ACTIVE = "active"
    SYNCHRONIZING = "synchronizing"

@dataclass
class PeerInfo:
    """Información de un peer"""
    node_id: str
    endpoint: str  # ip:port
    public_key: Optional[str] = None
    last_seen: Optional[datetime] = None
    state: NodeState = NodeState.DISCONNECTED
    latency_ms: float = float('inf')
    reputation_score: float = 0.5
    supported_protocols: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class P2PMessage:
    """Mensaje P2P"""
    message_id: str
    message_type: MessageType
    sender_id: str
    recipient_id: Optional[str] = None  # None for broadcast
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    ttl: int = 64  # Time to live for message routing
    signature: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'message_id': self.message_id,
            'message_type': self.message_type.value,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'payload': self.payload,
            'timestamp': self.timestamp.isoformat(),
            'ttl': self.ttl,
            'signature': self.signature
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'P2PMessage':
        """Create from dictionary"""
        return cls(
            message_id=data['message_id'],
            message_type=MessageType(data['message_type']),
            sender_id=data['sender_id'],
            recipient_id=data.get('recipient_id'),
            payload=data.get('payload', {}),
            timestamp=datetime.fromisoformat(data['timestamp']),
            ttl=data.get('ttl', 64),
            signature=data.get('signature')
        )

class P2PCommunicationManager:
    """
    Gestor de comunicaciones P2P con discovery automático y enrutamiento inteligente
    """

    def __init__(self, node_id: str, listen_port: int = 0, bootstrap_peers: List[str] = None):
        self.node_id = node_id
        self.listen_port = listen_port
        self.bootstrap_peers = bootstrap_peers or []

        # Node identity
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
        self.public_key_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

        # Peer management
        self.known_peers: Dict[str, PeerInfo] = {}
        self.active_connections: Dict[str, aiohttp.ClientSession] = {}
        self.routing_table: Dict[str, List[str]] = defaultdict(list)  # node_id -> [next_hop_node_ids]

        # Message handling
        self.message_handlers: Dict[MessageType, List[Callable]] = defaultdict(list)
        self.pending_messages: Dict[str, P2PMessage] = {}
        self.message_history: deque = deque(maxlen=1000)

        # Network state
        self.is_running = False
        self.server = None
        self.discovery_task = None
        self.heartbeat_task = None

        # Performance metrics
        self.messages_sent = 0
        self.messages_received = 0
        self.bytes_sent = 0
        self.bytes_received = 0

        # Configuration
        self.heartbeat_interval = 30  # seconds
        self.peer_timeout = 300  # seconds
        self.max_peers = 50
        self.message_ttl = 64

        # Register default message handlers
        self._register_default_handlers()

        logger.info(f"🌐 P2P Communication Manager initialized for node {node_id}")

    def _register_default_handlers(self):
        """Register default message handlers"""
        self.register_message_handler(MessageType.HANDSHAKE, self._handle_handshake)
        self.register_message_handler(MessageType.HEARTBEAT, self._handle_heartbeat)
        self.register_message_handler(MessageType.PEER_DISCOVERY, self._handle_peer_discovery)
        self.register_message_handler(MessageType.PEER_ANNOUNCEMENT, self._handle_peer_announcement)

    async def start(self):
        """Start P2P communication"""
        if self.is_running:
            return

        self.is_running = True

        # Start server
        self.server = await asyncio.start_server(
            self._handle_incoming_connection,
            '0.0.0.0',
            self.listen_port
        )

        # Get actual port if 0 was specified
        actual_port = self.server.sockets[0].getsockname()[1]
        self.listen_port = actual_port

        logger.info(f"🚀 P2P server started on port {actual_port}")

        # Connect to bootstrap peers
        if self.bootstrap_peers:
            await self._connect_to_bootstrap_peers()

        # Start background tasks
        self.discovery_task = asyncio.create_task(self._peer_discovery_loop())
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        # Announce ourselves to the network
        await self._announce_self()

    async def stop(self):
        """Stop P2P communication"""
        if not self.is_running:
            return

        self.is_running = False

        # Stop background tasks
        if self.discovery_task:
            self.discovery_task.cancel()
        if self.heartbeat_task:
            self.heartbeat_task.cancel()

        # Close connections
        for session in self.active_connections.values():
            await session.close()
        self.active_connections.clear()

        # Close server
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        logger.info("⏹️ P2P communication stopped")

    def register_message_handler(self, message_type: MessageType, handler: Callable):
        """Register a message handler"""
        self.message_handlers[message_type].append(handler)
        logger.debug(f"Registered handler for {message_type.value}")

    async def send_message(self, message: P2PMessage) -> bool:
        """Send a message to a peer or broadcast"""
        try:
            # Sign message
            message.signature = self._sign_message(message)

            if message.recipient_id:
                # Direct message
                return await self._send_direct_message(message)
            else:
                # Broadcast message
                return await self._broadcast_message(message)

        except Exception as e:
            logger.error(f"Failed to send message {message.message_id}: {e}")
            return False

    async def _send_direct_message(self, message: P2PMessage) -> bool:
        """Send message directly to a specific peer"""
        if message.recipient_id not in self.known_peers:
            logger.warning(f"Unknown recipient: {message.recipient_id}")
            return False

        peer = self.known_peers[message.recipient_id]
        if peer.state != NodeState.ACTIVE:
            logger.warning(f"Peer {message.recipient_id} not active")
            return False

        return await self._send_to_peer(peer, message)

    async def _broadcast_message(self, message: P2PMessage) -> bool:
        """Broadcast message to all known peers"""
        success_count = 0
        total_count = 0

        for peer in self.known_peers.values():
            if peer.state == NodeState.ACTIVE and peer.node_id != self.node_id:
                total_count += 1
                if await self._send_to_peer(peer, message):
                    success_count += 1

        success_rate = success_count / max(total_count, 1)
        logger.debug(f"Broadcast: {success_count}/{total_count} peers received message")

        return success_rate > 0.5  # Consider successful if >50% received

    async def _send_to_peer(self, peer: PeerInfo, message: P2PMessage) -> bool:
        """Send message to a specific peer"""
        try:
            # Get or create connection
            if peer.node_id not in self.active_connections:
                self.active_connections[peer.node_id] = aiohttp.ClientSession()

            session = self.active_connections[peer.node_id]

            # Send message
            start_time = time.time()
            async with session.post(
                f"http://{peer.endpoint}/p2p/message",
                json=message.to_dict(),
                timeout=10
            ) as response:

                latency = (time.time() - start_time) * 1000
                peer.latency_ms = latency

                if response.status == 200:
                    self.messages_sent += 1
                    self.bytes_sent += len(json.dumps(message.to_dict()).encode())
                    return True
                else:
                    logger.warning(f"Failed to send to {peer.node_id}: HTTP {response.status}")
                    return False

        except Exception as e:
            logger.warning(f"Error sending to {peer.node_id}: {e}")
            peer.state = NodeState.DISCONNECTED
            return False

    def _sign_message(self, message: P2PMessage) -> str:
        """Sign a message with node's private key"""
        message_data = json.dumps({
            'message_id': message.message_id,
            'message_type': message.message_type.value,
            'sender_id': message.sender_id,
            'recipient_id': message.recipient_id,
            'payload': message.payload,
            'timestamp': message.timestamp.isoformat(),
            'ttl': message.ttl
        }, sort_keys=True).encode()

        signature = self.private_key.sign(
            message_data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        return signature.hex()

    def _verify_message_signature(self, message: P2PMessage, public_key_pem: str) -> bool:
        """Verify message signature"""
        try:
            public_key = serialization.load_pem_public_key(public_key_pem.encode())

            message_data = json.dumps({
                'message_id': message.message_id,
                'message_type': message.message_type.value,
                'sender_id': message.sender_id,
                'recipient_id': message.recipient_id,
                'payload': message.payload,
                'timestamp': message.timestamp.isoformat(),
                'ttl': message.ttl
            }, sort_keys=True).encode()

            signature = bytes.fromhex(message.signature)

            public_key.verify(
                signature,
                message_data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

            return True

        except Exception as e:
            logger.warning(f"Signature verification failed: {e}")
            return False

    async def _handle_incoming_connection(self, reader: asyncio.StreamReader,
                                        writer: asyncio.StreamWriter):
        """Handle incoming P2P connection"""
        try:
            # Read message
            data = await reader.read(65536)
            if not data:
                return

            message_data = json.loads(data.decode())
            message = P2PMessage.from_dict(message_data)

            # Update peer info
            peer_ip, peer_port = writer.get_extra_info('peername')
            peer_endpoint = f"{peer_ip}:{peer_port}"

            if message.sender_id not in self.known_peers:
                self.known_peers[message.sender_id] = PeerInfo(
                    node_id=message.sender_id,
                    endpoint=peer_endpoint,
                    last_seen=datetime.now(),
                    state=NodeState.CONNECTED
                )

            peer = self.known_peers[message.sender_id]
            peer.last_seen = datetime.now()
            peer.endpoint = peer_endpoint

            # Verify signature if present
            if message.signature and peer.public_key:
                if not self._verify_message_signature(message, peer.public_key):
                    logger.warning(f"Invalid signature from {message.sender_id}")
                    writer.close()
                    await writer.wait_closed()
                    return

            # Process message
            await self._process_message(message)

            # Update metrics
            self.messages_received += 1
            self.bytes_received += len(data)

            # Send acknowledgment
            writer.write(b"ACK")
            await writer.drain()

        except Exception as e:
            logger.error(f"Error handling incoming connection: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def _process_message(self, message: P2PMessage):
        """Process incoming message"""
        # Store in history
        self.message_history.append(message)

        # Decrement TTL
        message.ttl -= 1

        # Route message if needed
        if message.recipient_id and message.recipient_id != self.node_id:
            await self._route_message(message)
            return

        # Handle message locally
        handlers = self.message_handlers.get(message.message_type, [])
        for handler in handlers:
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"Message handler error: {e}")

    async def _route_message(self, message: P2PMessage):
        """Route message to destination"""
        if message.ttl <= 0:
            logger.warning(f"Message TTL expired: {message.message_id}")
            return

        # Find next hop
        next_hops = self.routing_table.get(message.recipient_id, [])

        if not next_hops:
            # Flood to all peers (simple routing)
            next_hops = [peer_id for peer_id in self.known_peers.keys()
                        if peer_id != message.sender_id]

        # Send to next hops
        for next_hop in next_hops[:3]:  # Limit to 3 hops to prevent flooding
            if next_hop in self.known_peers:
                peer = self.known_peers[next_hop]
                await self._send_to_peer(peer, message)

    async def _handle_handshake(self, message: P2PMessage):
        """Handle handshake message"""
        sender_id = message.sender_id
        payload = message.payload

        # Update peer info
        if sender_id in self.known_peers:
            peer = self.known_peers[sender_id]
            peer.public_key = payload.get('public_key')
            peer.supported_protocols = payload.get('protocols', [])
            peer.state = NodeState.ACTIVE
            peer.last_seen = datetime.now()

        # Send handshake response
        response = P2PMessage(
            message_id=f"handshake_resp_{secrets.token_hex(8)}",
            message_type=MessageType.HANDSHAKE,
            sender_id=self.node_id,
            recipient_id=sender_id,
            payload={
                'public_key': self.public_key_pem,
                'protocols': ['p2p/v1', 'consensus/v1', 'data/v1'],
                'node_info': {
                    'version': '1.0.0',
                    'capabilities': ['routing', 'storage', 'consensus']
                }
            }
        )

        await self.send_message(response)

    async def _handle_heartbeat(self, message: P2PMessage):
        """Handle heartbeat message"""
        sender_id = message.sender_id

        if sender_id in self.known_peers:
            peer = self.known_peers[sender_id]
            peer.last_seen = datetime.now()
            peer.state = NodeState.ACTIVE

    async def _handle_peer_discovery(self, message: P2PMessage):
        """Handle peer discovery request"""
        # Send list of known peers
        known_peer_list = [
            {
                'node_id': peer.node_id,
                'endpoint': peer.endpoint,
                'last_seen': peer.last_seen.isoformat() if peer.last_seen else None,
                'reputation': peer.reputation_score
            }
            for peer in self.known_peers.values()
            if peer.state == NodeState.ACTIVE
        ]

        response = P2PMessage(
            message_id=f"discovery_resp_{secrets.token_hex(8)}",
            message_type=MessageType.PEER_ANNOUNCEMENT,
            sender_id=self.node_id,
            recipient_id=message.sender_id,
            payload={'peers': known_peer_list}
        )

        await self.send_message(response)

    async def _handle_peer_announcement(self, message: P2PMessage):
        """Handle peer announcement"""
        announced_peers = message.payload.get('peers', [])

        for peer_data in announced_peers:
            peer_id = peer_data['node_id']

            if peer_id not in self.known_peers and peer_id != self.node_id:
                self.known_peers[peer_id] = PeerInfo(
                    node_id=peer_id,
                    endpoint=peer_data['endpoint'],
                    last_seen=datetime.fromisoformat(peer_data['last_seen']) if peer_data.get('last_seen') else None,
                    reputation_score=peer_data.get('reputation', 0.5),
                    state=NodeState.CONNECTED
                )

                logger.debug(f"Discovered new peer: {peer_id}")

    async def _connect_to_bootstrap_peers(self):
        """Connect to bootstrap peers"""
        for bootstrap_peer in self.bootstrap_peers:
            try:
                # Send handshake to bootstrap peer
                handshake = P2PMessage(
                    message_id=f"handshake_{secrets.token_hex(8)}",
                    message_type=MessageType.HANDSHAKE,
                    sender_id=self.node_id,
                    payload={
                        'public_key': self.public_key_pem,
                        'protocols': ['p2p/v1', 'consensus/v1', 'data/v1']
                    }
                )

                # For bootstrap, we need to establish connection first
                # This is simplified - in production, you'd have a proper connection establishment
                logger.info(f"Attempting to connect to bootstrap peer: {bootstrap_peer}")

            except Exception as e:
                logger.warning(f"Failed to connect to bootstrap peer {bootstrap_peer}: {e}")

    async def _peer_discovery_loop(self):
        """Periodic peer discovery"""
        while self.is_running:
            try:
                # Send discovery requests to random peers
                active_peers = [p for p in self.known_peers.values() if p.state == NodeState.ACTIVE]

                if active_peers:
                    # Pick random peer to ask for discovery
                    discovery_peer = random.choice(active_peers)

                    discovery_request = P2PMessage(
                        message_id=f"discovery_{secrets.token_hex(8)}",
                        message_type=MessageType.PEER_DISCOVERY,
                        sender_id=self.node_id,
                        recipient_id=discovery_peer.node_id
                    )

                    await self.send_message(discovery_request)

                # Clean up stale peers
                current_time = datetime.now()
                stale_peers = []

                for peer_id, peer in self.known_peers.items():
                    if peer.last_seen and (current_time - peer.last_seen).total_seconds() > self.peer_timeout:
                        peer.state = NodeState.DISCONNECTED
                        stale_peers.append(peer_id)

                for peer_id in stale_peers:
                    logger.debug(f"Removed stale peer: {peer_id}")

                await asyncio.sleep(60)  # Discovery every minute

            except Exception as e:
                logger.error(f"Peer discovery error: {e}")
                await asyncio.sleep(30)

    async def _heartbeat_loop(self):
        """Periodic heartbeat to maintain connections"""
        while self.is_running:
            try:
                current_time = datetime.now()

                for peer in self.known_peers.values():
                    if peer.state == NodeState.ACTIVE:
                        # Send heartbeat
                        heartbeat = P2PMessage(
                            message_id=f"heartbeat_{secrets.token_hex(8)}",
                            message_type=MessageType.HEARTBEAT,
                            sender_id=self.node_id,
                            recipient_id=peer.node_id,
                            payload={'timestamp': current_time.isoformat()}
                        )

                        await self.send_message(heartbeat)

                await asyncio.sleep(self.heartbeat_interval)

            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(10)

    async def _announce_self(self):
        """Announce ourselves to the network"""
        announcement = P2PMessage(
            message_id=f"announce_{secrets.token_hex(8)}",
            message_type=MessageType.PEER_ANNOUNCEMENT,
            sender_id=self.node_id,
            payload={
                'peers': [{
                    'node_id': self.node_id,
                    'endpoint': f"127.0.0.1:{self.listen_port}",
                    'last_seen': datetime.now().isoformat(),
                    'reputation': 1.0
                }]
            }
        )

        await self.send_message(announcement)

    def get_network_status(self) -> Dict[str, Any]:
        """Get current network status"""
        return {
            'node_id': self.node_id,
            'listen_port': self.listen_port,
            'is_running': self.is_running,
            'known_peers': len(self.known_peers),
            'active_peers': len([p for p in self.known_peers.values() if p.state == NodeState.ACTIVE]),
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'bytes_sent': self.bytes_sent,
            'bytes_received': self.bytes_received,
            'public_key': self.public_key_pem[:50] + "..."  # Truncated for display
        }

    def get_peer_list(self) -> List[Dict[str, Any]]:
        """Get list of known peers"""
        return [
            {
                'node_id': peer.node_id,
                'endpoint': peer.endpoint,
                'state': peer.state.value,
                'latency_ms': peer.latency_ms,
                'reputation_score': peer.reputation_score,
                'last_seen': peer.last_seen.isoformat() if peer.last_seen else None
            }
            for peer in self.known_peers.values()
        ]

# Global P2P manager instance
p2p_manager_instance = None

def get_p2p_communication_manager(node_id: str, **kwargs) -> P2PCommunicationManager:
    """Get global P2P communication manager instance"""
    global p2p_manager_instance
    if p2p_manager_instance is None:
        p2p_manager_instance = P2PCommunicationManager(node_id, **kwargs)
    return p2p_manager_instance

if __name__ == '__main__':
    # Demo
    async def main():
        manager = get_p2p_communication_manager("demo_node_1", listen_port=8080)

        print("🌐 P2P Communication Manager Demo")
        print("=" * 50)

        # Start P2P communication
        await manager.start()
        print("✅ P2P communication started")

        try:
            # Show network status
            status = manager.get_network_status()
            print(f"📊 Network status: {status['known_peers']} known peers, {status['active_peers']} active")

            # Register a custom message handler
            async def custom_handler(message: P2PMessage):
                print(f"📨 Received custom message: {message.payload}")

            manager.register_message_handler(MessageType.DATA_REQUEST, custom_handler)
            print("✅ Custom message handler registered")

            # Send a test message (would need real peers to work)
            test_message = P2PMessage(
                message_id=f"test_{secrets.token_hex(8)}",
                message_type=MessageType.DATA_REQUEST,
                sender_id="demo_node_1",
                payload={'test': 'Hello P2P network!'}
            )

            print(f"📤 Sending test message: {test_message.message_id}")

            # Wait a bit
            await asyncio.sleep(5)

            # Show final status
            final_status = manager.get_network_status()
            print(f"📈 Final stats: {final_status['messages_sent']} sent, {final_status['messages_received']} received")

        finally:
            await manager.stop()
            print("⏹️ P2P communication stopped")

        print("🎉 P2P Communication Manager Demo completed!")

    asyncio.run(main())