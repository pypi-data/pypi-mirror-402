"""
Demo del Sistema de Feedback Loops para EmpoorioLM
==================================================

Esta demo muestra cómo utilizar el sistema completo de feedback loops
para mejorar continuamente el rendimiento de EmpoorioLM basado en
interacciones reales con usuarios.

El sistema incluye:
1. Recolección de feedback con anonimización
2. Análisis inteligente de patrones
3. Entrenamiento basado en feedback
4. Seguimiento de interacciones
5. Motor de mejora continua
6. Evaluación de calidad del feedback
"""

import asyncio
import logging
import time
from datetime import datetime

from .feedback import (
    ContinuousImprovementEngine,
    FeedbackType,
    FeedbackSource,
    FeedbackQuality
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def simulate_user_interactions(engine: ContinuousImprovementEngine):
    """
    Simula interacciones de usuario para generar datos de prueba.

    Args:
        engine: Motor de mejora continua
    """
    logger.info("🎭 Simulando interacciones de usuario...")

    # Simular diferentes tipos de interacciones
    interactions = [
        # Usuario 1 - Interacciones positivas
        {
            "query": "¿Cómo puedo mejorar mi código Python?",
            "response": "Para mejorar tu código Python, considera usar pylint para análisis estático, escribir tests unitarios, y seguir PEP 8.",
            "response_time": 1.2,
            "rating": 5,
            "comment": "Excelente respuesta, muy útil",
            "user_id": 1,
            "channel": "web"
        },
        {
            "query": "Explica qué es machine learning",
            "response": "Machine Learning es una rama de la inteligencia artificial que permite a los sistemas aprender de datos sin ser programados explícitamente.",
            "response_time": 0.8,
            "rating": 4,
            "comment": "Buena explicación pero podría ser más detallada",
            "user_id": 1,
            "channel": "web"
        },

        # Usuario 2 - Interacciones con problemas
        {
            "query": "¿Cuál es la capital de Francia?",
            "response": "La capital de Francia es París. París es una hermosa ciudad con una rica historia cultural y artística.",
            "response_time": 15.0,  # Muy lento
            "rating": 2,
            "comment": "La respuesta tardó demasiado en llegar",
            "user_id": 2,
            "channel": "mobile"
        },
        {
            "query": "Error en mi código: NameError: name 'x' is not defined",
            "response": "Parece que hay un error de NameError. Esto ocurre cuando intentas usar una variable que no ha sido definida.",
            "response_time": 2.1,
            "error_occurred": True,
            "error_type": "timeout",
            "user_id": 2,
            "channel": "api"
        },

        # Usuario 3 - Feedback constructivo
        {
            "query": "Necesito ayuda con algoritmos de ordenamiento",
            "response": "Los algoritmos de ordenamiento más comunes son bubble sort, quicksort, mergesort y heapsort. Cada uno tiene diferentes complejidades temporales.",
            "response_time": 1.8,
            "rating": 3,
            "comment": "Información correcta pero ejemplos de código ayudarían más",
            "user_id": 3,
            "channel": "web"
        },

        # Sistema - Métricas automáticas
        {
            "metric_name": "response_time",
            "value": 2.5,
            "context": {"endpoint": "/api/chat", "model_version": "v1.2"}
        },
        {
            "metric_name": "error_rate",
            "value": 0.05,
            "context": {"time_window": "1h", "error_type": "timeout"}
        },

        # Más interacciones para tener datos suficientes
        {
            "query": "¿Qué es la programación orientada a objetos?",
            "response": "La POO es un paradigma de programación que usa objetos y clases para estructurar código.",
            "response_time": 1.0,
            "rating": 4,
            "user_id": 1,
            "channel": "web"
        },
        {
            "query": "Cómo instalar Python en Windows",
            "response": "Descarga el instalador desde python.org, ejecuta como administrador, marca 'Add to PATH'.",
            "response_time": 0.9,
            "rating": 5,
            "user_id": 4,
            "channel": "mobile"
        }
    ]

    for i, interaction in enumerate(interactions):
        try:
            # Registrar interacción
            interaction_id = engine.record_user_interaction(
                user_query=interaction["query"],
                model_response=interaction["response"],
                response_time=interaction["response_time"],
                user_id=interaction.get("user_id"),
                channel=interaction.get("channel", "api"),
                error_occurred=interaction.get("error_occurred", False),
                error_type=interaction.get("error_type")
            )

            # Recopilar feedback adicional
            if "rating" in interaction:
                engine.collect_feedback(
                    feedback_type=FeedbackType.USER_RATING,
                    source=FeedbackSource.USER_DIRECT,
                    data={
                        "rating": interaction["rating"],
                        "comment": interaction.get("comment", "")
                    },
                    user_id=interaction.get("user_id")
                )

            if "metric_name" in interaction:
                engine.collect_feedback(
                    feedback_type=FeedbackType.SYSTEM_METRIC,
                    source=FeedbackSource.SYSTEM_AUTOMATIC,
                    data={
                        "metric_name": interaction["metric_name"],
                        "value": interaction["value"],
                        "context": interaction.get("context", {})
                    }
                )

            logger.info(f"✅ Interacción {i+1}/{len(interactions)} registrada (ID: {interaction_id})")

            # Pequeña pausa entre interacciones
            await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"❌ Error registrando interacción {i+1}: {e}")

    logger.info(f"🎭 Simulación completada: {len(interactions)} interacciones registradas")


