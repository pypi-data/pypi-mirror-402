# UI 失败诊断统一实现 - v3.46.3

## 实现总结

### 改进目标

将 UI 测试失败诊断功能从"测试项目手动实现"改为"框架统一实现"，实现零配置、开箱即用。

---

## 实现内容

### 1. 修改 `ui.py` - 简化 context fixture + 添加失败诊断 hook

**文件**: `src/df_test_framework/testing/fixtures/ui.py`

#### 变更 1: 简化 `context` fixture

**改进前**（职责混乱）:
```python
@pytest.fixture
def context(..., request):  # 需要 request 参数
    # 启动录屏
    ctx = browser.new_context(**context_options)
    yield ctx

    # ❌ 在 fixture 中判断失败
    if record_mode == "retain-on-failure":
        if not _test_failed(request):  # 判断失败
            _delete_video_file(video_path)
```

**改进后**（职责清晰）:
```python
@pytest.fixture
def context(...):  # 不需要 request
    # 只负责启动录屏
    ctx = browser.new_context(**context_options)
    yield ctx

    # ✅ 只关闭资源，不处理视频文件
    ctx.close()
```

#### 变更 2: 添加失败诊断 hook

```python
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """测试执行后的钩子 - 统一处理失败诊断

    功能:
    1. 失败自动截图（可配置）
    2. 视频文件处理（根据 record_video 模式）
    3. Allure 附件自动添加（可配置）
    4. 诊断信息输出
    """
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        if "page" in item.funcargs or "context" in item.funcargs:
            _handle_ui_test_result(item, report)
```

**核心逻辑**:
- 失败时：截图 + 保留视频 + Allure 附件
- 成功时：根据 `record_video` 模式决定是否删除视频

---

### 2. 扩展 `WebConfig` 配置

**文件**: `src/df_test_framework/infrastructure/config/schema.py`

```python
class WebConfig(BaseModel):
    # 现有配置
    record_video: bool | Literal["off", "on", "retain-on-failure", "on-first-retry"] = False
    video_dir: str = "reports/videos"

    # 新增配置（v3.46.3）⭐
    screenshot_on_failure: bool = Field(default=True, description="失败时自动截图")
    screenshot_dir: str = Field(default="reports/screenshots", description="截图保存目录")
    attach_to_allure: bool = Field(default=True, description="自动附加到 Allure 报告")
```

---

### 3. 注册 pytest11 Entry Points

**文件**: `pyproject.toml`

```toml
[project.entry-points.pytest11]
df_test_framework_ui = "df_test_framework.testing.fixtures.ui"  # v3.46.3: UI fixtures + 失败诊断 hooks
```

**效果**: pip install 后自动加载，无需手动声明 `pytest_plugins`

---

### 4. 更新脚手架模板

**文件**:
- `src/df_test_framework/cli/templates/project/ui_conftest.py`
- `src/df_test_framework/cli/templates/project/full_conftest.py`

**删除内容**:
- ❌ `pytest_plugins = ["df_test_framework.testing.fixtures.ui"]`（已通过 pytest11 自动加载）
- ❌ `@pytest.hookimpl def pytest_runtest_makereport(...)`（已在框架实现）

**新增说明**:
```python
# ============================================================
# v3.46.3: 失败诊断说明 ⭐
# ============================================================
# 框架已自动实现失败诊断功能，无需手动添加 pytest_runtest_makereport hook。
#
# 功能包括：
#   1. 失败时自动截图（可配置）
#   2. 视频文件处理（根据 record_video 模式）
#   3. Allure 附件自动添加（可配置）
#   4. 诊断信息输出
```

---

## 架构设计

### 职责分离

```
┌──────────────────────────────────────────────┐
│ fixtures/ui.py (统一实现)                     │
├──────────────────────────────────────────────┤
│ Fixtures (资源管理):                          │
│   - context: 启动录屏，不处理失败             │
│   - page: 提供页面实例                        │
│                                              │
│ Hooks (失败诊断):                             │
│   - pytest_runtest_makereport: 统一处理失败   │
│     ├─ 失败截图                              │
│     ├─ 视频处理                              │
│     └─ Allure 附件                           │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│ pytest11 自动加载                             │
│ pip install → 自动生效                        │
└──────────────────────────────────────────────┘
```

### 为什么统一在 ui.py？

参考框架现有模式：
- `fixtures/core.py`: fixtures + hooks（混合）✅
- `plugins/env_plugin.py`: hooks + fixtures（混合）✅

**结论**: 功能内聚性 > 严格分离

---

## 使用方式

### 新项目（v3.46.3+）

```bash
# 1. 生成项目
df-test init my-project --type ui

# 2. 配置（可选，使用默认值即可）
# config/base.yaml
web:
  screenshot_on_failure: true      # 默认 true
  screenshot_dir: reports/screenshots
  record_video: retain-on-failure  # 仅保留失败的视频
  attach_to_allure: true          # 默认 true

# 3. 运行测试（无需额外配置）
pytest tests/ -v -s
```

