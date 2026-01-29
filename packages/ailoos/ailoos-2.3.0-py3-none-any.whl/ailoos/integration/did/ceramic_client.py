import json
import logging
from datetime import datetime
import ipfshttpclient
from typing import Dict, Any, Optional

class CeramicClient:
    """
    Cliente para gestión de perfiles de usuario usando Ceramic Network.
    Proporciona métodos para crear y verificar perfiles DID almacenados en IPFS.
    """

    def __init__(self, ceramic_url: str, ipfs_url: str = '/ip4/127.0.0.1/tcp/5001/http'):
        """
        Inicializa el cliente Ceramic.

        Args:
            ceramic_url: URL del nodo Ceramic
            ipfs_url: URL del nodo IPFS
        """
        self.ceramic_url = ceramic_url
        self.ipfs_client = ipfshttpclient.connect(ipfs_url)
        self.logger = logging.getLogger(__name__)

    def create_profile(self, did: str, profile_data: Dict[str, Any]) -> str:
        """
        Crea un perfil de usuario y lo almacena en IPFS a través de Ceramic.

        Args:
            did: DID del usuario
            profile_data: Datos del perfil (nombre, email, etc.)

        Returns:
            str: ID del perfil (hash IPFS)

        Raises:
            Exception: Si ocurre un error durante la creación
        """
        try:
            self.logger.info(f"Creando perfil para DID: {did}")

            # Validar datos del perfil
            if not isinstance(profile_data, dict):
                raise ValueError("profile_data debe ser un diccionario")

            # Agregar metadatos
            profile_data['did'] = did
            profile_data['timestamp'] = str(datetime.utcnow().isoformat())

            # Serializar y subir a IPFS
            profile_json = json.dumps(profile_data, ensure_ascii=False)
            result = self.ipfs_client.add_str(profile_json)
            profile_id = result['Hash']

            self.logger.info(f"Perfil creado exitosamente: {profile_id}")
            return profile_id

        except ipfshttpclient.exceptions.ErrorResponse as e:
            self.logger.error(f"Error de IPFS: {e}")
            raise Exception(f"Error conectando con IPFS: {e}")
        except Exception as e:
            self.logger.error(f"Error creando perfil: {e}")
            raise

    def verify_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """
        Verifica y recupera un perfil de usuario desde IPFS.

        Args:
            profile_id: ID del perfil (hash IPFS)

        Returns:
            Dict con datos del perfil si existe, None si no

        Raises:
            Exception: Si ocurre un error durante la verificación
        """
        try:
            self.logger.info(f"Verificando perfil: {profile_id}")

            # Recuperar datos desde IPFS
            profile_bytes = self.ipfs_client.cat(profile_id)
            profile_data = json.loads(profile_bytes.decode('utf-8'))

            # Validar estructura básica
            if 'did' not in profile_data:
                self.logger.warning(f"Perfil inválido: falta DID en {profile_id}")
                return None

            self.logger.info(f"Perfil verificado exitosamente: {profile_id}")
            return profile_data

        except ipfshttpclient.exceptions.ErrorResponse as e:
            self.logger.warning(f"Perfil no encontrado en IPFS: {profile_id}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decodificando perfil JSON: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error verificando perfil: {e}")
            raise

    def update_profile(self, profile_id: str, updates: Dict[str, Any]) -> str:
        """
        Actualiza un perfil existente.

        Args:
            profile_id: ID del perfil actual
            updates: Cambios a aplicar

        Returns:
            str: Nuevo ID del perfil actualizado
        """
        try:
            current_profile = self.verify_profile(profile_id)
            if not current_profile:
                raise ValueError(f"Perfil no encontrado: {profile_id}")

            # Aplicar actualizaciones
            current_profile.update(updates)
            current_profile['updated_at'] = str(datetime.utcnow().isoformat())

            # Crear nuevo perfil
            return self.create_profile(current_profile['did'], current_profile)

        except Exception as e:
            self.logger.error(f"Error actualizando perfil: {e}")
            raise