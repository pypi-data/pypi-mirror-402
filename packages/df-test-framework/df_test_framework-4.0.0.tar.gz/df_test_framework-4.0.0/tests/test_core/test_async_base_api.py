"""测试 AsyncBaseAPI 核心功能（v4.0.0）

验证异步 API 基类的响应解析和业务错误处理
"""

from typing import Any
from unittest.mock import Mock

import pytest
from pydantic import BaseModel, Field

from df_test_framework.capabilities.clients.http.core import Response
from df_test_framework.capabilities.clients.http.rest.httpx.async_base_api import (
    AsyncBaseAPI,
    BusinessError,
)


class MockAsyncHttpClient:
    """模拟 AsyncHttpClient"""

    def __init__(self):
        self.last_url = ""
        self.last_kwargs = {}
        self.mock_response = None

    async def get(self, url: str, **kwargs) -> Response:
        self.last_url = url
        self.last_kwargs = kwargs
        return self.mock_response

    async def post(self, url: str, **kwargs) -> Response:
        self.last_url = url
        self.last_kwargs = kwargs
        return self.mock_response

    async def put(self, url: str, **kwargs) -> Response:
        self.last_url = url
        self.last_kwargs = kwargs
        return self.mock_response

    async def delete(self, url: str, **kwargs) -> Response:
        self.last_url = url
        self.last_kwargs = kwargs
        return self.mock_response

    async def patch(self, url: str, **kwargs) -> Response:
        self.last_url = url
        self.last_kwargs = kwargs
        return self.mock_response


def create_mock_response(
    status_code: int = 200, json_data: dict[str, Any] | None = None
) -> Response:
    """创建 mock Response"""
    mock_response = Mock(spec=Response)
    mock_response.status_code = status_code
    mock_response.body = str(json_data) if json_data else ""

    def mock_json():
        return json_data

    mock_response.json = mock_json
    return mock_response


class TestAsyncBaseAPIBusinessError:
    """测试业务错误处理"""

    def test_default_no_check(self):
        """测试默认不检查业务错误"""
        http_client = MockAsyncHttpClient()
        api = AsyncBaseAPI(http_client)

        # 默认 _check_business_error 不做任何检查
        response_data = {"code": 500, "message": "业务错误"}
        api._check_business_error(response_data)  # 不应抛出异常

    def test_custom_check_success_field(self):
        """测试自定义检查 success 字段"""

        class CustomAPI(AsyncBaseAPI):
            def _check_business_error(self, response_data):
                if not response_data.get("success", True):
                    raise BusinessError(
                        message=response_data.get("message", "未知错误"),
                        code=response_data.get("code"),
                        data=response_data,
                    )

        http_client = MockAsyncHttpClient()
        api = CustomAPI(http_client)

        # 成功情况
        api._check_business_error({"success": True, "data": {}})

        # 失败情况
        with pytest.raises(BusinessError) as exc_info:
            api._check_business_error({"success": False, "code": 1001, "message": "参数错误"})

        assert exc_info.value.code == 1001
        assert exc_info.value.message == "参数错误"

    def test_custom_check_code_field(self):
        """测试自定义检查 code 字段"""

        class CustomAPI(AsyncBaseAPI):
            def _check_business_error(self, response_data):
                code = response_data.get("code", 200)
                if code not in [200, 0]:
                    raise BusinessError(
                        message=response_data.get("message", "未知错误"),
                        code=code,
                        data=response_data,
                    )

        http_client = MockAsyncHttpClient()
        api = CustomAPI(http_client)

        # 成功情况
        api._check_business_error({"code": 200, "data": {}})
        api._check_business_error({"code": 0, "data": {}})

        # 失败情况
        with pytest.raises(BusinessError) as exc_info:
            api._check_business_error({"code": 500, "message": "服务器错误"})

        assert exc_info.value.code == 500
        assert exc_info.value.message == "服务器错误"

    def test_business_error_str(self):
        """测试 BusinessError 字符串表示"""
        error1 = BusinessError("错误消息")
        assert str(error1) == "[业务错误] 错误消息"

        error2 = BusinessError("错误消息", code=1001)
        assert str(error2) == "[业务错误 1001] 错误消息"


