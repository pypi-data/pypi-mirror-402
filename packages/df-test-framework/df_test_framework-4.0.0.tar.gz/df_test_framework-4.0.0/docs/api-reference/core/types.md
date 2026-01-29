# 类型定义 API 参考

> **最后更新**: 2026-01-17
> **适用版本**: v3.14.0+

## 概述

类型定义模块提供了框架中使用的所有类型别名、枚举和类型变量，确保类型安全和代码可读性。

### 设计原则

- **类型安全**: 使用枚举和类型别名提供编译时类型检查
- **可读性**: 使用有意义的类型名称提高代码可读性
- **可扩展**: 支持自定义类型和枚举
- **Pydantic 集成**: 提供 Pydantic 序列化类型支持

### 核心组件

```
types.py     # 类型定义
```

### 类型分类

```
类型定义
├── 枚举类型
│   ├── Environment (环境枚举)
│   ├── LogLevel (日志级别)
│   ├── HttpMethod (HTTP 方法)
│   ├── DatabaseDialect (数据库方言)
│   ├── MessageQueueType (消息队列类型)
│   ├── StorageType (存储类型)
│   ├── HttpStatusGroup (HTTP 状态码分组)
│   ├── HttpStatus (HTTP 状态码)
│   ├── DatabaseOperation (数据库操作类型)
│   ├── Priority (测试优先级)
│   └── CaseType (测试类型)
├── 类型变量
│   ├── TRequest (请求类型变量)
│   └── TResponse (响应类型变量)
├── 类型别名
│   ├── JsonDict (JSON 字典)
│   ├── Headers (HTTP 头)
│   └── QueryParams (查询参数)
└── Pydantic 序列化类型
    ├── DecimalAsFloat (Decimal 转浮点数)
    └── DecimalAsCurrency (Decimal 转货币格式)
```

---

## 枚举类型

### Environment

环境枚举，定义应用运行环境。

**定义位置**: `core/types.py`

#### 类签名

```python
class Environment(str, Enum):
    """环境枚举"""
```

#### 枚举值

```python
LOCAL = "local"          # 本地环境
DEV = "dev"              # 开发环境
TEST = "test"            # 测试环境
STAGING = "staging"      # 预发布环境
PRODUCTION = "production"  # 生产环境
PROD = "prod"            # 生产环境（简写）
```

#### 类方法

##### from_string()

```python
@classmethod
def from_string(cls, value: str) -> Environment:
    """从字符串创建环境枚举

    Args:
        value: 环境字符串（不区分大小写）

    Returns:
        Environment 枚举值

    Raises:
        ValueError: 未知的环境值
    """
```

#### 使用示例

```python
from df_test_framework.core.types import Environment

# 直接使用枚举值
env = Environment.DEV
print(env.value)  # "dev"

# 从字符串创建
env = Environment.from_string("PRODUCTION")
print(env)  # Environment.PRODUCTION

# 比较
if env == Environment.PRODUCTION:
    print("生产环境")
```

---

## LogLevel

日志级别枚举。

**定义位置**: `core/types.py`

#### 类签名

```python
class LogLevel(str, Enum):
    """日志级别"""
```

#### 枚举值

```python
DEBUG = "DEBUG"          # 调试级别
INFO = "INFO"            # 信息级别
WARNING = "WARNING"      # 警告级别
ERROR = "ERROR"          # 错误级别
CRITICAL = "CRITICAL"    # 严重错误级别
```

#### 使用示例

```python
from df_test_framework.core.types import LogLevel

# 配置日志级别
log_level = LogLevel.INFO

# 在配置中使用
config = {
    "logging": {
        "level": log_level.value,
    }
}
```

---

## HttpMethod

HTTP 方法枚举。

**定义位置**: `core/types.py`

#### 类签名

```python
class HttpMethod(str, Enum):
    """HTTP 方法"""
```

#### 枚举值

```python
GET = "GET"              # GET 请求
POST = "POST"            # POST 请求
PUT = "PUT"              # PUT 请求
PATCH = "PATCH"          # PATCH 请求
DELETE = "DELETE"        # DELETE 请求
HEAD = "HEAD"            # HEAD 请求
OPTIONS = "OPTIONS"      # OPTIONS 请求
```

#### 使用示例

```python
from df_test_framework.core.types import HttpMethod

# 发送请求
response = await http_client.request(
    method=HttpMethod.POST.value,
    path="/api/users",
    json={"name": "Alice"},
)

# 条件判断
if method == HttpMethod.GET:
    # 处理 GET 请求
    pass
```

---

## DatabaseDialect

数据库方言枚举。

