# 日志系统使用指南

> **最后更新**: 2026-01-17
> **适用版本**: v3.38.2+（structlog 日志系统）

## 概述

DF Test Framework 使用 **structlog** 作为日志系统，提供结构化日志、pytest 无缝集成、多种输出格式等现代化日志功能。

### v3.38.2 重大变更

v3.38.2 版本将日志系统从 **loguru** 迁移到 **structlog**：

| 特性 | v3.38.1 (loguru) | v3.38.2+ (structlog) |
|------|-----------------|---------------------|
| 日志库 | loguru | structlog |
| pytest 集成 | 需要桥接 | 原生支持（stdlib logging） |
| 时间格式 | `{time:YYYY-MM-DD HH:mm:ss}` | `%Y-%m-%d %H:%M:%S.%f` |
| 配置方式 | `setup_logger()` | `configure_logging()` |
| 导入方式 | `from loguru import logger` | `get_logger(__name__)` |

### 核心特性

- ✅ **日志级别由消息性质决定** - debug/info/error 调用对应方法（v3.38.7）
- ✅ **全局配置控制过滤** - YAML `logging.level` 统一控制显示级别（v3.38.7）
- ✅ **pytest 无缝集成** - ProcessorFormatter 统一格式，无重复输出（v3.38.5）
- ✅ **两阶段初始化** - 模块加载时即完成 structlog 早期配置（v3.38.6）
- ✅ **时间格式统一** - structlog 和 pytest 使用相同的 strftime 格式
- ✅ **结构化日志** - JSON/logfmt 输出，便于日志聚合
- ✅ **上下文传播** - 自动传播 request_id、user_id 等
- ✅ **第三方库支持** - PositionalArgumentsFormatter + ExtraAdder（v3.38.5）
- ✅ **多种输出格式** - text、json、logfmt（v3.38.5）
- ✅ **敏感信息脱敏** - 自动脱敏密码、token 等敏感字段
- ✅ **高性能** - orjson 可选支持（v3.38.4）

---

## 快速开始

### 基本使用

```python
from df_test_framework.infrastructure.logging import get_logger

logger = get_logger(__name__)

def test_example():
    logger.info("测试开始", test_id=123)
    logger.debug("调试信息", variable="value")
    logger.error("错误信息", error_code=500)
```

### 配置日志系统

```python
from df_test_framework.infrastructure.logging import configure_logging

configure_logging(
    env="dev",           # 环境: dev/test/staging/prod
    level="INFO",        # 级别: DEBUG/INFO/WARNING/ERROR/CRITICAL
    json_output=None,    # JSON 输出: None=自动, True=强制, False=禁用
    enable_sanitize=True # 敏感信息脱敏
)
```

### 在 pytest 中使用

pytest 插件自动配置，无需手动初始化：

```python
# conftest.py - 通过 Entry Points 自动加载
# 或手动声明：
pytest_plugins = ["df_test_framework.testing.plugins.logging_plugin"]

def test_with_logging():
    logger = get_logger(__name__)
    logger.info("测试执行中", step="验证数据")
    # 日志自动显示在 pytest 输出中
```

---

## 日志系统架构

### 整体架构（v3.38.7）

