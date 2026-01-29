import logging
import requests
from typing import Dict, Any, Optional, List
import os
import json

logger = logging.getLogger(__name__)

class AlchemyClient:
    """
    Cliente para interactuar con Alchemy API para enhanced RPC calls y analytics.
    """

    def __init__(self, api_key: Optional[str] = None, network: str = "eth-mainnet"):
        """
        Inicializa el cliente de Alchemy.

        Args:
            api_key: Clave API de Alchemy.
            network: Red blockchain (e.g., 'eth-mainnet', 'polygon-mainnet').
        """
        self.api_key = api_key or os.getenv("ALCHEMY_API_KEY")
        if not self.api_key:
            raise ValueError("Alchemy API key is required")
        self.base_url = f"https://{network}.g.alchemy.com/v2/{self.api_key}"
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def send_rpc_call(self, method: str, params: Optional[List[Any]] = None) -> Dict[str, Any]:
        """
        Envía una llamada RPC genérica a Alchemy.

        Args:
            method: Método RPC (e.g., 'eth_getBalance').
            params: Parámetros del método.

        Returns:
            Dict con la respuesta RPC.

        Raises:
            Exception: Si la llamada falla.
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or []
        }

        try:
            logger.info(f"Enviando llamada RPC: {method}")
            response = self.session.post(self.base_url, data=json.dumps(payload), timeout=30)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                logger.error(f"Error en respuesta RPC: {data['error']}")
                raise Exception(f"RPC error: {data['error']}")

            logger.info("Llamada RPC exitosa")
            return data.get("result", {})

        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red en llamada RPC: {e}")
            raise Exception(f"Network error during RPC call: {e}")
        except Exception as e:
            logger.error(f"Error inesperado en llamada RPC: {e}")
            raise

    def get_balance(self, address: str, block: str = "latest") -> str:
        """
        Obtiene el balance de una dirección.

        Args:
            address: Dirección Ethereum.
            block: Bloque (default: 'latest').

        Returns:
            Balance en wei como string hex.
        """
        return self.send_rpc_call("eth_getBalance", [address, block])

    def get_transaction_receipt(self, tx_hash: str) -> Dict[str, Any]:
        """
        Obtiene el recibo de una transacción.

        Args:
            tx_hash: Hash de la transacción.

        Returns:
            Dict con detalles del recibo.
        """
        return self.send_rpc_call("eth_getTransactionReceipt", [tx_hash])

    def get_logs(self, from_block: str, to_block: str, address: Optional[str] = None, topics: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Obtiene logs de eventos.

        Args:
            from_block: Bloque inicial.
            to_block: Bloque final.
            address: Dirección del contrato (opcional).
            topics: Topics de eventos (opcional).

        Returns:
            Lista de logs.
        """
        params = {
            "fromBlock": from_block,
            "toBlock": to_block
        }
        if address:
            params["address"] = address
        if topics:
            params["topics"] = topics

        return self.send_rpc_call("eth_getLogs", [params])

    def get_nft_metadata(self, contract_address: str, token_id: str) -> Dict[str, Any]:
        """
        Obtiene metadatos de un NFT.

        Args:
            contract_address: Dirección del contrato NFT.
            token_id: ID del token.

        Returns:
            Dict con metadatos del NFT.
        """
        # Usar endpoint específico de Alchemy para NFTs
        url = f"https://eth-mainnet.g.alchemy.com/nft/v2/{self.api_key}/getNFTMetadata"
        params = {
            "contractAddress": contract_address,
            "tokenId": token_id
        }

        try:
            logger.info(f"Obteniendo metadatos NFT: {contract_address}:{token_id}")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                logger.error(f"Error obteniendo metadatos NFT: {data['error']}")
                raise Exception(f"NFT metadata error: {data['error']}")

            logger.info("Metadatos NFT obtenidos exitosamente")
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red obteniendo metadatos NFT: {e}")
            raise Exception(f"Network error during NFT metadata request: {e}")
        except Exception as e:
            logger.error(f"Error inesperado obteniendo metadatos NFT: {e}")
            raise

    def get_nft_floor_price(self, contract_address: str) -> Dict[str, Any]:
        """
        Obtiene el precio floor de un NFT.

        Args:
            contract_address: Dirección del contrato NFT.

        Returns:
            Dict con precio floor.
        """
        url = f"https://eth-mainnet.g.alchemy.com/nft/v2/{self.api_key}/getFloorPrice"
        params = {"contractAddress": contract_address}

        try:
            logger.info(f"Obteniendo precio floor NFT: {contract_address}")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                logger.error(f"Error obteniendo precio floor NFT: {data['error']}")
                raise Exception(f"NFT floor price error: {data['error']}")

            logger.info("Precio floor NFT obtenido exitosamente")
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red obteniendo precio floor NFT: {e}")
            raise Exception(f"Network error during NFT floor price request: {e}")
        except Exception as e:
            logger.error(f"Error inesperado obteniendo precio floor NFT: {e}")
            raise