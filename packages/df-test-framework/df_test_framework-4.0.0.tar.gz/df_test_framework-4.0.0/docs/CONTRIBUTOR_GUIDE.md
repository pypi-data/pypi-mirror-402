# 框架贡献者指南

> **目标读者**: 想要为 DF Test Framework 核心代码做出贡献的开发者
> **更新日期**: 2026-01-19
> **框架版本**: v4.0.0

---

## 📋 目录

- [快速开始](#快速开始)
- [理解框架架构](#理解框架架构)
- [代码贡献流程](#代码贡献流程)
- [开发最佳实践](#开发最佳实践)
- [常见贡献场景](#常见贡献场景)
- [代码审查清单](#代码审查清单)

---

## 🚀 快速开始

### 第一步：环境准备

```bash
# 1. Fork 并克隆仓库
git clone https://github.com/yourorg/df-test-framework.git
cd df-test-framework

# 2. 安装开发依赖（推荐使用 uv）
uv sync --all-extras

# 3. 运行测试，确保环境正常
uv run pytest -v

# 4. 创建特性分支
git checkout -b feature/your-feature-name
```

### 第二步：理解项目结构

```
src/df_test_framework/
├── core/                # Layer 0: 核心抽象（无依赖）
│   ├── middleware/      #   中间件基类和协议
│   ├── context/         #   上下文管理
│   ├── events/          #   事件系统
│   └── protocols/       #   协议定义
├── infrastructure/      # Layer 1: 基础设施
│   ├── config/          #   配置管理
│   ├── logging/         #   日志系统
│   ├── telemetry/       #   遥测和追踪
│   └── plugins/         #   插件系统
├── capabilities/        # Layer 2: 能力层
│   ├── clients/         #   HTTP/GraphQL/gRPC 客户端
│   ├── drivers/         #   Playwright Web 驱动
│   ├── databases/       #   数据库访问
│   ├── messengers/      #   消息队列
│   └── storages/        #   存储客户端
├── testing/             # Layer 3: 测试支持
│   ├── fixtures/        #   pytest fixtures
│   ├── decorators/      #   装饰器
│   ├── data/            #   数据构建器
│   └── debugging/       #   调试工具
├── cli/                 # Layer 3: 命令行工具
│   ├── commands/        #   CLI 命令
│   └── templates/       #   项目模板
├── bootstrap/           # Layer 4: 引导层
│   ├── bootstrap.py     #   Bootstrap 类
│   ├── providers.py     #   Provider 注册
│   └── runtime.py       #   Runtime 上下文
└── plugins/             # 横切关注点
    ├── monitoring/      #   监控插件
    └── allure/          #   Allure 插件
```

### 第三步：选择贡献方向

根据您的兴趣和技能，选择合适的贡献方向：

| 贡献方向 | 难度 | 涉及模块 | 推荐阅读 |
|---------|------|---------|---------|
| **修复 Bug** | ⭐ | 任何模块 | [troubleshooting/](troubleshooting/) |
| **添加测试** | ⭐⭐ | `tests/` | [CONTRIBUTING.md](../CONTRIBUTING.md) |
| **优化性能** | ⭐⭐⭐ | `capabilities/` | [guides/](guides/) |
| **添加新功能** | ⭐⭐⭐⭐ | `capabilities/` | [architecture/](architecture/) |
| **架构改进** | ⭐⭐⭐⭐⭐ | `core/`, `infrastructure/` | [architecture/ARCHITECTURE_V4.0.md](architecture/ARCHITECTURE_V4.0.md) |

---

## 🏗️ 理解框架架构

### 五层架构原则

DF Test Framework 采用严格的五层架构，**依赖规则**：高层可依赖低层，反之不行。

```
Layer 4 (引导层)
    ↓ 依赖
Layer 3 (门面层)
    ↓ 依赖
Layer 2 (能力层)
    ↓ 依赖
Layer 1 (基础设施)
    ↓ 依赖
Layer 0 (核心层 - 无依赖)
```

**关键规则**：
- ✅ Layer 3 可以导入 Layer 0-2 的模块
- ❌ Layer 1 不能导入 Layer 2-4 的模块
- ✅ Layer 0 不依赖任何其他层（纯抽象）

### 核心设计模式

#### 1. 中间件系统（洋葱模型）

```python
# 中间件执行顺序（洋葱模型）
Request → M1 → M2 → M3 → Handler → M3 → M2 → M1 → Response

# 示例：添加自定义中间件
from df_test_framework.core.middleware import BaseMiddleware

class CustomMiddleware(BaseMiddleware):
    async def __call__(self, request: Request, call_next):
        # 请求前处理
        request = request.with_header("X-Custom", "value")

        # 调用下一个中间件
        response = await call_next(request)

        # 响应后处理
        response.headers["X-Processed"] = "true"
        return response
```

**关键文件**：
- `src/df_test_framework/core/middleware/base.py` - 中间件基类
- `src/df_test_framework/capabilities/clients/http/rest/httpx/middleware/` - 内置中间件

#### 2. 事件总线（发布-订阅）

```python
# 事件发布
from df_test_framework.core.events import EventBus, Event

event_bus = EventBus()
event_bus.publish(Event(
    type="http.request.started",
    data={"url": "https://api.example.com"}
))

# 事件订阅
@event_bus.subscribe("http.request.started")
def on_request_started(event: Event):
    print(f"Request started: {event.data['url']}")
```

**关键文件**：
- `src/df_test_framework/core/events/bus.py` - EventBus 实现
- `src/df_test_framework/infrastructure/events/` - 事件基础设施

#### 3. Provider 模式（依赖注入）

```python
# 注册 Provider
from df_test_framework.bootstrap import ProviderRegistry

registry = ProviderRegistry()
registry.register("http_client", HttpClientProvider())

# 获取实例
http_client = runtime.get("http_client")
```

**关键文件**：
- `src/df_test_framework/bootstrap/providers.py` - Provider 注册
- `src/df_test_framework/bootstrap/runtime.py` - Runtime 上下文

---

## 🔄 代码贡献流程

### 步骤1：从 Issue 开始

**建议**：在开始编码前，先创建或认领一个 Issue。

```bash
# 1. 在 GitHub 上创建 Issue，描述：
#    - 问题现象或功能需求
#    - 预期行为
#    - 复现步骤（如果是 Bug）

# 2. 等待维护者确认和分配

# 3. 在 Issue 中评论，表明您将处理此问题
```

### 步骤2：创建特性分支

```bash
# 分支命名规范
git checkout -b <type>/<issue-number>-<short-description>

# 示例
git checkout -b feature/123-add-async-redis
git checkout -b fix/456-middleware-order
git checkout -b refactor/789-simplify-config
```

**分支类型**：
- `feature/` - 新功能
- `fix/` - Bug 修复
- `refactor/` - 重构
- `docs/` - 文档更新
- `test/` - 测试改进
- `perf/` - 性能优化

### 步骤3：编写代码

#### 3.1 遵循代码规范

```bash
# 运行代码检查
uv run ruff check src/ tests/

# 自动修复
uv run ruff check --fix src/ tests/

# 格式化代码
uv run ruff format src/ tests/
```

#### 3.2 类型注解要求

```python
# ✅ 推荐：使用现代类型注解
def create_user(name: str, tags: list[str] | None = None) -> dict[str, Any]:
    ...

# ❌ 避免：旧式类型注解
from typing import Optional, List, Dict
def create_user(name: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    ...
```

#### 3.3 文档字符串要求

```python
def upload_file(key: str, content: bytes) -> dict:
    """上传文件到存储

    Args:
        key: 对象键（文件路径）
        content: 文件内容（字节）

    Returns:
        上传结果字典，包含 key、size 等信息

    Raises:
        ResourceError: 上传失败

    Example:
        >>> client.upload_file("test.txt", b"Hello")
        {'key': 'test.txt', 'size': 5}
    """
    ...
```

### 步骤4：编写测试

**测试覆盖率要求**：≥ 80%

```bash
# 运行测试
uv run pytest -v

# 运行测试并生成覆盖率报告
uv run pytest --cov=src/df_test_framework --cov-report=term-missing

# 只运行特定测试
uv run pytest tests/test_clients/test_http/ -v
```

#### 4.1 单元测试示例

```python
# tests/test_capabilities/test_storages/test_s3_client.py
import pytest
from df_test_framework.capabilities.storages.object.s3 import S3Client, S3Config

def test_upload_file():
    """测试文件上传功能"""
    # Arrange
    config = S3Config(
        endpoint_url="http://localhost:9000",
        access_key="test",
        secret_key="test",
        bucket_name="test-bucket"
    )
    client = S3Client(config)

    # Act
    result = client.upload("test.txt", b"Hello World")

    # Assert
    assert result["key"] == "test.txt"
    assert result["size"] == 11
```

#### 4.2 集成测试示例

```python
# tests/integration/test_http_middleware.py
import pytest
from df_test_framework import Bootstrap

@pytest.mark.integration
def test_middleware_chain():
    """测试中间件链执行顺序"""
    # 测试中间件按正确顺序执行
    ...
```

### 步骤5：提交代码

```bash
# 1. 暂存更改
git add .

# 2. 提交（遵循 Conventional Commits 规范）
git commit -m "feat(storage): add S3 client support

- Add S3Client with upload/download/delete methods
- Add S3Config for configuration
- Add unit tests with 85% coverage
- Update documentation

Closes #123"
```

**Commit Message 格式**：
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 类型**：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `test`: 测试改进
- `refactor`: 重构
- `perf`: 性能优化
- `chore`: 构建/工具链更新

### 步骤6：创建 Pull Request

```bash
# 1. 推送分支到远程
git push origin feature/123-add-s3-client

# 2. 在 GitHub 上创建 PR，填写：
#    - 标题：简洁描述变更
#    - 描述：详细说明变更内容、测试情况
#    - 关联 Issue：Closes #123
```

**PR 描述模板**：
```markdown
## 变更说明
简要描述此 PR 的目的和实现方式

## 变更类型
- [ ] 新功能
- [ ] Bug 修复
- [ ] 重构
- [ ] 文档更新
- [ ] 性能优化

## 测试情况
- [ ] 添加了单元测试
- [ ] 添加了集成测试
- [ ] 测试覆盖率 ≥ 80%
- [ ] 所有测试通过

## 检查清单
- [ ] 代码遵循项目规范
- [ ] 更新了相关文档
- [ ] 更新了 CHANGELOG.md
- [ ] 通过了代码检查（ruff）

## 关联 Issue
Closes #123
```

### 步骤7：代码审查

**审查重点**：
1. **架构合规性**：是否遵循五层架构原则
2. **代码质量**：是否符合代码规范
3. **测试覆盖**：测试是否充分
4. **文档完整性**：是否更新了相关文档
5. **向后兼容性**：是否破坏了现有 API

**响应审查意见**：
```bash
# 1. 根据审查意见修改代码
# 2. 提交新的 commit
git add .
git commit -m "fix: address review comments"
git push origin feature/123-add-s3-client

# 3. 在 PR 中回复审查意见
```

---

## 💡 开发最佳实践

### 1. 遵循五层架构原则

**依赖规则检查清单**：
- [ ] Layer 0 (core/) 不依赖任何其他层
- [ ] Layer 1 (infrastructure/) 只依赖 Layer 0
- [ ] Layer 2 (capabilities/) 只依赖 Layer 0-1
- [ ] Layer 3 (testing/, cli/) 只依赖 Layer 0-2
- [ ] Layer 4 (bootstrap/) 可以依赖所有层

**示例**：
```python
# ✅ 正确：Layer 2 依赖 Layer 1
# src/df_test_framework/capabilities/clients/http/rest/httpx/client.py
from df_test_framework.infrastructure.logging import get_logger  # Layer 1

# ❌ 错误：Layer 1 依赖 Layer 2
# src/df_test_framework/infrastructure/config/settings.py
from df_test_framework.capabilities.clients.http import HttpClient  # Layer 2 - 违反依赖规则！
```

### 2. 异步优先原则

**v4.0.0 开始，框架全面异步化**。新功能应优先实现异步版本：

```python
# ✅ 推荐：异步优先
class AsyncS3Client:
    async def upload(self, key: str, content: bytes) -> dict:
        ...

# ✅ 可选：提供同步包装
class S3Client:
    def __init__(self):
        self._async_client = AsyncS3Client()

    def upload(self, key: str, content: bytes) -> dict:
        return asyncio.run(self._async_client.upload(key, content))
```

### 3. 配置管理最佳实践

**使用 Pydantic v2 配置类**：

```python
from pydantic import Field
from df_test_framework.infrastructure.config import BaseConfig

class S3Config(BaseConfig):
    """S3 客户端配置"""

    endpoint_url: str = Field(
        default="",
        description="S3 端点 URL"
    )
    access_key: str = Field(
        default="",
        description="访问密钥"
    )
    bucket_name: str = Field(
        default="test-bucket",
        description="存储桶名称"
    )

    class Config:
        env_prefix = "S3_"  # 环境变量前缀
```

### 4. 错误处理最佳实践

**使用框架统一异常**：

```python
from df_test_framework.core.exceptions import (
    ConfigurationError,
    ResourceError,
    ValidationError
)

# ✅ 推荐：使用框架异常
def upload_file(key: str, content: bytes) -> dict:
    if not key:
        raise ValidationError("文件键不能为空")

    try:
        # 上传逻辑
        ...
    except ClientError as e:
        raise ResourceError(f"上传失败: {e}") from e

# ❌ 避免：使用通用异常
def upload_file(key: str, content: bytes) -> dict:
    if not key:
        raise ValueError("文件键不能为空")  # 不推荐
```

### 5. 日志记录最佳实践

```python
from df_test_framework.infrastructure.logging import get_logger

logger = get_logger(__name__)

def upload_file(key: str, content: bytes) -> dict:
    logger.info(f"开始上传文件: {key}")

    try:
        result = _do_upload(key, content)
        logger.info(f"文件上传成功: {key} ({result['size']} bytes)")
        return result
    except Exception as e:
        logger.error(f"文件上传失败: {key}", exc_info=True)
        raise
```

**日志级别使用**：
- `logger.debug()` - 详细调试信息
- `logger.info()` - 关键操作信息
- `logger.warning()` - 警告信息
- `logger.error()` - 错误信息（带 `exc_info=True`）

---

## 🎯 常见贡献场景

### 场景1：添加新的 HTTP 客户端功能

**示例**：添加 WebSocket 支持

```python
# 1. 在 capabilities/clients/ 下创建新模块
# src/df_test_framework/capabilities/clients/websocket/client.py

from df_test_framework.infrastructure.logging import get_logger

logger = get_logger(__name__)

class WebSocketClient:
    """WebSocket 客户端"""

    def __init__(self, url: str):
        self.url = url
        logger.info(f"WebSocket 客户端已初始化: {url}")

    async def connect(self):
        """建立连接"""
        ...

# 2. 添加配置类
# src/df_test_framework/capabilities/clients/websocket/config.py

from pydantic import Field
from df_test_framework.infrastructure.config import BaseConfig

class WebSocketConfig(BaseConfig):
    url: str = Field(default="", description="WebSocket URL")

# 3. 添加测试
# tests/test_capabilities/test_clients/test_websocket/test_client.py

def test_websocket_connect():
    """测试 WebSocket 连接"""
    ...

# 4. 更新文档
# docs/guides/websocket_client.md
```

### 场景2：修复 Bug

**示例**：修复中间件执行顺序问题

```bash
# 1. 复现 Bug
# 创建最小复现示例

# 2. 编写失败的测试
# tests/test_core/test_middleware/test_execution_order.py

def test_middleware_execution_order():
    """测试中间件按正确顺序执行"""
    # 这个测试应该失败，证明 Bug 存在
    ...

# 3. 修复代码
# src/df_test_framework/core/middleware/chain.py

# 4. 验证测试通过
uv run pytest tests/test_core/test_middleware/test_execution_order.py -v

# 5. 提交
git commit -m "fix(middleware): correct execution order in middleware chain

- Fix middleware chain to execute in correct order
- Add test to prevent regression

Fixes #456"
```

### 场景3：优化性能

**示例**：优化 HTTP 客户端连接池

```python
# 1. 添加性能测试
# tests/performance/test_http_client_performance.py

import pytest
import time

@pytest.mark.performance
def test_http_client_connection_pool():
    """测试连接池性能"""
    start = time.time()

    # 执行 100 个并发请求
    ...

    duration = time.time() - start
    assert duration < 5.0, f"性能不达标: {duration}s"

# 2. 优化代码
# src/df_test_framework/capabilities/clients/http/rest/httpx/client.py

# 增加连接池大小
self._client = httpx.Client(
    limits=httpx.Limits(
        max_connections=100,  # 从 10 增加到 100
        max_keepalive_connections=20
    )
)

# 3. 验证性能提升
uv run pytest tests/performance/ -v
```

### 场景4：添加新的存储客户端

**示例**：添加阿里云 OSS 客户端

```python
# 1. 创建模块结构
# src/df_test_framework/capabilities/storages/object/oss/
#   ├── __init__.py
#   ├── client.py
#   ├── config.py

# 2. 实现客户端
# src/df_test_framework/capabilities/storages/object/oss/client.py

class OSSClient:
    """阿里云 OSS 客户端"""

    def upload(self, key: str, content: bytes) -> dict:
        """上传文件"""
        ...

# 3. 添加到 __init__.py
# src/df_test_framework/capabilities/storages/__init__.py

from .object.oss import OSSClient, OSSConfig

__all__ = ["OSSClient", "OSSConfig", ...]

# 4. 添加文档
# docs/guides/storage.md - 添加 OSS 使用示例
```

---

## ✅ 代码审查清单

### 提交前自检

**架构合规性**：
- [ ] 遵循五层架构依赖规则
- [ ] 没有循环依赖
- [ ] 模块职责单一清晰

**代码质量**：
- [ ] 通过 `ruff check` 检查
- [ ] 通过 `ruff format` 格式化
- [ ] 使用现代类型注解（`list[str]` 而非 `List[str]`）
- [ ] 添加了完整的文档字符串

**测试覆盖**：
- [ ] 添加了单元测试
- [ ] 测试覆盖率 ≥ 80%
- [ ] 所有测试通过
- [ ] 添加了边界条件测试

**文档更新**：
- [ ] 更新了 API 参考文档
- [ ] 更新了用户指南（如有新功能）
- [ ] 更新了 CHANGELOG.md
- [ ] 更新了 README.md（如有重大变更）

**向后兼容性**：
- [ ] 没有破坏现有 API
- [ ] 如有破坏性变更，已在 CHANGELOG 中标注
- [ ] 提供了迁移指南（如需要）

### 审查者检查清单

**功能正确性**：
- [ ] 功能符合需求
- [ ] 边界条件处理正确
- [ ] 错误处理完善

**代码可维护性**：
- [ ] 代码易于理解
- [ ] 命名清晰准确
- [ ] 没有过度设计

**性能考虑**：
- [ ] 没有明显的性能问题
- [ ] 资源使用合理
- [ ] 异步操作正确实现

**安全性**：
- [ ] 没有安全漏洞
- [ ] 敏感信息正确处理
- [ ] 输入验证充分

---

## 📚 参考资源

### 核心文档
- [架构设计](architecture/ARCHITECTURE_V4.0.md)
- [五层架构详解](architecture/五层架构详解.md)
- [中间件指南](guides/middleware_guide.md)
- [事件总线指南](guides/event_bus_guide.md)

### 开发文档
- [本地开发指南](development/local-development.md)
- [依赖管理](development/FRAMEWORK_DEPENDENCY_MANAGEMENT.md)
- [发布流程](development/RELEASE.md)

### 问题排查
- [常见错误](troubleshooting/common-errors.md)
- [调试指南](troubleshooting/debugging-guide.md)

---

## 🤝 获取帮助

如果您在贡献过程中遇到问题：

1. **查看文档**：先查看 [docs/](docs/) 目录下的相关文档
2. **搜索 Issue**：在 GitHub Issues 中搜索类似问题
3. **提问**：在 Issue 或 Discussion 中提问
4. **联系维护者**：通过 GitHub 联系项目维护者

---

**感谢您为 DF Test Framework 做出贡献！** 🎉

