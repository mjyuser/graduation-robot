# -*- coding:utf-8 -*-

from config.config import config as configClient
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from model.mongo import Mongo
import redis

try:
    # 获取配置
    Base = declarative_base()
    config = configClient()

    # 实例化DB
    database = config.database
    schema = "mysql://%s:%s@%s/%s?charset=utf8" % (database["user"], database["password"], database["host"], database["db"])
    engine = create_engine(schema, encoding="utf8", echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    mgocli = Mongo(config.mongo["host"], config.mongo["port"])

    # 实例化Redis
    redis_config = config.redis_config
    redis_client = redis.Redis(host=redis_config['host'], port=redis_config['port'], db=redis_config['db'])
except Exception as e:
    print(e)
    exit(1)




