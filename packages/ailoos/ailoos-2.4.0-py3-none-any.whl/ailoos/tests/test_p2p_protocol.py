"""
Pruebas para el protocolo P2P seguro de AILOOS Federated Learning.
"""

import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from ..federated.p2p_protocol import (
    P2PProtocol, P2PMessage, P2PMessageType, PeerInfo, ConnectionState,
    create_p2p_protocol, SecureAggregationProtocol
)


class TestP2PMessage:
    """Pruebas para la clase P2PMessage."""

    def test_message_creation(self):
        """Test creación básica de mensaje."""
        import time
        current_time = time.time()

        message = P2PMessage(
            message_id="test-123",
            message_type=P2PMessageType.HANDSHAKE_INIT,
            sender_id="node1",
            receiver_id="node2",
            timestamp=current_time,
            payload={"test": "data"}
        )

        assert message.message_id == "test-123"
        assert message.message_type == P2PMessageType.HANDSHAKE_INIT
        assert message.sender_id == "node1"
        assert message.receiver_id == "node2"
        assert message.payload == {"test": "data"}
        assert not message.is_expired()

    def test_message_serialization(self):
        """Test serialización y deserialización de mensajes."""
        original = P2PMessage(
            message_id="test-123",
            message_type=P2PMessageType.MODEL_UPDATE,
            sender_id="node1",
            receiver_id="node2",
            timestamp=1234567890.0,
            payload={"weights": {"layer1": [1, 2, 3]}},
            signature="test_sig"
        )

        # Serializar
        data = original.to_dict()

        # Deserializar
        restored = P2PMessage.from_dict(data)

        assert restored.message_id == original.message_id
        assert restored.message_type == original.message_type
        assert restored.sender_id == original.sender_id
        assert restored.receiver_id == original.receiver_id
        assert restored.payload == original.payload
        assert restored.signature == original.signature

    def test_message_expiration(self):
        """Test expiración de mensajes."""
        import time

        # Mensaje expirado
        expired_message = P2PMessage(
            message_id="expired",
            message_type=P2PMessageType.HEARTBEAT,
            sender_id="node1",
            receiver_id="node2",
            timestamp=time.time() - 400,  # Timestamp 400 segundos atrás
            payload={},
            ttl=300  # TTL de 300 segundos
        )

        assert expired_message.is_expired()

        # Mensaje válido
        valid_message = P2PMessage(
            message_id="valid",
            message_type=P2PMessageType.HEARTBEAT,
            sender_id="node1",
            receiver_id="node2",
            timestamp=time.time(),  # Timestamp actual
            payload={}
        )

        assert not valid_message.is_expired()


class TestPeerInfo:
    """Pruebas para la clase PeerInfo."""

    def test_peer_info_creation(self):
        """Test creación de PeerInfo."""
        peer = PeerInfo(
            node_id="test-node",
            host="192.168.1.100",
            port=8443,
            public_key=b"test-key"
        )

        assert peer.node_id == "test-node"
        assert peer.address == ("192.168.1.100", 8443)
        assert peer.connection_state == ConnectionState.DISCONNECTED
        assert not peer.is_connected

    def test_peer_connection_states(self):
        """Test estados de conexión."""
        peer = PeerInfo(
            node_id="test-node",
            host="localhost",
            port=8443,
            public_key=b"test-key"
        )

        # Inicialmente desconectado
        assert not peer.is_connected

        # Conectando
        peer.connection_state = ConnectionState.CONNECTING
        assert not peer.is_connected

        # Conectado
        peer.connection_state = ConnectionState.CONNECTED
        assert peer.is_connected

        # Autenticado
        peer.connection_state = ConnectionState.AUTHENTICATED
        assert peer.is_connected

        # Error
        peer.connection_state = ConnectionState.ERROR
        assert not peer.is_connected


