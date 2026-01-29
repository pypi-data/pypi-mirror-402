# 中间件系统 API 参考

> **最后更新**: 2026-01-17
> **适用版本**: v3.0.0+

## 概述

中间件系统是 DF Test Framework 的核心机制之一，提供了统一的请求/响应拦截和处理能力。

### 设计原则

- **洋葱模型**: before 和 after 在同一作用域，便于共享状态
- **优先级控制**: 通过 priority 属性控制执行顺序
- **泛型支持**: 适用于所有能力层（HTTP、gRPC、Database、MQ）
- **链式调用**: 支持流畅的 API 设计

### 核心组件

```
middleware/
├── protocol.py     # 中间件协议定义
├── base.py         # 便捷基类（BaseMiddleware、SyncMiddleware）
├── chain.py        # 中间件执行链
└── decorator.py    # 装饰器支持
```

### 洋葱模型

```
请求 → Middleware1.before → Middleware2.before → Handler
                                                    ↓
响应 ← Middleware1.after  ← Middleware2.after  ← 处理结果
```

**执行顺序**：
- **before**: priority 升序（数字小的先执行）
- **after**: priority 降序（数字大的先执行，即逆序）

---

## 类型定义

### Next

Next 函数类型，表示调用下一个中间件或最终处理器的函数。

**定义位置**: `core/middleware/protocol.py`

```python
type Next[T, R] = Callable[[T], Awaitable[R]]
```

**类型参数**：
- `T`: 请求类型
- `R`: 响应类型

**说明**：
- 接收请求对象，返回异步响应
- 用于中间件链的传递

---

### MiddlewareFunc

中间件函数类型。

**定义位置**: `core/middleware/protocol.py`

```python
type MiddlewareFunc[T, R] = Callable[[T, Next[T, R]], Awaitable[R]]
```

**类型参数**：
- `T`: 请求类型
- `R`: 响应类型

**说明**：
- 接收请求和 next 函数，返回异步响应
- 用于函数式中间件定义

---

## Middleware

中间件协议基类，定义统一的中间件接口。

**定义位置**: `core/middleware/protocol.py`

### 类签名

```python
class Middleware[TRequest, TResponse](ABC):
    """统一中间件协议"""
```

### 类属性

#### name

```python
name: str = ""
```

中间件名称，用于标识和调试。

#### priority

```python
priority: int = 100
```

优先级，数字越小越先执行。

**推荐值**：
- 签名/加密: 10-20
- 认证/授权: 20-30
- 日志/监控: 90-100
- 重试/熔断: 80-90

### 方法

#### __call__()

```python
@abstractmethod
async def __call__(
    self,
    request: TRequest,
    call_next: Next[TRequest, TResponse],
) -> TResponse:
    """洋葱模型核心方法

    Args:
        request: 请求对象
        call_next: 调用下一个中间件或最终处理器的函数

    Returns:
        响应对象
    """
```

**实现要点**：
1. **before 逻辑**: 在 `await call_next(request)` 之前执行
2. **调用下一层**: 使用 `await call_next(request)` 传递请求
3. **after 逻辑**: 在 `await call_next(request)` 之后执行
4. **返回响应**: 必须返回响应对象

### 使用示例

#### 基础中间件

```python
from df_test_framework.core.middleware import Middleware, Next

class TimingMiddleware(Middleware[HttpRequest, HttpResponse]):
    """计时中间件"""

    def __init__(self):
        self.name = "TimingMiddleware"
        self.priority = 100

    async def __call__(
        self,
        request: HttpRequest,
        call_next: Next[HttpRequest, HttpResponse],
    ) -> HttpResponse:
        # before: 记录开始时间
        start = time.monotonic()

        # 调用下一个中间件
        response = await call_next(request)

        # after: 计算耗时
        duration = time.monotonic() - start
        print(f"Request took {duration:.3f}s")

        return response
```

#### 修改请求

```python
class AddHeaderMiddleware(Middleware[HttpRequest, HttpResponse]):
    """添加请求头中间件"""

    def __init__(self, key: str, value: str):
        self.name = "AddHeaderMiddleware"
        self.priority = 50
        self.key = key
        self.value = value

    async def __call__(self, request, call_next):
        # 修改请求
        request.headers[self.key] = self.value

        # 传递修改后的请求
        response = await call_next(request)

        return response
```

