# 异常体系 API 参考

> **最后更新**: 2026-01-17
> **适用版本**: v3.14.0+

## 概述

异常体系定义了框架中使用的所有异常类型，提供统一的错误处理机制。

### 设计原则

- **层次结构**: 所有框架异常继承自 FrameworkError
- **上下文信息**: 异常携带详细的上下文信息（details）
- **类型安全**: 使用类型注解确保异常处理的正确性
- **可扩展**: 支持自定义异常类型

### 核心组件

```
exceptions.py     # 异常类型定义
```

### 异常层次结构

```
Exception (Python 内置)
├── FrameworkError (框架基础异常)
│   ├── ConfigurationError (配置错误)
│   ├── HttpError (HTTP 错误)
│   ├── DatabaseError (数据库错误)
│   ├── MessengerError (消息队列错误)
│   ├── StorageError (存储错误)
│   ├── MiddlewareError (中间件错误)
│   ├── PluginError (插件错误)
│   ├── TelemetryError (可观测性错误)
│   ├── ResourceError (资源错误)
│   ├── RedisError (Redis 错误)
│   ├── ValidationError (验证错误)
│   ├── ExtensionError (扩展错误)
│   ├── ProviderError (Provider 错误)
│   └── TestError (测试错误)
└── MiddlewareAbort (中间件主动终止)
```

---

## FrameworkError

框架基础异常，所有框架异常的基类。

**定义位置**: `core/exceptions.py`

### 类签名

```python
class FrameworkError(Exception):
    """框架基础异常"""
```

### 构造函数

```python
def __init__(
    self,
    message: str = "",
    details: dict[str, Any] | None = None,
):
    """初始化异常

    Args:
        message: 错误消息
        details: 详细信息字典
    """
```

### 属性

#### message

```python
message: str
```

错误消息，描述异常的原因。

#### details

```python
details: dict[str, Any]
```

详细信息字典，包含异常的上下文信息。

### 使用示例

```python
from df_test_framework.core.exceptions import FrameworkError

# 抛出基础异常
raise FrameworkError(
    message="操作失败",
    details={"operation": "save_data", "reason": "invalid_input"},
)

# 捕获异常
try:
    do_something()
except FrameworkError as e:
    print(f"错误: {e.message}")
    print(f"详情: {e.details}")
```

---

## ConfigurationError

配置错误，用于配置文件格式错误、必填项缺失、值校验失败等场景。

**定义位置**: `core/exceptions.py`

### 类签名

```python
class ConfigurationError(FrameworkError):
    """配置错误"""
```

### 继承

继承自 `FrameworkError`，拥有 `message` 和 `details` 属性。

### 使用示例

```python
from df_test_framework.core.exceptions import ConfigurationError

# 配置文件格式错误
raise ConfigurationError(
    message="配置文件格式错误",
    details={"file": "config.yaml", "line": 10},
)

# 必填项缺失
raise ConfigurationError(
    message="缺少必填配置项",
    details={"field": "database.host"},
)

# 值校验失败
raise ConfigurationError(
    message="配置值无效",
    details={"field": "http.timeout", "value": -1, "expected": ">0"},
)
```

---

## HttpError

HTTP 错误，用于 HTTP 请求失败、响应解析错误等场景。

**定义位置**: `core/exceptions.py`

### 类签名

```python
class HttpError(FrameworkError):
    """HTTP 错误"""
```

### 构造函数

```python
def __init__(
    self,
    message: str = "",
    status_code: int | None = None,
    response_body: str | None = None,
    details: dict[str, Any] | None = None,
):
    """初始化异常

    Args:
        message: 错误消息
        status_code: HTTP 状态码
        response_body: 响应体内容
        details: 详细信息字典
    """
```

### 属性

#### status_code

```python
status_code: int | None
```

HTTP 状态码，如 404、500 等。

#### response_body

```python
response_body: str | None
```

