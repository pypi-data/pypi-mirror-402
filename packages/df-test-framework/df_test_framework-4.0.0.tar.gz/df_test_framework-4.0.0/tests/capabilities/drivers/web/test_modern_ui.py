"""测试现代UI模式（v4.0.0 同步版本）

v4.0.0: 同步兼容版本测试
v3.43.0: 测试 BaseComponent、BasePage、AppActions

测试覆盖:
- BaseComponent 组件封装
- 简化的 BasePage（同步版本）
- AppActions 业务操作（同步版本）
- UI 操作辅助方法（fill_input, click, select_option, check, wait_for_text）
- EventBus 集成

注意：异步版本测试见 tests/test_core/test_async_ui.py
"""

from unittest.mock import MagicMock, patch

import pytest


class TestBaseComponent:
    """测试 BaseComponent 组件基类"""

    def test_component_with_test_id(self):
        """测试使用 test-id 创建组件"""
        with patch(
            "df_test_framework.capabilities.drivers.web.playwright.component.PLAYWRIGHT_AVAILABLE",
            True,
        ):
            from df_test_framework.capabilities.drivers.web import BaseComponent

            # 创建 mock page
            mock_page = MagicMock()
            mock_locator = MagicMock()
            mock_page.get_by_test_id.return_value = mock_locator

            # 创建组件
            component = BaseComponent(mock_page, test_id="login-form")

            assert component.page == mock_page
            assert component.test_id == "login-form"
            assert component.root == mock_locator
            mock_page.get_by_test_id.assert_called_once_with("login-form")

    def test_component_without_test_id(self):
        """测试不使用 test-id 创建组件（整个页面）"""
        with patch(
            "df_test_framework.capabilities.drivers.web.playwright.component.PLAYWRIGHT_AVAILABLE",
            True,
        ):
            from df_test_framework.capabilities.drivers.web import BaseComponent

            mock_page = MagicMock()

            component = BaseComponent(mock_page)

            assert component.page == mock_page
            assert component.test_id is None
            assert component.root == mock_page

    def test_component_get_by_role(self):
        """测试组件的 get_by_role 方法"""
        with patch(
            "df_test_framework.capabilities.drivers.web.playwright.component.PLAYWRIGHT_AVAILABLE",
            True,
        ):
            from df_test_framework.capabilities.drivers.web import BaseComponent

            mock_page = MagicMock()
            mock_root = MagicMock()
            mock_page.get_by_test_id.return_value = mock_root

            component = BaseComponent(mock_page, test_id="form")

            # 调用 get_by_role
            component.get_by_role("button", name="Submit")

            # 应该在 root 上调用
            mock_root.get_by_role.assert_called_once_with("button", name="Submit")

    def test_component_locator_methods(self):
        """测试组件的各种定位方法"""
        with patch(
            "df_test_framework.capabilities.drivers.web.playwright.component.PLAYWRIGHT_AVAILABLE",
            True,
        ):
            from df_test_framework.capabilities.drivers.web import BaseComponent

            mock_page = MagicMock()
            mock_root = MagicMock()
            mock_page.get_by_test_id.return_value = mock_root

            component = BaseComponent(mock_page, test_id="form")

            # 测试各种定位方法
            component.get_by_test_id("submit-btn")
            component.get_by_label("Username")
            component.get_by_placeholder("Enter email")
            component.get_by_text("Welcome")
            component.locator("#username")

            # 验证都在 root 上调用
            mock_root.get_by_test_id.assert_called_once()
            mock_root.get_by_label.assert_called_once()
            mock_root.get_by_placeholder.assert_called_once()
            mock_root.get_by_text.assert_called_once()
            mock_root.locator.assert_called_once()


