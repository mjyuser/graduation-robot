from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from model.db import session, redis_client
from model.airConditioner import airConditioner
import requests

import time


class jd:
    website = "https://www.jd.com"
    parameter_selector = "#detail > div.tab-con > div:nth-child(2) > .Ptable > .Ptable-items > dl > dl"
    platform = "京东"
    href_map = "JD_URL"

    def __init__(self):
        self.driver = None
        self.detail = None
        self.redis = redis_client
        self.wait = None
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

    @property
    def params(self):
        return self._params

    @params.setter
    def params(self, value):
        self._params.update(value)

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
        # options.add_argument("--headless")
        prefs = {
            'profile.default_content_setting_values': {
                'images': 2,
            }
        }
        options.add_experimental_option("prefs", prefs)
        options.add_experimental_option("excludeSwitches", ['enable-automation'])

        return options

    def search(self, key):
        driver = self.get_driver()
        driver.get(self.website)
        search_btn = driver.find_element_by_css_selector("#key")
        search_btn.send_keys(key)
        search_btn.send_keys(Keys.ENTER)

        time.sleep(3)
        self.scroll()
        time.sleep(3)
        return driver.page_source

    def scroll(self):
        self.get_driver().execute_script("window.scrollTo(0, document.body.scrollHeight)")

    @property
    def page_source(self):
        return self.get_driver().page_source

    # 详情页信息
    def get_detail(self, href) -> dict:
        detail = self.get_detail_page(href, refresh=True)
        if detail is None:
            return {}
        parameter = {}
        items = detail.select(self.parameter_selector)
        for data in items:
            key = data.select_one("dt").get_text()
            value = data.select_one("dd").get_text()
            parameter[key] = value

        return parameter

    def get_detail_page(self, href, refresh=False):
        if self.detail is None or refresh is True:
            response = requests.get(href)
            print(response.url)
            if response.status_code != 200:
                return
            self.detail = BeautifulSoup(response.content, features="html.parser")
        return self.detail

    def save_href(self, href) -> None:
        if not self.is_spider(href):
            self.redis.sadd(self.href_map, href)

    def is_spider(self, href):
        return self.redis.sismember(self.href_map, href)

    def get_href_list(self, key):
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
                        continue
                    price = item.select_one("div.p-price > strong > i").get_text()
                    origin_price = price
                    title = item.select_one(".p-name > a > em").get_text()
                    merchant = item.select_one(".p-shop > .J_im_icon > a").get_text()

                    model = airConditioner(link=href, merchant=merchant, tag_str=tag_str, title=title,
                                           price=float(price) * 100, origin_price=float(origin_price) * 100,
                                           platform=self.platform)
                    session.add(model)

                    session.commit()
                    self.save_href(href)
                except Exception as e:
                    print("merchant message: %s, %s" % (title, href))
                    print(e)
                    continue

            # 获取下一页
            next_page_btn = self.get_driver().find_element_by_css_selector("#J_bottomPage > span.p-num > a.pn-next")
            if next_page_btn is None:
                break

            next_page_btn.click()
            # 等待页面加载 JD的商品页会下拉加载, 强制sleep 5s
            self.scroll()
            time.sleep(5)
            bs = BeautifulSoup(self.page_source, features="html.parser")

    def get_href_from_cache(self):
        items = self.redis.smembers(self.href_map)
        return [str(href, encoding="utf-8") for href in items]

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, value):
        self._headers.update(value)

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

    def get_labels(self):
        selector = "#detail > div.tab-con > div:nth-child(2) > div.Ptable > div:nth-child(1) > dl > dl"
        parameters = self.detail.select(selector)
        data = {}
        for parameter in parameters:
            key = parameter.select_one("dt").get_text()
            val = parameter.select_one("dd").get_text()
            data[key] = val
        return data

    def get_