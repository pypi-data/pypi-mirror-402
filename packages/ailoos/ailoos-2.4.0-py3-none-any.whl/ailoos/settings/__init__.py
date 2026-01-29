"""
Sistema de Configuraciones de AILOOS
====================================

Módulo central para la gestión de configuraciones del sistema AILOOS.
Proporciona una interfaz unificada para acceder a configuraciones desde
múltiples fuentes: archivos, variables de entorno, base de datos y valores por defecto.
"""

from typing import Dict, Any, Optional, List
import os
from pathlib import Path

# Importar configuraciones existentes
from ..core.config import Config, get_config, reload_config
from ..coordinator.config.settings import settings as coordinator_settings

# Instancia global de configuración
global_config = get_config()

# Importar modelos de datos
from .models import (
    BaseSettings,
    GeneralSettings,
    NotificationSettings,
    PersonalizationSettings,
    MemorySettings,
    AppsConnectorsSettings,
    DataControlsSettings,
    SecuritySettings,
    ParentalControlsSettings,
    AccountSettings,
    SettingsContainer,
    create_default_settings,
    load_settings_from_dict,
    validate_settings,
)

# Re-exportar clases principales
__all__ = [
    # Clases principales
    'Config',
    'SettingsManager',

    # Funciones de utilidad
    'get_config',
    'reload_config',
    'get_settings_manager',

    # Instancias globales
    'global_config',
    'coordinator_settings',

    # Constantes
    'DEFAULT_CONFIG_PATH',
    'CONFIG_CATEGORIES',

    # Modelos de datos
    'BaseSettings',
    'GeneralSettings',
    'NotificationSettings',
    'PersonalizationSettings',
    'MemorySettings',
    'AppsConnectorsSettings',
    'DataControlsSettings',
    'SecuritySettings',
    'ParentalControlsSettings',
    'AccountSettings',
    'SettingsContainer',

    # Funciones de modelos
    'create_default_settings',
    'load_settings_from_dict',
    'validate_settings',
]

# Constantes de configuración
DEFAULT_CONFIG_PATH = os.getenv('AILOOS_CONFIG', './ailoos.yaml')
CONFIG_CATEGORIES = [
    'api',
    'database',
    'federated',
    'marketplace',
    'security',
    'logging',
    'web',
    'models',
    'node',
    'rewards',
    'infrastructure',
    'monitoring',
]


class SettingsManager:
    """
    Gestor unificado de configuraciones para AILOOS.
    Proporciona acceso centralizado a todas las configuraciones del sistema.
    """

    def __init__(self):
        self._config = global_config
        self._coordinator_settings = coordinator_settings
        self._cache = {}

    def get(self, key: str, default: Any = None, source: str = 'auto') -> Any:
        """
        Obtener configuración desde la fuente especificada.

        Args:
            key: Clave de configuración
            default: Valor por defecto si no se encuentra
            source: Fuente de configuración ('auto', 'config', 'coordinator', 'env')

        Returns:
            Valor de configuración
        """
        if source == 'auto':
            # Intentar primero la configuración global
            value = self._config.get(key)
            if value is not None:
                return value

            # Luego intentar configuración del coordinador
            if hasattr(self._coordinator_settings, key):
                return getattr(self._coordinator_settings, key)

            # Finalmente variables de entorno
            env_key = f"AILOOS_{key.upper()}"
            return os.getenv(env_key, default)

        elif source == 'config':
            return self._config.get(key, default)

        elif source == 'coordinator':
            return getattr(self._coordinator_settings, key, default)

        elif source == 'env':
            env_key = f"AILOOS_{key.upper()}"
            return os.getenv(env_key, default)

        return default

    def set(self, key: str, value: Any, persist: bool = True,
            category: str = "general", description: str = ""):
        """
        Establecer configuración.

        Args:
            key: Clave de configuración
            value: Valor a establecer
            persist: Si persistir en base de datos
            category: Categoría de la configuración
            description: Descripción de la configuración
        """
        if persist:
            # Usar configuración asíncrona para persistencia
            import asyncio
            asyncio.run(self._config.set_async(key, value, description, category))
        else:
            self._config.set(key, value)

        # Limpiar cache
        if key in self._cache:
            del self._cache[key]

    def get_category(self, category: str) -> Dict[str, Any]:
        """
        Obtener todas las configuraciones de una categoría.

        Args:
            category: Nombre de la categoría

        Returns:
            Diccionario con configuraciones de la categoría
        """
        cache_key = f"category_{category}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Obtener desde configuración global
        category_config = {}
        all_config = self._config.to_dict()

        for key, value in all_config.items():
            # Inferir categoría desde la clave o usar categoría almacenada
            if key.startswith(f"{category}_") or key.startswith(f"{category}."):
                category_config[key] = value

        # Cachear resultado
        self._cache[cache_key] = category_config
        return category_config

    def validate(self) -> List[str]:
        """
        Validar todas las configuraciones.

        Returns:
            Lista de errores de validación
        """
        return self._config.validate()

    def save_to_file(self, file_path: str = None):
        """
        Guardar configuración actual a archivo.

        Args:
            file_path: Ruta del archivo (opcional)
        """
        self._config.save(file_path)

    def reload(self):
        """Recargar configuración desde fuentes."""
        global global_config
        global_config = reload_config()
        self._config = global_config
        self._cache.clear()

    def get_all_settings(self) -> Dict[str, Any]:
        """
        Obtener todas las configuraciones disponibles.

        Returns:
            Diccionario con todas las configuraciones
        """
        all_settings = self._config.to_dict()

        # Agregar configuraciones del coordinador
        coord_attrs = [attr for attr in dir(self._coordinator_settings)
                      if not attr.startswith('_') and not callable(getattr(self._coordinator_settings, attr))]
        for attr in coord_attrs:
            key = f"coordinator_{attr}"
            if key not in all_settings:
                all_settings[key] = getattr(self._coordinator_settings, attr)

        return all_settings

    def get_environment_info(self) -> Dict[str, Any]:
        """
        Obtener información del entorno de ejecución.

        Returns:
            Diccionario con información del entorno
        """
        return {
            'environment': self.get('environment', 'development'),
            'debug': self.get('debug', False),
            'config_file': self._config.config_file,
            'python_version': os.sys.version,
            'platform': os.sys.platform,
            'working_directory': str(Path.cwd()),
        }


# Instancia global del gestor de configuraciones
settings_manager = SettingsManager()


def get_settings_manager() -> SettingsManager:
    """Obtener instancia global del gestor de configuraciones."""
    return settings_manager