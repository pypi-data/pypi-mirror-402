# EventBus 使用指南

> **最后更新**: 2026-01-17
> **适用版本**: v3.17.0+（事件系统重构）

---

## 概述

EventBus 是 v3.14.0 引入的**发布/订阅**事件系统，用于解耦组件间的通信。

**核心优势**:
- ✅ 解耦：组件间无需直接依赖
- ✅ 可扩展：新增订阅者不影响发布者
- ✅ 异步：支持异步事件处理
- ✅ 类型安全：基于事件类的订阅
- ✅ 高性能：单一实例 + 作用域过滤（v3.46.1）

**v3.46.1 重大架构优化** ⚡:
- ✨ **单一 EventBus 实例** - 性能提升 100x，内存占用减少 99%
- ✨ **作用域过滤机制** - 通过 `scope` 字段实现测试隔离
- ✨ **统一事件发布接口** - `runtime.publish_event()` 自动注入 scope
- ✨ **简化 API** - 移除冗余方法，API 更清晰

**v3.17.0 特性**:
- ✨ 事件关联（correlation_id）- 关联 Start/End 事件对
- ✨ OpenTelemetry 整合 - 自动注入 trace_id/span_id
- ✨ Allure 深度整合 - AllureObserver 自动记录所有请求

---

## 快速开始

### 1. 基本用法（v3.46.1 推荐）

```python
from df_test_framework import HttpRequestEndEvent
from df_test_framework.infrastructure.events import get_global_event_bus

# 获取全局 EventBus 实例
bus = get_global_event_bus()

# 订阅事件（全局订阅）
@bus.on(HttpRequestEndEvent)
async def log_request(event: HttpRequestEndEvent):
    print(f"请求完成: {event.method} {event.url} - {event.status_code}")

# 在 pytest 测试中使用
def test_api_request(http_client):
    """http_client 自动使用全局 EventBus"""
    # 发送请求（自动触发事件）
    response = http_client.get("/users")
    # 输出: 请求完成: GET https://api.example.com/users - 200
    assert response.status_code == 200
```

### 2. 订阅多个事件

```python
from df_test_framework import HttpRequestEndEvent, DatabaseQueryEndEvent
from df_test_framework.infrastructure.events import get_global_event_bus

bus = get_global_event_bus()

# HTTP 事件（全局订阅）
@bus.on(HttpRequestEndEvent)
async def log_http(event):
    print(f"HTTP: {event.url} - {event.duration:.2f}s")

# 数据库事件（全局订阅）
@bus.on(DatabaseQueryEndEvent)
async def log_db(event):
    print(f"SQL: {event.sql} ({event.row_count} rows, {event.duration:.2f}s)")

# 在测试中使用（所有客户端自动使用全局 EventBus）
def test_api_and_db(http_client, database):
    # 所有操作自动触发事件
    http_client.get("/api")
    database.execute("SELECT * FROM users")
```

### 3. 作用域订阅（v3.46.1 新特性）

```python
from df_test_framework import HttpRequestEndEvent
from df_test_framework.infrastructure.events import get_global_event_bus

bus = get_global_event_bus()

# 订阅特定测试的事件（作用域订阅）
@pytest.fixture
def http_logger(request, runtime):
    """只记录当前测试的 HTTP 请求"""
    test_scope = request.node.nodeid

    events = []

    async def collect_events(event):
        events.append(event)

    # 订阅时指定 scope - 只接收该测试的事件
    bus.subscribe(HttpRequestEndEvent, collect_events, scope=test_scope)

    yield events

def test_with_scoped_logging(test_runtime, http_logger):
    """使用 test_runtime 发布的事件会被 http_logger 捕获"""
    from df_test_framework import HttpClient

    # 使用 test_runtime（带 scope）创建客户端
    client = HttpClient(base_url="...", runtime=test_runtime)
    client.get("/users")

    # 只有当前测试的事件
    assert len(http_logger) == 1
```

---

## 框架内置事件

### HTTP 事件

