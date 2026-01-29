#!/usr/bin/env python3
"""
EmpoorioDataLoader - High-performance multimodal data pipeline
Streaming data loader for training EmpoorioLM with text and vision data.
"""

import torch
from torch.utils.data import Dataset, DataLoader, DistributedSampler
from typing import List, Dict, Any, Optional, Union, Iterator, Tuple
from dataclasses import dataclass
import json
import os
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor
import mmap
import pickle
import hashlib
from PIL import Image
import io
import base64
# import webdataset as wds  # Optional dependency
# from braceexpand import braceexpand  # Optional dependency
# import fsspec  # Optional dependency
import numpy as np

from ..utils.logging import AiloosLogger
from ..models.empoorio_lm import EmpoorioBPETokenizer, EmpoorioImageProcessor


@dataclass
class DataLoaderConfig:
    """Configuration for the data loader."""

    # Data sources
    text_data_paths: List[str] = None
    image_data_paths: List[str] = None
    multimodal_data_paths: List[str] = None

    # Processing
    max_seq_length: int = 4096
    batch_size: int = 8
    num_workers: int = 4
    prefetch_factor: int = 2

    # Multimodal
    image_size: int = 224
    max_images_per_sample: int = 1

    # Distributed training
    world_size: int = 1
    rank: int = 0

    # Caching
    cache_dir: Optional[str] = None
    use_cache: bool = True

    # Streaming
    streaming: bool = True
    buffer_size: int = 10000

    def __post_init__(self):
        if self.text_data_paths is None:
            self.text_data_paths = []
        if self.image_data_paths is None:
            self.image_data_paths = []
        if self.multimodal_data_paths is None:
            self.multimodal_data_paths = []