**定义位置**: `core/types.py`

#### 类签名

```python
class DatabaseDialect(str, Enum):
    """数据库方言"""
```

#### 枚举值

```python
MYSQL = "mysql"          # MySQL 数据库
POSTGRESQL = "postgresql"  # PostgreSQL 数据库
SQLITE = "sqlite"        # SQLite 数据库
ORACLE = "oracle"        # Oracle 数据库
MSSQL = "mssql"          # Microsoft SQL Server
```

#### 使用示例

```python
from df_test_framework.core.types import DatabaseDialect

# 配置数据库
db_config = {
    "dialect": DatabaseDialect.MYSQL.value,
    "host": "localhost",
    "port": 3306,
}

# 根据方言选择驱动
if dialect == DatabaseDialect.MYSQL:
    driver = "pymysql"
elif dialect == DatabaseDialect.POSTGRESQL:
    driver = "psycopg2"
```

---

## MessageQueueType

消息队列类型枚举。

**定义位置**: `core/types.py`

#### 类签名

```python
class MessageQueueType(str, Enum):
    """消息队列类型"""
```

#### 枚举值

```python
KAFKA = "kafka"          # Apache Kafka
RABBITMQ = "rabbitmq"    # RabbitMQ
ROCKETMQ = "rocketmq"    # Apache RocketMQ
```

#### 使用示例

```python
from df_test_framework.core.types import MessageQueueType

# 配置消息队列
mq_config = {
    "type": MessageQueueType.KAFKA.value,
    "brokers": ["localhost:9092"],
}

# 根据类型创建客户端
if mq_type == MessageQueueType.KAFKA:
    client = KafkaClient(config)
elif mq_type == MessageQueueType.RABBITMQ:
    client = RabbitMQClient(config)
```

---

## StorageType

存储类型枚举。

**定义位置**: `core/types.py`

#### 类签名

```python
class StorageType(str, Enum):
    """存储类型"""
```

#### 枚举值

```python
S3 = "s3"                # Amazon S3
OSS = "oss"              # 阿里云 OSS
MINIO = "minio"          # MinIO
LOCAL = "local"          # 本地文件系统
```

#### 使用示例

```python
from df_test_framework.core.types import StorageType

# 配置存储
storage_config = {
    "type": StorageType.S3.value,
    "bucket": "my-bucket",
    "region": "us-west-1",
}

# 根据类型创建存储客户端
if storage_type == StorageType.S3:
    client = S3Client(config)
elif storage_type == StorageType.OSS:
    client = OSSClient(config)
```

---

## HttpStatusGroup

HTTP 状态码分组枚举。

**定义位置**: `core/types.py`

#### 类签名

```python
class HttpStatusGroup(str, Enum):
    """HTTP 状态码分组"""
```

#### 枚举值

```python
INFORMATIONAL = "1xx"    # 信息响应 (100-199)
SUCCESS = "2xx"          # 成功响应 (200-299)
REDIRECTION = "3xx"      # 重定向 (300-399)
CLIENT_ERROR = "4xx"     # 客户端错误 (400-499)
SERVER_ERROR = "5xx"     # 服务器错误 (500-599)
```

#### 使用示例

```python
from df_test_framework.core.types import HttpStatusGroup

# 判断状态码分组
def get_status_group(status_code: int) -> HttpStatusGroup:
    if 100 <= status_code < 200:
        return HttpStatusGroup.INFORMATIONAL
    elif 200 <= status_code < 300:
        return HttpStatusGroup.SUCCESS
    elif 300 <= status_code < 400:
        return HttpStatusGroup.REDIRECTION
    elif 400 <= status_code < 500:
        return HttpStatusGroup.CLIENT_ERROR
    else:
        return HttpStatusGroup.SERVER_ERROR

# 使用
group = get_status_group(404)
if group == HttpStatusGroup.CLIENT_ERROR:
    print("客户端错误")
```

---

## HttpStatus

常用 HTTP 状态码枚举。

**定义位置**: `core/types.py`

#### 类签名

```python
class HttpStatus(int, Enum):
    """常用 HTTP 状态码"""
```

#### 枚举值

##### 2xx 成功

```python
OK = 200                 # 请求成功
CREATED = 201            # 资源创建成功
ACCEPTED = 202           # 请求已接受
NO_CONTENT = 204         # 无内容返回
```

##### 3xx 重定向

```python
MOVED_PERMANENTLY = 301  # 永久重定向
FOUND = 302              # 临时重定向
NOT_MODIFIED = 304       # 资源未修改
```

##### 4xx 客户端错误

