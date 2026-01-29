"""
Comandos CLI para gestión de nodos físicos.
Permite iniciar, detener y monitorear nodos federados desde línea de comandos.
"""

import click
import asyncio
import json
import time
from typing import Dict, Any

try:
    from ailoos.node import PhysicalNodeManager, get_node_capabilities, start_physical_node
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from ailoos.node import PhysicalNodeManager, get_node_capabilities, start_physical_node


# Variable global para mantener referencia al nodo activo
_active_node: PhysicalNodeManager = None


@click.group()
@click.pass_context
def node_group(ctx):
    """Comandos para gestión de nodos físicos federados."""
    # Asegurar que tenemos configuración
    if not ctx.obj:
        from ailoos.core.config import get_config
        ctx.obj = get_config()


@node_group.command()
@click.option('--coordinator-url', default='http://136.119.191.184:8000',
              help='URL del coordinador federado')
@click.option('--auto-start', is_flag=True, help='Iniciar automáticamente después de crear')
@click.pass_context
def create(ctx, coordinator_url: str, auto_start: bool):
    """Crea un nuevo nodo físico."""
    try:
        global _active_node

        click.echo("🖥️ Creando nodo físico...")
        click.echo(f"📡 Coordinador: {coordinator_url}")

        # Crear nodo
        _active_node = PhysicalNodeManager(coordinator_url=coordinator_url)

        click.echo(f"✅ Nodo creado: {_active_node.node_id}")
        click.echo("🔧 Capacidades detectadas:")
        capabilities = _active_node.capabilities
        click.echo(f"   🖥️ CPU: {capabilities.cpu_cores} cores")
        click.echo(f"   🧠 RAM: {capabilities.memory_gb} GB")
        click.echo(f"   💾 Almacenamiento: {capabilities.storage_gb} GB")

        if capabilities.gpu_available:
            click.echo(f"   🎮 GPU: {capabilities.gpu_name} ({capabilities.gpu_memory_gb} GB)")
            if capabilities.supports_metal:
                click.echo("   🍎 Soporte Metal: Sí")
            if capabilities.supports_cuda:
                click.echo("   🟦 Soporte CUDA: Sí")
        else:
            click.echo("   🎮 GPU: No disponible")

        if auto_start:
            click.echo("\n🚀 Iniciando nodo automáticamente...")
            success = asyncio.run(_active_node.start_node())
            if success:
                click.echo("✅ Nodo iniciado exitosamente")
            else:
                click.echo("❌ Error al iniciar el nodo", err=True)

    except Exception as e:
        click.echo(f"❌ Error creando nodo: {e}", err=True)


@node_group.command()
@click.option('--coordinator-url', default='http://136.119.191.184:8000',
              help='URL del coordinador federado')
@click.pass_context
def start(ctx, coordinator_url: str):
    """Inicia un nodo físico y lo conecta al coordinador."""
    try:
        global _active_node

        if _active_node is None:
            click.echo("❌ No hay nodo creado. Use 'ailoos node create' primero", err=True)
            return

        click.echo("🚀 Iniciando nodo físico...")
        click.echo(f"📡 Conectando a: {coordinator_url}")

        # Iniciar nodo
        success = asyncio.run(_active_node.start_node())

        if success:
            click.echo("✅ Nodo iniciado y registrado exitosamente")
            click.echo(f"🆔 Node ID: {_active_node.node_id}")
            click.echo("💡 El nodo ahora está participando en la red federada")
            click.echo("💰 Comenzará a ganar DracmaS por contribuir al entrenamiento")
        else:
            click.echo("❌ Error al iniciar el nodo", err=True)

    except Exception as e:
        click.echo(f"❌ Error iniciando nodo: {e}", err=True)


@node_group.command()
@click.pass_context
def stop(ctx):
    """Detiene el nodo físico activo."""
    try:
        global _active_node

        if _active_node is None:
            click.echo("❌ No hay nodo activo", err=True)
            return

        click.echo("🛑 Deteniendo nodo físico...")

        # Detener nodo
        asyncio.run(_active_node.stop_node())

        click.echo("✅ Nodo detenido exitosamente")
        _active_node = None

    except Exception as e:
        click.echo(f"❌ Error deteniendo nodo: {e}", err=True)


