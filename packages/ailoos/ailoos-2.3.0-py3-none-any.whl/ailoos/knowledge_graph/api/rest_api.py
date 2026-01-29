"""
REST API para el Grafo de Conocimiento AILOOS.
Proporciona endpoints REST con autenticación, validación y documentación automática.
"""

import asyncio
import os
import time
import uuid
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Query, Body, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from enum import Enum
import jwt

from ...core.logging import get_logger
from ...core.config import get_config
from ..core import get_knowledge_graph_core, Triple, BackendType, FormatType
from ..query.query_executor import get_query_executor
from ..inference import get_inference_engine, InferenceType
from ...auditing.audit_manager import get_audit_manager, AuditEventType
from ...auditing.metrics_collector import get_metrics_collector
try:
    import redis  # type: ignore
except ImportError:
    redis = None

logger = get_logger(__name__)


# Modelos Pydantic para validación
class TripleModel(BaseModel):
    """Modelo para triple RDF."""
    subject: str = Field(..., min_length=1, max_length=1000, description="Sujeto del triple")
    predicate: str = Field(..., min_length=1, max_length=1000, description="Predicado del triple")
    object: Union[str, int, float, bool] = Field(..., description="Objeto del triple")

    @validator('subject', 'predicate')
    def validate_non_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('No puede estar vacío')
        return v.strip()

    @validator('object')
    def validate_object(cls, v):
        if v is None:
            raise ValueError('No puede ser None')
        return v


class QueryRequest(BaseModel):
    """Modelo para solicitud de consulta."""
    query: str = Field(..., min_length=1, description="Consulta a ejecutar")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Parámetros de la consulta")
    optimize: bool = Field(True, description="Si optimizar la consulta")
    use_cache: bool = Field(True, description="Si usar cache")


class InferenceRequest(BaseModel):
    """Modelo para solicitud de inferencia."""
    inference_type: InferenceType = Field(InferenceType.FORWARD_CHAINING, description="Tipo de inferencia")
    rules_to_apply: Optional[List[str]] = Field(None, description="Reglas específicas a aplicar")
    max_depth: Optional[int] = Field(10, ge=1, le=50, description="Profundidad máxima")


class BulkTripleRequest(BaseModel):
    """Modelo para operaciones bulk de triples."""
    triples: List[TripleModel] = Field(..., min_items=1, max_items=1000, description="Lista de triples")


class LoadFormatRequest(BaseModel):
    """Modelo para cargar datos desde formato."""
    data: str = Field(..., min_length=1, description="Datos en el formato especificado")
    format_type: FormatType = Field(..., description="Tipo de formato")


class AuthToken(BaseModel):
    """Modelo para token de autenticación."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str


class UserCredentials(BaseModel):
    """Modelo para credenciales de usuario."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


# Enums para respuestas
class APIResponseStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"


class APIResponse(BaseModel):
    """Modelo base para respuestas API."""
    status: APIResponseStatus
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None


