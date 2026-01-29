import asyncio
import logging
import os
from typing import Dict, Any, Optional, List
from decimal import Decimal
from yapapi import Golem
from yapapi.services import Service
from yapapi.payload import vm
from yapapi.rest.activity import BatchError
from yapapi.log import enable_default_logger


class GolemClient:
    """
    Cliente para computación distribuida en la red Golem.
    Maneja ejecución de tareas, verificación de resultados, gestión de costos,
    con logging y manejo de errores robusto.
    """

    def __init__(self,
                 app_key: str = None,
                 subnet_tag: str = "public",
                 driver: str = "erc20",
                 network: str = "holesky",
                 budget: Decimal = Decimal("10.0"),
                 log_level: int = logging.INFO):
        """
        Inicializa el cliente Golem.

        Args:
            app_key: Clave de aplicación de Golem (opcional, usa env var)
            subnet_tag: Etiqueta de subred
            driver: Driver de pago
            network: Red blockchain
            budget: Presupuesto máximo por tarea
            log_level: Nivel de logging
        """
        self.app_key = app_key or os.getenv("GOLEM_APP_KEY")
        if not self.app_key:
            raise ValueError("GOLEM_APP_KEY no configurada")

        self.subnet_tag = subnet_tag
        self.driver = driver
        self.network = network
        self.budget = budget

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

        self.logger.info("Cliente Golem inicializado")

    async def execute_task(self,
                          image_hash: str,
                          task_commands: List[str],
                          timeout: int = 300) -> Dict[str, Any]:
        """
        Ejecuta una tarea en la red Golem.

        Args:
            image_hash: Hash de la imagen Docker
            task_commands: Lista de comandos a ejecutar
            timeout: Timeout en segundos

        Returns:
            Dict con resultado de la tarea
        """
        try:
            self.logger.info(f"Ejecutando tarea con imagen {image_hash}")

            async with Golem(
                budget=self.budget,
                subnet_tag=self.subnet_tag,
                driver=self.driver,
                network=self.network,
            ) as golem:

                # Crear payload
                payload = await vm.repo(
                    image_hash=image_hash,
                    min_mem_gib=0.5,
                    min_storage_gib=2.0,
                )

                # Ejecutar tarea
                async for task in golem.execute_tasks(
                    task_commands,
                    payload=payload,
                    max_workers=1,
                    timeout=timeout,
                ):
                    try:
                        result = await task
                        cost = task.cost
                        self.total_cost += cost
                        self.task_count += 1

                        self.logger.info(
                            f"Tarea completada. Costo: {cost}, Total acumulado: {self.total_cost}"
                        )

                        return {
                            "success": True,
                            "result": result,
                            "cost": float(cost),
                            "task_id": task.id,
                        }

                    except BatchError as e:
                        self.logger.error(f"Error en batch de tarea: {e}")
                        return {
                            "success": False,
                            "error": str(e),
                            "cost": 0.0,
                        }

        except Exception as e:
            self.logger.error(f"Error ejecutando tarea: {e}")
            return {
                "success": False,
                "error": str(e),
                "cost": 0.0,
            }

    def verify_result(self, result: Dict[str, Any], expected_output: Any = None) -> bool:
        """
        Verifica el resultado de una tarea.

        Args:
            result: Resultado de la tarea
            expected_output: Salida esperada (opcional)

        Returns:
            True si válido, False si no
        """
        try:
            if not result.get("success", False):
                self.logger.warning("Resultado indica fallo")
                return False

            if expected_output is not None:
                # Verificación básica - puede extenderse
                if result.get("result") != expected_output:
                    self.logger.warning("Resultado no coincide con esperado")
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

    async def close(self):
        """Cierra conexiones y recursos."""
        self.logger.info("Cliente Golem cerrado")


# Ejemplo de uso
async def main():
    client = GolemClient()

    # Ejemplo de tarea simple
    result = await client.execute_task(
        image_hash="9a3b5d67b0b27746283cb5f287c13eab1beaa12d92a9f536b747c7ae",
        task_commands=["echo 'Hello from Golem!'"],
    )

    print(f"Resultado: {result}")
    print(f"Estadísticas: {client.get_cost_stats()}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())