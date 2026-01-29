from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import json
from .semantic_versioning import SemanticVersion
from .version_manager import VersionManager, VersionEntry
from .model_comparator import ModelComparator, ComparisonResult


@dataclass
class ChangeRecord:
    """Registro de un cambio específico."""
    timestamp: datetime
    version_from: Optional[SemanticVersion]
    version_to: SemanticVersion
    change_type: str  # 'created', 'updated', 'rollback', 'merged'
    description: str
    author: str
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'version_from': str(self.version_from) if self.version_from else None,
            'version_to': str(self.version_to),
            'change_type': self.change_type,
            'description': self.description,
            'author': self.author,
            'metadata': self.metadata or {}
        }


@dataclass
class EvolutionMetrics:
    """Métricas de evolución de un modelo."""
    total_versions: int
    major_releases: int
    minor_releases: int
    patch_releases: int
    average_time_between_versions: Optional[timedelta]
    most_active_period: Optional[Tuple[datetime, datetime]]
    change_frequency: Dict[str, int]  # tipo de cambio -> count
    author_contributions: Dict[str, int]  # author -> count


class VersionHistory:
    """
    Historial completo de cambios y evoluciones de modelos.
    Proporciona análisis detallado del desarrollo y evolución de modelos.
    """

    def __init__(self, version_manager: VersionManager):
        self.version_manager = version_manager
        self.change_records: List[ChangeRecord] = []
        self.comparator = ModelComparator()

    def record_change(self,
                     version_to: SemanticVersion,
                     change_type: str,
                     description: str,
                     author: str,
                     version_from: Optional[SemanticVersion] = None,
                     metadata: Optional[Dict[str, Any]] = None):
        """
        Registrar un cambio en el historial.

        Args:
            version_to: Versión resultante del cambio
            change_type: Tipo de cambio ('created', 'updated', 'rollback', 'merged')
            description: Descripción del cambio
            author: Autor del cambio
            version_from: Versión anterior (si aplica)
            metadata: Metadata adicional del cambio
        """
        record = ChangeRecord(
            timestamp=datetime.now(),
            version_from=version_from,
            version_to=version_to,
            change_type=change_type,
            description=description,
            author=author,
            metadata=metadata or {}
        )

        self.change_records.append(record)

    def get_change_history(self,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None,
                          author: Optional[str] = None,
                          change_type: Optional[str] = None,
                          limit: Optional[int] = None) -> List[ChangeRecord]:
        """
        Obtener historial de cambios con filtros.

        Args:
            start_date: Fecha inicial
            end_date: Fecha final
            author: Filtrar por autor
            change_type: Filtrar por tipo de cambio
            limit: Número máximo de registros

        Returns:
            Lista de registros de cambios
        """
        records = self.change_records

        if start_date:
            records = [r for r in records if r.timestamp >= start_date]
        if end_date:
            records = [r for r in records if r.timestamp <= end_date]
        if author:
            records = [r for r in records if r.author == author]
        if change_type:
            records = [r for r in records if r.change_type == change_type]

        # Ordenar por timestamp descendente
        records.sort(key=lambda r: r.timestamp, reverse=True)

        if limit:
            records = records[:limit]

        return records

    def get_version_evolution(self, version: SemanticVersion) -> List[Dict[str, Any]]:
        """
        Obtener evolución completa de una versión específica.

        Args:
            version: Versión a analizar

        Returns:
            Lista de cambios que llevaron a esta versión
        """
        evolution = []
        current = version

        # Recorrer hacia atrás desde la versión actual
        while current:
            # Encontrar cambios que resultaron en esta versión
            changes = [r for r in self.change_records if r.version_to == current]
            if changes:
                # Tomar el cambio más reciente
                change = max(changes, key=lambda r: r.timestamp)
                evolution.append({
                    'version': str(current),
                    'change': change.to_dict(),
                    'version_entry': self._get_version_entry(current)
                })
                current = change.version_from
            else:
                # No hay más cambios registrados
                break

        return evolution

    def compare_versions_detailed(self,
                                 version_a: SemanticVersion,
                                 version_b: SemanticVersion) -> Dict[str, Any]:
        """
        Comparación detallada entre dos versiones incluyendo cambios históricos.

        Args:
            version_a: Primera versión
            version_b: Segunda versión

        Returns:
            Diccionario con comparación completa
        """
        # Obtener entradas de versión
        entry_a = self.version_manager.versions.get(str(version_a))
        entry_b = self.version_manager.versions.get(str(version_b))

        if not entry_a or not entry_b:
            raise ValueError("Una o ambas versiones no existen")

        # Comparación básica de modelos
        comparison = self.comparator.compare_models(
            model_a=entry_a.model_data,
            model_b=entry_b.model_data,
            version_a=str(version_a),
            version_b=str(version_b),
            metrics_a=entry_a.metadata.get('quality_metrics', {}),
            metrics_b=entry_b.metadata.get('quality_metrics', {})
        )

        # Agregar información histórica
        evolution_a = self.get_version_evolution(version_a)
        evolution_b = self.get_version_evolution(version_b)

        # Encontrar ancestro común
        common_ancestor = self._find_common_ancestor(version_a, version_b)

        # Calcular cambios desde ancestro común
        changes_since_ancestor_a = self._get_changes_since_version(common_ancestor, version_a)
        changes_since_ancestor_b = self._get_changes_since_version(common_ancestor, version_b)

        return {
            'comparison': {
                'version_a': str(version_a),
                'version_b': str(version_b),
                'similarity_score': comparison.similarity_score,
                'breaking_changes': comparison.breaking_changes,
                'parameter_differences': comparison.parameter_differences,
                'architecture_changes': comparison.architecture_changes,
                'performance_metrics_diff': comparison.performance_metrics_diff
            },
            'evolution': {
                'version_a_evolution': evolution_a,
                'version_b_evolution': evolution_b,
                'common_ancestor': str(common_ancestor) if common_ancestor else None,
                'changes_since_ancestor_a': changes_since_ancestor_a,
                'changes_since_ancestor_b': changes_since_ancestor_b
            },
            'timeline': self._build_timeline(version_a, version_b)
        }

    def get_evolution_metrics(self,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> EvolutionMetrics:
        """
        Calcular métricas de evolución del modelo.

        Args:
            start_date: Fecha inicial para análisis
            end_date: Fecha final para análisis

        Returns:
            Métricas de evolución
        """
        # Filtrar cambios por fecha
        records = self.get_change_history(start_date=start_date, end_date=end_date)

        if not records:
            return EvolutionMetrics(
                total_versions=0,
                major_releases=0,
                minor_releases=0,
                patch_releases=0,
                average_time_between_versions=None,
                most_active_period=None,
                change_frequency={},
                author_contributions={}
            )

        # Contar tipos de versiones
        major_releases = 0
        minor_releases = 0
        patch_releases = 0

        versions = set()
        for record in records:
            versions.add(record.version_to)
            if record.version_to.major > 0:  # Simplificación
                if record.change_type == 'created':
                    major_releases += 1
                elif record.change_type == 'updated':
                    if record.version_from:
                        if record.version_to.minor > record.version_from.minor:
                            minor_releases += 1
                        elif record.version_to.patch > record.version_from.patch:
                            patch_releases += 1

        # Calcular tiempo promedio entre versiones
        timestamps = sorted([r.timestamp for r in records])
        if len(timestamps) > 1:
            intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
            avg_time = sum(intervals, timedelta()) / len(intervals)
        else:
            avg_time = None

        # Encontrar período más activo (últimos 30 días con más cambios)
        most_active = self._find_most_active_period(records)

        # Frecuencia de cambios por tipo
        change_freq = defaultdict(int)
        for record in records:
            change_freq[record.change_type] += 1

        # Contribuciones por autor
        author_contrib = defaultdict(int)
        for record in records:
            author_contrib[record.author] += 1

        return EvolutionMetrics(
            total_versions=len(versions),
            major_releases=major_releases,
            minor_releases=minor_releases,
            patch_releases=patch_releases,
            average_time_between_versions=avg_time,
            most_active_period=most_active,
            change_frequency=dict(change_freq),
            author_contributions=dict(author_contrib)
        )

    def export_history(self, file_path: str, format: str = 'json'):
        """
        Exportar historial completo a archivo.

        Args:
            file_path: Ruta del archivo
            format: Formato de exportación ('json')
        """
        if format == 'json':
            data = {
                'change_records': [r.to_dict() for r in self.change_records],
                'exported_at': datetime.now().isoformat(),
                'total_changes': len(self.change_records)
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    def import_history(self, file_path: str):
        """
        Importar historial desde archivo.

        Args:
            file_path: Ruta del archivo
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for record_data in data.get('change_records', []):
            record = ChangeRecord(
                timestamp=datetime.fromisoformat(record_data['timestamp']),
                version_from=SemanticVersion(record_data['version_from']) if record_data.get('version_from') else None,
                version_to=SemanticVersion(record_data['version_to']),
                change_type=record_data['change_type'],
                description=record_data['description'],
                author=record_data['author'],
                metadata=record_data.get('metadata', {})
            )
            self.change_records.append(record)

    def _get_version_entry(self, version: SemanticVersion) -> Optional[Dict[str, Any]]:
        """Obtener entrada de versión como diccionario."""
        entry = self.version_manager.versions.get(str(version))
        if entry:
            return {
                'version': str(entry.version),
                'created_at': entry.created_at.isoformat(),
                'branch': entry.branch,
                'commit_message': entry.commit_message,
                'metadata': entry.metadata
            }
        return None

    def _find_common_ancestor(self, version_a: SemanticVersion, version_b: SemanticVersion) -> Optional[SemanticVersion]:
        """Encontrar ancestro común entre dos versiones."""
        # Algoritmo simplificado: buscar en el historial
        ancestors_a = set()
        current = version_a
        while current:
            ancestors_a.add(current)
            entry = self.version_manager.versions.get(str(current))
            current = entry.parent_version if entry else None

        current = version_b
        while current:
            if current in ancestors_a:
                return current
            entry = self.version_manager.versions.get(str(current))
            current = entry.parent_version if entry else None

        return None

    def _get_changes_since_version(self, from_version: Optional[SemanticVersion], to_version: SemanticVersion) -> List[ChangeRecord]:
        """Obtener cambios desde una versión hasta otra."""
        if not from_version:
            return [r for r in self.change_records if r.version_to == to_version]

        changes = []
        current = to_version

        while current and current != from_version:
            version_changes = [r for r in self.change_records if r.version_to == current]
            changes.extend(version_changes)

            entry = self.version_manager.versions.get(str(current))
            current = entry.parent_version if entry else None

        return changes

    def _build_timeline(self, version_a: SemanticVersion, version_b: SemanticVersion) -> List[Dict[str, Any]]:
        """Construir línea de tiempo combinada de ambas versiones."""
        timeline = []

        # Recopilar todos los cambios relevantes
        all_changes = []
        for record in self.change_records:
            if record.version_to in [version_a, version_b] or record.version_from in [version_a, version_b]:
                all_changes.append(record)

        # Ordenar por timestamp
        all_changes.sort(key=lambda r: r.timestamp)

        for change in all_changes:
            timeline.append({
                'timestamp': change.timestamp.isoformat(),
                'version': str(change.version_to),
                'change_type': change.change_type,
                'description': change.description,
                'author': change.author
            })

        return timeline

    def _find_most_active_period(self, records: List[ChangeRecord]) -> Optional[Tuple[datetime, datetime]]:
        """Encontrar el período de 30 días más activo."""
        if len(records) < 2:
            return None

        # Agrupar por períodos de 30 días
        records.sort(key=lambda r: r.timestamp)
        start = records[0].timestamp
        end = records[-1].timestamp

        max_count = 0
        best_period = None

        current_start = start
        while current_start < end:
            current_end = current_start + timedelta(days=30)
            count = sum(1 for r in records if current_start <= r.timestamp <= current_end)

            if count > max_count:
                max_count = count
                best_period = (current_start, current_end)

            current_start += timedelta(days=1)

        return best_period