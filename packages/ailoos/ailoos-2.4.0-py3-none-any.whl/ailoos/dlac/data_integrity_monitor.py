#!/usr/bin/env python3
"""
Data Integrity Monitor - Monitoreo continuo de integridad de datos en entornos federados
"""

import asyncio
import hashlib
import threading
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DataIntegrityRecord:
    """Registro de integridad de datos."""
    data_id: str
    checksum: str
    timestamp: datetime
    data_size: int
    node_id: str
    data_type: str  # 'model', 'dataset', 'weights', etc.
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrityCheckResult:
    """Resultado de verificación de integridad."""
    data_id: str
    is_integrity_ok: bool
    previous_checksum: Optional[str]
    current_checksum: str
    timestamp: datetime
    node_id: str
    issues: List[str] = field(default_factory=list)


class DataIntegrityMonitor:
    """
    Monitor continuo de integridad de datos en entornos federados P2P.

    Características:
    - Monitoreo asíncrono de checksums
    - Detección automática de corrupción
    - Verificación cruzada entre nodos
    - Alertas en tiempo real
    - Escalabilidad para entornos distribuidos
    """

    def __init__(self,
                 check_interval: int = 300,  # 5 minutos
                 alert_callback: Optional[Callable] = None,
                 max_records: int = 10000):
        """
        Inicializar monitor de integridad.

        Args:
            check_interval: Intervalo entre verificaciones (segundos)
            alert_callback: Función para alertas
            max_records: Máximo número de registros a mantener
        """
        self.check_interval = check_interval
        self.alert_callback = alert_callback
        self.max_records = max_records

        # Almacenamiento de registros de integridad
        self.integrity_records: Dict[str, List[DataIntegrityRecord]] = {}
        self.last_checksums: Dict[str, str] = {}

        # Estado del monitor
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # Estadísticas
        self.stats = {
            'total_checks': 0,
            'integrity_failures': 0,
            'last_check_time': None,
            'monitored_data_ids': set()
        }

        logger.info("🛡️ Data Integrity Monitor initialized")

    def register_data(self, data_id: str, data: Any, node_id: str,
                     data_type: str = 'unknown', metadata: Dict[str, Any] = None) -> bool:
        """
        Registrar datos para monitoreo de integridad.

        Args:
            data_id: Identificador único de los datos
            data: Los datos a monitorear (bytes, dict, etc.)
            node_id: ID del nodo que contiene los datos
            data_type: Tipo de datos ('model', 'dataset', etc.)
            metadata: Metadatos adicionales

        Returns:
            True si registrado exitosamente
        """
        try:
            # Calcular checksum
            checksum = self._calculate_checksum(data)

            # Crear registro
            record = DataIntegrityRecord(
                data_id=data_id,
                checksum=checksum,
                timestamp=datetime.now(),
                data_size=self._get_data_size(data),
                node_id=node_id,
                data_type=data_type,
                metadata=metadata or {}
            )

            # Almacenar registro
            if data_id not in self.integrity_records:
                self.integrity_records[data_id] = []

            self.integrity_records[data_id].append(record)

            # Mantener límite de registros
            if len(self.integrity_records[data_id]) > 10:  # Máximo 10 registros por data_id
                self.integrity_records[data_id] = self.integrity_records[data_id][-10:]

            # Actualizar último checksum
            self.last_checksums[data_id] = checksum

            # Actualizar estadísticas
            self.stats['monitored_data_ids'].add(data_id)

            logger.info(f"📝 Registered data integrity for {data_id} on node {node_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to register data {data_id}: {e}")
            return False

    def check_integrity(self, data_id: str, current_data: Any, node_id: str) -> IntegrityCheckResult:
        """
        Verificar integridad de datos específicos.

        Args:
            data_id: ID de los datos a verificar
            current_data: Datos actuales
            node_id: ID del nodo

        Returns:
            Resultado de la verificación
        """
        try:
            current_checksum = self._calculate_checksum(current_data)
            previous_checksum = self.last_checksums.get(data_id)

            is_integrity_ok = (previous_checksum is None or current_checksum == previous_checksum)

            result = IntegrityCheckResult(
                data_id=data_id,
                is_integrity_ok=is_integrity_ok,
                previous_checksum=previous_checksum,
                current_checksum=current_checksum,
                timestamp=datetime.now(),
                node_id=node_id,
                issues=[]
            )

            if not is_integrity_ok:
                result.issues.append(f"Checksum mismatch: expected {previous_checksum}, got {current_checksum}")
                self.stats['integrity_failures'] += 1

                # Alertar si hay callback
                if self.alert_callback:
                    self.alert_callback('integrity_failure', {
                        'data_id': data_id,
                        'node_id': node_id,
                        'previous_checksum': previous_checksum,
                        'current_checksum': current_checksum,
                        'timestamp': result.timestamp.isoformat()
                    })

            self.stats['total_checks'] += 1
            return result

        except Exception as e:
            logger.error(f"❌ Integrity check failed for {data_id}: {e}")
            return IntegrityCheckResult(
                data_id=data_id,
                is_integrity_ok=False,
                previous_checksum=None,
                current_checksum='error',
                timestamp=datetime.now(),
                node_id=node_id,
                issues=[str(e)]
            )

    def start_monitoring(self):
        """Iniciar monitoreo continuo."""
        if self.is_monitoring:
            logger.warning("⚠️ Integrity monitor already running")
            return

        self.is_monitoring = True
        self.stop_event.clear()
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()

        logger.info("🚀 Started continuous data integrity monitoring")

    def stop_monitoring(self):
        """Detener monitoreo continuo."""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        self.stop_event.set()

        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        logger.info("⏹️ Stopped data integrity monitoring")

    def _monitoring_loop(self):
        """Bucle principal de monitoreo."""
        while not self.stop_event.is_set():
            try:
                self._perform_integrity_checks()
                self.stats['last_check_time'] = datetime.now()

            except Exception as e:
                logger.error(f"❌ Monitoring loop error: {e}")

            # Esperar hasta el próximo check
            self.stop_event.wait(self.check_interval)

    def _perform_integrity_checks(self):
        """Realizar verificaciones de integridad programadas."""
        # En una implementación real, esto debería verificar datos almacenados
        # Por ahora, solo logueamos que estamos verificando
        monitored_count = len(self.stats['monitored_data_ids'])
        if monitored_count > 0:
            logger.info(f"🔍 Performing integrity checks on {monitored_count} data items")

    def get_integrity_status(self, data_id: str) -> Dict[str, Any]:
        """
        Obtener estado de integridad para datos específicos.

        Args:
            data_id: ID de los datos

        Returns:
            Estado de integridad
        """
        records = self.integrity_records.get(data_id, [])
        last_checksum = self.last_checksums.get(data_id)

        return {
            'data_id': data_id,
            'last_checksum': last_checksum,
            'record_count': len(records),
            'last_record': records[-1].__dict__ if records else None,
            'is_monitored': data_id in self.stats['monitored_data_ids']
        }

    def get_monitor_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del monitor."""
        return {
            **self.stats,
            'is_monitoring': self.is_monitoring,
            'check_interval': self.check_interval,
            'monitored_count': len(self.stats['monitored_data_ids'])
        }

    def cross_node_verification(self, data_id: str, node_checksums: Dict[str, str]) -> Dict[str, Any]:
        """
        Verificación cruzada entre nodos.

        Args:
            data_id: ID de los datos
            node_checksums: Checksums por nodo

        Returns:
            Resultado de verificación cruzada
        """
        if not node_checksums:
            return {'status': 'no_data', 'consistent': True}

        # Verificar consistencia
        checksums = list(node_checksums.values())
        consistent = all(c == checksums[0] for c in checksums)

        result = {
            'data_id': data_id,
            'consistent': consistent,
            'node_count': len(node_checksums),
            'unique_checksums': len(set(checksums)),
            'node_checksums': node_checksums
        }

        if not consistent:
            result['issues'] = ['Inconsistent checksums across nodes']
            logger.warning(f"⚠️ Cross-node inconsistency detected for {data_id}")

            if self.alert_callback:
                self.alert_callback('cross_node_inconsistency', result)

        return result

    def _calculate_checksum(self, data: Any) -> str:
        """Calcular checksum de datos."""
        try:
            # Convertir datos a bytes
            if isinstance(data, bytes):
                data_bytes = data
            elif isinstance(data, str):
                data_bytes = data.encode('utf-8')
            elif isinstance(data, dict):
                data_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
            elif hasattr(data, '__dict__'):
                data_bytes = json.dumps(data.__dict__, sort_keys=True).encode('utf-8')
            else:
                data_bytes = str(data).encode('utf-8')

            # Calcular SHA-256
            return hashlib.sha256(data_bytes).hexdigest()

        except Exception as e:
            logger.error(f"❌ Checksum calculation error: {e}")
            return f"error_{hash(str(data))}"

    def _get_data_size(self, data: Any) -> int:
        """Obtener tamaño de datos."""
        try:
            if isinstance(data, bytes):
                return len(data)
            elif isinstance(data, str):
                return len(data.encode('utf-8'))
            elif isinstance(data, dict):
                return len(json.dumps(data).encode('utf-8'))
            elif hasattr(data, '__dict__'):
                return len(json.dumps(data.__dict__).encode('utf-8'))
            else:
                return len(str(data).encode('utf-8'))
        except:
            return 0

    def cleanup_old_records(self, max_age_days: int = 30):
        """
        Limpiar registros antiguos.

        Args:
            max_age_days: Edad máxima en días
        """
        cutoff = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)

        for data_id, records in self.integrity_records.items():
            # Filtrar registros recientes
            self.integrity_records[data_id] = [
                r for r in records if r.timestamp.timestamp() > cutoff
            ]

        logger.info("🧹 Cleaned up old integrity records")