# 数据库访问指南

> **最后更新**: 2026-01-16
> **适用版本**: v2.0.0+（同步），v4.0.0+（异步推荐）

---

## 概述

DF Test Framework 提供完整的数据库访问能力，支持同步和异步两种模式：

| 组件 | 版本 | 性能 | 适用场景 |
|------|------|------|---------|
| **AsyncDatabase** | v4.0.0+ | ⚡ 5-10倍提升 | 并发测试、批量操作、性能测试 |
| **Database** | v2.0.0+ | 标准 | 普通测试、简单查询 |
| **Repository** | v3.7.0+ | 标准 | 领域模型驱动、数据访问层封装 |
| **UnitOfWork** | v3.7.0+ | 标准 | 事务管理、多表操作 |

### 支持的数据库

| 数据库 | 同步驱动 | 异步驱动 | 推荐版本 |
|--------|---------|---------|---------|
| **MySQL** | pymysql | aiomysql | 5.7+ |
| **PostgreSQL** | psycopg2 | asyncpg | 12+ |
| **SQLite** | sqlite3 | aiosqlite | 3.35+ |

---

## 快速开始

### 1. 配置数据库

```yaml
# .env 或 configs/config.yaml
DB__HOST=localhost
DB__PORT=3306
DB__NAME=test_db
DB__USER=root
DB__PASSWORD=password

# 连接字符串方式
DB__CONNECTION_STRING=mysql+pymysql://root:password@localhost:3306/test_db
```

### 2. 选择合适的客户端

```python
# 异步客户端（推荐，v4.0.0+）
import pytest

@pytest.mark.asyncio
async def test_async_query(async_database):
    """使用异步客户端"""
    users = await async_database.query_all("SELECT * FROM users")
    assert len(users) > 0

# 同步客户端（兼容，v2.0.0+）
def test_sync_query(database):
    """使用同步客户端"""
    users = database.query_all("SELECT * FROM users")
    assert len(users) > 0
```

---

## Database 同步客户端

### 基础用法

#### 查询操作

```python
def test_query_operations(database):
    """同步查询操作"""

    # 查询所有记录
    users = database.query_all("SELECT * FROM users")

    # 带参数查询
    adult_users = database.query_all(
        "SELECT * FROM users WHERE age >= :min_age",
        {"min_age": 18}
    )

    # 查询单条记录
    user = database.query_one(
        "SELECT * FROM users WHERE id = :id",
        {"id": 1}
    )

    # 查询不存在的记录返回 None
    missing = database.query_one(
        "SELECT * FROM users WHERE id = :id",
        {"id": 99999}
    )
    assert missing is None
```

#### 插入操作

```python
def test_insert_operations(database):
    """同步插入操作"""

    # 单条插入
    user_id = database.insert(
        "users",
        {
            "name": "Alice",
            "email": "alice@example.com",
            "age": 25
        }
    )

    assert isinstance(user_id, int)
    assert user_id > 0

    # 验证插入
    user = database.query_one(
        "SELECT * FROM users WHERE id = :id",
        {"id": user_id}
    )
    assert user["name"] == "Alice"
```

#### 更新操作

```python
def test_update_operations(database):
    """同步更新操作"""

    # 创建测试数据
    user_id = database.insert(
        "users",
        {"name": "Bob", "email": "bob@example.com", "age": 30}
    )

    # 更新单条记录
    rows_affected = database.update(
        "users",
        {"age": 31, "email": "bob.new@example.com"},
        {"id": user_id}
    )
    assert rows_affected == 1

    # 批量更新
    rows_affected = database.update(
        "users",
        {"status": "active"},
        {"age__gte": 18}  # age >= 18
    )
    print(f"更新了 {rows_affected} 条记录")
```

#### 删除操作

```python
def test_delete_operations(database):
    """同步删除操作"""

    # 创建测试数据
    user_id = database.insert(
        "users",
        {"name": "Charlie", "email": "charlie@example.com", "age": 25}
    )

    # 删除单条记录
    rows_deleted = database.delete("users", {"id": user_id})
    assert rows_deleted == 1

    # 验证删除
    user = database.query_one(
        "SELECT * FROM users WHERE id = :id",
        {"id": user_id}
    )
    assert user is None

    # 批量删除
    rows_deleted = database.delete("users", {"status": "inactive"})
    print(f"删除了 {rows_deleted} 条记录")
```

#### 执行原生 SQL

