import os
from dotenv import load_dotenv
import requests
from urllib.parse import urljoin
import bs4
import pymongo
from datetime import datetime

date_dict = {'января': '01',
             'февраля': '02',
             'марта': '03',
             'апреля': '04',
             'мая': '05',
             'июня': '06',
             'июля': '07',
             'августа': '08',
             'сентября': '09',
             'октября': '10',
             'ноября': '11',
             'декабря': '12',
            }


class MagnitParser:

    def __init__(self, start_url, data_base):
        self.start_url = start_url
        self.database = data_base["gb_parse_12_01_2021"]

    @staticmethod
    def get_day_from(tag):
        return tag.find('div', attrs={'class': 'card-sale__date'}).text[1:-1].rsplit('\n')[0].rsplit(' ')[1]


    @staticmethod
    def get_month_from(tag):
        month = tag.find('div', attrs={'class': 'card-sale__date'}).text[1:-1].rsplit('\n')[0].rsplit(' ')[2]
        return date_dict[month]

    @staticmethod
    def get_day_to(tag):
        return tag.find('div', attrs={'class': 'card-sale__date'}).text[1:-1].rsplit('\n')[1].rsplit(' ')[1]

    @staticmethod
    def get_month_to(tag):
        month = tag.find('div', attrs={'class': 'card-sale__date'}).text[1:-1].rsplit('\n')[1].rsplit(' ')[2]
        return date_dict[month]

    @staticmethod
    def __get_response(url, *args, **kwargs):
        # todo обработать ошибки запросов и статусов тут
        response = requests.get(url, *args, **kwargs)
        return response

    @property
    def data_template(self):
        return {
            "url": lambda tag: urljoin(self.start_url, tag.attrs.get("href")),
            "product_name": lambda tag: tag.find(
                "div", attrs={"class": "card-sale__title"}
            ).text,
            "promo_name": lambda tag: tag.find(
                "div", attrs={"class": "card-sale__name"}
            ).text,
            "old_price": lambda tag: float(tag.find("div", attrs={"class": "label__price label__price_old"}
            ).text[1:-1].replace('\n', '.')),
            "new_price": lambda tag: float(tag.find("div", attrs={"class": "label__price label__price_new"}
            ).text[1:-1].replace('\n', '.')),
            "img_url": lambda tag: urljoin(self.start_url, tag.find(
                'img', attrs={'class': "lazy"}).get('data-src')),
            "date_from": lambda tag: datetime.strptime(self.get_day_from(tag) + ' ' + self.get_month_from(tag) +
                                                       ' ' + str(datetime.now().year), '%d %m %Y'),
            "date_to": lambda tag: datetime.strptime(self.get_day_to(tag) + ' ' + self.get_month_to(tag) +
                                                       ' ' + str(datetime.now().year), '%d %m %Y'),
            }

    @staticmethod
    def __get_soup(response):
        return bs4.BeautifulSoup(response.text, "lxml")

    def run(self):
        for product in self.parse(self.start_url):
            self.save(product)

    def validate_product(self, product_data):
        return product_data

    def parse(self, url):
        soup = self.__get_soup(self.__get_response(url))
        catalog_main = soup.find("div", attrs={"class": "сatalogue__main"})
        for product_tag in catalog_main.find_all(
            "a", attrs={"class": "card-sale"}, reversive=False
        ):
            yield self.__get_product_data(product_tag)

    def __get_product_data(self, product_tag):
        data = {}
        for key, pattern in self.data_template.items():
            try:
                data[key] = pattern(product_tag)
            except AttributeError:
                continue
        return data

    def save(self, data):
        collection = self.database["magnit_product_hw2"]
        collection.insert_one(data)

if __name__ == "__main__":
    load_dotenv('.env')
    data_base = pymongo.MongoClient(os.getenv("DATA_BASE_URL"))
    parser = MagnitParser("https://magnit.ru/promo/?geo=moskva", data_base)
    parser.run()
