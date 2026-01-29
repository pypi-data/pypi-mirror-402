#!/usr/bin/env python3
"""
Monitoring utilities for Ailoos
"""

import time
import psutil
import logging
from typing import Dict, Any
from datetime import datetime


class NodeMonitor:
    """Monitor for node health and performance"""

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.start_time = time.time()
        self.logger = logging.getLogger(f"monitor.{node_id}")

    def collect_metrics(self) -> Dict[str, Any]:
        """Collect system metrics"""
        return {
            'timestamp': time.time(),
            'uptime_seconds': time.time() - self.start_time,
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_used_gb': psutil.virtual_memory().used / (1024**3),
            'disk_usage_percent': psutil.disk_usage('/').percent,
            'gpu_available': False,  # Simplified for now
            'network_io': self._get_network_io()
        }

    def _get_network_io(self) -> Dict[str, Any]:
        """Get network I/O metrics"""
        net_io = psutil.net_io_counters()
        return {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv
        }

    def log_training_metrics(self, epoch: int, loss: float, accuracy: float):
        """Log training progress"""
        self.logger.info(
            f"Training epoch {epoch}: loss={loss:.4f}, accuracy={accuracy:.2f}%"
        )

    def log_federated_event(self, event_type: str, details: Dict[str, Any]):
        """Log federated learning events"""
        self.logger.info(f"Federated event '{event_type}': {details}")


class SystemMonitor:
    """System-wide monitoring"""

    def __init__(self):
        self.start_time = time.time()
        self.logger = logging.getLogger("system.monitor")

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        return {
            'status': 'healthy',
            'uptime': time.time() - self.start_time,
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'timestamp': datetime.now().isoformat()
        }