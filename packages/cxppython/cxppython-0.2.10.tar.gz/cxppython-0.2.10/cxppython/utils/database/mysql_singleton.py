import time
import asyncio
import threading
from typing import Iterable, List, Type, Any, Union, Dict, Optional

from urllib.parse import urlparse, parse_qs
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError, DatabaseError, DisconnectionError, DBAPIError
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine

# 保持模型基类不变
try:
    from sqlalchemy.orm import DeclarativeBase
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base

    DeclarativeBase = declarative_base()

# 遵循您的要求，保留此导入
import cxppython as cc


class Base(DeclarativeBase):
    pass


# 定义模型类型，用于类型提示
ModelType = Type[Base]


class MysqlDBSingleton:
    _instance: Optional['MysqlDBSingleton'] = None
    _lock = threading.Lock()

    # --- 资源定义 ---
    engine: Optional[Any] = None
    session_factory: Optional[Any] = None
    async_engine: Optional[AsyncEngine] = None
    async_session_factory: Optional[Any] = None
    _async_engine_created: bool = False

    def __init__(self, mysql_config: Union[str, Dict]):
        if MysqlDBSingleton._instance is not None:
            raise Exception("这是一个单例类。请使用 MysqlDBSingleton.create() 来初始化。")

        # --- 初始化同步资源 ---
        self.engine = self._create_engine(mysql_config)
        self.session_factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            class_=Session
        )

        # 保存配置以供异步引擎使用
        self._mysql_config = mysql_config
        self._async_engine_created = False

        MysqlDBSingleton._instance = self
        cc.logging.info("MysqlDBSingleton 同步引擎已创建。")

    def _ensure_async_engine(self):
        """延迟创建异步引擎（线程安全）"""
        if not self._async_engine_created:
            with MysqlDBSingleton._lock:
                if not self._async_engine_created:
                    self.async_engine = self._create_async_engine(self._mysql_config)
                    self.async_session_factory = sessionmaker(
                        bind=self.async_engine,
                        expire_on_commit=False,
                        class_=AsyncSession
                    )
                    self._async_engine_created = True
                    cc.logging.info("MysqlDBSingleton 异步引擎已创建。")

    @staticmethod
    def create(mysql_config: Union[str, Dict],async_engine: bool = False) -> 'MysqlDBSingleton':
        """
        创建并初始化数据库单例。如果已存在，则什么也不做（幂等）。
        """
        if MysqlDBSingleton._instance is None:
            with MysqlDBSingleton._lock:
                if MysqlDBSingleton._instance is None:
                    instance = MysqlDBSingleton(mysql_config)

            if async_engine:
                instance._ensure_async_engine()
        return MysqlDBSingleton._instance

    @staticmethod
    def instance() -> 'MysqlDBSingleton':
        """获取单例实例。"""
        if MysqlDBSingleton._instance is None:
            raise Exception("数据库实例未初始化。请先调用 create()。")
        return MysqlDBSingleton._instance

    # --- 会话和连接 ---
    @staticmethod
    def session() -> Session:
        """获取一个同步 SQLAlchemy Session。"""
        return MysqlDBSingleton.instance().session_factory()

    @staticmethod
    def get_db_connection():
        """获取一个同步数据库连接。"""
        return MysqlDBSingleton.instance().engine.connect()

    @staticmethod
    def async_session() -> AsyncSession:
        """获取一个异步 SQLAlchemy AsyncSession。"""
        instance = MysqlDBSingleton.instance()
        instance._ensure_async_engine()
        return instance.async_session_factory()

    @staticmethod
    def get_async_db_connection():
        """获取一个异步数据库连接。"""
        instance = MysqlDBSingleton.instance()
        instance._ensure_async_engine()
        return instance.async_engine.connect()

    # --- 引擎创建与配置解析 ---
    def _create_engine(self, mysql_config: Union[str, Dict]):
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
                'connect_timeout': 60,
                'autocommit': True
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
            if not all([config_dict["user"], config_dict["password"], config_dict["host"], config_dict["database"]]):
                raise ValueError("MySQL 配置缺少必要字段：user, password, host, 或 database")
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
            if not all([config_dict["user"], config_dict["password"], config_dict["host"], config_dict["database"]]):
                raise ValueError("MySQL 配置缺少必要字段：user, password, host, 或 database")

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

    # --- 错误判断辅助函数 ---
    @staticmethod
    def _is_retriable_error(err: Exception) -> bool:
        """检查是否为可重试的数据库错误（连接断开或死锁）。"""
        # DBAPIError 且连接已失效
        if isinstance(err, DBAPIError) and getattr(err, "connection_invalidated", False):
            return True
        # 明确的断连错误
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
            # 1213 (deadlock), 1205 (lock wait timeout), 1040 (too many connections)
            # 1317 (query execution was interrupted)
            if error_code in (2006, 2013, 1213, 1205, 1040, 1317):
                return True

        return any(msg in error_msg for msg in retriable_messages)

    @staticmethod
    def _calculate_backoff_delay(attempt: int) -> float:
        """计算指数退避延迟"""
        return min(0.5 * (2 ** attempt), 5.0)  # 最大延迟5秒

    # --- 核心数据库操作 ---

    @staticmethod
    def add(value: Base, retries: int = 3) -> None:
        """[同步] 添加单个 ORM 对象。失败时会引发异常。"""
        for attempt in range(retries):
            try:
                with MysqlDBSingleton.session() as session, session.begin():
                    session.add(value)
                return
            except (OperationalError, DatabaseError, DBAPIError) as err:
                if MysqlDBSingleton._is_retriable_error(err) and attempt < retries - 1:
                    delay = MysqlDBSingleton._calculate_backoff_delay(attempt)
                    cc.logging.warning(f"[同步] add() 可重试错误，{attempt+1}/{retries}，延迟 {delay:.2f}s")
                    time.sleep(delay)
                    continue
                raise err

    @staticmethod
    async def async_add(value: Base, retries: int = 3) -> None:
        """[异步] 添加单个 ORM 对象。失败时会引发异常。"""
        for attempt in range(retries):
            try:
                async with MysqlDBSingleton.async_session() as session, session.begin():
                    session.add(value)
                return
            except (OperationalError, DatabaseError, DBAPIError) as err:
                if MysqlDBSingleton._is_retriable_error(err) and attempt < retries - 1:
                    delay = MysqlDBSingleton._calculate_backoff_delay(attempt)
                    cc.logging.warning(f"[异步] async_add() 可重试错误，{attempt+1}/{retries}，延迟 {delay:.2f}s")
                    await asyncio.sleep(delay)
                    continue
                raise err

    @staticmethod
    def bulk_save(objects: Iterable[Base], retries: int = 3) -> None:
        """[同步] 批量保存多个 ORM 对象。失败时会引发异常。"""
        objects_list = list(objects)  # 确保可以重复迭代
        for attempt in range(retries):
            try:
                with MysqlDBSingleton.session() as session, session.begin():
                    session.bulk_save_objects(objects_list)
                return
            except (OperationalError, DatabaseError, DBAPIError) as err:
                if MysqlDBSingleton._is_retriable_error(err) and attempt < retries - 1:
                    delay = MysqlDBSingleton._calculate_backoff_delay(attempt)
                    cc.logging.warning(f"[同步] bulk_save() 可重试错误，{attempt+1}/{retries}，延迟 {delay:.2f}s")
                    time.sleep(delay)
                    continue
                raise err

    @staticmethod
    async def async_bulk_save(objects: Iterable[Base], retries: int = 3) -> None:
        """[异步] 批量保存多个 ORM 对象。失败时会引发异常。"""
        objects_list = list(objects)  # 确保可以重复迭代
        for attempt in range(retries):
            try:
                async with MysqlDBSingleton.async_session() as session, session.begin():
                    session.add_all(objects_list)
                return
            except (OperationalError, DatabaseError) as err:
                if MysqlDBSingleton._is_retriable_error(err) and attempt < retries - 1:
                    delay = MysqlDBSingleton._calculate_backoff_delay(attempt)
                    cc.logging.warning(f"[异步] async_bulk_save() 可重试错误，{attempt+1}/{retries}，延迟 {delay:.2f}s")
                    await asyncio.sleep(delay)
                    continue
                raise err

    @staticmethod
    def batch_insert_records(
            session: Session, model: ModelType, data: List[Dict[str, Any]],
            batch_size: int = 1000, ignore_existing: bool = True,
            commit_per_batch: bool = True, retries: int = 3
    ) -> int:
        """[同步] 批量插入记录，可选择忽略已存在的记录。"""
        if not data:
            return 0

        total_inserted = 0
        stmt = mysql_insert(model)
        if ignore_existing:
            stmt = stmt.prefix_with("IGNORE")

        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            batch_stmt = stmt.values(batch)

            for attempt in range(retries):
                try:
                    result = session.execute(batch_stmt)
                    total_inserted += result.rowcount
                    if commit_per_batch:
                        session.commit()
                    break
                except (OperationalError, DatabaseError, DBAPIError) as e:
                    session.rollback()
                    if MysqlDBSingleton._is_retriable_error(e) and attempt < retries - 1:
                        delay = MysqlDBSingleton._calculate_backoff_delay(attempt)
                        cc.logging.warning(f"[同步] batch_insert_records 第 {i//batch_size+1} 批可重试错误，"
                                           f"{attempt+1}/{retries}，延迟 {delay:.2f}s")
                        time.sleep(delay)
                        continue
                    raise e
        return total_inserted

    @staticmethod
    async def async_batch_insert_records(
            session: AsyncSession, model: ModelType, data: List[Dict[str, Any]],
            batch_size: int = 1000, ignore_existing: bool = True,
            commit_per_batch: bool = True, retries: int = 3
    ) -> int:
        """[异步] 批量插入记录，可选择忽略已存在的记录。"""
        if not data:
            return 0

        total_inserted = 0
        stmt = mysql_insert(model)
        if ignore_existing:
            stmt = stmt.prefix_with("IGNORE")

        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            batch_stmt = stmt.values(batch)

            for attempt in range(retries):
                try:
                    result = await session.execute(batch_stmt)
                    total_inserted += result.rowcount
                    if commit_per_batch:
                        await session.commit()
                    break
                except (OperationalError, DatabaseError, DBAPIError) as e:
                    await session.rollback()
                    if MysqlDBSingleton._is_retriable_error(e) and attempt < retries - 1:
                        delay = MysqlDBSingleton._calculate_backoff_delay(attempt)
                        cc.logging.warning(f"[异步] async_batch_insert_records 第 {i//batch_size+1} 批可重试错误，"
                                           f"{attempt+1}/{retries}，延迟 {delay:.2f}s")
                        await asyncio.sleep(delay)
                        continue
                    raise e
        return total_inserted

    @staticmethod
    def batch_replace_records(
            session: Session, model: ModelType, data: List[Dict[str, Any]],
            update_fields: List[str], batch_size: int = 1000,
            commit_per_batch: bool = True, retries: int = 3
    ) -> int:
        """[同步] 批量插入或更新记录 (UPSERT)，依赖主键或唯一约束。"""
        if not data:
            return 0

        total_changed = 0
        stmt = mysql_insert(model)
        set_dict = {field: stmt.inserted[field] for field in update_fields}
        stmt = stmt.on_duplicate_key_update(**set_dict)

        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            batch_stmt = stmt.values(batch)
            for attempt in range(retries):
                try:
                    result = session.execute(batch_stmt)
                    total_changed += result.rowcount
                    if commit_per_batch:
                        session.commit()
                    break
                except (OperationalError, DatabaseError, DBAPIError) as e:
                    session.rollback()
                    if MysqlDBSingleton._is_retriable_error(e) and attempt < retries - 1:
                        delay = MysqlDBSingleton._calculate_backoff_delay(attempt)
                        cc.logging.warning(f"[同步] batch_replace_records 第 {i//batch_size+1} 批可重试错误，"
                                           f"{attempt+1}/{retries}，延迟 {delay:.2f}s")
                        time.sleep(delay)
                        continue
                    raise e
        return total_changed

    @staticmethod
    async def async_batch_replace_records(
            session: AsyncSession, model: ModelType, data: List[Dict[str, Any]],
            update_fields: List[str], batch_size: int = 1000,
            commit_per_batch: bool = True, retries: int = 3
    ) -> int:
        """[异步] 批量插入或更新记录 (UPSERT)，依赖主键或唯一约束。"""
        if not data:
            return 0

        total_changed = 0
        stmt = mysql_insert(model)
        set_dict = {field: stmt.inserted[field] for field in update_fields}
        stmt = stmt.on_duplicate_key_update(**set_dict)

        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            batch_stmt = stmt.values(batch)

            for attempt in range(retries):
                try:
                    result = await session.execute(batch_stmt)
                    total_changed += result.rowcount
                    if commit_per_batch:
                        await session.commit()
                    break
                except (OperationalError, DatabaseError, DBAPIError) as e:
                    await session.rollback()
                    if MysqlDBSingleton._is_retriable_error(e) and attempt < retries - 1:
                        delay = MysqlDBSingleton._calculate_backoff_delay(attempt)
                        cc.logging.warning(f"[异步] async_batch_replace_records 第 {i//batch_size+1} 批可重试错误，"
                                           f"{attempt+1}/{retries}，延迟 {delay:.2f}s")
                        await asyncio.sleep(delay)
                        continue
                    raise e
        return total_changed

    @staticmethod
    def run_cmd(session: Session, cmd: str,is_select: bool = False):
        """[同步] 执行一条 SQL 命令，返回结果或受影响的行数。"""
        try:
            result = session.execute(text(cmd))
            if is_select:
                return result.fetchall()
            else:
                session.commit()
                return result.rowcount
        except Exception as e:
            session.rollback()
            raise e

    @staticmethod
    async def async_run_cmd(session: AsyncSession, cmd: str,is_select: bool = False):
        """[异步] 执行一条 SQL 命令，返回结果或受影响的行数。"""
        try:
            result = await session.execute(text(cmd))
            if is_select:
                return result.fetchall()
            else:
                await session.commit()
                return result.rowcount
        except Exception as e:
            await session.rollback()
            raise e
            
    # --- 测试与清理 ---
    @staticmethod
    def test_connection() -> bool:
        """测试同步数据库连接。"""
        try:
            with MysqlDBSingleton.get_db_connection() as connection:
                result = connection.execute(text("SELECT 1")).scalar()
                if result == 1:
                    cc.logging.success(f"同步数据库连接成功! {MysqlDBSingleton.instance().engine.url}")
                    return True
        except Exception as e:
            cc.logging.error(f"同步数据库连接失败 (test_connection): {e}, {MysqlDBSingleton.instance().engine.url}", exc_info=True)
        return False

    @staticmethod
    async def async_test_connection() -> bool:
        """测试异步数据库连接。"""
        try:
            instance = MysqlDBSingleton.instance()
            instance._ensure_async_engine()
            async with MysqlDBSingleton.get_async_db_connection() as connection:
                result = await connection.execute(text("SELECT 1"))
                scalar_result = result.scalar_one()
                if scalar_result == 1:
                    cc.logging.success(f"异步数据库连接成功! 引擎: {instance.async_engine.url}")
                    return True
        except Exception as e:
            cc.logging.error(f"异步数据库连接失败 (async_test_connection): {e}, 引擎: {instance.async_engine.url}", exc_info=True)
        return False

    @staticmethod
    def close():
        """同步清理资源，关闭所有引擎。"""
        with MysqlDBSingleton._lock:
            instance = MysqlDBSingleton._instance
            if instance:
                if instance.engine:
                    instance.engine.dispose()
                    cc.logging.info("同步引擎已关闭。")
                if instance.async_engine:
                    cc.logging.warning("异步引擎无法在同步 close() 中安全关闭。请调用 `await MysqlDBSingleton.async_close()`。")
                MysqlDBSingleton._instance = None

    @staticmethod
    async def async_close():
        """异步方式关闭和清理所有资源。"""
        instance = MysqlDBSingleton._instance
        if instance:
            if instance.engine:
                instance.engine.dispose()
                cc.logging.info("同步引擎已关闭。")
            if instance.async_engine:
                await instance.async_engine.dispose()
                cc.logging.info("异步引擎已关闭。")
            MysqlDBSingleton._instance = None
