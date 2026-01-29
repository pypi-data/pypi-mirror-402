"""页面对象异步基类（v4.0.0）

提供UI自动化测试的页面对象模式(POM)异步基类
基于 Playwright 异步 API 实现

v4.0.0: 异步优先
- AsyncBasePage：完全异步实现（推荐）
- 性能提升 2-3 倍
- 基于 playwright.async_api
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

try:
    from playwright.async_api import Page

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = Any


class AsyncBasePage(ABC):
    """
    页面对象异步基类（v4.0.0）

    现代 Page Object 模式的核心原则：
    1. 页面对象代表一个页面，而不是封装所有元素操作
    2. 直接使用 Playwright API 进行元素操作，不过度封装
    3. 使用语义化定位（get_by_role, get_by_label, get_by_test_id）
    4. 只封装业务操作（如 login），不封装基础操作（如 click）
    5. 组合使用 Component 来复用 UI 组件

    使用示例（v4.0.0 异步版本）:
        >>> from df_test_framework.capabilities.drivers.web import AsyncBasePage, AsyncBaseComponent
        >>>
        >>> class LoginForm(AsyncBaseComponent):
        ...     def __init__(self, page):
        ...         super().__init__(page, test_id="login-form")
        ...
        ...     async def submit(self, username: str, password: str):
        ...         await self.get_by_label("Username").fill(username)
        ...         await self.get_by_label("Password").fill(password)
        ...         await self.get_by_role("button", name="Sign in").click()
        >>>
        >>> class LoginPage(AsyncBasePage):
        ...     def __init__(self, page, runtime=None):
        ...         super().__init__(page, url="/login", runtime=runtime)
        ...         self.login_form = LoginForm(page)
        ...
        ...     async def wait_for_page_load(self):
        ...         await self.page.get_by_test_id("login-form").wait_for()
        ...
        ...     async def login(self, username: str, password: str):
        ...         await self.login_form.submit(username, password)
        >>>
        >>> # 在测试中使用
        >>> @pytest.mark.asyncio
        >>> async def test_login(page):
        ...     login_page = LoginPage(page)
        ...     await login_page.goto()
        ...     await login_page.login("admin", "password")
    """

    def __init__(
        self,
        page: Page,
        url: str | None = None,
        base_url: str | None = None,
        runtime: Any | None = None,
    ):
        """
        初始化页面对象

        Args:
            page: Playwright Page实例（异步版本）
            url: 页面相对URL（如 "/login", "/dashboard"）
            base_url: 基础URL - 如果为None且提供了runtime，则从配置读取
            runtime: RuntimeContext实例 - 用于自动读取配置

        Raises:
            ImportError: 如果未安装playwright

        Note:
            v4.0.0: 完全异步化
            参数优先级：显式传入的 base_url > runtime.settings.web.base_url > ""
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright未安装。请运行: pip install 'playwright>=1.40.0' && playwright install"
            )

        self.page = page
        self.url = url
        self.runtime = runtime

        # 自动从 runtime 读取 base_url（如果未显式提供）
        if base_url is not None:
            self.base_url = base_url
        elif runtime and hasattr(runtime, "settings") and runtime.settings.web:
            self.base_url = runtime.settings.web.base_url or ""
        else:
            self.base_url = ""

    @abstractmethod
    async def wait_for_page_load(self) -> None:
        """
        等待页面加载完成（异步）

        子类必须实现此方法来定义页面加载完成的标志。

        推荐的实现方式：
        1. 等待页面特有的元素（使用 test-id 或 role）
        2. 使用 Playwright 的自动等待机制
        3. 避免使用固定时间等待（asyncio.sleep）

        Example:
            >>> async def wait_for_page_load(self):
            ...     # 方式 1: 等待特定元素（推荐）
            ...     await self.page.get_by_test_id("dashboard").wait_for()
            ...
            ...     # 方式 2: 等待多个条件
            ...     await self.page.get_by_role("heading", name="Dashboard").wait_for()
            ...     await self.page.get_by_test_id("user-menu").wait_for()
            ...
            ...     # 方式 3: 等待网络空闲（谨慎使用）
            ...     await self.page.wait_for_load_state("networkidle")
        """
        pass

    async def goto(self, url: str | None = None, **kwargs: Any) -> None:
        """
        导航到页面（异步）

        Args:
            url: 目标URL，如果为None则使用self.url
            **kwargs: 传递给 page.goto() 的其他参数

        Raises:
            ValueError: 如果url和self.url都为None

        Example:
            >>> # 使用默认 URL
            >>> await login_page.goto()
            >>>
            >>> # 使用自定义 URL
            >>> await login_page.goto("/login?redirect=/dashboard")
            >>>
            >>> # 传递额外参数
            >>> await login_page.goto(wait_until="networkidle")
        """
        target_url = url or self.url
        if not target_url:
            raise ValueError("必须提供url参数或在构造函数中设置self.url")

        full_url = f"{self.base_url}{target_url}" if self.base_url else target_url

        await self.page.goto(full_url, **kwargs)
        await self.wait_for_page_load()

    # ========== 页面信息（便捷方法）==========

    async def get_title(self) -> str:
        """
        获取页面标题（异步）

        v4.0.0: 异步方法

        Returns:
            str: 页面标题

        Example:
            >>> title = await login_page.get_title()
        """
        return await self.page.title()

    @property
    def url_current(self) -> str:
        """
        获取当前URL（同步属性）

        Returns:
            str: 当前页面 URL
        """
        return self.page.url

    # ========== 便捷方法（可选）==========

    async def screenshot(self, path: str | Path | None = None, **kwargs: Any) -> bytes:
        """
        页面截图（异步）

        Args:
            path: 保存路径，如果为None则返回字节数据
            **kwargs: 其他截图参数（如 full_page=True）

        Returns:
            bytes: 截图数据

        Example:
            >>> # 保存到文件
            >>> await login_page.screenshot("screenshots/login.png")
            >>>
            >>> # 全页截图
            >>> await login_page.screenshot("full.png", full_page=True)
        """
        return await self.page.screenshot(path=path, **kwargs)

    async def reload(self, **kwargs: Any) -> None:
        """
        刷新页面（异步）

        Args:
            **kwargs: 传递给 page.reload() 的参数

        Example:
            >>> await login_page.reload()
        """
        await self.page.reload(**kwargs)
        await self.wait_for_page_load()


__all__ = ["AsyncBasePage"]
