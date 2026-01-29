"""
Servicio de Text-to-Speech (TTS) para AILOOS
=============================================

Este módulo proporciona funcionalidades para generar previews de audio de las voces disponibles,
incluyendo síntesis de texto a voz, gestión de archivos de audio temporales, y validación de voces.
Integra con APIs externas de TTS como OpenAI y ElevenLabs.

Funcionalidades principales:
- Validación de voces disponibles (Ember, Alloy, Echo)
- Generación de previews de audio usando OpenAI TTS API
- Gestión automática de archivos de audio temporales
- Manejo robusto de errores y logging
- Soporte para múltiples proveedores de TTS
"""

import logging
import os
import tempfile
import time
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import asyncio
from datetime import datetime, timedelta

import httpx
from pydantic import BaseModel, Field, validator

# Configurar logging
logger = logging.getLogger(__name__)


class TTSConfig(BaseModel):
    """Configuración para el servicio TTS."""

    openai_api_key: str = Field(..., description="Clave API de OpenAI")
    openai_base_url: str = Field(default="https://api.openai.com/v1", description="URL base de OpenAI API")
    elevenlabs_api_key: Optional[str] = Field(default=None, description="Clave API de ElevenLabs (opcional)")
    elevenlabs_base_url: str = Field(default="https://api.elevenlabs.io/v1", description="URL base de ElevenLabs API")

    # Configuración de audio
    temp_dir: str = Field(default="/tmp/ailoos_tts", description="Directorio para archivos temporales")
    max_file_age_hours: int = Field(default=24, description="Horas antes de limpiar archivos temporales")
    max_concurrent_requests: int = Field(default=5, description="Máximo de solicitudes concurrentes")

    # Configuración de voces
    available_voices: List[str] = Field(default=["ember", "alloy", "echo"], description="Voces disponibles")
    default_voice: str = Field(default="ember", description="Voz por defecto")
    preview_text: str = Field(
        default="Hola, esta es una muestra de mi voz. ¿Te gusta cómo sueno?",
        description="Texto de preview para generar audio"
    )

    @validator('available_voices')
    def validate_available_voices(cls, v):
        """Valida que las voces disponibles sean válidas."""
        valid_voices = ["ember", "alloy", "echo"]
        invalid_voices = [voice for voice in v if voice not in valid_voices]
        if invalid_voices:
            raise ValueError(f"Voces inválidas: {invalid_voices}. Voces válidas: {valid_voices}")
        return v

    @validator('default_voice')
    def validate_default_voice(cls, v):
        """Valida que la voz por defecto esté en las voces disponibles."""
        if v not in ["ember", "alloy", "echo"]:
            raise ValueError(f"Voz por defecto inválida: {v}. Debe ser: ember, alloy, o echo")
        return v


class TTSRequest(BaseModel):
    """Modelo para solicitud de TTS."""

    voice: str = Field(..., description="Voz a usar (ember, alloy, echo)")
    text: Optional[str] = Field(default=None, description="Texto a sintetizar (usa preview si no se especifica)")
    provider: str = Field(default="openai", description="Proveedor TTS (openai, elevenlabs)")

    @validator('voice')
    def validate_voice(cls, v):
        """Valida que la voz sea válida."""
        if v not in ["ember", "alloy", "echo"]:
            raise ValueError('La voz debe ser "ember", "alloy", o "echo"')
        return v

    @validator('provider')
    def validate_provider(cls, v):
        """Valida que el proveedor sea válido."""
        if v not in ["openai", "elevenlabs"]:
            raise ValueError('El proveedor debe ser "openai" o "elevenlabs"')
        return v


class TTSResponse(BaseModel):
    """Modelo para respuesta de TTS."""

    audio_file_path: str = Field(..., description="Ruta al archivo de audio generado")
    voice: str = Field(..., description="Voz usada")
    provider: str = Field(..., description="Proveedor usado")
    text_used: str = Field(..., description="Texto sintetizado")
    file_size_bytes: int = Field(..., description="Tamaño del archivo en bytes")
    duration_seconds: float = Field(..., description="Duración del audio en segundos")
    generated_at: datetime = Field(default_factory=datetime.now, description="Fecha de generación")


class TTSServiceError(Exception):
    """Excepción base para errores del servicio TTS."""
    pass


class VoiceValidationError(TTSServiceError):
    """Error de validación de voz."""
    pass


class TTSAPIError(TTSServiceError):
    """Error en la API de TTS."""
    pass


class AudioGenerationError(TTSServiceError):
    """Error en la generación de audio."""
    pass


