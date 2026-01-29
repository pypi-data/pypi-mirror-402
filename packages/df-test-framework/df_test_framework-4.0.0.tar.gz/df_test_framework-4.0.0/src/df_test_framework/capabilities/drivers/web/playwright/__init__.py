"""UI测试模块（v4.0.0 异步优先）

提供基于Playwright的UI自动化测试支持

v4.0.0: 异步优先，同步兼容
- AsyncBrowserManager, AsyncBasePage: 异步版本（推荐，性能提升 2-3 倍）
- BrowserManager, BasePage: 同步版本（向后兼容，用于简单场景）

核心功能:
- BrowserManager/AsyncBrowserManager: 浏览器管理（支持Chromium/Firefox/WebKit）
- BasePage/AsyncBasePage: 页面对象基类（POM模式）
- ElementLocator: 元素定位器
- WaitHelper: 等待策略助手

支持的浏览器:
- Chromium (推荐)
- Firefox
- WebKit (Safari引擎)

使用前需要安装:
    pip install playwright
    playwright install
"""

# 异步版本（推荐）
from .async_browser import AsyncBrowserManager
from .async_page import AsyncBasePage

# 同步版本（兼容）
from .browser import BrowserManager, BrowserType
from .locator import ElementLocator, LocatorType, WaitHelper
from .page import BasePage

__all__ = [
    # 异步版本（推荐）
    "AsyncBrowserManager",
    "AsyncBasePage",
    # 同步版本（兼容）
    "BrowserManager",
    "BasePage",
    # 浏览器类型
    "BrowserType",
    # 元素定位
    "ElementLocator",
    "LocatorType",
    # 等待助手
    "WaitHelper",
]