```python
from df_test_framework.core.events import (
    HttpRequestStartEvent,  # 请求开始
    HttpRequestEndEvent,    # 请求结束
    HttpRequestErrorEvent,  # 请求错误
)

@bus.on(HttpRequestEndEvent)
async def on_http_end(event):
    print(f"Method: {event.method}")
    print(f"URL: {event.url}")
    print(f"Status: {event.status_code}")
    print(f"Duration: {event.duration}s")
    print(f"Timestamp: {event.timestamp}")
```

### 数据库事件

```python
from df_test_framework.core.events import (
    DatabaseQueryStartEvent,  # 查询开始
    DatabaseQueryEndEvent,    # 查询结束
)

@bus.on(DatabaseQueryEndEvent)
async def on_query_end(event):
    print(f"SQL: {event.sql}")
    print(f"Params: {event.params}")
    print(f"Row Count: {event.row_count}")
    print(f"Duration: {event.duration}s")
```

### 消息队列事件

> **v3.34.1 重构**: MQ 事件已重构为 Start/End/Error 三态模式，与 HTTP/gRPC/GraphQL 保持一致。

```python
from df_test_framework.core.events import (
    # MQ 发布事件
    MessagePublishStartEvent,  # 发布开始
    MessagePublishEndEvent,    # 发布成功
    MessagePublishErrorEvent,  # 发布失败
    # MQ 消费事件
    MessageConsumeStartEvent,  # 消费开始
    MessageConsumeEndEvent,    # 消费成功
    MessageConsumeErrorEvent,  # 消费失败
)

@bus.on(MessagePublishEndEvent)
async def on_message_published(event):
    print(f"Type: {event.messenger_type}")  # kafka/rabbitmq/rocketmq
    print(f"Topic: {event.topic}")
    print(f"Message ID: {event.message_id}")
    print(f"Duration: {event.duration:.3f}s")

@bus.on(MessageConsumeEndEvent)
async def on_message_consumed(event):
    print(f"Type: {event.messenger_type}")
    print(f"Topic: {event.topic}")
    print(f"Consumer Group: {event.consumer_group}")
    print(f"Processing Time: {event.processing_time:.3f}s")

@bus.on(MessagePublishErrorEvent)
async def on_publish_error(event):
    print(f"❌ Publish failed: {event.topic}")
    print(f"   Error: {event.error_type}: {event.error_message}")
```

---

## 实用场景

### 场景 1: 慢请求告警

```python
@bus.on(HttpRequestEndEvent)
async def alert_slow_requests(event):
    if event.duration > 5.0:
        # 发送告警
        print(f"⚠️ 慢请求: {event.url} 耗时 {event.duration:.2f}s")
        # 可以调用告警接口、发送邮件等
```

### 场景 2: 请求统计

```python
from collections import defaultdict

stats = defaultdict(int)

@bus.on(HttpRequestEndEvent)
async def collect_stats(event):
    stats[event.method] += 1
    stats["total"] += 1

    if stats["total"] % 10 == 0:
        print(f"统计: {dict(stats)}")
```

### 场景 3: 自动重试记录

```python
@bus.on(HttpRequestErrorEvent)
async def log_errors(event):
    print(f"❌ 请求失败: {event.url}")
    print(f"   错误: {event.error}")
    print(f"   重试次数: {event.retry_count}")
```

### 场景 4: 慢 SQL 优化提示

```python
@bus.on(DatabaseQueryEndEvent)
async def optimize_slow_queries(event):
    if event.duration > 1.0:
        print(f"🐌 慢查询: {event.sql}")
        print(f"   耗时: {event.duration:.2f}s")
        print(f"   建议: 添加索引或优化查询")
```

### 场景 5: Allure 自动记录

```python
import allure

@bus.on(HttpRequestEndEvent)
async def record_to_allure(event):
    status_emoji = "✓" if 200 <= event.status_code < 300 else "✗"
    step_name = f"{event.method} {event.url} {status_emoji} {event.status_code}"

    with allure.step(step_name):
        allure.attach(
            f"Duration: {event.duration:.3f}s\nStatus: {event.status_code}",
            name="Response Info",
            attachment_type=allure.attachment_type.TEXT
        )
```

