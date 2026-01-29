"""异步 Redis 客户端封装（v4.0.0）

基于 redis.asyncio 提供完整的异步 Redis 操作能力

v4.0.0 新增:
- AsyncRedis: 完全异步的 Redis 客户端
- 性能提升：支持并发缓存操作
- 基于 redis.asyncio
"""

from __future__ import annotations

import time
from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any, TypeVar

import redis.asyncio as aioredis

from df_test_framework.core.events import (
    CacheOperationEndEvent,
    CacheOperationErrorEvent,
    CacheOperationStartEvent,
)
from df_test_framework.infrastructure.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")

if TYPE_CHECKING:
    from df_test_framework.bootstrap.runtime import RuntimeContext


class AsyncRedis:
    """异步 Redis 客户端封装（v4.0.0）

    功能:
    - 提供异步 Redis 连接管理
    - 封装常用的异步 Redis 操作
    - 支持连接池
    - EventBus 事件发布
    - 性能提升：支持并发缓存操作

    使用示例:
        >>> # 基础使用
        >>> async_redis = AsyncRedis(host="localhost", port=6379)
        >>>
        >>> # 异步操作
        >>> await async_redis.set("key", "value", ex=3600)
        >>> value = await async_redis.get("key")
        >>>
        >>> # 并发操作（性能提升显著）
        >>> tasks = [
        ...     async_redis.get(f"user:{i}")
        ...     for i in range(100)
        ... ]
        >>> results = await asyncio.gather(*tasks)
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        max_connections: int = 50,
        decode_responses: bool = True,
        runtime: RuntimeContext | None = None,
    ):
        """初始化异步 Redis 客户端

        Args:
            host: Redis 主机地址
            port: Redis 端口
            db: 数据库编号
            password: 密码
            max_connections: 连接池最大连接数
            decode_responses: 是否自动解码响应为字符串
            runtime: RuntimeContext 实例

        Note:
            v4.0.0: 完全异步化
            - 所有方法都是异步的，需要 await 调用
            - 使用 redis.asyncio 实现
        """
        self.host = host
        self.port = port
        self.db = db
        self._runtime = runtime

        # 创建异步连接池
        self.pool = aioredis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            max_connections=max_connections,
            decode_responses=decode_responses,
        )

        # 创建异步 Redis 客户端
        self.client = aioredis.Redis(connection_pool=self.pool)

        # ObservabilityLogger
        from df_test_framework.infrastructure.logging.observability import redis_logger

        self.obs_logger = redis_logger()

        logger.info(f"异步 Redis 连接已建立: {host}:{port}/{db}")

    def _publish_event(self, event: Any) -> None:
        """发布事件（同步发布，不阻塞异步流程）"""
        if self._runtime:
            try:
                self._runtime.publish_event(event)
            except Exception:
                pass  # 静默失败，不影响主流程

    async def _execute_operation(
        self,
        operation: str,
        key: str,
        func: Callable[[], Coroutine[Any, Any, T]],
        field: str | None = None,
        is_read: bool = False,
        value: Any | None = None,
    ) -> T:
        """统一的异步操作执行包装器

        提供 EventBus 事件发布、可观测性日志的统一处理。

        Args:
            operation: 操作类型（SET, GET, HSET 等）
            key: 缓存键
            func: 实际执行的异步操作函数
            field: Hash 操作的字段名（可选）
            is_read: 是否为读取操作（用于计算 hit）
            value: 写入的值（用于日志记录）

        Returns:
            操作结果
        """
        # 1. 发布开始事件
        start_event, correlation_id = CacheOperationStartEvent.create(
            operation=operation, key=key, field=field
        )
        self._publish_event(start_event)

        # 2. 记录可观测性日志
        self.obs_logger.cache_operation(operation, key)

        # 3. 执行异步操作
        start_time = time.perf_counter()
        try:
            result = await func()
            duration_ms = (time.perf_counter() - start_time) * 1000

            # 4. 计算 hit 状态（读取操作）
            hit = None
            if is_read:
                hit = result is not None

            # 5. 发布结束事件
            end_event = CacheOperationEndEvent.create(
                correlation_id=correlation_id,
                operation=operation,
                key=key,
                duration_ms=duration_ms,
                hit=hit,
            )
            self._publish_event(end_event)

            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000

            # 发布错误事件
            error_event = CacheOperationErrorEvent.create(
                correlation_id=correlation_id,
                operation=operation,
                key=key,
                error=e,
                duration_ms=duration_ms,
            )
            self._publish_event(error_event)

            raise

    async def ping(self) -> bool:
        """测试连接

        Returns:
            连接是否正常
        """
        try:
            return await self.client.ping()
        except Exception as e:
            logger.error(f"异步 Redis 连接测试失败: {str(e)}")
            return False

    # ========== 字符串操作 ==========

    async def set(
        self,
        key: str,
        value: Any,
        ex: int | None = None,
        nx: bool = False,
    ) -> bool:
        """异步设置键值

        Args:
            key: 键
            value: 值
            ex: 过期时间(秒)
            nx: 如果键不存在才设置

        Returns:
            是否成功
        """
        return await self._execute_operation(
            operation="SET",
            key=key,
            func=lambda: self.client.set(key, value, ex=ex, nx=nx),
            value=value,
        )

    async def get(self, key: str) -> str | None:
        """异步获取值

        Args:
            key: 键

        Returns:
            值，如果不存在返回 None
        """
        return await self._execute_operation(
            operation="GET",
            key=key,
            func=lambda: self.client.get(key),
            is_read=True,
        )

    async def delete(self, *keys: str) -> int:
        """异步删除键

        Args:
            *keys: 要删除的键

        Returns:
            删除的键数量
        """
        primary_key = keys[0] if keys else ""
        return await self._execute_operation(
            operation="DELETE",
            key=primary_key if len(keys) == 1 else f"{primary_key},...({len(keys)} keys)",
            func=lambda: self.client.delete(*keys),
        )

    async def exists(self, *keys: str) -> int:
        """异步检查键是否存在

        Args:
            *keys: 要检查的键

        Returns:
            存在的键数量
        """
        primary_key = keys[0] if keys else ""
        return await self._execute_operation(
            operation="EXISTS",
            key=primary_key if len(keys) == 1 else f"{primary_key},...({len(keys)} keys)",
            func=lambda: self.client.exists(*keys),
            is_read=True,
        )

    async def expire(self, key: str, seconds: int) -> bool:
        """异步设置键的过期时间

        Args:
            key: 键
            seconds: 过期时间(秒)

        Returns:
            是否成功
        """
        return await self._execute_operation(
            operation="EXPIRE",
            key=key,
            func=lambda: self.client.expire(key, seconds),
            value=f"{seconds}s",
        )

    async def ttl(self, key: str) -> int:
        """异步获取键的剩余过期时间

        Args:
            key: 键

        Returns:
            剩余秒数，-1 表示永久，-2 表示不存在
        """
        return await self._execute_operation(
            operation="TTL",
            key=key,
            func=lambda: self.client.ttl(key),
            is_read=True,
        )

    async def incr(self, key: str, amount: int = 1) -> int:
        """异步自增

        Args:
            key: 键
            amount: 增量

        Returns:
            增后的值
        """
        return await self._execute_operation(
            operation="INCR",
            key=key,
            func=lambda: self.client.incr(key, amount),
            value=amount,
        )

    async def decr(self, key: str, amount: int = 1) -> int:
        """异步自减

        Args:
            key: 键
            amount: 减量

        Returns:
            减后的值
        """
        return await self._execute_operation(
            operation="DECR",
            key=key,
            func=lambda: self.client.decr(key, amount),
            value=amount,
        )

    async def mget(self, *keys: str) -> list[str | None]:
        """异步批量获取值

        Args:
            *keys: 要获取的键

        Returns:
            值列表
        """
        primary_key = keys[0] if keys else ""
        return await self._execute_operation(
            operation="MGET",
            key=primary_key if len(keys) == 1 else f"{primary_key},...({len(keys)} keys)",
            func=lambda: self.client.mget(*keys),
            is_read=True,
        )

    async def mset(self, mapping: dict[str, Any]) -> bool:
        """异步批量设置值

        Args:
            mapping: {key: value} 字典

        Returns:
            是否成功
        """
        first_key = next(iter(mapping.keys())) if mapping else ""
        return await self._execute_operation(
            operation="MSET",
            key=first_key if len(mapping) == 1 else f"{first_key},...({len(mapping)} keys)",
            func=lambda: self.client.mset(mapping),
            value=f"[{len(mapping)} items]",
        )

    # ========== 哈希操作 ==========

    async def hset(self, name: str, key: str, value: Any) -> int:
        """异步设置哈希字段

        Args:
            name: 哈希名
            key: 字段名
            value: 字段值

        Returns:
            新创建的字段数量
        """
        return await self._execute_operation(
            operation="HSET",
            key=name,
            field=key,
            func=lambda: self.client.hset(name, key, value),
            value=value,
        )

    async def hget(self, name: str, key: str) -> str | None:
        """异步获取哈希字段

        Args:
            name: 哈希名
            key: 字段名

        Returns:
            字段值
        """
        return await self._execute_operation(
            operation="HGET",
            key=name,
            field=key,
            func=lambda: self.client.hget(name, key),
            is_read=True,
        )

    async def hgetall(self, name: str) -> dict:
        """异步获取哈希所有字段

        Args:
            name: 哈希名

        Returns:
            所有字段的字典
        """
        return await self._execute_operation(
            operation="HGETALL",
            key=name,
            func=lambda: self.client.hgetall(name),
            is_read=True,
        )

    async def hdel(self, name: str, *keys: str) -> int:
        """异步删除哈希字段

        Args:
            name: 哈希名
            *keys: 要删除的字段

        Returns:
            删除的字段数量
        """
        return await self._execute_operation(
            operation="HDEL",
            key=name,
            field=keys[0] if len(keys) == 1 else f"{keys[0]},...({len(keys)} fields)",
            func=lambda: self.client.hdel(name, *keys),
        )

    async def hexists(self, name: str, key: str) -> bool:
        """异步检查哈希字段是否存在

        Args:
            name: 哈希名
            key: 字段名

        Returns:
            是否存在
        """
        return await self._execute_operation(
            operation="HEXISTS",
            key=name,
            field=key,
            func=lambda: self.client.hexists(name, key),
            is_read=True,
        )

    async def hkeys(self, name: str) -> list:
        """异步获取哈希所有字段名

        Args:
            name: 哈希名

        Returns:
            字段名列表
        """
        return await self._execute_operation(
            operation="HKEYS",
            key=name,
            func=lambda: self.client.hkeys(name),
            is_read=True,
        )

    async def hvals(self, name: str) -> list:
        """异步获取哈希所有字段值

        Args:
            name: 哈希名

        Returns:
            字段值列表
        """
        return await self._execute_operation(
            operation="HVALS",
            key=name,
            func=lambda: self.client.hvals(name),
            is_read=True,
        )

    async def hlen(self, name: str) -> int:
        """异步获取哈希字段数量

        Args:
            name: 哈希名

        Returns:
            字段数量
        """
        return await self._execute_operation(
            operation="HLEN",
            key=name,
            func=lambda: self.client.hlen(name),
            is_read=True,
        )

    async def hmset(self, name: str, mapping: dict[str, Any]) -> bool:
        """异步批量设置哈希字段

        Args:
            name: 哈希名
            mapping: {field: value} 字典

        Returns:
            是否成功
        """
        return await self._execute_operation(
            operation="HMSET",
            key=name,
            func=lambda: self.client.hset(name, mapping=mapping),
            value=f"[{len(mapping)} fields]",
        )

    async def hmget(self, name: str, *keys: str) -> list:
        """异步批量获取哈希字段

        Args:
            name: 哈希名
            *keys: 字段名列表

        Returns:
            字段值列表
        """
        return await self._execute_operation(
            operation="HMGET",
            key=name,
            field=keys[0] if len(keys) == 1 else f"{keys[0]},...({len(keys)} fields)",
            func=lambda: self.client.hmget(name, *keys),
            is_read=True,
        )

    # ========== 列表操作 ==========

    async def lpush(self, name: str, *values: Any) -> int:
        """异步从左边推入列表

        Args:
            name: 列表名
            *values: 要推入的值

        Returns:
            列表长度
        """
        return await self._execute_operation(
            operation="LPUSH",
            key=name,
            func=lambda: self.client.lpush(name, *values),
            value=values[0] if len(values) == 1 else f"[{len(values)} items]",
        )

    async def rpush(self, name: str, *values: Any) -> int:
        """异步从右边推入列表

        Args:
            name: 列表名
            *values: 要推入的值

        Returns:
            列表长度
        """
        return await self._execute_operation(
            operation="RPUSH",
            key=name,
            func=lambda: self.client.rpush(name, *values),
            value=values[0] if len(values) == 1 else f"[{len(values)} items]",
        )

    async def lpop(self, name: str) -> str | None:
        """异步从左边弹出

        Args:
            name: 列表名

        Returns:
            弹出的值
        """
        return await self._execute_operation(
            operation="LPOP",
            key=name,
            func=lambda: self.client.lpop(name),
            is_read=True,
        )

    async def rpop(self, name: str) -> str | None:
        """异步从右边弹出

        Args:
            name: 列表名

        Returns:
            弹出的值
        """
        return await self._execute_operation(
            operation="RPOP",
            key=name,
            func=lambda: self.client.rpop(name),
            is_read=True,
        )

    async def lrange(self, name: str, start: int, end: int) -> list:
        """异步获取列表范围

        Args:
            name: 列表名
            start: 起始索引
            end: 结束索引

        Returns:
            元素列表
        """
        return await self._execute_operation(
            operation="LRANGE",
            key=name,
            func=lambda: self.client.lrange(name, start, end),
            is_read=True,
        )

    async def llen(self, name: str) -> int:
        """异步获取列表长度

        Args:
            name: 列表名

        Returns:
            列表长度
        """
        return await self._execute_operation(
            operation="LLEN",
            key=name,
            func=lambda: self.client.llen(name),
            is_read=True,
        )

    async def lindex(self, name: str, index: int) -> str | None:
        """异步获取列表指定索引的元素

        Args:
            name: 列表名
            index: 索引

        Returns:
            元素值
        """
        return await self._execute_operation(
            operation="LINDEX",
            key=name,
            func=lambda: self.client.lindex(name, index),
            is_read=True,
        )

    # ========== 集合操作 ==========

    async def sadd(self, name: str, *values: Any) -> int:
        """异步添加到集合

        Args:
            name: 集合名
            *values: 要添加的值

        Returns:
            新添加的元素数量
        """
        return await self._execute_operation(
            operation="SADD",
            key=name,
            func=lambda: self.client.sadd(name, *values),
            value=values[0] if len(values) == 1 else f"[{len(values)} items]",
        )

    async def smembers(self, name: str) -> set:
        """异步获取集合所有成员

        Args:
            name: 集合名

        Returns:
            成员集合
        """
        return await self._execute_operation(
            operation="SMEMBERS",
            key=name,
            func=lambda: self.client.smembers(name),
            is_read=True,
        )

    async def srem(self, name: str, *values: Any) -> int:
        """异步从集合移除

        Args:
            name: 集合名
            *values: 要移除的值

        Returns:
            移除的元素数量
        """
        return await self._execute_operation(
            operation="SREM",
            key=name,
            func=lambda: self.client.srem(name, *values),
            value=values[0] if len(values) == 1 else f"[{len(values)} items]",
        )

    async def sismember(self, name: str, value: Any) -> bool:
        """异步检查是否为集合成员

        Args:
            name: 集合名
            value: 要检查的值

        Returns:
            是否为成员
        """
        return await self._execute_operation(
            operation="SISMEMBER",
            key=name,
            func=lambda: self.client.sismember(name, value),
            is_read=True,
        )

    async def scard(self, name: str) -> int:
        """异步获取集合大小

        Args:
            name: 集合名

        Returns:
            集合大小
        """
        return await self._execute_operation(
            operation="SCARD",
            key=name,
            func=lambda: self.client.scard(name),
            is_read=True,
        )

    # ========== 有序集合操作 ==========

    async def zadd(self, name: str, mapping: dict) -> int:
        """异步添加到有序集合

        Args:
            name: 有序集合名
            mapping: {member: score} 字典

        Returns:
            新添加的元素数量
        """
        return await self._execute_operation(
            operation="ZADD",
            key=name,
            func=lambda: self.client.zadd(name, mapping),
            value=f"[{len(mapping)} items]",
        )

    async def zrange(self, name: str, start: int, end: int, withscores: bool = False) -> list:
        """异步获取有序集合范围

        Args:
            name: 有序集合名
            start: 起始索引
            end: 结束索引
            withscores: 是否返回分数

        Returns:
            元素列表
        """
        return await self._execute_operation(
            operation="ZRANGE",
            key=name,
            func=lambda: self.client.zrange(name, start, end, withscores=withscores),
            is_read=True,
        )

    async def zrevrange(self, name: str, start: int, end: int, withscores: bool = False) -> list:
        """异步获取有序集合逆序范围

        Args:
            name: 有序集合名
            start: 起始索引
            end: 结束索引
            withscores: 是否返回分数

        Returns:
            元素列表
        """
        return await self._execute_operation(
            operation="ZREVRANGE",
            key=name,
            func=lambda: self.client.zrevrange(name, start, end, withscores=withscores),
            is_read=True,
        )

    async def zscore(self, name: str, value: Any) -> float | None:
        """异步获取有序集合成员的分数

        Args:
            name: 有序集合名
            value: 成员

        Returns:
            分数
        """
        return await self._execute_operation(
            operation="ZSCORE",
            key=name,
            func=lambda: self.client.zscore(name, value),
            is_read=True,
        )

    async def zcard(self, name: str) -> int:
        """异步获取有序集合大小

        Args:
            name: 有序集合名

        Returns:
            集合大小
        """
        return await self._execute_operation(
            operation="ZCARD",
            key=name,
            func=lambda: self.client.zcard(name),
            is_read=True,
        )

    async def zrank(self, name: str, value: Any) -> int | None:
        """异步获取有序集合成员的排名

        Args:
            name: 有序集合名
            value: 成员

        Returns:
            排名（从 0 开始）
        """
        return await self._execute_operation(
            operation="ZRANK",
            key=name,
            func=lambda: self.client.zrank(name, value),
            is_read=True,
        )

    async def zrem(self, name: str, *values: Any) -> int:
        """异步从有序集合移除

        Args:
            name: 有序集合名
            *values: 要移除的成员

        Returns:
            移除的元素数量
        """
        return await self._execute_operation(
            operation="ZREM",
            key=name,
            func=lambda: self.client.zrem(name, *values),
            value=values[0] if len(values) == 1 else f"[{len(values)} items]",
        )

    # ========== 通用操作 ==========

    async def keys(self, pattern: str = "*") -> list:
        """异步获取匹配的键列表

        Args:
            pattern: 匹配模式

        Returns:
            键列表
        """
        return await self._execute_operation(
            operation="KEYS",
            key=pattern,
            func=lambda: self.client.keys(pattern),
            is_read=True,
        )

    async def scan(
        self,
        cursor: int = 0,
        match: str | None = None,
        count: int | None = None,
    ) -> tuple[int, list]:
        """异步增量迭代键

        Args:
            cursor: 游标
            match: 匹配模式
            count: 每次返回数量提示

        Returns:
            (新游标, 键列表)
        """
        return await self._execute_operation(
            operation="SCAN",
            key=match or "*",
            func=lambda: self.client.scan(cursor=cursor, match=match, count=count),
            is_read=True,
        )

    async def type(self, key: str) -> str:
        """异步获取键的类型

        Args:
            key: 键

        Returns:
            类型（string, list, set, zset, hash, none）
        """
        return await self._execute_operation(
            operation="TYPE",
            key=key,
            func=lambda: self.client.type(key),
            is_read=True,
        )

    async def rename(self, src: str, dst: str) -> bool:
        """异步重命名键

        Args:
            src: 源键名
            dst: 目标键名

        Returns:
            是否成功
        """
        return await self._execute_operation(
            operation="RENAME",
            key=f"{src} -> {dst}",
            func=lambda: self.client.rename(src, dst),
        )

    async def flushdb(self) -> bool:
        """异步清空当前数据库"""
        logger.warning(f"清空 Redis 数据库: DB{self.db}")
        return await self.client.flushdb()

    async def close(self) -> None:
        """关闭异步连接"""
        await self.client.aclose()
        logger.info("异步 Redis 连接已关闭")


__all__ = ["AsyncRedis"]
