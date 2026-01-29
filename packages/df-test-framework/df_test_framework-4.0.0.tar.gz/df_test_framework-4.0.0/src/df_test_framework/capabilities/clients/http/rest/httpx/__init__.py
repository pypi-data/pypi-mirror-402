"""HTTP模块 - HTTP客户端和API基类（v4.0.0 异步优先）

v4.0.0:
- 推荐使用 AsyncHttpClient 和 AsyncBaseAPI（异步优先）
- HttpClient 和 BaseAPI 保留用于迁移兼容
"""

from .async_base_api import AsyncBaseAPI
from .async_client import AsyncHttpClient
from .base_api import BaseAPI, BusinessError
from .client import HttpClient

__all__ = [
    # 异步版本（推荐）
    "AsyncHttpClient",
    "AsyncBaseAPI",
    # 同步版本（兼容）
    "HttpClient",
    "BaseAPI",
    # 异常
    "BusinessError",
]
