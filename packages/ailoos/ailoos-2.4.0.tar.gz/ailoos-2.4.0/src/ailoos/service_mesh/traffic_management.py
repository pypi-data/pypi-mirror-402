import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import random

logger = logging.getLogger(__name__)

class LoadBalancingStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RANDOM = "random"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    IP_HASH = "ip_hash"

class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class ServiceEndpoint:
    host: str
    port: int
    weight: int = 1
    healthy: bool = True
    connections: int = 0
    last_health_check: float = 0
    response_time: float = 0

@dataclass
class TrafficRule:
    service_name: str
    path_pattern: str
    methods: List[str] = field(default_factory=lambda: ["GET", "POST"])
    priority: int = 0
    timeout: int = 30
    retries: int = 3
    circuit_breaker: bool = True
    rate_limit: Optional[Dict[str, Any]] = None

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: int = 60
    success_threshold: int = 3
    monitoring_window: int = 60

@dataclass
class RateLimitConfig:
    requests_per_second: int = 100
    burst_size: int = 20
    window_size: int = 60

class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.success_count = 0
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        async with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                if time.time() - self.last_failure_time > self.config.recovery_timeout:
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise Exception("Circuit breaker is OPEN")

            try:
                result = await func(*args, **kwargs)
                await self._record_success()
                return result
            except Exception as e:
                await self._record_failure()
                raise e

    async def _record_success(self):
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                logger.info("Circuit breaker CLOSED")

    async def _record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning("Circuit breaker OPENED")

class RateLimiter:
    """Rate limiter implementation"""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests = {}
        self._lock = asyncio.Lock()

    async def allow_request(self, client_id: str) -> bool:
        """Check if request is allowed under rate limit"""
        async with self._lock:
            current_time = time.time()
            window_start = current_time - self.config.window_size

            # Clean old requests
            if client_id in self.requests:
                self.requests[client_id] = [t for t in self.requests[client_id] if t > window_start]

            # Check rate limit
            if len(self.requests.get(client_id, [])) < self.config.requests_per_second:
                if client_id not in self.requests:
                    self.requests[client_id] = []
                self.requests[client_id].append(current_time)
                return True
            else:
                return False

