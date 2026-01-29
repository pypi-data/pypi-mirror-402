"""
Unified API Gateway - FASE 10
=============================

El cerebro expuesto de AILOOS. Esta API conecta todo el ecosistema con el mundo exterior.

Endpoints principales:
- POST /v1/chat/completions: Generación de texto con EmpoorioLM
- POST /v1/vision/analyze: Análisis de imágenes con EmpoorioVision
- POST /v1/workflow/execute: Ejecución de workflows complejos
- GET /v1/health: Estado de salud del sistema

Características:
- Autenticación JWT básica
- Rate limiting (10 req/min por IP)
- Logging estructurado
- Inyección de dependencias para modelos
- Conexión con WorkflowEngine real
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import jwt

from ..core.config import get_config
from ..core.logging import get_logger
from .dependencies import get_model_dependencies, ModelDependencies

# Configuración
config = get_config()
logger = get_logger(__name__)

# Configuración JWT (simplificada para MVP)
SECRET_KEY = config.api.jwt_secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Rate limiting simple (en memoria - para producción usar Redis)
rate_limit_store: Dict[str, List[float]] = {}
RATE_LIMIT_REQUESTS = 10  # 10 requests por minuto
RATE_LIMIT_WINDOW = 60  # 60 segundos

# Modelos Pydantic para requests/responses
class ChatCompletionRequest(BaseModel):
    messages: List[Dict[str, Any]] = Field(..., description="Lista de mensajes")
    model: str = Field("empoorio-lm", description="Modelo a usar")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Temperatura de generación")
    max_tokens: int = Field(1024, ge=1, le=4096, description="Máximo de tokens a generar")

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

class VisionAnalyzeRequest(BaseModel):
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    prompt: str = Field(..., description="Prompt para análisis")

class VisionAnalyzeResponse(BaseModel):
    analysis: str
    confidence: float
    processing_time: float

class WorkflowExecuteRequest(BaseModel):
    template_id: str = Field(..., description="ID del template de workflow")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parámetros del workflow")

class WorkflowExecuteResponse(BaseModel):
    workflow_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    execution_time: float
    steps_executed: int

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    services: Dict[str, str]

# Utilidades de rate limiting
def check_rate_limit(client_ip: str) -> bool:
    """Verifica si el cliente excede el rate limit."""
    now = time.time()
    if client_ip not in rate_limit_store:
        rate_limit_store[client_ip] = []

    # Limpiar requests antiguos
    rate_limit_store[client_ip] = [
        req_time for req_time in rate_limit_store[client_ip]
        if now - req_time < RATE_LIMIT_WINDOW
    ]

    # Verificar límite
    if len(rate_limit_store[client_ip]) >= RATE_LIMIT_REQUESTS:
        return False

    # Añadir nuevo request
    rate_limit_store[client_ip].append(now)
    return True

# Utilidades JWT
def create_access_token(data: dict):
    """Crea un token JWT."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    """Verifica un token JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except jwt.PyJWTError:
        return None

# Dependencias de seguridad
security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene el usuario actual desde JWT."""
    if not credentials:
        # Para MVP, permitir requests sin auth
        return "anonymous"

    token = credentials.credentials
    username = verify_token(token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username

# Middleware de rate limiting
async def rate_limit_middleware(request: Request, call_next):
    """Middleware para rate limiting."""
    client_ip = request.client.host if request.client else "unknown"

    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again later."
        )

    response = await call_next(request)
    return response

# Inicialización de la aplicación
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo del ciclo de vida de la aplicación."""
    # Startup
    logger.info("🚀 Starting AILOOS Unified API Gateway")
    logger.info("📥 Loading model dependencies...")

    try:
        # Cargar dependencias de modelos al inicio
        app.state.model_deps = await get_model_dependencies()
        logger.info("✅ Model dependencies loaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to load model dependencies: {e}")
        app.state.model_deps = None

    yield

    # Shutdown
    logger.info("🛑 Shutting down AILOOS Unified API Gateway")

