"""API项目pytest配置模板

v4.0.0: 支持异步 fixtures
"""

CONFTEST_TEMPLATE = """\"\"\"Pytest 全局配置和 Fixtures (v4.0.0)

基于 df-test-framework v4.0.0 提供测试运行时环境和公共 fixtures。

v4.0.0 重要变更:
- ⚡ 异步优先，同步兼容: 提供 async_http_client, async_database, async_redis_client fixtures
- 🚀 性能提升: HTTP 30x, Database 5-10x, Redis 5-10x（并发场景）
- ✅ 完全兼容: v3.x 代码无需修改即可升级
- 详细信息: docs/releases/v4.0.0.md, docs/migration/v3-to-v4.md

v3.38.7 重要变更:
- structlog 25.5.0 最佳实践升级
- PositionalArgumentsFormatter: 支持第三方库 % 格式化
- ExtraAdder: 支持第三方库 extra 参数
- LogfmtRenderer: 新增 logfmt 输出格式
- pytest 日志集成修复: 无重复输出，统一格式

v3.38.4 重要变更:
- structlog 日志系统(替代 loguru)
- ProcessorFormatter 统一日志格式
- ISO 8601 + UTC 时间戳(生产环境)
- orjson 高性能 JSON 序列化(可选)

v3.38.0 重要变更:
- pytest11 Entry Points: pip install df-test-framework 后插件自动加载
- 无需手动声明 pytest_plugins(框架自动注册)
- pytest 9.0 原生 TOML 配置(使用 [tool.pytest])

配置系统:
- YAML 分层配置(推荐): config/base.yaml + config/environments/{env}.yaml
- 支持 _extends 继承机制(如 local.yaml extends test.yaml)
- --env 参数切换环境(如 --env=local)
- 现代化配置 API: get_settings(), get_config(), get_settings_for_class()

框架自动提供的核心 fixtures(通过 Entry Points 自动加载):
- settings: 框架配置(通过 env_plugin 自动加载)
- current_env: 当前环境名称
- runtime: 运行时上下文(Session级别)
- http_client: HTTP客户端(Session级别，支持中间件系统)
- async_http_client: 异步HTTP客户端(v4.0.0，性能提升30倍)
- database: 数据库连接(Session级别)
- async_database: 异步数据库连接(v4.0.0，性能提升5-10倍)
- redis_client: Redis客户端(Session级别)
- async_redis_client: 异步Redis客户端(v4.0.0，性能提升5-10倍)
- uow: Unit of Work(事务管理 + Repository)
- cleanup: 配置驱动的数据清理
- prepare_data / data_preparer: 数据准备工具
- http_mock: HTTP请求Mock(隔离测试)
- time_mock: 时间Mock(时间敏感测试)
- local_file_client / s3_client / oss_client: 存储客户端
- metrics_manager / metrics_observer: Prometheus 指标收集
- console_debugger / debug_mode: 彩色控制台调试输出
- allure_observer: Allure 事件自动记录

调试系统:
- console_debugger: 彩色控制台调试输出(HTTP/gRPC/GraphQL/MQ/数据库)
- debug_mode: 便捷调试模式
- @pytest.mark.debug: 为特定测试启用调试
- observability.debug_output: true(在 YAML 配置中启用)

注意: 调试输出需要 -s 标志才能实时显示:
    pytest -v -s tests/
    pytest -v -s tests/ --env=local  # 使用本地配置

环境切换示例:
    pytest tests/ --env=test      # 测试环境(默认)
    pytest tests/ --env=staging   # 预发布环境
    pytest tests/ --env=local     # 本地调试配置
\"\"\"

import pytest
from df_test_framework.infrastructure.logging import get_logger
from df_test_framework.testing.decorators import load_api_fixtures

logger = get_logger(__name__)

# ========== @api_class 装饰器自动注册 API fixtures ==========
# v3.38.7: 支持配置驱动的 API 自动发现
# 优先使用配置文件中的 test.apis_package，否则使用默认值
#
# 配置方式(config/base.yaml):
#   test:
#     apis_package: {project_name}.apis
#
# 或环境变量: TEST__APIS_PACKAGE={project_name}.apis


def _get_apis_package() -> str:
    \"\"\"获取 API 包路径(优先配置, 否则默认值)\"\"\"
    default_package = "{project_name}.apis"
    try:
        from df_test_framework.infrastructure.config import get_config
        config = get_config()
        return config.get("test", {{}}).get("apis_package") or default_package
    except Exception:
        return default_package


load_api_fixtures(globals(), apis_package=_get_apis_package())

# ========== 导入项目的业务 fixtures(如果有)==========
# from {project_name}.fixtures import (
#     # API fixtures
#     # some_api,
#     # 清理 fixtures
#     # cleanup_api_test_data,
# )


# ============================================================
# v3.37.0: 插件通过 pytest11 Entry Points 自动加载
# ============================================================
# pip install df-test-framework 后，以下插件自动可用，无需手动声明：
#   - df_test_framework.testing.fixtures.core - 核心 fixtures
#   - df_test_framework.testing.plugins.env_plugin - 环境管理
#   - df_test_framework.testing.plugins.logging_plugin - 日志配置(structlog)
#   - df_test_framework.testing.fixtures.allure - Allure 自动记录
#
# 如果需要额外的框架插件，可以手动添加：
# pytest_plugins = [
#     "df_test_framework.testing.fixtures.debugging",  # 调试工具
#     "df_test_framework.testing.fixtures.metrics",    # 指标收集
# ]


# ============================================================
# 注意: settings fixture 由 env_plugin 自动提供
# ============================================================
# v3.37.0: 不再需要手动定义 settings fixture
# env_plugin 会自动提供以下 fixtures:
#   - settings: 框架配置对象
#   - current_env: 当前环境名称
#
# 使用方式:
#     def test_example(settings, current_env):
#         print(f"当前环境: {{current_env}}")
#         base_url = settings.http.base_url
#         db_host = settings.db.host


# ============================================================
# 调试相关说明
# ============================================================
# 框架提供以下调试方式(通过 df_test_framework.testing.fixtures.debugging):
#
# 方式1(推荐): 使用 @pytest.mark.debug marker
#   @pytest.mark.debug
#   def test_problematic_api(http_client):
#       response = http_client.get("/users")
#       # 控制台自动输出彩色调试信息
#
# 方式2: 使用 console_debugger fixture
#   def test_db(database, console_debugger):
#       database.execute("SELECT * FROM users")
#       # 控制台自动输出 SQL 调试信息
#
# 方式3: 使用 debug_mode fixture
#   @pytest.mark.usefixtures("debug_mode")
#   def test_api(http_client):
#       response = http_client.get("/users")
#
# 方式4: 环境变量全局启用
#   OBSERVABILITY__DEBUG_OUTPUT=true pytest -v -s
#
# 注意: 需要 -s 标志才能看到调试输出！


# ============================================================
# Pytest 配置钩子
# ============================================================

# def pytest_configure(config: pytest.Config) -> None:
#     \"\"\"Pytest 配置钩子 - 在测试运行前执行
#
#     注意: 标记已在 pyproject.toml 的 [tool.pytest] markers 中定义，无需在此重复注册。
#     框架已自动注册 keep_data 和 debug 标记。
#     \"\"\"
#     config.addinivalue_line("markers", "smoke: 冒烟测试，核心功能验证")
#     pass


def pytest_sessionstart(session: pytest.Session) -> None:
    \"\"\"Session 开始时执行 - 配置 Allure 环境信息

    添加测试环境信息到 Allure 报告。

    v3.38.0: 通过 env_plugin 加载的配置获取环境信息。
    \"\"\"
    try:
        from df_test_framework.testing.reporting.allure import AllureHelper

        # 通过 env_plugin 获取配置(存储在 session.config 中)
        if hasattr(session.config, "_df_settings"):
            settings = session.config._df_settings
            current_env = getattr(session.config, "_df_current_env", settings.env)

            AllureHelper.add_environment_info({
                "环境": current_env,
                "API地址": settings.http.base_url,
                # "数据库": f"{settings.db.host}:{settings.db.port}",
                "Python版本": "3.12+",
                "框架版本": "df-test-framework v3.38.7",
                "项目版本": "{project_name} v1.0.0",
                "测试类型": "API自动化测试",
            })
    except Exception as e:
        logger.warning(f"无法加载 Allure 环境信息: {e}")


# ============================================================
# API 测试数据清理示例
# ============================================================
# v3.18.0+: 推荐使用配置驱动的清理(CLEANUP__MAPPINGS__*)
# 框架自动提供 cleanup fixture，只需在 .env 中配置映射即可
#
# .env 示例:
#   CLEANUP__ENABLED=true
#   CLEANUP__MAPPINGS__orders__table=order_table
#   CLEANUP__MAPPINGS__orders__field=order_no
#
# 使用方式:
#   def test_create_order(http_client, cleanup):
#       order_no = DataGenerator.test_id("TEST_ORD")
#       response = http_client.post("/orders", json={{"order_no": order_no}})
#       cleanup.add("orders", order_no)  # 自动清理
#
# 如果需要自定义清理逻辑，可以使用 ListCleanup:
# from df_test_framework.testing.fixtures.cleanup import ListCleanup
#
# @pytest.fixture
# def cleanup_orders(request, http_client):
#     orders = ListCleanup(request)
#     yield orders
#     if orders.should_do_cleanup():
#         for order_id in orders:
#             http_client.delete(f"/orders/{{order_id}}")


"""

__all__ = ["CONFTEST_TEMPLATE"]
