"""
Node verification system with zero-knowledge proofs.
Provides cryptographic verification of node identity, reputation, and privacy-preserving proofs.
"""

from .node_verifier import (
    NodeVerifier,
    NodeIdentity,
    NodeReputation,
    HardwareVerification,
    VerificationChallenge
)
from .zk_proofs import (
    ZKProofManager,
    ZKProver,
    ZKVerifier,
    ZKProof,
    ContributionProof,
    HardwareProof
)
from .dataset_integrity_verifier import (
    DatasetIntegrityVerifier,
    IntegrityCheckResult,
    CorruptionReport
)
# from .zkp_engine import (
#     ZKPEngine,
#     ZKPType,
#     ZKPKeyPair,
#     ZKPProof,
#     KeyManager,
#     ZKPProver as ZKPAdvancedProver,
#     ZKPVerifier as ZKPAdvancedVerifier,
#     BulletproofProver,
#     Groth16Prover,
#     BulletproofVerifier,
#     Groth16Verifier,
#     create_zkp_engine,
#     generate_bulletproof_range_proof,
#     verify_proof_batch
# )

__all__ = [
    'NodeVerifier',
    'ZKProofManager',
    'NodeIdentity',
    'NodeReputation',
    'HardwareVerification',
    'VerificationChallenge',
    'ZKProver',
    'ZKVerifier',
    'ZKProof',
    'ContributionProof',
    'HardwareProof',
    'DatasetIntegrityVerifier',
    'IntegrityCheckResult',
    'CorruptionReport',
    'create_node_verifier',
    'verify_node_eligibility',
    'get_node_reputation',
    'get_verification_stats',
    'create_dataset_integrity_verifier',
    # # Nuevo motor ZKP avanzado
    # 'ZKPEngine',
    # 'ZKPType',
    # 'ZKPKeyPair',
    # 'ZKPProof',
    # 'KeyManager',
    # 'ZKPAdvancedProver',
    # 'ZKPAdvancedVerifier',
    # 'BulletproofProver',
    # 'Groth16Prover',
    # 'BulletproofVerifier',
    # 'Groth16Verifier',
    # 'create_zkp_engine',
    # 'generate_bulletproof_range_proof',
    # 'verify_proof_batch'
]

# Funciones de conveniencia para verificación de nodos
def create_node_verifier(config=None, coordinator=None) -> NodeVerifier:
    """Crear instancia del verificador de nodos."""
    if config is None:
        from ..core.config import Config
        config = Config()
    return NodeVerifier(config, coordinator)

def verify_node_eligibility(node_verifier: NodeVerifier, node_id: str) -> tuple:
    """Verificar elegibilidad de un nodo."""
    return node_verifier.is_node_eligible(node_id)

def get_node_reputation(node_verifier: NodeVerifier, node_id: str) -> NodeReputation:
    """Obtener reputación de un nodo."""
    return node_verifier.get_node_reputation(node_id)

def get_verification_stats(node_verifier: NodeVerifier) -> dict:
    """Obtener estadísticas del sistema de verificación."""
    return node_verifier.get_verification_stats()

def create_dataset_integrity_verifier(config=None) -> DatasetIntegrityVerifier:
    """Crear instancia del verificador de integridad de datasets."""
    if config is None:
        from ..core.config import Config
        config = Config()
    return DatasetIntegrityVerifier(config)

# # Funciones de conveniencia para el motor ZKP avanzado
# def create_advanced_zkp_engine(config=None) -> ZKPEngine:
#     """Crear instancia del motor ZKP avanzado."""
#     return create_zkp_engine(config)

# def get_zkp_engine_stats(engine: ZKPEngine) -> dict:
#     """Obtener estadísticas del motor ZKP."""
#     return engine.get_engine_stats()