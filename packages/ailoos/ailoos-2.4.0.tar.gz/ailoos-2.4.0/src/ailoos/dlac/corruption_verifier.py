#!/usr/bin/env python3
"""
Corruption Verifier - Verificación de corrupción de datos con checksums avanzados
"""

import hashlib
import hmac
import zlib
import threading
import time
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import json
import os

from ..utils.logging import get_logger

logger = get_logger(__name__)


class ChecksumAlgorithm(Enum):
    """Algoritmos de checksum soportados."""
    SHA256 = "sha256"
    SHA512 = "sha512"
    BLAKE2B = "blake2b"
    MD5 = "md5"  # Solo para compatibilidad, no recomendado para seguridad


class CorruptionType(Enum):
    """Tipos de corrupción detectados."""
    CHECKSUM_MISMATCH = "checksum_mismatch"
    SIZE_MISMATCH = "size_mismatch"
    METADATA_CORRUPTION = "metadata_corruption"
    PARTIAL_CORRUPTION = "partial_corruption"
    COMPLETE_LOSS = "complete_loss"


@dataclass
class ChecksumRecord:
    """Registro de checksum de datos."""
    data_id: str
    algorithm: ChecksumAlgorithm
    checksum: str
    salt: Optional[str]  # Para HMAC
    timestamp: datetime
    data_size: int
    block_size: int  # Para verificación por bloques
    block_checksums: List[str] = field(default_factory=list)  # Checksums por bloque
    metadata_checksum: Optional[str] = None
    verification_count: int = 0
    last_verified: Optional[datetime] = None


@dataclass
class CorruptionReport:
    """Reporte de corrupción detectada."""
    data_id: str
    corruption_type: CorruptionType
    severity: str  # 'low', 'medium', 'high', 'critical'
    detected_at: datetime
    expected_checksum: str
    actual_checksum: str
    affected_blocks: List[int] = field(default_factory=list)  # Bloques corruptos
    corruption_percentage: float = 0.0
    recovery_suggestions: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


