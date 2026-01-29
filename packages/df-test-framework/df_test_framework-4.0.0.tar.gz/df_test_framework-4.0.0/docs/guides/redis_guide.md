# Redis 使用指南

> **最后更新**: 2026-01-17
> **适用版本**: v3.0.0+（同步 RedisClient），v4.0.0+（异步 AsyncRedis，推荐）

## 概述

DF Test Framework 提供了完整的 Redis 缓存支持，包括同步和异步两种客户端：

- **RedisClient**: 同步 Redis 客户端，适用于简单场景
- **AsyncRedis**: 异步 Redis 客户端（v4.0.0 新增），支持高并发操作，性能提升 5-10 倍

### 核心特性

- ✅ **完整的数据类型支持**: String、Hash、List、Set、Sorted Set
- ✅ **连接池管理**: 自动管理连接池，支持高并发
- ✅ **事件驱动**: 自动发布 EventBus 事件，集成 Allure 报告
- ✅ **可观测性**: 内置日志记录，支持性能监控
- ✅ **异步支持**: v4.0.0 全面异步化，支持并发缓存操作

### 性能对比

| 操作类型 | 同步 RedisClient | 异步 AsyncRedis | 性能提升 |
|---------|-----------------|----------------|---------|
| 单次操作 | ~1-2ms | ~1-2ms | 持平 |
| 100次串行操作 | ~100-200ms | ~100-200ms | 持平 |
| 100次并发操作 | ~100-200ms | ~10-20ms | **5-10倍** |

---

## 快速开始

### 1. 配置 Redis 连接

在配置文件中添加 Redis 连接信息：

```yaml
# config/default.yaml
redis:
  host: localhost
  port: 6379
  db: 0
  password: null  # 如果有密码
  max_connections: 50
```

### 2. 同步客户端使用

```python
from df_test_framework import Bootstrap

# 初始化框架
app = Bootstrap().build()
runtime = app.run()

# 获取 Redis 客户端
redis = runtime.redis_client()

# 基础操作
redis.set("key", "value", ex=3600)  # 设置键值，1小时过期
value = redis.get("key")            # 获取值
redis.delete("key")                 # 删除键
```

### 3. 异步客户端使用（v4.0.0）

```python
import asyncio
from df_test_framework import Bootstrap

async def main():
    # 初始化框架
    app = Bootstrap().build()
    runtime = app.run()

    # 获取异步 Redis 客户端
    async_redis = runtime.async_redis()

    # 异步操作（需要 await）
    await async_redis.set("key", "value", ex=3600)
    value = await async_redis.get("key")
    await async_redis.delete("key")

    # 关闭连接
    await async_redis.close()

# 运行异步代码
asyncio.run(main())
```

### 4. 在 pytest 中使用

```python
import pytest

def test_redis_cache(redis_client):
    """使用 redis_client fixture"""
    # 设置缓存
    redis_client.set("test_key", "test_value")

    # 验证缓存
    value = redis_client.get("test_key")
    assert value == "test_value"

    # 清理
    redis_client.delete("test_key")

@pytest.mark.asyncio
async def test_async_redis_cache(async_redis):
    """使用 async_redis fixture"""
    # 异步操作
    await async_redis.set("test_key", "test_value")
    value = await async_redis.get("test_key")
    assert value == "test_value"

    # 清理
    await async_redis.delete("test_key")
```

---

## 基础操作

### 字符串操作（String）

字符串是 Redis 最基本的数据类型，适用于缓存简单值。

#### 设置和获取

```python
# 同步方式
redis.set("username", "张三")
username = redis.get("username")  # "张三"

# 异步方式
await async_redis.set("username", "张三")
username = await async_redis.get("username")
```

#### 设置过期时间

```python
# 设置键值，60秒后过期
redis.set("session_token", "abc123", ex=60)

# 查看剩余时间
ttl = redis.ttl("session_token")  # 返回剩余秒数
# -1: 永久有效
# -2: 键不存在
```

#### 仅在键不存在时设置（NX）

```python
# 仅在键不存在时设置（分布式锁场景）
success = redis.set("lock:resource", "locked", ex=10, nx=True)
if success:
    print("获取锁成功")
else:
    print("锁已被占用")
```

#### 自增/自减

