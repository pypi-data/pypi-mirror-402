"""异步数据库操作封装（v4.0.0）

基于 SQLAlchemy 2.0 AsyncEngine 和 AsyncSession
提供完整的异步数据库操作能力

v4.0.0 新增:
- AsyncDatabase: 完全异步的数据库客户端
- 性能提升：支持并发数据库操作
- 基于 sqlalchemy.ext.asyncio
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import Executable

from df_test_framework.core.events import (
    DatabaseQueryEndEvent,
    DatabaseQueryErrorEvent,
    DatabaseQueryStartEvent,
)
from df_test_framework.infrastructure.logging import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from df_test_framework.bootstrap.runtime import RuntimeContext

# 默认不限制表名 (开发/测试环境)
DEFAULT_ALLOWED_TABLES: set[str] | None = None


class AsyncDatabase:
    """
    异步数据库操作封装（v4.0.0）

    功能:
    - 提供异步数据库连接管理
    - 支持异步会话上下文管理
    - 提供常用的异步查询和执行方法
    - 性能提升：支持并发数据库操作

    使用示例:
        >>> # 基础使用
        >>> async_db = AsyncDatabase("mysql+aiomysql://user:pass@host/db")
        >>>
        >>> # 异步查询
        >>> users = await async_db.query_all("SELECT * FROM users WHERE age > :age", {"age": 18})
        >>>
        >>> # 异步插入
        >>> user_id = await async_db.insert("users", {"name": "Alice", "age": 25})
        >>>
        >>> # 并发查询（性能提升显著）
        >>> tasks = [
        ...     async_db.query_one("SELECT * FROM users WHERE id = :id", {"id": i})
        ...     for i in range(100)
        ... ]
        >>> results = await asyncio.gather(*tasks)
    """

    def __init__(
        self,
        connection_string: str,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        pool_pre_ping: bool = True,
        echo: bool = False,
        allowed_tables: set[str] | None = None,
        runtime: RuntimeContext | None = None,
    ):
        """
        初始化异步数据库连接

        Args:
            connection_string: 异步数据库连接字符串
                示例: mysql+aiomysql://user:password@host:port/database?charset=utf8mb4
                      postgresql+asyncpg://user:password@host:port/database
            pool_size: 连接池大小 (默认10)
            max_overflow: 连接池最大溢出数 (默认20)
            pool_timeout: 连接池超时时间(秒) (默认30)
            pool_recycle: 连接回收时间(秒) (默认3600)
            pool_pre_ping: 是否检测连接有效性 (默认True)
            echo: 是否打印SQL语句 (默认False)
            allowed_tables: 允许操作的表名白名单 (None表示允许所有表)
            runtime: RuntimeContext（包含 event_bus 和 scope）

        Note:
            v4.0.0: 完全异步化
            - 连接字符串必须使用异步驱动（aiomysql, asyncpg 等）
            - 所有方法都是异步的，需要 await 调用
        """
        self.connection_string = connection_string
        self._runtime = runtime
        self.allowed_tables = (
            allowed_tables if allowed_tables is not None else DEFAULT_ALLOWED_TABLES
        )

        # 创建异步数据库引擎
        self.engine: AsyncEngine = create_async_engine(
            connection_string,
            poolclass=NullPool,  # 异步推荐使用 NullPool
            pool_pre_ping=pool_pre_ping,
            echo=echo,
        )

        # 创建异步会话工厂
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

        # ObservabilityLogger
        from df_test_framework.infrastructure.logging.observability import db_logger

        self.obs_logger = db_logger()
        self._query_counter = 0

        logger.info(f"异步数据库连接已建立: {self._mask_connection_string()}")
        if self.allowed_tables is not None:
            if self.allowed_tables:
                logger.debug(f"表名白名单已启用, 允许的表: {self.allowed_tables}")
            else:
                logger.warning("表名白名单为空集, 禁止所有表操作")

    def _mask_connection_string(self) -> str:
        """隐藏连接字符串中的密码"""
        if "@" in self.connection_string:
            parts = self.connection_string.split("@")
            if ":" in parts[0]:
                user_pass = parts[0].split(":")
                return f"{user_pass[0]}:****@{parts[1]}"
        return self.connection_string

    def _generate_query_id(self) -> str:
        """生成查询ID（用于日志关联）"""
        self._query_counter += 1
        return f"query-{self._query_counter:03d}"

    def _publish_event(self, event: Any) -> None:
        """发布事件（v4.0.0: 同步发布，不阻塞异步流程）"""
        if self._runtime:
            try:
                self._runtime.publish_event(event)
            except Exception:
                pass  # 静默失败，不影响主流程

    def _validate_table_name(self, table: str) -> None:
        """验证表名是否在白名单中"""
        if self.allowed_tables is None:
            return

        if not self.allowed_tables:
            raise ValueError(
                f"表操作已禁用: 白名单为空集, 不允许操作任何表. 尝试操作的表: '{table}'"
            )

        if table not in self.allowed_tables:
            raise ValueError(f"表名 '{table}' 不在白名单中. 允许的表: {self.allowed_tables}")

    @staticmethod
    def _prepare_statement(sql: str | Executable) -> Executable:
        """将字符串SQL或可执行语句统一转换为 Executable 对象"""
        if isinstance(sql, str):
            return text(sql)
        return sql

    @asynccontextmanager
    async def session(self):
        """
        获取异步数据库会话上下文管理器

        使用方式:
            async with db.session() as session:
                result = await session.execute(text("SELECT * FROM table"))

        Yields:
            AsyncSession: SQLAlchemy异步会话对象
        """
        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"异步数据库操作失败,已回滚: {str(e)}")
            raise
        finally:
            await session.close()

    async def execute(
        self,
        sql: str | Executable,
        params: dict[str, Any] | None = None,
    ) -> int:
        """
        异步执行SQL语句(INSERT/UPDATE/DELETE)

        Args:
            sql: SQL语句
            params: 参数字典

        Returns:
            影响的行数

        Example:
            >>> rowcount = await db.execute(
            ...     "UPDATE users SET age = :age WHERE id = :id",
            ...     {"age": 26, "id": 1}
            ... )
        """
        query_id = self._generate_query_id()

        # 从SQL中提取操作类型和表名
        sql_str = str(sql).strip().upper()
        operation = "EXECUTE"
        table_name = "unknown"

        for op in ["INSERT", "UPDATE", "DELETE"]:
            if sql_str.startswith(op):
                operation = op
                break

        if "INTO" in sql_str:
            parts = sql_str.split("INTO")[1].split()
            if parts:
                table_name = parts[0].strip()
        elif operation in ["UPDATE", "DELETE"]:
            keyword = "FROM" if operation == "DELETE" else operation
            if keyword in sql_str:
                parts = sql_str.split(keyword)[1].split()
                if parts:
                    table_name = parts[0].strip()

        async with self.session() as session:
            start_time = time.perf_counter()
            self.obs_logger.query_start(operation, table_name, query_id)

            start_event, correlation_id = DatabaseQueryStartEvent.create(
                operation=operation,
                table=table_name,
                sql=str(sql),
                params=params,
            )
            self._publish_event(start_event)

            try:
                statement = self._prepare_statement(sql)
                result = await session.execute(statement, params or {})
                rowcount = result.rowcount

                duration_ms = (time.perf_counter() - start_time) * 1000
                self.obs_logger.query_end(query_id, rowcount, duration_ms)

                end_event = DatabaseQueryEndEvent.create(
                    correlation_id=correlation_id,
                    operation=operation,
                    table=table_name,
                    sql=str(sql),
                    params=params,
                    duration_ms=duration_ms,
                    row_count=rowcount,
                )
                self._publish_event(end_event)

                return rowcount
            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                self.obs_logger.query_error(e, query_id)

                error_event = DatabaseQueryErrorEvent.create(
                    correlation_id=correlation_id,
                    operation=operation,
                    table=table_name,
                    sql=str(sql),
                    params=params,
                    error=e,
                    duration_ms=duration_ms,
                )
                self._publish_event(error_event)
                raise

    async def query_one(
        self,
        sql: str | Executable,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """
        异步查询单条记录

        Args:
            sql: SQL查询语句
            params: 参数字典

        Returns:
            单条记录的字典,如果没有结果则返回None

        Example:
            >>> user = await db.query_one(
            ...     "SELECT * FROM users WHERE id = :id",
            ...     {"id": 1}
            ... )
            >>> print(user["name"])
        """
        query_id = self._generate_query_id()

        sql_str = str(sql).strip().upper()
        table_name = "unknown"
        if "FROM" in sql_str:
            parts = sql_str.split("FROM")[1].split()
            if parts:
                table_name = parts[0].strip()

        async with self.session() as session:
            start_time = time.perf_counter()
            self.obs_logger.query_start("SELECT", table_name, query_id)

            start_event, correlation_id = DatabaseQueryStartEvent.create(
                operation="SELECT",
                table=table_name,
                sql=str(sql),
                params=params,
            )
            self._publish_event(start_event)

            try:
                statement = self._prepare_statement(sql)
                result = await session.execute(statement, params or {})
                row = result.fetchone()

                duration_ms = (time.perf_counter() - start_time) * 1000
                row_count = 1 if row else 0
                self.obs_logger.query_end(query_id, row_count, duration_ms)

                end_event = DatabaseQueryEndEvent.create(
                    correlation_id=correlation_id,
                    operation="SELECT",
                    table=table_name,
                    sql=str(sql),
                    params=params,
                    duration_ms=duration_ms,
                    row_count=row_count,
                )
                self._publish_event(end_event)

                if row:
                    return dict(row._mapping)
                return None
            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                self.obs_logger.query_error(e, query_id)

                error_event = DatabaseQueryErrorEvent.create(
                    correlation_id=correlation_id,
                    operation="SELECT",
                    table=table_name,
                    sql=str(sql),
                    params=params,
                    error=e,
                    duration_ms=duration_ms,
                )
                self._publish_event(error_event)
                raise

    async def query_all(
        self,
        sql: str | Executable,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        异步查询多条记录

        Args:
            sql: SQL查询语句
            params: 参数字典

        Returns:
            记录列表

        Example:
            >>> users = await db.query_all(
            ...     "SELECT * FROM users WHERE age > :age",
            ...     {"age": 18}
            ... )
            >>> for user in users:
            ...     print(user["name"])
        """
        query_id = self._generate_query_id()

        sql_str = str(sql).strip().upper()
        table_name = "unknown"
        if "FROM" in sql_str:
            parts = sql_str.split("FROM")[1].split()
            if parts:
                table_name = parts[0].strip()

        async with self.session() as session:
            start_time = time.perf_counter()
            self.obs_logger.query_start("SELECT", table_name, query_id)

            start_event, correlation_id = DatabaseQueryStartEvent.create(
                operation="SELECT",
                table=table_name,
                sql=str(sql),
                params=params,
            )
            self._publish_event(start_event)

            try:
                statement = self._prepare_statement(sql)
                result = await session.execute(statement, params or {})
                rows = result.fetchall()
                result_list = [dict(row._mapping) for row in rows]

                duration_ms = (time.perf_counter() - start_time) * 1000
                self.obs_logger.query_end(query_id, len(result_list), duration_ms)

                end_event = DatabaseQueryEndEvent.create(
                    correlation_id=correlation_id,
                    operation="SELECT",
                    table=table_name,
                    sql=str(sql),
                    params=params,
                    duration_ms=duration_ms,
                    row_count=len(result_list),
                )
                self._publish_event(end_event)

                return result_list
            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                self.obs_logger.query_error(e, query_id)

                error_event = DatabaseQueryErrorEvent.create(
                    correlation_id=correlation_id,
                    operation="SELECT",
                    table=table_name,
                    sql=str(sql),
                    params=params,
                    error=e,
                    duration_ms=duration_ms,
                )
                self._publish_event(error_event)
                raise

    async def insert(
        self,
        table: str,
        data: dict[str, Any],
    ) -> int:
        """
        异步插入单条记录

        Args:
            table: 表名
            data: 要插入的数据字典

        Returns:
            插入的行ID（如果数据库支持）

        Example:
            >>> user_id = await db.insert("users", {
            ...     "name": "Alice",
            ...     "age": 25,
            ...     "email": "alice@example.com"
            ... })
        """
        self._validate_table_name(table)

        columns = ", ".join(data.keys())
        placeholders = ", ".join(f":{k}" for k in data.keys())
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        async with self.session() as session:
            query_id = self._generate_query_id()
            start_time = time.perf_counter()
            self.obs_logger.query_start("INSERT", table, query_id)

            start_event, correlation_id = DatabaseQueryStartEvent.create(
                operation="INSERT",
                table=table,
                sql=sql,
                params=data,
            )
            self._publish_event(start_event)

            try:
                result = await session.execute(text(sql), data)
                # 尝试获取最后插入的ID
                last_id = result.lastrowid if hasattr(result, "lastrowid") else 0

                duration_ms = (time.perf_counter() - start_time) * 1000
                self.obs_logger.query_end(query_id, 1, duration_ms)

                end_event = DatabaseQueryEndEvent.create(
                    correlation_id=correlation_id,
                    operation="INSERT",
                    table=table,
                    sql=sql,
                    params=data,
                    duration_ms=duration_ms,
                    row_count=1,
                )
                self._publish_event(end_event)

                return last_id
            except IntegrityError as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                self.obs_logger.query_error(e, query_id)

                error_event = DatabaseQueryErrorEvent.create(
                    correlation_id=correlation_id,
                    operation="INSERT",
                    table=table,
                    sql=sql,
                    params=data,
                    error=e,
                    duration_ms=duration_ms,
                )
                self._publish_event(error_event)

                logger.error(f"插入数据违反唯一性约束: {e}")
                raise
            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                self.obs_logger.query_error(e, query_id)

                error_event = DatabaseQueryErrorEvent.create(
                    correlation_id=correlation_id,
                    operation="INSERT",
                    table=table,
                    sql=sql,
                    params=data,
                    error=e,
                    duration_ms=duration_ms,
                )
                self._publish_event(error_event)
                raise

    async def update(
        self,
        table: str,
        id_value: int,
        data: dict[str, Any],
        id_column: str = "id",
    ) -> int:
        """
        异步更新记录

        Args:
            table: 表名
            id_value: ID值
            data: 要更新的数据字典
            id_column: ID列名(默认"id")

        Returns:
            影响的行数

        Example:
            >>> affected = await db.update("users", 1, {"age": 26})
        """
        self._validate_table_name(table)

        set_clause = ", ".join(f"{k} = :{k}" for k in data.keys())
        sql = f"UPDATE {table} SET {set_clause} WHERE {id_column} = :_id_value"

        params = {**data, "_id_value": id_value}
        return await self.execute(sql, params)

    async def delete(
        self,
        table: str,
        id_value: int,
        id_column: str = "id",
    ) -> int:
        """
        异步删除记录

        Args:
            table: 表名
            id_value: ID值
            id_column: ID列名(默认"id")

        Returns:
            影响的行数

        Example:
            >>> affected = await db.delete("users", 1)
        """
        self._validate_table_name(table)

        sql = f"DELETE FROM {table} WHERE {id_column} = :id_value"
        return await self.execute(sql, {"id_value": id_value})

    async def close(self) -> None:
        """
        关闭异步数据库连接

        Example:
            >>> await db.close()
        """
        await self.engine.dispose()
        logger.info("异步数据库连接已关闭")


__all__ = ["AsyncDatabase"]
