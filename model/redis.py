import redis

from config.config import cfg


class Redis:
    def __init__(self, host, port, db=0):
        self.__host = host
        self.__port = port
        self.__db = db
        self.__instance = redis.Redis(self.__host, self.__port, self.__db)

    @property
    def instance(self):
        return self.__instance


host = cfg.get("redis.host")
port = cfg.get("redis.port")
db = cfg.get("redis.db")
rediscli = Redis(host, port, db)
