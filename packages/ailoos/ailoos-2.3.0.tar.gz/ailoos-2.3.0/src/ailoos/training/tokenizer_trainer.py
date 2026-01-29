#!/usr/bin/env python3
"""
Tokenizer Trainer para fine-tuning de tokenizer en dominio AILOOS.
Implementa análisis de corpus, recopilación de datos y entrenamiento BPE con SentencePiece.
"""

import os
import json
import time
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import Counter, defaultdict

# Añadir el directorio raíz al path para evitar dependencias del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import sentencepiece as spm
except ImportError:
    print("❌ SentencePiece no está instalado. Instale con: pip install sentencepiece")
    sys.exit(1)

logger = logging.getLogger(__name__)


@dataclass
class CorpusStats:
    """Estadísticas del corpus de datos."""
    total_texts: int = 0
    total_tokens: int = 0
    unique_tokens: int = 0
    avg_text_length: float = 0.0
    hot_data_ratio: float = 0.0
    cold_data_ratio: float = 0.0
    domain_specific_terms: List[str] = None
    timestamp: float = 0.0

    def __post_init__(self):
        if self.domain_specific_terms is None:
            self.domain_specific_terms = []
        self.timestamp = time.time()


@dataclass
class DataSource:
    """Fuente de datos para el corpus."""
    name: str
    path: str
    data_type: str  # 'collections', 'logs', 'federated'
    last_modified: Optional[float] = None
    text_count: int = 0


class CorpusAnalyzer:
    """Analizador de corpus para datos calientes/fríos."""

    def __init__(self, hot_data_threshold_days: int = 30):
        self.hot_data_threshold_days = hot_data_threshold_days
        self.hot_threshold_timestamp = time.time() - (hot_data_threshold_days * 24 * 3600)

    def analyze_corpus(self, texts: List[str], timestamps: Optional[List[float]] = None) -> CorpusStats:
        """
        Analizar corpus y clasificar datos calientes/fríos.

        Args:
            texts: Lista de textos
            timestamps: Timestamps correspondientes (opcional)

        Returns:
            Estadísticas del corpus
        """
        if not texts:
            return CorpusStats()

        # Estadísticas básicas
        total_texts = len(texts)
        text_lengths = [len(text.split()) for text in texts]
        avg_text_length = sum(text_lengths) / len(text_lengths) if text_lengths else 0

        # Tokenización básica para estadísticas
        all_tokens = []
        for text in texts:
            tokens = self._basic_tokenize(text)
            all_tokens.extend(tokens)

        total_tokens = len(all_tokens)
        unique_tokens = len(set(all_tokens))

        # Análisis de datos calientes/fríos
        hot_data_ratio = 0.0
        cold_data_ratio = 0.0

        if timestamps:
            hot_texts = sum(1 for ts in timestamps if ts >= self.hot_threshold_timestamp)
            hot_data_ratio = hot_texts / total_texts if total_texts > 0 else 0
            cold_data_ratio = 1 - hot_data_ratio

        # Identificar términos específicos del dominio AILOOS
        domain_terms = self._identify_domain_terms(all_tokens)

        return CorpusStats(
            total_texts=total_texts,
            total_tokens=total_tokens,
            unique_tokens=unique_tokens,
            avg_text_length=avg_text_length,
            hot_data_ratio=hot_data_ratio,
            cold_data_ratio=cold_data_ratio,
            domain_specific_terms=domain_terms
        )

    def _basic_tokenize(self, text: str) -> List[str]:
        """Tokenización básica para análisis."""
        # Limpieza básica
        text = text.lower()
        # Dividir por espacios y puntuación básica
        import re
        tokens = re.findall(r'\b\w+\b', text)
        return tokens

    def _identify_domain_terms(self, tokens: List[str]) -> List[str]:
        """Identificar términos específicos del dominio AILOOS."""
        # Términos clave del dominio federated learning y AILOOS
        domain_keywords = {
            'federated', 'learning', 'model', 'training', 'session', 'node', 'coordinator',
            'aggregation', 'privacy', 'budget', 'round', 'weights', 'dataset', 'inference',
            'blockchain', 'dracma', 'wallet', 'marketplace', 'rag', 'embedding', 'vector',
            'consensus', 'validation', 'verification', 'auditing', 'compliance', 'security',
            'encryption', 'signature', 'certificate', 'p2p', 'ipfs', 'cid', 'distributed',
            'decentralized', 'sovereign', 'ai', 'machine', 'learning', 'empiorio', 'ailoos'
        }

        # Contar frecuencia
        token_counts = Counter(tokens)
        domain_terms = []

        for token, count in token_counts.most_common(100):  # Top 100 términos
            if token in domain_keywords and count > 5:  # Frecuencia mínima
                domain_terms.append(token)

        return domain_terms[:20]  # Top 20


