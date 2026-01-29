"""
Almacenamiento inmutable de logs críticos para AILOOS.
Proporciona almacenamiento persistente e inmutable de logs de auditoría.
"""

import hashlib
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
import threading
import os

from ..core.logging import get_logger

logger = get_logger(__name__)

Base = declarative_base()


class ImmutableLogEntry(Base):
    """Modelo de base de datos para entradas de log inmutables."""
    __tablename__ = "immutable_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(64), unique=True, nullable=False, index=True)
    log_type = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    user_id = Column(String(100), index=True)
    operation_type = Column(String(50), index=True)
    data_hash = Column(String(64), nullable=False)
    data_content = Column(Text, nullable=False)  # JSON serializado
    signature = Column(String(128))  # Firma digital
    blockchain_hash = Column(String(64))  # Hash del bloque blockchain
    compliance_status = Column(String(20), default="pending")
    retention_period_days = Column(Integer, default=2555)  # 7 años por defecto
    created_at = Column(DateTime, default=func.now())
    is_immutable = Column(Boolean, default=True)

    # Índices para optimización
    __table_args__ = (
        Index('idx_log_timestamp_type', 'timestamp', 'log_type'),
        Index('idx_user_operation', 'user_id', 'operation_type'),
        Index('idx_compliance_status', 'compliance_status'),
    )


class LogIntegrityProof(Base):
    """Modelo para pruebas de integridad de logs."""
    __tablename__ = "log_integrity_proofs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(64), nullable=False, index=True)
    proof_type = Column(String(20), nullable=False)  # 'hash_chain', 'merkle', 'blockchain'
    proof_data = Column(Text, nullable=False)  # JSON con datos de prueba
    timestamp = Column(DateTime, default=func.now())
    is_valid = Column(Boolean, default=True)

    __table_args__ = (
        Index('idx_proof_log_timestamp', 'log_id', 'timestamp'),
    )


@dataclass
class LogEntry:
    """Entrada de log para procesamiento."""
    log_id: str
    log_type: str
    timestamp: datetime
    user_id: Optional[str]
    operation_type: str
    data: Dict[str, Any]
    signature: Optional[str] = None
    compliance_status: str = "pending"
    retention_period_days: int = 2555

    def calculate_hash(self) -> str:
        """Calcula hash de integridad del log."""
        content = {
            "log_id": self.log_id,
            "log_type": self.log_type,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "operation_type": self.operation_type,
            "data": self.data,
            "compliance_status": self.compliance_status
        }
        content_str = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return asdict(self)