```python
# 计数器场景
redis.set("page_views", "0")
redis.incr("page_views")        # 自增1，返回 1
redis.incr("page_views", 10)    # 自增10，返回 11
redis.decr("page_views", 5)     # 自减5，返回 6
```

#### 批量操作（仅异步）

```python
# 批量设置
await async_redis.mset({
    "user:1:name": "张三",
    "user:2:name": "李四",
    "user:3:name": "王五"
})

# 批量获取
values = await async_redis.mget("user:1:name", "user:2:name", "user:3:name")
# ["张三", "李四", "王五"]
```

### 存储 JSON 数据

Redis 字符串可以存储 JSON 数据：

```python
import json

# 存储 JSON
user_data = {
    "id": 1,
    "name": "张三",
    "email": "zhangsan@example.com"
}
redis.set("user:1", json.dumps(user_data), ex=3600)

# 读取 JSON
stored_data = redis.get("user:1")
user = json.loads(stored_data)
print(user["name"])  # "张三"
```

### 键管理

```python
# 检查键是否存在
exists = redis.exists("key1", "key2")  # 返回存在的键数量

# 删除键
deleted = redis.delete("key1", "key2", "key3")  # 返回删除的键数量

# 重命名键
redis.rename("old_key", "new_key")

# 获取键的类型
key_type = redis.type("my_key")  # "string", "list", "set", "zset", "hash", "none"

# 查找键（生产环境慎用，性能差）
keys = redis.keys("user:*")  # 返回匹配的键列表

# 增量迭代键（推荐，性能好）
cursor, keys = redis.scan(cursor=0, match="user:*", count=100)
```

---

## 高级数据类型

### Hash 操作

Hash 适用于存储对象，每个 Hash 可以存储多个字段。

#### 基础操作

```python
# 设置 Hash 字段
redis.hset("product:1", "name", "笔记本电脑")
redis.hset("product:1", "price", "5999.00")
redis.hset("product:1", "stock", "100")

# 获取 Hash 字段
name = redis.hget("product:1", "name")      # "笔记本电脑"
price = redis.hget("product:1", "price")    # "5999.00"

# 获取所有字段
product = redis.hgetall("product:1")
# {"name": "笔记本电脑", "price": "5999.00", "stock": "100"}

# 检查字段是否存在
exists = redis.hexists("product:1", "name")  # True

# 删除字段
redis.hdel("product:1", "stock")

# 获取所有字段名
fields = redis.hkeys("product:1")  # ["name", "price"]

# 获取所有字段值
values = redis.hvals("product:1")  # ["笔记本电脑", "5999.00"]

# 获取字段数量
count = redis.hlen("product:1")  # 2
```

#### 批量操作（仅异步）

```python
# 批量设置 Hash 字段
await async_redis.hmset("user:1", {
    "name": "张三",
    "age": "30",
    "email": "zhangsan@example.com"
})

# 批量获取 Hash 字段
values = await async_redis.hmget("user:1", "name", "age", "email")
# ["张三", "30", "zhangsan@example.com"]
```

#### 使用场景

```python
# 场景1: 存储用户信息
redis.hset("user:1001", "name", "张三")
redis.hset("user:1001", "email", "zhangsan@example.com")
redis.hset("user:1001", "login_count", "0")

# 场景2: 购物车（用户ID为Hash名，商品ID为字段）
redis.hset("cart:user123", "product_1", "2")  # 商品1，数量2
redis.hset("cart:user123", "product_2", "1")  # 商品2，数量1
cart = redis.hgetall("cart:user123")
```

### List 操作

List 是有序列表，适用于队列、栈、时间线等场景。

#### 基础操作

```python
# 从左侧推入（头部）
redis.lpush("tasks", "任务1")
redis.lpush("tasks", "任务2")  # ["任务2", "任务1"]

# 从右侧推入（尾部）
redis.rpush("tasks", "任务3")  # ["任务2", "任务1", "任务3"]

# 从左侧弹出
task = redis.lpop("tasks")  # "任务2"

# 从右侧弹出
task = redis.rpop("tasks")  # "任务3"

# 获取列表长度
length = redis.llen("tasks")  # 1

# 获取范围元素
tasks = redis.lrange("tasks", 0, -1)  # 获取所有元素
tasks = redis.lrange("tasks", 0, 9)   # 获取前10个元素

# 获取指定索引的元素
task = redis.lindex("tasks", 0)  # 获取第一个元素
```

