from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.common.exceptions import NoSuchAttributeException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import json
from services import chaojiying
import requests
import os
from model.db import config, redis_client, session
from bs4 import BeautifulSoup
from utils import helper
import model.airConditioner as Conditioner
from sqlalchemy import exc


class taobao():
    href_map_key = "taobao_href"
    spider_key = "taobao_spider"
    platform = "淘宝"

    def __init__(self):
        self.href_list = None
        self.cookie_expired = False
        options = self.__set_options()
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 30)
        self.driver.maximize_window()
        self.filepath = self.get_filepath()
        self.cookie = None
        # 检查登录态
        self.__check_login()
        if self.cookie is None or self.cookie_expired is True:
            self.login()

    @staticmethod
    def __set_options():
        options = Options()
        # # 设置开发者模式
        options.add_experimental_option("excludeSwitches", ['enable-automation'])

        return options

    # 检查是否登录
    def __check_login(self):
        if os.path.exists(self.filepath) is True:
            try:
                nickname = self.get_taobao_nick_name()
                if nickname is None:
                    self.cookie_expired = True
                else:
                    self.nickname = nickname.text
            except Exception as e:
                os.remove(self.get_filepath())
                print("cookies 过期, 删除cookie文件;", e)
                self.cookie_expired = True
                self.driver.delete_all_cookies()

    # 通过微博登录淘宝
    def login(self):
        self.driver.get("https://login.taobao.com/member/login.jhtml")
        self.driver.find_element_by_class_name("J_Quick2Static").click()
        self.driver.find_element_by_class_name("weibo-login").click()
        username = self.driver.find_element_by_name("username")
        username.send_keys(config.weibo["username"])
        time.sleep(1)
        password = self.driver.find_element_by_name("password")
        password.send_keys(config.weibo["password"])
        time.sleep(1)
        captcha = self.get_captcha()
        if captcha is not None:
            captcha_input = self.driver.find_element_by_name("verifycode")
            client = chaojiying.Chaojiying(config.chaojiying["username"], config.chaojiying["password"],
                                           config.chaojiying["soft_id"])
            client.PostPic(captcha, 1902)
            captcha_input.send_keys(client.pic_str)
        self.driver.find_element_by_class_name("W_btn_g").click()

        nickname = self.__get_nickname()
        if nickname is None:
            print("登录淘宝失败")
            return
        # 存储cookies
        self.cookie = self.driver.get_cookies()
        self.serialization_cookies()

    def serialization_cookies(self):
        if self.cookie is not None:
            json_cookies = json.dumps(self.cookie)
            with open("cookie.json", "w") as f:
                f.write(json_cookies)

    # 添加cookie时需要向先调用driver.get(), 是的url和cookie的domian处在同一级域名下
    def deserialization_cookies(self, filepath):
        with open(filepath, "r+", encoding="utf-8") as f:
            cookies = json.loads(f.read())
            self.cookie = cookies
            for item in cookies:
                if "expiry" in item:
                    # 需要将expiry 的值从float -> int
                    item["expiry"] = int(item["expiry"])
                self.driver.add_cookie(item)
            return cookies

    # 获取json的配置文件
    def get_filepath(self):
        rootpath = self.get_rootpath()
        return rootpath + "/cookie.json"

    def get_rootpath(self):
        curpath = os.path.abspath(os.path.dirname(__file__))
        rootpath = curpath[:curpath.find("appliance") + len("appliance")]
        return rootpath

    # 获取列表页
    def get_list_url(self, page=0):
        url = "https://uland.taobao.com/sem/tbsearch?keyword={key}&page={page}".format(key=self.key, page=page)
        return url

    def get_captcha(self, name="captcha.png"):
        try:
            element = self.driver.find_element_by_xpath('//img[@node-type="verifycode_image"]')
            if element is not None:
                src = element.get_attribute("src")
                if src is None or src.strip() == "":
                    return None
                img_response = requests.get(src)
                if img_response.status_code != 200:
                    print("get captcha failed")
                    return
                with open(name, 'wb') as f:
                    f.write(img_response.content)
                return img_response.content
        except NoSuchAttributeException:
            print("get captcha failed")
        return None

    def get_taobao_nick_name(self):
        self.driver.get("https://www.taobao.com/")
        self.deserialization_cookies(self.filepath)
        self.driver.get("https://www.taobao.com/")
        taobao_name = self.__get_nickname()
        return taobao_name

    def __get_nickname(self):
        return self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                               ".site-nav-bd > ul.site-nav-bd-l > li#J_SiteNavLogin > "
                                                               "div.site-nav-menu-hd > div.site-nav-user > "
                                                               "a.site-nav-login-info-nick")))

    def get_goods_list(self, force=False):
        self.__load_href()
        if self.href_list is None or force is True:
            # 输入搜索框
            try:
                search_input = self.driver.find_element_by_class_name("search-combobox-input")
                search_input.send_keys(r"智能空调")
                search_input.send_keys(Keys.ENTER)

                # 获取当前页的所有详情页的url
                self.__get_detail_url(self.driver.page_source)
                next_page = self.driver.find_element_by_link_text(r"下一页")
                count = 0
                selector = (By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > ul > li.item.next > a")
                try:
                    while count <= 50 or next_page is not None:
                        self.__get_detail_url(self.driver.page_source)
                        #  模拟点击下一页
                        count = count + 1
                        next_button = self.wait.until(EC.presence_of_element_located(selector))
                        next_button.click()
                except Exception as e:
                    print("获取下一页异常, message: ", e)
                    return

                # 加载数据列表
                self.__load_href()

            except Exception as e:
                print("获取家电列表异常")
                print(e)
                return

        return self.href_list

    def parse_list(self):
        list_page = self.get_rootpath() + "/list.html"
        page = open(list_page, "r")
        return self.__get_detail_url(page)

    def __get_detail_url(self, page):
        bs = BeautifulSoup(page, features="html.parser")
        data = bs.find(id="mainsrp-itemlist")
        if data is not None:
            items = data.select(".items > .J_MouserOnverReq")
            if items is not None:
                for item in items:
                    message_box = item.select_one(".J_IconMoreNew > .title > a")
                    if message_box is not None:
                        href = message_box["href"]
                        if not href.startswith("http"):
                            href = "https:" + href
                        if redis_client.sismember(self.href_map_key, href) is False:
                            redis_client.sadd(self.href_map_key, href)

    # 加载列表
    def __load_href(self):
        count = redis_client.scard(self.href_map_key)
        if self.href_list is None or len(self.href_list) < count:
            members = redis_client.smembers(self.href_map_key)
            self.href_list = [str(href, encoding="utf-8") for href in members]

    def get_page_message(self, href):
        print(href)
        self.driver.get(href)
        try:
            login_btn = self.driver.find_element_by_link_text("请登录")
            if login_btn is not None:
                self.login()
                self.driver.get(href)
        except Exception as e:
            print(e)

        bs4 = BeautifulSoup(self.driver.page_source, features="html.parser")
        basic = bs4.select_one(".tb-property")
        price = origin_price = score = 0
        tags_str = labels_str = title = ""
        if basic is not None:
            title_box = basic.select_one(".tb-detail-hd > h1 > a")
            if title_box is None:
                return
            title = title_box.get_text()
            tag = basic.select_one("#J_DetailMeta > div.tm-clear > div.tb-property > div > div.tb-detail-hd > p")
            if tag is not None:
                tags = helper.get_char(tag.get_text())
                tags_str = ",".join(tags)
            price = self.get_price(basic)
            origin_price = self.get_origin_price(basic)

        merchant = bs4.select_one("#shopExtra > div.slogo > a > strong").get_text()
        parameter_list = bs4.select(".tm-tableAttr > tbody > tr:not(.tm-tableAttrSub)")
        parameter = {}
        if parameter_list is not None:
            for item in parameter_list:
                parameter[item.select_one("th").get_text()] = item.select_one("td").get_text()

        ignore = False
        # 用户评价需要点击后加载
        try:
            self.driver.execute_script("window.scrollTo(0, 200)")
            tags_button = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#J_TabBar > li:nth-child(3)")))
            tags_button.click()
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#J_Reviews > div > "
                                                                             "div.rate-header")))
        except Exception as e:
            print(e)
            ignore = True

        if ignore is False:
            bs4 = BeautifulSoup(self.driver.page_source, features="html.parser")
            rate_box = bs4.select_one("#J_Reviews > div > div.rate-header")
            if rate_box is None:
                rate_box = bs4.select_one("#J_Reviews > div > div.rate-header.rate-header-tags")
            if rate_box is not None:
                score = rate_box.select_one(".rate-score > strong")
                if score is not None:
                    score = self.__transToCentesimal(score.get_text())
                tag_list = rate_box.select(".rate-tag-inner > span > a")
                if tag_list is not None:
                    labels = [helper.get_char(tag.get_text())[0] for tag in tag_list]
                    labels_str = ",".join(labels)
            else:
                print("not found tag list")
        print(score)
        model = Conditioner.airConditioner(tag_str=tags_str, link=self.driver.current_url,
                                           title=title, merchant=merchant,
                                           property=parameter, price=float(price) * 100,
                                           origin_price=float(origin_price) * 100,
                                           feedback=score, labels=labels_str, platform=self.platform)  # 转化成百分制
        session.add(model)

        try:
            session.commit()
            redis_client.sadd(self.spider_key, href)
        except exc.SQLAlchemyError as e:
            print("insert taobao data failed.", e)
            return

    def __get_price_box(self, basic):
        if basic is not None:
            return basic.select_one(".tm-fcs-panel")

    def get_origin_price(self, basic):
        price_box = self.__get_price_box(basic)
        if price_box is not None:
            price = price_box.select_one(".tm-price-panel > dd > .tm-price")
            if price is None:
                return 0
            return price.get_text()

    def get_price(self, basic):
        price_box = self.__get_price_box(basic)
        if price_box is not None:
            price = None
            try:
                price = price_box.select_one(".tm-promo-panel > dd > .tm-promo-price > .tm-price").get_text()
            except AttributeError:
                price = price_box.select_one(".tm-promo-panel > span.tm-price").get_text()
            finally:
                if price is None:
                    return 0
                return price

    # 检查是否爬取过当前页面
    def is_spider(self, href):
        if redis_client.sismember(self.spider_key, href):
            return True
        return False

    @staticmethod
    def __transToCentesimal(score):
        return float(score) * 20
