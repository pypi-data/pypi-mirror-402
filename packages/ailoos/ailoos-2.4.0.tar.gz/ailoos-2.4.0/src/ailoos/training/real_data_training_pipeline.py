"""
Real Data Training Pipeline para EmpoorioLM - FASE REAL-5
Pipeline completo de datos reales para entrenamiento de EmpoorioLM.
Integra todos los componentes: carga, preprocessing, sharding, validación y DataLoader.
"""

import os
import logging
import time
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json

from datasets import Dataset
from torch.utils.data import DataLoader

# Importar componentes del pipeline
from .real_data_pipeline import RealDataPipeline, DataPipelineConfig
from .data_preprocessing import DataPreprocessor, PreprocessingConfig
from .dataset_sharding import FederatedDatasetSharder, ShardingConfig, DatasetShard
from .data_quality_validation import DataQualityValidator, QualityValidationConfig
from .efficient_data_loader import EfficientDataLoader, DataLoaderConfig

logger = logging.getLogger(__name__)


@dataclass
class RealTrainingPipelineConfig:
    """Configuración completa del pipeline de entrenamiento real."""
    # Pipeline de datos
    datasets: List[str] = field(default_factory=lambda: ["wikitext", "openwebtext"])
    cache_dir: str = "./data_cache"
    max_samples_per_dataset: Optional[int] = None

    # Preprocessing
    max_length: int = 512
    tokenizer_path: Optional[str] = None
    clean_text: bool = True

    # Sharding
    num_shards: int = 10
    shard_dir: str = "./federated_shards"
    validation_split: float = 0.1
    test_split: float = 0.05

    # DataLoader
    batch_size: int = 8
    num_workers: int = 4
    distributed: bool = False
    world_size: int = 1
    rank: int = 0

    # Validación
    enable_quality_validation: bool = True
    quality_sample_size: int = 10000

    # Output
    output_dir: str = "./real_training_data"
    save_intermediates: bool = True


