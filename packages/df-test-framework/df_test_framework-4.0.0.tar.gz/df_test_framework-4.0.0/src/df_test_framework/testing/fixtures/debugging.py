"""调试相关 Fixtures

v3.22.0 新增
v3.22.1 扩展：支持数据库调试
v3.23.0 扩展：通过 ObservabilityConfig 控制是否启用
v3.28.0 改进：显式使用 fixture 或 @pytest.mark.debug 时强制启用
v3.28.1 改进：添加 -s 标志提示
v3.46.0 扩展：支持 Web UI 调试（与 HTTP 模式一致）

提供测试调试功能的 pytest fixtures:
- console_debugger: 彩色控制台调试输出（HTTP + 数据库 + Web UI）
- debug_mode: 便捷调试模式

v3.28.0 调试输出控制优先级（从高到低）:
    1. @pytest.mark.debug         - 强制启用（最高优先级）
    2. 显式使用 console_debugger  - 启用（用户明确请求）
    3. DEBUG_OUTPUT=true          - 全局启用
    4. DEBUG_OUTPUT=false         - 全局禁用（默认）

注意：调试输出需要 -s 标志才能实时显示：
    pytest -v -s tests/

使用方式：
    # 方式1：显式使用 fixture（推荐，无论全局配置如何都会启用）
    def test_api(http_client, console_debugger):
        response = http_client.get("/users")
        # 控制台自动输出彩色调试信息

    # 方式2：使用 @pytest.mark.debug marker
    @pytest.mark.debug
    def test_problematic_api(http_client):
        response = http_client.get("/users")
        # 控制台自动输出调试信息

    # 方式3：全局配置启用（所有测试都输出）
    # OBSERVABILITY__DEBUG_OUTPUT=true

    # v3.46.0: Web UI 调试
    def test_ui(page, console_debugger):
        page.goto("https://example.com")
        # 控制台自动输出页面加载、网络请求等调试信息
"""

from __future__ import annotations

import sys
from collections.abc import Generator
from typing import TYPE_CHECKING

import pytest

from df_test_framework.infrastructure.logging import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from df_test_framework.testing.debugging import ConsoleDebugObserver

# v3.28.1: 是否已经显示过 -s 提示（每个 session 只显示一次）
_s_flag_hint_shown = False


def _is_global_debug_enabled() -> bool:
    """检查全局调试输出配置（v3.23.0）

    读取 ObservabilityConfig 配置决定是否全局启用调试输出。

    Returns:
        True: 全局启用调试输出
        False: 全局禁用调试输出
    """
    try:
        from df_test_framework.infrastructure.config import get_settings

        settings = get_settings()
        if settings is None:
            return False  # 没有配置时默认禁用

        # 检查 observability 配置
        obs = getattr(settings, "observability", None)
        if obs is None:
            return False  # 没有 observability 配置时默认禁用

        # v3.23.0: 使用 ObservabilityConfig
        if not obs.enabled:
            return False  # 总开关关闭
        return obs.debug_output

    except Exception:
        # 配置获取失败时默认禁用
        return False


def _show_s_flag_hint() -> None:
    """显示 -s 标志提示（v3.28.1）

    当调试输出启用但 stderr 被 pytest 捕获时，显示一次提示。
    通过 logger 输出，会显示在 pytest 的日志区域。
    """
    global _s_flag_hint_shown

    # 只提示一次
    if _s_flag_hint_shown:
        return

    # 检查 stderr 是否被捕获（不是 TTY）
    if not sys.stderr.isatty():
        logger.warning("调试输出已启用，使用 -s 标志查看彩色输出: pytest -v -s")
        _s_flag_hint_shown = True