# Middleware de autenticación
class AuthMiddleware:
    """Middleware para autenticación JWT."""

    ISSUER = "ailoos-kg"
    AUDIENCE = "ailoos-clients"

    def __init__(self, secret_key: str = None):
        if secret_key:
            self.secret_key = secret_key
        else:
            config = get_config()
            # En desarrollo permitimos una clave fija (DEV_JWT_SECRET) o efímera para no bloquear el arranque
            dev_secret = os.getenv("DEV_JWT_SECRET")
            if config.environment == "development" and not config.api.jwt_secret and dev_secret:
                self.secret_key = dev_secret
                logger.warning("⚠️ Using DEV_JWT_SECRET for development auth")
            elif config.environment == "development" and not config.api.jwt_secret:
                self.secret_key = secrets.token_hex(32)
                logger.warning("⚠️ No JWT secret configured in development; using ephemeral secret for this run")
            else:
                if not config.api.jwt_secret:
                    raise ValueError("JWT secret not configured")
                self.secret_key = config.api.jwt_secret
        self.security = HTTPBearer(auto_error=False)
        self.revocation_client = None
        if redis:
            try:
                redis_url = f"redis://{config.redis.host}:{config.redis.port}/{config.redis.db}"
                if config.redis.password:
                    redis_url = f"redis://:{config.redis.password}@{config.redis.host}:{config.redis.port}/{config.redis.db}"
                self.revocation_client = redis.Redis.from_url(redis_url, decode_responses=True)
            except Exception as exc:
                logger.warning(f"⚠️ Could not initialize Redis revocation backend: {exc}")
        self.revoked_jtis: Dict[str, int] = {}

    def create_token(self, user_id: str, expires_in: int = 3600) -> str:
        """Crear token JWT."""
        payload = {
            "user_id": user_id,
            "iss": self.ISSUER,
            "aud": self.AUDIENCE,
            "jti": str(uuid.uuid4()),
            "exp": int(time.time()) + expires_in,
            "iat": int(time.time())
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def verify_token(self, token: str) -> Optional[str]:
        """Verificar token JWT."""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=["HS256"],
                audience=self.AUDIENCE,
                options={"require": ["iss", "aud", "exp", "iat", "jti"]},
            )
            if payload.get("iss") != self.ISSUER:
                return None
            if self._is_revoked(payload.get("jti")):
                return None
            return payload.get("user_id")
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def revoke_token(self, jti: str, exp: int):
        """Revocar token guardando jti hasta su expiración."""
        ttl = max(exp - int(time.time()), 0)
        if self.revocation_client and ttl > 0:
            try:
                self.revocation_client.setex(f"kg:revoked:{jti}", ttl, "1")
                return
            except Exception as exc:
                logger.warning(f"⚠️ Could not persist revoked jti to Redis: {exc}")
        self.revoked_jtis[jti] = exp

    def _is_revoked(self, jti: str) -> bool:
        """Comprobar si un jti está revocado."""
        now = time.time()
        if self.revocation_client:
            try:
                return bool(self.revocation_client.exists(f"kg:revoked:{jti}"))
            except Exception as exc:
                logger.warning(f"⚠️ Could not check revocation backend: {exc}")
        expired = [k for k, v in self.revoked_jtis.items() if v < now]
        for key in expired:
            self.revoked_jtis.pop(key, None)
        return jti in self.revoked_jtis

    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))) -> Optional[str]:
        """Obtener usuario actual desde token."""
        if not credentials:
            return None

        return self.verify_token(credentials.credentials)