```
┌─────────────────────────────────────────────────────────────┐
│  日志系统架构 (v3.38.7 - structlog 25.5.0)                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  logger.debug/info/error("msg", k=v)  ← 日志级别由消息决定  │
│  logging.info("msg %s", arg)          ← 第三方库           │
│          │                                                  │
│          ▼                                                  │
│  structlog Processors 管道:                                │
│     ├─ merge_contextvars (合并上下文)                       │
│     ├─ add_logger_name (logger 名称)                       │
│     ├─ add_log_level (添加级别)                            │
│     ├─ PositionalArgumentsFormatter (% 格式化) ← v3.38.5  │
│     ├─ ExtraAdder (extra 参数) ← v3.38.5                  │
│     ├─ sanitize_sensitive_data (脱敏)                      │
│     ├─ TimeStamper (时间戳)                                │
│     ├─ CallsiteParameterAdder (调用位置，可选)            │
│     ├─ _add_trace_info (OpenTelemetry)                    │
│     └─ wrap_for_formatter                                  │
│          │                                                  │
│          ▼                                                  │
│  ProcessorFormatter 渲染:                                  │
│     ├─ text: ConsoleRenderer (彩色)                        │
│     ├─ json: JSONRenderer (orjson 可选)                    │
│     └─ logfmt: LogfmtRenderer ← v3.38.5                   │
│          │                                                  │
│          ▼                                                  │
│  pytest logging-plugin handlers                            │
│     ├─ log_cli_handler (实时显示)                          │
│     └─ log_file_handler (文件日志)                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### pytest 集成架构（v3.38.6）

```
┌─────────────────────────────────────────────────────────────────────────┐
│  pytest + structlog 集成架构 (v3.38.6)                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  阶段 1: 模块加载时 (_early_init_logging)                                │
│     └─ 配置 structlog 基础 processors                                   │
│                                                                         │
│  阶段 2: pytest_configure                                               │
│     └─ 从 settings 读取配置，禁用 structlog 控制台输出                   │
│                                                                         │
│  阶段 3: pytest_sessionstart                                            │
│     └─ 替换 pytest handlers 的 formatter 为 ProcessorFormatter          │
│                                                                         │
│  logger.info("message", key=value)    ← structlog API                  │
│          │                                                              │
│          ▼                                                              │
│  stdlib logging.Logger                ← structlog 使用 stdlib 后端      │
│          │                                                              │
│          ▼                                                              │
│  pytest logging-plugin handlers:                                       │
│     ├─ log_cli_handler (实时显示)     ← 使用 ProcessorFormatter         │
│     └─ log_file_handler (文件日志)    ← 使用 ProcessorFormatter         │
│          │                                                              │
│          ▼                                                              │
│  ProcessorFormatter 渲染输出:                                           │
│     ├─ text: ConsoleRenderer (彩色)                                    │
│     ├─ json: JSONRenderer                                              │
│     └─ logfmt: LogfmtRenderer (v3.38.5)                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 关键设计决策

1. **两阶段初始化** - 模块加载时即配置 structlog，确保日志格式统一（v3.38.6）
2. **禁用 structlog 控制台输出** - 避免与 pytest 输出冲突
3. **替换 pytest handler formatter** - 使用 ProcessorFormatter 统一格式
4. **通过 pluginmanager 访问** - structlog 官方推荐方式
5. **日志级别由消息性质决定** - debug/info/error 调用对应方法（v3.38.7）
6. **全局配置控制过滤** - YAML `logging.level` 统一控制显示级别（v3.38.7）

---

## 配置方法

### configure_logging() API

```python
from df_test_framework.infrastructure.logging import configure_logging

configure_logging(
    env="dev",           # 环境: dev/test/staging/prod
    level="INFO",        # 级别: DEBUG/INFO/WARNING/ERROR/CRITICAL
    json_output=None,    # JSON 输出: None=自动, True=强制, False=禁用
    enable_sanitize=True # 敏感信息脱敏
)
```

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `env` | str | "dev" | 环境名称，影响输出格式 |
| `level` | str | "INFO" | 日志级别 |
| `json_output` | bool \| None | None | JSON 输出模式 |
| `enable_sanitize` | bool | True | 敏感信息脱敏 |

### 环境与输出格式

| 环境 | json_output | 输出格式 |
|------|-------------|----------|
| dev | None/False | 彩色控制台 |
| test | None/False | 彩色控制台 |
| staging | None | JSON |
| prod/production | None | JSON |
| 任意 | True | JSON |
| 任意 | False | 彩色控制台 |

### YAML 配置

```yaml
# config/base.yaml
logging:
  level: DEBUG
  format: text       # text（开发）/ json（生产）/ logfmt（Loki）
  sanitize: true     # 敏感信息脱敏
  # pytest 环境下 enable_console 会自动设为 false
```

### 开发环境配置