class TestBasePage:
    """测试简化的 BasePage"""

    def test_base_page_goto(self):
        """测试页面导航"""
        with patch(
            "df_test_framework.capabilities.drivers.web.playwright.page.PLAYWRIGHT_AVAILABLE",
            True,
        ):
            from df_test_framework.capabilities.drivers.web import BasePage

            # 创建具体页面类
            class LoginPage(BasePage):
                def wait_for_page_load(self):
                    pass

            mock_page = MagicMock()

            page = LoginPage(mock_page, url="/login", base_url="https://example.com")
            page.goto()

            # 验证调用了 page.goto
            mock_page.goto.assert_called_once_with("https://example.com/login")

    def test_base_page_title_property(self):
        """测试 title 属性"""
        with patch(
            "df_test_framework.capabilities.drivers.web.playwright.page.PLAYWRIGHT_AVAILABLE",
            True,
        ):
            from df_test_framework.capabilities.drivers.web import BasePage

            class LoginPage(BasePage):
                def wait_for_page_load(self):
                    pass

            mock_page = MagicMock()
            mock_page.title.return_value = "Login Page"

            page = LoginPage(mock_page)

            assert page.title == "Login Page"
            mock_page.title.assert_called_once()

    def test_base_page_screenshot(self):
        """测试截图方法"""
        with patch(
            "df_test_framework.capabilities.drivers.web.playwright.page.PLAYWRIGHT_AVAILABLE",
            True,
        ):
            from df_test_framework.capabilities.drivers.web import BasePage

            class LoginPage(BasePage):
                def wait_for_page_load(self):
                    pass

            mock_page = MagicMock()
            mock_page.screenshot.return_value = b"screenshot_data"

            page = LoginPage(mock_page)
            result = page.screenshot("test.png")

            assert result == b"screenshot_data"
            mock_page.screenshot.assert_called_once_with(path="test.png")


class TestAppActions:
    """测试 AppActions 业务操作基类"""

    def test_app_actions_init(self):
        """测试 AppActions 初始化"""
        with patch(
            "df_test_framework.capabilities.drivers.web.app_actions.PLAYWRIGHT_AVAILABLE",
            True,
        ):
            from df_test_framework.capabilities.drivers.web import AppActions

            mock_page = MagicMock()
            actions = AppActions(mock_page, base_url="https://example.com")

            assert actions.page == mock_page
            assert actions.base_url == "https://example.com"

    def test_app_actions_goto(self):
        """测试 AppActions 的 goto 方法"""
        with patch(
            "df_test_framework.capabilities.drivers.web.app_actions.PLAYWRIGHT_AVAILABLE",
            True,
        ):
            from df_test_framework.capabilities.drivers.web import AppActions

            mock_page = MagicMock()
            actions = AppActions(mock_page, base_url="https://example.com")

            # 测试带路径
            actions.goto("/login")
            mock_page.goto.assert_called_with("https://example.com/login")

            # 测试不带路径
            actions.goto()
            mock_page.goto.assert_called_with("https://example.com")

    def test_app_actions_custom_implementation(self):
        """测试自定义 AppActions 实现"""
        with patch(
            "df_test_framework.capabilities.drivers.web.app_actions.PLAYWRIGHT_AVAILABLE",
            True,
        ):
            from df_test_framework.capabilities.drivers.web import AppActions

            class MyAppActions(AppActions):
                def login_as_admin(self):
                    self.page.get_by_label("Username").fill("admin")
                    self.page.get_by_label("Password").fill("admin123")
                    self.page.get_by_role("button", name="Sign in").click()

            mock_page = MagicMock()
            actions = MyAppActions(mock_page, base_url="https://example.com")

            actions.login_as_admin()

            # 验证调用了正确的方法
            mock_page.get_by_label.assert_any_call("Username")
            mock_page.get_by_label.assert_any_call("Password")