class RealDataTrainingPipeline:
    """
    Pipeline completo para datos reales de entrenamiento de EmpoorioLM.
    Maneja todo el flujo desde carga de datasets hasta DataLoader listo para entrenamiento.
    """

    def __init__(self, config: RealTrainingPipelineConfig):
        self.config = config
        self.components = {}

        # Crear directorios
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config.cache_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config.shard_dir).mkdir(parents=True, exist_ok=True)

        logger.info("🚀 RealDataTrainingPipeline inicializado")
        logger.info(f"   Output dir: {self.config.output_dir}")
        logger.info(f"   Datasets: {self.config.datasets}")

    def run_full_pipeline(self) -> Dict[str, Any]:
        """
        Ejecutar pipeline completo.
        Returns:
            Dict con resultados y estadísticas
        """
        start_time = time.time()
        results = {
            "success": False,
            "stages": {},
            "statistics": {},
            "artifacts": {}
        }

        try:
            # Etapa 1: Cargar datasets
            logger.info("📥 Etapa 1: Cargando datasets reales...")
            stage_result = self._run_data_loading()
            results["stages"]["data_loading"] = stage_result

            if not stage_result["success"]:
                raise Exception("Error en carga de datos")

            # Etapa 2: Preprocesamiento
            logger.info("🔧 Etapa 2: Preprocesamiento de datos...")
            stage_result = self._run_preprocessing()
            results["stages"]["preprocessing"] = stage_result

            if not stage_result["success"]:
                raise Exception("Error en preprocesamiento")

            # Etapa 3: Validación de calidad
            if self.config.enable_quality_validation:
                logger.info("🔍 Etapa 3: Validación de calidad...")
                stage_result = self._run_quality_validation()
                results["stages"]["quality_validation"] = stage_result

            # Etapa 4: Sharding federado
            logger.info("🔀 Etapa 4: Sharding federado...")
            stage_result = self._run_sharding()
            results["stages"]["sharding"] = stage_result

            if not stage_result["success"]:
                raise Exception("Error en sharding")

            # Etapa 5: Crear DataLoader
            logger.info("⚡ Etapa 5: Creando DataLoader eficiente...")
            stage_result = self._run_dataloader_creation()
            results["stages"]["dataloader"] = stage_result

            if not stage_result["success"]:
                raise Exception("Error en creación de DataLoader")

            # Estadísticas finales
            results["statistics"] = self._collect_final_statistics()
            results["artifacts"] = self._collect_artifacts()
            results["success"] = True

            total_time = time.time() - start_time
            logger.info("✅ Pipeline completado exitosamente")
            logger.info(f"   Tiempo total: {total_time:.2f}s")
            logger.info(f"   Artifacts generados: {len(results['artifacts'])}")

        except Exception as e:
            logger.error(f"❌ Error en pipeline: {e}")
            results["error"] = str(e)

        # Guardar reporte
        self._save_pipeline_report(results)

        return results

    def _run_data_loading(self) -> Dict[str, Any]:
        """Ejecutar carga de datasets."""
        try:
            # Configurar pipeline de datos
            pipeline_config = DataPipelineConfig(
                datasets=self.config.datasets,
                cache_dir=self.config.cache_dir,
                max_samples_per_dataset=self.config.max_samples_per_dataset
            )

            pipeline = RealDataPipeline(pipeline_config)
            self.components["data_pipeline"] = pipeline

            # Cargar datasets
            datasets = pipeline.load_datasets()

            # Combinar
            combined_dataset = pipeline.combine_datasets()

            # Guardar si configurado
            if self.config.save_intermediates:
                output_path = Path(self.config.output_dir) / "raw_combined_dataset.parquet"
                pipeline.save_dataset(str(output_path))

            return {
                "success": True,
                "datasets_loaded": len(datasets),
                "total_samples": len(combined_dataset),
                "dataset_info": pipeline.get_dataset_info()
            }

        except Exception as e:
            logger.error(f"Error en carga de datos: {e}")
            return {"success": False, "error": str(e)}

    def _run_preprocessing(self) -> Dict[str, Any]:
        """Ejecutar preprocesamiento."""
        try:
            pipeline = self.components.get("data_pipeline")
            if not pipeline or not pipeline.combined_dataset:
                raise ValueError("Dataset no disponible para preprocesamiento")

            # Configurar preprocesador
            preprocessing_config = PreprocessingConfig(
                max_length=self.config.max_length,
                tokenizer_path=self.config.tokenizer_path,
                clean_text=self.config.clean_text
            )

            preprocessor = DataPreprocessor(preprocessing_config)
            self.components["preprocessor"] = preprocessor

            # Preprocesar
            processed_dataset = preprocessor.preprocess_dataset(pipeline.combined_dataset)
            self.components["processed_dataset"] = processed_dataset

            # Estadísticas
            stats = preprocessor.get_preprocessing_stats(processed_dataset)

            # Guardar si configurado
            if self.config.save_intermediates:
                output_path = Path(self.config.output_dir) / "processed_dataset"
                processed_dataset.save_to_disk(str(output_path))

            return {
                "success": True,
                "processed_samples": len(processed_dataset),
                "statistics": stats
            }

        except Exception as e:
            logger.error(f"Error en preprocesamiento: {e}")
            return {"success": False, "error": str(e)}

    def _run_quality_validation(self) -> Dict[str, Any]:
        """Ejecutar validación de calidad."""
        try:
            dataset = self.components.get("processed_dataset")
            if not dataset:
                dataset = self.components["data_pipeline"].combined_dataset

            # Configurar validador
            validation_config = QualityValidationConfig(
                sample_size=self.config.quality_sample_size
            )

            validator = DataQualityValidator(validation_config)
            self.components["quality_validator"] = validator

            # Validar
            metrics = validator.validate_dataset(dataset)

            # Detectar anomalías
            anomalies = validator.detect_anomalies(dataset)

            # Guardar reporte
            if self.config.save_intermediates:
                report_path = Path(self.config.output_dir) / "quality_report.json"
                import json
                with open(report_path, "w") as f:
                    json.dump({
                        "metrics": {
                            "total_samples": metrics.total_samples,
                            "valid_samples": metrics.valid_samples,
                            "quality_score": metrics.quality_score,
                            "vocab_size": metrics.vocab_size
                        },
                        "issues": metrics.issues[:50],  # Limitar
                        "anomalies": anomalies
                    }, f, indent=2)

            return {
                "success": True,
                "quality_score": metrics.quality_score,
                "valid_samples": metrics.valid_samples,
                "issues_count": len(metrics.issues),
                "anomalies_count": sum(len(v) for v in anomalies.values())
            }

        except Exception as e:
            logger.error(f"Error en validación de calidad: {e}")
            return {"success": False, "error": str(e)}

    def _run_sharding(self) -> Dict[str, Any]:
        """Ejecutar sharding federado."""
        try:
            dataset = self.components.get("processed_dataset")
            if not dataset:
                raise ValueError("Dataset procesado no disponible para sharding")

            # Configurar sharder
            sharding_config = ShardingConfig(
                num_shards=self.config.num_shards,
                shard_dir=self.config.shard_dir,
                validation_split=self.config.validation_split,
                test_split=self.config.test_split
            )

            sharder = FederatedDatasetSharder(sharding_config)
            self.components["sharder"] = sharder

            # Shardear
            shards = sharder.shard_dataset(dataset)
            self.components["shards"] = shards

            # Guardar shards
            if self.config.save_intermediates:
                sharder.save_all_shards()

            # Estadísticas
            stats = sharder.get_sharding_stats()

            return {
                "success": True,
                "num_shards": len(shards),
                "total_samples": stats["total_samples"],
                "avg_shard_size": stats["avg_shard_size"],
                "statistics": stats
            }

        except Exception as e:
            logger.error(f"Error en sharding: {e}")
            return {"success": False, "error": str(e)}

    def _run_dataloader_creation(self) -> Dict[str, Any]:
        """Crear DataLoader eficiente."""
        try:
            # Para simplificar, crear DataLoader para el primer shard
            # En producción, cada nodo federado usaría su propio shard
            shards = self.components.get("shards", [])
            if not shards:
                raise ValueError("No hay shards disponibles para DataLoader")

            # Usar primer shard como ejemplo
            sample_shard = shards[0]

            # Configurar DataLoader
            dataloader_config = DataLoaderConfig(
                batch_size=self.config.batch_size,
                max_length=self.config.max_length,
                num_workers=self.config.num_workers,
                distributed=self.config.distributed,
                world_size=self.config.world_size,
                rank=self.config.rank
            )

            # Obtener tokenizer del preprocesador
            preprocessor = self.components.get("preprocessor")
            if not preprocessor:
                raise ValueError("Preprocesador no disponible")

            # Crear DataLoader
            dataloader = EfficientDataLoader(
                sample_shard.data,
                preprocessor.tokenizer,
                dataloader_config
            )
            self.components["dataloader"] = dataloader

            # Estadísticas
            stats = dataloader.get_dataloader_stats()

            return {
                "success": True,
                "batch_size": self.config.batch_size,
                "num_batches": len(dataloader),
                "statistics": stats
            }

        except Exception as e:
            logger.error(f"Error en creación de DataLoader: {e}")
            return {"success": False, "error": str(e)}

    def _collect_final_statistics(self) -> Dict[str, Any]:
        """Recopilar estadísticas finales."""
        stats = {}

        # Dataset final
        if "processed_dataset" in self.components:
            dataset = self.components["processed_dataset"]
            stats["final_dataset_size"] = len(dataset)

        # Shards
        if "sharder" in self.components:
            shard_stats = self.components["sharder"].get_sharding_stats()
            stats["sharding"] = shard_stats

        # DataLoader
        if "dataloader" in self.components:
            loader_stats = self.components["dataloader"].get_dataloader_stats()
            stats["dataloader"] = loader_stats

        return stats

    def _collect_artifacts(self) -> Dict[str, str]:
        """Recopilar artifacts generados."""
        artifacts = {}

        base_path = Path(self.config.output_dir)

        # Verificar archivos generados
        potential_artifacts = [
            "raw_combined_dataset.parquet",
            "processed_dataset",
            "quality_report.json"
        ]

        for artifact in potential_artifacts:
            path = base_path / artifact
            if path.exists():
                artifacts[artifact] = str(path)

        # Directorio de shards
        shard_dir = Path(self.config.shard_dir)
        if shard_dir.exists():
            artifacts["shards_directory"] = str(shard_dir)

        return artifacts

    def _save_pipeline_report(self, results: Dict[str, Any]):
        """Guardar reporte del pipeline."""
        report_path = Path(self.config.output_dir) / "pipeline_report.json"

        # Añadir metadata
        results["metadata"] = {
            "config": {
                "datasets": self.config.datasets,
                "max_length": self.config.max_length,
                "batch_size": self.config.batch_size,
                "num_shards": self.config.num_shards
            },
            "timestamp": time.time(),
            "version": "FASE_REAL_5"
        }

        with open(report_path, "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"📋 Reporte del pipeline guardado en {report_path}")

    def get_training_dataloader(self, shard_id: int = 0) -> Optional[EfficientDataLoader]:
        """
        Obtener DataLoader para un shard específico (para nodos federados).
        """
        try:
            sharder = self.components.get("sharder")
            preprocessor = self.components.get("preprocessor")

            if not sharder or not preprocessor:
                logger.error("Componentes no disponibles para crear DataLoader")
                return None

            # Cargar shard
            shard = sharder.load_shard(shard_id)

            # Configurar DataLoader
            dataloader_config = DataLoaderConfig(
                batch_size=self.config.batch_size,
                max_length=self.config.max_length,
                num_workers=self.config.num_workers,
                distributed=self.config.distributed,
                world_size=self.config.world_size,
                rank=self.config.rank
            )

            # Crear DataLoader
            dataloader = EfficientDataLoader(
                shard.data,
                preprocessor.tokenizer,
                dataloader_config
            )

            return dataloader

        except Exception as e:
            logger.error(f"Error obteniendo DataLoader para shard {shard_id}: {e}")
            return None


def create_real_training_pipeline(
    datasets: List[str] = None,
    output_dir: str = "./real_training_data",
    num_shards: int = 10,
    batch_size: int = 8,
    max_length: int = 512
) -> RealDataTrainingPipeline:
    """
    Factory function para crear pipeline completo de entrenamiento real.
    """
    if datasets is None:
        datasets = ["wikitext", "openwebtext"]

    config = RealTrainingPipelineConfig(
        datasets=datasets,
        output_dir=output_dir,
        num_shards=num_shards,
        batch_size=batch_size,
        max_length=max_length
    )

    return RealDataTrainingPipeline(config)


def run_real_data_pipeline(
    datasets: List[str] = None,
    output_dir: str = "./real_training_data",
    num_shards: int = 10
) -> Dict[str, Any]:
    """
    Función de conveniencia para ejecutar pipeline completo.
    """
    pipeline = create_real_training_pipeline(
        datasets=datasets,
        output_dir=output_dir,
        num_shards=num_shards
    )

    results = pipeline.run_full_pipeline()

    if results["success"]:
        logger.info("🎉 Pipeline de datos reales completado exitosamente!")
        logger.info(f"   Datos listos para entrenamiento federado en {output_dir}")
    else:
        logger.error("❌ Pipeline falló")

    return results