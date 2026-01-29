#!/usr/bin/env python3
"""
Memory Marketplace - Sistema de trading para slots de memoria premium
Permite a los nodos comprar/vender acceso a memoria distribuida con DRACMA tokens.
"""

import asyncio
import uuid
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..core.logging import get_logger
from ..core.config import get_config

logger = get_logger(__name__)


class MemorySlotType(Enum):
    """Tipos de slots de memoria disponibles."""
    STANDARD = "standard"      # Memoria estándar
    PREMIUM = "premium"        # Memoria de alta velocidad
    PERSISTENT = "persistent"  # Memoria persistente
    SECURE = "secure"          # Memoria encriptada


class ListingStatus(Enum):
    """Estados de los listings en el marketplace."""
    ACTIVE = "active"
    SOLD = "sold"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class MemorySlot:
    """Representa un slot de memoria disponible para trading."""
    slot_id: str
    owner_node_id: str
    slot_type: MemorySlotType
    capacity_gb: float
    bandwidth_mbps: int
    latency_ms: int
    uptime_guarantee: float  # 0.0-1.0
    security_level: str      # "basic", "encrypted", "zkp_verified"
    location: str           # Región geográfica
    price_per_hour: float   # Precio en DRACMA por hora
    min_duration_hours: int
    max_duration_hours: int
    created_at: datetime
    expires_at: datetime
    status: ListingStatus = ListingStatus.ACTIVE


@dataclass
class MemoryLease:
    """Representa un contrato de alquiler de memoria."""
    lease_id: str
    buyer_node_id: str
    seller_node_id: str
    slot_id: str
    duration_hours: int
    total_price: float
    start_time: datetime
    end_time: datetime
    status: str  # "active", "completed", "cancelled", "disputed"
    performance_metrics: Dict[str, Any] = None


