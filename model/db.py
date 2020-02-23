# -*- coding:utf-8 -*-

from config.config import config as configClient
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis


# 获取配置
Base = declarative_base()
config = configClient()

# 实例化DB
database = config.database
schema = "mysql://%s:%s@%s/%s" % (database["user"], database["password"], database["host"], database["db"])
engine = create_engine(schema, encoding="utf8", echo=True)
Session = sessionmaker(bind=engine)
session = Session()


# 实例化Redis
redis_config = config.redis_config
redis_client = redis.Redis(host=redis_config['host'], port=redis_config['port'], db=redis_config['db'])



