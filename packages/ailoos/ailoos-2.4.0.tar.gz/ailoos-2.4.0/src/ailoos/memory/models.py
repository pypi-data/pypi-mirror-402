"""
Modelos de datos para el sistema de memoria conversacional de AILOOS
====================================================================

Este módulo define los modelos de datos para el sistema de memoria conversacional,
incluyendo ítems de memoria con importancia, timestamps y compresión automática.
"""

from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from datetime import datetime
import json
import hashlib


@dataclass
class MemoryItem:
    """
    Representa un ítem individual de memoria conversacional.

    Cada ítem contiene información sobre una interacción, su importancia,
    timestamp y metadatos adicionales para gestión eficiente.
    """

    id: str = field(default_factory=lambda: hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8])
    user_id: int = 0
    content: str = ""
    importance: float = 1.0  # 0.0 a 1.0, donde 1.0 es máxima importancia
    timestamp: datetime = field(default_factory=datetime.now)
    category: str = "general"  # "general", "personal", "factual", "emotional", "contextual"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    compressed: bool = False
    original_length: int = 0
    access_count: int = 0
    last_accessed: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el ítem de memoria a diccionario."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, list):
                result[key] = value
            else:
                result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        """Crea un ítem de memoria desde un diccionario."""
        # Convertir timestamps
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if 'last_accessed' in data and isinstance(data['last_accessed'], str):
            data['last_accessed'] = datetime.fromisoformat(data['last_accessed'])

        return cls(**data)

    def calculate_importance_score(self) -> float:
        """
        Calcula un puntaje de importancia compuesto basado en múltiples factores.

        Returns:
            float: Puntaje compuesto de importancia (0.0 a 1.0)
        """
        base_score = self.importance

        # Factor de recency (más reciente = más importante)
        days_since_creation = (datetime.now() - self.timestamp).days
        recency_factor = max(0.1, 1.0 - (days_since_creation / 365.0))  # Decae en un año

        # Factor de acceso (más accedido = más importante)
        access_factor = min(1.0, 0.5 + (self.access_count * 0.1))

        # Factor de categoría
        category_weights = {
            'personal': 1.2,
            'emotional': 1.1,
            'factual': 1.0,
            'contextual': 0.9,
            'general': 0.8
        }
        category_factor = category_weights.get(self.category, 0.8)

        # Puntaje compuesto
        composite_score = (base_score * 0.4 + recency_factor * 0.3 +
                          access_factor * 0.2 + category_factor * 0.1)

        return min(1.0, max(0.0, composite_score))

    def should_compress(self, threshold: float = 0.3) -> bool:
        """
        Determina si el ítem debería comprimirse basado en su importancia.

        Args:
            threshold: Umbral de importancia por debajo del cual comprimir

        Returns:
            bool: True si debería comprimirse
        """
        return self.calculate_importance_score() < threshold and not self.compressed

    def compress(self) -> None:
        """Comprime el contenido del ítem de memoria."""
        if self.compressed:
            return

        self.original_length = len(self.content)

        # Estrategia de compresión simple: resumir manteniendo información clave
        words = self.content.split()
        if len(words) > 50:
            # Mantener primeras 20 palabras, últimas 20, y resumen del medio
            compressed_parts = []
            compressed_parts.extend(words[:20])
            compressed_parts.append(f"[...{len(words) - 40} palabras resumidas...]")
            compressed_parts.extend(words[-20:])
            self.content = " ".join(compressed_parts)
        else:
            # Para contenido corto, mantener pero marcar como comprimido
            self.content = f"[Comprimido] {self.content[:100]}..."

        self.compressed = True

    def decompress(self) -> None:
        """Descomprime el ítem si es posible (placeholder para futura implementación)."""
        # En una implementación real, esto requeriría almacenar el contenido original
        # o usar algoritmos de compresión reversibles
        pass

    def update_access(self) -> None:
        """Actualiza estadísticas de acceso."""
        self.access_count += 1
        self.last_accessed = datetime.now()

    def validate(self) -> List[str]:
        """Valida el ítem de memoria."""
        errors = []

        if not self.content.strip():
            errors.append("El contenido no puede estar vacío")

        if not (0.0 <= self.importance <= 1.0):
            errors.append("La importancia debe estar entre 0.0 y 1.0")

        if self.category not in ["general", "personal", "factual", "emotional", "contextual"]:
            errors.append("Categoría no válida")

        if self.user_id <= 0:
            errors.append("ID de usuario inválido")

        if len(self.content) > 10000:  # Límite razonable
            errors.append("El contenido no puede exceder 10000 caracteres")

        return errors


@dataclass
class MemoryStats:
    """
    Estadísticas del sistema de memoria para un usuario.
    """

    user_id: int
    total_items: int = 0
    compressed_items: int = 0
    average_importance: float = 0.0
    oldest_item: Optional[datetime] = None
    newest_item: Optional[datetime] = None
    categories_count: Dict[str, int] = field(default_factory=dict)
    total_access_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convierte las estadísticas a diccionario."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryStats':
        """Crea estadísticas desde un diccionario."""
        # Convertir timestamps
        if 'oldest_item' in data and isinstance(data['oldest_item'], str):
            data['oldest_item'] = datetime.fromisoformat(data['oldest_item'])
        if 'newest_item' in data and isinstance(data['newest_item'], str):
            data['newest_item'] = datetime.fromisoformat(data['newest_item'])

        return cls(**data)


@dataclass
class MemoryQuery:
    """
    Parámetros para consultas de memoria.
    """

    user_id: int
    category: Optional[str] = None
    min_importance: Optional[float] = None
    max_importance: Optional[float] = None
    tags: Optional[List[str]] = None
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    limit: int = 50
    include_compressed: bool = True
    sort_by: str = "importance"  # "importance", "timestamp", "access_count"
    sort_order: str = "desc"  # "asc", "desc"

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la consulta a diccionario."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result


# Funciones de utilidad
def create_memory_item(user_id: int, content: str, importance: float = 1.0,
                      category: str = "general", tags: Optional[List[str]] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> MemoryItem:
    """
    Crea un nuevo ítem de memoria con validación básica.

    Args:
        user_id: ID del usuario
        content: Contenido de la memoria
        importance: Nivel de importancia (0.0-1.0)
        category: Categoría de la memoria
        tags: Lista de etiquetas
        metadata: Metadatos adicionales

    Returns:
        MemoryItem: Nuevo ítem de memoria

    Raises:
        ValueError: Si los parámetros son inválidos
    """
    item = MemoryItem(
        user_id=user_id,
        content=content,
        importance=importance,
        category=category,
        tags=tags or [],
        metadata=metadata or {}
    )

    errors = item.validate()
    if errors:
        raise ValueError(f"Errores de validación: {errors}")

    return item


def calculate_compression_threshold(memory_usage: int, max_items: int) -> float:
    """
    Calcula el umbral de compresión basado en el uso de memoria.

    Args:
        memory_usage: Número actual de ítems
        max_items: Límite máximo de ítems

    Returns:
        float: Umbral de importancia para compresión
    """
    if memory_usage < max_items * 0.8:
        return 0.2  # Umbral bajo cuando hay espacio
    elif memory_usage < max_items * 0.9:
        return 0.4  # Umbral medio
    else:
        return 0.6  # Umbral alto cuando cerca del límite