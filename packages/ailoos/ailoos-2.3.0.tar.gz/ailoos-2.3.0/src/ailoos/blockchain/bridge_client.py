"""
Bridge Client - Cliente HTTP para comunicarse con el puente Rust DracmaS
"""

import asyncio
import json
import os
import time
from typing import Dict, Any, Optional, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from eth_account import Account
from eth_account.signers.local import LocalAccount
from eth_account.messages import encode_defunct

from ..core.logging import get_logger

logger = get_logger(__name__)


class BridgeClientError(Exception):
    """Error del cliente del puente."""
    pass


class BridgeClient:
    """
    Cliente HTTP para el puente cross-chain DracmaS.

    Maneja autenticación, firmas, retry logic y comunicación con el puente Rust.
    """

    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: int = 30):
        """
        Inicializar cliente del puente.

        Args:
            base_url: URL base del puente (ej: http://localhost:3000)
            api_key: Clave API opcional para autenticación
            timeout: Timeout en segundos para requests
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout

        # Configurar sesión con retry
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Headers comunes
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Ailoos-Bridge-Client/1.0'
        })

        if self.api_key:
            self.session.headers.update({'X-API-Key': self.api_key})

        # Cargar signer si hay private key
        self.signer: Optional[LocalAccount] = None
        private_key = self._get_private_key()
        if private_key:
            self.signer = Account.from_key(private_key)

        logger.info(f"🔗 Bridge client initialized for {base_url}")

    def _get_private_key(self) -> Optional[str]:
        """Obtener private key de entorno."""
        return os.getenv('AILOOS_BRIDGE_PRIVATE_KEY')

    def _sign_message(self, message: str) -> str:
        """Firmar mensaje con EIP-191 (Ethereum Signed Message)."""
        if not self.signer:
            raise BridgeClientError("No private key available for signing")

        signable = encode_defunct(text=message)
        signed = self.signer.sign_message(signable)
        return signed.signature.hex()

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Hacer request HTTP con manejo de errores.

        Args:
            method: Método HTTP
            endpoint: Endpoint relativo
            data: Datos JSON a enviar

        Returns:
            Respuesta JSON

        Raises:
            BridgeClientError: En caso de error
        """
        url = f"{self.base_url}{endpoint}"

        try:
            if data:
                response = self.session.request(method, url, json=data, timeout=self.timeout)
            else:
                response = self.session.request(method, url, timeout=self.timeout)

            response.raise_for_status()

            if response.content:
                result = response.json()
            else:
                result = {}

            # Verificar respuesta del puente
            if not result.get('success', False):
                error_msg = result.get('error', 'Unknown bridge error')
                raise BridgeClientError(f"Bridge error: {error_msg}")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            raise BridgeClientError(f"Invalid JSON response: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error calling {url}: {e}")
            raise BridgeClientError(f"HTTP error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error calling {url}: {e}")
            raise BridgeClientError(f"HTTP error: {e}")

    async def register_node(
        self,
        node_id: str,
        cpu_score: int,
        gpu_score: int,
        ram_gb: int,
        location: str,
        owner: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Registrar un nuevo nodo en DracmaS.

        Args:
            node_id: ID único del nodo
            cpu_score: Puntaje CPU
            gpu_score: Puntaje GPU
            ram_gb: RAM en GB
            location: Ubicación del nodo

        Returns:
            Resultado del registro
        """
        # Crear mensaje para firma
        owner_value = owner or ""
        message = f"register_node:{node_id}{cpu_score}{gpu_score}{ram_gb}{location}{owner_value}"

        # Firmar
        signature = self._sign_message(message)

        # Preparar payload
        payload = {
            "node_id": node_id,
            "cpu_score": cpu_score,
            "gpu_score": gpu_score,
            "ram_gb": ram_gb,
            "location": location,
            "owner": owner,
            "signature": signature
        }

        # Hacer request
        result = await asyncio.get_event_loop().run_in_executor(
            None, self._make_request, 'POST', '/register_node_from_ailoos', payload
        )

        logger.info(f"✅ Node {node_id} registered via bridge")
        return result

    async def report_work(self, node_id: str, units: int) -> Dict[str, Any]:
        """
        Reportar trabajo realizado por un nodo.

        Args:
            node_id: ID del nodo
            units: Unidades de trabajo realizadas

        Returns:
            Resultado del reporte
        """
        # Crear mensaje para firma
        message = f"report_work:{node_id}{units}"

        # Firmar
        signature = self._sign_message(message)

        # Preparar payload
        payload = {
            "node_id": node_id,
            "units": units,
            "signature": signature
        }

        # Hacer request
        result = await asyncio.get_event_loop().run_in_executor(
            None, self._make_request, 'POST', '/report_work_from_ailoos', payload
        )

        logger.info(f"✅ Work reported for node {node_id}: {units} units")
        return result

    async def validate_proof(self, node_id: str, dataset_id: str, compute_power: int,
                           proof: bytes, model_hash: str, expected_accuracy: str) -> Dict[str, Any]:
        """
        Validar proof de entrenamiento.

        Args:
            node_id: ID del nodo
            dataset_id: ID del dataset
            compute_power: Poder computacional usado
            proof: Proof de entrenamiento (bytes)
            model_hash: Hash del modelo resultante
            expected_accuracy: Precisión esperada

        Returns:
            Resultado de la validación
        """
        # Crear mensaje para firma
        message = f"validate_proof:{node_id}{dataset_id}{compute_power}{model_hash}{expected_accuracy}"

        # Firmar
        signature = self._sign_message(message)

        # Preparar payload
        payload = {
            "node_id": node_id,
            "dataset_id": dataset_id,
            "compute_power": str(compute_power),  # Como string para compatibilidad
            "proof": list(proof),  # Convertir bytes a lista
            "model_hash": model_hash,
            "expected_accuracy": expected_accuracy,
            "signature": signature
        }

        # Hacer request
        result = await asyncio.get_event_loop().run_in_executor(
            None, self._make_request, 'POST', '/validate_proof_from_ailoos', payload
        )

        logger.info(f"✅ Proof validated for node {node_id} on dataset {dataset_id}")
        return result

    async def claim_rewards(self, node_id: str) -> Dict[str, Any]:
        """
        Reclamar recompensas para un nodo.

        Args:
            node_id: ID del nodo

        Returns:
            Resultado del claim
        """
        # Crear mensaje para firma
        message = f"claim_rewards:{node_id}"

        # Firmar
        signature = self._sign_message(message)

        # Preparar payload
        payload = {
            "node_id": node_id,
            "signature": signature
        }

        # Hacer request
        result = await asyncio.get_event_loop().run_in_executor(
            None, self._make_request, 'POST', '/claim_rewards_from_ailoos', payload
        )

        logger.info(f"✅ Rewards claimed for node {node_id}")
        return result

    async def get_pending_rewards(self, node_id: str) -> Dict[str, Any]:
        """
        Consultar recompensas pendientes para un nodo.

        Args:
            node_id: ID del nodo

        Returns:
            Resultado con recompensas pendientes
        """
        message = f"pending_rewards:{node_id}"
        signature = self._sign_message(message)

        payload = {
            "node_id": node_id,
            "signature": signature
        }

        result = await asyncio.get_event_loop().run_in_executor(
            None, self._make_request, 'POST', '/pending_rewards_from_ailoos', payload
        )

        logger.info(f"✅ Pending rewards requested for node {node_id}")
        return result

    async def get_wallet_balance(self, address: str) -> Dict[str, Any]:
        """
        Consultar balance de una wallet via bridge.

        Args:
            address: Direccion de la wallet

        Returns:
            Resultado con balance
        """
        message = f"wallet_balance:{address}"
        signature = self._sign_message(message)

        payload = {
            "address": address,
            "signature": signature
        }

        result = await asyncio.get_event_loop().run_in_executor(
            None, self._make_request, 'POST', '/wallet_balance_from_ailoos', payload
        )

        logger.info(f"✅ Wallet balance requested for {address}")
        return result

    async def get_staking_info(self, address: str) -> Dict[str, Any]:
        """
        Consultar informacion de staking via bridge.

        Args:
            address: Direccion de la wallet

        Returns:
            Resultado con staking info
        """
        message = f"staking_info:{address}"
        signature = self._sign_message(message)

        payload = {
            "address": address,
            "signature": signature
        }

        result = await asyncio.get_event_loop().run_in_executor(
            None, self._make_request, 'POST', '/staking_info_from_ailoos', payload
        )

        logger.info(f"✅ Staking info requested for {address}")
        return result

    async def get_transaction_history(self, address: str, limit: int = 50) -> Dict[str, Any]:
        """
        Consultar historial de transacciones via bridge.

        Args:
            address: Direccion de la wallet
            limit: Numero maximo de transacciones

        Returns:
            Resultado con historial
        """
        message = f"wallet_history:{address}:{limit}"
        signature = self._sign_message(message)

        payload = {
            "address": address,
            "limit": limit,
            "signature": signature
        }

        result = await asyncio.get_event_loop().run_in_executor(
            None, self._make_request, 'POST', '/wallet_history_from_ailoos', payload
        )

        logger.info(f"✅ Wallet history requested for {address}")
        return result

    async def get_rewards_totals(self) -> Dict[str, Any]:
        """
        Consultar totales globales de rewards via bridge.

        Returns:
            Resultado con totales
        """
        message = "rewards_totals"
        signature = self._sign_message(message)

        payload = {
            "signature": signature
        }

        result = await asyncio.get_event_loop().run_in_executor(
            None, self._make_request, 'POST', '/rewards_totals_from_ailoos', payload
        )

        logger.info("✅ Rewards totals requested")
        return result

    async def get_bridge_signer_address(self) -> Dict[str, Any]:
        """
        Obtener la direccion cosmos del signer del bridge.
        """
        message = "bridge_signer_address"
        signature = self._sign_message(message)
        payload = {"signature": signature}

        result = await asyncio.get_event_loop().run_in_executor(
            None, self._make_request, 'POST', '/bridge_signer_address_from_ailoos', payload
        )
        logger.info("✅ Bridge signer address requested")
        return result

    async def register_bridge_signer_system_account(self) -> Dict[str, Any]:
        """
        Registrar el signer del bridge como system account en la chain.
        """
        message = "register_bridge_signer"
        signature = self._sign_message(message)
        payload = {"signature": signature}

        result = await asyncio.get_event_loop().run_in_executor(
            None, self._make_request, 'POST', '/register_bridge_signer_from_ailoos', payload
        )
        logger.info("✅ Bridge signer registered as system account")
        return result

    async def stake_tokens(self, amount: float, address: str) -> Dict[str, Any]:
        """
        Stakear tokens en DracmaS a través del puente.

        Args:
            amount: Cantidad a stakear
            address: Dirección del usuario

        Returns:
            Resultado del staking
        """
        # Crear mensaje para firma
        message = f"stake:{amount}:{address}"

        # Firmar
        signature = self._sign_message(message)

        # Preparar payload
        payload = {
            "amount": str(amount),
            "address": address,
            "signature": signature
        }

        # Hacer request (asumiendo endpoint /stake_from_ailoos)
        result = await asyncio.get_event_loop().run_in_executor(
            None, self._make_request, 'POST', '/stake_from_ailoos', payload
        )

        logger.info(f"✅ Tokens staked via bridge: {amount} for {address}")
        return result

    async def unstake_tokens(self, amount: float, address: str) -> Dict[str, Any]:
        """
        Unstakear tokens de DracmaS a través del puente.

        Args:
            amount: Cantidad a unstakear
            address: Dirección del usuario

        Returns:
            Resultado del unstaking
        """
        # Crear mensaje para firma
        message = f"unstake:{amount}:{address}"

        # Firmar
        signature = self._sign_message(message)

        # Preparar payload
        payload = {
            "amount": str(amount),
            "address": address,
            "signature": signature
        }

        # Hacer request (asumiendo endpoint /unstake_from_ailoos)
        result = await asyncio.get_event_loop().run_in_executor(
            None, self._make_request, 'POST', '/unstake_from_ailoos', payload
        )

        logger.info(f"✅ Tokens unstaked via bridge: {amount} for {address}")
        return result

    async def get_bridge_status(self) -> Dict[str, Any]:
        """
        Obtener estado del puente.

        Returns:
            Información del estado
        """
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._make_request, 'GET', '/status'
            )
            return result
        except BridgeClientError:
            # Si no hay endpoint de status, devolver info básica
            return {
                "status": "unknown",
                "bridge_url": self.base_url,
                "has_signer": self.signer is not None
            }

    def close(self):
        """Cerrar sesión HTTP."""
        self.session.close()
        logger.info("🔌 Bridge client connection closed")


# Instancia global del cliente
_bridge_client: Optional[BridgeClient] = None


def get_bridge_client() -> BridgeClient:
    """Obtener instancia global del cliente del puente."""
    global _bridge_client
    if _bridge_client is None:
        # Configuración por defecto
        base_url = os.getenv('DRACMAS_BRIDGE_URL', 'http://localhost:3000')
        api_key = os.getenv('DRACMAS_BRIDGE_API_KEY')

        _bridge_client = BridgeClient(base_url, api_key)
    return _bridge_client


def create_bridge_client(base_url: str, api_key: Optional[str] = None) -> BridgeClient:
    """Crear nueva instancia del cliente del puente."""
    return BridgeClient(base_url, api_key)
