import json
import scrapy
from gb_parse.loaders import InstaTagLoader
from datetime import datetime as dt
from ..items import InstagramPostItem, InstaTagItem


class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['www.instagram.com']
    start_urls = ['http://www.instagram.com/']
    login_url = "https://www.instagram.com/accounts/login/ajax/"
    graphql_url = "/graphql/query/"
    query_hash = {
        "posts": "56a7068fea504063273cc2120ffd54f3",
        "tag_posts": "9b498c08113f1e09617a1703c22b2f32",
    }

    def __init__(self, login, password, *args, **kwargs):
        self.tags = ["python", "программирование", "developers"]
        self.login = login
        self.enc_passwd = password
        super().__init__(*args, **kwargs)

    def parse(self, response, **kwargs):
        try:
            js_data = self.js_data_extract(response)
            yield scrapy.FormRequest(
                self.login_url,
                method="POST",
                callback=self.parse,
                formdata={
                    "username": self.login,
                    "enc_password": self.enc_passwd,
                },
                headers={"X-CSRFToken": js_data["config"]["csrf_token"]},
            )
        except AttributeError as e:
            if response.json().get("authenticated"):
                for tag in self.tags:
                    yield response.follow(f"/explore/tags/{tag}/", callback=self.tag_parse)

    def tag_parse(self, response, **kwargs):
        js_data = self.js_data_extract(response)
        yield InstaTagItem(
            date_parse = dt.now(),
            data= {
                "url": response.url,
                "insta_id": js_data['entry_data']['TagPage'][0]['graphql']['hashtag']['id'],
                "name": js_data['entry_data']['TagPage'][0]['graphql']['hashtag']['name'],
                "profile_pic_url": js_data['entry_data']['TagPage'][0]['graphql']['hashtag']['profile_pic_url'],
            },
        )

        tag = js_data["entry_data"]["TagPage"][0]["graphql"]["hashtag"]
        yield from self.pagination_tag_posts(tag, response)

    def tag_page_parse(self, response):
        tag = response.json()["data"]["hashtag"]
        yield from self.pagination_tag_posts(tag, response)

    def pagination_tag_posts(self, tag, response):
        if tag["edge_hashtag_to_media"]["page_info"]["has_next_page"]:
            variables = {
                "tag_name": tag["name"],
                "first": 100,
                "after": tag["edge_hashtag_to_media"]["page_info"]["end_cursor"],
            }
            url = f'{self.graphql_url}?query_hash={self.query_hash["tag_posts"]}&variables={str(variables)}'
            yield response.follow(url, callback=self.tag_page_parse)

        edges_data = tag["edge_hashtag_to_media"]["edges"]
        yield from self.get_post_item(edges_data)

    @staticmethod
    def get_post_item(edges_data):
        for node in edges_data:
            yield InstagramPostItem(date_parse=dt.now(), data=node["node"])

    @staticmethod
    def js_data_extract(response):
        script = response.xpath('//script[contains(text(), "window._sharedData =")]/text()').get()
        return json.loads(script.replace("window._sharedData =", "")[:-1])
