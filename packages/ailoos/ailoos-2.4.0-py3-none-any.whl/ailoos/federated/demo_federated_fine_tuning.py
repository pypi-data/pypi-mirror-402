#!/usr/bin/env python3
"""
Demo del Sistema de Fine-Tuning Federado para EmpoorioLM
Muestra cómo usar el sistema completo de aprendizaje federado continuo.
"""

import asyncio
import time
import torch
from typing import List

from ailoos.federated.federated_fine_tuning_system import (
    FederatedFineTuningSystem,
    FederatedFineTuningSystemConfig,
    create_federated_fine_tuning_system,
    initialize_system_with_nodes,
    run_autonomous_learning_cycle
)


async def demo_basic_federated_fine_tuning():
    """Demo básico del sistema de fine-tuning federado."""
    print("🚀 Iniciando demo del Sistema de Fine-Tuning Federado")
    print("=" * 60)

    # Configurar sistema
    config = FederatedFineTuningSystemConfig(
        session_id="demo_session_001",
        base_model_name="microsoft/DialoGPT-medium",
        enable_continuous_learning=True,
        enable_domain_adaptation=True,
        enable_precision_maintenance=True,
        enable_curriculum_learning=True,
        enable_evolution_tracking=True
    )

    # Crear sistema
    system = create_federated_fine_tuning_system(config)
    print(f"✅ Sistema creado para sesión: {config.session_id}")

    # Registrar nodos
    node_ids = ["node_001", "node_002", "node_003", "node_004", "node_005"]
    init_result = await initialize_system_with_nodes(system, node_ids)
    print(f"✅ Nodos registrados: {init_result['nodes_registered']}/{init_result['total_nodes']}")

    # Mostrar estado inicial
    status = system.get_system_status()
    print(f"📊 Estado del sistema: {status['system_status']}")
    print(f"👥 Nodos activos: {status['active_nodes']}")

    # Ejecutar fine-tuning federado con actualizaciones reales de nodos
    print("\n🎯 Ejecutando Fine-Tuning Federado...")
    ft_result = await system.initiate_federated_fine_tuning(
        dataset_name="demo_dataset",
        domain="general_conversation",
        node_updates=None  # El sistema generará actualizaciones reales de nodos
    )

    if ft_result["success"]:
        print("✅ Fine-tuning completado exitosamente")
        print(f"📦 Modelo actualizado con CID: {ft_result['result'].get('model_cid', 'N/A')}")
    else:
        print(f"❌ Error en fine-tuning: {ft_result.get('error', 'Unknown')}")

    # Ejecutar análisis de dominio
    print("\n🧠 Ejecutando Análisis de Dominio...")
    domain_result = await system.analyze_and_adapt_domains(
        source_domain="general",
        target_domain="technical",
        training_data=["This is a technical document about machine learning.",
                      "Neural networks are powerful AI models.",
                      "Federated learning preserves privacy."]
    )

    if domain_result["success"] and domain_result["adaptation_performed"]:
        print("✅ Adaptación de dominio completada")
    else:
        print("ℹ️ No se requirió adaptación de dominio")

    # Evaluar currículo
    print("\n📚 Evaluando Progreso en Currículo...")
    for node_id in node_ids[:3]:  # Evaluar primeros 3 nodos
        curriculum_result = system.evaluate_curriculum_progress(
            node_id,
            {"accuracy": 0.82, "f1_score": 0.79, "loss": 0.35}
        )
        if curriculum_result["success"]:
            progress = curriculum_result["result"]
            print(f"✅ {node_id}: Etapa {progress['current_stage']}, Progreso: {progress['stage_progress']:.1%}")

    # Mostrar métricas finales
    final_status = system.get_system_status()
    metrics = final_status["system_metrics"]
    print("\n📈 Métricas Finales:")
    print(f"   Sesiones de aprendizaje: {metrics['total_learning_sessions']}")
    print(f"   Adaptaciones realizadas: {metrics['total_adaptations']}")
    print(f"   Acciones de mantenimiento: {metrics['total_maintenance_actions']}")
    print(f"   Dominios adaptados: {metrics['domains_adapted']}")

    # Salud del sistema
    health = system.get_system_health()
    print("\n🏥 Salud del Sistema:")
    print(f"   Estado general: {health['overall_status']}")
    print(f"   Puntaje de salud: {health['overall_health']:.2%}")

    # Detener sistema
    await system.stop_system()
    print("\n🛑 Sistema detenido correctamente")


