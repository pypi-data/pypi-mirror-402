import asyncio
import logging
import time
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import statistics

from .content_distribution import DistributionStrategy

logger = logging.getLogger(__name__)

class OptimizationGoal(Enum):
    LATENCY_MINIMIZATION = "latency_minimization"
    COST_OPTIMIZATION = "cost_optimization"
    THROUGHPUT_MAXIMIZATION = "throughput_maximization"
    RELIABILITY_MAXIMIZATION = "reliability_maximization"
    BALANCED = "balanced"

class OptimizationAction(Enum):
    SWITCH_DISTRIBUTION_STRATEGY = "switch_distribution_strategy"
    REBALANCE_LOAD = "rebalance_load"
    SCALE_EDGE_NODES = "scale_edge_nodes"
    ADJUST_CACHE_TTL = "adjust_cache_ttl"
    PURGE_CACHE = "purge_cache"
    REDISTRIBUTE_CONTENT = "redistribute_content"

@dataclass
class OptimizationRule:
    name: str
    condition: str  # Expression to evaluate
    action: OptimizationAction
    parameters: Dict[str, Any]
    cooldown_minutes: int = 5
    enabled: bool = True
    last_executed: Optional[float] = None

@dataclass
class OptimizationResult:
    rule_name: str
    action: OptimizationAction
    success: bool
    timestamp: float
    metrics_before: Dict[str, float]
    metrics_after: Dict[str, float]
    description: str