---

## v3.46.1 作用域过滤机制

### 核心概念

v3.46.1 引入**作用域过滤**机制，实现单一 EventBus 实例下的事件隔离。

**架构演进**:
- ❌ **v3.17.0 - v3.46.0**: 每个测试创建独立 EventBus → 性能开销大
- ✅ **v3.46.1**: 单一 EventBus + scope 过滤 → 性能优化 100x

### scope 的语义

```python
# scope=None: 全局事件
# - 用于 session 级别的客户端（http_client, database）
# - 用于全局观察者（allure_observer）
event = HttpRequestEndEvent(url="/api", scope=None)

# scope="test_id": 测试专属事件
# - 用于 function 级别的 actions（UI 测试）
# - 用于测试专属观察者（console_debugger）
event = HttpRequestEndEvent(url="/api", scope="test::test_ui_workflow")
```

### 订阅模式

#### 1. 全局订阅（scope=None）

```python
from df_test_framework.infrastructure.events import get_global_event_bus

bus = get_global_event_bus()

# 全局订阅 - 接收所有事件（不论 scope）
bus.subscribe(
    HttpRequestEndEvent,
    handler,
    scope=None  # 关键：None 表示接收所有事件
)

# 适用场景：
# - Allure 报告（记录所有测试的请求）
# - 全局监控（性能统计、错误告警）
# - 日志记录（记录所有操作）
```

#### 2. 作用域订阅（scope="test_id"）

```python
# 作用域订阅 - 只接收特定 scope 的事件
bus.subscribe(
    HttpRequestEndEvent,
    handler,
    scope="test_id"  # 关键：只接收该 scope 的事件
)

# 适用场景：
# - console_debugger（只显示当前测试的请求）
# - 测试专属统计（只统计当前测试的性能）
# - UI 测试隔离（多个测试并发时互不干扰）
```

### 事件发布（自动注入 scope）

#### 使用 runtime.publish_event()（推荐）

```python
from df_test_framework.bootstrap.runtime import RuntimeContext

# session 级别客户端 - 发布全局事件（scope=None）
@pytest.fixture(scope="session")
def http_client(runtime: RuntimeContext):
    """runtime.scope = None（session 级别）"""
    client = HttpClient(base_url="...", runtime=runtime)
    client.get("/api")  # 发布事件：scope=None

# function 级别 actions - 发布测试专属事件（scope="test_id"）
@pytest.fixture(scope="function")
def test_runtime(request, runtime):
    """带有测试 scope 的 runtime"""
    test_scope = request.node.nodeid
    return runtime.with_scope(test_scope)

def test_ui(page, test_runtime):
    """test_runtime.scope = "test::test_ui" """
    app = MyAppActions(page, runtime=test_runtime)
    app.click_button("button")  # 发布事件：scope="test::test_ui"
```

#### 作用域匹配规则

```python
# 发布事件
event = HttpRequestEndEvent(url="/api", scope="test_1")

# 订阅者 1: scope=None（全局订阅）
bus.subscribe(HttpRequestEndEvent, handler1, scope=None)
# ✅ 接收：scope=None, scope="test_1", scope="test_2", ...

# 订阅者 2: scope="test_1"（作用域订阅）
bus.subscribe(HttpRequestEndEvent, handler2, scope="test_1")
# ✅ 接收：scope="test_1"
# ❌ 忽略：scope=None, scope="test_2", ...

# 订阅者 3: scope="test_2"（作用域订阅）
bus.subscribe(HttpRequestEndEvent, handler3, scope="test_2")
# ❌ 忽略：scope=None, scope="test_1", ...
```

### 完整示例

#### 全局订阅（Allure）

