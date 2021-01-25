import json
import requests
import time


class Parser5ka:
    _params = {
        "records_per_page": 50,
    }
    _headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:81.0) Gecko/20100101 Firefox/81.0",
    }

    def __init__(self, start_url):
        self.start_url = start_url

    @staticmethod
    def _get(*args, **kwargs):
        while True:
            try:
                response = requests.get(*args, **kwargs)
                if response.status_code != 200:
                    raise Exception  # todo сделать класс ошибки для работы со статусами
                time.sleep(0.1)
                return response
            # todo Обработать конкретные ошибки
            except Exception:
                time.sleep(0.250)

    def run(self):
        for products in self.parse(self.start_url):
            for product in products:
                self.save_to_json_file(product, product["id"])

    def parse(self, url):
        if not url:
            url = self.start_url
        params = self._params
        while url:
            response = self._get(url, params=params, headers=self._headers)
            if params:
                params = {}
            data: dict = response.json()
            url = data.get("next")

            yield data.get("results")

    @staticmethod
    def save_to_json_file(data: dict, file_name):
        with open(f"products/{file_name}.json", "w", encoding="UTF-8") as file:
            json.dump(data, file, ensure_ascii=False)


class CategoriesParser5ka(Parser5ka):

    def __init__(self, start_url, category_url):
        self.category_url = category_url
        super().__init__(start_url)

    def get_categories(self, category_url):
        response = self._get(category_url, headers=self._headers)
        categories = response.json()
        return categories

    def run(self):
        for category in self.get_categories(self.category_url):
            result = {'name': category['parent_group_name'],
                      'code': category['parent_group_code'],
                      'products': []}
            self._params["categories"] = category['parent_group_code']
            for products in self.parse(self.start_url):
                result["products"].extend(products)
                self.save_to_json_file(result, result['name'])


if __name__ == "__main__":
    parser = CategoriesParser5ka(start_url="https://5ka.ru/api/v2/special_offers/", category_url="https://5ka.ru/api/v2/categories/")
    parser.run()