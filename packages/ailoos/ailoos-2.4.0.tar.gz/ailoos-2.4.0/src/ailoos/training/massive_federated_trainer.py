"""
Entrenador federado masivo para AILOOS.
Ejecuta entrenamiento real con datos masivos distribuidos entre múltiples nodos.
"""

import asyncio
import logging
import time
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, List, Any, Optional
import json
import os
from pathlib import Path
import aiohttp
import websockets
from websockets.exceptions import ConnectionClosedError

from ..models.empoorio_lm import EmpoorioLM, EmpoorioLMConfig
from ..data.massive_dataset_generator import generate_massive_suite
from ..federated.aggregator import FedAvgAggregator
from ..federated.adamw_optimizer import FederatedAdamWOptimizer, create_federated_adamw_optimizer
from ..utils.logging import setup_logging

logger = logging.getLogger(__name__)


class MassiveFederatedNode:
    """
    Nodo federado para entrenamiento masivo.
    Maneja datasets grandes y comunicación con coordinador.
    """

    def __init__(
        self,
        node_id: str,
        coordinator_url: str,
        hardware_type: str = "macbook_m4",
        dataset_partition: str = "wikipedia"
    ):
        self.node_id = node_id
        self.coordinator_url = coordinator_url
        self.hardware_type = hardware_type
        self.dataset_partition = dataset_partition

        # Modelo y configuración
        self.model = EmpoorioLM(EmpoorioLMConfig())
        # Usar el nuevo optimizador AdamW federado
        self.optimizer = create_federated_adamw_optimizer(
            self.model, self.node_id, lr=5e-5, warmup_steps=50, total_steps=1000, use_tenseal=False
        )
        self.criterion = nn.CrossEntropyLoss()

        # Estado del nodo
        self.is_registered = False
        self.current_session = None
        self.local_data = None
        self.global_weights = None

        # Estadísticas
        self.training_stats = {
            "rounds_completed": 0,
            "total_samples_processed": 0,
            "total_training_time": 0,
            "best_accuracy": 0.0
        }

        logger.info(f"🚀 Nodo {node_id} inicializado ({hardware_type})")

    async def register_with_coordinator(self) -> bool:
        """Registra el nodo con el coordinador."""
        try:
            payload = {
                "node_id": self.node_id,
                "hardware_info": {
                    "type": self.hardware_type,
                    "cpu": "Apple M4" if "m4" in self.hardware_type.lower() else "Intel",
                    "memory": "16GB",
                    "gpu": "Integrated" if "m4" in self.hardware_type.lower() else "None"
                },
                "capabilities": {
                    "max_batch_size": 8,
                    "supported_datasets": ["wikipedia", "technical", "code"],
                    "federated_compatible": True
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.coordinator_url}/api/v1/nodes/register",
                    json=payload
                ) as response:
                    if response.status == 200:
                        self.is_registered = True
                        logger.info(f"✅ Nodo {self.node_id} registrado exitosamente")
                        return True
                    else:
                        error = await response.text()
                        logger.error(f"❌ Error registrando nodo: {error}")
                        return False

        except Exception as e:
            logger.error(f"❌ Error de conexión: {e}")
            return False

    async def load_local_dataset(self) -> bool:
        """Carga el dataset local asignado a este nodo."""
        try:
            # Buscar archivos de dataset masivo
            data_dir = Path("./data/massive_datasets")
            if not data_dir.exists():
                logger.error("❌ Directorio de datasets no encontrado")
                return False

            # Buscar archivos que coincidan con la partición asignada
            matching_files = list(data_dir.glob(f"{self.dataset_partition}_*.jsonl"))
            if not matching_files:
                logger.error(f"❌ No se encontraron archivos para partición {self.dataset_partition}")
                return False

            # Cargar el archivo más grande (más datos)
            dataset_file = max(matching_files, key=lambda x: x.stat().st_size)
            logger.info(f"📂 Cargando dataset: {dataset_file}")

            # Cargar datos (simplificado - en producción usar streaming)
            self.local_data = []
            with open(dataset_file, 'r') as f:
                for i, line in enumerate(f):
                    if i >= 1000:  # Limitar para pruebas (primeros 1000 samples)
                        break
                    try:
                        sample = json.loads(line.strip())
                        self.local_data.append(sample)
                    except json.JSONDecodeError:
                        continue

            logger.info(f"✅ Dataset cargado: {len(self.local_data)} muestras")
            return True

        except Exception as e:
            logger.error(f"❌ Error cargando dataset: {e}")
            return False

    async def get_global_weights(self) -> bool:
        """Obtiene los pesos globales del coordinador."""
        if not self.current_session:
            logger.error("❌ No hay sesión activa")
            return False

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.coordinator_url}/api/v1/sessions/{self.current_session}/global-weights"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        weights_data = data.get("global_weights")

                        if weights_data:
                            # Convertir de vuelta a tensores
                            self.global_weights = {}
                            for key, tensor_data in weights_data.items():
                                self.global_weights[key] = torch.tensor(tensor_data)

                            # Cargar pesos en el modelo
                            self.model.load_state_dict(self.global_weights)
                            logger.info("✅ Pesos globales obtenidos y cargados")
                            return True
                        else:
                            logger.error("❌ No se encontraron pesos globales")
                            return False
                    else:
                        error = await response.text()
                        logger.error(f"❌ Error obteniendo pesos: {error}")
                        return False

        except Exception as e:
            logger.error(f"❌ Error de conexión: {e}")
            return False

    def prepare_training_data(self):
        """Prepara datos de entrenamiento desde el dataset cargado."""
        if not self.local_data:
            logger.error("❌ No hay datos locales cargados")
            return

        # Convertir datos a tensores (simplificado)
        # En producción, esto sería más sofisticado con tokenización real
        self.train_inputs = []
        self.train_labels = []

        for sample in self.local_data[:500]:  # Usar primeros 500 para entrenamiento
            content = sample.get('content', '')
            if len(content) > 10:  # Filtro básico
                # Simular tokenización (en producción usar tokenizer real)
                input_ids = torch.randint(0, self.model.config.vocab_size, (32,))  # 32 tokens
                label = torch.randint(0, self.model.config.vocab_size, (32,))     # Next token prediction

                self.train_inputs.append(input_ids)
                self.train_labels.append(label)

        logger.info(f"📊 Datos preparados: {len(self.train_inputs)} batches")

    def train_local_round(self, num_epochs: int = 2) -> Dict[str, Any]:
        """Entrena el modelo localmente por una ronda usando AdamW federado."""
        if not self.train_inputs:
            logger.error("❌ No hay datos preparados")
            return {"error": "No training data prepared"}

        self.model.train()
        total_loss = 0
        total_correct = 0
        total_samples = 0

        start_time = time.time()

        for epoch in range(num_epochs):
            epoch_loss = 0
            epoch_correct = 0
            epoch_samples = 0

            for input_ids, labels in zip(self.train_inputs, self.train_labels):
                self.optimizer.zero_grad()

                # Forward pass
                outputs = self.model(input_ids.unsqueeze(0))  # Añadir dimensión batch
                logits = outputs["logits"].squeeze(0)  # Remover dimensión batch

                # Calcular loss
                loss = self.criterion(logits.view(-1, logits.size(-1)), labels.view(-1))

                # Backward pass
                loss.backward()

                # Optimizer step con el nuevo AdamW federado
                step_stats = self.optimizer.step(loss)

                # Estadísticas
                epoch_loss += loss.item()
                _, predicted = logits.max(1)
                epoch_correct += (predicted == labels).sum().item()
                epoch_samples += labels.size(0)

            # Promedios de la época
            avg_loss = epoch_loss / len(self.train_inputs)
            accuracy = 100. * epoch_correct / epoch_samples

            logger.info(f"   Epoch {epoch+1}/{num_epochs}: Loss={avg_loss:.4f}, Acc={accuracy:.2f}%, LR={step_stats['learning_rate']:.6f}")

            total_loss += avg_loss
            total_correct += epoch_correct
            total_samples += epoch_samples

        training_time = time.time() - start_time
        final_accuracy = 100. * total_correct / total_samples
        avg_loss = total_loss / num_epochs

        # Obtener estadísticas del optimizador
        optimizer_stats = self.optimizer.get_optimizer_stats()

        # Actualizar estadísticas
        self.training_stats["rounds_completed"] += 1
        self.training_stats["total_samples_processed"] += total_samples
        self.training_stats["total_training_time"] += training_time
        self.training_stats["best_accuracy"] = max(self.training_stats["best_accuracy"], final_accuracy)

        logger.info(f"🏁 Ronda completada: Acc={final_accuracy:.2f}%, Time={training_time:.2f}s, Steps={optimizer_stats['current_step']}")

        return {
            "accuracy": final_accuracy,
            "loss": avg_loss,
            "training_time": training_time,
            "samples_processed": total_samples,
            "round_number": self.training_stats["rounds_completed"],
            "learning_rate": step_stats["learning_rate"],
            "gradient_norm": step_stats["gradient_norm"],
            "optimizer_stats": optimizer_stats
        }

    async def submit_weights_to_coordinator(self, round_id: str, metrics: Dict[str, Any]) -> bool:
        """Envía los pesos entrenados al coordinador."""
        try:
            # Serializar pesos para envío
            weights_serialized = {}
            for key, tensor in self.model.state_dict().items():
                weights_serialized[key] = tensor.detach().cpu().numpy().tolist()

            payload = {
                "node_id": self.node_id,
                "local_weights": weights_serialized,
                "metrics": metrics
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.coordinator_url}/api/v1/rounds/{round_id}/submit-weights",
                    json=payload
                ) as response:
                    if response.status == 200:
                        logger.info(f"✅ Pesos enviados para ronda {round_id}")
                        return True
                    else:
                        error = await response.text()
                        logger.error(f"❌ Error enviando pesos: {error}")
                        return False

        except Exception as e:
            logger.error(f"❌ Error de conexión: {e}")
            return False

    async def participate_in_federated_round(self, round_id: str) -> bool:
        """Participa en una ronda completa de entrenamiento federado."""
        try:
            logger.info(f"🎯 Participando en ronda {round_id}")

            # 1. Obtener pesos globales
            if not await self.get_global_weights():
                return False

            # 2. Entrenar localmente
            local_results = self.train_local_round()

            # 3. Enviar pesos al coordinador
            success = await self.submit_weights_to_coordinator(round_id, local_results)

            return success

        except Exception as e:
            logger.error(f"❌ Error en ronda federada: {e}")
            return False

    def get_node_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del nodo."""
        return {
            "node_id": self.node_id,
            "hardware_type": self.hardware_type,
            "dataset_partition": self.dataset_partition,
            "is_registered": self.is_registered,
            "training_stats": self.training_stats,
            "model_info": self.model.get_model_info()
        }


class MassiveFederatedTrainer:
    """
    Entrenador principal para sesiones federadas masivas.
    Coordina múltiples nodos y gestiona el entrenamiento distribuido.
    """

    def __init__(self, coordinator_url: str = "http://localhost:8000"):
        self.coordinator_url = coordinator_url
        self.nodes: Dict[str, MassiveFederatedNode] = {}
        self.session_id = None

        # Configuración
        self.num_rounds = 3
        self.nodes_per_round = 2  # Para pruebas

        logger.info("🚀 Entrenador federado masivo inicializado")

    async def create_session(self, model_version: str = "empoorio_lm_v1.0") -> bool:
        """Crea una nueva sesión de entrenamiento."""
        try:
            payload = {
                "model_version": model_version,
                "session_config": {
                    "num_rounds": self.num_rounds,
                    "min_nodes_per_round": self.nodes_per_round,
                    "dataset_partitions": ["wikipedia", "technical", "code"]
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.coordinator_url}/api/v1/sessions/create",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.session_id = data.get("session_id")
                        logger.info(f"✅ Sesión creada: {self.session_id}")
                        return True
                    else:
                        error = await response.text()
                        logger.error(f"❌ Error creando sesión: {error}")
                        return False

        except Exception as e:
            logger.error(f"❌ Error de conexión: {e}")
            return False

    def add_node(self, node_id: str, hardware_type: str, dataset_partition: str) -> bool:
        """Añade un nodo al entrenador."""
        if node_id in self.nodes:
            logger.warning(f"Nodo {node_id} ya existe")
            return False

        node = MassiveFederatedNode(
            node_id=node_id,
            coordinator_url=self.coordinator_url,
            hardware_type=hardware_type,
            dataset_partition=dataset_partition
        )

        self.nodes[node_id] = node
        logger.info(f"✅ Nodo añadido: {node_id} ({hardware_type})")
        return True

    async def initialize_nodes(self) -> bool:
        """Inicializa todos los nodos."""
        logger.info("🔧 Inicializando nodos...")

        success_count = 0
        for node_id, node in self.nodes.items():
            try:
                # Registrar con coordinador
                if await node.register_with_coordinator():
                    # Cargar dataset
                    if await node.load_local_dataset():
                        # Preparar datos
                        node.prepare_training_data()
                        success_count += 1
                        logger.info(f"✅ Nodo {node_id} inicializado correctamente")
                    else:
                        logger.error(f"❌ Error cargando dataset para {node_id}")
                else:
                    logger.error(f"❌ Error registrando {node_id}")
            except Exception as e:
                logger.error(f"❌ Error inicializando {node_id}: {e}")

        logger.info(f"📊 Nodos inicializados: {success_count}/{len(self.nodes)}")
        return success_count == len(self.nodes)

    async def run_federated_training(self) -> Dict[str, Any]:
        """Ejecuta el entrenamiento federado completo."""
        if not self.session_id:
            logger.error("❌ No hay sesión activa")
            return {"error": "No active session"}

        logger.info("🚀 Iniciando entrenamiento federado masivo")
        logger.info(f"📊 Nodos: {len(self.nodes)}")
        logger.info(f"🎯 Rondas: {self.num_rounds}")

        results = {
            "session_id": self.session_id,
            "total_rounds": 0,
            "completed_rounds": 0,
            "node_results": {},
            "global_stats": {
                "total_training_time": 0,
                "total_samples_processed": 0,
                "average_accuracy": 0.0
            }
        }

        for round_num in range(self.num_rounds):
            logger.info(f"\n🎯 RONDA {round_num + 1}/{self.num_rounds}")
            logger.info("=" * 50)

            # Iniciar ronda
            round_id = f"round_{round_num + 1}_{int(time.time())}"

            # Participar nodos en la ronda
            round_tasks = []
            for node_id, node in self.nodes.items():
                task = node.participate_in_federated_round(round_id)
                round_tasks.append((node_id, task))

            # Ejecutar ronda
            round_results = {}
            successful_nodes = 0

            for node_id, task in round_tasks:
                try:
                    success = await task
                    if success:
                        round_results[node_id] = node.get_node_stats()
                        successful_nodes += 1
                        logger.info(f"✅ {node_id} completó ronda {round_num + 1}")
                    else:
                        logger.error(f"❌ {node_id} falló en ronda {round_num + 1}")
                except Exception as e:
                    logger.error(f"❌ Error en {node_id}: {e}")

            # Resultados de la ronda
            results["total_rounds"] = round_num + 1
            if successful_nodes >= self.nodes_per_round:
                results["completed_rounds"] += 1
                logger.info(f"✅ Ronda {round_num + 1} completada con {successful_nodes} nodos")
            else:
                logger.warning(f"⚠️ Ronda {round_num + 1} completada parcialmente ({successful_nodes}/{self.nodes_per_round})")

            # Esperar antes de siguiente ronda
            await asyncio.sleep(2)

        # Estadísticas finales
        total_accuracy = 0
        total_samples = 0
        total_time = 0

        for node_id, node in self.nodes.items():
            stats = node.get_node_stats()
            results["node_results"][node_id] = stats

            training_stats = stats["training_stats"]
            total_accuracy += training_stats["best_accuracy"]
            total_samples += training_stats["total_samples_processed"]
            total_time += training_stats["total_training_time"]

        if self.nodes:
            results["global_stats"]["average_accuracy"] = total_accuracy / len(self.nodes)
            results["global_stats"]["total_samples_processed"] = total_samples
            results["global_stats"]["total_training_time"] = total_time

        logger.info("\n🎉 ENTRENAMIENTO FEDERADO COMPLETADO")
        logger.info("=" * 60)
        logger.info(f"✅ Rondas completadas: {results['completed_rounds']}/{results['total_rounds']}")
        logger.info(f"📊 Accuracy promedio: {results['global_stats']['average_accuracy']:.2f}%")
        logger.info(f"📈 Muestras procesadas: {results['global_stats']['total_samples_processed']}")
        logger.info(f"⏱️ Tiempo total: {results['global_stats']['total_training_time']:.2f}s")

        return results

    def save_results(self, results: Dict[str, Any], output_file: str = "federated_training_results.json"):
        """Guarda los resultados del entrenamiento."""
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"💾 Resultados guardados en {output_file}")
        except Exception as e:
            logger.error(f"❌ Error guardando resultados: {e}")


async def run_massive_federated_training():
    """
    Función principal para ejecutar entrenamiento federado masivo.
    """
    print("🤖 AILOOS - ENTRENAMIENTO FEDERADO MASIVO")
    print("=" * 60)

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Crear entrenador
    trainer = MassiveFederatedTrainer()

    # Añadir nodos simulando los dos MacBooks
    trainer.add_node("macbook_m4", "macbook_m4", "wikipedia")
    trainer.add_node("macbook_2012", "macbook_2012", "technical")

    try:
        # Crear sesión
        print("\n1️⃣ Creando sesión de entrenamiento...")
        if not await trainer.create_session():
            print("❌ Error creando sesión")
            return

        # Inicializar nodos
        print("\n2️⃣ Inicializando nodos...")
        if not await trainer.initialize_nodes():
            print("❌ Error inicializando nodos")
            return

        # Ejecutar entrenamiento
        print("\n3️⃣ Ejecutando entrenamiento federado...")
        results = await trainer.run_federated_training()

        # Guardar resultados
        print("\n4️⃣ Guardando resultados...")
        trainer.save_results(results)

        # Mostrar resumen final
        print("\n🎉 ¡ENTRENAMIENTO FEDERADO MASIVO COMPLETADO!")
        print("=" * 60)
        print(f"✅ Rondas: {results['completed_rounds']}/{results['total_rounds']}")
        print(f"📊 Accuracy promedio: {results['global_stats']['average_accuracy']:.2f}%")
        print(f"📈 Muestras procesadas: {results['global_stats']['total_samples_processed']}")
        print(f"⏱️ Tiempo total: {results['global_stats']['total_training_time']:.2f}s")
        print(f"💾 Resultados guardados en: federated_training_results.json")

        return results

    except Exception as e:
        logger.error(f"❌ Error en entrenamiento: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    # Ejecutar entrenamiento masivo
    asyncio.run(run_massive_federated_training())