```python
@pytest.fixture(scope="session")
def _auto_allure_observer(runtime):
    """全局观察者 - 记录所有测试的请求"""
    from df_test_framework.testing.reporting.allure import AllureObserver

    observer = AllureObserver()

    # 使用 scope=None 全局订阅
    runtime.event_bus.subscribe(
        HttpRequestEndEvent,
        observer.handle_http_request_end_event,
        scope=None  # 接收所有测试的事件
    )

    yield observer
```

#### 作用域订阅（Console Debugger）

```python
@pytest.fixture(scope="function")
def console_debugger(request, runtime):
    """测试专属观察者 - 只显示当前测试的请求"""
    from df_test_framework.testing.debugging import ConsoleDebugObserver

    # 获取当前测试的 scope
    test_scope = None
    if "test_runtime" in request.fixturenames:
        test_runtime = request.getfixturevalue("test_runtime")
        test_scope = test_runtime.scope

    debugger = ConsoleDebugObserver()

    # 使用测试 scope 订阅
    runtime.event_bus.subscribe(
        HttpRequestStartEvent,
        debugger.handle_http_start,
        scope=test_scope  # 只接收该测试的事件
    )

    yield debugger
```

### 性能对比

| 指标 | v3.46.0 | v3.46.1 | 优化 |
|------|---------|---------|------|
| EventBus 实例数 | 100 个（100 个测试） | 1 个 | **99% 减少** |
| 订阅者注册次数 | 每个测试重新注册 | 只注册一次 | **100x 减少** |
| 内存占用 | 高（重复实例） | 低（单一实例） | **99% 减少** |
| 事件发布开销 | O(m) | O(m) + O(1) 过滤 | **几乎无影响** |

> m = 订阅者数量

### 测试隔离保证

```python
# 测试 A（API 测试 - session 级别）
def test_api_a(http_client):
    http_client.get("/api/a")
    # 发布事件：scope=None（全局）

# 测试 B（API 测试 - session 级别）
def test_api_b(http_client):
    http_client.get("/api/b")
    # 发布事件：scope=None（全局）

# 测试 C（UI 测试 - function 级别）
def test_ui_c(page, test_runtime):
    app = MyAppActions(page, runtime=test_runtime)
    app.click_button("button")
    # 发布事件：scope="test::test_ui_c"（隔离）

# 测试 D（UI 测试 - function 级别）
def test_ui_d(page, test_runtime):
    app = MyAppActions(page, runtime=test_runtime)
    app.click_button("button")
    # 发布事件：scope="test::test_ui_d"（隔离）
```

**隔离效果**:
- ✅ Allure 观察者（scope=None）：接收所有测试的事件
- ✅ console_debugger（scope="test::test_ui_c"）：只接收测试 C 的事件
- ✅ console_debugger（scope="test::test_ui_d"）：只接收测试 D 的事件

---

## 自定义事件

### 1. 定义事件类

```python
from df_test_framework.core.events import Event
from datetime import datetime

class OrderCreatedEvent(Event):
    """订单创建事件"""

    def __init__(self, order_id: str, amount: float, user_id: int):
        super().__init__()
        self.order_id = order_id
        self.amount = amount
        self.user_id = user_id
```

### 2. 发布自定义事件

```python
# 创建并发布事件
event = OrderCreatedEvent(
    order_id="ORDER001",
    amount=100.0,
    user_id=123
)

await bus.publish(event)
```

### 3. 订阅自定义事件

```python
@bus.on(OrderCreatedEvent)
async def send_notification(event):
    print(f"新订单: {event.order_id}")
    print(f"金额: {event.amount}")
    # 发送通知...
```

---

## 高级用法

### 作用域过滤（v3.46.1）

```python
from df_test_framework.infrastructure.events import get_global_event_bus

bus = get_global_event_bus()

# 1. 全局订阅（接收所有事件）
bus.subscribe(HttpRequestEndEvent, handler1, scope=None)

# 2. 作用域订阅（只接收特定 scope 的事件）
bus.subscribe(HttpRequestEndEvent, handler2, scope="test_id")

# 3. 清理指定 scope 的订阅（可选）
bus.clear_scope("test_id")
```

