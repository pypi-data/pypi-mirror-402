"""
Message Processor - Procesamiento avanzado de mensajes
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
import base64

logger = logging.getLogger(__name__)


@dataclass
class ProcessedMessage:
    """Mensaje procesado con metadatos"""
    content: Any
    metadata: Dict[str, Any]
    message_id: str
    timestamp: float
    checksum: str
    size: int
    version: str = "1.0"


class MessageProcessor:
    """
    Procesamiento avanzado de mensajes.
    Incluye validación, transformación, encriptación y optimización.
    """

    def __init__(self):
        self._validators: List[Callable[[Any, Dict[str, Any]], bool]] = []
        self._transformers: List[Callable[[Any, Dict[str, Any]], Any]] = []
        self._compressors: Dict[str, Callable[[bytes], bytes]] = {}
        self._encryptors: Dict[str, Callable[[bytes, str], bytes]] = {}

    async def process(self, message: Any, metadata: Dict[str, Any]) -> ProcessedMessage:
        """
        Procesa un mensaje completo

        Args:
            message: Contenido del mensaje
            metadata: Metadatos adicionales

        Returns:
            ProcessedMessage con el mensaje procesado
        """
        # Generar ID único
        message_id = self._generate_message_id(message, metadata)

        # Timestamp
        timestamp = time.time()

        # Validar mensaje
        if not await self._validate_message(message, metadata):
            raise ValueError("Mensaje no pasó validación")

        # Transformar mensaje
        transformed_message = await self._transform_message(message, metadata)

        # Serializar para checksum y tamaño
        serialized = self._serialize_message(transformed_message)
        checksum = self._calculate_checksum(serialized)
        size = len(serialized)

        # Actualizar metadatos
        enriched_metadata = metadata.copy()
        enriched_metadata.update({
            "processed_at": timestamp,
            "message_id": message_id,
            "original_size": size,
            "checksum": checksum
        })

        return ProcessedMessage(
            content=transformed_message,
            metadata=enriched_metadata,
            message_id=message_id,
            timestamp=timestamp,
            checksum=checksum,
            size=size
        )

    async def validate_batch(self, messages: List[Dict[str, Any]]) -> List[bool]:
        """
        Valida un lote de mensajes

        Args:
            messages: Lista de mensajes con metadata

        Returns:
            Lista de resultados de validación
        """
        tasks = []
        for msg_data in messages:
            message = msg_data.get("message")
            metadata = msg_data.get("metadata", {})
            tasks.append(self._validate_message(message, metadata))

        return await asyncio.gather(*tasks)

    async def _validate_message(self, message: Any, metadata: Dict[str, Any]) -> bool:
        """
        Valida un mensaje usando todos los validadores registrados

        Args:
            message: Contenido del mensaje
            metadata: Metadatos

        Returns:
            True si pasa todas las validaciones
        """
        for validator in self._validators:
            try:
                if not await validator(message, metadata):
                    logger.warning("Mensaje falló validación")
                    return False
            except Exception as e:
                logger.error(f"Error en validador: {e}")
                return False

        return True

    async def _transform_message(self, message: Any, metadata: Dict[str, Any]) -> Any:
        """
        Aplica todas las transformaciones registradas

        Args:
            message: Contenido del mensaje
            metadata: Metadatos

        Returns:
            Mensaje transformado
        """
        transformed = message

        for transformer in self._transformers:
            try:
                transformed = await transformer(transformed, metadata)
            except Exception as e:
                logger.error(f"Error en transformador: {e}")
                raise

        return transformed

    def _serialize_message(self, message: Any) -> bytes:
        """Serializa un mensaje a bytes para checksum"""
        if isinstance(message, (dict, list)):
            return json.dumps(message, sort_keys=True).encode('utf-8')
        elif isinstance(message, str):
            return message.encode('utf-8')
        elif isinstance(message, bytes):
            return message
        else:
            return str(message).encode('utf-8')

    def _calculate_checksum(self, data: bytes) -> str:
        """Calcula checksum SHA256 del mensaje"""
        return hashlib.sha256(data).hexdigest()

    def _generate_message_id(self, message: Any, metadata: Dict[str, Any]) -> str:
        """Genera ID único para el mensaje"""
        content_hash = self._calculate_checksum(self._serialize_message(message))
        timestamp = str(time.time())
        metadata_str = json.dumps(metadata, sort_keys=True)

        combined = f"{content_hash}:{timestamp}:{metadata_str}"
        return hashlib.md5(combined.encode('utf-8')).hexdigest()

    def add_validator(self, validator: Callable[[Any, Dict[str, Any]], bool]) -> None:
        """
        Agrega un validador personalizado

        Args:
            validator: Función que recibe (message, metadata) y retorna bool
        """
        self._validators.append(validator)

    def add_transformer(self, transformer: Callable[[Any, Dict[str, Any]], Any]) -> None:
        """
        Agrega un transformador personalizado

        Args:
            transformer: Función que recibe (message, metadata) y retorna mensaje transformado
        """
        self._transformers.append(transformer)

    def add_compressor(self, name: str, compressor: Callable[[bytes], bytes]) -> None:
        """
        Agrega un compresor personalizado

        Args:
            name: Nombre del compresor
            compressor: Función que recibe bytes y retorna bytes comprimidos
        """
        self._compressors[name] = compressor

    def add_encryptor(self, name: str, encryptor: Callable[[bytes, str], bytes]) -> None:
        """
        Agrega un encriptador personalizado

        Args:
            name: Nombre del encriptador
            encryptor: Función que recibe (bytes, key) y retorna bytes encriptados
        """
        self._encryptors[name] = encryptor

    async def compress_message(self, message: ProcessedMessage, compressor_name: str) -> ProcessedMessage:
        """
        Comprime el contenido de un mensaje procesado

        Args:
            message: Mensaje procesado
            compressor_name: Nombre del compresor

        Returns:
            Mensaje con contenido comprimido
        """
        if compressor_name not in self._compressors:
            raise ValueError(f"Compresor '{compressor_name}' no registrado")

        serialized = self._serialize_message(message.content)
        compressed = self._compressors[compressor_name](serialized)

        # Actualizar metadatos
        new_metadata = message.metadata.copy()
        new_metadata["compressed"] = True
        new_metadata["compressor"] = compressor_name
        new_metadata["original_size"] = message.size
        new_metadata["compressed_size"] = len(compressed)

        return ProcessedMessage(
            content=base64.b64encode(compressed).decode('utf-8'),  # Base64 para JSON
            metadata=new_metadata,
            message_id=message.message_id,
            timestamp=message.timestamp,
            checksum=message.checksum,
            size=len(compressed)
        )

    async def encrypt_message(self, message: ProcessedMessage, encryptor_name: str, key: str) -> ProcessedMessage:
        """
        Encripta el contenido de un mensaje procesado

        Args:
            message: Mensaje procesado
            encryptor_name: Nombre del encriptador
            key: Clave de encriptación

        Returns:
            Mensaje con contenido encriptado
        """
        if encryptor_name not in self._encryptors:
            raise ValueError(f"Encriptador '{encryptor_name}' no registrado")

        serialized = self._serialize_message(message.content)
        encrypted = self._encryptors[encryptor_name](serialized, key)

        # Actualizar metadatos
        new_metadata = message.metadata.copy()
        new_metadata["encrypted"] = True
        new_metadata["encryptor"] = encryptor_name

        return ProcessedMessage(
            content=base64.b64encode(encrypted).decode('utf-8'),  # Base64 para JSON
            metadata=new_metadata,
            message_id=message.message_id,
            timestamp=message.timestamp,
            checksum=message.checksum,
            size=len(encrypted)
        )

    def get_stats(self) -> Dict[str, int]:
        """Obtiene estadísticas del procesador"""
        return {
            "validators_count": len(self._validators),
            "transformers_count": len(self._transformers),
            "compressors_count": len(self._compressors),
            "encryptors_count": len(self._encryptors)
        }