import logging

from config.config import cfg
from utils import helper
import os


class Logger:
    def __init__(self):
        log_path = helper.get_rootpath(cfg.get("itemName")) + "/logs"
        log_name = log_path + "/app.log"
        if not os.path.exists(log_path):
            os.mkdir(log_path)

        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        logger.info("logger init success")

        handler = logging.FileHandler(log_name, mode='a')
        handler.setLevel(logging.INFO)

        formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        self.__logger = logger

    @property
    def logger(self):
        return self.__logger

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)

    def warning(self, message):
        self.logger.warning(message)


logger = Logger()
