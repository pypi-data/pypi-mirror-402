"""
NodeSDK - Clase principal del SDK de AILOOS para nodos federados
Proporciona una interfaz unificada para todas las funcionalidades del SDK.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime

from ..core.logging import get_logger
from .auth import NodeAuthenticator
from .federated_client import FederatedClient
from .model_manager import ModelManager
from .p2p_client import P2PClient
from .marketplace_client import MarketplaceClient
from .datahub_client import DataHubClient
from .datahub_client import DataHubClient
from .refinery_client import RefineryClient
from .hardware_monitor import HardwareMonitor
from .inference import InferenceEngine

logger = get_logger(__name__)


@dataclass
class NodeConfig:
    """Configuración del nodo SDK."""
    node_id: str
    coordinator_url: str = "http://localhost:5001"
    datahub_url: str = "http://localhost:8001"
    p2p_port: int = 8443
    cert_dir: str = "./certs"
    data_dir: str = "./data"
    models_dir: str = "./models"
    enable_p2p: bool = True
    enable_marketplace: bool = True
    enable_monitoring: bool = True
    heartbeat_interval: int = 30
    max_concurrent_sessions: int = 3


@dataclass
class NodeStatus:
    """Estado actual del nodo."""
    node_id: str
    is_initialized: bool = False
    is_running: bool = False
    active_sessions: List[str] = field(default_factory=list)
    p2p_connected: bool = False
    marketplace_connected: bool = False
    datahub_connected: bool = False
    hardware_info: Dict[str, Any] = field(default_factory=dict)
    last_heartbeat: Optional[datetime] = None
    uptime_seconds: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)


class NodeSDK:
    """
    SDK principal para nodos federados en AILOOS.

    Esta clase proporciona una interfaz unificada para todas las funcionalidades
    necesarias para que un nodo participe en el sistema federado de AILOOS.

    Ejemplo de uso básico:

        # Crear instancia del SDK
        sdk = NodeSDK(node_id="my_node_123")

        # Inicializar
        await sdk.initialize()

        # Unirse a una sesión federada
        await sdk.join_federated_session("session_456")

        # Participar en rondas
        await sdk.participate_in_round(model_weights=my_weights)

        # Cerrar
        await sdk.shutdown()
    """

    def __init__(self, node_id: str, coordinator_url: str = "http://localhost:5001", **kwargs):
        """
        Inicializar el NodeSDK.

        Args:
            node_id: ID único del nodo
            coordinator_url: URL del coordinador
            **kwargs: Configuraciones adicionales (ver NodeConfig)
        """
        self.config = NodeConfig(node_id=node_id, coordinator_url=coordinator_url, **kwargs)
        self.status = NodeStatus(node_id=node_id)

        # Componentes del SDK
        self.auth: Optional[NodeAuthenticator] = None
        self.federated: Optional[FederatedClient] = None
        self.models: Optional[ModelManager] = None
        self.p2p: Optional[P2PClient] = None
        self.marketplace: Optional[MarketplaceClient] = None
        self.datahub: Optional[DataHubClient] = None
        self.refinery: Optional[RefineryClient] = None
        self.monitoring: Optional[HardwareMonitor] = None
        self.inference: Optional[InferenceEngine] = None

        # Estado interno
        self._initialized = False
        self._running = False
        self._shutdown_event = asyncio.Event()

        logger.info(f"🔧 NodeSDK initialized for node {node_id}")

    async def initialize(self) -> bool:
        """
        Inicializar todos los componentes del SDK.

        Returns:
            True si la inicialización fue exitosa
        """
        try:
            if self._initialized:
                logger.warning("NodeSDK already initialized")
                return True

            logger.info(f"🚀 Initializing NodeSDK for node {self.config.node_id}")

            # Inicializar autenticación
            self.auth = NodeAuthenticator(self.config.node_id, self.config.coordinator_url)
            auth_success = await self.auth.initialize()
            if not auth_success:
                logger.error("Failed to initialize authentication")
                return False

            # Inicializar cliente federado
            self.federated = FederatedClient(
                node_id=self.config.node_id,
                coordinator_url=self.config.coordinator_url,
                authenticator=self.auth
            )

            # Inicializar gestor de modelos
            self.models = ModelManager(
                node_id=self.config.node_id,
                models_dir=self.config.models_dir or str(Path.home() / ".ailoos" / "models"),
                coordinator_url=self.config.coordinator_url,
                authenticator=self.auth
            )

            # Inicializar motor de inferencia
            self.inference = InferenceEngine(self.models)

            # Inicializar P2P si está habilitado
            if self.config.enable_p2p:
                self.p2p = P2PClient(
                    node_id=self.config.node_id,
                    port=self.config.p2p_port
                )
                self.p2p.start()
                self.status.p2p_connected = True

            # Inicializar marketplace si está habilitado
            if self.config.enable_marketplace:
                self.marketplace = MarketplaceClient(
                    node_id=self.config.node_id
                )
                marketplace_success = await self.marketplace.initialize()
                self.status.marketplace_connected = marketplace_success

            # Inicializar cliente DataHub
            if self.config.datahub_url:
                self.datahub = DataHubClient(
                    base_url=self.config.datahub_url,
                    authenticator=self.auth
                )
                datahub_success = await self.datahub.initialize()
                self.status.datahub_connected = datahub_success

            # Inicializar cliente de Refinería (Siempre disponible)
            self.refinery = RefineryClient(node_id=self.config.node_id)
            await self.refinery.initialize()

            # Inicializar monitoring si está habilitado
            if self.config.enable_monitoring:
                self.monitoring = HardwareMonitor(self.config.node_id)
                await self.monitoring.initialize()
                self.status.hardware_info = self.monitoring.get_hardware_info()

            # Actualizar estado
            self.status.is_initialized = True
            self._initialized = True

            logger.info(f"✅ NodeSDK initialized successfully for node {self.config.node_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error initializing NodeSDK: {e}")
            self.status.is_initialized = False
            return False

    async def start(self) -> bool:
        """
        Iniciar el nodo y comenzar operaciones.

        Returns:
            True si el inicio fue exitoso
        """
        try:
            if not self._initialized:
                logger.error("NodeSDK not initialized. Call initialize() first")
                return False

            if self._running:
                logger.warning("NodeSDK already running")
                return True

            logger.info(f"▶️ Starting NodeSDK for node {self.config.node_id}")

            # Iniciar componentes
            if self.p2p:
                await self.p2p.start()

            if self.monitoring:
                await self.monitoring.start()

            # Iniciar heartbeat loop
            asyncio.create_task(self._heartbeat_loop())

            self.status.is_running = True
            self._running = True
            self.status.start_time = datetime.now()

            logger.info(f"✅ NodeSDK started successfully for node {self.config.node_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error starting NodeSDK: {e}")
            return False

    async def shutdown(self):
        """Apagar el SDK y limpiar recursos."""
        try:
            if not self._running:
                return

            logger.info(f"⏹️ Shutting down NodeSDK for node {self.config.node_id}")

            self._running = False
            self._shutdown_event.set()

            # Detener componentes en orden inverso
            if self.monitoring:
                await self.monitoring.stop()

            if self.p2p:
                await self.p2p.stop()

            if self.marketplace:
                await self.marketplace.close()

            if self.federated:
                await self.federated.disconnect()

            if self.datahub:
                await self.datahub.close()

            if self.auth:
                await self.auth.close()

            self.status.is_running = False
            logger.info(f"✅ NodeSDK shutdown complete for node {self.config.node_id}")

        except Exception as e:
            logger.error(f"❌ Error shutting down NodeSDK: {e}")

    # ==================== AUTENTICACIÓN ====================

    async def authenticate(self) -> bool:
        """
        Autenticar el nodo con el coordinador.

        Returns:
            True si la autenticación fue exitosa
        """
        if not self.auth:
            return False
        return await self.auth.authenticate()

    def get_auth_token(self) -> Optional[str]:
        """
        Obtener token de autenticación actual.

        Returns:
            Token JWT o None si no está autenticado
        """
        if not self.auth:
            return None
        return self.auth.get_token()

    # ==================== FEDERATED LEARNING ====================

    async def join_federated_session(self, session_id: str) -> bool:
        """
        Unirse a una sesión federada.

        Args:
            session_id: ID de la sesión

        Returns:
            True si se unió exitosamente
        """
        if not self.federated:
            return False

        success = await self.federated.join_session(session_id)
        if success:
            self.status.active_sessions.append(session_id)
        return success

    async def leave_federated_session(self, session_id: str) -> bool:
        """
        Abandonar una sesión federada.

        Args:
            session_id: ID de la sesión

        Returns:
            True si se abandonó exitosamente
        """
        if not self.federated:
            return False

        success = await self.federated.leave_session(session_id)
        if success and session_id in self.status.active_sessions:
            self.status.active_sessions.remove(session_id)
        return success

    async def participate_in_round(self, session_id: str, model_weights: Dict[str, Any],
                                 metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Participar en una ronda de entrenamiento federado.

        Args:
            session_id: ID de la sesión
            model_weights: Pesos del modelo entrenado
            metadata: Metadatos adicionales (accuracy, loss, etc.)

        Returns:
            True si la participación fue exitosa
        """
        if not self.federated:
            return False

        return await self.federated.submit_update(session_id, model_weights, metadata or {})

    async def get_round_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener información de la ronda actual.

        Args:
            session_id: ID de la sesión

        Returns:
            Información de la ronda o None
        """
        if not self.federated:
            return None
        return await self.federated.get_round_info(session_id)

    # ==================== GESTIÓN DE MODELOS ====================

    async def upload_model(self, model_path: str, metadata: Dict[str, Any]) -> Optional[str]:
        """
        Subir un modelo al sistema.

        Args:
            model_path: Ruta al archivo del modelo
            metadata: Metadatos del modelo

        Returns:
            ID del modelo subido o None si falló
        """
        if not self.models:
            return None
        return await self.models.upload_model(model_path, metadata)

    async def download_model(self, model_id: str, save_path: str) -> bool:
        """
        Descargar un modelo del sistema.

        Args:
            model_id: ID del modelo
            save_path: Ruta donde guardar el modelo

        Returns:
            True si la descarga fue exitosa
        """
        if not self.models:
            return False
        return await self.models.download_model(model_id, save_path)

    async def list_available_models(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Listar modelos disponibles.

        Args:
            filters: Filtros opcionales

        Returns:
            Lista de modelos disponibles
        """
        if not self.models:
            return []
        return await self.models.list_models(filters or {})

    # ==================== DATASETS & IPFS ====================

    async def download_dataset_manifest(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """
        Descargar manifiesto IPFS de un dataset via DataHub.

        Args:
            dataset_id: ID del dataset en DataHub

        Returns:
            Dict con el manifiesto o None si falló
        """
        if not self.datahub:
            return None
        try:
            return await self.datahub.download_manifest(dataset_id)
        except Exception as e:
            logger.error(f"❌ Error downloading dataset manifest: {e}")
            return None

    # ==================== COMUNICACIÓN P2P ====================

    async def connect_to_peer(self, peer_address: str, peer_port: int) -> bool:
        """
        Conectar a un peer P2P.

        Args:
            peer_address: Dirección del peer
            peer_port: Puerto del peer

        Returns:
            True si la conexión fue exitosa
        """
        if not self.p2p:
            return False
        return await self.p2p.connect_to_peer(peer_address, peer_port)

    async def send_p2p_message(self, peer_id: str, message: Dict[str, Any]) -> bool:
        """
        Enviar mensaje P2P a un peer.

        Args:
            peer_id: ID del peer destino
            message: Mensaje a enviar

        Returns:
            True si el envío fue exitoso
        """
        if not self.p2p:
            return False
        return await self.p2p.send_message(peer_id, message)

    def get_connected_peers(self) -> List[str]:
        """
        Obtener lista de peers conectados.

        Returns:
            Lista de IDs de peers conectados
        """
        if not self.p2p:
            return []
        return self.p2p.get_connected_peers()

    # ==================== MARKETPLACE ====================

    async def create_data_listing(self, title: str, description: str, data_path: str,
                                price_dracma: float, metadata: Dict[str, Any]) -> Optional[str]:
        """
        Crear un listing de datos en el marketplace.

        Args:
            title: Título del dataset
            description: Descripción
            data_path: Ruta al archivo de datos
            price_dracma: Precio en DRACMA
            metadata: Metadatos adicionales

        Returns:
            ID del listing creado o None
        """
        if not self.marketplace:
            return None
        return await self.marketplace.create_listing(title, description, data_path,
                                                    price_dracma, metadata)

    async def purchase_data(self, listing_id: str) -> bool:
        """
        Comprar un dataset del marketplace.

        Args:
            listing_id: ID del listing

        Returns:
            True si la compra fue exitosa
        """
        if not self.marketplace:
            return False
        return await self.marketplace.purchase_data(listing_id)

    # ==================== INFERENCIA ====================

    def generate(self, model_id: str, prompt: str, max_length: int = 50, 
                temperature: float = 0.7, top_k: int = 50) -> Dict[str, Any]:
        """
        Generar texto usando un modelo local.
        
        Args:
            model_id: ID del modelo (debe estar descargado)
            prompt: Prompt de entrada
            max_length: Longitud máxima de generación
            
        Returns:
            Dict con texto generado o error
        """
        if not self.inference:
            return {"error": "Inference engine not initialized"}
        return self.inference.generate(model_id, prompt, max_length, temperature, top_k)

    async def get_wallet_balance(self) -> float:
        """
        Obtener balance de la wallet DRACMA.

        Returns:
            Balance en DRACMA
        """
        if not self.marketplace:
            return 0.0
        return await self.marketplace.get_balance()

    async def search_datasets(self, query: str = "", **filters) -> List[Dict[str, Any]]:
        """
        Buscar datasets en el marketplace.

        Args:
            query: Término de búsqueda
            **filters: Filtros adicionales

        Returns:
            Lista de datasets encontrados
        """
        if not self.marketplace:
            return []
        return await self.marketplace.search_datasets(query, **filters)

    # ==================== MONITORING ====================

    def get_hardware_info(self) -> Dict[str, Any]:
        """
        Obtener información del hardware.

        Returns:
            Información del hardware
        """
        if not self.monitoring:
            return {}
        return self.monitoring.get_hardware_info()

    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Obtener métricas del sistema.

        Returns:
            Métricas actuales del sistema
        """
        if not self.monitoring:
            return {}
        return self.monitoring.get_current_metrics()

    async def get_performance_report(self) -> Dict[str, Any]:
        """
        Obtener reporte de rendimiento.

        Returns:
            Reporte completo de rendimiento
        """
        if not self.monitoring:
            return {}
        return await self.monitoring.generate_report()

    # ==================== ESTADO Y DIAGNÓSTICO ====================

    def get_status(self) -> Dict[str, Any]:
        """
        Obtener estado completo del nodo.

        Returns:
            Estado completo del nodo
        """
        # Actualizar uptime
        if self.status.start_time:
            self.status.uptime_seconds = (datetime.now() - self.status.start_time).total_seconds()

        return {
            "node_id": self.status.node_id,
            "is_initialized": self.status.is_initialized,
            "is_running": self.status.is_running,
            "active_sessions": self.status.active_sessions.copy(),
            "p2p_connected": self.status.p2p_connected,
            "marketplace_connected": self.status.marketplace_connected,
            "datahub_connected": self.status.datahub_connected,
            "hardware_info": self.status.hardware_info.copy(),
            "last_heartbeat": self.status.last_heartbeat.isoformat() if self.status.last_heartbeat else None,
            "uptime_seconds": self.status.uptime_seconds,
            "config": {
                "coordinator_url": self.config.coordinator_url,
                "p2p_port": self.config.p2p_port,
                "enable_p2p": self.config.enable_p2p,
                "enable_marketplace": self.config.enable_marketplace,
                "enable_monitoring": self.config.enable_monitoring
            }
        }

    async def run_diagnostics(self) -> Dict[str, Any]:
        """
        Ejecutar diagnósticos del sistema.

        Returns:
            Resultados de los diagnósticos
        """
        diagnostics = {
            "timestamp": datetime.now().isoformat(),
            "node_id": self.config.node_id,
            "checks": {}
        }

        # Verificar inicialización
        diagnostics["checks"]["initialization"] = self._initialized

        # Verificar componentes
        diagnostics["checks"]["auth"] = self.auth is not None and await self.auth.is_authenticated()
        diagnostics["checks"]["federated"] = self.federated is not None
        diagnostics["checks"]["models"] = self.models is not None
        diagnostics["checks"]["p2p"] = self.p2p is not None and self.status.p2p_connected
        diagnostics["checks"]["marketplace"] = self.marketplace is not None and self.status.marketplace_connected
        diagnostics["checks"]["monitoring"] = self.monitoring is not None

        # Verificar conectividad
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.config.coordinator_url}/health", timeout=5) as response:
                    diagnostics["checks"]["coordinator_reachable"] = response.status == 200
        except:
            diagnostics["checks"]["coordinator_reachable"] = False

        # Métricas de rendimiento
        if self.monitoring:
            diagnostics["performance"] = await self.monitoring.generate_report()

        return diagnostics

    # ==================== UTILIDADES INTERNAS ====================

    async def _heartbeat_loop(self):
        """Loop de heartbeat periódico."""
        while self._running and not self._shutdown_event.is_set():
            try:
                # Enviar heartbeat
                await self._send_heartbeat()

                # Esperar intervalo
                await asyncio.sleep(self.config.heartbeat_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(5)

    async def _send_heartbeat(self):
        """Enviar heartbeat al coordinador."""
        try:
            if not self.auth or not await self.auth.is_authenticated():
                return

            # Recopilar métricas
            metrics = {}
            if self.monitoring:
                metrics = self.monitoring.get_current_metrics()

            # Enviar heartbeat
            payload = {
                "node_id": self.config.node_id,
                "timestamp": datetime.now().isoformat(),
                "status": "active" if self._running else "inactive",
                "active_sessions": self.status.active_sessions,
                "metrics": metrics
            }

            # Aquí iría la llamada HTTP al coordinador
            # Por ahora solo actualizamos el estado local
            self.status.last_heartbeat = datetime.now()

        except Exception as e:
            logger.debug(f"Heartbeat failed: {e}")


# Funciones de conveniencia

async def create_node_sdk(node_id: str, **kwargs) -> NodeSDK:
    """
    Crear e inicializar una instancia del NodeSDK.

    Args:
        node_id: ID único del nodo
        **kwargs: Configuraciones adicionales

    Returns:
        Instancia inicializada del NodeSDK
    """
    sdk = NodeSDK(node_id, **kwargs)
    success = await sdk.initialize()
    if not success:
        raise RuntimeError(f"Failed to initialize NodeSDK for node {node_id}")
    return sdk


def get_node_sdk_status(sdk: NodeSDK) -> Dict[str, Any]:
    """
    Obtener estado formateado del SDK.

    Args:
        sdk: Instancia del NodeSDK

    Returns:
        Estado formateado
    """
    return sdk.get_status()
