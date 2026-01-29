# Bootstrap 引导系统指南

> **最后更新**: 2026-01-17
> **适用版本**: v3.16.0+（Bootstrap 架构），v4.0.0+（异步支持）

## 概述

Bootstrap 是 DF Test Framework 的引导层（Layer 4），负责框架的初始化、配置加载和运行时管理。

### 核心组件

- **Bootstrap**: 链式配置引导器，用于配置 settings、logging、providers、plugins
- **RuntimeContext**: 运行时上下文，保持框架运行时的单例（settings、logger、providers、event_bus）
- **Provider**: 服务提供者，负责创建和管理各种能力层服务（HTTP、Database、Redis 等）
- **ProviderRegistry**: 提供者注册表，管理所有服务提供者

### 架构位置

```
Layer 4 ─── bootstrap/          # 引导层（本指南）
Layer 3 ─── testing/ + cli/     # 门面层
Layer 2 ─── capabilities/       # 能力层
Layer 1 ─── infrastructure/     # 基础设施
Layer 0 ─── core/               # 核心层
```

**依赖规则**: Bootstrap 作为引导层，可以依赖所有其他层（Layer 0-3），但其他层不应依赖 bootstrap。

---

## 快速开始

### 基本用法

```python
from df_test_framework import Bootstrap

# 1. 创建 Bootstrap 实例
app = Bootstrap().build()

# 2. 运行并获取 RuntimeContext
runtime = app.run()

# 3. 使用 RuntimeContext 获取服务
http_client = runtime.http_client()
database = runtime.database()
redis = runtime.redis()

# 4. 使用服务
response = http_client.get("/users")
users = database.query_all("SELECT * FROM users")
```

### 自定义配置

```python
from df_test_framework import Bootstrap
from myproject.config import MySettings

# 使用自定义配置类
app = Bootstrap().with_settings(
    MySettings,
    profile="dev",  # 指定环境
    config_dir="config"  # 配置目录
).build()

runtime = app.run()
```

### 在 pytest 中使用

框架已自动集成 pytest，无需手动初始化：

```python
def test_example(runtime):
    """runtime fixture 自动提供 RuntimeContext"""
    http_client = runtime.http_client()
    response = http_client.get("/users")
    assert response.status_code == 200
```

---

## Bootstrap 类

> **引入版本**: v3.16.0
> **职责**: 链式配置框架初始化参数

### 基本结构

```python
from df_test_framework import Bootstrap

bootstrap = (Bootstrap()
    .with_settings(MySettings, profile="dev")
    .with_logging(level="DEBUG", json_output=False)
    .with_plugin("myproject.plugins.custom_plugin")
    .build())

runtime = bootstrap.run()
```

### 配置方法

#### with_settings() - 配置 Settings

```python
bootstrap.with_settings(
    settings_cls=MySettings,  # Settings 类
    profile="dev",            # 环境配置（dev/test/staging/prod）
    config_dir="config"       # 配置目录
)
```

**参数说明**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `settings_cls` | type[FrameworkSettings] | FrameworkSettings | Settings 类 |
| `profile` | str | None | 环境配置，优先级高于 ENV 环境变量 |
| `config_dir` | str \| Path | "config" | 配置目录 |

**配置加载优先级**：
1. `profile` 参数（最高优先级）
2. `ENV` 环境变量
3. `default.yaml`（默认配置）

#### with_logging() - 配置日志

```python
bootstrap.with_logging(
    level="DEBUG",        # 日志级别
    json_output=False     # 是否使用 JSON 输出
)
```

**参数说明**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `level` | str | "INFO" | 日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL） |
| `json_output` | bool | None | JSON 输出（None=根据环境自动判断） |

#### with_plugin() - 注册插件

```python
bootstrap.with_plugin("myproject.plugins.custom_plugin")
```

**参数说明**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `plugin` | str \| object | 插件路径或插件实例 |

---

## RuntimeContext

> **引入版本**: v3.16.0
> **职责**: 运行时上下文，保持框架运行时的单例

### 核心属性

```python
@dataclass(frozen=True)
class RuntimeContext:
    settings: FrameworkSettings  # 框架配置
    logger: Logger               # 日志记录器
    providers: ProviderRegistry  # 服务提供者注册表
    event_bus: EventBus          # 事件总线（v3.44.0）
    extensions: ExtensionManager # 扩展管理器
    scope: str | None            # 事件作用域（v3.46.1）
```

### 获取服务

RuntimeContext 提供了便捷方法来获取各种服务：

```python
# HTTP 客户端
http_client = runtime.http_client()          # 同步
async_http_client = runtime.async_http_client()  # 异步（v4.0.0）

# 数据库
database = runtime.database()                # 同步
async_database = runtime.async_database()    # 异步（v4.0.0）

# Redis
redis = runtime.redis()                      # 同步
async_redis = runtime.async_redis()          # 异步（v4.0.0）

# 存储
local_file = runtime.local_file()            # 本地文件
s3 = runtime.s3()                            # S3 对象存储
oss = runtime.oss()                          # 阿里云 OSS
```

### 事件发布

RuntimeContext 集成了 EventBus，支持事件发布：

