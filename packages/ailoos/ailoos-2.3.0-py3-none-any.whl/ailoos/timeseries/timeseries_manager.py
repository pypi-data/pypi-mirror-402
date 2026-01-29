"""
Time Series Manager - Main coordinator for time series database operations
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .influx_integration import InfluxDBIntegration
from .questdb_integration import QuestDBIntegration
from .metrics_collector import MetricsCollector
from .analyzer import TimeSeriesAnalyzer
from .retention_manager import RetentionPolicyManager


class BackendType(Enum):
    INFLUXDB = "influxdb"
    QUESTDB = "questdb"


@dataclass
class TimeSeriesConfig:
    """Configuration for time series database"""
    backends: List[BackendType]
    influx_config: Optional[Dict[str, Any]] = None
    questdb_config: Optional[Dict[str, Any]] = None
    retention_policies: Optional[Dict[str, Any]] = None
    metrics_collection_interval: int = 60  # seconds
    enable_auto_collection: bool = True


class TimeSeriesManager:
    """
    Main manager for time series database operations.
    Coordinates multiple backends and provides unified interface.
    """

    def __init__(self, config: TimeSeriesConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize backends
        self.backends: Dict[BackendType, Any] = {}
        self._initialize_backends()

        # Initialize components
        self.metrics_collector = MetricsCollector(self, config.metrics_collection_interval)
        self.analyzer = TimeSeriesAnalyzer(self)
        self.retention_manager = RetentionPolicyManager(self, config.retention_policies or {})

        # Auto-collection task
        self._collection_task: Optional[asyncio.Task] = None
        if config.enable_auto_collection:
            self._start_auto_collection()

    def _initialize_backends(self):
        """Initialize configured backends"""
        for backend_type in self.config.backends:
            if backend_type == BackendType.INFLUXDB and self.config.influx_config:
                self.backends[backend_type] = InfluxDBIntegration(self.config.influx_config)
            elif backend_type == BackendType.QUESTDB and self.config.questdb_config:
                self.backends[backend_type] = QuestDBIntegration(self.config.questdb_config)
            else:
                self.logger.warning(f"Backend {backend_type.value} not configured properly")

    def _start_auto_collection(self):
        """Start automatic metrics collection"""
        if self._collection_task is None:
            self._collection_task = asyncio.create_task(self._run_auto_collection())

    async def _run_auto_collection(self):
        """Run automatic metrics collection loop"""
        while True:
            try:
                await self.metrics_collector.collect_system_metrics()
                await asyncio.sleep(self.config.metrics_collection_interval)
            except Exception as e:
                self.logger.error(f"Error in auto collection: {e}")
                await asyncio.sleep(self.config.metrics_collection_interval)

    async def write_data(self, measurement: str, tags: Dict[str, str],
                        fields: Dict[str, Union[float, int, str, bool]],
                        timestamp: Optional[datetime] = None,
                        backend: Optional[BackendType] = None) -> bool:
        """
        Write time series data to specified backend or all backends
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        backends_to_use = [self.backends[backend]] if backend else list(self.backends.values())

        success = True
        for backend_instance in backends_to_use:
            try:
                await backend_instance.write_data(measurement, tags, fields, timestamp)
            except Exception as e:
                self.logger.error(f"Failed to write to {backend_instance.__class__.__name__}: {e}")
                success = False

        return success

    async def query_data(self, query: str, backend: BackendType) -> List[Dict[str, Any]]:
        """
        Query data from specific backend
        """
        if backend not in self.backends:
            raise ValueError(f"Backend {backend.value} not available")

        return await self.backends[backend].query_data(query)

    async def get_measurements(self, backend: BackendType) -> List[str]:
        """
        Get list of measurements from backend
        """
        if backend not in self.backends:
            raise ValueError(f"Backend {backend.value} not available")

        return await self.backends[backend].get_measurements()

    async def delete_data(self, measurement: str, start_time: datetime,
                         end_time: Optional[datetime] = None,
                         backend: Optional[BackendType] = None) -> bool:
        """
        Delete data from specified backend or all backends
        """
        if end_time is None:
            end_time = datetime.utcnow()

        backends_to_use = [self.backends[backend]] if backend else list(self.backends.values())

        success = True
        for backend_instance in backends_to_use:
            try:
                await backend_instance.delete_data(measurement, start_time, end_time)
            except Exception as e:
                self.logger.error(f"Failed to delete from {backend_instance.__class__.__name__}: {e}")
                success = False

        return success

    async def analyze_trends(self, measurement: str, field: str,
                           start_time: datetime, end_time: datetime,
                           backend: BackendType) -> Dict[str, Any]:
        """
        Analyze trends and patterns in time series data
        """
        return await self.analyzer.analyze_trends(measurement, field, start_time, end_time, backend)

    async def apply_retention_policy(self, measurement: str, backend: BackendType) -> bool:
        """
        Apply retention policy to measurement
        """
        return await self.retention_manager.apply_policy(measurement, backend)

    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of all backends and components
        """
        status = {
            "backends": {},
            "components": {},
            "overall_health": "healthy"
        }

        # Check backends
        for backend_type, backend in self.backends.items():
            try:
                backend_health = await backend.get_health_status()
                status["backends"][backend_type.value] = backend_health
                if not backend_health.get("healthy", True):
                    status["overall_health"] = "degraded"
            except Exception as e:
                status["backends"][backend_type.value] = {"healthy": False, "error": str(e)}
                status["overall_health"] = "unhealthy"

        # Check components
        status["components"]["metrics_collector"] = {
            "healthy": self.metrics_collector.is_running(),
            "last_collection": self.metrics_collector.last_collection_time
        }

        status["components"]["analyzer"] = {"healthy": True}
        status["components"]["retention_manager"] = {"healthy": True}

        return status

    async def shutdown(self):
        """
        Gracefully shutdown the manager and all components
        """
        self.logger.info("Shutting down TimeSeriesManager...")

        # Stop auto collection
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass

        # Shutdown backends
        for backend in self.backends.values():
            try:
                await backend.close()
            except Exception as e:
                self.logger.error(f"Error closing backend: {e}")

        # Shutdown components
        await self.metrics_collector.stop()

        self.logger.info("TimeSeriesManager shutdown complete")