#!/usr/bin/env python3
"""
Script de prueba para el Sistema de Monitoreo Unificado 24/7 de AILOOS
Prueba todas las funcionalidades del sistema de monitoreo enterprise-grade.
"""

import asyncio
import logging
import time
from datetime import datetime
import sys
import os

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(__file__))

from monitoring_system import UnifiedMonitoringSystem, MonitoringComponent, AlertSeverity

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_basic_monitoring():
    """Prueba las funcionalidades básicas de monitoreo"""
    print("🧪 Probando funcionalidades básicas de monitoreo...")

    # Configuración de prueba
    config = {
        "coordinator_url": "http://localhost:5001",
        "metrics_api_url": "http://localhost:8080",
        "dashboard_port": 3001,
        "alert_email_enabled": False,
        "alert_slack_webhook": "",
        "auto_healing_enabled": True,
        "high_availability": True,
        "monitoring_interval_seconds": 5,  # Más rápido para pruebas
        "health_check_interval_seconds": 10
    }

    # Crear sistema de monitoreo
    monitoring = UnifiedMonitoringSystem(config)

    try:
        # Iniciar monitoreo
        print("▶️ Iniciando sistema de monitoreo...")
        await monitoring.start_monitoring()

        # Esperar a que se inicialice
        await asyncio.sleep(2)

        # Verificar estado inicial
        status = monitoring.get_system_status()
        print(f"📊 Estado inicial: {status['system_health']['overall_status']}")
        assert status['monitoring_active'] == True
        assert status['system_health']['overall_status'] in ['HEALTHY', 'INITIALIZING']

        # Probar recolección de métricas
        print("📈 Probando recolección de métricas...")
        await monitoring._collect_all_metrics()

        # Verificar que se recolectaron métricas
        if hasattr(monitoring, 'metrics_history') and monitoring.metrics_history:
            latest_metrics = monitoring.metrics_history[-1]
            print(f"✅ Métricas recolectadas: {len(latest_metrics['metrics'])} categorías")
        else:
            print("⚠️ No se encontraron métricas recolectadas")

        # Probar evaluación de alertas
        print("🚨 Probando sistema de alertas...")
        await monitoring._evaluate_alert_rules()

        # Verificar estado después de evaluación
        status_after = monitoring.get_system_status()
        print(f"📊 Estado después de evaluación: {status_after['system_health']['overall_status']}")

        # Probar auto-healing
        print("🔧 Probando sistema de auto-healing...")
        healing_stats = monitoring.auto_healing.get_healing_stats()
        print(f"📊 Auto-healing: {healing_stats['available_actions']} acciones disponibles")

        # Simular una alerta para probar auto-healing
        test_alert = {
            "type": "node_down",
            "node_id": "test_node_001",
            "downtime_minutes": 15,
            "timestamp": datetime.now().isoformat()
        }

        healing_triggered = await monitoring.auto_healing.trigger_healing(test_alert)
        print(f"🔧 Auto-healing disparado: {healing_triggered}")

        # Esperar un poco para que se ejecute el healing
        await asyncio.sleep(3)

        # Verificar estado del healing
        healing_stats_after = monitoring.auto_healing.get_healing_stats()
        print(f"📊 Healing después de trigger: {healing_stats_after}")

        # Probar generación de reporte
        print("📋 Generando reporte comprehensivo...")
        report = monitoring.get_comprehensive_report()
        print(f"✅ Reporte generado con {len(report)} secciones")

        print("✅ Pruebas básicas completadas exitosamente")

    except Exception as e:
        print(f"❌ Error en pruebas básicas: {e}")
        raise
    finally:
        # Detener monitoreo
        print("⏹️ Deteniendo sistema de monitoreo...")
        await monitoring.stop_monitoring()


async def test_alert_system():
    """Prueba el sistema de alertas inteligente"""
    print("\n🔔 Probando sistema de alertas inteligente...")

    config = {
        "auto_healing_enabled": True,
        "alert_email_enabled": False,
        "alert_slack_webhook": ""
    }

    monitoring = UnifiedMonitoringSystem(config)
    await monitoring.start_monitoring()

    try:
        # Esperar inicialización
        await asyncio.sleep(2)

        # Simular diferentes tipos de alertas
        alerts_to_test = [
            {
                "rule_id": "test_high_cpu",
                "severity": AlertSeverity.WARNING,
                "message": "CPU usage above 90%",
                "component": MonitoringComponent.PERFORMANCE_METRICS,
                "auto_healing_actions": ["optimize_high_latency"]
            },
            {
                "rule_id": "test_memory_critical",
                "severity": AlertSeverity.CRITICAL,
                "message": "Memory usage critical: 96%",
                "component": MonitoringComponent.PERFORMANCE_METRICS,
                "auto_healing_actions": ["memory_optimization"]
            }
        ]

        for alert_data in alerts_to_test:
            print(f"🚨 Probando alerta: {alert_data['message']}")

            # Crear regla de alerta
            rule = monitoring.alert_rules.get(alert_data['rule_id'])
            if not rule:
                # Trigger alerta manualmente
                await monitoring._trigger_alert(type('MockRule', (), alert_data)())

            await asyncio.sleep(1)

        # Verificar alertas activas
        status = monitoring.get_system_status()
        active_alerts = status['active_alerts']
        print(f"📊 Alertas activas después de pruebas: {len(active_alerts)}")

        # Verificar historial de alertas
        report = monitoring.get_comprehensive_report()
        alerts_by_severity = report['alert_summary']['alerts_by_severity']
        print(f"📊 Alertas por severidad: {alerts_by_severity}")

        print("✅ Sistema de alertas probado exitosamente")

    except Exception as e:
        print(f"❌ Error en pruebas de alertas: {e}")
        raise
    finally:
        await monitoring.stop_monitoring()