class ImmutableLogStorage:
    """
    Almacenamiento inmutable de logs críticos.
    Una vez almacenados, los logs no pueden ser modificados o eliminados.
    """

    def __init__(self, database_url: Optional[str] = None):
        if not database_url:
            # Usar SQLite por defecto para desarrollo
            db_path = os.path.join(os.getcwd(), "data", "audit_logs.db")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            database_url = f"sqlite:///{db_path}"

        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Crear tablas
        Base.metadata.create_all(bind=self.engine)

        self.lock = threading.Lock()

        logger.info(f"💾 ImmutableLogStorage initialized with database: {database_url}")

    def store_log(self, log_entry: LogEntry) -> str:
        """
        Almacena un log de forma inmutable.

        Args:
            log_entry: Entrada de log a almacenar

        Returns:
            ID del log almacenado

        Raises:
            ValueError: Si el log ya existe
        """
        with self.lock:
            session = self.SessionLocal()

            try:
                # Verificar si el log ya existe
                existing = session.query(ImmutableLogEntry).filter_by(log_id=log_entry.log_id).first()
                if existing:
                    raise ValueError(f"Log with ID {log_entry.log_id} already exists")

                # Calcular hash de integridad
                data_hash = log_entry.calculate_hash()

                # Crear entrada de base de datos
                db_entry = ImmutableLogEntry(
                    log_id=log_entry.log_id,
                    log_type=log_entry.log_type,
                    timestamp=log_entry.timestamp,
                    user_id=log_entry.user_id,
                    operation_type=log_entry.operation_type,
                    data_hash=data_hash,
                    data_content=json.dumps(log_entry.data),
                    signature=log_entry.signature,
                    compliance_status=log_entry.compliance_status,
                    retention_period_days=log_entry.retention_period_days
                )

                session.add(db_entry)
                session.commit()

                logger.info(f"📝 Stored immutable log: {log_entry.log_id}")

                return log_entry.log_id

            except Exception as e:
                session.rollback()
                logger.error(f"Error storing log {log_entry.log_id}: {e}")
                raise
            finally:
                session.close()

    def get_log(self, log_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un log por ID.

        Args:
            log_id: ID del log

        Returns:
            Datos del log o None si no existe
        """
        session = self.SessionLocal()

        try:
            entry = session.query(ImmutableLogEntry).filter_by(log_id=log_id).first()

            if not entry:
                return None

            # Reconstruir datos
            log_data = {
                "log_id": entry.log_id,
                "log_type": entry.log_type,
                "timestamp": entry.timestamp.isoformat(),
                "user_id": entry.user_id,
                "operation_type": entry.operation_type,
                "data": json.loads(entry.data_content),
                "data_hash": entry.data_hash,
                "signature": entry.signature,
                "blockchain_hash": entry.blockchain_hash,
                "compliance_status": entry.compliance_status,
                "retention_period_days": entry.retention_period_days,
                "created_at": entry.created_at.isoformat(),
                "is_immutable": entry.is_immutable
            }

            return log_data

        except Exception as e:
            logger.error("Error getting log %s: %s", log_id, e)
            return None
        finally:
            session.close()

    def verify_log_integrity(self, log_id: str) -> bool:
        """
        Verifica la integridad de un log.

        Args:
            log_id: ID del log

        Returns:
            True si el log es íntegro
        """
        log_data = self.get_log(log_id)
        if not log_data:
            return False

        # Recrear hash y comparar
        content = {
            "log_id": log_data["log_id"],
            "log_type": log_data["log_type"],
            "timestamp": log_data["timestamp"],
            "user_id": log_data["user_id"],
            "operation_type": log_data["operation_type"],
            "data": log_data["data"],
            "compliance_status": log_data["compliance_status"]
        }

        content_str = json.dumps(content, sort_keys=True, default=str)
        calculated_hash = hashlib.sha256(content_str.encode()).hexdigest()

        return calculated_hash == log_data["data_hash"]

    def search_logs(self, filters: Dict[str, Any], limit: int = 100,
                   offset: int = 0) -> List[Dict[str, Any]]:
        """
        Busca logs por filtros.

        Args:
            filters: Diccionario con filtros
            limit: Número máximo de resultados
            offset: Desplazamiento para paginación

        Returns:
            Lista de logs que coinciden
        """
        session = self.SessionLocal()

        try:
            query = session.query(ImmutableLogEntry)

            # Aplicar filtros
            if "log_type" in filters:
                query = query.filter(ImmutableLogEntry.log_type == filters["log_type"])

            if "user_id" in filters:
                query = query.filter(ImmutableLogEntry.user_id == filters["user_id"])

            if "operation_type" in filters:
                query = query.filter(ImmutableLogEntry.operation_type == filters["operation_type"])

            if "compliance_status" in filters:
                query = query.filter(ImmutableLogEntry.compliance_status == filters["compliance_status"])

            if "date_from" in filters:
                query = query.filter(ImmutableLogEntry.timestamp >= filters["date_from"])

            if "date_to" in filters:
                query = query.filter(ImmutableLogEntry.timestamp <= filters["date_to"])

            # Ordenar por timestamp descendente
            query = query.order_by(ImmutableLogEntry.timestamp.desc())

            # Aplicar paginación
            query = query.limit(limit).offset(offset)

            results = []
            for entry in query.all():
                results.append({
                    "log_id": entry.log_id,
                    "log_type": entry.log_type,
                    "timestamp": entry.timestamp.isoformat(),
                    "user_id": entry.user_id,
                    "operation_type": entry.operation_type,
                    "data_hash": entry.data_hash,
                    "compliance_status": entry.compliance_status,
                    "blockchain_hash": entry.blockchain_hash
                })

            return results

        except Exception as e:
            logger.error("Error searching logs: %s", e)
            return []
        finally:
            session.close()

    def update_compliance_status(self, log_id: str, status: str,
                                blockchain_hash: Optional[str] = None) -> bool:
        """
        Actualiza el estado de compliance de un log.
        Solo puede hacerse una vez (de pending a final).

        Args:
            log_id: ID del log
            status: Nuevo estado
            blockchain_hash: Hash del bloque blockchain

        Returns:
            True si se actualizó correctamente
        """
        with self.lock:
            session = self.SessionLocal()

            try:
                entry = session.query(ImmutableLogEntry).filter_by(log_id=log_id).first()

                if not entry:
                    return False

                # Solo permitir actualización si está en pending
                if entry.compliance_status != "pending":
                    return False

                # Validar estados permitidos
                allowed_statuses = ["compliant", "non_compliant", "requires_review"]
                if status not in allowed_statuses:
                    return False

                entry.compliance_status = status
                if blockchain_hash:
                    entry.blockchain_hash = blockchain_hash

                session.commit()

                logger.info("✅ Updated compliance status for log %s: %s", log_id, status)

                return True

            except Exception as e:
                session.rollback()
                logger.error("Error updating compliance status for %s: %s", log_id, e)
                return False
            finally:
                session.close()

    def get_logs_for_retention_cleanup(self, cutoff_date: datetime) -> List[str]:
        """
        Obtiene IDs de logs que han excedido su período de retención.

        Args:
            cutoff_date: Fecha límite para limpieza

        Returns:
            Lista de IDs de logs a limpiar
        """
        session = self.SessionLocal()

        try:
            # Calcular fecha límite considerando períodos de retención
            # Esta es una simplificación - en producción sería más compleja
            entries = session.query(ImmutableLogEntry).all()

            expired_logs = []
            for entry in entries:
                retention_end = entry.timestamp + timedelta(days=entry.retention_period_days)
                if retention_end < cutoff_date:
                    expired_logs.append(entry.log_id)

            return expired_logs

        except Exception as e:
            logger.error("Error getting logs for retention cleanup: %s", e)
            return []
        finally:
            session.close()

    def create_integrity_proof(self, log_id: str) -> Optional[Dict[str, Any]]:
        """
        Crea una prueba de integridad para un log.

        Args:
            log_id: ID del log

        Returns:
            Prueba de integridad o None
        """
        log_data = self.get_log(log_id)
        if not log_data:
            return None

        # Crear prueba
        proof = {
            "log_id": log_id,
            "timestamp": datetime.now().isoformat(),
            "data_hash": log_data["data_hash"],
            "is_integrity_valid": self.verify_log_integrity(log_id),
            "blockchain_hash": log_data.get("blockchain_hash"),
            "proof_type": "immutable_storage"
        }

        # Almacenar prueba en base de datos
        session = self.SessionLocal()

        try:
            proof_entry = LogIntegrityProof(
                log_id=log_id,
                proof_type="immutable_storage",
                proof_data=json.dumps(proof),
                is_valid=proof["is_integrity_valid"]
            )

            session.add(proof_entry)
            session.commit()

            proof["proof_id"] = proof_entry.id

        except Exception as e:
            session.rollback()
            logger.error("Error storing integrity proof for %s: %s", log_id, e)
        finally:
            session.close()

        return proof

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del almacenamiento.

        Returns:
            Estadísticas del almacenamiento
        """
        session = self.SessionLocal()

        try:
            total_logs = session.query(func.count(ImmutableLogEntry.id)).scalar() or 0

            # Conteo por tipo
            type_counts = {}
            for row in session.query(ImmutableLogEntry.log_type, func.count(ImmutableLogEntry.id)).group_by(ImmutableLogEntry.log_type).all():
                type_counts[row[0]] = row[1]

            # Conteo por estado de compliance
            compliance_counts = {}
            for row in session.query(ImmutableLogEntry.compliance_status, func.count(ImmutableLogEntry.id)).group_by(ImmutableLogEntry.compliance_status).all():
                compliance_counts[row[0]] = row[1]

            # Fecha del log más antiguo y más reciente
            oldest = session.query(func.min(ImmutableLogEntry.timestamp)).scalar()
            newest = session.query(func.max(ImmutableLogEntry.timestamp)).scalar()

            return {
                "total_logs": total_logs,
                "logs_by_type": type_counts,
                "logs_by_compliance_status": compliance_counts,
                "oldest_log": oldest.isoformat() if oldest else None,
                "newest_log": newest.isoformat() if newest else None,
                "database_engine": str(self.engine.url)
            }

        except Exception as e:
            logger.error("Error getting storage stats: %s", e)
            return {}
        finally:
            session.close()

    def verify_all_logs_integrity(self) -> Dict[str, Any]:
        """
        Verifica integridad de todos los logs almacenados.

        Returns:
            Resultado de verificación
        """
        session = self.SessionLocal()

        try:
            entries = session.query(ImmutableLogEntry).all()

            total = len(entries)
            valid = 0
            invalid = []

            for entry in entries:
                if self.verify_log_integrity(entry.log_id):
                    valid += 1
                else:
                    invalid.append(entry.log_id)

            return {
                "total_logs": total,
                "valid_logs": valid,
                "invalid_logs": len(invalid),
                "invalid_log_ids": invalid[:10],  # Limitar para respuesta
                "integrity_percentage": (valid / total * 100) if total > 0 else 100
            }

        except Exception as e:
            logger.error(f"Error verifying all logs integrity: {e}")
            return {"error": str(e)}
        finally:
            session.close()


# Instancia global del almacenamiento inmutable
immutable_log_storage = ImmutableLogStorage()


def get_immutable_log_storage() -> ImmutableLogStorage:
    """Obtiene instancia global del almacenamiento inmutable."""
    return immutable_log_storage