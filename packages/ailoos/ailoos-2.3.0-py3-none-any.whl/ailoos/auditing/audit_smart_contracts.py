"""
Smart contracts para validación automática de operaciones críticas en AILOOS.
Implementa contratos inteligentes en Python para validación automática de compliance.
"""

import hashlib
import json
import time
from typing import Dict, Any, List, Optional, Callable, Protocol
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from enum import Enum
import threading

from ..core.logging import get_logger

logger = get_logger(__name__)


class ContractState(Enum):
    """Estados posibles de un contrato inteligente."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    TERMINATED = "terminated"


@dataclass
class ContractExecution:
    """Resultado de ejecución de contrato."""
    contract_id: str
    operation_id: str
    success: bool
    result: Any
    gas_used: int
    timestamp: float
    events: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.events is None:
            self.events = []


class SmartContract(ABC):
    """Clase base para contratos inteligentes."""

    def __init__(self, contract_id: str, owner: str):
        self.contract_id = contract_id
        self.owner = owner
        self.state = ContractState.DRAFT
        self.created_at = time.time()
        self.last_executed = None
        self.execution_count = 0
        self.total_gas_used = 0

    @abstractmethod
    async def execute(self, operation: Dict[str, Any], **kwargs) -> ContractExecution:
        """Ejecuta la lógica del contrato."""
        pass

    def get_contract_info(self) -> Dict[str, Any]:
        """Obtiene información del contrato."""
        return {
            "contract_id": self.contract_id,
            "owner": self.owner,
            "state": self.state.value,
            "created_at": self.created_at,
            "last_executed": self.last_executed,
            "execution_count": self.execution_count,
            "total_gas_used": self.total_gas_used
        }


class ComplianceValidationContract(SmartContract):
    """
    Contrato para validación automática de compliance en operaciones.
    Verifica reglas de cumplimiento normativo.
    """

    def __init__(self, contract_id: str, owner: str, compliance_rules: List[Dict[str, Any]]):
        super().__init__(contract_id, owner)
        self.compliance_rules = compliance_rules
        self.violations_log = []

    async def execute(self, operation: Dict[str, Any], **kwargs) -> ContractExecution:
        """Valida compliance de la operación."""
        start_time = time.time()
        gas_used = 100  # Gas base

        violations = []
        compliance_score = 100

        # Validar cada regla
        for rule in self.compliance_rules:
            rule_type = rule.get("type")
            gas_used += 50

            if rule_type == "data_retention":
                # Verificar retención de datos
                if not self._check_data_retention(operation, rule):
                    violations.append({
                        "rule": rule["id"],
                        "type": "data_retention_violation",
                        "severity": rule.get("severity", "medium")
                    })
                    compliance_score -= rule.get("penalty", 20)

            elif rule_type == "privacy_consent":
                # Verificar consentimiento de privacidad
                if not self._check_privacy_consent(operation, rule):
                    violations.append({
                        "rule": rule["id"],
                        "type": "privacy_consent_violation",
                        "severity": rule.get("severity", "high")
                    })
                    compliance_score -= rule.get("penalty", 30)

            elif rule_type == "audit_trail":
                # Verificar registro de auditoría
                if not self._check_audit_trail(operation, rule):
                    violations.append({
                        "rule": rule["id"],
                        "type": "audit_trail_violation",
                        "severity": rule.get("severity", "high")
                    })
                    compliance_score -= rule.get("penalty", 25)

            elif rule_type == "access_control":
                # Verificar control de acceso
                if not self._check_access_control(operation, rule):
                    violations.append({
                        "rule": rule["id"],
                        "type": "access_control_violation",
                        "severity": rule.get("severity", "critical")
                    })
                    compliance_score -= rule.get("penalty", 50)

        # Registrar violaciones si existen
        if violations:
            self.violations_log.append({
                "operation_id": operation.get("operation_id"),
                "timestamp": time.time(),
                "violations": violations,
                "compliance_score": max(0, compliance_score)
            })

        # Crear eventos
        events = []
        if violations:
            events.append({
                "event": "ComplianceViolation",
                "operation_id": operation.get("operation_id"),
                "violations_count": len(violations),
                "compliance_score": max(0, compliance_score)
            })

        # Actualizar estadísticas
        self.execution_count += 1
        self.last_executed = time.time()
        self.total_gas_used += gas_used

        result = {
            "compliant": len(violations) == 0,
            "compliance_score": max(0, compliance_score),
            "violations": violations,
            "rules_checked": len(self.compliance_rules)
        }

        return ContractExecution(
            contract_id=self.contract_id,
            operation_id=operation.get("operation_id", "unknown"),
            success=len(violations) == 0,
            result=result,
            gas_used=gas_used,
            timestamp=time.time(),
            events=events
        )

    def _check_data_retention(self, operation: Dict[str, Any], rule: Dict[str, Any]) -> bool:
        """Verifica reglas de retención de datos."""
        data_type = operation.get("data", {}).get("type")
        retention_days = rule.get("retention_days", 2555)  # 7 años por defecto

        # Lógica simplificada - en producción sería más compleja
        if data_type in ["personal_data", "health_data"]:
            return operation.get("retention_policy", {}).get("max_days", 0) <= retention_days

        return True

    def _check_privacy_consent(self, operation: Dict[str, Any], rule: Dict[str, Any]) -> bool:
        """Verifica consentimiento de privacidad."""
        user_id = operation.get("user_id")
        data_processing = operation.get("data_processing", [])

        # Verificar que el usuario haya dado consentimiento
        required_consents = rule.get("required_consents", [])
        user_consents = operation.get("user_consents", [])

        for consent in required_consents:
            if consent not in user_consents:
                return False

        return True

    def _check_audit_trail(self, operation: Dict[str, Any], rule: Dict[str, Any]) -> bool:
        """Verifica registro de auditoría."""
        # Verificar que la operación tenga campos requeridos de auditoría
        required_fields = ["operation_id", "user_id", "timestamp", "operation_type"]

        for field in required_fields:
            if field not in operation:
                return False

        # Verificar que tenga hash de integridad
        if "data_hash" not in operation:
            return False

        return True

    def _check_access_control(self, operation: Dict[str, Any], rule: Dict[str, Any]) -> bool:
        """Verifica control de acceso."""
        user_role = operation.get("user_role", "user")
        operation_type = operation.get("operation_type", "")
        required_role = rule.get("required_role", "user")

        # Lógica simplificada de control de acceso basado en roles
        role_hierarchy = {
            "admin": 100,
            "auditor": 80,
            "manager": 60,
            "user": 40,
            "guest": 20
        }

        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 100)

        return user_level >= required_level


class AuditTrailContract(SmartContract):
    """
    Contrato para gestión automática de audit trails.
    Asegura que todas las operaciones críticas sean registradas.
    """

    def __init__(self, contract_id: str, owner: str, required_fields: List[str]):
        super().__init__(contract_id, owner)
        self.required_fields = required_fields
        self.audit_log = []

    async def execute(self, operation: Dict[str, Any], **kwargs) -> ContractExecution:
        """Ejecuta validación de audit trail."""
        gas_used = 50
        missing_fields = []
        validation_errors = []

        # Verificar campos requeridos
        for field in self.required_fields:
            gas_used += 10
            if field not in operation:
                missing_fields.append(field)
                validation_errors.append(f"Missing required field: {field}")

        # Verificar formato de timestamp
        if "timestamp" in operation:
            try:
                ts = operation["timestamp"]
                if isinstance(ts, str):
                    # Intentar parsear
                    time.strptime(ts, "%Y-%m-%d %H:%M:%S")
                elif not isinstance(ts, (int, float)):
                    validation_errors.append("Invalid timestamp format")
            except:
                validation_errors.append("Invalid timestamp format")

        # Verificar operation_id único
        operation_id = operation.get("operation_id")
        if operation_id:
            # En producción, verificar contra base de datos
            if any(log.get("operation_id") == operation_id for log in self.audit_log):
                validation_errors.append("Duplicate operation_id")

        # Calcular hash de integridad
        operation_copy = operation.copy()
        operation_copy.pop("data_hash", None)  # Remover hash existente para recalcular
        data_str = json.dumps(operation_copy, sort_keys=True, default=str)
        calculated_hash = hashlib.sha256(data_str.encode()).hexdigest()

        if "data_hash" in operation and operation["data_hash"] != calculated_hash:
            validation_errors.append("Data integrity hash mismatch")

        # Registrar en audit log si válido
        is_valid = len(validation_errors) == 0
        if is_valid:
            audit_entry = {
                "operation_id": operation_id,
                "timestamp": time.time(),
                "operation_hash": calculated_hash,
                "validated_by": self.contract_id
            }
            self.audit_log.append(audit_entry)

        # Crear eventos
        events = []
        if validation_errors:
            events.append({
                "event": "AuditValidationFailed",
                "operation_id": operation_id,
                "errors": validation_errors
            })
        else:
            events.append({
                "event": "AuditTrailValidated",
                "operation_id": operation_id,
                "hash": calculated_hash
            })

        # Actualizar estadísticas
        self.execution_count += 1
        self.last_executed = time.time()
        self.total_gas_used += gas_used

        result = {
            "valid": is_valid,
            "missing_fields": missing_fields,
            "validation_errors": validation_errors,
            "calculated_hash": calculated_hash
        }

        return ContractExecution(
            contract_id=self.contract_id,
            operation_id=operation_id or "unknown",
            success=is_valid,
            result=result,
            gas_used=gas_used,
            timestamp=time.time(),
            events=events
        )


class RiskAssessmentContract(SmartContract):
    """
    Contrato para evaluación automática de riesgos.
    Calcula niveles de riesgo para operaciones críticas.
    """

    def __init__(self, contract_id: str, owner: str, risk_rules: List[Dict[str, Any]]):
        super().__init__(contract_id, owner)
        self.risk_rules = risk_rules
        self.risk_assessments = []

    async def execute(self, operation: Dict[str, Any], **kwargs) -> ContractExecution:
        """Ejecuta evaluación de riesgo."""
        gas_used = 75
        risk_score = 0
        risk_factors = []

        # Evaluar cada regla de riesgo
        for rule in self.risk_rules:
            gas_used += 25
            rule_type = rule.get("type")

            if rule_type == "user_behavior":
                # Evaluar comportamiento del usuario
                user_risk = self._assess_user_behavior(operation, rule)
                risk_score += user_risk.get("score", 0)
                if user_risk.get("factors"):
                    risk_factors.extend(user_risk["factors"])

            elif rule_type == "operation_sensitivity":
                # Evaluar sensibilidad de la operación
                op_risk = self._assess_operation_sensitivity(operation, rule)
                risk_score += op_risk.get("score", 0)
                if op_risk.get("factors"):
                    risk_factors.extend(op_risk["factors"])

            elif rule_type == "data_volume":
                # Evaluar volumen de datos
                data_risk = self._assess_data_volume(operation, rule)
                risk_score += data_risk.get("score", 0)
                if data_risk.get("factors"):
                    risk_factors.extend(data_risk["factors"])

        # Determinar nivel de riesgo
        risk_level = self._calculate_risk_level(risk_score)

        # Registrar evaluación
        assessment = {
            "operation_id": operation.get("operation_id"),
            "timestamp": time.time(),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors
        }
        self.risk_assessments.append(assessment)

        # Crear eventos
        events = [{
            "event": "RiskAssessmentCompleted",
            "operation_id": operation.get("operation_id"),
            "risk_level": risk_level,
            "risk_score": risk_score
        }]

        # Actualizar estadísticas
        self.execution_count += 1
        self.last_executed = time.time()
        self.total_gas_used += gas_used

        result = {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "assessment_id": f"risk_{len(self.risk_assessments)}"
        }

        return ContractExecution(
            contract_id=self.contract_id,
            operation_id=operation.get("operation_id", "unknown"),
            success=True,  # Risk assessment always succeeds
            result=result,
            gas_used=gas_used,
            timestamp=time.time(),
            events=events
        )

    def _assess_user_behavior(self, operation: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa comportamiento del usuario."""
        user_id = operation.get("user_id", "")
        operation_type = operation.get("operation_type", "")

        score = 0
        factors = []

        # Lógica simplificada - en producción usaría ML/models
        if operation_type in ["delete_data", "export_data"]:
            score += rule.get("high_risk_penalty", 30)
            factors.append("High-risk operation type")

        # Verificar frecuencia de operaciones
        # En producción, consultar historial del usuario
        recent_ops = operation.get("recent_operations_count", 0)
        if recent_ops > rule.get("suspicious_threshold", 100):
            score += rule.get("frequency_penalty", 20)
            factors.append("High operation frequency")

        return {"score": score, "factors": factors}

    def _assess_operation_sensitivity(self, operation: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa sensibilidad de la operación."""
        data_types = operation.get("data_types", [])
        operation_type = operation.get("operation_type", "")

        score = 0
        factors = []

        sensitive_data_types = rule.get("sensitive_data_types", ["personal", "health", "financial"])
        for data_type in data_types:
            if data_type in sensitive_data_types:
                score += rule.get("sensitivity_penalty", 25)
                factors.append(f"Sensitive data type: {data_type}")

        high_risk_operations = rule.get("high_risk_operations", ["bulk_delete", "system_config"])
        if operation_type in high_risk_operations:
            score += rule.get("operation_penalty", 35)
            factors.append(f"High-risk operation: {operation_type}")

        return {"score": score, "factors": factors}

    def _assess_data_volume(self, operation: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa volumen de datos."""
        data_volume = operation.get("data_volume", 0)

        score = 0
        factors = []

        if data_volume > rule.get("large_volume_threshold", 1000000):  # 1M records
            score += rule.get("volume_penalty", 20)
            factors.append("Large data volume operation")

        return {"score": score, "factors": factors}

    def _calculate_risk_level(self, score: int) -> str:
        """Calcula nivel de riesgo basado en score."""
        if score >= 80:
            return "critical"
        elif score >= 60:
            return "high"
        elif score >= 40:
            return "medium"
        elif score >= 20:
            return "low"
        else:
            return "minimal"


class SmartContractManager:
    """
    Gestor de contratos inteligentes para auditoría.
    Administra el ciclo de vida y ejecución de contratos.
    """

    def __init__(self):
        self.contracts: Dict[str, SmartContract] = {}
        self.execution_history: List[ContractExecution] = []
        self.lock = threading.Lock()

        # Crear contratos por defecto
        self._initialize_default_contracts()

        logger.info(f"📋 SmartContractManager initialized with {len(self.contracts)} contracts")

    def _initialize_default_contracts(self):
        """Inicializa contratos por defecto."""
        # Contrato de compliance
        compliance_rules = [
            {
                "id": "gdpr_data_retention",
                "type": "data_retention",
                "retention_days": 2555,
                "severity": "high",
                "penalty": 30
            },
            {
                "id": "privacy_consent_required",
                "type": "privacy_consent",
                "required_consents": ["data_processing", "analytics"],
                "severity": "critical",
                "penalty": 50
            },
            {
                "id": "audit_trail_mandatory",
                "type": "audit_trail",
                "severity": "high",
                "penalty": 25
            },
            {
                "id": "admin_access_control",
                "type": "access_control",
                "required_role": "admin",
                "severity": "critical",
                "penalty": 100
            }
        ]

        self.contracts["compliance_validator"] = ComplianceValidationContract(
            "compliance_validator",
            "system",
            compliance_rules
        )

        # Contrato de audit trail
        audit_fields = ["operation_id", "user_id", "timestamp", "operation_type", "data_hash"]
        self.contracts["audit_trail_enforcer"] = AuditTrailContract(
            "audit_trail_enforcer",
            "system",
            audit_fields
        )

        # Contrato de evaluación de riesgo
        risk_rules = [
            {
                "type": "user_behavior",
                "high_risk_penalty": 30,
                "frequency_penalty": 20,
                "suspicious_threshold": 100
            },
            {
                "type": "operation_sensitivity",
                "sensitive_data_types": ["personal", "health", "financial"],
                "sensitivity_penalty": 25,
                "high_risk_operations": ["bulk_delete", "system_config"],
                "operation_penalty": 35
            },
            {
                "type": "data_volume",
                "large_volume_threshold": 1000000,
                "volume_penalty": 20
            }
        ]

        self.contracts["risk_assessor"] = RiskAssessmentContract(
            "risk_assessor",
            "system",
            risk_rules
        )

        # Activar contratos por defecto
        for contract in self.contracts.values():
            contract.state = ContractState.ACTIVE

    async def execute_contract(self, contract_id: str, operation: Dict[str, Any],
                              **kwargs) -> Optional[ContractExecution]:
        """
        Ejecuta un contrato específico.

        Args:
            contract_id: ID del contrato
            operation: Operación a validar
            **kwargs: Parámetros adicionales

        Returns:
            Resultado de ejecución o None si el contrato no existe
        """
        contract = self.contracts.get(contract_id)
        if not contract or contract.state != ContractState.ACTIVE:
            return None

        execution = await contract.execute(operation, **kwargs)

        with self.lock:
            self.execution_history.append(execution)

        logger.debug(f"⚡ Executed contract {contract_id} for operation {operation.get('operation_id', 'unknown')}: {execution.success}")

        return execution

    async def execute_all_contracts(self, operation: Dict[str, Any]) -> List[ContractExecution]:
        """
        Ejecuta todos los contratos activos sobre una operación.

        Args:
            operation: Operación a validar

        Returns:
            Lista de resultados de ejecución
        """
        executions = []

        for contract_id, contract in self.contracts.items():
            if contract.state == ContractState.ACTIVE:
                execution = await self.execute_contract(contract_id, operation)
                if execution:
                    executions.append(execution)

        return executions

    def get_contract_info(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene información de un contrato."""
        contract = self.contracts.get(contract_id)
        return contract.get_contract_info() if contract else None

    def get_all_contracts_info(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene información de todos los contratos."""
        return {cid: contract.get_contract_info() for cid, contract in self.contracts.items()}

    def get_execution_history(self, contract_id: Optional[str] = None,
                            limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtiene historial de ejecuciones.

        Args:
            contract_id: Filtrar por contrato específico (opcional)
            limit: Número máximo de resultados

        Returns:
            Lista de ejecuciones
        """
        history = self.execution_history

        if contract_id:
            history = [exec for exec in history if exec.contract_id == contract_id]

        # Ordenar por timestamp descendente
        history.sort(key=lambda x: x.timestamp, reverse=True)

        return [asdict(exec) for exec in history[:limit]]

    def pause_contract(self, contract_id: str) -> bool:
        """Pausa un contrato."""
        contract = self.contracts.get(contract_id)
        if contract and contract.state == ContractState.ACTIVE:
            contract.state = ContractState.PAUSED
            logger.info(f"⏸️ Paused contract {contract_id}")
            return True
        return False

    def resume_contract(self, contract_id: str) -> bool:
        """Reanuda un contrato."""
        contract = self.contracts.get(contract_id)
        if contract and contract.state == ContractState.PAUSED:
            contract.state = ContractState.ACTIVE
            logger.info(f"▶️ Resumed contract {contract_id}")
            return True
        return False


# Instancia global del gestor de contratos inteligentes
smart_contract_manager = SmartContractManager()


def get_smart_contract_manager() -> SmartContractManager:
    """Obtiene instancia global del gestor de contratos inteligentes."""
    return smart_contract_manager