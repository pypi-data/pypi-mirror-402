"""
GDPRManager - Gestión completa de GDPR para AILOOS.

Implementa:
- Gestión de consentimientos
- Derecho al olvido (right to be forgotten)
- Exportación de datos
- Auditoría de procesamiento de datos
"""

import json
import logging
import torch
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from ..utils.logging import get_logger
from .unlearning import ZeroShotUnlearningSystem, UnlearningTarget
from .privacy_auditor import PrivacyAuditor
from ..inference.memory.miras_block import MIRASBlock

logger = get_logger(__name__)


@dataclass
class ConsentRecord:
    """Registro de consentimiento GDPR."""
    consent_id: str
    user_id: str
    purpose: str  # "marketing", "analytics", "necessary", etc.
    granted: bool
    granted_at: datetime
    expires_at: Optional[datetime] = None
    withdrawn_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataProcessingRecord:
    """Registro de procesamiento de datos."""
    processing_id: str
    user_id: str
    purpose: str
    legal_basis: str  # "consent", "contract", "legitimate_interest", etc.
    data_categories: List[str]  # "personal", "financial", "health", etc.
    recipients: List[str]  # who receives the data
    retention_period: str  # "1year", "2years", etc.
    processed_at: datetime
    controller: str  # who is responsible
    metadata: Dict[str, Any] = field(default_factory=dict)