响应体内容，用于调试和错误分析。

### 使用示例

```python
from df_test_framework.core.exceptions import HttpError

# HTTP 请求失败
raise HttpError(
    message="请求失败",
    status_code=500,
    response_body='{"error": "Internal Server Error"}',
    details={"url": "https://api.example.com/users", "method": "POST"},
)

# 捕获并处理
try:
    response = await http_client.get("/api/users")
except HttpError as e:
    print(f"HTTP 错误: {e.status_code}")
    print(f"响应: {e.response_body}")
```

---

## DatabaseError

数据库错误，用于连接失败、查询错误、事务错误等场景。

**定义位置**: `core/exceptions.py`

### 类签名

```python
class DatabaseError(FrameworkError):
    """数据库错误"""
```

### 构造函数

```python
def __init__(
    self,
    message: str = "",
    sql: str | None = None,
    params: dict[str, Any] | None = None,
    details: dict[str, Any] | None = None,
):
    """初始化异常

    Args:
        message: 错误消息
        sql: SQL 语句
        params: SQL 参数
        details: 详细信息字典
    """
```

### 属性

#### sql

```python
sql: str | None
```

执行失败的 SQL 语句。

#### params

```python
params: dict[str, Any] | None
```

SQL 语句的参数。

### 使用示例

```python
from df_test_framework.core.exceptions import DatabaseError

# 查询错误
raise DatabaseError(
    message="查询失败",
    sql="SELECT * FROM users WHERE id = :id",
    params={"id": 123},
    details={"error": "Table 'users' doesn't exist"},
)

# 连接失败
raise DatabaseError(
    message="数据库连接失败",
    details={"host": "localhost", "port": 3306, "database": "test"},
)
```

---

## MessengerError

消息队列错误，用于发送/消费消息失败等场景。

**定义位置**: `core/exceptions.py`

### 类签名

```python
class MessengerError(FrameworkError):
    """消息队列错误"""
```

### 构造函数

```python
def __init__(
    self,
    message: str = "",
    topic: str | None = None,
    details: dict[str, Any] | None = None,
):
    """初始化异常

    Args:
        message: 错误消息
        topic: 主题/队列名称
        details: 详细信息字典
    """
```

### 属性

#### topic

```python
topic: str | None
```

消息主题或队列名称。

### 使用示例

```python
from df_test_framework.core.exceptions import MessengerError

# 发送消息失败
raise MessengerError(
    message="发送消息失败",
    topic="user.created",
    details={"broker": "kafka://localhost:9092", "error": "Connection refused"},
)

# 消费消息失败
raise MessengerError(
    message="消费消息失败",
    topic="order.paid",
    details={"group_id": "order-service", "offset": 12345},
)
```

---

## StorageError

存储错误，用于文件上传/下载失败等场景。

**定义位置**: `core/exceptions.py`

### 类签名

```python
class StorageError(FrameworkError):
    """存储错误"""
```

### 构造函数

```python
def __init__(
    self,
    message: str = "",
    bucket: str | None = None,
    key: str | None = None,
    details: dict[str, Any] | None = None,
):
    """初始化异常

    Args:
        message: 错误消息
        bucket: 存储桶名称
        key: 对象键名
        details: 详细信息字典
    """
```

### 属性

#### bucket

```python
bucket: str | None
```

存储桶名称（S3/OSS）。

#### key

```python
key: str | None
```

对象键名（文件路径）。

### 使用示例

```python
from df_test_framework.core.exceptions import StorageError

# 上传失败
raise StorageError(
    message="文件上传失败",
    bucket="my-bucket",
    key="uploads/image.png",
    details={"error": "Access denied"},
)

# 下载失败
raise StorageError(
    message="文件下载失败",
    bucket="my-bucket",
    key="downloads/report.pdf",
    details={"error": "Object not found"},
)
```

---

## MiddlewareError

中间件错误，用于中间件执行过程中的错误。