```python
def test_execute_sql(database):
    """执行原生 SQL"""

    # DDL 操作
    database.execute("""
        CREATE TABLE IF NOT EXISTS temp_table (
            id INT PRIMARY KEY AUTO_INCREMENT,
            data VARCHAR(255)
        )
    """)

    # DML 操作
    database.execute(
        "INSERT INTO temp_table (data) VALUES (:data)",
        {"data": "test"}
    )

    # 清理
    database.execute("DROP TABLE temp_table")
```

### 事务管理

```python
def test_transaction(database):
    """使用事务"""

    with database.session() as session:
        # 开始事务
        with session.begin():
            # 操作1：插入用户
            result1 = session.execute(
                "INSERT INTO users (name, email) VALUES (:name, :email)",
                {"name": "Dave", "email": "dave@example.com"}
            )

            # 操作2：插入订单
            result2 = session.execute(
                "INSERT INTO orders (user_id, total) VALUES (:user_id, :total)",
                {"user_id": result1.lastrowid, "total": 100}
            )

            # 如果任何操作失败，整个事务回滚
            # 如果成功，事务自动提交
```

### Fixture 使用

```python
# conftest.py
import pytest
from df_test_framework import Database

@pytest.fixture(scope="session")
def database():
    """数据库连接 fixture"""
    db = Database.from_env()  # 从环境变量加载配置
    yield db
    db.close()

# 测试文件
def test_with_fixture(database):
    """使用 database fixture"""
    users = database.query_all("SELECT * FROM users LIMIT 10")
    assert isinstance(users, list)
```

---

## AsyncDatabase 异步客户端（推荐）

> **引入版本**: v4.0.0
> **稳定版本**: v4.0.0+

### 核心优势

| 特性 | AsyncDatabase | Database |
|------|--------------|----------|
| **性能** | ⚡ 并发50查询 ~2秒 | ~10秒 |
| **并发支持** | ✅ 原生支持 | ❌ 不支持 |
| **语法** | `await db.query_all()` | `db.query_all()` |
| **适用场景** | 并发数据操作、性能测试 | 普通测试 |
| **驱动** | aiomysql/asyncpg/aiosqlite | pymysql/psycopg2/sqlite3 |

### 基础用法

#### 查询操作

```python
import pytest

@pytest.mark.asyncio
async def test_async_query(async_database):
    """异步查询操作"""

    # 查询所有记录
    users = await async_database.query_all("SELECT * FROM users")

    # 带参数查询
    adult_users = await async_database.query_all(
        "SELECT * FROM users WHERE age >= :min_age",
        {"min_age": 18}
    )

    # 查询单条记录
    user = await async_database.query_one(
        "SELECT * FROM users WHERE id = :id",
        {"id": 1}
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

#### CRUD 完整示例

```python
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

### 高级用法

#### 并发查询（性能提升 5-10 倍）

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

#### 并发插入

```python
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

#### 批量操作优化

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

#### Pydantic 模型集成

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

### 事务管理

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

### Fixture 使用

```python
# conftest.py
import pytest

@pytest.fixture
async def async_database():
    """异步数据库 fixture"""
    # fixture 自动处理：
    # - 数据库连接配置
    # - 连接池管理
    # - EventBus 事件发布
    # - 资源清理
    from df_test_framework import AsyncDatabase

    db = AsyncDatabase.from_env()
    yield db
    await db.close()

# 测试文件
@pytest.mark.asyncio
async def test_with_fixture(async_database):
    """使用 async_database fixture"""
    users = await async_database.query_all("SELECT * FROM users")
    assert isinstance(users, list)
```

### 驱动自动转换

框架会自动将同步驱动转换为异步驱动：

```python
# 配置文件中使用同步驱动
DB__CONNECTION_STRING=mysql+pymysql://user:pass@localhost/test_db

# 框架自动转换：
# mysql+pymysql → mysql+aiomysql ✅
# postgresql+psycopg2 → postgresql+asyncpg ✅
# sqlite → sqlite+aiosqlite ✅
```

### 迁移指南

从 Database 迁移到 AsyncDatabase 只需两步：

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

---

## Repository 模式

> **引入版本**: v3.7.0
> **稳定版本**: v3.7.0+

Repository 模式封装数据访问逻辑，提供类似集合的接口，使用领域语言而非数据库语言。

### 定义 Repository

```python
from df_test_framework.capabilities.databases.repositories import BaseRepository
from sqlalchemy.orm import Session