```python
BAD_REQUEST = 400        # 请求错误
UNAUTHORIZED = 401       # 未授权
FORBIDDEN = 403          # 禁止访问
NOT_FOUND = 404          # 资源不存在
METHOD_NOT_ALLOWED = 405 # 方法不允许
CONFLICT = 409           # 冲突
UNPROCESSABLE_ENTITY = 422  # 无法处理的实体
TOO_MANY_REQUESTS = 429  # 请求过多
```

##### 5xx 服务器错误

```python
INTERNAL_SERVER_ERROR = 500  # 服务器内部错误
BAD_GATEWAY = 502        # 网关错误
SERVICE_UNAVAILABLE = 503  # 服务不可用
GATEWAY_TIMEOUT = 504    # 网关超时
```

#### 使用示例

```python
from df_test_framework.core.types import HttpStatus

# 断言状态码
assert response.status_code == HttpStatus.OK

# 条件判断
if response.status_code == HttpStatus.NOT_FOUND:
    print("资源不存在")

# 返回响应
return Response(
    status_code=HttpStatus.CREATED,
    body={"id": 123, "name": "Alice"},
)
```

---

## DatabaseOperation

数据库操作类型枚举。

**定义位置**: `core/types.py`

#### 类签名

```python
class DatabaseOperation(str, Enum):
    """数据库操作类型"""
```

#### 枚举值

```python
SELECT = "SELECT"        # 查询操作
INSERT = "INSERT"        # 插入操作
UPDATE = "UPDATE"        # 更新操作
DELETE = "DELETE"        # 删除操作
```

#### 使用示例

```python
from df_test_framework.core.types import DatabaseOperation

# 记录操作类型
def log_operation(operation: DatabaseOperation, table: str):
    print(f"{operation.value} on {table}")

# 使用
log_operation(DatabaseOperation.SELECT, "users")

# 权限检查
if operation == DatabaseOperation.DELETE:
    check_delete_permission()
```

---

## Priority

测试用例优先级枚举。

**定义位置**: `core/types.py`

#### 类签名

```python
class Priority(str, Enum):
    """测试用例优先级"""
```

**说明**：
- v3.35.5: 从 TestPriority 重命名为 Priority，避免 pytest 收集警告

#### 枚举值

```python
CRITICAL = "critical"    # 关键优先级
HIGH = "high"            # 高优先级
MEDIUM = "medium"        # 中优先级
LOW = "low"              # 低优先级
```

#### 使用示例

```python
from df_test_framework.core.types import Priority
import pytest

# 标记测试优先级
@pytest.mark.priority(Priority.CRITICAL)
def test_login():
    """关键测试：用户登录"""
    pass

@pytest.mark.priority(Priority.HIGH)
def test_create_order():
    """高优先级测试：创建订单"""
    pass

# 根据优先级筛选测试
# pytest -m "priority==critical"
```

---

## CaseType

测试类型枚举。

**定义位置**: `core/types.py`

#### 类签名

```python
class CaseType(str, Enum):
    """测试类型"""
```

**说明**：
- v3.35.5: 从 TestType 重命名为 CaseType，避免 pytest 收集警告

#### 枚举值

```python
SMOKE = "smoke"          # 冒烟测试
REGRESSION = "regression"  # 回归测试
INTEGRATION = "integration"  # 集成测试
E2E = "e2e"              # 端到端测试
PERFORMANCE = "performance"  # 性能测试
SECURITY = "security"    # 安全测试
```

#### 使用示例

```python
from df_test_framework.core.types import CaseType
import pytest

# 标记测试类型
@pytest.mark.case_type(CaseType.SMOKE)
def test_health_check():
    """冒烟测试：健康检查"""
    pass

@pytest.mark.case_type(CaseType.E2E)
def test_complete_order_flow():
    """端到端测试：完整订单流程"""
    pass

# 根据类型筛选测试
# pytest -m "case_type==smoke"
```

---

## 类型变量

### TRequest

请求类型变量，用于泛型中间件和客户端。

**定义位置**: `core/types.py`

```python
TRequest = TypeVar("TRequest")
```

#### 使用示例

```python
from typing import TypeVar
from df_test_framework.core.types import TRequest, TResponse

# 泛型中间件
class Middleware[TRequest, TResponse]:
    async def __call__(
        self,
        request: TRequest,
        call_next: Callable[[TRequest], Awaitable[TResponse]],
    ) -> TResponse:
        # 处理请求
        return await call_next(request)
```

---

### TResponse

响应类型变量，用于泛型中间件和客户端。

**定义位置**: `core/types.py`

```python
TResponse = TypeVar("TResponse")
```

#### 使用示例

