import asyncio
import logging
from typing import Optional, List, Dict, Any
from nio import AsyncClient, LoginResponse, RoomCreateResponse, RoomInviteResponse, RoomJoinResponse, SendResponse, SyncResponse
from nio.crypto import OlmDevice
from nio.exceptions import OlmUnverifiedDeviceError

logger = logging.getLogger(__name__)

class MatrixClient:
    def __init__(self, homeserver: str, user_id: str, password: str, device_id: Optional[str] = None):
        self.homeserver = homeserver
        self.user_id = user_id
        self.password = password
        self.device_id = device_id
        self.client: Optional[AsyncClient] = None
        self._sync_task: Optional[asyncio.Task] = None
        self._message_callbacks: List[callable] = []

    async def connect(self) -> bool:
        """Conectar al servidor Matrix y autenticar."""
        try:
            self.client = AsyncClient(self.homeserver, self.user_id, device_id=self.device_id)
            login_response = await self.client.login(self.password)
            if isinstance(login_response, LoginResponse):
                logger.info(f"Conectado a Matrix como {self.user_id}")
                # Iniciar sincronización para recibir mensajes
                self._sync_task = asyncio.create_task(self._sync_loop())
                return True
            else:
                logger.error(f"Error de login: {login_response}")
                return False
        except Exception as e:
            logger.error(f"Error conectando a Matrix: {e}")
            return False

    async def disconnect(self):
        """Desconectar del servidor Matrix."""
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        if self.client:
            await self.client.close()
            logger.info("Desconectado de Matrix")

    async def _sync_loop(self):
        """Bucle de sincronización para recibir mensajes."""
        try:
            while True:
                sync_response = await self.client.sync(timeout=30000)
                if isinstance(sync_response, SyncResponse):
                    await self._process_sync_response(sync_response)
                else:
                    logger.error(f"Error en sync: {sync_response}")
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Sync loop cancelado")
        except Exception as e:
            logger.error(f"Error en sync loop: {e}")

    async def _process_sync_response(self, sync_response: SyncResponse):
        """Procesar respuesta de sync para manejar mensajes."""
        for room_id, room_info in sync_response.rooms.join.items():
            for event in room_info.timeline.events:
                if event.type == "m.room.message":
                    for callback in self._message_callbacks:
                        await callback(room_id, event.sender, event.content.get("body", ""))

    def add_message_callback(self, callback: callable):
        """Agregar callback para mensajes entrantes."""
        self._message_callbacks.append(callback)

    async def send_message(self, room_id: str, message: str) -> bool:
        """Enviar mensaje a un room."""
        try:
            response = await self.client.room_send(
                room_id=room_id,
                message_type="m.room.message",
                content={"msgtype": "m.text", "body": message}
            )
            if isinstance(response, SendResponse):
                logger.info(f"Mensaje enviado a {room_id}")
                return True
            else:
                logger.error(f"Error enviando mensaje: {response}")
                return False
        except Exception as e:
            logger.error(f"Error enviando mensaje: {e}")
            return False

    async def create_room(self, name: str, topic: Optional[str] = None, is_public: bool = False) -> Optional[str]:
        """Crear un nuevo room."""
        try:
            visibility = "public" if is_public else "private"
            response = await self.client.room_create(
                name=name,
                topic=topic,
                visibility=visibility
            )
            if isinstance(response, RoomCreateResponse):
                logger.info(f"Room creado: {response.room_id}")
                return response.room_id
            else:
                logger.error(f"Error creando room: {response}")
                return None
        except Exception as e:
            logger.error(f"Error creando room: {e}")
            return None

    async def join_room(self, room_id_or_alias: str) -> bool:
        """Unirse a un room."""
        try:
            response = await self.client.join(room_id_or_alias)
            if isinstance(response, RoomJoinResponse):
                logger.info(f"Unido a room: {room_id_or_alias}")
                return True
            else:
                logger.error(f"Error uniendo a room: {response}")
                return False
        except Exception as e:
            logger.error(f"Error uniendo a room: {e}")
            return False

    async def invite_to_room(self, room_id: str, user_id: str) -> bool:
        """Invitar usuario a room."""
        try:
            response = await self.client.room_invite(room_id, user_id)
            if isinstance(response, RoomInviteResponse):
                logger.info(f"Usuario {user_id} invitado a {room_id}")
                return True
            else:
                logger.error(f"Error invitando: {response}")
                return False
        except Exception as e:
            logger.error(f"Error invitando: {e}")
            return False

    async def list_rooms(self) -> List[str]:
        """Listar rooms unidos."""
        if not self.client:
            return []
        return list(self.client.rooms.keys())

    async def enable_e2e_encryption(self, room_id: str) -> bool:
        """Habilitar encriptación E2E en un room."""
        try:
            # Matrix habilita E2E automáticamente si los dispositivos lo soportan
            # Aquí podemos verificar o forzar
            response = await self.client.room_send(
                room_id=room_id,
                message_type="m.room.encryption",
                content={
                    "algorithm": "m.megolm.v1.aes-sha2",
                    "rotation_period_ms": 604800000,
                    "rotation_period_msgs": 100
                }
            )
            if isinstance(response, SendResponse):
                logger.info(f"Encriptación E2E habilitada en {room_id}")
                return True
            else:
                logger.error(f"Error habilitando E2E: {response}")
                return False
        except Exception as e:
            logger.error(f"Error habilitando E2E: {e}")
            return False

    async def verify_device(self, user_id: str, device_id: str) -> bool:
        """Verificar dispositivo para E2E."""
        try:
            # Implementación simplificada; en producción, usar UI para verificación
            await self.client.verify_device(user_id, device_id)
            logger.info(f"Dispositivo {device_id} de {user_id} verificado")
            return True
        except Exception as e:
            logger.error(f"Error verificando dispositivo: {e}")
            return False