class UserRepository(BaseRepository):
    """用户数据访问"""

    def __init__(self, session: Session):
        super().__init__(session, table_name="users")

    def find_by_username(self, username: str) -> dict | None:
        """根据用户名查找用户"""
        return self.find_one({"username": username})

    def find_active_users(self) -> list[dict]:
        """查找所有激活用户"""
        return self.find_all({"status": "ACTIVE"})

    def count_by_role(self, role: str) -> int:
        """统计指定角色的用户数"""
        return self.count({"role": role})
```

### 基础 API

#### 查询方法

```python
# 根据 ID 查找
user = repo.find_by_id(123)

# 指定 ID 列
user = repo.find_by_id("user_001", id_column="user_id")

# 根据条件查找单条
user = repo.find_one({"username": "alice", "status": "ACTIVE"})

# 查找多条记录
users = repo.find_all({"status": "ACTIVE"})

# 排序和分页
users = repo.find_all(
    {"status": "ACTIVE"},
    order_by="created_at DESC",
    limit=20,
    offset=0
)

# 统计记录数
total = repo.count()
active_count = repo.count({"status": "ACTIVE"})

# 检查记录是否存在
if repo.exists({"username": "alice"}):
    print("用户已存在")
```

#### 修改方法

```python
# 创建记录
user_data = {
    "username": "alice",
    "email": "alice@example.com",
    "status": "ACTIVE"
}
user_id = repo.create(user_data)

# 更新记录
affected = repo.update(
    {"username": "alice"},
    {"email": "alice_new@example.com"}
)

# 删除记录
affected = repo.delete({"username": "alice"})
```

### 扩展 Repository

```python
class UserRepository(BaseRepository):
    """扩展 Repository 添加业务方法"""

    def find_by_email(self, email: str) -> dict | None:
        """根据邮箱查找用户"""
        return self.find_one({"email": email})

    def activate_user(self, user_id: int) -> int:
        """激活用户"""
        return self.update(
            {"id": user_id},
            {"status": "ACTIVE", "activated_at": "NOW()"}
        )

    def find_users_by_role_with_orders(self, role: str) -> list[dict]:
        """查找指定角色的用户及其订单（自定义 SQL）"""
        sql = """
            SELECT u.*, COUNT(o.id) as order_count
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            WHERE u.role = :role
            GROUP BY u.id
        """
        return self._query_all(sql, {"role": role})
```

### 在测试中使用

```python
# conftest.py
import pytest
from df_test_framework import Database

@pytest.fixture(scope="session")
def database():
    """数据库连接"""
    db = Database.from_env()
    yield db
    db.close()

@pytest.fixture
def user_repo(database):
    """用户 Repository"""
    with database.session() as session:
        yield UserRepository(session)

# 测试文件
def test_with_repository(user_repo):
    """使用 Repository 模式"""

    # 创建用户
    user_data = {
        "username": "frank",
        "email": "frank@example.com",
        "status": "ACTIVE"
    }
    user_id = user_repo.create(user_data)

    # 查询用户
    user = user_repo.find_by_id(user_id)
    assert user["username"] == "frank"

    # 使用业务方法
    active_users = user_repo.find_active_users()
    assert len(active_users) > 0
```

---

## Unit of Work 模式

> **引入版本**: v3.7.0
> **稳定版本**: v3.7.0+

Unit of Work (工作单元) 维护受业务事务影响的对象列表，并协调变更的写入和并发问题的解决。

### 核心特性

- ✅ 统一的事务边界管理
- ✅ 多个 Repository 共享同一 Session
- ✅ 显式的提交/回滚控制
- ✅ 测试友好的数据隔离
- ✅ EventBus 集成（v3.14.0+）

### 定义 UnitOfWork

```python
from df_test_framework.capabilities.databases import UnitOfWork
from sqlalchemy.orm import Session

class MyProjectUoW(UnitOfWork):
    """项目 Unit of Work"""

    def __init__(self, session_factory, event_bus=None):
        super().__init__(session_factory, event_bus=event_bus)

    @property
    def users(self) -> UserRepository:
        """用户 Repository"""
        if not hasattr(self, "_users"):
            self._users = UserRepository(self.session)
        return self._users

    @property
    def orders(self) -> OrderRepository:
        """订单 Repository"""
        if not hasattr(self, "_orders"):
            self._orders = OrderRepository(self.session)
        return self._orders
```

### 基本用法

```python
from df_test_framework.capabilities.databases import UnitOfWork

