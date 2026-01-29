"""UI App Actions 模板

v4.0.0: 支持异步版本（AsyncAppActions）
v3.44.0: 应用业务操作层 + 配置驱动（runtime 支持）
v3.45.0: 支持 @actions_class 装饰器自动注册为 fixture
v3.46.0: 使用 practice.expandtesting.com 作为演示网站
"""

UI_APP_ACTIONS_TEMPLATE = '''"""应用业务操作 - practice.expandtesting.com 演示

封装高级业务操作和完整的用户流程。

演示网站: https://practice.expandtesting.com
测试账号: practice / SuperSecretPassword!

v4.0.0 新增异步版本:
- 推荐使用 AsyncAppActions 获得 2-3 倍性能提升
- 本模板使用同步版本（向后兼容）
- 异步版本示例请参考文档：docs/migration/v3-to-v4.md

异步版本示例:
    from df_test_framework.capabilities.drivers.web import AsyncAppActions

    @actions_class()
    class LoginActions(AsyncAppActions):
        async def login_with_valid_credentials(self):
            await self.goto("/login")
            await self.fill_input('input[name="username"]', "practice", "用户名")
            await self.click('button[type="submit"]', "登录按钮")

v3.45.0: 支持 @actions_class 装饰器
- 自动注册为 pytest fixture
- 支持多个 Actions 类按业务模块拆分
- 与 HTTP 的 @api_class 保持一致的使用体验

v3.46.0: 支持 UI 操作辅助方法
- fill_input(), click(), select_option() 等辅助方法
- 自动发布 UIActionEvent 事件，输出调试信息
- 与 HTTP 测试一致的可观测性

三种操作方式演示:
    1. LoginActions: Playwright API + 手动发布事件
    2. NotesActions: 辅助方法（自动发布事件）
    3. SecurePageActions: 混合使用

使用方式:
    # 方式 1: 使用 @actions_class 装饰器（推荐）
    >>> @actions_class()  # 自动命名为 login_actions
    >>> class LoginActions(AppActions):
    ...     def login_with_valid_credentials(self):
    ...         ...

    # 方式 2: 在 conftest.py 中手动定义 fixture
    >>> @pytest.fixture
    >>> def login_actions(page, browser_manager):
    ...     return LoginActions(page, base_url=browser_manager.base_url)
"""

from df_test_framework.capabilities.drivers.web import AppActions
from df_test_framework.testing.decorators import actions_class


# ========== 登录相关操作（演示：Playwright API + 手动发布事件）==========

@actions_class()  # 自动命名为 login_actions
class LoginActions(AppActions):
    """登录相关业务操作

    演示：使用 Playwright 原生 API + 手动发布事件
    适用场景：复杂元素定位、需要自定义事件描述

    测试账号:
        - Username: practice
        - Password: SuperSecretPassword!

    使用示例:
        >>> def test_login(login_actions):
        ...     login_actions.login_with_valid_credentials()
        ...     assert login_actions.is_logged_in()
    """

    def login_with_valid_credentials(self):
        """使用有效凭证登录

        演示：Playwright API + 手动发布事件
        - 使用 Playwright 原生 API 进行元素操作
        - 手动调用 _publish_ui_action_event() 发布事件
        - 自定义事件描述，输出调试信息

        调试输出示例:
            ────────────────────────────────────────────────────────
            📝 填写 [用户名输入框]: practice
            ────────────────────────────────────────────────────────
            📝 填写 [密码输入框]: SuperSecretPassword!
            ────────────────────────────────────────────────────────
            👆 点击 [登录按钮]
            ────────────────────────────────────────────────────────
        """
        # 导航到登录页
        self.goto("/login")

        # ✅ 方式：Playwright API + 手动发布事件
        # 优点：精确控制、自定义事件描述
        # 缺点：需要手动发布事件

        # 填写用户名
        username_input = self.page.locator('input[name="username"]')
        self._publish_ui_action_event("fill", value="practice", description="用户名输入框")
        username_input.fill("practice")

        # 填写密码
        password_input = self.page.locator('input[name="password"]')
        self._publish_ui_action_event("fill", value="SuperSecretPassword!", description="密码输入框")
        password_input.fill("SuperSecretPassword!")

        # 点击登录按钮
        login_button = self.page.locator('button[type="submit"]')
        self._publish_ui_action_event("click", description="登录按钮")
        login_button.click()

        # 等待跳转到安全页面
        self.page.wait_for_url("**/secure", timeout=5000)

    def login_as_user(self, username: str, password: str):
        """使用指定凭证登录

        演示：纯 Playwright API（无事件发布）
        适用场景：不需要调试输出的简单操作

        Args:
            username: 用户名
            password: 密码

        示例:
            >>> login_actions.login_as_user("practice", "SuperSecretPassword!")
        """
        self.goto("/login")

        # ✅ 纯 Playwright API（无事件发布）
        # 优点：代码简洁
        # 缺点：无调试输出和 Allure 记录

        self.page.locator('input[name="username"]').fill(username)
        self.page.locator('input[name="password"]').fill(password)
        self.page.locator('button[type="submit"]').click()

        # 等待跳转
        self.page.wait_for_url("**/secure", timeout=5000)

    def logout(self):
        """登出操作

        示例:
            >>> login_actions.logout()
        """
        # 点击登出按钮
        logout_button = self.page.locator('a[href="/logout"]')
        self._publish_ui_action_event("click", description="登出按钮")
        logout_button.click()

        # 等待跳转回登录页
        self.page.wait_for_url("**/login", timeout=5000)

    def is_logged_in(self) -> bool:
        """检查是否已登录

        Returns:
            bool: 是否在安全页面（已登录状态）
        """
        return "/secure" in self.page.url

    def get_success_message(self) -> str:
        """获取登录成功消息

        Returns:
            str: 成功消息文本
        """
        return self.page.locator('.alert-success').text_content() or ""


# ========== Notes 应用操作（演示：辅助方法 - 自动发布事件）==========

@actions_class()  # 自动命名为 notes_actions
class NotesActions(AppActions):
    """Notes 应用业务操作

    演示：使用辅助方法（自动发布事件）
    适用场景：常规表单操作、需要统一调试输出

    Notes 应用地址: /notes/app
    功能: 创建、编辑、删除、搜索笔记

    使用示例:
        >>> def test_create_note(notes_actions):
        ...     note_id = notes_actions.create_note("标题", "内容")
        ...     assert note_id is not None
    """

    def navigate_to_notes_app(self):
        """导航到 Notes 应用

        注意: Notes 应用可能需要先登录或注册
        """
        self.goto("/notes/app")

    def create_note(self, title: str, description: str, category: str = "Home") -> str:
        """创建新笔记

        演示：使用辅助方法（推荐）
        - fill_input(): 自动发布 UIActionEvent
        - click(): 自动发布 UIActionEvent
        - 自动输出彩色调试信息

        Args:
            title: 笔记标题
            description: 笔记内容
            category: 分类（Home/Work/Personal）

        Returns:
            str: 创建的笔记ID或标题

        调试输出示例:
            ────────────────────────────────────────────────────────
            👆 点击 [添加笔记按钮]
            ────────────────────────────────────────────────────────
            📝 填写 [标题输入框]: 我的第一条笔记
            ────────────────────────────────────────────────────────
            📝 填写 [内容输入框]: 这是笔记内容
            ────────────────────────────────────────────────────────
        """
        # ✅ 使用辅助方法（推荐）
        # 优点：代码简洁、自动发布事件、统一调试输出
        # 适用：常规表单操作

        # 点击添加笔记按钮
        self.click('button[data-testid="add-note"]', "添加笔记按钮")

        # 填写表单
        self.fill_input('input[id="title"]', title, "标题输入框")
        self.fill_input('textarea[id="description"]', description, "内容输入框")
        self.select_option('select[id="category"]', category, "分类下拉框")

        # 提交
        self.click('button[data-testid="submit-note"]', "创建笔记按钮")

        # 等待笔记出现
        self.wait_for_text(title, timeout=5000)

        return title

    def edit_note(self, note_title: str, new_description: str):
        """编辑笔记

        Args:
            note_title: 要编辑的笔记标题
            new_description: 新的笔记内容

        示例:
            >>> notes_actions.edit_note("我的笔记", "更新后的内容")
        """
        # 找到笔记并点击编辑
        note_card = self.page.locator(f'div[data-note-title="{note_title}"]')
        edit_button = note_card.locator('button[data-action="edit"]')
        self._publish_ui_action_event("click", description=f"编辑笔记 [{note_title}]")
        edit_button.click()

        # 使用辅助方法更新内容
        self.fill_input('textarea[id="description"]', new_description, "内容输入框")
        self.click('button[data-testid="save-note"]', "保存按钮")

        # 等待保存成功
        self.wait_for_text("Note updated", timeout=3000)

    def delete_note(self, note_title: str):
        """删除笔记

        Args:
            note_title: 要删除的笔记标题

        示例:
            >>> notes_actions.delete_note("我的笔记")
        """
        # 找到笔记并点击删除
        note_card = self.page.locator(f'div[data-note-title="{note_title}"]')
        delete_button = note_card.locator('button[data-action="delete"]')

        self._publish_ui_action_event("click", description=f"删除笔记 [{note_title}]")
        delete_button.click()

        # 确认删除（如果有确认对话框）
        confirm_button = self.page.locator('button[data-testid="confirm-delete"]')
        if confirm_button.is_visible(timeout=1000):
            self.click('button[data-testid="confirm-delete"]', "确认删除")

    def search_notes(self, keyword: str) -> int:
        """搜索笔记

        Args:
            keyword: 搜索关键词

        Returns:
            int: 搜索结果数量

        示例:
            >>> count = notes_actions.search_notes("重要")
            >>> print(f"找到 {count} 条笔记")
        """
        # 使用辅助方法填写搜索框
        self.fill_input('input[data-testid="search-notes"]', keyword, "搜索框")

        # 等待搜索结果更新
        self.page.wait_for_timeout(1000)

        # 统计结果数量
        results = self.page.locator('div[data-testid="note-card"]').count()
        return results


# ========== 安全页面操作（演示：混合使用）==========

@actions_class()  # 自动命名为 secure_page_actions
class SecurePageActions(AppActions):
    """安全页面操作

    演示：混合使用辅助方法和 Playwright API
    适用场景：复杂业务流程，根据需求选择合适的方式

    使用示例:
        >>> def test_secure_area(login_actions, secure_page_actions):
        ...     login_actions.login_with_valid_credentials()
        ...     message = secure_page_actions.get_welcome_message()
        ...     assert "secure area" in message.lower()
    """

    def get_welcome_message(self) -> str:
        """获取欢迎消息

        演示：纯 Playwright API（简单查询操作无需事件）

        Returns:
            str: 欢迎消息文本
        """
        # ✅ 简单查询操作，使用原生 API 即可
        return self.page.locator('.alert-success').text_content() or ""

    def verify_on_secure_page(self) -> bool:
        """验证是否在安全页面

        Returns:
            bool: 是否在安全页面
        """
        return "/secure" in self.page.url

    def perform_secure_action(self, action_name: str):
        """执行安全区域的某个操作

        演示：混合使用
        - 简单操作用 Playwright API
        - 复杂操作用辅助方法

        Args:
            action_name: 操作名称
        """
        # 使用辅助方法点击操作按钮（自动发布事件）
        self.click(f'button[data-action="{action_name}"]', f"{action_name} 按钮")

        # 使用原生 API 等待结果
        self.page.wait_for_selector('.result-message', timeout=5000)


# ========== 通用应用操作（可选）==========

@actions_class("{project_name}_actions")  # 显式命名
class {ProjectName}AppActions(AppActions):
    """{project_name} 通用应用操作

    如果需要一个包含所有操作的统一入口，可以使用此类。
    但推荐按业务模块拆分为多个 Actions 类（如上述示例）。

    使用示例:
        >>> def test_full_flow({project_name}_actions):
        ...     {project_name}_actions.login()
        ...     {project_name}_actions.create_note("标题", "内容")
    """

    def login(self):
        """快速登录"""
        self.goto("/login")
        self.page.locator('input[name="username"]').fill("practice")
        self.page.locator('input[name="password"]').fill("SuperSecretPassword!")
        self.page.locator('button[type="submit"]').click()
        self.page.wait_for_url("**/secure", timeout=5000)

    def create_note(self, title: str, description: str) -> str:
        """快速创建笔记"""
        self.goto("/notes/app")
        self.click('button[data-testid="add-note"]', "添加笔记")
        self.fill_input('input[id="title"]', title, "标题")
        self.fill_input('textarea[id="description"]', description, "内容")
        self.click('button[data-testid="submit-note"]', "创建")
        return title


__all__ = ["LoginActions", "NotesActions", "SecurePageActions", "{ProjectName}AppActions"]
'''

__all__ = ["UI_APP_ACTIONS_TEMPLATE"]