class CorruptionVerifier:
    """
    Verificador avanzado de corrupción de datos con múltiples checksums.

    Características:
    - Múltiples algoritmos de hash
    - Verificación por bloques
    - Detección de corrupción parcial
    - Verificación de metadatos
    - Recuperación automática de backups
    """

    def __init__(self,
                 primary_algorithm: ChecksumAlgorithm = ChecksumAlgorithm.SHA256,
                 secondary_algorithms: List[ChecksumAlgorithm] = None,
                 block_size: int = 1024 * 1024,  # 1MB
                 alert_callback: Optional[Callable] = None,
                 enable_hmac: bool = True):
        """
        Inicializar verificador de corrupción.

        Args:
            primary_algorithm: Algoritmo principal de checksum
            secondary_algorithms: Algoritmos secundarios
            block_size: Tamaño de bloque para verificación
            alert_callback: Función para alertas
            enable_hmac: Habilitar HMAC para mayor seguridad
        """
        self.primary_algorithm = primary_algorithm
        self.secondary_algorithms = secondary_algorithms or [ChecksumAlgorithm.BLAKE2B]
        self.block_size = block_size
        self.alert_callback = alert_callback
        self.enable_hmac = enable_hmac

        # Clave HMAC (debería venir de configuración segura)
        self.hmac_key = os.getenv('AILOOS_HMAC_KEY', 'default_key_change_in_production').encode()

        # Registros de checksums
        self.checksum_records: Dict[str, ChecksumRecord] = {}
        self.verification_history: Dict[str, List[CorruptionReport]] = {}

        # Estadísticas
        self.stats = {
            'total_verifications': 0,
            'corruption_detected': 0,
            'successful_recoveries': 0,
            'verification_failures': 0,
            'last_verification_time': None
        }

        logger.info("🔐 Corruption Verifier initialized")

    def register_data(self, data_id: str, data: Any, metadata: Dict[str, Any] = None) -> bool:
        """
        Registrar datos para verificación de corrupción.

        Args:
            data_id: ID único de los datos
            data: Los datos a verificar
            metadata: Metadatos asociados

        Returns:
            True si registrado exitosamente
        """
        try:
            # Convertir datos a bytes
            data_bytes = self._data_to_bytes(data)

            # Calcular checksums
            primary_checksum = self._calculate_checksum(data_bytes, self.primary_algorithm)
            secondary_checksums = {}
            for alg in self.secondary_algorithms:
                secondary_checksums[alg.value] = self._calculate_checksum(data_bytes, alg)

            # Calcular checksums por bloque
            block_checksums = self._calculate_block_checksums(data_bytes)

            # Checksum de metadatos
            metadata_checksum = None
            if metadata:
                metadata_bytes = json.dumps(metadata, sort_keys=True).encode('utf-8')
                metadata_checksum = self._calculate_checksum(metadata_bytes, self.primary_algorithm)

            # Crear registro
            record = ChecksumRecord(
                data_id=data_id,
                algorithm=self.primary_algorithm,
                checksum=primary_checksum,
                salt=self._generate_salt() if self.enable_hmac else None,
                timestamp=datetime.now(),
                data_size=len(data_bytes),
                block_size=self.block_size,
                block_checksums=block_checksums,
                metadata_checksum=metadata_checksum
            )

            self.checksum_records[data_id] = record

            logger.info(f"📝 Registered corruption verification for {data_id} "
                       f"({len(data_bytes)} bytes, {len(block_checksums)} blocks)")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to register data {data_id}: {e}")
            return False

    def verify_integrity(self, data_id: str, current_data: Any,
                        current_metadata: Dict[str, Any] = None) -> Tuple[bool, Optional[CorruptionReport]]:
        """
        Verificar integridad de datos.

        Args:
            data_id: ID de los datos
            current_data: Datos actuales
            current_metadata: Metadatos actuales

        Returns:
            (is_integrity_ok, corruption_report)
        """
        if data_id not in self.checksum_records:
            logger.warning(f"⚠️ No checksum record found for {data_id}")
            return False, None

        record = self.checksum_records[data_id]
        record.verification_count += 1
        record.last_verified = datetime.now()

        try:
            # Convertir datos actuales
            current_bytes = self._data_to_bytes(current_data)

            # Verificación primaria
            current_checksum = self._calculate_checksum(current_bytes, record.algorithm)
            is_primary_ok = current_checksum == record.checksum

            # Verificación de tamaño
            is_size_ok = len(current_bytes) == record.data_size

            # Verificación de metadatos
            is_metadata_ok = True
            if record.metadata_checksum and current_metadata:
                metadata_bytes = json.dumps(current_metadata, sort_keys=True).encode('utf-8')
                current_metadata_checksum = self._calculate_checksum(metadata_bytes, record.algorithm)
                is_metadata_ok = current_metadata_checksum == record.metadata_checksum

            # Verificación por bloques
            block_corruption_info = self._verify_block_checksums(current_bytes, record.block_checksums)

            # Determinar si hay corrupción
            is_integrity_ok = is_primary_ok and is_size_ok and is_metadata_ok and block_corruption_info['is_ok']

            corruption_report = None
            if not is_integrity_ok:
                corruption_report = self._create_corruption_report(
                    data_id, record, current_checksum, current_bytes,
                    is_primary_ok, is_size_ok, is_metadata_ok, block_corruption_info
                )
                self.stats['corruption_detected'] += 1

                # Almacenar en historial
                if data_id not in self.verification_history:
                    self.verification_history[data_id] = []
                self.verification_history[data_id].append(corruption_report)

            self.stats['total_verifications'] += 1
            return is_integrity_ok, corruption_report

        except Exception as e:
            logger.error(f"❌ Integrity verification failed for {data_id}: {e}")
            self.stats['verification_failures'] += 1
            return False, None

    def verify_data_block(self, data_id: str, block_index: int, block_data: bytes) -> bool:
        """
        Verificar integridad de un bloque específico.

        Args:
            data_id: ID de los datos
            block_index: Índice del bloque
            block_data: Datos del bloque

        Returns:
            True si el bloque es íntegro
        """
        if data_id not in self.checksum_records:
            return False

        record = self.checksum_records[data_id]
        if block_index >= len(record.block_checksums):
            return False

        expected_checksum = record.block_checksums[block_index]
        actual_checksum = self._calculate_checksum(block_data, record.algorithm)

        return actual_checksum == expected_checksum

    def get_corruption_history(self, data_id: str, limit: int = 10) -> List[CorruptionReport]:
        """
        Obtener historial de corrupción para datos específicos.

        Args:
            data_id: ID de los datos
            limit: Número máximo de reportes

        Returns:
            Lista de reportes de corrupción
        """
        history = self.verification_history.get(data_id, [])
        return history[-limit:] if limit else history

    def get_verification_stats(self, data_id: str) -> Dict[str, Any]:
        """
        Obtener estadísticas de verificación para datos específicos.

        Args:
            data_id: ID de los datos

        Returns:
            Estadísticas de verificación
        """
        if data_id not in self.checksum_records:
            return {'error': 'Data ID not found'}

        record = self.checksum_records[data_id]
        history = self.verification_history.get(data_id, [])

        corruption_rate = len(history) / record.verification_count if record.verification_count > 0 else 0

        return {
            'data_id': data_id,
            'total_verifications': record.verification_count,
            'corruption_events': len(history),
            'corruption_rate': corruption_rate,
            'last_verified': record.last_verified.isoformat() if record.last_verified else None,
            'algorithm': record.algorithm.value,
            'data_size': record.data_size,
            'block_count': len(record.block_checksums)
        }

    def get_global_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas globales del verificador."""
        total_registered = len(self.checksum_records)
        total_history_events = sum(len(history) for history in self.verification_history.values())

        return {
            **self.stats,
            'registered_data_count': total_registered,
            'total_corruption_reports': total_history_events,
            'primary_algorithm': self.primary_algorithm.value,
            'secondary_algorithms': [alg.value for alg in self.secondary_algorithms],
            'block_size': self.block_size
        }

    def _calculate_checksum(self, data: bytes, algorithm: ChecksumAlgorithm) -> str:
        """Calcular checksum usando el algoritmo especificado."""
        if self.enable_hmac:
            # Usar HMAC para mayor seguridad
            return hmac.new(self.hmac_key, data, algorithm.value).hexdigest()
        else:
            # Hash simple
            hash_obj = hashlib.new(algorithm.value)
            hash_obj.update(data)
            return hash_obj.hexdigest()

    def _calculate_block_checksums(self, data: bytes) -> List[str]:
        """Calcular checksums por bloques."""
        checksums = []
        for i in range(0, len(data), self.block_size):
            block = data[i:i + self.block_size]
            checksum = self._calculate_checksum(block, self.primary_algorithm)
            checksums.append(checksum)
        return checksums

    def _verify_block_checksums(self, data: bytes, expected_checksums: List[str]) -> Dict[str, Any]:
        """Verificar checksums por bloques."""
        actual_checksums = self._calculate_block_checksums(data)
        affected_blocks = []
        corruption_percentage = 0.0

        if len(actual_checksums) != len(expected_checksums):
            return {
                'is_ok': False,
                'affected_blocks': list(range(min(len(actual_checksums), len(expected_checksums)))),
                'corruption_percentage': 100.0 if len(actual_checksums) != len(expected_checksums) else 0.0
            }

        for i, (expected, actual) in enumerate(zip(expected_checksums, actual_checksums)):
            if expected != actual:
                affected_blocks.append(i)

        if expected_checksums:
            corruption_percentage = (len(affected_blocks) / len(expected_checksums)) * 100

        return {
            'is_ok': len(affected_blocks) == 0,
            'affected_blocks': affected_blocks,
            'corruption_percentage': corruption_percentage
        }

    def _create_corruption_report(self, data_id: str, record: ChecksumRecord,
                                current_checksum: str, current_bytes: bytes,
                                is_primary_ok: bool, is_size_ok: bool,
                                is_metadata_ok: bool, block_info: Dict[str, Any]) -> CorruptionReport:
        """Crear reporte de corrupción."""
        # Determinar tipo de corrupción
        if not is_size_ok and len(current_bytes) == 0:
            corruption_type = CorruptionType.COMPLETE_LOSS
            severity = 'critical'
        elif block_info['corruption_percentage'] > 50:
            corruption_type = CorruptionType.PARTIAL_CORRUPTION
            severity = 'high'
        elif not is_primary_ok:
            corruption_type = CorruptionType.CHECKSUM_MISMATCH
            severity = 'high'
        elif not is_size_ok:
            corruption_type = CorruptionType.SIZE_MISMATCH
            severity = 'medium'
        elif not is_metadata_ok:
            corruption_type = CorruptionType.METADATA_CORRUPTION
            severity = 'medium'
        else:
            corruption_type = CorruptionType.CHECKSUM_MISMATCH
            severity = 'low'

        # Sugerencias de recuperación
        recovery_suggestions = []
        if corruption_type == CorruptionType.COMPLETE_LOSS:
            recovery_suggestions.extend([
                "Restore from backup",
                "Request data from other nodes",
                "Check IPFS/storage availability"
            ])
        elif block_info['affected_blocks']:
            recovery_suggestions.extend([
                f"Restore corrupted blocks: {block_info['affected_blocks']}",
                "Use error-correcting codes if available",
                "Verify data source integrity"
            ])
        else:
            recovery_suggestions.extend([
                "Recalculate checksums",
                "Check storage media integrity",
                "Run diagnostic tools"
            ])

        report = CorruptionReport(
            data_id=data_id,
            corruption_type=corruption_type,
            severity=severity,
            detected_at=datetime.now(),
            expected_checksum=record.checksum,
            actual_checksum=current_checksum,
            affected_blocks=block_info['affected_blocks'],
            corruption_percentage=block_info['corruption_percentage'],
            recovery_suggestions=recovery_suggestions,
            details={
                'primary_checksum_ok': is_primary_ok,
                'size_ok': is_size_ok,
                'metadata_ok': is_metadata_ok,
                'block_info': block_info,
                'data_size_expected': record.data_size,
                'data_size_actual': len(current_bytes),
                'algorithm': record.algorithm.value
            }
        )

        # Alertar
        if self.alert_callback:
            self.alert_callback('corruption_detected', {
                'data_id': data_id,
                'corruption_type': corruption_type.value,
                'severity': severity,
                'corruption_percentage': block_info['corruption_percentage'],
                'timestamp': report.detected_at.isoformat()
            })

        logger.warning(f"🚨 Corruption detected in {data_id}: {corruption_type.value} "
                      f"(severity: {severity}, {block_info['corruption_percentage']:.1f}% corrupted)")
        return report

    def _data_to_bytes(self, data: Any) -> bytes:
        """Convertir datos a bytes para checksum."""
        if isinstance(data, bytes):
            return data
        elif isinstance(data, str):
            return data.encode('utf-8')
        elif isinstance(data, dict):
            return json.dumps(data, sort_keys=True).encode('utf-8')
        elif hasattr(data, '__dict__'):
            return json.dumps(data.__dict__, sort_keys=True).encode('utf-8')
        else:
            return str(data).encode('utf-8')

    def _generate_salt(self) -> str:
        """Generar salt para HMAC."""
        return hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]

    def cleanup_old_history(self, max_age_days: int = 30):
        """
        Limpiar historial antiguo de corrupción.

        Args:
            max_age_days: Edad máxima en días
        """
        cutoff = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)

        for data_id in list(self.verification_history.keys()):
            self.verification_history[data_id] = [
                report for report in self.verification_history[data_id]
                if report.detected_at.timestamp() > cutoff
            ]

            # Remover entradas vacías
            if not self.verification_history[data_id]:
                del self.verification_history[data_id]

        logger.info("🧹 Cleaned up old corruption history")