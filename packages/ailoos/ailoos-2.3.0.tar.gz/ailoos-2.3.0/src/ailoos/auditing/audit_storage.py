"""
Advanced Audit Storage with optimized indexing and partitioning.
Supports multiple storage backends with automatic partitioning and indexing.
"""

import asyncio
import json
import hashlib
import os
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from dataclasses import dataclass
import aiofiles
import sqlite3
import aiosqlite
from concurrent.futures import ThreadPoolExecutor

from ..core.config import get_config
from ..core.logging import get_logger
from .audit_event import AuditEvent, AuditEventType, AuditSeverity


class StorageBackend(Enum):
    """Storage backend types."""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    ELASTICSEARCH = "elasticsearch"
    FILESYSTEM = "filesystem"


class PartitionStrategy(Enum):
    """Partitioning strategies."""
    TIME_BASED = "time_based"  # Partition by time (daily, weekly, monthly)
    SIZE_BASED = "size_based"   # Partition by size
    HASH_BASED = "hash_based"   # Partition by hash of key
    CUSTOM = "custom"          # Custom partitioning logic


@dataclass
class StorageConfig:
    """Configuration for audit storage."""
    backend: StorageBackend
    connection_string: str
    partition_strategy: PartitionStrategy = PartitionStrategy.TIME_BASED
    partition_size: int = 10000  # Events per partition for size-based
    retention_days: int = 365
    compression: bool = True
    encryption: bool = False
    indexes: List[str] = None

    def __post_init__(self):
        if self.indexes is None:
            self.indexes = ['timestamp', 'event_type', 'user_id', 'resource', 'severity']


@dataclass
class PartitionInfo:
    """Information about a storage partition."""
    partition_id: str
    start_date: datetime
    end_date: datetime
    event_count: int
    size_bytes: int
    last_accessed: datetime
    status: str  # 'active', 'archived', 'deleted'


