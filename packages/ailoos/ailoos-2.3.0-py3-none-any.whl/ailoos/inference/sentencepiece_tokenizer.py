"""
SentencePiece Tokenizer Wrapper
Wrapper para hacer compatible SentencePiece con la interfaz de HuggingFace transformers.
"""

from typing import Dict, List, Any, Optional, Union
import logging

try:
    import sentencepiece as spm
except ImportError:
    raise ImportError("SentencePiece no está instalado. Instale con: pip install sentencepiece")

# Import torch opcionalmente
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    torch = None
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)


class SentencePieceTokenizerWrapper:
    """
    Wrapper para SentencePiece que emula la interfaz de AutoTokenizer de HuggingFace.
    """

    def __init__(self, model_path: str):
        """
        Inicializar wrapper con modelo SentencePiece.

        Args:
            model_path: Ruta al archivo .model de SentencePiece
        """
        self.sp = spm.SentencePieceProcessor()
        self.sp.load(model_path)

        # Configurar IDs de tokens especiales
        self.unk_token_id = self.sp.unk_id()
        self.bos_token_id = self.sp.bos_id()
        self.eos_token_id = self.sp.eos_id()
        self.pad_token_id = self.sp.pad_id() if self.sp.pad_id() != -1 else self.eos_token_id

        # Configurar strings de tokens especiales
        self.unk_token = self.sp.id_to_piece(self.unk_token_id)
        self.bos_token = self.sp.id_to_piece(self.bos_token_id) if self.bos_token_id != -1 else None
        self.eos_token = self.sp.id_to_piece(self.eos_token_id) if self.eos_token_id != -1 else None
        self.pad_token = self.sp.id_to_piece(self.pad_token_id) if self.pad_token_id != -1 else self.eos_token

        # Propiedades adicionales para compatibilidad
        self.vocab_size = self.sp.get_piece_size()

        logger.info(f"✅ SentencePiece tokenizer cargado: vocab_size={self.vocab_size}")

    def encode(self, text: str, add_special_tokens: bool = True) -> List[int]:
        """
        Codificar texto a IDs de tokens.

        Args:
            text: Texto a codificar
            add_special_tokens: Si añadir tokens especiales

        Returns:
            Lista de IDs de tokens
        """
        if add_special_tokens:
            return self.sp.encode_as_ids(text)
        else:
            # Codificar sin BOS/EOS si add_special_tokens=False
            ids = self.sp.encode_as_ids(text)
            # Remover BOS y EOS si están presentes
            if ids and ids[0] == self.bos_token_id:
                ids = ids[1:]
            if ids and ids[-1] == self.eos_token_id:
                ids = ids[:-1]
            return ids

    def decode(self, token_ids: Union[List[int], "torch.Tensor"], skip_special_tokens: bool = True) -> str:
        """
        Decodificar IDs de tokens a texto.

        Args:
            token_ids: IDs de tokens a decodificar
            skip_special_tokens: Si omitir tokens especiales

        Returns:
            Texto decodificado
        """
        if TORCH_AVAILABLE and isinstance(token_ids, torch.Tensor):
            token_ids = token_ids.tolist()

        if skip_special_tokens:
            # Filtrar tokens especiales
            filtered_ids = []
            for tid in token_ids:
                if tid not in [self.unk_token_id, self.bos_token_id, self.eos_token_id, self.pad_token_id]:
                    filtered_ids.append(tid)
            return self.sp.decode_ids(filtered_ids)
        else:
            return self.sp.decode_ids(token_ids)

    def __call__(self, text: Union[str, List[str]],
                  return_tensors: Optional[str] = None,
                  padding: bool = False,
                  truncation: bool = False,
                  max_length: Optional[int] = None) -> Dict[str, Any]:
        """
        Método de llamada para compatibilidad con HuggingFace.

        Args:
            text: Texto(s) a procesar
            return_tensors: Formato de tensores ('pt' para PyTorch)
            padding: Si hacer padding
            truncation: Si truncar
            max_length: Longitud máxima

        Returns:
            Diccionario con input_ids y attention_mask
        """
        if isinstance(text, str):
            texts = [text]
        else:
            texts = text

        # Procesar cada texto
        all_input_ids = []
        max_len = 0

        for t in texts:
            ids = self.encode(t, add_special_tokens=True)
            if truncation and max_length and len(ids) > max_length:
                ids = ids[:max_length]
            all_input_ids.append(ids)
            max_len = max(max_len, len(ids))

        # Aplicar padding si se solicita
        if padding:
            for ids in all_input_ids:
                while len(ids) < max_len:
                    ids.append(self.pad_token_id)

        result = {"input_ids": all_input_ids}

        # Crear attention_mask
        attention_mask = []
        for ids in all_input_ids:
            mask = [1 if tid != self.pad_token_id else 0 for tid in ids]
            attention_mask.append(mask)
        result["attention_mask"] = attention_mask

        # Convertir a tensores si se solicita
        if return_tensors == "pt":
            if not TORCH_AVAILABLE:
                raise ImportError("PyTorch no está disponible. Instale torch para usar return_tensors='pt'")
            result["input_ids"] = torch.tensor(result["input_ids"])
            result["attention_mask"] = torch.tensor(result["attention_mask"])

        return result

    def save_pretrained(self, save_directory: str):
        """
        Guardar tokenizer (simulado - SentencePiece ya está guardado).

        Args:
            save_directory: Directorio donde guardar
        """
        logger.info(f"Tokenizer SentencePiece ya guardado en: {self.sp.model_file}")

    @classmethod
    def from_pretrained(cls, model_path: str) -> 'SentencePieceTokenizerWrapper':
        """
        Cargar tokenizer desde archivo.

        Args:
            model_path: Ruta al modelo SentencePiece

        Returns:
            Instancia del tokenizer
        """
        return cls(model_path)


def create_ailoos_tokenizer(tokenizer_path: Optional[str] = None) -> SentencePieceTokenizerWrapper:
    """
    Crear tokenizer AILOOS fine-tuned.

    Args:
        tokenizer_path: Ruta al modelo del tokenizer (opcional, usa default si no se especifica)

    Returns:
        Tokenizer configurado
    """
    import os
    from pathlib import Path

    if tokenizer_path is None:
        # Ruta por defecto del tokenizer entrenado
        base_path = Path(__file__).parent.parent.parent.parent  # /Users/juliojavier/Desktop/Ailoos
        default_path = base_path / "test_tokenizer_output" / "ailoos_tokenizer.model"
        tokenizer_path = str(default_path)

    if not os.path.exists(tokenizer_path):
        raise FileNotFoundError(f"Tokenizer no encontrado en: {tokenizer_path}")

    logger.info(f"🔤 Cargando tokenizer AILOOS desde: {tokenizer_path}")
    return SentencePieceTokenizerWrapper(tokenizer_path)