class TestAsyncBaseAPIResponseParsing:
    """测试响应解析"""

    def test_parse_response_dict(self):
        """测试解析响应为字典"""
        http_client = MockAsyncHttpClient()
        api = AsyncBaseAPI(http_client)

        response = create_mock_response(200, {"id": 1, "name": "Alice"})
        result = api._parse_response(response)

        assert result == {"id": 1, "name": "Alice"}

    def test_parse_response_model(self):
        """测试解析响应为 Pydantic 模型"""

        class UserResponse(BaseModel):
            id: int
            name: str

        http_client = MockAsyncHttpClient()
        api = AsyncBaseAPI(http_client)

        response = create_mock_response(200, {"id": 1, "name": "Alice"})
        result = api._parse_response(response, model=UserResponse)

        assert isinstance(result, UserResponse)
        assert result.id == 1
        assert result.name == "Alice"

    def test_parse_response_http_error(self):
        """测试 HTTP 错误时抛出异常"""
        http_client = MockAsyncHttpClient()
        api = AsyncBaseAPI(http_client)

        response = create_mock_response(404, {"error": "Not Found"})

        with pytest.raises(Exception) as exc_info:
            api._parse_response(response)

        assert "HTTP 404" in str(exc_info.value)

    def test_parse_response_skip_http_error_check(self):
        """测试跳过 HTTP 错误检查"""
        http_client = MockAsyncHttpClient()
        api = AsyncBaseAPI(http_client)

        response = create_mock_response(404, {"error": "Not Found"})
        result = api._parse_response(response, raise_for_status=False)

        assert result == {"error": "Not Found"}


class TestAsyncBaseAPIBuildUrl:
    """测试 URL 构建"""

    def test_build_url_with_slash(self):
        """测试以 / 开头的 endpoint"""
        http_client = MockAsyncHttpClient()
        api = AsyncBaseAPI(http_client)

        url = api._build_url("/users")
        assert url == "/users"

    def test_build_url_without_slash(self):
        """测试不以 / 开头的 endpoint（自动补全）"""
        http_client = MockAsyncHttpClient()
        api = AsyncBaseAPI(http_client)

        url = api._build_url("users")
        assert url == "/users"


