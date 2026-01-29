"""
Sistema de Versioning para control de versiones del grafo de conocimiento.
Implementa snapshots, diffs incrementales, metadatos y gestión de versiones con tags.
"""

import json
import hashlib
import time
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from ..core.logging import get_logger
from .core import KnowledgeGraphCore, Triple, FormatType
from ..auditing.audit_manager import get_audit_manager, AuditEventType
from ..auditing.metrics_collector import get_metrics_collector

logger = get_logger(__name__)


class VersionStatus(Enum):
    """Estados de una versión."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass
class VersionMetadata:
    """Metadatos de una versión del grafo."""
    version_id: str
    timestamp: datetime
    user_id: Optional[str] = None
    description: str = ""
    tags: Set[str] = field(default_factory=set)
    status: VersionStatus = VersionStatus.ACTIVE
    parent_version_id: Optional[str] = None
    checksum: str = ""
    triple_count: int = 0
    size_bytes: int = 0
    format_type: FormatType = FormatType.JSON_LD

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para serialización."""
        return {
            "version_id": self.version_id,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "description": self.description,
            "tags": list(self.tags),
            "status": self.status.value,
            "parent_version_id": self.parent_version_id,
            "checksum": self.checksum,
            "triple_count": self.triple_count,
            "size_bytes": self.size_bytes,
            "format_type": self.format_type.value
        }


@dataclass
class VersionDiff:
    """Diferencias entre dos versiones."""
    from_version: str
    to_version: str
    added_triples: List[Triple] = field(default_factory=list)
    removed_triples: List[Triple] = field(default_factory=list)
    modified_triples: List[Tuple[Triple, Triple]] = field(default_factory=list)  # (old, new)

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "added_triples": [t.to_dict() for t in self.added_triples],
            "removed_triples": [t.to_dict() for t in self.removed_triples],
            "modified_triples": [
                {"old": old.to_dict(), "new": new.to_dict()}
                for old, new in self.modified_triples
            ]
        }


