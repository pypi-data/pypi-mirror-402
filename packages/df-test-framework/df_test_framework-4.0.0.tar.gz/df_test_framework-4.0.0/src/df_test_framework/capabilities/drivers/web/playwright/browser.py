"""浏览器管理器（v4.0.0 同步兼容版本）

提供浏览器实例的创建、配置和管理
基于 Playwright 同步 API 实现，支持多种浏览器

v4.0.0: 异步优先，同步兼容
- BrowserManager：同步版本（向后兼容，用于简单场景）
- AsyncBrowserManager：异步版本（推荐，性能提升 2-3 倍）

推荐：新项目使用 AsyncBrowserManager 获得更好的性能。
"""

from enum import Enum
from typing import Any

try:
    from playwright.sync_api import (
        Browser,
        BrowserContext,
        Page,
        Playwright,
        sync_playwright,
    )

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Browser = Any
    BrowserContext = Any
    Page = Any
    Playwright = Any

    # 为测试 mock 提供占位符
    def sync_playwright():
        raise ImportError("Playwright未安装")


class BrowserType(str, Enum):
    """浏览器类型枚举"""

    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class BrowserManager:
    """
    浏览器管理器（v4.0.0 同步兼容版本）

    基于 Playwright 同步 API 实现，提供浏览器启动、配置和页面管理。

    v4.0.0 版本选择:
    - 同步版本（BrowserManager）：向后兼容，适合简单场景
    - 异步版本（AsyncBrowserManager）：推荐使用，性能提升 2-3 倍

    使用示例（同步版本）:
        >>> # 配置驱动模式（推荐）
        >>> manager = BrowserManager(config=web_config, runtime=runtime)
        >>> manager.start()
        >>> manager.page.goto("https://example.com")
        >>> manager.stop()
        >>>
        >>> # 同步上下文管理器
        >>> with BrowserManager(config=web_config) as (browser, context, page):
        ...     page.goto("https://example.com")

    推荐：使用异步版本以获得更好的性能:
        >>> from df_test_framework.capabilities.drivers.web import AsyncBrowserManager
        >>>
        >>> async with AsyncBrowserManager(config=web_config) as (browser, context, page):
        ...     await page.goto("https://example.com")
    """

    def __init__(
        self,
        config: Any | None = None,
        runtime: Any | None = None,
        **overrides: Any,
    ):
        """
        初始化浏览器管理器

        Args:
            config: WebConfig 配置对象
            runtime: RuntimeContext 实例 - 用于事件发布
            **overrides: 配置覆盖（browser_type, headless, timeout 等）

        Raises:
            ImportError: 如果未安装 Playwright
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright未安装。请运行: pip install 'playwright>=1.40.0' && playwright install"
            )

        # 从 config 读取配置，overrides 优先
        def get_config(key: str, default: Any) -> Any:
            if key in overrides and overrides[key] is not None:
                return overrides[key]
            if config and hasattr(config, key):
                return getattr(config, key)
            return default

        # 浏览器类型需要特殊处理（字符串转枚举）
        browser_type_value = get_config("browser_type", "chromium")
        if isinstance(browser_type_value, str):
            browser_type_value = BrowserType(browser_type_value)

        self.base_url = get_config("base_url", None)
        self.browser_type = browser_type_value
        self.headless = get_config("headless", True)
        self.slow_mo = get_config("slow_mo", 0)
        self.timeout = get_config("timeout", 30000)
        self.viewport = get_config("viewport", {"width": 1280, "height": 720})

        # 标准化 record_video 值（布尔值转字符串）
        record_video_value = get_config("record_video", "off")
        if isinstance(record_video_value, bool):
            self.record_video = "on" if record_video_value else "off"
        else:
            self.record_video = record_video_value

        self.video_dir = get_config("video_dir", "reports/videos")
        self.video_size = get_config("video_size", None)

        # 合并 browser_options
        config_options = getattr(config, "browser_options", {}) if config else {}
        override_options = overrides.get("browser_options", {})
        self.browser_options = {**config_options, **override_options}

        # 保存 runtime 引用，用于获取 event_bus
        self.runtime = runtime

        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    def start(self) -> tuple[Browser, BrowserContext, Page]:
        """
        启动浏览器并创建页面（同步）

        Returns:
            tuple: (browser, context, page) 三元组

        Raises:
            RuntimeError: 如果浏览器已经启动

        Example:
            >>> manager = BrowserManager()
            >>> manager.start()
            >>> manager.page.goto("https://example.com")
        """
        if self._browser is not None:
            raise RuntimeError("浏览器已经启动，请先调用 stop() 关闭")

        # 启动 Playwright（同步）
        self._playwright = sync_playwright().start()

        # 获取浏览器启动器
        if self.browser_type == BrowserType.CHROMIUM:
            launcher = self._playwright.chromium
        elif self.browser_type == BrowserType.FIREFOX:
            launcher = self._playwright.firefox
        elif self.browser_type == BrowserType.WEBKIT:
            launcher = self._playwright.webkit
        else:
            raise ValueError(f"不支持的浏览器类型: {self.browser_type}")

        # 启动浏览器（同步）
        self._browser = launcher.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
            **self.browser_options,
        )

        # 创建浏览器上下文（支持视频录制）
        context_options: dict[str, Any] = {"viewport": self.viewport}

        # 支持完整的 record_video 选项
        # 支持: "off", "on", "retain-on-failure", "on-first-retry"
        if self.record_video and self.record_video != "off":
            from pathlib import Path

            Path(self.video_dir).mkdir(parents=True, exist_ok=True)
            context_options["record_video_dir"] = self.video_dir
            if self.video_size:
                context_options["record_video_size"] = self.video_size

        self._context = self._browser.new_context(**context_options)

        # 设置默认超时
        self._context.set_default_timeout(self.timeout)

        # 创建页面
        self._page = self._context.new_page()

        # 事件监听器注册移到 page fixture 中
        # 这里不再自动注册，确保与测试隔离的 EventBus 配合

        return self._browser, self._context, self._page

    def stop(self) -> None:
        """
        关闭浏览器并清理资源（同步）

        Example:
            >>> manager.stop()
        """
        if self._page:
            self._page.close()
            self._page = None

        if self._context:
            self._context.close()
            self._context = None

        if self._browser:
            self._browser.close()
            self._browser = None

        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def __enter__(self):
        """同步上下文管理器入口"""
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """同步上下文管理器退出"""
        self.stop()
        return False

    @property
    def browser(self) -> Browser:
        """获取浏览器实例"""
        if self._browser is None:
            raise RuntimeError("浏览器未启动，请先调用 start()")
        return self._browser

    @property
    def context(self) -> BrowserContext:
        """获取浏览器上下文"""
        if self._context is None:
            raise RuntimeError("浏览器上下文未创建，请先调用 start()")
        return self._context

    @property
    def page(self) -> Page:
        """获取页面实例"""
        if self._page is None:
            raise RuntimeError("页面未创建，请先调用 start()")
        return self._page

    def _setup_event_listeners(self, page: Page) -> None:
        """
        设置页面事件监听器

        Args:
            page: Playwright Page 对象

        Note:
            此方法由 page fixture 调用，用于注册事件监听器
        """
        if not self.runtime or not hasattr(self.runtime, "event_bus"):
            return

        event_bus = self.runtime.event_bus

        # 页面加载事件
        def on_load(page_obj):
            try:
                event_bus.publish(
                    "ui.page_load",
                    {
                        "url": page_obj.url,
                        "title": page_obj.title(),
                    },
                )
            except Exception:
                pass  # 静默失败，不影响测试

        # 页面导航事件
        def on_framenavigated(frame):
            if frame == page.main_frame:
                try:
                    event_bus.publish(
                        "ui.page_navigate",
                        {
                            "url": frame.url,
                        },
                    )
                except Exception:
                    pass

        # 控制台消息事件
        def on_console(msg):
            try:
                event_bus.publish(
                    "ui.console",
                    {
                        "type": msg.type,
                        "text": msg.text,
                        "location": msg.location,
                    },
                )
            except Exception:
                pass

        # 页面错误事件
        def on_pageerror(error):
            try:
                event_bus.publish(
                    "ui.page_error",
                    {
                        "error": str(error),
                    },
                )
            except Exception:
                pass

        # 注册监听器
        page.on("load", on_load)
        page.on("framenavigated", on_framenavigated)
        page.on("console", on_console)
        page.on("pageerror", on_pageerror)


__all__ = ["BrowserManager", "BrowserType"]
