"""
Advanced Audit Logger with multiple output destinations.
Supports file, database, cloud storage, and real-time streaming outputs.
"""

import asyncio
import json
import threading
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime
from enum import Enum
from pathlib import Path
from dataclasses import dataclass
import aiofiles
import structlog

from ..core.config import get_config
from ..core.logging import get_logger
from .audit_event import AuditEvent, AuditEventType, AuditSeverity


class OutputType(Enum):
    """Types of audit log outputs."""
    FILE = "file"
    DATABASE = "database"
    CLOUD_STORAGE = "cloud_storage"
    STREAMING = "streaming"
    SYSLOG = "syslog"
    ELASTICSEARCH = "elasticsearch"


class OutputFormat(Enum):
    """Formats for audit log outputs."""
    JSON = "json"
    CSV = "csv"
    XML = "xml"
    SYSLOG = "syslog"
    STRUCTURED = "structured"


@dataclass
class OutputConfig:
    """Configuration for an audit output."""
    output_type: OutputType
    format: OutputFormat
    destination: str
    batch_size: int = 100
    flush_interval: int = 30  # seconds
    compression: bool = False
    encryption: bool = False
    retention_days: Optional[int] = None
    filters: Optional[Dict[str, Any]] = None


class AuditLogger:
    """
    Advanced audit logger with multiple configurable outputs.
    Handles centralized logging with various output destinations and formats.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_config()
        self.logger = get_logger("audit_logger")

        # Output configurations
        self.outputs: Dict[str, OutputConfig] = {}
        self.output_queues: Dict[str, asyncio.Queue] = {}
        self.output_tasks: Dict[str, asyncio.Task] = {}

        # Buffers for batching
        self.buffers: Dict[str, List[AuditEvent]] = {}
        self.buffer_locks: Dict[str, asyncio.Lock] = {}

        # Performance tracking
        self.stats = {
            'events_logged': 0,
            'outputs_active': 0,
            'buffer_size': 0,
            'flush_operations': 0,
            'errors': 0
        }

        # Initialize outputs from config
        self._load_output_configs()

    def _load_output_configs(self):
        """Load output configurations from config."""
        audit_config = getattr(self.config, 'audit_logger', {})

        # Default file output
        if 'outputs' not in audit_config:
            audit_config['outputs'] = {
                'file_default': {
                    'type': 'file',
                    'format': 'json',
                    'destination': './data/audit.log',
                    'batch_size': 50,
                    'flush_interval': 30
                }
            }

        for output_name, output_cfg in audit_config['outputs'].items():
            config = OutputConfig(
                output_type=OutputType(output_cfg['type']),
                format=OutputFormat(output_cfg['format']),
                destination=output_cfg['destination'],
                batch_size=output_cfg.get('batch_size', 100),
                flush_interval=output_cfg.get('flush_interval', 30),
                compression=output_cfg.get('compression', False),
                encryption=output_cfg.get('encryption', False),
                retention_days=output_cfg.get('retention_days'),
                filters=output_cfg.get('filters')
            )

            self.add_output(output_name, config)

    def add_output(self, name: str, config: OutputConfig):
        """Add a new output destination."""
        self.outputs[name] = config
        self.output_queues[name] = asyncio.Queue()
        self.buffers[name] = []
        self.buffer_locks[name] = asyncio.Lock()

        # Start output task
        self.output_tasks[name] = asyncio.create_task(
            self._output_worker(name, config)
        )

        self.stats['outputs_active'] += 1
        self.logger.info(f"Added audit output: {name} ({config.output_type.value})")

    def remove_output(self, name: str):
        """Remove an output destination."""
        if name in self.output_tasks:
            self.output_tasks[name].cancel()
            del self.output_tasks[name]

        if name in self.outputs:
            del self.outputs[name]
            del self.output_queues[name]
            del self.buffers[name]
            del self.buffer_locks[name]

            self.stats['outputs_active'] -= 1
            self.logger.info(f"Removed audit output: {name}")

    async def log_event(self, event: AuditEvent):
        """Log an audit event to all configured outputs."""
        self.stats['events_logged'] += 1

        # Send to all outputs
        for output_name, config in self.outputs.items():
            # Apply filters if configured
            if config.filters and not self._matches_filters(event, config.filters):
                continue

            # Add to output queue
            await self.output_queues[output_name].put(event)

            # Add to buffer for batching
            async with self.buffer_locks[output_name]:
                self.buffers[output_name].append(event)
                self.stats['buffer_size'] += 1

                # Flush if buffer is full
                if len(self.buffers[output_name]) >= config.batch_size:
                    await self._flush_buffer(output_name, config)

    def _matches_filters(self, event: AuditEvent, filters: Dict[str, Any]) -> bool:
        """Check if event matches the output filters."""
        for key, value in filters.items():
            if key == 'event_type' and event.event_type.value != value:
                return False
            elif key == 'severity' and event.severity.value != value:
                return False
            elif key == 'user_id' and event.user_id != value:
                return False
            elif key == 'resource' and value not in event.resource:
                return False
            elif key == 'tenant_id' and event.tenant_id != value:
                return False
            elif key == 'min_severity':
                severity_levels = {'debug': 1, 'info': 2, 'warning': 3, 'error': 4, 'critical': 5}
                if severity_levels.get(event.severity.value, 0) < severity_levels.get(value, 0):
                    return False
            elif key == 'tags' and not any(tag in event.tags for tag in value):
                return False
            elif key == 'min_risk_score' and (event.risk_score or 0) < value:
                return False

        return True

    async def _output_worker(self, output_name: str, config: OutputConfig):
        """Worker task for processing output queue."""
        while True:
            try:
                # Wait for flush interval or manual trigger
                await asyncio.sleep(config.flush_interval)

                # Flush buffer
                await self._flush_buffer(output_name, config)

            except asyncio.CancelledError:
                # Final flush before shutdown
                await self._flush_buffer(output_name, config)
                break
            except Exception as e:
                self.logger.error(f"Error in output worker {output_name}: {e}")
                self.stats['errors'] += 1

    async def _flush_buffer(self, output_name: str, config: OutputConfig):
        """Flush buffered events to output destination."""
        async with self.buffer_locks[output_name]:
            if not self.buffers[output_name]:
                return

            events = self.buffers[output_name].copy()
            self.buffers[output_name].clear()
            self.stats['buffer_size'] -= len(events)
            self.stats['flush_operations'] += 1

        try:
            if config.output_type == OutputType.FILE:
                await self._write_to_file(config, events)
            elif config.output_type == OutputType.DATABASE:
                await self._write_to_database(config, events)
            elif config.output_type == OutputType.CLOUD_STORAGE:
                await self._write_to_cloud(config, events)
            elif config.output_type == OutputType.STREAMING:
                await self._write_to_stream(config, events)
            elif config.output_type == OutputType.SYSLOG:
                await self._write_to_syslog(config, events)
            elif config.output_type == OutputType.ELASTICSEARCH:
                await self._write_to_elasticsearch(config, events)

        except Exception as e:
            self.logger.error(f"Error flushing to {config.output_type.value}: {e}")
            self.stats['errors'] += 1

            # Re-queue failed events
            for event in events:
                await self.output_queues[output_name].put(event)

    async def _write_to_file(self, config: OutputConfig, events: List[AuditEvent]):
        """Write events to file output."""
        try:
            # Ensure directory exists
            Path(config.destination).parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(config.destination, 'a', encoding='utf-8') as f:
                for event in events:
                    if config.format == OutputFormat.JSON:
                        await f.write(json.dumps(event.to_dict(), ensure_ascii=False) + '\n')
                    elif config.format == OutputFormat.CSV:
                        await f.write(self._format_csv(event) + '\n')
                    elif config.format == OutputFormat.XML:
                        await f.write(self._format_xml(event) + '\n')

        except Exception as e:
            raise Exception(f"File write error: {e}")

    async def _write_to_database(self, config: OutputConfig, events: List[AuditEvent]):
        """Write events to database output."""
        # Placeholder for database integration
        # In production, this would use SQLAlchemy or similar
        self.logger.debug(f"Database output not implemented yet: {config.destination}")

    async def _write_to_cloud(self, config: OutputConfig, events: List[AuditEvent]):
        """Write events to cloud storage output."""
        # Placeholder for cloud storage integration (S3, GCS, etc.)
        self.logger.debug(f"Cloud storage output not implemented yet: {config.destination}")

    async def _write_to_stream(self, config: OutputConfig, events: List[AuditEvent]):
        """Write events to streaming output."""
        # Placeholder for streaming integration (Kafka, Kinesis, etc.)
        self.logger.debug(f"Streaming output not implemented yet: {config.destination}")

    async def _write_to_syslog(self, config: OutputConfig, events: List[AuditEvent]):
        """Write events to syslog output."""
        # Placeholder for syslog integration
        self.logger.debug(f"Syslog output not implemented yet: {config.destination}")

    async def _write_to_elasticsearch(self, config: OutputConfig, events: List[AuditEvent]):
        """Write events to Elasticsearch output."""
        # Placeholder for Elasticsearch integration
        self.logger.debug(f"Elasticsearch output not implemented yet: {config.destination}")

    def _format_csv(self, event: AuditEvent) -> str:
        """Format event as CSV."""
        data = event.to_dict()
        return ','.join(str(data.get(key, '')) for key in [
            'event_id', 'timestamp', 'event_type', 'user_id', 'resource', 'action', 'severity', 'success'
        ])

    def _format_xml(self, event: AuditEvent) -> str:
        """Format event as XML."""
        data = event.to_dict()
        xml_parts = [f'<audit_event>']
        for key, value in data.items():
            xml_parts.append(f'<{key}>{value}</{key}>')
        xml_parts.append('</audit_event>')
        return ''.join(xml_parts)

    async def flush_all(self):
        """Flush all output buffers."""
        tasks = []
        for output_name, config in self.outputs.items():
            tasks.append(self._flush_buffer(output_name, config))

        await asyncio.gather(*tasks, return_exceptions=True)

    async def shutdown(self):
        """Shutdown the audit logger gracefully."""
        # Cancel all output tasks
        for task in self.output_tasks.values():
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.output_tasks.values(), return_exceptions=True)

        # Final flush
        await self.flush_all()

        self.logger.info("Audit logger shutdown complete")

    def get_stats(self) -> Dict[str, Any]:
        """Get logger statistics."""
        return {
            **self.stats,
            'outputs_configured': len(self.outputs),
            'active_tasks': len([t for t in self.output_tasks.values() if not t.done()])
        }


# Global instance
audit_logger = AuditLogger()