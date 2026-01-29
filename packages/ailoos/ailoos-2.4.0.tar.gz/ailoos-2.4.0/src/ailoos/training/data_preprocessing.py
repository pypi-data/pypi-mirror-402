"""
Data Preprocessing para EmpoorioLM - FASE REAL-5
Preprocesamiento de datos con tokenización BPE usando el tokenizer AILOOS entrenado.
Incluye limpieza, tokenización y preparación para entrenamiento.
"""

import os
import logging
import re
from typing import Dict, List, Optional, Union, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor

import torch
from datasets import Dataset
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PreprocessingConfig:
    """Configuración del preprocesamiento de datos."""
    max_length: int = 512
    min_length: int = 10
    tokenizer_path: Optional[str] = None
    text_column: str = "text"
    batch_size: int = 1000
    num_proc: int = mp.cpu_count()
    add_special_tokens: bool = True
    truncation: bool = True
    padding: bool = False
    clean_text: bool = True
    lowercase: bool = False
    remove_urls: bool = True
    remove_emails: bool = True
    remove_html: bool = True
    normalize_whitespace: bool = True


class AILOOSTokenizerWrapper:
    """
    Wrapper para el tokenizer AILOOS BPE.
    """

    def __init__(self, tokenizer_path: Optional[str] = None):
        self.tokenizer = None
        self._load_tokenizer(tokenizer_path)

    def _load_tokenizer(self, tokenizer_path: Optional[str] = None):
        """Cargar tokenizer AILOOS."""
        try:
            # Importar el wrapper existente
            from src.ailoos.inference.sentencepiece_tokenizer import create_ailoos_tokenizer

            self.tokenizer = create_ailoos_tokenizer(tokenizer_path)
            logger.info("✅ Tokenizer AILOOS cargado")

        except Exception as e:
            logger.warning(f"❌ Error cargando tokenizer AILOOS: {e}")
            logger.warning("Usando tokenizer GPT-2 como fallback")
            from transformers import GPT2Tokenizer
            self.tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
            self.tokenizer.pad_token = self.tokenizer.eos_token

    @property
    def vocab_size(self) -> int:
        """Tamaño del vocabulario."""
        return self.tokenizer.vocab_size

    @property
    def pad_token_id(self) -> int:
        """ID del token de padding."""
        return getattr(self.tokenizer, 'pad_token_id', self.tokenizer.eos_token_id)

    @property
    def eos_token_id(self) -> int:
        """ID del token de fin de secuencia."""
        return self.tokenizer.eos_token_id

    @property
    def bos_token_id(self) -> int:
        """ID del token de inicio de secuencia."""
        return getattr(self.tokenizer, 'bos_token_id', self.tokenizer.eos_token_id)

    def encode(self, text: str, **kwargs) -> List[int]:
        """Codificar texto a tokens."""
        return self.tokenizer.encode(text, add_special_tokens=False)

    def decode(self, tokens: List[int], **kwargs) -> str:
        """Decodificar tokens a texto."""
        return self.tokenizer.decode(tokens, skip_special_tokens=True)

    def __call__(self, text: str, **kwargs):
        """Interface similar a transformers."""
        tokens = self.encode(text)
        return {"input_ids": tokens}


class TextPreprocessor:
    """
    Preprocesador de texto con limpieza avanzada.
    """

    def __init__(self, config: PreprocessingConfig):
        self.config = config

        # Patrones de regex para limpieza
        self.url_pattern = re.compile(r'https?://\S+|www\.\S+')
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.html_pattern = re.compile(r'<[^>]+>')
        self.whitespace_pattern = re.compile(r'\s+')

    def clean_text(self, text: str) -> str:
        """Limpiar texto según configuración."""
        if not self.config.clean_text:
            return text

        # Convertir a minúsculas si configurado
        if self.config.lowercase:
            text = text.lower()

        # Remover URLs
        if self.config.remove_urls:
            text = self.url_pattern.sub('', text)

        # Remover emails
        if self.config.remove_emails:
            text = self.email_pattern.sub('', text)

        # Remover HTML
        if self.config.remove_html:
            text = self.html_pattern.sub('', text)

        # Normalizar espacios en blanco
        if self.config.normalize_whitespace:
            text = self.whitespace_pattern.sub(' ', text)

        return text.strip()

    def validate_text(self, text: str) -> bool:
        """Validar que el texto cumple criterios mínimos."""
        if not text or len(text.strip()) < self.config.min_length:
            return False

        # Verificar que no sea mayoritariamente caracteres especiales
        alpha_ratio = sum(c.isalpha() for c in text) / len(text) if text else 0
        if alpha_ratio < 0.1:  # Menos del 10% alfanumérico
            return False

        return True