class TrafficManagement:
    """Advanced traffic management for service mesh"""

    def __init__(self):
        self.services: Dict[str, List[ServiceEndpoint]] = {}
        self.traffic_rules: Dict[str, TrafficRule] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.load_balancers: Dict[str, LoadBalancingStrategy] = {}
        self.round_robin_index: Dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def register_service(self, service_name: str, endpoints: List[ServiceEndpoint],
                             strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN) -> bool:
        """Register a service with its endpoints"""
        async with self._lock:
            self.services[service_name] = endpoints
            self.load_balancers[service_name] = strategy
            self.round_robin_index[service_name] = 0
            logger.info(f"Registered service {service_name} with {len(endpoints)} endpoints")
            return True

    async def add_traffic_rule(self, rule: TrafficRule) -> bool:
        """Add a traffic routing rule"""
        async with self._lock:
            rule_key = f"{rule.service_name}:{rule.path_pattern}"
            self.traffic_rules[rule_key] = rule

            # Initialize circuit breaker if enabled
            if rule.circuit_breaker:
                cb_config = CircuitBreakerConfig()
                self.circuit_breakers[rule_key] = CircuitBreaker(cb_config)

            # Initialize rate limiter if configured
            if rule.rate_limit:
                rl_config = RateLimitConfig(**rule.rate_limit)
                self.rate_limiters[rule_key] = RateLimiter(rl_config)

            logger.info(f"Added traffic rule for {rule_key}")
            return True

    async def route_request(self, service_name: str, path: str, method: str = "GET",
                          client_id: str = None) -> Optional[ServiceEndpoint]:
        """Route a request to an appropriate endpoint"""
        async with self._lock:
            # Find matching traffic rule
            rule_key = self._find_matching_rule(service_name, path, method)
            rule = self.traffic_rules.get(rule_key) if rule_key else None

            # Check rate limit
            if rule and rule.rate_limit and client_id:
                rate_limiter = self.rate_limiters.get(rule_key)
                if rate_limiter and not await rate_limiter.allow_request(client_id):
                    logger.warning(f"Rate limit exceeded for client {client_id}")
                    return None

            # Get available endpoints
            endpoints = self.services.get(service_name, [])
            healthy_endpoints = [ep for ep in endpoints if ep.healthy]

            if not healthy_endpoints:
                logger.error(f"No healthy endpoints available for service {service_name}")
                return None

            # Select endpoint based on load balancing strategy
            strategy = self.load_balancers.get(service_name, LoadBalancingStrategy.ROUND_ROBIN)
            selected_endpoint = await self._select_endpoint(healthy_endpoints, strategy, service_name)

            if selected_endpoint:
                selected_endpoint.connections += 1

            return selected_endpoint

    async def complete_request(self, service_name: str, endpoint: ServiceEndpoint,
                             response_time: float, success: bool):
        """Mark request completion and update metrics"""
        async with self._lock:
            endpoint.connections = max(0, endpoint.connections - 1)
            endpoint.response_time = response_time
            endpoint.last_health_check = time.time()

            if not success:
                # Could mark as unhealthy based on consecutive failures
                pass

    async def health_check_endpoints(self, service_name: str) -> Dict[str, bool]:
        """Perform health checks on all endpoints of a service"""
        async with self._lock:
            endpoints = self.services.get(service_name, [])
            health_status = {}

            for endpoint in endpoints:
                # Simple health check simulation
                healthy = await self._perform_health_check(endpoint)
                endpoint.healthy = healthy
                health_status[f"{endpoint.host}:{endpoint.port}"] = healthy

            logger.info(f"Health check completed for {service_name}: {health_status}")
            return health_status

    async def get_service_metrics(self, service_name: str) -> Dict[str, Any]:
        """Get traffic metrics for a service"""
        async with self._lock:
            endpoints = self.services.get(service_name, [])
            total_connections = sum(ep.connections for ep in endpoints)
            healthy_count = sum(1 for ep in endpoints if ep.healthy)

            return {
                "service_name": service_name,
                "total_endpoints": len(endpoints),
                "healthy_endpoints": healthy_count,
                "total_connections": total_connections,
                "average_response_time": sum(ep.response_time for ep in endpoints) / len(endpoints) if endpoints else 0
            }

    async def update_endpoint_weight(self, service_name: str, host: str, port: int, weight: int) -> bool:
        """Update weight of a specific endpoint"""
        async with self._lock:
            endpoints = self.services.get(service_name, [])
            for ep in endpoints:
                if ep.host == host and ep.port == port:
                    ep.weight = weight
                    logger.info(f"Updated weight for {host}:{port} to {weight}")
                    return True
            return False

    async def enable_circuit_breaker(self, service_name: str, path_pattern: str,
                                   config: CircuitBreakerConfig) -> bool:
        """Enable circuit breaker for a specific route"""
        async with self._lock:
            rule_key = f"{service_name}:{path_pattern}"
            self.circuit_breakers[rule_key] = CircuitBreaker(config)
            logger.info(f"Enabled circuit breaker for {rule_key}")
            return True

    async def set_rate_limit(self, service_name: str, path_pattern: str,
                           config: RateLimitConfig) -> bool:
        """Set rate limit for a specific route"""
        async with self._lock:
            rule_key = f"{service_name}:{path_pattern}"
            self.rate_limiters[rule_key] = RateLimiter(config)
            logger.info(f"Set rate limit for {rule_key}")
            return True

    def _find_matching_rule(self, service_name: str, path: str, method: str) -> Optional[str]:
        """Find the best matching traffic rule"""
        matching_rules = []
        for rule_key, rule in self.traffic_rules.items():
            if rule.service_name == service_name and method in rule.methods:
                # Simple pattern matching (could be enhanced with regex)
                if rule.path_pattern in path or rule.path_pattern == "*":
                    matching_rules.append((rule_key, rule.priority))

        if matching_rules:
            # Return rule with highest priority
            return max(matching_rules, key=lambda x: x[1])[0]
        return None

    async def _select_endpoint(self, endpoints: List[ServiceEndpoint],
                             strategy: LoadBalancingStrategy, service_name: str) -> Optional[ServiceEndpoint]:
        """Select an endpoint based on load balancing strategy"""
        if not endpoints:
            return None

        if strategy == LoadBalancingStrategy.ROUND_ROBIN:
            index = self.round_robin_index.get(service_name, 0)
            selected = endpoints[index % len(endpoints)]
            self.round_robin_index[service_name] = (index + 1) % len(endpoints)
            return selected

        elif strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return min(endpoints, key=lambda ep: ep.connections)

        elif strategy == LoadBalancingStrategy.RANDOM:
            return random.choice(endpoints)

        elif strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            total_weight = sum(ep.weight for ep in endpoints)
            if total_weight == 0:
                return random.choice(endpoints)

            # Simple weighted selection
            rand_val = random.uniform(0, total_weight)
            current_weight = 0
            for ep in endpoints:
                current_weight += ep.weight
                if rand_val <= current_weight:
                    return ep

        elif strategy == LoadBalancingStrategy.IP_HASH:
            # For demo, use random since we don't have client IP
            return random.choice(endpoints)

        return endpoints[0]  # Default fallback

    async def _perform_health_check(self, endpoint: ServiceEndpoint) -> bool:
        """Perform health check on an endpoint"""
        # Simulate health check
        await asyncio.sleep(0.01)
        # In real implementation, this would make an actual HTTP/TCP health check
        return random.random() > 0.1  # 90% success rate for simulation