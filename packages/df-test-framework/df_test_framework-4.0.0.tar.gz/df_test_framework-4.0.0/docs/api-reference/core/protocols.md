# 协议定义 API 参考

> **最后更新**: 2026-01-17
> **适用版本**: v3.0.0+

## 概述

Core 层的协议定义模块提供了框架的核心接口协议，定义了各个组件的标准行为。

### 设计原则

- **纯抽象**: 只定义接口，不包含具体实现
- **零依赖**: 不依赖任何第三方库
- **类型安全**: 使用 Protocol 实现结构化类型检查
- **可扩展**: 支持多种实现方式

### 协议分类

```
protocols/
├── client.py       # 客户端协议（HTTP、Database、Redis）
├── event.py        # 事件协议（EventBus、EventHandler）
├── telemetry.py    # 可观测性协议（Tracer、Meter、Logger）
├── repository.py   # 数据访问协议（Repository、UnitOfWork）
└── plugin.py       # 插件协议（PluginManager）
```

---

## 客户端协议

### IHttpClient

HTTP 客户端协议，定义标准的 HTTP 请求接口。

**定义位置**: `core/protocols/client.py`

#### 属性

##### base_url

```python
@property
def base_url(self) -> str:
    """基础 URL"""
```

获取客户端的基础 URL。

#### 方法

##### request()

```python
async def request(
    self,
    method: str,
    path: str,
    **kwargs: Any,
) -> IHttpResponse:
    """发送 HTTP 请求

    Args:
        method: HTTP 方法（GET、POST、PUT、PATCH、DELETE）
        path: 请求路径
        **kwargs: 其他请求参数（headers、params、json、data 等）

    Returns:
        HTTP 响应对象
    """
```

##### get()

```python
async def get(self, path: str, **kwargs: Any) -> IHttpResponse:
    """GET 请求"""
```

##### post()

```python
async def post(self, path: str, **kwargs: Any) -> IHttpResponse:
    """POST 请求"""
```

##### put()

```python
async def put(self, path: str, **kwargs: Any) -> IHttpResponse:
    """PUT 请求"""
```

##### patch()

```python
async def patch(self, path: str, **kwargs: Any) -> IHttpResponse:
    """PATCH 请求"""
```

##### delete()

```python
async def delete(self, path: str, **kwargs: Any) -> IHttpResponse:
    """DELETE 请求"""
```

#### 使用示例

```python
from df_test_framework.core.protocols import IHttpClient

class MyHttpClient:
    """自定义 HTTP 客户端实现"""

    @property
    def base_url(self) -> str:
        return "https://api.example.com"

    async def request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> IHttpResponse:
        # 实现具体逻辑
        pass

    async def get(self, path: str, **kwargs: Any) -> IHttpResponse:
        return await self.request("GET", path, **kwargs)
```

---

### IHttpResponse

HTTP 响应协议，定义标准的响应数据访问接口。

**定义位置**: `core/protocols/client.py`

#### 属性

##### status_code

```python
@property
def status_code(self) -> int:
    """HTTP 状态码"""
```

##### headers

```python
@property
def headers(self) -> dict[str, str]:
    """响应头"""
```

##### body

```python
@property
def body(self) -> bytes:
    """响应体（字节）"""
```

##### text

```python
@property
def text(self) -> str:
    """响应体（文本）"""
```

##### json

```python
@property
def json(self) -> dict[str, Any]:
    """响应体（JSON）"""
```

##### is_success

```python
@property
def is_success(self) -> bool:
    """是否成功（2xx 状态码）"""
```

##### elapsed

```python
@property
def elapsed(self) -> float:
    """请求耗时（秒）"""
```

---

### IDatabaseClient

数据库客户端协议，定义数据库操作接口。

**定义位置**: `core/protocols/client.py`

#### 方法

##### session_factory()

```python
def session_factory(self) -> Any:
    """获取 Session 工厂

    Returns:
        SQLAlchemy Session 工厂
    """
```

##### execute()

```python
def execute(self, sql: str, params: dict[str, Any] | None = None) -> Any:
    """执行 SQL

    Args:
        sql: SQL 语句
        params: 参数字典

    Returns:
        执行结果
    """
```

---

### IRedisClient

Redis 客户端协议，定义 Redis 操作接口。

**定义位置**: `core/protocols/client.py`

#### 方法

##### get()

```python
async def get(self, key: str) -> str | None:
    """获取值

    Args:
        key: 键名

    Returns:
        值（不存在返回 None）
    """
```

##### set()