#### 使用场景

```python
# 场景1: FIFO 队列（先进先出）
redis.rpush("task_queue", "任务1")  # 从右侧推入
redis.rpush("task_queue", "任务2")
task = redis.lpop("task_queue")     # 从左侧弹出，"任务1"

# 场景2: LIFO 栈（后进先出）
redis.lpush("history", "页面1")  # 从左侧推入
redis.lpush("history", "页面2")
page = redis.lpop("history")     # 从左侧弹出，"页面2"

# 场景3: 最新消息列表（保留最新100条）
redis.lpush("messages", "新消息")
redis.ltrim("messages", 0, 99)  # 只保留前100条
```

### Set 操作

Set 是无序集合，适用于去重、标签、关系等场景。

#### 基础操作

```python
# 添加成员
redis.sadd("tags", "Python", "Redis", "测试")

# 获取所有成员
tags = redis.smembers("tags")  # {"Python", "Redis", "测试"}

# 检查成员是否存在
exists = redis.sismember("tags", "Python")  # True

# 移除成员
redis.srem("tags", "测试")

# 获取集合大小
count = redis.scard("tags")  # 2
```

#### 使用场景

```python
# 场景1: 用户标签
redis.sadd("user:1001:tags", "VIP", "活跃用户", "技术爱好者")

# 场景2: 点赞用户（去重）
redis.sadd("post:123:likes", "user_1", "user_2", "user_3")
like_count = redis.scard("post:123:likes")

# 场景3: 在线用户
redis.sadd("online_users", "user_1", "user_2")
is_online = redis.sismember("online_users", "user_1")
```

### Sorted Set 操作

Sorted Set 是有序集合，每个成员关联一个分数，适用于排行榜、优先队列等场景。

#### 基础操作

```python
# 添加成员（member: score）
redis.zadd("leaderboard", {"张三": 100, "李四": 95, "王五": 98})

# 获取排名范围（按分数升序）
top3 = redis.zrange("leaderboard", 0, 2, withscores=True)
# [("李四", 95.0), ("王五", 98.0), ("张三", 100.0)]

# 获取排名范围（按分数降序）
top3_desc = redis.zrevrange("leaderboard", 0, 2, withscores=True)
# [("张三", 100.0), ("王五", 98.0), ("李四", 95.0)]

# 获取成员分数
score = redis.zscore("leaderboard", "张三")  # 100.0

# 获取成员排名（从0开始）
rank = redis.zrank("leaderboard", "张三")  # 2（升序排名）

# 移除成员
redis.zrem("leaderboard", "李四")

# 获取集合大小
count = redis.zcard("leaderboard")  # 2
```

#### 使用场景

```python
# 场景1: 游戏排行榜
redis.zadd("game:scores", {"player1": 1000, "player2": 1500, "player3": 1200})
top10 = redis.zrevrange("game:scores", 0, 9, withscores=True)

# 场景2: 延迟队列（按时间戳排序）
import time
redis.zadd("delayed_tasks", {
    "task1": time.time() + 60,   # 60秒后执行
    "task2": time.time() + 120,  # 120秒后执行
})

# 场景3: 热门文章（按浏览量排序）
redis.zadd("hot_articles", {"article_1": 1000, "article_2": 1500})
```

---

## 并发操作（异步）

异步 Redis 的最大优势是支持高并发操作，性能提升显著。

### 并发读取

```python
import asyncio

async def batch_get_users():
    """并发获取多个用户信息"""
    async_redis = runtime.async_redis()

    # 创建100个并发任务
    tasks = [
        async_redis.get(f"user:{i}")
        for i in range(1, 101)
    ]

    # 并发执行（性能提升 5-10 倍）
    results = await asyncio.gather(*tasks)

    return results

# 性能对比：
# 同步方式：100次 * 2ms = 200ms
# 异步并发：~20ms（提升 10 倍）
```

### 并发写入

```python
async def batch_set_cache():
    """并发设置多个缓存"""
    async_redis = runtime.async_redis()

    # 创建批量写入任务
    tasks = [
        async_redis.set(f"cache:{i}", f"value_{i}", ex=3600)
        for i in range(1, 101)
    ]

    # 并发执行
    results = await asyncio.gather(*tasks)

    return results
```

### 混合操作

