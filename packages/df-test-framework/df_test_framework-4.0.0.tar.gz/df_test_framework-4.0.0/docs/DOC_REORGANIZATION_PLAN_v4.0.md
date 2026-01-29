# DF Test Framework v4.0 文档整理和更新计划

> **制定时间**: 2026-01-16
> **目标版本**: v4.0.0
> **文档总数**: 308 个 .md 文件
> **整理目标**: 保持实时更新的核心文档，归档历史文档，建立清晰的文档体系

---

## 📋 整理原则

### 1. 文档分类原则
- **核心文档**：保持实时更新，反映最新架构和功能
- **指南文档**：详细的使用手册，按模块组织
- **历史文档**：归档到 `archive/` 目录，保留追溯能力
- **临时文档**：设计方案、分析报告等，完成后归档

### 2. 更新原则
- **版本管理合理化**：仅核心文档标注框架版本，指南文档使用"最后更新时间"+"适用版本"
- **架构一致性**：确保文档反映真实的五层架构
- **从底层到顶层**：按照 Layer 0 → Layer 4 → 横切关注点的顺序更新
- **详略得当**：全局文档简洁明了，模块文档详细深入
- **避免过度维护**：不同文档采用不同的版本标注策略，降低后续维护成本

### 3. 归档原则
- 历史版本的架构文档（v2、v3.x）归档
- 已完成的设计方案和分析报告归档
- 临时文档和讨论记录归档
- 过时的迁移指南保留最近 2-3 个版本

### 4. 文档版本管理策略

**核心原则**：避免所有文档都跟随框架版本更新，造成维护负担

| 文档类型 | 版本标注策略 | 更新时机 | 数量 | 示例 |
|---------|------------|---------|------|------|
| **核心文档** | 框架版本号 | 大版本发布 | ~5 个 | README.md: v4.0.0 |
| **使用指南** | 最后更新时间 + 适用版本范围 | 内容变化时 | ~30 个 | 最后更新: 2026-01-16<br>适用版本: v3.8.0+ |
| **API 参考** | 功能引入版本 + 变更历史 | 功能变化时 | ~20 个 | 引入: v3.8.0<br>优化: v4.0.0 |
| **发布说明** | 版本号（文件名） | 每次发布 | 累积 | v4.0.0.md |
| **归档文档** | 历史版本号 + 归档状态 | 归档后不再更新 | 归档 | v3.17（已归档） |

**文档头部模板**：

```markdown
# 模板 1: 核心文档（README.md, CLAUDE.md 等）
# DF Test Framework

> **版本**: v4.0.0
> **更新时间**: 2026-01-16

---

# 模板 2: 使用指南（guides/ 目录）
# HTTP 客户端使用指南

> **最后更新**: 2026-01-16
> **适用版本**: v3.8.0+（同步模式），v4.0.0+（推荐异步）

---

# 模板 3: API 参考（api-reference/ 目录）
## AsyncHttpClient

> **引入版本**: v3.8.0
> **稳定版本**: v3.10.0
> **重大改进**: v4.0.0（性能提升 30 倍）

### 版本历史
- v4.0.0: 连接池优化，性能提升 30 倍
- v3.10.0: 稳定版本
- v3.8.0: 首次引入

---

# 模板 4: 归档文档（archive/ 目录）
# v3.17 事件系统架构设计

> **版本**: v3.17.0
> **创建时间**: 2025-12-05
> **状态**: ⚠️ 已归档
> **当前文档**: 请参考 [ARCHITECTURE_V4.0.md](../ARCHITECTURE_V4.0.md)
```

**后续版本更新时的文档维护成本**：

| 更新类型 | 需要更新的文档数量 | 工作量 |
|---------|------------------|--------|
| 小版本更新（v4.0.1） | 1-2 个（仅发布说明） | 5 分钟 |
| 次版本更新（v4.1.0） | 5-15 个（核心文档 + 新功能指南） | 30 分钟 |
| 大版本更新（v5.0.0） | 20-50 个（核心文档 + 架构 + 受影响指南） | 2-3 小时 |

