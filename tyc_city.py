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
from fake_useragent import UserAgent
import requests, subprocess, webbrowser
from selenium import webdriver
from lxml import etree
from tianyan import chaojiying
import pymongo

class Tianyancha():

    # 常量定义
    url = 'https://www.tianyancha.com/login'

    def __init__(self, username, password,key):
        self.username = username
        self.password = password
        self.chromeOptions = webdriver.ChromeOptions()
        # proxy = "--proxy-server=http://" + '125.111.149.239:4205'
        # self.chromeOptions.add_argument(proxy)
        self.driver = webdriver.Chrome(chrome_options=self.chromeOptions)
        self.client = pymongo.MongoClient('localhost')
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
        self.driver.get("https://www.tianyancha.com/search/ohp1?searchType=company&key=" + quote(key))
        # self.driver.find_element_by_xpath("").click()
        content = self.driver.page_source.encode('utf-8')
        doc = etree.HTML(content)
        time.sleep(0.5)
        divs = doc.xpath("//*[@id='prov_box']/div[1]/div[2]/div[@class='item'and position()>1]")
        if divs:
            for div in divs:
                link = div.xpath("./a/@href")[0]
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
        city_list = doc.xpath("//*[@id='prov_box']/div[2]/div[2]/div[@class='item']")
        if len(city_list) == 1:
            city_list = doc.xpath("//*[@id='prov_box']/div[2]/div[2]/div[@class='item']")
        else:
            city_list = doc.xpath("//*[@id='prov_box']/div[2]/div[2]/div[@class='item'and position()>1]")
        for city in city_list:
            city_link = city.xpath("./a/@href")[0]
            self.parse(city_link)
        return self.driver

    def parse(self,link):
        self.driver.get(link)
        html = self.driver.page_source
        time.sleep(1)
        self.zym(html)
        doc = etree.HTML(self.driver.page_source)
        divs= doc.xpath("//div[@class='result-list sv-search-container']/div[@class='search-item sv-search-company']")
        for div in divs:
            item = {}
            Additional = div.xpath(".//div[@class='content']/div[@class='match text-ellipsis']/span[2]/text()")
            item["附加信息"] = ''.join(Additional) if len(Additional) > 0 else None
            name = div.xpath(".//div[@class='content']/div[@class='header']/a//text()")
            item['企业名称'] = ''.join(name) if len(name) > 0 else None
            # if '租赁' in item['企业名称'] or '办公设备' in item['企业名称']:
            link = div.xpath(".//div[@class='content']/div[@class='header']/a/@href")
            item['网址链接'] = link[0] if len(link) > 0 else None
            City = doc.xpath("//*[@id='prov_box']/div[2]/div[1]/span[1]/text()")
            # Qu = doc.xpath("//*[@id='prov_box']/div[3]/div[1]/span[1]/text()")
            if len(City) >0 and City[0] == '全部':
                city = '特别行政区'
            elif City[0] == '市':
                city = '首页城市'
            else:
                city =  City[0]
            item['区域'] = city
            fa = div.xpath(".//div[@class='content']/div[@class='info']/div[1]//text()")
            item['法人代表'] = fa[1] if len(fa) else "未公开"
            money = div.xpath(".//div[@class='content']/div[@class='info']/div[2]//text()")
            item['注册资金'] = money[1] if len(money) > 0 else "未公开"
            date = div.xpath(".//div[@class='content']/div[@class='info']/div[3]//text()")
            item['成立时间'] =date[1] if len(date) > 0 else "未公开"
            status = div.xpath(".//div[@class='content']/div/div/text()")
            item['状态'] = status[0] if len(status) > 0 else "未公开"
            desc = div.xpath(".//div[@class='content']/div[@class='contact']/div")
            if len(desc) == 2:
                content1 = ''.join(desc[0].xpath(".//text()"))
                content2 = ''.join(desc[1].xpath(".//text()"))
                if ('联系电话' in content1 and '查看更多' in content1) and ('邮箱' in content2 and '查看更多' in content2):
                    tel = desc[0].xpath(".//text()")
                    e = desc[1].xpath(".//text()")
                    # print(tel[1:3])
                    item['联系电话'] = self.is_11(tel[1:3])
                    item['邮箱'] = e[1:3][0]
                elif ('联系电话' in content1 and '查看更多' not in content1) and ('邮箱' in content2 and '查看更多' not in content2):
                    tel = desc[0].xpath(".//text()")
                    e = desc[1].xpath(".//text()")
                    item['联系电话'] = tel[1]
                    item['邮箱'] = e[1]

                elif ('邮箱' in content2 and '查看更多' in content2) and ('联系电话' in content1 and '查看更多' not in content1):
                    tel = desc[0].xpath(".//text()")
                    e = desc[1].xpath(".//text()")
                    item['联系电话'] = tel[1]
                    item['邮箱'] = e[1:3][0]
                elif ('邮箱' in content2 and '查看更多' not in content2) and ('联系电话' in content1 and '查看更多' in content1):
                    tel = desc[0].xpath(".//text()")
                    e = desc[1].xpath(".//text()")
                    item['联系电话'] = self.is_11(tel[1:3])
                    item['邮箱'] = e[1]

            elif len(desc) == 1:
                content = ''.join(desc[0].xpath(".//text()"))
                if '联系电话' in content and '查看更多' in content:
                    tel = desc[0].xpath(".//text()")
                    # print(tel[1:3])
                    item['联系电话'] = self.is_11(tel[1:3])
                    item['邮箱'] = '暂无信息'
                elif '联系电话' in content and '查看更多' not in content:
                    tel = desc[0].xpath(".//text()")
                    item['联系电话'] = tel[1]
                    item['邮箱'] = '暂无信息'
                elif '邮箱' in content and '查看更多' in content:
                    email = desc[0].xpath(".//text()")
                    item['邮箱'] = email[1:3][0]
                    item['联系电话'] = '暂无信息'
                elif '邮箱' in content and '查看更多' not in content:
                    email = desc[0].xpath(".//text()")
                    item['邮箱'] = email[1]
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

            # item = {}
            # item['name'] = name
            # item['link'] = link
            # print(name,link,city,fa,money,date,status)
            # self.save_to_mongo(item)
            # print(name)
    #         item = {}
    #         try:
    #             self.parse_detail(link,item)
    #         except TimeoutException:
    #             self.parse_detail(link,item)
    #     next_page = doc.xpath("//ul[@class='pagination']/li/a[@class='num -next']/@href")[0]
    #     time.sleep(0.5)
    #     if next_page:
    #         print('当前link',next_page)
    #         return self.parse(next_page)
    #     else:
    #         pass
    #     return self.driver
    #
    # def parse_detail(self,link,item):
    #     l = [0.2,0.3,0.4]
    #     time.sleep(random.choice(l))
    #     self.driver.get(link)
    #     html = self.driver.page_source
    #     if '系统检测到您非人类行为' in html:
    #         self.proxy_ip = self.get_proxy_ip(self.proxy_url)
    #         proxy = "--proxy-server=http://" + self.proxy_ip
    #         self.chromeOptions.add_argument(proxy)
    #         return self.parse_detail(link,item)
    #     self.zym(html)
    #     doc = etree.HTML(self.driver.page_source)
    #     base = doc.xpath("//div[@id='company_web_top']//div[@class='content']")[0]
    #     item['link'] = link
    #     item['name'] = base.xpath("./div[@class='header']/h1/text()")[0]
    #     # item['history_name'] = doc.xpath("")
    #     representative = doc.xpath("//div[@class='humancompany']/div[@class='name']/a/text()")
    #     item['representative'] = representative[0] if len(representative) > 0 else None
    #     capital = doc.xpath("//*[@id='_container_baseInfo']/table[1]/tbody/tr[1]/td[2]/div[2]/@title")
    #     item['capital'] = capital[0] if len(capital) > 0 else None
    #     date = doc.xpath("//*[@id='_container_baseInfo']/table[1]/tbody/tr[2]/td/div[2]/text/text()")
    #     if len(date) > 0:
    #         date = date[0]
    #         font = {}
    #         font['0'] = 3;font['1'] = 8;font['2'] = 4;font['3'] = 2;font['4'] = 0;font['5'] = 1;font['6'] = 7;font['7'] = 5;font['8'] = 9;font['9'] = 6
    #         new_date = ''
    #         d = date[0:4] + date[5:7] + date[8:]
    #         for i in d:
    #             new_date += str(font[i])
    #         item['date'] = new_date
    #     else:
    #         item['date'] = '暂无信息'
    #     status = base.xpath(".//div[@class='tag tag-company-status-normal mr10']/text()")
    #     item['status'] = status[0] if len(status) > 0 else '暂无信息'
    #     tel = doc.xpath("//*[@id='company_web_top']/div[2]/div[3]/div[3]/div[1]/div[1]/span[2]/text()")
    #     item['tel'] = tel[0] if len(tel) > 0 else '暂无信息'
    #     email = doc.xpath("//*[@id='company_web_top']/div[2]/div[3]/div[3]/div[1]/div[2]/span[2]/text()")
    #     item['email'] = email[0] if len(email) > 0 else '暂无信息'
    #     address = doc.xpath("//*[@id='company_web_top']/div[2]/div[3]/div[3]/div[2]/div[2]/span[2]/@title")
    #     if len(address) > 0:
    #         address = address
    #     elif address == []:
    #         address = doc.xpath("//*[@id='company_web_top']/div[2]/div[3]/div[3]/div[2]/div[2]/span[2]/text()")
    #         if address == []:
    #             address = doc.xpath("//*[@id='company_web_top']/div[2]/div[3]/div[3]/div[2]/div[2]/text()")
    #     item['address'] = address[0]
    #     info_detail = doc.xpath("//*[@id='company_base_info_detail']/text()")
    #     item['info_detail'] = ''.join(info_detail).strip('\n ') if len(info_detail) > 0 else '暂无信息'
    #     print(item)
    #     # self.save_to_mongo(item)
    #     return self.driver

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
    for key in [""]:
        t = Tianyancha('','',key)
        t.log_in()
        t.search_key(key)
        t.search_company(key)