class VersionManager:
    """
    Gestor de versiones para el grafo de conocimiento.
    Maneja snapshots, diffs incrementales, metadatos y tags.
    """

    def __init__(self, knowledge_graph_core: KnowledgeGraphCore):
        self.kg_core = knowledge_graph_core

        # Integraciones
        self.audit_manager = get_audit_manager()
        self.metrics_collector = get_metrics_collector()

        # Almacenamiento de versiones
        self.versions: Dict[str, VersionMetadata] = {}
        self.snapshots: Dict[str, str] = {}  # version_id -> serialized_data
        self.diffs_cache: Dict[str, VersionDiff] = {}  # cache_key -> diff

        # Tags index
        self.tag_index: Dict[str, Set[str]] = {}  # tag -> set of version_ids

        # Configuración
        self.max_versions = 1000  # Máximo número de versiones activas
        self.compression_enabled = True

        logger.info("VersionManager initialized")

    async def create_version(
        self,
        user_id: Optional[str] = None,
        description: str = "",
        tags: Optional[List[str]] = None,
        format_type: FormatType = FormatType.JSON_LD
    ) -> str:
        """
        Crear una nueva versión (snapshot) del grafo de conocimiento.

        Args:
            user_id: ID del usuario que crea la versión
            description: Descripción de la versión
            tags: Lista de tags para la versión
            format_type: Formato para serializar el snapshot

        Returns:
            ID de la versión creada
        """
        start_time = time.time()

        try:
            # Generar ID único para la versión
            timestamp = datetime.now()
            version_data = f"{timestamp.isoformat()}-{user_id or 'system'}"
            version_id = hashlib.sha256(version_data.encode()).hexdigest()[:16]

            # Obtener snapshot del grafo
            snapshot_data = await self._create_snapshot(format_type)

            # Calcular checksum
            checksum = hashlib.sha256(snapshot_data.encode()).hexdigest()

            # Contar triples (aproximado)
            triple_count = self._estimate_triple_count(snapshot_data, format_type)

            # Crear metadatos
            metadata = VersionMetadata(
                version_id=version_id,
                timestamp=timestamp,
                user_id=user_id,
                description=description,
                tags=set(tags or []),
                checksum=checksum,
                triple_count=triple_count,
                size_bytes=len(snapshot_data.encode('utf-8')),
                format_type=format_type
            )

            # Almacenar versión
            self.versions[version_id] = metadata
            self.snapshots[version_id] = snapshot_data

            # Actualizar índices de tags
            for tag in metadata.tags:
                if tag not in self.tag_index:
                    self.tag_index[tag] = set()
                self.tag_index[tag].add(version_id)

            # Limpiar versiones antiguas si excede el límite
            await self._cleanup_old_versions()

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph_versioning",
                action="create_version",
                user_id=user_id,
                details={
                    "version_id": version_id,
                    "description": description,
                    "tags": list(tags or []),
                    "triple_count": triple_count,
                    "size_bytes": metadata.size_bytes
                },
                success=True,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            # Métricas
            self.metrics_collector.record_request("versioning.create_version")
            self.metrics_collector.record_response_time((time.time() - start_time) * 1000)

            logger.info(f"Version created: {version_id}, triples: {triple_count}")
            return version_id

        except Exception as e:
            # Logging de error
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph_versioning",
                action="create_version",
                user_id=user_id,
                details={"error": str(e), "description": description},
                success=False,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            self.metrics_collector.record_error("versioning.create_version", "creation_error")
            logger.error(f"Failed to create version: {e}")
            raise

    async def get_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        """
        Recuperar una versión específica.

        Args:
            version_id: ID de la versión

        Returns:
            Diccionario con metadatos y datos de la versión, o None si no existe
        """
        start_time = time.time()

        try:
            if version_id not in self.versions:
                logger.warning(f"Version not found: {version_id}")
                return None

            metadata = self.versions[version_id]
            snapshot_data = self.snapshots.get(version_id)

            if not snapshot_data:
                logger.error(f"Snapshot data missing for version: {version_id}")
                return None

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph_versioning",
                action="get_version",
                details={"version_id": version_id},
                success=True,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            # Métricas
            self.metrics_collector.record_request("versioning.get_version")
            self.metrics_collector.record_response_time((time.time() - start_time) * 1000)

            return {
                "metadata": metadata.to_dict(),
                "data": snapshot_data
            }

        except Exception as e:
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph_versioning",
                action="get_version",
                details={"error": str(e), "version_id": version_id},
                success=False,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            self.metrics_collector.record_error("versioning.get_version", "retrieval_error")
            logger.error(f"Failed to get version {version_id}: {e}")
            return None

    async def diff_versions(
        self,
        from_version: str,
        to_version: str,
        incremental: bool = True
    ) -> Optional[VersionDiff]:
        """
        Comparar dos versiones y calcular diferencias.

        Args:
            from_version: ID de la versión base
            to_version: ID de la versión a comparar
            incremental: Si usar diff incremental o comparación completa

        Returns:
            VersionDiff con las diferencias, o None si falla
        """
        start_time = time.time()

        try:
            # Verificar que las versiones existen
            if from_version not in self.versions or to_version not in self.versions:
                logger.warning(f"Version(s) not found: {from_version}, {to_version}")
                return None

            # Cache key para diffs
            cache_key = f"{from_version}:{to_version}"
            if cache_key in self.diffs_cache:
                return self.diffs_cache[cache_key]

            # Obtener snapshots
            from_data = self.snapshots.get(from_version)
            to_data = self.snapshots.get(to_version)

            if not from_data or not to_data:
                logger.error(f"Snapshot data missing for versions: {from_version}, {to_version}")
                return None

            # Parsear triples
            from_triples = self._parse_snapshot(from_data, self.versions[from_version].format_type)
            to_triples = self._parse_snapshot(to_data, self.versions[to_version].format_type)

            # Calcular diferencias
            diff = self._calculate_diff(from_triples, to_triples, from_version, to_version)

            # Cachear diff si es incremental
            if incremental:
                self.diffs_cache[cache_key] = diff

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph_versioning",
                action="diff_versions",
                details={
                    "from_version": from_version,
                    "to_version": to_version,
                    "added_count": len(diff.added_triples),
                    "removed_count": len(diff.removed_triples),
                    "modified_count": len(diff.modified_triples)
                },
                success=True,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            # Métricas
            self.metrics_collector.record_request("versioning.diff_versions")
            self.metrics_collector.record_response_time((time.time() - start_time) * 1000)

            logger.info(f"Diff calculated: {from_version} -> {to_version}, "
                       f"added: {len(diff.added_triples)}, removed: {len(diff.removed_triples)}")
            return diff

        except Exception as e:
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph_versioning",
                action="diff_versions",
                details={
                    "error": str(e),
                    "from_version": from_version,
                    "to_version": to_version
                },
                success=False,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            self.metrics_collector.record_error("versioning.diff_versions", "diff_error")
            logger.error(f"Failed to diff versions {from_version} -> {to_version}: {e}")
            return None

    async def rollback(
        self,
        version_id: str,
        user_id: Optional[str] = None,
        create_backup: bool = True
    ) -> bool:
        """
        Revertir el grafo a una versión anterior.

        Args:
            version_id: ID de la versión a la que revertir
            user_id: ID del usuario que realiza el rollback
            create_backup: Si crear una versión de backup antes del rollback

        Returns:
            True si el rollback fue exitoso
        """
        start_time = time.time()

        try:
            # Verificar que la versión existe
            if version_id not in self.versions:
                logger.warning(f"Version not found for rollback: {version_id}")
                return False

            # Crear backup si solicitado
            backup_version_id = None
            if create_backup:
                backup_version_id = await self.create_version(
                    user_id=user_id,
                    description=f"Backup before rollback to {version_id}",
                    tags=["backup", "rollback"]
                )

            # Obtener datos de la versión
            version_data = self.snapshots.get(version_id)
            if not version_data:
                logger.error(f"Snapshot data missing for rollback version: {version_id}")
                return False

            # Parsear triples
            triples = self._parse_snapshot(version_data, self.versions[version_id].format_type)

            # Limpiar grafo actual
            await self.kg_core.clear(user_id=user_id)

            # Cargar triples de la versión
            success_count = 0
            for triple in triples:
                if await self.kg_core.add_triple(triple, user_id=user_id):
                    success_count += 1

            # Logging de auditoría
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph_versioning",
                action="rollback",
                user_id=user_id,
                details={
                    "version_id": version_id,
                    "backup_version_id": backup_version_id,
                    "triples_loaded": success_count,
                    "total_triples": len(triples)
                },
                success=success_count == len(triples),
                processing_time_ms=(time.time() - start_time) * 1000
            )

            # Métricas
            self.metrics_collector.record_request("versioning.rollback")
            self.metrics_collector.record_response_time((time.time() - start_time) * 1000)

            logger.info(f"Rollback completed: {version_id}, loaded {success_count}/{len(triples)} triples")
            return success_count == len(triples)

        except Exception as e:
            await self.audit_manager.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                resource="knowledge_graph_versioning",
                action="rollback",
                user_id=user_id,
                details={"error": str(e), "version_id": version_id},
                success=False,
                processing_time_ms=(time.time() - start_time) * 1000
            )

            self.metrics_collector.record_error("versioning.rollback", "rollback_error")
            logger.error(f"Failed to rollback to version {version_id}: {e}")
            return False

    def list_versions(
        self,
        tag: Optional[str] = None,
        user_id: Optional[str] = None,
        status: VersionStatus = VersionStatus.ACTIVE,
        limit: int = 50
    ) -> List[VersionMetadata]:
        """
        Listar versiones filtradas.

        Args:
            tag: Filtrar por tag
            user_id: Filtrar por usuario
            status: Estado de las versiones
            limit: Número máximo de versiones a retornar

        Returns:
            Lista de metadatos de versiones
        """
        versions = list(self.versions.values())

        # Aplicar filtros
        if tag:
            tag_versions = self.tag_index.get(tag, set())
            versions = [v for v in versions if v.version_id in tag_versions]

        if user_id:
            versions = [v for v in versions if v.user_id == user_id]

        versions = [v for v in versions if v.status == status]

        # Ordenar por timestamp descendente
        versions.sort(key=lambda v: v.timestamp, reverse=True)

        return versions[:limit]

    def add_tag(self, version_id: str, tag: str) -> bool:
        """
        Agregar un tag a una versión.

        Args:
            version_id: ID de la versión
            tag: Tag a agregar

        Returns:
            True si se agregó exitosamente
        """
        if version_id not in self.versions:
            return False

        self.versions[version_id].tags.add(tag)

        if tag not in self.tag_index:
            self.tag_index[tag] = set()
        self.tag_index[tag].add(version_id)

        logger.info(f"Tag '{tag}' added to version {version_id}")
        return True

    def remove_tag(self, version_id: str, tag: str) -> bool:
        """
        Remover un tag de una versión.

        Args:
            version_id: ID de la versión
            tag: Tag a remover

        Returns:
            True si se removió exitosamente
        """
        if version_id not in self.versions:
            return False

        self.versions[version_id].tags.discard(tag)

        if tag in self.tag_index:
            self.tag_index[tag].discard(version_id)
            if not self.tag_index[tag]:
                del self.tag_index[tag]

        logger.info(f"Tag '{tag}' removed from version {version_id}")
        return True

    def get_version_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de versiones.

        Returns:
            Diccionario con estadísticas
        """
        total_versions = len(self.versions)
        active_versions = len([v for v in self.versions.values() if v.status == VersionStatus.ACTIVE])
        archived_versions = len([v for v in self.versions.values() if v.status == VersionStatus.ARCHIVED])

        total_size = sum(v.size_bytes for v in self.versions.values())
        avg_triple_count = sum(v.triple_count for v in self.versions.values()) / max(total_versions, 1)

        return {
            "total_versions": total_versions,
            "active_versions": active_versions,
            "archived_versions": archived_versions,
            "deleted_versions": total_versions - active_versions - archived_versions,
            "total_size_bytes": total_size,
            "average_triple_count": int(avg_triple_count),
            "tags_count": len(self.tag_index),
            "cached_diffs": len(self.diffs_cache)
        }

    async def _create_snapshot(self, format_type: FormatType) -> str:
        """Crear snapshot del grafo actual."""
        return await self.kg_core.export_to_format(format_type) or ""

    def _parse_snapshot(self, data: str, format_type: FormatType) -> List[Triple]:
        """Parsear snapshot a triples."""
        try:
            if format_type == FormatType.JSON_LD:
                return self.kg_core._parse_json_ld(data)
            elif format_type in [FormatType.RDF, FormatType.OWL]:
                return self.kg_core._parse_rdf(data, format_type)
            else:
                # Fallback: intentar JSON-LD
                return self.kg_core._parse_json_ld(data)
        except Exception as e:
            logger.error(f"Error parsing snapshot: {e}")
            return []

    def _calculate_diff(
        self,
        from_triples: List[Triple],
        to_triples: List[Triple],
        from_version: str,
        to_version: str
    ) -> VersionDiff:
        """Calcular diferencias entre dos conjuntos de triples."""
        # Convertir a sets para comparación eficiente
        from_set = set((t.subject, t.predicate, t.object) for t in from_triples)
        to_set = set((t.subject, t.predicate, t.object) for t in to_triples)

        # Triples añadidos
        added = to_set - from_set
        added_triples = [Triple(s, p, o) for s, p, o in added]

        # Triples removidos
        removed = from_set - to_set
        removed_triples = [Triple(s, p, o) for s, p, o in removed]

        # Por simplicidad, no detectar modificaciones (cambios en objeto)
        # En una implementación completa, se podría detectar cambios

        return VersionDiff(
            from_version=from_version,
            to_version=to_version,
            added_triples=added_triples,
            removed_triples=removed_triples
        )

    def _estimate_triple_count(self, data: str, format_type: FormatType) -> int:
        """Estimar número de triples en el snapshot."""
        try:
            if format_type == FormatType.JSON_LD:
                json_data = json.loads(data)
                if "@graph" in json_data:
                    return len(json_data["@graph"])
            # Para otros formatos, estimación simple
            return max(1, len(data.split('\n')))
        except:
            return 0

    async def _cleanup_old_versions(self):
        """Limpiar versiones antiguas si excede el límite."""
        if len(self.versions) <= self.max_versions:
            return

        # Ordenar por timestamp y mantener las más recientes
        sorted_versions = sorted(
            self.versions.values(),
            key=lambda v: v.timestamp,
            reverse=True
        )

        # Marcar versiones antiguas como archived
        for version in sorted_versions[self.max_versions:]:
            if version.status == VersionStatus.ACTIVE:
                version.status = VersionStatus.ARCHIVED
                logger.info(f"Version archived: {version.version_id}")


# Instancia global
_version_manager = None

def get_version_manager(knowledge_graph_core: Optional[KnowledgeGraphCore] = None) -> VersionManager:
    """Obtener instancia global del gestor de versiones."""
    global _version_manager
    if _version_manager is None:
        if knowledge_graph_core is None:
            from .core import get_knowledge_graph_core
            knowledge_graph_core = get_knowledge_graph_core()
        _version_manager = VersionManager(knowledge_graph_core)
    return _version_manager