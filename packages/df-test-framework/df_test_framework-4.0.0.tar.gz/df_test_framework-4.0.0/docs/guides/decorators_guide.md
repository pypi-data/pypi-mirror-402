# 装饰器使用指南

> **最后更新**: 2026-01-17
> **适用版本**: v3.7.0+（通用装饰器），v3.45.0+（测试装饰器）

## 概述

DF Test Framework 提供了两类装饰器，帮助简化测试代码和增强功能：

### 测试装饰器（Testing Decorators）

用于自动注册 API 类和 UI Actions 类为 pytest fixture，无需手动创建 fixture 函数。

- **@api_class**: 自动将 BaseAPI 子类注册为 pytest fixture
- **@actions_class**: 自动将 AppActions 子类注册为 pytest fixture
- **load_api_fixtures()**: 自动加载所有 API fixtures
- **load_actions_fixtures()**: 自动加载所有 Actions fixtures

### 通用装饰器（Core Decorators）

用于增强函数功能，提供重试、日志、缓存等能力。

- **@retry_on_failure**: 失败自动重试（支持指数退避）
- **@log_execution**: 记录函数执行（参数和结果）
- **@deprecated**: 标记函数为已废弃
- **@cache_result**: 缓存函数结果（LRU 策略 + TTL）

---

## 快速开始

### 测试装饰器快速示例

```python
# apis/user_api.py
from df_test_framework import BaseAPI
from df_test_framework.testing.decorators import api_class

@api_class()  # 自动注册为 user_api fixture
class UserAPI(BaseAPI):
    def get_user(self, user_id: int):
        return self.get(f"/users/{user_id}")

# tests/test_user.py
def test_get_user(user_api):  # 直接使用，无需手动创建 fixture
    response = user_api.get_user(1)
    assert response["id"] == 1
```

### 通用装饰器快速示例

```python
from df_test_framework.core.decorators import retry_on_failure, cache_result

@retry_on_failure(max_retries=3, delay=1.0)
def unstable_api_call():
    return requests.get("https://api.example.com/data")

@cache_result(ttl=60, maxsize=100)
def expensive_calculation(n):
    return sum(range(n))
```

---

## @api_class 装饰器

> **引入版本**: v3.45.0
> **适用场景**: HTTP API 测试

### 基本用法

`@api_class` 装饰器自动将 BaseAPI 子类注册为 pytest fixture，无需手动创建 fixture 函数。

```python
from df_test_framework import BaseAPI
from df_test_framework.testing.decorators import api_class

@api_class()  # 自动命名为 user_api
class UserAPI(BaseAPI):
    def get_user(self, user_id: int):
        return self.get(f"/users/{user_id}")

    def create_user(self, data: dict):
        return self.post("/users", json=data)

    def update_user(self, user_id: int, data: dict):
        return self.put(f"/users/{user_id}", json=data)
```

### 自动命名规则

装饰器会自动将类名转换为 fixture 名称：

| 类名 | 自动生成的 fixture 名称 |
|------|------------------------|
| `UserAPI` | `user_api` |
| `MasterCardAPI` | `master_card_api` |
| `OrderManagementAPI` | `order_management_api` |

### 自定义 fixture 名称

```python
@api_class("my_custom_api")  # 指定 fixture 名称
class UserAPI(BaseAPI):
    pass

def test_example(my_custom_api):  # 使用自定义名称
    response = my_custom_api.get_user(1)
```

### 指定 Scope

```python
# Session scope（默认）- 所有测试共享同一个实例
@api_class(scope="session")
class UserAPI(BaseAPI):
    pass

# Function scope - 每个测试创建新实例
@api_class(scope="function")
class TempAPI(BaseAPI):
    pass

# Module scope - 同一模块的测试共享实例
@api_class(scope="module")
class ModuleAPI(BaseAPI):
    pass
```

### 自定义依赖注入

```python
@api_class("custom_api", http_client="http_client", settings="runtime")
class CustomAPI(BaseAPI):
    def __init__(self, http_client, settings):
        super().__init__(http_client)
        self.settings = settings
```

### 自动加载 API Fixtures

在 `conftest.py` 中使用 `load_api_fixtures()` 自动加载所有 API：

```python
# conftest.py
from df_test_framework.testing.decorators import load_api_fixtures

# 方式1: 自动发现模式（推荐）
load_api_fixtures(globals(), apis_package="myproject.apis")

# 方式2: 手动导入模式
from myproject.apis.user_api import UserAPI  # noqa: F401
from myproject.apis.order_api import OrderAPI  # noqa: F401
load_api_fixtures(globals())
```

### 在测试中使用

