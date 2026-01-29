"""
DHT Node Implementation (Kademlia) for Ailoos P2P
"""

import asyncio
import json
import logging
import secrets
from typing import Dict, Any, Optional, Callable
from .routing import RoutingTable, Node

logger = logging.getLogger(__name__)

class DHTProtocol(asyncio.DatagramProtocol):
    """UDP Protocol for DHT RPCs."""
    def __init__(self, node_id: bytes, routing_table: RoutingTable, store: Dict[str, str]):
        self.node_id = node_id
        self.routing_table = routing_table
        self.store = store
        self.transport = None
        self.pending_requests = {} # id -> future

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data: bytes, addr: tuple):
        try:
            msg = json.loads(data.decode())
            asyncio.create_task(self._handle_message(msg, addr))
        except Exception as e:
            logger.warning(f"Invalid DHT packet from {addr}: {e}")

    async def _handle_message(self, msg: Dict, addr: tuple):
        msg_type = msg.get('type')
        msg_id = msg.get('id')
        sender_id = bytes.fromhex(msg.get('sender_id', ''))
        
        # Update routing table
        self.routing_table.add_contact(Node(sender_id, addr[0], addr[1]))
        
        if msg_type == 'PING':
            self._send_response(addr, msg_id, {'type': 'PONG'})
            
        elif msg_type == 'STORE':
            key = msg.get('key')
            value = msg.get('value')
            if key and value:
                self.store[key] = value
                self._send_response(addr, msg_id, {'status': 'OK'})
                
        elif msg_type == 'FIND_NODE':
            target = bytes.fromhex(msg.get('target', ''))
            nearest = self.routing_table.find_nearest_nodes(target)
            nodes_data = [{'id': n.id.hex(), 'ip': n.ip, 'port': n.port} for n in nearest]
            self._send_response(addr, msg_id, {'nodes': nodes_data})
            
        elif msg_type == 'FIND_VALUE':
            key = msg.get('key')
            if key in self.store:
                self._send_response(addr, msg_id, {'value': self.store[key]})
            else:
                target = bytes.fromhex(key) # Key is hash
                nearest = self.routing_table.find_nearest_nodes(target)
                nodes_data = [{'id': n.id.hex(), 'ip': n.ip, 'port': n.port} for n in nearest]
                self._send_response(addr, msg_id, {'nodes': nodes_data})
                
        elif msg_type in ['PONG', 'RESPONSE']:
            if msg_id in self.pending_requests:
                self.pending_requests[msg_id].set_result(msg)
                del self.pending_requests[msg_id]

    def _send_response(self, addr: tuple, msg_id: str, payload: Dict):
        response = {'type': 'RESPONSE', 'id': msg_id, 'sender_id': self.node_id.hex()}
        response.update(payload)
        self.transport.sendto(json.dumps(response).encode(), addr)

    async def call_rpc(self, addr: tuple, method: str, payload: Dict, timeout=5.0) -> Dict:
        msg_id = secrets.token_hex(4)
        msg = {'type': method, 'id': msg_id, 'sender_id': self.node_id.hex()}
        msg.update(payload)
        
        future = asyncio.get_event_loop().create_future()
        self.pending_requests[msg_id] = future
        
        self.transport.sendto(json.dumps(msg).encode(), addr)
        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            if msg_id in self.pending_requests:
                del self.pending_requests[msg_id]
            raise

class DHTNode:
    """High-level DHT Node."""
    def __init__(self, port: int = 9000):
        self.id = secrets.token_bytes(20) # 160 bits
        self.port = port
        self.routing = RoutingTable(self.id)
        self.storage = {}
        self.protocol = None
        self.transport = None

    async def start(self):
        loop = asyncio.get_running_loop()
        listen = loop.create_datagram_endpoint(
            lambda: DHTProtocol(self.id, self.routing, self.storage),
            local_addr=('0.0.0.0', self.port)
        )
        self.transport, self.protocol = await listen
        logger.info(f"🕸️ DHT Node started on port {self.port} (ID: {self.id.hex()[:6]})")

    async def bootstrap(self, peers: list):
        """Join network via known peers [(ip, port), ...]."""
        for ip, port in peers:
            try:
                # Ping to check liveness
                await self.protocol.call_rpc((ip, port), 'PING', {})
                # Find ourselves to populate routing table
                await self.protocol.call_rpc((ip, port), 'FIND_NODE', {'target': self.id.hex()})
            except Exception as e:
                logger.debug(f"Bootstrap failed for {ip}:{port}: {e}")

    async def put(self, key: str, value: str):
        """Store value in the network."""
        key_hash = bytes.fromhex(key) if len(key) == 40 else secrets.token_bytes(20) # Mock hash
        # 1. Find K closest nodes
        # 2. Store on them
        # Simplified: Store locally and announce (Gossip/Flooding in real impl)
        self.storage[key] = value
        logger.info(f"Stored {key} locally.")

    async def get(self, key: str) -> Optional[str]:
        """Retrieve value from network."""
        return self.storage.get(key)
        
        if self.transport:
            self.transport.close()

    def get_peer_count(self) -> int:
        """Returns total number of known peers in routing table."""
        count = 0
        for bucket in self.routing.buckets:
            count += len(bucket.get_nodes())
        return count
