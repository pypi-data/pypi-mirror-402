# AsyncBaseAPI 使用指南

> **框架版本**: v4.0.0
> **更新日期**: 2026-01-16
> **最低版本要求**: v4.0.0+

## 概述

`AsyncBaseAPI` 是 v4.0.0 新增的全异步 API 基类，提供与 `BaseAPI` 完全对应的异步接口。在并发测试场景下，性能提升可达 **30 倍**。

## 核心优势

| 特性 | AsyncBaseAPI | BaseAPI |
|------|-------------|---------|
| **性能** | ⚡ 并发100请求 1秒 | 30秒 |
| **语法** | `await self.get()` | `self.get()` |
| **并发支持** | ✅ 原生支持 | ❌ 不支持 |
| **适用场景** | 高并发测试 | 普通测试 |
| **学习成本** | async/await | 更低 |

## 快速开始

### 1. 定义 API 类

```python
from df_test_framework.capabilities.clients.http import AsyncBaseAPI
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str

class UserAPI(AsyncBaseAPI):
    """用户 API（异步版本）"""

    async def create_user(self, user_data: dict) -> User:
        """创建用户"""
        response = await self.post("/users", json=user_data)
        return User(**response)

    async def get_user(self, user_id: int) -> User:
        """获取用户"""
        response = await self.get(f"/users/{user_id}")
        return User(**response)

    async def list_users(self, page: int = 1, size: int = 10) -> list[User]:
        """获取用户列表"""
        response = await self.get("/users", params={"page": page, "size": size})
        return [User(**u) for u in response["items"]]

    async def update_user(self, user_id: int, user_data: dict) -> User:
        """更新用户"""
        response = await self.put(f"/users/{user_id}", json=user_data)
        return User(**response)

    async def delete_user(self, user_id: int) -> None:
        """删除用户"""
        await self.delete(f"/users/{user_id}")
```

### 2. 在测试中使用

```python
import pytest

@pytest.mark.asyncio
async def test_user_lifecycle(async_http_client):
    """测试用户完整生命周期"""
    # 创建 API 实例
    api = UserAPI(async_http_client)

    # 创建用户
    user = await api.create_user({
        "name": "Alice",
        "email": "alice@example.com"
    })
    assert user.name == "Alice"

    # 获取用户
    fetched_user = await api.get_user(user.id)
    assert fetched_user.id == user.id

    # 更新用户
    updated_user = await api.update_user(user.id, {
        "name": "Alice Updated"
    })
    assert updated_user.name == "Alice Updated"

    # 删除用户
    await api.delete_user(user.id)
```

### 3. 并发测试（性能提升 30 倍）

```python
import asyncio
import pytest

@pytest.mark.asyncio
async def test_concurrent_user_creation(async_http_client):
    """并发创建 100 个用户"""
    api = UserAPI(async_http_client)

    # 准备 100 个用户数据
    user_data_list = [
        {"name": f"User{i}", "email": f"user{i}@example.com"}
        for i in range(100)
    ]

    # 并发创建（性能提升 30 倍）
    tasks = [api.create_user(data) for data in user_data_list]
    users = await asyncio.gather(*tasks)

    assert len(users) == 100
    assert all(isinstance(u, User) for u in users)
```

## 核心功能

### 1. HTTP 方法

所有 HTTP 方法都是异步的，需要使用 `await`:

```python
class MyAPI(AsyncBaseAPI):
    async def example_methods(self):
        # GET 请求
        data = await self.get("/endpoint")

        # POST 请求
        data = await self.post("/endpoint", json={"key": "value"})

        # PUT 请求
        data = await self.put("/endpoint/1", json={"key": "value"})

        # PATCH 请求
        data = await self.patch("/endpoint/1", json={"key": "value"})

        # DELETE 请求
        await self.delete("/endpoint/1")

        # HEAD 请求
        headers = await self.head("/endpoint")

        # OPTIONS 请求
        options = await self.options("/endpoint")
```

### 2. Pydantic 模型支持

与同步版本一样，完整支持 Pydantic 模型：

```python
from pydantic import BaseModel

class CreateUserRequest(BaseModel):
    name: str
    email: str
    age: int

class User(BaseModel):
    id: int
    name: str
    email: str
    age: int

class UserAPI(AsyncBaseAPI):
    async def create_user(self, req: CreateUserRequest) -> User:
        # 自动序列化 Pydantic 模型
        response = await self.post("/users", json=req)
        # 自动反序列化为 Pydantic 模型
        return User(**response)

# 使用
@pytest.mark.asyncio
async def test_pydantic_support(async_http_client):
    api = UserAPI(async_http_client)

    req = CreateUserRequest(name="Bob", email="bob@example.com", age=25)
    user = await api.create_user(req)

    assert isinstance(user, User)
    assert user.name == "Bob"
```

### 3. 认证控制

完整支持认证控制，与同步版本一致：

