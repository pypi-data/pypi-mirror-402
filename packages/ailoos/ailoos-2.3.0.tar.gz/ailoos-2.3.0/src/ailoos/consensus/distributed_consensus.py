#!/usr/bin/env python3
"""
Distributed Consensus System for Ailoos
Implementa algoritmos de consenso distribuido con tolerancia a fallos bizantinos
"""

import asyncio
import logging
import hashlib
import json
import time
import random
from typing import Dict, List, Any, Optional, Tuple, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import aiohttp
from collections import defaultdict, Counter
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConsensusAlgorithm(Enum):
    """Algoritmos de consenso disponibles"""
    PBFT = "pbft"                    # Practical Byzantine Fault Tolerance
    RAFT = "raft"                    # Raft consensus
    PROOF_OF_WORK = "pow"           # Proof of Work
    PROOF_OF_STAKE = "pos"          # Proof of Stake
    DELEGATED_POS = "dpos"          # Delegated Proof of Stake
    HOTSTUFF = "hotstuff"           # HotStuff BFT

class ConsensusPhase(Enum):
    """Fases del consenso"""
    PRE_PREPARE = "pre_prepare"
    PREPARE = "prepare"
    COMMIT = "commit"
    DECIDE = "decide"

class NodeRole(Enum):
    """Roles de nodos en el consenso"""
    LEADER = "leader"
    VALIDATOR = "validator"
    FOLLOWER = "follower"
    CANDIDATE = "candidate"

@dataclass
class ConsensusMessage:
    """Mensaje de consenso"""
    message_id: str
    algorithm: ConsensusAlgorithm
    phase: ConsensusPhase
    sender_id: str
    round_number: int
    proposal_id: str
    proposal_data: Any
    signature: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    view_number: int = 0

@dataclass
class ConsensusProposal:
    """Propuesta de consenso"""
    proposal_id: str
    proposer_id: str
    data: Any
    timestamp: datetime
    signatures: Dict[str, str] = field(default_factory=dict)  # node_id -> signature
    status: str = "proposed"  # proposed, accepted, rejected, committed

@dataclass
class ConsensusState:
    """Estado del consenso"""
    current_view: int = 0
    current_round: int = 0
    leader_id: Optional[str] = None
    active_proposals: Dict[str, ConsensusProposal] = field(default_factory=dict)
    committed_proposals: List[ConsensusProposal] = field(default_factory=list)
    node_states: Dict[str, NodeRole] = field(default_factory=dict)
    last_heartbeat: Dict[str, datetime] = field(default_factory=dict)

