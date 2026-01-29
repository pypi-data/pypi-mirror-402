"""
Módulo TTS (Text-to-Speech) de AILOOS
=====================================

Este módulo proporciona funcionalidades para generar previews de audio de las voces disponibles,
incluyendo síntesis de texto a voz, gestión de archivos de audio temporales, y validación de voces.
Integra con APIs externas de TTS como OpenAI y ElevenLabs.
"""

from .service import (
    TTSConfig,
    TTSRequest,
    TTSResponse,
    TTSService,
    TTSServiceError,
    VoiceValidationError,
    TTSAPIError,
    AudioGenerationError
)

__all__ = [
    "TTSConfig",
    "TTSRequest",
    "TTSResponse",
    "TTSService",
    "TTSServiceError",
    "VoiceValidationError",
    "TTSAPIError",
    "AudioGenerationError"
]