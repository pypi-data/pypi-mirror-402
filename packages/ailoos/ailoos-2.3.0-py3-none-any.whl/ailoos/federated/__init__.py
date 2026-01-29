"""
Sistema federado de AILOOS.
Incluye sesiones, training coordinado, agregación FedAvg, homomorphic encryption y protocolo P2P seguro.
"""

from .session import FederatedSession
from .trainer import FederatedTrainer, create_federated_trainer, distribute_model_async
from .aggregator import FederatedAggregator, create_aggregator, aggregate_weights_async
from .secure_preference_aggregator import (
    SecurePreferenceAggregator, PreferenceAggregationConfig, EncryptedPreferenceUpdate,
    create_secure_preference_aggregator, encrypt_preference_data,
    integrate_with_federated_dpo_training, aggregate_preferences_secure_async
)
from .data_coordinator import FederatedDataCoordinator, DatasetInfo, DataPipelineStatus
from .optimal_dataset_partitioner import OptimalDatasetPartitioner, PartitionStrategy, PartitionResult
from .ipfs_data_loader import IPFSDataLoader, create_ipfs_data_loader
from .p2p_protocol import (
    P2PProtocol, create_p2p_protocol, connect_to_peer_network,
    P2PMessage, P2PMessageType, PeerInfo, ConnectionState,
    SecureAggregationProtocol
)

# TenSEAL Homomorphic Encryption (conditional import)
try:
    # Check if tenseal is available before importing the module
    import tenseal as ts
    # Only import if tenseal is available
    from . import tenseal_encryptor
    TenSEALEncryptor = tenseal_encryptor.TenSEALEncryptor
    TenSEALConfig = tenseal_encryptor.TenSEALConfig
    TenSEALContextManager = tenseal_encryptor.TenSEALContextManager
    create_tenseal_encryptor = tenseal_encryptor.create_tenseal_encryptor
    benchmark_tenseal_operations = tenseal_encryptor.benchmark_tenseal_operations
    TENSEAL_AVAILABLE = True
except ImportError:
    # TenSEAL not available, create dummy classes
    TenSEALEncryptor = None
    TenSEALConfig = None
    TenSEALContextManager = None
    create_tenseal_encryptor = None
    benchmark_tenseal_operations = None
    TENSEAL_AVAILABLE = False

# AdamW Optimizer for Federated Training
from .adamw_optimizer import (
    FederatedAdamWOptimizer, AdamWOptimizer, WarmupLRScheduler, GradientClipper,
    AdamWConfig, LRSchedulerConfig, GradientClippingConfig, FederatedAdamWConfig,
    create_federated_adamw_optimizer, benchmark_adamw_optimizer
)

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Real Federated Training Loop - FASE REAL-5
    from .real_federated_training_loop import (
        RealFederatedTrainingLoop, SecureGradientAggregation, BlockchainRewardsIntegration,
        RealLearningValidation, DistributedStateSync, FederatedTrainingConfig,
        NodeContribution, RoundResult, create_real_federated_training_loop,
        run_real_federated_training_demo
    )

    # Load Testing Infrastructure - FASE 4.1
    from .load_testing import (
        LoadTestingCoordinator, LoadTestConfig, LoadTestResults, NodeSimulator,
        NetworkSimulator, run_load_test, create_default_load_test_config,
        run_scalability_test
    )

    # Multi-Coordinator Architecture - FASE 4.1
    from .multi_coordinator import (
        MultiCoordinatorManager, CoordinatorNode, CoordinatorRole, CoordinatorStatus,
        LoadBalancer, FailoverManager, StateSynchronizer, SessionState,
        create_multi_coordinator_system, create_default_coordinator_config,
        run_failover_test
    )


