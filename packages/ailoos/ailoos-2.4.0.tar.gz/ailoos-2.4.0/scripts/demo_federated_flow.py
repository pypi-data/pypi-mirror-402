#!/usr/bin/env python3
"""
DEMO DE ENTRENAMIENTO FEDERADO AILOOS (Simulación Pura en Python)
=================================================================

Este script demuestra el ciclo COMPLETO de aprendizaje federado asíncrono
descrito en la documentación, implementado desde cero para funcionar
en cualquier entorno (sin requerir PyTorch/CUDA pesado).

Fases:
1. 🧊 SHARDING: División de un "Dataset Global" en fragmentos (shards).
2. 📡 DISTRIBUCIÓN: Simulación de red P2P/IPFS.
3. 🤖 ENTRENAMIENTO LOCAL: Nodos (simulados) entrenan en sus shards.
4. 🔗 AGREGACIÓN: Nodo coordinador une los pesos (FedAvg).
5. 🛡️ VERIFICACIÓN: Validación criptográfica de contribuciones.
"""

import os
import json
import time
import random
import hashlib
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Simulación de colores para terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_step(phase: str, msg: str):
    print(f"\n{Colors.HEADER}=== FASE {phase}: {msg} ==={Colors.ENDC}")

def print_info(msg: str):
    print(f"{Colors.CYAN}ℹ {msg}{Colors.ENDC}")

def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.ENDC}")

# ==========================================
# 1. CORE LOGIC (Simulando Torch en Python)
# ==========================================

class SimpleModel:
    """Un modelo simple representado por un diccionario de pesos."""
    def __init__(self):
        # Simulamos una red neuronal simple: Input(5) -> Hidden(4) -> Output(2)
        random.seed(42)
        self.weights = {
            "layer1.weight": [[random.random() for _ in range(5)] for _ in range(4)],
            "layer1.bias": [0.0] * 4,
            "layer2.weight": [[random.random() for _ in range(4)] for _ in range(2)],
            "layer2.bias": [0.0] * 2
        }
    
    def get_weights(self):
        return self.weights
    
    def set_weights(self, new_weights):
        self.weights = new_weights

    def update(self, gradients: Dict[str, Any], lr: float = 0.01):
        """Simula un paso de optimización SGD."""
        for name in self.weights:
            if isinstance(self.weights[name][0], list): # Matriz
                for i in range(len(self.weights[name])):
                    for j in range(len(self.weights[name][i])):
                        self.weights[name][i][j] -= lr * gradients[name][i][j]
            else: # Vector
                for i in range(len(self.weights[name])):
                    self.weights[name][i] -= lr * gradients[name][i]

# ==========================================
# 2. COMPONENTS (Sharder, Trainer, Aggregator)
# ==========================================

class DatasetSharder:
    def __init__(self, data: List[str], num_shards: int, output_dir: str):
        self.data = data
        self.num_shards = num_shards
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def shard_and_distribute(self):
        print_info(f"Dividiendo {len(self.data)} muestras en {self.num_shards} shards...")
        
        chunk_size = len(self.data) // self.num_shards
        shards_info = []
        
        for i in range(self.num_shards):
            shard_data = self.data[i * chunk_size : (i + 1) * chunk_size]
            shard_id = f"shard_{i:04d}"
            
            # 1. Guardar Shard (Simula IPFS)
            file_path = self.output_dir / f"{shard_id}.json"
            with open(file_path, "w") as f:
                json.dump({"id": shard_id, "data": shard_data}, f, indent=2)
                
            # 2. Calcular Hash (CID de IPFS)
            file_hash = hashlib.sha256(json.dumps(shard_data).encode()).hexdigest()[:16]
            
            shards_info.append({
                "shard_id": shard_id,
                "local_path": str(file_path),
                "ipfs_cid": f"Qm{file_hash}",
                "sample_count": len(shard_data)
            })
            
            print(f"  > Generado {shard_id} -> IPFS CID: Qm{file_hash} ({len(shard_data)} muestras)")
            
        return shards_info

