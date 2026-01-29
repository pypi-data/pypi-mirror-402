# UI 测试最佳实践（2026）与框架集成方案

## 当前 UI 测试最佳实践演进

### 1. 传统 Page Object Model (POM) - 我们当前使用的

```python
# 传统 POM（我们当前的实现）
class LoginPage(BasePage):
    def __init__(self, page, base_url=""):
        super().__init__(page, url="/login", base_url=base_url)
        self.username_input = "#username"
        self.password_input = "#password"
        self.submit_button = "button[type='submit']"

    def login(self, username: str, password: str):
        self.fill(self.username_input, username)
        self.fill(self.password_input, password)
        self.click(self.submit_button)
```

**问题**：
- ❌ CSS 选择器脆弱（`#username` 容易变化）
- ❌ 过度封装（每个元素操作都封装一层）
- ❌ 不利用 Playwright 的现代特性（auto-waiting, 语义化定位）

---

## 2. Playwright 官方推荐模式（2024-2026）

### 核心理念转变

| 传统 POM | Playwright 推荐 |
|---------|----------------|
| 封装所有元素定位器 | 使用语义化定位（role, text, label） |
| 每个操作都是方法 | 直接使用 Playwright API |
| Page 级别封装 | Component 级别封装 + App Actions |
| CSS/XPath 优先 | Test ID 和 ARIA role 优先 |

### 最佳实践：三层模式

```
App Actions (业务操作)
    ↓
Components (可复用组件)
    ↓
Playwright API (直接使用)
```

---

## 3. 现代最佳实践示例

### 3.1 不推荐：过度封装 ❌

```python
class LoginPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.username = "#username"
        self.password = "#password"
        self.submit = "button"

    def fill_username(self, value):  # ❌ 过度封装
        self.fill(self.username, value)

    def fill_password(self, value):  # ❌ 过度封装
        self.fill(self.password, value)

    def click_submit(self):  # ❌ 过度封装
        self.click(self.submit)

# 测试
def test_login(page):
    login_page = LoginPage(page)
    login_page.fill_username("admin")  # ❌ 繁琐
    login_page.fill_password("password")
    login_page.click_submit()
```

### 3.2 推荐：语义化定位 + 直接操作 ✅

```python
class LoginPage(BasePage):
    def __init__(self, page, base_url=""):
        super().__init__(page, url="/login", base_url=base_url)

    # 只封装复杂的业务操作，不封装单个元素
    def login(self, username: str, password: str):
        """执行登录操作"""
        # ✅ 使用语义化定位
        self.page.get_by_label("Username").fill(username)
        self.page.get_by_label("Password").fill(password)
        self.page.get_by_role("button", name="Sign in").click()

# 测试
def test_login(page):
    login_page = LoginPage(page)
    login_page.login("admin", "password")  # ✅ 简洁
```

### 3.3 更推荐：Test ID + Components + App Actions ⭐

```python
# ========== 1. Component 封装（可复用组件）==========

class LoginForm:
    """登录表单组件（可能在多个页面使用）"""

    def __init__(self, page):
        self.page = page
        # ✅ 使用 test-id（最稳定）
        self.form = page.get_by_test_id("login-form")

    def login(self, username: str, password: str):
        """填写登录表单"""
        # ✅ 在组件范围内定位
        self.form.get_by_label("Username").fill(username)
        self.form.get_by_label("Password").fill(password)
        self.form.get_by_role("button", name="Sign in").click()


# ========== 2. Page Object（业务页面）==========

class LoginPage(BasePage):
    """登录页面"""

    def __init__(self, page, base_url=""):
        super().__init__(page, url="/login", base_url=base_url)
        self.login_form = LoginForm(page)  # ✅ 组合组件

    def wait_for_page_load(self):
        self.page.get_by_test_id("login-form").wait_for()


# ========== 3. App Actions（高级业务操作）==========

class AppActions:
    """应用级别的业务操作"""

    def __init__(self, page, base_url=""):
        self.page = page
        self.base_url = base_url

    def login_as_admin(self):
        """以管理员身份登录（常用操作）"""
        login_page = LoginPage(self.page, self.base_url)
        login_page.goto()
        login_page.login_form.login("admin", "admin123")
        # 等待登录成功
        self.page.get_by_test_id("user-menu").wait_for()

    def login_as_user(self, username: str, password: str):
        """以普通用户登录"""
        login_page = LoginPage(self.page, self.base_url)
        login_page.goto()
        login_page.login_form.login(username, password)


# ========== 测试使用 ==========

def test_admin_can_access_dashboard(page, app_actions):
    """测试管理员可以访问仪表板"""
    # ✅ 使用高级业务操作
    app_actions.login_as_admin()

    # ✅ 直接使用 Playwright API（不过度封装）
    page.get_by_role("link", name="Dashboard").click()

    # ✅ 语义化断言
    assert page.get_by_role("heading", name="Dashboard").is_visible()


def test_user_profile(page, app_actions):
    """测试用户资料页面"""
    app_actions.login_as_admin()

    # ✅ 直接操作，代码可读性高
    page.get_by_test_id("user-menu").click()
    page.get_by_role("menuitem", name="Profile").click()

    # ✅ 表单填写也可以直接写
    page.get_by_label("Email").fill("admin@example.com")
    page.get_by_role("button", name="Save").click()
```

