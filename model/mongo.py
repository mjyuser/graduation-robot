# coding: utf-8

import pymongo
from config.config import cfg
from utils.logger import logger


class Mongo():
    def __init__(self, host, port):
        self.__host = host
        self.__port = port
        logger.info("init mongo db host: %s, port: %s" % (self.__host, self.__port))
        self.__instance = pymongo.MongoClient("mongodb://%s:%s" % (self.__host, self.__port))

    # 获取mongo链接的实例
    @property
    def instance(self):
        return self.__instance


host = cfg.get_key("mongo.host")
port = cfg.get_key("mongo.port")
mgocli = Mongo(host, port)
