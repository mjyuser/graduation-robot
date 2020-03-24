# coding: utf-8
from bson.objectid import ObjectId

class mechina():
    def __init__(self, mgocli):
        if mgocli is None:
            print("mgocli is nil")
            return
        self.__moncli = mgocli
        self.__database = self.__moncli["graduation"]
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
            print("data must be instance of dict")
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

    def find(self, query):
        return self.instance.find_one(query)