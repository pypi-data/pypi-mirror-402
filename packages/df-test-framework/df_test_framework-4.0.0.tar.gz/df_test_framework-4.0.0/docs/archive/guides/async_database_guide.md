# AsyncDatabase 使用指南

> **框架版本**: v4.0.0
> **更新日期**: 2026-01-16
> **最低版本要求**: v4.0.0+

## 概述

`AsyncDatabase` 是 v4.0.0 新增的全异步数据库客户端，基于 SQLAlchemy 2.0 AsyncEngine 实现。在并发数据库操作场景下，性能提升可达 **5-10 倍**。

## 核心优势

| 特性 | AsyncDatabase | Database |
|------|--------------|----------|
| **性能** | ⚡ 并发50查询 2秒 | 10秒 |
| **并发支持** | ✅ 原生支持 | ❌ 不支持 |
| **语法** | `await db.query_all()` | `db.query_all()` |
| **适用场景** | 并发数据操作 | 普通测试 |
| **驱动** | aiomysql/asyncpg | pymysql/psycopg2 |

## 快速开始

### 1. 配置数据库

```yaml
# .env
DB__HOST=localhost
DB__PORT=3306
DB__NAME=test_db
DB__USER=root
DB__PASSWORD=password

# 框架自动转换驱动：
# mysql+pymysql → mysql+aiomysql ✅
# postgresql+psycopg2 → postgresql+asyncpg ✅
# sqlite → sqlite+aiosqlite ✅
```

### 2. 基础使用

```python
import pytest

@pytest.mark.asyncio
async def test_basic_query(async_database):
    """基础查询示例"""
    # 查询所有用户
    users = await async_database.query_all(
        "SELECT * FROM users WHERE age > :age",
        {"age": 18}
    )

    assert len(users) > 0
    assert all(u["age"] > 18 for u in users)
```

### 3. 完整 CRUD 示例

```python
import pytest

@pytest.mark.asyncio
async def test_user_crud(async_database):
    """用户 CRUD 完整示例"""

    # CREATE - 插入数据
    user_id = await async_database.insert(
        "users",
        {
            "name": "Alice",
            "email": "alice@example.com",
            "age": 25
        }
    )
    assert user_id > 0

    # READ - 查询单条
    user = await async_database.query_one(
        "SELECT * FROM users WHERE id = :id",
        {"id": user_id}
    )
    assert user["name"] == "Alice"

    # UPDATE - 更新数据
    rows_affected = await async_database.update(
        "users",
        {"age": 26},
        {"id": user_id}
    )
    assert rows_affected == 1

    # 验证更新
    updated_user = await async_database.query_one(
        "SELECT * FROM users WHERE id = :id",
        {"id": user_id}
    )
    assert updated_user["age"] == 26

    # DELETE - 删除数据
    rows_deleted = await async_database.delete(
        "users",
        {"id": user_id}
    )
    assert rows_deleted == 1
```

## 核心功能

### 1. 查询操作

#### query_all - 查询多条记录

```python
@pytest.mark.asyncio
async def test_query_all(async_database):
    """查询多条记录"""

    # 基础查询
    users = await async_database.query_all("SELECT * FROM users")

    # 带参数查询
    adult_users = await async_database.query_all(
        "SELECT * FROM users WHERE age >= :min_age",
        {"min_age": 18}
    )

    # 复杂查询
    results = await async_database.query_all("""
        SELECT u.*, COUNT(o.id) as order_count
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        WHERE u.status = :status
        GROUP BY u.id
        ORDER BY order_count DESC
        LIMIT :limit
    """, {
        "status": "active",
        "limit": 10
    })
```

#### query_one - 查询单条记录

```python
@pytest.mark.asyncio
async def test_query_one(async_database):
    """查询单条记录"""

    # 查询单个用户
    user = await async_database.query_one(
        "SELECT * FROM users WHERE email = :email",
        {"email": "alice@example.com"}
    )

    assert user is not None
    assert user["email"] == "alice@example.com"

    # 查询不存在的记录（返回 None）
    missing_user = await async_database.query_one(
        "SELECT * FROM users WHERE id = :id",
        {"id": 99999}
    )
    assert missing_user is None
```

### 2. 插入操作

```python
@pytest.mark.asyncio
async def test_insert(async_database):
    """插入数据"""

    # 单条插入
    user_id = await async_database.insert(
        "users",
        {
            "name": "Bob",
            "email": "bob@example.com",
            "age": 30
        }
    )

    # 返回自增ID
    assert isinstance(user_id, int)
    assert user_id > 0

    # 验证插入成功
    user = await async_database.query_one(
        "SELECT * FROM users WHERE id = :id",
        {"id": user_id}
    )
    assert user["name"] == "Bob"
```