class PBFTConsensus:
    """
    Implementación de Practical Byzantine Fault Tolerance (PBFT)
    """

    def __init__(self, node_id: str, total_nodes: int, fault_tolerance: int = None):
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.fault_tolerance = fault_tolerance or (total_nodes - 1) // 3

        # PBFT state
        self.view_number = 0
        self.sequence_number = 0
        self.last_executed = 0

        # Message logs
        self.pre_prepare_log: Dict[int, ConsensusMessage] = {}
        self.prepare_log: Dict[Tuple[int, int], List[ConsensusMessage]] = defaultdict(list)
        self.commit_log: Dict[Tuple[int, int], List[ConsensusMessage]] = defaultdict(list)

        # Certificates
        self.prepared_certificates: Set[Tuple[int, int]] = set()
        self.committed_certificates: Set[Tuple[int, int]] = set()

        logger.info(f"🏛️ PBFT Consensus initialized for node {node_id} (f={self.fault_tolerance})")

    def is_leader(self, view: int) -> bool:
        """Check if this node is the leader for the given view"""
        return (view % self.total_nodes) == (int(self.node_id.split('_')[-1]) % self.total_nodes)

    async def propose_request(self, request_data: Any) -> Optional[ConsensusProposal]:
        """Propose a new request for consensus"""
        if not self.is_leader(self.view_number):
            return None

        proposal = ConsensusProposal(
            proposal_id=f"proposal_{self.node_id}_{self.sequence_number}_{int(time.time())}",
            proposer_id=self.node_id,
            data=request_data,
            timestamp=datetime.now()
        )

        # Create PRE-PREPARE message
        pre_prepare_msg = ConsensusMessage(
            message_id=f"pre_prepare_{proposal.proposal_id}",
            algorithm=ConsensusAlgorithm.PBFT,
            phase=ConsensusPhase.PRE_PREPARE,
            sender_id=self.node_id,
            round_number=self.sequence_number,
            proposal_id=proposal.proposal_id,
            proposal_data=request_data,
            view_number=self.view_number
        )

        self.sequence_number += 1
        self.pre_prepare_log[self.sequence_number] = pre_prepare_msg

        logger.info(f"📤 PBFT: Proposed request {proposal.proposal_id}")
        return proposal

    async def handle_pre_prepare(self, message: ConsensusMessage) -> Optional[ConsensusMessage]:
        """Handle PRE-PREPARE message"""
        # Validate message
        if message.view_number != self.view_number:
            return None

        # Store in log
        self.pre_prepare_log[message.round_number] = message

        # Send PREPARE message
        prepare_msg = ConsensusMessage(
            message_id=f"prepare_{message.proposal_id}_{self.node_id}",
            algorithm=ConsensusAlgorithm.PBFT,
            phase=ConsensusPhase.PREPARE,
            sender_id=self.node_id,
            round_number=message.round_number,
            proposal_id=message.proposal_id,
            proposal_data=message.proposal_data,
            view_number=self.view_number
        )

        logger.debug(f"📤 PBFT: Sent PREPARE for {message.proposal_id}")
        return prepare_msg

    async def handle_prepare(self, message: ConsensusMessage) -> Optional[ConsensusMessage]:
        """Handle PREPARE message"""
        key = (message.view_number, message.round_number)

        # Store prepare message
        self.prepare_log[key].append(message)

        # Check if we have 2f+1 prepares (including our own)
        if len(self.prepare_log[key]) >= (2 * self.fault_tolerance + 1):
            # Mark as prepared
            self.prepared_certificates.add(key)

            # Send COMMIT message
            commit_msg = ConsensusMessage(
                message_id=f"commit_{message.proposal_id}_{self.node_id}",
                algorithm=ConsensusAlgorithm.PBFT,
                phase=ConsensusPhase.COMMIT,
                sender_id=self.node_id,
                round_number=message.round_number,
                proposal_id=message.proposal_id,
                proposal_data=message.proposal_data,
                view_number=self.view_number
            )

            logger.debug(f"📤 PBFT: Sent COMMIT for {message.proposal_id}")
            return commit_msg

        return None

    async def handle_commit(self, message: ConsensusMessage) -> Optional[ConsensusMessage]:
        """Handle COMMIT message"""
        key = (message.view_number, message.round_number)

        # Store commit message
        self.commit_log[key].append(message)

        # Check if we have 2f+1 commits
        if len(self.commit_log[key]) >= (2 * self.fault_tolerance + 1):
            # Mark as committed
            self.committed_certificates.add(key)

            # Execute the request
            await self._execute_request(message.proposal_data)

            # Send DECIDE message
            decide_msg = ConsensusMessage(
                message_id=f"decide_{message.proposal_id}_{self.node_id}",
                algorithm=ConsensusAlgorithm.PBFT,
                phase=ConsensusPhase.DECIDE,
                sender_id=self.node_id,
                round_number=message.round_number,
                proposal_id=message.proposal_id,
                proposal_data=message.proposal_data,
                view_number=self.view_number
            )

            logger.info(f"✅ PBFT: Consensus reached for {message.proposal_id}")
            return decide_msg

        return None

    async def _execute_request(self, request_data: Any):
        """Execute the agreed-upon request"""
        # This would be implemented based on the specific application
        logger.info(f"⚡ Executing request: {request_data}")

