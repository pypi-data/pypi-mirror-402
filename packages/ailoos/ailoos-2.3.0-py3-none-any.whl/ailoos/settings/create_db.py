"""
Script para crear la base de datos settings.db con esquemas completos
======================================================================

Este script crea una base de datos SQLite con todas las tablas necesarias
para almacenar las configuraciones de usuario de AILOOS.
"""

import sqlite3
import os
from datetime import datetime
from typing import List


def create_database_schema(db_path: str = "settings.db") -> None:
    """
    Crea la base de datos SQLite con todos los esquemas necesarios.

    Args:
        db_path: Ruta donde crear la base de datos
    """
    # Eliminar base de datos existente si existe
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Habilitar restricciones de clave foránea
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Habilitar integridad referencial estricta
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Crear tabla de usuarios
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Crear tabla de configuraciones generales
        cursor.execute("""
            CREATE TABLE general_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                appearance VARCHAR(10) NOT NULL CHECK (appearance IN ('system', 'light', 'dark')),
                accent_color VARCHAR(10) NOT NULL CHECK (accent_color IN ('blue', 'green', 'purple', 'red')),
                font_size VARCHAR(10) NOT NULL CHECK (font_size IN ('small', 'medium', 'large')),
                send_with_enter BOOLEAN NOT NULL DEFAULT 1,
                ui_language VARCHAR(2) NOT NULL CHECK (ui_language IN ('es', 'en', 'fr', 'de')),
                spoken_language VARCHAR(2) NOT NULL CHECK (spoken_language IN ('es', 'en', 'fr', 'de')),
                voice VARCHAR(10) NOT NULL CHECK (voice IN ('ember', 'alloy', 'echo')),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                version VARCHAR(10) DEFAULT '1.0.0',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Crear tabla de configuraciones de notificaciones
        cursor.execute("""
            CREATE TABLE notification_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                mute_all BOOLEAN NOT NULL DEFAULT 0,
                responses_app BOOLEAN NOT NULL DEFAULT 1,
                responses_email BOOLEAN NOT NULL DEFAULT 1,
                tasks_app BOOLEAN NOT NULL DEFAULT 1,
                tasks_email BOOLEAN NOT NULL DEFAULT 0,
                projects_app BOOLEAN NOT NULL DEFAULT 1,
                projects_email BOOLEAN NOT NULL DEFAULT 1,
                recommendations_app BOOLEAN NOT NULL DEFAULT 0,
                recommendations_email BOOLEAN NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                version VARCHAR(10) DEFAULT '1.0.0',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Crear tabla de configuraciones de personalización
        cursor.execute("""
            CREATE TABLE personalization_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                enable_personalization BOOLEAN NOT NULL DEFAULT 1,
                custom_instructions BOOLEAN NOT NULL DEFAULT 0,
                base_style_tone VARCHAR(15) NOT NULL CHECK (base_style_tone IN ('talkative', 'witty', 'professional', 'casual')),
                nickname VARCHAR(50) DEFAULT '',
                occupation VARCHAR(100) DEFAULT '',
                more_about_you TEXT DEFAULT '',
                reference_chat_history BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                version VARCHAR(10) DEFAULT '1.0.0',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Crear tabla de configuraciones de memoria
        cursor.execute("""
            CREATE TABLE memory_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                memory_used INTEGER NOT NULL DEFAULT 0 CHECK (memory_used >= 0),
                max_memory_items INTEGER NOT NULL DEFAULT 256 CHECK (max_memory_items > 0),
                reference_memories BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                version VARCHAR(10) DEFAULT '1.0.0',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                CHECK (memory_used <= max_memory_items)
            );
        """)

        # Crear tabla de configuraciones de aplicaciones y conectores
        cursor.execute("""
            CREATE TABLE apps_connectors_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                google_drive BOOLEAN NOT NULL DEFAULT 0,
                dropbox BOOLEAN NOT NULL DEFAULT 0,
                slack BOOLEAN NOT NULL DEFAULT 0,
                discord BOOLEAN NOT NULL DEFAULT 0,
                webhook_url VARCHAR(500) DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                version VARCHAR(10) DEFAULT '1.0.0',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Crear tabla de configuraciones de controles de datos
        cursor.execute("""
            CREATE TABLE data_controls_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                data_collection BOOLEAN NOT NULL DEFAULT 1,
                analytics BOOLEAN NOT NULL DEFAULT 1,
                data_retention VARCHAR(15) NOT NULL CHECK (data_retention IN ('3months', '6months', '1year', '2years', 'indefinite')),
                export_data BOOLEAN NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                version VARCHAR(10) DEFAULT '1.0.0',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Crear tabla de configuraciones de seguridad
        cursor.execute("""
            CREATE TABLE security_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                two_factor BOOLEAN NOT NULL DEFAULT 0,
                two_factor_secret VARCHAR(32),
                two_factor_enabled BOOLEAN NOT NULL DEFAULT 0,
                two_factor_algorithm VARCHAR(10) NOT NULL DEFAULT 'SHA256' CHECK (two_factor_algorithm IN ('SHA1', 'SHA256', 'SHA512')),
                two_factor_digits INTEGER NOT NULL DEFAULT 6 CHECK (two_factor_digits IN (6, 8)),
                two_factor_interval INTEGER NOT NULL DEFAULT 30 CHECK (two_factor_interval BETWEEN 15 AND 60),
                session_timeout VARCHAR(10) NOT NULL CHECK (session_timeout IN ('15min', '30min', '1hour', '4hours', 'never')),
                login_alerts BOOLEAN NOT NULL DEFAULT 1,
                password_change_pending BOOLEAN NOT NULL DEFAULT 0,
                password_last_changed DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                version VARCHAR(10) DEFAULT '1.0.0',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Crear tabla de configuraciones de controles parentales
        cursor.execute("""
            CREATE TABLE parental_controls_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                parental_control BOOLEAN NOT NULL DEFAULT 0,
                content_filter VARCHAR(10) NOT NULL CHECK (content_filter IN ('strict', 'moderate', 'lenient')),
                time_limits BOOLEAN NOT NULL DEFAULT 0,
                max_time_per_day VARCHAR(10) NOT NULL CHECK (max_time_per_day IN ('1hour', '2hours', '4hours', '8hours')),
                parental_pin_hash VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                version VARCHAR(10) DEFAULT '1.0.0',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Crear tabla de configuraciones de cuenta
        cursor.execute("""
            CREATE TABLE account_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name VARCHAR(100) DEFAULT '',
                email VARCHAR(255) DEFAULT '',
                phone VARCHAR(20) DEFAULT '',
                bio TEXT DEFAULT '',
                sessions_completed INTEGER NOT NULL DEFAULT 0 CHECK (sessions_completed >= 0),
                tokens_used INTEGER NOT NULL DEFAULT 0 CHECK (tokens_used >= 0),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                version VARCHAR(10) DEFAULT '1.0.0',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Crear tabla de suscripciones push
        cursor.execute("""
            CREATE TABLE push_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                endpoint VARCHAR(500) NOT NULL UNIQUE,
                p256dh_key VARCHAR(100) NOT NULL,
                auth_key VARCHAR(50) NOT NULL,
                user_agent VARCHAR(500),
                browser_info VARCHAR(200),
                ip_address VARCHAR(45),
                is_active BOOLEAN NOT NULL DEFAULT 1,
                last_used_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # Crear índices para mejorar rendimiento
        cursor.execute("CREATE INDEX idx_general_settings_user_id ON general_settings(user_id);")
        cursor.execute("CREATE INDEX idx_notification_settings_user_id ON notification_settings(user_id);")
        cursor.execute("CREATE INDEX idx_personalization_settings_user_id ON personalization_settings(user_id);")
        cursor.execute("CREATE INDEX idx_memory_settings_user_id ON memory_settings(user_id);")
        cursor.execute("CREATE INDEX idx_apps_connectors_settings_user_id ON apps_connectors_settings(user_id);")
        cursor.execute("CREATE INDEX idx_data_controls_settings_user_id ON data_controls_settings(user_id);")
        cursor.execute("CREATE INDEX idx_security_settings_user_id ON security_settings(user_id);")
        cursor.execute("CREATE INDEX idx_parental_controls_settings_user_id ON parental_controls_settings(user_id);")
        cursor.execute("CREATE INDEX idx_account_settings_user_id ON account_settings(user_id);")
        cursor.execute("CREATE INDEX idx_push_subscriptions_user_id ON push_subscriptions(user_id);")
        cursor.execute("CREATE INDEX idx_push_subscriptions_endpoint ON push_subscriptions(endpoint);")
        cursor.execute("CREATE INDEX idx_push_subscriptions_active ON push_subscriptions(is_active);")
        cursor.execute("CREATE INDEX idx_push_subscriptions_created_at ON push_subscriptions(created_at);")

        # Índices adicionales para búsquedas comunes
        cursor.execute("CREATE INDEX idx_users_email ON users(email);")
        cursor.execute("CREATE INDEX idx_users_username ON users(username);")

        # Insertar datos de ejemplo (usuario por defecto)
        cursor.execute("""
            INSERT INTO users (username, email) VALUES ('default_user', 'user@example.com');
        """)

        # Insertar configuraciones por defecto para el usuario
        user_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO general_settings (user_id, appearance, accent_color, font_size, send_with_enter, ui_language, spoken_language, voice)
            VALUES (?, 'system', 'blue', 'medium', 1, 'es', 'es', 'ember');
        """, (user_id,))

        cursor.execute("""
            INSERT INTO notification_settings (user_id, mute_all, responses_app, responses_email, tasks_app, tasks_email, projects_app, projects_email, recommendations_app, recommendations_email)
            VALUES (?, 0, 1, 1, 1, 0, 1, 1, 0, 0);
        """, (user_id,))

        cursor.execute("""
            INSERT INTO personalization_settings (user_id, enable_personalization, custom_instructions, base_style_tone, nickname, occupation, more_about_you, reference_chat_history)
            VALUES (?, 1, 0, 'witty', '', '', '', 1);
        """, (user_id,))

        cursor.execute("""
            INSERT INTO memory_settings (user_id, memory_used, max_memory_items, reference_memories)
            VALUES (?, 0, 256, 1);
        """, (user_id,))

        cursor.execute("""
            INSERT INTO apps_connectors_settings (user_id, google_drive, dropbox, slack, discord, webhook_url)
            VALUES (?, 0, 0, 0, 0, '');
        """, (user_id,))

        cursor.execute("""
            INSERT INTO data_controls_settings (user_id, data_collection, analytics, data_retention, export_data)
            VALUES (?, 1, 1, '1year', 0);
        """, (user_id,))

        cursor.execute("""
            INSERT INTO security_settings (user_id, two_factor, two_factor_secret, two_factor_enabled, two_factor_algorithm, two_factor_digits, two_factor_interval, session_timeout, login_alerts, password_change_pending, password_last_changed)
            VALUES (?, 0, NULL, 0, 'SHA256', 6, 30, '30min', 1, 0, NULL);
        """, (user_id,))

        cursor.execute("""
            INSERT INTO parental_controls_settings (user_id, parental_control, content_filter, time_limits, max_time_per_day, parental_pin_hash)
            VALUES (?, 0, 'moderate', 0, '2hours', NULL);
        """, (user_id,))

        cursor.execute("""
            INSERT INTO account_settings (user_id, name, email, phone, bio, sessions_completed, tokens_used)
            VALUES (?, '', '', '', '', 0, 0);
        """, (user_id,))

        # Confirmar cambios
        conn.commit()

        print(f"Base de datos '{db_path}' creada exitosamente con todos los esquemas.")
        print(f"Se creó un usuario por defecto con ID: {user_id}")

    except sqlite3.Error as e:
        print(f"Error al crear la base de datos: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def verify_database_schema(db_path: str = "settings.db") -> None:
    """
    Verifica que la base de datos tenga la estructura correcta.

    Args:
        db_path: Ruta de la base de datos a verificar
    """
    if not os.path.exists(db_path):
        print(f"Error: La base de datos '{db_path}' no existe.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Obtener lista de tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        expected_tables = [
            'users', 'general_settings', 'notification_settings',
            'personalization_settings', 'memory_settings', 'apps_connectors_settings',
            'data_controls_settings', 'security_settings', 'parental_controls_settings',
            'account_settings', 'push_subscriptions'
        ]

        print(f"Tablas encontradas en '{db_path}':")
        for table in tables:
            table_name = table[0]
            if table_name in expected_tables:
                print(f"  ✓ {table_name}")
            else:
                print(f"  ? {table_name} (inesperada)")

        # Verificar que todas las tablas esperadas estén presentes
        found_tables = [table[0] for table in tables]
        missing_tables = [t for t in expected_tables if t not in found_tables]

        if missing_tables:
            print(f"\nTablas faltantes: {missing_tables}")
        else:
            print("\n✓ Todas las tablas requeridas están presentes.")

        # Verificar restricciones de clave foránea
        cursor.execute("PRAGMA foreign_keys;")
        fk_enabled = cursor.fetchone()[0]
        print(f"\nClaves foráneas: {'Habilitadas' if fk_enabled else 'Deshabilitadas'}")

        # Contar registros en cada tabla
        print("\nConteo de registros:")
        for table in expected_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} registros")

    except sqlite3.Error as e:
        print(f"Error al verificar la base de datos: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    # Crear la base de datos
    create_database_schema()

    # Verificar la estructura
    verify_database_schema()