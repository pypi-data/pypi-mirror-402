"""
DracmaS Token Compliance - Travel Rule & VASP Integration

Implementa compliance para criptomonedas según FATF guidelines:
- Travel Rule para transacciones P2P
- Registro y verificación de VASPs
- Reportes regulatorios de transacciones
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid

logger = logging.getLogger(__name__)


class VASPStatus(Enum):
    """Estados de registro VASP."""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class VASPType(Enum):
    """Tipos de VASP."""
    EXCHANGE = "exchange"
    WALLET_PROVIDER = "wallet_provider"
    OTC_DESK = "otc_desk"
    P2P_PLATFORM = "p2p_platform"
    ATM_OPERATOR = "atm_operator"
    CUSTODY_SERVICE = "custody_service"


class TravelRuleStatus(Enum):
    """Estados del Travel Rule."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING_VERIFICATION = "pending_verification"
    VERIFICATION_FAILED = "verification_failed"
    EXEMPTED = "exempted"


@dataclass
class VASPRegistration:
    """Registro de VASP (Virtual Asset Service Provider)."""
    vasp_id: str
    name: str
    legal_name: str
    registration_number: str
    jurisdiction: str
    vasp_type: VASPType

    # Información de contacto
    email: str
    phone: str
    website: str

    # Información regulatoria
    regulatory_approvals: List[str] = field(default_factory=list)
    compliance_officer: Dict[str, str] = field(default_factory=dict)

    # Estado y metadata
    status: VASPStatus = VASPStatus.PENDING
    registered_at: datetime = field(default_factory=datetime.now)
    approved_at: Optional[datetime] = None
    last_updated: datetime = field(default_factory=datetime.now)

    # Información técnica para Travel Rule
    travel_rule_endpoints: Dict[str, str] = field(default_factory=dict)  # API endpoints
    public_keys: Dict[str, str] = field(default_factory=dict)  # Para verificación

    # Estadísticas
    monthly_volume: float = 0.0
    risk_score: float = 0.0

    @property
    def is_active(self) -> bool:
        """Verificar si el VASP está activo."""
        return self.status == VASPStatus.APPROVED

    @property
    def travel_rule_compliant(self) -> bool:
        """Verificar si soporta Travel Rule."""
        return bool(self.travel_rule_endpoints)


@dataclass
class TravelRuleTransaction:
    """Transacción sujeta a Travel Rule."""
    transaction_id: str
    originator_vasp: str
    beneficiary_vasp: str
    originator_user: Dict[str, Any]  # Información del originador
    beneficiary_user: Dict[str, Any]  # Información del beneficiario

    # Detalles de la transacción
    amount: float
    currency: str = "DRACMA"
    transaction_hash: str = ""  # Ahora tiene valor por defecto
    timestamp: datetime = field(default_factory=datetime.now)

    # Estado del Travel Rule
    status: TravelRuleStatus = TravelRuleStatus.PENDING_VERIFICATION
    verification_attempts: int = 0
    last_verification_attempt: Optional[datetime] = None

    # Información de cumplimiento
    compliance_check_passed: bool = False
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    regulatory_reports: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    exemption_reason: Optional[str] = None
    notes: List[str] = field(default_factory=list)


@dataclass
class RegulatoryReport:
    """Reporte regulatorio de transacciones."""
    report_id: str
    report_type: str  # "monthly", "suspicious_activity", "travel_rule"
    jurisdiction: str
    reporting_period_start: datetime
    reporting_period_end: datetime

    # Contenido del reporte
    transactions: List[Dict[str, Any]] = field(default_factory=list)
    total_volume: float = 0.0
    high_value_transactions: List[Dict[str, Any]] = field(default_factory=list)
    suspicious_activities: List[Dict[str, Any]] = field(default_factory=list)

    # Estado
    status: str = "draft"  # draft, submitted, accepted, rejected
    submitted_at: Optional[datetime] = None
    regulator_response: Optional[str] = None

    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)
    generated_by: str = "ailoos_compliance_system"