async def demonstrate_feedback_analysis(engine: ContinuousImprovementEngine):
    """
    Demuestra el análisis de feedback y generación de insights.

    Args:
        engine: Motor de mejora continua
    """
    logger.info("🔍 Ejecutando análisis de feedback...")

    try:
        # Forzar un ciclo de mejora para análisis inmediato
        cycle_id = await engine.force_improvement_cycle()
        logger.info(f"🔄 Ciclo de mejora iniciado: {cycle_id}")

        # Esperar un poco para que el análisis se complete
        await asyncio.sleep(2)

        # Obtener estado del sistema
        status = engine.get_system_status()
        logger.info("📊 Estado del sistema después del análisis:")
        logger.info(f"   - Ciclo actual: {status.get('current_cycle', {}).get('status', 'none')}")
        logger.info(f"   - Feedback recopilado: {status['components_status']['feedback_collector']}")
        logger.info(f"   - Interacciones: {status['components_status']['interaction_tracker']}")

        # Mostrar estadísticas de calidad
        quality_stats = status['components_status'].get('quality_assessor', {})
        if quality_stats and quality_stats.get('total_assessed', 0) > 0:
            logger.info("⭐ Estadísticas de calidad del feedback:")
            logger.info(f"   - Total evaluado: {quality_stats['total_assessed']}")
            logger.info(".2f")
            logger.info(".2f")
            dist = quality_stats.get('quality_distribution', {})
            for quality, count in dist.items():
                logger.info(f"   - {quality}: {count}")

        # Obtener historial de mejoras
        history = engine.get_improvement_history(limit=3)
        if history:
            logger.info("📈 Historial de ciclos de mejora:")
            for cycle in history:
                improvement = cycle.get('improvement_score')
                status_cycle = cycle.get('status')
                logger.info(f"   - {cycle['cycle_id']}: {status_cycle}" +
                          (f", mejora: {improvement:.3f}" if improvement else ""))

    except Exception as e:
        logger.error(f"❌ Error en análisis de feedback: {e}")


async def demonstrate_continuous_improvement(engine: ContinuousImprovementEngine):
    """
    Demuestra el funcionamiento del motor de mejora continua.

    Args:
        engine: Motor de mejora continua
    """
    logger.info("🚀 Iniciando demostración de mejora continua...")

    try:
        # Iniciar el motor de mejora continua (solo por unos segundos para demo)
        improvement_task = asyncio.create_task(engine.start_continuous_improvement())

        # Dejar que corra por 10 segundos
        logger.info("⏱️  Motor ejecutándose por 10 segundos...")
        await asyncio.sleep(10)

        # Detener el motor
        engine.stop_continuous_improvement()
        await improvement_task

        logger.info("✅ Demostración de mejora continua completada")

    except Exception as e:
        logger.error(f"❌ Error en mejora continua: {e}")


