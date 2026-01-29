"""UI测试示例模板

v3.44.0: 现代UI测试最佳实践 + 配置驱动（runtime/test_runtime）
v3.45.0: 支持 @actions_class 装饰器，多 Actions 模式
v3.46.0: 使用 practice.expandtesting.com 作为演示网站
"""

UI_TEST_EXAMPLE_TEMPLATE = '''"""UI测试示例 - practice.expandtesting.com 演示

演示现代UI测试最佳实践和框架的各种功能。

演示网站: https://practice.expandtesting.com
测试账号: practice / SuperSecretPassword!

v3.45.0: 支持多 Actions 模式
- 使用 @actions_class 装饰器自动注册 Actions 为 fixture
- 按业务模块拆分 Actions（LoginActions, NotesActions 等）
- 与 HTTP 的 @api_class 保持一致的使用体验

v3.46.0: 演示三种操作方式
- LoginActions: Playwright API + 手动发布事件
- NotesActions: 辅助方法（自动发布事件）
- SecurePageActions: 混合使用

Actions 自动发现:
- 在 {project_name}/actions/ 目录下创建 Actions 类
- 使用 @actions_class() 装饰器
- conftest.py 中的 load_actions_fixtures() 自动加载
- 测试中直接使用 fixture（如 login_actions, notes_actions）
"""

import pytest


# ============================================================
# 登录功能测试 - 演示 Playwright API + 手动发布事件
# ============================================================

class TestLogin:
    """登录功能测试

    演示：
    - 使用 login_actions fixture（@actions_class 自动注册）
    - Playwright API + 手动发布事件
    - 验证登录成功和失败场景
    """

    @pytest.mark.ui
    def test_login_with_valid_credentials(self, login_actions):
        """测试有效凭证登录

        验证点:
        - 登录成功后跳转到 /secure 页面
        - 显示成功消息
        - 可以获取欢迎消息

        调试输出示例（需要 pytest -s）:
            📝 填写 [用户名输入框]: practice
            📝 填写 [密码输入框]: SuperSecretPassword!
            👆 点击 [登录按钮]
        """
        # 执行登录
        login_actions.login_with_valid_credentials()

        # 验证登录成功
        assert login_actions.is_logged_in(), "应该已登录"
        assert "secure area" in login_actions.get_success_message().lower()

    @pytest.mark.ui
    def test_login_with_invalid_username(self, login_actions):
        """测试无效用户名登录

        验证点:
        - 显示错误消息
        - 停留在登录页面
        """
        login_actions.login_as_user("invalid_user", "SuperSecretPassword!")

        # 验证仍在登录页面（登录失败）
        assert not login_actions.is_logged_in(), "不应该登录成功"

    @pytest.mark.ui
    def test_logout(self, login_actions):
        """测试登出功能

        验证点:
        - 登出后返回登录页
        - 不再处于登录状态
        """
        # 先登录
        login_actions.login_with_valid_credentials()
        assert login_actions.is_logged_in()

        # 执行登出
        login_actions.logout()

        # 验证已登出
        assert not login_actions.is_logged_in(), "应该已登出"


# ============================================================
# Notes 应用测试 - 演示辅助方法（自动发布事件）
# ============================================================

class TestNotesApp:
    """Notes 应用测试

    演示：
    - 使用 notes_actions fixture（@actions_class 自动注册）
    - 辅助方法自动发布事件、输出调试信息
    - CRUD 操作（创建、编辑、删除、搜索）

    注意: Notes 应用可能需要先注册或登录
    """

    @pytest.mark.ui
    @pytest.mark.skip(reason="Notes 应用需要先注册账号，根据实际情况调整")
    def test_create_note(self, notes_actions):
        """测试创建笔记

        验证点:
        - 笔记创建成功
        - 笔记标题显示在列表中

        调试输出示例（需要 pytest -s）:
            👆 点击 [添加笔记按钮]
            📝 填写 [标题输入框]: 我的第一条笔记
            📝 填写 [内容输入框]: 这是笔记内容
            📋 选择 [分类下拉框]: Home
            👆 点击 [创建笔记按钮]
        """
        # 导航到 Notes 应用
        notes_actions.navigate_to_notes_app()

        # 创建笔记
        title = "测试笔记"
        description = "这是一条测试笔记的内容"
        result = notes_actions.create_note(title, description, category="Home")

        # 验证创建成功
        assert result == title

    @pytest.mark.ui
    @pytest.mark.skip(reason="Notes 应用需要先注册账号，根据实际情况调整")
    def test_edit_note(self, notes_actions):
        """测试编辑笔记

        验证点:
        - 笔记内容更新成功
        - 显示更新成功消息
        """
        notes_actions.navigate_to_notes_app()

        # 先创建一条笔记
        title = "待编辑笔记"
        notes_actions.create_note(title, "原始内容")

        # 编辑笔记
        new_description = "更新后的内容"
        notes_actions.edit_note(title, new_description)

        # 验证更新成功（可以通过查找更新后的内容）
        page = notes_actions.page
        assert page.get_by_text(new_description).is_visible()

    @pytest.mark.ui
    @pytest.mark.skip(reason="Notes 应用需要先注册账号，根据实际情况调整")
    def test_delete_note(self, notes_actions):
        """测试删除笔记

        验证点:
        - 笔记删除成功
        - 笔记不再显示在列表中
        """
        notes_actions.navigate_to_notes_app()

        # 先创建一条笔记
        title = "待删除笔记"
        notes_actions.create_note(title, "即将被删除")

        # 删除笔记
        notes_actions.delete_note(title)

        # 验证笔记已删除
        page = notes_actions.page
        assert not page.get_by_text(title).is_visible()

    @pytest.mark.ui
    @pytest.mark.skip(reason="Notes 应用需要先注册账号，根据实际情况调整")
    def test_search_notes(self, notes_actions):
        """测试搜索笔记

        验证点:
        - 搜索返回匹配的笔记
        - 不匹配的笔记被过滤
        """
        notes_actions.navigate_to_notes_app()

        # 创建多条笔记
        notes_actions.create_note("重要会议", "明天上午10点")
        notes_actions.create_note("购物清单", "买牛奶和面包")

        # 搜索"重要"
        count = notes_actions.search_notes("重要")

        # 验证搜索结果
        assert count >= 1, "应该至少找到一条笔记"


# ============================================================
# 安全页面测试 - 演示混合使用
# ============================================================

class TestSecurePage:
    """安全页面测试

    演示：
    - 组合使用多个 Actions（login_actions + secure_page_actions）
    - 混合使用辅助方法和 Playwright API
    """

    @pytest.mark.ui
    def test_access_secure_page(self, login_actions, secure_page_actions):
        """测试访问安全页面

        验证点:
        - 登录后可以访问安全页面
        - 显示欢迎消息
        """
        # 登录
        login_actions.login_with_valid_credentials()

        # 验证在安全页面
        assert secure_page_actions.verify_on_secure_page()

        # 获取欢迎消息
        message = secure_page_actions.get_welcome_message()
        assert "secure area" in message.lower()


# ============================================================
# Page Object 模式测试（可选）
# ============================================================

class TestWithPageObject:
    """使用 Page Object 模式的测试

    演示：
    - 三层架构（Actions + Pages + Components）
    - 适用于需要精细控制页面元素的场景

    注意: 需要先创建对应的 Page Object 类
    """

    @pytest.mark.ui
    @pytest.mark.skip(reason="示例代码，需要先创建 LoginPage 类")
    def test_login_with_page_object(self, page, browser_manager):
        """使用 Page Object 模式登录

        适用场景:
        - 复杂页面结构
        - 需要复用页面元素
        - 团队协作标准化
        """
        from {project_name}.pages.login_page import LoginPage

        # 创建 Page Object 实例
        login_page = LoginPage(page, base_url=browser_manager.base_url or "")

        # 导航到登录页
        login_page.goto()

        # 执行登录
        login_page.login("practice", "SuperSecretPassword!")

        # 验证登录成功
        assert "/secure" in page.url


# ============================================================
# 直接使用 Playwright API 测试
# ============================================================

class TestDirectPlaywright:
    """直接使用 Playwright API 的测试

    演示：
    - 不使用 Actions，直接使用 page fixture
    - 适用于简单场景、快速验证
    - 语义化定位器的使用
    """

    @pytest.mark.ui
    def test_login_direct_api(self, page):
        """直接使用 Playwright API 登录

        适用场景:
        - 简单测试
        - 一次性操作
        - 不需要复用
        """
        # 导航到登录页
        page.goto("https://practice.expandtesting.com/login")

        # 填写表单（使用 CSS 选择器）
        page.locator('input[name="username"]').fill("practice")
        page.locator('input[name="password"]').fill("SuperSecretPassword!")
        page.locator('button[type="submit"]').click()

        # 等待跳转
        page.wait_for_url("**/secure", timeout=5000)

        # 验证成功
        assert "/secure" in page.url

    @pytest.mark.ui
    def test_semantic_locators(self, page):
        """语义化定位器示例

        定位器优先级:
        1. test-id（最稳定）
        2. role + name（语义化）
        3. label（表单字段）
        4. text（文本内容）
        5. CSS/XPath（最后选择）
        """
        page.goto("https://practice.expandtesting.com/login")

        # ✅ 推荐：使用 name 属性定位
        page.locator('input[name="username"]').fill("practice")
        page.locator('input[name="password"]').fill("SuperSecretPassword!")

        # ✅ 推荐：使用 type 和 text 定位按钮
        page.locator('button[type="submit"]').click()

        # ✅ 推荐：使用文本定位链接
        page.wait_for_url("**/secure")
        assert page.locator('a[href="/logout"]').is_visible()


# ============================================================
# 调试与可观测性演示
# ============================================================

class TestDebugging:
    """调试功能演示

    演示：
    - @pytest.mark.debug 标记
    - 事件驱动的调试输出
    - Allure 自动记录
    """

    @pytest.mark.ui
    @pytest.mark.debug  # 启用调试模式（需要在配置中启用）
    def test_with_debug_mode(self, login_actions):
        """启用调试模式的测试

        运行方式:
            pytest -s -v tests/ui/test_example.py::TestDebugging::test_with_debug_mode

        调试输出会显示:
        - UI 操作事件（填写、点击等）
        - 浏览器事件（console error/warning、dialog）
        - 页面错误和崩溃
        - HTTP 请求（如果有）

        需要在配置中启用:
            OBSERVABILITY__DEBUG_OUTPUT=true
        """
        login_actions.login_with_valid_credentials()
        assert login_actions.is_logged_in()
'''

__all__ = ["UI_TEST_EXAMPLE_TEMPLATE"]
