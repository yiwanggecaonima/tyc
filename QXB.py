import json
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from lxml import etree
import pymongo
import time

class Qxb():

    def __init__(self):

        self.client = pymongo.MongoClient("localhost",27017)
        self.db = self.client["QXB"]
        self.browser = webdriver.Chrome()
        # self.browser = webdriver.PhantomJS(service_args=SERVICE_ARGS)
        self.wait = WebDriverWait(self.browser,10)
        self.browser.set_window_size(1400, 900)
        self.base_url = "https://www.qixin.com"

    def login(self):
        try:
            self.browser.get('https://www.qixin.com/auth/login')
            input_user = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > div.app-auth-container > div > div.auth-form-container.pull-right > div > div:nth-child(2) > div > div > div > div > div.form-group.margin-t-1x > input')))
            iuput_pwd = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > div.app-auth-container > div > div.auth-form-container.pull-right > div > div:nth-child(2) > div > div > div > div > div:nth-child(2) > input')))
            input_user.send_keys("")
            time.sleep(0.6)
            iuput_pwd.send_keys("")
            time.sleep(15)
            # submit = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > div.app-auth-container > div > div.auth-form-container.pull-right > div > div:nth-child(2) > div > div > div > div > div:nth-child(4) > a')))
            # submit.click()
            return self.browser

        except:
            pass

    def input_search(self):
        # self.browser.get("")
        search_key = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                    'body > div.app-home > div.bg > div.margin-t-70px > div > div > div.margin-t-0-3x.col-lg-offset-3.col-lg-18.col-md-offset-2.col-md-20.col-xs-24 > div > span.twitter-typeahead > input:nth-child(2)')))
        search_key.send_keys("产业园")
        time.sleep(0.5)
        search_submit = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > div.app-home > div.bg > div.margin-t-70px > div > div > div.margin-t-0-3x.col-lg-offset-3.col-lg-18.col-md-offset-2.col-md-20.col-xs-24 > div > span.input-group-addon.search-btn')))
        search_submit.click()
        return self.browser


    def get_page_num(self, city_link):
        self.browser.get(city_link)
        self.yanzheng()
        doc = self.etree_doc(self.browser.page_source)
        total_num = doc.xpath("//div[@class='padding-b-1x font-f2 clearfix']/div[@class='pull-left small']/em/text()")[0]
        if total_num == '5000+':
            page_num = 500
        else:
            page_num = int(total_num) / 10 + 1
        return page_num

    def parse_page(self):
        doc = self.etree_doc(self.browser.page_source.encode('utf-8'))
        divs = doc.xpath("//div[@class='padding-h-1x border-h-b4 border-t-b4 app-list-items']/div[2]/div[@class='col-xs-24 padding-v-1x margin-0-0x border-b-b4 company-item']")
        city = doc.xpath("//div[@class='col-xs-24 small font-f3 margin-b-0-3x  search-condition-row']//div[@class='wrapper expand']/div/a/text()")
        city = ' '.join(city) if len(city) > 0 else None
        for div in divs:
            item = {}
            link = div.xpath("./div[@class='col-2']//div[@class='company-title']/a/@href")
            item["link"] = self.base_url + link[0] if len(link) > 0 else None
            name = div.xpath("./div[@class='col-2']//div[@class='company-title']/a//text()")
            item["name"] = ''.join(name) if len(name) >0 else None
            fa = div.xpath("./div[@class='col-2']//div[@class='legal-person'][1]//text()")
            item["Representative"] = ''.join(fa).split('：')[-1] if len(fa) > 0 else None
            tel = div.xpath("./div[@class='col-2']//div[@class='legal-person'][2]/span[@class='margin-r-1x']//text()")
            item["tel"] = ''.join(tel).split('：')[-1] if len(tel) > 0 else None
            email = div.xpath("./div[@class='col-2']//div[@class='legal-person'][2]/span[2]/a/text()")
            item["email"] = ''.join(email) if len(email) > 0 else None
            addr = div.xpath("./div[@class='col-2']//div[@class='legal-person'][3]/span/text()")
            if len(addr) > 0:
                item["addr"] = ''.join(addr).split('：')[-1]
            else:
                addr = ''.join(div.xpath("./div[@class='col-2']//div[@class='legal-person'][2]/span/text()"))
                item["addr"] = ''.join(addr).replace(' ','') if len(addr) > 0 else "确切地址未显示"
            stat = div.xpath("./div[@class='col-2']//div[@class='company-tags']/span[@class='label label-red']/text()")
            item["stat"] = stat[0] if len(stat) > 0 else None
            qian = div.xpath("./div[@class='col-3 clearfix font-f2']/div[@class='col-3-1 text-center content-text']/text()")
            item["Money"] = qian[0] if len(qian) > 0 else None
            date_time = div.xpath("./div[@class='col-3 clearfix font-f2']/div[@class='col-3-2 text-center content-text']/text()")
            item["date_time"] =date_time[0] if len(date_time) > 0 else None
            new_addr_or_Additional = div.xpath("./div[@class='col-2']//div[@class='match-item']/span//text()")
            item["new_addr_or_Additional"] = ''.join(new_addr_or_Additional) if len(new_addr_or_Additional) > 0 else "没有最新地址或附加信息"
            item["city"] = city
            print(item)
            self.save_to_mongo(item)
        time.sleep(0.6)

    def next_page(self,page_num):
        self.yanzheng()
        try:
            next_page_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                         'body > div.container.margin-t-2x > div > div.col-md-18 > div.padding-t-1x.clearfix > div > div > div > input')))
            next_page_input.clear()
            next_page_input.send_keys(page_num)
            next_page_submit = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,
                                                 'body > div.container.margin-t-2x > div > div.col-md-18 > div.padding-t-1x.clearfix > div > div > div > button')))
            time.sleep(0.2)
            next_page_submit.click()
        except:
            pass
        self.yanzheng()
        time.sleep(0.5)
        return self.parse_page()

    def etree_doc(self,html):
        doc = etree.HTML(html)
        return doc

    def save_to_mongo(self,data):
        if self.db['qxb'].update({'name': data['name']}, {'$set': data}, True):
            print('Save to Mongodb', data['name'])
        else:
            print('Saved to Mongodb Failed', data['name'])

    def yanzheng(self):
        if "点击按钮进行验证" in self.browser.page_source:
            time.sleep(10)
            return self.browser
            # yz_submit = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,
            #                                             'body > div.border-t-b4 > div > div > div > div > button')))
            # time.sleep(0.6)
            # yz_submit.click()
            # time.sleep(1)
            # try:
            #     one = self.browser.find_element_by_xpath("/html/body/div[12]/div[2]")
            # except:
            #     one = self.browser.find_element_by_xpath("/html/body/div[7]/div[2]")
            # print(one)
            # location = one.location
            # size = one.size
            # print(location)
            # print(size)
            # top, bottom, left, right = location['y'], location['y'] + size['height'], location['x'], location['x'] + \
            #                            size['width']
            # top = int(top)
            # bottom = int(bottom)
            # left = int(left)
            # right = int(right)
            # print('验证码位置', top, bottom, left, right)
            # screenshot = self.browser.get_screenshot_as_png()
            # import PIL.Image
            # screenshot = PIL.Image.open(io.BytesIO(screenshot))
            # captcha = screenshot.crop((left, top, right, bottom))
            # captcha.save('hh.png')
            # code = chaojiying.get_code()
            # print(code)
            # locations = [[int(number) for number in group.split(',')] for group in code]
            # for location in locations:
            #     print(location)
            #     selenium.webdriver.ActionChains(self.browser).move_to_element_with_offset(one, location[0],
            #                                                                              location[1]).click().perform()
            #     time.sleep(random.choice([0.5,1,0.8,0.7]))
            # submit = self.browser.find_element_by_xpath("/html/body/div[7]/div[2]/div[6]/div/div/div[3]/a/div")
            # submit.click()
            # time.sleep(1)
            # if '点击按钮进行验证' in self.browser.page_source:
            #     return self.yanzheng()
            # else:
            #     return self.browser

    def run(self):
        self.login()
        # self.search()
        self.yanzheng()
        # with open("/home/parrot/PycharmProjects/Qxb/First_class_city.txt","r") as f:
        #     for data_str in f.readlines():
        #         data = json.loads(data_str.strip('\n'))
        #         province_code = data["province_code"]
        #         city_code = data["city_code"]
        for province_code in ["11","12","31","50"]:
            url = "https://www.qixin.com/search?&area.province=" + province_code +"&key=产业园"
            # url = "https://www.qixin.com/search?area.city=" + city_code +"&area.province=" + province_code +"&key=众创空间"
            page_nums = self.get_page_num(url)
            for page_num in range(1,int(page_nums)+1):
                self.next_page(page_num)

if __name__ == '__main__':
    Q = Qxb()
    Q.run()
