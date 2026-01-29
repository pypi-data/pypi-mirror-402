"""init命令实现

创建测试项目脚手架。
"""

from __future__ import annotations

import os
from pathlib import Path

from ..templates import (
    BASE_API_TEMPLATE,
    CONFTEST_TEMPLATE,
    CONSTANTS_ERROR_CODES_TEMPLATE,
    DATA_CLEANERS_TEMPLATE,
    DOCS_API_TEMPLATE,
    EDITORCONFIG_TEMPLATE,
    ENHANCED_GITIGNORE_TEMPLATE,
    EXAMPLE_API_TEMPLATE,
    FIXTURES_INIT_TEMPLATE,
    FULL_CONFTEST_TEMPLATE,  # v3.45.0
    FULL_SETTINGS_TEMPLATE,  # v3.45.0
    GITATTRIBUTES_TEMPLATE,
    MODELS_REQUESTS_EXAMPLE_TEMPLATE,
    MODELS_RESPONSES_EXAMPLE_TEMPLATE,
    PYPROJECT_TOML_TEMPLATE,
    README_API_TEMPLATE,
    README_FULL_TEMPLATE,
    README_UI_TEMPLATE,
    SCRIPT_FETCH_SWAGGER_TEMPLATE,
    SCRIPT_RUN_TESTS_TEMPLATE,
    SETTINGS_TEMPLATE,
    TEST_EXAMPLE_TEMPLATE,
    UI_APP_ACTIONS_TEMPLATE,  # v3.45.0
    UI_CONFTEST_TEMPLATE,
    UI_FIXTURES_INIT_TEMPLATE,
    UI_PAGE_OBJECT_TEMPLATE,
    UI_SETTINGS_TEMPLATE,
    UI_TEST_EXAMPLE_TEMPLATE,
    UTILS_CONVERTERS_TEMPLATE,
    # 增强功能模板
    UTILS_VALIDATORS_TEMPLATE,
    VSCODE_EXTENSIONS_TEMPLATE,
    VSCODE_SETTINGS_TEMPLATE,
)
from ..templates.generators.env_files import (
    # v3.35.0+ YAML 配置模板
    SECRETS_ENV_LOCAL_TEMPLATE,
    YAML_BASE_FULL_TEMPLATE,  # v3.45.0: Full 项目专用
    YAML_BASE_TEMPLATE,
    YAML_BASE_UI_TEMPLATE,  # v3.45.0: UI 项目专用
    YAML_DEV_TEMPLATE,
    YAML_LOCAL_TEMPLATE,
    YAML_PROD_TEMPLATE,
    YAML_STAGING_TEMPLATE,
    YAML_TEST_TEMPLATE,
)
from ..utils import (
    AUTO_GENERATED_END,
    AUTO_GENERATED_START,
    AUTO_GENERATED_WARNING,
    USER_EXTENSIONS_HINT,
    USER_EXTENSIONS_START,
    create_file,
    replace_template_vars,
    to_pascal_case,
    to_snake_case,
)
from .cicd import generate_cicd_files


def _get_framework_dependency() -> str:
    """智能选择框架依赖

    根据环境自动选择合适的依赖方式：
    1. CI 环境（自动检测） → 本地路径依赖
    2. DF_TEST_LOCAL_DEV=1 → 本地路径依赖
    3. 默认 → PyPI 版本依赖

    Returns:
        框架依赖字符串

    Example:
        >>> os.environ["CI"] = "true"
        >>> _get_framework_dependency()
        '"df-test-framework @ file://.."'

        >>> os.environ.pop("CI")
        >>> _get_framework_dependency()
        '"df-test-framework>=3.5.0"'
    """
    # 检测 CI 环境（GitHub Actions, GitLab CI, Jenkins 等都会设置 CI=true）
    if os.getenv("CI") == "true":
        return '"df-test-framework @ file://.."'

    # 检测本地开发标志
    if os.getenv("DF_TEST_LOCAL_DEV") == "1":
        return '"df-test-framework @ file://.."'

    # 生产环境：从 PyPI 安装
    return '"df-test-framework>=3.38.0"'


