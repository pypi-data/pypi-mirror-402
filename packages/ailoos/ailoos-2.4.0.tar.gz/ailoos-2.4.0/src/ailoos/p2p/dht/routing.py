"""
Kademlia Routing Table Implementation for Ailoos P2P
"""

import time
import heapq
import logging
from collections import OrderedDict
from typing import List, Tuple

logger = logging.getLogger(__name__)

# Kademlia constants
K = 20  # Bucket size
ALPHA = 3  # Concurrency parameter
ID_BITS = 160  # SHA-1 hash size for node IDs

class Node:
    """Represents a node in the DHT network."""
    def __init__(self, node_id: bytes, ip: str, port: int):
        self.id = node_id
        self.ip = ip
        self.port = port
        self.last_seen = time.time()
        
    def distance_to(self, other_id: bytes) -> int:
        """XOR distance metric."""
        return int.from_bytes(self.id, 'big') ^ int.from_bytes(other_id, 'big')

    def __repr__(self):
        return f"<Node {self.id.hex()[:6]}... {self.ip}:{self.port}>"
        
    def __eq__(self, other):
        return self.id == other.id

class KBucket:
    """
    A bucket in the Kademlia routing table.
    Stores up to K nodes, sorted by last seen time (least recently seen at head).
    """
    def __init__(self, k=K):
        self.k = k
        self.nodes = OrderedDict() # ID -> Node
        self.last_updated = time.time()

    def add_node(self, node: Node):
        """Update node in bucket (move to tail) or add if space exists."""
        if node.id in self.nodes:
            del self.nodes[node.id]
            self.nodes[node.id] = node
        elif len(self.nodes) < self.k:
            self.nodes[node.id] = node
        else:
            # Bucket is full - in a real impl we would ping the head (LRU)
            # here we just drop the new one for simplicity or assume head is stale?
            # Standard Kademlia: Ping head. If dead, replace. If alive, discard new.
            # We'll assume strict LRU for now without pinging here.
            pass
        self.last_updated = time.time()

    def get_nodes(self) -> List[Node]:
        return list(self.nodes.values())

class RoutingTable:
    """
    The Kademlia Routing Table.
    Organizes nodes into buckets based on distance from local node.
    """
    def __init__(self, local_node_id: bytes):
        self.local_node_id = local_node_id
        self.buckets = [KBucket() for _ in range(ID_BITS)]

    def _get_bucket_index(self, node_id: bytes) -> int:
        """Returns the index of the bucket for a given node ID."""
        distance = int.from_bytes(self.local_node_id, 'big') ^ int.from_bytes(node_id, 'big')
        return distance.bit_length() - 1 if distance > 0 else 0

    def add_contact(self, node: Node):
        """Add a contact to the routing table."""
        if node.id == self.local_node_id:
            return
        index = self._get_bucket_index(node.id)
        self.buckets[index].add_node(node)

    def find_nearest_nodes(self, target_id: bytes, limit=K) -> List[Node]:
        """Finds the K nearest nodes to target_id."""
        all_nodes = []
        for bucket in self.buckets:
            all_nodes.extend(bucket.get_nodes())
            
        # Sort by XOR distance
        all_nodes.sort(key=lambda n: n.distance_to(target_id))
        return all_nodes[:limit]