**定义位置**: `core/exceptions.py`

### 类签名

```python
class MiddlewareError(FrameworkError):
    """中间件错误"""
```

### 构造函数

```python
def __init__(
    self,
    message: str = "",
    middleware_name: str | None = None,
    details: dict[str, Any] | None = None,
):
    """初始化异常

    Args:
        message: 错误消息
        middleware_name: 中间件名称
        details: 详细信息字典
    """
```

### 属性

#### middleware_name

```python
middleware_name: str | None
```

发生错误的中间件名称。

### 使用示例

```python
from df_test_framework.core.exceptions import MiddlewareError

# 中间件执行失败
raise MiddlewareError(
    message="中间件执行失败",
    middleware_name="AuthMiddleware",
    details={"error": "Token validation failed"},
)

# 中间件配置错误
raise MiddlewareError(
    message="中间件配置错误",
    middleware_name="RetryMiddleware",
    details={"field": "max_retries", "value": -1},
)
```

---

## MiddlewareAbort

中间件主动终止请求异常，用于认证失败、限流触发等场景。

**定义位置**: `core/exceptions.py`

### 类签名

```python
class MiddlewareAbort(Exception):
    """中间件主动终止请求"""
```

**说明**：
- **不继承** `FrameworkError`，是独立的异常类型
- 用于中间件主动终止请求链
- 可选地携带预设响应返回给调用者

### 构造函数

```python
def __init__(
    self,
    message: str = "",
    response: Any = None,
):
    """初始化异常

    Args:
        message: 错误消息
        response: 预设响应对象（可选）
    """
```

### 属性

#### response

```python
response: Any
```

预设响应对象，当中间件终止请求时返回此响应。

### 使用示例

```python
from df_test_framework.core.exceptions import MiddlewareAbort

# 认证失败，终止请求
raise MiddlewareAbort(
    message="认证失败",
    response={"status_code": 401, "body": {"error": "Unauthorized"}},
)

# 限流触发，终止请求
raise MiddlewareAbort(
    message="请求过于频繁",
    response={"status_code": 429, "body": {"error": "Too Many Requests"}},
)

# 在中间件中捕获
try:
    response = await call_next(request)
except MiddlewareAbort as e:
    # 返回预设响应
    if e.response:
        return e.response
    raise
```

---

## PluginError

插件错误，用于插件加载、注册、执行错误等场景。

**定义位置**: `core/exceptions.py`

### 类签名

```python
class PluginError(FrameworkError):
    """插件错误"""
```

### 构造函数

```python
def __init__(
    self,
    message: str = "",
    plugin_name: str | None = None,
    details: dict[str, Any] | None = None,
):
    """初始化异常

    Args:
        message: 错误消息
        plugin_name: 插件名称
        details: 详细信息字典
    """
```

### 属性

#### plugin_name

```python
plugin_name: str | None
```

发生错误的插件名称。

### 使用示例

```python
from df_test_framework.core.exceptions import PluginError

# 插件加载失败
raise PluginError(
    message="插件加载失败",
    plugin_name="AllurePlugin",
    details={"error": "Module not found"},
)

# 插件注册失败
raise PluginError(
    message="插件注册失败",
    plugin_name="MonitoringPlugin",
    details={"error": "Duplicate plugin name"},
)

# Hook 调用失败
raise PluginError(
    message="Hook 调用失败",
    plugin_name="CustomPlugin",
    details={"hook": "df_providers", "error": "Invalid return value"},
)
```

---

## TelemetryError

可观测性错误，用于追踪、指标、日志配置或导出错误等场景。

**定义位置**: `core/exceptions.py`

### 类签名

```python
class TelemetryError(FrameworkError):
    """可观测性错误"""
```

### 继承

继承自 `FrameworkError`，拥有 `message` 和 `details` 属性。

### 使用示例