class TTSService:
    """
    Servicio de Text-to-Speech para generar previews de voces.

    Proporciona funcionalidades para validar voces, generar audio usando APIs externas,
    y gestionar archivos temporales de manera eficiente.
    """

    def __init__(self, config: TTSConfig):
        """
        Inicializa el servicio TTS.

        Args:
            config: Configuración del servicio
        """
        self.config = config
        self._setup_temp_directory()
        self._semaphore = asyncio.Semaphore(config.max_concurrent_requests)

        # Cliente HTTP para OpenAI
        self.openai_client = httpx.AsyncClient(
            base_url=config.openai_base_url,
            headers={"Authorization": f"Bearer {config.openai_api_key}"},
            timeout=30.0
        )

        # Cliente HTTP para ElevenLabs (si está configurado)
        self.elevenlabs_client = None
        if config.elevenlabs_api_key:
            self.elevenlabs_client = httpx.AsyncClient(
                base_url=config.elevenlabs_base_url,
                headers={"xi-api-key": config.elevenlabs_api_key},
                timeout=30.0
            )

        logger.info("Servicio TTS inicializado")

    def _setup_temp_directory(self) -> None:
        """Configura el directorio temporal para archivos de audio."""
        temp_path = Path(self.config.temp_dir)
        temp_path.mkdir(parents=True, exist_ok=True)

        # Verificar permisos de escritura
        test_file = temp_path / ".test_write"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except Exception as e:
            raise TTSServiceError(f"No se puede escribir en el directorio temporal {temp_path}: {e}")

        logger.info(f"Directorio temporal configurado: {temp_path}")

    async def validate_voice(self, voice: str) -> bool:
        """
        Valida si una voz está disponible.

        Args:
            voice: Nombre de la voz a validar

        Returns:
            bool: True si la voz es válida

        Raises:
            VoiceValidationError: Si la voz no es válida
        """
        if voice not in self.config.available_voices:
            raise VoiceValidationError(
                f"Voz '{voice}' no disponible. Voces disponibles: {self.config.available_voices}"
            )
        return True

    async def get_available_voices(self) -> List[str]:
        """
        Obtiene la lista de voces disponibles.

        Returns:
            List[str]: Lista de voces disponibles
        """
        return self.config.available_voices.copy()

    async def generate_voice_preview(self, request: TTSRequest) -> TTSResponse:
        """
        Genera un preview de audio para una voz específica.

        Args:
            request: Solicitud de TTS con voz y parámetros

        Returns:
            TTSResponse: Respuesta con información del audio generado

        Raises:
            VoiceValidationError: Si la voz no es válida
            TTSAPIError: Si hay error en la API
            AudioGenerationError: Si hay error en la generación
        """
        async with self._semaphore:
            # Validar voz
            await self.validate_voice(request.voice)

            # Determinar texto a usar
            text = request.text if request.text else self.config.preview_text

            # Generar audio según proveedor
            if request.provider == "openai":
                return await self._generate_openai_preview(request.voice, text)
            elif request.provider == "elevenlabs":
                return await self._generate_elevenlabs_preview(request.voice, text)
            else:
                raise TTSAPIError(f"Proveedor no soportado: {request.provider}")

    async def _generate_openai_preview(self, voice: str, text: str) -> TTSResponse:
        """
        Genera preview usando OpenAI TTS API.

        Args:
            voice: Voz a usar
            text: Texto a sintetizar

        Returns:
            TTSResponse: Respuesta con audio generado
        """
        try:
            # Mapear voces de AILOOS a voces de OpenAI
            openai_voice_map = {
                "ember": "nova",  # Voz similar a ember
                "alloy": "alloy",
                "echo": "echo"
            }

            openai_voice = openai_voice_map.get(voice, "alloy")

            # Preparar solicitud
            payload = {
                "model": "tts-1",
                "input": text,
                "voice": openai_voice,
                "response_format": "mp3",
                "speed": 1.0
            }

            # Hacer solicitud a OpenAI
            response = await self.openai_client.post("/audio/speech", json=payload)

            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Error en OpenAI API: {response.status_code} - {error_detail}")
                raise TTSAPIError(f"Error en OpenAI API: {response.status_code}")

            # Generar nombre de archivo único
            timestamp = int(time.time() * 1000)
            filename = f"preview_{voice}_{timestamp}.mp3"
            file_path = Path(self.config.temp_dir) / filename

            # Guardar audio
            audio_content = response.content
            file_path.write_bytes(audio_content)

            # Calcular duración aproximada (estimación simple)
            # OpenAI TTS-1 genera ~1 segundo por ~15-20 caracteres
            duration_estimate = max(1.0, len(text) / 18.0)

            # Crear respuesta
            tts_response = TTSResponse(
                audio_file_path=str(file_path),
                voice=voice,
                provider="openai",
                text_used=text,
                file_size_bytes=len(audio_content),
                duration_seconds=duration_estimate
            )

            logger.info(f"Preview generado exitosamente: {voice} ({len(audio_content)} bytes)")
            return tts_response

        except httpx.RequestError as e:
            logger.error(f"Error de conexión con OpenAI: {e}")
            raise TTSAPIError(f"Error de conexión con OpenAI: {e}")
        except Exception as e:
            logger.error(f"Error generando preview con OpenAI: {e}")
            raise AudioGenerationError(f"Error generando audio: {e}")

    async def _generate_elevenlabs_preview(self, voice: str, text: str) -> TTSResponse:
        """
        Genera preview usando ElevenLabs TTS API.

        Args:
            voice: Voz a usar
            text: Texto a sintetizar

        Returns:
            TTSResponse: Respuesta con audio generado
        """
        if not self.elevenlabs_client:
            raise TTSAPIError("ElevenLabs no está configurado")

        try:
            # Mapear voces de AILOOS a voces de ElevenLabs
            # Nota: ElevenLabs tiene voces específicas por ID, aquí usamos IDs de ejemplo
            elevenlabs_voice_map = {
                "ember": "21m00Tcm4TlvDq8ikWAM",  # Rachel (similar a ember)
                "alloy": "AZnzlk1XvdvUeBnXmlld",   # Dora (similar a alloy)
                "echo": "EXAVITQu4vr4xnSDxMaL"     # Bella (similar a echo)
            }

            elevenlabs_voice_id = elevenlabs_voice_map.get(voice)

            if not elevenlabs_voice_id:
                raise VoiceValidationError(f"Voz '{voice}' no disponible en ElevenLabs")

            # Preparar solicitud
            payload = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }

            # Hacer solicitud a ElevenLabs
            url = f"/text-to-speech/{elevenlabs_voice_id}"
            response = await self.elevenlabs_client.post(url, json=payload)

            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Error en ElevenLabs API: {response.status_code} - {error_detail}")
                raise TTSAPIError(f"Error en ElevenLabs API: {response.status_code}")

            # Generar nombre de archivo único
            timestamp = int(time.time() * 1000)
            filename = f"preview_{voice}_{timestamp}.mp3"
            file_path = Path(self.config.temp_dir) / filename

            # Guardar audio
            audio_content = response.content
            file_path.write_bytes(audio_content)

            # Calcular duración aproximada
            duration_estimate = max(1.0, len(text) / 15.0)

            # Crear respuesta
            tts_response = TTSResponse(
                audio_file_path=str(file_path),
                voice=voice,
                provider="elevenlabs",
                text_used=text,
                file_size_bytes=len(audio_content),
                duration_seconds=duration_estimate
            )

            logger.info(f"Preview generado exitosamente con ElevenLabs: {voice} ({len(audio_content)} bytes)")
            return tts_response

        except httpx.RequestError as e:
            logger.error(f"Error de conexión con ElevenLabs: {e}")
            raise TTSAPIError(f"Error de conexión con ElevenLabs: {e}")
        except Exception as e:
            logger.error(f"Error generando preview con ElevenLabs: {e}")
            raise AudioGenerationError(f"Error generando audio: {e}")

    async def cleanup_temp_files(self, max_age_hours: Optional[int] = None) -> int:
        """
        Limpia archivos temporales antiguos.

        Args:
            max_age_hours: Horas de antigüedad máxima (usa config si no se especifica)

        Returns:
            int: Número de archivos eliminados
        """
        if max_age_hours is None:
            max_age_hours = self.config.max_file_age_hours

        temp_path = Path(self.config.temp_dir)
        if not temp_path.exists():
            return 0

        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        deleted_count = 0

        try:
            for file_path in temp_path.glob("*.mp3"):
                if file_path.stat().st_mtime < cutoff_time.timestamp():
                    file_path.unlink()
                    deleted_count += 1

            if deleted_count > 0:
                logger.info(f"Archivos temporales limpiados: {deleted_count}")

            return deleted_count

        except Exception as e:
            logger.error(f"Error limpiando archivos temporales: {e}")
            return 0

    async def get_temp_file_info(self) -> Dict[str, Any]:
        """
        Obtiene información sobre archivos temporales.

        Returns:
            Dict[str, Any]: Información de archivos temporales
        """
        temp_path = Path(self.config.temp_dir)
        if not temp_path.exists():
            return {"total_files": 0, "total_size_bytes": 0, "files": []}

        files_info = []
        total_size = 0

        try:
            for file_path in temp_path.glob("*.mp3"):
                stat = file_path.stat()
                files_info.append({
                    "filename": file_path.name,
                    "size_bytes": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
                total_size += stat.st_size

            return {
                "total_files": len(files_info),
                "total_size_bytes": total_size,
                "files": files_info
            }

        except Exception as e:
            logger.error(f"Error obteniendo información de archivos temporales: {e}")
            return {"total_files": 0, "total_size_bytes": 0, "files": [], "error": str(e)}

    async def close(self) -> None:
        """Cierra los clientes HTTP y libera recursos."""
        await self.openai_client.aclose()
        if self.elevenlabs_client:
            await self.elevenlabs_client.aclose()
        logger.info("Servicio TTS cerrado")

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()