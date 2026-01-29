#!/usr/bin/env python3
"""
Ejemplo de uso completo del Sistema de Benchmarking Automático para EmpoorioLM

Este ejemplo demuestra cómo integrar todos los componentes del sistema
de benchmarking para una evaluación completa del rendimiento del modelo.
"""

import sys
import os
from pathlib import Path

# Añadir el directorio raíz al path para importar ailoos
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ailoos.benchmarking import (
    AutomatedBenchmarkRunner,
    VersionComparator,
    PerformanceProfiler,
    BenchmarkDatasetManager,
    RegressionDetector,
    BenchmarkReporter,
    BenchmarkConfig,
    DatasetConfig,
    ReportConfig
)

def main():
    """Ejemplo completo de uso del sistema de benchmarking."""

    print("🚀 Iniciando Sistema de Benchmarking Automático para EmpoorioLM")
    print("=" * 60)

    # 1. Configurar datasets de benchmark
    print("\n📊 Configurando datasets de benchmark...")

    dataset_configs = [
        DatasetConfig(
            name="wikitext_test",
            source="huggingface",
            path="wikitext",
            subset="wikitext-2-raw-v1",
            split="test",
            num_samples=100  # Para demo - usar más en producción
        ),
        DatasetConfig(
            name="glue_sst2",
            source="huggingface",
            path="glue",
            subset="sst2",
            split="validation",
            num_samples=100
        )
    ]

    # 2. Configurar el runner de benchmarks
    print("\n🏃 Configurando AutomatedBenchmarkRunner...")

    benchmark_config = BenchmarkConfig(
        model_name="gpt2",  # Cambiar por el modelo EmpoorioLM cuando esté disponible
        datasets=["wikitext_test", "glue_sst2"],
        metrics=["perplexity", "accuracy"],
        batch_size=4,
        max_length=128,
        num_samples=50,
        seed=42
    )

    # 3. Inicializar componentes
    print("\n🔧 Inicializando componentes...")

    dataset_manager = BenchmarkDatasetManager()
    benchmark_runner = AutomatedBenchmarkRunner(benchmark_config)
    performance_profiler = PerformanceProfiler()
    version_comparator = VersionComparator()
    regression_detector = RegressionDetector()
    benchmark_reporter = BenchmarkReporter()

    # 4. Preparar datasets
    print("\n📥 Preparando datasets...")

    datasets = {}
    for config in dataset_configs:
        try:
            dataset = dataset_manager.get_dataset(config)
            datasets[config.name] = dataset
            print(f"✅ Dataset {config.name} preparado")
        except Exception as e:
            print(f"❌ Error preparando dataset {config.name}: {e}")
            continue

    # 5. Ejecutar benchmarks con perfilado
    print("\n⚡ Ejecutando benchmarks con perfilado de rendimiento...")

    performance_profiler.start_profiling("full_benchmark_run")

    try:
        results = benchmark_runner.run_benchmarks()
        print(f"✅ Benchmarks completados. {len(results)} resultados obtenidos.")
    except Exception as e:
        print(f"❌ Error ejecutando benchmarks: {e}")
        results = []

    profiling_result = performance_profiler.stop_profiling()

    # 6. Detectar regresiones
    print("\n🔍 Detectando regresiones...")

    if results:
        # Establecer baselines si no existen
        if not regression_detector.baselines:
            print("📏 Estableciendo baselines iniciales...")
            regression_detector.update_baseline_from_results()

        regression_report = regression_detector.detect_regressions(results)
        print(f"✅ Análisis de regresiones completado. {len(regression_report.alerts)} alertas detectadas.")
    else:
        regression_report = None

    # 7. Comparar versiones (simulado)
    print("\n📈 Comparando versiones...")

    # Simular comparación entre versiones
    comparison_report = None
    if len(results) > 1:
        # Crear datos simulados para comparación
        version_a_results = results[:len(results)//2]
        version_b_results = results[len(results)//2:]

        # Guardar resultados simulados para comparación
        import json
        from datetime import datetime

        # Simular archivo de resultados de versión anterior
        fake_old_results = []
        for result in version_a_results:
            fake_old_results.append({
                "metric": result.metric,
                "score": result.score * 0.95,  # Simular mejora
                "dataset": result.dataset,
                "execution_time": result.execution_time
            })

        fake_results_file = Path("benchmark_results") / "benchmark_results_v1.0.0_20231119_120000.json"
        fake_results_file.parent.mkdir(exist_ok=True)

        with open(fake_results_file, 'w') as f:
            json.dump({
                "config": benchmark_config.__dict__,
                "results": fake_old_results,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)

        comparison_report = version_comparator.compare_versions("v1.0.0", "current")
        print("✅ Comparación de versiones completada.")
    else:
        print("⚠️ No hay suficientes resultados para comparación de versiones.")

    # 8. Generar reportes
    print("\n📋 Generando reportes...")

    report_config = ReportConfig(
        title="Reporte de Benchmarking - EmpoorioLM",
        include_plots=True,
        include_tables=True,
        include_summary=True,
        output_formats=["html", "json", "markdown"]
    )

    generated_reports = benchmark_reporter.generate_report(
        config=report_config,
        results=[r.__dict__ for r in results],
        comparisons=[c.__dict__ for c in comparison_report.comparisons] if comparison_report else None,
        performance_data=profiling_result.__dict__,
        regressions=[r.__dict__ for r in regression_report.alerts] if regression_report else None
    )

    print("✅ Reportes generados:")
    for format_type, filepath in generated_reports.items():
        print(f"  - {format_type.upper()}: {filepath}")

    # 9. Resumen final
    print("\n" + "=" * 60)
    print("🎉 Sistema de Benchmarking completado exitosamente!")
    print("\n📊 Resumen:")
    print(f"  - Datasets procesados: {len(datasets)}")
    print(f"  - Benchmarks ejecutados: {len(results)}")
    print(f"  - Regresiones detectadas: {len(regression_report.alerts) if regression_report else 0}")
    print(f"  - Reportes generados: {len(generated_reports)}")
    print(f"  - Tiempo total de perfilado: {profiling_result.duration:.2f}s")
    print(f"  - CPU promedio: {profiling_result.summary['cpu_percent']['mean']:.1f}%")
    print(f"  - Memoria promedio: {profiling_result.summary['memory_percent']['mean']:.1f}%")

    if regression_report and regression_report.alerts:
        print("\n🚨 Alertas de regresión:")
        for alert in regression_report.alerts:
            print(f"  - {alert.metric}: {alert.delta_percentage:.2f}% ({alert.severity.value})")

    print(f"\n📁 Archivos generados en: benchmark_results/ y reports/")
    print("\n💡 Próximos pasos:")
    print("  - Revisar los reportes HTML para visualizaciones detalladas")
    print("  - Configurar baselines más precisas para detección de regresiones")
    print("  - Integrar con CI/CD para ejecución automática")
    print("  - Añadir más métricas y datasets específicos del dominio")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Ejecución interrumpida por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)