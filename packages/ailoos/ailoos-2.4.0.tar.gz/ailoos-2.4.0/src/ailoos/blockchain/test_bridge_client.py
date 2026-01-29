"""
Unit tests for Bridge Client
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from eth_account import Account
from eth_account.messages import encode_defunct

from .bridge_client import BridgeClient, BridgeClientError, get_bridge_client


class TestBridgeClient:
    """Test cases for BridgeClient."""

    @pytest.fixture
    def mock_session(self):
        """Mock requests session."""
        session = Mock()
        response = Mock()
        response.json.return_value = {"success": True, "tx_hash": "0x123"}
        response.raise_for_status.return_value = None
        session.request.return_value = response
        return session

    @pytest.fixture
    def bridge_client(self, mock_session):
        """Create bridge client with mocked session."""
        with patch('requests.Session', return_value=mock_session):
            client = BridgeClient("http://test-bridge.com")
            client.session = mock_session
            return client

    @pytest.fixture
    def signer_client(self, mock_session):
        """Create bridge client with signer."""
        private_key = "0x" + "1" * 64  # Dummy private key
        with patch('requests.Session', return_value=mock_session):
            client = BridgeClient("http://test-bridge.com")
            client.session = mock_session
            client.signer = Account.from_key(private_key)
            return client

    def test_init(self):
        """Test client initialization."""
        with patch('requests.Session') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            client = BridgeClient("http://test.com", "api_key", 60)

            assert client.base_url == "http://test.com"
            assert client.api_key == "api_key"
            assert client.timeout == 60
            mock_session.headers.update.assert_called()

    @pytest.mark.asyncio
    async def test_register_node_success(self, signer_client):
        """Test successful node registration."""
        signer_client._make_request = Mock(return_value={"success": True, "tx_hash": "0x123"})

        result = await signer_client.register_node(
            node_id="test_node",
            cpu_score=100,
            gpu_score=200,
            ram_gb=16,
            location="US"
        )

        assert result["success"] is True
        assert result["tx_hash"] == "0x123"

        # Verify the request was made with correct payload
        signer_client._make_request.assert_called_once()
        call_args = signer_client._make_request.call_args
        assert call_args[0][0] == 'POST'
        assert call_args[0][1] == '/register_node_from_ailoos'

        payload = call_args[0][2]
        assert payload["node_id"] == "test_node"
        assert payload["cpu_score"] == 100
        assert "signature" in payload

    @pytest.mark.asyncio
    async def test_register_node_no_signer(self, bridge_client):
        """Test node registration without signer fails."""
        with pytest.raises(BridgeClientError, match="No private key available"):
            await bridge_client.register_node("test", 1, 1, 1, "loc")

    @pytest.mark.asyncio
    async def test_report_work_success(self, signer_client):
        """Test successful work reporting."""
        signer_client._make_request = Mock(return_value={"success": True})

        result = await signer_client.report_work("test_node", 1000)

        assert result["success"] is True

        call_args = signer_client._make_request.call_args
        assert call_args[0][1] == '/report_work_from_ailoos'
        payload = call_args[0][2]
        assert payload["node_id"] == "test_node"
        assert payload["units"] == 1000

    @pytest.mark.asyncio
    async def test_validate_proof_success(self, signer_client):
        """Test successful proof validation."""
        signer_client._make_request = Mock(return_value={"success": True})

        proof_data = b"test_proof_data"
        result = await signer_client.validate_proof(
            node_id="test_node",
            dataset_id="dataset_1",
            compute_power=1000000,
            proof=proof_data,
            model_hash="hash123",
            expected_accuracy="95.5"
        )

        assert result["success"] is True

        call_args = signer_client._make_request.call_args
        assert call_args[0][1] == '/validate_proof_from_ailoos'
        payload = call_args[0][2]
        assert payload["node_id"] == "test_node"
        assert payload["dataset_id"] == "dataset_1"
        assert payload["proof"] == list(proof_data)

    @pytest.mark.asyncio
    async def test_claim_rewards_success(self, signer_client):
        """Test successful rewards claiming."""
        signer_client._make_request = Mock(return_value={"success": True})

        result = await signer_client.claim_rewards("test_node")

        assert result["success"] is True

        call_args = signer_client._make_request.call_args
        assert call_args[0][1] == '/claim_rewards_from_ailoos'

    @pytest.mark.asyncio
    async def test_stake_tokens_success(self, signer_client):
        """Test successful token staking."""
        signer_client._make_request = Mock(return_value={"success": True, "tx_hash": "0x456"})

        result = await signer_client.stake_tokens(100.0, "0x123...")

        assert result["success"] is True
        assert result["tx_hash"] == "0x456"

        call_args = signer_client._make_request.call_args
        assert call_args[0][1] == '/stake_from_ailoos'
        payload = call_args[0][2]
        assert payload["amount"] == "100.0"
        assert payload["address"] == "0x123..."

    @pytest.mark.asyncio
    async def test_unstake_tokens_success(self, signer_client):
        """Test successful token unstaking."""
        signer_client._make_request = Mock(return_value={"success": True, "tx_hash": "0x789"})

        result = await signer_client.unstake_tokens(50.0, "0x123...")

        assert result["success"] is True
        assert result["tx_hash"] == "0x789"

        call_args = signer_client._make_request.call_args
        assert call_args[0][1] == '/unstake_from_ailoos'

    def test_make_request_success(self, bridge_client, mock_session):
        """Test successful HTTP request."""
        mock_response = Mock()
        mock_response.json.return_value = {"success": True, "data": "test"}
        mock_response.raise_for_status.return_value = None
        mock_session.request.return_value = mock_response

        result = bridge_client._make_request('GET', '/test')

        assert result == {"success": True, "data": "test"}

    def test_make_request_http_error(self, bridge_client, mock_session):
        """Test HTTP request error handling."""
        mock_session.request.side_effect = Exception("Connection failed")

        with pytest.raises(BridgeClientError, match="HTTP error"):
            bridge_client._make_request('GET', '/test')

    def test_make_request_bridge_error(self, bridge_client, mock_session):
        """Test bridge error response."""
        mock_response = Mock()
        mock_response.json.return_value = {"success": False, "error": "Bridge error"}
        mock_response.raise_for_status.return_value = None
        mock_session.request.return_value = mock_response

        with pytest.raises(BridgeClientError, match="Bridge error"):
            bridge_client._make_request('GET', '/test')

    @pytest.mark.asyncio
    async def test_get_bridge_status_no_endpoint(self, bridge_client):
        """Test bridge status when no status endpoint."""
        bridge_client._make_request = Mock(side_effect=BridgeClientError("Not found"))

        result = await bridge_client.get_bridge_status()

        assert result["status"] == "unknown"
        assert "bridge_url" in result

    @patch.dict(os.environ, {
        'DRACMAS_BRIDGE_URL': 'http://env-bridge.com',
        'DRACMAS_BRIDGE_API_KEY': 'env_key'
    })
    def test_get_bridge_client_from_env(self):
        """Test getting bridge client from environment variables."""
        import ailoos.blockchain.bridge_client as bridge_client_module
        bridge_client_module._bridge_client = None
        with patch.object(bridge_client_module, 'BridgeClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            client = bridge_client_module.get_bridge_client()

            mock_client_class.assert_called_once_with('http://env-bridge.com', 'env_key')
            assert client == mock_client

    def test_sign_message(self, signer_client):
        """Test message signing."""
        message = "test message"
        signature = signer_client._sign_message(message)

        # Verify signature format
        assert not signature.startswith('0x')
        assert len(signature) == 130  # 65 bytes hex

        # Verify signature is valid for the message
        signable = encode_defunct(text=message)
        recovered = Account.recover_message(signable, signature="0x" + signature)
        assert recovered == signer_client.signer.address


if __name__ == "__main__":
    pytest.main([__file__])
