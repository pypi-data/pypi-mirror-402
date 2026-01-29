"""
Liquid Memory - Sistema de Memoria Líquida para MoE
Sistema de memoria líquida que asigna memoria especializada a cada experto MoE.
Implementa asignación dinámica, optimización de recursos y compatibilidad con MIRAS.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any, Union
import math
import logging
import time
from dataclasses import dataclass
from collections import defaultdict
import threading

from .miras_block import MIRASBlock, MIRASState, create_miras_block

logger = logging.getLogger(__name__)


@dataclass
class ExpertMemoryProfile:
    """Perfil de memoria para un experto específico."""
    expert_id: int
    domain_specialization: str  # e.g., "mathematics", "language", "code", "general"
    memory_capacity: int  # Slots de memoria asignados
    specialization_score: float  # Puntaje de especialización (0-1)
    usage_frequency: float  # Frecuencia de uso reciente
    memory_efficiency: float  # Eficiencia de uso de memoria
    last_accessed: float  # Timestamp del último acceso


@dataclass
class MemorySpilloverPointer:
    """Puntero ligero para spillover de memoria entre expertos."""
    source_expert_id: int
    target_expert_id: int
    memory_slice: torch.Tensor
    spillover_size: int
    access_count: int = 0
    last_access: float = 0.0
    priority: float = 1.0


@dataclass
class LiquidMemoryState:
    """Estado global del sistema de memoria líquida."""
    expert_profiles: Dict[int, ExpertMemoryProfile]
    global_memory_pool: torch.Tensor  # Pool de memoria compartida [total_memory, compressed_size]
    memory_allocation: Dict[int, torch.Tensor]  # Asignación por experto [expert_id -> memory_slice]
    memory_utilization: Dict[int, float]  # Utilización por experto
    adaptation_history: List[Dict[str, Any]]  # Historial de adaptaciones
    spillover_pointers: Dict[int, List[MemorySpilloverPointer]]  # Punteros de spillover por experto
    lock: threading.Lock  # Para acceso thread-safe


class LiquidMemoryManager(nn.Module):
    """
    Administrador de Memoria Líquida para MoE.
    Gestiona la asignación dinámica de memoria especializada por experto.
    """

    def __init__(
        self,
        num_experts: int,
        hidden_size: int,
        total_memory_slots: int = 4096,
        base_memory_per_expert: int = 256,
        adaptation_rate: float = 0.01,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        super().__init__()
        self.num_experts = num_experts
        self.hidden_size = hidden_size
        self.total_memory_slots = total_memory_slots
        self.base_memory_per_expert = base_memory_per_expert
        self.adaptation_rate = adaptation_rate
        self.device = device

        # Pool de memoria global comprimida
        compressed_size = hidden_size // 4
        self.register_buffer('global_memory_pool', torch.zeros(total_memory_slots, compressed_size))

        # Estado de memoria líquida
        self.liquid_state = LiquidMemoryState(
            expert_profiles={},
            global_memory_pool=self.global_memory_pool,
            memory_allocation={},
            memory_utilization={},
            adaptation_history=[],
            spillover_pointers={},
            lock=threading.Lock()
        )

        # Redes para gestión de memoria
        self.memory_router = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.GELU(),
            nn.Linear(hidden_size // 2, num_experts),
            nn.Softmax(dim=-1)
        )

        self.memory_optimizer = nn.Sequential(
            nn.Linear(hidden_size + num_experts, hidden_size // 2),
            nn.GELU(),
            nn.Linear(hidden_size // 2, 1),
            nn.Sigmoid()  # Probabilidad de optimización
        )

        # Inicializar perfiles de expertos
        self._initialize_expert_profiles()

        # Mover a dispositivo
        self.to(device)

        logger.info(f"🧠 LiquidMemoryManager inicializado: {num_experts} expertos, {total_memory_slots} slots totales")

    def _initialize_expert_profiles(self):
        """Inicializa perfiles de memoria para cada experto."""
        domain_templates = [
            "mathematics", "language", "code", "science",
            "reasoning", "analysis", "creativity", "general"
        ]

        for i in range(self.num_experts):
            domain = domain_templates[i % len(domain_templates)]
            profile = ExpertMemoryProfile(
                expert_id=i,
                domain_specialization=domain,
                memory_capacity=self.base_memory_per_expert,
                specialization_score=0.5,  # Inicial neutral
                usage_frequency=0.0,
                memory_efficiency=1.0,
                last_accessed=0.0
            )
            self.liquid_state.expert_profiles[i] = profile

            # Asignar memoria inicial
            start_idx = i * self.base_memory_per_expert
            end_idx = start_idx + self.base_memory_per_expert
            self.liquid_state.memory_allocation[i] = self.global_memory_pool[start_idx:end_idx]
            self.liquid_state.memory_utilization[i] = 0.0

    def allocate_expert_memory(
        self,
        expert_id: int,
        requested_capacity: int,
        context_embedding: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Asigna memoria especializada para un experto.

        Args:
            expert_id: ID del experto
            requested_capacity: Capacidad solicitada
            context_embedding: Embedding contextual para optimización

        Returns:
            Memoria asignada [capacity, compressed_size]
        """
        with self.liquid_state.lock:
            profile = self.liquid_state.expert_profiles[expert_id]

            # Calcular capacidad óptima basada en contexto
            if context_embedding is not None:
                optimal_capacity = self._calculate_optimal_capacity(expert_id, context_embedding)
                requested_capacity = int(optimal_capacity)

            # Limitar capacidad máxima
            max_capacity = min(requested_capacity, self.total_memory_slots // self.num_experts * 2)
            actual_capacity = min(max_capacity, profile.memory_capacity * 2)  # Máximo doble

            # Intentar asignación normal primero
            if actual_capacity != profile.memory_capacity:
                success = self._reallocate_expert_memory(expert_id, actual_capacity)
                if not success:
                    # Si falla la reasignación, intentar spillover
                    logger.info(f"💧 Reasignación fallida para experto {expert_id}, intentando spillover")
                    spillover_memory = self.request_memory_spillover(expert_id, requested_capacity, context_embedding)
                    if spillover_memory is not None:
                        # Combinar memoria existente con spillover
                        existing_memory = self.liquid_state.memory_allocation.get(expert_id)
                        if existing_memory is not None:
                            combined_memory = torch.cat([existing_memory, spillover_memory], dim=0)
                        else:
                            combined_memory = spillover_memory

                        # Almacenar memoria combinada temporalmente
                        self.liquid_state.memory_allocation[expert_id] = combined_memory
                        profile.memory_capacity = combined_memory.shape[0]
                        logger.info(f"✅ Spillover exitoso para experto {expert_id}: {spillover_memory.shape[0]} slots adicionales")
                    else:
                        logger.warning(f"❌ Spillover fallido para experto {expert_id}, usando capacidad reducida")
                        # Usar capacidad máxima posible
                        actual_capacity = min(profile.memory_capacity, max_capacity)
                        self._reallocate_expert_memory(expert_id, actual_capacity)
                else:
                    profile.memory_capacity = actual_capacity
            else:
                # Capacidad ya adecuada, verificar si hay spillover que liberar
                if expert_id in self.liquid_state.spillover_pointers and self.liquid_state.spillover_pointers[expert_id]:
                    # Si la demanda bajó, liberar spillover
                    self.release_memory_spillover(expert_id)

            # Actualizar perfil
            profile.last_accessed = torch.cuda.Event().elapsed_time() if torch.cuda.is_available() else time.time()

            return self.liquid_state.memory_allocation[expert_id]

    def _calculate_optimal_capacity(
        self,
        expert_id: int,
        context_embedding: torch.Tensor
    ) -> float:
        """Calcula la capacidad óptima basada en el contexto."""
        # Usar el router de memoria para determinar importancia
        routing_logits = self.memory_router(context_embedding)  # [num_experts]
        expert_importance = routing_logits[expert_id].item()

        # Usar optimizador de memoria
        combined_input = torch.cat([context_embedding, routing_logits], dim=-1)
        optimization_prob = self.memory_optimizer(combined_input).item()

        # Calcular capacidad base
        base_capacity = self.base_memory_per_expert
        profile = self.liquid_state.expert_profiles[expert_id]

        # Ajustar basado en importancia y eficiencia
        capacity_multiplier = (
            0.5 +  # Base
            expert_importance * 1.0 +  # Importancia del experto
            profile.memory_efficiency * 0.5 +  # Eficiencia
            optimization_prob * 0.5  # Probabilidad de optimización
        )

        return base_capacity * capacity_multiplier

    def _reallocate_expert_memory(self, expert_id: int, new_capacity: int) -> bool:
        """Reasigna memoria para un experto.

        Returns:
            True si la reasignación fue exitosa, False si no hay memoria disponible
        """
        # Verificar si hay suficiente memoria disponible
        current_allocated = sum(profile.memory_capacity for profile in self.liquid_state.expert_profiles.values())
        available_memory = self.total_memory_slots - current_allocated

        # Si estamos reduciendo capacidad, siempre es posible
        old_capacity = self.liquid_state.expert_profiles[expert_id].memory_capacity
        if new_capacity <= old_capacity:
            available_memory += (old_capacity - new_capacity)

        if available_memory < new_capacity:
            logger.warning(f"❌ Memoria insuficiente para reasignar experto {expert_id}: solicitado {new_capacity}, disponible {available_memory}")
            return False

        # Liberar memoria antigua
        old_allocation = self.liquid_state.memory_allocation.get(expert_id)
        if old_allocation is not None:
            # Marcar como disponible (simplificado - en implementación real usaría un allocator)
            pass

        # Asignar nueva memoria desde el pool global
        # Estrategia simple: asignar slots contiguos
        start_idx = (expert_id * self.base_memory_per_expert) % self.total_memory_slots
        end_idx = min(start_idx + new_capacity, self.total_memory_slots)

        if end_idx - start_idx < new_capacity:
            # No hay suficientes slots contiguos, usar estrategia alternativa
            start_idx = 0
            end_idx = new_capacity

        new_allocation = self.global_memory_pool[start_idx:end_idx]
        self.liquid_state.memory_allocation[expert_id] = new_allocation

        # Registrar adaptación
        adaptation_record = {
            "expert_id": expert_id,
            "old_capacity": len(old_allocation) if old_allocation is not None else 0,
            "new_capacity": new_capacity,
            "timestamp": torch.cuda.Event().elapsed_time() if torch.cuda.is_available() else time.time()
        }
        self.liquid_state.adaptation_history.append(adaptation_record)

        logger.info(f"🔄 Memoria reasignada para experto {expert_id}: {new_capacity} slots")
        return True

    def update_memory_utilization(self, expert_id: int, utilization: float):
        """Actualiza la utilización de memoria para un experto."""
        with self.liquid_state.lock:
            self.liquid_state.memory_utilization[expert_id] = utilization

            # Actualizar perfil del experto
            profile = self.liquid_state.expert_profiles[expert_id]
            profile.usage_frequency = 0.9 * profile.usage_frequency + 0.1 * utilization
            profile.memory_efficiency = min(1.0, utilization / 0.8)  # Eficiencia basada en utilización

    def get_expert_memory(self, expert_id: int) -> Optional[torch.Tensor]:
        """Obtiene la memoria asignada para un experto."""
        return self.liquid_state.memory_allocation.get(expert_id)

    def request_memory_spillover(
        self,
        requesting_expert_id: int,
        requested_capacity: int,
        context_embedding: Optional[torch.Tensor] = None
    ) -> Optional[torch.Tensor]:
        """
        Solicita spillover de memoria desde otros expertos usando punteros ligeros.

        Args:
            requesting_expert_id: ID del experto que solicita memoria
            requested_capacity: Capacidad solicitada
            context_embedding: Embedding contextual para optimización

        Returns:
            Memoria spillover o None si no disponible
        """
        with self.liquid_state.lock:
            # Calcular qué expertos pueden donar memoria
            available_donors = self._find_memory_donors(requesting_expert_id, requested_capacity)

            if not available_donors:
                return None

            # Crear punteros de spillover
            spillover_memory = []
            total_spilled = 0

            for donor_id, spill_size in available_donors.items():
                if total_spilled >= requested_capacity:
                    break

                # Crear puntero ligero
                donor_memory = self.liquid_state.memory_allocation.get(donor_id)
                if donor_memory is not None:
                    # Tomar slice de memoria del donante (últimas posiciones menos utilizadas)
                    spill_slice = donor_memory[-spill_size:]

                    spillover_pointer = MemorySpilloverPointer(
                        source_expert_id=donor_id,
                        target_expert_id=requesting_expert_id,
                        memory_slice=spill_slice,
                        spillover_size=spill_size,
                        last_access=time.time(),
                        priority=1.0
                    )

                    # Registrar spillover
                    if requesting_expert_id not in self.liquid_state.spillover_pointers:
                        self.liquid_state.spillover_pointers[requesting_expert_id] = []
                    self.liquid_state.spillover_pointers[requesting_expert_id].append(spillover_pointer)

                    spillover_memory.append(spill_slice)
                    total_spilled += spill_size

                    # Actualizar perfil del donante
                    donor_profile = self.liquid_state.expert_profiles[donor_id]
                    donor_profile.memory_efficiency *= 0.95  # Penalización por compartir

                    logger.debug(f"🔗 Spillover: experto {donor_id} -> {requesting_expert_id}, {spill_size} slots")

            if spillover_memory:
                # Concatenar memoria spillover
                combined_memory = torch.cat(spillover_memory, dim=0)
                logger.info(f"🌊 Memory spillover completado: {total_spilled} slots para experto {requesting_expert_id}")
                return combined_memory

        return None

    def _find_memory_donors(self, requesting_expert_id: int, requested_capacity: int) -> Dict[int, int]:
        """
        Encuentra expertos que pueden donar memoria para spillover.

        Args:
            requesting_expert_id: ID del experto solicitante
            requested_capacity: Capacidad solicitada

        Returns:
            Dict[donor_id, spill_size]
        """
        donors = {}
        remaining_needed = requested_capacity

        # Calcular prioridades de donación basadas en eficiencia y utilización
        donor_priorities = []
        for expert_id, profile in self.liquid_state.expert_profiles.items():
            if expert_id == requesting_expert_id:
                continue

            utilization = self.liquid_state.memory_utilization.get(expert_id, 0.0)
            current_capacity = profile.memory_capacity

            # Solo considerar expertos con baja utilización (< 70%)
            if utilization < 0.7 and current_capacity > self.base_memory_per_expert:
                # Prioridad = eficiencia * (1 - utilización) * capacidad disponible
                available_capacity = current_capacity - int(current_capacity * utilization)
                priority = profile.memory_efficiency * (1 - utilization) * min(available_capacity, current_capacity // 4)
                donor_priorities.append((expert_id, priority, available_capacity))

        # Ordenar por prioridad descendente
        donor_priorities.sort(key=lambda x: x[1], reverse=True)

        # Asignar spillover
        for expert_id, priority, available_capacity in donor_priorities:
            if remaining_needed <= 0:
                break

            # Donar máximo 25% de capacidad disponible o lo que se necesite
            spill_size = min(
                available_capacity // 4,  # Máximo 25%
                remaining_needed,
                self.base_memory_per_expert // 2  # Máximo medio base
            )

            if spill_size > 0:
                donors[expert_id] = spill_size
                remaining_needed -= spill_size

        return donors

    def release_memory_spillover(self, expert_id: int):
        """
        Libera punteros de spillover para un experto.

        Args:
            expert_id: ID del experto
        """
        with self.liquid_state.lock:
            if expert_id in self.liquid_state.spillover_pointers:
                spillover_count = len(self.liquid_state.spillover_pointers[expert_id])

                # Restaurar eficiencia de donantes
                for pointer in self.liquid_state.spillover_pointers[expert_id]:
                    donor_profile = self.liquid_state.expert_profiles[pointer.source_expert_id]
                    donor_profile.memory_efficiency = min(1.0, donor_profile.memory_efficiency * 1.05)  # Bonus por liberar

                # Limpiar punteros
                self.liquid_state.spillover_pointers[expert_id].clear()

                logger.info(f"🔄 Liberado spillover para experto {expert_id}: {spillover_count} punteros")

    def get_spillover_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas de spillover de memoria.

        Returns:
            Estadísticas de spillover
        """
        with self.liquid_state.lock:
            total_spillovers = sum(len(pointers) for pointers in self.liquid_state.spillover_pointers.values())
            total_spilled_memory = 0
            active_experts_with_spillover = 0

            for expert_id, pointers in self.liquid_state.spillover_pointers.items():
                if pointers:
                    active_experts_with_spillover += 1
                    total_spilled_memory += sum(p.spillover_size for p in pointers)

            return {
                "total_spillovers": total_spillovers,
                "total_spilled_memory_slots": total_spilled_memory,
                "active_experts_with_spillover": active_experts_with_spillover,
                "spillover_efficiency": total_spilled_memory / (self.total_memory_slots * 0.1) if self.total_memory_slots > 0 else 0
            }

    def optimize_memory_allocation(self):
        """Optimiza la asignación global de memoria."""
        with self.liquid_state.lock:
            # Calcular utilización total
            total_utilization = sum(self.liquid_state.memory_utilization.values())

            if total_utilization > self.total_memory_slots * 0.9:  # 90% utilizado
                # Trigger rebalance
                self._rebalance_memory()

    def _rebalance_memory(self):
        """Rebalancea la memoria entre expertos basado en utilización."""
        # Calcular prioridades basadas en frecuencia de uso y eficiencia
        priorities = {}
        for expert_id, profile in self.liquid_state.expert_profiles.items():
            utilization = self.liquid_state.memory_utilization.get(expert_id, 0.0)
            priority = (
                profile.usage_frequency * 0.6 +
                profile.memory_efficiency * 0.3 +
                profile.specialization_score * 0.1
            )
            priorities[expert_id] = priority

        # Normalizar prioridades
        total_priority = sum(priorities.values())
        if total_priority > 0:
            for expert_id in priorities:
                priorities[expert_id] /= total_priority

        # Reasignar basado en prioridades
        for expert_id, priority in priorities.items():
            target_capacity = int(priority * self.total_memory_slots * 0.8)  # 80% del total
            target_capacity = max(self.base_memory_per_expert // 2, min(target_capacity, self.base_memory_per_expert * 3))

            current_capacity = self.liquid_state.expert_profiles[expert_id].memory_capacity
            if abs(target_capacity - current_capacity) > self.base_memory_per_expert * 0.2:  # 20% de cambio
                self._reallocate_expert_memory(expert_id, target_capacity)

        logger.info("⚖️ Memoria rebalanceada basado en prioridades de expertos")

    def get_memory_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del sistema de memoria líquida."""
        with self.liquid_state.lock:
            total_allocated = sum(profile.memory_capacity for profile in self.liquid_state.expert_profiles.values())
            total_utilized = sum(self.liquid_state.memory_utilization.values())

            expert_stats = {}
            for expert_id, profile in self.liquid_state.expert_profiles.items():
                utilization = self.liquid_state.memory_utilization.get(expert_id, 0.0)
                expert_stats[f"expert_{expert_id}"] = {
                    "domain": profile.domain_specialization,
                    "capacity": profile.memory_capacity,
                    "utilization": utilization,
                    "efficiency": profile.memory_efficiency,
                    "usage_frequency": profile.usage_frequency,
                    "specialization_score": profile.specialization_score
                }

            spillover_stats = self.get_spillover_stats()

            return {
                "total_memory_slots": self.total_memory_slots,
                "total_allocated": total_allocated,
                "total_utilized": total_utilized,
                "allocation_efficiency": total_utilized / total_allocated if total_allocated > 0 else 0,
                "num_experts": self.num_experts,
                "num_adaptations": len(self.liquid_state.adaptation_history),
                "spillover_stats": spillover_stats,
                "expert_stats": expert_stats
            }


class LiquidMemoryMIRASBlock(nn.Module):
    """
    Bloque MIRAS integrado con memoria líquida.
    Combina MIRAS con asignación dinámica de memoria por experto.
    """

    def __init__(
        self,
        liquid_memory_manager: LiquidMemoryManager,
        expert_id: int,
        hidden_size: int,
        num_heads: int = 8,
        dropout: float = 0.1
    ):
        super().__init__()
        self.liquid_memory_manager = liquid_memory_manager
        self.expert_id = expert_id
        self.hidden_size = hidden_size

        # Crear bloque MIRAS especializado para este experto
        self.miras_block = create_miras_block(
            hidden_size=hidden_size,
            num_heads=num_heads,
            memory_size=liquid_memory_manager.base_memory_per_expert,
            dropout=dropout,
            expert_id=expert_id,
            num_experts=liquid_memory_manager.num_experts
        )

        # Conectar con memoria líquida
        self.miras_block.expert_memory_buffer = liquid_memory_manager.global_memory_pool

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        context_embedding: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Forward pass con memoria líquida.

        Args:
            hidden_states: Estados ocultos
            attention_mask: Máscara de atención
            context_embedding: Embedding contextual para optimización de memoria

        Returns:
            hidden_states_updated, aux_info
        """
        # Optimizar asignación de memoria basada en contexto
        if context_embedding is not None:
            expert_memory = self.liquid_memory_manager.allocate_expert_memory(
                self.expert_id, self.miras_block.memory_size, context_embedding
            )
            # Actualizar el bloque MIRAS con la nueva memoria
            self.miras_block.expert_memory_buffer = self.liquid_memory_manager.global_memory_pool

        # Ejecutar MIRAS
        output, aux_info = self.miras_block(
            hidden_states=hidden_states,
            attention_mask=attention_mask
        )

        # Actualizar estadísticas de utilización
        memory_utilization = aux_info.get('memory_utilization', 0.0)
        self.liquid_memory_manager.update_memory_utilization(self.expert_id, memory_utilization)

        # Añadir información de memoria líquida
        aux_info['liquid_memory'] = {
            'expert_id': self.expert_id,
            'memory_capacity': self.liquid_memory_manager.liquid_state.expert_profiles[self.expert_id].memory_capacity,
            'allocation_optimized': context_embedding is not None
        }

        return output, aux_info


def create_liquid_memory_manager(
    num_experts: int,
    hidden_size: int,
    total_memory_slots: int = 4096,
    base_memory_per_expert: int = 256,
    adaptation_rate: float = 0.01,
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
) -> LiquidMemoryManager:
    """
    Factory function para crear un administrador de memoria líquida.

    Args:
        num_experts: Número de expertos
        hidden_size: Dimensión oculta
        total_memory_slots: Slots totales de memoria
        base_memory_per_expert: Memoria base por experto
        adaptation_rate: Tasa de adaptación
        device: Dispositivo

    Returns:
        LiquidMemoryManager instance
    """
    return LiquidMemoryManager(
        num_experts=num_experts,
        hidden_size=hidden_size,
        total_memory_slots=total_memory_slots,
        base_memory_per_expert=base_memory_per_expert,
        adaptation_rate=adaptation_rate,
        device=device
    )


def create_liquid_memory_miras_block(
    liquid_memory_manager: LiquidMemoryManager,
    expert_id: int,
    hidden_size: int,
    num_heads: int = 8,
    dropout: float = 0.1
) -> LiquidMemoryMIRASBlock:
    """
    Factory function para crear un bloque MIRAS con memoria líquida.

    Args:
        liquid_memory_manager: Administrador de memoria líquida
        expert_id: ID del experto
        hidden_size: Dimensión oculta
        num_heads: Número de cabezas de atención
        dropout: Tasa de dropout

    Returns:
        LiquidMemoryMIRASBlock instance
    """
    return LiquidMemoryMIRASBlock(
        liquid_memory_manager=liquid_memory_manager,
        expert_id=expert_id,
        hidden_size=hidden_size,
        num_heads=num_heads,
        dropout=dropout
    )