```python
from df_test_framework.infrastructure.logging import configure_logging

configure_logging(
    env="dev",
    level="DEBUG",
    json_output=False,
)
```

输出示例：
```
2025-12-25 11:35:07.590123 [info     ] 用户登录          user_id=123 username=alice
```

### 生产环境配置

```python
configure_logging(
    env="prod",
    level="INFO",
    json_output=True,
)
```

输出示例：
```json
{"event": "用户登录", "user_id": 123, "username": "alice", "timestamp": "2025-12-25 11:35:07.590123", "level": "info"}
```

---

## pytest 集成

### 自动配置

**v3.37.0+**: 插件通过 Entry Points 自动加载，无需手动配置。

如需显式声明（向后兼容）：

```python
# conftest.py
pytest_plugins = ["df_test_framework.testing.plugins.logging_plugin"]
```

### pyproject.toml 配置

```toml
[tool.pytest]
# Live logging: 实时显示日志
log_cli = true
log_cli_level = "INFO"
log_cli_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
log_cli_date_format = "%Y-%m-%d %H:%M:%S"

# 捕获日志（测试失败时显示）
log_level = "DEBUG"
log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
log_date_format = "%Y-%m-%d %H:%M:%S"
```

### 配置项说明

| 配置项 | 作用 | 默认值 | 推荐值 |
|--------|------|--------|--------|
| `log_cli` | 启用实时日志 | false | true |
| `log_cli_level` | 实时显示级别 | NOTSET | INFO |
| `log_cli_format` | 实时日志格式 | pytest 默认 | 见上方示例 |
| `log_cli_date_format` | 时间格式 | %H:%M:%S | %Y-%m-%d %H:%M:%S |
| `log_level` | 捕获级别 | NOTSET | DEBUG |

### 日志输出效果

**开发环境 (format: text)**：

```
-------------------------- live log sessionstart --------------------------
2025-12-25 10:27:55.139176 [info] 环境信息已添加到Allure报告 [allure.helper]

tests/api/test_example.py::TestExample::test_uow_pattern
----------------------------- live log setup ------------------------------
2025-12-25 10:27:55.451533 [info] 数据库连接已建立 [databases.database]
PASSED
---------------------------- live log teardown ----------------------------
2025-12-25 10:27:55.479190 [info] UnitOfWork: 数据已回滚 [databases.uow]
```

**生产环境 (format: json)**：

```json
{"timestamp": "2025-12-25T10:27:55.139176Z", "level": "info", "event": "环境信息已添加到Allure报告", "logger": "allure.helper"}
```

**Loki/Prometheus (format: logfmt)**：

```
timestamp=2025-12-25T10:27:55.139176Z level=info logger=allure.helper event="环境信息已添加到Allure报告"
```

---

## 使用指南

### 基础使用

```python
from df_test_framework.infrastructure.logging import get_logger

logger = get_logger(__name__)

def test_example():
    logger.info("测试开始", test_id=123)
    logger.debug("调试信息", variable="value")
    logger.error("错误信息", error_code=500)
```

### 结构化日志

```python
# ✅ 推荐：结构化字段
logger.info("用户登录", user_id=123, ip="192.168.1.1")

# ❌ 不推荐：格式化字符串
logger.info(f"用户 {user_id} 从 {ip} 登录")
```

### 上下文绑定

```python
from df_test_framework.infrastructure.logging import (
    bind_contextvars,
    clear_contextvars,
    get_logger,
)

def test_with_context():
    # 绑定请求上下文
    bind_contextvars(request_id="req_123", user_id=456)

    logger = get_logger(__name__)
    logger.info("处理请求")  # 自动包含 request_id, user_id

    # 清理上下文
    clear_contextvars()
```

### 第三方库日志

v3.38.5 自动处理第三方库的日志格式：

```python
import logging

def test_third_party_logging():
    # 第三方库使用标准 logging
    stdlib_logger = logging.getLogger("httpx")

    # % 格式化自动处理
    stdlib_logger.info("Request %s %s", "GET", "/api/users")

    # extra 参数自动处理
    stdlib_logger.info("Response", extra={"status": 200, "duration": 45.5})
```

