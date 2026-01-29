#!/usr/bin/env python3
"""
Security Policy Engine Dinámico
==============================

Implementa un motor de políticas de seguridad dinámico que evalúa
reglas de seguridad en tiempo real, aplica políticas adaptativas,
y toma decisiones automatizadas basadas en contexto y riesgo.
"""

import logging
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import ast
import operator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PolicyAction(Enum):
    """Acciones de política"""
    ALLOW = "allow"
    DENY = "deny"
    CHALLENGE = "challenge"
    LOG = "log"
    ALERT = "alert"
    QUARANTINE = "quarantine"
    THROTTLE = "throttle"

class PolicyEffect(Enum):
    """Efectos de política"""
    PERMIT = "permit"
    DENY = "deny"

class PolicyOperator(Enum):
    """Operadores para condiciones"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX = "regex"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    BETWEEN = "between"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"

class RiskLevel(Enum):
    """Niveles de riesgo"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class PolicyCondition:
    """Condición de política"""
    field: str
    operator: PolicyOperator
    value: Any
    case_sensitive: bool = True

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evalúa la condición contra un contexto

        Args:
            context: Contexto de evaluación

        Returns:
            True si la condición se cumple
        """
        actual_value = self._get_nested_value(context, self.field)
        if actual_value is None:
            return False

        expected_value = self.value

        # Convertir tipos si es necesario
        if isinstance(expected_value, str) and not isinstance(actual_value, str):
            actual_value = str(actual_value)
        elif isinstance(expected_value, (int, float)) and isinstance(actual_value, str):
            try:
                actual_value = float(actual_value)
            except ValueError:
                return False

        # Aplicar operador
        if self.operator == PolicyOperator.EQUALS:
            return self._compare_values(actual_value, expected_value, self.case_sensitive) == 0
        elif self.operator == PolicyOperator.NOT_EQUALS:
            return self._compare_values(actual_value, expected_value, self.case_sensitive) != 0
        elif self.operator == PolicyOperator.CONTAINS:
            return str(expected_value) in str(actual_value)
        elif self.operator == PolicyOperator.NOT_CONTAINS:
            return str(expected_value) not in str(actual_value)
        elif self.operator == PolicyOperator.STARTS_WITH:
            return str(actual_value).startswith(str(expected_value))
        elif self.operator == PolicyOperator.ENDS_WITH:
            return str(actual_value).endswith(str(expected_value))
        elif self.operator == PolicyOperator.REGEX:
            try:
                return bool(re.search(str(expected_value), str(actual_value)))
            except re.error:
                return False
        elif self.operator == PolicyOperator.GREATER_THAN:
            try:
                return float(actual_value) > float(expected_value)
            except (ValueError, TypeError):
                return False
        elif self.operator == PolicyOperator.LESS_THAN:
            try:
                return float(actual_value) < float(expected_value)
            except (ValueError, TypeError):
                return False
        elif self.operator == PolicyOperator.BETWEEN:
            if not isinstance(expected_value, (list, tuple)) or len(expected_value) != 2:
                return False
            try:
                val = float(actual_value)
                return float(expected_value[0]) <= val <= float(expected_value[1])
            except (ValueError, TypeError):
                return False
        elif self.operator == PolicyOperator.IN_LIST:
            if not isinstance(expected_value, (list, tuple, set)):
                return False
            return actual_value in expected_value
        elif self.operator == PolicyOperator.NOT_IN_LIST:
            if not isinstance(expected_value, (list, tuple, set)):
                return False
            return actual_value not in expected_value

        return False

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Obtiene un valor anidado usando notación de punto"""
        keys = path.split('.')
        current = data

        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, (list, tuple)) and key.isdigit():
                index = int(key)
                current = current[index] if 0 <= index < len(current) else None
            else:
                return None

            if current is None:
                break

        return current

    def _compare_values(self, a: Any, b: Any, case_sensitive: bool) -> int:
        """Compara dos valores"""
        if not case_sensitive and isinstance(a, str) and isinstance(b, str):
            a = a.lower()
            b = b.lower()
        return (a > b) - (a < b)

