import logging
import hashlib
import io
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
import uplink  # Requiere instalación: pip install uplink-python

logger = logging.getLogger(__name__)

@dataclass
class UploadResult:
    key: str
    etag: str
    size: int

@dataclass
class DownloadResult:
    data: bytes
    etag: str

class StorjClient:
    """
    Cliente para interactuar con Storj DCS para almacenamiento distribuido.
    Maneja almacenamiento, recuperación, verificación de integridad y gestión de costos.
    """

    def __init__(self, access_grant: str, bucket_name: str = "ailoos-storage"):
        """
        Inicializa el cliente Storj.

        Args:
            access_grant: Access grant de Storj
            bucket_name: Nombre del bucket por defecto
        """
        self.access_grant = access_grant
        self.bucket_name = bucket_name
        self.project = None
        self.bucket = None

        self._connect()

    def _connect(self):
        """Establece conexión con Storj."""
        try:
            self.project = uplink.Project.from_access(self.access_grant)
            logger.info("Conexión a Storj establecida")

            # Asegurar que el bucket existe
            try:
                self.bucket = self.project.bucket(self.bucket_name)
                # Intentar crear si no existe
                self.project.create_bucket(self.bucket_name)
                logger.info(f"Bucket '{self.bucket_name}' listo")
            except Exception as e:
                if "bucket already exists" not in str(e).lower():
                    raise

        except Exception as e:
            logger.error(f"Error conectando a Storj: {e}")
            raise

    def store_data(self, data: bytes, key: str, metadata: Dict[str, str] = None) -> UploadResult:
        """
        Almacena datos en Storj.

        Args:
            data: Datos a almacenar
            key: Clave única para el objeto
            metadata: Metadatos adicionales

        Returns:
            Resultado del upload

        Raises:
            Exception: Si falla el almacenamiento
        """
        try:
            data_hash = hashlib.sha256(data).hexdigest()
            logger.info(f"Iniciando almacenamiento de datos con hash: {data_hash}, clave: {key}")

            # Preparar upload
            upload = self.bucket.new_upload(key)

            # Agregar metadatos
            custom_metadata = metadata or {}
            custom_metadata['data-hash'] = data_hash
            custom_metadata['upload-timestamp'] = str(int(time.time()))

            # Subir datos
            upload.set_custom_metadata(custom_metadata)
            upload.write(data, len(data))
            upload.commit()

            # Obtener info del objeto
            object_info = self.bucket.object_key(key).info()

            result = UploadResult(
                key=key,
                etag=object_info.etag,
                size=len(data)
            )

            logger.info(f"Datos almacenados exitosamente con clave: {key}")
            return result

        except Exception as e:
            logger.error(f"Error almacenando datos en Storj: {e}")
            raise

    def retrieve_data(self, key: str) -> DownloadResult:
        """
        Recupera datos desde Storj.

        Args:
            key: Clave del objeto a recuperar

        Returns:
            Resultado del download

        Raises:
            Exception: Si falla la recuperación
        """
        try:
            logger.info(f"Recuperando datos con clave: {key}")

            # Descargar objeto
            download = self.bucket.object_key(key).download()
            data = download.read_all()

            object_info = download.info()

            result = DownloadResult(
                data=data,
                etag=object_info.etag
            )

            logger.info(f"Datos recuperados exitosamente con clave: {key}")
            return result

        except Exception as e:
            logger.error(f"Error recuperando datos desde Storj: {e}")
            raise

    def delete_data(self, key: str):
        """
        Elimina datos de Storj.

        Args:
            key: Clave del objeto a eliminar

        Raises:
            Exception: Si falla la eliminación
        """
        try:
            logger.info(f"Eliminando datos con clave: {key}")

            self.bucket.object_key(key).delete()

            logger.info(f"Datos eliminados exitosamente con clave: {key}")

        except Exception as e:
            logger.error(f"Error eliminando datos de Storj: {e}")
            raise

    def verify_integrity(self, key: str, expected_hash: str) -> bool:
        """
        Verifica la integridad de los datos almacenados comparando hashes.

        Args:
            key: Clave del objeto
            expected_hash: Hash SHA256 esperado

        Returns:
            True si la integridad es correcta, False en caso contrario
        """
        try:
            logger.info(f"Verificando integridad de clave: {key}")

            result = self.retrieve_data(key)
            actual_hash = hashlib.sha256(result.data).hexdigest()

            is_valid = actual_hash == expected_hash
            if not is_valid:
                logger.warning(f"Integridad comprometida. Esperado: {expected_hash}, Actual: {actual_hash}")
            else:
                logger.info("Integridad verificada correctamente")

            return is_valid

        except Exception as e:
            logger.error(f"Error verificando integridad: {e}")
            return False

    def estimate_cost(self, size_bytes: int, storage_days: int = 30, downloads_gb: int = 0) -> float:
        """
        Estima el costo de almacenamiento en USD.

        Args:
            size_bytes: Tamaño de los datos en bytes
            storage_days: Días de almacenamiento
            downloads_gb: GB descargados

        Returns:
            Costo estimado en USD
        """
        try:
            # Tasas aproximadas de Storj (pueden cambiar)
            storage_rate_per_gb_month = 0.004  # $0.004 por GB/mes
            download_rate_per_gb = 0.007       # $0.007 por GB descargado

            # Calcular tamaño en GB
            size_gb = size_bytes / (1024 ** 3)

            # Costo de almacenamiento
            storage_months = storage_days / 30
            storage_cost = size_gb * storage_months * storage_rate_per_gb_month

            # Costo de descarga
            download_cost = downloads_gb * download_rate_per_gb

            total_cost = storage_cost + download_cost

            logger.info(f"Costo estimado: ${total_cost:.4f} para {size_gb:.4f} GB por {storage_days} días + {downloads_gb} GB descargados")
            return total_cost

        except Exception as e:
            logger.error(f"Error estimando costo: {e}")
            # Valor por defecto
            return (size_bytes / (1024 ** 3)) * 0.004 * (storage_days / 30)

    def list_objects(self, prefix: str = "") -> list:
        """
        Lista objetos en el bucket.

        Args:
            prefix: Prefijo para filtrar objetos

        Returns:
            Lista de claves de objetos
        """
        try:
            objects = self.bucket.list_objects(prefix=prefix)
            keys = [obj.key for obj in objects]
            logger.info(f"Encontrados {len(keys)} objetos con prefijo '{prefix}'")
            return keys

        except Exception as e:
            logger.error(f"Error listando objetos: {e}")
            return []

    def get_object_info(self, key: str) -> Dict[str, Any]:
        """
        Obtiene información de un objeto.

        Args:
            key: Clave del objeto

        Returns:
            Información del objeto
        """
        try:
            info = self.bucket.object_key(key).info()
            return {
                'key': key,
                'size': info.size,
                'etag': info.etag,
                'created': info.created,
                'modified': info.modified,
                'custom_metadata': info.custom_metadata
            }

        except Exception as e:
            logger.error(f"Error obteniendo info del objeto: {e}")
            raise

    def copy_object(self, source_key: str, dest_key: str):
        """
        Copia un objeto dentro del bucket.

        Args:
            source_key: Clave del objeto fuente
            dest_key: Clave del objeto destino

        Raises:
            Exception: Si falla la copia
        """
        try:
            logger.info(f"Copiando objeto de {source_key} a {dest_key}")

            self.bucket.object_key(source_key).copy_to(self.bucket, dest_key)

            logger.info("Objeto copiado exitosamente")

        except Exception as e:
            logger.error(f"Error copiando objeto: {e}")
            raise

    def close(self):
        """Cierra la conexión con Storj."""
        try:
            if self.project:
                self.project.close()
                logger.info("Conexión a Storj cerrada")
        except Exception as e:
            logger.error(f"Error cerrando conexión: {e}")