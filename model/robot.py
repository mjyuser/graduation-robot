# coding: utf-8
from bson.objectid import ObjectId
from utils.logger import logger


class robot():
    def __init__(self, mgocli):
        if mgocli is None:
            logger.error("mgocli is not init")
            return
        self.__mogcli = mgocli
        self.__database = self.__mogcli["graduation"]
        self.__table = self.__database["machine"]

    @property
    def instance(self):
        return self.__table

    def __validate(self, data) -> dict:
        for k, v in data.items():
            if isinstance(v, str):
                data.update({k: v.replace(".", "_")})
        return data

    def insert(self, data):
        # data = self.__validate(data)
        if not isinstance(data, dict):
            logger.error("data must be instance of dict")
            return False
        res = self.instance.insert_one(data)
        if res is not None:
            return res.inserted_id

    def upsert(self, primary_id, data):
        # data = self.__validate(data)
        obj = self.find_by_id(primary_id)
        if obj is not None:
            self.instance.update_one({"_id": primary_id}, {"$set": data})
            return primary_id
        else:
            return self.insert(data)

    def find_by_id(self, _id):
        if isinstance(_id, str):
            _id = ObjectId(_id)
        return self.instance.find_one({"_id": _id})

    def find_one(self, query):
        return self.instance.find_one(query)
