# 代码结构导航

> **目标读者**: 框架开发者、问题修复者、代码贡献者
> **更新日期**: 2026-01-19
> **框架版本**: v4.0.0

---

## 📋 目录

- [目录结构概览](#目录结构概览)
- [Layer 0: 核心层 (core/)](#layer-0-核心层-core)
- [Layer 1: 基础设施层 (infrastructure/)](#layer-1-基础设施层-infrastructure)
- [Layer 2: 能力层 (capabilities/)](#layer-2-能力层-capabilities)
- [Layer 3: 门面层 (testing/ + cli/)](#layer-3-门面层-testing--cli)
- [Layer 4: 引导层 (bootstrap/)](#layer-4-引导层-bootstrap)
- [横切关注点 (plugins/)](#横切关注点-plugins)
- [依赖关系图](#依赖关系图)
- [快速导航指南](#快速导航指南)

---

## 🗂️ 目录结构概览

```
src/df_test_framework/
├── core/                    # Layer 0: 核心抽象（无依赖）
│   ├── middleware/          #   中间件基类和协议
│   ├── context/             #   上下文管理
│   ├── events/              #   事件系统
│   ├── protocols/           #   协议定义
│   └── exceptions.py        #   统一异常体系
│
├── infrastructure/          # Layer 1: 基础设施
│   ├── config/              #   配置管理（Pydantic v2）
│   ├── logging/             #   结构化日志（structlog）
│   ├── telemetry/           #   OpenTelemetry 追踪
│   ├── events/              #   事件基础设施
│   └── plugins/             #   Pluggy 插件系统
│
├── capabilities/            # Layer 2: 能力层（按交互模式组织）
│   ├── clients/             #   客户端（HTTP/GraphQL/gRPC）
│   │   ├── http/            #     HTTP 客户端
│   │   │   └── rest/        #       REST 客户端
│   │   │       └── httpx/   #         基于 httpx 实现
│   │   ├── graphql/         #     GraphQL 客户端
│   │   └── grpc/            #     gRPC 客户端
│   ├── drivers/             #   驱动（UI 自动化）
│   │   └── web/             #     Web 驱动
│   │       └── playwright/  #       Playwright 实现
│   ├── databases/           #   数据库访问
│   │   ├── sql/             #     SQL 数据库（SQLAlchemy）
│   │   ├── nosql/           #     NoSQL 数据库
│   │   │   └── redis/       #       Redis 客户端
│   │   └── patterns/        #     设计模式（Repository/UoW）
│   ├── messengers/          #   消息队列
│   │   └── queue/           #     队列消息
│   │       ├── kafka/       #       Kafka 客户端
│   │       ├── rabbitmq/    #       RabbitMQ 客户端
│   │       └── rocketmq/    #       RocketMQ 客户端
│   └── storages/            #   存储客户端
│       ├── local/           #     本地文件系统
│       └── object/          #     对象存储
│           ├── s3/          #       S3 客户端
│           └── oss/         #       阿里云 OSS 客户端
│
├── testing/                 # Layer 3: 测试支持
│   ├── fixtures/            #   pytest fixtures
│   │   ├── core.py          #     核心 fixtures（runtime、http_client）
│   │   ├── allure.py        #     Allure 集成
│   │   ├── debugging.py     #     调试工具
│   │   ├── metrics.py       #     性能指标
│   │   ├── monitoring.py    #     监控集成
│   │   └── ui.py            #     UI 测试 fixtures
│   ├── decorators/          #   装饰器
│   │   ├── api_class.py     #     @api_class 装饰器
│   │   └── actions_class.py #     @actions_class 装饰器
│   ├── data/                #   测试数据
│   │   ├── builders/        #     Builder 模式
│   │   └── cleanup/         #     数据清理
│   └── debugging/           #   调试工具
│       ├── http_debugger.py #     HTTP 调试器
│       └── db_debugger.py   #     数据库调试器
│
├── cli/                     # Layer 3: 命令行工具
│   ├── commands/            #   CLI 命令
│   │   ├── init.py          #     项目初始化
│   │   └── gen.py           #     代码生成
│   └── templates/           #   项目模板
│       ├── project/         #     项目初始化模板
│       └── generators/      #     代码生成模板
│
├── bootstrap/               # Layer 4: 引导层
│   ├── bootstrap.py         #   Bootstrap 类（流式 API）
│   ├── providers.py         #   Provider 注册表
│   └── runtime.py           #   Runtime 上下文
│
├── plugins/                 # 横切关注点
│   ├── monitoring/          #   监控插件
│   └── allure/              #   Allure 插件
│
└── __init__.py              # 公共 API 导出
```

---

## 🔵 Layer 0: 核心层 (core/)

**职责**：提供框架的核心抽象和协议定义，**不依赖任何其他层**。

### 📁 core/middleware/

**职责**：中间件系统的核心抽象

```
core/middleware/
├── __init__.py
├── base.py              # BaseMiddleware 基类
├── chain.py             # MiddlewareChain 中间件链
└── protocols.py         # 中间件协议定义
```

**关键类**：
- `BaseMiddleware` - 中间件基类（洋葱模型）
- `MiddlewareChain` - 中间件链管理器
- `Request/Response` - 请求/响应抽象

**使用场景**：
- 实现自定义中间件
- 理解中间件执行顺序

### 📁 core/context/

**职责**：上下文管理（ContextVar）

```
core/context/
├── __init__.py
└── context.py           # RuntimeContext 上下文管理
```

**关键类**：
- `RuntimeContext` - 运行时上下文（基于 ContextVar）
- 用于测试隔离、事件总线隔离

### 📁 core/events/

**职责**：事件系统核心抽象

```
core/events/
├── __init__.py
├── bus.py               # EventBus 事件总线
├── event.py             # Event 事件基类
└── protocols.py         # 事件协议定义
```

**关键类**：
- `Event` - 事件基类
- `EventBus` - 事件总线（发布-订阅）
- `EventSubscriber` - 事件订阅者协议

### 📁 core/protocols/

**职责**：协议定义（Protocol）

```
core/protocols/
├── __init__.py
├── client.py            # 客户端协议
└── provider.py          # Provider 协议
```

### 📄 core/exceptions.py

**职责**：统一异常体系

**关键异常**：
- `FrameworkError` - 框架基础异常
- `ConfigurationError` - 配置错误
- `ResourceError` - 资源错误
- `ValidationError` - 验证错误
- `TimeoutError` - 超时错误

---

## 🟢 Layer 1: 基础设施层 (infrastructure/)

**职责**：提供配置、日志、遥测、插件等基础设施，**只依赖 Layer 0**。

### 📁 infrastructure/config/

**职责**：配置管理（Pydantic v2 + 环境变量）

```
infrastructure/config/
├── __init__.py
├── settings.py          # FrameworkSettings 基类
├── loader.py            # 配置加载器（YAML + 环境变量）
└── models/              # 配置模型
    ├── http.py          #   HTTPConfig
    ├── database.py      #   DatabaseConfig
    └── web.py           #   WebConfig
```

**关键类**：
- `FrameworkSettings` - 配置基类（Pydantic BaseSettings）
- `ConfigLoader` - 配置加载器（支持 YAML 分层配置）

**使用场景**：
- 添加新的配置项
- 理解配置加载顺序

### 📁 infrastructure/logging/

**职责**：结构化日志（structlog）

```
infrastructure/logging/
├── __init__.py
├── logger.py            # get_logger() 工厂函数
└── config.py            # 日志配置
```

**关键函数**：
- `get_logger(__name__)` - 获取结构化日志器
- 支持 JSON 格式、控制台格式

### 📁 infrastructure/telemetry/

**职责**：OpenTelemetry 分布式追踪

```
infrastructure/telemetry/
├── __init__.py
├── tracer.py            # Tracer 初始化
└── exporters/           # 导出器（Jaeger/Zipkin）
```

### 📁 infrastructure/events/

**职责**：事件基础设施（观察者、监听器）

```
infrastructure/events/
├── __init__.py
├── observers/           # 事件观察者
│   └── allure.py        #   AllureObserver（自动记录到 Allure）
└── listeners/           # 事件监听器
```

### 📁 infrastructure/plugins/

**职责**：Pluggy 插件系统

```
infrastructure/plugins/
├── __init__.py
├── manager.py           # PluginManager
└── hooks.py             # Hook 定义
```

**关键 Hooks**：
- `df_config_sources` - 配置源扩展
- `df_providers` - Provider 注册扩展
- `df_post_bootstrap` - Bootstrap 后处理

---

## 🟡 Layer 2: 能力层 (capabilities/)

**职责**：提供各种能力实现（HTTP、数据库、UI、消息队列、存储），**只依赖 Layer 0-1**。

**组织原则**：按交互模式组织，而非技术栈。

### 📁 capabilities/clients/http/

**职责**：HTTP 客户端（同步 + 异步）

```
capabilities/clients/http/
└── rest/
    └── httpx/
        ├── __init__.py
        ├── client.py            # HttpClient（同步）
        ├── async_client.py      # AsyncHttpClient（异步）
        ├── config.py            # HTTPConfig
        └── middleware/          # 内置中间件
            ├── retry.py         #   RetryMiddleware
            ├── timeout.py       #   TimeoutMiddleware
            ├── logging.py       #   LoggingMiddleware
            ├── signature.py     #   SignatureMiddleware
            └── bearer_token.py  #   BearerTokenMiddleware
```

**关键类**：
- `HttpClient` - 同步 HTTP 客户端（基于 httpx.Client）
- `AsyncHttpClient` - 异步 HTTP 客户端（基于 httpx.AsyncClient）
- `HTTPConfig` - HTTP 配置（超时、重试、代理等）

**中间件**：
- `RetryMiddleware` - 自动重试（指数退避）
- `TimeoutMiddleware` - 超时控制
- `LoggingMiddleware` - 请求/响应日志
- `SignatureMiddleware` - 请求签名
- `BearerTokenMiddleware` - Bearer Token 认证

### 📁 capabilities/databases/

**职责**：数据库访问（SQL + NoSQL）

```
capabilities/databases/
├── sql/
│   ├── __init__.py
│   ├── client.py            # Database 客户端（SQLAlchemy）
│   ├── async_client.py      # AsyncDatabase（异步）
│   └── config.py            # DatabaseConfig
├── nosql/
│   └── redis/
│       ├── client.py        # RedisClient
│       ├── async_client.py  # AsyncRedisClient
│       └── config.py        # RedisConfig
└── patterns/
    ├── repository.py        # Repository 模式
    └── unit_of_work.py      # UnitOfWork 模式
```

**关键类**：
- `Database` - SQL 数据库客户端（同步）
- `AsyncDatabase` - SQL 数据库客户端（异步）
- `RedisClient` - Redis 客户端（同步）
- `AsyncRedisClient` - Redis 客户端（异步）
- `Repository` - 仓储模式基类
- `UnitOfWork` - 工作单元模式

### 📁 capabilities/drivers/web/playwright/

**职责**：Web UI 自动化（Playwright）

```
capabilities/drivers/web/playwright/
├── __init__.py
├── manager.py               # BrowserManager
├── actions.py               # AppActions（同步）
├── async_actions.py         # AsyncAppActions（异步）
├── base_page.py             # BasePage（同步）
├── async_base_page.py       # AsyncBasePage（异步）
└── config.py                # WebConfig
```

**关键类**：
- `BrowserManager` - 浏览器管理器
- `AppActions` - 应用操作类（同步）
- `AsyncAppActions` - 应用操作类（异步）
- `BasePage` - 页面对象基类（同步）
- `AsyncBasePage` - 页面对象基类（异步）

### 📁 capabilities/storages/

**职责**：存储客户端（本地文件 + 对象存储）

```
capabilities/storages/
├── local/
│   ├── client.py            # LocalFileClient
│   └── config.py            # LocalFileConfig
└── object/
    ├── s3/
    │   ├── client.py        # S3Client
    │   └── config.py        # S3Config
    └── oss/
        ├── client.py        # OSSClient
        └── config.py        # OSSConfig
```

**关键类**：
- `LocalFileClient` - 本地文件系统客户端
- `S3Client` - S3 对象存储客户端（支持 MinIO）
- `OSSClient` - 阿里云 OSS 客户端

---

## 🟣 Layer 3: 门面层 (testing/ + cli/)

**职责**：提供测试支持和命令行工具，**只依赖 Layer 0-2**。

### 📁 testing/fixtures/

**职责**：pytest fixtures（自动加载）

```
testing/fixtures/
├── core.py              # 核心 fixtures（runtime、http_client）
├── allure.py            # Allure 集成
├── debugging.py         # 调试工具（console_debugger、debug_mode）
├── metrics.py           # 性能指标
├── monitoring.py        # 监控集成
└── ui.py                # UI 测试 fixtures
```

**关键 Fixtures**：
- `runtime` - RuntimeContext 实例
- `http_client` - HttpClient 实例
- `database` - Database 实例
- `redis_client` - RedisClient 实例
- `browser_manager` - BrowserManager 实例
- `console_debugger` - 控制台调试器
- `debug_mode` - 调试模式开关

### 📁 testing/decorators/

**职责**：装饰器（自动加载 API/Actions 类）

```
testing/decorators/
├── api_class.py         # @api_class 装饰器
└── actions_class.py     # @actions_class 装饰器
```

**关键装饰器**：
- `@api_class(scope="session")` - 自动加载 API 类为 fixture
- `@actions_class(scope="function")` - 自动加载 Actions 类为 fixture

### 📁 cli/commands/

**职责**：CLI 命令实现

```
cli/commands/
├── init.py              # df-test init（项目初始化）
└── gen.py               # df-test gen（代码生成）
```

**关键命令**：
- `df-test init <project-name> --type api|ui|full` - 初始化项目
- `df-test gen api <name>` - 生成 API 类
- `df-test gen page <name>` - 生成 Page 类

---

## 🔴 Layer 4: 引导层 (bootstrap/)

**职责**：框架启动和运行时管理，**可以依赖所有层**。

```
bootstrap/
├── __init__.py
├── bootstrap.py         # Bootstrap 类（流式 API）
├── providers.py         # ProviderRegistry
└── runtime.py           # RuntimeContext
```

**关键类**：
- `Bootstrap` - 框架启动类（流式 API）
- `ProviderRegistry` - Provider 注册表
- `RuntimeContext` - 运行时上下文

**使用示例**：
```python
runtime = (
    Bootstrap()
    .with_settings(DemoSettings)
    .with_provider("custom", CustomProvider())
    .build()
    .run()
)

http_client = runtime.http_client()
```

---

## ⚫ 横切关注点 (plugins/)

**职责**：跨层的功能插件

```
plugins/
├── monitoring/          # 监控插件
│   ├── __init__.py
│   └── plugin.py        # MonitoringPlugin
└── allure/              # Allure 插件
    ├── __init__.py
    └── plugin.py        # AllurePlugin
```

**关键插件**：
- `MonitoringPlugin` - 性能监控、慢查询检测
- `AllurePlugin` - Allure 报告集成

---

## 🔗 依赖关系图

### 五层架构依赖关系

```
┌─────────────────────────────────────────────────────────┐
│  Layer 4: bootstrap/                                    │
│  (可以依赖所有层)                                        │
└────────────────────┬────────────────────────────────────┘
                     │ 依赖
┌────────────────────▼────────────────────────────────────┐
│  Layer 3: testing/ + cli/                               │
│  (只依赖 Layer 0-2)                                     │
└────────────────────┬────────────────────────────────────┘
                     │ 依赖
┌────────────────────▼────────────────────────────────────┐
│  Layer 2: capabilities/                                 │
│  (只依赖 Layer 0-1)                                     │
│  - clients/  - drivers/  - databases/                   │
│  - messengers/  - storages/                             │
└────────────────────┬────────────────────────────────────┘
                     │ 依赖
┌────────────────────▼────────────────────────────────────┐
│  Layer 1: infrastructure/                               │
│  (只依赖 Layer 0)                                       │
│  - config/  - logging/  - telemetry/  - plugins/        │
└────────────────────┬────────────────────────────────────┘
                     │ 依赖
┌────────────────────▼────────────────────────────────────┐
│  Layer 0: core/                                         │
│  (无依赖 - 纯抽象)                                       │
│  - middleware/  - context/  - events/  - protocols/     │
└─────────────────────────────────────────────────────────┘

横切关注点: plugins/ (可以依赖任何层)
```

### 模块间依赖示例

```python
# ✅ 正确：Layer 2 依赖 Layer 1
# capabilities/clients/http/rest/httpx/client.py
from df_test_framework.infrastructure.logging import get_logger  # Layer 1
from df_test_framework.core.middleware import BaseMiddleware      # Layer 0

# ✅ 正确：Layer 3 依赖 Layer 2
# testing/fixtures/core.py
from df_test_framework.capabilities.clients.http import HttpClient  # Layer 2

# ❌ 错误：Layer 1 不能依赖 Layer 2
# infrastructure/config/settings.py
from df_test_framework.capabilities.clients.http import HttpClient  # 违反依赖规则！
```

---

## 🧭 快速导航指南

### 场景1：我想添加新的 HTTP 中间件

**导航路径**：
1. 查看 `core/middleware/base.py` - 理解中间件基类
2. 参考 `capabilities/clients/http/rest/httpx/middleware/` - 查看现有中间件实现
3. 创建新中间件类，继承 `BaseMiddleware`
4. 在 `HttpClient` 中注册中间件

**关键文件**：
- `src/df_test_framework/core/middleware/base.py`
- `src/df_test_framework/capabilities/clients/http/rest/httpx/middleware/retry.py`

### 场景2：我想添加新的存储客户端

**导航路径**：
1. 查看 `capabilities/storages/object/s3/` - 参考 S3 客户端实现
2. 在 `capabilities/storages/` 下创建新目录
3. 实现客户端类和配置类
4. 在 `capabilities/storages/__init__.py` 中导出

**关键文件**：
- `src/df_test_framework/capabilities/storages/object/s3/client.py`
- `src/df_test_framework/capabilities/storages/object/s3/config.py`

### 场景3：我想理解配置加载流程

**导航路径**：
1. 查看 `infrastructure/config/settings.py` - FrameworkSettings 基类
2. 查看 `infrastructure/config/loader.py` - 配置加载器
3. 查看 `bootstrap/bootstrap.py` - Bootstrap 如何加载配置

**关键文件**：
- `src/df_test_framework/infrastructure/config/settings.py`
- `src/df_test_framework/infrastructure/config/loader.py`
- `src/df_test_framework/bootstrap/bootstrap.py`

### 场景4：我想理解事件系统

**导航路径**：
1. 查看 `core/events/bus.py` - EventBus 核心实现
2. 查看 `infrastructure/events/observers/allure.py` - AllureObserver 示例
3. 查看 `capabilities/clients/http/rest/httpx/client.py` - HTTP 客户端如何发布事件

**关键文件**：
- `src/df_test_framework/core/events/bus.py`
- `src/df_test_framework/infrastructure/events/observers/allure.py`

### 场景5：我想添加新的 pytest fixture

**导航路径**：
1. 查看 `testing/fixtures/core.py` - 核心 fixtures 实现
2. 在 `testing/fixtures/` 下创建新文件或修改现有文件
3. 在 `pyproject.toml` 的 `[project.entry-points.pytest11]` 中注册

**关键文件**：
- `src/df_test_framework/testing/fixtures/core.py`
- `pyproject.toml`

### 场景6：我想理解 Bootstrap 启动流程

**导航路径**：
1. 查看 `bootstrap/bootstrap.py` - Bootstrap 类实现
2. 查看 `bootstrap/providers.py` - Provider 注册
3. 查看 `bootstrap/runtime.py` - RuntimeContext 实现

**关键文件**：
- `src/df_test_framework/bootstrap/bootstrap.py`
- `src/df_test_framework/bootstrap/providers.py`
- `src/df_test_framework/bootstrap/runtime.py`

---

## 📚 相关文档

- [架构设计](ARCHITECTURE_V4.0.md) - 五层架构详细设计
- [贡献者指南](../CONTRIBUTOR_GUIDE.md) - 如何为框架贡献代码
- [中间件指南](../guides/middleware_guide.md) - 中间件系统详解
- [事件总线指南](../guides/event_bus_guide.md) - 事件系统详解

---

**最后更新**: 2026-01-19

