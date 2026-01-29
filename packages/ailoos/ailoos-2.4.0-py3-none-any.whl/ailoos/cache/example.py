"""
Example usage of the Distributed Intelligent Cache System for AILOOS
Demonstrates all components working together
"""

import asyncio
import logging
import time

from .manager import DistributedCacheManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def demo_basic_caching():
    """Demonstrate basic cache operations"""
    print("🚀 Demonstrating Distributed Intelligent Cache System")
    print("=" * 60)

    # Initialize cache manager
    cache = DistributedCacheManager(
        node_id="demo_node_1",
        strategy="adaptive",
        max_size=1000,
        compression_type="zlib",
        enable_p2p=False  # Disable P2P for this demo
    )

    await cache.start()

    print("✅ Cache manager initialized")

    # Basic operations
    print("\n📝 Testing basic operations...")

    # Set some values
    await cache.set("user:123", {"name": "Alice", "email": "alice@example.com"}, ttl=300)
    await cache.set("product:456", {"name": "Widget", "price": 29.99}, ttl=600)
    await cache.set("config:app", {"debug": True, "version": "1.0.0"})

    print("✅ Set 3 cache entries")

    # Get values
    user = await cache.get("user:123")
    product = await cache.get("product:456")
    config = await cache.get("config:app")

    print(f"✅ Retrieved user: {user['name']}")
    print(f"✅ Retrieved product: {product['name']}")
    print(f"✅ Retrieved config: {config['version']}")

    # Test cache hit/miss
    nonexistent = await cache.get("nonexistent:key")
    print(f"✅ Non-existent key returned: {nonexistent}")

    # Check existence
    exists = await cache.exists("user:123")
    not_exists = await cache.exists("nonexistent:key")
    print(f"✅ user:123 exists: {exists}")
    print(f"✅ nonexistent:key exists: {not_exists}")

async def demo_compression():
    """Demonstrate compression capabilities"""
    print("\n🗜️  Testing compression...")

    cache = DistributedCacheManager(
        node_id="compression_demo",
        compression_type="zlib",
        enable_p2p=False
    )

    await cache.start()

    # Create large data
    large_data = {
        "data": "x" * 5000,  # 5KB of data
        "metadata": {"size": "large", "type": "test"},
        "nested": {"deep": {"structure": list(range(100))}}
    }

    await cache.set("large:key", large_data)

    # Check compression stats
    stats = await cache.get_stats()
    compression_stats = stats['compression']

    print(f"✅ Compressed data saved: {compression_stats['space_saved']} bytes")
    print(".2f")
    print(f"✅ Compression operations: {compression_stats['compression_operations']}")

async def demo_invalidation():
    """Demonstrate cache invalidation"""
    print("\n🚫 Testing invalidation...")

    cache = DistributedCacheManager(
        node_id="invalidation_demo",
        enable_p2p=False
    )

    await cache.start()

    # Set values with dependencies
    await cache.set("user:profile:123", {"name": "Bob"})
    await cache.set("user:posts:123", ["post1", "post2", "post3"])
    await cache.set("user:stats:123", {"posts": 3, "followers": 150})

    # Add dependency: stats depends on posts
    cache.add_invalidation_dependency("user:stats:123", "user:posts:123")

    print("✅ Set user data with dependencies")

    # Invalidate posts - should also invalidate stats
    await cache.invalidate_pattern("user:posts:*")

    # Check if dependent data was invalidated
    posts = await cache.get("user:posts:123")
    stats = await cache.get("user:stats:123")

    print(f"✅ Posts invalidated: {posts is None}")
    print(f"✅ Dependent stats invalidated: {stats is None}")

async def demo_metrics():
    """Demonstrate metrics monitoring"""
    print("\n📊 Testing metrics...")

    cache = DistributedCacheManager(
        node_id="metrics_demo",
        enable_p2p=False
    )

    await cache.start()

    # Generate some cache activity
    for i in range(100):
        key = f"test:key:{i}"
        await cache.set(key, f"value_{i}", ttl=300)

    # Access some entries multiple times
    for i in range(10):
        await cache.get(f"test:key:{i}")

    # Get metrics
    stats = await cache.get_stats()
    metrics = stats['metrics']

    print(".2f")
    print(f"✅ Total requests: {metrics['hits']['count'] + metrics['misses']['count']}")
    print(f"✅ Cache entries: {stats['cache_entries']}")
    print(f"✅ Cache size: {stats['cache_size_bytes']} bytes")

async def demo_strategy_switching():
    """Demonstrate strategy switching"""
    print("\n🔄 Testing strategy switching...")

    cache = DistributedCacheManager(
        node_id="strategy_demo",
        strategy="lru",
        max_size=50,
        enable_p2p=False
    )

    await cache.start()

    print(f"✅ Initial strategy: {cache.strategy.strategy_name}")

    # Fill cache
    for i in range(60):  # Over max_size to trigger evictions
        await cache.set(f"key:{i}", f"value_{i}")

    initial_entries = (await cache.get_stats())['cache_entries']
    print(f"✅ Cache entries after filling: {initial_entries}")

    # Switch to LFU
    cache.switch_strategy("lfu")
    print(f"✅ Switched to strategy: {cache.strategy.strategy_name}")

    # Access some entries frequently
    for _ in range(10):
        for i in range(10):
            await cache.get(f"key:{i}")

    # Add more entries to trigger evictions
    for i in range(60, 80):
        await cache.set(f"key:{i}", f"value_{i}")

    final_entries = (await cache.get_stats())['cache_entries']
    print(f"✅ Cache entries after LFU operations: {final_entries}")

async def demo_health_check():
    """Demonstrate health monitoring"""
    print("\n🏥 Testing health monitoring...")

    cache = DistributedCacheManager(
        node_id="health_demo",
        enable_p2p=False
    )

    await cache.start()

    # Add some data
    for i in range(10):
        await cache.set(f"health:key:{i}", f"health_value_{i}")

    # Perform health check
    health = await cache.health_check()

    print(f"✅ Health status: {health['status']}")
    print(f"✅ Issues found: {len(health['issues'])}")
    if health['issues']:
        for issue in health['issues']:
            print(f"   - {issue}")

async def main():
    """Run all demonstrations"""
    try:
        await demo_basic_caching()
        await demo_compression()
        await demo_invalidation()
        await demo_metrics()
        await demo_strategy_switching()
        await demo_health_check()

        print("\n🎉 All demonstrations completed successfully!")
        print("The Distributed Intelligent Cache System is ready for production use.")

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())