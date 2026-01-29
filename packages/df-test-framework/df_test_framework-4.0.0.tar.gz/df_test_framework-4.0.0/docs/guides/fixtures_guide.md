# Fixtures 使用指南

> **最后更新**: 2026-01-17
> **适用版本**: v3.0.0+

---

## 概述

本指南介绍 DF Test Framework 提供的 pytest fixtures，用于简化测试编写。框架提供了丰富的内置 fixtures，涵盖 HTTP 客户端、数据库、Redis、UI 测试、配置管理等各个方面。

### 核心特性

- **自动注入**: 通过 pytest 的依赖注入机制，自动提供测试所需的资源
- **生命周期管理**: 支持 session、module、class、function 等多种 scope
- **同步/异步双模式**: v4.0.0+ 提供完整的异步 fixtures 支持
- **配置驱动**: 通过 `.env` 或 YAML 配置文件统一管理
- **自动清理**: 测试结束后自动释放资源

---

## 目录

- [核心 Fixtures](#核心-fixtures)
  - [HTTP 客户端 Fixtures](#http-客户端-fixtures)
  - [数据库 Fixtures](#数据库-fixtures)
  - [Redis Fixtures](#redis-fixtures)
  - [UI 测试 Fixtures](#ui-测试-fixtures)
  - [配置与运行时 Fixtures](#配置与运行时-fixtures)
- [API 封装 Fixtures](#api-封装-fixtures)
- [数据管理 Fixtures](#数据管理-fixtures)
- [Fixture Scope 说明](#fixture-scope-说明)
- [自定义 Fixtures](#自定义-fixtures)
- [最佳实践](#最佳实践)

---

## 核心 Fixtures

### HTTP 客户端 Fixtures

#### `http_client` - 同步 HTTP 客户端

**Scope**: `session`
**版本**: v2.0.0+

同步 HTTP 客户端，适合简单的 API 测试场景。

```python
def test_get_user(http_client):
    """测试获取用户信息"""
    response = http_client.get("/users/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1

def test_create_user(http_client):
    """测试创建用户"""
    payload = {"name": "张三", "email": "zhangsan@example.com"}
    response = http_client.post("/users", json=payload)
    assert response.status_code == 201
```

#### `async_http_client` - 异步 HTTP 客户端

**Scope**: `session`
**版本**: v4.0.0+

异步 HTTP 客户端，并发性能提升 10-30 倍，适合高并发测试场景。

```python
import pytest

@pytest.mark.asyncio
async def test_get_user(async_http_client):
    """测试获取用户信息（异步）"""
    response = await async_http_client.get("/users/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1

@pytest.mark.asyncio
async def test_concurrent_requests(async_http_client):
    """测试并发请求"""
    import asyncio

    # 并发发送 10 个请求
    tasks = [
        async_http_client.get(f"/users/{i}")
        for i in range(1, 11)
    ]
    responses = await asyncio.gather(*tasks)

    assert all(r.status_code == 200 for r in responses)
```

**配置示例**:

```yaml
# .env 或 configs/config.yaml
HTTP__BASE_URL=https://api.example.com
HTTP__TIMEOUT=30
HTTP__VERIFY_SSL=true
```

---

### 数据库 Fixtures

#### `database` - 同步数据库客户端

**Scope**: `session`
**版本**: v2.0.0+

同步数据库客户端，基于 SQLAlchemy，支持 MySQL、PostgreSQL、SQLite。

```python
def test_query_users(database):
    """测试查询用户"""
    users = database.query_all("SELECT * FROM users WHERE status = :status", {"status": 1})
    assert len(users) > 0

def test_insert_user(database):
    """测试插入用户"""
    user_id = database.insert(
        "users",
        {"name": "李四", "email": "lisi@example.com", "status": 1}
    )
    assert user_id > 0

    # 验证插入
    user = database.query_one("SELECT * FROM users WHERE id = :id", {"id": user_id})
    assert user["name"] == "李四"
```

#### `async_database` - 异步数据库客户端

**Scope**: `session`
**版本**: v4.0.0+

异步数据库客户端，基于 SQLAlchemy 2.0 AsyncEngine，性能提升 5-10 倍。

```python
import pytest

@pytest.mark.asyncio
async def test_query_users(async_database):
    """测试查询用户（异步）"""
    users = await async_database.query_all(
        "SELECT * FROM users WHERE status = :status",
        {"status": 1}
    )
    assert len(users) > 0

@pytest.mark.asyncio
async def test_batch_insert(async_database):
    """测试批量插入"""
    import asyncio

    # 并发插入 100 条记录
    tasks = [
        async_database.insert(
            "users",
            {"name": f"用户{i}", "email": f"user{i}@example.com", "status": 1}
        )
        for i in range(100)
    ]
    user_ids = await asyncio.gather(*tasks)

    assert len(user_ids) == 100
```

**配置示例**:

```yaml
# .env 或 configs/config.yaml
DB__HOST=localhost
DB__PORT=3306
DB__NAME=test_db
DB__USER=root
DB__PASSWORD=password
DB__CHARSET=utf8mb4

# 或使用连接字符串
DB__CONNECTION_STRING=mysql+aiomysql://root:password@localhost:3306/test_db?charset=utf8mb4
```

---

### Redis Fixtures

#### `redis_client` - 同步 Redis 客户端

**Scope**: `session`
**版本**: v3.0.0+

同步 Redis 客户端，用于缓存和会话管理。

```python
def test_redis_operations(redis_client):
    """测试 Redis 基本操作"""
    # 设置值
    redis_client.set("test_key", "test_value", ex=60)

    # 获取值
    value = redis_client.get("test_key")
    assert value == "test_value"

    # 删除
    redis_client.delete("test_key")
    assert redis_client.get("test_key") is None
```

#### `async_redis_client` - 异步 Redis 客户端

**Scope**: `session`
**版本**: v4.0.0+

异步 Redis 客户端，缓存操作性能提升 5-10 倍。

```python
import pytest

@pytest.mark.asyncio
async def test_redis_operations(async_redis_client):
    """测试 Redis 基本操作（异步）"""
    # 设置值
    await async_redis_client.set("test_key", "test_value", ex=60)

    # 获取值
    value = await async_redis_client.get("test_key")
    assert value == "test_value"

    # 删除
    await async_redis_client.delete("test_key")
    assert await async_redis_client.get("test_key") is None
```

**配置示例**:

```yaml
# .env 或 configs/config.yaml
REDIS__HOST=localhost
REDIS__PORT=6379
REDIS__DB=0
REDIS__PASSWORD=your_password
```

---

### UI 测试 Fixtures

#### `page` - 同步页面实例

**Scope**: `function`
**版本**: v3.0.0+

Playwright 页面实例，每个测试函数独立的页面，测试间相互隔离。

```python
def test_login(page):
    """测试登录功能"""
    page.goto("https://example.com/login")
    page.get_by_label("Username").fill("admin")
    page.get_by_label("Password").fill("admin123")
    page.get_by_role("button", name="Sign in").click()

    # 验证登录成功
    assert page.get_by_test_id("user-menu").is_visible()

def test_search(page):
    """测试搜索功能"""
    page.goto("https://example.com")
    page.get_by_placeholder("Search...").fill("Python")
    page.get_by_role("button", name="Search").click()

    # 验证搜索结果
    assert page.get_by_text("Python").count() > 0
```

#### `async_page` - 异步页面实例

**Scope**: `function`
**版本**: v4.0.0+

异步 Playwright 页面实例，性能提升 2-3 倍。

```python
import pytest

@pytest.mark.asyncio
async def test_login(async_page):
    """测试登录功能（异步）"""
    await async_page.goto("https://example.com/login")
    await async_page.get_by_label("Username").fill("admin")
    await async_page.get_by_label("Password").fill("admin123")
    await async_page.get_by_role("button", name="Sign in").click()

    # 验证登录成功
    assert await async_page.get_by_test_id("user-menu").is_visible()
```

#### `browser` / `async_browser` - 浏览器实例

**Scope**: `function`
**版本**: v3.0.0+ / v4.0.0+

Playwright 浏览器实例，用于获取浏览器信息或创建多个上下文。

```python
def test_browser_info(browser):
    """测试浏览器信息"""
    version = browser.version
    print(f"Browser version: {version}")
```

#### `context` / `async_context` - 浏览器上下文

**Scope**: `function`
**版本**: v3.0.0+ / v4.0.0+

浏览器上下文，用于管理 cookies、存储等。

```python
def test_with_cookies(context):
    """测试带 cookies 的场景"""
    # 添加 cookies
    context.add_cookies([
        {"name": "session_id", "value": "abc123", "url": "https://example.com"}
    ])

    # 创建页面
    page = context.new_page()
    page.goto("https://example.com")
```

#### `browser_manager` / `async_browser_manager` - 浏览器管理器

**Scope**: `function`
**版本**: v3.0.0+ / v4.0.0+

完整的浏览器管理器，包含 browser、context、page。

```python
def test_with_manager(browser_manager):
    """使用浏览器管理器"""
    page = browser_manager.page
    page.goto("https://example.com")

    # 访问配置
    base_url = browser_manager.base_url
    print(f"Base URL: {base_url}")
```

**配置示例**:

```yaml
# .env 或 configs/config.yaml
WEB__BROWSER_TYPE=chromium  # chromium/firefox/webkit
WEB__HEADLESS=true
WEB__TIMEOUT=30000
WEB__VIEWPORT__width=1920
WEB__VIEWPORT__height=1080
WEB__SCREENSHOT_ON_FAILURE=true
WEB__SCREENSHOT_DIR=reports/screenshots
```

---

### 配置与运行时 Fixtures

#### `runtime` - 运行时上下文

**Scope**: `session`
**版本**: v3.37.0+

RuntimeContext 实例，包含配置、日志、事件总线等。

```python
def test_with_runtime(runtime):
    """使用运行时上下文"""
    # 访问配置
    settings = runtime.settings
    print(f"Environment: {settings.env}")

    # 访问日志
    logger = runtime.logger
    logger.info("测试开始")

    # 发布事件
    runtime.event_bus.publish("test.started", {"test_name": "example"})
```

#### `test_runtime` - 测试专用运行时

**Scope**: `function`
**版本**: v3.44.0+

带有测试专用事件作用域的 RuntimeContext，每个测试函数独立的事件隔离。

```python
def test_with_test_runtime(test_runtime):
    """使用测试专用运行时"""
    # 发布的事件只在当前测试中可见
    test_runtime.event_bus.publish("test.event", {"data": "value"})
```

---

## API 封装 Fixtures

### 自动加载机制（v3.45.0+）

框架提供 `@api_class` 和 `@actions_class` 装饰器，自动将 API 类和 Actions 类注册为 pytest fixture。

#### `@api_class` - API 类装饰器

将 BaseAPI 子类自动注册为 pytest fixture，无需手动创建 fixture 函数。

```python
# apis/user_api.py
from df_test_framework import BaseAPI, api_class

@api_class()  # 自动命名为 user_api
class UserAPI(BaseAPI):
    """用户 API 封装"""

    def get_user(self, user_id: int):
        """获取用户信息"""
        return self.get(f"/users/{user_id}")

    def create_user(self, name: str, email: str):
        """创建用户"""
        return self.post("/users", json={"name": name, "email": email})

    def update_user(self, user_id: int, **kwargs):
        """更新用户"""
        return self.put(f"/users/{user_id}", json=kwargs)

    def delete_user(self, user_id: int):
        """删除用户"""
        return self.delete(f"/users/{user_id}")
```

**在测试中使用**:

```python
# tests/test_user.py
def test_user_crud(user_api):
    """测试用户 CRUD 操作"""
    # 创建用户
    response = user_api.create_user("张三", "zhangsan@example.com")
    assert response.status_code == 201
    user_id = response.json()["id"]

    # 获取用户
    response = user_api.get_user(user_id)
    assert response.status_code == 200
    assert response.json()["name"] == "张三"

    # 更新用户
    response = user_api.update_user(user_id, name="李四")
    assert response.status_code == 200

    # 删除用户
    response = user_api.delete_user(user_id)
    assert response.status_code == 204
```

**配置自动加载**:

```python
# conftest.py
from df_test_framework.testing.decorators import load_api_fixtures

# 自动导入 apis 包下所有模块，无需手动 import
load_api_fixtures(globals(), apis_package="myproject.apis")
```

#### `@actions_class` - Actions 类装饰器

将 AppActions 子类自动注册为 pytest fixture，用于 UI 测试。

```python
# actions/login_actions.py
from df_test_framework import AppActions, actions_class

@actions_class()  # 自动命名为 login_actions
class LoginActions(AppActions):
    """登录相关操作"""

    def login_as_admin(self):
        """以管理员身份登录"""
        self.goto("/login")
        self.page.get_by_label("Username").fill("admin")
        self.page.get_by_label("Password").fill("admin123")
        self.page.get_by_role("button", name="Sign in").click()

    def login_as_user(self, username: str, password: str):
        """以普通用户身份登录"""
        self.goto("/login")
        self.page.get_by_label("Username").fill(username)
        self.page.get_by_label("Password").fill(password)
        self.page.get_by_role("button", name="Sign in").click()

    def logout(self):
        """退出登录"""
        self.page.get_by_test_id("user-menu").click()
        self.page.get_by_role("menuitem", name="Logout").click()
```

**在测试中使用**:

```python
# tests/test_login.py
def test_admin_login(login_actions):
    """测试管理员登录"""
    login_actions.login_as_admin()
    assert login_actions.page.get_by_test_id("user-menu").is_visible()

def test_user_login(login_actions):
    """测试普通用户登录"""
    login_actions.login_as_user("user1", "password123")
    assert login_actions.page.get_by_test_id("user-menu").is_visible()
```

**配置自动加载**:

```python
# conftest.py
from df_test_framework.testing.decorators import load_actions_fixtures

# 自动导入 actions 包下所有模块
load_actions_fixtures(globals(), actions_package="myproject.actions")
```

---

## 数据管理 Fixtures

### `uow` - Unit of Work

**Scope**: `function`
**版本**: v3.7.0+

Unit of Work 模式，管理事务边界和 Repository 生命周期。测试结束后自动回滚（默认）。

```python
def test_with_uow(uow):
    """使用 UnitOfWork 管理事务"""
    # 获取 Repository
    user_repo = uow.users  # 自动创建 UserRepository

    # 创建用户
    user = User(name="张三", email="zhangsan@example.com")
    user_repo.add(user)

    # 提交事务
    uow.commit()

    # 验证
    assert user.id is not None
```

**保留测试数据**:

```python
# 方式1: 使用 @pytest.mark.keep_data 标记
@pytest.mark.keep_data
def test_create_user(uow):
    """测试创建用户（保留数据）"""
    user_repo = uow.users
    user = User(name="测试用户", email="test@example.com")
    user_repo.add(user)
    uow.commit()

# 方式2: 命令行参数
# pytest tests/ --keep-test-data

# 方式3: .env 配置
# KEEP_TEST_DATA=1
```

### `cleanup` - 数据清理管理器

**Scope**: `function`
**版本**: v3.11.0+

配置驱动的数据清理管理器，测试结束后自动清理数据。

```python
def test_with_cleanup(cleanup, database):
    """使用 cleanup 管理数据清理"""
    # 创建订单
    order_no = "ORD20260117001"
    database.insert("orders", {"order_no": order_no, "status": 0})

    # 注册清理
    cleanup.add("orders", order_no)

    # 测试逻辑...
    # 测试结束后自动清理 orders 表中的数据
```

**配置驱动清理**:

```yaml
# .env 或 configs/config.yaml
CLEANUP__ENABLED=true
CLEANUP__MAPPINGS__orders__table=card_order
CLEANUP__MAPPINGS__orders__field=customer_order_no
CLEANUP__MAPPINGS__cards__table=card_inventory
CLEANUP__MAPPINGS__cards__field=card_no
```

```python
def test_with_config_cleanup(cleanup, database):
    """使用配置驱动清理"""
    # 创建订单
    order_no = "ORD20260117001"
    database.insert("card_order", {"customer_order_no": order_no, "status": 0})

    # 注册清理（自动映射到 card_order 表）
    cleanup.add("orders", order_no)

    # 测试结束后自动执行: DELETE FROM card_order WHERE customer_order_no = 'ORD20260117001'
```

### `prepare_data` - 数据准备（回调式）

**Scope**: `function`
**版本**: v3.15.0+

回调式数据准备 fixture，用于在测试前准备数据。

```python
def test_with_prepare_data(prepare_data, cleanup):
    """使用 prepare_data 准备测试数据"""

    def setup_test_data(uow):
        """准备测试数据"""
        user_repo = uow.users
        user = User(name="测试用户", email="test@example.com")
        user_repo.add(user)
        return user.id

    # 执行数据准备并注册清理
    user_id = prepare_data(
        setup_test_data,
        cleanup_items=[("users", user_id)]
    )

    # 测试逻辑...
    assert user_id is not None
```

### `data_preparer` - 数据准备器（上下文管理器式）

**Scope**: `function`
**版本**: v3.15.0+

上下文管理器式数据准备器，更灵活的数据准备方式。

```python
def test_with_data_preparer(data_preparer):
    """使用 data_preparer 准备测试数据"""

    with data_preparer as preparer:
        # 获取 UnitOfWork
        uow = preparer.uow

        # 创建用户
        user_repo = uow.users
        user = User(name="测试用户", email="test@example.com")
        user_repo.add(user)

        # 注册清理
        preparer.cleanup("users", user.id)

    # 测试逻辑...
    # 数据已提交，测试结束后自动清理
```

---

## Fixture Scope 说明

Pytest 支持多种 fixture scope，控制 fixture 的生命周期和共享范围。

### Scope 类型

| Scope | 生命周期 | 适用场景 | 示例 Fixture |
|-------|---------|---------|-------------|
| **session** | 整个测试会话 | 重量级资源，所有测试共享 | `http_client`, `database`, `redis_client` |
| **module** | 单个测试模块 | 模块级别共享 | 自定义模块级 fixture |
| **class** | 测试类 | 类级别共享 | 自定义类级 fixture |
| **function** | 单个测试函数 | 每个测试独立 | `page`, `uow`, `cleanup` |

### 核心 Fixtures 的 Scope

```python
# Session 级别（所有测试共享）
http_client          # session
async_http_client    # session
database             # session
async_database       # session
redis_client         # session
async_redis_client   # session
runtime              # session

# Function 级别（每个测试独立）
test_runtime         # function
page                 # function
async_page           # function
browser              # function
context              # function
uow                  # function
cleanup              # function
prepare_data         # function
data_preparer        # function

# 自动加载的 Fixtures
user_api             # session（默认，@api_class）
login_actions        # function（默认，@actions_class）
```

### 选择合适的 Scope

**使用 session scope 的场景**:
- HTTP 客户端（无状态，可复用）
- 数据库连接池（重量级资源）
- Redis 连接（可复用）
- API 封装类（无状态）

**使用 function scope 的场景**:
- UI 测试（需要隔离，避免状态污染）
- 事务管理（UoW，每个测试独立事务）
- 数据清理（每个测试独立清理）
- 测试数据准备（每个测试独立数据）

---

## 自定义 Fixtures

### 创建自定义 Fixture

在项目的 `conftest.py` 中创建自定义 fixture。

```python
# conftest.py
import pytest

@pytest.fixture
def test_user(database):
    """创建测试用户 fixture"""
    # Setup: 创建测试用户
    user_id = database.insert("users", {
        "name": "测试用户",
        "email": "test@example.com",
        "status": 1
    })

    yield user_id

    # Teardown: 清理测试用户
    database.delete("users", {"id": user_id})

@pytest.fixture
def authenticated_client(http_client, test_user):
    """创建已认证的 HTTP 客户端"""
    # 登录获取 token
    response = http_client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    token = response.json()["token"]

    # 设置认证头
    http_client.headers["Authorization"] = f"Bearer {token}"

    yield http_client

    # 清理认证头
    http_client.headers.pop("Authorization", None)
```

### 使用自定义 Fixture

```python
def test_get_profile(authenticated_client):
    """测试获取用户资料（需要认证）"""
    response = authenticated_client.get("/users/profile")
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
```

### Fixture 组合

```python
@pytest.fixture
def order_test_data(database, test_user, cleanup):
    """创建订单测试数据"""
    # 创建订单
    order_no = "ORD20260117001"
    order_id = database.insert("orders", {
        "order_no": order_no,
        "user_id": test_user,
        "status": 0,
        "amount": 100.00
    })

    # 注册清理
    cleanup.add("orders", order_no)

    return {
        "order_id": order_id,
        "order_no": order_no,
        "user_id": test_user
    }

def test_order_payment(order_test_data, http_client):
    """测试订单支付"""
    order_no = order_test_data["order_no"]
    response = http_client.post(f"/orders/{order_no}/pay", json={
        "payment_method": "alipay"
    })
    assert response.status_code == 200
```

---

## 最佳实践

### 1. 优先使用框架提供的 Fixtures

框架提供的 fixtures 经过充分测试和优化，应优先使用。

```python
# ✅ 推荐：使用框架 fixture
def test_api(http_client):
    response = http_client.get("/users/1")
    assert response.status_code == 200

# ❌ 不推荐：手动创建客户端
def test_api():
    from df_test_framework import HttpClient
    client = HttpClient("https://api.example.com")
    response = client.get("/users/1")
    assert response.status_code == 200
```

### 2. 合理设置 Fixture Scope

根据资源特性选择合适的 scope，避免不必要的资源创建。

```python
# ✅ 推荐：重量级资源使用 session scope
@pytest.fixture(scope="session")
def database_connection():
    conn = create_connection()
    yield conn
    conn.close()

# ✅ 推荐：需要隔离的资源使用 function scope
@pytest.fixture(scope="function")
def clean_database(database):
    yield database
    database.execute("TRUNCATE TABLE test_data")
```

### 3. 使用 yield 进行资源清理

使用 yield 确保资源在测试后正确释放。

```python
@pytest.fixture
def temp_file():
    """创建临时文件"""
    import tempfile

    # Setup
    f = tempfile.NamedTemporaryFile(delete=False)
    f.write(b"test data")
    f.close()

    yield f.name

    # Teardown
    import os
    os.unlink(f.name)
```

### 4. 避免 Fixture 之间的强依赖

保持 fixture 的独立性，避免复杂的依赖链。

```python
# ✅ 推荐：独立的 fixture
@pytest.fixture
def user_data():
    return {"name": "张三", "email": "zhangsan@example.com"}

@pytest.fixture
def order_data():
    return {"order_no": "ORD001", "amount": 100.00}

# ❌ 不推荐：过度依赖
@pytest.fixture
def complex_data(user_data, order_data, payment_data, shipping_data):
    # 依赖过多，难以维护
    pass
```

### 5. 使用装饰器自动注册 API/Actions

利用 `@api_class` 和 `@actions_class` 简化 fixture 创建。

```python
# ✅ 推荐：使用装饰器
@api_class()
class UserAPI(BaseAPI):
    def get_user(self, user_id: int):
        return self.get(f"/users/{user_id}")

# 测试中直接使用
def test_get_user(user_api):
    response = user_api.get_user(1)
    assert response.status_code == 200

# ❌ 不推荐：手动创建 fixture
@pytest.fixture
def user_api(http_client):
    return UserAPI(http_client)
```

### 6. 合理使用数据清理

根据测试需求选择合适的数据清理策略。

```python
# 开发调试：保留数据
@pytest.mark.keep_data
def test_create_order(database):
    order_id = database.insert("orders", {...})
    # 数据保留，便于调试

# 正常测试：自动清理
def test_create_order(cleanup, database):
    order_id = database.insert("orders", {...})
    cleanup.add("orders", order_id)
    # 测试结束后自动清理
```

### 7. 异步优先（v4.0.0+）

对于高并发场景，优先使用异步 fixtures。

```python
# ✅ 推荐：异步模式（高性能）
@pytest.mark.asyncio
async def test_concurrent_requests(async_http_client):
    import asyncio
    tasks = [async_http_client.get(f"/users/{i}") for i in range(100)]
    responses = await asyncio.gather(*tasks)
    assert all(r.status_code == 200 for r in responses)

# ⚠️ 同步模式（简单场景）
def test_single_request(http_client):
    response = http_client.get("/users/1")
    assert response.status_code == 200
```

---

## 常见问题

### Q1: 如何在测试中获取配置信息？

使用 `runtime` fixture 访问配置。

```python
def test_with_config(runtime):
    settings = runtime.settings
    print(f"Environment: {settings.env}")
    print(f"Base URL: {settings.http.base_url}")
```

### Q2: 如何在 UI 测试中使用自定义 base_url？

通过配置文件设置 `WEB__BASE_URL`。

```yaml
# .env
WEB__BASE_URL=https://example.com
```

```python
def test_navigation(page):
    # 使用相对路径，自动拼接 base_url
    page.goto("/login")  # 实际访问 https://example.com/login
```

### Q3: 如何调试时保留测试数据？

使用 `--keep-test-data` 参数或 `@pytest.mark.keep_data` 标记。

```bash
# 命令行方式
pytest tests/ --keep-test-data

# 或在 .env 中配置
KEEP_TEST_DATA=1
```

```python
# 标记方式
@pytest.mark.keep_data
def test_debug(database):
    # 测试数据将被保留
    pass
```

### Q4: 如何在异步测试中使用 fixtures？

使用 `@pytest.mark.asyncio` 装饰器和异步 fixtures。

```python
import pytest

@pytest.mark.asyncio
async def test_async(async_http_client, async_database):
    response = await async_http_client.get("/users/1")
    users = await async_database.query_all("SELECT * FROM users")
    assert len(users) > 0
```

### Q5: 如何组合多个 API 类？

在测试中同时注入多个 API fixture。

```python
def test_user_order_flow(user_api, order_api):
    # 创建用户
    user_response = user_api.create_user("张三", "zhangsan@example.com")
    user_id = user_response.json()["id"]

    # 创建订单
    order_response = order_api.create_order(user_id, "Product A")
    assert order_response.status_code == 201
```

---

## 相关文档

### 核心功能指南

- [HTTP 客户端使用指南](./http_client_guide.md) - HttpClient 和 AsyncHttpClient 详细说明
- [数据库访问指南](./database_guide.md) - Database、AsyncDatabase、Repository、UoW
- [Web UI 测试指南](./web-ui-testing.md) - Playwright UI 测试完整指南
- [异步 API 指南](./async_api_guide.md) - 异步 HTTP 客户端使用
- [异步数据库指南](./async_database_guide.md) - 异步数据库客户端使用

### 高级功能指南

- [Repository & UoW 指南](./repository_uow_guide.md) - 领域模型和事务管理
- [中间件使用指南](./middleware_guide.md) - HTTP 中间件系统
- [事件总线指南](./event_bus_guide.md) - 事件驱动架构
- [测试数据管理](./test_data.md) - 测试数据生成和管理
- [测试数据清理](./test_data_cleanup.md) - 数据清理策略

### 配置和工具

- [环境配置指南](./env_config_guide.md) - 配置文件和环境变量
- [脚手架 CLI 指南](./scaffold_cli_guide.md) - 项目初始化和代码生成

---

## 快速参考

### 核心 Fixtures 速查表

| Fixture | Scope | 版本 | 说明 |
|---------|-------|------|------|
| `http_client` | session | v2.0.0+ | 同步 HTTP 客户端 |
| `async_http_client` | session | v4.0.0+ | 异步 HTTP 客户端 |
| `database` | session | v2.0.0+ | 同步数据库客户端 |
| `async_database` | session | v4.0.0+ | 异步数据库客户端 |
| `redis_client` | session | v3.0.0+ | 同步 Redis 客户端 |
| `async_redis_client` | session | v4.0.0+ | 异步 Redis 客户端 |
| `page` | function | v3.0.0+ | 同步 Playwright 页面 |
| `async_page` | function | v4.0.0+ | 异步 Playwright 页面 |
| `browser` | function | v3.0.0+ | 同步浏览器实例 |
| `context` | function | v3.0.0+ | 同步浏览器上下文 |
| `runtime` | session | v3.37.0+ | 运行时上下文 |
| `test_runtime` | function | v3.44.0+ | 测试专用运行时 |
| `uow` | function | v3.7.0+ | Unit of Work |
| `cleanup` | function | v3.11.0+ | 数据清理管理器 |
| `prepare_data` | function | v3.15.0+ | 数据准备（回调式） |
| `data_preparer` | function | v3.15.0+ | 数据准备器（上下文式） |

### 装饰器速查表

| 装饰器 | 用途 | 默认 Scope | 版本 |
|--------|------|-----------|------|
| `@api_class()` | API 类自动注册 | session | v3.45.0+ |
| `@actions_class()` | Actions 类自动注册 | function | v3.45.0+ |
| `@pytest.mark.keep_data` | 保留测试数据 | - | v3.11.0+ |
| `@pytest.mark.asyncio` | 异步测试标记 | - | pytest-asyncio |

---

## 版本历史

- **v4.0.0** (2026-01-16): 全面异步化，新增 `async_http_client`、`async_database`、`async_redis_client`、`async_page` 等异步 fixtures
- **v3.45.0** (2025-12): 新增 `@api_class` 和 `@actions_class` 装饰器，API/Actions 自动加载
- **v3.44.0** (2025-11): 新增 `test_runtime` fixture，测试专用事件作用域
- **v3.37.0** (2025-10): 新增 `runtime` fixture
- **v3.18.0** (2025-09): 配置驱动清理管理器
- **v3.15.0** (2025-08): 新增 `prepare_data` 和 `data_preparer` fixtures
- **v3.11.0** (2025-07): 新增 `cleanup` fixture，统一数据清理
- **v3.7.0** (2025-06): 新增 `uow` fixture，Repository 和 UnitOfWork 支持
- **v3.0.0** (2025-05): 新增 UI 测试 fixtures（`page`、`browser`、`context`）
- **v2.0.0** (2025-04): 核心 fixtures（`http_client`、`database`）

---

## 总结

DF Test Framework 提供了丰富的 pytest fixtures，覆盖了测试自动化的各个方面：

1. **HTTP 测试**: `http_client`、`async_http_client` - 同步/异步 HTTP 客户端
2. **数据库测试**: `database`、`async_database`、`uow` - 数据库访问和事务管理
3. **UI 测试**: `page`、`async_page`、`browser`、`context` - Playwright UI 自动化
4. **数据管理**: `cleanup`、`prepare_data`、`data_preparer` - 测试数据准备和清理
5. **配置管理**: `runtime`、`test_runtime` - 运行时上下文和配置访问

通过合理使用这些 fixtures，可以大幅简化测试代码，提高测试效率和可维护性。

**推荐实践**:
- 优先使用框架提供的 fixtures
- 合理设置 fixture scope
- 使用 `@api_class` 和 `@actions_class` 简化 fixture 创建
- v4.0.0+ 优先使用异步 fixtures 提升性能
- 使用 `cleanup` 和 `uow` 管理测试数据

---

**文档维护**: 如有问题或建议，请提交 Issue 或 PR。
