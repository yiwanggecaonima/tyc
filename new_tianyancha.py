# 城市为单位 遍历关键字
import json
import random
import multiprocessing
import re
from  urllib.parse import quote
import PIL.Image
import io
import time
from selenium.common.exceptions import TimeoutException
from json.decoder import JSONDecodeError
import numpy as np
import selenium.webdriver
from bs4 import BeautifulSoup
# from fake_useragent import UserAgent
import requests, subprocess, webbrowser
from selenium import webdriver
from lxml import etree
from tyc import chaojiying
import pymongo

class Tianyancha():

    # 常量定义
    url = 'https://www.tianyancha.com/login'

    def __init__(self, username, password,key):
        self.username = username
        self.password = password
        self.chromeOptions = webdriver.ChromeOptions()
        # proxy = "--proxy-server=http://" + '220.165.29.219:4221'
        # self.chromeOptions.add_argument(proxy)
        self.driver = webdriver.Chrome(chrome_options=self.chromeOptions)
        self.client = pymongo.MongoClient('', 27017)
        self.db = self.client['天眼查']
        self.proxy_ip = None
        self.key = key


    def get_proxy_ip(self,proxy_url):
        try:
            response = requests.get(proxy_url)
            if response.status_code == 200:
                proxy = response.text
                return proxy
        except requests.ConnectionError:
            return False

    # 登录天眼查
    def log_in(self):
        # 打开浏览器
        self.driver.get(self.url)

        # 模拟登陆
        time.sleep(1)
        self.driver.find_element_by_xpath("//*[@id='web-content']/div/div[2]/div/div[2]/div/div[3]/div[1]/div[2]").\
            click()
        time.sleep(1)
        self.driver.find_element_by_xpath(
            "//*[@id='web-content']/div/div[2]/div/div[2]/div/div[3]/div[2]/div[2]/input").send_keys(self.username)
        time.sleep(0.3)
        self.driver.find_element_by_xpath(
            "//*[@id='web-content']/div/div[2]/div/div[2]/div/div[3]/div[2]/div[3]/input"). \
            send_keys(self.password)
        # time.sleep(8)
        self.driver.find_element_by_xpath(
            "//*[@id='web-content']/div/div[2]/div/div[2]/div/div[3]/div[2]/div[5]").click()
        time.sleep(8)
        return self.driver
    def search_key(self,key):
        time.sleep(1.5)
        input = self.driver.find_element_by_xpath("//*[@id='home-main-search']")
        input.send_keys(key)
        time.sleep(1)
        submit = self.driver.find_element_by_xpath("//*[@id='web-content']/div/div[1]/div[2]/div/div/div[2]/div[2]/div[1]/div")
        submit.click()
        html = self.driver.page_source
        time.sleep(0.5)
        self.zym(html)
        time.sleep(2)
        return self.driver

    def search_company(self,key):
        # time.sleep(1)
        # content = self.driver.page_source.encode('utf-8')
        # doc = etree.HTML(content)
        # company_link = doc.xpath("//*[@id='web-content']/div/div[1]/div[3]/div[1]/div[2]/div[1]/div/a[2]/@href")[0]
        self.driver.get("https://www.tianyancha.com/search/ohp1?key=" + quote(key))
        # self.driver.find_element_by_xpath("").click()
        content = self.driver.page_source.encode('utf-8')
        doc = etree.HTML(content)
        time.sleep(0.5)
        divs = doc.xpath("//div[@class='folder-body']/div[3]/div[@class='scope-box scope-content-box']/a")
        if len(divs) > 0:
            for div in divs[22:]:
                link = div.xpath("./@href")[0]
                print(link)
                self.get_city(link)
                time.sleep(2)
        else:
            self.get_city("https://www.tianyancha.com/search?searchType=company&key=%E5%9F%B9%E8%AE%AD&base=tw")
            # 这是台湾
        return self.driver

    def get_city(self,shen_link):
        self.driver.get(shen_link)
        doc = etree.HTML(self.driver.page_source.encode('utf-8'))
        city_list = doc.xpath("//div[@class='folder-body']/div[@class='filter-scope -expand']/div[@class='scope-box']/a")
        # if len(city_list) == 1:
        #     city_list = doc.xpath("//*[@id='prov_box']/div[2]/div[2]/div[@class='item']")
        # else:
        #     city_list = doc.xpath("//*[@id='prov_box']/div[2]/div[2]/div[@class='item'and position()>1]")
        for city in city_list:
            city_link = city.xpath("./@href")[0]
            time.sleep(random.uniform(1,2))
            print(city_link)
            self.parse(city_link)
        return self.driver

    def parse(self,link):  # 常规解析 xpath
        self.driver.get(link)
        html = self.driver.page_source
        time.sleep(1)
        self.zym(html)
        doc = etree.HTML(self.driver.page_source)
        script_obj = doc.xpath("//script[@id='_seach_obj']/text()")
        script_obj = script_obj[0] if len(script_obj) > 0 else None
        if script_obj:
            script_data = json.loads(script_obj)
            city = script_data["base"]["name"]
        else:
            city = None
        divs= doc.xpath("//div[@class='result-list sv-search-container']/div[@class='search-item sv-search-company']")
        for div in divs:
            item = {}
            item["城市"] = city
            name = div.xpath(".//div[@class='content']/div[@class='header']/a//text()")
            item['企业名称'] = ''.join(name) if len(name) > 0 else None
            link = div.xpath(".//div[@class='content']/div[@class='header']/a/@href")
            item['网址链接'] = link[0] if len(link) > 0 else None
            fa = div.xpath(".//div[@class='content']/div[@class='info row text-ellipsis']/div[1]/a/text()")
            item['法人代表'] = fa[0] if len(fa) else "未公开"
            money = div.xpath(".//div[@class='content']/div[@class='info row text-ellipsis']/div[2]/span/text()")
            item['注册资金'] = money[0] if len(money) > 0 else "未公开"
            date = div.xpath(".//div[@class='content']/div[@class='info row text-ellipsis']/div[3]/span/text()")
            item['成立时间'] = date[0] if len(date) > 0 else "未公开"
            status = div.xpath(".//div[@class='content']/div[@class='header']/div[@class='tag-common -normal-bg']/text()")
            item['状态'] = status[0] if len(status) > 0 else "未公开"
            # city_ret = re.compile(r'城市：(.*?)&nbsp;')
            # data = re.findall(city_ret, self.driver.page_source)
            # city = data[0] if len(data) > 0 else None
            # item["城市"] = city
            score = div.xpath(".//span[@class='score-num']/text()")
            item["评分"] = score[0] if len(score) > 0 else None
            Additional = div.xpath(".//div[@class='content']/div[@class='match row text-ellipsis']//text()")
            item["附加信息"] = ''.join(Additional) if len(Additional) > 0 else None



            desc = div.xpath(".//div[@class='content']/div[@class='contact row ']/div")
            if len(desc) == 2:
                if desc[0].xpath(".//span[@class='link-click']") and desc[1].xpath("./span[@class='link-click']"):  # 查看更多
                    tel = desc[0].xpath("./script/text()")
                    e = desc[1].xpath("./script/text()")
                    item['联系电话'] = tel[0]
                    item['邮箱'] = e[0]
                elif desc[0].xpath(".//span[@class='link-click']") and not desc[1].xpath("./span[@class='link-click']"):
                    tel = desc[0].xpath("./script/text()")
                    e = desc[1].xpath("./span[2]/text()")
                    item['联系电话'] = tel[0]
                    item['邮箱'] = e[0]

                elif not desc[0].xpath(".//span[@class='link-click']") and desc[1].xpath("./span[@class='link-click']"):
                    tel = desc[0].xpath("./span/span/text()")
                    e = desc[1].xpath("./script/text()")
                    item['联系电话'] = tel[0]
                    item['邮箱'] = e[0]

                elif not desc[0].xpath(".//span[@class='link-click']") and  not desc[1].xpath("./span[@class='link-click']"):
                    tel = desc[0].xpath("./span/span/text()")
                    e = desc[1].xpath("./span[2]/text()")
                    item['联系电话'] = tel[0]
                    item['邮箱'] = e[0]

            elif len(desc) == 1:
                if desc[0].xpath("./span/span[@class='link-click']"):
                    tel = desc[0].xpath("./script/text()")
                    item['联系电话'] = tel[0]
                    item['邮箱'] = '暂无信息'

                elif desc[0].xpath("./span[@class='link-click']"):
                    e = desc[0].xpath("./script/text()")
                    item['联系电话'] = '暂无信息'
                    item['邮箱'] = e[0]

                elif not desc[0].xpath("./span/span[@class='link-click']"):
                    tel = desc[0].xpath("./span/span/text()")
                    item['联系电话'] = tel[0]
                    item['邮箱'] = '暂无信息'

                elif not desc[0].xpath("./span[@class='link-click']"):
                    e = desc[0].xpath("./span[2]/text()")
                    item['邮箱'] = e[0]
                    item['联系电话'] = '暂无信息'
            elif len(desc) == 0:
                continue

            print(item)
            self.save_to_mongo(self.key,item)


        try:
            next_page = doc.xpath("//ul[@class='pagination']/li/a[@class='num -next']/@href")[0]
            time.sleep(0.5)
            if next_page:
                print('当前link',next_page)
                return self.parse(next_page)
            else:
                next_page = doc.xpath("//ul[@class='pagination']/li/a[@class='num -next']/@href")[0]
                print('当前link', next_page)
                return self.parse(next_page)
        except:
            # print("页面枯竭 ")
            pass

    # 11位手机号码优先  其次是带有区号的固定号码  最后是8位或者7位的固定号码
    def is_11(self,tel):
        # print(tel)
        try:
            if len(tel[0]) == 11:
                pl = tel[0]
                # print(pl)
                return pl
            else:
                a, b, c = [], [], []
                we = json.loads(tel[0])
                for i in we:
                    if len(i) == 11:
                        a.append(i)
                    if '-' in i:
                        b.append(i)
                    if len(i) == 8 or len(i) == 7:
                        c.append(i)
                if len(a) > 0:
                    pl = a[0]
                    # print(pl)
                    return pl
                else:
                    if len(b) > 0:
                        pl = b[0]
                        # print(pl)
                        return pl
                    else:
                        if len(c) > 0:
                            pl = c[0]
                            # print(pl)
                            return pl
        except JSONDecodeError:
            pass

    # 详情页 改版后已经失效
    def detail_page(self):
        pass

    def save_to_mongo(self,name,data):
        if self.db[name].update({'企业名称': data['企业名称']}, {'$set': data}, True):
            print('Save to Mongo', data['企业名称'])
        else:
            print('Saved to Mongo Failed', data['企业名称'])

    def zym(self,html,link=None):
        time.sleep(1)
        if '我们只是确认一下你不是机器人' in html:
            one = self.driver.find_element_by_xpath("//div[@class='box2']/div[@class='new-box94']")
            print(one)
            location = one.location
            size = one.size
            print(location)
            print(size)
            top, bottom, left, right = location['y'], location['y'] + size['height'], location['x'], location['x'] + \
                                       size['width']
            top = int(top)
            bottom = int(bottom)
            left = int(left)
            right = int(right)
            print('验证码位置', top, bottom, left, right)
            screenshot = self.driver.get_screenshot_as_png()
            screenshot = PIL.Image.open(io.BytesIO(screenshot))
            captcha = screenshot.crop((left, top, right, bottom))
            captcha.save('hh.png')
            # time.sleep(1)
            code = chaojiying.get_code()
            print(code)
            locations = [[int(number) for number in group.split(',')] for group in code]
            for location in locations:
                print(location)
                selenium.webdriver.ActionChains(self.driver).move_to_element_with_offset(one, location[0], location[1]).click().perform()
                time.sleep(1)
            sub = self.driver.find_element_by_xpath("//*[@id='submitie']")
            sub.click()
            time.sleep(2)
            html = self.driver.page_source
            if '我们只是确认一下你不是机器人' in html:
                return self.zym(html)
            else:
                return self.driver

if __name__ == '__main__':
    for key in ["净水机"]:
        t = Tianyancha('', '', key)
        t.log_in()
        t.search_key(key)
        t.search_company(key)
