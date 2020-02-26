# coding:utf-8
import requests
from sqlalchemy import exc
from bs4 import BeautifulSoup
import model.airConditioner as Conditioner
from model.db import session, engine, redis_client
from services import sn, taobao, jd
import time

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
    page = client.search("智能空调")
    bs = BeautifulSoup(page, features="html.parser")

    count = 0
    while count <= 50:
        items = bs.select("#J_goodsList > .gl-warp > .gl-item")
        print(len(items))
        for item in items:
            try:
                img_box = item.select_one("div.p-img > a")
                tag_str = img_box["title"]
                href = img_box["href"]
                if not href.startswith("https"):
                    href = "https:" + href
                if client.is_spider(href):
                    continue
                price = item.select_one("div.p-price > strong > i").get_text()
                origin_price = price
                title = item.select_one(".p-name > a > em").get_text()
                merchant = item.select_one(".p-shop > .J_im_icon > a").get_text()

                model = Conditioner.airConditioner(link=href, merchant=merchant, tag_str=tag_str, title=title,
                                                   price=float(price) * 100, origin_price=float(origin_price) * 100,
                                                   platform=client.platform)
                session.add(model)

                session.commit()
                client.save_href(href)
            except Exception as e:
                print("merchant message: %s, %s" % (title, href))
                print(e)
                continue

        # 获取下一页
        next_page_btn = client.get_driver().find_element_by_css_selector("#J_bottomPage > span.p-num > a.pn-next")
        if next_page_btn is None:
            break

        next_page_btn.click()
        time.sleep(5)
        client.scroll()
        time.sleep(5)
        bs = BeautifulSoup(client.page_source, features="html.parser")


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
