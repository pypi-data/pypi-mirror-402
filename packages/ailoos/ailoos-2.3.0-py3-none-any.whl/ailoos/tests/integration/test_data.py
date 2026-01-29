"""
Datos de prueba para pruebas de integración frontend-backend.
Crea datos iniciales necesarios para las pruebas.
"""

from sqlalchemy.orm import Session
from ailoos.coordinator.database.connection import get_db
from ailoos.coordinator.models.base import Node, FederatedSession, User
from ailoos.coordinator.auth.dependencies import create_access_token
import uuid


def create_test_data():
    """Crear datos de prueba para integración."""
    db = next(get_db())

    try:
        # Crear usuario de prueba
        test_user = User(
            id=str(uuid.uuid4()),
            email="test@example.com",
            username="testuser",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPjYfY8mQkqK",  # "password"
            is_active=True,
            role="user"
        )
        db.add(test_user)

        # Crear nodos de prueba
        test_nodes = [
            Node(
                id="test-node-001",
                public_key="test-public-key-001",
                status="active",
                reputation_score=0.9,
                trust_level="verified",
                is_verified=True
            ),
            Node(
                id="test-node-002",
                public_key="test-public-key-002",
                status="active",
                reputation_score=0.8,
                trust_level="verified",
                is_verified=True
            )
        ]
        for node in test_nodes:
            db.add(node)

        # Crear sesión federada de prueba
        test_session = FederatedSession(
            id=str(uuid.uuid4()),
            name="Test Federated Session",
            description="Sesión de prueba para integración",
            model_type="neural_network",
            min_nodes=2,
            max_nodes=5,
            total_rounds=3,
            coordinator_node_id="test-node-001"
        )
        db.add(test_session)

        db.commit()
        print("✅ Datos de prueba creados exitosamente")

        # Generar token de acceso para pruebas
        token = create_access_token(
            data={"sub": test_user.id, "role": test_user.role},
            expires_delta=None
        )

        return {
            "user": test_user,
            "nodes": test_nodes,
            "session": test_session,
            "token": token
        }

    except Exception as e:
        db.rollback()
        print(f"❌ Error creando datos de prueba: {e}")
        raise
    finally:
        db.close()


def cleanup_test_data():
    """Limpiar datos de prueba."""
    db = next(get_db())

    try:
        # Eliminar en orden inverso por dependencias
        db.query(FederatedSession).delete()
        db.query(Node).delete()
        db.query(User).filter(User.email == "test@example.com").delete()
        db.commit()
        print("✅ Datos de prueba limpiados")
    except Exception as e:
        db.rollback()
        print(f"❌ Error limpiando datos de prueba: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_test_data()