# coding:utf-8
from model.redis import rediscli
from services import jd, sn, taobao

REDIS_KEY = "URL_MAP"


def fetchAir(router):
    if router == "sn":
        getSuNing(r'智能机器人', page=0, offset=0)
    elif router == "taobao":
        getTaoBao()
    elif router == "jd":
        getJd()


def getJd():
    client = jd.jd()
    # 转到搜索后的列表页
    client.get_jd_data(r"智能机器人")
    # client.consumer()


def getTaoBao():
    ins = taobao.taobao()
    href_list = ins.get_goods_list(r'智能机器人')
    if href_list is not None:
        for href in href_list:
            if not ins.is_spider(href):
                ins.get_page_message(href)


def getSuNing(key, page=0, offset=0):
    ins = sn.sn(key)
    ins.get_data(page, offset)


def clear():
    print("clean db and redis data")
    rediscli.delete(REDIS_KEY, "JD_URL")