#### 修改响应

```python
class AddResponseHeaderMiddleware(Middleware[HttpRequest, HttpResponse]):
    """添加响应头中间件"""

    def __init__(self, key: str, value: str):
        self.name = "AddResponseHeaderMiddleware"
        self.priority = 90
        self.key = key
        self.value = value

    async def __call__(self, request, call_next):
        # 获取响应
        response = await call_next(request)

        # 修改响应
        response.headers[self.key] = self.value

        return response
```

#### 异常处理

```python
class ErrorHandlingMiddleware(Middleware[HttpRequest, HttpResponse]):
    """错误处理中间件"""

    def __init__(self):
        self.name = "ErrorHandlingMiddleware"
        self.priority = 10

    async def __call__(self, request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # 捕获异常，返回错误响应
            logger.error(f"Request failed: {e}")
            return ErrorResponse(status_code=500, message=str(e))
```

---

## BaseMiddleware

中间件便捷基类，提供默认实现。

**定义位置**: `core/middleware/base.py`

### 类签名

```python
class BaseMiddleware[TRequest, TResponse](Middleware[TRequest, TResponse]):
    """中间件便捷基类"""
```

### 构造函数

```python
def __init__(
    self,
    name: str | None = None,
    priority: int = 100,
):
    """初始化中间件

    Args:
        name: 中间件名称（默认使用类名）
        priority: 优先级（默认 100）
    """
```

### 方法

#### __call__()

```python
async def __call__(
    self,
    request: TRequest,
    call_next: Next[TRequest, TResponse],
) -> TResponse:
    """默认实现：直接传递"""
    return await call_next(request)
```

**说明**：
- 默认实现直接调用 `call_next`，不做任何处理
- 子类覆盖此方法来实现自定义逻辑

### 使用示例

```python
from df_test_framework.core.middleware import BaseMiddleware

class LoggingMiddleware(BaseMiddleware[HttpRequest, HttpResponse]):
    """日志中间件"""

    def __init__(self):
        super().__init__(priority=100)

    async def __call__(self, request, call_next):
        print(f"Request: {request.method} {request.path}")
        response = await call_next(request)
        print(f"Response: {response.status_code}")
        return response
```

---

## SyncMiddleware

同步中间件基类，适用于不需要异步操作的简单场景。

**定义位置**: `core/middleware/base.py`

### 类签名

```python
class SyncMiddleware[TRequest, TResponse](BaseMiddleware[TRequest, TResponse]):
    """同步中间件基类"""
```

### 方法

#### before()

```python
def before(self, request: TRequest) -> TRequest:
    """前置处理（同步）

    Args:
        request: 请求对象

    Returns:
        处理后的请求对象
    """
    return request
```

**说明**：
- 在请求发送前执行
- 可以修改请求对象
- 默认实现直接返回原请求

#### after()

```python
def after(self, response: TResponse) -> TResponse:
    """后置处理（同步）

    Args:
        response: 响应对象

    Returns:
        处理后的响应对象
    """
    return response
```

**说明**：
- 在响应返回后执行
- 可以修改响应对象
- 默认实现直接返回原响应

### 使用示例

#### 前置处理

```python
from df_test_framework.core.middleware import SyncMiddleware

class AddHeaderMiddleware(SyncMiddleware[HttpRequest, HttpResponse]):
    """添加请求头中间件"""

    def __init__(self, key: str, value: str):
        super().__init__()
        self.key = key
        self.value = value

    def before(self, request):
        # 修改请求
        request.headers[self.key] = self.value
        return request
```

#### 后置处理

```python
class LogResponseMiddleware(SyncMiddleware[HttpRequest, HttpResponse]):
    """日志响应中间件"""

    def after(self, response):
        # 记录响应
        print(f"Status: {response.status_code}")
        return response
```

#### 前后处理

```python
class TimingMiddleware(SyncMiddleware[HttpRequest, HttpResponse]):
    """计时中间件"""

    def __init__(self):
        super().__init__()
        self.start_time = 0

    def before(self, request):
        self.start_time = time.monotonic()
        return request

    def after(self, response):
        duration = time.monotonic() - self.start_time
        print(f"Duration: {duration:.3f}s")
        return response
```

