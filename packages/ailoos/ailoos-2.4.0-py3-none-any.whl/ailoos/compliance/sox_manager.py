"""
SOXManager - Gestión de compliance SOX para auditoría financiera.

Implementa:
- Controles internos financieros
- Segregación de funciones
- Auditoría de transacciones financieras
- Reportes de controles internos
- Gestión de riesgos financieros
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from sqlalchemy.orm import Session

from ..utils.logging import get_logger

logger = get_logger(__name__)


class ControlType(Enum):
    """Tipos de controles internos."""
    PREVENTIVE = "preventive"
    DETECTIVE = "detective"
    CORRECTIVE = "corrective"


class RiskLevel(Enum):
    """Niveles de riesgo."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TransactionType(Enum):
    """Tipos de transacciones financieras."""
    REVENUE = "revenue"
    EXPENSE = "expense"
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    TRANSFER = "transfer"


@dataclass
class InternalControl:
    """Control interno SOX."""
    control_id: str
    name: str
    description: str
    control_type: ControlType
    owner: str
    frequency: str  # "daily", "weekly", "monthly", "quarterly"
    risk_level: RiskLevel
    is_effective: bool = True
    last_tested: Optional[datetime] = None
    next_test_due: Optional[datetime] = None
    deficiencies: List[str] = field(default_factory=list)
    remediation_plan: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FinancialTransaction:
    """Transacción financiera auditada."""
    transaction_id: str
    transaction_type: TransactionType
    amount: float
    currency: str
    initiator: str
    approver: str
    timestamp: datetime
    description: str
    supporting_docs: List[str] = field(default_factory=list)
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)
    risk_score: float = 0.0
    flags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SegregationOfDuties:
    """Registro de segregación de funciones."""
    sod_id: str
    user_id: str
    roles: List[str]
    conflicting_roles: List[Tuple[str, str]] = field(default_factory=list)
    risk_assessment: str = ""
    mitigation_controls: List[str] = field(default_factory=list)
    last_reviewed: Optional[datetime] = None
    is_compliant: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class SOXManager:
    """
    Gestor de cumplimiento SOX para auditoría financiera.

    Maneja controles internos, segregación de funciones,
    auditoría de transacciones y reportes financieros.
    """

    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session
        self.internal_controls: Dict[str, InternalControl] = {}
        self.financial_transactions: Dict[str, FinancialTransaction] = {}
        self.sod_records: Dict[str, SegregationOfDuties] = {}
        self._initialized = False

    def initialize(self):
        """Inicializar el gestor SOX."""
        if not self._initialized:
            self._load_internal_controls_from_db()
            self._load_financial_transactions_from_db()
            self._load_sod_records_from_db()
            self._initialize_default_controls()
            self._initialized = True
            logger.info("✅ SOXManager inicializado")

    def _initialize_default_controls(self):
        """Inicializar controles internos por defecto."""
        default_controls = [
            {
                "control_id": "access_control",
                "name": "Control de Acceso a Sistemas Financieros",
                "description": "Asegura que solo usuarios autorizados accedan a sistemas financieros",
                "control_type": ControlType.PREVENTIVE,
                "owner": "IT Security",
                "frequency": "monthly",
                "risk_level": RiskLevel.HIGH
            },
            {
                "control_id": "transaction_approval",
                "name": "Aprobación de Transacciones",
                "description": "Requiere aprobación dual para transacciones significativas",
                "control_type": ControlType.PREVENTIVE,
                "owner": "Finance",
                "frequency": "daily",
                "risk_level": RiskLevel.CRITICAL
            },
            {
                "control_id": "reconciliation",
                "name": "Conciliación de Cuentas",
                "description": "Verifica la exactitud de balances y transacciones",
                "control_type": ControlType.DETECTIVE,
                "owner": "Accounting",
                "frequency": "monthly",
                "risk_level": RiskLevel.HIGH
            }
        ]

        for control_data in default_controls:
            if control_data["control_id"] not in self.internal_controls:
                control = InternalControl(**control_data)
                self.internal_controls[control.control_id] = control
                self._save_control_to_db(control)

    def _load_internal_controls_from_db(self):
        """Cargar controles internos desde DB."""
        # TODO: Implementar carga desde DB
        pass

    def _load_financial_transactions_from_db(self):
        """Cargar transacciones financieras desde DB."""
        # TODO: Implementar carga desde DB
        pass

    def _load_sod_records_from_db(self):
        """Cargar registros SOD desde DB."""
        # TODO: Implementar carga desde DB
        pass

    def record_financial_transaction(self, transaction_type: TransactionType, amount: float,
                                   currency: str, initiator: str, description: str,
                                   supporting_docs: Optional[List[str]] = None) -> str:
        """
        Registrar transacción financiera.

        Args:
            transaction_type: Tipo de transacción
            amount: Monto
            currency: Moneda
            initiator: Usuario que inicia
            description: Descripción
            supporting_docs: Documentos de soporte

        Returns:
            ID de la transacción
        """
        transaction_id = f"fin_tx_{transaction_type.value}_{datetime.now().timestamp()}"

        # Calcular riesgo de la transacción
        risk_score = self._calculate_transaction_risk(amount, transaction_type, initiator)

        # Verificar controles
        flags = self._check_transaction_controls(transaction_type, amount, initiator)

        transaction = FinancialTransaction(
            transaction_id=transaction_id,
            transaction_type=transaction_type,
            amount=amount,
            currency=currency,
            initiator=initiator,
            approver="",  # Se asignará después
            timestamp=datetime.now(),
            description=description,
            supporting_docs=supporting_docs or [],
            risk_score=risk_score,
            flags=flags
        )

        # Agregar al audit trail inicial
        transaction.audit_trail.append({
            "action": "created",
            "user": initiator,
            "timestamp": datetime.now().isoformat(),
            "details": "Transaction initiated"
        })

        self.financial_transactions[transaction_id] = transaction
        self._save_transaction_to_db(transaction)

        logger.info(f"💰 Financial transaction recorded: {transaction_id} (${amount} {currency})")
        return transaction_id

    def approve_transaction(self, transaction_id: str, approver: str) -> bool:
        """
        Aprobar transacción financiera.

        Args:
            transaction_id: ID de la transacción
            approver: Usuario que aprueba

        Returns:
            True si aprobada exitosamente
        """
        if transaction_id not in self.financial_transactions:
            logger.error(f"Transaction not found: {transaction_id}")
            return False

        transaction = self.financial_transactions[transaction_id]

        # Verificar segregación de funciones
        if not self._check_segregation_of_duties(transaction.initiator, approver):
            logger.warning(f"SoD violation: {transaction.initiator} cannot approve own transaction")
            transaction.flags.append("sod_violation")
            self._save_transaction_to_db(transaction)
            return False

        transaction.approver = approver
        transaction.audit_trail.append({
            "action": "approved",
            "user": approver,
            "timestamp": datetime.now().isoformat(),
            "details": "Transaction approved"
        })

        self._update_transaction_in_db(transaction)
        logger.info(f"✅ Transaction approved: {transaction_id} by {approver}")
        return True

    def test_internal_control(self, control_id: str, tester: str, result: bool,
                           deficiencies: Optional[List[str]] = None,
                           remediation_plan: str = "") -> bool:
        """
        Probar control interno.

        Args:
            control_id: ID del control
            tester: Usuario que prueba
            result: Resultado de la prueba
            deficiencies: Deficiencias encontradas
            remediation_plan: Plan de remediación

        Returns:
            True si la prueba fue registrada
        """
        if control_id not in self.internal_controls:
            logger.error(f"Control not found: {control_id}")
            return False

        control = self.internal_controls[control_id]
        control.last_tested = datetime.now()
        control.is_effective = result
        control.deficiencies = deficiencies or []
        control.remediation_plan = remediation_plan

        # Calcular próxima fecha de prueba
        control.next_test_due = self._calculate_next_test_date(control.frequency)

        self._update_control_in_db(control)

        status = "PASSED" if result else "FAILED"
        logger.info(f"🧪 Control test {status}: {control_id} by {tester}")
        return True

    def assess_segregation_of_duties(self, user_id: str, roles: List[str]) -> SegregationOfDuties:
        """
        Evaluar segregación de funciones para un usuario.

        Args:
            user_id: ID del usuario
            roles: Roles asignados

        Returns:
            Registro de evaluación SOD
        """
        sod_id = f"sod_{user_id}_{datetime.now().timestamp()}"

        # Identificar conflictos
        conflicting_roles = self._identify_role_conflicts(roles)

        # Evaluar riesgo
        risk_assessment = self._assess_sod_risk(conflicting_roles)

        # Controles de mitigación
        mitigation_controls = self._suggest_mitigation_controls(conflicting_roles)

        sod_record = SegregationOfDuties(
            sod_id=sod_id,
            user_id=user_id,
            roles=roles,
            conflicting_roles=conflicting_roles,
            risk_assessment=risk_assessment,
            mitigation_controls=mitigation_controls,
            last_reviewed=datetime.now(),
            is_compliant=len(conflicting_roles) == 0
        )

        self.sod_records[sod_id] = sod_record
        self._save_sod_record_to_db(sod_record)

        compliance_status = "COMPLIANT" if sod_record.is_compliant else "NON-COMPLIANT"
        logger.info(f"🔍 SoD assessment {compliance_status}: {user_id}")
        return sod_record

    def generate_control_report(self, date_from: Optional[datetime] = None,
                              date_to: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Generar reporte de controles internos.

        Args:
            date_from: Fecha desde
            date_to: Fecha hasta

        Returns:
            Reporte de controles
        """
        if not date_from:
            date_from = datetime.now() - timedelta(days=90)
        if not date_to:
            date_to = datetime.now()

        report = {
            "report_period": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat()
            },
            "controls_summary": {
                "total": len(self.internal_controls),
                "effective": sum(1 for c in self.internal_controls.values() if c.is_effective),
                "ineffective": sum(1 for c in self.internal_controls.values() if not c.is_effective)
            },
            "controls": [],
            "high_risk_issues": []
        }

        for control in self.internal_controls.values():
            control_data = {
                "control_id": control.control_id,
                "name": control.name,
                "type": control.control_type.value,
                "owner": control.owner,
                "frequency": control.frequency,
                "risk_level": control.risk_level.value,
                "is_effective": control.is_effective,
                "last_tested": control.last_tested.isoformat() if control.last_tested else None,
                "deficiencies": control.deficiencies,
                "remediation_plan": control.remediation_plan
            }
            report["controls"].append(control_data)

            # Identificar issues de alto riesgo
            if not control.is_effective and control.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                report["high_risk_issues"].append({
                    "control_id": control.control_id,
                    "issue": "Control ineffective",
                    "risk_level": control.risk_level.value,
                    "deficiencies": control.deficiencies
                })

        return report

    def audit_transaction_trail(self, transaction_id: Optional[str] = None,
                               initiator: Optional[str] = None,
                               date_from: Optional[datetime] = None,
                               date_to: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Auditar trail de transacciones.

        Args:
            transaction_id: Filtrar por transacción específica
            initiator: Filtrar por iniciador
            date_from: Fecha desde
            date_to: Fecha hasta

        Returns:
            Lista de transacciones auditadas
        """
        results = []

        for tx in self.financial_transactions.values():
            # Aplicar filtros
            if transaction_id and tx.transaction_id != transaction_id:
                continue
            if initiator and tx.initiator != initiator:
                continue
            if date_from and tx.timestamp < date_from:
                continue
            if date_to and tx.timestamp > date_to:
                continue

            results.append({
                "transaction_id": tx.transaction_id,
                "type": tx.transaction_type.value,
                "amount": tx.amount,
                "currency": tx.currency,
                "initiator": tx.initiator,
                "approver": tx.approver,
                "timestamp": tx.timestamp.isoformat(),
                "description": tx.description,
                "risk_score": tx.risk_score,
                "flags": tx.flags,
                "audit_trail": tx.audit_trail
            })

        return sorted(results, key=lambda x: x["timestamp"], reverse=True)

    def _calculate_transaction_risk(self, amount: float, tx_type: TransactionType, initiator: str) -> float:
        """Calcular puntuación de riesgo de transacción."""
        risk_score = 0.0

        # Riesgo por monto
        if amount > 100000:
            risk_score += 0.8
        elif amount > 10000:
            risk_score += 0.4
        elif amount > 1000:
            risk_score += 0.2

        # Riesgo por tipo
        high_risk_types = [TransactionType.EQUITY, TransactionType.TRANSFER]
        if tx_type in high_risk_types:
            risk_score += 0.3

        # TODO: Agregar factores adicionales como historial del usuario

        return min(risk_score, 1.0)  # Máximo 1.0

    def _check_transaction_controls(self, tx_type: TransactionType, amount: float, initiator: str) -> List[str]:
        """Verificar controles aplicables a la transacción."""
        flags = []

        # Control de aprobación dual para montos altos
        if amount > 50000 and tx_type in [TransactionType.EXPENSE, TransactionType.ASSET]:
            flags.append("dual_approval_required")

        # Control de documentación
        if amount > 10000 and tx_type == TransactionType.REVENUE:
            flags.append("supporting_docs_required")

        return flags

    def _check_segregation_of_duties(self, initiator: str, approver: str) -> bool:
        """Verificar segregación de funciones."""
        # Regla básica: el iniciador no puede aprobar su propia transacción
        return initiator != approver

    def _identify_role_conflicts(self, roles: List[str]) -> List[Tuple[str, str]]:
        """Identificar conflictos entre roles."""
        conflicts = []

        # Definir conflictos conocidos
        conflict_matrix = {
            ("accountant", "approver"): "Cannot both record and approve transactions",
            ("initiator", "approver"): "Cannot both initiate and approve transactions",
            ("custodian", "reconciler"): "Cannot both custody assets and reconcile accounts"
        }

        for i, role1 in enumerate(roles):
            for role2 in roles[i+1:]:
                conflict_key = tuple(sorted([role1, role2]))
                if conflict_key in conflict_matrix:
                    conflicts.append((role1, role2))

        return conflicts

    def _assess_sod_risk(self, conflicts: List[Tuple[str, str]]) -> str:
        """Evaluar riesgo de conflictos SOD."""
        if not conflicts:
            return "LOW - No conflicts detected"

        high_risk_conflicts = [
            ("accountant", "approver"),
            ("custodian", "reconciler")
        ]

        for conflict in conflicts:
            if tuple(sorted(conflict)) in high_risk_conflicts:
                return "HIGH - Critical segregation violation"

        return "MEDIUM - Segregation concerns identified"

    def _suggest_mitigation_controls(self, conflicts: List[Tuple[str, str]]) -> List[str]:
        """Sugerir controles de mitigación."""
        suggestions = []

        for conflict in conflicts:
            if "approver" in conflict:
                suggestions.append("Implement dual authorization requirement")
            if "custodian" in conflict:
                suggestions.append("Implement periodic independent reviews")
            suggestions.append("Conduct regular access reviews")

        return list(set(suggestions))  # Remover duplicados

    def _calculate_next_test_date(self, frequency: str) -> datetime:
        """Calcular próxima fecha de prueba."""
        now = datetime.now()

        if frequency == "daily":
            return now + timedelta(days=1)
        elif frequency == "weekly":
            return now + timedelta(weeks=1)
        elif frequency == "monthly":
            return now + timedelta(days=30)
        elif frequency == "quarterly":
            return now + timedelta(days=90)
        else:
            return now + timedelta(days=30)  # Default mensual

    def _save_control_to_db(self, control: InternalControl):
        """Guardar control en DB."""
        # TODO: Implementar persistencia
        pass

    def _update_control_in_db(self, control: InternalControl):
        """Actualizar control en DB."""
        # TODO: Implementar actualización
        pass

    def _save_transaction_to_db(self, transaction: FinancialTransaction):
        """Guardar transacción en DB."""
        # TODO: Implementar persistencia
        pass

    def _update_transaction_in_db(self, transaction: FinancialTransaction):
        """Actualizar transacción en DB."""
        # TODO: Implementar actualización
        pass

    def _save_sod_record_to_db(self, sod_record: SegregationOfDuties):
        """Guardar registro SOD en DB."""
        # TODO: Implementar persistencia
        pass