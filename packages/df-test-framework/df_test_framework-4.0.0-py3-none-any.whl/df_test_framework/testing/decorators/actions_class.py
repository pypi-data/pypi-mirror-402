"""UI Actions 类自动注册装饰器

提供 @actions_class 装饰器，自动将 AppActions 子类注册为 pytest fixture。

v3.45.0 新增:
- @actions_class 装饰器（类似 @api_class）
- load_actions_fixtures() 自动发现并加载所有 Actions
- 支持多个 Actions 类（LoginActions, OrderActions, UserActions...）

设计理念:
- 与 HTTP 的 @api_class 保持一致的使用体验
- 支持按业务模块拆分 Actions（而非单一的 AppActions）
- 自动注入 page 和 runtime 依赖
"""

from collections.abc import Callable
from typing import Any, Literal, cast

import pytest

from df_test_framework.capabilities.drivers.web.app_actions import AppActions

# 全局 Actions 注册表
# 格式: {fixture_name: (actions_class, scope, dependencies)}
_actions_registry: dict[str, tuple[type[AppActions], str, dict[str, Any]]] = {}


def actions_class(
    name: str | None = None,
    scope: str = "function",
    **dependencies: Any,
):
    """UI Actions 类装饰器，自动注册为 pytest fixture

    将 AppActions 子类自动注册为 pytest fixture，无需手动创建 fixture 函数。

    Args:
        name: fixture 名称，默认为类名转小写
              例如: LoginActions -> login_actions
        scope: pytest fixture scope，默认 "function"（UI 测试通常需要隔离）
               可选: "session", "module", "class", "function"
        **dependencies: fixture 依赖项，会自动注入到 Actions 类构造函数
                       默认自动注入: page, browser_manager

    Returns:
        装饰后的类（不改变类本身）

    Example:
        >>> # 基本用法
        >>> @actions_class("login_actions")
        >>> class LoginActions(AppActions):
        ...     def login_as_admin(self):
        ...         self.goto("/login")
        ...         self.page.get_by_label("Username").fill("admin")
        ...         self.page.get_by_label("Password").fill("admin123")
        ...         self.page.get_by_role("button", name="Sign in").click()
        ...
        ...     def login_as_user(self, username: str, password: str):
        ...         self.goto("/login")
        ...         self.page.get_by_label("Username").fill(username)
        ...         self.page.get_by_label("Password").fill(password)
        ...         self.page.get_by_role("button", name="Sign in").click()
        >>>
        >>> # 自动生成 fixture，测试中直接使用
        >>> def test_login(login_actions):
        ...     login_actions.login_as_admin()
        ...     assert login_actions.page.get_by_test_id("user-menu").is_visible()

        >>> # 自动命名（推荐）
        >>> @actions_class()  # 自动命名为 order_actions
        >>> class OrderActions(AppActions):
        ...     def create_order(self, product: str) -> str:
        ...         # 创建订单并返回订单号
        ...         ...

        >>> # 多个 Actions 组合使用
        >>> def test_order_flow(login_actions, order_actions):
        ...     login_actions.login_as_admin()
        ...     order_id = order_actions.create_order("Phone")
        ...     assert order_id is not None
    """

    def decorator(cls: type[AppActions]) -> type[AppActions]:
        # 生成 fixture 名称
        fixture_name = name
        if fixture_name is None:
            # 自动生成：LoginActions -> login_actions
            fixture_name = cls.__name__
            # 转换为 snake_case
            import re

            fixture_name = re.sub(r"(?<!^)(?=[A-Z])", "_", fixture_name).lower()

        # 注册到全局注册表
        _actions_registry[fixture_name] = (cls, scope, dependencies)

        # 返回原始类（不修改）
        return cls

    return decorator


def get_actions_registry() -> dict[str, tuple[type[AppActions], str, dict[str, Any]]]:
    """获取 Actions 注册表

    Returns:
        Actions 注册表字典
    """
    return _actions_registry.copy()


ScopeType = Literal["session", "package", "module", "class", "function"]


