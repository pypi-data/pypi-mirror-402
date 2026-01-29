# Allure 报告集成指南

> **最后更新**: 2026-01-17
> **适用版本**: v3.17.0+（Fixture 集成），v4.0.0+（推荐）

## 概述

DF Test Framework 提供了完整的 Allure 报告集成，通过 Pytest Fixture 自动记录测试执行过程中的所有操作。

### 核心特性

- **零配置**: 自动生效，无需手动启用
- **自动记录**: 自动记录 HTTP 请求、数据库查询、Redis 操作、UI 事件等
- **测试隔离**: 每个测试使用独立的 EventBus，不会互相干扰
- **事件驱动**: 基于 EventBus 实现，所有能力层统一集成
- **详细报告**: 包含请求/响应详情、SQL 语句、错误堆栈等

### 支持的操作类型

- ✅ HTTP 请求/响应（包括中间件执行）
- ✅ 数据库查询（SQL、耗时、行数）
- ✅ Redis 缓存操作
- ✅ 消息队列（发布/消费）
- ✅ 存储操作（本地文件、S3、OSS）
- ✅ 事务操作（commit/rollback）
- ✅ Web UI 事件（页面加载、网络请求、Console）
- ✅ 错误和异常

---

## 快速开始

### 1. 安装 Allure

```bash
# 安装 allure-pytest
pip install allure-pytest

# 安装 Allure 命令行工具（可选，用于查看报告）
# macOS
brew install allure

# Windows
scoop install allure

# Linux
# 下载并解压 https://github.com/allure-framework/allure2/releases
```

### 2. 运行测试并生成报告

```bash
# 运行测试，生成 Allure 结果
pytest --alluredir=./allure-results

# 查看报告（自动打开浏览器）
allure serve ./allure-results

# 或生成静态 HTML 报告
allure generate ./allure-results -o ./allure-report --clean
```

### 3. 自动记录示例

框架会自动记录所有操作，无需任何额外代码：

```python
def test_user_api(http_client):
    """测试用户 API - 自动记录到 Allure"""
    # HTTP 请求自动记录
    response = http_client.get("/users/1")
    assert response["id"] == 1

def test_database_query(database):
    """测试数据库查询 - 自动记录到 Allure"""
    # 数据库查询自动记录
    users = database.query_all("SELECT * FROM users")
    assert len(users) > 0

def test_ui_action(login_actions):
    """测试 UI 操作 - 自动记录到 Allure"""
    # UI 操作自动记录
    login_actions.login_as_admin()
    assert login_actions.page.get_by_text("欢迎").is_visible()
```

---

## 配置选项

### 启用/禁用 Allure 记录

通过环境变量或配置文件控制 Allure 记录：

```yaml
# config/default.yaml
observability:
  enabled: true              # 启用可观测性（默认）
  allure_recording: true     # 启用 Allure 记录（默认）
```

```bash
# 环境变量方式
export OBSERVABILITY__ALLURE_RECORDING=true   # 启用
export OBSERVABILITY__ALLURE_RECORDING=false  # 禁用

# 禁用所有可观测性（包括 Allure）
export OBSERVABILITY__ENABLED=false
```

### pytest 配置

```ini
# pytest.ini
[pytest]
# Allure 结果目录
addopts = --alluredir=./allure-results

# 清理旧结果
addopts = --alluredir=./allure-results --clean-alluredir
```

---

## 自动记录的详细信息

### HTTP 请求记录

每个 HTTP 请求会记录：

- **请求信息**: 方法、URL、Headers、Body
- **响应信息**: 状态码、Headers、Body
- **性能指标**: 请求耗时
- **中间件执行**: 中间件名称、执行顺序
- **错误信息**: 异常堆栈、错误消息

**Allure 报告中的展示**：
```
Step: GET /users/1
├── Request
│   ├── Method: GET
│   ├── URL: https://api.example.com/users/1
│   ├── Headers: {...}
│   └── Body: (empty)
├── Response
│   ├── Status: 200 OK
│   ├── Headers: {...}
│   └── Body: {"id": 1, "name": "张三"}
└── Duration: 0.123s
```

### 数据库查询记录

每个数据库查询会记录：

- **SQL 语句**: 完整的 SQL（包括参数）
- **执行时间**: 查询耗时
- **返回行数**: 查询结果行数
- **错误信息**: SQL 错误、异常堆栈

