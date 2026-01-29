"""
Repositorio para persistencia de memoria conversacional
=====================================================

Este módulo proporciona una capa de persistencia para el sistema de memoria conversacional,
utilizando SQLite para almacenar ítems de memoria de manera eficiente.
"""

import sqlite3
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import os

from .models import MemoryItem, MemoryStats, MemoryQuery

# Configurar logging
logger = logging.getLogger(__name__)


class MemoryRepositoryError(Exception):
    """Excepción base para errores del repositorio de memoria."""
    pass


class MemoryRepository:
    """
    Repositorio para gestión de persistencia de memoria conversacional.

    Proporciona operaciones CRUD completas para ítems de memoria,
    optimizadas para el límite de 256 ítems por usuario.
    """

    def __init__(self, db_path: str = "memory.db"):
        """
        Inicializa el repositorio con la base de datos.

        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = db_path
        self._init_db()
        logger.info(f"Repositorio de memoria inicializado: {db_path}")

    def _init_db(self) -> None:
        """Inicializa la estructura de la base de datos."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Crear tabla de ítems de memoria
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memory_items (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    importance REAL NOT NULL DEFAULT 1.0,
                    timestamp TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'general',
                    tags TEXT,  -- JSON array
                    metadata TEXT,  -- JSON object
                    compressed INTEGER NOT NULL DEFAULT 0,
                    original_length INTEGER NOT NULL DEFAULT 0,
                    access_count INTEGER NOT NULL DEFAULT 0,
                    last_accessed TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Crear índices para optimización
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON memory_items(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_importance ON memory_items(user_id, importance)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_timestamp ON memory_items(user_id, timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_category ON memory_items(user_id, category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_access ON memory_items(user_id, access_count)')

            conn.commit()

    def _item_to_row(self, item: MemoryItem) -> Tuple:
        """Convierte un MemoryItem a tupla para inserción en BD."""
        return (
            item.id,
            item.user_id,
            item.content,
            item.importance,
            item.timestamp.isoformat(),
            item.category,
            json.dumps(item.tags),
            json.dumps(item.metadata),
            1 if item.compressed else 0,
            item.original_length,
            item.access_count,
            item.last_accessed.isoformat() if item.last_accessed else None
        )

    def _row_to_item(self, row) -> MemoryItem:
        """Convierte una fila de BD a MemoryItem."""
        return MemoryItem(
            id=row[0],
            user_id=row[1],
            content=row[2],
            importance=row[3],
            timestamp=datetime.fromisoformat(row[4]),
            category=row[5],
            tags=json.loads(row[6]) if row[6] else [],
            metadata=json.loads(row[7]) if row[7] else {},
            compressed=bool(row[8]),
            original_length=row[9],
            access_count=row[10],
            last_accessed=datetime.fromisoformat(row[11]) if row[11] else None
        )

    # ==================== OPERACIONES CRUD ====================

    def create_memory_item(self, item: MemoryItem) -> bool:
        """
        Crea un nuevo ítem de memoria.

        Args:
            item: Ítem de memoria a crear

        Returns:
            bool: True si se creó exitosamente

        Raises:
            MemoryRepositoryError: Si ocurre un error
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO memory_items
                    (id, user_id, content, importance, timestamp, category, tags, metadata,
                     compressed, original_length, access_count, last_accessed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', self._item_to_row(item))
                conn.commit()
                logger.debug(f"Ítem de memoria creado: {item.id} para usuario {item.user_id}")
                return True
        except sqlite3.IntegrityError:
            raise MemoryRepositoryError(f"Ítem de memoria ya existe: {item.id}")
        except Exception as e:
            logger.error(f"Error al crear ítem de memoria {item.id}: {e}")
            raise MemoryRepositoryError(f"Error al crear ítem de memoria: {e}")

    def get_memory_item(self, item_id: str, user_id: int) -> Optional[MemoryItem]:
        """
        Obtiene un ítem de memoria específico.

        Args:
            item_id: ID del ítem
            user_id: ID del usuario (para seguridad)

        Returns:
            Optional[MemoryItem]: Ítem encontrado o None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, user_id, content, importance, timestamp, category, tags, metadata,
                           compressed, original_length, access_count, last_accessed
                    FROM memory_items
                    WHERE id = ? AND user_id = ?
                ''', (item_id, user_id))

                row = cursor.fetchone()
                if row:
                    item = self._row_to_item(row)
                    # Actualizar estadísticas de acceso
                    self._update_access_stats(item_id, user_id)
                    return item
                return None
        except Exception as e:
            logger.error(f"Error al obtener ítem de memoria {item_id}: {e}")
            raise MemoryRepositoryError(f"Error al obtener ítem de memoria: {e}")

    def update_memory_item(self, item: MemoryItem) -> bool:
        """
        Actualiza un ítem de memoria existente.

        Args:
            item: Ítem actualizado

        Returns:
            bool: True si se actualizó exitosamente
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE memory_items
                    SET content = ?, importance = ?, category = ?, tags = ?, metadata = ?,
                        compressed = ?, original_length = ?, access_count = ?, last_accessed = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                ''', (
                    item.content, item.importance, item.category,
                    json.dumps(item.tags), json.dumps(item.metadata),
                    1 if item.compressed else 0, item.original_length,
                    item.access_count, item.last_accessed.isoformat() if item.last_accessed else None,
                    item.id, item.user_id
                ))
                conn.commit()
                success = cursor.rowcount > 0
                if success:
                    logger.debug(f"Ítem de memoria actualizado: {item.id}")
                return success
        except Exception as e:
            logger.error(f"Error al actualizar ítem de memoria {item.id}: {e}")
            raise MemoryRepositoryError(f"Error al actualizar ítem de memoria: {e}")

    def delete_memory_item(self, item_id: str, user_id: int) -> bool:
        """
        Elimina un ítem de memoria.

        Args:
            item_id: ID del ítem
            user_id: ID del usuario

        Returns:
            bool: True si se eliminó exitosamente
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM memory_items WHERE id = ? AND user_id = ?',
                             (item_id, user_id))
                conn.commit()
                success = cursor.rowcount > 0
                if success:
                    logger.debug(f"Ítem de memoria eliminado: {item_id}")
                return success
        except Exception as e:
            logger.error(f"Error al eliminar ítem de memoria {item_id}: {e}")
            raise MemoryRepositoryError(f"Error al eliminar ítem de memoria: {e}")

    # ==================== CONSULTAS AVANZADAS ====================

    def query_memory_items(self, query: MemoryQuery) -> List[MemoryItem]:
        """
        Consulta ítems de memoria con filtros avanzados.

        Args:
            query: Parámetros de consulta

        Returns:
            List[MemoryItem]: Lista de ítems encontrados
        """
        try:
            conditions = ["user_id = ?"]
            params = [query.user_id]

            # Filtros opcionales
            if query.category:
                conditions.append("category = ?")
                params.append(query.category)

            if query.min_importance is not None:
                conditions.append("importance >= ?")
                params.append(query.min_importance)

            if query.max_importance is not None:
                conditions.append("importance <= ?")
                params.append(query.max_importance)

            if query.since:
                conditions.append("timestamp >= ?")
                params.append(query.since.isoformat())

            if query.until:
                conditions.append("timestamp <= ?")
                params.append(query.until.isoformat())

            if not query.include_compressed:
                conditions.append("compressed = 0")

            # Manejo de tags (búsqueda en JSON)
            if query.tags:
                tag_conditions = []
                for tag in query.tags:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f'%"{tag}"%')
                if tag_conditions:
                    conditions.append(f"({' OR '.join(tag_conditions)})")

            # Ordenamiento
            sort_column = {
                "importance": "importance",
                "timestamp": "timestamp",
                "access_count": "access_count"
            }.get(query.sort_by, "importance")

            sort_order = "DESC" if query.sort_order == "desc" else "ASC"

            # Construir consulta
            sql = f'''
                SELECT id, user_id, content, importance, timestamp, category, tags, metadata,
                       compressed, original_length, access_count, last_accessed
                FROM memory_items
                WHERE {' AND '.join(conditions)}
                ORDER BY {sort_column} {sort_order}
                LIMIT ?
            '''
            params.append(query.limit)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                rows = cursor.fetchall()

                items = []
                for row in rows:
                    item = self._row_to_item(row)
                    # Actualizar estadísticas de acceso para ítems consultados
                    self._update_access_stats(item.id, query.user_id)
                    items.append(item)

                return items

        except Exception as e:
            logger.error(f"Error en consulta de memoria para usuario {query.user_id}: {e}")
            raise MemoryRepositoryError(f"Error en consulta de memoria: {e}")

    def get_user_memory_stats(self, user_id: int) -> MemoryStats:
        """
        Obtiene estadísticas de memoria para un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            MemoryStats: Estadísticas del usuario
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Consulta principal de estadísticas
                cursor.execute('''
                    SELECT
                        COUNT(*) as total_items,
                        SUM(CASE WHEN compressed = 1 THEN 1 ELSE 0 END) as compressed_items,
                        AVG(importance) as avg_importance,
                        MIN(timestamp) as oldest_timestamp,
                        MAX(timestamp) as newest_timestamp,
                        SUM(access_count) as total_access
                    FROM memory_items
                    WHERE user_id = ?
                ''', (user_id,))

                row = cursor.fetchone()
                if not row:
                    return MemoryStats(user_id=user_id)

                # Consulta de categorías
                cursor.execute('''
                    SELECT category, COUNT(*) as count
                    FROM memory_items
                    WHERE user_id = ?
                    GROUP BY category
                ''', (user_id,))

                categories = {row[0]: row[1] for row in cursor.fetchall()}

                stats = MemoryStats(
                    user_id=user_id,
                    total_items=row[0] or 0,
                    compressed_items=row[1] or 0,
                    average_importance=row[2] or 0.0,
                    oldest_item=datetime.fromisoformat(row[3]) if row[3] else None,
                    newest_item=datetime.fromisoformat(row[4]) if row[4] else None,
                    categories_count=categories,
                    total_access_count=row[5] or 0
                )

                return stats

        except Exception as e:
            logger.error(f"Error al obtener estadísticas para usuario {user_id}: {e}")
            raise MemoryRepositoryError(f"Error al obtener estadísticas: {e}")

    # ==================== GESTIÓN DE LÍMITES ====================

    def get_memory_count(self, user_id: int) -> int:
        """
        Obtiene el número total de ítems de memoria para un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            int: Número de ítems
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM memory_items WHERE user_id = ?', (user_id,))
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error al contar ítems para usuario {user_id}: {e}")
            return 0

    def compress_old_items(self, user_id: int, max_items: int, threshold: float) -> int:
        """
        Comprime ítems antiguos de baja importancia para mantener el límite.

        Args:
            user_id: ID del usuario
            max_items: Límite máximo de ítems
            threshold: Umbral de importancia para compresión

        Returns:
            int: Número de ítems comprimidos
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Obtener ítems candidatos para compresión
                cursor.execute('''
                    SELECT id, content, importance, timestamp
                    FROM memory_items
                    WHERE user_id = ? AND compressed = 0 AND importance < ?
                    ORDER BY importance ASC, timestamp ASC
                    LIMIT ?
                ''', (user_id, threshold, max_items // 4))  # Comprimir máximo 25%

                candidates = cursor.fetchall()
                compressed_count = 0

                for item_id, content, importance, timestamp in candidates:
                    # Calcular longitud original
                    original_length = len(content)

                    # Compresión simple (truncar)
                    if len(content) > 200:
                        compressed_content = content[:150] + "...[comprimido]"
                    else:
                        compressed_content = f"[Comprimido] {content}"

                    # Actualizar en BD
                    cursor.execute('''
                        UPDATE memory_items
                        SET content = ?, compressed = 1, original_length = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND user_id = ?
                    ''', (compressed_content, original_length, item_id, user_id))

                    compressed_count += 1

                conn.commit()
                if compressed_count > 0:
                    logger.info(f"Comprimidos {compressed_count} ítems para usuario {user_id}")

                return compressed_count

        except Exception as e:
            logger.error(f"Error al comprimir ítems para usuario {user_id}: {e}")
            raise MemoryRepositoryError(f"Error al comprimir ítems: {e}")

    def delete_old_items(self, user_id: int, max_items: int) -> int:
        """
        Elimina ítems antiguos de muy baja importancia cuando la compresión no es suficiente.

        Args:
            user_id: ID del usuario
            max_items: Límite máximo de ítems

        Returns:
            int: Número de ítems eliminados
        """
        try:
            current_count = self.get_memory_count(user_id)
            if current_count <= max_items:
                return 0

            items_to_delete = current_count - max_items

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Eliminar ítems menos importantes y más antiguos
                cursor.execute('''
                    DELETE FROM memory_items
                    WHERE id IN (
                        SELECT id FROM memory_items
                        WHERE user_id = ?
                        ORDER BY importance ASC, timestamp ASC
                        LIMIT ?
                    )
                ''', (user_id, items_to_delete))

                deleted_count = cursor.rowcount
                conn.commit()

                if deleted_count > 0:
                    logger.warning(f"Eliminados {deleted_count} ítems antiguos para usuario {user_id}")

                return deleted_count

        except Exception as e:
            logger.error(f"Error al eliminar ítems antiguos para usuario {user_id}: {e}")
            raise MemoryRepositoryError(f"Error al eliminar ítems antiguos: {e}")

    # ==================== MÉTODOS DE UTILIDAD ====================

    def _update_access_stats(self, item_id: str, user_id: int) -> None:
        """Actualiza estadísticas de acceso para un ítem."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE memory_items
                    SET access_count = access_count + 1, last_accessed = ?
                    WHERE id = ? AND user_id = ?
                ''', (datetime.now().isoformat(), item_id, user_id))
                conn.commit()
        except Exception:
            # No fallar la operación principal por error en estadísticas
            pass

    def cleanup_database(self) -> None:
        """Limpia y optimiza la base de datos."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('VACUUM')
                cursor.execute('ANALYZE')
                conn.commit()
                logger.info("Base de datos de memoria limpiada y optimizada")
        except Exception as e:
            logger.error(f"Error al limpiar base de datos: {e}")

    def backup_memory(self, user_id: int, backup_path: str) -> bool:
        """
        Crea una copia de respaldo de la memoria de un usuario.

        Args:
            user_id: ID del usuario
            backup_path: Ruta del archivo de respaldo

        Returns:
            bool: True si el respaldo se creó exitosamente
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Adjuntar base de respaldo
                conn.execute(f"ATTACH DATABASE '{backup_path}' AS backup")

                # Copiar datos del usuario
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS backup.memory_backup AS
                    SELECT * FROM main.memory_items WHERE user_id = ?
                ''', (user_id,))

                conn.commit()
                logger.info(f"Respaldo creado para usuario {user_id}: {backup_path}")
                return True

        except Exception as e:
            logger.error(f"Error al crear respaldo para usuario {user_id}: {e}")
            return False