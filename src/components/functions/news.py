import json

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




if __name__ == '__main__':
    n = NewsFunctions("pub_32005769a84dc89f492b5cb67b8bc78808ce2")
    k = {
        "size": 5,
        "domain": "foxnews"
    }
    x = n.get_news_raw()
    print(json.dumps(x, indent=4))