class RaftConsensus:
    """
    Implementación simplificada del algoritmo Raft
    """

    def __init__(self, node_id: str, cluster_nodes: List[str]):
        self.node_id = node_id
        self.cluster_nodes = cluster_nodes
        self.total_nodes = len(cluster_nodes)

        # Raft state
        self.current_term = 0
        self.voted_for: Optional[str] = None
        self.log: List[Dict[str, Any]] = []
        self.commit_index = 0
        self.last_applied = 0

        # Leader state
        self.next_index: Dict[str, int] = {}
        self.match_index: Dict[str, int] = {}

        # Election timeout
        self.election_timeout = random.uniform(1.0, 2.0)
        self.last_heartbeat = time.time()

        # Role
        self.role = NodeRole.FOLLOWER

        logger.info(f"⚖️ Raft Consensus initialized for node {node_id}")

    async def start_election(self):
        """Start leader election"""
        self.current_term += 1
        self.role = NodeRole.CANDIDATE
        self.voted_for = self.node_id

        votes_received = 1  # Vote for self

        # Request votes from other nodes
        vote_requests = []
        for node in self.cluster_nodes:
            if node != self.node_id:
                # In real implementation, send vote request messages
                vote_requests.append(self._request_vote_from_node(node))

        # Wait for responses (simplified)
        results = await asyncio.gather(*vote_requests, return_exceptions=True)

        for result in results:
            if not isinstance(result, Exception) and result.get('vote_granted', False):
                votes_received += 1

        # Check if we have majority
        if votes_received > self.total_nodes // 2:
            await self.become_leader()
        else:
            self.role = NodeRole.FOLLOWER

    async def _request_vote_from_node(self, node_id: str) -> Dict[str, Any]:
        """Request vote from a specific node"""
        # Simplified - in real implementation would send network message
        await asyncio.sleep(random.uniform(0.1, 0.5))  # Simulate network delay

        # Random vote (simplified)
        return {'vote_granted': random.choice([True, False])}

    async def become_leader(self):
        """Become the leader"""
        self.role = NodeRole.LEADER

        # Initialize leader state
        for node in self.cluster_nodes:
            if node != self.node_id:
                self.next_index[node] = len(self.log)
                self.match_index[node] = 0

        logger.info(f"👑 Node {self.node_id} became leader for term {self.current_term}")

        # Start sending heartbeats
        asyncio.create_task(self._send_heartbeats())

    async def _send_heartbeats(self):
        """Send periodic heartbeats to followers"""
        while self.role == NodeRole.LEADER:
            await asyncio.sleep(0.1)  # Heartbeat interval

            for node in self.cluster_nodes:
                if node != self.node_id:
                    # Send heartbeat (simplified)
                    pass

    async def append_entries(self, entries: List[Dict[str, Any]]) -> bool:
        """Append entries to log (leader operation)"""
        if self.role != NodeRole.LEADER:
            return False

        # Append to local log
        for entry in entries:
            self.log.append({
                'term': self.current_term,
                'command': entry,
                'timestamp': datetime.now()
            })

        # Replicate to followers (simplified)
        success_count = 1  # Self

        for node in self.cluster_nodes:
            if node != self.node_id:
                # Send append entries RPC
                if await self._send_append_entries_to_node(node, entries):
                    success_count += 1

        # Check if majority replicated
        return success_count > self.total_nodes // 2

    async def _send_append_entries_to_node(self, node_id: str, entries: List[Dict[str, Any]]) -> bool:
        """Send append entries to a specific node"""
        # Simplified implementation
        await asyncio.sleep(random.uniform(0.05, 0.2))  # Simulate network delay
        return random.choice([True, True, True, False])  # 75% success rate

class ProofOfStakeConsensus:
    """
    Implementación de Proof of Stake
    """

    def __init__(self, node_id: str, stake_amount: float):
        self.node_id = node_id
        self.stake_amount = stake_amount
        self.total_network_stake = 1000000.0  # Would be dynamic in real network

        # PoS state
        self.selected_validators: List[str] = []
        self.epoch = 0
        self.blocks_proposed = 0

        logger.info(f"🔐 PoS Consensus initialized for node {node_id} (stake: {stake_amount})")

    def calculate_selection_probability(self) -> float:
        """Calculate probability of being selected as validator"""
        return self.stake_amount / self.total_network_stake

    async def try_propose_block(self, block_data: Any) -> bool:
        """Try to propose a new block"""
        selection_prob = self.calculate_selection_probability()

        # Simulate selection based on stake
        if random.random() < selection_prob:
            self.blocks_proposed += 1
            logger.info(f"📦 Block proposed by {self.node_id} (stake-weighted selection)")
            return True

        return False