class TestP2PProtocol:
    """Pruebas para la clase P2PProtocol."""

    @pytest.fixture
    def temp_cert_dir(self):
        """Directorio temporal para certificados."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def protocol(self, temp_cert_dir):
        """Instancia de protocolo para pruebas."""
        return P2PProtocol(
            node_id="test-node",
            host="127.0.0.1",
            port=8444,
            cert_dir=str(temp_cert_dir),
            enable_tls=False  # Deshabilitar TLS para pruebas
        )

    def test_protocol_initialization(self, protocol):
        """Test inicialización del protocolo."""
        assert protocol.node_id == "test-node"
        assert protocol.host == "127.0.0.1"
        assert protocol.port == 8444
        assert not protocol.is_running
        assert not protocol.enable_tls

    def test_add_peer(self, protocol):
        """Test añadir peer."""
        peer = PeerInfo(
            node_id="peer1",
            host="127.0.0.1",
            port=8445,
            public_key=b"peer-key"
        )

        protocol.add_peer(peer)

        assert "peer1" in protocol.peers
        assert protocol.peers["peer1"] == peer

    def test_get_peer_info(self, protocol):
        """Test obtener información de peer."""
        peer = PeerInfo(
            node_id="peer1",
            host="127.0.0.1",
            port=8445,
            public_key=b"peer-key"
        )

        protocol.add_peer(peer)

        retrieved = protocol.get_peer_info("peer1")
        assert retrieved == peer

        # Peer inexistente
        assert protocol.get_peer_info("nonexistent") is None

    def test_get_connected_peers(self, protocol):
        """Test obtener peers conectados."""
        # Peer desconectado
        peer1 = PeerInfo(
            node_id="peer1",
            host="127.0.0.1",
            port=8445,
            public_key=b"peer-key",
            connection_state=ConnectionState.DISCONNECTED
        )

        # Peer conectado
        peer2 = PeerInfo(
            node_id="peer2",
            host="127.0.0.1",
            port=8446,
            public_key=b"peer-key2",
            connection_state=ConnectionState.CONNECTED
        )

        # Peer autenticado
        peer3 = PeerInfo(
            node_id="peer3",
            host="127.0.0.1",
            port=8447,
            public_key=b"peer-key3",
            connection_state=ConnectionState.AUTHENTICATED
        )

        protocol.add_peer(peer1)
        protocol.add_peer(peer2)
        protocol.add_peer(peer3)

        connected = protocol.get_connected_peers()
        assert len(connected) == 2
        assert "peer2" in connected
        assert "peer3" in connected
        assert "peer1" not in connected

    def test_get_stats(self, protocol):
        """Test obtener estadísticas."""
        stats = protocol.get_stats()

        expected_keys = [
            "messages_sent", "messages_received", "bytes_sent", "bytes_received",
            "connections_established", "connections_failed", "handshakes_completed",
            "errors", "active_connections", "known_peers", "pending_handshakes",
            "is_running"
        ]

        for key in expected_keys:
            assert key in stats

        assert stats["is_running"] == False
        assert stats["known_peers"] == 0
        assert stats["active_connections"] == 0

    @pytest.mark.asyncio
    async def test_protocol_start_stop(self, protocol):
        """Test iniciar y detener protocolo."""
        # El protocolo debería iniciarse sin TLS
        await protocol.start()
        assert protocol.is_running

        # Verificar que las tareas de mantenimiento están corriendo
        await asyncio.sleep(0.1)  # Pequeña pausa

        await protocol.stop()
        assert not protocol.is_running

    def test_message_handler_registration(self, protocol):
        """Test registro de handlers de mensajes."""
        async def test_handler(message):
            pass

        protocol.register_message_handler(P2PMessageType.MODEL_UPDATE, test_handler)

        assert P2PMessageType.MODEL_UPDATE in protocol.message_handlers
        assert protocol.message_handlers[P2PMessageType.MODEL_UPDATE] == test_handler

    def test_connection_handler_registration(self, protocol):
        """Test registro de handlers de conexión."""
        def test_handler(event):
            pass

        protocol.register_connection_handler("connected", test_handler)

        assert "connected" in protocol.connection_handlers
        assert protocol.connection_handlers["connected"] == test_handler


class TestSecureAggregationProtocol:
    """Pruebas para SecureAggregationProtocol."""

    @pytest.fixture
    def mock_protocol(self):
        """Protocolo mock para pruebas."""
        protocol = Mock(spec=P2PProtocol)
        protocol.node_id = "test-node"
        return protocol

    @pytest.fixture
    def secure_agg(self, mock_protocol):
        """Instancia de SecureAggregationProtocol."""
        return SecureAggregationProtocol(mock_protocol)

    def test_secure_aggregation_init(self, secure_agg):
        """Test inicialización de agregación segura."""
        assert secure_agg.protocol.node_id == "test-node"
        assert secure_agg.aggregation_sessions == {}

    @pytest.mark.asyncio
    async def test_initiate_secure_aggregation(self, secure_agg):
        """Test iniciar sesión de agregación segura."""
        # Mock del método de envío
        secure_agg._send_aggregation_request = Mock(return_value=asyncio.Future())
        secure_agg._send_aggregation_request.return_value.set_result(None)

        aggregation_id = await secure_agg.initiate_secure_aggregation(
            session_id="session-123",
            participants=["node1", "node2", "node3"],
            aggregation_type="fedavg"
        )

        assert aggregation_id in secure_agg.aggregation_sessions
        session = secure_agg.aggregation_sessions[aggregation_id]

        assert session["session_id"] == "session-123"
        assert session["participants"] == ["node1", "node2", "node3"]
        assert session["aggregation_type"] == "fedavg"
        assert session["status"] == "collecting"

    def test_verify_masked_update(self, secure_agg):
        """Test verificación de actualización enmascarada."""
        # Actualización válida
        valid_update = {
            "weights": {"layer1": [1, 2, 3]},
            "num_samples": 100
        }
        assert secure_agg._verify_masked_update(valid_update)

        # Actualización inválida - faltan campos
        invalid_update = {"weights": {"layer1": [1, 2, 3]}}
        assert not secure_agg._verify_masked_update(invalid_update)

        # Actualización inválida - sin pesos
        invalid_update2 = {"num_samples": 100}
        assert not secure_agg._verify_masked_update(invalid_update2)


class TestP2PProtocolIntegration:
    """Pruebas de integración del protocolo P2P."""

    @pytest.fixture
    def temp_cert_dir(self):
        """Directorio temporal para certificados."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_create_p2p_protocol(self, temp_cert_dir):
        """Test función de conveniencia para crear protocolo."""
        protocol = create_p2p_protocol(
            node_id="test-node",
            host="127.0.0.1",
            port=8444,
            cert_dir=str(temp_cert_dir)
        )

        assert isinstance(protocol, P2PProtocol)
        assert protocol.node_id == "test-node"
        assert protocol.host == "127.0.0.1"
        assert protocol.port == 8444

    @pytest.mark.asyncio
    async def test_connect_to_peer_network(self, temp_cert_dir):
        """Test conexión a red de peers."""
        protocol = create_p2p_protocol(
            node_id="coordinator",
            host="127.0.0.1",
            port=8444,
            cert_dir=str(temp_cert_dir)
        )

        peer_addresses = [
            ("127.0.0.1", 8445, "node1"),
            ("127.0.0.1", 8446, "node2"),
        ]

        # Mock de connect_to_peer para evitar conexiones reales
        with patch.object(protocol, 'connect_to_peer', return_value=asyncio.Future()) as mock_connect:
            mock_connect.return_value.set_result(True)

            from ..federated.p2p_protocol import connect_to_peer_network
            await connect_to_peer_network(protocol, peer_addresses)

            # Verificar que se intentó conectar a ambos peers
            assert mock_connect.call_count == 2

            # Verificar que los peers fueron añadidos
            assert "node1" in protocol.peers
            assert "node2" in protocol.peers
            assert protocol.peers["node1"].host == "127.0.0.1"
            assert protocol.peers["node1"].port == 8445
            assert protocol.peers["node2"].port == 8446


if __name__ == "__main__":
    pytest.main([__file__])