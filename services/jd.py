from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from bs4 import BeautifulSoup
from model.db import redis_client

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

    def get_driver(self):
        if self.driver is None:
            self.driver = webdriver.Chrome(options=self.options)
        return self.driver

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
            self.get_driver().get(href)
            self.detail = BeautifulSoup(self.page_source, features="html.parser")

        return self.detail

    def save_href(self, href) -> None:
        if not self.is_spider(href):
            self.redis.sadd(self.href_map, href)

    def is_spider(self, href):
        return self.redis.sismember(self.href_map, href)