---

## 🎯 整理计划概览

### 阶段 1：清理和归档（预计 2 小时）
1. 归档顶级临时文档
2. 整理架构文档目录
3. 清理重复和过时文档
4. 建立归档索引

### 阶段 2：更新核心文档（预计 1 小时）
1. 更新项目 README.md
2. 更新 CLAUDE.md
3. 更新 ESSENTIAL_DOCS.md
4. 更新 docs/README.md

### 阶段 3：更新架构文档（预计 2 小时）
1. 创建/更新 v4.0.0 架构总览
2. 归档历史版本架构文档
3. 更新特定模式/机制的架构文档

### 阶段 4：按分层更新模块文档（预计 6 小时）
1. Layer 0 (core) - 核心抽象
2. Layer 1 (infrastructure) - 基础设施
3. Layer 2 (capabilities) - 能力层
4. Layer 3 (testing + cli) - 门面层
5. Layer 4 (bootstrap) - 引导层
6. 横切关注点 (plugins) - 插件系统

### 阶段 5：更新开发者文档（预计 1 小时）
1. 贡献指南
2. 开发流程
3. 测试规范

---

## 📂 详细整理计划

### 阶段 1：清理和归档

#### 1.1 归档顶级临时文档
**位置**: `docs/` 根目录
**需要归档的文件**:
- `web-架构一致性设计方案.md` → `docs/archive/design/web-architecture-consistency-design.md`
- `web-事件驱动方案对比.md` → `docs/archive/design/web-event-driven-comparison.md`
- `方案B实施评估报告.md` → `docs/archive/reports/solution-b-evaluation.md`
- `ui-best-practices-2026.md` → 合并到 `docs/guides/web-ui-testing.md` 或归档

**操作**:
```bash
# 创建归档目录
mkdir -p docs/archive/design
mkdir -p docs/archive/reports

# 移动文件
mv docs/web-*.md docs/archive/design/
mv docs/方案B*.md docs/archive/reports/
```

#### 1.2 整理架构文档目录
**位置**: `docs/architecture/`
**当前状态**: 43 个文件，包含大量历史版本

**整理策略**:

1. **保留的核心架构文档**（实时更新）:
   - `README.md` - 架构文档导航
   - `ARCHITECTURE_V4.0.md` - **新建** v4.0 架构总览（全局，简洁）
   - `五层架构详解.md` - **新建** 五层架构详细说明

2. **保留的专题架构文档**（按需更新）:
   - `observability-architecture.md` - 可观测性架构
   - `MIDDLEWARE_V3.14_DESIGN.md` - 中间件系统设计
   - `PLUGIN_SYSTEM_V3.37.md` - 插件系统
   - `TEST_EXECUTION_LIFECYCLE.md` - 测试执行生命周期
   - `extension-points.md` - 扩展点
   - `multi-project-reuse.md` - 多项目复用
   - `test-type-support.md` - 测试类型支持

3. **归档的历史文档**:
   - `FRAMEWORK_ARCHITECTURE_v3.6.2.md` → `archive/`
   - `OVERVIEW_V3.17.md` → `archive/`
   - `v2-architecture.md` → `archive/`
   - `V3_ARCHITECTURE.md` → `archive/`
   - `V3_IMPLEMENTATION.md` → `archive/`
   - `V3.14_ENTERPRISE_PLATFORM_DESIGN.md` → `archive/`
   - `V3.16_LAYER4_BOOTSTRAP_ARCHITECTURE.md` → `archive/`
   - `V3.17_EVENT_SYSTEM_REDESIGN.md` → `archive/`

