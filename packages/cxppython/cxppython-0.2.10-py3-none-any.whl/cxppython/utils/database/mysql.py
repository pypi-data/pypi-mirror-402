import asyncio
import threading
import time
from typing import Iterable, List, Type, Any, Union, Dict, Optional
from urllib.parse import urlparse, parse_qs

from sqlalchemy import create_engine, text, Engine
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.exc import OperationalError, DatabaseError, DisconnectionError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

import cxppython as cc

logger = cc.logging


# 替换过时的 declarative_base
class Base(DeclarativeBase):
    pass


# 定义模型类型，用于类型提示
ModelType = Type[Base]


class MysqlDB:
    _instance: Optional['MysqlDB'] = None
    _lock = threading.Lock()

    def __init__(self, mysql_config: Union[str, Dict], async_engine: bool = False,singleton: bool = False):
        """
        初始化 MysqlDB 实例，支持单例和非单例模式。
        :param mysql_config: 数据库配置（字符串或字典，包含 user, password, host, port, database 等）
        :param singleton: 是否启用单例模式（默认 False）
        """
        if singleton:
            if MysqlDB._instance is not None:
                raise Exception("单例实例已存在。请使用 MysqlDB.instance() 或 MysqlDB.create()。")
            MysqlDB._instance = self

        # --- 初始化同步资源 ---
        self.engine = self._create_engine(mysql_config)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False, class_=Session)

        # 保存配置以供异步引擎使用
        self._mysql_config = mysql_config
        self.async_engine: Optional[AsyncEngine] = None
        self.async_session_factory: Optional[Any] = None
        self._async_engine_created: bool = False
        self._ctx_session: Optional[Session] = None
        self._async_ctx_session: Optional[AsyncSession] = None

        logger.info("MysqlDB 同步引擎已创建。")

        if async_engine:
            self._ensure_async_engine()

    # --- 上下文管理协议，便于 with 使用 ---
    def __enter__(self) -> Session:
        """支持 `with MysqlDB as session` 便捷获取会话。"""
        self._ctx_session = self.session_factory()
        return self._ctx_session

    def __exit__(self, exc_type, exc_val, exc_tb):
        session = self._ctx_session
        if session is None:
            return False
        try:
            if exc_type:
                if session.in_transaction():
                    session.rollback()
            else:
                if session.in_transaction():
                    session.commit()
        finally:
            session.close()
            self._ctx_session = None
        # 返回 False 以便异常向外继续传播
        return False

    async def __aenter__(self) -> AsyncSession:
        """支持 `async with MysqlDB as session`。"""
        self._ensure_async_engine()
        self._async_ctx_session = self.async_session_factory()
        return self._async_ctx_session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        session = self._async_ctx_session
        if session is None:
            return False
        try:
            if exc_type:
                if session.in_transaction():
                    await session.rollback()
            else:
                if session.in_transaction():
                    await session.commit()
        finally:
            await session.close()
            self._async_ctx_session = None
        return False

    def _ensure_async_engine(self):
        """延迟创建异步引擎（线程安全）"""
        if not self._async_engine_created:
            with MysqlDB._lock:
                if not self._async_engine_created:
                    self.async_engine = self._create_async_engine(self._mysql_config)
                    self.async_session_factory = sessionmaker(
                        bind=self.async_engine,
                        expire_on_commit=False,
                        class_=AsyncSession
                    )
                    self._async_engine_created = True
                    logger.info("MysqlDB 异步引擎已创建。")

    @staticmethod
    def create(mysql_config: Union[str, Dict]) -> 'MysqlDB':
        """
        创建单例实例。
        :param mysql_config: 数据库配置
        """
        if MysqlDB._instance is None:
            with MysqlDB._lock:
                if MysqlDB._instance is None:
                    MysqlDB(mysql_config, singleton=True)
        return MysqlDB._instance

    @staticmethod
    def instance() -> 'MysqlDB':
        """
        获取单例实例。
        :return: 单例 MysqlDB 实例
        """
        if MysqlDB._instance is None:
            raise Exception("数据库实例未初始化。请先调用 create()。")
        return MysqlDB._instance

    def _create_engine(self, mysql_config: Union[str, Dict]):
        """
        创建 SQLAlchemy 引擎。
        :param mysql_config: 数据库配置（字符串或字典）
        :return: SQLAlchemy 引擎
        """
        config_dict, engine_options = self._parse_config(mysql_config)

        # 默认引擎参数
        default_options = {
            'pool_size': 20,
            'max_overflow': 30,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
            'echo': False,
            'pool_timeout': 30,
            'connect_args': {
                'charset': 'utf8mb4',
                'connect_timeout': 60,
                'read_timeout': 60,
                'write_timeout': 60
            }
        }

        # 合并配置
        default_options.update(engine_options)

        return create_engine(
            'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'.format(**config_dict),
            **default_options
        )

    def _create_async_engine(self, mysql_config: Union[str, Dict]):
        """创建异步引擎"""
        config_dict, engine_options = self._parse_config(mysql_config)

        # 默认异步引擎参数
        default_options = {
            'pool_size': 20,
            'max_overflow': 30,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
            'echo': False,
            'pool_timeout': 30,
            'connect_args': {
                'charset': 'utf8mb4',
                'connect_timeout': 60
            }
        }

        # 移除同步特有的连接参数
        if 'connect_args' in engine_options:
            async_connect_args = engine_options['connect_args'].copy()
            async_connect_args.pop('read_timeout', None)
            async_connect_args.pop('write_timeout', None)
            engine_options['connect_args'] = async_connect_args

        # 合并配置
        default_options.update(engine_options)

        return create_async_engine(
            'mysql+aiomysql://{user}:{password}@{host}:{port}/{database}'.format(**config_dict),
            **default_options
        )

    def _parse_config(self, config: Union[str, Dict]) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """解析配置，返回连接参数和引擎选项"""
        engine_options = {}
        config_dict = {}

        if isinstance(config, str):
            if not config.startswith("mysql://"):
                config = f"mysql://{config}"
            parsed = urlparse(config)
            config_dict = {
                "user": parsed.username,
                "password": parsed.password,
                "host": parsed.hostname,
                "port": parsed.port or 3306,
                "database": parsed.path.lstrip("/")
            }
            query_params = parse_qs(parsed.query)
            if "echo" in query_params:
                engine_options["echo"] = query_params["echo"][0].lower() == "true"
        else:
            config_dict = {
                "user": config.get("user"),
                "password": config.get("password"),
                "host": config.get("host"),
                "port": config.get("port", 3306),
                "database": config.get("database")
            }

            # 提取引擎相关配置
            engine_keys = ['echo', 'pool_size', 'max_overflow', 'pool_recycle',
                           'pool_pre_ping', 'pool_timeout']
            for key in engine_keys:
                if key in config:
                    engine_options[key] = config[key]

            # 提取连接参数
            if 'connect_args' in config:
                engine_options['connect_args'] = config['connect_args']

        return config_dict, engine_options

    @staticmethod
    def _is_retriable_error(err: Exception) -> bool:
        """检查是否为可重试的数据库错误（连接断开或死锁）。"""
        if isinstance(err, DisconnectionError):
            return True

        if not isinstance(err, (OperationalError, DatabaseError)):
            return False

        error_msg = str(err).lower()
        # MySQL 常见的可重试错误
        retriable_messages = [
            "gone away", "lost connection", "connection reset",
            "deadlock", "lock wait timeout", "try restarting transaction"
        ]

        # 检查错误码
        if hasattr(err.orig, 'args') and err.orig.args:
            error_code = err.orig.args[0]
            # MySQL 错误码: 2006 (gone away), 2013 (lost connection),
            # 1213 (deadlock), 1205 (lock wait timeout)
            if error_code in (2006, 2013, 1213, 1205, 1040, 1317):
                return True

        return any(msg in error_msg for msg in retriable_messages)

    @staticmethod
    def _calculate_backoff_delay(attempt: int) -> float:
        """计算指数退避延迟"""
        return min(0.5 * (2 ** attempt), 5.0)  # 最大延迟5秒

    def session(self) -> Session:
        """
        获取一个新的 SQLAlchemy 会话。
        :return: SQLAlchemy 会话
        """
        return self.session_factory()

    def async_session(self) -> AsyncSession:
        """获取一个异步 SQLAlchemy AsyncSession。"""
        self._ensure_async_engine()
        return self.async_session_factory()

    def get_engine(self) -> Engine:
        """
        获取 SQLAlchemy 引擎。
        :return: SQLAlchemy 引擎
        """
        return self.engine

    def get_db_connection(self):
        """
        返回 SQLAlchemy 引擎的连接。
        :return: 数据库连接
        """
        return self.engine.connect()

    def get_async_db_connection(self):
        """获取一个异步数据库连接。"""
        self._ensure_async_engine()
        return self.async_engine.connect()

    def add(self, value: Base, retries: int = 3) -> Optional[Exception]:
        """
        添加单个对象到数据库。
        :param value: 要添加的对象
        :param retries: 重试次数
        :return: 异常（如果有）或 None
        """
        for attempt in range(retries):
            try:
                with self.session() as session, session.begin():
                    session.add(value)
                return None
            except (OperationalError, DatabaseError) as err:
                if self._is_retriable_error(err) and attempt < retries - 1:
                    delay = self._calculate_backoff_delay(attempt)
                    logger.warning(f"[同步] add() 出现可重试错误，重试 {attempt + 1}/{retries}... 延迟 {delay}s")
                    time.sleep(delay)
                    continue
                logger.error(f"添加对象失败: {err}")
                return err
        return Exception("重试后仍然添加失败")

    async def async_add(self, value: Base, retries: int = 3) -> Optional[Exception]:
        """
        [异步] 添加单个对象到数据库。
        :param value: 要添加的对象
        :param retries: 重试次数
        :return: 异常（如果有）或 None
        """
        for attempt in range(retries):
            try:
                async with self.async_session() as session, session.begin():
                    session.add(value)
                return None
            except (OperationalError, DatabaseError) as err:
                if self._is_retriable_error(err) and attempt < retries - 1:
                    delay = self._calculate_backoff_delay(attempt)
                    logger.warning(f"[异步] add() 出现可重试错误，重试 {attempt + 1}/{retries}... 延迟 {delay}s")
                    await asyncio.sleep(delay)
                    continue
                logger.error(f"异步添加对象失败: {err}")
                return err
        return Exception("重试后仍然添加失败")

    def bulk_save(self, objects: Iterable[Base], retries: int = 3) -> Optional[Exception]:
        """
        批量保存对象到数据库。
        :param objects: 要保存的对象列表
        :param retries: 重试次数
        :return: 异常（如果有）或 None
        """
        objects_list = list(objects)  # 确保可以重复迭代
        for attempt in range(retries):
            try:
                with self.session() as session, session.begin():
                    session.bulk_save_objects(objects_list)
                return None
            except (OperationalError, DatabaseError) as err:
                if self._is_retriable_error(err) and attempt < retries - 1:
                    delay = self._calculate_backoff_delay(attempt)
                    logger.warning(f"[同步] bulk_save() 出现可重试错误，重试 {attempt + 1}/{retries}... 延迟 {delay}s")
                    time.sleep(delay)
                    continue
                logger.error(f"批量保存对象失败: {err}")
                return err
        return Exception("重试后仍然批量保存失败")

    async def async_bulk_save(self, objects: Iterable[Base], retries: int = 3) -> Optional[Exception]:
        """
        [异步] 批量保存对象到数据库。
        :param objects: 要保存的对象列表
        :param retries: 重试次数
        :return: 异常（如果有）或 None
        """
        objects_list = list(objects)  # 确保可以重复迭代
        for attempt in range(retries):
            try:
                async with self.async_session() as session, session.begin():
                    session.add_all(objects_list)
                return None
            except (OperationalError, DatabaseError) as err:
                if self._is_retriable_error(err) and attempt < retries - 1:
                    delay = self._calculate_backoff_delay(attempt)
                    logger.warning(f"[异步] bulk_save() 出现可重试错误，重试 {attempt + 1}/{retries}... 延迟 {delay}s")
                    await asyncio.sleep(delay)
                    continue
                logger.error(f"异步批量保存对象失败: {err}")
                return err
        return Exception("重试后仍然批量保存失败")

    def test_connection(self) -> bool:
        """
        测试数据库连接。
        :return: 连接是否成功
        """
        try:
            with self.get_db_connection() as connection:
                result = connection.execute(text("SELECT 1")).scalar()
                if result == 1:
                    logger.success(f"同步数据库连接成功: {self.engine.url}")
                    return True
        except Exception as e:
            logger.error(f"同步数据库连接失败: {e}", exc_info=True)
        return False

    async def async_test_connection(self) -> bool:
        """
        [异步] 测试数据库连接。
        :return: 连接是否成功
        """
        try:
            self._ensure_async_engine()
            async with self.get_async_db_connection() as connection:
                result = await connection.execute(text("SELECT 1"))
                value = result.scalar()
                if value == 1:
                    logger.success(f"异步数据库连接成功: {self.async_engine.url}")
                    return True
        except Exception as e:
            logger.error(f"异步数据库连接失败: {e}", exc_info=True)
        return False

    def batch_insert_records(
            self,
            model: ModelType,
            data: List[Dict[str, Any]],
            batch_size: int = 1000,
            ignore_existing: bool = True,
            commit_per_batch: bool = True,  # 默认值改为 True
            retries: int = 3,
            delay: float = 1.0
    ) -> int:
        """
        批量插入记录。
        :param model: SQLAlchemy 模型类
        :param data: 批量插入的数据（字典列表）
        :param batch_size: 每批次处理的数据量
        :param ignore_existing: 是否忽略已存在的记录
        :param commit_per_batch: 是否每批次提交事务
        :param retries: 重试次数
        :param delay: 重试延迟（秒）
        :return: 插入的记录数
        """
        if not data:
            return 0

        total_inserted = 0
        with self.session() as session:
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                stmt = mysql_insert(model).values(batch)
                if ignore_existing:
                    stmt = stmt.prefix_with("IGNORE")

                for attempt in range(retries):
                    try:
                        result = session.execute(stmt)
                        total_inserted += result.rowcount
                        if commit_per_batch:
                            session.commit()
                        break
                    except (OperationalError, DatabaseError) as e:
                        session.rollback()
                        if self._is_retriable_error(e) and attempt < retries - 1:
                            logger.warning(f"[同步] batch_insert 批次 {i // batch_size + 1} 出现可重试错误，重试 {attempt + 1}/{retries}...")
                            time.sleep(delay)
                            continue
                        logger.error(f"批量插入失败，索引 {i}: {e}")
                        raise
        return total_inserted

    async def async_batch_insert_records(
            self,
            model: ModelType,
            data: List[Dict[str, Any]],
            batch_size: int = 1000,
            ignore_existing: bool = True,
            commit_per_batch: bool = True,  # 默认值改为 True
            retries: int = 3,
            delay: float = 1.0
    ) -> int:
        """
        [异步] 批量插入记录。
        """
        if not data:
            return 0

        total_inserted = 0
        async with self.async_session() as session:
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                stmt = mysql_insert(model).values(batch)
                if ignore_existing:
                    stmt = stmt.prefix_with("IGNORE")

                for attempt in range(retries):
                    try:
                        result = await session.execute(stmt)
                        total_inserted += result.rowcount
                        if commit_per_batch:
                            await session.commit()
                        break
                    except (OperationalError, DatabaseError) as e:
                        await session.rollback()
                        if self._is_retriable_error(e) and attempt < retries - 1:
                            logger.warning(f"[异步] batch_insert 批次 {i // batch_size + 1} 出现可重试错误，重试 {attempt + 1}/{retries}...")
                            await asyncio.sleep(delay)
                            continue
                        logger.error(f"异步批量插入失败，索引 {i}: {e}")
                        raise
        return total_inserted

    def batch_replace_records(
            self,
            model: ModelType,
            data: List[Dict[str, Any]],
            update_fields: List[str],
            batch_size: int = 1000,
            commit_per_batch: bool = True,  # 默认值改为 True
            retries_count: int = 3,
    ) -> int:
        """
        批量替换记录，支持联合唯一索引的冲突检测。
        :param model: SQLAlchemy 模型类
        :param data: 批量插入的数据（字典列表）
        :param update_fields: 需要更新的字段列表
        :param batch_size: 每批次处理的数据量
        :param commit_per_batch: 是否每批次提交事务
        :param retries_count: 死锁重试次数
        :param lock_table: 是否显式加表级锁（谨慎使用）
        :return: 受影响的记录数
        """
        if not data:
            return 0

        total_changed = 0
        with self.session() as session:
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                stmt = mysql_insert(model).values(batch)
                set_dict = {field: stmt.inserted[field] for field in update_fields}
                stmt = stmt.on_duplicate_key_update(**set_dict)

                for attempt in range(retries_count):
                    try:
                        result = session.execute(stmt)
                        total_changed += result.rowcount
                        if commit_per_batch:
                            session.commit()
                        break
                    except (OperationalError, DatabaseError) as e:
                        session.rollback()
                        if self._is_retriable_error(e) and attempt < retries_count - 1:
                            delay = self._calculate_backoff_delay(attempt)
                            logger.warning(f"[同步] batch_replace 批次 {i // batch_size + 1} 出现可重试错误，重试 {attempt + 1}/{retries_count}... 延迟 {delay}s")
                            time.sleep(delay)
                            continue
                        logger.error(f"批量替换失败，索引 {i}: {e}")
                        raise
        return total_changed

    async def async_batch_replace_records(
            self,
            model: ModelType,
            data: List[Dict[str, Any]],
            update_fields: List[str],
            batch_size: int = 1000,
            commit_per_batch: bool = True,  # 默认值改为 True
            retries_count: int = 3,
    ) -> int:
        """
        [异步] 批量替换记录，支持联合唯一索引的冲突检测。
        """
        if not data:
            return 0

        total_changed = 0
        async with self.async_session() as session:
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                stmt = mysql_insert(model).values(batch)
                set_dict = {field: stmt.inserted[field] for field in update_fields}
                stmt = stmt.on_duplicate_key_update(**set_dict)

                for attempt in range(retries_count):
                    try:
                        result = await session.execute(stmt)
                        total_changed += result.rowcount
                        if commit_per_batch:
                            await session.commit()
                        break
                    except (OperationalError, DatabaseError) as e:
                        await session.rollback()
                        if self._is_retriable_error(e) and attempt < retries_count - 1:
                            delay = self._calculate_backoff_delay(attempt)
                            logger.warning(f"[异步] batch_replace 批次 {i // batch_size + 1} 出现可重试错误，重试 {attempt + 1}/{retries_count}... 延迟 {delay}s")
                            await asyncio.sleep(delay)
                            continue
                        logger.error(f"异步批量替换失败，索引 {i}: {e}")
                        raise
        return total_changed

    def close(self):
        """
        清理资源，关闭引擎。
        """
        if self.engine:
            self.engine.dispose()
            logger.info("同步引擎已关闭。")
        if self.async_engine:
            logger.warning("异步引擎需要在异步上下文中关闭。请调用 `await async_close()` 进行正确清理。")
        if MysqlDB._instance == self:
            MysqlDB._instance = None

    async def async_close(self):
        """
        异步方式关闭和清理所有资源。
        """
        if self.engine:
            self.engine.dispose()
            logger.info("同步引擎已关闭。")
        if self.async_engine:
            await self.async_engine.dispose()
            logger.info("异步引擎已关闭。")
        if MysqlDB._instance == self:
            MysqlDB._instance = None

    # 静态方法，供单例模式调用
    @staticmethod
    def static_session() -> Session:
        """
        获取单例模式的会话。
        :return: SQLAlchemy 会话
        """
        return MysqlDB.instance().session()

    @staticmethod
    def static_async_session() -> AsyncSession:
        """获取单例模式的异步会话。"""
        return MysqlDB.instance().async_session()

    @staticmethod
    def static_get_db_connection():
        """
        获取单例模式的数据库连接。
        :return: 数据库连接
        """
        return MysqlDB.instance().get_db_connection()

    @staticmethod
    def static_get_async_db_connection():
        """获取单例模式的异步数据库连接。"""
        return MysqlDB.instance().get_async_db_connection()

    @staticmethod
    def static_add(value: Base, retries: int = 3) -> Optional[Exception]:
        """
        单例模式下添加单个对象。
        :param value: 要添加的对象
        :param retries: 重试次数
        :return: 异常（如果有）或 None
        """
        return MysqlDB.instance().add(value, retries)

    @staticmethod
    async def static_async_add(value: Base, retries: int = 3) -> Optional[Exception]:
        """单例模式下异步添加单个对象。"""
        return await MysqlDB.instance().async_add(value, retries)

    @staticmethod
    def static_bulk_save(objects: Iterable[Base], retries: int = 3) -> Optional[Exception]:
        """
        单例模式下批量保存对象。
        :param objects: 要保存的对象列表
        :param retries: 重试次数
        :return: 异常（如果有）或 None
        """
        return MysqlDB.instance().bulk_save(objects, retries)

    @staticmethod
    async def static_async_bulk_save(objects: Iterable[Base], retries: int = 3) -> Optional[Exception]:
        """单例模式下异步批量保存对象。"""
        return await MysqlDB.instance().async_bulk_save(objects, retries)

    @staticmethod
    def static_test_connection() -> bool:
        """
        单例模式下测试数据库连接。
        :return: 连接是否成功
        """
        return MysqlDB.instance().test_connection()

    @staticmethod
    async def static_async_test_connection() -> bool:
        """单例模式下异步测试数据库连接。"""
        return await MysqlDB.instance().async_test_connection()

    @staticmethod
    def static_batch_insert_records(
            model: ModelType,
            data: List[Dict[str, Any]],
            batch_size: int = 1000,
            ignore_existing: bool = True,
            commit_per_batch: bool = True,
            retries: int = 3,
            delay: float = 1.0
    ) -> int:
        """
        单例模式下批量插入记录。
        """
        return MysqlDB.instance().batch_insert_records(
            model, data, batch_size, ignore_existing, commit_per_batch, retries, delay
        )

    @staticmethod
    async def static_async_batch_insert_records(
            model: ModelType,
            data: List[Dict[str, Any]],
            batch_size: int = 1000,
            ignore_existing: bool = True,
            commit_per_batch: bool = True,
            retries: int = 3,
            delay: float = 1.0
    ) -> int:
        """单例模式下异步批量插入记录。"""
        return await MysqlDB.instance().async_batch_insert_records(
            model, data, batch_size, ignore_existing, commit_per_batch, retries, delay
        )

    @staticmethod
    def static_batch_replace_records(
            model: ModelType,
            data: List[Dict[str, Any]],
            update_fields: List[str],
            batch_size: int = 1000,
            commit_per_batch: bool = True,
            retries_count: int = 3,
            lock_table: bool = False
    ) -> int:
        """
        单例模式下批量替换记录。
        """
        return MysqlDB.instance().batch_replace_records(
            model, data, update_fields, batch_size, commit_per_batch, retries_count, lock_table
        )

    @staticmethod
    async def static_async_batch_replace_records(
            model: ModelType,
            data: List[Dict[str, Any]],
            update_fields: List[str],
            batch_size: int = 1000,
            commit_per_batch: bool = True,
            retries_count: int = 3,
            lock_table: bool = False
    ) -> int:
        """单例模式下异步批量替换记录。"""
        return await MysqlDB.instance().async_batch_replace_records(
            model, data, update_fields, batch_size, commit_per_batch, retries_count, lock_table
        )

    @staticmethod
    def static_close():
        """
        单例模式下关闭数据库连接。
        """
        instance = MysqlDB.instance()
        instance.close()

    @staticmethod
    async def static_async_close():
        """单例模式下异步关闭数据库连接。"""
        instance = MysqlDB.instance()
        await instance.async_close()
