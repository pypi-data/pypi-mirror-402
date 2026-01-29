"""测试 AsyncDatabase（v4.0.0）

验证异步数据库客户端的各种操作方法。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from df_test_framework.capabilities.databases.async_database import AsyncDatabase
from df_test_framework.core.events import (
    DatabaseQueryEndEvent,
    DatabaseQueryErrorEvent,
    DatabaseQueryStartEvent,
)
from df_test_framework.infrastructure.events import EventBus


class TestAsyncDatabaseInit:
    """测试 AsyncDatabase 初始化"""

    @patch("df_test_framework.capabilities.databases.async_database.create_async_engine")
    @patch("df_test_framework.capabilities.databases.async_database.async_sessionmaker")
    def test_init_default(self, mock_sessionmaker, mock_engine):
        """测试默认初始化"""
        db = AsyncDatabase("mysql+aiomysql://user:pass@localhost/test")

        assert db.connection_string == "mysql+aiomysql://user:pass@localhost/test"
        assert db.allowed_tables is None  # 默认不限制
        mock_engine.assert_called_once()

    @patch("df_test_framework.capabilities.databases.async_database.create_async_engine")
    @patch("df_test_framework.capabilities.databases.async_database.async_sessionmaker")
    def test_init_with_allowed_tables(self, mock_sessionmaker, mock_engine):
        """测试指定表名白名单"""
        allowed = {"users", "orders"}
        db = AsyncDatabase("mysql+aiomysql://user:pass@localhost/test", allowed_tables=allowed)

        assert db.allowed_tables == allowed

    @patch("df_test_framework.capabilities.databases.async_database.create_async_engine")
    @patch("df_test_framework.capabilities.databases.async_database.async_sessionmaker")
    def test_mask_connection_string(self, mock_sessionmaker, mock_engine):
        """测试连接字符串密码脱敏"""
        db = AsyncDatabase("mysql+aiomysql://myuser:secret123@localhost/test")

        masked = db._mask_connection_string()
        assert "secret123" not in masked
        assert "****" in masked
        # 验证主机部分保留
        assert "localhost/test" in masked


class TestAsyncDatabaseTableValidation:
    """测试表名白名单验证"""

    @patch("df_test_framework.capabilities.databases.async_database.create_async_engine")
    @patch("df_test_framework.capabilities.databases.async_database.async_sessionmaker")
    def test_validate_table_allowed(self, mock_sessionmaker, mock_engine):
        """测试允许的表名通过验证"""
        db = AsyncDatabase(
            "mysql+aiomysql://user:pass@localhost/test",
            allowed_tables={"users", "orders"},
        )

        # 不应抛出异常
        db._validate_table_name("users")
        db._validate_table_name("orders")

    @patch("df_test_framework.capabilities.databases.async_database.create_async_engine")
    @patch("df_test_framework.capabilities.databases.async_database.async_sessionmaker")
    def test_validate_table_not_allowed(self, mock_sessionmaker, mock_engine):
        """测试不在白名单的表名抛出异常"""
        db = AsyncDatabase(
            "mysql+aiomysql://user:pass@localhost/test",
            allowed_tables={"users", "orders"},
        )

        with pytest.raises(ValueError) as exc_info:
            db._validate_table_name("admin")

        assert "不在白名单中" in str(exc_info.value)

    @patch("df_test_framework.capabilities.databases.async_database.create_async_engine")
    @patch("df_test_framework.capabilities.databases.async_database.async_sessionmaker")
    def test_validate_table_empty_whitelist(self, mock_sessionmaker, mock_engine):
        """测试空白名单禁止所有表"""
        db = AsyncDatabase("mysql+aiomysql://user:pass@localhost/test", allowed_tables=set())

        with pytest.raises(ValueError) as exc_info:
            db._validate_table_name("users")

        assert "白名单为空集" in str(exc_info.value)

    @patch("df_test_framework.capabilities.databases.async_database.create_async_engine")
    @patch("df_test_framework.capabilities.databases.async_database.async_sessionmaker")
    def test_validate_table_no_whitelist(self, mock_sessionmaker, mock_engine):
        """测试无白名单时允许所有表"""
        db = AsyncDatabase("mysql+aiomysql://user:pass@localhost/test", allowed_tables=None)

        # 不应抛出异常
        db._validate_table_name("any_table")
        db._validate_table_name("users")


class TestAsyncDatabaseQueryMethods:
    """测试异步查询方法"""

    @pytest.fixture
    def mock_async_db(self):
        """创建 mock 异步数据库"""
        with (
            patch("df_test_framework.capabilities.databases.async_database.create_async_engine"),
            patch(
                "df_test_framework.capabilities.databases.async_database.async_sessionmaker"
            ) as mock_sessionmaker,
        ):
            # 创建 mock session
            mock_session = AsyncMock()
            mock_session_factory = MagicMock(return_value=mock_session)
            mock_sessionmaker.return_value = mock_session_factory

            db = AsyncDatabase("mysql+aiomysql://user:pass@localhost/test")
            db._mock_session = mock_session
            yield db

    @pytest.mark.asyncio
    async def test_query_one_found(self, mock_async_db):
        """测试 query_one 查询到数据"""
        # Mock 查询结果
        mock_row = MagicMock()
        mock_row._mapping = {"id": 1, "name": "Alice"}
        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_async_db._mock_session.execute = AsyncMock(return_value=mock_result)

        result = await mock_async_db.query_one("SELECT * FROM users WHERE id = :id", {"id": 1})

        assert result == {"id": 1, "name": "Alice"}

    @pytest.mark.asyncio
    async def test_query_one_not_found(self, mock_async_db):
        """测试 query_one 未查询到数据"""
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_async_db._mock_session.execute = AsyncMock(return_value=mock_result)

        result = await mock_async_db.query_one("SELECT * FROM users WHERE id = :id", {"id": 999})

        assert result is None

    @pytest.mark.asyncio
    async def test_query_all(self, mock_async_db):
        """测试 query_all 查询多条数据"""
        # Mock 查询结果
        mock_rows = [
            MagicMock(_mapping={"id": 1, "name": "Alice"}),
            MagicMock(_mapping={"id": 2, "name": "Bob"}),
        ]
        mock_result = MagicMock()
        mock_result.fetchall.return_value = mock_rows
        mock_async_db._mock_session.execute = AsyncMock(return_value=mock_result)

        result = await mock_async_db.query_all("SELECT * FROM users")

        assert len(result) == 2
        assert result[0] == {"id": 1, "name": "Alice"}
        assert result[1] == {"id": 2, "name": "Bob"}

    @pytest.mark.asyncio
    async def test_query_all_empty(self, mock_async_db):
        """测试 query_all 空结果"""
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_async_db._mock_session.execute = AsyncMock(return_value=mock_result)

        result = await mock_async_db.query_all("SELECT * FROM users WHERE status = 0")

        assert result == []


class TestAsyncDatabaseExecuteMethods:
    """测试异步执行方法"""

    @pytest.fixture
    def mock_async_db(self):
        """创建 mock 异步数据库"""
        with (
            patch("df_test_framework.capabilities.databases.async_database.create_async_engine"),
            patch(
                "df_test_framework.capabilities.databases.async_database.async_sessionmaker"
            ) as mock_sessionmaker,
        ):
            mock_session = AsyncMock()
            mock_session_factory = MagicMock(return_value=mock_session)
            mock_sessionmaker.return_value = mock_session_factory

            db = AsyncDatabase("mysql+aiomysql://user:pass@localhost/test")
            db._mock_session = mock_session
            yield db

    @pytest.mark.asyncio
    async def test_execute_update(self, mock_async_db):
        """测试 execute 执行更新"""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_async_db._mock_session.execute = AsyncMock(return_value=mock_result)

        rowcount = await mock_async_db.execute(
            "UPDATE users SET name = :name WHERE id = :id", {"name": "Bob", "id": 1}
        )

        assert rowcount == 1

    @pytest.mark.asyncio
    async def test_execute_delete(self, mock_async_db):
        """测试 execute 执行删除"""
        mock_result = MagicMock()
        mock_result.rowcount = 3
        mock_async_db._mock_session.execute = AsyncMock(return_value=mock_result)

        rowcount = await mock_async_db.execute(
            "DELETE FROM users WHERE status = :status", {"status": 0}
        )

        assert rowcount == 3


class TestAsyncDatabaseCRUDMethods:
    """测试异步 CRUD 方法"""

    @pytest.fixture
    def mock_async_db(self):
        """创建 mock 异步数据库"""
        with (
            patch("df_test_framework.capabilities.databases.async_database.create_async_engine"),
            patch(
                "df_test_framework.capabilities.databases.async_database.async_sessionmaker"
            ) as mock_sessionmaker,
        ):
            mock_session = AsyncMock()
            mock_session_factory = MagicMock(return_value=mock_session)
            mock_sessionmaker.return_value = mock_session_factory

            db = AsyncDatabase("mysql+aiomysql://user:pass@localhost/test")
            db._mock_session = mock_session
            yield db

    @pytest.mark.asyncio
    async def test_insert(self, mock_async_db):
        """测试 insert 插入数据"""
        mock_result = MagicMock()
        mock_result.lastrowid = 1
        mock_async_db._mock_session.execute = AsyncMock(return_value=mock_result)

        last_id = await mock_async_db.insert("users", {"name": "Alice", "age": 25})

        assert last_id == 1
        # 验证 SQL 调用
        mock_async_db._mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update(self, mock_async_db):
        """测试 update 更新数据"""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_async_db._mock_session.execute = AsyncMock(return_value=mock_result)

        rowcount = await mock_async_db.update("users", 1, {"age": 26})

        assert rowcount == 1

    @pytest.mark.asyncio
    async def test_delete(self, mock_async_db):
        """测试 delete 删除数据"""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_async_db._mock_session.execute = AsyncMock(return_value=mock_result)

        rowcount = await mock_async_db.delete("users", 1)

        assert rowcount == 1


class TestAsyncDatabaseClose:
    """测试关闭连接"""

    @pytest.mark.asyncio
    async def test_close(self):
        """测试 close 关闭连接"""
        with (
            patch(
                "df_test_framework.capabilities.databases.async_database.create_async_engine"
            ) as mock_create_engine,
            patch("df_test_framework.capabilities.databases.async_database.async_sessionmaker"),
        ):
            mock_engine = AsyncMock()
            mock_create_engine.return_value = mock_engine

            db = AsyncDatabase("mysql+aiomysql://user:pass@localhost/test")
            await db.close()

            mock_engine.dispose.assert_called_once()


# =============================================================================
# EventBus 集成测试 (v4.0.0)
# =============================================================================


class TestAsyncDatabaseEventBusIntegration:
    """测试异步数据库 EventBus 事件发布"""

    @pytest.fixture
    def event_bus_and_events(self):
        """创建事件总线和事件收集器"""
        event_bus = EventBus()
        collected_events = []

        async def collect_event(event):
            collected_events.append(event)

        event_bus.subscribe(DatabaseQueryStartEvent, collect_event)
        event_bus.subscribe(DatabaseQueryEndEvent, collect_event)
        event_bus.subscribe(DatabaseQueryErrorEvent, collect_event)

        return event_bus, collected_events

    @pytest.fixture
    def async_db_with_eventbus(self, event_bus_and_events):
        """创建带 EventBus 的异步数据库"""
        from df_test_framework.bootstrap import ProviderRegistry, RuntimeContext
        from df_test_framework.infrastructure.config import FrameworkSettings
        from df_test_framework.infrastructure.logging import logger

        event_bus, _ = event_bus_and_events

        runtime = RuntimeContext(
            settings=FrameworkSettings(app_name="test"),
            logger=logger,
            providers=ProviderRegistry(providers={}),
            event_bus=event_bus,
        )

        with (
            patch("df_test_framework.capabilities.databases.async_database.create_async_engine"),
            patch(
                "df_test_framework.capabilities.databases.async_database.async_sessionmaker"
            ) as mock_sessionmaker,
        ):
            mock_session = AsyncMock()
            mock_session_factory = MagicMock(return_value=mock_session)
            mock_sessionmaker.return_value = mock_session_factory

            db = AsyncDatabase("mysql+aiomysql://user:pass@localhost/test", runtime=runtime)
            db._mock_session = mock_session
            yield db

    @pytest.mark.asyncio
    async def test_query_publishes_events(self, async_db_with_eventbus, event_bus_and_events):
        """测试查询操作发布事件"""
        import asyncio

        _, collected_events = event_bus_and_events

        # Mock 查询结果
        mock_row = MagicMock()
        mock_row._mapping = {"id": 1, "name": "Alice"}
        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        async_db_with_eventbus._mock_session.execute = AsyncMock(return_value=mock_result)

        await async_db_with_eventbus.query_one("SELECT * FROM users WHERE id = :id", {"id": 1})

        # 等待事件循环处理 pending 任务
        await asyncio.sleep(0)

        # 验证发布了开始和结束事件
        assert len(collected_events) == 2

        start_event = collected_events[0]
        end_event = collected_events[1]

        assert isinstance(start_event, DatabaseQueryStartEvent)
        assert start_event.operation == "SELECT"

        assert isinstance(end_event, DatabaseQueryEndEvent)
        assert end_event.operation == "SELECT"

        # 验证 correlation_id 关联
        assert start_event.correlation_id == end_event.correlation_id

    @pytest.mark.asyncio
    async def test_error_publishes_error_event(self, async_db_with_eventbus, event_bus_and_events):
        """测试查询失败发布错误事件"""
        import asyncio

        _, collected_events = event_bus_and_events

        async_db_with_eventbus._mock_session.execute = AsyncMock(
            side_effect=Exception("Database error")
        )

        with pytest.raises(Exception, match="Database error"):
            await async_db_with_eventbus.query_one("SELECT * FROM users WHERE id = :id", {"id": 1})

        # 等待事件循环处理 pending 任务
        await asyncio.sleep(0)

        # 应该有开始事件和错误事件
        assert len(collected_events) == 2

        start_event = collected_events[0]
        error_event = collected_events[1]

        assert isinstance(start_event, DatabaseQueryStartEvent)
        assert isinstance(error_event, DatabaseQueryErrorEvent)
        assert "Database error" in error_event.error_message

        # 验证 correlation_id 关联
        assert start_event.correlation_id == error_event.correlation_id
