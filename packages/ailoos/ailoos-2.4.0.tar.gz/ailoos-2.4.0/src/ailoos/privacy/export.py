"""
Sistema de exportación GDPR para AILOOS
=======================================

Este módulo implementa la funcionalidad de exportación de datos personales
conforme al Reglamento General de Protección de Datos (GDPR), permitiendo
a los usuarios exportar todos sus datos personales almacenados en el sistema.
"""

import json
import csv
import zipfile
import os
import tempfile
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging
import asyncio
from pathlib import Path

from ..settings.service import SettingsService
from ..memory.service import MemoryService
from ..federated.session import FederatedSession
from ..monitoring.metrics_api import MetricsAPI

logger = logging.getLogger(__name__)


class ExportStatus(Enum):
    """Estados posibles de una exportación GDPR."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExportRequest:
    """Solicitud de exportación GDPR."""
    user_id: int
    request_id: str = field(default_factory=lambda: f"gdpr_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    status: ExportStatus = ExportStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    export_path: Optional[str] = None
    error_message: Optional[str] = None
    data_types: List[str] = field(default_factory=lambda: ["settings", "memory", "sessions", "metrics"])
    format: str = "json"  # "json", "csv", "zip"

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la solicitud a diccionario."""
        return {
            "user_id": self.user_id,
            "request_id": self.request_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "export_path": self.export_path,
            "error_message": self.error_message,
            "data_types": self.data_types,
            "format": self.format
        }