### 全局订阅（所有事件类型）

```python
# 订阅所有事件类型
async def log_all_events(event):
    print(f"事件: {type(event).__name__}")

# 全局订阅所有事件类型
bus.subscribe_all(log_all_events)

# 作用域订阅所有事件类型（v3.46.1）
bus.subscribe_all(log_all_events, scope="test_id")
```

### 取消订阅

```python
# 订阅
async def my_handler(event):
    print(event.url)

bus.subscribe(HttpRequestEndEvent, my_handler)

# 取消订阅
bus.unsubscribe(HttpRequestEndEvent, my_handler)

# 取消全局订阅
bus.unsubscribe_all(log_all_events)

# v3.46.1: 清理指定 scope 的所有订阅
bus.clear_scope("test_id")
```

### 手动发布事件（带 scope）

```python
from df_test_framework.core.events import HttpRequestEndEvent

# 发布全局事件
event = HttpRequestEndEvent(
    method="GET",
    url="/api",
    status_code=200,
    duration=0.5,
    scope=None  # 全局事件
)
bus.publish_sync(event)

# 发布测试专属事件
event = HttpRequestEndEvent(
    method="GET",
    url="/api",
    status_code=200,
    duration=0.5,
    scope="test::test_api"  # 测试专属事件
)
bus.publish_sync(event)
```

---

## 最佳实践

### 1. 事件处理器保持轻量

```python
# ✅ 好：快速处理
@bus.on(HttpRequestEndEvent)
async def quick_handler(event):
    logger.info(f"Request: {event.url}")

# ❌ 差：耗时操作阻塞
# @bus.on(HttpRequestEndEvent)
# async def slow_handler(event):
#     time.sleep(10)  # 阻塞其他事件处理
```

### 2. 异常处理

```python
@bus.on(HttpRequestEndEvent)
async def safe_handler(event):
    try:
        # 处理逻辑
        process(event)
    except Exception as e:
        logger.error(f"事件处理失败: {e}")
        # 不要让异常传播，影响其他订阅者
```

### 3. 使用类型注解

```python
from df_test_framework.core.events import HttpRequestEndEvent

@bus.on(HttpRequestEndEvent)
async def typed_handler(event: HttpRequestEndEvent):
    # IDE 有类型提示
    print(event.url)  # ✅ 有提示
```

### 4. 支持同步和异步处理器（v3.18.0）

```python
# 异步处理器（推荐）
@bus.on(HttpRequestEndEvent)
async def async_handler(event):
    await process_async(event)

# 同步处理器（也支持）
@bus.on(HttpRequestEndEvent)
def sync_handler(event):
    process_sync(event)
```

---

## v3.17.0 新特性详解

### 1. 事件关联（Event Correlation）

**问题**: 如何关联同一个请求的 Start 和 End 事件？

**解决方案**: v3.17.0 引入 `correlation_id`，自动关联事件对。

```python
from df_test_framework import EventBus, HttpRequestStartEvent, HttpRequestEndEvent

bus = EventBus()

# 记录所有请求
requests = {}

@bus.on(HttpRequestStartEvent)
def on_start(event):
    # Start 事件包含 correlation_id
    requests[event.correlation_id] = {
        "start_time": event.timestamp,
        "url": event.url
    }
    print(f"请求开始: {event.url} [cor:{event.correlation_id}]")

@bus.on(HttpRequestEndEvent)
def on_end(event):
    # End 事件的 correlation_id 与 Start 相同
    if event.correlation_id in requests:
        start_info = requests[event.correlation_id]
        duration = event.duration
        print(f"请求完成: {event.url} [cor:{event.correlation_id}]")
        print(f"  实际耗时: {duration}s")
        del requests[event.correlation_id]

# HttpClient 自动生成 correlation_id
client = HttpClient(base_url="...", event_bus=bus)
response = client.get("/users")
# 输出:
# 请求开始: /users [cor:cor-a1b2c3d4e5f6]
# 请求完成: /users [cor:cor-a1b2c3d4e5f6]
```

