# coding: utf-8

import pymongo


class Mongo():
    def __init__(self, host, port):
        self.__host = host
        self.__port = port

        self.__instance = pymongo.MongoClient("mongodb://%s:%s" % (self.__host, self.__port))

    # 获取mongo链接的实例
    @property
    def instance(self):
        return self.__instance