class DistributedConsensusManager:
    """
    Gestor de consenso distribuido con múltiples algoritmos
    """

    def __init__(self, node_id: str, algorithm: ConsensusAlgorithm = ConsensusAlgorithm.PBFT):
        self.node_id = node_id
        self.algorithm = algorithm

        # Consensus instances
        self.consensus_instances: Dict[ConsensusAlgorithm, Any] = {}

        # Network state
        self.known_nodes: Set[str] = set()
        self.consensus_state = ConsensusState()

        # Message queues
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.pending_proposals: Dict[str, ConsensusProposal] = {}

        # Callbacks
        self.consensus_callbacks: Dict[str, List[Callable]] = {
            'proposal_accepted': [],
            'consensus_reached': [],
            'leader_changed': [],
            'view_changed': []
        }

        # Initialize consensus algorithm
        self._initialize_consensus_algorithm()

        logger.info(f"🎯 Distributed Consensus Manager initialized with {algorithm.value}")

    def _initialize_consensus_algorithm(self):
        """Initialize the selected consensus algorithm"""
        if self.algorithm == ConsensusAlgorithm.PBFT:
            # Assume 4 nodes for demo, f=1 fault tolerance
            self.consensus_instances[self.algorithm] = PBFTConsensus(self.node_id, 4)
        elif self.algorithm == ConsensusAlgorithm.RAFT:
            # Assume cluster of 5 nodes
            cluster_nodes = [f"node_{i}" for i in range(5)]
            self.consensus_instances[self.algorithm] = RaftConsensus(self.node_id, cluster_nodes)
        elif self.algorithm == ConsensusAlgorithm.PROOF_OF_STAKE:
            # Random stake amount
            stake = random.uniform(1000, 10000)
            self.consensus_instances[self.algorithm] = ProofOfStakeConsensus(self.node_id, stake)

    def register_callback(self, event: str, callback: Callable):
        """Register callback for consensus events"""
        if event in self.consensus_callbacks:
            self.consensus_callbacks[event].append(callback)

    async def propose_value(self, value: Any) -> Optional[str]:
        """Propose a value for consensus"""
        proposal_id = f"proposal_{self.node_id}_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"

        proposal = ConsensusProposal(
            proposal_id=proposal_id,
            proposer_id=self.node_id,
            data=value,
            timestamp=datetime.now()
        )

        self.pending_proposals[proposal_id] = proposal

        # Send to consensus algorithm
        consensus_instance = self.consensus_instances.get(self.algorithm)
        if consensus_instance:
            if hasattr(consensus_instance, 'propose_request'):
                result = await consensus_instance.propose_request(value)
                if result:
                    await self._trigger_callbacks('proposal_accepted', proposal)
                    return proposal_id

        return None

    async def handle_consensus_message(self, message: ConsensusMessage):
        """Handle incoming consensus message"""
        consensus_instance = self.consensus_instances.get(message.algorithm)

        if not consensus_instance:
            logger.warning(f"No consensus instance for algorithm {message.algorithm}")
            return

        response = None

        # Route to appropriate handler
        if message.phase == ConsensusPhase.PRE_PREPARE:
            if hasattr(consensus_instance, 'handle_pre_prepare'):
                response = await consensus_instance.handle_pre_prepare(message)
        elif message.phase == ConsensusPhase.PREPARE:
            if hasattr(consensus_instance, 'handle_prepare'):
                response = await consensus_instance.handle_prepare(message)
        elif message.phase == ConsensusPhase.COMMIT:
            if hasattr(consensus_instance, 'handle_commit'):
                response = await consensus_instance.handle_commit(message)

        # Send response if any
        if response:
            await self._send_consensus_message(response)

    async def _send_consensus_message(self, message: ConsensusMessage):
        """Send consensus message to other nodes"""
        # In real implementation, this would send to network
        logger.debug(f"📤 Consensus message: {message.phase.value} for {message.proposal_id}")

        # Simulate network by putting in queue for processing
        await self.message_queue.put(message)

    async def _trigger_callbacks(self, event: str, *args, **kwargs):
        """Trigger consensus callbacks"""
        for callback in self.consensus_callbacks[event]:
            try:
                await callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Consensus callback error: {e}")

    def get_consensus_status(self) -> Dict[str, Any]:
        """Get current consensus status"""
        consensus_instance = self.consensus_instances.get(self.algorithm)

        status = {
            'algorithm': self.algorithm.value,
            'node_id': self.node_id,
            'pending_proposals': len(self.pending_proposals),
            'known_nodes': len(self.known_nodes),
            'current_view': self.consensus_state.current_view,
            'leader_id': self.consensus_state.leader_id
        }

        # Add algorithm-specific status
        if consensus_instance:
            if hasattr(consensus_instance, 'view_number'):
                status['view_number'] = consensus_instance.view_number
            if hasattr(consensus_instance, 'current_term'):
                status['current_term'] = consensus_instance.current_term
            if hasattr(consensus_instance, 'role'):
                status['role'] = consensus_instance.role.value if hasattr(consensus_instance.role, 'value') else str(consensus_instance.role)

        return status

    async def start_consensus_round(self):
        """Start a new consensus round"""
        self.consensus_state.current_round += 1

        # Select new leader if needed
        if self.algorithm == ConsensusAlgorithm.RAFT:
            consensus_instance = self.consensus_instances.get(self.algorithm)
            if consensus_instance and consensus_instance.role == NodeRole.FOLLOWER:
                # Check if election timeout
                if time.time() - consensus_instance.last_heartbeat > consensus_instance.election_timeout:
                    await consensus_instance.start_election()

    async def validate_proposal(self, proposal: ConsensusProposal) -> bool:
        """Validate a consensus proposal"""
        # Basic validation
        if not proposal.proposal_id or not proposal.data:
            return False

        # Check timestamp (not too old)
        if (datetime.now() - proposal.timestamp).total_seconds() > 300:  # 5 minutes
            return False

        # Algorithm-specific validation
        consensus_instance = self.consensus_instances.get(self.algorithm)
        if consensus_instance and hasattr(consensus_instance, 'validate_proposal'):
            return await consensus_instance.validate_proposal(proposal)

        return True

