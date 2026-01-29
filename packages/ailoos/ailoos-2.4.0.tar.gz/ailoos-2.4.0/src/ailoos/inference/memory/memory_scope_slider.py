#!/usr/bin/env python3
"""
Memory Scope Slider - Control deslizante de ámbito de memoria para UX
Sistema de control intuitivo que permite al usuario ajustar el alcance de la memoria
entre diferentes modos: Amnesia, Proyecto, Vida.
"""

import torch
import torch.nn as nn
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum
import logging
from dataclasses import dataclass
import time
from collections import defaultdict

from ..core.config import Config
from ..utils.logging import AiloosLogger


class MemoryScope(Enum):
    """Modos de ámbito de memoria."""
    AMNESIA = "amnesia"      # Memoria mínima - olvido rápido
    PROYECTO = "proyecto"    # Memoria de proyecto actual
    VIDA = "vida"           # Memoria completa de toda la vida


@dataclass
class MemoryScopeConfig:
    """Configuración para un ámbito de memoria específico."""
    scope: MemoryScope
    retention_hours: float          # Horas de retención
    context_window: int            # Ventana de contexto en tokens
    importance_threshold: float    # Umbral de importancia para retención
    consolidation_rate: float      # Tasa de consolidación de memoria
    forgetting_rate: float         # Tasa de olvido
    max_memory_items: int          # Máximo número de items en memoria


@dataclass
class MemoryItem:
    """Item de memoria con metadatos."""
    content: Any
    timestamp: float
    importance: float
    scope: MemoryScope
    access_count: int
    last_access: float
    consolidation_level: float
    tags: List[str]


