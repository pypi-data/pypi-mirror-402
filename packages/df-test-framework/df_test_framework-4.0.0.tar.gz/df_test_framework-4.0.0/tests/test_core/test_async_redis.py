"""测试 AsyncRedis（v4.0.0）

验证异步 Redis 客户端的各种操作方法。
"""

from unittest.mock import AsyncMock, patch

import pytest

from df_test_framework.capabilities.databases.redis.async_redis import AsyncRedis
from df_test_framework.core.events import (
    CacheOperationEndEvent,
    CacheOperationErrorEvent,
    CacheOperationStartEvent,
)
from df_test_framework.infrastructure.events import EventBus


class TestAsyncRedisInit:
    """测试 AsyncRedis 初始化"""

    @patch("redis.asyncio.ConnectionPool")
    @patch("redis.asyncio.Redis")
    def test_client_creation_default(self, mock_redis, mock_pool):
        """测试使用默认配置创建"""
        client = AsyncRedis()

        assert client.host == "localhost"
        assert client.port == 6379
        assert client.db == 0

        # 验证连接池被创建
        mock_pool.assert_called_once()

    @patch("redis.asyncio.ConnectionPool")
    @patch("redis.asyncio.Redis")
    def test_client_creation_custom(self, mock_redis, mock_pool):
        """测试使用自定义配置创建"""
        client = AsyncRedis(
            host="redis.example.com",
            port=6380,
            db=1,
            password="secret",
            max_connections=100,
        )

        assert client.host == "redis.example.com"
        assert client.port == 6380
        assert client.db == 1

        # 验证连接池被创建时使用了正确的参数
        mock_pool.assert_called_once()
        call_kwargs = mock_pool.call_args[1]
        assert call_kwargs["host"] == "redis.example.com"
        assert call_kwargs["port"] == 6380
        assert call_kwargs["db"] == 1
        assert call_kwargs["password"] == "secret"
        assert call_kwargs["max_connections"] == 100


class TestAsyncRedisPing:
    """测试 ping 方法"""

    @pytest.mark.asyncio
    @patch("redis.asyncio.ConnectionPool")
    @patch("redis.asyncio.Redis")
    async def test_ping_success(self, mock_redis, mock_pool):
        """测试 ping 成功"""
        mock_client = AsyncMock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client

        client = AsyncRedis()
        result = await client.ping()

        assert result is True
        mock_client.ping.assert_called_once()

    @pytest.mark.asyncio
    @patch("redis.asyncio.ConnectionPool")
    @patch("redis.asyncio.Redis")
    async def test_ping_failure(self, mock_redis, mock_pool):
        """测试 ping 失败"""
        mock_client = AsyncMock()
        mock_client.ping.side_effect = Exception("Connection failed")
        mock_redis.return_value = mock_client

        client = AsyncRedis()
        result = await client.ping()

        assert result is False