### 3. 更新操作

```python
@pytest.mark.asyncio
async def test_update(async_database):
    """更新数据"""

    # 创建测试数据
    user_id = await async_database.insert(
        "users",
        {"name": "Charlie", "email": "charlie@example.com", "age": 25}
    )

    # 单条更新
    rows_affected = await async_database.update(
        "users",
        {"age": 26, "email": "charlie.updated@example.com"},
        {"id": user_id}
    )
    assert rows_affected == 1

    # 批量更新
    rows_affected = await async_database.update(
        "users",
        {"status": "inactive"},
        {"age__lt": 18}  # age < 18
    )
    print(f"更新了 {rows_affected} 条记录")
```

### 4. 删除操作

```python
@pytest.mark.asyncio
async def test_delete(async_database):
    """删除数据"""

    # 创建测试数据
    user_id = await async_database.insert(
        "users",
        {"name": "Dave", "email": "dave@example.com", "age": 25}
    )

    # 单条删除
    rows_deleted = await async_database.delete(
        "users",
        {"id": user_id}
    )
    assert rows_deleted == 1

    # 验证删除成功
    user = await async_database.query_one(
        "SELECT * FROM users WHERE id = :id",
        {"id": user_id}
    )
    assert user is None

    # 批量删除
    rows_deleted = await async_database.delete(
        "users",
        {"status": "inactive"}
    )
    print(f"删除了 {rows_deleted} 条记录")
```

### 5. 执行原生 SQL

```python
@pytest.mark.asyncio
async def test_execute(async_database):
    """执行原生 SQL"""

    # DDL 操作
    await async_database.execute("""
        CREATE TABLE IF NOT EXISTS temp_table (
            id INT PRIMARY KEY AUTO_INCREMENT,
            data VARCHAR(255)
        )
    """)

    # DML 操作
    result = await async_database.execute(
        "INSERT INTO temp_table (data) VALUES (:data)",
        {"data": "test"}
    )

    # 清理
    await async_database.execute("DROP TABLE temp_table")
```

### 6. 事务管理

```python
@pytest.mark.asyncio
async def test_transaction(async_database):
    """使用事务"""

    async with async_database.session() as session:
        # 开始事务
        async with session.begin():
            # 操作1：插入用户
            result1 = await session.execute(
                "INSERT INTO users (name, email) VALUES (:name, :email)",
                {"name": "Eve", "email": "eve@example.com"}
            )

            # 操作2：插入订单
            result2 = await session.execute(
                "INSERT INTO orders (user_id, total) VALUES (:user_id, :total)",
                {"user_id": result1.lastrowid, "total": 100}
            )

            # 如果任何操作失败，整个事务回滚
            # 如果成功，事务自动提交
```

## 高级用法

### 1. 并发查询（性能提升 5-10 倍）

```python
import asyncio
import pytest

@pytest.mark.asyncio
async def test_concurrent_queries(async_database):
    """并发执行多个查询"""

    # 准备查询任务
    tasks = [
        async_database.query_one(
            "SELECT * FROM users WHERE id = :id",
            {"id": i}
        )
        for i in range(1, 51)
    ]

    # 并发执行（性能提升 5-10 倍）
    users = await asyncio.gather(*tasks)

    # 验证结果
    assert len(users) == 50
    assert all(u is not None for u in users)
```

### 2. 并发插入

```python
import asyncio
import pytest

@pytest.mark.asyncio
async def test_concurrent_inserts(async_database):
    """并发插入数据"""

    # 准备插入任务
    tasks = [
        async_database.insert(
            "users",
            {
                "name": f"User{i}",
                "email": f"user{i}@example.com",
                "age": 20 + (i % 30)
            }
        )
        for i in range(100)
    ]

    # 并发执行
    user_ids = await asyncio.gather(*tasks)

    # 验证结果
    assert len(user_ids) == 100
    assert all(isinstance(uid, int) for uid in user_ids)
```

### 3. 批量操作优化

```python
@pytest.mark.asyncio
async def test_batch_operations(async_database):
    """批量操作优化"""

    # 批量插入（使用事务）
    async with async_database.session() as session:
        async with session.begin():
            for i in range(1000):
                await session.execute(
                    "INSERT INTO users (name, email) VALUES (:name, :email)",
                    {"name": f"User{i}", "email": f"user{i}@example.com"}
                )

    # 批量更新
    await async_database.execute(
        "UPDATE users SET status = :status WHERE age > :age",
        {"status": "adult", "age": 18}
    )

    # 批量删除
    await async_database.execute(
        "DELETE FROM users WHERE status = :status",
        {"status": "inactive"}
    )
```

