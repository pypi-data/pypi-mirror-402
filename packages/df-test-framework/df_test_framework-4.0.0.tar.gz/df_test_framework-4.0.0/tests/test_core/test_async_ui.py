"""测试 AsyncAppActions 和 AsyncBasePage（v4.0.0）

验证异步 UI 操作的核心功能。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ============================================================================
# AsyncAppActions 测试
# ============================================================================


class TestAsyncAppActionsInit:
    """测试 AsyncAppActions 初始化"""

    @patch(
        "df_test_framework.capabilities.drivers.web.async_app_actions.PLAYWRIGHT_AVAILABLE",
        True,
    )
    def test_init_with_base_url(self):
        """测试使用 base_url 初始化"""
        from df_test_framework.capabilities.drivers.web import AsyncAppActions

        mock_page = MagicMock()
        actions = AsyncAppActions(mock_page, base_url="https://example.com")

        assert actions.page == mock_page
        assert actions.base_url == "https://example.com"

    @patch(
        "df_test_framework.capabilities.drivers.web.async_app_actions.PLAYWRIGHT_AVAILABLE",
        True,
    )
    def test_init_without_base_url(self):
        """测试不传 base_url 初始化"""
        from df_test_framework.capabilities.drivers.web import AsyncAppActions

        mock_page = MagicMock()
        actions = AsyncAppActions(mock_page)

        assert actions.base_url == ""

    @patch(
        "df_test_framework.capabilities.drivers.web.async_app_actions.PLAYWRIGHT_AVAILABLE",
        True,
    )
    def test_init_with_runtime(self):
        """测试使用 runtime 初始化（自动读取 base_url）"""
        from df_test_framework.capabilities.drivers.web import AsyncAppActions

        mock_page = MagicMock()
        mock_runtime = MagicMock()
        mock_runtime.settings.web.base_url = "https://from-runtime.com"

        actions = AsyncAppActions(mock_page, runtime=mock_runtime)

        assert actions.base_url == "https://from-runtime.com"
        assert actions.runtime == mock_runtime

    @patch(
        "df_test_framework.capabilities.drivers.web.async_app_actions.PLAYWRIGHT_AVAILABLE",
        True,
    )
    def test_init_base_url_priority(self):
        """测试 base_url 参数优先级（显式传入 > runtime）"""
        from df_test_framework.capabilities.drivers.web import AsyncAppActions

        mock_page = MagicMock()
        mock_runtime = MagicMock()
        mock_runtime.settings.web.base_url = "https://from-runtime.com"

        # 显式传入的 base_url 应该优先
        actions = AsyncAppActions(mock_page, base_url="https://explicit.com", runtime=mock_runtime)

        assert actions.base_url == "https://explicit.com"


class TestAsyncAppActionsGoto:
    """测试 AsyncAppActions.goto 方法"""

    @pytest.mark.asyncio
    @patch(
        "df_test_framework.capabilities.drivers.web.async_app_actions.PLAYWRIGHT_AVAILABLE",
        True,
    )
    async def test_goto_with_path(self):
        """测试导航到指定路径"""
        from df_test_framework.capabilities.drivers.web import AsyncAppActions

        mock_page = AsyncMock()
        actions = AsyncAppActions(mock_page, base_url="https://example.com")

        await actions.goto("/login")

        mock_page.goto.assert_called_once_with("https://example.com/login")

    @pytest.mark.asyncio
    @patch(
        "df_test_framework.capabilities.drivers.web.async_app_actions.PLAYWRIGHT_AVAILABLE",
        True,
    )
    async def test_goto_without_path(self):
        """测试导航到基础 URL"""
        from df_test_framework.capabilities.drivers.web import AsyncAppActions

        mock_page = AsyncMock()
        actions = AsyncAppActions(mock_page, base_url="https://example.com")

        await actions.goto()

        mock_page.goto.assert_called_once_with("https://example.com")


class TestAsyncAppActionsUIOperations:
    """测试 AsyncAppActions UI 操作方法"""

    @pytest.fixture
    def async_app_actions(self):
        """创建 mock AsyncAppActions"""
        with patch(
            "df_test_framework.capabilities.drivers.web.async_app_actions.PLAYWRIGHT_AVAILABLE",
            True,
        ):
            from df_test_framework.capabilities.drivers.web import AsyncAppActions

            mock_page = AsyncMock()
            mock_locator = AsyncMock()
            # locator() 和 get_by_text() 是同步方法，返回 Locator 对象
            # 但 Locator 上的 fill(), click() 等是异步方法
            mock_page.locator = MagicMock(return_value=mock_locator)
            mock_page.get_by_text = MagicMock(return_value=mock_locator)

            actions = AsyncAppActions(mock_page, base_url="https://example.com")
            actions._mock_locator = mock_locator
            return actions

    @pytest.mark.asyncio
    async def test_fill_input(self, async_app_actions):
        """测试填写输入框"""
        await async_app_actions.fill_input('input[name="username"]', "admin", "用户名")

        async_app_actions.page.locator.assert_called_once_with('input[name="username"]')
        async_app_actions._mock_locator.fill.assert_called_once_with("admin")

    @pytest.mark.asyncio
    async def test_click(self, async_app_actions):
        """测试点击元素"""
        await async_app_actions.click('button[type="submit"]', "登录按钮")

        async_app_actions.page.locator.assert_called_once_with('button[type="submit"]')
        async_app_actions._mock_locator.click.assert_called_once()

    @pytest.mark.asyncio
    async def test_select_option(self, async_app_actions):
        """测试选择下拉选项"""
        await async_app_actions.select_option('select[name="country"]', "China", "国家选择")

        async_app_actions.page.locator.assert_called_once_with('select[name="country"]')
        async_app_actions._mock_locator.select_option.assert_called_once_with("China")

    @pytest.mark.asyncio
    async def test_check(self, async_app_actions):
        """测试勾选复选框"""
        await async_app_actions.check('input[name="remember"]', "记住密码")

        async_app_actions.page.locator.assert_called_once_with('input[name="remember"]')
        async_app_actions._mock_locator.check.assert_called_once()

    @pytest.mark.asyncio
    async def test_wait_for_text(self, async_app_actions):
        """测试等待文本出现"""
        await async_app_actions.wait_for_text("登录成功", timeout=5000)

        async_app_actions.page.get_by_text.assert_called_once_with("登录成功")
        async_app_actions._mock_locator.wait_for.assert_called_once_with(timeout=5000)


# ============================================================================
# AsyncBasePage 测试
# ============================================================================


class TestAsyncBasePageInit:
    """测试 AsyncBasePage 初始化"""

    @patch(
        "df_test_framework.capabilities.drivers.web.playwright.async_page.PLAYWRIGHT_AVAILABLE",
        True,
    )
    def test_init_with_url(self):
        """测试使用 URL 初始化"""
        from df_test_framework.capabilities.drivers.web import AsyncBasePage

        class TestPage(AsyncBasePage):
            async def wait_for_page_load(self):
                pass

        mock_page = MagicMock()
        page = TestPage(mock_page, url="/login", base_url="https://example.com")

        assert page.page == mock_page
        assert page.url == "/login"
        assert page.base_url == "https://example.com"

    @patch(
        "df_test_framework.capabilities.drivers.web.playwright.async_page.PLAYWRIGHT_AVAILABLE",
        True,
    )
    def test_init_with_runtime(self):
        """测试使用 runtime 初始化"""
        from df_test_framework.capabilities.drivers.web import AsyncBasePage

        class TestPage(AsyncBasePage):
            async def wait_for_page_load(self):
                pass

        mock_page = MagicMock()
        mock_runtime = MagicMock()
        mock_runtime.settings.web.base_url = "https://from-runtime.com"

        page = TestPage(mock_page, url="/dashboard", runtime=mock_runtime)

        assert page.base_url == "https://from-runtime.com"
        assert page.runtime == mock_runtime


class TestAsyncBasePageNavigation:
    """测试 AsyncBasePage 导航方法"""

    @pytest.mark.asyncio
    @patch(
        "df_test_framework.capabilities.drivers.web.playwright.async_page.PLAYWRIGHT_AVAILABLE",
        True,
    )
    async def test_goto_default_url(self):
        """测试使用默认 URL 导航"""
        from df_test_framework.capabilities.drivers.web import AsyncBasePage

        class TestPage(AsyncBasePage):
            async def wait_for_page_load(self):
                pass

        mock_page = AsyncMock()
        page = TestPage(mock_page, url="/login", base_url="https://example.com")

        await page.goto()

        mock_page.goto.assert_called_once_with("https://example.com/login")

    @pytest.mark.asyncio
    @patch(
        "df_test_framework.capabilities.drivers.web.playwright.async_page.PLAYWRIGHT_AVAILABLE",
        True,
    )
    async def test_goto_custom_url(self):
        """测试使用自定义 URL 导航"""
        from df_test_framework.capabilities.drivers.web import AsyncBasePage

        class TestPage(AsyncBasePage):
            async def wait_for_page_load(self):
                pass

        mock_page = AsyncMock()
        page = TestPage(mock_page, url="/login", base_url="https://example.com")

        await page.goto("/dashboard")

        mock_page.goto.assert_called_once_with("https://example.com/dashboard")

    @pytest.mark.asyncio
    @patch(
        "df_test_framework.capabilities.drivers.web.playwright.async_page.PLAYWRIGHT_AVAILABLE",
        True,
    )
    async def test_goto_no_url_raises_error(self):
        """测试没有 URL 时抛出错误"""
        from df_test_framework.capabilities.drivers.web import AsyncBasePage

        class TestPage(AsyncBasePage):
            async def wait_for_page_load(self):
                pass

        mock_page = AsyncMock()
        page = TestPage(mock_page)  # 没有设置 url

        with pytest.raises(ValueError) as exc_info:
            await page.goto()

        assert "必须提供url参数" in str(exc_info.value)


class TestAsyncBasePageMethods:
    """测试 AsyncBasePage 其他方法"""

    @pytest.fixture
    def async_page(self):
        """创建 mock AsyncBasePage"""
        with patch(
            "df_test_framework.capabilities.drivers.web.playwright.async_page.PLAYWRIGHT_AVAILABLE",
            True,
        ):
            from df_test_framework.capabilities.drivers.web import AsyncBasePage

            class TestPage(AsyncBasePage):
                async def wait_for_page_load(self):
                    pass

            mock_page = AsyncMock()
            mock_page.url = "https://example.com/current"
            page = TestPage(mock_page, url="/test", base_url="https://example.com")
            return page

    @pytest.mark.asyncio
    async def test_get_title(self, async_page):
        """测试获取页面标题"""
        async_page.page.title.return_value = "Test Page Title"

        title = await async_page.get_title()

        assert title == "Test Page Title"
        async_page.page.title.assert_called_once()

    def test_url_current(self, async_page):
        """测试获取当前 URL"""
        url = async_page.url_current

        assert url == "https://example.com/current"

    @pytest.mark.asyncio
    async def test_screenshot(self, async_page):
        """测试页面截图"""
        async_page.page.screenshot.return_value = b"screenshot_data"

        result = await async_page.screenshot("test.png", full_page=True)

        assert result == b"screenshot_data"
        async_page.page.screenshot.assert_called_once_with(path="test.png", full_page=True)

    @pytest.mark.asyncio
    async def test_reload(self, async_page):
        """测试刷新页面"""
        await async_page.reload()

        async_page.page.reload.assert_called_once()


# ============================================================================
# EventBus 集成测试
# ============================================================================


class TestAsyncAppActionsEventBus:
    """测试 AsyncAppActions EventBus 事件发布"""

    @pytest.fixture
    def async_app_actions_with_eventbus(self):
        """创建带 EventBus 的 AsyncAppActions"""
        with patch(
            "df_test_framework.capabilities.drivers.web.async_app_actions.PLAYWRIGHT_AVAILABLE",
            True,
        ):
            from df_test_framework.capabilities.drivers.web import AsyncAppActions
            from df_test_framework.infrastructure.events import EventBus

            mock_page = AsyncMock()
            mock_page.url = "https://example.com/login"
            mock_locator = AsyncMock()
            # locator() 和 get_by_text() 是同步方法
            mock_page.locator = MagicMock(return_value=mock_locator)
            mock_page.get_by_text = MagicMock(return_value=mock_locator)

            # 创建 EventBus 和事件收集器
            event_bus = EventBus()
            collected_events = []

            from df_test_framework.core.events import UIActionEvent

            # 使用同步处理器收集事件
            def collect_event(event):
                collected_events.append(event)

            event_bus.subscribe(UIActionEvent, collect_event)

            # 创建 mock runtime
            mock_runtime = MagicMock()
            mock_runtime.event_bus = event_bus
            mock_runtime.settings.web.base_url = "https://example.com"

            # 使用 publish_sync，它会自动处理事件循环问题
            def publish_event(event):
                event_bus.publish_sync(event)

            mock_runtime.publish_event = publish_event

            actions = AsyncAppActions(mock_page, runtime=mock_runtime)
            actions._collected_events = collected_events
            actions._mock_locator = mock_locator
            return actions

    @pytest.mark.asyncio
    async def test_fill_input_publishes_event(self, async_app_actions_with_eventbus):
        """测试 fill_input 发布 UIActionEvent"""
        import asyncio

        await async_app_actions_with_eventbus.fill_input(
            'input[name="username"]', "admin", "用户名输入框"
        )

        # 等待事件循环处理 pending 任务
        await asyncio.sleep(0)

        # 验证事件被发布
        events = async_app_actions_with_eventbus._collected_events
        assert len(events) == 1

        event = events[0]
        assert event.action == "fill"
        assert event.selector == 'input[name="username"]'
        assert event.value == "admin"
        assert event.description == "用户名输入框"

    @pytest.mark.asyncio
    async def test_click_publishes_event(self, async_app_actions_with_eventbus):
        """测试 click 发布 UIActionEvent"""
        import asyncio

        await async_app_actions_with_eventbus.click('button[type="submit"]', "登录按钮")

        # 等待事件循环处理 pending 任务
        await asyncio.sleep(0)

        events = async_app_actions_with_eventbus._collected_events
        assert len(events) == 1

        event = events[0]
        assert event.action == "click"
        assert event.selector == 'button[type="submit"]'
        assert event.description == "登录按钮"