**Allure 报告中的展示**：
```
Step: Database Query
├── SQL: SELECT * FROM users WHERE id = ?
├── Parameters: [1]
├── Duration: 0.045s
├── Row Count: 1
└── Status: Success
```

### Redis 操作记录

每个 Redis 操作会记录：

- **操作类型**: GET、SET、HGET、LPUSH 等
- **键名**: Redis key
- **值**: 操作的值（可配置是否记录）
- **执行时间**: 操作耗时
- **错误信息**: Redis 错误

### UI 事件记录

Web UI 测试会记录：

- **页面加载**: URL、加载时间
- **网络请求**: 页面内的 AJAX 请求
- **Console 日志**: 浏览器控制台输出
- **错误信息**: JavaScript 错误
- **截图**: 失败时自动截图

---

## 自定义 Allure 标记

除了自动记录，你还可以使用 Allure 的装饰器和 API 来自定义报告内容。

### 测试元数据

```python
import allure

@allure.feature("用户管理")
@allure.story("用户登录")
@allure.severity(allure.severity_level.CRITICAL)
def test_user_login(http_client):
    """测试用户登录功能"""
    response = http_client.post("/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert response["success"] is True
```

### 测试步骤

```python
import allure

def test_order_flow(http_client):
    """测试订单流程"""
    with allure.step("创建订单"):
        order = http_client.post("/orders", json={"product_id": 1})
        order_id = order["id"]

    with allure.step("支付订单"):
        payment = http_client.post(f"/orders/{order_id}/pay")
        assert payment["status"] == "paid"

    with allure.step("确认订单"):
        confirmation = http_client.get(f"/orders/{order_id}")
        assert confirmation["status"] == "confirmed"
```

### 附加信息

```python
import allure

def test_api_response(http_client):
    """测试 API 响应"""
    response = http_client.get("/users/1")

    # 附加 JSON 数据
    allure.attach(
        json.dumps(response, indent=2),
        name="API Response",
        attachment_type=allure.attachment_type.JSON
    )

    # 附加文本
    allure.attach(
        "测试环境: dev",
        name="Environment",
        attachment_type=allure.attachment_type.TEXT
    )
```

### 动态标题和描述

```python
import allure

@allure.title("测试用户 {user_id} 的信息")
def test_user_info(http_client, user_id):
    """动态标题示例"""
    response = http_client.get(f"/users/{user_id}")
    assert response["id"] == user_id

@allure.description("""
这是一个详细的测试描述。
可以使用多行文本。
支持 Markdown 格式。
""")
def test_with_description(http_client):
    """带描述的测试"""
    pass
```

---

## 最佳实践

### 1. 合理使用自动记录

框架已自动记录所有操作，无需手动添加 Allure 步骤：

```python
# ✅ 推荐：依赖自动记录
def test_user_api(http_client):
    """HTTP 请求自动记录到 Allure"""
    response = http_client.get("/users/1")
    assert response["id"] == 1

# ❌ 不推荐：重复记录
def test_user_api_redundant(http_client):
    with allure.step("GET /users/1"):  # 多余，框架已自动记录
        response = http_client.get("/users/1")
    assert response["id"] == 1
```

### 2. 使用 Allure 标记组织测试

```python
# ✅ 推荐：使用 feature 和 story 组织测试
@allure.feature("用户管理")
@allure.story("用户注册")
def test_user_registration(http_client):
    pass

@allure.feature("用户管理")
@allure.story("用户登录")
def test_user_login(http_client):
    pass

@allure.feature("订单管理")
@allure.story("创建订单")
def test_create_order(http_client):
    pass
```

### 3. 设置测试优先级

```python
import allure

@allure.severity(allure.severity_level.BLOCKER)
def test_critical_payment(http_client):
    """关键支付功能"""
    pass

@allure.severity(allure.severity_level.CRITICAL)
def test_user_login(http_client):
    """用户登录"""
    pass

@allure.severity(allure.severity_level.NORMAL)
def test_user_profile(http_client):
    """用户资料"""
    pass

@allure.severity(allure.severity_level.MINOR)
def test_ui_style(login_actions):
    """UI 样式检查"""
    pass
```

### 4. 添加测试链接