```python
class SecureAPI(AsyncBaseAPI):
    async def public_endpoint(self):
        """公开接口，跳过认证"""
        return await self.get("/public", skip_auth=True)

    async def admin_endpoint(self, admin_token: str):
        """管理员接口，使用特定 token"""
        return await self.get("/admin", token=admin_token)

    async def user_endpoint(self):
        """用户接口，使用默认认证"""
        return await self.get("/user")
```

### 4. 文件上传

完整支持文件上传：

```python
class FileAPI(AsyncBaseAPI):
    async def upload_avatar(self, user_id: int, file_path: str):
        """上传用户头像"""
        with open(file_path, "rb") as f:
            files = {"avatar": f}
            return await self.post(
                f"/users/{user_id}/avatar",
                files=files
            )

    async def upload_multiple_files(self, files_dict: dict):
        """上传多个文件"""
        return await self.post("/upload", files=files_dict)
```

### 5. 查询参数

支持多种查询参数格式：

```python
class SearchAPI(AsyncBaseAPI):
    async def search_users(
        self,
        keyword: str,
        filters: dict | None = None,
        page: int = 1,
        size: int = 10
    ):
        """搜索用户"""
        params = {
            "q": keyword,
            "page": page,
            "size": size,
        }
        if filters:
            params.update(filters)

        return await self.get("/users/search", params=params)
```

## 高级用法

### 1. 并发请求 + 错误处理

```python
import asyncio

@pytest.mark.asyncio
async def test_concurrent_with_error_handling(async_http_client):
    api = UserAPI(async_http_client)

    async def create_user_safe(data):
        """安全的创建用户（带错误处理）"""
        try:
            return await api.create_user(data)
        except Exception as e:
            print(f"创建失败: {e}")
            return None

    # 并发创建，部分可能失败
    tasks = [
        create_user_safe({"name": f"User{i}", "email": f"user{i}@example.com"})
        for i in range(100)
    ]
    results = await asyncio.gather(*tasks)

    # 过滤成功的结果
    successful_users = [r for r in results if r is not None]
    print(f"成功创建 {len(successful_users)} 个用户")
```

### 2. 依赖链调用

```python
@pytest.mark.asyncio
async def test_dependent_api_calls(async_http_client):
    """测试有依赖关系的 API 调用"""
    api = UserAPI(async_http_client)

    # Step 1: 创建用户
    user = await api.create_user({
        "name": "Charlie",
        "email": "charlie@example.com"
    })

    # Step 2: 基于用户ID，创建订单（假设有 OrderAPI）
    order_api = OrderAPI(async_http_client)
    order = await order_api.create_order({
        "user_id": user.id,
        "items": ["item1", "item2"]
    })

    # Step 3: 验证用户订单
    user_orders = await order_api.get_user_orders(user.id)
    assert order.id in [o.id for o in user_orders]
```

### 3. 批量操作优化

```python
@pytest.mark.asyncio
async def test_batch_operations(async_http_client):
    """批量操作优化"""
    api = UserAPI(async_http_client)

    # 批量创建
    create_tasks = [
        api.create_user({"name": f"User{i}", "email": f"user{i}@example.com"})
        for i in range(50)
    ]
    users = await asyncio.gather(*create_tasks)

    # 批量更新（并发）
    update_tasks = [
        api.update_user(u.id, {"name": f"{u.name} Updated"})
        for u in users
    ]
    updated_users = await asyncio.gather(*update_tasks)

    # 批量删除（并发）
    delete_tasks = [api.delete_user(u.id) for u in updated_users]
    await asyncio.gather(*delete_tasks)
```

## Fixture 使用

### async_http_client fixture

框架提供 `async_http_client` fixture，自动管理生命周期：

```python
@pytest.mark.asyncio
async def test_with_fixture(async_http_client):
    """使用 async_http_client fixture"""
    api = UserAPI(async_http_client)

    # fixture 会自动处理：
    # - base_url 配置
    # - 认证中间件
    # - EventBus 事件发布
    # - 资源清理

    user = await api.create_user({
        "name": "Dave",
        "email": "dave@example.com"
    })
    assert user.name == "Dave"
```

### 自定义 API fixture

创建项目专用的 API fixture：

```python
# conftest.py
import pytest

@pytest.fixture
async def user_api(async_http_client):
    """用户 API fixture"""
    return UserAPI(async_http_client)

@pytest.fixture
async def order_api(async_http_client):
    """订单 API fixture"""
    return OrderAPI(async_http_client)

# 测试文件
@pytest.mark.asyncio
async def test_with_custom_fixtures(user_api, order_api):
    """使用自定义 API fixtures"""
    user = await user_api.create_user({
        "name": "Eve",
        "email": "eve@example.com"
    })

    order = await order_api.create_order({
        "user_id": user.id,
        "items": ["item1"]
    })

    assert order.user_id == user.id
```

## 性能对比

### 顺序执行 vs 并发执行