```python
async def set(
    self,
    key: str,
    value: str,
    ex: int | None = None,
) -> bool:
    """设置值

    Args:
        key: 键名
        value: 值
        ex: 过期时间（秒）

    Returns:
        是否成功
    """
```

##### delete()

```python
async def delete(self, key: str) -> int:
    """删除键

    Args:
        key: 键名

    Returns:
        删除的键数量
    """
```

##### exists()

```python
async def exists(self, key: str) -> bool:
    """检查键是否存在

    Args:
        key: 键名

    Returns:
        是否存在
    """
```

---

## 事件协议

### IEventHandler

事件处理器协议，定义事件处理接口。

**定义位置**: `core/protocols/event.py`

#### 方法

##### __call__()

```python
async def __call__(self, event: T) -> None:
    """处理事件

    Args:
        event: 事件对象
    """
```

#### 使用示例

```python
from df_test_framework.core.protocols import IEventHandler

class MyEventHandler:
    """自定义事件处理器"""

    async def __call__(self, event: MyEvent) -> None:
        print(f"处理事件: {event}")
```

---

### IEventBus

事件总线协议，定义发布/订阅模式的事件通信接口。

**定义位置**: `core/protocols/event.py`

#### 方法

##### subscribe()

```python
def subscribe(
    self,
    event_type: type[T],
    handler: Callable[[T], Awaitable[None]],
) -> None:
    """订阅特定类型事件

    Args:
        event_type: 事件类型
        handler: 事件处理器
    """
```

##### subscribe_all()

```python
def subscribe_all(
    self,
    handler: Callable[[Any], Awaitable[None]],
) -> None:
    """订阅所有事件

    Args:
        handler: 事件处理器
    """
```

##### unsubscribe()

```python
def unsubscribe(
    self,
    event_type: type[T],
    handler: Callable[[T], Awaitable[None]],
) -> None:
    """取消订阅

    Args:
        event_type: 事件类型
        handler: 事件处理器
    """
```

##### publish()

```python
async def publish(self, event: Any) -> None:
    """发布事件

    Args:
        event: 事件对象
    """
```

##### on()

```python
def on(
    self,
    event_type: type[T],
) -> Callable[[Callable[[T], Awaitable[None]]], Callable[[T], Awaitable[None]]]:
    """装饰器：订阅事件

    Args:
        event_type: 事件类型

    Returns:
        装饰器函数
    """
```

#### 使用示例

```python
from df_test_framework.core.protocols import IEventBus

# 订阅事件
async def handle_user_login(event: UserLoginEvent):
    print(f"用户登录: {event.user_id}")

event_bus.subscribe(UserLoginEvent, handle_user_login)

# 使用装饰器订阅
@event_bus.on(UserLoginEvent)
async def on_user_login(event: UserLoginEvent):
    print(f"用户登录: {event.user_id}")

# 发布事件
await event_bus.publish(UserLoginEvent(user_id=123))
```

---

## 可观测性协议

### ISpan

Span 协议，定义追踪 Span 的接口。

**定义位置**: `core/protocols/telemetry.py`

#### 方法

##### set_attribute()

```python
def set_attribute(self, key: str, value: Any) -> None:
    """设置 Span 属性

    Args:
        key: 属性键
        value: 属性值
    """
```

##### record_exception()

```python
def record_exception(self, exception: Exception) -> None:
    """记录异常

    Args:
        exception: 异常对象
    """
```

##### end()

```python
def end(self) -> None:
    """结束 Span"""
```

---

### ITracer

Tracer 协议，定义链路追踪接口。

**定义位置**: `core/protocols/telemetry.py`

#### 方法

##### start_span()

```python
def start_span(
    self,
    name: str,
    attributes: dict[str, Any] | None = None,
) -> ISpan:
    """创建 Span

    Args:
        name: Span 名称
        attributes: 初始属性

    Returns:
        Span 对象
    """
```

##### inject()

```python
def inject(self, carrier: dict[str, str]) -> None:
    """注入追踪上下文到载体

    Args:
        carrier: 载体字典（如 HTTP headers）
    """
```

##### extract()

```python
def extract(self, carrier: dict[str, str]) -> Any:
    """从载体提取追踪上下文

    Args:
        carrier: 载体字典（如 HTTP headers）

    Returns:
        追踪上下文
    """
```

---

### IMeter

Meter 协议，定义指标记录接口。

**定义位置**: `core/protocols/telemetry.py`

#### 方法

##### record_histogram()

```python
def record_histogram(
    self,
    name: str,
    value: float,
    attributes: dict[str, Any] | None = None,
) -> None:
    """记录直方图

    Args:
        name: 指标名称
        value: 指标值
        attributes: 属性标签
    """
```

