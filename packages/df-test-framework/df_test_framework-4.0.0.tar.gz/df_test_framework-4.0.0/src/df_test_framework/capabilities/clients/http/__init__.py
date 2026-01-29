"""
HTTP 客户端（v4.0.0 异步优先）

v4.0.0 重大变更：
- 推荐使用 AsyncHttpClient 和 AsyncBaseAPI（性能提升 2-3 倍）
- 同步版本（HttpClient、BaseAPI）保留用于兼容

v3.14.0 增强：
- 统一中间件系统（洋葱模型）
- 可观测性集成
- 上下文传播

导入示例：
    # v4.0.0 异步版本（推荐）
    from df_test_framework.capabilities.clients.http import AsyncHttpClient, AsyncBaseAPI

    async with AsyncHttpClient("https://api.example.com") as client:
        api = AsyncBaseAPI(client)
        response = await api.get("/users")

    # v3.x 同步版本（兼容）
    from df_test_framework.capabilities.clients.http import HttpClient, BaseAPI

    # 中间件
    from df_test_framework.capabilities.clients.http.middleware import (
        SignatureMiddleware,
        BearerTokenMiddleware,
    )
"""

# 核心对象
from df_test_framework.capabilities.clients.http.core.request import Request
from df_test_framework.capabilities.clients.http.core.response import Response

# 异步客户端（推荐）
from df_test_framework.capabilities.clients.http.rest.httpx.async_base_api import AsyncBaseAPI
from df_test_framework.capabilities.clients.http.rest.httpx.async_client import AsyncHttpClient

# 同步客户端（兼容）
from df_test_framework.capabilities.clients.http.rest.httpx.base_api import (
    BaseAPI,
    BusinessError,
)
from df_test_framework.capabilities.clients.http.rest.httpx.client import HttpClient

__all__ = [
    # 异步版本（推荐）
    "AsyncHttpClient",
    "AsyncBaseAPI",
    # 同步版本（兼容）
    "HttpClient",
    "BaseAPI",
    # 核心对象
    "Request",
    "Response",
    # 异常
    "BusinessError",
]
