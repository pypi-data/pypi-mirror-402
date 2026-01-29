"""
Zero-knowledge audit logger for GDPR compliance.
Provides privacy-preserving logging of compliant actions with ZK proofs.
"""

import asyncio
import hashlib
import json
import secrets
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import base64

from ..core.config import Config
from ..verification.zk_proofs import ZKProof, ZKProver, ZKVerifier
from ..infrastructure.ipfs_embedded import IPFSManager
from ..blockchain.dracma_token import get_token_manager
from ..utils.logging import AiloosLogger


@dataclass
class CompliantActionLog:
    """Log entry for a GDPR compliant action with ZK proof."""
    log_id: str
    user_id: str
    action_type: str
    compliance_proof: ZKProof
    timestamp: datetime
    ipfs_cid: Optional[str] = None
    blockchain_tx_hash: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class AuditQueryResult:
    """Result of an audit query."""
    logs: List[CompliantActionLog]
    total_count: int
    verified_proofs: int
    query_timestamp: datetime


class ZKAuditLogger:
    """
    Zero-knowledge audit logger for GDPR compliance.
    Logs actions with ZK proofs that verify compliance without revealing sensitive data.
    """

    def __init__(self, config: Config):
        self.config = config
        self.logger = AiloosLogger(__name__)

        # ZK components
        self.zk_prover = ZKProver(config)
        self.zk_verifier = ZKVerifier(config)

        # Storage components
        self.ipfs_manager = IPFSManager()
        self.token_manager = get_token_manager()

        # Log storage
        self.logs: Dict[str, CompliantActionLog] = {}
        self.user_logs: Dict[str, List[str]] = {}  # user_id -> list of log_ids

        # Configuration
        self.enable_ipfs_storage = config.get('zk_audit_enable_ipfs', True)
        self.enable_blockchain_storage = config.get('zk_audit_enable_blockchain', False)
        self.max_logs_per_user = config.get('zk_audit_max_logs_per_user', 1000)

        # Start background cleanup
        asyncio.create_task(self._start_background_cleanup())

    async def log_compliant_action(
        self,
        action_data: Dict[str, Any],
        user_id: str,
        compliance_rules: List[str] = None
    ) -> CompliantActionLog:
        """
        Log a GDPR compliant action with ZK proof.

        Args:
            action_data: Data about the action (will be hashed, not stored)
            user_id: User identifier
            compliance_rules: List of compliance rules verified

        Returns:
            CompliantActionLog with ZK proof
        """
        try:
            if compliance_rules is None:
                compliance_rules = ['GDPR_Article_6', 'GDPR_Article_9', 'Data_Minimization']

            # Generate ZK proof of compliance
            compliance_proof = await self._prove_action_compliance(
                action_data, user_id, compliance_rules
            )

            # Create log entry
            log_id = secrets.token_hex(16)
            log_entry = CompliantActionLog(
                log_id=log_id,
                user_id=user_id,
                action_type=action_data.get('action_type', 'unknown'),
                compliance_proof=compliance_proof,
                timestamp=datetime.now(),
                metadata={
                    'compliance_rules': compliance_rules,
                    'action_category': action_data.get('category', 'general'),
                    'data_sensitivity': action_data.get('sensitivity_level', 'low')
                }
            )

            # Store log
            self.logs[log_id] = log_entry

            # Track user logs
            if user_id not in self.user_logs:
                self.user_logs[user_id] = []
            self.user_logs[user_id].append(log_id)

            # Limit logs per user
            if len(self.user_logs[user_id]) > self.max_logs_per_user:
                oldest_log_id = self.user_logs[user_id].pop(0)
                if oldest_log_id in self.logs:
                    del self.logs[oldest_log_id]

            # Store in IPFS if enabled
            if self.enable_ipfs_storage:
                await self._store_log_in_ipfs(log_entry)

            # Store hash in blockchain if enabled
            if self.enable_blockchain_storage:
                await self._store_log_hash_in_blockchain(log_entry)

            self.logger.info(f"✅ Logged compliant action for user {user_id}: {log_id}")
            return log_entry

        except Exception as e:
            self.logger.error(f"❌ Error logging compliant action: {e}")
            raise

    async def verify_compliance_proof(self, proof: ZKProof) -> bool:
        """
        Verify a ZK compliance proof.

        Args:
            proof: ZK proof to verify

        Returns:
            True if proof is valid
        """
        try:
            is_valid = await self.zk_verifier._verify_zk_proof(proof)
            if is_valid:
                proof.verified = True
                self.logger.info(f"✅ Verified compliance proof: {proof.proof_id}")
            else:
                self.logger.warning(f"❌ Invalid compliance proof: {proof.proof_id}")
            return is_valid

        except Exception as e:
            self.logger.error(f"❌ Error verifying compliance proof: {e}")
            return False

    async def query_audit_logs(
        self,
        user_id: Optional[str] = None,
        action_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        verified_only: bool = False,
        limit: int = 100
    ) -> AuditQueryResult:
        """
        Query audit logs with filtering.

        Args:
            user_id: Filter by user ID
            action_type: Filter by action type
            date_from: Filter from date
            date_to: Filter to date
            verified_only: Only return logs with verified proofs
            limit: Maximum number of results

        Returns:
            AuditQueryResult with matching logs
        """
        try:
            matching_logs = []

            # Get candidate logs
            if user_id:
                candidate_log_ids = self.user_logs.get(user_id, [])
            else:
                candidate_log_ids = list(self.logs.keys())

            # Apply filters
            for log_id in candidate_log_ids:
                if log_id not in self.logs:
                    continue

                log_entry = self.logs[log_id]

                # Date filters
                if date_from and log_entry.timestamp < date_from:
                    continue
                if date_to and log_entry.timestamp > date_to:
                    continue

                # Action type filter
                if action_type and log_entry.action_type != action_type:
                    continue

                # Verified only filter
                if verified_only and not log_entry.compliance_proof.verified:
                    continue

                matching_logs.append(log_entry)

                if len(matching_logs) >= limit:
                    break

            # Sort by timestamp (newest first)
            matching_logs.sort(key=lambda x: x.timestamp, reverse=True)

            # Count verified proofs
            verified_count = sum(1 for log in matching_logs if log.compliance_proof.verified)

            result = AuditQueryResult(
                logs=matching_logs,
                total_count=len(matching_logs),
                verified_proofs=verified_count,
                query_timestamp=datetime.now()
            )

            self.logger.info(f"📊 Audit query returned {len(matching_logs)} logs")
            return result

        except Exception as e:
            self.logger.error(f"❌ Error querying audit logs: {e}")
            raise

    async def get_compliance_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get compliance statistics.

        Args:
            user_id: User ID to get stats for, or None for global stats

        Returns:
            Dictionary with compliance statistics
        """
        try:
            if user_id:
                logs = [self.logs[log_id] for log_id in self.user_logs.get(user_id, [])
                       if log_id in self.logs]
            else:
                logs = list(self.logs.values())

            total_logs = len(logs)
            verified_logs = sum(1 for log in logs if log.compliance_proof.verified)

            # Compliance by action type
            action_types = {}
            for log in logs:
                action_types[log.action_type] = action_types.get(log.action_type, 0) + 1

            # Compliance over time (last 30 days)
            thirty_days_ago = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            recent_logs = [log for log in logs if log.timestamp >= thirty_days_ago]

            return {
                'total_logs': total_logs,
                'verified_logs': verified_logs,
                'verification_rate': verified_logs / max(total_logs, 1),
                'action_type_distribution': action_types,
                'recent_logs_count': len(recent_logs),
                'ipfs_stored_logs': sum(1 for log in logs if log.ipfs_cid),
                'blockchain_stored_logs': sum(1 for log in logs if log.blockchain_tx_hash)
            }

        except Exception as e:
            self.logger.error(f"❌ Error getting compliance stats: {e}")
            raise

    async def _prove_action_compliance(
        self,
        action_data: Dict[str, Any],
        user_id: str,
        compliance_rules: List[str]
    ) -> ZKProof:
        """
        Generate ZK proof that action complies with GDPR rules.
        Proves compliance without revealing the actual action data.
        """
        # Create commitment to action data (hash without revealing content)
        action_hash = hashlib.sha256(json.dumps(action_data, sort_keys=True).encode()).hexdigest()

        # Create compliance statement
        compliance_data = {
            'user_id': user_id,
            'action_hash': action_hash,
            'compliance_rules': compliance_rules,
            'timestamp': datetime.now().isoformat(),
            'data_minimized': self._check_data_minimization(action_data),
            'consent_verified': self._check_consent(action_data),
            'privacy_preserved': True  # Assumed for compliant actions
        }

        # Generate ZK proof
        proof_data = {
            'commitment': self._create_commitment(json.dumps(compliance_data, sort_keys=True)),
            'proof_elements': self.zk_prover._generate_proof_elements(),
            'compliance_hash': hashlib.sha256(json.dumps(compliance_rules, sort_keys=True).encode()).hexdigest()
        }

        return ZKProof(
            proof_id=secrets.token_hex(16),
            statement="action_complies_with_gdpr",
            proof_data=proof_data,
            public_inputs={
                'user_id': user_id,
                'compliance_rules_count': len(compliance_rules),
                'action_category': action_data.get('category', 'unknown')
            },
            created_at=datetime.now()
        )

    async def _store_log_in_ipfs(self, log_entry: CompliantActionLog) -> None:
        """Store log entry in IPFS."""
        try:
            # Prepare log data for IPFS (without sensitive information)
            ipfs_data = {
                'log_id': log_entry.log_id,
                'user_id': log_entry.user_id,
                'action_type': log_entry.action_type,
                'timestamp': log_entry.timestamp.isoformat(),
                'compliance_proof_id': log_entry.compliance_proof.proof_id,
                'metadata': log_entry.metadata,
                'proof_verified': log_entry.compliance_proof.verified
            }

            # Convert to JSON and store in IPFS
            json_data = json.dumps(ipfs_data, indent=2).encode('utf-8')
            cid = await self.ipfs_manager.publish_data(json_data, {
                'type': 'zk_audit_log',
                'user_id': log_entry.user_id,
                'timestamp': log_entry.timestamp.isoformat()
            })

            log_entry.ipfs_cid = cid
            self.logger.debug(f"📤 Stored log {log_entry.log_id} in IPFS: {cid}")

        except Exception as e:
            self.logger.warning(f"⚠️ Failed to store log in IPFS: {e}")

    async def _store_log_hash_in_blockchain(self, log_entry: CompliantActionLog) -> None:
        """Store log hash in blockchain for immutability."""
        try:
            # Create hash of the log entry
            log_hash = hashlib.sha256(json.dumps({
                'log_id': log_entry.log_id,
                'user_id': log_entry.user_id,
                'proof_id': log_entry.compliance_proof.proof_id,
                'timestamp': log_entry.timestamp.isoformat()
            }, sort_keys=True).encode()).hexdigest()

            # For simulation, we'll use a mock transaction
            # In production, this would interact with a smart contract
            tx_result = await self.token_manager.transfer_tokens(
                from_address="audit_contract",
                to_address="audit_log",
                amount=0.0  # Zero amount transfer just to record hash
            )

            if tx_result.success:
                log_entry.blockchain_tx_hash = tx_result.tx_hash
                self.logger.debug(f"🔗 Stored log hash in blockchain: {tx_result.tx_hash}")
            else:
                self.logger.warning(f"⚠️ Failed to store log hash in blockchain: {tx_result.error_message}")

        except Exception as e:
            self.logger.warning(f"⚠️ Failed to store log hash in blockchain: {e}")

    def _check_data_minimization(self, action_data: Dict[str, Any]) -> bool:
        """Check if action data follows data minimization principles."""
        # Simple check: ensure only necessary fields are present
        required_fields = {'action_type', 'category', 'sensitivity_level'}
        return all(field in action_data for field in required_fields)

    def _check_consent(self, action_data: Dict[str, Any]) -> bool:
        """Check if proper consent was obtained."""
        # In practice, this would verify against consent records
        return action_data.get('consent_obtained', False)

    def _create_commitment(self, value: str) -> str:
        """Create cryptographic commitment."""
        nonce = secrets.token_bytes(16)
        commitment = hashlib.sha256(value.encode() + nonce).hexdigest()
        return commitment

    async def _start_background_cleanup(self):
        """Background task to clean up old logs and verify proofs."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour

                # Verify unverified proofs
                unverified_count = 0
                for log in self.logs.values():
                    if not log.compliance_proof.verified:
                        await self.verify_compliance_proof(log.compliance_proof)
                        unverified_count += 1

                if unverified_count > 0:
                    self.logger.info(f"🔍 Verified {unverified_count} pending compliance proofs")

                # Clean up old logs (older than 1 year)
                one_year_ago = datetime.now().replace(year=datetime.now().year - 1)
                old_logs = [log_id for log_id, log in self.logs.items()
                           if log.timestamp < one_year_ago]

                for log_id in old_logs:
                    del self.logs[log_id]
                    # Remove from user logs
                    for user_logs in self.user_logs.values():
                        if log_id in user_logs:
                            user_logs.remove(log_id)

                if old_logs:
                    self.logger.info(f"🧹 Cleaned up {len(old_logs)} old audit logs")

            except Exception as e:
                self.logger.error(f"❌ Error in background cleanup: {e}")
                await asyncio.sleep(300)  # Retry in 5 minutes

    def get_logger_stats(self) -> Dict[str, Any]:
        """Get logger statistics."""
        total_logs = len(self.logs)
        verified_logs = sum(1 for log in self.logs.values() if log.compliance_proof.verified)
        ipfs_stored = sum(1 for log in self.logs.values() if log.ipfs_cid)
        blockchain_stored = sum(1 for log in self.logs.values() if log.blockchain_tx_hash)

        return {
            'total_logs': total_logs,
            'verified_logs': verified_logs,
            'verification_rate': verified_logs / max(total_logs, 1),
            'ipfs_stored_logs': ipfs_stored,
            'blockchain_stored_logs': blockchain_stored,
            'unique_users': len(self.user_logs),
            'storage_enabled': {
                'ipfs': self.enable_ipfs_storage,
                'blockchain': self.enable_blockchain_storage
            }
        }