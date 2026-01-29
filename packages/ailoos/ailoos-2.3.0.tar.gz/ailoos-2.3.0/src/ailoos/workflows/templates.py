"""
Workflow Templates - Plantillas de Workflows Automatizados
========================================================

Definiciones YAML/JSON para workflows comunes que pueden ser reutilizados
y personalizados para diferentes casos de uso.
"""

import yaml
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from .engine import WorkflowStep

from ..models.empoorio_lm.expert_system import Domain


class WorkflowTemplate:
    """
    Plantilla de workflow que define una receta de automatización.

    Una plantilla incluye:
    - Metadatos del workflow
    - Pasos definidos
    - Configuraciones por defecto
    - Validaciones
    """

    def __init__(self, template_id: str, name: str, description: str,
                 steps: List[Dict[str, Any]], metadata: Dict[str, Any] = None):
        self.template_id = template_id
        self.name = name
        self.description = description
        self.steps = steps
        self.metadata = metadata or {}

    def instantiate(self, parameters: Dict[str, Any] = None) -> List[WorkflowStep]:
        """
        Instanciar la plantilla con parámetros específicos.

        Args:
            parameters: Parámetros para personalizar el workflow

        Returns:
            Lista de pasos de workflow listos para ejecutar
        """
        params = parameters or {}

        instantiated_steps = []
        for step_config in self.steps:
            # Aplicar parámetros a la configuración
            step_config = self._apply_parameters(step_config, params)

            step = WorkflowStep(
                step_id=step_config['step_id'],
                step_type=step_config['step_type'],
                description=step_config['description'],
                config=step_config.get('config', {}),
                dependencies=step_config.get('dependencies', []),
                timeout_seconds=step_config.get('timeout_seconds', 30)
            )
            instantiated_steps.append(step)

        return instantiated_steps

    def _apply_parameters(self, config: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Aplicar parámetros a una configuración de paso."""
        # Recursivamente reemplazar placeholders como {param_name}
        config_str = json.dumps(config)
        for key, value in parameters.items():
            placeholder = f"{{{key}}}"
            config_str = config_str.replace(placeholder, str(value))

        return json.loads(config_str)

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para serialización."""
        return {
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'steps': self.steps,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowTemplate':
        """Crear desde diccionario."""
        return cls(
            template_id=data['template_id'],
            name=data['name'],
            description=data['description'],
            steps=data['steps'],
            metadata=data.get('metadata', {})
        )

    def save_to_file(self, file_path: str):
        """Guardar plantilla a archivo YAML."""
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, allow_unicode=True)

    @classmethod
    def load_from_file(cls, file_path: str) -> 'WorkflowTemplate':
        """Cargar plantilla desde archivo YAML."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)


# Plantillas predefinidas
DOCUMENT_ANALYSIS_TEMPLATE = WorkflowTemplate(
    template_id="document_analysis",
    name="Análisis de Documentos",
    description="Workflow completo para analizar documentos: extracción de texto, análisis experto y validación",
    steps=[
        {
            "step_id": "vision_extraction",
            "step_type": "vision",
            "description": "Extraer texto de la imagen del documento",
            "config": {
                "extraction_mode": "ocr",
                "language": "es"
            },
            "timeout_seconds": 15
        },
        {
            "step_id": "expert_analysis",
            "step_type": "expert",
            "description": "Analizar contenido con experto especializado",
            "config": {
                "domain": "{domain}",
                "prompt_template": "Analiza el siguiente documento y extrae información clave:\n\n{text}\n\nProporciona un resumen estructurado.",
                "max_tokens": 300
            },
            "dependencies": ["vision_extraction"],
            "timeout_seconds": 30
        },
        {
            "step_id": "data_validation",
            "step_type": "tool",
            "description": "Validar y estructurar los datos extraídos",
            "config": {
                "tool_name": "validator",
                "rules": [
                    {
                        "type": "required_fields",
                        "fields": ["extracted_text", "expert_response"]
                    }
                ]
            },
            "dependencies": ["expert_analysis"],
            "timeout_seconds": 10
        },
        {
            "step_id": "final_validation",
            "step_type": "validation",
            "description": "Validación final del resultado estructurado",
            "config": {
                "required_fields": ["validation_success", "validated_data"],
                "type_checks": {
                    "validation_success": "bool"
                }
            },
            "dependencies": ["data_validation"],
            "timeout_seconds": 5
        }
    ],
    metadata={
        "version": "1.0.0",
        "author": "AILOOS Team",
        "supported_domains": ["legal", "medical", "financial"],
        "estimated_duration": "50s",
        "input_types": ["image_path"],
        "output_format": "structured_json"
    }
)

INVOICE_AUDIT_TEMPLATE = WorkflowTemplate(
    template_id="invoice_audit",
    name="Auditoría de Facturas",
    description="Workflow completo para auditar facturas: OCR, validación legal y cálculo de impuestos",
    steps=[
        {
            "step_id": "text_extraction",
            "step_type": "vision",
            "description": "Extraer texto y montos de la factura",
            "config": {
                "extraction_mode": "invoice_ocr",
                "fields_to_extract": ["amount", "tax_rate", "vendor", "date"]
            },
            "timeout_seconds": 20
        },
        {
            "step_id": "legal_validation",
            "step_type": "expert",
            "description": "Validar cumplimiento legal de la factura",
            "config": {
                "domain": "legal",
                "prompt_template": "Valida si esta factura cumple con la normativa legal:\n\n{text}\n\nVerifica: formato correcto, datos obligatorios, plazos.",
                "max_tokens": 200
            },
            "dependencies": ["text_extraction"],
            "timeout_seconds": 25
        },
        {
            "step_id": "tax_calculation",
            "step_type": "tool",
            "description": "Calcular impuestos y validar montos",
            "config": {
                "tool_name": "calculator",
                "tax_rate": 0.21,
                "expression": "base_amount * tax_rate"
            },
            "dependencies": ["text_extraction"],
            "timeout_seconds": 5
        },
        {
            "step_id": "compliance_check",
            "step_type": "validation",
            "description": "Verificar cumplimiento completo de la factura",
            "config": {
                "required_fields": ["legal_validation", "tax_calculation", "final_amount"],
                "business_rules": [
                    "tax_amount > 0",
                    "total_amount = base_amount + tax_amount"
                ]
            },
            "dependencies": ["legal_validation", "tax_calculation"],
            "timeout_seconds": 10
        }
    ],
    metadata={
        "version": "1.0.0",
        "author": "AILOOS Team",
        "category": "financial_audit",
        "estimated_duration": "60s",
        "compliance": ["GDPR", "SOX", "local_tax_laws"],
        "output_format": "audit_report_json"
    }
)

MEDICAL_DIAGNOSIS_TEMPLATE = WorkflowTemplate(
    template_id="medical_diagnosis",
    name="Diagnóstico Médico Asistido",
    description="Workflow para asistencia al diagnóstico médico: análisis de síntomas y recomendaciones",
    steps=[
        {
            "step_id": "symptom_extraction",
            "step_type": "vision",
            "description": "Extraer síntomas de imágenes médicas o texto",
            "config": {
                "extraction_mode": "medical_ocr",
                "medical_entities": ["symptoms", "vital_signs", "test_results"]
            },
            "timeout_seconds": 15
        },
        {
            "step_id": "medical_analysis",
            "step_type": "expert",
            "description": "Análisis médico especializado de síntomas",
            "config": {
                "domain": "medical",
                "prompt_template": "Como médico especialista, analiza estos síntomas:\n\n{text}\n\nProporciona: diagnóstico probable, pruebas recomendadas, tratamiento inicial.",
                "max_tokens": 400
            },
            "dependencies": ["symptom_extraction"],
            "timeout_seconds": 35
        },
        {
            "step_id": "risk_assessment",
            "step_type": "tool",
            "description": "Evaluar nivel de riesgo y urgencia",
            "config": {
                "tool_name": "risk_calculator",
                "risk_factors": ["age", "symptoms_severity", "vital_signs"],
                "urgency_levels": ["low", "medium", "high", "emergency"]
            },
            "dependencies": ["medical_analysis"],
            "timeout_seconds": 10
        },
        {
            "step_id": "ethical_validation",
            "step_type": "validation",
            "description": "Validar recomendaciones éticas y médicas",
            "config": {
                "required_fields": ["diagnosis", "recommendations", "risk_level"],
                "ethical_checks": [
                    "no_experimental_treatments_without_consent",
                    "privacy_protected",
                    "evidence_based_recommendations"
                ]
            },
            "dependencies": ["risk_assessment"],
            "timeout_seconds": 5
        }
    ],
    metadata={
        "version": "1.0.0",
        "author": "AILOOS Medical Team",
        "category": "healthcare",
        "estimated_duration": "65s",
        "compliance": ["HIPAA", "medical_ethics", "evidence_based_medicine"],
        "disclaimer": "Este es un sistema de asistencia, no reemplaza el diagnóstico médico profesional",
        "output_format": "medical_report_json"
    }
)


def create_document_analysis_workflow(domain: str = "legal") -> WorkflowTemplate:
    """
    Crear workflow personalizado para análisis de documentos.

    Args:
        domain: Dominio del experto a utilizar

    Returns:
        WorkflowTemplate personalizado
    """
    # Clonar la plantilla base
    template = WorkflowTemplate(
        template_id=f"document_analysis_{domain}",
        name=f"Análisis de Documentos - {domain.title()}",
        description=f"Workflow para analizar documentos usando experto {domain}",
        steps=DOCUMENT_ANALYSIS_TEMPLATE.steps.copy(),
        metadata=DOCUMENT_ANALYSIS_TEMPLATE.metadata.copy()
    )

    # Actualizar metadatos
    template.metadata['domain'] = domain
    template.metadata['template_id'] = f"document_analysis_{domain}"

    return template


def load_template_from_file(file_path: str) -> WorkflowTemplate:
    """Cargar plantilla desde archivo."""
    return WorkflowTemplate.load_from_file(file_path)


def save_template_to_file(template: WorkflowTemplate, file_path: str):
    """Guardar plantilla a archivo."""
    template.save_to_file(file_path)


# Plantilla de pensamiento profundo iterativo
DEEP_THINKING_TEMPLATE = WorkflowTemplate(
    template_id="deep_thinking",
    name="Pensamiento Profundo Iterativo",
    description="Workflow de pensamiento profundo que utiliza descomposición de problemas, crítica de respuestas y reflexión para resolver problemas complejos de manera iterativa",
    steps=[
        {
            "step_id": "iterative_reasoning",
            "step_type": "deep_thinking",
            "description": "Ejecutar razonamiento iterativo con fases de planificación, ejecución, reflexión y corrección",
            "config": {
                "thinking_budget": {
                    "max_time_seconds": 300,
                    "max_iterations": 5,
                    "min_confidence_threshold": 0.7,
                    "time_per_iteration_seconds": 60
                },
                "domain": "{domain}",
                "reasoning_strategy": "{reasoning_strategy}"
            },
            "timeout_seconds": 360  # 6 minutos máximo
        }
    ],
    metadata={
        "version": "1.0.0",
        "author": "AILOOS Reasoning Team",
        "category": "reasoning",
        "estimated_duration": "5-6min",
        "supported_strategies": ["analytical", "creative", "technical", "general"],
        "input_format": {"problem_statement": "string", "input_data": "any"},
        "output_format": "iterative_result_json",
        "components_used": ["ProblemDecomposer", "ResponseCritic", "ReflectionEngine"],
        "phases": ["planning", "execution", "reflection", "correction"]
    }
)

# Plantillas especializadas para diferentes estrategias de razonamiento
ANALYTICAL_DEEP_THINKING_TEMPLATE = WorkflowTemplate(
    template_id="analytical_deep_thinking",
    name="Pensamiento Profundo Analítico",
    description="Pensamiento profundo enfocado en análisis lógico, descomposición sistemática y evaluación crítica de evidencia",
    steps=[
        {
            "step_id": "analytical_reasoning",
            "step_type": "deep_thinking",
            "description": "Razonamiento analítico iterativo con énfasis en evidencia y lógica",
            "config": {
                "thinking_budget": {
                    "max_time_seconds": 400,
                    "max_iterations": 6,
                    "min_confidence_threshold": 0.8,
                    "time_per_iteration_seconds": 60
                },
                "domain": "research",
                "reasoning_strategy": "analytical"
            },
            "timeout_seconds": 420
        }
    ],
    metadata={
        "version": "1.0.0",
        "author": "AILOOS Reasoning Team",
        "category": "reasoning",
        "strategy": "analytical",
        "estimated_duration": "6-7min",
        "strengths": ["Análisis lógico", "Evaluación de evidencia", "Descomposición sistemática"],
        "use_cases": ["Investigación", "Análisis de datos", "Resolución de problemas técnicos"]
    }
)

CREATIVE_DEEP_THINKING_TEMPLATE = WorkflowTemplate(
    template_id="creative_deep_thinking",
    name="Pensamiento Profundo Creativo",
    description="Pensamiento profundo que fomenta la innovación, generación de ideas y enfoques no convencionales",
    steps=[
        {
            "step_id": "creative_reasoning",
            "step_type": "deep_thinking",
            "description": "Razonamiento creativo iterativo con énfasis en innovación y múltiples perspectivas",
            "config": {
                "thinking_budget": {
                    "max_time_seconds": 350,
                    "max_iterations": 5,
                    "min_confidence_threshold": 0.6,
                    "time_per_iteration_seconds": 70
                },
                "domain": "business_strategy",
                "reasoning_strategy": "creative"
            },
            "timeout_seconds": 380
        }
    ],
    metadata={
        "version": "1.0.0",
        "author": "AILOOS Reasoning Team",
        "category": "reasoning",
        "strategy": "creative",
        "estimated_duration": "5-6min",
        "strengths": ["Innovación", "Múltiples perspectivas", "Generación de ideas"],
        "use_cases": ["Desarrollo de productos", "Estrategia empresarial", "Resolución creativa de problemas"]
    }
)

TECHNICAL_DEEP_THINKING_TEMPLATE = WorkflowTemplate(
    template_id="technical_deep_thinking",
    name="Pensamiento Profundo Técnico",
    description="Pensamiento profundo especializado en problemas técnicos, implementación y optimización de sistemas",
    steps=[
        {
            "step_id": "technical_reasoning",
            "step_type": "deep_thinking",
            "description": "Razonamiento técnico iterativo con énfasis en implementación y optimización",
            "config": {
                "thinking_budget": {
                    "max_time_seconds": 450,
                    "max_iterations": 7,
                    "min_confidence_threshold": 0.75,
                    "time_per_iteration_seconds": 60
                },
                "domain": "software_development",
                "reasoning_strategy": "technical"
            },
            "timeout_seconds": 480
        }
    ],
    metadata={
        "version": "1.0.0",
        "author": "AILOOS Reasoning Team",
        "category": "reasoning",
        "strategy": "technical",
        "estimated_duration": "7-8min",
        "strengths": ["Implementación técnica", "Optimización", "Análisis de sistemas"],
        "use_cases": ["Desarrollo de software", "Arquitectura de sistemas", "Optimización técnica"]
    }
)


# Registro de plantillas disponibles
AVAILABLE_TEMPLATES = {
    "document_analysis": DOCUMENT_ANALYSIS_TEMPLATE,
    "invoice_audit": INVOICE_AUDIT_TEMPLATE,
    "medical_diagnosis": MEDICAL_DIAGNOSIS_TEMPLATE,
    "deep_thinking": DEEP_THINKING_TEMPLATE,
    "analytical_deep_thinking": ANALYTICAL_DEEP_THINKING_TEMPLATE,
    "creative_deep_thinking": CREATIVE_DEEP_THINKING_TEMPLATE,
    "technical_deep_thinking": TECHNICAL_DEEP_THINKING_TEMPLATE
}


def get_template(template_id: str) -> Optional[WorkflowTemplate]:
    """Obtener plantilla por ID."""
    return AVAILABLE_TEMPLATES.get(template_id)


def list_available_templates() -> Dict[str, str]:
    """Listar plantillas disponibles con descripciones."""
    return {
        template_id: template.description
        for template_id, template in AVAILABLE_TEMPLATES.items()
    }