**工作原理**:
1. HttpClient 创建 Start 事件时生成 `correlation_id`
2. End 事件复用相同的 `correlation_id`
3. 订阅者通过 `correlation_id` 匹配事件对

### 2. OpenTelemetry 整合

**v3.17.0 自动注入追踪上下文到事件**，无需手动配置。

```python
from opentelemetry import trace
from df_test_framework import EventBus, HttpRequestEndEvent

bus = EventBus()

@bus.on(HttpRequestEndEvent)
def on_request(event):
    # v3.17.0: 事件自动包含 trace_id 和 span_id
    print(f"Trace ID: {event.trace_id}")     # 32 字符十六进制
    print(f"Span ID: {event.span_id}")       # 16 字符十六进制
    print(f"Correlation: {event.correlation_id}")  # cor-{12hex}

# 在 Span 上下文中发送请求
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("test-api-call") as span:
    client = HttpClient(base_url="...", event_bus=bus)
    response = client.get("/users")
    # 事件自动包含当前 Span 的 trace_id 和 span_id
```

**与 Allure 集成**:

```python
# v3.17.0: AllureObserver 自动提取追踪信息
def test_with_tracing(allure_observer, http_client):
    response = http_client.get("/users")
    # ✅ Allure 报告自动显示:
    #    - Trace ID: 1234567890abcdef1234567890abcdef
    #    - Span ID: 1234567890abcdef
    #    - Correlation ID: cor-a1b2c3d4e5f6
```

### 3. 测试隔离（Test Isolation）

**问题**: 并发测试时事件互相干扰。

**v3.17.0 - v3.46.0 解决方案**: 每个测试独立的 EventBus 实例（已废弃）。

**v3.46.1 最优解决方案**: 单一 EventBus + 作用域过滤（性能优化 100x）。

```python
from df_test_framework.infrastructure.events import get_global_event_bus

# 全局单一 EventBus 实例
bus = get_global_event_bus()

def test_isolated_events_1(test_runtime):
    """测试 1 - 使用 test_runtime.scope 隔离事件"""
    events = []

    @bus.on(HttpRequestEndEvent)
    async def collect(event):
        # 只收集当前测试的事件
        if event.scope == test_runtime.scope:
            events.append(event)

    # 或者使用作用域订阅（推荐）
    bus.subscribe(HttpRequestEndEvent, collect, scope=test_runtime.scope)

    # 使用 test_runtime 创建客户端（自动注入 scope）
    client = HttpClient(base_url="...", runtime=test_runtime)
    client.get("/users")

    assert len(events) == 1  # ✅ 只有本测试的事件

def test_isolated_events_2(test_runtime):
    """测试 2 - 独立的 scope，不受测试 1 影响"""
    events = []

    bus.subscribe(HttpRequestEndEvent, collect, scope=test_runtime.scope)

    client = HttpClient(base_url="...", runtime=test_runtime)
    client.get("/orders")

    assert len(events) == 1  # ✅ 不受其他测试影响
```

**v3.46.1 优势**:
- ✅ 单一 EventBus 实例，性能提升 100x
- ✅ 订阅者只注册一次，内存占用减少 99%
- ✅ 通过 scope 过滤实现测试隔离
- ✅ 无需手动清理（scope 过滤自动隔离）

### 4. Allure 深度整合（v3.17.0）

**AllureObserver**: 自动记录所有 HTTP 请求到 Allure 报告。

```python
# 使用 allure_observer fixture（推荐）
def test_with_allure(allure_observer, http_client):
    response = http_client.get("/users")
    # ✅ 自动记录到 Allure:
    #    - 完整请求体和响应体
    #    - OpenTelemetry trace_id/span_id
    #    - 响应时间
    #    - 事件关联 ID

# 手动创建 AllureObserver
from df_test_framework.testing.reporting.allure import AllureObserver

def test_manual_observer():
    test_bus = EventBus()
    observer = AllureObserver(test_bus)

    client = HttpClient(base_url="...", event_bus=test_bus)
    response = client.get("/users")
    # 所有请求自动记录
```