---

## 最佳实践

### 1. 日志级别使用

| 级别 | 使用场景 | 示例 |
|------|----------|------|
| DEBUG | 详细诊断信息 | SQL 查询、变量值 |
| INFO | 关键操作确认 | 用户登录、订单创建 |
| WARNING | 警告但不影响运行 | 缓存未命中 |
| ERROR | 错误但可恢复 | API 超时重试 |
| CRITICAL | 严重错误 | 数据库连接失败 |

### 2. 推荐配置

**开发环境**：
```toml
[tool.pytest]
log_cli = true
log_cli_level = "DEBUG"
log_cli_date_format = "%Y-%m-%d %H:%M:%S"
```

**生产环境**：
```python
configure_logging(env="prod", level="INFO")
```

### 3. 结构化日志

```python
# ✅ 推荐：结构化字段
logger.info("用户登录", user_id=123, ip="192.168.1.1")

# ❌ 不推荐：格式化字符串
logger.info(f"用户 {user_id} 从 {ip} 登录")
```

### 4. 上下文传播

```python
from df_test_framework.infrastructure.logging import (
    bind_contextvars,
    clear_contextvars,
)

# 请求开始时
bind_contextvars(request_id="req_123", user_id=456)

# 请求结束时
clear_contextvars()
```

---

## 常见问题

### Q1: 日志没有显示？

检查以下配置：

```toml
[tool.pytest]
log_cli = true           # 必须启用
log_cli_level = "DEBUG"  # 级别足够低
```

### Q2: 日志与测试名称混在同一行？

**症状**：
```
tests/test_example.py::test_foo 2025-12-25 09:21:37 | INFO | ... - 日志内容
```

**原因**：v3.38.2 之前版本的桥接问题

**解决**：升级到 v3.38.2+，使用 structlog 原生 stdlib 支持

### Q3: 测试失败时看不到 DEBUG 日志？

**原因**：`log_level` 配置过高

**解决**：
```toml
[tool.pytest]
log_level = "DEBUG"  # 捕获所有级别
```

注意区分：
- `log_cli_level` - 控制**实时显示**
- `log_level` - 控制**捕获级别**

### Q4: 敏感信息（密码、token）泄露到日志？

**原因**：脱敏功能未启用

**解决**：确保 `enable_sanitize=True`（默认启用）

```python
configure_logging(env="dev", enable_sanitize=True)
```

自动脱敏的字段：
- password, passwd, pwd
- token, secret, api_key, apikey
- authorization, auth, credential
- access_token, refresh_token

### Q5: 如何禁用实时日志？

```bash
pytest --log-cli-level=CRITICAL  # 只显示 CRITICAL 级别
```

或在配置中：

```toml
[tool.pytest]
log_cli = false
```

---

## 相关文档

- [配置系统指南](config_guide.md) - 日志配置管理
- [Fixtures 使用指南](fixtures_guide.md) - pytest fixtures 详细说明
- [Bootstrap 引导系统指南](bootstrap_guide.md) - 框架初始化
- [EventBus 使用指南](event_bus_guide.md) - 事件系统详解

### 官方文档

- [structlog 文档](https://www.structlog.org/)
- [pytest logging 文档](https://docs.pytest.org/en/stable/how-to/logging.html)
- [Python logging 文档](https://docs.python.org/3/library/logging.html)

### 版本历史

| 版本 | 变更 |
|------|------|
| v3.38.7 | 简化架构：日志级别由消息性质决定，全局配置控制过滤 |
| v3.38.6 | 两阶段初始化：模块加载时即完成 structlog 早期配置 |
| v3.38.5 | 修复 pytest 集成：禁用 structlog 控制台输出，替换 pytest handler formatter |
| v3.38.2 | 从 loguru 迁移到 structlog，使用 stdlib logging 后端 |
| v3.26.0 | loguru → logging 桥接方案（已废弃） |

---

**完成时间**: 2026-01-17

