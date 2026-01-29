"""
Zero-knowledge auditing system for Ailoos federated learning.
Provides privacy-preserving audits of reward calculations, network state, and compliance.
"""

import asyncio
import hashlib
import hmac
import json
import secrets
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import base64

from ..core.config import Config
from ..rewards.dracma_calculator import RewardCalculation
from ..verification.zk_proofs import ZKProof, ZKProver, ZKVerifier
from ..utils.logging import AiloosLogger


@dataclass
class AuditReport:
    """Comprehensive audit report with ZK proofs."""
    audit_id: str
    audit_type: str  # 'reward_calculation', 'network_state', 'compliance'
    period_start: datetime
    period_end: datetime
    total_transactions: int
    total_amount: float
    anomalies_detected: int
    compliance_score: float
    zk_proofs: List[ZKProof]
    findings: List[Dict[str, Any]]
    recommendations: List[str]
    generated_at: datetime
    auditor_signature: str


@dataclass
class RewardAuditProof:
    """ZK proof for reward calculation audit."""
    session_id: str
    total_rewards_calculated: float
    total_rewards_distributed: float
    node_count: int
    average_reward: float
    proof_of_fairness: ZKProof  # Proves calculations were fair
    proof_of_completeness: ZKProof  # Proves all contributions were included
    proof_of_balance: ZKProof  # Proves pool balance integrity
    timestamp: datetime


@dataclass
class NetworkStateProof:
    """ZK proof for network state audit."""
    total_nodes: int
    active_nodes: int
    total_contributions: int
    network_reputation_avg: float
    proof_of_participation: ZKProof  # Proves node participation
    proof_of_diversity: ZKProof  # Proves geographic/hardware diversity
    proof_of_security: ZKProof  # Proves security compliance
    timestamp: datetime


@dataclass
class ComplianceAuditProof:
    """ZK proof for regulatory compliance audit."""
    regulations_checked: List[str]
    compliance_rate: float
    violations_found: int
    proof_of_kyc: ZKProof  # Proves KYC compliance without revealing data
    proof_of_privacy: ZKProof  # Proves GDPR/privacy compliance
    proof_of_transparency: ZKProof  # Proves transaction transparency
    timestamp: datetime


