import asyncio
import logging
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import socket
import json

logger = logging.getLogger(__name__)

class DiscoveryProtocol(Enum):
    DNS = "dns"
    CONSUL = "consul"
    ETCD = "etcd"
    KUBERNETES = "kubernetes"
    ZOOKEEPER = "zookeeper"

@dataclass
class ServiceInstance:
    id: str
    name: str
    host: str
    port: int
    protocol: str = "http"
    health_check_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    registered_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    healthy: bool = True

@dataclass
class ServiceDefinition:
    name: str
    instances: List[ServiceInstance] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    health_check_interval: int = 30
    deregister_after: int = 90

class ServiceRegistry:
    """In-memory service registry"""

    def __init__(self):
        self.services: Dict[str, ServiceDefinition] = {}
        self.watchers: Dict[str, List[Callable]] = {}
        self._lock = asyncio.Lock()

    async def register_service(self, instance: ServiceInstance) -> bool:
        """Register a service instance"""
        async with self._lock:
            if instance.name not in self.services:
                self.services[instance.name] = ServiceDefinition(
                    name=instance.name,
                    health_check_interval=30,
                    deregister_after=90
                )

            service_def = self.services[instance.name]

            # Check if instance already exists
            existing = next((i for i in service_def.instances if i.id == instance.id), None)
            if existing:
                # Update existing instance
                existing.host = instance.host
                existing.port = instance.port
                existing.metadata.update(instance.metadata)
                existing.last_heartbeat = time.time()
                existing.healthy = True
            else:
                # Add new instance
                service_def.instances.append(instance)

            logger.info(f"Registered service instance: {instance.name}/{instance.id}")
            await self._notify_watchers(instance.name)
            return True

    async def deregister_service(self, service_name: str, instance_id: str) -> bool:
        """Deregister a service instance"""
        async with self._lock:
            if service_name not in self.services:
                return False

            service_def = self.services[service_name]
            original_count = len(service_def.instances)

            service_def.instances = [i for i in service_def.instances if i.id != instance_id]

            if len(service_def.instances) < original_count:
                logger.info(f"Deregistered service instance: {service_name}/{instance_id}")
                await self._notify_watchers(service_name)

                # Remove service if no instances left
                if not service_def.instances:
                    del self.services[service_name]

                return True
            return False

    async def get_service_instances(self, service_name: str, only_healthy: bool = True) -> List[ServiceInstance]:
        """Get all instances of a service"""
        async with self._lock:
            if service_name not in self.services:
                return []

            service_def = self.services[service_name]
            instances = service_def.instances

            if only_healthy:
                instances = [i for i in instances if i.healthy]

            return instances.copy()

    async def get_all_services(self) -> Dict[str, List[ServiceInstance]]:
        """Get all registered services"""
        async with self._lock:
            result = {}
            for name, service_def in self.services.items():
                result[name] = service_def.instances.copy()
            return result

    async def heartbeat(self, service_name: str, instance_id: str) -> bool:
        """Update heartbeat for a service instance"""
        async with self._lock:
            if service_name not in self.services:
                return False

            service_def = self.services[service_name]
            instance = next((i for i in service_def.instances if i.id == instance_id), None)

            if instance:
                instance.last_heartbeat = time.time()
                return True
            return False

    async def perform_health_checks(self):
        """Perform health checks on all service instances"""
        async with self._lock:
            for service_name, service_def in self.services.items():
                for instance in service_def.instances:
                    # Check if instance should be marked unhealthy
                    time_since_heartbeat = time.time() - instance.last_heartbeat
                    if time_since_heartbeat > service_def.deregister_after:
                        if instance.healthy:
                            instance.healthy = False
                            logger.warning(f"Service instance marked unhealthy: {service_name}/{instance.id}")
                            await self._notify_watchers(service_name)
                    elif instance.health_check_url:
                        # Perform actual health check
                        healthy = await self._check_instance_health(instance)
                        if healthy != instance.healthy:
                            instance.healthy = healthy
                            status = "healthy" if healthy else "unhealthy"
                            logger.info(f"Service instance {status}: {service_name}/{instance.id}")
                            await self._notify_watchers(service_name)

    async def add_watcher(self, service_name: str, callback: Callable):
        """Add a watcher for service changes"""
        async with self._lock:
            if service_name not in self.watchers:
                self.watchers[service_name] = []
            self.watchers[service_name].append(callback)

    async def remove_watcher(self, service_name: str, callback: Callable):
        """Remove a watcher for service changes"""
        async with self._lock:
            if service_name in self.watchers:
                self.watchers[service_name] = [w for w in self.watchers[service_name] if w != callback]
                if not self.watchers[service_name]:
                    del self.watchers[service_name]

    async def _notify_watchers(self, service_name: str):
        """Notify watchers of service changes"""
        if service_name in self.watchers:
            instances = await self.get_service_instances(service_name, only_healthy=False)
            for callback in self.watchers[service_name]:
                try:
                    await callback(service_name, instances)
                except Exception as e:
                    logger.error(f"Error in watcher callback: {e}")

    async def _check_instance_health(self, instance: ServiceInstance) -> bool:
        """Perform health check on a service instance"""
        if not instance.health_check_url:
            return True

        try:
            # Simple HTTP health check simulation
            await asyncio.sleep(0.01)  # Simulate network delay
            # In real implementation, make actual HTTP request
            return True  # Assume healthy for demo
        except Exception as e:
            logger.error(f"Health check failed for {instance.id}: {e}")
            return False

