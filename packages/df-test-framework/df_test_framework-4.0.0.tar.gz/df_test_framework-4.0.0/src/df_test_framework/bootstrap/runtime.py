"""
运行时上下文 (Layer 4: Bootstrap)

职责:
- RuntimeContext: 保持运行时单例（settings, logger, providers, event_bus）
- RuntimeBuilder: 构建 RuntimeContext 的辅助类

v3.16.0 架构重构:
- 从 infrastructure/runtime/ 迁移到 bootstrap/
- 作为 Layer 4 可以合法依赖所有层

v3.44.0 架构重构:
- 新增 event_bus 字段，统一事件总线管理
- EventBus 作为运行时核心组件，与 settings、logger 同级
- 所有能力层（HTTP、Web UI、Database 等）通过 runtime.event_bus 发布事件
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from df_test_framework.core.events.types import Event
    from df_test_framework.infrastructure.events import EventBus
    from df_test_framework.infrastructure.logging import Logger

from df_test_framework.infrastructure.config.schema import FrameworkSettings
from df_test_framework.infrastructure.plugins import PluggyPluginManager as ExtensionManager

from .providers import ProviderRegistry, default_providers


@dataclass(frozen=True)
class RuntimeContext:
    """运行时上下文

    保持运行时单例，包含：
    - settings: 框架配置
    - logger: 日志记录器
    - providers: 服务提供者注册表
    - event_bus: 事件总线（v3.44.0）
    - extensions: 扩展管理器
    - scope: 事件作用域（v3.46.1）

    v3.44.0: 新增 event_bus 字段
    - EventBus 作为运行时核心组件
    - 所有能力层通过 runtime.publish_event() 发布事件

    v3.46.1: 重构为单一 EventBus + 作用域模式
    - 新增 scope 字段，用于事件隔离
    - 新增 publish_event() 方法，自动注入 scope
    - 移除 with_event_bus()，改用 with_scope()
    """

    settings: FrameworkSettings
    logger: Logger
    providers: ProviderRegistry
    event_bus: EventBus  # v3.46.1: 不再是 Optional，必须提供
    extensions: ExtensionManager | None = field(default=None)
    scope: str | None = field(default=None)  # v3.46.1: 事件作用域

    def get(self, key: str):
        return self.providers.get(key, self)

    def http_client(self):
        """获取同步 HTTP 客户端"""
        return self.get("http_client")

    def async_http_client(self):
        """获取异步 HTTP 客户端（v4.0.0）"""
        return self.get("async_http_client")

    def database(self):
        """获取同步数据库客户端"""
        return self.get("database")

    def async_database(self):
        """获取异步数据库客户端（v4.0.0）"""
        return self.get("async_database")

    def redis(self):
        """获取同步 Redis 客户端"""
        return self.get("redis")

    def async_redis(self):
        """获取异步 Redis 客户端（v4.0.0）"""
        return self.get("async_redis")

    def local_file(self):
        """获取本地文件存储客户端"""
        return self.get("local_file")

    def s3(self):
        """获取 S3 对象存储客户端"""
        return self.get("s3")

    def oss(self):
        """获取阿里云 OSS 对象存储客户端"""
        return self.get("oss")

    def browser_manager(self):
        """获取同步浏览器管理器（v3.42.0）"""
        return self.get("browser_manager")

    def async_browser_manager(self):
        """获取异步浏览器管理器（v4.0.0）"""
        return self.get("async_browser_manager")

    def publish_event(self, event: Event) -> None:
        """发布事件（自动注入当前作用域）

        v3.46.1 新增：统一的事件发布接口，自动注入 scope。

        Args:
            event: 要发布的事件

        示例:
            # API 测试（无 scope，全局事件）
            runtime.publish_event(HttpRequestStartEvent(...))

            # UI 测试（有 scope，测试隔离）
            test_runtime.publish_event(UIActionEvent(...))
        """
        from dataclasses import replace

        # 如果当前 runtime 有 scope，自动注入到事件
        if self.scope:
            event = replace(event, scope=self.scope)

        # 发布事件
        self.event_bus.publish_sync(event)

    def close(self) -> None:
        """关闭运行时上下文，释放资源"""
        self.providers.shutdown()
        # v3.46.1: 清理当前 scope 的订阅
        if self.scope:
            self.event_bus.clear_scope(self.scope)

    def with_overrides(self, overrides: dict[str, Any]) -> RuntimeContext:
        """创建带有配置覆盖的新RuntimeContext

        v3.5 Phase 3: 运行时动态覆盖配置，用于测试场景

        Args:
            overrides: 要覆盖的配置字典（支持嵌套，如 {"http.timeout": 10}）

        Returns:
            新的RuntimeContext实例，配置已被覆盖

        Example:
            >>> # 在测试中临时修改超时配置
            >>> test_ctx = ctx.with_overrides({"http": {"timeout": 1}})
            >>> client = test_ctx.http_client()  # 使用1秒超时

            >>> # 支持点号路径
            >>> test_ctx = ctx.with_overrides({"http.base_url": "http://mock.local"})

        Note:
            - 返回新实例，不修改原RuntimeContext
            - logger共享（无状态），extensions共享（配置不变）
            - providers必须重新创建，避免SingletonProvider共享导致配置不隔离
            - event_bus 共享（测试隔离由 fixture 控制）
            - 适用于测试中临时修改配置，不影响全局
        """
        # 创建settings的副本并应用覆盖
        new_settings = self._apply_overrides_to_settings(self.settings, overrides)

        # 创建新的ProviderRegistry，而非共享
        # 原因: SingletonProvider会缓存实例，导致不同配置下共享同一HttpClient/Database等
        # 解决方案: 使用default_providers()创建新的Provider实例
        new_providers = default_providers()

        # 创建新的RuntimeContext，logger、extensions、event_bus、scope 可共享
        return RuntimeContext(
            settings=new_settings,
            logger=self.logger,
            providers=new_providers,
            event_bus=self.event_bus,
            extensions=self.extensions,
            scope=self.scope,  # v3.46.1: 保持 scope
        )

    def with_scope(self, scope: str) -> RuntimeContext:
        """创建带有测试作用域的 RuntimeContext

        v3.46.1 新增：用于测试隔离，每个测试有独立的事件作用域。

        Args:
            scope: 测试作用域（通常使用测试 ID）

        Returns:
            新的 RuntimeContext 实例（共享 EventBus，但有独立 scope）

        示例:
            # 在 test_runtime fixture 中使用
            test_scope = request.node.nodeid
            test_ctx = runtime.with_scope(test_scope)
        """
        return RuntimeContext(
            settings=self.settings,
            logger=self.logger,
            providers=self.providers,
            event_bus=self.event_bus,  # 共享同一个 EventBus
            extensions=self.extensions,
            scope=scope,  # 设置新的 scope
        )

    def _apply_overrides_to_settings(
        self, settings: FrameworkSettings, overrides: dict[str, Any]
    ) -> FrameworkSettings:
        """应用覆盖到settings

        Args:
            settings: 原始settings
            overrides: 覆盖字典

        Returns:
            新的settings实例
        """
        # 将settings转为字典
        settings_dict = settings.model_dump()

        # 应用覆盖（支持嵌套和点号路径）
        for key, value in overrides.items():
            if "." in key:
                # 支持点号路径: "http.timeout" -> {"http": {"timeout": ...}}
                parts = key.split(".")
                current = settings_dict
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            else:
                # 直接覆盖
                if (
                    isinstance(value, dict)
                    and key in settings_dict
                    and isinstance(settings_dict[key], dict)
                ):
                    # 嵌套字典：深度合并
                    settings_dict[key] = {**settings_dict[key], **value}
                else:
                    settings_dict[key] = value

        # 重新创建settings实例
        return settings.__class__(**settings_dict)


class RuntimeBuilder:
    """RuntimeContext 构建器

    v3.44.0: 新增 with_event_bus() 方法
    """

    def __init__(self):
        self._settings: FrameworkSettings | None = None
        self._logger: Logger | None = None
        self._providers_factory: Callable[[], ProviderRegistry] | None = None
        self._event_bus: EventBus | None = None
        self._extensions: ExtensionManager | None = None

    def with_settings(self, settings: FrameworkSettings) -> RuntimeBuilder:
        self._settings = settings
        return self

    def with_logger(self, logger: Logger) -> RuntimeBuilder:
        self._logger = logger
        return self

    def with_providers(self, factory: Callable[[], ProviderRegistry]) -> RuntimeBuilder:
        self._providers_factory = factory
        return self

    def with_event_bus(self, event_bus: EventBus) -> RuntimeBuilder:
        """设置 EventBus

        v3.44.0: 新增
        """
        self._event_bus = event_bus
        return self

    def with_extensions(self, extensions: ExtensionManager) -> RuntimeBuilder:
        self._extensions = extensions
        return self

    def build(self) -> RuntimeContext:
        if not self._settings:
            raise ValueError("Settings must be provided to RuntimeBuilder")
        if not self._logger:
            raise ValueError("Logger must be provided to RuntimeBuilder")

        providers = (
            self._providers_factory()
            if self._providers_factory is not None
            else default_providers()
        )

        return RuntimeContext(
            settings=self._settings,
            logger=self._logger,
            providers=providers,
            event_bus=self._event_bus,
            extensions=self._extensions,
        )


__all__ = [
    "RuntimeContext",
    "RuntimeBuilder",
]