def _create_console_debugger(event_bus=None, scope=None) -> ConsoleDebugObserver:
    """创建控制台调试器实例

    Args:
        event_bus: 可选的 EventBus 实例。如果提供，使用该实例；否则使用 get_event_bus()
        scope: 可选的事件作用域（v3.46.1）

    v3.46.1: 支持传入 event_bus 和 scope 参数，实现测试隔离
    """
    from df_test_framework.testing.debugging import ConsoleDebugObserver

    # v3.28.1: 显示 -s 标志提示
    _show_s_flag_hint()

    # 创建调试器
    debugger = ConsoleDebugObserver(
        show_headers=True,
        show_body=True,
        show_params=True,
        max_body_length=500,
        # 数据库调试选项
        show_database=True,
        show_sql=True,
        show_sql_params=True,
        max_sql_length=500,
    )

    # v3.46.1: 优先使用传入的 event_bus（来自 test_runtime）
    if event_bus is None:
        from df_test_framework.infrastructure.events import get_global_event_bus

        event_bus = get_global_event_bus()

    if event_bus:
        debugger.subscribe(event_bus, scope=scope)  # v3.46.1: 传递 scope
    else:
        logger.warning("[_create_console_debugger] EventBus 未找到，ConsoleDebugObserver 无法订阅")

    return debugger


@pytest.fixture
def console_debugger(request: pytest.FixtureRequest) -> Generator[ConsoleDebugObserver, None, None]:
    """控制台调试器 fixture

    v3.22.0 新增
    v3.22.1 扩展：支持数据库调试
    v3.28.0 改进：显式使用时强制启用（忽略全局配置）
    v3.46.1 重构：统一从 test_runtime 获取 EventBus，回退到 runtime (session)

    提供事件驱动的彩色控制台调试输出。
    自动订阅 EventBus，在测试结束时自动取消订阅。
    支持 HTTP 请求、数据库查询、Web UI 操作的调试输出。

    v3.28.0 行为变更：
        显式使用此 fixture 时，无论全局 DEBUG_OUTPUT 配置如何，
        都会创建调试器并输出调试信息。这允许在全局禁用调试的情况下，
        仍然可以为特定测试启用调试。

    v3.46.1 行为变更：
        多级回退获取 EventBus：
        1. test_runtime.event_bus (function 级别，测试隔离)
        2. runtime.event_bus (session 级别，全局共享)
        3. get_event_bus() (向后兼容)

    使用方式：
        # 显式使用（推荐）- 无论全局配置如何都会启用
        def test_api(http_client, console_debugger):
            response = http_client.get("/users")
            # 控制台自动输出请求/响应调试信息

        # Web UI 调试（v3.46.1）
        def test_ui(page, console_debugger, test_runtime):
            app = MyAppActions(page, runtime=test_runtime)
            app.fill_input('input[name="user"]', 'admin', '用户名')
            # 控制台自动输出：📝 填写 [用户名]: admin

        # 数据库调试
        def test_db(database, console_debugger):
            database.execute("SELECT * FROM users")
            # 控制台自动输出 SQL 调试信息

    Yields:
        ConsoleDebugObserver: 控制台调试器实例（始终创建）
    """
    # v3.46.1: 多级回退获取 EventBus 和 scope
    event_bus = None
    scope = None

    # 优先级1: test_runtime.event_bus (function 级别，测试隔离)
    if "test_runtime" in request.fixturenames:
        try:
            test_runtime = request.getfixturevalue("test_runtime")
            event_bus = getattr(test_runtime, "event_bus", None)
            scope = getattr(test_runtime, "scope", None)  # v3.46.1: 获取 scope
        except Exception:
            pass

    # 优先级2: runtime.event_bus (session 级别，全局共享)
    if event_bus is None and "runtime" in request.fixturenames:
        try:
            runtime = request.getfixturevalue("runtime")
            event_bus = getattr(runtime, "event_bus", None)
            if event_bus:
                logger.debug("[console_debugger] 使用 session runtime.event_bus")
        except Exception:
            pass

    # v3.28.0: 显式使用 fixture 时，始终创建调试器
    debugger = _create_console_debugger(event_bus=event_bus, scope=scope)  # v3.46.1: 传递 scope

    yield debugger

    # 取消订阅
    debugger.unsubscribe()