class TestAsyncRedisStringOperations:
    """测试字符串操作"""

    @pytest.fixture
    def async_redis_client(self):
        """创建 mock 异步 Redis 客户端"""
        with patch("redis.asyncio.ConnectionPool"), patch("redis.asyncio.Redis") as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            client = AsyncRedis()
            client._mock_client = mock_client
            yield client

    @pytest.mark.asyncio
    async def test_set(self, async_redis_client):
        """测试 set 方法"""
        async_redis_client._mock_client.set.return_value = True

        result = await async_redis_client.set("key1", "value1")

        assert result is True
        async_redis_client._mock_client.set.assert_called_once_with(
            "key1", "value1", ex=None, nx=False
        )

    @pytest.mark.asyncio
    async def test_set_with_expiration(self, async_redis_client):
        """测试带过期时间的 set"""
        async_redis_client._mock_client.set.return_value = True

        result = await async_redis_client.set("key1", "value1", ex=60)

        assert result is True
        async_redis_client._mock_client.set.assert_called_once_with(
            "key1", "value1", ex=60, nx=False
        )

    @pytest.mark.asyncio
    async def test_set_with_nx(self, async_redis_client):
        """测试带 nx 标志的 set"""
        async_redis_client._mock_client.set.return_value = True

        result = await async_redis_client.set("key1", "value1", nx=True)

        assert result is True
        async_redis_client._mock_client.set.assert_called_once_with(
            "key1", "value1", ex=None, nx=True
        )

    @pytest.mark.asyncio
    async def test_get(self, async_redis_client):
        """测试 get 方法"""
        async_redis_client._mock_client.get.return_value = "value1"

        result = await async_redis_client.get("key1")

        assert result == "value1"
        async_redis_client._mock_client.get.assert_called_once_with("key1")

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, async_redis_client):
        """测试获取不存在的键"""
        async_redis_client._mock_client.get.return_value = None

        result = await async_redis_client.get("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, async_redis_client):
        """测试 delete 方法"""
        async_redis_client._mock_client.delete.return_value = 1

        result = await async_redis_client.delete("key1")

        assert result == 1
        async_redis_client._mock_client.delete.assert_called_once_with("key1")

    @pytest.mark.asyncio
    async def test_delete_multiple(self, async_redis_client):
        """测试删除多个键"""
        async_redis_client._mock_client.delete.return_value = 2

        result = await async_redis_client.delete("key1", "key2")

        assert result == 2
        async_redis_client._mock_client.delete.assert_called_once_with("key1", "key2")

    @pytest.mark.asyncio
    async def test_exists(self, async_redis_client):
        """测试 exists 方法"""
        async_redis_client._mock_client.exists.return_value = 1

        result = await async_redis_client.exists("key1")

        assert result == 1
        async_redis_client._mock_client.exists.assert_called_once_with("key1")

    @pytest.mark.asyncio
    async def test_expire(self, async_redis_client):
        """测试 expire 方法"""
        async_redis_client._mock_client.expire.return_value = True

        result = await async_redis_client.expire("key1", 60)

        assert result is True
        async_redis_client._mock_client.expire.assert_called_once_with("key1", 60)

    @pytest.mark.asyncio
    async def test_ttl(self, async_redis_client):
        """测试 ttl 方法"""
        async_redis_client._mock_client.ttl.return_value = 60

        result = await async_redis_client.ttl("key1")

        assert result == 60
        async_redis_client._mock_client.ttl.assert_called_once_with("key1")

    @pytest.mark.asyncio
    async def test_incr(self, async_redis_client):
        """测试 incr 方法"""
        async_redis_client._mock_client.incr.return_value = 2

        result = await async_redis_client.incr("counter")

        assert result == 2
        async_redis_client._mock_client.incr.assert_called_once_with("counter", 1)

    @pytest.mark.asyncio
    async def test_decr(self, async_redis_client):
        """测试 decr 方法"""
        async_redis_client._mock_client.decr.return_value = 0

        result = await async_redis_client.decr("counter")

        assert result == 0
        async_redis_client._mock_client.decr.assert_called_once_with("counter", 1)

    @pytest.mark.asyncio
    async def test_mget(self, async_redis_client):
        """测试 mget 方法"""
        async_redis_client._mock_client.mget.return_value = ["value1", "value2", None]

        result = await async_redis_client.mget("key1", "key2", "key3")

        assert result == ["value1", "value2", None]
        async_redis_client._mock_client.mget.assert_called_once_with("key1", "key2", "key3")

    @pytest.mark.asyncio
    async def test_mset(self, async_redis_client):
        """测试 mset 方法"""
        async_redis_client._mock_client.mset.return_value = True

        result = await async_redis_client.mset({"key1": "value1", "key2": "value2"})

        assert result is True
        async_redis_client._mock_client.mset.assert_called_once_with(
            {"key1": "value1", "key2": "value2"}
        )


class TestAsyncRedisHashOperations:
    """测试哈希操作"""

    @pytest.fixture
    def async_redis_client(self):
        """创建 mock 异步 Redis 客户端"""
        with patch("redis.asyncio.ConnectionPool"), patch("redis.asyncio.Redis") as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            client = AsyncRedis()
            client._mock_client = mock_client
            yield client

    @pytest.mark.asyncio
    async def test_hset(self, async_redis_client):
        """测试 hset 方法"""
        async_redis_client._mock_client.hset.return_value = 1

        result = await async_redis_client.hset("hash1", "field1", "value1")

        assert result == 1
        async_redis_client._mock_client.hset.assert_called_once_with("hash1", "field1", "value1")

    @pytest.mark.asyncio
    async def test_hget(self, async_redis_client):
        """测试 hget 方法"""
        async_redis_client._mock_client.hget.return_value = "value1"

        result = await async_redis_client.hget("hash1", "field1")

        assert result == "value1"
        async_redis_client._mock_client.hget.assert_called_once_with("hash1", "field1")

    @pytest.mark.asyncio
    async def test_hgetall(self, async_redis_client):
        """测试 hgetall 方法"""
        async_redis_client._mock_client.hgetall.return_value = {
            "field1": "value1",
            "field2": "value2",
        }

        result = await async_redis_client.hgetall("hash1")

        assert result == {"field1": "value1", "field2": "value2"}
        async_redis_client._mock_client.hgetall.assert_called_once_with("hash1")

    @pytest.mark.asyncio
    async def test_hdel(self, async_redis_client):
        """测试 hdel 方法"""
        async_redis_client._mock_client.hdel.return_value = 1

        result = await async_redis_client.hdel("hash1", "field1")

        assert result == 1
        async_redis_client._mock_client.hdel.assert_called_once_with("hash1", "field1")

    @pytest.mark.asyncio
    async def test_hexists(self, async_redis_client):
        """测试 hexists 方法"""
        async_redis_client._mock_client.hexists.return_value = True

        result = await async_redis_client.hexists("hash1", "field1")

        assert result is True
        async_redis_client._mock_client.hexists.assert_called_once_with("hash1", "field1")

    @pytest.mark.asyncio
    async def test_hkeys(self, async_redis_client):
        """测试 hkeys 方法"""
        async_redis_client._mock_client.hkeys.return_value = ["field1", "field2"]

        result = await async_redis_client.hkeys("hash1")

        assert result == ["field1", "field2"]
        async_redis_client._mock_client.hkeys.assert_called_once_with("hash1")

    @pytest.mark.asyncio
    async def test_hvals(self, async_redis_client):
        """测试 hvals 方法"""
        async_redis_client._mock_client.hvals.return_value = ["value1", "value2"]

        result = await async_redis_client.hvals("hash1")

        assert result == ["value1", "value2"]
        async_redis_client._mock_client.hvals.assert_called_once_with("hash1")

    @pytest.mark.asyncio
    async def test_hlen(self, async_redis_client):
        """测试 hlen 方法"""
        async_redis_client._mock_client.hlen.return_value = 5

        result = await async_redis_client.hlen("hash1")

        assert result == 5
        async_redis_client._mock_client.hlen.assert_called_once_with("hash1")

    @pytest.mark.asyncio
    async def test_hmget(self, async_redis_client):
        """测试 hmget 方法"""
        async_redis_client._mock_client.hmget.return_value = ["value1", "value2"]

        result = await async_redis_client.hmget("hash1", "field1", "field2")

        assert result == ["value1", "value2"]
        async_redis_client._mock_client.hmget.assert_called_once_with("hash1", "field1", "field2")


class TestAsyncRedisListOperations:
    """测试列表操作"""

    @pytest.fixture
    def async_redis_client(self):
        """创建 mock 异步 Redis 客户端"""
        with patch("redis.asyncio.ConnectionPool"), patch("redis.asyncio.Redis") as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            client = AsyncRedis()
            client._mock_client = mock_client
            yield client

    @pytest.mark.asyncio
    async def test_lpush(self, async_redis_client):
        """测试 lpush 方法"""
        async_redis_client._mock_client.lpush.return_value = 1

        result = await async_redis_client.lpush("list1", "value1")

        assert result == 1
        async_redis_client._mock_client.lpush.assert_called_once_with("list1", "value1")

    @pytest.mark.asyncio
    async def test_rpush(self, async_redis_client):
        """测试 rpush 方法"""
        async_redis_client._mock_client.rpush.return_value = 2

        result = await async_redis_client.rpush("list1", "value1", "value2")

        assert result == 2
        async_redis_client._mock_client.rpush.assert_called_once_with("list1", "value1", "value2")

    @pytest.mark.asyncio
    async def test_lpop(self, async_redis_client):
        """测试 lpop 方法"""
        async_redis_client._mock_client.lpop.return_value = "value1"

        result = await async_redis_client.lpop("list1")

        assert result == "value1"
        async_redis_client._mock_client.lpop.assert_called_once_with("list1")

    @pytest.mark.asyncio
    async def test_rpop(self, async_redis_client):
        """测试 rpop 方法"""
        async_redis_client._mock_client.rpop.return_value = "value1"

        result = await async_redis_client.rpop("list1")

        assert result == "value1"
        async_redis_client._mock_client.rpop.assert_called_once_with("list1")

    @pytest.mark.asyncio
    async def test_lrange(self, async_redis_client):
        """测试 lrange 方法"""
        async_redis_client._mock_client.lrange.return_value = ["value1", "value2", "value3"]

        result = await async_redis_client.lrange("list1", 0, -1)

        assert result == ["value1", "value2", "value3"]
        async_redis_client._mock_client.lrange.assert_called_once_with("list1", 0, -1)

    @pytest.mark.asyncio
    async def test_llen(self, async_redis_client):
        """测试 llen 方法"""
        async_redis_client._mock_client.llen.return_value = 10

        result = await async_redis_client.llen("list1")

        assert result == 10
        async_redis_client._mock_client.llen.assert_called_once_with("list1")

    @pytest.mark.asyncio
    async def test_lindex(self, async_redis_client):
        """测试 lindex 方法"""
        async_redis_client._mock_client.lindex.return_value = "item"

        result = await async_redis_client.lindex("list1", 0)

        assert result == "item"
        async_redis_client._mock_client.lindex.assert_called_once_with("list1", 0)


class TestAsyncRedisSetOperations:
    """测试集合操作"""

    @pytest.fixture
    def async_redis_client(self):
        """创建 mock 异步 Redis 客户端"""
        with patch("redis.asyncio.ConnectionPool"), patch("redis.asyncio.Redis") as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            client = AsyncRedis()
            client._mock_client = mock_client
            yield client

    @pytest.mark.asyncio
    async def test_sadd(self, async_redis_client):
        """测试 sadd 方法"""
        async_redis_client._mock_client.sadd.return_value = 2

        result = await async_redis_client.sadd("set1", "value1", "value2")

        assert result == 2
        async_redis_client._mock_client.sadd.assert_called_once_with("set1", "value1", "value2")

    @pytest.mark.asyncio
    async def test_smembers(self, async_redis_client):
        """测试 smembers 方法"""
        async_redis_client._mock_client.smembers.return_value = {"value1", "value2"}

        result = await async_redis_client.smembers("set1")

        assert result == {"value1", "value2"}
        async_redis_client._mock_client.smembers.assert_called_once_with("set1")

    @pytest.mark.asyncio
    async def test_srem(self, async_redis_client):
        """测试 srem 方法"""
        async_redis_client._mock_client.srem.return_value = 1

        result = await async_redis_client.srem("set1", "value1")

        assert result == 1
        async_redis_client._mock_client.srem.assert_called_once_with("set1", "value1")

    @pytest.mark.asyncio
    async def test_sismember(self, async_redis_client):
        """测试 sismember 方法"""
        async_redis_client._mock_client.sismember.return_value = True

        result = await async_redis_client.sismember("set1", "value1")

        assert result is True
        async_redis_client._mock_client.sismember.assert_called_once_with("set1", "value1")

    @pytest.mark.asyncio
    async def test_scard(self, async_redis_client):
        """测试 scard 方法"""
        async_redis_client._mock_client.scard.return_value = 3

        result = await async_redis_client.scard("set1")

        assert result == 3
        async_redis_client._mock_client.scard.assert_called_once_with("set1")


class TestAsyncRedisSortedSetOperations:
    """测试有序集合操作"""

    @pytest.fixture
    def async_redis_client(self):
        """创建 mock 异步 Redis 客户端"""
        with patch("redis.asyncio.ConnectionPool"), patch("redis.asyncio.Redis") as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            client = AsyncRedis()
            client._mock_client = mock_client
            yield client

    @pytest.mark.asyncio
    async def test_zadd(self, async_redis_client):
        """测试 zadd 方法"""
        async_redis_client._mock_client.zadd.return_value = 2

        result = await async_redis_client.zadd("zset1", {"value1": 1.0, "value2": 2.0})

        assert result == 2
        async_redis_client._mock_client.zadd.assert_called_once_with(
            "zset1", {"value1": 1.0, "value2": 2.0}
        )

    @pytest.mark.asyncio
    async def test_zrange(self, async_redis_client):
        """测试 zrange 方法"""
        async_redis_client._mock_client.zrange.return_value = ["value1", "value2"]

        result = await async_redis_client.zrange("zset1", 0, -1)

        assert result == ["value1", "value2"]
        async_redis_client._mock_client.zrange.assert_called_once_with(
            "zset1", 0, -1, withscores=False
        )

    @pytest.mark.asyncio
    async def test_zrange_with_scores(self, async_redis_client):
        """测试带分数的 zrange"""
        async_redis_client._mock_client.zrange.return_value = [("value1", 1.0), ("value2", 2.0)]

        result = await async_redis_client.zrange("zset1", 0, -1, withscores=True)

        assert result == [("value1", 1.0), ("value2", 2.0)]
        async_redis_client._mock_client.zrange.assert_called_once_with(
            "zset1", 0, -1, withscores=True
        )

    @pytest.mark.asyncio
    async def test_zrevrange(self, async_redis_client):
        """测试 zrevrange 方法"""
        async_redis_client._mock_client.zrevrange.return_value = ["c", "b", "a"]

        result = await async_redis_client.zrevrange("zset1", 0, -1)

        assert result == ["c", "b", "a"]
        async_redis_client._mock_client.zrevrange.assert_called_once_with(
            "zset1", 0, -1, withscores=False
        )

    @pytest.mark.asyncio
    async def test_zscore(self, async_redis_client):
        """测试 zscore 方法"""
        async_redis_client._mock_client.zscore.return_value = 1.5

        result = await async_redis_client.zscore("zset1", "member")

        assert result == 1.5
        async_redis_client._mock_client.zscore.assert_called_once_with("zset1", "member")

    @pytest.mark.asyncio
    async def test_zcard(self, async_redis_client):
        """测试 zcard 方法"""
        async_redis_client._mock_client.zcard.return_value = 10

        result = await async_redis_client.zcard("zset1")

        assert result == 10
        async_redis_client._mock_client.zcard.assert_called_once_with("zset1")

    @pytest.mark.asyncio
    async def test_zrank(self, async_redis_client):
        """测试 zrank 方法"""
        async_redis_client._mock_client.zrank.return_value = 2

        result = await async_redis_client.zrank("zset1", "member")

        assert result == 2
        async_redis_client._mock_client.zrank.assert_called_once_with("zset1", "member")

    @pytest.mark.asyncio
    async def test_zrem(self, async_redis_client):
        """测试 zrem 方法"""
        async_redis_client._mock_client.zrem.return_value = 1

        result = await async_redis_client.zrem("zset1", "member")

        assert result == 1
        async_redis_client._mock_client.zrem.assert_called_once_with("zset1", "member")


class TestAsyncRedisGenericOperations:
    """测试通用操作"""

    @pytest.fixture
    def async_redis_client(self):
        """创建 mock 异步 Redis 客户端"""
        with patch("redis.asyncio.ConnectionPool"), patch("redis.asyncio.Redis") as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            client = AsyncRedis()
            client._mock_client = mock_client
            yield client

    @pytest.mark.asyncio
    async def test_keys_all(self, async_redis_client):
        """测试 keys 获取所有键"""
        async_redis_client._mock_client.keys.return_value = ["key1", "key2", "key3"]

        result = await async_redis_client.keys()

        assert result == ["key1", "key2", "key3"]
        async_redis_client._mock_client.keys.assert_called_once_with("*")

    @pytest.mark.asyncio
    async def test_keys_with_pattern(self, async_redis_client):
        """测试 keys 使用模式匹配"""
        async_redis_client._mock_client.keys.return_value = ["user:1", "user:2"]

        result = await async_redis_client.keys("user:*")

        assert result == ["user:1", "user:2"]
        async_redis_client._mock_client.keys.assert_called_once_with("user:*")

    @pytest.mark.asyncio
    async def test_scan(self, async_redis_client):
        """测试 scan 方法"""
        async_redis_client._mock_client.scan.return_value = (0, ["key1", "key2"])

        cursor, keys = await async_redis_client.scan(0)

        assert cursor == 0
        assert keys == ["key1", "key2"]
        async_redis_client._mock_client.scan.assert_called_once_with(
            cursor=0, match=None, count=None
        )

    @pytest.mark.asyncio
    async def test_scan_with_pattern(self, async_redis_client):
        """测试带模式的 scan"""
        async_redis_client._mock_client.scan.return_value = (5, ["user:1", "user:2"])

        cursor, keys = await async_redis_client.scan(0, match="user:*", count=50)

        assert cursor == 5
        assert keys == ["user:1", "user:2"]
        async_redis_client._mock_client.scan.assert_called_once_with(
            cursor=0, match="user:*", count=50
        )

    @pytest.mark.asyncio
    async def test_type(self, async_redis_client):
        """测试 type 方法"""
        async_redis_client._mock_client.type.return_value = "string"

        result = await async_redis_client.type("key")

        assert result == "string"
        async_redis_client._mock_client.type.assert_called_once_with("key")

    @pytest.mark.asyncio
    async def test_rename(self, async_redis_client):
        """测试 rename 方法"""
        async_redis_client._mock_client.rename.return_value = True

        result = await async_redis_client.rename("old_key", "new_key")

        assert result is True
        async_redis_client._mock_client.rename.assert_called_once_with("old_key", "new_key")

    @pytest.mark.asyncio
    async def test_flushdb(self, async_redis_client):
        """测试 flushdb 清空数据库"""
        async_redis_client._mock_client.flushdb.return_value = True

        result = await async_redis_client.flushdb()

        assert result is True
        async_redis_client._mock_client.flushdb.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self, async_redis_client):
        """测试 close 关闭连接"""
        await async_redis_client.close()

        async_redis_client._mock_client.aclose.assert_called_once()


