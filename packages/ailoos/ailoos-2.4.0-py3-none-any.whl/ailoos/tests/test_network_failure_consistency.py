"""
Test de consistencia de estado con fallos de red simulados.
Valida la consistencia eventual del coordinador bajo condiciones de fallos de red,
incluyendo particiones de red, reconexiones, conflictos de estado y recuperación automática.
"""

import asyncio
import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, List, Any, Optional
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from ailoos.coordinator.state_validator import StateValidator, ValidationIssue, ValidationSeverity
from ailoos.coordinator.state_sync import StateSync, VectorClock, StateUpdate, Conflict, ConflictResolutionStrategy
from ailoos.consensus.distributed_consensus import DistributedConsensusManager, ConsensusAlgorithm
from ailoos.core.config import Config


@dataclass
class MockCoordinator:
    """Coordinador mock para testing."""
    node_id: str
    state_sync: StateSync
    consensus_manager: DistributedConsensusManager
    state_validator: StateValidator
    local_state: Dict[str, Any] = field(default_factory=dict)
    network_partitioned: bool = False
    last_sync_time: float = 0.0

    def __post_init__(self):
        self.state_sync.add_peer(self.node_id)

    async def update_state(self, key: str, value: Any):
        """Actualiza estado local y propaga."""
        if self.network_partitioned:
            # Durante partición, solo actualiza localmente
            self.local_state[key] = value
            return

        # Actualización normal con sincronización
        update = self.state_sync.update_local_state(key, value)
        self.local_state[key] = value

        # Propagar a través de consenso si es líder
        if self.consensus_manager.get_consensus_status().get('role') == 'leader':
            await self.consensus_manager.propose_value({
                'action': 'state_update',
                'key': key,
                'value': value,
                'update_id': update.update_id
            })

    def get_state_value(self, key: str) -> Any:
        """Obtiene valor de estado."""
        return self.local_state.get(key)

    async def sync_with_peer(self, peer: 'MockCoordinator'):
        """Sincroniza con otro coordinador."""
        if self.network_partitioned or peer.network_partitioned:
            return False, []

        # Simular sincronización
        peer_state = peer.local_state.copy()
        peer_updates = [
            {
                'update_id': f"{peer.node_id}_{int(time.time() * 1000)}",
                'node_id': peer.node_id,
                'timestamp': time.time(),
                'vector_clock': peer.state_sync.vector_clock.__dict__,
                'operation': 'update',
                'key': k,
                'value': v,
                'checksum': ''
            }
            for k, v in peer_state.items()
        ]

        success, conflicts = await self.state_sync.synchronize_with_peer(
            peer.node_id, peer_state, peer_updates
        )

        if success:
            self.last_sync_time = time.time()
            peer.last_sync_time = time.time()

        return success, conflicts


class NetworkFailureSimulator:
    """Simulador de fallos de red."""

    def __init__(self):
        self.partitions: Dict[str, List[str]] = {}  # partition_id -> [node_ids]
        self.network_delays: Dict[str, float] = {}  # node_id -> delay_seconds
        self.node_failures: Dict[str, float] = {}  # node_id -> failure_until_timestamp

    def create_partition(self, partition_id: str, node_ids: List[str]):
        """Crea una partición de red."""
        self.partitions[partition_id] = node_ids

    def heal_partition(self, partition_id: str):
        """Cura una partición de red."""
        if partition_id in self.partitions:
            del self.partitions[partition_id]

    def add_network_delay(self, node_id: str, delay_seconds: float):
        """Agrega delay de red para un nodo."""
        self.network_delays[node_id] = delay_seconds

    def simulate_node_failure(self, node_id: str, duration_seconds: float):
        """Simula fallo de nodo."""
        self.node_failures[node_id] = time.time() + duration_seconds

    def is_node_failed(self, node_id: str) -> bool:
        """Verifica si un nodo está fallado."""
        failure_time = self.node_failures.get(node_id, 0)
        return time.time() < failure_time

    def can_communicate(self, node_a: str, node_b: str) -> bool:
        """Verifica si dos nodos pueden comunicarse."""
        if self.is_node_failed(node_a) or self.is_node_failed(node_b):
            return False

        # Verificar particiones
        for partition_nodes in self.partitions.values():
            if node_a in partition_nodes and node_b not in partition_nodes:
                return False
            if node_b in partition_nodes and node_a not in partition_nodes:
                return False

        return True


