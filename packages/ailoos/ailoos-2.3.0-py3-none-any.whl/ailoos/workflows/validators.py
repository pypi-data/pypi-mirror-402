"""
Workflow Validators - Validación de Workflows
============================================

Sistema de validación para asegurar que los workflows están bien formados
y que sus resultados cumplen con los criterios de calidad esperados.
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from .engine import WorkflowResult

logger = logging.getLogger(__name__)


class WorkflowValidator:
    """
    Validador de workflows que verifica:
    - Estructura del workflow
    - Calidad de los resultados
    - Cumplimiento de reglas de negocio
    - Métricas de rendimiento
    """

    def __init__(self):
        self.validation_rules: Dict[str, Callable] = {
            'structure': self._validate_structure,
            'performance': self._validate_performance,
            'quality': self._validate_quality,
            'business_rules': self._validate_business_rules
        }

    def validate_result(self, result: WorkflowResult,
                       validation_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validar resultado completo de workflow.

        Args:
            result: Resultado del workflow
            validation_config: Configuración de validación

        Returns:
            Dict con resultados de validación
        """
        validation_results = {
            'overall_success': True,
            'validation_details': {},
            'score': 1.0,
            'issues': []
        }

        # Ejecutar todas las validaciones configuradas
        for rule_name, rule_config in validation_config.items():
            if rule_name in self.validation_rules:
                try:
                    rule_result = self.validation_rules[rule_name](result, rule_config)
                    validation_results['validation_details'][rule_name] = rule_result

                    if not rule_result.get('passed', True):
                        validation_results['overall_success'] = False
                        validation_results['issues'].extend(rule_result.get('issues', []))

                        # Reducir score por cada fallo
                        penalty = rule_config.get('penalty', 0.1)
                        validation_results['score'] = max(0.0, validation_results['score'] - penalty)

                except Exception as e:
                    logger.error(f"Error en validación {rule_name}: {e}")
                    validation_results['issues'].append(f"Error en validación {rule_name}: {str(e)}")
                    validation_results['overall_success'] = False

        return validation_results

    def _validate_structure(self, result: WorkflowResult, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validar estructura del resultado."""
        issues = []

        # Verificar que todos los pasos esperados se ejecutaron
        expected_steps = config.get('expected_steps', [])
        if expected_steps:
            executed_set = set(result.steps_executed)
            expected_set = set(expected_steps)

            missing_steps = expected_set - executed_set
            if missing_steps:
                issues.append(f"Pasos faltantes: {list(missing_steps)}")

        # Verificar estructura del output final
        required_fields = config.get('required_output_fields', [])
        if required_fields and result.final_output:
            if isinstance(result.final_output, dict):
                missing_fields = [field for field in required_fields if field not in result.final_output]
                if missing_fields:
                    issues.append(f"Campos faltantes en output: {missing_fields}")
            else:
                issues.append("Output final no es un diccionario estructurado")

        return {
            'passed': len(issues) == 0,
            'issues': issues,
            'expected_steps': len(expected_steps),
            'executed_steps': len(result.steps_executed)
        }

    def _validate_performance(self, result: WorkflowResult, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validar métricas de rendimiento."""
        issues = []

        # Verificar tiempo de ejecución
        max_time = config.get('max_execution_time', 300)  # 5 minutos por defecto
        if result.execution_time > max_time:
            issues.append(f"Tiempo de ejecución excesivo: {result.execution_time:.2f}s > {max_time}s")

        # Verificar tiempo por paso
        max_step_time = config.get('max_step_time', 60)  # 1 minuto por paso
        for step_id, step_result in result.step_results.items():
            step_time = step_result.get('execution_time', 0)
            if step_time > max_step_time:
                issues.append(f"Paso {step_id} excedió tiempo máximo: {step_time:.2f}s > {max_step_time}s")

        # Verificar tasa de éxito de pasos
        min_success_rate = config.get('min_success_rate', 0.8)
        total_steps = len(result.steps_executed) + len(result.errors)
        if total_steps > 0:
            success_rate = len(result.steps_executed) / total_steps
            if success_rate < min_success_rate:
                issues.append(f"Tasa de éxito baja: {success_rate:.2%} < {min_success_rate:.2%}")
        return {
            'passed': len(issues) == 0,
            'issues': issues,
            'execution_time': result.execution_time,
            'success_rate': len(result.steps_executed) / max(1, len(result.steps_executed) + len(result.errors))
        }

    def _validate_quality(self, result: WorkflowResult, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validar calidad del resultado."""
        issues = []

        if not result.final_output:
            issues.append("No hay output final para validar calidad")
            return {'passed': False, 'issues': issues}

        # Validar confianza mínima
        min_confidence = config.get('min_confidence', 0.7)
        if isinstance(result.final_output, dict):
            confidence = result.final_output.get('confidence', 1.0)
            if confidence < min_confidence:
                issues.append(f"Confianza baja: {confidence:.2f} < {min_confidence}")

        # Validar completitud
        min_completeness = config.get('min_completeness', 0.8)
        if isinstance(result.final_output, dict):
            total_fields = len(result.final_output)
            filled_fields = sum(1 for v in result.final_output.values() if v is not None and v != "")
            completeness = filled_fields / max(1, total_fields)

            if completeness < min_completeness:
                issues.append(f"Completitud baja: {completeness:.2%} < {min_completeness:.2%}")

        # Validar consistencia interna
        if isinstance(result.final_output, dict):
            consistency_issues = self._check_internal_consistency(result.final_output)
            issues.extend(consistency_issues)

        return {
            'passed': len(issues) == 0,
            'issues': issues,
            'confidence': result.final_output.get('confidence', 0) if isinstance(result.final_output, dict) else 0,
            'completeness': self._calculate_completeness(result.final_output)
        }

    def _validate_business_rules(self, result: WorkflowResult, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validar reglas de negocio específicas."""
        issues = []

        rules = config.get('rules', [])
        if not result.final_output or not isinstance(result.final_output, dict):
            issues.append("No se puede validar reglas de negocio: output no estructurado")
            return {'passed': False, 'issues': issues}

        for rule in rules:
            rule_type = rule.get('type', '')
            field = rule.get('field', '')
            value = result.final_output.get(field)

            if value is None:
                continue  # Campo no presente, regla no aplicable

            if rule_type == 'range':
                min_val = rule.get('min', float('-inf'))
                max_val = rule.get('max', float('inf'))
                if not (min_val <= value <= max_val):
                    issues.append(f"Regla de rango violada para {field}: {value} no está en [{min_val}, {max_val}]")

            elif rule_type == 'required_value':
                required = rule.get('value')
                if value != required:
                    issues.append(f"Valor requerido para {field}: esperado {required}, obtenido {value}")

            elif rule_type == 'format':
                pattern = rule.get('pattern', '')
                import re
                if not re.match(pattern, str(value)):
                    issues.append(f"Formato inválido para {field}: {value} no cumple {pattern}")

        return {
            'passed': len(issues) == 0,
            'issues': issues,
            'rules_checked': len(rules),
            'rules_passed': len(rules) - len(issues)
        }

    def _check_internal_consistency(self, output: Dict[str, Any]) -> List[str]:
        """Verificar consistencia interna del output."""
        issues = []

        # Ejemplo: si hay tax_amount y base_amount, verificar que total = base + tax
        if 'tax_amount' in output and 'base_amount' in output:
            tax = output['tax_amount']
            base = output['base_amount']
            expected_total = base + tax
            actual_total = output.get('total_amount', 0)

            if abs(expected_total - actual_total) > 0.01:
                issues.append(f"Inconsistencia aritmética: esperado {expected_total:.2f}, obtenido {actual_total:.2f}")
        # Verificar que porcentajes estén entre 0 y 1
        percentage_fields = ['tax_rate', 'confidence', 'completeness']
        for field in percentage_fields:
            if field in output:
                value = output[field]
                if not (0 <= value <= 1):
                    issues.append(f"Porcentaje inválido en {field}: {value} (debe estar entre 0 y 1)")

        return issues

    def _calculate_completeness(self, output: Any) -> float:
        """Calcular completitud del output."""
        if not isinstance(output, dict):
            return 0.0

        total_fields = len(output)
        if total_fields == 0:
            return 0.0

        filled_fields = sum(1 for v in output.values() if v is not None and v != "")
        return filled_fields / total_fields


def create_default_validator() -> WorkflowValidator:
    """Crear validador con configuración por defecto."""
    return WorkflowValidator()


def validate_workflow_result(result: WorkflowResult,
                           template_type: str = "general") -> Dict[str, Any]:
    """
    Función de conveniencia para validar resultados de workflow.

    Args:
        result: Resultado del workflow
        template_type: Tipo de template para configuración de validación

    Returns:
        Resultados de validación
    """
    validator = create_default_validator()

    # Configuraciones por tipo de template
    validation_configs = {
        "document_analysis": {
            'structure': {
                'expected_steps': ['vision_extraction', 'expert_analysis', 'data_validation', 'final_validation'],
                'required_output_fields': ['validation_success', 'validated_data']
            },
            'performance': {
                'max_execution_time': 60,
                'max_step_time': 30,
                'min_success_rate': 0.9
            },
            'quality': {
                'min_confidence': 0.8,
                'min_completeness': 0.9
            }
        },
        "invoice_audit": {
            'structure': {
                'expected_steps': ['text_extraction', 'legal_validation', 'tax_calculation', 'compliance_check'],
                'required_output_fields': ['validation_success', 'tax_amount', 'total_amount']
            },
            'performance': {
                'max_execution_time': 70,
                'max_step_time': 25,
                'min_success_rate': 0.95
            },
            'business_rules': {
                'rules': [
                    {'type': 'range', 'field': 'tax_amount', 'min': 0},
                    {'type': 'range', 'field': 'total_amount', 'min': 0}
                ]
            }
        },
        "general": {
            'performance': {
                'max_execution_time': 300,
                'min_success_rate': 0.8
            }
        }
    }

    config = validation_configs.get(template_type, validation_configs['general'])
    return validator.validate_result(result, config)