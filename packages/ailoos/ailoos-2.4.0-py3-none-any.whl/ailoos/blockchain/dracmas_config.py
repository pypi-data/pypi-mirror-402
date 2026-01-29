"""
Configuración específica para integración DracmaS en Ailoos.

Contiene direcciones de contratos, endpoints RPC, configuración del puente
y parámetros de red para EmporioChain.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from urllib.parse import urlparse

from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DracmaSContractAddresses:
    """Direcciones de contratos principales en EmporioChain."""
    token_contract: str = "emp1dracmascontract"
    ailoos_contract: str = "emp1ailooscontract"
    pool_address: str = "emp1ailoospool"

    def validate_addresses(self) -> bool:
        """Valida que las direcciones tengan formato correcto de CosmWasm."""
        for field_name, address in self.__dict__.items():
            if not address.startswith('emp1'):
                logger.error(f"Dirección inválida para {field_name}: {address}")
                return False
            if len(address) != 45:  # Longitud típica de direcciones emp1
                logger.warning(f"Dirección {field_name} tiene longitud inusual: {len(address)}")
        return True


@dataclass
class EmporioChainConfig:
    """Configuración de red para EmporioChain."""
    rpc_url: str = "https://rpc.empooriochain.dev:443"
    chain_id: str = "emporiochain-1"
    gas_price: str = "0.025uemp"
    gas_limit: int = 200000
    timeout: int = 30

    def validate_rpc_url(self) -> bool:
        """Valida que la URL RPC sea válida."""
        try:
            parsed = urlparse(self.rpc_url)
            if parsed.scheme not in ['http', 'https']:
                logger.error(f"Esquema inválido en RPC URL: {self.rpc_url}")
                return False
            if not parsed.netloc:
                logger.error(f"URL RPC inválida: {self.rpc_url}")
                return False
            return True
        except Exception as e:
            logger.error(f"Error validando RPC URL: {e}")
            return False


@dataclass
class BridgeConfig:
    """Configuración del puente cross-chain."""
    bridge_url: str = "http://localhost:3000"
    api_key: Optional[str] = None
    timeout: int = 30
    retry_attempts: int = 3
    backoff_factor: float = 1.0

    def validate_bridge_url(self) -> bool:
        """Valida que la URL del puente sea válida."""
        try:
            parsed = urlparse(self.bridge_url)
            if parsed.scheme not in ['http', 'https']:
                logger.error(f"Esquema inválido en bridge URL: {self.bridge_url}")
                return False
            if not parsed.netloc:
                logger.error(f"URL del puente inválida: {self.bridge_url}")
                return False
            return True
        except Exception as e:
            logger.error(f"Error validando bridge URL: {e}")
            return False


@dataclass
class DracmaSConfig:
    """Configuración completa para DracmaS."""
    contracts: DracmaSContractAddresses
    network: EmporioChainConfig
    bridge: BridgeConfig

    def __post_init__(self):
        """Validar configuración después de inicialización."""
        if not self.contracts.validate_addresses():
            raise ValueError("Direcciones de contratos inválidas")
        if not self.network.validate_rpc_url():
            raise ValueError("URL RPC inválida")
        if not self.bridge.validate_bridge_url():
            raise ValueError("URL del puente inválida")

    @classmethod
    def from_env(cls) -> 'DracmaSConfig':
        """Crea configuración desde variables de entorno."""
        contracts = DracmaSContractAddresses(
            token_contract=os.getenv('DRACMAS_TOKEN_CONTRACT', 'emp1dracmascontract'),
            ailoos_contract=os.getenv('DRACMAS_AILOOS_CONTRACT', 'emp1ailooscontract'),
            pool_address=os.getenv('DRACMAS_POOL_ADDRESS', 'emp1ailoospool')
        )

        network = EmporioChainConfig(
            rpc_url=os.getenv('EMPORIO_RPC_URL', 'https://rpc.empooriochain.dev:443')
        )

        bridge = BridgeConfig(
            bridge_url=os.getenv('DRACMAS_BRIDGE_URL', 'http://localhost:3000'),
            api_key=os.getenv('DRACMAS_BRIDGE_API_KEY')
        )

        return cls(contracts=contracts, network=network, bridge=bridge)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte configuración a diccionario."""
        return {
            'contracts': {
                'token_contract': self.contracts.token_contract,
                'ailoos_contract': self.contracts.ailoos_contract,
                'pool_address': self.contracts.pool_address
            },
            'network': {
                'rpc_url': self.network.rpc_url,
                'chain_id': self.network.chain_id,
                'gas_price': self.network.gas_price,
                'gas_limit': self.network.gas_limit,
                'timeout': self.network.timeout
            },
            'bridge': {
                'bridge_url': self.bridge.bridge_url,
                'api_key': self.bridge.api_key,
                'timeout': self.bridge.timeout,
                'retry_attempts': self.bridge.retry_attempts,
                'backoff_factor': self.bridge.backoff_factor
            }
        }


# Instancia global de configuración
_dracmas_config: Optional[DracmaSConfig] = None


def get_dracmas_config() -> DracmaSConfig:
    """Obtiene instancia global de configuración DracmaS."""
    global _dracmas_config
    if _dracmas_config is None:
        _dracmas_config = DracmaSConfig.from_env()
        logger.info("✅ DracmaS configuration loaded from environment")
    return _dracmas_config


def reload_dracmas_config() -> DracmaSConfig:
    """Recarga configuración desde variables de entorno."""
    global _dracmas_config
    _dracmas_config = DracmaSConfig.from_env()
    logger.info("🔄 DracmaS configuration reloaded")
    return _dracmas_config


# Configuración por defecto para desarrollo/testing
DEFAULT_DRACMAS_CONFIG = DracmaSConfig(
    contracts=DracmaSContractAddresses(),
    network=EmporioChainConfig(),
    bridge=BridgeConfig()
)