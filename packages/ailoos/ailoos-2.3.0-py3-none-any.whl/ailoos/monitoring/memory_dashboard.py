#!/usr/bin/env python3
"""
Memory Dashboard - Dashboard visual del cerebro del usuario
Sistema de visualización que muestra el estado mental como grafo de conceptos conectados.
"""

import torch
import torch.nn as nn
from typing import Dict, List, Any, Optional, Tuple, Union
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
import threading
import time

from ..core.config import Config
from ..utils.logging import AiloosLogger
from ..inference.memory.memory_scope_slider import MemoryScopeSlider, MemoryScope, MemoryItem


class MemoryDashboard:
    """
    Dashboard visual que representa el cerebro del usuario como un grafo de conceptos conectados.

    Características principales:
    - Visualización de red neuronal de memoria
    - Grafo de conceptos con conexiones semánticas
    - Métricas de salud mental y cognitiva
    - Análisis de patrones de pensamiento
    - Alertas de sobrecarga cognitiva
    """

    def __init__(self, config: Config, memory_scope_slider: Optional[MemoryScopeSlider] = None):
        self.config = config
        self.logger = AiloosLogger(__name__)
        self.memory_scope_slider = memory_scope_slider

        # Estado del dashboard
        self.dashboard_data = {
            'brain_graph': {'nodes': [], 'links': []},
            'cognitive_metrics': {},
            'memory_health': {},
            'thought_patterns': {},
            'alerts': [],
            'last_update': None
        }

        # Configuración de visualización
        self.viz_config = {
            'max_nodes': 500,
            'min_link_strength': 0.1,
            'node_size_range': [5, 50],
            'update_interval_seconds': 30,
            'enable_real_time': True
        }

        # Redes para análisis cognitivo
        self.pattern_analyzer = self._build_pattern_analyzer()
        self.health_assessor = self._build_health_assessor()

        # Cache para optimización
        self.viz_cache = {}
        self.cache_timeout = 60  # segundos

        # Thread para actualizaciones en tiempo real
        self.update_thread = None
        self.running = False

        self.logger.info("🧠 Memory Dashboard inicializado")

    def _build_pattern_analyzer(self) -> nn.Module:
        """Construye red para análisis de patrones de pensamiento."""
        return nn.Sequential(
            nn.Linear(768, 512),
            nn.GELU(),
            nn.Linear(512, 256),
            nn.GELU(),
            nn.Linear(256, 128),
            nn.LayerNorm(128)
        )

    def _build_health_assessor(self) -> nn.Module:
        """Construye red para evaluación de salud cognitiva."""
        return nn.Sequential(
            nn.Linear(128 + 10, 64),  # Features cognitivas + métricas
            nn.GELU(),
            nn.Linear(64, 32),
            nn.GELU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

    async def get_dashboard_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Obtiene datos completos del dashboard.

        Args:
            force_refresh: Forzar actualización de datos

        Returns:
            Datos del dashboard
        """
        try:
            current_time = time.time()

            # Verificar si necesita actualización
            if (not force_refresh and self.dashboard_data['last_update'] and
                current_time - self.dashboard_data['last_update'] < self.viz_config['update_interval_seconds']):
                return self.dashboard_data

            # Actualizar datos
            await self._update_dashboard_data()

            self.dashboard_data['last_update'] = current_time
            return self.dashboard_data

        except Exception as e:
            self.logger.error(f"Error obteniendo datos del dashboard: {e}")
            return self._get_error_dashboard()

    async def _update_dashboard_data(self):
        """Actualiza todos los datos del dashboard."""
        try:
            # Obtener datos de memoria si está disponible
            memory_data = {}
            if self.memory_scope_slider:
                memory_data = self.memory_scope_slider.get_memory_visualization_data()

            # Construir grafo cerebral
            brain_graph = await self._build_brain_graph(memory_data)

            # Calcular métricas cognitivas
            cognitive_metrics = await self._calculate_cognitive_metrics(memory_data)

            # Evaluar salud mental
            memory_health = await self._assess_memory_health(memory_data, cognitive_metrics)

            # Analizar patrones de pensamiento
            thought_patterns = await self._analyze_thought_patterns(memory_data)

            # Generar alertas
            alerts = await self._generate_alerts(cognitive_metrics, memory_health)

            # Actualizar dashboard
            self.dashboard_data.update({
                'brain_graph': brain_graph,
                'cognitive_metrics': cognitive_metrics,
                'memory_health': memory_health,
                'thought_patterns': thought_patterns,
                'alerts': alerts
            })

            self.logger.debug("📊 Dashboard actualizado")

        except Exception as e:
            self.logger.error(f"Error actualizando dashboard: {e}")

    async def _build_brain_graph(self, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construye el grafo visual del cerebro basado en datos de memoria.

        Returns:
            Grafo con nodos y enlaces
        """
        nodes = []
        links = []

        if not memory_data:
            return {'nodes': nodes, 'links': links}

        # Procesar nodos de memoria
        memory_nodes = memory_data.get('nodes', [])
        node_id_map = {}

        for i, mem_node in enumerate(memory_nodes[:self.viz_config['max_nodes']]):
            # Crear nodo visual
            visual_node = {
                'id': f"memory_{i}",
                'type': 'memory',
                'scope': mem_node['scope'],
                'importance': mem_node['importance'],
                'age_hours': mem_node['age_hours'],
                'activity': mem_node['access_count'],
                'consolidation': mem_node['consolidation'],
                'tags': mem_node['tags'],
                'color': self._get_scope_color(mem_node['scope']),
                'size': self._calculate_node_size(mem_node),
                'position': self._calculate_node_position(mem_node, i),
                'metadata': {
                    'scope': mem_node['scope'],
                    'importance': mem_node['importance'],
                    'age': mem_node['age_hours'],
                    'activity': mem_node['access_count']
                }
            }

            nodes.append(visual_node)
            node_id_map[mem_node['id']] = f"memory_{i}"

        # Procesar enlaces de memoria
        memory_links = memory_data.get('links', [])
        for link in memory_links:
            if link['strength'] >= self.viz_config['min_link_strength']:
                source_id = node_id_map.get(link['source'])
                target_id = node_id_map.get(link['target'])

                if source_id and target_id:
                    visual_link = {
                        'source': source_id,
                        'target': target_id,
                        'strength': link['strength'],
                        'type': 'semantic',
                        'color': '#888'
                    }
                    links.append(visual_link)

        # Agregar nodos conceptuales (clusters)
        concept_nodes = self._create_concept_nodes(nodes)
        nodes.extend(concept_nodes)

        # Agregar enlaces conceptuales
        concept_links = self._create_concept_links(nodes, concept_nodes)
        links.extend(concept_links)

        return {
            'nodes': nodes,
            'links': links,
            'metadata': {
                'total_nodes': len(nodes),
                'total_links': len(links),
                'memory_nodes': len([n for n in nodes if n['type'] == 'memory']),
                'concept_nodes': len([n for n in nodes if n['type'] == 'concept'])
            }
        }

    def _get_scope_color(self, scope: str) -> str:
        """Obtiene color para un ámbito de memoria."""
        colors = {
            'amnesia': '#ff6b6b',
            'proyecto': '#4ecdc4',
            'vida': '#45b7d1'
        }
        return colors.get(scope, '#999')

    def _calculate_node_size(self, mem_node: Dict[str, Any]) -> float:
        """Calcula tamaño del nodo basado en importancia y actividad."""
        importance_factor = mem_node['importance']
        activity_factor = min(mem_node['access_count'] / 10, 1.0)  # Max 10 accesos
        consolidation_factor = mem_node['consolidation']

        size_factor = (importance_factor * 0.5 + activity_factor * 0.3 + consolidation_factor * 0.2)
        min_size, max_size = self.viz_config['node_size_range']

        return min_size + (max_size - min_size) * size_factor

    def _calculate_node_position(self, mem_node: Dict[str, Any], index: int) -> Dict[str, float]:
        """Calcula posición del nodo en el grafo."""
        # Posicionamiento basado en ámbito y propiedades
        scope_positions = {
            'amnesia': {'x': 0, 'y': 0},
            'proyecto': {'x': 200, 'y': 0},
            'vida': {'x': 400, 'y': 0}
        }

        base_pos = scope_positions.get(mem_node['scope'], {'x': 0, 'y': 0})

        # Añadir variación basada en importancia y edad
        importance_offset = (mem_node['importance'] - 0.5) * 100
        age_offset = (mem_node['age_hours'] / 24) * 50  # Más viejo = más alejado

        return {
            'x': base_pos['x'] + importance_offset + (index % 20 - 10) * 10,
            'y': base_pos['y'] + age_offset + (index // 20 - 5) * 20
        }

    def _create_concept_nodes(self, memory_nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Crea nodos conceptuales agrupando memoria relacionada."""
        concept_nodes = []

        # Agrupar por tags
        tag_groups = defaultdict(list)
        for node in memory_nodes:
            for tag in node.get('tags', []):
                tag_groups[tag].append(node)

        # Crear nodos para grupos grandes
        for tag, nodes_in_group in tag_groups.items():
            if len(nodes_in_group) >= 3:  # Mínimo 3 nodos para formar concepto
                avg_importance = sum(n['importance'] for n in nodes_in_group) / len(nodes_in_group)
                avg_age = sum(n['age_hours'] for n in nodes_in_group) / len(nodes_in_group)

                concept_node = {
                    'id': f"concept_{tag}",
                    'type': 'concept',
                    'label': tag,
                    'importance': avg_importance,
                    'size': 30 + avg_importance * 20,
                    'color': '#ffeb3b',
                    'position': {
                        'x': 300 + hash(tag) % 200 - 100,
                        'y': 100 + avg_age * 2
                    },
                    'metadata': {
                        'tag': tag,
                        'member_count': len(nodes_in_group),
                        'avg_importance': avg_importance,
                        'avg_age': avg_age
                    }
                }
                concept_nodes.append(concept_node)

        return concept_nodes

    def _create_concept_links(self, all_nodes: List[Dict[str, Any]],
                            concept_nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Crea enlaces entre nodos de memoria y conceptos."""
        links = []

        for concept in concept_nodes:
            tag = concept['metadata']['tag']

            # Encontrar nodos de memoria con este tag
            for node in all_nodes:
                if node['type'] == 'memory' and tag in node.get('tags', []):
                    links.append({
                        'source': node['id'],
                        'target': concept['id'],
                        'strength': 0.8,
                        'type': 'conceptual',
                        'color': '#ffeb3b'
                    })

        return links

    async def _calculate_cognitive_metrics(self, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula métricas cognitivas del usuario."""
        metrics = {}

        if not memory_data:
            return self._get_default_cognitive_metrics()

        scope_info = memory_data.get('scope_info', {})

        # Métricas básicas
        memory_stats = scope_info.get('memory_stats', {})
        total_memory = sum(memory_stats.values())

        # Diversidad cognitiva
        scope_diversity = len([s for s in memory_stats.values() if s > 0]) / 3.0

        # Actividad reciente
        recent_activity = sum(
            1 for node in memory_data.get('nodes', [])
            if node['age_hours'] < 1  # Última hora
        )

        # Profundidad de pensamiento (basado en enlaces)
        link_count = len(memory_data.get('links', []))
        thought_depth = min(link_count / max(total_memory, 1), 1.0)

        # Salud cognitiva
        usage_stats = scope_info.get('usage_stats', {})
        consolidation_rate = usage_stats.get('consolidation_events', 0) / max(usage_stats.get('memory_items_total', 1), 1)

        metrics.update({
            'memory_capacity': total_memory / 1000,  # Normalizado
            'cognitive_diversity': scope_diversity,
            'recent_activity': recent_activity / max(total_memory, 1),
            'thought_depth': thought_depth,
            'memory_consolidation': consolidation_rate,
            'attention_span': self._calculate_attention_span(memory_data),
            'learning_velocity': self._calculate_learning_velocity(memory_data),
            'cognitive_load': self._calculate_cognitive_load(memory_data)
        })

        return metrics

    def _get_default_cognitive_metrics(self) -> Dict[str, Any]:
        """Métricas cognitivas por defecto."""
        return {
            'memory_capacity': 0.0,
            'cognitive_diversity': 0.0,
            'recent_activity': 0.0,
            'thought_depth': 0.0,
            'memory_consolidation': 0.0,
            'attention_span': 0.0,
            'learning_velocity': 0.0,
            'cognitive_load': 0.0
        }

    def _calculate_attention_span(self, memory_data: Dict[str, Any]) -> float:
        """Calcula span de atención basado en patrones de memoria."""
        nodes = memory_data.get('nodes', [])
        if not nodes:
            return 0.0

        # Span basado en distribución de edades
        ages = [n['age_hours'] for n in nodes]
        avg_age = sum(ages) / len(ages)

        # Span normalizado (más bajo = mejor atención)
        attention_span = 1.0 / (1.0 + avg_age / 24)  # Normalizado por día
        return attention_span

    def _calculate_learning_velocity(self, memory_data: Dict[str, Any]) -> float:
        """Calcula velocidad de aprendizaje."""
        nodes = memory_data.get('nodes', [])
        if not nodes:
            return 0.0

        # Velocidad basada en items recientes con alta importancia
        recent_high_importance = sum(
            1 for n in nodes
            if n['age_hours'] < 1 and n['importance'] > 0.7
        )

        velocity = recent_high_importance / max(len(nodes), 1)
        return velocity

    def _calculate_cognitive_load(self, memory_data: Dict[str, Any]) -> float:
        """Calcula carga cognitiva actual."""
        scope_info = memory_data.get('scope_info', {})
        usage_stats = scope_info.get('usage_stats', {})

        # Carga basada en eventos recientes
        recent_forgetting = usage_stats.get('forgetting_events', 0)
        recent_consolidation = usage_stats.get('consolidation_events', 0)

        # Carga = olvido / (olvido + consolidación)
        total_events = recent_forgetting + recent_consolidation
        if total_events == 0:
            return 0.0

        cognitive_load = recent_forgetting / total_events
        return cognitive_load

    async def _assess_memory_health(self, memory_data: Dict[str, Any],
                                  cognitive_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa la salud de la memoria."""
        health = {
            'overall_score': 0.0,
            'memory_integrity': 0.0,
            'cognitive_flexibility': 0.0,
            'attention_health': 0.0,
            'learning_capacity': 0.0,
            'stress_indicators': [],
            'recommendations': []
        }

        # Calcular puntuaciones de salud
        health['memory_integrity'] = cognitive_metrics.get('memory_consolidation', 0.0)
        health['cognitive_flexibility'] = cognitive_metrics.get('cognitive_diversity', 0.0)
        health['attention_health'] = cognitive_metrics.get('attention_span', 0.0)
        health['learning_capacity'] = cognitive_metrics.get('learning_velocity', 0.0)

        # Puntuación general
        health['overall_score'] = (
            health['memory_integrity'] * 0.3 +
            health['cognitive_flexibility'] * 0.2 +
            health['attention_health'] * 0.25 +
            health['learning_capacity'] * 0.25
        )

        # Indicadores de estrés
        cognitive_load = cognitive_metrics.get('cognitive_load', 0.0)
        if cognitive_load > 0.7:
            health['stress_indicators'].append('cognitive_overload')
        if cognitive_metrics.get('attention_span', 1.0) < 0.3:
            health['stress_indicators'].append('attention_deficit')

        # Recomendaciones
        if health['overall_score'] < 0.5:
            health['recommendations'].append('Consider reducing cognitive load')
        if health['memory_integrity'] < 0.4:
            health['recommendations'].append('Memory consolidation needed')
        if health['cognitive_flexibility'] < 0.3:
            health['recommendations'].append('Increase cognitive diversity')

        return health

    async def _analyze_thought_patterns(self, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza patrones de pensamiento."""
        patterns = {
            'dominant_themes': [],
            'thinking_style': 'balanced',
            'creativity_index': 0.0,
            'analytical_depth': 0.0,
            'emotional_resonance': 0.0,
            'pattern_clusters': []
        }

        nodes = memory_data.get('nodes', [])
        if not nodes:
            return patterns

        # Análisis de temas dominantes
        tag_counts = defaultdict(int)
        for node in nodes:
            for tag in node.get('tags', []):
                tag_counts[tag] += 1

        # Top 5 temas
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        patterns['dominant_themes'] = [tag for tag, _ in sorted_tags[:5]]

        # Estilo de pensamiento basado en distribución
        scope_counts = defaultdict(int)
        for node in nodes:
            scope_counts[node['scope']] += 1

        total = sum(scope_counts.values())
        if total > 0:
            amnesia_ratio = scope_counts.get('amnesia', 0) / total
            proyecto_ratio = scope_counts.get('proyecto', 0) / total
            vida_ratio = scope_counts.get('vida', 0) / total

            if amnesia_ratio > 0.6:
                patterns['thinking_style'] = 'reactive'
            elif proyecto_ratio > 0.6:
                patterns['thinking_style'] = 'focused'
            elif vida_ratio > 0.6:
                patterns['thinking_style'] = 'reflective'
            else:
                patterns['thinking_style'] = 'balanced'

        # Índice de creatividad (diversidad de conexiones)
        links = memory_data.get('links', [])
        if links:
            avg_strength = sum(l['strength'] for l in links) / len(links)
            patterns['creativity_index'] = avg_strength

        return patterns

    async def _generate_alerts(self, cognitive_metrics: Dict[str, Any],
                             memory_health: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Genera alertas basadas en métricas."""
        alerts = []

        # Alerta de sobrecarga cognitiva
        cognitive_load = cognitive_metrics.get('cognitive_load', 0.0)
        if cognitive_load > 0.8:
            alerts.append({
                'type': 'warning',
                'title': 'Cognitive Overload Detected',
                'message': 'High cognitive load may affect memory performance',
                'severity': 'high',
                'timestamp': datetime.now().isoformat()
            })

        # Alerta de baja salud mental
        overall_health = memory_health.get('overall_score', 1.0)
        if overall_health < 0.4:
            alerts.append({
                'type': 'critical',
                'title': 'Memory Health Critical',
                'message': 'Memory health is critically low. Consider memory scope adjustment.',
                'severity': 'critical',
                'timestamp': datetime.now().isoformat()
            })

        # Alerta de falta de diversidad
        diversity = cognitive_metrics.get('cognitive_diversity', 1.0)
        if diversity < 0.3:
            alerts.append({
                'type': 'info',
                'title': 'Low Cognitive Diversity',
                'message': 'Consider exploring different types of content to improve cognitive flexibility.',
                'severity': 'medium',
                'timestamp': datetime.now().isoformat()
            })

        return alerts

    def _get_error_dashboard(self) -> Dict[str, Any]:
        """Dashboard de error cuando hay problemas."""
        return {
            'brain_graph': {'nodes': [], 'links': []},
            'cognitive_metrics': self._get_default_cognitive_metrics(),
            'memory_health': {'overall_score': 0.0, 'error': 'Unable to assess memory health'},
            'thought_patterns': {},
            'alerts': [{
                'type': 'error',
                'title': 'Dashboard Error',
                'message': 'Unable to load dashboard data',
                'severity': 'high',
                'timestamp': datetime.now().isoformat()
            }],
            'last_update': time.time()
        }

    def start_real_time_updates(self):
        """Inicia actualizaciones en tiempo real del dashboard."""
        if self.running:
            return

        self.running = True
        self.update_thread = threading.Thread(target=self._real_time_update_loop, daemon=True)
        self.update_thread.start()
        self.logger.info("🔄 Real-time dashboard updates started")

    def stop_real_time_updates(self):
        """Detiene actualizaciones en tiempo real."""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=5)
        self.logger.info("⏹️ Real-time dashboard updates stopped")

    def _real_time_update_loop(self):
        """Loop de actualización en tiempo real."""
        while self.running:
            try:
                # Ejecutar actualización en event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._update_dashboard_data())
                loop.close()

                time.sleep(self.viz_config['update_interval_seconds'])

            except Exception as e:
                self.logger.error(f"Error in real-time update loop: {e}")
                time.sleep(10)  # Esperar antes de reintentar

    def export_dashboard_snapshot(self, filepath: str):
        """
        Exporta snapshot del dashboard actual.

        Args:
            filepath: Ruta donde guardar el snapshot
        """
        try:
            snapshot = {
                'timestamp': datetime.now().isoformat(),
                'dashboard_data': self.dashboard_data,
                'config': self.viz_config
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, indent=2, ensure_ascii=False)

            self.logger.info(f"📸 Dashboard snapshot exported to {filepath}")

        except Exception as e:
            self.logger.error(f"Error exporting dashboard snapshot: {e}")