# 作为上下文管理器（推荐）
with UnitOfWork(session_factory) as uow:
    # 1. 执行业务操作
    user = uow.users.find_by_username("alice")
    uow.orders.create({"user_id": user["id"], "amount": 100})

    # 2. 显式提交
    uow.commit()
    # 如果不调用 commit()，退出时自动回滚
```

### 事务控制

#### 提交事务

```python
with UnitOfWork(session_factory) as uow:
    uow.users.create({"username": "alice"})
    uow.commit()  # 提交更改
```

#### 回滚事务

```python
with UnitOfWork(session_factory) as uow:
    try:
        uow.users.create({"username": "alice"})
        uow.orders.create({"user_id": 999})  # 可能失败
        uow.commit()
    except Exception as e:
        uow.rollback()  # 回滚所有更改
        raise
```

### 共享 Session

Unit of Work 中的所有 Repository 共享同一 Session：

```python
with UnitOfWork(session_factory) as uow:
    # 所有操作在同一事务中
    user_id = uow.users.create({"username": "alice"})
    uow.orders.create({"user_id": user_id, "amount": 100})
    uow.payments.create({"order_id": ..., "amount": 100})

    # 一次性提交所有更改
    uow.commit()
```

### 在测试中使用

```python
# conftest.py
import pytest
from df_test_framework import Database

@pytest.fixture(scope="session")
def database():
    """数据库连接"""
    db = Database.from_env()
    yield db
    db.close()

@pytest.fixture
def uow(database):
    """Unit of Work"""
    with MyProjectUoW(database.session_factory) as uow:
        yield uow
        # 自动回滚（除非已 commit）

# 测试文件
def test_create_user(uow):
    """测试创建用户"""
    # 创建用户
    user_data = {
        "username": "alice",
        "email": "alice@example.com",
        "status": "ACTIVE"
    }
    user_id = uow.users.create(user_data)

    # 提交事务
    uow.commit()

    # 验证
    user = uow.users.find_by_id(user_id)
    assert user["username"] == "alice"

def test_transaction_rollback(uow):
    """测试事务回滚"""
    # 创建用户（不提交）
    user_id = uow.users.create({"username": "temp_user"})

    # fixture 结束时自动回滚，不影响其他测试
```

### 高级用法

#### EventBus 集成（v3.14.0+）

```python
from df_test_framework.infrastructure.events import EventBus

event_bus = EventBus()
uow = MyProjectUoW(session_factory, event_bus=event_bus)

# 订阅事务事件
@event_bus.subscribe("transaction.committed")
def on_committed(event):
    print(f"事务已提交: {event.timestamp}")

with uow:
    uow.users.create({"username": "alice"})
    uow.commit()  # 触发 transaction.committed 事件
```

#### 自动发现 Repository

```python
class MyProjectUoW(UnitOfWork):
    """自动发现 repositories 包下的所有 Repository"""

    def __init__(self, session_factory):
        super().__init__(
            session_factory,
            repository_package="my_project.repositories"
        )
        # ✅ 自动发现并注册所有 Repository

# 使用
with MyProjectUoW(session_factory) as uow:
    # 自动注册的 Repository 可直接使用
    user = uow.users.find_by_username("alice")
    order = uow.orders.find_by_id(123)
```

#### 嵌套事务

```python
with UnitOfWork(session_factory) as outer_uow:
    user_id = outer_uow.users.create({"username": "alice"})

    # 内部 UoW 使用 savepoint
    with UnitOfWork(session_factory) as inner_uow:
        inner_uow.orders.create({"user_id": user_id})
        inner_uow.commit()  # 提交到 savepoint

    outer_uow.commit()  # 提交整个事务
```

---

## 常见场景

### 场景1：基础数据查询

**场景**: 查询用户列表，验证数据存在

```python
# 同步方式
def test_query_users(database):
    users = database.query_all("SELECT * FROM users WHERE status = :status", {"status": "active"})
    assert len(users) > 0

# 异步方式（推荐）
@pytest.mark.asyncio
async def test_query_users(async_database):
    users = await async_database.query_all("SELECT * FROM users WHERE status = :status", {"status": "active"})
    assert len(users) > 0
```

### 场景2：批量数据插入

**场景**: 并发插入大量测试数据

```python
# 同步方式（慢）
def test_bulk_insert(database):
    for i in range(100):
        database.insert("users", {"name": f"User{i}", "email": f"user{i}@example.com"})

# 异步方式（快 5-10 倍）
@pytest.mark.asyncio
async def test_bulk_insert(async_database):
    tasks = [
        async_database.insert("users", {"name": f"User{i}", "email": f"user{i}@example.com"})
        for i in range(100)
    ]
    await asyncio.gather(*tasks)
