from newsdataapi import NewsDataApiClient
# https://rapidapi.com/newslit/api/newslit-news-search/details # todo


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
            # "domain": "abcnews,nbcnews,cnn,npr"
        }
        refine.update(kwargs)
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
            items = [
                {
                    "Title": x["title"].replace(r"\u2019", "'"),
                    "Link": x["link"],
                    "Source": f'[{x["pubDate"]}] {x["source_id"]} ({",".join(x["country"])})'
                }
                for x in n["results"]
            ]
            return items