class EmpoorioTextDataset(Dataset):
    """Dataset for text-only training data."""

    def __init__(
        self,
        data_paths: List[str],
        tokenizer: EmpoorioBPETokenizer,
        max_seq_length: int = 4096,
        streaming: bool = True
    ):
        self.data_paths = data_paths
        self.tokenizer = tokenizer
        self.max_seq_length = max_seq_length
        self.streaming = streaming

        # Build index for non-streaming mode
        if not streaming:
            self.samples = self._build_index()
        else:
            self.samples = None

        self.logger = AiloosLogger(__name__)

    def _build_index(self) -> List[Dict[str, Any]]:
        """Build index of all samples."""
        samples = []

        for path in self.data_paths:
            if path.endswith('.jsonl'):
                samples.extend(self._index_jsonl(path))
            elif path.endswith('.txt'):
                samples.extend(self._index_text_file(path))
            elif path.endswith('.tar'):
                samples.extend(self._index_webdataset(path))

        return samples

    def _index_jsonl(self, path: str) -> List[Dict[str, Any]]:
        """Index JSONL file."""
        samples = []
        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f):
                try:
                    data = json.loads(line.strip())
                    samples.append({
                        'path': path,
                        'offset': line_num,
                        'text': data.get('text', ''),
                        'metadata': data.get('metadata', {})
                    })
                except json.JSONDecodeError:
                    continue
        return samples

    def _index_text_file(self, path: str) -> List[Dict[str, Any]]:
        """Index plain text file."""
        samples = []
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split into chunks
        chunks = self._split_text_into_chunks(content)
        for i, chunk in enumerate(chunks):
            samples.append({
                'path': path,
                'chunk_id': i,
                'text': chunk,
                'metadata': {}
            })

        return samples

    def _index_webdataset(self, path: str) -> List[Dict[str, Any]]:
        """Index WebDataset tar file."""
        # For WebDataset, we'll handle this in __getitem__
        return [{'path': path, 'streaming': True}]

    def _split_text_into_chunks(self, text: str, chunk_size: int = 4000) -> List[str]:
        """Split text into chunks of approximately chunk_size tokens."""
        words = text.split()
        chunks = []

        current_chunk = []
        current_length = 0

        for word in words:
            word_tokens = len(self.tokenizer.encode(word, add_special_tokens=False))
            if current_length + word_tokens > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_tokens
            else:
                current_chunk.append(word)
                current_length += word_tokens

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def __len__(self) -> int:
        if self.streaming:
            # Estimate length for streaming
            return sum(self._estimate_file_length(path) for path in self.data_paths)
        else:
            return len(self.samples)

    def _estimate_file_length(self, path: str) -> int:
        """Estimate number of samples in a file."""
        if path.endswith('.jsonl'):
            with open(path, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        elif path.endswith('.txt'):
            # Rough estimate
            file_size = os.path.getsize(path)
            return max(1, file_size // (1000 * self.max_seq_length // 4))  # Rough token estimate
        else:
            return 1000  # Default estimate

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        if self.streaming:
            return self._get_streaming_item(idx)
        else:
            return self._get_indexed_item(idx)

    def _get_indexed_item(self, idx: int) -> Dict[str, Any]:
        """Get item from pre-built index."""
        sample = self.samples[idx]

        # Tokenize text
        text = sample['text']
        tokens = self.tokenizer.encode(text, add_special_tokens=True)

        # Truncate if too long
        if len(tokens) > self.max_seq_length:
            tokens = tokens[:self.max_seq_length]

        # Pad if needed
        if len(tokens) < self.max_seq_length:
            pad_id = self.tokenizer.special_tokens[self.tokenizer.config.pad_token]
            tokens.extend([pad_id] * (self.max_seq_length - len(tokens)))

        return {
            'input_ids': torch.tensor(tokens, dtype=torch.long),
            'attention_mask': torch.tensor([1 if t != pad_id else 0 for t in tokens], dtype=torch.long),
            'labels': torch.tensor(tokens, dtype=torch.long),  # For causal LM
            'metadata': sample.get('metadata', {})
        }

    def _get_streaming_item(self, idx: int) -> Dict[str, Any]:
        """Get item in streaming mode."""
        # Cycle through data sources
        file_idx = idx % len(self.data_paths)
        path = self.data_paths[file_idx]

        if path.endswith('.jsonl'):
            return self._stream_jsonl_sample(path, idx // len(self.data_paths))
        elif path.endswith('.txt'):
            return self._stream_text_sample(path, idx // len(self.data_paths))
        else:
            # Fallback
            return self._get_empty_sample()

    def _stream_jsonl_sample(self, path: str, sample_idx: int) -> Dict[str, Any]:
        """Stream a sample from JSONL file."""
        with open(path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i == sample_idx % self._estimate_file_length(path):
                    try:
                        data = json.loads(line.strip())
                        text = data.get('text', '')
                        return self._process_text_sample(text, data.get('metadata', {}))
                    except json.JSONDecodeError:
                        break
        return self._get_empty_sample()

    def _stream_text_sample(self, path: str, sample_idx: int) -> Dict[str, Any]:
        """Stream a sample from text file."""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        chunks = self._split_text_into_chunks(content)
        if chunks:
            chunk = chunks[sample_idx % len(chunks)]
            return self._process_text_sample(chunk, {})
        return self._get_empty_sample()

    def _process_text_sample(self, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process a text sample into tensors."""
        tokens = self.tokenizer.encode(text, add_special_tokens=True)

        # Truncate
        if len(tokens) > self.max_seq_length:
            tokens = tokens[:self.max_seq_length]

        # Pad
        pad_id = self.tokenizer.special_tokens[self.tokenizer.config.pad_token]
        attention_mask = [1] * len(tokens)

        if len(tokens) < self.max_seq_length:
            tokens.extend([pad_id] * (self.max_seq_length - len(tokens)))
            attention_mask.extend([0] * (self.max_seq_length - len(attention_mask)))

        return {
            'input_ids': torch.tensor(tokens, dtype=torch.long),
            'attention_mask': torch.tensor(attention_mask, dtype=torch.long),
            'labels': torch.tensor(tokens, dtype=torch.long),
            'metadata': metadata
        }

    def _get_empty_sample(self) -> Dict[str, Any]:
        """Get empty sample for error cases."""
        pad_id = self.tokenizer.special_tokens[self.tokenizer.config.pad_token]
        return {
            'input_ids': torch.tensor([pad_id] * self.max_seq_length, dtype=torch.long),
            'attention_mask': torch.tensor([0] * self.max_seq_length, dtype=torch.long),
            'labels': torch.tensor([pad_id] * self.max_seq_length, dtype=torch.long),
            'metadata': {}
        }


class EmpoorioMultimodalDataset(Dataset):
    """Dataset for multimodal training data (text + images)."""

    def __init__(
        self,
        data_paths: List[str],
        tokenizer: EmpoorioBPETokenizer,
        image_processor: EmpoorioImageProcessor,
        max_seq_length: int = 4096,
        max_images_per_sample: int = 1,
        streaming: bool = True
    ):
        self.data_paths = data_paths
        self.tokenizer = tokenizer
        self.image_processor = image_processor
        self.max_seq_length = max_seq_length
        self.max_images_per_sample = max_images_per_sample
        self.streaming = streaming

        if not streaming:
            self.samples = self._build_index()
        else:
            self.samples = None

        self.logger = AiloosLogger(__name__)

    def _build_index(self) -> List[Dict[str, Any]]:
        """Build index for multimodal samples."""
        samples = []

        for path in self.data_paths:
            if path.endswith('.jsonl'):
                samples.extend(self._index_multimodal_jsonl(path))
            elif path.endswith('.tar'):
                samples.extend(self._index_webdataset(path))

        return samples

    def _index_multimodal_jsonl(self, path: str) -> List[Dict[str, Any]]:
        """Index multimodal JSONL file."""
        samples = []
        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f):
                try:
                    data = json.loads(line.strip())
                    samples.append({
                        'path': path,
                        'offset': line_num,
                        'text': data.get('text', ''),
                        'images': data.get('images', []),
                        'metadata': data.get('metadata', {})
                    })
                except json.JSONDecodeError:
                    continue
        return samples

    def _index_webdataset(self, path: str) -> List[Dict[str, Any]]:
        """Index WebDataset for multimodal data."""
        return [{'path': path, 'streaming': True}]

    def __len__(self) -> int:
        if self.streaming:
            return sum(self._estimate_file_length(path) for path in self.data_paths)
        else:
            return len(self.samples)

    def _estimate_file_length(self, path: str) -> int:
        """Estimate number of samples."""
        if path.endswith('.jsonl'):
            with open(path, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        return 1000

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        if self.streaming:
            return self._get_streaming_item(idx)
        else:
            return self._get_indexed_item(idx)

    def _get_indexed_item(self, idx: int) -> Dict[str, Any]:
        """Get indexed multimodal item."""
        sample = self.samples[idx]
        return self._process_multimodal_sample(
            sample['text'],
            sample['images'],
            sample.get('metadata', {})
        )

    def _get_streaming_item(self, idx: int) -> Dict[str, Any]:
        """Get streaming multimodal item."""
        file_idx = idx % len(self.data_paths)
        path = self.data_paths[file_idx]

        if path.endswith('.jsonl'):
            return self._stream_multimodal_jsonl(path, idx // len(self.data_paths))
        else:
            return self._get_empty_multimodal_sample()

    def _stream_multimodal_jsonl(self, path: str, sample_idx: int) -> Dict[str, Any]:
        """Stream multimodal sample from JSONL."""
        with open(path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i == sample_idx % self._estimate_file_length(path):
                    try:
                        data = json.loads(line.strip())
                        return self._process_multimodal_sample(
                            data.get('text', ''),
                            data.get('images', []),
                            data.get('metadata', {})
                        )
                    except json.JSONDecodeError:
                        break
        return self._get_empty_multimodal_sample()

    def _process_multimodal_sample(
        self,
        text: str,
        images: List[Union[str, Dict]],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a multimodal sample."""
        # Process images
        processed_images = []
        image_positions = []

        for i, img_data in enumerate(images[:self.max_images_per_sample]):
            try:
                if isinstance(img_data, str):
                    # Base64 encoded image
                    img_bytes = base64.b64decode(img_data)
                    image = Image.open(io.BytesIO(img_bytes))
                elif isinstance(img_data, dict) and 'path' in img_data:
                    # Image path
                    image = Image.open(img_data['path'])
                else:
                    continue

                # Process image
                pixel_values = self.image_processor.preprocess_image(image)
                processed_images.append(pixel_values)

                # Add image token to text
                image_token = self.tokenizer.config.image_token
                image_token_id = self.tokenizer.special_tokens[image_token]

                # Insert image token at position (simplified)
                text_parts = text.split()
                insert_pos = min(i * 50, len(text_parts))  # Rough positioning
                text_parts.insert(insert_pos, image_token)
                text = ' '.join(text_parts)

                image_positions.append((insert_pos, insert_pos + 1))

            except Exception as e:
                self.logger.warning(f"Failed to process image {i}: {e}")
                continue

        # Tokenize text
        tokens = self.tokenizer.encode(text, add_special_tokens=True)

        # Truncate
        if len(tokens) > self.max_seq_length:
            tokens = tokens[:self.max_seq_length]

        # Create attention mask
        pad_id = self.tokenizer.special_tokens[self.tokenizer.config.pad_token]
        attention_mask = [1 if t != pad_id else 0 for t in tokens]

        # Pad
        if len(tokens) < self.max_seq_length:
            tokens.extend([pad_id] * (self.max_seq_length - len(tokens)))
            attention_mask.extend([0] * (self.max_seq_length - len(attention_mask)))

        result = {
            'input_ids': torch.tensor(tokens, dtype=torch.long),
            'attention_mask': torch.tensor(attention_mask, dtype=torch.long),
            'labels': torch.tensor(tokens, dtype=torch.long),
            'metadata': metadata
        }

        # Add images if any
        if processed_images:
            # Stack images
            image_tensor = torch.stack(processed_images, dim=0)
            result['images'] = image_tensor
            result['image_positions'] = image_positions
            result['num_images'] = len(processed_images)

        return result

    def _get_empty_multimodal_sample(self) -> Dict[str, Any]:
        """Get empty multimodal sample."""
        pad_id = self.tokenizer.special_tokens[self.tokenizer.config.pad_token]
        return {
            'input_ids': torch.tensor([pad_id] * self.max_seq_length, dtype=torch.long),
            'attention_mask': torch.tensor([0] * self.max_seq_length, dtype=torch.long),
            'labels': torch.tensor([pad_id] * self.max_seq_length, dtype=torch.long),
            'metadata': {},
            'num_images': 0
        }


class EmpoorioDataLoader:
    """High-performance data loader for EmpoorioLM training."""

    def __init__(self, config: DataLoaderConfig):
        self.config = config
        self.logger = AiloosLogger(__name__)

        # Initialize components
        self.tokenizer = None
        self.image_processor = None
        self.text_dataset = None
        self.multimodal_dataset = None

    def setup_tokenizer(self, tokenizer: EmpoorioBPETokenizer):
        """Set up tokenizer."""
        self.tokenizer = tokenizer

    def setup_image_processor(self, image_processor: EmpoorioImageProcessor):
        """Set up image processor."""
        self.image_processor = image_processor

    def create_text_dataloader(self) -> DataLoader:
        """Create text-only data loader."""
        if not self.tokenizer:
            raise ValueError("Tokenizer not set up")

        dataset = EmpoorioTextDataset(
            data_paths=self.config.text_data_paths,
            tokenizer=self.tokenizer,
            max_seq_length=self.config.max_seq_length,
            streaming=self.config.streaming
        )

        sampler = DistributedSampler(
            dataset,
            num_replicas=self.config.world_size,
            rank=self.config.rank,
            shuffle=True
        ) if self.config.world_size > 1 else None

        dataloader = DataLoader(
            dataset,
            batch_size=self.config.batch_size,
            sampler=sampler,
            num_workers=self.config.num_workers,
            prefetch_factor=self.config.prefetch_factor,
            pin_memory=True,
            persistent_workers=True
        )

        return dataloader

    def create_multimodal_dataloader(self) -> DataLoader:
        """Create multimodal data loader."""
        if not self.tokenizer or not self.image_processor:
            raise ValueError("Tokenizer and image processor not set up")

        dataset = EmpoorioMultimodalDataset(
            data_paths=self.config.multimodal_data_paths,
            tokenizer=self.tokenizer,
            image_processor=self.image_processor,
            max_seq_length=self.config.max_seq_length,
            max_images_per_sample=self.config.max_images_per_sample,
            streaming=self.config.streaming
        )

        sampler = DistributedSampler(
            dataset,
            num_replicas=self.config.world_size,
            rank=self.config.rank,
            shuffle=True
        ) if self.config.world_size > 1 else None

        dataloader = DataLoader(
            dataset,
            batch_size=self.config.batch_size,
            sampler=sampler,
            num_workers=self.config.num_workers,
            prefetch_factor=self.config.prefetch_factor,
            pin_memory=True,
            persistent_workers=True,
            collate_fn=self._multimodal_collate_fn
        )

        return dataloader

    def _multimodal_collate_fn(self, batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Custom collate function for multimodal batches."""
        # Standard collate for text
        result = {
            'input_ids': torch.stack([item['input_ids'] for item in batch]),
            'attention_mask': torch.stack([item['attention_mask'] for item in batch]),
            'labels': torch.stack([item['labels'] for item in batch]),
        }

        # Handle images (variable number per sample)
        if any('images' in item for item in batch):
            # Find max number of images in batch
            max_images = max((item.get('num_images', 0) for item in batch), default=0)

            if max_images > 0:
                # Pad images to max_images
                image_tensors = []
                image_masks = []

                for item in batch:
                    num_images = item.get('num_images', 0)
                    if num_images > 0:
                        images = item['images']  # [num_images, C, H, W]
                        # Pad to max_images
                        if num_images < max_images:
                            # Create padding
                            pad_shape = (max_images - num_images, *images.shape[1:])
                            padding = torch.zeros(pad_shape, dtype=images.dtype)
                            images = torch.cat([images, padding], dim=0)

                        image_tensors.append(images)

                        # Create mask
                        mask = torch.ones(max_images, dtype=torch.bool)
                        mask[num_images:] = False
                        image_masks.append(mask)
                    else:
                        # No images - create zero tensor
                        pad_shape = (max_images, 3, self.config.image_size, self.config.image_size)
                        padding = torch.zeros(pad_shape, dtype=torch.float32)
                        image_tensors.append(padding)
                        image_masks.append(torch.zeros(max_images, dtype=torch.bool))

                result['images'] = torch.stack(image_tensors)
                result['image_masks'] = torch.stack(image_masks)
                result['max_images'] = max_images

        return result

    def create_combined_dataloader(self) -> DataLoader:
        """Create combined text + multimodal data loader."""
        # This would combine text and multimodal datasets
        # Implementation would depend on training strategy
        raise NotImplementedError("Combined dataloader not yet implemented")


# Utility functions
def create_data_loader_config(
    text_paths: List[str] = None,
    multimodal_paths: List[str] = None,
    batch_size: int = 8,
    max_seq_length: int = 4096,
    world_size: int = 1,
    rank: int = 0
) -> DataLoaderConfig:
    """Create data loader configuration."""
    return DataLoaderConfig(
        text_data_paths=text_paths or [],
        multimodal_data_paths=multimodal_paths or [],
        batch_size=batch_size,
        max_seq_length=max_seq_length,
        world_size=world_size,
        rank=rank
    )


def estimate_dataset_size(data_paths: List[str]) -> Dict[str, Any]:
    """Estimate total dataset size and statistics."""
    stats = {
        'total_files': len(data_paths),
        'estimated_samples': 0,
        'file_types': {}
    }

    for path in data_paths:
        if path.endswith('.jsonl'):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    count = sum(1 for _ in f)
                stats['estimated_samples'] += count
                stats['file_types']['jsonl'] = stats['file_types'].get('jsonl', 0) + 1
            except:
                pass
        elif path.endswith('.txt'):
            stats['file_types']['txt'] = stats['file_types'].get('txt', 0) + 1
            # Rough estimate
            stats['estimated_samples'] += 1000
        elif path.endswith('.tar'):
            stats['file_types']['tar'] = stats['file_types'].get('tar', 0) + 1
            stats['estimated_samples'] += 10000

    return stats