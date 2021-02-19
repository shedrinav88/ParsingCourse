import scrapy
from gb_parse.loaders import HeadhunterLoader, CompanyHeadhunterLoader


class HeadhunterSpider(scrapy.Spider):
    name = 'headhunter'
    allowed_domains = ['hh.ru']
    start_urls = ['https://hh.ru/search/vacancy?schedule=remote/']

    xpath_query = {
        "pagination": "//div[@data-qa='pager-block']//a",
        "ads": "//a[@data-qa='vacancy-serp__vacancy-title']",
        "company_page": "//a[@data-qa='vacancy-company-name']",
        "company_vacancies": "//a[@data-qa='employer-page__employer-vacancies-link']",
    }
    data_xpath = {
        "title": "//h1[@data-qa='vacancy-title']/text()",
        "salary": "//p[@class='vacancy-salary']//text()",
        "description": "//div[@data-qa='vacancy-description']//text()",
        "skills": '//div[@class="bloko-tag-list"]//div[contains(@data-qa, "skills-element")]//text()',
        "author_url": '//a[@data-qa="vacancy-company-name"]/@href',
        }
    company_data_xpath = {
        "company_name": "//div[@class='company-header']//span[@data-qa='company-header-title-name']/text()",
        "site_url": "//div[@class='employer-sidebar-content']//a[@class='g-user-content']/@href",
        "activity_areas": "//div[@class='employer-sidebar-block']//p/text()",
        "description": "//div[@class='company-description']//text()",
    }

    def parse(self, response, **kwargs):
        pag_links = response.xpath(self.xpath_query["pagination"])
        yield from self.gen_task(response, pag_links, self.parse)
        ads_links = response.xpath(self.xpath_query["ads"])
        yield from self.gen_task(response, ads_links, self.ads_parse)

    def ads_parse(self, response):
        loader = HeadhunterLoader(response=response)
        loader.add_value("url", response.url)
        for key, selector in self.data_xpath.items():
            loader.add_xpath(key, selector)
        yield loader.load_item()

        company_page_links = response.xpath(self.xpath_query["company_page"])
        yield from self.gen_task(response, company_page_links, self.company_page_parse)

    def company_page_parse(self, response):
        loader = CompanyHeadhunterLoader(response=response)
        loader.add_value("url", response.url)
        for key, selector in self.company_data_xpath.items():
            loader.add_xpath(key, selector)

        yield loader.load_item()

        company_vacancies_links = response.xpath(self.xpath_query["company_vacancies"])
        yield from self.gen_task(response, company_vacancies_links, self.company_vacancies_parse)

    def company_vacancies_parse(self, response):
        pag_links = response.xpath(self.xpath_query["pagination"])
        yield from self.gen_task(response, pag_links, self.parse)
        ads_links = response.xpath(self.xpath_query["ads"])
        yield from self.gen_task(response, ads_links, self.ads_parse)


    @staticmethod
    def gen_task(response, link_list, callback):
        for link in link_list:
            yield response.follow(link.attrib["href"], callback=callback)
