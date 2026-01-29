"""
Ejemplo de uso del protocolo Gossip para consenso de metadatos críticos.
Demuestra cómo usar el GossipProtocol con el P2PClient existente.
"""

import asyncio
import json
from typing import Dict, Any

from .gossip_protocol import (
    GossipProtocol,
    GossipConfig,
    MetadataType,
    create_gossip_protocol
)
from .p2p_client import create_p2p_client_sync


async def demo_gossip_protocol():
    """
    Demo del protocolo gossip con metadatos críticos.
    """
    print("🗣️ Gossip Protocol Demo")
    print("=" * 50)

    # Crear configuración personalizada
    gossip_config = GossipConfig(
        gossip_interval=2.0,  # Más lento para demo
        fanout=2,
        consensus_timeout=10.0,
        min_consensus_peers=2
    )

    # Crear cliente P2P (simulado para demo)
    p2p_client = create_p2p_client_sync("demo_node_1", port=8443)

    # Crear protocolo gossip
    gossip = await create_gossip_protocol("demo_node_1", p2p_client, gossip_config)

    print("✅ Gossip protocol initialized")

    # Registrar callback para actualizaciones de metadatos
    async def on_metadata_update(key: str, entry):
        print(f"📥 Metadata updated: {key} = {entry.value} (v{entry.version})")

    gossip.register_metadata_callback(MetadataType.CONFIGURATION, on_metadata_update)
    gossip.register_metadata_callback(MetadataType.COSIGN_KEYS, on_metadata_update)
    gossip.register_metadata_callback(MetadataType.TRUSTED_NODES, on_metadata_update)

    # Registrar callback para consenso
    async def on_consensus_reached(key: str, entry):
        print(f"🎯 Consensus reached for {key}: {entry.value} (v{entry.version}, {entry.consensus_votes} votes)")

    gossip.register_consensus_callback("config.network.max_peers", on_consensus_reached)

    print("✅ Callbacks registered")

    # Actualizar metadatos de configuración
    print("\n📝 Updating configuration metadata...")

    await gossip.update_metadata(
        MetadataType.CONFIGURATION,
        "config.network.max_peers",
        100
    )

    await gossip.update_metadata(
        MetadataType.CONFIGURATION,
        "config.security.encryption_level",
        "AES256"
    )

    # Actualizar claves Cosign
    print("\n🔐 Updating Cosign keys...")

    cosign_keys = {
        "key1": "cosign_public_key_1...",
        "key2": "cosign_public_key_2..."
    }

    await gossip.update_metadata(
        MetadataType.COSIGN_KEYS,
        "cosign.keys.active",
        cosign_keys
    )

    # Actualizar lista de nodos trusted
    print("\n🤝 Updating trusted nodes...")

    trusted_nodes = [
        "node_alpha",
        "node_beta",
        "node_gamma"
    ]

    await gossip.update_metadata(
        MetadataType.TRUSTED_NODES,
        "network.trusted_nodes",
        trusted_nodes
    )

    # Solicitar consenso para configuración crítica
    print("\n🎯 Requesting consensus for critical config...")

    consensus_result = await gossip.request_metadata_consensus(
        "config.network.max_peers",
        timeout=5.0
    )

    if consensus_result:
        print(f"✅ Consensus achieved: max_peers = {consensus_result.value}")
    else:
        print("⚠️ Consensus not achieved within timeout")

    # Mostrar estadísticas
    print("\n📊 Gossip Protocol Statistics:")
    stats = gossip.get_stats()
    print(json.dumps(stats, indent=2))

    # Mostrar metadatos por tipo
    print("\n📋 Metadata by type:")

    for metadata_type in MetadataType:
        metadata = await gossip.get_metadata_by_type(metadata_type)
        if metadata:
            print(f"\n{metadata_type.value.upper()}:")
            for key, entry in metadata.items():
                print(f"  {key}: {entry.value} (v{entry.version})")

    # Esperar un poco para ver gossip en acción
    print("\n⏳ Waiting for gossip propagation...")
    await asyncio.sleep(5)

    # Mostrar estadísticas finales
    print("\n📈 Final Statistics:")
    final_stats = gossip.get_stats()
    print(json.dumps(final_stats, indent=2))

    # Detener protocolo
    await gossip.stop()
    print("\n🛑 Gossip protocol stopped")

    print("\n🎉 Demo completed!")


async def demo_cosign_integration():
    """
    Demo de integración con Cosign para verificación de imágenes.
    """
    print("\n🔐 Cosign Integration Demo")
    print("=" * 30)

    # Simular verificación de imagen con Cosign
    try:
        from ..federated.image_verifier import get_image_verifier

        verifier = get_image_verifier()

        # Simular verificación de imagen
        test_image_uri = "docker.io/ailoos/model:v1.0"

        print(f"Verifying image: {test_image_uri}")
        verification = await verifier.verify_image(test_image_uri)

        if verification.is_verified:
            print("✅ Image verification successful")
            print(f"   Signature found: {verification.signature_found}")
            print(f"   Verification time: {verification.verification_time}")

            # Actualizar metadatos con resultado de verificación
            gossip_config = GossipConfig()
            p2p_client = create_p2p_client_sync("verifier_node", port=8444)
            gossip = await create_gossip_protocol("verifier_node", p2p_client, gossip_config)

            await gossip.update_metadata(
                MetadataType.COSIGN_KEYS,
                f"cosign.verification.{test_image_uri}",
                {
                    "verified": True,
                    "timestamp": verification.verification_time,
                    "signature_found": verification.signature_found
                }
            )

            print("📝 Verification result stored in gossip network")

            await gossip.stop()

        else:
            print("❌ Image verification failed")
            print(f"   Error: {verification.error_message}")

    except ImportError:
        print("⚠️ Cosign integration not available (image_verifier module not found)")


def main():
    """Función principal del demo."""
    print("🚀 Starting Gossip Protocol Demo...")

    # Ejecutar demo principal
    asyncio.run(demo_gossip_protocol())

    # Ejecutar demo de Cosign si está disponible
    try:
        asyncio.run(demo_cosign_integration())
    except Exception as e:
        print(f"Cosign demo skipped: {e}")


if __name__ == "__main__":
    main()