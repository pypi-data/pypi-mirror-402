# 事件类型 API 参考

> **最后更新**: 2026-01-17
> **适用版本**: v3.17.0+

## 概述

事件系统定义了框架中使用的各种事件类型，用于组件间的解耦通信和可观测性集成。

### 设计原则

- **不可变性**: 所有事件都是不可变的 dataclass
- **唯一标识**: 每个事件有唯一的 event_id
- **追踪集成**: 自动集成 OpenTelemetry 追踪上下文
- **事件关联**: 支持 Start/End 事件对的关联
- **作用域隔离**: 支持测试隔离的事件作用域

### 核心组件

```
events/
└── types.py     # 事件类型定义
```

### 事件层次结构

```
Event (基类)
├── CorrelatedEvent (可关联事件)
│   ├── HttpRequestStartEvent / HttpRequestEndEvent
│   ├── DatabaseQueryStartEvent / DatabaseQueryEndEvent
│   ├── WebActionStartEvent / WebActionEndEvent
│   └── ...
└── 其他事件
    ├── TestStartEvent / TestEndEvent
    ├── FixtureSetupEvent / FixtureTeardownEvent
    └── ...
```

---

## Event

事件基类，所有事件都应继承此类。

**定义位置**: `core/events/types.py`

### 类签名

```python
@dataclass(frozen=True)
class Event:
    """事件基类"""
```

### 属性

#### event_id

```python
event_id: str = field(default_factory=generate_event_id)
```

事件唯一标识，自动生成。格式：`evt-{12位十六进制}`

#### timestamp

```python
timestamp: datetime = field(default_factory=datetime.now)
```

事件发生时间，自动生成。

#### context

```python
context: ExecutionContext | None = None
```

执行上下文，用于追踪关联。

#### trace_id

```python
trace_id: str | None = field(default=None)
```

OpenTelemetry 追踪 ID，自动从当前 Span 获取。

#### span_id

```python
span_id: str | None = field(default=None)
```

OpenTelemetry Span ID，自动从当前 Span 获取。

#### scope

```python
scope: str | None = field(default=None)
```

事件作用域，用于测试隔离。None 表示全局事件。

---

## CorrelatedEvent

可关联事件基类，用于 Start/End 事件对的关联。

**定义位置**: `core/events/types.py`

### 类签名

```python
@dataclass(frozen=True)
class CorrelatedEvent(Event):
    """可关联事件基类"""
```

### 属性

#### correlation_id

```python
correlation_id: str = ""
```

关联 ID，同一对 Start/End 事件共享相同的 correlation_id。

### 说明

- Start 事件通过工厂方法 `create()` 生成 correlation_id
- End 事件复用 Start 事件的 correlation_id
- 用于关联请求的开始和结束

---

## HTTP 事件

### HttpRequestStartEvent

HTTP 请求开始事件，在发送 HTTP 请求前触发。

**定义位置**: `core/events/types.py`

#### 属性

```python
@dataclass(frozen=True)
class HttpRequestStartEvent(CorrelatedEvent):
    method: str = ""              # HTTP 方法
    url: str = ""                 # 请求 URL
    headers: dict[str, str] = field(default_factory=dict)  # 请求头
    params: dict[str, Any] = field(default_factory=dict)   # GET 参数
    body: str | None = None       # 请求体
```

#### 工厂方法

```python
@classmethod
def create(
    cls,
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    body: str | None = None,
    context: ExecutionContext | None = None,
) -> tuple[HttpRequestStartEvent, str]:
    """创建事件并返回 correlation_id

    自动注入当前 OpenTelemetry 追踪上下文。

    Returns:
        (event, correlation_id) 元组
    """
```

#### 使用示例

```python
from df_test_framework.core.events import HttpRequestStartEvent

# 创建事件
event, correlation_id = HttpRequestStartEvent.create(
    method="POST",
    url="https://api.example.com/users",
    headers={"Content-Type": "application/json"},
    body='{"name": "Alice"}',
)

# 发布事件
await event_bus.publish(event)
```

---

### HttpRequestEndEvent

HTTP 请求结束事件，在收到 HTTP 响应后触发。

**定义位置**: `core/events/types.py`

#### 属性

```python
@dataclass(frozen=True)
class HttpRequestEndEvent(CorrelatedEvent):
    method: str = ""              # HTTP 方法
    url: str = ""                 # 请求 URL
    status_code: int = 0          # 响应状态码
    duration: float = 0.0         # 请求耗时（秒）
    headers: dict[str, str] = field(default_factory=dict)  # 响应头
    body: str | None = None       # 响应体
```

#### 工厂方法

```python
@classmethod
def create(
    cls,
    correlation_id: str,
    method: str,
    url: str,
    status_code: int,
    duration: float,
    headers: dict[str, str] | None = None,
    body: str | None = None,
    context: ExecutionContext | None = None,
) -> HttpRequestEndEvent:
    """创建事件

    Args:
        correlation_id: 与 StartEvent 相同的关联 ID
        ...

    Returns:
        事件实例
    """
```

