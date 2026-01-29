"""Pytest配置文件

为UI测试示例配置pytest fixtures和选项

v3.46.3: UI fixtures 和失败诊断通过 pytest11 自动加载，无需手动声明
"""

from pathlib import Path

import pytest

# ============================================================
# v3.46.3: UI 插件通过 pytest11 自动加载 ⭐
# ============================================================
# pip install df-test-framework 后，以下功能自动可用：
#   - df_test_framework.testing.fixtures.ui (浏览器 fixtures)
#   - pytest_runtest_makereport hook (失败诊断)
#
# 无需手动声明 pytest_plugins


# ========== 配置选项 ==========


def pytest_addoption(parser):
    """添加命令行选项"""
    parser.addoption(
        "--headed",
        action="store_true",
        default=False,
        help="显示浏览器窗口（非无头模式）",
    )
    parser.addoption(
        "--browser",
        action="store",
        default="chromium",
        help="选择浏览器: chromium, firefox, webkit",
    )
    parser.addoption(
        "--slowmo",
        action="store",
        default=0,
        type=int,
        help="每个操作的延迟（毫秒），用于调试",
    )


# ========== 自定义fixtures ==========


@pytest.fixture(scope="session")
def browser_headless(request):
    """
    配置浏览器无头模式

    通过--headed命令行参数控制
    """
    return not request.config.getoption("--headed")


@pytest.fixture(scope="session")
def browser_type(request):
    """
    配置浏览器类型

    通过--browser命令行参数控制
    """
    from df_test_framework.ui import BrowserType

    browser_name = request.config.getoption("--browser").lower()

    browser_map = {
        "chromium": BrowserType.CHROMIUM,
        "firefox": BrowserType.FIREFOX,
        "webkit": BrowserType.WEBKIT,
    }

    return browser_map.get(browser_name, BrowserType.CHROMIUM)


@pytest.fixture(scope="session")
def browser_slow_mo(request):
    """配置操作延迟（用于调试）"""
    return request.config.getoption("--slowmo")


@pytest.fixture(scope="session")
def screenshots_dir():
    """截图保存目录"""
    screenshots_path = Path(__file__).parent / "screenshots"
    screenshots_path.mkdir(exist_ok=True)
    return screenshots_path


# ========== Hooks ==========


# ============================================================
# v3.46.3: 失败诊断已由框架自动实现 ⭐
# ============================================================
# 框架已通过 pytest11 自动加载失败诊断功能：
#   - 失败时自动截图
#   - 视频处理
#   - Allure 附件
#
# 以下是自定义 hook 示例（可选）：
# 如果需要自定义失败诊断逻辑，可以添加自己的 hook
# pytest 允许多个同名 hook 共存，都会执行

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    自定义失败诊断示例（可选）

    注意：框架已提供默认的失败诊断，此处仅作为示例展示如何自定义
    """
    # 执行所有其他hooks以获取测试结果
    outcome = yield
    report = outcome.get_result()

    # 只处理测试执行阶段的失败
    if report.when == "call" and report.failed:
        # 如果测试使用了page fixture
        if "page" in item.funcargs:
            page = item.funcargs["page"]

            # 自定义截图路径（示例：保存到 examples/06-ui-testing/screenshots）
            screenshots_dir = Path(__file__).parent / "screenshots"
            screenshots_dir.mkdir(exist_ok=True)

            screenshot_path = screenshots_dir / f"{item.name}_failure.png"

            try:
                page.screenshot(path=str(screenshot_path))
                print(f"\n[自定义] 失败截图已保存: {screenshot_path}")
            except Exception as e:
                print(f"\n[自定义] 截图失败: {e}")


def pytest_configure(config):
    """pytest配置钩子"""
    # 注册自定义标记
    config.addinivalue_line("markers", "ui: mark test as ui test")
    config.addinivalue_line("markers", "slow: mark test as slow running")

    print("\n" + "=" * 70)
    print("DF Test Framework - UI测试示例")
    print("=" * 70)
    print(f"浏览器: {config.getoption('--browser')}")
    print(f"无头模式: {not config.getoption('--headed')}")

    if config.getoption("--slowmo"):
        print(f"操作延迟: {config.getoption('--slowmo')}ms")

    print("=" * 70 + "\n")


def pytest_collection_modifyitems(items):
    """修改收集到的测试项"""
    for item in items:
        # 为所有UI测试添加ui标记
        if "page" in item.fixturenames or "browser" in item.fixturenames:
            item.add_marker(pytest.mark.ui)
