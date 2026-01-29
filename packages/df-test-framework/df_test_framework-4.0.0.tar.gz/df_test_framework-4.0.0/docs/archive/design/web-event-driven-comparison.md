# Web UI 测试事件驱动方案对比

> **版本**: v3.44.0 设计对比
> **日期**: 2026-01-08
> **目标**: 找到最佳的Web事件发布架构
> **实现说明**: 最终落地版本使用 BrowserManager + page fixture 自动注册监听器并发布 `WebBrowserEvent`（page.load/network.* 等）+ `UIErrorEvent`，不再包装 Page API；下文涉及的 `UINavigation*` 等事件示例为早期方案，可作为扩展参考。

---

## 问题分析

### HTTP vs Web 的本质差异

| 维度 | HTTP | Web |
|------|------|-----|
| **API特点** | 统一入口（request方法） | 分散API（100+ 方法） |
| **拦截点** | 请求/响应边界明确 | 无统一边界 |
| **中间件可行性** | ✅ 可行（洋葱模型） | ❌ 不可行（无统一入口） |
| **原生事件支持** | ❌ 无 | ✅ 有（request/response/console等） |

**核心问题**：
1. ❌ Wrapper模式需要包装100+ API，维护成本高
2. ❌ Playwright API变动需要同步修改
3. ❌ 与HTTP的Middleware模式不一致

---

## 方案对比

### ❌ 方案1：InstrumentedPage 包装器（已否决）

```python
class InstrumentedPage:
    def goto(self, url, **kwargs):
        # 发布事件
        self._page.goto(url, **kwargs)

    def get_by_label(self, text, **kwargs):
        locator = self._page.get_by_label(text, **kwargs)
        return InstrumentedLocator(locator, ...)

    def get_by_role(self, role, **kwargs):
        locator = self._page.get_by_role(role, **kwargs)
        return InstrumentedLocator(locator, ...)

    # ... 需要包装100+ API
    def __getattr__(self, name):
        return getattr(self._page, name)
```

**问题**：
- ❌ 需要包装大量API
- ❌ Playwright更新需要同步
- ❌ 架构与HTTP不一致（Wrapper vs Middleware）
- ❌ 维护成本高

---

### ✅ 方案2：BrowserManager事件监听器 + Playwright原生事件（推荐）

**核心思想**：利用Playwright自带的事件系统，不包装API

```python
class BrowserManager:
    """浏览器管理器 - 自动注册事件监听器

    v3.44.0: 新增事件驱动架构
    - 利用Playwright原生事件（page.on()）
    - 不包装Page API，维护成本为零
    - 与HTTP的Middleware理念一致（统一拦截点）
    """

    def __init__(self, config=None, runtime=None):
        self.runtime = runtime
        self.event_bus = runtime.event_bus if runtime else None
        # ... 原有代码

    def start(self):
        """启动浏览器 - 自动注册事件监听器"""
        # 原有代码：创建 browser/context/page
        self._browser = launcher.launch(...)
        self._context = self._browser.new_context(...)
        self._page = self._context.new_page()

        # ✅ 新增：自动注册事件监听器（用户无感知）
        if self.event_bus:
            self._setup_event_listeners(self._page)

        return self._browser, self._context, self._page

    def _setup_event_listeners(self, page):
        """设置Playwright原生事件监听器

        利用Playwright自带的事件系统：
        - page.on("load") - 页面加载完成
        - page.on("request") - 网络请求
        - page.on("response") - 网络响应
        - page.on("console") - Console输出
        - page.on("dialog") - 弹窗
        - page.on("pageerror") - 页面错误

        这些事件会自动触发，无需包装API ✅
        """
        # 1. 页面导航事件
        page.on("load", lambda: self._on_page_load(page))
        page.on("domcontentloaded", lambda: self._on_dom_content_loaded(page))

        # 2. 网络事件（与HTTP的request/response对应）
        page.on("request", self._on_request)
        page.on("response", self._on_response)
        page.on("requestfailed", self._on_request_failed)

        # 3. Console事件
        page.on("console", self._on_console)

        # 4. Dialog事件
        page.on("dialog", self._on_dialog)

        # 5. 错误事件
        page.on("pageerror", self._on_page_error)
        page.on("crash", self._on_crash)

    # ========== 事件处理器 ==========

    def _on_page_load(self, page):
        """页面加载完成"""
        if not self.event_bus:
            return

        from df_test_framework.core.events import UINavigationEndEvent

        event = UINavigationEndEvent.create(
            page_name="Page",
            url=page.url,
            title=page.title(),
            duration=0,  # TODO: 计算导航耗时
        )
        self.event_bus.publish_sync(event)

    def _on_request(self, request):
        """网络请求开始"""
        if not self.event_bus:
            return

        # 可以发布自定义事件或复用HTTP事件
        from df_test_framework.core.events import Event

        event = Event(
            event_type="web.request.start",
            data={
                "method": request.method,
                "url": request.url,
                "headers": dict(request.headers),
            }
        )
        self.event_bus.publish_sync(event)

    def _on_response(self, response):
        """网络响应返回"""
        if not self.event_bus:
            return

        event = Event(
            event_type="web.response.end",
            data={
                "status": response.status,
                "url": response.url,
                "headers": dict(response.headers),
            }
        )
        self.event_bus.publish_sync(event)

    def _on_console(self, msg):
        """Console输出"""
        if not self.event_bus:
            return

        event = Event(
            event_type="web.console",
            data={
                "type": msg.type,
                "text": msg.text,
                "location": msg.location,
            }
        )
        self.event_bus.publish_sync(event)

    def _on_page_error(self, error):
        """页面错误"""
        if not self.event_bus:
            return

        from df_test_framework.core.events import UIErrorEvent

        event = UIErrorEvent.create(
            page_name="Page",
            operation="page_error",
            selector="",
            error_type=type(error).__name__,
            error_message=str(error),
        )
        self.event_bus.publish_sync(event)
```

