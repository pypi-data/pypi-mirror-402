# 熔断器使用指南

> **最后更新**: 2026-01-17
> **适用版本**: v3.7.0+（熔断器模式）

## 概述

CircuitBreaker 是 DF Test Framework 的熔断器实现，用于防止级联失败和系统雪崩。

### 核心特性

- ✅ **自动熔断** - 失败次数达到阈值时自动打开熔断器
- ✅ **自动恢复** - 超时后自动尝试恢复
- ✅ **状态机管理** - CLOSED → OPEN → HALF_OPEN → CLOSED
- ✅ **装饰器支持** - 简洁的装饰器语法
- ✅ **线程安全** - 支持多线程环境
- ✅ **降级处理** - 熔断时可使用降级方案

### 工作原理

```
正常请求 → CLOSED（关闭状态）
    ↓ 失败次数达到阈值
熔断请求 → OPEN（打开状态）
    ↓ 超时后
尝试恢复 → HALF_OPEN（半开状态）
    ↓ 成功
恢复正常 → CLOSED（关闭状态）
```

### 典型使用场景

1. **HTTP API 调用** - 防止外部服务故障导致雪崩
2. **数据库查询** - 数据库超时时快速失败
3. **第三方服务调用** - 限制失败重试
4. **微服务调用** - 服务间调用保护

---

## 快速开始

### 装饰器方式（推荐）

```python
from df_test_framework.infrastructure.resilience import circuit_breaker, CircuitOpenError

@circuit_breaker(failure_threshold=5, timeout=30)
def call_payment_api(amount):
    \"\"\"调用支付 API\"\"\"
    response = requests.post("/payment", json={"amount": amount})
    response.raise_for_status()
    return response.json()

# 使用
try:
    result = call_payment_api(100)
except CircuitOpenError:
    # 熔断器已打开，使用降级方案
    logger.warning("支付服务熔断，使用降级方案")
    result = {"status": "pending", "message": "服务暂时不可用"}
```

### 直接调用方式

```python
from df_test_framework.infrastructure.resilience import CircuitBreaker, CircuitOpenError

# 创建熔断器实例
breaker = CircuitBreaker(failure_threshold=3, timeout=60)

def external_api_call():
    \"\"\"外部 API 调用\"\"\"
    response = requests.get("https://api.example.com/data")
    response.raise_for_status()
    return response.json()

# 使用熔断器保护调用
try:
    result = breaker.call(external_api_call)
except CircuitOpenError:
    # 熔断器已打开，使用缓存数据
    result = get_cached_data()
```

---

## 熔断器状态机

### CLOSED（关闭状态）

**正常运行状态**，所有请求正常执行。

- 请求成功：重置失败计数器
- 请求失败：失败计数器 +1
- 失败次数达到阈值：切换到 OPEN 状态

```python
# CLOSED 状态示例
breaker = CircuitBreaker(failure_threshold=3)

# 前 2 次失败，仍在 CLOSED 状态
breaker.call(failing_function)  # 失败 1
breaker.call(failing_function)  # 失败 2

# 第 3 次失败，切换到 OPEN 状态
breaker.call(failing_function)  # 失败 3 → OPEN
```

### OPEN（打开状态）

**熔断状态**，所有请求直接失败，不执行实际调用。

- 所有请求立即抛出 `CircuitOpenError`
- 不执行被保护的函数
- 超时后自动切换到 HALF_OPEN 状态

```python
# OPEN 状态示例
try:
    breaker.call(function)  # 直接抛出 CircuitOpenError
except CircuitOpenError:
    logger.warning("熔断器已打开，使用降级方案")
    return fallback_response()
```

### HALF_OPEN（半开状态）

**尝试恢复状态**，允许少量请求尝试执行。

- 允许一次测试请求
- 测试请求成功：切换到 CLOSED 状态
- 测试请求失败：切换回 OPEN 状态

```python
# HALF_OPEN 状态示例
# 超时后，熔断器进入 HALF_OPEN 状态
time.sleep(timeout + 1)

# 第一次请求作为测试请求
breaker.call(function)  # 成功 → CLOSED
                        # 失败 → OPEN
```

---

## 配置参数

### failure_threshold（失败阈值）

连续失败多少次后打开熔断器。

```python
# 连续失败 5 次后熔断
breaker = CircuitBreaker(failure_threshold=5)
```