```python
from df_test_framework.core.types import TRequest, TResponse

# 泛型客户端
class Client[TRequest, TResponse]:
    async def send(self, request: TRequest) -> TResponse:
        # 发送请求
        pass
```

---

## 类型别名

### JsonDict

JSON 字典类型别名。

**定义位置**: `core/types.py`

```python
JsonDict = dict[str, Any]
```

#### 使用示例

```python
from df_test_framework.core.types import JsonDict

# 函数参数
def process_data(data: JsonDict) -> None:
    user_id = data.get("user_id")
    name = data.get("name")

# 返回值
def get_user_data() -> JsonDict:
    return {"id": 123, "name": "Alice", "email": "alice@example.com"}
```

---

### Headers

HTTP 头类型别名。

**定义位置**: `core/types.py`

```python
Headers = dict[str, str]
```

#### 使用示例

```python
from df_test_framework.core.types import Headers

# 函数参数
def add_auth_header(headers: Headers, token: str) -> Headers:
    headers["Authorization"] = f"Bearer {token}"
    return headers

# 使用
headers: Headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}
```

---

### QueryParams

查询参数类型别名。

**定义位置**: `core/types.py`

```python
QueryParams = dict[str, Any]
```

#### 使用示例

```python
from df_test_framework.core.types import QueryParams

# 函数参数
def build_url(base_url: str, params: QueryParams) -> str:
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{base_url}?{query_string}"

# 使用
params: QueryParams = {
    "page": 1,
    "size": 20,
    "sort": "created_at",
}
```

---

## Pydantic 序列化类型

### DecimalAsFloat

Decimal 序列化为浮点数的 Pydantic 类型注解。

**定义位置**: `core/types.py`

**版本**: v3.29.0 从 utils/types.py 迁移

```python
DecimalAsFloat = Annotated[
    Decimal,
    PlainSerializer(lambda x: float(x), return_type=float, when_used="json"),
]
```

#### 使用场景

某些 API 要求金额字段为数字类型而不是字符串。

#### 使用示例

```python
from decimal import Decimal
from pydantic import BaseModel
from df_test_framework.core.types import DecimalAsFloat

class PriceRequest(BaseModel):
    price: DecimalAsFloat  # 序列化为浮点数

# 创建实例
request = PriceRequest(price=Decimal("99.99"))

# 序列化为 JSON
print(request.model_dump_json())
# 输出: {"price":99.99}  # 数字类型，不是字符串

# 默认 Decimal 序列化为字符串
class DefaultPriceRequest(BaseModel):
    price: Decimal

request2 = DefaultPriceRequest(price=Decimal("99.99"))
print(request2.model_dump_json())
# 输出: {"price":"99.99"}  # 字符串类型
```

#### 警告

⚠️ **浮点数有精度问题，金融场景慎用！**

推荐使用默认的字符串序列化以避免精度损失。

```python
# ❌ 不推荐：金融场景使用浮点数
class PaymentRequest(BaseModel):
    amount: DecimalAsFloat  # 可能有精度问题

# ✅ 推荐：金融场景使用字符串
class PaymentRequest(BaseModel):
    amount: Decimal  # 序列化为字符串，保证精度
```

---

### DecimalAsCurrency

Decimal 序列化为货币格式的 Pydantic 类型注解。

**定义位置**: `core/types.py`

**版本**: v3.29.0 从 utils/types.py 迁移

```python
DecimalAsCurrency = Annotated[
    Decimal,
    PlainSerializer(_format_currency, return_type=str, when_used="json"),
]
```

**格式化函数**:
```python
def _format_currency(value: Decimal) -> str:
    """格式化为货币格式：$123.45"""
    return f"${value:.2f}"
```

#### 使用场景

显示层需要格式化的金额字符串。

#### 使用示例

```python
from decimal import Decimal
from pydantic import BaseModel
from df_test_framework.core.types import DecimalAsCurrency

class DisplayRequest(BaseModel):
    amount: DecimalAsCurrency  # 序列化为货币格式

# 创建实例
request = DisplayRequest(amount=Decimal("123.45"))

# 序列化为 JSON
print(request.model_dump_json())
# 输出: {"amount":"$123.45"}

# 更多示例
request2 = DisplayRequest(amount=Decimal("1000.5"))
print(request2.model_dump_json())
# 输出: {"amount":"$1000.50"}
```

#### 说明

- **默认使用美元符号** ($)
- **保留 2 位小数**
- **如需自定义格式**，请使用 `@field_serializer` 装饰器