class AuditStorage:
    """
    Advanced audit storage with optimized indexing and partitioning.
    Handles efficient storage, retrieval, and maintenance of audit events.
    """

    def __init__(self, config: Optional[StorageConfig] = None):
        self.config = config or self._default_config()
        self.logger = get_logger("audit_storage")

        # Storage components
        self.backend = self.config.backend
        self.partitions: Dict[str, PartitionInfo] = {}
        self.active_partition: Optional[str] = None
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Indexes
        self.indexes: Dict[str, Dict[Any, Set[str]]] = {}  # field -> value -> set of event_ids
        self.reverse_indexes: Dict[str, Dict[str, Any]] = {}  # event_id -> field -> value

        # Cache
        self.cache: Dict[str, AuditEvent] = {}
        self.cache_size = 1000

        # Statistics
        self.stats = {
            'total_events': 0,
            'total_partitions': 0,
            'index_size': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'storage_operations': 0
        }

        # Initialize storage
        asyncio.create_task(self._initialize_storage())

    def _default_config(self) -> StorageConfig:
        """Get default storage configuration."""
        config = get_config()
        db_path = getattr(config, 'audit_db_path', './data/audit.db')
        return StorageConfig(
            backend=StorageBackend.SQLITE,
            connection_string=db_path
        )

    async def _initialize_storage(self):
        """Initialize storage backend and load existing partitions."""
        try:
            if self.backend == StorageBackend.SQLITE:
                await self._init_sqlite()
            elif self.backend == StorageBackend.FILESYSTEM:
                await self._init_filesystem()
            # Add other backends as needed

            # Load existing partitions
            await self._load_partitions()

            # Create indexes
            await self._build_indexes()

            self.logger.info(f"Audit storage initialized with backend: {self.backend.value}")

        except Exception as e:
            self.logger.error(f"Failed to initialize audit storage: {e}")
            raise

    async def _init_sqlite(self):
        """Initialize SQLite storage."""
        db_path = Path(self.config.connection_string)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(self.config.connection_string) as db:
            # Create main events table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    partition_id TEXT,
                    event_type TEXT,
                    timestamp TEXT,
                    resource TEXT,
                    action TEXT,
                    user_id TEXT,
                    session_id TEXT,
                    tenant_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    severity TEXT,
                    success INTEGER,
                    details TEXT,
                    tags TEXT,
                    processing_time_ms REAL,
                    checksum TEXT,
                    correlation_id TEXT,
                    location TEXT,
                    device_info TEXT,
                    compliance_flags TEXT,
                    risk_score REAL,
                    created_at REAL
                )
            ''')

            # Create partitions table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS partitions (
                    partition_id TEXT PRIMARY KEY,
                    start_date TEXT,
                    end_date TEXT,
                    event_count INTEGER,
                    size_bytes INTEGER,
                    last_accessed TEXT,
                    status TEXT
                )
            ''')

            # Create indexes
            for index_field in self.config.indexes:
                await db.execute(f'''
                    CREATE INDEX IF NOT EXISTS idx_{index_field}
                    ON audit_events({index_field})
                ''')

            await db.commit()

    async def _init_filesystem(self):
        """Initialize filesystem storage."""
        storage_path = Path(self.config.connection_string)
        storage_path.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for partitions
        (storage_path / 'partitions').mkdir(exist_ok=True)
        (storage_path / 'indexes').mkdir(exist_ok=True)
        (storage_path / 'archive').mkdir(exist_ok=True)

    async def store_event(self, event: AuditEvent) -> str:
        """Store an audit event."""
        self.stats['storage_operations'] += 1

        # Determine partition
        partition_id = self._get_partition_id(event)

        # Ensure partition exists
        if partition_id not in self.partitions:
            await self._create_partition(partition_id)

        # Store in backend
        if self.backend == StorageBackend.SQLITE:
            await self._store_sqlite(event, partition_id)
        elif self.backend == StorageBackend.FILESYSTEM:
            await self._store_filesystem(event, partition_id)

        # Update indexes
        await self._update_indexes(event)

        # Update cache
        self._update_cache(event)

        # Update partition stats
        self.partitions[partition_id].event_count += 1
        self.partitions[partition_id].last_accessed = datetime.now()

        self.stats['total_events'] += 1
        return event.event_id

    def _get_partition_id(self, event: AuditEvent) -> str:
        """Determine partition ID for an event."""
        if self.config.partition_strategy == PartitionStrategy.TIME_BASED:
            # Daily partitions
            return event.timestamp.strftime('%Y-%m-%d')
        elif self.config.partition_strategy == PartitionStrategy.SIZE_BASED:
            # Use current active partition or create new one
            if self.active_partition and self.partitions[self.active_partition].event_count < self.config.partition_size:
                return self.active_partition
            else:
                return f"size_{int(event.timestamp.timestamp())}"
        elif self.config.partition_strategy == PartitionStrategy.HASH_BASED:
            # Hash-based partitioning
            hash_value = hashlib.md5(event.event_id.encode()).hexdigest()
            return f"hash_{hash_value[:4]}"
        else:
            return "default"

    async def _create_partition(self, partition_id: str):
        """Create a new partition."""
        now = datetime.now()
        partition = PartitionInfo(
            partition_id=partition_id,
            start_date=now,
            end_date=now,
            event_count=0,
            size_bytes=0,
            last_accessed=now,
            status='active'
        )

        self.partitions[partition_id] = partition
        self.active_partition = partition_id

        # Persist partition info
        if self.backend == StorageBackend.SQLITE:
            async with aiosqlite.connect(self.config.connection_string) as db:
                await db.execute('''
                    INSERT OR REPLACE INTO partitions
                    (partition_id, start_date, end_date, event_count, size_bytes, last_accessed, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    partition.partition_id,
                    partition.start_date.isoformat(),
                    partition.end_date.isoformat(),
                    partition.event_count,
                    partition.size_bytes,
                    partition.last_accessed.isoformat(),
                    partition.status
                ))
                await db.commit()

        self.stats['total_partitions'] += 1
        self.logger.debug(f"Created partition: {partition_id}")

    async def _store_sqlite(self, event: AuditEvent, partition_id: str):
        """Store event in SQLite."""
        async with aiosqlite.connect(self.config.connection_string) as db:
            await db.execute('''
                INSERT OR REPLACE INTO audit_events
                (event_id, partition_id, event_type, timestamp, resource, action,
                 user_id, session_id, tenant_id, ip_address, user_agent, severity,
                 success, details, tags, processing_time_ms, checksum, correlation_id,
                 location, device_info, compliance_flags, risk_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.event_id, partition_id, event.event_type.value,
                event.timestamp.isoformat(), event.resource, event.action,
                event.user_id, event.session_id, event.tenant_id,
                event.ip_address, event.user_agent, event.severity.value,
                1 if event.success else 0, json.dumps(event.details),
                json.dumps(event.tags), event.processing_time_ms,
                event.checksum, event.correlation_id, event.location,
                json.dumps(event.device_info) if event.device_info else None,
                json.dumps(event.compliance_flags), event.risk_score,
                datetime.now().timestamp()
            ))
            await db.commit()

    async def _store_filesystem(self, event: AuditEvent, partition_id: str):
        """Store event in filesystem."""
        partition_dir = Path(self.config.connection_string) / 'partitions' / partition_id
        partition_dir.mkdir(exist_ok=True)

        event_file = partition_dir / f"{event.event_id}.json"

        async with aiofiles.open(event_file, 'w') as f:
            await f.write(json.dumps(event.to_dict(), indent=2))

    async def _update_indexes(self, event: AuditEvent):
        """Update indexes for the event."""
        for field in self.config.indexes:
            if not hasattr(event, field):
                continue

            value = getattr(event, field)
            if value is None:
                continue

            # Handle different field types
            if isinstance(value, datetime):
                index_value = value.isoformat()
            elif isinstance(value, (list, dict)):
                index_value = json.dumps(value, sort_keys=True)
            else:
                index_value = str(value)

            # Update index
            if field not in self.indexes:
                self.indexes[field] = {}
            if index_value not in self.indexes[field]:
                self.indexes[field][index_value] = set()

            self.indexes[field][index_value].add(event.event_id)

            # Update reverse index
            if event.event_id not in self.reverse_indexes:
                self.reverse_indexes[event.event_id] = {}
            self.reverse_indexes[event.event_id][field] = index_value

        self.stats['index_size'] = sum(len(values) for field_index in self.indexes.values()
                                      for values in field_index.values())

    def _update_cache(self, event: AuditEvent):
        """Update cache with the event."""
        if len(self.cache) >= self.cache_size:
            # Remove oldest entry (simple LRU)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        self.cache[event.event_id] = event

    async def get_event(self, event_id: str) -> Optional[AuditEvent]:
        """Retrieve an audit event by ID."""
        # Check cache first
        if event_id in self.cache:
            self.stats['cache_hits'] += 1
            return self.cache[event_id]

        self.stats['cache_misses'] += 1

        # Retrieve from storage
        if self.backend == StorageBackend.SQLITE:
            return await self._get_sqlite(event_id)
        elif self.backend == StorageBackend.FILESYSTEM:
            return await self._get_filesystem(event_id)

        return None

    async def _get_sqlite(self, event_id: str) -> Optional[AuditEvent]:
        """Get event from SQLite."""
        async with aiosqlite.connect(self.config.connection_string) as db:
            async with db.execute('SELECT * FROM audit_events WHERE event_id = ?', (event_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_event(row)
        return None

    async def _get_filesystem(self, event_id: str) -> Optional[AuditEvent]:
        """Get event from filesystem."""
        # Find the event file (this is inefficient, would need better indexing in production)
        storage_path = Path(self.config.connection_string)
        for partition_dir in (storage_path / 'partitions').iterdir():
            if partition_dir.is_dir():
                event_file = partition_dir / f"{event_id}.json"
                if event_file.exists():
                    async with aiofiles.open(event_file, 'r') as f:
                        data = json.loads(await f.read())
                        return AuditEvent.from_dict(data)
        return None

    def _row_to_event(self, row) -> AuditEvent:
        """Convert database row to AuditEvent."""
        return AuditEvent(
            event_type=AuditEventType(row[2]),
            event_id=row[0],
            timestamp=datetime.fromisoformat(row[3]),
            resource=row[4],
            action=row[5],
            user_id=row[6],
            session_id=row[7],
            tenant_id=row[8],
            ip_address=row[9],
            user_agent=row[10],
            severity=AuditSeverity(row[11]),
            success=bool(row[12]),
            details=json.loads(row[13]) if row[13] else {},
            tags=json.loads(row[14]) if row[14] else [],
            processing_time_ms=row[15],
            checksum=row[16],
            correlation_id=row[17],
            location=row[18],
            device_info=json.loads(row[19]) if row[19] else None,
            compliance_flags=json.loads(row[20]) if row[20] else [],
            risk_score=row[21]
        )

    async def query_events(self, filters: Dict[str, Any], limit: int = 100) -> List[AuditEvent]:
        """Query events with filters."""
        # Use indexes for efficient querying
        candidate_ids = None

        for field, value in filters.items():
            if field in self.indexes:
                index_value = str(value)
                if index_value in self.indexes[field]:
                    field_ids = self.indexes[field][index_value]
                    if candidate_ids is None:
                        candidate_ids = field_ids.copy()
                    else:
                        candidate_ids &= field_ids

        if candidate_ids is None:
            candidate_ids = set(self.reverse_indexes.keys())

        # Retrieve events
        events = []
        for event_id in list(candidate_ids)[:limit]:
            event = await self.get_event(event_id)
            if event:
                events.append(event)

        return events

    async def _load_partitions(self):
        """Load existing partitions from storage."""
        if self.backend == StorageBackend.SQLITE:
            async with aiosqlite.connect(self.config.connection_string) as db:
                async with db.execute('SELECT * FROM partitions') as cursor:
                    async for row in cursor:
                        partition = PartitionInfo(
                            partition_id=row[0],
                            start_date=datetime.fromisoformat(row[1]),
                            end_date=datetime.fromisoformat(row[2]),
                            event_count=row[3],
                            size_bytes=row[4],
                            last_accessed=datetime.fromisoformat(row[5]),
                            status=row[6]
                        )
                        self.partitions[partition.partition_id] = partition

    async def _build_indexes(self):
        """Build indexes from existing data."""
        # This would be expensive for large datasets
        # In production, indexes would be maintained incrementally
        pass

    async def cleanup_expired_data(self):
        """Clean up expired partitions based on retention policy."""
        cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
        expired_partitions = []

        for partition_id, partition in self.partitions.items():
            if partition.end_date < cutoff_date and partition.status == 'active':
                expired_partitions.append(partition_id)

        for partition_id in expired_partitions:
            # Archive or delete partition
            self.partitions[partition_id].status = 'archived'
            self.logger.info(f"Archived expired partition: {partition_id}")

    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return {
            **self.stats,
            'active_partitions': len([p for p in self.partitions.values() if p.status == 'active']),
            'archived_partitions': len([p for p in self.partitions.values() if p.status == 'archived']),
            'cache_size': len(self.cache),
            'index_memory_usage': self.stats['index_size'] * 50  # Rough estimate
        }

    async def shutdown(self):
        """Shutdown storage gracefully."""
        self.executor.shutdown(wait=True)
        self.logger.info("Audit storage shutdown complete")