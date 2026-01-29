"""
Text Preprocessor for EmpoorioLM
Sistema avanzado de preprocesamiento de texto para datos masivos.
"""

import re
import unicodedata
from typing import List, Dict, Any, Optional, Tuple, Set
import logging
from pathlib import Path
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class TextPreprocessingConfig:
    """Configuración del preprocesamiento de texto."""

    # Limpieza básica
    remove_urls: bool = True
    remove_emails: bool = True
    remove_mentions: bool = True
    remove_hashtags: bool = False  # Útil para análisis de tendencias
    remove_punctuation: bool = False  # Mantener para LM

    # Normalización
    lowercase: bool = False  # Case-sensitive para LM
    normalize_unicode: bool = True
    remove_extra_whitespace: bool = True

    # Filtros de calidad
    min_length: int = 10
    max_length: int = 10000
    min_words: int = 3
    max_words: int = 2000

    # Filtros de idioma (simplificado)
    allowed_languages: Optional[Set[str]] = None  # ['es', 'en', etc.]

    # Filtros de contenido
    remove_duplicates: bool = True
    remove_near_duplicates: bool = False  # Computacionalmente costoso
    similarity_threshold: float = 0.85

    # Configuración de rendimiento
    max_workers: int = 4
    batch_size: int = 1000

    # Estadísticas
    enable_stats: bool = True


