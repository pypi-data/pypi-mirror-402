# 插件系统使用指南

> **最后更新**: 2026-01-17
> **适用版本**: v3.37.0+（插件系统重构）

## 概述

DF Test Framework 提供了强大的插件系统，允许你扩展框架功能而无需修改核心代码。

### 核心特性

- **基于 Pluggy**: 使用 pytest 的插件系统 Pluggy 实现
- **Hook 机制**: 通过 Hook 点扩展框架行为
- **事件驱动**: 插件可以订阅 EventBus 事件
- **生命周期管理**: 自动管理插件的初始化和清理
- **内置插件**: 提供 MonitoringPlugin 和 AllurePlugin

### 插件类型

| 类型 | 说明 | 示例 |
|------|------|------|
| **监控插件** | 收集性能指标和统计信息 | MonitoringPlugin |
| **报告插件** | 生成测试报告 | AllurePlugin（已废弃，推荐 Fixture 方式） |
| **扩展插件** | 添加新功能或修改现有行为 | 自定义插件 |

---

## 快速开始

### 使用内置插件

```python
from df_test_framework import Bootstrap
from df_test_framework.plugins.builtin.monitoring import MonitoringPlugin

# 创建插件实例
monitoring = MonitoringPlugin()

# 注册插件
app = Bootstrap().with_plugin(monitoring).build()
runtime = app.run()

# 使用框架
http_client = runtime.http_client()
http_client.get("/users")

# 查看监控数据
print(f"API 调用次数: {len(monitoring.api_calls)}")
```

### 在 pytest 中使用

```python
# conftest.py
import pytest
from df_test_framework.plugins.builtin.monitoring import MonitoringPlugin

@pytest.fixture(scope="session")
def monitoring_plugin():
    return MonitoringPlugin()

def pytest_configure(config):
    monitoring = MonitoringPlugin()
    config._df_monitoring = monitoring
```

---

## 插件系统架构

### 核心组件

```
PluginManager (Pluggy)
├── Hook Specifications (定义扩展点)
├── Hook Implementations (插件实现)
└── Plugin Registry (插件注册表)
```

### Hook 点

框架提供以下 Hook 点供插件扩展：

| Hook 点 | 触发时机 | 用途 |
|---------|---------|------|
| `pytest_configure` | pytest 配置阶段 | 初始化插件 |
| `pytest_unconfigure` | pytest 结束阶段 | 清理插件资源 |
| `pytest_runtest_setup` | 测试开始前 | 测试前置操作 |
| `pytest_runtest_teardown` | 测试结束后 | 测试后置操作 |

---

## 内置插件

### MonitoringPlugin

监控插件用于收集测试执行过程中的性能指标。

**功能**：
- 自动记录 HTTP 请求（方法、URL、状态码、耗时）
- 自动记录数据库查询（SQL、耗时、行数）
- 提供统计摘要（总数、总耗时、平均耗时）

**使用方法**：

```python
from df_test_framework.plugins.builtin.monitoring import MonitoringPlugin

# 创建插件
monitoring = MonitoringPlugin()

# 注册插件
app = Bootstrap().with_plugin(monitoring).build()
runtime = app.run()

# 执行测试
http_client = runtime.http_client()
http_client.get("/users")
http_client.post("/users", json={"name": "张三"})

# 查看监控数据
api_calls = monitoring.api_calls
print(f"总请求数: {len(api_calls)}")

# 获取统计摘要
summary = monitoring.get_summary()
print(f"平均耗时: {summary['api_calls']['avg_duration']:.3f}s")
```

**详细文档**: [监控插件指南](monitoring_plugin.md)

---

### AllurePlugin（已废弃）

> **重要**: AllurePlugin 已在 v3.18.0 标记为废弃，将在 v4.0.0 移除。
>
> **推荐**: 使用 Fixture 集成方式，自动生效，无需手动注册。

**迁移指南**: [Allure 插件指南](allure_plugin.md)

---

## 自定义插件开发

### 创建插件类

自定义插件需要实现特定的接口或订阅 EventBus 事件。

**基于 EventBus 的插件**（推荐）：

```python
from df_test_framework.core.events import Event

class CustomPlugin:
    """自定义插件示例"""

    def __init__(self):
        self.data = []

    def on_http_request_end(self, event: Event):
        """处理 HTTP 请求结束事件"""
        self.data.append({
            "method": event.data.get("method"),
            "url": event.data.get("url"),
            "status_code": event.data.get("status_code")
        })

    def get_summary(self):
        """获取统计摘要"""
        return {
            "total_requests": len(self.data),
            "success_count": len([d for d in self.data if d["status_code"] < 400])
        }
```

