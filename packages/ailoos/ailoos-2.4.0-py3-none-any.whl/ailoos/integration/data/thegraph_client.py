import logging
import requests
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

class TheGraphClient:
    """
    Cliente para interactuar con The Graph para indexing de blockchain data via GraphQL.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el cliente de The Graph.

        Args:
            api_key: Clave API opcional para acceso premium.
        """
        self.base_url = "https://api.thegraph.com/subgraphs/name/"
        self.api_key = api_key or os.getenv("THEGRAPH_API_KEY")
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def query(self, subgraph_id: str, query_string: str) -> Dict[str, Any]:
        """
        Ejecuta una query GraphQL en un subgraph específico.

        Args:
            subgraph_id: ID del subgraph (e.g., 'uniswap/uniswap-v2').
            query_string: String de la query GraphQL.

        Returns:
            Dict con los datos de respuesta.

        Raises:
            Exception: Si la query falla.
        """
        url = f"{self.base_url}{subgraph_id}"
        payload = {"query": query_string}

        try:
            logger.info(f"Ejecutando query GraphQL en subgraph: {subgraph_id}")
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                logger.error(f"Errores en query GraphQL: {data['errors']}")
                raise Exception(f"GraphQL query errors: {data['errors']}")

            logger.info("Query GraphQL ejecutada exitosamente")
            return data.get("data", {})

        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red en query GraphQL: {e}")
            raise Exception(f"Network error during GraphQL query: {e}")
        except Exception as e:
            logger.error(f"Error inesperado en query GraphQL: {e}")
            raise

    def get_block_data(self, subgraph_id: str, block_number: int) -> Dict[str, Any]:
        """
        Obtiene datos de un bloque específico.

        Args:
            subgraph_id: ID del subgraph.
            block_number: Número del bloque.

        Returns:
            Dict con datos del bloque.
        """
        query = f"""
        {{
            blocks(where: {{number: {block_number}}}) {{
                id
                number
                timestamp
                transactions {{
                    id
                    from
                    to
                    value
                }}
            }}
        }}
        """
        return self.query(subgraph_id, query)

    def get_token_transfers(self, subgraph_id: str, token_address: str, limit: int = 100) -> Dict[str, Any]:
        """
        Obtiene transferencias de un token específico.

        Args:
            subgraph_id: ID del subgraph.
            token_address: Dirección del token.
            limit: Límite de resultados.

        Returns:
            Dict con transferencias.
        """
        query = f"""
        {{
            transfers(where: {{token: "{token_address}"}}, first: {limit}, orderBy: timestamp, orderDirection: desc) {{
                id
                from
                to
                value
                timestamp
            }}
        }}
        """
        return self.query(subgraph_id, query)