class TextPreprocessor:
    """
    Preprocesador avanzado de texto para EmpoorioLM.

    Funcionalidades:
    - Limpieza y normalización de texto
    - Detección y eliminación de duplicados
    - Filtros de calidad de contenido
    - Procesamiento distribuido para datos masivos
    - Estadísticas detalladas de procesamiento
    """

    def __init__(self, config: TextPreprocessingConfig):
        self.config = config
        self.stats = {
            "processed_texts": 0,
            "filtered_texts": 0,
            "duplicate_texts": 0,
            "quality_filtered": 0,
            "language_filtered": 0,
            "total_input_chars": 0,
            "total_output_chars": 0,
            "processing_time": 0.0
        }

        # Compilar expresiones regulares para eficiencia
        self._compile_regex()

        # Conjunto para detección de duplicados
        self.seen_hashes: Set[str] = set()

        logger.info("🧹 TextPreprocessor inicializado")

    def _compile_regex(self):
        """Compilar expresiones regulares para limpieza."""
        # URLs
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )

        # Emails
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

        # Menciones de Twitter/Redes sociales
        self.mention_pattern = re.compile(r'@\w+')

        # Hashtags
        self.hashtag_pattern = re.compile(r'#\w+')

        # Múltiples espacios en blanco
        self.whitespace_pattern = re.compile(r'\s+')

    def preprocess_batch(self, texts: List[str]) -> List[str]:
        """
        Preprocesar un lote de textos.

        Args:
            texts: Lista de textos a procesar

        Returns:
            Lista de textos procesados
        """
        import time
        start_time = time.time()

        # Procesar en paralelo si hay muchos textos
        if len(texts) > self.config.batch_size:
            processed_texts = self._preprocess_parallel(texts)
        else:
            processed_texts = [self.preprocess_text(text) for text in texts]

        # Filtrar textos vacíos o None
        processed_texts = [text for text in processed_texts if text and len(text.strip()) > 0]

        # Actualizar estadísticas
        processing_time = time.time() - start_time
        self.stats["processed_texts"] += len(texts)
        self.stats["filtered_texts"] += (len(texts) - len(processed_texts))
        self.stats["processing_time"] += processing_time

        if self.config.enable_stats:
            self.stats["total_input_chars"] += sum(len(text) for text in texts)
            self.stats["total_output_chars"] += sum(len(text) for text in processed_texts)

        return processed_texts

    def _preprocess_parallel(self, texts: List[str]) -> List[str]:
        """Procesar textos en paralelo para mejor rendimiento."""
        batches = [
            texts[i:i + self.config.batch_size]
            for i in range(0, len(texts), self.config.batch_size)
        ]

        processed_batches = []
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = [
                executor.submit(self.preprocess_batch, batch)
                for batch in batches
            ]

            for future in futures:
                processed_batches.extend(future.result())

        return processed_batches

    def preprocess_text(self, text: str) -> Optional[str]:
        """
        Preprocesar un texto individual.

        Args:
            text: Texto a procesar

        Returns:
            Texto procesado o None si debe filtrarse
        """
        if not text or not isinstance(text, str):
            return None

        original_text = text

        # 1. Limpieza básica
        text = self._clean_text(text)

        # 2. Normalización
        text = self._normalize_text(text)

        # 3. Filtros de calidad
        if not self._passes_quality_filters(text):
            self.stats["quality_filtered"] += 1
            return None

        # 4. Detección de duplicados
        if self.config.remove_duplicates and not self._is_unique(text):
            self.stats["duplicate_texts"] += 1
            return None

        # 5. Filtro de idioma (simplificado)
        if self.config.allowed_languages and not self._passes_language_filter(text):
            self.stats["language_filtered"] += 1
            return None

        return text

    def _clean_text(self, text: str) -> str:
        """Limpiar texto básico."""
        # Convertir a string si no lo es
        text = str(text)

        # Remover URLs
        if self.config.remove_urls:
            text = self.url_pattern.sub('', text)

        # Remover emails
        if self.config.remove_emails:
            text = self.email_pattern.sub('', text)

        # Remover menciones
        if self.config.remove_mentions:
            text = self.mention_pattern.sub('', text)

        # Remover hashtags
        if self.config.remove_hashtags:
            text = self.hashtag_pattern.sub('', text)

        # Remover caracteres de control
        text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C')

        return text

    def _normalize_text(self, text: str) -> str:
        """Normalizar texto."""
        # Minúsculas
        if self.config.lowercase:
            text = text.lower()

        # Normalizar Unicode
        if self.config.normalize_unicode:
            text = unicodedata.normalize('NFKC', text)

        # Remover espacios extra
        if self.config.remove_extra_whitespace:
            text = self.whitespace_pattern.sub(' ', text).strip()

        return text

    def _passes_quality_filters(self, text: str) -> bool:
        """Verificar si el texto pasa los filtros de calidad."""
        # Longitud de caracteres
        if not (self.config.min_length <= len(text) <= self.config.max_length):
            return False

        # Número de palabras
        words = text.split()
        if not (self.config.min_words <= len(words) <= self.config.max_words):
            return False

        # Verificar que no esté vacío después del procesamiento
        if len(text.strip()) == 0:
            return False

        # Verificar que tenga caracteres legibles
        readable_chars = sum(1 for char in text if char.isalnum() or char.isspace())
        if readable_chars / len(text) < 0.3:  # Al menos 30% caracteres legibles
            return False

        return True

    def _is_unique(self, text: str) -> bool:
        """Verificar si el texto es único (no duplicado)."""
        # Crear hash del texto para comparación eficiente
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()

        if text_hash in self.seen_hashes:
            return False

        self.seen_hashes.add(text_hash)
        return True

    def _passes_language_filter(self, text: str) -> bool:
        """Filtro básico de idioma (muy simplificado)."""
        if not self.config.allowed_languages:
            return True

        # Detección muy básica por caracteres comunes
        # En producción, usar librerías como langdetect o fasttext
        text_lower = text.lower()

        # Caracteres específicos por idioma
        language_markers = {
            'es': ['ñ', 'á', 'é', 'í', 'ó', 'ú', 'ü', '¿', '¡'],
            'en': ['w', 'k', 'z'],  # Más distintivos que comunes
            'fr': ['ç', 'à', 'è', 'ù', 'â', 'ê', 'î', 'ô', 'û'],
            'de': ['ä', 'ö', 'ü', 'ß'],
            'pt': ['ã', 'õ', 'ç'],
        }

        detected_languages = set()

        for lang, markers in language_markers.items():
            if any(marker in text_lower for marker in markers):
                detected_languages.add(lang)

        # Si se detecta al menos un idioma permitido
        return bool(detected_languages & self.config.allowed_languages)

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de procesamiento."""
        stats = self.stats.copy()

        # Calcular métricas derivadas
        if stats["processed_texts"] > 0:
            stats["filtration_rate"] = stats["filtered_texts"] / stats["processed_texts"]
            stats["duplicate_rate"] = stats["duplicate_texts"] / stats["processed_texts"]
            stats["quality_filtration_rate"] = stats["quality_filtered"] / stats["processed_texts"]

        if stats["total_input_chars"] > 0:
            stats["compression_ratio"] = stats["total_output_chars"] / stats["total_input_chars"]

        if stats["processing_time"] > 0:
            stats["throughput"] = stats["processed_texts"] / stats["processing_time"]

        return stats

    def reset_stats(self):
        """Reiniciar estadísticas."""
        self.stats = {key: 0.0 if isinstance(value, float) else 0 for key, value in self.stats.items()}
        self.seen_hashes.clear()

    def save_stats(self, filepath: str):
        """Guardar estadísticas en archivo JSON."""
        stats = self.get_stats()
        stats["timestamp"] = json.dumps(stats, indent=2, default=str)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, default=str)

    def load_stats(self, filepath: str):
        """Cargar estadísticas desde archivo."""
        with open(filepath, 'r', encoding='utf-8') as f:
            saved_stats = json.load(f)

        # Actualizar estadísticas actuales
        for key, value in saved_stats.items():
            if key in self.stats:
                self.stats[key] = value


class DataPreprocessor:
    """
    Preprocesador de datos de alto nivel para EmpoorioLM.

    Coordina múltiples preprocesadores y maneja datasets grandes.
    """

    def __init__(self, text_config: Optional[TextPreprocessingConfig] = None):
        self.text_preprocessor = TextPreprocessor(text_config or TextPreprocessingConfig())
        self.dataset_stats = {}

        logger.info("🔧 DataPreprocessor inicializado")

    def preprocess_dataset(
        self,
        input_path: str,
        output_path: str,
        format: str = "jsonl"
    ) -> Dict[str, Any]:
        """
        Preprocesar un dataset completo.

        Args:
            input_path: Ruta del dataset de entrada
            output_path: Ruta del dataset de salida
            format: Formato del archivo ('jsonl', 'txt', 'csv')

        Returns:
            Estadísticas del procesamiento
        """
        logger.info(f"📊 Procesando dataset: {input_path}")

        # Cargar datos
        texts = self._load_dataset(input_path, format)

        # Preprocesar
        processed_texts = self.text_preprocessor.preprocess_batch(texts)

        # Guardar resultados
        self._save_dataset(processed_texts, output_path, format)

        # Recopilar estadísticas
        stats = {
            "input_path": input_path,
            "output_path": output_path,
            "original_texts": len(texts),
            "processed_texts": len(processed_texts),
            "processing_stats": self.text_preprocessor.get_stats()
        }

        logger.info(f"✅ Dataset procesado: {len(processed_texts)}/{len(texts)} textos mantenidos")
        return stats

    def _load_dataset(self, filepath: str, format: str) -> List[str]:
        """Cargar dataset desde archivo."""
        texts = []

        with open(filepath, 'r', encoding='utf-8') as f:
            if format == "jsonl":
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        if "text" in data:
                            texts.append(data["text"])
                    except json.JSONDecodeError:
                        continue
            elif format == "txt":
                content = f.read()
                # Dividir en párrafos
                paragraphs = content.split('\n\n')
                texts = [p.strip() for p in paragraphs if p.strip()]
            elif format == "csv":
                import csv
                reader = csv.DictReader(f)
                for row in reader:
                    if "text" in row:
                        texts.append(row["text"])

        return texts

    def _save_dataset(self, texts: List[str], filepath: str, format: str):
        """Guardar dataset procesado."""
        with open(filepath, 'w', encoding='utf-8') as f:
            if format == "jsonl":
                for text in texts:
                    json.dump({"text": text}, f, ensure_ascii=False)
                    f.write('\n')
            elif format == "txt":
                for text in texts:
                    f.write(text + '\n\n')
            elif format == "csv":
                import csv
                writer = csv.writer(f)
                writer.writerow(["text"])
                for text in texts:
                    writer.writerow([text])

    def get_combined_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas combinadas."""
        return {
            "text_preprocessing": self.text_preprocessor.get_stats(),
            "datasets_processed": self.dataset_stats
        }