```python
def test_get_user(user_api):
    """直接使用 user_api fixture"""
    response = user_api.get_user(1)
    assert response["id"] == 1
    assert response["name"] == "张三"

def test_create_user(user_api):
    """创建用户"""
    data = {"name": "李四", "email": "lisi@example.com"}
    response = user_api.create_user(data)
    assert response["success"] is True

def test_multiple_apis(user_api, order_api):
    """使用多个 API"""
    user = user_api.get_user(1)
    orders = order_api.get_user_orders(user["id"])
    assert len(orders) > 0
```

---

## @actions_class 装饰器

> **引入版本**: v3.45.0
> **适用场景**: Web UI 测试

### 基本用法

`@actions_class` 装饰器自动将 AppActions 子类注册为 pytest fixture，用于 UI 测试。

```python
from df_test_framework import AppActions
from df_test_framework.testing.decorators import actions_class

@actions_class()  # 自动命名为 login_actions
class LoginActions(AppActions):
    def login_as_admin(self):
        self.goto("/login")
        self.page.get_by_label("Username").fill("admin")
        self.page.get_by_label("Password").fill("admin123")
        self.page.get_by_role("button", name="Sign in").click()

    def login_as_user(self, username: str, password: str):
        self.goto("/login")
        self.page.get_by_label("Username").fill(username)
        self.page.get_by_label("Password").fill(password)
        self.page.get_by_role("button", name="Sign in").click()
```

### 自动命名规则

装饰器会自动将类名转换为 fixture 名称：

| 类名 | 自动生成的 fixture 名称 |
|------|------------------------|
| `LoginActions` | `login_actions` |
| `OrderActions` | `order_actions` |
| `UserManagementActions` | `user_management_actions` |

### 默认 Scope

UI Actions 默认使用 `function` scope（每个测试独立），与 API 的 `session` scope 不同：

```python
# Function scope（默认）- 每个测试创建新实例
@actions_class()
class LoginActions(AppActions):
    pass

# Session scope - 所有测试共享（不推荐，可能导致状态污染）
@actions_class(scope="session")
class SharedActions(AppActions):
    pass
```

### 自动加载 Actions Fixtures

在 `conftest.py` 中使用 `load_actions_fixtures()` 自动加载所有 Actions：

```python
# conftest.py
from df_test_framework.testing.decorators import load_actions_fixtures

# 方式1: 自动发现模式（推荐）
load_actions_fixtures(globals(), actions_package="myproject.actions")

# 方式2: 手动导入模式
from myproject.actions.login_actions import LoginActions  # noqa: F401
from myproject.actions.order_actions import OrderActions  # noqa: F401
load_actions_fixtures(globals())
```

### 在测试中使用

```python
def test_admin_login(login_actions):
    """测试管理员登录"""
    login_actions.login_as_admin()
    assert login_actions.page.get_by_test_id("user-menu").is_visible()

def test_user_login(login_actions):
    """测试普通用户登录"""
    login_actions.login_as_user("zhangsan", "password123")
    assert login_actions.page.get_by_text("欢迎，张三").is_visible()

def test_order_flow(login_actions, order_actions):
    """测试订单流程（使用多个 Actions）"""
    login_actions.login_as_admin()
    order_id = order_actions.create_order("Phone")
    assert order_id is not None
```

### 与 @api_class 的对比

| 特性 | @api_class | @actions_class |
|------|-----------|----------------|
| 基类 | `BaseAPI` | `AppActions` |
| 默认 scope | `session` | `function` |
| 配置字段 | `test.apis_package` | `test.actions_package` |
| 目录约定 | `apis/` | `actions/` |
| 自动依赖 | `http_client` | `page`, `browser_manager` |

---

## 通用装饰器

> **引入版本**: v3.7.0（初始实现），v3.29.0（迁移到 core）
> **适用场景**: 增强函数功能

### @retry_on_failure - 失败重试

自动重试失败的函数调用，支持指数退避策略。

```python
from df_test_framework.core.decorators import retry_on_failure

@retry_on_failure(max_retries=3, delay=1.0, backoff=2.0)
def unstable_api_call():
    """不稳定的 API 调用"""
    response = requests.get("https://api.example.com/data")
    response.raise_for_status()
    return response.json()

# 执行流程：
# 第1次失败 -> 等待1秒 -> 第2次失败 -> 等待2秒 -> 第3次失败 -> 等待4秒 -> 抛出异常
```

**参数说明**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `max_retries` | int | 3 | 最大重试次数 |
| `delay` | float | 1.0 | 初始延迟时间（秒） |
| `backoff` | float | 2.0 | 延迟倍数（指数退避） |
| `exceptions` | tuple | (Exception,) | 需要重试的异常类型 |