class TestModernUIExports:
    """测试现代UI模式的导出"""

    def test_base_component_is_exported(self):
        """BaseComponent 可以导入"""
        from df_test_framework.capabilities.drivers.web import BaseComponent

        assert BaseComponent is not None

    def test_app_actions_is_exported(self):
        """AppActions 可以导入"""
        from df_test_framework.capabilities.drivers.web import AppActions

        assert AppActions is not None

    def test_all_exports_available(self):
        """所有导出都可用"""
        import df_test_framework.capabilities.drivers.web as web

        assert "BaseComponent" in web.__all__
        assert "AppActions" in web.__all__
        assert "BasePage" in web.__all__

    def test_async_exports_available(self):
        """异步版本导出可用（v4.0.0）"""
        import df_test_framework.capabilities.drivers.web as web

        assert "AsyncAppActions" in web.__all__
        assert "AsyncBasePage" in web.__all__


# ============================================================================
# AppActions UI 操作辅助方法测试（v4.0.0）
# ============================================================================


class TestAppActionsUIOperations:
    """测试 AppActions UI 操作辅助方法（同步版本）"""

    @pytest.fixture
    def app_actions(self):
        """创建 mock AppActions"""
        with patch(
            "df_test_framework.capabilities.drivers.web.app_actions.PLAYWRIGHT_AVAILABLE",
            True,
        ):
            from df_test_framework.capabilities.drivers.web import AppActions

            mock_page = MagicMock()
            mock_locator = MagicMock()
            mock_page.locator.return_value = mock_locator
            mock_page.get_by_text.return_value = mock_locator

            actions = AppActions(mock_page, base_url="https://example.com")
            actions._mock_locator = mock_locator
            return actions

    def test_fill_input(self, app_actions):
        """测试填写输入框"""
        app_actions.fill_input('input[name="username"]', "admin", "用户名")

        app_actions.page.locator.assert_called_once_with('input[name="username"]')
        app_actions._mock_locator.fill.assert_called_once_with("admin")

    def test_click(self, app_actions):
        """测试点击元素"""
        app_actions.click('button[type="submit"]', "登录按钮")

        app_actions.page.locator.assert_called_once_with('button[type="submit"]')
        app_actions._mock_locator.click.assert_called_once()

    def test_select_option(self, app_actions):
        """测试选择下拉选项"""
        app_actions.select_option('select[name="country"]', "China", "国家选择")

        app_actions.page.locator.assert_called_once_with('select[name="country"]')
        app_actions._mock_locator.select_option.assert_called_once_with("China")

    def test_check(self, app_actions):
        """测试勾选复选框"""
        app_actions.check('input[name="remember"]', "记住密码")

        app_actions.page.locator.assert_called_once_with('input[name="remember"]')
        app_actions._mock_locator.check.assert_called_once()

    def test_wait_for_text(self, app_actions):
        """测试等待文本出现"""
        app_actions.wait_for_text("登录成功", timeout=5000)

        app_actions.page.get_by_text.assert_called_once_with("登录成功")
        app_actions._mock_locator.wait_for.assert_called_once_with(timeout=5000)


# ============================================================================
# EventBus 集成测试（v4.0.0）
# ============================================================================