```python
import time
import asyncio

# ❌ 顺序执行（慢）
def test_sequential():
    api = UserAPI(http_client)  # 同步版本
    start = time.time()

    for i in range(100):
        api.create_user({"name": f"User{i}", "email": f"user{i}@example.com"})

    print(f"顺序执行: {time.time() - start:.2f}秒")  # ~30秒

# ✅ 并发执行（快 30 倍）
@pytest.mark.asyncio
async def test_concurrent():
    api = UserAPI(async_http_client)  # 异步版本
    start = time.time()

    tasks = [
        api.create_user({"name": f"User{i}", "email": f"user{i}@example.com"})
        for i in range(100)
    ]
    await asyncio.gather(*tasks)

    print(f"并发执行: {time.time() - start:.2f}秒")  # ~1秒 ⚡
```

## 最佳实践

### 1. 优先使用异步（高并发场景）

```python
# ✅ 推荐：高并发场景使用异步
@pytest.mark.asyncio
async def test_high_concurrency(async_http_client):
    api = UserAPI(async_http_client)
    tasks = [api.get_user(i) for i in range(1000)]
    users = await asyncio.gather(*tasks)  # 性能提升 30 倍
```

### 2. 同步/异步混用（渐进式迁移）

```python
# 新测试使用异步
@pytest.mark.asyncio
async def test_new_feature(async_http_client):
    api = UserAPI(async_http_client)
    # ...

# 旧测试保持同步（无需修改）
def test_old_feature(http_client):
    api = UserAPI(http_client)  # 使用同步版本
    # ...
```

### 3. 合理控制并发数

```python
import asyncio

@pytest.mark.asyncio
async def test_controlled_concurrency(async_http_client):
    """控制并发数，避免压垮服务器"""
    api = UserAPI(async_http_client)

    # 使用 Semaphore 控制并发数
    semaphore = asyncio.Semaphore(10)  # 最多10个并发

    async def create_user_with_limit(data):
        async with semaphore:
            return await api.create_user(data)

    tasks = [
        create_user_with_limit({"name": f"User{i}", "email": f"user{i}@example.com"})
        for i in range(100)
    ]
    users = await asyncio.gather(*tasks)
```

## 迁移指南

### 从 BaseAPI 迁移到 AsyncBaseAPI

只需要三步：

```python
# Step 1: 修改基类
- class UserAPI(BaseAPI):
+ class UserAPI(AsyncBaseAPI):

# Step 2: 方法加 async
-     def create_user(self, data):
+     async def create_user(self, data):

# Step 3: 调用加 await
-         return self.post("/users", json=data)
+         return await self.post("/users", json=data)
```

**完整示例**:

```python
# v3.x (同步)
class UserAPI(BaseAPI):
    def create_user(self, data):
        return self.post("/users", json=data)

    def get_user(self, user_id):
        return self.get(f"/users/{user_id}")

# v4.0.0 (异步)
class UserAPI(AsyncBaseAPI):
    async def create_user(self, data):
        return await self.post("/users", json=data)

    async def get_user(self, user_id):
        return await self.get(f"/users/{user_id}")
```

## 常见问题

### Q1: 什么时候使用异步？

**A**: 推荐在以下场景使用异步：

- ✅ **高并发测试**: 需要同时发起大量请求
- ✅ **性能测试**: 需要测试系统在高负载下的表现
- ✅ **压力测试**: 需要模拟大量用户并发访问
- ❌ **简单测试**: 单个请求的简单测试，同步即可

### Q2: 异步会增加复杂度吗？

**A**: 略有增加，但收益远大于成本：

- **学习成本**: 需要理解 async/await（1-2 小时）
- **代码变化**: 只需添加 `async` 和 `await` 关键字
- **性能收益**: 30 倍性能提升 ⚡

### Q3: 能同时使用同步和异步吗？

**A**: 完全可以！这是渐进式迁移的核心优势：

```python
# 同步测试（v3.x 保留）
def test_simple(http_client):
    api = UserAPI(http_client)
    user = api.get_user(1)

# 异步测试（v4.0.0 新增）
@pytest.mark.asyncio
async def test_concurrent(async_http_client):
    api = UserAPI(async_http_client)
    users = await asyncio.gather(*[api.get_user(i) for i in range(100)])
```

### Q4: pytest 如何运行异步测试？

**A**: 使用 `pytest-asyncio` 插件（框架已集成）：

```python
# 安装（框架已包含）
pip install pytest-asyncio

# 测试文件中使用
@pytest.mark.asyncio
async def test_example():
    # 异步测试代码
    pass
```

## 相关文档

- [AsyncHttpClient 使用指南](./async_http_client.md) - 底层 HTTP 客户端
- [v3 to v4 迁移指南](../migration/v3-to-v4.md) - 完整迁移步骤
- [v4.0.0 发布说明](../releases/v4.0.0.md) - 版本详细信息
- [EventBus 使用指南](./event_bus_guide.md) - 事件总线集成

## 总结

AsyncBaseAPI 为 v4.0.0 带来了：

- ⚡ **30 倍性能提升** - 并发请求场景
- 🔄 **完全兼容** - 与 BaseAPI API 对应
- 🎯 **渐进式迁移** - 可逐步升级
- 🛠️ **完整功能** - Pydantic、认证、文件上传全支持

**立即开始使用异步 API，享受性能飞跃！**🚀
