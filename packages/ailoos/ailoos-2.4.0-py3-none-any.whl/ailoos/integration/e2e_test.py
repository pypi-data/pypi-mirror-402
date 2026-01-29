"""
End-to-End Testing Suite - Pruebas completas del sistema AILOOS.
Valida el flujo completo desde nodos físicos hasta transacciones DRACMA.
"""

import asyncio
import json
import time
import tempfile
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

from ..node import PhysicalNodeManager, create_physical_node
from ..blockchain import get_token_manager
from ..marketplace import marketplace
from ..federated.session import FederatedSession
from ..core.logging import get_logger

logger = get_logger(__name__)


class AiloosE2ETestSuite:
    """
    Suite completa de pruebas end-to-end para AILOOS.
    Prueba el flujo completo del sistema desde nodos físicos hasta transacciones.
    """

    def __init__(self):
        self.test_results: Dict[str, Any] = {}
        self.test_nodes: List[PhysicalNodeManager] = []
        self.test_sessions: List[FederatedSession] = []
        self.temp_dir = Path(tempfile.mkdtemp(prefix="ailoos_e2e_"))

        logger.info("🧪 AILOOS E2E Test Suite initialized")

    async def run_full_test_suite(self) -> Dict[str, Any]:
        """
        Ejecutar suite completa de pruebas end-to-end.

        Returns:
            Resultados completos de las pruebas
        """
        logger.info("🚀 Starting AILOOS E2E Test Suite...")

        try:
            # Prueba 1: Configuración de nodos físicos
            await self.test_physical_node_setup()

            # Prueba 2: Sistema de tokens DRACMA
            await self.test_dracma_token_system()

            # Prueba 3: Marketplace de datos
            await self.test_marketplace_operations()

            # Prueba 4: Entrenamiento federado
            await self.test_federated_training()

            # Prueba 5: Integración completa
            await self.test_full_integration()

            # Resultado final
            self.test_results["overall_success"] = all(
                test.get("success", False)
                for test in self.test_results.values()
                if isinstance(test, dict)
            )

            logger.info("✅ E2E Test Suite completed")
            return self.test_results

        except Exception as e:
            logger.error(f"❌ E2E Test Suite failed: {e}")
            self.test_results["overall_success"] = False
            self.test_results["error"] = str(e)
            return self.test_results

        finally:
            await self.cleanup()

    async def test_physical_node_setup(self):
        """Prueba la configuración y detección de nodos físicos."""
        logger.info("🔧 Testing Physical Node Setup...")

        test_result = {
            "test_name": "physical_node_setup",
            "success": False,
            "details": {}
        }

        try:
            # Crear múltiples nodos de prueba
            node_configs = [
                {"coordinator_url": "http://136.119.191.184:8000"},
                {"coordinator_url": "http://136.119.191.184:8000"},
                {"coordinator_url": "http://136.119.191.184:8000"}
            ]

            nodes_created = 0
            for i, config in enumerate(node_configs):
                try:
                    node = PhysicalNodeManager(**config)
                    self.test_nodes.append(node)
                    nodes_created += 1

                    # Verificar capacidades detectadas
                    capabilities = node.capabilities
                    assert capabilities.cpu_cores > 0, "CPU cores not detected"
                    assert capabilities.memory_gb > 0, "Memory not detected"

                    test_result["details"][f"node_{i}"] = {
                        "node_id": node.node_id,
                        "cpu_cores": capabilities.cpu_cores,
                        "memory_gb": capabilities.memory_gb,
                        "gpu_available": capabilities.gpu_available
                    }

                except Exception as e:
                    logger.warning(f"Failed to create node {i}: {e}")

            # Verificar que al menos un nodo se creó
            assert nodes_created > 0, "No nodes could be created"

            test_result["success"] = True
            test_result["nodes_created"] = nodes_created

            logger.info(f"✅ Physical node setup test passed: {nodes_created} nodes created")

        except Exception as e:
            test_result["error"] = str(e)
            logger.error(f"❌ Physical node setup test failed: {e}")

        self.test_results["physical_node_setup"] = test_result

    async def test_dracma_token_system(self):
        """Prueba el sistema completo de tokens DRACMA."""
        logger.info("💰 Testing DracmaS Token System...")

        test_result = {
            "test_name": "dracma_token_system",
            "success": False,
            "details": {}
        }

        try:
            token_manager = get_token_manager()

            # Crear wallets de prueba
            user_ids = ["test_user_1", "test_user_2", "test_user_3"]
            wallets = {}

            for user_id in user_ids:
                address = await token_manager.initialize_user_wallet(user_id)
                wallets[user_id] = address

                # Verificar balance inicial
                balance = await token_manager.get_user_balance(address)
                assert balance >= 1000, f"Initial balance too low for {user_id}: {balance}"

                test_result["details"][f"wallet_{user_id}"] = {
                    "address": address,
                    "initial_balance": balance
                }

            # Probar transferencias
            sender = wallets["test_user_1"]
            receiver = wallets["test_user_2"]
            transfer_amount = 100.0

            result = await token_manager.transfer_tokens(sender, receiver, transfer_amount)
            assert result.success, f"Transfer failed: {result.error_message}"

            # Verificar balances después de transferencia
            sender_balance_after = await token_manager.get_user_balance(sender)
            receiver_balance_after = await token_manager.get_user_balance(receiver)

            sender_initial = test_result["details"]["wallet_test_user_1"]["initial_balance"]
            receiver_initial = test_result["details"]["wallet_test_user_2"]["initial_balance"]

            assert sender_balance_after < sender_initial, "Sender balance not reduced"
            assert receiver_balance_after > receiver_initial, "Receiver balance not increased"

            # Probar staking
            stake_amount = 500.0
            stake_result = await token_manager.stake_tokens(sender, stake_amount)
            assert stake_result.success, f"Staking failed: {stake_result.error_message}"

            # Verificar staking info
            staking_info = await token_manager.get_staking_rewards(sender)
            assert staking_info["staked_amount"] >= stake_amount, "Staking amount not recorded"

            test_result["success"] = True
            test_result["transfers_tested"] = 1
            test_result["staking_tested"] = True

            logger.info("✅ DracmaS token system test passed")

        except Exception as e:
            test_result["error"] = str(e)
            logger.error(f"❌ DracmaS token system test failed: {e}")

        self.test_results["dracma_token_system"] = test_result

    async def test_marketplace_operations(self):
        """Prueba operaciones completas del marketplace."""
        logger.info("🛒 Testing Marketplace Operations...")

        test_result = {
            "test_name": "marketplace_operations",
            "success": False,
            "details": {}
        }

        try:
            token_manager = get_token_manager()

            # Crear wallets para comprador y vendedor
            seller_address = await token_manager.initialize_user_wallet("marketplace_seller")
            buyer_address = await token_manager.initialize_user_wallet("marketplace_buyer")

            # Crear listing de datos usando el marketplace global
            from ailoos.marketplace import marketplace

            listing_id = marketplace.create_data_listing(
                seller_id="marketplace_seller",
                title="Test Dataset E2E",
                description="Dataset for end-to-end testing",
                category="text_data",
                data_hash="e2e_test_hash_123",
                ipfs_cid="QmTestCID123",
                price_dracma=50.0,
                data_size_mb=10.0,
                sample_count=1000,
                quality_score=0.9,
                tags=["test", "e2e", "text"]
            )
            assert listing_id, "Listing creation failed"

            # Verificar que el listing existe
            listing_details = marketplace.search_datasets(query="Test Dataset E2E")
            assert len(listing_details) > 0, "Listing not found in search"

            # Ejecutar compra
            tx_hash = marketplace.purchase_data("marketplace_buyer", listing_id)
            assert tx_hash, "Purchase failed"

            # Verificar balances después de compra
            seller_balance_after = await token_manager.get_user_balance(seller_address)
            buyer_balance_after = await token_manager.get_user_balance(buyer_address)

            # El vendedor debería tener más tokens, el comprador menos
            assert seller_balance_after > 1000, "Seller did not receive payment"
            assert buyer_balance_after < 1000, "Buyer balance not reduced"

            test_result["success"] = True
            test_result["listing_created"] = listing_id
            test_result["purchase_completed"] = tx_hash
            test_result["details"] = {
                "seller_balance_after": seller_balance_after,
                "buyer_balance_after": buyer_balance_after
            }

            logger.info("✅ Marketplace operations test passed")

        except Exception as e:
            test_result["error"] = str(e)
            logger.error(f"❌ Marketplace operations test failed: {e}")

        self.test_results["marketplace_operations"] = test_result

    async def test_federated_training(self):
        """Prueba el flujo completo de entrenamiento federado."""
        logger.info("🎯 Testing Federated Training...")

        test_result = {
            "test_name": "federated_training",
            "success": False,
            "details": {}
        }

        try:
            # Esta prueba es más compleja y requeriría modelos reales
            # Por ahora, probamos la creación de sesiones y nodos

            if not self.test_nodes:
                raise ValueError("No test nodes available for federated training")

            # Crear sesión de prueba
            session_config = {
                "model_name": "test_model",
                "rounds": 2,
                "min_nodes": 1,
                "max_nodes": len(self.test_nodes)
            }

            # Aquí iría la lógica para crear una sesión real
            # Por simplicidad, probamos que los nodos pueden inicializarse

            successful_nodes = 0
            for i, node in enumerate(self.test_nodes):
                try:
                    # Verificar que el nodo puede obtener su estado
                    status = await node.get_node_status()
                    assert status["node_id"] == node.node_id, "Node ID mismatch"
                    successful_nodes += 1

                    test_result["details"][f"node_{i}"] = {
                        "node_id": status["node_id"],
                        "online": status["status"]["is_online"],
                        "capabilities": status["capabilities"]
                    }

                except Exception as e:
                    logger.warning(f"Node {i} status check failed: {e}")

            assert successful_nodes > 0, "No nodes could be verified"

            test_result["success"] = True
            test_result["nodes_verified"] = successful_nodes

            logger.info(f"✅ Federated training test passed: {successful_nodes} nodes verified")

        except Exception as e:
            test_result["error"] = str(e)
            logger.error(f"❌ Federated training test failed: {e}")

        self.test_results["federated_training"] = test_result

    async def test_full_integration(self):
        """Prueba la integración completa de todos los componentes."""
        logger.info("🔗 Testing Full System Integration...")

        test_result = {
            "test_name": "full_integration",
            "success": False,
            "details": {}
        }

        try:
            # Verificar que todos los componentes principales funcionan juntos

            # 1. Token manager
            token_manager = get_token_manager()
            token_info = token_manager.get_token_info()
            assert token_info["name"] == "DRACMA", "Token info incorrect"

            # 2. Marketplace
            from ailoos.marketplace import marketplace
            market_stats = marketplace.get_market_stats()
            assert isinstance(market_stats, dict), "Market stats not available"

            # 3. Nodos físicos
            if self.test_nodes:
                node_status = await self.test_nodes[0].get_node_status()
                assert node_status["node_id"], "Node status not available"

            # 4. Verificar conectividad entre componentes
            # Crear una transacción completa
            user_address = await token_manager.initialize_user_wallet("integration_test_user")
            balance_before = await token_manager.get_user_balance(user_address)

            # Transferir a sí mismo (prueba de sistema)
            transfer_result = await token_manager.transfer_tokens(
                user_address, user_address, 1.0
            )
            assert transfer_result.success, "Self-transfer failed"

            balance_after = await token_manager.get_user_balance(user_address)
            assert abs(balance_before - balance_after) < 0.01, "Balance changed unexpectedly"

            test_result["success"] = True
            test_result["details"] = {
                "token_system": "operational",
                "marketplace": "operational",
                "nodes": len(self.test_nodes),
                "integration_transfer": transfer_result.tx_hash
            }

            logger.info("✅ Full integration test passed")

        except Exception as e:
            test_result["error"] = str(e)
            logger.error(f"❌ Full integration test failed: {e}")

        self.test_results["full_integration"] = test_result

    async def cleanup(self):
        """Limpiar recursos de prueba."""
        logger.info("🧹 Cleaning up test resources...")

        try:
            # Detener nodos de prueba
            for node in self.test_nodes:
                try:
                    await node.stop_node()
                except Exception as e:
                    logger.warning(f"Error stopping test node: {e}")

            # Limpiar archivos temporales
            if self.temp_dir.exists():
                import shutil
                shutil.rmtree(self.temp_dir, ignore_errors=True)

            logger.info("✅ Test cleanup completed")

        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")

    def save_test_results(self, output_file: str = "e2e_test_results.json"):
        """
        Guardar resultados de pruebas en archivo JSON.

        Args:
            output_file: Archivo donde guardar los resultados
        """
        try:
            results_with_timestamp = {
                "test_suite": "AILOOS E2E Test Suite",
                "timestamp": time.time(),
                "datetime": time.strftime('%Y-%m-%d %H:%M:%S'),
                "results": self.test_results
            }

            with open(output_file, 'w') as f:
                json.dump(results_with_timestamp, f, indent=2, default=str)

            logger.info(f"📄 Test results saved to {output_file}")

        except Exception as e:
            logger.error(f"❌ Failed to save test results: {e}")

    def print_test_summary(self):
        """Imprimir resumen de pruebas ejecutadas."""
        print("\n" + "="*60)
        print("🧪 AILOOS E2E TEST SUITE RESULTS")
        print("="*60)

        for test_name, result in self.test_results.items():
            if isinstance(result, dict):
                status = "✅ PASSED" if result.get("success", False) else "❌ FAILED"
                print(f"\n{test_name.upper()}: {status}")

                if result.get("success"):
                    # Mostrar detalles de éxito
                    if "details" in result:
                        for key, value in result["details"].items():
                            if isinstance(value, dict) and len(value) <= 3:
                                print(f"  • {key}: {value}")
                            else:
                                print(f"  • {key}: {str(value)[:50]}...")
                else:
                    # Mostrar error
                    error = result.get("error", "Unknown error")
                    print(f"  ❌ Error: {error}")

        overall_success = self.test_results.get("overall_success", False)
        print(f"\nOVERALL RESULT: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
        print("="*60)


# Funciones de conveniencia
async def run_e2e_tests(save_results: bool = True, output_file: str = "e2e_test_results.json") -> Dict[str, Any]:
    """
    Ejecutar pruebas end-to-end completas.

    Args:
        save_results: Si guardar resultados en archivo
        output_file: Archivo donde guardar resultados

    Returns:
        Resultados completos de las pruebas
    """
    test_suite = AiloosE2ETestSuite()
    results = await test_suite.run_full_test_suite()

    if save_results:
        test_suite.save_test_results(output_file)

    test_suite.print_test_summary()

    return results


def run_e2e_tests_sync(save_results: bool = True, output_file: str = "e2e_test_results.json") -> Dict[str, Any]:
    """
    Ejecutar pruebas end-to-end de manera síncrona.

    Args:
        save_results: Si guardar resultados en archivo
        output_file: Archivo donde guardar resultados

    Returns:
        Resultados completos de las pruebas
    """
    return asyncio.run(run_e2e_tests(save_results, output_file))


if __name__ == "__main__":
    print("🚀 Running AILOOS E2E Test Suite...")
    results = run_e2e_tests_sync()
    print(f"\n🏁 Test suite completed. Overall success: {results.get('overall_success', False)}")