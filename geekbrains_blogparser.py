import os
import requests
import bs4
from dotenv import load_dotenv
from urllib.parse import urljoin
import database
from datetime import datetime
import json

class GbParse:
    def __init__(self, start_url, db, comment_url):
        self.db = db
        self.start_url = start_url
        self.comment_url = comment_url
        self.done_url = set()
        self.tasks = [self.parse_task(self.start_url, self.pag_parse)]
        self.done_url.add(self.start_url)

    @staticmethod
    def _get_response(*args, **kwargs):
        # TODO обработки ошибок
        return requests.get(*args, **kwargs)

    def _get_soup(self, *args, **kwargs):
        response = self._get_response(*args, **kwargs)
        return bs4.BeautifulSoup(response.text, "lxml")

    def parse_task(self, url, callback):
        def wrap():
            soup = self._get_soup(url)
            return callback(url, soup)

        return wrap

    def run(self):
        for task in self.tasks:
            result = task()
            if result:
                self.save(result)

    def pag_parse(self, url, soup):
        for a_tag in soup.find("ul", attrs={"class": "gb__pagination"}).find_all("a"):
            pag_url = urljoin(url, a_tag.get("href"))
            if pag_url not in self.done_url:
                task = self.parse_task(pag_url, self.pag_parse)
                self.tasks.append(task)
            self.done_url.add(pag_url)
        for a_post in soup.find("div", attrs={"class": "post-items-wrapper"}).find_all(
            "a", attrs={"class": "post-item__title"}
        ):
            post_url = urljoin(url, a_post.get("href"))
            if post_url not in self.done_url:
                task = self.parse_task(post_url, self.post_parse)
                self.tasks.append(task)
            self.done_url.add(post_url)

    def get_comment(self, comment_url, soup):
        comment_response = requests.get(comment_url, params={'commentable_id': soup.find('comments').get('commentable-id'), 'commentable_type': 'Post'})
        if comment_response.status_code == 200:
            comment_list = json.loads(comment_response.text)
            comments_basket = []
            for comment in comment_list:
                comments_basket.append(comment)
            return comments_basket

    def post_parse(self, url, soup):
        author_name_tag = soup.find("div", attrs={"itemprop": "author"})
        title = soup.find("h1", attrs={"class": "blogpost-title"}).text
        img_url = soup.find('article').find('img').get('src')
        public_date = datetime.strptime(soup.find('div', attrs={'class':'blogpost-date-views'}).find('time')
                                        .get('datetime')[:10], '%Y-%m-%d')

        com_list = self.get_comment(self.comment_url, soup)
        comments = []
        try:
            for com in com_list:
                comments.append({
                    "name": com['comment']['user']['full_name'],
                    "comment_text": com['comment']['body'],
                    "url": com['comment']['id']
                })
        except TypeError:
            pass

        author = {
            "url": urljoin(url, author_name_tag.parent.get("href")),
            "name": author_name_tag.text,

        }
        tags = [
            {"name": tag.text, "url": urljoin(url, tag.get("href"))}
            for tag in soup.find("article").find_all("a", attrs={"class": "small"})
        ]

        return {
            "post_data": {
                "url": url,
                "title": title,
                "img_url": img_url,
                "public_date": public_date
            },
            "author": author,
            "tags": tags,
            "comments": comments
        }

    def save(self, data: dict):
        self.db.create_post(data)


if __name__ == "__main__":
    load_dotenv('.env')
    parser = GbParse("https://geekbrains.ru/posts", database.Database(os.getenv("SQLDB_URL")),
                     'https://geekbrains.ru/api/v2/comments')
    parser.run()