def init_project(
    path: Path, *, project_type: str = "api", ci_platform: str = "none", force: bool = False
) -> None:
    """初始化测试项目

    创建完整的项目结构，支持不同类型的测试项目。

    项目类型:
    - api: API测试项目（默认）
    - ui: UI测试项目（基于Playwright）
    - full: 完整项目（API + UI）

    CI/CD平台:
    - github-actions: GitHub Actions工作流
    - gitlab-ci: GitLab CI配置
    - jenkins: Jenkins Pipeline
    - all: 所有平台
    - none: 不生成CI/CD配置（默认）

    Args:
        path: 项目路径
        project_type: 项目类型（api, ui, full）
        ci_platform: CI/CD平台（github-actions, gitlab-ci, jenkins, all, none）
        force: 是否强制覆盖已存在的文件

    Raises:
        FileExistsError: 文件已存在且force=False
        ValueError: 不支持的项目类型

    Example:
        >>> init_project(Path("my-test-project"), project_type="api")
        ✅ API测试项目初始化成功！
        ...
        >>> init_project(Path("my-test-project"), project_type="api", ci_platform="github-actions")
        ✅ API测试项目初始化成功！
        ✅ GitHub Actions工作流配置已生成！
        ...
    """
    if project_type not in ("api", "ui", "full"):
        raise ValueError(f"不支持的项目类型: {project_type}，支持: api, ui, full")
    # 创建项目根目录
    path.mkdir(parents=True, exist_ok=True)

    # 项目名称转换
    project_name_raw = path.name
    project_name = to_snake_case(project_name_raw)
    project_name_pascal = to_pascal_case(project_name_raw)

    # 变量替换字典
    replacements = {
        "{project_name}": project_name,
        "{ProjectName}": project_name_pascal,
        "{framework_dependency}": _get_framework_dependency(),  # 智能依赖选择
        "{timestamp}": "auto-generated",  # YAML 模板时间戳
    }

    def replace_template(template: str) -> str:
        """替换模板中的变量"""
        return replace_template_vars(template, replacements)

    # 根据项目类型选择模板
    if project_type == "api":
        settings_template = SETTINGS_TEMPLATE
        conftest_template = CONFTEST_TEMPLATE
        fixtures_template = FIXTURES_INIT_TEMPLATE
        yaml_base_template = YAML_BASE_TEMPLATE  # API 项目使用默认模板
    elif project_type == "ui":
        settings_template = UI_SETTINGS_TEMPLATE
        conftest_template = UI_CONFTEST_TEMPLATE
        fixtures_template = UI_FIXTURES_INIT_TEMPLATE
        yaml_base_template = YAML_BASE_UI_TEMPLATE  # v3.45.0: UI 项目专用模板
    else:  # full
        settings_template = FULL_SETTINGS_TEMPLATE  # v3.45.0: 合并 API 和 UI 配置
        conftest_template = FULL_CONFTEST_TEMPLATE  # v3.45.0: 合并 API 和 UI 配置
        fixtures_template = FIXTURES_INIT_TEMPLATE
        yaml_base_template = YAML_BASE_FULL_TEMPLATE  # v3.45.0: Full 项目专用模板

    # 选择对应的 README 模板
    if project_type == "api":
        readme_template = README_API_TEMPLATE
    elif project_type == "ui":
        readme_template = README_UI_TEMPLATE
    else:  # full
        readme_template = README_FULL_TEMPLATE

    # 基础文件结构（所有项目类型共有）
    files_to_create = {
        # src目录
        f"src/{project_name}/__init__.py": '"""项目根模块"""\n\n__version__ = "1.0.0"\n',
        f"src/{project_name}/config/__init__.py": replace_template(
            '"""配置模块"""\n\nfrom .settings import {ProjectName}Settings\n\n__all__ = ["{ProjectName}Settings"]\n'
        ),
        f"src/{project_name}/config/settings.py": replace_template(settings_template),
        f"src/{project_name}/fixtures/__init__.py": replace_template(fixtures_template),
        # utils目录（工具函数）
        f"src/{project_name}/utils/__init__.py": replace_template(
            '"""工具函数模块"""\n\nfrom .validators import *\nfrom .converters import *\n\n__all__ = ["validators", "converters"]\n'
        ),
        f"src/{project_name}/utils/validators.py": replace_template(UTILS_VALIDATORS_TEMPLATE),
        f"src/{project_name}/utils/converters.py": replace_template(UTILS_CONVERTERS_TEMPLATE),
        # constants目录（常量定义）
        f"src/{project_name}/constants/__init__.py": replace_template(
            '"""常量模块"""\n\nfrom .error_codes import *\n\n__all__ = ["error_codes"]\n'
        ),
        f"src/{project_name}/constants/error_codes.py": replace_template(
            CONSTANTS_ERROR_CODES_TEMPLATE
        ),
        # tests目录
        "tests/__init__.py": '"""测试根模块"""\n',
        "tests/conftest.py": replace_template(conftest_template),
        "tests/data/fixtures/.gitkeep": "",
        "tests/data/files/.gitkeep": "",
        # 配置文件（pytest配置已整合到pyproject.toml）
        ".gitignore": ENHANCED_GITIGNORE_TEMPLATE,
        ".gitattributes": GITATTRIBUTES_TEMPLATE,
        ".editorconfig": EDITORCONFIG_TEMPLATE,
        "README.md": replace_template(readme_template),
        "pyproject.toml": replace_template(PYPROJECT_TOML_TEMPLATE),
        # VSCode 工作区配置
        ".vscode/settings.json": VSCODE_SETTINGS_TEMPLATE,
        ".vscode/extensions.json": VSCODE_EXTENSIONS_TEMPLATE,
        # v3.35.0+ YAML 分层配置（推荐）
        # v3.45.0: 根据项目类型使用不同的 base.yaml 模板
        "config/base.yaml": replace_template(yaml_base_template),
        "config/environments/dev.yaml": YAML_DEV_TEMPLATE,
        "config/environments/test.yaml": YAML_TEST_TEMPLATE,
        "config/environments/staging.yaml": YAML_STAGING_TEMPLATE,
        "config/environments/prod.yaml": YAML_PROD_TEMPLATE,
        "config/environments/local.yaml.example": replace_template(YAML_LOCAL_TEMPLATE),
        "config/secrets/.gitkeep": "",
        "config/secrets/.env.local.example": SECRETS_ENV_LOCAL_TEMPLATE,
        # 文档目录
        "docs/api.md": replace_template(DOCS_API_TEMPLATE),
        # 脚本目录
        "scripts/run_tests.sh": replace_template(SCRIPT_RUN_TESTS_TEMPLATE),
        "scripts/fetch_swagger.py": replace_template(SCRIPT_FETCH_SWAGGER_TEMPLATE),
        # reports子目录占位文件
        "reports/screenshots/.gitkeep": "",
        "reports/allure-results/.gitkeep": "",
        "reports/logs/.gitkeep": "",
    }

    # API项目特有文件
    if project_type in ("api", "full"):
        api_files = {
            f"src/{project_name}/apis/__init__.py": replace_template(
                f'''"""API封装模块"""

{AUTO_GENERATED_START}
{AUTO_GENERATED_WARNING}

from .base import {{ProjectName}}BaseAPI
from .example_api import ExampleAPI

__all__ = ["{{ProjectName}}BaseAPI", "ExampleAPI"]

{AUTO_GENERATED_END}


{USER_EXTENSIONS_START}
{USER_EXTENSIONS_HINT}

'''
            ),
            f"src/{project_name}/apis/base.py": replace_template(BASE_API_TEMPLATE),
            f"src/{project_name}/apis/example_api.py": replace_template(EXAMPLE_API_TEMPLATE),
            # models 目录结构（与 OpenAPI 生成器保持一致）
            f"src/{project_name}/models/__init__.py": replace_template(
                f'''"""数据模型模块

组织结构:
- requests/: 请求模型
- responses/: 响应模型
"""

{AUTO_GENERATED_START}
{AUTO_GENERATED_WARNING}

from .requests import *  # noqa: F401, F403
from .responses import *  # noqa: F401, F403

__all__ = ["requests", "responses"]

{AUTO_GENERATED_END}


{USER_EXTENSIONS_START}
{USER_EXTENSIONS_HINT}

'''
            ),
            f"src/{project_name}/models/requests/__init__.py": replace_template(
                f'''"""请求模型"""

{AUTO_GENERATED_START}
{AUTO_GENERATED_WARNING}

from .example import CreateExampleRequest, QueryExamplesRequest, UpdateExampleRequest

__all__ = ["CreateExampleRequest", "QueryExamplesRequest", "UpdateExampleRequest"]

{AUTO_GENERATED_END}


{USER_EXTENSIONS_START}
{USER_EXTENSIONS_HINT}

'''
            ),
            f"src/{project_name}/models/requests/example.py": replace_template(
                MODELS_REQUESTS_EXAMPLE_TEMPLATE
            ),
            f"src/{project_name}/models/responses/__init__.py": replace_template(
                f'''"""响应模型"""

{AUTO_GENERATED_START}
{AUTO_GENERATED_WARNING}

from .example import ApiResponse, ExampleResponse, PagedExamplesResponse

__all__ = ["ApiResponse", "ExampleResponse", "PagedExamplesResponse"]

{AUTO_GENERATED_END}


{USER_EXTENSIONS_START}
{USER_EXTENSIONS_HINT}

'''
            ),
            f"src/{project_name}/models/responses/example.py": replace_template(
                MODELS_RESPONSES_EXAMPLE_TEMPLATE
            ),
            f"src/{project_name}/repositories/__init__.py": '"""Repository层"""\n',
            f"src/{project_name}/builders/__init__.py": '"""Builder层"""\n',
            f"src/{project_name}/fixtures/data_cleaners.py": replace_template(
                DATA_CLEANERS_TEMPLATE
            ),
            "tests/api/__init__.py": '"""API测试模块"""\n',
            "tests/api/test_example.py": replace_template(TEST_EXAMPLE_TEMPLATE),
        }
        files_to_create.update(api_files)

    # UI项目特有文件
    if project_type in ("ui", "full"):
        # 创建HomePage页面对象示例
        home_page_template = replace_template(
            UI_PAGE_OBJECT_TEMPLATE.replace("{page_name}", "home")
            .replace("{PageName}", "Home")
            .replace("{page_url}", "/")
        )

        # v3.45.0: 创建 LoginPage 页面对象示例
        login_page_template = replace_template(
            UI_PAGE_OBJECT_TEMPLATE.replace("{page_name}", "login")
            .replace("{PageName}", "Login")
            .replace("{page_url}", "/login")
            .replace("{page_name_lower}", "login")
        )

        ui_files = {
            # pages 目录
            f"src/{project_name}/pages/__init__.py": replace_template(
                '"""页面对象模块"""\n\nfrom .home_page import HomePage\nfrom .login_page import LoginPage\n\n__all__ = ["HomePage", "LoginPage"]\n'
            ),
            f"src/{project_name}/pages/home_page.py": home_page_template,
            f"src/{project_name}/pages/login_page.py": login_page_template,
            # v3.45.0: actions 目录（与 HTTP 的 apis 目录对应）
            f"src/{project_name}/actions/__init__.py": replace_template(
                '"""UI Actions 模块\n\n使用 @actions_class 装饰器自动注册为 pytest fixture。\n"""\n\nfrom .login_actions import LoginActions\nfrom .user_actions import UserActions\n\n__all__ = ["LoginActions", "UserActions"]\n'
            ),
            f"src/{project_name}/actions/login_actions.py": replace_template(
                UI_APP_ACTIONS_TEMPLATE
            )
            .split("# ========== 用户管理操作 ==========")[0]
            .rstrip()
            + '\n\n\n__all__ = ["LoginActions"]\n',
            f"src/{project_name}/actions/user_actions.py": replace_template(
                '"""用户管理操作\n\n封装用户管理相关的业务操作。\n"""\n\nfrom df_test_framework.capabilities.drivers.web import AppActions\nfrom df_test_framework.testing.decorators import actions_class\n\n\n@actions_class()  # 自动命名为 user_actions\nclass UserActions(AppActions):\n    """用户管理业务操作\n\n    封装用户管理相关的操作流程。\n\n    使用示例:\n        >>> def test_create_user(login_actions, user_actions):\n        ...     login_actions.login_as_admin()\n        ...     user_id = user_actions.create_user("john", "john@example.com")\n        ...     assert user_id is not None\n    """\n\n    def create_user(self, username: str, email: str) -> str:\n        """创建新用户\n\n        Args:\n            username: 用户名\n            email: 邮箱\n\n        Returns:\n            str: 创建的用户ID\n        """\n        # 1. 导航到用户管理\n        self.page.get_by_role("link", name="Users").click()\n\n        # 2. 打开创建对话框\n        self.page.get_by_role("button", name="Add User").click()\n\n        # 3. 填写表单\n        self.page.get_by_label("Username").fill(username)\n        self.page.get_by_label("Email").fill(email)\n\n        # 4. 提交\n        self.page.get_by_role("button", name="Create").click()\n\n        # 5. 等待成功消息\n        self.page.get_by_text("User created successfully").wait_for()\n\n        # 6. 提取并返回用户ID\n        user_id = self.page.get_by_test_id("user-id").text_content()\n        return user_id or ""\n\n    def delete_user(self, username: str):\n        """删除用户\n\n        Args:\n            username: 要删除的用户名\n        """\n        # 导航到用户管理\n        self.page.get_by_role("link", name="Users").click()\n\n        # 找到用户行并点击删除\n        user_row = self.page.get_by_role("row", name=username)\n        user_row.get_by_role("button", name="Delete").click()\n\n        # 确认删除\n        self.page.get_by_role("button", name="Confirm").click()\n\n        # 等待成功消息\n        self.page.get_by_text("User deleted successfully").wait_for()\n\n\n__all__ = ["UserActions"]\n'
            ),
            # components 目录（可复用组件）
            f"src/{project_name}/components/__init__.py": replace_template(
                '"""UI 组件模块\n\n可复用的页面组件。\n"""\n\nfrom .header import Header\n\n__all__ = ["Header"]\n'
            ),
            f"src/{project_name}/components/header.py": replace_template(
                '"""Header 组件\n\n页面头部导航组件。\n"""\n\nfrom df_test_framework.capabilities.drivers.web import BaseComponent\n\n\nclass Header(BaseComponent):\n    """页面头部组件\n\n    封装页面头部的通用操作。\n\n    使用示例:\n        >>> header = Header(page)\n        >>> header.open_user_menu()\n        >>> header.click_logout()\n    """\n\n    def __init__(self, page):\n        super().__init__(page, test_id="header")\n\n    def open_user_menu(self):\n        """打开用户菜单"""\n        self.page.get_by_test_id("user-menu").click()\n\n    def click_logout(self):\n        """点击登出"""\n        self.page.get_by_role("menuitem", name="Logout").click()\n\n    def click_profile(self):\n        """点击个人资料"""\n        self.page.get_by_role("menuitem", name="Profile").click()\n\n\n__all__ = ["Header"]\n'
            ),
            # 测试目录
            "tests/ui/__init__.py": '"""UI测试模块"""\n',
            "tests/ui/test_login.py": replace_template(UI_TEST_EXAMPLE_TEMPLATE),
        }
        # UI项目也添加data_cleaners（E2E测试可能需要）
        if project_type == "ui":
            ui_files[f"src/{project_name}/fixtures/data_cleaners.py"] = replace_template(
                DATA_CLEANERS_TEMPLATE
            )
        files_to_create.update(ui_files)

    # 创建所有文件
    created_files = []
    for file_path_str, content in files_to_create.items():
        file_path = path / file_path_str
        try:
            create_file(file_path, content, force=force)
            created_files.append(file_path_str)
        except FileExistsError as e:
            print(f"⚠️  跳过: {e}")
            continue

    # 打印成功信息
    print(f"\n✅ {project_type.upper()}测试项目初始化成功！")
    print(f"📁 项目路径: {path.absolute()}\n")
    print("📋 已创建的文件:")
    for file in created_files:
        print(f"  ✓ {file}")

    print("\n🚀 下一步:")
    print(f"  1. cd {path.name}")

    if project_type in ("ui", "full"):
        print("  2. uv sync --extra ui  # 或 pip install .[ui]（安装 Playwright）")
        print("  3. playwright install  # 安装浏览器驱动")
        print("  4. uv sync --extra database-async  # (可选) 安装异步数据库驱动，性能提升 5-10 倍")
        step_num = 5
    elif project_type == "api":
        print("  2. uv sync --extra database-async  # (可选) 安装异步数据库驱动，性能提升 5-10 倍")
        step_num = 3
    else:
        step_num = 2

    print(f"  {step_num}. cp config/environments/local.yaml.example config/environments/local.yaml")
    print(f"  {step_num + 1}. cp config/secrets/.env.local.example config/secrets/.env.local")
    print(f"  {step_num + 2}. 根据需要编辑 local.yaml 和 .env.local 配置文件")

    if project_type == "api":
        print(f"  {step_num + 3}. pytest tests/api/ -v  # 运行API测试")
    elif project_type == "ui":
        print(f"  {step_num + 3}. pytest tests/ui/ -v  # 运行UI测试")
        print("\n💡 提示:")
        print("  - 使用 --headed 参数查看浏览器界面: pytest --headed")
        print("  - 使用 --browser 选择浏览器: pytest --browser firefox")
    else:  # full
        print(f"  {step_num + 3}. pytest tests/api/ -v  # 运行API测试")
        print(f"  {step_num + 4}. pytest tests/ui/ -v  # 运行UI测试")
        print("\n💡 提示:")
        print("  - UI测试: 使用 --headed 查看浏览器界面")
        print("  - 失败截图保存在 reports/screenshots/ 目录")

    print("\n📚 参考文档: https://github.com/your-org/df-test-framework")

    # 生成CI/CD配置文件（如果指定）
    if ci_platform != "none":
        print("\n🔧 生成CI/CD配置...")
        try:
            cicd_files = generate_cicd_files(path, ci_platform)
            if cicd_files:
                print(f"✅ {ci_platform.upper()} 配置已生成！")
                print("📋 CI/CD文件:")
                for file in cicd_files:
                    relative_path = file.relative_to(path)
                    print(f"  ✓ {relative_path}")

                print("\n💡 CI/CD使用提示:")
                if ci_platform in ("github-actions", "all"):
                    print("  - GitHub Actions: 在仓库Settings → Secrets中配置环境变量")
                if ci_platform in ("gitlab-ci", "all"):
                    print("  - GitLab CI: 在项目Settings → CI/CD → Variables中配置")
                if ci_platform in ("jenkins", "all"):
                    print("  - Jenkins: 在Pipeline配置中添加凭据")
                print("  - 详细文档: docs/user-guide/ci-cd.md")
        except Exception as e:
            print(f"⚠️  CI/CD配置生成失败: {e}")


__all__ = ["init_project"]
