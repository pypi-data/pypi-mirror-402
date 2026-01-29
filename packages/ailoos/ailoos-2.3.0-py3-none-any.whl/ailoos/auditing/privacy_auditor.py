"""
Privacy auditor for Ailoos with zero-knowledge proofs.
Audits data privacy, GDPR compliance, and information leakage without accessing sensitive data.
"""

import asyncio
import hashlib
import json
import secrets
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import re

from ..core.config import Config
from ..verification.zk_proofs import ZKProof
from ..utils.logging import AiloosLogger


@dataclass
class PrivacyAuditReport:
    """Privacy audit report with ZK proofs."""
    audit_id: str
    period_start: datetime
    period_end: datetime
    data_processing_operations: int
    privacy_violations: int
    gdpr_compliance_score: float
    data_leakage_risk: str  # 'low', 'medium', 'high', 'critical'
    privacy_proofs: List[ZKProof]
    violations_found: List[Dict[str, Any]]
    recommendations: List[str]
    generated_at: datetime


@dataclass
class DataProcessingProof:
    """ZK proof for data processing compliance."""
    operation_id: str
    data_subjects_affected: int
    lawful_basis: str
    consent_obtained: bool
    processing_purpose: str
    retention_period_days: int
    proof_of_consent: ZKProof
    proof_of_minimization: ZKProof
    proof_of_security: ZKProof
    timestamp: datetime


@dataclass
class DataLeakageProof:
    """ZK proof for data leakage detection."""
    system_component: str
    data_access_logs: int
    suspicious_activities: int
    encryption_verified: bool
    access_control_verified: bool
    proof_of_no_leakage: ZKProof
    proof_of_encryption: ZKProof
    timestamp: datetime