```python
async def complex_cache_operations():
    """复杂的缓存操作"""
    async_redis = runtime.async_redis()

    # 并发执行不同类型的操作
    results = await asyncio.gather(
        async_redis.get("user:1"),
        async_redis.hgetall("product:1"),
        async_redis.lrange("tasks", 0, 10),
        async_redis.smembers("tags"),
        async_redis.zrevrange("leaderboard", 0, 9),
    )

    user, product, tasks, tags, leaderboard = results
    return {
        "user": user,
        "product": product,
        "tasks": tasks,
        "tags": tags,
        "leaderboard": leaderboard
    }
```

---

## 常见场景

### 缓存模式（Cache-Aside）

最常用的缓存模式，先查缓存，未命中再查数据库。

```python
import json

def get_user_with_cache(user_id: int):
    """带缓存的用户查询（同步）"""
    cache_key = f"user:{user_id}"

    # 1. 先查缓存
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # 2. 缓存未命中，查数据库
    user = database.query(f"SELECT * FROM users WHERE id = {user_id}")

    # 3. 写入缓存（5分钟过期）
    redis.set(cache_key, json.dumps(user), ex=300)

    return user

async def get_user_with_cache_async(user_id: int):
    """带缓存的用户查询（异步）"""
    cache_key = f"user:{user_id}"

    # 1. 先查缓存
    cached = await async_redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # 2. 缓存未命中，查数据库
    user = await async_database.query(f"SELECT * FROM users WHERE id = {user_id}")

    # 3. 写入缓存
    await async_redis.set(cache_key, json.dumps(user), ex=300)

    return user
```

### 分布式锁

使用 Redis 实现简单的分布式锁。

```python
import time
import uuid

def acquire_lock(lock_key: str, timeout: int = 10) -> str | None:
    """获取分布式锁"""
    lock_value = str(uuid.uuid4())

    # 使用 NX 参数确保原子性
    success = redis.set(lock_key, lock_value, ex=timeout, nx=True)

    if success:
        return lock_value
    return None

def release_lock(lock_key: str, lock_value: str) -> bool:
    """释放分布式锁"""
    # 检查锁是否属于当前持有者
    current_value = redis.get(lock_key)
    if current_value == lock_value:
        redis.delete(lock_key)
        return True
    return False

# 使用示例
lock_value = acquire_lock("resource:lock")
if lock_value:
    try:
        # 执行业务逻辑
        print("获取锁成功，执行业务")
    finally:
        release_lock("resource:lock", lock_value)
else:
    print("获取锁失败")
```

### 限流器（令牌桶）

使用 Redis 实现简单的限流器。

```python
def rate_limit(user_id: int, max_requests: int = 10, window: int = 60) -> bool:
    """限流检查（每分钟最多10次请求）"""
    key = f"rate_limit:{user_id}"

    # 获取当前计数
    current = redis.get(key)

    if current is None:
        # 首次请求，设置计数为1
        redis.set(key, "1", ex=window)
        return True

    if int(current) < max_requests:
        # 未超限，计数+1
        redis.incr(key)
        return True

    # 超限
    return False

# 使用示例
if rate_limit(user_id=1001):
    print("请求通过")
else:
    print("请求被限流")
```

### 会话管理

使用 Redis 存储用户会话。

```python
import json

def create_session(user_id: int, session_data: dict) -> str:
    """创建会话"""
    session_id = str(uuid.uuid4())
    session_key = f"session:{session_id}"

    # 存储会话数据（30分钟过期）
    redis.set(session_key, json.dumps(session_data), ex=1800)

    return session_id

def get_session(session_id: str) -> dict | None:
    """获取会话"""
    session_key = f"session:{session_id}"
    data = redis.get(session_key)

    if data:
        # 刷新过期时间
        redis.expire(session_key, 1800)
        return json.loads(data)

    return None

def delete_session(session_id: str):
    """删除会话（登出）"""
    session_key = f"session:{session_id}"
    redis.delete(session_key)
```

---

## 最佳实践

### 1. 键命名规范

使用清晰的命名规范，便于管理和维护。

```python
# ✅ 推荐：使用冒号分隔，层次清晰
"user:1001:profile"
"product:123:stock"
"cache:api:user:1001"

# ❌ 不推荐：命名不清晰
"u1001"
"p123s"
"cache_user_1001"
```

### 2. 设置合理的过期时间