```python
@allure.link("https://jira.example.com/PROJ-123", name="JIRA Issue")
@allure.issue("PROJ-123", "Bug: 登录失败")
@allure.testcase("TC-001", "测试用例: 用户登录")
def test_login_bug_fix(http_client):
    """修复登录 Bug 的测试"""
    pass
```

### 5. 环境信息配置

在项目根目录创建 `allure-results/environment.properties`：

```properties
# environment.properties
Environment=dev
Base.URL=https://api-dev.example.com
Browser=Chrome 120
Python.Version=3.12
Framework.Version=4.0.0
```

或使用代码动态设置：

```python
# conftest.py
import allure
import pytest

@pytest.fixture(scope="session", autouse=True)
def set_allure_environment(runtime):
    """设置 Allure 环境信息"""
    allure.environment(
        Environment=runtime.settings.env,
        Base_URL=runtime.settings.http.base_url,
        Framework_Version="4.0.0"
    )
```

---

## 从旧版 AllurePlugin 迁移

> **重要**: AllurePlugin（插件方式）已在 v3.18.0 标记为废弃，将在 v4.0.0 移除。请迁移到 Fixture 集成方式。

### 迁移步骤

#### 1. 移除旧的插件注册代码

```python
# ❌ 旧方式（v3.18.0 之前）
from df_test_framework import Bootstrap
from df_test_framework.plugins.builtin.reporting import AllurePlugin

app = Bootstrap().with_plugin(AllurePlugin()).build()  # 移除这行
```

#### 2. 无需任何替代代码

Fixture 集成方式是自动生效的，无需手动注册：

```python
# ✅ 新方式（v3.17.0+）
from df_test_framework import Bootstrap

app = Bootstrap().build()  # 就这样，Allure 自动集成
```

#### 3. 配置方式保持不变

配置文件中的 Allure 相关配置保持不变：

```yaml
# config/default.yaml
observability:
  enabled: true
  allure_recording: true  # 控制 Allure 记录
```

### 功能对比

| 功能 | 旧版 AllurePlugin | 新版 Fixture 集成 |
|------|------------------|------------------|
| 自动记录 HTTP | ✅ | ✅ |
| 自动记录数据库 | ✅ | ✅ |
| 自动记录 Redis | ✅ | ✅ |
| 自动记录 UI | ✅ | ✅ |
| 测试隔离 | ❌ 共享 EventBus | ✅ 独立 EventBus |
| 配置方式 | 插件注册 | 自动生效 |
| 性能 | 较低 | 更高 |

### 迁移优势

1. **零配置**: 无需手动注册插件，自动生效
2. **测试隔离**: 每个测试使用独立的 EventBus，避免干扰
3. **更好的性能**: 优化的事件订阅机制
4. **更简洁的代码**: 减少样板代码

---

## 注意事项

### 1. Allure 命令行工具

框架只负责生成 Allure 结果，查看报告需要安装 Allure 命令行工具：

```bash
# macOS
brew install allure

# Windows
scoop install allure

# Linux
# 下载并解压 https://github.com/allure-framework/allure2/releases
```

### 2. 结果目录清理

建议定期清理 `allure-results` 目录：

```bash
# 清理旧结果
pytest --alluredir=./allure-results --clean-alluredir
```

### 3. CI/CD 集成

在 CI/CD 中生成报告：

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: pytest --alluredir=./allure-results

- name: Generate Allure report
  run: allure generate ./allure-results -o ./allure-report --clean

- name: Upload report
  uses: actions/upload-artifact@v3
  with:
    name: allure-report
    path: ./allure-report
```

### 4. 性能影响

Allure 记录有轻微性能开销，如需禁用：

```bash
# 环境变量方式
export OBSERVABILITY__ALLURE_RECORDING=false

# 或在配置文件中
observability:
  allure_recording: false
```

---

## 相关文档

- [Fixtures 使用指南](fixtures_guide.md) - pytest fixtures 详细说明
- [HTTP 客户端指南](http_client_guide.md) - HTTP 请求自动记录
- [数据库使用指南](database_guide.md) - 数据库查询自动记录
- [Redis 使用指南](redis_guide.md) - Redis 操作自动记录
- [Web UI 测试指南](web-ui-testing.md) - UI 事件自动记录
- [Bootstrap 引导系统指南](bootstrap_guide.md) - 框架初始化
- [监控插件指南](monitoring_plugin.md) - 性能监控插件

---

**完成时间**: 2026-01-17
