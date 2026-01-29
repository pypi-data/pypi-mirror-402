from .mongo_singleton import MongoDBSingleton
from .mysql_singleton import MysqlDBSingleton
from .mysql import MysqlDB
from .redis import RedisUtil
db = MysqlDBSingleton
mongo = MongoDBSingleton
redis = RedisUtil