4. **归档的设计文档**（已完成的设计方案）:
   - `allure_integration_modes.md` → `archive/design/`
   - `capability_plan_vs_current.md` → `archive/design/`
   - `config-driven-design.md` → `archive/design/`
   - `config-management-analysis.md` → `archive/design/`
   - `DI_STRATEGY.md` → `archive/design/`
   - `eventbus-integration-analysis.md` → `archive/design/`
   - `failure-diagnosis-v2-design.md` → `archive/design/`
   - `future_allure_plugin_plans.md` → `archive/design/`
   - `http-vs-web-comparison.md` → `archive/design/`
   - `observability-debugging-unification.md` → `archive/design/`
   - `PREPARE_DATA_DESIGN.md` → `archive/design/`
   - `provider-pattern-deep-dive.md` → `archive/design/`
   - `tech-debt-cleanup-plan.md` → `archive/design/`
   - `ui-failure-diagnosis-implementation-v3.46.3.md` → `archive/design/`
   - `ui-observability-design.md` → `archive/design/`
   - `UOW_CLEANUP_ARCHITECTURE.md` → `archive/design/`
   - `UOW_REFACTORING_PROPOSAL.md` → `archive/design/`

**最终架构文档目录结构**:
```
docs/architecture/
├── README.md                           # 架构文档导航
├── ARCHITECTURE_V4.0.md                # v4.0 架构总览（新建）
├── 五层架构详解.md                      # 五层架构详细说明（新建）
├── observability-architecture.md       # 可观测性架构
├── MIDDLEWARE_V3.14_DESIGN.md          # 中间件系统
├── PLUGIN_SYSTEM_V3.37.md              # 插件系统
├── TEST_EXECUTION_LIFECYCLE.md         # 测试执行生命周期
├── extension-points.md                 # 扩展点
├── multi-project-reuse.md              # 多项目复用
├── test-type-support.md                # 测试类型支持
├── FUTURE_ENHANCEMENTS.md              # 未来增强
├── ROADMAP_V3.29_ENHANCEMENTS.md       # 功能增强路线图
├── ARCHITECTURE_AUDIT.md               # 架构审计（保留用于验证）
└── archive/                            # 历史和设计文档归档
    ├── v2-architecture.md
    ├── v3.6.2/
    ├── v3.17/
    ├── design/                         # 已完成的设计方案
    └── README.md                       # 归档索引
```

#### 1.3 清理其他目录

