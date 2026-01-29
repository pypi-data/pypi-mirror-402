import logging
import hashlib
import requests
import json
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DealInfo:
    deal_id: str
    cid: str
    miner: str
    price: float
    duration: int
    status: str

class FilecoinClient:
    """
    Cliente para interactuar con la red Filecoin para deals de almacenamiento.
    Maneja almacenamiento, recuperación, verificación de integridad y gestión de costos.
    """

    def __init__(self, lotus_endpoint: str, auth_token: Optional[str] = None, timeout: int = 30):
        """
        Inicializa el cliente Filecoin.

        Args:
            lotus_endpoint: URL del endpoint de Lotus (ej: http://localhost:1234/rpc/v0)
            auth_token: Token de autenticación si es necesario
            timeout: Timeout para requests en segundos
        """
        self.lotus_endpoint = lotus_endpoint
        self.auth_token = auth_token
        self.timeout = timeout
        self.session = requests.Session()
        if auth_token:
            self.session.headers.update({'Authorization': f'Bearer {auth_token}'})

    def _make_request(self, method: str, params: list = None) -> Dict[str, Any]:
        """
        Realiza una petición JSON-RPC al endpoint de Lotus.

        Args:
            method: Método JSON-RPC
            params: Parámetros del método

        Returns:
            Respuesta JSON-RPC

        Raises:
            Exception: Si la petición falla
        """
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or [],
            "id": int(time.time() * 1000)
        }

        try:
            response = self.session.post(
                self.lotus_endpoint,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()

            if 'error' in result:
                raise Exception(f"Lotus API error: {result['error']}")

            return result.get('result')

        except requests.RequestException as e:
            logger.error(f"Error en petición a Lotus: {e}")
            raise Exception(f"Failed to communicate with Lotus: {e}")

    def store_data(self, data: bytes, duration: int, miner_address: str = None) -> str:
        """
        Almacena datos en Filecoin creando un deal.

        Args:
            data: Datos a almacenar
            duration: Duración del deal en epochs
            miner_address: Dirección del miner (opcional, se selecciona automáticamente si no se proporciona)

        Returns:
            CID del deal creado

        Raises:
            Exception: Si falla el almacenamiento
        """
        try:
            # Calcular hash SHA256 para integridad
            data_hash = hashlib.sha256(data).hexdigest()
            logger.info(f"Iniciando almacenamiento de datos con hash: {data_hash}")

            # Primero, importar datos a Lotus
            import_result = self._make_request("ClientImport", [{
                "Path": "/tmp/temp_data",  # Nota: En producción, manejar archivos temporales correctamente
                "IsCAR": False
            }])

            cid = import_result.get('Root', {}).get('Cid', {}).get('/')
            if not cid:
                raise Exception("Failed to import data to Lotus")

            logger.info(f"Datos importados con CID: {cid}")

            # Si no se proporciona miner, buscar uno disponible
            if not miner_address:
                miners = self._find_available_miners()
                if not miners:
                    raise Exception("No available miners found")
                miner_address = miners[0]

            # Crear deal
            deal_params = {
                "Data": {"TransferType": "graphsync", "Root": {"/": cid}},
                "Wallet": self._get_wallet_address(),
                "Miner": miner_address,
                "EpochPrice": "25000000000",  # 0.000000025 FIL per epoch per GiB
                "MinBlocksDuration": duration,
                "ProviderCollateral": "1000000000000000000",  # 1 FIL
                "DealStartEpoch": -1,  # Start immediately
                "FastRetrieval": True,
                "VerifiedDeal": False
            }

            deal_result = self._make_request("ClientStartDeal", [deal_params])
            deal_id = deal_result.get('DealID')

            logger.info(f"Deal iniciado con ID: {deal_id}")

            # Esperar confirmación del deal
            self._wait_for_deal_confirmation(deal_id)

            return cid

        except Exception as e:
            logger.error(f"Error almacenando datos en Filecoin: {e}")
            raise

    def retrieve_data(self, cid: str) -> bytes:
        """
        Recupera datos desde Filecoin usando el CID.

        Args:
            cid: CID de los datos a recuperar

        Returns:
            Datos recuperados

        Raises:
            Exception: Si falla la recuperación
        """
        try:
            logger.info(f"Iniciando recuperación de datos con CID: {cid}")

            # Encontrar deal activo para el CID
            deals = self._make_request("ClientListDeals")
            active_deal = None
            for deal in deals:
                if deal.get('Proposal', {}).get('PieceCID', {}).get('/') == cid and deal.get('State') == 'Active':
                    active_deal = deal
                    break

            if not active_deal:
                raise Exception(f"No active deal found for CID: {cid}")

            # Recuperar datos
            retrieve_result = self._make_request("ClientRetrieve", [{
                "Root": {"Cid": {"/": cid}, "Piece": None},
                "DealID": active_deal['DealID']
            }])

            # Nota: En implementación real, manejar el stream de datos correctamente
            # Aquí asumimos que retrieve_result contiene los datos
            data = retrieve_result  # Placeholder

            logger.info(f"Datos recuperados exitosamente para CID: {cid}")
            return data

        except Exception as e:
            logger.error(f"Error recuperando datos desde Filecoin: {e}")
            raise

    def verify_integrity(self, cid: str, expected_hash: str) -> bool:
        """
        Verifica la integridad de los datos almacenados comparando hashes.

        Args:
            cid: CID de los datos
            expected_hash: Hash SHA256 esperado

        Returns:
            True si la integridad es correcta, False en caso contrario
        """
        try:
            logger.info(f"Verificando integridad para CID: {cid}")

            data = self.retrieve_data(cid)
            actual_hash = hashlib.sha256(data).hexdigest()

            is_valid = actual_hash == expected_hash
            if not is_valid:
                logger.warning(f"Integridad comprometida. Esperado: {expected_hash}, Actual: {actual_hash}")
            else:
                logger.info("Integridad verificada correctamente")

            return is_valid

        except Exception as e:
            logger.error(f"Error verificando integridad: {e}")
            return False

    def estimate_cost(self, size_bytes: int, duration_epochs: int) -> float:
        """
        Estima el costo de almacenamiento en FIL.

        Args:
            size_bytes: Tamaño de los datos en bytes
            duration_epochs: Duración en epochs

        Returns:
            Costo estimado en FIL
        """
        try:
            # Obtener precio actual del mercado
            market_stats = self._make_request("StateMarketStats")

            # Calcular tamaño en GiB
            size_gib = size_bytes / (1024 ** 3)

            # Precio base por epoch por GiB (en attoFIL)
            epoch_price = int(market_stats.get('AvgPricePerEpoch', '25000000000'))

            # Costo total
            total_cost_attofil = epoch_price * size_gib * duration_epochs

            # Convertir a FIL
            total_cost_fil = total_cost_attofil / 10**18

            logger.info(f"Costo estimado: {total_cost_fil} FIL para {size_gib} GiB por {duration_epochs} epochs")
            return total_cost_fil

        except Exception as e:
            logger.error(f"Error estimando costo: {e}")
            # Valor por defecto
            return (size_bytes / (1024 ** 3)) * 0.000000025 * duration_epochs

    def _find_available_miners(self) -> list:
        """Encuentra miners disponibles para deals."""
        try:
            miners = self._make_request("StateListMiners", [[]])
            # Filtrar miners activos (simplificado)
            return miners[:10]  # Retornar primeros 10
        except Exception:
            return []

    def _get_wallet_address(self) -> str:
        """Obtiene la dirección de wallet por defecto."""
        try:
            wallets = self._make_request("WalletList")
            return wallets[0] if wallets else ""
        except Exception:
            return ""

    def _wait_for_deal_confirmation(self, deal_id: int, timeout: int = 300):
        """Espera confirmación del deal."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                deal_info = self._make_request("ClientGetDealInfo", [deal_id])
                if deal_info.get('State') == 'Active':
                    logger.info(f"Deal {deal_id} confirmado como activo")
                    return
                elif deal_info.get('State') in ['Failed', 'Rejected']:
                    raise Exception(f"Deal {deal_id} failed: {deal_info.get('State')}")
            except Exception as e:
                logger.warning(f"Error checking deal status: {e}")

            time.sleep(10)

        raise Exception(f"Deal {deal_id} no se confirmó en {timeout} segundos")