class ServiceDiscovery:
    """Automatic service discovery system"""

    def __init__(self, protocol: DiscoveryProtocol = DiscoveryProtocol.DNS):
        self.protocol = protocol
        self.registry = ServiceRegistry()
        self.discovery_clients: Dict[str, Any] = {}
        self._health_check_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Start the service discovery system"""
        if self._running:
            return

        self._running = True
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Service discovery started")

    async def stop(self):
        """Stop the service discovery system"""
        if not self._running:
            return

        self._running = False
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        logger.info("Service discovery stopped")

    async def register_service(self, instance: ServiceInstance) -> bool:
        """Register a service instance"""
        # Register in local registry
        success = await self.registry.register_service(instance)

        # Register with external discovery service if configured
        if self.protocol != DiscoveryProtocol.DNS:
            await self._register_with_external_service(instance)

        return success

    async def deregister_service(self, service_name: str, instance_id: str) -> bool:
        """Deregister a service instance"""
        # Deregister from local registry
        success = await self.registry.deregister_service(service_name, instance_id)

        # Deregister from external discovery service if configured
        if self.protocol != DiscoveryProtocol.DNS:
            await self._deregister_from_external_service(service_name, instance_id)

        return success

    async def discover_service(self, service_name: str, only_healthy: bool = True) -> List[ServiceInstance]:
        """Discover service instances"""
        # Try local registry first
        instances = await self.registry.get_service_instances(service_name, only_healthy)

        # If no instances found locally, try external discovery
        if not instances and self.protocol != DiscoveryProtocol.DNS:
            instances = await self._discover_from_external_service(service_name, only_healthy)

        return instances

    async def watch_service(self, service_name: str, callback: Callable):
        """Watch for changes in a service"""
        await self.registry.add_watcher(service_name, callback)

    async def unwatch_service(self, service_name: str, callback: Callable):
        """Stop watching a service"""
        await self.registry.remove_watcher(service_name, callback)

    async def get_service_stats(self) -> Dict[str, Any]:
        """Get discovery statistics"""
        all_services = await self.registry.get_all_services()
        total_instances = sum(len(instances) for instances in all_services.values())
        healthy_instances = 0

        for instances in all_services.values():
            healthy_instances += sum(1 for i in instances if i.healthy)

        return {
            "total_services": len(all_services),
            "total_instances": total_instances,
            "healthy_instances": healthy_instances,
            "unhealthy_instances": total_instances - healthy_instances,
            "protocol": self.protocol.value
        }

    async def _health_check_loop(self):
        """Continuous health check loop"""
        while self._running:
            try:
                await self.registry.perform_health_checks()
                await asyncio.sleep(30)  # Health check interval
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(5)

    async def _register_with_external_service(self, instance: ServiceInstance):
        """Register with external discovery service"""
        try:
            if self.protocol == DiscoveryProtocol.CONSUL:
                await self._register_consul(instance)
            elif self.protocol == DiscoveryProtocol.ETCD:
                await self._register_etcd(instance)
            elif self.protocol == DiscoveryProtocol.KUBERNETES:
                await self._register_kubernetes(instance)
            elif self.protocol == DiscoveryProtocol.ZOOKEEPER:
                await self._register_zookeeper(instance)
        except Exception as e:
            logger.error(f"Failed to register with external service: {e}")

    async def _deregister_from_external_service(self, service_name: str, instance_id: str):
        """Deregister from external discovery service"""
        try:
            if self.protocol == DiscoveryProtocol.CONSUL:
                await self._deregister_consul(service_name, instance_id)
            elif self.protocol == DiscoveryProtocol.ETCD:
                await self._deregister_etcd(service_name, instance_id)
            elif self.protocol == DiscoveryProtocol.KUBERNETES:
                await self._deregister_kubernetes(service_name, instance_id)
            elif self.protocol == DiscoveryProtocol.ZOOKEEPER:
                await self._deregister_zookeeper(service_name, instance_id)
        except Exception as e:
            logger.error(f"Failed to deregister from external service: {e}")

    async def _discover_from_external_service(self, service_name: str, only_healthy: bool) -> List[ServiceInstance]:
        """Discover from external discovery service"""
        try:
            if self.protocol == DiscoveryProtocol.CONSUL:
                return await self._discover_consul(service_name, only_healthy)
            elif self.protocol == DiscoveryProtocol.ETCD:
                return await self._discover_etcd(service_name, only_healthy)
            elif self.protocol == DiscoveryProtocol.KUBERNETES:
                return await self._discover_kubernetes(service_name, only_healthy)
            elif self.protocol == DiscoveryProtocol.ZOOKEEPER:
                return await self._discover_zookeeper(service_name, only_healthy)
        except Exception as e:
            logger.error(f"Failed to discover from external service: {e}")
        return []

    # Placeholder implementations for external services
    async def _register_consul(self, instance: ServiceInstance):
        # Implement Consul registration
        pass

    async def _register_etcd(self, instance: ServiceInstance):
        # Implement etcd registration
        pass

    async def _register_kubernetes(self, instance: ServiceInstance):
        # Implement Kubernetes service registration
        pass

    async def _register_zookeeper(self, instance: ServiceInstance):
        # Implement ZooKeeper registration
        pass

    async def _deregister_consul(self, service_name: str, instance_id: str):
        # Implement Consul deregistration
        pass

    async def _deregister_etcd(self, service_name: str, instance_id: str):
        # Implement etcd deregistration
        pass

    async def _deregister_kubernetes(self, service_name: str, instance_id: str):
        # Implement Kubernetes deregistration
        pass

    async def _deregister_zookeeper(self, service_name: str, instance_id: str):
        # Implement ZooKeeper deregistration
        pass

    async def _discover_consul(self, service_name: str, only_healthy: bool) -> List[ServiceInstance]:
        # Implement Consul discovery
        return []

    async def _discover_etcd(self, service_name: str, only_healthy: bool) -> List[ServiceInstance]:
        # Implement etcd discovery
        return []

    async def _discover_kubernetes(self, service_name: str, only_healthy: bool) -> List[ServiceInstance]:
        # Implement Kubernetes discovery
        return []

    async def _discover_zookeeper(self, service_name: str, only_healthy: bool) -> List[ServiceInstance]:
        # Implement ZooKeeper discovery
        return []