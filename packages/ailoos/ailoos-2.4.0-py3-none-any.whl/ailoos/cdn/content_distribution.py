import asyncio
import logging
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import random
import time

from .cdn_manager import CDNManager, CDNProviderType

logger = logging.getLogger(__name__)

class ContentType(Enum):
    STATIC = "static"
    DYNAMIC = "dynamic"
    STREAMING = "streaming"
    API = "api"

@dataclass
class ContentMetadata:
    content_type: ContentType
    size_bytes: int
    ttl_seconds: Optional[int] = None
    priority: int = 1  # 1-10, higher is more important
    regions: List[str] = None  # Target regions
    tags: List[str] = None

@dataclass
class UserLocation:
    country: str
    region: str
    city: str
    latitude: float
    longitude: float

class DistributionStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    GEOGRAPHIC = "geographic"
    LOAD_BALANCED = "load_balanced"
    PERFORMANCE_BASED = "performance_based"

class ContentDistribution:
    """Intelligent content distribution system"""

    def __init__(self, cdn_manager: CDNManager):
        self.cdn_manager = cdn_manager
        self.distribution_strategy = DistributionStrategy.PERFORMANCE_BASED
        self.provider_performance: Dict[str, Dict[str, float]] = {}
        self.content_registry: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def distribute_content(self, content_id: str, content: bytes,
                               metadata: ContentMetadata,
                               user_location: Optional[UserLocation] = None) -> Optional[str]:
        """Distribute content using intelligent routing"""
        async with self._lock:
            # Select optimal provider
            provider_name = await self._select_provider(content_id, metadata, user_location)

            if not provider_name:
                logger.error(f"No suitable provider found for content {content_id}")
                return None

            # Upload content
            url = await self.cdn_manager.upload_content(
                content_id, content,
                self._metadata_to_dict(metadata)
            )

            if url:
                # Register content distribution
                self.content_registry[content_id] = {
                    'provider': provider_name,
                    'url': url,
                    'metadata': metadata,
                    'distributed_at': time.time(),
                    'access_count': 0
                }
                logger.info(f"Distributed content {content_id} via {provider_name}")
            else:
                logger.error(f"Failed to distribute content {content_id}")

            return url

    async def get_content_url(self, content_id: str, user_location: Optional[UserLocation] = None) -> Optional[str]:
        """Get optimal content URL for user location"""
        if content_id not in self.content_registry:
            return None

        registry_entry = self.content_registry[content_id]
        provider_name = registry_entry['provider']

        # Check if we need to redistribute based on location
        optimal_provider = await self._select_provider(content_id, registry_entry['metadata'], user_location)

        if optimal_provider != provider_name:
            # Trigger redistribution in background
            asyncio.create_task(self._redistribute_content(content_id, optimal_provider))
            # For now, return current URL
            return registry_entry['url']

        # Update access count
        registry_entry['access_count'] += 1

        return registry_entry['url']

    async def purge_content(self, content_id: str) -> bool:
        """Purge content from all providers"""
        if content_id not in self.content_registry:
            return False

        provider_name = self.content_registry[content_id]['provider']
        success = await self.cdn_manager.purge_content(content_id, provider_name)

        if success:
            del self.content_registry[content_id]
            logger.info(f"Purged content {content_id}")

        return success

    async def update_distribution_strategy(self, strategy: DistributionStrategy) -> None:
        """Update the distribution strategy"""
        async with self._lock:
            self.distribution_strategy = strategy
            logger.info(f"Updated distribution strategy to {strategy.value}")

    async def get_distribution_metrics(self) -> Dict[str, Any]:
        """Get distribution metrics"""
        total_content = len(self.content_registry)
        total_access = sum(entry['access_count'] for entry in self.content_registry.values())

        provider_usage = {}
        for entry in self.content_registry.values():
            provider = entry['provider']
            provider_usage[provider] = provider_usage.get(provider, 0) + 1

        return {
            'total_distributed_content': total_content,
            'total_access_count': total_access,
            'provider_usage': provider_usage,
            'strategy': self.distribution_strategy.value
        }

    async def _select_provider(self, content_id: str, metadata: ContentMetadata,
                             user_location: Optional[UserLocation] = None) -> Optional[str]:
        """Select optimal provider based on strategy"""
        available_providers = self.cdn_manager.list_providers()

        if not available_providers:
            return None

        if len(available_providers) == 1:
            return available_providers[0]

        if self.distribution_strategy == DistributionStrategy.ROUND_ROBIN:
            return self._round_robin_select(available_providers, content_id)

        elif self.distribution_strategy == DistributionStrategy.GEOGRAPHIC:
            return self._geographic_select(available_providers, user_location)

        elif self.distribution_strategy == DistributionStrategy.LOAD_BALANCED:
            return self._load_balanced_select(available_providers)

        elif self.distribution_strategy == DistributionStrategy.PERFORMANCE_BASED:
            return await self._performance_based_select(available_providers, metadata)

        return available_providers[0]  # Default fallback

    def _round_robin_select(self, providers: List[str], content_id: str) -> str:
        """Round-robin provider selection"""
        hash_value = int(hashlib.md5(content_id.encode()).hexdigest(), 16)
        index = hash_value % len(providers)
        return providers[index]

    def _geographic_select(self, providers: List[str], user_location: Optional[UserLocation]) -> str:
        """Geographic-based provider selection"""
        if not user_location:
            return providers[0]

        # Simple geographic routing (can be enhanced with actual geo-data)
        region_map = {
            'cloudflare': ['US', 'EU', 'ASIA'],
            'akamai': ['US', 'EU', 'ASIA'],
            # Add more mappings
        }

        for provider in providers:
            if provider in region_map and user_location.country in region_map[provider]:
                return provider

        return providers[0]

    def _load_balanced_select(self, providers: List[str]) -> str:
        """Load-balanced provider selection"""
        # Simple random selection for load balancing
        return random.choice(providers)

    async def _performance_based_select(self, providers: List[str], metadata: ContentMetadata) -> str:
        """Performance-based provider selection"""
        # Get metrics from all providers
        metrics = await self.cdn_manager.get_all_metrics()

        # Score providers based on performance metrics
        scores = {}
        for provider in providers:
            if provider in metrics:
                m = metrics[provider]
                # Calculate score based on cache hit ratio, uptime, etc.
                score = (
                    m.get('cache_hit_ratio', 0.5) * 0.4 +
                    m.get('uptime', 0.99) * 0.4 +
                    (1.0 / (m.get('requests', 1) + 1)) * 0.2  # Lower load is better
                )
                scores[provider] = score
            else:
                scores[provider] = 0.5  # Default score

        # Return provider with highest score
        return max(scores, key=scores.get)

    async def _redistribute_content(self, content_id: str, new_provider: str) -> None:
        """Redistribute content to a different provider"""
        if content_id not in self.content_registry:
            return

        entry = self.content_registry[content_id]
        metadata = entry['metadata']

        # This would need the original content, which we don't have
        # In a real system, content would be stored or re-fetched
        logger.info(f"Would redistribute {content_id} to {new_provider}")
        # For now, just update the registry
        entry['provider'] = new_provider

    def _metadata_to_dict(self, metadata: ContentMetadata) -> Dict[str, Any]:
        """Convert ContentMetadata to dictionary"""
        return {
            'content_type': metadata.content_type.value,
            'size_bytes': metadata.size_bytes,
            'ttl_seconds': metadata.ttl_seconds,
            'priority': metadata.priority,
            'regions': metadata.regions or [],
            'tags': metadata.tags or []
        }