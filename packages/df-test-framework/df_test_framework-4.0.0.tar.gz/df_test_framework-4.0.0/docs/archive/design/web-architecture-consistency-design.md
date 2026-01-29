# Web UI 测试架构一致性设计方案

> **版本**: v3.44.0 (建议)
> **日期**: 2026-01-08
> **目标**: 让 Web 与 HTTP 保持完全一致的架构设计
> **实现说明**: v3.44.0 最终实现采用 `WebBrowserEvent`（page.load/network.* 等）+ `UIErrorEvent`，通过 page fixture 自动注册监听器。下文中出现的 `UINavigation*`/`UIClick*`/`UIInput*` 事件描述属于早期方案（保留作为可选扩展），与当前实现的核心差异仅在事件命名。

---

## 目录

- [现状分析](#现状分析)
- [HTTP 架构回顾](#http-架构回顾)
- [Web 架构问题](#web-架构问题)
- [一致性设计方案](#一致性设计方案)
- [实施路线](#实施路线)

---

## 现状分析

### HTTP 客户端 - 完整的架构集成 ✅

```python
# ========== 配置驱动 ==========
settings = FrameworkSettings(
    http=HTTPConfig(
        base_url="https://api.example.com",
        timeout=30,
        middlewares=[...],
    )
)

# ========== Provider 单例 ==========
client = runtime.http_client()  # ✅ 从 Provider 获取，已配置好

# ========== 事件发布 ==========
# HttpEventPublisherMiddleware 自动发布事件：
# - HttpRequestStartEvent
# - HttpRequestEndEvent
# - HttpRequestErrorEvent

# ========== 日志集成 ==========
# get_logger(__name__) 记录调试信息

# ========== Allure 集成 ==========
# AllureObserver 订阅事件，自动记录到 Allure 报告

# ========== 可观测性 ==========
# - EventBus: 事件发布/订阅
# - OpenTelemetry: trace_id/span_id
# - Logging: structlog 结构化日志
# - Allure: 可视化报告
```

### Web 驱动 - 架构不一致 ⚠️

```python
# ========== 配置驱动 ==========
settings = FrameworkSettings(
    web=WebConfig(
        base_url="http://localhost:3000",
        browser_type="chromium",
    )
)

# ========== Provider 单例 ==========
browser_manager = runtime.browser_manager()  # ✅ 有 Provider
page = browser_manager.browser.new_page()

# ========== 问题：Page Object 无法自动获取配置 ==========
login_page = LoginPage(
    page,
    base_url=runtime.settings.web.base_url  # ⚠️ 需要手动传
)

# ========== 问题：无事件发布 ==========
# BasePage (v3.43.0) 移除了过度封装，也移除了事件发布 ❌
# 虽然有 UI 事件定义（v3.35.7），但没有发布

# ========== 问题：无 Allure 自动集成 ==========
# AllureObserver 有 UI 事件处理方法，但没有事件源 ❌

# ========== 可观测性缺失 ==========
# - EventBus: ❌ 无事件发布
# - OpenTelemetry: ❌ 无 trace_id/span_id
# - Logging: ⚠️ 部分日志
# - Allure: ❌ 无自动记录
```

---

## HTTP 架构回顾

### HTTP 的完整数据流

```
┌─────────────────────────────────────────────────────────────┐
│             HTTP 客户端完整架构（v3.23.0）                    │
└─────────────────────────────────────────────────────────────┘

1. 配置加载
   FrameworkSettings
   └─ http: HTTPConfig
      ├─ base_url
      ├─ timeout
      └─ middlewares: [SignatureMiddleware, BearerTokenMiddleware]

2. Provider 创建
   runtime.http_client()
   └─ http_factory(context)
      └─ HttpClient(
           base_url=context.settings.http.base_url,  # ✅ 自动读取
           config=context.settings.http,              # ✅ 传递完整配置
           event_bus=event_bus,                       # ✅ 注入 EventBus
         )

3. 请求执行
   client.get("/users")
   └─ MiddlewareChain
      ├─ RetryMiddleware
      ├─ SignatureMiddleware
      ├─ BearerTokenMiddleware
      └─ HttpEventPublisherMiddleware  # ✅ 自动发布事件
         ├─ HttpRequestStartEvent (correlation_id: abc123)
         ├─ _send_request_async()
         └─ HttpRequestEndEvent (correlation_id: abc123)

4. 事件订阅
   EventBus
   └─ AllureObserver
      └─ handle_http_request_start_event()
         └─ allure.step("🌐 GET /users")
            └─ allure.attach("Request Details", ...)

5. 可观测性
   - EventBus: 发布/订阅事件
   - Logger: get_logger(__name__).debug("HTTP客户端已初始化")
   - OpenTelemetry: trace_id/span_id 自动注入
   - Allure: 自动记录到报告
```

### HTTP 架构的关键设计

| 特性 | 实现方式 | 代码位置 |
|------|---------|---------|
| **配置驱动** | HTTPConfig + Provider | `bootstrap/providers.py:http_factory()` |
| **事件发布** | HttpEventPublisherMiddleware | `http/middleware/event_publisher.py` |
| **日志记录** | `get_logger(__name__)` | `http/rest/httpx/client.py` |
| **Allure 集成** | AllureObserver 订阅事件 | `testing/reporting/allure/observer.py` |
| **可观测性** | EventBus + OpenTelemetry | `core/events/` + `infrastructure/telemetry/` |

---

## Web 架构问题

### 问题 1: 配置传递不自动化 ⚠️

```python
# ❌ 当前方式 - 手动传递
login_page = LoginPage(page, base_url=runtime.settings.web.base_url)
app_actions = AppActions(page, base_url=runtime.settings.web.base_url)

# ✅ 期望方式 - 自动获取（与 HTTP 一致）
login_page = LoginPage(page, runtime=runtime)  # base_url 自动从配置读取
app_actions = AppActions(page, runtime=runtime)
```

### 问题 2: 事件系统未启用 ❌

```python
# ✅ 框架已有 UI 事件定义（v3.35.7）
UINavigationStartEvent
UINavigationEndEvent
UIClickEvent
UIInputEvent
UIScreenshotEvent
UIWaitEvent
UIErrorEvent

# ✅ AllureObserver 已有事件处理方法
AllureObserver.handle_ui_navigation_start_event()
AllureObserver.handle_ui_navigation_end_event()
AllureObserver.handle_ui_click_event()
# ...

# ❌ 但是 BasePage (v3.43.0) 没有发布事件！
# 原因：v3.43.0 移除过度封装时，也移除了事件发布代码
```

### 问题 3: Allure 集成断裂 ❌

```python
# ❌ 当前状态
def test_login(page):
    login_page = LoginPage(page)
    login_page.goto()                      # ❌ 无事件，Allure 无记录
    page.get_by_label("Username").fill()   # ❌ 无事件，Allure 无记录
    page.get_by_role("button").click()     # ❌ 无事件，Allure 无记录

# ✅ 期望状态（与 HTTP 一致）
def test_login(page):
    login_page = LoginPage(page, runtime=runtime)
    login_page.goto()  # ✅ 发布 UINavigationStartEvent + UINavigationEndEvent
    # ✅ Allure 自动记录：🌐 Navigate: LoginPage → /login

    page.get_by_label("Username").fill("admin")
    # ✅ 发布 UIInputEvent
    # ✅ Allure 自动记录：⌨️ Input: Username = 'admin'

    page.get_by_role("button", name="Sign in").click()
    # ✅ 发布 UIClickEvent
    # ✅ Allure 自动记录：👆 Click: button[Sign in]
```

---

## 一致性设计方案

### 方案核心：BrowserManager 事件监听器 + Playwright 原生事件

**设计理念**：
- ✅ 不包装 Playwright API（维护成本为零）
- ✅ 利用 Playwright 原生事件系统（page.on()）
- ✅ 与 HTTP 的 Middleware 理念一致（统一拦截点 + 自动执行）

```
┌─────────────────────────────────────────────────────────────┐
│          Web UI 测试完整架构（v3.44.0 建议）                  │
└─────────────────────────────────────────────────────────────┘

1. 配置加载
   FrameworkSettings
   └─ web: WebConfig
      ├─ base_url
      ├─ browser_type
      └─ headless

2. Provider 创建
   runtime.browser_manager()
   └─ browser_manager_factory(context)
      └─ BrowserManager(
           config=context.settings.web,  # ✅ 自动读取
           runtime=runtime,              # ✅ 注入 runtime
         )

3. BrowserManager 自动注册事件监听器（新增 🆕）
   BrowserManager.start()
   └─ _setup_event_listeners(page)  # ✅ 统一拦截点
      └─ 注册 Playwright 原生事件：
         ├─ page.on("load", handler)          # 页面加载完成
         ├─ page.on("request", handler)       # 网络请求（与 HTTP 对应）
         ├─ page.on("response", handler)      # 网络响应（与 HTTP 对应）
         ├─ page.on("console", handler)       # Console 输出
         ├─ page.on("dialog", handler)        # 弹窗
         └─ page.on("pageerror", handler)     # 页面错误

4. 事件自动触发（Playwright 原生）
   用户代码：page.goto("/login")  # ✅ 使用原生 API
   └─ Playwright 自动触发事件：
      ├─ "load" 事件 → handler 发布 UINavigationEndEvent
      └─ "request"/"response" 事件 → handler 发布网络事件

5. BasePage 增强（可选）
   class BasePage:
       def __init__(self, page, runtime=None):
           self.runtime = runtime
           self.base_url = (
               runtime.settings.web.base_url
               if runtime and runtime.settings.web
               else ""
           )
           self.page = page  # ✅ 使用原生 Page，不包装

       def goto(self):
           """导航（可选发布业务事件）"""
           url = urljoin(self.base_url, self.url)

           # 可选：发布导航开始事件
           if self.runtime and self.runtime.event_bus:
               event = UINavigationStartEvent.create(...)
               self.runtime.event_bus.publish_sync(event)

           self.page.goto(url)  # ✅ 使用原生 API
           # 页面加载完成事件由 BrowserManager 自动发布

6. 事件订阅
   EventBus
   └─ AllureObserver
      └─ handle_ui_navigation_end_event()
         └─ allure.step("🌐 Navigate: Page loaded → /login")

7. 可观测性
   - EventBus: 发布/订阅 UI 事件（粗粒度自动 + 细粒度可选）
   - Logger: get_logger(__name__).debug("Page navigated")
   - OpenTelemetry: trace_id/span_id 自动注入
   - Allure: 自动记录 UI 操作
```

**架构对齐检查**：

| 维度 | HTTP | Web (v3.44.0) |
|------|------|--------------|
| **统一拦截点** | ✅ HttpClient.request() | ✅ BrowserManager.start() + page.on() |
| **自动机制** | ✅ Middleware 自动执行 | ✅ Event Listener 自动触发 |
| **实现方式** | Middleware（洋葱模型） | Event Listener（观察者模式） |
| **维护成本** | ✅ 低（一个入口） | ✅ 低（Playwright 原生 API） |
| **API 变动影响** | ✅ 无影响 | ✅ 无影响（不包装 API） |
| **用户体验** | ✅ 完全透明 | ✅ 完全透明 |

---

## 具体实施

### 1. 增强 BrowserManager（核心改动）🔄

```python
# src/df_test_framework/capabilities/drivers/web/playwright/browser.py

"""浏览器管理器

v3.44.0 增强：
- 支持 runtime 参数（注入 EventBus）
- 自动注册 Playwright 原生事件监听器
- 利用 page.on() 实现事件发布（无需包装 API）
"""

from enum import Enum
from typing import Any
import time

try:
    from playwright.sync_api import (
        Browser,
        BrowserContext,
        Page,
        Playwright,
        Request,
        Response,
        ConsoleMessage,
        Dialog,
        sync_playwright,
    )
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    # ... 占位符

from df_test_framework.infrastructure.logging import get_logger

logger = get_logger(__name__)


class BrowserType(str, Enum):
    """Playwright 页面事件化（自动发布 WebBrowserEvent）

    设计理念：
    - 透明代理：保留原生 Playwright API
    - 自动观测：通过 page.on() 监听并发布 WebBrowserEvent/ UIErrorEvent
    - 零侵入：用户代码无需修改，page fixture 自动完成注册
    - 与 HTTP 一致：统一拦截点 + 自动事件发布的理念

    使用方式：
        >>> # 方式1: 通过 runtime/page fixture（推荐）
        >>> def test_example(page):  # page 已自动注册事件监听器
        ...     page.goto("/login")  # ✅ 自动发布 WebBrowserEvent(page.load)
        ...     page.get_by_label("Username").fill("admin")
    """

    def __init__(
        self,
        page: Page,
        runtime: "RuntimeContext | None" = None,
        page_name: str = "Page",
    ):
        """初始化 InstrumentedPage

        Args:
            page: 原生 Playwright Page 实例
            runtime: RuntimeContext（用于获取 EventBus 和配置）
            page_name: 页面名称（用于事件标识）
        """
        self._page = page
        self._runtime = runtime
        self._page_name = page_name
        self._event_bus = runtime.event_bus if runtime else None

        logger.debug(
            f"InstrumentedPage initialized: page_name={page_name}, "
            f"event_bus={'enabled' if self._event_bus else 'disabled'}"
        )

    # ========== 导航操作 ==========

    def goto(self, url: str, **kwargs: Any) -> None:
        """导航到 URL（发布 UINavigationStartEvent + UINavigationEndEvent）

        Args:
            url: 目标 URL
            **kwargs: 传递给 page.goto() 的其他参数
        """
        if not self._event_bus:
            # 无 EventBus，直接执行
            return self._page.goto(url, **kwargs)

        # 发布 Start 事件
        base_url = (
            self._runtime.settings.web.base_url
            if self._runtime and self._runtime.settings.web
            else ""
        )
        start_event, correlation_id = UINavigationStartEvent.create(
            page_name=self._page_name,
            url=url,
            base_url=base_url,
        )
        self._event_bus.publish_sync(start_event)

        # 执行导航
        start_time = time.time()
        success = True
        try:
            response = self._page.goto(url, **kwargs)
            duration = time.time() - start_time

            # 获取页面标题
            title = self._page.title()

            return response
        except Exception as e:
            duration = time.time() - start_time
            success = False

            # 发布 Error 事件
            from df_test_framework.core.events import UIErrorEvent
            error_event = UIErrorEvent.create(
                page_name=self._page_name,
                operation="goto",
                selector=url,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            self._event_bus.publish_sync(error_event)
            raise
        finally:
            # 发布 End 事件
            end_event = UINavigationEndEvent.create(
                page_name=self._page_name,
                url=url,
                title=title if success else "",
                duration=duration,
                success=success,
                correlation_id=correlation_id,
            )
            self._event_bus.publish_sync(end_event)

    # ========== Locator 包装 ==========

    def get_by_test_id(self, test_id: str) -> "InstrumentedLocator":
        """获取 Locator（自动包装）"""
        locator = self._page.get_by_test_id(test_id)
        return InstrumentedLocator(
            locator,
            page_name=self._page_name,
            event_bus=self._event_bus,
            selector_type="test-id",
            selector_value=test_id,
        )

    def get_by_role(self, role: str, **kwargs: Any) -> "InstrumentedLocator":
        """获取 Locator（自动包装）"""
        locator = self._page.get_by_role(role, **kwargs)
        name = kwargs.get("name", "")
        selector = f"role={role}" + (f"[name={name}]" if name else "")
        return InstrumentedLocator(
            locator,
            page_name=self._page_name,
            event_bus=self._event_bus,
            selector_type="role",
            selector_value=selector,
        )

    def get_by_label(self, text: str, **kwargs: Any) -> "InstrumentedLocator":
        """获取 Locator（自动包装）"""
        locator = self._page.get_by_label(text, **kwargs)
        return InstrumentedLocator(
            locator,
            page_name=self._page_name,
            event_bus=self._event_bus,
            selector_type="label",
            selector_value=text,
        )

    # ========== 其他方法：透明代理 ==========

    def __getattr__(self, name: str) -> Any:
        """透明代理：所有未定义的方法转发给原生 Page"""
        return getattr(self._page, name)


class InstrumentedLocator:
    """Locator 包装器（自动发布事件）

    拦截 click(), fill() 等操作，发布事件。
    """

    def __init__(
        self,
        locator: Locator,
        page_name: str,
        event_bus: "EventBus | None",
        selector_type: str,
        selector_value: str,
    ):
        self._locator = locator
        self._page_name = page_name
        self._event_bus = event_bus
        self._selector_type = selector_type
        self._selector_value = selector_value

    def click(self, **kwargs: Any) -> None:
        """点击操作（发布 UIClickEvent）"""
        if not self._event_bus:
            return self._locator.click(**kwargs)

        start_time = time.time()
        try:
            # 尝试获取元素文本
            element_text = ""
            try:
                element_text = self._locator.text_content() or ""
            except Exception:
                pass

            # 执行点击
            self._locator.click(**kwargs)
            duration = time.time() - start_time

            # 发布事件
            event = UIClickEvent.create(
                page_name=self._page_name,
                selector=self._selector_value,
                element_text=element_text,
                duration=duration,
            )
            self._event_bus.publish_sync(event)
        except Exception as e:
            duration = time.time() - start_time

            # 发布 Error 事件
            from df_test_framework.core.events import UIErrorEvent
            error_event = UIErrorEvent.create(
                page_name=self._page_name,
                operation="click",
                selector=self._selector_value,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            self._event_bus.publish_sync(error_event)
            raise

    def fill(self, value: str, **kwargs: Any) -> None:
        """填充操作（发布 UIInputEvent）"""
        if not self._event_bus:
            return self._locator.fill(value, **kwargs)

        start_time = time.time()
        try:
            # 执行填充
            self._locator.fill(value, **kwargs)
            duration = time.time() - start_time

            # 发布事件（密码字段脱敏）
            is_password = "password" in self._selector_value.lower()
            display_value = "****" if is_password else value

            event = UIInputEvent.create(
                page_name=self._page_name,
                selector=self._selector_value,
                value=display_value,
                masked=is_password,
                duration=duration,
            )
            self._event_bus.publish_sync(event)
        except Exception as e:
            duration = time.time() - start_time

            # 发布 Error 事件
            from df_test_framework.core.events import UIErrorEvent
            error_event = UIErrorEvent.create(
                page_name=self._page_name,
                operation="fill",
                selector=self._selector_value,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            self._event_bus.publish_sync(error_event)
            raise

    def __getattr__(self, name: str) -> Any:
        """透明代理：其他方法转发给原生 Locator"""
        return getattr(self._locator, name)


__all__ = ["InstrumentedPage", "InstrumentedLocator"]
```

---

### 2. BasePage 增强（支持 runtime） 🔄

```python
# src/df_test_framework/capabilities/drivers/web/playwright/page.py

class BasePage(ABC):
    """页面对象基类

    v3.44.0 增强：
    - 支持 runtime 参数（自动读取配置）
    - 自动包装为 InstrumentedPage（发布事件）
    - 与 HTTP 客户端保持架构一致
    """

    def __init__(
        self,
        page: Page,
        url: str | None = None,
        base_url: str | None = None,
        runtime: "RuntimeContext | None" = None,  # 🆕 支持 runtime
    ):
        """初始化页面对象

        Args:
            page: Playwright Page 实例
            url: 页面相对 URL
            base_url: 基础 URL（可选，从 runtime 自动读取）
            runtime: RuntimeContext（可选，用于自动配置和事件发布）

        Example:
            >>> # 方式1: 传入 runtime（推荐 ✅）
            >>> login_page = LoginPage(page, runtime=runtime)
            >>> # base_url 自动从 runtime.settings.web.base_url 读取
            >>> # 事件自动发布到 runtime.event_bus
            >>>
            >>> # 方式2: 显式传入 base_url（高级场景）
            >>> login_page = LoginPage(page, base_url="http://mock.local")
            >>>
            >>> # 方式3: 不传任何参数（兼容旧代码）
            >>> login_page = LoginPage(page)
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(...)

        self.runtime = runtime
        self.url = url

        # ✅ 自动从 runtime 获取 base_url
        if base_url is not None:
            self.base_url = base_url
        elif runtime and runtime.settings.web:
            self.base_url = runtime.settings.web.base_url or ""
        else:
            self.base_url = ""

        # ✅ 自动包装为 InstrumentedPage（发布事件）
        if isinstance(page, InstrumentedPage):
            # 已经是 InstrumentedPage，直接使用
            self.page = page
        elif runtime:
            # 包装为 InstrumentedPage（启用事件发布）
            self.page = InstrumentedPage(
                page,
                runtime=runtime,
                page_name=self.__class__.__name__,
            )
        else:
            # 无 runtime，直接使用原生 Page（向后兼容）
            self.page = page

        logger.debug(
            f"BasePage initialized: {self.__class__.__name__}, "
            f"base_url={self.base_url}, "
            f"instrumented={isinstance(self.page, InstrumentedPage)}"
        )

    # ... 其他方法保持不变
```

---

### 3. AppActions 增强（支持 runtime） 🔄

```python
# src/df_test_framework/capabilities/drivers/web/app_actions.py

class AppActions:
    """应用业务操作基类

    v3.44.0 增强：
    - 支持 runtime 参数（自动读取配置）
    - 自动包装 page 为 InstrumentedPage
    """

    def __init__(
        self,
        page: Page,
        base_url: str | None = None,
        runtime: "RuntimeContext | None" = None,  # 🆕 支持 runtime
    ):
        """初始化 App Actions

        Args:
            page: Playwright Page 实例
            base_url: 基础 URL（可选，从 runtime 自动读取）
            runtime: RuntimeContext（可选）

        Example:
            >>> # 方式1: 传入 runtime（推荐 ✅）
            >>> app_actions = AppActions(page, runtime=runtime)
            >>>
            >>> # 方式2: 显式传入 base_url
            >>> app_actions = AppActions(page, base_url="http://localhost:3000")
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(...)

        self.runtime = runtime

        # ✅ 自动从 runtime 获取 base_url
        if base_url is not None:
            self.base_url = base_url
        elif runtime and runtime.settings.web:
            self.base_url = runtime.settings.web.base_url or ""
        else:
            self.base_url = ""

        # ✅ 自动包装为 InstrumentedPage
        if isinstance(page, InstrumentedPage):
            self.page = page
        elif runtime:
            self.page = InstrumentedPage(
                page,
                runtime=runtime,
                page_name=self.__class__.__name__,
            )
        else:
            self.page = page
```

---

### 4. 增强现有 Fixtures（关键改动）🔄

```python
# src/df_test_framework/testing/fixtures/ui.py

# ========== 方案 A：直接增强 page fixture（推荐 ⭐⭐⭐⭐⭐）==========

@pytest.fixture(scope="function")
def page(context, runtime):
    """页面实例（函数级）- 自动包装为 InstrumentedPage

    v3.44.0 增强：
    - 自动包装为 InstrumentedPage（启用事件发布）
    - runtime 参数对用户透明（无需在测试中使用）
    - 与 HTTP 的 http_client fixture 完全一致的用户体验

    Args:
        context: 浏览器上下文
        runtime: RuntimeContext（自动注入，用户无需关心）

    Yields:
        Page: 自动注册事件监听器的 Playwright 页面实例

    示例（用户完全无感知 runtime）:
        >>> def test_example(page):  # ✅ 与 HTTP 完全一致
        ...     page.goto("https://example.com")  # ✅ 自动发布 WebBrowserEvent(page.load)
        ...     page.get_by_label("Username").fill("admin")
        ...     assert page.title() == "Example Domain"
    """
    p = context.new_page()

    # ✅ 自动注册事件监听器（发布 WebBrowserEvent + UIErrorEvent）
    browser_manager._setup_event_listeners(p)

    yield p

    p.close()


# ========== 方案 B：page fixture 直接事件化（当前实现）==========

@pytest.fixture(scope="function")
def page(context, browser_manager):
    """页面实例（函数级，自动注册事件监听器）

    v3.44.0: 使用 BrowserManager 注册 Playwright 原生事件监听器，事件发布到 runtime.event_bus。

    Args:
        context: 浏览器上下文
        browser_manager: 浏览器管理器（提供配置与事件监听注册）

    Returns:
        Page: 自动事件化的 Playwright 页面实例
    """
    p = context.new_page()
    browser_manager._setup_event_listeners(p)
    yield p
    p.close()


# ========== Page Object Factory（可选，高级场景）==========

@pytest.fixture
def page_object_factory(page, runtime):
    """Page Object 工厂（runtime 自动注入）

    v3.44.0: 新增

    用于创建 Page Object 时自动注入 runtime，用户无需手动传参。

    Args:
        page: Playwright Page 实例（可以是原生或 InstrumentedPage）
        runtime: RuntimeContext（自动注入）

    Returns:
        callable: Page Object 工厂函数

    示例:
        >>> def test_login(page_object_factory):
        ...     from my_project.pages import LoginPage
        ...     login_page = page_object_factory(LoginPage)  # ✅ runtime 自动注入
        ...     login_page.goto()  # base_url 自动读取
    """
    def _factory(page_class, **kwargs):
        # ✅ 自动注入 runtime（用户无感知）
        return page_class(page, runtime=runtime, **kwargs)
    return _factory


# ========== App Actions（推荐模式）==========

@pytest.fixture
def app_actions(page, runtime):
    """App Actions fixture（推荐业务操作模式）

    v3.44.0: 更新 - 自动注入 runtime

    用户应在项目的 conftest.py 中覆盖此 fixture，指定具体的 AppActions 类。
    runtime 参数会自动注入，用户无需关心。

    Args:
        page: Playwright Page 实例
        runtime: RuntimeContext（自动注入）

    Returns:
        AppActions: 应用业务操作实例

    用户项目示例（conftest.py）:
        >>> from my_project.app_actions import MyAppActions
        >>>
        >>> @pytest.fixture
        >>> def app_actions(page, runtime):  # ✅ runtime 自动注入
        ...     return MyAppActions(page, runtime=runtime)
        >>>
        >>> # 测试中使用（test_user.py）:
        >>> def test_user_flow(app_actions):  # ✅ 完全自动化
        ...     app_actions.login_as_admin()  # ✅ base_url、事件发布全自动
        ...     app_actions.create_user("john", "john@example.com")
    """
    # 默认实现（用户应覆盖）
    from df_test_framework.capabilities.drivers.web import AppActions
    return AppActions(page, runtime=runtime)
```

**关键设计决策**：

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **方案A** | 完全透明，与HTTP完全一致 | 破坏向后兼容性（page变为InstrumentedPage） | ⭐⭐⭐⭐⭐ (v4.0.0) |
| **方案B** | 100%向后兼容，渐进式升级 | page fixture 自动事件化，无需新增 fixture | ⭐⭐⭐⭐⭐ (v3.44.0) |

**推荐实施**：
- **v3.44.0**: 采用方案B（向后兼容）
  - page fixture 自动注册事件监听器（推荐使用）
  - 文档中引导用户迁移到事件化的 page 用法

- **v4.0.0**: 采用方案A（破坏性变更）
  - 直接增强 `page` fixture
  - 移除额外包装（不再需要）
  - 完全与 HTTP 一致

---

### 5. 使用方式对比：真正的一致性 ✅

#### HTTP 使用方式（参照标准）

```python
def test_api(http_client):
    """HTTP 测试 - 完全自动化 ✅

    用户体验：
    - ❌ 不需要传 runtime
    - ❌ 不需要传 base_url
    - ✅ 事件自动发布
    - ✅ Allure 自动记录
    """
    response = http_client.get("/users")  # ✅ 完全透明
    assert response.status_code == 200
```

#### 当前 Web 方式（v3.43.0）- 不够自动化 ⚠️

```python
def test_login(page, runtime):
    """Web 测试 - 需要手动配置 ⚠️

    问题：
    - ⚠️ 需要手动传 runtime
    - ⚠️ 需要手动传 base_url
    - ❌ 无事件发布
    - ❌ Allure 无记录
    """
    # ⚠️ 需要手动传 base_url
    login_page = LoginPage(page, base_url=runtime.settings.web.base_url)

    # ❌ 无事件发布，Allure 无记录
    login_page.goto()
    page.get_by_label("Username").fill("admin")
    page.get_by_role("button", name="Sign in").click()
```

#### 新 Web 方式（v3.44.0）- 完全配置驱动 ✅

```python
# ========== 方式1: 使用 page fixture（事件已自动注册，推荐 ⭐⭐⭐⭐⭐）==========
def test_login(page):
    """与 HTTP 完全一致的用户体验 ✅

    用户体验：
    - ✅ 不需要传 runtime（完全隐藏）
    - ✅ 不需要传 base_url
    - ✅ 事件自动发布
    - ✅ Allure 自动记录
    """
    # ✅ 完全透明，与 http_client 一致
    page.goto("/login")  # 🌐 自动发布 WebBrowserEvent(page.load)
    page.get_by_label("Username").fill("admin")
    page.get_by_role("button", name="Sign in").click()


# ========== 方式2: 使用 page_object_factory（推荐 ⭐⭐⭐⭐⭐）==========
def test_login(page_object_factory):
    """Page Object 模式 - runtime 完全隐藏 ✅"""
    # ✅ runtime 自动注入，用户无感知
    login_page = page_object_factory(LoginPage)

    # ✅ base_url 自动读取，事件自动发布
    login_page.goto()  # 内部自动拼接 base_url
    login_page.page.get_by_label("Username").fill("admin")
    login_page.page.get_by_role("button", name="Sign in").click()


# ========== 方式3: 使用 app_actions（最推荐 ⭐⭐⭐⭐⭐）==========
def test_user_flow(app_actions):
    """业务操作模式 - 与 HTTP 完全等价 ✅

    等价对比：
    - HTTP: http_client.post("/users", json=data)
    - Web:  app_actions.create_user(name, email)

    两者都是：完全配置驱动 + 事件自动发布 + Allure 自动记录
    """
    # ✅ 完全自动化，与 HTTP 完全一致
    app_actions.login_as_admin()  # 🚀 一行搞定
    app_actions.create_user("john", "john@example.com")
    app_actions.delete_user("john")


# ========== 对比总结 ==========
```

**一致性验证**：

| 维度 | HTTP | Web (v3.43.0) | Web (v3.44.0) |
|------|------|---------------|---------------|
| **用户需要传 runtime？** | ❌ 不需要 | ⚠️ 需要 | ✅ 不需要 |
| **用户需要传 base_url？** | ❌ 不需要 | ⚠️ 需要 | ✅ 不需要 |
| **事件自动发布？** | ✅ 是 | ❌ 否 | ✅ 是 |
| **Allure 自动记录？** | ✅ 是 | ❌ 否 | ✅ 是 |
| **用户体验** | ✅ 完全透明 | ⚠️ 需要手动配置 | ✅ 完全透明 |
| **架构一致性** | ✅ 标准 | ❌ 不一致 | ✅ 完全一致 |

---

## 实施路线

### v3.44.0 - 核心架构（推荐）

**目标**: 实现与 HTTP 完全一致的架构

1. ✅ **新增 InstrumentedPage / InstrumentedLocator**
   - 包装 Playwright API
   - 自动发布 UI 事件
   - 透明代理，不影响现有功能

2. ✅ **增强 BasePage**
   - 支持 `runtime` 参数
   - 自动读取 `base_url` 从配置
   - 自动包装为 InstrumentedPage

3. ✅ **增强 AppActions**
   - 支持 `runtime` 参数
   - 自动读取 `base_url` 从配置
   - 自动包装 page

4. ✅ **新增 Fixtures**
   - `page` - 自动注册事件监听器（WebBrowserEvent + UIErrorEvent）
   - `page_object_factory` - Page Object 工厂
   - 更新 `app_actions` 示例

5. ✅ **文档更新**
   - 更新使用指南
   - 添加最佳实践示例
   - 更新 CHANGELOG

**工作量**: 约 2-3 天

---

### v3.45.0 - 完善与优化（可选）

1. **BaseComponent 增强**
   ```python
   class BaseComponent:
       def __init__(self, page, test_id=None, runtime=None):
           # ✅ 支持 runtime
           self.runtime = runtime
   ```

2. **Screenshot 事件**
   - 自动发布 UIScreenshotEvent
   - 自动附加到 Allure 报告

3. **性能优化**
   - 缓存事件发布逻辑
   - 减少不必要的事件

4. **调试增强**
   - ConsoleDebugObserver 支持 UI 事件
   - 终端彩色输出 UI 操作

---

## 总结

### 核心改进

| 维度 | v3.43.0 (当前) | v3.44.0 (建议) | 改进 |
|------|---------------|---------------|------|
| **配置传递** | 手动传 base_url | 自动从 runtime 读取 | ✅ 与 HTTP 一致 |
| **事件发布** | ❌ 无 | ✅ 自动发布 UI 事件 | ✅ 与 HTTP 一致 |
| **Allure 集成** | ❌ 无 | ✅ 自动记录 UI 操作 | ✅ 与 HTTP 一致 |
| **日志记录** | ⚠️ 部分 | ✅ 完整日志 | ✅ 与 HTTP 一致 |
| **可观测性** | ⚠️ 部分 | ✅ 完整（EventBus + OTel + Allure） | ✅ 与 HTTP 一致 |
| **向后兼容** | - | ✅ 100% 兼容 | ✅ 不破坏现有代码 |

### 架构对齐检查 ✅

| 特性 | HTTP | Web (v3.44.0) |
|------|------|--------------|
| **配置驱动** | HTTPConfig + Provider | WebConfig + Provider ✅ |
| **自动获取配置** | ✅ `http_client` fixture（runtime完全隐藏） | ✅ `page` fixture（runtime完全隐藏） |
| **事件发布** | ✅ HttpEventPublisherMiddleware | ✅ InstrumentedPage（fixture自动包装） |
| **日志集成** | ✅ get_logger() | ✅ get_logger() |
| **Allure 集成** | ✅ AllureObserver | ✅ AllureObserver |
| **可观测性** | ✅ EventBus + OTel | ✅ EventBus + OTel |
| **用户体验** | ✅ 完全透明，无需传runtime | ✅ 完全透明，无需传runtime |

---

**结论**: v3.44.0 方案实现了 Web 与 HTTP 的完全架构一致性，建议实施！

---

**文档维护者**: DF Test Framework Team
**最后更新**: 2026-01-08
**建议版本**: v3.44.0
