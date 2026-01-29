"""API基类模板

v4.0.0: 支持异步版本（AsyncBaseAPI + AsyncHttpClient）
"""

BASE_API_TEMPLATE = """\"\"\"API基类

提供统一的API调用接口和业务错误处理。

v4.0.0 新增异步版本:
- 推荐使用 AsyncBaseAPI + AsyncHttpClient 获得 30 倍性能提升
- 本模板使用同步版本（向后兼容）
- 异步版本示例请参考文档：docs/guides/async_api_guide.md

异步版本示例:
    from df_test_framework import AsyncBaseAPI, AsyncHttpClient

    class {ProjectName}BaseAPI(AsyncBaseAPI):
        async def _check_business_error(self, response_data: dict) -> None:
            # 异步错误检查
            ...
\"\"\"

from df_test_framework import BaseAPI, HttpClient
from df_test_framework.capabilities.clients.http.rest.httpx import BusinessError


class {ProjectName}BaseAPI(BaseAPI):
    \"\"\"项目API基类

    继承框架的BaseAPI，添加项目特定的业务错误检查。

    特性:
    - 自动检查业务错误（code != 200）
    - 自动HTTP重试
    - 统一错误处理
    \"\"\"

    def __init__(self, http_client: HttpClient):
        super().__init__(http_client)

    def _check_business_error(self, response_data: dict) -> None:
        \"\"\"检查业务错误

        Args:
            response_data: 响应数据字典

        Raises:
            BusinessError: 业务错误（code != 200）
        \"\"\"
        code = response_data.get("code")
        if code != 200:
            message = response_data.get("message", "未知错误")
            raise BusinessError(message=message, code=code, data=response_data)


__all__ = ["{ProjectName}BaseAPI"]
"""

__all__ = ["BASE_API_TEMPLATE"]