##### increment_counter()

```python
def increment_counter(
    self,
    name: str,
    attributes: dict[str, Any] | None = None,
    amount: int = 1,
) -> None:
    """增加计数器

    Args:
        name: 计数器名称
        attributes: 属性标签
        amount: 增加量
    """
```

##### set_gauge()

```python
def set_gauge(
    self,
    name: str,
    value: float,
    attributes: dict[str, Any] | None = None,
) -> None:
    """设置仪表盘

    Args:
        name: 仪表盘名称
        value: 当前值
        attributes: 属性标签
    """
```

---

### ILogger

Logger 协议，定义日志记录接口。

**定义位置**: `core/protocols/telemetry.py`

#### 方法

##### debug()

```python
def debug(self, message: str, **kwargs: Any) -> None:
    """DEBUG 日志

    Args:
        message: 日志消息
        **kwargs: 结构化字段
    """
```

##### info()

```python
def info(self, message: str, **kwargs: Any) -> None:
    """INFO 日志

    Args:
        message: 日志消息
        **kwargs: 结构化字段
    """
```

##### warning()

```python
def warning(self, message: str, **kwargs: Any) -> None:
    """WARNING 日志

    Args:
        message: 日志消息
        **kwargs: 结构化字段
    """
```

##### error()

```python
def error(self, message: str, **kwargs: Any) -> None:
    """ERROR 日志

    Args:
        message: 日志消息
        **kwargs: 结构化字段
    """
```

##### log()

```python
def log(self, level: str, message: str, **kwargs: Any) -> None:
    """通用日志

    Args:
        level: 日志级别
        message: 日志消息
        **kwargs: 结构化字段
    """
```

---

### ITelemetry

统一可观测性协议，融合 Tracer + Meter + Logger。

**定义位置**: `core/protocols/telemetry.py`

#### 方法

##### span()

```python
def span(
    self,
    name: str,
    attributes: dict[str, Any] | None = None,
    *,
    record_exception: bool = True,
    log_level: str = "DEBUG",
) -> AbstractAsyncContextManager[ISpan]:
    """创建追踪 Span，同时记录指标和日志

    Args:
        name: Span 名称
        attributes: 初始属性
        record_exception: 是否自动记录异常
        log_level: 日志级别

    Returns:
        异步上下文管理器
    """
```

##### inject_context()

```python
def inject_context(self, carrier: dict[str, str]) -> None:
    """注入追踪上下文到载体

    Args:
        carrier: 载体字典
    """
```

##### extract_context()

```python
def extract_context(self, carrier: dict[str, str]) -> Any:
    """从载体提取追踪上下文

    Args:
        carrier: 载体字典

    Returns:
        追踪上下文
    """
```

#### 使用示例

```python
from df_test_framework.core.protocols import ITelemetry

# 使用 span 记录操作
async with telemetry.span("http.request", {"method": "POST"}) as span:
    response = await send_request()
    span.set_attribute("status_code", response.status_code)

# 自动产生：
# - Trace Span (链路追踪)
# - Metrics (指标统计: duration histogram, count counter)
# - Logs (结构化日志: Starting/Completed http.request)
```

---

## 数据访问协议

### IRepository

Repository 协议，定义泛型仓储接口。

**定义位置**: `core/protocols/repository.py`

#### 方法

##### find_by_id()

```python
def find_by_id(self, id: Any) -> T | None:
    """根据 ID 查找实体

    Args:
        id: 实体 ID

    Returns:
        实体对象（不存在返回 None）
    """
```

##### find_all()

```python
def find_all(self) -> Sequence[T]:
    """查找所有实体

    Returns:
        实体列表
    """
```

##### find_by()

```python
def find_by(self, **kwargs: Any) -> Sequence[T]:
    """根据条件查找实体

    Args:
        **kwargs: 查询条件

    Returns:
        实体列表
    """
```

##### create()

```python
def create(self, entity: T) -> T:
    """创建实体

    Args:
        entity: 实体对象

    Returns:
        创建后的实体
    """
```

##### update()

```python
def update(self, entity: T) -> T:
    """更新实体

    Args:
        entity: 实体对象

    Returns:
        更新后的实体
    """
```

##### delete()

```python
def delete(self, entity: T) -> None:
    """删除实体

    Args:
        entity: 实体对象
    """
```

##### delete_by_id()

```python
def delete_by_id(self, id: Any) -> bool:
    """根据 ID 删除实体

    Args:
        id: 实体 ID

    Returns:
        是否删除成功
    """
```

