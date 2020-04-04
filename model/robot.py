# coding: utf-8
from bson.objectid import ObjectId
from utils.logger import logger
import random


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
        return self.instance.find_one_by_query({"_id": _id})

    def find_one_by_query(self, query):
        return self.instance.find_one_by_query(query)

    def create_sale_data(self):
        # min_price = self.instance.find_one({"price": {"$gt": 0}}, sort=[("price", 1)])
        # max_price = self.instance.find({"price": {"$gt": 0}}).sort("price", -1).limit(1)
        counts = self.instance.find({"price": {"$gt": 0, "$lt": 300000}}).count()
        data = self.instance.find({"price": {"$gt": 0, "$lt": 300000}}).sort("price", 1)
        prices = [x['price'] / 100 for x in data]

        # 第一个区间的数据
        idx_one = [random.randint(0, 1000) for i in range(0, int(counts / 10))]
        idx_two = [random.randint(0, 800) for i in range(int(counts/10) + 1, int((counts/10)) * 2)]
        idx_one.extend(idx_two)
        idx_other = [random. randint(0, 400) for i in range(0, counts - len(idx_one))]
        idx_one.extend(idx_other)
        # 分为10个区间
        # 第一,二个区间的数据相对较大, 后面八个区间相对较少
        return idx_one, prices
