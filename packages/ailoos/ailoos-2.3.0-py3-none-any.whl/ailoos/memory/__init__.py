"""
Sistema de Memoria Conversacional de AILOOS
==========================================

Este módulo implementa un sistema completo de memoria conversacional que permite
a EmpoorioLM recordar interacciones pasadas, gestionar importancia de información,
y mantener límites automáticos de memoria por usuario.

Características principales:
- Gestión de ítems de memoria con importancia y timestamps
- Compresión automática basada en importancia
- Límite de 256 ítems por usuario con gestión automática
- Integración con servicio de configuraciones
- Consultas avanzadas y búsqueda
- Mantenimiento automático y monitoreo

Componentes:
- models.py: Modelos de datos y estructuras
- repository.py: Capa de persistencia SQLite
- service.py: Lógica de negocio y gestión automática
- __init__.py: Punto de entrada principal

Uso básico:
    from src.ailoos.memory import MemoryService

    # Crear servicio
    memory_service = MemoryService()

    # Agregar ítem de memoria
    item = memory_service.add_memory_item(
        user_id=1,
        content="El usuario prefiere respuestas en español",
        importance=0.9,
        category="personal"
    )

    # Consultar memorias recientes
    recent = memory_service.get_recent_memories(user_id=1, limit=5)

    # Buscar por contenido
    results = memory_service.search_memory_by_content(user_id=1, search_term="español")
"""

from .models import (
    MemoryItem,
    MemoryStats,
    MemoryQuery,
    create_memory_item,
    calculate_compression_threshold
)

from .repository import MemoryRepository, MemoryRepositoryError

from .service import (
    MemoryService,
    MemoryServiceError,
    MemoryLimitExceededError,
    InvalidMemoryItemError
)

__all__ = [
    # Modelos
    'MemoryItem',
    'MemoryStats',
    'MemoryQuery',
    'create_memory_item',
    'calculate_compression_threshold',

    # Repositorio
    'MemoryRepository',
    'MemoryRepositoryError',

    # Servicio
    'MemoryService',
    'MemoryServiceError',
    'MemoryLimitExceededError',
    'InvalidMemoryItemError',
]

__version__ = "1.0.0"