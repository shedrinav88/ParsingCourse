from urllib.parse import urljoin
from scrapy import Selector
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose, Join
from .items import HeadhunterItem, CompanyHeadhunterItem


def get_company_url(item):
    base_url = "https://hh.ru"
    return urljoin(base_url, item)


def clear_unicode(value):
    return value.replace("\xa0", "")


class HeadhunterLoader(ItemLoader):
    default_item_class = HeadhunterItem
    url_out = TakeFirst()
    title_out = TakeFirst()
    author_url_out = TakeFirst()
    salary_in = MapCompose(Join(separator=''), clear_unicode)
    salary_out = Join(separator='')
    description_out = Join(separator='')
    author_url_in = MapCompose(get_company_url)
    company_name_in = MapCompose(Join(separator=''), clear_unicode)
    company_name_out = Join(separator='')


class CompanyHeadhunterLoader(ItemLoader):
    default_item_class = CompanyHeadhunterItem
    url_out = TakeFirst()
    company_name_in = MapCompose(Join(separator=''), clear_unicode)
    company_name_out = Join(separator='')
    site_url_out = TakeFirst()
    description_in = MapCompose(Join(separator=''), clear_unicode)
    description_out = Join(separator='')