async def demo_autonomous_learning():
    """Demo de aprendizaje autónomo continuo."""
    print("\n🔄 Iniciando demo de Aprendizaje Autónomo")
    print("=" * 60)

    # Configurar sistema con aprendizaje continuo
    config = FederatedFineTuningSystemConfig(
        session_id="autonomous_session_001",
        base_model_name="microsoft/DialoGPT-medium",
        enable_continuous_learning=True,
        enable_domain_adaptation=True,
        enable_precision_maintenance=True,
        enable_curriculum_learning=True,
        enable_evolution_tracking=True,
        learning_budget_per_day=5.0  # Menos restrictivo para demo
    )

    system = create_federated_fine_tuning_system(config)

    # Inicializar con nodos
    node_ids = ["auto_node_001", "auto_node_002", "auto_node_003"]
    await initialize_system_with_nodes(system, node_ids)

    print("🚀 Ejecutando 3 ciclos de aprendizaje autónomo...")

    # Ejecutar ciclos autónomos
    cycle_result = await run_autonomous_learning_cycle(system, cycles=3)

    print(f"✅ Completados {cycle_result['cycles_completed']} ciclos autónomos")

    # Mostrar resultados de ciclos
    for i, cycle in enumerate(cycle_result['results'], 1):
        ft_success = cycle['fine_tuning']['success']
        health_status = cycle['system_health']['overall_status']
        print(f"   Ciclo {i}: FT={'✅' if ft_success else '❌'}, Salud={health_status}")

    # Estado final
    final_status = cycle_result['final_system_status']
    print("\n📊 Estado Final del Sistema Autónomo:")
    print(f"   Sesiones completadas: {final_status['system_metrics']['total_learning_sessions']}")
    print(f"   Salud del sistema: {system.get_system_health()['overall_status']}")

    await system.stop_system()


async def demo_precision_maintenance():
    """Demo de mantenimiento de precisión."""
    print("\n🛡️ Iniciando demo de Mantenimiento de Precisión")
    print("=" * 60)

    config = FederatedFineTuningSystemConfig(
        session_id="precision_session_001",
        enable_precision_maintenance=True
    )

    system = create_federated_fine_tuning_system(config)
    await initialize_system_with_nodes(system, ["precision_node_001"])

    # Simular datos de entrenamiento para mantenimiento
    training_data = [
        (torch.randn(10), torch.randint(0, 2, (1,)).float()) for _ in range(50)
    ]

    print("🔧 Aplicando mantenimiento de precisión...")

    # Aplicar destilación de conocimiento
    maintenance_result = await system.apply_precision_maintenance(
        maintenance_method="knowledge_distillation",
        training_data=training_data
    )

    if maintenance_result["success"]:
        print("✅ Mantenimiento de precisión aplicado exitosamente")
        result = maintenance_result["result"]
        print(f"   Método: {result.get('method', 'N/A')}")
        print(f"   Pérdida final: {result.get('final_loss', 'N/A')}")
    else:
        print(f"❌ Error en mantenimiento: {maintenance_result.get('error', 'Unknown')}")

    await system.stop_system()


async def main():
    """Función principal de la demo."""
    print("🤖 Demo del Sistema de Fine-Tuning Federado para EmpoorioLM")
    print("Este demo muestra las capacidades del sistema de aprendizaje automático distribuido.\n")

    try:
        # Demo básico
        await demo_basic_federated_fine_tuning()

        # Demo de aprendizaje autónomo
        await demo_autonomous_learning()

        # Demo de mantenimiento de precisión
        await demo_precision_maintenance()

        print("\n🎉 Todas las demos completadas exitosamente!")
        print("\nEl sistema de fine-tuning federado incluye:")
        print("  • Fine-tuning distribuido con LoRA")
        print("  • Adaptación automática de dominio")
        print("  • Aprendizaje continuo coordinado")
        print("  • Mantenimiento de precisión con destilación")
        print("  • Aprendizaje curriculado federado")
        print("  • Seguimiento de evolución del modelo")
        print("  • Preservación de privacidad con DP y HE")

    except Exception as e:
        print(f"\n❌ Error en la demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Ejecutar demo
    asyncio.run(main())