---

## MiddlewareChain

中间件执行链，管理中间件的注册和执行。

**定义位置**: `core/middleware/chain.py`

### 类签名

```python
class MiddlewareChain[TRequest, TResponse]:
    """中间件执行链"""
```

### 构造函数

```python
def __init__(self, handler: Next[TRequest, TResponse]):
    """初始化中间件链

    Args:
        handler: 最终处理函数（如发送 HTTP 请求）
    """
```

### 方法

#### use()

```python
def use(self, middleware: Middleware[TRequest, TResponse]) -> Self:
    """添加中间件（支持链式调用）

    Args:
        middleware: 要添加的中间件

    Returns:
        self，支持链式调用
    """
```

**说明**：
- 添加中间件到执行链
- 自动按 priority 排序
- 支持链式调用

#### use_many()

```python
def use_many(self, middlewares: list[Middleware[TRequest, TResponse]]) -> Self:
    """批量添加中间件

    Args:
        middlewares: 中间件列表

    Returns:
        self，支持链式调用
    """
```

#### remove()

```python
def remove(self, middleware: Middleware[TRequest, TResponse]) -> Self:
    """移除中间件

    Args:
        middleware: 要移除的中间件

    Returns:
        self，支持链式调用
    """
```

#### clear()

```python
def clear(self) -> Self:
    """清空所有中间件

    Returns:
        self，支持链式调用
    """
```

#### execute()

```python
async def execute(self, request: TRequest) -> TResponse:
    """执行中间件链

    Args:
        request: 请求对象

    Returns:
        响应对象

    Raises:
        MiddlewareAbort: 如果中间件主动终止请求且未提供响应
    """
```

**说明**：
- 按优先级顺序执行中间件
- 构建洋葱模型：从内到外包装
- 自动处理 MiddlewareAbort 异常

### 属性

#### middlewares

```python
@property
def middlewares(self) -> list[Middleware[TRequest, TResponse]]:
    """已注册的中间件列表（只读副本）"""
```

### 特殊方法

#### __len__()

```python
def __len__(self) -> int:
    """返回中间件数量"""
```

#### __contains__()

```python
def __contains__(self, middleware: Middleware[TRequest, TResponse]) -> bool:
    """检查中间件是否存在"""
```

### 使用示例

#### 基础用法

```python
from df_test_framework.core.middleware import MiddlewareChain

# 创建中间件链
async def send_request(request: HttpRequest) -> HttpResponse:
    # 实际发送请求的逻辑
    return await httpx_client.request(request.method, request.url)

chain = MiddlewareChain(send_request)

# 添加中间件
chain.use(SignMiddleware(priority=10))
chain.use(AuthMiddleware(priority=20))
chain.use(LogMiddleware(priority=100))

# 执行请求
response = await chain.execute(request)
```

#### 链式调用

```python
chain = (
    MiddlewareChain(send_request)
    .use(SignMiddleware(priority=10))
    .use(AuthMiddleware(priority=20))
    .use(LogMiddleware(priority=100))
)

response = await chain.execute(request)
```

#### 批量添加

```python
middlewares = [
    SignMiddleware(priority=10),
    AuthMiddleware(priority=20),
    LogMiddleware(priority=100),
]

chain = MiddlewareChain(send_request).use_many(middlewares)
```

#### 动态管理

```python
# 检查中间件
if auth_middleware in chain:
    print("Auth middleware is registered")

# 移除中间件
chain.remove(auth_middleware)

# 清空所有中间件
chain.clear()

# 获取中间件数量
print(f"Total middlewares: {len(chain)}")
```

### 执行流程

```
请求 → SignMiddleware.before (priority=10)
         ↓
       AuthMiddleware.before (priority=20)
         ↓
       LogMiddleware.before (priority=100)
         ↓
       send_request (最终处理器)
         ↓
       LogMiddleware.after (priority=100)
         ↓
       AuthMiddleware.after (priority=20)
         ↓
       SignMiddleware.after (priority=10)
         ↓
响应 ← 返回
```

---

## 使用指南

### 选择合适的基类

