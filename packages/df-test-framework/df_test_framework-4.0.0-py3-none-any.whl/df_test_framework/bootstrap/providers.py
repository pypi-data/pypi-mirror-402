"""
资源提供者系统 (Layer 4: Bootstrap)

职责:
- 定义 Provider 协议
- 实现 SingletonProvider（单例提供者）
- 实现 ProviderRegistry（提供者注册表）
- 提供 default_providers() 工厂函数

v3.16.0 架构重构:
- 从 infrastructure/providers/ 迁移到 bootstrap/
- 作为 Layer 4 可以合法依赖 capabilities/ (Layer 2)
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, TypeVar

from df_test_framework.capabilities.clients.http.rest.httpx import AsyncHttpClient, HttpClient
from df_test_framework.capabilities.databases.async_database import AsyncDatabase
from df_test_framework.capabilities.databases.database import Database
from df_test_framework.capabilities.databases.redis.async_redis import AsyncRedis
from df_test_framework.capabilities.databases.redis.redis_client import RedisClient
from df_test_framework.capabilities.drivers.web.playwright.async_browser import AsyncBrowserManager
from df_test_framework.capabilities.drivers.web.playwright.browser import BrowserManager
from df_test_framework.capabilities.storages import LocalFileClient, OSSClient, S3Client
from df_test_framework.infrastructure.config.schema import FrameworkSettings

TRuntime = TypeVar("TRuntime", bound="RuntimeContextProtocol")


class RuntimeContextProtocol(Protocol):
    settings: FrameworkSettings


class Provider(Protocol):
    def get(self, context: TRuntime): ...

    def shutdown(self) -> None: ...


class SingletonProvider:
    """
    Provider wrapper that memoises a single instance and calls optional
    `close`/`shutdown` when released.

    使用双重检查锁定模式确保线程安全：
    1. 第一次检查（无锁）：快速路径，如果实例已存在则直接返回
    2. 获取锁：确保只有一个线程进入临界区
    3. 第二次检查（有锁）：防止多个线程同时创建实例
    """

    def __init__(self, factory: Callable[[TRuntime], object]):
        self._factory = factory
        self._instance: object | None = None
        self._lock = threading.Lock()  # 用于双重检查锁定

    def get(self, context: TRuntime):
        """获取单例实例（线程安全）

        Args:
            context: 运行时上下文

        Returns:
            单例实例
        """
        # 第一次检查（无锁，快速路径）
        if self._instance is None:
            # 获取锁
            with self._lock:
                # 第二次检查（有锁，防止竞态条件）
                if self._instance is None:
                    self._instance = self._factory(context)
        return self._instance

    def reset(self) -> None:
        """重置单例（主要用于测试）"""
        with self._lock:
            if self._instance is not None:
                # 先调用清理方法
                instance = self._instance
                for method_name in ("close", "shutdown"):
                    method = getattr(instance, method_name, None)
                    if callable(method):
                        try:
                            method()
                        except Exception:  # pragma: no cover
                            pass
                # 再清空引用
                self._instance = None

    def shutdown(self) -> None:
        """关闭并释放单例资源"""
        self.reset()


@dataclass
class ProviderRegistry:
    providers: dict[str, Provider]

    def get(self, key: str, context: TRuntime):
        if key not in self.providers:
            raise KeyError(f"Provider '{key}' not registered")
        return self.providers[key].get(context)

    def shutdown(self) -> None:
        for provider in self.providers.values():
            provider.shutdown()

    def register(self, key: str, provider: Provider) -> None:
        self.providers[key] = provider

    def extend(self, items: dict[str, Provider]) -> None:
        for key, provider in items.items():
            self.register(key, provider)


def default_providers() -> ProviderRegistry:
    """
    Build the default provider registry using FrameworkSettings.
    """

    def http_factory(context: TRuntime) -> HttpClient:
        """创建同步 HTTP 客户端"""
        config = context.settings.http
        if not config.base_url:
            raise ValueError("HTTP base URL is not configured")
        return HttpClient(
            base_url=config.base_url,
            timeout=config.timeout,
            verify_ssl=config.verify_ssl,
            max_retries=config.max_retries,
            max_connections=config.max_connections,
            max_keepalive_connections=config.max_keepalive_connections,
            config=config,  # 传递HTTPConfig以支持拦截器自动加载
            runtime=context,  # v3.46.1: 传递整个 runtime（包含 event_bus 和 scope）
        )

    def async_http_factory(context: TRuntime) -> AsyncHttpClient:
        """创建异步 HTTP 客户端（v4.0.0）"""
        config = context.settings.http
        if not config.base_url:
            raise ValueError("HTTP base URL is not configured")
        return AsyncHttpClient(
            base_url=config.base_url,
            timeout=config.timeout,
            verify_ssl=config.verify_ssl,
            max_retries=config.max_retries,
            max_connections=config.max_connections,
            max_keepalive_connections=config.max_keepalive_connections,
            config=config,
            runtime=context,
        )

    def db_factory(context: TRuntime) -> Database:
        """创建同步数据库客户端"""
        config = context.settings.db
        if config is None:
            raise ValueError("Database configuration is not set")
        conn_str = config.resolved_connection_string()
        return Database(
            connection_string=conn_str,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_timeout=config.pool_timeout,
            pool_recycle=config.pool_recycle,
            pool_pre_ping=config.pool_pre_ping,
            echo=config.echo,
            runtime=context,
        )

    def async_db_factory(context: TRuntime) -> AsyncDatabase:
        """创建异步数据库客户端（v4.0.0）"""
        config = context.settings.db
        if config is None:
            raise ValueError("Database configuration is not set")
        conn_str = config.resolved_async_connection_string()
        return AsyncDatabase(
            connection_string=conn_str,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_timeout=config.pool_timeout,
            pool_recycle=config.pool_recycle,
            pool_pre_ping=config.pool_pre_ping,
            echo=config.echo,
            runtime=context,
        )

    def redis_factory(context: TRuntime) -> RedisClient:
        """创建同步 Redis 客户端"""
        config = context.settings.redis
        if config is None:
            raise ValueError("Redis configuration is not set")
        password = config.password.get_secret_value() if config.password else None
        return RedisClient(
            host=config.host,
            port=config.port,
            db=config.db,
            password=password,
            max_connections=config.max_connections,
            decode_responses=config.decode_responses,
            runtime=context,
        )

    def async_redis_factory(context: TRuntime) -> AsyncRedis:
        """创建异步 Redis 客户端（v4.0.0）"""
        config = context.settings.redis
        if config is None:
            raise ValueError("Redis configuration is not set")
        password = config.password.get_secret_value() if config.password else None
        return AsyncRedis(
            host=config.host,
            port=config.port,
            db=config.db,
            password=password,
            max_connections=config.max_connections,
            decode_responses=config.decode_responses,
            runtime=context,
        )

    def local_file_factory(context: TRuntime) -> LocalFileClient:
        """创建本地文件存储客户端

        如果未配置 local_file，则使用默认配置
        """
        from df_test_framework.capabilities.storages.file import LocalFileConfig

        storage_config = context.settings.storage
        if storage_config and storage_config.local_file:
            config = storage_config.local_file
        else:
            # 使用默认配置
            config = LocalFileConfig()

        return LocalFileClient(config)

    def s3_factory(context: TRuntime) -> S3Client:
        """创建 S3 对象存储客户端

        如果未配置 s3，则抛出异常
        """
        from df_test_framework.core.exceptions import ConfigurationError

        storage_config = context.settings.storage
        if not storage_config or not storage_config.s3:
            raise ConfigurationError(
                "S3 storage not configured. "
                "Please configure settings.storage.s3 before using S3Client"
            )

        return S3Client(storage_config.s3)

    def oss_factory(context: TRuntime) -> OSSClient:
        """创建阿里云 OSS 对象存储客户端

        如果未配置 oss，则抛出异常
        """
        from df_test_framework.core.exceptions import ConfigurationError

        storage_config = context.settings.storage
        if not storage_config or not storage_config.oss:
            raise ConfigurationError(
                "OSS storage not configured. "
                "Please configure settings.storage.oss before using OSSClient"
            )

        return OSSClient(storage_config.oss)

    def browser_manager_factory(context: TRuntime) -> BrowserManager:
        """创建同步浏览器管理器

        v3.42.0: 支持 WebConfig 配置驱动
        v3.44.0: 注入 RuntimeContext，自动注册事件监听器

        使用 WebConfig 配置创建 BrowserManager。
        如果未配置 web，则使用默认配置。
        自动注入 runtime，启用事件发布功能。
        """
        web_config = context.settings.web
        if web_config:
            return BrowserManager(config=web_config, runtime=context)
        else:
            # 使用默认配置
            return BrowserManager(runtime=context)

    def async_browser_manager_factory(context: TRuntime) -> AsyncBrowserManager:
        """创建异步浏览器管理器（v4.0.0）

        使用 WebConfig 配置创建 AsyncBrowserManager。
        如果未配置 web，则使用默认配置。
        自动注入 runtime，启用事件发布功能。
        """
        web_config = context.settings.web
        if web_config:
            return AsyncBrowserManager(config=web_config, runtime=context)
        else:
            # 使用默认配置
            return AsyncBrowserManager(runtime=context)

    return ProviderRegistry(
        providers={
            # HTTP 客户端
            "http_client": SingletonProvider(http_factory),
            "async_http_client": SingletonProvider(async_http_factory),  # v4.0.0
            # 数据库
            "database": SingletonProvider(db_factory),
            "async_database": SingletonProvider(async_db_factory),  # v4.0.0
            # Redis
            "redis": SingletonProvider(redis_factory),
            "async_redis": SingletonProvider(async_redis_factory),  # v4.0.0
            # 存储
            "local_file": SingletonProvider(local_file_factory),
            "s3": SingletonProvider(s3_factory),
            "oss": SingletonProvider(oss_factory),
            # 浏览器
            "browser_manager": SingletonProvider(browser_manager_factory),
            "async_browser_manager": SingletonProvider(async_browser_manager_factory),  # v4.0.0
        }
    )


__all__ = [
    "Provider",
    "SingletonProvider",
    "ProviderRegistry",
    "default_providers",
]