#### 使用示例

```python
from df_test_framework.core.protocols import IRepository

class UserRepository:
    """用户仓储实现"""

    def find_by_id(self, id: int) -> User | None:
        # 实现查询逻辑
        pass

    def create(self, entity: User) -> User:
        # 实现创建逻辑
        pass
```

---

### IUnitOfWork

Unit of Work 协议，定义工作单元模式接口。

**定义位置**: `core/protocols/repository.py`

#### 方法

##### __aenter__()

```python
async def __aenter__(self) -> IUnitOfWork:
    """进入异步上下文

    Returns:
        UnitOfWork 实例
    """
```

##### __aexit__()

```python
async def __aexit__(
    self,
    exc_type: type[BaseException] | None,
    exc_val: BaseException | None,
    exc_tb: Any,
) -> None:
    """退出异步上下文

    Args:
        exc_type: 异常类型
        exc_val: 异常值
        exc_tb: 异常追踪
    """
```

##### commit()

```python
async def commit(self) -> None:
    """提交事务"""
```

##### rollback()

```python
async def rollback(self) -> None:
    """回滚事务"""
```

##### register_repository()

```python
def register_repository(
    self,
    name: str,
    repo_class: type[IRepository[Any]],
) -> None:
    """注册 Repository

    Args:
        name: Repository 名称
        repo_class: Repository 类
    """
```

#### 使用示例

```python
from df_test_framework.core.protocols import IUnitOfWork

# 使用 UnitOfWork 管理事务
async with uow:
    user = uow.users.find_by_id(123)
    user.name = "Alice"
    uow.users.update(user)
    await uow.commit()
```

---

## 插件协议

### IPluginManager

插件管理器协议，定义插件注册和管理接口。

**定义位置**: `core/protocols/plugin.py`

#### 方法

##### register()

```python
def register(self, plugin: Any, name: str | None = None) -> str | None:
    """注册插件

    Args:
        plugin: 插件实例
        name: 插件名称（可选）

    Returns:
        注册成功返回插件名称，失败返回 None
    """
```

##### unregister()

```python
def unregister(self, plugin: Any) -> None:
    """注销插件

    Args:
        plugin: 要注销的插件实例
    """
```

##### hook

```python
@property
def hook(self) -> Any:
    """获取 Hook 调用代理

    通过此属性调用已注册插件的 hook 方法。

    Example:
        results = plugin_manager.hook.df_providers(settings=settings, logger=logger)
    """
```

##### discover_plugins()

```python
def discover_plugins(self, package: str) -> None:
    """自动发现并加载插件

    Args:
        package: 插件包路径
    """
```

##### get_plugins()

```python
def get_plugins(self) -> list[Any]:
    """获取所有已注册插件

    Returns:
        插件列表
    """
```

##### is_registered()

```python
def is_registered(self, plugin: Any) -> bool:
    """检查插件是否已注册

    Args:
        plugin: 插件实例

    Returns:
        是否已注册
    """
```

#### 使用示例

```python
from df_test_framework.core.protocols import IPluginManager

# 注册插件
plugin_manager.register(MyPlugin(), name="my_plugin")

# 调用 Hook
results = plugin_manager.hook.df_providers(settings=settings, logger=logger)

# 自动发现插件
plugin_manager.discover_plugins("my_package.plugins")

# 检查插件
if plugin_manager.is_registered(my_plugin):
    print("插件已注册")
```

---

## 相关文档

### 使用指南
- [中间件使用指南](../../guides/middleware_guide.md) - 中间件系统使用
- [EventBus 使用指南](../../guides/event_bus_guide.md) - 事件系统使用
- [Telemetry 可观测性指南](../../guides/telemetry_guide.md) - 可观测性系统使用
- [数据库使用指南](../../guides/database_guide.md) - Repository 和 UnitOfWork 使用

### 架构文档
- [五层架构详解](../../architecture/五层架构详解.md) - 架构层次说明
- [ARCHITECTURE_V4.0.md](../../architecture/ARCHITECTURE_V4.0.md) - v4.0 架构总览

### API 参考
- [Core 层 API 参考](README.md) - Core 层概览
- [中间件系统 API 参考](middleware.md) - 中间件 API
- [上下文系统 API 参考](context.md) - 上下文 API
- [事件类型 API 参考](events.md) - 事件类型定义
- [异常体系 API 参考](exceptions.md) - 异常类型定义
- [类型定义 API 参考](types.md) - 类型别名和协议

---

**完成时间**: 2026-01-17

