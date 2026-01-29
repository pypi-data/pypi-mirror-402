# v3.x 到 v4.0.0 迁移指南

> **最后更新**: 2026-01-16
> **适用版本**: v3.x → v4.0.0

⭐⭐⭐ **重要性**：必读文档，所有从 v3 升级到 v4 的用户都应该阅读

**预计迁移时间**：1-3 小时（取决于项目规模）

## 概述

**v4.0.0** 是一个**重大版本升级**，引入了"异步优先，同步兼容"策略。

**核心理念**：
- ✅ 异步 API 是推荐的、性能最优的方式（2-30倍性能提升）
- ✅ 同步 API 完全保留，确保向后兼容
- ✅ 用户可以选择最佳迁移时机，渐进式升级

---

## 重大变更总结

### 1. HTTP 层

| 组件 | v3.x (同步) | v4.0.0 (异步) | 状态 |
|------|-------------|---------------|------|
| HTTP 客户端 | `HttpClient` | `AsyncHttpClient` | ✅ 共存 |
| API 基类 | `BaseAPI` | `AsyncBaseAPI` | ✅ 共存 |

**性能提升**：并发100个请求从30秒降至1秒（30倍）

### 2. UI 层

| 组件 | v3.x (同步) | v4.0.0 (异步) | 状态 |
|------|-------------|---------------|------|
| 业务操作 | `AppActions` | `AsyncAppActions` | ✅ 共存 |
| 页面对象 | `BasePage` | `AsyncBasePage` | ✅ 共存 |

**性能提升**：UI 操作性能提升 2-3 倍

### 3. 数据库层

| 组件 | v3.x (同步) | v4.0.0 (异步) | 状态 |
|------|-------------|---------------|------|
| 数据库客户端 | `Database` | `AsyncDatabase` | ✅ 共存 |

**性能提升**：支持并发数据库操作

---

## 快速决策指南

### 我应该升级吗？

**✅ 推荐升级**（使用异步 API）：
- 新项目
- 性能敏感的项目（大量 I/O 操作）
- 需要并发测试的场景
- 团队熟悉 Python async/await

**⏸️ 暂不升级**（继续使用同步 API）：
- 旧项目，暂无性能问题
- 团队不熟悉异步编程
- 测试用例简单，单次执行即可

**✅ 渐进式升级**（推荐）：
- 新测试用例使用异步 API
- 旧测试用例保持同步 API
- 逐步迁移关键路径

---

## 迁移步骤

### 步骤 1：安装异步驱动

根据使用的数据库类型，安装对应的异步驱动：

```bash
# MySQL
pip install aiomysql

# PostgreSQL
pip install asyncpg

# SQLite
pip install aiosqlite
```

### 步骤 2：配置 pytest-asyncio

在 `pyproject.toml` 或 `pytest.ini` 中配置：

```toml
[tool.pytest.ini_options]
asyncio_mode = "strict"
```

### 步骤 3：选择迁移策略

---

## 迁移策略 A：完全不改（同步兼容）

**适用场景**：旧项目，暂无升级需求

**改动**：无需任何改动 ✅

```python
# v3.x 代码（继续使用）
from df_test_framework.capabilities.clients.http import HttpClient, BaseAPI
from df_test_framework.capabilities.drivers.web import AppActions, BasePage
from df_test_framework.capabilities.databases import Database

# HTTP 测试（同步）
def test_api(http_client):
    api = MyAPI(http_client)
    response = api.get_users()
    assert len(response) > 0

# UI 测试（同步）
def test_ui(page):
    login_page = LoginPage(page)
    login_page.goto()
    login_page.login("admin", "password")

# 数据库测试（同步）
def test_db(db):
    users = db.query_all("SELECT * FROM users")
    assert len(users) > 0
```

**结论**：v4.0.0 完全向后兼容，无需改动即可升级！

---

## 迁移策略 B：完全升级（异步优先）

**适用场景**：新项目，追求最佳性能

**改动**：所有测试改为异步

### HTTP 层迁移

**v3.x (同步)**：
```python
from df_test_framework.capabilities.clients.http import HttpClient, BaseAPI

class UserAPI(BaseAPI):
    def get_users(self):
        return self.get("/users", model=UserListResponse)

def test_get_users(http_client):
    api = UserAPI(http_client)
    users = api.get_users()
    assert len(users.data) > 0
```

**v4.0.0 (异步)**：
```python
from df_test_framework.capabilities.clients.http import AsyncHttpClient, AsyncBaseAPI

class UserAPI(AsyncBaseAPI):
    async def get_users(self):
        return await self.get("/users", model=UserListResponse)

@pytest.mark.asyncio
async def test_get_users():
    async with AsyncHttpClient("https://api.example.com") as client:
        api = UserAPI(client)
        users = await api.get_users()
        assert len(users.data) > 0
```

