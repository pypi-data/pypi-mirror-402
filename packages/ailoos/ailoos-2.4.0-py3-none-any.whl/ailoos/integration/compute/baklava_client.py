import logging
import os
import time
from typing import Dict, Any, Optional, List
from decimal import Decimal
from hexbytes import HexBytes

try:
    from web3 import Web3
    from eth_account import Account
except ImportError:  # Legacy EVM integration (EmpoorioChain usa bridge)
    Web3 = None
    Account = None


class BaklavaClient:
    """
    Cliente para computación distribuida en Baklava testnet (Celo).
    Maneja ejecución de tareas vía contratos inteligentes, verificación de resultados,
    gestión de costos, con logging y manejo de errores robusto.
    """
    LEGACY_MESSAGE = (
        "Integracion compute EVM legacy. Ailoos usa EmpoorioChain + DracmaSToken via bridge."
    )

    # Direcciones de contratos en Baklava (ejemplo - actualizar según despliegue)
    CONTRACTS = {
        "task_manager": "0x1234567890123456789012345678901234567890",  # Contrato de gestión de tareas
        "oracle": "0x0987654321098765432109876543210987654321",     # Oráculo para verificación
    }

    def __init__(self,
                 rpc_url: str = "https://baklava-forno.celo-testnet.org",
                 private_key: str = None,
                 chain_id: int = 62320,
                 log_level: int = logging.INFO):
        """
        Inicializa el cliente Baklava.

        Args:
            rpc_url: URL del RPC de Baklava
            private_key: Clave privada para transacciones
            chain_id: ID de la cadena (62320 para Baklava)
            log_level: Nivel de logging
        """
        raise NotImplementedError(self.LEGACY_MESSAGE)
        self.rpc_url = rpc_url
        self.private_key = private_key or os.getenv("BAKLAVA_PRIVATE_KEY")
        if not self.private_key:
            raise ValueError("BAKLAVA_PRIVATE_KEY no configurada")

        self.chain_id = chain_id

        # Conectar a Web3
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))

        if not self.w3.is_connected():
            raise ConnectionError("No se pudo conectar a Baklava testnet")

        # Cuenta
        self.account = Account.from_key(self.private_key)
        self.address = self.account.address

        # Configurar logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)

        # Estadísticas de costos
        self.total_cost = Decimal("0.0")
        self.task_count = 0

        self.logger.info(f"Cliente Baklava inicializado. Dirección: {self.address}")

    def _send_transaction(self, tx: Dict[str, Any]) -> str:
        """Envía una transacción y espera confirmación."""
        try:
            # Estimar gas
            gas_estimate = self.w3.eth.estimate_gas(tx)
            tx['gas'] = int(gas_estimate * 1.1)  # 10% buffer
            tx['gasPrice'] = self.w3.eth.gas_price

            # Firmar y enviar
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

            # Esperar confirmación
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status == 1:
                self.logger.info(f"Transacción confirmada: {tx_hash.hex()}")
                return tx_hash.hex()
            else:
                raise Exception(f"Transacción fallida: {tx_hash.hex()}")

        except Exception as e:
            self.logger.error(f"Error enviando transacción: {e}")
            raise

    def _get_contract(self, name: str, abi: List[Dict[str, Any]]) -> Any:
        """Obtiene instancia de contrato."""
        return self.w3.eth.contract(
            address=self.CONTRACTS[name],
            abi=abi
        )

    async def execute_task(self,
                          task_data: str,
                          reward_amount: int = 1000000000000000000,  # 1 CELO en wei
                          timeout: int = 300) -> Dict[str, Any]:
        """
        Ejecuta una tarea en Baklava vía contrato inteligente.

        Args:
            task_data: Datos de la tarea (JSON string)
            reward_amount: Recompensa en wei
            timeout: Timeout en segundos

        Returns:
            Dict con resultado de la tarea
        """
        try:
            self.logger.info(f"Ejecutando tarea: {task_data[:50]}...")

            # ABI simplificado del contrato TaskManager (ejemplo)
            task_manager_abi = [
                {
                    "inputs": [
                        {"internalType": "string", "name": "taskData", "type": "string"},
                        {"internalType": "uint256", "name": "reward", "type": "uint256"}
                    ],
                    "name": "submitTask",
                    "outputs": [{"internalType": "uint256", "name": "taskId", "type": "uint256"}],
                    "stateMutability": "payable",
                    "type": "function"
                },
                {
                    "inputs": [{"internalType": "uint256", "name": "taskId", "type": "uint256"}],
                    "name": "getTaskResult",
                    "outputs": [{"internalType": "string", "name": "", "type": "string"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]

            contract = self._get_contract("task_manager", task_manager_abi)

            # Enviar tarea
            tx = contract.functions.submitTask(task_data, reward_amount).build_transaction({
                'from': self.address,
                'value': reward_amount,
                'nonce': self.w3.eth.get_transaction_count(self.address),
            })

            tx_hash = self._send_transaction(tx)

            # Extraer task_id del evento (simplificado)
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            task_id = 1  # Simulado - en producción parsear logs

            # Esperar resultado (en producción, monitorear eventos o polling)
            start_time = time.time()
            result = None
            while time.time() - start_time < timeout:
                try:
                    result = contract.functions.getTaskResult(task_id).call()
                    if result:
                        break
                except:
                    pass
                time.sleep(5)

            if not result:
                raise TimeoutError("Timeout esperando resultado")

            cost = Decimal(str(self.w3.from_wei(reward_amount, 'ether')))
            self.total_cost += cost
            self.task_count += 1

            self.logger.info(
                f"Tarea completada. Task ID: {task_id}, Costo: {cost} CELO"
            )

            return {
                "success": True,
                "result": result,
                "task_id": task_id,
                "cost": float(cost),
                "tx_hash": tx_hash,
            }

        except Exception as e:
            self.logger.error(f"Error ejecutando tarea: {e}")
            return {
                "success": False,
                "error": str(e),
                "cost": 0.0,
            }

    def verify_result(self, result: Dict[str, Any], expected_hash: Optional[str] = None) -> bool:
        """
        Verifica el resultado de una tarea usando oráculo.

        Args:
            result: Resultado de la tarea
            expected_hash: Hash esperado (opcional)

        Returns:
            True si válido, False si no
        """
        try:
            if not result.get("success", False):
                self.logger.warning("Resultado indica fallo")
                return False

            # Verificación vía oráculo
            if expected_hash:
                oracle_abi = [
                    {
                        "inputs": [{"internalType": "bytes32", "name": "dataHash", "type": "bytes32"}],
                        "name": "verifyHash",
                        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                        "stateMutability": "view",
                        "type": "function"
                    }
                ]

                contract = self._get_contract("oracle", oracle_abi)
                data_hash = self.w3.keccak(text=result.get("result", ""))

                is_valid = contract.functions.verifyHash(data_hash).call()
                if not is_valid:
                    self.logger.warning("Verificación de oráculo fallida")
                    return False

            self.logger.info("Resultado verificado correctamente")
            return True

        except Exception as e:
            self.logger.error(f"Error verificando resultado: {e}")
            return False

    def get_cost_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de costos.

        Returns:
            Dict con estadísticas
        """
        return {
            "total_cost": float(self.total_cost),
            "task_count": self.task_count,
            "average_cost": float(self.total_cost / self.task_count) if self.task_count > 0 else 0.0,
        }

    def reset_cost_stats(self):
        """Reinicia estadísticas de costos."""
        self.total_cost = Decimal("0.0")
        self.task_count = 0
        self.logger.info("Estadísticas de costos reiniciadas")

    def close(self):
        """Cierra conexiones."""
        self.logger.info("Cliente Baklava cerrado")


# Ejemplo de uso
def main():
    client = BaklavaClient()

    # Ejemplo de tarea
    result = client.execute_task(
        task_data='{"command": "echo \'Hello from Baklava testnet!\'"}'
    )

    print(f"Resultado: {result}")
    print(f"Estadísticas: {client.get_cost_stats()}")

    client.close()


if __name__ == "__main__":
    main()
