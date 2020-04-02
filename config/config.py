import yaml
import os


class config:
    database = None

    def __init__(self):
        try:
            file_path = os.path.realpath(__file__)
            dir_path = os.path.split(file_path)[0]
            yaml_path = os.path.join(dir_path, "config.yaml")
        except OSError:
            print("open config yaml failed")
            return

        f = open(yaml_path, encoding="utf-8")
        content = f.read()
        data = yaml.safe_load(content)
        self.__data = data
        for k, v in data.items():
            setattr(self, k, v)
        # self.database = data["database"]
        # self.redis_config = data['redis']
        # self.chaojiying = data['chaojiying']
        # self.weibo = data['weibo']
        # self.mongo = data['mongo']
        #
        # self.itemName = data['itemName']

    def get(self, key):
        # if hasattr(self, key):
        #     return getattr(self, key)
        # return ""
        keys = str.split(key, ".")
        val = self.__search_key(keys, self.__data)
        return val

    # 解析.分割的key
    # mongo.key, redis.host
    def __search_key(self, keys, data):
        if len(keys) > 0:
            key = keys.pop(0)
            if isinstance(data, dict):
                if key in data:
                    if len(keys) == 0:
                        return data[key]
                    else:
                        return self.__search_key(keys, data[key])
        return ""


cfg = config()
