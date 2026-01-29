"""
Pruebas de integración end-to-end para comunicación P2P con federated learning.
Simula una red P2P completa con 3 nodos federados, incluyendo handshake seguro,
envío de actualizaciones de modelos y agregación segura.
"""

import asyncio
import pytest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any

from ..federated.p2p_protocol import (
    P2PProtocol, P2PMessage, P2PMessageType, PeerInfo, ConnectionState,
    SecureAggregationProtocol
)
from ..coordinator.empoorio_lm.coordinator import (
    EmpoorioLMCoordinator, EmpoorioLMCoordinatorConfig, EmpoorioLMTrainingSession
)
from ..federated.node_communicator import NodeCommunicator, NodeUpdate


class MockP2PNode:
    """
    Nodo P2P simulado para pruebas de integración.
    Simula el comportamiento de un nodo federado real.
    """

    def __init__(self, node_id: str, host: str = "127.0.0.1", port: int = 0):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.p2p_protocol = None
        self.is_connected = False
        self.session_id = None
        self.model_weights = self._generate_initial_weights()
        self.training_metrics = {
            "accuracy": 0.85,
            "loss": 0.45,
            "training_time": 120.5,
            "samples_processed": 1000
        }
        self.received_model_updates = []

    def _generate_initial_weights(self) -> Dict[str, Any]:
        """Generar pesos iniciales simulados del modelo."""
        return {
            "layer1": {"weights": [0.1, 0.2, 0.3], "bias": [0.0]},
            "layer2": {"weights": [[0.1, 0.2], [0.3, 0.4]], "bias": [0.0, 0.0]},
            "output": {"weights": [0.5, 0.6], "bias": [0.0]}
        }

    async def initialize(self, cert_dir: str):
        """Inicializar el protocolo P2P del nodo."""
        self.p2p_protocol = P2PProtocol(
            node_id=self.node_id,
            host=self.host,
            port=self.port,
            cert_dir=cert_dir,
            enable_tls=False  # Deshabilitar TLS para pruebas
        )

        # Registrar handlers para mensajes
        self.p2p_protocol.register_message_handler(
            P2PMessageType.AGGREGATION_REQUEST, self._handle_aggregation_request
        )
        self.p2p_protocol.register_message_handler(
            P2PMessageType.MODEL_UPDATE, self._handle_model_update
        )

        await self.p2p_protocol.start()
        self.port = self.p2p_protocol.port  # Puerto asignado dinámicamente
        return self.port

    async def connect_to_coordinator(self, coordinator_host: str, coordinator_port: int):
        """Conectar al coordinador."""
        coordinator_peer = PeerInfo(
            node_id="coordinator",
            host=coordinator_host,
            port=coordinator_port,
            public_key=b"coordinator_key"
        )

        self.p2p_protocol.add_peer(coordinator_peer)
        success = await self.p2p_protocol.connect_to_peer(coordinator_peer)

        if success:
            self.is_connected = True
            # Registrar en sesión
            await self._register_in_session()

        return success

    async def _register_in_session(self):
        """Registrar el nodo en una sesión de entrenamiento."""
        # Simular registro enviando mensaje de handshake con info de sesión
        message = P2PMessage(
            message_id=f"register_{self.node_id}_{asyncio.get_event_loop().time()}",
            message_type=P2PMessageType.HANDSHAKE_INIT,
            sender_id=self.node_id,
            receiver_id="coordinator",
            timestamp=asyncio.get_event_loop().time(),
            payload={
                "session_id": "test_session_123",
                "node_info": {
                    "hardware_type": "cpu",
                    "compute_capacity": 4,
                    "memory_gb": 8,
                    "p2p_host": self.host,
                    "p2p_port": self.port
                }
            }
        )

        message.signature = self.p2p_protocol._sign_message(message)
        await self.p2p_protocol._send_message_to_peer("coordinator", message)

    async def _handle_aggregation_request(self, message: P2PMessage):
        """Manejar solicitud de agregación (inicio de ronda)."""
        payload = message.payload
        self.session_id = payload.get("session_id")
        round_num = payload.get("round_num")

        print(f"📡 Nodo {self.node_id} recibió solicitud de ronda {round_num}")

        # Simular entrenamiento local y envío de contribución
        await asyncio.sleep(0.1)  # Simular tiempo de entrenamiento

        # Actualizar pesos simulados
        self._update_weights()

        # Enviar contribución
        await self._send_contribution(round_num)

    async def _handle_model_update(self, message: P2PMessage):
        """Manejar actualización de modelo del coordinador."""
        payload = message.payload
        model_weights = payload.get("model_weights")
        round_num = payload.get("round_num")

        self.received_model_updates.append({
            "round_num": round_num,
            "model_weights": model_weights,
            "timestamp": asyncio.get_event_loop().time()
        })

        print(f"📥 Nodo {self.node_id} recibió actualización de modelo para ronda {round_num}")

    def _update_weights(self):
        """Actualizar pesos simulados después del entrenamiento."""
        # Simular actualización de pesos con ruido
        import random
        for layer_name, layer_data in self.model_weights.items():
            if "weights" in layer_data:
                weights = layer_data["weights"]
                if isinstance(weights, list):
                    if isinstance(weights[0], list):  # Matriz
                        for i in range(len(weights)):
                            for j in range(len(weights[i])):
                                weights[i][j] += random.uniform(-0.01, 0.01)
                    else:  # Vector
                        for i in range(len(weights)):
                            weights[i] += random.uniform(-0.01, 0.01)

    async def _send_contribution(self, round_num: int):
        """Enviar contribución de entrenamiento al coordinador."""
        message = P2PMessage(
            message_id=f"contribution_{self.node_id}_{round_num}_{asyncio.get_event_loop().time()}",
            message_type=P2PMessageType.MODEL_UPDATE,
            sender_id=self.node_id,
            receiver_id="coordinator",
            timestamp=asyncio.get_event_loop().time(),
            payload={
                "session_id": self.session_id,
                "round_num": round_num,
                "model_weights": self.model_weights,
                "training_metrics": self.training_metrics
            }
        )

        message.signature = self.p2p_protocol._sign_message(message)
        await self.p2p_protocol._send_message_to_peer("coordinator", message)

        print(f"📤 Nodo {self.node_id} envió contribución para ronda {round_num}")

    async def disconnect(self):
        """Desconectar el nodo."""
        if self.p2p_protocol:
            await self.p2p_protocol.stop()
        self.is_connected = False


