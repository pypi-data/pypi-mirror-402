"""组件基类

提供可复用 UI 组件的封装基类
基于 Playwright 实现

v3.43.0: 新增 - 现代 UI 测试最佳实践
"""

from typing import Any

try:
    from playwright.sync_api import Locator, Page

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = Any
    Locator = Any


class BaseComponent:
    """
    UI 组件基类

    用于封装页面中的可复用组件（如 Header, Footer, LoginForm 等）。
    组件应该是独立的、可测试的、可在多个页面中复用的 UI 单元。

    核心特性：
    - 组件级别的定位（基于 test-id）
    - 语义化元素定位（role, label, text）
    - 组件内部元素相对定位
    - 支持嵌套组件

    最佳实践：
    1. 每个组件对应一个独立的 UI 单元（如表单、导航栏、对话框）
    2. 使用 test-id 定位组件根元素
    3. 组件内元素使用语义化定位（role, label）
    4. 只封装组件的业务操作，不封装单个元素操作

    示例:
        >>> # 定义组件
        >>> class LoginForm(BaseComponent):
        ...     def __init__(self, page: Page):
        ...         super().__init__(page, test_id="login-form")
        ...
        ...     def submit(self, username: str, password: str):
        ...         '''填写并提交登录表单'''
        ...         self.get_by_label("Username").fill(username)
        ...         self.get_by_label("Password").fill(password)
        ...         self.get_by_role("button", name="Sign in").click()
        ...
        >>> # 使用组件
        >>> login_form = LoginForm(page)
        >>> login_form.submit("admin", "password")

        >>> # 嵌套组件
        >>> class UserMenu(BaseComponent):
        ...     def __init__(self, page: Page):
        ...         super().__init__(page, test_id="user-menu")
        ...
        >>> class Header(BaseComponent):
        ...     def __init__(self, page: Page):
        ...         super().__init__(page, test_id="header")
        ...         self.user_menu = UserMenu(page)
    """

    def __init__(self, page: Page, test_id: str | None = None):
        """
        初始化组件

        Args:
            page: Playwright Page 实例
            test_id: 组件根元素的 test-id（data-testid 属性值）
                    如果为 None，则组件范围为整个页面

        Raises:
            ImportError: 如果未安装 Playwright

        Example:
            >>> # 有 test-id 的组件
            >>> login_form = BaseComponent(page, test_id="login-form")
            >>>
            >>> # 无 test-id（整个页面）
            >>> full_page = BaseComponent(page)
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright未安装。请运行: pip install playwright && playwright install"
            )

        self.page = page
        self.test_id = test_id

        # 组件根元素
        # 如果提供了 test_id，则限定在该组件范围内
        # 否则组件范围为整个页面
        self.root: Locator | Page = page.get_by_test_id(test_id) if test_id else page

    # ========== Playwright 现代定位方法 ==========
    # 所有定位都基于组件根元素（self.root）

    def get_by_test_id(self, test_id: str) -> Locator:
        """
        通过 test-id 定位元素（推荐 - 优先级 1）

        Test ID 是最稳定的定位方式，专为测试设计，不会因为
        UI 样式变化而失效。

        Args:
            test_id: data-testid 属性值

        Returns:
            Locator: 定位器

        Example:
            >>> # HTML: <button data-testid="submit-btn">Submit</button>
            >>> button = component.get_by_test_id("submit-btn")
            >>> button.click()
        """
        return self.root.get_by_test_id(test_id)

    def get_by_role(self, role: str, *, name: str | None = None, **kwargs: Any) -> Locator:
        """
        通过 ARIA role 定位元素（推荐 - 优先级 2）

        基于可访问性属性定位，既有利于测试，也能验证页面的可访问性。

        Args:
            role: ARIA role（如 "button", "link", "textbox", "heading"）
            name: 可访问名称（通常是元素的文本内容或 aria-label）
            **kwargs: 其他 Playwright 定位选项

        Returns:
            Locator: 定位器

        Example:
            >>> # 定位按钮
            >>> button = component.get_by_role("button", name="Submit")
            >>> button.click()
            >>>
            >>> # 定位链接
            >>> link = component.get_by_role("link", name="Dashboard")
            >>> link.click()
            >>>
            >>> # 定位标题
            >>> heading = component.get_by_role("heading", name="Welcome")
        """
        return self.root.get_by_role(role, name=name, **kwargs)

    def get_by_label(self, text: str, **kwargs: Any) -> Locator:
        """
        通过 label 文本定位表单元素（推荐 - 优先级 3）

        适用于有 <label> 标签的表单字段。

        Args:
            text: label 文本内容
            **kwargs: 其他 Playwright 定位选项

        Returns:
            Locator: 定位器

        Example:
            >>> # HTML: <label>Username <input /></label>
            >>> username = component.get_by_label("Username")
            >>> username.fill("admin")
        """
        return self.root.get_by_label(text, **kwargs)

    def get_by_placeholder(self, text: str, **kwargs: Any) -> Locator:
        """
        通过 placeholder 定位输入框（备选 - 优先级 4）

        Args:
            text: placeholder 文本
            **kwargs: 其他 Playwright 定位选项

        Returns:
            Locator: 定位器

        Example:
            >>> # HTML: <input placeholder="Enter email" />
            >>> email = component.get_by_placeholder("Enter email")
            >>> email.fill("user@example.com")
        """
        return self.root.get_by_placeholder(text, **kwargs)

    def get_by_text(self, text: str, **kwargs: Any) -> Locator:
        """
        通过文本内容定位元素（备选 - 优先级 5）

        Args:
            text: 元素的文本内容
            **kwargs: 其他 Playwright 定位选项

        Returns:
            Locator: 定位器

        Example:
            >>> # 定位包含特定文本的元素
            >>> element = component.get_by_text("Welcome back")
            >>> assert element.is_visible()
        """
        return self.root.get_by_text(text, **kwargs)

    def locator(self, selector: str) -> Locator:
        """
        使用 CSS 或 XPath 选择器定位元素（最后选择 - 优先级 6）

        注意：CSS/XPath 选择器容易因为页面结构变化而失效，
        应该优先使用语义化定位方法。

        Args:
            selector: CSS 选择器或 XPath

        Returns:
            Locator: 定位器

        Example:
            >>> # 仅在其他方式无法使用时才用 CSS
            >>> element = component.locator(".some-class")
        """
        return self.root.locator(selector)

    # ========== 组件可见性检查 ==========

    def is_visible(self, timeout: int | None = None) -> bool:
        """
        检查组件是否可见

        Args:
            timeout: 超时时间（毫秒）

        Returns:
            bool: 组件是否可见

        Example:
            >>> if login_form.is_visible():
            ...     login_form.submit("user", "pass")
        """
        if isinstance(self.root, Page):
            # 整个页面没有 is_visible() 方法
            return True
        return self.root.is_visible(timeout=timeout)

    def wait_for(self, state: str = "visible", timeout: int | None = None) -> None:
        """
        等待组件达到指定状态

        Args:
            state: 状态（"visible", "hidden", "attached", "detached"）
            timeout: 超时时间（毫秒）

        Example:
            >>> login_form.wait_for(state="visible")
        """
        if isinstance(self.root, Page):
            # Page 没有 wait_for() 方法
            return
        self.root.wait_for(state=state, timeout=timeout)


__all__ = ["BaseComponent"]