---

## 4. 定位器优先级（Playwright 官方推荐）

### 优先级从高到低

| 优先级 | 定位方式 | 示例 | 原因 |
|-------|---------|------|------|
| 1 | **Test ID** | `get_by_test_id("submit-btn")` | 最稳定，专为测试设计 |
| 2 | **Role + Name** | `get_by_role("button", name="Submit")` | 语义化，有利于可访问性 |
| 3 | **Label** | `get_by_label("Username")` | 表单字段首选 |
| 4 | **Placeholder** | `get_by_placeholder("Enter email")` | 表单字段备选 |
| 5 | **Text** | `get_by_text("Welcome back")` | 文本内容定位 |
| 6 | CSS/XPath | `locator("#username")` | ⚠️ 最后选择，易碎 |

### 前端协作：Test ID 规范

```html
<!-- ✅ 推荐：添加 test-id -->
<form data-testid="login-form">
  <input data-testid="username-input" aria-label="Username" />
  <input data-testid="password-input" aria-label="Password" type="password" />
  <button data-testid="submit-btn" type="submit">Sign in</button>
</form>

<!-- ❌ 不推荐：依赖 CSS 类名（易变化） -->
<form class="LoginForm__container-x7k9s">
  <input class="Input__field-2h8s" />
</form>
```

---

## 5. 与我们框架的集成方案

### 方案 A：渐进式升级（推荐）⭐

保留现有 BasePage，新增现代模式支持：

```python
# ========== 1. 新增 BaseComponent ==========
# src/df_test_framework/capabilities/drivers/web/playwright/component.py

class BaseComponent:
    """可复用组件基类

    用于封装页面中的独立组件（如 Header, Footer, LoginForm）

    v3.43.0: 新增
    """

    def __init__(self, page: Page, test_id: str | None = None):
        self.page = page
        # 组件根元素
        self.root = page.get_by_test_id(test_id) if test_id else page

    # 组件内的定位都基于 self.root
    def get_by_role(self, role: str, **kwargs):
        return self.root.get_by_role(role, **kwargs)

    def get_by_label(self, label: str, **kwargs):
        return self.root.get_by_label(label, **kwargs)


# ========== 2. 新增 AppActions ==========
# src/df_test_framework/capabilities/drivers/web/app_actions.py

class AppActions:
    """应用业务操作基类

    封装高级业务操作，提高测试复用性

    v3.43.0: 新增

    Example:
        >>> class MyAppActions(AppActions):
        ...     def login_as_admin(self):
        ...         # 复杂的登录流程
        ...         pass
    """

    def __init__(self, page: Page, base_url: str = ""):
        self.page = page
        self.base_url = base_url


# ========== 3. 保留 BasePage，增强功能 ==========
# src/df_test_framework/capabilities/drivers/web/playwright/page.py

class BasePage(ABC):
    """页面对象基类

    v3.43.0: 新增现代定位方法，推荐使用 Playwright 原生 API
    """

    def __init__(self, page: Page, url: str | None = None, base_url: str = ""):
        self.page = page  # ✅ 直接暴露 page，鼓励使用原生 API
        self.url = url
        self.base_url = base_url

    # ✅ 新增：直接暴露 Playwright 现代定位方法
    def get_by_test_id(self, test_id: str):
        """通过 test-id 定位（推荐）"""
        return self.page.get_by_test_id(test_id)

    def get_by_role(self, role: str, **kwargs):
        """通过 ARIA role 定位（推荐）"""
        return self.page.get_by_role(role, **kwargs)

    # 保留原有方法用于兼容...
```

### 方案 B：提供两种模式模板

