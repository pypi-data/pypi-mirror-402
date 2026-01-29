"""
AILOOS Networking Module

This module provides networking functionality for AILOOS distributed system.
"""

# IPFS Optimization - FASE 4.3
from .ipfs_optimizer import (
    IPFSClusterManager, IPFSNode, PinningStrategy, IPFSNodeStatus,
    ContentPin, IPFSHealthMonitor, BandwidthOptimizer,
    create_global_ipfs_cluster, initialize_ipfs_cluster,
    demonstrate_ipfs_optimization
)

# P2P Network Improvements - FASE 4.3
from .p2p_optimizer import (
    P2PConnectionManager, P2PConnection, ConnectionState,
    NATTraversalManager, NATTraversalMethod, ConnectionMultiplexer,
    MultiplexedChannel, BandwidthThrottler, ConnectionPool,
    initialize_p2p_network, demonstrate_p2p_improvements
)

__all__ = [
    # IPFS Optimization
    'IPFSClusterManager',
    'IPFSNode',
    'PinningStrategy',
    'IPFSNodeStatus',
    'ContentPin',
    'IPFSHealthMonitor',
    'BandwidthOptimizer',
    'create_global_ipfs_cluster',
    'initialize_ipfs_cluster',
    'demonstrate_ipfs_optimization',
    # P2P Network Improvements
    'P2PConnectionManager',
    'P2PConnection',
    'ConnectionState',
    'NATTraversalManager',
    'NATTraversalMethod',
    'ConnectionMultiplexer',
    'MultiplexedChannel',
    'BandwidthThrottler',
    'ConnectionPool',
    'initialize_p2p_network',
    'demonstrate_p2p_improvements'
]

__version__ = "1.0.0"