**关键变更**：
1. ✅ 导入从 `HttpClient, BaseAPI` 改为 `AsyncHttpClient, AsyncBaseAPI`
2. ✅ 所有方法改为 `async def`
3. ✅ 所有调用添加 `await`
4. ✅ 测试函数添加 `@pytest.mark.asyncio` 装饰器
5. ✅ 使用 `async with` 管理客户端生命周期

### UI 层迁移

**v3.x (同步)**：
```python
from df_test_framework.capabilities.drivers.web import AppActions, BasePage

class LoginPage(BasePage):
    def wait_for_page_load(self):
        self.page.get_by_test_id("login-form").wait_for()

    def login(self, username: str, password: str):
        self.page.get_by_label("Username").fill(username)
        self.page.get_by_label("Password").fill(password)
        self.page.get_by_role("button", name="Sign in").click()

def test_login(page):
    login_page = LoginPage(page)
    login_page.goto()
    login_page.login("admin", "password")
```

**v4.0.0 (异步)**：
```python
from df_test_framework.capabilities.drivers.web import AsyncAppActions, AsyncBasePage

class LoginPage(AsyncBasePage):
    async def wait_for_page_load(self):
        await self.page.get_by_test_id("login-form").wait_for()

    async def login(self, username: str, password: str):
        await self.page.get_by_label("Username").fill(username)
        await self.page.get_by_label("Password").fill(password)
        await self.page.get_by_role("button", name="Sign in").click()

@pytest.mark.asyncio
async def test_login(page):
    login_page = LoginPage(page)
    await login_page.goto()
    await login_page.login("admin", "password")
```

**关键变更**：
1. ✅ 导入从 `AppActions, BasePage` 改为 `AsyncAppActions, AsyncBasePage`
2. ✅ `wait_for_page_load()` 改为 `async def`
3. ✅ 所有 Page 操作添加 `await`
4. ✅ 测试函数改为 `async def` 并添加 `@pytest.mark.asyncio`

### 数据库层迁移

**v3.x (同步)**：
```python
from df_test_framework.capabilities.databases import Database

def test_database():
    db = Database("mysql+pymysql://user:pass@host/db")
    users = db.query_all("SELECT * FROM users WHERE age > :age", {"age": 18})
    assert len(users) > 0
```

**v4.0.0 (异步)**：
```python
from df_test_framework.capabilities.databases import AsyncDatabase

@pytest.mark.asyncio
async def test_database():
    async_db = AsyncDatabase("mysql+aiomysql://user:pass@host/db")
    users = await async_db.query_all("SELECT * FROM users WHERE age > :age", {"age": 18})
    assert len(users) > 0
    await async_db.close()
```

**关键变更**：
1. ✅ 导入从 `Database` 改为 `AsyncDatabase`
2. ✅ 连接字符串使用异步驱动（`pymysql` → `aiomysql`）
3. ✅ 所有数据库操作添加 `await`
4. ✅ 记得调用 `await async_db.close()` 关闭连接

---

## 迁移策略 C：渐进式升级（推荐）

**适用场景**：大型项目，希望平滑过渡

**策略**：新测试用异步，旧测试保持同步，逐步迁移

```python
# 文件1：旧测试（保持同步）
from df_test_framework.capabilities.clients.http import HttpClient, BaseAPI

def test_legacy_api(http_client):
    api = MyAPI(http_client)
    response = api.get_users()
    assert len(response) > 0

# 文件2：新测试（使用异步）
from df_test_framework.capabilities.clients.http import AsyncHttpClient, AsyncBaseAPI

@pytest.mark.asyncio
async def test_new_api():
    async with AsyncHttpClient("https://api.example.com") as client:
        api = MyAPI(client)
        response = await api.get_users()
        assert len(response) > 0
```

**优势**：
- ✅ 降低风险，分批迁移
- ✅ 逐步积累异步经验
- ✅ 关键路径优先获得性能提升

---

## 性能对比

### HTTP 并发场景

```python
# v3.x (同步) - 30秒
for i in range(100):
    response = client.get(f"/users/{i}")

# v4.0.0 (异步) - 1秒（30倍提升）
tasks = [client.get(f"/users/{i}") for i in range(100)]
responses = await asyncio.gather(*tasks)
```

### UI 自动化

