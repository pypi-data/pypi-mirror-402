"""
KYC/AML Integration para AILOOS

Implementa flujos de verificación de identidad, monitoreo de transacciones
y reportes de actividades sospechosas según regulaciones financieras.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import re

logger = logging.getLogger(__name__)


class KYCStatus(Enum):
    """Estados de verificación KYC."""
    NOT_STARTED = "not_started"
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REQUIRES_UPDATE = "requires_update"


class RiskLevel(Enum):
    """Niveles de riesgo para AML."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TransactionType(Enum):
    """Tipos de transacción para monitoreo."""
    DRACMA_TRANSFER = "dracma_transfer"
    FIAT_DEPOSIT = "fiat_deposit"
    FIAT_WITHDRAWAL = "fiat_withdrawal"
    NFT_PURCHASE = "nft_purchase"
    DATA_PURCHASE = "data_purchase"
    STAKING_REWARD = "staking_reward"
    FEDERATED_TRAINING = "federated_training"


class SuspiciousActivityType(Enum):
    """Tipos de actividades sospechosas."""
    UNUSUAL_VOLUME = "unusual_volume"
    FREQUENT_SMALL_TRANSACTIONS = "frequent_small_transactions"
    ROUND_NUMBER_TRANSACTIONS = "round_number_transactions"
    GEOGRAPHIC_ANOMALY = "geographic_anomaly"
    TIME_PATTERN_ANOMALY = "time_pattern_anomaly"
    PEER_ANALYSIS = "peer_analysis"
    SANCTIONS_MATCH = "sanctions_match"
    PEP_ASSOCIATION = "pep_association"


@dataclass
class KYCProfile:
    """Perfil KYC de un usuario."""
    user_id: str
    status: KYCStatus = KYCStatus.NOT_STARTED
    risk_level: RiskLevel = RiskLevel.MEDIUM
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    # Información personal
    personal_info: Dict[str, Any] = field(default_factory=dict)
    documents: List[Dict[str, Any]] = field(default_factory=list)

    # Verificaciones
    identity_verified: bool = False
    address_verified: bool = False
    sanctions_checked: bool = False
    pep_checked: bool = False

    # Metadata
    verification_attempts: int = 0
    last_verification_attempt: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    review_notes: List[str] = field(default_factory=list)

    @property
    def is_active(self) -> bool:
        """Verificar si el perfil KYC está activo."""
        if self.status != KYCStatus.APPROVED:
            return False
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        return True

    @property
    def requires_update(self) -> bool:
        """Verificar si requiere actualización."""
        if not self.expires_at:
            return False
        # Requiere actualización 30 días antes de expirar
        return datetime.now() > (self.expires_at - timedelta(days=30))


@dataclass
class TransactionRecord:
    """Registro de transacción para monitoreo AML."""
    transaction_id: str
    user_id: str
    transaction_type: TransactionType
    amount: float
    currency: str = "DRACMA"
    timestamp: datetime = field(default_factory=datetime.now)

    # Información de origen/destino
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    from_user_id: Optional[str] = None
    to_user_id: Optional[str] = None

    # Metadata adicional
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    geolocation: Optional[Dict[str, Any]] = None
    device_fingerprint: Optional[str] = None

    # Flags de riesgo
    risk_score: float = 0.0
    flagged: bool = False
    suspicious_activities: Set[SuspiciousActivityType] = field(default_factory=set)

    # Estado
    status: str = "completed"  # completed, pending, failed
    blockchain_tx_hash: Optional[str] = None


@dataclass
class SuspiciousActivityReport:
    """Reporte de actividad sospechosa."""
    report_id: str
    user_id: str
    activity_type: SuspiciousActivityType
    severity: RiskLevel
    detected_at: datetime = field(default_factory=datetime.now)
    transactions: List[str] = field(default_factory=list)  # IDs de transacciones
    description: str = ""
    indicators: List[str] = field(default_factory=list)
    status: str = "open"  # open, investigating, closed, false_positive
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None