```python
from df_test_framework.core.exceptions import TelemetryError

# 追踪配置错误
raise TelemetryError(
    message="追踪配置错误",
    details={"exporter": "otlp", "endpoint": "invalid-url"},
)

# 指标导出失败
raise TelemetryError(
    message="指标导出失败",
    details={"exporter": "prometheus", "error": "Connection refused"},
)

# 日志记录失败
raise TelemetryError(
    message="日志记录失败",
    details={"handler": "file", "path": "/var/log/app.log", "error": "Permission denied"},
)
```

---

## ResourceError

资源错误，资源（数据库、Redis、HTTP等）访问或操作错误的基类。

**定义位置**: `core/exceptions.py`

### 类签名

```python
class ResourceError(FrameworkError):
    """资源错误"""
```

### 继承

继承自 `FrameworkError`，拥有 `message` 和 `details` 属性。

### 使用示例

```python
from df_test_framework.core.exceptions import ResourceError

# 资源访问失败
raise ResourceError(
    message="资源访问失败",
    details={"resource": "database", "operation": "connect"},
)

# 资源不可用
raise ResourceError(
    message="资源不可用",
    details={"resource": "redis", "status": "unavailable"},
)
```

---

## RedisError

Redis 错误，用于 Redis 连接或操作错误。

**定义位置**: `core/exceptions.py`

### 类签名

```python
class RedisError(FrameworkError):
    """Redis 错误"""
```

### 构造函数

```python
def __init__(
    self,
    message: str = "",
    key: str | None = None,
    details: dict[str, Any] | None = None,
):
    """初始化异常

    Args:
        message: 错误消息
        key: Redis 键名
        details: 详细信息字典
    """
```

### 属性

#### key

```python
key: str | None
```

操作失败的 Redis 键名。

### 使用示例

```python
from df_test_framework.core.exceptions import RedisError

# 连接失败
raise RedisError(
    message="Redis 连接失败",
    details={"host": "localhost", "port": 6379, "error": "Connection refused"},
)

# 操作失败
raise RedisError(
    message="Redis 操作失败",
    key="user:123",
    details={"operation": "get", "error": "Key not found"},
)

# 设置失败
raise RedisError(
    message="Redis 设置失败",
    key="session:abc",
    details={"operation": "set", "ttl": 3600, "error": "Out of memory"},
)
```

---

## ValidationError

验证错误，用于数据验证、参数检查等错误。

**定义位置**: `core/exceptions.py`

### 类签名

```python
class ValidationError(FrameworkError):
    """验证错误"""
```

### 继承

继承自 `FrameworkError`，拥有 `message` 和 `details` 属性。

### 使用示例

```python
from df_test_framework.core.exceptions import ValidationError

# 参数验证失败
raise ValidationError(
    message="参数验证失败",
    details={"field": "email", "value": "invalid-email", "rule": "email format"},
)

# 数据格式错误
raise ValidationError(
    message="数据格式错误",
    details={"field": "age", "value": -1, "expected": "positive integer"},
)

# 必填字段缺失
raise ValidationError(
    message="必填字段缺失",
    details={"fields": ["username", "password"]},
)
```

---

## ExtensionError

扩展错误，用于扩展加载、执行或 Hook 调用错误。

**定义位置**: `core/exceptions.py`

### 类签名

```python
class ExtensionError(FrameworkError):
    """扩展错误"""
```

### 继承

继承自 `FrameworkError`，拥有 `message` 和 `details` 属性。

### 使用示例

```python
from df_test_framework.core.exceptions import ExtensionError

# 扩展加载失败
raise ExtensionError(
    message="扩展加载失败",
    details={"extension": "custom_extension", "error": "Module not found"},
)

# Hook 调用失败
raise ExtensionError(
    message="Hook 调用失败",
    details={"hook": "pytest_configure", "error": "Invalid signature"},
)

# 扩展执行错误
raise ExtensionError(
    message="扩展执行错误",
    details={"extension": "data_generator", "operation": "generate", "error": "Invalid template"},
)
```

