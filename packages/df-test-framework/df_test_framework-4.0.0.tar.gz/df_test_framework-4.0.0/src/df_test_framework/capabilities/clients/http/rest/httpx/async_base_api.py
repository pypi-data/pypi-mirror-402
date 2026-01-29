"""异步 API 基类（v4.0.0）

v4.0.0 新增:
- AsyncBaseAPI: 全异步 API 基类
- 基于 AsyncHttpClient，所有方法都是异步的
- 完整支持 Pydantic 模型自动序列化和验证
- 完整支持认证控制（skip_auth, token）
- 完整支持文件上传（files 参数）

设计理念:
- 与 BaseAPI 保持 API 一致性，方便迁移
- 所有 HTTP 方法都是异步的（需要 await）
- 响应解析、业务错误检查逻辑保持一致
"""

from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from df_test_framework.capabilities.clients.http.core import Response
from df_test_framework.capabilities.clients.http.core.request import FilesTypes
from df_test_framework.infrastructure.logging import get_logger

from .async_client import AsyncHttpClient

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


# ========== 业务异常 ==========


class BusinessError(Exception):
    """业务错误异常

    当API返回的业务状态码表示失败时抛出此异常

    Attributes:
        message: 错误消息
        code: 业务错误码
        data: 原始响应数据
    """

    def __init__(
        self, message: str, code: int | str | None = None, data: dict[str, Any] | None = None
    ):
        self.message = message
        self.code = code
        self.data = data
        super().__init__(message)

    def __str__(self) -> str:
        if self.code:
            return f"[业务错误 {self.code}] {self.message}"
        return f"[业务错误] {self.message}"


