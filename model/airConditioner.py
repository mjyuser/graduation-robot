# -*- coding:utf-8 -*-
import re
from model.db import Base
from sqlalchemy import Column, Integer, String, UniqueConstraint, Index, JSON


class airConditioner(Base):
    __tablename__ = 'air_conditioner'
    id = Column(Integer, primary_key=True)
    link = Column(String(256), comment="主页链接")
    merchant = Column(String(128), comment="销售商家")
    tag_str = Column(String(1024), comment="tag标签")
    title = Column(String(256), comment="商品名")
    property = Column(JSON, comment="商品属性")
    price = Column(Integer, comment="售卖价格(单位:分)")
    origin_price = Column(Integer, comment="原始价格(单位:分)")
    feedback = Column(Integer, comment="好评率")
    labels = Column(String(1024), comment="评价标签")
    __table_args__ = (
        UniqueConstraint('link', name="idx_link"),
        Index("idx_merchant", "merchant")
    )

    @staticmethod
    def get_tag(tag_str):
        # 匹配中文+英文+数字
        pattern = re.compile(r'[\u4e00-\u9fa5a-z0-9A-Z]+')
        result = pattern.findall(tag_str)
        return result

    def print_self(self):
        for each in dir(self):
            value = self.__getattribute__(each)
            print(each, ":", value)
