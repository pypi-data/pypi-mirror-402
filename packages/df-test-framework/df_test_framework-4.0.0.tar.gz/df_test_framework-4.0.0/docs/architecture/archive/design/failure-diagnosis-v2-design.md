# Web 测试失败诊断系统 v2.0 设计方案

> 基于策略模式的现代化失败诊断架构设计
>
> 📅 创建日期: 2026-01-15
> 🎯 优先级: P2（未来增强，非核心功能）
> 📊 状态: 设计阶段

---

## 📋 目录

- [1. 背景和动机](#1-背景和动机)
- [2. 现有实现分析](#2-现有实现分析)
- [3. 设计目标](#3-设计目标)
- [4. 核心架构设计](#4-核心架构设计)
- [5. 详细实现方案](#5-详细实现方案)
- [6. 配置系统](#6-配置系统)
- [7. Pytest 集成](#7-pytest-集成)
- [8. 实施路径](#8-实施路径)
- [9. 对比分析](#9-对比分析)
- [10. 参考资料](#10-参考资料)

---

## 1. 背景和动机

### 1.1 问题陈述

当前框架已实现 Web 测试失败自动诊断功能（v3.46.x），包括：
- ✅ Playwright 原生视频录制（`retain-on-failure` 模式）
- ✅ EventBus 事件驱动架构
- ✅ AllureObserver 自动记录事件到 Allure 报告
- ✅ 零配置自动化（autouse fixture）

**然而，现有实现存在以下局限性**：

| 问题 | 影响 | 场景示例 |
|------|------|---------|
| **失败策略固化** | 只支持 Playwright 原生的几种视频模式 | 无法自定义"仅保留最后 3 次失败的视频" |
| **扩展性受限** | 难以添加自定义失败处理器 | 无法上传到 OSS、发送 Slack 通知 |
| **类型安全不足** | 事件处理器缺乏强类型约束 | 运行时才能发现类型错误 |
| **同步阻塞调用** | 视频处理在 fixture teardown 中同步执行 | 阻塞测试进程，影响性能 |
| **资源管理分散** | 截图、视频、日志管理分散在不同位置 | 难以统一清理、归档 |

### 1.2 设计动机

设计一套**现代化、可扩展、高性能**的失败诊断系统，核心理念：

> **将失败诊断从固化的流程转变为可组合的策略系统**

**设计原则**：
1. ✅ **策略可插拔** - 用户可自由组合策略链
2. ✅ **类型安全** - Protocol + Pydantic + 泛型
3. ✅ **异步优先** - 支持并发执行，不阻塞测试
4. ✅ **异常隔离** - 单个策略失败不影响其他策略
5. ✅ **零侵入集成** - 保持现有的零配置自动化体验

---

## 2. 现有实现分析

### 2.1 架构概览

当前实现采用 **EventBus + Pytest Fixtures + Allure Observer** 架构：

```
┌─────────────────────────────────────────────────────────┐
│                Pytest Test Execution                    │
└─────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  _auto_allure_observer (autouse fixture)                │
│  - 创建 AllureObserver                                  │
│  - 订阅所有事件到 EventBus                              │
└─────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  BrowserManager (Playwright)                            │
│  - _setup_event_listeners(page)                         │
│  - page.on("console", ...)                              │
│  - page.on("pageerror", ...)                            │
└─────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  EventBus.publish(event)                                │
│  - 根据 scope 过滤订阅者                                │
│  - 异步分发事件                                         │
└─────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  AllureObserver.handle_ui_error_event(event)            │
│  - 解析事件数据                                         │
│  - 附加截图到 Allure                                    │
│  - 附加错误详情到 Allure                                │
└─────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  context fixture teardown                               │
│  - 获取视频路径                                         │
│  - 根据 record_mode 决定是否删除视频                    │
└─────────────────────────────────────────────────────────┘
```

### 2.2 关键代码位置

| 功能模块 | 文件路径 | 关键函数/类 |
|---------|---------|-----------|
| **视频录制** | `testing/fixtures/ui.py:88-159` | `context` fixture |
| **视频清理** | `testing/fixtures/ui.py:161-208` | `_test_failed()`, `_delete_video_file()` |
| **截图助手** | `testing/fixtures/ui.py:296-324` | `screenshot` fixture |
| **EventBus** | `infrastructure/events/bus.py` | `EventBus.publish()`, `.subscribe()` |
| **Playwright 事件** | `capabilities/drivers/web/playwright/browser.py:260-412` | `_setup_event_listeners()` |
| **Allure 自动订阅** | `testing/fixtures/allure.py:127-293` | `_auto_allure_observer` fixture |
| **Allure 事件处理** | `testing/reporting/allure/observer.py` | `AllureObserver.handle_ui_*()` |

### 2.3 优势分析

| 优势 | 说明 | 价值 |
|------|------|------|
| ✅ **零配置自动化** | autouse fixture 自动生效 | 用户无需编写额外代码 |
| ✅ **事件驱动解耦** | 通过 EventBus 解耦各组件 | 组件独立，易于测试 |
| ✅ **智能资源管理** | `retain-on-failure` 只保留失败视频 | 节省存储空间 |
| ✅ **测试隔离** | function 级别 fixture | 每个测试独立环境 |
| ✅ **Pytest 深度集成** | 充分利用 pytest 生态 | 用户体验好 |

### 2.4 不足分析

| 不足 | 影响 | 改进方向 |
|------|------|---------|
| ❌ **失败策略固化** | 只支持 Playwright 原生模式 | 策略模式重构 |
| ❌ **扩展性受限** | 难以添加自定义处理器 | 可插拔策略链 |
| ❌ **类型安全不足** | 事件处理器缺乏强类型约束 | Protocol + 泛型 |
| ❌ **同步阻塞调用** | 视频处理阻塞测试进程 | 异步并发执行 |
| ❌ **资源管理分散** | 截图、视频、日志分散管理 | 统一资源模型 |

---

## 3. 设计目标

### 3.1 核心目标

1. **🎯 可扩展性** - 用户可自由添加自定义策略，无需修改框架代码
2. **🎯 类型安全** - 编译时类型检查，减少运行时错误
3. **🎯 高性能** - 支持并发执行策略，不阻塞测试进程
4. **🎯 容错性** - 单个策略失败不影响其他策略和测试执行
5. **🎯 零侵入** - 保持现有的零配置自动化体验

### 3.2 非目标（Not Goals）

- ❌ **不替换 EventBus** - EventBus 仍用于实时事件监听
- ❌ **不破坏现有 API** - 提供向后兼容层
- ❌ **不增加复杂度** - 对于简单场景，保持零配置

### 3.3 成功标准

| 标准 | 衡量方式 |
|------|---------|
| **可扩展性** | 用户可在 10 行代码内添加自定义策略 |
| **类型安全** | mypy 检查通过，无类型错误 |
| **性能** | 并行执行策略，诊断时间 < 5 秒 |
| **容错性** | 单个策略失败，其他策略正常执行 |
| **零侵入** | 现有测试无需修改，自动生效 |

---

## 4. 核心架构设计

### 4.1 整体架构

采用 **策略模式 + 责任链模式 + 异步事件驱动** 的混合架构：

```
┌─────────────────────────────────────────────────────────────┐
│                     Pytest Layer                            │
│          (pytest_runtest_makereport hook + fixtures)        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              DiagnosisCoordinator                           │
│     (失败诊断协调器 - 编排策略链，管理生命周期)               │
│                                                             │
│  - setup_strategies()      # 初始化所有策略                │
│  - execute_strategies()    # 并行/串行执行策略             │
│  - cleanup_strategies()    # 清理资源                      │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  CaptureStrategy │  │ ProcessStrategy  │  │  ReportStrategy  │
│   (资源采集)     │  │   (资源处理)     │  │   (报告附加)     │
├──────────────────┤  ├──────────────────┤  ├──────────────────┤
│ • Screenshot     │  │ • Compress       │  │ • AllureReporter │
│ • Video          │  │ • Upload to OSS  │  │ • SlackReporter  │
│ • HTML Snapshot  │  │ • Cleanup        │  │ • JiraReporter   │
│ • Console Logs   │  │ • Retention      │  │ • CustomWebhook  │
│ • Network HAR    │  │ • Encrypt        │  │                  │
└──────────────────┘  └──────────────────┘  └──────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Artifact Storage                               │
│     (统一的诊断资源存储抽象 - 支持本地/S3/OSS)               │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 分层职责

| 层次 | 组件 | 职责 |
|------|------|------|
| **控制层** | `DiagnosisCoordinator` | 编排策略链，管理生命周期，异常隔离 |
| **策略层** | `CaptureStrategy` | 采集诊断资源（截图、视频、日志等） |
| **策略层** | `ProcessStrategy` | 处理资源（压缩、上传、清理等） |
| **策略层** | `ReportStrategy` | 附加到报告系统（Allure、Slack 等） |
| **存储层** | `ArtifactStorage` | 统一资源存储抽象（本地/S3/OSS） |

### 4.3 核心设计模式

#### 4.3.1 策略模式（Strategy Pattern）

**意图**：定义一系列算法，把它们一个个封装起来，并且使它们可以相互替换。

```python
# 定义策略接口
class DiagnosisStrategy(Protocol):
    async def setup(self, test_context: TestContext) -> None: ...
    async def execute(self, test_context: TestContext, result: DiagnosisResult) -> list[DiagnosisArtifact]: ...
    async def cleanup(self) -> None: ...

# 具体策略实现
class ScreenshotCaptureStrategy:
    async def execute(self, test_context, result):
        # 采集截图
        return [screenshot_artifact]

class OSSUploadStrategy:
    async def execute(self, test_context, result):
        # 上传资源到 OSS
        return [uploaded_artifact]
```

**优势**：
- ✅ 策略可独立开发、测试、部署
- ✅ 符合开闭原则（对扩展开放，对修改封闭）
- ✅ 用户可自由组合策略

#### 4.3.2 责任链模式（Chain of Responsibility）

**意图**：使多个对象都有机会处理请求，从而避免请求的发送者和接收者之间的耦合关系。

```python
class DiagnosisCoordinator:
    def __init__(self, strategies: Sequence[DiagnosisStrategy]):
        # 按 priority 排序策略链
        self._strategies = sorted(strategies, key=lambda s: s.priority)

    async def diagnose(self, test_context):
        result = DiagnosisResult(test_context=test_context)

        # 依次执行策略链
        for strategy in self._strategies:
            artifacts = await strategy.execute(test_context, result)
            result.artifacts.extend(artifacts)

        return result
```

**优势**：
- ✅ 降低耦合度（请求者和处理者解耦）
- ✅ 灵活的责任分配（通过 priority 控制顺序）
- ✅ 支持动态添加/删除策略

#### 4.3.3 模板方法模式（Template Method）

**意图**：定义算法骨架，将一些步骤延迟到子类实现。

```python
class DiagnosisCoordinator:
    async def diagnose(self, test_context):
        # 模板方法：定义诊断流程
        result = DiagnosisResult(test_context=test_context)

        # 1. Setup 阶段
        await self._setup_strategies(test_context, result)

        # 2. Execute 阶段
        await self._execute_strategies(test_context, result)

        # 3. Cleanup 阶段
        await self._cleanup_strategies(result)

        return result
```

**优势**：
- ✅ 封装不变部分，扩展可变部分
- ✅ 提取公共代码，便于维护
- ✅ 行为由父类控制，子类实现细节

### 4.4 关键设计决策

| 决策点 | 选项 A | 选项 B | **最终选择** | 理由 |
|--------|--------|--------|-------------|------|
| **策略执行顺序** | 固定顺序 | priority 排序 | **B: priority 排序** | 灵活性更高，用户可控制 |
| **策略执行模式** | 串行执行 | 并行执行 | **B: 支持并行** | 性能更好，可配置 |
| **异常处理** | 整体失败 | 异常隔离 | **B: 异常隔离** | 单个策略失败不影响其他 |
| **类型约束** | Duck Typing | Protocol | **B: Protocol** | 类型安全，IDE 友好 |
| **资源存储** | 仅本地 | 抽象接口 | **B: 抽象接口** | 支持多种存储后端 |

---

## 5. 详细实现方案

### 5.1 核心数据模型

#### 5.1.1 数据模型设计

```python
"""
src/df_test_framework/testing/diagnosis/models.py
失败诊断核心数据模型
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict


class DiagnosisType(str, Enum):
    """诊断资源类型"""
    SCREENSHOT = "screenshot"
    VIDEO = "video"
    HTML_SNAPSHOT = "html_snapshot"
    CONSOLE_LOG = "console_log"
    NETWORK_HAR = "network_har"
    TRACE = "trace"
    STORAGE_STATE = "storage_state"  # Cookies/LocalStorage
    CUSTOM = "custom"


class FailureReason(str, Enum):
    """失败原因分类"""
    ASSERTION_ERROR = "assertion_error"
    TIMEOUT = "timeout"
    ELEMENT_NOT_FOUND = "element_not_found"
    NETWORK_ERROR = "network_error"
    JAVASCRIPT_ERROR = "javascript_error"
    CRASH = "crash"
    UNKNOWN = "unknown"


class TestContext(BaseModel):
    """测试上下文信息

    包含测试标识、失败信息、环境信息、时间戳等
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # 测试标识
    test_id: str = Field(default_factory=lambda: str(uuid4()))
    test_name: str
    test_nodeid: str  # pytest nodeid
    test_file: str
    test_class: str | None = None
    test_function: str

    # 失败信息
    failure_reason: FailureReason
    exception: Exception | None = None
    exception_message: str
    exception_traceback: str | None = None

    # 时间戳
    started_at: datetime
    failed_at: datetime

    # 环境信息
    browser_type: str | None = None
    viewport: dict[str, int] | None = None
    url: str | None = None
    user_agent: str | None = None

    # 额外元数据
    metadata: dict[str, Any] = Field(default_factory=dict)


class DiagnosisArtifact(BaseModel):
    """诊断资源

    表示一个诊断产生的资源（截图、视频、日志等）
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # 资源标识
    artifact_id: str = Field(default_factory=lambda: str(uuid4()))
    artifact_type: DiagnosisType
    name: str
    description: str | None = None

    # 文件信息
    file_path: Path | None = None  # 本地路径
    remote_url: str | None = None  # 远程 URL（上传后）
    mime_type: str
    size_bytes: int | None = None
    checksum: str | None = None  # SHA256

    # 关联信息
    test_context: TestContext

    # 时间戳
    captured_at: datetime = Field(default_factory=datetime.now)

    # 额外元数据
    metadata: dict[str, Any] = Field(default_factory=dict)


class DiagnosisResult(BaseModel):
    """诊断结果

    包含所有采集的资源、执行统计、错误信息
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # 测试上下文
    test_context: TestContext

    # 采集的资源
    artifacts: list[DiagnosisArtifact] = Field(default_factory=list)

    # 执行统计
    total_strategies: int = 0
    successful_strategies: int = 0
    failed_strategies: int = 0
    execution_time_ms: float = 0.0

    # 错误信息
    errors: list[str] = Field(default_factory=list)

    # 完成时间
    completed_at: datetime = Field(default_factory=datetime.now)
```

### 5.2 策略接口协议

#### 5.2.1 协议定义

```python
"""
src/df_test_framework/testing/diagnosis/protocols.py
失败诊断策略协议定义
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable, Any

from df_test_framework.testing.diagnosis.models import (
    DiagnosisArtifact,
    DiagnosisResult,
    TestContext,
)


@runtime_checkable
class DiagnosisStrategy(Protocol):
    """诊断策略协议

    所有诊断策略必须实现此协议
    支持生命周期管理：setup -> execute -> cleanup
    """

    @property
    def name(self) -> str:
        """策略名称"""
        ...

    @property
    def enabled(self) -> bool:
        """是否启用"""
        ...

    @property
    def priority(self) -> int:
        """优先级（数字越小优先级越高，用于排序）"""
        ...

    async def setup(self, test_context: TestContext) -> None:
        """初始化策略

        Args:
            test_context: 测试上下文
        """
        ...

    async def execute(
        self,
        test_context: TestContext,
        result: DiagnosisResult,
    ) -> list[DiagnosisArtifact]:
        """执行策略，返回采集的资源

        Args:
            test_context: 测试上下文
            result: 当前诊断结果（可读取前序策略产生的资源）

        Returns:
            采集的诊断资源列表
        """
        ...

    async def cleanup(self) -> None:
        """清理资源"""
        ...


@runtime_checkable
class CaptureStrategy(DiagnosisStrategy, Protocol):
    """资源采集策略

    负责采集失败诊断资源（截图、视频、日志等）
    Priority 范围: 1-99
    """
    pass


@runtime_checkable
class ProcessStrategy(DiagnosisStrategy, Protocol):
    """资源处理策略

    负责处理已采集的资源（压缩、上传、清理、加密等）
    Priority 范围: 100-199
    """
    pass


@runtime_checkable
class ReportStrategy(DiagnosisStrategy, Protocol):
    """报告附加策略

    负责将诊断结果附加到报告系统（Allure、Slack、Jira 等）
    Priority 范围: 200-299
    """
    pass


@runtime_checkable
class ArtifactStorage(Protocol):
    """资源存储协议

    统一的存储抽象，支持本地文件系统、S3、OSS 等
    """

    async def save(
        self,
        content: bytes,
        filename: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """保存资源

        Args:
            content: 资源内容
            filename: 文件名
            metadata: 额外元数据

        Returns:
            资源 URL 或路径
        """
        ...

    async def delete(self, url: str) -> None:
        """删除资源"""
        ...

    async def exists(self, url: str) -> bool:
        """检查资源是否存在"""
        ...
```

### 5.3 诊断协调器

#### 5.3.1 协调器实现

```python
"""
src/df_test_framework/testing/diagnosis/coordinator.py
失败诊断协调器
"""

from __future__ import annotations

import asyncio
import time
from typing import Sequence

from df_test_framework.core.logging import get_logger
from df_test_framework.testing.diagnosis.models import (
    DiagnosisResult,
    TestContext,
)
from df_test_framework.testing.diagnosis.protocols import DiagnosisStrategy

logger = get_logger(__name__)


class DiagnosisCoordinator:
    """失败诊断协调器

    负责：
    1. 管理策略生命周期（setup -> execute -> cleanup）
    2. 编排策略执行顺序（按 priority 排序）
    3. 支持并行执行策略（capture 并行，process/report 串行）
    4. 异常隔离（单个策略失败不影响其他策略）
    5. 结构化日志和指标收集
    """

    def __init__(
        self,
        strategies: Sequence[DiagnosisStrategy],
        parallel_execution: bool = True,
        timeout_seconds: float = 30.0,
    ):
        """初始化协调器

        Args:
            strategies: 诊断策略列表
            parallel_execution: 是否并行执行策略
            timeout_seconds: 总超时时间
        """
        # 按 priority 排序策略（数字越小优先级越高）
        self._strategies = sorted(
            [s for s in strategies if s.enabled],
            key=lambda s: s.priority,
        )
        self._parallel_execution = parallel_execution
        self._timeout_seconds = timeout_seconds

    async def diagnose(self, test_context: TestContext) -> DiagnosisResult:
        """执行失败诊断

        Args:
            test_context: 测试上下文

        Returns:
            诊断结果
        """
        start_time = time.perf_counter()
        result = DiagnosisResult(test_context=test_context)

        logger.info(
            "开始执行失败诊断",
            extra={
                "test_id": test_context.test_id,
                "test_name": test_context.test_name,
                "strategies_count": len(self._strategies),
                "parallel_execution": self._parallel_execution,
            },
        )

        try:
            # 1. Setup 阶段（串行）
            await self._setup_strategies(test_context, result)

            # 2. Execute 阶段（可并行）
            if self._parallel_execution:
                await self._execute_strategies_parallel(test_context, result)
            else:
                await self._execute_strategies_sequential(test_context, result)

            # 3. Cleanup 阶段（串行）
            await self._cleanup_strategies(result)

        except asyncio.TimeoutError:
            error_msg = f"诊断超时（{self._timeout_seconds}s）"
            logger.error(error_msg, extra={"test_id": test_context.test_id})
            result.errors.append(error_msg)
        except Exception as e:
            error_msg = f"诊断异常: {e}"
            logger.exception(error_msg, extra={"test_id": test_context.test_id})
            result.errors.append(error_msg)
        finally:
            # 统计信息
            result.total_strategies = len(self._strategies)
            result.execution_time_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                "完成失败诊断",
                extra={
                    "test_id": test_context.test_id,
                    "artifacts_count": len(result.artifacts),
                    "successful_strategies": result.successful_strategies,
                    "failed_strategies": result.failed_strategies,
                    "execution_time_ms": result.execution_time_ms,
                },
            )

        return result

    async def _setup_strategies(
        self,
        test_context: TestContext,
        result: DiagnosisResult,
    ) -> None:
        """初始化所有策略（串行）"""
        for strategy in self._strategies:
            try:
                await strategy.setup(test_context)
                logger.debug(
                    f"策略初始化成功: {strategy.name}",
                    extra={"strategy": strategy.name},
                )
            except Exception as e:
                error_msg = f"策略初始化失败 [{strategy.name}]: {e}"
                logger.warning(error_msg, exc_info=True)
                result.errors.append(error_msg)
                result.failed_strategies += 1

    async def _execute_strategies_parallel(
        self,
        test_context: TestContext,
        result: DiagnosisResult,
    ) -> None:
        """并行执行所有策略"""
        tasks = [
            self._execute_single_strategy(strategy, test_context, result)
            for strategy in self._strategies
        ]

        # 使用 asyncio.gather 并行执行，return_exceptions=True 隔离异常
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_strategies_sequential(
        self,
        test_context: TestContext,
        result: DiagnosisResult,
    ) -> None:
        """串行执行所有策略"""
        for strategy in self._strategies:
            await self._execute_single_strategy(strategy, test_context, result)

    async def _execute_single_strategy(
        self,
        strategy: DiagnosisStrategy,
        test_context: TestContext,
        result: DiagnosisResult,
    ) -> None:
        """执行单个策略（异常隔离）"""
        try:
            start_time = time.perf_counter()

            artifacts = await strategy.execute(test_context, result)

            execution_time = (time.perf_counter() - start_time) * 1000

            # 更新结果
            result.artifacts.extend(artifacts)
            result.successful_strategies += 1

            logger.debug(
                f"策略执行成功: {strategy.name}",
                extra={
                    "strategy": strategy.name,
                    "artifacts_count": len(artifacts),
                    "execution_time_ms": execution_time,
                },
            )

        except Exception as e:
            error_msg = f"策略执行失败 [{strategy.name}]: {e}"
            logger.warning(error_msg, exc_info=True)
            result.errors.append(error_msg)
            result.failed_strategies += 1

    async def _cleanup_strategies(self, result: DiagnosisResult) -> None:
        """清理所有策略（串行，逆序）"""
        for strategy in reversed(self._strategies):
            try:
                await strategy.cleanup()
                logger.debug(
                    f"策略清理成功: {strategy.name}",
                    extra={"strategy": strategy.name},
                )
            except Exception as e:
                error_msg = f"策略清理失败 [{strategy.name}]: {e}"
                logger.warning(error_msg, exc_info=True)
                result.errors.append(error_msg)
```

### 5.4 策略实现示例

#### 5.4.1 截图采集策略

```python
"""
src/df_test_framework/testing/diagnosis/strategies/capture/screenshot.py
截图采集策略
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

from playwright.async_api import Page

from df_test_framework.testing.diagnosis.models import (
    DiagnosisArtifact,
    DiagnosisResult,
    DiagnosisType,
    TestContext,
)


class ScreenshotCaptureStrategy:
    """截图采集策略

    配置项：
    - full_page: 是否全页截图
    - format: 截图格式（png/jpeg）
    - quality: 图片质量（仅 JPEG）
    """

    def __init__(
        self,
        page: Page | None = None,
        full_page: bool = True,
        format: str = "png",
        quality: int | None = None,
        output_dir: Path | None = None,
        enabled: bool = True,
        priority: int = 10,
    ):
        self._page = page
        self._full_page = full_page
        self._format = format
        self._quality = quality
        self._output_dir = output_dir or Path("reports/diagnosis/screenshots")
        self._enabled = enabled
        self._priority = priority

    @property
    def name(self) -> str:
        return "screenshot_capture"

    @property
    def enabled(self) -> bool:
        return self._enabled and self._page is not None

    @property
    def priority(self) -> int:
        return self._priority

    async def setup(self, test_context: TestContext) -> None:
        """创建输出目录"""
        self._output_dir.mkdir(parents=True, exist_ok=True)

    async def execute(
        self,
        test_context: TestContext,
        result: DiagnosisResult,
    ) -> list[DiagnosisArtifact]:
        """执行截图"""
        if not self._page:
            return []

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{test_context.test_function}_{timestamp}.{self._format}"
        file_path = self._output_dir / filename

        # 执行截图
        screenshot_bytes = await self._page.screenshot(
            path=str(file_path),
            full_page=self._full_page,
            type=self._format,
            quality=self._quality,
        )

        # 计算校验和
        checksum = hashlib.sha256(screenshot_bytes).hexdigest()

        # 创建资源对象
        artifact = DiagnosisArtifact(
            artifact_type=DiagnosisType.SCREENSHOT,
            name=f"Screenshot - {test_context.test_function}",
            description=f"Full page: {self._full_page}, Format: {self._format}",
            file_path=file_path,
            mime_type=f"image/{self._format}",
            size_bytes=len(screenshot_bytes),
            checksum=checksum,
            test_context=test_context,
            metadata={
                "full_page": self._full_page,
                "format": self._format,
                "url": test_context.url,
            },
        )

        return [artifact]

    async def cleanup(self) -> None:
        """清理资源"""
        pass
```

#### 5.4.2 Allure 报告策略

```python
"""
src/df_test_framework/testing/diagnosis/strategies/report/allure.py
Allure 报告策略
"""

from __future__ import annotations

import json

import allure

from df_test_framework.testing.diagnosis.models import (
    DiagnosisArtifact,
    DiagnosisResult,
    DiagnosisType,
    TestContext,
)


class AllureReportStrategy:
    """Allure 报告策略

    将诊断资源附加到 Allure 报告
    """

    # 资源类型到 Allure 附件类型的映射
    _TYPE_MAPPING = {
        DiagnosisType.SCREENSHOT: allure.attachment_type.PNG,
        DiagnosisType.VIDEO: allure.attachment_type.WEBM,
        DiagnosisType.HTML_SNAPSHOT: allure.attachment_type.HTML,
        DiagnosisType.CONSOLE_LOG: allure.attachment_type.TEXT,
        DiagnosisType.NETWORK_HAR: allure.attachment_type.JSON,
        DiagnosisType.TRACE: allure.attachment_type.JSON,
    }

    def __init__(
        self,
        enabled: bool = True,
        priority: int = 200,
    ):
        self._enabled = enabled
        self._priority = priority

    @property
    def name(self) -> str:
        return "allure_report"

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def priority(self) -> int:
        return self._priority

    async def setup(self, test_context: TestContext) -> None:
        """初始化"""
        pass

    async def execute(
        self,
        test_context: TestContext,
        result: DiagnosisResult,
    ) -> list[DiagnosisArtifact]:
        """附加资源到 Allure"""

        # 1. 附加测试上下文摘要
        context_summary = {
            "test_id": test_context.test_id,
            "test_name": test_context.test_name,
            "failure_reason": test_context.failure_reason.value,
            "exception_message": test_context.exception_message,
            "url": test_context.url,
            "browser": test_context.browser_type,
            "failed_at": test_context.failed_at.isoformat(),
        }

        allure.attach(
            json.dumps(context_summary, indent=2, ensure_ascii=False),
            name="🔍 Test Failure Context",
            attachment_type=allure.attachment_type.JSON,
        )

        # 2. 附加每个诊断资源
        for artifact in result.artifacts:
            await self._attach_artifact(artifact)

        # 3. 附加诊断统计
        diagnosis_stats = {
            "total_artifacts": len(result.artifacts),
            "total_strategies": result.total_strategies,
            "successful_strategies": result.successful_strategies,
            "failed_strategies": result.failed_strategies,
            "execution_time_ms": result.execution_time_ms,
            "errors": result.errors,
        }

        allure.attach(
            json.dumps(diagnosis_stats, indent=2, ensure_ascii=False),
            name="📊 Diagnosis Statistics",
            attachment_type=allure.attachment_type.JSON,
        )

        return []  # 报告策略不产生新资源

    async def _attach_artifact(self, artifact: DiagnosisArtifact) -> None:
        """附加单个资源到 Allure"""

        # 确定附件类型
        attachment_type = self._TYPE_MAPPING.get(
            artifact.artifact_type,
            allure.attachment_type.TEXT,
        )

        # 资源图标
        icons = {
            DiagnosisType.SCREENSHOT: "📸",
            DiagnosisType.VIDEO: "🎥",
            DiagnosisType.HTML_SNAPSHOT: "📄",
            DiagnosisType.CONSOLE_LOG: "📝",
            DiagnosisType.NETWORK_HAR: "🌐",
            DiagnosisType.TRACE: "🔍",
        }
        icon = icons.get(artifact.artifact_type, "📎")

        # 附加资源
        if artifact.file_path and artifact.file_path.exists():
            # 从本地文件读取
            content = artifact.file_path.read_bytes()
            allure.attach(
                content,
                name=f"{icon} {artifact.name}",
                attachment_type=attachment_type,
            )
        elif artifact.remote_url:
            # 附加远程 URL（仅元数据）
            metadata = {
                "artifact_id": artifact.artifact_id,
                "remote_url": artifact.remote_url,
                "size_bytes": artifact.size_bytes,
                "mime_type": artifact.mime_type,
                "captured_at": artifact.captured_at.isoformat(),
                **artifact.metadata,
            }
            allure.attach(
                json.dumps(metadata, indent=2, ensure_ascii=False),
                name=f"{icon} {artifact.name} (Remote)",
                attachment_type=allure.attachment_type.JSON,
            )

    async def cleanup(self) -> None:
        """清理资源"""
        pass
```

---

## 6. 配置系统

### 6.1 配置 Schema

```python
"""
src/df_test_framework/infrastructure/config/schema.py
失败诊断配置 Schema
"""

from pydantic import BaseModel, Field


class DiagnosisConfig(BaseModel):
    """失败诊断配置

    环境变量前缀: DIAGNOSIS__
    """

    # 全局开关
    enabled: bool = Field(default=True, description="是否启用失败诊断")
    parallel_execution: bool = Field(default=True, description="是否并行执行策略")
    timeout_seconds: float = Field(default=30.0, description="诊断总超时时间（秒）")

    # Capture 策略配置
    capture_screenshot: bool = Field(default=True, description="是否采集截图")
    screenshot_full_page: bool = Field(default=True, description="是否全页截图")
    screenshot_format: str = Field(default="png", description="截图格式（png/jpeg）")
    screenshot_quality: int | None = Field(default=None, description="JPEG 质量（0-100）")

    capture_video: bool = Field(default=True, description="是否采集视频")
    video_record_mode: str = Field(
        default="on-failure",
        description="视频录制模式（always/on-failure/disabled）",
    )
    video_size: dict[str, int] | None = Field(
        default=None,
        description="视频尺寸 {width, height}",
    )

    capture_console_log: bool = Field(default=True, description="是否采集控制台日志")
    capture_network_har: bool = Field(default=False, description="是否采集网络 HAR")
    capture_trace: bool = Field(default=False, description="是否采集 Playwright Trace")

    # Process 策略配置
    enable_compression: bool = Field(default=False, description="是否压缩资源")
    compression_format: str = Field(default="gzip", description="压缩格式（gzip/bz2/lzma）")

    enable_oss_upload: bool = Field(default=False, description="是否上传到 OSS")
    oss_bucket: str = Field(default="", description="OSS Bucket 名称")
    oss_prefix: str = Field(default="test-diagnosis", description="OSS 对象键前缀")
    oss_delete_local: bool = Field(default=True, description="上传后是否删除本地文件")

    # Report 策略配置
    enable_allure_report: bool = Field(default=True, description="是否附加到 Allure")
    enable_slack_notification: bool = Field(default=False, description="是否发送 Slack 通知")
    slack_webhook_url: str = Field(default="", description="Slack Webhook URL")

    # 资源保留策略
    retention_days: int = Field(default=7, description="本地资源保留天数")
    auto_cleanup: bool = Field(default=True, description="是否自动清理过期资源")
```

### 6.2 YAML 配置示例

```yaml
# config/base.yaml

# 失败诊断配置
diagnosis:
  enabled: true
  parallel_execution: true
  timeout_seconds: 30.0

  # 采集配置
  capture_screenshot: true
  screenshot_full_page: true
  screenshot_format: png

  capture_video: true
  video_record_mode: on-failure  # always / on-failure / disabled
  video_size:
    width: 1024
    height: 768

  capture_console_log: true
  capture_network_har: false  # HAR 文件较大，默认关闭
  capture_trace: false         # Trace 文件巨大，仅调试时开启

  # 处理配置
  enable_compression: false

  enable_oss_upload: false
  oss_bucket: my-test-diagnosis-bucket
  oss_prefix: test-diagnosis
  oss_delete_local: true

  # 报告配置
  enable_allure_report: true
  enable_slack_notification: false
  slack_webhook_url: ""

  # 清理配置
  retention_days: 7
  auto_cleanup: true
```

---

## 7. Pytest 集成

### 7.1 Fixture 实现

```python
"""
src/df_test_framework/testing/fixtures/diagnosis.py
失败诊断 Pytest Fixtures
"""

from __future__ import annotations

import asyncio
from typing import Generator

import pytest
from playwright.async_api import Page

from df_test_framework.infrastructure.runtime import TestRuntime
from df_test_framework.testing.diagnosis.coordinator import DiagnosisCoordinator
from df_test_framework.testing.diagnosis.models import (
    FailureReason,
    TestContext,
)
from df_test_framework.testing.diagnosis.strategies.capture.screenshot import (
    ScreenshotCaptureStrategy,
)
from df_test_framework.testing.diagnosis.strategies.report.allure import (
    AllureReportStrategy,
)


@pytest.fixture(scope="function")
def diagnosis_coordinator(
    test_runtime: TestRuntime,
    page: Page | None = None,
) -> DiagnosisCoordinator:
    """失败诊断协调器 fixture

    自动配置诊断策略
    """
    config = test_runtime.config.diagnosis

    # 构建策略链
    strategies = []

    # Capture 策略
    if config.capture_screenshot:
        strategies.append(
            ScreenshotCaptureStrategy(
                page=page,
                full_page=config.screenshot_full_page,
                format=config.screenshot_format,
                priority=10,
            )
        )

    # Report 策略
    if config.enable_allure_report:
        strategies.append(
            AllureReportStrategy(priority=200)
        )

    return DiagnosisCoordinator(
        strategies=strategies,
        parallel_execution=config.parallel_execution,
        timeout_seconds=config.timeout_seconds,
    )


@pytest.fixture(scope="function", autouse=True)
def _auto_diagnosis(
    request: pytest.FixtureRequest,
    diagnosis_coordinator: DiagnosisCoordinator,
) -> Generator[None, None, None]:
    """自动失败诊断 fixture（零配置）"""
    yield

    # 检查测试是否失败
    if not _is_test_failed(request):
        return

    # 构建测试上下文
    test_context = _build_test_context(request)

    # 执行诊断
    loop = asyncio.get_event_loop()
    diagnosis_result = loop.run_until_complete(
        diagnosis_coordinator.diagnose(test_context)
    )

    # 附加到 request.node
    request.node.diagnosis_result = diagnosis_result


def _is_test_failed(request: pytest.FixtureRequest) -> bool:
    """检查测试是否失败"""
    try:
        return request.node.rep_call.failed if hasattr(request.node, "rep_call") else False
    except Exception:
        return False


def _build_test_context(request: pytest.FixtureRequest) -> TestContext:
    """构建测试上下文"""
    from datetime import datetime

    # ... 实现省略
    pass
```

### 7.2 使用示例

#### 7.2.1 零配置使用

```python
"""
tests/test_login.py
测试失败时自动诊断（零配置）
"""

import pytest
from playwright.async_api import Page


def test_login_success(page: Page):
    """登录成功测试"""
    page.goto("https://practice.expandtesting.com/login")

    page.fill("#username", "practice")
    page.fill("#password", "SuperSecretPassword!")
    page.click("button[type='submit']")

    # 断言失败 -> 自动触发诊断
    assert "Logout" in page.content()


# 无需任何额外代码，失败时会自动：
# 1. 截图（全页）
# 2. 保存视频（如果录制了）
# 3. 采集控制台日志
# 4. 附加到 Allure 报告
```

#### 7.2.2 自定义策略

```python
"""
tests/conftest.py
自定义失败诊断策略
"""

import pytest
from df_test_framework.testing.diagnosis.coordinator import DiagnosisCoordinator


class SlackNotificationStrategy:
    """自定义 Slack 通知策略"""

    def __init__(self, webhook_url: str):
        self._webhook_url = webhook_url

    @property
    def name(self) -> str:
        return "slack_notification"

    @property
    def enabled(self) -> bool:
        return bool(self._webhook_url)

    @property
    def priority(self) -> int:
        return 300

    async def setup(self, test_context):
        pass

    async def execute(self, test_context, result):
        import httpx

        message = {
            "text": f"🚨 Test Failed: {test_context.test_name}",
        }

        async with httpx.AsyncClient() as client:
            await client.post(self._webhook_url, json=message)

        return []

    async def cleanup(self):
        pass


@pytest.fixture(scope="function")
def diagnosis_coordinator(page):
    """自定义诊断协调器"""
    from df_test_framework.testing.diagnosis.strategies.capture.screenshot import (
        ScreenshotCaptureStrategy,
    )

    strategies = [
        ScreenshotCaptureStrategy(page=page, priority=10),
        SlackNotificationStrategy(
            webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK",
        ),
    ]

    return DiagnosisCoordinator(strategies=strategies)
```

---

## 8. 实施路径

### 8.1 阶段划分

#### Phase 1: 核心基础设施（2 周）

**目标**：实现核心架构和基础组件

**交付物**：
- ✅ 数据模型（`models.py`）
- ✅ 协议接口（`protocols.py`）
- ✅ 诊断协调器（`coordinator.py`）
- ✅ 单元测试（覆盖率 ≥ 80%）

**验收标准**：
- mypy 类型检查通过
- 所有单元测试通过
- 文档完整

#### Phase 2: 基础策略实现（1-2 周）

**目标**：实现基本的采集和报告策略

**交付物**：
- ✅ Screenshot 策略
- ✅ Video 策略
- ✅ Allure Report 策略
- ✅ 集成测试

**验收标准**：
- 策略独立工作正常
- 策略链协同工作正常
- 性能测试通过（诊断时间 < 5 秒）

#### Phase 3: 高级策略扩展（1 周）

**目标**：实现高级处理策略

**交付物**：
- ✅ OSS Upload 策略
- ✅ Compression 策略
- ✅ Cleanup 策略
- ✅ Slack/Jira 通知策略

**验收标准**：
- 所有策略正常工作
- 异常隔离测试通过
- 性能无明显下降

#### Phase 4: Pytest 集成与文档（1 周）

**目标**：完成 pytest 集成和文档

**交付物**：
- ✅ Pytest fixtures
- ✅ 配置系统
- ✅ 使用文档
- ✅ 迁移指南

**验收标准**：
- 零配置自动生效
- 向后兼容
- 文档完整

### 8.2 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| **异步集成问题** | 中 | 高 | 早期 PoC 验证 asyncio 集成 |
| **性能回归** | 低 | 中 | 性能测试，支持并行执行 |
| **向后兼容性破坏** | 低 | 高 | 提供兼容层，渐进式迁移 |
| **用户学习成本** | 中 | 中 | 保持零配置体验，文档完善 |

### 8.3 实施检查清单

#### Phase 1: 核心基础设施
- [ ] 实现 `testing/diagnosis/models.py`
  - [ ] `TestContext` 模型
  - [ ] `DiagnosisArtifact` 模型
  - [ ] `DiagnosisResult` 模型
  - [ ] 单元测试
- [ ] 实现 `testing/diagnosis/protocols.py`
  - [ ] `DiagnosisStrategy` 协议
  - [ ] `CaptureStrategy` 协议
  - [ ] `ProcessStrategy` 协议
  - [ ] `ReportStrategy` 协议
  - [ ] `ArtifactStorage` 协议
- [ ] 实现 `testing/diagnosis/coordinator.py`
  - [ ] `DiagnosisCoordinator` 类
  - [ ] setup/execute/cleanup 流程
  - [ ] 异常隔离
  - [ ] 单元测试
- [ ] 文档
  - [ ] API 文档
  - [ ] 架构说明

#### Phase 2: 基础策略实现
- [ ] 实现 `strategies/capture/screenshot.py`
  - [ ] `ScreenshotCaptureStrategy` 类
  - [ ] 单元测试
- [ ] 实现 `strategies/capture/video.py`
  - [ ] `VideoCaptureStrategy` 类
  - [ ] 单元测试
- [ ] 实现 `strategies/report/allure.py`
  - [ ] `AllureReportStrategy` 类
  - [ ] 单元测试
- [ ] 集成测试
  - [ ] 策略链测试
  - [ ] 端到端测试

#### Phase 3: 高级策略扩展
- [ ] 实现 `strategies/process/oss_upload.py`
  - [ ] `OSSUploadStrategy` 类
  - [ ] 单元测试
- [ ] 实现 `strategies/process/compress.py`
  - [ ] `CompressionStrategy` 类
  - [ ] 单元测试
- [ ] 实现 `strategies/process/cleanup.py`
  - [ ] `CleanupStrategy` 类
  - [ ] 单元测试
- [ ] 实现通知策略
  - [ ] `SlackNotificationStrategy`
  - [ ] `JiraNotificationStrategy`
  - [ ] 单元测试

#### Phase 4: Pytest 集成与文档
- [ ] 实现 `testing/fixtures/diagnosis.py`
  - [ ] `diagnosis_coordinator` fixture
  - [ ] `_auto_diagnosis` fixture
  - [ ] 集成测试
- [ ] 实现配置系统
  - [ ] `DiagnosisConfig` Schema
  - [ ] YAML 配置示例
- [ ] 文档
  - [ ] 使用指南
  - [ ] 配置说明
  - [ ] 自定义策略教程
  - [ ] 迁移指南

---

## 9. 对比分析

### 9.1 架构对比

| 维度 | 现有实现 | v2.0 设计 |
|------|---------|-----------|
| **架构模式** | EventBus + autouse fixture | 策略模式 + 责任链 + 协调器 |
| **扩展性** | 中等（需修改 Observer） | 高（插件式策略，无需修改核心） |
| **类型安全** | 部分（事件缺乏强类型约束） | 强（Protocol + Pydantic + 泛型） |
| **并发执行** | 串行 | 支持并行策略执行 |
| **失败隔离** | 有限（单个事件处理器异常会影响后续） | 完全隔离（每个策略独立异常处理） |
| **生命周期** | 隐式（通过 fixture） | 显式（setup/execute/cleanup） |
| **配置灵活性** | 固定模式（retain-on-failure 等） | 完全可配置的策略链 |
| **资源存储** | 仅本地文件系统 | 抽象存储接口（本地/S3/OSS） |
| **报告系统** | 仅 Allure | 多报告器（Allure/Slack/Jira/自定义） |
| **可观测性** | 基础日志 | 结构化日志 + 指标 + 追踪 |

### 9.2 优势总结

#### v2.0 核心优势

1. **✅ 可插拔策略系统**
   - 每个策略独立开发、测试、部署
   - 无需修改核心代码即可扩展功能
   - 支持优先级控制和条件启用

2. **✅ 强类型约束**
   - Protocol 定义清晰的接口契约
   - Pydantic 模型提供运行时验证
   - IDE 友好，完整的类型提示

3. **✅ 异步并发执行**
   - 策略可并行执行，提升性能
   - 支持超时控制，防止阻塞
   - 异步 I/O，不阻塞测试进程

4. **✅ 完整的生命周期管理**
   - setup：初始化资源
   - execute：执行策略逻辑
   - cleanup：释放资源（即使异常也会执行）

5. **✅ 异常隔离与容错**
   - 单个策略失败不影响其他策略
   - 详细的错误日志和诊断统计
   - 优雅降级，确保测试不被诊断逻辑破坏

6. **✅ 统一资源模型**
   - DiagnosisArtifact 统一抽象所有诊断资源
   - 支持元数据、校验和、远程 URL
   - 便于后续处理和归档

### 9.3 向后兼容性

v2.0 设计保持向后兼容：

| 功能 | 现有实现 | v2.0 实现 | 兼容性 |
|------|---------|-----------|--------|
| **零配置自动化** | ✅ autouse fixture | ✅ autouse fixture | ✅ 完全兼容 |
| **视频录制** | ✅ Playwright 原生 | ✅ VideoCaptureStrategy | ✅ 功能增强 |
| **截图** | ✅ screenshot fixture | ✅ ScreenshotCaptureStrategy | ✅ 功能增强 |
| **Allure 报告** | ✅ AllureObserver | ✅ AllureReportStrategy | ✅ 功能增强 |
| **EventBus** | ✅ 实时事件监听 | ✅ 保留不变 | ✅ 完全兼容 |

**迁移策略**：
- ✅ 保留现有 fixtures，作为兼容层
- ✅ 新项目使用 v2.0 API
- ✅ 旧项目可选择性迁移

---

## 10. 参考资料

### 10.1 相关文档

- **V3_ARCHITECTURE.md** - v3 架构设计方案
- **FUTURE_ENHANCEMENTS.md** - 未来增强功能规划
- **web-ui-testing.md** - Web UI 测试指南

### 10.2 设计模式参考

- **Strategy Pattern** - Design Patterns: Elements of Reusable Object-Oriented Software
- **Chain of Responsibility** - Design Patterns: Elements of Reusable Object-Oriented Software
- **Template Method** - Design Patterns: Elements of Reusable Object-Oriented Software

### 10.3 技术栈参考

- **Playwright** - https://playwright.dev/
- **Pydantic** - https://docs.pydantic.dev/
- **Python asyncio** - https://docs.python.org/3/library/asyncio.html
- **pytest** - https://docs.pytest.org/
- **Allure** - https://docs.qameta.io/allure/

---

## ✅ 结论

### 核心价值主张

Web 测试失败诊断系统 v2.0 通过 **策略模式 + 协调器 + 强类型约束**，将失败诊断从固化的流程转变为可组合的策略系统，实现：

- ✅ **高扩展性** - 无需修改核心代码即可添加新策略
- ✅ **高性能** - 支持并行执行和异步 I/O
- ✅ **高可靠** - 异常隔离和优雅降级
- ✅ **高可维护** - 清晰的接口契约和生命周期管理

### 实施建议

- **优先级**: P2（未来增强，非紧急）
- **实施时间**: 4-6 周
- **依赖条件**: 无重大依赖，可独立实施
- **风险评估**: 低风险，向后兼容

### 下一步行动

1. ✅ **评审设计方案** - 团队讨论和反馈
2. ✅ **创建实施计划** - 详细的任务分解
3. ✅ **PoC 验证** - 实现核心组件的原型
4. ✅ **正式开发** - 按阶段逐步实施

---

**文档创建日期**: 2026-01-15
**作者**: Claude Code
**审核状态**: 待审核
**优先级**: P2（未来增强）
**状态**: 设计阶段