### 现有项目升级

```bash
# 1. 升级框架
pip install --upgrade df-test-framework>=3.47.0

# 2. 删除 conftest.py 中的手动 hook（可选）
# ❌ 删除以下代码（框架已接管）
# @pytest.hookimpl(tryfirst=True, hookwrapper=True)
# def pytest_runtest_makereport(item, call):
#     ...

# 3. 无需其他配置，自动生效！✅
pytest tests/ -v -s
```

---

## 配置选项

| 配置项 | 默认值 | 说明 |
|-------|--------|------|
| `screenshot_on_failure` | `true` | 失败时自动截图 |
| `screenshot_dir` | `reports/screenshots` | 截图保存目录 |
| `record_video` | `false` | 视频录制模式 |
| `video_dir` | `reports/videos` | 视频保存目录 |
| `attach_to_allure` | `true` | 自动附加到 Allure |

### 录制模式说明

| 模式 | 说明 | 磁盘占用 | 推荐场景 |
|-----|------|---------|---------|
| `off` | 不录制 | 无 | 快速测试 |
| `on` | 始终录制 | 高 | 调试阶段 |
| `retain-on-failure` ⭐ | 仅保留失败 | 低 | **生产环境推荐** |
| `on-first-retry` | 首次重试录制 | 中 | 结合 pytest-rerunfailures |

---

## 向后兼容性

### 兼容性保证

- ✅ pytest 允许多个同名 hook 共存（都会执行）
- ✅ 用户自定义 hook 优先级更高（tryfirst）
- ✅ 可通过配置禁用框架 hook（`screenshot_on_failure: false`）

### 升级路径

```python
# 现有项目的 conftest.py 中的 hook 可以保留，不冲突
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # 用户自定义逻辑
    ...

# 框架的 hook 也会执行，两者共存
```

---

## 优势总结

| 维度 | 改进前 | 改进后 |
|------|--------|--------|
| **用户体验** | 需手动添加 30+ 行代码 | 零配置，开箱即用 ✅ |
| **维护成本** | 每个项目维护 | 框架统一维护 ✅ |
| **一致性** | 实现可能不同 | 完全一致 ✅ |
| **职责清晰** | fixture 混入业务逻辑 | 职责分离 ✅ |
| **可测试性** | 分散难测 | 集中易测 ✅ |
| **学习成本** | 需理解 pytest hook | 无需理解内部 ✅ |

---

## 测试验证

### 验证步骤

1. **生成测试项目**:
   ```bash
   df-test init test-ui-project --type ui
   cd test-ui-project
   ```

2. **配置失败诊断**:
   ```yaml
   # config/base.yaml
   web:
     record_video: retain-on-failure
     screenshot_on_failure: true
   ```

3. **编写失败测试**:
   ```python
   def test_will_fail(page):
       page.goto("https://example.com")
       assert False, "故意失败"
   ```

4. **运行测试**:
   ```bash
   pytest tests/ -v -s
   ```

5. **验证输出**:
   ```
   📸 失败截图: reports/screenshots/test_will_fail_failure.png
   🎬 测试视频: reports/videos/test_will_fail.webm
   ```

---

## 文件清单

### 修改的文件

1. ✅ `src/df_test_framework/testing/fixtures/ui.py`
   - 简化 `context` fixture
   - 添加 `pytest_runtest_makereport` hook
   - 添加失败诊断辅助函数

2. ✅ `src/df_test_framework/infrastructure/config/schema.py`
   - 扩展 `WebConfig` 配置项

3. ✅ `pyproject.toml`
   - 注册 `df_test_framework_ui` 到 pytest11

4. ✅ `src/df_test_framework/cli/templates/project/ui_conftest.py`
   - 删除手动 hook
   - 添加使用说明

5. ✅ `src/df_test_framework/cli/templates/project/full_conftest.py`
   - 删除手动 hook
   - 添加使用说明

### 删除的代码

- ❌ `context` fixture 中的失败判断逻辑
- ❌ `_test_failed()` 辅助函数（移到 hook）
- ❌ `_is_first_retry()` 辅助函数（移到 hook）
- ❌ `_delete_video_file()` 辅助函数（移到 hook）
- ❌ 脚手架模板中的手动 hook

---

## 后续优化建议

1. **截图增强**: 支持全页截图、元素截图
2. **失败重现**: 保存 page context、cookies、localStorage
3. **诊断报告**: 生成结构化失败诊断 JSON
4. **智能分析**: 基于截图/视频自动分析失败原因

---

## 参考

- pytest hook 文档: https://docs.pytest.org/en/stable/reference/reference.html#hooks
- Playwright 截图文档: https://playwright.dev/python/docs/screenshots
- Allure 附件文档: https://allurereport.org/docs/pytest/#attachments
