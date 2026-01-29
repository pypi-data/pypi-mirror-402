# 常见问题 FAQ

> **更新日期**: 2026-01-19
> **框架版本**: v4.0.0

本文档收集了使用 DF Test Framework 过程中的常见问题和解决方案。

---

## 📋 目录

- [安装和环境问题](#安装和环境问题)
- [配置问题](#配置问题)
- [HTTP 客户端问题](#http-客户端问题)
- [数据库问题](#数据库问题)
- [UI 测试问题](#ui-测试问题)
- [调试和排错](#调试和排错)
- [性能优化](#性能优化)
- [版本升级](#版本升级)

---

## 🔧 安装和环境问题

### Q1: 如何安装框架？

**A**: 推荐使用 `uv` 安装：

```bash
# 基础安装
uv add df-test-framework

# 安装可选依赖
uv add "df-test-framework[ui]"            # UI 测试
uv add "df-test-framework[observability]" # 可观测性
uv add "df-test-framework[all]"           # 所有功能
```

如果使用 `pip`：
```bash
pip install df-test-framework
```

**参考文档**: [README.md - 安装](../README.md#安装)

---

### Q2: 安装后提示 `ModuleNotFoundError: No module named 'df_test_framework'`

**A**: 可能的原因和解决方案：

1. **虚拟环境未激活**
   ```bash
   # 检查当前 Python 环境
   which python

   # 激活虚拟环境
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```

2. **安装到了错误的 Python 环境**
   ```bash
   # 使用 uv 确保安装到正确环境
   uv sync

   # 或使用 python -m pip
   python -m pip install df-test-framework
   ```

3. **IDE 使用了错误的 Python 解释器**
   - VSCode: 按 `Ctrl+Shift+P`，选择 "Python: Select Interpreter"
   - PyCharm: Settings → Project → Python Interpreter

---

### Q3: 安装 UI 测试依赖后，Playwright 提示浏览器未安装

**A**: 需要手动安装 Playwright 浏览器：

```bash
# 安装所有浏览器
playwright install

# 只安装 Chromium
playwright install chromium

# 安装浏览器依赖（Linux）
playwright install-deps
```

**参考文档**: [Web UI 测试指南](guides/web-ui-testing.md)

---

### Q4: Windows 上安装 Kafka 客户端失败

**A**: Kafka 客户端 `confluent-kafka` 需要 C 扩展编译。解决方案：

1. **使用预编译的 wheel**（推荐）
   ```bash
   # confluent-kafka 2.12.0+ 提供 Windows wheel
   uv add "df-test-framework[kafka]"
   ```

2. **如果仍然失败，跳过 Kafka 依赖**
   ```bash
   # 只安装核心功能
   uv add df-test-framework

   # 使用其他消息队列（RabbitMQ 不需要编译）
   uv add "df-test-framework[rabbitmq]"
   ```

---

### Q5: Python 版本要求是什么？

**A**: 框架要求 **Python 3.12+**。

检查 Python 版本：
```bash
python --version
```

如果版本过低，请升级 Python：
- 官方下载: https://www.python.org/downloads/
- 使用 pyenv: `pyenv install 3.12`

---

## ⚙️ 配置问题

### Q6: 如何配置 API 基础 URL？

**A**: 有三种方式配置：

1. **YAML 配置文件**（推荐）
   ```yaml
   # config/base.yaml
   http:
     base_url: "https://api.example.com"
     timeout: 30
   ```

   ```yaml
   # config/environments/staging.yaml
   http:
     base_url: "https://staging-api.example.com"
   ```

2. **环境变量**
   ```bash
   export HTTP__BASE_URL="https://api.example.com"
   ```

3. **代码中配置**
   ```python
   from df_test_framework.infrastructure.config import get_settings

   # 加载配置
   settings = get_settings(env="staging")
   base_url = settings.http.base_url
   ```

**参考文档**: [配置指南](guides/config_guide.md)

---

### Q7: 配置文件放在哪里？

**A**: 框架使用 YAML 分层配置系统（v3.35.0+）：

**标准目录结构**：
```
my-project/
├── config/
│   ├── base.yaml              # 基础配置（所有环境共享）
│   ├── environments/
│   │   ├── local.yaml         # 本地开发环境
│   │   ├── dev.yaml           # 开发环境
│   │   ├── test.yaml          # 测试环境
│   │   ├── staging.yaml       # 预发布环境
│   │   └── prod.yaml          # 生产环境
│   └── secrets/               # 敏感配置（已 .gitignore）
│       └── .env.local         # 本地敏感配置
└── tests/
```

**配置优先级**（从高到低）：
1. 环境变量（最高优先级）
2. `config/secrets/.env.local`
3. `config/environments/{env}.yaml`
4. `config/base.yaml`
5. `.env` + `.env.{env}`（回退模式）

**初始化配置目录**：
```bash
df-test env init  # 自动创建标准目录结构
```

**切换环境**：
```bash
pytest tests/ --env=staging  # 使用 staging 环境
pytest tests/ --env=prod     # 使用 prod 环境
```

---

### Q8: 如何配置数据库连接？

**A**: 使用 YAML 配置或环境变量：

**YAML 配置**（推荐）：
```yaml
# config/base.yaml
db:
  host: "localhost"
  port: 3306
  database: "test_db"
  username: "root"
  charset: "utf8mb4"
  pool_size: 5
  pool_max_overflow: 10
```

```yaml
# config/environments/staging.yaml
db:
  host: "staging-db.example.com"
  database: "staging_db"
  username: "staging_user"
```

**环境变量**：
```bash
export DB__HOST="localhost"
export DB__PORT="3306"
export DB__USERNAME="root"
export DB__PASSWORD="password"
export DB__DATABASE="test_db"
```

**敏感信息**（密码）：
```bash
# config/secrets/.env.local
DB_PASSWORD=your_secret_password
```

**参考文档**: [数据库指南](guides/database_guide.md) | [配置指南](guides/config_guide.md)

---

## 🌐 HTTP 客户端问题

### Q9: 如何发送带认证的 HTTP 请求？

**A**: 框架提供多种认证方式：

1. **Bearer Token**
   ```python
   http_client.get("/api/users", token="your-token")
   ```

2. **自定义 Header**
   ```python
   http_client.get("/api/users", headers={"Authorization": "Bearer token"})
   ```

3. **全局配置**
   ```python
   # 在 settings 中配置
   class MySettings(FrameworkSettings):
       http_auth_token: str = Field(default="your-token")
   ```

**参考文档**: [HTTP 客户端指南](guides/http_client_guide.md)

---

### Q10: 如何跳过某个请求的认证？

**A**: 使用 `skip_auth=True` 参数：

```python
# 跳过认证
response = http_client.get("/public/api", skip_auth=True)
```

这在测试公开 API 或登录接口时很有用。

---

### Q11: HTTP 请求超时如何配置？

**A**: 有三种方式：

1. **请求级别**（优先级最高）
   ```python
   http_client.get("/api/users", timeout=30)
   ```

2. **客户端级别**
   ```python
   http_client = HttpClient(base_url="...", timeout=30)
   ```

3. **全局配置**
   ```yaml
   # config/settings.yaml
   http:
     timeout: 30
   ```

**参考文档**: [HTTP 客户端指南](guides/http_client_guide.md)

---

## 🗄️ 数据库问题

### Q12: 如何在测试中使用数据库事务回滚？

**A**: 使用 `db_transaction` fixture（自动回滚）：

```python
def test_create_user(database, db_transaction):
    """测试结束后自动回滚"""
    user_id = database.execute(
        "INSERT INTO users (name) VALUES (:name)",
        {"name": "test"}
    )
    assert user_id > 0
    # 测试结束后自动回滚，数据不会保留
```

**禁用自动回滚**（保留测试数据）：
```bash
pytest --keep-test-data
```

**参考文档**: [数据库指南](guides/database_guide.md)

---

### Q13: 数据库连接池满了怎么办？

**A**: 调整连接池配置：

```yaml
# config/settings.yaml
database:
  pool_size: 20          # 增加连接池大小（默认 10）
  max_overflow: 10       # 增加溢出连接数（默认 5）
  pool_timeout: 30       # 连接超时时间
```

**检查连接泄漏**：
```python
# 确保使用 with 语句或手动关闭连接
with database.get_connection() as conn:
    # 使用连接
    pass
# 连接自动归还到池中
```

---

### Q14: 如何使用异步数据库客户端？

**A**: v4.0.0 新增异步数据库支持：

```python
import pytest
from df_test_framework import AsyncDatabase

@pytest.mark.asyncio
async def test_async_query(async_database: AsyncDatabase):
    """异步数据库查询"""
    result = await async_database.execute(
        "SELECT * FROM users WHERE id = :id",
        {"id": 1}
    )
    assert result is not None
```

**性能提升**：异步数据库操作比同步快 **2-5 倍**。

**参考文档**: [数据库指南](guides/database_guide.md)

---

## 🖥️ UI 测试问题

### Q15: Playwright 测试失败，提示 "Browser not found"

**A**: 需要安装 Playwright 浏览器：

```bash
playwright install chromium
```

**参考**: [Q3: Playwright 浏览器安装](#q3-安装-ui-测试依赖后playwright-提示浏览器未安装)

---

### Q16: UI 测试如何使用无头模式？

**A**: 配置 `headless` 参数：

```yaml
# config/settings.yaml
web:
  headless: true  # 无头模式（默认）
```

**临时使用有头模式**（调试时）：
```bash
export WEB_HEADLESS=false
pytest tests/test_ui.py
```

**参考文档**: [Web UI 测试指南](guides/web-ui-testing.md)

---

### Q17: 如何使用异步 UI 测试？

**A**: v4.0.0 新增异步 UI 支持：

```python
import pytest
from df_test_framework import AsyncAppActions

@pytest.mark.asyncio
async def test_async_ui(async_app_actions: AsyncAppActions):
    """异步 UI 测试"""
    await async_app_actions.navigate("https://example.com")
    await async_app_actions.click("button#submit")

    # 性能提升 2-3 倍
```

**参考文档**: [Web UI 测试指南](guides/web-ui-testing.md)

---

## 🐛 调试和排错

### Q18: 如何启用调试模式？

**A**: 有三种方式启用调试：

1. **测试级别**（使用 `@pytest.mark.debug`）
   ```python
   @pytest.mark.debug
   def test_something():
       # 自动启用控制台调试输出
       pass
   ```

2. **使用 `console_debugger` fixture**
   ```python
   def test_something(console_debugger):
       # 启用控制台调试
       pass
   ```

3. **全局启用**
   ```bash
   export DEBUG=true
   pytest tests/
   ```

**参考文档**: [调试指南](user-guide/debugging.md)

---

### Q19: 如何查看 HTTP 请求/响应详情？

**A**: v3.28.0+ 推荐使用统一调试系统：

**方式1：使用 `@pytest.mark.debug` marker**（推荐）
```python
import pytest

@pytest.mark.debug
def test_api(http_client):
    """自动打印 HTTP 请求/响应详情"""
    response = http_client.get("/api/users")
    # 终端显示彩色请求/响应详情（需要 pytest -v -s）
```

**方式2：使用 `debug_mode` fixture**
```python
def test_api(http_client, debug_mode):
    """启用调试模式"""
    response = http_client.get("/api/users")
```

**方式3：使用环境变量**（全局启用）
```bash
export OBSERVABILITY__DEBUG_OUTPUT=true
pytest tests/ -v -s
```

**参考文档**: [调试指南](user-guide/debugging.md)

---

### Q20: 测试失败时如何保留测试数据？

**A**: 使用 `--keep-test-data` 选项：

```bash
# 保留所有测试数据
pytest --keep-test-data

# 只保留失败测试的数据
pytest --keep-test-data-on-failure
```

**或使用 `@pytest.mark.keep_data`**：
```python
@pytest.mark.keep_data
def test_something(database):
    # 此测试的数据不会被清理
    pass
```

---

### Q21: 如何查看 Allure 报告？

**A**: 生成并查看 Allure 报告：

```bash
# 1. 运行测试并生成 Allure 数据
pytest --alluredir=allure-results

# 2. 生成并打开报告
allure serve allure-results
```

**参考文档**: [Allure 插件指南](guides/allure_plugin.md)

---

## ⚡ 性能优化

### Q22: 如何提升 HTTP 请求性能？

**A**: v4.0.0 引入异步 HTTP 客户端，性能提升 **10-30 倍**：

**同步模式**（传统）：
```python
# 100 个请求需要 20 秒
for i in range(100):
    response = http_client.get(f"/users/{i}")
```

**异步模式**（推荐）：
```python
import asyncio
from df_test_framework import AsyncHttpClient

async def test_concurrent():
    async with AsyncHttpClient("https://api.example.com") as client:
        # 100 个请求仅需 0.5 秒！
        tasks = [client.get(f"/users/{i}") for i in range(100)]
        responses = await asyncio.gather(*tasks)
```

**性能对比**：
- 同步模式：20 秒（串行执行）
- 异步模式：0.5 秒（并发执行）
- **性能提升：40 倍**

**参考文档**: [HTTP 客户端指南](guides/http_client_guide.md)

---

### Q23: 如何提升数据库查询性能？

**A**: 使用异步数据库客户端：

```python
import pytest
from df_test_framework import AsyncDatabase

@pytest.mark.asyncio
async def test_batch_query(async_database: AsyncDatabase):
    """批量查询（异步）"""
    # 并发执行 10 个查询
    tasks = [
        async_database.execute(f"SELECT * FROM users WHERE id = {i}")
        for i in range(1, 11)
    ]
    results = await asyncio.gather(*tasks)

    # 性能提升 2-5 倍
```

**其他优化建议**：
1. **使用连接池**
   ```yaml
   database:
     pool_size: 20
     max_overflow: 10
   ```

2. **批量操作**
   ```python
   # ❌ 避免：循环插入
   for user in users:
       database.execute("INSERT INTO users ...", user)

   # ✅ 推荐：批量插入
   database.execute_many("INSERT INTO users ...", users)
   ```

3. **使用索引**
   ```sql
   CREATE INDEX idx_user_email ON users(email);
   ```

**参考文档**: [数据库指南](guides/database_guide.md)

---

### Q24: 如何提升 UI 测试性能？

**A**: 使用异步 UI 测试：

```python
import pytest
from df_test_framework import AsyncAppActions

@pytest.mark.asyncio
async def test_async_ui(async_app_actions: AsyncAppActions):
    """异步 UI 测试"""
    await async_app_actions.navigate("https://example.com")
    await async_app_actions.click("button#submit")

    # 性能提升 2-3 倍
```

**其他优化建议**：
1. **使用无头模式**
   ```yaml
   web:
     headless: true  # 无头模式更快
   ```

2. **禁用不必要的功能**
   ```yaml
   web:
     disable_images: true   # 禁用图片加载
     disable_css: true      # 禁用 CSS
   ```

3. **并行执行测试**
   ```bash
   pytest -n 4  # 4 个进程并行
   ```

**参考文档**: [Web UI 测试指南](guides/web-ui-testing.md)

---

## 🔄 版本升级

### Q25: 如何从 v3.x 升级到 v4.0.0？

**A**: v4.0.0 完全向后兼容，升级非常简单：

**步骤1：升级框架**
```bash
uv add df-test-framework@latest
```

**步骤2：验证现有测试**
```bash
pytest -v
```

**步骤3：逐步迁移到异步 API（可选）**
```python
# 旧代码（v3.x）- 仍然可用
def test_api(http_client):
    response = http_client.get("/users/1")
    assert response.status_code == 200

# 新代码（v4.0.0）- 性能更好
@pytest.mark.asyncio
async def test_api_async(async_http_client):
    response = await async_http_client.get("/users/1")
    assert response.status_code == 200
```

**重要提示**：
- ✅ 所有 v3.x 代码无需修改即可运行
- ✅ 可以逐步迁移到异步 API
- ✅ 同步和异步 API 可以混用

**参考文档**: [v4.0.0 迁移指南](migration/v3-to-v4.md)

---

### Q26: 升级后遇到 `ImportError` 怎么办？

**A**: 检查可选依赖是否安装：

```bash
# 检查当前安装的依赖
uv pip list | grep df-test-framework

# 重新安装可选依赖
uv add "df-test-framework[ui,observability,storage]"
```

**常见问题**：
1. **Playwright 相关错误**
   ```bash
   uv add "df-test-framework[ui]"
   playwright install chromium
   ```

2. **OpenTelemetry 相关错误**
   ```bash
   uv add "df-test-framework[observability]"
   ```

3. **存储客户端相关错误**
   ```bash
   uv add "df-test-framework[storage]"
   ```

---

### Q27: 如何查看版本更新内容？

**A**: 框架提供多种方式查看更新内容：

1. **查看 CHANGELOG**
   ```bash
   # 查看最新更新
   cat CHANGELOG.md | head -n 50
   ```

2. **查看详细发布说明**
   - 访问 `docs/releases/` 目录
   - 每个版本都有详细的发布说明文档

3. **查看迁移指南**
   - 访问 `docs/migration/` 目录
   - 包含版本间的迁移步骤和注意事项

**在线资源**：
- GitHub Releases: https://github.com/yourorg/test-framework/releases
- 文档网站: https://github.com/yourorg/test-framework/tree/master/docs

---

### Q28: 升级后测试失败怎么办？

**A**: 按以下步骤排查：

**步骤1：检查版本兼容性**
```bash
# 查看当前版本
python -c "import df_test_framework; print(df_test_framework.__version__)"

# 查看 Python 版本（需要 3.12+）
python --version
```

**步骤2：清理缓存**
```bash
# 清理 pytest 缓存
rm -rf .pytest_cache

# 清理 Python 缓存
find . -type d -name "__pycache__" -exec rm -rf {} +
```

**步骤3：重新安装依赖**
```bash
# 使用 uv 重新同步
uv sync --all-extras

# 或使用 pip 重新安装
pip uninstall df-test-framework -y
pip install df-test-framework[all]
```

**步骤4：查看迁移指南**
- 访问 `docs/migration/` 目录
- 查看对应版本的迁移指南

**步骤5：寻求帮助**
- 在 GitHub Issues 中搜索类似问题
- 创建新 Issue 并提供详细信息

---

## 📚 更多资源

### 官方文档

- **快速开始**: [user-guide/QUICK_START.md](user-guide/QUICK_START.md)
- **用户手册**: [user-guide/USER_MANUAL.md](user-guide/USER_MANUAL.md)
- **API 参考**: [api-reference/](api-reference/)
- **使用指南**: [guides/](guides/)
- **架构设计**: [architecture/](architecture/)

### 社区支持

- **GitHub Issues**: https://github.com/yourorg/test-framework/issues
- **GitHub Discussions**: https://github.com/yourorg/test-framework/discussions
- **贡献指南**: [CONTRIBUTING.md](../CONTRIBUTING.md)

### 示例项目

- **示例代码**: [examples/](../examples/)
- **脚手架模板**: 使用 `df-test init` 生成

---

**最后更新**: 2026-01-19

如果您有其他问题,欢迎在 [GitHub Issues](https://github.com/yourorg/test-framework/issues) 中提问。