# Global consensus manager instance
consensus_manager_instance = None

def get_distributed_consensus_manager(node_id: str, **kwargs) -> DistributedConsensusManager:
    """Get global distributed consensus manager instance"""
    global consensus_manager_instance
    if consensus_manager_instance is None:
        consensus_manager_instance = DistributedConsensusManager(node_id, **kwargs)
    return consensus_manager_instance

if __name__ == '__main__':
    # Demo
    async def main():
        manager = get_distributed_consensus_manager("demo_node_1", algorithm=ConsensusAlgorithm.PBFT)

        print("🎯 Distributed Consensus Demo")
        print("=" * 50)

        # Show status
        status = manager.get_consensus_status()
        print(f"📊 Consensus status: {status['algorithm']} algorithm, node {status['node_id']}")

        # Propose a value
        proposal_id = await manager.propose_value({"action": "update_config", "key": "timeout", "value": 30})
        if proposal_id:
            print(f"📤 Proposed value with ID: {proposal_id}")
        else:
            print("❌ Failed to propose value")

        # Simulate consensus message handling
        message = ConsensusMessage(
            message_id="test_msg_1",
            algorithm=ConsensusAlgorithm.PBFT,
            phase=ConsensusPhase.PRE_PREPARE,
            sender_id="demo_node_2",
            round_number=1,
            proposal_id="test_proposal",
            proposal_data={"test": "data"}
        )

        await manager.handle_consensus_message(message)
        print("📨 Handled consensus message")

        print("🎉 Distributed Consensus Demo completed!")

    asyncio.run(main())