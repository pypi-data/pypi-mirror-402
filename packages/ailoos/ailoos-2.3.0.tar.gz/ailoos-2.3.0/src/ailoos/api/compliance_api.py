"""
API de Compliance para AILOOS.
Proporciona endpoints para auditoría, KYC/AML, detección de Sybil y logging con ZK proofs.
Implementa integración completa con OracleAuditor, ZKAuditLogger y SybilProtector.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from ..auditing.oracle_auditor import OracleAuditor, OracleAuditorError
from ..auditing.zk_audit_logger import ZKAuditLogger
from ..security.sybil_protector import SybilProtector, SybilProtectionError
from ..coordinator.auth.jwt import get_current_token_data, TokenData, require_permissions
from ..coordinator.database.connection import get_db
from ..core.state_manager import get_state_manager, ComponentStatus
from ..core.event_system import get_event_bus, publish_system_event
from ..utils.logging import get_logger

# Importar nuevo ComplianceManager de FASE 8
from ..compliance import ComplianceManager

logger = get_logger(__name__)

# Crear router
router = APIRouter(
    prefix="/compliance",
    tags=["compliance"],
    responses={404: {"description": "Not found"}},
)


# Modelos Pydantic para requests y responses

class AuditRequest(BaseModel):
    """Request para auditoría de transacción."""
    transaction_id: str = Field(..., description="ID único de la transacción")
    transaction_data: Dict[str, Any] = Field(..., description="Datos de la transacción")
    rules: Optional[List[Dict[str, Any]]] = Field(None, description="Reglas de auditoría personalizadas")

    @validator('transaction_data')
    def validate_transaction_data(cls, v):
        required_fields = ['amount', 'currency']
        if not all(field in v for field in required_fields):
            raise ValueError(f"Datos de transacción deben incluir: {required_fields}")
        return v


class KYCRequest(BaseModel):
    """Request para verificación KYC/AML."""
    user_id: str = Field(..., description="ID del usuario")
    transaction_data: Dict[str, Any] = Field(..., description="Datos de la transacción")
    risk_threshold: Optional[float] = Field(10000.0, description="Umbral de riesgo en USD")


class AMLRequest(BaseModel):
    """Request para análisis AML."""
    user_id: str = Field(..., description="ID del usuario")
    transaction_data: Dict[str, Any] = Field(..., description="Datos de la transacción")
    check_history: Optional[bool] = Field(True, description="Verificar historial de transacciones")


class SybilCheckRequest(BaseModel):
    """Request para detección de ataques Sybil."""
    user_data: Dict[str, Any] = Field(..., description="Datos del usuario para análisis")

    @validator('user_data')
    def validate_user_data(cls, v):
        required_fields = ['user_id']
        if not all(field in v for field in required_fields):
            raise ValueError(f"Datos de usuario deben incluir: {required_fields}")
        return v


class ZKLogsRequest(BaseModel):
    """Request para consulta de logs ZK."""
    user_id: Optional[str] = Field(None, description="Filtrar por ID de usuario")
    action_type: Optional[str] = Field(None, description="Filtrar por tipo de acción")
    date_from: Optional[datetime] = Field(None, description="Fecha desde")
    date_to: Optional[datetime] = Field(None, description="Fecha hasta")
    verified_only: Optional[bool] = Field(False, description="Solo logs verificados")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Límite de resultados")


# === Modelos para ComplianceManager FASE 8 ===

class ConsentRequest(BaseModel):
    """Request para gestión de consentimientos GDPR."""
    user_id: str = Field(..., description="ID del usuario")
    purpose: str = Field(..., description="Propósito del consentimiento")
    ip_address: Optional[str] = Field(None, description="Dirección IP")
    user_agent: Optional[str] = Field(None, description="User agent")


class DataExportRequest(BaseModel):
    """Request para exportación de datos."""
    user_id: str = Field(..., description="ID del usuario")
    format: str = Field("json", description="Formato de exportación")


class RightToBeForgottenRequest(BaseModel):
    """Request para derecho al olvido."""
    user_id: str = Field(..., description="ID del usuario")


class PHIRequest(BaseModel):
    """Request para acceso a PHI."""
    patient_id: str = Field(..., description="ID del paciente")
    accessor_id: str = Field(..., description="ID del accessor")
    accessor_role: str = Field(..., description="Rol del accessor")
    purpose: str = Field(..., description="Propósito del acceso")
    data_requested: List[str] = Field(..., description="Datos solicitados")


class BreachReportRequest(BaseModel):
    """Request para reporte de brecha."""
    patient_ids_affected: List[str] = Field(..., description="IDs de pacientes afectados")
    data_breached: List[str] = Field(..., description="Datos comprometidos")
    breach_date: datetime = Field(..., description="Fecha de la brecha")
    risk_assessment: str = Field(..., description="Evaluación de riesgo")


class FinancialTransactionRequest(BaseModel):
    """Request para transacción financiera."""
    transaction_type: str = Field(..., description="Tipo de transacción")
    amount: float = Field(..., description="Monto")
    currency: str = Field("USD", description="Moneda")
    initiator: str = Field(..., description="Iniciador")
    description: str = Field(..., description="Descripción")


class TransactionApprovalRequest(BaseModel):
    """Request para aprobación de transacción."""
    transaction_id: str = Field(..., description="ID de la transacción")
    approver: str = Field(..., description="Aprobador")


class DataSubjectRightRequest(BaseModel):
    """Request para derecho del interesado."""
    user_id: str = Field(..., description="ID del usuario")
    right: str = Field(..., description="Derecho solicitado")
    description: str = Field("", description="Descripción")


class ProcessRightRequest(BaseModel):
    """Request para procesar derecho."""
    request_id: str = Field(..., description="ID de la solicitud")
    assigned_to: str = Field(..., description="Asignado a")
    status: str = Field(..., description="Nuevo estado")
    response: str = Field("", description="Respuesta")


class ComplianceAuditRequest(BaseModel):
    """Request para auditoría."""
    audit_type: str = Field("on_demand", description="Tipo de auditoría")
    regulations: List[str] = Field(..., description="Regulaciones a auditar")
    scope: str = Field(..., description="Alcance")


class DataRetentionRequest(BaseModel):
    """Request para registro de retención."""
    user_id: Optional[str] = Field(None, description="ID del usuario")
    data_category: str = Field(..., description="Categoría de datos")
    regulation: str = Field(..., description="Regulación")


class DataDeletionRequest(BaseModel):
    """Request para eliminación de datos."""
    record_ids: List[str] = Field(..., description="IDs de registros")
    scheduled_by: str = Field(..., description="Programado por")


class ComplianceResponse(BaseModel):
    """Response genérica de compliance."""
    success: bool
    data: Dict[str, Any]
    timestamp: datetime
    request_id: str


class ErrorResponse(BaseModel):
    """Response de error."""
    success: bool = False
    error: str
    error_code: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None


# Clase principal ComplianceAPI

class ComplianceAPI:
    """
    API de Compliance para AILOOS.
    Gestiona auditoría, KYC/AML, detección Sybil y logging con ZK proofs.
    """

    def __init__(self):
        self.oracle_auditor: Optional[OracleAuditor] = None
        self.zk_logger: Optional[ZKAuditLogger] = None
        self.sybil_protector: Optional[SybilProtector] = None
        self.compliance_manager: Optional[ComplianceManager] = None
        self._initialized = False

        # Integración con sistemas centrales
        self.state_manager = get_state_manager()
        self.event_bus = get_event_bus()

        # Registrar componente con nuevos endpoints
        self.state_manager.register_component("compliance_api", {
            "type": "api",
            "endpoints": ["audit", "kyc", "aml", "sybil-check", "zk-logs",
                         "gdpr", "hipaa", "sox", "data-rights", "auditor", "retention"]
        })

    def initialize_components(self):
        """Inicializar componentes de compliance."""
        try:
            if not self._initialized:
                # Actualizar estado
                self.state_manager.update_component_status("compliance_api", ComponentStatus.INITIALIZING)

                # Inicializar OracleAuditor
                self.oracle_auditor = OracleAuditor()

                # Inicializar ZKAuditLogger (necesita config)
                from ..core.config import get_config
                config = get_config()
                self.zk_logger = ZKAuditLogger(config)

                # Inicializar SybilProtector
                self.sybil_protector = SybilProtector()

                # Inicializar nuevo ComplianceManager de FASE 8
                self.compliance_manager = ComplianceManager()
                self.compliance_manager.initialize()

                self._initialized = True

                # Actualizar estado y publicar evento
                self.state_manager.update_component_status("compliance_api", ComponentStatus.RUNNING)
                asyncio.create_task(publish_system_event("compliance.initialized", {
                    "components": ["oracle_auditor", "zk_audit_logger", "sybil_protector", "compliance_manager_fase8"]
                }))

                logger.info("✅ Componentes de Compliance API inicializados")

        except Exception as e:
            # Actualizar estado de error
            self.state_manager.update_component_status("compliance_api", ComponentStatus.ERROR,
                                                     error_message=str(e))
            logger.error(f"❌ Error inicializando componentes de compliance: {e}")
            raise

    async def audit_transaction(self, request: AuditRequest) -> Dict[str, Any]:
        """Auditar transacción usando OracleAuditor."""
        if not self.oracle_auditor:
            self.initialize_components()

        try:
            result = self.oracle_auditor.audit_transaction(
                transaction_id=request.transaction_id,
                transaction_data=request.transaction_data,
                rules=request.rules
            )

            # Log de auditoría
            await self._log_compliance_action(
                action_data={
                    'action_type': 'transaction_audit',
                    'transaction_id': request.transaction_id,
                    'risk_level': result.get('overall_risk', 'unknown')
                },
                user_id=request.transaction_data.get('user_id', 'system')
            )

            return result

        except OracleAuditorError as e:
            logger.error(f"Error en auditoría de transacción {request.transaction_id}: {e}")
            raise HTTPException(status_code=400, detail=f"Error en auditoría: {str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado en auditoría: {e}")
            raise HTTPException(status_code=500, detail="Error interno del servidor")

    async def verify_kyc(self, request: KYCRequest) -> Dict[str, Any]:
        """Verificar KYC/AML usando OracleAuditor."""
        if not self.oracle_auditor:
            self.initialize_components()

        try:
            result = self.oracle_auditor.verify_kyc(
                user_id=request.user_id,
                transaction_data=request.transaction_data,
                risk_threshold=request.risk_threshold
            )

            # Log de verificación KYC
            await self._log_compliance_action(
                action_data={
                    'action_type': 'kyc_verification',
                    'compliance_status': result.get('compliance_status', 'unknown')
                },
                user_id=request.user_id
            )

            return result

        except OracleAuditorError as e:
            logger.error(f"Error en verificación KYC para {request.user_id}: {e}")
            raise HTTPException(status_code=400, detail=f"Error en verificación KYC: {str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado en KYC: {e}")
            raise HTTPException(status_code=500, detail="Error interno del servidor")

    async def analyze_aml(self, request: AMLRequest) -> Dict[str, Any]:
        """Analizar AML usando OracleAuditor."""
        if not self.oracle_auditor:
            self.initialize_components()

        try:
            # Para AML, usamos verify_identity que incluye análisis de patrones
            result = self.oracle_auditor.verify_identity(
                identity_data={'user_id': request.user_id, **request.transaction_data},
                verification_type='comprehensive'
            )

            # Log de análisis AML
            await self._log_compliance_action(
                action_data={
                    'action_type': 'aml_analysis',
                    'verification_type': 'comprehensive',
                    'overall_verified': result.get('overall_verified', False)
                },
                user_id=request.user_id
            )

            return result

        except OracleAuditorError as e:
            logger.error(f"Error en análisis AML para {request.user_id}: {e}")
            raise HTTPException(status_code=400, detail=f"Error en análisis AML: {str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado en AML: {e}")
            raise HTTPException(status_code=500, detail="Error interno del servidor")

    async def check_sybil_attack(self, request: SybilCheckRequest) -> Dict[str, Any]:
        """Detectar ataques Sybil usando SybilProtector."""
        if not self.sybil_protector:
            self.initialize_components()

        try:
            # Verificar proof-of-humanity
            human_verification = self.sybil_protector.verify_human(
                user_id=request.user_data.get('user_id'),
                proof_data=request.user_data
            )

            # Detectar patrones Sybil
            pattern_detection = self.sybil_protector.detect_sybil_patterns(
                user_data=request.user_data
            )

            # Validar identidad única
            identity_validation = self.sybil_protector.validate_unique_identity(
                identity_hash=str(hash(str(request.user_data))),
                user_data=request.user_data
            )

            result = {
                'user_id': request.user_data.get('user_id'),
                'human_verification': human_verification,
                'pattern_analysis': pattern_detection,
                'identity_validation': identity_validation,
                'overall_risk': max(
                    pattern_detection.get('risk_score', 0),
                    0 if human_verification.get('is_human', False) else 1
                ),
                'recommendations': pattern_detection.get('recommendations', [])
            }

            # Log de detección Sybil
            await self._log_compliance_action(
                action_data={
                    'action_type': 'sybil_detection',
                    'is_suspicious': pattern_detection.get('is_suspicious', False),
                    'risk_score': result['overall_risk']
                },
                user_id=request.user_data.get('user_id')
            )

            return result

        except SybilProtectionError as e:
            logger.error(f"Error en detección Sybil para {request.user_data.get('user_id')}: {e}")
            raise HTTPException(status_code=400, detail=f"Error en detección Sybil: {str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado en Sybil check: {e}")
            raise HTTPException(status_code=500, detail="Error interno del servidor")

    async def query_zk_logs(self, request: ZKLogsRequest) -> Dict[str, Any]:
        """Consultar logs de auditoría con ZK proofs."""
        if not self.zk_logger:
            self.initialize_components()

        try:
            result = await self.zk_logger.query_audit_logs(
                user_id=request.user_id,
                action_type=request.action_type,
                date_from=request.date_from,
                date_to=request.date_to,
                verified_only=request.verified_only,
                limit=request.limit
            )

            # Convertir a dict serializable
            logs_data = []
            for log in result.logs:
                log_dict = {
                    'log_id': log.log_id,
                    'user_id': log.user_id,
                    'action_type': log.action_type,
                    'timestamp': log.timestamp.isoformat(),
                    'compliance_proof_id': log.compliance_proof.proof_id,
                    'metadata': log.metadata,
                    'proof_verified': log.compliance_proof.verified,
                    'ipfs_cid': log.ipfs_cid,
                    'blockchain_tx_hash': log.blockchain_tx_hash
                }
                logs_data.append(log_dict)

            return {
                'logs': logs_data,
                'total_count': result.total_count,
                'verified_proofs': result.verified_proofs,
                'query_timestamp': result.query_timestamp.isoformat()
            }

        except Exception as e:
            logger.error(f"Error consultando logs ZK: {e}")
            raise HTTPException(status_code=500, detail="Error interno del servidor")

    async def _log_compliance_action(self, action_data: Dict[str, Any], user_id: str):
        """Log acción de compliance usando ZKAuditLogger."""
        try:
            if self.zk_logger:
                await self.zk_logger.log_compliant_action(
                    action_data=action_data,
                    user_id=user_id,
                    compliance_rules=['GDPR_Article_6', 'GDPR_Article_9', 'Data_Minimization']
                )
        except Exception as e:
            logger.warning(f"Error logging compliance action: {e}")


# Instancia global de la API
compliance_api = ComplianceAPI()


# Endpoints FastAPI

@router.options("/audit")
async def options_audit():
    """OPTIONS handler for audit endpoint."""
    return {"Allow": "POST, OPTIONS"}

@router.post("/audit", response_model=ComplianceResponse)
async def audit_transaction(
    request: AuditRequest,
    background_tasks: BackgroundTasks,
    token_data: TokenData = Depends(require_permissions(["compliance:audit"])),
    db: Session = Depends(get_db)
):
    """
    Auditar transacción usando oráculos blockchain.

    **Parámetros:**
    - **transaction_id**: ID único de la transacción
    - **transaction_data**: Datos de la transacción (amount, currency, etc.)
    - **rules**: Reglas de auditoría opcionales

    **Requiere permisos:** compliance:audit

    **Retorna:** Resultado de auditoría con nivel de riesgo
    """
    try:
        result = await compliance_api.audit_transaction(request)

        return ComplianceResponse(
            success=True,
            data=result,
            timestamp=datetime.utcnow(),
            request_id=f"audit_{request.transaction_id}_{datetime.utcnow().timestamp()}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint /audit: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/kyc", response_model=ComplianceResponse)
async def verify_kyc(
    request: KYCRequest,
    background_tasks: BackgroundTasks,
    token_data: TokenData = Depends(require_permissions(["compliance:kyc"])),
    db: Session = Depends(get_db)
):
    """
    Verificar cumplimiento KYC/AML usando oráculos.

    **Parámetros:**
    - **user_id**: ID del usuario
    - **transaction_data**: Datos de la transacción
    - **risk_threshold**: Umbral de riesgo en USD (opcional)

    **Requiere permisos:** compliance:kyc

    **Retorna:** Resultado de verificación con estado de cumplimiento
    """
    try:
        result = await compliance_api.verify_kyc(request)

        return ComplianceResponse(
            success=True,
            data=result,
            timestamp=datetime.utcnow(),
            request_id=f"kyc_{request.user_id}_{datetime.utcnow().timestamp()}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint /kyc: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/aml", response_model=ComplianceResponse)
async def analyze_aml(
    request: AMLRequest,
    background_tasks: BackgroundTasks,
    token_data: TokenData = Depends(require_permissions(["compliance:aml"])),
    db: Session = Depends(get_db)
):
    """
    Analizar cumplimiento AML usando verificación de identidad.

    **Parámetros:**
    - **user_id**: ID del usuario
    - **transaction_data**: Datos de la transacción
    - **check_history**: Verificar historial (opcional)

    **Requiere permisos:** compliance:aml

    **Retorna:** Resultado de análisis AML con confianza
    """
    try:
        result = await compliance_api.analyze_aml(request)

        return ComplianceResponse(
            success=True,
            data=result,
            timestamp=datetime.utcnow(),
            request_id=f"aml_{request.user_id}_{datetime.utcnow().timestamp()}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint /aml: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/sybil-check", response_model=ComplianceResponse)
async def check_sybil_attack(
    request: SybilCheckRequest,
    background_tasks: BackgroundTasks,
    token_data: TokenData = Depends(require_permissions(["compliance:sybil"])),
    db: Session = Depends(get_db)
):
    """
    Detectar ataques Sybil usando análisis de patrones y proof-of-humanity.

    **Parámetros:**
    - **user_data**: Datos del usuario para análisis

    **Requiere permisos:** compliance:sybil

    **Retorna:** Análisis de riesgo Sybil con recomendaciones
    """
    try:
        result = await compliance_api.check_sybil_attack(request)

        return ComplianceResponse(
            success=True,
            data=result,
            timestamp=datetime.utcnow(),
            request_id=f"sybil_{request.user_data.get('user_id')}_{datetime.utcnow().timestamp()}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint /sybil-check: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/zk-logs", response_model=ComplianceResponse)
async def query_zk_logs(
    request: ZKLogsRequest,
    background_tasks: BackgroundTasks,
    token_data: TokenData = Depends(require_permissions(["compliance:logs"])),
    db: Session = Depends(get_db)
):
    """
    Consultar logs de auditoría con pruebas ZK de cumplimiento.

    **Parámetros:**
    - **user_id**: Filtrar por usuario (opcional)
    - **action_type**: Filtrar por tipo de acción (opcional)
    - **date_from/date_to**: Rango de fechas (opcional)
    - **verified_only**: Solo logs verificados (opcional)
    - **limit**: Límite de resultados (1-1000)

    **Requiere permisos:** compliance:logs

    **Retorna:** Logs de auditoría con proofs ZK
    """
    try:
        result = await compliance_api.query_zk_logs(request)

        return ComplianceResponse(
            success=True,
            data=result,
            timestamp=datetime.utcnow(),
            request_id=f"zk_logs_{datetime.utcnow().timestamp()}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en endpoint /zk-logs: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/health")
async def health_check():
    """
    Verificar estado de salud de la API de compliance.

    **Retorna:** Estado de componentes
    """
    try:
        compliance_api.initialize_components()

        return {
            "status": "healthy",
            "components": {
                "oracle_auditor": compliance_api.oracle_auditor is not None,
                "zk_audit_logger": compliance_api.zk_logger is not None,
                "sybil_protector": compliance_api.sybil_protector is not None,
                "compliance_manager_fase8": compliance_api.compliance_manager is not None
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error en health check: {e}")
        raise HTTPException(status_code=503, detail="Servicio no disponible")


# === ENDPOINTS PARA ComplianceManager FASE 8 ===

@router.post("/gdpr/consent", response_model=ComplianceResponse)
async def grant_gdpr_consent(
    request: ConsentRequest,
    token_data: TokenData = Depends(require_permissions(["compliance:gdpr"])),
    db: Session = Depends(get_db)
):
    """
    Otorgar consentimiento GDPR.

    **Requiere permisos:** compliance:gdpr
    """
    try:
        if not compliance_api.compliance_manager:
            compliance_api.initialize_components()

        consent_id = compliance_api.compliance_manager.grant_gdpr_consent(
            user_id=request.user_id,
            purpose=request.purpose,
            ip_address=request.ip_address,
            user_agent=request.user_agent
        )

        return ComplianceResponse(
            success=True,
            data={"consent_id": consent_id},
            timestamp=datetime.utcnow(),
            request_id=f"gdpr_consent_{request.user_id}_{datetime.utcnow().timestamp()}"
        )

    except Exception as e:
        logger.error(f"Error en GDPR consent: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.delete("/gdpr/consent", response_model=ComplianceResponse)
async def withdraw_gdpr_consent(
    user_id: str,
    purpose: str,
    token_data: TokenData = Depends(require_permissions(["compliance:gdpr"])),
    db: Session = Depends(get_db)
):
    """
    Retirar consentimiento GDPR.

    **Parámetros URL:**
    - **user_id**: ID del usuario
    - **purpose**: Propósito del consentimiento

    **Requiere permisos:** compliance:gdpr
    """
    try:
        if not compliance_api.compliance_manager:
            compliance_api.initialize_components()

        withdrawn = compliance_api.compliance_manager.withdraw_gdpr_consent(user_id, purpose)

        return ComplianceResponse(
            success=True,
            data={"withdrawn": withdrawn},
            timestamp=datetime.utcnow(),
            request_id=f"gdpr_withdraw_{user_id}_{datetime.utcnow().timestamp()}"
        )

    except Exception as e:
        logger.error(f"Error withdrawing GDPR consent: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/gdpr/export", response_model=ComplianceResponse)
async def export_user_data(
    request: DataExportRequest,
    token_data: TokenData = Depends(require_permissions(["compliance:gdpr"])),
    db: Session = Depends(get_db)
):
    """
    Exportar datos del usuario (GDPR).

    **Requiere permisos:** compliance:gdpr
    """
    try:
        if not compliance_api.compliance_manager:
            compliance_api.initialize_components()

        export_data = compliance_api.compliance_manager.export_user_data(
            user_id=request.user_id,
            format=request.format
        )

        return ComplianceResponse(
            success=True,
            data=export_data,
            timestamp=datetime.utcnow(),
            request_id=f"gdpr_export_{request.user_id}_{datetime.utcnow().timestamp()}"
        )

    except Exception as e:
        logger.error(f"Error exporting user data: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/gdpr/forgotten", response_model=ComplianceResponse)
async def right_to_be_forgotten(
    request: RightToBeForgottenRequest,
    token_data: TokenData = Depends(require_permissions(["compliance:gdpr"])),
    db: Session = Depends(get_db)
):
    """
    Aplicar derecho al olvido (GDPR).

    **Requiere permisos:** compliance:gdpr
    """
    try:
        if not compliance_api.compliance_manager:
            compliance_api.initialize_components()

        result = compliance_api.compliance_manager.right_to_be_forgotten(request.user_id)

        return ComplianceResponse(
            success=True,
            data=result,
            timestamp=datetime.utcnow(),
            request_id=f"gdpr_forgotten_{request.user_id}_{datetime.utcnow().timestamp()}"
        )

    except Exception as e:
        logger.error(f"Error applying right to be forgotten: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/hipaa/phi-access", response_model=ComplianceResponse)
async def request_phi_access(
    request: PHIRequest,
    token_data: TokenData = Depends(require_permissions(["compliance:hipaa"])),
    db: Session = Depends(get_db)
):
    """
    Solicitar acceso a PHI (HIPAA).

    **Requiere permisos:** compliance:hipaa
    """
    try:
        if not compliance_api.compliance_manager:
            compliance_api.initialize_components()

        result, message = compliance_api.compliance_manager.request_phi_access(
            patient_id=request.patient_id,
            accessor_id=request.accessor_id,
            accessor_role=request.accessor_role,
            purpose=request.purpose,
            data_requested=request.data_requested
        )

        return ComplianceResponse(
            success=True,
            data={"result": result, "message": message},
            timestamp=datetime.utcnow(),
            request_id=f"hipaa_phi_{request.patient_id}_{datetime.utcnow().timestamp()}"
        )

    except Exception as e:
        logger.error(f"Error requesting PHI access: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/hipaa/breach", response_model=ComplianceResponse)
async def report_breach(
    request: BreachReportRequest,
    token_data: TokenData = Depends(require_permissions(["compliance:hipaa"])),
    db: Session = Depends(get_db)
):
    """
    Reportar brecha de seguridad (HIPAA).

    **Requiere permisos:** compliance:hipaa
    """
    try:
        if not compliance_api.compliance_manager:
            compliance_api.initialize_components()

        breach_id = compliance_api.compliance_manager.report_breach(
            patient_ids_affected=request.patient_ids_affected,
            data_breached=request.data_breached,
            breach_date=request.breach_date,
            risk_assessment=request.risk_assessment
        )

        return ComplianceResponse(
            success=True,
            data={"breach_id": breach_id},
            timestamp=datetime.utcnow(),
            request_id=f"hipaa_breach_{datetime.utcnow().timestamp()}"
        )

    except Exception as e:
        logger.error(f"Error reporting breach: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/sox/transaction", response_model=ComplianceResponse)
async def record_financial_transaction(
    request: FinancialTransactionRequest,
    token_data: TokenData = Depends(require_permissions(["compliance:sox"])),
    db: Session = Depends(get_db)
):
    """
    Registrar transacción financiera (SOX).

    **Requiere permisos:** compliance:sox
    """
    try:
        if not compliance_api.compliance_manager:
            compliance_api.initialize_components()

        tx_id = compliance_api.compliance_manager.record_financial_transaction(
            transaction_type=request.transaction_type,
            amount=request.amount,
            currency=request.currency,
            initiator=request.initiator,
            description=request.description
        )

        return ComplianceResponse(
            success=True,
            data={"transaction_id": tx_id},
            timestamp=datetime.utcnow(),
            request_id=f"sox_tx_{datetime.utcnow().timestamp()}"
        )

    except Exception as e:
        logger.error(f"Error recording financial transaction: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/sox/approve", response_model=ComplianceResponse)
async def approve_transaction(
    request: TransactionApprovalRequest,
    token_data: TokenData = Depends(require_permissions(["compliance:sox"])),
    db: Session = Depends(get_db)
):
    """
    Aprobar transacción financiera (SOX).

    **Requiere permisos:** compliance:sox
    """
    try:
        if not compliance_api.compliance_manager:
            compliance_api.initialize_components()

        approved = compliance_api.compliance_manager.approve_transaction(
            transaction_id=request.transaction_id,
            approver=request.approver
        )

        return ComplianceResponse(
            success=True,
            data={"approved": approved},
            timestamp=datetime.utcnow(),
            request_id=f"sox_approve_{request.transaction_id}_{datetime.utcnow().timestamp()}"
        )

    except Exception as e:
        logger.error(f"Error approving transaction: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/data-rights/request", response_model=ComplianceResponse)
async def submit_data_right_request(
    request: DataSubjectRightRequest,
    token_data: TokenData = Depends(require_permissions(["compliance:data-rights"])),
    db: Session = Depends(get_db)
):
    """
    Enviar solicitud de derecho del interesado.

    **Requiere permisos:** compliance:data-rights
    """
    try:
        if not compliance_api.compliance_manager:
            compliance_api.initialize_components()

        request_id = compliance_api.compliance_manager.submit_data_right_request(
            user_id=request.user_id,
            right=request.right,
            description=request.description
        )

        return ComplianceResponse(
            success=True,
            data={"request_id": request_id},
            timestamp=datetime.utcnow(),
            request_id=f"data_rights_{request.user_id}_{datetime.utcnow().timestamp()}"
        )

    except Exception as e:
        logger.error(f"Error submitting data rights request: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/auditor/audit", response_model=ComplianceResponse)
async def start_compliance_audit(
    request: ComplianceAuditRequest,
    token_data: TokenData = Depends(require_permissions(["compliance:auditor"])),
    db: Session = Depends(get_db)
):
    """
    Iniciar auditoría de compliance.

    **Requiere permisos:** compliance:auditor
    """
    try:
        if not compliance_api.compliance_manager:
            compliance_api.initialize_components()

        audit_id = compliance_api.compliance_manager.start_compliance_audit(
            audit_type=request.audit_type,
            regulations=request.regulations,
            scope=request.scope
        )

        return ComplianceResponse(
            success=True,
            data={"audit_id": audit_id},
            timestamp=datetime.utcnow(),
            request_id=f"audit_start_{datetime.utcnow().timestamp()}"
        )

    except Exception as e:
        logger.error(f"Error starting compliance audit: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/auditor/dashboard", response_model=ComplianceResponse)
async def get_compliance_dashboard(
    token_data: TokenData = Depends(require_permissions(["compliance:auditor"])),
    db: Session = Depends(get_db)
):
    """
    Obtener dashboard de compliance.

    **Requiere permisos:** compliance:auditor
    """
    try:
        if not compliance_api.compliance_manager:
            compliance_api.initialize_components()

        dashboard = compliance_api.compliance_manager.get_compliance_dashboard()

        return ComplianceResponse(
            success=True,
            data=dashboard,
            timestamp=datetime.utcnow(),
            request_id=f"dashboard_{datetime.utcnow().timestamp()}"
        )

    except Exception as e:
        logger.error(f"Error getting compliance dashboard: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/retention/register", response_model=ComplianceResponse)
async def register_data_for_retention(
    request: DataRetentionRequest,
    token_data: TokenData = Depends(require_permissions(["compliance:retention"])),
    db: Session = Depends(get_db)
):
    """
    Registrar datos para gestión de retención.

    **Requiere permisos:** compliance:retention
    """
    try:
        if not compliance_api.compliance_manager:
            compliance_api.initialize_components()

        record_id = compliance_api.compliance_manager.register_data_for_retention(
            user_id=request.user_id,
            data_category=request.data_category,
            regulation=request.regulation
        )

        return ComplianceResponse(
            success=True,
            data={"record_id": record_id},
            timestamp=datetime.utcnow(),
            request_id=f"retention_reg_{datetime.utcnow().timestamp()}"
        )

    except Exception as e:
        logger.error(f"Error registering data for retention: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/retention/delete", response_model=ComplianceResponse)
async def schedule_data_deletion(
    request: DataDeletionRequest,
    token_data: TokenData = Depends(require_permissions(["compliance:retention"])),
    db: Session = Depends(get_db)
):
    """
    Programar eliminación de datos.

    **Requiere permisos:** compliance:retention
    """
    try:
        if not compliance_api.compliance_manager:
            compliance_api.initialize_components()

        scheduled = compliance_api.compliance_manager.schedule_data_deletion(
            record_ids=request.record_ids,
            scheduled_by=request.scheduled_by
        )

        return ComplianceResponse(
            success=True,
            data={"scheduled": scheduled},
            timestamp=datetime.utcnow(),
            request_id=f"retention_del_{datetime.utcnow().timestamp()}"
        )

    except Exception as e:
        logger.error(f"Error scheduling data deletion: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/status", response_model=ComplianceResponse)
async def get_compliance_status(
    token_data: TokenData = Depends(require_permissions(["compliance:status"])),
    db: Session = Depends(get_db)
):
    """
    Obtener estado completo de compliance.

    **Requiere permisos:** compliance:status
    """
    try:
        if not compliance_api.compliance_manager:
            compliance_api.initialize_components()

        status = compliance_api.compliance_manager.get_compliance_status()

        return ComplianceResponse(
            success=True,
            data=status,
            timestamp=datetime.utcnow(),
            request_id=f"status_{datetime.utcnow().timestamp()}"
        )

    except Exception as e:
        logger.error(f"Error getting compliance status: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# Función para crear la aplicación FastAPI completa
def create_compliance_app() -> APIRouter:
    """
    Crear router de compliance con todos los endpoints.

    Returns:
        APIRouter configurado
    """
    return router


# Función de conveniencia para testing
if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI

    app = FastAPI(title="AILOOS Compliance API", version="1.0.0")
    app.include_router(router)

    print("🚀 Iniciando Compliance API en http://localhost:8000")
    print("📚 Documentación OpenAPI en http://localhost:8000/docs")

    uvicorn.run(app, host="0.0.0.0", port=8000)