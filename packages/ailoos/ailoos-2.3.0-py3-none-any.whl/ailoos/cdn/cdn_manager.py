import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class CDNProviderType(Enum):
    CLOUDFLARE = "cloudflare"
    AKAMAI = "akamai"
    FASTLY = "fastly"
    AWS_CLOUDFRONT = "aws_cloudfront"

@dataclass
class CDNConfig:
    provider_type: CDNProviderType
    api_key: str
    zone_id: Optional[str] = None
    region: Optional[str] = None
    custom_config: Dict[str, Any] = None

class CDNProvider(ABC):
    """Abstract base class for CDN providers"""

    def __init__(self, config: CDNConfig):
        self.config = config
        self._is_connected = False

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to CDN provider"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from CDN provider"""
        pass

    @abstractmethod
    async def upload_content(self, content_id: str, content: bytes, metadata: Dict[str, Any]) -> str:
        """Upload content to CDN"""
        pass

    @abstractmethod
    async def get_content_url(self, content_id: str) -> str:
        """Get CDN URL for content"""
        pass

    @abstractmethod
    async def purge_content(self, content_id: str) -> bool:
        """Purge content from CDN cache"""
        pass

    @abstractmethod
    async def get_metrics(self) -> Dict[str, Any]:
        """Get provider-specific metrics"""
        pass

    @property
    def is_connected(self) -> bool:
        return self._is_connected

class CloudflareProvider(CDNProvider):
    """Cloudflare CDN provider implementation"""

    async def connect(self) -> bool:
        try:
            # Simulate connection
            await asyncio.sleep(0.1)
            self._is_connected = True
            logger.info(f"Connected to Cloudflare CDN (zone: {self.config.zone_id})")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Cloudflare: {e}")
            return False

    async def disconnect(self) -> None:
        self._is_connected = False
        logger.info("Disconnected from Cloudflare CDN")

    async def upload_content(self, content_id: str, content: bytes, metadata: Dict[str, Any]) -> str:
        if not self.is_connected:
            raise ConnectionError("Not connected to Cloudflare")
        # Simulate upload
        await asyncio.sleep(0.05)
        url = f"https://{self.config.zone_id}.cdn.cloudflare.net/{content_id}"
        logger.info(f"Uploaded content {content_id} to Cloudflare")
        return url

    async def get_content_url(self, content_id: str) -> str:
        return f"https://{self.config.zone_id}.cdn.cloudflare.net/{content_id}"

    async def purge_content(self, content_id: str) -> bool:
        if not self.is_connected:
            return False
        # Simulate purge
        await asyncio.sleep(0.02)
        logger.info(f"Purged content {content_id} from Cloudflare")
        return True

    async def get_metrics(self) -> Dict[str, Any]:
        return {
            "requests": 150000,
            "bandwidth_gb": 250.5,
            "cache_hit_ratio": 0.85,
            "uptime": 0.999
        }

class AkamaiProvider(CDNProvider):
    """Akamai CDN provider implementation"""

    async def connect(self) -> bool:
        try:
            await asyncio.sleep(0.1)
            self._is_connected = True
            logger.info("Connected to Akamai CDN")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Akamai: {e}")
            return False

    async def disconnect(self) -> None:
        self._is_connected = False
        logger.info("Disconnected from Akamai CDN")

    async def upload_content(self, content_id: str, content: bytes, metadata: Dict[str, Any]) -> str:
        if not self.is_connected:
            raise ConnectionError("Not connected to Akamai")
        await asyncio.sleep(0.05)
        url = f"https://akamai-cdn.com/{content_id}"
        logger.info(f"Uploaded content {content_id} to Akamai")
        return url

    async def get_content_url(self, content_id: str) -> str:
        return f"https://akamai-cdn.com/{content_id}"

    async def purge_content(self, content_id: str) -> bool:
        if not self.is_connected:
            return False
        await asyncio.sleep(0.02)
        logger.info(f"Purged content {content_id} from Akamai")
        return True

    async def get_metrics(self) -> Dict[str, Any]:
        return {
            "requests": 200000,
            "bandwidth_gb": 350.0,
            "cache_hit_ratio": 0.90,
            "uptime": 0.998
        }