class TravelRuleEngine:
    """
    Motor de Travel Rule para transacciones DRACMA.

    Implementa FATF Travel Rule requirements:
    - Recopilación de información del originador y beneficiario
    - Verificación de VASPs
    - Transmisión segura de información
    - Manejo de exenciones
    """

    def __init__(self):
        self.vasps: Dict[str, VASPRegistration] = {}
        self.transactions: List[TravelRuleTransaction] = []
        self.thresholds = {
            'travel_rule_threshold': 1000,  # DracmaS - umbral para Travel Rule
            'high_value_threshold': 10000,  # DracmaS - transacción de alto valor
            'verification_timeout': 24,  # horas para timeout de verificación
        }

        # Estadísticas
        self.stats = {
            'total_transactions': 0,
            'compliant_transactions': 0,
            'non_compliant_transactions': 0,
            'exempted_transactions': 0,
            'verification_failures': 0
        }

        logger.info("TravelRuleEngine initialized")

    def register_vasp(self, registration: VASPRegistration) -> str:
        """Registrar un nuevo VASP."""
        if registration.vasp_id in self.vasps:
            raise ValueError(f"VASP {registration.vasp_id} already registered")

        self.vasps[registration.vasp_id] = registration

        # Iniciar proceso de verificación
        asyncio.create_task(self._verify_vasp_registration(registration))

        logger.info(f"VASP registered: {registration.vasp_id} - {registration.name}")
        return registration.vasp_id

    async def _verify_vasp_registration(self, vasp: VASPRegistration):
        """Verificar registro de VASP (simulado)."""
        await asyncio.sleep(1)  # Simular verificación

        # En producción, verificar:
        # - Documentación regulatoria
        # - Información de contacto
        # - Capacidad técnica
        # - Historial de cumplimiento

        if vasp.jurisdiction in ['US', 'EU', 'UK']:  # Jurisdicciones confiables
            vasp.status = VASPStatus.APPROVED
            vasp.approved_at = datetime.now()
        else:
            vasp.status = VASPStatus.UNDER_REVIEW

        vasp.last_updated = datetime.now()
        logger.info(f"VASP verification completed: {vasp.vasp_id} - {vasp.status.value}")

    def check_travel_rule_required(self, amount: float, originator_vasp: str, beneficiary_vasp: str) -> bool:
        """Verificar si una transacción requiere Travel Rule."""
        # Travel Rule aplica si:
        # 1. Monto supera el umbral
        # 2. Involucra diferentes VASPs
        # 3. No está exenta

        if amount < self.thresholds['travel_rule_threshold']:
            return False

        if originator_vasp == beneficiary_vasp:
            return False  # Misma VASP, no requiere Travel Rule

        return True

    async def process_travel_rule_transaction(self,
                                            transaction_id: str,
                                            originator_vasp: str,
                                            beneficiary_vasp: str,
                                            amount: float,
                                            originator_info: Dict[str, Any],
                                            transaction_hash: str) -> TravelRuleTransaction:
        """Procesar transacción sujeta a Travel Rule."""

        # Verificar si Travel Rule aplica
        if not self.check_travel_rule_required(amount, originator_vasp, beneficiary_vasp):
            # Crear transacción exenta
            transaction = TravelRuleTransaction(
                transaction_id=transaction_id,
                originator_vasp=originator_vasp,
                beneficiary_vasp=beneficiary_vasp,
                originator_user=originator_info,
                beneficiary_user={},  # No requerida para exenciones
                amount=amount,
                transaction_hash=transaction_hash,
                status=TravelRuleStatus.EXEMPTED,
                exemption_reason="Below threshold or same VASP"
            )
            self.transactions.append(transaction)
            self.stats['exempted_transactions'] += 1
            return transaction

        # Verificar VASPs
        originator = self.vasps.get(originator_vasp)
        beneficiary = self.vasps.get(beneficiary_vasp)

        if not originator or not originator.is_active:
            raise ValueError(f"Originator VASP {originator_vasp} not found or inactive")

        if not beneficiary or not beneficiary.is_active:
            raise ValueError(f"Beneficiary VASP {beneficiary_vasp} not found or inactive")

        # Crear transacción Travel Rule
        transaction = TravelRuleTransaction(
            transaction_id=transaction_id,
            originator_vasp=originator_vasp,
            beneficiary_vasp=beneficiary_vasp,
            originator_user=originator_info,
            beneficiary_user={},  # Se obtendrá del beneficiario
            amount=amount,
            transaction_hash=transaction_hash
        )

        self.transactions.append(transaction)
        self.stats['total_transactions'] += 1

        # Iniciar proceso de verificación
        asyncio.create_task(self._verify_travel_rule_compliance(transaction))

        logger.info(f"Travel Rule transaction initiated: {transaction_id}")
        return transaction

    async def _verify_travel_rule_compliance(self, transaction: TravelRuleTransaction):
        """Verificar cumplimiento de Travel Rule."""
        try:
            transaction.verification_attempts += 1
            transaction.last_verification_attempt = datetime.now()

            # Paso 1: Obtener información del beneficiario del VASP destino
            beneficiary_info = await self._request_beneficiary_info(transaction)

            if beneficiary_info:
                transaction.beneficiary_user = beneficiary_info

                # Paso 2: Verificar información requerida
                if self._validate_travel_rule_data(transaction):
                    transaction.status = TravelRuleStatus.COMPLIANT
                    transaction.compliance_check_passed = True
                    self.stats['compliant_transactions'] += 1

                    # Paso 3: Transmitir información al VASP destino
                    await self._transmit_travel_rule_data(transaction)

                else:
                    transaction.status = TravelRuleStatus.NON_COMPLIANT
                    self.stats['non_compliant_transactions'] += 1
            else:
                transaction.status = TravelRuleStatus.VERIFICATION_FAILED
                self.stats['verification_failures'] += 1

        except Exception as e:
            logger.error(f"Travel Rule verification failed for {transaction.transaction_id}: {e}")
            transaction.status = TravelRuleStatus.VERIFICATION_FAILED
            self.stats['verification_failures'] += 1

    async def _request_beneficiary_info(self, transaction: TravelRuleTransaction) -> Optional[Dict[str, Any]]:
        """Solicitar información del beneficiario al VASP destino."""
        beneficiary_vasp = self.vasps.get(transaction.beneficiary_vasp)

        if not beneficiary_vasp or not beneficiary_vasp.travel_rule_compliant:
            return None

        # En producción, hacer API call al endpoint del VASP
        # Simulado para demo
        await asyncio.sleep(0.5)

        # Simular respuesta exitosa
        return {
            'name': 'John Doe',
            'account_id': f'account_{transaction.transaction_id}',
            'verification_status': 'verified',
            'risk_score': 0.2
        }

    def _validate_travel_rule_data(self, transaction: TravelRuleTransaction) -> bool:
        """Validar que la transacción tiene toda la información requerida."""
        required_fields = ['name', 'account_id', 'verification_status']

        originator_valid = all(
            field in transaction.originator_user and transaction.originator_user[field]
            for field in required_fields
        )

        beneficiary_valid = all(
            field in transaction.beneficiary_user and transaction.beneficiary_user[field]
            for field in required_fields
        )

        return originator_valid and beneficiary_valid

    async def _transmit_travel_rule_data(self, transaction: TravelRuleTransaction):
        """Transmitir datos de Travel Rule al VASP destino."""
        beneficiary_vasp = self.vasps.get(transaction.beneficiary_vasp)

        if not beneficiary_vasp:
            return

        # En producción, enviar datos encriptados al endpoint del VASP
        # Simulado para demo
        await asyncio.sleep(0.2)

        logger.info(f"Travel Rule data transmitted to {transaction.beneficiary_vasp} for transaction {transaction.transaction_id}")

    def get_travel_rule_status(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de Travel Rule para una transacción."""
        transaction = next((t for t in self.transactions if t.transaction_id == transaction_id), None)

        if not transaction:
            return None

        return {
            'transaction_id': transaction.transaction_id,
            'status': transaction.status.value,
            'verification_attempts': transaction.verification_attempts,
            'compliance_check_passed': transaction.compliance_check_passed,
            'last_verification_attempt': transaction.last_verification_attempt.isoformat() if transaction.last_verification_attempt else None,
            'exemption_reason': transaction.exemption_reason
        }

    def get_travel_rule_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de Travel Rule."""
        return {
            **self.stats,
            'compliance_rate': (self.stats['compliant_transactions'] / self.stats['total_transactions'] * 100) if self.stats['total_transactions'] > 0 else 0,
            'generated_at': datetime.now().isoformat()
        }


class TransactionReportingEngine:
    """
    Motor de reportes regulatorios para transacciones DRACMA.

    Genera reportes requeridos por reguladores según jurisdicción.
    """

    def __init__(self):
        self.reports: List[RegulatoryReport] = []
        self.reporting_jurisdictions = {
            'US': {'threshold': 3000, 'frequency': 'monthly'},
            'EU': {'threshold': 1000, 'frequency': 'quarterly'},
            'UK': {'threshold': 1000, 'frequency': 'monthly'}
        }

        logger.info("TransactionReportingEngine initialized")

    def generate_monthly_report(self, jurisdiction: str, year: int, month: int) -> RegulatoryReport:
        """Generar reporte mensual para una jurisdicción."""
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)

        report = RegulatoryReport(
            report_id=f"monthly_{jurisdiction}_{year}_{month:02d}",
            report_type="monthly",
            jurisdiction=jurisdiction,
            reporting_period_start=start_date,
            reporting_period_end=end_date
        )

        # En producción, recopilar transacciones reales del período
        # Simulado para demo
        report.transactions = self._get_mock_transactions(start_date, end_date)
        report.total_volume = sum(t['amount'] for t in report.transactions)
        report.high_value_transactions = [
            t for t in report.transactions
            if t['amount'] >= self.reporting_jurisdictions[jurisdiction]['threshold']
        ]

        self.reports.append(report)
        logger.info(f"Monthly report generated: {report.report_id}")

        return report

    def generate_suspicious_activity_report(self, jurisdiction: str, start_date: datetime, end_date: datetime) -> RegulatoryReport:
        """Generar reporte de actividades sospechosas."""
        report = RegulatoryReport(
            report_id=f"sar_{jurisdiction}_{int(start_date.timestamp())}",
            report_type="suspicious_activity",
            jurisdiction=jurisdiction,
            reporting_period_start=start_date,
            reporting_period_end=end_date
        )

        # En producción, obtener de AML monitor
        # Simulado para demo
        report.suspicious_activities = self._get_mock_suspicious_activities(start_date, end_date)

        self.reports.append(report)
        logger.info(f"Suspicious activity report generated: {report.report_id}")

        return report

    def _get_mock_transactions(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Obtener transacciones mock para reporte."""
        # Simular transacciones para demo
        import random
        transactions = []

        for i in range(100):  # 100 transacciones de ejemplo
            transactions.append({
                'transaction_id': f'tx_{i:04d}',
                'timestamp': (start_date + timedelta(days=random.randint(0, 30))).isoformat(),
                'amount': random.uniform(10, 50000),
                'currency': 'DRACMA',
                'originator_vasp': 'ailoos_exchange',
                'beneficiary_vasp': 'external_wallet',
                'travel_rule_compliant': random.choice([True, False])
            })

        return transactions

    def _get_mock_suspicious_activities(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Obtener actividades sospechosas mock."""
        # Simular algunas actividades sospechosas
        return [
            {
                'activity_id': 'sar_001',
                'type': 'unusual_volume',
                'description': 'Large volume transaction from new user',
                'severity': 'medium',
                'transactions': ['tx_0045', 'tx_0067']
            },
            {
                'activity_id': 'sar_002',
                'type': 'geographic_anomaly',
                'description': 'Transaction from unusual geographic location',
                'severity': 'low',
                'transactions': ['tx_0099']
            }
        ]

    def submit_report(self, report_id: str) -> bool:
        """Enviar reporte a regulador (simulado)."""
        report = next((r for r in self.reports if r.report_id == report_id), None)

        if not report:
            return False

        # En producción, enviar a API del regulador
        # Simulado para demo
        report.status = "submitted"
        report.submitted_at = datetime.now()

        logger.info(f"Report submitted: {report_id}")
        return True

    def get_report_status(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de un reporte."""
        report = next((r for r in self.reports if r.report_id == report_id), None)

        if not report:
            return None

        return {
            'report_id': report.report_id,
            'type': report.report_type,
            'jurisdiction': report.jurisdiction,
            'status': report.status,
            'submitted_at': report.submitted_at.isoformat() if report.submitted_at else None,
            'total_transactions': len(report.transactions),
            'total_volume': report.total_volume
        }

    def get_reporting_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de reportes."""
        submitted = len([r for r in self.reports if r.status == "submitted"])
        pending = len([r for r in self.reports if r.status == "draft"])

        return {
            'total_reports': len(self.reports),
            'submitted_reports': submitted,
            'pending_reports': pending,
            'submission_rate': (submitted / len(self.reports) * 100) if self.reports else 0,
            'generated_at': datetime.now().isoformat()
        }


# Instancias globales
_travel_rule_engine = TravelRuleEngine()
_transaction_reporting = TransactionReportingEngine()


def get_travel_rule_engine() -> TravelRuleEngine:
    """Obtener instancia global del Travel Rule engine."""
    return _travel_rule_engine


def get_transaction_reporting_engine() -> TransactionReportingEngine:
    """Obtener instancia global del transaction reporting engine."""
    return _transaction_reporting


# Funciones de conveniencia

def register_vasp(name: str, jurisdiction: str, vasp_type: VASPType, **kwargs) -> str:
    """Registrar un VASP."""
    vasp_id = f"vasp_{uuid.uuid4().hex[:8]}"

    registration = VASPRegistration(
        vasp_id=vasp_id,
        name=name,
        legal_name=kwargs.get('legal_name', name),
        registration_number=kwargs.get('registration_number', f"REG_{jurisdiction}_{uuid.uuid4().hex[:6]}"),
        jurisdiction=jurisdiction,
        vasp_type=vasp_type,
        email=kwargs.get('email', f'compliance@{name.lower().replace(" ", "")}.com'),
        phone=kwargs.get('phone', '+1-555-0123'),
        website=kwargs.get('website', f'https://{name.lower().replace(" ", "")}.com')
    )

    return _travel_rule_engine.register_vasp(registration)


async def process_dracma_transaction(originator_vasp: str,
                                   beneficiary_vasp: str,
                                   amount: float,
                                   originator_info: Dict[str, Any],
                                   transaction_hash: str) -> TravelRuleTransaction:
    """Procesar transacción DracmaS con Travel Rule."""
    transaction_id = f"dracma_tx_{uuid.uuid4().hex}"

    return await _travel_rule_engine.process_travel_rule_transaction(
        transaction_id=transaction_id,
        originator_vasp=originator_vasp,
        beneficiary_vasp=beneficiary_vasp,
        amount=amount,
        originator_info=originator_info,
        transaction_hash=transaction_hash
    )


def generate_monthly_report(jurisdiction: str, year: int, month: int) -> RegulatoryReport:
    """Generar reporte mensual."""
    return _transaction_reporting.generate_monthly_report(jurisdiction, year, month)