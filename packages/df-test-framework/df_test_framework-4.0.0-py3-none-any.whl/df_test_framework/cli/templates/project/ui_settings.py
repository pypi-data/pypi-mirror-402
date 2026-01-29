"""UI项目配置模板

v3.46.0: 使用 practice.expandtesting.com 作为演示网站
"""

UI_SETTINGS_TEMPLATE = """\"\"\"项目配置 - UI测试项目

基于 df-test-framework 的 UI 测试配置。

v3.42.0: 配置驱动模式
- 使用 WebConfig 统一管理浏览器配置
- 支持环境变量覆盖
- 分层配置支持

v3.46.0: 演示网站配置
- 默认使用 practice.expandtesting.com
- 测试账号: practice / SuperSecretPassword!
\"\"\"

from pydantic import Field
from df_test_framework import FrameworkSettings


class {ProjectName}Settings(FrameworkSettings):
    \"\"\"UI测试项目配置

    v3.42.0+ 推荐使用 WebConfig 统一管理浏览器配置。
    这里保留的字段主要用于项目特定的业务配置。

    测试网站: https://practice.expandtesting.com
    测试账号: practice / SuperSecretPassword!
    \"\"\"

    # ============================================================
    # 注意: 浏览器配置已迁移到 WebConfig
    # ============================================================
    # 不再需要在这里定义 browser_type、headless 等配置。
    # 请使用环境变量或 YAML 配置文件：
    #
    # .env 文件示例：
    #   WEB__BASE_URL=https://practice.expandtesting.com
    #   WEB__BROWSER_TYPE=chromium
    #   WEB__HEADLESS=true
    #   WEB__TIMEOUT=30000
    #
    # 或 config/base.yaml：
    #   web:
    #     base_url: https://practice.expandtesting.com
    #     browser_type: chromium
    #     headless: true
    #     timeout: 30000

    # ============================================================
    # 项目特定配置
    # ============================================================
    # 添加项目业务相关的配置，例如：

    # 测试账号配置（如果不想硬编码在代码中）
    test_username: str = Field(
        default="practice",
        description="测试账号用户名"
    )
    test_password: str = Field(
        default="SuperSecretPassword!",
        description="测试账号密码"
    )

    # 其他业务配置示例
    # max_notes: int = Field(default=100, description="最大笔记数量")
    # default_note_category: str = Field(default="Home", description="默认笔记分类")


__all__ = ["{ProjectName}Settings"]
"""

__all__ = ["UI_SETTINGS_TEMPLATE"]