def create_app() -> FastAPI:
    """Factory function para crear la aplicación FastAPI"""
    app = FastAPI(
        title="AILOOS Unified API Gateway",
        description="El cerebro expuesto de AILOOS - Conectando IA avanzada con el mundo",
        version="1.0.0",
        lifespan=lifespan
    )

    # Middlewares
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://www.ailoos.com", "https://ailoos.com", "http://localhost:3000", "http://localhost:8000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])  # Para desarrollo

    # Rate limiting middleware
    @app.middleware("http")
    async def add_rate_limiting(request: Request, call_next):
        return await rate_limit_middleware(request, call_next)

    # Endpoints principales

    @app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
    async def chat_completions(
        request: ChatCompletionRequest,
        user: str = Depends(get_current_user),
        model_deps: ModelDependencies = Depends(lambda: app.state.model_deps)
    ):
        """Genera texto usando EmpoorioLM."""
        start_time = time.time()

        # Extraer el último mensaje del usuario primero
        user_message = ""
        for msg in reversed(request.messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")

        try:
            # Obtener EmpoorioLM con lazy loading
            empoorio_lm = await model_deps.get_empoorio_lm() if model_deps else None

            if not empoorio_lm:
                allow_mocks = os.getenv("AILOOS_ALLOW_MOCKS", "").lower() in ("1", "true", "yes")
                if not allow_mocks:
                    raise HTTPException(status_code=503, detail="EmpoorioLM not available")
                logger.warning("EmpoorioLM not available, using mock response")
                response_text = f"Mock response: Gracias por tu consulta sobre '{user_message[:50]}...'. Esta es una respuesta simulada mientras el modelo se carga."
            else:
                # Generar respuesta con EmpoorioLM
                response_text = await empoorio_lm.generate_text(
                    prompt=user_message,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature
                )

            execution_time = time.time() - start_time

            return ChatCompletionResponse(
                id=f"chatcmpl-{int(time.time())}",
                created=int(time.time()),
                model=request.model,
                choices=[{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }],
                usage={
                    "prompt_tokens": len(user_message.split()),
                    "completion_tokens": len(response_text.split()),
                    "total_tokens": len(user_message.split()) + len(response_text.split())
                }
            )

        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    @app.post("/v1/vision/analyze", response_model=VisionAnalyzeResponse)
    async def vision_analyze(
        request: VisionAnalyzeRequest,
        user: str = Depends(get_current_user),
        model_deps: ModelDependencies = Depends(lambda: app.state.model_deps)
    ):
        """Analiza imágenes usando EmpoorioVision."""
        start_time = time.time()

        if not model_deps or not model_deps.empoorio_vision:
            raise HTTPException(status_code=503, detail="EmpoorioVision model not available")

        try:
            # Aquí iría la lógica de análisis de imagen
            # Por ahora, mock response
            analysis = f"Análisis simulado de imagen: {request.prompt}"
            confidence = 0.85

            execution_time = time.time() - start_time

            return VisionAnalyzeResponse(
                analysis=analysis,
                confidence=confidence,
                processing_time=execution_time
            )

        except Exception as e:
            logger.error(f"Error in vision analysis: {e}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    @app.post("/v1/workflow/execute", response_model=WorkflowExecuteResponse)
    async def workflow_execute(
        request: WorkflowExecuteRequest,
        user: str = Depends(get_current_user),
        model_deps: ModelDependencies = Depends(lambda: app.state.model_deps)
    ):
        """Ejecuta un workflow complejo usando WorkflowEngine."""
        start_time = time.time()

        try:
            # Obtener WorkflowEngine con lazy loading
            workflow_engine = await model_deps.get_workflow_engine() if model_deps else None

            if not workflow_engine:
                allow_mocks = os.getenv("AILOOS_ALLOW_MOCKS", "").lower() in ("1", "true", "yes")
                if not allow_mocks:
                    raise HTTPException(status_code=503, detail="Workflow engine not available")
                logger.warning("Workflow engine not available, using mock response")
                execution_time = time.time() - start_time
                mock_result = {
                    "analysis": f"Análisis simulado del texto: '{request.parameters.get('input_text', 'Texto de prueba')[:50]}...'",
                    "sentiment": "neutral",
                    "confidence": 0.75
                }
                return WorkflowExecuteResponse(
                    workflow_id=f"mock-wf-{int(time.time())}",
                    status="completed",
                    result=mock_result,
                    execution_time=execution_time,
                    steps_executed=1
                )

            # Crear workflow simple basado en template
            from ..workflows.engine import WorkflowStep

            # Workflow simple de análisis de texto
            steps = [
                WorkflowStep(
                    step_id="analyze_text",
                    step_type="expert",
                    description="Analizar texto con experto",
                    config={
                        "domain": "general",
                        "prompt_template": f"Analiza el siguiente texto: {{text}}",
                        "max_tokens": 200
                    }
                )
            ]

            # Ejecutar workflow
            result = await workflow_engine.execute_workflow(
                workflow_id=f"wf-{int(time.time())}",
                steps=steps,
                input_data={"text": request.parameters.get("input_text", "Texto de prueba")}
            )

            execution_time = time.time() - start_time

            return WorkflowExecuteResponse(
                workflow_id=result.workflow_id,
                status=result.status,
                result=result.final_output,
                execution_time=execution_time,
                steps_executed=len(result.steps) if hasattr(result, 'steps') else 0
            )

        except Exception as e:
            logger.error(f"Error in workflow execution: {e}")
            raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

    @app.get("/v1/health", response_model=HealthResponse)
    async def health_check():
        """Verifica el estado de salud del sistema."""
        services_status = {}

        # Verificar servicios básicos
        try:
            if hasattr(app.state, 'model_deps') and app.state.model_deps:
                services_status["model_dependencies"] = "healthy"
                # Nota: Con lazy loading, los modelos aparecen como None hasta que se usan
                # Esto es normal y esperado
                services_status["empoorio_lm"] = "lazy_loaded"
                services_status["empoorio_vision"] = "lazy_loaded"
                services_status["workflow_engine"] = "lazy_loaded"
            else:
                services_status["model_dependencies"] = "unavailable"
        except:
            services_status["model_dependencies"] = "error"

        # Determinar estado general
        overall_status = "healthy"
        if any(status == "unavailable" for status in services_status.values()):
            overall_status = "degraded"
        if any(status == "error" for status in services_status.values()):
            overall_status = "unhealthy"

        return HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow().isoformat(),
            version="1.0.0",
            services=services_status
        )

    @app.post("/v1/auth/login")
    async def login():
        """Endpoint simple de login (para desarrollo)."""
        # En producción, esto validaría credenciales reales
        access_token = create_access_token(data={"sub": "test_user"})
        return {"access_token": access_token, "token_type": "bearer"}

    # Logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Middleware para logging de requests."""
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time

        logger.info(
            "Request",
            extra={
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "process_time": f"{process_time:.3f}s",
                "client_ip": request.client.host if request.client else "unknown"
            }
        )

        return response

    return app

# Instancia global para servidores ASGI (uvicorn)
app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "src.ailoos.api.gateway:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