@node_group.command()
@click.option('--watch', is_flag=True, help='Monitoreo continuo')
@click.option('--interval', default=5, type=int, help='Intervalo de actualización en segundos')
@click.pass_context
def status(ctx, watch: bool, interval: int):
    """Muestra el estado del nodo físico."""
    try:
        global _active_node

        if _active_node is None:
            click.echo("❌ No hay nodo activo. Use 'ailoos node start' para iniciar uno", err=True)
            return

        while True:
            # Obtener estado
            node_status = asyncio.run(_active_node.get_node_status())

            # Limpiar pantalla si es modo watch
            if watch:
                click.clear()

            # Header
            click.echo("📊 ESTADO DEL NODO FÍSICO")
            click.echo("=" * 50)
            click.echo(f"🆔 Node ID: {node_status['node_id']}")
            click.echo(f"🟢 Online: {'Sí' if node_status['status']['is_online'] else 'No'}")
            click.echo(f"🎯 Entrenando: {'Sí' if node_status['status']['is_training'] else 'No'}")

            if node_status['status']['current_session']:
                click.echo(f"📋 Sesión actual: {node_status['status']['current_session']}")

            # Rendimiento
            perf = node_status['performance_metrics']
            if perf:
                click.echo("\n⚡ RENDIMIENTO:")
                click.echo(f"   🖥️ CPU: {perf.get('cpu_percent', 0):.1f}%")
                click.echo(f"   🧠 RAM: {perf.get('memory_used_gb', 0):.1f}GB / {perf.get('memory_total_gb', 0):.1f}GB ({perf.get('memory_percent', 0):.1f}%)")
                click.echo(f"   💾 Disco: {perf.get('disk_used_gb', 0):.1f}GB / {perf.get('disk_total_gb', 0):.1f}GB ({perf.get('disk_percent', 0):.1f}%)")

            # Estadísticas de entrenamiento
            training_stats = node_status['status']
            if training_stats['total_samples_processed'] > 0:
                click.echo("\n🎯 ESTADÍSTICAS DE ENTRENAMIENTO:")
                click.echo(f"   📊 Muestras procesadas: {training_stats['total_samples_processed']:,}")
                click.echo(f"   ⏱️ Tiempo total: {training_stats['total_training_time']:.1f}s")
                click.echo(f"   💰 DracmaS ganado: {training_stats['dracma_earned']:.2f}")

            # Capacidades
            caps = node_status['capabilities']
            click.echo("\n🔧 CAPACIDADES:")
            click.echo(f"   🖥️ CPU: {caps['cpu_cores']} cores")
            click.echo(f"   🧠 RAM: {caps['memory_gb']:.1f} GB")

            if caps['gpu_available']:
                click.echo(f"   🎮 GPU: {caps['gpu_name']} ({caps['gpu_memory_gb']:.1f} GB)")
                click.echo(f"   🍎 Metal: {'Sí' if caps['supports_metal'] else 'No'}")
                click.echo(f"   🟦 CUDA: {'Sí' if caps['supports_cuda'] else 'No'}")

            click.echo(f"   💾 Almacenamiento: {caps['storage_gb']:.1f} GB")

            # Sesiones activas
            active_sessions = node_status['active_sessions']
            if active_sessions:
                click.echo("\n📋 SESIONES ACTIVAS:")
                for session_id in active_sessions:
                    click.echo(f"   🔗 {session_id}")
            else:
                click.echo("\n📋 Sesiones activas: Ninguna")
            # Timestamp
            click.echo(f"\n🕒 Última actualización: {time.strftime('%H:%M:%S')}")

            if not watch:
                break

            time.sleep(interval)

    except KeyboardInterrupt:
        click.echo("\n🛑 Monitoreo detenido por usuario")
    except Exception as e:
        click.echo(f"❌ Error obteniendo estado: {e}", err=True)


@node_group.command()
@click.option('--session-id', required=True, help='ID de la sesión federada')
@click.pass_context
def join_session(ctx, session_id: str):
    """Une el nodo a una sesión de entrenamiento federado."""
    try:
        global _active_node

        if _active_node is None:
            click.echo("❌ No hay nodo activo. Use 'ailoos node start' primero", err=True)
            return

        click.echo(f"🤝 Uniéndose a sesión federada: {session_id}...")

        success = asyncio.run(_active_node.join_federated_session(session_id))

        if success:
            click.echo("✅ Unido a sesión exitosamente")
            click.echo("🎯 El nodo comenzará a contribuir al entrenamiento")
            click.echo("💰 Ganará DracmaS por cada ronda completada")
        else:
            click.echo("❌ Error al unirse a la sesión", err=True)

    except Exception as e:
        click.echo(f"❌ Error uniéndose a sesión: {e}", err=True)