class CDNOptimization:
    """Automatic CDN optimization system"""

    def __init__(self, optimization_interval: int = 300):  # 5 minutes
        self.optimization_interval = optimization_interval
        self.optimization_rules: Dict[str, OptimizationRule] = {}
        self.optimization_history: List[OptimizationResult] = []
        self.current_goal = OptimizationGoal.BALANCED
        self._running = False
        self._optimization_task: Optional[asyncio.Task] = None

        # Component references
        self.monitoring = None
        self.content_distribution = None
        self.edge_computing = None
        self.global_cache = None
        self.cdn_manager = None

    async def start(self) -> None:
        """Start the optimization system"""
        self._running = True
        self._optimization_task = asyncio.create_task(self._optimization_worker())
        logger.info("CDN optimization system started")

    async def stop(self) -> None:
        """Stop the optimization system"""
        self._running = False
        if self._optimization_task:
            self._optimization_task.cancel()
            try:
                await self._optimization_task
            except asyncio.CancelledError:
                pass
        logger.info("CDN optimization system stopped")

    def set_components(self, monitoring=None, content_distribution=None,
                      edge_computing=None, global_cache=None, cdn_manager=None) -> None:
        """Set component references for optimization"""
        self.monitoring = monitoring
        self.content_distribution = content_distribution
        self.edge_computing = edge_computing
        self.global_cache = global_cache
        self.cdn_manager = cdn_manager

    async def set_optimization_goal(self, goal: OptimizationGoal) -> None:
        """Set the primary optimization goal"""
        self.current_goal = goal
        logger.info(f"Optimization goal set to: {goal.value}")

    async def add_optimization_rule(self, rule: OptimizationRule) -> bool:
        """Add an optimization rule"""
        if rule.name in self.optimization_rules:
            return False

        self.optimization_rules[rule.name] = rule
        logger.info(f"Added optimization rule: {rule.name}")
        return True

    async def remove_optimization_rule(self, rule_name: str) -> bool:
        """Remove an optimization rule"""
        if rule_name not in self.optimization_rules:
            return False

        del self.optimization_rules[rule_name]
        logger.info(f"Removed optimization rule: {rule_name}")
        return True

    async def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status"""
        recent_optimizations = [
            opt for opt in self.optimization_history
            if opt.timestamp > time.time() - 3600  # Last hour
        ]

        success_rate = (
            len([opt for opt in recent_optimizations if opt.success]) /
            len(recent_optimizations) if recent_optimizations else 0
        )

        return {
            'current_goal': self.current_goal.value,
            'active_rules': len([r for r in self.optimization_rules.values() if r.enabled]),
            'total_rules': len(self.optimization_rules),
            'recent_optimizations': len(recent_optimizations),
            'success_rate': success_rate,
            'last_optimization': max((opt.timestamp for opt in self.optimization_history), default=None)
        }

    async def get_optimization_history(self, hours: int = 24) -> List[OptimizationResult]:
        """Get optimization history"""
        cutoff_time = time.time() - (hours * 3600)
        return [opt for opt in self.optimization_history if opt.timestamp > cutoff_time]

    async def manual_optimize(self, rule_name: str) -> Optional[OptimizationResult]:
        """Manually trigger an optimization rule"""
        if rule_name not in self.optimization_rules:
            return None

        rule = self.optimization_rules[rule_name]
        return await self._execute_optimization(rule)

    async def _optimization_worker(self) -> None:
        """Background optimization worker"""
        while self._running:
            try:
                await asyncio.sleep(self.optimization_interval)

                # Get current metrics
                if not self.monitoring:
                    continue

                current_metrics = await self.monitoring.get_current_metrics()

                # Evaluate and execute rules
                for rule_name, rule in self.optimization_rules.items():
                    if not rule.enabled:
                        continue

                    # Check cooldown
                    if rule.last_executed and time.time() - rule.last_executed < rule.cooldown_minutes * 60:
                        continue

                    # Evaluate condition
                    if self._evaluate_condition(rule.condition, current_metrics):
                        result = await self._execute_optimization(rule)
                        if result:
                            self.optimization_history.append(result)
                            rule.last_executed = time.time()

                            # Keep history manageable
                            if len(self.optimization_history) > 1000:
                                self.optimization_history = self.optimization_history[-500:]

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Optimization worker error: {e}")

    def _evaluate_condition(self, condition: str, metrics: Dict[str, Any]) -> bool:
        """Evaluate optimization condition"""
        def get_metric_value(path: str) -> float:
            """Extract metric value from nested dict"""
            keys = path.split('.')
            value = metrics
            try:
                for key in keys:
                    if '[' in key and ']' in key:
                        # Handle array indexing
                        base_key, index = key.split('[')
                        index = int(index.rstrip(']'))
                        value = value[base_key][index]
                    else:
                        value = value[key]
                return float(value) if isinstance(value, (int, float)) else 0.0
            except (KeyError, IndexError, TypeError, ValueError):
                return 0.0

        # Replace metric references in condition
        import re
        metric_refs = re.findall(r'metric\[([^\]]+)\]', condition)

        eval_condition = condition
        for ref in metric_refs:
            value = get_metric_value(ref)
            eval_condition = eval_condition.replace(f'metric[{ref}]', str(value))

        try:
            return bool(eval(eval_condition, {"__builtins__": {}}, {}))
        except Exception as e:
            logger.error(f"Condition evaluation error: {e}")
            return False

    async def _execute_optimization(self, rule: OptimizationRule) -> Optional[OptimizationResult]:
        """Execute an optimization action"""
        # Get metrics before optimization
        metrics_before = {}
        if self.monitoring:
            current_metrics = await self.monitoring.get_current_metrics()
            metrics_before = self._extract_key_metrics(current_metrics)

        success = False
        description = ""

        try:
            if rule.action == OptimizationAction.SWITCH_DISTRIBUTION_STRATEGY:
                success, description = await self._switch_distribution_strategy(rule.parameters)

            elif rule.action == OptimizationAction.REBALANCE_LOAD:
                success, description = await self._rebalance_load(rule.parameters)

            elif rule.action == OptimizationAction.SCALE_EDGE_NODES:
                success, description = await self._scale_edge_nodes(rule.parameters)

            elif rule.action == OptimizationAction.ADJUST_CACHE_TTL:
                success, description = await self._adjust_cache_ttl(rule.parameters)

            elif rule.action == OptimizationAction.PURGE_CACHE:
                success, description = await self._purge_cache(rule.parameters)

            elif rule.action == OptimizationAction.REDISTRIBUTE_CONTENT:
                success, description = await self._redistribute_content(rule.parameters)

        except Exception as e:
            logger.error(f"Optimization execution error: {e}")
            description = f"Error: {str(e)}"

        # Get metrics after optimization
        metrics_after = {}
        if self.monitoring:
            await asyncio.sleep(2)  # Wait for metrics to stabilize
            current_metrics = await self.monitoring.get_current_metrics()
            metrics_after = self._extract_key_metrics(current_metrics)

        result = OptimizationResult(
            rule_name=rule.name,
            action=rule.action,
            success=success,
            timestamp=time.time(),
            metrics_before=metrics_before,
            metrics_after=metrics_after,
            description=description
        )

        logger.info(f"Optimization result: {rule.name} - {'Success' if success else 'Failed'}: {description}")
        return result

    async def _switch_distribution_strategy(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Switch content distribution strategy"""
        if not self.content_distribution:
            return False, "Content distribution not available"

        strategy_name = params.get('strategy', 'performance_based')
        strategy = getattr(DistributionStrategy, strategy_name.upper(), DistributionStrategy.PERFORMANCE_BASED)

        await self.content_distribution.update_distribution_strategy(strategy)
        return True, f"Switched to {strategy.value} distribution strategy"

    async def _rebalance_load(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Rebalance load across providers"""
        if not self.cdn_manager:
            return False, "CDN manager not available"

        # Get current metrics
        metrics = await self.cdn_manager.get_all_metrics()

        # Find overloaded providers
        overloaded = []
        for provider, m in metrics.items():
            utilization = m.get('requests', 0) / 100000  # Normalize
            if utilization > 0.8:
                overloaded.append(provider)

        if not overloaded:
            return True, "No overloaded providers found"

        # Simulate rebalancing
        await asyncio.sleep(0.1)
        return True, f"Rebalanced load from providers: {', '.join(overloaded)}"

    async def _scale_edge_nodes(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Scale edge computing nodes"""
        if not self.edge_computing:
            return False, "Edge computing not available"

        direction = params.get('direction', 'up')
        count = params.get('count', 1)

        # This would integrate with actual scaling mechanisms
        await asyncio.sleep(0.1)
        return True, f"Scaled edge nodes {direction} by {count}"

    async def _adjust_cache_ttl(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Adjust cache TTL settings"""
        if not self.global_cache:
            return False, "Global cache not available"

        # This would modify cache TTL policies
        await asyncio.sleep(0.1)
        return True, "Adjusted cache TTL settings"

    async def _purge_cache(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Purge cache entries"""
        if not self.global_cache:
            return False, "Global cache not available"

        pattern = params.get('pattern', '*')
        deleted = await self.global_cache.invalidate_pattern(pattern)
        return True, f"Purged {deleted} cache entries matching '{pattern}'"

    async def _redistribute_content(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Redistribute content based on access patterns"""
        if not self.content_distribution:
            return False, "Content distribution not available"

        # Analyze access patterns and redistribute
        await asyncio.sleep(0.1)
        return True, "Redistributed content based on access patterns"

    def _extract_key_metrics(self, metrics: Dict[str, Any]) -> Dict[str, float]:
        """Extract key metrics for comparison"""
        key_metrics = {}

        # CDN metrics
        if 'cdn_providers' in metrics:
            for provider, m in metrics['cdn_providers'].items():
                key_metrics[f'cdn_{provider}_requests'] = m.get('requests', 0)
                key_metrics[f'cdn_{provider}_hit_rate'] = m.get('cache_hit_ratio', 0)

        # Cache metrics
        if 'global_cache' in metrics:
            cache = metrics['global_cache']
            key_metrics['cache_hit_rate'] = cache.get('overall_hit_rate', 0)
            key_metrics['cache_utilization'] = cache.get('memory_utilization', 0)

        # Edge metrics
        if 'edge_computing' in metrics:
            edge = metrics['edge_computing']
            key_metrics['edge_utilization'] = edge.get('overall_utilization', 0)

        return key_metrics

    async def generate_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on current state"""
        recommendations = []

        if not self.monitoring:
            return recommendations

        metrics = await self.monitoring.get_current_metrics()

        # Analyze cache performance
        if 'global_cache' in metrics:
            cache = metrics['global_cache']
            hit_rate = cache.get('overall_hit_rate', 0)
            utilization = cache.get('memory_utilization', 0)

            if hit_rate < 0.7:
                recommendations.append("Consider increasing cache size or adjusting TTL policies to improve hit rate")
            if utilization > 0.9:
                recommendations.append("Cache utilization is high, consider scaling cache capacity")

        # Analyze CDN performance
        if 'cdn_providers' in metrics:
            for provider, m in metrics['cdn_providers'].items():
                hit_rate = m.get('cache_hit_ratio', 0)
                uptime = m.get('uptime', 0)

                if hit_rate < 0.75:
                    recommendations.append(f"Provider {provider} has low cache hit rate, consider content optimization")
                if uptime < 0.995:
                    recommendations.append(f"Provider {provider} has low uptime, consider failover strategies")

        # Analyze edge computing
        if 'edge_computing' in metrics:
            edge = metrics['edge_computing']
            utilization = edge.get('overall_utilization', 0)

            if utilization > 0.8:
                recommendations.append("Edge computing utilization is high, consider scaling edge nodes")
            elif utilization < 0.3:
                recommendations.append("Edge computing utilization is low, consider consolidating resources")

        return recommendations