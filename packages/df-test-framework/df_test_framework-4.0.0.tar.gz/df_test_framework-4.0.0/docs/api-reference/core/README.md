# Core 核心层 API 参考

> **最后更新**: 2026-01-17
> **适用版本**: v3.0.0+

## 概述

Core 层是 DF Test Framework 的**核心抽象层**（Layer 0），提供框架的基础协议、类型定义和核心机制。

### 设计原则

- **零依赖**: Core 层不依赖任何其他层，是框架的最底层
- **纯抽象**: 只定义协议和接口，不包含具体实现
- **高内聚**: 每个模块职责单一，边界清晰
- **可扩展**: 通过协议和抽象类支持扩展

### 架构位置

```
Layer 4 ─── bootstrap/          # 引导层
Layer 3 ─── testing/ + cli/     # 门面层
Layer 2 ─── capabilities/       # 能力层
Layer 1 ─── infrastructure/     # 基础设施
Layer 0 ─── core/               # 核心层 ← 本文档
```

---

## 核心模块

### 协议定义 (protocols/)

定义框架的核心协议和接口。

- **HttpClientProtocol** - HTTP 客户端协议
- **DatabaseProtocol** - 数据库协议
- **CacheProtocol** - 缓存协议
- **StorageProtocol** - 存储协议

📖 [协议定义 API 参考](protocols.md)

### 中间件系统 (middleware/)

定义中间件的抽象基类和执行机制。

- **BaseMiddleware** - 中间件基类
- **MiddlewareChain** - 中间件链
- **MiddlewareContext** - 中间件上下文

📖 [中间件系统 API 参考](middleware.md)

### 上下文系统 (context/)

定义请求上下文和上下文管理器。

- **RequestContext** - 请求上下文
- **ContextManager** - 上下文管理器
- **ContextVar** - 上下文变量

📖 [上下文系统 API 参考](context.md)

### 事件系统 (events/)

定义事件类型和事件总线协议。

- **Event** - 事件基类
- **EventBusProtocol** - 事件总线协议
- **事件类型定义** - 框架内置事件

📖 [事件类型 API 参考](events.md)

### 异常体系 (exceptions.py)

定义框架的异常层次结构。

- **FrameworkError** - 框架基础异常
- **ConfigurationError** - 配置错误
- **ValidationError** - 验证错误
- **其他异常类型**

📖 [异常体系 API 参考](exceptions.md)

### 类型定义 (types.py)

定义框架使用的类型别名和类型协议。

- **类型别名** - 常用类型的别名
- **类型协议** - 类型检查协议
- **泛型类型** - 泛型定义

📖 [类型定义 API 参考](types.md)

---

## 使用指南

### 导入核心模块

```python
# 导入协议
from df_test_framework.core.protocols import HttpClientProtocol, DatabaseProtocol

# 导入中间件
from df_test_framework.core.middleware import BaseMiddleware

# 导入事件
from df_test_framework.core.events import Event

# 导入异常
from df_test_framework.core.exceptions import FrameworkError

# 导入类型
from df_test_framework.core.types import JSONType, HeadersType
```

### 实现自定义协议

```python
from df_test_framework.core.protocols import HttpClientProtocol

class MyHttpClient(HttpClientProtocol):
    """自定义 HTTP 客户端实现"""

    def request(self, method: str, url: str, **kwargs) -> Response:
        # 实现具体逻辑
        pass
```

### 创建自定义中间件

```python
from df_test_framework.core.middleware import BaseMiddleware

class MyMiddleware(BaseMiddleware):
    """自定义中间件"""

    def process(self, context, next_middleware):
        # 前置处理
        print("Before request")

        # 调用下一个中间件
        response = next_middleware(context)

        # 后置处理
        print("After request")
        return response
```

---

## 依赖关系

### Core 层依赖

```
core/
├── 无外部依赖（纯抽象）
└── 仅依赖 Python 标准库
```

### 被依赖关系

```
Layer 4 (bootstrap) ──┐
Layer 3 (testing)    ─┤
Layer 2 (capabilities)├─→ Layer 0 (core)
Layer 1 (infrastructure)┘
```

所有其他层都可以依赖 Core 层，但 Core 层不依赖任何其他层。

---

## 相关文档

### 使用指南
- [中间件使用指南](../../guides/middleware_guide.md) - 中间件系统使用
- [EventBus 使用指南](../../guides/event_bus_guide.md) - 事件系统使用
- [Bootstrap 引导系统指南](../../guides/bootstrap_guide.md) - 框架初始化

### 架构文档
- [五层架构详解](../../architecture/五层架构详解.md) - 架构层次说明
- [ARCHITECTURE_V4.0.md](../../architecture/ARCHITECTURE_V4.0.md) - v4.0 架构总览

---

**完成时间**: 2026-01-17