@node_group.command()
@click.option('--session-id', required=True, help='ID de la sesión a abandonar')
@click.pass_context
def leave_session(ctx, session_id: str):
    """Abandona una sesión de entrenamiento federado."""
    try:
        global _active_node

        if _active_node is None:
            click.echo("❌ No hay nodo activo", err=True)
            return

        click.echo(f"👋 Abandonando sesión: {session_id}...")

        asyncio.run(_active_node.leave_federated_session(session_id))

        click.echo("✅ Sesión abandonada exitosamente")

    except Exception as e:
        click.echo(f"❌ Error abandonando sesión: {e}", err=True)


@node_group.command()
@click.pass_context
def capabilities(ctx):
    """Muestra las capacidades del dispositivo actual."""
    try:
        click.echo("🔍 Detectando capacidades del dispositivo...")

        capabilities = get_node_capabilities()

        click.echo("\n🖥️ CAPACIDADES DETECTADAS:")
        click.echo("=" * 40)
        click.echo(f"🖥️ CPU Cores: {capabilities['cpu_cores']}")
        click.echo(f"🧠 Memoria RAM: {capabilities['memory_gb']} GB")
        click.echo(f"💾 Almacenamiento: {capabilities['storage_gb']} GB")

        if capabilities['gpu_available']:
            click.echo(f"🎮 GPU Disponible: Sí")
            click.echo(f"   📛 Nombre: {capabilities['gpu_name']}")
            click.echo(f"   🧠 Memoria: {capabilities['gpu_memory_gb']} GB")
            click.echo(f"   🍎 Metal Support: {'Sí' if capabilities['supports_metal'] else 'No'}")
            click.echo(f"   🟦 CUDA Support: {'Sí' if capabilities['supports_cuda'] else 'No'}")
            click.echo(f"   🔄 OpenCL Support: {'Sí' if capabilities['supports_opencl'] else 'No'}")
        else:
            click.echo("🎮 GPU Disponible: No")

        if capabilities['network_speed_mbps']:
            click.echo(f"🌐 Velocidad de Red: {capabilities['network_speed_mbps']} Mbps")
        else:
            click.echo("🌐 Velocidad de Red: No medida")

        click.echo("\n💡 RECOMENDACIONES:")
        if capabilities['gpu_available']:
            click.echo("   ✅ Excelente para entrenamiento federado con GPU")
        elif capabilities['cpu_cores'] >= 8:
            click.echo("   ✅ Bueno para entrenamiento federado con CPU")
        else:
            click.echo("   ⚠️ Limitado para entrenamiento intensivo")

        if capabilities['memory_gb'] >= 16:
            click.echo("   ✅ Memoria suficiente para modelos grandes")
        elif capabilities['memory_gb'] >= 8:
            click.echo("   ⚠️ Memoria limitada - usar modelos pequeños")
        else:
            click.echo("   ❌ Memoria insuficiente")

    except Exception as e:
        click.echo(f"❌ Error detectando capacidades: {e}", err=True)


@node_group.command()
@click.option('--output', default='node_status.json', help='Archivo de salida')
@click.pass_context
def export_status(ctx, output: str):
    """Exporta el estado completo del nodo a un archivo JSON."""
    try:
        global _active_node

        if _active_node is None:
            click.echo("❌ No hay nodo activo", err=True)
            return

        click.echo("📤 Exportando estado del nodo...")

        # Obtener estado completo
        status = asyncio.run(_active_node.get_node_status())

        # Añadir timestamp
        status['export_timestamp'] = time.time()
        status['export_datetime'] = time.strftime('%Y-%m-%d %H:%M:%S')

        # Guardar a archivo
        with open(output, 'w') as f:
            json.dump(status, f, indent=2, default=str)

        click.echo(f"✅ Estado exportado a: {output}")

    except Exception as e:
        click.echo(f"❌ Error exportando estado: {e}", err=True)


# Alias para el grupo principal
node = node_group
node_cli = node_group