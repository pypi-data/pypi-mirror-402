# 脱敏服务使用指南

> **最后更新**: 2026-01-17
> **适用版本**: v3.40.0+（统一脱敏服务）

## 概述

SanitizeService 是 DF Test Framework 的统一脱敏服务，用于保护敏感数据在日志、控制台、测试报告中的安全。

### 核心特性

- ✅ **统一脱敏** - 日志、控制台、Allure 报告统一脱敏逻辑
- ✅ **多种策略** - FULL（完全隐藏）、PARTIAL（部分保留）、HASH（哈希）
- ✅ **深度递归** - 支持嵌套 dict/list 的深度脱敏
- ✅ **正则匹配** - 支持字段名和消息内容的正则表达式匹配
- ✅ **配置驱动** - 通过 YAML 配置敏感字段和脱敏策略
- ✅ **自动集成** - 与 settings 生命周期绑定，配置变更自动生效

### 工作原理

```
敏感数据 → SanitizeService → 脱敏后数据
    ↓
配置检查 → 字段名匹配 → 策略应用
    ↓           ↓           ↓
enabled?   sensitive_keys  FULL/PARTIAL/HASH
```

---

## 快速开始

### 基本使用

```python
from df_test_framework.infrastructure.sanitize import get_sanitize_service

# 获取脱敏服务实例
service = get_sanitize_service()

# 脱敏单个值
masked = service.sanitize_value("password", "mysecretpassword")
print(masked)  # 输出: myse****word

# 判断字段是否敏感
is_sensitive = service.is_sensitive("api_key")
print(is_sensitive)  # 输出: True

# 脱敏字典
data = {
    "username": "alice",
    "password": "secret123",
    "email": "alice@example.com"
}
sanitized = service.sanitize_dict(data)
print(sanitized)
# 输出: {'username': 'alice', 'password': 'secr****123', 'email': 'alice@example.com'}
```

### 自动集成

脱敏服务已自动集成到框架的各个组件中：

```python
# 日志自动脱敏
logger.info("用户登录", username="alice", password="secret123")
# 输出: 用户登录 username=alice password=secr****123

# HTTP 请求日志自动脱敏
http_client.post("/login", json={"username": "alice", "password": "secret123"})
# Allure 报告中密码自动脱敏

# 控制台调试自动脱敏
console.print({"api_key": "sk-1234567890"})
# 输出: {'api_key': 'sk-1****890'}
```

---

## 配置方法

### YAML 配置

```yaml
# config/base.yaml
sanitize:
  enabled: true                    # 启用脱敏
  default_strategy: PARTIAL        # 默认策略: FULL/PARTIAL/HASH
  mask_value: "****"               # 完全隐藏时的替换值

  # 敏感字段列表（支持正则表达式）
  sensitive_keys:
    - password
    - passwd
    - pwd
    - token
    - secret
    - api_key
    - apikey
    - authorization
    - auth
    - credential
    - access_token
    - refresh_token
    - private_key
    - ".*_token"                   # 正则：匹配所有以 _token 结尾的字段
    - "api.*key"                   # 正则：匹配 api_key, apikey 等

  # 消息内容正则匹配（脱敏消息中的敏感信息）
  sensitive_patterns:
    - "password[=:]\\s*\\S+"       # 匹配 password=xxx 或 password: xxx
    - "token[=:]\\s*\\S+"          # 匹配 token=xxx 或 token: xxx
```

### 代码配置

```python
from df_test_framework.infrastructure.config import SanitizeConfig, SanitizeStrategy
from df_test_framework.infrastructure.sanitize import SanitizeService

# 创建自定义配置
config = SanitizeConfig(
    enabled=True,
    default_strategy=SanitizeStrategy.PARTIAL,
    sensitive_keys=["password", "api_key", ".*_token"],
    sensitive_patterns=[r"password[=:]\s*\S+"]
)

# 创建脱敏服务实例
service = SanitizeService(config)
```

### 环境变量配置

```bash
# 启用/禁用脱敏
export SANITIZE__ENABLED=true

# 设置默认策略
export SANITIZE__DEFAULT_STRATEGY=PARTIAL

# 设置替换值
export SANITIZE__MASK_VALUE="***"
```

---

## 使用指南

### 获取服务实例

```python
from df_test_framework.infrastructure.sanitize import get_sanitize_service

# 获取全局单例（推荐）
service = get_sanitize_service()
```

### 判断字段是否敏感