class TestAppActionsEventBus:
    """测试 AppActions EventBus 事件发布（同步版本）"""

    @pytest.fixture
    def app_actions_with_eventbus(self):
        """创建带 EventBus 的 AppActions"""
        with patch(
            "df_test_framework.capabilities.drivers.web.app_actions.PLAYWRIGHT_AVAILABLE",
            True,
        ):
            from df_test_framework.capabilities.drivers.web import AppActions
            from df_test_framework.infrastructure.events import EventBus

            mock_page = MagicMock()
            mock_page.url = "https://example.com/login"
            mock_locator = MagicMock()
            mock_page.locator.return_value = mock_locator
            mock_page.get_by_text.return_value = mock_locator

            # 创建 EventBus 和事件收集器
            event_bus = EventBus()
            collected_events = []

            from df_test_framework.core.events import UIActionEvent

            def collect_event(event):
                collected_events.append(event)

            # subscribe 支持同步处理器
            event_bus.subscribe(UIActionEvent, collect_event)

            # 创建 mock runtime
            mock_runtime = MagicMock()
            mock_runtime.event_bus = event_bus
            mock_runtime.settings.web.base_url = "https://example.com"

            def publish_event(event):
                event_bus.publish_sync(event)

            mock_runtime.publish_event = publish_event

            actions = AppActions(mock_page, runtime=mock_runtime)
            actions._collected_events = collected_events
            actions._mock_locator = mock_locator
            return actions

    def test_fill_input_publishes_event(self, app_actions_with_eventbus):
        """测试 fill_input 发布 UIActionEvent"""
        app_actions_with_eventbus.fill_input('input[name="username"]', "admin", "用户名输入框")

        # 验证事件被发布
        events = app_actions_with_eventbus._collected_events
        assert len(events) == 1

        event = events[0]
        assert event.action == "fill"
        assert event.selector == 'input[name="username"]'
        assert event.value == "admin"
        assert event.description == "用户名输入框"

    def test_click_publishes_event(self, app_actions_with_eventbus):
        """测试 click 发布 UIActionEvent"""
        app_actions_with_eventbus.click('button[type="submit"]', "登录按钮")

        events = app_actions_with_eventbus._collected_events
        assert len(events) == 1

        event = events[0]
        assert event.action == "click"
        assert event.selector == 'button[type="submit"]'
        assert event.description == "登录按钮"


# ============================================================================
# BasePage 补充测试（v4.0.0）
# ============================================================================


class TestBasePageAdditional:
    """测试 BasePage 补充功能（同步版本）"""

    def test_base_page_with_runtime(self):
        """测试使用 runtime 初始化"""
        with patch(
            "df_test_framework.capabilities.drivers.web.playwright.page.PLAYWRIGHT_AVAILABLE",
            True,
        ):
            from df_test_framework.capabilities.drivers.web import BasePage

            class TestPage(BasePage):
                def wait_for_page_load(self):
                    pass

            mock_page = MagicMock()
            mock_runtime = MagicMock()
            mock_runtime.settings.web.base_url = "https://from-runtime.com"

            page = TestPage(mock_page, url="/dashboard", runtime=mock_runtime)

            assert page.base_url == "https://from-runtime.com"
            assert page.runtime == mock_runtime

    def test_base_page_url_current(self):
        """测试获取当前 URL"""
        with patch(
            "df_test_framework.capabilities.drivers.web.playwright.page.PLAYWRIGHT_AVAILABLE",
            True,
        ):
            from df_test_framework.capabilities.drivers.web import BasePage

            class TestPage(BasePage):
                def wait_for_page_load(self):
                    pass

            mock_page = MagicMock()
            mock_page.url = "https://example.com/current"
            page = TestPage(mock_page)

            assert page.url_current == "https://example.com/current"

    def test_base_page_reload(self):
        """测试刷新页面"""
        with patch(
            "df_test_framework.capabilities.drivers.web.playwright.page.PLAYWRIGHT_AVAILABLE",
            True,
        ):
            from df_test_framework.capabilities.drivers.web import BasePage

            class TestPage(BasePage):
                def __init__(self, page, **kwargs):
                    super().__init__(page, **kwargs)
                    self.load_count = 0

                def wait_for_page_load(self):
                    self.load_count += 1

            mock_page = MagicMock()
            page = TestPage(mock_page)
            page.reload()

            mock_page.reload.assert_called_once()
            assert page.load_count == 1

    def test_base_page_goto_no_url_raises_error(self):
        """测试没有 URL 时抛出错误"""
        with patch(
            "df_test_framework.capabilities.drivers.web.playwright.page.PLAYWRIGHT_AVAILABLE",
            True,
        ):
            from df_test_framework.capabilities.drivers.web import BasePage

            class TestPage(BasePage):
                def wait_for_page_load(self):
                    pass

            mock_page = MagicMock()
            page = TestPage(mock_page)  # 没有设置 url

            with pytest.raises(ValueError) as exc_info:
                page.goto()

            assert "必须提供url参数" in str(exc_info.value)
