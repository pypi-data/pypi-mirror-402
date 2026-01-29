"""应用业务操作异步基类（v4.0.0）

提供高级业务操作的封装基类
基于 Playwright 异步 API 实现

v4.0.0: 异步优先
- AsyncAppActions：完全异步实现（推荐）
- 性能提升 2-3 倍
- 基于 playwright.async_api
"""

from typing import Any

try:
    from playwright.async_api import Page

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = Any


class AsyncAppActions:
    """
    应用业务操作异步基类（v4.0.0）

    用于封装高级业务操作和复杂的用户流程。App Actions 是测试中最常用的抽象层，
    它将多个页面操作组合成有意义的业务操作，提高测试的可读性和可维护性。

    核心理念：
    - 封装完整的业务流程（如"登录"、"创建订单"、"用户注册"）
    - 隐藏页面导航和底层操作细节
    - 提供测试友好的 API
    - 提高测试代码复用性

    与 Page Object 的区别：
    - Page Object: 表示单个页面，封装页面元素和操作
    - App Actions: 跨页面的业务操作，封装用户完整的使用场景

    最佳实践：
    1. 每个 App Action 方法代表一个完整的业务操作
    2. 方法名应该清晰表达业务意图（如 login_as_admin, create_order）
    3. 隐藏页面导航和等待逻辑
    4. 使用有意义的参数名和默认值
    5. 在必要时返回业务结果（如创建的 ID）

    示例（v4.0.0 异步版本）:
        >>> # 定义 App Actions
        >>> class MyAppActions(AsyncAppActions):
        ...     async def login_as_admin(self):
        ...         '''管理员登录（常用操作）'''
        ...         await self.page.goto(f"{self.base_url}/login")
        ...         await self.page.get_by_label("Username").fill("admin")
        ...         await self.page.get_by_label("Password").fill("admin123")
        ...         await self.page.get_by_role("button", name="Sign in").click()
        ...         # 等待登录成功
        ...         await self.page.get_by_test_id("user-menu").wait_for()
        ...
        ...     async def create_user(self, username: str, email: str) -> str:
        ...         '''创建新用户并返回用户 ID'''
        ...         # 1. 导航到用户管理
        ...         await self.page.get_by_role("link", name="Users").click()
        ...         # 2. 打开创建对话框
        ...         await self.page.get_by_role("button", name="Add User").click()
        ...         # 3. 填写表单
        ...         await self.page.get_by_label("Username").fill(username)
        ...         await self.page.get_by_label("Email").fill(email)
        ...         # 4. 提交并等待成功
        ...         await self.page.get_by_role("button", name="Create").click()
        ...         # 5. 提取并返回用户 ID
        ...         user_id = await self.page.get_by_test_id("user-id").text_content()
        ...         return user_id
        ...
        >>> # 在测试中使用
        >>> @pytest.mark.asyncio
        >>> async def test_user_management(app_actions):
        ...     await app_actions.login_as_admin()
        ...     user_id = await app_actions.create_user("john", "john@example.com")
        ...     assert user_id is not None

    高级示例 - 组合 Page Object 和 Component:
        >>> class MyAppActions(AsyncAppActions):
        ...     def __init__(self, page, base_url=""):
        ...         super().__init__(page, base_url)
        ...         # 可以组合使用 Page Object
        ...         from .pages.login_page import LoginPage
        ...         self.login_page = LoginPage(page, base_url)
        ...
        ...     async def login_with_google(self):
        ...         '''使用 Google 账号登录'''
        ...         await self.login_page.goto()
        ...         # 点击 Google 登录按钮
        ...         await self.page.get_by_role("button", name="Sign in with Google").click()
        ...         # 在弹出窗口中操作...
        ...         # （处理复杂的第三方登录流程）
    """

    def __init__(
        self,
        page: Page,
        base_url: str | None = None,
        runtime: Any | None = None,
    ):
        """
        初始化异步 App Actions

        Args:
            page: Playwright Page 实例
            base_url: 应用的基础 URL（如 "https://example.com"）- 如果为None且提供了runtime，则从配置读取
            runtime: RuntimeContext实例 - 用于自动读取配置和可选事件发布

        Raises:
            ImportError: 如果未安装 Playwright

        Example:
            >>> # 方式1: 传统方式（向后兼容）
            >>> app_actions = MyAppActions(page, base_url="https://example.com")
            >>>
            >>> # 方式2: 使用 runtime（推荐）
            >>> app_actions = MyAppActions(page, runtime=runtime)
            >>> # base_url 自动从 runtime.settings.web.base_url 读取

        Note:
            v4.0.0: 完全异步化
            - 支持 runtime 参数
            - 如果提供 runtime 且 base_url 为 None，将从 runtime.settings.web.base_url 读取
            - 参数优先级：显式传入的 base_url > runtime.settings.web.base_url > ""
            - 子类可使用 self.runtime 来访问 RuntimeContext（可选发布细粒度事件）
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright未安装。请运行: pip install 'playwright>=1.40.0' && playwright install"
            )

        self.page = page
        self.runtime = runtime

        # 自动从 runtime 读取 base_url（如果未显式提供）
        if base_url is not None:
            self.base_url = base_url
        elif runtime and hasattr(runtime, "settings") and runtime.settings.web:
            self.base_url = runtime.settings.web.base_url or ""
        else:
            self.base_url = ""

    async def goto(self, path: str = "", **kwargs: Any) -> None:
        """
        导航到应用的指定路径（异步）

        Args:
            path: 相对于 base_url 的路径（如 "/login", "/dashboard"）
            **kwargs: 传递给 page.goto() 的其他参数

        Example:
            >>> await app_actions.goto("/login")
            >>> # 等价于 await page.goto("https://example.com/login")
        """
        url = f"{self.base_url}{path}" if path else self.base_url
        await self.page.goto(url, **kwargs)

    # ========== UI 操作辅助方法（自动记录日志）==========

    def _publish_ui_action_event(
        self, action: str, selector: str = "", value: str = "", description: str = ""
    ) -> None:
        """发布 UI 操作事件（内部方法）

        v4.0.0: 保持同步，事件发布不阻塞
        v3.46.0 新增：通过 EventBus 发布事件，统一处理调试输出和 Allure 记录

        Args:
            action: 操作类型（fill, click, select, check, wait）
            selector: 元素选择器
            value: 操作值
            description: 操作描述
        """
        # 检查 runtime 和 event_bus 是否可用
        if not self.runtime:
            return
        event_bus = getattr(self.runtime, "event_bus", None)
        if not event_bus:
            return

        from df_test_framework.core.events import UIActionEvent

        # 发布事件
        event = UIActionEvent.create(
            action=action,
            selector=selector,
            value=value,
            description=description,
            page_url=self.page.url,
        )

        # 使用 runtime.publish_event() 自动注入 scope
        self.runtime.publish_event(event)

    async def fill_input(self, selector: str, value: str, description: str = "") -> None:
        """填写输入框（异步，自动记录日志和发布事件）

        v4.0.0: 异步化
        v3.46.0 新增：与 HTTP 日志输出一致，自动记录 UI 操作

        Args:
            selector: 元素选择器（支持 Playwright 所有选择器语法）
            value: 要填写的值
            description: 操作描述（如"用户名输入框"）

        Example:
            >>> await app_actions.fill_input('input[name="username"]', 'admin', '用户名输入框')
            >>> # 调试输出：📝 填写 [用户名输入框]: admin
        """
        # 发布事件（触发 ConsoleDebugObserver 和 AllureObserver）
        self._publish_ui_action_event("fill", selector, value, description)

        # 执行操作（异步）
        locator = self.page.locator(selector)
        await locator.fill(value)

    async def click(self, selector: str, description: str = "") -> None:
        """点击元素（异步，自动记录日志和发布事件）

        v4.0.0: 异步化
        v3.46.0 新增：与 HTTP 日志输出一致，自动记录 UI 操作

        Args:
            selector: 元素选择器（支持 Playwright 所有选择器语法）
            description: 操作描述（如"登录按钮"）

        Example:
            >>> await app_actions.click('button[type="submit"]', '登录按钮')
            >>> # 调试输出：👆 点击 [登录按钮]
        """
        # 发布事件
        self._publish_ui_action_event("click", selector, "", description)

        # 执行操作（异步）
        locator = self.page.locator(selector)
        await locator.click()

    async def select_option(self, selector: str, value: str, description: str = "") -> None:
        """选择下拉选项（异步，自动记录日志和发布事件）

        v4.0.0: 异步化
        v3.46.0 新增：与 HTTP 日志输出一致，自动记录 UI 操作

        Args:
            selector: 元素选择器
            value: 要选择的值
            description: 操作描述（如"省份下拉框"）

        Example:
            >>> await app_actions.select_option('select[name="province"]', '广东省', '省份下拉框')
            >>> # 调试输出：🎯 选择 [省份下拉框]: 广东省
        """
        # 发布事件
        self._publish_ui_action_event("select", selector, value, description)

        # 执行操作（异步）
        locator = self.page.locator(selector)
        await locator.select_option(value)

    async def check(self, selector: str, description: str = "") -> None:
        """勾选复选框（异步，自动记录日志和发布事件）

        v4.0.0: 异步化
        v3.46.0 新增：与 HTTP 日志输出一致，自动记录 UI 操作

        Args:
            selector: 元素选择器
            description: 操作描述（如"记住密码"）

        Example:
            >>> await app_actions.check('input[name="remember"]', '记住密码')
            >>> # 调试输出：☑️  勾选 [记住密码]
        """
        # 发布事件
        self._publish_ui_action_event("check", selector, "", description)

        # 执行操作（异步）
        locator = self.page.locator(selector)
        await locator.check()

    async def wait_for_text(self, text: str, timeout: int | None = None) -> None:
        """等待文本出现（异步，自动记录日志和发布事件）

        v4.0.0: 异步化
        v3.46.0 新增：与 HTTP 日志输出一致，自动记录 UI 操作

        Args:
            text: 要等待的文本
            timeout: 超时时间（毫秒），None 使用默认超时

        Example:
            >>> await app_actions.wait_for_text('登录成功')
            >>> # 调试输出：⏳ 等待文本出现: 登录成功
        """
        # 发布事件
        self._publish_ui_action_event("wait", "", text, "等待文本")

        # 执行操作（异步）
        await self.page.get_by_text(text).wait_for(timeout=timeout)


__all__ = ["AsyncAppActions"]