def create_actions_fixture(
    cls: type[AppActions],
    fixture_name: str,
    scope: ScopeType = "function",
    **dependencies: Any,
) -> Callable[..., Any]:
    """为单个 Actions 类创建 pytest fixture

    Args:
        cls: Actions 类
        fixture_name: fixture 名称
        scope: fixture scope
        **dependencies: 依赖注入配置

    Returns:
        pytest fixture 函数

    Example:
        >>> # 手动创建 fixture
        >>> login_fixture = create_actions_fixture(
        ...     LoginActions,
        ...     "login_actions",
        ...     scope="function",
        ... )
    """
    # 如果没有指定依赖，自动推断
    if not dependencies:
        import inspect

        sig = inspect.signature(cls.__init__)
        params = list(sig.parameters.keys())

        # 移除 self
        if "self" in params:
            params.remove("self")

        # 自动推断依赖（UI Actions 的标准依赖）
        if "page" in params:
            dependencies["page"] = "page"
        if "base_url" in params:
            dependencies["base_url"] = None  # 从 browser_manager 获取
        if "runtime" in params:
            dependencies["runtime"] = None  # 从 browser_manager 获取

    # 创建 fixture 函数
    @pytest.fixture(scope=scope, name=fixture_name)
    def actions_fixture(request, page, browser_manager):
        """自动生成的 Actions fixture"""
        # 解析依赖项
        resolved_deps = {}

        for param_name, fixture_name_or_value in dependencies.items():
            if fixture_name_or_value is None:
                # None 表示需要特殊处理
                continue
            elif isinstance(fixture_name_or_value, str):
                # 字符串表示 fixture 名称，从 request 获取
                try:
                    resolved_deps[param_name] = request.getfixturevalue(fixture_name_or_value)
                except Exception:
                    # 如果获取失败，尝试直接使用值
                    resolved_deps[param_name] = fixture_name_or_value
            else:
                # 直接使用值
                resolved_deps[param_name] = fixture_name_or_value

        # 设置标准依赖
        if "page" not in resolved_deps:
            resolved_deps["page"] = page
        if "base_url" not in resolved_deps:
            resolved_deps["base_url"] = browser_manager.base_url or ""
        if "runtime" not in resolved_deps:
            resolved_deps["runtime"] = browser_manager.runtime

        # 创建 Actions 实例
        return cls(**resolved_deps)

    # 设置函数名称和文档
    actions_fixture.__name__ = fixture_name
    actions_fixture.__doc__ = f"Auto-generated fixture for {cls.__name__}"

    return cast(Callable[..., Any], actions_fixture)


def load_actions_fixtures(module_globals: dict, actions_package: str | None = None) -> None:
    """加载所有注册的 Actions fixture 到指定模块

    在 conftest.py 中调用此函数，自动注册所有 @actions_class 装饰的 Actions 为 fixture。

    Args:
        module_globals: 模块的 globals() 字典，通常在 conftest.py 中传入
        actions_package: Actions 包路径（如 "myproject.actions"），如果提供则自动导入该包下所有模块

    Example:
        >>> # conftest.py - 自动发现模式（推荐）
        >>> from df_test_framework.testing.decorators import load_actions_fixtures
        >>>
        >>> # 自动导入 actions 包下所有模块，无需手动 import
        >>> load_actions_fixtures(globals(), actions_package="myproject.actions")

        >>> # conftest.py - 手动导入模式
        >>> from df_test_framework.testing.decorators import load_actions_fixtures
        >>> from myproject.actions.login_actions import LoginActions  # noqa: F401
        >>> from myproject.actions.order_actions import OrderActions  # noqa: F401
        >>>
        >>> load_actions_fixtures(globals())
    """
    # 如果指定了 actions_package，自动导入该包下所有模块
    if actions_package:
        import importlib
        import pkgutil

        try:
            package = importlib.import_module(actions_package)
            # 遍历包下所有模块并导入（触发 @actions_class 装饰器）
            for _, modname, _ in pkgutil.iter_modules(package.__path__):
                try:
                    importlib.import_module(f"{actions_package}.{modname}")
                except ImportError as e:
                    import warnings

                    warnings.warn(f"无法导入模块 {actions_package}.{modname}: {e}")
        except ImportError as e:
            import warnings

            warnings.warn(f"无法导入 Actions 包 {actions_package}: {e}")

    # 从注册表创建 fixture
    for fixture_name, (actions_cls, scope, deps) in _actions_registry.items():
        # 创建 fixture
        fixture_func = create_actions_fixture(actions_cls, fixture_name, scope, **deps)
        # 添加到模块全局变量
        module_globals[fixture_name] = fixture_func


__all__ = [
    "actions_class",
    "get_actions_registry",
    "create_actions_fixture",
    "load_actions_fixtures",
]
