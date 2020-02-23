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
        self.database = data["database"]
        self.redis_config = data['redis']
        self.chaojiying = data['chaojiying']
        self.weibo = data['weibo']