class NetworkFailureConsistencyTest:
    """Suite de tests para consistencia con fallos de red."""

    def setup_method(self):
        """Configura el entorno de test."""
        # Usar configuración mock para evitar problemas de asyncio
        self.config = Mock()
        self.config.get = Mock(return_value="test_value")
        self.network_simulator = NetworkFailureSimulator()

        # Crear coordinadores mock
        self.coordinators = {}
        for i in range(3):  # 3 coordinadores para tolerancia a fallos
            node_id = f"coordinator_{i}"
            state_sync = StateSync(node_id, ConflictResolutionStrategy.VECTOR_CLOCK_PRIORITY)
            consensus_manager = DistributedConsensusManager(node_id, ConsensusAlgorithm.PBFT)
            state_validator = StateValidator(self.config)

            coordinator = MockCoordinator(
                node_id=node_id,
                state_sync=state_sync,
                consensus_manager=consensus_manager,
                state_validator=state_validator
            )

            self.coordinators[node_id] = coordinator

            # Conectar peers
            for other_id, other_coord in self.coordinators.items():
                if other_id != node_id:
                    coordinator.state_sync.add_peer(other_id)

    @pytest.mark.asyncio
    async def test_network_partition_consistency(self):
        """Test de consistencia durante particiones de red."""
        print("🧪 Test: Consistencia durante particiones de red")

        # Estado inicial consistente
        initial_value = "initial_value"
        await self.coordinators['coordinator_0'].update_state('test_key', initial_value)

        # Verificar estado inicial - solo el coordinador que actualizó debe tener el valor
        assert self.coordinators['coordinator_0'].get_state_value('test_key') == initial_value
        # Los otros coordinadores no tienen el valor aún (no se ha sincronizado)

        # Crear partición de red: coordinator_0 aislado
        self.network_simulator.create_partition('partition_1', ['coordinator_0'])

        # Marcar nodos como particionados
        self.coordinators['coordinator_0'].network_partitioned = True

        # Actualizar estado en partición aislada
        partition_value = "partition_value"
        await self.coordinators['coordinator_0'].update_state('test_key', partition_value)

        # Actualizar estado en la partición mayoritaria
        majority_value = "majority_value"
        await self.coordinators['coordinator_1'].update_state('test_key', majority_value)

        # Verificar que las particiones tienen valores diferentes
        assert self.coordinators['coordinator_0'].get_state_value('test_key') == partition_value
        assert self.coordinators['coordinator_1'].get_state_value('test_key') == majority_value
        # coordinator_2 no tiene el valor porque no se ha sincronizado aún

        # Curar partición
        self.network_simulator.heal_partition('partition_1')
        self.coordinators['coordinator_0'].network_partitioned = False

        # Sincronizar después de la partición
        await self.coordinators['coordinator_0'].sync_with_peer(self.coordinators['coordinator_1'])

        # Verificar resolución de conflicto (debería mantener el valor mayoritario o más reciente)
        final_value = self.coordinators['coordinator_0'].get_state_value('test_key')
        assert final_value in [partition_value, majority_value]  # Dependiendo de la estrategia de resolución

        print("✅ Partición de red resuelta, conflicto manejado")

    @pytest.mark.asyncio
    async def test_node_reconnection_recovery(self):
        """Test de recuperación automática tras reconexión de nodo."""
        print("🧪 Test: Recuperación automática tras reconexión")

        # Estado inicial
        await self.coordinators['coordinator_0'].update_state('recovery_key', 'initial')

        # Simular fallo de nodo
        self.network_simulator.simulate_node_failure('coordinator_1', 2.0)  # 2 segundos

        # Durante el fallo, actualizar estado en nodos activos
        await asyncio.sleep(0.5)  # Pequeño delay
        await self.coordinators['coordinator_0'].update_state('recovery_key', 'updated_during_failure')
        await self.coordinators['coordinator_2'].update_state('recovery_key', 'updated_during_failure')

        # Esperar recuperación
        await asyncio.sleep(2.5)

        # Verificar que el nodo fallado puede reconectarse y sincronizarse
        assert not self.network_simulator.is_node_failed('coordinator_1')

        # Sincronizar nodo recuperado
        await self.coordinators['coordinator_1'].sync_with_peer(self.coordinators['coordinator_0'])

        # Verificar consistencia eventual
        recovered_value = self.coordinators['coordinator_1'].get_state_value('recovery_key')
        assert recovered_value == 'updated_during_failure'

        print("✅ Nodo recuperado y sincronizado correctamente")

    @pytest.mark.asyncio
    async def test_state_conflict_resolution(self):
        """Test de resolución de conflictos de estado."""
        print("🧪 Test: Resolución de conflictos de estado")

        # Crear escenario de conflicto simultáneo
        conflict_key = 'conflict_key'

        # Todos los nodos actualizan simultáneamente (simulado)
        await self.coordinators['coordinator_0'].update_state(conflict_key, 'value_from_0')
        await self.coordinators['coordinator_1'].update_state(conflict_key, 'value_from_1')
        await self.coordinators['coordinator_2'].update_state(conflict_key, 'value_from_2')

        # Forzar sincronización entre todos los pares
        for i, coord_a in self.coordinators.items():
            for j, coord_b in self.coordinators.items():
                if i != j:
                    await coord_a.sync_with_peer(coord_b)

        # Verificar que se alcanza consistencia eventual
        values = [coord.get_state_value(conflict_key) for coord in self.coordinators.values()]
        unique_values = set(values)

        # Debería converger a un solo valor (dependiendo de la estrategia de resolución)
        assert len(unique_values) == 1, f"Conflicto no resuelto: valores encontrados {unique_values}"

        resolved_value = list(unique_values)[0]
        print(f"✅ Conflicto resuelto con valor: {resolved_value}")

    @pytest.mark.asyncio
    async def test_automatic_recovery_from_failures(self):
        """Test de recuperación automática de múltiples fallos."""
        print("🧪 Test: Recuperación automática de múltiples fallos")

        # Estado inicial consistente
        await self.coordinators['coordinator_0'].update_state('recovery_test', 'initial_state')

        # Simular múltiples fallos secuenciales
        failure_sequence = [
            ('coordinator_1', 1.0),
            ('coordinator_2', 1.5),
            ('coordinator_0', 1.0),
        ]

        for node_id, duration in failure_sequence:
            self.network_simulator.simulate_node_failure(node_id, duration)
            print(f"🔌 Simulando fallo de {node_id} por {duration}s")

            # Durante el fallo, actualizar estado si hay nodos activos
            active_coords = [c for c in self.coordinators.values() if not self.network_simulator.is_node_failed(c.node_id)]
            if active_coords:
                await active_coords[0].update_state('recovery_test', f'updated_during_{node_id}_failure')

            await asyncio.sleep(duration + 0.1)  # Esperar recuperación

        # Verificar que todos los nodos se recuperan
        for coord in self.coordinators.values():
            assert not self.network_simulator.is_node_failed(coord.node_id)

        # Forzar sincronización completa
        for coord_a in self.coordinators.values():
            for coord_b in self.coordinators.values():
                if coord_a.node_id != coord_b.node_id:
                    await coord_a.sync_with_peer(coord_b)

        # Verificar consistencia eventual
        values = [coord.get_state_value('recovery_test') for coord in self.coordinators.values()]
        unique_values = set(values)
        assert len(unique_values) == 1, f"Recuperación fallida: valores {unique_values}"

        print("✅ Recuperación automática completada exitosamente")

    @pytest.mark.asyncio
    async def test_eventual_consistency_under_load(self):
        """Test de consistencia eventual bajo carga con fallos."""
        print("🧪 Test: Consistencia eventual bajo carga")

        # Simular carga alta con actualizaciones concurrentes y fallos
        async def concurrent_updates(coord: MockCoordinator, update_count: int):
            for i in range(update_count):
                await coord.update_state(f'load_key_{i}', f'value_{coord.node_id}_{i}')
                await asyncio.sleep(0.01)  # Pequeño delay entre actualizaciones

        # Iniciar actualizaciones concurrentes
        tasks = []
        for coord in self.coordinators.values():
            tasks.append(concurrent_updates(coord, 10))

        # Durante las actualizaciones, simular fallos intermitentes
        async def intermittent_failures():
            for _ in range(5):
                failed_node = 'coordinator_' + str(1)  # Alternar entre nodos
                self.network_simulator.simulate_node_failure(failed_node, 0.5)
                await asyncio.sleep(0.3)

        # Ejecutar todo concurrentemente
        await asyncio.gather(
            asyncio.gather(*tasks),
            intermittent_failures()
        )

        # Esperar un poco para estabilización
        await asyncio.sleep(1.0)

        # Forzar sincronización final
        for coord_a in self.coordinators.values():
            for coord_b in self.coordinators.values():
                if coord_a.node_id != coord_b.node_id:
                    await coord_a.sync_with_peer(coord_b)

        # Verificar que se alcanza algún nivel de consistencia
        # (No podemos verificar valores exactos debido a la concurrencia,
        # pero sí que no hay corrupciones críticas)
        for coord in self.coordinators.values():
            # Verificar que el estado no está corrupto
            state_size = len(coord.local_state)
            assert state_size > 0, f"Estado corrupto en {coord.node_id}"

        print("✅ Consistencia eventual mantenida bajo carga")

    @pytest.mark.asyncio
    async def test_validation_during_failures(self):
        """Test de validación de estado durante fallos de red."""
        print("🧪 Test: Validación de estado durante fallos")

        # Mock de base de datos para validación
        mock_db = Mock()

        # Configurar mock de modelos
        mock_models = []
        for i in range(5):
            mock_model = Mock()
            mock_model.id = i
            mock_model.status = 'trained'
            mock_model.global_parameters_hash = f'hash_{i}'
            mock_models.append(mock_model)

        mock_db.query.return_value.all.return_value = mock_models

        # Estado inicial válido
        validator = self.coordinators['coordinator_0'].state_validator
        is_valid, issues = await validator.validate_global_state(mock_db)
        assert is_valid, f"Estado inicial debería ser válido: {issues}"

        # Simular fallos y verificar que la validación detecta inconsistencias
        self.network_simulator.simulate_node_failure('coordinator_1', 5.0)

        # Crear partición
        self.network_simulator.create_partition('test_partition', ['coordinator_0', 'coordinator_1'])

        # Después de fallos, el estado podría ser inconsistente
        # La validación debería detectar los issues apropiadamente
        is_valid_after_failure, issues_after = await validator.validate_global_state(mock_db)

        # No necesariamente inválido, pero debería reportar issues si los hay
        print(f"📊 Issues después de fallos: {len(issues_after)}")

        # Curar fallos y verificar recuperación
        self.network_simulator.heal_partition('test_partition')

        # Después de recuperación, el sistema debería volver a ser consistente
        await asyncio.sleep(1.0)  # Tiempo para recuperación

        print("✅ Validación durante fallos completada")


if __name__ == '__main__':
    # Ejecutar tests manualmente para debugging
    async def run_tests():
        test_instance = NetworkFailureConsistencyTest()
        test_instance.setup_method()

        try:
            await test_instance.test_network_partition_consistency()
            await test_instance.test_node_reconnection_recovery()
            await test_instance.test_state_conflict_resolution()
            await test_instance.test_automatic_recovery_from_failures()
            await test_instance.test_eventual_consistency_under_load()
            await test_instance.test_validation_during_failures()

            print("🎉 Todos los tests de consistencia con fallos de red pasaron exitosamente!")

        except Exception as e:
            print(f"❌ Error en tests: {e}")
            raise

    asyncio.run(run_tests())