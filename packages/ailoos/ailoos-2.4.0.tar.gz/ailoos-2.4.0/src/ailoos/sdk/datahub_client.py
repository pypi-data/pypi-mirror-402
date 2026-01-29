"""
DataHubClient - Cliente SDK para el DataHub de AILOOS.
Permite consultar el estado IPFS de datasets y descargar manifiestos reales.
"""

import asyncio
from typing import Any, Dict, Optional

import aiohttp
import logging
from ..data.ipfs_connector import ipfs_connector
from .auth import NodeAuthenticator

logger = logging.getLogger(__name__)


class DataHubClient:
    """Cliente SDK para interactuar con el DataHub API."""

    def __init__(self, base_url: str, authenticator: Optional[NodeAuthenticator] = None, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.authenticator = authenticator
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None

    async def initialize(self) -> bool:
        """Inicializar sesión HTTP."""
        if self._session:
            return True
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self._session = aiohttp.ClientSession(timeout=timeout)
        return True

    async def close(self) -> None:
        """Cerrar sesión HTTP."""
        if self._session:
            await self._session.close()
            self._session = None

    def _headers(self) -> Dict[str, str]:
        if self.authenticator:
            if hasattr(self.authenticator, "get_auth_headers"):
                return self.authenticator.get_auth_headers()
            if hasattr(self.authenticator, "get_headers"):
                return self.authenticator.get_headers()
        return {}

    async def get_ipfs_status(self, dataset_id: str) -> Dict[str, Any]:
        """Obtener estado IPFS de un dataset desde DataHub."""
        if not self._session:
            raise RuntimeError("DataHubClient not initialized")

        url = f"{self.base_url}/datasets/{dataset_id}/ipfs-status"
        async with self._session.get(url, headers=self._headers()) as response:
            data = await response.json()
            if response.status != 200:
                raise RuntimeError(f"DataHub error {response.status}: {data}")
            return data

    async def download_manifest(self, dataset_id: str) -> Dict[str, Any]:
        """
        Descargar manifiesto IPFS del dataset.

        Returns:
            Dict con el manifiesto JSON.
        """
        status = await self.get_ipfs_status(dataset_id)
        ipfs_cid = status.get("ipfs_cid")
        if not ipfs_cid:
            raise RuntimeError("Dataset IPFS CID not available yet")

        manifest = await asyncio.to_thread(ipfs_connector.get_json, ipfs_cid)
        if not manifest:
            raise RuntimeError(f"Failed to download manifest from IPFS: {ipfs_cid}")

        return manifest
