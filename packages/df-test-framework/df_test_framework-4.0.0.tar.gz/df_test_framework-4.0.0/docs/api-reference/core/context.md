# 上下文系统 API 参考

> **最后更新**: 2026-01-17
> **适用版本**: v3.0.0+

## 概述

上下文系统提供了贯穿整个请求链路的执行上下文管理，支持追踪信息、业务信息和扩展信息的自动传播。

### 设计原则

- **不可变性**: ExecutionContext 是不可变对象，所有修改返回新实例
- **自动传播**: 使用 contextvars 在异步上下文中自动传播
- **层次结构**: 支持父子上下文关系（trace_id 相同，span_id 不同）
- **扩展性**: 通过 baggage 支持自定义键值对传播

### 核心组件

```
context/
├── execution.py     # ExecutionContext 类
└── propagation.py   # 上下文传播管理
```

### 上下文信息

```
ExecutionContext
├── 追踪信息
│   ├── trace_id         # 追踪 ID（贯穿整个请求链路）
│   ├── span_id          # Span ID（标识当前操作）
│   └── parent_span_id   # 父 Span ID
├── 请求信息
│   ├── request_id       # 请求 ID
│   └── correlation_id   # 关联 ID（业务关联）
├── 业务信息
│   ├── user_id          # 用户 ID
│   └── tenant_id        # 租户 ID
└── 扩展信息
    └── baggage          # 跨服务传播的键值对
```

---

## ExecutionContext

执行上下文类，贯穿整个请求链路。

**定义位置**: `core/context/execution.py`

### 类签名

```python
@dataclass(frozen=True, slots=True)
class ExecutionContext:
    """执行上下文"""
```

**特性**：
- `frozen=True`: 不可变对象
- `slots=True`: 优化内存占用

### 属性

#### trace_id

```python
trace_id: str
```

追踪 ID，贯穿整个请求链路。同一个请求的所有操作共享相同的 trace_id。

#### span_id

```python
span_id: str
```

Span ID，标识当前操作。每个操作有唯一的 span_id。

#### parent_span_id

```python
parent_span_id: str | None = None
```

父 Span ID，用于构建调用链层次结构。

#### request_id

```python
request_id: str = field(default_factory=_generate_id)
```

请求 ID，自动生成 16 字符唯一标识。

#### correlation_id

```python
correlation_id: str | None = None
```

关联 ID，用于业务关联（如订单 ID、交易 ID）。

#### user_id

```python
user_id: str | None = None
```

用户 ID，标识当前操作的用户。

#### tenant_id

```python
tenant_id: str | None = None
```

租户 ID，用于多租户场景。

#### baggage

```python
baggage: dict[str, str] = field(default_factory=dict)
```

扩展信息，跨服务传播的键值对。

### 类方法

#### create_root()

```python
@classmethod
def create_root(
    cls,
    request_id: str | None = None,
    user_id: str | None = None,
    tenant_id: str | None = None,
) -> ExecutionContext:
    """创建根上下文

    Args:
        request_id: 请求 ID（可选，默认自动生成）
        user_id: 用户 ID（可选）
        tenant_id: 租户 ID（可选）

    Returns:
        新的根上下文
    """
```

**说明**：
- 自动生成 trace_id 和 span_id
- request_id 可选，默认自动生成
- 用于创建请求链路的起点

### 实例方法

#### child_context()

```python
def child_context(self, span_name: str | None = None) -> ExecutionContext:
    """创建子上下文（新 Span）

    子上下文继承父上下文的 trace_id 和业务信息，
    但有新的 span_id。

    Args:
        span_name: Span 名称（可选，仅用于调试）

    Returns:
        新的子上下文
    """
```

**说明**：
- 继承父上下文的 trace_id、request_id、user_id、tenant_id、baggage
- 生成新的 span_id
- 设置 parent_span_id 为父上下文的 span_id

#### with_baggage()

```python
def with_baggage(self, key: str, value: str) -> ExecutionContext:
    """添加 baggage 项

    返回新的上下文，原上下文不变（不可变对象）。

    Args:
        key: baggage 键
        value: baggage 值

    Returns:
        包含新 baggage 的上下文
    """
```

#### with_user()

```python
def with_user(self, user_id: str) -> ExecutionContext:
    """设置用户 ID

    Args:
        user_id: 用户 ID

    Returns:
        包含用户 ID 的上下文
    """
```

#### with_tenant()

```python
def with_tenant(self, tenant_id: str) -> ExecutionContext:
    """设置租户 ID

    Args:
        tenant_id: 租户 ID

    Returns:
        包含租户 ID 的上下文
    """
```

#### with_correlation_id()