@dataclass
class ExportedData:
    """Contenedor para datos exportados."""
    settings: Optional[Dict[str, Any]] = None
    memory_items: List[Dict[str, Any]] = field(default_factory=list)
    sessions: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Optional[Dict[str, Any]] = None
    account_info: Optional[Dict[str, Any]] = None
    export_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte los datos exportados a diccionario."""
        return {
            "settings": self.settings,
            "memory_items": self.memory_items,
            "sessions": self.sessions,
            "metrics": self.metrics,
            "account_info": self.account_info,
            "export_metadata": self.export_metadata
        }


class ExportService:
    """
    Servicio principal para exportación de datos personales conforme a GDPR.

    Este servicio permite exportar todos los datos personales de un usuario
    incluyendo configuraciones, memoria conversacional, sesiones federadas,
    métricas de uso y estadísticas de cuenta.
    """

    def __init__(self,
                 settings_service: Optional[SettingsService] = None,
                 memory_service: Optional[MemoryService] = None,
                 export_dir: str = "exports/gdpr"):
        """
        Inicializa el servicio de exportación.

        Args:
            settings_service: Servicio de configuraciones
            memory_service: Servicio de memoria
            export_dir: Directorio donde guardar las exportaciones
        """
        self.settings_service = settings_service
        self.memory_service = memory_service
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

        # Cache de solicitudes activas
        self.active_exports: Dict[str, ExportRequest] = {}

        logger.info(f"ExportService inicializado. Directorio de exportaciones: {self.export_dir}")

    async def request_export(self,
                           user_id: int,
                           data_types: Optional[List[str]] = None,
                           format: str = "json") -> ExportRequest:
        """
        Solicita una nueva exportación GDPR.

        Args:
            user_id: ID del usuario que solicita la exportación
            data_types: Tipos de datos a exportar (por defecto todos)
            format: Formato de exportación ("json", "csv", "zip")

        Returns:
            ExportRequest: Solicitud de exportación creada
        """
        if data_types is None:
            data_types = ["settings", "memory", "sessions", "metrics", "account"]

        request = ExportRequest(
            user_id=user_id,
            data_types=data_types,
            format=format
        )

        self.active_exports[request.request_id] = request
        logger.info(f"Exportación GDPR solicitada: {request.request_id} para usuario {user_id}")

        # Iniciar exportación en background
        asyncio.create_task(self._process_export(request))

        return request

    async def get_export_status(self, request_id: str) -> Optional[ExportRequest]:
        """
        Obtiene el estado de una solicitud de exportación.

        Args:
            request_id: ID de la solicitud

        Returns:
            ExportRequest o None si no existe
        """
        return self.active_exports.get(request_id)

    async def cancel_export(self, request_id: str) -> bool:
        """
        Cancela una exportación en curso.

        Args:
            request_id: ID de la solicitud a cancelar

        Returns:
            bool: True si se canceló exitosamente
        """
        request = self.active_exports.get(request_id)
        if request and request.status in [ExportStatus.PENDING, ExportStatus.IN_PROGRESS]:
            request.status = ExportStatus.CANCELLED
            request.completed_at = datetime.now()
            logger.info(f"Exportación cancelada: {request_id}")
            return True
        return False

    async def _process_export(self, request: ExportRequest) -> None:
        """
        Procesa una solicitud de exportación en background.

        Args:
            request: Solicitud de exportación a procesar
        """
        try:
            request.status = ExportStatus.IN_PROGRESS
            logger.info(f"Iniciando procesamiento de exportación: {request.request_id}")

            # Recopilar datos
            exported_data = await self._gather_user_data(request.user_id, request.data_types)

            # Generar archivos de exportación
            export_path = await self._generate_export_files(exported_data, request)

            # Completar solicitud
            request.status = ExportStatus.COMPLETED
            request.completed_at = datetime.now()
            request.export_path = str(export_path)

            logger.info(f"Exportación completada: {request.request_id} - Archivo: {export_path}")

        except Exception as e:
            logger.error(f"Error procesando exportación {request.request_id}: {e}")
            request.status = ExportStatus.FAILED
            request.error_message = str(e)
            request.completed_at = datetime.now()

    async def _gather_user_data(self, user_id: int, data_types: List[str]) -> ExportedData:
        """
        Recopila todos los datos personales del usuario.

        Args:
            user_id: ID del usuario
            data_types: Tipos de datos a recopilar

        Returns:
            ExportedData: Datos recopilados
        """
        exported_data = ExportedData()
        exported_data.export_metadata = {
            "user_id": user_id,
            "export_timestamp": datetime.now().isoformat(),
            "gdpr_compliant": True,
            "data_types_exported": data_types
        }

        # Configuraciones
        if "settings" in data_types and self.settings_service:
            try:
                settings = await self.settings_service.get_user_settings(user_id)
                exported_data.settings = settings.to_dict() if settings else None
                logger.debug(f"Configuraciones exportadas para usuario {user_id}")
            except Exception as e:
                logger.warning(f"Error exportando configuraciones: {e}")

        # Memoria conversacional
        if "memory" in data_types and self.memory_service:
            try:
                memory_items = await self.memory_service.get_user_memory(user_id)
                exported_data.memory_items = [item.to_dict() for item in memory_items]
                logger.debug(f"Memoria exportada para usuario {user_id}: {len(memory_items)} items")
            except Exception as e:
                logger.warning(f"Error exportando memoria: {e}")

        # Sesiones federadas
        if "sessions" in data_types:
            try:
                sessions = await self._get_user_sessions(user_id)
                exported_data.sessions = sessions
                logger.debug(f"Sesiones exportadas para usuario {user_id}: {len(sessions)} sesiones")
            except Exception as e:
                logger.warning(f"Error exportando sesiones: {e}")

        # Métricas de uso
        if "metrics" in data_types:
            try:
                metrics = await self._get_user_metrics(user_id)
                exported_data.metrics = metrics
                logger.debug(f"Métricas exportadas para usuario {user_id}")
            except Exception as e:
                logger.warning(f"Error exportando métricas: {e}")

        # Información de cuenta
        if "account" in data_types:
            try:
                account_info = await self._get_account_info(user_id)
                exported_data.account_info = account_info
                logger.debug(f"Información de cuenta exportada para usuario {user_id}")
            except Exception as e:
                logger.warning(f"Error exportando información de cuenta: {e}")

        return exported_data

    async def _get_user_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene las sesiones federadas del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Lista de sesiones en formato diccionario
        """
        # En una implementación real, esto consultaría la base de datos
        # Por ahora, devolver datos de ejemplo basados en archivos existentes
        sessions = []

        # Buscar archivos de sesiones en el directorio data/sessions
        sessions_dir = Path("data/sessions")
        if sessions_dir.exists():
            for session_file in sessions_dir.glob("*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                        # Filtrar por usuario si es necesario
                        sessions.append(session_data)
                except Exception as e:
                    logger.warning(f"Error leyendo sesión {session_file}: {e}")

        return sessions

    async def _get_user_metrics(self, user_id: int) -> Dict[str, Any]:
        """
        Obtiene métricas de uso del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con métricas
        """
        # En una implementación real, esto consultaría logs y métricas
        return {
            "user_id": user_id,
            "total_sessions": 0,
            "total_tokens_used": 0,
            "last_activity": datetime.now().isoformat(),
            "account_created": datetime.now().isoformat(),
            "export_timestamp": datetime.now().isoformat()
        }

    async def _get_account_info(self, user_id: int) -> Dict[str, Any]:
        """
        Obtiene información básica de la cuenta del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con información de cuenta
        """
        # En una implementación real, esto consultaría la base de datos de usuarios
        return {
            "user_id": user_id,
            "account_status": "active",
            "created_at": datetime.now().isoformat(),
            "last_login": datetime.now().isoformat(),
            "gdpr_consent_given": True,
            "gdpr_consent_date": datetime.now().isoformat()
        }

    async def _generate_export_files(self, data: ExportedData, request: ExportRequest) -> Path:
        """
        Genera los archivos de exportación en el formato solicitado.

        Args:
            data: Datos a exportar
            request: Solicitud de exportación

        Returns:
            Path: Ruta al archivo de exportación generado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"gdpr_export_{request.user_id}_{timestamp}"

        if request.format == "json":
            return await self._generate_json_export(data, base_filename)
        elif request.format == "csv":
            return await self._generate_csv_export(data, base_filename)
        elif request.format == "zip":
            return await self._generate_zip_export(data, base_filename)
        else:
            raise ValueError(f"Formato no soportado: {request.format}")

    async def _generate_json_export(self, data: ExportedData, base_filename: str) -> Path:
        """Genera exportación en formato JSON."""
        export_path = self.export_dir / f"{base_filename}.json"

        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(data.to_dict(), f, indent=2, ensure_ascii=False)

        return export_path

    async def _generate_csv_export(self, data: ExportedData, base_filename: str) -> Path:
        """Genera exportación en formato CSV (múltiples archivos)."""
        export_dir = self.export_dir / base_filename
        export_dir.mkdir(exist_ok=True)

        # Exportar memoria como CSV
        if data.memory_items:
            memory_csv = export_dir / "memory.csv"
            with open(memory_csv, 'w', newline='', encoding='utf-8') as f:
                if data.memory_items:
                    writer = csv.DictWriter(f, fieldnames=data.memory_items[0].keys())
                    writer.writeheader()
                    writer.writerows(data.memory_items)

        # Exportar sesiones como CSV
        if data.sessions:
            sessions_csv = export_dir / "sessions.csv"
            with open(sessions_csv, 'w', newline='', encoding='utf-8') as f:
                if data.sessions:
                    writer = csv.DictWriter(f, fieldnames=data.sessions[0].keys())
                    writer.writeheader()
                    writer.writerows(data.sessions)

        # Crear archivo ZIP con todos los CSVs
        zip_path = self.export_dir / f"{base_filename}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for csv_file in export_dir.glob("*.csv"):
                zf.write(csv_file, csv_file.name)

        # Limpiar directorio temporal
        import shutil
        shutil.rmtree(export_dir)

        return zip_path

    async def _generate_zip_export(self, data: ExportedData, base_filename: str) -> Path:
        """Genera exportación completa en formato ZIP."""
        zip_path = self.export_dir / f"{base_filename}.zip"

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Archivo principal JSON
            json_data = json.dumps(data.to_dict(), indent=2, ensure_ascii=False)
            zf.writestr("gdpr_export.json", json_data)

            # Metadatos adicionales
            metadata = {
                "export_info": {
                    "format": "ZIP",
                    "contains": list(data.to_dict().keys()),
                    "gdpr_compliant": True,
                    "generated_at": datetime.now().isoformat()
                }
            }
            zf.writestr("metadata.json", json.dumps(metadata, indent=2, ensure_ascii=False))

        return zip_path

    async def cleanup_old_exports(self, days: int = 30) -> int:
        """
        Limpia exportaciones antiguas.

        Args:
            days: Días de antigüedad para considerar archivos como antiguos

        Returns:
            int: Número de archivos eliminados
        """
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        deleted_count = 0

        for export_file in self.export_dir.glob("*"):
            if export_file.stat().st_mtime < cutoff_date:
                export_file.unlink()
                deleted_count += 1

        # Limpiar solicitudes completadas antiguas
        old_requests = [
            req_id for req_id, request in self.active_exports.items()
            if request.completed_at and
               (datetime.now() - request.completed_at).days > days
        ]

        for req_id in old_requests:
            del self.active_exports[req_id]

        logger.info(f"Limpieza completada: {deleted_count} archivos eliminados, {len(old_requests)} solicitudes limpiadas")
        return deleted_count