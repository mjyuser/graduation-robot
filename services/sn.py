from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from bs4 import BeautifulSoup
from utils import helper


class sn:
    key = "%E6%99%BA%E8%83%BD%E7%A9%BA%E8%B0%83"
    platform = "苏宁"

    def __init__(self):
        options = Options()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)
        self.home_page = None
        self.evaluate_page = None
        self.home_url = None
        self.evaluate_warp = None

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
