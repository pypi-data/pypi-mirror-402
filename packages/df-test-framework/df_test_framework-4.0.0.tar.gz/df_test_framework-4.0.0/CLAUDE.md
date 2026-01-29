# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 项目概述

**DF Test Framework** - 现代化 Python 测试自动化框架

- **版本**: v4.0.0
- **更新时间**: 2026-01-16
- **Python**: 3.12+
- **核心技术栈**: pytest + httpx + Playwright + Pydantic v2 + SQLAlchemy 2.0 + Pluggy
- **架构**: 五层架构 + 横切关注点（能力层驱动设计）

### v4.0.0 重大变更

**全面异步化**：
- ✅ AsyncHttpClient - 并发性能提升 10-30 倍
- ✅ AsyncDatabase - 基于 SQLAlchemy 2.0 AsyncEngine
- ✅ AsyncRedis - 缓存操作提升 5-10 倍
- ✅ AsyncAppActions + AsyncBasePage - UI 测试性能提升 2-3 倍
- ✅ 完全向后兼容 - 同步 API 保留

---

## 核心开发命令

```bash
# 依赖管理
uv sync                    # 同步开发依赖
uv sync --all-extras       # 同步所有可选依赖

# 测试
uv run pytest -v                                    # 运行所有测试
uv run pytest -v --ignore=tests/test_messengers/    # 排除 MQ 测试

# 代码质量
uv run ruff check --fix src/ tests/    # 检查 + 自动修复
uv run ruff format src/ tests/         # 格式化
uv run mypy src/                       # 类型检查，可以跳过

# 覆盖率（目标 ≥80%）
uv run pytest --cov=src/df_test_framework --cov-report=term-missing
```

---

## 五层架构

```
Layer 4 ─── bootstrap/          # 引导层：Bootstrap、Providers、Runtime
Layer 3 ─── testing/ + cli/     # 门面层：Fixtures、CLI 工具、脚手架
Layer 2 ─── capabilities/       # 能力层：HTTP/UI/DB/MQ/Storage
Layer 1 ─── infrastructure/     # 基础设施：config/logging/events/plugins
Layer 0 ─── core/               # 核心层：纯抽象（无依赖）
横切 ───── plugins/             # 插件：MonitoringPlugin、AllurePlugin
```

**依赖规则**: 高层可依赖低层，反之不行。Layer 0 无任何依赖。

---

## 核心模式

### HTTP 与 UI 测试架构一致性 (v3.45.0)

| 维度 | HTTP 测试 | UI 测试 |
|------|-----------|---------|
| **装饰器** | `@api_class()` | `@actions_class()` |
| **基类** | `BaseAPI` | `AppActions` |
| **自动加载** | `load_api_fixtures()` | `load_actions_fixtures()` |
| **配置字段** | `test.apis_package` | `test.actions_package` |
| **目录** | `apis/` | `actions/` |
| **默认 scope** | `session` | `function` |

### 脚手架项目类型

```bash
df-test init my-project --type api   # API 项目：apis/, models/
df-test init my-project --type ui    # UI 项目：actions/, pages/, components/
df-test init my-project --type full  # 完整项目：apis/ + actions/ + pages/
```

### 关键组件

- **中间件系统**: 洋葱模型，SignatureMiddleware、BearerTokenMiddleware、RetryMiddleware
- **EventBus**: 事件驱动，HTTP/UI 事件自动发布，Allure 自动记录
- **配置系统**: YAML 分层配置 + 环境变量，WebConfig/HTTPConfig/DatabaseConfig

---

## 代码规范

### 类型注解

```python
# ✅ 现代风格
def create(name: str, items: list[str] | None = None) -> dict[str, Any]: ...

# ❌ 旧式
def create(name: str, items: Optional[List[str]] = None) -> Dict[str, Any]: ...
```

### 测试命名

```python
# ✅ 清晰描述场景
def test_login_with_valid_credentials_returns_token(self): ...

# ❌ 不清晰
def test_login(self): ...
```

### Ruff 配置

- 行长度: 100
- 目标版本: Python 3.12

---

## 版本发布

**每次发布必须更新**:
1. `pyproject.toml` + `__init__.py` 版本号
2. `CHANGELOG.md` - 简洁摘要
3. `docs/releases/vX.X.X.md` - 详细发布说明
4. `docs/guides/xxx.md` - 功能使用指南（如有新功能）

**Commit Message**: `<type>(<scope>): <subject>`
- Type: feat/fix/docs/test/refactor/chore
- Subject: 中文描述

---

## 目录结构

```
src/df_test_framework/
├── core/                # Layer 0: middleware/context/events/protocols
├── infrastructure/      # Layer 1: config/logging/telemetry/events/plugins
├── capabilities/        # Layer 2: clients/drivers/databases/messengers/storages
│   ├── clients/         #   HTTP + GraphQL + gRPC
│   ├── drivers/         #   Playwright (Web UI)
│   ├── databases/       #   MySQL + Redis + Repository + UoW
│   ├── messengers/      #   Kafka + RabbitMQ + RocketMQ
│   └── storages/        #   LocalFile + S3 + OSS
├── testing/             # Layer 3: fixtures/decorators/data/debugging
├── cli/                 # Layer 3: commands + templates
├── bootstrap/           # Layer 4: Bootstrap + Providers + Runtime
└── plugins/             # 横切: MonitoringPlugin + AllurePlugin

cli/templates/
├── project/             # 项目初始化模板（api/ui/full）
└── generators/          # 代码生成模板
```

---

## 重要提示

- `tests/test_messengers/` 需要外部服务（Kafka/RabbitMQ/RocketMQ），CI 中跳过
- `engines/` 目录预留，暂未实现
- Windows 平台使用 `start` 而非 `open` 打开报告

---

## 参考文档

| 类型 | 路径 |
|------|------|
| 架构设计 | `docs/architecture/` |
| 使用指南 | `docs/guides/` |
| Web UI 测试 | `docs/guides/web-ui-testing.md` |
| 版本发布 | `docs/releases/` |
| 更新日志 | `CHANGELOG.md` |