```python
def with_correlation_id(self, correlation_id: str) -> ExecutionContext:
    """设置关联 ID

    Args:
        correlation_id: 关联 ID

    Returns:
        包含关联 ID 的上下文
    """
```

#### to_dict()

```python
def to_dict(self) -> dict[str, str | None]:
    """转换为字典

    Returns:
        上下文信息字典
    """
```

**说明**：
- 返回包含所有上下文字段的字典
- 不包含 baggage 字段

### 使用示例

#### 创建根上下文

```python
from df_test_framework.core.context import ExecutionContext

# 创建根上下文
ctx = ExecutionContext.create_root()
print(f"Trace ID: {ctx.trace_id}")
print(f"Span ID: {ctx.span_id}")

# 创建带用户信息的根上下文
ctx = ExecutionContext.create_root(user_id="user_001", tenant_id="tenant_001")
```

#### 创建子上下文

```python
# 创建根上下文
root_ctx = ExecutionContext.create_root()

# 创建子上下文（新 Span）
child_ctx = root_ctx.child_context(span_name="database_query")

# 验证层次关系
assert child_ctx.trace_id == root_ctx.trace_id  # 相同的 trace_id
assert child_ctx.span_id != root_ctx.span_id    # 不同的 span_id
assert child_ctx.parent_span_id == root_ctx.span_id  # 父子关系
```

#### 添加业务信息

```python
# 创建上下文
ctx = ExecutionContext.create_root()

# 添加用户信息
ctx_with_user = ctx.with_user("user_001")

# 添加租户信息
ctx_with_tenant = ctx_with_user.with_tenant("tenant_001")

# 添加关联 ID
ctx_with_correlation = ctx_with_tenant.with_correlation_id("order_12345")

# 链式调用
ctx = (
    ExecutionContext.create_root()
    .with_user("user_001")
    .with_tenant("tenant_001")
    .with_correlation_id("order_12345")
)
```

#### 使用 baggage

```python
# 添加 baggage
ctx = ExecutionContext.create_root()
ctx = ctx.with_baggage("env", "production")
ctx = ctx.with_baggage("region", "us-west-1")

# 访问 baggage
print(ctx.baggage["env"])  # "production"
print(ctx.baggage["region"])  # "us-west-1"
```

---

## 上下文传播函数

上下文传播管理函数，使用 contextvars 在异步上下文中自动传播。

**定义位置**: `core/context/propagation.py`

### get_current_context()

```python
def get_current_context() -> ExecutionContext | None:
    """获取当前上下文

    Returns:
        当前上下文，如果没有则返回 None
    """
```

**使用示例**：

```python
from df_test_framework.core.context import get_current_context

ctx = get_current_context()
if ctx:
    print(f"Current trace: {ctx.trace_id}")
else:
    print("No context available")
```

---

### get_or_create_context()

```python
def get_or_create_context() -> ExecutionContext:
    """获取当前上下文，如果不存在则创建根上下文

    Returns:
        当前上下文或新创建的根上下文
    """
```

**使用示例**：

```python
from df_test_framework.core.context import get_or_create_context

# 总是返回有效的上下文
ctx = get_or_create_context()
print(f"Trace ID: {ctx.trace_id}")
```

---

### set_current_context()

```python
def set_current_context(ctx: ExecutionContext | None) -> None:
    """设置当前上下文

    Args:
        ctx: 要设置的上下文，None 表示清除
    """
```

**使用示例**：

```python
from df_test_framework.core.context import set_current_context, ExecutionContext

# 设置上下文
ctx = ExecutionContext.create_root()
set_current_context(ctx)

# 清除上下文
set_current_context(None)
```

---

### with_context()

```python
@contextmanager
def with_context(ctx: ExecutionContext):
    """同步上下文作用域

    在作用域内设置指定的上下文，退出时恢复原上下文。

    Args:
        ctx: 要设置的上下文

    Yields:
        设置的上下文
    """
```

**使用示例**：

```python
from df_test_framework.core.context import with_context, ExecutionContext

ctx = ExecutionContext.create_root()
with with_context(ctx) as current:
    print(f"In context: {current.trace_id}")
    # 此作用域内的所有操作都使用此上下文
# 作用域外恢复原上下文
```

---

### with_context_async()

```python
@asynccontextmanager
async def with_context_async(ctx: ExecutionContext):
    """异步上下文作用域

    在作用域内设置指定的上下文，退出时恢复原上下文。

    Args:
        ctx: 要设置的上下文

    Yields:
        设置的上下文
    """
```

**使用示例**：

```python
from df_test_framework.core.context import with_context_async, ExecutionContext

ctx = ExecutionContext.create_root()
async with with_context_async(ctx) as current:
    response = await http_client.get("/api")
    # 此作用域内的所有操作都使用此上下文
```

---

### run_with_context()