async def show_system_capabilities(engine: ContinuousImprovementEngine):
    """
    Muestra las capacidades del sistema de feedback loops.

    Args:
        engine: Motor de mejora continua
    """
    logger.info("🎯 Capacidades del Sistema de Feedback Loops:")
    logger.info("=" * 60)

    # 1. Anonimización de datos
    logger.info("1. 🔒 Anonimización de Privacidad:")
    logger.info("   - Datos personales hasheados automáticamente")
    logger.info("   - Información sensible protegida por defecto")
    logger.info("   - Cumplimiento con regulaciones de privacidad")

    # 2. Análisis inteligente
    logger.info("2. 🧠 Análisis Inteligente:")
    logger.info("   - Detección automática de patrones en feedback")
    logger.info("   - Identificación de problemas recurrentes")
    logger.info("   - Análisis de sentimiento y tendencias temporales")

    # 3. Entrenamiento adaptativo
    logger.info("3. 🎓 Entrenamiento Basado en Feedback:")
    logger.info("   - Generación automática de datos de entrenamiento")
    logger.info("   - Re-entrenamiento selectivo del modelo")
    logger.info("   - Integración con aprendizaje federado")

    # 4. Evaluación de calidad
    logger.info("4. ⭐ Evaluación de Calidad:")
    logger.info("   - Puntuación automática de confiabilidad del feedback")
    logger.info("   - Filtrado de contenido spam o irrelevante")
    logger.info("   - Ranking de usuarios por confiabilidad")

    # 5. Mejora continua
    logger.info("5. 🔄 Mejora Continua:")
    logger.info("   - Ciclos automáticos de recopilación-análisis-mejora")
    logger.info("   - Monitoreo de métricas de rendimiento")
    logger.info("   - Adaptación proactiva a cambios en comportamiento de usuario")

    # 6. Ética y seguridad
    logger.info("6. 🛡️ Ética y Seguridad:")
    logger.info("   - Procesamiento ético de datos personales")
    logger.info("   - Prevención de sesgos en análisis")
    logger.info("   - Transparencia en decisiones de mejora")

    logger.info("")
    logger.info("📊 Estado Actual del Sistema:")
    status = engine.get_system_status()
    logger.info(f"   - Motor activo: {status['is_running']}")
    logger.info(f"   - Feedback total: {status['components_status']['feedback_collector']}")
    logger.info(f"   - Interacciones: {status['components_status']['interaction_tracker']}")
    logger.info(f"   - Insights generados: {status['components_status']['feedback_analyzer']}")


async def run_feedback_loops_demo():
    """
    Ejecuta la demostración completa del sistema de feedback loops.
    """
    print("🤖 AILOOS - DEMO SISTEMA DE FEEDBACK LOOPS")
    print("=" * 60)
    print("Esta demo muestra cómo el sistema de feedback loops")
    print("puede aprender y mejorar EmpoorioLM basado en interacciones reales.")
    print("")

    # Inicializar el motor de mejora continua
    engine = ContinuousImprovementEngine()

    try:
        # Fase 1: Simular interacciones de usuario
        print("\n📝 FASE 1: Simulando interacciones de usuario")
        print("-" * 50)
        await simulate_user_interactions(engine)

        # Fase 2: Demostrar análisis de feedback
        print("\n📊 FASE 2: Análisis de feedback")
        print("-" * 50)
        await demonstrate_feedback_analysis(engine)

        # Fase 3: Mostrar capacidades del sistema
        print("\n🎯 FASE 3: Capacidades del sistema")
        print("-" * 50)
        await show_system_capabilities(engine)

        # Fase 4: Demostración de mejora continua (opcional - requiere coordinador)
        print("\n🚀 FASE 4: Demostración de mejora continua")
        print("-" * 50)
        print("Nota: Esta fase requiere un coordinador federado ejecutándose.")
        print("Se omite en esta demo para evitar dependencias externas.")
        # await demonstrate_continuous_improvement(engine)

        # Fase 5: Exportar resultados
        print("\n💾 FASE 5: Exportando resultados")
        print("-" * 50)
        engine.export_system_data("demo_feedback_loops")
        print("✅ Datos exportados a archivos 'demo_feedback_loops_*'")

        print("\n🎉 DEMO COMPLETADA EXITOSAMENTE!")
        print("=" * 60)
        print("El sistema de feedback loops está listo para:")
        print("• Recopilar feedback de usuarios reales")
        print("• Analizar patrones y generar insights")
        print("• Mejorar continuamente el rendimiento de EmpoorioLM")
        print("• Mantener la privacidad y ética en todo momento")

    except Exception as e:
        logger.error(f"❌ Error en la demo: {e}")
        print(f"\n❌ Error durante la ejecución: {e}")

    finally:
        # Limpiar recursos
        engine.stop_continuous_improvement()


if __name__ == "__main__":
    # Ejecutar la demo
    asyncio.run(run_feedback_loops_demo())