"""
Tests de Compliance para Fase Maturity 3: Gobernanza del Dato en RAG/CAG
========================================================================

Este módulo contiene tests para validar:
- Anonimización y filtrado de PII en datos de entrada
- Control de acceso a documentos (DLAC) en retriever
- Integración completa del pipeline de seguridad
"""

import unittest
from unittest.mock import Mock, patch
import json
from datetime import datetime, timedelta

from ...privacy import PIIFilterService, PIICategory, PIIAction
from ..core.preprocessing import RAGPreprocessingPipeline, PIIFilteringStep
from ..core.access_control import (
    AccessControlEngine, DocumentAccessFilter, AccessPolicy,
    UserContext, DocumentMetadata, AccessLevel, AccessDecision
)


class TestPIIAnonymization(unittest.TestCase):
    """Tests para anonimización y filtrado de PII."""

    def setUp(self):
        """Configurar tests."""
        self.pii_service = PIIFilterService()

    def test_email_detection_and_anonymization(self):
        """Test detección y anonimización de emails."""
        query = "Contact me at john.doe@example.com for more info"
        result = self.pii_service.preprocess_query(query, user_id=1)

        self.assertTrue(result['pii_detected'])
        self.assertIn('[EMAIL]', result['filtered_query'])
        self.assertNotIn('john.doe@example.com', result['filtered_query'])
        self.assertEqual(len(result['pii_changes']), 1)
        self.assertEqual(result['pii_changes'][0]['category'], 'email')

    def test_phone_detection_and_masking(self):
        """Test detección y enmascaramiento de teléfonos."""
        query = "Call me at 111-222-3333 or (111) 444-5555"
        result = self.pii_service.preprocess_query(query, user_id=1)

        self.assertTrue(result['pii_detected'])
        self.assertNotIn('111-222-3333', result['filtered_query'])
        self.assertNotIn('(111) 444-5555', result['filtered_query'])
        self.assertEqual(len(result['pii_changes']), 2)

    def test_ssn_detection_and_masking(self):
        """Test detección y enmascaramiento de SSN."""
        query = "My SSN is 123-45-6789"
        result = self.pii_service.preprocess_query(query, user_id=1)

        self.assertTrue(result['pii_detected'])
        self.assertNotIn('123-45-6789', result['filtered_query'])
        self.assertIn('XXX-XX-XXXX', result['filtered_query'])

    def test_credit_card_detection(self):
        """Test detección de tarjetas de crédito."""
        query = "Payment with card 4111-1111-1111-1111"
        result = self.pii_service.preprocess_query(query, user_id=1)

        self.assertTrue(result['pii_detected'])
        self.assertNotIn('4111-1111-1111-1111', result['filtered_query'])

    def test_no_pii_detection(self):
        """Test cuando no hay PII."""
        query = "What is the weather like today?"
        result = self.pii_service.preprocess_query(query, user_id=1)

        self.assertFalse(result['pii_detected'])
        self.assertEqual(result['filtered_query'], query)
        self.assertEqual(len(result['pii_changes']), 0)

    def test_compliance_validation(self):
        """Test validación de compliance."""
        # Query con PII
        bad_query = "Email: dummy@example.com Phone: 111-222-3333"
        compliance = self.pii_service.validate_compliance(bad_query)
        self.assertFalse(compliance['compliant'])
        self.assertEqual(compliance['risk_level'], 'HIGH')

        # Query sin PII
        good_query = "What is machine learning?"
        compliance = self.pii_service.validate_compliance(good_query)
        self.assertTrue(compliance['compliant'])
        self.assertEqual(compliance['risk_level'], 'LOW')