| 场景 | 推荐基类 | 说明 |
|------|----------|------|
| 需要异步操作 | `BaseMiddleware` | 完全控制，支持异步 |
| 简单同步操作 | `SyncMiddleware` | 分离 before/after，代码清晰 |
| 复杂逻辑 | `Middleware` | 直接实现协议，最大灵活性 |

### 优先级设置建议

```python
# 推荐的优先级范围
PRIORITY_SIGNATURE = 10      # 签名/加密（最先执行）
PRIORITY_AUTH = 20           # 认证/授权
PRIORITY_VALIDATION = 30     # 参数验证
PRIORITY_TRANSFORM = 50      # 数据转换
PRIORITY_RETRY = 80          # 重试/熔断
PRIORITY_LOGGING = 90        # 日志记录
PRIORITY_MONITORING = 100    # 监控/统计（最后执行）
```

### 最佳实践

#### 1. 保持中间件单一职责

```python
# ✅ 推荐：单一职责
class AuthMiddleware(BaseMiddleware):
    """只负责认证"""
    async def __call__(self, request, call_next):
        token = request.headers.get("Authorization")
        if not self.validate_token(token):
            raise AuthError("Invalid token")
        return await call_next(request)

# ❌ 不推荐：职责混乱
class AuthAndLogMiddleware(BaseMiddleware):
    """既认证又记录日志"""
    async def __call__(self, request, call_next):
        # 认证逻辑
        token = request.headers.get("Authorization")
        if not self.validate_token(token):
            raise AuthError("Invalid token")

        # 日志逻辑（应该分离）
        logger.info(f"Request: {request.method} {request.path}")
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response
```

#### 2. 使用上下文共享状态

```python
class TimingMiddleware(BaseMiddleware):
    """使用 request 对象共享状态"""

    async def __call__(self, request, call_next):
        # 在 request 上附加开始时间
        request.start_time = time.monotonic()

        response = await call_next(request)

        # 在同一作用域访问开始时间
        duration = time.monotonic() - request.start_time
        response.headers["X-Duration"] = str(duration)

        return response
```

#### 3. 正确处理异常

```python
class ErrorHandlingMiddleware(BaseMiddleware):
    """统一错误处理"""

    async def __call__(self, request, call_next):
        try:
            return await call_next(request)
        except ValidationError as e:
            # 验证错误 -> 400
            return ErrorResponse(status_code=400, message=str(e))
        except AuthError as e:
            # 认证错误 -> 401
            return ErrorResponse(status_code=401, message=str(e))
        except Exception as e:
            # 其他错误 -> 500
            logger.exception("Unexpected error")
            return ErrorResponse(status_code=500, message="Internal error")
```

#### 4. 避免阻塞操作

```python
# ✅ 推荐：使用异步操作
class CacheMiddleware(BaseMiddleware):
    async def __call__(self, request, call_next):
        # 异步读取缓存
        cached = await self.cache.get(request.cache_key)
        if cached:
            return cached

        response = await call_next(request)

        # 异步写入缓存
        await self.cache.set(request.cache_key, response)
        return response

# ❌ 不推荐：阻塞操作
class CacheMiddleware(BaseMiddleware):
    async def __call__(self, request, call_next):
        # 同步操作会阻塞事件循环
        cached = self.cache.get_sync(request.cache_key)  # 阻塞！
        if cached:
            return cached

        response = await call_next(request)
        self.cache.set_sync(request.cache_key, response)  # 阻塞！
        return response
```

---

## 相关文档

### 使用指南
- [中间件使用指南](../../guides/middleware_guide.md) - 中间件系统详细使用
- [HTTP 客户端指南](../../guides/http_client_guide.md) - HTTP 中间件应用
- [EventBus 使用指南](../../guides/event_bus_guide.md) - 事件系统集成

### 架构文档
- [五层架构详解](../../architecture/五层架构详解.md) - 架构层次说明
- [ARCHITECTURE_V4.0.md](../../architecture/ARCHITECTURE_V4.0.md) - v4.0 架构总览

### API 参考
- [Core 层 API 参考](README.md) - Core 层概览
- [协议定义 API 参考](protocols.md) - 协议接口
- [上下文系统 API 参考](context.md) - 上下文管理
- [异常体系 API 参考](exceptions.md) - 异常类型定义

---

**完成时间**: 2026-01-17

