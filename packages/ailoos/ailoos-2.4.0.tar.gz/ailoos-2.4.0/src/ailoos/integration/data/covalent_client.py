import logging
import requests
from typing import Dict, Any, Optional, List
import os

logger = logging.getLogger(__name__)

class CovalentClient:
    """
    Cliente para interactuar con Covalent API para datos históricos de blockchain.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el cliente de Covalent.

        Args:
            api_key: Clave API de Covalent.
        """
        self.base_url = "https://api.covalenthq.com/v1"
        self.api_key = api_key or os.getenv("COVALENT_API_KEY")
        if not self.api_key:
            raise ValueError("Covalent API key is required")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Realiza una petición a la API de Covalent.

        Args:
            endpoint: Endpoint de la API.
            params: Parámetros de query.

        Returns:
            Dict con la respuesta.

        Raises:
            Exception: Si la petición falla.
        """
        url = f"{self.base_url}{endpoint}"
        try:
            logger.info(f"Realizando petición a Covalent API: {url}")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get("error"):
                logger.error(f"Error en respuesta de Covalent: {data['error']}")
                raise Exception(f"Covalent API error: {data['error']}")

            logger.info("Petición a Covalent API exitosa")
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red en petición a Covalent: {e}")
            raise Exception(f"Network error during Covalent API request: {e}")
        except Exception as e:
            logger.error(f"Error inesperado en petición a Covalent: {e}")
            raise

    def get_token_balances(self, chain_id: int, address: str) -> Dict[str, Any]:
        """
        Obtiene balances de tokens para una dirección.

        Args:
            chain_id: ID de la cadena (e.g., 1 para Ethereum).
            address: Dirección de la wallet.

        Returns:
            Dict con balances de tokens.
        """
        endpoint = f"/{chain_id}/address/{address}/balances_v2/"
        return self._make_request(endpoint)

    def get_transaction_history(self, chain_id: int, address: str, page_size: int = 100, page_number: int = 0) -> Dict[str, Any]:
        """
        Obtiene historial de transacciones para una dirección.

        Args:
            chain_id: ID de la cadena.
            address: Dirección de la wallet.
            page_size: Tamaño de página.
            page_number: Número de página.

        Returns:
            Dict con historial de transacciones.
        """
        endpoint = f"/{chain_id}/address/{address}/transactions_v2/"
        params = {"page-size": page_size, "page-number": page_number}
        return self._make_request(endpoint, params)

    def get_historical_portfolio(self, chain_id: int, address: str, days: int = 30) -> Dict[str, Any]:
        """
        Obtiene portafolio histórico para una dirección.

        Args:
            chain_id: ID de la cadena.
            address: Dirección de la wallet.
            days: Número de días para el historial.

        Returns:
            Dict con portafolio histórico.
        """
        endpoint = f"/{chain_id}/address/{address}/portfolio_v2/"
        params = {"days": days}
        return self._make_request(endpoint, params)

    def get_nft_balances(self, chain_id: int, address: str) -> Dict[str, Any]:
        """
        Obtiene balances de NFTs para una dirección.

        Args:
            chain_id: ID de la cadena.
            address: Dirección de la wallet.

        Returns:
            Dict con balances de NFTs.
        """
        endpoint = f"/{chain_id}/address/{address}/balances_nft/"
        return self._make_request(endpoint)

    def get_block_details(self, chain_id: int, block_height: str) -> Dict[str, Any]:
        """
        Obtiene detalles de un bloque.

        Args:
            chain_id: ID de la cadena.
            block_height: Altura del bloque (o 'latest').

        Returns:
            Dict con detalles del bloque.
        """
        endpoint = f"/{chain_id}/block/{block_height}/"
        return self._make_request(endpoint)