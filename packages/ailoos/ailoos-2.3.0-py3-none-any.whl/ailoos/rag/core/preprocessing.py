"""
Preprocessing Pipeline for RAG Systems
======================================

Este módulo implementa el pipeline de preprocesamiento para sistemas RAG,
incluyendo filtrado de PII, normalización de texto, y validación de compliance
antes de que los datos sean procesados por el sistema de recuperación.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
from .deduplication import DocumentDeduplicator, DistributedHashRegistry

from ...privacy import PIIFilterService, PIIFilterConfig

logger = logging.getLogger(__name__)


class PreprocessingStep(ABC):
    """
    Clase base abstracta para pasos de preprocesamiento.

    Cada paso del pipeline debe heredar de esta clase e implementar
    el método process.
    """

    @abstractmethod
    def process(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa los datos en este paso del pipeline.

        Args:
            data: Datos a procesar
            context: Contexto adicional del pipeline

        Returns:
            Datos procesados
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre del paso de preprocesamiento."""
        pass


class PIIFilteringStep(PreprocessingStep):
    """Paso de filtrado de PII usando el servicio de privacidad."""

    def __init__(self, pii_config: Optional[PIIFilterConfig] = None):
        """
        Inicializa el paso de filtrado PII.

        Args:
            pii_config: Configuración del filtro PII
        """
        self.pii_service = PIIFilterService(pii_config)

    def process(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filtra PII de la query del usuario.

        Args:
            data: Datos con 'query' y otros campos
            context: Contexto con 'user_id', etc.

        Returns:
            Datos con query filtrada y metadata de PII
        """
        query = data.get('query', '')
        user_id = context.get('user_id')

        # Preprocesar query
        pii_result = self.pii_service.preprocess_query(query, user_id)

        # Actualizar datos con resultados del filtrado
        processed_data = data.copy()
        processed_data['original_query'] = query
        processed_data['query'] = pii_result['filtered_query']
        processed_data['pii_detected'] = pii_result['pii_detected']
        processed_data['pii_changes'] = pii_result['pii_changes']
        processed_data['processing_metadata'] = {
            'pii_filtered_at': pii_result['processing_timestamp'],
            'step': self.name
        }

        if pii_result['pii_detected']:
            logger.info(f"PII filtrada en query de usuario {user_id}: {len(pii_result['pii_changes'])} elementos")

        return processed_data

    @property
    def name(self) -> str:
        return "pii_filtering"


class TextNormalizationStep(PreprocessingStep):
    """Paso de normalización de texto."""

    def __init__(self, lowercase: bool = True, remove_extra_spaces: bool = True,
                 normalize_unicode: bool = False):
        """
        Inicializa el paso de normalización.

        Args:
            lowercase: Convertir a minúsculas
            remove_extra_spaces: Remover espacios extra
            normalize_unicode: Normalizar caracteres unicode
        """
        self.lowercase = lowercase
        self.remove_extra_spaces = remove_extra_spaces
        self.normalize_unicode = normalize_unicode

    def process(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza el texto de la query.

        Args:
            data: Datos con 'query'
            context: Contexto del pipeline

        Returns:
            Datos con query normalizada
        """
        query = data.get('query', '')

        # Aplicar normalizaciones
        if self.normalize_unicode:
            import unicodedata
            query = unicodedata.normalize('NFKC', query)

        if self.lowercase:
            query = query.lower()

        if self.remove_extra_spaces:
            import re
            query = re.sub(r'\s+', ' ', query).strip()

        processed_data = data.copy()
        processed_data['query'] = query
        processed_data['processing_metadata'] = data.get('processing_metadata', {}).copy()
        processed_data['processing_metadata']['text_normalization_at'] = datetime.now().isoformat()
        processed_data['processing_metadata']['step'] = self.name

        return processed_data

    @property
    def name(self) -> str:
        return "text_normalization"


class ComplianceValidationStep(PreprocessingStep):
    """Paso de validación de compliance."""

    def __init__(self, pii_service: Optional[PIIFilterService] = None):
        """
        Inicializa el paso de validación.

        Args:
            pii_service: Servicio de PII para validación
        """
        self.pii_service = pii_service or PIIFilterService()

    def process(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida compliance de la query procesada.

        Args:
            data: Datos procesados
            context: Contexto del pipeline

        Returns:
            Datos con validación de compliance
        """
        query = data.get('query', '')

        # Validar compliance
        compliance_result = self.pii_service.validate_compliance(query)

        processed_data = data.copy()
        processed_data['compliance_check'] = compliance_result
        processed_data['processing_metadata'] = data.get('processing_metadata', {}).copy()
        processed_data['processing_metadata']['compliance_validated_at'] = datetime.now().isoformat()
        processed_data['processing_metadata']['step'] = self.name

        # Log de alertas si hay problemas de compliance
        if not compliance_result['compliant']:
            risk_level = compliance_result['risk_level']
            logger.warning(f"Query no compliant detectada. Nivel de riesgo: {risk_level}")
            for rec in compliance_result['recommendations']:
                logger.warning(f"Recomendación: {rec}")

        return processed_data

    @property
    def name(self) -> str:
        return "compliance_validation"


@dataclass
class PreprocessingConfig:
    """Configuración del pipeline de preprocesamiento."""
    steps: List[PreprocessingStep] = field(default_factory=list)
    enable_audit_log: bool = True
    fail_on_pii_detection: bool = False  # Si True, falla el pipeline si se detecta PII
    max_query_length: Optional[int] = None

    def add_step(self, step: PreprocessingStep) -> None:
        """Agrega un paso al pipeline."""
        self.steps.append(step)

    def get_step_by_name(self, name: str) -> Optional[PreprocessingStep]:
        """Obtiene un paso por nombre."""
        return next((step for step in self.steps if step.name == name), None)


class RAGPreprocessingPipeline:
    """
    Pipeline completo de preprocesamiento para sistemas RAG.

    Coordina múltiples pasos de preprocesamiento asegurando que los datos
    de entrada cumplan con políticas de privacidad y calidad antes de ser
    procesados por el sistema RAG.
    """

    def __init__(self, config: Optional[PreprocessingConfig] = None):
        """
        Inicializa el pipeline de preprocesamiento.

        Args:
            config: Configuración del pipeline
        """
        self.config = config or self._create_default_config()
        self.audit_log: List[Dict[str, Any]] = []
        logger.info("RAGPreprocessingPipeline inicializado")

    def _create_default_config(self) -> PreprocessingConfig:
        """Crea configuración por defecto con pasos estándar."""
        config = PreprocessingConfig()

        # Agregar pasos por defecto
        config.add_step(PIIFilteringStep())
        config.add_step(TextNormalizationStep())
        config.add_step(ComplianceValidationStep())

        return config

    def preprocess(self, query: str, user_id: Optional[int] = None,
                  context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Ejecuta el pipeline completo de preprocesamiento.

        Args:
            query: Query original del usuario
            user_id: ID del usuario
            context: Contexto adicional

        Returns:
            Resultado del preprocesamiento con query procesada y metadata

        Raises:
            ValueError: Si el pipeline falla y está configurado para fallar
        """
        # Inicializar datos y contexto
        data = {'query': query}
        pipeline_context = context or {}
        pipeline_context['user_id'] = user_id
        pipeline_context['pipeline_start_time'] = datetime.now().isoformat()

        # Ejecutar cada paso del pipeline
        for step in self.config.steps:
            try:
                logger.debug(f"Ejecutando paso: {step.name}")
                data = step.process(data, pipeline_context)

                # Registrar en audit log si está habilitado
                if self.config.enable_audit_log:
                    audit_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'step': step.name,
                        'user_id': user_id,
                        'query_length': len(data.get('query', '')),
                        'pii_detected': data.get('pii_detected', False)
                    }
                    self.audit_log.append(audit_entry)

            except Exception as e:
                logger.error(f"Error en paso {step.name}: {str(e)}")
                if self.config.fail_on_pii_detection and 'pii' in str(e).lower():
                    raise ValueError(f"Pipeline falló en paso {step.name}: {str(e)}")
                # Continuar con el siguiente paso si no es crítico

        # Validaciones finales
        final_query = data.get('query', '')
        if self.config.max_query_length and len(final_query) > self.config.max_query_length:
            logger.warning(f"Query excede longitud máxima: {len(final_query)} > {self.config.max_query_length}")
            data['query'] = final_query[:self.config.max_query_length]

        # Resultado final
        result = {
            'original_query': query,
            'processed_query': data.get('query', ''),
            'pipeline_metadata': {
                'total_steps': len(self.config.steps),
                'completed_at': datetime.now().isoformat(),
                'user_id': user_id
            },
            'processing_details': data
        }

        logger.info(f"Pipeline completado para usuario {user_id}: {len(self.config.steps)} pasos")
        return result

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Obtiene el log de auditoría del pipeline."""
        return self.audit_log.copy()

    def clear_audit_log(self) -> None:
        """Limpia el log de auditoría."""
        self.audit_log.clear()

    def validate_pipeline_config(self) -> List[str]:
        """
        Valida la configuración del pipeline.

        Returns:
            Lista de errores de validación
        """
        errors = []

        if not self.config.steps:
            errors.append("El pipeline debe tener al menos un paso")

        step_names = [step.name for step in self.config.steps]
        if len(step_names) != len(set(step_names)):
            errors.append("Los nombres de pasos deben ser únicos")

        # Validar dependencias entre pasos
        has_pii_filter = any(isinstance(step, PIIFilteringStep) for step in self.config.steps)
        has_compliance = any(isinstance(step, ComplianceValidationStep) for step in self.config.steps)

        if has_compliance and not has_pii_filter:
            errors.append("ComplianceValidationStep requiere PIIFilteringStep")
        return errors


class DeduplicationStep(PreprocessingStep):
    """Paso de deduplicación de documentos usando hashing distribuido."""

    def __init__(self, deduplicator: DocumentDeduplicator):
        """
        Inicializa el paso de deduplicación.

        Args:
            deduplicator: Instancia del deduplicador de documentos
        """
        self.deduplicator = deduplicator

    async def process(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verifica si el documento es duplicado usando el registro distribuido.

        Args:
            data: Datos del documento
            context: Contexto del pipeline

        Returns:
            Datos del documento con información de deduplicación
        """
        document = data.get('document', data)

        # Verificar si el documento debe procesarse
        should_process = await self.deduplicator.should_process_document(document)

        processed_data = data.copy()
        processed_data['is_duplicate'] = not should_process
        processed_data['processing_metadata'] = data.get('processing_metadata', {}).copy()
        processed_data['processing_metadata']['deduplication_at'] = datetime.now().isoformat()
        processed_data['processing_metadata']['step'] = self.name

        if not should_process:
            logger.info(f"Documento duplicado omitido: {document.get('id', 'unknown')}")
            processed_data['skip_processing'] = True

        return processed_data

    @property
    def name(self) -> str:
        return "deduplication"


@dataclass
class DocumentPreprocessingConfig:
    """Configuración del pipeline de preprocesamiento de documentos."""
    steps: List[PreprocessingStep] = field(default_factory=list)
    enable_audit_log: bool = True
    skip_duplicates: bool = True  # Si True, omite documentos duplicados

    def add_step(self, step: PreprocessingStep) -> None:
        """Agrega un paso al pipeline."""
        self.steps.append(step)

    def get_step_by_name(self, name: str) -> Optional[PreprocessingStep]:
        """Obtiene un paso por nombre."""
        return next((step for step in self.steps if step.name == name), None)


class DocumentPreprocessingPipeline:
    """
    Pipeline de preprocesamiento para documentos en sistemas RAG.

    Coordina múltiples pasos de preprocesamiento incluyendo deduplicación
    distribuida para evitar almacenamiento redundante.
    """

    def __init__(self, config: Optional[DocumentPreprocessingConfig] = None):
        """
        Inicializa el pipeline de preprocesamiento de documentos.

        Args:
            config: Configuración del pipeline
        """
        self.config = config or self._create_default_config()
        self.audit_log: List[Dict[str, Any]] = []
        logger.info("DocumentPreprocessingPipeline inicializado")

    def _create_default_config(self) -> DocumentPreprocessingConfig:
        """Crea configuración por defecto con deduplicación."""
        config = DocumentPreprocessingConfig()

        # Nota: DeduplicationStep requiere configuración externa del deduplicator
        # Se debe agregar manualmente o proporcionar config personalizada

        return config

    async def preprocess_documents(self, documents: List[Dict[str, Any]],
                                 context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Ejecuta el pipeline completo de preprocesamiento para múltiples documentos.

        Args:
            documents: Lista de documentos a procesar
            context: Contexto adicional del pipeline

        Returns:
            Resultado del preprocesamiento con documentos procesados y metadata
        """
        pipeline_context = context or {}
        pipeline_context['pipeline_start_time'] = datetime.now().isoformat()

        processed_documents = []
        skipped_documents = []
        duplicate_count = 0

        # Procesar cada documento
        for doc in documents:
            try:
                # Ejecutar cada paso del pipeline
                processed_doc = {'document': doc}

                for step in self.config.steps:
                    logger.debug(f"Ejecutando paso {step.name} en documento {doc.get('id', 'unknown')}")

                    if hasattr(step, 'process'):
                        if asyncio.iscoroutinefunction(step.process):
                            processed_doc = await step.process(processed_doc, pipeline_context)
                        else:
                            processed_doc = step.process(processed_doc, pipeline_context)
                    else:
                        logger.warning(f"Paso {step.name} no tiene método process")

                    # Registrar en audit log si está habilitado
                    if self.config.enable_audit_log:
                        audit_entry = {
                            'timestamp': datetime.now().isoformat(),
                            'step': step.name,
                            'document_id': doc.get('id', 'unknown'),
                            'is_duplicate': processed_doc.get('is_duplicate', False)
                        }
                        self.audit_log.append(audit_entry)

                # Decidir si incluir el documento
                if processed_doc.get('skip_processing', False) and self.config.skip_duplicates:
                    skipped_documents.append(processed_doc['document'])
                    duplicate_count += 1
                else:
                    processed_documents.append(processed_doc['document'])

            except Exception as e:
                logger.error(f"Error procesando documento {doc.get('id', 'unknown')}: {str(e)}")
                # Continuar con el siguiente documento

        # Resultado final
        result = {
            'original_count': len(documents),
            'processed_documents': processed_documents,
            'skipped_documents': skipped_documents,
            'duplicate_count': duplicate_count,
            'pipeline_metadata': {
                'total_steps': len(self.config.steps),
                'completed_at': datetime.now().isoformat(),
                'processing_stats': {
                    'processed': len(processed_documents),
                    'skipped': len(skipped_documents),
                    'duplicates': duplicate_count
                }
            }
        }

        logger.info(f"Pipeline de documentos completado: {len(documents)} -> {len(processed_documents)} documentos procesados, {duplicate_count} duplicados omitidos")
        return result

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Obtiene el log de auditoría del pipeline."""
        return self.audit_log.copy()

    def clear_audit_log(self) -> None:
        """Limpia el log de auditoría."""
        self.audit_log.clear()

    def validate_pipeline_config(self) -> List[str]:
        """
        Valida la configuración del pipeline.

        Returns:
            Lista de errores de validación
        """
        errors = []

        if not self.config.steps:
            errors.append("El pipeline debe tener al menos un paso")

        step_names = [step.name for step in self.config.steps]
        if len(step_names) != len(set(step_names)):
            errors.append("Los nombres de pasos deben ser únicos")

        return errors

        return errors