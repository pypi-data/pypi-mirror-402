"""
Data Loader for Ailoos Federated Learning
Handles loading of real datasets (HuggingFace, local files) for physical nodes.
"""

import torch
from torch.utils.data import Dataset, DataLoader
from typing import Dict, List, Any, Optional, Union
import logging
import os
from pathlib import Path

# Try to import datasets, but handle if not installed
try:
    from datasets import load_dataset as hf_load_dataset
    HAS_HF_DATASETS = True
except ImportError:
    HAS_HF_DATASETS = False

logger = logging.getLogger(__name__)

class TextDataset(Dataset):
    """Simple Dataset for text data."""
    def __init__(self, encodings):
        self.encodings = encodings

    def __getitem__(self, idx):
        return {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}

    def __len__(self):
        return len(self.encodings['input_ids'])

class AiloosDataLoader:
    """
    Loads and preprocesses data for federated training.
    Supports HuggingFace datasets and local text files.
    """
    
    def __init__(self, tokenizer, max_length: int = 512):
        self.tokenizer = tokenizer
        self.max_length = max_length
        
    def load_dataset(self, dataset_name: str, split: str = "train", 
                     num_samples: Optional[int] = None) -> Dataset:
        """
        Load a dataset and return a PyTorch Dataset.
        
        Args:
            dataset_name: Name of HF dataset or path to local file
            split: Dataset split (train, test, validation)
            num_samples: Limit number of samples (for quick testing/debugging)
        """
        logger.info(f"📚 Loading dataset: {dataset_name} (split={split})")
        
        raw_data = []
        
        # 1. Try loading from HuggingFace
        if HAS_HF_DATASETS and not os.path.exists(dataset_name):
            try:
                ds = hf_load_dataset(dataset_name, split=split)
                if num_samples:
                    ds = ds.select(range(min(len(ds), num_samples)))
                
                # Extract text content (assuming 'text' column exists, common in NLP datasets)
                # For specific datasets, this might need adjustment
                text_column = "text"
                if text_column not in ds.column_names:
                    # Try to find a suitable column
                    for col in ["content", "document", "sentence"]:
                        if col in ds.column_names:
                            text_column = col
                            break
                
                raw_data = ds[text_column]
                logger.info(f"✅ Loaded {len(raw_data)} samples from HuggingFace")
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to load from HuggingFace: {e}")
        
        # 2. Try loading from local file
        if not raw_data and os.path.exists(dataset_name):
            try:
                with open(dataset_name, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if num_samples:
                        lines = lines[:num_samples]
                    raw_data = [line.strip() for line in lines if line.strip()]
                logger.info(f"✅ Loaded {len(raw_data)} samples from local file")
            except Exception as e:
                logger.error(f"❌ Failed to load local file: {e}")

        # 3. Fallback to synthetic data if nothing else works
        if not raw_data:
            logger.warning("⚠️ No real data loaded. Using synthetic fallback.")
            return self._generate_synthetic_dataset(num_samples or 100)
            
        # Tokenize
        return self._tokenize_data(raw_data)

    def _tokenize_data(self, texts: List[str]) -> Dataset:
        """Tokenize list of texts."""
        if not self.tokenizer.pad_token:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
        encodings = self.tokenizer(
            texts,
            truncation=True,
            padding=True,
            max_length=self.max_length,
            return_tensors="pt"
        )
        return TextDataset(encodings)

    def _generate_synthetic_dataset(self, num_samples: int) -> Dataset:
        """Generate synthetic data for testing."""
        vocab_size = self.tokenizer.vocab_size
        input_ids = torch.randint(0, vocab_size, (num_samples, 32))
        attention_mask = torch.ones((num_samples, 32))
        
        return TextDataset({
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": input_ids.clone()
        })
