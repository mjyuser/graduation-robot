# coding:utf-8
import requests
from sqlalchemy import exc
from bs4 import BeautifulSoup
import model.airConditioner as Conditioner
from model.db import session, engine, redis_client
from services import sn, taobao, jd
from utils import helper
import traceback

REDIS_KEY = "URL_MAP"


def fetchAir(router):
    if router == "sn":
        getSuNing(page=0, offset=0)
    elif router == "taobao":
        getTaoBao()
    elif router == "jd":
        getJd()


def getJd():
    client = jd.jd()
    # 转到搜索后的列表页
    items = client.get_href_from_cache()
    data = {}
    for href in items:
        detail = client.get_detail_page(href, refresh=True)
        # 获取参数页
        parameters = detail.select("#detail > div.tab-con > div:nth-child(2) > div.Ptable > div:nth-child(1) > dl > dl")
        for parameter in parameters:
            key = parameter.select_one("dt").get_text()
            val = parameter.select_one("dd").get_text()
            data[key] = val

        productId = helper.get_number(href)
        score, labels = client.get_comment(productId)
        model = Conditioner.airConditioner.find_one_by_href(href)
        dicts = {"property": data, "feedback": score, "labels": labels}
        try:
            model.update(dicts)
        except:
            print("save model data failed. detail: {}".format(traceback.format_exc()))


def getTaoBao():
    ins = taobao.taobao()
    href_list = ins.get_goods_list()
    if href_list is not None:
        for href in href_list:
            if not ins.is_spider(href):
                ins.get_page_message(href)


def getSuNing(page=0, offset=0):
    while True:
        ins = sn.sn()
        url = ins.get_list_url(page, offset)
        response = requests.get(url)
        if response.status_code != 200:
            print("获取苏宁家电异常, url:%s, code:%d" % (url, response.status_code))
            return

        ct = response.headers["Content-type"].split("charset=")[1].lower()
        bs = BeautifulSoup(response.content, features="html.parser", from_encoding=ct)

        data = bs.find_all("li", class_="basic")
        if not data:
            break

        for item in data:
            box = item.select_one(".product-box")
            img_box = box.select_one(".res-img > .img-block > a")
            store_box = box.select_one(".store-stock > a")
            href = img_box["href"]
            if not href.startswith("http"):
                href = "https:" + href
            if redis_client.sismember(REDIS_KEY, href) > 0:
                print("the url is scraped. url:%s" % href)
                continue

            print("fetch href: %s" % href)

            # 空调相关的参数
            parameter = ins.get_parameter(href)
            # 获取售卖价格
            price = ins.get_price()
            # 获取原价
            origin_price = ins.get_origin_price()

            # 获取好评率
            score = ins.get_evaluate_score()
            # 获取评价标签
            labels = ins.get_evaluate_labels()
            # 插入DB
            model = Conditioner.airConditioner(tag_str=img_box["title"], link=href,
                                               title=img_box.select_one("img")["alt"], merchant=store_box.get_text(),
                                               property=parameter, price=price * 100, origin_price=origin_price * 100,
                                               feedback=score, labels=",".join(labels), platform=ins.platform)
            session.add(model)
            redis_client.sadd(REDIS_KEY, href)

            try:
                session.commit()
            except exc.SQLAlchemyError as e:
                print("sql failed", e)
                continue

        # 苏宁的web规则, paging的值为0~3
        if offset <= 3:
            offset = offset + 1
        else:
            page = page + 1
            offset = 0
        if page > 50:
            break


def clear():
    print("clean db and redis data")
    redis_client.delete(REDIS_KEY)
    Conditioner.airConditioner.__table__.drop(engine)
