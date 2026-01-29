"""
Model Loader & Cache Manager
Gestor de rutas para almacenar pesos de modelos localmente.
"""

from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)

class ModelLoader:
    def __init__(self, cache_dir: str = "~/.ailoos/models"):
        self.cache_dir = Path(os.path.expanduser(cache_dir))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_model_path(self, model_name: str) -> str:
        """
        Retorna la ruta absoluta para un modelo dado.
        Si es un modelo de HuggingFace, retorna el ID para que transformers lo maneje.
        """
        local_path = self.cache_dir / model_name
        if local_path.exists():
            return str(local_path)
        return model_name # Retorna string original (ej: "Empoorio/EmpoorioLM-7B")

    def list_local_models(self):
        return [p.name for p in self.cache_dir.iterdir() if p.is_dir()]
