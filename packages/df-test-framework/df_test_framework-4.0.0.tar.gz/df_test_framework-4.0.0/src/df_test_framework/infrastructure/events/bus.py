"""
事件总线实现

v3.17.0 重构:
- 添加 publish_sync() 同步发布方法
- 添加测试隔离支持（set_test_event_bus）
- 按注册顺序执行处理器（保证顺序）

v3.38.7:
- 修复日志使用标准 logging 导致配置不生效的问题
- 改用 structlog get_logger() 统一日志配置

v3.46.1 重构:
- 添加作用域（scope）支持，实现事件隔离
- 单一 EventBus 实例，通过 scope 过滤事件
- 移除 set_test_event_bus/get_event_bus 全局状态
"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from df_test_framework.core.events.types import Event
from df_test_framework.core.protocols.event import IEventBus
from df_test_framework.infrastructure.logging import get_logger

T = TypeVar("T", bound=Event)

EventHandler = Callable[[Event], Awaitable[None]]


class EventBus(IEventBus):
    """事件总线

    发布/订阅模式，解耦组件通信。

    特性：
    - 异步处理
    - 同步发布模式（v3.17.0）
    - 事件处理异常不影响主流程
    - 支持通配符订阅（subscribe_all）
    - 支持装饰器语法
    - 作用域隔离（v3.46.1）

    v3.46.1 新增作用域支持：
    - 订阅时可指定 scope，只接收匹配的事件
    - scope=None 表示接收所有事件（全局订阅）
    - 事件的 scope 字段用于过滤订阅者

    示例:
        bus = EventBus()

        # 全局订阅（接收所有事件）
        @bus.on(HttpRequestEndEvent)
        async def log_request(event: HttpRequestEndEvent):
            print(f"{event.method} {event.url} -> {event.status_code}")

        # 作用域订阅（只接收特定测试的事件）
        bus.subscribe(HttpRequestEndEvent, handler, scope="test_ui_1")

        # 异步发布
        await bus.publish(event)

        # 同步发布（v3.17.0，推荐用于测试）
        bus.publish_sync(event)
    """

    def __init__(self, logger: Any | None = None):
        """初始化事件总线

        Args:
            logger: 日志对象（可选，默认使用 structlog）
        """
        # v3.46.1: 存储 (handler, scope) 元组
        self._handlers: dict[type[Event], list[tuple[EventHandler, str | None]]] = {}
        self._global_handlers: list[tuple[EventHandler, str | None]] = []
        self._logger = logger or get_logger(__name__)

    def subscribe(
        self,
        event_type: type[T],
        handler: Callable[[T], Awaitable[None]],
        scope: str | None = None,
    ) -> None:
        """订阅特定类型事件

        Args:
            event_type: 事件类型
            handler: 事件处理器
            scope: 作用域（None=全局订阅，接收所有事件；指定值=只接收该作用域的事件）

        示例:
            # 全局订阅
            async def handle_http(event: HttpRequestEndEvent):
                print(event.status_code)
            bus.subscribe(HttpRequestEndEvent, handle_http)

            # 作用域订阅
            bus.subscribe(HttpRequestEndEvent, handle_http, scope="test_ui_1")
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append((handler, scope))  # type: ignore
        scope_info = f" (scope={scope})" if scope else " (global)"
        self._logger.debug(f"Subscribed {handler.__name__} to {event_type.__name__}{scope_info}")

    def subscribe_all(self, handler: EventHandler, scope: str | None = None) -> None:
        """订阅所有事件

        Args:
            handler: 事件处理器
            scope: 作用域（None=全局订阅，接收所有事件；指定值=只接收该作用域的事件）

        示例:
            async def log_all(event: Event):
                print(f"Event: {type(event).__name__}")

            bus.subscribe_all(log_all)
        """
        self._global_handlers.append((handler, scope))
        scope_info = f" (scope={scope})" if scope else " (global)"
        self._logger.debug(f"Subscribed {handler.__name__} to all events{scope_info}")

    def unsubscribe(
        self,
        event_type: type[T],
        handler: Callable[[T], Awaitable[None]],
    ) -> None:
        """取消订阅

        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        if event_type in self._handlers:
            # 移除所有匹配的 handler（不管 scope）
            self._handlers[event_type] = [
                (h, s) for h, s in self._handlers[event_type] if h != handler
            ]
            self._logger.debug(f"Unsubscribed {handler.__name__} from {event_type.__name__}")

    def unsubscribe_all(self, handler: EventHandler) -> None:
        """取消订阅所有事件

        Args:
            handler: 事件处理器
        """
        self._global_handlers = [(h, s) for h, s in self._global_handlers if h != handler]

    async def publish(self, event: Event) -> None:
        """异步发布事件

        按注册顺序依次执行处理器（v3.17.0 改为顺序执行，保证处理顺序）。
        v3.46.1: 根据事件的 scope 过滤订阅者。

        Args:
            event: 要发布的事件

        示例:
            await bus.publish(HttpRequestEndEvent(
                method="GET",
                url="/api",
                status_code=200,
                duration=0.5,
                scope="test_ui_1"  # 只有订阅了该 scope 的处理器会收到
            ))
        """
        # 获取事件的 scope
        event_scope = getattr(event, "scope", None)

        # 获取所有可能的处理器
        type_handlers = self._handlers.get(type(event), [])
        all_handlers = type_handlers + self._global_handlers

        if not all_handlers:
            return

        # v3.46.1: 过滤匹配的处理器
        matched_handlers = []
        for handler, subscriber_scope in all_handlers:
            # 匹配规则：
            # 1. subscriber_scope=None：接收所有事件（全局订阅）
            # 2. subscriber_scope=event_scope：只接收匹配的事件
            if subscriber_scope is None or subscriber_scope == event_scope:
                matched_handlers.append(handler)

        # v3.17.0: 按注册顺序依次执行（保证顺序，便于调试）
        for handler in matched_handlers:
            await self._safe_call(handler, event)

    def publish_sync(self, event: Event) -> None:
        """同步发布事件（阻塞等待所有处理器完成）

        v3.17.0 新增：适用于测试场景，确保事件处理完成后再继续。
        v3.45.1 修复：在已有事件循环时使用 create_task 而非 run_until_complete
        v3.46.1: 支持作用域过滤

        Args:
            event: 要发布的事件

        示例:
            # 同步发布，等待所有处理器执行完成
            bus.publish_sync(HttpRequestStartEvent(...))

            # 执行操作...

            bus.publish_sync(HttpRequestEndEvent(...))
        """
        try:
            # 检测是否已在事件循环中运行
            asyncio.get_running_loop()
            # 如果已在事件循环中，使用 create_task 异步执行
            # 不能使用 run_until_complete，会导致嵌套事件循环错误
            asyncio.create_task(self.publish(event))
        except RuntimeError:
            # 没有运行中的事件循环，创建新的并执行
            asyncio.run(self.publish(event))

    async def _safe_call(self, handler: EventHandler, event: Event) -> None:
        """安全调用处理器（异常不传播）

        v3.18.0: 支持同步和异步两种处理器

        Args:
            handler: 事件处理器（可以是同步或异步函数）
            event: 事件
        """
        try:
            result = handler(event)
            # 检查是否为协程（异步函数的返回值）
            if asyncio.iscoroutine(result):
                await result
            # 如果是同步函数，result 为 None，无需 await
        except Exception as e:
            self._logger.warning(
                f"Event handler error: {handler.__name__} failed with {e}",
                exc_info=True,
            )

    def on(
        self,
        event_type: type[T],
        scope: str | None = None,
    ) -> Callable[[Callable[[T], Awaitable[None]]], Callable[[T], Awaitable[None]]]:
        """装饰器：订阅事件

        Args:
            event_type: 事件类型
            scope: 作用域（可选）

        Returns:
            装饰器函数

        示例:
            @bus.on(HttpRequestEndEvent)
            async def handle(event: HttpRequestEndEvent):
                print(event.status_code)

            @bus.on(HttpRequestEndEvent, scope="test_ui_1")
            async def handle_test(event: HttpRequestEndEvent):
                print("Test UI 1:", event.status_code)
        """

        def decorator(
            handler: Callable[[T], Awaitable[None]],
        ) -> Callable[[T], Awaitable[None]]:
            self.subscribe(event_type, handler, scope=scope)
            return handler

        return decorator

    def clear(self) -> None:
        """清空所有订阅"""
        self._handlers.clear()
        self._global_handlers.clear()

    def clear_scope(self, scope: str) -> None:
        """清理指定作用域的订阅

        v3.46.1 新增：用于测试结束时清理该测试的订阅

        Args:
            scope: 要清理的作用域

        示例:
            # 测试结束时清理
            bus.clear_scope("test_ui_1")
        """
        # 清理特定事件类型的订阅
        for event_type in self._handlers:
            self._handlers[event_type] = [
                (h, s) for h, s in self._handlers[event_type] if s != scope
            ]

        # 清理全局订阅
        self._global_handlers = [(h, s) for h, s in self._global_handlers if s != scope]

        self._logger.debug(f"Cleared all subscriptions for scope={scope}")

    def get_handlers(self, event_type: type[Event]) -> list[EventHandler]:
        """获取特定事件类型的处理器列表

        Args:
            event_type: 事件类型

        Returns:
            处理器列表（不包含 scope 信息）
        """
        return [h for h, _ in self._handlers.get(event_type, [])]

    def handler_count(self) -> int:
        """获取处理器总数"""
        count = sum(len(handlers) for handlers in self._handlers.values())
        return count + len(self._global_handlers)


# v3.46.1: 全局单例 EventBus（由 pytest_configure 创建）
_global_event_bus: EventBus | None = None


def get_global_event_bus() -> EventBus:
    """获取全局单例 EventBus

    v3.46.1: 简化为单一全局实例，不再支持测试隔离的 ContextVar。
    测试隔离通过事件的 scope 字段实现。

    Returns:
        全局 EventBus 实例

    Raises:
        RuntimeError: 如果 EventBus 未初始化
    """
    global _global_event_bus
    if _global_event_bus is None:
        raise RuntimeError(
            "Global EventBus not initialized. "
            "Ensure pytest_configure has been called or call set_global_event_bus() first."
        )
    return _global_event_bus


def set_global_event_bus(bus: EventBus) -> None:
    """设置全局单例 EventBus

    v3.46.1: 由 pytest_configure 调用，初始化全局 EventBus。

    Args:
        bus: EventBus 实例
    """
    global _global_event_bus
    _global_event_bus = bus