```python
from df_test_framework.core.events import Event

# 发布事件
runtime.publish_event(Event(
    type="custom.event",
    data={"key": "value"}
))

# 订阅事件
def handler(event):
    print(f"收到事件: {event.type}")

runtime.event_bus.subscribe("custom.event", handler)
```

### 作用域管理（v3.46.1）

RuntimeContext 支持事件作用域，用于测试隔离：

```python
# 创建带作用域的 RuntimeContext
test_runtime = runtime.with_scope("test_001")

# 发布事件时自动注入 scope
test_runtime.publish_event(Event(type="test.event"))

# 清理作用域
runtime.event_bus.clear_scope("test_001")
```

---

## Provider 系统

> **引入版本**: v3.16.0
> **职责**: 服务提供者，负责创建和管理各种能力层服务

### Provider 协议

```python
class Provider(Protocol):
    def get(self, context: RuntimeContext): ...
    def shutdown(self) -> None: ...
```

### SingletonProvider

单例提供者，确保服务只创建一次：

```python
from df_test_framework.bootstrap import SingletonProvider

def http_factory(context):
    return HttpClient(base_url=context.settings.http.base_url)

http_provider = SingletonProvider(http_factory)
```

**特性**：
- 线程安全（双重检查锁定）
- 自动调用 `close()` 或 `shutdown()` 方法
- 支持 `reset()` 重置单例（测试用）

### 自定义 Provider

```python
from df_test_framework.bootstrap import default_providers, SingletonProvider

def custom_providers():
    """自定义 Provider 工厂"""
    # 获取默认 providers
    registry = default_providers()

    # 注册自定义服务
    def custom_service_factory(context):
        return CustomService(context.settings.custom)

    registry.register("custom_service", SingletonProvider(custom_service_factory))

    return registry

# 使用自定义 providers
app = Bootstrap().with_provider_factory(custom_providers).build()
runtime = app.run()

# 获取自定义服务
custom_service = runtime.get("custom_service")
```

---

## 最佳实践

### 1. 配置管理

```python
# ✅ 推荐：使用环境配置
Bootstrap().with_settings(MySettings, profile="dev")

# ✅ 推荐：配置文件分层
# config/default.yaml - 默认配置
# config/dev.yaml - 开发环境
# config/test.yaml - 测试环境
# config/prod.yaml - 生产环境

# ❌ 不推荐：硬编码配置
Bootstrap().with_settings(MySettings)  # 依赖环境变量
```

### 2. 日志配置

```python
# ✅ 开发环境：DEBUG 级别，彩色输出
Bootstrap().with_logging(level="DEBUG", json_output=False)

# ✅ 生产环境：INFO 级别，JSON 输出
Bootstrap().with_logging(level="INFO", json_output=True)

# ❌ 不推荐：生产环境使用 DEBUG
Bootstrap().with_logging(level="DEBUG")  # 性能影响
```

### 3. 插件注册

```python
# ✅ 推荐：使用插件路径
Bootstrap().with_plugin("myproject.plugins.monitoring")

# ✅ 推荐：按需注册插件
if settings.monitoring.enabled:
    Bootstrap().with_plugin("myproject.plugins.monitoring")

# ❌ 不推荐：注册过多插件
Bootstrap()
    .with_plugin("plugin1")
    .with_plugin("plugin2")
    .with_plugin("plugin3")  # 影响启动性能
```

### 4. RuntimeContext 使用

```python
# ✅ 推荐：使用 pytest fixture
def test_example(runtime):
    http_client = runtime.http_client()

# ✅ 推荐：复用 RuntimeContext
runtime = app.run()
http_client = runtime.http_client()
database = runtime.database()

# ❌ 不推荐：重复创建 RuntimeContext
runtime1 = app.run()
runtime2 = app.run()  # 浪费资源
```

---

## 注意事项

### 1. 单例模式

- RuntimeContext 是单例，多次调用 `app.run()` 返回同一实例
- Provider 使用 SingletonProvider 确保服务单例
- 测试时使用 `force_reload=True` 清除缓存

### 2. 线程安全

- SingletonProvider 使用双重检查锁定，线程安全
- RuntimeContext 是不可变对象（frozen dataclass）
- 服务本身的线程安全由服务实现保证

### 3. 资源清理

```python
# 框架会自动清理资源
# pytest 插件会在测试结束时调用 runtime.close()

# 手动清理（非 pytest 环境）
try:
    runtime = app.run()
    # 使用 runtime
finally:
    runtime.close()
```

### 4. 配置优先级

配置加载优先级（从高到低）：
1. `profile` 参数
2. `ENV` 环境变量
3. `default.yaml` 默认配置

---

## 相关文档

- [配置系统指南](config_guide.md) - FrameworkSettings 详细说明
- [Fixtures 使用指南](fixtures_guide.md) - runtime fixture 使用
- [插件系统指南](plugins_guide.md) - 插件开发和注册
- [HTTP 客户端指南](http_client_guide.md) - HttpClient 使用
- [数据库使用指南](database_guide.md) - Database 使用

---

**完成时间**: 2026-01-17