**优点**：
- ✅ 不需要包装Playwright API（维护成本为零）
- ✅ 利用Playwright原生事件系统
- ✅ Playwright更新不影响我们的代码
- ✅ 与HTTP的Middleware理念一致（统一拦截点在BrowserManager）
- ✅ 自动发布事件（用户无感知）

**局限**：
- ⚠️ Playwright没有提供click/fill等细粒度事件
- ⚠️ 细粒度操作需要在BasePage/AppActions显式发布

---

### ✅ 方案3：混合架构（最佳平衡）

**粗粒度事件** → Playwright原生事件 + BrowserManager监听
**细粒度事件** → BasePage/AppActions显式发布（可选）

```python
# ========== 粗粒度事件（自动）==========
# 由BrowserManager自动监听Playwright原生事件

class BrowserManager:
    def _setup_event_listeners(self, page):
        """自动监听粗粒度事件"""
        page.on("load", self._on_page_load)         # ✅ 页面加载
        page.on("request", self._on_request)        # ✅ 网络请求
        page.on("response", self._on_response)      # ✅ 网络响应
        page.on("console", self._on_console)        # ✅ Console输出
        page.on("dialog", self._on_dialog)          # ✅ 弹窗
        page.on("pageerror", self._on_page_error)   # ✅ 页面错误


# ========== 细粒度事件（可选）==========
# 由BasePage/AppActions显式发布（用户可控）

class BasePage:
    def goto(self):
        """导航到页面（可选发布事件）"""
        url = urljoin(self.base_url, self.url)

        # ✅ 可选：发布导航开始事件
        if self.runtime and self.runtime.event_bus:
            start_event = UINavigationStartEvent.create(
                page_name=self.__class__.__name__,
                url=url,
                base_url=self.base_url,
            )
            self.runtime.event_bus.publish_sync(start_event)

        # 执行导航（Playwright原生API）
        self.page.goto(url)

        # 注意：页面加载完成事件由BrowserManager的page.on("load")自动发布


class AppActions:
    def login(self, username, password):
        """登录操作（细粒度事件）"""
        # ✅ 可选：发布业务事件
        if self.runtime and self.runtime.event_bus:
            event = Event(
                event_type="app.login.start",
                data={"username": username}
            )
            self.runtime.event_bus.publish_sync(event)

        # 执行操作（使用Playwright原生API）
        self.page.get_by_label("Username").fill(username)
        self.page.get_by_label("Password").fill(password)
        self.page.get_by_role("button", name="Sign in").click()

        # ✅ 可选：发布成功事件
        if self.runtime and self.runtime.event_bus:
            event = Event(
                event_type="app.login.success",
                data={"username": username}
            )
            self.runtime.event_bus.publish_sync(event)
```

**优点**：
- ✅ 粗粒度事件（导航、网络、Console）自动发布
- ✅ 细粒度事件（click、fill）可选发布（用户控制）
- ✅ 不包装Playwright API（维护成本低）
- ✅ 灵活性高（用户可选择发布哪些事件）

---

## 架构对齐分析

### HTTP 架构（参照标准）

