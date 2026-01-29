"""REST API客户端（v4.0.0 异步优先）

支持多种HTTP客户端实现（httpx、requests等）
通过Factory模式提供统一接口

v4.0.0:
- 推荐使用 AsyncHttpClient 和 AsyncBaseAPI
- 同步版本保留用于兼容
"""

# 协议定义
# 工厂类
from .factory import RestClientFactory

# 异步实现（推荐）
from .httpx.async_base_api import AsyncBaseAPI
from .httpx.async_client import AsyncHttpClient

# 同步实现（兼容）
from .httpx.base_api import BaseAPI, BusinessError
from .httpx.client import HttpClient
from .protocols import BaseAPIProtocol, RestClientProtocol

__all__ = [
    # 协议
    "RestClientProtocol",
    "BaseAPIProtocol",
    # 工厂
    "RestClientFactory",
    # 异步实现（推荐）
    "AsyncHttpClient",
    "AsyncBaseAPI",
    # 同步实现（兼容）
    "HttpClient",
    "BaseAPI",
    # 异常
    "BusinessError",
]
