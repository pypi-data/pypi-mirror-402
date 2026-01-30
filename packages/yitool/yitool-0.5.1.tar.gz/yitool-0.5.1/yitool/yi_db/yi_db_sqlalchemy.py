from __future__ import annotations

from time import sleep
from typing import Any

from pymysql import OperationalError
from sqlalchemy import MetaData, Table, create_engine, inspect, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker

from yitool.const import __ENV__
from yitool.enums import DB_TYPE
from yitool.log import logger
from yitool.utils.dict_utils import DictUtils
from yitool.utils.env_utils import EnvUtils
from yitool.utils.url_utils import UrlUtils
from yitool.yi_db._abc import AbcYiDB


class YiDB(AbcYiDB):
    """数据库工具，支持同步和异步引擎"""

    _connection: AsyncConnection | Any = None
    _engine: AsyncEngine | Engine = None
    _slave_db: YiDB | None = None
    _tasks_db: YiDB | None = None
    _datasource: Any | None = None
    _is_async: bool = False
    _is_mock: bool = False

    def __init__(self, engine: AsyncEngine | Engine, max_retries: int = 3):
        self._engine = engine
        self._connection = None
        self._slave_db = None
        self._tasks_db = None
        self._datasource = None
        self._max_retries = max_retries

        # 检查引擎类型，避免每次方法调用都重复检查
        from sqlalchemy.ext.asyncio import AsyncEngine
        self._is_async = isinstance(engine, AsyncEngine)

        # 检测是否是模拟对象（通过检查是否有 spec 属性或 _spec_class）
        self._is_mock = hasattr(engine, "_spec_class") or hasattr(engine, "spec")

    # 同步和异步兼容的方法实现
    def connect(self):
        """连接数据库（支持同步和异步调用）"""
        import asyncio

        # 同步引擎或模拟对象，直接调用 connect
        if not self._is_async or self._is_mock:
            if self.closed:
                self._connection = self._engine.connect()
            return self._connection

        # 异步引擎，检查事件循环
        try:
            asyncio.get_running_loop()
            # 如果有，返回协程对象，让调用者自己 await
            return self._connect_async()
        except RuntimeError:
            # 如果没有，使用新的事件循环运行
            return asyncio.run(self._connect_async())

    async def _connect_async(self):
        """异步连接数据库"""
        if self.closed:
            self._connection = await self._engine.connect()
        return self._connection

    def close(self):
        """关闭数据库连接（支持同步和异步调用）"""
        import asyncio

        from sqlalchemy.ext.asyncio import AsyncConnection

        # 检测是否是异步连接
        is_async_connection = isinstance(self._connection, AsyncConnection)

        # 同步连接或模拟对象，直接调用 close
        if not is_async_connection or self._is_mock:
            try:
                if self._connection and hasattr(self._connection, "closed") and not self._connection.closed:
                    self._connection.close()
            except Exception as err:
                logger.error(f"close db connection error: {err}")
            return

        # 异步连接，检查事件循环
        try:
            asyncio.get_running_loop()
            return self._close_async()
        except RuntimeError:
            return asyncio.run(self._close_async())

    async def _close_async(self):
        """异步关闭数据库连接"""
        try:
            if self._connection and not self._connection.closed:
                await self._connection.close()
        except Exception as err:
            logger.error(f"close db connection error: {err}")

    def execute(self, query: str, params: dict[str, Any] | None = None, retry_times: int = 3) -> Any:
        """执行 SQL 查询（支持同步和异步调用）"""
        params = params or {}

        # 同步引擎，直接执行
        if not self._is_async or self._is_mock:
            return self._execute_sync(query, params, retry_times)

        # 异步引擎，检查事件循环
        import asyncio
        try:
            asyncio.get_running_loop()
            return self._execute_async(query, params, retry_times)
        except RuntimeError:
            return asyncio.run(self._execute_async(query, params, retry_times))

    def _execute_sync(self, query: str, params: dict[str, Any] | None = None, retry_times: int | None = None) -> Any:
        """同步执行 SQL 查询"""
        # 使用实例配置的重试次数，或方法参数提供的重试次数
        max_retries = retry_times if retry_times is not None else self._max_retries
        params = params or {}

        # 预编译SQL语句，提高执行效率
        compiled_query = text(query)

        try:
            # 如果已经有活跃的连接并且在事务中，使用该连接
            if not self.closed and hasattr(self._connection, "in_transaction") and self._connection.in_transaction():
                result = self._connection.execute(compiled_query, params)
                # 事务中的操作由外部控制提交/回滚
                return result
            # 否则使用新连接
            else:
                with self._engine.connect() as conn:
                    result = conn.execute(compiled_query, params)
                    conn.commit()
                    return result
        except Exception as err:
            logger.error(f"execute sql error (query: {query}): {err}")
            # 检查是否在事务中，如果在事务中则不dispose引擎，否则dispose
            if not (not self.closed and hasattr(self._connection, "in_transaction") and self._connection.in_transaction()):
                self._engine.dispose()
            sleep(3)
            if max_retries <= 0:
                raise
            return self._execute_sync(query, params, retry_times=max_retries-1)

    async def _execute_async(self, query: str, params: dict[str, Any] | None = None, retry_times: int | None = None) -> Any:
        """异步执行 SQL 查询"""
        # 使用实例配置的重试次数，或方法参数提供的重试次数
        max_retries = retry_times if retry_times is not None else self._max_retries
        params = params or {}

        # 预编译SQL语句，提高执行效率
        compiled_query = text(query)

        try:
            # 如果已经有活跃的连接并且在事务中，使用该连接
            if not self.closed and hasattr(self._connection, "in_transaction") and self._connection.in_transaction():
                result = await self._connection.execute(compiled_query, params)
                # 事务中的操作由外部控制提交/回滚
                return result
            # 否则使用新连接
            else:
                async with self._engine.connect() as conn:
                    result = await conn.execute(compiled_query, params)
                    await conn.commit()
                    return result
        except Exception as err:
            logger.error(f"execute sql error (query: {query}): {err}")
            # 检查是否在事务中，如果在事务中则不dispose引擎，否则dispose
            if not (not self.closed and hasattr(self._connection, "in_transaction") and self._connection.in_transaction()):
                await self._engine.dispose()
            import asyncio
            await asyncio.sleep(3)
            if max_retries <= 0:
                raise
            return await self._execute_async(query, params, retry_times=max_retries-1)

    def read(self, query: str, schema_overrides: dict | None = None, retry_times: int = 3) -> list[dict[str, Any]]:
        """从数据库读取数据（支持同步和异步调用）

        Args:
            query: SQL查询语句
            schema_overrides: 查询参数
            retry_times: 重试次数

        Returns:
            查询结果列表
        """
        # 同步引擎，直接执行
        if not self._is_async or self._is_mock:
            result = self._read_sync(query, schema_overrides, retry_times)
        else:
            # 异步引擎，检查事件循环
            import asyncio
            try:
                asyncio.get_running_loop()
                result = self._read_async(query, schema_overrides, retry_times)
            except RuntimeError:
                result = asyncio.run(self._read_async(query, schema_overrides, retry_times))
        
        return result

    def _read_sync(self, query: str, schema_overrides: dict | None = None, retry_times: int | None = None) -> list[dict[str, Any]]:
        """同步从数据库读取数据"""
        # 使用实例配置的重试次数，或方法参数提供的重试次数
        max_retries = retry_times if retry_times is not None else self._max_retries
        try:
            result = []
            params = schema_overrides or {}
            compiled_query = text(query)

            # 如果已经有活跃的连接并且在事务中，使用该连接
            # 否则使用新连接
            if not self.closed and hasattr(self._connection, "in_transaction") and self._connection.in_transaction():
                # 使用现有连接
                cursor = self._connection.execute(compiled_query, params)
                columns = cursor.keys()
                result = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
            else:
                # 使用新连接
                with self._engine.connect() as conn:
                    cursor = conn.execute(compiled_query, params)
                    columns = cursor.keys()
                    result = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
            return result
        except Exception as err:
            logger.error(f"read from db error (query: {query}): {err}")
            # 检查是否在事务中，如果在事务中则不dispose引擎，否则dispose
            if not (not self.closed and hasattr(self._connection, "in_transaction") and self._connection.in_transaction()):
                self._engine.dispose()
            sleep(3)
            if max_retries <= 0:
                return []
            return self._read_sync(query, schema_overrides, retry_times=max_retries-1)

    async def _read_async(self, query: str, schema_overrides: dict | None = None, retry_times: int | None = None) -> list[dict[str, Any]]:
        """异步从数据库读取数据"""
        # 使用实例配置的重试次数，或方法参数提供的重试次数
        max_retries = retry_times if retry_times is not None else self._max_retries
        try:
            result = []
            params = schema_overrides or {}
            compiled_query = text(query)

            # 如果已经有活跃的连接并且在事务中，使用该连接
            # 否则使用新连接
            if not self.closed and hasattr(self._connection, "in_transaction") and self._connection.in_transaction():
                # 使用现有连接
                cursor = await self._connection.execute(compiled_query, params)
                columns = cursor.keys()
                result = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
            else:
                # 使用新连接
                async with self._engine.connect() as conn:
                    cursor = await conn.execute(compiled_query, params)
                    columns = cursor.keys()
                    result = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
            return result
        except Exception as err:
            logger.error(f"read from db error (query: {query}): {err}")
            # 检查是否在事务中，如果在事务中则不dispose引擎，否则dispose
            if not (not self.closed and hasattr(self._connection, "in_transaction") and self._connection.in_transaction()):
                await self._engine.dispose()
            import asyncio
            await asyncio.sleep(3)
            if max_retries <= 0:
                return []
            return await self._read_async(query, schema_overrides, retry_times=max_retries-1)

    def write(self, data: list[dict[str, Any]] | Any, table_name: str, if_table_exists: str = "append", retry_times: int = 3, batch_size: int = 1000) -> int:
        """写入数据库表（支持同步和异步调用）"""
        # 同步引擎，直接执行
        if not self._is_async or self._is_mock:
            return self._write_sync(data, table_name, if_table_exists, retry_times, batch_size)

        # 异步引擎，检查事件循环
        import asyncio
        try:
            asyncio.get_running_loop()
            return self._write_async(data, table_name, if_table_exists, retry_times, batch_size)
        except RuntimeError:
            return asyncio.run(self._write_async(data, table_name, if_table_exists, retry_times, batch_size))

    def _write_sync(self, data: list[dict[str, Any]] | Any, table_name: str, if_table_exists: str = "append", retry_times: int | None = None, batch_size: int = 1000) -> int:
        """同步写入数据库表，支持批量操作优化"""
        num = 0
        # 使用实例配置的重试次数，或方法参数提供的重试次数
        max_retries = retry_times if retry_times is not None else self._max_retries

        try:
            if isinstance(data, list):
                if not data:
                    return 0

                if isinstance(data[0], dict):
                    # 批量插入字典列表，优化为分批处理
                    # 对于所有数据库类型，都使用新连接以确保一致性
                    with self._engine.connect() as conn:
                        # 获取表结构
                        metadata = MetaData()
                        table = Table(table_name, metadata, autoload_with=conn)

                        # 获取表的所有列名
                        table_columns = [column.name for column in table.columns]

                        if if_table_exists == "replace":
                            # 清空表
                            delete_stmt = table.delete()
                            delete_result = conn.execute(delete_stmt)
                            conn.commit()
                            logger.info(f"Deleted {delete_result.rowcount} rows for replace operation")

                        # 分批插入，避免内存占用过高
                        total_inserted = 0
                        for i in range(0, len(data), batch_size):
                            batch_data = data[i:i+batch_size]

                            # 过滤数据，只保留表中存在的列
                            filtered_batch = []
                            for item in batch_data:
                                filtered_item = {k: v for k, v in item.items() if k in table_columns}
                                filtered_batch.append(filtered_item)

                            result = conn.execute(table.insert().values(filtered_batch))
                            conn.commit()
                            total_inserted += result.rowcount
                        
                        num = total_inserted
                else:
                    # 支持ORM模型实例，优化为分批处理
                    # ORM实例使用Session，不支持事务连接共享
                    session = self.get_session()()
                    try:
                        if if_table_exists == "replace":
                            # 清空表
                            session.execute(select(type(data[0])).delete())
                            session.commit()

                        # 分批添加，避免内存占用过高
                        for i in range(0, len(data), batch_size):
                            batch_data = data[i:i+batch_size]
                            session.add_all(batch_data)
                            session.commit()
                            session.flush()  # 清空session，释放内存
                            session.expunge_all()  # 清除所有实例
                            num += len(batch_data)
                    finally:
                        session.close()
            else:
                # 单个ORM实例
                session = self.get_session()()
                try:
                    session.add(data)
                    session.commit()
                    num = 1
                finally:
                    session.close()
        except OperationalError as db_error:
            logger.error(f"write to db error (table: {table_name}): {db_error}")
            # 检查是否在事务中，如果在事务中则不dispose引擎，否则dispose
            if not (not self.closed and hasattr(self._connection, "in_transaction") and self._connection.in_transaction()):
                self._engine.dispose()
            sleep(3)
            if max_retries <= 0:
                return num
            return self._write_sync(data, table_name, if_table_exists=if_table_exists, retry_times=max_retries-1, batch_size=batch_size)
        except Exception as err:
            logger.error(f"write to db error (table: {table_name}): {err}")
            # 检查是否在事务中，如果在事务中则不dispose引擎，否则dispose
            if not (not self.closed and hasattr(self._connection, "in_transaction") and self._connection.in_transaction()):
                self._engine.dispose()
            sleep(3)
            if max_retries <= 0:
                return num
            return self._write_sync(data, table_name, if_table_exists=if_table_exists, retry_times=max_retries-1, batch_size=batch_size)
        return num

    async def _write_async(self, data: list[dict[str, Any]] | Any, table_name: str, if_table_exists: str = "append", retry_times: int | None = None, batch_size: int = 1000) -> int:
        """异步写入数据库表，支持批量操作优化"""
        num = 0
        # 使用实例配置的重试次数，或方法参数提供的重试次数
        max_retries = retry_times if retry_times is not None else self._max_retries

        try:
            if isinstance(data, list):
                if not data:
                    return 0

                if isinstance(data[0], dict):
                    # 批量插入字典列表，优化为分批处理
                    # 对于所有数据库类型，都使用新连接以避免协程重用问题
                    async with self._engine.connect() as conn:
                        # 获取表结构
                        def sync_get_table(conn):
                            metadata = MetaData()
                            table = Table(table_name, metadata, autoload_with=conn)
                            return table
                        table = await conn.run_sync(sync_get_table)

                        # 获取表的所有列名
                        table_columns = [column.name for column in table.columns]

                        if if_table_exists == "replace":
                            # 清空表
                            delete_result = await conn.execute(table.delete())
                            await conn.commit()
                            logger.info(f"Deleted {delete_result.rowcount} rows for replace operation")

                        # 分批插入，避免内存占用过高
                        total_inserted = 0
                        for i in range(0, len(data), batch_size):
                            batch_data = data[i:i+batch_size]

                            # 过滤数据，只保留表中存在的列
                            filtered_batch = []
                            for item in batch_data:
                                filtered_item = {k: v for k, v in item.items() if k in table_columns}
                                filtered_batch.append(filtered_item)

                            result = await conn.execute(table.insert().values(filtered_batch))
                            await conn.commit()
                            total_inserted += result.rowcount
                        
                        num = total_inserted
                else:
                    # 支持ORM模型实例，优化为分批处理
                    # ORM实例使用Session，不支持事务连接共享
                    # 创建新的会话工厂来避免协程重用问题
                    async_session_factory = self.get_session()
                    async with async_session_factory() as session:
                        if if_table_exists == "replace":
                            # 清空表
                            delete_stmt = select(type(data[0]))
                            await session.execute(delete_stmt.delete())
                            await session.commit()

                        # 分批添加，避免内存占用过高
                        for i in range(0, len(data), batch_size):
                            batch_data = data[i:i+batch_size]
                            session.add_all(batch_data)
                            await session.commit()
                            await session.flush()  # 清空session，释放内存
                            session.expunge_all()  # 清除所有实例
                            num += len(batch_data)
            else:
                # 单个ORM实例
                # 创建新的会话工厂来避免协程重用问题
                async_session_factory = self.get_session()
                async with async_session_factory() as session:
                    session.add(data)
                    await session.commit()
                    num = 1
        except OperationalError as db_error:
            logger.error(f"write to db error (table: {table_name}): {db_error}")
            # 检查是否在事务中，如果在事务中则不dispose引擎，否则dispose
            if not (not self.closed and hasattr(self._connection, "in_transaction") and self._connection.in_transaction()):
                await self._engine.dispose()
            import asyncio
            await asyncio.sleep(3)
            if max_retries <= 0:
                return num
            return await self._write_async(data, table_name, if_table_exists=if_table_exists, retry_times=max_retries-1, batch_size=batch_size)
        except Exception as err:
            logger.error(f"write to db error (table: {table_name}): {err}")
            # 检查是否在事务中，如果在事务中则不dispose引擎，否则dispose
            if not (not self.closed and hasattr(self._connection, "in_transaction") and self._connection.in_transaction()):
                await self._engine.dispose()
            import asyncio
            await asyncio.sleep(3)
            if max_retries <= 0:
                return num
            return await self._write_async(data, table_name, if_table_exists=if_table_exists, retry_times=max_retries-1, batch_size=batch_size)
        return num

    def begin(self) -> None:
        """开始事务（支持同步和异步调用）"""
        # 同步引擎，直接执行
        if not self._is_async or self._is_mock:
            if self.closed:
                self.connect()
            if hasattr(self._connection, "in_transaction") and not self._connection.in_transaction():
                self._connection.begin()
            return

        # 异步引擎，检查事件循环
        import asyncio
        try:
            asyncio.get_running_loop()
            return self._begin_async()
        except RuntimeError:
            return asyncio.run(self._begin_async())

    async def _begin_async(self) -> None:
        """异步开始事务"""
        if self.closed:
            await self._connect_async()
        if not self._connection.in_transaction():
            await self._connection.begin()

    def commit(self) -> None:
        """提交事务（支持同步和异步调用）"""
        # 同步引擎，直接执行
        if not self._is_async or self._is_mock:
            if not self.closed and hasattr(self._connection, "in_transaction") and self._connection.in_transaction():
                self._connection.commit()
            return

        # 异步引擎，检查事件循环
        import asyncio
        try:
            asyncio.get_running_loop()
            return self._commit_async()
        except RuntimeError:
            return asyncio.run(self._commit_async())

    async def _commit_async(self) -> None:
        """异步提交事务"""
        if not self.closed and self._connection.in_transaction():
            await self._connection.commit()

    def rollback(self) -> None:
        """回滚事务（支持同步和异步调用）"""
        # 同步引擎，直接执行
        if not self._is_async or self._is_mock:
            if not self.closed and hasattr(self._connection, "in_transaction") and self._connection.in_transaction():
                self._connection.rollback()
            return

        # 异步引擎，检查事件循环
        import asyncio
        try:
            asyncio.get_running_loop()
            return self._rollback_async()
        except RuntimeError:
            return asyncio.run(self._rollback_async())

    async def _rollback_async(self) -> None:
        """异步回滚事务"""
        if not self.closed and self._connection.in_transaction():
            await self._connection.rollback()

    def add(self, instance: Any) -> None:
        """添加单个 ORM 实例（支持同步和异步调用）"""
        # 同步引擎，直接执行
        if not self._is_async or self._is_mock:
            session = self.get_session()()
            try:
                session.add(instance)
                session.commit()
            finally:
                session.close()
            return

        # 异步引擎，检查事件循环
        import asyncio
        try:
            asyncio.get_running_loop()
            return self._add_async(instance)
        except RuntimeError:
            return asyncio.run(self._add_async(instance))

    async def _add_async(self, instance: Any) -> None:
        """异步添加单个 ORM 实例"""
        async_session = self.get_session()
        async with async_session() as session:
            session.add(instance)
            await session.commit()

    def add_all(self, instances: list[Any]) -> None:
        """添加多个 ORM 实例（支持同步和异步调用）"""
        # 同步引擎，直接执行
        if not self._is_async or self._is_mock:
            session = self.get_session()()
            try:
                session.add_all(instances)
                session.commit()
            finally:
                session.close()
            return

        # 异步引擎，检查事件循环
        import asyncio
        try:
            asyncio.get_running_loop()
            return self._add_all_async(instances)
        except RuntimeError:
            return asyncio.run(self._add_all_async(instances))

    async def _add_all_async(self, instances: list[Any]) -> None:
        """异步添加多个 ORM 实例"""
        async_session = self.get_session()
        async with async_session() as session:
            session.add_all(instances)
            await session.commit()

    def query(self, model: Any, *criteria: Any, **filters: Any) -> list[Any]:
        """使用 ORM 模型查询数据（支持同步和异步调用）"""
        # 同步引擎，直接执行
        if not self._is_async or self._is_mock:
            session = self.get_session()()
            try:
                query = select(model)
                if criteria:
                    query = query.filter(*criteria)
                if filters:
                    query = query.filter_by(**filters)
                result = session.execute(query)
                return result.scalars().all()
            finally:
                session.close()
            return

        # 异步引擎，检查事件循环
        import asyncio
        try:
            asyncio.get_running_loop()
            return self._query_async(model, *criteria, **filters)
        except RuntimeError:
            return asyncio.run(self._query_async(model, *criteria, **filters))

    async def _query_async(self, model: Any, *criteria: Any, **filters: Any) -> list[Any]:
        """异步使用 ORM 模型查询数据"""
        async_session = self.get_session()
        async with async_session() as session:
            query = select(model)
            if criteria:
                query = query.filter(*criteria)
            if filters:
                query = query.filter_by(**filters)
            result = await session.execute(query)
            return result.scalars().all()

    def exists(self, table_name: str) -> bool:
        """检查表是否存在（支持同步和异步调用）"""
        # 同步引擎，直接执行
        if not self._is_async or self._is_mock:
            inspector = inspect(self._engine)
            return table_name in inspector.get_table_names()

        # 异步引擎，检查事件循环
        import asyncio
        try:
            asyncio.get_running_loop()
            return self._exists_async(table_name)
        except RuntimeError:
            return asyncio.run(self._exists_async(table_name))

    async def _exists_async(self, table_name: str) -> bool:
        """异步检查表是否存在"""
        async with self._engine.connect() as conn:
            def sync_exists(conn):
                inspector = inspect(conn)
                return table_name in inspector.get_table_names()
            return await conn.run_sync(sync_exists)

    def columns(self, table_name: str) -> list:
        """获取表的所有列名（支持同步和异步调用）"""
        # 同步引擎，直接执行
        if not self._is_async or self._is_mock:
            if not self.exists(table_name):
                return []
            inspector = inspect(self._engine)
            return inspector.get_columns(table_name)

        # 异步引擎，检查事件循环
        import asyncio
        try:
            asyncio.get_running_loop()
            return self._columns_async(table_name)
        except RuntimeError:
            return asyncio.run(self._columns_async(table_name))

    async def _columns_async(self, table_name: str) -> list:
        """异步获取表的所有列名"""
        if not await self._exists_async(table_name):
            return []
        async with self._engine.connect() as conn:
            def sync_columns(conn):
                inspector = inspect(conn)
                return inspector.get_columns(table_name)
            return await conn.run_sync(sync_columns)

    def column_names(self, table_name: str) -> list[str] | None | Any:
        """获取表的所有列名（支持同步和异步调用）"""
        # 同步引擎，直接执行
        if not self._is_async or self._is_mock:
            columns = self.columns(table_name)
            if columns is None:
                return None
            return [col["name"] for col in columns]

        # 异步引擎，检查事件循环
        import asyncio
        try:
            asyncio.get_running_loop()
            # 如果在事件循环中，返回协程对象让调用者等待
            return self._column_names_async(table_name)
        except RuntimeError:
            # 否则直接运行
            return asyncio.run(self._column_names_async(table_name))

    async def _column_names_async(self, table_name: str) -> list[str] | None:
        """异步获取表的所有列名"""
        columns = await self.columns(table_name)
        if columns is None:
            return None
        return [col["name"] for col in columns]

    def primary_key(self, table_name: str) -> list[str] | None | Any:
        """获取表的主键列名（支持同步和异步调用）"""
        # 同步引擎，直接执行
        if not self._is_async or self._is_mock:
            if not self.exists(table_name):
                return None
            inspector = inspect(self._engine)
            pk = inspector.get_pk_constraint(table_name)
            return pk.get("constrained_columns", []) if pk else []

        # 异步引擎，检查事件循环
        import asyncio
        try:
            asyncio.get_running_loop()
            return self._primary_key_async(table_name)
        except RuntimeError:
            return asyncio.run(self._primary_key_async(table_name))

    async def _primary_key_async(self, table_name: str) -> list[str] | None:
        """异步获取表的主键列名"""
        if not await self._exists_async(table_name):
            return None
        async with self._engine.connect() as conn:
            def sync_pk(conn):
                inspector = inspect(conn)
                pk = inspector.get_pk_constraint(table_name)
                return pk.get("constrained_columns", []) if pk else []
            return await conn.run_sync(sync_pk)

    def execute_many(self, query: str, params_list: list[dict[str, Any]] | None = None, retry_times: int | None = None) -> Any:
        """批量执行 SQL 查询，提高批量操作效率（支持同步和异步调用）

        Args:
            query: SQL查询语句
            params_list: 查询参数列表
            retry_times: 重试次数

        Returns:
            查询结果
        """
        if not params_list:
            return None

        # 同步引擎，直接执行
        if not self._is_async or self._is_mock:
            return self._execute_many_sync(query, params_list, retry_times)

        # 异步引擎，检查事件循环
        import asyncio
        try:
            asyncio.get_running_loop()
            return self._execute_many_async(query, params_list, retry_times)
        except RuntimeError:
            return asyncio.run(self._execute_many_async(query, params_list, retry_times))

    def _execute_many_sync(self, query: str, params_list: list[dict[str, Any]] | None = None, retry_times: int | None = None) -> Any:
        """同步批量执行 SQL 查询，提高批量操作效率"""
        if not params_list:
            return None

        # 使用实例配置的重试次数，或方法参数提供的重试次数
        max_retries = retry_times if retry_times is not None else self._max_retries

        # 预编译SQL语句
        compiled_query = text(query)

        try:
            # 检查是否有活跃的连接并且在事务中
            in_transaction = not self.closed and hasattr(self._connection, "in_transaction") and self._connection.in_transaction()
            conn = self._connection if in_transaction else self._engine.connect()

            try:
                # SQLAlchemy的Connection对象没有executemany方法，使用execute处理批量参数
                result = conn.execute(compiled_query, params_list)
                if not in_transaction:
                    conn.commit()
                return result
            finally:
                if not in_transaction:
                    conn.close()
        except Exception as err:
            logger.error(f"execute_many sql error (query: {query}): {err}")
            # 检查是否在事务中，如果在事务中则不dispose引擎，否则dispose
            if not (not self.closed and hasattr(self._connection, "in_transaction") and self._connection.in_transaction()):
                self._engine.dispose()
            sleep(3)
            if max_retries <= 0:
                raise
            return self._execute_many_sync(query, params_list, retry_times=max_retries-1)

    @property
    def engine(self) -> AsyncEngine | Engine:
        return self._engine

    @property
    def connection(self) -> AsyncConnection | Any:
        return self._connection

    @property
    def closed(self) -> bool:
        return self._connection is None or (hasattr(self._connection, "closed") and self._connection.closed)

    def get_session(self) -> sessionmaker:
        """获取 SQLAlchemy ORM 会话工厂，根据引擎类型返回同步或异步会话"""
        from sqlalchemy.orm import Session

        if self._is_async:
            return sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )
        else:
            return sessionmaker(
                self._engine,
                class_=Session,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )

    @property
    def inspector(self) -> Inspector:
        """获取数据库检查器"""
        # 同步引擎或模拟对象，直接调用 inspect
        if not self._is_async or self._is_mock:
            return inspect(self._engine)

        # 异步引擎，使用 run_sync
        def sync_inspect(engine):
            return inspect(engine)
        import asyncio
        return asyncio.run(self._engine.run_sync(sync_inspect))

    @property
    def metadata(self) -> MetaData:
        """获取数据库元数据"""
        # SQLAlchemy 2.0+ 不再支持在 MetaData 构造函数中使用 bind 参数
        return MetaData()

    @property
    def tables(self) -> dict[str, Table]:
        """获取数据库所有表"""
        meta = self.metadata

        # 模拟对象或同步引擎，直接调用 reflect
        if not self._is_async or self._is_mock:
            # 对于模拟对象或同步引擎，直接反射
            meta.reflect(bind=self._engine)
            return meta.tables

        # 异步引擎，使用 run_sync
        async def sync_reflect(engine):
            meta.reflect(bind=engine)
            return meta.tables
        import asyncio
        return asyncio.run(self._engine.run_sync(sync_reflect))

    async def _execute_many_async(self, query: str, params_list: list[dict[str, Any]] | None = None, retry_times: int | None = None) -> Any:
        """异步批量执行 SQL 查询，提高批量操作效率"""
        if not params_list:
            return None

        # 使用实例配置的重试次数，或方法参数提供的重试次数
        max_retries = retry_times if retry_times is not None else self._max_retries

        # 预编译SQL语句
        compiled_query = text(query)

        try:
            # 检查是否有活跃的连接并且在事务中
            in_transaction = not self.closed and self._connection.in_transaction()
            conn = self._connection if in_transaction else await self._engine.connect()

            try:
                # SQLAlchemy的Connection对象没有executemany方法，使用execute处理批量参数
                result = await conn.execute(compiled_query, params_list)
                if not in_transaction:
                    await conn.commit()
                return result
            finally:
                if not in_transaction:
                    await conn.close()
        except Exception as err:
            logger.error(f"execute_many sql error (query: {query}): {err}")
            # 检查是否在事务中，如果在事务中则不dispose引擎，否则dispose
            if not (not self.closed and self._connection.in_transaction()):
                await self._engine.dispose()
            import asyncio
            await asyncio.sleep(3)
            if max_retries <= 0:
                raise
            return await self._execute_many_async(query, params_list, retry_times=max_retries-1)

    @staticmethod
    def load_env_values(values: dict[str, str], db_type: str = DB_TYPE.MYSQL.value) -> dict[str, str]:
        db_prefix = db_type.upper()
        return {
            "username": DictUtils.get_value_or_raise(values, f"{db_prefix}_USERNAME"),
            "password": DictUtils.get_value_or_raise(values, f"{db_prefix}_PASSWORD"),
            "host": DictUtils.get_value_or_raise(values, f"{db_prefix}_HOST"),
            "port": DictUtils.get_value_or_raise(values, f"{db_prefix}_PORT"),
        }

    @staticmethod
    def create_engine(
        database: str | None = None,
        db_type_value: str = DB_TYPE.MYSQL.value,
        env_path: str = __ENV__,
        charset: str | None = None,
        config: Any | None = None
    ) -> Engine:
        """创建数据库引擎

        支持两种方式创建引擎：
        1. 从环境变量创建（传统方式）
        2. 从 DatabaseConfig 创建（推荐方式，支持连接池配置）
        """
        if config:
            # 从 DatabaseConfig 创建引擎
            from yitool.yi_config.database import DatabaseConfig
            if isinstance(config, DatabaseConfig):
                logger.debug(f"Creating engine from DatabaseConfig: {config.url}")
                # 检查数据库类型，SQLite不支持某些连接池参数
                is_sqlite = "sqlite" in config.url.lower()
                
                engine_kwargs = {
                    "pool_size": config.pool_size,
                    "pool_recycle": config.pool_recycle,
                    "pool_pre_ping": True,  # 连接池预检测，确保连接有效
                    "echo": False,  # 关闭SQL日志，提高性能
                    "echo_pool": False  # 关闭连接池日志，提高性能
                }
                
                # 只对非SQLite数据库添加这些参数
                if not is_sqlite:
                    engine_kwargs["max_overflow"] = config.max_overflow
                    engine_kwargs["pool_timeout"] = config.pool_timeout
                
                return create_engine(config.url, **engine_kwargs)
            else:
                raise TypeError(f"Expected DatabaseConfig, got {type(config).__name__}")

        # 传统方式：从环境变量创建
        if not DB_TYPE.has(db_type_value):
            raise ValueError(f"不支持的数据库类型: {db_type_value}")

        if not database:
            raise ValueError("Database name is required when not using DatabaseConfig")

        values = EnvUtils.dotenv_values(env_path)
        db_values = YiDB.load_env_values(values, db_type_value)
        db_url = UrlUtils.url_from_db_type(db_type_value)(**db_values, database=database)
        logger.debug(f"Connecting to database with URL: {db_url}")

        # 检查是否是SQLite数据库
        is_sqlite = "sqlite" in db_url.lower()

        # 优化连接池配置，提高性能和可靠性
        engine_kwargs = {
            "pool_size": 10,  # 默认连接池大小
            "pool_recycle": 3600,  # 连接回收时间
            "pool_pre_ping": True,  # 连接池预检测，确保连接有效
            "echo": False,  # 关闭SQL日志，提高性能
            "echo_pool": False  # 关闭连接池日志，提高性能
        }

        # 只对非SQLite数据库添加这些参数
        if not is_sqlite:
            engine_kwargs["max_overflow"] = 20  # 最大溢出连接数
            engine_kwargs["pool_timeout"] = 30  # 连接超时时间

        if db_type_value == DB_TYPE.MSSQL.value:
            if charset is not None:
                engine_kwargs["connect_args"] = {"charset": charset}
            else:
                engine_kwargs["connect_args"] = {"charset": "utf8"}

        return create_engine(db_url, **engine_kwargs)

    @classmethod
    def from_env(cls, database: str, db_type_value: str = DB_TYPE.MYSQL.value, env_path: str = __ENV__, charset: str | None = None) -> YiDB:
        engine = cls.create_engine(database, db_type_value, env_path, charset)
        return cls(engine)

    @classmethod
    def from_config(cls, config: Any) -> YiDB:
        """从 DatabaseConfig 创建 YiDB 实例

        Args:
            config: DatabaseConfig 对象，包含数据库连接信息和连接池配置

        Returns:
            YiDB 实例
        """
        from yitool.yi_config.database import DatabaseConfig
        if not isinstance(config, DatabaseConfig):
            raise TypeError(f"Expected DatabaseConfig, got {type(config).__name__}")
        engine = cls.create_engine(config=config)
        return cls(engine)

    @classmethod
    def from_datasource(cls, datasource: Any) -> YiDB:
        """从 DataSourceConfig 创建 YiDB 实例

        Args:
            datasource: DataSourceConfig 对象，包含主从等数据源配置

        Returns:
            YiDB 实例，其中包含主库连接，从库和任务库连接可通过属性访问
        """
        from yitool.yi_config.datasource import DataSourceConfig

        if not isinstance(datasource, DataSourceConfig):
            raise TypeError(f"Expected DataSourceConfig, got {type(datasource).__name__}")

        # 创建主库实例
        master_db = cls.from_config(datasource.master)
        master_db._datasource = datasource

        # 创建从库实例（如果有）
        if datasource.slave:
            master_db._slave_db = cls.from_config(datasource.slave)

        # 创建任务库实例（如果有）
        if datasource.tasks:
            master_db._tasks_db = cls.from_config(datasource.tasks)

        return master_db

    @property
    def slave(self) -> YiDB | None:
        """获取从库 YiDB 实例

        Returns:
            从库 YiDB 实例，如果没有配置从库则返回 None
        """
        return self._slave_db

    @property
    def tasks(self) -> YiDB | None:
        """获取任务库 YiDB 实例

        Returns:
            任务库 YiDB 实例，如果没有配置任务库则返回 None
        """
        return self._tasks_db

    @property
    def has_slave(self) -> bool:
        """是否配置了从库

        Returns:
            如果配置了从库则返回 True，否则返回 False
        """
        return self._slave_db is not None

    @property
    def has_tasks(self) -> bool:
        """是否配置了任务库

        Returns:
            如果配置了任务库则返回 True，否则返回 False
        """
        return self._tasks_db is not None
    
    def check_connection_health(self) -> bool:
        """检查数据库连接健康状态

        Returns:
            如果连接健康则返回True，否则返回False
        """
        try:
            # 执行一个简单的查询来测试连接
            test_query = "SELECT 1"
            if self._is_async:
                import asyncio
                try:
                    asyncio.get_running_loop()
                    self._execute_async(test_query)
                    return True
                except RuntimeError:
                    asyncio.run(self._execute_async(test_query))
                    return True
            else:
                self._execute_sync(test_query)
                return True
        except Exception as e:
            logger.error(f"Connection health check failed: {e}")
            return False
    
    def get_connection_pool_stats(self) -> dict:
        """获取连接池统计信息

        Returns:
            连接池统计信息字典
        """
        stats = {}
        try:
            # 检查引擎是否有连接池
            if hasattr(self._engine, "pool"):
                pool = self._engine.pool
                if pool:
                    # 尝试获取连接池统计信息，处理不同SQLAlchemy版本的差异
                    try:
                        # 尝试使用方法调用获取统计信息
                        if hasattr(pool, "size"):
                            if callable(pool.size):
                                stats["pool_size"] = pool.size()
                            else:
                                stats["pool_size"] = pool.size
                        if hasattr(pool, "overflow"):
                            if callable(pool.overflow):
                                stats["pool_overflow"] = pool.overflow()
                            else:
                                stats["pool_overflow"] = pool.overflow
                        if hasattr(pool, "checkedout"):
                            if callable(pool.checkedout):
                                stats["pool_checked_out"] = pool.checkedout()
                            else:
                                stats["pool_checked_out"] = pool.checkedout
                        if hasattr(pool, "checkedin"):
                            if callable(pool.checkedin):
                                stats["pool_checked_in"] = pool.checkedin()
                            else:
                                stats["pool_checked_in"] = pool.checkedin
                        if hasattr(pool, "invalid"):
                            if callable(pool.invalid):
                                stats["pool_invalid"] = pool.invalid()
                            else:
                                stats["pool_invalid"] = pool.invalid
                    except Exception:
                        # 如果获取详细统计信息失败，返回基本信息
                        stats = {
                            "pool_size": 0
                        }
        except Exception as e:
            logger.error(f"Failed to get connection pool stats: {e}")
        
        return stats
    
    def close_idle_connections(self) -> None:
        """关闭空闲连接，释放资源"""
        try:
            if hasattr(self._engine, "pool") and self._engine.pool:
                # 对于SQLAlchemy连接池，我们可以通过dispose来关闭所有连接
                # 注意：这会关闭所有连接，包括活跃连接
                # 在生产环境中，应该谨慎使用
                self._engine.dispose()
                logger.info("Connection pool disposed, all connections closed")
        except Exception as e:
            logger.error(f"Failed to close idle connections: {e}")
    
    def analyze_query_for_indexes(self, query: str) -> list[dict]:
        """分析SQL查询并建议适当的索引
        
        Args:
            query: SQL查询语句
            
        Returns:
            索引建议列表，每个建议包含表名、列名和索引类型
        """
        import re
        
        suggestions = []
        
        try:
            # 解析SQL查询，提取表名和WHERE子句中的列
            # 简单的正则表达式，实际应用中可能需要更复杂的解析
            table_pattern = re.compile(r"FROM\s+(\w+)", re.IGNORECASE)
            where_pattern = re.compile(r"WHERE\s+(.+)", re.IGNORECASE | re.DOTALL)
            
            table_match = table_pattern.search(query)
            where_match = where_pattern.search(query)
            
            if not table_match:
                logger.warning("Could not extract table name from query")
                return suggestions
                
            table_name = table_match.group(1)
            
            if not where_match:
                logger.info("No WHERE clause found, no index suggestions")
                return suggestions
                
            where_clause = where_match.group(1)
            
            # 提取WHERE子句中的列名
            # 简单的正则表达式，匹配常见的条件模式
            column_patterns = [
                re.compile(r"(\w+)\s*[=<>!]+", re.IGNORECASE),
                re.compile(r"(\w+)\s+IN", re.IGNORECASE),
                re.compile(r"(\w+)\s+LIKE", re.IGNORECASE),
                re.compile(r"(\w+)\s+BETWEEN", re.IGNORECASE)
            ]
            
            columns = set()
            for pattern in column_patterns:
                for match in pattern.finditer(where_clause):
                    columns.add(match.group(1))
            
            # 为每个列生成索引建议
            for column in columns:
                # 跳过可能的函数调用或表达式
                if "(" in column or ")" in column:
                    continue
                    
                suggestions.append({
                    "table": table_name,
                    "columns": [column],
                    "index_type": "BTREE",
                    "reason": f"Column used in WHERE clause: {column}"
                })
            
            # 检查是否有多个列的组合条件
            # 简单的实现，实际应用中可能需要更复杂的分析
            if len(columns) > 1:
                suggestions.append({
                    "table": table_name,
                    "columns": list(columns),
                    "index_type": "BTREE",
                    "reason": "Composite index for multiple columns in WHERE clause"
                })
                
            logger.info(f"Generated {len(suggestions)} index suggestions for query")
            
        except Exception as e:
            logger.error(f"Error analyzing query for indexes: {e}")
            
        return suggestions


# 延迟注册 YiDB 到工厂类，避免循环导入
try:
    from yitool.yi_db.yi_db import YiDBFactory, YiDBType
    YiDBFactory.register(YiDBType.SQLALCHEMY, YiDB)
except ImportError:
    pass