### 4. 复杂查询 + Pydantic 模型

```python
from pydantic import BaseModel
import pytest

class User(BaseModel):
    id: int
    name: str
    email: str
    age: int

@pytest.mark.asyncio
async def test_pydantic_integration(async_database):
    """与 Pydantic 模型集成"""

    # 查询数据
    rows = await async_database.query_all(
        "SELECT * FROM users WHERE age > :age",
        {"age": 18}
    )

    # 转换为 Pydantic 模型
    users = [User(**row) for row in rows]

    # 使用 Pydantic 验证和类型提示
    assert all(isinstance(u, User) for u in users)
    assert all(u.age > 18 for u in users)
```

## Fixture 使用

### async_database fixture

框架提供 `async_database` fixture：

```python
@pytest.mark.asyncio
async def test_with_fixture(async_database):
    """使用 async_database fixture"""

    # fixture 自动处理：
    # - 数据库连接配置
    # - 连接池管理
    # - EventBus 事件发布
    # - 资源清理

    users = await async_database.query_all("SELECT * FROM users")
    assert isinstance(users, list)
```

### 自定义 Repository（推荐）

创建数据访问层封装：

```python
# repositories/user_repository.py
from df_test_framework.capabilities.databases import AsyncDatabase

class AsyncUserRepository:
    def __init__(self, db: AsyncDatabase):
        self.db = db

    async def get_by_id(self, user_id: int):
        return await self.db.query_one(
            "SELECT * FROM users WHERE id = :id",
            {"id": user_id}
        )

    async def get_active_users(self):
        return await self.db.query_all(
            "SELECT * FROM users WHERE status = :status",
            {"status": "active"}
        )

    async def create(self, user_data: dict):
        return await self.db.insert("users", user_data)

    async def update(self, user_id: int, user_data: dict):
        return await self.db.update("users", user_data, {"id": user_id})

    async def delete(self, user_id: int):
        return await self.db.delete("users", {"id": user_id})

# conftest.py
import pytest

@pytest.fixture
async def user_repo(async_database):
    return AsyncUserRepository(async_database)

# 测试文件
@pytest.mark.asyncio
async def test_with_repository(user_repo):
    """使用 Repository 模式"""

    # 创建用户
    user_id = await user_repo.create({
        "name": "Frank",
        "email": "frank@example.com",
        "age": 30
    })

    # 查询用户
    user = await user_repo.get_by_id(user_id)
    assert user["name"] == "Frank"

    # 清理
    await user_repo.delete(user_id)
```

## 性能对比

### 顺序查询 vs 并发查询

```python
import time
import asyncio

# ❌ 顺序查询（慢）
def test_sequential_queries():
    db = Database(...)  # 同步版本
    start = time.time()

    for i in range(50):
        db.query_one("SELECT * FROM users WHERE id = :id", {"id": i})

    print(f"顺序查询: {time.time() - start:.2f}秒")  # ~10秒

# ✅ 并发查询（快 5 倍）
@pytest.mark.asyncio
async def test_concurrent_queries():
    db = AsyncDatabase(...)  # 异步版本
    start = time.time()

    tasks = [
        db.query_one("SELECT * FROM users WHERE id = :id", {"id": i})
        for i in range(50)
    ]
    await asyncio.gather(*tasks)

    print(f"并发查询: {time.time() - start:.2f}秒")  # ~2秒 ⚡
```

## 驱动支持

### MySQL

```python
# 同步驱动（v3.x）
DB__CONNECTION_STRING=mysql+pymysql://user:pass@localhost/test_db

# 异步驱动（v4.0.0 自动转换）
# mysql+aiomysql://user:pass@localhost/test_db

# 安装依赖
pip install aiomysql
```

### PostgreSQL

```python
# 同步驱动（v3.x）
DB__CONNECTION_STRING=postgresql+psycopg2://user:pass@localhost/test_db

# 异步驱动（v4.0.0 自动转换）
# postgresql+asyncpg://user:pass@localhost/test_db

# 安装依赖
pip install asyncpg
```

### SQLite

```python
# 同步驱动（v3.x）
DB__CONNECTION_STRING=sqlite:///test.db

# 异步驱动（v4.0.0 自动转换）
# sqlite+aiosqlite:///test.db

# 安装依赖
pip install aiosqlite
```