**基于 Hook 的插件**：

```python
import pytest

class CustomHookPlugin:
    """基于 Hook 的插件"""

    @pytest.hookimpl
    def pytest_configure(self, config):
        """pytest 配置阶段"""
        print("插件初始化")

    @pytest.hookimpl
    def pytest_runtest_setup(self, item):
        """测试开始前"""
        print(f"开始测试: {item.name}")

    @pytest.hookimpl
    def pytest_runtest_teardown(self, item):
        """测试结束后"""
        print(f"结束测试: {item.name}")
```

### 注册插件

**方式 1：通过 Bootstrap 注册**

```python
from df_test_framework import Bootstrap

# 创建插件实例
custom_plugin = CustomPlugin()

# 注册插件
app = Bootstrap().with_plugin(custom_plugin).build()
runtime = app.run()

# 订阅事件
runtime.event_bus.subscribe("http.request.end", custom_plugin.on_http_request_end)
```

**方式 2：通过 pytest 注册**

```python
# conftest.py
import pytest

def pytest_configure(config):
    """注册插件到 pytest"""
    plugin = CustomHookPlugin()
    config.pluginmanager.register(plugin, "custom_plugin")
```

### 插件生命周期

```python
class LifecyclePlugin:
    """完整生命周期示例"""

    def __init__(self):
        """初始化阶段"""
        self.initialized = False

    def setup(self, runtime):
        """设置阶段 - 订阅事件"""
        runtime.event_bus.subscribe("http.request.end", self.on_request)
        self.initialized = True

    def on_request(self, event):
        """事件处理"""
        pass

    def teardown(self):
        """清理阶段"""
        self.initialized = False
```

---

## 最佳实践

### 1. 使用 EventBus 而非 Hook

```python
# ✅ 推荐：使用 EventBus
class GoodPlugin:
    def __init__(self):
        self.data = []

    def on_event(self, event):
        self.data.append(event.data)

# ❌ 不推荐：使用 Hook（除非必要）
class BadPlugin:
    @pytest.hookimpl
    def pytest_runtest_protocol(self, item):
        # Hook 实现复杂，难以维护
        pass
```

### 2. 插件职责单一

```python
# ✅ 推荐：单一职责
class MetricsPlugin:
    """只负责收集指标"""
    def collect_metric(self, event):
        pass

class ReportPlugin:
    """只负责生成报告"""
    def generate_report(self, data):
        pass

# ❌ 不推荐：职责混杂
class MegaPlugin:
    """既收集指标又生成报告还发送通知"""
    pass
```

### 3. 避免阻塞操作

```python
# ✅ 推荐：异步处理
class AsyncPlugin:
    async def on_event(self, event):
        await self.save_to_database(event.data)

# ❌ 不推荐：同步阻塞
class BlockingPlugin:
    def on_event(self, event):
        time.sleep(5)  # 阻塞测试执行
```

### 4. 提供清理方法

```python
# ✅ 推荐：提供清理方法
class CleanPlugin:
    def __init__(self):
        self.resources = []

    def cleanup(self):
        for resource in self.resources:
            resource.close()

# 在 pytest 中自动清理
@pytest.fixture(scope="session")
def clean_plugin():
    plugin = CleanPlugin()
    yield plugin
    plugin.cleanup()
```

---

## 注意事项

### 1. 线程安全

插件可能在多线程环境中运行，注意线程安全：

```python
import threading

class ThreadSafePlugin:
    def __init__(self):
        self.data = []
        self.lock = threading.Lock()

    def on_event(self, event):
        with self.lock:
            self.data.append(event.data)
```

### 2. 性能影响

插件会影响测试性能，避免耗时操作：

```python
# ✅ 推荐：轻量级操作
def on_event(self, event):
    self.counter += 1

# ❌ 不推荐：耗时操作
def on_event(self, event):
    self.save_to_database(event.data)  # 同步数据库操作
```

### 3. 事件订阅清理

确保在插件清理时取消事件订阅：

```python
class ProperPlugin:
    def setup(self, runtime):
        self.event_bus = runtime.event_bus
        self.event_bus.subscribe("http.request.end", self.on_request)

    def teardown(self):
        # 取消订阅
        self.event_bus.unsubscribe("http.request.end", self.on_request)
```

---

## 相关文档

- [Bootstrap 引导系统指南](bootstrap_guide.md) - 插件注册方法
- [EventBus 使用指南](event_bus_guide.md) - 事件系统详解
- [监控插件指南](monitoring_plugin.md) - MonitoringPlugin 使用
- [Allure 插件指南](allure_plugin.md) - Allure 集成方式

---

**完成时间**: 2026-01-17