```python
# ========== 模板 1: 传统 POM（适合简单项目）==========
# templates/project/pages/login_page_traditional.py

class LoginPage(BasePage):
    """登录页面（传统 POM 模式）"""

    def __init__(self, page, base_url=""):
        super().__init__(page, url="/login", base_url=base_url)

    def login(self, username: str, password: str):
        # 使用 CSS 定位
        self.fill("#username", username)
        self.fill("#password", password)
        self.click("button[type='submit']")


# ========== 模板 2: 现代模式（推荐）==========
# templates/project/pages/login_page_modern.py

class LoginForm(BaseComponent):
    """登录表单组件"""

    def __init__(self, page):
        super().__init__(page, test_id="login-form")

    def fill_and_submit(self, username: str, password: str):
        """填写并提交登录表单"""
        self.get_by_label("Username").fill(username)
        self.get_by_label("Password").fill(password)
        self.get_by_role("button", name="Sign in").click()


class LoginPage(BasePage):
    """登录页面"""

    def __init__(self, page, base_url=""):
        super().__init__(page, url="/login", base_url=base_url)
        self.login_form = LoginForm(page)  # 组合组件

    def wait_for_page_load(self):
        self.page.get_by_test_id("login-form").wait_for()


# ========== 模板 3: App Actions ==========
# templates/project/app_actions.py

class MyAppActions(AppActions):
    """应用业务操作"""

    def login_as_admin(self):
        """管理员登录（常用操作）"""
        login_page = LoginPage(self.page, self.base_url)
        login_page.goto()
        login_page.login_form.fill_and_submit("admin", "admin123")

    def create_user(self, username: str, email: str):
        """创建用户（复杂业务流程）"""
        # 1. 导航到用户管理
        self.page.get_by_role("link", name="Users").click()
        # 2. 打开创建对话框
        self.page.get_by_role("button", name="Add User").click()
        # 3. 填写表单
        self.page.get_by_label("Username").fill(username)
        self.page.get_by_label("Email").fill(email)
        # 4. 提交
        self.page.get_by_role("button", name="Create").click()
        # 5. 等待成功消息
        self.page.get_by_text("User created successfully").wait_for()


# ========== 测试使用 ==========

@pytest.fixture
def app_actions(page, base_url):
    """App Actions fixture"""
    return MyAppActions(page, base_url)


def test_user_management(page, app_actions):
    """测试用户管理功能"""
    # ✅ 使用高级操作
    app_actions.login_as_admin()
    app_actions.create_user("john", "john@example.com")

    # ✅ 直接使用 Playwright API
    assert page.get_by_text("john").is_visible()
```

---

## 6. 最佳实践总结

### DO ✅

1. **使用 Test ID**：让前端添加 `data-testid`
2. **语义化定位优先**：`get_by_role`, `get_by_label`
3. **组件化**：封装可复用的 Component
4. **App Actions**：封装高级业务流程
5. **直接使用 Playwright API**：不过度封装
6. **测试可读性**：代码应该像文档一样易读

```python
# ✅ 好的测试
def test_user_can_update_profile(app_actions):
    app_actions.login_as_admin()

    page.get_by_test_id("user-menu").click()
    page.get_by_role("menuitem", name="Profile").click()
    page.get_by_label("Email").fill("new@example.com")
    page.get_by_role("button", name="Save").click()

    assert page.get_by_text("Profile updated").is_visible()
```

### DON'T ❌

1. **过度封装**：不要为每个元素创建方法
2. **脆弱定位**：避免依赖 CSS 类名、XPath
3. **不必要的等待**：Playwright 有 auto-waiting
4. **硬编码等待时间**：`sleep(3)` ❌

```python
# ❌ 不好的测试
def test_update_profile(login_page):
    login_page.click_username_field()  # ❌ 过度封装
    login_page.enter_username("admin")  # ❌ 过度封装
    login_page.click_password_field()
    login_page.enter_password("pass")
    login_page.click_submit_button()
    time.sleep(3)  # ❌ 硬编码等待
```

---

## 7. 实施建议

### 短期（v3.43.0）
- ✅ 新增 `BaseComponent` 类
- ✅ 新增 `AppActions` 类
- ✅ BasePage 暴露 Playwright 原生 API
- ✅ 提供两种模式的模板（传统 + 现代）
- ✅ 文档说明最佳实践

### 中期（v3.44.0）
- 📋 `@page_class` 装饰器（自动注册 fixture）
- 📋 `@component_class` 装饰器
- 📋 提供脚手架命令生成现代模式代码

### 长期
- 📋 与前端团队协作，推广 Test ID 规范
- 📋 提供 Test ID 生成工具/VSCode 插件
- 📋 示例项目展示最佳实践

---

## 8. 迁移路径

### 现有项目迁移

```python
# 阶段 1: 保持现有代码不变（兼容）
class LoginPage(BasePage):
    def login(self, username, password):
        self.fill("#username", username)  # 旧方式仍然工作
        self.fill("#password", password)
        self.click("button")

# 阶段 2: 逐步引入现代定位（渐进）
class LoginPage(BasePage):
    def login(self, username, password):
        self.page.get_by_label("Username").fill(username)  # ✅ 新方式
        self.page.get_by_label("Password").fill(password)
        self.page.get_by_role("button", name="Sign in").click()

# 阶段 3: 引入组件化（可选）
class LoginPage(BasePage):
    def __init__(self, page, base_url=""):
        super().__init__(page, url="/login", base_url=base_url)
        self.login_form = LoginForm(page)  # ✅ 组件化
```

---

## 总结

**核心原则**：
1. **Test ID 优先** - 稳定性
2. **组件化** - 复用性
3. **App Actions** - 业务抽象
4. **直接使用 Playwright API** - 简洁性
5. **可读性优先** - 可维护性

**我们框架的优势**：
- ✅ 保留 BasePage（向后兼容）
- ✅ 新增 BaseComponent（组件化）
- ✅ 新增 AppActions（业务抽象）
- ✅ 暴露 Playwright 原生 API（灵活性）
- ✅ 提供多种模式模板（适应不同场景）