## 最佳实践

### 1. 使用连接池

框架自动管理连接池，无需手动配置：

```yaml
# .env
DB__POOL_SIZE=10              # 连接池大小
DB__MAX_OVERFLOW=20           # 额外连接数
DB__POOL_TIMEOUT=30           # 获取连接超时（秒）
DB__POOL_RECYCLE=3600         # 连接回收时间（秒）
DB__POOL_PRE_PING=true        # 启用连接预检查
```

### 2. 合理控制并发

```python
import asyncio

@pytest.mark.asyncio
async def test_controlled_concurrency(async_database):
    """控制并发数"""

    # 使用 Semaphore 限制并发
    semaphore = asyncio.Semaphore(10)  # 最多10个并发

    async def query_with_limit(user_id):
        async with semaphore:
            return await async_database.query_one(
                "SELECT * FROM users WHERE id = :id",
                {"id": user_id}
            )

    tasks = [query_with_limit(i) for i in range(100)]
    users = await asyncio.gather(*tasks)
```

### 3. 使用事务保证一致性

```python
@pytest.mark.asyncio
async def test_transaction_rollback(async_database):
    """事务回滚示例"""

    try:
        async with async_database.session() as session:
            async with session.begin():
                # 操作1：扣款
                await session.execute(
                    "UPDATE accounts SET balance = balance - :amount WHERE id = :id",
                    {"amount": 100, "id": 1}
                )

                # 操作2：加款
                await session.execute(
                    "UPDATE accounts SET balance = balance + :amount WHERE id = :id",
                    {"amount": 100, "id": 2}
                )

                # 如果余额不足，抛出异常
                # 整个事务自动回滚
    except Exception as e:
        print(f"事务回滚: {e}")
```

## 迁移指南

### 从 Database 迁移到 AsyncDatabase

只需要两步：

```python
# Step 1: 更改 fixture
- def test_user_query(database):
+ @pytest.mark.asyncio
+ async def test_user_query(async_database):

# Step 2: 调用加 await
-     users = database.query_all("SELECT * FROM users")
+     users = await async_database.query_all("SELECT * FROM users")
```

**完整示例**:

```python
# v3.x (同步)
def test_user_operations(database):
    user_id = database.insert("users", {"name": "Alice", "age": 25})
    user = database.query_one("SELECT * FROM users WHERE id = :id", {"id": user_id})
    database.delete("users", {"id": user_id})

# v4.0.0 (异步)
@pytest.mark.asyncio
async def test_user_operations(async_database):
    user_id = await async_database.insert("users", {"name": "Alice", "age": 25})
    user = await async_database.query_one("SELECT * FROM users WHERE id = :id", {"id": user_id})
    await async_database.delete("users", {"id": user_id})
```

## 常见问题

### Q1: 什么时候使用异步数据库？

**A**: 推荐在以下场景使用：

- ✅ **并发测试**: 需要同时执行多个数据库查询
- ✅ **性能测试**: 测试系统在高并发数据库访问下的表现
- ✅ **批量操作**: 需要插入/更新/删除大量数据
- ❌ **简单测试**: 单个查询的简单测试，同步即可

### Q2: 驱动如何自动转换？

**A**: 框架提供 `resolved_async_connection_string()` 方法：

```python
# 配置文件中使用同步驱动
DB__CONNECTION_STRING=mysql+pymysql://user:pass@localhost/test_db

# 框架自动检测并转换
# mysql+pymysql → mysql+aiomysql ✅
```

### Q3: 事务如何使用？

**A**: 使用 `async with session.begin()`:

```python
async with async_database.session() as session:
    async with session.begin():
        # 事务中的操作
        await session.execute(...)
        # 自动提交/回滚
```

## 相关文档

- [v4.0.0 发布说明](../releases/v4.0.0.md) - 版本详细信息
- [v3 to v4 迁移指南](../migration/v3-to-v4.md) - 完整迁移步骤
- [AsyncBaseAPI 使用指南](./async_api_guide.md) - 异步 HTTP 客户端
- [Repository & UoW 指南](./repository_uow_guide.md) - 数据访问层模式

## 总结

AsyncDatabase 为 v4.0.0 带来了：

- ⚡ **5-10 倍性能提升** - 并发数据库操作
- 🔄 **完全兼容** - 与 Database API 一致
- 🎯 **自动驱动转换** - 无需手动配置
- 🛠️ **完整功能** - CRUD、事务、连接池全支持

**立即使用异步数据库，提升测试性能！**🚀
