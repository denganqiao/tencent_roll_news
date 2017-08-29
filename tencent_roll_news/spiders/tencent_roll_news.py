#!usr/bin/env python
#-*- coding:utf-8 -*-
"""
@author: Jeff Zhang
@date:   2017-08-28
"""

from scrapy.selector import Selector
import json
import re
from scrapy import Request, Spider
import time
import datetime
from tencent_roll_news.items import TencentRollNewsItem
from tencent_roll_news.settings import DEFAULT_REQUEST_HEADERS
def ListCombiner(lst):
    string = ""
    for e in lst:
        string += e
    return string.replace(' ','').replace('\n','').replace('\t','')\
        .replace('\xa0','').replace('\u3000','').replace('\r','')\
        .replace('[]','')


class TencentNewsSpider(Spider):
    name = 'tencent_news_spider'
    allowed_domains = ['news.qq.com', 'tech.qq.com','ent.qq.com','sport.qq.com','edu.qq.com',
                       'finance.qq.com','games.qq.com','auto.qq.com','house.qq.com']
    # start_urls = ['http://news.qq.com/articleList/rolls/']
    url_pattern = r'(.*)/a/(\d{8})/(\d+)\.htm'

    list_url = 'http://roll.news.qq.com/interface/cpcroll.php?callback=rollback&site={class_}&mode=1&cata=&date={date}&page={page}&_={time_stamp}'
    date_time = datetime.datetime.now().strftime('%Y-%m-%d')
    time_stamp = int(round(time.time()*1000))
    item_num = 0

    def start_requests(self):
        categories = ['tech', 'news', 'ent', 'sports', 'finance', 'games', 'auto', 'edu', 'house']
        # categories = ['house']
        for category in categories:
            DEFAULT_REQUEST_HEADERS['Accept'] = '*/*'
            DEFAULT_REQUEST_HEADERS['Host'] = 'roll.news.qq.com'
            DEFAULT_REQUEST_HEADERS['Referer'] = 'http://{}.qq.com/articleList/rolls/'.format(category)
            yield Request(self.list_url.format(class_=category, date='2017-08-28', page='1', time_stamp=str(self.time_stamp)), callback=self.parse_list, meta={'category':category}, headers=DEFAULT_REQUEST_HEADERS)

    def parse_list(self, response):
        results = json.loads(response.text[9:-1])
        article_info = results['data']['article_info']
        category = response.meta['category']
        for element in article_info:
            time_ = element['time']
            title = element['title']
            column = element['column']
            url = element['url']
            if column != u'图片':
                DEFAULT_REQUEST_HEADERS['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
                DEFAULT_REQUEST_HEADERS['Host'] = '{}.qq.com'.format(category)
                DEFAULT_REQUEST_HEADERS['Referer'] = ''

                yield Request(url, callback=self.parse_news, meta={'column':column,
                                                                   'url':url,
                                                                   'title':title,
                                                                   'time':time_,
                                                                   'category':category
                                                                  },
                                                                   dont_filter=True, headers=DEFAULT_REQUEST_HEADERS)
        list_page = results['data']['page']
        list_count = results['data']['count']
        if list_page < list_count:
            time_stamp = int(round(time.time() * 1000))
            yield Request(self.list_url.format(class_=category, date='2017-08-28', page=str(list_page+1), time_stamp=str(time_stamp)), callback=self.parse_list, meta={'category':category}, dont_filter=True)

    def parse_news(self, response):
        sel = Selector(response)

        url = response.meta['url']
        title = response.meta['title']
        column = response.meta['column']
        time_ = response.meta['time']
        category = response.meta['category']

        pattern = re.match(self.url_pattern, str(response.url))
        source = pattern.group(1)
        date = pattern.group(2)
        date = date[0:4] + '-' + date[4:6] + '-' + date[6:]
        newsId = pattern.group(3)
        contents = ListCombiner(sel.xpath('//p/text()').extract()[:-3])

        # item = TencentRollNewsItem()
        # item['source'] = source
        # item['category'] = category
        # item['time'] = time_
        # item['date'] = date
        # item['contents'] = contents
        # item['title'] = title
        # item['url'] = url
        # item['newsId'] = newsId
        # item['comments'] = 0
        # item['column'] = column
        # return item




        if sel.xpath('//*[@id="Main-Article-QQ"]/div/div[1]/div[2]/script[2]'):
            cmt = sel.xpath('//*[@id="Main-Article-QQ"]/div/div[1]/div[2]/script[2]/text()').extract()[0]
            cmt_id = re.findall(r'cmt_id = (\d*);', cmt)[0]
        elif category == 'tech' and sel.xpath('//*[@id="Main-Article-QQ"]/div/div[1]/div[2]/script'):
            cmt = sel.xpath('//*[@id="Main-Article-QQ"]/div/div[1]/div[2]/script/text()').extract()[0]
            cmt_id = re.findall(r'cmt_id = (\d*);', cmt)[0]
        elif category == 'ent' and sel.xpath('//*[@id="Main-Article-QQ"]/div/div[1]/div[3]/script[2]'):
            cmt = sel.xpath('//*[@id="Main-Article-QQ"]/div/div[1]/div[3]/script[2]/text()').extract()[0]
            cmt_id = re.findall(r'cmt_id = (\d*);', cmt)[0]
        elif category == 'auto' and sel.xpath('//*[@id="Main-Article-QQ"]/div[1]/div[1]/div[3]/div[8]/script'):
            cmt = sel.xpath('//*[@id="Main-Article-QQ"]/div[1]/div[1]/div[3]/div[8]/script/text()').extract()[0]
            cmt_id = re.findall(r'cmt_id = (\d*);', cmt)[0]
        elif category == 'edu' and sel.xpath('//*[@id="Main-Article-QQ"]/div/div[1]/div[3]/script[2]'):
            cmt = sel.xpath('//*[@id="Main-Article-QQ"]/div/div[1]/div[3]/script[2]/text()').extract()[0]
            cmt_id = re.findall(r'cmt_id = (\d*);', cmt)[0]
        elif category == 'house':
            cmt_id = re.findall(r'cmt_id = (\d*);', response.text)[0]
        else:
            item = TencentRollNewsItem()
            item['source'] = source
            item['category'] = category
            item['time'] = time_
            item['date'] = date
            item['contents'] = contents
            item['title'] = title
            item['url'] = url
            item['newsId'] = newsId
            item['comments'] = 0
            item['column'] = column
            return item

        comment_url = 'http://coral.qq.com/article/{}/comment?commentid=0&reqnum=1&tag=&callback=mainComment&_=1389623278900'.format(cmt_id)
        print(comment_url)
        yield Request(comment_url, callback=self.parse_comment, dont_filter=True, meta={'source': source,
                                                                               'date': date,
                                                                               'newsId': newsId,
                                                                               'url': url,
                                                                               'title': title,
                                                                               'contents': contents,
                                                                               'time': time_,
                                                                               'column': column,
                                                                               'category': category
                                                                               })
    def parse_comment(self, response):
        if re.findall(r'"total":(\d*)\,', response.text):
            comments = re.findall(r'"total":(\d*)\,', response.text)[0]
        else:
            comments = 0
        item = TencentRollNewsItem()
        item['category'] = response.meta['category']
        item['source'] = response.meta['source']
        item['time'] = response.meta['time']
        item['date'] = response.meta['date']
        item['contents'] = response.meta['contents']
        item['title'] = response.meta['title']
        item['url'] = response.meta['url']
        item['newsId'] = response.meta['newsId']
        item['comments'] = comments
        item['column'] = response.meta['column']
        return item