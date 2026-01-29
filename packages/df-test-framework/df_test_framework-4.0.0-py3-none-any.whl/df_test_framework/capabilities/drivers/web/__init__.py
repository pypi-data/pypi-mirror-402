"""Web浏览器驱动（v4.0.0 异步优先）

支持多种Web驱动实现（Playwright、Selenium等）
通过Factory模式提供统一接口

v4.0.0 重大变更：异步优先，同步兼容
- AsyncAppActions, AsyncBasePage: 异步版本（推荐，性能提升 2-3 倍）
- AppActions, BasePage: 同步版本（向后兼容，用于简单场景）

v3.43.0: 新增现代UI测试模式
- BaseComponent: 可复用组件
- AppActions: 应用业务操作
- 重构 BasePage: 移除过度封装，直接使用 Playwright API

导入示例：
    # v4.0.0 异步版本（推荐）
    from df_test_framework.capabilities.drivers.web import AsyncAppActions, AsyncBasePage

    class LoginPage(AsyncBasePage):
        async def wait_for_page_load(self):
            await self.page.get_by_test_id("login-form").wait_for()

    # v3.x 同步版本（兼容）
    from df_test_framework.capabilities.drivers.web import AppActions, BasePage

    class LoginPage(BasePage):
        def wait_for_page_load(self):
            self.page.get_by_test_id("login-form").wait_for()
"""

# 协议定义
# 同步实现（兼容，v3.x）
from .app_actions import AppActions

# 异步实现（推荐，v4.0.0）
from .async_app_actions import AsyncAppActions

# 工厂类
from .factory import WebDriverFactory

# Playwright 实现
# 异步版本（推荐）
from .playwright.async_browser import AsyncBrowserManager
from .playwright.async_page import AsyncBasePage

# 同步版本（兼容）
from .playwright.browser import BrowserManager, BrowserType
from .playwright.component import BaseComponent
from .playwright.locator import ElementLocator, LocatorType, WaitHelper
from .playwright.page import BasePage
from .protocols import PageProtocol, WebDriverProtocol

__all__ = [
    # 协议
    "WebDriverProtocol",
    "PageProtocol",
    # 工厂
    "WebDriverFactory",
    # 异步版本（推荐）
    "AsyncAppActions",
    "AsyncBasePage",
    "AsyncBrowserManager",
    # 同步版本（兼容）
    "AppActions",
    "BasePage",
    "BrowserManager",
    # Playwright 实现
    "BrowserType",
    "ElementLocator",
    "LocatorType",
    "WaitHelper",
    "BaseComponent",
]
