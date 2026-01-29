from typing import Union, Dict, Any, List
from urllib.parse import quote_plus
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError
from threading import Lock
import cxppython as cc


class MongoDBSingleton:
    """MongoDB 单例类，用于管理 MongoDB 数据库连接"""
    __instance = None
    __connection_string = None

    def __new__(cls, *args, **kwargs):
        """实现单例模式"""
        if cls.__instance is None:
            # cc.logging.debug("Creating new MongoDBSingleton instance")
            cls.__instance = super(MongoDBSingleton, cls).__new__(cls)
        return cls.__instance

    @staticmethod
    def create(connection: Union[str, Dict[str, Any]], max_pool_size: int = 10, connect_timeout: int = 5000) -> 'MongoDBSingleton':
        """
        静态方法，用于创建 MongoDBSingleton 单例实例
        Args:
            connection: 连接字符串或配置字典
            max_pool_size: 连接池最大大小，默认为 10
            connect_timeout: 连接超时时间（毫秒），默认为 5000
        Returns:
            MongoDBSingleton: 单例实例
        Raises:
            ValueError: 如果连接参数无效
            PyMongoError: 如果连接初始化失败
        """
        if MongoDBSingleton.__instance is not None:
            cc.logging.debug("Returning existing MongoDBSingleton instance")
            return MongoDBSingleton.__instance

        # cc.logging.debug("Initializing MongoDB connection")
        try:
            if isinstance(connection, str):
                client = MongoClient(connection, maxPoolSize=max_pool_size, connectTimeoutMS=connect_timeout)
                MongoDBSingleton.__connection_string = connection
                parts = connection.split('/')
                if len(parts) < 4 or not parts[-1]:
                    raise ValueError("连接字符串中未指定数据库名称")
                db_name = parts[-1].split('?')[0]
            elif isinstance(connection, dict):
                client = MongoClient(
                    host=connection.get('host', 'localhost'),
                    port=connection.get('port', 27017),
                    username=connection.get('user'),
                    password=connection.get('password'),
                    maxPoolSize=max_pool_size,
                    connectTimeoutMS=connect_timeout
                )
                username = quote_plus(connection.get('user', '')) if connection.get('user') else None
                password = quote_plus(connection.get('password', '')) if connection.get('password') else None
                host = connection.get('host', 'localhost')
                port = connection.get('port', 27017)
                MongoDBSingleton.__connection_string = (
                    f"mongodb://{username}:{password}@{host}:{port}" if username and password
                    else f"mongodb://{host}:{port}"
                )
                db_name = connection.get('database')
                if not db_name:
                    raise ValueError("字典连接参数必须包含 'database' 字段")
            else:
                raise ValueError("连接参数必须是字符串或字典")

            # 初始化单例实例
            MongoDBSingleton.__instance = MongoDBSingleton.__new__(MongoDBSingleton)
            MongoDBSingleton.__instance._init_connection(client, db_name)
            # cc.logging.debug("MongoDBSingleton initialized successfully")
            return MongoDBSingleton.__instance
        except Exception as e:
            cc.logging.error(f"Failed to initialize MongoDBSingleton: {str(e)}")
            # 确保异常不会导致半初始化状态
            MongoDBSingleton.__instance = None
            MongoDBSingleton.__connection_string = None
            raise

    @staticmethod
    def instance() -> 'MongoDBSingleton':
        """
        获取当前单例实例
        Returns:
            MongoDBSingleton: 单例实例
        Raises:
            RuntimeError: 如果单例尚未初始化
        """
        if MongoDBSingleton.__instance is None:
            raise RuntimeError("MongoDBSingleton 尚未初始化")
        return MongoDBSingleton.__instance

    @staticmethod
    def client() -> MongoClient:
        """
        获取 MongoClient 对象
        Returns:
            MongoClient: MongoDB 客户端对象
        Raises:
            RuntimeError: 如果单例尚未初始化
        """
        if MongoDBSingleton.__instance is None:
            raise RuntimeError("MongoDBSingleton 尚未初始化")
        return MongoDBSingleton.__instance.get_client()

    @staticmethod
    def collection(collection_name: str, db=None):
        """
        获取指定集合
        Args:
            collection_name: 集合名称
            db: 可选的数据库对象，默认为当前数据库
        Returns:
            Collection: MongoDB 集合对象
        Raises:
            ValueError: 如果 collection_name 为空
            RuntimeError: 如果单例尚未初始化
        """
        if MongoDBSingleton.__instance is None:
            raise RuntimeError("MongoDBSingleton 尚未初始化")
        return MongoDBSingleton.__instance.get_collection(collection_name, db)

    @staticmethod
    def test_connection() -> bool:
        """
        测试 MongoDB 连接是否有效
        Returns:
            bool: 连接成功返回 True，否则返回 False
        """
        try:
            MongoDBSingleton.__instance.client.admin.command('ping')
            cc.logging.success(f"MongoDB connection successful! : {MongoDBSingleton.__instance.print_connection_string()}")
            return True
        except ConnectionFailure:
            cc.logging.error("MongoDB 连接失败：无法连接到服务器")
            return False
        except Exception as e:
            cc.logging.error(f"MongoDB 连接测试失败：{str(e)}")
            return False

    def _init_connection(self, client: MongoClient, db_name: str):
        """
        初始化 MongoDB 连接
        Args:
            client: MongoClient 实例
            db_name: 数据库名称
        """
        self.client = client
        self.db = self.client[db_name]

    def __enter__(self):
        """支持上下文管理器，进入时返回自身"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持上下文管理器，退出时关闭连接"""
        self.close()

    def print_connection_string(self) -> str | None:
        """
        返回安全的 MongoDB 连接字符串，密码部分替换为 ***
        Returns:
            str | None: 安全的连接字符串，或 None（如果未找到）
        """
        if not MongoDBSingleton.__connection_string:
            cc.logging.warning("未找到连接字符串")
            return None
        connection_str = MongoDBSingleton.__connection_string
        try:
            if '@' in connection_str and ':' in connection_str.split('@')[0]:
                prefix = connection_str.split('://')[0] + '://'
                user_pass = connection_str.split('://')[1].split('@')[0]
                host_part = connection_str.split('@')[1]
                username = user_pass.split(':')[0]
                safe_connection_str = f"{prefix}{username}:***@{host_part}"
                return safe_connection_str
            return connection_str
        except (IndexError, AttributeError):
            cc.logging.warning(f"无效的连接字符串格式: {connection_str}")
            return connection_str

    def get_client(self) -> MongoClient:
        """
        获取 MongoClient 对象
        Returns:
            MongoClient: MongoDB 客户端对象
        """
        return self.client

    def get_db(self, db_name: str = None):
        """
        获取指定数据库对象
        Args:
            db_name: 数据库名称，默认为当前数据库
        Returns:
            Database: MongoDB 数据库对象
        """
        return self.db if db_name is None else self.client[db_name]

    def get_collection(self, collection_name: str, db=None):
        """
        获取或创建指定集合
        Args:
            collection_name: 集合名称
            db: 可选的数据库对象，默认为当前数据库
        Returns:
            Collection: MongoDB 集合对象
        Raises:
            ValueError: 如果 collection_name 为空
        """
        if not collection_name:
            raise ValueError("集合名称不能为空")
        db = db or self.db
        return db[collection_name]

    def list_collections(self, db=None) -> List[str]:
        """
        列出数据库中的所有集合
        Args:
            db: 可选的数据库对象，默认为当前数据库
        Returns:
            List[str]: 集合名称列表
        """
        db = db or self.db
        return db.list_collection_names()

    def create_collection(self, collection_name: str, db=None) -> None:
        """
        创建新集合（如果不存在）
        Args:
            collection_name: 集合名称
            db: 可选的数据库对象，默认为当前数据库
        Raises:
            ValueError: 如果 collection_name 为空
            PyMongoError: 如果创建集合失败
        """
        if not collection_name:
            raise ValueError("集合名称不能为空")
        try:
            db = db or self.db
            if collection_name not in db.list_collection_names():
                db.create_collection(collection_name)
        except PyMongoError as e:
            cc.logging.error(f"创建集合失败: {str(e)}")
            raise

    def drop_collection(self, collection_name: str, db=None) -> None:
        """
        删除指定集合
        Args:
            collection_name: 集合名称
            db: 可选的数据库对象，默认为当前数据库
        Raises:
            ValueError: 如果 collection_name 为空
            PyMongoError: 如果删除集合失败
        """
        if not collection_name:
            raise ValueError("集合名称不能为空")
        try:
            db = db or self.db
            db[collection_name].drop()
        except PyMongoError as e:
            cc.logging.error(f"删除集合失败: {str(e)}")
            raise

    def insert_one(self, collection_name: str, document: Dict[str, Any], db=None) -> str:
        """
        插入单个文档到指定集合
        Args:
            collection_name: 集合名称
            document: 要插入的文档
            db: 可选的数据库对象，默认为当前数据库
        Returns:
            str: 插入文档的ID
        Raises:
            ValueError: 如果 collection_name 为空或 document 无效
            PyMongoError: 如果插入操作失败
        """
        if not collection_name:
            raise ValueError("集合名称不能为空")
        if not isinstance(document, dict):
            raise ValueError("文档必须是字典类型")
        try:
            db = db or self.db
            collection = self.get_collection(collection_name, db)
            result = collection.insert_one(document)
            return str(result.inserted_id)
        except PyMongoError as e:
            cc.logging.error(f"插入文档失败: {str(e)}")
            raise

    def insert_many(self, collection_name: str, documents: List[Dict[str, Any]], db=None) -> List[str]:
        """
        插入多个文档到指定集合
        Args:
            collection_name: 集合名称
            documents: 要插入的文档列表
            db: 可选的数据库对象，默认为当前数据库
        Returns:
            List[str]: 插入文档的ID列表
        Raises:
            ValueError: 如果 collection_name 为空或 documents 无效
            PyMongoError: 如果插入操作失败
        """
        if not collection_name:
            raise ValueError("集合名称不能为空")
        if not isinstance(documents, list) or not documents:
            raise ValueError("文档列表必须是非空列表")
        try:
            db = db or self.db
            collection = self.get_collection(collection_name, db)
            result = collection.insert_many(documents)
            return [str(id) for id in result.inserted_ids]
        except PyMongoError as e:
            cc.logging.error(f"批量插入文档失败: {str(e)}")
            raise

    def find_one(self, collection_name: str, query: Dict[str, Any] = None, db=None) -> Dict[str, Any] | None:
        """
        查询指定集合中的单个文档
        Args:
            collection_name: 集合名称
            query: 查询条件，默认为 None（返回第一个文档）
            db: 可选的数据库对象，默认为当前数据库
        Returns:
            Dict[str, Any] | None: 查找到的文档，或 None（如果未找到）
        Raises:
            ValueError: 如果 collection_name 为空
            PyMongoError: 如果查询操作失败
        """
        if not collection_name:
            raise ValueError("集合名称不能为空")
        try:
            db = db or self.db
            collection = self.get_collection(collection_name, db)
            return collection.find_one(query or {})
        except PyMongoError as e:
            cc.logging.error(f"查询文档失败: {str(e)}")
            raise

    def find_many(self, collection_name: str, query: Dict[str, Any] = None, limit: int = 0, db=None) -> List[Dict[str, Any]]:
        """
        查询指定集合中的多个文档
        Args:
            collection_name: 集合名称
            query: 查询条件，默认为 None（返回所有文档）
            limit: 返回文档数量限制，0 表示无限制
            db: 可选的数据库对象，默认为当前数据库
        Returns:
            List[Dict[str, Any]]: 查找到的文档列表
        Raises:
            ValueError: 如果 collection_name 为空
            PyMongoError: 如果查询操作失败
        """
        if not collection_name:
            raise ValueError("集合名称不能为空")
        try:
            db = db or self.db
            collection = self.get_collection(collection_name, db)
            cursor = collection.find(query or {})
            if limit > 0:
                cursor = cursor.limit(limit)
            return list(cursor)
        except PyMongoError as e:
            cc.logging.error(f"批量查询文档失败: {str(e)}")
            raise

    def update_one(self, collection_name: str, query: Dict[str, Any], update: Dict[str, Any], db=None) -> int:
        """
        更新指定集合中的单个文档
        Args:
            collection_name: 集合名称
            query: 查询条件
            update: 更新内容
            db: 可选的数据库对象，默认为当前数据库
        Returns:
            int: 受影响的文档数量
        Raises:
            ValueError: 如果 collection_name 为空或 query/update 无效
            PyMongoError: 如果更新操作失败
        """
        if not collection_name:
            raise ValueError("集合名称不能为空")
        if not isinstance(query, dict) or not isinstance(update, dict):
            raise ValueError("查询条件和更新内容必须是字典类型")
        try:
            db = db or self.db
            collection = self.get_collection(collection_name, db)
            result = collection.update_one(query, {"$set": update})
            return result.modified_count
        except PyMongoError as e:
            cc.logging.error(f"更新文档失败: {str(e)}")
            raise

    def update_many(self, collection_name: str, query: Dict[str, Any], update: Dict[str, Any], db=None) -> int:
        """
        更新指定集合中的多个文档
        Args:
            collection_name: 集合名称
            query: 查询条件
            update: 更新内容
            db: 可选的数据库对象，默认为当前数据库
        Returns:
            int: 受影响的文档数量
        Raises:
            ValueError: 如果 collection_name 为空或 query/update 无效
            PyMongoError: 如果更新操作失败
        """
        if not collection_name:
            raise ValueError("集合名称不能为空")
        if not isinstance(query, dict) or not isinstance(update, dict):
            raise ValueError("查询条件和更新内容必须是字典类型")
        try:
            db = db or self.db
            collection = self.get_collection(collection_name, db)
            result = collection.update_many(query, {"$set": update})
            return result.modified_count
        except PyMongoError as e:
            cc.logging.error(f"批量更新文档失败: {str(e)}")
            raise

    def delete_one(self, collection_name: str, query: Dict[str, Any], db=None) -> int:
        """
        删除指定集合中的单个文档
        Args:
            collection_name: 集合名称
            query: 查询条件
            db: 可选的数据库对象，默认为当前数据库
        Returns:
            int: 删除的文档数量
        Raises:
            ValueError: 如果 collection_name 为空或 query 无效
            PyMongoError: 如果删除操作失败
        """
        if not collection_name:
            raise ValueError("集合名称不能为空")
        if not isinstance(query, dict):
            raise ValueError("查询条件必须是字典类型")
        try:
            db = db or self.db
            collection = self.get_collection(collection_name, db)
            result = collection.delete_one(query)
            return result.deleted_count
        except PyMongoError as e:
            cc.logging.error(f"删除文档失败: {str(e)}")
            raise

    def delete_many(self, collection_name: str, query: Dict[str, Any], db=None) -> int:
        """
        删除指定集合中的多个文档
        Args:
            collection_name: 集合名称
            query: 查询条件
            db: 可选的数据库对象，默认为当前数据库
        Returns:
            int: 删除的文档数量
        Raises:
            ValueError: 如果 collection_name 为空或 query 无效
            PyMongoError: 如果删除操作失败
        """
        if not collection_name:
            raise ValueError("集合名称不能为空")
        if not isinstance(query, dict):
            raise ValueError("查询条件必须是字典类型")
        try:
            db = db or self.db
            collection = self.get_collection(collection_name, db)
            result = collection.delete_many(query)
            return result.deleted_count
        except PyMongoError as e:
            cc.logging.error(f"批量删除文档失败: {str(e)}")
            raise

    def is_healthy(self) -> bool:
        """
        检查 MongoDB 连接是否健康
        Returns:
            bool: 如果连接健康返回 True，否则返回 False
        """
        try:
            self.client.admin.command('ping')
            return True
        except ConnectionFailure:
            cc.logging.error("MongoDB 连接不健康")
            return False

    def bulk_write(self, collection_name: str, operations: List[Dict[str, Any]], db=None) -> Dict[str, Any]:
        """
        执行批量写操作
        Args:
            collection_name: 集合名称
            operations: 批量操作列表（支持 insert, update, delete）
            db: 可选的数据库对象，默认为当前数据库
        Returns:
            Dict[str, Any]: 批量操作结果
        Raises:
            ValueError: 如果 collection_name 为空或 operations 无效
            PyMongoError: 如果批量操作失败
        """
        if not collection_name:
            raise ValueError("集合名称不能为空")
        if not isinstance(operations, list) or not operations:
            raise ValueError("操作列表必须是非空列表")
        try:
            db = db or self.db
            collection = self.get_collection(collection_name, db)
            from pymongo import InsertOne, UpdateOne, DeleteOne
            result = collection.bulk_write(operations)
            return {
                "inserted_count": result.inserted_count,
                "modified_count": result.modified_count,
                "deleted_count": result.deleted_count
            }
        except PyMongoError as e:
            cc.logging.error(f"批量写操作失败: {str(e)}")
            raise

    def close(self):
        """
        关闭 MongoDB 连接并重置单例状态
        """
        if self.client:
            self.client.close()
            MongoDBSingleton.__instance = None
            MongoDBSingleton.__connection_string = None