class MemoryMarketplace:
    """
    Marketplace para trading de slots de memoria premium.
    Gestiona listings, transacciones y contratos de memoria distribuida.
    """

    def __init__(self, config=None):
        self.config = config or get_config()
        self.logger = logger

        # Configuración del marketplace
        self.listing_fee = self.config.get('memory_marketplace_listing_fee', 0.1)  # DRACMA por listing
        self.transaction_fee = self.config.get('memory_marketplace_transaction_fee', 0.02)  # 2% fee
        self.max_listing_duration_days = self.config.get('max_listing_duration_days', 30)
        self.min_listing_price = self.config.get('min_listing_price', 0.01)  # DRACMA/hora

        # Estado del marketplace
        self.memory_slots: Dict[str, MemorySlot] = {}
        self.active_leases: Dict[str, MemoryLease] = {}
        self.market_stats: Dict[str, Any] = {
            'total_listings': 0,
            'active_listings': 0,
            'total_volume': 0.0,
            'total_fees_collected': 0.0,
            'avg_price_per_gb_hour': 0.0
        }

        # Cache de precios y demanda
        self.price_history: List[Dict[str, Any]] = []
        self.demand_indicators: Dict[str, float] = {}

        logger.info("🧠 Memory Marketplace initialized")

    async def create_memory_listing(self, owner_node_id: str, slot_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear un nuevo listing de slot de memoria.

        Args:
            owner_node_id: ID del nodo propietario
            slot_config: Configuración del slot de memoria

        Returns:
            Resultado de la creación del listing
        """
        try:
            # Validar configuración
            validation_result = self._validate_slot_config(slot_config)
            if not validation_result['valid']:
                return {'success': False, 'error': validation_result['error']}

            # Generar ID único para el slot
            slot_id = f"mem_slot_{uuid.uuid4().hex}"

            # Crear objeto MemorySlot
            memory_slot = MemorySlot(
                slot_id=slot_id,
                owner_node_id=owner_node_id,
                slot_type=MemorySlotType(slot_config['type']),
                capacity_gb=slot_config['capacity_gb'],
                bandwidth_mbps=slot_config['bandwidth_mbps'],
                latency_ms=slot_config['latency_ms'],
                uptime_guarantee=slot_config['uptime_guarantee'],
                security_level=slot_config['security_level'],
                location=slot_config['location'],
                price_per_hour=slot_config['price_per_hour'],
                min_duration_hours=slot_config['min_duration_hours'],
                max_duration_hours=slot_config['max_duration_hours'],
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=slot_config.get('listing_duration_days', 7))
            )

            # Verificar precio mínimo
            if memory_slot.price_per_hour < self.min_listing_price:
                return {'success': False, 'error': f'Price too low. Minimum: {self.min_listing_price} DRACMA/hour'}

            # Almacenar slot
            self.memory_slots[slot_id] = memory_slot
            self.market_stats['total_listings'] += 1
            self.market_stats['active_listings'] += 1

            # Actualizar estadísticas de precios
            self._update_price_statistics(memory_slot)

            self.logger.info(f"📦 Created memory listing: {slot_id} by {owner_node_id} - "
                           f"{memory_slot.capacity_gb}GB @ {memory_slot.price_per_hour} DRACMA/hour")

            return {
                'success': True,
                'slot_id': slot_id,
                'listing_fee': self.listing_fee,
                'expires_at': memory_slot.expires_at.isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error creating memory listing for {owner_node_id}: {e}")
            return {'success': False, 'error': str(e)}

    def _validate_slot_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validar configuración del slot de memoria."""
        required_fields = [
            'type', 'capacity_gb', 'bandwidth_mbps', 'latency_ms',
            'uptime_guarantee', 'security_level', 'location',
            'price_per_hour', 'min_duration_hours', 'max_duration_hours'
        ]

        for field in required_fields:
            if field not in config:
                return {'valid': False, 'error': f'Missing required field: {field}'}

        # Validar tipos
        if config['type'] not in [t.value for t in MemorySlotType]:
            return {'valid': False, 'error': f'Invalid slot type: {config["type"]}'}

        if not (0.1 <= config['capacity_gb'] <= 1000):
            return {'valid': False, 'error': 'Capacity must be between 0.1GB and 1000GB'}

        if not (1 <= config['bandwidth_mbps'] <= 10000):
            return {'valid': False, 'error': 'Bandwidth must be between 1Mbps and 10000Mbps'}

        if not (1 <= config['latency_ms'] <= 1000):
            return {'valid': False, 'error': 'Latency must be between 1ms and 1000ms'}

        if not (0.5 <= config['uptime_guarantee'] <= 1.0):
            return {'valid': False, 'error': 'Uptime guarantee must be between 0.5 and 1.0'}

        if config['price_per_hour'] <= 0:
            return {'valid': False, 'error': 'Price per hour must be positive'}

        return {'valid': True}

    async def purchase_memory_slot(self, buyer_node_id: str, slot_id: str,
                                 duration_hours: int) -> Dict[str, Any]:
        """
        Comprar un slot de memoria por duración específica.

        Args:
            buyer_node_id: ID del nodo comprador
            slot_id: ID del slot a comprar
            duration_hours: Duración del alquiler en horas

        Returns:
            Resultado de la compra
        """
        try:
            # Verificar que el slot existe y está disponible
            if slot_id not in self.memory_slots:
                return {'success': False, 'error': 'Memory slot not found'}

            memory_slot = self.memory_slots[slot_id]

            if memory_slot.status != ListingStatus.ACTIVE:
                return {'success': False, 'error': 'Memory slot not available'}

            if memory_slot.owner_node_id == buyer_node_id:
                return {'success': False, 'error': 'Cannot purchase your own memory slot'}

            # Validar duración
            if not (memory_slot.min_duration_hours <= duration_hours <= memory_slot.max_duration_hours):
                return {
                    'success': False,
                    'error': f'Duration must be between {memory_slot.min_duration_hours} and {memory_slot.max_duration_hours} hours'
                }

            # Calcular precio total
            base_price = memory_slot.price_per_hour * duration_hours
            transaction_fee = base_price * self.transaction_fee
            total_price = base_price + transaction_fee

            # Verificar límite de tiempo del listing
            if datetime.now() > memory_slot.expires_at:
                memory_slot.status = ListingStatus.EXPIRED
                return {'success': False, 'error': 'Memory slot listing has expired'}

            # Crear contrato de lease
            lease_id = f"lease_{uuid.uuid4().hex}"
            lease = MemoryLease(
                lease_id=lease_id,
                buyer_node_id=buyer_node_id,
                seller_node_id=memory_slot.owner_node_id,
                slot_id=slot_id,
                duration_hours=duration_hours,
                total_price=total_price,
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(hours=duration_hours),
                status="active"
            )

            # Almacenar lease
            self.active_leases[lease_id] = lease

            # Marcar slot como vendido (temporalmente)
            memory_slot.status = ListingStatus.SOLD

            # Actualizar estadísticas del mercado
            self.market_stats['total_volume'] += total_price
            self.market_stats['total_fees_collected'] += transaction_fee

            self.logger.info(f"💰 Memory slot purchased: {slot_id} by {buyer_node_id} - "
                           f"{duration_hours}h @ {total_price:.4f} DRACMA")

            return {
                'success': True,
                'lease_id': lease_id,
                'total_price': total_price,
                'transaction_fee': transaction_fee,
                'start_time': lease.start_time.isoformat(),
                'end_time': lease.end_time.isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error purchasing memory slot {slot_id}: {e}")
            return {'success': False, 'error': str(e)}

    async def complete_memory_lease(self, lease_id: str, performance_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Completar un contrato de alquiler de memoria.

        Args:
            lease_id: ID del contrato
            performance_metrics: Métricas de rendimiento durante el alquiler

        Returns:
            Resultado de la finalización
        """
        try:
            if lease_id not in self.active_leases:
                return {'success': False, 'error': 'Lease not found'}

            lease = self.active_leases[lease_id]

            if lease.status != "active":
                return {'success': False, 'error': 'Lease is not active'}

            # Verificar que el lease haya expirado
            if datetime.now() < lease.end_time:
                return {'success': False, 'error': 'Lease has not expired yet'}

            # Almacenar métricas de rendimiento
            lease.performance_metrics = performance_metrics
            lease.status = "completed"

            # Liberar el slot para nuevos alquileres
            memory_slot = self.memory_slots.get(lease.slot_id)
            if memory_slot:
                memory_slot.status = ListingStatus.ACTIVE

            # Calcular calificación del vendedor basada en métricas
            seller_rating = self._calculate_seller_rating(performance_metrics)

            self.logger.info(f"✅ Memory lease completed: {lease_id} - Rating: {seller_rating:.2f}")

            return {
                'success': True,
                'lease_id': lease_id,
                'seller_rating': seller_rating,
                'performance_metrics': performance_metrics
            }

        except Exception as e:
            self.logger.error(f"Error completing memory lease {lease_id}: {e}")
            return {'success': False, 'error': str(e)}

    def _calculate_seller_rating(self, metrics: Dict[str, Any]) -> float:
        """Calcular calificación del vendedor basada en métricas de rendimiento."""
        try:
            uptime_achieved = metrics.get('uptime_percentage', 0.0)
            latency_avg = metrics.get('avg_latency_ms', 1000)
            bandwidth_util = metrics.get('bandwidth_utilization', 0.0)
            data_integrity = metrics.get('data_integrity_score', 0.0)

            # Puntuación compuesta (0-5 escala)
            uptime_score = min(uptime_achieved * 5, 5.0)
            latency_score = max(0, 5.0 - (latency_avg / 200))  # Penalización por latencia alta
            bandwidth_score = bandwidth_util * 5.0
            integrity_score = data_integrity * 5.0

            total_score = (uptime_score + latency_score + bandwidth_score + integrity_score) / 4.0

            return round(total_score, 2)

        except Exception:
            return 3.0  # Puntuación neutral por defecto

    def search_memory_slots(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Buscar slots de memoria disponibles con filtros.

        Args:
            filters: Criterios de búsqueda

        Returns:
            Lista de slots que coinciden con los filtros
        """
        try:
            available_slots = [
                slot for slot in self.memory_slots.values()
                if slot.status == ListingStatus.ACTIVE and datetime.now() < slot.expires_at
            ]

            # Aplicar filtros
            filtered_slots = []
            for slot in available_slots:
                if self._matches_filters(slot, filters):
                    filtered_slots.append({
                        'slot_id': slot.slot_id,
                        'owner_node_id': slot.owner_node_id,
                        'slot_type': slot.slot_type.value,
                        'capacity_gb': slot.capacity_gb,
                        'bandwidth_mbps': slot.bandwidth_mbps,
                        'latency_ms': slot.latency_ms,
                        'uptime_guarantee': slot.uptime_guarantee,
                        'security_level': slot.security_level,
                        'location': slot.location,
                        'price_per_hour': slot.price_per_hour,
                        'min_duration_hours': slot.min_duration_hours,
                        'max_duration_hours': slot.max_duration_hours,
                        'expires_at': slot.expires_at.isoformat()
                    })

            # Ordenar por precio (más bajo primero)
            filtered_slots.sort(key=lambda x: x['price_per_hour'])

            return filtered_slots

        except Exception as e:
            self.logger.error(f"Error searching memory slots: {e}")
            return []

    def _matches_filters(self, slot: MemorySlot, filters: Dict[str, Any]) -> bool:
        """Verificar si un slot coincide con los filtros."""
        try:
            # Filtro por tipo
            if 'slot_type' in filters and slot.slot_type.value != filters['slot_type']:
                return False

            # Filtro por capacidad mínima
            if 'min_capacity_gb' in filters and slot.capacity_gb < filters['min_capacity_gb']:
                return False

            # Filtro por precio máximo
            if 'max_price_per_hour' in filters and slot.price_per_hour > filters['max_price_per_hour']:
                return False

            # Filtro por ubicación
            if 'location' in filters and slot.location != filters['location']:
                return False

            # Filtro por nivel de seguridad
            if 'security_level' in filters and slot.security_level != filters['security_level']:
                return False

            # Filtro por uptime guarantee
            if 'min_uptime' in filters and slot.uptime_guarantee < filters['min_uptime']:
                return False

            return True

        except Exception:
            return False

    def get_market_statistics(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del mercado de memoria.

        Returns:
            Estadísticas del marketplace
        """
        try:
            # Calcular estadísticas adicionales
            active_slots = [s for s in self.memory_slots.values() if s.status == ListingStatus.ACTIVE]

            if active_slots:
                avg_price = sum(s.price_per_hour for s in active_slots) / len(active_slots)
                min_price = min(s.price_per_hour for s in active_slots)
                max_price = max(s.price_per_hour for s in active_slots)

                # Precio por GB/hora
                avg_price_per_gb = sum(s.price_per_hour / s.capacity_gb for s in active_slots) / len(active_slots)
            else:
                avg_price = min_price = max_price = avg_price_per_gb = 0.0

            # Estadísticas por tipo
            type_distribution = {}
            for slot_type in MemorySlotType:
                count = sum(1 for s in active_slots if s.slot_type == slot_type)
                type_distribution[slot_type.value] = count

            stats = self.market_stats.copy()
            stats.update({
                'avg_price_per_hour': round(avg_price, 4),
                'min_price_per_hour': round(min_price, 4),
                'max_price_per_hour': round(max_price, 4),
                'avg_price_per_gb_hour': round(avg_price_per_gb, 4),
                'slot_type_distribution': type_distribution,
                'active_leases': len([l for l in self.active_leases.values() if l.status == "active"]),
                'total_capacity_gb': sum(s.capacity_gb for s in active_slots),
                'last_updated': datetime.now().isoformat()
            })

            return stats

        except Exception as e:
            self.logger.error(f"Error getting market statistics: {e}")
            return {'error': str(e)}

    def _update_price_statistics(self, new_slot: MemorySlot):
        """Actualizar estadísticas de precios con nuevo listing."""
        try:
            self.price_history.append({
                'timestamp': datetime.now(),
                'slot_type': new_slot.slot_type.value,
                'price_per_hour': new_slot.price_per_hour,
                'capacity_gb': new_slot.capacity_gb,
                'location': new_slot.location
            })

            # Mantener solo últimas 1000 entradas
            if len(self.price_history) > 1000:
                self.price_history = self.price_history[-1000:]

        except Exception as e:
            self.logger.error(f"Error updating price statistics: {e}")

    def cancel_memory_listing(self, owner_node_id: str, slot_id: str) -> Dict[str, Any]:
        """
        Cancelar un listing de memoria.

        Args:
            owner_node_id: ID del propietario
            slot_id: ID del slot

        Returns:
            Resultado de la cancelación
        """
        try:
            if slot_id not in self.memory_slots:
                return {'success': False, 'error': 'Memory slot not found'}

            memory_slot = self.memory_slots[slot_id]

            if memory_slot.owner_node_id != owner_node_id:
                return {'success': False, 'error': 'Not authorized to cancel this listing'}

            if memory_slot.status != ListingStatus.ACTIVE:
                return {'success': False, 'error': 'Listing is not active'}

            memory_slot.status = ListingStatus.CANCELLED
            self.market_stats['active_listings'] = max(0, self.market_stats['active_listings'] - 1)

            self.logger.info(f"❌ Memory listing cancelled: {slot_id} by {owner_node_id}")

            return {'success': True, 'slot_id': slot_id}

        except Exception as e:
            self.logger.error(f"Error cancelling memory listing {slot_id}: {e}")
            return {'success': False, 'error': str(e)}

    def get_user_memory_leases(self, node_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Obtener contratos de memoria para un usuario (como comprador y vendedor).

        Args:
            node_id: ID del nodo

        Returns:
            Contratos como comprador y vendedor
        """
        try:
            buyer_leases = []
            seller_leases = []

            for lease in self.active_leases.values():
                if lease.buyer_node_id == node_id:
                    buyer_leases.append({
                        'lease_id': lease.lease_id,
                        'slot_id': lease.slot_id,
                        'seller_node_id': lease.seller_node_id,
                        'duration_hours': lease.duration_hours,
                        'total_price': lease.total_price,
                        'start_time': lease.start_time.isoformat(),
                        'end_time': lease.end_time.isoformat(),
                        'status': lease.status
                    })
                elif lease.seller_node_id == node_id:
                    seller_leases.append({
                        'lease_id': lease.lease_id,
                        'slot_id': lease.slot_id,
                        'buyer_node_id': lease.buyer_node_id,
                        'duration_hours': lease.duration_hours,
                        'total_price': lease.total_price,
                        'start_time': lease.start_time.isoformat(),
                        'end_time': lease.end_time.isoformat(),
                        'status': lease.status
                    })

            return {
                'as_buyer': buyer_leases,
                'as_seller': seller_leases
            }

        except Exception as e:
            self.logger.error(f"Error getting user memory leases for {node_id}: {e}")
            return {'as_buyer': [], 'as_seller': []}


# Funciones de conveniencia
def create_memory_marketplace(config=None) -> MemoryMarketplace:
    """Crear una nueva instancia del marketplace de memoria."""
    return MemoryMarketplace(config)


async def get_memory_slot_price_estimate(slot_config: Dict[str, Any], market_data: Dict[str, Any]) -> float:
    """
    Estimar precio óptimo para un slot de memoria basado en datos del mercado.

    Args:
        slot_config: Configuración del slot
        market_data: Datos actuales del mercado

    Returns:
        Precio estimado por hora en DRACMA
    """
    try:
        # Lógica simple de estimación de precios basada en oferta/demanda
        base_price = 0.05  # Precio base

        # Ajustes por características
        capacity_multiplier = min(slot_config.get('capacity_gb', 1) / 10, 5.0)
        bandwidth_bonus = min(slot_config.get('bandwidth_mbps', 100) / 1000, 2.0)
        latency_penalty = max(0, 1.0 - (slot_config.get('latency_ms', 100) / 500))

        # Ajuste por demanda del mercado
        demand_multiplier = market_data.get('demand_multiplier', 1.0)

        estimated_price = base_price * capacity_multiplier * (1 + bandwidth_bonus) * (1 + latency_penalty) * demand_multiplier

        return round(estimated_price, 4)

    except Exception:
        return 0.05  # Precio por defecto</content>
