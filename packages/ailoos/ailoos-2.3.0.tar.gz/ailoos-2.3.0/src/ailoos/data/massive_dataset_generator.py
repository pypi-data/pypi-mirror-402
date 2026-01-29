"""
Generador de datasets masivos para entrenamiento federado de EmpoorioLM.
Crea datasets realistas de alta calidad para pruebas de escala real.
"""

import json
import random
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Iterator
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
from dataclasses import dataclass
from enum import Enum


class DatasetType(Enum):
    """Tipos de datasets disponibles."""
    WIKIPEDIA_ARTICLES = "wikipedia"
    TECHNICAL_DOCS = "technical"
    CODE_REPOSITORIES = "code"
    BOOKS_TEXTS = "books"
    NEWS_ARTICLES = "news"
    SOCIAL_MEDIA = "social"


@dataclass
class DatasetConfig:
    """Configuración para generación de datasets."""
    dataset_type: DatasetType
    num_samples: int = 10000
    min_length: int = 100
    max_length: int = 2000
    language: str = "es"
    quality_level: str = "high"
    include_metadata: bool = True


class MassiveDatasetGenerator:
    """
    Generador de datasets masivos para entrenamiento federado.
    Crea contenido realista de alta calidad para pruebas de escala.
    """

    def __init__(self, output_dir: str = "./data/massive_datasets"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Templates de contenido por tipo
        self.templates = self._load_templates()

        # Estadísticas de generación
        self.stats = {
            "total_samples": 0,
            "total_tokens": 0,
            "generation_time": 0,
            "datasets_created": []
        }

    def _load_templates(self) -> Dict[str, List[str]]:
        """Carga templates de contenido por categoría."""
        return {
            "wikipedia": [
                "La inteligencia artificial (IA) es una rama de la informática que busca crear máquinas capaces de realizar tareas que requieren inteligencia humana. El término fue acuñado en 1956 por John McCarthy en la Conferencia de Darmouth. Desde entonces, ha evolucionado significativamente, incorporando técnicas como el aprendizaje automático, el procesamiento de lenguaje natural y la visión por computadora.",
                "El aprendizaje federado es un enfoque de aprendizaje automático que permite entrenar modelos de IA de manera distribuida, manteniendo la privacidad de los datos. Desarrollado por Google en 2016, permite que múltiples dispositivos colaboren en el entrenamiento de un modelo sin compartir sus datos locales.",
                "La computación en la nube se refiere a la entrega de servicios de computación a través de internet. Incluye servidores, almacenamiento, bases de datos, redes, software y análisis. Los proveedores principales son Amazon Web Services (AWS), Microsoft Azure y Google Cloud Platform.",
                "El procesamiento de lenguaje natural (NLP) es una rama de la IA que se enfoca en la interacción entre computadoras y lenguaje humano. Incluye tareas como traducción automática, análisis de sentimientos, resumen de textos y generación de lenguaje natural.",
                "La blockchain es una tecnología de registro distribuido que mantiene una lista creciente de registros, llamados bloques, que están vinculados mediante criptografía. Cada bloque contiene un hash criptográfico del bloque anterior, una marca de tiempo y datos de transacción."
            ],
            "technical": [
                "La arquitectura de microservicios permite construir aplicaciones como una colección de servicios pequeños e independientes. Cada servicio implementa una funcionalidad específica y se comunica con otros servicios a través de APIs bien definidas. Esta arquitectura facilita el escalado, el mantenimiento y el despliegue independiente de componentes.",
                "Los contenedores Docker proporcionan un entorno de ejecución ligero y portable para aplicaciones. Utilizan el kernel del sistema operativo host pero aíslan completamente el sistema de archivos, la red y otros recursos. Esto permite ejecutar aplicaciones de manera consistente en diferentes entornos.",
                "El aprendizaje profundo utiliza redes neuronales con múltiples capas para resolver problemas complejos. Las redes convolucionales (CNN) son especialmente efectivas en visión por computadora, mientras que las redes recurrentes (RNN) y transformers son ideales para procesamiento de secuencias.",
                "La ingeniería de datos implica el diseño y construcción de sistemas para recopilar, almacenar y analizar grandes volúmenes de datos. Incluye ETL (Extract, Transform, Load), modelado de datos, optimización de consultas y garantía de calidad de datos.",
                "La seguridad en la nube requiere múltiples capas de protección: autenticación multifactor, encriptación de datos en tránsito y en reposo, control de acceso basado en roles, monitoreo continuo y cumplimiento de estándares regulatorios."
            ],
            "code": [
                "def train_federated_model(self, global_weights, local_epochs=3):\n    '''\n    Entrena el modelo localmente con pesos globales iniciales.\n    \n    Args:\n        global_weights: Pesos del modelo global\n        local_epochs: Número de epochs locales\n    \n    Returns:\n        dict: Pesos actualizados y métricas\n    '''\n    self.model.load_state_dict(global_weights)\n    self.model.train()\n    \n    for epoch in range(local_epochs):\n        for batch in self.train_loader:\n            self.optimizer.zero_grad()\n            outputs = self.model(batch['input_ids'])\n            loss = self.criterion(outputs, batch['labels'])\n            loss.backward()\n            self.optimizer.step()\n    \n    return {\n        'weights': self.model.state_dict(),\n        'accuracy': self.evaluate_accuracy(),\n        'loss': loss.item()\n    }",
                "class FederatedCoordinator:\n    '''\n    Coordinador central para entrenamiento federado.\n    Gestiona sesiones, nodos y agregación de pesos.\n    '''\n    \n    def __init__(self, config):\n        self.config = config\n        self.active_sessions = {}\n        self.node_registry = {}\n        \n    async def create_session(self, model_config):\n        session_id = str(uuid.uuid4())\n        self.active_sessions[session_id] = {\n            'model_config': model_config,\n            'nodes': [],\n            'start_time': time.time(),\n            'status': 'waiting_for_nodes'\n        }\n        return session_id\n        \n    def aggregate_weights(self, node_weights):\n        '''Agrega pesos usando algoritmo FedAvg.'''\n        aggregated = {}\n        for key in node_weights[0].keys():\n            tensors = [w[key] for w in node_weights]\n            aggregated[key] = torch.stack(tensors).mean(dim=0)\n        return aggregated",
                "import torch\nimport torch.nn as nn\nimport torch.optim as optim\nfrom torch.utils.data import DataLoader, Dataset\n\nclass EmpoorioLM(nn.Module):\n    '''\n    Modelo de lenguaje transformer optimizado para federated learning.\n    '''\n    \n    def __init__(self, config):\n        super().__init__()\n        self.config = config\n        \n        # Embeddings\n        self.word_embeddings = nn.Embedding(config.vocab_size, config.hidden_size)\n        self.position_embeddings = nn.Embedding(config.max_position_embeddings, config.hidden_size)\n        \n        # Transformer blocks\n        self.blocks = nn.ModuleList([\n            TransformerBlock(config) for _ in range(config.num_hidden_layers)\n        ])\n        \n        # Language modeling head\n        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size)\n        \n    def forward(self, input_ids, attention_mask=None):\n        # Embedding + positional encoding\n        embeddings = self.word_embeddings(input_ids) + self.position_embeddings(torch.arange(input_ids.size(1)))\n        \n        # Apply transformer blocks\n        hidden_states = embeddings\n        for block in self.blocks:\n            hidden_states = block(hidden_states, attention_mask)\n            \n        # Language modeling\n        logits = self.lm_head(hidden_states)\n        return {'logits': logits, 'hidden_states': hidden_states}"
            ],
            "books": [
                "En el vasto universo de la literatura, cada página representa una puerta hacia mundos desconocidos. Los libros no son meros objetos inanimados, sino compañeros de viaje que nos transportan a través del tiempo y el espacio. Desde las antiguas epopeyas sumerias hasta las novelas contemporáneas, la escritura ha sido el vehículo principal para preservar el conocimiento humano, las emociones y las experiencias colectivas.",
                "La filosofía de la ciencia moderna comenzó con la revolución copernicana, cuando Nicolás Copérnico propuso que la Tierra no era el centro del universo. Esta idea revolucionaria, desarrollada posteriormente por Galileo Galilei y Johannes Kepler, sentó las bases para el método científico experimental. Francis Bacon y René Descartes contribuyeron con sus respectivos métodos inductivo y deductivo, estableciendo las bases epistemológicas de la investigación científica.",
                "La historia de la humanidad puede verse como una progresión desde la ignorancia hacia el conocimiento, desde la superstición hacia la razón. Cada generación construye sobre los hombros de la anterior, incorporando nuevas tecnologías, nuevos conocimientos y nuevas formas de entender el mundo. Sin embargo, este progreso no ha sido lineal ni uniforme; ha estado marcado por retrocesos, conflictos y momentos de iluminación colectiva.",
                "El arte contemporáneo desafía las convenciones tradicionales, explorando nuevos medios y formas de expresión. Desde las instalaciones multimedia hasta el arte digital, los artistas modernos buscan cuestionar nuestras percepciones del mundo, desafiar las normas sociales y explorar los límites de la creatividad humana. El arte ya no se limita a los museos y galerías; se ha convertido en una experiencia interactiva y participativa.",
                "La psicología cognitiva ha revolucionado nuestra comprensión de cómo funciona la mente humana. Desde los experimentos de memoria de Hermann Ebbinghaus hasta las teorías de procesamiento de información de Ulric Neisser, hemos aprendido que el pensamiento no es un proceso pasivo, sino una actividad constructiva que implica la manipulación activa de información simbólica."
            ],
            "news": [
                "La Unión Europea ha anunciado un paquete de medidas sin precedentes para combatir el cambio climático, con inversiones de 500 mil millones de euros destinadas a energías renovables y eficiencia energética. El plan incluye objetivos ambiciosos de reducción de emisiones para 2030 y 2050, con el objetivo de convertir a Europa en el primer continente climáticamente neutro del mundo.",
                "Los avances en inteligencia artificial están transformando la industria automotriz, con vehículos autónomos que prometen revolucionar el transporte urbano. Empresas como Tesla, Waymo y Baidu están invirtiendo miles de millones en el desarrollo de sistemas de conducción automatizada, que combinan sensores avanzados, aprendizaje profundo y algoritmos de toma de decisiones en tiempo real.",
                "El sector de la salud digital está experimentando un crecimiento exponencial, impulsado por la pandemia de COVID-19. Las teleconsultas, las aplicaciones de monitoreo remoto y los sistemas de diagnóstico asistido por IA están mejorando el acceso a la atención médica, especialmente en áreas rurales y países en desarrollo. Sin embargo, estos avances también plantean desafíos éticos y de privacidad.",
                "La exploración espacial comercial está entrando en una nueva era, con empresas privadas compitiendo con agencias gubernamentales. SpaceX ha demostrado la viabilidad de reutilizar cohetes, reduciendo drásticamente los costos de lanzamiento. Mientras tanto, Blue Origin y Virgin Galactic se centran en el turismo espacial, abriendo nuevas oportunidades económicas.",
                "La transformación digital de las empresas tradicionales está acelerándose, impulsada por la necesidad de adaptarse a un entorno económico volátil. Las tecnologías emergentes como blockchain, IoT y realidad aumentada están creando nuevas oportunidades de negocio, pero también requieren una reevaluación fundamental de los modelos operativos y las estrategias de recursos humanos."
            ],
            "social": [
                "¡Increíble cómo la tecnología está cambiando nuestras vidas! Hoy mismo pude hablar con mi familia al otro lado del mundo sin costo alguno gracias a internet. ¿Qué opinan ustedes sobre cómo el acceso a la información global está democratizando el conocimiento? #Tecnología #Conectividad",
                "Reflexionando sobre el futuro del trabajo: con la automatización y la IA avanzando tan rápido, ¿qué habilidades serán más valiosas en los próximos años? Creo que la creatividad, el pensamiento crítico y la capacidad de adaptación serán clave. ¿Están preparados para este cambio? #FuturoDelTrabajo #IA",
                "¡Qué maravilla de día! Salí a caminar por el parque y pude observar cómo la naturaleza sigue su ciclo perfecto. En medio del caos urbano, estos momentos de conexión con lo natural nos recuerdan lo importante que es preservar nuestro planeta. ¿Cuál es su lugar favorito para reconectar con la naturaleza? #Naturaleza #Bienestar",
                "Compartiendo mi experiencia con el aprendizaje online durante la pandemia. Las plataformas educativas han hecho posible que miles de personas continúen formándose desde casa. Sin embargo, echo de menos la interacción personal en el aula. ¿Cómo creen que evolucionará la educación en el futuro? #Educación #AprendizajeOnline",
                "Celebrando los pequeños logros diarios: hoy terminé un proyecto que había estado postergando por semanas. Me recuerda que la consistencia y la perseverancia son más importantes que el talento innato. ¿Cuál ha sido su mayor logro reciente? ¡Felicitaciones por adelantado! #Motivación #Logros"
            ]
        }

    def generate_sample(self, dataset_type: DatasetType, config: DatasetConfig) -> Dict[str, Any]:
        """Genera una muestra individual de dataset."""
        templates = self.templates[dataset_type.value]

        # Seleccionar template base
        base_text = random.choice(templates)

        # Generar variaciones
        if dataset_type == DatasetType.WIKIPEDIA_ARTICLES:
            sample = self._generate_wikipedia_article(base_text, config)
        elif dataset_type == DatasetType.TECHNICAL_DOCS:
            sample = self._generate_technical_doc(base_text, config)
        elif dataset_type == DatasetType.CODE_REPOSITORIES:
            sample = self._generate_code_sample(base_text, config)
        elif dataset_type == DatasetType.BOOKS_TEXTS:
            sample = self._generate_book_text(base_text, config)
        elif dataset_type == DatasetType.NEWS_ARTICLES:
            sample = self._generate_news_article(base_text, config)
        elif dataset_type == DatasetType.SOCIAL_MEDIA:
            sample = self._generate_social_post(base_text, config)
        else:
            sample = self._generate_generic_text(base_text, config)

        return sample

    def _generate_wikipedia_article(self, base_text: str, config: DatasetConfig) -> Dict[str, Any]:
        """Genera artículo estilo Wikipedia."""
        titles = [
            "Inteligencia Artificial", "Aprendizaje Federado", "Computación en la Nube",
            "Procesamiento de Lenguaje Natural", "Blockchain", "Criptografía",
            "Aprendizaje Profundo", "Redes Neuronales", "Big Data", "Machine Learning"
        ]

        title = random.choice(titles)
        content = base_text

        # Añadir secciones
        sections = ["Introducción", "Historia", "Aplicaciones", "Desafíos", "Futuro"]
        for section in random.sample(sections, random.randint(2, 4)):
            content += f"\n\n{section}\n" + ".".join(base_text.split(".")[:2]) + "."

        return {
            "title": title,
            "content": content,
            "language": config.language,
            "category": "encyclopedia",
            "word_count": len(content.split()),
            "source": "wikipedia_synthetic",
            "quality_score": random.uniform(0.85, 0.95)
        }

    def _generate_technical_doc(self, base_text: str, config: DatasetConfig) -> Dict[str, Any]:
        """Genera documentación técnica."""
        topics = [
            "Arquitectura de Microservicios", "Contenedores Docker", "Aprendizaje Profundo",
            "Ingeniería de Datos", "Seguridad en la Nube", "DevOps", "CI/CD",
            "APIs RESTful", "Bases de Datos Distribuidas", "Monitoreo y Logging"
        ]

        topic = random.choice(topics)
        content = base_text

        # Añadir elementos técnicos
        technical_terms = ["API", "microservicios", "contenedores", "orquestación", "escalabilidad"]
        for term in random.sample(technical_terms, random.randint(2, 4)):
            content += f" La implementación de {term} requiere consideraciones específicas de diseño y arquitectura."

        return {
            "title": f"Guía de {topic}",
            "content": content,
            "language": config.language,
            "category": "technical",
            "difficulty": random.choice(["beginner", "intermediate", "advanced"]),
            "word_count": len(content.split()),
            "source": "technical_docs_synthetic",
            "quality_score": random.uniform(0.90, 0.98)
        }

    def _generate_code_sample(self, base_text: str, config: DatasetConfig) -> Dict[str, Any]:
        """Genera muestra de código con documentación."""
        languages = ["python", "javascript", "typescript", "java", "go", "rust"]
        frameworks = ["tensorflow", "pytorch", "react", "django", "spring", "fastapi"]

        language = random.choice(languages)
        framework = random.choice(frameworks)

        # El base_text ya contiene código, añadir documentación
        documentation = f"Este código demuestra el uso de {framework} en {language} para implementar funcionalidades avanzadas. Incluye manejo de errores, logging y optimizaciones de rendimiento."

        return {
            "title": f"Ejemplo de {framework} en {language}",
            "code": base_text,
            "documentation": documentation,
            "language": language,
            "framework": framework,
            "category": "code",
            "complexity": random.choice(["simple", "medium", "complex"]),
            "word_count": len((base_text + documentation).split()),
            "source": "code_repository_synthetic",
            "quality_score": random.uniform(0.88, 0.96)
        }

    def _generate_book_text(self, base_text: str, config: DatasetConfig) -> Dict[str, Any]:
        """Genera texto estilo libro."""
        genres = ["filosofía", "ciencia", "historia", "literatura", "psicología"]
        authors = ["Aristóteles", "Platón", "Descartes", "Kant", "Nietzsche", "Sartre"]

        genre = random.choice(genres)
        author = random.choice(authors)

        return {
            "title": f"Reflexiones sobre {genre.title()}",
            "content": base_text,
            "author": author,
            "genre": genre,
            "language": config.language,
            "category": "literature",
            "word_count": len(base_text.split()),
            "source": "book_text_synthetic",
            "quality_score": random.uniform(0.82, 0.94)
        }

    def _generate_news_article(self, base_text: str, config: DatasetConfig) -> Dict[str, Any]:
        """Genera artículo de noticias."""
        topics = ["tecnología", "ciencia", "economía", "medio ambiente", "salud", "política"]
        sources = ["El País", "BBC News", "Reuters", "CNN", "The Guardian", "New York Times"]

        topic = random.choice(topics)
        source = random.choice(sources)

        return {
            "title": f"Avances en {topic.title()}: Nuevos descubrimientos transforman el sector",
            "content": base_text,
            "topic": topic,
            "source": source,
            "language": config.language,
            "category": "news",
            "word_count": len(base_text.split()),
            "publication_date": "2024-11-06",
            "quality_score": random.uniform(0.87, 0.93)
        }

    def _generate_social_post(self, base_text: str, config: DatasetConfig) -> Dict[str, Any]:
        """Genera post de redes sociales."""
        platforms = ["twitter", "facebook", "instagram", "linkedin", "tiktok"]
        sentiments = ["positive", "neutral", "negative", "enthusiastic", "reflective"]

        platform = random.choice(platforms)
        sentiment = random.choice(sentiments)

        return {
            "content": base_text,
            "platform": platform,
            "sentiment": sentiment,
            "language": config.language,
            "category": "social_media",
            "hashtags": ["#Tecnología", "#IA", "#Innovación", "#Futuro"],
            "word_count": len(base_text.split()),
            "source": "social_media_synthetic",
            "quality_score": random.uniform(0.75, 0.89)
        }

    def _generate_generic_text(self, base_text: str, config: DatasetConfig) -> Dict[str, Any]:
        """Genera texto genérico."""
        return {
            "content": base_text,
            "language": config.language,
            "category": "general",
            "word_count": len(base_text.split()),
            "source": "generic_synthetic",
            "quality_score": random.uniform(0.80, 0.90)
        }

    def generate_dataset(
        self,
        config: DatasetConfig,
        output_file: str = None,
        batch_size: int = 1000
    ) -> str:
        """
        Genera un dataset completo.

        Args:
            config: Configuración del dataset
            output_file: Archivo de salida (opcional)
            batch_size: Tamaño de batch para escritura

        Returns:
            Ruta del archivo generado
        """
        if output_file is None:
            timestamp = int(time.time())
            output_file = f"{config.dataset_type.value}_{config.num_samples}_{timestamp}.jsonl"

        output_path = self.output_dir / output_file

        start_time = time.time()
        samples_generated = 0

        print(f"🚀 Generando dataset {config.dataset_type.value} con {config.num_samples} muestras...")

        with open(output_path, 'w', encoding='utf-8') as f:
            batch = []

            for i in range(config.num_samples):
                # Generar muestra
                sample = self.generate_sample(config.dataset_type, config)
                batch.append(sample)
                samples_generated += 1

                # Escribir en batches
                if len(batch) >= batch_size:
                    for item in batch:
                        json.dump(item, f, ensure_ascii=False)
                        f.write('\n')
                    batch = []

                    # Progreso
                    progress = (samples_generated / config.num_samples) * 100
                    print(f"   📊 Progreso: {progress:.1f}%")
                # Último batch
                for item in batch:
                    json.dump(item, f, ensure_ascii=False)
                    f.write('\n')

        generation_time = time.time() - start_time

        # Estadísticas
        total_tokens = sum(len(sample.get('content', '').split()) for sample in batch)

        dataset_info = {
            "dataset_type": config.dataset_type.value,
            "num_samples": config.num_samples,
            "output_file": str(output_path),
            "generation_time": generation_time,
            "samples_per_second": config.num_samples / generation_time,
            "total_tokens": total_tokens,
            "config": {
                "language": config.language,
                "quality_level": config.quality_level,
                "min_length": config.min_length,
                "max_length": config.max_length
            }
        }

        # Guardar metadatos
        metadata_file = output_path.with_suffix('.metadata.json')
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(dataset_info, f, indent=2, ensure_ascii=False)

        # Actualizar estadísticas globales
        self.stats["total_samples"] += config.num_samples
        self.stats["total_tokens"] += total_tokens
        self.stats["generation_time"] += generation_time
        self.stats["datasets_created"].append(dataset_info)

        print("✅ Dataset generado exitosamente:")
        print(f"   📁 Archivo: {output_path}")
        print(f"   📊 Muestras: {config.num_samples}")
        print(f"   ⏱️ Tiempo: {generation_time:.2f}s")
        print(f"   📈 Velocidad: {config.num_samples/generation_time:.1f} muestras/s")

        return str(output_path)

    def generate_massive_dataset_suite(self, target_size_gb: float = 1.0) -> List[str]:
        """
        Genera una suite completa de datasets masivos.

        Args:
            target_size_gb: Tamaño objetivo total en GB

        Returns:
            Lista de archivos generados
        """
        print(f"🎯 Generando suite de datasets masivos ({target_size_gb}GB objetivo)...")

        # Calcular distribución por tipo
        dataset_configs = [
            DatasetConfig(DatasetType.WIKIPEDIA_ARTICLES, num_samples=15000),
            DatasetConfig(DatasetType.TECHNICAL_DOCS, num_samples=12000),
            DatasetConfig(DatasetType.CODE_REPOSITORIES, num_samples=8000),
            DatasetConfig(DatasetType.BOOKS_TEXTS, num_samples=10000),
            DatasetConfig(DatasetType.NEWS_ARTICLES, num_samples=13000),
            DatasetConfig(DatasetType.SOCIAL_MEDIA, num_samples=20000)
        ]

        generated_files = []

        for config in dataset_configs:
            file_path = self.generate_dataset(config)
            generated_files.append(file_path)

        # Verificar tamaño total
        total_size = sum(Path(f).stat().st_size for f in generated_files) / (1024**3)  # GB

        print("\n📊 SUITE COMPLETA GENERADA:")
        print(f"   📁 Datasets: {len(generated_files)}")
        print(f"   💾 Tamaño total: {total_size:.2f}GB")
        print(f"   📈 Eficiencia: {total_size/target_size_gb*100:.1f}% del objetivo")
        return generated_files

    def save_stats(self):
        """Guarda estadísticas de generación."""
        stats_file = self.output_dir / "generation_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, default=str)


# Funciones de conveniencia
def generate_wikipedia_dataset(num_samples: int = 10000) -> str:
    """Genera dataset de artículos Wikipedia."""
    generator = MassiveDatasetGenerator()
    config = DatasetConfig(DatasetType.WIKIPEDIA_ARTICLES, num_samples=num_samples)
    return generator.generate_dataset(config)


def generate_technical_dataset(num_samples: int = 8000) -> str:
    """Genera dataset de documentación técnica."""
    generator = MassiveDatasetGenerator()
    config = DatasetConfig(DatasetType.TECHNICAL_DOCS, num_samples=num_samples)
    return generator.generate_dataset(config)


def generate_massive_suite(target_gb: float = 1.0) -> List[str]:
    """Genera suite completa de datasets masivos."""
    generator = MassiveDatasetGenerator()
    return generator.generate_massive_dataset_suite(target_gb)


if __name__ == "__main__":
    # Demo de generación
    print("🧪 DEMO: Generador de Datasets Masivos para AILOOS")
    print("=" * 60)

    generator = MassiveDatasetGenerator()

    # Generar dataset pequeño para demo
    print("\n1️⃣ Generando dataset de prueba (Wikipedia)...")
    config = DatasetConfig(DatasetType.WIKIPEDIA_ARTICLES, num_samples=100)
    wiki_file = generator.generate_dataset(config)

    print("\n2️⃣ Generando dataset técnico...")
    config = DatasetConfig(DatasetType.TECHNICAL_DOCS, num_samples=50)
    tech_file = generator.generate_dataset(config)

    print("\n3️⃣ Generando muestra de código...")
    config = DatasetConfig(DatasetType.CODE_REPOSITORIES, num_samples=25)
    code_file = generator.generate_dataset(config)

    # Mostrar estadísticas
    print("\n📊 ESTADÍSTICAS FINALES:")
    print(f"   📁 Datasets generados: {len(generator.stats['datasets_created'])}")
    print(f"   📊 Muestras totales: {generator.stats['total_samples']}")
    print(f"   📝 Tokens totales: {generator.stats['total_tokens']}")
    print(f"   ⏱️ Tiempo total: {generator.stats['generation_time']:.2f}s")
    print("\n✅ ¡Generación completada! Los datasets están listos para entrenamiento federado.")
    print(f"📂 Ubicación: {generator.output_dir}")

    # Guardar estadísticas
    generator.save_stats()