# Funciones de conveniencia
def create_text_preprocessor(
    min_length: int = 10,
    max_length: int = 10000,
    remove_duplicates: bool = True
) -> TextPreprocessor:
    """Crear preprocesador de texto con configuración común."""
    config = TextPreprocessingConfig(
        min_length=min_length,
        max_length=max_length,
        remove_duplicates=remove_duplicates
    )
    return TextPreprocessor(config)


def preprocess_text_batch(
    texts: List[str],
    config: Optional[TextPreprocessingConfig] = None
) -> List[str]:
    """Función de conveniencia para preprocesar lote de textos."""
    preprocessor = TextPreprocessor(config or TextPreprocessingConfig())
    return preprocessor.preprocess_batch(texts)


if __name__ == "__main__":
    # Test del preprocesador
    print("🧪 Probando TextPreprocessor...")

    config = TextPreprocessingConfig()
    preprocessor = TextPreprocessor(config)

    test_texts = [
        "Este es un texto normal para probar el preprocesador.",
        "Texto con URL: https://example.com y email: test@example.com",
        "Texto muy corto.",
        "Texto con caracteres especiales: ñáéíóú 🚀 @usuario #hashtag",
        "",  # Texto vacío
        "Texto duplicado.",  # Duplicado
        "Texto duplicado.",  # Duplicado
    ]

    processed = preprocessor.preprocess_batch(test_texts)
    stats = preprocessor.get_stats()

    print(f"✅ Procesamiento completado: {len(processed)} textos válidos")
    print(f"📊 Estadísticas: {stats}")
    print("🎉 Preprocesador funcionando correctamente")