"""Redis 模块（v4.0.0 异步优先）

v4.0.0 重大变更：异步优先，同步兼容
- AsyncRedis: 异步 Redis 客户端（推荐，支持并发操作）
- RedisClient: 同步 Redis 客户端（向后兼容）

导入示例:
    # v4.0.0 异步版本（推荐）
    from df_test_framework.capabilities.databases.redis import AsyncRedis

    async_redis = AsyncRedis(host="localhost", port=6379)
    value = await async_redis.get("key")

    # v3.x 同步版本（兼容）
    from df_test_framework.capabilities.databases.redis import RedisClient

    redis_client = RedisClient(host="localhost", port=6379)
    value = redis_client.get("key")
"""

# 异步版本（推荐，v4.0.0）
from .async_redis import AsyncRedis

# 同步版本（兼容，v3.x）
from .redis_client import RedisClient

__all__ = ["AsyncRedis", "RedisClient"]
