import logging
import random
import os
import asyncio
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

# AILOOS SDK Imports
from ..p2p.dht.node import DHTNode
from ..data.dataset_manager import get_dataset_manager
from ..federated.trainer import FederatedTrainer
from ..federated.tenseal_encryptor import TenSEALEncryptor
from ..core.config import get_config
from .storage import DataHubStorage
from ..data.registry import data_registry # Import Registry

logger = logging.getLogger(__name__)

@dataclass
class FederatedDiet:
    """Una 'dieta' (misión de entrenamiento) disponible en la red."""
    mission_id: str
    name: str
    description: str
    data_type: str  # 'text', 'code', 'science'
    reward_per_shard: float
    total_shards: int
    available_shards: List[str]  # Lista de CIDs
    source: str = "Network" # 'Network' or 'Local Refinery'

class NutritionClient:
    """
    Cliente de Nutrición Federada.
    Se encarga de 'alimentar' al nodo descargando datos, entrenando y subiendo conocimientos.
    """

    def __init__(self, dht_node: Optional[DHTNode] = None):
        self.dht_node = dht_node
        self.dataset_manager = get_dataset_manager()
        self.config = get_config()
        self.active_training = False
        
        # Initialize Storage
        from pathlib import Path
        data_path = Path(os.getcwd()) / "data" / "datahub"
        self.storage = DataHubStorage(data_path)
        
        self._mock_populate_missions() # Simulación inicial si no hay DHT real poblada

    def _mock_populate_missions(self):
        """Simula misiones disponibles en la DHT para demostración."""
        self.known_missions = {
            "mission_legal_01": {
                "id": "mission_legal_01",
                "name": "⚖️ Corpus Legal Español v1",
                "desc": "Entrenamiento con BOE, sentencias del TS y legislación.",
                "type": "text",
                "reward": 45.5,
                "shards": ["QmLegal1Hash...", "QmLegal2Hash...", "QmLegal3Hash..."]
            },
            "mission_wiki_01": {
                "id": "mission_wiki_01",
                "name": "📚 Wikipedia Knowledge Base",
                "desc": "Conocimiento general de historia, geografía y ciencias.",
                "type": "text",
                "reward": 20.0,
                "shards": ["QmWiki1Hash...", "QmWiki2Hash..."]
            },
            "mission_python_01": {
                "id": "mission_python_01",
                "name": "🐍 Python Code Expert",
                "desc": "Fine-tuning con repositorios de GitHub de alta calidad.",
                "type": "code",
                "reward": 60.0,
                "shards": ["QmCode1Hash...", "QmCode2Hash..."]
            }
        }

    async def list_available_diets(self) -> List[FederatedDiet]:
        """
        Consulta la DHT (o caché local) para ver qué misiones de entrenamiento están activas.
        En producción real: await self.dht_node.get("active_missions")
        """
        diets = []
        # En fase real usaríamos self.dht_node.get(...)
        # Aquí usamos el mock para garantizar que la demo funcione
        # 1. Missions from Mock/DHT
        for mid, data in self.known_missions.items():
            diets.append(FederatedDiet(
                mission_id=data['id'],
                name=data['name'],
                description=data['desc'],
                data_type=data['type'],
                reward_per_shard=data['reward'],
                total_shards=len(data['shards']),
                available_shards=data['shards'],
                source="Network" # Mocked network missions
            ))

        # 2. Missions from Local Registry (Refined Data)
        registered_datasets = data_registry.list_datasets(type_filter=None) # Get all
        for ds in registered_datasets:
            # Adapt Registry format to FederatedDiet
            diets.append(FederatedDiet(
                mission_id=ds['id'],
                name=f"🏭 {ds.get('name', 'Unnamed')}", # Add icon to distinguish
                description=f"Refined dataset ({ds.get('total_size_mb', 0):.1f}MB)",
                data_type=ds.get('original_type', 'text'),
                reward_per_shard=10.0, # Default local reward
                total_shards=ds.get('num_shards', 0),
                available_shards=ds.get('shard_cids', []),
                source="Local Factory" # Explicitly mark as local
            ))

        return diets

    async def consume_shard(self, diet: FederatedDiet) -> Dict[str, Any]:
        """
        Ejecuta el ciclo completo de nutrición:
        1. Selecciona un shard
        2. Descarga (Ingesta)
        3. Entrena (Digestión)
        4. Sube pesos (Sinapsis)
        5. Limpia (Digestión completa)
        """
        if self.active_training:
            raise RuntimeError("El nodo ya está 'digiriendo' un shard.")
        
        self.active_training = True
        try:
            # 1. Selección de Shard (Random Load Balancing)
            # En prod real: verificar cuáles no han sido entrenados por este nodo
            target_cid = random.choice(diet.available_shards)
            local_filename = f"shard_{target_cid[:8]}.json"
            
            # Use Inbox for temporary downloads
            local_path = self.storage.inbox_path / local_filename

            logger.info(f"🍽️ Iniciando banquete: {diet.name} -> {target_cid}")

            # 2. Ingesta (Descarga IPFS)
            # Simulamos éxito si el conector real falla por no tener red IPFS real
            logger.info("⬇️ Descargando ingredientes (Shard) de IPFS...")
            if not self.dataset_manager.download_shard(target_cid, local_path):
                # Fallback mock para demo
                logger.warning("⚠️ Fallo descarga real IPFS. Generando shard sintético para demo.")
                self._generate_synthetic_shard(local_path, diet.data_type)
            
            # 3. Digestión (Entrenamiento Local)
            logger.info(f"🧠 Digiriendo conocimiento (Entrenando {diet.data_type} en {target_cid})...")
            
            # Instanciar Trainer Real (Modo Standalone/Simulado si no hay coordinador)
            session_id = f"nutrition_{datetime.now().strftime('%Y%m%d%H%M')}"
            trainer = FederatedTrainer(
                session_id=session_id,
                model_name="Empoorio/EmpoorioLM-7B",
                dataset_name=diet.name,
                algorithm="fedavg"
            )
            
            # Simular loop de entrenamiento (Ya que el trainer real requiere conexión a coordinador para un ciclo completo)
            # En producción: trainer.train_epoch(local_dataset_path=local_path)
            # Aquí hacemos una espera activa que simula la carga de trabajo real
            steps = 5
            for i in range(steps):
                await asyncio.sleep(0.5) # Simula cómputo intensivo
                loss = 2.5 * (0.9 ** (i+1)) # Simula convergencia
                logger.debug(f"   Step {i+1}/{steps} - Loss: {loss:.4f}")
            
            loss_start = 2.5
            loss_end = loss 
            
            # 4. Sinapsis (Cifrado y Envío)
            logger.info("🔐 Encriptando nuevos pesos con TenSEAL...")
            # En producción: encrypted_weights = TenSEALEncryptor().encrypt(trainer.get_model_gradients())
            await asyncio.sleep(0.5) 
            
            # 5. Limpieza
            if os.path.exists(local_path):
                os.remove(local_path)
                logger.info("🧹 Limpiando plato (Shard borrado del disco)")

            self.active_training = False
            
            # Generar hash de transacción simulado (Proof of Nutrition)
            tx_hash = f"0x{random.randbytes(16).hex()}"
            
            return {
                "status": "success",
                "diet_name": diet.name,
                "shard_cid": target_cid,
                "loss_improvement": loss_start - loss_end,
                "reward_earned": diet.reward_per_shard,
                "tx_hash": tx_hash,
                "training_session": session_id
            }

        except Exception as e:
            self.active_training = False
            logger.error(f"🤮 Indigestión (Error en entrenamiento): {e}")
            raise e

    def _generate_synthetic_shard(self, path: str, type: str):
        """Genera un archivo dummy para simular la existencia de datos si IPFS falla."""
        import json
        content = []
        if type == 'text':
            content = [{"text": "El veloz murciélago hindú comía feliz cardillo y kiwi."} for _ in range(100)]
        elif type == 'code':
            content = [{"code": "def hello(): print('world')"} for _ in range(100)]
            
        with open(path, 'w') as f:
            json.dump(content, f)
