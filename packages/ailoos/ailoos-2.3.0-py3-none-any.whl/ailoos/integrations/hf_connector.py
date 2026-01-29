"""
Hugging Face Integration Connector
Acts as a bridge between the centralized HF Hub and the decentralized Ailoos Swarm.
"""

import os
import logging
import shutil
from pathlib import Path
from typing import Optional, List, Dict
import asyncio
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TransferSpeedColumn, TimeRemainingColumn

logger = logging.getLogger(__name__)
console = Console()

class HFConnector:
    """
    Bridge to Hugging Face Hub.
    Capabilities:
    1. Clone models/datasets
    2. Convert them to Ailoos Shards (simulated)
    3. Push trained adapters (LoRA) back to HF
    """
    
    def __init__(self, cache_dir: str = "~/.ailoos/models"):
        self.cache_dir = Path(os.path.expanduser(cache_dir))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        # Check for huggingface_hub availability
        try:
            import huggingface_hub
            self.api = huggingface_hub.HfApi()
            self.available = True
        except ImportError:
            logger.warning("huggingface_hub library not found. Integration limited.")
            self.available = False

    def download_model(self, repo_id: str, local_name: Optional[str] = None):
        """
        Downloads a model from HF Hub with CLI visual feedback.
        """
        if not self.available:
            logger.error("❌ HuggingFace Hub library is missing. 'pip install huggingface-hub'")
            return None

        from huggingface_hub import snapshot_download

        if not local_name:
            local_name = repo_id.split("/")[-1]
            
        target_path = self.cache_dir / local_name
        
        logger.info(f"🌉 Bridging {repo_id} -> {target_path}...")
        
        try:
            # We can't easily hook into snapshot_download progress bar without TQDM hook hacks,
            # so we show a spinner for the "metadata fetch" and then the download happens.
            # ideally we'd use hf_hub_download or similar file-by-file for granular progress.
            # For simplicity, we wrap the whole call in a status.
            
            with console.status(f"[bold cyan]Downloading {repo_id} from HF (cached)...[/bold cyan]", spinner="dots"):
                snapshot_download(
                    repo_id=repo_id,
                    local_dir=str(target_path),
                    local_dir_use_symlinks=False, # Copy actual files for decentralization
                    ignore_patterns=["*.msgpack", "*.h5", "*.ot"] # Keep only torch/safetensors
                )
            
            logger.info(f"✅ Download complete: {target_path}")
            return str(target_path)
            
            return str(target_path)
            
        except Exception as e:
            logger.error(f"❌ Download failed: {e}")
            return None

    def list_datasets(self, limit: int = 50, search: str = None, sort: str = "downloads"):
        """
        Queries HF Hub for popular datasets.
        Returns a list of dicts with essential metadata (name, size, downloads, license).
        """
        if not self.available:
            return []

        try:
            # Construct args
            args = {"sort": sort, "direction": -1, "limit": limit, "full": True}
            if search:
                args["search"] = search
            
            logger.info(f"🔍 Querying HF Hub: {args}")
            # Use the API list_datasets feature
            hf_datasets = self.api.list_datasets(**args)
            
            results = []
            
            for d in hf_datasets:
                try:
                    # Size calculation (File summing)
                    size_bytes = 0
                    if hasattr(d, 'siblings') and d.siblings:
                        # Defensive integer conversion
                        size_bytes = sum([s.rfilename.size for s in d.siblings if hasattr(s, 'rfilename') and hasattr(s.rfilename, 'size') and s.rfilename.size])
                    
                    # Category Fallback
                    category = None
                    if hasattr(d, 'tags') and d.tags:
                        category = next((t.split(':')[1] for t in d.tags if t.startswith("size_categories:")), None)

                    # Downloads - Specific check
                    downloads = 0
                    if hasattr(d, 'downloads'):
                        downloads = d.downloads
                    
                    meta = {
                        "id": d.id,
                        "name": d.id.split("/")[-1],
                        "author": d.author,
                        "downloads": downloads,
                        "likes": getattr(d, 'likes', 0),
                        "last_modified": str(d.lastModified) if hasattr(d, 'lastModified') else None,
                        "tags": getattr(d, 'tags', []),
                        "description": getattr(d, "description", "") or "No description",
                        "license": next((t for t in d.tags if t.startswith("license:")), "license:unknown").replace("license:", "") if hasattr(d, 'tags') and d.tags else "unknown",
                        "size_bytes": size_bytes if size_bytes > 0 else -1,
                        "size_category": category 
                    }
                    results.append(meta)
                except Exception as loop_e:
                    logger.warning(f"⚠️ Skipped dataset {d.id} due to parse error: {loop_e}")
                    continue
                
            logger.info(f"✅ Found {len(results)} datasets")
            return results
            
        except Exception as e:
            logger.error(f"❌ List datasets failed: {e}")
            return []

    def push_adapter(self, adapter_path: str, repo_id: str, token: str):
        """
        Pushes a trained LoRA adapter back to HF Hub.
        """
        if not self.available:
            return False
            
        try:
            self.api.upload_folder(
                folder_path=adapter_path,
                repo_id=repo_id,
                repo_type="model",
                token=token,
                commit_message="Pushed from Ailoos Decentralized Node 🚀"
            )
            logger.info(f"✅ Adapter pushed to https://huggingface.co/{repo_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Push failed: {e}")
            return False

# Global instance
hf_connector = HFConnector()
