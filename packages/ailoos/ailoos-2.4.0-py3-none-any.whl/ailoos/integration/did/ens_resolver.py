import logging
from typing import Optional

try:
    from web3 import Web3
    from web3.exceptions import ContractLogicError, InvalidAddress
except ImportError:  # Legacy EVM integration (EmpoorioChain usa bridge)
    Web3 = None
    ContractLogicError = InvalidAddress = Exception

class ENSResolver:
    """
    Cliente para resolución de nombres ENS (.eth) usando Web3.
    Proporciona métodos para resolver nombres a direcciones y viceversa.
    """
    LEGACY_MESSAGE = (
        "Integracion ENS legacy. Ailoos usa EmpoorioChain + DracmaSToken via bridge."
    )

    def __init__(self, rpc_url: str = "https://mainnet.infura.io/v3/YOUR_INFURA_KEY"):
        """
        Inicializa el resolvedor ENS.

        Args:
            rpc_url: URL del nodo Ethereum (mainnet por defecto)
        """
        raise NotImplementedError(self.LEGACY_MESSAGE)
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        self.logger = logging.getLogger(__name__)

        if not self.web3.is_connected():
            raise ConnectionError("No se pudo conectar al nodo Ethereum")

        self.logger.info("ENS Resolver inicializado exitosamente")

    def resolve_name(self, ens_name: str) -> Optional[str]:
        """
        Resuelve un nombre ENS a una dirección Ethereum.

        Args:
            ens_name: Nombre ENS (ej: "vitalik.eth")

        Returns:
            str: Dirección Ethereum si resuelta, None si no

        Raises:
            Exception: Si ocurre un error de conexión o formato
        """
        try:
            self.logger.info(f"Resolviendo nombre ENS: {ens_name}")

            if not ens_name.endswith('.eth'):
                ens_name += '.eth'

            # Resolver usando ENS
            address = self.web3.ens.address(ens_name)

            if address:
                self.logger.info(f"Nombre {ens_name} resuelto a: {address}")
                return address
            else:
                self.logger.warning(f"Nombre {ens_name} no encontrado")
                return None

        except ContractLogicError as e:
            self.logger.warning(f"Nombre ENS no registrado: {ens_name}")
            return None
        except InvalidAddress as e:
            self.logger.error(f"Dirección inválida para {ens_name}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error resolviendo nombre ENS: {e}")
            raise

    def resolve_address(self, address: str) -> Optional[str]:
        """
        Resuelve una dirección Ethereum a nombre ENS (reverse lookup).

        Args:
            address: Dirección Ethereum

        Returns:
            str: Nombre ENS si encontrado, None si no

        Raises:
            Exception: Si ocurre un error de conexión o formato
        """
        try:
            self.logger.info(f"Resolviendo dirección: {address}")

            # Validar dirección
            if not self.web3.is_address(address):
                raise ValueError(f"Dirección inválida: {address}")

            # Resolver reverse usando ENS
            ens_name = self.web3.ens.name(address)

            if ens_name:
                self.logger.info(f"Dirección {address} resuelta a: {ens_name}")
                return ens_name
            else:
                self.logger.warning(f"No se encontró nombre ENS para {address}")
                return None

        except ValueError as e:
            self.logger.error(f"Dirección inválida: {e}")
            raise
        except ContractLogicError as e:
            self.logger.warning(f"No hay nombre ENS para la dirección: {address}")
            return None
        except Exception as e:
            self.logger.error(f"Error resolviendo dirección: {e}")
            raise

    def is_valid_ens_name(self, ens_name: str) -> bool:
        """
        Verifica si un nombre ENS tiene formato válido.

        Args:
            ens_name: Nombre a verificar

        Returns:
            bool: True si válido
        """
        try:
            # Verificaciones básicas
            if not ens_name or len(ens_name) > 253:
                return False

            # Debe terminar en .eth o ser subdominio
            if not (ens_name.endswith('.eth') or '.' in ens_name):
                return False

            # Verificar caracteres válidos
            import re
            if not re.match(r'^[a-zA-Z0-9.-]+\.eth$', ens_name):
                return False

            return True

        except Exception:
            return False

    def get_text_record(self, ens_name: str, key: str) -> Optional[str]:
        """
        Obtiene un registro de texto de un nombre ENS.

        Args:
            ens_name: Nombre ENS
            key: Clave del registro (ej: "email", "url")

        Returns:
            str: Valor del registro si existe
        """
        try:
            self.logger.info(f"Obteniendo registro de texto '{key}' para {ens_name}")

            text_value = self.web3.ens.get_text(ens_name, key)

            if text_value:
                self.logger.info(f"Registro encontrado: {text_value}")
                return text_value
            else:
                self.logger.warning(f"Registro '{key}' no encontrado para {ens_name}")
                return None

        except Exception as e:
            self.logger.error(f"Error obteniendo registro de texto: {e}")
            return None

    def set_resolver(self, ens_name: str, resolver_address: str):
        """
        Establece el resolvedor para un nombre ENS (requiere ser propietario).

        Args:
            ens_name: Nombre ENS
            resolver_address: Dirección del nuevo resolvedor

        Raises:
            Exception: Si no se puede establecer
        """
        # Nota: Esto requiere transacción firmada, no implementado aquí
        # En producción, requeriría wallet y firma
        self.logger.warning("set_resolver no implementado - requiere transacción firmada")
        raise NotImplementedError("Funcionalidad requiere integración con wallet")
