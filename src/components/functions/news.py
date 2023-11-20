import json
import requests


class News:
    def __init__(self, apikey=""):
        # WORLDNEWSAPIKEY
        self.api_key = apikey
        self.headers = {}
        self.url_suffix = f"api-key={self.api_key}"
        self.base_url = "https://api.worldnewsapi.com/"
        self.source_map = {
            "AP": "https://apnews.com",
            "FOX": "https://www.foxnews.com",
            "REUTERS": "https://www.reuters.com",
            "BBC": "https://www.bbc.com",
            "NPR": "https://www.npr.org",
            "CNN": "https://www.cnn.com",
            "SKYNEWS": "https://news.sky.com"
        }


    def encode(self, param):
        encoding_mappings = {
            ':': '%3A',
            ",": "%2C",
            " ": "%20",
            "/": "%2f",
        }
        for k, v in encoding_mappings.items():
            param = param.replace(k, v)
        return param


    def source_to_url(self, source):
        return self.source_map.get(source.upper(), "")


    def build_url(self, action, **kwargs):
        url = f"{self.base_url}{action}?api-key={self.api_key}"
        for k, v in kwargs.items():
            param = k.replace('_', '-')
            value = self.encode(v)
            url += f"&{param}={value}"
        return url


    def verify_response(self, response: requests.Response):
        if response.status_code // 100 != 2:
            print(response.json())
            print(response.url)
            return False, {"error": "Non 200 status code from API"}
        try:
            data = response.json()
            news_articles = data["news"]
            return True, news_articles
        except Exception as ex:
            return False, {"error": "Failed to read API response as json"}


    def search_news(
            self,
            sources: list = None,
            **kwargs
    ):
        """
        searches news articles
        """
        params = {
            'language': 'en',
            'source-countries': 'us',
            'sort': 'publish-time',
            'sort-direction': 'DESC'
        }

        if sources:
            sources = [x.upper() for x in sources]
            sources = [self.source_to_url(x) for x in sources]
            sources = [x for x in sources if x != ""]
            params["news-sources"] = ",".join(sources)

        params.update(kwargs)
        url = self.build_url(
            action="search-news",
            **params
        )
        print(url)
        response = requests.get(url=url)
        success, data = self.verify_response(response=response)
        return data











class NewsFunctions:
    def __init__(self, api_key):
        self.client = NewsDataApiClient(apikey=api_key)


    def get_news_raw(self, **kwargs):
        refine = {
            "size": 10,
            "language": "en",
            "prioritydomain": "top",
            # "category": "business,politics,science,technology,world",
            "country": 'us,au,gb',
            "domain": "npr,bbc,abcnews,nbcnews"
        }
        refine.update(kwargs)
        print(json.dumps(refine, indent=4))
        # arguments = refine.copy()
        bad = [k for k, v in refine.items() if v==""]
        for b in bad:
            del refine[b]
        try:
            results = self.client.news_api(**refine)

            return results
        except Exception as e:
            # errors = '\n'.join([f"{k}: {v}" for k, v in e.args.items()])
            errors = str(e.args)
            print(f"error {errors}")
            return {"error": errors}

    def get_news(self, **kwargs):
        n = self.get_news_raw(**kwargs)
        if "error" in n.keys():
            return f"An error occurred getting news: {n['error']}"
        else:
            sep = "\u200b\t|\u200b\t"
            sep = "  |  "
            items = [
                {
                    "Title": x["title"].replace(r"\u2019", "'"),
                    "Link": x["link"],
                    "description": x['description'],
                    "img_url": x["image_url"],
                    # "footer": f'{x["source_id"]} \t|\t {x["pubDate"]} \t|\t {",".join(x["country"])} \t|\t Source: Newsdata.io'
                    "footer": f'{x["source_id"]}{sep}{x["pubDate"]}{sep}Source: Newsdata.io'

            }
                for x in n["results"]
            ]
            return items