class DataCollector:
    """Recopilador de datos desde múltiples fuentes."""

    def __init__(self, base_path: str = "/Users/juliojavier/Desktop/Ailoos"):
        self.base_path = Path(base_path)
        self.sources = self._initialize_sources()

    def _initialize_sources(self) -> List[DataSource]:
        """Inicializar fuentes de datos."""
        sources = []

        # Collections
        collections_path = self.base_path / "collections"
        if collections_path.exists():
            for file_path in collections_path.glob("*.json"):
                sources.append(DataSource(
                    name=f"collection_{file_path.stem}",
                    path=str(file_path),
                    data_type="collections"
                ))

        # Reports (logs RAG)
        reports_path = self.base_path / "reports"
        if reports_path.exists():
            for file_path in reports_path.glob("*.json"):
                if "rag" in file_path.name.lower():
                    sources.append(DataSource(
                        name=f"rag_log_{file_path.stem}",
                        path=str(file_path),
                        data_type="logs"
                    ))

        # Federated data (archivos de configuración y logs)
        federated_path = self.base_path / "src" / "ailoos" / "federated"
        if federated_path.exists():
            for file_path in federated_path.glob("*.py"):
                sources.append(DataSource(
                    name=f"federated_code_{file_path.stem}",
                    path=str(file_path),
                    data_type="federated"
                ))

        return sources

    def collect_texts(self) -> Tuple[List[str], List[float]]:
        """
        Recopilar textos desde todas las fuentes.

        Returns:
            Tupla de (textos, timestamps)
        """
        all_texts = []
        all_timestamps = []

        for source in self.sources:
            try:
                texts, timestamps = self._extract_texts_from_source(source)
                all_texts.extend(texts)
                all_timestamps.extend(timestamps)

                logger.info(f"✅ Recopilados {len(texts)} textos de {source.name}")

            except Exception as e:
                logger.warning(f"⚠️ Error recopilando de {source.name}: {e}")

        logger.info(f"📊 Total recopilados: {len(all_texts)} textos")
        return all_texts, all_timestamps

    def _extract_texts_from_source(self, source: DataSource) -> Tuple[List[str], List[float]]:
        """Extraer textos de una fuente específica."""
        texts = []
        timestamps = []

        if source.data_type == "collections":
            texts, timestamps = self._extract_from_collections(source.path)
        elif source.data_type == "logs":
            texts, timestamps = self._extract_from_logs(source.path)
        elif source.data_type == "federated":
            texts, timestamps = self._extract_from_federated(source.path)

        return texts, timestamps

    def _extract_from_collections(self, file_path: str) -> Tuple[List[str], List[float]]:
        """Extraer textos de archivos de collections."""
        texts = []
        timestamps = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extraer textos de diferentes estructuras
            if "resources" in data:  # Formato Insomnia
                for resource in data["resources"]:
                    if "name" in resource:
                        texts.append(resource["name"])
                        timestamps.append(time.time())  # Timestamp actual como aproximación

                    if "description" in resource:
                        texts.append(resource["description"])
                        timestamps.append(time.time())

                    # Extraer de requests
                    if "item" in resource:
                        texts_from_items, ts_from_items = self._extract_from_collection_items(resource["item"])
                        texts.extend(texts_from_items)
                        timestamps.extend(ts_from_items)

            elif isinstance(data, list):  # Lista de items
                texts_from_items, ts_from_items = self._extract_from_collection_items(data)
                texts.extend(texts_from_items)
                timestamps.extend(ts_from_items)

        except Exception as e:
            logger.warning(f"Error procesando collection {file_path}: {e}")

        return texts, timestamps

    def _extract_from_collection_items(self, items: List[Dict]) -> Tuple[List[str], List[float]]:
        """Extraer textos de items de collection."""
        texts = []
        timestamps = []

        for item in items:
            # Nombre del request
            if "name" in item:
                texts.append(item["name"])
                timestamps.append(time.time())

            # Descripción
            if "description" in item:
                texts.append(item["description"])
                timestamps.append(time.time())

            # URL y parámetros
            if "request" in item:
                request = item["request"]
                if "url" in request:
                    if isinstance(request["url"], dict) and "raw" in request["url"]:
                        texts.append(request["url"]["raw"])
                        timestamps.append(time.time())

                # Body del request
                if "body" in request and "raw" in request["body"]:
                    texts.append(request["body"]["raw"])
                    timestamps.append(time.time())

            # Sub-items recursivos
            if "item" in item:
                sub_texts, sub_timestamps = self._extract_from_collection_items(item["item"])
                texts.extend(sub_texts)
                timestamps.extend(sub_timestamps)

        return texts, timestamps

    def _extract_from_logs(self, file_path: str) -> Tuple[List[str], List[float]]:
        """Extraer textos de archivos de logs RAG."""
        texts = []
        timestamps = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extraer textos de diferentes estructuras de logs
            if "scenarios" in data:  # Formato benchmark RAG
                for scenario_name, scenario_data in data["scenarios"].items():
                    texts.append(f"Scenario: {scenario_name}")
                    timestamps.append(data.get("timestamp", time.time()))

                    # Extraer descripciones y métricas
                    if "performance_improvements" in scenario_data:
                        improvements = scenario_data["performance_improvements"]
                        texts.append(f"Latency improvement: {improvements.get('latency_improvement', 0):.2f}%")
                        texts.append(f"Throughput improvement: {improvements.get('throughput_improvement', 0):.2f}%")
                        timestamps.extend([data.get("timestamp", time.time())] * 2)

            elif isinstance(data, list):  # Lista de logs
                for entry in data:
                    if isinstance(entry, dict):
                        # Extraer campos de texto
                        for key, value in entry.items():
                            if isinstance(value, str) and len(value) > 10:
                                texts.append(value)
                                timestamps.append(entry.get("timestamp", time.time()))

        except Exception as e:
            logger.warning(f"Error procesando log {file_path}: {e}")

        return texts, timestamps

    def _extract_from_federated(self, file_path: str) -> Tuple[List[str], List[float]]:
        """Extraer textos de archivos federated (código y documentación)."""
        texts = []
        timestamps = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extraer docstrings y comentarios
            lines = content.split('\n')
            current_docstring = []
            in_docstring = False

            for line in lines:
                line = line.strip()

                # Detectar docstrings
                if '"""' in line or "'''" in line:
                    if in_docstring:
                        # Fin de docstring
                        if current_docstring:
                            docstring_text = ' '.join(current_docstring)
                            if len(docstring_text) > 20:  # Docstring significativo
                                texts.append(docstring_text)
                                timestamps.append(os.path.getmtime(file_path))
                        current_docstring = []
                        in_docstring = False
                    else:
                        # Inicio de docstring
                        in_docstring = True
                elif in_docstring:
                    current_docstring.append(line)

                # Extraer comentarios
                elif line.startswith('#') and len(line) > 5:
                    comment = line[1:].strip()
                    if len(comment) > 10:
                        texts.append(comment)
                        timestamps.append(os.path.getmtime(file_path))

                # Extraer strings literales largos (posibles mensajes)
                elif ('"' in line or "'" in line) and len(line) > 20:
                    # Extraer strings entre comillas
                    import re
                    strings = re.findall(r'["\']([^"\']+)["\']', line)
                    for string in strings:
                        if len(string) > 10 and not string.startswith('http'):
                            texts.append(string)
                            timestamps.append(os.path.getmtime(file_path))

        except Exception as e:
            logger.warning(f"Error procesando federated file {file_path}: {e}")

        return texts, timestamps