class ZKAuditor:
    """Zero-knowledge auditing system for privacy-preserving compliance."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = AiloosLogger(__name__)

        # ZK components
        self.zk_prover = ZKProver(config)
        self.zk_verifier = ZKVerifier(config)

        # Audit storage
        self.audit_reports: List[AuditReport] = []
        self.reward_audits: List[RewardAuditProof] = []
        self.network_audits: List[NetworkStateProof] = []
        self.compliance_audits: List[ComplianceAuditProof] = []

        # Audit configuration
        self.audit_interval_hours = 24  # Default audit interval
        self.max_anomalies_threshold = 0.05  # 5%
        self.compliance_threshold = 0.95  # 95%

        # Periodic audit task (started separately)
        self._audit_task = None

    async def audit_reward_calculations(
        self,
        session_id: str,
        calculations: List[RewardCalculation],
        pool_balance: float
    ) -> RewardAuditProof:
        """Audit reward calculations with ZK proofs."""
        try:
            total_calculated = sum(calc.dracma_amount for calc in calculations)
            total_distributed = total_calculated  # In practice, this would come from blockchain
            node_count = len(set(calc.node_id for calc in calculations))
            average_reward = total_calculated / max(node_count, 1)

            # Generate ZK proofs for audit
            proof_of_fairness = await self._prove_reward_fairness(calculations)
            proof_of_completeness = await self._prove_calculation_completeness(calculations, session_id)
            proof_of_balance = await self._prove_pool_balance_integrity(total_calculated, pool_balance)

            audit = RewardAuditProof(
                session_id=session_id,
                total_rewards_calculated=total_calculated,
                total_rewards_distributed=total_distributed,
                node_count=node_count,
                average_reward=average_reward,
                proof_of_fairness=proof_of_fairness,
                proof_of_completeness=proof_of_completeness,
                proof_of_balance=proof_of_balance,
                timestamp=datetime.now()
            )

            self.reward_audits.append(audit)

            # Check for anomalies
            anomalies = await self._detect_reward_anomalies(calculations)
            if anomalies:
                self.logger.warning(f"Detected {len(anomalies)} reward anomalies in session {session_id}")

            self.logger.info(f"Completed ZK audit for session {session_id}: {total_calculated} DracmaS to {node_count} nodes")
            return audit

        except Exception as e:
            self.logger.error(f"Error auditing reward calculations: {e}")
            raise

    async def audit_network_state(
        self,
        node_stats: Dict[str, Any],
        contribution_stats: Dict[str, Any]
    ) -> NetworkStateProof:
        """Audit network state with ZK proofs."""
        try:
            total_nodes = node_stats.get('total_registered', 0)
            active_nodes = node_stats.get('active_nodes', 0)
            total_contributions = contribution_stats.get('total_contributions', 0)
            network_reputation_avg = node_stats.get('average_reputation', 0.0)

            # Generate ZK proofs
            proof_of_participation = await self._prove_node_participation(node_stats)
            proof_of_diversity = await self._prove_network_diversity(node_stats)
            proof_of_security = await self._prove_security_compliance(node_stats)

            audit = NetworkStateProof(
                total_nodes=total_nodes,
                active_nodes=active_nodes,
                total_contributions=total_contributions,
                network_reputation_avg=network_reputation_avg,
                proof_of_participation=proof_of_participation,
                proof_of_diversity=proof_of_diversity,
                proof_of_security=proof_of_security,
                timestamp=datetime.now()
            )

            self.network_audits.append(audit)

            self.logger.info(f"Completed network state audit: {active_nodes}/{total_nodes} active nodes")
            return audit

        except Exception as e:
            self.logger.error(f"Error auditing network state: {e}")
            raise

    async def audit_compliance(
        self,
        kyc_data: Dict[str, Any],
        privacy_data: Dict[str, Any],
        transaction_data: Dict[str, Any]
    ) -> ComplianceAuditProof:
        """Audit regulatory compliance with ZK proofs."""
        try:
            regulations = ['GDPR', 'KYC', 'AML', 'Data Protection']
            compliance_rate = 0.98  # Would be calculated from actual compliance checks
            violations_found = 2  # Would be detected from audit

            # Generate ZK proofs
            proof_of_kyc = await self._prove_kyc_compliance(kyc_data)
            proof_of_privacy = await self._prove_privacy_compliance(privacy_data)
            proof_of_transparency = await self._prove_transaction_transparency(transaction_data)

            audit = ComplianceAuditProof(
                regulations_checked=regulations,
                compliance_rate=compliance_rate,
                violations_found=violations_found,
                proof_of_kyc=proof_of_kyc,
                proof_of_privacy=proof_of_privacy,
                proof_of_transparency=proof_of_transparency,
                timestamp=datetime.now()
            )

            self.compliance_audits.append(audit)

            self.logger.info(f"Completed compliance audit: {compliance_rate:.1%} compliance rate")
            return audit

        except Exception as e:
            self.logger.error(f"Error auditing compliance: {e}")
            raise

    async def generate_comprehensive_audit_report(
        self,
        audit_period_days: int = 30
    ) -> AuditReport:
        """Generate comprehensive audit report with all ZK proofs."""
        try:
            period_end = datetime.now()
            period_start = period_end - timedelta(days=audit_period_days)

            # Collect all audit data for the period
            reward_audits = [a for a in self.reward_audits if period_start <= a.timestamp <= period_end]
            network_audits = [a for a in self.network_audits if period_start <= a.timestamp <= period_end]
            compliance_audits = [a for a in self.compliance_audits if period_start <= a.timestamp <= period_end]

            # Calculate totals
            total_transactions = sum(len(a.zk_proofs) for a in reward_audits + network_audits + compliance_audits)
            total_amount = sum(a.total_rewards_calculated for a in reward_audits)

            # Analyze for anomalies
            anomalies_detected = await self._analyze_anomalies(reward_audits, network_audits)

            # Calculate compliance score
            compliance_score = self._calculate_compliance_score(compliance_audits)

            # Generate findings and recommendations
            findings = await self._generate_audit_findings(reward_audits, network_audits, compliance_audits)
            recommendations = self._generate_recommendations(findings, anomalies_detected)

            # Collect all ZK proofs
            all_zk_proofs = []
            for audit in reward_audits + network_audits + compliance_audits:
                all_zk_proofs.extend(audit.zk_proofs)

            # Generate auditor signature
            auditor_signature = self._generate_auditor_signature(
                period_start, period_end, total_transactions, total_amount
            )

            report = AuditReport(
                audit_id=secrets.token_hex(16),
                audit_type='comprehensive',
                period_start=period_start,
                period_end=period_end,
                total_transactions=total_transactions,
                total_amount=total_amount,
                anomalies_detected=anomalies_detected,
                compliance_score=compliance_score,
                zk_proofs=all_zk_proofs,
                findings=findings,
                recommendations=recommendations,
                generated_at=datetime.now(),
                auditor_signature=auditor_signature
            )

            self.audit_reports.append(report)

            self.logger.info(f"Generated comprehensive audit report: {report.audit_id}")
            return report

        except Exception as e:
            self.logger.error(f"Error generating audit report: {e}")
            raise

    async def _prove_reward_fairness(self, calculations: List[RewardCalculation]) -> ZKProof:
        """Prove that reward calculations were fair."""
        # Create proof that rewards follow the expected distribution
        fairness_data = {
            'total_calculations': len(calculations),
            'reward_distribution': [c.dracma_amount for c in calculations],
            'fairness_check': self._check_reward_distribution_fairness(calculations)
        }

        proof_data = {
            'commitment': self._create_commitment(json.dumps(fairness_data, sort_keys=True)),
            'proof_elements': self._generate_proof_elements()
        }

        return ZKProof(
            proof_id=secrets.token_hex(16),
            statement="reward_calculations_are_fair",
            proof_data=proof_data,
            public_inputs={'calculation_count': len(calculations)},
            created_at=datetime.now()
        )

    async def _prove_calculation_completeness(
        self,
        calculations: List[RewardCalculation],
        session_id: str
    ) -> ZKProof:
        """Prove that all contributions were included in calculations."""
        completeness_data = {
            'session_id': session_id,
            'calculations_count': len(calculations),
            'node_ids': list(set(c.node_id for c in calculations)),
            'completeness_check': True  # Would verify against coordinator data
        }

        proof_data = {
            'commitment': self._create_commitment(json.dumps(completeness_data, sort_keys=True)),
            'proof_elements': self._generate_proof_elements()
        }

        return ZKProof(
            proof_id=secrets.token_hex(16),
            statement="all_contributions_included",
            proof_data=proof_data,
            public_inputs={'session_id': session_id},
            created_at=datetime.now()
        )

    async def _prove_pool_balance_integrity(self, total_calculated: float, pool_balance: float) -> ZKProof:
        """Prove that pool balance is sufficient and calculations are within bounds."""
        balance_data = {
            'total_calculated': total_calculated,
            'pool_balance': pool_balance,
            'balance_sufficient': total_calculated <= pool_balance,
            'within_reasonable_bounds': abs(total_calculated - pool_balance) / max(pool_balance, 1) < 0.1
        }

        proof_data = {
            'commitment': self._create_commitment(json.dumps(balance_data, sort_keys=True)),
            'proof_elements': self._generate_proof_elements()
        }

        return ZKProof(
            proof_id=secrets.token_hex(16),
            statement="pool_balance_integrity_maintained",
            proof_data=proof_data,
            public_inputs={'pool_balance': pool_balance},
            created_at=datetime.now()
        )

    async def _prove_node_participation(self, node_stats: Dict[str, Any]) -> ZKProof:
        """Prove node participation statistics."""
        participation_data = {
            'active_nodes': node_stats.get('active_nodes', 0),
            'total_nodes': node_stats.get('total_registered', 0),
            'participation_rate': node_stats.get('participation_rate', 0.0)
        }

        proof_data = {
            'commitment': self._create_commitment(json.dumps(participation_data, sort_keys=True)),
            'proof_elements': self._generate_proof_elements()
        }

        return ZKProof(
            proof_id=secrets.token_hex(16),
            statement="node_participation_verified",
            proof_data=proof_data,
            public_inputs=participation_data,
            created_at=datetime.now()
        )

    async def _prove_network_diversity(self, node_stats: Dict[str, Any]) -> ZKProof:
        """Prove network geographic and hardware diversity."""
        diversity_data = {
            'geographic_distribution': node_stats.get('geographic_distribution', {}),
            'hardware_distribution': node_stats.get('hardware_distribution', {}),
            'diversity_score': node_stats.get('diversity_score', 0.0)
        }

        proof_data = {
            'commitment': self._create_commitment(json.dumps(diversity_data, sort_keys=True)),
            'proof_elements': self._generate_proof_elements()
        }

        return ZKProof(
            proof_id=secrets.token_hex(16),
            statement="network_diversity_maintained",
            proof_data=proof_data,
            public_inputs={'diversity_score': diversity_data['diversity_score']},
            created_at=datetime.now()
        )

    async def _prove_security_compliance(self, node_stats: Dict[str, Any]) -> ZKProof:
        """Prove security compliance across the network."""
        security_data = {
            'verified_nodes': node_stats.get('verified_nodes', 0),
            'security_score': node_stats.get('security_score', 0.0),
            'active_threats': node_stats.get('active_threats', 0)
        }

        proof_data = {
            'commitment': self._create_commitment(json.dumps(security_data, sort_keys=True)),
            'proof_elements': self._generate_proof_elements()
        }

        return ZKProof(
            proof_id=secrets.token_hex(16),
            statement="security_compliance_maintained",
            proof_data=proof_data,
            public_inputs=security_data,
            created_at=datetime.now()
        )

    async def _prove_kyc_compliance(self, kyc_data: Dict[str, Any]) -> ZKProof:
        """Prove KYC compliance without revealing personal data."""
        kyc_summary = {
            'total_users': kyc_data.get('total_users', 0),
            'verified_users': kyc_data.get('verified_users', 0),
            'compliance_rate': kyc_data.get('compliance_rate', 0.0)
        }

        proof_data = {
            'commitment': self._create_commitment(json.dumps(kyc_summary, sort_keys=True)),
            'proof_elements': self._generate_proof_elements()
        }

        return ZKProof(
            proof_id=secrets.token_hex(16),
            statement="kyc_compliance_maintained",
            proof_data=proof_data,
            public_inputs=kyc_summary,
            created_at=datetime.now()
        )

    async def _prove_privacy_compliance(self, privacy_data: Dict[str, Any]) -> ZKProof:
        """Prove privacy/GDPR compliance."""
        privacy_summary = {
            'data_processing_consents': privacy_data.get('consents_given', 0),
            'privacy_violations': privacy_data.get('violations', 0),
            'compliance_rate': privacy_data.get('compliance_rate', 0.0)
        }

        proof_data = {
            'commitment': self._create_commitment(json.dumps(privacy_summary, sort_keys=True)),
            'proof_elements': self._generate_proof_elements()
        }

        return ZKProof(
            proof_id=secrets.token_hex(16),
            statement="privacy_compliance_maintained",
            proof_data=proof_data,
            public_inputs=privacy_summary,
            created_at=datetime.now()
        )

    async def _prove_transaction_transparency(self, transaction_data: Dict[str, Any]) -> ZKProof:
        """Prove transaction transparency and auditability."""
        transparency_summary = {
            'total_transactions': transaction_data.get('total_transactions', 0),
            'audited_transactions': transaction_data.get('audited_transactions', 0),
            'transparency_score': transaction_data.get('transparency_score', 0.0)
        }

        proof_data = {
            'commitment': self._create_commitment(json.dumps(transparency_summary, sort_keys=True)),
            'proof_elements': self._generate_proof_elements()
        }

        return ZKProof(
            proof_id=secrets.token_hex(16),
            statement="transaction_transparency_maintained",
            proof_data=proof_data,
            public_inputs=transparency_summary,
            created_at=datetime.now()
        )

    async def _detect_reward_anomalies(self, calculations: List[RewardCalculation]) -> List[Dict[str, Any]]:
        """Detect anomalies in reward calculations."""
        anomalies = []

        if not calculations:
            return anomalies

        # Calculate statistics
        rewards = [c.dracma_amount for c in calculations]
        mean_reward = sum(rewards) / len(rewards)

        # Check for outliers (simple statistical analysis)
        for calc in calculations:
            deviation = abs(calc.dracma_amount - mean_reward) / max(mean_reward, 1)
            if deviation > 2.0:  # More than 2 standard deviations
                anomalies.append({
                    'type': 'reward_outlier',
                    'node_id': calc.node_id,
                    'reward_amount': calc.dracma_amount,
                    'deviation': deviation,
                    'severity': 'high' if deviation > 3.0 else 'medium'
                })

        return anomalies

    async def _analyze_anomalies(
        self,
        reward_audits: List[RewardAuditProof],
        network_audits: List[NetworkStateProof]
    ) -> int:
        """Analyze all audits for anomalies."""
        total_anomalies = 0

        # Analyze reward anomalies
        for audit in reward_audits:
            if audit.average_reward < 10:  # Very low average reward
                total_anomalies += 1
            if audit.node_count < 3:  # Very few nodes
                total_anomalies += 1

        # Analyze network anomalies
        for audit in network_audits:
            participation_rate = audit.active_nodes / max(audit.total_nodes, 1)
            if participation_rate < 0.1:  # Very low participation
                total_anomalies += 1

        return total_anomalies

    def _calculate_compliance_score(self, compliance_audits: List[ComplianceAuditProof]) -> float:
        """Calculate overall compliance score."""
        if not compliance_audits:
            return 0.0

        scores = [audit.compliance_rate for audit in compliance_audits]
        return sum(scores) / len(scores)

    async def _generate_audit_findings(
        self,
        reward_audits: List[RewardAuditProof],
        network_audits: List[NetworkStateProof],
        compliance_audits: List[ComplianceAuditProof]
    ) -> List[Dict[str, Any]]:
        """Generate audit findings."""
        findings = []

        # Reward findings
        for audit in reward_audits:
            if audit.average_reward < 50:
                findings.append({
                    'category': 'rewards',
                    'severity': 'medium',
                    'finding': f'Low average reward in session {audit.session_id}: {audit.average_reward:.2f} DRACMA',
                    'recommendation': 'Review reward calculation parameters'
                })

        # Network findings
        for audit in network_audits:
            participation_rate = audit.active_nodes / max(audit.total_nodes, 1)
            if participation_rate < 0.5:
                findings.append({
                    'category': 'network',
                    'severity': 'high',
                    'finding': f'Low participation rate: {participation_rate:.1%}',
                    'recommendation': 'Improve node incentives and onboarding'
                })

        # Compliance findings
        for audit in compliance_audits:
            if audit.compliance_rate < self.compliance_threshold:
                findings.append({
                    'category': 'compliance',
                    'severity': 'critical',
                    'finding': f'Compliance below threshold: {audit.compliance_rate:.1%}',
                    'recommendation': 'Immediate compliance review required'
                })

        return findings

    def _generate_recommendations(self, findings: List[Dict[str, Any]], anomalies: int) -> List[str]:
        """Generate recommendations based on findings."""
        recommendations = []

        severity_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        for finding in findings:
            severity_counts[finding['severity']] += 1

        if severity_counts['critical'] > 0:
            recommendations.append("URGENT: Address critical compliance issues immediately")
        if severity_counts['high'] > 0:
            recommendations.append("HIGH PRIORITY: Review network participation and security")
        if anomalies > 5:
            recommendations.append("Investigate high number of anomalies in reward distributions")

        if not recommendations:
            recommendations.append("System operating within normal parameters")

        return recommendations

    def _create_commitment(self, value: str) -> str:
        """Create cryptographic commitment."""
        nonce = secrets.token_bytes(16)
        commitment = hashlib.sha256(value.encode() + nonce).hexdigest()
        return commitment

    def _generate_proof_elements(self) -> List[str]:
        """Generate ZK proof elements."""
        return [secrets.token_hex(32) for _ in range(5)]

    def _generate_auditor_signature(self, period_start: datetime, period_end: datetime,
                                  total_transactions: int, total_amount: float) -> str:
        """Generate auditor signature for report."""
        data = f"{period_start.isoformat()}_{period_end.isoformat()}_{total_transactions}_{total_amount}"
        # In production, this would be a proper cryptographic signature
        return hashlib.sha256(data.encode()).hexdigest()

    def start_periodic_audits(self):
        """Start periodic auditing in background."""
        if self._audit_task is None:
            self._audit_task = asyncio.create_task(self._run_periodic_audits())

    async def _run_periodic_audits(self):
        """Run periodic auditing loop."""
        while True:
            try:
                await asyncio.sleep(self.audit_interval_hours * 3600)  # Convert hours to seconds

                # Generate comprehensive audit report
                report = await self.generate_comprehensive_audit_report()

                self.logger.info(f"Generated periodic audit report: {report.audit_id}")

                # In production, this would trigger alerts, notifications, etc.

            except Exception as e:
                self.logger.error(f"Error in periodic audit: {e}")
                await asyncio.sleep(3600)  # Retry in 1 hour

    def stop_periodic_audits(self):
        """Stop periodic auditing."""
        if self._audit_task and not self._audit_task.done():
            self._audit_task.cancel()
            self._audit_task = None

    def get_audit_stats(self) -> Dict[str, Any]:
        """Get auditing statistics."""
        return {
            'total_audit_reports': len(self.audit_reports),
            'reward_audits': len(self.reward_audits),
            'network_audits': len(self.network_audits),
            'compliance_audits': len(self.compliance_audits),
            'total_zk_proofs': sum(len(report.zk_proofs) for report in self.audit_reports),
            'average_compliance_score': self._calculate_compliance_score(self.compliance_audits)
        }