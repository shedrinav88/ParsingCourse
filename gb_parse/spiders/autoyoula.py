import scrapy
import re
import pymongo
from dotenv import load_dotenv
import os


class AutoyoulaSpider(scrapy.Spider):
    name = 'autoyoula'
    allowed_domains = ['auto.youla.ru']
    start_urls = ['http://auto.youla.ru/']

    css_query = {
        "brands": "div.TransportMainFilters_brandsList__2tIkv div.ColumnItemList_container__5gTrc a.blackLink",
        "pagination": "div.Paginator_block__2XAPy a.Paginator_button__u1e7D",
        "ads": "div.SerpSnippet_titleWrapper__38bZM a.blackLink",
    }

    data_query = {
        'title': 'div.AdvertCard_advertTitle__1S1Ak::text',
        'price': 'div.AdvertCard_price__3dDCr::text',
        'description': 'div.AdvertCard_descriptionInner__KnuRi::text',
        'photos': 'img.PhotoGallery_photoImage__2mHGn',
        'characteristics': 'div.AdvertSpecs_row__ljPcX div.AdvertSpecs_label__2JHnS::text',
        'user_url': '//script[contains(text(), "window.transitState")]'
    }

    load_dotenv('.env')
    data_base = pymongo.MongoClient(os.getenv("DATA_BASE_URL"))
    database = data_base["gb_parse_12_01_2021"]

    def save(self, data):
        collection = self.database["autoyoula"]
        collection.insert_one(data)

    @staticmethod
    def gen_tasks(response, link_list, callback):
        for link in link_list:
            yield response.follow(link.attrib.get("href"), callback=callback)

    def parse(self, response):
        yield from self.gen_tasks(
            response, response.css(self.css_query["brands"]), self.brand_parse
        )

    def brand_parse(self, response):
        yield from self.gen_tasks(
            response, response.css(self.css_query["pagination"]), self.brand_parse
        )
        yield from self.gen_tasks(response, response.css(self.css_query["ads"]), self.ads_parse)

    def ads_parse(self, response):
        data = {}
        for key, query in self.data_query.items():
            if key == 'photos':
                data[key] = response.css(query).xpath('@src').getall()
            elif key == 'characteristics':
                keys = response.css(query).getall()
                values_1 = response.css('div.AdvertSpecs_data__xK2Qx::text').getall()
                values_2 = response.css('div.AdvertSpecs_data__xK2Qx').css('a.blackLink::text').getall()
                values_1.insert(0, values_2[0])
                values_1.insert(2, values_2[1])
                data[key] = dict(zip(keys, values_1))
            elif key == 'user_url':
                script_text = response.xpath(query).get()
                data[key] = 'https://youla.ru/user/' + re.findall(r'youlaId%22%2C%22([^%]+)%22%2C%22avatar', script_text)[0]
            else:
                data[key] = response.css(query).get()

        self.save(data)