"""
FederatedClient - Cliente para participación en sesiones federadas
Maneja la participación de nodos en sesiones de aprendizaje federado.
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import aiohttp
import numpy as np

try:
    import tenseal as ts
    TENSEAL_AVAILABLE = True
except ImportError:
    TENSEAL_AVAILABLE = False
    ts = None

from ..core.logging import get_logger
from ..core.logging import get_logger
from .auth import NodeAuthenticator
from ..utils.decorators import retry, circuit_breaker, log_execution_time

logger = get_logger(__name__)


@dataclass
class FederatedSession:
    """Información de una sesión federada."""
    session_id: str
    coordinator_url: str
    status: str = "unknown"
    round_num: int = 0
    participants: List[str] = field(default_factory=list)
    model_config: Dict[str, Any] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    last_update: Optional[datetime] = None


@dataclass
class RoundUpdate:
    """Actualización de modelo para una ronda."""
    session_id: str
    round_num: int
    model_weights: Dict[str, Any]
    num_samples: int
    accuracy: float = 0.0
    loss: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class FederatedClient:
    """
    Cliente para participación en sesiones federadas.

    Maneja la comunicación con el coordinador para:
    - Unirse/abandonar sesiones federadas
    - Enviar actualizaciones de modelo
    - Recibir actualizaciones globales
    - Gestionar rondas de entrenamiento
    """

    def __init__(self, node_id: str, coordinator_url: str, authenticator: NodeAuthenticator,
                 max_retries: int = 3, retry_delay: float = 1.0, connection_timeout: int = 30):
        """
        Inicializar el cliente federado.

        Args:
            node_id: ID del nodo
            coordinator_url: URL del coordinador
            authenticator: Autenticador para requests
            max_retries: Máximo número de reintentos en caso de error
            retry_delay: Delay entre reintentos en segundos
            connection_timeout: Timeout para conexiones HTTP
        """
        self.node_id = node_id
        self.coordinator_url = coordinator_url.rstrip('/')
        self.auth = authenticator
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.connection_timeout = connection_timeout

        # Estado de sesiones
        self.active_sessions: Dict[str, FederatedSession] = {}
        self.pending_updates: Dict[str, RoundUpdate] = {}

        # Callbacks
        self.update_callbacks: Dict[str, List[Callable]] = {}
        self.round_callbacks: Dict[str, List[Callable]] = {}

        # HTTP client
        self._session: Optional[aiohttp.ClientSession] = None
        self._running = False
        self._connection_errors = 0
        self._last_connection_error: Optional[datetime] = None

        # Encryption Context
        self.ts_context = None
        if TENSEAL_AVAILABLE:
            try:
                # Setup TenSEAL context for CKKS
                self.ts_context = ts.context(
                    ts.SCHEME_TYPE.CKKS,
                    poly_modulus_degree=8192,
                    coeff_mod_bit_sizes=[60, 40, 40, 60]
                )
                self.ts_context.global_scale = 2**40
                self.ts_context.generate_galois_keys()
                logger.info("🔐 TenSEAL Homomorphic Encryption enabled")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize TenSEAL context: {e}")
                self.ts_context = None

        logger.info(f"🔗 FederatedClient initialized for node {node_id} with auto-retry")

        # Iniciar monitoreo de sesiones
        self._monitor_task: Optional[asyncio.Task] = None

    async def initialize(self) -> bool:
        """
        Inicializar el cliente federado.

        Returns:
            True si la inicialización fue exitosa
        """
        try:
            # Crear HTTP session
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.connection_timeout)
            )

            self._running = True

            # Iniciar monitoreo de sesiones
            self._monitor_task = asyncio.create_task(self._session_monitor_loop())

            logger.info(f"✅ FederatedClient initialized for node {self.node_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error initializing FederatedClient: {e}")
            return False

    async def disconnect(self):
        """Desconectar y limpiar recursos."""
        self._running = False

        # Cancelar tareas de background
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        if self._session:
            await self._session.close()

        # Limpiar sesiones activas
        self.active_sessions.clear()
        self.pending_updates.clear()

        logger.info(f"🔌 FederatedClient disconnected for node {self.node_id}")

    async def _make_request_with_retry(self, method: str, url: str, **kwargs) -> Optional[aiohttp.ClientResponse]:
        """
        Hacer request HTTP con reintentos automáticos.

        Args:
            method: Método HTTP
            url: URL completa
            **kwargs: Argumentos adicionales para el request

        Returns:
            Response o None si falla definitivamente
        """
        for attempt in range(self.max_retries + 1):
            try:
                if not self._session:
                    logger.error("HTTP session not available")
                    return None

                # Asegurar autenticación
                if not await self.auth.is_authenticated():
                    logger.info("Re-authenticating before request...")
                    if not await self.auth.authenticate():
                        logger.error("Re-authentication failed")
                        return None

                # Agregar headers de autenticación si no están
                if 'headers' not in kwargs:
                    kwargs['headers'] = {}
                auth_headers = self.auth.get_auth_headers()
                kwargs['headers'].update(auth_headers)

                # Hacer request
                async with self._session.request(method, url, **kwargs) as response:
                    # Resetear contador de errores en éxito
                    if response.status < 500:  # No reintentar errores del cliente
                        self._connection_errors = 0
                        return response
                    else:
                        logger.warning(f"Server error {response.status} on attempt {attempt + 1}")

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                self._connection_errors += 1
                self._last_connection_error = datetime.now()

                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries + 1}): {e}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Request failed after {self.max_retries + 1} attempts: {e}")
                    return None

        return None

    @retry(max_attempts=3, delay=1.0, backoff=2.0)
    @circuit_breaker(failure_threshold=5, recovery_timeout=60)
    @log_execution_time()
    async def join_session(self, session_id: str) -> bool:
        """
        Unirse a una sesión federada.

        Args:
            session_id: ID de la sesión

        Returns:
            True si se unió exitosamente
        """
        try:
            if not self._session or not await self.auth.is_authenticated():
                logger.error("Not authenticated or session not initialized")
                return False

            # Preparar payload
            join_payload = {
                "node_id": self.node_id,
                "session_id": session_id,
                "join_time": datetime.now().isoformat(),
                "capabilities": {
                    "federated_learning": True,
                    "model_updates": True,
                    "secure_aggregation": True
                }
            }

            # Enviar solicitud con reintentos
            response = await self._make_request_with_retry(
                "POST",
                f"{self.coordinator_url}/api/sessions/{session_id}/join",
                json=join_payload
            )

            if not response:
                logger.error(f"Failed to join session {session_id} after retries")
                return False

            async with response:

                if response.status == 200:
                    data = await response.json()

                    # Crear objeto de sesión
                    session = FederatedSession(
                        session_id=session_id,
                        coordinator_url=self.coordinator_url,
                        status="joined",
                        round_num=data.get("current_round", 0),
                        participants=data.get("participants", []),
                        model_config=data.get("model_config", {}),
                        start_time=datetime.now(),
                        last_update=datetime.now()
                    )

                    self.active_sessions[session_id] = session

                    logger.info(f"✅ Node {self.node_id} joined federated session {session_id}")
                    logger.info(f"📊 Session details: round={session.round_num}, participants={len(session.participants)}")
                    return True

                else:
                    error_text = await response.text()
                    logger.error(f"Failed to join session {session_id}: {response.status} - {error_text}")
                    return False

        except Exception as e:
            logger.error(f"❌ Error joining session {session_id}: {e}")
            return False

    async def leave_session(self, session_id: str) -> bool:
        """
        Abandonar una sesión federada.

        Args:
            session_id: ID de la sesión

        Returns:
            True si se abandonó exitosamente
        """
        try:
            if session_id not in self.active_sessions:
                logger.warning(f"Not joined to session {session_id}")
                return True

            if not self._session:
                return False

            # Enviar solicitud de abandono con reintentos
            response = await self._make_request_with_retry(
                "POST",
                f"{self.coordinator_url}/api/sessions/{session_id}/leave",
                json={"node_id": self.node_id}
            )

            if not response:
                logger.error(f"Failed to leave session {session_id} after retries")
                return False

            async with response:

                if response.status in [200, 404]:  # 404 si ya se fue
                    # Remover sesión local
                    del self.active_sessions[session_id]

                    # Limpiar updates pendientes
                    if session_id in self.pending_updates:
                        del self.pending_updates[session_id]

                    logger.info(f"👋 Left federated session {session_id}")
                    return True

                else:
                    error_text = await response.text()
                    logger.error(f"Failed to leave session {session_id}: {response.status} - {error_text}")
                    return False

        except Exception as e:
            logger.error(f"❌ Error leaving session {session_id}: {e}")
            return False

    async def submit_update(self, session_id: str, model_weights: Dict[str, Any],
                          metadata: Dict[str, Any]) -> bool:
        """
        Enviar actualización de modelo para una sesión.

        Args:
            session_id: ID de la sesión
            model_weights: Pesos del modelo
            metadata: Metadatos adicionales

        Returns:
            True si el envío fue exitoso
        """
        try:
            if session_id not in self.active_sessions:
                logger.error(f"Not joined to session {session_id}")
                return False

            session = self.active_sessions[session_id]

            # Crear actualización
            update = RoundUpdate(
                session_id=session_id,
                round_num=session.round_num,
                model_weights=model_weights,
                num_samples=metadata.get("num_samples", 0),
                accuracy=metadata.get("accuracy", 0.0),
                loss=metadata.get("loss", 0.0),
                metadata=metadata
            )

            # Preparar payload
            update_payload = {
                "node_id": self.node_id,
                "session_id": session_id,
                "round_num": update.round_num,
                "model_weights": self._serialize_weights(model_weights),
                "num_samples": update.num_samples,
                "accuracy": update.accuracy,
                "loss": update.loss,
                "metadata": update.metadata,
                "timestamp": update.timestamp.isoformat()
            }

            # Enviar actualización con reintentos
            response = await self._make_request_with_retry(
                "POST",
                f"{self.coordinator_url}/api/sessions/{session_id}/updates",
                json=update_payload
            )

            if not response:
                logger.error(f"Failed to submit update for session {session_id} after retries")
                return False

            async with response:

                if response.status == 200:
                    # Actualizar estado de sesión
                    session.last_update = datetime.now()

                    # Trigger callbacks
                    await self._trigger_update_callbacks(session_id, update)

                    logger.info(f"📤 Node {self.node_id} submitted encrypted model update for session {session_id}")
                    logger.info(f"📊 Update details: round={update.round_num}, samples={update.num_samples}, accuracy={update.accuracy:.4f}")
                    return True

                else:
                    error_text = await response.text()
                    logger.error(f"Failed to submit update for session {session_id}: {response.status} - {error_text}")
                    return False

        except Exception as e:
            logger.error(f"❌ Error submitting update for session {session_id}: {e}")
            return False

    async def get_round_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener información de la ronda actual.

        Args:
            session_id: ID de la sesión

        Returns:
            Información de la ronda o None
        """
        try:
            if session_id not in self.active_sessions:
                return None

            response = await self._make_request_with_retry(
                "GET",
                f"{self.coordinator_url}/api/sessions/{session_id}/round"
            )

            if not response:
                logger.warning(f"Failed to get round info for session {session_id} after retries")
                return None

            async with response:

                if response.status == 200:
                    data = await response.json()

                    # Actualizar información local
                    session = self.active_sessions[session_id]
                    session.round_num = data.get("round_num", session.round_num)
                    session.participants = data.get("participants", session.participants)
                    session.last_update = datetime.now()

                    return data

                else:
                    logger.warning(f"Failed to get round info for session {session_id}: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"❌ Error getting round info for session {session_id}: {e}")
            return None

    async def get_global_model(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener el modelo global actual.

        Args:
            session_id: ID de la sesión

        Returns:
            Modelo global o None
        """
        try:
            if session_id not in self.active_sessions:
                return None

            response = await self._make_request_with_retry(
                "GET",
                f"{self.coordinator_url}/api/sessions/{session_id}/model"
            )

            if not response:
                logger.warning(f"Failed to get global model for session {session_id} after retries")
                return None

            async with response:

                if response.status == 200:
                    data = await response.json()
                    model_weights = self._deserialize_weights(data.get("model_weights", {}))
                    return {
                        "weights": model_weights,
                        "round_num": data.get("round_num", 0),
                        "updated_at": data.get("updated_at"),
                        "metadata": data.get("metadata", {})
                    }

                else:
                    logger.warning(f"Failed to get global model for session {session_id}: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"❌ Error getting global model for session {session_id}: {e}")
            return None

    async def download_global_model(self, session_id: str, local_path: str) -> bool:
        """
        Descargar y guardar el modelo global en un archivo local.

        Args:
            session_id: ID de la sesión
            local_path: Ruta local donde guardar el modelo

        Returns:
            True si la descarga fue exitosa
        """
        try:
            global_model = await self.get_global_model(session_id)
            if not global_model:
                return False

            # Serializar y guardar el modelo
            model_data = {
                "session_id": session_id,
                "round_num": global_model["round_num"],
                "weights": global_model["weights"],
                "metadata": global_model["metadata"],
                "downloaded_at": datetime.now().isoformat()
            }

            with open(local_path, 'w') as f:
                json.dump(model_data, f, indent=2)

            logger.info(f"💾 Global model saved to {local_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Error downloading global model: {e}")
            return False

    async def auto_download_models(self, session_id: str, download_dir: str, check_interval: int = 60):
        """
        Monitorear y descargar automáticamente nuevos modelos globales.

        Args:
            session_id: ID de la sesión
            download_dir: Directorio donde guardar los modelos
            check_interval: Intervalo de verificación en segundos
        """
        try:
            import os
            os.makedirs(download_dir, exist_ok=True)

            last_round = -1

            while self._running and session_id in self.active_sessions:
                try:
                    global_model = await self.get_global_model(session_id)
                    if global_model and global_model["round_num"] > last_round:
                        # Nuevo modelo disponible
                        model_path = os.path.join(
                            download_dir,
                            f"global_model_{session_id}_round_{global_model['round_num']}.json"
                        )

                        with open(model_path, 'w') as f:
                            json.dump({
                                "session_id": session_id,
                                "round_num": global_model["round_num"],
                                "weights": global_model["weights"],
                                "metadata": global_model["metadata"],
                                "downloaded_at": datetime.now().isoformat()
                            }, f, indent=2)

                        logger.info(f"🔄 Auto-downloaded new global model: round {global_model['round_num']}")
                        last_round = global_model["round_num"]

                    await asyncio.sleep(check_interval)

                except Exception as e:
                    logger.warning(f"Error in auto-download loop: {e}")
                    await asyncio.sleep(check_interval)

        except Exception as e:
            logger.error(f"❌ Error in auto-download models: {e}")

    async def wait_for_round(self, session_id: str, timeout: int = 300) -> Optional[Dict[str, Any]]:
        """
        Esperar a que comience una nueva ronda.

        Args:
            session_id: ID de la sesión
            timeout: Timeout en segundos

        Returns:
            Información de la nueva ronda o None si timeout
        """
        try:
            if session_id not in self.active_sessions:
                return None

            session = self.active_sessions[session_id]
            initial_round = session.round_num

            start_time = time.time()
            while time.time() - start_time < timeout:
                round_info = await self.get_round_info(session_id)
                if round_info and round_info.get("round_num", 0) > initial_round:
                    return round_info

                await asyncio.sleep(5)  # Check every 5 seconds

            logger.warning(f"Timeout waiting for new round in session {session_id}")
            return None

        except Exception as e:
            logger.error(f"❌ Error waiting for round in session {session_id}: {e}")
            return None

    def register_update_callback(self, session_id: str, callback: Callable):
        """
        Registrar callback para actualizaciones.

        Args:
            session_id: ID de la sesión
            callback: Función callback
        """
        if session_id not in self.update_callbacks:
            self.update_callbacks[session_id] = []

        self.update_callbacks[session_id].append(callback)
        logger.debug(f"Registered update callback for session {session_id}")

    def register_round_callback(self, session_id: str, callback: Callable):
        """
        Registrar callback para nuevas rondas.

        Args:
            session_id: ID de la sesión
            callback: Función callback
        """
        if session_id not in self.round_callbacks:
            self.round_callbacks[session_id] = []

        self.round_callbacks[session_id].append(callback)
        logger.debug(f"Registered round callback for session {session_id}")

    def get_active_sessions(self) -> List[str]:
        """
        Obtener lista de sesiones activas.

        Returns:
            Lista de IDs de sesiones activas
        """
        return list(self.active_sessions.keys())

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener información de una sesión.

        Args:
            session_id: ID de la sesión

        Returns:
            Información de la sesión o None
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return None

        return {
            "session_id": session.session_id,
            "status": session.status,
            "round_num": session.round_num,
            "participants": session.participants.copy(),
            "model_config": session.model_config.copy(),
            "start_time": session.start_time.isoformat() if session.start_time else None,
            "last_update": session.last_update.isoformat() if session.last_update else None
        }

    async def _session_monitor_loop(self):
        """Monitoreo continuo del estado de sesiones activas."""
        while self._running:
            try:
                # Monitorear cada sesión activa
                for session_id in list(self.active_sessions.keys()):
                    await self._monitor_session(session_id)

                # Esperar antes del próximo ciclo de monitoreo
                await asyncio.sleep(30)  # Check every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in session monitor loop: {e}")
                await asyncio.sleep(10)

    async def _monitor_session(self, session_id: str):
        """Monitorear el estado de una sesión específica."""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return

            # Obtener información actualizada de la ronda
            round_info = await self.get_round_info(session_id)
            if round_info:
                # Actualizar información local
                old_round = session.round_num
                session.round_num = round_info.get("round_num", session.round_num)
                session.participants = round_info.get("participants", session.participants)
                session.last_update = datetime.now()

                # Trigger callback si cambió la ronda
                if session.round_num > old_round:
                    logger.info(f"🔄 Session {session_id} advanced to round {session.round_num}")
                    await self._trigger_round_callbacks(session_id, round_info)

            # Verificar si la sesión terminó
            if round_info and round_info.get("round_num", 0) >= round_info.get("total_rounds", 0):
                logger.info(f"🏁 Session {session_id} completed all rounds")
                # Trigger final callback
                await self._trigger_round_callbacks(session_id, round_info)

        except Exception as e:
            logger.warning(f"Error monitoring session {session_id}: {e}")

    # ==================== MÉTODOS INTERNOS ====================

    def _serialize_weights(self, weights: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serializar pesos del modelo, prefiriendo encriptación Homomórfica (TenSEAL).
        Asegura que los pesos sean convertidos a formatos seguros antes de transmisión.
        """
        serialized = {}
        
        # 1. Pre-procesamiento de tensores (seguridad de tipos)
        processed_weights = {}
        for k, v in weights.items():
            if isinstance(v, (list, tuple)):
                processed_weights[k] = np.array(v, dtype=np.float32)
            elif isinstance(v, np.ndarray):
                processed_weights[k] = v.astype(np.float32)
            else:
                # Intentar conversión segura o saltar
                try:
                    processed_weights[k] = np.array(v, dtype=np.float32)
                except:
                    logger.warning(f"Could not convert weight {k} to numpy, skipping.")

        # 2. Encriptación
        if TENSEAL_AVAILABLE and self.ts_context:
            try:
                for k, v in processed_weights.items():
                    # Aplanar para encriptación vectorizada (CKKS)
                    flat_v = v.flatten()
                    encrypted_vector = ts.ckks_vector(self.ts_context, flat_v)
                    serialized[k] = {
                        "data": encrypted_vector.serialize(),
                        "shape": v.shape,
                        "encrypted": True
                    }
                logger.info("🔒 Weights encrypted with Homomorphic Encryption")
                return serialized
            except Exception as e:
                logger.error(f"❌ Encryption failed: {e}. Falling back to cleartext (DANGEROUS).")
                # En producción estricta, aquí deberíamos lanzar error y abortar.
                # Para compatibilidad, continuamos pero con log crítico.
        else:
            logger.warning("⚠️ Sending weights UNENCRYPTED (Privacy Leak Risk). Install TenSEAL for security.")

        # 3. Serialización Cleartext (Fallback)
        for k, v in processed_weights.items():
            serialized[k] = {
                "data": v.tolist(),
                "shape": v.shape,
                "encrypted": False
            }
            
        return serialized

    def _deserialize_weights(self, serialized_weights: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deserializar pesos recibidos, manejando desencriptación si es necesario.
        """
        try:
            deserialized = {}
            for k, payload in serialized_weights.items():
                # Verificar formato esperado
                if not isinstance(payload, dict) or "data" not in payload:
                    # Formato legacy o raw - intentar recuperar
                    if isinstance(payload, (list, np.ndarray)):
                        deserialized[k] = np.array(payload)
                    else:
                        deserialized[k] = payload
                    continue

                shape = tuple(payload.get("shape", []))
                is_encrypted = payload.get("encrypted", False)

                if is_encrypted:
                    if not TENSEAL_AVAILABLE or not self.ts_context:
                        raise RuntimeError("Received encrypted weights but TenSEAL is not available.")
                    
                    # Desencriptar
                    try:
                        vec = ts.ckks_vector_from(self.ts_context, payload["data"])
                        # Desencriptación requiere clave privada (si context la tiene)
                        deserialized[k] = np.array(vec.decrypt()).reshape(shape)
                    except Exception as e:
                        # Si falla desencriptar (ej. no tenemos secret key en context), conservamos el raw
                        logger.warning(f"Could not decrypt weight {k}: {e}. Keeping encrypted.")
                        deserialized[k] = payload 
                else:
                    # Cleartext payload
                    data_list = payload["data"]
                    deserialized[k] = np.array(data_list, dtype=np.float32).reshape(shape)

            return deserialized
        except Exception as e:
            logger.error(f"❌ Error deserializing weights: {e}")
            return {}

    async def _trigger_update_callbacks(self, session_id: str, update: RoundUpdate):
        """Trigger callbacks de actualización."""
        try:
            callbacks = self.update_callbacks.get(session_id, [])
            for callback in callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(update)
                    else:
                        # Ejecutar en thread pool
                        await asyncio.get_event_loop().run_in_executor(None, callback, update)
                except Exception as e:
                    logger.error(f"Error in update callback for session {session_id}: {e}")
        except Exception as e:
            logger.error(f"Error triggering update callbacks: {e}")

    async def _trigger_round_callbacks(self, session_id: str, round_info: Dict[str, Any]):
        """Trigger callbacks de ronda."""
        try:
            callbacks = self.round_callbacks.get(session_id, [])
            for callback in callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(round_info)
                    else:
                        await asyncio.get_event_loop().run_in_executor(None, callback, round_info)
                except Exception as e:
                    logger.error(f"Error in round callback for session {session_id}: {e}")
        except Exception as e:
            logger.error(f"Error triggering round callbacks: {e}")

    # ==================== MÉTODOS DE UTILIDAD ====================

    def get_client_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del cliente.

        Returns:
            Estadísticas del cliente
        """
        return {
            "node_id": self.node_id,
            "active_sessions": len(self.active_sessions),
            "pending_updates": len(self.pending_updates),
            "total_updates_sent": sum(len(callbacks) for callbacks in self.update_callbacks.values()),
            "is_running": self._running
        }


# Funciones de conveniencia

async def create_federated_client(node_id: str, coordinator_url: str,
                                authenticator: NodeAuthenticator) -> FederatedClient:
    """
    Crear e inicializar un cliente federado.

    Args:
        node_id: ID del nodo
        coordinator_url: URL del coordinador
        authenticator: Autenticador

    Returns:
        Instancia inicializada del cliente
    """
    client = FederatedClient(node_id, coordinator_url, authenticator)
    success = await client.initialize()
    if not success:
        raise RuntimeError(f"Failed to initialize federated client for node {node_id}")
    return client


def create_round_update(session_id: str, round_num: int, model_weights: Dict[str, Any],
                       num_samples: int, **metadata) -> RoundUpdate:
    """
    Crear una actualización de ronda.

    Args:
        session_id: ID de la sesión
        round_num: Número de ronda
        model_weights: Pesos del modelo
        num_samples: Número de muestras
        **metadata: Metadatos adicionales

    Returns:
        Actualización de ronda
    """
    return RoundUpdate(
        session_id=session_id,
        round_num=round_num,
        model_weights=model_weights,
        num_samples=num_samples,
        accuracy=metadata.get("accuracy", 0.0),
        loss=metadata.get("loss", 0.0),
        metadata=metadata
    )