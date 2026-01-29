# 架构设计文档

深入了解 DF Test Framework 架构设计和实现原理。

> **最后更新**: 2026-01-16
> **适用版本**: v4.0.0+

## 📚 核心架构文档

### 主要文档 ⭐

1. **[v4.0 架构总览](ARCHITECTURE_V4.0.md)** ⭐⭐⭐ - 框架整体架构视图
   - 五层架构 + 事件驱动 + 依赖注入
   - v4.0.0 重大变更（全面异步化）
   - 数据流图（HTTP/UI）
   - 性能对比（30x 提升）
   - 架构优势与设计原则

2. **[五层架构详解](五层架构详解.md)** ⭐⭐⭐ - 各层详细说明与最佳实践
   - Layer 0: Core（协议、中间件、事件）
   - Layer 1: Infrastructure（配置、日志、EventBus）
   - Layer 2: Capabilities（HTTP/UI/DB 客户端）
   - Layer 3: Testing + CLI（Fixtures、装饰器、CLI）
   - Layer 4: Bootstrap（引导层、依赖注入）
   - 横切关注点: Plugins（监控、报告）
   - 代码示例与扩展指南

### 专题文档

**配置与依赖注入**:
- **[配置驱动架构设计](config-driven-design.md)** ⭐⭐⭐⭐ - 配置驱动模式全面解析
- **[Provider 模式深度剖析](provider-pattern-deep-dive.md)** ⭐⭐⭐⭐⭐ - 依赖注入实现技术深度解析
- **[依赖管理策略](DI_STRATEGY.md)** - 混合 DI 模式（Provider/Settings/Fixtures）

**可观测性与事件**:
- **[可观测性架构](observability-architecture.md)** - Logging/Tracing/Metrics + EventBus
- **[EventBus 集成分析](eventbus-integration-analysis.md)** - 模块集成状态与路线图
- **[测试执行生命周期](TEST_EXECUTION_LIFECYCLE.md)** - 从初始化到报告生成

**系统设计对比**:
- **[HTTP vs Web 架构对比](http-vs-web-comparison.md)** ⭐⭐⭐ - 客户端与驱动的架构差异
- **[中间件系统设计](MIDDLEWARE_V3.14_DESIGN.md)** - 洋葱模型实现（v3.14+）

**插件与扩展**:
- **[插件系统架构](PLUGIN_SYSTEM_V3.37.md)** - pytest 插件现代化实现

---

## 📂 历史版本与归档

### 当前保留的历史文档
- **[架构总览 v3.17](OVERVIEW_V3.17.md)** - v3.17 版本架构总览（v4.0 前最后版本）
- **[V3 架构设计](V3_ARCHITECTURE.md)** - v3.0 核心架构方案
- **[V3 实施指南](V3_IMPLEMENTATION.md)** - v3.0 实施步骤
- **[架构审计报告](ARCHITECTURE_AUDIT.md)** - 文档与代码一致性审计
- **[未来增强功能](FUTURE_ENHANCEMENTS.md)** - 后续增强规划

### 归档文档
- **[归档索引](../archive/README.md)** - 查看所有已归档的历史文档
- **[架构历史版本](../archive/versions/)** - 各版本架构演进文档
- **[设计方案归档](../archive/design/)** - 历史设计方案和评审文档

## 🏗️ 快速参考

### 五层架构（v4.0+）

详细说明请参考 **[v4.0 架构总览](ARCHITECTURE_V4.0.md)** 和 **[五层架构详解](五层架构详解.md)**。

```
Layer 4 ─── bootstrap/          # 引导层：Bootstrap、Providers、Runtime
Layer 3 ─── testing/ + cli/     # 门面层：Fixtures、CLI 工具、脚手架
Layer 2 ─── capabilities/       # 能力层：HTTP/UI/DB/MQ/Storage
Layer 1 ─── infrastructure/     # 基础设施：config/logging/events/plugins
Layer 0 ─── core/               # 核心层：纯抽象（无依赖）
横切 ───── plugins/             # 插件：MonitoringPlugin、AllurePlugin
```

**依赖规则**: 高层可依赖低层，反之不行。Layer 0 无任何第三方依赖。

### 核心设计模式

| 模式 | 用途 | 文档 |
|------|------|------|
| **Middleware** | 洋葱模型请求处理链 | [中间件系统设计](MIDDLEWARE_V3.14_DESIGN.md) |
| **EventBus** | 发布/订阅，模块解耦 | [可观测性架构](observability-architecture.md) |
| **Provider** | 依赖注入 | [Provider 模式深度剖析](provider-pattern-deep-dive.md) |
| **Repository** | 数据访问抽象 | [五层架构详解](五层架构详解.md#layer-2-capabilities) |
| **Factory** | 测试数据生成 | [五层架构详解](五层架构详解.md#layer-3-testing) |
| **Plugin** | 功能扩展（Pluggy） | [插件系统架构](PLUGIN_SYSTEM_V3.37.md) |

### v4.0.0 重大变更

- ✅ **全面异步化**：AsyncHttpClient、AsyncDatabase、AsyncRedis、AsyncAppActions
- ✅ **性能飞跃**：并发性能提升 2-30 倍
- ✅ **向后兼容**：同步 API 完全保留
- ✅ **更好的资源管理**：async with 上下文管理器

详见 **[v4.0 架构总览](ARCHITECTURE_V4.0.md)**。

### 技术栈

- **httpx**: 异步 HTTP 客户端（支持 HTTP/2）
- **playwright**: UI 自动化（异步 API）
- **sqlalchemy 2.0**: AsyncEngine 数据库访问
- **pydantic v2**: 数据验证和配置
- **structlog**: 结构化日志
- **opentelemetry**: 分布式追踪
- **pluggy**: 插件系统
- **pytest**: 测试框架

## 🔗 相关资源

- **[用户指南](../guides/)** - 功能使用手册（HTTP、Database、UI、中间件等）
- **[API 参考](../api-reference/README.md)** - 各层级模块 API 文档
- **[发布说明](../releases/)** - 各版本变更说明
- **[迁移指南](../migration/)** - 版本升级指南

---

**返回**: [文档首页](../README.md)
