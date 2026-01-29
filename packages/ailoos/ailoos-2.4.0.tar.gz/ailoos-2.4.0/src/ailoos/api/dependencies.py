"""
Sistema de Inyección de Dependencias para AILOOS API Gateway
==========================================================

Este módulo maneja la carga y gestión de todos los modelos y servicios
que necesita el API Gateway para funcionar.

Componentes principales:
- EmpoorioLM: Modelo de lenguaje principal
- EmpoorioVision: Modelo de visión (placeholder por ahora)
- WorkflowEngine: Motor de workflows complejos
"""

import asyncio
import logging
import os
from typing import Optional, Any
from dataclasses import dataclass
from pathlib import Path

from ..core.logging import get_logger
from ..models.empoorio_lm import EmpoorioLM, EmpoorioLMConfig
from ..models.empoorio_lm.expert_system import ExpertManager
from ..models.vision.lvlm_wrapper import LVLMWrapper
from ..models.vision import VisionConfig
from ..inference.api import EmpoorioLMInferenceAPI, InferenceConfig
from ..workflows.engine import WorkflowEngine

logger = get_logger(__name__)

@dataclass
class ModelDependencies:
    """Contenedor para todas las dependencias de modelos con lazy loading."""
    empoorio_lm: Optional[EmpoorioLM] = None
    empoorio_vision: Optional[Any] = None  # Placeholder para visión
    workflow_engine: Optional[WorkflowEngine] = None

    # Flags para controlar carga lazy
    _empoorio_lm_loaded: bool = False
    _empoorio_vision_loaded: bool = False
    _workflow_engine_loaded: bool = False

    def is_ready(self) -> bool:
        """Verifica si todas las dependencias críticas están disponibles."""
        return (
            self.empoorio_lm is not None and
            self.workflow_engine is not None
        )

    async def get_empoorio_lm(self) -> Optional[EmpoorioLM]:
        """Obtiene EmpoorioLM con lazy loading."""
        if not self._empoorio_lm_loaded:
            self.empoorio_lm = await load_empoorio_lm()
            self._empoorio_lm_loaded = True
        return self.empoorio_lm

    async def get_empoorio_vision(self) -> Optional[Any]:
        """Obtiene EmpoorioVision con lazy loading."""
        if not self._empoorio_vision_loaded:
            self.empoorio_vision = await load_empoorio_vision()
            self._empoorio_vision_loaded = True
        return self.empoorio_vision

    async def get_workflow_engine(self) -> Optional[WorkflowEngine]:
        """Obtiene WorkflowEngine con lazy loading."""
        if not self._workflow_engine_loaded:
            self.workflow_engine = await load_workflow_engine()
            self._workflow_engine_loaded = True
        return self.workflow_engine

async def load_empoorio_lm() -> Optional[EmpoorioLM]:
    """Carga el modelo EmpoorioLM."""
    try:
        logger.info("📥 Loading EmpoorioLM model...")

        # Crear configuración básica
        config = EmpoorioLMConfig()

        # Intentar crear el modelo
        model = EmpoorioLM(config).float()

        # Aquí iría la lógica para cargar pesos pre-entrenados
        # Por ahora, solo inicializamos el modelo
        logger.info("✅ EmpoorioLM model loaded successfully")
        return model

    except Exception as e:
        logger.warning(f"⚠️ Failed to load EmpoorioLM: {e}")
        logger.warning("🚀 Continuing without EmpoorioLM - API endpoints may be unavailable")
        return None

async def load_empoorio_vision() -> Optional[Any]:
    """Carga el modelo EmpoorioVision usando LVLMWrapper."""
    try:
        logger.info("📥 Loading EmpoorioVision model...")

        # Cargar modelo base EmpoorioLM primero
        empoorio_lm = await load_empoorio_lm()
        if empoorio_lm is None:
            logger.warning("⚠️ Cannot load EmpoorioVision: EmpoorioLM not available")
            logger.warning("🚀 Continuing without EmpoorioVision")
            return None

        # Crear configuración de visión
        vision_config = VisionConfig()

        # Instanciar LVLMWrapper con el modelo base
        vision_model = LVLMWrapper(
            base_model=empoorio_lm,
            vision_config=vision_config
        )

        logger.info("✅ EmpoorioVision loaded successfully")
        return vision_model

    except Exception as e:
        logger.warning(f"⚠️ Failed to load EmpoorioVision: {e}")
        logger.warning("🚀 Continuing without EmpoorioVision")
        return None

async def load_workflow_engine() -> Optional[WorkflowEngine]:
    """Carga el WorkflowEngine con sus dependencias."""
    try:
        logger.info("📥 Loading WorkflowEngine...")

        # Crear directorio de expertos si no existe
        experts_dir = Path(os.getcwd()) / "models" / "experts"
        experts_dir.mkdir(parents=True, exist_ok=True)

        # Cargar dependencias del WorkflowEngine
        expert_manager = ExpertManager(experts_dir=str(experts_dir))
        inference_config = InferenceConfig()
        inference_api = EmpoorioLMInferenceAPI(inference_config)

        # Crear instancia del WorkflowEngine
        engine = WorkflowEngine(expert_manager, inference_api)

        # Aquí iría cualquier inicialización adicional del engine
        logger.info("✅ WorkflowEngine loaded successfully")
        return engine

    except Exception as e:
        logger.warning(f"⚠️ Failed to load WorkflowEngine: {e}")
        logger.warning("🚀 Continuing without WorkflowEngine")
        return None

async def get_model_dependencies() -> ModelDependencies:
    """
    Inicializa el contenedor de dependencias de modelos con lazy loading.

    Los modelos se cargan bajo demanda para optimizar el tiempo de startup.
    """
    logger.info("🔄 Initializing model dependencies container (lazy loading enabled)...")

    # Crear contenedor vacío - los modelos se cargarán bajo demanda
    deps = ModelDependencies()

    logger.info("✅ Model dependencies container initialized - models will load on first use")
    logger.info("💡 Lazy loading: EmpoorioLM, EmpoorioVision, and WorkflowEngine will load on demand")

    return deps

# Instancia global para desarrollo/testing
_global_deps: Optional[ModelDependencies] = None

async def get_global_dependencies() -> ModelDependencies:
    """Obtiene las dependencias globales (para testing)."""
    global _global_deps

    if _global_deps is None:
        _global_deps = await get_model_dependencies()

    return _global_deps

def reset_global_dependencies():
    """Resetea las dependencias globales (para testing)."""
    global _global_deps
    _global_deps = None