class SentencePieceTrainer:
    """Entrenador de tokenizer BPE con SentencePiece."""

    def __init__(self, vocab_size: int = 32000, model_type: str = "bpe"):
        self.vocab_size = vocab_size
        self.model_type = model_type
        self.model_path = None

    def prepare_training_data(self, texts: List[str], output_file: str) -> str:
        """
        Preparar datos de entrenamiento para SentencePiece.

        Args:
            texts: Lista de textos
            output_file: Archivo de salida

        Returns:
            Ruta del archivo preparado
        """
        logger.info(f"📝 Preparando {len(texts)} textos para entrenamiento...")

        # Filtrar y limpiar textos
        cleaned_texts = []
        for text in texts:
            if isinstance(text, str) and len(text.strip()) > 5:
                # Limpieza básica
                cleaned = text.strip()
                cleaned = ' '.join(cleaned.split())  # Normalizar espacios
                if len(cleaned) > 10:  # Texto significativo
                    cleaned_texts.append(cleaned)

        # Eliminar duplicados manteniendo orden aproximado
        seen = set()
        unique_texts = []
        for text in cleaned_texts:
            if text not in seen:
                unique_texts.append(text)
                seen.add(text)

        logger.info(f"✅ Preparados {len(unique_texts)} textos únicos")

        # Escribir archivo de entrenamiento
        with open(output_file, 'w', encoding='utf-8') as f:
            for text in unique_texts:
                f.write(text + '\n')

        logger.info(f"💾 Datos guardados en {output_file}")
        return output_file

    def train_tokenizer(self, input_file: str, model_prefix: str,
                       character_coverage: float = 0.9995) -> str:
        """
        Entrenar tokenizer con SentencePiece.

        Args:
            input_file: Archivo de entrada
            model_prefix: Prefijo para archivos del modelo
            character_coverage: Cobertura de caracteres

        Returns:
            Ruta del modelo entrenado
        """
        logger.info(f"🚀 Entrenando tokenizer BPE con vocab_size={self.vocab_size}...")

        # Configurar parámetros de entrenamiento
        spm_args = {
            'input': input_file,
            'model_prefix': model_prefix,
            'vocab_size': self.vocab_size,
            'model_type': self.model_type,
            'character_coverage': character_coverage,
            'unk_id': 0,
            'bos_id': 1,
            'eos_id': 2,
            'pad_id': -1,
            'unk_piece': '<unk>',
            'bos_piece': '<s>',
            'eos_piece': '</s>',
            'pad_piece': '<pad>',
            'user_defined_symbols': [
                '<mask>', '<sep>', '<cls>',
                '[FEDERATED]', '[RAG]', '[BLOCKCHAIN]', '[AI]', '[TRAINING]'
            ]
        }

        # Entrenar modelo
        spm.SentencePieceTrainer.train(**spm_args)

        model_file = f"{model_prefix}.model"
        vocab_file = f"{model_prefix}.vocab"

        if os.path.exists(model_file):
            self.model_path = model_file
            logger.info(f"✅ Tokenizer entrenado: {model_file}")
            logger.info(f"📊 Vocabulario guardado: {vocab_file}")

            # Mostrar estadísticas del vocabulario
            self._show_vocab_stats(vocab_file)
        else:
            raise FileNotFoundError(f"Modelo no encontrado: {model_file}")

        return model_file

    def _show_vocab_stats(self, vocab_file: str):
        """Mostrar estadísticas del vocabulario."""
        try:
            with open(vocab_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            logger.info(f"📈 Vocabulario: {len(lines)} tokens")

            # Mostrar algunos tokens de ejemplo
            logger.info("🔍 Ejemplos de tokens:")
            for i, line in enumerate(lines[:10]):
                token, score = line.strip().split('\t')
                logger.info(f"  {i+1:2d}: {token} (score: {score})")

        except Exception as e:
            logger.warning(f"Error mostrando estadísticas del vocabulario: {e}")

    def load_tokenizer(self, model_path: str) -> spm.SentencePieceProcessor:
        """Cargar tokenizer entrenado."""
        sp = spm.SentencePieceProcessor()
        sp.load(model_path)
        logger.info(f"✅ Tokenizer cargado desde {model_path}")
        return sp

    def test_tokenizer(self, sp: spm.SentencePieceProcessor, test_texts: List[str]) -> Dict[str, Any]:
        """Probar tokenizer con textos de ejemplo."""
        results = {
            'total_texts': len(test_texts),
            'avg_tokens_per_text': 0.0,
            'total_tokens': 0,
            'unknown_tokens': 0,
            'examples': []
        }

        total_tokens = 0
        total_unknown = 0

        for i, text in enumerate(test_texts[:5]):  # Probar con primeros 5
            tokens = sp.encode_as_pieces(text)
            ids = sp.encode_as_ids(text)

            total_tokens += len(tokens)
            unknown_count = sum(1 for tid in ids if tid == sp.unk_id())
            total_unknown += unknown_count

            results['examples'].append({
                'text': text[:100] + '...' if len(text) > 100 else text,
                'tokens': tokens[:20],  # Primeros 20 tokens
                'token_count': len(tokens),
                'unknown_count': unknown_count
            })

        if results['total_texts'] > 0:
            results['avg_tokens_per_text'] = total_tokens / results['total_texts']
        results['total_tokens'] = total_tokens
        results['unknown_tokens'] = total_unknown

        return results


class TokenizerTrainer:
    """Trainer completo para tokenizer en dominio AILOOS."""

    def __init__(self, vocab_size: int = 32000, hot_data_threshold_days: int = 30):
        self.vocab_size = vocab_size
        self.hot_data_threshold_days = hot_data_threshold_days

        # Componentes
        self.data_collector = DataCollector()
        self.corpus_analyzer = CorpusAnalyzer(hot_data_threshold_days)
        self.sp_trainer = SentencePieceTrainer(vocab_size)

        # Estado
        self.corpus_stats = None
        self.trained_model_path = None

        logger.info("🚀 TokenizerTrainer inicializado para dominio AILOOS")

    def train_tokenizer(self, output_dir: str = "./tokenizer_output") -> Dict[str, Any]:
        """
        Entrenar tokenizer completo desde recopilación hasta modelo final.

        Args:
            output_dir: Directorio de salida

        Returns:
            Resultados del entrenamiento
        """
        start_time = time.time()

        # Crear directorio de salida
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = {
            'success': False,
            'training_time': 0.0,
            'corpus_stats': None,
            'model_path': None,
            'vocab_size': self.vocab_size,
            'test_results': None,
            'error': None
        }

        try:
            logger.info("📊 Paso 1: Recopilando datos del corpus...")

            # 1. Recopilar datos
            texts, timestamps = self.data_collector.collect_texts()

            if not texts:
                raise ValueError("No se recopilaron textos suficientes")

            logger.info("📊 Paso 2: Analizando corpus...")

            # 2. Analizar corpus
            self.corpus_stats = self.corpus_analyzer.analyze_corpus(texts, timestamps)
            results['corpus_stats'] = {
                'total_texts': self.corpus_stats.total_texts,
                'total_tokens': self.corpus_stats.total_tokens,
                'unique_tokens': self.corpus_stats.unique_tokens,
                'avg_text_length': self.corpus_stats.avg_text_length,
                'hot_data_ratio': self.corpus_stats.hot_data_ratio,
                'cold_data_ratio': self.corpus_stats.cold_data_ratio,
                'domain_terms': self.corpus_stats.domain_specific_terms
            }

            logger.info(f"📈 Corpus: {self.corpus_stats.total_texts} textos, "
                       f"{self.corpus_stats.total_tokens} tokens, "
                       f"{self.corpus_stats.hot_data_ratio:.1%} datos calientes")

            logger.info("📝 Paso 3: Preparando datos de entrenamiento...")

            # 3. Preparar datos para SentencePiece
            training_file = str(output_path / "ailoos_training.txt")
            self.sp_trainer.prepare_training_data(texts, training_file)

            logger.info("🚀 Paso 4: Entrenando tokenizer BPE...")

            # 4. Entrenar tokenizer
            model_prefix = str(output_path / "ailoos_tokenizer")
            model_path = self.sp_trainer.train_tokenizer(training_file, model_prefix)
            self.trained_model_path = model_path
            results['model_path'] = model_path

            logger.info("🧪 Paso 5: Probando tokenizer...")

            # 5. Probar tokenizer
            sp = self.sp_trainer.load_tokenizer(model_path)
            test_texts = texts[:10] if len(texts) >= 10 else texts
            test_results = self.sp_trainer.test_tokenizer(sp, test_texts)
            results['test_results'] = test_results

            logger.info(f"✅ Tokenizer probado: {test_results['avg_tokens_per_text']:.1f} tokens/texto promedio")

            results['success'] = True
            results['training_time'] = time.time() - start_time

            logger.info(f"🎉 Entrenamiento completado en {results['training_time']:.2f}s")
            logger.info(f"📁 Modelo guardado en: {model_path}")

        except Exception as e:
            logger.error(f"❌ Error en entrenamiento: {e}")
            results['error'] = str(e)

        return results

    def get_corpus_stats(self) -> Optional[CorpusStats]:
        """Obtener estadísticas del corpus."""
        return self.corpus_stats

    def load_trained_tokenizer(self) -> Optional[spm.SentencePieceProcessor]:
        """Cargar tokenizer entrenado."""
        if self.trained_model_path and os.path.exists(self.trained_model_path):
            return self.sp_trainer.load_tokenizer(self.trained_model_path)
        return None


def main():
    """Función principal para ejecutar el entrenamiento."""
    import argparse

    parser = argparse.ArgumentParser(description="Tokenizer Trainer para dominio AILOOS")
    parser.add_argument("--vocab-size", type=int, default=32000,
                       help="Tamaño del vocabulario")
    parser.add_argument("--output-dir", type=str, default="./tokenizer_output",
                       help="Directorio de salida")
    parser.add_argument("--hot-threshold", type=int, default=30,
                       help="Días para considerar datos como 'calientes'")

    args = parser.parse_args()

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Entrenar tokenizer
    trainer = TokenizerTrainer(
        vocab_size=args.vocab_size,
        hot_data_threshold_days=args.hot_threshold
    )

    results = trainer.train_tokenizer(args.output_dir)

    # Mostrar resultados
    if results['success']:
        print("\n🎉 Entrenamiento exitoso!")
        print(f"⏱️  Tiempo total: {results['training_time']:.2f}s")
        print(f"📊 Corpus: {results['corpus_stats']['total_texts']} textos")
        print(f"🔤 Vocabulario: {results['vocab_size']} tokens")
        print(f"📁 Modelo: {results['model_path']}")
        print(f"📈 Tokens/texto promedio: {results['test_results']['avg_tokens_per_text']:.1f}")
        print(f"🔥 Datos calientes: {results['corpus_stats']['hot_data_ratio']:.1%}")
        print(f"🧊 Datos fríos: {results['corpus_stats']['cold_data_ratio']:.1%}")
        print(f"🎯 Términos dominio: {', '.join(results['corpus_stats']['domain_terms'][:5])}")
    else:
        print(f"\n❌ Error: {results['error']}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())