class TestAsyncBaseAPIHttpMethods:
    """测试异步 HTTP 方法"""

    @pytest.fixture
    def api_with_mock_client(self):
        """创建带 mock 客户端的 API"""
        http_client = MockAsyncHttpClient()
        api = AsyncBaseAPI(http_client)
        return api, http_client

    @pytest.mark.asyncio
    async def test_get(self, api_with_mock_client):
        """测试异步 GET 请求"""
        api, http_client = api_with_mock_client
        http_client.mock_response = create_mock_response(200, {"id": 1, "name": "Alice"})

        result = await api.get("/users/1")

        assert http_client.last_url == "/users/1"
        assert result == {"id": 1, "name": "Alice"}

    @pytest.mark.asyncio
    async def test_get_with_params(self, api_with_mock_client):
        """测试带参数的 GET 请求"""
        api, http_client = api_with_mock_client
        http_client.mock_response = create_mock_response(200, {"users": []})

        await api.get("/users", params={"page": 1, "size": 10})

        assert http_client.last_kwargs["params"] == {"page": 1, "size": 10}

    @pytest.mark.asyncio
    async def test_get_with_pydantic_params(self, api_with_mock_client):
        """测试 Pydantic 模型作为查询参数"""

        class QueryParams(BaseModel):
            model_config = {"populate_by_name": True}  # 允许通过字段名或别名设置值

            user_id: str = Field(alias="userId")
            status: str | None = None

        api, http_client = api_with_mock_client
        http_client.mock_response = create_mock_response(200, {"users": []})

        params = QueryParams(user_id="user_001")
        await api.get("/users", params=params)

        # 验证 Pydantic 模型被正确序列化（使用别名，排除 None）
        assert http_client.last_kwargs["params"] == {"userId": "user_001"}

    @pytest.mark.asyncio
    async def test_post(self, api_with_mock_client):
        """测试异步 POST 请求"""
        api, http_client = api_with_mock_client
        http_client.mock_response = create_mock_response(201, {"id": 1, "name": "Alice"})

        result = await api.post("/users", json={"name": "Alice"})

        assert http_client.last_url == "/users"
        assert result == {"id": 1, "name": "Alice"}

    @pytest.mark.asyncio
    async def test_post_with_pydantic_json(self, api_with_mock_client):
        """测试 Pydantic 模型作为 JSON body"""

        class CreateUserRequest(BaseModel):
            name: str
            age: int | None = None

        api, http_client = api_with_mock_client
        http_client.mock_response = create_mock_response(201, {"id": 1})

        request = CreateUserRequest(name="Alice")
        await api.post("/users", json=request)

        # 验证 Pydantic 模型被正确序列化
        assert http_client.last_kwargs["json"] == {"name": "Alice"}

    @pytest.mark.asyncio
    async def test_put(self, api_with_mock_client):
        """测试异步 PUT 请求"""
        api, http_client = api_with_mock_client
        http_client.mock_response = create_mock_response(200, {"id": 1, "name": "Bob"})

        result = await api.put("/users/1", json={"name": "Bob"})

        assert http_client.last_url == "/users/1"
        assert result == {"id": 1, "name": "Bob"}

    @pytest.mark.asyncio
    async def test_delete(self, api_with_mock_client):
        """测试异步 DELETE 请求"""
        api, http_client = api_with_mock_client
        http_client.mock_response = create_mock_response(200, {"success": True})

        result = await api.delete("/users/1")

        assert http_client.last_url == "/users/1"
        assert result == {"success": True}

    @pytest.mark.asyncio
    async def test_patch(self, api_with_mock_client):
        """测试异步 PATCH 请求"""
        api, http_client = api_with_mock_client
        http_client.mock_response = create_mock_response(200, {"id": 1, "age": 30})

        result = await api.patch("/users/1", json={"age": 30})

        assert http_client.last_url == "/users/1"
        assert result == {"id": 1, "age": 30}


class TestAsyncBaseAPIAuthControl:
    """测试认证控制参数"""

    @pytest.fixture
    def api_with_mock_client(self):
        """创建带 mock 客户端的 API"""
        http_client = MockAsyncHttpClient()
        api = AsyncBaseAPI(http_client)
        return api, http_client

    @pytest.mark.asyncio
    async def test_skip_auth_get(self, api_with_mock_client):
        """测试 GET 请求的 skip_auth 参数"""
        api, http_client = api_with_mock_client
        http_client.mock_response = create_mock_response(200, {})

        await api.get("/users", skip_auth=True)

        assert http_client.last_kwargs["metadata"]["skip_auth"] is True

    @pytest.mark.asyncio
    async def test_custom_token_get(self, api_with_mock_client):
        """测试 GET 请求的 token 参数"""
        api, http_client = api_with_mock_client
        http_client.mock_response = create_mock_response(200, {})

        await api.get("/users", token="custom_token_123")

        assert http_client.last_kwargs["metadata"]["custom_token"] == "custom_token_123"

    @pytest.mark.asyncio
    async def test_skip_auth_post(self, api_with_mock_client):
        """测试 POST 请求的 skip_auth 参数"""
        api, http_client = api_with_mock_client
        http_client.mock_response = create_mock_response(200, {})

        await api.post("/users", skip_auth=True)

        assert http_client.last_kwargs["metadata"]["skip_auth"] is True

    @pytest.mark.asyncio
    async def test_custom_token_post(self, api_with_mock_client):
        """测试 POST 请求的 token 参数"""
        api, http_client = api_with_mock_client
        http_client.mock_response = create_mock_response(200, {})

        await api.post("/users", token="custom_token_456")

        assert http_client.last_kwargs["metadata"]["custom_token"] == "custom_token_456"

    @pytest.mark.asyncio
    async def test_skip_auth_put(self, api_with_mock_client):
        """测试 PUT 请求的 skip_auth 参数"""
        api, http_client = api_with_mock_client
        http_client.mock_response = create_mock_response(200, {})

        await api.put("/users/1", skip_auth=True)

        assert http_client.last_kwargs["metadata"]["skip_auth"] is True

    @pytest.mark.asyncio
    async def test_skip_auth_delete(self, api_with_mock_client):
        """测试 DELETE 请求的 skip_auth 参数"""
        api, http_client = api_with_mock_client
        http_client.mock_response = create_mock_response(200, {})

        await api.delete("/users/1", skip_auth=True)

        assert http_client.last_kwargs["metadata"]["skip_auth"] is True

    @pytest.mark.asyncio
    async def test_skip_auth_patch(self, api_with_mock_client):
        """测试 PATCH 请求的 skip_auth 参数"""
        api, http_client = api_with_mock_client
        http_client.mock_response = create_mock_response(200, {})

        await api.patch("/users/1", skip_auth=True)

        assert http_client.last_kwargs["metadata"]["skip_auth"] is True