---

## ProviderError

Provider 错误，用于 Provider 注册、查找或实例化错误。

**定义位置**: `core/exceptions.py`

### 类签名

```python
class ProviderError(FrameworkError):
    """Provider 错误"""
```

### 继承

继承自 `FrameworkError`，拥有 `message` 和 `details` 属性。

### 使用示例

```python
from df_test_framework.core.exceptions import ProviderError

# Provider 注册失败
raise ProviderError(
    message="Provider 注册失败",
    details={"provider": "HttpClientProvider", "error": "Duplicate registration"},
)

# Provider 查找失败
raise ProviderError(
    message="Provider 查找失败",
    details={"interface": "IHttpClient", "error": "No provider registered"},
)

# Provider 实例化失败
raise ProviderError(
    message="Provider 实例化失败",
    details={"provider": "DatabaseProvider", "error": "Missing configuration"},
)
```

---

## TestError

测试错误，用于测试执行过程中的框架级错误（不是测试断言失败）。

**定义位置**: `core/exceptions.py`

### 类签名

```python
class TestError(FrameworkError):
    """测试错误"""
```

### 继承

继承自 `FrameworkError`，拥有 `message` 和 `details` 属性。

### 使用示例

```python
from df_test_framework.core.exceptions import TestError

# Fixture 加载失败
raise TestError(
    message="Fixture 加载失败",
    details={"fixture": "http_client", "error": "Initialization failed"},
)

# 测试数据准备失败
raise TestError(
    message="测试数据准备失败",
    details={"data_file": "test_data.json", "error": "File not found"},
)

# 测试环境配置错误
raise TestError(
    message="测试环境配置错误",
    details={"env": "staging", "error": "Invalid configuration"},
)
```

---

## 使用指南

### 异常捕获

#### 捕获特定异常

```python
from df_test_framework.core.exceptions import HttpError, DatabaseError

try:
    response = await http_client.get("/api/users")
except HttpError as e:
    print(f"HTTP 错误: {e.status_code}")
    print(f"响应: {e.response_body}")
except DatabaseError as e:
    print(f"数据库错误: {e.sql}")
    print(f"参数: {e.params}")
```

#### 捕获所有框架异常

```python
from df_test_framework.core.exceptions import FrameworkError

try:
    # 执行操作
    result = await do_something()
except FrameworkError as e:
    # 统一处理所有框架异常
    print(f"框架错误: {e.message}")
    print(f"详情: {e.details}")
```

#### 异常链

```python
from df_test_framework.core.exceptions import DatabaseError

try:
    # 数据库操作
    result = await db.query("SELECT * FROM users")
except Exception as e:
    # 包装原始异常
    raise DatabaseError(
        message="查询失败",
        sql="SELECT * FROM users",
        details={"original_error": str(e)},
    ) from e
```

### 自定义异常

#### 继承 FrameworkError

```python
from df_test_framework.core.exceptions import FrameworkError

class CustomError(FrameworkError):
    """自定义异常"""

    def __init__(
        self,
        message: str = "",
        custom_field: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, details)
        self.custom_field = custom_field

# 使用自定义异常
raise CustomError(
    message="自定义错误",
    custom_field="custom_value",
    details={"context": "additional info"},
)
```

#### 添加自定义属性

```python
from df_test_framework.core.exceptions import FrameworkError

class BusinessError(FrameworkError):
    """业务错误"""

    def __init__(
        self,
        message: str = "",
        error_code: str | None = None,
        user_message: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, details)
        self.error_code = error_code
        self.user_message = user_message

# 使用业务异常
raise BusinessError(
    message="订单创建失败",
    error_code="ORDER_001",
    user_message="库存不足，请稍后再试",
    details={"product_id": 123, "requested": 10, "available": 5},
)
```

---

