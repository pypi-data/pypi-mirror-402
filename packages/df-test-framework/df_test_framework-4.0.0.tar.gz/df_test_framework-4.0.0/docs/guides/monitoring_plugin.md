# 监控插件使用指南

> **最后更新**: 2026-01-17
> **适用版本**: v3.14.0+（插件系统重构）

## 概述

MonitoringPlugin 是 DF Test Framework 的内置监控插件，用于收集和统计测试执行过程中的性能指标。

### 核心功能

- **HTTP 请求监控**: 自动记录所有 HTTP 请求的方法、URL、状态码、耗时
- **数据库查询监控**: 自动记录所有数据库查询的 SQL、耗时、行数
- **性能统计**: 提供请求数量、总耗时、平均耗时等统计信息
- **事件驱动**: 基于 EventBus 实现，无侵入式监控

### 工作原理

MonitoringPlugin 通过订阅框架的事件总线（EventBus）来收集性能数据：

```
HTTP 请求 → HttpRequestEndEvent → MonitoringPlugin 记录
数据库查询 → DatabaseQueryEndEvent → MonitoringPlugin 记录
```

---

## 快速开始

### 基本用法

```python
from df_test_framework import Bootstrap
from df_test_framework.plugins.builtin.monitoring import MonitoringPlugin

# 1. 创建监控插件实例
monitoring = MonitoringPlugin()

# 2. 注册插件
app = Bootstrap().with_plugin(monitoring).build()
runtime = app.run()

# 3. 执行测试
http_client = runtime.http_client()
http_client.get("/users")
http_client.post("/users", json={"name": "张三"})

# 4. 查看监控数据
print(f"API 调用次数: {len(monitoring.api_calls)}")
print(f"数据库查询次数: {len(monitoring.db_queries)}")

# 5. 获取统计摘要
summary = monitoring.get_summary()
print(summary)
```

### 在 pytest 中使用

```python
# conftest.py
import pytest
from df_test_framework.plugins.builtin.monitoring import MonitoringPlugin

@pytest.fixture(scope="session")
def monitoring_plugin():
    return MonitoringPlugin()

# 在 pytest_configure 中注册插件
def pytest_configure(config):
    monitoring = MonitoringPlugin()
    config._df_monitoring = monitoring
    # 插件会自动注册到 EventBus

# test_example.py
def test_api_monitoring(http_client, monitoring_plugin):
    """测试 API 监控"""
    # 执行 API 调用
    http_client.get("/users")
    http_client.post("/users", json={"name": "张三"})

    # 验证监控数据
    assert len(monitoring_plugin.api_calls) == 2
    assert monitoring_plugin.api_calls[0]["method"] == "GET"
    assert monitoring_plugin.api_calls[1]["method"] == "POST"
```

---

## API 监控

### 监控数据结构

每个 HTTP 请求会记录以下信息：

```python
{
    "method": "GET",                    # 请求方法
    "url": "https://api.example.com/users",  # 请求 URL
    "status_code": 200,                 # 响应状态码
    "duration": 0.123,                  # 请求耗时（秒）
    "timestamp": "2026-01-17T10:30:00"  # 请求时间
}
```

### 获取 API 调用记录

```python
# 获取所有 API 调用记录
api_calls = monitoring.api_calls

# 遍历记录
for call in api_calls:
    print(f"{call['method']} {call['url']} - {call['status_code']} ({call['duration']}s)")

# 筛选特定方法的请求
get_requests = [c for c in api_calls if c["method"] == "GET"]
post_requests = [c for c in api_calls if c["method"] == "POST"]

# 筛选失败的请求
failed_requests = [c for c in api_calls if c["status_code"] >= 400]
```

### API 统计分析

```python
# 获取统计摘要
summary = monitoring.get_summary()

api_stats = summary["api_calls"]
print(f"总请求数: {api_stats['count']}")
print(f"总耗时: {api_stats['total_duration']:.2f}s")
print(f"平均耗时: {api_stats['avg_duration']:.3f}s")

# 自定义统计
api_calls = monitoring.api_calls
total_duration = sum(c["duration"] for c in api_calls)
avg_duration = total_duration / len(api_calls) if api_calls else 0
max_duration = max((c["duration"] for c in api_calls), default=0)
min_duration = min((c["duration"] for c in api_calls), default=0)

print(f"最慢请求: {max_duration:.3f}s")
print(f"最快请求: {min_duration:.3f}s")
```

---

## 数据库监控

### 监控数据结构

