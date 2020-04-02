import requests
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from bs4 import BeautifulSoup

from model.mongo import mgocli
from model.redis import rediscli
from model.robot import robot
from utils import helper


class sn:
    platform = "苏宁"
    REDIS_KEY = "URL_MAP"

    def __init__(self, key):
        self.key = key
        options = Options()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)
        self.home_page = None
        self.evaluate_page = None
        self.home_url = None
        self.evaluate_warp = None
        self.redis = rediscli.instance
        self.mongo = mgocli

    def get_data(self, page, offset):
        while True:
            url = self.get_list_url(page, offset)
            print(url)
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
                if self.redis.sismember(self.REDIS_KEY, href) > 0:
                    print("the url is scraped. url:%s" % href)
                    continue

                print("fetch href: %s" % href)

                # 空调相关的参数
                parameter = self.get_parameter(href)
                # 获取售卖价格
                price = self.get_price()
                # 获取原价
                origin_price = self.get_origin_price()

                # 获取好评率
                score = self.get_evaluate_score()
                # 获取评价标签
                labels = self.get_evaluate_labels()
                # 插入DB

                model = robot(self.mongo.instance)
                data = {
                    "tags": img_box["title"],
                    "link": href,
                    "title": img_box.select_one("img")["alt"],
                    "merchant": store_box.get_text(),
                    "property": parameter,
                    "price": price * 100,
                    "origin_price": origin_price * 100,
                    "feedback": score,
                    "labels": ",".join(labels),
                    "platform": self.platform
                }

                try:
                    model.insert(data)
                    self.redis.sadd(self.REDIS_KEY, href)
                except Exception as e:
                    print("insert taobao data failed.", e)
                    return

            # 苏宁的web规则, paging的值为0~3
            if offset <= 3:
                offset = offset + 1
            else:
                page = page + 1
                offset = 0
            if page > 50:
                break

    def build_dom(self, content):
        return BeautifulSoup(content, features="html.parser")

    # 评价页
    def get_evaluate_page(self):
        if self.evaluate_page is None:
            home = self.get_home_page()
            if home is not None:
                self.driver.find_element_by_id("productCommTitle").click()
                self.evaluate_page = self.build_dom(self.driver.page_source)

        return self.evaluate_page

    def get_evaluate_wrap(self):
        page = self.get_evaluate_page()
        if page is not None:
            self.evaluate_warp = page.select_one(".rv-rate-wrap")

        return self.evaluate_warp

    def get_evaluate_score(self):
        score = 0
        wrap = self.get_evaluate_wrap()
        if wrap is not None:
            score_box = wrap.select_one(".rv-rate-score > .item > .score > span")
            if score_box is not None:
                score = score_box.get_text()

        return score

    def get_evaluate_labels(self):
        labels = []
        wrap = self.get_evaluate_wrap()
        if wrap is not None:
            label_box = wrap.select(".rv-rate-label > .item > a > span")
            if label_box is not None:
                for label in label_box:
                    labels.append(label.get_text().strip())
        return labels

    def get_home_page(self, url=None, new=False):
        if url is None:
            url = self.home_url
        if self.home_page is None or new is True:
            self.driver.get(url)
            self.home_page = self.build_dom(self.driver.page_source)

        return self.home_page

    # 获取空调相关参数
    def get_parameter(self, url):
        home = self.get_home_page(url=url, new=True)
        items = home.select("#itemParameter > tbody > tr")
        parameter = {}
        for dd in items:
            if dd.has_attr("parametercode"):
                name = dd.select_one(".name > .name-inner > span")
                value = dd.select_one(".val")
                if name is not None and value is not None:
                    parameter[name.get_text().strip()] = value.get_text().strip()
        return parameter

    def get_price(self, element="span.mainprice"):
        home = self.get_home_page()
        price_box = home.select_one(element)
        price = 0
        if price_box is not None:
            price = price_box.get_text()
            price = float(helper.get_number(price))
        return price

    def get_origin_price(self):
        return self.get_price(".small-price")

    def get_list_url(self, page=0, offset=0):
        sn_air_url = "https://search.suning.com/emall/searchV1Product.do?" \
                     "keyword={key}&ci=0&pg=01&cp={page}&il=0&st=0&iy=0&adNumber=10" \
                     "&isNoResult=0&n=1&sesab=ACAABAABCAAA&id=IDENTIFYING" \
                     "&cc=577&sub=0&jzq=4123&paging={paging}".format(key=self.key, page=page, paging=offset)
        return sn_air_url
