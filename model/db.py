# -*- coding:utf-8 -*-

from config.config import config as configClient
import redis

try:
    config = configClient()

    # 实例化Redis
    redis_config = config.redis
    redis_client = redis.Redis(host=redis_config['host'], port=redis_config['port'], db=redis_config['db'])
except Exception as e:
    print(e)
    exit(1)