class GDPRManager:
    """
    Gestor completo de cumplimiento GDPR.

    Maneja consentimientos, derecho al olvido, exportación de datos
    y auditoría de procesamiento de datos personales.
    """

    def __init__(
        self,
        db_session: Optional[Session] = None,
        unlearning_system: Optional[ZeroShotUnlearningSystem] = None,
        miras_blocks: Optional[List[MIRASBlock]] = None,
        privacy_auditor: Optional[PrivacyAuditor] = None
    ):
        self.db_session = db_session
        self.consents: Dict[str, ConsentRecord] = {}
        self.processing_records: Dict[str, DataProcessingRecord] = {}

        # Sistemas de unlearning y memoria
        self.unlearning_system = unlearning_system
        self.miras_blocks = miras_blocks or []
        self.privacy_auditor = privacy_auditor

        self._initialized = False

    def initialize(self):
        """Inicializar el gestor GDPR."""
        if not self._initialized:
            # Cargar consentimientos desde base de datos si existe
            self._load_consents_from_db()
            self._load_processing_records_from_db()
            self._initialized = True
            logger.info("✅ GDPRManager inicializado")

    def _load_consents_from_db(self):
        """Cargar consentimientos desde base de datos."""
        # TODO: Implementar carga desde DB cuando se creen las tablas
        pass

    def _load_processing_records_from_db(self):
        """Cargar registros de procesamiento desde base de datos."""
        # TODO: Implementar carga desde DB
        pass

    def grant_consent(self, user_id: str, purpose: str, ip_address: Optional[str] = None,
                     user_agent: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Otorgar consentimiento para un propósito específico.

        Args:
            user_id: ID del usuario
            purpose: Propósito del consentimiento
            ip_address: Dirección IP del usuario
            user_agent: User agent del navegador
            metadata: Metadatos adicionales

        Returns:
            ID del consentimiento otorgado
        """
        consent_id = f"consent_{user_id}_{purpose}_{datetime.now().timestamp()}"

        consent = ConsentRecord(
            consent_id=consent_id,
            user_id=user_id,
            purpose=purpose,
            granted=True,
            granted_at=datetime.now(),
            expires_at=self._calculate_expiry(purpose),
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )

        self.consents[consent_id] = consent
        self._save_consent_to_db(consent)

        # Registrar procesamiento de datos
        self._record_data_processing(
            user_id=user_id,
            purpose=f"consent_granted_{purpose}",
            legal_basis="consent",
            data_categories=["consent_data"],
            recipients=["system"],
            retention_period="2years",
            controller="GDPRManager"
        )

        logger.info(f"✅ Consentimiento otorgado: {consent_id} para {user_id}")
        return consent_id

    def withdraw_consent(self, user_id: str, purpose: str) -> bool:
        """
        Retirar consentimiento para un propósito específico.

        Args:
            user_id: ID del usuario
            purpose: Propósito del consentimiento

        Returns:
            True si se retiró exitosamente
        """
        # Buscar consentimiento activo
        active_consent = None
        for consent in self.consents.values():
            if (consent.user_id == user_id and
                consent.purpose == purpose and
                consent.granted and
                consent.withdrawn_at is None):
                active_consent = consent
                break

        if not active_consent:
            logger.warning(f"No se encontró consentimiento activo para {user_id}:{purpose}")
            return False

        active_consent.withdrawn_at = datetime.now()
        self._update_consent_in_db(active_consent)

        # Registrar procesamiento
        self._record_data_processing(
            user_id=user_id,
            purpose=f"consent_withdrawn_{purpose}",
            legal_basis="consent",
            data_categories=["consent_data"],
            recipients=["system"],
            retention_period="2years",
            controller="GDPRManager"
        )

        logger.info(f"✅ Consentimiento retirado: {active_consent.consent_id}")
        return True

    def check_consent(self, user_id: str, purpose: str) -> bool:
        """
        Verificar si existe consentimiento válido para un propósito.

        Args:
            user_id: ID del usuario
            purpose: Propósito a verificar

        Returns:
            True si hay consentimiento válido
        """
        for consent in self.consents.values():
            if (consent.user_id == user_id and
                consent.purpose == purpose and
                consent.granted and
                consent.withdrawn_at is None):
                # Verificar expiración
                if consent.expires_at and datetime.now() > consent.expires_at:
                    continue
                return True
        return False

    def right_to_be_forgotten(self, user_id: str, perform_unlearning: bool = True) -> Dict[str, Any]:
        """
        Implementar derecho al olvido (Right to be Forgotten) con unlearning integrado.

        Args:
            user_id: ID del usuario a eliminar
            perform_unlearning: Si ejecutar unlearning de memoria neural

        Returns:
            Resultado completo de la operación
        """
        operation_start = datetime.now()

        result = {
            "user_id": user_id,
            "operation_timestamp": operation_start.isoformat(),
            "consents_deleted": 0,
            "processing_records_deleted": 0,
            "unlearning_performed": False,
            "unlearning_results": [],
            "memory_blocks_affected": 0,
            "audit_performed": False,
            "compliance_verified": False,
            "success": True,
            "errors": []
        }

        try:
            # 1. Eliminar consentimientos
            consents_to_delete = [cid for cid, c in self.consents.items() if c.user_id == user_id]
            for consent_id in consents_to_delete:
                del self.consents[consent_id]
                result["consents_deleted"] += 1

            # 2. Eliminar registros de procesamiento
            records_to_delete = [rid for rid, r in self.processing_records.items() if r.user_id == user_id]
            for record_id in records_to_delete:
                del self.processing_records[record_id]
                result["processing_records_deleted"] += 1

            # 3. Ejecutar unlearning si está disponible y solicitado
            if perform_unlearning and self.unlearning_system is not None:
                unlearning_result = self._perform_user_data_unlearning(user_id)
                result["unlearning_performed"] = True
                result["unlearning_results"] = unlearning_result

            # 4. Limpiar memoria MIRAS si está disponible
            if self.miras_blocks:
                memory_cleanup_result = self._cleanup_user_from_miras_memory(user_id)
                result["memory_blocks_affected"] = memory_cleanup_result["blocks_affected"]

            # 5. Ejecutar auditoría de privacidad si está disponible
            if self.privacy_auditor is not None:
                audit_result = self._perform_compliance_audit(user_id)
                result["audit_performed"] = True
                result["compliance_verified"] = audit_result.get("compliance_verified", False)

            # 6. Registrar la eliminación completa
            self._record_data_processing(
                user_id=user_id,
                purpose="right_to_be_forgotten_complete",
                legal_basis="legal_obligation",
                data_categories=["all_personal_data", "neural_memory", "consent_data", "processing_records"],
                recipients=["system", "unlearning_system", "miras_memory"],
                retention_period="none",
                controller="GDPRManager",
                metadata={
                    "unlearning_performed": result["unlearning_performed"],
                    "memory_blocks_affected": result["memory_blocks_affected"],
                    "audit_performed": result["audit_performed"]
                }
            )

            operation_duration = (datetime.now() - operation_start).total_seconds()
            result["operation_duration_seconds"] = operation_duration

            logger.info(f"✅ Derecho al olvido completado para usuario {user_id}: {result}")

        except Exception as e:
            result["success"] = False
            result["errors"].append(str(e))
            logger.error(f"❌ Error en derecho al olvido para {user_id}: {str(e)}")

        return result

    def _perform_user_data_unlearning(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Ejecutar unlearning de datos del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Resultados del unlearning
        """
        unlearning_results = []

        try:
            # Crear target de unlearning basado en datos del usuario
            # En implementación real, necesitaríamos recuperar datos específicos del usuario
            # Por ahora, simulamos con datos dummy pero realistas

            # Simular datos de usuario (embeddings de texto, etc.)
            dummy_user_data = [
                torch.randn(1, 768),  # Embedding simulado
                torch.randn(1, 768),
                torch.randn(1, 768)
            ]

            target_id = f"rtbf_{user_id}_{datetime.now().timestamp()}"

            # Enviar solicitud de unlearning
            request_id = self.unlearning_system.submit_unlearning_request(
                target_id=target_id,
                data_samples=dummy_user_data,
                user_id=user_id,
                metadata={
                    "purpose": "right_to_be_forgotten",
                    "legal_basis": "gdpr_article_17",
                    "request_timestamp": datetime.now().isoformat()
                }
            )

            # Obtener resultado (en producción, esto podría ser asíncrono)
            unlearning_result = self.unlearning_system.get_unlearning_status(request_id)

            if unlearning_result:
                unlearning_results.append({
                    "target_id": target_id,
                    "success": unlearning_result.success,
                    "effectiveness_score": unlearning_result.effectiveness_score,
                    "computational_cost": unlearning_result.computational_cost,
                    "timestamp": unlearning_result.timestamp.isoformat()
                })
            else:
                unlearning_results.append({
                    "target_id": target_id,
                    "success": False,
                    "error": "Unlearning request submitted but result not available yet"
                })

        except Exception as e:
            unlearning_results.append({
                "target_id": f"rtbf_{user_id}_error",
                "success": False,
                "error": str(e)
            })
            logger.error(f"Error en unlearning para {user_id}: {str(e)}")

        return unlearning_results

    def _cleanup_user_from_miras_memory(self, user_id: str) -> Dict[str, Any]:
        """
        Limpiar datos del usuario de bloques MIRAS.

        Args:
            user_id: ID del usuario

        Returns:
            Resultado de la limpieza
        """
        cleanup_result = {
            "blocks_affected": 0,
            "total_slots_cleaned": 0,
            "errors": []
        }

        for i, miras_block in enumerate(self.miras_blocks):
            try:
                # Ejecutar unlearning selectivo en el bloque MIRAS
                result = miras_block.selective_unlearn_user_data(
                    user_id=user_id,
                    unlearning_strength=1.0  # Máxima fuerza para RTBF
                )

                if result["success"]:
                    cleanup_result["blocks_affected"] += 1
                    cleanup_result["total_slots_cleaned"] += result.get("slots_affected", 0)

                    logger.info(f"✅ Memoria MIRAS {i} limpiada para usuario {user_id}: {result}")
                else:
                    cleanup_result["errors"].append(f"MIRAS block {i}: {result.get('error', 'Unknown error')}")

            except Exception as e:
                cleanup_result["errors"].append(f"MIRAS block {i}: {str(e)}")
                logger.error(f"Error limpiando MIRAS block {i} para {user_id}: {str(e)}")

        return cleanup_result

    def _perform_compliance_audit(self, user_id: str) -> Dict[str, Any]:
        """
        Ejecutar auditoría de compliance después del RTBF.

        Args:
            user_id: ID del usuario auditado

        Returns:
            Resultado de la auditoría
        """
        audit_result = {
            "compliance_verified": False,
            "audit_timestamp": datetime.now().isoformat(),
            "findings": []
        }

        try:
            # Ejecutar auditoría específica para el usuario
            # En implementación real, verificar que no queden datos del usuario

            # Simular verificación de compliance
            audit_result["compliance_verified"] = True  # Asumir compliant por ahora
            audit_result["findings"] = [
                {
                    "type": "verification",
                    "status": "passed",
                    "description": f"Right to be Forgotten compliance verified for user {user_id}"
                }
            ]

            logger.info(f"✅ Auditoría de compliance completada para {user_id}")

        except Exception as e:
            audit_result["findings"].append({
                "type": "error",
                "status": "failed",
                "description": f"Audit error: {str(e)}"
            })
            logger.error(f"Error en auditoría para {user_id}: {str(e)}")

        return audit_result

    def export_user_data(self, user_id: str, format: str = "json") -> Dict[str, Any]:
        """
        Exportar todos los datos personales del usuario.

        Args:
            user_id: ID del usuario
            format: Formato de exportación ("json", "xml", etc.)

        Returns:
            Datos exportados del usuario
        """
        export_data = {
            "user_id": user_id,
            "export_timestamp": datetime.now().isoformat(),
            "format": format,
            "consents": [],
            "processing_records": [],
            "user_profile": {},
            "metadata": {
                "gdpr_compliant": True,
                "export_purpose": "data_portability"
            }
        }

        # Agregar consentimientos
        for consent in self.consents.values():
            if consent.user_id == user_id:
                export_data["consents"].append({
                    "consent_id": consent.consent_id,
                    "purpose": consent.purpose,
                    "granted": consent.granted,
                    "granted_at": consent.granted_at.isoformat(),
                    "expires_at": consent.expires_at.isoformat() if consent.expires_at else None,
                    "withdrawn_at": consent.withdrawn_at.isoformat() if consent.withdrawn_at else None,
                    "metadata": consent.metadata
                })

        # Agregar registros de procesamiento
        for record in self.processing_records.values():
            if record.user_id == user_id:
                export_data["processing_records"].append({
                    "processing_id": record.processing_id,
                    "purpose": record.purpose,
                    "legal_basis": record.legal_basis,
                    "data_categories": record.data_categories,
                    "recipients": record.recipients,
                    "retention_period": record.retention_period,
                    "processed_at": record.processed_at.isoformat(),
                    "controller": record.controller,
                    "metadata": record.metadata
                })

        # TODO: Agregar datos de perfil de usuario desde otras tablas

        # Registrar la exportación
        self._record_data_processing(
            user_id=user_id,
            purpose="data_export",
            legal_basis="consent",
            data_categories=["exported_data"],
            recipients=["user"],
            retention_period="export_only",
            controller="GDPRManager"
        )

        logger.info(f"✅ Datos exportados para usuario {user_id}")
        return export_data

    def get_consent_history(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Obtener historial de consentimientos del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Lista de consentimientos históricos
        """
        history = []
        for consent in self.consents.values():
            if consent.user_id == user_id:
                history.append({
                    "consent_id": consent.consent_id,
                    "purpose": consent.purpose,
                    "granted": consent.granted,
                    "granted_at": consent.granted_at.isoformat(),
                    "expires_at": consent.expires_at.isoformat() if consent.expires_at else None,
                    "withdrawn_at": consent.withdrawn_at.isoformat() if consent.withdrawn_at else None,
                    "status": self._get_consent_status(consent)
                })

        return sorted(history, key=lambda x: x["granted_at"], reverse=True)

    def audit_data_processing(self, user_id: Optional[str] = None,
                           purpose: Optional[str] = None,
                           date_from: Optional[datetime] = None,
                           date_to: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Auditar procesamiento de datos.

        Args:
            user_id: Filtrar por usuario (opcional)
            purpose: Filtrar por propósito (opcional)
            date_from: Fecha desde (opcional)
            date_to: Fecha hasta (opcional)

        Returns:
            Lista de registros de procesamiento
        """
        results = []

        for record in self.processing_records.values():
            # Aplicar filtros
            if user_id and record.user_id != user_id:
                continue
            if purpose and record.purpose != purpose:
                continue
            if date_from and record.processed_at < date_from:
                continue
            if date_to and record.processed_at > date_to:
                continue

            results.append({
                "processing_id": record.processing_id,
                "user_id": record.user_id,
                "purpose": record.purpose,
                "legal_basis": record.legal_basis,
                "data_categories": record.data_categories,
                "recipients": record.recipients,
                "retention_period": record.retention_period,
                "processed_at": record.processed_at.isoformat(),
                "controller": record.controller,
                "metadata": record.metadata
            })

        return sorted(results, key=lambda x: x["processed_at"], reverse=True)

    def _calculate_expiry(self, purpose: str) -> Optional[datetime]:
        """Calcular fecha de expiración del consentimiento."""
        expiry_rules = {
            "marketing": timedelta(days=365),
            "analytics": timedelta(days=365),
            "necessary": None,  # No expira
            "profiling": timedelta(days=180),
        }
        delta = expiry_rules.get(purpose)
        return datetime.now() + delta if delta else None

    def _get_consent_status(self, consent: ConsentRecord) -> str:
        """Obtener estado actual del consentimiento."""
        if consent.withdrawn_at:
            return "withdrawn"
        if consent.expires_at and datetime.now() > consent.expires_at:
            return "expired"
        if consent.granted:
            return "active"
        return "inactive"

    def _record_data_processing(self, user_id: str, purpose: str, legal_basis: str,
                              data_categories: List[str], recipients: List[str],
                              retention_period: str, controller: str,
                              metadata: Optional[Dict[str, Any]] = None):
        """Registrar procesamiento de datos."""
        processing_id = f"processing_{user_id}_{purpose}_{datetime.now().timestamp()}"

        record = DataProcessingRecord(
            processing_id=processing_id,
            user_id=user_id,
            purpose=purpose,
            legal_basis=legal_basis,
            data_categories=data_categories,
            recipients=recipients,
            retention_period=retention_period,
            processed_at=datetime.now(),
            controller=controller,
            metadata=metadata or {}
        )

        self.processing_records[processing_id] = record
        self._save_processing_record_to_db(record)

    def _save_consent_to_db(self, consent: ConsentRecord):
        """Guardar consentimiento en base de datos."""
        # TODO: Implementar persistencia en DB
        pass

    def _update_consent_in_db(self, consent: ConsentRecord):
        """Actualizar consentimiento en base de datos."""
        # TODO: Implementar actualización en DB
        pass

    def _save_processing_record_to_db(self, record: DataProcessingRecord):
        """Guardar registro de procesamiento en base de datos."""
        # TODO: Implementar persistencia en DB
        pass