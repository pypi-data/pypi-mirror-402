"""UI页面对象模板

v3.44.0: 现代UI测试最佳实践 + 配置驱动
- Component + Page Object 模式
- 语义化定位（test-id, role, label）
- 直接使用 Playwright API
- 支持 runtime 注入，自动读取 base_url
v3.46.0: 使用 practice.expandtesting.com 演示三层架构
"""

UI_PAGE_OBJECT_TEMPLATE = '''"""页面对象示例 - practice.expandtesting.com

演示现代 Page Object 模式 + Component 组件化。

演示网站: https://practice.expandtesting.com
测试账号: practice / SuperSecretPassword!

v3.43.0: 采用现代UI测试最佳实践
- 使用 BaseComponent 封装可复用组件
- 使用 BasePage 表示页面
- 语义化定位优先（CSS selector）
- 直接使用 Playwright API，不过度封装

v3.46.0: 完整示例
- LoginPage: 登录页面
- LoginForm: 登录表单组件
- AlertMessage: 消息组件
"""

from df_test_framework.capabilities.drivers.web import BasePage, BaseComponent


# ==========================================================================
# 组件定义 - 封装可复用的 UI 组件
# ==========================================================================

class LoginForm(BaseComponent):
    """登录表单组件

    封装登录表单的交互逻辑，可在多个地方复用。

    示例:
        >>> form = LoginForm(page)
        >>> form.fill_username("practice")
        >>> form.fill_password("SuperSecretPassword!")
        >>> form.submit()
    """

    def __init__(self, page):
        """初始化组件

        Args:
            page: Playwright Page 实例
        """
        # 使用 CSS 选择器定位表单容器
        # practice.expandtesting.com 的登录表单使用 id="login"
        super().__init__(page, css_selector='#login')

    def fill_username(self, username: str):
        """填写用户名

        Args:
            username: 用户名

        示例:
            >>> form.fill_username("practice")
        """
        # 使用 name 属性定位输入框
        self.root.locator('input[name="username"]').fill(username)

    def fill_password(self, password: str):
        """填写密码

        Args:
            password: 密码

        示例:
            >>> form.fill_password("SuperSecretPassword!")
        """
        # 使用 name 属性定位输入框
        self.root.locator('input[name="password"]').fill(password)

    def submit(self):
        """提交表单

        示例:
            >>> form.submit()
        """
        # 使用 type 属性定位提交按钮
        self.root.locator('button[type="submit"]').click()

    def login(self, username: str, password: str):
        """一键登录（组合操作）

        Args:
            username: 用户名
            password: 密码

        示例:
            >>> form.login("practice", "SuperSecretPassword!")
        """
        self.fill_username(username)
        self.fill_password(password)
        self.submit()


class AlertMessage(BaseComponent):
    """消息提示组件

    封装页面上的 alert 消息（成功、错误等）。

    示例:
        >>> alert = AlertMessage(page)
        >>> message = alert.get_text()
        >>> assert "secure area" in message.lower()
    """

    def __init__(self, page, alert_type: str = "success"):
        """初始化组件

        Args:
            page: Playwright Page 实例
            alert_type: 消息类型（success/error/warning/info）
        """
        # 使用 class 定位 alert 元素
        super().__init__(page, css_selector=f'.alert-{alert_type}')

    def get_text(self) -> str:
        """获取消息文本

        Returns:
            str: 消息内容

        示例:
            >>> text = alert.get_text()
            >>> print(text)
        """
        return self.root.text_content() or ""

    def is_visible(self) -> bool:
        """检查消息是否可见

        Returns:
            bool: 是否可见

        示例:
            >>> if alert.is_visible():
            >>>     print(alert.get_text())
        """
        return self.root.is_visible(timeout=2000)

    def close(self):
        """关闭消息（如果有关闭按钮）

        示例:
            >>> alert.close()
        """
        close_button = self.root.locator('button.close')
        if close_button.is_visible():
            close_button.click()


# ==========================================================================
# 页面定义 - 表示具体页面
# ==========================================================================

class LoginPage(BasePage):
    """登录页面对象

    页面 URL: /login
    测试账号: practice / SuperSecretPassword!

    使用示例:
        >>> # 方式 1: 使用 runtime 自动读取 base_url（推荐）
        >>> login_page = LoginPage(page, runtime=runtime)
        >>> login_page.goto()
        >>> login_page.login("practice", "SuperSecretPassword!")
        >>>
        >>> # 方式 2: 显式传入 base_url
        >>> login_page = LoginPage(page, base_url="https://practice.expandtesting.com")
        >>> login_page.goto()
        >>> login_page.login("practice", "SuperSecretPassword!")
    """

    def __init__(self, page, runtime=None, base_url: str | None = None):
        """初始化页面对象

        Args:
            page: Playwright Page 实例
            runtime: RuntimeContext（可选，自动读取 base_url）
            base_url: 基础 URL（显式传入时优先）
        """
        super().__init__(page, url="/login", base_url=base_url, runtime=runtime)

        # 组合使用组件
        self.login_form = LoginForm(page)
        self.success_alert = AlertMessage(page, alert_type="success")
        self.error_alert = AlertMessage(page, alert_type="error")

    def wait_for_page_load(self):
        """等待页面加载完成

        等待登录表单出现，表示页面已加载。
        """
        self.page.locator('#login').wait_for(state="visible")

    # ========== 业务操作 ==========

    def login(self, username: str, password: str):
        """执行登录操作

        Args:
            username: 用户名
            password: 密码

        示例:
            >>> login_page.login("practice", "SuperSecretPassword!")
        """
        self.login_form.login(username, password)

        # 等待页面跳转
        self.page.wait_for_url("**/secure", timeout=5000)

    def login_expect_error(self, username: str, password: str) -> str:
        """执行登录操作并期望失败

        Args:
            username: 用户名
            password: 密码

        Returns:
            str: 错误消息

        示例:
            >>> error = login_page.login_expect_error("invalid", "wrong")
            >>> assert "Invalid" in error
        """
        self.login_form.login(username, password)

        # 等待错误消息出现
        self.error_alert.root.wait_for(state="visible", timeout=3000)

        # 返回错误消息
        return self.error_alert.get_text()

    def get_page_title(self) -> str:
        """获取页面标题

        Returns:
            str: 页面标题文本

        示例:
            >>> title = login_page.get_page_title()
            >>> assert "Login" in title
        """
        return self.page.locator('h2').text_content() or ""


class SecurePage(BasePage):
    """安全页面对象（登录后的页面）

    页面 URL: /secure

    使用示例:
        >>> secure_page = SecurePage(page, runtime=runtime)
        >>> message = secure_page.get_welcome_message()
        >>> assert "secure area" in message.lower()
    """

    def __init__(self, page, runtime=None, base_url: str | None = None):
        """初始化页面对象

        Args:
            page: Playwright Page 实例
            runtime: RuntimeContext（可选，自动读取 base_url）
            base_url: 基础 URL（显式传入时优先）
        """
        super().__init__(page, url="/secure", base_url=base_url, runtime=runtime)

        # 组合使用组件
        self.success_alert = AlertMessage(page, alert_type="success")

    def wait_for_page_load(self):
        """等待页面加载完成

        等待成功消息出现。
        """
        self.success_alert.root.wait_for(state="visible")

    # ========== 业务操作 ==========

    def get_welcome_message(self) -> str:
        """获取欢迎消息

        Returns:
            str: 欢迎消息文本

        示例:
            >>> message = secure_page.get_welcome_message()
            >>> print(message)  # "You logged into a secure area!"
        """
        return self.success_alert.get_text()

    def logout(self):
        """执行登出操作

        示例:
            >>> secure_page.logout()
        """
        logout_link = self.page.locator('a[href="/logout"]')
        logout_link.click()

        # 等待跳转回登录页
        self.page.wait_for_url("**/login", timeout=5000)


__all__ = ["LoginPage", "SecurePage", "LoginForm", "AlertMessage"]
'''

__all__ = ["UI_PAGE_OBJECT_TEMPLATE"]
