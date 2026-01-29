#!/usr/bin/env python3
"""
EmpoorioTokenizer - Independent tokenizer for EmpoorioLM
Completely original implementation with our own copyright.
Optimized for code, Spanish, English, and special tokens.
"""

import json
import os
import regex as re
from typing import List, Dict, Tuple, Optional, Union, Any
from dataclasses import dataclass
from pathlib import Path
import logging
from collections import defaultdict

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    TORCH_AVAILABLE = False

from ...utils.logging import AiloosLogger


@dataclass
class EmpoorioTokenizerConfig:
    """Configuration for EmpoorioTokenizer."""

    vocab_size: int = 32000
    min_frequency: int = 2
    special_tokens: Dict[str, int] = None
    unk_token: str = "<unk>"
    bos_token: str = "<s>"
    eos_token: str = "</s>"
    pad_token: str = "<pad>"
    mask_token: str = "<mask>"

    # Special tokens for multimodal and memory
    image_token: str = "<image>"
    memory_token: str = "<memory>"
    tool_token: str = "<tool>"

    # Language-specific optimizations
    enable_spanish_optimization: bool = True
    enable_code_optimization: bool = True

    def __post_init__(self):
        if self.special_tokens is None:
            self.special_tokens = {
                self.unk_token: 0,
                self.bos_token: 1,
                self.eos_token: 2,
                self.pad_token: 3,
                self.mask_token: 4,
                self.image_token: 5,
                self.memory_token: 6,
                self.tool_token: 7,
            }


