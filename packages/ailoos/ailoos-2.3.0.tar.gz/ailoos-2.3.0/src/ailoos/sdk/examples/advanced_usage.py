"""
Ejemplos avanzados de uso del SDK de AILOOS
Demuestra funcionalidades avanzadas como P2P, modelos personalizados, etc.
"""

import asyncio
import json
import logging
import numpy as np
from typing import Dict, Any

from ..node_sdk import NodeSDK
from ..federated_client import RoundUpdate

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CustomModelTrainer:
    """
    Ejemplo de entrenador de modelo personalizado que integra con el SDK.
    """

    def __init__(self, sdk: NodeSDK, session_id: str):
        self.sdk = sdk
        self.session_id = session_id
        self.model_weights = self._initialize_model()

    def _initialize_model(self) -> Dict[str, Any]:
        """Inicializar pesos del modelo."""
        return {
            "conv1": {
                "weights": np.random.randn(32, 3, 3, 3).tolist(),
                "bias": np.zeros(32).tolist()
            },
            "conv2": {
                "weights": np.random.randn(64, 32, 3, 3).tolist(),
                "bias": np.zeros(64).tolist()
            },
            "fc1": {
                "weights": np.random.randn(128, 1024).tolist(),
                "bias": np.zeros(128).tolist()
            },
            "fc2": {
                "weights": np.random.randn(10, 128).tolist(),
                "bias": np.zeros(10).tolist()
            }
        }

    async def train_epoch(self, num_epochs: int = 1) -> Dict[str, Any]:
        """
        Simular entrenamiento de una epoch.

        Returns:
            Métricas de entrenamiento
        """
        print(f"🎓 Entrenando modelo por {num_epochs} epochs...")

        # Simular entrenamiento
        for epoch in range(num_epochs):
            # Simular pérdida decreciente
            loss = 2.5 * np.exp(-epoch * 0.1)
            accuracy = 0.1 + (1 - 0.1) * (1 - np.exp(-epoch * 0.2))

            # Actualizar pesos (simulación)
            for layer_name in self.model_weights:
                layer = self.model_weights[layer_name]
                # Simular actualización de gradientes
                noise = np.random.normal(0, 0.01, size=np.array(layer["weights"]).shape)
                layer["weights"] = (np.array(layer["weights"]) - 0.01 * noise).tolist()

            print(f"    Epoch {epoch+1}: Loss={loss:.4f}, Accuracy={accuracy:.4f}")
        return {
            "final_loss": loss,
            "final_accuracy": accuracy,
            "epochs_trained": num_epochs
        }

    async def participate_in_federated_round(self, round_num: int) -> bool:
        """
        Participar en una ronda federada con el modelo entrenado.

        Args:
            round_num: Número de ronda

        Returns:
            True si la participación fue exitosa
        """
        print(f"🔄 Participando en ronda federada {round_num}...")

        # Entrenar modelo localmente
        metrics = await self.train_epoch(num_epochs=2)

        # Enviar actualización al coordinador
        success = await self.sdk.participate_in_round(
            session_id=self.session_id,
            model_weights=self.model_weights,
            metadata={
                "round_num": round_num,
                "accuracy": metrics["final_accuracy"],
                "loss": metrics["final_loss"],
                "epochs_trained": metrics["epochs_trained"],
                "num_samples": 1000,
                "model_type": "cnn",
                "framework": "custom"
            }
        )

        if success:
            print("✅ Actualización federada enviada exitosamente"
        else:
            print("❌ Error enviando actualización federada"
        return success

    async def receive_global_model(self) -> bool:
        """
        Recibir modelo global actualizado.

        Returns:
            True si se recibió el modelo
        """
        print("📥 Recibiendo modelo global...")

        global_model = await self.sdk.get_global_model(self.session_id)
        if global_model:
            # Actualizar pesos locales con modelo global
            self.model_weights = global_model["weights"]
            print("✅ Modelo global recibido y aplicado")
            return True
        else:
            print("⚠️ No se pudo obtener modelo global")
            return False


async def advanced_federated_example():
    """
    Ejemplo avanzado de federated learning con modelo personalizado.
    """
    print("🔬 AILOOS SDK - Ejemplo Avanzado de Federated Learning")
    print("=" * 60)

    # Crear SDK
    sdk = NodeSDK(
        node_id="advanced_federated_node_001",
        coordinator_url="http://localhost:5001"
    )

    try:
        # Inicializar SDK
        await sdk.initialize()
        await sdk.start()

        # Crear entrenador personalizado
        trainer = CustomModelTrainer(sdk, "advanced_session_001")

        # Unirse a sesión federada
        print("🤝 Uniéndose a sesión federada avanzada...")
        joined = await sdk.join_federated_session("advanced_session_001")

        if joined:
            print("✅ Unido a sesión federada")

            # Simular múltiples rondas
            for round_num in range(1, 4):
                print(f"\n🎯 RONDA {round_num}")
                print("-" * 20)

                # Participar en ronda
                await trainer.participate_in_federated_round(round_num)

                # Esperar un poco
                await asyncio.sleep(2)

                # Recibir modelo global (en ronda real vendría del coordinador)
                await trainer.receive_global_model()

                # Mostrar métricas del sistema
                metrics = sdk.get_system_metrics()
                print(".1f"
                # Pequeña pausa entre rondas
                await asyncio.sleep(3)

            print("\n🏆 Entrenamiento federado completado!")

        else:
            print("⚠️ No se pudo unir a sesión (coordinador no disponible)")
            print("💡 Ejecutando modo simulado...")

            # Modo simulado sin coordinador
            for round_num in range(1, 3):
                print(f"\n🎯 RONDA SIMULADA {round_num}")
                await trainer.participate_in_federated_round(round_num)
                await asyncio.sleep(2)

    except Exception as e:
        print(f"❌ Error en ejemplo avanzado: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await sdk.shutdown()


async def p2p_communication_example():
    """
    Ejemplo de comunicación P2P directa entre nodos.
    """
    print("\n🌐 AILOOS SDK - Ejemplo de Comunicación P2P")
    print("=" * 50)

    # Crear SDK
    sdk = NodeSDK(
        node_id="p2p_node_001",
        coordinator_url="http://localhost:5001"
    )

    try:
        # Inicializar SDK
        await sdk.initialize()
        await sdk.start()

        # Conectar a peers (en producción tendrías direcciones reales)
        print("🔗 Intentando conectar a peers P2P...")

        # Para demo, intentar conectar a localhost (no funcionará sin peers reales)
        connected = await sdk.connect_to_peer("127.0.0.1", 8444)
        if connected:
            print("✅ Conectado a peer P2P")

            # Enviar mensaje de prueba
            test_message = {
                "type": "test",
                "content": "Hola desde AILOOS SDK!",
                "timestamp": asyncio.get_event_loop().time()
            }

            sent = await sdk.send_p2p_message("peer_127.0.0.1_8444", test_message)
            if sent:
                print("📤 Mensaje P2P enviado")
            else:
                print("⚠️ Error enviando mensaje P2P")

        else:
            print("⚠️ No se pudo conectar a peers P2P (normal en entorno de prueba)")

        # Mostrar peers conectados
        peers = sdk.get_connected_peers()
        print(f"📊 Peers conectados: {len(peers)}")
        if peers:
            for peer in peers:
                peer_info = sdk.get_peer_info(peer)
                if peer_info:
                    print(f"  - {peer}: {peer_info.get('host')}:{peer_info.get('port')}")

        # Broadcast de mensaje
        broadcast_message = {
            "type": "announcement",
            "content": "Nodo AILOOS SDK activo",
            "capabilities": ["federated_learning", "model_sharing"]
        }

        broadcast_count = await sdk.broadcast_message(broadcast_message)
        print(f"📢 Broadcast enviado a {broadcast_count} peers")

    except Exception as e:
        print(f"❌ Error en ejemplo P2P: {e}")

    finally:
        await sdk.shutdown()


async def model_management_example():
    """
    Ejemplo de gestión avanzada de modelos.
    """
    print("\n📦 AILOOS SDK - Ejemplo de Gestión de Modelos")
    print("=" * 50)

    # Crear SDK
    sdk = NodeSDK(
        node_id="model_mgmt_node_001",
        coordinator_url="http://localhost:5001"
    )

    try:
        # Inicializar SDK
        await sdk.initialize()
        await sdk.start()

        # Crear datos de modelo de ejemplo
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            model_data = {
                "model_type": "neural_network",
                "layers": ["conv1", "conv2", "fc1", "fc2"],
                "parameters": 12544,
                "weights": {
                    "conv1": {"shape": [32, 3, 3, 3]},
                    "conv2": {"shape": [64, 32, 3, 3]},
                    "fc1": {"shape": [128, 1024]},
                    "fc2": {"shape": [10, 128]}
                }
            }
            json.dump(model_data, f)
            model_path = f.name

        try:
            # Subir modelo
            print("📤 Subiendo modelo...")
            model_id = await sdk.upload_model(
                model_path=model_path,
                metadata={
                    "model_type": "cnn",
                    "framework": "pytorch",
                    "dataset": "cifar10",
                    "accuracy": 0.85,
                    "description": "Modelo CNN básico para clasificación"
                }
            )

            if model_id:
                print(f"✅ Modelo subido con ID: {model_id}")

                # Listar modelos disponibles
                print("📋 Modelos disponibles:")
                models = await sdk.list_available_models()
                for model in models[:3]:  # Mostrar primeros 3
                    print(f"  - {model.get('id', 'N/A')}: {model.get('filename', 'N/A')}")

                # Descargar modelo (a ubicación temporal)
                with tempfile.TemporaryDirectory() as temp_dir:
                    download_path = os.path.join(temp_dir, "downloaded_model.json")

                    downloaded = await sdk.download_model(model_id, download_path)
                    if downloaded:
                        print("✅ Modelo descargado exitosamente")

                        # Verificar tamaño del archivo descargado
                        if os.path.exists(download_path):
                            size = os.path.getsize(download_path)
                            print(f"📊 Tamaño del archivo descargado: {size} bytes")
                    else:
                        print("⚠️ Error descargando modelo")

            else:
                print("⚠️ Error subiendo modelo (coordinador no disponible)")

        finally:
            # Limpiar archivo temporal
            if os.path.exists(model_path):
                os.unlink(model_path)

    except Exception as e:
        print(f"❌ Error en ejemplo de modelos: {e}")

    finally:
        await sdk.shutdown()


async def monitoring_and_alerts_example():
    """
    Ejemplo de monitoreo avanzado y alertas.
    """
    print("\n📊 AILOOS SDK - Ejemplo de Monitoreo y Alertas")
    print("=" * 50)

    # Crear SDK
    sdk = NodeSDK(
        node_id="monitoring_node_001",
        coordinator_url="http://localhost:5001"
    )

    try:
        # Inicializar SDK
        await sdk.initialize()
        await sdk.start()

        # Configurar alertas personalizadas
        def cpu_alert(cpu_percent: float):
            print(f"🚨 ALERTA: CPU alta ({cpu_percent:.1f}%)")

        def memory_alert(memory_percent: float):
            print(f"🚨 ALERTA: Memoria alta ({memory_percent:.1f}%)")

        # Nota: En implementación real, conectar callbacks
        # sdk.monitoring.register_alert_callback("cpu_alert", cpu_alert)
        # sdk.monitoring.register_alert_callback("memory_alert", memory_alert)

        print("📈 Monitoreando sistema por 15 segundos...")

        # Monitorear por un período
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < 15:
            # Obtener métricas actuales
            metrics = sdk.get_system_metrics()

            # Mostrar métricas cada 3 segundos
            if int(asyncio.get_event_loop().time() - start_time) % 3 == 0:
                print(".1f"
            await asyncio.sleep(1)

        # Generar reporte final
        print("📊 Generando reporte de rendimiento...")
        report = await sdk.get_performance_report()

        if 'averages' in report:
            print("📈 Promedios durante monitoreo:")
            for key, value in report['averages'].items():
                print(f"  {key}: {value}")

        if 'recommendations' in report:
            print("💡 Recomendaciones:")
            for rec in report['recommendations']:
                print(f"  - {rec}")

        # Mostrar estadísticas del nodo
        print("📊 Estadísticas del nodo:")
        status = sdk.get_status()
        print(f"  Uptime: {status['uptime_seconds']:.0f} segundos")
        print(f"  Sesiones activas: {len(status['active_sessions'])}")

    except Exception as e:
        print(f"❌ Error en ejemplo de monitoreo: {e}")

    finally:
        await sdk.shutdown()


async def main():
    """
    Ejecutar todos los ejemplos avanzados.
    """
    print("🎯 AILOOS SDK - Ejemplos Avanzados")
    print("=" * 60)

    # Ejecutar ejemplos
    await advanced_federated_example()
    await p2p_communication_example()
    await model_management_example()
    await monitoring_and_alerts_example()

    print("\n🎉 Todos los ejemplos avanzados completados!")
    print("\n📚 Para más ejemplos, consulta la documentación completa del SDK.")


if __name__ == "__main__":
    # Ejecutar ejemplos avanzados
    asyncio.run(main())