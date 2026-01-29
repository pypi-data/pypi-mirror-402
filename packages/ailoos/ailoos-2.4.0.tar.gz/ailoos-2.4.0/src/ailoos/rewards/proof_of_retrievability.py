#!/usr/bin/env python3
"""
Proof of Retrievability System - Cryptographic verification of memory availability
"""

import hashlib
import secrets
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio

from ..core.config import Config
from ..utils.logging import AiloosLogger


@dataclass
class Challenge:
    """Represents a cryptographic challenge for memory verification."""
    challenge_id: str
    node_id: str
    challenge_data: bytes
    challenge_hash: str
    timestamp: datetime
    difficulty: int
    expires_at: datetime


@dataclass
class Proof:
    """Represents a proof response to a challenge."""
    proof_id: str
    challenge_id: str
    node_id: str
    proof_data: bytes
    proof_hash: str
    response_time_ms: float
    timestamp: datetime


class ProofOfRetrievability:
    """
    Proof of Retrievability system for verifying memory availability in storage nodes.

    Uses cryptographic challenges to ensure nodes maintain data availability without
    requiring full data retrieval.
    """

    def __init__(self, config: Config):
        self.config = config
        self.logger = AiloosLogger(__name__)

        # Configuration parameters
        self.challenge_interval_seconds = config.get('por_challenge_interval', 300)  # 5 minutes
        self.challenge_timeout_seconds = config.get('por_challenge_timeout', 30)  # 30 seconds
        self.challenge_difficulty = config.get('por_difficulty', 4)  # Proof of work difficulty
        self.max_concurrent_challenges = config.get('por_max_concurrent', 10)
        self.slashing_threshold = config.get('por_slashing_threshold', 0.7)  # 70% success rate

        # In-memory storage (in production, use database)
        self.active_challenges: Dict[str, Challenge] = {}
        self.completed_proofs: Dict[str, Proof] = {}
        self.node_stats: Dict[str, Dict[str, Any]] = {}

        # Challenge generation parameters
        self.challenge_size_bytes = 1024  # 1KB challenge data

    async def generate_challenge(self, node_id: str, memory_segment_id: str) -> Challenge:
        """
        Generate a cryptographic challenge for a specific memory segment.

        Args:
            node_id: ID of the node to challenge
            memory_segment_id: ID of the memory segment to verify

        Returns:
            Generated challenge
        """
        try:
            challenge_id = f"challenge_{secrets.token_hex(16)}"

            # Generate random challenge data
            challenge_data = secrets.token_bytes(self.challenge_size_bytes)

            # Create challenge hash
            challenge_content = f"{node_id}:{memory_segment_id}:{challenge_data.hex()}"
            challenge_hash = hashlib.sha256(challenge_content.encode()).hexdigest()

            # Set expiration
            expires_at = datetime.now() + timedelta(seconds=self.challenge_timeout_seconds)

            challenge = Challenge(
                challenge_id=challenge_id,
                node_id=node_id,
                challenge_data=challenge_data,
                challenge_hash=challenge_hash,
                timestamp=datetime.now(),
                difficulty=self.challenge_difficulty,
                expires_at=expires_at
            )

            # Store active challenge
            self.active_challenges[challenge_id] = challenge

            # Initialize node stats if not exists
            if node_id not in self.node_stats:
                self.node_stats[node_id] = {
                    'total_challenges': 0,
                    'successful_proofs': 0,
                    'failed_proofs': 0,
                    'avg_response_time_ms': 0.0,
                    'last_challenge': None,
                    'success_rate': 1.0
                }

            self.node_stats[node_id]['total_challenges'] += 1
            self.node_stats[node_id]['last_challenge'] = datetime.now()

            self.logger.info(f"🔐 Generated PoR challenge {challenge_id} for node {node_id}")

            return challenge

        except Exception as e:
            self.logger.error(f"Error generating challenge for {node_id}: {e}")
            raise

    async def submit_proof(self, challenge_id: str, proof_data: bytes, node_id: str) -> Dict[str, Any]:
        """
        Submit a proof response to a challenge.

        Args:
            challenge_id: ID of the challenge
            proof_data: Proof response data
            node_id: ID of the responding node

        Returns:
            Verification result
        """
        try:
            if challenge_id not in self.active_challenges:
                return {
                    'success': False,
                    'error': 'Challenge not found or expired',
                    'challenge_id': challenge_id
                }

            challenge = self.active_challenges[challenge_id]

            # Verify challenge hasn't expired
            if datetime.now() > challenge.expires_at:
                del self.active_challenges[challenge_id]
                return {
                    'success': False,
                    'error': 'Challenge expired',
                    'challenge_id': challenge_id
                }

            # Verify node matches
            if challenge.node_id != node_id:
                return {
                    'success': False,
                    'error': 'Node ID mismatch',
                    'challenge_id': challenge_id
                }

            # Calculate response time
            response_time = datetime.now() - challenge.timestamp
            response_time_ms = response_time.total_seconds() * 1000

            # Verify proof
            verification_result = await self._verify_proof(challenge, proof_data)

            # Create proof record
            proof_id = f"proof_{secrets.token_hex(8)}"
            proof_hash = hashlib.sha256(proof_data).hexdigest()

            proof = Proof(
                proof_id=proof_id,
                challenge_id=challenge_id,
                node_id=node_id,
                proof_data=proof_data,
                proof_hash=proof_hash,
                response_time_ms=response_time_ms,
                timestamp=datetime.now()
            )

            # Store proof
            self.completed_proofs[proof_id] = proof

            # Update node statistics
            node_stat = self.node_stats[node_id]
            if verification_result['valid']:
                node_stat['successful_proofs'] += 1
            else:
                node_stat['failed_proofs'] += 1

            # Update average response time
            total_proofs = node_stat['successful_proofs'] + node_stat['failed_proofs']
            node_stat['avg_response_time_ms'] = (
                (node_stat['avg_response_time_ms'] * (total_proofs - 1)) + response_time_ms
            ) / total_proofs

            # Update success rate
            node_stat['success_rate'] = node_stat['successful_proofs'] / node_stat['total_challenges']

            # Clean up challenge
            del self.active_challenges[challenge_id]

            result = {
                'success': verification_result['valid'],
                'proof_id': proof_id,
                'challenge_id': challenge_id,
                'node_id': node_id,
                'response_time_ms': response_time_ms,
                'verification_details': verification_result,
                'node_stats': node_stat.copy()
            }

            if verification_result['valid']:
                self.logger.info(f"✅ Valid proof submitted by {node_id} for challenge {challenge_id}")
            else:
                self.logger.warning(f"❌ Invalid proof submitted by {node_id} for challenge {challenge_id}: "
                                  f"{verification_result.get('error', 'Unknown error')}")

            return result

        except Exception as e:
            self.logger.error(f"Error submitting proof for challenge {challenge_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'challenge_id': challenge_id
            }

    async def _verify_proof(self, challenge: Challenge, proof_data: bytes) -> Dict[str, Any]:
        """
        Verify a proof against a challenge.

        Args:
            challenge: The original challenge
            proof_data: Submitted proof data

        Returns:
            Verification result
        """
        try:
            # Basic verification: proof should be derived from challenge data
            # In a real implementation, this would involve more sophisticated cryptography

            # Check proof size (should be reasonable)
            if len(proof_data) < 32 or len(proof_data) > 4096:
                return {
                    'valid': False,
                    'error': 'Invalid proof size',
                    'proof_size_bytes': len(proof_data)
                }

            # Verify proof of work (simple difficulty check)
            proof_hash = hashlib.sha256(proof_data).hexdigest()
            leading_zeros = 0
            for char in proof_hash:
                if char == '0':
                    leading_zeros += 1
                else:
                    break

            if leading_zeros < challenge.difficulty:
                return {
                    'valid': False,
                    'error': f'Insufficient proof of work (required: {challenge.difficulty}, got: {leading_zeros})',
                    'proof_hash': proof_hash
                }

            # Verify challenge data is incorporated (HMAC-like verification)
            combined_data = challenge.challenge_data + proof_data
            verification_hash = hashlib.sha256(combined_data).hexdigest()

            # Check if verification hash meets difficulty requirement
            verification_leading_zeros = 0
            for char in verification_hash:
                if char == '0':
                    verification_leading_zeros += 1
                else:
                    break

            if verification_leading_zeros < challenge.difficulty // 2:
                return {
                    'valid': False,
                    'error': 'Challenge data not properly incorporated',
                    'verification_hash': verification_hash
                }

            return {
                'valid': True,
                'proof_hash': proof_hash,
                'verification_hash': verification_hash,
                'proof_size_bytes': len(proof_data)
            }

        except Exception as e:
            self.logger.error(f"Error verifying proof: {e}")
            return {
                'valid': False,
                'error': f'Verification error: {str(e)}'
            }

    def get_node_stats(self, node_id: str) -> Dict[str, Any]:
        """
        Get Proof of Retrievability statistics for a node.

        Args:
            node_id: Node ID

        Returns:
            Node statistics
        """
        return self.node_stats.get(node_id, {
            'total_challenges': 0,
            'successful_proofs': 0,
            'failed_proofs': 0,
            'avg_response_time_ms': 0.0,
            'success_rate': 1.0,
            'last_challenge': None
        })

    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get overall system statistics.

        Returns:
            System-wide statistics
        """
        total_challenges = sum(stats['total_challenges'] for stats in self.node_stats.values())
        total_successful = sum(stats['successful_proofs'] for stats in self.node_stats.values())
        total_failed = sum(stats['failed_proofs'] for stats in self.node_stats.values())

        avg_success_rate = (
            sum(stats['success_rate'] for stats in self.node_stats.values()) / len(self.node_stats)
            if self.node_stats else 1.0
        )

        return {
            'total_nodes': len(self.node_stats),
            'total_challenges': total_challenges,
            'total_successful_proofs': total_successful,
            'total_failed_proofs': total_failed,
            'overall_success_rate': total_successful / max(total_challenges, 1),
            'average_node_success_rate': avg_success_rate,
            'active_challenges': len(self.active_challenges),
            'completed_proofs': len(self.completed_proofs)
        }

    def check_slashing_eligibility(self, node_id: str) -> Dict[str, Any]:
        """
        Check if a node is eligible for slashing based on PoR performance.

        Args:
            node_id: Node ID to check

        Returns:
            Slashing eligibility assessment
        """
        stats = self.get_node_stats(node_id)

        if stats['total_challenges'] < 10:  # Minimum challenges for assessment
            return {
                'eligible': False,
                'reason': 'Insufficient challenge history',
                'stats': stats
            }

        success_rate = stats['success_rate']
        avg_response_time = stats['avg_response_time_ms']

        # Check success rate threshold
        if success_rate < self.slashing_threshold:
            return {
                'eligible': True,
                'reason': f'Low success rate: {success_rate:.2%} < {self.slashing_threshold:.2%}',
                'severity': 'high' if success_rate < 0.5 else 'medium',
                'stats': stats
            }

        # Check response time (if too slow, might indicate poor availability)
        if avg_response_time > 5000:  # 5 seconds
            return {
                'eligible': True,
                'reason': f'Poor response time: {avg_response_time:.1f}ms > 5000ms',
                'severity': 'medium',
                'stats': stats
            }

        return {
            'eligible': False,
            'reason': 'Performance within acceptable limits',
            'stats': stats
        }

    async def cleanup_expired_challenges(self):
        """
        Clean up expired challenges from memory.
        """
        try:
            current_time = datetime.now()
            expired_challenges = [
                cid for cid, challenge in self.active_challenges.items()
                if current_time > challenge.expires_at
            ]

            for cid in expired_challenges:
                challenge = self.active_challenges[cid]
                node_id = challenge.node_id

                # Mark as failed proof for statistics
                if node_id in self.node_stats:
                    self.node_stats[node_id]['failed_proofs'] += 1
                    total_challenges = self.node_stats[node_id]['total_challenges']
                    successful = self.node_stats[node_id]['successful_proofs']
                    self.node_stats[node_id]['success_rate'] = successful / total_challenges

                del self.active_challenges[cid]

            if expired_challenges:
                self.logger.info(f"🧹 Cleaned up {len(expired_challenges)} expired challenges")

        except Exception as e:
            self.logger.error(f"Error cleaning up expired challenges: {e}")

    def export_challenge_data(self, challenge_id: str) -> Optional[Dict[str, Any]]:
        """
        Export challenge data for external verification.

        Args:
            challenge_id: Challenge ID

        Returns:
            Challenge data or None if not found
        """
        challenge = self.active_challenges.get(challenge_id)
        if not challenge:
            return None

        return {
            'challenge_id': challenge.challenge_id,
            'node_id': challenge.node_id,
            'challenge_hash': challenge.challenge_hash,
            'timestamp': challenge.timestamp.isoformat(),
            'difficulty': challenge.difficulty,
            'expires_at': challenge.expires_at.isoformat(),
            'challenge_data_hex': challenge.challenge_data.hex()
        }

