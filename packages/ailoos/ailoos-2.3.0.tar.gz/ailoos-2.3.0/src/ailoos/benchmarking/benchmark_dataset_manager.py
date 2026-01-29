import logging
import hashlib
import json
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path
import os
from datetime import datetime
import shutil

# Optional dependencies
try:
    from datasets import load_dataset, Dataset, DatasetDict
    DATASETS_AVAILABLE = True
except ImportError:
    DATASETS_AVAILABLE = False
    print("Warning: datasets library not installed. Hugging Face datasets will not be available.")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

@dataclass
class DatasetConfig:
    name: str
    source: str  # "huggingface", "url", "local"
    path: Optional[str] = None
    subset: Optional[str] = None
    split: str = "test"
    num_samples: Optional[int] = None
    seed: int = 42
    cache_dir: Optional[str] = None
    expected_hash: Optional[str] = None

@dataclass
class DatasetInfo:
    name: str
    size: int
    num_samples: int
    features: List[str]
    hash: str
    last_modified: str
    metadata: Dict[str, Any]

class BenchmarkDatasetManager:
    """
    Gestión de datasets de benchmark estandarizados.
    Maneja descarga, cache, validación y preparación de datasets.
    """

    def __init__(self, cache_dir: str = "benchmark_datasets",
                 log_level: str = "INFO"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.logger = self._setup_logger(log_level)
        self._dataset_cache = {}

    def _setup_logger(self, log_level: str) -> logging.Logger:
        logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        logger.setLevel(getattr(logging, log_level.upper()))

        file_handler = logging.FileHandler(self.cache_dir / "dataset_manager.log")
        console_handler = logging.StreamHandler()

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def get_dataset(self, config: DatasetConfig) -> Optional[Dataset]:
        """
        Obtiene un dataset según la configuración proporcionada.
        """
        cache_key = self._get_cache_key(config)

        # Check cache first
        if cache_key in self._dataset_cache:
            self.logger.info(f"Loading dataset {config.name} from memory cache")
            return self._dataset_cache[cache_key]

        # Check disk cache
        cached_path = self._get_cached_dataset_path(config)
        if cached_path.exists() and self._is_cache_valid(cached_path, config):
            self.logger.info(f"Loading dataset {config.name} from disk cache")
            dataset = self._load_from_cache(cached_path, config)
            if dataset:
                self._dataset_cache[cache_key] = dataset
                return dataset

        # Download/load dataset
        self.logger.info(f"Downloading/loading dataset {config.name}")
        dataset = self._download_dataset(config)
        if dataset:
            self._save_to_cache(dataset, config)
            self._dataset_cache[cache_key] = dataset

        return dataset

    def _get_cache_key(self, config: DatasetConfig) -> str:
        """Genera una clave única para el cache."""
        config_str = f"{config.name}_{config.source}_{config.path}_{config.subset}_{config.split}_{config.num_samples}_{config.seed}"
        return hashlib.md5(config_str.encode()).hexdigest()

    def _get_cached_dataset_path(self, config: DatasetConfig) -> Path:
        """Obtiene la ruta del cache para un dataset."""
        cache_key = self._get_cache_key(config)
        return self.cache_dir / f"{cache_key}.json"

    def _is_cache_valid(self, cache_path: Path, config: DatasetConfig) -> bool:
        """Verifica si el cache es válido."""
        if not cache_path.exists():
            return False

        try:
            with open(cache_path / "metadata.json", 'r') as f:
                metadata = json.load(f)

            # Check if config matches
            cached_config = metadata.get("config", {})
            if cached_config != config.__dict__:
                return False

            # Check hash if provided
            if config.expected_hash:
                if metadata.get("hash") != config.expected_hash:
                    self.logger.warning(f"Hash mismatch for cached dataset {config.name}")
                    return False

            return True
        except Exception as e:
            self.logger.warning(f"Error validating cache for {config.name}: {e}")
            return False

    def _download_dataset(self, config: DatasetConfig) -> Optional[Dataset]:
        """Descarga un dataset según su fuente."""
        try:
            if config.source == "huggingface":
                return self._download_huggingface_dataset(config)
            elif config.source == "url":
                return self._download_url_dataset(config)
            elif config.source == "local":
                return self._load_local_dataset(config)
            else:
                self.logger.error(f"Unsupported dataset source: {config.source}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to download dataset {config.name}: {e}")
            return None

    def _download_huggingface_dataset(self, config: DatasetConfig) -> Optional[Dataset]:
        """Descarga un dataset de Hugging Face."""
        if not DATASETS_AVAILABLE:
            self.logger.error("datasets library not available for Hugging Face datasets")
            return None

        try:
            load_kwargs = {
                "path": config.path or config.name,
                "split": config.split
            }

            if config.subset:
                load_kwargs["name"] = config.subset

            dataset = load_dataset(**load_kwargs)

            # Apply sampling if specified
            if config.num_samples and isinstance(dataset, Dataset):
                dataset = dataset.shuffle(seed=config.seed).select(range(min(config.num_samples, len(dataset))))

            return dataset
        except Exception as e:
            self.logger.error(f"Failed to load Hugging Face dataset {config.name}: {e}")
            return None

    def _download_url_dataset(self, config: DatasetConfig) -> Optional[Dataset]:
        """Descarga un dataset desde una URL."""
        if not REQUESTS_AVAILABLE:
            self.logger.error("requests library not available for URL downloads")
            return None

        if not config.path:
            self.logger.error("URL path required for URL dataset source")
            return None

        try:
            response = requests.get(config.path)
            response.raise_for_status()

            # For now, assume JSON format - extend for other formats
            data = response.json()

            # Convert to Dataset format
            from datasets import Dataset
            dataset = Dataset.from_list(data)

            if config.num_samples:
                dataset = dataset.shuffle(seed=config.seed).select(range(min(config.num_samples, len(dataset))))

            return dataset
        except Exception as e:
            self.logger.error(f"Failed to download URL dataset {config.name}: {e}")
            return None

    def _load_local_dataset(self, config: DatasetConfig) -> Optional[Dataset]:
        """Carga un dataset local."""
        if not config.path:
            self.logger.error("Local path required for local dataset source")
            return None

        local_path = Path(config.path)
        if not local_path.exists():
            self.logger.error(f"Local dataset path does not exist: {local_path}")
            return None

        try:
            if local_path.is_file():
                # Assume JSON for now
                with open(local_path, 'r') as f:
                    data = json.load(f)

                from datasets import Dataset
                dataset = Dataset.from_list(data)
            else:
                # Assume directory with multiple files
                # This is a simplified implementation
                self.logger.warning("Directory datasets not fully implemented")
                return None

            if config.num_samples:
                dataset = dataset.shuffle(seed=config.seed).select(range(min(config.num_samples, len(dataset))))

            return dataset
        except Exception as e:
            self.logger.error(f"Failed to load local dataset {config.name}: {e}")
            return None

    def _save_to_cache(self, dataset: Dataset, config: DatasetConfig):
        """Guarda un dataset en el cache."""
        cache_path = self._get_cached_dataset_path(config)
        cache_path.mkdir(exist_ok=True)

        try:
            # Save dataset
            dataset_path = cache_path / "dataset.json"
            with open(dataset_path, 'w') as f:
                json.dump(dataset.to_list(), f, indent=2)

            # Save metadata
            metadata = {
                "config": config.__dict__,
                "num_samples": len(dataset),
                "features": list(dataset.features.keys()) if hasattr(dataset, 'features') else [],
                "hash": self._calculate_dataset_hash(dataset),
                "created": datetime.now().isoformat()
            }

            metadata_path = cache_path / "metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            self.logger.info(f"Dataset {config.name} cached successfully")
        except Exception as e:
            self.logger.error(f"Failed to cache dataset {config.name}: {e}")

    def _load_from_cache(self, cache_path: Path, config: DatasetConfig) -> Optional[Dataset]:
        """Carga un dataset desde el cache."""
        try:
            dataset_path = cache_path / "dataset.json"
            with open(dataset_path, 'r') as f:
                data = json.load(f)

            from datasets import Dataset
            dataset = Dataset.from_list(data)

            # Apply sampling if needed
            if config.num_samples and len(dataset) > config.num_samples:
                dataset = dataset.shuffle(seed=config.seed).select(range(config.num_samples))

            return dataset
        except Exception as e:
            self.logger.error(f"Failed to load cached dataset: {e}")
            return None

    def _calculate_dataset_hash(self, dataset: Dataset) -> str:
        """Calcula un hash para el dataset."""
        try:
            # Simple hash based on string representation of first few samples
            sample_data = str(dataset[:min(10, len(dataset))])
            return hashlib.md5(sample_data.encode()).hexdigest()
        except:
            return "unknown"

    def list_available_datasets(self) -> List[DatasetInfo]:
        """Lista los datasets disponibles en el cache."""
        datasets = []
        for cache_dir in self.cache_dir.iterdir():
            if cache_dir.is_dir():
                metadata_path = cache_dir / "metadata.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)

                        info = DatasetInfo(
                            name=metadata.get("config", {}).get("name", "unknown"),
                            size=metadata_path.stat().st_size,
                            num_samples=metadata.get("num_samples", 0),
                            features=metadata.get("features", []),
                            hash=metadata.get("hash", "unknown"),
                            last_modified=metadata.get("created", "unknown"),
                            metadata=metadata
                        )
                        datasets.append(info)
                    except Exception as e:
                        self.logger.warning(f"Error reading metadata for {cache_dir}: {e}")

        return datasets

    def clear_cache(self, dataset_name: Optional[str] = None):
        """Limpia el cache de datasets."""
        if dataset_name:
            # Find and remove specific dataset
            for cache_dir in self.cache_dir.iterdir():
                if cache_dir.is_dir():
                    metadata_path = cache_dir / "metadata.json"
                    if metadata_path.exists():
                        try:
                            with open(metadata_path, 'r') as f:
                                metadata = json.load(f)
                            if metadata.get("config", {}).get("name") == dataset_name:
                                shutil.rmtree(cache_dir)
                                self.logger.info(f"Cleared cache for dataset {dataset_name}")
                                break
                        except:
                            pass
        else:
            # Clear all cache
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(exist_ok=True)
            self._dataset_cache.clear()
            self.logger.info("Cleared all dataset cache")

    def validate_dataset_integrity(self, config: DatasetConfig) -> bool:
        """Valida la integridad de un dataset."""
        dataset = self.get_dataset(config)
        if not dataset:
            return False

        if config.expected_hash:
            current_hash = self._calculate_dataset_hash(dataset)
            if current_hash != config.expected_hash:
                self.logger.error(f"Dataset integrity check failed for {config.name}")
                return False

        self.logger.info(f"Dataset integrity validated for {config.name}")
        return True