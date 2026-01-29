"""Full项目配置模板

v3.45.0: 合并 API 和 UI 配置，支持完整项目（API + UI）
"""

FULL_SETTINGS_TEMPLATE = """\"\"\"项目配置 - Full 项目 (API + UI)

基于 df-test-framework v3.45.0 的完整测试项目配置。

v3.45.0 重要变更:
- 合并 API 和 UI 配置，支持完整项目
- 同时支持 HTTP 和 Web 配置
- 支持 @api_class 和 @actions_class 自动发现

配置方式（v3.35.0+）:
- ✅ YAML 分层配置（推荐）: config/base.yaml + config/environments/{env}.yaml
- ✅ _extends 继承机制（local.yaml extends test.yaml）
- ✅ --env 参数切换环境（pytest tests/ --env=local）
- ✅ .env 环境变量（回退模式）

YAML 配置示例（config/base.yaml）:
    env: dev
    http:
      base_url: http://localhost:8000/api
      timeout: 30
    web:
      base_url: http://localhost:3000
      browser_type: chromium
      headless: true
    observability:
      enabled: true
      debug_output: false

使用方式:
    # 方式1: 直接实例化（使用 .env 或默认值）
    >>> from {project_name}.config import {ProjectName}Settings
    >>> settings = {ProjectName}Settings()

    # 方式2: 使用现代化 API（推荐，YAML 配置）
    >>> from df_test_framework import get_settings_for_class
    >>> from {project_name}.config import {ProjectName}Settings
    >>> settings = get_settings_for_class({ProjectName}Settings, env="local")

    # 方式3: 在 pytest 中使用（自动通过 env_plugin 加载）
    >>> def test_example(settings, current_env):
    ...     print(f"当前环境: {current_env}")
    ...     print(settings.http.base_url)  # API 基础 URL
    ...     print(settings.web.base_url)   # Web 基础 URL
\"\"\"

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from df_test_framework.infrastructure.config import (
    FrameworkSettings,
    HTTPConfig,
    WebConfig,
    DatabaseConfig,
    RedisConfig,
    ObservabilityConfig,
    SignatureMiddlewareConfig,
    BearerTokenMiddlewareConfig,
    SignatureAlgorithm,
    TokenSource,
)


class BusinessConfig:
    \"\"\"业务配置（使用 BUSINESS_ 前缀）

    清晰的配置分层:
    - 独立于框架配置
    - 包含业务特定的测试数据和配置

    环境变量:
        BUSINESS_TEST_USER_ID - 测试用户ID
        BUSINESS_TEST_ROLE - 测试角色
    \"\"\"

    def __init__(self):
        import os
        self.test_user_id = os.getenv("BUSINESS_TEST_USER_ID", "test_user_001")
        self.test_role = os.getenv("BUSINESS_TEST_ROLE", "admin")


class {ProjectName}Settings(FrameworkSettings):
    \"\"\"项目测试配置（v3.45.0 Full 项目）

    配置特性:
    - ✅ YAML 分层配置（推荐）
    - ✅ 同时支持 HTTP 和 Web 配置
    - ✅ 中间件系统配置（自动按优先级排序）
    - ✅ 配置驱动清理（CLEANUP__MAPPINGS__*）
    - ✅ 可观测性配置（OBSERVABILITY__*）
    - ✅ API 自动发现（@api_class）
    - ✅ Actions 自动发现（@actions_class）

    环境变量配置:
        # 基础配置
        ENV - 环境（dev/test/staging/prod）
        DEBUG - 调试模式

        # HTTP 配置（API 测试）
        HTTP__BASE_URL - API基础URL
        HTTP__TIMEOUT - 请求超时时间
        HTTP__MAX_RETRIES - 最大重试次数

        # Web 配置（UI 测试）
        WEB__BASE_URL - Web应用基础URL
        WEB__BROWSER_TYPE - 浏览器类型（chromium/firefox/webkit）
        WEB__HEADLESS - 无头模式
        WEB__TIMEOUT - 浏览器超时时间（毫秒）
        WEB__VIEWPORT__width - 视口宽度
        WEB__VIEWPORT__height - 视口高度
        WEB__RECORD_VIDEO - 是否录制视频
        WEB__VIDEO_DIR - 视频保存目录

        # 签名中间件配置
        SIGNATURE__ENABLED - 签名中间件开关
        SIGNATURE__ALGORITHM - 签名算法（md5/sha256/hmac-sha256）
        SIGNATURE__SECRET - 签名密钥

        # Bearer Token 中间件配置
        BEARER_TOKEN__ENABLED - Token中间件开关
        BEARER_TOKEN__SOURCE - Token来源（login/static/env）

        # 数据库配置
        DB__HOST - 数据库主机
        DB__PORT - 数据库端口
        DB__NAME - 数据库名称

        # Redis 配置
        REDIS__HOST - Redis主机
        REDIS__PORT - Redis端口

        # 可观测性配置
        OBSERVABILITY__ENABLED - 总开关
        OBSERVABILITY__DEBUG_OUTPUT - 调试输出

        # 测试配置
        TEST__KEEP_TEST_DATA - 保留测试数据
        TEST__APIS_PACKAGE - API包路径（@api_class 自动发现）
        TEST__ACTIONS_PACKAGE - Actions包路径（@actions_class 自动发现）

    使用方式:
        >>> from {project_name}.config import {ProjectName}Settings
        >>> settings = {ProjectName}Settings()
        >>> print(settings.http.base_url)  # API 基础 URL
        >>> print(settings.web.base_url)   # Web 基础 URL
    \"\"\"

    # ========== HTTP 配置（API 测试）==========
    http: HTTPConfig = Field(
        default_factory=lambda: HTTPConfig(
            base_url="http://localhost:8000/api",
            timeout=30,
            max_retries=3,
        ),
        description="HTTP配置（API测试）"
    )

    # ========== Web 配置（UI 测试）==========
    # v3.46.0: 使用 practice.expandtesting.com 作为演示网站
    # 测试账号: practice / SuperSecretPassword!
    web: WebConfig = Field(
        default_factory=lambda: WebConfig(
            base_url="https://practice.expandtesting.com",
            browser_type="chromium",
            headless=True,
            timeout=30000,
            viewport={{"width": 1920, "height": 1080}},
            record_video=False,
            video_dir="reports/videos",
        ),
        description="Web配置（UI测试）"
    )

    # ========== 签名中间件配置（可选）==========
    # 取消注释以启用签名中间件
    # signature: SignatureMiddlewareConfig = Field(
    #     default_factory=lambda: SignatureMiddlewareConfig(
    #         enabled=True,
    #         priority=10,
    #         algorithm=SignatureAlgorithm.MD5,
    #         secret="your-secret-key",  # ⚠️ 通过环境变量覆盖
    #         header="X-Sign",
    #         include_paths=["/api/**"],
    #         exclude_paths=["/health", "/metrics"],
    #     ),
    #     description="签名中间件配置"
    # )

    # ========== Bearer Token 中间件配置（可选）==========
    # 取消注释以启用 Bearer Token 中间件
    # bearer_token: BearerTokenMiddlewareConfig = Field(
    #     default_factory=lambda: BearerTokenMiddlewareConfig(
    #         enabled=True,
    #         priority=20,
    #         source=TokenSource.LOGIN,
    #         login_url="/auth/login",
    #         credentials={{"username": "admin", "password": "password"}},  # ⚠️ 通过环境变量覆盖
    #         token_path="data.token",
    #         header="Authorization",
    #         token_prefix="Bearer",
    #         include_paths=["/api/**"],
    #         exclude_paths=["/auth/login", "/auth/register"],
    #     ),
    #     description="Bearer Token中间件配置"
    # )

    # ========== 数据库配置（可选）==========
    # 取消注释以启用数据库
    # db: DatabaseConfig = Field(
    #     default_factory=lambda: DatabaseConfig(
    #         host="localhost",
    #         port=3306,
    #         name="test_db",
    #         user="root",
    #         password="password",  # ⚠️ 通过环境变量覆盖
    #         pool_size=10,
    #         charset="utf8mb4",
    #     ),
    #     description="数据库配置"
    # )

    # ========== Redis 配置（可选）==========
    # 取消注释以启用 Redis
    # redis: RedisConfig = Field(
    #     default_factory=lambda: RedisConfig(
    #         host="localhost",
    #         port=6379,
    #         db=0,
    #         password=None,
    #     ),
    #     description="Redis配置"
    # )

    # ========== 可观测性配置 ==========
    observability: ObservabilityConfig = Field(
        default_factory=lambda: ObservabilityConfig(
            enabled=True,
            debug_output=False,  # 设为 True 启用调试输出（需要 pytest -s）
            allure_recording=True,
        ),
        description="可观测性配置"
    )

    # ========== UI 测试便捷属性 ==========
    @property
    def base_url(self) -> str:
        \"\"\"Web 基础 URL（UI 测试便捷访问）\"\"\"
        return self.web.base_url if self.web else ""

    @property
    def browser_type(self) -> str:
        \"\"\"浏览器类型\"\"\"
        return self.web.browser_type if self.web else "chromium"

    @property
    def headless(self) -> bool:
        \"\"\"无头模式\"\"\"
        return self.web.headless if self.web else True

    @property
    def browser_timeout(self) -> int:
        \"\"\"浏览器超时时间（毫秒）\"\"\"
        return self.web.timeout if self.web else 30000

    @property
    def viewport_width(self) -> int:
        \"\"\"视口宽度\"\"\"
        return self.web.viewport.get("width", 1280) if self.web and self.web.viewport else 1280

    @property
    def viewport_height(self) -> int:
        \"\"\"视口高度\"\"\"
        return self.web.viewport.get("height", 720) if self.web and self.web.viewport else 720

    # ========== 业务配置 ==========
    @property
    def business(self) -> BusinessConfig:
        \"\"\"获取业务配置\"\"\"
        return BusinessConfig()

    # Pydantic v2 配置
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


__all__ = ["{ProjectName}Settings", "BusinessConfig"]
"""

__all__ = ["FULL_SETTINGS_TEMPLATE"]
