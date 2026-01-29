"""
Script para crear las tablas de configuraciones en PostgreSQL usando SQLAlchemy
================================================================================

Este script crea todas las tablas necesarias para almacenar las configuraciones
del usuario en la base de datos PostgreSQL del coordinador usando SQLAlchemy.
"""

import logging
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from typing import Optional

from .models_sqlalchemy import Base

# Configurar logging
logger = logging.getLogger(__name__)


def create_database_schema(database_url: str, drop_existing: bool = False) -> None:
    """
    Crea la base de datos PostgreSQL con todos los esquemas necesarios usando SQLAlchemy.

    Args:
        database_url: URL de conexión a la base de datos PostgreSQL
        drop_existing: Si se deben eliminar las tablas existentes antes de crearlas

    Raises:
        Exception: Si hay error al crear las tablas
    """
    try:
        # Crear engine
        engine = create_engine(database_url, echo=False)

        # Crear todas las tablas
        if drop_existing:
            logger.info("Eliminando tablas existentes...")
            Base.metadata.drop_all(engine)

        logger.info("Creando tablas de configuraciones...")
        Base.metadata.create_all(engine)

        logger.info("Base de datos creada exitosamente con todos los esquemas de configuraciones.")

        # Verificar que las tablas se crearon correctamente
        with engine.connect() as conn:
            result = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'settings_%' ORDER BY table_name;")
            tables = [row[0] for row in result.fetchall()]

            expected_tables = [
                'settings_users', 'general_settings', 'notification_settings',
                'personalization_settings', 'memory_settings', 'apps_connectors_settings',
                'data_controls_settings', 'security_settings', 'parental_controls_settings',
                'account_settings'
            ]

            logger.info(f"Tablas creadas: {tables}")

            # Verificar que todas las tablas esperadas estén presentes
            missing_tables = [t for t in expected_tables if t not in tables]
            if missing_tables:
                logger.warning(f"Tablas faltantes: {missing_tables}")
            else:
                logger.info("✓ Todas las tablas requeridas están presentes.")

    except Exception as e:
        logger.error(f"Error al crear la base de datos: {e}")
        raise


def verify_database_schema(database_url: str) -> bool:
    """
    Verifica que la base de datos tenga la estructura correcta.

    Args:
        database_url: URL de conexión a la base de datos PostgreSQL

    Returns:
        bool: True si la estructura es correcta, False en caso contrario
    """
    try:
        engine = create_engine(database_url, echo=False)

        with engine.connect() as conn:
            # Obtener lista de tablas
            result = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'settings_%' ORDER BY table_name;")
            tables = [row[0] for row in result.fetchall()]

            expected_tables = [
                'settings_users', 'general_settings', 'notification_settings',
                'personalization_settings', 'memory_settings', 'apps_connectors_settings',
                'data_controls_settings', 'security_settings', 'parental_controls_settings',
                'account_settings'
            ]

            logger.info(f"Tablas encontradas: {tables}")

            # Verificar que todas las tablas esperadas estén presentes
            found_tables = [t for t in expected_tables if t in tables]
            missing_tables = [t for t in expected_tables if t not in tables]

            if missing_tables:
                logger.error(f"Tablas faltantes: {missing_tables}")
                return False
            else:
                logger.info("✓ Todas las tablas requeridas están presentes.")

            # Verificar índices
            for table in expected_tables:
                result = conn.execute(f"SELECT indexname FROM pg_indexes WHERE tablename = '{table}' AND indexname LIKE '%{table}%';")
                indexes = [row[0] for row in result.fetchall()]
                logger.info(f"Índices en {table}: {indexes}")

            return True

    except Exception as e:
        logger.error(f"Error al verificar la base de datos: {e}")
        return False


def create_session_factory(database_url: str):
    """
    Crea una fábrica de sesiones para SQLAlchemy.

    Args:
        database_url: URL de conexión a la base de datos PostgreSQL

    Returns:
        function: Función que crea sesiones de base de datos
    """
    engine = create_engine(database_url, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def get_db_session():
        """Retorna una nueva sesión de base de datos."""
        return SessionLocal()

    return get_db_session


if __name__ == "__main__":
    # Configuración por defecto para desarrollo
    DATABASE_URL = "postgresql://user:password@localhost:5432/ailoos"

    print("Creando esquema de base de datos para configuraciones...")
    create_database_schema(DATABASE_URL, drop_existing=False)

    print("\nVerificando esquema de base de datos...")
    if verify_database_schema(DATABASE_URL):
        print("✓ Verificación exitosa: La base de datos tiene la estructura correcta.")
    else:
        print("✗ Verificación fallida: La base de datos no tiene la estructura correcta.")