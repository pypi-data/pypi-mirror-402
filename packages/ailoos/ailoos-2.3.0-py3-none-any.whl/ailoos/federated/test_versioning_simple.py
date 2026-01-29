"""
Simple tests for Federated Versioning System components.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from .federated_version_manager import FederatedVersionManager, VersionStatus


class TestVersionManagerBasic:
    """Basic tests for Version Manager."""

    @pytest.fixture
    async def mock_ipfs(self):
        """Mock IPFS for tests."""
        mock = AsyncMock()
        mock.store_data = AsyncMock(return_value="QmTestCID")
        return mock

    @pytest.fixture
    def version_manager(self, mock_ipfs):
        """Version manager instance."""
        return FederatedVersionManager(
            registry_path=":memory:",
            ipfs_manager=mock_ipfs,
            min_validations=2
        )

    @pytest.mark.asyncio
    async def test_version_registration(self, version_manager, mock_ipfs):
        """Test basic version registration."""
        with patch.object(version_manager, '_save_registry', new_callable=AsyncMock):
            version_id = await version_manager.register_new_version(
                model_data=b"test_data",
                metadata={"version": "1.0.0", "model_name": "test"},
                creator_node="node1"
            )

            assert version_id is not None
            assert "test" in version_id
            assert "1.0.0" in version_id

    @pytest.mark.asyncio
    async def test_validation_vote(self, version_manager):
        """Test validation voting."""
        # Register version first
        with patch.object(version_manager, '_save_registry', new_callable=AsyncMock):
            version_id = await version_manager.register_new_version(
                model_data=b"test",
                metadata={"version": "1.0.0"},
                creator_node="node1"
            )

        # Submit vote
        with patch.object(version_manager, '_save_registry', new_callable=AsyncMock):
            success = await version_manager.submit_validation_vote(
                version_id=version_id,
                node_id="node2",
                vote="approved"
            )

            assert success


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])