"""
RAG API - API REST para el sistema RAG de AILOOS.
Proporciona endpoints para consultas RAG con diferentes técnicas.
"""

import asyncio
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ..core.config import get_config
from ..core.logging import get_logger
from ..rag import create_naive_rag, CorrectiveRAG, SpeculativeRAG, SelfRAG
from ..rag.techniques.naive_rag import NaiveRAG
from ..rag.cache_augmented.cache_augmented_rag import CacheAugmentedRAG

logger = get_logger(__name__)


# Modelos Pydantic
class RAGQueryRequest(BaseModel):
    """Request model for RAG query."""
    query: str = Field(..., description="The search query for RAG processing")
    rag_type: str = Field("NaiveRAG", description="Type of RAG system to use: NaiveRAG, CorrectiveRAG, SpeculativeRAG, SelfRAG, CacheAugmentedRAG")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Additional query parameters")


class RAGQueryResponse(BaseModel):
    """Response model for RAG query."""
    query: str
    response: str
    context: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    metadata: Dict[str, Any]


class RAGHealthResponse(BaseModel):
    """Response model for RAG health check."""
    status: str
    rag_systems_available: List[str]
    timestamp: str


class RAGAPI:
    """
    API REST completa para el sistema RAG de AILOOS.
    Maneja consultas RAG con diferentes técnicas y configuraciones.
    """

    def __init__(self):
        self.app = FastAPI(
            title="AILOOS RAG API",
            description="API para consultas RAG con diferentes técnicas",
            version="1.0.0"
        )

        # Componentes del sistema RAG
        self.rag_systems: Dict[str, Any] = {}
        self._initialize_rag_systems()

        logger.info("🚀 RAG API initialized")

        # Configurar rutas
        self._setup_routes()

    def _initialize_rag_systems(self):
        """Inicializar sistemas RAG disponibles."""
        try:
            allow_mocks = os.getenv("AILOOS_ALLOW_MOCKS", "").lower() in ("1", "true", "yes")
            # Crear sistema Naive RAG básico con generador mock para demo
            rag_system = create_naive_rag(
                chunk_size=500,
                chunk_overlap=50,
                use_mock_generator=allow_mocks
            )

            # Agregar documentos de muestra para testing
            sample_documents = [
                {
                    "content": """
                    La Inteligencia Artificial (IA) es una rama de la informática que se ocupa de crear
                    máquinas capaces de realizar tareas que requieren inteligencia humana. Estas tareas
                    incluyen el aprendizaje, el razonamiento, la resolución de problemas, la percepción,
                    el entendimiento del lenguaje natural y la toma de decisiones.

                    La IA se divide en dos tipos principales: IA débil (o estrecha) e IA fuerte (o general).
                    La IA débil está diseñada para realizar tareas específicas, como el reconocimiento
                    de imágenes o el procesamiento del lenguaje natural. La IA fuerte, por otro lado,
                    tendría la capacidad de realizar cualquier tarea intelectual que un humano pueda hacer.
                    """,
                    "metadata": {
                        "title": "Introducción a la Inteligencia Artificial",
                        "author": "Dr. Ana García",
                        "topic": "IA",
                        "source": "manual"
                    }
                },
                {
                    "content": """
                    El aprendizaje automático (Machine Learning) es un subcampo de la IA que permite
                    a los sistemas aprender y mejorar automáticamente a partir de la experiencia,
                    sin ser programados explícitamente para cada tarea específica.

                    Los algoritmos de ML se entrenan con grandes cantidades de datos para identificar
                    patrones y hacer predicciones. Los tipos principales de aprendizaje automático son:
                    supervisado, no supervisado y por refuerzo.
                    """,
                    "metadata": {
                        "title": "Aprendizaje Automático",
                        "author": "Dr. Carlos López",
                        "topic": "Machine Learning",
                        "source": "manual"
                    }
                }
            ]

            # Indexar documentos
            rag_system.retriever.add_documents(sample_documents)
            logger.info(f"✅ Indexed {len(sample_documents)} sample documents")

            self.rag_systems["NaiveRAG"] = rag_system
            logger.info("✅ NaiveRAG system initialized with sample data")

            # Initialize CorrectiveRAG
            try:
                corrective_rag = CorrectiveRAG({
                    'retriever_config': {'chunk_size': 500, 'chunk_overlap': 50},
                    'generator_config': {'use_mock': allow_mocks},
                    'evaluator_config': {},
                    'correction_config': {
                        'max_iterations': 3,
                        'confidence_threshold': 0.7,
                        'relevance_threshold': 0.5,
                        'factuality_threshold': 0.6
                    }
                })
                corrective_rag.retriever.add_documents(sample_documents)
                self.rag_systems["CorrectiveRAG"] = corrective_rag
                logger.info("✅ CorrectiveRAG system initialized")
            except Exception as e:
                logger.warning(f"❌ Failed to initialize CorrectiveRAG: {e}")

            # Initialize SpeculativeRAG
            try:
                speculative_rag = SpeculativeRAG({
                    'retriever_config': {'chunk_size': 500, 'chunk_overlap': 50},
                    'generator_config': {'use_mock': allow_mocks},
                    'evaluator_config': {},
                    'speculative_config': {
                        'num_candidates': 3,
                        'verification_agents': 2,
                        'evidence_retrieval': True,
                        'selection_threshold': 0.7
                    }
                })
                speculative_rag.retriever.add_documents(sample_documents)
                self.rag_systems["SpeculativeRAG"] = speculative_rag
                logger.info("✅ SpeculativeRAG system initialized")
            except Exception as e:
                logger.warning(f"❌ Failed to initialize SpeculativeRAG: {e}")

            # Initialize SelfRAG
            try:
                self_rag = SelfRAG({
                    'retriever_config': {'chunk_size': 500, 'chunk_overlap': 50},
                    'generator_config': {'use_mock': allow_mocks},
                    'evaluator_config': {},
                    'reflection_config': {
                        'enable_self_assessment': True,
                        'confidence_threshold': 0.6,
                        'force_retrieval_for_complex_queries': True
                    }
                })
                self_rag.retriever.add_documents(sample_documents)
                self.rag_systems["SelfRAG"] = self_rag
                logger.info("✅ SelfRAG system initialized")
            except Exception as e:
                logger.warning(f"❌ Failed to initialize SelfRAG: {e}")

            # Initialize CacheAugmentedRAG
            try:
                cache_augmented_rag = CacheAugmentedRAG({
                    'base_rag_class': NaiveRAG,
                    'base_rag_config': {
                        'retriever_config': {'chunk_size': 500, 'chunk_overlap': 50},
                        'generator_config': {'use_mock': allow_mocks},
                        'evaluator_config': {}
                    },
                    'cache_config': {
                        'model_name': 'all-MiniLM-L6-v2',
                        'similarity_threshold': 0.8,
                        'max_size': 1000,
                        'eviction_policy': 'LRU'
                    },
                    'cache_enabled': True
                })
                cache_augmented_rag.base_rag.retriever.add_documents(sample_documents)
                self.rag_systems["CacheAugmentedRAG"] = cache_augmented_rag
                logger.info("✅ CacheAugmentedRAG system initialized")
            except Exception as e:
                logger.warning(f"❌ Failed to initialize CacheAugmentedRAG: {e}")

        except Exception as e:
            logger.error(f"❌ Error initializing RAG systems: {e}")

    def _setup_routes(self):
        """Configurar todas las rutas de la API."""

        @self.app.options("/query")
        async def options_rag_query():
            """OPTIONS handler for RAG query."""
            return {"Allow": "POST, OPTIONS"}

        @self.app.post("/query", response_model=RAGQueryResponse)
        async def query_rag(request: RAGQueryRequest):
            """Procesar consulta RAG."""
            try:
                if not request.query.strip():
                    raise HTTPException(status_code=400, detail="Query cannot be empty")

                # Obtener sistema RAG
                rag_system = self.rag_systems.get(request.rag_type)
                if not rag_system:
                    available_systems = list(self.rag_systems.keys())
                    raise HTTPException(
                        status_code=400,
                        detail=f"RAG system '{request.rag_type}' not available. Available: {available_systems}"
                    )

                # Ejecutar consulta
                start_time = datetime.now()
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: rag_system.run(request.query, **(request.parameters or {}))
                )
                end_time = datetime.now()

                # Formatear respuesta
                response = RAGQueryResponse(
                    query=request.query,
                    response=result.get('response', ''),
                    context=result.get('context', []),
                    metrics=result.get('metrics', {}),
                    metadata={
                        'rag_type': request.rag_type,
                        'processing_time': (end_time - start_time).total_seconds(),
                        'timestamp': end_time.isoformat()
                    }
                )

                logger.info(f"✅ RAG query processed: {request.query[:50]}... using {request.rag_type}")
                return response

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"❌ Error processing RAG query: {e}")
                raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

        @self.app.get("/health", response_model=RAGHealthResponse)
        async def health_check():
            """Health check del servicio RAG."""
            try:
                return RAGHealthResponse(
                    status="healthy",
                    rag_systems_available=list(self.rag_systems.keys()),
                    timestamp=datetime.now().isoformat()
                )
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return RAGHealthResponse(
                    status="unhealthy",
                    rag_systems_available=[],
                    timestamp=datetime.now().isoformat()
                )

        @self.app.get("/systems")
        async def get_available_systems():
            """Obtener sistemas RAG disponibles."""
            try:
                systems_info = {}
                for name, system in self.rag_systems.items():
                    systems_info[name] = {
                        "name": name,
                        "type": type(system).__name__,
                        "status": "available"
                    }

                return {
                    "systems": systems_info,
                    "total": len(systems_info),
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Error getting systems info: {e}")
                raise HTTPException(status_code=500, detail=f"Error retrieving systems: {str(e)}")

    def create_app(self) -> FastAPI:
        """Crear y retornar la aplicación FastAPI."""
        return self.app


# Instancia global de la API RAG
rag_api = RAGAPI()


def create_rag_app() -> FastAPI:
    """Función de conveniencia para crear la app FastAPI RAG."""
    return rag_api.create_app()