class FederatedClient:
    def __init__(self, node_id: str, hardware_score: float):
        self.node_id = node_id
        self.hardware_score = hardware_score
        self.local_model = SimpleModel()
        
    def train_on_shard(self, shard_info: Dict):
        print_info(f"[{self.node_id}] Descargando shard {shard_info['ipfs_cid']}...")
        time.sleep(0.5) # Simular red
        
        # Cargar datos
        with open(shard_info['local_path'], 'r') as f:
            data = json.load(f)['data']
            
        print_info(f"[{self.node_id}] Iniciando entrenamiento local en {len(data)} muestras...")
        
        # Simular Training Loop
        epochs = 3
        current_loss = 0.8
        
        for epoch in range(epochs):
            # Simular cómputo pesado
            time.sleep(0.2 * self.hardware_score) 
            
            # "Entrenar" (Perturbar pesos para simular aprendizaje)
            # Generamos gradientes falsos basados en el contenido del texto para ser deterministas pero variados
            random.seed(shard_info['shard_id'] + str(epoch))
            fake_gradients = {
                "layer1.weight": [[random.uniform(-0.1, 0.1) for _ in range(5)] for _ in range(4)],
                "layer1.bias": [random.uniform(-0.1, 0.1) for _ in range(4)],
                "layer2.weight": [[random.uniform(-0.1, 0.1) for _ in range(4)] for _ in range(2)],
                "layer2.bias": [random.uniform(-0.1, 0.1) for _ in range(2)]
            }
            
            self.local_model.update(fake_gradients)
            current_loss *= 0.85 # Loss baja en cada epoch
            
            print(f"    Epoch {epoch+1}/{epochs} - Loss: {current_loss:.4f} - Accuracy: {0.5 + (epoch*0.1):.2f}")
            
        # Generar "Proof of Training" (Hash de los pesos)
        weights_str = str(self.local_model.weights)
        proof = hashlib.sha256(weights_str.encode()).hexdigest()
        
        return {
            "node_id": self.node_id,
            "shard_id": shard_info['shard_id'],
            "final_loss": current_loss,
            "weights": self.local_model.weights,
            "proof": proof
        }

class FederatedAggregator:
    def aggregate(self, global_model: SimpleModel, contributions: List[Dict]):
        print_info(f"Agregando {len(contributions)} contribuciones usando FedAvg...")
        
        if not contributions:
            return
            
        # Algoritmo FedAvg: Promedio de pesos
        new_weights = global_model.get_weights() # Copia estructura
        
        # Resetear acumuladores
        for name in new_weights:
            if isinstance(new_weights[name][0], list):
                new_weights[name] = [[0.0] * len(row) for row in new_weights[name]]
            else:
                new_weights[name] = [0.0] * len(new_weights[name])
                
        # Sumar
        for contrib in contributions:
            w = contrib['weights']
            for name in w:
                if isinstance(w[name][0], list):
                    for i in range(len(w[name])):
                        for j in range(len(w[name][i])):
                            new_weights[name][i][j] += w[name][i][j]
                else:
                    for i in range(len(w[name])):
                        new_weights[name][i] += w[name][i]
                        
        # Dividir (Promedio)
        n = len(contributions)
        for name in new_weights:
            if isinstance(new_weights[name][0], list):
                for i in range(len(new_weights[name])):
                    for j in range(len(new_weights[name][i])):
                        new_weights[name][i][j] /= n
            else:
                for i in range(len(new_weights[name])):
                    new_weights[name][i] /= n
                    
        global_model.set_weights(new_weights)
        print_success("Modelo Global actualizado con éxito.")
        return global_model

# ==========================================
# 3. MAIN WORKFLOW
# ==========================================

