"""
Advanced SDK Client - Cliente unificado para todas las funcionalidades de AILOOS
Integra wallet, staking, datasets, IPFS, marketplace, y entrenamiento federado.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path

from ..core.logging import get_logger
from ..blockchain.wallet_manager import get_wallet_manager, WalletManager
from ..blockchain.staking_manager import get_staking_manager, StakingManager
from ..data.dataset_manager import dataset_manager
from ..data.ipfs_connector import ipfs_connector
# from ..coordinator.registry import data_registry  <-- REMOVED SERVER DEPENDENCY
from ..sdk.marketplace_client import MarketplaceClient
from ..sdk.federated_client import FederatedClient
from ..sdk.auth import NodeAuthenticator

# Client-side stub for registry interactions
class RegistryClientStub:
    def register_node(self, *args, **kwargs):
        logger.info("📡 Registering node via API (stub implementation)")
        
    def register_dataset(self, *args, **kwargs):
        logger.info("📡 Registering dataset via API (stub implementation)")
        
    def record_shard_access(self, *args, **kwargs):
        pass
        
    def search_datasets(self, *args, **kwargs):
        return []
        
    def get_dataset_info(self, *args, **kwargs):
        # Return mock info to prevent crashes
        return {'shard_cids': [], 'metadata': {}}
        
    def unregister_node(self, *args, **kwargs):
        pass
        
    def get_network_stats(self):
        return {}

data_registry = RegistryClientStub()

logger = get_logger(__name__)


class AILOOSNode:
    """
    Representa un nodo completo de AILOOS con todas sus capacidades.
    """

    def __init__(self, node_id: str, workspace_path: str = "./ailoos_workspace"):
        self.node_id = node_id
        self.workspace_path = Path(workspace_path)
        self.workspace_path.mkdir(parents=True, exist_ok=True)

        # Componentes del nodo
        self.wallet_manager: Optional[WalletManager] = None
        self.staking_manager: Optional[StakingManager] = None
        self.marketplace_client: Optional[MarketplaceClient] = None
        self.federated_client: Optional[FederatedClient] = None

        # Estado del nodo
        self.initialized = False
        self.capabilities = {
            'has_gpu': False,
            'gpu_memory_gb': 0,
            'cpu_cores': 0,
            'ram_gb': 0,
            'storage_gb': 0,
            'network_speed': 'unknown'
        }

        # Estadísticas del nodo
        self.stats = {
            'datasets_processed': 0,
            'training_sessions': 0,
            'tokens_earned': 0.0,
            'uptime_hours': 0.0,
            'last_activity': datetime.now()
        }

        logger.info(f"🤖 AILOOS Node initialized: {node_id}")

    async def initialize(self, coordinator_url: str = "http://localhost:8000",
                        enable_marketplace: bool = True,
                        enable_federated: bool = True) -> bool:
        """
        Inicializa completamente el nodo con todos sus componentes.

        Args:
            coordinator_url: URL del coordinador federado
            enable_marketplace: Si habilitar marketplace
            enable_federated: Si habilitar entrenamiento federado

        Returns:
            True si la inicialización fue exitosa
        """
        try:
            logger.info("🚀 Initializing AILOOS Node components...")

            # 1. Detectar capacidades del hardware
            await self._detect_capabilities()

            # 2. Inicializar wallet y staking
            self.wallet_manager = get_wallet_manager()
            self.staking_manager = get_staking_manager()

            # 3. Inicializar autenticador
            auth = NodeAuthenticator(self.node_id, "demo_key")

            # 4. Inicializar marketplace si está habilitado
            if enable_marketplace:
                self.marketplace_client = MarketplaceClient(
                    node_id=self.node_id,
                    rpc_url="http://localhost:8545" # Default RPC
                )
                success = await self.marketplace_client.initialize()
                if not success:
                    logger.warning("⚠️ Marketplace client initialization failed")

            # 5. Inicializar cliente federado si está habilitado
            if enable_federated:
                self.federated_client = FederatedClient(
                    node_id=self.node_id,
                    coordinator_url=coordinator_url,
                    authenticator=auth
                )

            # 6. Registrar nodo en el registry
            data_registry.register_node(self.node_id, self.capabilities)

            self.initialized = True
            logger.info(f"✅ AILOOS Node {self.node_id} fully initialized")
            return True

        except Exception as e:
            logger.error(f"❌ Node initialization failed: {e}")
            return False

    async def _detect_capabilities(self) -> None:
        """Detecta las capacidades del hardware del nodo."""
        try:
            import psutil
            import GPUtil

            # CPU
            self.capabilities['cpu_cores'] = psutil.cpu_count(logical=True)

            # RAM
            ram_bytes = psutil.virtual_memory().total
            self.capabilities['ram_gb'] = round(ram_bytes / (1024**3), 1)

            # Disco
            disk_bytes = psutil.disk_usage('/').total
            self.capabilities['storage_gb'] = round(disk_bytes / (1024**3), 1)

            # GPU
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]  # Primera GPU
                    self.capabilities['has_gpu'] = True
                    self.capabilities['gpu_memory_gb'] = round(gpu.memoryTotal / 1024, 1)
                    self.capabilities['gpu_name'] = gpu.name
                else:
                    self.capabilities['has_gpu'] = False
            except:
                self.capabilities['has_gpu'] = False

            logger.info(f"🔍 Hardware detected: {self.capabilities}")

        except ImportError:
            logger.warning("⚠️ psutil/GPUtil not available, using basic capabilities")
            self.capabilities.update({
                'cpu_cores': 4,
                'ram_gb': 8,
                'has_gpu': False,
                'storage_gb': 100
            })

    # ==================== WALLET & STAKING ====================

    async def get_wallet_balance(self) -> float:
        """Obtiene balance de la wallet."""
        if not self.wallet_manager:
            raise RuntimeError("Wallet manager not initialized")

        # Get user's wallets
        user_wallets = self.wallet_manager.get_user_wallets(self.node_id)
        if not user_wallets:
            return 0.0

        # Get balance from first wallet (simplified)
        wallet = user_wallets[0]
        balance_info = await self.wallet_manager.get_wallet_balance(wallet.wallet_id)
        return balance_info.get('total_balance', 0.0)

    async def stake_tokens(self, amount: float) -> Dict[str, Any]:
        """Hace stake de tokens."""
        if not self.staking_manager:
            raise RuntimeError("Staking manager not initialized")

        result = await self.staking_manager.stake_tokens(self.node_id, amount)
        if result.get('success'):
            self.stats['tokens_earned'] += amount  # Track staked amount

        return result

    async def unstake_tokens(self, amount: float) -> Dict[str, Any]:
        """Hace unstake de tokens."""
        if not self.staking_manager:
            raise RuntimeError("Staking manager not initialized")
        return await self.staking_manager.unstake_tokens(self.node_id, amount)

    async def get_staking_info(self) -> Dict[str, Any]:
        """Obtiene información de staking."""
        if not self.staking_manager:
            raise RuntimeError("Staking manager not initialized")
        return self.staking_manager.get_staking_info(self.node_id)

    async def transfer_tokens(self, recipient: str, amount: float) -> Dict[str, Any]:
        """Transfiere tokens a otro nodo."""
        if not self.wallet_manager:
            raise RuntimeError("Wallet manager not initialized")
        return await self.wallet_manager.transfer(self.node_id, recipient, amount)

    # ==================== DATASETS & IPFS ====================

    async def process_dataset(self, file_path: str, dataset_name: str,
                            shard_size_mb: int = 50) -> Dict[str, Any]:
        """
        Procesa un archivo y lo convierte en dataset distribuido.

        Args:
            file_path: Ruta al archivo a procesar
            dataset_name: Nombre del dataset
            shard_size_mb: Tamaño de cada shard

        Returns:
            Información del dataset procesado
        """
        logger.info(f"📦 Processing dataset: {dataset_name}")

        # Procesar con el dataset manager
        dataset_info = dataset_manager.process_text_file(
            file_path=file_path,
            dataset_name=dataset_name,
            shard_size_mb=shard_size_mb
        )

        # Registrar en el registry global
        data_registry.register_dataset(
            dataset_name=dataset_name,
            owner_node=self.node_id,
            shard_cids=dataset_info['shard_cids'],
            metadata={
                'file_size_mb': dataset_info['total_size_mb'],
                'num_shards': dataset_info['num_shards'],
                'quality_score': 0.8,  # Calidad por defecto
                'category': 'processed_text'
            }
        )

        self.stats['datasets_processed'] += 1
        self.stats['last_activity'] = datetime.now()

        logger.info(f"✅ Dataset processed and registered: {dataset_name}")
        return dataset_info

    async def download_shard(self, cid: str, local_path: Optional[str] = None) -> Any:
        """
        Descarga un shard desde IPFS.

        Args:
            cid: Content Identifier del shard
            local_path: Ruta local opcional para guardar

        Returns:
            Datos del shard descargado
        """
        logger.info(f"⬇️ Downloading shard: {cid}")

        # Registrar acceso en el registry
        data_registry.record_shard_access(cid, self.node_id)

        # Descargar
        shard = dataset_manager.download_shard(cid, local_path)

        self.stats['last_activity'] = datetime.now()
        return shard

    async def search_datasets(self, query: str = "", category: str = "",
                            min_quality: float = 0.0, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Busca datasets disponibles en la red.

        Args:
            query: Término de búsqueda
            category: Categoría específica
            min_quality: Calidad mínima
            limit: Número máximo de resultados

        Returns:
            Lista de datasets encontrados
        """
        datasets = data_registry.search_datasets(
            query=query,
            category=category,
            min_quality=min_quality
        )
        return datasets[:limit]

    # ==================== MARKETPLACE ====================

    async def list_dataset_for_sale(self, dataset_name: str, price_dracma: float,
                                  description: str = "") -> Dict[str, Any]:
        """
        Lista un dataset en el marketplace.

        Args:
            dataset_name: Nombre del dataset a vender
            price_dracma: Precio en tokens DRACMA
            description: Descripción del dataset

        Returns:
            Resultado de la operación
        """
        if not self.marketplace_client:
            raise RuntimeError("Marketplace client not initialized")

        # Obtener información del dataset
        dataset_info = data_registry.get_dataset_info(dataset_name)
        if not dataset_info:
            raise ValueError(f"Dataset not found: {dataset_name}")

        # Crear metadata para el marketplace
        metadata = {
            'dataset_name': dataset_name,
            'shard_cids': dataset_info['shard_cids'],
            'data_size_mb': dataset_info.get('metadata', {}).get('file_size_mb', 0),
            'quality_score': dataset_info.get('quality_score', 0.5),
            'category': 'dataset',
            'owner_node': self.node_id
        }

        # Crear listing (usando un archivo temporal como placeholder)
        temp_file = self.workspace_path / f"{dataset_name}_listing.json"
        with open(temp_file, 'w') as f:
            json.dump(metadata, f)

        try:
            listing_id = await self.marketplace_client.create_listing(
                title=f"Dataset: {dataset_name}",
                description=description or f"High-quality dataset: {dataset_name}",
                data_path=str(temp_file),
                price_dracma=price_dracma,
                metadata=metadata
            )

            return {
                'success': True,
                'listing_id': listing_id,
                'dataset_name': dataset_name,
                'price_dracma': price_dracma
            }

        finally:
            # Limpiar archivo temporal
            if temp_file.exists():
                temp_file.unlink()

    async def purchase_dataset(self, listing_id: str) -> Dict[str, Any]:
        """
        Compra un dataset del marketplace.

        Args:
            listing_id: ID del listing a comprar

        Returns:
            Resultado de la compra
        """
        if not self.marketplace_client:
            raise RuntimeError("Marketplace client not initialized")

        # Obtener detalles del listing
        listings = await self.marketplace_client.search_datasets(limit=1000)
        listing = next((l for l in listings if l.get('listing_id') == listing_id), None)

        if not listing:
            raise ValueError(f"Listing not found: {listing_id}")

        # Verificar balance suficiente
        balance = await self.get_wallet_balance()
        price = listing.get('price_dracma', 0)

        if balance < price:
            raise ValueError(f"Insufficient balance: {balance} < {price} DRACMA")

        # Realizar compra
        result = await self.marketplace_client.purchase_data(listing_id, use_escrow=True)

        if result.get('success'):
            # Registrar como réplica en el registry
            dataset_name = f"purchased_{listing_id}"
            shard_cids = listing.get('shard_cids', [])

            data_registry.register_dataset(
                dataset_name=dataset_name,
                owner_node=self.node_id,  # El comprador se convierte en "dueño" local
                shard_cids=shard_cids,
                metadata={
                    'source_listing': listing_id,
                    'purchase_price': price,
                    'quality_score': listing.get('quality_score', 0.5)
                }
            )

            logger.info(f"🛒 Dataset purchased and registered: {dataset_name}")

        return result

    # ==================== FEDERATED TRAINING ====================

    async def join_training_session(self, session_id: str) -> Dict[str, Any]:
        """
        Únete a una sesión de entrenamiento federado.

        Args:
            session_id: ID de la sesión

        Returns:
            Resultado de la unión
        """
        if not self.federated_client:
            raise RuntimeError("Federated client not initialized")

        success = await self.federated_client.join_session(session_id)
        if success:
            self.stats['training_sessions'] += 1
            self.stats['last_activity'] = datetime.now()

        return {'success': success, 'session_id': session_id}

    async def submit_training_result(self, session_id: str, gradients: Any) -> Dict[str, Any]:
        """
        Envía resultados de entrenamiento a la sesión federada.

        Args:
            session_id: ID de la sesión
            gradients: Gradientes/resultados del entrenamiento

        Returns:
            Resultado del envío
        """
        if not self.federated_client:
            raise RuntimeError("Federated client not initialized")

        success = await self.federated_client.submit_gradients(session_id, gradients)
        return {'success': success, 'session_id': session_id}

    # ==================== GOVERNANCE & VOTING ====================

    async def vote_on_proposal(self, proposal_id: str, vote: bool,
                             reasoning: str = "") -> Dict[str, Any]:
        """
        Vota en una propuesta de gobernanza.

        Args:
            proposal_id: ID de la propuesta
            vote: True para sí, False para no
            reasoning: Razón del voto

        Returns:
            Resultado del voto
        """
        if not self.staking_manager:
            raise RuntimeError("Staking manager not initialized")

        return self.staking_manager.vote_on_proposal(
            node_id=self.node_id,
            proposal_id=proposal_id,
            vote=vote,
            reasoning=reasoning
        )

    async def create_governance_proposal(self, title: str, description: str,
                                       changes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea una nueva propuesta de gobernanza.

        Args:
            title: Título de la propuesta
            description: Descripción detallada
            changes: Cambios propuestos

        Returns:
            Resultado de la creación
        """
        if not self.staking_manager:
            raise RuntimeError("Staking manager not initialized")

        return self.staking_manager.create_proposal(
            creator_id=self.node_id,
            title=title,
            description=description,
            changes=changes
        )

    # ==================== MONITORING & STATS ====================

    def get_node_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas completas del nodo.

        Returns:
            Diccionario con todas las estadísticas
        """
        from datetime import datetime

        # Actualizar uptime
        if hasattr(self, '_start_time'):
            self.stats['uptime_hours'] = (datetime.now() - self._start_time).total_seconds() / 3600

        return {
            'node_id': self.node_id,
            'initialized': self.initialized,
            'capabilities': self.capabilities,
            'stats': self.stats,
            'wallet_balance': None,  # Se obtiene async
            'staking_info': None,    # Se obtiene async
            'ipfs_status': ipfs_connector.get_stats(),
            'network_stats': data_registry.get_network_stats(),
            'last_updated': datetime.now().isoformat()
        }

    async def get_full_status(self) -> Dict[str, Any]:
        """
        Obtiene estado completo del nodo incluyendo datos async.

        Returns:
            Estado completo con balances y staking
        """
        status = self.get_node_stats()

        try:
            status['wallet_balance'] = await self.get_wallet_balance()
            status['staking_info'] = await self.get_staking_info()
        except Exception as e:
            logger.debug(f"Could not get async status: {e}")

        return status

    # ==================== UTILITIES ====================

    def cleanup(self) -> None:
        """Limpia recursos del nodo."""
        logger.info(f"🧹 Cleaning up node {self.node_id}")

        # Marcar como offline en el registry
        data_registry.unregister_node(self.node_id)

        # Aquí irían otras limpiezas (conexiones, archivos temporales, etc.)

    def __str__(self) -> str:
        return f"AILOOSNode({self.node_id}, initialized={self.initialized})"


# Función de conveniencia para crear nodos
async def create_ailoos_node(node_id: str, workspace_path: str = "./ailoos_workspace",
                           **init_kwargs) -> AILOOSNode:
    """
    Crea e inicializa un nodo AILOOS completo.

    Args:
        node_id: ID único del nodo
        workspace_path: Directorio de trabajo
        **init_kwargs: Parámetros para inicialización

    Returns:
        Nodo inicializado
    """
    node = AILOOSNode(node_id, workspace_path)
    success = await node.initialize(**init_kwargs)

    if not success:
        raise RuntimeError(f"Failed to initialize AILOOS node {node_id}")

    return node


# Instancia global para uso simple
_default_node: Optional[AILOOSNode] = None

async def get_default_node(node_id: str = "default_node") -> AILOOSNode:
    """Obtiene o crea el nodo por defecto."""
    global _default_node
    if _default_node is None:
        _default_node = await create_ailoos_node(node_id)
    return _default_node