```

### 场景3：跨表事务操作

**场景**: 创建用户和订单，确保事务一致性

```python
# 使用 UnitOfWork（推荐）
def test_create_user_and_order(uow):
    # 创建用户
    user_id = uow.users.create({
        "username": "alice",
        "email": "alice@example.com"
    })

    # 创建订单
    order_id = uow.orders.create({
        "user_id": user_id,
        "total": 100
    })

    # 一次性提交
    uow.commit()

    # 验证
    user = uow.users.find_by_id(user_id)
    order = uow.orders.find_by_id(order_id)
    assert order["user_id"] == user["id"]
```

### 场景4：数据访问层封装

**场景**: 封装复杂的数据访问逻辑

```python
# 定义 Repository
class UserRepository(BaseRepository):
    def find_active_users_with_orders(self) -> list[dict]:
        """查找有订单的活跃用户"""
        sql = """
            SELECT u.*, COUNT(o.id) as order_count
            FROM users u
            INNER JOIN orders o ON u.id = o.user_id
            WHERE u.status = 'ACTIVE'
            GROUP BY u.id
            HAVING order_count > 0
        """
        return self._query_all(sql)

# 使用
def test_active_users_with_orders(user_repo):
    users = user_repo.find_active_users_with_orders()
    assert all(u["order_count"] > 0 for u in users)
```

### 场景5：性能测试

**场景**: 测试系统在高并发数据库访问下的表现

```python
@pytest.mark.asyncio
async def test_high_concurrency(async_database):
    """模拟高并发查询"""

    # 并发50个查询
    tasks = [
        async_database.query_one("SELECT * FROM users WHERE id = :id", {"id": i})
        for i in range(1, 51)
    ]

    import time
    start = time.time()
    results = await asyncio.gather(*tasks)
    duration = time.time() - start

    # 性能断言
    assert duration < 3  # 应该在3秒内完成
    assert len(results) == 50
```

---

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

### 性能提升数据

| 操作类型 | Database (同步) | AsyncDatabase (异步) | 性能提升 |
|---------|----------------|-------------------|---------|
| 50个查询 | ~10秒 | ~2秒 | 5倍 |
| 100个插入 | ~20秒 | ~3秒 | 6.7倍 |
| 复杂JOIN | ~15秒 | ~2秒 | 7.5倍 |

---

## 最佳实践

### 1. 选择合适的客户端

```python
# ✅ 并发测试使用异步
@pytest.mark.asyncio
async def test_concurrent_operations(async_database):
    tasks = [async_database.query_one(...) for _ in range(50)]
    await asyncio.gather(*tasks)

# ✅ 简单测试使用同步
def test_simple_query(database):
    user = database.query_one("SELECT * FROM users WHERE id = 1")
    assert user is not None
```

### 2. 使用 Repository 封装数据访问

```python
# ✅ 好的实践 - Repository 只负责数据访问
class UserRepository(BaseRepository):
    def find_by_username(self, username: str) -> dict | None:
        return self.find_one({"username": username})

# ❌ 不好的实践 - 不要在 Repository 中处理业务逻辑
class UserRepository(BaseRepository):
    def authenticate(self, username: str, password: str) -> dict | None:
        user = self.find_one({"username": username})
        if user and verify_password(password, user["password_hash"]):
            return user
        return None
```

### 3. UoW 管理事务边界

```python
# ✅ 好的实践 - UoW 控制事务
def create_order_with_payment(uow, order_data, payment_data):
    order_id = uow.orders.create(order_data)
    payment_data["order_id"] = order_id
    uow.payments.create(payment_data)
    uow.commit()  # 一次性提交

# ❌ 不好的实践 - Repository 不应该提交事务
class OrderRepository(BaseRepository):
    def create_with_commit(self, data):
        order_id = self.create(data)
        self.session.commit()  # ❌ 不要这样做
        return order_id
```

### 4. 显式提交

```python
# ✅ 好的实践 - 显式提交
with UnitOfWork(session_factory) as uow:
    uow.users.create(data)
    uow.commit()  # 明确提交

# ❌ 不好的实践 - 依赖自动提交
with UnitOfWork(session_factory) as uow:
    uow.users.create(data)
    # 没有 commit()，会自动回滚
```

### 5. 测试隔离

```python
# ✅ 好的实践 - 使用 fixture 自动回滚
@pytest.fixture
def uow(database):
    with MyProjectUoW(database.session_factory) as uow:
        yield uow
        # 自动回滚