# =============================================================================
# EventBus 集成测试 (v4.0.0)
# =============================================================================


class TestAsyncRedisEventBusIntegration:
    """测试异步 Redis 客户端 EventBus 事件发布"""

    @pytest.fixture
    def event_bus_and_events(self):
        """创建事件总线和事件收集器"""
        event_bus = EventBus()
        collected_events = []

        # 订阅所有缓存事件
        async def collect_event(event):
            collected_events.append(event)

        event_bus.subscribe(CacheOperationStartEvent, collect_event)
        event_bus.subscribe(CacheOperationEndEvent, collect_event)
        event_bus.subscribe(CacheOperationErrorEvent, collect_event)

        return event_bus, collected_events

    @pytest.fixture
    def async_redis_with_eventbus(self, event_bus_and_events):
        """创建带 EventBus 的异步 Redis 客户端"""
        from df_test_framework.bootstrap import ProviderRegistry, RuntimeContext
        from df_test_framework.infrastructure.config import FrameworkSettings
        from df_test_framework.infrastructure.logging import logger

        event_bus, _ = event_bus_and_events

        # 创建 RuntimeContext
        runtime = RuntimeContext(
            settings=FrameworkSettings(app_name="test"),
            logger=logger,
            providers=ProviderRegistry(providers={}),
            event_bus=event_bus,
        )

        with patch("redis.asyncio.ConnectionPool"), patch("redis.asyncio.Redis") as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            client = AsyncRedis(runtime=runtime)
            client._mock_client = mock_client
            yield client

    @pytest.mark.asyncio
    async def test_set_publishes_events(self, async_redis_with_eventbus, event_bus_and_events):
        """测试 set 操作发布开始和结束事件"""
        import asyncio

        _, collected_events = event_bus_and_events
        async_redis_with_eventbus._mock_client.set.return_value = True

        await async_redis_with_eventbus.set("test_key", "test_value")

        # 等待事件循环处理 pending 任务
        await asyncio.sleep(0)

        # 验证发布了开始和结束事件
        assert len(collected_events) == 2

        start_event = collected_events[0]
        end_event = collected_events[1]

        assert isinstance(start_event, CacheOperationStartEvent)
        assert start_event.operation == "SET"
        assert start_event.key == "test_key"

        assert isinstance(end_event, CacheOperationEndEvent)
        assert end_event.operation == "SET"
        assert end_event.key == "test_key"
        assert end_event.success is True

        # 验证 correlation_id 关联
        assert start_event.correlation_id == end_event.correlation_id

    @pytest.mark.asyncio
    async def test_get_hit_publishes_events(self, async_redis_with_eventbus, event_bus_and_events):
        """测试 get 命中发布事件（hit=True）"""
        import asyncio

        _, collected_events = event_bus_and_events
        async_redis_with_eventbus._mock_client.get.return_value = "cached_value"

        result = await async_redis_with_eventbus.get("hit_key")

        # 等待事件循环处理 pending 任务
        await asyncio.sleep(0)

        assert result == "cached_value"
        assert len(collected_events) == 2

        end_event = collected_events[1]
        assert isinstance(end_event, CacheOperationEndEvent)
        assert end_event.hit is True

    @pytest.mark.asyncio
    async def test_get_miss_publishes_events(self, async_redis_with_eventbus, event_bus_and_events):
        """测试 get 未命中发布事件（hit=False）"""
        import asyncio

        _, collected_events = event_bus_and_events
        async_redis_with_eventbus._mock_client.get.return_value = None

        result = await async_redis_with_eventbus.get("miss_key")

        # 等待事件循环处理 pending 任务
        await asyncio.sleep(0)

        assert result is None
        assert len(collected_events) == 2

        end_event = collected_events[1]
        assert isinstance(end_event, CacheOperationEndEvent)
        assert end_event.hit is False

    @pytest.mark.asyncio
    async def test_error_publishes_error_event(
        self, async_redis_with_eventbus, event_bus_and_events
    ):
        """测试操作失败发布错误事件"""
        import asyncio

        _, collected_events = event_bus_and_events
        async_redis_with_eventbus._mock_client.get.side_effect = Exception("Redis connection error")

        with pytest.raises(Exception, match="Redis connection error"):
            await async_redis_with_eventbus.get("error_key")

        # 等待事件循环处理 pending 任务
        await asyncio.sleep(0)

        # 应该有开始事件和错误事件
        assert len(collected_events) == 2

        start_event = collected_events[0]
        error_event = collected_events[1]

        assert isinstance(start_event, CacheOperationStartEvent)
        assert isinstance(error_event, CacheOperationErrorEvent)
        assert error_event.operation == "GET"
        assert error_event.key == "error_key"
        assert error_event.error_type == "Exception"
        assert "Redis connection error" in error_event.error_message

        # 验证 correlation_id 关联
        assert start_event.correlation_id == error_event.correlation_id

    @pytest.mark.asyncio
    async def test_no_events_without_eventbus(self):
        """测试没有 EventBus 时不发布事件"""
        with patch("redis.asyncio.ConnectionPool"), patch("redis.asyncio.Redis") as mock_redis:
            mock_client = AsyncMock()
            mock_client.get.return_value = "value"
            mock_redis.return_value = mock_client

            # 不传入 runtime
            client = AsyncRedis()
            result = await client.get("key")

            assert result == "value"
            # 不应该抛出异常