**支持的协议**:
- ✅ HTTP/REST
- ✅ GraphQL（v3.11+）
- ✅ gRPC（v3.11+）

**记录内容**:
- 请求方法、URL、Headers、Body
- 响应状态码、Headers、Body（支持 gzip/deflate 解压）
- OpenTelemetry 追踪信息（trace_id, span_id）
- 事件关联 ID（correlation_id）
- 响应时间
- 错误信息（如有）

---

## 事件参考

### 事件基础字段

所有事件都包含以下字段：

```python
class Event:
    timestamp: datetime        # 事件时间
    correlation_id: str        # v3.17.0: 关联 ID (cor-{12hex})
    scope: str | None          # v3.46.1: 事件作用域（用于过滤）
    # scope=None: 全局事件（session 级别）
    # scope="test_id": 测试专属事件（function 级别）
```

**OpenTelemetry 追踪字段**（v3.17.0）:

```python
class Event:
    trace_id: str | None    # OpenTelemetry Trace ID（32 字符十六进制）
    span_id: str | None     # OpenTelemetry Span ID（16 字符十六进制）
```

### HTTP 事件字段

#### HttpRequestStartEvent

```python
event_id: str              # evt-a1b2c3d4e5f6
correlation_id: str        # cor-x7y8z9a1b2c3
method: str                # GET/POST/PUT/DELETE
url: str                   # https://api.example.com/users
headers: dict              # 请求头
body: Any | None           # 请求体
timestamp: datetime
trace_id: str | None       # OpenTelemetry Trace ID
span_id: str | None        # OpenTelemetry Span ID
```

#### HttpRequestEndEvent

```python
event_id: str              # evt-b2c3d4e5f6a1
correlation_id: str        # cor-x7y8z9a1b2c3 (与 Start 相同)
method: str
url: str
status_code: int
headers: dict              # 响应头
body: Any | None           # v3.17.0: 响应体
duration: float            # 耗时（秒）
timestamp: datetime
trace_id: str | None
span_id: str | None
```

---

## 版本特性对比

| 特性 | v3.14.0 | v3.17.0 | v3.46.1 |
|------|---------|---------|---------|
| 基础发布/订阅 | ✅ | ✅ | ✅ |
| 异步事件处理 | ✅ | ✅ | ✅ |
| 内置事件（HTTP/DB/MQ） | ✅ | ✅ | ✅ |
| 事件关联（correlation_id） | ❌ | ✅ | ✅ |
| OpenTelemetry 整合 | ❌ | ✅ | ✅ |
| 测试隔离 | ❌ | ✅（独立实例） | ✅（作用域过滤） |
| AllureObserver | ❌ | ✅ | ✅ |
| 响应体记录 | ❌ | ✅ | ✅ |
| **单一 EventBus 实例** | ❌ | ❌ | ✅ |
| **作用域过滤（scope）** | ❌ | ❌ | ✅ |
| **runtime.publish_event()** | ❌ | ❌ | ✅ |
| **性能优化（100x）** | - | - | ✅ |
| **内存优化（99% 减少）** | - | - | ✅ |

**架构演进**:
- **v3.14.0**: 基础 EventBus 实现
- **v3.17.0**: 添加追踪和关联功能，每个测试独立 EventBus
- **v3.46.1**: 单一 EventBus + 作用域过滤，性能和内存优化

---

## 参考资料

- [快速开始](../user-guide/QUICK_START.md)
- [快速参考](../user-guide/QUICK_REFERENCE.md)
- [中间件使用指南](middleware_guide.md)
- **[v3.46.1 发布说明](../releases/v3.46.1.md) - EventBus 架构优化**
- [v3.17.0 发布说明](../releases/v3.17.0.md)
- [v3.17.0 架构设计](../architecture/V3.17_EVENT_SYSTEM_REDESIGN.md)