## 最佳实践

### 1. 选择合适的异常类型

```python
# ✅ 推荐：使用具体的异常类型
from df_test_framework.core.exceptions import HttpError

raise HttpError(
    message="请求失败",
    status_code=500,
    response_body='{"error": "Internal Server Error"}',
)

# ❌ 不推荐：使用通用异常
raise FrameworkError("请求失败")
```

### 2. 提供详细的上下文信息

```python
# ✅ 推荐：提供详细的 details
raise DatabaseError(
    message="查询失败",
    sql="SELECT * FROM users WHERE id = :id",
    params={"id": 123},
    details={
        "error": "Table 'users' doesn't exist",
        "database": "test_db",
        "host": "localhost",
    },
)

# ❌ 不推荐：缺少上下文
raise DatabaseError("查询失败")
```

### 3. 使用异常链保留原始错误

```python
# ✅ 推荐：使用 from 保留原始异常
try:
    result = await db.query("SELECT * FROM users")
except Exception as e:
    raise DatabaseError(
        message="查询失败",
        sql="SELECT * FROM users",
        details={"original_error": str(e)},
    ) from e

# ❌ 不推荐：丢失原始异常信息
try:
    result = await db.query("SELECT * FROM users")
except Exception:
    raise DatabaseError("查询失败")
```

### 4. 在合适的层次捕获异常

```python
# ✅ 推荐：在适当的层次处理异常
async def get_user(user_id: int):
    """业务层：捕获并转换异常"""
    try:
        return await db.query("SELECT * FROM users WHERE id = :id", {"id": user_id})
    except DatabaseError as e:
        # 转换为业务异常
        raise BusinessError(
            message=f"获取用户失败: {user_id}",
            error_code="USER_001",
            details={"user_id": user_id, "db_error": str(e)},
        ) from e

# ❌ 不推荐：在底层吞掉异常
async def query(sql: str):
    try:
        return await execute(sql)
    except Exception:
        return None  # 吞掉异常，调用者无法知道发生了什么
```

### 5. 避免过度捕获

```python
# ✅ 推荐：只捕获预期的异常
try:
    response = await http_client.get("/api/users")
except HttpError as e:
    # 处理 HTTP 错误
    handle_http_error(e)

# ❌ 不推荐：捕获所有异常
try:
    response = await http_client.get("/api/users")
except Exception:
    # 可能捕获了不应该处理的异常（如 KeyboardInterrupt）
    pass
```

### 6. 记录异常信息

```python
# ✅ 推荐：记录异常详情
import logging

logger = logging.getLogger(__name__)

try:
    response = await http_client.get("/api/users")
except HttpError as e:
    logger.error(
        "HTTP 请求失败",
        extra={
            "status_code": e.status_code,
            "response_body": e.response_body,
            "details": e.details,
        },
    )
    raise

# ❌ 不推荐：只记录消息
try:
    response = await http_client.get("/api/users")
except HttpError as e:
    logger.error(str(e))
    raise
```

---

## 相关文档

### 使用指南
- [中间件使用指南](../../guides/middleware_guide.md) - 中间件异常处理
- [HTTP 客户端指南](../../guides/http_client_guide.md) - HTTP 异常处理
- [数据库使用指南](../../guides/database_guide.md) - 数据库异常处理

### 架构文档
- [五层架构详解](../../architecture/五层架构详解.md) - 架构层次说明
- [ARCHITECTURE_V4.0.md](../../architecture/ARCHITECTURE_V4.0.md) - v4.0 架构总览

### API 参考
- [Core 层 API 参考](README.md) - Core 层概览
- [协议定义 API 参考](protocols.md) - 协议接口
- [中间件系统 API 参考](middleware.md) - 中间件 API
- [上下文系统 API 参考](context.md) - 上下文管理
- [事件类型 API 参考](events.md) - 事件类型定义

---

**完成时间**: 2026-01-17

