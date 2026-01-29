"""
Ejemplo básico de uso del SDK de AILOOS
Demuestra cómo usar el NodeSDK para operaciones básicas.
"""

import asyncio
import json
import logging

from ..node_sdk import NodeSDK

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def basic_sdk_example():
    """
    Ejemplo básico de uso del NodeSDK.
    """
    print("🚀 AILOOS SDK - Ejemplo Básico")
    print("=" * 50)

    # Crear instancia del SDK
    sdk = NodeSDK(
        node_id="example_node_001",
        coordinator_url="http://localhost:5001"
    )

    try:
        # 1. Inicializar el SDK
        print("📋 Inicializando SDK...")
        success = await sdk.initialize()
        if not success:
            print("❌ Error inicializando SDK")
            return

        print("✅ SDK inicializado correctamente")

        # 2. Iniciar operaciones
        print("▶️ Iniciando operaciones...")
        await sdk.start()

        # 3. Autenticar el nodo
        print("🔐 Autenticando nodo...")
        auth_success = await sdk.authenticate()
        if auth_success:
            print("✅ Nodo autenticado")
        else:
            print("⚠️ Autenticación fallida (coordinador no disponible)")

        # 4. Obtener información del hardware
        print("💻 Información del hardware:")
        hardware = sdk.get_hardware_info()
        for key, value in hardware.items():
            print(f"  {key}: {value}")

        # 5. Obtener métricas del sistema
        print("📊 Métricas del sistema:")
        metrics = sdk.get_system_metrics()
        for key, value in metrics.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.1f}")
            else:
                print(f"  {key}: {value}")

        # 6. Buscar datasets en el marketplace
        print("🛒 Buscando datasets en marketplace...")
        try:
            datasets = await sdk.search_datasets(limit=3)
            if datasets:
                print(f"✅ Encontrados {len(datasets)} datasets:")
                for dataset in datasets[:3]:
                    print(f"  - {dataset.get('title', 'N/A')} ({dataset.get('price_dracma', 0)} DRACMA)")
            else:
                print("ℹ️ No se encontraron datasets (marketplace no disponible)")
        except Exception as e:
            print(f"⚠️ Error accediendo al marketplace: {e}")

        # 7. Obtener balance de wallet
        print("💰 Consultando balance de wallet...")
        try:
            balance = await sdk.get_wallet_balance()
            print(f"✅ Balance: {balance} DRACMA")
        except Exception as e:
            print(f"⚠️ Error obteniendo balance: {e}")

        # 8. Obtener estado del nodo
        print("📈 Estado del nodo:")
        status = sdk.get_status()
        print(f"  Node ID: {status['node_id']}")
        print(f"  Inicializado: {status['is_initialized']}")
        print(f"  Ejecutándose: {status['is_running']}")
        print(f"  P2P conectado: {status['p2p_connected']}")
        print(f"  Marketplace conectado: {status['marketplace_connected']}")

        # 9. Generar reporte de rendimiento
        print("📊 Generando reporte de rendimiento...")
        try:
            report = await sdk.get_performance_report()
            if 'averages' in report:
                print("  Promedios (última hora):")
                for key, value in report['averages'].items():
                    print(f"    {key}: {value}")
            if 'recommendations' in report:
                print("  Recomendaciones:")
                for rec in report['recommendations']:
                    print(f"    - {rec}")
        except Exception as e:
            print(f"⚠️ Error generando reporte: {e}")

        # 10. Esperar un poco para mostrar métricas en tiempo real
        print("⏳ Monitoreando por 10 segundos...")
        await asyncio.sleep(10)

        print("✅ Ejemplo completado exitosamente")

    except Exception as e:
        print(f"❌ Error en el ejemplo: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Limpiar
        print("🧹 Limpiando recursos...")
        await sdk.shutdown()
        print("✅ SDK cerrado")


async def federated_learning_example():
    """
    Ejemplo de participación en aprendizaje federado.
    """
    print("\n🔄 AILOOS SDK - Ejemplo de Federated Learning")
    print("=" * 50)

    # Crear instancia del SDK
    sdk = NodeSDK(
        node_id="federated_node_001",
        coordinator_url="http://localhost:5001"
    )

    try:
        # Inicializar
        await sdk.initialize()
        await sdk.start()

        # Simular pesos de modelo (en la práctica vendrían de tu modelo ML)
        model_weights = {
            "layer1": {"weights": [0.1, 0.2, 0.3], "bias": [0.0]},
            "layer2": {"weights": [0.4, 0.5], "bias": [0.1]},
        }

        # Unirse a una sesión federada
        print("🤝 Uniéndose a sesión federada...")
        session_joined = await sdk.join_federated_session("session_demo_001")
        if session_joined:
            print("✅ Unido a sesión federada")

            # Enviar actualización de modelo
            print("📤 Enviando actualización de modelo...")
            update_sent = await sdk.participate_in_round(
                session_id="session_demo_001",
                model_weights=model_weights,
                metadata={
                    "accuracy": 0.85,
                    "loss": 0.234,
                    "num_samples": 1000,
                    "epoch": 5
                }
            )

            if update_sent:
                print("✅ Actualización enviada")
            else:
                print("⚠️ Error enviando actualización")

            # Obtener información de ronda
            print("📊 Obteniendo información de ronda...")
            round_info = await sdk.get_round_info("session_demo_001")
            if round_info:
                print(f"  Ronda actual: {round_info.get('round_num', 'N/A')}")
                print(f"  Participantes: {len(round_info.get('participants', []))}")
            else:
                print("⚠️ No se pudo obtener información de ronda")

        else:
            print("⚠️ No se pudo unir a sesión (coordinador no disponible)")

        # Simular espera de nueva ronda
        print("⏳ Esperando nueva ronda...")
        await asyncio.sleep(5)

    except Exception as e:
        print(f"❌ Error en ejemplo federado: {e}")

    finally:
        await sdk.shutdown()


async def marketplace_example():
    """
    Ejemplo de uso del marketplace.
    """
    print("\n🛒 AILOOS SDK - Ejemplo de Marketplace")
    print("=" * 50)

    # Crear instancia del SDK
    sdk = NodeSDK(
        node_id="marketplace_node_001",
        coordinator_url="http://localhost:5001"
    )

    try:
        # Inicializar
        await sdk.initialize()
        await sdk.start()

        # Ver balance inicial
        balance = await sdk.get_wallet_balance()
        print(f"💰 Balance inicial: {balance} DRACMA")

        # Buscar datasets
        print("🔍 Buscando datasets de machine learning...")
        datasets = await sdk.search_datasets(
            query="machine learning",
            category="ml",
            limit=5
        )

        if datasets:
            print(f"✅ Encontrados {len(datasets)} datasets:")
            for i, dataset in enumerate(datasets, 1):
                print(f"  {i}. {dataset.get('title')} - {dataset.get('price_dracma')} DRACMA")
                print(f"     Categoría: {dataset.get('category')}, Calidad: {dataset.get('quality_score')}")

            # Intentar comprar el primer dataset
            if datasets:
                first_dataset = datasets[0]
                listing_id = first_dataset.get('listing_id')
                price = first_dataset.get('price_dracma', 0)

                print(f"🛒 Intentando comprar: {first_dataset.get('title')}")
                if balance >= price:
                    purchase_success = await sdk.purchase_data(listing_id)
                    if purchase_success:
                        print("✅ Compra exitosa!")
                        new_balance = await sdk.get_wallet_balance()
                        print(f"💰 Nuevo balance: {new_balance} DRACMA")
                    else:
                        print("⚠️ Error en la compra")
                else:
                    print(f"⚠️ Balance insuficiente ({balance} < {price})")
        else:
            print("ℹ️ No se encontraron datasets")

        # Ver historial de transacciones
        print("📜 Historial de transacciones:")
        try:
            transactions = await sdk.get_transaction_history(limit=5)
            if transactions:
                for tx in transactions:
                    print(f"  {tx.get('type', 'N/A')}: {tx.get('amount', 0)} DracmaS - {tx.get('status', 'N/A')}")
            else:
                print("  No hay transacciones")
        except Exception as e:
            print(f"⚠️ Error obteniendo historial: {e}")

    except Exception as e:
        print(f"❌ Error en ejemplo de marketplace: {e}")

    finally:
        await sdk.shutdown()


async def main():
    """
    Función principal que ejecuta todos los ejemplos.
    """
    print("🎯 AILOOS Federated Learning SDK - Ejemplos de Uso")
    print("=" * 60)

    # Ejecutar ejemplos
    await basic_sdk_example()
    await federated_learning_example()
    await marketplace_example()

    print("\n🎉 Todos los ejemplos completados!")
    print("\n💡 Para más información, consulta la documentación del SDK.")


if __name__ == "__main__":
    # Ejecutar ejemplos
    asyncio.run(main())