**docs/analysis/**:
- 全部归档到 `docs/archive/analysis/`
- 这些是历史分析报告，已经完成

**docs/plans/**:
- 全部归档到 `docs/archive/plans/`
- 这些是历史计划文档

**docs/design/**:
- 全部归档到 `docs/archive/design/`
- 这些是设计讨论文档

**docs/auth/**:
- 检查内容，决定是归档还是合并到指南

**docs/performance/**:
- `async_vs_sync.md` 保留或合并到 `docs/guides/async_api_guide.md`

---

### 阶段 2：更新核心文档

> **说明**：核心文档采用"框架版本号 + 更新时间"策略，这些是仅有的需要标注框架版本的文档

#### 2.1 更新项目 README.md
**文件**: `README.md`
**版本策略**: ✅ 核心文档 - 标注框架版本 v4.0.0

**更新内容**:
```markdown
# DF Test Framework

> **版本**: v4.0.0
> **更新时间**: 2026-01-16
```

**任务清单**:
- [ ] 版本号更新到 v4.0.0
- [ ] 更新时间为 2026-01-16
- [ ] 更新"当前版本亮点"部分，突出 v4.0.0 异步化特性
- [ ] 更新架构概览，确保反映五层架构
- [ ] 检查所有链接，确保指向正确的文档
- [ ] 更新依赖安装说明（database-async 等）
- [ ] 简化内容，重点突出快速开始

#### 2.2 更新 CLAUDE.md
**文件**: `CLAUDE.md`
**版本策略**: ✅ 核心文档 - 标注框架版本 v4.0.0

**更新内容**:
```markdown
# CLAUDE.md

## 项目概述

**DF Test Framework** - 现代化 Python 测试自动化框架

- **版本**: v4.0.0
- **更新时间**: 2026-01-16
- **Python**: 3.12+
```

**任务清单**:
- [ ] 版本号从 3.45.0 更新到 4.0.0
- [ ] 更新时间为 2026-01-16
- [ ] 添加 v4.0.0 异步化说明
- [ ] 更新核心模式部分，补充异步 API（AsyncHttpClient、AsyncDatabase 等）
- [ ] 确保目录结构准确

#### 2.3 更新 ESSENTIAL_DOCS.md
**文件**: `docs/ESSENTIAL_DOCS.md`
**版本策略**: ✅ 核心文档 - 标注框架版本 v4.0.0

**更新内容**:
```markdown
# 核心文档导航 - 真正有价值的文档清单

> **目标读者**: 测试开发人员、框架使用者、新团队成员
> **更新日期**: 2026-01-16
> **框架版本**: v4.0.0
```

**任务清单**:
- [ ] 框架版本更新到 v4.0.0
- [ ] 更新日期为 2026-01-16
- [ ] 更新必读文档列表，添加异步相关指南
- [ ] 检查所有链接
- [ ] 更新文档价值评估表

#### 2.4 更新 docs/README.md
**文件**: `docs/README.md`
**版本策略**: ✅ 核心文档 - 标注框架版本 v4.0.0

**更新内容**:
```markdown
# DF Test Framework 文档中心

> 版本：v4.0.0 · 最近更新：2026-01-16
```

**任务清单**:
- [ ] 版本号更新到 v4.0.0
- [ ] 更新时间为 2026-01-16
- [ ] 添加 v4.0.0 新特性导航
- [ ] 更新文档结构索引
- [ ] 移除归档文档的链接（指向归档索引即可）

---

### 阶段 3：更新架构文档

#### 3.1 创建 v4.0.0 架构总览
**新建文件**: `docs/architecture/ARCHITECTURE_V4.0.md`
**内容结构**:
```markdown
# DF Test Framework v4.0 架构总览

## 版本信息
- 版本：v4.0.0
- 更新日期：2026-01-16
- 重大变更：全面异步化

## 核心架构

### 五层架构
- Layer 0: core - 纯抽象
- Layer 1: infrastructure - 基础设施
- Layer 2: capabilities - 能力层
- Layer 3: testing + cli - 门面层
- Layer 4: bootstrap - 引导层
- 横切：plugins - 插件系统

### 依赖规则
- 高层可依赖低层
- 反之不行
- Layer 0 无任何依赖

## v4.0.0 重大变更

### 全面异步化
- AsyncHttpClient
- AsyncDatabase
- AsyncRedis
- AsyncAppActions + AsyncBasePage

### 向后兼容
- 同步 API 完全保留
- 升级路径平滑

## 架构图
[插入架构图]

## 详细说明
参见各模块文档...
```

#### 3.2 创建五层架构详解
**新建文件**: `docs/architecture/五层架构详解.md`
**内容**：详细说明每一层的职责、包含的模块、依赖关系等

#### 3.3 更新专题架构文档
- `observability-architecture.md` - 检查是否需要更新
- `MIDDLEWARE_V3.14_DESIGN.md` - 检查是否需要补充异步中间件
- 其他文档根据需要更新

#### 3.4 创建架构文档导航
**更新文件**: `docs/architecture/README.md`
**内容**：清晰的架构文档导航，指向核心文档和归档

---

### 阶段 4：按分层更新模块文档

> **说明**：模块文档采用"最后更新时间 + 适用版本范围"策略，不跟随框架版本更新

**文档头部模板**（所有指南和 API 参考文档统一使用）:
```markdown
# HTTP 客户端使用指南

> **最后更新**: 2026-01-16
> **适用版本**: v3.8.0+（同步模式），v4.0.0+（推荐异步）

## AsyncHttpClient（推荐）

> **引入版本**: v3.8.0
> **稳定版本**: v3.10.0
> **重大改进**: v4.0.0（性能提升 30 倍）

...
```

#### 4.1 Layer 0: Core 核心层
**目标**: 创建/更新核心抽象的 API 参考文档
**版本策略**: 📘 API 参考 - 标注"引入版本 + 变更历史"

**需要创建的文档**:
- `docs/api-reference/core/README.md` - 核心层概览
- `docs/api-reference/core/protocols.md` - 协议定义
- `docs/api-reference/core/middleware.md` - 中间件系统
- `docs/api-reference/core/context.md` - 上下文系统
- `docs/api-reference/core/events.md` - 事件类型
- `docs/api-reference/core/exceptions.md` - 异常体系
- `docs/api-reference/core/types.md` - 类型定义

**文档头部示例**:
```markdown
## BaseMiddleware

> **引入版本**: v3.14.0
> **稳定版本**: v3.16.0

### 版本历史
- v3.16.0: 移除 Interceptor，统一为 Middleware
- v3.14.0: 首次引入中间件系统
```

**内容要点**:
- 每个模块的职责
- 主要类和接口
- 使用示例
- 注意事项

#### 4.2 Layer 1: Infrastructure 基础设施层
**目标**: 创建/更新基础设施的使用指南
**版本策略**: 📖 使用指南 - 标注"最后更新时间 + 适用版本范围"

**需要创建/更新的文档**:
- `docs/guides/config_guide.md` - 配置系统完整指南（更新现有的 env_config_guide.md）
  ```markdown
  > **最后更新**: 2026-01-16
  > **适用版本**: v3.35.0+（YAML 分层配置）
  ```
- `docs/guides/logging_guide.md` - 日志系统完整指南（整合现有的多个日志文档）
  ```markdown
  > **最后更新**: 2026-01-16
  > **适用版本**: v3.38.0+（structlog 集成）
  ```
- `docs/guides/event_bus_guide.md` - EventBus 完整指南（已存在，需要更新）
  ```markdown
  > **最后更新**: 2026-01-16
  > **适用版本**: v3.17.0+（事件系统重构）
  ```
- `docs/guides/telemetry_guide.md` - 遥测系统指南（已存在，需要更新）
- `docs/guides/plugins_guide.md` - 插件系统指南（新建）
- `docs/guides/sanitize_guide.md` - 脱敏服务指南（新建）
- `docs/guides/resilience_guide.md` - 熔断器指南（新建）

**需要归档的文档**:
- `docs/guides/logging_configuration.md` - 合并到新的 logging_guide.md
- `docs/guides/logging_pytest_integration.md` - 合并到新的 logging_guide.md
- `docs/guides/modern_logging_best_practices.md` - 合并到新的 logging_guide.md

#### 4.3 Layer 2: Capabilities 能力层
**目标**: 为每个能力创建详细的使用手册
**版本策略**: 📖 使用指南 - 标注"最后更新时间 + 适用版本范围"

**需要创建/更新的文档**:

**HTTP 客户端**:
- `docs/guides/http_client_guide.md` - HTTP 客户端完整指南（新建，整合多个文档）
  ```markdown
  > **最后更新**: 2026-01-16
  > **适用版本**: v2.0.0+（同步），v3.8.0+（异步），v4.0.0+（推荐）

  ## 同步 HttpClient
  > **引入版本**: v2.0.0
  > **状态**: 稳定，向后兼容

  ## 异步 AsyncHttpClient（推荐）
  > **引入版本**: v3.8.0
  > **优化版本**: v4.0.0（性能提升 30 倍）
  ```
  - 同步 HttpClient
  - 异步 AsyncHttpClient
  - 中间件系统
  - 文件上传
  - 认证控制

**数据库**:
- `docs/guides/database_guide.md` - 数据库完整指南（新建）
  ```markdown
  > **最后更新**: 2026-01-16
  > **适用版本**: v2.0.0+（同步），v4.0.0+（异步）

  ## 同步 Database
  > **引入版本**: v2.0.0
  > **状态**: 稳定，向后兼容

  ## 异步 AsyncDatabase（推荐）
  > **引入版本**: v4.0.0
  > **性能提升**: 5-10 倍
  ```
  - 同步 Database
  - 异步 AsyncDatabase
  - Repository 模式
  - Unit of Work 模式
  - 事务管理

**Redis**:
- `docs/guides/redis_guide.md` - Redis 完整指南（新建）
  ```markdown
  > **最后更新**: 2026-01-16
  > **适用版本**: v3.0.0+（同步），v4.0.0+（异步）
  ```
  - 同步 RedisClient
  - 异步 AsyncRedis
  - 常用操作

**UI 驱动**:
- `docs/guides/web-ui-testing.md` - Web UI 测试指南（已存在，需要更新）
  ```markdown
  > **最后更新**: 2026-01-16
  > **适用版本**: v3.0.0+（同步），v4.0.0+（异步）
  ```
  - 同步 AppActions + BasePage
  - 异步 AsyncAppActions + AsyncBasePage
  - 组件模式
  - 调试技巧

**GraphQL & gRPC**:
- `docs/guides/graphql_client.md` - 已存在，检查更新
- `docs/guides/grpc_client.md` - 已存在，检查更新

**消息队列**:
- `docs/guides/message_queue.md` - 已存在，检查更新

**存储**:
- `docs/guides/storage.md` - 已存在，检查更新

**需要归档/合并的文档**:
- `docs/guides/async_http_client.md` - 合并到 http_client_guide.md
- `docs/guides/httpx_advanced_usage.md` - 合并到 http_client_guide.md
- `docs/guides/repository_uow_guide.md` - 合并到 database_guide.md
- `docs/guides/async_database_guide.md` - 合并到 database_guide.md

#### 4.4 Layer 3: Testing + CLI 门面层
**目标**: 更新测试支持和 CLI 文档

**需要创建/更新的文档**:
- `docs/guides/fixtures_guide.md` - Fixtures 完整指南（新建）
- `docs/guides/decorators_guide.md` - 装饰器指南（新建）
- `docs/guides/test_data.md` - 测试数据管理（已存在，需要更新）
- `docs/guides/test_data_cleanup.md` - 已存在，检查更新
- `docs/guides/factory_guide.md` - 已存在，检查更新
- `docs/guides/assertions_guide.md` - 已存在，检查更新
- `docs/guides/mocking.md` - 已存在，检查更新
- `docs/guides/scaffold_cli_guide.md` - CLI 脚手架指南（已存在，检查更新）
- `docs/user-guide/code-generation.md` - 代码生成指南（检查更新）

#### 4.5 Layer 4: Bootstrap 引导层
**目标**: 创建引导层的文档

**需要创建的文档**:
- `docs/guides/bootstrap_guide.md` - Bootstrap 引导系统指南（新建）
  - Bootstrap 初始化
  - Providers 依赖注入
  - Runtime 运行时管理
  - 自定义 Provider

#### 4.6 横切关注点: Plugins
**目标**: 更新插件文档

**需要创建/更新的文档**:
- `docs/guides/monitoring_plugin.md` - 监控插件指南（新建）
- `docs/guides/allure_plugin.md` - Allure 插件指南（新建）
- 更新 `docs/architecture/PLUGIN_SYSTEM_V3.37.md`

--
### 阶段 5：更新开发者文档

#### 5.1 更新贡献指南
**文件**: `CONTRIBUTING.md`
**更新内容**:
- [ ] 更新开发环境设置
- [ ] 更新测试运行说明
- [ ] 更新代码质量要求
- [ ] 添加文档更新规范

#### 5.2 更新开发文档
**目录**: `docs/development/`
**需要更新的文档**:
- `FRAMEWORK_DEPENDENCY_MANAGEMENT.md` - 依赖管理
- `RELEASE.md` - 发布流程

#### 5.3 创建文档维护指南
**新建文件**: `docs/development/DOCUMENTATION_MAINTENANCE.md`
**内容**:
- 文档更新流程
- 文档结构规范
- 版本同步要求
- 归档策略

---

## 📊 文档整理检查清单

### 第一步：清理和归档
- [ ] 归档顶级临时文档（3个文件）
- [ ] 整理架构文档目录（归档约 30 个文件）
- [ ] 归档 docs/analysis/（8 个文件）
- [ ] 归档 docs/plans/（若干文件）
- [ ] 归档 docs/design/（若干文件）
- [ ] 创建归档索引 `docs/archive/README.md`

### 第二步：更新核心文档（仅 5 个需要标注框架版本）
- [ ] 更新 README.md - 版本 v4.0.0 + 更新时间 2026-01-16
- [ ] 更新 CLAUDE.md - 版本 v4.0.0 + 更新时间 2026-01-16
- [ ] 更新 ESSENTIAL_DOCS.md - 框架版本 v4.0.0 + 更新日期 2026-01-16
- [ ] 更新 docs/README.md - 版本 v4.0.0 + 最近更新 2026-01-16
- [ ] 验证所有核心文档版本号一致

### 第三步：更新架构文档
- [ ] 创建 ARCHITECTURE_V4.0.md（核心文档，标注 v4.0.0）
- [ ] 创建五层架构详解.md（使用"最后更新"策略）
- [ ] 更新架构文档导航 README.md
- [ ] 检查并更新专题架构文档（使用"最后更新"策略）
- [ ] 归档历史版本架构文档（标注"已归档"状态）

### 第四步：按分层更新模块文档（使用"最后更新 + 适用版本"策略）
- [ ] Layer 0: Core（7个 API 参考文档）- 标注"引入版本 + 变更历史"
- [ ] Layer 1: Infrastructure（7个指南）- 标注"最后更新 2026-01-16 + 适用版本范围"
- [ ] Layer 2: Capabilities（10个指南）- 标注"最后更新 2026-01-16 + 适用版本范围"
- [ ] Layer 3: Testing + CLI（9个指南）- 标注"最后更新 2026-01-16 + 适用版本范围"
- [ ] Layer 4: Bootstrap（1个指南）- 标注"最后更新 2026-01-16 + 适用版本范围"
- [ ] Plugins（2个指南）- 标注"最后更新 2026-01-16 + 适用版本范围"
- [ ] 验证所有指南文档使用统一的头部模板

### 第五步：更新开发者文档
- [ ] 更新 CONTRIBUTING.md
- [ ] 更新 docs/development/
- [ ] 创建文档维护指南

---

## 🎯 优先级排序

### 高优先级（立即完成）
1. 归档临时文档和历史文档
2. 更新核心文档（README、CLAUDE.md）
3. 创建 v4.0.0 架构总览

### 中优先级（本周完成）
4. 整理架构文档目录
5. 更新 Layer 2 能力层文档（HTTP、Database、Redis、UI）
6. 更新测试支持文档

### 低优先级（按需完成）
7. 创建详细的 API 参考文档
8. 补充高级特性文档
9. 完善示例代码文档

---

## 📝 执行建议

### 分批执行
- **第一批**：清理归档 + 核心文档更新（2-3 小时）
- **第二批**：架构文档 + Layer 0-1（2-3 小时）
- **第三批**：Layer 2 能力层（3-4 小时）
- **第四批**：Layer 3-4 + Plugins（2-3 小时）
- **第五批**：开发者文档 + 最终检查（1-2 小时）

### 验证方法
- 检查所有链接是否有效
- **核心文档**：确保 5 个核心文档版本号统一为 v4.0.0
- **指南文档**：验证所有指南使用"最后更新 + 适用版本"模板
- **API 参考**：确保标注"引入版本 + 变更历史"
- 验证文档内容与代码一致
- 测试文档中的示例代码

---

## 📌 版本管理最佳实践总结

### ✅ 正确的做法

**核心文档（~5 个）**：
```markdown
# README.md, CLAUDE.md, ESSENTIAL_DOCS.md, docs/README.md, ARCHITECTURE_V4.0.md

> **版本**: v4.0.0
> **更新时间**: 2026-01-16
```
- ✅ 每次大版本发布时更新
- ✅ 版本号与框架版本保持一致
- ✅ 数量少，维护成本低

**使用指南（~30 个）**：
```markdown
# HTTP 客户端使用指南

> **最后更新**: 2026-01-16
> **适用版本**: v3.8.0+（同步），v4.0.0+（推荐异步）
```
- ✅ 内容变化时才更新"最后更新"时间
- ✅ 标注功能适用的版本范围
- ✅ 不需要跟随每次框架版本更新

**API 参考（~20 个）**：
```markdown
## AsyncHttpClient

> **引入版本**: v3.8.0
> **稳定版本**: v3.10.0
> **重大改进**: v4.0.0（性能提升 30 倍）

### 版本历史
- v4.0.0: 连接池优化，性能提升 30 倍
- v3.10.0: 稳定版本
- v3.8.0: 首次引入
```
- ✅ 标注功能引入的版本
- ✅ 记录重要的版本变更
- ✅ 帮助用户理解功能演进

**归档文档**：
```markdown
# v3.17 事件系统架构设计

> **版本**: v3.17.0
> **创建时间**: 2025-12-05
> **状态**: ⚠️ 已归档
> **当前文档**: 请参考 [ARCHITECTURE_V4.0.md](../ARCHITECTURE_V4.0.md)
```
- ✅ 明确标注"已归档"状态
- ✅ 指向最新文档
- ✅ 归档后不再更新

### ❌ 错误的做法

- ❌ 所有文档都标注框架版本号
- ❌ 每次框架版本更新都改所有文档
- ❌ 指南文档跟随框架版本号
- ❌ 没有区分"核心文档"和"指南文档"

### 💡 实践建议

1. **核心文档 < 10 个**：只有真正代表框架整体状态的文档才标注框架版本
2. **指南文档**：使用"最后更新"时间，不跟随框架版本
3. **新功能**：在指南中标注"引入版本"，而不是更新整个文档的版本号
4. **版本发布时**：
   - 小版本（v4.0.1）：只更新发布说明
   - 次版本（v4.1.0）：更新核心文档 + 新功能指南
   - 大版本（v5.0.0）：更新核心文档 + 架构文档 + 受影响指南

---

## 🔄 后续维护

### 文档同步机制

**代码变更时**：
- [ ] 功能变化时更新对应指南的"最后更新"时间
- [ ] 新增功能时创建新指南，标注"引入版本"
- [ ] 废弃功能时标注"已废弃"和替代方案

**版本发布时**（按版本类型区分）：
- [ ] **小版本**（v4.0.1）：仅更新发布说明（5 分钟）
- [ ] **次版本**（v4.1.0）：更新 5 个核心文档 + 新功能指南（30 分钟）
- [ ] **大版本**（v5.0.0）：更新核心文档 + 架构 + 受影响指南（2-3 小时）

**定期审查**：
- [ ] 每季度审查文档与代码的一致性
- [ ] 检查"最后更新"时间超过 6 个月的文档
- [ ] 更新过时的示例代码

### 文档质量保证
- [ ] 建立文档审查流程（PR Review 包含文档检查）
- [ ] 定期检查断链（使用工具自动化）
- [ ] 收集用户反馈（GitHub Issues）
- [ ] 持续优化文档结构（基于使用数据）

### 文档更新规范

**创建新文档时**：
1. 确定文档类型（核心/指南/API 参考/归档）
2. 使用对应的头部模板
3. 核心文档需要在 ESSENTIAL_DOCS.md 中添加索引

**更新现有文档时**：
1. 更新"最后更新"时间（指南和 API 参考）
2. 如果是功能变更，在"版本历史"中添加记录
3. 验证示例代码可以运行

**归档文档时**：
1. 移动到 `docs/archive/` 对应目录
2. 添加"已归档"状态和指向当前文档的链接
3. 更新归档索引 `docs/archive/README.md`

---

**下一步行动**: 开始执行第一批任务 - 清理归档 + 核心文档更新