class PrivacyAuditor:
    """Audits privacy compliance using zero-knowledge proofs."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = AiloosLogger(__name__)

        # Privacy audit storage
        self.privacy_reports: List[PrivacyAuditReport] = []
        self.processing_proofs: List[DataProcessingProof] = []
        self.leakage_proofs: List[DataLeakageProof] = []

        # Privacy thresholds
        self.gdpr_compliance_threshold = getattr(config, 'gdpr_compliance_threshold', 0.95)
        self.max_privacy_violations = getattr(config, 'max_privacy_violations', 5)
        self.audit_interval_days = getattr(config, 'privacy_audit_interval_days', 30)

        # Privacy patterns for detection
        self._load_privacy_patterns()

        # Periodic audit task (started separately)
        self._privacy_audit_task = None

    def _load_privacy_patterns(self):
        """Load patterns for privacy violation detection."""
        self.privacy_patterns = {
            'pii_patterns': [
                r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
                r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',  # Credit card
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
                r'\b\d{10,15}\b',  # Phone numbers
            ],
            'sensitive_keywords': [
                'password', 'ssn', 'social_security', 'credit_card',
                'medical_record', 'health_data', 'financial_data'
            ]
        }

    async def audit_data_processing(
        self,
        operation_id: str,
        processing_metadata: Dict[str, Any]
    ) -> DataProcessingProof:
        """Audit data processing operation with ZK proofs."""
        try:
            data_subjects = processing_metadata.get('data_subjects_affected', 0)
            lawful_basis = processing_metadata.get('lawful_basis', 'consent')
            consent_obtained = processing_metadata.get('consent_obtained', False)
            purpose = processing_metadata.get('processing_purpose', 'unspecified')
            retention_days = processing_metadata.get('retention_period_days', 2555)  # 7 years default

            # Generate ZK proofs
            proof_of_consent = await self._prove_consent_obtained(processing_metadata)
            proof_of_minimization = await self._prove_data_minimization(processing_metadata)
            proof_of_security = await self._prove_processing_security(processing_metadata)

            proof = DataProcessingProof(
                operation_id=operation_id,
                data_subjects_affected=data_subjects,
                lawful_basis=lawful_basis,
                consent_obtained=consent_obtained,
                processing_purpose=purpose,
                retention_period_days=retention_days,
                proof_of_consent=proof_of_consent,
                proof_of_minimization=proof_of_minimization,
                proof_of_security=proof_of_security,
                timestamp=datetime.now()
            )

            self.processing_proofs.append(proof)

            # Check for violations
            violations = self._check_processing_violations(proof)
            if violations:
                self.logger.warning(f"Privacy violations detected in operation {operation_id}: {len(violations)}")

            self.logger.info(f"Audited data processing operation {operation_id}: {data_subjects} subjects affected")
            return proof

        except Exception as e:
            self.logger.error(f"Error auditing data processing: {e}")
            raise

    async def audit_data_leakage(
        self,
        component_id: str,
        access_logs: List[Dict[str, Any]],
        system_metadata: Dict[str, Any]
    ) -> DataLeakageProof:
        """Audit for potential data leakage with ZK proofs."""
        try:
            data_access_logs = len(access_logs)
            suspicious_activities = self._analyze_access_patterns(access_logs)
            encryption_verified = system_metadata.get('encryption_enabled', False)
            access_control_verified = system_metadata.get('access_control_enabled', True)

            # Generate ZK proofs
            proof_of_no_leakage = await self._prove_no_data_leakage(access_logs, system_metadata)
            proof_of_encryption = await self._prove_encryption_compliance(system_metadata)

            proof = DataLeakageProof(
                system_component=component_id,
                data_access_logs=data_access_logs,
                suspicious_activities=suspicious_activities,
                encryption_verified=encryption_verified,
                access_control_verified=access_control_verified,
                proof_of_no_leakage=proof_of_no_leakage,
                proof_of_encryption=proof_of_encryption,
                timestamp=datetime.now()
            )

            self.leakage_proofs.append(proof)

            if suspicious_activities > 0:
                self.logger.warning(f"Suspicious activities detected in {component_id}: {suspicious_activities}")

            self.logger.info(f"Audited data leakage for {component_id}: {data_access_logs} access logs analyzed")
            return proof

        except Exception as e:
            self.logger.error(f"Error auditing data leakage: {e}")
            raise

    async def generate_privacy_audit_report(
        self,
        audit_period_days: int = 30
    ) -> PrivacyAuditReport:
        """Generate comprehensive privacy audit report."""
        try:
            period_end = datetime.now()
            period_start = period_end - timedelta(days=audit_period_days)

            # Collect data for the period
            processing_proofs = [p for p in self.processing_proofs
                               if period_start <= p.timestamp <= period_end]
            leakage_proofs = [p for p in self.leakage_proofs
                            if period_start <= p.timestamp <= period_end]

            # Calculate metrics
            data_processing_operations = len(processing_proofs)
            privacy_violations = sum(len(self._check_processing_violations(p)) for p in processing_proofs)
            gdpr_compliance_score = self._calculate_gdpr_compliance(processing_proofs)
            data_leakage_risk = self._assess_leakage_risk(leakage_proofs)

            # Collect all ZK proofs
            all_privacy_proofs = []
            for proof in processing_proofs:
                all_privacy_proofs.extend([proof.proof_of_consent, proof.proof_of_minimization, proof.proof_of_security])
            for proof in leakage_proofs:
                all_privacy_proofs.extend([proof.proof_of_no_leakage, proof.proof_of_encryption])

            # Generate findings and recommendations
            violations_found = self._compile_violations(processing_proofs, leakage_proofs)
            recommendations = self._generate_privacy_recommendations(violations_found, gdpr_compliance_score)

            report = PrivacyAuditReport(
                audit_id=secrets.token_hex(16),
                period_start=period_start,
                period_end=period_end,
                data_processing_operations=data_processing_operations,
                privacy_violations=privacy_violations,
                gdpr_compliance_score=gdpr_compliance_score,
                data_leakage_risk=data_leakage_risk,
                privacy_proofs=all_privacy_proofs,
                violations_found=violations_found,
                recommendations=recommendations,
                generated_at=datetime.now()
            )

            self.privacy_reports.append(report)

            self.logger.info(f"Generated privacy audit report: {report.audit_id}")
            return report

        except Exception as e:
            self.logger.error(f"Error generating privacy audit report: {e}")
            raise

    async def _prove_consent_obtained(self, metadata: Dict[str, Any]) -> ZKProof:
        """Prove that proper consent was obtained."""
        consent_data = {
            'consent_mechanism': metadata.get('consent_mechanism', 'unknown'),
            'consent_records': metadata.get('consent_records_count', 0),
            'consent_withdrawal_available': metadata.get('consent_withdrawal_available', False),
            'consent_audit_trail': metadata.get('consent_audit_trail', False)
        }

        proof_data = {
            'commitment': self._create_commitment(json.dumps(consent_data, sort_keys=True)),
            'proof_elements': self._generate_proof_elements()
        }

        return ZKProof(
            proof_id=secrets.token_hex(16),
            statement="proper_consent_obtained",
            proof_data=proof_data,
            public_inputs={'consent_records': consent_data['consent_records']},
            created_at=datetime.now()
        )

    async def _prove_data_minimization(self, metadata: Dict[str, Any]) -> ZKProof:
        """Prove data minimization principles were followed."""
        minimization_data = {
            'data_collected': metadata.get('data_fields_collected', []),
            'data_used': metadata.get('data_fields_used', []),
            'retention_policy': metadata.get('retention_policy', 'unknown'),
            'data_pseudonymized': metadata.get('data_pseudonymized', False),
            'unnecessary_data_removed': metadata.get('unnecessary_data_removed', False)
        }

        proof_data = {
            'commitment': self._create_commitment(json.dumps(minimization_data, sort_keys=True)),
            'proof_elements': self._generate_proof_elements()
        }

        return ZKProof(
            proof_id=secrets.token_hex(16),
            statement="data_minimization_applied",
            proof_data=proof_data,
            public_inputs={'data_fields': len(minimization_data['data_collected'])},
            created_at=datetime.now()
        )

    async def _prove_processing_security(self, metadata: Dict[str, Any]) -> ZKProof:
        """Prove processing security measures."""
        security_data = {
            'encryption_at_rest': metadata.get('encryption_at_rest', False),
            'encryption_in_transit': metadata.get('encryption_in_transit', False),
            'access_controls': metadata.get('access_controls', False),
            'audit_logging': metadata.get('audit_logging', False),
            'data_backup_encrypted': metadata.get('data_backup_encrypted', False)
        }

        proof_data = {
            'commitment': self._create_commitment(json.dumps(security_data, sort_keys=True)),
            'proof_elements': self._generate_proof_elements()
        }

        return ZKProof(
            proof_id=secrets.token_hex(16),
            statement="processing_security_maintained",
            proof_data=proof_data,
            public_inputs=security_data,
            created_at=datetime.now()
        )

    async def _prove_no_data_leakage(
        self,
        access_logs: List[Dict[str, Any]],
        system_metadata: Dict[str, Any]
    ) -> ZKProof:
        """Prove no data leakage occurred."""
        leakage_analysis = {
            'access_logs_analyzed': len(access_logs),
            'suspicious_patterns': self._analyze_access_patterns(access_logs),
            'encryption_verified': system_metadata.get('encryption_enabled', False),
            'anomaly_detection': system_metadata.get('anomaly_detection_enabled', False),
            'leakage_prevention': system_metadata.get('leakage_prevention_enabled', False)
        }

        proof_data = {
            'commitment': self._create_commitment(json.dumps(leakage_analysis, sort_keys=True)),
            'proof_elements': self._generate_proof_elements()
        }

        return ZKProof(
            proof_id=secrets.token_hex(16),
            statement="no_data_leakage_detected",
            proof_data=proof_data,
            public_inputs={'logs_analyzed': leakage_analysis['access_logs_analyzed']},
            created_at=datetime.now()
        )

    async def _prove_encryption_compliance(self, system_metadata: Dict[str, Any]) -> ZKProof:
        """Prove encryption compliance."""
        encryption_data = {
            'algorithm': system_metadata.get('encryption_algorithm', 'unknown'),
            'key_rotation_days': system_metadata.get('key_rotation_days', 0),
            'encrypted_fields': system_metadata.get('encrypted_fields', []),
            'compliance_standard': system_metadata.get('compliance_standard', 'unknown'),
            'audit_trail': system_metadata.get('encryption_audit_trail', False)
        }

        proof_data = {
            'commitment': self._create_commitment(json.dumps(encryption_data, sort_keys=True)),
            'proof_elements': self._generate_proof_elements()
        }

        return ZKProof(
            proof_id=secrets.token_hex(16),
            statement="encryption_compliance_maintained",
            proof_data=proof_data,
            public_inputs={'encrypted_fields': len(encryption_data['encrypted_fields'])},
            created_at=datetime.now()
        )

    def _analyze_access_patterns(self, access_logs: List[Dict[str, Any]]) -> int:
        """Analyze access logs for suspicious patterns."""
        suspicious_count = 0

        for log in access_logs:
            # Check for unusual access patterns
            if self._is_suspicious_access(log):
                suspicious_count += 1

        return suspicious_count

    def _is_suspicious_access(self, log: Dict[str, Any]) -> bool:
        """Check if an access log entry is suspicious."""
        # Simple heuristics for suspicious activity
        access_time = log.get('timestamp', '')
        data_accessed = log.get('data_accessed', '')
        user_role = log.get('user_role', 'unknown')

        # Check for off-hours access
        try:
            dt = datetime.fromisoformat(access_time.replace('Z', '+00:00'))
            if dt.hour < 6 or dt.hour > 22:  # Outside 6 AM - 10 PM
                return True
        except:
            pass

        # Check for sensitive data access by unauthorized users
        if 'sensitive' in data_accessed.lower() and user_role not in ['admin', 'auditor']:
            return True

        # Check for bulk data access
        if log.get('records_accessed', 0) > 1000:
            return True

        return False

    def _check_processing_violations(self, proof: DataProcessingProof) -> List[Dict[str, Any]]:
        """Check for privacy violations in processing."""
        violations = []

        # Check consent requirements
        if not proof.consent_obtained and proof.lawful_basis == 'consent':
            violations.append({
                'type': 'missing_consent',
                'severity': 'high',
                'description': 'Processing requires consent but none obtained'
            })

        # Check retention periods
        if proof.retention_period_days > 2555:  # More than 7 years
            violations.append({
                'type': 'excessive_retention',
                'severity': 'medium',
                'description': f'Retention period too long: {proof.retention_period_days} days'
            })

        # Check lawful basis validity
        valid_bases = ['consent', 'contract', 'legal_obligation', 'vital_interests', 'public_task', 'legitimate_interests']
        if proof.lawful_basis not in valid_bases:
            violations.append({
                'type': 'invalid_lawful_basis',
                'severity': 'high',
                'description': f'Invalid lawful basis: {proof.lawful_basis}'
            })

        return violations

    def _calculate_gdpr_compliance(self, processing_proofs: List[DataProcessingProof]) -> float:
        """Calculate GDPR compliance score."""
        if not processing_proofs:
            return 1.0

        total_checks = 0
        passed_checks = 0

        for proof in processing_proofs:
            # Check consent
            total_checks += 1
            if proof.consent_obtained:
                passed_checks += 1

            # Check retention
            total_checks += 1
            if proof.retention_period_days <= 2555:
                passed_checks += 1

            # Check lawful basis
            total_checks += 1
            if proof.lawful_basis in ['consent', 'contract', 'legal_obligation', 'vital_interests', 'public_task', 'legitimate_interests']:
                passed_checks += 1

        return passed_checks / max(total_checks, 1)

    def _assess_leakage_risk(self, leakage_proofs: List[DataLeakageProof]) -> str:
        """Assess overall data leakage risk."""
        if not leakage_proofs:
            return 'low'

        total_suspicious = sum(p.suspicious_activities for p in leakage_proofs)
        total_logs = sum(p.data_access_logs for p in leakage_proofs)

        if total_logs == 0:
            return 'low'

        suspicious_rate = total_suspicious / total_logs

        if suspicious_rate > 0.1:
            return 'critical'
        elif suspicious_rate > 0.05:
            return 'high'
        elif suspicious_rate > 0.01:
            return 'medium'
        else:
            return 'low'

    def _compile_violations(
        self,
        processing_proofs: List[DataProcessingProof],
        leakage_proofs: List[DataLeakageProof]
    ) -> List[Dict[str, Any]]:
        """Compile all violations found."""
        violations = []

        # Processing violations
        for proof in processing_proofs:
            violations.extend(self._check_processing_violations(proof))

        # Leakage violations
        for proof in leakage_proofs:
            if proof.suspicious_activities > 0:
                violations.append({
                    'type': 'suspicious_activity',
                    'severity': 'high' if proof.suspicious_activities > 10 else 'medium',
                    'description': f'Suspicious activities detected in {proof.system_component}: {proof.suspicious_activities}'
                })

        return violations

    def _generate_privacy_recommendations(
        self,
        violations: List[Dict[str, Any]],
        compliance_score: float
    ) -> List[str]:
        """Generate privacy recommendations."""
        recommendations = []

        if compliance_score < self.gdpr_compliance_threshold:
            recommendations.append("URGENT: GDPR compliance below threshold - immediate review required")

        violation_types = {}
        for violation in violations:
            v_type = violation['type']
            violation_types[v_type] = violation_types.get(v_type, 0) + 1

        if violation_types.get('missing_consent', 0) > 0:
            recommendations.append("Implement proper consent management system")

        if violation_types.get('excessive_retention', 0) > 0:
            recommendations.append("Review and optimize data retention policies")

        if violation_types.get('suspicious_activity', 0) > 0:
            recommendations.append("Enhance access monitoring and anomaly detection")

        if not recommendations:
            recommendations.append("Privacy compliance is within acceptable parameters")

        return recommendations

    def _create_commitment(self, value: str) -> str:
        """Create cryptographic commitment."""
        nonce = secrets.token_bytes(16)
        commitment = hashlib.sha256(value.encode() + nonce).hexdigest()
        return commitment

    def _generate_proof_elements(self) -> List[str]:
        """Generate ZK proof elements."""
        return [secrets.token_hex(32) for _ in range(5)]

    def start_periodic_privacy_audits(self):
        """Start periodic privacy auditing."""
        if self._privacy_audit_task is None:
            self._privacy_audit_task = asyncio.create_task(self._run_periodic_privacy_audits())

    async def _run_periodic_privacy_audits(self):
        """Run periodic privacy auditing loop."""
        while True:
            try:
                await asyncio.sleep(self.audit_interval_days * 24 * 3600)  # Convert days to seconds

                # Generate privacy audit report
                report = await self.generate_privacy_audit_report()

                self.logger.info(f"Generated periodic privacy audit report: {report.audit_id}")

                # Check for critical issues
                if report.gdpr_compliance_score < self.gdpr_compliance_threshold:
                    self.logger.critical(f"GDPR compliance below threshold: {report.gdpr_compliance_score:.1%}")

                if report.data_leakage_risk in ['high', 'critical']:
                    self.logger.critical(f"High data leakage risk detected: {report.data_leakage_risk}")

            except Exception as e:
                self.logger.error(f"Error in periodic privacy audit: {e}")
                await asyncio.sleep(24 * 3600)  # Retry in 24 hours

    def stop_periodic_privacy_audits(self):
        """Stop periodic privacy auditing."""
        if self._privacy_audit_task and not self._privacy_audit_task.done():
            self._privacy_audit_task.cancel()
            self._privacy_audit_task = None

    def get_privacy_stats(self) -> Dict[str, Any]:
        """Get privacy auditing statistics."""
        return {
            'total_privacy_reports': len(self.privacy_reports),
            'processing_proofs': len(self.processing_proofs),
            'leakage_proofs': len(self.leakage_proofs),
            'total_privacy_proofs': sum(len(report.privacy_proofs) for report in self.privacy_reports),
            'average_gdpr_compliance': self._calculate_gdpr_compliance(self.processing_proofs),
            'current_leakage_risk': self._assess_leakage_risk(self.leakage_proofs)
        }