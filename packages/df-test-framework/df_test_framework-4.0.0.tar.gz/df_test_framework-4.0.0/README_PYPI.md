# DF Test Framework

> 简单、强大、可扩展的现代化 Python 测试自动化框架

[![PyPI version](https://img.shields.io/pypi/v/df-test-framework.svg)](https://pypi.org/project/df-test-framework/)
[![Python](https://img.shields.io/badge/python-3.12+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](https://github.com/yourorg/test-framework/blob/master/LICENSE)

---

## 核心特性

### v4.0.0 全面异步化 - 性能飞跃 🚀

- **AsyncHttpClient** - 异步 HTTP 客户端，并发性能提升 **10-30 倍**
- **AsyncDatabase** - 异步数据库客户端，基于 SQLAlchemy 2.0 AsyncEngine
- **AsyncRedis** - 异步 Redis 客户端，缓存操作提升 **5-10 倍**
- **AsyncAppActions** - 异步 UI 测试，Playwright 异步 API，性能提升 **2-3 倍**
- **完全向后兼容** - 同步 API 完整保留，升级路径平滑

### 完整功能

- **HTTP 客户端** - 同步/异步，拦截器链，自动重试
- **GraphQL/gRPC 客户端** - 完整协议支持
- **数据库访问** - SQLAlchemy 2.0，Repository + UnitOfWork 模式
- **消息队列** - Kafka/RabbitMQ/RocketMQ 统一接口
- **存储客户端** - LocalFile/S3/阿里云 OSS
- **可观测性** - OpenTelemetry 追踪 + Prometheus 监控
- **测试工具** - Fixtures、数据构建器、Mock 工具、Allure 集成

---

## 安装

```bash
# 使用 uv（推荐 - 更快更可靠）
uv add df-test-framework

# 使用 pip
pip install df-test-framework

# 可选依赖
uv add "df-test-framework[ui]"            # UI 测试（Playwright）
uv add "df-test-framework[mq]"            # 消息队列
uv add "df-test-framework[observability]" # 可观测性
uv add "df-test-framework[storage]"       # 存储客户端
uv add "df-test-framework[all]"           # 所有功能
```

---

## 快速开始

### 脚手架创建项目

```bash
df-test init my-test-project
cd my-test-project
cp .env.example .env
pytest -v
```

### 手动使用

```python
from df_test_framework import Bootstrap, FrameworkSettings
from pydantic import Field

class DemoSettings(FrameworkSettings):
    api_base_url: str = Field(default="https://api.example.com")

runtime = (
    Bootstrap()
    .with_settings(DemoSettings)
    .build()
    .run()
)

http = runtime.http_client()
response = http.get("/users/1")
assert response.status_code == 200
```

### 异步高性能模式

```python
import asyncio
from df_test_framework import AsyncHttpClient

async def test_concurrent():
    async with AsyncHttpClient("https://api.example.com") as client:
        tasks = [client.get(f"/users/{i}") for i in range(100)]
        responses = await asyncio.gather(*tasks)
        assert len(responses) == 100

asyncio.run(test_concurrent())
```

---

## 架构

```
Layer 4 ─── bootstrap/          # 引导层：Bootstrap、Providers、Runtime
Layer 3 ─── testing/ + cli/     # 门面层：Fixtures、CLI 工具、脚手架
Layer 2 ─── capabilities/       # 能力层：HTTP/UI/DB/MQ/Storage
Layer 1 ─── infrastructure/     # 基础设施：config/logging/events/plugins
Layer 0 ─── core/               # 核心层：纯抽象（无依赖）
横切 ───── plugins/             # 插件：MonitoringPlugin、AllurePlugin
```

---

## 文档

完整文档请访问 [GitHub 仓库](https://github.com/yourorg/test-framework)：

- [快速开始指南](https://github.com/yourorg/test-framework/blob/master/docs/user-guide/QUICK_START.md)
- [完整用户手册](https://github.com/yourorg/test-framework/blob/master/docs/user-guide/USER_MANUAL.md)
- [API 参考](https://github.com/yourorg/test-framework/tree/master/docs/api-reference)
- [版本发布说明](https://github.com/yourorg/test-framework/tree/master/docs/releases)

---

## 许可证

MIT License
