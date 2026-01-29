# Web UI 测试使用手册

> **最后更新**: 2026-01-16
> **适用版本**: v3.0.0+（同步 AppActions），v4.0.0+（异步 AsyncAppActions）

## 概述

本指南介绍如何使用 DF Test Framework 进行 Web UI 测试，基于 Playwright 实现，采用配置驱动 + @actions_class 装饰器 + 事件驱动架构。

**框架提供两种模式**：
- **AppActions + BasePage**：同步模式（v3.0.0+），简单易用
- **AsyncAppActions + AsyncBasePage**：异步模式（v4.0.0+），性能提升 2-3 倍 ⭐ **推荐**

> **v4.0.0 重大更新**:
> - ✅ 异步 UI 测试支持（`AsyncAppActions` + `AsyncBasePage`）
> - ✅ 性能提升 2-3 倍
> - ✅ 更好的资源管理（async with 上下文管理器）
>
> 本指南主要介绍**同步版本**（向后兼容）。异步版本使用方法请参考：
> - [v4.0.0 发布说明](../releases/v4.0.0.md) - 异步 UI 测试概述
> - [五层架构详解](../architecture/五层架构详解.md#layer-2-capabilities) - AsyncAppActions 详细说明

---

## 目录

1. [快速开始](#1-快速开始)
2. [配置驱动模式](#2-配置驱动模式)
3. [核心组件](#3-核心组件)
4. [@actions_class 装饰器](#4-actions_class-装饰器)
5. [三层架构模式](#5-三层架构模式)
6. [定位器优先级](#6-定位器优先级)
7. [测试示例](#7-测试示例)
8. [事件驱动与可观测性](#8-事件驱动与可观测性)
9. [调试与可视化](#9-调试与可视化)
10. [迁移指南](#10-迁移指南)

---

## 1. 快速开始

### 1.1 安装依赖

```bash
# 安装框架（包含 UI 测试支持）
uv sync --all-extras

# 安装 Playwright 浏览器
playwright install
```

### 1.2 最简测试

```python
import pytest

@pytest.mark.ui
def test_login(page, base_url):
    """最简单的 UI 测试"""
    # 导航
    page.goto(f"{base_url}/login")

    # 填写表单（使用语义化定位）
    page.get_by_label("Username").fill("admin")
    page.get_by_label("Password").fill("admin123")
    page.get_by_role("button", name="Sign in").click()

    # 验证
    assert page.get_by_test_id("user-menu").is_visible()
```

### 1.3 配置 Web 基础 URL

```bash
# .env 文件
WEB__BASE_URL=https://your-app.example.com
WEB__BROWSER_TYPE=chromium
WEB__HEADLESS=true
```

---

## 2. 配置驱动模式

### 2.1 WebConfig 配置类

v3.42.0 新增 `WebConfig`，统一管理浏览器配置：

```python
from df_test_framework.infrastructure.config import WebConfig, FrameworkSettings

# 方式 1: 代码配置
settings = FrameworkSettings(
    web=WebConfig(
        base_url="https://example.com",
        browser_type="chromium",  # chromium | firefox | webkit
        headless=True,
        timeout=30000,            # 毫秒
        viewport={"width": 1920, "height": 1080},
        record_video=False,
        video_dir="reports/videos",
    )
)

# 方式 2: 环境变量配置（推荐）
# .env 文件
```

### 2.2 完整配置选项

```bash
# .env 文件 - Web 配置
WEB__BASE_URL=https://example.com      # 基础 URL
WEB__BROWSER_TYPE=chromium             # 浏览器类型
WEB__HEADLESS=true                     # 无头模式
WEB__SLOW_MO=0                         # 操作延迟（调试用）
WEB__TIMEOUT=30000                     # 超时时间（毫秒）
WEB__VIEWPORT__width=1280              # 视口宽度
WEB__VIEWPORT__height=720              # 视口高度
WEB__RECORD_VIDEO=false                # 是否录制视频
WEB__VIDEO_DIR=reports/videos          # 视频保存目录
```

### 2.3 与 HTTP 配置分离

```bash
# API 和 Web 可以使用不同的基础 URL
HTTP__BASE_URL=https://api.example.com      # API 地址
WEB__BASE_URL=https://web.example.com       # Web 地址
```

---

## 3. 核心组件

### 3.1 Fixtures 列表

| Fixture | 作用域 | 描述 |
|---------|--------|------|
| `browser_manager` | session | 浏览器管理器（单例） |
| `browser` | function | 浏览器实例 |
| `context` | function | 浏览器上下文（隔离） |
| `page` | function | 页面实例 |
| `app_actions` | function | 基础业务操作（v3.45.0） |
| `goto` | function | 页面导航助手 |
| `screenshot` | function | 截图助手 |

### 3.2 基础使用

```python
def test_with_page(page):
    """使用 page fixture"""
    page.goto("https://example.com")
    assert page.title() == "Example Domain"

def test_with_context(context):
    """创建独立页面"""
    page = context.new_page()
    page.goto("https://example.com")

def test_with_screenshot(page, screenshot):
    """使用截图助手"""
    page.goto("https://example.com")
    screenshot("example.png")
```

---

## 4. @actions_class 装饰器

v3.45.0 新增 `@actions_class` 装饰器，与 HTTP 的 `@api_class` 保持一致的使用体验。

### 4.1 与 HTTP 架构对比

| 维度 | HTTP | UI |
|------|------|-----|
| **装饰器** | `@api_class()` | `@actions_class()` |
| **基类** | `BaseAPI` | `AppActions` |
| **自动加载** | `load_api_fixtures()` | `load_actions_fixtures()` |
| **配置字段** | `test.apis_package` | `test.actions_package` |
| **目录** | `apis/` | `actions/` |

### 4.2 定义 Actions 类

```python
# src/my_project/actions/login_actions.py
from df_test_framework.capabilities.drivers.web import AppActions
from df_test_framework.testing.decorators import actions_class


@actions_class()  # 自动命名为 login_actions
class LoginActions(AppActions):
    """登录相关业务操作"""

    def login_as_admin(self):
        """管理员登录"""
        self.goto("/login")
        self.page.get_by_label("Username").fill("admin")
        self.page.get_by_label("Password").fill("admin123")
        self.page.get_by_role("button", name="Sign in").click()
        self.page.get_by_test_id("user-menu").wait_for()

    def login_as_user(self, username: str, password: str):
        """普通用户登录"""
        self.goto("/login")
        self.page.get_by_label("Username").fill(username)
        self.page.get_by_label("Password").fill(password)
        self.page.get_by_role("button", name="Sign in").click()

    def logout(self):
        """登出"""
        self.page.get_by_test_id("user-menu").click()
        self.page.get_by_role("menuitem", name="Logout").click()
```

### 4.3 配置自动发现

```python
# conftest.py
from df_test_framework.testing.decorators import load_actions_fixtures

def _get_actions_package() -> str:
    """获取 Actions 包路径（优先配置，否则默认值）"""
    default_package = "my_project.actions"
    try:
        from df_test_framework.infrastructure.config import get_config
        config = get_config()
        return config.get("test", {}).get("actions_package") or default_package
    except Exception:
        return default_package

# 自动加载所有 @actions_class 装饰的类
load_actions_fixtures(globals(), actions_package=_get_actions_package())
```

### 4.4 在测试中使用

```python
@pytest.mark.ui
def test_login(login_actions):
    """login_actions 由 @actions_class 自动注册"""
    login_actions.login_as_admin()
    assert login_actions.page.get_by_test_id("user-menu").is_visible()


@pytest.mark.ui
def test_user_management(login_actions, user_actions):
    """组合使用多个 Actions"""
    # 登录
    login_actions.login_as_admin()

    # 创建用户
    user_id = user_actions.create_user("john", "john@example.com")

    # 验证
    assert user_id
    assert login_actions.page.get_by_text("john").is_visible()
```

### 4.5 项目目录结构

```
src/my_project/
├── actions/                    # Actions 目录（对应 HTTP 的 apis/）
│   ├── __init__.py
│   ├── login_actions.py        # @actions_class 自动注册
│   └── user_actions.py
├── pages/                      # 页面对象（可选）
│   └── login_page.py
├── components/                 # 可复用组件（可选）
│   └── header.py
└── config/
    └── settings.py
```

### 4.6 UI 操作辅助方法（v3.46.0）

v3.46.0 新增 UI 操作辅助方法，**自动发布 UIActionEvent 事件**，实现与 HTTP 测试一致的调试输出和 Allure 记录。

#### 两种操作方式对比

框架同时支持两种方式，根据需求选择：

| 方式 | 调试输出 | Allure 记录 | 使用场景 | 推荐度 |
|------|---------|------------|---------|--------|
| **辅助方法** | ✅ 自动输出 | ✅ 自动记录 | 常规业务操作 | ⭐⭐⭐⭐⭐ |
| **Playwright API** | ❌ 无输出 | ❌ 无记录 | 复杂操作、特殊场景 | ⭐⭐⭐ |
| **Playwright API + 手动发布** | ✅ 手动输出 | ✅ 手动记录 | 需要自定义事件描述 | ⭐⭐⭐⭐ |

#### 方式 1: 使用辅助方法（推荐）

辅助方法会自动发布 UIActionEvent，无需手动操作：

```python
@actions_class()
class LoginActions(AppActions):
    """登录相关业务操作"""

    def login_as_admin(self):
        """使用辅助方法 - 自动记录日志和 Allure"""
        self.goto("/login")

        # ✅ 使用辅助方法（推荐）
        self.fill_input('input[name="username"]', "admin", "用户名输入框")
        self.fill_input('input[type="password"]', "admin123", "密码输入框")
        self.click('button[type="submit"]', "登录按钮")

        # 等待登录成功
        self.wait_for_text("Welcome")
```

**调试输出示例**：

```
────────────────────────────────────────────────────────
📝 填写 [用户名输入框]: admin
────────────────────────────────────────────────────────
────────────────────────────────────────────────────────
📝 填写 [密码输入框]: admin123
────────────────────────────────────────────────────────
────────────────────────────────────────────────────────
👆 点击 [登录按钮]
────────────────────────────────────────────────────────
```

#### 方式 2: 使用 Playwright 原生 API

对于复杂操作或辅助方法不支持的场景，可以直接使用 Playwright API：

```python
@actions_class()
class LoginActions(AppActions):
    """登录相关业务操作"""

    def login_as_admin(self):
        """使用 Playwright 原生 API - 无自动日志"""
        self.goto("/login")

        # ✅ 使用 Playwright 原生 API（适合复杂操作）
        self.page.get_by_label("Username").fill("admin")
        self.page.get_by_label("Password").fill("admin123")
        self.page.get_by_role("button", name="Sign in").click()

        # 等待登录成功
        self.page.get_by_test_id("user-menu").wait_for()
```

**注意**: 使用原生 API 不会自动输出调试信息和 Allure 记录。

#### 方式 3: Playwright API + 手动发布事件

如果需要使用原生 API 同时获得调试输出，可以手动发布事件：

```python
@actions_class()
class LoginActions(AppActions):
    """登录相关业务操作"""

    def login_as_admin(self):
        """使用 Playwright API + 手动发布事件"""
        self.goto("/login")

        # 手动发布事件 + 执行操作
        username_input = self.page.get_by_label("Username")
        self._publish_ui_action_event("fill", value="admin", description="用户名输入框")
        username_input.fill("admin")

        password_input = self.page.get_by_label("Password")
        self._publish_ui_action_event("fill", value="admin123", description="密码输入框")
        password_input.fill("admin123")

        login_button = self.page.get_by_role("button", name="Sign in")
        self._publish_ui_action_event("click", description="登录按钮")
        login_button.click()

        # 等待登录成功
        self.page.get_by_test_id("user-menu").wait_for()
```

**调试输出**: 与方式 1 相同，会输出彩色日志并记录到 Allure。

**参数说明**：
- `action`: 操作类型（必需）- `"fill"`, `"click"`, `"select"`, `"check"`, `"wait"`
- `selector`: 元素选择器（可选）- 用于调试定位，可以省略
- `value`: 操作值（可选）- 填写的内容
- `description`: 操作描述（推荐）- 显示在日志中的友好描述

#### 辅助方法 API 参考

| 方法 | 参数 | 说明 |
|------|------|------|
| `fill_input(selector, value, description)` | selector: 元素选择器<br>value: 填写的值<br>description: 操作描述 | 填写输入框 |
| `click(selector, description)` | selector: 元素选择器<br>description: 操作描述 | 点击元素 |
| `select_option(selector, value, description)` | selector: 元素选择器<br>value: 选项值<br>description: 操作描述 | 选择下拉选项 |
| `check(selector, description)` | selector: 元素选择器<br>description: 操作描述 | 勾选复选框 |
| `wait_for_text(text, timeout)` | text: 等待的文本<br>timeout: 超时时间（毫秒） | 等待文本出现 |

#### 选择建议

**使用辅助方法**（推荐）：
- ✅ 常规表单操作（填写、点击、选择）
- ✅ 需要调试输出和 Allure 记录
- ✅ 团队协作，统一操作风格

**使用 Playwright API**：
- ✅ 复杂操作（拖拽、键盘快捷键、多步骤交互）
- ✅ 辅助方法不支持的场景
- ✅ 需要精细控制的场景

**使用 Playwright API + 手动发布**：
- ✅ 需要使用原生 API 的复杂操作
- ✅ 同时需要调试输出和 Allure 记录
- ✅ 需要自定义事件描述

#### 混合使用示例

实际项目中，可以根据场景灵活组合：

```python
@actions_class()
class UserActions(AppActions):
    """用户管理操作"""

    def create_user(self, username: str, email: str) -> str:
        """创建用户 - 混合使用辅助方法和原生 API"""
        # 导航到用户管理页
        self.goto("/users")

        # 使用辅助方法：常规操作
        self.click('button[data-testid="add-user-btn"]', "添加用户按钮")

        # 使用辅助方法：表单填写
        self.fill_input('input[name="username"]', username, "用户名输入框")
        self.fill_input('input[name="email"]', email, "邮箱输入框")

        # 使用原生 API：复杂操作（上传头像）
        file_input = self.page.locator('input[type="file"]')
        file_input.set_input_files("avatar.png")

        # 使用辅助方法：提交表单
        self.click('button[type="submit"]', "提交按钮")

        # 使用原生 API：等待并提取结果
        self.page.wait_for_selector('.user-id')
        user_id = self.page.locator('.user-id').text_content()

        return user_id or ""
```

---

## 5. 三层架构模式

v3.43.0 采用现代 UI 测试最佳实践：

```
App Actions (业务操作)  ← 封装完整业务流程
    ↓
Components (可复用组件) ← 封装 UI 组件
    ↓
Playwright API (直接使用) ← 不过度封装
```

### 4.1 BaseComponent - 组件层

封装可复用的 UI 组件（如表单、导航栏、对话框）：

```python
from df_test_framework.capabilities.drivers.web import BaseComponent

class LoginForm(BaseComponent):
    """登录表单组件"""

    def __init__(self, page):
        # 使用 test-id 定位组件根元素
        super().__init__(page, test_id="login-form")

    def submit(self, username: str, password: str):
        """填写并提交表单"""
        # 组件内使用语义化定位
        self.get_by_label("Username").fill(username)
        self.get_by_label("Password").fill(password)
        self.get_by_role("button", name="Sign in").click()


class Header(BaseComponent):
    """页头组件"""

    def __init__(self, page):
        super().__init__(page, test_id="header")

    def open_user_menu(self):
        self.get_by_test_id("user-menu").click()

    def logout(self):
        self.open_user_menu()
        self.get_by_role("menuitem", name="Logout").click()
```

### 4.2 BasePage - 页面层

表示一个具体的页面：

```python
from df_test_framework.capabilities.drivers.web import BasePage

class LoginPage(BasePage):
    """登录页面"""

    def __init__(self, page, base_url: str = "", runtime=None):
        super().__init__(page, url="/login", base_url=base_url, runtime=runtime)
        # 组合使用组件
        self.login_form = LoginForm(page)
        self.header = Header(page)

    def wait_for_page_load(self):
        """等待页面加载完成（必须实现）"""
        self.page.get_by_test_id("login-form").wait_for()

    def login(self, username: str, password: str):
        """业务操作：登录"""
        self.login_form.submit(username, password)
        # 等待登录成功
        self.page.get_by_test_id("user-menu").wait_for()
```

### 4.3 AppActions - 业务操作层

封装跨页面的完整业务流程：

```python
from df_test_framework.capabilities.drivers.web import AppActions

class MyAppActions(AppActions):
    """应用业务操作"""

    def __init__(self, page, base_url: str = "", runtime=None):
        super().__init__(page, base_url=base_url, runtime=runtime)

    def login_as_admin(self):
        """管理员登录"""
        self.goto("/login")
        self.page.get_by_label("Username").fill("admin")
        self.page.get_by_label("Password").fill("admin123")
        self.page.get_by_role("button", name="Sign in").click()
        self.page.get_by_test_id("user-menu").wait_for()

    def create_user(self, username: str, email: str) -> str:
        """创建用户并返回用户 ID"""
        # 1. 导航到用户管理
        self.page.get_by_role("link", name="Users").click()
        # 2. 打开创建对话框
        self.page.get_by_role("button", name="Add User").click()
        # 3. 填写表单
        self.page.get_by_label("Username").fill(username)
        self.page.get_by_label("Email").fill(email)
        # 4. 提交
        self.page.get_by_role("button", name="Create").click()
        # 5. 等待成功
        self.page.get_by_text("User created").wait_for()
        # 6. 返回结果
        return self.page.get_by_test_id("user-id").text_content() or ""
```

---

## 6. 定位器优先级

### 6.1 优先级顺序

| 优先级 | 方法 | 示例 | 说明 |
|--------|------|------|------|
| **1** | `get_by_test_id()` | `get_by_test_id("submit-btn")` | ✅ 最稳定 |
| **2** | `get_by_role()` | `get_by_role("button", name="Submit")` | ✅ 语义化 |
| **3** | `get_by_label()` | `get_by_label("Username")` | ✅ 表单字段 |
| **4** | `get_by_placeholder()` | `get_by_placeholder("Enter email")` | 表单备选 |
| **5** | `get_by_text()` | `get_by_text("Welcome")` | 文本内容 |
| **6** | `locator()` | `locator("#username")` | ⚠️ CSS/XPath |

### 6.2 推荐的前端规范

```html
<!-- ✅ 推荐：添加 data-testid -->
<form data-testid="login-form">
  <input data-testid="username-input" aria-label="Username" />
  <input data-testid="password-input" aria-label="Password" type="password" />
  <button data-testid="submit-btn" type="submit">Sign in</button>
</form>

<!-- ❌ 不推荐：依赖动态 CSS 类名 -->
<form class="LoginForm__container-x7k9s">
  <input class="Input__field-2h8s" />
</form>
```

---

## 7. 测试示例

### 7.1 直接使用 Playwright API

```python
@pytest.mark.ui
def test_simple_login(page, base_url):
    """简单测试 - 直接使用 Playwright API"""
    page.goto(f"{base_url}/login")

    page.get_by_label("Username").fill("admin")
    page.get_by_label("Password").fill("admin123")
    page.get_by_role("button", name="Sign in").click()

    assert page.get_by_test_id("user-menu").is_visible()
    assert page.get_by_text("Welcome, admin").is_visible()
```

### 7.2 使用 Page Object

```python
@pytest.mark.ui
def test_with_page_object(page, base_url):
    """使用 Page Object 模式"""
    from my_project.pages.login_page import LoginPage

    login_page = LoginPage(page, base_url=base_url)
    login_page.goto()
    login_page.login("admin", "admin123")

    assert page.get_by_test_id("user-menu").is_visible()
```

### 7.3 使用 @actions_class（推荐）

```python
# 使用 @actions_class 自动注册的 fixture
@pytest.mark.ui
def test_login(login_actions):
    """login_actions 由 @actions_class 自动注册"""
    login_actions.login_as_admin()
    assert login_actions.page.get_by_test_id("user-menu").is_visible()


@pytest.mark.ui
def test_user_flow(login_actions, user_actions):
    """组合使用多个 Actions"""
    login_actions.login_as_admin()
    user_id = user_actions.create_user("john", "john@example.com")
    assert user_id
```

### 7.4 使用 Component

```python
@pytest.mark.ui
def test_with_components(page, base_url):
    """使用组件模式"""
    from my_project.components.header import Header

    page.goto(f"{base_url}/dashboard")

    header = Header(page)
    header.open_user_menu()
    header.logout()

    assert page.get_by_role("heading", name="Login").is_visible()
```

---

## 8. 事件驱动与可观测性

v3.44.0 新增事件驱动架构，与 HTTP 测试保持一致的可观测性。

### 8.1 自动事件发布

框架自动捕获并发布以下事件：

| 事件类型 | 描述 | 触发方式 | 版本 |
|---------|------|---------|------|
| `UIActionEvent` | AppActions 业务操作（填写、点击等） | 辅助方法自动发布 / 手动发布 | v3.46.0 |
| `WebBrowserEvent` | 浏览器事件（console error/warning、dialog） | BrowserManager 自动发布 | v3.44.0 |
| `UIErrorEvent` | 页面错误/崩溃 | BrowserManager 自动发布 | v3.44.0 |

**事件说明**：

- **UIActionEvent**: 记录 AppActions 的业务操作，与 HTTP 的 `HttpRequestStartEvent` 对应
  - 使用辅助方法（`fill_input`、`click` 等）自动发布
  - 使用 Playwright 原生 API 需要手动发布（调用 `_publish_ui_action_event`）
  - 自动输出到控制台调试器和 Allure 报告

- **WebBrowserEvent**: 记录浏览器底层事件（v3.46.1 优化，只保留有价值的事件）
  - Console error/warning（帮助发现 JS 错误）
  - Dialog（alert/confirm/prompt）
  - 自动发布，无需手动操作

- **UIErrorEvent**: 记录页面错误和崩溃
  - Page error（未捕获的异常）
  - Page crash（页面崩溃）
  - 自动发布，无需手动操作

### 8.2 Allure 自动集成

事件自动记录到 Allure 报告，无需额外配置：

- **UIActionEvent**: UI 操作步骤（填写、点击等）
- **WebBrowserEvent**: Console 输出、弹窗
- **UIErrorEvent**: 页面错误和崩溃

### 8.3 调试输出示例

#### 使用辅助方法（自动输出）

```python
@actions_class()
class LoginActions(AppActions):
    def login_as_admin(self):
        self.goto("/login")
        self.fill_input('input[name="username"]', "admin", "用户名输入框")
        self.click('button[type="submit"]', "登录按钮")
```

**控制台输出**：

```
────────────────────────────────────────────────────────
📝 填写 [用户名输入框]: admin
────────────────────────────────────────────────────────

────────────────────────────────────────────────────────
👆 点击 [登录按钮]
────────────────────────────────────────────────────────

────────────────────────────────────────────────────────
❌ Console [error]: Uncaught TypeError: Cannot read property 'foo'
────────────────────────────────────────────────────────
```

#### 使用 Playwright API（无输出）

```python
@actions_class()
class LoginActions(AppActions):
    def login_as_admin(self):
        self.goto("/login")
        # ❌ 使用原生 API - 无调试输出
        self.page.get_by_label("Username").fill("admin")
        self.page.get_by_role("button", name="Submit").click()
```

**控制台输出**：

```
# 无 UIActionEvent 输出
# 只有 WebBrowserEvent（console error/warning、dialog）
────────────────────────────────────────────────────────
❌ Console [error]: Uncaught TypeError: Cannot read property 'foo'
────────────────────────────────────────────────────────
```

#### 手动发布事件（自定义输出）

```python
@actions_class()
class LoginActions(AppActions):
    def login_as_admin(self):
        self.goto("/login")

        # ✅ 手动发布事件 + 原生 API（简化写法）
        username_input = self.page.get_by_label("Username")
        self._publish_ui_action_event("fill", value="admin", description="用户名输入框")
        username_input.fill("admin")

        login_button = self.page.get_by_role("button", name="Submit")
        self._publish_ui_action_event("click", description="登录按钮")
        login_button.click()
```

**控制台输出**：

```
────────────────────────────────────────────────────────
📝 填写 [用户名输入框]: admin
────────────────────────────────────────────────────────

────────────────────────────────────────────────────────
👆 点击 [登录按钮]
────────────────────────────────────────────────────────
```

**提示**: `selector` 参数是可选的，通常只需要提供 `action`、`value`（如果有）和 `description` 即可。

---

## 9. 调试与可视化

在开发和调试 UI 测试时，能够看到浏览器的实际操作过程非常重要。框架提供了多种方式来可视化测试执行。

### 9.1 查看浏览器操作

#### 有头模式（Headed Mode）

默认情况下，测试在无头模式下运行（不显示浏览器窗口）。开发调试时可以显示浏览器窗口：

```bash
# 方式 1: 环境变量配置
WEB__HEADLESS=false uv run pytest tests/ui/ -v

# 方式 2: 配置文件
# config/environments/local.yaml
web:
  headless: false
```

然后运行：
```bash
uv run pytest tests/ui/ --env=local -v
```

#### 慢速模式（Slow Motion）

减慢操作速度，便于观察每个步骤：

```bash
# 每个操作延迟 1000 毫秒（1 秒）
WEB__SLOW_MO=1000 uv run pytest tests/ui/ -v

# 或在配置文件中设置
# config/environments/local.yaml
web:
  headless: false
  slow_mo: 1000  # 毫秒
```

#### Playwright Inspector 调试

使用 Playwright 的内置调试工具，可以逐步执行测试：

```bash
# Windows PowerShell
$env:PWDEBUG = "1"
uv run pytest tests/ui/test_login.py

# Windows CMD
set PWDEBUG=1
uv run pytest tests/ui/test_login.py

# Linux/Mac
PWDEBUG=1 uv run pytest tests/ui/test_login.py
```

Inspector 功能：
- 逐步执行每个操作
- 查看元素定位器
- 实时修改定位器并测试
- 查看页面快照

### 9.2 视频录制

#### 配置视频录制

```yaml
# config/test.yaml 或 config/environments/local.yaml
web:
  record_video: true              # 启用视频录制
  video_dir: reports/videos       # 视频保存目录
```

或使用环境变量：
```bash
WEB__RECORD_VIDEO=true WEB__VIDEO_DIR=reports/videos uv run pytest tests/ui/ -v
```

#### 失败时录制（推荐）

为了节省存储空间，可以配置仅在测试失败时保留视频：

```yaml
web:
  record_video: on-failure  # 仅失败时保留
  video_dir: reports/videos
```

#### 查看录制的视频

```bash
# 视频保存在配置的目录中
ls reports/videos/

# Windows 打开视频目录
start reports/videos

# Linux/Mac
open reports/videos
```

### 9.3 截图

#### 自动截图配置

```yaml
# config/test.yaml
web:
  screenshot_on_failure: true     # 失败时自动截图
  screenshot_dir: reports/screenshots
```

#### 手动截图

在测试代码中手动截图：

```python
def test_with_screenshot(page, screenshot):
    """使用 screenshot fixture"""
    page.goto("https://example.com")

    # 截取整个页面
    screenshot("example_page.png")

    # 或直接使用 page 对象
    page.screenshot(path="reports/screenshots/custom.png")

    # 截取特定元素
    page.locator("#header").screenshot(path="reports/screenshots/header.png")
```

### 9.4 调试最佳实践

#### 本地开发调试工作流

```bash
# 1. 开发阶段：有头模式 + 慢速
WEB__HEADLESS=false WEB__SLOW_MO=500 uv run pytest tests/ui/test_login.py -v -s

# 2. 遇到问题：使用 Inspector 逐步调试
PWDEBUG=1 uv run pytest tests/ui/test_login.py

# 3. 验证修复：正常速度有头模式
WEB__HEADLESS=false uv run pytest tests/ui/ -v

# 4. CI 准备：无头模式 + 视频录制
uv run pytest tests/ui/ -v  # 使用默认配置
```

#### 组合使用调试选项

```bash
# 有头 + 慢速 + DEBUG 日志 + 显示 print
WEB__HEADLESS=false WEB__SLOW_MO=1000 \
  uv run pytest tests/ui/ --env=local --log-cli-level=DEBUG -v -s

# 失败时进入 pdb 调试器
WEB__HEADLESS=false \
  uv run pytest tests/ui/ --env=local --pdb -v

# 只运行失败的测试（快速迭代）
uv run pytest tests/ui/ --env=local --lf -v
```

#### 在代码中添加断点

```python
def test_login_flow(page, base_url):
    """调试登录流程"""
    page.goto(f"{base_url}/login")

    # 添加断点，暂停执行
    breakpoint()  # Python 3.7+

    # 或使用 page.pause() 打开 Playwright Inspector
    page.pause()

    page.get_by_label("Username").fill("admin")
    page.get_by_label("Password").fill("admin123")
    page.get_by_role("button", name="Sign in").click()
```

### 9.5 浏览器选择

测试不同浏览器的兼容性：

```bash
# Chromium（默认）
WEB__BROWSER_TYPE=chromium uv run pytest tests/ui/ -v

# Firefox
WEB__BROWSER_TYPE=firefox uv run pytest tests/ui/ -v

# WebKit (Safari 引擎)
WEB__BROWSER_TYPE=webkit uv run pytest tests/ui/ -v
```

### 9.6 调试配置示例

创建专门的调试配置文件：

```yaml
# config/environments/debug.yaml
_extends: environments/local.yaml
env: debug
debug: true

web:
  base_url: "http://localhost:3000"
  browser_type: chromium
  headless: false           # 显示浏览器
  slow_mo: 500              # 减慢操作
  timeout: 60000            # 延长超时
  viewport:
    width: 1920
    height: 1080
  record_video: on-failure  # 失败时录制
  video_dir: reports/videos
  screenshot_on_failure: true
  screenshot_dir: reports/screenshots

logging:
  level: DEBUG
  format: text
  sanitize: false

observability:
  debug_output: true
```

使用调试配置：
```bash
uv run pytest tests/ui/ --env=debug -v -s
```

### 9.7 常见调试场景

#### 元素定位问题

```python
def test_debug_locator(page):
    """调试元素定位"""
    page.goto("https://example.com")

    # 使用 page.pause() 打开 Inspector
    page.pause()

    # 在 Inspector 中测试不同的定位器
    # 找到正确的定位器后，更新测试代码
    element = page.get_by_test_id("submit-btn")
    element.click()
```

#### 等待时间问题

```python
def test_debug_timing(page):
    """调试等待时间"""
    page.goto("https://example.com")

    # 增加超时时间
    page.wait_for_selector("#dynamic-content", timeout=60000)

    # 或使用网络空闲等待
    page.wait_for_load_state("networkidle")
```

#### 查看网络请求

```python
def test_debug_network(page):
    """调试网络请求"""
    # 监听所有请求
    page.on("request", lambda request: print(f">> {request.method} {request.url}"))
    page.on("response", lambda response: print(f"<< {response.status} {response.url}"))

    page.goto("https://example.com")
    page.get_by_role("button", name="Load Data").click()

    # 查看控制台输出
```

---

## 10. 迁移指南

### 10.1 从旧版迁移

**v3.42.0 之前**（配置型 fixtures）：
```python
# ❌ 旧方式 - 多个配置 fixtures
@pytest.fixture
def browser_type():
    return BrowserType.CHROMIUM

@pytest.fixture
def browser_headless():
    return True
```

**v3.42.0+**（配置驱动）：
```python
# ✅ 新方式 - 统一使用 WebConfig
# .env 文件
WEB__BROWSER_TYPE=chromium
WEB__HEADLESS=true
```

### 10.2 从传统 POM 迁移

**传统 POM**（过度封装）：
```python
# ❌ 不推荐
class LoginPage(BasePage):
    def fill_username(self, value):
        self.fill("#username", value)

    def fill_password(self, value):
        self.fill("#password", value)

    def click_submit(self):
        self.click("button")
```

**现代模式**（语义化 + 直接操作）：
```python
# ✅ 推荐
class LoginPage(BasePage):
    def login(self, username: str, password: str):
        # 直接使用 Playwright API
        self.page.get_by_label("Username").fill(username)
        self.page.get_by_label("Password").fill(password)
        self.page.get_by_role("button", name="Sign in").click()
```

### 10.3 渐进式迁移策略

```python
# 阶段 1: 保持现有代码（兼容）
class LoginPage(BasePage):
    def login(self, username, password):
        self.fill("#username", username)  # 旧方式仍然工作

# 阶段 2: 引入语义化定位
class LoginPage(BasePage):
    def login(self, username, password):
        self.page.get_by_label("Username").fill(username)  # 新方式

# 阶段 3: 引入组件化（可选）
class LoginPage(BasePage):
    def __init__(self, page, base_url=""):
        super().__init__(page, url="/login", base_url=base_url)
        self.login_form = LoginForm(page)  # 组件化
```

---

## 最佳实践总结

### ✅ DO

1. **使用 Test ID** - 最稳定的定位方式
2. **语义化定位优先** - `get_by_role`, `get_by_label`
3. **组件化** - 封装可复用的 UI 组件
4. **App Actions** - 封装高级业务流程
5. **直接使用 Playwright API** - 不过度封装
6. **配置驱动** - 使用 WebConfig 统一管理

### ❌ DON'T

1. **过度封装** - 不要为每个元素创建方法
2. **脆弱定位** - 避免依赖动态 CSS 类名
3. **硬编码等待** - `sleep(3)` ❌，使用 Playwright 的自动等待
4. **重复代码** - 使用组件和 App Actions 复用

---

## 参考资料

- [v3.42.0 发布说明](../releases/v3.42.0.md) - 配置驱动模式
- [v3.43.0 发布说明](../releases/v3.43.0.md) - 现代 UI 测试最佳实践
- [v3.44.0 发布说明](../releases/v3.44.0.md) - 事件驱动架构
- [v3.45.0 发布说明](../releases/v3.45.0.md) - @actions_class 装饰器
- [架构设计文档](../architecture/README.md)
- [Playwright 官方文档](https://playwright.dev/python/)
