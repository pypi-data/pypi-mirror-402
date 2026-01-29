"""
Metrics Collector for automatic system metrics collection
"""

import asyncio
import logging
import psutil
import platform
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class MetricType(Enum):
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    SYSTEM = "system"
    CUSTOM = "custom"


@dataclass
class MetricDefinition:
    """Definition of a metric to collect"""
    name: str
    type: MetricType
    measurement: str
    tags: Dict[str, str]
    collection_function: Callable[[], Dict[str, Any]]
    interval: int = 60  # seconds


class MetricsCollector:
    """
    Automatic metrics collector for system and application metrics
    """

    def __init__(self, manager, collection_interval: int = 60):
        """
        Initialize metrics collector

        Args:
            manager: TimeSeriesManager instance
            collection_interval: Default collection interval in seconds
        """
        self.manager = manager
        self.collection_interval = collection_interval
        self.logger = logging.getLogger(__name__)

        self.metrics: Dict[str, MetricDefinition] = {}
        self.running = False
        self.last_collection_time: Optional[datetime] = None
        self.collection_task: Optional[asyncio.Task] = None

        # Register default system metrics
        self._register_default_metrics()

    def _register_default_metrics(self):
        """Register default system metrics"""
        hostname = platform.node()

        # CPU metrics
        self.register_metric(MetricDefinition(
            name="cpu_percent",
            type=MetricType.CPU,
            measurement="system_cpu",
            tags={"host": hostname},
            collection_function=self._collect_cpu_metrics,
            interval=self.collection_interval
        ))

        # Memory metrics
        self.register_metric(MetricDefinition(
            name="memory_usage",
            type=MetricType.MEMORY,
            measurement="system_memory",
            tags={"host": hostname},
            collection_function=self._collect_memory_metrics,
            interval=self.collection_interval
        ))

        # Disk metrics
        self.register_metric(MetricDefinition(
            name="disk_usage",
            type=MetricType.DISK,
            measurement="system_disk",
            tags={"host": hostname},
            collection_function=self._collect_disk_metrics,
            interval=self.collection_interval
        ))

        # Network metrics
        self.register_metric(MetricDefinition(
            name="network_io",
            type=MetricType.NETWORK,
            measurement="system_network",
            tags={"host": hostname},
            collection_function=self._collect_network_metrics,
            interval=self.collection_interval
        ))

        # System info
        self.register_metric(MetricDefinition(
            name="system_info",
            type=MetricType.SYSTEM,
            measurement="system_info",
            tags={"host": hostname},
            collection_function=self._collect_system_info,
            interval=3600  # Collect system info hourly
        ))

    def register_metric(self, metric_def: MetricDefinition):
        """
        Register a custom metric for collection

        Args:
            metric_def: Metric definition
        """
        self.metrics[metric_def.name] = metric_def
        self.logger.info(f"Registered metric: {metric_def.name}")

    def unregister_metric(self, metric_name: str):
        """
        Unregister a metric

        Args:
            metric_name: Name of the metric to remove
        """
        if metric_name in self.metrics:
            del self.metrics[metric_name]
            self.logger.info(f"Unregistered metric: {metric_name}")

    async def start(self):
        """
        Start automatic metrics collection
        """
        if self.running:
            self.logger.warning("Metrics collector is already running")
            return

        self.running = True
        self.collection_task = asyncio.create_task(self._collection_loop())
        self.logger.info("Metrics collector started")

    async def stop(self):
        """
        Stop automatic metrics collection
        """
        if not self.running:
            return

        self.running = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Metrics collector stopped")

    async def _collection_loop(self):
        """Main collection loop"""
        while self.running:
            try:
                await self.collect_system_metrics()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                self.logger.error(f"Error in collection loop: {e}")
                await asyncio.sleep(self.collection_interval)

    async def collect_system_metrics(self):
        """
        Collect all registered metrics and send to time series database
        """
        timestamp = datetime.utcnow()

        for metric_name, metric_def in self.metrics.items():
            try:
                # Check if it's time to collect this metric
                if not self._should_collect_metric(metric_def, timestamp):
                    continue

                # Collect metric data
                fields = metric_def.collection_function()

                if fields:
                    # Write to all configured backends
                    success = await self.manager.write_data(
                        measurement=metric_def.measurement,
                        tags=metric_def.tags,
                        fields=fields,
                        timestamp=timestamp
                    )

                    if success:
                        self.logger.debug(f"Collected metric: {metric_name}")
                    else:
                        self.logger.warning(f"Failed to write metric: {metric_name}")

            except Exception as e:
                self.logger.error(f"Error collecting metric {metric_name}: {e}")

        self.last_collection_time = timestamp

    def _should_collect_metric(self, metric_def: MetricDefinition, current_time: datetime) -> bool:
        """
        Determine if a metric should be collected based on its interval

        Args:
            metric_def: Metric definition
            current_time: Current timestamp

        Returns:
            True if metric should be collected
        """
        if self.last_collection_time is None:
            return True

        time_diff = (current_time - self.last_collection_time).total_seconds()
        return time_diff >= metric_def.interval

    def _collect_cpu_metrics(self) -> Dict[str, Any]:
        """Collect CPU usage metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_times = psutil.cpu_times()

            return {
                "usage_percent": cpu_percent,
                "user_time": cpu_times.user,
                "system_time": cpu_times.system,
                "idle_time": cpu_times.idle,
                "cpu_count": psutil.cpu_count(),
                "cpu_count_logical": psutil.cpu_count(logical=True)
            }
        except Exception as e:
            self.logger.error(f"Error collecting CPU metrics: {e}")
            return {}

    def _collect_memory_metrics(self) -> Dict[str, Any]:
        """Collect memory usage metrics"""
        try:
            memory = psutil.virtual_memory()

            return {
                "total_bytes": memory.total,
                "available_bytes": memory.available,
                "used_bytes": memory.used,
                "used_percent": memory.percent,
                "free_bytes": memory.free
            }
        except Exception as e:
            self.logger.error(f"Error collecting memory metrics: {e}")
            return {}

    def _collect_disk_metrics(self) -> Dict[str, Any]:
        """Collect disk usage metrics"""
        try:
            disk_usage = psutil.disk_usage('/')

            # Disk I/O counters
            disk_io = psutil.disk_io_counters()
            io_read_bytes = disk_io.read_bytes if disk_io else 0
            io_write_bytes = disk_io.write_bytes if disk_io else 0

            return {
                "total_bytes": disk_usage.total,
                "used_bytes": disk_usage.used,
                "free_bytes": disk_usage.free,
                "used_percent": disk_usage.percent,
                "io_read_bytes": io_read_bytes,
                "io_write_bytes": io_write_bytes
            }
        except Exception as e:
            self.logger.error(f"Error collecting disk metrics: {e}")
            return {}

    def _collect_network_metrics(self) -> Dict[str, Any]:
        """Collect network I/O metrics"""
        try:
            network_io = psutil.net_io_counters()

            return {
                "bytes_sent": network_io.bytes_sent,
                "bytes_recv": network_io.bytes_recv,
                "packets_sent": network_io.packets_sent,
                "packets_recv": network_io.packets_recv,
                "errin": network_io.errin,
                "errout": network_io.errout,
                "dropin": network_io.dropin,
                "dropout": network_io.dropout
            }
        except Exception as e:
            self.logger.error(f"Error collecting network metrics: {e}")
            return {}

    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect system information"""
        try:
            return {
                "platform": platform.platform(),
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "boot_time": psutil.boot_time()
            }
        except Exception as e:
            self.logger.error(f"Error collecting system info: {e}")
            return {}

    def register_custom_metric(self, name: str, measurement: str,
                             tags: Dict[str, str], collection_function: Callable[[], Dict[str, Any]],
                             interval: int = 60):
        """
        Register a custom metric

        Args:
            name: Metric name
            measurement: Measurement name
            tags: Tags dictionary
            collection_function: Function that returns metric fields
            interval: Collection interval in seconds
        """
        metric_def = MetricDefinition(
            name=name,
            type=MetricType.CUSTOM,
            measurement=measurement,
            tags=tags,
            collection_function=collection_function,
            interval=interval
        )

        self.register_metric(metric_def)

    async def collect_metric_now(self, metric_name: str) -> bool:
        """
        Collect a specific metric immediately

        Args:
            metric_name: Name of the metric to collect

        Returns:
            True if successful, False otherwise
        """
        if metric_name not in self.metrics:
            self.logger.error(f"Metric {metric_name} not found")
            return False

        metric_def = self.metrics[metric_name]
        timestamp = datetime.utcnow()

        try:
            fields = metric_def.collection_function()

            if fields:
                success = await self.manager.write_data(
                    measurement=metric_def.measurement,
                    tags=metric_def.tags,
                    fields=fields,
                    timestamp=timestamp
                )

                if success:
                    self.logger.info(f"Manually collected metric: {metric_name}")
                    return True
                else:
                    self.logger.error(f"Failed to write metric: {metric_name}")
                    return False
            else:
                self.logger.warning(f"No data collected for metric: {metric_name}")
                return False

        except Exception as e:
            self.logger.error(f"Error collecting metric {metric_name}: {e}")
            return False

    def get_registered_metrics(self) -> List[Dict[str, Any]]:
        """
        Get list of all registered metrics

        Returns:
            List of metric information dictionaries
        """
        return [
            {
                "name": metric.name,
                "type": metric.type.value,
                "measurement": metric.measurement,
                "tags": metric.tags,
                "interval": metric.interval
            }
            for metric in self.metrics.values()
        ]

    def is_running(self) -> bool:
        """
        Check if the collector is running

        Returns:
            True if running, False otherwise
        """
        return self.running and (self.collection_task is not None and not self.collection_task.done())