@dataclass
class SecurityPolicy:
    """Política de seguridad"""
    id: str
    name: str
    description: Optional[str] = None
    effect: PolicyEffect = PolicyEffect.PERMIT
    actions: List[PolicyAction] = field(default_factory=list)
    conditions: List[PolicyCondition] = field(default_factory=list)
    priority: int = 100
    enabled: bool = True
    risk_level: RiskLevel = RiskLevel.MEDIUM
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    def evaluate(self, context: Dict[str, Any]) -> Tuple[bool, List[PolicyAction]]:
        """
        Evalúa la política contra un contexto

        Args:
            context: Contexto de evaluación

        Returns:
            Tuple de (si aplica, acciones a tomar)
        """
        if not self.enabled:
            return False, []

        if self.expires_at and datetime.now() > self.expires_at:
            return False, []

        # Evaluar todas las condiciones
        for condition in self.conditions:
            if not condition.evaluate(context):
                return False, []

        # Si todas las condiciones se cumplen, aplicar efecto
        return True, self.actions

    def to_dict(self) -> Dict[str, Any]:
        """Convierte política a diccionario"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'effect': self.effect.value,
            'actions': [a.value for a in self.actions],
            'conditions': [{
                'field': c.field,
                'operator': c.operator.value,
                'value': c.value,
                'case_sensitive': c.case_sensitive
            } for c in self.conditions],
            'priority': self.priority,
            'enabled': self.enabled,
            'risk_level': self.risk_level.value,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecurityPolicy':
        """Crea política desde diccionario"""
        return cls(
            id=data['id'],
            name=data['name'],
            description=data.get('description'),
            effect=PolicyEffect(data.get('effect', 'permit')),
            actions=[PolicyAction(a) for a in data.get('actions', [])],
            conditions=[PolicyCondition(
                field=c['field'],
                operator=PolicyOperator(c['operator']),
                value=c['value'],
                case_sensitive=c.get('case_sensitive', True)
            ) for c in data.get('conditions', [])],
            priority=data.get('priority', 100),
            enabled=data.get('enabled', True),
            risk_level=RiskLevel(data.get('risk_level', 'medium')),
            tags=data.get('tags', []),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None
        )

@dataclass
class PolicyEvaluationResult:
    """Resultado de evaluación de política"""
    policy_id: str
    applied: bool
    effect: PolicyEffect
    actions: List[PolicyAction]
    risk_level: RiskLevel
    evaluation_time: float
    matched_conditions: int
    total_conditions: int

class SecurityPolicyEngine:
    """
    Motor de políticas de seguridad dinámico
    """

    def __init__(self):
        # Políticas activas
        self.policies: Dict[str, SecurityPolicy] = {}

        # Políticas por tag
        self.policies_by_tag: Dict[str, Set[str]] = defaultdict(set)

        # Cache de evaluaciones
        self._evaluation_cache: Dict[str, PolicyEvaluationResult] = {}
        self._cache_expiration = timedelta(minutes=5)
        self._last_cache_cleanup = datetime.now()

        # Métricas
        self.evaluation_count = 0
        self.cache_hit_count = 0
        self.policy_hit_count = defaultdict(int)

        # Políticas por defecto
        self._create_default_policies()

        logger.info("🔒 Security Policy Engine initialized")

    def _create_default_policies(self):
        """Crea políticas de seguridad por defecto"""

        # Política: Bloquear IPs sospechosas
        suspicious_ip_policy = SecurityPolicy(
            id="block_suspicious_ips",
            name="Block Suspicious IPs",
            description="Bloquea acceso desde IPs conocidas como maliciosas",
            effect=PolicyEffect.DENY,
            actions=[PolicyAction.DENY, PolicyAction.ALERT],
            conditions=[
                PolicyCondition("ip_address", PolicyOperator.IN_LIST,
                              ["192.168.1.100", "10.0.0.1"])  # IPs de ejemplo
            ],
            priority=10,
            risk_level=RiskLevel.HIGH,
            tags=["network", "security"]
        )

        # Política: Requerir MFA para accesos de alto riesgo
        mfa_required_policy = SecurityPolicy(
            id="require_mfa_high_risk",
            name="Require MFA for High Risk Access",
            description="Requiere MFA para operaciones de alto riesgo",
            effect=PolicyEffect.PERMIT,
            actions=[PolicyAction.CHALLENGE],
            conditions=[
                PolicyCondition("risk_score", PolicyOperator.GREATER_THAN, 70),
                PolicyCondition("mfa_verified", PolicyOperator.EQUALS, False)
            ],
            priority=20,
            risk_level=RiskLevel.MEDIUM,
            tags=["authentication", "mfa"]
        )

        # Política: Limitar intentos de login fallidos
        login_attempts_policy = SecurityPolicy(
            id="limit_failed_logins",
            name="Limit Failed Login Attempts",
            description="Limita intentos de login fallidos por IP",
            effect=PolicyEffect.DENY,
            actions=[PolicyAction.THROTTLE, PolicyAction.ALERT],
            conditions=[
                PolicyCondition("failed_login_attempts", PolicyOperator.GREATER_THAN, 5),
                PolicyCondition("time_window_minutes", PolicyOperator.LESS_THAN, 60)
            ],
            priority=15,
            risk_level=RiskLevel.MEDIUM,
            tags=["authentication", "brute_force"]
        )

        # Política: Monitorear accesos fuera de horario laboral
        after_hours_policy = SecurityPolicy(
            id="monitor_after_hours",
            name="Monitor After Hours Access",
            description="Monitorea accesos fuera del horario laboral normal",
            effect=PolicyEffect.PERMIT,
            actions=[PolicyAction.LOG, PolicyAction.ALERT],
            conditions=[
                PolicyCondition("hour", PolicyOperator.NOT_BETWEEN, [9, 17]),
                PolicyCondition("day_of_week", PolicyOperator.NOT_EQUALS, "saturday"),
                PolicyCondition("day_of_week", PolicyOperator.NOT_EQUALS, "sunday")
            ],
            priority=50,
            risk_level=RiskLevel.LOW,
            tags=["monitoring", "business_hours"]
        )

        # Registrar políticas
        for policy in [suspicious_ip_policy, mfa_required_policy, login_attempts_policy, after_hours_policy]:
            self.add_policy(policy)

    def add_policy(self, policy: SecurityPolicy):
        """
        Agrega una política al motor

        Args:
            policy: Política a agregar
        """
        self.policies[policy.id] = policy

        # Indexar por tags
        for tag in policy.tags:
            self.policies_by_tag[tag].add(policy.id)

        logger.info(f"📋 Policy added: {policy.id}")

    def remove_policy(self, policy_id: str) -> bool:
        """
        Remueve una política del motor

        Args:
            policy_id: ID de la política

        Returns:
            True si se removió correctamente
        """
        if policy_id not in self.policies:
            return False

        policy = self.policies[policy_id]

        # Remover de índices
        for tag in policy.tags:
            self.policies_by_tag[tag].discard(policy_id)
            if not self.policies_by_tag[tag]:
                del self.policies_by_tag[tag]

        del self.policies[policy_id]

        # Limpiar cache
        self._clear_cache()

        logger.info(f"🚫 Policy removed: {policy_id}")
        return True

    def update_policy(self, policy_id: str, updates: Dict[str, Any]) -> Optional[SecurityPolicy]:
        """
        Actualiza una política existente

        Args:
            policy_id: ID de la política
            updates: Campos a actualizar

        Returns:
            Política actualizada o None si no existe
        """
        policy = self.policies.get(policy_id)
        if not policy:
            return None

        for key, value in updates.items():
            if hasattr(policy, key):
                setattr(policy, key, value)

        policy.updated_at = datetime.now()

        # Limpiar cache
        self._clear_cache()

        logger.info(f"📝 Policy updated: {policy_id}")
        return policy

    def evaluate_policies(self, context: Dict[str, Any], tags: Optional[List[str]] = None) -> List[PolicyEvaluationResult]:
        """
        Evalúa todas las políticas aplicables contra un contexto

        Args:
            context: Contexto de evaluación
            tags: Tags para filtrar políticas (opcional)

        Returns:
            Lista de resultados de evaluación
        """
        start_time = datetime.now()

        # Filtrar políticas por tags si se especifican
        if tags:
            policy_ids = set()
            for tag in tags:
                policy_ids.update(self.policies_by_tag.get(tag, set()))
        else:
            policy_ids = set(self.policies.keys())

        # Ordenar por prioridad (menor número = mayor prioridad)
        applicable_policies = [
            self.policies[pid] for pid in policy_ids
            if pid in self.policies and self.policies[pid].enabled
        ]
        applicable_policies.sort(key=lambda p: p.priority)

        results = []
        for policy in applicable_policies:
            eval_start = datetime.now()

            applied, actions = policy.evaluate(context)

            eval_time = (datetime.now() - eval_start).total_seconds()

            result = PolicyEvaluationResult(
                policy_id=policy.id,
                applied=applied,
                effect=policy.effect,
                actions=actions,
                risk_level=policy.risk_level,
                evaluation_time=eval_time,
                matched_conditions=len(policy.conditions) if applied else 0,
                total_conditions=len(policy.conditions)
            )

            results.append(result)

            if applied:
                self.policy_hit_count[policy.id] += 1

        self.evaluation_count += 1

        total_time = (datetime.now() - start_time).total_seconds()
        logger.debug(f"⚡ Policy evaluation completed in {total_time:.4f}s for {len(results)} policies")

        return results

    def evaluate_access_request(self, user_id: str, resource: str, action: str,
                              context: Dict[str, Any]) -> Tuple[bool, List[PolicyAction], RiskLevel]:
        """
        Evalúa una solicitud de acceso

        Args:
            user_id: ID del usuario
            resource: Recurso solicitado
            action: Acción solicitada
            context: Contexto adicional

        Returns:
            Tuple de (permitido, acciones, nivel de riesgo)
        """
        # Enriquecer contexto
        enriched_context = context.copy()
        enriched_context.update({
            'user_id': user_id,
            'resource': resource,
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'hour': datetime.now().hour,
            'day_of_week': datetime.now().strftime('%A').lower()
        })

        # Evaluar políticas
        results = self.evaluate_policies(enriched_context, tags=['access_control'])

        # Determinar resultado final
        allowed = True
        actions = []
        max_risk = RiskLevel.LOW

        for result in results:
            if result.applied:
                if result.effect == PolicyEffect.DENY:
                    allowed = False
                actions.extend(result.actions)
                if result.risk_level.value > max_risk.value:
                    max_risk = result.risk_level

        return allowed, actions, max_risk

    def get_policies_by_tag(self, tag: str) -> List[SecurityPolicy]:
        """
        Obtiene políticas por tag

        Args:
            tag: Tag a buscar

        Returns:
            Lista de políticas
        """
        policy_ids = self.policies_by_tag.get(tag, set())
        return [self.policies[pid] for pid in policy_ids if pid in self.policies]

    def get_policy(self, policy_id: str) -> Optional[SecurityPolicy]:
        """
        Obtiene una política por ID

        Args:
            policy_id: ID de la política

        Returns:
            Política o None si no existe
        """
        return self.policies.get(policy_id)

    def list_policies(self, enabled_only: bool = True) -> List[SecurityPolicy]:
        """
        Lista todas las políticas

        Args:
            enabled_only: Solo políticas habilitadas

        Returns:
            Lista de políticas
        """
        policies = list(self.policies.values())
        if enabled_only:
            policies = [p for p in policies if p.enabled]
        return policies

    def validate_policy_syntax(self, policy_dict: Dict[str, Any]) -> List[str]:
        """
        Valida la sintaxis de una política

        Args:
            policy_dict: Política en formato diccionario

        Returns:
            Lista de errores de validación
        """
        errors = []

        # Validar campos requeridos
        required_fields = ['id', 'name', 'effect']
        for field in required_fields:
            if field not in policy_dict:
                errors.append(f"Missing required field: {field}")

        # Validar effect
        if 'effect' in policy_dict:
            try:
                PolicyEffect(policy_dict['effect'])
            except ValueError:
                errors.append(f"Invalid effect: {policy_dict['effect']}")

        # Validar actions
        if 'actions' in policy_dict:
            for action in policy_dict['actions']:
                try:
                    PolicyAction(action)
                except ValueError:
                    errors.append(f"Invalid action: {action}")

        # Validar conditions
        if 'conditions' in policy_dict:
            for condition in policy_dict['conditions']:
                if not isinstance(condition, dict):
                    errors.append("Condition must be a dictionary")
                    continue

                required_cond_fields = ['field', 'operator', 'value']
                for field in required_cond_fields:
                    if field not in condition:
                        errors.append(f"Condition missing field: {field}")

                if 'operator' in condition:
                    try:
                        PolicyOperator(condition['operator'])
                    except ValueError:
                        errors.append(f"Invalid operator: {condition['operator']}")

        return errors

    def _clear_cache(self):
        """Limpia el cache de evaluaciones"""
        self._evaluation_cache.clear()
        self._last_cache_cleanup = datetime.now()

    def cleanup_expired_policies(self):
        """Limpia políticas expiradas"""
        current_time = datetime.now()
        expired = []

        for policy_id, policy in self.policies.items():
            if policy.expires_at and current_time > policy.expires_at:
                expired.append(policy_id)

        for policy_id in expired:
            self.remove_policy(policy_id)

        if expired:
            logger.info(f"🧹 Cleaned up {len(expired)} expired policies")

    def get_system_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del motor de políticas"""
        total_policies = len(self.policies)
        enabled_policies = len([p for p in self.policies.values() if p.enabled])

        tag_distribution = {}
        for tag, policy_ids in self.policies_by_tag.items():
            tag_distribution[tag] = len(policy_ids)

        risk_distribution = {}
        for policy in self.policies.values():
            risk_distribution[policy.risk_level.value] = risk_distribution.get(policy.risk_level.value, 0) + 1

        return {
            'total_policies': total_policies,
            'enabled_policies': enabled_policies,
            'disabled_policies': total_policies - enabled_policies,
            'evaluation_count': self.evaluation_count,
            'cache_hit_count': self.cache_hit_count,
            'tag_distribution': tag_distribution,
            'risk_distribution': risk_distribution,
            'top_hit_policies': dict(sorted(self.policy_hit_count.items(), key=lambda x: x[1], reverse=True)[:10])
        }


# Instancia global del motor de políticas
security_policy_engine = SecurityPolicyEngine()


def get_security_policy_engine() -> SecurityPolicyEngine:
    """Obtiene la instancia global del motor de políticas"""
    return security_policy_engine