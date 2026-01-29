# HTTP 客户端使用指南

> **最后更新**: 2026-01-16
> **适用版本**: v2.0.0+（同步 HttpClient），v3.8.0+（异步 AsyncHttpClient），v4.0.0+（推荐异步）

## 概述

本指南介绍 DF Test Framework 的 HTTP 客户端，包括同步和异步两种模式。

- **HttpClient**：同步 HTTP 客户端，简单易用，适合简单测试场景
- **AsyncHttpClient**：异步 HTTP 客户端，基于 httpx.AsyncClient，并发性能提升 10-30 倍

## 目录

- [快速开始](#快速开始)
- [HttpClient 同步客户端](#httpclient-同步客户端)
- [AsyncHttpClient 异步客户端（推荐）](#asynchttpclient-异步客户端推荐)
- [高级功能](#高级功能)
- [中间件系统](#中间件系统)
- [BaseAPI 封装模式](#baseapi-封装模式)
- [性能对比与最佳实践](#性能对比与最佳实践)
- [常见场景](#常见场景)

---

## 快速开始

### 同步方式（简单场景）

```python
from df_test_framework import HttpClient

# 创建客户端
client = HttpClient("https://api.example.com")

# 发起请求
response = client.get("/users/1")
assert response.status_code == 200
print(response.json())
```

### 异步方式（推荐）

```python
import asyncio
from df_test_framework import AsyncHttpClient

async def test_basic():
    # 使用 async with 自动管理资源
    async with AsyncHttpClient("https://api.example.com") as client:
        # 发起 GET 请求
        response = await client.get("/users/1")

        assert response.status_code == 200
        assert response.json_data["id"] == 1

# 运行异步测试
asyncio.run(test_basic())
```

---

## HttpClient 同步客户端

> **引入版本**: v2.0.0
> **稳定版本**: v3.0.0

### 基本使用

```python
from df_test_framework import HttpClient

# 创建客户端
client = HttpClient(
    base_url="https://api.example.com",
    timeout=30,                    # 超时时间（秒）
    headers={"X-API-Key": "xxx"},  # 默认请求头
    verify_ssl=True,               # SSL 证书验证
)
```

### HTTP 方法

```python
# GET 请求
response = client.get("/users")
response = client.get("/users", params={"page": 1, "size": 10})

# POST 请求
response = client.post("/users", json={"name": "Alice", "age": 30})

# PUT 请求
response = client.put("/users/1", json={"name": "Bob"})

# DELETE 请求
response = client.delete("/users/1")

# PATCH 请求
response = client.patch("/users/1", json={"age": 31})

# HEAD 请求（v3.20.0+）
response = client.head("/files/123")

# OPTIONS 请求（v3.20.0+）
response = client.options("/users")
```

### 认证 Token

```python
# 设置 Bearer Token
client.set_auth_token("your_token_here", token_type="Bearer")

# 后续所有请求自动携带 Authorization header
response = client.get("/protected/resource")
# Authorization: Bearer your_token_here
```

### 响应处理

```python
response = client.get("/users/1")

# 状态码
print(response.status_code)  # 200

# JSON 数据
data = response.json()
print(data["name"])

# 原始内容
print(response.content)  # bytes
print(response.text)      # str

# 响应头
print(response.headers["Content-Type"])
```

---

## AsyncHttpClient 异步客户端（推荐）

> **引入版本**: v3.8.0
> **稳定版本**: v3.10.0
> **重大优化**: v4.0.0（性能提升 30 倍）

### 为什么使用异步？

异步客户端在并发场景下性能显著提升：

| 场景 | 同步 HttpClient | 异步 AsyncHttpClient | 性能提升 |
|------|----------------|---------------------|---------|
| 单个请求 | 200ms | 200ms | 相同 |
| 100 个串行请求 | 20 秒 | 20 秒 | 相同 |
| **100 个并发请求** | 20 秒 | **0.5 秒** | **40 倍** |

### 基础使用

```python
import asyncio
from df_test_framework import AsyncHttpClient

async def test_basic():
    # 使用 async with 自动管理资源
    async with AsyncHttpClient("https://api.example.com") as client:
        # 发起 GET 请求
        response = await client.get("/users/1")

        assert response.status_code == 200
        assert response.json_data["id"] == 1

# 运行异步测试
asyncio.run(test_basic())
```

### pytest 异步测试

```python
import pytest
from df_test_framework import AsyncHttpClient

@pytest.mark.asyncio
async def test_with_pytest():
    """使用 pytest-asyncio 插件"""
    async with AsyncHttpClient("https://api.example.com") as client:
        response = await client.get("/users")
        assert response.status_code == 200
```

**pytest 配置**：

需要安装 `pytest-asyncio`：

```bash
uv pip install pytest-asyncio
```

配置 `pyproject.toml`：

```toml
[tool.pytest.ini_options]
markers = [
    "asyncio: 异步测试",
]
```

### HTTP 方法

```python
async with AsyncHttpClient("https://api.example.com") as client:
    # GET 请求
    response = await client.get("/users")
    response = await client.get("/users", params={"page": 1, "size": 10})

    # POST 请求
    response = await client.post("/users", json={"name": "Alice", "age": 30})

    # PUT 请求
    response = await client.put("/users/1", json={"name": "Bob"})

    # DELETE 请求
    response = await client.delete("/users/1")

    # PATCH 请求
    response = await client.patch("/users/1", json={"age": 31})
```

### 并发请求（核心优势）

**这是异步客户端的核心优势！**

```python
import asyncio
from df_test_framework import AsyncHttpClient

async def test_concurrent():
    async with AsyncHttpClient("https://api.example.com") as client:
        # 创建 100 个请求任务
        tasks = [
            client.get(f"/users/{i}")
            for i in range(1, 101)
        ]

        # 并发执行所有请求
        responses = await asyncio.gather(*tasks)

        # 验证所有响应
        assert len(responses) == 100
        for response in responses:
            assert response.status_code == 200

# 性能对比:
# - 同步 HttpClient: 100 * 200ms = 20 秒
# - 异步 AsyncHttpClient: ~500ms (40倍提升!)
```

### 配置选项

```python
from df_test_framework import AsyncHttpClient

async with AsyncHttpClient(
    base_url="https://api.example.com",
    timeout=60,                    # 超时时间（秒）
    headers={"X-API-Key": "xxx"},  # 默认请求头
    verify_ssl=True,               # SSL 证书验证
    max_connections=200,           # 最大并发连接数
    max_keepalive_connections=40,  # Keep-Alive 连接数
    http2=True,                    # 启用 HTTP/2（推荐）
) as client:
    response = await client.get("/users")
```

#### 配置优先级（v3.9.0+）

当同时提供构造函数参数和 `HTTPConfig` 时，遵循以下优先级：

**显式参数 > HTTPConfig > 默认值**

```python
from df_test_framework import AsyncHttpClient
from df_test_framework.infrastructure import HTTPConfig

# HTTPConfig 提供默认配置
config = HTTPConfig(
    base_url="https://default.example.com",
    timeout=30,
    verify_ssl=True,
    max_connections=100,
)

# 显式参数会覆盖 HTTPConfig 中的配置
async with AsyncHttpClient(
    base_url="https://override.example.com",  # 覆盖 config.base_url
    timeout=60,                                # 覆盖 config.timeout
    # verify_ssl 未指定，使用 config.verify_ssl = True
    # max_connections 未指定，使用 config.max_connections = 100
    config=config,
) as client:
    # 实际配置:
    # - base_url: "https://override.example.com" (显式参数)
    # - timeout: 60 (显式参数)
    # - verify_ssl: True (来自 HTTPConfig)
    # - max_connections: 100 (来自 HTTPConfig)
    response = await client.get("/users")
```

这种设计使得：
- **HTTPConfig** 可以作为项目级别的默认配置
- **显式参数** 可以在特定场景下覆盖默认配置
- 测试代码更灵活，减少重复配置

### 认证 Token

```python
async with AsyncHttpClient("https://api.example.com") as client:
    # 设置 Bearer Token
    client.set_auth_token("your_token_here", token_type="Bearer")

    # 后续所有请求自动携带 Authorization header
    response = await client.get("/protected/resource")
    # Authorization: Bearer your_token_here
```

### Pydantic 模型支持

```python
from pydantic import BaseModel
from df_test_framework import AsyncHttpClient

class User(BaseModel):
    name: str
    age: int
    email: str

async with AsyncHttpClient("https://api.example.com") as client:
    # Pydantic 模型自动序列化
    user = User(name="Alice", age=30, email="alice@example.com")
    response = await client.post("/users", json=user)

    # 等价于:
    # response = await client.post("/users", json={
    #     "name": "Alice",
    #     "age": 30,
    #     "email": "alice@example.com"
    # })
```

---

## 高级功能

> **引入版本**: v3.20.0
> **文档来源**: 整合自 httpx_advanced_usage.md

### 文件上传（multipart/form-data）

#### 基本文件上传

```python
# 方式1: 简单 bytes
response = client.post("/upload", files={"file": b"file_content"})

# 方式2: 带文件名
response = client.post("/upload", files={
    "file": ("filename.txt", b"file_content")
})

# 方式3: 带文件名和 MIME 类型
response = client.post("/upload", files={
    "image": ("photo.jpg", image_bytes, "image/jpeg")
})

# 方式4: 带自定义 headers
response = client.post("/upload", files={
    "file": ("doc.pdf", pdf_bytes, "application/pdf", {"X-Custom": "value"})
})
```

#### 从文件读取

```python
from pathlib import Path

# 方式1: 读取到内存
with open("photo.jpg", "rb") as f:
    response = client.post("/upload", files={
        "image": ("photo.jpg", f.read(), "image/jpeg")
    })

# 方式2: 流式读取（大文件推荐）
with open("large_file.zip", "rb") as f:
    response = client.post("/upload", files={
        "file": ("large_file.zip", f, "application/zip")
    })
```

### 混合表单（文字+文件）

当需要同时发送表单字段和文件时：

```python
# 表单字段：filename 设为 None
# 文件字段：filename 为实际文件名

response = client.post("/templates", files={
    # 表单字段（filename=None 表示这是普通字段，不是文件）
    "name": (None, "测试模板"),
    "description": (None, "这是模板描述"),
    "price": (None, "99.99"),

    # 文件字段
    "cover_image": ("cover.jpg", image_bytes, "image/jpeg"),
    "attachment": ("doc.pdf", pdf_bytes, "application/pdf"),
})
```

#### 编码注意事项

```python
# 中文字段需要编码为 bytes
response = client.post("/templates", files={
    "name": (None, "测试名称".encode("utf-8"), None),
    "price": (None, b"100.00", None),  # 数字也需要是 bytes
    "image": ("photo.jpg", image_bytes, "image/jpeg"),
})
```

### 多文件上传（同名字段）

当 API 需要同一个字段名上传多个文件时，使用 list 格式：

```python
# 使用 list 格式（而非 dict）支持重复的字段名
response = client.post("/batch-upload", files=[
    ("files", ("doc1.pdf", pdf1_bytes, "application/pdf")),
    ("files", ("doc2.pdf", pdf2_bytes, "application/pdf")),
    ("files", ("doc3.pdf", pdf3_bytes, "application/pdf")),
])
```

#### 混合使用

```python
# 可以混合不同字段
response = client.post("/batch-upload", files=[
    ("title", (None, b"Batch Upload", None)),
    ("files", ("doc1.pdf", pdf1_bytes, "application/pdf")),
    ("files", ("doc2.pdf", pdf2_bytes, "application/pdf")),
    ("tags", (None, b"tag1", None)),
    ("tags", (None, b"tag2", None)),
])
```

### 二进制数据上传（raw body）

当需要发送原始二进制数据（非 multipart）时，使用 `content` 参数：

#### application/octet-stream

```python
binary_data = b"\x00\x01\x02\x03\x04\x05"

response = client.post(
    "/upload/binary",
    content=binary_data,
    headers={"Content-Type": "application/octet-stream"}
)
```

#### text/plain

```python
text_data = "plain text content"

response = client.post(
    "/webhook",
    content=text_data,
    headers={"Content-Type": "text/plain; charset=utf-8"}
)
```

#### 自定义 Content-Type

```python
# XML
xml_data = '<?xml version="1.0"?><root><item>value</item></root>'
response = client.post(
    "/api/xml",
    content=xml_data,
    headers={"Content-Type": "application/xml"}
)

# GraphQL（非 JSON 格式）
graphql_query = 'query { users { id name } }'
response = client.post(
    "/graphql",
    content=graphql_query,
    headers={"Content-Type": "application/graphql"}
)
```

### 流式上传（大文件）

对于大文件，避免一次性加载到内存：

```python
def file_generator():
    """生成器函数，逐块读取文件"""
    with open("large_file.zip", "rb") as f:
        while chunk := f.read(8192):  # 8KB 块
            yield chunk

# 流式上传
response = client.post(
    "/upload/stream",
    content=file_generator(),
    headers={
        "Content-Type": "application/octet-stream",
        "Transfer-Encoding": "chunked",
    }
)
```

#### 异步流式上传

```python
import httpx

async def async_file_generator():
    async with aiofiles.open("large_file.zip", "rb") as f:
        while chunk := await f.read(8192):
            yield chunk

async with AsyncHttpClient("https://api.example.com") as client:
    response = await client.post(
        "/upload/stream",
        content=async_file_generator(),
    )
```

### HEAD 请求（获取资源元信息）

```python
# 检查文件是否存在，获取大小
response = client.head("/files/123")

if response.status_code == 200:
    content_length = response.headers.get("Content-Length")
    content_type = response.headers.get("Content-Type")
    last_modified = response.headers.get("Last-Modified")
    print(f"文件大小: {content_length} bytes")
    print(f"类型: {content_type}")
    print(f"最后修改: {last_modified}")
elif response.status_code == 404:
    print("文件不存在")
```

### OPTIONS 请求（CORS 预检/API 发现）

```python
# 获取 API 支持的方法
response = client.options("/users")

allowed_methods = response.headers.get("Allow")
print(f"支持的方法: {allowed_methods}")  # GET, POST, PUT, DELETE

# CORS 相关
access_control_methods = response.headers.get("Access-Control-Allow-Methods")
access_control_origin = response.headers.get("Access-Control-Allow-Origin")
```

---

## 中间件系统

> **引入版本**: v3.14.0（洋葱模型）
> **稳定版本**: v3.16.0（完全移除 Interceptor）
> **配置化**: v3.36.0（支持 HTTPConfig 配置）

中间件系统采用**洋葱模型**架构，提供灵活的请求/响应处理能力。

### 洋葱模型

```
Request → Middleware 1 (before) →
            Middleware 2 (before) →
              Middleware 3 (before) →
                [HTTP 请求]
              Middleware 3 (after) ←
            Middleware 2 (after) ←
          Middleware 1 (after) ← Response
```

### 使用内置中间件（v3.14.0+）

```python
from df_test_framework import (
    HttpClient,
    SignatureMiddleware,
    BearerTokenMiddleware,
    RetryMiddleware,
    LoggingMiddleware,
)

# 创建客户端
client = HttpClient(base_url="https://api.example.com")

# 链式添加中间件
client.use(LoggingMiddleware(priority=100))
client.use(RetryMiddleware(max_attempts=3, priority=20))
client.use(SignatureMiddleware(
    algorithm="md5",
    secret="my_secret",
    header_name="X-Sign",
    priority=10,
))

# 发送请求（中间件自动生效）
response = client.get("/users")
```

### 构造时传入中间件

```python
client = HttpClient(
    base_url="https://api.example.com",
    middlewares=[
        SignatureMiddleware(algorithm="md5", secret="my_secret", priority=10),
        BearerTokenMiddleware(token="my_token", priority=20),
        LoggingMiddleware(priority=100),
    ]
)

response = client.post("/api/users", json={"name": "Alice"})
```

### 异步客户端的中间件支持

```python
from df_test_framework import AsyncHttpClient

async with AsyncHttpClient(
    "https://api.example.com",
    middlewares=[
        SignatureMiddleware(algorithm="md5", secret="my_secret", priority=10),
        BearerTokenMiddleware(token="my_token", priority=20),
        LoggingMiddleware(priority=100),
    ]
) as client:
    response = await client.get("/api/users")
```

### 配置化中间件（v3.16.0+）

```python
from df_test_framework import AsyncHttpClient
from df_test_framework.infrastructure.config import (
    HTTPConfig,
    SignatureMiddlewareConfig,
    SignatureAlgorithm,
)

# 使用 HTTPConfig 配置中间件
config = HTTPConfig(
    base_url="https://api.example.com",
    timeout=60,
    middlewares=[
        # 签名中间件配置（支持路径过滤）
        SignatureMiddlewareConfig(
            algorithm=SignatureAlgorithm.MD5,
            secret="my_secret",
            header="X-Sign",
            include_paths=["/api/**"],  # 只对 /api/** 路径生效
            priority=10,
        )
    ]
)

async with AsyncHttpClient(config=config) as client:
    # /api/** 路径会自动签名
    response = await client.post("/api/users", json={"name": "Alice"})

    # /other/** 路径不会签名
    response = await client.get("/other/health")
```

### 内置中间件列表

| 中间件 | 功能 | 优先级建议 | 版本 |
|--------|------|-----------|------|
| `SignatureMiddleware` | 请求签名（MD5/SHA256/HMAC） | 10 | v3.14.0+ |
| `BearerTokenMiddleware` | Bearer Token 认证 | 20 | v3.14.0+ |
| `RetryMiddleware` | 请求失败自动重试 | 30 | v3.14.0+ |
| `LoggingMiddleware` | 请求/响应日志 | 100 | v3.14.0+ |
| `HttpEventPublisherMiddleware` | 发布 HTTP 事件到 EventBus | 1000 | v3.22.0+ |

**优先级规则**：数值越小优先级越高（越靠近 HTTP 请求核心）

### 请求级认证控制（v3.19.0+）

```python
# 跳过认证（某些接口不需要 Token）
response = client.get("/public/info", skip_auth=True)

# 使用自定义 Token（临时使用其他账号）
response = client.get("/users/profile", token="custom_token_here")

# 清除 Token 缓存（完整认证流程测试）
client.clear_auth_cache()
```

更多中间件使用细节请参考：[中间件使用指南](./middleware_guide.md)

---

## BaseAPI 封装模式

> **引入版本**: v3.0.0
> **简化重构**: v3.3.0
> **高级功能**: v3.19.0（skip_auth/token）、v3.20.0（files/head/options）

BaseAPI 提供了一种标准的 API 封装模式，用于组织和管理 API 调用。

### 基本使用

```python
from df_test_framework import BaseAPI, HttpClient

class UserAPI(BaseAPI):
    """用户 API 封装"""

    def get_user(self, user_id: int) -> dict:
        """获取用户信息"""
        response = self.http_client.get(f"/users/{user_id}")
        return response.json()

    def create_user(self, name: str, email: str) -> dict:
        """创建用户"""
        response = self.http_client.post("/users", json={
            "name": name,
            "email": email
        })
        return response.json()

    def update_user(self, user_id: int, **kwargs) -> dict:
        """更新用户信息"""
        response = self.http_client.put(f"/users/{user_id}", json=kwargs)
        return response.json()

    def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        response = self.http_client.delete(f"/users/{user_id}")
        return response.status_code == 204

# 使用
client = HttpClient("https://api.example.com")
user_api = UserAPI(client)

# 调用 API
user = user_api.get_user(1)
print(user["name"])

new_user = user_api.create_user("Alice", "alice@example.com")
print(new_user["id"])
```

### Pydantic 模型解析

```python
from pydantic import BaseModel
from df_test_framework import BaseAPI

class User(BaseModel):
    id: int
    name: str
    email: str

class UserAPI(BaseAPI):
    def get_user(self, user_id: int) -> User:
        """获取用户信息，返回 Pydantic 模型"""
        response = self.http_client.get(f"/users/{user_id}")
        # BaseAPI 提供的 _parse_response 方法自动解析
        return self._parse_response(response, model=User)

    def list_users(self) -> list[User]:
        """获取用户列表"""
        response = self.http_client.get("/users")
        data = response.json()
        # 手动解析列表
        return [User(**item) for item in data["users"]]

# 使用
user_api = UserAPI(client)
user = user_api.get_user(1)  # 返回 User 对象
print(user.name)  # 直接访问属性
```

### 业务错误处理

```python
from df_test_framework import BaseAPI, BusinessError

class MyAPI(BaseAPI):
    """自定义 API 基类"""

    def _check_business_error(self, response_data: dict) -> None:
        """重写业务错误检查（统一响应格式）"""
        if not response_data.get("success", True):
            raise BusinessError(
                message=response_data.get("message", "未知错误"),
                code=response_data.get("code"),
                data=response_data
            )

class UserAPI(MyAPI):
    def get_user(self, user_id: int) -> dict:
        response = self.http_client.get(f"/users/{user_id}")
        # 自动检查业务错误
        return self._parse_response(response, check_business_error=True)

# 使用
try:
    user = user_api.get_user(999)  # 不存在的用户
except BusinessError as e:
    print(f"业务错误: {e.message}")
    print(f"错误码: {e.code}")
```

### 文件上传封装（v3.20.0+）

```python
class TemplateAPI(BaseAPI):
    def upload_template(
        self,
        name: str,
        description: str,
        cover_image: bytes,
        attachment: bytes | None = None
    ) -> dict:
        """上传模板"""
        files = {
            # 表单字段
            "name": (None, name.encode("utf-8"), None),
            "description": (None, description.encode("utf-8"), None),

            # 文件字段
            "cover_image": ("cover.jpg", cover_image, "image/jpeg"),
        }

        # 可选附件
        if attachment:
            files["attachment"] = ("doc.pdf", attachment, "application/pdf")

        response = self.http_client.post("/templates", files=files)
        return response.json()

# 使用
template_api = TemplateAPI(client)
with open("cover.jpg", "rb") as f:
    cover_bytes = f.read()

result = template_api.upload_template(
    name="测试模板",
    description="这是测试模板",
    cover_image=cover_bytes
)
```

### 资源检查封装（v3.20.0+）

```python
class FileAPI(BaseAPI):
    def file_exists(self, file_id: str) -> bool:
        """检查文件是否存在"""
        response = self.http_client.head(f"/files/{file_id}")
        return response.status_code == 200

    def get_file_info(self, file_id: str) -> dict:
        """获取文件元信息（不下载文件内容）"""
        response = self.http_client.head(f"/files/{file_id}")
        if response.status_code == 404:
            raise ValueError(f"文件 {file_id} 不存在")

        return {
            "size": int(response.headers.get("Content-Length", 0)),
            "type": response.headers.get("Content-Type"),
            "last_modified": response.headers.get("Last-Modified"),
        }

# 使用
file_api = FileAPI(client)
if file_api.file_exists("123"):
    info = file_api.get_file_info("123")
    print(f"文件大小: {info['size']} bytes")
```

---

## 性能对比与最佳实践

### 性能对比表

| 特性 | HttpClient | AsyncHttpClient |
|------|-----------|-----------------|
| 语法 | 同步 | async/await |
| 单个请求性能 | 200ms | 200ms（相同） |
| 100 个串行请求 | 20 秒 | 20 秒（相同） |
| 100 个并发请求 | 20 秒 | 0.5 秒（**40x**） |
| 中间件支持 | ✅ | ✅（完全兼容） |
| Pydantic 支持 | ✅ | ✅ |
| HTTP/2 支持 | ❌ | ✅ |
| 连接池 | ❌ | ✅ |
| 适用场景 | 简单测试 | 并发测试、压力测试 |

### 最佳实践

#### 1. 控制并发数

```python
import asyncio
from df_test_framework import AsyncHttpClient

async def controlled_concurrency():
    """使用 Semaphore 控制并发数"""
    async with AsyncHttpClient("https://api.example.com") as client:
        # 最多同时 10 个并发请求
        semaphore = asyncio.Semaphore(10)

        async def fetch_with_semaphore(user_id):
            async with semaphore:
                return await client.get(f"/users/{user_id}")

        # 创建 100 个任务，但最多同时 10 个
        tasks = [fetch_with_semaphore(i) for i in range(100)]
        responses = await asyncio.gather(*tasks)

        print(f"完成 {len(responses)} 个请求")

asyncio.run(controlled_concurrency())
```

#### 2. 连接池配置

```python
# 高并发场景：增大连接池
async with AsyncHttpClient(
    "https://api.example.com",
    max_connections=500,           # 最大连接数
    max_keepalive_connections=100, # Keep-Alive 连接数
) as client:
    # 可以支持更高的并发
    tasks = [client.get(f"/users/{i}") for i in range(500)]
    responses = await asyncio.gather(*tasks)
```

#### 3. HTTP/2 优势

```python
# 启用 HTTP/2（默认已启用）
async with AsyncHttpClient(
    "https://api.example.com",
    http2=True,  # 启用 HTTP/2
) as client:
    # HTTP/2 优势:
    # 1. 多路复用（一个连接多个请求）
    # 2. 头部压缩（减少传输量）
    # 3. 服务器推送
    # 4. 二进制协议（更高效）

    tasks = [client.get(f"/users/{i}") for i in range(100)]
    responses = await asyncio.gather(*tasks)
```

#### 4. 复用客户端实例

```python
# ❌ 错误：每次请求创建新客户端
async def bad_example():
    for i in range(100):
        async with AsyncHttpClient("https://api.example.com") as client:
            await client.get(f"/users/{i}")

# ✅ 正确：复用客户端实例
async def good_example():
    async with AsyncHttpClient("https://api.example.com") as client:
        tasks = [client.get(f"/users/{i}") for i in range(100)]
        await asyncio.gather(*tasks)
```

#### 5. 资源管理

```python
# ✅ 推荐：使用 async with（自动关闭）
async def recommended():
    async with AsyncHttpClient("https://api.example.com") as client:
        await client.get("/users")
    # 自动调用 client.close()

# ⚠️ 手动管理（需要显式关闭）
async def manual():
    client = AsyncHttpClient("https://api.example.com")
    try:
        await client.get("/users")
    finally:
        await client.close()  # 必须手动关闭
```

---

## 常见场景

### 场景 1: 批量创建数据

```python
import asyncio
from df_test_framework import AsyncHttpClient

async def batch_create_users():
    """批量创建 1000 个用户"""
    async with AsyncHttpClient("https://api.example.com") as client:
        # 准备 1000 个创建任务
        tasks = [
            client.post("/users", json={"name": f"User_{i}", "age": 20 + i % 50})
            for i in range(1000)
        ]

        # 并发执行（分批控制并发数）
        batch_size = 50
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            responses = await asyncio.gather(*batch)
            print(f"批次 {i//batch_size + 1}: 创建 {len(responses)} 个用户")

asyncio.run(batch_create_users())
```

### 场景 2: 压力测试

```python
import asyncio
import time
from df_test_framework import AsyncHttpClient

async def stress_test(qps: int, duration_seconds: int):
    """压力测试

    Args:
        qps: 每秒请求数
        duration_seconds: 持续时间（秒）
    """
    async with AsyncHttpClient("https://api.example.com") as client:
        start_time = time.time()
        total_requests = 0
        total_errors = 0

        while time.time() - start_time < duration_seconds:
            # 每秒发送 qps 个请求
            tasks = [client.get("/health") for _ in range(qps)]

            try:
                responses = await asyncio.gather(*tasks, return_exceptions=True)

                # 统计结果
                for response in responses:
                    total_requests += 1
                    if isinstance(response, Exception) or response.status_code != 200:
                        total_errors += 1

            except Exception as e:
                print(f"批次失败: {e}")

            # 等待 1 秒（维持 QPS）
            await asyncio.sleep(1)

        # 输出结果
        print(f"总请求: {total_requests}")
        print(f"失败数: {total_errors}")
        print(f"成功率: {(total_requests - total_errors) / total_requests * 100:.2f}%")

# 执行: 100 QPS，持续 60 秒
asyncio.run(stress_test(qps=100, duration_seconds=60))
```

### 场景 3: 依赖接口调用

```python
import asyncio
from df_test_framework import AsyncHttpClient

async def create_user_with_posts():
    """创建用户并发布 10 篇文章"""
    async with AsyncHttpClient("https://api.example.com") as client:
        # 1. 创建用户
        user_response = await client.post("/users", json={"name": "Alice"})
        user_id = user_response.json_data["id"]

        # 2. 并发发布 10 篇文章
        post_tasks = [
            client.post("/posts", json={
                "user_id": user_id,
                "title": f"Post {i}",
                "content": f"Content {i}"
            })
            for i in range(10)
        ]

        post_responses = await asyncio.gather(*post_tasks)

        print(f"用户 {user_id} 发布了 {len(post_responses)} 篇文章")

asyncio.run(create_user_with_posts())
```

### 场景 4: 错误处理

```python
import asyncio
import httpx
from df_test_framework import AsyncHttpClient

async def handle_errors():
    """处理各种错误情况"""
    async with AsyncHttpClient("https://api.example.com", timeout=5) as client:
        try:
            response = await client.get("/users/999")

            # 检查 HTTP 状态码
            if response.status_code == 404:
                print("用户不存在")
            elif response.status_code == 500:
                print("服务器错误")

        except httpx.TimeoutException:
            print("请求超时")

        except httpx.NetworkError as e:
            print(f"网络错误: {e}")

        except httpx.HTTPError as e:
            print(f"HTTP 错误: {e}")

        except Exception as e:
            print(f"未知错误: {e}")

asyncio.run(handle_errors())
```

### 场景 5: 配置化中间件（v3.16.0+）

```python
from df_test_framework import AsyncHttpClient
from df_test_framework.infrastructure.config import (
    HTTPConfig,
    SignatureMiddlewareConfig,
    SignatureAlgorithm,
)

# 使用 HTTPConfig 配置中间件
config = HTTPConfig(
    base_url="https://api.example.com",
    timeout=60,
    middlewares=[
        # 签名中间件配置（支持路径过滤）
        SignatureMiddlewareConfig(
            algorithm=SignatureAlgorithm.MD5,
            secret="my_secret",
            header="X-Sign",
            include_paths=["/api/**"],  # 只对 /api/** 路径生效
            priority=10,
        )
    ]
)

async with AsyncHttpClient(config=config) as client:
    # /api/** 路径会自动签名
    response = await client.post("/api/users", json={"name": "Alice"})

    # /other/** 路径不会签名
    response = await client.get("/other/health")
```

---

## 注意事项

### 1. 必须使用 async/await（异步客户端）

```python
# ❌ 错误：忘记 await
async def wrong():
    async with AsyncHttpClient("https://api.example.com") as client:
        response = client.get("/users")  # 返回 coroutine，不是 Response
        print(response.status_code)      # AttributeError

# ✅ 正确
async def correct():
    async with AsyncHttpClient("https://api.example.com") as client:
        response = await client.get("/users")  # await 等待结果
        print(response.status_code)            # OK
```

### 2. 资源管理

```python
# ✅ 推荐：使用 async with（自动关闭）
async def recommended():
    async with AsyncHttpClient("https://api.example.com") as client:
        await client.get("/users")
    # 自动调用 client.close()

# ⚠️ 手动管理（需要显式关闭）
async def manual():
    client = AsyncHttpClient("https://api.example.com")
    try:
        await client.get("/users")
    finally:
        await client.close()  # 必须手动关闭
```

### 3. 同步 vs 异步选择

```python
# ✅ 简单测试：使用同步客户端
def test_simple():
    client = HttpClient("https://api.example.com")
    response = client.get("/users/1")
    assert response.status_code == 200

# ✅ 并发测试：使用异步客户端
@pytest.mark.asyncio
async def test_concurrent():
    async with AsyncHttpClient("https://api.example.com") as client:
        tasks = [client.get(f"/users/{i}") for i in range(100)]
        responses = await asyncio.gather(*tasks)
        assert len(responses) == 100
```

---

## 相关文档

- [v4.0 架构总览](../architecture/ARCHITECTURE_V4.0.md) - HTTP 客户端在架构中的位置
- [中间件使用指南](./middleware_guide.md) - 中间件系统详细说明
- [五层架构详解](../architecture/五层架构详解.md#layer-2-capabilities) - Capabilities 层设计

## 版本历史

- **v4.0.0**: 异步性能优化（30倍提升）
- **v3.36.0**: HTTPConfig 支持顶层配置和环境变量
- **v3.22.0**: HttpEventPublisherMiddleware 发布事件
- **v3.20.0**: 支持文件上传（files）、二进制上传（content）、HEAD/OPTIONS 方法
- **v3.19.0**: 请求级认证控制（skip_auth/token）、clear_auth_cache()
- **v3.17.0**: 新事件系统（correlation_id）
- **v3.16.0**: 配置化中间件（HTTPConfig.middlewares）
- **v3.14.0**: 中间件系统统一（洋葱模型）
- **v3.8.0**: AsyncHttpClient 首次引入
- **v3.3.0**: BaseAPI 简化重构
- **v2.0.0**: HttpClient 同步客户端