_LAZY_IMPORTS = {
    # Real Federated Training Loop - FASE REAL-5
    "RealFederatedTrainingLoop": ("real_federated_training_loop", "RealFederatedTrainingLoop"),
    "SecureGradientAggregation": ("real_federated_training_loop", "SecureGradientAggregation"),
    "BlockchainRewardsIntegration": ("real_federated_training_loop", "BlockchainRewardsIntegration"),
    "RealLearningValidation": ("real_federated_training_loop", "RealLearningValidation"),
    "DistributedStateSync": ("real_federated_training_loop", "DistributedStateSync"),
    "FederatedTrainingConfig": ("real_federated_training_loop", "FederatedTrainingConfig"),
    "NodeContribution": ("real_federated_training_loop", "NodeContribution"),
    "RoundResult": ("real_federated_training_loop", "RoundResult"),
    "create_real_federated_training_loop": ("real_federated_training_loop", "create_real_federated_training_loop"),
    "run_real_federated_training_demo": ("real_federated_training_loop", "run_real_federated_training_demo"),
    # Load Testing Infrastructure - FASE 4.1
    "LoadTestingCoordinator": ("load_testing", "LoadTestingCoordinator"),
    "LoadTestConfig": ("load_testing", "LoadTestConfig"),
    "LoadTestResults": ("load_testing", "LoadTestResults"),
    "NodeSimulator": ("load_testing", "NodeSimulator"),
    "NetworkSimulator": ("load_testing", "NetworkSimulator"),
    "run_load_test": ("load_testing", "run_load_test"),
    "create_default_load_test_config": ("load_testing", "create_default_load_test_config"),
    "run_scalability_test": ("load_testing", "run_scalability_test"),
    # Multi-Coordinator Architecture - FASE 4.1
    "MultiCoordinatorManager": ("multi_coordinator", "MultiCoordinatorManager"),
    "CoordinatorNode": ("multi_coordinator", "CoordinatorNode"),
    "CoordinatorRole": ("multi_coordinator", "CoordinatorRole"),
    "CoordinatorStatus": ("multi_coordinator", "CoordinatorStatus"),
    "LoadBalancer": ("multi_coordinator", "LoadBalancer"),
    "FailoverManager": ("multi_coordinator", "FailoverManager"),
    "StateSynchronizer": ("multi_coordinator", "StateSynchronizer"),
    "SessionState": ("multi_coordinator", "SessionState"),
    "create_multi_coordinator_system": ("multi_coordinator", "create_multi_coordinator_system"),
    "create_default_coordinator_config": ("multi_coordinator", "create_default_coordinator_config"),
    "run_failover_test": ("multi_coordinator", "run_failover_test"),
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        module_name, attr_name = _LAZY_IMPORTS[name]
        module = importlib.import_module(f".{module_name}", __name__)
        value = getattr(module, attr_name)
        globals()[name] = value
        return value
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    'FederatedSession',
    'FederatedTrainer',
    'create_federated_trainer',
    'distribute_model_async',
    'FederatedAggregator',
    'create_aggregator',
    'aggregate_weights_async',
    'SecurePreferenceAggregator',
    'PreferenceAggregationConfig',
    'EncryptedPreferenceUpdate',
    'create_secure_preference_aggregator',
    'encrypt_preference_data',
    'integrate_with_federated_dpo_training',
    'aggregate_preferences_secure_async',
    'FederatedDataCoordinator',
    'DatasetInfo',
    'DataPipelineStatus',
    'OptimalDatasetPartitioner',
    'PartitionStrategy',
    'PartitionResult',
    'IPFSDataLoader',
    'create_ipfs_data_loader',
    # Protocol P2P
    'P2PProtocol',
    'create_p2p_protocol',
    'connect_to_peer_network',
    'P2PMessage',
    'P2PMessageType',
    'PeerInfo',
    'ConnectionState',
    'SecureAggregationProtocol',
    # TenSEAL Homomorphic Encryption (only if available)
    *(['TenSEALEncryptor', 'TenSEALConfig', 'TenSEALContextManager',
       'create_tenseal_encryptor', 'benchmark_tenseal_operations'] if TENSEAL_AVAILABLE else []),
    # AdamW Optimizer for Federated Training
    'FederatedAdamWOptimizer',
    'AdamWOptimizer',
    'WarmupLRScheduler',
    'GradientClipper',
    'AdamWConfig',
    'LRSchedulerConfig',
    'GradientClippingConfig',
    'FederatedAdamWConfig',
    'create_federated_adamw_optimizer',
    'benchmark_adamw_optimizer',
    # Real Federated Training Loop - FASE REAL-5
    'RealFederatedTrainingLoop',
    'SecureGradientAggregation',
    'BlockchainRewardsIntegration',
    'RealLearningValidation',
    'DistributedStateSync',
    'FederatedTrainingConfig',
    'NodeContribution',
    'RoundResult',
    'create_real_federated_training_loop',
    'run_real_federated_training_demo',
    # Load Testing Infrastructure - FASE 4.1
    'LoadTestingCoordinator',
    'LoadTestConfig',
    'LoadTestResults',
    'NodeSimulator',
    'NetworkSimulator',
    'run_load_test',
    'create_default_load_test_config',
    'run_scalability_test',
    # Multi-Coordinator Architecture - FASE 4.1
    'MultiCoordinatorManager',
    'CoordinatorNode',
    'CoordinatorRole',
    'CoordinatorStatus',
    'LoadBalancer',
    'FailoverManager',
    'StateSynchronizer',
    'SessionState',
    'create_multi_coordinator_system',
    'create_default_coordinator_config',
    'run_failover_test'
]
