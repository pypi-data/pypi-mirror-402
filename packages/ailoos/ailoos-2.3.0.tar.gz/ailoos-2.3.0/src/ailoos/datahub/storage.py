"""
DataHubStorage - Gestión de Almacenamiento Local para Nodos
Maneja la persistencia de shards, pinning y garbage collection.
"""

import os
import shutil
import time
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

from ..core.logging import get_logger

logger = get_logger(__name__)

class DataHubStorage:
    """
    Gestor de almacenamiento local del nodo.
    Estructura:
    - data/datahub/inbox/  -> Descargas temporales (sujetas a GC)
    - data/datahub/pinned/ -> Contenido persistente (protegido)
    """

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.inbox_path = base_path / "inbox"
        self.pinned_path = base_path / "pinned"
        self.metadata_path = base_path / "storage_metadata.json"
        
        self._initialize_storage()
        self.metadata = self._load_metadata()

    def _initialize_storage(self):
        """Crea la estructura de directorios si no existe."""
        self.inbox_path.mkdir(parents=True, exist_ok=True)
        self.pinned_path.mkdir(parents=True, exist_ok=True)

    def _load_metadata(self) -> Dict:
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_metadata(self):
        try:
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving storage metadata: {e}")

    def list_inbox_files(self) -> List[Dict[str, Any]]:
        """Lista archivos en el Inbox con detalles."""
        files = []
        for f in self.inbox_path.glob("**/*"):
            if f.is_file():
                stat = f.stat()
                files.append({
                    "name": f.name,
                    "size_mb": stat.st_size / (1024*1024),
                    "created": datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M'),
                    "path": str(f)
                })
        return files

    def list_pinned_files(self) -> List[Dict[str, Any]]:
        """Lista archivos pinneados (protegidos)."""
        files = []
        for f in self.pinned_path.glob("**/*"):
            if f.is_file():
                stat = f.stat()
                meta = self.metadata.get(f.name, {})
                files.append({
                    "name": f.name,
                    "size_mb": stat.st_size / (1024*1024),
                    "pinned_at": meta.get("pinned_at", "Unknown"),
                    "category": meta.get("category", "General"),
                    "path": str(f)
                })
        return files

    def pin_file(self, filename: str, category: str = "General") -> bool:
        """Mueve un archivo del Inbox a Pinned (persistente)."""
        source = self.inbox_path / filename
        dest = self.pinned_path / filename
        
        if not source.exists():
            logger.warning(f"File not found in inbox: {filename}")
            return False
            
        try:
            shutil.move(str(source), str(dest))
            self.metadata[filename] = {
                "pinned_at": datetime.now().isoformat(),
                "category": category,
                "original_source": "inbox"
            }
            self._save_metadata()
            logger.info(f"📌 Pinned file: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error pinning file: {e}")
            return False

    def unpin_file(self, filename: str) -> bool:
        """Mueve un archivo de Pinned a Inbox (susceptible a GC)."""
        source = self.pinned_path / filename
        dest = self.inbox_path / filename
        
        if not source.exists():
            return False
            
        try:
            shutil.move(str(source), str(dest))
            if filename in self.metadata:
                del self.metadata[filename]
                self._save_metadata()
            logger.info(f"Unpinned file: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error unpinning file: {e}")
            return False

    def run_garbage_collection(self, max_age_days: int = 7) -> Dict[str, int]:
        """Elimina archivos del Inbox más antiguos que max_age_days."""
        deleted_count = 0
        freed_space_mb = 0.0
        cutoff_time = time.time() - (max_age_days * 86400)
        
        for f in self.inbox_path.glob("**/*"):
            if f.is_file():
                stat = f.stat()
                if stat.st_mtime < cutoff_time:
                    try:
                        size = stat.st_size
                        f.unlink()
                        deleted_count += 1
                        freed_space_mb += size / (1024*1024)
                    except Exception as e:
                        logger.error(f"Error deleting {f.name}: {e}")
                        
        logger.info(f"🧹 GC Completed: Deleted {deleted_count} files, Freed {freed_space_mb:.2f} MB")
        return {"deleted_files": deleted_count, "freed_mb": freed_space_mb}

    def get_storage_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de uso de disco."""
        total, used, free = shutil.disk_usage(self.base_path)
        
        # Calcular uso específico de Ailoos
        inbox_size = sum(f.stat().st_size for f in self.inbox_path.glob("**/*") if f.is_file())
        pinned_size = sum(f.stat().st_size for f in self.pinned_path.glob("**/*") if f.is_file())
        
        return {
            "total_disk_gb": total / (1024**3),
            "free_disk_gb": free / (1024**3),
            "inbox_usage_mb": inbox_size / (1024**2),
            "pinned_usage_mb": pinned_size / (1024**2),
            "total_ailoos_usage_mb": (inbox_size + pinned_size) / (1024**2)
        }
