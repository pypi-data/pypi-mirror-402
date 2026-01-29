"""
RefineryClient - Cliente SDK para la Refinería de Datos de AILOOS.
Permite ingestar, limpiar y convertir datos crudos en "comida" (Shards) para el entrenamiento.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Union, Any
from pathlib import Path

from ..data.refinery_engine import refinery_engine
from ..data.dataset_downloader import DatasetDownloader, DownloadConfig, DownloadProgress
from ..core.logging import get_logger
from ..utils.hardware import get_hardware_info, get_training_capability_score

logger = get_logger(__name__)

class RefineryClient:
    """
    Cliente SDK para interactuar con el Motor de Refinería.
    Expone funcionalidades para descargar, procesar y registrar datasets.
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        # El motor es un singleton, pero lo envolvemos para consistencia SDK
        self.engine = refinery_engine
        self.downloader = None # Lazy init

    async def initialize(self) -> bool:
        """Inicializar recursos del cliente."""
        try:
            # Inicializar downloader con configuración por defecto (se puede mejorar)
            config_path = Path("config/datasets.yaml")
            if not config_path.exists():
                # Crear dir si no existe para evitar errores
                Path("config").mkdir(exist_ok=True)
                # No fallamos si no existe config, instanciamos sin ella para descargas directas
                
            if config_path.exists():
                self.downloader = DatasetDownloader(str(config_path))
            else:
                logger.warning("No datasets.yaml found, using minimal config")
                # Create a minimal dummy config if needed or pass None/empty path if supported
                # For now, let's create a temporary dummy file to satisfy DatasetDownloader
                dummy_path = Path("config/dummy_config.yaml")
                dummy_path.parent.mkdir(exist_ok=True)
                if not dummy_path.exists():
                     with open(dummy_path, 'w') as f: f.write("datasets: []")
                self.downloader = DatasetDownloader(str(dummy_path))
            logger.info(f"🏭 RefineryClient initialized for node {self.node_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error initializing RefineryClient: {e}")
            return False

    async def refine_from_url(self, url: str, dataset_name: str, 
                            data_type: str = "auto", metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Descarga un archivo desde una URL y lo refina.
        
        Args:
            url: URL del archivo a descargar (txt, json, etc)
            dataset_name: Nombre para el dataset procesado
            data_type: Tipo de datos ('text', 'json', 'auto')
            metadata: Metadatos extra
            
        Returns:
            Resultado del procesamiento
        """
        try:
            logger.info(f"⬇️ Downloading raw data from {url}...")
            
            # 1. Download to temporary location
            # Usamos un nombre temporal seguro
            import tempfile
            import aiohttp
            import aiofiles
            
            temp_dir = Path("./data/temp_ingest")
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            filename = url.split('/')[-1] or f"raw_{dataset_name}.dat"
            local_path = temp_dir / filename
            
            # Streaming download implementation
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise RuntimeError(f"Download failed: {response.status}")
                    
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    async with aiofiles.open(local_path, mode='wb') as f:
                        async for chunk in response.content.iter_chunked(1024 * 1024): # 1MB chunks
                            await f.write(chunk)
                            downloaded += len(chunk)
                            # Optional: Log progress (could be noisy)
                    
                    logger.info(f"✅ Download complete: {local_path} ({downloaded/(1024*1024):.2f} MB)")
            
            logger.info(f"✅ Download complete: {local_path}")
            
            # 2. Refine using Engine
            return await self.refine_local_file(
                file_path=str(local_path),
                dataset_name=dataset_name,
                data_type=data_type,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"❌ Error during URL refinement: {e}")
            return {"success": False, "error": str(e)}

    async def process_file(self, file_path: str, dataset_name: str, 
                          data_type: str = "auto") -> Dict:
        """Alias para refine_local_file por compatibilidad."""
        return await self.refine_local_file(file_path, dataset_name, data_type)
        
    def get_node_profile(self) -> Dict[str, Any]:
        """
        Detecta y retorna el perfil de hardware del nodo (Edge/Scout/Forge).
        Esencial para determinar capacidades de entrenamiento y validación.
        """
        try:
            score = get_training_capability_score()
            hw_info = get_hardware_info()
            
            role = "EDGE"
            if score >= 0.7:
                role = "FORGE"
            elif score >= 0.4:
                role = "SCOUT"
                
            descriptions = {
                "FORGE": "AI Model Training & Block Forging (High Power)",
                "SCOUT": "Data Validation & Relay (Medium Power)",
                "EDGE": "Inference Consumer & Light Client (Low Power)"
            }

            return {
                'role': role,
                'score': score,
                'description': descriptions.get(role, "Unknown"),
                'cpu_cores': hw_info['cpu']['logical_cores'],
                'memory_gb': hw_info['memory']['total_gb'],
                'gpu_available': hw_info['gpu']['available']
            }
        except Exception as e:
            logger.error(f"Error filtering node profile: {e}")
            return {
                'role': 'EDGE', 
                'score': 0.0, 
                'description': 'Fallback Profile',
                'error': str(e)
            }

    async def refine_local_file(self, file_path: str, dataset_name: str,
                              data_type: str = "auto", metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Procesa un archivo local a través del pipeline de refinería.
        
        Args:
            file_path: Ruta al archivo local
            dataset_name: Nombre del dataset
            data_type: Tipo de datos
            metadata: Metadatos extra
            
        Returns:
            Resultado del procesamiento (shards, cids, stats)
        """
        try:
            logger.info(f"🏭 Starting refinement pipeline for {dataset_name}...")
            
            # Ejecutar en thread pool para no bloquear el loop asyncio (el engine es síncrono por ahora)
            result = await asyncio.to_thread(
                self.engine.process_data_pipeline,
                data_input=file_path,
                dataset_name=dataset_name,
                input_type=data_type,
                metadata=metadata or {}
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error refining local file: {e}")
            return {"success": False, "error": str(e)}

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de la refinería."""
        return self.engine.get_stats()

    def list_datasets(self, **filters) -> List[Dict[str, Any]]:
        """
        Listar datasets registrados localmente.
        
        Args:
            **filters: Filtros opcionales (domain_filter, quality_min, type_filter)
            
        Returns:
            Lista de datasets
        """
        return self.engine.list_datasets(**filters)

    def get_storage_map(self) -> Dict[str, str]:
        """
        Obtener mapa de ubicaciones de almacenamiento.
        
        Returns:
            Diccionario con rutas absolutas de:
            - ingest_dir: Donde caen los datos crudos
            - shards_dir: Donde se guardan los shards (comida)
            - registry_path: Donde está el registro de datasets
        """
        base_dir = Path.cwd() / "data"
        return {
            "ingest_dir": str(base_dir / "temp_ingest"),
            "shards_dir": str(base_dir / "debug_shards"), # En prod sería IPFS local o shards/
            "registry_path": str(base_dir / "config" / "dataset_registry.json")
        }