避免内存溢出，确保缓存及时更新。

```python
# 短期缓存（5分钟）
redis.set("session:token", token, ex=300)

# 中期缓存（1小时）
redis.set("user:profile", profile, ex=3600)

# 长期缓存（24小时）
redis.set("config:settings", settings, ex=86400)
```

### 3. 使用连接池

框架已自动配置连接池，无需手动管理。

```python
# ✅ 框架自动管理连接池
redis = runtime.redis_client()  # 复用连接池

# ❌ 不要每次创建新客户端
# redis = RedisClient()  # 错误：每次创建新连接
```

### 4. 异步优先（v4.0.0+）

对于高并发场景，优先使用异步客户端。

```python
# ✅ 推荐：异步并发（性能提升 5-10 倍）
async def batch_operations():
    tasks = [async_redis.get(f"key:{i}") for i in range(100)]
    results = await asyncio.gather(*tasks)

# ⚠️ 同步串行（性能较低）
def batch_operations_sync():
    results = [redis.get(f"key:{i}") for i in range(100)]
```

### 5. 避免大键

大键会影响性能，建议拆分。

```python
# ❌ 不推荐：单个 Hash 存储大量字段
redis.hset("all_users", "user_1", data1)
redis.hset("all_users", "user_2", data2)
# ... 10000 个字段

# ✅ 推荐：分散存储
redis.set("user:1", data1)
redis.set("user:2", data2)
```

### 6. 使用 Pipeline（批量操作）

对于大量操作，使用 Pipeline 减少网络往返。

```python
# 注意：框架暂未封装 Pipeline，可直接使用底层客户端
pipe = redis.client.pipeline()
for i in range(100):
    pipe.set(f"key:{i}", f"value_{i}")
pipe.execute()
```

### 7. 监控和告警

利用框架的可观测性功能监控 Redis 性能。

```python
# 框架自动记录 Redis 操作日志
# 查看日志：logs/redis.log

# Allure 报告自动记录缓存操作
# 包括：操作类型、耗时、命中率等
```

---

## 注意事项

### 1. 数据持久化

Redis 主要用于缓存，不应作为主数据存储。

- ✅ 缓存数据库查询结果
- ✅ 存储临时会话数据
- ❌ 不要存储关键业务数据（应存储在数据库）

### 2. 内存管理

Redis 是内存数据库，注意内存使用。

```python
# 设置过期时间，避免内存泄漏
redis.set("key", "value", ex=3600)  # ✅ 有过期时间

# 定期清理测试数据
redis.flushdb()  # ⚠️ 仅在测试环境使用
```

### 3. 键冲突

避免不同模块使用相同的键名。

```python
# ✅ 使用模块前缀
"auth:session:123"
"cart:user:456"

# ❌ 可能冲突
"session:123"
"user:456"
```

### 4. 异步上下文

异步客户端必须在异步函数中使用。

```python
# ✅ 正确
async def test_async():
    await async_redis.get("key")

# ❌ 错误：在同步函数中使用异步客户端
def test_sync():
    await async_redis.get("key")  # SyntaxError
```

### 5. 连接关闭

测试结束后，框架会自动关闭连接。

```python
# 框架自动管理，无需手动关闭
# 如需手动关闭：
redis.close()
await async_redis.close()
```

---

## 相关文档

- [数据库使用指南](database_guide.md) - Database 和 AsyncDatabase
- [HTTP 客户端指南](http_client_guide.md) - HttpClient 和 AsyncHttpClient
- [Web UI 测试指南](web-ui-testing.md) - UI 自动化测试
- [配置系统指南](config_guide.md) - 配置管理

---

## 版本历史

### v4.0.0（2026-01-17）
- ✅ 新增 AsyncRedis 异步客户端
- ✅ 支持并发缓存操作，性能提升 5-10 倍
- ✅ 新增批量操作（mget/mset、hmget/hmset）
- ✅ 完全向后兼容同步 RedisClient

### v3.17.1（2025-12-XX）
- ✅ 集成 EventBus 事件发布
- ✅ 完善 Allure 报告集成
- ✅ 统一操作执行包装器

### v3.0.0（2025-XX-XX）
- ✅ 首次引入 RedisClient
- ✅ 支持基础数据类型操作
- ✅ 连接池管理

---

**完成时间**: 2026-01-17