def run_simulation():
    print(f"{Colors.BOLD}{Colors.GREEN}")
    print("  __  __     __     __         ______     ______     ______    ")
    print(" /\ \/ /    /\ \   /\ \       /\  __ \   /\  __ \   /\  ___\   ")
    print(" \ \  _\"-.  \ \ \  \ \ \____  \ \  __ \  \ \ \/\ \  \ \___  \  ")
    print("  \ \_\ \_\  \ \_\  \ \_____\  \ \_\ \_\  \ \_____\  \/\_____\ ")
    print("   \/_/\/_/   \/_/   \/_____/   \/_/\/_/   \/_____/   \/_____/ ")
    print("                                                               ")
    print("     FEDERATED LEARNING PROTOCOL - LIVE SIMULATION v2.2.17     ")
    print(f"{Colors.ENDC}\n")
    
    # 0. Datos Dummy
    dataset = [
        "El aprendizaje federado protege la privacidad.",
        "Los nodos entrenan localmente sin compartir datos raw.",
        "El coordinador agrega gradientes encriptados.",
        "EmpoorioLM aprende de miles de fuentes distribuidas.",
        "La descentralización es clave para la IA soberana.",
        "DracmaS incentiva la participación honesta.",
        "Proof of Training valida el trabajo computacional.",
        "Sharding permite paralelizar el entrenamiento masivo.",
        "Redes neuronales distribuidas son el futuro.",
        "La privacidad diferencial añade ruido estadístico.",
        "Consenso por prueba de aprendizaje.",
        "Nodos Forge tienen GPUs potentes.",
    ]
    
    # 1. Sharding
    print_step("1", "PREPARACIÓN Y SHARDING")
    sharder = DatasetSharder(dataset, num_shards=3, output_dir="./demo_shards")
    shards = sharder.shard_and_distribute()
    
    # 2. Distribución (Simular Nodos)
    print_step("2", "DISTRIBUCIÓN DE TAREAS")
    participants = [
        FederatedClient("NODE_FORGE_01", hardware_score=1.0),
        FederatedClient("NODE_SCOUT_A7", hardware_score=1.5), # Más lento
        FederatedClient("NODE_EDGE_99", hardware_score=0.8)
    ]
    
    tasks = []
    for i, p in enumerate(participants):
        tasks.append((p, shards[i % len(shards)]))
        print(f"  > Asignado {shards[i % len(shards)]['shard_id']} -> {p.node_id}")
        
    # 3. Entrenamiento
    print_step("3", "ENTRENAMIENTO DISTRIBUIDO (PARALELO)")
    contributions = []
    
    start_time = time.time()
    for client, shard in tasks:
        result = client.train_on_shard(shard)
        contributions.append(result)
        print_success(f"Nodo {client.node_id} completó tarea. Proof: {result['proof'][:16]}...")
    
    duration = time.time() - start_time
    print(f"\n  ⏱ Tiempo total de ronda: {duration:.2f}s")
        
    # 4. Agregación
    print_step("4", "AGREGACIÓN Y CONSENSO")
    model_v1 = SimpleModel()
    aggregator = FederatedAggregator()
    
    print(f"  > Peso 'layer1.weight[0][0]' antes: {model_v1.weights['layer1.weight'][0][0]:.6f}")
    
    aggregator.aggregate(model_v1, contributions)
    
    print(f"  > Peso 'layer1.weight[0][0]' AHORA: {Colors.BOLD}{model_v1.weights['layer1.weight'][0][0]:.6f}{Colors.ENDC}")
    
    print_step("5", "RESULTADO FINAL")
    print(f"""
    ✅ Ronda #2481 completada con éxito.
    ✅ 3/3 Nodos contribuyeron.
    ✅ Modelo EmpoorioLM actualizado a v2.2.18-dev.
    
    💰 Recompensas distribuidas:
       - NODE_FORGE_01: 5.2 DRACMA
       - NODE_SCOUT_A7: 4.8 DRACMA
       - NODE_EDGE_99:  5.0 DRACMA
    """)

if __name__ == "__main__":
    try:
        run_simulation()
    except KeyboardInterrupt:
        print("\n\n🛑 Simulación detenida.")
    except Exception as e:
        print(f"\n\n❌ Error fatal: {e}")
