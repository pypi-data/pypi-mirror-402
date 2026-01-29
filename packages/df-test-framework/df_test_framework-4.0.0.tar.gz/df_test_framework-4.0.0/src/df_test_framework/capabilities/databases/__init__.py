"""数据访问能力层 - Layer 1（v4.0.0 异步优先）

提供SQL、NoSQL等数据库访问能力
按数据库类型扁平化组织：mysql/、postgresql/、redis/、mongodb/等

v4.0.0 重大变更：异步优先，同步兼容
- AsyncDatabase: 异步数据库客户端（推荐，支持并发操作）
- Database: 同步数据库客户端（向后兼容）
- AsyncRedis: 异步 Redis 客户端（推荐，支持并发操作）
- RedisClient: 同步 Redis 客户端（向后兼容）

v3.13.0 变更:
- UnitOfWork 支持配置驱动（repository_package 通过配置指定）
- 移除 BaseUnitOfWork（直接使用 UnitOfWork）

v3.11.1 新增:
- QueryBuilder：流式查询构建器（P2-2）

导入示例:
    # v4.0.0 异步版本（推荐）
    from df_test_framework.capabilities.databases import AsyncDatabase, AsyncRedis

    async_db = AsyncDatabase("mysql+aiomysql://user:pass@host/db")
    users = await async_db.query_all("SELECT * FROM users")

    async_redis = AsyncRedis(host="localhost", port=6379)
    value = await async_redis.get("key")

    # v3.x 同步版本（兼容）
    from df_test_framework.capabilities.databases import Database, RedisClient

    db = Database("mysql+pymysql://user:pass@host/db")
    users = db.query_all("SELECT * FROM users")

    redis_client = RedisClient(host="localhost", port=6379)
    value = redis_client.get("key")
"""

# 工厂类
# 异步版本（推荐，v4.0.0）
from .async_database import AsyncDatabase

# 同步版本（兼容，v3.x）
from .database import Database
from .factory import DatabaseFactory

# Query Builder（v3.11.1 P2-2）
from .query_builder import QueryBuilder

# Redis 客户端（v4.0.0 异步优先）
from .redis.async_redis import AsyncRedis
from .redis.redis_client import RedisClient

# Repository模式
from .repositories.base import BaseRepository
from .repositories.query_spec import QuerySpec

# Unit of Work 模式
from .uow import UnitOfWork

__all__ = [
    # 工厂
    "DatabaseFactory",
    # 异步版本（推荐，v4.0.0）
    "AsyncDatabase",
    "AsyncRedis",
    # 同步版本（兼容，v3.x）
    "Database",
    "RedisClient",
    # Unit of Work
    "UnitOfWork",
    # Repository 模式
    "BaseRepository",
    "QuerySpec",
    # Query Builder
    "QueryBuilder",
]