class EmpoorioBPETokenizer:
    """
    Byte-Pair Encoding tokenizer optimized for EmpoorioLM.
    Independent implementation with our own copyright.
    """

    def __init__(self, config: EmpoorioTokenizerConfig):
        self.config = config
        self.logger = AiloosLogger(__name__)

        # Core BPE components
        self.vocab: Dict[str, int] = {}
        self.inverse_vocab: Dict[int, str] = {}
        self.merges: Dict[Tuple[str, str], int] = {}

        # Regex patterns for tokenization
        self.pat = self._compile_patterns()

        # Special token handling
        self.special_tokens = config.special_tokens
        self.special_token_ids = {v: k for k, v in self.special_tokens.items()}
        self.unk_token_id = self.special_tokens[self.config.unk_token]
        self.bos_token_id = self.special_tokens[self.config.bos_token]
        self.eos_token_id = self.special_tokens[self.config.eos_token]
        self.pad_token_id = self.special_tokens[self.config.pad_token]

        self.unk_token = self.config.unk_token
        self.bos_token = self.config.bos_token
        self.eos_token = self.config.eos_token
        self.pad_token = self.config.pad_token

        # Initialize base vocabulary
        self._initialize_base_vocab()

        # Cache for performance
        self.encode_cache = {}
        self.decode_cache = {}

        self.logger.info("🪙 EmpoorioTokenizer initialized")

    def _compile_patterns(self) -> re.Pattern:
        """Compile regex patterns for efficient tokenization."""
        # Base pattern for general text
        base_pattern = r"""(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?+\p{L}+|\p{N}{1,3}| ?[^\s\p{L}\p{N}]++[\r\n]*|\s*[\r\n]|\s+(?!\S)|\s+"""

        # Enhanced pattern for code and special characters
        if self.config.enable_code_optimization:
            # Add patterns for common programming tokens
            code_patterns = [
                r'\b(?:def|class|if|else|for|while|try|except|import|from|return|yield)\b',  # Keywords
                r'[a-zA-Z_][a-zA-Z0-9_]*',  # Identifiers
                r'\d+(?:\.\d+)?(?:[eE][+-]?\d+)?',  # Numbers
                r'[+\-*/%=<>!&|^~]+',  # Operators
                r'[(){}[\]]',  # Brackets
                r'[.,;:]',  # Punctuation
                r'["\'`]',  # Quotes
            ]
            code_pattern = '|'.join(f'(?:{p})' for p in code_patterns)
            base_pattern = f'{code_pattern}|{base_pattern}'

        # Spanish-specific optimizations
        if self.config.enable_spanish_optimization:
            # Common Spanish contractions and patterns
            spanish_patterns = [
                r'\b(?:el|la|los|las|un|una|unos|unas|de|del|y|o|que|en|con|por|para|como|si|no|es|son|está|están)\b',
                r'ñ',  # ñ character
                r'¿|¡',  # Spanish punctuation
            ]
            spanish_pattern = '|'.join(spanish_patterns)
            base_pattern = f'{spanish_pattern}|{base_pattern}'

        return re.compile(base_pattern, re.UNICODE | re.MULTILINE)

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text before tokenization."""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text.strip())

        # Handle special characters
        if self.config.enable_code_optimization:
            # Preserve common programming patterns
            text = re.sub(r'(\w+)\s*(\+|\-|\*|\/|\=|\<|\>|\!|\&|\||\^|\~)\s*(\w+)', r'\1 \2 \3', text)

        return text

    def train(self, texts: List[str], vocab_size: Optional[int] = None) -> None:
        """
        Train the tokenizer on a corpus of texts.

        Args:
            texts: List of training texts
            vocab_size: Target vocabulary size (overrides config)
        """
        if vocab_size is None:
            vocab_size = self.config.vocab_size

        self.logger.info(f"🎯 Training tokenizer on {len(texts)} texts, target vocab size: {vocab_size}")

        # Step 1: Preprocess and get word frequencies
        word_freqs = self._get_word_frequencies(texts)

        # Step 2: Initialize vocabulary with characters
        self._initialize_base_vocab_from_freqs(word_freqs)

        # Step 3: Perform BPE merges
        self._perform_bpe_merges(word_freqs, vocab_size)

        # Step 4: Build final vocabularies
        self._build_vocabularies()

        # Ensure we reach the configured vocab size even with small corpora
        if len(self.vocab) < vocab_size:
            self._pad_vocab(vocab_size)

        self.logger.info(f"✅ Tokenizer trained. Final vocab size: {len(self.vocab)}")

    def _get_word_frequencies(self, texts: List[str]) -> Dict[str, int]:
        """Get word frequencies from training texts."""
        word_freqs = defaultdict(int)

        for text in texts:
            # Preprocess text
            text = self._preprocess_text(text)

            # Split into words using regex
            words = self.pat.findall(text)

            for word in words:
                # Skip empty tokens
                if not word.strip():
                    continue

                # Convert to bytes for BPE
                word_bytes = word.encode('utf-8')
                word_freqs[word_bytes] += 1

        return word_freqs

    def _initialize_base_vocab(self) -> None:
        """Initialize base vocabulary with byte-level tokens."""
        # Create base vocabulary (bytes 0-255)
        self.vocab.clear()
        self.inverse_vocab.clear()

        # Add special tokens first
        for token, token_id in self.special_tokens.items():
            token_bytes = token.encode('utf-8')
            self.vocab[token_bytes] = token_id
            self.inverse_vocab[token_id] = token_bytes

        # Add byte-level tokens
        for byte_val in range(256):
            byte_token = bytes([byte_val])
            if byte_token not in self.vocab:
                token_id = len(self.vocab)
                self.vocab[byte_token] = token_id
                self.inverse_vocab[token_id] = byte_token

    def _initialize_base_vocab_from_freqs(self, word_freqs: Dict[bytes, int]) -> None:
        """Initialize base vocabulary with byte-level tokens from word frequencies."""
        # Get all unique bytes
        all_bytes = set()
        for word in word_freqs.keys():
            all_bytes.update(word)

        # Create base vocabulary (bytes 0-255)
        self.vocab.clear()
        self.inverse_vocab.clear()

        # Add special tokens first
        for token, token_id in self.special_tokens.items():
            token_bytes = token.encode('utf-8')
            self.vocab[token_bytes] = token_id
            self.inverse_vocab[token_id] = token_bytes

        # Add byte-level tokens
        for byte_val in range(256):
            byte_token = bytes([byte_val])
            if byte_token not in self.vocab:
                token_id = len(self.vocab)
                self.vocab[byte_token] = token_id
                self.inverse_vocab[token_id] = byte_token

    def _perform_bpe_merges(self, word_freqs: Dict[bytes, int], target_vocab_size: int) -> None:
        """Perform BPE merges to build vocabulary."""
        self.merges.clear()

        # Convert word frequencies to character-level splits
        splits = {}
        for word, freq in word_freqs.items():
            if freq < self.config.min_frequency:
                continue
            splits[word] = [bytes([b]) for b in word]

        merge_id = 0
        while len(self.vocab) < target_vocab_size:
            # Find most frequent pair
            pair_freqs = self._get_pair_frequencies(splits, word_freqs)

            if not pair_freqs:
                break

            # Get most frequent pair
            best_pair = max(pair_freqs.items(), key=lambda x: x[1])[0]

            # Merge the pair
            self._merge_pair(splits, best_pair)
            self.merges[best_pair] = merge_id
            merge_id += 1

            # Add merged token to vocabulary
            merged_token = best_pair[0] + best_pair[1]
            if merged_token not in self.vocab:
                token_id = len(self.vocab)
                self.vocab[merged_token] = token_id
                self.inverse_vocab[token_id] = merged_token

    def _get_pair_frequencies(self, splits: Dict[bytes, List[bytes]], word_freqs: Dict[bytes, int]) -> Dict[Tuple[bytes, bytes], int]:
        """Get frequencies of adjacent pairs in splits."""
        pair_freqs = defaultdict(int)

        for word, word_splits in splits.items():
            freq = word_freqs[word]
            for i in range(len(word_splits) - 1):
                pair = (word_splits[i], word_splits[i + 1])
                pair_freqs[pair] += freq

        return pair_freqs

    def _merge_pair(self, splits: Dict[bytes, List[bytes]], pair: Tuple[bytes, bytes]) -> None:
        """Merge a pair in all word splits."""
        first, second = pair

        for word, word_splits in splits.items():
            i = 0
            while i < len(word_splits) - 1:
                if word_splits[i] == first and word_splits[i + 1] == second:
                    # Merge the pair
                    word_splits[i] = first + second
                    del word_splits[i + 1]
                else:
                    i += 1

    def _build_vocabularies(self) -> None:
        """Build final vocabularies after training."""
        # Ensure all merges are in vocab
        for merge_pair, merge_id in self.merges.items():
            merged = merge_pair[0] + merge_pair[1]
            if merged not in self.vocab:
                token_id = len(self.vocab)
                self.vocab[merged] = token_id
                self.inverse_vocab[token_id] = merged

        self.logger.info(f"📚 Vocabulary built: {len(self.vocab)} tokens")

    def _pad_vocab(self, target_vocab_size: int) -> None:
        """Pad vocabulary with unused tokens to reach target size."""
        if len(self.vocab) >= target_vocab_size:
            return

        idx = 0
        while len(self.vocab) < target_vocab_size:
            token = f"<extra_token_{idx:06d}>".encode("utf-8")
            idx += 1
            if token in self.vocab:
                continue
            token_id = len(self.vocab)
            self.vocab[token] = token_id
            self.inverse_vocab[token_id] = token

        self.logger.warning(
            f"⚠️  Vocab padded to {target_vocab_size} tokens due to limited corpus coverage."
        )

    def encode(self, text: str, add_special_tokens: bool = True) -> List[int]:
        """
        Encode text to token IDs.

        Args:
            text: Input text
            add_special_tokens: Whether to add BOS/EOS tokens

        Returns:
            List of token IDs
        """
        # Check cache
        cache_key = (text, add_special_tokens)
        if cache_key in self.encode_cache:
            return self.encode_cache[cache_key]

        # Preprocess text
        text = self._preprocess_text(text)

        # Handle special tokens in text
        tokens = self._encode_text(text)

        # Add special tokens
        if add_special_tokens:
            bos_id = self.special_tokens[self.config.bos_token]
            eos_id = self.special_tokens[self.config.eos_token]
            tokens = [bos_id] + tokens + [eos_id]

        # Cache result
        self.encode_cache[cache_key] = tokens
        return tokens

    def _encode_text(self, text: str) -> List[int]:
        """Encode text using BPE."""
        tokens = []

        # Split text into words
        words = self.pat.findall(text)

        for word in words:
            if not word.strip():
                continue

            # Encode word using BPE
            word_tokens = self._encode_word(word.encode('utf-8'))
            tokens.extend(word_tokens)

        return tokens

    def _encode_word(self, word_bytes: bytes) -> List[int]:
        """Encode a word using BPE merges."""
        if word_bytes in self.vocab:
            return [self.vocab[word_bytes]]

        # Split into characters
        tokens = [bytes([b]) for b in word_bytes]

        # Apply merges
        while len(tokens) > 1:
            # Find best pair to merge
            pairs = [(tokens[i], tokens[i + 1]) for i in range(len(tokens) - 1)]
            pair_scores = [(pair, self.merges.get(pair, float('inf'))) for pair in pairs]

            if not pair_scores:
                break

            # Get pair with lowest merge ID (earliest merge)
            best_pair, best_score = min(pair_scores, key=lambda x: x[1])

            if best_score == float('inf'):
                break

            # Apply merge
            new_tokens = []
            i = 0
            while i < len(tokens):
                if i < len(tokens) - 1 and tokens[i] == best_pair[0] and tokens[i + 1] == best_pair[1]:
                    new_tokens.append(best_pair[0] + best_pair[1])
                    i += 2
                else:
                    new_tokens.append(tokens[i])
                    i += 1

            tokens = new_tokens

        # Convert to token IDs
        token_ids = []
        for token in tokens:
            if token in self.vocab:
                token_ids.append(self.vocab[token])
            else:
                # Fallback to UNK token
                token_ids.append(self.special_tokens[self.config.unk_token])

        return token_ids

    def decode(self, token_ids: List[int], skip_special_tokens: bool = True) -> str:
        """
        Decode token IDs to text.

        Args:
            token_ids: List of token IDs
            skip_special_tokens: Whether to skip special tokens

        Returns:
            Decoded text
        """
        if hasattr(token_ids, "tolist"):
            token_ids = token_ids.tolist()
        if isinstance(token_ids, int):
            token_ids = [token_ids]

        # Check cache
        cache_key = tuple(token_ids), skip_special_tokens
        if cache_key in self.decode_cache:
            return self.decode_cache[cache_key]

        byte_chunks: List[bytes] = []
        for token_id in token_ids:
            if skip_special_tokens and token_id in self.special_token_ids:
                continue

            token_bytes = self.inverse_vocab.get(token_id)
            if token_bytes is None:
                byte_chunks.append(self.config.unk_token.encode("utf-8"))
                continue

            if isinstance(token_bytes, str):
                token_bytes = token_bytes.encode("utf-8")

            if skip_special_tokens and token_bytes.startswith(b"<extra_token_"):
                continue

            byte_chunks.append(token_bytes)

        # Decode the full byte stream to preserve multibyte chars across tokens.
        try:
            text = b"".join(byte_chunks).decode("utf-8")
        except UnicodeDecodeError:
            text = b"".join(byte_chunks).decode("utf-8", errors="replace")

        # Cache result
        self.decode_cache[cache_key] = text
        return text

    def __call__(self,
                 text: Union[str, List[str]],
                 return_tensors: Optional[str] = None,
                 padding: bool = False,
                 truncation: bool = False,
                 max_length: Optional[int] = None) -> Dict[str, Any]:
        """Compatibility wrapper for HuggingFace-style tokenizer calls."""
        if isinstance(text, str):
            texts = [text]
        else:
            texts = text

        all_input_ids: List[List[int]] = []
        max_len = 0
        for t in texts:
            ids = self.encode(t, add_special_tokens=True)
            if truncation and max_length and len(ids) > max_length:
                ids = ids[:max_length]
            all_input_ids.append(ids)
            max_len = max(max_len, len(ids))

        if padding:
            for ids in all_input_ids:
                while len(ids) < max_len:
                    ids.append(self.pad_token_id)

        attention_mask = []
        for ids in all_input_ids:
            attention_mask.append([1 if tid != self.pad_token_id else 0 for tid in ids])

        result: Dict[str, Any] = {"input_ids": all_input_ids, "attention_mask": attention_mask}
        if return_tensors == "pt":
            if not TORCH_AVAILABLE:
                raise ImportError("PyTorch no está disponible. Instale torch para usar return_tensors='pt'")
            result["input_ids"] = torch.tensor(result["input_ids"])
            result["attention_mask"] = torch.tensor(result["attention_mask"])

        return result

    def save(self, path: Union[str, Path]) -> None:
        """Save tokenizer to disk."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        # Save config
        config_path = path / "tokenizer_config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump({
                'vocab_size': self.config.vocab_size,
                'min_frequency': self.config.min_frequency,
                'special_tokens': self.special_tokens,
                'unk_token': self.config.unk_token,
                'bos_token': self.config.bos_token,
                'eos_token': self.config.eos_token,
                'pad_token': self.config.pad_token,
                'mask_token': self.config.mask_token,
                'image_token': self.config.image_token,
                'memory_token': self.config.memory_token,
                'tool_token': self.config.tool_token,
                'enable_spanish_optimization': self.config.enable_spanish_optimization,
                'enable_code_optimization': self.config.enable_code_optimization,
            }, f, indent=2, ensure_ascii=False)

        # Save vocab
        vocab_path = path / "vocab.json"
        # Convert bytes keys to strings for JSON serialization
        vocab_str_keys = {k.hex(): v for k, v in self.vocab.items()}
        with open(vocab_path, 'w', encoding='utf-8') as f:
            json.dump(vocab_str_keys, f, indent=2, ensure_ascii=False)

        # Save merges
        merges_path = path / "merges.json"
        merges_str_keys = {f"{k[0].hex()},{k[1].hex()}": v for k, v in self.merges.items()}
        with open(merges_path, 'w', encoding='utf-8') as f:
            json.dump(merges_str_keys, f, indent=2, ensure_ascii=False)

        self.logger.info(f"💾 Tokenizer saved to {path}")

    @classmethod
    def load(cls, path: Union[str, Path]) -> 'EmpoorioBPETokenizer':
        """Load tokenizer from disk."""
        path = Path(path)

        # Load config
        config_path = path / "tokenizer_config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        config = EmpoorioTokenizerConfig(**config_data)

        # Create tokenizer
        tokenizer = cls(config)

        # Load vocab
        vocab_path = path / "vocab.json"
        with open(vocab_path, 'r', encoding='utf-8') as f:
            vocab_str_keys = json.load(f)
            tokenizer.vocab = {bytes.fromhex(k): v for k, v in vocab_str_keys.items()}

        # Rebuild inverse vocab
        tokenizer.inverse_vocab = {v: k for k, v in tokenizer.vocab.items()}

        # Load merges
        merges_path = path / "merges.json"
        with open(merges_path, 'r', encoding='utf-8') as f:
            merges_str_keys = json.load(f)
            tokenizer.merges = {tuple(bytes.fromhex(k.split(',')[i]) for i in range(2)): v
                              for k, v in merges_str_keys.items()}

        return tokenizer

    def get_vocab_size(self) -> int:
        """Get vocabulary size."""
        return len(self.vocab)

    def get_special_tokens(self) -> Dict[str, int]:
        """Get special tokens mapping."""
        return self.special_tokens.copy()


# Factory functions
def create_empoorio_tokenizer(vocab_size: int = 32000, min_frequency: int = 2) -> EmpoorioBPETokenizer:
    """Create EmpoorioTokenizer with default config."""
    config = EmpoorioTokenizerConfig(vocab_size=vocab_size, min_frequency=min_frequency)
    return EmpoorioBPETokenizer(config)


def train_empoorio_tokenizer(
    texts: List[str],
    vocab_size: int = 32000,
    min_frequency: int = 2,
    save_path: Optional[Union[str, Path]] = None
) -> EmpoorioBPETokenizer:
    """Train and optionally save a new EmpoorioTokenizer."""
    tokenizer = create_empoorio_tokenizer(vocab_size=vocab_size, min_frequency=min_frequency)
    tokenizer.train(texts)

    if save_path:
        tokenizer.save(save_path)

    return tokenizer
