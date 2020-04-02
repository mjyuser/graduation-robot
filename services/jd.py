from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from model.db import redis_client
from model.robot import robot
from model.mongo import mgocli
from utils import helper
import requests
import traceback
from multiprocessing import Process, Queue
import platform
import os

import time


class jd:
    website = "https://www.jd.com"
    parameter_selector = "#detail > div.tab-con > div:nth-child(2) > .Ptable > .Ptable-items > dl > dl"
    website_name = "京东"
    href_map = "JD_URL"
    record_href_map = "JD_RECORD"

    def __init__(self):
        self.driver = None
        self.detail = None
        self.redis = redis_client
        self.wait = None
        self.queue = None
        self._consumer = None
        self._platform = platform.system()
        self._headers = {
            "DNT": "1",
            "sec-ch-ua": "Google Chrome 74",
            "Sec-Fetch-Dest": "script",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "same-site",
            "Sec-Fetch-User": "?F",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36"
        }

        self._params = {
            "score": "0",
            "sortType": "5",
            "page": "0",
            "pageSize": "10",
            "isShadowSku": "0",
            "fold": "1",
        }

        self.mongocli = robot(mgocli.instance)

        # self.create_queue()
        # self.create_consumer()

    @property
    def platform(self):
        return self._platform

    def is_windows(self):
        return self.platform == "Windows"

    def is_Linux(self):
        return self.platform == "Linux"

    @property
    def params(self):
        return self._params

    @params.setter
    def params(self, value):
        self._params.update(value)

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, value):
        self._headers.update(value)

    def get_driver(self):
        if self.driver is None:
            self.driver = webdriver.Chrome(options=self.options)
        return self.driver

    def get_wait(self, timeout=10):
        if self.wait is None:
            self.wait = WebDriverWait(self.get_driver(), timeout)
        return self.wait

    @property
    def options(self):
        options = Options()
        options.add_argument("--headless")
        prefs = {
            'profile.default_content_setting_values': {
                'images': 2,
            }
        }
        options.add_experimental_option("prefs", prefs)
        options.add_experimental_option("excludeSwitches", ['enable-automation'])

        return options

    @property
    def page_source(self):
        return self.get_driver().page_source

    # 调用京东的搜索框
    def search(self, key):
        driver = self.get_driver()
        driver.get(self.website)
        search_btn = driver.find_element_by_css_selector("#key")
        search_btn.send_keys(key)
        search_btn.send_keys(Keys.ENTER)

        time.sleep(3)
        self.scroll()
        # 防止页面未加载成功
        time.sleep(3)
        return driver.page_source

    # 滑动右侧滑动条
    def scroll(self):
        self.get_driver().execute_script("window.scrollTo(0, document.body.scrollHeight)")

    # 保存爬取下来的详情页链接
    def save_href(self, href) -> None:
        if not self.is_spider(href):
            self.redis.sadd(self.href_map, href)

            # 将链接输入到队列当中, 另一个进程进行消费
            if self.queue is not None:
                self.queue.put(href)

    # 详情页信息
    def get_detail(self, _id):
        model = self.mongocli.find_by_id(_id)
        href = ""
        if model is not None:
            href = model["link"]
        detail = self.get_detail_page(href, refresh=True)
        data = {}
        # 获取参数页
        parameters = detail.select("#detail > div.tab-con > div:nth-child(2) > div.Ptable > div:nth-child(1) > dl > dl")
        for parameter in parameters:
            key = parameter.select_one("dt").get_text()
            val = parameter.select_one("dd").get_text()
            data[key] = val

        productId = helper.get_number(href)
        score, labels = self.get_comment(productId)
        dicts = {"property": data, "feedback": score, "labels": labels}
        print(dicts)
        try:
            res = self.mongocli.upsert(_id, dicts)
            print("prit res: %s" % res)
        except:
            print("save model data failed. detail: {}".format(traceback.format_exc()))

    def get_detail_page(self, href, refresh=False):
        if self.detail is None or refresh is True:
            content = self.fetch_detail_page_content(href)
            if content is not None:
                self.detail = BeautifulSoup(content, features="html.parser")
        return self.detail

    # 请求详情页的内容
    def fetch_detail_page_content(self, href):
        print("fetch %s" % href)
        response = requests.get(href)
        if response.status_code != 200:
            print("fetch %s failed, the response code is %d" % (href, response.status_code))
            return
        return response.content

    def is_spider(self, href):
        data = self.mongocli.find({"link": href})
        return self.redis.sismember(self.href_map, href) or data is not None

    def get_jd_data(self, key):
        page = self.search(key)
        bs = BeautifulSoup(page, features="html.parser")

        count = 0
        while count <= 50:
            items = bs.select("#J_goodsList > .gl-warp > .gl-item")
            for item in items:
                try:
                    img_box = item.select_one("div.p-img > a")
                    tag_str = img_box["title"]
                    href = img_box["href"]
                    if not href.startswith("https"):
                        href = "https:" + href
                    if self.is_spider(href):
                        print("the href %s is spidered" % href)
                        continue
                    print("url: %s" % href)
                    price = item.select_one("div.p-price > strong > i").get_text()
                    origin_price = price
                    title = item.select_one(".p-name > a > em").get_text()
                    merchant = "自营"
                    merchant_box = item.select_one(".p-shop > .J_im_icon > a")
                    if merchant_box is not None:
                        merchant = merchant_box.get_text()



                    data = {
                        "tags": tag_str,
                        "link": href,
                        "title": title,
                        "merchant": merchant,
                        "price": float(price) * 100,
                        "origin_price": float(origin_price) * 100,
                        "platform": self.website_name
                    }
                    _id = self.mongocli.insert(data)
                    redis_client.sadd(self.href_map, href)
                except Exception as e:
                    print(traceback.format_exc())
                    print("insert JD data failed.", e)
                    return
                # 爬取后续数据
                self.get_detail(_id)

            # 获取下一页
            next_page_btn = self.get_driver().find_element_by_css_selector("#J_bottomPage > span.p-num > a.pn-next")
            if next_page_btn is None:
                break
            count = count + 1
            next_page_btn.click()
            # 等待页面加载 JD的商品页会下拉加载, 强制sleep 5s
            self.scroll()
            time.sleep(5)
            bs = BeautifulSoup(self.page_source, features="html.parser")

        # 等待队列消费完毕
        # self.queue.join()

    def get_href_from_cache(self):
        items = self.redis.smembers(self.href_map)
        return [str(href, encoding="utf-8") for href in items]

    def save_page_is_spider(self, href) -> None:
        self.redis.sadd(self.record_href_map, href)

    def detail_is_spider(self, href) -> bool:
        return self.redis.sismember(self.record_href_map, href)

    # 获取评论数据
    def get_comment(self, product_id):
        self.headers = {"Referer": "https://item.jd.com/{productId}.html".format(productId=product_id)}
        self.params = {"productId": product_id}

        response = requests.get("https://sclub.jd.com/comment/productPageComments.action", params=self.params,
                                headers=self.headers)
        try:
            score = response.json()["productCommentSummary"]["goodRateShow"]
            statistics = response.json()["hotCommentTagStatistics"]
            items = [item["name"] for item in statistics]
            return score, ",".join(items)
        except Exception as e:
            print(e)
        return

    # 获取评论标签
    def get_labels(self):
        selector = "#detail > div.tab-con > div:nth-child(2) > div.Ptable > div:nth-child(1) > dl > dl"
        parameters = self.detail.select(selector)
        data = {}
        for parameter in parameters:
            key = parameter.select_one("dt").get_text()
            val = parameter.select_one("dd").get_text()
            data[key] = val
        return data

    def create_queue(self):
        if self.queue is None and self.is_Linux():
            print('Process to read: %s' % os.getpid())
            self.queue = Queue()

    def create_consumer(self):
        if self.is_Linux() and self._consumer is None:
            self._consumer = Process(target=self.consumer)

            self._consumer.start()

    def consumer(self):
        while True:
            href = self.queue.get()
            self.get_detail(href)
            if self.queue.empty():
                break