**使用场景**：
- 网络请求（API 调用、数据库连接）
- 文件操作（临时锁定、权限问题）
- 外部服务调用（消息队列、缓存服务）

**自定义异常类型**：

```python
@retry_on_failure(
    max_retries=5,
    delay=0.5,
    exceptions=(requests.ConnectionError, requests.Timeout)
)
def fetch_data():
    return requests.get("https://api.example.com/data", timeout=5)
```

### @log_execution - 记录执行

自动记录函数的调用参数和返回值，方便调试和审计。

```python
from df_test_framework.core.decorators import log_execution

@log_execution(log_args=True, log_result=True)
def process_data(data: dict) -> dict:
    """处理数据"""
    return {"processed": data["value"] * 2}

# 日志输出：
# [执行] process_data - args=({'value': 10},), kwargs={}
# [完成] process_data - result={'processed': 20}
```

**参数说明**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `log_args` | bool | True | 是否记录参数 |
| `log_result` | bool | False | 是否记录返回值 |

**使用场景**：
- 调试复杂函数
- 审计关键操作
- 性能分析

**注意事项**：
- 避免记录敏感信息（密码、token）
- 大数据量时谨慎使用 `log_result=True`

### @deprecated - 标记废弃

标记函数为已废弃，调用时记录警告日志。

```python
from df_test_framework.core.decorators import deprecated

@deprecated(message="请使用 new_function 替代", version="2.0.0")
def old_function():
    """旧函数（已废弃）"""
    return "old result"

# 调用时输出：
# 函数 old_function 已废弃 (自版本 2.0.0): 请使用 new_function 替代
```

**参数说明**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `message` | str | None | 废弃原因或替代方法说明 |
| `version` | str | None | 废弃版本号 |

**使用场景**：
- API 版本迁移
- 功能重构
- 向后兼容

### @cache_result - 缓存结果

使用 LRU 策略缓存函数结果，适用于重复计算的函数。

```python
from df_test_framework.core.decorators import cache_result

@cache_result(ttl=60, maxsize=100)
def expensive_calculation(n: int) -> int:
    """耗时计算"""
    return sum(range(n))

# 第一次调用: 执行计算，结果被缓存
result1 = expensive_calculation(1000000)

# 第二次调用（60秒内）: 直接返回缓存结果
result2 = expensive_calculation(1000000)

# 清除缓存
expensive_calculation.clear_cache()

# 查看缓存信息
info = expensive_calculation.cache_info()
# {'size': 1, 'maxsize': 100, 'ttl': 60, 'keys': [...]}
```

**参数说明**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `ttl` | float | None | 缓存过期时间（秒），None 表示永不过期 |
| `maxsize` | int | 128 | 最大缓存条目数 |

**附加方法**：
- `clear_cache()`: 清除所有缓存
- `cache_info()`: 获取缓存统计信息

**使用场景**：
- 重复计算（数学运算、数据处理）
- 配置读取（频繁访问的配置）
- 数据转换（格式转换、编码解码）

**注意事项**：
- 仅适用于纯函数（相同输入总是返回相同输出）
- 参数必须可哈希（不能是 list、dict 等可变类型）

---

## 最佳实践

### 1. 测试装饰器使用建议

**✅ 推荐做法**：

```python
# 使用自动发现模式
# conftest.py
from df_test_framework.testing.decorators import load_api_fixtures, load_actions_fixtures

load_api_fixtures(globals(), apis_package="myproject.apis")
load_actions_fixtures(globals(), actions_package="myproject.actions")

# 按业务模块拆分 API 和 Actions
# apis/user_api.py
@api_class()
class UserAPI(BaseAPI):
    pass

# apis/order_api.py
@api_class()
class OrderAPI(BaseAPI):
    pass

# actions/login_actions.py
@actions_class()
class LoginActions(AppActions):
    pass
```

**❌ 不推荐做法**：

```python
# 不要手动创建 fixture（装饰器已自动处理）
@pytest.fixture
def user_api(http_client):  # 多余的代码
    return UserAPI(http_client)

# 不要在单个文件中定义所有 API（难以维护）
class UserAPI(BaseAPI):
    pass

class OrderAPI(BaseAPI):
    pass

class ProductAPI(BaseAPI):
    pass
```

### 2. 通用装饰器组合使用

装饰器可以组合使用，但要注意顺序：