每个数据库查询会记录以下信息：

```python
{
    "sql": "SELECT * FROM users WHERE id = ?",  # SQL 语句
    "duration": 0.045,                          # 查询耗时（秒）
    "row_count": 1,                             # 返回行数
    "timestamp": "2026-01-17T10:30:00"          # 查询时间
}
```

### 获取数据库查询记录

```python
# 获取所有数据库查询记录
db_queries = monitoring.db_queries

# 遍历记录
for query in db_queries:
    print(f"{query['sql']} - {query['row_count']} rows ({query['duration']}s)")

# 筛选慢查询（超过 0.1 秒）
slow_queries = [q for q in db_queries if q["duration"] > 0.1]

# 筛选特定表的查询
user_queries = [q for q in db_queries if "users" in q["sql"].lower()]
```

### 数据库统计分析

```python
# 获取统计摘要
summary = monitoring.get_summary()

db_stats = summary["db_queries"]
print(f"总查询数: {db_stats['count']}")
print(f"总耗时: {db_stats['total_duration']:.2f}s")
print(f"平均耗时: {db_stats['avg_duration']:.3f}s")

# 自定义统计
db_queries = monitoring.db_queries
total_rows = sum(q["row_count"] for q in db_queries)
print(f"总返回行数: {total_rows}")
```

---

## 监控控制

### 启用/禁用监控

```python
# 禁用监控
monitoring.disable()

# 执行操作（不会被记录）
http_client.get("/users")

# 启用监控
monitoring.enable()

# 执行操作（会被记录）
http_client.get("/users")
```

### 清空监控记录

```python
# 清空所有记录
monitoring.clear()

# 验证已清空
assert len(monitoring.api_calls) == 0
assert len(monitoring.db_queries) == 0
```

### 获取完整摘要

```python
summary = monitoring.get_summary()

# 摘要结构
{
    "api_calls": {
        "count": 10,
        "total_duration": 1.234,
        "avg_duration": 0.123
    },
    "db_queries": {
        "count": 5,
        "total_duration": 0.456,
        "avg_duration": 0.091
    }
}
```

---

## 最佳实践

### 1. 测试隔离

```python
# ✅ 推荐：每个测试前清空记录
@pytest.fixture(autouse=True)
def clear_monitoring(monitoring_plugin):
    monitoring_plugin.clear()
    yield

def test_api_call(http_client, monitoring_plugin):
    http_client.get("/users")
    assert len(monitoring_plugin.api_calls) == 1
```

### 2. 性能分析

```python
# ✅ 推荐：分析慢请求
def test_performance(http_client, monitoring_plugin):
    # 执行测试
    for i in range(100):
        http_client.get(f"/users/{i}")

    # 分析性能
    slow_requests = [c for c in monitoring_plugin.api_calls if c["duration"] > 0.5]
    assert len(slow_requests) == 0, f"发现 {len(slow_requests)} 个慢请求"
```

### 3. 监控报告

```python
# ✅ 推荐：生成监控报告
def generate_monitoring_report(monitoring_plugin):
    summary = monitoring_plugin.get_summary()

    report = f"""
    监控报告
    ========
    API 调用:
    - 总数: {summary['api_calls']['count']}
    - 总耗时: {summary['api_calls']['total_duration']:.2f}s
    - 平均耗时: {summary['api_calls']['avg_duration']:.3f}s

    数据库查询:
    - 总数: {summary['db_queries']['count']}
    - 总耗时: {summary['db_queries']['total_duration']:.2f}s
    - 平均耗时: {summary['db_queries']['avg_duration']:.3f}s
    """

    return report
```

---

## 注意事项

### 1. 内存占用

- 监控数据存储在内存中，长时间运行可能占用大量内存
- 建议定期调用 `clear()` 清空记录
- 生产环境谨慎使用

### 2. 性能影响

- 监控本身有轻微性能开销（事件订阅和数据记录）
- 对于性能敏感的场景，可以使用 `disable()` 临时禁用

### 3. 线程安全

- MonitoringPlugin 不是线程安全的
- 多线程环境下可能出现数据竞争
- 建议在单线程测试中使用

---

## 相关文档

- [Bootstrap 引导系统指南](bootstrap_guide.md) - 插件注册方法
- [HTTP 客户端指南](http_client_guide.md) - HTTP 请求监控
- [数据库使用指南](database_guide.md) - 数据库查询监控
- [EventBus 指南](event_bus_guide.md) - 事件系统详解

---

**完成时间**: 2026-01-17