# ❌ 不好的实践 - 手动清理数据
def test_user_creation(database):
    uow = MyProjectUoW(database.session_factory)
    user_id = uow.users.create(data)
    uow.commit()
    # ... 测试
    uow.users.delete({"id": user_id})  # ❌ 不推荐
```

### 6. 连接池配置

```yaml
# .env
DB__POOL_SIZE=10              # 连接池大小
DB__MAX_OVERFLOW=20           # 额外连接数
DB__POOL_TIMEOUT=30           # 获取连接超时（秒）
DB__POOL_RECYCLE=3600         # 连接回收时间（秒）
DB__POOL_PRE_PING=true        # 启用连接预检查
```

### 7. 控制并发数

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

---

## 常见问题

### Q1: 什么时候使用异步数据库？

**A**: 推荐在以下场景使用：

- ✅ **并发测试**: 需要同时执行多个数据库查询
- ✅ **性能测试**: 测试系统在高并发数据库访问下的表现
- ✅ **批量操作**: 需要插入/更新/删除大量数据
- ❌ **简单测试**: 单个查询的简单测试，同步即可

### Q2: Repository 和 DAO 的区别？

**A**: Repository 使用领域语言（如 `find_by_username`），而 DAO 使用数据库语言（如 `selectByUsername`）。Repository 更面向领域模型。

### Q3: 为什么 Repository 返回字典而不是模型？

**A**: 为了灵活性。你可以在 Repository 方法中转换为 Pydantic 模型：

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    username: str
    email: str

class UserRepository(BaseRepository):
    def find_by_username(self, username: str) -> User | None:
        data = self.find_one({"username": username})
        return User(**data) if data else None
```

### Q4: 驱动如何自动转换？

**A**: 框架提供 `resolved_async_connection_string()` 方法：

```python
# 配置文件中使用同步驱动
DB__CONNECTION_STRING=mysql+pymysql://user:pass@localhost/test_db

# 框架自动检测并转换
# mysql+pymysql → mysql+aiomysql ✅
# postgresql+psycopg2 → postgresql+asyncpg ✅
# sqlite → sqlite+aiosqlite ✅
```

### Q5: 如何处理复杂查询？

**A**: 使用 `_query_all()` 或 `_query_one()` 执行原生 SQL：

```python
def find_with_complex_join(self) -> list[dict]:
    sql = """
        SELECT u.*, p.name as profile_name
        FROM users u
        LEFT JOIN profiles p ON u.id = p.user_id
        WHERE u.status = :status
    """
    return self._query_all(sql, {"status": "ACTIVE"})
```

### Q6: 事务如何使用？

**A**: 使用上下文管理器：

```python
# 同步事务
with database.session() as session:
    with session.begin():
        # 事务中的操作
        session.execute(...)
        # 自动提交/回滚

# 异步事务
async with async_database.session() as session:
    async with session.begin():
        # 事务中的操作
        await session.execute(...)
        # 自动提交/回滚
```

---

## 相关文档

| 文档 | 描述 |
|------|------|
| [v4.0.0 发布说明](../releases/v4.0.0.md) | AsyncDatabase 版本详细信息 |
| [v3 to v4 迁移指南](../migration/v3-to-v4.md) | 完整迁移步骤 |
| [AsyncBaseAPI 使用指南](./async_api_guide.md) | 异步 HTTP 客户端 |
| [测试数据指南](./test_data.md) | 测试数据管理 |
| [测试数据清理指南](./test_data_cleanup.md) | 数据清理策略 |
| [EventBus 使用指南](./event_bus_guide.md) | 事件总线集成 |

---

## 总结

DF Test Framework 提供完整的数据库访问方案：

| 组件 | 优势 | 适用场景 |
|------|------|---------|
| **AsyncDatabase** | ⚡ 5-10倍性能提升 | 并发测试、性能测试、批量操作 |
| **Database** | 简单易用 | 普通测试、简单查询 |
| **Repository** | 领域驱动、封装良好 | 数据访问层设计、复杂业务 |
| **UnitOfWork** | 事务管理、多表操作 | 跨表事务、业务一致性 |

**推荐组合**:

- 🚀 **高性能场景**: AsyncDatabase + asyncio.gather
- 📦 **业务场景**: UnitOfWork + Repository
- ✅ **简单场景**: Database 直接使用

**立即开始使用，提升测试效率！** 🎯