class TestAsyncBaseAPIFileUpload:
    """测试文件上传"""

    @pytest.fixture
    def api_with_mock_client(self):
        """创建带 mock 客户端的 API"""
        http_client = MockAsyncHttpClient()
        api = AsyncBaseAPI(http_client)
        return api, http_client

    @pytest.mark.asyncio
    async def test_post_with_files(self, api_with_mock_client):
        """测试 POST 请求的文件上传"""
        api, http_client = api_with_mock_client
        http_client.mock_response = create_mock_response(200, {"id": 1})

        files = {"file": ("test.txt", b"content", "text/plain")}
        await api.post("/upload", files=files)

        assert http_client.last_kwargs["files"] == files

    @pytest.mark.asyncio
    async def test_put_with_files(self, api_with_mock_client):
        """测试 PUT 请求的文件上传"""
        api, http_client = api_with_mock_client
        http_client.mock_response = create_mock_response(200, {"id": 1})

        files = {"file": ("test.txt", b"content", "text/plain")}
        await api.put("/upload/1", files=files)

        assert http_client.last_kwargs["files"] == files

    @pytest.mark.asyncio
    async def test_patch_with_files(self, api_with_mock_client):
        """测试 PATCH 请求的文件上传"""
        api, http_client = api_with_mock_client
        http_client.mock_response = create_mock_response(200, {"id": 1})

        files = {"file": ("test.txt", b"content", "text/plain")}
        await api.patch("/upload/1", files=files)

        assert http_client.last_kwargs["files"] == files


class TestAsyncBaseAPIModelValidation:
    """测试响应模型验证"""

    @pytest.mark.asyncio
    async def test_get_with_model(self):
        """测试 GET 请求返回 Pydantic 模型"""

        class UserResponse(BaseModel):
            id: int
            name: str
            email: str | None = None

        http_client = MockAsyncHttpClient()
        http_client.mock_response = create_mock_response(
            200, {"id": 1, "name": "Alice", "email": "alice@example.com"}
        )
        api = AsyncBaseAPI(http_client)

        result = await api.get("/users/1", model=UserResponse)

        assert isinstance(result, UserResponse)
        assert result.id == 1
        assert result.name == "Alice"
        assert result.email == "alice@example.com"

    @pytest.mark.asyncio
    async def test_post_with_model(self):
        """测试 POST 请求返回 Pydantic 模型"""

        class CreateUserResponse(BaseModel):
            id: int
            success: bool

        http_client = MockAsyncHttpClient()
        http_client.mock_response = create_mock_response(201, {"id": 1, "success": True})
        api = AsyncBaseAPI(http_client)

        result = await api.post("/users", json={"name": "Alice"}, model=CreateUserResponse)

        assert isinstance(result, CreateUserResponse)
        assert result.id == 1
        assert result.success is True