class MemoryScopeSlider:
    """
    Control deslizante de ámbito de memoria para UX intuitiva.

    Permite al usuario ajustar dinámicamente el alcance de la memoria entre:
    - Amnesia: Memoria efímera, olvido rápido
    - Proyecto: Memoria contextual del proyecto actual
    - Vida: Memoria persistente de toda la vida del usuario
    """

    def __init__(self, config: Config):
        self.config = config
        self.logger = AiloosLogger(__name__)

        # Configuraciones predefinidas para cada ámbito
        self.scope_configs = {
            MemoryScope.AMNESIA: MemoryScopeConfig(
                scope=MemoryScope.AMNESIA,
                retention_hours=1.0,      # 1 hora
                context_window=128,       # Contexto corto
                importance_threshold=0.8, # Solo información muy importante
                consolidation_rate=0.1,   # Consolidación lenta
                forgetting_rate=0.9,      # Olvido rápido
                max_memory_items=100      # Memoria limitada
            ),
            MemoryScope.PROYECTO: MemoryScopeConfig(
                scope=MemoryScope.PROYECTO,
                retention_hours=24.0,     # 1 día
                context_window=512,       # Contexto medio
                importance_threshold=0.5, # Información relevante
                consolidation_rate=0.3,   # Consolidación media
                forgetting_rate=0.3,      # Olvido moderado
                max_memory_items=1000     # Memoria moderada
            ),
            MemoryScope.VIDA: MemoryScopeConfig(
                scope=MemoryScope.VIDA,
                retention_hours=8760.0,   # 1 año
                context_window=2048,      # Contexto largo
                importance_threshold=0.2, # Información general
                consolidation_rate=0.7,   # Consolidación fuerte
                forgetting_rate=0.05,     # Olvido muy lento
                max_memory_items=10000    # Memoria extensa
            )
        }

        # Estado actual
        self.current_scope = MemoryScope.PROYECTO  # Default
        self.slider_position = 0.5  # 0.0 = Amnesia, 0.5 = Proyecto, 1.0 = Vida

        # Memoria organizada por ámbito
        self.memory_store: Dict[MemoryScope, List[MemoryItem]] = {
            scope: [] for scope in MemoryScope
        }

        # Estadísticas de uso
        self.usage_stats = {
            'scope_changes': 0,
            'memory_items_total': 0,
            'memory_items_retained': 0,
            'forgetting_events': 0,
            'consolidation_events': 0,
            'security_events': 0,
            'validation_events': 0
        }

        # Sistema de validación de hechos y detección de contradicciones
        self.fact_validator = self._build_fact_validator()
        self.contradiction_detector = self._build_contradiction_detector()
        self.verified_facts = set()  # Cache de hechos verificados
        self.contradiction_alerts = []  # Alertas de contradicciones detectadas

        # Redes neuronales para análisis de importancia
        self.importance_analyzer = self._build_importance_analyzer()
        self.consolidation_network = self._build_consolidation_network()

        self.logger.info("🎚️ Memory Scope Slider inicializado con validación de seguridad - Modo: Proyecto")

    def _build_importance_analyzer(self) -> nn.Module:
        """Construye la red para analizar importancia de contenido."""
        return nn.Sequential(
            nn.Linear(768, 256),  # Asumiendo embeddings de 768
            nn.GELU(),
            nn.Linear(256, 128),
            nn.GELU(),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )

    def _build_consolidation_network(self) -> nn.Module:
        """Construye la red para consolidación de memoria."""
        return nn.Sequential(
            nn.Linear(768 + 4, 256),  # Embeddings + metadatos
            nn.GELU(),
            nn.Linear(256, 128),
            nn.GELU(),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )

    def _build_fact_validator(self) -> nn.Module:
        """Construye la red para validación de hechos."""
        return nn.Sequential(
            nn.Linear(768, 512),
            nn.GELU(),
            nn.Linear(512, 256),
            nn.GELU(),
            nn.Linear(256, 128),
            nn.GELU(),
            nn.Linear(128, 1),
            nn.Sigmoid()  # Output: 0-1 (probabilidad de ser factual)
        )

    def _build_contradiction_detector(self) -> nn.Module:
        """Construye la red para detección de contradicciones."""
        return nn.Sequential(
            nn.Linear(768 * 2, 512),  # Concatenated embeddings
            nn.GELU(),
            nn.Linear(512, 256),
            nn.GELU(),
            nn.Linear(256, 128),
            nn.GELU(),
            nn.Linear(128, 1),
            nn.Sigmoid()  # Output: 0-1 (probabilidad de contradicción)
        )

    def set_scope_by_slider(self, position: float) -> Dict[str, Any]:
        """
        Ajusta el ámbito de memoria usando el slider (0.0 a 1.0).

        Args:
            position: Posición del slider (0.0 = Amnesia, 1.0 = Vida)

        Returns:
            Información del cambio de ámbito
        """
        position = max(0.0, min(1.0, position))  # Clamp

        # Determinar ámbito basado en posición
        if position < 0.33:
            new_scope = MemoryScope.AMNESIA
        elif position < 0.67:
            new_scope = MemoryScope.PROYECTO
        else:
            new_scope = MemoryScope.VIDA

        # Aplicar transición suave si cambió el ámbito
        if new_scope != self.current_scope:
            transition_info = self._transition_scope(new_scope, position)
            self.current_scope = new_scope
            self.slider_position = position
            self.usage_stats['scope_changes'] += 1

            self.logger.info(f"🎚️ Scope cambiado a {new_scope.value} (slider: {position:.2f})")
            return transition_info

        self.slider_position = position
        return {
            'scope_changed': False,
            'current_scope': self.current_scope.value,
            'slider_position': position,
            'message': f'Scope mantenido: {self.current_scope.value}'
        }

    def _transition_scope(self, new_scope: MemoryScope, slider_position: float) -> Dict[str, Any]:
        """Transición suave entre ámbitos de memoria."""
        old_config = self.scope_configs[self.current_scope]
        new_config = self.scope_configs[new_scope]

        # Calcular factores de transición basados en slider
        transition_factor = slider_position

        # Configuración interpolada
        interpolated_config = MemoryScopeConfig(
            scope=new_scope,
            retention_hours=old_config.retention_hours + (new_config.retention_hours - old_config.retention_hours) * transition_factor,
            context_window=int(old_config.context_window + (new_config.context_window - old_config.context_window) * transition_factor),
            importance_threshold=old_config.importance_threshold + (new_config.importance_threshold - old_config.importance_threshold) * transition_factor,
            consolidation_rate=old_config.consolidation_rate + (new_config.consolidation_rate - old_config.consolidation_rate) * transition_factor,
            forgetting_rate=old_config.forgetting_rate + (new_config.forgetting_rate - old_config.forgetting_rate) * transition_factor,
            max_memory_items=int(old_config.max_memory_items + (new_config.max_memory_items - old_config.max_memory_items) * transition_factor)
        )

        # Limpiar memoria según nuevo ámbito
        cleaned_items = self._cleanup_memory_for_scope(new_scope, interpolated_config)

        return {
            'scope_changed': True,
            'old_scope': self.current_scope.value,
            'new_scope': new_scope.value,
            'slider_position': slider_position,
            'interpolated_config': {
                'retention_hours': interpolated_config.retention_hours,
                'context_window': interpolated_config.context_window,
                'importance_threshold': interpolated_config.importance_threshold,
                'max_memory_items': interpolated_config.max_memory_items
            },
            'memory_cleaned': cleaned_items,
            'message': f'Transición a {new_scope.value} completada'
        }

    def _cleanup_memory_for_scope(self, new_scope: MemoryScope, config: MemoryScopeConfig) -> int:
        """Limpia memoria incompatible con el nuevo ámbito."""
        current_time = time.time()
        cleaned_count = 0

        # Para cada ámbito, aplicar reglas de limpieza
        for scope in MemoryScope:
            memory_items = self.memory_store[scope]
            retained_items = []

            for item in memory_items:
                # Calcular edad en horas
                age_hours = (current_time - item.timestamp) / 3600

                # Reglas de retención basadas en ámbito
                should_retain = True

                if new_scope == MemoryScope.AMNESIA:
                    # En amnesia, solo retener items muy recientes e importantes
                    should_retain = age_hours < 0.5 and item.importance > 0.9

                elif new_scope == MemoryScope.PROYECTO:
                    # En proyecto, retener items del proyecto actual
                    should_retain = (age_hours < config.retention_hours and
                                   'project' in item.tags)

                elif new_scope == MemoryScope.VIDA:
                    # En vida, retener todo con importancia suficiente
                    should_retain = (age_hours < config.retention_hours and
                                   item.importance >= config.importance_threshold)

                if should_retain and len(retained_items) < config.max_memory_items:
                    retained_items.append(item)
                else:
                    cleaned_count += 1

            self.memory_store[scope] = retained_items

        self.usage_stats['memory_items_retained'] = sum(len(items) for items in self.memory_store.values())
        return cleaned_count

    def add_memory_item(self, content: Any, embedding: torch.Tensor,
                        tags: List[str] = None, scope_override: MemoryScope = None) -> MemoryItem:
        """
        Agrega un nuevo item a la memoria con validación de seguridad.

        Args:
            content: Contenido a memorizar
            embedding: Embedding del contenido
            tags: Etiquetas para categorización
            scope_override: Forzar ámbito específico

        Returns:
            MemoryItem creado
        """
        if tags is None:
            tags = []

        current_time = time.time()
        scope = scope_override or self.current_scope

        # Validación de seguridad: verificar hechos y contradicciones
        security_check = self._validate_memory_security(content, embedding, scope)
        if not security_check['approved']:
            self.usage_stats['security_events'] += 1
            self.logger.warning(f"🚨 Memoria rechazada por seguridad: {security_check['reason']}")
            # Crear item con importancia cero para marcar como sospechoso
            importance = 0.0
        else:
            # Analizar importancia usando la red neuronal
            with torch.no_grad():
                importance = self.importance_analyzer(embedding.unsqueeze(0)).item()

        # Crear item de memoria
        memory_item = MemoryItem(
            content=content,
            timestamp=current_time,
            importance=importance,
            scope=scope,
            access_count=0,
            last_access=current_time,
            consolidation_level=0.0,
            tags=tags
        )

        # Agregar a store correspondiente
        config = self.scope_configs[scope]
        memory_list = self.memory_store[scope]

        # Aplicar límite de memoria
        if len(memory_list) >= config.max_memory_items:
            # Remover item menos importante
            memory_list.sort(key=lambda x: x.importance)
            removed_item = memory_list.pop(0)
            self.usage_stats['forgetting_events'] += 1

        memory_list.append(memory_item)
        self.usage_stats['memory_items_total'] += 1

        self.logger.debug(f"🧠 Memoria agregada: importancia={importance:.3f}, scope={scope.value}, security_check={security_check['approved']}")
        return memory_item

    def retrieve_relevant_memory(self, query_embedding: torch.Tensor,
                               context_window: int = None) -> List[MemoryItem]:
        """
        Recupera memoria relevante para una consulta.

        Args:
            query_embedding: Embedding de la consulta
            context_window: Ventana de contexto (usa config actual si None)

        Returns:
            Lista de items de memoria relevantes
        """
        if context_window is None:
            config = self.scope_configs[self.current_scope]
            context_window = config.context_window

        relevant_items = []
        current_time = time.time()

        # Buscar en todos los ámbitos accesibles
        accessible_scopes = self._get_accessible_scopes()

        for scope in accessible_scopes:
            memory_items = self.memory_store[scope]
            config = self.scope_configs[scope]

            for item in memory_items:
                # Verificar tiempo de retención
                age_hours = (current_time - item.timestamp) / 3600
                if age_hours > config.retention_hours:
                    continue

                # Calcular similitud (cosine similarity)
                if hasattr(item, 'embedding'):
                    similarity = torch.cosine_similarity(
                        query_embedding.unsqueeze(0),
                        item.embedding.unsqueeze(0)
                    ).item()
                else:
                    # Fallback si no hay embedding
                    similarity = item.importance

                # Aplicar umbral de importancia
                if similarity >= config.importance_threshold:
                    # Actualizar estadísticas de acceso
                    item.access_count += 1
                    item.last_access = current_time

                    relevant_items.append((item, similarity))

        # Ordenar por similitud y recencia
        relevant_items.sort(key=lambda x: (x[1], x[0].last_access), reverse=True)

        # Limitar a ventana de contexto
        result_items = [item for item, _ in relevant_items[:context_window]]

        self.logger.debug(f"🔍 Recuperados {len(result_items)} items de memoria")
        return result_items

    def _validate_memory_security(self, content: Any, embedding: torch.Tensor, scope: MemoryScope) -> Dict[str, Any]:
        """
        Valida la seguridad del contenido de memoria.

        Args:
            content: Contenido a validar
            embedding: Embedding del contenido
            scope: Ámbito de memoria

        Returns:
            Dict con resultado de validación
        """
        try:
            self.usage_stats['validation_events'] += 1

            # Convertir contenido a string para análisis
            content_str = str(content).lower()

            # 1. Validación básica de hechos (usando red neuronal)
            with torch.no_grad():
                fact_score = self.fact_validator(embedding.unsqueeze(0)).item()

            # Umbrales de validación basados en ámbito
            fact_thresholds = {
                MemoryScope.AMNESIA: 0.9,  # Muy estricto en amnesia
                MemoryScope.PROYECTO: 0.7, # Moderado en proyecto
                MemoryScope.VIDA: 0.5      # Más permisivo en vida
            }

            fact_threshold = fact_thresholds[scope]

            if fact_score < fact_threshold:
                return {
                    'approved': False,
                    'reason': f'Fact validation failed (score: {fact_score:.3f}, threshold: {fact_threshold})',
                    'fact_score': fact_score
                }

            # 2. Detección de contradicciones
            contradiction_detected = self._detect_contradictions(content_str, embedding, scope)
            if contradiction_detected['detected']:
                self.contradiction_alerts.append({
                    'timestamp': time.time(),
                    'content': content_str,
                    'contradiction_with': contradiction_detected['existing_content'],
                    'severity': contradiction_detected['severity']
                })

                # En ámbitos estrictos, rechazar contradicciones
                if scope in [MemoryScope.AMNESIA, MemoryScope.PROYECTO]:
                    return {
                        'approved': False,
                        'reason': f'Contradiction detected with existing memory: {contradiction_detected["existing_content"][:50]}...',
                        'contradiction_info': contradiction_detected
                    }

            # 3. Verificación de contenido sensible
            if self._contains_sensitive_content(content_str):
                return {
                    'approved': False,
                    'reason': 'Content contains sensitive or potentially harmful information'
                }

            return {
                'approved': True,
                'fact_score': fact_score,
                'reason': 'Content validated successfully'
            }

        except Exception as e:
            self.logger.error(f"Error in memory security validation: {e}")
            # En caso de error, permitir pero marcar como sospechoso
            return {
                'approved': True,
                'reason': f'Validation error (allowing but flagged): {str(e)}',
                'error': str(e)
            }

    def _detect_contradictions(self, content_str: str, embedding: torch.Tensor, scope: MemoryScope) -> Dict[str, Any]:
        """
        Detecta contradicciones con memoria existente.

        Returns:
            Dict con información de contradicción detectada
        """
        try:
            # Buscar en memoria existente del mismo ámbito
            existing_items = self.memory_store[scope]

            for item in existing_items:
                if hasattr(item, 'embedding') and item.embedding is not None:
                    # Calcular similitud semántica
                    with torch.no_grad():
                        combined_embedding = torch.cat([embedding, item.embedding])
                        contradiction_score = self.contradiction_detector(combined_embedding.unsqueeze(0)).item()

                    # Si hay alta probabilidad de contradicción
                    if contradiction_score > 0.7:
                        return {
                            'detected': True,
                            'existing_content': str(item.content),
                            'severity': 'high' if contradiction_score > 0.9 else 'medium',
                            'score': contradiction_score
                        }

            return {'detected': False}

        except Exception as e:
            self.logger.error(f"Error in contradiction detection: {e}")
            return {'detected': False, 'error': str(e)}

    def _contains_sensitive_content(self, content_str: str) -> bool:
        """
        Verifica si el contenido contiene información sensible.

        Returns:
            True si contiene contenido sensible
        """
        sensitive_patterns = [
            # Información personal
            r'\b\d{3,4}-\d{3,4}-\d{4}\b',  # Números de teléfono
            r'\b\d{4} \d{4} \d{4} \d{4}\b',  # Tarjetas de crédito
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Emails
            r'\b\d{9,12}\b',  # Números de identificación

            # Información financiera
            r'\b\d{10,16}\b',  # Números de cuenta
            r'\$\d+[\.,]\d{2}',  # Montos de dinero

            # Información técnica sensible
            r'\bapi[_-]?key\b',  # API keys
            r'\bpassword\b',  # Contraseñas
            r'\btoken\b',  # Tokens
            r'\bsecret\b',  # Secretos
        ]

        import re
        for pattern in sensitive_patterns:
            if re.search(pattern, content_str, re.IGNORECASE):
                return True

        return False

    def _get_accessible_scopes(self) -> List[MemoryScope]:
        """Determina qué ámbitos son accesibles en el modo actual."""
        if self.current_scope == MemoryScope.AMNESIA:
            return [MemoryScope.AMNESIA]
        elif self.current_scope == MemoryScope.PROYECTO:
            return [MemoryScope.AMNESIA, MemoryScope.PROYECTO]
        else:  # VIDA
            return [MemoryScope.AMNESIA, MemoryScope.PROYECTO, MemoryScope.VIDA]

    def consolidate_memory(self):
        """Ejecuta consolidación de memoria periódica."""
        current_time = time.time()
        consolidated_count = 0

        for scope in MemoryScope:
            memory_items = self.memory_store[scope]
            config = self.scope_configs[scope]

            for item in memory_items:
                # Calcular tiempo desde último acceso
                time_since_access = current_time - item.last_access

                # Consolidar basado en frecuencia de acceso e importancia
                if item.access_count > 5 and item.importance > config.importance_threshold:
                    # Aumentar nivel de consolidación
                    consolidation_boost = min(config.consolidation_rate, 1.0 - item.consolidation_level)
                    item.consolidation_level += consolidation_boost
                    consolidated_count += 1

                # Aplicar olvido gradual
                forgetting_factor = config.forgetting_rate * (time_since_access / 86400)  # Por día
                item.importance = max(0.0, item.importance - forgetting_factor)

        if consolidated_count > 0:
            self.usage_stats['consolidation_events'] += consolidated_count
            self.logger.debug(f"🧠 Consolidación completada: {consolidated_count} items")

    def get_scope_info(self) -> Dict[str, Any]:
        """Obtiene información completa del ámbito actual."""
        config = self.scope_configs[self.current_scope]

        return {
            'current_scope': self.current_scope.value,
            'slider_position': self.slider_position,
            'config': {
                'retention_hours': config.retention_hours,
                'context_window': config.context_window,
                'importance_threshold': config.importance_threshold,
                'consolidation_rate': config.consolidation_rate,
                'forgetting_rate': config.forgetting_rate,
                'max_memory_items': config.max_memory_items
            },
            'memory_stats': {
                scope.value: len(items) for scope, items in self.memory_store.items()
            },
            'usage_stats': self.usage_stats.copy(),
            'accessible_scopes': [s.value for s in self._get_accessible_scopes()]
        }

    def get_memory_visualization_data(self) -> Dict[str, Any]:
        """
        Obtiene datos para visualización del estado de memoria.

        Returns:
            Datos para dashboard visual
        """
        current_time = time.time()

        # Preparar datos para grafo de conceptos
        nodes = []
        links = []

        scope_colors = {
            MemoryScope.AMNESIA: '#ff6b6b',
            MemoryScope.PROYECTO: '#4ecdc4',
            MemoryScope.VIDA: '#45b7d1'
        }

        node_id = 0
        for scope in MemoryScope:
            memory_items = self.memory_store[scope]

            for item in memory_items:
                # Crear nodo
                age_hours = (current_time - item.timestamp) / 3600
                node_size = max(5, min(20, item.importance * 20))

                nodes.append({
                    'id': node_id,
                    'scope': scope.value,
                    'importance': item.importance,
                    'age_hours': age_hours,
                    'access_count': item.access_count,
                    'consolidation': item.consolidation_level,
                    'tags': item.tags,
                    'color': scope_colors[scope],
                    'size': node_size
                })

                # Crear enlaces basados en tags similares (simplificado)
                for other_node in nodes[:-1]:  # Excluir el nodo actual
                    if other_node['scope'] == scope.value:
                        # Calcular similitud de tags
                        common_tags = set(item.tags) & set(other_node['tags'])
                        if len(common_tags) > 0:
                            similarity = len(common_tags) / max(len(item.tags), len(other_node['tags']), 1)
                            if similarity > 0.3:
                                links.append({
                                    'source': other_node['id'],
                                    'target': node_id,
                                    'strength': similarity
                                })

                node_id += 1

        return {
            'nodes': nodes,
            'links': links,
            'scope_info': self.get_scope_info(),
            'timestamp': current_time
        }

    def get_security_report(self) -> Dict[str, Any]:
        """
        Obtiene reporte de seguridad del sistema de memoria.

        Returns:
            Reporte completo de seguridad
        """
        return {
            'security_events': self.usage_stats['security_events'],
            'validation_events': self.usage_stats['validation_events'],
            'contradiction_alerts': len(self.contradiction_alerts),
            'recent_alerts': self.contradiction_alerts[-5:] if self.contradiction_alerts else [],
            'verified_facts_count': len(self.verified_facts),
            'security_score': self._calculate_security_score()
        }

    def _calculate_security_score(self) -> float:
        """
        Calcula puntuación de seguridad del sistema de memoria.

        Returns:
            Puntuación de seguridad (0-100)
        """
        try:
            total_validations = self.usage_stats['validation_events']
            security_events = self.usage_stats['security_events']
            contradiction_alerts = len(self.contradiction_alerts)

            if total_validations == 0:
                return 100.0  # Sin actividad = seguro

            # Factores de seguridad
            validation_rate = (total_validations - security_events) / total_validations
            contradiction_penalty = min(contradiction_alerts * 5, 30)  # Máximo 30 puntos de penalización

            # Puntuación base
            base_score = validation_rate * 100

            # Aplicar penalizaciones
            final_score = max(0, base_score - contradiction_penalty)

            return round(final_score, 1)

        except Exception as e:
            self.logger.error(f"Error calculating security score: {e}")
            return 50.0  # Puntuación por defecto en caso de error