class TestDocumentAccessControl(unittest.TestCase):
    """Tests para control de acceso a documentos (DLAC)."""

    def setUp(self):
        """Configurar tests."""
        self.access_engine = AccessControlEngine()
        self.access_filter = DocumentAccessFilter(self.access_engine)

        # Crear política de prueba
        policy = AccessPolicy(
            name="confidential_policy",
            access_level=AccessLevel.CONFIDENTIAL,
            allowed_roles={"admin", "manager"}
        )
        self.access_engine.add_policy(policy)

    def test_public_document_access(self):
        """Test acceso a documento público."""
        user = UserContext(user_id=1, clearance_level=AccessLevel.PUBLIC)
        doc_metadata = DocumentMetadata(
            document_id="doc1",
            access_level=AccessLevel.PUBLIC
        )

        decision = self.access_engine.evaluate_access(user, doc_metadata)
        self.assertEqual(decision, AccessDecision.ALLOW)

    def test_confidential_document_access_denied(self):
        """Test acceso denegado a documento confidencial."""
        user = UserContext(user_id=1, clearance_level=AccessLevel.INTERNAL)
        doc_metadata = DocumentMetadata(
            document_id="doc2",
            access_level=AccessLevel.CONFIDENTIAL
        )

        decision = self.access_engine.evaluate_access(user, doc_metadata)
        self.assertEqual(decision, AccessDecision.DENY)

    def test_confidential_document_access_allowed_by_role(self):
        """Test acceso permitido por rol."""
        user = UserContext(
            user_id=1,
            roles={"admin"},
            clearance_level=AccessLevel.INTERNAL
        )
        doc_metadata = DocumentMetadata(
            document_id="doc2",
            access_level=AccessLevel.CONFIDENTIAL
        )

        decision = self.access_engine.evaluate_access(user, doc_metadata)
        self.assertEqual(decision, AccessDecision.ALLOW)

    def test_owner_access(self):
        """Test acceso del propietario."""
        user = UserContext(user_id=1, clearance_level=AccessLevel.PUBLIC)
        doc_metadata = DocumentMetadata(
            document_id="doc3",
            access_level=AccessLevel.SECRET,
            owner_id=1
        )

        decision = self.access_engine.evaluate_access(user, doc_metadata)
        self.assertEqual(decision, AccessDecision.ALLOW)

    def test_explicit_user_allowance(self):
        """Test permiso explícito de usuario."""
        user = UserContext(user_id=1, clearance_level=AccessLevel.PUBLIC)
        doc_metadata = DocumentMetadata(
            document_id="doc4",
            access_level=AccessLevel.RESTRICTED,
            allowed_users={1, 2, 3}
        )

        decision = self.access_engine.evaluate_access(user, doc_metadata)
        self.assertEqual(decision, AccessDecision.ALLOW)

    def test_user_denial(self):
        """Test denegación explícita de usuario."""
        user = UserContext(user_id=1, clearance_level=AccessLevel.SECRET)
        doc_metadata = DocumentMetadata(
            document_id="doc5",
            access_level=AccessLevel.PUBLIC,
            denied_users={1}
        )

        decision = self.access_engine.evaluate_access(user, doc_metadata)
        self.assertEqual(decision, AccessDecision.DENY)

    def test_expired_document(self):
        """Test acceso a documento expirado."""
        user = UserContext(user_id=1, clearance_level=AccessLevel.SECRET)
        past_time = datetime.now() - timedelta(days=1)
        doc_metadata = DocumentMetadata(
            document_id="doc6",
            access_level=AccessLevel.PUBLIC,
            expires_at=past_time
        )

        decision = self.access_engine.evaluate_access(user, doc_metadata)
        self.assertEqual(decision, AccessDecision.DENY)

    def test_document_filtering(self):
        """Test filtrado de documentos basado en acceso."""
        # Usuario con acceso limitado
        user = UserContext(user_id=1, clearance_level=AccessLevel.INTERNAL)

        # Documentos de prueba
        documents = [
            ({"id": "public_doc", "content": "Public info", "access_level": "public"}, 0.9),
            ({"id": "confidential_doc", "content": "Secret info", "access_level": "confidential"}, 0.8),
            ({"id": "internal_doc", "content": "Internal info", "access_level": "internal"}, 0.7)
        ]

        filtered = self.access_filter.filter_results(user, documents)

        # Debería obtener solo documentos públicos e internos
        self.assertEqual(len(filtered), 2)
        doc_ids = [doc["id"] for doc, score in filtered]
        self.assertIn("public_doc", doc_ids)
        self.assertIn("internal_doc", doc_ids)
        self.assertNotIn("confidential_doc", doc_ids)