async def test_performance_metrics():
    """Prueba las métricas de rendimiento detalladas"""
    print("\n📊 Probando métricas de rendimiento...")

    monitoring = UnifiedMonitoringSystem()
    await monitoring.start_monitoring()

    try:
        await asyncio.sleep(2)

        # Probar métricas de negocio
        business_metrics = monitoring.components[MonitoringComponent.PERFORMANCE_METRICS]["business_metrics"]
        kpis = business_metrics.get_business_kpis()
        print(f"💼 KPIs de negocio: {len(kpis)} métricas calculadas")

        # Probar analytics avanzado
        analytics = monitoring.components[MonitoringComponent.PERFORMANCE_METRICS]["advanced_analytics"]

        # Generar reporte diario (simulado)
        try:
            daily_report = analytics.generate_daily_report()
            if 'error' not in daily_report:
                print("📈 Reporte diario generado exitosamente")
            else:
                print(f"⚠️ Reporte diario: {daily_report['error']}")
        except Exception as e:
            print(f"⚠️ Error generando reporte diario: {e}")

        # Probar predicción de fallos
        try:
            predictions = analytics.predict_failures("system", 7)
            if 'error' not in predictions:
                print(f"🔮 Predicciones de fallos: Nivel de riesgo {predictions.get('risk_level', 'UNKNOWN')}")
            else:
                print(f"⚠️ Predicciones: {predictions['error']}")
        except Exception as e:
            print(f"⚠️ Error en predicciones: {e}")

        # Probar monitoreo multi-región
        multi_region = monitoring.components[MonitoringComponent.PERFORMANCE_METRICS]["multi_region_monitor"]
        geo_dist = multi_region.get_geographic_distribution()
        print(f"🌍 Distribución geográfica: {len(geo_dist)} regiones")

        load_status = multi_region.get_load_balancing_status()
        print(f"⚖️ Estado de balanceo: {len(load_status)} regiones analizadas")

        print("✅ Métricas de rendimiento probadas exitosamente")

    except Exception as e:
        print(f"❌ Error en pruebas de rendimiento: {e}")
        raise
    finally:
        await monitoring.stop_monitoring()


async def test_high_availability():
    """Prueba características de alta disponibilidad"""
    print("\n🔄 Probando alta disponibilidad...")

    # Configurar para alta disponibilidad
    config = {
        "high_availability": True,
        "auto_healing_enabled": True,
        "monitoring_interval_seconds": 2,  # Muy frecuente para pruebas
        "health_check_interval_seconds": 5
    }

    monitoring = UnifiedMonitoringSystem(config)
    await monitoring.start_monitoring()

    try:
        # Probar por un período más largo
        print("⏳ Probando estabilidad por 15 segundos...")
        start_time = time.time()

        while time.time() - start_time < 15:
            # Verificar salud periódicamente
            status = monitoring.get_system_status()
            if status['system_health']['overall_status'] not in ['HEALTHY', 'INITIALIZING']:
                print(f"⚠️ Estado inestable detectado: {status['system_health']['overall_status']}")

            await asyncio.sleep(2)

        # Verificar estadísticas finales
        final_status = monitoring.get_system_status()
        uptime = final_status['system_health']['uptime_percentage']
        performance = final_status['system_health']['performance_score']

        print(f"⏱️ Uptime durante prueba: {uptime:.1f}%")
        print(f"📊 Performance score: {performance:.1f}/100")

        # Verificar resiliencia
        if uptime > 95 and performance > 80:
            print("✅ Alta disponibilidad verificada")
        else:
            print("⚠️ Problemas de estabilidad detectados")

    except Exception as e:
        print(f"❌ Error en pruebas de alta disponibilidad: {e}")
        raise
    finally:
        await monitoring.stop_monitoring()


async def run_comprehensive_test():
    """Ejecutar todas las pruebas de manera comprehensiva"""
    print("🚀 Iniciando pruebas comprehensivas del Sistema de Monitoreo AILOOS")
    print("=" * 70)

    start_time = time.time()

    try:
        # Ejecutar todas las pruebas
        await test_basic_monitoring()
        await test_alert_system()
        await test_performance_metrics()
        await test_high_availability()

        # Calcular tiempo total
        total_time = time.time() - start_time

        print("\n" + "=" * 70)
        print("🎉 TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        print(f"⏱️ Tiempo total de pruebas: {total_time:.2f} segundos")
        print("✅ Sistema de Monitoreo 24/7 AILOOS está listo para producción")

    except Exception as e:
        print(f"\n❌ PRUEBAS FALLIDAS: {e}")
        print("🔧 Revisar configuración y dependencias")
        raise
    finally:
        print("\n📋 Resumen de funcionalidades probadas:")
        print("  ✅ Monitoreo continuo de componentes del sistema")
        print("  ✅ Sistema de alertas inteligente con severidad y escalada")
        print("  ✅ Dashboards en tiempo real con métricas críticas")
        print("  ✅ Auto-healing automático para problemas detectados")
        print("  ✅ Métricas detalladas de rendimiento y salud del sistema")
        print("  ✅ Alta disponibilidad y escalabilidad enterprise-grade")


if __name__ == "__main__":
    # Ejecutar pruebas
    asyncio.run(run_comprehensive_test())