```python
# 判断字段名是否敏感
is_sensitive = service.is_sensitive("password")
print(is_sensitive)  # True

is_sensitive = service.is_sensitive("username")
print(is_sensitive)  # False

# 支持正则匹配
is_sensitive = service.is_sensitive("user_token")  # True（匹配 .*_token）
is_sensitive = service.is_sensitive("api_secret_key")  # True（匹配 api.*key）
```

### 脱敏单个值

```python
# 使用默认策略（PARTIAL）
masked = service.sanitize_value("password", "mysecretpassword")
print(masked)  # myse****word

# 指定策略
from df_test_framework.infrastructure.config import SanitizeStrategy

# 完全隐藏
masked = service.sanitize_value("password", "mysecretpassword", SanitizeStrategy.FULL)
print(masked)  # ****

# 哈希
masked = service.sanitize_value("password", "mysecretpassword", SanitizeStrategy.HASH)
print(masked)  # hash:a1b2c3d4e5f6...
```

### 脱敏字典

```python
# 脱敏字典中的敏感字段
data = {
    "username": "alice",
    "password": "secret123",
    "email": "alice@example.com",
    "api_key": "sk-1234567890"
}

sanitized = service.sanitize_dict(data)
print(sanitized)
# {
#     'username': 'alice',
#     'password': 'secr****123',
#     'email': 'alice@example.com',
#     'api_key': 'sk-1****890'
# }
```

### 脱敏嵌套结构

```python
# 深度递归脱敏
data = {
    "user": {
        "name": "alice",
        "credentials": {
            "password": "secret123",
            "api_key": "sk-1234567890"
        }
    },
    "tokens": ["token1", "token2"]
}

sanitized = service.sanitize_dict(data)
# 所有嵌套的敏感字段都会被脱敏
```

### 脱敏消息内容

```python
# 脱敏消息中的敏感信息（基于正则匹配）
message = "User login with password=secret123 and token=abc123"
sanitized = service.sanitize_message(message)
print(sanitized)
# User login with password=**** and token=****
```

---

## 脱敏策略

### FULL - 完全隐藏

完全替换为配置的 `mask_value`（默认 `****`）：

```python
service.sanitize_value("password", "mysecretpassword", SanitizeStrategy.FULL)
# 输出: ****
```

**适用场景**：
- 极度敏感的信息（如密码、私钥）
- 不需要任何原始信息的场景

### PARTIAL - 部分保留

保留前后各 25% 的字符，中间替换为 `****`：

```python
service.sanitize_value("password", "mysecretpassword", SanitizeStrategy.PARTIAL)
# 输出: myse****word

service.sanitize_value("api_key", "sk-1234567890", SanitizeStrategy.PARTIAL)
# 输出: sk-1****890
```

**适用场景**：
- 需要部分识别信息的场景（如调试）
- Token、API Key 等需要区分不同值的场景

### HASH - 哈希值

使用 SHA256 哈希，取前 16 位：

```python
service.sanitize_value("password", "mysecretpassword", SanitizeStrategy.HASH)
# 输出: hash:a1b2c3d4e5f6g7h8
```

**适用场景**：
- 需要唯一标识但不能暴露原值
- 日志聚合、问题追踪

---

## 最佳实践

### 1. 使用默认配置

框架已提供合理的默认配置，大多数场景无需修改：

```yaml
# config/base.yaml - 默认配置已足够
sanitize:
  enabled: true
  default_strategy: PARTIAL
```

### 2. 添加自定义敏感字段

根据项目需求添加特定的敏感字段：

```yaml
sanitize:
  sensitive_keys:
    - password
    - api_key
    # 添加项目特定字段
    - ".*_secret"
    - "internal_token"
```

### 3. 生产环境启用脱敏

确保生产环境启用脱敏功能：

```yaml
# config/environments/prod.yaml
sanitize:
  enabled: true
  default_strategy: FULL  # 生产环境使用完全隐藏
```

### 4. 测试环境可选禁用

开发/测试环境可以禁用脱敏以便调试：

```yaml
# config/environments/dev.yaml
sanitize:
  enabled: false  # 开发环境禁用，方便调试
```

---

## 相关文档

- [配置系统指南](config_guide.md) - 脱敏配置管理
- [日志系统指南](logging_guide.md) - 日志自动脱敏
- [HTTP 客户端指南](http_client_guide.md) - HTTP 请求脱敏
- [Bootstrap 引导系统指南](bootstrap_guide.md) - 框架初始化

---

**完成时间**: 2026-01-17

