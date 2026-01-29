"""UI Actions 类自动注册装饰器单元测试

v3.45.0 新增：测试 @actions_class 装饰器
"""

from df_test_framework.capabilities.drivers.web import AppActions
from df_test_framework.testing.decorators.actions_class import (
    _actions_registry,
    actions_class,
    create_actions_fixture,
    get_actions_registry,
    load_actions_fixtures,
)


class TestActionsClassDecorator:
    """actions_class 装饰器测试"""

    def setup_method(self):
        """每个测试前清空注册表"""
        _actions_registry.clear()

    def test_decorator_with_name(self):
        """测试带名称的装饰器"""

        @actions_class("test_actions")
        class TestActions(AppActions):
            pass

        assert "test_actions" in _actions_registry
        assert _actions_registry["test_actions"][0] == TestActions
        assert _actions_registry["test_actions"][1] == "function"  # 默认 scope

    def test_decorator_auto_name(self):
        """测试自动生成名称"""

        @actions_class()
        class LoginActions(AppActions):
            pass

        assert "login_actions" in _actions_registry

    def test_decorator_auto_name_with_actions_suffix(self):
        """测试自动生成名称（已有 Actions 后缀）"""

        @actions_class()
        class UserManagementActions(AppActions):
            pass

        # UserManagementActions -> user_management_actions
        assert "user_management_actions" in _actions_registry

    def test_decorator_custom_scope(self):
        """测试自定义 scope"""

        @actions_class("custom_actions", scope="session")
        class CustomActions(AppActions):
            pass

        assert _actions_registry["custom_actions"][1] == "session"

    def test_decorator_with_dependencies(self):
        """测试带依赖的装饰器"""

        @actions_class("dep_actions", page="custom_page", settings="settings")
        class DepActions(AppActions):
            pass

        deps = _actions_registry["dep_actions"][2]
        assert deps["page"] == "custom_page"
        assert deps["settings"] == "settings"

    def test_decorator_returns_class(self):
        """测试装饰器返回原始类"""

        @actions_class("orig_actions")
        class OriginalActions(AppActions):
            pass

        assert OriginalActions.__name__ == "OriginalActions"

    def test_default_scope_is_function(self):
        """测试默认 scope 是 function（UI 测试需要隔离）"""

        @actions_class()
        class DefaultScopeActions(AppActions):
            pass

        # UI Actions 默认 scope 是 function，与 API 的 session 不同
        assert _actions_registry["default_scope_actions"][1] == "function"


class TestGetActionsRegistry:
    """get_actions_registry 函数测试"""

    def setup_method(self):
        """每个测试前清空注册表"""
        _actions_registry.clear()

    def test_get_registry_copy(self):
        """测试获取注册表副本"""

        @actions_class("reg_actions")
        class RegActions(AppActions):
            pass

        registry = get_actions_registry()
        assert "reg_actions" in registry

        # 修改副本不影响原始
        registry["new_actions"] = None
        assert "new_actions" not in _actions_registry

    def test_get_empty_registry(self):
        """测试获取空注册表"""
        registry = get_actions_registry()
        assert registry == {}


class TestCreateActionsFixture:
    """create_actions_fixture 函数测试"""

    def test_create_fixture_basic(self):
        """测试创建基本 fixture"""

        class SimpleActions(AppActions):
            def __init__(self, page, base_url="", runtime=None):
                super().__init__(page, base_url, runtime)

        fixture = create_actions_fixture(SimpleActions, "simple_actions")
        assert fixture is not None
        assert fixture.__name__ == "simple_actions"

    def test_create_fixture_with_scope(self):
        """测试创建带 scope 的 fixture"""

        class ScopedActions(AppActions):
            def __init__(self, page, base_url="", runtime=None):
                super().__init__(page, base_url, runtime)

        fixture = create_actions_fixture(ScopedActions, "scoped_actions", scope="module")
        assert fixture is not None

    def test_create_fixture_auto_infer_deps(self):
        """测试自动推断依赖"""

        class AutoActions(AppActions):
            def __init__(self, page, base_url="", runtime=None):
                super().__init__(page, base_url, runtime)

        fixture = create_actions_fixture(AutoActions, "auto_actions")
        assert fixture is not None


