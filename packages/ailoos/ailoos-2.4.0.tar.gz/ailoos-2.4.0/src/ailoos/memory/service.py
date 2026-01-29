"""
Servicio de negocio para el sistema de memoria conversacional
===========================================================

Este módulo proporciona una capa de negocio completa para el sistema de memoria conversacional,
incluyendo gestión automática de límites, compresión inteligente y integración con configuraciones.
"""

import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import threading

from .models import MemoryItem, MemoryStats, MemoryQuery, create_memory_item, calculate_compression_threshold
from .repository import MemoryRepository, MemoryRepositoryError

# Configurar logging
logger = logging.getLogger(__name__)


class MemoryServiceError(Exception):
    """Excepción base para errores del servicio de memoria."""
    pass


class MemoryLimitExceededError(MemoryServiceError):
    """Error cuando se excede el límite de memoria."""
    pass


class InvalidMemoryItemError(MemoryServiceError):
    """Error de validación de ítem de memoria."""
    pass


class MemoryService:
    """
    Servicio de negocio para gestión de memoria conversacional.

    Proporciona una interfaz de alto nivel con gestión automática de límites,
    compresión inteligente basada en importancia, y operaciones de negocio complejas.
    """

    def __init__(self, db_path: str = "memory.db", settings_service = None):
        """
        Inicializa el servicio de memoria.

        Args:
            db_path: Ruta a la base de datos de memoria
            settings_service: Servicio de configuraciones (opcional, se integra después)
        """
        self.repository = MemoryRepository(db_path)
        self.settings_service = settings_service
        self._lock = threading.RLock()  # Thread-safe operations
        self._maintenance_thread = None
        self._stop_maintenance = threading.Event()

        # Configuración por defecto
        self.default_max_items = 256
        self.compression_enabled = True
        self.auto_cleanup_enabled = True

        logger.info("Servicio de memoria inicializado")

        # Integrar con servicio de configuraciones si se proporciona
        if settings_service:
            self.set_settings_service(settings_service)

    def _get_user_memory_limit(self, user_id: int) -> int:
        """
        Obtiene el límite de memoria para un usuario desde configuraciones.

        Args:
            user_id: ID del usuario

        Returns:
            int: Límite máximo de ítems
        """
        if self.settings_service:
            try:
                settings = self.settings_service.get_user_settings(user_id)
                return settings.memory.max_memory_items
            except Exception as e:
                logger.warning(f"Error al obtener límite de memoria para usuario {user_id}: {e}")
                # Actualizar contador de memoria usada en configuraciones
                try:
                    current_count = self.repository.get_memory_count(user_id)
                    self.settings_service.update_category_settings(
                        user_id, 'memory', {'memory_used': current_count}, validate=False
                    )
                except Exception:
                    pass  # No fallar por actualización de estadísticas

        return self.default_max_items

    def _should_compress_for_user(self, user_id: int) -> bool:
        """
        Determina si la compresión está habilitada para un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            bool: True si la compresión está habilitada
        """
        if self.settings_service:
            try:
                settings = self.settings_service.get_user_settings(user_id)
                return settings.memory.reference_memories  # Usar como indicador de compresión
            except Exception as e:
                logger.warning(f"Error al verificar configuración de compresión para usuario {user_id}: {e}")

        return self.compression_enabled

    # ==================== GESTIÓN DE ÍTEMS DE MEMORIA ====================

    def add_memory_item(self, user_id: int, content: str, importance: float = 1.0,
                       category: str = "general", tags: Optional[List[str]] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> MemoryItem:
        """
        Agrega un nuevo ítem de memoria con gestión automática de límites.

        Args:
            user_id: ID del usuario
            content: Contenido de la memoria
            importance: Nivel de importancia (0.0-1.0)
            category: Categoría de la memoria
            tags: Lista de etiquetas
            metadata: Metadatos adicionales

        Returns:
            MemoryItem: Ítem creado

        Raises:
            InvalidMemoryItemError: Si los datos son inválidos
            MemoryLimitExceededError: Si se excede el límite y no se puede gestionar
        """
        with self._lock:
            try:
                # Crear y validar ítem
                item = create_memory_item(user_id, content, importance, category, tags, metadata)

                # Verificar límites antes de agregar
                max_items = self._get_user_memory_limit(user_id)
                current_count = self.repository.get_memory_count(user_id)

                if current_count >= max_items:
                    # Intentar gestión automática de memoria
                    if not self._manage_memory_limit(user_id, max_items):
                        raise MemoryLimitExceededError(
                            f"Límite de memoria excedido ({max_items} ítems). "
                            "No se puede agregar nuevo ítem."
                        )

                # Crear ítem en repositorio
                success = self.repository.create_memory_item(item)
                if not success:
                    raise MemoryServiceError("Error al crear ítem de memoria")

                # Actualizar estadísticas en configuraciones
                if self.settings_service:
                    try:
                        new_count = current_count + 1
                        self.settings_service.update_category_settings(
                            user_id, 'memory', {'memory_used': new_count}, validate=False
                        )
                    except Exception as e:
                        logger.warning(f"Error al actualizar estadísticas de memoria: {e}")

                logger.info(f"Ítem de memoria agregado para usuario {user_id}: {item.id}")
                return item

            except ValueError as e:
                raise InvalidMemoryItemError(f"Datos inválidos: {e}")
            except MemoryRepositoryError as e:
                logger.error(f"Error del repositorio al agregar ítem para usuario {user_id}: {e}")
                raise MemoryServiceError(f"Error al agregar ítem de memoria: {e}")

    def get_memory_item(self, item_id: str, user_id: int) -> Optional[MemoryItem]:
        """
        Obtiene un ítem de memoria específico.

        Args:
            item_id: ID del ítem
            user_id: ID del usuario (seguridad)

        Returns:
            Optional[MemoryItem]: Ítem encontrado o None
        """
        try:
            return self.repository.get_memory_item(item_id, user_id)
        except MemoryRepositoryError as e:
            logger.error(f"Error al obtener ítem {item_id} para usuario {user_id}: {e}")
            raise MemoryServiceError(f"Error al obtener ítem de memoria: {e}")

    def update_memory_item(self, item_id: str, user_id: int, updates: Dict[str, Any]) -> Optional[MemoryItem]:
        """
        Actualiza un ítem de memoria existente.

        Args:
            item_id: ID del ítem
            user_id: ID del usuario
            updates: Campos a actualizar

        Returns:
            Optional[MemoryItem]: Ítem actualizado o None si no existe

        Raises:
            InvalidMemoryItemError: Si los datos de actualización son inválidos
        """
        with self._lock:
            try:
                # Obtener ítem actual
                item = self.get_memory_item(item_id, user_id)
                if not item:
                    return None

                # Aplicar actualizaciones
                for key, value in updates.items():
                    if hasattr(item, key):
                        setattr(item, key, value)

                # Validar ítem actualizado
                errors = item.validate()
                if errors:
                    raise InvalidMemoryItemError(f"Errores de validación: {errors}")

                # Actualizar en repositorio
                success = self.repository.update_memory_item(item)
                if not success:
                    raise MemoryServiceError("Error al actualizar ítem en repositorio")

                logger.info(f"Ítem de memoria actualizado: {item_id}")
                return item

            except InvalidMemoryItemError:
                raise
            except MemoryRepositoryError as e:
                logger.error(f"Error del repositorio al actualizar ítem {item_id}: {e}")
                raise MemoryServiceError(f"Error al actualizar ítem de memoria: {e}")

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
            success = self.repository.delete_memory_item(item_id, user_id)
            if success:
                # Actualizar estadísticas en configuraciones
                if self.settings_service:
                    try:
                        current_count = self.repository.get_memory_count(user_id)
                        self.settings_service.update_category_settings(
                            user_id, 'memory', {'memory_used': current_count}, validate=False
                        )
                    except Exception as e:
                        logger.warning(f"Error al actualizar estadísticas de memoria: {e}")

                logger.info(f"Ítem de memoria eliminado: {item_id}")
            return success
        except MemoryRepositoryError as e:
            logger.error(f"Error al eliminar ítem {item_id} para usuario {user_id}: {e}")
            raise MemoryServiceError(f"Error al eliminar ítem de memoria: {e}")

    # ==================== CONSULTAS Y BÚSQUEDA ====================

    def query_memory(self, user_id: int, category: Optional[str] = None,
                    min_importance: Optional[float] = None, max_importance: Optional[float] = None,
                    tags: Optional[List[str]] = None, since: Optional[datetime] = None,
                    until: Optional[datetime] = None, limit: int = 50,
                    include_compressed: bool = True, sort_by: str = "importance",
                    sort_order: str = "desc") -> List[MemoryItem]:
        """
        Consulta ítems de memoria con filtros avanzados.

        Args:
            user_id: ID del usuario
            category: Filtrar por categoría
            min_importance: Importancia mínima
            max_importance: Importancia máxima
            tags: Filtrar por etiquetas
            since: Fecha desde
            until: Fecha hasta
            limit: Número máximo de resultados
            include_compressed: Incluir ítems comprimidos
            sort_by: Campo de ordenamiento
            sort_order: Orden (asc/desc)

        Returns:
            List[MemoryItem]: Lista de ítems encontrados
        """
        try:
            query = MemoryQuery(
                user_id=user_id, category=category, min_importance=min_importance,
                max_importance=max_importance, tags=tags, since=since, until=until,
                limit=limit, include_compressed=include_compressed,
                sort_by=sort_by, sort_order=sort_order
            )

            return self.repository.query_memory_items(query)

        except MemoryRepositoryError as e:
            logger.error(f"Error en consulta de memoria para usuario {user_id}: {e}")
            raise MemoryServiceError(f"Error en consulta de memoria: {e}")

    def get_recent_memories(self, user_id: int, limit: int = 10) -> List[MemoryItem]:
        """
        Obtiene los ítems de memoria más recientes.

        Args:
            user_id: ID del usuario
            limit: Número máximo de ítems

        Returns:
            List[MemoryItem]: Ítems más recientes
        """
        return self.query_memory(user_id, limit=limit, sort_by="timestamp", sort_order="desc")

    def get_important_memories(self, user_id: int, min_importance: float = 0.7,
                              limit: int = 20) -> List[MemoryItem]:
        """
        Obtiene los ítems de memoria más importantes.

        Args:
            user_id: ID del usuario
            min_importance: Importancia mínima
            limit: Número máximo de ítems

        Returns:
            List[MemoryItem]: Ítems más importantes
        """
        return self.query_memory(user_id, min_importance=min_importance, limit=limit)

    def search_memory_by_content(self, user_id: int, search_term: str,
                                limit: int = 20) -> List[MemoryItem]:
        """
        Busca ítems de memoria por contenido (búsqueda simple).

        Args:
            user_id: ID del usuario
            search_term: Término de búsqueda
            limit: Número máximo de resultados

        Returns:
            List[MemoryItem]: Ítems que contienen el término
        """
        # Nota: Esta es una implementación básica. En producción, considerar búsqueda full-text
        try:
            # Obtener todos los ítems y filtrar (no eficiente para grandes volúmenes)
            all_items = self.query_memory(user_id, limit=1000, include_compressed=True)

            matching_items = []
            search_lower = search_term.lower()

            for item in all_items:
                if (search_lower in item.content.lower() or
                    any(search_lower in tag.lower() for tag in item.tags) or
                    search_lower in item.category.lower()):
                    matching_items.append(item)
                    if len(matching_items) >= limit:
                        break

            return matching_items

        except MemoryServiceError:
            raise
        except Exception as e:
            logger.error(f"Error en búsqueda de memoria para usuario {user_id}: {e}")
            raise MemoryServiceError(f"Error en búsqueda de memoria: {e}")

    # ==================== GESTIÓN AUTOMÁTICA DE MEMORIA ====================

    def _manage_memory_limit(self, user_id: int, max_items: int) -> bool:
        """
        Gestiona automáticamente el límite de memoria mediante compresión y eliminación.

        Args:
            user_id: ID del usuario
            max_items: Límite máximo

        Returns:
            bool: True si se liberó espacio suficiente
        """
        try:
            current_count = self.repository.get_memory_count(user_id)
            if current_count < max_items:
                return True

            # Calcular umbral de compresión basado en uso
            threshold = calculate_compression_threshold(current_count, max_items)

            # Intentar compresión primero
            if self._should_compress_for_user(user_id):
                compressed = self.repository.compress_old_items(user_id, max_items, threshold)
                current_count = self.repository.get_memory_count(user_id)

                if current_count < max_items:
                    # Actualizar estadísticas en configuraciones
                    if self.settings_service:
                        try:
                            self.settings_service.update_category_settings(
                                user_id, 'memory', {'memory_used': current_count}, validate=False
                            )
                        except Exception as e:
                            logger.warning(f"Error al actualizar estadísticas después de compresión: {e}")

                    logger.info(f"Compresión exitosa para usuario {user_id}: {compressed} ítems comprimidos")
                    return True

            # Si la compresión no es suficiente, eliminar ítems antiguos
            if self.auto_cleanup_enabled:
                deleted = self.repository.delete_old_items(user_id, max_items)
                current_count = self.repository.get_memory_count(user_id)

                if current_count < max_items:
                    # Actualizar estadísticas en configuraciones
                    if self.settings_service:
                        try:
                            self.settings_service.update_category_settings(
                                user_id, 'memory', {'memory_used': current_count}, validate=False
                            )
                        except Exception as e:
                            logger.warning(f"Error al actualizar estadísticas después de eliminación: {e}")

                    logger.warning(f"Eliminación automática para usuario {user_id}: {deleted} ítems eliminados")
                    return True

            return False

        except Exception as e:
            logger.error(f"Error en gestión automática de memoria para usuario {user_id}: {e}")
            return False

    def force_memory_cleanup(self, user_id: int) -> Dict[str, int]:
        """
        Fuerza una limpieza completa de memoria para un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Dict[str, int]: Estadísticas de la limpieza
        """
        with self._lock:
            try:
                max_items = self._get_user_memory_limit(user_id)
                initial_count = self.repository.get_memory_count(user_id)

                # Aplicar gestión de memoria agresiva
                threshold = 0.5  # Umbral más alto para limpieza forzada
                compressed = self.repository.compress_old_items(user_id, max_items, threshold)
                deleted = self.repository.delete_old_items(user_id, max_items)

                final_count = self.repository.get_memory_count(user_id)

                result = {
                    'initial_count': initial_count,
                    'compressed': compressed,
                    'deleted': deleted,
                    'final_count': final_count
                }

                logger.info(f"Limpieza forzada completada para usuario {user_id}: {result}")
                return result

            except Exception as e:
                logger.error(f"Error en limpieza forzada para usuario {user_id}: {e}")
                raise MemoryServiceError(f"Error en limpieza de memoria: {e}")

    # ==================== ESTADÍSTICAS Y MONITOREO ====================

    def get_memory_stats(self, user_id: int) -> MemoryStats:
        """
        Obtiene estadísticas completas de memoria para un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            MemoryStats: Estadísticas de memoria
        """
        try:
            return self.repository.get_user_memory_stats(user_id)
        except MemoryRepositoryError as e:
            logger.error(f"Error al obtener estadísticas para usuario {user_id}: {e}")
            raise MemoryServiceError(f"Error al obtener estadísticas: {e}")

    def get_memory_usage_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Obtiene un resumen ejecutivo del uso de memoria.

        Args:
            user_id: ID del usuario

        Returns:
            Dict[str, Any]: Resumen de uso
        """
        try:
            stats = self.get_memory_stats(user_id)
            max_items = self._get_user_memory_limit(user_id)

            return {
                'user_id': user_id,
                'current_usage': stats.total_items,
                'max_capacity': max_items,
                'usage_percentage': (stats.total_items / max_items * 100) if max_items > 0 else 0,
                'compressed_items': stats.compressed_items,
                'compression_rate': (stats.compressed_items / stats.total_items * 100) if stats.total_items > 0 else 0,
                'average_importance': stats.average_importance,
                'categories': stats.categories_count,
                'total_access_count': stats.total_access_count,
                'memory_health': self._calculate_memory_health(stats, max_items)
            }

        except MemoryServiceError:
            raise
        except Exception as e:
            logger.error(f"Error al generar resumen para usuario {user_id}: {e}")
            raise MemoryServiceError(f"Error al generar resumen: {e}")

    def _calculate_memory_health(self, stats: MemoryStats, max_items: int) -> str:
        """
        Calcula el estado de salud de la memoria basado en estadísticas.

        Args:
            stats: Estadísticas de memoria
            max_items: Límite máximo

        Returns:
            str: Estado de salud ("healthy", "warning", "critical")
        """
        usage_ratio = stats.total_items / max_items if max_items > 0 else 0
        compression_ratio = stats.compressed_items / stats.total_items if stats.total_items > 0 else 0

        if usage_ratio < 0.7 and compression_ratio < 0.3:
            return "healthy"
        elif usage_ratio < 0.9 and compression_ratio < 0.5:
            return "warning"
        else:
            return "critical"

    # ==================== MANTENIMIENTO AUTOMÁTICO ====================

    def start_maintenance_thread(self, interval_hours: int = 24) -> None:
        """
        Inicia un hilo de mantenimiento automático.

        Args:
            interval_hours: Intervalo entre mantenimientos en horas
        """
        if self._maintenance_thread and self._maintenance_thread.is_alive():
            return

        self._stop_maintenance.clear()

        def maintenance_worker():
            while not self._stop_maintenance.is_set():
                try:
                    self._perform_maintenance()
                except Exception as e:
                    logger.error(f"Error en mantenimiento automático: {e}")

                # Esperar hasta el próximo intervalo
                self._stop_maintenance.wait(interval_hours * 3600)

        self._maintenance_thread = threading.Thread(target=maintenance_worker, daemon=True)
        self._maintenance_thread.start()
        logger.info(f"Hilo de mantenimiento iniciado (intervalo: {interval_hours}h)")

    def stop_maintenance_thread(self) -> None:
        """Detiene el hilo de mantenimiento automático."""
        if self._maintenance_thread:
            self._stop_maintenance.set()
            self._maintenance_thread.join(timeout=5)
            logger.info("Hilo de mantenimiento detenido")

    def _perform_maintenance(self) -> None:
        """Realiza tareas de mantenimiento automático."""
        try:
            # Limpiar base de datos
            self.repository.cleanup_database()

            # Log de mantenimiento completado
            logger.info("Mantenimiento automático completado")

        except Exception as e:
            logger.error(f"Error en mantenimiento automático: {e}")

    # ==================== INTEGRACIÓN CON CONFIGURACIONES ====================

    def set_settings_service(self, settings_service) -> None:
        """
        Establece el servicio de configuraciones para integración.

        Args:
            settings_service: Instancia del servicio de configuraciones
        """
        self.settings_service = settings_service
        logger.info("Servicio de configuraciones integrado con memoria")

    # ==================== EXPORTACIÓN E IMPORTACIÓN ====================

    def export_user_memory(self, user_id: int) -> Dict[str, Any]:
        """
        Exporta toda la memoria de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Dict[str, Any]: Datos exportados
        """
        try:
            # Obtener todos los ítems
            all_items = self.query_memory(user_id, limit=10000, include_compressed=True)

            # Obtener estadísticas
            stats = self.get_memory_stats(user_id)

            return {
                'user_id': user_id,
                'export_timestamp': datetime.now().isoformat(),
                'memory_items': [item.to_dict() for item in all_items],
                'stats': stats.to_dict(),
                'version': '1.0'
            }

        except MemoryServiceError:
            raise
        except Exception as e:
            logger.error(f"Error al exportar memoria para usuario {user_id}: {e}")
            raise MemoryServiceError(f"Error al exportar memoria: {e}")

    def import_user_memory(self, user_id: int, data: Dict[str, Any],
                          merge_strategy: str = "replace") -> int:
        """
        Importa memoria desde datos exportados.

        Args:
            user_id: ID del usuario destino
            data: Datos exportados
            merge_strategy: Estrategia de fusión ("replace", "merge", "skip")

        Returns:
            int: Número de ítems importados

        Raises:
            InvalidMemoryItemError: Si los datos son inválidos
        """
        with self._lock:
            try:
                if 'memory_items' not in data:
                    raise InvalidMemoryItemError("Datos de importación inválidos")

                imported_count = 0

                if merge_strategy == "replace":
                    # Limpiar memoria existente (excepto ítems críticos)
                    self._clear_user_memory(user_id)

                for item_data in data['memory_items']:
                    try:
                        # Convertir datos a MemoryItem
                        item = MemoryItem.from_dict(item_data)
                        item.user_id = user_id  # Asegurar propiedad

                        # Verificar si ya existe
                        existing = self.get_memory_item(item.id, user_id)
                        if existing and merge_strategy == "skip":
                            continue

                        # Crear o actualizar
                        if existing:
                            self.repository.update_memory_item(item)
                        else:
                            self.repository.create_memory_item(item)

                        imported_count += 1

                    except Exception as e:
                        logger.warning(f"Error al importar ítem {item_data.get('id', 'unknown')}: {e}")
                        continue

                # Gestionar límites después de importación
                max_items = self._get_user_memory_limit(user_id)
                self._manage_memory_limit(user_id, max_items)

                logger.info(f"Importación completada para usuario {user_id}: {imported_count} ítems")
                return imported_count

            except InvalidMemoryItemError:
                raise
            except Exception as e:
                logger.error(f"Error al importar memoria para usuario {user_id}: {e}")
                raise MemoryServiceError(f"Error al importar memoria: {e}")

    def _clear_user_memory(self, user_id: int) -> None:
        """Limpia toda la memoria de un usuario (operación interna)."""
        try:
            # Obtener todos los ítems y eliminarlos uno por uno
            # (En producción, implementar eliminación masiva en repositorio)
            all_items = self.query_memory(user_id, limit=10000)
            for item in all_items:
                self.repository.delete_memory_item(item.id, user_id)

            # Actualizar estadísticas en configuraciones
            if self.settings_service:
                try:
                    self.settings_service.update_category_settings(
                        user_id, 'memory', {'memory_used': 0}, validate=False
                    )
                except Exception as e:
                    logger.warning(f"Error al actualizar estadísticas después de limpieza: {e}")

            logger.info(f"Memoria limpiada para usuario {user_id}")

        except Exception as e:
            logger.error(f"Error al limpiar memoria para usuario {user_id}: {e}")

    # ==================== MÉTODOS DE ALTO NIVEL ====================

    def remember_conversation_context(self, user_id: int, context: str,
                                    importance: float = 0.7) -> MemoryItem:
        """
        Almacena un contexto de conversación importante.

        Args:
            user_id: ID del usuario
            context: Contexto a recordar
            importance: Nivel de importancia (0.0-1.0)

        Returns:
            MemoryItem: Ítem de memoria creado
        """
        return self.add_memory_item(
            user_id=user_id,
            content=context,
            importance=importance,
            category="contextual",
            tags=["conversation", "context"]
        )

    def remember_user_preference(self, user_id: int, preference: str,
                               category: str = "personal") -> MemoryItem:
        """
        Almacena una preferencia del usuario.

        Args:
            user_id: ID del usuario
            preference: Preferencia a recordar
            category: Categoría de la preferencia

        Returns:
            MemoryItem: Ítem de memoria creado
        """
        return self.add_memory_item(
            user_id=user_id,
            content=preference,
            importance=0.8,
            category=category,
            tags=["preference", "user"]
        )

    def remember_fact(self, user_id: int, fact: str, source: str = "conversation") -> MemoryItem:
        """
        Almacena un hecho importante.

        Args:
            user_id: ID del usuario
            fact: Hecho a recordar
            source: Fuente del hecho

        Returns:
            MemoryItem: Ítem de memoria creado
        """
        return self.add_memory_item(
            user_id=user_id,
            content=fact,
            importance=0.9,
            category="factual",
            tags=["fact", source],
            metadata={"source": source}
        )

    def get_conversation_context(self, user_id: int, limit: int = 10) -> List[MemoryItem]:
        """
        Obtiene el contexto de conversación relevante.

        Args:
            user_id: ID del usuario
            limit: Número máximo de ítems

        Returns:
            List[MemoryItem]: Ítems de contexto relevantes
        """
        return self.query_memory(
            user_id=user_id,
            category="contextual",
            min_importance=0.5,
            limit=limit,
            sort_by="importance"
        )

    def get_user_insights(self, user_id: int) -> Dict[str, Any]:
        """
        Genera insights sobre el usuario basados en su memoria.

        Args:
            user_id: ID del usuario

        Returns:
            Dict[str, Any]: Insights del usuario
        """
        try:
            # Obtener estadísticas
            stats = self.get_memory_stats(user_id)

            # Obtener ítems más importantes
            important_items = self.get_important_memories(user_id, limit=20)

            # Analizar categorías
            category_insights = {}
            for category, count in stats.categories_count.items():
                category_insights[category] = {
                    'count': count,
                    'percentage': (count / stats.total_items * 100) if stats.total_items > 0 else 0
                }

            # Extraer preferencias comunes
            preferences = []
            for item in important_items:
                if "preference" in item.tags or item.category == "personal":
                    preferences.append(item.content[:100] + "..." if len(item.content) > 100 else item.content)

            return {
                'total_memories': stats.total_items,
                'memory_health': self._calculate_memory_health(stats, self._get_user_memory_limit(user_id)),
                'category_distribution': category_insights,
                'top_preferences': preferences[:5],  # Top 5 preferencias
                'average_importance': stats.average_importance,
                'compression_rate': (stats.compressed_items / stats.total_items * 100) if stats.total_items > 0 else 0
            }

        except Exception as e:
            logger.error(f"Error al generar insights para usuario {user_id}: {e}")
            return {
                'error': f"Error al generar insights: {e}",
                'total_memories': 0,
                'memory_health': 'unknown'
            }

    def cleanup_user_memory(self, user_id: int, aggressive: bool = False) -> Dict[str, int]:
        """
        Limpieza inteligente de memoria para un usuario.

        Args:
            user_id: ID del usuario
            aggressive: Si usar limpieza agresiva

        Returns:
            Dict[str, int]: Resultados de la limpieza
        """
        with self._lock:
            try:
                if aggressive:
                    return self.force_memory_cleanup(user_id)
                else:
                    # Limpieza conservadora: comprimir ítems antiguos de baja importancia
                    max_items = self._get_user_memory_limit(user_id)
                    threshold = 0.3  # Umbral conservador

                    compressed = self.repository.compress_old_items(user_id, max_items, threshold)
                    current_count = self.repository.get_memory_count(user_id)

                    # Actualizar estadísticas
                    if self.settings_service:
                        try:
                            self.settings_service.update_category_settings(
                                user_id, 'memory', {'memory_used': current_count}, validate=False
                            )
                        except Exception as e:
                            logger.warning(f"Error al actualizar estadísticas después de limpieza: {e}")

                    return {
                        'compressed': compressed,
                        'deleted': 0,
                        'final_count': current_count
                    }

            except Exception as e:
                logger.error(f"Error en limpieza de memoria para usuario {user_id}: {e}")
                raise MemoryServiceError(f"Error en limpieza de memoria: {e}")

    # ==================== MÉTODOS DE UTILIDAD ====================

    def validate_memory_item(self, item: MemoryItem) -> List[str]:
        """
        Valida un ítem de memoria.

        Args:
            item: Ítem a validar

        Returns:
            List[str]: Lista de errores de validación
        """
        return item.validate()

    def get_memory_health_check(self, user_id: int) -> Dict[str, Any]:
        """
        Realiza una verificación de salud completa del sistema de memoria.

        Args:
            user_id: ID del usuario

        Returns:
            Dict[str, Any]: Resultado de la verificación
        """
        try:
            summary = self.get_memory_usage_summary(user_id)
            stats = self.get_memory_stats(user_id)

            issues = []

            # Verificar límites
            if summary['usage_percentage'] > 95:
                issues.append("Uso de memoria crítico (>95%)")
            elif summary['usage_percentage'] > 80:
                issues.append("Uso de memoria alto (>80%)")

            # Verificar compresión excesiva
            if summary['compression_rate'] > 60:
                issues.append("Tasa de compresión muy alta (>60%)")

            # Verificar ítems sin acceso reciente
            if stats.oldest_item and (datetime.now() - stats.oldest_item).days > 365:
                issues.append("Ítems muy antiguos sin mantenimiento")

            return {
                'healthy': len(issues) == 0,
                'issues': issues,
                'summary': summary,
                'recommendations': self._generate_health_recommendations(issues, summary)
            }

        except Exception as e:
            logger.error(f"Error en verificación de salud para usuario {user_id}: {e}")
            return {
                'healthy': False,
                'issues': [f"Error en verificación: {e}"],
                'summary': {},
                'recommendations': ["Contactar soporte técnico"]
            }

    def _generate_health_recommendations(self, issues: List[str],
                                       summary: Dict[str, Any]) -> List[str]:
        """
        Genera recomendaciones basadas en problemas detectados.

        Args:
            issues: Lista de problemas
            summary: Resumen de uso

        Returns:
            List[str]: Lista de recomendaciones
        """
        recommendations = []

        if "Uso de memoria crítico" in str(issues):
            recommendations.append("Realizar limpieza inmediata de memoria")
            recommendations.append("Revisar importancia de ítems existentes")

        if "Tasa de compresión muy alta" in str(issues):
            recommendations.append("Considerar eliminar ítems poco importantes")
            recommendations.append("Ajustar criterios de compresión")

        if summary.get('usage_percentage', 0) > 50:
            recommendations.append("Monitorear crecimiento de memoria")

        if not recommendations:
            recommendations.append("Sistema de memoria funcionando correctamente")

        return recommendations