class TestPreprocessingPipeline(unittest.TestCase):
    """Tests para el pipeline completo de preprocesamiento."""

    def setUp(self):
        """Configurar tests."""
        self.pipeline = RAGPreprocessingPipeline()

    def test_full_pipeline_pii_filtering(self):
        """Test pipeline completo con filtrado PII."""
        query = "Contact test.user@example.com or call 999-888-7777"
        result = self.pipeline.preprocess(query, user_id=1)

        self.assertNotEqual(result['original_query'], result['processed_query'])
        self.assertTrue(result['pipeline_metadata']['total_steps'] > 0)
        self.assertIn('pii_filtered_at', result['processing_details']['processing_metadata'])

    def test_pipeline_validation(self):
        """Test validación de configuración del pipeline."""
        errors = self.pipeline.validate_pipeline_config()
        self.assertEqual(len(errors), 0)  # Configuración por defecto debería ser válida

    def test_pipeline_with_empty_config(self):
        """Test pipeline con configuración mínima."""
        from ..core.preprocessing import PreprocessingConfig
        config = PreprocessingConfig()
        pipeline = RAGPreprocessingPipeline(config)

        result = pipeline.preprocess("Test query", user_id=1)
        self.assertEqual(result['processed_query'], "test query")  # Solo lowercase


class TestIntegratedSecurity(unittest.TestCase):
    """Tests para integración completa de seguridad."""

    def setUp(self):
        """Configurar tests."""
        # Mock RAG system components
        self.mock_retriever = Mock()
        self.mock_generator = Mock()
        self.mock_evaluator = Mock()

        # Configurar mocks
        self.mock_retriever.retrieve.return_value = [
            {"id": "doc1", "content": "Public content", "access_level": "public"},
            {"id": "doc2", "content": "Secret content", "access_level": "secret"}
        ]
        self.mock_generator.generate.return_value = "Generated response"
        self.mock_evaluator.evaluate.return_value = {"accuracy": 0.85}

    @patch('src.ailoos.rag.core.base_rag.RAGPreprocessingPipeline')
    @patch('src.ailoos.rag.core.base_rag.DocumentAccessFilter')
    def test_rag_pipeline_with_security(self, mock_access_filter, mock_preprocessing):
        """Test pipeline RAG completo con seguridad."""
        from ..core.base_rag import BaseRAG

        # Configurar mocks
        mock_prep_instance = Mock()
        mock_prep_instance.preprocess.return_value = {
            'processed_query': 'processed query',
            'processing_details': {'pii_detected': True, 'pii_changes': []}
        }
        mock_preprocessing.return_value = mock_prep_instance

        mock_filter_instance = Mock()
        mock_filter_instance.filter_results.return_value = [
            ({"id": "doc1", "content": "Public content"}, 0.9)
        ]
        mock_access_filter.return_value = mock_filter_instance

        # Crear RAG system mock
        config = {}
        rag = BaseRAG(config)
        rag.retriever = self.mock_retriever
        rag.generator = self.mock_generator
        rag.evaluator = self.mock_evaluator

        # Usuario de prueba
        user_context = UserContext(user_id=1, clearance_level=AccessLevel.INTERNAL)

        # Ejecutar pipeline
        result = rag.run("Test query with PII", user_context=user_context)

        # Verificar que se llamaron los componentes de seguridad
        mock_prep_instance.preprocess.assert_called_once()
        mock_filter_instance.filter_results.assert_called_once()

        # Verificar resultado
        self.assertIn('security_info', result)
        self.assertIn('processed_query', result)
        self.assertEqual(len(result['context']), 1)  # Solo documento permitido


class TestAuditLogging(unittest.TestCase):
    """Tests para logging de auditoría."""

    def setUp(self):
        """Configurar tests."""
        self.pii_service = PIIFilterService()
        self.access_engine = AccessControlEngine()

    def test_pii_audit_log(self):
        """Test logging de auditoría para PII."""
        query = "Email: test@example.com"
        self.pii_service.preprocess_query(query, user_id=1)

        audit_log = self.pii_service.detector.get_audit_log()
        self.assertEqual(len(audit_log), 1)
        self.assertEqual(audit_log[0]['category'], 'email')
        self.assertEqual(audit_log[0]['user_id'], 1)

    def test_access_control_audit_log(self):
        """Test logging de auditoría para control de acceso."""
        user = UserContext(user_id=1, clearance_level=AccessLevel.PUBLIC)
        doc_metadata = DocumentMetadata(
            document_id="test_doc",
            access_level=AccessLevel.CONFIDENTIAL
        )

        self.access_engine.evaluate_access(user, doc_metadata)

        audit_log = self.access_engine.get_audit_log()
        self.assertEqual(len(audit_log), 1)
        self.assertEqual(audit_log[0]['decision'], 'deny')
        self.assertEqual(audit_log[0]['user_id'], 1)


if __name__ == '__main__':
    unittest.main()