class DataPreprocessor:
    """
    Preprocesador completo de datos con tokenización BPE.
    """

    def __init__(self, config: PreprocessingConfig):
        self.config = config
        self.tokenizer = AILOOSTokenizerWrapper(config.tokenizer_path)
        self.text_preprocessor = TextPreprocessor(config)

        logger.info("🔧 DataPreprocessor inicializado")
        logger.info(f"   Tokenizer vocab_size: {self.tokenizer.vocab_size}")
        logger.info(f"   Max length: {config.max_length}")

    def preprocess_batch(self, batch: Dict[str, List[Any]]) -> Dict[str, List[Any]]:
        """
        Preprocesar un batch de datos.
        """
        texts = batch[self.config.text_column]

        processed_batch = {
            "input_ids": [],
            "attention_mask": [],
            "labels": []
        }

        for text in texts:
            # Limpiar texto
            cleaned_text = self.text_preprocessor.clean_text(text)

            # Validar
            if not self.text_preprocessor.validate_text(cleaned_text):
                # Si no pasa validación, crear entrada vacía
                empty_tokens = [self.tokenizer.pad_token_id] * self.config.max_length
                processed_batch["input_ids"].append(empty_tokens)
                processed_batch["attention_mask"].append([0] * self.config.max_length)
                processed_batch["labels"].append(empty_tokens)
                continue

            # Tokenizar
            tokens = self.tokenizer.encode(cleaned_text)

            # Truncar/padear
            if len(tokens) > self.config.max_length:
                tokens = tokens[:self.config.max_length]
            elif len(tokens) < self.config.max_length and self.config.padding:
                tokens.extend([self.tokenizer.pad_token_id] * (self.config.max_length - len(tokens)))

            # Crear attention_mask
            attention_mask = [1] * len(tokens) + [0] * (self.config.max_length - len(tokens))

            # Padear si es necesario
            if len(tokens) < self.config.max_length:
                tokens.extend([self.tokenizer.pad_token_id] * (self.config.max_length - len(tokens)))

            # Para causal LM, labels = input_ids
            labels = tokens.copy()

            processed_batch["input_ids"].append(tokens)
            processed_batch["attention_mask"].append(attention_mask)
            processed_batch["labels"].append(labels)

        return processed_batch

    def preprocess_dataset(self, dataset: Dataset) -> Dataset:
        """
        Preprocesar dataset completo usando map.
        """
        logger.info("🚀 Preprocesando dataset con tokenización BPE...")

        # Función de preprocessing para map
        def preprocess_function(examples):
            return self.preprocess_batch(examples)

        # Aplicar preprocessing
        processed_dataset = dataset.map(
            preprocess_function,
            batched=True,
            batch_size=self.config.batch_size,
            num_proc=self.config.num_proc,
            remove_columns=[self.config.text_column]  # Remover columna original
        )

        # Convertir a tensores de PyTorch
        processed_dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "labels"])

        logger.info("✅ Preprocesamiento completado")
        logger.info(f"   Dataset size: {len(processed_dataset)}")
        logger.info(f"   Columns: {processed_dataset.column_names}")

        return processed_dataset

    def get_preprocessing_stats(self, dataset: Dataset) -> Dict[str, Any]:
        """Obtener estadísticas del preprocesamiento."""
        stats = {
            "original_size": len(dataset),
            "tokenizer_vocab_size": self.tokenizer.vocab_size,
            "max_length": self.config.max_length,
            "cleaning_enabled": self.config.clean_text
        }

        # Calcular estadísticas de tokens
        if hasattr(dataset, 'column_names') and 'input_ids' in dataset.column_names:
            sample_lengths = []
            for i in range(min(100, len(dataset))):  # Muestra de primeros 100
                tokens = dataset[i]['input_ids']
                if isinstance(tokens, torch.Tensor):
                    # Contar tokens no padding
                    non_pad = (tokens != self.tokenizer.pad_token_id).sum().item()
                    sample_lengths.append(non_pad)
                else:
                    sample_lengths.append(len(tokens))

            if sample_lengths:
                stats["avg_tokens_per_sample"] = np.mean(sample_lengths)
                stats["max_tokens_per_sample"] = np.max(sample_lengths)
                stats["min_tokens_per_sample"] = np.min(sample_lengths)

        return stats


def create_data_preprocessor(
    max_length: int = 512,
    tokenizer_path: Optional[str] = None,
    clean_text: bool = True
) -> DataPreprocessor:
    """
    Factory function para crear preprocesador de datos.
    """
    config = PreprocessingConfig(
        max_length=max_length,
        tokenizer_path=tokenizer_path,
        clean_text=clean_text
    )

    return DataPreprocessor(config)


def preprocess_real_dataset(
    dataset: Dataset,
    max_length: int = 512,
    tokenizer_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> Dataset:
    """
    Función de conveniencia para preprocesar dataset real.
    """
    preprocessor = create_data_preprocessor(
        max_length=max_length,
        tokenizer_path=tokenizer_path
    )

    processed_dataset = preprocessor.preprocess_dataset(dataset)

    if output_path:
        processed_dataset.save_to_disk(output_path)
        logger.info(f"💾 Dataset preprocesado guardado en {output_path}")

    return processed_dataset