from newsdataapi import NewsDataApiClient
# https://rapidapi.com/newslit/api/newslit-news-search/details # todo


class News:
    def __init__(self, api_key):
        self.client = NewsDataApiClient(apikey=api_key)

    def get_news_raw(self, **kwargs):
        refine = {
            "size": 10,
            "language": "en",
            "prioritydomain": "top",
            "category": "business,politics,science,technology,world",
            "country": 'us',
            "domain": "nbcnews,reuters,npr"
            # "domain": "abcnews,nbcnews,cnn,npr"
        }
        refine.update(kwargs)
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
        text = ""
        if "error" in n.keys():
            text = f"An error occurred getting news: {n['error']}"
        else:
            items = [
                {
                    "Title": x["title"].replace(r"\u2019", "'"),
                    "Link": x["link"],
                    "Source": f'[{x["pubDate"]}] {x["source_id"]} ({",".join(x["country"])})'
                }
                for x in n["results"]
            ]
            for x in items:
                for k, v in x.items():
                    text = text + f"{v}\n"
                text = text + "\n\n"
        return text