class AsyncBaseAPI:
    """
    异步 API 基类（v4.0.0）

    职责:
    - 管理 AsyncHttpClient
    - 提供便捷的异步 get/post/put/delete 方法
    - 解析响应为 Pydantic 模型
    - 处理业务错误

    设计原则:
    - ✅ 所有方法都是异步的（async def）
    - ✅ 专注于 API 封装和响应解析
    - ✅ 中间件在 AsyncHttpClient 层统一管理

    使用中间件的推荐方式:
        # 在 HTTPConfig 中配置中间件（全局生效）
        >>> settings = FrameworkSettings(
        ...     http=HTTPConfig(
        ...         middlewares=[
        ...             SignatureMiddlewareConfig(algorithm="md5", secret="..."),
        ...             BearerTokenMiddlewareConfig(source=TokenSource.STATIC, token="...")
        ...         ]
        ...     )
        ... )
        >>> async with AsyncHttpClient(base_url="...", config=settings.http) as client:
        ...     api = MyAsyncAPI(client)
        ...     response = await api.get("/users")

    Example:
        >>> class UserAPI(AsyncBaseAPI):
        ...     async def get_current_user(self) -> UserResponse:
        ...         return await self.get("/users/current", model=UserResponse)
        ...
        >>> async with AsyncHttpClient("https://api.example.com") as client:
        ...     api = UserAPI(client)
        ...     user = await api.get_current_user()
    """

    def __init__(self, http_client: AsyncHttpClient):
        """
        初始化异步 API 基类

        Args:
            http_client: 异步 HTTP 客户端实例
        """
        self.http_client = http_client

    def _check_business_error(self, response_data: dict[str, Any]) -> None:
        """
        检查业务错误 (可在子类中重写)

        默认实现不检查业务错误,适用于没有统一响应格式的项目
        子类可以根据自己的业务响应格式重写此方法

        常见实现示例:

        # 示例1: 检查 success 字段
        def _check_business_error(self, response_data):
            if not response_data.get("success", True):
                raise BusinessError(
                    message=response_data.get("message", "未知错误"),
                    code=response_data.get("code"),
                    data=response_data
                )

        # 示例2: 检查 code 字段
        def _check_business_error(self, response_data):
            code = response_data.get("code", 200)
            if code not in [200, 0]:  # 假设200和0表示成功
                raise BusinessError(
                    message=response_data.get("message", "未知错误"),
                    code=code,
                    data=response_data
                )

        Args:
            response_data: 响应数据字典

        Raises:
            BusinessError: 业务错误
        """
        pass  # 默认不检查,由子类决定是否实现

    def _parse_response(
        self,
        response: Response,
        model: type[T] | None = None,
        raise_for_status: bool = True,
        check_business_error: bool = True,
    ) -> T | dict[str, Any]:
        """
        解析响应数据

        Args:
            response: 框架 Response 对象
            model: Pydantic 模型类,如果提供则解析为模型实例
            raise_for_status: 是否在 HTTP 错误时抛出异常
            check_business_error: 是否检查业务错误 (调用 _check_business_error 方法)

        Returns:
            解析后的数据 (Pydantic 模型实例或字典)

        Raises:
            Exception: 当 HTTP 状态码表示错误且 raise_for_status=True 时
            BusinessError: 当业务状态码表示错误且 check_business_error=True 时
            ValidationError: 当响应数据验证失败时
        """
        # 检查 HTTP 状态码
        if raise_for_status:
            if response.status_code >= 400:
                logger.error(f"HTTP 错误: {response.status_code} - {response.body[:200]}")
                raise Exception(f"HTTP {response.status_code}: {response.body[:200]}")

        # 解析 JSON 响应
        response_data = response.json()
        if response_data is None:
            logger.error(f"解析 JSON 失败, 响应内容: {response.body[:200]}")
            raise Exception(f"无法解析 JSON 响应: {response.body[:200]}")

        # 检查业务错误
        if check_business_error:
            try:
                self._check_business_error(response_data)
            except BusinessError as e:
                logger.error(f"业务错误: {e}")
                logger.debug(f"响应数据: {response_data}")
                raise

        # 如果提供了模型,则解析为模型实例
        if model:
            try:
                return model.model_validate(response_data)
            except ValidationError as e:
                logger.error(f"响应数据验证失败: {e.error_count()} 个错误")
                logger.debug(f"验证错误详情: {e.errors()}")
                logger.debug(f"原始响应数据: {response_data}")
                raise
            except Exception as e:
                logger.error(f"解析响应模型失败: {str(e)}")
                logger.debug(f"响应数据: {response_data}")
                raise

        return response_data

    def _build_url(self, endpoint: str) -> str:
        """
        构建请求路径

        遵循 httpx 官方 URL 拼接规范
        - base_url 不需要尾部 /（如 "https://api.example.com"）
        - endpoint 以 / 开头（如 "/users"）

        根据 httpx 官方文档:
        https://github.com/encode/httpx/blob/master/docs/advanced/clients.md

            with httpx.Client(base_url='http://httpbin.org') as client:
                r = client.get('/headers')  # → http://httpbin.org/headers

        Args:
            endpoint: API 端点路径，应以 / 开头（如 "/admin/current"）

        Returns:
            确保以 / 开头的路径

        Examples:
            base_url="https://api.example.com"
            endpoint="/users" → 返回 "/users"
            最终URL: "https://api.example.com/users" ✅

            endpoint="users" → 返回 "/users"（自动补全）
        """
        # 确保 endpoint 以 / 开头，遵循 httpx 官方规范
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        return endpoint

    async def get(
        self,
        endpoint: str,
        model: type[T] | None = None,
        skip_auth: bool = False,
        token: str | None = None,
        **kwargs,
    ) -> T | dict[str, Any]:
        """
        发送异步 GET 请求（v4.0.0）

        Args:
            endpoint: API端点
            model: 响应模型类
            skip_auth: 跳过认证中间件（不添加 Token）
            token: 使用自定义 Token（绕过中间件缓存）
            **kwargs: 其他请求参数
                - params: 查询参数（支持 dict 或 Pydantic 模型）

        Returns:
            解析后的响应数据

        Note:
            如果 params 参数是 Pydantic BaseModel 实例，会自动序列化为字典。
            序列化时会使用 by_alias=True（使用字段别名）和 exclude_none=True（排除 None 值）。

            示例:
                >>> class QueryRequest(BaseModel):
                ...     user_id: str = Field(alias="userId")
                ...     status: str | None = None
                >>>
                >>> request = QueryRequest(user_id="user_001")
                >>> await api.get("/users", params=request)  # 自动转换为 {"userId": "user_001"}

            认证控制:
                >>> # 跳过认证（测试未登录场景）
                >>> await api.get("/users/current", skip_auth=True)
                >>> # 使用自定义 Token（测试特定 Token）
                >>> await api.get("/users/current", token="my_token")

        Example:
            >>> user = await api.get("/users/1", model=UserResponse)
            >>> users = await api.get("/users", params={"page": 1, "size": 10})
        """
        # 自动处理 Pydantic 模型序列化为查询参数
        if "params" in kwargs and isinstance(kwargs["params"], BaseModel):
            kwargs["params"] = kwargs["params"].model_dump(
                mode="json", by_alias=True, exclude_none=True
            )

        # 传递认证控制参数（通过 metadata）
        if skip_auth:
            if "metadata" not in kwargs:
                kwargs["metadata"] = {}
            kwargs["metadata"]["skip_auth"] = True
        if token:
            if "metadata" not in kwargs:
                kwargs["metadata"] = {}
            kwargs["metadata"]["custom_token"] = token

        url = self._build_url(endpoint)
        response = await self.http_client.get(url, **kwargs)
        return self._parse_response(response, model)

    async def post(
        self,
        endpoint: str,
        model: type[T] | None = None,
        skip_auth: bool = False,
        token: str | None = None,
        files: FilesTypes | None = None,
        **kwargs,
    ) -> T | dict[str, Any]:
        """
        发送异步 POST 请求（v4.0.0）

        Args:
            endpoint: API端点
            model: 响应模型类
            skip_auth: 跳过认证中间件（不添加 Token）
            token: 使用自定义 Token（绕过中间件缓存）
            files: 文件上传（multipart/form-data）
            **kwargs: 其他请求参数

        Returns:
            解析后的响应数据

        Note:
            如果 json 参数是 Pydantic BaseModel 实例，会自动序列化为字典

        Example:
            >>> # JSON 请求
            >>> user = await api.post("/users", json={"name": "Alice"}, model=UserResponse)
            >>>
            >>> # 文件上传
            >>> template = await api.post("/templates", files={
            ...     "name": (None, "模板名称"),
            ...     "image": ("img.jpg", img_bytes, "image/jpeg"),
            ... }, model=TemplateResponse)
        """
        # 自动处理 Pydantic 模型序列化
        if "json" in kwargs and isinstance(kwargs["json"], BaseModel):
            kwargs["json"] = kwargs["json"].model_dump(
                mode="json", by_alias=True, exclude_none=True
            )

        # 传递认证控制参数
        if skip_auth:
            if "metadata" not in kwargs:
                kwargs["metadata"] = {}
            kwargs["metadata"]["skip_auth"] = True
        if token:
            if "metadata" not in kwargs:
                kwargs["metadata"] = {}
            kwargs["metadata"]["custom_token"] = token

        # 传递 files 参数
        if files is not None:
            kwargs["files"] = files

        url = self._build_url(endpoint)
        response = await self.http_client.post(url, **kwargs)
        return self._parse_response(response, model)

    async def put(
        self,
        endpoint: str,
        model: type[T] | None = None,
        skip_auth: bool = False,
        token: str | None = None,
        files: FilesTypes | None = None,
        **kwargs,
    ) -> T | dict[str, Any]:
        """
        发送异步 PUT 请求（v4.0.0）

        Args:
            endpoint: API端点
            model: 响应模型类
            skip_auth: 跳过认证中间件（不添加 Token）
            token: 使用自定义 Token（绕过中间件缓存）
            files: 文件上传（multipart/form-data）
            **kwargs: 其他请求参数

        Returns:
            解析后的响应数据

        Note:
            如果 json 参数是 Pydantic BaseModel 实例，会自动序列化为字典

        Example:
            >>> updated_user = await api.put("/users/1", json={"name": "Bob"}, model=UserResponse)
        """
        # 自动处理 Pydantic 模型序列化
        if "json" in kwargs and isinstance(kwargs["json"], BaseModel):
            kwargs["json"] = kwargs["json"].model_dump(
                mode="json", by_alias=True, exclude_none=True
            )

        # 传递认证控制参数
        if skip_auth:
            if "metadata" not in kwargs:
                kwargs["metadata"] = {}
            kwargs["metadata"]["skip_auth"] = True
        if token:
            if "metadata" not in kwargs:
                kwargs["metadata"] = {}
            kwargs["metadata"]["custom_token"] = token

        # 传递 files 参数
        if files is not None:
            kwargs["files"] = files

        url = self._build_url(endpoint)
        response = await self.http_client.put(url, **kwargs)
        return self._parse_response(response, model)

    async def delete(
        self,
        endpoint: str,
        model: type[T] | None = None,
        skip_auth: bool = False,
        token: str | None = None,
        **kwargs,
    ) -> T | dict[str, Any]:
        """
        发送异步 DELETE 请求（v4.0.0）

        Args:
            endpoint: API端点
            model: 响应模型类
            skip_auth: 跳过认证中间件（不添加 Token）
            token: 使用自定义 Token（绕过中间件缓存）
            **kwargs: 其他请求参数

        Returns:
            解析后的响应数据

        Example:
            >>> await api.delete("/users/1")
        """
        # 传递认证控制参数
        if skip_auth:
            if "metadata" not in kwargs:
                kwargs["metadata"] = {}
            kwargs["metadata"]["skip_auth"] = True
        if token:
            if "metadata" not in kwargs:
                kwargs["metadata"] = {}
            kwargs["metadata"]["custom_token"] = token

        url = self._build_url(endpoint)
        response = await self.http_client.delete(url, **kwargs)
        return self._parse_response(response, model)

    async def patch(
        self,
        endpoint: str,
        model: type[T] | None = None,
        skip_auth: bool = False,
        token: str | None = None,
        files: FilesTypes | None = None,
        **kwargs,
    ) -> T | dict[str, Any]:
        """
        发送异步 PATCH 请求（v4.0.0）

        Args:
            endpoint: API端点
            model: 响应模型类
            skip_auth: 跳过认证中间件（不添加 Token）
            token: 使用自定义 Token（绕过中间件缓存）
            files: 文件上传（multipart/form-data）
            **kwargs: 其他请求参数

        Returns:
            解析后的响应数据

        Note:
            如果 json 参数是 Pydantic BaseModel 实例，会自动序列化为字典

        Example:
            >>> updated_user = await api.patch("/users/1", json={"age": 30}, model=UserResponse)
        """
        # 自动处理 Pydantic 模型序列化
        if "json" in kwargs and isinstance(kwargs["json"], BaseModel):
            kwargs["json"] = kwargs["json"].model_dump(
                mode="json", by_alias=True, exclude_none=True
            )

        # 传递认证控制参数
        if skip_auth:
            if "metadata" not in kwargs:
                kwargs["metadata"] = {}
            kwargs["metadata"]["skip_auth"] = True
        if token:
            if "metadata" not in kwargs:
                kwargs["metadata"] = {}
            kwargs["metadata"]["custom_token"] = token

        # 传递 files 参数
        if files is not None:
            kwargs["files"] = files

        url = self._build_url(endpoint)
        response = await self.http_client.patch(url, **kwargs)
        return self._parse_response(response, model)


__all__ = [
    "AsyncBaseAPI",
    "BusinessError",
]
