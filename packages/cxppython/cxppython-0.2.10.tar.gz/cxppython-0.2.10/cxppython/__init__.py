from .utils.cxplogging import logging
from .utils.easy_imports import *
from .utils.database import db
from .utils.database import MysqlDB
from .utils.database import mongo
from .utils.database import redis
debug()

database_dict={}
def add_db(name,database:MysqlDB,overlay=True):
    if database_dict.get(name,None):
        logging.warning(f"Already existing Database {name},Overlay: {overlay}")
        if overlay:
            database_dict[name]=database
    else:
        database_dict[name]=database

def get_db(name)->MysqlDB:
    sqldb=database_dict.get(name,None)
    if sqldb is None:
        logging.error(f"Database not found {name}")
    return sqldb