#### 使用示例

```python
from df_test_framework.core.events import HttpRequestEndEvent

# 创建事件（使用 StartEvent 的 correlation_id）
event = HttpRequestEndEvent.create(
    correlation_id=correlation_id,  # 来自 StartEvent
    method="POST",
    url="https://api.example.com/users",
    status_code=201,
    duration=0.234,
    headers={"Content-Type": "application/json"},
    body='{"id": 123, "name": "Alice"}',
)

# 发布事件
await event_bus.publish(event)
```

---

## 其他事件类型

框架定义了多种事件类型，用于不同场景的可观测性和组件通信。

### 数据库事件

- **DatabaseQueryStartEvent** - 数据库查询开始
- **DatabaseQueryEndEvent** - 数据库查询结束

### Web UI 事件

- **WebActionStartEvent** - Web 操作开始
- **WebActionEndEvent** - Web 操作结束

### 测试事件

- **TestStartEvent** - 测试开始
- **TestEndEvent** - 测试结束
- **TestSkippedEvent** - 测试跳过

### Fixture 事件

- **FixtureSetupEvent** - Fixture 设置
- **FixtureTeardownEvent** - Fixture 清理

---

## 使用指南

### 发布事件

```python
from df_test_framework.infrastructure.events import get_event_bus
from df_test_framework.core.events import HttpRequestStartEvent

# 获取事件总线
event_bus = get_event_bus()

# 创建并发布事件
event, correlation_id = HttpRequestStartEvent.create(
    method="GET",
    url="https://api.example.com/users",
)
await event_bus.publish(event)
```

### 订阅事件

```python
from df_test_framework.infrastructure.events import get_event_bus
from df_test_framework.core.events import HttpRequestEndEvent

event_bus = get_event_bus()

# 订阅事件
@event_bus.on(HttpRequestEndEvent)
async def on_http_request_end(event: HttpRequestEndEvent):
    print(f"HTTP {event.method} {event.url} - {event.status_code} ({event.duration}s)")
```

### 关联 Start/End 事件

```python
# 发布 Start 事件
start_event, correlation_id = HttpRequestStartEvent.create(
    method="POST",
    url="https://api.example.com/users",
)
await event_bus.publish(start_event)

# 执行操作
response = await http_client.post("/users", json={"name": "Alice"})

# 发布 End 事件（使用相同的 correlation_id）
end_event = HttpRequestEndEvent.create(
    correlation_id=correlation_id,  # 关联 Start 事件
    method="POST",
    url="https://api.example.com/users",
    status_code=response.status_code,
    duration=response.elapsed,
)
await event_bus.publish(end_event)
```

### 自定义事件

```python
from dataclasses import dataclass, field
from df_test_framework.core.events import Event

@dataclass(frozen=True)
class CustomEvent(Event):
    """自定义事件"""
    user_id: str = ""
    action: str = ""
    data: dict = field(default_factory=dict)

# 使用自定义事件
event = CustomEvent(
    user_id="user_001",
    action="login",
    data={"ip": "192.168.1.1"},
)
await event_bus.publish(event)
```

---

## 最佳实践

### 1. 使用工厂方法创建事件

```python
# ✅ 推荐：使用工厂方法
event, correlation_id = HttpRequestStartEvent.create(
    method="POST",
    url="/api/users",
)

# ❌ 不推荐：手动创建
event = HttpRequestStartEvent(
    method="POST",
    url="/api/users",
    correlation_id=generate_correlation_id(),
)
```

### 2. 保持 Start/End 事件关联

```python
# ✅ 推荐：保存 correlation_id
start_event, correlation_id = HttpRequestStartEvent.create(...)
await event_bus.publish(start_event)

result = await do_something()

end_event = HttpRequestEndEvent.create(
    correlation_id=correlation_id,  # 关联
    ...
)
await event_bus.publish(end_event)
```

### 3. 传递执行上下文

```python
from df_test_framework.core.context import get_current_context

# ✅ 推荐：传递当前上下文
ctx = get_current_context()
event, correlation_id = HttpRequestStartEvent.create(
    method="GET",
    url="/api/users",
    context=ctx,
)
```

---

## 相关文档

### 使用指南
- [EventBus 使用指南](../../guides/event_bus_guide.md) - 事件系统详细使用
- [Telemetry 可观测性指南](../../guides/telemetry_guide.md) - 可观测性系统使用

### API 参考
- [Core 层 API 参考](README.md) - Core 层概览
- [协议定义 API 参考](protocols.md) - 协议接口
- [上下文系统 API 参考](context.md) - 上下文管理

---

**完成时间**: 2026-01-17