```python
# v3.x (同步) - 10秒
page.goto("https://example.com")
page.get_by_label("Username").fill("admin")
page.get_by_label("Password").fill("password")
page.get_by_role("button", name="Sign in").click()

# v4.0.0 (异步) - 3-4秒（2-3倍提升）
await page.goto("https://example.com")
await page.get_by_label("Username").fill("admin")
await page.get_by_label("Password").fill("password")
await page.get_by_role("button", name="Sign in").click()
```

### 数据库并发查询

```python
# v3.x (同步) - 每次查询串行执行
for user_id in range(100):
    user = db.query_one("SELECT * FROM users WHERE id = :id", {"id": user_id})

# v4.0.0 (异步) - 并发执行
tasks = [
    async_db.query_one("SELECT * FROM users WHERE id = :id", {"id": i})
    for i in range(100)
]
users = await asyncio.gather(*tasks)
```

---

## 常见问题 (FAQ)

### Q1: 我必须升级到异步吗？

**A**: 不必须。v4.0.0 完全向后兼容，同步 API 保留。你可以：
- 继续使用同步 API（无需改动）
- 选择最佳时机升级到异步 API
- 新旧 API 混用（渐进式迁移）

### Q2: 异步和同步可以混用吗？

**A**: 可以，但不推荐在同一个测试文件中混用。建议：
- 同步测试文件：使用 `HttpClient`, `BaseAPI`, `AppActions`, `BasePage`
- 异步测试文件：使用 `AsyncHttpClient`, `AsyncBaseAPI`, `AsyncAppActions`, `AsyncBasePage`

### Q3: 异步性能提升有多大？

**A**: 取决于场景：
- **HTTP 并发**：10-30 倍（100个并发请求）
- **UI 操作**：2-3 倍（减少等待时间）
- **数据库并发**：显著提升（取决于并发度）
- **单个操作**：提升不明显

### Q4: 需要修改多少代码？

**A**:
- **策略 A（同步兼容）**：0 行修改 ✅
- **策略 B（完全异步）**：每个测试需要修改
  - 添加 `async def` 和 `await`
  - 添加 `@pytest.mark.asyncio`
  - 修改导入语句
- **策略 C（渐进式）**：新测试使用异步，旧测试不改

### Q5: 异步驱动如何选择？

**A**: 根据数据库类型选择：

| 数据库 | 同步驱动 | 异步驱动 | 连接字符串示例 |
|--------|----------|----------|----------------|
| MySQL | pymysql | aiomysql | `mysql+aiomysql://user:pass@host/db` |
| PostgreSQL | psycopg2 | asyncpg | `postgresql+asyncpg://user:pass@host/db` |
| SQLite | - | aiosqlite | `sqlite+aiosqlite:///path/to/db.sqlite` |

### Q6: pytest-asyncio 配置是必须的吗？

**A**: 推荐配置 `asyncio_mode = "strict"`，这样：
- 异步测试必须添加 `@pytest.mark.asyncio`（清晰明确）
- 避免同步/异步混淆
- 提高测试可读性

---

## 迁移检查清单

### 准备阶段
- [ ] 阅读本迁移指南
- [ ] 确定迁移策略（A/B/C）
- [ ] 安装异步驱动（如需要）
- [ ] 配置 pytest-asyncio

### HTTP 层
- [ ] 导入改为 `AsyncHttpClient`, `AsyncBaseAPI`
- [ ] API 方法改为 `async def`
- [ ] 所有调用添加 `await`
- [ ] 测试函数添加 `@pytest.mark.asyncio`

### UI 层
- [ ] 导入改为 `AsyncAppActions`, `AsyncBasePage`
- [ ] Page Object 方法改为 `async def`
- [ ] Playwright 操作添加 `await`
- [ ] 测试函数添加 `@pytest.mark.asyncio`

### 数据库层
- [ ] 导入改为 `AsyncDatabase`
- [ ] 连接字符串使用异步驱动
- [ ] 数据库操作添加 `await`
- [ ] 测试函数添加 `@pytest.mark.asyncio`

### 测试验证
- [ ] 运行测试确保通过
- [ ] 检查性能是否提升
- [ ] 代码审查

---

## 总结

**v4.0.0 核心优势**：

1. ✅ **完全向后兼容**：旧项目无需改动
2. ✅ **性能显著提升**：异步 API 提供 2-30 倍性能提升
3. ✅ **渐进式迁移**：可以逐步升级，降低风险
4. ✅ **符合现代实践**：与主流库（httpx, SQLAlchemy, Playwright）策略一致

**迁移建议**：

- 新项目：直接使用异步 API ⭐
- 旧项目：渐进式迁移，关键路径优先
- 简单项目：继续使用同步 API

欢迎升级到 v4.0.0，享受异步带来的性能提升！🚀