class KYCManager:
    """
    Gestor de verificación KYC (Know Your Customer).

    Características:
    - Flujos de verificación de identidad
    - Gestión de documentos
    - Evaluación de riesgo
    - Integración con proveedores externos
    """

    def __init__(self):
        self.profiles: Dict[str, KYCProfile] = {}
        self.providers = {
            'identity_verification': self._mock_identity_check,
            'address_verification': self._mock_address_check,
            'sanctions_screening': self._mock_sanctions_check,
            'pep_screening': self._mock_pep_check
        }

        # Estadísticas
        self.stats = {
            'total_profiles': 0,
            'approved_profiles': 0,
            'rejected_profiles': 0,
            'pending_reviews': 0,
            'high_risk_profiles': 0
        }

        logger.info("KYCManager initialized")

    def initiate_kyc_process(self, user_id: str, personal_info: Dict[str, Any]) -> str:
        """Iniciar proceso KYC para un usuario."""
        profile = self.profiles.get(user_id)
        if not profile:
            profile = KYCProfile(user_id=user_id)
            self.profiles[user_id] = profile

        profile.status = KYCStatus.PENDING
        profile.personal_info = personal_info
        profile.updated_at = datetime.now()
        profile.verification_attempts += 1
        profile.last_verification_attempt = datetime.now()

        # Iniciar verificaciones automáticas
        asyncio.create_task(self._run_automated_checks(profile))

        self._update_stats()
        logger.info(f"KYC process initiated for user {user_id}")

        return f"kyc_{user_id}_{int(datetime.now().timestamp())}"

    async def _run_automated_checks(self, profile: KYCProfile):
        """Ejecutar verificaciones automáticas."""
        try:
            # Verificación de identidad
            identity_result = await self.providers['identity_verification'](profile)
            profile.identity_verified = identity_result.get('verified', False)

            # Verificación de dirección
            address_result = await self.providers['address_verification'](profile)
            profile.address_verified = address_result.get('verified', False)

            # Screening de sanciones
            sanctions_result = await self.providers['sanctions_screening'](profile)
            profile.sanctions_checked = True

            # Screening PEP (Politically Exposed Persons)
            pep_result = await self.providers['pep_screening'](profile)
            profile.pep_checked = True

            # Evaluar riesgo
            profile.risk_level = self._assess_risk_level(profile)

            # Determinar estado final
            if profile.identity_verified and profile.address_verified and not sanctions_result.get('flagged'):
                if profile.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]:
                    profile.status = KYCStatus.APPROVED
                    profile.expires_at = datetime.now() + timedelta(days=365)
                else:
                    profile.status = KYCStatus.IN_REVIEW
            else:
                profile.status = KYCStatus.REJECTED
                profile.rejection_reason = "Failed automated verification checks"

            profile.updated_at = datetime.now()
            self._update_stats()

            logger.info(f"KYC automated checks completed for user {profile.user_id}: {profile.status.value}")

        except Exception as e:
            logger.error(f"Error in automated KYC checks for user {profile.user_id}: {e}")
            profile.status = KYCStatus.REJECTED
            profile.rejection_reason = f"Error during verification: {str(e)}"

    def _assess_risk_level(self, profile: KYCProfile) -> RiskLevel:
        """Evaluar nivel de riesgo del perfil."""
        risk_score = 0

        # Factores de riesgo
        if not profile.identity_verified:
            risk_score += 30
        if not profile.address_verified:
            risk_score += 20

        # País de origen (ejemplo simplificado)
        country = profile.personal_info.get('country', '').upper()
        high_risk_countries = ['IR', 'KP', 'SY', 'CU', 'VE']  # Ejemplo
        if country in high_risk_countries:
            risk_score += 40

        # Tipo de actividad
        if profile.personal_info.get('business_type') == 'high_value_goods':
            risk_score += 25

        # Historial de transacciones (simulado)
        # En implementación real, analizar historial real
        if profile.verification_attempts > 3:
            risk_score += 15

        # Determinar nivel
        if risk_score >= 70:
            return RiskLevel.CRITICAL
        elif risk_score >= 40:
            return RiskLevel.HIGH
        elif risk_score >= 20:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    async def _mock_identity_check(self, profile: KYCProfile) -> Dict[str, Any]:
        """Mock de verificación de identidad."""
        await asyncio.sleep(0.1)  # Simular API call
        # En producción, integrar con proveedores como Jumio, Onfido, etc.
        return {
            'verified': True,
            'confidence_score': 0.95,
            'check_date': datetime.now().isoformat()
        }

    async def _mock_address_check(self, profile: KYCProfile) -> Dict[str, Any]:
        """Mock de verificación de dirección."""
        await asyncio.sleep(0.1)
        return {
            'verified': True,
            'address_type': 'residential',
            'check_date': datetime.now().isoformat()
        }

    async def _mock_sanctions_check(self, profile: KYCProfile) -> Dict[str, Any]:
        """Mock de screening de sanciones."""
        await asyncio.sleep(0.1)
        # En producción, usar bases de datos como OFAC, EU Sanctions, etc.
        return {
            'flagged': False,
            'lists_checked': ['OFAC', 'EU_SANCTIONS', 'UN_SANCTIONS'],
            'check_date': datetime.now().isoformat()
        }

    async def _mock_pep_check(self, profile: KYCProfile) -> Dict[str, Any]:
        """Mock de screening PEP."""
        await asyncio.sleep(0.1)
        return {
            'flagged': False,
            'associations_found': [],
            'check_date': datetime.now().isoformat()
        }

    def get_kyc_status(self, user_id: str) -> Dict[str, Any]:
        """Obtener estado KYC de un usuario."""
        profile = self.profiles.get(user_id)
        if not profile:
            return {
                'user_id': user_id,
                'status': KYCStatus.NOT_STARTED.value,
                'is_active': False
            }

        return {
            'user_id': user_id,
            'status': profile.status.value,
            'risk_level': profile.risk_level.value,
            'is_active': profile.is_active,
            'requires_update': profile.requires_update,
            'created_at': profile.created_at.isoformat(),
            'expires_at': profile.expires_at.isoformat() if profile.expires_at else None,
            'identity_verified': profile.identity_verified,
            'address_verified': profile.address_verified,
            'sanctions_checked': profile.sanctions_checked,
            'pep_checked': profile.pep_checked,
            'rejection_reason': profile.rejection_reason
        }

    def _update_stats(self):
        """Actualizar estadísticas."""
        total = len(self.profiles)
        approved = len([p for p in self.profiles.values() if p.status == KYCStatus.APPROVED])
        rejected = len([p for p in self.profiles.values() if p.status == KYCStatus.REJECTED])
        pending = len([p for p in self.profiles.values() if p.status == KYCStatus.PENDING])
        high_risk = len([p for p in self.profiles.values() if p.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]])

        self.stats.update({
            'total_profiles': total,
            'approved_profiles': approved,
            'rejected_profiles': rejected,
            'pending_reviews': pending,
            'high_risk_profiles': high_risk
        })

    def get_kyc_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas KYC."""
        return {
            **self.stats,
            'approval_rate': (self.stats['approved_profiles'] / self.stats['total_profiles'] * 100) if self.stats['total_profiles'] > 0 else 0,
            'generated_at': datetime.now().isoformat()
        }


class AMLMonitor:
    """
    Monitor de actividades AML (Anti-Money Laundering).

    Características:
    - Monitoreo de transacciones
    - Detección de actividades sospechosas
    - Reportes regulatorios
    - Análisis de patrones
    """

    def __init__(self):
        self.transactions: List[TransactionRecord] = []
        self.suspicious_reports: List[SuspiciousActivityReport] = []
        self.risk_thresholds = {
            'daily_volume_limit': 10000,  # DRACMA
            'single_transaction_limit': 5000,
            'frequency_threshold': 10,  # transacciones por hora
            'round_number_penalty': 0.3,  # factor de riesgo para números redondos
        }

        # Estadísticas
        self.stats = {
            'total_transactions': 0,
            'flagged_transactions': 0,
            'suspicious_reports': 0,
            'high_risk_users': set()
        }

        logger.info("AMLMonitor initialized")

    def record_transaction(self, transaction: TransactionRecord):
        """Registrar una transacción para monitoreo."""
        self.transactions.append(transaction)
        self.stats['total_transactions'] += 1

        # Ejecutar análisis de riesgo
        risk_analysis = self._analyze_transaction_risk(transaction)

        transaction.risk_score = risk_analysis['risk_score']
        transaction.suspicious_activities = risk_analysis['suspicious_activities']

        if risk_analysis['flagged']:
            transaction.flagged = True
            self.stats['flagged_transactions'] += 1

            # Crear reporte de actividad sospechosa
            self._create_suspicious_activity_report(transaction, risk_analysis)

        # Mantener tamaño del historial
        if len(self.transactions) > 100000:
            self.transactions = self.transactions[-50000:]

        logger.debug(f"Transaction recorded: {transaction.transaction_id}, risk_score: {transaction.risk_score}")

    def _analyze_transaction_risk(self, transaction: TransactionRecord) -> Dict[str, Any]:
        """Analizar riesgo de una transacción."""
        risk_score = 0.0
        suspicious_activities = set()

        # Análisis de volumen inusual
        if transaction.amount > self.risk_thresholds['single_transaction_limit']:
            risk_score += 40
            suspicious_activities.add(SuspiciousActivityType.UNUSUAL_VOLUME)

        # Análisis de números redondos
        if self._is_round_number(transaction.amount):
            risk_score += self.risk_thresholds['round_number_penalty'] * 100
            suspicious_activities.add(SuspiciousActivityType.ROUND_NUMBER_TRANSACTIONS)

        # Análisis de frecuencia
        recent_transactions = self._get_recent_transactions(transaction.user_id, hours=1)
        if len(recent_transactions) > self.risk_thresholds['frequency_threshold']:
            risk_score += 25
            suspicious_activities.add(SuspiciousActivityType.FREQUENT_SMALL_TRANSACTIONS)

        # Análisis geográfico (simulado)
        if transaction.geolocation:
            if self._is_geographic_anomaly(transaction):
                risk_score += 35
                suspicious_activities.add(SuspiciousActivityType.GEOGRAPHIC_ANOMALY)

        # Análisis de patrones temporales
        if self._detect_time_pattern_anomaly(transaction):
            risk_score += 20
            suspicious_activities.add(SuspiciousActivityType.TIME_PATTERN_ANOMALY)

        # Análisis de peers
        if self._peer_analysis_flagged(transaction):
            risk_score += 30
            suspicious_activities.add(SuspiciousActivityType.PEER_ANALYSIS)

        # Screening de sanciones/PEP (simulado)
        if self._sanctions_pep_check(transaction):
            risk_score += 100  # Alta penalización
            suspicious_activities.add(SuspiciousActivityType.SANCTIONS_MATCH)

        flagged = risk_score >= 50  # Threshold para marcar como sospechosa

        return {
            'risk_score': risk_score,
            'flagged': flagged,
            'suspicious_activities': suspicious_activities
        }

    def _is_round_number(self, amount: float) -> bool:
        """Verificar si el monto es un número redondo."""
        return amount == round(amount) and amount >= 100

    def _get_recent_transactions(self, user_id: str, hours: int) -> List[TransactionRecord]:
        """Obtener transacciones recientes de un usuario."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            t for t in self.transactions[-1000:]  # Últimas 1000 transacciones
            if t.user_id == user_id and t.timestamp > cutoff
        ]

    def _is_geographic_anomaly(self, transaction: TransactionRecord) -> bool:
        """Detectar anomalías geográficas (simulado)."""
        if not transaction.geolocation:
            return False

        # En implementación real, comparar con historial del usuario
        # Por ahora, simular detección aleatoria baja
        import random
        return random.random() < 0.05  # 5% de transacciones marcadas

    def _detect_time_pattern_anomaly(self, transaction: TransactionRecord) -> bool:
        """Detectar anomalías en patrones temporales."""
        # Verificar si es hora inusual (ej: 3 AM)
        hour = transaction.timestamp.hour
        if hour in [2, 3, 4]:  # Horas inusuales
            return True

        # Verificar fines de semana
        if transaction.timestamp.weekday() >= 5:  # Sábado o domingo
            return True

        return False

    def _peer_analysis_flagged(self, transaction: TransactionRecord) -> bool:
        """Análisis de peers (simulado)."""
        # En implementación real, analizar red de transacciones
        # Por ahora, simular detección basada en frecuencia
        recent_count = len(self._get_recent_transactions(transaction.user_id, hours=24))
        return recent_count > 50  # Más de 50 transacciones en 24h

    def _sanctions_pep_check(self, transaction: TransactionRecord) -> bool:
        """Verificación de sanciones/PEP (simulado)."""
        # En implementación real, consultar bases de datos
        # Por ahora, simular detección muy baja
        import random
        return random.random() < 0.001  # 0.1% de transacciones

    def _create_suspicious_activity_report(self, transaction: TransactionRecord, risk_analysis: Dict[str, Any]):
        """Crear reporte de actividad sospechosa."""
        severity = RiskLevel.MEDIUM
        if risk_analysis['risk_score'] >= 80:
            severity = RiskLevel.HIGH
        elif risk_analysis['risk_score'] >= 60:
            severity = RiskLevel.CRITICAL

        report = SuspiciousActivityReport(
            report_id=f"sar_{transaction.transaction_id}",
            user_id=transaction.user_id,
            activity_type=list(risk_analysis['suspicious_activities'])[0],  # Primer tipo detectado
            severity=severity,
            transactions=[transaction.transaction_id],
            description=f"Suspicious transaction detected with risk score {risk_analysis['risk_score']}",
            indicators=list(risk_analysis['suspicious_activities'])
        )

        self.suspicious_reports.append(report)
        self.stats['suspicious_reports'] += 1

        if severity in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            self.stats['high_risk_users'].add(transaction.user_id)

        logger.warning(f"Suspicious activity report created: {report.report_id} for user {transaction.user_id}")

    def get_transaction_risk_report(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Generar reporte de riesgo para un usuario."""
        cutoff = datetime.now() - timedelta(days=days)

        user_transactions = [
            t for t in self.transactions
            if t.user_id == user_id and t.timestamp > cutoff
        ]

        flagged_transactions = [t for t in user_transactions if t.flagged]

        return {
            'user_id': user_id,
            'period_days': days,
            'total_transactions': len(user_transactions),
            'flagged_transactions': len(flagged_transactions),
            'risk_score_avg': sum(t.risk_score for t in user_transactions) / len(user_transactions) if user_transactions else 0,
            'suspicious_activities': list(set(
                activity for t in flagged_transactions
                for activity in t.suspicious_activities
            )),
            'generated_at': datetime.now().isoformat()
        }

    def get_suspicious_activity_reports(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtener reportes de actividades sospechosas."""
        reports = self.suspicious_reports.copy()

        if status:
            reports = [r for r in reports if r.status == status]

        # Ordenar por severidad y fecha
        reports.sort(key=lambda x: (x.severity.value, x.detected_at), reverse=True)

        return [
            {
                'report_id': r.report_id,
                'user_id': r.user_id,
                'activity_type': r.activity_type.value,
                'severity': r.severity.value,
                'detected_at': r.detected_at.isoformat(),
                'status': r.status,
                'description': r.description,
                'indicators': r.indicators
            }
            for r in reports[:limit]
        ]

    def get_aml_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas AML."""
        return {
            **self.stats,
            'high_risk_users_count': len(self.stats['high_risk_users']),
            'flagged_rate': (self.stats['flagged_transactions'] / self.stats['total_transactions'] * 100) if self.stats['total_transactions'] > 0 else 0,
            'generated_at': datetime.now().isoformat()
        }


# Instancias globales
_kyc_manager = KYCManager()
_aml_monitor = AMLMonitor()


def get_kyc_manager() -> KYCManager:
    """Obtener instancia global del KYC manager."""
    return _kyc_manager


def get_aml_monitor() -> AMLMonitor:
    """Obtener instancia global del AML monitor."""
    return _aml_monitor


# Funciones de conveniencia

def initiate_kyc(user_id: str, personal_info: Dict[str, Any]) -> str:
    """Iniciar proceso KYC."""
    return _kyc_manager.initiate_kyc_process(user_id, personal_info)


def get_kyc_status(user_id: str) -> Dict[str, Any]:
    """Obtener estado KYC."""
    return _kyc_manager.get_kyc_status(user_id)


def record_transaction(transaction: TransactionRecord):
    """Registrar transacción para monitoreo AML."""
    _aml_monitor.record_transaction(transaction)


def get_user_risk_report(user_id: str, days: int = 30) -> Dict[str, Any]:
    """Obtener reporte de riesgo de usuario."""
    return _aml_monitor.get_transaction_risk_report(user_id, days)