```
HttpClient
  ↓ request()  ← 统一入口点
  ↓ MiddlewareChain
    ↓ RetryMiddleware
    ↓ SignatureMiddleware
    ↓ HttpEventPublisherMiddleware  ← 在这里自动发布事件
    ↓ _send_request_async()
```

### Web 架构（方案2 - 推荐）

```
BrowserManager
  ↓ start()  ← 统一入口点
  ↓ _setup_event_listeners()  ← 在这里自动注册监听器
    ↓ page.on("load", handler)
    ↓ page.on("request", handler)
    ↓ page.on("response", handler)
    ↓ page.on("console", handler)
    ↓ Playwright自动触发这些事件
```

**一致性验证**：

| 维度 | HTTP | Web（方案2） | 一致性 |
|------|------|-------------|--------|
| **统一入口点** | ✅ request() | ✅ start() + page.on() | ✅ 一致 |
| **自动拦截** | ✅ 中间件链 | ✅ 事件监听器 | ✅ 一致 |
| **用户透明** | ✅ 自动执行 | ✅ 自动注册 | ✅ 一致 |
| **维护成本** | ✅ 低（一个入口） | ✅ 低（Playwright原生API） | ✅ 一致 |
| **扩展性** | ✅ 添加中间件 | ✅ 添加事件监听器 | ✅ 一致 |

---

## 实施建议

### v3.44.0 实施计划

1. **增强 BrowserManager**
   ```python
   # src/df_test_framework/capabilities/drivers/web/playwright/browser.py

   class BrowserManager:
       def __init__(self, config=None, runtime=None):  # ✅ 新增runtime参数
           self.runtime = runtime
           self.event_bus = runtime.event_bus if runtime else None

       def start(self):
           # ... 创建浏览器
           if self.event_bus:
               self._setup_event_listeners(self._page)  # ✅ 自动注册监听器

       def _setup_event_listeners(self, page):  # ✅ 新增方法
           # 注册Playwright原生事件监听器
           pass
   ```

2. **增强 Fixtures**
   ```python
   # src/df_test_framework/testing/fixtures/ui.py

   @pytest.fixture(scope="session")
   def browser_manager(runtime):
       """浏览器管理器 - 自动注册事件监听器"""
       manager = runtime.browser_manager()  # ✅ 从Provider获取（已注入runtime）
       manager.start()  # ✅ 自动注册事件监听器
       yield manager
       manager.stop()

   @pytest.fixture
   def page(context, runtime):
       """页面实例 - 已自动监听事件"""
       p = context.new_page()

       # ✅ 如果需要，可以额外注册监听器
       # 但通常不需要，因为BrowserManager已经在context级别注册了

       yield p
       p.close()
   ```

3. **BasePage可选增强**（用户可选）
   ```python
   class BasePage:
       def goto(self):
           """导航（可选发布事件）"""
           url = urljoin(self.base_url, self.url)

           # 可选：发布导航开始事件
           if self.runtime and self.runtime.event_bus:
               event = UINavigationStartEvent.create(...)
               self.runtime.event_bus.publish_sync(event)

           self.page.goto(url)  # ✅ 使用原生API
   ```

**工作量**：约1-2天
- 增强BrowserManager（新增runtime参数 + 事件监听器注册）
- 更新Provider工厂（注入runtime）
- 更新文档

---

## 总结

### 推荐方案：方案2（BrowserManager事件监听器）

**核心优势**：
1. ✅ **不包装Playwright API** - 维护成本为零
2. ✅ **利用原生事件系统** - 与Playwright深度集成
3. ✅ **架构一致性** - 与HTTP的Middleware理念对齐
4. ✅ **用户透明** - 事件自动发布
5. ✅ **向后兼容** - 不破坏现有代码

**架构对齐**：

| 特性 | HTTP | Web (v3.44.0) |
|------|------|--------------|
| **统一拦截点** | ✅ HttpClient.request() | ✅ BrowserManager.start() |
| **自动机制** | ✅ Middleware自动执行 | ✅ 事件监听器自动触发 |
| **实现方式** | Middleware（洋葱模型） | Event Listener（观察者模式） |
| **维护成本** | ✅ 低（一个入口） | ✅ 低（原生API） |
| **用户体验** | ✅ 完全透明 | ✅ 完全透明 |

**结论**：虽然实现机制不同（Middleware vs Event Listener），但架构理念一致（统一拦截点 + 自动执行）✅

---

**文档维护者**: DF Test Framework Team
**最后更新**: 2026-01-08
**建议版本**: v3.44.0