class CDNManager:
    """Main CDN manager with support for multiple providers"""

    def __init__(self):
        self.providers: Dict[str, CDNProvider] = {}
        self._active_provider: Optional[str] = None
        self._lock = asyncio.Lock()

    async def add_provider(self, name: str, config: CDNConfig) -> bool:
        """Add a CDN provider"""
        async with self._lock:
            if name in self.providers:
                logger.warning(f"Provider {name} already exists")
                return False

            provider_class = self._get_provider_class(config.provider_type)
            provider = provider_class(config)

            if await provider.connect():
                self.providers[name] = provider
                if self._active_provider is None:
                    self._active_provider = name
                logger.info(f"Added CDN provider: {name}")
                return True
            else:
                logger.error(f"Failed to add provider {name}")
                return False

    async def remove_provider(self, name: str) -> bool:
        """Remove a CDN provider"""
        async with self._lock:
            if name not in self.providers:
                return False

            provider = self.providers[name]
            await provider.disconnect()
            del self.providers[name]

            if self._active_provider == name:
                self._active_provider = next(iter(self.providers.keys()), None)

            logger.info(f"Removed CDN provider: {name}")
            return True

    async def set_active_provider(self, name: str) -> bool:
        """Set the active CDN provider"""
        async with self._lock:
            if name not in self.providers:
                return False
            self._active_provider = name
            logger.info(f"Set active provider to: {name}")
            return True

    async def upload_content(self, content_id: str, content: bytes, metadata: Dict[str, Any] = None,
                           provider_name: Optional[str] = None) -> Optional[str]:
        """Upload content using specified or active provider"""
        provider_name = provider_name or self._active_provider
        if not provider_name or provider_name not in self.providers:
            logger.error("No active provider available")
            return None

        provider = self.providers[provider_name]
        try:
            return await provider.upload_content(content_id, content, metadata or {})
        except Exception as e:
            logger.error(f"Failed to upload content: {e}")
            return None

    async def get_content_url(self, content_id: str, provider_name: Optional[str] = None) -> Optional[str]:
        """Get content URL from specified or active provider"""
        provider_name = provider_name or self._active_provider
        if not provider_name or provider_name not in self.providers:
            return None

        provider = self.providers[provider_name]
        return provider.get_content_url(content_id)

    async def purge_content(self, content_id: str, provider_name: Optional[str] = None) -> bool:
        """Purge content from specified or active provider"""
        provider_name = provider_name or self._active_provider
        if not provider_name or provider_name not in self.providers:
            return False

        provider = self.providers[provider_name]
        return await provider.purge_content(content_id)

    async def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics from all providers"""
        metrics = {}
        for name, provider in self.providers.items():
            try:
                metrics[name] = await provider.get_metrics()
            except Exception as e:
                logger.error(f"Failed to get metrics for {name}: {e}")
                metrics[name] = {}
        return metrics

    def list_providers(self) -> List[str]:
        """List all configured providers"""
        return list(self.providers.keys())

    def get_active_provider(self) -> Optional[str]:
        """Get the name of the active provider"""
        return self._active_provider

    def _get_provider_class(self, provider_type: CDNProviderType):
        """Get provider class based on type"""
        provider_classes = {
            CDNProviderType.CLOUDFLARE: CloudflareProvider,
            CDNProviderType.AKAMAI: AkamaiProvider,
            # Add more providers as needed
        }
        return provider_classes.get(provider_type, CloudflareProvider)  # Default fallback

    async def health_check(self) -> Dict[str, bool]:
        """Perform health check on all providers"""
        health = {}
        for name, provider in self.providers.items():
            health[name] = provider.is_connected
        return health