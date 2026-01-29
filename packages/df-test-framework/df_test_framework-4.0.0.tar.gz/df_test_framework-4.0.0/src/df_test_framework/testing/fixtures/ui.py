"""UI测试 fixtures（v4.0.0 同步默认，异步可选）

提供 UI 自动化测试的 pytest fixtures 和失败诊断 hooks

v4.0.0 命名规范:
- 同步版本（默认）: browser_manager, page 等 - 无需装饰器
- 异步版本（async_ 前缀）: async_browser_manager, async_page 等 - 需要 @pytest.mark.asyncio

v3.46.3 特性保留:
- 统一失败诊断架构（pytest_runtest_makereport hook 集成到框架）
- WebConfig 配置驱动
- pytest11 自动加载
- 事件总线集成
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from typing import TYPE_CHECKING, Any

import pytest

from df_test_framework.capabilities.drivers.web import (
    AsyncBrowserManager,
    BrowserManager,
)

if TYPE_CHECKING:
    from df_test_framework.bootstrap.runtime import RuntimeContext

# 尝试导入异步 Playwright API
try:
    from playwright.async_api import Browser as AsyncBrowser
    from playwright.async_api import BrowserContext as AsyncBrowserContext
    from playwright.async_api import Page as AsyncPage

    ASYNC_PLAYWRIGHT_AVAILABLE = True
except ImportError:
    ASYNC_PLAYWRIGHT_AVAILABLE = False
    AsyncBrowser = Any
    AsyncBrowserContext = Any
    AsyncPage = Any

# 尝试导入同步 Playwright API
try:
    from playwright.sync_api import Browser as SyncBrowser
    from playwright.sync_api import BrowserContext as SyncBrowserContext
    from playwright.sync_api import Page as SyncPage

    SYNC_PLAYWRIGHT_AVAILABLE = True
except ImportError:
    SYNC_PLAYWRIGHT_AVAILABLE = False
    SyncBrowser = Any
    SyncBrowserContext = Any
    SyncPage = Any

PLAYWRIGHT_AVAILABLE = ASYNC_PLAYWRIGHT_AVAILABLE or SYNC_PLAYWRIGHT_AVAILABLE

# ========== 同步 Fixtures（默认）==========


@pytest.fixture(scope="function")
def browser_manager(
    test_runtime: RuntimeContext,
) -> Generator[BrowserManager, None, None]:
    """
    同步浏览器管理器（函数级，默认）

    v4.0.0: 同步版本作为默认，简单易用

    配置示例:
        # .env 文件
        WEB__BROWSER_TYPE=chromium
        WEB__HEADLESS=true
        WEB__TIMEOUT=30000

    Yields:
        BrowserManager: 同步浏览器管理器实例

    Example:
        >>> def test_example(browser_manager):
        ...     browser_manager.page.goto("https://example.com")
        ...     assert "Example" in browser_manager.page.title()
    """
    if not SYNC_PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright未安装，跳过UI测试")

    web_config = test_runtime.settings.web
    manager = BrowserManager(config=web_config, runtime=test_runtime)
    manager.start()

    yield manager

    manager.stop()


@pytest.fixture(scope="function")
def browser(browser_manager: BrowserManager) -> SyncBrowser:
    """
    浏览器实例（函数级，同步版本）

    Args:
        browser_manager: 同步浏览器管理器

    Returns:
        Browser: Playwright 浏览器实例

    Example:
        >>> def test_browser_info(browser):
        ...     version = browser.version
        ...     print(f"Browser version: {version}")
    """
    return browser_manager.browser


@pytest.fixture(scope="function")
def context(browser_manager: BrowserManager) -> SyncBrowserContext:
    """
    浏览器上下文（函数级，同步版本）

    每个测试函数使用独立的浏览器上下文，测试间相互隔离

    Args:
        browser_manager: 同步浏览器管理器

    Returns:
        BrowserContext: Playwright 浏览器上下文

    Example:
        >>> def test_context(context):
        ...     context.add_cookies([{"name": "test", "value": "123", "url": "https://example.com"}])
    """
    return browser_manager.context


@pytest.fixture(scope="function")
def page(
    context: SyncBrowserContext, browser_manager: BrowserManager
) -> Generator[SyncPage, None, None]:
    """
    页面实例（函数级，同步版本）

    每个测试函数获取独立的页面实例

    Args:
        context: 浏览器上下文
        browser_manager: 浏览器管理器（用于注册事件监听器）

    Yields:
        Page: Playwright 页面实例

    Example:
        >>> def test_example(page):
        ...     page.goto("https://example.com")
        ...     assert "Example" in page.title()
    """
    p = context.new_page()

    # 自动注册事件监听器
    browser_manager._setup_event_listeners(p)

    yield p

    p.close()


@pytest.fixture(scope="function")
def ui_manager(browser_manager: BrowserManager) -> BrowserManager:
    """
    UI 管理器（函数级，同步版本）

    提供完整的浏览器管理器，包含 browser、context、page

    Args:
        browser_manager: 同步浏览器管理器

    Returns:
        BrowserManager: 同步浏览器管理器实例

    Example:
        >>> def test_with_manager(ui_manager):
        ...     page = ui_manager.page
        ...     page.goto("https://example.com")
        ...     assert "Example" in page.title()
    """
    return browser_manager


# ========== 异步 Fixtures（async_ 前缀）==========


@pytest.fixture(scope="function")
async def async_browser_manager(
    test_runtime: RuntimeContext,
) -> AsyncGenerator[AsyncBrowserManager, None]:
    """
    异步浏览器管理器（函数级）

    v4.0.0: 完全异步化，使用 async/await，性能提升 2-3 倍

    配置示例:
        # .env 文件
        WEB__BROWSER_TYPE=chromium
        WEB__HEADLESS=true
        WEB__TIMEOUT=30000
        WEB__VIEWPORT__width=1920
        WEB__VIEWPORT__height=1080

    Yields:
        AsyncBrowserManager: 异步浏览器管理器实例

    Example:
        >>> @pytest.mark.asyncio
        >>> async def test_example(async_browser_manager):
        ...     await async_browser_manager.page.goto("https://example.com")
        ...     assert "Example" in await async_browser_manager.page.title()
    """
    if not ASYNC_PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright未安装，跳过UI测试")

    web_config = test_runtime.settings.web
    manager = AsyncBrowserManager(config=web_config, runtime=test_runtime)
    await manager.start()

    yield manager

    await manager.stop()


@pytest.fixture(scope="function")
def async_browser(async_browser_manager: AsyncBrowserManager) -> AsyncBrowser:
    """
    浏览器实例（函数级，异步版本）

    Args:
        async_browser_manager: 异步浏览器管理器

    Returns:
        Browser: Playwright 浏览器实例

    Example:
        >>> @pytest.mark.asyncio
        >>> async def test_browser_info(async_browser):
        ...     version = async_browser.version
        ...     print(f"Browser version: {version}")
    """
    return async_browser_manager.browser


@pytest.fixture(scope="function")
def async_context(async_browser_manager: AsyncBrowserManager) -> AsyncBrowserContext:
    """
    浏览器上下文（函数级，异步版本）

    每个测试函数使用独立的浏览器上下文，测试间相互隔离

    Args:
        async_browser_manager: 异步浏览器管理器

    Returns:
        BrowserContext: Playwright 浏览器上下文

    Example:
        >>> @pytest.mark.asyncio
        >>> async def test_context(async_context):
        ...     await async_context.add_cookies([{"name": "test", "value": "123", "url": "https://example.com"}])
    """
    return async_browser_manager.context


@pytest.fixture(scope="function")
async def async_page(
    async_context: AsyncBrowserContext, async_browser_manager: AsyncBrowserManager
) -> AsyncGenerator[AsyncPage, None]:
    """
    页面实例（函数级，异步）

    每个测试函数获取独立的页面实例

    v4.0.0: 异步化，使用 await 创建和关闭页面

    Args:
        async_context: 浏览器上下文
        async_browser_manager: 浏览器管理器（用于注册事件监听器）

    Yields:
        Page: Playwright 页面实例

    Example:
        >>> @pytest.mark.asyncio
        >>> async def test_example(async_page):
        ...     await async_page.goto("https://example.com")
        ...     assert "Example" in await async_page.title()
    """
    p = await async_context.new_page()

    # 自动注册事件监听器
    async_browser_manager._setup_event_listeners(p)

    yield p

    await p.close()


@pytest.fixture(scope="function")
def async_ui_manager(async_browser_manager: AsyncBrowserManager) -> AsyncBrowserManager:
    """
    UI 管理器（函数级，异步版本）

    提供完整的浏览器管理器，包含 browser、context、page

    Args:
        async_browser_manager: 异步浏览器管理器

    Returns:
        AsyncBrowserManager: 异步浏览器管理器实例

    Example:
        >>> @pytest.mark.asyncio
        >>> async def test_with_manager(async_ui_manager):
        ...     page = async_ui_manager.page
        ...     await page.goto("https://example.com")
        ...     assert "Example" in await page.title()
    """
    return async_browser_manager


# ========== 同步便捷 fixtures ==========


@pytest.fixture
def goto(page: SyncPage):
    """
    页面导航助手（同步）

    提供简化的页面导航方法

    Args:
        page: 同步页面实例

    Returns:
        callable: 同步导航函数

    Example:
        >>> def test_navigation(goto):
        ...     goto("https://example.com")
    """

    def _goto(url: str, **kwargs):
        """导航到指定URL"""
        page.goto(url, **kwargs)
        return page

    return _goto


@pytest.fixture
def screenshot(page: SyncPage):
    """
    截图助手（同步）

    提供便捷的截图功能

    Args:
        page: 同步页面实例

    Returns:
        callable: 同步截图函数

    Example:
        >>> def test_with_screenshot(page, screenshot):
        ...     page.goto("https://example.com")
        ...     screenshot("example.png")
    """

    def _screenshot(path: str = None, **kwargs):
        """
        页面截图

        Args:
            path: 保存路径
            kwargs: 其他参数
        """
        return page.screenshot(path=path, **kwargs)

    return _screenshot


# ========== 异步便捷 fixtures ==========


@pytest.fixture
def async_goto(async_page: AsyncPage):
    """
    页面导航助手（异步）

    提供简化的页面导航方法

    Args:
        async_page: 异步页面实例

    Returns:
        callable: 异步导航函数

    Example:
        >>> @pytest.mark.asyncio
        >>> async def test_navigation(async_goto):
        ...     await async_goto("https://example.com")
    """

    async def _goto(url: str, **kwargs):
        """导航到指定URL"""
        await async_page.goto(url, **kwargs)
        return async_page

    return _goto


@pytest.fixture
def async_screenshot(async_page: AsyncPage):
    """
    截图助手（异步）

    提供便捷的截图功能

    Args:
        async_page: 异步页面实例

    Returns:
        callable: 异步截图函数

    Example:
        >>> @pytest.mark.asyncio
        >>> async def test_with_screenshot(async_page, async_screenshot):
        ...     await async_page.goto("https://example.com")
        ...     await async_screenshot("example.png")
    """

    async def _screenshot(path: str = None, **kwargs):
        """
        页面截图

        Args:
            path: 保存路径
            kwargs: 其他参数
        """
        return await async_page.screenshot(path=path, **kwargs)

    return _screenshot


# ========== App Actions Fixture ==========


@pytest.fixture
def app_actions(page: SyncPage, browser_manager: BrowserManager):
    """
    应用业务操作 fixture（v4.0.0 同步版本）

    提供 AppActions 基类实例，用于简单场景。
    复杂项目应在 conftest.py 中定义项目专用的 AppActions fixture。

    Args:
        page: 同步页面实例（已注册事件监听器）
        browser_manager: 同步浏览器管理器（用于获取配置）

    Returns:
        AppActions: 同步业务操作实例

    Example:
        >>> def test_navigation(app_actions):
        ...     app_actions.goto("/login")
        ...     # 直接使用 page 进行操作
        ...     app_actions.page.get_by_label("Username").fill("admin")

    Note:
        推荐在项目 conftest.py 中定义专用的 AppActions:

        >>> @pytest.fixture
        >>> def app_actions(page, test_runtime):
        ...     from myproject.app_actions import MyAppActions
        ...     return MyAppActions(page, runtime=test_runtime)
    """
    from df_test_framework.capabilities.drivers.web import AppActions

    return AppActions(
        page=page,
        base_url=browser_manager.base_url or "",
        runtime=browser_manager.runtime,
    )


@pytest.fixture
def async_app_actions(async_page: AsyncPage, async_browser_manager: AsyncBrowserManager):
    """
    应用业务操作 fixture（v4.0.0 异步版本）

    提供 AsyncAppActions 基类实例，用于简单场景。
    复杂项目应在 conftest.py 中定义项目专用的 AppActions fixture。

    Args:
        async_page: 异步页面实例（已注册事件监听器）
        async_browser_manager: 异步浏览器管理器（用于获取配置）

    Returns:
        AsyncAppActions: 异步业务操作实例

    Example:
        >>> @pytest.mark.asyncio
        >>> async def test_navigation(async_app_actions):
        ...     await async_app_actions.goto("/login")
        ...     # 直接使用 page 进行操作
        ...     await async_app_actions.page.get_by_label("Username").fill("admin")

    Note:
        推荐在项目 conftest.py 中定义专用的 AppActions:

        >>> @pytest.fixture
        >>> def async_app_actions(async_page, test_runtime):
        ...     from myproject.app_actions import MyAsyncAppActions
        ...     return MyAsyncAppActions(async_page, runtime=test_runtime)
    """
    from df_test_framework.capabilities.drivers.web import AsyncAppActions

    return AsyncAppActions(
        page=async_page,
        base_url=async_browser_manager.base_url or "",
        runtime=async_browser_manager.runtime,
    )


__all__ = [
    # 同步核心 fixtures（默认）
    "browser_manager",
    "browser",
    "context",
    "page",
    "ui_manager",
    # 同步业务操作 fixture
    "app_actions",
    # 同步便捷 fixtures
    "goto",
    "screenshot",
    # 异步核心 fixtures（async_ 前缀）
    "async_browser_manager",
    "async_browser",
    "async_context",
    "async_page",
    "async_ui_manager",
    # 异步业务操作 fixture
    "async_app_actions",
    # 异步便捷 fixtures
    "async_goto",
    "async_screenshot",
    # Hooks (pytest 会自动发现)
    "pytest_runtest_makereport",
]


# ========== 失败诊断 Hooks ==========


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """测试执行后的钩子 - 统一处理失败诊断

    v4.0.0: 适配异步 fixtures
    v3.46.3: 所有失败诊断逻辑统一在此处理
    - 失败时：截图 + 保留视频 + Allure 附件
    - 成功时：根据配置决定是否删除视频

    功能:
    1. 失败自动截图（可配置）
    2. 视频文件处理（根据 record_video 模式）
    3. Allure 附件自动添加（可配置）
    4. 诊断信息输出

    配置:
        # config/base.yaml
        web:
          screenshot_on_failure: true      # 默认 true
          screenshot_dir: reports/screenshots
          record_video: retain-on-failure  # off/on/retain-on-failure/on-first-retry
          attach_to_allure: true           # 默认 true
    """
    outcome = yield
    report = outcome.get_result()

    # 只处理测试执行阶段（call）
    if report.when == "call":
        # 检查是否是 UI 测试（有 page 或 context fixture，同步或异步）
        is_ui_test = any(
            fixture_name in item.funcargs
            for fixture_name in ["page", "async_page", "context", "async_context"]
        )
        if is_ui_test:
            _handle_ui_test_result(item, report)


def _handle_ui_test_result(item, report):
    """处理 UI 测试结果（失败或成功）

    Args:
        item: pytest 测试项
        report: pytest 测试报告
    """
    # 获取配置
    config = _get_failure_config(item.config)

    # 获取 page 和 context（同步或异步）
    page = item.funcargs.get("page") or item.funcargs.get("async_page")
    context = item.funcargs.get("context") or item.funcargs.get("async_context")

    if report.failed:
        # ========== 失败处理 ==========
        if page and config["screenshot_on_failure"]:
            _take_failure_screenshot(page, item, config)

        if page or context:
            _handle_video_on_failure(page, context, config)
    else:
        # ========== 成功处理 ==========
        # 根据录制模式决定是否删除视频
        if config["record_video"] == "retain-on-failure":
            video_path = _get_video_path(page, context)
            if video_path:
                _delete_video_file(video_path)
        elif config["record_video"] == "on-first-retry":
            # 非重试时删除视频
            if not _is_first_retry(item):
                video_path = _get_video_path(page, context)
                if video_path:
                    _delete_video_file(video_path)


def _get_failure_config(pytest_config):
    """获取失败诊断配置

    优先级: WebConfig > 默认值

    Args:
        pytest_config: pytest Config 对象

    Returns:
        dict: 失败诊断配置
    """
    settings = getattr(pytest_config, "_df_settings", None)

    if settings and hasattr(settings, "web") and settings.web:
        web_config = settings.web
        return {
            "screenshot_on_failure": getattr(web_config, "screenshot_on_failure", True),
            "screenshot_dir": getattr(web_config, "screenshot_dir", "reports/screenshots"),
            "record_video": getattr(web_config, "record_video", False),
            "attach_to_allure": getattr(web_config, "attach_to_allure", True),
        }

    # 默认配置
    return {
        "screenshot_on_failure": True,
        "screenshot_dir": "reports/screenshots",
        "record_video": False,
        "attach_to_allure": True,
    }


def _take_failure_screenshot(page, item, config):
    """失败时自动截图（同步/异步兼容）

    v4.0.0: 支持同步和异步 page

    Args:
        page: Playwright Page 对象（同步或异步）
        item: pytest 测试项
        config: 失败诊断配置
    """
    from pathlib import Path

    screenshots_dir = Path(config["screenshot_dir"])
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = screenshots_dir / f"{item.name}_failure.png"

    try:
        # 检测 page 是同步还是异步
        # 通过检查 screenshot 方法的返回值类型来判断
        import inspect

        screenshot_method = page.screenshot

        # 判断是否是异步方法
        if inspect.iscoroutinefunction(screenshot_method):
            # 异步 page - 使用 asyncio
            import asyncio

            # 在同步 hook 中运行异步操作
            try:
                # 尝试获取已存在的事件循环
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果循环正在运行（pytest-asyncio 环境），使用 run_until_complete
                    # 注意：这在某些情况下可能不工作，但我们会在 except 中捕获
                    loop.run_until_complete(screenshot_method(path=str(screenshot_path)))
                else:
                    # 创建新循环运行
                    asyncio.run(screenshot_method(path=str(screenshot_path)))
            except RuntimeError:
                # 循环正在运行时无法使用 run_until_complete，使用同步包装
                # 这种情况下截图可能无法在 hook 中完成，但至少不会崩溃
                asyncio.create_task(screenshot_method(path=str(screenshot_path)))
        else:
            # 同步 page - 直接调用
            page.screenshot(path=str(screenshot_path))

        print(f"\n📸 失败截图: {screenshot_path}")

        # 附加到 Allure
        if config["attach_to_allure"]:
            _attach_to_allure(screenshot_path, "失败截图", "png")
    except Exception as e:
        print(f"\n⚠️  截图失败: {e}")


def _handle_video_on_failure(page, context, config):
    """失败时处理视频（输出路径 + Allure 附件）

    Args:
        page: Playwright Page 对象
        context: Playwright BrowserContext 对象
        config: 失败诊断配置
    """
    video_path = _get_video_path(page, context)
    if video_path:
        print(f"\n🎬 测试视频: {video_path}")

        if config["attach_to_allure"]:
            _attach_to_allure(video_path, "测试视频", "webm")


def _get_video_path(page, context):
    """获取视频路径

    Args:
        page: Playwright Page 对象
        context: Playwright BrowserContext 对象

    Returns:
        str | None: 视频文件路径
    """
    try:
        if page and page.video:
            return page.video.path()
        elif context and context.pages:
            first_page = context.pages[0]
            if first_page.video:
                return first_page.video.path()
    except Exception:
        pass
    return None


def _delete_video_file(video_path: str) -> None:
    """删除视频文件

    Args:
        video_path: 视频文件路径
    """
    try:
        from pathlib import Path

        Path(video_path).unlink(missing_ok=True)
    except Exception:
        pass  # 静默失败，不影响测试


def _is_first_retry(item) -> bool:
    """检查是否是首次重试

    需要 pytest-rerunfailures 插件支持

    Args:
        item: pytest 测试项

    Returns:
        bool: 是否是首次重试
    """
    try:
        # pytest-rerunfailures 会在 node 上添加 execution_count 属性
        execution_count = getattr(item, "execution_count", 0)
        return execution_count == 1  # 0 是首次执行，1 是首次重试
    except Exception:
        return False


def _attach_to_allure(file_path, name, attachment_type):
    """附加到 Allure 报告

    Args:
        file_path: 文件路径
        name: 附件名称
        attachment_type: 附件类型（png/webm）
    """
    try:
        import allure

        # 映射类型
        type_map = {
            "png": allure.attachment_type.PNG,
            "webm": allure.attachment_type.WEBM,
        }

        allure.attach.file(
            str(file_path),
            name=name,
            attachment_type=type_map.get(attachment_type, allure.attachment_type.TEXT),
        )
    except ImportError:
        pass  # 未安装 allure-pytest，跳过