# API REST principal
class KnowledgeGraphRESTAPI:
    """
    API REST completa para el grafo de conocimiento.
    Incluye autenticación, validación, documentación y monitoreo.
    """

    def __init__(self, app: Optional[FastAPI] = None):
        self.app = app or FastAPI(
            title="AILOOS Knowledge Graph API",
            description="API REST para operaciones del grafo de conocimiento",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )

        # Componentes del sistema
        self.kg_core = get_knowledge_graph_core()
        self.query_executor = get_query_executor()
        self.inference_engine = get_inference_engine()
        self.audit_manager = get_audit_manager()
        self.metrics_collector = get_metrics_collector()

        # Autenticación
        self.auth = AuthMiddleware()

        # Configurar CORS
        self._setup_cors()

        # Configurar rutas
        self._setup_routes()

        # Configurar middleware
        self._setup_middleware()

    def _setup_cors(self):
        """Configurar CORS."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # En producción, especificar orígenes
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_middleware(self):
        """Configurar middleware personalizado."""

        @self.app.middleware("http")
        async def audit_middleware(request: Request, call_next):
            """Middleware para auditoría de requests."""
            start_time = time.time()
            user_id = None

            # Intentar extraer user_id del token
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                user_id = self.auth.verify_token(token)

            # Extraer IP y User-Agent
            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")

            try:
                response = await call_next(request)
                processing_time = (time.time() - start_time) * 1000

                # Log de auditoría
                await self.audit_manager.log_event(
                    event_type=AuditEventType.DATA_ACCESS,
                    resource="knowledge_graph_api",
                    action=f"{request.method} {request.url.path}",
                    user_id=user_id,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    details={
                        "method": request.method,
                        "path": request.url.path,
                        "query_params": dict(request.query_params),
                        "status_code": response.status_code
                    },
                    success=response.status_code < 400,
                    processing_time_ms=processing_time
                )

                # Métricas
                self.metrics_collector.record_request(f"api.{request.method.lower()}.{request.url.path}")
                self.metrics_collector.record_response_time(processing_time)

                return response

            except Exception as e:
                processing_time = (time.time() - start_time) * 1000

                # Log de error
                await self.audit_manager.log_event(
                    event_type=AuditEventType.DATA_ACCESS,
                    resource="knowledge_graph_api",
                    action=f"{request.method} {request.url.path}",
                    user_id=user_id,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    details={
                        "method": request.method,
                        "path": request.url.path,
                        "error": str(e)
                    },
                    success=False,
                    processing_time_ms=processing_time
                )

                self.metrics_collector.record_error(f"api.{request.method.lower()}.{request.url.path}", "request_error")
                raise

    def _setup_routes(self):
        """Configurar todas las rutas de la API."""

        # Autenticación
        @self.app.post("/auth/login", response_model=APIResponse)
        async def login(credentials: UserCredentials):
            """Autenticar usuario y obtener token."""
            # En implementación real, verificar credenciales contra base de datos
            # Por ahora, simular autenticación
            if credentials.username and credentials.password:
                token = self.auth.create_token(credentials.username)
                return APIResponse(
                    status=APIResponseStatus.SUCCESS,
                    message="Login exitoso",
                    data=AuthToken(
                        access_token=token,
                        user_id=credentials.username,
                        expires_in=3600
                    )
                )
            else:
                raise HTTPException(status_code=401, detail="Credenciales inválidas")

        # CRUD de triples
        @self.app.post("/triples", response_model=APIResponse)
        async def create_triple(
            triple: TripleModel,
            user_id: Optional[str] = Depends(self.auth.get_current_user)
        ):
            """Crear un nuevo triple."""
            if not user_id:
                raise HTTPException(status_code=401, detail="Autenticación requerida")

            try:
                kg_triple = Triple(triple.subject, triple.predicate, triple.object)
                success = await self.kg_core.add_triple(kg_triple, user_id)

                if success:
                    return APIResponse(
                        status=APIResponseStatus.SUCCESS,
                        message="Triple creado exitosamente",
                        data=triple.dict()
                    )
                else:
                    raise HTTPException(status_code=500, detail="Error al crear triple")

            except Exception as e:
                logger.error(f"Error creating triple: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/triples", response_model=APIResponse)
        async def get_triples(
            subject: Optional[str] = Query(None),
            predicate: Optional[str] = Query(None),
            object: Optional[Union[str, int, float, bool]] = Query(None),
            limit: int = Query(100, ge=1, le=1000),
            user_id: Optional[str] = Depends(self.auth.get_current_user)
        ):
            """Obtener triples con filtros opcionales."""
            try:
                # Construir query SPARQL simple
                query_parts = []
                if subject:
                    query_parts.append(f"?s = <{subject}>")
                if predicate:
                    query_parts.append(f"?p = <{predicate}>")
                if object is not None:
                    if isinstance(object, str):
                        query_parts.append(f"?o = '{object}'")
                    else:
                        query_parts.append(f"?o = {object}")

                where_clause = " . ".join(query_parts) if query_parts else "true"
                sparql_query = f"SELECT ?s ?p ?o WHERE {{ {where_clause} }} LIMIT {limit}"

                results = await self.kg_core.query(sparql_query, user_id)

                return APIResponse(
                    status=APIResponseStatus.SUCCESS,
                    message=f"Obtenidos {len(results)} triples",
                    data=[r.to_dict() for r in results]
                )

            except Exception as e:
                logger.error(f"Error getting triples: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.delete("/triples", response_model=APIResponse)
        async def delete_triple(
            triple: TripleModel,
            user_id: Optional[str] = Depends(self.auth.get_current_user)
        ):
            """Eliminar un triple."""
            if not user_id:
                raise HTTPException(status_code=401, detail="Autenticación requerida")

            try:
                kg_triple = Triple(triple.subject, triple.predicate, triple.object)
                success = await self.kg_core.remove_triple(kg_triple, user_id)

                if success:
                    return APIResponse(
                        status=APIResponseStatus.SUCCESS,
                        message="Triple eliminado exitosamente",
                        data=triple.dict()
                    )
                else:
                    raise HTTPException(status_code=404, detail="Triple no encontrado")

            except Exception as e:
                logger.error(f"Error deleting triple: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post("/triples/bulk", response_model=APIResponse)
        async def bulk_create_triples(
            request: BulkTripleRequest,
            user_id: Optional[str] = Depends(self.auth.get_current_user)
        ):
            """Crear múltiples triples en bulk."""
            if not user_id:
                raise HTTPException(status_code=401, detail="Autenticación requerida")

            try:
                kg_triples = [Triple(t.subject, t.predicate, t.object) for t in request.triples]
                success_count = 0

                for kg_triple in kg_triples:
                    if await self.kg_core.add_triple(kg_triple, user_id):
                        success_count += 1

                return APIResponse(
                    status=APIResponseStatus.SUCCESS,
                    message=f"Creados {success_count}/{len(kg_triples)} triples",
                    data={
                        "total_requested": len(kg_triples),
                        "success_count": success_count,
                        "failed_count": len(kg_triples) - success_count
                    }
                )

            except Exception as e:
                logger.error(f"Error in bulk create: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        # Consultas
        @self.app.post("/query", response_model=APIResponse)
        async def execute_query(
            request: QueryRequest,
            user_id: Optional[str] = Depends(self.auth.get_current_user)
        ):
            """Ejecutar consulta en el grafo."""
            try:
                result = await self.query_executor.execute_query(
                    request.query,
                    parameters=request.parameters,
                    user_id=user_id,
                    optimize=request.optimize,
                    use_cache=request.use_cache
                )

                return APIResponse(
                    status=APIResponseStatus.SUCCESS,
                    message="Consulta ejecutada exitosamente",
                    data={
                        "query": result.query,
                        "results": [r.to_dict() for r in result.results],
                        "execution_time_ms": result.execution_time_ms,
                        "result_count": len(result.results),
                        "error": result.error
                    }
                )

            except Exception as e:
                logger.error(f"Error executing query: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post("/query/batch", response_model=APIResponse)
        async def execute_batch_queries(
            queries: List[QueryRequest],
            user_id: Optional[str] = Depends(self.auth.get_current_user)
        ):
            """Ejecutar múltiples consultas en batch."""
            try:
                query_data = [
                    {
                        "query": q.query,
                        "parameters": q.parameters,
                        "optimize": q.optimize,
                        "use_cache": q.use_cache
                    }
                    for q in queries
                ]

                results = await self.query_executor.execute_batch(query_data, user_id)

                return APIResponse(
                    status=APIResponseStatus.SUCCESS,
                    message=f"Ejecutadas {len(results)} consultas",
                    data=[
                        {
                            "query": r.query,
                            "results": [res.to_dict() for res in r.results],
                            "execution_time_ms": r.execution_time_ms,
                            "result_count": len(r.results),
                            "error": r.error
                        }
                        for r in results
                    ]
                )

            except Exception as e:
                logger.error(f"Error in batch query: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        # Inferencias
        @self.app.post("/inference", response_model=APIResponse)
        async def run_inference(
            request: InferenceRequest,
            user_id: Optional[str] = Depends(self.auth.get_current_user)
        ):
            """Ejecutar inferencia automática."""
            if not user_id:
                raise HTTPException(status_code=401, detail="Autenticación requerida")

            try:
                result = await self.inference_engine.infer(
                    inference_type=request.inference_type,
                    rules_to_apply=request.rules_to_apply,
                    max_depth=request.max_depth,
                    user_id=user_id
                )

                return APIResponse(
                    status=APIResponseStatus.SUCCESS,
                    message="Inferencia ejecutada exitosamente",
                    data=result.to_dict()
                )

            except Exception as e:
                logger.error(f"Error running inference: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/inference/rules", response_model=APIResponse)
        async def add_inference_rule(
            rule_id: str = Body(..., min_length=1),
            name: str = Body(..., min_length=1),
            description: str = Body(..., min_length=1),
            sparql_query: str = Body(..., min_length=1),
            priority: int = Body(0, ge=0),
            user_id: Optional[str] = Depends(self.auth.get_current_user)
        ):
            """Agregar regla de inferencia personalizada."""
            if not user_id:
                raise HTTPException(status_code=401, detail="Autenticación requerida")

            try:
                success = await self.inference_engine.add_custom_rule(
                    rule_id=rule_id,
                    name=name,
                    description=description,
                    sparql_query=sparql_query,
                    priority=priority,
                    user_id=user_id
                )

                if success:
                    return APIResponse(
                        status=APIResponseStatus.SUCCESS,
                        message="Regla de inferencia agregada exitosamente",
                        data={"rule_id": rule_id}
                    )
                else:
                    raise HTTPException(status_code=400, detail="Error al agregar regla")

            except Exception as e:
                logger.error(f"Error adding inference rule: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/inference/rules", response_model=APIResponse)
        async def get_inference_rules():
            """Obtener todas las reglas de inferencia."""
            try:
                rules = self.inference_engine.get_inference_rules()
                return APIResponse(
                    status=APIResponseStatus.SUCCESS,
                    message=f"Obtenidas {len(rules)} reglas de inferencia",
                    data=rules
                )

            except Exception as e:
                logger.error(f"Error getting inference rules: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Importación/Exportación
        @self.app.post("/import", response_model=APIResponse)
        async def import_data(
            request: LoadFormatRequest,
            user_id: Optional[str] = Depends(self.auth.get_current_user)
        ):
            """Importar datos desde formato específico."""
            if not user_id:
                raise HTTPException(status_code=401, detail="Autenticación requerida")

            try:
                success = await self.kg_core.load_from_format(
                    request.data,
                    request.format_type,
                    user_id
                )

                if success:
                    return APIResponse(
                        status=APIResponseStatus.SUCCESS,
                        message=f"Datos importados exitosamente desde {request.format_type.value}",
                        data={"format": request.format_type.value}
                    )
                else:
                    raise HTTPException(status_code=400, detail="Error al importar datos")

            except Exception as e:
                logger.error(f"Error importing data: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/export", response_model=APIResponse)
        async def export_data(
            format_type: FormatType = Query(...),
            user_id: Optional[str] = Depends(self.auth.get_current_user)
        ):
            """Exportar grafo a formato específico."""
            try:
                data = await self.kg_core.export_to_format(format_type)

                if data:
                    return APIResponse(
                        status=APIResponseStatus.SUCCESS,
                        message=f"Grafo exportado exitosamente a {format_type.value}",
                        data={
                            "format": format_type.value,
                            "data": data
                        }
                    )
                else:
                    raise HTTPException(status_code=500, detail="Error al exportar datos")

            except Exception as e:
                logger.error(f"Error exporting data: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Estadísticas y monitoreo
        @self.app.get("/stats", response_model=APIResponse)
        async def get_graph_stats():
            """Obtener estadísticas del grafo."""
            try:
                stats = await self.kg_core.get_stats()
                return APIResponse(
                    status=APIResponseStatus.SUCCESS,
                    message="Estadísticas obtenidas exitosamente",
                    data=stats
                )

            except Exception as e:
                logger.error(f"Error getting stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/health", response_model=APIResponse)
        async def health_check():
            """Verificación de salud del servicio."""
            try:
                # Verificar componentes críticos
                health_data = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "components": {
                        "knowledge_graph_core": "healthy",
                        "query_executor": "healthy",
                        "inference_engine": "healthy",
                        "audit_manager": "healthy",
                        "metrics_collector": "healthy"
                    }
                }

                # Verificar estadísticas básicas
                stats = await self.kg_core.get_stats()
                if "error" in stats:
                    health_data["components"]["knowledge_graph_core"] = "unhealthy"
                    health_data["status"] = "degraded"

                return APIResponse(
                    status=APIResponseStatus.SUCCESS,
                    message="Health check completado",
                    data=health_data
                )

            except Exception as e:
                logger.error(f"Health check failed: {e}")
                raise HTTPException(status_code=503, detail="Servicio no disponible")

        @self.app.delete("/graph", response_model=APIResponse)
        async def clear_graph(
            user_id: Optional[str] = Depends(self.auth.get_current_user)
        ):
            """Limpiar todo el grafo (operación destructiva)."""
            if not user_id:
                raise HTTPException(status_code=401, detail="Autenticación requerida")

            try:
                success = await self.kg_core.clear(user_id)

                if success:
                    return APIResponse(
                        status=APIResponseStatus.SUCCESS,
                        message="Grafo limpiado exitosamente",
                        data={"cleared": True}
                    )
                else:
                    raise HTTPException(status_code=500, detail="Error al limpiar grafo")

            except Exception as e:
                logger.error(f"Error clearing graph: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    def get_app(self) -> FastAPI:
        """Obtener la aplicación FastAPI."""
        return self.app

    async def start_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Iniciar servidor."""
        import uvicorn
        logger.info(f"Starting Knowledge Graph API server on {host}:{port}")
        config = uvicorn.Config(self.app, host=host, port=port)
        server = uvicorn.Server(config)
        await server.serve()

    def create_app(self) -> FastAPI:
        """Crear y configurar aplicación FastAPI."""
        return self.app