```python
def run_with_context[T](ctx: ExecutionContext, func: Callable[[], T]) -> T:
    """在指定上下文中运行函数

    Args:
        ctx: 要使用的上下文
        func: 要运行的函数

    Returns:
        函数返回值
    """
```

**使用示例**：

```python
from df_test_framework.core.context import run_with_context, ExecutionContext

ctx = ExecutionContext.create_root()
result = run_with_context(ctx, lambda: do_something())
```

---

## 使用指南

### 典型使用场景

#### 1. HTTP 请求追踪

```python
from df_test_framework.core.context import ExecutionContext, with_context_async

async def handle_request(request):
    # 创建根上下文
    ctx = ExecutionContext.create_root(
        user_id=request.headers.get("X-User-ID"),
        tenant_id=request.headers.get("X-Tenant-ID"),
    )

    # 在上下文中处理请求
    async with with_context_async(ctx):
        # 所有子操作自动继承上下文
        response = await process_request(request)
        return response
```

#### 2. 数据库操作追踪

```python
from df_test_framework.core.context import get_or_create_context

async def query_user(user_id: str):
    # 获取当前上下文
    ctx = get_or_create_context()

    # 创建子上下文（新 Span）
    child_ctx = ctx.child_context(span_name="database.query")

    async with with_context_async(child_ctx):
        # 数据库查询
        result = await db.query("SELECT * FROM users WHERE id = ?", user_id)
        return result
```

#### 3. 跨服务调用

```python
from df_test_framework.core.context import get_current_context

async def call_external_service():
    # 获取当前上下文
    ctx = get_current_context()
    if ctx:
        # 将上下文信息注入到 HTTP headers
        headers = {
            "X-Trace-ID": ctx.trace_id,
            "X-Span-ID": ctx.span_id,
            "X-Request-ID": ctx.request_id,
        }

        # 添加 baggage
        for key, value in ctx.baggage.items():
            headers[f"X-Baggage-{key}"] = value

        # 发送请求
        response = await http_client.get("/api", headers=headers)
        return response
```

### 最佳实践

#### 1. 在请求入口创建根上下文

```python
# ✅ 推荐：在请求入口创建根上下文
async def handle_request(request):
    ctx = ExecutionContext.create_root(
        user_id=extract_user_id(request),
        tenant_id=extract_tenant_id(request),
    )

    async with with_context_async(ctx):
        return await process_request(request)

# ❌ 不推荐：在每个函数中创建新的根上下文
async def process_request(request):
    ctx = ExecutionContext.create_root()  # 丢失了父上下文
    # ...
```

#### 2. 使用子上下文标识操作

```python
# ✅ 推荐：为每个重要操作创建子上下文
async def process_order(order_id: str):
    ctx = get_or_create_context()

    # 验证订单
    async with with_context_async(ctx.child_context("validate_order")):
        await validate_order(order_id)

    # 处理支付
    async with with_context_async(ctx.child_context("process_payment")):
        await process_payment(order_id)

    # 发送通知
    async with with_context_async(ctx.child_context("send_notification")):
        await send_notification(order_id)
```

#### 3. 使用 baggage 传播元数据

```python
# ✅ 推荐：使用 baggage 传播环境信息
ctx = ExecutionContext.create_root()
ctx = ctx.with_baggage("env", "production")
ctx = ctx.with_baggage("region", "us-west-1")
ctx = ctx.with_baggage("version", "v1.2.3")

# 在下游服务中访问
ctx = get_current_context()
if ctx:
    env = ctx.baggage.get("env")
    region = ctx.baggage.get("region")
```

#### 4. 避免在上下文中存储大量数据

```python
# ✅ 推荐：只存储标识符
ctx = ctx.with_baggage("order_id", "12345")

# ❌ 不推荐：存储大量数据
# ctx = ctx.with_baggage("order_data", json.dumps(large_order_object))
```

---

## 相关文档

### 使用指南
- [Telemetry 可观测性指南](../../guides/telemetry_guide.md) - 可观测性系统使用
- [中间件使用指南](../../guides/middleware_guide.md) - 中间件系统详细使用
- [EventBus 使用指南](../../guides/event_bus_guide.md) - 事件系统集成

### 架构文档
- [五层架构详解](../../architecture/五层架构详解.md) - 架构层次说明
- [ARCHITECTURE_V4.0.md](../../architecture/ARCHITECTURE_V4.0.md) - v4.0 架构总览

### API 参考
- [Core 层 API 参考](README.md) - Core 层概览
- [协议定义 API 参考](protocols.md) - 协议接口
- [中间件系统 API 参考](middleware.md) - 中间件 API
- [事件类型 API 参考](events.md) - 事件类型定义

---

**完成时间**: 2026-01-17