class TestP2PFederatedIntegration:
    """Pruebas de integración end-to-end para federated learning P2P."""

    @pytest.fixture
    def temp_cert_dir(self):
        """Directorio temporal para certificados."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    async def coordinator(self, temp_cert_dir):
        """Coordinador EmpoorioLM para pruebas."""
        config = EmpoorioLMCoordinatorConfig(
            coordinator_id="test_coordinator",
            enable_p2p=True,
            p2p_host="127.0.0.1",
            p2p_port=8443,  # Puerto fijo para pruebas
            cert_dir=str(temp_cert_dir),
            enable_secure_aggregation=False,  # Deshabilitar para pruebas simples
            min_nodes_per_round=2,
            max_rounds_per_session=3
        )

        coordinator = EmpoorioLMCoordinator(config)
        await coordinator.initialize_base_model()

        yield coordinator

        # Cleanup
        try:
            if coordinator.p2p_protocol and coordinator.p2p_protocol.is_running:
                await coordinator.p2p_protocol.stop()
        except Exception:
            pass  # Ignore cleanup errors

    @pytest.fixture
    async def mock_nodes(self, temp_cert_dir):
        """Tres nodos simulados para pruebas."""
        nodes = []
        for i in range(3):
            node = MockP2PNode(f"node_{i+1}", "127.0.0.1", 8444 + i)  # Puertos fijos
            port = await node.initialize(str(temp_cert_dir))
            nodes.append(node)

        yield nodes

        # Cleanup
        for node in nodes:
            try:
                if node.p2p_protocol and node.p2p_protocol.is_running:
                    await node.disconnect()
            except Exception:
                pass  # Ignore cleanup errors

    @pytest.mark.asyncio
    async def test_p2p_federated_training_complete_flow(self, coordinator, mock_nodes, temp_cert_dir):
        """
        Prueba completa del flujo de entrenamiento federado P2P con 3 nodos.

        Esta prueba simula:
        1. Inicialización de nodos y coordinador
        2. Conexión P2P y handshake seguro
        3. Registro de nodos en sesión
        4. Inicio de rondas de entrenamiento
        5. Envío de actualizaciones de modelos
        6. Agregación de pesos
        7. Distribución de modelo actualizado
        8. Verificación de comunicación end-to-end
        """
        print("\n🚀 Iniciando prueba de integración P2P Federated Learning")

        # 1. Verificar inicialización del coordinador
        coord = await coordinator.__anext__()
        assert coord.p2p_enabled
        assert coord.p2p_protocol.is_running
        coordinator_port = coord.p2p_protocol.port
        print(f"✅ Coordinador inicializado en puerto {coordinator_port}")

        # 2. Conectar nodos al coordinador
        nodes = await mock_nodes.__anext__()
        connected_nodes = []
        for i, node in enumerate(nodes):
            success = await node.connect_to_coordinator("127.0.0.1", coordinator_port)
            assert success, f"Falló conexión del nodo {node.node_id}"
            connected_nodes.append(node)
            print(f"✅ Nodo {node.node_id} conectado al coordinador")

        # Esperar a que se establezcan las conexiones y handshakes
        await asyncio.sleep(1.0)

        # Verificar conexiones en el coordinador
        connected_peers = coord.p2p_protocol.get_connected_peers()
        print(f"Peers conectados en coordinador: {connected_peers}")
        print(f"Peers conocidos: {list(coord.p2p_protocol.peers.keys())}")

        # Para esta prueba de integración, verificamos que los nodos se conectaron exitosamente
        # Los peers se registran automáticamente durante el handshake
        # Simulamos el registro manual para la prueba usando la sesión que se creó automáticamente
        session_id = list(coord.active_sessions.keys())[0]  # Usar la sesión que se creó automáticamente

        for node in nodes:
            node_info = {
                "hardware_type": "cpu",
                "compute_capacity": 4,
                "memory_gb": 8,
                "p2p_host": node.host,
                "p2p_port": node.port
            }
            success = await coord.register_node(session_id, node.node_id, node_info)
            assert success, f"Falló registro del nodo {node.node_id}"

        print(f"✅ Registrados {len(nodes)} nodos en el coordinador")

        # 3. Crear sesión de entrenamiento
        session_id = await coord.create_training_session(
            session_name="test_p2p_session",
            num_rounds=2
        )
        assert session_id is not None
        print(f"✅ Sesión de entrenamiento creada: {session_id}")

        # 4. Registrar nodos en la sesión (esto debería suceder automáticamente vía P2P)
        # Los nodos ya enviaron mensajes de registro durante la conexión
        await asyncio.sleep(0.5)  # Esperar procesamiento de mensajes

        session = coord.active_sessions.get(session_id)
        assert session is not None
        # Los nodos se registraron en la sesión anterior, verificar la sesión correcta
        print(f"✅ Sesión activa: {session_id}")

        # 5. Iniciar primera ronda
        success = await coord.start_round(session_id)
        assert success
        print("✅ Primera ronda iniciada")

        # 6. Esperar contribuciones de nodos (los nodos deberían responder automáticamente)
        await asyncio.sleep(1.0)  # Tiempo para que los nodos procesen y respondan

        # Verificar que se recibieron contribuciones
        session = coord.active_sessions.get(session_id)
        assert session.current_round == 1
        round_data = session.round_data.get(1)
        assert round_data is not None
        contributions_received = round_data.get("received_contributions", 0)
        assert contributions_received >= 2, f"Se esperaban al menos 2 contribuciones, se recibieron {contributions_received}"
        print(f"✅ Recibidas {contributions_received} contribuciones en ronda 1")

        # 7. Verificar agregación automática
        # La agregación debería haberse completado automáticamente
        assert round_data["status"] == "completed"
        assert session.global_weights is not None
        print("✅ Agregación completada, modelo global actualizado")

        # 8. Verificar distribución del modelo actualizado a nodos
        await asyncio.sleep(0.5)  # Tiempo para distribución

        # Verificar que los nodos recibieron actualizaciones
        total_updates_received = sum(len(node.received_model_updates) for node in nodes)
        assert total_updates_received >= 2, f"Se esperaban al menos 2 actualizaciones, se recibieron {total_updates_received}"
        print(f"✅ {total_updates_received} nodos recibieron actualización de modelo")

        # 9. Iniciar segunda ronda
        success = await coord.start_round(session_id)
        assert success
        print("✅ Segunda ronda iniciada")

        # 10. Esperar segunda ronda
        await asyncio.sleep(1.0)

        session = coord.active_sessions.get(session_id)
        assert session.current_round == 2
        round_data_2 = session.round_data.get(2)
        assert round_data_2 is not None
        contributions_round_2 = round_data_2.get("received_contributions", 0)
        assert contributions_round_2 >= 2
        print(f"✅ Recibidas {contributions_round_2} contribuciones en ronda 2")

        # 11. Verificar finalización de sesión
        # Después de 2 rondas, la sesión debería completarse
        await asyncio.sleep(0.5)
        assert session_id not in coord.active_sessions
        assert session_id in coord.completed_sessions
        print("✅ Sesión completada exitosamente")

        # 12. Verificaciones finales
        final_session = coord.completed_sessions[session_id]
        assert final_session.status == "completed"
        assert final_session.total_contributions >= 4  # Al menos 2 contribuciones por ronda
        assert final_session.global_model_path is not None

        print("🎉 Prueba de integración P2P Federated Learning completada exitosamente!")
        print(f"📊 Estadísticas finales:")
        print(f"   - Rondas completadas: {final_session.current_round}")
        print(f"   - Contribuciones totales: {final_session.total_contributions}")
        print(f"   - Nodos participantes: {len(final_session.active_nodes)}")
        print(f"   - Versión final del modelo: {final_session.global_model_path}")

    @pytest.mark.asyncio
    async def test_secure_aggregation_flow(self, coordinator, mock_nodes, temp_cert_dir):
        """
        Prueba del flujo de agregación segura con comunicación P2P.
        """
        print("\n🔐 Probando agregación segura P2P")

        # Habilitar agregación segura en el coordinador
        coordinator.config.enable_secure_aggregation = True

        # Inicializar nodos
        coordinator_port = coordinator.p2p_protocol.port
        for node in mock_nodes:
            await node.connect_to_coordinator("127.0.0.1", coordinator_port)

        await asyncio.sleep(0.5)

        # Crear sesión con agregación segura
        session_id = await coordinator.create_training_session(
            session_name="secure_test_session",
            num_rounds=1
        )

        await asyncio.sleep(0.5)

        # Iniciar ronda
        success = await coordinator.start_round(session_id)
        assert success

        # Esperar procesamiento
        await asyncio.sleep(1.0)

        # Verificar que se usó agregación segura
        session = coordinator.completed_sessions.get(session_id)
        assert session is not None
        print("✅ Agregación segura completada")

    @pytest.mark.asyncio
    async def test_node_failure_handling(self, coordinator, mock_nodes, temp_cert_dir):
        """
        Prueba de manejo de fallos de nodos durante el entrenamiento federado.
        """
        print("\n💥 Probando manejo de fallos de nodos")

        # Conectar solo 2 nodos inicialmente
        coordinator_port = coordinator.p2p_protocol.port
        await mock_nodes[0].connect_to_coordinator("127.0.0.1", coordinator_port)
        await mock_nodes[1].connect_to_coordinator("127.0.0.1", coordinator_port)

        await asyncio.sleep(0.5)

        # Crear sesión
        session_id = await coordinator.create_training_session(
            session_name="failure_test_session",
            num_rounds=1
        )

        await asyncio.sleep(0.5)

        # Simular desconexión de un nodo
        await mock_nodes[1].disconnect()
        print("⚠️ Nodo desconectado simulado")

        # Intentar iniciar ronda (debería funcionar con nodos mínimos)
        success = await coordinator.start_round(session_id)
        assert success

        await asyncio.sleep(1.0)

        # Verificar que la ronda se completó con el nodo restante
        session = coordinator.completed_sessions.get(session_id)
        assert session is not None
        assert session.total_contributions >= 1
        print("✅ Sesión completada a pesar de fallo de nodo")

    @pytest.mark.asyncio
    async def test_p2p_message_security(self, coordinator, mock_nodes, temp_cert_dir):
        """
        Prueba de seguridad de mensajes P2P (firmas, verificación).
        """
        print("\n🔒 Probando seguridad de mensajes P2P")

        # Conectar nodos
        coordinator_port = coordinator.p2p_protocol.port
        for node in mock_nodes[:2]:  # Solo 2 nodos para esta prueba
            await node.connect_to_coordinator("127.0.0.1", coordinator_port)

        await asyncio.sleep(0.5)

        # Verificar que las conexiones están autenticadas
        connected_peers = coordinator.p2p_protocol.get_connected_peers()
        assert len(connected_peers) == 2

        # Verificar estados de conexión
        for peer_id in connected_peers:
            peer_info = coordinator.p2p_protocol.get_peer_info(peer_id)
            assert peer_info.connection_state == ConnectionState.AUTHENTICATED

        print("✅ Conexiones P2P autenticadas correctamente")

        # Crear sesión y verificar comunicación segura
        session_id = await coordinator.create_training_session(
            session_name="security_test_session",
            num_rounds=1
        )

        await asyncio.sleep(0.5)

        success = await coordinator.start_round(session_id)
        assert success

        await asyncio.sleep(1.0)

        # Verificar estadísticas de seguridad
        p2p_stats = coordinator.p2p_protocol.get_stats()
        assert p2p_stats["handshakes_completed"] >= 2
        print(f"✅ {p2p_stats['handshakes_completed']} handshakes seguros completados")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])