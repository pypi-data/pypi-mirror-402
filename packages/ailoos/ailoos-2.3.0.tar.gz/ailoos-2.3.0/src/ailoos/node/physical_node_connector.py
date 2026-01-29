"""
Conector para nodos físicos AILOOS.
Permite conectar MacBooks físicos al coordinador federado en Google Cloud.
"""

import asyncio
import logging
import time
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, List, Any, Optional
import aiohttp
import websockets
from websockets.exceptions import ConnectionClosedError
import platform
import subprocess
import json
import os
from pathlib import Path
import hashlib

from ..models.empoorio_lm import EmpoorioLM, EmpoorioLMConfig
from ..federated.aggregator import FedAvgAggregator
from ..models.empoorio_lm import EmpoorioLM, EmpoorioLMConfig
from ..federated.aggregator import FedAvgAggregator
from ..utils.logging import setup_logging
from ..utils.data_loader import AiloosDataLoader
from ..infrastructure.ipfs_embedded import IPFSManager

logger = logging.getLogger(__name__)


class PhysicalNodeConnector:
    """
    Conector para nodos físicos que se conectan al coordinador federado.
    Maneja registro, entrenamiento local y comunicación con el coordinador.
    """

    def __init__(
        self,
        coordinator_url: str = "http://136.119.191.184:8000",
        node_id: Optional[str] = None,
        hardware_type: Optional[str] = None
    ):
        self.coordinator_url = coordinator_url.rstrip('/')
        self.node_id = node_id or self._generate_node_id()
        self.hardware_type = hardware_type or self._detect_hardware_type()

        # Estado del nodo
        self.is_registered = False
        self.is_running = False
        self.current_session = None
        self.model = EmpoorioLM(EmpoorioLMConfig())
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        self.criterion = nn.CrossEntropyLoss()

        # Estadísticas
        self.training_stats = {
            "rounds_completed": 0,
            "total_samples_processed": 0,
            "total_training_time": 0,
            "best_accuracy": 0.0,
            "dracma_earned": 0.0
        }

        # WebSocket para comunicación en tiempo real
        self.websocket = None
        
        # IPFS Manager para descargar modelos
        self.ipfs_manager = None  # Se inicializa de forma lazy
        
        # Tracking de versiones descargadas
        self.downloaded_versions = {}  # {version_id: {cid, hash, timestamp}}
        
        # Background tasks
        self._heartbeat_task = None
        self._discovery_task = None
        
        # NodeCommunicator para P2P (opcional)
        self.node_communicator = None

        logger.info(f"🚀 Nodo físico {self.node_id} inicializado ({self.hardware_type})")

    def _generate_node_id(self) -> str:
        """Genera un ID único para el nodo basado en hardware y timestamp."""
        hardware_hash = str(hash(platform.machine() + platform.system()))[:8]
        timestamp = str(int(time.time()))[-6:]  # Últimos 6 dígitos
        return f"{self._detect_hardware_type()}_{hardware_hash}_{timestamp}"

    def _detect_hardware_type(self) -> str:
        """Detecta automáticamente el tipo de hardware."""
        system = platform.system()

        if system == "Darwin":  # macOS
            try:
                # Ejecutar sysctl para obtener modelo de Mac
                result = subprocess.run(
                    ['sysctl', 'hw.model'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                model = result.stdout.strip().split(': ')[1]

                if "MacBookPro" in model:
                    # Detectar generación aproximada
                    if any(x in model for x in ["8", "9", "10", "11"]):
                        return "macbook_2012"
                    elif any(x in model for x in ["14", "15", "16", "17"]):
                        return "macbook_m4"
                    else:
                        return "macbook_unknown"
                elif "MacBookAir" in model:
                    return "macbook_air"
                elif "iMac" in model:
                    return "imac"
                else:
                    return "mac_unknown"
            except:
                return "mac_unknown"
        elif system == "Linux":
            return "linux"
        elif system == "Windows":
            return "windows"
        else:
            return f"{system.lower()}_unknown"

    def get_hardware_info(self) -> Dict[str, Any]:
        """Obtiene información detallada del hardware."""
        try:
            info = {
                "system": platform.system(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "cpu_count": os.cpu_count(),
                "memory_gb": self._get_memory_gb(),
                "gpu_available": torch.cuda.is_available(),
                "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
                "pytorch_version": torch.__version__
            }

            # Información específica de GPU
            if torch.cuda.is_available():
                info["gpu_name"] = torch.cuda.get_device_name(0)
                info["gpu_memory_gb"] = torch.cuda.get_device_properties(0).total_memory / (1024**3)

            return info
        except Exception as e:
            logger.warning(f"Error obteniendo info de hardware: {e}")
            return {"error": str(e)}

    def _get_memory_gb(self) -> float:
        """Obtiene la cantidad de memoria RAM en GB."""
        try:
            if platform.system() == "Darwin":  # macOS
                result = subprocess.run(
                    ['sysctl', 'hw.memsize'],
                    capture_output=True,
                    text=True
                )
                bytes_memory = int(result.stdout.strip().split(': ')[1])
                return bytes_memory / (1024**3)
            elif platform.system() == "Linux":
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if line.startswith('MemTotal:'):
                            kb_memory = int(line.split()[1])
                            return kb_memory / (1024**2)
            return 8.0  # Default
        except:
            return 8.0

    async def register_with_coordinator(self) -> bool:
        """Registra el nodo con el coordinador central."""
        try:
            payload = {
                "node_id": self.node_id,
                "hardware_info": self.get_hardware_info(),
                "capabilities": {
                    "max_batch_size": 4,  # Limitado para hardware físico
                    "supported_datasets": ["wikipedia", "technical", "code"],
                    "federated_compatible": True,
                    "supports_empiorio_lm": True
                },
                "location": self._get_location_info(),
                "registration_time": time.time()
            }

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.post(
                    f"{self.coordinator_url}/api/v1/nodes/register",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Nodo {self.node_id} registrado exitosamente")
                        logger.info(f"📊 Node token: {data.get('node_token', 'N/A')}")
                        self.is_registered = True
                        return True
                    else:
                        error = await response.text()
                        logger.error(f"❌ Error registrando nodo: HTTP {response.status} - {error}")
                        return False

        except Exception as e:
            logger.error(f"❌ Error de conexión: {e}")
            return False

    def _get_location_info(self) -> Dict[str, Any]:
        """Obtiene información de ubicación (simplificada)."""
        # En producción, usar IP geolocation API
        return {
            "country": "Spain",
            "city": "Madrid",
            "timezone": "Europe/Madrid",
            "coordinates": {"lat": 40.4168, "lon": -3.7038}
        }

    async def connect_websocket(self) -> bool:
        """Establece conexión WebSocket con el coordinador."""
        try:
            websocket_url = f"ws://{self.coordinator_url.replace('http://', '').replace('https://', '')}/ws"
            self.websocket = await websockets.connect(
                websocket_url,
                extra_headers={"node_id": self.node_id}
            )
            logger.info("🔌 Conexión WebSocket establecida")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando WebSocket: {e}")
            return False

    async def listen_for_training_rounds(self):
        """Escucha mensajes del coordinador sobre nuevas rondas de entrenamiento."""
        if not self.websocket:
            logger.error("❌ WebSocket no conectado")
            return

        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get("type")

                    if message_type == "new_round":
                        await self.handle_new_round(data)
                    elif message_type == "global_weights_available":
                        await self.handle_global_weights(data)
                    elif message_type == "model_distribution":
                        await self.handle_model_distribution(data)
                    elif message_type == "round_complete":
                        await self.handle_round_complete(data)
                    elif message_type == "reward_earned":
                        await self.handle_reward_earned(data)
                    else:
                        logger.debug(f"Mensaje recibido: {message_type}")

                except json.JSONDecodeError:
                    logger.warning(f"Mensaje no válido recibido: {message}")

        except ConnectionClosedError:
            logger.warning("🔌 Conexión WebSocket cerrada")
        except Exception as e:
            logger.error(f"❌ Error en WebSocket: {e}")

    async def handle_new_round(self, data: Dict[str, Any]):
        """Maneja el inicio de una nueva ronda de entrenamiento."""
        round_id = data.get("round_id")
        session_id = data.get("session_id")

        logger.info(f"🎯 Nueva ronda iniciada: {round_id}")

        # Solicitar pesos globales
        await self.request_global_weights(session_id, round_id)

    async def handle_model_distribution(self, data: Dict[str, Any]):
        """
        Maneja la notificación de distribución de modelo desde el coordinator.
        
        Descarga el modelo desde IPFS, verifica el hash y envía ACK.
        """
        try:
            version_id = data.get("version_id")
            model_cid = data.get("model_cid")
            metadata_cid = data.get("metadata_cid")
            expected_hash = data.get("expected_hash")
            
            logger.info(f"📦 Recibida notificación de distribución para versión {version_id}")
            logger.info(f"   Model CID: {model_cid}")
            
            # Verificar si ya tenemos esta versión
            if version_id in self.downloaded_versions:
                logger.info(f"✅ Versión {version_id} ya descargada, enviando ACK")
                await self._send_distribution_ack(version_id, expected_hash, success=True)
                return
            
            # Inicializar IPFS Manager si no existe
            if not self.ipfs_manager:
                logger.info("📡 Inicializando IPFS Manager...")
                self.ipfs_manager = IPFSManager()
                await self.ipfs_manager.start()
            
            # Descargar modelo desde IPFS
            logger.info(f"⬇️ Descargando modelo {model_cid} desde IPFS...")
            model_data = await self.ipfs_manager.get_data(model_cid)
            
            # Verificar hash
            actual_hash = hashlib.sha256(model_data).hexdigest()
            if actual_hash != expected_hash:
                logger.error(f"❌ Hash mismatch: expected {expected_hash}, got {actual_hash}")
                await self._send_distribution_ack(version_id, actual_hash, success=False, error="Hash mismatch")
                return
            
            logger.info(f"✅ Hash verificado correctamente: {actual_hash}")
            
            # Descargar metadata
            logger.info(f"⬇️ Descargando metadata {metadata_cid} desde IPFS...")
            metadata_data = await self.ipfs_manager.get_data(metadata_cid)
            
            # Guardar modelo localmente (opcional, para cache)
            local_model_dir = Path.home() / ".ailoos" / "models" / version_id
            local_model_dir.mkdir(parents=True, exist_ok=True)
            
            model_path = local_model_dir / "model.pt"
            with open(model_path, "wb") as f:
                f.write(model_data)
            
            metadata_path = local_model_dir / "metadata.json"
            with open(metadata_path, "wb") as f:
                f.write(metadata_data)
            
            logger.info(f"💾 Modelo guardado en {model_path}")
            
            # Registrar versión descargada
            self.downloaded_versions[version_id] = {
                "model_cid": model_cid,
                "metadata_cid": metadata_cid,
                "hash": actual_hash,
                "timestamp": time.time(),
                "local_path": str(model_path)
            }
            
            # Enviar ACK al coordinator
            await self._send_distribution_ack(version_id, actual_hash, success=True)
            
            logger.info(f"✅ Modelo {version_id} descargado y verificado exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error manejando distribución de modelo: {e}")
            await self._send_distribution_ack(
                data.get("version_id", "unknown"), 
                "", 
                success=False, 
                error=str(e)
            )

    async def _send_distribution_ack(self, version_id: str, verified_hash: str, 
                                    success: bool, error: str = ""):
        """Envía confirmación (ACK) de descarga de modelo al coordinator."""
        try:
            payload = {
                "node_id": self.node_id,
                "version_id": version_id,
                "verified_hash": verified_hash,
                "success": success,
                "error": error,
                "timestamp": time.time()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.coordinator_url}/api/v1/nodes/distribution-ack",
                    json=payload
                ) as response:
                    if response.status == 200:
                        logger.info(f"✅ ACK enviado para versión {version_id}")
                    else:
                        logger.warning(f"⚠️ Error enviando ACK: HTTP {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Error enviando ACK: {e}")

    async def request_global_weights(self, session_id: str, round_id: str):
        """Solicita los pesos globales del coordinador."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.coordinator_url}/api/v1/sessions/{session_id}/global-weights"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        weights_data = data.get("global_weights")

                        if weights_data:
                            # Convertir a tensores PyTorch
                            global_weights = {}
                            for key, tensor_data in weights_data.items():
                                global_weights[key] = torch.tensor(tensor_data)

                            # Cargar pesos en el modelo
                            self.model.load_state_dict(global_weights)
                            logger.info("✅ Pesos globales cargados")

                            # Iniciar entrenamiento local
                            await self.start_local_training(session_id, round_id)
                        else:
                            logger.error("❌ No se encontraron pesos globales")
                    else:
                        logger.error(f"❌ Error obteniendo pesos: HTTP {response.status}")

        except Exception as e:
            logger.error(f"❌ Error solicitando pesos globales: {e}")

    async def start_local_training(self, session_id: str, round_id: str):
        """Inicia el entrenamiento local para la ronda."""
        logger.info("🏃 Iniciando entrenamiento local...")

        try:
            # Preparar datos locales (simplificado)
            train_data = self._prepare_local_training_data()

            # Entrenar localmente
            local_results = self._train_local_round(train_data)

            # Enviar pesos al coordinador
            await self.submit_local_weights(session_id, round_id, local_results)

        except Exception as e:
            logger.error(f"❌ Error en entrenamiento local: {e}")

    def _prepare_local_training_data(self) -> List[Dict[str, torch.Tensor]]:
        """Prepara datos de entrenamiento locales (simplificado)."""
        # En producción, cargar datos reales del usuario
        try:
            # Inicializar data loader
            data_loader = AiloosDataLoader(self.model.tokenizer)
            
            # Intentar cargar dataset real (ej. wikitext para demo)
            # En un nodo real, esto podría ser un archivo local de logs o documentos
            dataset = data_loader.load_dataset("wikitext", split="train", num_samples=200)
            
            # Crear batches
            train_data = []
            batch_size = 4
            
            for i in range(0, len(dataset), batch_size):
                batch = dataset[i:i+batch_size]
                # Asegurar formato correcto
                if "input_ids" in batch:
                    input_ids = batch["input_ids"]
                    if not isinstance(input_ids, torch.Tensor):
                        input_ids = torch.tensor(input_ids)
                    
                    # Labels son input_ids desplazados (causal LM)
                    labels = input_ids.clone()
                    
                    train_data.append({
                        "input_ids": input_ids,
                        "labels": labels
                    })
            
            if train_data:
                logger.info(f"📊 Datos reales cargados: {len(train_data)} batches")
                return train_data
                
        except Exception as e:
            logger.error(f"❌ Error cargando datos reales: {e}. Usando sintéticos.")

        # Fallback: generar datos sintéticos
        train_data = []

        for _ in range(50):  # 50 batches
            input_ids = torch.randint(0, self.model.config.vocab_size, (4, 32))  # batch_size=4, seq_len=32
            labels = torch.randint(0, self.model.config.vocab_size, (4, 32))
            train_data.append({"input_ids": input_ids, "labels": labels})

        logger.info(f"📊 Datos locales preparados: {len(train_data)} batches")
        return train_data

    def _train_local_round(self, train_data: List[Dict[str, torch.Tensor]]) -> Dict[str, Any]:
        """Entrena el modelo localmente por una ronda."""
        self.model.train()
        total_loss = 0
        total_correct = 0
        total_samples = 0

        start_time = time.time()

        for batch in train_data:
            input_ids = batch["input_ids"]
            labels = batch["labels"]

            self.optimizer.zero_grad()

            # Forward pass
            outputs = self.model(input_ids)
            logits = outputs["logits"]

            # Calcular loss
            loss = self.criterion(logits.view(-1, logits.size(-1)), labels.view(-1))

            # Backward pass
            loss.backward()
            self.optimizer.step()

            # Estadísticas
            total_loss += loss.item()
            _, predicted = logits.max(2)
            total_correct += (predicted == labels).sum().item()
            total_samples += labels.numel()

        training_time = time.time() - start_time
        accuracy = 100. * total_correct / total_samples
        avg_loss = total_loss / len(train_data)

        # Actualizar estadísticas
        self.training_stats["rounds_completed"] += 1
        self.training_stats["total_samples_processed"] += total_samples
        self.training_stats["total_training_time"] += training_time
        self.training_stats["best_accuracy"] = max(self.training_stats["best_accuracy"], accuracy)

        logger.info(f"🏁 Entrenamiento local completado: Acc={accuracy:.2f}%, Loss={avg_loss:.4f}, Time={training_time:.2f}s")
        return {
            "accuracy": accuracy,
            "loss": avg_loss,
            "training_time": training_time,
            "samples_processed": total_samples
        }

    async def submit_local_weights(self, session_id: str, round_id: str, metrics: Dict[str, Any]):
        """Envía los pesos entrenados al coordinador."""
        try:
            # Serializar pesos
            weights_serialized = {}
            for key, tensor in self.model.state_dict().items():
                weights_serialized[key] = tensor.detach().cpu().numpy().tolist()

            payload = {
                "node_id": self.node_id,
                "round_id": round_id,
                "local_weights": weights_serialized,
                "metrics": metrics,
                "hardware_info": self.get_hardware_info(),
                "timestamp": time.time()
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.coordinator_url}/api/v1/rounds/{round_id}/submit-weights",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Pesos enviados para ronda {round_id}")
                        logger.info(f"📊 Contribución reconocida: {data.get('contribution_score', 0)}")
                        return True
                    else:
                        error = await response.text()
                        logger.error(f"❌ Error enviando pesos: HTTP {response.status} - {error}")
                        return False

        except Exception as e:
            logger.error(f"❌ Error enviando pesos: {e}")
            return False

    async def handle_global_weights(self, data: Dict[str, Any]):
        """Maneja la recepción de nuevos pesos globales."""
        logger.info("📥 Nuevos pesos globales disponibles")

    async def handle_round_complete(self, data: Dict[str, Any]):
        """Maneja la finalización de una ronda."""
        round_id = data.get("round_id")
        logger.info(f"✅ Ronda {round_id} completada")

    async def handle_reward_earned(self, data: Dict[str, Any]):
        """Maneja la recepción de recompensas DRACMA."""
        amount = data.get("amount", 0)
        self.training_stats["dracma_earned"] += amount
        logger.info(f"💰 ¡Recompensa ganada! +{amount} DRACMA")

    def get_node_status(self) -> Dict[str, Any]:
        """Retorna el estado completo del nodo."""
        return {
            "node_id": self.node_id,
            "hardware_type": self.hardware_type,
            "is_registered": self.is_registered,
            "websocket_connected": self.websocket is not None and not self.websocket.closed,
            "training_stats": self.training_stats,
            "hardware_info": self.get_hardware_info(),
            "coordinator_url": self.coordinator_url
        }

    async def start(self):
        """Inicia el conector del nodo físico."""
        logger.info("🚀 Iniciando conector de nodo físico...")

        # Registrar con coordinador
        if not await self.register_with_coordinator():
            logger.error("❌ Falló registro con coordinador")
            return

        # Conectar WebSocket
        if not await self.connect_websocket():
            logger.warning("⚠️ WebSocket no disponible, usando polling")

        # Escuchar rondas de entrenamiento
        if self.websocket:
            await self.listen_for_training_rounds()
        else:
            # Fallback a polling cada 30 segundos
            while True:
                await self.check_for_new_rounds()
                await asyncio.sleep(30)

    async def check_for_new_rounds(self):
        """Verifica periódicamente si hay nuevas rondas (fallback)."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.coordinator_url}/api/v1/nodes/{self.node_id}/rounds"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        active_rounds = data.get("active_rounds", [])

                        for round_info in active_rounds:
                            if round_info["status"] == "waiting_for_nodes":
                                await self.handle_new_round(round_info)
                                break
        except Exception as e:
            logger.debug(f"Error checking rounds: {e}")

    async def stop(self):
        """Detiene el conector."""
        if self.websocket:
            await self.websocket.close()
        logger.info("🛑 Conector detenido")


async def main():
    """Función principal para ejecutar el conector de nodo físico."""
    import argparse

    parser = argparse.ArgumentParser(description="AILOOS Physical Node Connector")
    parser.add_argument("--coordinator", default="http://136.119.191.184:8000",
                       help="URL del coordinador")
    parser.add_argument("--node-id", help="ID específico del nodo")
    parser.add_argument("--hardware-type", help="Tipo de hardware específico")

    args = parser.parse_args()

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Crear conector
    connector = PhysicalNodeConnector(
        coordinator_url=args.coordinator,
        node_id=args.node_id,
        hardware_type=args.hardware_type
    )

    print("🤖 AILOOS - Conector de Nodo Físico")
    print("=" * 50)
    print(f"🆔 Node ID: {connector.node_id}")
    print(f"💻 Hardware: {connector.hardware_type}")
    print(f"🌐 Coordinator: {connector.coordinator_url}")
    print()

    try:
        await connector.start()
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo conector...")
        await connector.stop()
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        await connector.stop()


if __name__ == "__main__":
    asyncio.run(main())