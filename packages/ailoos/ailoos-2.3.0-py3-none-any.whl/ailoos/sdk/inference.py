"""
InferenceEngine - Motor de inferencia para nodos AILOOS
Maneja la carga de modelos, gestión de memoria y generación de texto.
"""

from typing import Optional, Dict, Any, List, Union
import torch
from pathlib import Path
import logging

from ..core.logging import get_logger
from ..models.empoorio_lm_real import EmpoorioLM, EmpoorioLMTokenizer, EmpoorioLMConfig
from .model_manager import ModelManager

logger = get_logger(__name__)

class InferenceEngine:
    """
    Motor de inferencia que gestiona modelos cargados y peticiones de generación.
    Utiliza LRU cache simple (por ahora 1 modelo activo) para optimizar memoria.
    """

    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.active_model_id: Optional[str] = None
        self.active_model: Optional[EmpoorioLM] = None
        self.active_tokenizer: Optional[EmpoorioLMTokenizer] = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
    def _load_model(self, model_id: str) -> bool:
        """
        Cargar modelo en memoria. Si ya está cargado, no hace nada.
        """
        if self.active_model_id == model_id and self.active_model is not None:
            return True

        logger.info(f"🔄 Loading model {model_id} for inference...")
        
        # 1. Resolver ruta del modelo
        # Asumimos que el ModelManager guarda los modelos en su models_dir/model_id
        # O necesitamos consultar al ModelManager dónde está.
        # Dado que ModelManager.download_model pide save_path, el SDK debe saber la estructura.
        # Vamos a asumir una estructura estándar: <models_dir>/<model_id>/
        
        model_path = Path(self.model_manager.models_dir) / model_id
        if not model_path.exists():
            logger.error(f"❌ Model path not found: {model_path}")
            # Intenta descargar si no existe (opcional, por ahora requerimos que esté descargado)
            return False

        try:
            # 2. Cargar modelo y tokenizer
            self.active_tokenizer = EmpoorioLMTokenizer.from_pretrained(model_path)
            self.active_model = EmpoorioLM.from_pretrained(model_path)
            
            # Mover a device
            self.active_model.to(self.device)
            self.active_model.eval()
            
            self.active_model_id = model_id
            logger.info(f"✅ Model {model_id} loaded successfully on {self.device}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading model {model_id}: {e}")
            self.active_model = None
            self.active_tokenizer = None
            self.active_model_id = None
            return False

    def generate(self, model_id: str, prompt: str, max_length: int = 50, 
                 temperature: float = 0.7, top_k: int = 50) -> Dict[str, Any]:
        """
        Generar texto usando el modelo especificado.
        
        Args:
            model_id: ID del modelo a usar
            prompt: Texto de entrada
            max_length: Longitud máxima a generar
            temperature: Temperatura de muestreo
            top_k: Top-K sampling
            
        Returns:
            Dict con 'generated_text' y metadatos
        """
        if not self._load_model(model_id):
            return {"error": f"Failed to load model {model_id}"}
            
        try:
            # Tokenizar
            inputs = self.active_tokenizer(prompt, return_tensors="pt")
            input_ids = inputs["input_ids"].to(self.device)
            
            # Generar
            with torch.no_grad():
                output_ids = self.active_model.generate(
                    input_ids,
                    max_length=max_length + input_ids.shape[-1],
                    temperature=temperature,
                    top_k=top_k
                )
            
            # Decodificar
            generated_text = self.active_tokenizer.decode(output_ids[0].tolist())
            
            return {
                "model_id": model_id,
                "prompt": prompt,
                "generated_text": generated_text,
                "tokens_generated": len(output_ids[0]) - len(input_ids[0])
            }
            
        except Exception as e:
            logger.error(f"❌ Inference error: {e}")
            return {"error": str(e)}

    def unload_model(self):
        """Liberar memoria del modelo activo."""
        if self.active_model:
            del self.active_model
            del self.active_tokenizer
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            self.active_model = None
            self.active_model_id = None
            logger.info("🧹 Model unloaded from memory")
