"""测试装饰器

提供用于测试的装饰器，如 API 类自动注册、Actions 类自动注册等。

v3.45.0 新增:
- @actions_class: UI Actions 类自动注册装饰器
- load_actions_fixtures: 自动加载所有 Actions fixtures
"""

# v3.45.0: UI Actions 装饰器
from .actions_class import (
    actions_class,
    get_actions_registry,
    load_actions_fixtures,
)
from .api_class import api_class, get_api_registry, load_api_fixtures

__all__ = [
    # HTTP API 装饰器
    "api_class",
    "get_api_registry",
    "load_api_fixtures",
    # UI Actions 装饰器 (v3.45.0)
    "actions_class",
    "get_actions_registry",
    "load_actions_fixtures",
]