@pytest.fixture(autouse=True)
def _auto_debug_by_marker(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    """自动调试 fixture（通过 marker 或全局配置）

    v3.28.0 新增
    v3.46.0 修复：确保在 test_runtime 之后执行，使用正确的 EventBus
    v3.46.1 重构：统一从 test_runtime 获取 EventBus，回退到 runtime (session)

    检测 @pytest.mark.debug marker 或全局配置，自动启用调试。
    这是一个 autouse fixture，会在每个测试前自动运行。

    优先级：
        1. @pytest.mark.debug marker - 强制启用
        2. 全局 DEBUG_OUTPUT=true - 启用
        3. 其他情况 - 不启用

    EventBus 获取优先级：
        1. test_runtime.event_bus (function 级别，测试隔离)
        2. runtime.event_bus (session 级别，全局共享)
        3. get_event_bus() (向后兼容)

    使用方式：
        @pytest.mark.debug
        def test_problematic_api(http_client):
            response = http_client.get("/users")
            # 控制台自动输出调试信息

        @pytest.mark.debug
        class TestDebugAPI:
            def test_get_users(self, http_client):
                response = http_client.get("/users")
    """
    # 检查是否有 debug marker
    has_debug_marker = request.node.get_closest_marker("debug") is not None

    # 检查是否已经显式使用了 console_debugger fixture
    # 如果已经使用了，就不需要再创建了
    if "console_debugger" in request.fixturenames:
        yield
        return

    # 检查是否需要自动启用调试
    should_enable = has_debug_marker or _is_global_debug_enabled()

    if not should_enable:
        yield
        return

    # v3.46.1: 多级回退获取 EventBus 和 scope
    event_bus = None
    scope = None

    # 优先级1: test_runtime.event_bus (function 级别，测试隔离)
    if "test_runtime" in request.fixturenames:
        try:
            test_runtime = request.getfixturevalue("test_runtime")
            event_bus = getattr(test_runtime, "event_bus", None)
            scope = getattr(test_runtime, "scope", None)  # v3.46.1: 获取 scope
        except Exception as e:
            logger.warning(f"[_auto_debug_by_marker] 无法获取 test_runtime: {e}")

    # 优先级2: runtime.event_bus (session 级别，全局共享)
    if event_bus is None and "runtime" in request.fixturenames:
        try:
            runtime = request.getfixturevalue("runtime")
            event_bus = getattr(runtime, "event_bus", None)
            if event_bus:
                logger.debug("[_auto_debug_by_marker] 使用 session runtime.event_bus")
        except Exception as e:
            logger.warning(f"[_auto_debug_by_marker] 无法获取 runtime: {e}")

    # 自动创建调试器
    debugger = _create_console_debugger(event_bus=event_bus, scope=scope)  # v3.46.1: 传递 scope

    yield

    # 取消订阅
    debugger.unsubscribe()


@pytest.fixture
def debug_mode(console_debugger: ConsoleDebugObserver) -> Generator[None, None, None]:
    """调试模式 fixture

    v3.22.0 新增
    v3.28.0 更新：依赖 console_debugger，始终启用

    启用调试模式，显示详细的请求/响应信息。
    这是一个便捷 fixture，只需声明即可启用调试。

    使用方式：
        @pytest.mark.usefixtures("debug_mode")
        def test_api(http_client):
            response = http_client.get("/users")
            # 控制台自动输出调试信息

        # 或者在测试类上使用
        @pytest.mark.usefixtures("debug_mode")
        class TestAPI:
            def test_get_users(self, http_client):
                response = http_client.get("/users")
    """
    yield


__all__ = [
    "console_debugger",
    "debug_mode",
]
