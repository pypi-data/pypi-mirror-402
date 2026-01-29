#!/usr/bin/env python3
"""
Ejemplo de uso del Privacy Web Search Bridge

Este script demuestra cómo usar el PrivacyWebSearchBridge para búsquedas web anónimas.
"""

import asyncio
from privacy_web_search_bridge import PrivacyWebSearchBridge, SearchOptions


async def main():
    """Ejemplo principal de uso"""

    # Crear bridge con configuración por defecto
    bridge = PrivacyWebSearchBridge()

    print("🔍 Privacy Web Search Bridge Demo")
    print("=" * 40)

    # Verificar configuración
    print(f"Web search enabled: {bridge.is_web_search_enabled()}")
    print(f"Preferred engine: {bridge.config.get('preferred_engine')}")
    print()

    # Test detección automática
    queries = [
        "¿Cuál es el precio del Bitcoin hoy?",
        "¿Quién ganó las elecciones 2024?",
        "¿Cuál es la capital de Francia?",  # No necesita búsqueda
        "¿Cuántos habitantes tiene Madrid?",
    ]

    print("🤖 Detección automática de necesidad de búsqueda:")
    for query in queries:
        needs_search = bridge.detect_web_search_need(query)
        status = "✅ Sí" if needs_search else "❌ No"
        print(f"  {status}: {query}")
    print()

    # Test búsqueda (comentado para evitar requests reales en demo)
    """
    print("🌐 Realizando búsqueda web...")
    try:
        results = await bridge.search_web("precio bitcoin hoy")
        print(f"Encontrados {len(results)} resultados:")

        for i, result in enumerate(results[:3], 1):
            print(f"{i}. {result.title}")
            print(f"   URL: {result.url}")
            print(f"   Score: {result.score:.2f}")
            print(f"   {result.snippet[:100]}...")
            print()

    except Exception as e:
        print(f"Error en búsqueda: {e}")
    """

    # Test enriquecimiento de contexto
    print("📝 Enriquecimiento de contexto:")
    context = "El usuario pregunta sobre criptomonedas."
    enriched = bridge.enrich_context_with_search("¿Precio Bitcoin hoy?", context)
    print(f"Contexto original: {context}")
    print(f"Contexto enriquecido: {enriched[:200]}...")
    print()

    # Test configuración
    print("⚙️ Gestión de configuración:")
    print(f"Motor actual: {bridge.get_config()['preferred_engine']}")

    # Cambiar configuración
    bridge.update_config({"preferred_engine": "startpage"})
    print(f"Motor cambiado: {bridge.get_config()['preferred_engine']}")
    print()

    # Test historial
    print("📊 Gestión de historial:")
    bridge._add_to_history("test query", SearchOptions(), 5)
    history = bridge.get_search_history()
    print(f"Entradas en historial: {len(history)}")

    # Limpiar historial
    bridge.clear_search_history()
    print(f"Después de limpiar: {len(bridge.get_search_history())} entradas")
    print()

    # Test fallback
    print("🔄 Conocimiento de fallback:")
    fallback = bridge.get_fallback_knowledge("precio bitcoin")
    print(f"Fallback: {fallback}")
    print()

    # Cerrar bridge
    await bridge.close()
    print("✅ Demo completada exitosamente")


if __name__ == "__main__":
    asyncio.run(main())