**推荐值**：
- 高可用服务：3-5 次
- 一般服务：5-10 次
- 容错性高的服务：10-20 次

### timeout（超时时间）

熔断器打开后，多少秒后尝试恢复（进入 HALF_OPEN 状态）。

```python
# 熔断 60 秒后尝试恢复
breaker = CircuitBreaker(failure_threshold=5, timeout=60)
```

**推荐值**：
- 快速恢复：30-60 秒
- 一般场景：60-120 秒
- 慢速恢复：120-300 秒

---

## 使用指南

### HTTP API 调用保护

```python
from df_test_framework.infrastructure.resilience import circuit_breaker, CircuitOpenError

@circuit_breaker(failure_threshold=5, timeout=60)
def call_external_api(endpoint, data):
    """调用外部 API"""
    response = requests.post(f"https://api.example.com{endpoint}", json=data)
    response.raise_for_status()
    return response.json()

# 使用
try:
    result = call_external_api("/users", {"name": "Alice"})
except CircuitOpenError:
    logger.warning("外部 API 熔断，使用降级方案")
    result = {"status": "pending", "message": "服务暂时不可用"}
```

### 数据库查询保护

```python
@circuit_breaker(failure_threshold=3, timeout=30)
def query_user_data(user_id):
    """查询用户数据"""
    with database.session() as session:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        return user.to_dict()

# 使用
try:
    user = query_user_data(123)
except CircuitOpenError:
    logger.warning("数据库查询熔断，使用缓存")
    user = cache.get(f"user:{123}")
```

### 降级处理

```python
def get_user_info(user_id):
    """获取用户信息（带降级）"""
    try:
        # 尝试从 API 获取
        return call_user_api(user_id)
    except CircuitOpenError:
        # API 熔断，尝试从缓存获取
        cached = cache.get(f"user:{user_id}")
        if cached:
            return cached
        # 缓存也没有，返回默认值
        return {"id": user_id, "name": "Unknown", "status": "unavailable"}
```

---

## 最佳实践

### 1. 合理设置阈值

根据服务特性设置合理的失败阈值：

```python
# ✅ 推荐：根据服务特性设置
@circuit_breaker(failure_threshold=5, timeout=60)  # 一般服务
def call_api(): ...

@circuit_breaker(failure_threshold=3, timeout=30)  # 高可用服务
def call_payment_api(): ...

# ❌ 不推荐：阈值过低或过高
@circuit_breaker(failure_threshold=1, timeout=10)  # 太敏感
@circuit_breaker(failure_threshold=100, timeout=600)  # 太宽松
```

### 2. 提供降级方案

熔断时应提供降级方案，而不是直接失败：

```python
# ✅ 推荐：提供降级方案
try:
    result = call_api()
except CircuitOpenError:
    result = get_cached_data()  # 使用缓存
    # 或返回默认值
    # result = get_default_response()

# ❌ 不推荐：直接失败
result = call_api()  # 熔断时直接抛出异常
```

### 3. 记录熔断事件

熔断事件应该被记录和监控：

```python
@circuit_breaker(failure_threshold=5, timeout=60)
def call_api():
    try:
        return requests.get("/api/data").json()
    except Exception as e:
        logger.error(f"API 调用失败: {e}")
        raise

# 使用时记录熔断
try:
    result = call_api()
except CircuitOpenError:
    logger.warning("API 熔断，使用降级方案")
    # 发送告警
    alert_service.send("API 服务熔断")
    result = get_cached_data()
```

### 4. 避免过度使用

不是所有函数都需要熔断器保护：

```python
# ✅ 推荐：保护外部调用
@circuit_breaker(failure_threshold=5, timeout=60)
def call_external_service(): ...

# ❌ 不推荐：保护内部函数
@circuit_breaker(failure_threshold=5, timeout=60)
def calculate_sum(a, b):  # 内部计算不需要熔断器
    return a + b
```

---

## 相关文档

- [HTTP 客户端指南](http_client_guide.md) - HTTP 请求保护
- [数据库使用指南](database_guide.md) - 数据库查询保护
- [日志系统指南](logging_guide.md) - 熔断事件记录
- [配置系统指南](config_guide.md) - 熔断器配置管理

---

**完成时间**: 2026-01-17