```python
from pydantic import BaseModel, field_serializer
from decimal import Decimal

class CustomCurrencyRequest(BaseModel):
    amount: Decimal

    @field_serializer("amount", when_used="json")
    def serialize_amount(self, value: Decimal) -> str:
        # 自定义格式：人民币
        return f"¥{value:.2f}"
```

---

## 使用指南

### 枚举类型使用

#### 比较枚举值

```python
from df_test_framework.core.types import Environment

env = Environment.DEV

# ✅ 推荐：直接比较枚举
if env == Environment.DEV:
    print("开发环境")

# ✅ 也可以：比较值
if env.value == "dev":
    print("开发环境")

# ❌ 不推荐：字符串比较
if str(env) == "Environment.DEV":
    print("开发环境")
```

#### 遍历枚举

```python
from df_test_framework.core.types import HttpMethod

# 遍历所有 HTTP 方法
for method in HttpMethod:
    print(f"{method.name}: {method.value}")

# 输出:
# GET: GET
# POST: POST
# PUT: PUT
# ...
```

#### 从字符串创建枚举

```python
from df_test_framework.core.types import Environment

# 使用类方法
env = Environment.from_string("production")

# 使用枚举构造
env = Environment("dev")

# 处理未知值
try:
    env = Environment.from_string("unknown")
except ValueError as e:
    print(f"错误: {e}")
```

### 类型注解使用

#### 函数参数和返回值

```python
from df_test_framework.core.types import JsonDict, Headers, QueryParams

def send_request(
    url: str,
    headers: Headers,
    params: QueryParams,
) -> JsonDict:
    """发送 HTTP 请求

    Args:
        url: 请求 URL
        headers: HTTP 头
        params: 查询参数

    Returns:
        响应数据
    """
    # 实现逻辑
    pass
```

#### 泛型类型

```python
from df_test_framework.core.types import TRequest, TResponse

class GenericClient[TRequest, TResponse]:
    """泛型客户端"""

    async def send(self, request: TRequest) -> TResponse:
        # 发送请求
        pass

# 使用
class MyRequest:
    pass

class MyResponse:
    pass

client: GenericClient[MyRequest, MyResponse] = GenericClient()
```

---

## 最佳实践

### 1. 优先使用枚举而非字符串

```python
# ✅ 推荐：使用枚举
from df_test_framework.core.types import HttpMethod

method = HttpMethod.POST

# ❌ 不推荐：使用字符串
method = "POST"
```

**优点**：
- 类型安全
- IDE 自动补全
- 避免拼写错误

### 2. 使用类型别名提高可读性

```python
# ✅ 推荐：使用类型别名
from df_test_framework.core.types import JsonDict

def process_data(data: JsonDict) -> None:
    pass

# ❌ 不推荐：使用原始类型
def process_data(data: dict[str, Any]) -> None:
    pass
```

### 3. Decimal 序列化选择

```python
from decimal import Decimal
from pydantic import BaseModel
from df_test_framework.core.types import DecimalAsFloat, DecimalAsCurrency

# ✅ 推荐：金融场景使用默认字符串
class PaymentRequest(BaseModel):
    amount: Decimal  # 序列化为 "99.99"

# ✅ 适用：API 要求数字类型
class PriceRequest(BaseModel):
    price: DecimalAsFloat  # 序列化为 99.99

# ✅ 适用：显示层格式化
class DisplayRequest(BaseModel):
    amount: DecimalAsCurrency  # 序列化为 "$99.99"
```

### 4. 枚举值的配置使用

```python
from df_test_framework.core.types import Environment, DatabaseDialect

# ✅ 推荐：在配置中使用枚举值
config = {
    "environment": Environment.PRODUCTION.value,
    "database": {
        "dialect": DatabaseDialect.MYSQL.value,
        "host": "localhost",
    },
}

# 从配置读取
env = Environment(config["environment"])
dialect = DatabaseDialect(config["database"]["dialect"])
```

---

## 相关文档

### 使用指南
- [HTTP 客户端指南](../../guides/http_client_guide.md) - HTTP 类型使用
- [数据库使用指南](../../guides/database_guide.md) - 数据库类型使用
- [Fixtures 使用指南](../../guides/fixtures_guide.md) - 测试类型使用

### 架构文档
- [五层架构详解](../../architecture/五层架构详解.md) - 架构层次说明
- [ARCHITECTURE_V4.0.md](../../architecture/ARCHITECTURE_V4.0.md) - v4.0 架构总览

### API 参考
- [Core 层 API 参考](README.md) - Core 层概览
- [协议定义 API 参考](protocols.md) - 协议接口
- [异常体系 API 参考](exceptions.md) - 异常类型定义

---

**完成时间**: 2026-01-17