class TestLoadActionsFixtures:
    """load_actions_fixtures 函数测试"""

    def setup_method(self):
        """每个测试前清空注册表"""
        _actions_registry.clear()

    def test_load_fixtures_to_module(self):
        """测试加载 fixtures 到模块"""

        @actions_class("load_actions")
        class LoadActions(AppActions):
            def __init__(self, page, base_url="", runtime=None):
                super().__init__(page, base_url, runtime)

        module_globals = {}
        load_actions_fixtures(module_globals)

        assert "load_actions" in module_globals

    def test_load_multiple_fixtures(self):
        """测试加载多个 fixtures"""

        @actions_class("actions_one")
        class ActionsOne(AppActions):
            def __init__(self, page, base_url="", runtime=None):
                super().__init__(page, base_url, runtime)

        @actions_class("actions_two")
        class ActionsTwo(AppActions):
            def __init__(self, page, base_url="", runtime=None):
                super().__init__(page, base_url, runtime)

        module_globals = {}
        load_actions_fixtures(module_globals)

        assert "actions_one" in module_globals
        assert "actions_two" in module_globals


class TestAutoNaming:
    """自动命名测试"""

    def setup_method(self):
        """每个测试前清空注册表"""
        _actions_registry.clear()

    def test_camel_case_conversion(self):
        """测试驼峰命名转换"""

        @actions_class()
        class PaymentGatewayActions(AppActions):
            pass

        # PaymentGatewayActions -> payment_gateway_actions
        assert "payment_gateway_actions" in _actions_registry

    def test_single_word(self):
        """测试单词命名"""

        @actions_class()
        class OrderActions(AppActions):
            pass

        # OrderActions -> order_actions
        assert "order_actions" in _actions_registry

    def test_complex_name(self):
        """测试复杂命名"""

        @actions_class()
        class UserProfileManagementActions(AppActions):
            pass

        # UserProfileManagementActions -> user_profile_management_actions
        assert "user_profile_management_actions" in _actions_registry


class TestActionsClassExports:
    """测试 actions_class 导出"""

    def test_actions_class_is_exported_from_decorators(self):
        """actions_class 可以从 decorators 模块导入"""
        from df_test_framework.testing.decorators import actions_class

        assert actions_class is not None

    def test_load_actions_fixtures_is_exported(self):
        """load_actions_fixtures 可以从 decorators 模块导入"""
        from df_test_framework.testing.decorators import load_actions_fixtures

        assert load_actions_fixtures is not None

    def test_get_actions_registry_is_exported(self):
        """get_actions_registry 可以从 decorators 模块导入"""
        from df_test_framework.testing.decorators import get_actions_registry

        assert get_actions_registry is not None

    def test_actions_class_is_exported_from_top_level(self):
        """actions_class 可以从顶层模块导入"""
        from df_test_framework import actions_class, load_actions_fixtures

        assert actions_class is not None
        assert load_actions_fixtures is not None


class TestActionsClassWithHttpApiClassComparison:
    """测试 @actions_class 与 @api_class 的一致性"""

    def setup_method(self):
        """每个测试前清空注册表"""
        _actions_registry.clear()

    def test_similar_api_to_api_class(self):
        """测试 @actions_class 与 @api_class 有相似的 API"""

        # 两者都支持 name 参数
        @actions_class("my_actions")
        class MyActions(AppActions):
            pass

        # 两者都支持 scope 参数
        @actions_class("scoped_actions", scope="session")
        class ScopedActions(AppActions):
            pass

        # 两者都支持自动命名
        @actions_class()
        class AutoNameActions(AppActions):
            pass

        assert "my_actions" in _actions_registry
        assert "scoped_actions" in _actions_registry
        assert "auto_name_actions" in _actions_registry

    def test_default_scope_difference(self):
        """测试默认 scope 的差异（actions=function, api=session）"""
        from df_test_framework.testing.decorators.api_class import _api_registry

        _api_registry.clear()

        from df_test_framework.capabilities.clients.http.rest.httpx import BaseAPI
        from df_test_framework.testing.decorators import api_class

        @api_class()
        class TestAPI(BaseAPI):
            pass

        @actions_class()
        class TestActions(AppActions):
            pass

        # API 默认 session scope
        assert _api_registry["test_api"][1] == "session"
        # Actions 默认 function scope（UI 测试需要隔离）
        assert _actions_registry["test_actions"][1] == "function"


class TestActionsPackageAutoDiscovery:
    """测试 actions_package 自动发现功能"""

    def setup_method(self):
        """每个测试前清空注册表"""
        _actions_registry.clear()

    def test_load_actions_fixtures_with_invalid_package(self):
        """测试加载不存在的包时发出警告"""
        import warnings

        module_globals = {}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            load_actions_fixtures(module_globals, actions_package="nonexistent.package")

            # 应该发出警告
            assert len(w) >= 1
            assert "无法导入" in str(w[0].message)

    def test_load_actions_fixtures_without_package(self):
        """测试不指定包时只加载已注册的 Actions"""

        @actions_class("registered_actions")
        class RegisteredActions(AppActions):
            pass

        module_globals = {}
        load_actions_fixtures(module_globals)

        assert "registered_actions" in module_globals
