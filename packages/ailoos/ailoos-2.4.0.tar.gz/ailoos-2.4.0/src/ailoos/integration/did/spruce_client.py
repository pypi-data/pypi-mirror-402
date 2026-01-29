import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import didkit

class SpruceClient:
    """
    Cliente para gestión de Verifiable Credentials usando Spruce/DIDKit.
    Proporciona métodos para emitir y verificar credenciales verificables.
    """

    def __init__(self, issuer_did: str, issuer_key: str):
        """
        Inicializa el cliente Spruce.

        Args:
            issuer_did: DID del emisor
            issuer_key: Clave privada del emisor (en formato JWK)
        """
        self.issuer_did = issuer_did
        self.issuer_key = issuer_key
        self.logger = logging.getLogger(__name__)

    def issue_credential(self, subject_did: str, credential_data: Dict[str, Any],
                        credential_type: str = "VerifiableCredential") -> str:
        """
        Emite una nueva credencial verificable.

        Args:
            subject_did: DID del sujeto
            credential_data: Datos de la credencial
            credential_type: Tipo de credencial

        Returns:
            str: Credencial en formato JWT

        Raises:
            Exception: Si ocurre un error durante la emisión
        """
        try:
            self.logger.info(f"Emitiendo credencial para sujeto: {subject_did}")

            # Construir la credencial
            credential = {
                "@context": [
                    "https://www.w3.org/2018/credentials/v1",
                    "https://www.w3.org/2018/credentials/examples/v1"
                ],
                "type": [credential_type],
                "issuer": self.issuer_did,
                "issuanceDate": datetime.utcnow().isoformat() + "Z",
                "credentialSubject": {
                    "id": subject_did,
                    **credential_data
                }
            }

            # Convertir a JSON
            credential_json = json.dumps(credential, ensure_ascii=False)

            # Firmar con DIDKit
            signed_credential = didkit.issue_credential(
                credential_json,
                self.issuer_key,
                "{}"  # Opciones adicionales (vacías por defecto)
            )

            self.logger.info(f"Credencial emitida exitosamente para {subject_did}")
            return signed_credential

        except didkit.DIDKitException as e:
            self.logger.error(f"Error de DIDKit: {e}")
            raise Exception(f"Error firmando credencial: {e}")
        except Exception as e:
            self.logger.error(f"Error emitiendo credencial: {e}")
            raise

    def verify_credential(self, credential_jwt: str) -> bool:
        """
        Verifica una credencial verificable.

        Args:
            credential_jwt: Credencial en formato JWT

        Returns:
            bool: True si es válida

        Raises:
            Exception: Si ocurre un error durante la verificación
        """
        try:
            self.logger.info("Verificando credencial")

            # Verificar con DIDKit
            result = didkit.verify_credential(
                credential_jwt,
                "{}"  # Opciones de verificación
            )

            # Parsear resultado
            verification_result = json.loads(result)

            if verification_result.get("errors"):
                self.logger.warning(f"Errores en verificación: {verification_result['errors']}")
                return False

            self.logger.info("Credencial verificada exitosamente")
            return True

        except didkit.DIDKitException as e:
            self.logger.error(f"Error de DIDKit en verificación: {e}")
            return False
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decodificando resultado de verificación: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error verificando credencial: {e}")
            raise

    def get_credential_data(self, credential_jwt: str) -> Optional[Dict[str, Any]]:
        """
        Extrae los datos de una credencial verificable.

        Args:
            credential_jwt: Credencial en formato JWT

        Returns:
            Dict con datos de la credencial, None si inválida
        """
        try:
            # Decodificar JWT (sin verificar firma)
            import base64

            # JWT tiene 3 partes: header.payload.signature
            parts = credential_jwt.split('.')
            if len(parts) != 3:
                return None

            # Decodificar payload
            payload_b64 = parts[1]
            # Agregar padding si necesario
            payload_b64 += '=' * (4 - len(payload_b64) % 4)
            payload_bytes = base64.urlsafe_b64decode(payload_b64)
            payload = json.loads(payload_bytes.decode('utf-8'))

            return payload.get('vc', payload)

        except Exception as e:
            self.logger.error(f"Error extrayendo datos de credencial: {e}")
            return None

    def revoke_credential(self, credential_id: str) -> bool:
        """
        Revoca una credencial (simulado - en producción requeriría un registro de revocación).

        Args:
            credential_id: ID de la credencial

        Returns:
            bool: True si revocada exitosamente
        """
        try:
            self.logger.info(f"Revocando credencial: {credential_id}")
            # En implementación real, actualizar registro de revocación en blockchain/IPFS
            # Por ahora, solo log
            self.logger.warning("Revocación simulada - implementar registro de revocación real")
            return True
        except Exception as e:
            self.logger.error(f"Error revocando credencial: {e}")
            return False