```python
# ✅ 正确顺序：从内到外执行
@log_execution(log_args=True, log_result=True)  # 最外层：记录日志
@retry_on_failure(max_retries=3)                # 中间层：重试
@cache_result(ttl=60)                           # 最内层：缓存
def fetch_user_data(user_id: int):
    return requests.get(f"/users/{user_id}").json()

# 执行流程：
# 1. 检查缓存（cache_result）
# 2. 如果未命中，执行函数，失败时重试（retry_on_failure）
# 3. 记录执行日志（log_execution）
```

### 3. Scope 选择建议

| 场景 | 推荐 Scope | 原因 |
|------|-----------|------|
| HTTP API 测试 | `session` | 无状态，可共享实例 |
| UI Actions 测试 | `function` | 有状态，需要隔离 |
| 数据库操作 | `function` | 避免事务冲突 |
| 配置读取 | `session` | 配置不变，可共享 |

### 4. 命名规范

```python
# ✅ 清晰的命名
@api_class()
class UserManagementAPI(BaseAPI):  # 自动生成：user_management_api
    pass

@actions_class()
class LoginActions(AppActions):  # 自动生成：login_actions
    pass

# ❌ 不清晰的命名
@api_class()
class API1(BaseAPI):  # 自动生成：api1（不清晰）
    pass

@actions_class()
class Actions(AppActions):  # 自动生成：actions（太泛化）
    pass
```

---

## 注意事项

### 1. 测试装饰器注意事项

**自动发现的限制**：
- `load_api_fixtures()` 和 `load_actions_fixtures()` 只能导入指定包下的直接子模块
- 不支持嵌套子包（如 `apis/v1/user_api.py`）
- 如需嵌套结构，请使用手动导入模式

**Fixture 名称冲突**：
```python
# ❌ 错误：两个类生成相同的 fixture 名称
@api_class()  # 生成 user_api
class UserAPI(BaseAPI):
    pass

@api_class()  # 生成 user_api（冲突！）
class UserApi(BaseAPI):
    pass

# ✅ 解决方案：手动指定不同的名称
@api_class("user_api_v1")
class UserAPI(BaseAPI):
    pass

@api_class("user_api_v2")
class UserApi(BaseAPI):
    pass
```

### 2. 通用装饰器注意事项

**@retry_on_failure 注意事项**：
- 不要用于幂等性操作（如创建订单、支付）
- 重试会增加执行时间，谨慎设置 `max_retries`
- 指数退避可能导致长时间等待

**@cache_result 注意事项**：
- 仅适用于纯函数（无副作用）
- 参数必须可哈希（不能是 list、dict）
- 注意内存占用（`maxsize` 设置合理值）
- 多进程环境下缓存不共享

**@log_execution 注意事项**：
- 避免记录敏感信息（密码、token、个人信息）
- 大数据量时避免使用 `log_result=True`
- 日志级别为 DEBUG，生产环境可能不输出

### 3. 性能考虑

```python
# ❌ 性能问题：每次调用都重试 + 记录日志
@log_execution(log_args=True, log_result=True)
@retry_on_failure(max_retries=10, delay=2.0)
def frequent_call():
    pass

# ✅ 优化：仅在必要时使用装饰器
@retry_on_failure(max_retries=3, delay=0.5)  # 减少重试次数和延迟
def frequent_call():
    pass
```

---

## 相关文档

- [Fixtures 使用指南](fixtures_guide.md) - pytest fixtures 详细说明
- [HTTP 客户端指南](http_client_guide.md) - BaseAPI 使用方法
- [Web UI 测试指南](web-ui-testing.md) - AppActions 使用方法
- [配置系统指南](config_guide.md) - 配置 apis_package 和 actions_package

---

## 快速参考

### 导入语句

```python
# 测试装饰器
from df_test_framework.testing.decorators import (
    api_class,
    actions_class,
    load_api_fixtures,
    load_actions_fixtures,
)

# 通用装饰器
from df_test_framework.core.decorators import (
    retry_on_failure,
    log_execution,
    deprecated,
    cache_result,
)
```

### 常用模式

```python
# API 测试项目结构
myproject/
├── apis/
│   ├── __init__.py
│   ├── user_api.py      # @api_class()
│   └── order_api.py     # @api_class()
├── tests/
│   ├── conftest.py      # load_api_fixtures(globals(), "myproject.apis")
│   └── test_user.py     # def test_xxx(user_api): ...
└── ...

# UI 测试项目结构
myproject/
├── actions/
│   ├── __init__.py
│   ├── login_actions.py   # @actions_class()
│   └── order_actions.py   # @actions_class()
├── tests/
│   ├── conftest.py        # load_actions_fixtures(globals(), "myproject.actions")
│   └── test_login.py      # def test_xxx(login_actions): ...
└── ...
```

---

**完成时间**: 2026-01-17
